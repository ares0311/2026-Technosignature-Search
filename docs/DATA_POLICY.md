# DATA POLICY

## Purpose

Define how data should be handled in the Technosignature Search repository.

This project uses public astronomical datasets that may be large, complex, and governed by external citation or usage requirements. The repository should remain lightweight and reproducible.

---

## General Rules

Do not commit large raw data files.

Do not commit:

- Breakthrough Listen raw or reduced radio data files
- large HDF5 files
- filterbank files
- large FITS files
- downloaded survey images
- bulk catalog dumps
- cache directories
- local SQLite databases, journals, write-ahead logs, and raw log files
- generated model arrays, serialized models, and temporary calibration products
- machine-specific data inventories containing absolute local paths or hostnames
- private credentials
- API tokens
- generated intermediate products

Live-provider metadata caches belong under `cache/live_providers/` by default or under the local directory named by `TECHNO_SEARCH_LIVE_CACHE_DIR`. These cache files are ignored local artifacts and should be regenerated from recorded provider request provenance when needed.

Future catalog cache metadata belongs under `cache/catalog_metadata/` by default or under the local directory named by `TECHNO_SEARCH_CATALOG_CACHE_DIR`. This policy is not catalog ingestion; it only defines where future local metadata should live and what must stay out of Git.

Tiny live metadata fixtures under `tests/fixtures/live_metadata/` are allowed only when they contain normalized metadata and provenance summaries, not bulk provider data or candidate interpretation.

Small synthetic fixtures are allowed.

## GitHub-Visible Artifact Map

Other coding agents can only see what is committed to GitHub. Do not solve that
by committing local payloads. Preserve continuity by committing a sanitized
artifact map instead.

The committed map must explain:

- expected ignored directories and filename patterns;
- scripts or CLI commands that create each artifact class;
- review-safe manifests, checksums, and sidecar expectations;
- which artifacts are local-only and which small fixtures are intentionally
  tracked;
- scientific guardrails and any production blockers the artifacts support.

The map must not include:

- absolute user-machine paths;
- hostnames or machine identifiers;
- raw directory listings from local workstations;
- large data, SQLite databases, logs, caches, or generated run outputs.

`docs/LOCAL_DATA_INVENTORY.md` is the committed sanitized map. A machine-local
snapshot may be generated for the current workstation as
`docs/LOCAL_DATA_INVENTORY.local.md`; that local snapshot is ignored and must
not be committed.

---

## Recommended Data Layout

```text
data/
  raw/          ignored
  interim/      ignored
  processed/    ignored except tiny examples
  external/     ignored
  examples/     small curated examples only
```

```text
tests/
  fixtures/     tiny synthetic test data
```

---

## Provenance Requirements

Every generated candidate should record:

- source dataset
- query parameters
- download time
- processing code version
- config version
- thresholds used
- candidate ID
- input file hashes where practical
- external catalog versions where practical

---

## Real Data Examples

Real data examples should be:

- small
- clearly sourced
- reproducible
- non-sensitive
- legally redistributable

If redistribution is unclear, provide a script or instructions to fetch the data instead of committing it.

---

## Synthetic Fixtures

Synthetic fixtures are preferred for tests.

Examples:

- artificial radio narrowband hit
- artificial RFI-like hit
- mock infrared excess source
- mock blended infrared source
- mock vanishing-source candidate
- mock proper-motion false positive

---

## External Data Licensing

This repository does not relicense external datasets.

Users must follow the original terms and citation requirements of:

- Breakthrough Listen
- MAST
- Gaia
- NASA/IPAC IRSA
- VizieR
- SIMBAD
- WISE / AllWISE / CatWISE
- 2MASS
- other source archives

---

## Git Hygiene

Large files should not be committed.

If large data is accidentally committed:

1. stop development
2. remove the file
3. purge from Git history if necessary
4. update `.gitignore`
5. document the issue in `docs/PROJECT_STATUS.md`

Before any commit touching data acquisition, pipeline outputs, logs, or
calibration artifacts, verify that the repository remains safe under the
standard staging cadence:

```bash
git add --dry-run .
```

That dry run must not show generated payloads. If future agents need context,
update the sanitized artifact map rather than committing local payloads.

---

## Default Testing Policy

Default tests must use synthetic fixtures and mocked services.

Live-data tests must be marked:

```python
@pytest.mark.integration_live
```

Live-data tests should not run by default.
