# Research Note: Machine-readable Breakthrough Listen HPRC Target List

Date checked: 2026-07-04

## Agent Instructions

This note is intended to be consumed by a coding agent. Treat all URLs, catalog IDs, table names, column names, and row counts below as verified facts from the cited sources or from the live retrieval described here. Do not substitute adjacent-looking identifiers, do not reconstruct target properties from other catalogs, and do not silently "correct" the row count to match project memory.

Required implementation outcome:

1. Add or generate a full Breakthrough Listen HPRC stellar target CSV from VizieR source `J/PASP/129/E4501/table1`.
2. Preserve the raw VizieR TSV response with metadata comments for provenance.
3. Validate the parsed row count against the live VizieR table. As of this check, the expected count is `1709`.
4. Treat any row-count change as a data-source change requiring review, not as a parser bug by default.
5. Do not assert a Breakthrough Listen concurrent-download policy. Only the `500`-file query-result cap was found in published archive documentation.

Recommended output files for the codebase:

```text
data/bl_hprc_full_targets_vizier_raw.tsv
data/bl_hprc_full_targets_vizier.csv
```

## Bottom line

A real machine-readable stellar target list for Isaacson et al. 2017 exists in VizieR. The confirmed catalog is **`J/PASP/129/E4501`**, not `J/PASP/129/054501`.

Use this table for the full stellar target list:

```text
VizieR catalog: J/PASP/129/E4501
Table: J/PASP/129/E4501/table1
Table title: Stellar Targets
Machine-readable TSV:
https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=J/PASP/129/E4501/table1&-out.max=unlimited&-out=*
```

The current VizieR machine-readable table returns **1,709 stellar rows**. That is consistent with the paper abstract wording of 60 nearest stars plus 1,649 Hipparcos stars, and is not 1,702 rows. Do not force the row count to 1,702 in code.

URL-encoded form suitable for scripts:

```text
https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=J%2FPASP%2F129%2FE4501%2Ftable1&-out.max=unlimited&-out=%2A
```

Primary sources:

- VizieR landing page: [J/PASP/129/E4501, "Search for extraterrestrial intelligence"](https://cdsarc.cds.unistra.fr/viz-bin/cat/J/PASP/129/E4501)
- VizieR machine-readable TSV endpoint: [J/PASP/129/E4501/table1 as TSV](https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=J/PASP/129/E4501/table1&-out.max=unlimited&-out=*)
- arXiv paper page: [arXiv:1701.06227](https://arxiv.org/abs/1701.06227)
- Published article DOI: [10.1088/1538-3873/aa5800](https://doi.org/10.1088/1538-3873/aa5800)
- VizieR dataset citation from the TSV metadata: `doi:10.26093/cds/vizier.61303501`

## Confirmed VizieR Details

The VizieR ASU-TSV response identifies the resource as:

```text
#Name: J/PASP/129/E4501
#Title: Search for extraterrestrial intelligence (Isaacson+, 2017)
#INFO cites=bibcode:2017PASP..129e4501I
#INFO journal=PASP
#INFO original_date=2017
#INFO reference_url=https://cdsarc.cds.unistra.fr/viz-bin/cat/J/PASP/129/E4501
#INFO citation=doi:10.26093/cds/vizier.61303501

#Table J_PASP_129_E4501_table1:
#Name: J/PASP/129/E4501/table1
#Title: Stellar Targets
```

The tempting identifier `J/PASP/129/054501` was tested and rejected: VizieR returned `Table or Catalog not found`. The confirmed identifier uses the PASP article-code form `E4501`.

Do not add fallback logic that tries `J/PASP/129/054501`; that fallback would encode a known-bad identifier.

## Table Schema

The current `table1` columns are:

| Column | Meaning | Unit / format |
|---|---|---|
| `Star` | Star name / primary identifier | text |
| `RAJ2000` | Right ascension, J2000 | sexagesimal |
| `DEJ2000` | Declination, J2000 | sexagesimal |
| `Ep` | Epoch | year, mostly `2000` |
| `Vmag` | V magnitude | mag |
| `SpType` | Spectral type | text |
| `Dist` | Distance | pc |
| `pmRA` | Proper motion in RA, including cos(dec) factor | arcsec/yr |
| `pmDE` | Proper motion in Dec | arcsec/yr |
| `SimbadName` | SIMBAD name added by CDS | text |

Minimum fields requested by the project are present: star/HIP identifier, RA/Dec, distance, and spectral type.

## Parser Requirements

VizieR ASU-TSV includes metadata comments, a header row, unit rows, and separator rows. A parser must:

1. Keep the raw TSV unchanged for provenance.
2. Ignore lines starting with `#` for CSV data extraction.
3. Detect the column header line where the first field is exactly `Star`.
4. Skip units and separator rows after the header.
5. Preserve sexagesimal `RAJ2000` and `DEJ2000` strings unless a downstream feature explicitly needs numeric coordinates.
6. Preserve all columns listed in the schema table.
7. Validate that required columns are present before writing the normalized CSV.
8. Emit a clear error if the row count differs from the expected count and include the observed count in the error message.

Required columns:

```text
Star, RAJ2000, DEJ2000, Ep, Vmag, SpType, Dist, pmRA, pmDE, SimbadName
```

## Reproduction Commands

This uses only the Python standard library.

```python
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import csv

params = {
    "-source": "J/PASP/129/E4501/table1",
    "-out.max": "unlimited",
    "-out": "*",
}
url = "https://vizier.cds.unistra.fr/viz-bin/asu-tsv?" + urlencode(params)

req = Request(url, headers={"User-Agent": "TechnosignatureSearch/1.0"})
text = urlopen(req, timeout=60).read().decode("utf-8", "replace")

raw_path = Path("data/bl_hprc_full_targets_vizier_raw.tsv")
csv_path = Path("data/bl_hprc_full_targets_vizier.csv")
raw_path.parent.mkdir(parents=True, exist_ok=True)
raw_path.write_text(text, encoding="utf-8")

header = None
rows = []

for line in text.splitlines():
    if not line or line.startswith("#"):
        continue

    fields = [field.strip() for field in line.split("\t")]

    if fields[0] == "Star":
        header = fields
        continue

    # Skip units and separator rows emitted by VizieR ASU-TSV.
    if header is None:
        continue
    if fields[0] in {"", "---"} or set(fields[0]) <= {"-"}:
        continue

    rows.append(dict(zip(header, fields)))

print(f"rows={len(rows)}")
print(rows[0])
print(rows[-1])

with csv_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=header)
    writer.writeheader()
    writer.writerows(rows)

# Expected as of 2026-07-04 from live VizieR:
assert len(rows) == 1709
```

Hardened production version with required-column validation:

```python
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import csv

EXPECTED_COLUMNS = [
    "Star",
    "RAJ2000",
    "DEJ2000",
    "Ep",
    "Vmag",
    "SpType",
    "Dist",
    "pmRA",
    "pmDE",
    "SimbadName",
]
EXPECTED_ROWS_AS_OF_2026_07_04 = 1709

params = {
    "-source": "J/PASP/129/E4501/table1",
    "-out.max": "unlimited",
    "-out": "*",
}
url = "https://vizier.cds.unistra.fr/viz-bin/asu-tsv?" + urlencode(params)

req = Request(url, headers={"User-Agent": "TechnosignatureSearch/1.0"})
text = urlopen(req, timeout=60).read().decode("utf-8", "replace")

raw_path = Path("data/bl_hprc_full_targets_vizier_raw.tsv")
csv_path = Path("data/bl_hprc_full_targets_vizier.csv")
raw_path.parent.mkdir(parents=True, exist_ok=True)
raw_path.write_text(text, encoding="utf-8")

header = None
rows = []

for line in text.splitlines():
    if not line or line.startswith("#"):
        continue

    fields = [field.strip() for field in line.split("\t")]

    if fields[0] == "Star":
        header = fields
        missing = [col for col in EXPECTED_COLUMNS if col not in header]
        if missing:
            raise RuntimeError(f"VizieR schema changed; missing columns: {missing}")
        continue

    if header is None:
        continue

    first = fields[0].strip()
    if first == "" or set(first) <= {"-"}:
        continue

    row = dict(zip(header, fields))
    if row.get("Star"):
        rows.append(row)

if header is None:
    raise RuntimeError("No Star header row found in VizieR TSV response")

if len(rows) != EXPECTED_ROWS_AS_OF_2026_07_04:
    raise RuntimeError(
        "VizieR row count changed for J/PASP/129/E4501/table1: "
        f"expected {EXPECTED_ROWS_AS_OF_2026_07_04}, observed {len(rows)}. "
        "Review the source before accepting this update."
    )

with csv_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=EXPECTED_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
```

Verification output from the live VizieR pull:

```text
URL: https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=J%2FPASP%2F129%2FE4501%2Ftable1&-out.max=unlimited&-out=%2A
data_rows: 1709
first Star: HIP2
last Star: HIP118310
```

## arXiv and IOPscience Check

The arXiv page for `1701.06227` confirms the paper and abstract. The abstract says the authors selected 60 nearest stars and added 1,649 Hipparcos stars, which totals 1,709 stellar targets. The arXiv page shows paper PDF and TeX source links, but no explicit ancillary data-table link in the page metadata checked on 2026-07-04. Source: [arXiv:1701.06227](https://arxiv.org/abs/1701.06227).

The IOPscience article page is the article-of-record DOI page, but direct automated access was blocked in this environment. No project-critical claim here depends on IOPscience, because CDS/VizieR provides the machine-readable table and citation metadata directly.

## Breakthrough Listen Open Data Archive Policy Check

Published documentation found:

- The public Open Data Archive page says Breakthrough Listen files can be several GB and links to backend API documentation. It also states: **"All queries are limited to return at most 500 files"**. Source: [Breakthrough Listen Open Data Archive](https://seti.berkeley.edu/opendata).
- The backend API documentation linked from that page is the GitHub README for `ggroode/bl-opendata`. It documents endpoints including `api/list-targets`, `api/list-telescopes`, `api/list-file-types`, and `api/query-files`, and documents `api/query-files` parameters including `target`, `telescopes`, `file-types`, `pos-ra`, `pos-dec`, `pos-rad`, `time-start`, `time-end`, `freq-start`, `freq-end`, `limit`, `cadence`, `quality`, and size filters. Source: [bl-opendata README](https://github.com/ggroode/bl-opendata/blob/master/README.md).

No published simultaneous-request or concurrent-download limit was found in the checked public archive page, SETI Berkeley open-data pages, or the linked backend API README. Therefore, code should not hard-code a claimed BL concurrency policy such as "N simultaneous downloads allowed" unless a future source documents one.

Implementation recommendation, clearly not a published BL policy: default discovery and downloads to serial or a user-configurable low concurrency, respect the documented 500-result query cap, and expose `--max-concurrent` as an operator setting rather than encoding an asserted archive limit.

Agent-safe policy wording to use in code comments or docs:

```text
The BL Open Data Archive documentation checked on 2026-07-04 documents a 500-file query-result cap. No published concurrent-request or concurrent-download limit was found. This client therefore defaults to conservative, configurable concurrency rather than claiming an archive-published limit.
```

Do not write comments such as "BL allows 4 concurrent downloads" or "BL rate limit is N requests/sec" unless a future source is added to this note.

## Coding-Agent Checklist

1. Use VizieR source `J/PASP/129/E4501/table1`.
2. Download through `asu-tsv` with `-out.max=unlimited` and `-out=*`.
3. Preserve the raw TSV with metadata comments for provenance.
4. Parse only non-comment data rows after the `Star` header.
5. Validate that current row count is 1,709, not 1,702.
6. Do not use `J/PASP/129/054501`; it was checked and is not the VizieR catalog ID.
7. For BL Open Data Archive querying, honor the documented 500-file query-result limit.
8. Do not claim a documented concurrent-request limit unless a future BL/SETI source explicitly publishes one.
9. If integrating the generated CSV into tests, use schema and row-count assertions separately so schema drift and row-count drift produce distinct failures.
10. If the live VizieR row count changes, preserve the old raw TSV and new raw TSV for diff review before replacing project data.

## Acceptance Criteria

A coding task based on this note is complete only when:

- The raw VizieR TSV is saved unchanged.
- The normalized CSV contains exactly the required columns in this order: `Star`, `RAJ2000`, `DEJ2000`, `Ep`, `Vmag`, `SpType`, `Dist`, `pmRA`, `pmDE`, `SimbadName`.
- The normalized CSV has `1709` data rows when run against the 2026-07-04 VizieR response.
- The first parsed `Star` is `HIP2`.
- The last parsed `Star` is `HIP118310`.
- The implementation does not contain `J/PASP/129/054501`.
- Any BL Open Data Archive code treats the `500`-result limit as documented, and treats concurrency as configurable/local policy rather than published archive policy.

## Fallback Status

No fallback target list is needed. The requested full Isaacson et al. 2017 stellar target table is available in machine-readable form from VizieR.
