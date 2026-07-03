# Production Scan Runbook

**Purpose:** Durable UX rules for operating a continuous, prioritized, history-aware
production scan pipeline. The rules here are project-agnostic and can be adapted to any
pipeline that processes a directory of input files with a CLI tool.

---

## The Five Rules of Correct Production Scan Orchestration

These rules were derived from operational failures observed when running `run_production_scan.sh`.
Each rule fixes a concrete class of bug.

### Rule 1 — The scan script must acquire new data, not just report on old data

**Anti-pattern:** A "scan" script that only reads already-processed results and
reports on them. This produces the same output every run even if new input files
have been added.

**Correct pattern:**
1. Accept a `--dat-dir` (or equivalent) argument pointing to the raw input file directory.
2. Discover all input files at runtime with `discover_dat_files(dat_dir)`.
3. Call the actual pipeline (`run-pipeline` or equivalent) on each selected file.
4. Write pipeline output to a separate `--output-dir`.
5. After all targets are processed, run post-processing (scan-summary, RFI flagging,
   escalation gate, dashboard) over the output directory.

Post-processing is a separate step that runs *after* acquisition.

### Rule 2 — Every scan of a target must carry a stable cross-run identity

**Anti-pattern:** Generating a new scan index (e.g., `NEG-RUN1-001`, `NEG-RUN2-001`)
each run, making it impossible to tell whether two scan entries refer to the same
physical target observation.

**Correct pattern:**
- The **target stem** (filename without extension, e.g., `HIP99427`) is the stable
  cross-run identity. It is derived from the input file name and never changes.
- The **run ID** identifies a single execution of the scan script. It changes each run.
- The **scan index** (e.g., `20260620-143022-HIP99427`) is a convenience label for
  display only. It encodes timestamp + target stem and is never used as a database key.
- Store target-level history keyed by `target_stem`, not by run-scoped index.

### Rule 3 — The scan must detect already-searched targets and handle re-scans explicitly

**Anti-pattern:** Processing the same target on every run, with no awareness that it
has been seen before.

**Correct pattern:**
1. Maintain a **scan history file** (`results/scan_history.ndjson`) — an append-only
   NDJSON file where each line records one completed scan:
   ```json
   {"target_stem": "HIP99427", "run_id": "PROD-RUN-001", "scanned_at_utc": "...",
    "score": 0.72, "pathway": "follow_up", "dat_file": "/data/HIP99427.dat",
    "parent_run_id": null}
   ```
2. Before selecting a target, check the history. If the target has been scanned before:
   - In one-shot mode (default): skip it (queue only contains never-scanned targets).
   - In `--force-rescan` mode: include it at lower priority and set `parent_run_id`
     to the current `run_id` to link the two scans together.
3. The `parent_run_id` field creates a chain: given any scan record, follow
   `parent_run_id` links to see the full search history for that target.

### Rule 4 — The target selection algorithm must be visible at runtime

**Anti-pattern:** Scanning targets in filesystem order or silently skipping targets,
with no explanation printed to the terminal.

**Correct pattern:**
1. Use a **selection score** that is computed and printed for every target in the queue:
   - Base score: `0.50`
   - First-scan bonus: `+0.08` (targets never seen before get priority)
   - Re-scan penalty: `-0.04` per prior scan, capped at `-0.12`
2. Before the scan loop starts, print the full ranked queue with selection scores and
   rationale strings, e.g.:
   ```
   [ 1]* HIP99427    score=0.5800  (never scanned +0.08 boost)
   [ 2]* HIP17147    score=0.5800  (never scanned +0.08 boost)
   [ 3]  Voyager1    score=0.4600  (scanned 1 time  -0.04 penalty)
   ```
3. Each target selected by the loop prints its rationale before processing begins.

The selection algorithm is defined in `src/techno_search/prod_scan_queue.py` and
surfaced via `techno-search prod-target-queue`.

### Rule 5 — The scan must run continuously until stopped, not exit after a finite queue

**Anti-pattern:** A scan script that exits after processing a fixed list of targets.
This makes the script useless for monitoring newly deposited data files.

**Correct pattern:**
1. Wrap the target selection and pipeline call in a `while true` loop.
2. Trap `SIGINT` and `SIGTERM` at the top of the script:
   ```bash
   STOPPING=0
   trap 'STOPPING=1; warn "Stopping after current target..."' INT TERM
   ```
3. Check `STOPPING` at the top of each loop iteration.
4. When the queue is exhausted:
   - **One-shot mode** (default): print a summary and exit normally.
   - **Continuous mode** (`--continuous`): sleep for `POLL_INTERVAL` seconds and then
     rebuild the queue, picking up any newly added input files.
5. Never use `exit` inside a pipeline sub-process; return exit codes to the wrapper.

---

## CLI Architecture

These CLI commands implement the runbook rules:

| Command | Purpose |
|---|---|
| `techno-search prod-target-queue --dat-dir PATH [--history-file F] [--force]` | Show ranked queue with selection scores and rationale |
| `techno-search prod-record-scan --target-stem T --run-id R --score S --pathway P --dat-file F --history-file H [--parent-run-id ID]` | Append a completed scan record to the history NDJSON |
| `techno-search scan-history-summary [--history-file H] [--dat-dir D]` | Show all prior scans; count pending targets |
| `techno-search prod-scan INPUT_DIR OUTPUT_DIR [--track radio] [--force]` | Single-run batch scan with Rich spinner (does not use history) |
| `techno-search run-pipeline FILE TRACK OUTPUT_DIR [--semisupervised-model PATH]` | Process one input file through the pipeline; radio packets use the default local fitted scorer model when present |
| `techno-search radio-real-corpus-summary --dat-dir PATH [--dat-dir PATH2] [--hit-ndjson PATH] [--candidate-sample-limit N]` | Summarize local real `.dat` and normalized hit-NDJSON evidence for drift, cross-target RFI recurrence, fitted scorer integration, and bounded candidate-review survivors |
| `techno-search track-b-candidate-readiness CANDIDATE_JSON [--crossmatch-json CROSSMATCH_JSON] [--satellite-json SATELLITE_JSON]` | Fail-closed audit of whether a real candidate packet has the packet metadata and explicit evidence needed for Track B gate review; it never guesses missing sky position, observation time, telescope location, or catalog classifications |
| `techno-search track-b-unknown-candidate-gate CANDIDATE_JSON --crossmatch-json CROSSMATCH_JSON [--satellite-json SATELLITE_JSON]` | Combine explicit Track A crossmatch, optional satellite-match, RFI/artifact/cadence/anomaly/provenance evidence into the Phase 4 `unknown_candidate` gate without network lookups |
| `techno-search validate-all` | Must pass before any scan proceeds |

---

## Track A Known-Explanation Gate

`docs/technosignature_datasets_agent_brief.md` is the authoritative handoff for
the next model-hardening milestone. Before any production path emits a Track B
`unknown_candidate` label, the project must have a tested Track A baseline that
classifies or rejects known explanations: pulsars, FRBs, blazars/AGN, known
gamma-ray sources, satellite/transmitter matches, terrestrial RFI, instrument
artifacts, and noise.

Current status: Track A HTRU2 baseline training, known-source catalog
cross-matching, satellite-transmitter matching, and small historical replay are
implemented. Track B's Phase 4 gate is available as
`track-b-unknown-candidate-gate`, and `track-b-candidate-readiness` audits real
packet metadata/evidence completeness before the gate is attempted. The
unresolved anomaly/OOD threshold still blocks `eligible_for_unknown_candidate`
by construction. Production radio runs may produce non-detection ledgers,
follow-up-review triage rows, public-null context summaries, and
`low_confidence` known-explanation outcomes. They must not treat an unresolved
or ineligible Track B gate result as a detection, discovery, expert-review,
external-validation, or external-submission claim.

Track A acquisition work must follow the brief's source order and disk cap. Raw
downloads and temporary extraction products stay local in ignored paths:
`data_cache/`, `tmp_training/`, `tmp_features/`, `artifacts/`, `models/`, and
`metrics/`. GitHub-visible continuity belongs in sanitized manifests,
checksums, schemas, tests, and documentation. Do not download Kaggle SETI,
install/use Setigen, or depend on pretrained models for the first Track A
milestone.

---

## File Layout

```
data/bl_hits/                  ← raw turboSETI .dat input files
data_cache/                    ← ignored Track A raw/catalog cache
tmp_training/                  ← ignored temporary training workspace
tmp_features/                  ← ignored temporary feature extraction workspace
results/
  scan_history.ndjson          ← append-only cross-run scan log (gitignored)
  scans/
    PROD-RUN-YYYYMMDD-HHMMSS/ ← per-run audit directory (committed)
      validate_all.json
      *_scan_summary.json
      *_review_dashboard.json
      *_follow_ups.json
      *_non_detections.json
      cross_target_rfi.json
      escalations/
  prod_scan_output/            ← pipeline outputs per target (gitignored)
    HIP99427/
      HIP99427.json            ← scored candidate packet
      HIP99427.md              ← Markdown report
      HIP99427.manifest.json   ← report manifest
    HIP17147/
      zero/
        HIP17147__zero.manifest.json ← zero-hit observation manifest
```

Curated `results/scans/` summaries can be committed to GitHub as a durable
audit trail. Generated local `results/scans/RUN-*` directories are ignored by
default so the user's standard `git add .` cadence does not stage
machine-specific scan outputs accidentally. Commit only reviewed, sanitized
summaries/manifests deliberately.

---

## Scan History Schema

Each line in `results/scan_history.ndjson` is one JSON object:

```json
{
  "schema_version": "prod_scan_history_v1",
  "target_stem": "HIP99427",
  "run_id": "PROD-RUN-20260620-143022",
  "scanned_at_utc": "2026-06-20T14:30:22Z",
  "score": 0.72,
  "pathway": "follow_up",
  "dat_file": "/Users/you/project/data/bl_hits/HIP99427.dat",
  "parent_run_id": null
}
```

- `parent_run_id` is `null` for first scans; set to the *current* run ID for re-scans
  to create a linked chain.
- The file is append-only. Never delete or rewrite lines; add a new record instead.
- Gitignored because it contains absolute local paths and grows without bound.

---

## Data Directories

| Directory | Contents | Source |
|---|---|---|
| `data/bl_hits/` | Voyager 1 GBT `.dat` hit table (pipeline calibration) | `scripts/download_bl_hits.sh` |
| `data/extended_corpus/<TARGET>/` | GBT L-band HDF5 files from the stratified HPRC manifest | `scripts/download_bl_extended_corpus.sh --manifest data/target_sample_manifest.json` |
| `data_cache/raw/<SOURCE>/` | Ignored Track A source cache from `docs/technosignature_datasets_agent_brief.md` | Future Track A acquisition CLI |
| `tmp_training/`, `tmp_features/` | Ignored temporary Track A training/feature workspaces | Future Track A acquisition/training CLI |

HDF5 files in `data/extended_corpus/` must be processed with turboSETI before they can
enter the production scan queue.  Use `scripts/run_turboseti_on_extended_corpus.sh` (idempotent).

Zero-hit turboSETI `.dat` files are still evidence. `scripts/bl_fetch.py run-pipeline`
writes `zero_hit_observation_manifest_v1` records for hit tables with no non-comment
rows, and `prod-scan` turns those records into non-detection ledger entries with
score `0.0`, no follow-up requirement, and explicit negative evidence.

When `data/meerkat_hits/semisupervised_scorer.joblib` exists, radio
`run-pipeline` packets include local semi-supervised anomaly-score features and
provenance. Override the model with `--semisupervised-model PATH` when testing a
new fitted scorer. These scores are local triage evidence only; they do not
constitute detection, discovery, external validation, or external-submission
approval.

Check local scorer readiness with:

```bash
git pull origin main
.venv/bin/techno-search semisupervised-scorer-summary
```

The summary reads ignored local metadata/model artifacts by default and reports
`model_ready: true` only when both the real-corpus training metadata and fitted
joblib model are present.

Use the real-corpus summary after local radio data changes or scorer retraining:

```bash
git pull origin main
caffeinate -i .venv/bin/techno-search radio-real-corpus-summary \
  --dat-dir data/extended_corpus \
  --dat-dir data/bl_hits \
  --hit-ndjson data/meerkat_hits/meerkat_normalised_200000.ndjson \
  --max-hit-rows 5000 \
  --candidate-sample-limit 5
```

The command reads ignored local `.dat` payloads, the verified normalized
MeerKAT BLUSE hit corpus when present, and fitted models, but writes no payload
files. Treat its output as local validation evidence only. If the
`--hit-ndjson` file is omitted, the current local GBT `.dat` corpus remains
useful negative evidence but has only one hit-bearing target, so cross-target
RFI recurrence validation is expected to remain blocked.
Use a bounded `--max-hit-rows` value for routine operator checks; omit it only
for a full-corpus review. The scorer uses vectorized batch scoring, so the
current local 200,000-row MeerKAT review is practical as a diagnostic. Use
`--candidate-sample-limit 0` for counts-only checks, or a small value such as 5
to inspect the top automated review survivors plus a bounded rejected/control
sample. Rows labeled `needs_follow_up_review` are triage survivors only, not
detections or external-submission candidates. Known control targets such as
Voyager and stationary-frequency rows are counted separately and are not
promoted as follow-up candidates. Inspect `candidate_review.top_review_targets`
before individual rows; a survivor set concentrated on one target is a
source-context and instrumental-vetting task, not a discovery claim.

Before expanding `data/extended_corpus/`, verify current BL Open Data
availability from the committed manifest. This command queries the official
search pages, prints only target-to-HDF5 URL rows, and downloads no payloads:

```bash
git pull origin main
caffeinate -i bash scripts/download_bl_extended_corpus.sh \
  --manifest data/target_sample_manifest.json \
  --discover-only \
  --availability-output /tmp/bl_hdf5_availability.tsv
```

For a bounded download, the target limit applies to new URL-available downloads,
not raw manifest position and not already-downloaded HDF5 evidence. This
prevents resumed runs from stopping on unavailable manifest entries or evidence
that is already present locally:

```bash
git pull origin main
TECHNO_EXTENDED_CORPUS_MAX_TARGETS=5 caffeinate -i bash scripts/download_bl_extended_corpus.sh \
  --manifest data/target_sample_manifest.json
```

---

## Data Collection Status Reporting — Non-Negotiable

Real data-acquisition scripts and CLI commands (BL extended-corpus
downloads, JWST/MAST searches, photometry light-curve searches,
satellite/catalog acquisitions, and any future ones) must update the
tracked `docs/data_collection_status.json` manifest after a real successful
run, via `techno-search record-data-collection-status --script NAME
--summary-json '{...}'` (`src/techno_search/data_collection_status.py`).
This replaces pasting console output for review: the agent reviews progress
by `git pull`-ing this one small tracked file instead.

By default this also runs `git add`/`git commit`/`git push` for just that
one file — but **only when the current branch is `main`**
(`commit_and_push_status()` checks `git branch --show-current` and no-ops
otherwise). This guard exists because a real integration test in this
project's own suite runs the real download script end-to-end, and without
it, running the test suite silently auto-committed and pushed a fake
status entry to whatever branch happened to be checked out (caught and
fixed 2026-07-03). Do not remove or weaken this guard without an equally
strong replacement safeguard — the acquisition scripts run on the user's
real machine where `main` is always the real working branch (per
`CLAUDE.md`'s GIT SYNC DIRECTIVES), so this reliably distinguishes a real
run from a test/CI/agent-branch invocation.

When adding a new data-acquisition script or CLI command, call
`record_and_publish_data_collection_status()` (or the CLI wrapper) after a
real successful run, with a small JSON summary of real counts (found,
downloaded, skipped, reused, failed) -- not raw payload contents. Also
consider the `CLAUDE.md` "DATA COLLECTION PARALLELIZATION DIRECTIVE" when
building new acquisition scripts.

---

## Running the Script

### Full setup — extended corpus (recommended, 5 targets)

Run once after downloading the extended corpus:

```bash
git pull origin main

# Step 1: produce .dat hit tables (~5–15 min per target on M4 Max, one-time)
caffeinate -i bash scripts/run_turboseti_on_extended_corpus.sh

# Step 2: build candidate reports
caffeinate -i bash scripts/run_pipeline_on_bl_data.sh \
    --dat-dir data/extended_corpus

# Step 3: continuous production scan (5 targets)
caffeinate -i bash scripts/run_production_scan.sh \
    --dat-dir data/extended_corpus
```

### First run — Voyager calibration only (3 targets)

```bash
git pull origin main
caffeinate -i bash scripts/run_production_scan.sh \
    --dat-dir data/bl_hits
```

### Continuous mode (polls for new files every 60 s)

```bash
caffeinate -i bash scripts/run_production_scan.sh \
    --dat-dir data/extended_corpus \
    --continuous
```

### Re-scan all targets (e.g., after a model update)

```bash
caffeinate -i bash scripts/run_production_scan.sh \
    --dat-dir data/extended_corpus \
    --force-rescan
```

### Check what the queue looks like before running

```bash
.venv/bin/techno-search prod-target-queue \
    --dat-dir data/extended_corpus \
    --history-file results/scan_history.ndjson
```

### Inspect scan history

```bash
.venv/bin/techno-search scan-history-summary \
    --history-file results/scan_history.ndjson \
    --dat-dir data/extended_corpus
```

---

## Storage Cleanup — Non-Negotiable

Large intermediate files accumulate quickly. Before each new download batch,
plan cleanup for prior converted or ledgered runs to free storage space.

### Plan cleanup between batches

```bash
git pull origin main
.venv/bin/techno-search radio-corpus-cleanup
```

This dry run only proposes:

- HDF5 files under `data/extended_corpus/` after a same-stem non-empty `.dat`
  exists.
- Zero-hit `.dat` files under `data/extended_corpus/` after a zero-hit manifest
  in `results/` records the file's relative `source_data_path`.

Hit-bearing `.dat` files are never cleanup candidates.

### Apply cleanup

Review the dry-run JSON first. If the plan is correct:

```bash
git pull origin main
.venv/bin/techno-search radio-corpus-cleanup \
  --apply \
  --acknowledge-local-apply
```

### What to keep

| Keep | Reason |
|---|---|
| `results/scans/RUN-*/` | Local generated production run artifacts — ignored unless deliberately reviewed and force-added |
| `data/target_sample_manifest.json` | Reproduces the download list |
| `data/bl_hprc_seed_targets.csv` | Source of stratified sample |
| `data/meerkat_hits/*.ndjson` | Real MeerKAT corpus used for model training |
| Any `.dat` file with real hits above threshold | Needed for re-processing |

### Synthetic training data — delete permanently

Synthetic calibration data was never scientifically valid for training models
that will operate on real signals. Delete it:

```bash
# These files contain synthetic (fake) data and must not be used for training
rm -f tests/fixtures/calibration_false_positives.json
rm -f tests/fixtures/score_regressions.json

# After deletion, update any tests that import these fixtures to skip or remove
```

Do not replace synthetic training data with more synthetic data. Use real
labeled corpora only (MeerKAT BLUSE, real GBT hits, real turboSETI output).

---

## Scientific Guardrails (non-negotiable)

1. `validate-all` must pass before any scan proceeds. The script aborts on failure.
2. No scan result constitutes a detection claim or authorizes external submission.
3. All outputs are local production-scan evidence records only; they are not
   detection, discovery, expert-review, peer-review, external-validation, or
   external-submission claims.
4. Escalation candidates require `operator_cleared` and `external_review_authorized`
   to both be `True` before any external action — those fields start as `False` and
   require explicit human approval.
5. The scan history file is a provenance record, not a discovery log.

---

## Adapting This Runbook to Other Projects

The five rules above are project-agnostic. To adapt:

1. Replace `techno-search run-pipeline` with your pipeline CLI command.
2. Replace `.dat` discovery with your input file extension.
3. Replace `signal_reality_confidence` score extraction with your score field.
4. Keep the NDJSON history schema — it is minimal and self-describing.
5. Keep the `parent_run_id` chain for re-scan linking.
6. Keep the continuous loop + SIGINT trap pattern verbatim.
7. Keep `validate-all` (or equivalent) as a mandatory preflight gate.
