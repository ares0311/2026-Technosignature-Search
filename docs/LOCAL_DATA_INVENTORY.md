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
| `data/meerkat_hits/` | `scripts/ingest_meerkat_hits.py`, `techno-search semisupervised-corpus-build`, `techno-search semisupervised-scorer-train` | Verified MeerKAT BLUSE false-positive corpus when available, real turboSETI `.dat` normalized training corpora, and local scorer model/metadata payloads | Ignored payloads; commit methodology only |
| `data/injection_grid/` | `scripts/setigen_injection_grid.py` | Setigen injection-recovery HDF5 files, derived hit tables, and local grid manifests | Ignored payloads; commit review-safe summaries only |
| `results/` | Pipeline CLIs and scan workflows | Local pipeline reports, manifests, scan outputs, and candidate artifacts | Ignored except curated scan summaries |
| `results/scans/` | `.github/workflows/weekly_scan.yml` | Review-safe scheduled scan summaries; generated local `RUN-*` directories stay ignored unless deliberately reviewed and force-added | Commit curated summaries/manifests only |
| `logs/` | SQLite operational log CLIs | Local top-level SQLite operational logs and backups | Ignored payloads |
| `cache/` | Live-provider and catalog-cache helpers | Local provider metadata caches | Ignored payloads |
| `artifacts/` | Local validation, export, and scratch workflows | Generated intermediate products | Ignored payloads |

## Committed Metadata And Scheduling Artifacts

These are intentionally small, GitHub-visible maps that keep future agents from
depending on local-only state:

| Path | Producer | Purpose | Git policy |
|---|---|---|---|
| `data/bl_hprc_seed_targets.csv` | Sampling design workflow | Small stratified/null-result target sample | Committed map |
| `data/bl_hprc_full_targets_vizier.csv` | `scripts/acquire_bl_hprc_full_catalog.py` | Full HPRC catalog metadata export from the approved source workflow | Committed metadata map |
| `data/bl_hprc_full_seed_targets.csv` | `scripts/build_bl_hprc_full_seed.py` | Full HPRC seed target metadata used for local-coverage target selection | Committed metadata map |
| `data/target_sample_manifest.json` | Sampling design workflow | Stratified sample manifest retained for null-result defensibility | Committed manifest |
| `docs/data_collection_status.json` | Data acquisition entrypoints | Compact tracked data-collection status and per-target outcomes | Committed status manifest |
| `data_selection/target_priority_queue.csv` | `techno-search build-target-priority-queue` | Metadata-first live-search target queue for local-coverage novelty selection | Committed scheduling artifact |
| `data_selection/data_role_registry.yaml` | Data-selection policy workflow | Role separation for live-search metadata and local-cache status | Committed policy artifact |

The first target-priority queue contains 1,703 unique target IDs derived from
the 1,709-row full HPRC metadata seed. It records 1,683 targets queued for
product metadata discovery, 4 metadata-retry targets, and 16 already-acquired
local-cache controls. `HIP75676` appears in the extended-corpus status manifest
but not in the full HPRC seed CSV, so it is documented as a source-list
limitation rather than forced into the queue.

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
2. Semi-supervised scorer corpus/model payloads: `data/meerkat_hits/`
   (verified MeerKAT BLUSE when available, or normalized real turboSETI `.dat`
   corpora built locally)
3. Injection-recovery grid: `data/injection_grid/`
4. Calibration corpus holdouts: `data/calibration_corpus/*.dat`

Committed evidence should be limited to review-safe summaries, methodology,
provenance manifests, checksums, schemas, and tests. No committed artifact
constitutes a detection claim, external validation, or external-submission
authorization.

Current committed review-safe DECISION-134 evidence map:

- `tests/fixtures/ai_hardening_hip17147_zero_hit_evidence.json` records the
  first bounded HIP17147 `data/extended_corpus` HDF5 acquisition, checksums,
  zero-hit turboSETI result, method abstentions, and remaining blockers.
- `docs/ai_hardening_evidence/HIP17147_ZERO_HIT_EVIDENCE.md` summarizes the
  same evidence for future agents. Raw HDF5, `.dat`, and `.log` payloads remain
  ignored local artifacts.
- `tests/fixtures/ai_hardening_hip39826_zero_hit_evidence.json` records the
  second bounded HIP39826 `data/extended_corpus` HDF5 acquisition, checksums,
  zero-hit turboSETI result, method abstentions, and remaining blockers.
- `docs/ai_hardening_evidence/HIP39826_ZERO_HIT_EVIDENCE.md` summarizes the
  second bounded attempt. Raw HDF5, `.dat`, and `.log` payloads remain ignored
  local artifacts.
- `tests/fixtures/ai_hardening_injection_grid_closure_evidence.json` records
  the DECISION-134 closure evidence: Voyager 1 GBT HDF5 checksum, setigen
  injection-grid manifest checksum, 75/75 recovered injections, 256 valid
  turboSETI hit rows, method-family reviews, abstentions, and local-only
  production scope.
- `docs/ai_hardening_evidence/INJECTION_GRID_CLOSURE_EVIDENCE.md` summarizes
  the same closure evidence for future GitHub-only agents. Raw HDF5, generated
  injected HDF5, `.dat`, and `.log` payloads remain ignored local artifacts.

### 2026-07-02 Extended-Corpus Download

The user ran the System-Directive-compliant download command:

```bash
git pull origin main
caffeinate -i bash scripts/download_bl_extended_corpus.sh --manifest data/target_sample_manifest.json 2>&1 | tee /tmp/bl_extended_corpus_download.log
```

Measured result from pasted terminal output:

- 31 manifest targets checked.
- 11 new URL-available HDF5 downloads completed.
- 6 existing HDF5 targets were reused.
- 17 URL-available HDF5 targets were processed.
- 14 targets had no current HDF5 URL or were otherwise skipped.

New ignored local HDF5 payload targets included `HIP113421`, `HIP26779`,
`HIP67275`, `HIP74981`, `HIP16852`, `HIP99427`, `HIP66704`, `HIP39826`,
`HIP23311`, `HIP82860`, and `HIP17147`. These are local calibration and
generalization aids only. They are ignored payloads under `data/extended_corpus/`
and must not be committed by `git add .`.

### 2026-07-02 Extended-Corpus turboSETI + Production Scan

After the download above, local processing completed with:

```bash
caffeinate -i bash scripts/run_turboseti_on_extended_corpus.sh
caffeinate -i bash scripts/run_pipeline_on_bl_data.sh --dat-dir data/extended_corpus
caffeinate -i bash scripts/run_production_scan.sh --dat-dir data/extended_corpus
```

Measured result:

- turboSETI processed 8 newly downloaded HDF5 files, skipped 9 existing `.dat`
  files, and failed 0 targets.
- `data/extended_corpus/` now has 17 local `.dat` files; all 17 are zero-hit
  observations at the configured turboSETI threshold.
- Candidate-report generation completed 17/17 `.dat` files with 0 failures.
- Production scan `RUN-2026-07-02_130330Z-3ZNT-prod-scan` scanned 11 pending
  targets, failed 0, flagged 0 escalations, and left 0 pending targets.
- The run produced 0 follow-up entries and 39 non-detection/no-follow-up ledger
  entries across the current local result set.
- `ai-hardening-gate-summary` remained closed with `production_promotion_allowed:
  true` for local operations only; no detection, discovery, expert-review,
  external-validation, or external-submission claim was made.

These `.dat`, `.log`, production-run, and report artifacts remain ignored local
payloads. GitHub-visible continuity is this measured map plus the committed
scripts and tests, not the payloads.

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
