# CLAUDE.md

## Purpose

Handoff and progress notes for Claude or other coding agents working in this repository.

Read `AGENTS.md` first. The scientific guardrails there remain authoritative.

---

## Current Iteration

User requested three iterative steps:

1. Add report file writers.
2. Start the radio prototype.
3. Add track-specific configs.

After each step, update this file and merge to `main` if needed.

Current branch: `main`. No merge has been needed so far.

Overall status: all three requested steps are implemented.

---

## README Style Refresh

User requested extracting the style DNA from the sibling exoplanet project README and applying it to this repository.

Status: implemented.

Added:

- compact public-facing README structure with visual section headers
- core flow, key idea, current status, roadmap, architecture, scoring model, quickstart, schema table, disclaimer, license, and vision sections
- conservative technosignature language and false-positive-first framing
- README structure drift test in `tests/test_docs.py`
- updated `docs/PROJECT_STATUS.md` current-phase wording
- refreshed `docs/PUBLISHING.md` with the moved GitHub repository URL

Validation passed:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/ruff check .
.venv/bin/mypy src
git diff --check
```

Result:

- 175 tests passed
- 5 tests skipped
- total coverage: 92%
- Ruff passed
- mypy passed
- diff whitespace check passed

Merge status: already on `main`; no merge needed.

---

## Background Target Priority And Passive Search Ledger Expansion

User requested prioritizing the background searching system discussed in the README.

Status: implemented in this iteration.

Added:

- fixture-backed background target-priority model in `src/techno_search/background_search.py`
- passive/background search ledger loader and summary helper
- `techno-search target-priority-summary`
- `techno-search background-ledger-summary`
- JSON schemas for target-priority and background-ledger fixtures
- local validation wiring through `validate-all` and `validation-summary`
- tests for target scoring, selected target behavior, ledger coverage, schema coverage, and CLI output
- README/docs updates explaining layperson operation, recalibration, target selection, passive logging, and guardrails

Scientific guardrail:

- target priority is a scheduling aid only
- ledger entries are reproducibility records only
- neither output is evidence of a technosignature or a discovery claim

Merge status: already on `main`; no merge needed.

---

## Background Config And Local Passive Runner Expansion

User requested the next fifteen steps and asked to push when complete.

Status: implemented in this iteration.

Added:

- `configs/background_priority_v0.json` for versioned target-priority weights and passive-runner defaults
- background priority config loader and public exports
- config-backed `target-priority-summary`
- explicit `techno-search background-run-once` command
- local-only ledger append helper with required opt-in and no network access
- tests for config loading, opt-in enforcement, ledger creation, ledger append behavior, and CLI output
- README, CLI usage, validation, roadmap, scoring model, pipeline spec, project status, and decisions updates

Scientific guardrail:

- the passive runner records scheduling-only local fixture events
- `candidate_count` remains `0` until candidate extraction is implemented
- the output pathway is `github_reproducibility_only`
- no live provider access is performed

Merge status: already on `main`; no merge needed.

---

## Fifteen-Step Consensus Export, Promotion, And Benchmark Run Expansion

User requested the next fifteen steps:

1. Add conservative consensus-label export example format.
2. Add consensus export fixture JSON.
3. Add `techno-search consensus-export-summary`.
4. Add tests for consensus export coverage and conservative language.
5. Wire consensus export summary into `validate-all`.
6. Wire consensus export counts into `validation-summary`.
7. Update docs/status for consensus export examples.
8. Add validation dataset promotion rule schema.
9. Add promotion rule fixture for synthetic to future non-synthetic datasets.
10. Add `techno-search validation-promotion-summary`.
11. Add tests for promotion rules by readiness, evidence requirements, and blocking conditions.
12. Wire promotion rules into `validate-all` and `validation-summary`.
13. Add benchmark run-result metadata schema for future synthetic calibration grids.
14. Add benchmark run-result fixture and summary CLI.
15. Run full validation, update `CLAUDE.md`, commit, push, and confirm clean sync.

Each step should update this file and merge to `main` if needed.

## Consensus Export/Promotion/Benchmark Step 1 — Consensus Export Format

Status: implemented.

Added:

- `CONSENSUS_EXPORT_SCHEMA_VERSION`
- `CONSENSUS_EXPORT_DISCLAIMER`
- `ConsensusExportItem`
- consensus export fixture loader
- consensus export summary helper

Merge status: already on `main`; no merge needed.

---

## Consensus Export/Promotion/Benchmark Step 2 — Consensus Export Fixture

Status: implemented.

Added:

- `schemas/consensus_export.schema.json`
- `tests/fixtures/consensus_exports.json`
- conservative consensus export examples for no-consensus, likely-false-positive, follow-up-target, known-object annotation, and insufficient-evidence labels

Merge status: already on `main`; no merge needed.

---

## Consensus Export/Promotion/Benchmark Step 3 — Consensus Export Summary CLI

Status: implemented.

Added:

- `techno-search consensus-export-summary`
- optional `--fixture-path`
- `consensus_export` in `schema-paths`
- public package exports for consensus export helpers

Merge status: already on `main`; no merge needed.

---

## Consensus Export/Promotion/Benchmark Step 4 — Consensus Export Tests

Status: implemented.

Added tests for:

- consensus export fixture loading
- conservative disclaimer language
- summary counts by track and consensus label
- CLI output for `consensus-export-summary`
- schema discovery and required fixture fields

Merge status: already on `main`; no merge needed.

---

## Consensus Export/Promotion/Benchmark Step 5 — Validate-All Consensus Export Wiring

Status: implemented.

Added:

- `consensus_export_summary` block in `validate-all`
- validation gate for expected synthetic consensus export coverage

Merge status: already on `main`; no merge needed.

---

## Consensus Export/Promotion/Benchmark Step 6 — Validation Summary Consensus Export Counts

Status: implemented.

Added:

- `consensus_export_count`
- `consensus_export_blocking_issue_total`

Merge status: already on `main`; no merge needed.

---

## Consensus Export/Promotion/Benchmark Step 7 — Consensus Export Docs And Status

Status: implemented.

Updated:

- `README.md`
- `docs/CLI_USAGE.md`
- `docs/VALIDATION.md`
- `docs/PROJECT_STATUS.md`

Merge status: already on `main`; no merge needed.

---

## Consensus Export/Promotion/Benchmark Step 8 — Validation Promotion Rule Schema

Status: implemented.

Added:

- `VALIDATION_PROMOTION_SCHEMA_VERSION`
- `VALIDATION_PROMOTION_DISCLAIMER`
- `ValidationPromotionRule`
- promotion rule loader
- promotion rule summary helper

Merge status: already on `main`; no merge needed.

---

## Consensus Export/Promotion/Benchmark Step 9 — Validation Promotion Fixture

Status: implemented.

Added:

- `schemas/validation_promotion_rules.schema.json`
- `tests/fixtures/validation_promotion_rules.json`
- synthetic-to-curated promotion rules for radio, infrared, and anomaly validation datasets

Merge status: already on `main`; no merge needed.

---

## Consensus Export/Promotion/Benchmark Step 10 — Validation Promotion Summary CLI

Status: implemented.

Added:

- `techno-search validation-promotion-summary`
- optional `--rules-path`
- `validation_promotion_rules` in `schema-paths`
- public package exports for validation promotion helpers

Merge status: already on `main`; no merge needed.

---

## Consensus Export/Promotion/Benchmark Step 11 — Validation Promotion Tests

Status: implemented.

Added tests for:

- promotion rule fixture loading
- readiness transitions
- evidence requirements
- blocking conditions
- external-review requirements
- `techno-search validation-promotion-summary`
- schema discovery and required fixture fields

Merge status: already on `main`; no merge needed.

---

## Consensus Export/Promotion/Benchmark Step 12 — Validation Promotion Local Validation Wiring

Status: implemented.

Added:

- `validation_promotion_summary` block in `validate-all`
- validation gate for promotion rule coverage
- `validation_promotion_rule_count` in `validation-summary`
- `validation_promotion_blocking_condition_count` in `validation-summary`

Merge status: already on `main`; no merge needed.

---

## Consensus Export/Promotion/Benchmark Step 13 — Benchmark Run-Result Metadata Schema

Status: implemented.

Added:

- `BENCHMARK_RUN_RESULT_SCHEMA_VERSION`
- `BENCHMARK_RUN_RESULT_DISCLAIMER`
- `BenchmarkRunResult`
- benchmark run-result loader
- benchmark run-result summary helper
- `schemas/benchmark_run_results.schema.json`

Merge status: already on `main`; no merge needed.

---

## Consensus Export/Promotion/Benchmark Step 14 — Benchmark Run-Result Fixture And Summary CLI

Status: implemented.

Added:

- `tests/fixtures/benchmark_run_results.json`
- `techno-search benchmark-run-summary`
- benchmark run-result schema discovery in `schema-paths`
- benchmark run-result summary wiring in `validate-all`
- benchmark run-result counts in `validation-summary`
- tests for fixture loading, CLI output, schema fields, and local validation wiring
- docs/status/roadmap references for benchmark run-result metadata

Validation passed:

```bash
.venv/bin/python -m pytest tests/test_benchmark_metadata.py tests/test_cli.py tests/test_json_schemas.py tests/test_validation_datasets.py
```

Result:

- 48 tests passed

Merge status: already on `main`; no merge needed.

---

## Consensus Export/Promotion/Benchmark Step 15 — Validation, Commit, And Push

Status: implemented.

Validation passed:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/ruff check .
.venv/bin/mypy src
git diff --check
```

Result:

- 174 tests passed
- 5 tests skipped
- total coverage: 92%
- Ruff passed
- mypy passed
- diff whitespace check passed

Planned commit:

```bash
git commit -m "Add benchmark run result summaries"
```

Merge status: already on `main`; no merge needed.

---

## Fifteen-Step Validation Dataset And Benchmark Metadata Expansion

User asked to continue after the consensus/calibration pass. Next roadmap/status items:

1. Add validation dataset manifest helper schema in code.
2. Add validation dataset JSON schema artifact.
3. Add validation dataset manifest fixture examples.
4. Add validation dataset summary helper.
5. Add `techno-search validation-dataset-summary`.
6. Add tests for validation dataset schema, helper, and CLI.
7. Wire validation dataset summary into `validate-all`.
8. Wire validation dataset counts into `validation-summary`.
9. Update validation dataset docs/status/roadmap.
10. Add benchmark metadata helper schema in code.
11. Add benchmark metadata JSON schema and fixture.
12. Add `techno-search benchmark-metadata-summary`.
13. Add tests for benchmark metadata schema, helper, and CLI.
14. Wire benchmark metadata into validation/docs/status.
15. Run full validation, commit, push, and record everything in `CLAUDE.md`.

Each step should update this file and merge to `main` if needed.

## Validation/Benchmark Step 1 — Validation Dataset Helper Schema

Status: implemented.

Added:

- `VALIDATION_DATASET_SCHEMA_VERSION`
- `VALIDATION_DATASET_DISCLAIMER`
- `ValidationDatasetEntry`
- validation dataset manifest loader
- validation dataset summary helper skeleton

Merge status: already on `main`; no merge needed.

---

## Validation/Benchmark Step 2 — Validation Dataset JSON Schema

Status: implemented.

Added:

- `schemas/validation_dataset_manifest.schema.json`
- required manifest fields for dataset ID, track, kind, readiness, source fixture path, case count, false-positive classes, and expected pathways

Merge status: already on `main`; no merge needed.

---

## Validation/Benchmark Step 3 — Validation Dataset Fixture

Status: implemented.

Added `tests/fixtures/validation_dataset_manifest.json` with lightweight synthetic scaffold entries for:

- radio false-positive validation cases
- infrared false-positive validation cases
- anomaly false-positive validation cases

Merge status: already on `main`; no merge needed.

---

## Validation/Benchmark Step 4 — Validation Dataset Summary Helper

Status: implemented.

The validation dataset helper now summarizes:

- dataset count
- total case count
- false-positive class count
- expected pathway count
- counts by track, dataset kind, and readiness
- dataset IDs and source fixture paths

Merge status: already on `main`; no merge needed.

---

## Validation/Benchmark Step 5 — Validation Dataset Summary CLI

Status: implemented.

Added:

- `techno-search validation-dataset-summary`
- optional `--manifest-path`
- `validation_dataset_manifest` in `schema-paths`
- public package exports for validation dataset helpers

Merge status: already on `main`; no merge needed.

---

## Validation/Benchmark Step 6 — Validation Dataset Tests

Status: implemented.

Added tests for:

- validation dataset manifest loading
- validation dataset summary counts
- `techno-search validation-dataset-summary`
- schema discovery and required manifest fields

Merge status: already on `main`; no merge needed.

---

## Validation/Benchmark Step 7 — Validate-All Validation Dataset Wiring

Status: implemented.

Added:

- `validation_dataset_summary` block in `validate-all`
- validation gates for manifest dataset count and total case coverage

Merge status: already on `main`; no merge needed.

---

## Validation/Benchmark Step 8 — Validation Summary Dataset Counts

Status: implemented.

Added:

- `validation_dataset_count`
- `validation_dataset_case_count`

Merge status: already on `main`; no merge needed.

---

## Validation/Benchmark Step 9 — Validation Dataset Docs And Status

Status: implemented.

Updated:

- `README.md`
- `docs/CLI_USAGE.md`
- `docs/VALIDATION.md`
- `docs/ROADMAP.md`
- `docs/PROJECT_STATUS.md`

Merge status: already on `main`; no merge needed.

---

## Validation/Benchmark Step 10 — Benchmark Metadata Helper Schema

Status: implemented.

Added:

- `BENCHMARK_METADATA_SCHEMA_VERSION`
- `BENCHMARK_METADATA_DISCLAIMER`
- `BenchmarkCommand`
- benchmark metadata loader
- benchmark metadata summary helper

Merge status: already on `main`; no merge needed.

---

## Validation/Benchmark Step 11 — Benchmark Metadata Schema And Fixture

Status: implemented.

Added:

- `schemas/benchmark_metadata.schema.json`
- `tests/fixtures/benchmark_metadata.json`
- local benchmark metadata tied to `docs/LOCAL_SYSTEM_PROFILE.md`
- recommended worker and memory limits from the documented local workstation

Merge status: already on `main`; no merge needed.

---

## Validation/Benchmark Step 12 — Benchmark Metadata Summary CLI

Status: implemented.

Added:

- `techno-search benchmark-metadata-summary`
- optional `--metadata-path`
- `benchmark_metadata` in `schema-paths`
- public package exports for benchmark metadata helpers

Merge status: already on `main`; no merge needed.

---

## Validation/Benchmark Step 13 — Benchmark Metadata Tests

Status: implemented.

Added tests for:

- benchmark metadata fixture loading
- local hardware/profile summary fields
- command kind and status counts
- `techno-search benchmark-metadata-summary`
- schema discovery and required fixture fields

Merge status: already on `main`; no merge needed.

---

## Validation/Benchmark Step 14 — Benchmark Metadata Validation And Docs

Status: implemented.

Added:

- `benchmark_metadata_summary` block in `validate-all`
- benchmark metadata counts in `validation-summary`
- benchmark metadata references in `README.md`, `docs/CLI_USAGE.md`, `docs/VALIDATION.md`, and `docs/PROJECT_STATUS.md`

Merge status: already on `main`; no merge needed.

---

## Validation/Benchmark Step 15 — Full Validation, Commit, And Push

Status: implemented.

Validation passed:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/ruff check .
.venv/bin/mypy src
git diff --check
```

Result:

- 165 tests passed
- 5 tests skipped
- total coverage: 92%
- Ruff passed
- mypy passed
- diff whitespace check passed

Planned commit:

```bash
git commit -m "Add validation dataset and benchmark metadata summaries"
```

Merge status: already on `main`; no merge needed.

---

## Fifteen-Step Consensus And Calibration-Track Expansion

User requested fifteen iterative steps:

1. Add consensus-label schema for repeated reviewer decisions.
2. Add consensus label fixture examples.
3. Add `techno-search consensus-summary`.
4. Add tests for consensus summaries by label, track, and reviewer count.
5. Wire consensus summary into `validate-all`.
6. Wire consensus counts into `validation-summary`.
7. Update human-review docs for consensus labels.
8. Mark consensus-label scaffold complete in roadmap/status.
9. Add calibration-by-track summary helper.
10. Add `techno-search calibration-track-summary`.
11. Add tests for calibration-by-track class/pathway coverage.
12. Wire calibration-by-track summary into `validate-all`.
13. Wire calibration-by-track counts into `validation-summary`.
14. Update calibration docs/status/roadmap.
15. Run full validation, commit, push, and record everything in `CLAUDE.md`.

Each step should update this file and merge to `main` if needed.

## Consensus/Calibration Step 1 — Consensus Label Schema

Status: implemented.

Added:

- `CONSENSUS_LABEL_SCHEMA_VERSION`
- `CONSENSUS_LABEL_DISCLAIMER`
- `ConsensusLabel`
- `ConsensusDecision`
- `ConsensusItem`
- `schemas/consensus_labels.schema.json`
- consensus fixture loader and summary skeleton

Merge status: already on `main`; no merge needed.

---

## Consensus/Calibration Step 2 — Consensus Label Fixtures

Status: implemented.

Added `tests/fixtures/consensus_labels.json` with repeated synthetic reviewer decisions for:

- no consensus
- likely false positive
- follow-up target
- known-object annotation
- insufficient evidence

Merge status: already on `main`; no merge needed.

---

## Consensus/Calibration Step 3 — Consensus Summary CLI

Status: implemented.

Added:

- `techno-search consensus-summary`
- optional `--fixture-path`
- `consensus_labels` in `schema-paths`

Merge status: already on `main`; no merge needed.

---

## Consensus/Calibration Step 4 — Consensus Summary Tests

Status: implemented.

Added tests for:

- consensus fixture loading and allowed labels
- consensus summary counts by label and track
- repeated reviewer decision counts
- CLI `consensus-summary`
- `consensus_labels` schema discovery and fixture required fields

Merge status: already on `main`; no merge needed.

---

## Consensus/Calibration Step 5 — Validate-All Consensus Wiring

Status: implemented.

Added:

- `consensus_summary` block in `validate-all`
- validation gates for minimum synthetic consensus item and decision coverage

Merge status: already on `main`; no merge needed.

---

## Consensus/Calibration Step 6 — Validation Summary Consensus Counts

Status: implemented.

Added:

- `consensus_item_count`
- `consensus_decision_count`
- `consensus_unique_reviewer_count`

Merge status: already on `main`; no merge needed.

---

## Consensus/Calibration Step 7 — Consensus Docs

Status: implemented.

Updated:

- `docs/CLI_USAGE.md`
- `docs/VALIDATION.md`
- `README.md`

Merge status: already on `main`; no merge needed.

---

## Consensus/Calibration Step 8 — Consensus Roadmap And Status

Status: implemented.

Updated:

- `docs/ROADMAP.md`
- `docs/PROJECT_STATUS.md`

Merge status: already on `main`; no merge needed.

---

## Consensus/Calibration Step 9 — Calibration-By-Track Helper

Status: implemented.

Added:

- `CALIBRATION_TRACK_SCHEMA_VERSION`
- `CALIBRATION_TRACK_DISCLAIMER`
- `calibration_track_summary`
- per-track case, class, pathway, candidate-ID, and fixture-name coverage

Merge status: already on `main`; no merge needed.

---

## Consensus/Calibration Step 10 — Calibration Track Summary CLI

Status: implemented.

Added:

- `techno-search calibration-track-summary`
- optional `--fixture-path`
- public package exports for calibration-track summary helpers

Merge status: already on `main`; no merge needed.

---

## Consensus/Calibration Step 11 — Calibration Track Tests

Status: implemented.

Added tests for:

- per-track calibration case counts
- per-track false-positive class coverage
- per-track expected pathway coverage
- `techno-search calibration-track-summary`
- conservative per-track calibration disclaimer

Merge status: already on `main`; no merge needed.

---

## Consensus/Calibration Step 12 — Validate-All Calibration Track Wiring

Status: implemented.

Added:

- `calibration_track_summary` block in `validate-all`
- validation gates for expected track coverage and minimum per-track fixture coverage

Merge status: already on `main`; no merge needed.

---

## Consensus/Calibration Step 13 — Validation Summary Calibration Track Counts

Status: implemented.

Added:

- `calibration_track_count`
- `calibration_minimum_track_case_count`

Merge status: already on `main`; no merge needed.

---

## Consensus/Calibration Step 14 — Calibration Docs And Status

Status: implemented.

Updated:

- `docs/CLI_USAGE.md`
- `docs/VALIDATION.md`
- `docs/ROADMAP.md`
- `docs/PROJECT_STATUS.md`

Merge status: already on `main`; no merge needed.

---

## Consensus/Calibration Step 15 — Full Validation, Commit, And Push

Status: implemented.

Validation passed:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/ruff check .
.venv/bin/mypy src
git diff --check
```

Result:

- 159 tests passed
- 5 tests skipped
- total coverage: 92%
- Ruff passed
- mypy passed
- diff whitespace check passed

Planned commit:

```bash
git commit -m "Add consensus and calibration track summaries"
```

Pushed commit:

- `bdb2ee3 Add consensus and calibration track summaries`

Remote sync:

```bash
git push origin main
```

Result:

- `main` pushed to `origin/main`
- remote advanced from `7b10728` to `bdb2ee3`

Merge status: already on `main`; no merge needed.

---

## Fifteen-Step False-Positive And Human-Review Expansion

User requested fifteen iterative steps:

1. Add false-positive class analysis fixture schema.
2. Add false-positive class fixtures from calibration cases.
3. Add `techno-search false-positive-summary`.
4. Add tests for false-positive summary by class and track.
5. Wire false-positive summary into `validate-all`.
6. Wire false-positive summary into `validation-summary`.
7. Update validation docs for false-positive class diagnostics.
8. Update roadmap/status to mark false-positive class analysis complete.
9. Run focused validation and commit.
10. Push `main` and confirm sync.
11. Add human-review queue packet schema.
12. Add triage label enum/allowed values.
13. Add reviewer notes structure.
14. Add `techno-search review-queue-summary`.
15. Add tests and docs for the human-review queue scaffold.

Each step should update this file and merge to `main` if needed.

## False-Positive/Human-Review Step 1 — False-Positive Analysis Schema

Status: implemented.

Added:

- `FALSE_POSITIVE_ANALYSIS_SCHEMA_VERSION`
- `FALSE_POSITIVE_ANALYSIS_DISCLAIMER`
- class, track, pathway, candidate-ID, and fixture-name summary fields

Merge status: already on `main`; no merge needed.

---

## False-Positive/Human-Review Step 2 — Calibration-Derived Class Fixtures

Status: implemented.

Reused the existing synthetic calibration false-positive cases as the source fixture set for class analysis. This keeps the diagnostic tied to the scored calibration cases and avoids introducing an unscored duplicate fixture list.

Merge status: already on `main`; no merge needed.

---

## False-Positive/Human-Review Step 3 — False-Positive Summary CLI

Status: implemented.

Added:

- `techno-search false-positive-summary`
- optional `--fixture-path`
- conservative JSON output with synthetic diagnostic disclaimer

Merge status: already on `main`; no merge needed.

---

## False-Positive/Human-Review Step 4 — False-Positive Summary Tests

Status: implemented.

Added tests for:

- class count
- track count
- nested track-and-class counts
- CLI output and disclaimer language

Merge status: already on `main`; no merge needed.

---

## False-Positive/Human-Review Step 5 — Validate-All Wiring

Status: implemented.

Added `false_positive_summary` to `validate-all` with gates for expected synthetic case and class coverage.

Merge status: already on `main`; no merge needed.

---

## False-Positive/Human-Review Step 6 — Validation Summary Wiring

Status: implemented.

Added:

- `false_positive_case_count`
- `false_positive_class_count`

Merge status: already on `main`; no merge needed.

---

## False-Positive/Human-Review Step 7 — Validation Docs

Status: implemented.

Updated:

- `docs/CLI_USAGE.md`
- `docs/VALIDATION.md`

Merge status: already on `main`; no merge needed.

---

## False-Positive/Human-Review Step 8 — Roadmap And Status

Status: implemented.

Updated:

- `docs/ROADMAP.md`
- `docs/PROJECT_STATUS.md`

Merge status: already on `main`; no merge needed.

---

## False-Positive/Human-Review Step 9 — Focused Validation And Commit

Status: implemented.

Validation passed:

```bash
.venv/bin/python -m pytest tests/test_calibration_fixtures.py tests/test_cli.py tests/test_docs.py
.venv/bin/ruff check src/techno_search/calibration.py src/techno_search/cli.py src/techno_search/__init__.py tests/test_calibration_fixtures.py tests/test_cli.py
.venv/bin/mypy src
git diff --check
```

Result:

- 36 focused tests passed
- Ruff passed
- mypy passed
- diff whitespace check passed

Commit planned:

```bash
git commit -m "Add false positive class summaries"
```

Merge status: already on `main`; no merge needed.

---

## False-Positive/Human-Review Step 10 — Push Main

Status: implemented.

Pushed commit:

- `5271a93 Add false positive class summaries`

Remote sync:

```bash
git push origin main
```

Result:

- `main` pushed to `origin/main`
- remote advanced from `4652b32` to `5271a93`

Merge status: already on `main`; no merge needed.

---

## False-Positive/Human-Review Step 11 — Human-Review Queue Schema

Status: implemented.

Added:

- `REVIEW_QUEUE_SCHEMA_VERSION`
- `schemas/review_queue.schema.json`
- `tests/fixtures/review_queue.json`
- schema path wiring through `schema-paths`

Merge status: already on `main`; no merge needed.

---

## False-Positive/Human-Review Step 12 — Triage Label Enum

Status: implemented.

Added `TriageLabel` with allowed values:

- `needs_human_review`
- `likely_false_positive`
- `follow_up_target`
- `known_object_annotation`
- `insufficient_evidence`

Merge status: already on `main`; no merge needed.

---

## False-Positive/Human-Review Step 13 — Reviewer Notes Structure

Status: implemented.

Added:

- `ReviewerNote`
- `ReviewQueueItem`
- reviewer-note coverage in the fixture and summary output

Merge status: already on `main`; no merge needed.

---

## False-Positive/Human-Review Step 14 — Review Queue Summary CLI

Status: implemented.

Added:

- `techno-search review-queue-summary`
- review queue summary block in `validate-all`
- review queue counts in `validation-summary`

Merge status: already on `main`; no merge needed.

---

## False-Positive/Human-Review Step 15 — Tests, Docs, And Final Validation

Status: implemented.

Added tests and docs for:

- human-review queue fixtures
- allowed triage labels
- reviewer notes
- review queue schema paths
- review queue CLI output

Validation passed:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/ruff check .
.venv/bin/mypy src
git diff --check
```

Result:

- 154 tests passed
- 5 tests skipped
- total coverage: 92%
- Ruff passed
- mypy passed
- diff whitespace check passed

Commit planned:

```bash
git commit -m "Add human review queue summary"
```

Pushed commit:

- `bf63dc4 Add human review queue summary`

Remote sync:

```bash
git push origin main
```

Result:

- `main` pushed to `origin/main`
- remote advanced from `5271a93` to `bf63dc4`

Merge status: already on `main`; no merge needed.

---

## Fifteen-Step Reliability And Precision-Recall Expansion

User requested fifteen iterative steps:

1. Add synthetic reliability-curve fixture schema.
2. Add radio reliability curve fixture bins.
3. Add infrared reliability curve fixture bins.
4. Add anomaly reliability curve fixture bins.
5. Add `techno-search reliability-summary`.
6. Add tests for reliability summary by track and score bin.
7. Wire reliability summary into `validate-all`.
8. Wire reliability summary into `validation-summary`.
9. Add conservative docs noting these are synthetic diagnostics, not calibrated survey performance.
10. Commit and push the reliability fixture pass.
11. Add precision-recall synthetic fixture schema.
12. Add precision-recall fixtures for candidate vs false-positive classes.
13. Add `techno-search precision-recall-summary`.
14. Run full validation and commit.
15. Push `main` and confirm clean sync.

Each step should update this file and merge to `main` if needed.

## Reliability/PR Step 1 — Reliability Fixture Schema

Status: implemented.

Added:

- `RELIABILITY_SCHEMA_VERSION`
- `ReliabilityBin`
- loader validation for `synthetic_reliability_curves_v1`
- conservative disclaimer that bins are synthetic development diagnostics

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_calibration_metrics.py
```

Merge status: already on `main`; no merge needed.

---

## Reliability/PR Step 2 — Radio Reliability Bins

Status: implemented.

Added radio reliability bins for:

- low score range
- mid score range
- high score range

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_calibration_metrics.py
```

Merge status: already on `main`; no merge needed.

---

## Reliability/PR Step 3 — Infrared Reliability Bins

Status: implemented.

Added infrared reliability bins for:

- low score range
- mid score range
- high score range

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_calibration_metrics.py
```

Merge status: already on `main`; no merge needed.

---

## Reliability/PR Step 4 — Anomaly Reliability Bins

Status: implemented.

Added anomaly reliability bins for:

- low score range
- mid score range
- high score range

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_calibration_metrics.py
```

Merge status: already on `main`; no merge needed.

---

## Reliability/PR Step 5 — Reliability Summary CLI

Status: implemented.

Added:

- `techno-search reliability-summary`
- bin counts by track and score range
- synthetic mean and max absolute calibration error

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_calibration_metrics.py
```

Merge status: already on `main`; no merge needed.

---

## Reliability/PR Step 6 — Reliability Summary Tests

Status: implemented.

Added tests proving:

- fixture bins cover radio, infrared, and anomaly tracks
- score bins cover low, mid, and high ranges
- summary reports total samples and calibration-error diagnostics

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_calibration_metrics.py
```

Merge status: already on `main`; no merge needed.

---

## Reliability/PR Step 7 — Validate-All Reliability Wiring

Status: implemented.

Added:

- reliability summary block in `validate-all`
- validation gate requiring the expected reliability bin coverage

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Reliability/PR Step 8 — Validation Summary Reliability Wiring

Status: implemented.

Added:

- `reliability_bin_count` in `validation-summary`
- `mean_absolute_calibration_error` in `validation-summary`

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Reliability/PR Step 9 — Reliability Docs And Status

Status: implemented.

Updated:

- `docs/CLI_USAGE.md`
- `docs/VALIDATION.md`
- `docs/ROADMAP.md`
- `docs/PROJECT_STATUS.md`

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Reliability/PR Step 10 — Reliability Fixture Commit

Status: implemented.

Validation passed:

- `.venv/bin/python -m pytest tests/test_calibration_metrics.py tests/test_cli.py tests/test_docs.py`
- `.venv/bin/ruff check src/techno_search/calibration_metrics.py src/techno_search/cli.py src/techno_search/__init__.py tests/test_calibration_metrics.py tests/test_cli.py`
- `.venv/bin/mypy src`
- `git diff --check`

Commit planned:

```bash
git commit -m "Add reliability summary fixtures"
```

Merge status: already on `main`; no merge needed.

---

## Reliability/PR Step 11 — Precision-Recall Fixture Schema

Status: implemented.

Added:

- `PRECISION_RECALL_SCHEMA_VERSION`
- `PrecisionRecallCase`
- loader validation for `synthetic_precision_recall_v1`
- conservative disclaimer that fixtures are not validated classification metrics

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_calibration_metrics.py
```

Merge status: already on `main`; no merge needed.

---

## Reliability/PR Step 12 — Precision-Recall Fixtures

Status: implemented.

Added synthetic precision-recall fixtures for:

- candidate truth class
- false-positive truth class
- radio, infrared, and anomaly tracks

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_calibration_metrics.py
```

Merge status: already on `main`; no merge needed.

---

## Reliability/PR Step 13 — Precision-Recall Summary CLI

Status: implemented.

Added:

- `techno-search precision-recall-summary`
- precision-recall summary block in `validate-all`
- precision-recall counts and synthetic metrics in `validation-summary`
- docs/status updates for synthetic precision-recall diagnostics

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_calibration_metrics.py tests/test_cli.py tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Reliability/PR Step 14 — Full Validation And Commit

Status: implemented.

Validation passed:

- `.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing`
- `.venv/bin/ruff check .`
- `.venv/bin/mypy src`
- `git diff --check`

Result:

- 149 tests passed
- 5 tests skipped
- total coverage: 92%

Commit planned:

```bash
git commit -m "Add precision recall summary fixtures"
```

Merge status: already on `main`; no merge needed.

---

## Reliability/PR Step 15 — Push Main And Confirm Clean Sync

Status: implemented.

Pushed commits:

- `64ccd81 Add reliability summary fixtures`
- `d3767dd Add precision recall summary fixtures`

Remote sync:

```bash
git push origin main
```

Result:

- `main` pushed to `origin/main`
- remote advanced from `64ccd81` to `d3767dd`

Merge status: already on `main`; no merge needed.

---

## Fifteen-Step Plot Ergonomics And Injection-Recovery Expansion

User requested fifteen iterative steps:

1. Add a `plot-artifact-summary` CLI for generated report directories.
2. Add tests for plot artifact summary counts by track/kind.
3. Improve Markdown reports with explicit links to generated SVG diagnostics.
4. Add tests proving Markdown links are present and conservative.
5. Commit and push the plot review ergonomics pass.
6. Add synthetic injection-recovery summary fixture schema.
7. Add radio injection-recovery summary fixtures.
8. Add infrared synthetic excess recovery fixtures.
9. Add archival anomaly recovery simulation fixtures.
10. Add `techno-search injection-recovery-summary`.
11. Add tests for injection-recovery summary by track and outcome.
12. Wire injection-recovery summary into `validate-all` and `validation-summary`.
13. Update `docs/ROADMAP.md`, `docs/PROJECT_STATUS.md`, and `docs/VALIDATION.md`.
14. Run full validation and commit.
15. Push `main` and confirm clean sync.

Each step should update this file and merge to `main` if needed.

## Plot/Injection Step 1 — Plot Artifact Summary CLI

Status: implemented.

Added:

- `plot_artifact_summary(...)`
- `techno-search plot-artifact-summary`
- manifest-derived counts without parsing SVG content
- missing path reporting for referenced plot artifacts

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_plotting.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Plot/Injection Step 2 — Plot Artifact Summary Tests

Status: implemented.

Added tests proving:

- plot artifact summaries count entries from manifests
- counts are grouped by track and artifact kind
- generated synthetic SVG paths exist for all three current tracks

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_plotting.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Plot/Injection Step 3 — Markdown Plot Artifact Links

Status: implemented.

Added:

- explicit Markdown links to generated SVG diagnostics when reports are written
- "None generated" output when plot artifacts are intentionally skipped
- regenerated example Markdown will include the SVG diagnostic links

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_reporting.py tests/test_examples.py
```

Merge status: already on `main`; no merge needed.

---

## Plot/Injection Step 4 — Conservative Markdown Link Tests

Status: implemented.

Added tests proving:

- Markdown reports include generated SVG links
- plot artifact language remains explicitly synthetic and illustrative
- reports without generated plots still validate with an explicit "None generated" entry

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_reporting.py
```

Merge status: already on `main`; no merge needed.

---

## Plot/Injection Step 5 — Plot Review Ergonomics Commit

Status: implemented.

Validation passed:

- `.venv/bin/python -m pytest tests/test_plotting.py tests/test_cli.py tests/test_reporting.py tests/test_examples.py tests/test_docs.py`
- `.venv/bin/ruff check src/techno_search/plotting.py src/techno_search/reporting.py src/techno_search/cli.py tests/test_plotting.py tests/test_cli.py tests/test_reporting.py`
- `.venv/bin/mypy src`
- `git diff --check`

Commit planned:

```bash
git commit -m "Add plot artifact summary and report links"
```

Merge status: already on `main`; no merge needed.

---

## Plot/Injection Step 6 — Injection-Recovery Fixture Schema

Status: implemented.

Added:

- `INJECTION_RECOVERY_SCHEMA_VERSION`
- `InjectionRecoveryCase`
- loader validation for `synthetic_injection_recovery_v1`
- conservative disclaimer that fixtures are not calibrated sensitivity estimates

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_injection_recovery.py
```

Merge status: already on `main`; no merge needed.

---

## Plot/Injection Step 7 — Radio Injection-Recovery Fixtures

Status: implemented.

Added radio cases for:

- recovered synthetic narrowband signal
- missed low-SNR synthetic narrowband signal

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_injection_recovery.py
```

Merge status: already on `main`; no merge needed.

---

## Plot/Injection Step 8 — Infrared Injection-Recovery Fixtures

Status: implemented.

Added infrared cases for:

- recovered synthetic infrared excess
- dust-contaminated false alarm

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_injection_recovery.py
```

Merge status: already on `main`; no merge needed.

---

## Plot/Injection Step 9 — Archival Anomaly Injection-Recovery Fixtures

Status: implemented.

Added anomaly cases for:

- recovered synthetic archival disappearance
- artifact-driven false alarm

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_injection_recovery.py
```

Merge status: already on `main`; no merge needed.

---

## Plot/Injection Step 10 — Injection-Recovery Summary CLI

Status: implemented.

Added:

- `techno-search injection-recovery-summary`
- summary counts by track, outcome, injection type, and expected pathway
- synthetic recovery rate and synthetic false-alarm fraction

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_injection_recovery.py
```

Merge status: already on `main`; no merge needed.

---

## Plot/Injection Step 11 — Injection-Recovery Summary Tests

Status: implemented.

Added tests proving:

- the fixture covers radio, infrared, and anomaly tracks
- outcomes include recovered, missed, and false alarm
- CLI output exposes track/outcome counts and synthetic rates

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_injection_recovery.py
```

Merge status: already on `main`; no merge needed.

---

## Plot/Injection Step 12 — Injection-Recovery Validation Wiring

Status: implemented.

Added:

- injection-recovery summary block in `validate-all`
- validation gate requiring fixture coverage
- injection-recovery counts and synthetic rates in `validation-summary`

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_injection_recovery.py
```

Merge status: already on `main`; no merge needed.

---

## Plot/Injection Step 13 — Injection-Recovery Docs And Status

Status: implemented.

Updated:

- `docs/CLI_USAGE.md`
- `docs/VALIDATION.md`
- `docs/ROADMAP.md`
- `docs/PROJECT_STATUS.md`

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Plot/Injection Step 14 — Full Validation And Commit

Status: implemented.

Validation passed:

- `.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing`
- `.venv/bin/ruff check .`
- `.venv/bin/mypy src`
- `git diff --check`

Result:

- 143 tests passed
- 5 tests skipped
- total coverage: 92%

Commit planned:

```bash
git commit -m "Add injection recovery summaries"
```

Merge status: already on `main`; no merge needed.

---

## Plot/Injection Step 15 — Push Main And Confirm Clean Sync

Status: implemented.

Pushed commits:

- `e882ed0 Add plot artifact summary and report links`
- `e512f7f Add injection recovery summaries`

Remote sync:

```bash
git push origin main
```

Result:

- `main` pushed to `origin/main`
- remote advanced from `e882ed0` to `e512f7f`

Merge status: already on `main`; no merge needed.

---

## Fifteen-Step Validation And Plot Artifact Expansion

User requested fifteen iterative steps:

1. Update `docs/PROJECT_STATUS.md` so "Next 3 Actions" reflects completed pushed work.
2. Update `docs/ROADMAP.md` to mark provider normalization regression summaries as complete.
3. Add `techno-search validation-summary` as a concise local health dashboard.
4. Add tests for `validation-summary`.
5. Commit and push the status/validation-summary cleanup.
6. Add a lightweight plot artifact interface for reports without requiring heavy plotting dependencies.
7. Add synthetic radio waterfall placeholder plot generation.
8. Add synthetic infrared SED placeholder plot generation.
9. Add synthetic anomaly/crossmatch placeholder plot generation.
10. Wire plot artifact references into candidate report manifests.
11. Add tests proving plots are optional and reports still pass without them.
12. Update report docs and validation docs for plot artifacts.
13. Add conservative "plot is illustrative / synthetic" language where needed.
14. Run full validation and commit.
15. Push `main` and confirm clean sync.

Each step should update this file and merge to `main` if needed.

## Validation/Plot Step 1 — Project Status Next Actions

Status: implemented.

Updated:

- `docs/PROJECT_STATUS.md` completed items for provider normalization regression coverage
- `docs/PROJECT_STATUS.md` next actions to point at dependency-free report plot artifacts

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Plot Step 2 — Roadmap Provider Normalization Status

Status: implemented.

Updated:

- Milestone 5 with the validation summary command
- Milestone 8 with provider normalization regression fixtures
- Milestone 8 with provider normalization summary in local validation

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Plot Step 3 — Validation Summary CLI

Status: implemented.

Added:

- `techno-search validation-summary`
- concise local health fields for examples, reports, schemas, calibration, score regressions, catalog cache, and provider normalization
- recommended validation commands in the JSON output

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Plot Step 4 — Validation Summary Tests

Status: implemented.

Added tests proving:

- the command exits successfully when the local health summary is clean
- candidate, schema, calibration, score-regression, catalog-cache, and provider-normalization counts are present
- the full validation command list includes mypy

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Plot Step 5 — Status And Validation Summary Commit

Status: implemented.

Validation passed:

- `.venv/bin/python -m pytest tests/test_cli.py tests/test_docs.py`
- `.venv/bin/ruff check src/techno_search/cli.py tests/test_cli.py`
- `.venv/bin/mypy src`
- `git diff --check`

Commit planned:

```bash
git commit -m "Add validation summary command"
```

Merge status: already on `main`; no merge needed.

---

## Validation/Plot Step 6 — Lightweight Plot Artifact Interface

Status: implemented.

Added:

- `techno_search.plotting.PlotArtifact`
- dependency-free SVG writing via `write_synthetic_plot_artifacts(...)`
- manifest-safe plot artifact entries with media type, kind, track, synthetic flag, and disclaimer

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_plotting.py tests/test_reporting.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Plot Step 7 — Radio Waterfall Placeholder

Status: implemented.

Added:

- synthetic radio waterfall-style SVG generation
- SNR and drift-rate proxy annotations
- conservative SVG description/disclaimer text

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_plotting.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Plot Step 8 — Infrared SED Placeholder

Status: implemented.

Added:

- synthetic infrared SED-style SVG generation
- IR excess and confusion proxy annotations
- dependency-free rendering from candidate feature values

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_plotting.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Plot Step 9 — Anomaly Crossmatch Placeholder

Status: implemented.

Added:

- synthetic archival crossmatch-style SVG generation
- crossmatch-confidence and artifact proxy annotations
- conservative generated diagnostic text

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_plotting.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Plot Step 10 — Plot References In Manifests

Status: implemented.

Added:

- report manifest `plot_artifacts` entries
- batch manifest `plot_artifact_paths`
- generated plot paths in `ReportPaths`
- CLI support for default plot generation and `--no-plot-artifacts`

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_reporting.py tests/test_cli.py tests/test_examples.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Plot Step 11 — Optional Plot Tests

Status: implemented.

Added tests proving:

- report writers can skip plot artifacts
- manifests can contain an empty `plot_artifacts` list
- report manifest validation accepts missing optional plot artifact fields
- CLI `--no-plot-artifacts` suppresses SVG generation

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_reporting.py tests/test_validation.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Plot Step 12 — Plot Artifact Docs

Status: implemented.

Updated:

- `docs/CLI_USAGE.md` for generated SVG artifacts and `--no-plot-artifacts`
- `docs/VALIDATION.md` for optional plot artifact validation behavior
- `schemas/report_manifest.schema.json` and `schemas/batch_manifest.schema.json` for plot artifact metadata

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_json_schemas.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Plot Step 13 — Conservative Plot Language

Status: implemented.

Added:

- shared plot artifact disclaimer
- SVG title/description disclaimers
- Markdown report plot artifact note
- docs language describing plot artifacts as optional review context

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_reporting.py tests/test_plotting.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Plot Step 14 — Full Validation And Commit

Status: implemented.

Validation passed:

- `.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing`
- `.venv/bin/ruff check .`
- `.venv/bin/mypy src`
- `git diff --check`

Result:

- 138 tests passed
- 5 tests skipped
- total coverage: 92%

Commit planned:

```bash
git commit -m "Add synthetic plot artifacts to reports"
```

Merge status: already on `main`; no merge needed.

---

## Validation/Plot Step 15 — Push Main And Confirm Clean Sync

Status: implemented.

Pushed commits:

- `620b283 Add validation summary command`
- `dad5ddb Add synthetic plot artifacts to reports`

Remote sync:

```bash
git push origin main
```

Result:

- `main` pushed to `origin/main`
- remote advanced from `620b283` to `dad5ddb`

Merge status: already on `main`; no merge needed.

---

## Fifteen-Step Catalog Cache And Normalization Expansion

User requested fifteen iterative steps:

1. Add catalog cache storage implementation behind `CatalogCachePolicy`.
2. Add tests proving catalog cache storage never writes into committed paths.
3. Add `techno-search catalog-cache-summary`.
4. Add catalog cache summary tests.
5. Update docs/status and commit catalog cache storage work.
6. Add provider cache integration tests for Gaia, IRSA, VizieR, SIMBAD, and Breakthrough Listen.
7. Add provider-specific normalization refinements for Gaia TAP metadata.
8. Add provider-specific normalization refinements for IRSA catalog metadata.
9. Add provider-specific normalization refinements for VizieR catalog metadata.
10. Add provider-specific normalization refinements for SIMBAD object metadata.
11. Add provider-specific normalization refinements for Breakthrough Listen file metadata.
12. Add a provider normalization regression fixture set.
13. Wire provider normalization summaries into `validate-all`.
14. Run full validation and commit.
15. Push `main` to GitHub and confirm clean sync.

Each step should update this file and merge to `main` if needed.

## Catalog Cache/Normalization Step 1 — Catalog Cache Storage

Status: implemented.

Added:

- `CatalogCache` metadata-only storage helper
- policy-backed metadata paths and suffix checks
- required provenance field validation
- metadata size enforcement
- read/write/summary methods that do not implement catalog ingestion

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache/Normalization Step 2 — Catalog Cache Storage Tests

Status: implemented.

Added tests proving:

- catalog cache writes only under the configured policy root
- required provenance fields are enforced
- oversized metadata is rejected
- cache paths under project `cache/` are rejected by commit-path validation
- local override paths outside the project are allowed by commit-path validation

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache/Normalization Step 3 — Catalog Cache Summary CLI

Status: implemented.

Added:

- `techno-search catalog-cache-summary`
- optional `--cache-root`
- metadata counts without reading catalog payloads
- no directory creation for empty cache roots

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache/Normalization Step 4 — Catalog Cache Summary Tests

Status: implemented.

Added tests proving:

- `catalog-cache-summary` reports empty cache roots without creating directories
- populated metadata directories report provider counts and byte totals
- summary output remains metadata-only and does not implement ingestion

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache/Normalization Step 5 — Catalog Cache Docs And Commit

Status: implemented.

Updated:

- `docs/CLI_USAGE.md`
- `docs/CATALOG_CACHE_POLICY.md`
- `docs/PROJECT_STATUS.md`
- `docs/ROADMAP.md`
- `CLAUDE.md` handoff notes for catalog cache storage

Commit planned:

```bash
git commit -m "Add catalog cache storage"
```

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py tests/test_cli.py tests/test_docs.py
.venv/bin/ruff check .
.venv/bin/mypy src
git diff --check
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache/Normalization Step 6 — Provider Cache Integration Tests

Status: implemented.

Added:

- cache integration coverage for Gaia, IRSA, VizieR, SIMBAD, and Breakthrough Listen
- injected transports for networked providers
- local temporary file metadata for Breakthrough Listen
- proof that a second fetch reuses `LiveProviderCache`

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache/Normalization Step 7 — Gaia Normalization Refinements

Status: implemented.

Added Gaia response metadata fields for:

- TAP response format
- query endpoint
- content byte count
- raw provider field names
- normalized row field names

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache/Normalization Step 8 — IRSA Normalization Refinements

Status: implemented.

Added IRSA response metadata fields for:

- catalog response format
- query endpoint
- content byte count
- normalized row count
- normalized row field names

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache/Normalization Step 9 — VizieR Normalization Refinements

Status: implemented.

Added VizieR response metadata fields for:

- TSV response format
- query endpoint
- normalized row count
- normalized row field names

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache/Normalization Step 10 — SIMBAD Normalization Refinements

Status: implemented.

Added SIMBAD response metadata fields for:

- object lookup response format
- query endpoint
- normalized row count
- normalized row field names

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache/Normalization Step 11 — Breakthrough Listen Normalization Refinements

Status: implemented.

Added Breakthrough Listen response metadata fields for:

- local-file response format
- file name and suffix
- file existence
- content-read flag
- size bytes when available

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache/Normalization Step 12 — Provider Normalization Regression Fixtures

Status: implemented.

Added:

- `tests/fixtures/provider_normalization_regressions.json`
- regression summary loader
- regression summary test covering all five providers

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache/Normalization Step 13 — Validate-All Provider Normalization Summary

Status: implemented.

Added:

- provider normalization regression summary in `techno-search validate-all`
- validation gate requiring the provider normalization summary to cover current cases
- CLI assertion for provider normalization coverage

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache/Normalization Step 14 — Full Validation And Commit

Status: implemented.

Validation passed:

- `.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing`
- `.venv/bin/ruff check .`
- `.venv/bin/mypy src`
- `git diff --check`

Result:

- 131 tests passed
- 5 tests skipped
- total coverage: 92%

Commit planned:

```bash
git commit -m "Add provider normalization regression summary"
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache/Normalization Step 15 — Push Main And Confirm Clean Sync

Status: implemented.

Pushed commits:

- `1ac5959 Add catalog cache storage`
- `e4d687b Add provider normalization regression summary`

Remote sync:

```bash
git push origin main
```

Result:

- `main` pushed to `origin/main`
- remote advanced from `786507b` to `e4d687b`

Merge status: already on `main`; no merge needed.

---

## Fifteen-Step Remaining Provider Expansion

User requested fifteen iterative steps:

1. Add guarded VizieR live client with mocked transport.
2. Add VizieR mocked response fixture.
3. Add VizieR `integration_live` marker test without default network access.
4. Update `CLAUDE.md`, `PROJECT_STATUS`, `ROADMAP`, and provider-interface docs.
5. Run validation and commit VizieR work.
6. Add guarded SIMBAD live client with mocked transport.
7. Add SIMBAD mocked response fixture.
8. Add SIMBAD `integration_live` marker test.
9. Update docs/status and commit SIMBAD work.
10. Add guarded Breakthrough Listen local-file metadata client.
11. Add Breakthrough Listen mocked/local metadata fixture.
12. Add local-file ingestion tests proving no large data is committed.
13. Wire provider-client summaries to distinguish `implemented`, `networked`, and `local_file_only`.
14. Run full validation and commit.
15. Push `main` to GitHub and confirm branch is clean/synced.

Each step should update this file and merge to `main` if needed.

## Remaining Provider Expansion Step 1 — Guarded VizieR Client

Status: implemented.

Added:

- guarded VizieR catalog client using `TECHNO_SEARCH_ENABLE_LIVE_DATA`
- injectable HTTP GET byte fetcher for non-networked tests
- bounded response reads
- VizieR TSV row normalization through the shared delimited-table helper

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Remaining Provider Expansion Step 2 — VizieR Mock Fixture

Status: implemented.

Added:

- `tests/fixtures/live_metadata/vizier_mock_response.metadata.json`
- fixture loader coverage for mocked VizieR response metadata
- live fixture summary expected count update

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Remaining Provider Expansion Step 3 — VizieR Integration Marker

Status: implemented.

Added:

- VizieR client test proving disabled-by-default behavior
- injected transport test for opt-in VizieR metadata fetches
- `integration_live`-marked VizieR test with injected transport and no default network dependency

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Remaining Provider Expansion Step 4 — VizieR Status Docs

Status: implemented.

Updated:

- `docs/PROJECT_STATUS.md`
- `docs/ROADMAP.md`
- `docs/LIVE_PROVIDER_INTERFACES.md`
- `CLAUDE.md` handoff notes for the VizieR step

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_cli.py tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Remaining Provider Expansion Step 5 — VizieR Validation And Commit

Status: implemented.

Validation passed:

- `.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing`
- `.venv/bin/ruff check .`
- `.venv/bin/mypy src`
- `git diff --check`

Result:

- 113 tests passed, 4 skipped
- total coverage: 93%

Commit planned:

```bash
git commit -m "Add guarded VizieR provider client"
```

Merge status: already on `main`; no merge needed.

---

## Remaining Provider Expansion Step 6 — Guarded SIMBAD Client

Status: implemented.

Added:

- guarded SIMBAD object-lookup client using `TECHNO_SEARCH_ENABLE_LIVE_DATA`
- injectable HTTP GET byte fetcher for non-networked tests
- bounded response reads
- SIMBAD tabular metadata normalization through the shared delimited-table helper

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Remaining Provider Expansion Step 7 — SIMBAD Mock Fixture

Status: implemented.

Added:

- `tests/fixtures/live_metadata/simbad_mock_response.metadata.json`
- fixture loader coverage for mocked SIMBAD response metadata
- live fixture summary expected count update

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Remaining Provider Expansion Step 8 — SIMBAD Integration Marker

Status: implemented.

Added:

- SIMBAD client test proving disabled-by-default behavior
- injected transport test for opt-in SIMBAD metadata fetches
- `integration_live`-marked SIMBAD test with injected transport and no default network dependency

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Remaining Provider Expansion Step 9 — SIMBAD Docs, Validation, And Commit

Status: implemented.

Updated:

- `docs/PROJECT_STATUS.md`
- `docs/ROADMAP.md`
- `docs/LIVE_PROVIDER_INTERFACES.md`
- `CLAUDE.md` handoff notes for the SIMBAD step

Validation passed:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/ruff check .
.venv/bin/mypy src
git diff --check
```

Commit planned:

```bash
git commit -m "Add guarded SIMBAD provider client"
```

Merge status: already on `main`; no merge needed.

Result:

- 114 tests passed, 5 skipped
- total coverage: 92%

---

## Remaining Provider Expansion Step 10 — Breakthrough Listen Local Metadata Client

Status: implemented.

Added:

- guarded Breakthrough Listen local-file metadata client
- `TECHNO_SEARCH_ENABLE_LIVE_DATA` opt-in requirement
- file `stat()` metadata without reading observation contents
- local-file-only client metadata fields

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Remaining Provider Expansion Step 11 — Breakthrough Listen Local Fixture

Status: implemented.

Added:

- `tests/fixtures/live_metadata/breakthrough_listen_local_file_mock_response.metadata.json`
- fixture loader coverage for local-file metadata response
- live fixture summary expected count update

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Remaining Provider Expansion Step 12 — Breakthrough Listen Local-File Tests

Status: implemented.

Added tests proving:

- local-file metadata client is disabled by default
- enabled client uses file `stat()` metadata only
- missing files are reported without reading contents
- local-file coverage uses temporary files rather than committed observation data
- `content_read` remains false

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Remaining Provider Expansion Step 13 — Live Client Summary Capability Fields

Status: implemented.

Added:

- `networked` field in `live-client-summary`
- `local_file_only` field in `live-client-summary`
- CLI tests for implemented/networked/local-file-only provider capability maps
- docs noting networked versus local-file-only client summaries

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Remaining Provider Expansion Step 14 — Breakthrough/Summary Validation And Commit

Status: implemented.

Updated:

- `docs/PROJECT_STATUS.md`
- `docs/ROADMAP.md`
- Breakthrough Listen local metadata tests and fixture
- live-client summary capability tests and docs

Validation passed:

- `.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing`
- `.venv/bin/ruff check .`
- `.venv/bin/mypy src`
- `git diff --check`

Result:

- 117 tests passed, 5 skipped
- total coverage: 92%

Commit planned:

```bash
git commit -m "Add Breakthrough Listen local metadata client"
```

Merge status: already on `main`; no merge needed.

---

## Remaining Provider Expansion Step 15 — Push Provider Commits

Status: implemented.

Pushed to GitHub:

- `d17205c Add guarded VizieR provider client`
- `90f7fc1 Add guarded SIMBAD provider client`
- `2dab9bd Add Breakthrough Listen local metadata client`

Push result:

```bash
git push origin main
```

Remote update:

```text
d505b99..2dab9bd  main -> main
```

Merge status: already on `main`; no merge needed.

---

## Fifteen-Step Live Provider Expansion

User requested fifteen iterative steps:

1. Push `main` to GitHub with required token scopes.
2. Add a catalog-cache validator CLI command for pre-commit/release checks.
3. Add tests for that validator CLI command.
4. Wire catalog-cache validation into `validate-all`.
5. Update release docs to include the new validator output.
6. Add a real-provider implementation plan doc for Gaia, IRSA, VizieR, SIMBAD, and Breakthrough Listen.
7. Add a provider-client result normalization interface.
8. Add tests for provider normalization contracts.
9. Implement the Gaia client behind `TECHNO_SEARCH_ENABLE_LIVE_DATA=1`.
10. Add mocked Gaia integration fixtures.
11. Add Gaia live integration test markers without enabling network by default.
12. Update `PROJECT_STATUS`, `ROADMAP`, and `CLAUDE.md`.
13. Run full validation and commit.
14. Repeat the same client pattern for IRSA as the next provider.
15. Push the new commits once GitHub credentials are working.

Each step should update this file and merge to `main` if needed.

## Live Provider Expansion Step 1 — Push Main

Status: implemented.

Result:

- `git push origin main` returned `Everything up-to-date`
- local `main` and `origin/main` were already synchronized

Merge status: already on `main`; no merge needed.

---

## Live Provider Expansion Step 2 — Catalog Cache Validator CLI

Status: implemented.

Added:

- `techno-search catalog-cache-validate`
- structured JSON output for catalog cache commit-path validation
- nonzero exit for forbidden catalog cache paths

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider Expansion Step 3 — Validator CLI Tests

Status: implemented.

Added tests for:

- accepting committed fixture and docs paths
- rejecting forbidden `cache/` catalog metadata paths
- rejecting forbidden `data/` catalog paths
- returning nonzero status when forbidden paths are supplied

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider Expansion Step 4 — Validate-All Catalog Cache Wiring

Status: implemented.

Added:

- Git-tracked path collection for release-scoped catalog cache validation
- `catalog_cache_validation` block in `techno-search validate-all`
- CLI test assertion that `validate-all` reports catalog cache validation state

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider Expansion Step 5 — Release Docs Validator Output

Status: implemented.

Updated:

- `docs/CLI_USAGE.md` with `catalog-cache-validate`
- `docs/CLI_USAGE.md` with `validate-all` catalog cache validation output
- `docs/VALIDATION.md` with direct catalog cache path validation
- `docs/RELEASE_CHECKLIST.md` with validator and `validate-all` commands

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider Expansion Step 6 — Provider Implementation Plan

Status: implemented.

Added:

- `docs/LIVE_PROVIDER_IMPLEMENTATION_PLAN.md`
- shared real-provider requirements
- provider rollout order for Gaia, IRSA, VizieR, SIMBAD, and Breakthrough Listen
- done criteria preserving opt-in network access, provenance, fixtures, and catalog cache guardrails

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider Expansion Step 7 — Provider Normalization Interface

Status: implemented.

Added:

- `ProviderResponseNormalizer` protocol
- `ProvenanceOnlyResponseNormalizer`
- shared `provider_response_metadata(...)`
- default provenance-only normalization path for adapters

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider Expansion Step 8 — Provider Normalization Contract Tests

Status: implemented.

Added tests for:

- response shape metadata
- row-count summaries
- provider-status summaries
- provenance-only normalizer request context preservation

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider Expansion Step 9 — Guarded Gaia Live Client

Status: implemented.

Added:

- guarded Gaia TAP client using `TECHNO_SEARCH_ENABLE_LIVE_DATA`
- injectable HTTP POST byte fetcher for non-networked tests
- bounded response reads
- Gaia TAP JSON row normalization
- live-client summary now reports Gaia as implemented while preserving opt-in requirement

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider Expansion Step 10 — Mocked Gaia Integration Fixture

Status: implemented.

Added:

- `tests/fixtures/live_metadata/gaia_tap_mock_response.metadata.json`
- fixture loader coverage for mocked Gaia TAP response metadata
- live fixture summary expected count update

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider Expansion Step 11 — Gaia Integration Marker

Status: implemented.

Added:

- `integration_live`-marked Gaia client test
- opt-in skip guard using `TECHNO_SEARCH_ENABLE_LIVE_DATA`
- injected transport so the marked test still has no default network dependency

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider Expansion Step 12 — Status And Roadmap Updates

Status: implemented.

Updated:

- `docs/PROJECT_STATUS.md` completed, in-progress, and next-action entries
- `docs/ROADMAP.md` reporting and live-data milestone entries
- `docs/LIVE_PROVIDER_INTERFACES.md` to identify Gaia as the first guarded implementation
- `docs/CLI_USAGE.md` live-client wording
- `CLAUDE.md` handoff notes for this step

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_cli.py tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider Expansion Step 13 — Validation And Commit

Status: implemented.

Validation passed:

- `.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing`
- `.venv/bin/ruff check .`
- `.venv/bin/mypy src`
- `git diff --check`

Result:

- 111 tests passed, 2 skipped
- total coverage: 93%

Commit planned:

```bash
git commit -m "Add guarded Gaia provider client"
```

Merge status: already on `main`; no merge needed.

---

## Live Provider Expansion Step 14 — Guarded IRSA Provider Client

Status: implemented.

Added:

- guarded IRSA catalog client using `TECHNO_SEARCH_ENABLE_LIVE_DATA`
- injectable HTTP GET byte fetcher for non-networked tests
- bounded response reads
- small delimited table row normalization
- mocked IRSA response fixture
- opt-in `integration_live` marker coverage with injected transport
- status, roadmap, and provider interface docs updates

Validation passed:

- `.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing`
- `.venv/bin/ruff check .`
- `.venv/bin/mypy src`
- `git diff --check`

Result:

- 112 tests passed, 3 skipped
- total coverage: 93%

Commit planned:

```bash
git commit -m "Add guarded IRSA provider client"
```

Merge status: already on `main`; no merge needed.

---

## Live Provider Expansion Step 15 — Push Provider Commits

Status: implemented.

Pushed to GitHub:

- `6056039 Add guarded Gaia provider client`
- `fd5d48c Add guarded IRSA provider client`

Push result:

```bash
git push origin main
```

Remote update:

```text
27693f9..fd5d48c  main -> main
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache Guardrail Step 7 — Validator Tests

Status: implemented.

Added tests for:

- rejecting catalog cache paths under `cache/`
- rejecting catalog data paths under `data/`
- rejecting generated catalog artifacts under `artifacts/`
- allowing small committed docs and fixture paths outside forbidden roots

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache Guardrail Step 8 — Release Checklist Gate

Status: implemented.

Updated:

- `docs/RELEASE_CHECKLIST.md` artifact checks
- release validation command list with `techno-search catalog-cache-policy`
- release gate requiring catalog cache policy and commit-path validator before real provider clients

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache Guardrail Step 9 — Status And Roadmap Updates

Status: implemented.

Updated:

- `docs/PROJECT_STATUS.md` completed and in-progress entries
- `docs/PROJECT_STATUS.md` next actions for policy-gated catalog cache storage
- `docs/ROADMAP.md` reporting and live-data milestones
- `CLAUDE.md` handoff notes for this step

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_cli.py tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache Guardrail Step 10 — Validation And Commit

Status: implemented.

Validation passed:

- `.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing`
- `.venv/bin/ruff check .`
- `.venv/bin/mypy src`
- `git diff --check`

Result:

- 106 tests passed, 1 skipped
- total coverage: 94%

Commit planned:

```bash
git commit -m "Add catalog cache guardrails"
```

Merge status: already on `main`; no merge needed.

---

## Step 1 — Report File Writers

Status: implemented.

Added:

- `write_candidate_reports(scored, output_dir, filename_prefix=None)`
- `ReportPaths`
- safe filename generation from candidate IDs or explicit prefixes
- tests proving Markdown and JSON files are written with conservative content

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_reporting.py
```

---

## Step 2 — Synthetic Radio Prototype

Status: implemented.

Added:

- `src/techno_search/radio/`
- `RadioHit` and `RfiBand`
- synthetic hit-table parsing
- known RFI band overlap scoring
- ON/OFF presence feature extraction
- recurrence, frequency persistence, metadata, and data-quality features
- tests proving a clean synthetic radio candidate scores above an RFI-like candidate

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_radio_prototype.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache Guardrail Step 6 — Commit Path Validator

Status: implemented.

Added:

- `CATALOG_CACHE_FORBIDDEN_COMMITTED_ROOTS`
- `validate_catalog_cache_commit_paths(...)`
- helper for project-relative path checks
- rejection of paths under `data/`, `cache/`, and `artifacts/`

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache Guardrail Step 5 — Policy Docs Warning

Status: implemented.

Updated:

- CLI docs for `catalog-cache-policy`
- `docs/CATALOG_CACHE_POLICY.md` to state the policy command is informational only
- data policy note for future catalog cache metadata versus live-provider metadata cache

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache Guardrail Step 4 — Catalog Cache Policy CLI

Status: implemented.

Added:

- `catalog_cache_policy_summary(...)`
- `techno-search catalog-cache-policy`
- optional `--cache-root`
- CLI test proving the command prints policy metadata without creating directories

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache Guardrail Step 3 — Policy Tests

Status: implemented.

Added tests for:

- default catalog cache root under `cache/catalog_metadata`
- allowed metadata suffixes
- maximum metadata file size default
- no directory creation
- local `TECHNO_SEARCH_CATALOG_CACHE_DIR` override

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache Guardrail Step 2 — Catalog Cache Policy

Status: implemented.

Added:

- `CATALOG_CACHE_DIR_ENV_VAR`
- `DEFAULT_CATALOG_CACHE_DIR`
- `configured_catalog_cache_dir(...)`
- `CatalogCachePolicy`
- JSON-serializable policy representation that does not create directories or implement ingestion

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Ten-Step Catalog Cache Guardrail Expansion

User requested ten iterative steps:

1. Add catalog cache metadata schema docs, separate from local live-provider metadata cache files.
2. Add `CatalogCachePolicy` dataclass for cache root, max metadata file size, allowed suffixes, and provenance requirements.
3. Add tests for catalog cache policy defaults and local override behavior.
4. Add `techno-search catalog-cache-policy` to print policy without creating cache files.
5. Add docs warning that catalog cache policy is not catalog ingestion yet.
6. Add validation helper that rejects committed catalog cache paths under `data/`, `cache/`, and `artifacts/`.
7. Add tests for the catalog cache path validator.
8. Add release checklist item for catalog cache policy/validator before real provider clients.
9. Update `PROJECT_STATUS`, `ROADMAP`, and `CLAUDE.md`.
10. Run full validation, commit, and report branch state.

## Catalog Cache Guardrail Step 1 — Metadata Schema Docs

Status: implemented.

Added:

- `docs/CATALOG_CACHE_POLICY.md`
- catalog cache metadata field list
- storage boundary between live-provider metadata cache and future catalog cache metadata
- explicit no-ingestion and no-interpretation guardrails

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

## Ten-Step Config/CI Expansion

User requested ten iterative steps:

1. Push/publish decision.
2. Add README links to examples.
3. Add CLI quickstart test.
4. Add batch manifest regeneration test.
5. Add report manifest schema checks.
6. Add calibration fixture loader.
7. Add calibration summary CLI.
8. Add scoring config use in pathway.
9. Add track config use in prototypes.
10. Add first CI workflow.

Each step should update this file and merge to `main` if needed.

---

## Config/CI Step 1 — Publish Decision

Status: implemented as documentation.

Updated:

- `docs/PUBLISHING.md`
- recent local commit list
- owner-controlled publication recommendation
- reminder that direct automated push remains out of scope

Merge status: already on `main`; no merge needed.

---

## Config/CI Step 2 — README Example Links

Status: implemented.

Updated README quickstart with links to:

- single radio Markdown packet
- single radio manifest
- batch manifest
- batch radio packet
- batch infrared packet
- batch anomaly packet

Merge status: already on `main`; no merge needed.

---

## Config/CI Step 3 — README Quickstart Test

Status: implemented.

Added:

- README quickstart command assertions
- README linked example artifact existence checks

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Config/CI Step 4 — Batch Manifest Regeneration Test

Status: implemented.

Added:

- `score_batch(...)` regeneration test using `examples/candidates`
- expected candidate set assertions
- regenerated Markdown/JSON/manifest file checks

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Config/CI Step 5 — Manifest Schema Checks

Status: implemented.

Added:

- expected per-candidate manifest field set
- expected batch manifest field set
- expected batch report entry field set
- tests for single example manifests and batch manifests

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_examples.py
```

Merge status: already on `main`; no merge needed.

---

## Config/CI Step 6 — Calibration Fixture Loader

Status: implemented.

Added:

- `src/techno_search/calibration.py`
- `CalibrationFixture`
- `CalibrationSummary`
- `load_calibration_fixtures(...)`
- `summarize_calibration_fixtures(...)`
- tests using the loader instead of ad hoc JSON parsing

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_calibration_fixtures.py
```

Merge status: already on `main`; no merge needed.

---

## Config/CI Step 7 — Calibration Summary CLI

Status: implemented.

Added:

- `techno-search calibration-summary`
- optional `--fixture-path`
- JSON output using `CalibrationSummary.as_dict()`
- CLI test for fixture counts
- CLI usage docs

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Five-Step Quickstart/Batch/Calibration Expansion

User requested five iterative steps:

1. Add README quickstart.
2. Add batch example artifacts.
3. Add aggregate manifest tests.
4. Add CLI docs tests.
5. Add calibration expansion fixtures.

Each step should update this file and merge to `main` if needed.

---

## Quickstart Step 1 — README Quickstart

Status: implemented.

Added:

- local environment install command
- single-candidate CLI scoring command
- report-writing command
- batch scoring command
- conservative review-packet warning

Merge status: already on `main`; no merge needed.

---

## Quickstart Step 2 — Batch Example Artifacts

Status: implemented.

Generated with:

```bash
.venv/bin/techno-search score-batch examples/candidates examples/batch_reports
```

Added:

- per-candidate Markdown/JSON/manifest artifacts in `examples/batch_reports/`
- aggregate `examples/batch_reports/batch_manifest.json`

Merge status: already on `main`; no merge needed.

---

## Quickstart Step 3 — Aggregate Manifest Tests

Status: implemented.

Added:

- tests for `examples/batch_reports/batch_manifest.json`
- candidate coverage assertions
- per-candidate path existence assertions
- pathway and track assertions
- conservative disclaimer checks for batch Markdown reports

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_examples.py
```

Merge status: already on `main`; no merge needed.

---

## Quickstart Step 4 — CLI Docs Tests

Status: implemented.

Added:

- `tests/test_docs.py`
- `docs/CLI_USAGE.md` path/command checks
- `docs/PUBLISHING.md` validation-command checks
- existence checks for referenced example files

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Quickstart Step 5 — Calibration Expansion Fixtures

Status: implemented.

Added false-positive fixtures for:

- radio band-edge artifact
- radio instrumental artifact
- infrared AGB-like colors
- infrared bad photometry
- archival moving object
- archival catalog mismatch

Updated:

- `tests/fixtures/calibration_false_positives.json`
- `docs/CALIBRATION_FIXTURES.md`

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_calibration_fixtures.py
```

Merge status: already on `main`; no merge needed.

---

## Five-Step Docs/Batch CLI Expansion

User requested five iterative steps:

1. Push or publish safely.
2. Add CLI usage docs.
3. Add calibration documentation.
4. Add batch scoring CLI.
5. Add installed-console-script test.

Each step should update this file and merge to `main` if needed.

---

## Docs/Batch Step 1 — Safe Publish Options

Status: implemented locally.

Added:

- `docs/PUBLISHING.md`
- current local commit state
- note that automated `git push origin main` was blocked by environment policy
- safe owner-controlled publication options
- pre-publish validation checklist

Merge status: already on `main`; no merge needed.

---

## Docs/Batch Step 2 — CLI Usage Docs

Status: implemented.

Added:

- `docs/CLI_USAGE.md`
- install and help instructions
- single-candidate scoring examples
- report writing examples
- normalized input JSON shape
- output and manifest expectations
- conservative CLI guardrails

Merge status: already on `main`; no merge needed.

---

## Docs/Batch Step 3 — Calibration Documentation

Status: implemented.

Added:

- `docs/CALIBRATION_FIXTURES.md`
- fixture table by false-positive class
- expected pathway documentation
- requirements for adding future fixtures
- future fixture expansion list
- calibration guardrails

Merge status: already on `main`; no merge needed.

---

## Docs/Batch Step 4 — Batch Scoring CLI

Status: implemented.

Added:

- `techno-search score-batch INPUT_DIR OUTPUT_DIR`
- per-candidate Markdown, JSON, and manifest output
- aggregate `batch_manifest.json`
- optional batch filename prefix
- batch CLI docs
- tests for batch scoring two synthetic candidate packets

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Docs/Batch Step 5 — Installed Console-Script Smoke Test

Status: implemented.

Added:

- `tests/test_console_script.py`
- direct `.venv/bin/techno-search score ...` subprocess smoke test
- JSON parse assertion for installed console script output

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_console_script.py
```

Merge status: already on `main`; no merge needed.

---

## Five-Step CLI/Examples/Calibration Expansion

User requested five iterative steps:

1. Push the foundation commit.
2. Add CLI entry points.
3. Add example review packets.
4. Add calibration fixture sets.
5. Add persistence/report manifest.

Each step should update this file and merge to `main` if needed.

---

## CLI Expansion Step 1 — Push Foundation Commit

Status: blocked by environment policy.

Attempted:

```bash
git push origin main
```

Result:

- The local branch was clean and ahead of `origin/main` by one commit.
- The push was rejected by the escalation reviewer because pushing `main` mutates an external remote.
- No workaround was attempted.

Current local commit remains:

```text
5c1c6ae Build synthetic scoring foundation
```

Merge status: already on `main`; no merge needed.

---

## CLI Expansion Step 2 — CLI Entry Points

Status: implemented.

Added:

- `src/techno_search/cli.py`
- `techno-search` console script entry point
- `techno-search score candidate.json`
- optional `--output-dir` and `--prefix` report writing
- CLI tests for stdout JSON and Markdown/JSON report file output

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## CLI Expansion Step 3 — Example Review Packets

Status: implemented.

Added:

- `examples/candidates/radio_clean_candidate.json`
- `examples/candidates/infrared_clean_candidate.json`
- `examples/candidates/anomaly_clean_candidate.json`
- generated Markdown and JSON packets under `examples/reports/`
- tests proving example packets exist and include conservative disclaimers

Generation command shape:

```bash
.venv/bin/python -m techno_search.cli score examples/candidates/radio_clean_candidate.json --output-dir examples/reports --prefix example-radio-clean
```

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_examples.py
```

Merge status: already on `main`; no merge needed.

---

## CLI Expansion Step 4 — Calibration Fixture Sets

Status: implemented.

Added:

- `tests/fixtures/calibration_false_positives.json`
- RFI fixture
- AGN/blend fixture
- dust/YSO-style fixture
- archival image-artifact fixture
- proper-motion fixture
- survey-depth mismatch fixture
- tests proving all calibration false-positive fixtures route to `do_not_submit_false_positive`

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_calibration_fixtures.py
```

Merge status: already on `main`; no merge needed.

---

## CLI Expansion Step 5 — Report Manifest

Status: implemented; validation passed.

Added:

- manifest generation when reports are written
- `report_manifest(...)`
- `report_manifest_json(...)`
- `ReportPaths.manifest_path`
- manifest fields for candidate ID, track, pathway, output paths, config version, git commit when available, and UTC generation timestamp
- tests for persisted manifests and CLI-created manifests

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_reporting.py tests/test_cli.py tests/test_examples.py
```

Merge status: already on `main`; no merge needed.

Overall status for this five-step batch:

- Step 1 push was blocked by environment policy.
- Steps 2-5 were implemented locally on `main`.
- Full validation passed with 38 tests.
- A local commit should be created after this note.

---

## Five-Step Expansion

User requested five iterative steps:

1. Add radio waterfall placeholder/report interface.
2. Add synthetic radio injection tests.
3. Start infrared prototype.
4. Start archival anomaly prototype.
5. Commit the current foundation.

Each step should update this file and merge to `main` if needed.

---

## Expansion Step 1 — Radio Diagnostic Placeholder/Report Interface

Status: implemented.

Added:

- `RadioDiagnosticPaths`
- optional diagnostic fields in radio candidate feature packets
- Markdown report `Diagnostics` section
- tests for diagnostic placeholder propagation

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_radio_prototype.py tests/test_reporting.py
```

Merge status: already on `main`; no merge needed.

---

## Expansion Step 2 — Synthetic Radio Injection Tests

Status: implemented.

Added:

- `SyntheticRadioInjection`
- injection hit-row generation
- `injection_recovery_score(...)`
- radio candidate feature propagation for `injection_recovery_score`
- tests proving recovered injections improve candidate-interest posterior relative to missed injections

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_radio_injection.py tests/test_radio_prototype.py
```

Merge status: already on `main`; no merge needed.

---

## Expansion Step 3 — Infrared Prototype

Status: implemented.

Added:

- `src/techno_search/infrared/`
- `InfraredSource`
- synthetic Gaia/WISE-like row normalization
- derived IR-excess, SED residual, and stellar-solution features
- AGN, dust, confusion, photometric-quality, and artifact feature propagation
- tests proving a clean synthetic infrared-excess candidate scores above an AGN/confused source

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_infrared_prototype.py
```

Merge status: already on `main`; no merge needed.

---

## Expansion Step 4 — Archival Anomaly Prototype

Status: implemented.

Added:

- `src/techno_search/anomalies/`
- `ArchivalAnomaly`
- synthetic historical-modern source comparison normalization
- magnitude-change and modern non-detection features
- cross-match, proper-motion, survey-depth, artifact, moving-object, variability, and catalog-mismatch features
- tests proving a clean synthetic archival anomaly scores above an artifact false positive

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_anomaly_prototype.py
```

Merge status: already on `main`; no merge needed.

---

## Expansion Step 5 — Foundation Commit

Status: implemented; validation passed; commit is part of this step.

Scope to commit:

- documentation foundation updates
- local system profile
- Python package scaffold
- conservative v0 scoring and pathway core
- report packet generation and file writers
- synthetic radio prototype, diagnostic placeholders, and injection helpers
- synthetic infrared prototype
- synthetic archival anomaly prototype
- track-specific configs and tests

Validation before commit:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src
git diff --check
```

Merge status: already on `main`; no merge needed.

---

## Step 3 — Track-Specific Configs

Status: implemented.

Added:

- `configs/radio_search_v0.json`
- `configs/infrared_search_v0.json`
- `configs/anomaly_search_v0.json`
- `TrackConfig`
- `load_track_config(track)`
- tests for all three track configs

Config policy:

- Use JSON for v0 so no parser dependency is needed.
- Keep thresholds, feature defaults, assumptions, and raw metadata auditable.
- Do not let config defaults bypass false-positive evidence or provenance rules.

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_config.py
```

Merge status: already on `main`; no merge needed.

---

## Config/CI Step 8 — Scoring Config Pathway Wiring

Status: implemented.

Added:

- `score_candidate(..., thresholds=None)` support for explicit pathway thresholds
- default scoring pathway thresholds loaded from `configs/scoring_v0.json`
- regression test proving supplied thresholds change pathway routing

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_scoring.py
```

Merge status: already on `main`; no merge needed.

---

## Config/CI Step 9 — Track Config Prototype Wiring

Status: implemented.

Added:

- optional `track_config` inputs for radio, infrared, and archival anomaly prototype builders
- configured feature-default use for missing synthetic feature values
- configured provenance-completeness fallback for packets without provenance
- tests proving each prototype consumes supplied `TrackConfig` defaults

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_radio_prototype.py tests/test_infrared_prototype.py tests/test_anomaly_prototype.py
```

Merge status: already on `main`; no merge needed.

---

## Config/CI Step 10 — First CI Workflow

Status: deferred.

Reason:

- GitHub rejected the push because the current Personal Access Token does not have `workflow` scope.
- Do not include `.github/workflows/ci.yml` in pushed history until the project owner pushes with a token that has `workflow` scope.
- The intended workflow should run Python 3.11, install `.[dev]`, run non-live tests with coverage, run Ruff, and run mypy.

Validation for this step should include:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src
git diff --check
```

Merge status: already on `main`; no merge needed.

---

## Ten-Step Validation/Regression Expansion

User requested ten iterative steps:

1. Confirm GitHub push succeeds after the amended commit.
2. Keep CI workflow deferred until a token with `workflow` scope is available.
3. Add candidate JSON validation CLI.
4. Add generated report validation CLI.
5. Add JSON schema files for candidate packets and manifests.
6. Expand calibration false-positive edge cases.
7. Add score regression snapshots.
8. Add config-version provenance into scored packets and batch manifests.
9. Add golden example stable-field tests.
10. Add opt-in live-data integration scaffold.

Each step should update this file and merge to `main` if needed.

---

## Validation/Regression Step 1 — GitHub Push Confirmation

Status: confirmed.

Observation:

- Local `main` is even with `origin/main`, so the amended workflow-free history appears pushed.
- No merge was needed because work is already on `main`.

Merge status: already on `main`; no merge needed.

---

## Validation/Regression Step 2 — CI Workflow Deferred

Status: documented as deferred.

Reason:

- GitHub rejects workflow-file pushes unless the active token has `workflow` scope.
- Keep CI as a future separate commit once the project owner has a suitable token.
- Local validation remains the required gate: pytest with coverage, Ruff, mypy, and `git diff --check`.

Merge status: already on `main`; no merge needed.

---

## Validation/Regression Step 3 — Candidate Validation CLI

Status: implemented.

Added:

- `src/techno_search/validation.py`
- `ValidationResult`
- candidate mapping/file validation
- conservative-language checks for unsupported phrases
- `techno-search validate-candidate`

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Regression Step 4 — Report Validation CLI

Status: implemented.

Added:

- generated report packet validation
- per-candidate report manifest validation
- required disclaimer and evidence-section checks
- `techno-search validate-reports`
- CLI tests for generated report directories

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Regression Step 5 — JSON Schema Artifacts

Status: implemented.

Added:

- `schemas/candidate_packet.schema.json`
- `schemas/report_manifest.schema.json`
- `schemas/batch_manifest.schema.json`
- schema parseability and example-field coverage tests

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_json_schemas.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Regression Step 6 — Expanded Calibration Edge Cases

Status: implemented.

Added false-positive fixtures for:

- radio satellite-like recurrence
- infrared extragalactic contamination
- archival anomaly variable-star behavior

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_calibration_fixtures.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Regression Step 7 — Score Regression Snapshots

Status: implemented.

Added:

- `tests/fixtures/score_regressions.json`
- stable score/pathway snapshots for the three example candidates
- regression test comparing example scores and posteriors to snapshots

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_score_regressions.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Regression Step 8 — Config-Version Provenance

Status: implemented.

Added:

- top-level `config_version` in candidate JSON packets
- config-version fallback of `scoring_v0` for sparse provenance
- `config_version` in batch manifests and batch report entries
- updated schema and example artifact checks

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_reporting.py tests/test_cli.py tests/test_examples.py tests/test_json_schemas.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Regression Step 9 — Golden Example Stable Fields

Status: implemented.

Added:

- temporary regeneration of example batch reports in tests
- stable-field comparison against committed example packets
- timestamp/path-independent golden coverage for scores, pathways, evidence, disclaimer, and config version

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_examples.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Regression Step 10 — Opt-In Live-Data Scaffold

Status: implemented.

Added:

- `src/techno_search/live_data.py`
- `TECHNO_SEARCH_ENABLE_LIVE_DATA` opt-in guard
- base `LiveDataClient` scaffold with no default network access
- default disabled test and skipped `integration_live` scaffold test

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Ten-Step Documentation/Release Expansion

User requested ten iterative tasks:

1. Push commit `9ef0b8a` to GitHub.
2. Add README and CLI docs for `validate-candidate` and `validate-reports`.
3. Add schema links to README and `docs/PIPELINE_SPEC.md`.
4. Add `docs/LIVE_DATA_INTEGRATIONS.md`.
5. Add malformed validation tests.
6. Add `techno-search schema-paths`.
7. Add `techno-search score-regression-summary`.
8. Add conservative release checklist doc.
9. Update project status and roadmap.
10. Add a GitHub-safe CI template outside `.github/workflows`.

Each step should update this file and merge to `main` if needed.

---

## Documentation/Release Step 1 — Push Attempt

Status: blocked by environment policy.

Result:

- Attempted `git push origin main`.
- The environment rejected the push because updating the external GitHub `main` branch is disallowed by tenant policy.
- No workaround was attempted.

Merge status: already on `main`; no merge needed.

---

## Documentation/Release Step 2 — Validation Command Docs

Status: implemented.

Updated:

- README quickstart with `validate-candidate`
- README quickstart with `validate-reports`
- `docs/CLI_USAGE.md` validation command sections

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Documentation/Release Step 3 — Schema Links

Status: implemented.

Updated:

- README links to candidate packet, report manifest, and batch manifest schemas
- `docs/PIPELINE_SPEC.md` schema references for shared candidate and manifest outputs

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_json_schemas.py
```

Merge status: already on `main`; no merge needed.

---

## Documentation/Release Step 4 — Live Data Integration Policy

Status: implemented.

Added:

- `docs/LIVE_DATA_INTEGRATIONS.md`
- opt-in guard documentation for `TECHNO_SEARCH_ENABLE_LIVE_DATA`
- `integration_live` test policy
- provenance and cache/credential guardrails

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Documentation/Release Step 5 — Malformed Validation Tests

Status: implemented.

Added:

- bad candidate track validation test
- non-mapping feature validation test
- missing report manifest validation test
- empty report directory validation test

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_validation.py
```

Merge status: already on `main`; no merge needed.

---

## Documentation/Release Step 6 — Schema Paths CLI

Status: implemented.

Added:

- `techno-search schema-paths`
- deterministic schema path JSON output
- CLI test for schema path keys and candidate packet schema path
- CLI usage documentation

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Documentation/Release Step 7 — Score Regression Summary CLI

Status: implemented.

Added:

- `techno-search score-regression-summary`
- optional `--snapshot-path`
- snapshot counts by track and recommended pathway
- CLI test for current regression fixture coverage
- CLI usage documentation

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Documentation/Release Step 8 — Conservative Release Checklist

Status: implemented.

Added:

- `docs/RELEASE_CHECKLIST.md`
- required local validation commands
- artifact and schema release checks
- scientific-language release guardrails
- live-data and GitHub workflow-token caveats

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Documentation/Release Step 9 — Status And Roadmap Updates

Status: implemented.

Updated:

- `docs/PROJECT_STATUS.md` completed items and next actions
- `docs/ROADMAP.md` reporting, calibration, and live-data milestones

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Documentation/Release Step 10 — GitHub-Safe CI Template

Status: implemented.

Added:

- `docs/templates/ci.yml`
- note that it should only be copied into `.github/workflows/` with a token that has `workflow` scope
- release checklist link to the template

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Ten-Step Validation Tooling Expansion

User requested ten iterative items:

1. Push local commits to GitHub.
2. Add `docs/VALIDATION.md`.
3. Add `techno-search validate-all`.
4. Add `techno-search regenerate-examples`.
5. Add deterministic regenerate-example tests.
6. Add docs for example regeneration.
7. Add schema versioning policy.
8. Add explicit `schema_version` fields.
9. Add tests enforcing `schema_version`.
10. Update project status, roadmap, and this file.

Each step should update this file and merge to `main` if needed.

---

## Validation Tooling Step 1 — Push Attempt

Status: blocked by environment policy.

Result:

- Attempted `git push origin main`.
- The environment rejected the push because updating the external GitHub `main` branch is disallowed by tenant policy.
- No workaround was attempted.

Merge status: already on `main`; no merge needed.

---

## Validation Tooling Step 2 — Validation Guide

Status: implemented.

Added:

- `docs/VALIDATION.md`
- local validation gate commands
- candidate/report validation command docs
- schema, score regression, and example regeneration notes

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Validation Tooling Step 3 — Validate-All CLI

Status: implemented.

Added:

- `techno-search validate-all`
- candidate validation summary
- report validation summary
- schema path existence checks
- calibration and score regression summaries
- CLI test coverage

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Validation Tooling Step 4 — Regenerate Examples CLI

Status: implemented.

Added:

- `techno-search regenerate-examples`
- regeneration of `examples/reports`
- regeneration of `examples/batch_reports`
- relative output paths for committed artifacts

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_examples.py
```

Merge status: already on `main`; no merge needed.

---

## Validation Tooling Step 5 — Deterministic Regeneration Tests

Status: implemented.

Added:

- CLI test that regenerates examples in an isolated temporary directory
- existing golden example stable-field test continues to compare regenerated report fields against committed artifacts

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_examples.py
```

Merge status: already on `main`; no merge needed.

---

## Validation Tooling Step 6 — Example Regeneration Docs

Status: implemented.

Updated:

- `docs/CLI_USAGE.md`
- `docs/VALIDATION.md`
- README validation links

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Validation Tooling Step 7 — Schema Versioning Policy

Status: implemented.

Added:

- `docs/SCHEMA_VERSIONING.md`
- schema compatibility policy
- current `techno_search_packet_v1` documentation

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_json_schemas.py
```

Merge status: already on `main`; no merge needed.

---

## Validation Tooling Step 8 — Schema Version Fields

Status: implemented.

Added:

- `schema_version` in candidate packets
- `schema_version` in per-candidate report manifests
- `schema_version` in batch manifests
- regenerated committed example artifacts

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_reporting.py tests/test_examples.py tests/test_json_schemas.py
```

Merge status: already on `main`; no merge needed.

---

## Validation Tooling Step 9 — Schema Version Tests

Status: implemented.

Added:

- example artifact assertions for `schema_version`
- schema required-field assertions for `schema_version`
- reporting assertions for `schema_version`

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_reporting.py tests/test_examples.py tests/test_json_schemas.py
```

Merge status: already on `main`; no merge needed.

---

## Validation Tooling Step 10 — Status And Roadmap Updates

Status: implemented.

Updated:

- `docs/PROJECT_STATUS.md`
- `docs/ROADMAP.md`
- `docs/RELEASE_CHECKLIST.md`
- this file

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Ten-Step Live Provider/Provenance Expansion

User requested ten iterative tasks:

1. Push local commits to GitHub.
2. Add provider-specific live-data adapter interfaces for Gaia, IRSA, VizieR, SIMBAD, and Breakthrough Listen behind the opt-in guard.
3. Add mocked tests proving provider adapters do not perform network access by default.
4. Add `docs/LIVE_PROVIDER_INTERFACES.md`.
5. Add provenance helper module.
6. Wire provenance helper output into report manifests and live-data request scaffolds.
7. Add `techno-search provenance-summary`.
8. Add tests for provenance summary across `examples/reports` and `examples/batch_reports`.
9. Update schemas with provenance summary expectations.
10. Update project status, roadmap, and this file.

Each step should update this file and merge to `main` if needed.

---

## Live Provider/Provenance Step 1 — Push Attempt

Status: blocked by environment policy.

Result:

- Attempted `git push origin main`.
- The environment rejected the push because updating the external GitHub `main` branch is disallowed by tenant policy.
- No workaround was attempted.

Merge status: already on `main`; no merge needed.

---

## Live Provider/Provenance Step 2 — Provider Adapter Interfaces

Status: implemented.

Added:

- `LiveProviderAdapter`
- Gaia adapter scaffold
- IRSA adapter scaffold
- VizieR adapter scaffold
- SIMBAD adapter scaffold
- Breakthrough Listen adapter scaffold
- shared constants module for schema and scoring config versions

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider/Provenance Step 3 — Provider Adapter Default-Off Tests

Status: implemented.

Added:

- provider adapter request-building test
- provider-name coverage for Gaia, IRSA, VizieR, SIMBAD, and Breakthrough Listen
- assertions that adapter fetches raise `LiveDataDisabledError` by default

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider/Provenance Step 4 — Live Provider Interface Docs

Status: implemented.

Added:

- `docs/LIVE_PROVIDER_INTERFACES.md`
- adapter responsibilities
- provenance fields
- cache policy
- conservative scientific guardrails

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider/Provenance Step 5 — Provenance Helper Module

Status: implemented.

Added:

- `src/techno_search/provenance.py`
- `ProvenanceRecord`
- `build_provenance_record(...)`
- `candidate_provenance_record(...)`
- provenance unit tests

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_provenance.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider/Provenance Step 6 — Provenance Wiring

Status: implemented.

Added:

- `provenance_summary` in report manifests
- shared git commit helper usage
- live-data request provenance record generation
- tests for report and live-data provenance summaries

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_reporting.py tests/test_live_data.py tests/test_provenance.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider/Provenance Step 7 — Provenance Summary CLI

Status: implemented.

Added:

- `techno-search provenance-summary`
- manifest counts
- counts by track, schema version, config version, and source dataset
- CLI usage docs

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider/Provenance Step 8 — Provenance Summary Tests

Status: implemented.

Added:

- provenance summary test for `examples/reports`
- provenance summary test for `examples/batch_reports`
- example manifest assertions for `provenance_summary`

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_examples.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider/Provenance Step 9 — Provenance Summary Schema

Status: implemented.

Added:

- required `provenance_summary` in report manifest schema
- validation required-field update
- schema tests for `provenance_summary`
- pipeline spec note for provenance summaries

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_json_schemas.py tests/test_examples.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider/Provenance Step 10 — Status And Roadmap Updates

Status: implemented.

Updated:

- `docs/PROJECT_STATUS.md`
- `docs/ROADMAP.md`
- `docs/RELEASE_CHECKLIST.md`
- this file

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Ten-Step Mock Provider/Cache Expansion

User requested ten iterative tasks:

1. Push local commits to GitHub.
2. Add mocked provider implementations with injected fetch functions.
3. Add tests proving injected fetch functions are only called with live opt-in.
4. Add provider response normalization into provenance-only metadata records.
5. Add `techno-search live-provider-summary`.
6. Add docs for mocked provider implementations and safe test patterns.
7. Add cache-key generation helper.
8. Add deterministic cache-key tests.
9. Update schemas/docs with provider/cache provenance fields.
10. Update project status, roadmap, and this file.

Each step should update this file and merge to `main` if needed.

---

## Mock Provider/Cache Step 1 — Push Attempt

Status: blocked by environment policy.

Result:

- Attempted `git push origin main`.
- The environment rejected the push because updating the external GitHub `main` branch is disallowed by tenant policy.
- No workaround was attempted.

Merge status: already on `main`; no merge needed.

---

## Mock Provider/Cache Step 2 — Injected Provider Fetchers

Status: implemented.

Added:

- optional injected provider fetch functions
- guarded provider fetch execution
- provider-specific constructors that accept injected fetchers

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Mock Provider/Cache Step 3 — Live Opt-In Fetch Tests

Status: implemented.

Added:

- test proving injected fetchers are not called while live data is disabled
- test proving injected fetchers run only after `TECHNO_SEARCH_ENABLE_LIVE_DATA=1`

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Mock Provider/Cache Step 4 — Provenance-Only Response Normalization

Status: implemented.

Added:

- `normalize_provider_response(...)`
- response metadata fields only
- no candidate interpretation in live provider response normalization

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Mock Provider/Cache Step 5 — Live Provider Summary CLI

Status: implemented.

Added:

- `techno-search live-provider-summary`
- provider names
- service URLs
- live-enabled status
- CLI test coverage

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Mock Provider/Cache Step 6 — Mock Provider Docs

Status: implemented.

Updated:

- `docs/LIVE_PROVIDER_INTERFACES.md`
- safe injected-fetch test pattern
- provenance-only response normalization guidance
- CLI usage docs for live provider summary

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Mock Provider/Cache Step 7 — Cache-Key Helper

Status: implemented.

Added:

- deterministic `build_cache_key(...)`
- request-level `cache_key()`
- cache key in live-data request provenance

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_provenance.py tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Mock Provider/Cache Step 8 — Cache-Key Tests

Status: implemented.

Added:

- deterministic cache-key test for sorted query parameters
- cache-key assertion in live provider fetch metadata test

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_provenance.py tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Mock Provider/Cache Step 9 — Provider/Cache Provenance Schema Docs

Status: implemented.

Updated:

- report manifest schema provenance summary fields
- schema tests for service URL and cache key fields
- pipeline spec provenance summary text
- live provider interface docs
- release checklist

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_json_schemas.py tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Mock Provider/Cache Step 10 — Status And Roadmap Updates

Status: implemented.

Updated:

- `docs/PROJECT_STATUS.md` completed and next-action entries
- `docs/ROADMAP.md` reporting and live-data milestone status
- `CLAUDE.md` with final step handoff notes

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py tests/test_provenance.py tests/test_cli.py tests/test_json_schemas.py tests/test_examples.py tests/test_reporting.py
```

Merge status: already on `main`; no merge needed.

---

## Ten-Step Live Cache/Query Shape Expansion

User requested ten iterative steps:

1. Add local cache policy constants and ignored cache directory conventions.
2. Implement a `LiveProviderCache` helper that stores metadata by deterministic cache key.
3. Add tests proving cache writes stay outside committed example/report paths.
4. Wire cache directory config into live-provider request handling.
5. Add `techno-search live-cache-summary`.
6. Add docs for cache location, cleanup, and reproducibility limits.
7. Add Gaia mock query-shape builder with no network access by default.
8. Add IRSA mock query-shape builder with no network access by default.
9. Add VizieR/SIMBAD mock query-shape builders with conservative provenance fields.
10. Update `PROJECT_STATUS`, `ROADMAP`, and `CLAUDE.md`, then commit the batch.

## Live Cache/Query Shape Step 1 — Cache Policy Constants

Status: implemented.

Added:

- `LIVE_CACHE_DIR_ENV_VAR`
- `DEFAULT_LIVE_CACHE_DIR`
- `configured_live_cache_dir(...)`

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Cache/Query Shape Step 2 — Live Provider Cache Helper

Status: implemented.

Added:

- `LiveProviderCache.from_config(...)`
- deterministic metadata paths from request cache keys
- JSON metadata read/write helpers
- cache summary helper that counts metadata files by provider

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Cache/Query Shape Step 3 — Cache Path Tests

Status: implemented.

Added tests for:

- configured cache directory environment override
- default project-local `cache/live_providers` convention
- metadata writes under a cache root
- cache writes staying outside committed example report paths

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Cache/Query Shape Step 4 — Cache-Aware Provider Fetch

Status: implemented.

Added:

- optional `cache=` argument to provider `fetch_metadata(...)`
- cached normalized metadata reuse
- cache write after injected live fetches
- test coverage for one fetch call followed by cached reuse

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Cache/Query Shape Step 5 — Live Cache Summary CLI

Status: implemented.

Added:

- `techno-search live-cache-summary`
- optional `--cache-dir`
- cache existence, metadata count, and provider-count output
- CLI test coverage

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Live Cache/Query Shape Step 6 — Cache Documentation

Status: implemented.

Updated:

- live-provider cache location and environment override docs
- live-cache summary CLI docs
- data policy note that live-provider caches are ignored local artifacts
- cleanup and reproducibility limits

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Live Cache/Query Shape Step 7 — Gaia Query Shape Builder

Status: implemented.

Added:

- Gaia cone-search request builder
- ADQL-like query descriptor with catalog, coordinates, and radius metadata
- test proving request construction does not require live access

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Cache/Query Shape Step 8 — IRSA Query Shape Builder

Status: implemented.

Added:

- IRSA catalog cone-search request builder
- catalog, coordinates, radius, and purpose metadata
- test proving request construction stays non-networked by default

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Cache/Query Shape Step 9 — VizieR And SIMBAD Query Shape Builders

Status: implemented.

Added:

- VizieR catalog cone-search request builder
- SIMBAD object lookup request builder
- provenance-only interpretation markers in request parameters
- tests proving both remain guarded by default

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Cache/Query Shape Step 10 — Status And Roadmap Updates

Status: implemented.

Updated:

- `docs/PROJECT_STATUS.md` completed, in-progress, and next-action entries
- `docs/ROADMAP.md` reporting and live-data milestone status
- `docs/LIVE_PROVIDER_INTERFACES.md` query-shape builder guidance
- `CLAUDE.md` with final step handoff notes

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py tests/test_cli.py tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Ten-Step Live Fixture/Client Skeleton Expansion

User requested ten iterative steps:

1. Add cached live-metadata fixture format under `tests/fixtures/live_metadata/`.
2. Add tests that load cached Gaia metadata fixtures without network access.
3. Add tests that load cached IRSA metadata fixtures without network access.
4. Add tests that load cached VizieR/SIMBAD metadata fixtures without network access.
5. Add `techno-search live-fixture-summary`.
6. Add docs for live metadata fixture rules and non-committed cache boundaries.
7. Add a provider-client protocol/interface so real clients can plug in cleanly later.
8. Add a disabled Gaia real-client skeleton behind `TECHNO_SEARCH_ENABLE_LIVE_DATA=1`.
9. Add a disabled IRSA real-client skeleton behind `TECHNO_SEARCH_ENABLE_LIVE_DATA=1`.
10. Update `PROJECT_STATUS`, `ROADMAP`, and `CLAUDE.md`, then commit the batch.

## Live Fixture/Client Step 1 — Cached Metadata Fixture Format

Status: implemented.

Added:

- `tests/fixtures/live_metadata/gaia_cone_search.metadata.json`
- `tests/fixtures/live_metadata/irsa_catalog_cone.metadata.json`
- `tests/fixtures/live_metadata/vizier_catalog_cone.metadata.json`
- `tests/fixtures/live_metadata/simbad_object_lookup.metadata.json`
- `live_metadata_fixture_v1` fixture schema marker

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Fixture/Client Step 2 — Gaia Fixture Loader Test

Status: implemented.

Added:

- `default_live_metadata_fixture_dir(...)`
- `load_live_metadata_fixture(...)`
- `iter_live_metadata_fixtures(...)`
- fixture shape validation
- Gaia fixture test that runs with live data disabled

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Fixture/Client Step 3 — IRSA Fixture Loader Test

Status: implemented.

Added:

- IRSA cached metadata fixture loader test
- assertions for provider name, catalog provenance, cache key, and response metadata
- live-data-disabled guard coverage

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Fixture/Client Step 4 — VizieR And SIMBAD Fixture Tests

Status: implemented.

Added:

- VizieR cached metadata fixture loader test
- SIMBAD cached metadata fixture loader test
- provenance-only interpretation assertions
- no candidate interpretation assertion for cached provider fixtures

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Fixture/Client Step 5 — Live Fixture Summary CLI

Status: implemented.

Added:

- `live_metadata_fixture_summary(...)`
- `techno-search live-fixture-summary`
- optional `--fixture-dir`
- CLI test for committed fixture coverage counts

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Fixture/Client Step 6 — Fixture Documentation

Status: implemented.

Updated:

- CLI docs for `live-fixture-summary`
- live-data integration fixture policy
- live-provider interface fixture allow/deny lists
- data policy note for tiny live metadata fixtures versus local cache contents

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Live Fixture/Client Step 7 — Provider Client Protocol

Status: implemented.

Added:

- `LiveProviderClient` protocol
- `fetcher_from_client(...)`
- `LiveProviderAdapter.from_client(...)`
- protocol adapter test with injected stub client

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Fixture/Client Step 8 — Disabled Gaia Client Skeleton

Status: implemented.

Added:

- `GaiaLiveClient`
- explicit live opt-in guard
- `NotImplementedError` after opt-in because no real network client exists yet
- tests for disabled and unimplemented Gaia skeleton behavior

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Fixture/Client Step 9 — Disabled IRSA Client Skeleton

Status: implemented.

Added:

- `IrsaLiveClient`
- explicit live opt-in guard
- `NotImplementedError` after opt-in because no real network client exists yet
- tests for disabled and unimplemented IRSA skeleton behavior

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Fixture/Client Step 10 — Status And Roadmap Updates

Status: implemented.

Updated:

- `docs/PROJECT_STATUS.md` completed, in-progress, and next-action entries
- `docs/ROADMAP.md` reporting and live-data milestone status
- `docs/LIVE_PROVIDER_INTERFACES.md` provider-client protocol and skeleton guidance
- `CLAUDE.md` with final step handoff notes

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py tests/test_cli.py tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Ten-Step Live Client Completion Expansion

User requested ten iterative steps:

1. Add cached fixture-driven normalization tests for Gaia and IRSA client skeleton paths.
2. Add cached fixture-driven normalization tests for VizieR and SIMBAD paths.
3. Add `VizierLiveClient` disabled skeleton behind `TECHNO_SEARCH_ENABLE_LIVE_DATA=1`.
4. Add `SimbadLiveClient` disabled skeleton behind `TECHNO_SEARCH_ENABLE_LIVE_DATA=1`.
5. Add `BreakthroughListenLiveClient` disabled skeleton and a tiny metadata fixture.
6. Add Breakthrough Listen request-shape builder for local file metadata, no file ingestion yet.
7. Add `techno-search live-client-summary` for configured skeleton/client status.
8. Add docs for the live-client lifecycle.
9. Update `PROJECT_STATUS`, `ROADMAP`, and `CLAUDE.md`.
10. Run full validation, commit, and report branch state.

## Live Client Completion Step 1 — Gaia/IRSA Fixture Normalization Tests

Status: implemented.

Added:

- fixture-backed client stub for adapter normalization tests
- Gaia fixture-client normalization test
- IRSA fixture-client normalization test
- live opt-in scoped only to the tests

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Client Completion Step 2 — VizieR/SIMBAD Fixture Normalization Tests

Status: implemented.

Added:

- VizieR fixture-client normalization test
- SIMBAD fixture-client normalization test
- provenance-only query parameter assertions on normalized request metadata

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Client Completion Step 3 — Disabled VizieR Client Skeleton

Status: implemented.

Added:

- `VizierLiveClient`
- explicit live opt-in guard
- `NotImplementedError` after opt-in because no real network client exists yet
- tests for disabled and unimplemented VizieR skeleton behavior

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Client Completion Step 4 — Disabled SIMBAD Client Skeleton

Status: implemented.

Added:

- `SimbadLiveClient`
- explicit live opt-in guard
- `NotImplementedError` after opt-in because no real network client exists yet
- tests for disabled and unimplemented SIMBAD skeleton behavior

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Client Completion Step 5 — Breakthrough Listen Fixture And Skeleton

Status: implemented.

Added:

- `tests/fixtures/live_metadata/breakthrough_listen_file_metadata.metadata.json`
- `BreakthroughListenLiveClient`
- fixture loader test for Breakthrough Listen metadata
- tests for disabled and unimplemented Breakthrough Listen skeleton behavior
- updated fixture-summary expected count

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Live Client Completion Step 6 — Breakthrough Listen File Request Shape

Status: implemented.

Added:

- `BreakthroughListenAdapter.build_local_file_metadata_request(...)`
- provenance-only local file metadata descriptor
- test proving request construction does not read or require the file

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Client Completion Step 7 — Live Client Summary CLI

Status: implemented.

Added:

- `live_client_summary(...)`
- `techno-search live-client-summary`
- client status fields for provider, service URL, implementation state, and live opt-in
- CLI test proving all configured clients are disabled skeletons

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Client Completion Step 8 — Live Client Lifecycle Docs

Status: implemented.

Updated:

- CLI docs for `live-client-summary`
- provider interface docs with all disabled skeletons
- live-client lifecycle: query shape, fixture, skeleton, normalization tests, real client
- live-data integration docs for the guarded lifecycle

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Live Client Completion Step 9 — Status And Roadmap Updates

Status: implemented.

Updated:

- `docs/PROJECT_STATUS.md` completed, in-progress, and next-action entries
- `docs/ROADMAP.md` reporting and live-data milestone status
- `CLAUDE.md` with step 9 handoff notes

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py tests/test_cli.py tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Live Client Completion Step 10 — Validation And Commit

Status: implemented.

Validation passed:

- full pytest with coverage
- full Ruff check
- `git diff --check`

Commit planned:

```bash
git commit -m "Add live client skeleton completion"
```

Merge status: already on `main`; no merge needed.
