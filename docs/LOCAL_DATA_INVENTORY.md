# LOCAL DATA INVENTORY

## Purpose

This is the GitHub-visible artifact map for data and generated products used by
the Technosignature Search project. It is intentionally sanitized so future
agents can understand the artifact topology from GitHub without seeing local
machine paths, hostnames, raw data payloads, SQLite databases, or generated run
outputs.

Machine-specific snapshots belong in `docs/LOCAL_DATA_INVENTORY.local.md`.
That file is generated locally by `scripts/create_data_inventory.sh`, is
ignored by Git, and must not be committed.

## Core Rule

Ignore the payloads, commit the map.

Large science data, logs, caches, SQLite databases, and generated run products
stay out of Git. Reproducibility context belongs in committed docs, scripts,
schemas, checksums, manifests, small fixtures, and tests.

## Git-Ignored Artifact Topology

| Path or pattern | Producer | Purpose | Git policy |
|---|---|---|---|
| `data/bl_hits/` | `scripts/download_bl_hits.sh`, `scripts/fetch_bl_alternative.sh`, `scripts/ingest_gbt_cadence.py` | Breakthrough Listen / GBT HDF5 inputs and turboSETI hit tables | Ignored payloads |
| `data/calibration_corpus/` | `scripts/download_calibration_corpus.sh`, `scripts/fetch_bl_calibration_targets.sh`, `scripts/run_calibration_corpus_pipeline.sh` | Real `.dat` hit tables, provenance sidecars, calibration gate outputs | Ignored payloads; commit sanitized summaries only |
| `data/extended_corpus/` | `scripts/download_bl_extended_corpus.sh` | Held-out GBT evidence inputs from current BL Open Data HDF5 records and any derived hit tables for DECISION-134 hardening | Ignored payloads; commit review-safe manifests only |
| `data/meerkat_hits/` | `scripts/ingest_meerkat_hits.py` | MeerKAT BLUSE false-positive corpus and normalized local derivatives | Ignored payloads; commit methodology only |
| `data/injection_grid/` | `scripts/setigen_injection_grid.py` | Setigen injection-recovery HDF5 files, derived hit tables, and local grid manifests | Ignored payloads; commit review-safe summaries only |
| `results/` | Pipeline CLIs and scan workflows | Local pipeline reports, manifests, scan outputs, and candidate artifacts | Ignored except `results/scans/` |
| `results/scans/` | `.github/workflows/weekly_scan.yml` | Review-safe scheduled scan summaries | Tracked by workflow when intentionally committed |
| `logs/` | SQLite operational log CLIs | Local top-level SQLite operational logs and backups | Ignored payloads |
| `cache/` | Live-provider and catalog-cache helpers | Local provider metadata caches | Ignored payloads |
| `artifacts/` | Local validation, export, and scratch workflows | Generated intermediate products | Ignored payloads |

## Broadly Ignored File Classes

The repository ignores raw or generated science payloads wherever they appear:

- HDF5: `*.h5`, `*.hdf5`
- radio filterbank: `*.fil`
- FITS: `*.fits`, `*.fit`, `*.fits.gz`
- turboSETI hit tables: `*.dat`
- array/model products: `*.npy`, `*.npz`, `*.parquet`, `*.feather`, `*.pkl`,
  `*.pickle`, `*.joblib`
- SQLite/log products: `*.sqlite`, `*.sqlite3`, `*.db`, `*.db-wal`,
  `*.db-shm`, journal files, and `*.log`

Tiny intentional test fixtures are allowed under `tests/fixtures/`, including
the tracked sample turboSETI `.dat` fixture used by parser tests.

## Expected Local Evidence Streams

The DECISION-134 AI hardening production blocker is not closed by paths merely
existing on disk. Review credit requires populated, provenance-preserving
evidence streams and independent-method citizen-science review.

Expected ignored local evidence streams:

1. Extended GBT corpus: `data/extended_corpus/<target>/` HDF5 inputs and any
   derived hit tables
2. MeerKAT BLUSE corpus: `data/meerkat_hits/`
3. Injection-recovery grid: `data/injection_grid/`
4. Calibration corpus holdouts: `data/calibration_corpus/*.dat`

Committed evidence should be limited to review-safe summaries, methodology,
provenance manifests, checksums, schemas, and tests. No committed artifact
constitutes a detection claim, external validation, or external-submission
authorization.

## Local Inventory Snapshot

To inspect the current workstation without committing local paths:

```bash
bash scripts/create_data_inventory.sh
```

The command writes `docs/LOCAL_DATA_INVENTORY.local.md`. It may include absolute
local paths and machine details to help the current operator, so it is ignored
by Git.

## Agent Checklist

Before committing changes that touch data acquisition, logs, calibration, or
pipeline outputs:

1. Confirm the relevant producer script or CLI output path.
2. Confirm `.gitignore` covers the generated payloads.
3. Keep or add a committed sanitized map, manifest, checksum, schema, or test
   when future GitHub-only agents need continuity.
4. Verify `git add --dry-run .` does not stage unintended artifacts.
5. Preserve conservative scientific language: candidate signal, anomaly,
   follow-up target, or technosignature-interest candidate only.
