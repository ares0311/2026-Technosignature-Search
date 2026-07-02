"""Track A Phase 2: known-source catalog acquisition and normalization.

Implements the fixed-sky-position catalogs from
docs/technosignature_datasets_agent_brief.md Phase 2 (Catalog Cross-Matching):
ATNF pulsars, CHIME/FRB Catalog 1, Roma-BZCAT blazars/AGN, and Fermi LAT
4FGL-DR4 gamma-ray sources. Each is normalized to a common schema (ICRS
RA/Dec degrees, object class, source provenance) so a candidate sky position
can be cross-matched against all four in one cone search.

CelesTrak/SatNOGS satellite-transmitter matching is out of scope here: it
requires SGP4 orbital propagation against an observation timestamp, not a
static sky position, and is tracked separately in
docs/PRODUCTION_READINESS.md.

Acquisition requires network access to HEASARC/VizieR/FSSC hosts that this
sandbox's network policy may not reach; acquisition must then be run locally.
"""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from techno_search.track_a_data_guard import (
    AcquisitionManifestRecord,
    append_acquisition_manifest,
    check_disk_budget_or_raise,
    log_progress,
)

NORMALIZED_CATALOG_SCHEMA_VERSION = "track_a_normalized_catalog_v1"

NORMALIZED_COLUMNS = ("source_id", "ra_deg", "dec_deg", "object_class", "catalog_name")

ATNF_EXPECTED_MIN_ROW_COUNT = 1000
CHIME_FRB_EXPECTED_MIN_ROW_COUNT = 536
ROMABZCAT_EXPECTED_ROW_COUNT = 3561
FERMI_4FGL_EXPECTED_ROW_COUNT = 7194

_RA_ALIASES = ("RAJ2000", "RA_ICRS", "_RAJ2000", "RA")
_DEC_ALIASES = ("DEJ2000", "DE_ICRS", "_DEJ2000", "DEC", "Dec")


def default_catalog_cache_dir(project_root: Path | None = None, *, name: str) -> Path:
    root = project_root or Path(__file__).resolve().parents[2]
    return root / "data_cache" / "raw" / name


def default_normalized_catalog_path(project_root: Path | None = None, *, name: str) -> Path:
    root = project_root or Path(__file__).resolve().parents[2]
    return root / "data_cache" / "normalized" / f"{name}.parquet"


def _resolve_column(columns: Any, aliases: tuple[str, ...]) -> str:
    for alias in aliases:
        if alias in columns:
            return alias
    msg = f"None of the expected coordinate columns {aliases} found in {list(columns)}"
    raise ValueError(msg)


def _write_normalized(
    df: Any,
    *,
    project_root: Path,
    catalog_name: str,
) -> Path:
    out_path = default_normalized_catalog_path(project_root, name=catalog_name)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)
    return out_path


def normalize_atnf_pulsars(df: Any) -> Any:
    """Normalize a psrqpy ATNF table (RAJ/DECJ sexagesimal) to ra_deg/dec_deg."""

    import pandas as pd
    from astropy import units as u
    from astropy.coordinates import Angle

    if "PSRJ" not in df.columns:
        msg = "ATNF table missing required column: PSRJ"
        raise ValueError(msg)
    if "RAJ" not in df.columns or "DECJ" not in df.columns:
        msg = "ATNF table missing required sexagesimal columns: RAJ, DECJ"
        raise ValueError(msg)

    ra_deg = Angle(df["RAJ"].astype(str).to_numpy(), unit=u.hourangle).degree
    dec_deg = Angle(df["DECJ"].astype(str).to_numpy(), unit=u.deg).degree

    return pd.DataFrame(
        {
            "source_id": df["PSRJ"].astype(str),
            "ra_deg": ra_deg,
            "dec_deg": dec_deg,
            "object_class": "pulsar",
            "catalog_name": "atnf",
        }
    )


def normalize_chime_frb(df: Any) -> Any:
    """Normalize a CHIME/FRB Catalog 1 VizieR table to ra_deg/dec_deg."""

    import pandas as pd

    ra_col = _resolve_column(df.columns, _RA_ALIASES)
    dec_col = _resolve_column(df.columns, _DEC_ALIASES)
    name_col = next((c for c in ("TNS", "FRB", "Name") if c in df.columns), df.columns[0])
    repeater_col = next((c for c in ("Rep", "Repeater", "repeater_flag") if c in df.columns), None)

    if repeater_col is not None:
        object_class = df[repeater_col].apply(
            lambda v: "repeating_frb" if str(v).strip().lower() in {"1", "true", "yes", "r"}
            else "nonrepeating_frb_candidate"
        )
    else:
        object_class = "frb"

    return pd.DataFrame(
        {
            "source_id": df[name_col].astype(str),
            "ra_deg": df[ra_col].astype(float),
            "dec_deg": df[dec_col].astype(float),
            "object_class": object_class,
            "catalog_name": "chime_frb",
        }
    )


def normalize_romabzcat(df: Any) -> Any:
    """Normalize a Roma-BZCAT VizieR table to ra_deg/dec_deg."""

    import pandas as pd

    ra_col = _resolve_column(df.columns, _RA_ALIASES)
    dec_col = _resolve_column(df.columns, _DEC_ALIASES)
    name_col = next((c for c in ("Name", "BZCAT", "Source") if c in df.columns), df.columns[0])

    return pd.DataFrame(
        {
            "source_id": df[name_col].astype(str),
            "ra_deg": df[ra_col].astype(float),
            "dec_deg": df[dec_col].astype(float),
            "object_class": "blazar_agn",
            "catalog_name": "romabzcat",
        }
    )


def normalize_fermi_4fgl(df: Any) -> Any:
    """Normalize a Fermi LAT 4FGL-DR4 FITS-derived table to ra_deg/dec_deg."""

    import pandas as pd

    ra_col = _resolve_column(df.columns, _RA_ALIASES)
    dec_col = _resolve_column(df.columns, _DEC_ALIASES)
    name_col = next(
        (c for c in ("Source_Name", "ASSOC1", "Name") if c in df.columns), df.columns[0]
    )

    return pd.DataFrame(
        {
            "source_id": df[name_col].astype(str),
            "ra_deg": df[ra_col].astype(float),
            "dec_deg": df[dec_col].astype(float),
            "object_class": "gamma_ray_source",
            "catalog_name": "fermi_4fgl",
        }
    )


def acquire_atnf_pulsars(
    *, manifest_path: Path | None = None, project_root: Path | None = None
) -> AcquisitionManifestRecord:
    """Download the ATNF pulsar catalog via `psrqpy` and normalize it."""

    try:
        from psrqpy import QueryATNF
    except ImportError as exc:
        msg = (
            "psrqpy is required to acquire the ATNF catalog. Install with "
            "`.venv/bin/pip install psrqpy`."
        )
        raise RuntimeError(msg) from exc

    root = project_root or Path(__file__).resolve().parents[2]
    check_disk_budget_or_raise(project_root=root, additional_expected_bytes=5 * 1024 * 1024)

    log_progress("[START] Querying ATNF pulsar catalog via psrqpy")
    query = QueryATNF(params=["PSRJ", "RAJ", "DECJ", "P0", "P1", "DM", "BINARY", "DIST"])
    df = query.table.to_pandas()
    log_progress(f"[INFO] Downloaded {len(df)} rows, verifying row count")
    if len(df) <= ATNF_EXPECTED_MIN_ROW_COUNT:
        msg = (
            f"ATNF catalog row count too low: expected >{ATNF_EXPECTED_MIN_ROW_COUNT}, "
            f"got {len(df)}"
        )
        raise RuntimeError(msg)

    normalized = normalize_atnf_pulsars(df)
    out_path = _write_normalized(normalized, project_root=root, catalog_name="atnf")
    log_progress(f"[OK] Wrote {len(df)} verified rows -> {out_path}")

    record = AcquisitionManifestRecord(
        source_name="atnf_pulsars",
        source_url="https://heasarc.gsfc.nasa.gov/W3Browse/all/atnfpulsar.html",
        access_method="psrqpy.QueryATNF",
        downloaded_at_utc=datetime.now(UTC).isoformat(),
        local_path=str(out_path),
        file_size_bytes=out_path.stat().st_size,
        row_count=len(df),
        auth_required=False,
        license_or_terms="ATNF Pulsar Catalogue — public, cite Manchester et al. 2005",
    )
    manifest = manifest_path or (root / "artifacts" / "manifests" / "data_manifest.jsonl")
    append_acquisition_manifest(record, manifest)
    return record


def acquire_chime_frb(
    *, manifest_path: Path | None = None, project_root: Path | None = None
) -> AcquisitionManifestRecord:
    """Download the CHIME/FRB Catalog 1 via VizieR and normalize it."""

    try:
        from astroquery.vizier import Vizier
    except ImportError as exc:
        msg = (
            "astroquery is required to acquire CHIME/FRB. Install with "
            "`.venv/bin/pip install astroquery`."
        )
        raise RuntimeError(msg) from exc

    root = project_root or Path(__file__).resolve().parents[2]
    check_disk_budget_or_raise(project_root=root, additional_expected_bytes=5 * 1024 * 1024)

    log_progress("[START] Querying CHIME/FRB Catalog 1 via VizieR (J/ApJS/257/59)")
    Vizier.ROW_LIMIT = -1
    tables = Vizier.get_catalogs("J/ApJS/257/59")
    table = tables["J/ApJS/257/59/table2"]
    df = table.to_pandas()
    log_progress(f"[INFO] Downloaded {len(df)} rows, verifying row count")
    if len(df) < CHIME_FRB_EXPECTED_MIN_ROW_COUNT:
        msg = (
            f"CHIME/FRB catalog row count too low: expected >={CHIME_FRB_EXPECTED_MIN_ROW_COUNT}, "
            f"got {len(df)}"
        )
        raise RuntimeError(msg)

    normalized = normalize_chime_frb(df)
    out_path = _write_normalized(normalized, project_root=root, catalog_name="chime_frb")
    log_progress(f"[OK] Wrote {len(df)} verified rows -> {out_path}")

    record = AcquisitionManifestRecord(
        source_name="chime_frb_catalog1",
        source_url="https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=J/ApJS/257/59/table2",
        access_method="astroquery.vizier.Vizier.get_catalogs('J/ApJS/257/59')",
        downloaded_at_utc=datetime.now(UTC).isoformat(),
        local_path=str(out_path),
        file_size_bytes=out_path.stat().st_size,
        row_count=len(df),
        auth_required=False,
        license_or_terms="CHIME/FRB Collaboration, public per doi.org/10.3847/1538-4365/ac33ab",
    )
    manifest = manifest_path or (root / "artifacts" / "manifests" / "data_manifest.jsonl")
    append_acquisition_manifest(record, manifest)
    return record


def acquire_romabzcat(
    *, manifest_path: Path | None = None, project_root: Path | None = None
) -> AcquisitionManifestRecord:
    """Download the Roma-BZCAT blazar catalog via VizieR and normalize it."""

    try:
        from astroquery.vizier import Vizier
    except ImportError as exc:
        msg = (
            "astroquery is required to acquire Roma-BZCAT. Install with "
            "`.venv/bin/pip install astroquery`."
        )
        raise RuntimeError(msg) from exc

    root = project_root or Path(__file__).resolve().parents[2]
    check_disk_budget_or_raise(project_root=root, additional_expected_bytes=5 * 1024 * 1024)

    log_progress("[START] Querying Roma-BZCAT via VizieR (VII/274)")
    Vizier.ROW_LIMIT = -1
    tables = Vizier.get_catalogs("VII/274")
    table = tables["VII/274/bzcat5"]
    df = table.to_pandas()
    log_progress(f"[INFO] Downloaded {len(df)} rows, verifying row count")
    if len(df) != ROMABZCAT_EXPECTED_ROW_COUNT:
        msg = (
            f"Roma-BZCAT row count mismatch: expected {ROMABZCAT_EXPECTED_ROW_COUNT}, "
            f"got {len(df)}"
        )
        raise RuntimeError(msg)

    normalized = normalize_romabzcat(df)
    out_path = _write_normalized(normalized, project_root=root, catalog_name="romabzcat")
    log_progress(f"[OK] Wrote {len(df)} verified rows -> {out_path}")

    record = AcquisitionManifestRecord(
        source_name="romabzcat",
        source_url="https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=VII/274/bzcat5",
        access_method="astroquery.vizier.Vizier.get_catalogs('VII/274')",
        downloaded_at_utc=datetime.now(UTC).isoformat(),
        local_path=str(out_path),
        file_size_bytes=out_path.stat().st_size,
        row_count=len(df),
        auth_required=False,
        license_or_terms="Roma-BZCAT, public via HEASARC/VizieR",
    )
    manifest = manifest_path or (root / "artifacts" / "manifests" / "data_manifest.jsonl")
    append_acquisition_manifest(record, manifest)
    return record


def acquire_fermi_4fgl(
    *, manifest_path: Path | None = None, project_root: Path | None = None
) -> AcquisitionManifestRecord:
    """Download the Fermi LAT 4FGL-DR4 FITS catalog and normalize it."""

    try:
        import requests
        from astropy.table import Table
    except ImportError as exc:
        msg = "requests and astropy are required to acquire Fermi 4FGL-DR4."
        raise RuntimeError(msg) from exc

    root = project_root or Path(__file__).resolve().parents[2]
    check_disk_budget_or_raise(project_root=root, additional_expected_bytes=50 * 1024 * 1024)

    out_dir = default_catalog_cache_dir(root, name="fermi_4fgl_dr4")
    out_dir.mkdir(parents=True, exist_ok=True)
    url = "https://fermi.gsfc.nasa.gov/ssc/data/access/lat/14yr_catalog/gll_psc_v32.fit"
    fits_path = out_dir / "gll_psc_v32.fit"

    log_progress(f"[START] Downloading Fermi 4FGL-DR4 FITS from {url}")
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    fits_path.write_bytes(response.content)
    log_progress(f"[INFO] Downloaded {len(response.content)} bytes, parsing FITS table")

    table = Table.read(fits_path)
    df = table.to_pandas()
    log_progress(f"[INFO] Parsed {len(df)} rows, verifying row count")
    if len(df) != FERMI_4FGL_EXPECTED_ROW_COUNT:
        msg = (
            f"Fermi 4FGL-DR4 row count mismatch: expected {FERMI_4FGL_EXPECTED_ROW_COUNT}, "
            f"got {len(df)}"
        )
        raise RuntimeError(msg)

    normalized = normalize_fermi_4fgl(df)
    out_path = _write_normalized(normalized, project_root=root, catalog_name="fermi_4fgl")
    log_progress(f"[OK] Wrote {len(df)} verified rows -> {out_path}")

    record = AcquisitionManifestRecord(
        source_name="fermi_4fgl_dr4",
        source_url=url,
        access_method="requests.get + astropy.table.Table.read (FITS)",
        downloaded_at_utc=datetime.now(UTC).isoformat(),
        local_path=str(out_path),
        file_size_bytes=out_path.stat().st_size,
        row_count=len(df),
        auth_required=False,
        license_or_terms="Fermi LAT 4FGL-DR4, public via FSSC",
    )
    manifest = manifest_path or (root / "artifacts" / "manifests" / "data_manifest.jsonl")
    append_acquisition_manifest(record, manifest)
    return record


CATALOG_ACQUISITION_SPECS: dict[str, Any] = {
    "atnf": acquire_atnf_pulsars,
    "chime_frb": acquire_chime_frb,
    "romabzcat": acquire_romabzcat,
    "fermi_4fgl": acquire_fermi_4fgl,
}
