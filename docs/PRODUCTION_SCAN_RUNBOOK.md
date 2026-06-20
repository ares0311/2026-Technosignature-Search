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
| `techno-search run-pipeline FILE TRACK OUTPUT_DIR` | Process one input file through the pipeline |
| `techno-search validate-all` | Must pass before any scan proceeds |

---

## File Layout

```
data/bl_hits/                  ← raw turboSETI .dat input files
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
```

The `results/scans/` subtree is committed to GitHub as the durable audit trail.
Everything else under `results/` is local-only (gitignored).

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
| `data/extended_corpus/<TARGET>/` | GBT L-band HDF5 files for 5 HIP targets | `scripts/download_bl_extended_corpus.sh` |

HDF5 files in `data/extended_corpus/` must be processed with turboSETI before they can
enter the production scan queue.  Use `scripts/run_turboseti_on_extended_corpus.sh` (idempotent).

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

## Scientific Guardrails (non-negotiable)

1. `validate-all` must pass before any scan proceeds. The script aborts on failure.
2. No scan result constitutes a detection claim or authorizes external submission.
3. All outputs are local citizen-science scheduling aids only.
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
