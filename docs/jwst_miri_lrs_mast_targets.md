<<<<<<< HEAD
# Research request: real JWST MIRI LRS target for a MAST download test

## Context (assume zero prior knowledge of this project)

I run a codebase called "Technosignature Search" that searches public
astronomical archives for candidate signals. It has a Python CLI command,
`techno-search jwst-miri-lrs-search <target>`, that queries NASA's MAST
archive via `astroquery.mast.Observations.query_criteria()` for real JWST
MIRI Low Resolution Spectrometer (LRS) transmission-spectrum observations
of a named astronomical object, then downloads the resulting "x1d"
(1D-extracted-spectrum) FITS product(s).

The query it runs is equivalent to:

```python
from astroquery.mast import Observations
obs = Observations.query_criteria(
=======
# Verified JWST MIRI LRS Targets for MAST Download Testing

Date verified: 2026-07-03

## Short answer

Use `WASP-43` as the first test target. It resolves through `astroquery.mast.Observations.query_criteria()` and returns a real JWST MIRI LRS slitless observation with `P750L` and downloadable `x1dints` FITS products.

The exact query criterion tested was:

```python
Observations.query_criteria(
>>>>>>> 0f03d7a (  Adding a JWST Note)
    objectname="<TARGET>",
    obs_collection="JWST",
    instrument_name=["MIRI/SLIT", "MIRI/SLITLESS"],
    filters="P750L",
)
```

<<<<<<< HEAD
I need a **real target name that resolves via MAST's name resolver and
actually has at least one MIRI LRS observation with an x1d product
available**, so I can run and verify this command for the first time
against real data. I do not want a guessed name — the command has already
failed once against a placeholder string.

## What I need you to find and report back

1. **One (or a few) real, specific object identifiers** (e.g. a star name,
   "WASP-XX", "TOI-XXXX", a 2MASS/Gaia ID, etc.) that MAST's name resolver
   can resolve to a sky position, AND that has at least one real JWST
   MIRI LRS observation (`instrument_name` = `MIRI/SLIT` or
   `MIRI/SLITLESS`) with a corresponding x1d or x1dints data product
   available for download.
2. How you verified it (e.g. searched the MAST portal directly at
   https://mast.stsci.edu/portal/Mashup/Clients/Mast/Portal.html, or the
   JWST proposal/program information, or a paper that names the exact
   target and instrument mode used). I need a citable source or a
   direct verification method, not an inference from general astronomy
   knowledge.
3. If possible, the exact MAST **proposal ID / observation ID** for that
   x1d product, so I can cross-check it lines up with what my code
   downloads.

## What NOT to do

- Do not guess a plausible-sounding star name without checking it actually
  has MIRI LRS x1d data in MAST — many exoplanet hosts have *other*
  instrument modes (NIRSpec, NIRISS) but not MIRI LRS specifically.
- Do not assume Boyajian's Star (KIC 8462852) has MIRI LRS observations —
  that target was used in a *different* part of this project (Kepler
  photometry), not JWST spectroscopy, and I have no evidence it has JWST
  MIRI LRS data.
=======
## Product-level verified targets

These were verified by running `astroquery.mast.Observations.query_criteria()` and then `Observations.get_product_list()` against MAST. A target is included only if the MAST query returned at least one `MIRI/SLIT` or `MIRI/SLITLESS` observation with `filters="P750L"` and at least one FITS product whose filename/product subgroup indicates `x1d` or `x1dints`.

| CLI target to try | MAST target_name returned | Proposal ID | MAST observation ID | instrument_name | Filter | x1d-like products found | Example x1d/x1dints product |
|---|---:|---:|---|---|---|---:|---|
| `WASP-43` | `WASP-43` | `1366` | `jw01366-o011_t002_miri_p750l-slitlessprism` | `MIRI/SLITLESS` | `P750L` | 31 | `jw01366011001_04103_00002-seg003_mirimage_x1dints.fits` |
| `WASP-43b` | `WASP-43` | `1366` | `jw01366-o011_t002_miri_p750l-slitlessprism` | `MIRI/SLITLESS` | `P750L` | 31 | `jw01366011001_04103_00002-seg003_mirimage_x1dints.fits` |
| `GJ 1214` | `GJ1214` | `1803` | `jw01803-o001_t001_miri_p750l-slitlessprism` | `MIRI/SLITLESS` | `P750L` | 51 | `jw01803001001_04103_00002-seg007_mirimage_x1dints.fits` |
| `GJ1214` | `GJ1214` | `1803` | `jw01803-o001_t001_miri_p750l-slitlessprism` | `MIRI/SLITLESS` | `P750L` | 51 | `jw01803001001_04103_00002-seg007_mirimage_x1dints.fits` |
| `HD 189733` | `HD-189733B` | `2001` | `jw02001-o001_t001_miri_p750l-slitlessprism` | `MIRI/SLITLESS` | `P750L` | 32 | `jw02001-o001_t001_miri_p750l-slitlessprism_x1dints.fits` |
| `HD 209458` | `HD-209458` | `2667` | `jw02667-o051_t001_miri_p750l-slitlessprism` | `MIRI/SLITLESS` | `P750L` | 9 | `jw02667-o051_t001_miri_p750l-slitlessprism_x1dints.fits` |

## Source support

The MAST instrument names used in the query are the documented JWST instrument/configuration values `MIRI/SLIT` and `MIRI/SLITLESS`; STScI lists those exact values in its MAST JWST instrument-name update notice ([STScI MAST newsletter](https://archive.stsci.edu/contents/newsletters/march-2023/jwst-instrument-names-updated-in-mast)).

For MIRI LRS, `P750L` is the MIRI imager filter-wheel element used for the low-resolution spectroscopy double prism. STScI's JWST documentation says MIRI LRS/slitless modes use the `P750L` double prism and cover roughly 5-14 microns ([JWST MIRI filters and dispersers](https://jwst-docs.stsci.edu/jwst-mid-infrared-instrument/miri-instrumentation/miri-filters-and-dispersers), [JWST MIRI low-resolution spectroscopy](https://jwst-docs.stsci.edu/jwst-mid-infrared-instrument/miri-observing-modes/miri-low-resolution-spectroscopy)).

`WASP-43b` is independently documented in the literature as a JWST MIRI/LRS phase-curve target: Bell et al. state that they observed a full-orbit phase curve of WASP-43b with MIRI/LRS as part of the Transiting Exoplanet Community Early Release Science Program ([arXiv:2301.06350](https://arxiv.org/abs/2301.06350)). Follow-up analyses also identify the data as a JWST MIRI/LRS phase-curve observation of WASP-43b ([arXiv:2404.16488](https://arxiv.org/abs/2404.16488), [arXiv:2406.03490](https://arxiv.org/abs/2406.03490)).

## Reproduction script

No HITRAN or other login credentials are needed for this MAST verification. This uses public JWST archive metadata/products through `astroquery`.

```bash
python -m pip install astroquery astropy
python - <<'PY'
from astroquery.mast import Observations

Observations.TIMEOUT = 120

candidates = [
    "WASP-43",
    "WASP-43b",
    "GJ 1214",
    "GJ1214",
    "HD 189733",
    "HD 209458",
]

for target in candidates:
    print(f"\n=== TARGET {target} ===")
    obs = Observations.query_criteria(
        objectname=target,
        obs_collection="JWST",
        instrument_name=["MIRI/SLIT", "MIRI/SLITLESS"],
        filters="P750L",
    )

    print("obs_rows", len(obs))
    cols = [
        c for c in [
            "obsid", "obs_id", "target_name", "proposal_id",
            "instrument_name", "filters", "dataproduct_type",
            "calib_level", "t_obs_release"
        ]
        if c in obs.colnames
    ]

    for row in obs:
        print("OBS", {c: str(row[c]) for c in cols})

    if len(obs) == 0:
        continue

    products = Observations.get_product_list(obs)
    pcols = products.colnames

    matches = []
    for p in products:
        fn = str(p["productFilename"]) if "productFilename" in pcols else ""
        sub = str(p["productSubGroupDescription"]) if "productSubGroupDescription" in pcols else ""
        if fn.endswith(".fits") and ("_x1d" in fn or "_x1dints" in fn or sub in {"X1D", "X1DINTS"}):
            matches.append(p)

    print("product_rows", len(products))
    print("x1d_like_rows", len(matches))

    for p in matches[:10]:
        keep = [
            c for c in [
                "obsID", "obs_id", "parent_obsid",
                "productFilename", "productSubGroupDescription",
                "productType", "calib_level", "description", "dataURI"
            ]
            if c in pcols
        ]
        print("PROD", {c: str(p[c]) for c in keep})
PY
```

## Minimal expected pass condition

For `techno-search jwst-miri-lrs-search WASP-43`, the query should find:

- `obs_id`: `jw01366-o011_t002_miri_p750l-slitlessprism`
- `proposal_id`: `1366`
- `instrument_name`: `MIRI/SLITLESS`
- `filters`: `P750L`
- at least one `x1dints` FITS product, for example `jw01366011001_04103_00002-seg003_mirimage_x1dints.fits`

If your downloader prefers level-3 products, `HD 189733` and `HD 209458` both showed source-level/observation-level `*_p750l-slitlessprism_x1dints.fits` products in addition to exposure/segment-level products.
>>>>>>> 0f03d7a (  Adding a JWST Note)
