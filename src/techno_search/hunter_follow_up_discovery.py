"""Archive-backed discovery of exact later-epoch Hunter follow-up cadences."""

from __future__ import annotations

import json
import re
import ssl
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import certifi

ARCHIVE_SEARCH_URL = "https://breakthroughinitiatives.org/opendatasearch"
DATA_USE_URL = "https://seti.berkeley.edu/lband2017/downloads.html"
FOLLOW_UP_CADENCE_SCHEMA_VERSION = "hunter_follow_up_cadence_v1"
EXPECTED_ROLES = ("on", "off", "on", "off", "on", "off")
_FILENAME_RE = re.compile(
    r"_guppi_(?P<mjd_day>\d+)_(?P<seconds>\d+)_.*_(?P<sequence>\d{4})"
    r"\.gpuspec\.0002\.h5$"
)


class FollowUpDiscoveryError(RuntimeError):
    """Raised when current archive evidence cannot support an exact follow-up."""


@dataclass(frozen=True)
class ArchiveProduct:
    utc_start: str
    mjd: float
    telescope: str
    target_name: str
    ra_deg: float
    dec_deg: float
    center_frequency_mhz: float
    file_type: str
    size_bytes: int
    md5: str
    url: str

    @property
    def filename(self) -> str:
        return Path(urllib.parse.urlparse(self.url).path).name

    @property
    def sequence(self) -> int:
        match = _FILENAME_RE.search(self.filename)
        if match is None:
            raise FollowUpDiscoveryError(
                f"archive product lacks a supported GBT sequence filename: {self.filename}"
            )
        return int(match.group("sequence"))

    @property
    def archive_directory(self) -> str:
        return self.url.rsplit("/", 1)[0]


ArchiveFetcher = Callable[[Mapping[str, str]], str]


class _ArchiveTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[tuple[list[str], str]] = []
        self._in_row = False
        self._in_cell = False
        self._cells: list[str] = []
        self._cell_parts: list[str] = []
        self._href = ""

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag == "tr":
            self._in_row = True
            self._cells = []
            self._href = ""
        elif tag == "td" and self._in_row:
            self._in_cell = True
            self._cell_parts = []
        elif tag == "a" and self._in_row:
            href = dict(attrs).get("href")
            if href:
                self._href = href

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._cell_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self._in_cell:
            self._cells.append(" ".join("".join(self._cell_parts).split()))
            self._in_cell = False
        elif tag == "tr" and self._in_row:
            if self._cells and self._href:
                self.rows.append((self._cells, self._href))
            self._in_row = False


def parse_archive_products(html: str) -> list[ArchiveProduct]:
    """Parse authoritative BL archive search rows, excluding other HDF5 products."""
    parser = _ArchiveTableParser()
    parser.feed(html)
    products: list[ArchiveProduct] = []
    for cells, href in parser.rows:
        if len(cells) < 10 or not href.endswith(".gpuspec.0002.h5"):
            continue
        try:
            product = ArchiveProduct(
                utc_start=f"{cells[0].replace(' ', 'T')}Z",
                mjd=float(cells[1]),
                telescope=cells[2],
                target_name=cells[3],
                ra_deg=float(cells[4]),
                dec_deg=float(cells[5]),
                center_frequency_mhz=float(cells[6]),
                file_type=cells[7],
                size_bytes=int(cells[8]),
                md5=cells[9].lower(),
                url=href,
            )
        except (TypeError, ValueError) as exc:
            raise FollowUpDiscoveryError(
                "BL archive returned a malformed product metadata row"
            ) from exc
        if (
            product.telescope != "GBT"
            or product.file_type != "HDF5"
            or product.size_bytes <= 0
            or not re.fullmatch(r"[0-9a-f]{32}", product.md5)
        ):
            raise FollowUpDiscoveryError(
                f"BL archive returned invalid provenance for {product.filename}"
            )
        products.append(product)
    return products


def fetch_archive_products(
    parameters: Mapping[str, str],
    *,
    timeout_seconds: float = 60.0,
) -> str:
    query = urllib.parse.urlencode(
        {
            "project": "GBT",
            "file_type": "HDF5",
            "search": "Search",
            "perPage": "100",
            **parameters,
        }
    )
    request = urllib.request.Request(
        f"{ARCHIVE_SEARCH_URL}?{query}",
        headers={"User-Agent": "Techno-Hunter/1 archive metadata discovery"},
    )
    context = ssl.create_default_context(cafile=certifi.where())
    try:
        with urllib.request.urlopen(
            request, context=context, timeout=timeout_seconds
        ) as response:
            payload: bytes = response.read()
            return payload.decode("utf-8")
    except Exception as exc:
        raise FollowUpDiscoveryError(
            f"BL archive metadata retrieval failed: {type(exc).__name__}: {exc}"
        ) from exc


def discover_follow_up_targets(
    targets: Sequence[Mapping[str, Any]],
    *,
    fetcher: ArchiveFetcher = fetch_archive_products,
    retrieved_at_utc: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Attach current exact cadence products to later-epoch follow-up targets."""
    retrieved_at = retrieved_at_utc or datetime.now(UTC).isoformat().replace(
        "+00:00", "Z"
    )
    enriched: list[dict[str, Any]] = []
    discoveries: list[dict[str, Any]] = []
    for raw_target in targets:
        target = dict(raw_target)
        action = str(target.get("recommended_next_action", "")).lower()
        if "later epoch" not in action and "on/off cadence" not in action:
            enriched.append(target)
            continue
        target_name = str(target.get("hip", "")).strip()
        if not target_name:
            raise FollowUpDiscoveryError(
                "follow-up target lacks a canonical target identifier"
            )
        prior_max_mjd = _prior_observation_max_mjd(target)
        cadence = _discover_later_cadence(
            target_name=target_name,
            prior_max_mjd=prior_max_mjd,
            fetcher=fetcher,
            retrieved_at_utc=retrieved_at,
        )
        output_path = (
            Path("data/extended_corpus/hunter_follow_ups/bl_hits")
            / f"{cadence['cadence_id']}.csv"
        )
        target.update(
            {
                "source_hdf5_url": "",
                "source_data_path": str(output_path),
                "estimated_download_gb": cadence["estimated_download_gb"],
                "follow_up_cadence": cadence,
            }
        )
        enriched.append(target)
        discoveries.append(
            {
                "target_id": target_name,
                "cadence_id": cadence["cadence_id"],
                "scan_count": len(cadence["scans"]),
                "prior_observation_max_mjd": prior_max_mjd,
                "follow_up_observation_min_mjd": cadence[
                    "follow_up_observation_min_mjd"
                ],
                "later_epoch_days": cadence["later_epoch_days"],
                "estimated_download_gb": cadence["estimated_download_gb"],
                "validity_state": cadence["validity_state"],
            }
        )
    return (
        enriched,
        {
            "schema_version": "hunter_follow_up_discovery_report_v1",
            "source": ARCHIVE_SEARCH_URL,
            "retrieved_at_utc": retrieved_at,
            "requested_target_count": len(targets),
            "cadence_discovery_count": len(discoveries),
            "discoveries": discoveries,
        },
    )


def _discover_later_cadence(
    *,
    target_name: str,
    prior_max_mjd: float,
    fetcher: ArchiveFetcher,
    retrieved_at_utc: str,
) -> dict[str, Any]:
    target_products = [
        product
        for product in parse_archive_products(fetcher({"target": target_name}))
        if product.target_name.casefold() == target_name.casefold()
        and product.mjd > prior_max_mjd
    ]
    triples: list[tuple[ArchiveProduct, ArchiveProduct, ArchiveProduct]] = []
    by_directory: dict[str, list[ArchiveProduct]] = {}
    for product in target_products:
        by_directory.setdefault(product.archive_directory, []).append(product)
    for products in by_directory.values():
        by_sequence = {product.sequence: product for product in products}
        for sequence, first in by_sequence.items():
            if sequence + 2 in by_sequence and sequence + 4 in by_sequence:
                triple = (
                    first,
                    by_sequence[sequence + 2],
                    by_sequence[sequence + 4],
                )
                if triple[2].mjd - triple[0].mjd <= 0.05:
                    triples.append(triple)
    if not triples:
        raise FollowUpDiscoveryError(
            f"no complete later-epoch three-ON cadence was found for {target_name}"
        )

    for on_scans in sorted(triples, key=lambda item: item[0].mjd, reverse=True):
        center = (on_scans[0].mjd + on_scans[-1].mjd) / 2.0
        session_products = parse_archive_products(
            fetcher({"mjd": f"{center:.7f}", "mjd_range": "0.03"})
        )
        start_sequence = on_scans[0].sequence
        by_sequence = {
            product.sequence: product
            for product in session_products
            if product.archive_directory == on_scans[0].archive_directory
            and start_sequence <= product.sequence <= start_sequence + 5
        }
        if len(by_sequence) != 6:
            continue
        scans = [by_sequence[start_sequence + offset] for offset in range(6)]
        roles = tuple(
            "on" if product.target_name.casefold() == target_name.casefold() else "off"
            for product in scans
        )
        if roles != EXPECTED_ROLES:
            continue
        return _cadence_payload(
            target_name=target_name,
            scans=scans,
            prior_max_mjd=prior_max_mjd,
            retrieved_at_utc=retrieved_at_utc,
        )
    raise FollowUpDiscoveryError(
        f"no provenance-complete later-epoch ABACAD cadence was found for {target_name}"
    )


def _cadence_payload(
    *,
    target_name: str,
    scans: Sequence[ArchiveProduct],
    prior_max_mjd: float,
    retrieved_at_utc: str,
) -> dict[str, Any]:
    first = scans[0]
    date = first.utc_start[:10]
    size_bytes = sum(scan.size_bytes for scan in scans)
    scan_payloads = []
    for index, (role, scan) in enumerate(zip(EXPECTED_ROLES, scans, strict=True), 1):
        scan_payloads.append(
            {
                "sequence_index": index,
                "scan_role": role,
                "source_name": scan.target_name,
                "utc_start": scan.utc_start,
                "mjd": scan.mjd,
                "filename": scan.filename,
                "size_bytes": scan.size_bytes,
                "md5": scan.md5,
                "url": scan.url,
            }
        )
    return {
        "schema_version": FOLLOW_UP_CADENCE_SCHEMA_VERSION,
        "cadence_id": f"GBT_{target_name}_{date}_ABACAD",
        "target_name": target_name,
        "instrument": "Green Bank Telescope",
        "receiver": "L band",
        "source_archive": "Breakthrough Listen Open Data Archive",
        "archive_search_url": ARCHIVE_SEARCH_URL,
        "data_use_url": DATA_USE_URL,
        "data_license": "CC BY 4.0",
        "retrieved_at_utc": retrieved_at_utc,
        "validity_state": "valid",
        "prior_observation_max_mjd": round(prior_max_mjd, 7),
        "follow_up_observation_min_mjd": first.mjd,
        "later_epoch_days": round(first.mjd - prior_max_mjd, 7),
        "estimated_download_bytes": size_bytes,
        "estimated_download_gb": round(size_bytes / 1_000_000_000, 6),
        "human_approval_status": "pending",
        "approved_for_local_real_data": False,
        "external_submission_authorized": False,
        "analysis": {
            "max_drift_hz_per_sec": 10.0,
            "min_drift_hz_per_sec": 0.0001,
            "snr_threshold": 10.0,
        },
        "scans": scan_payloads,
    }


def _prior_observation_max_mjd(target: Mapping[str, Any]) -> float:
    source_path = Path(str(target.get("source_data_path", "")))
    sidecar_path = source_path.with_name(source_path.name + ".provenance.json")
    if not source_path.is_file() or not sidecar_path.is_file():
        raise FollowUpDiscoveryError(
            f"prior follow-up evidence lacks a readable cadence artifact: {source_path}"
        )
    try:
        provenance = json.loads(sidecar_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FollowUpDiscoveryError(
            f"prior cadence provenance is unreadable: {sidecar_path}"
        ) from exc
    if provenance.get("classification") != "derived_real_observation_cadence":
        raise FollowUpDiscoveryError(
            f"prior evidence is not a validated observation cadence: {sidecar_path}"
        )
    values: list[float] = []
    for artifact in provenance.get("source_artifacts", []):
        if not isinstance(artifact, Mapping):
            continue
        filename = str(artifact.get("artifact_filename", ""))
        match = _FILENAME_RE.search(filename.replace(".dat", ".h5"))
        if match is None:
            continue
        values.append(
            float(match.group("mjd_day"))
            + float(match.group("seconds")) / 86_400.0
        )
    if not values:
        raise FollowUpDiscoveryError(
            f"prior cadence provenance has no parseable observation times: {sidecar_path}"
        )
    return max(values)


def cadence_as_gbt_manifest(
    cadence: Mapping[str, Any], *, approved_at_utc: str
) -> dict[str, Any]:
    """Convert frozen Hunter metadata into the existing approved GBT executor schema."""
    payload = {
        key: value
        for key, value in cadence.items()
        if key
        not in {
            "estimated_download_bytes",
            "estimated_download_gb",
            "prior_observation_max_mjd",
            "follow_up_observation_min_mjd",
            "later_epoch_days",
            "retrieved_at_utc",
            "validity_state",
        }
    }
    payload.update(
        {
            "schema_version": "gbt_observation_cadence_v1",
            "human_approval_status": "approved",
            "approved_for_local_real_data": True,
            "hunter_acquisition_approval": {
                "method": "Run-New-Search --approve-acquisition",
                "approved_at_utc": approved_at_utc,
            },
        }
    )
    return payload
