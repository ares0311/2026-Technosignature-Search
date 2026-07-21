# Techno-Hunter

![Status](https://img.shields.io/badge/Hunter%20workflow-PROD-brightgreen)
![Version](https://img.shields.io/badge/version-1.2.43-blue)
![License](https://img.shields.io/badge/license-Apache--2.0-green)
![Focus](https://img.shields.io/badge/focus-multimodal%20technosignature%20search-purple)

Techno-Hunter is a conservative, reproducible search tool for finding
astronomical observations that warrant additional technosignature analysis. It
builds and resolves a candidate universe, ranks eligible new or follow-up
targets, freezes the exact selection, acquires or reuses data, runs the
scientific pipeline, preserves results and provenance, and recommends the next
follow-up action.

The Hunter core workflow is production-complete. Its outputs are local triage
evidence and documented null results—not detections, discoveries, expert
review, external validation, or permission to contact an outside party.

## Pipeline architecture

```text
candidate universe
  -> identity and search-history resolution
  -> eligibility
  -> deterministic ranking and selection
  -> immutable search manifest
  -> durable pending search
  -> approved acquisition or retained-data reuse
  -> preprocessing and modality-specific scoring
  -> composite interpretation
  -> durable results and provenance
  -> follow-up registration
  -> recommended next action
```

Three shell commands operate that lifecycle:

- `Create-New-Search` ranks targets and creates an immutable pending search.
- `Run-New-Search` executes that exact search without regenerating its targets.
- `Show-Follow-Ups` displays the durable, actionable follow-up registry.

The deterministic workflow does not require AI. If a fitted semi-supervised
model is locally available, its anomaly score is optional ranking evidence
only; it cannot promote a candidate or make a detection decision.

## Scientific boundary

The project uses labels for training, calibration, threshold selection, or
scientific evaluation only when independent row-level labels already exist
with documented provenance.

- No confirmed positive technosignature labels exist.
- Nobody is asked to label, annotate, classify, or review observations to
  create project labels.
- Unlabeled observations may be searched, ranked, and investigated, but they
  remain unlabeled.
- An anomaly score is a ranking diagnostic, not a class probability or a
  detection claim.
- `unknown_candidate` is a local Track B triage state, not a positive label,
  discovery, or authorization for external submission.
- Missing calibration evidence keeps dependent learned-model gates
  fail-closed.
- False positive is always the default hypothesis.

The governing rules are in [AGENTS.md](AGENTS.md). Current evidence and
limitations are in
[docs/PRODUCTION_READINESS.md](docs/PRODUCTION_READINESS.md), and the sequenced
science plan is in
[docs/SYSTEMATIC_SEARCH_PLAN.md](docs/SYSTEMATIC_SEARCH_PLAN.md).

## Current status

Phase 0 is complete. Phases 1–5 have real, tested baselines, and the Hunter
core workflow meets its production lifecycle contract.

| Area | Current state |
|---|---|
| Hunter lifecycle | Production-complete and verified with a real approval-gated new-target run, a durable failure/resume cycle, retained-data follow-up execution, and restart protection. |
| Candidate universe | 12,086 unique Breakthrough Listen archive labels are durable. Exact evidence resolves 1,184 identities; 358 are currently ranking-eligible. Unresolved identities are excluded rather than guessed. |
| Radio | Real GBT/MeerKAT ingest, turboSETI preprocessing, ABACAB cadence checks, known-explanation checks, drift analysis, cross-target recurrence, and frequency-family diagnostics are implemented. |
| Transit photometry | BLS, aperiodic-dip, ingress/egress asymmetry, and transit-shape checks are wired end to end. |
| Infrared | AllWISE ingest, photosphere fitting, W3/W4 excess significance, and AGN-color checks are implemented; live IRSA use is network-dependent. |
| Spectroscopy | JWST MIRI LRS ingest and HITRAN-derived artificial-gas band checks are implemented; a corrected real WASP-43 run produced negative evidence. |
| Multi-modal review | Sky-position crossmatching and deterministic adversarial-review dossiers are implemented. No real candidate has advanced to outside expert review. |
| Learned calibration | Fail-closed: no adequate pre-existing independent row-level calibration set is available. Uncalibrated scores remain routing indices only. |

The current real radio review has unresolved, unlabeled follow-up rows but
zero independently escalation-ready candidates. No current result is ready for
external submission.

## Environment

Prerequisites are Git, Python 3.14.3, and `jq`. The documented long-running
commands use macOS `caffeinate`; omit that wrapper on systems that do not
provide it.

Use the repository from `main` with a local `.venv` running Python 3.14.3. If
the environment does not yet exist, create it with a Python 3.14 environment
manager before continuing. Install every science/development extra because the
Hunter run path spans acquisition, radio processing, scientific catalogs, and
validation:

```bash
git pull origin main
.venv/bin/python -m pip install -e ".[dev,radio,science,ml,track_a,photometry]"
bash scripts/patch_turbo_seti_numpy2_compat.sh
```

The turboSETI compatibility patch is required after every reinstall of the
`radio` extra. It applies an idempotent NumPy 2 compatibility correction to the
pinned turboSETI 2.3.2 environment; it does not modify repository source.

Verify the installed entry points:

```bash
git pull origin main
.venv/bin/Create-New-Search --help
.venv/bin/Run-New-Search --help
.venv/bin/Show-Follow-Ups --help
```

## Quick start

### 1. Create and inspect a new-target search

Creation performs selection only. It does not download or process raw data.

```bash
git pull origin main
SEARCH_ID=$(.venv/bin/Create-New-Search --targets 10 --mode new --json | jq -r '.search_id')
printf '%s\n' "$SEARCH_ID"
jq '{search_id, mode, candidate_catalog, eligibility_queue, selection, targets}' \
  "results/searches/${SEARCH_ID}/manifest.json"
```

For 100 targets or fewer, the default non-JSON command prints a terminal table.
For more than 100, it writes a timestamped review CSV under
`results/search_manifests/` and prints its path. The immutable JSON manifest—not
the CSV—is the search system of record.

Review the following before authorizing any acquisition:

- exact targets and stable identifiers;
- selection score and reason;
- prior-search provenance;
- execution kind;
- source URL and projected download size;
- candidate-catalog and priority-queue hashes;
- app, code, scorer, and processing versions.

### 2. Run the exact pending search

If every selected target already has a retained local DAT artifact, no download
approval is required:

```bash
git pull origin main
caffeinate -i .venv/bin/Run-New-Search --search-id SEARCH-...
```

Replace `SEARCH-...` with the ID printed by the create command. If raw archive
data is required, the command exits with status 2 before downloading anything.
After reviewing the immutable manifest and projected size, authorize only that
exact bounded search:

```bash
git pull origin main
caffeinate -i .venv/bin/Run-New-Search \
  --search-id SEARCH-... \
  --approve-acquisition
```

The download and all derived processing occur inside the repository workspace.
The runner preserves raw-to-derived provenance and then evicts re-downloadable
raw HDF5 cache after the retained DAT and candidate report exist. The project
enforces a permanent 100 GB managed-data cap.

### 3. Review follow-ups

```bash
git pull origin main
.venv/bin/Show-Follow-Ups
```

The table shows target identity, evidence summary, prior-search count, priority,
and recommended next action. Machine-readable output is available with
`--json`:

```bash
git pull origin main
.venv/bin/Show-Follow-Ups --json | jq \
  '{eligible_count, unresolved_identity_count, eligible_entries}'
```

### 4. Create a follow-up search

Follow-up mode ranks targets from durable run ledgers. It preserves every prior
search relationship and does not imply that reprocessing old data fulfills a
recommended later-epoch observation.

```bash
git pull origin main
SEARCH_ID=$(.venv/bin/Create-New-Search --targets 3 --mode follow-up --json | jq -r '.search_id')
caffeinate -i .venv/bin/Run-New-Search --search-id "$SEARCH_ID"
.venv/bin/Show-Follow-Ups
```

## Failure and recovery

Failures are visible, non-zero, and resumable:

- exit 2 means raw acquisition needs explicit manifest approval;
- exit 1 means a lifecycle, validation, or execution failure occurred;
- a failed attempt appends `run_failed` and preserves its stage and run ID;
- rerunning the same search ID resumes the same immutable target list;
- completed targets, partial downloads, retained DAT files, and completed
  interpretation artifacts are reused where valid;
- a completed search rejects another execution instead of duplicating history;
- a manifest hash or app-version mismatch fails rather than silently migrating
  or substituting work.

Resume with the same command after correcting the visible cause:

```bash
git pull origin main
caffeinate -i .venv/bin/Run-New-Search --search-id SEARCH-...
```

Add `--approve-acquisition` only if that same immutable search still requires
raw data and its manifest has been reviewed.

## Durable outputs

| Concept | Durable location |
|---|---|
| Candidate catalog | `data_selection/bl_archive_candidate_catalog.csv` |
| Eligibility/ranking queue | `data_selection/target_priority_queue.csv` |
| Exact search manifest | `results/searches/SEARCH-*/manifest.json` |
| Append-only lifecycle | `results/searches/SEARCH-*/events.ndjson` |
| Isolated pipeline reports | `results/searches/SEARCH-*/pipeline_results/` |
| Search run results | `results/searches/SEARCH-*/runs/RUN-*/` |
| Target search history | `results/scan_history.ndjson` |
| Follow-up registry sources | per-run `*_follow_ups.json` ledgers |
| Compact acquisition status | `docs/data_collection_status.json` |

Search history and provenance are append-only. CSV review manifests are never
used as a replacement for the immutable JSON search record.

## Real-data workflows

The lower-level `techno-search` CLI exposes modality-specific ingest,
validation, scoring, Track A/B, production-ledger, and adversarial-review
commands. Start with the complete command reference in
[docs/CLI_USAGE.md](docs/CLI_USAGE.md) and the bounded production procedure in
[docs/PRODUCTION_SCAN_RUNBOOK.md](docs/PRODUCTION_SCAN_RUNBOOK.md).

Summarize retained radio evidence without writing data:

```bash
git pull origin main
.venv/bin/techno-search radio-real-corpus-summary \
  --dat-dir data/extended_corpus \
  --dat-dir data/bl_hits
```

Check explicit Track B evidence without making a candidate claim:

```bash
git pull origin main
.venv/bin/techno-search track-b-candidate-readiness candidate.json \
  --crossmatch-json track_a_crossmatch.json \
  --satellite-json satellite_match.json
```

## Data and target-selection policy

Target selection maximizes expected search value rather than statistical
representativeness. New mode uses the config-versioned
`target_selection_score`; follow-up mode uses real ledger evidence and a
separate deterministic `follow_up_priority`. Stable canonical identity is
required in both modes.

Acquisition is metadata-first and begins with a metadata target queue:

1. preserve the candidate catalog and identity resolution;
2. build the eligibility/ranking queue;
3. discover archive products without downloading payloads;
4. perform size and storage preflight;
5. freeze the exact ranked selection;
6. require explicit approval for raw acquisition;
7. process in bounded chunks and evict re-downloadable raw cache;
8. retain provenance, derived evidence, results, failures, and follow-ups.

The 358 currently eligible archive targets total approximately 89.275 GB by
preflight. That is an inventory, not blanket download authorization.

Relevant policies:

- [Systematic search plan](docs/SYSTEMATIC_SEARCH_PLAN.md)
- [Data-selection policy](docs/astrometrics_data_selection_policy.md)
- [Storage policy](docs/astrometrics_external_and_cloud_storage_policy.md)
- [Detection-agent guide](docs/astrometrics_coding_agents_master_guide.md)
- [Track A dataset handoff](docs/technosignature_datasets_agent_brief.md)
- [Production scan runbook](docs/PRODUCTION_SCAN_RUNBOOK.md)

## Validation and release discipline

Run the canonical validation suite after changing release-relevant behavior or
documentation:

```bash
git pull origin main
caffeinate -i .venv/bin/python scripts/run_parallel_validation.py
```

The launcher uses six non-overlapping pytest-xdist workers, then runs the app
version gate, Ruff, mypy, `validate-all`, directive parity, and the
no-fake-completion gate. A successful clean run records the exact verified
commit locally.

Release-relevant changes must keep these versions synchronized:

- `pyproject.toml`;
- `src/techno_search/__init__.py`;
- `docs/PRODUCTION_READINESS.md`.

See [docs/VALIDATION.md](docs/VALIDATION.md),
[docs/CI.md](docs/CI.md), and
[docs/LOCAL_SYSTEM_PROFILE.md](docs/LOCAL_SYSTEM_PROFILE.md).

## Repository layout

```text
src/techno_search/       application and scientific pipeline code
scripts/                 bounded acquisition, processing, and validation tools
tests/                   regression, scientific, and integration tests
docs/                    authoritative status, policies, methods, and runbooks
data_selection/          candidate catalog, ranking queue, and review manifests
schemas/                 active machine-readable contracts
data/                    ignored or selectively tracked local science inputs
results/                 ignored durable local searches, runs, and reports
```

Large raw HDF5, FITS, filterbank, cache, fitted-model, and generated result
payloads are not committed. Small manifests, checksums, schemas, sanitized
status records, and reproducibility evidence are committed when policy allows.

## Scientific guardrails

- Track A known-explanation checks precede Track B triage.
- Track A may abstain with `low_confidence`; abstention is not a positive class.
- Unlabeled data is never treated as negative ground truth.
- Uncalibrated routing values are not probabilities.
- Accuracy alone is not promotion evidence for rare-event search.
- Learned-model promotion requires provenance, grouped leakage-safe evaluation,
  calibration context, and injection-recovery evidence in real backgrounds.
- Candidate reports expose negative evidence, uncertainty, provenance, and
  blockers.
- No automated or AI component makes a final detection decision.
- No result authorizes public disclosure or external submission.

## Disclaimer

Techno-Hunter is research software. Its outputs are local triage evidence,
candidate-interest reports, and documented null results. They are not confirmed
technosignatures, detections, discoveries, expert review, external validation,
or authority-facing notifications.

## License

Apache-2.0. See [LICENSE](LICENSE).
