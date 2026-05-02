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
- private credentials
- API tokens
- generated intermediate products

Live-provider metadata caches belong under `cache/live_providers/` by default or under the local directory named by `TECHNO_SEARCH_LIVE_CACHE_DIR`. These cache files are ignored local artifacts and should be regenerated from recorded provider request provenance when needed.

Future catalog cache metadata belongs under `cache/catalog_metadata/` by default or under the local directory named by `TECHNO_SEARCH_CATALOG_CACHE_DIR`. This policy is not catalog ingestion; it only defines where future local metadata should live and what must stay out of Git.

Tiny live metadata fixtures under `tests/fixtures/live_metadata/` are allowed only when they contain normalized metadata and provenance summaries, not bulk provider data or candidate interpretation.

Small synthetic fixtures are allowed.

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

---

## Default Testing Policy

Default tests must use synthetic fixtures and mocked services.

Live-data tests must be marked:

```python
@pytest.mark.integration_live
```

Live-data tests should not run by default.
