# VALIDATION

## Purpose

Central guide for local validation, schema checks, score regression snapshots, and example regeneration.

Validation is a scientific guardrail. It helps keep outputs reproducible, conservative, and explicit about false positives.

---

## Local Validation Gate

Run:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src
git diff --check
```

---

## CLI Validators

Validate one candidate:

```bash
.venv/bin/techno-search validate-candidate examples/candidates/radio_clean_candidate.json
```

Validate generated reports:

```bash
.venv/bin/techno-search validate-reports examples/reports
```

Run local validation summaries:

```bash
.venv/bin/techno-search validate-all
```

Print a compact local health dashboard:

```bash
.venv/bin/techno-search validation-summary
```

Validate catalog cache commit paths:

```bash
.venv/bin/techno-search catalog-cache-validate docs/CATALOG_CACHE_POLICY.md
```

`validate-all` includes a `catalog_cache_validation` block for Git-tracked paths.
Use `catalog-cache-validate` directly for pre-commit checks on a proposed path list.

---

## Schemas

Schema artifact paths:

```bash
.venv/bin/techno-search schema-paths
```

Committed schemas:

- `schemas/candidate_packet.schema.json`
- `schemas/report_manifest.schema.json`
- `schemas/batch_manifest.schema.json`
- `schemas/review_queue.schema.json`
- `schemas/consensus_labels.schema.json`
- `schemas/consensus_export.schema.json`
- `schemas/validation_dataset_manifest.schema.json`
- `schemas/benchmark_metadata.schema.json`
- `schemas/benchmark_run_results.schema.json`
- `schemas/background_targets.schema.json`
- `schemas/background_search_ledger.schema.json`

---

## Score Regression Snapshots

Review snapshot coverage:

```bash
.venv/bin/techno-search score-regression-summary
```

Review synthetic false-positive class coverage:

```bash
.venv/bin/techno-search false-positive-summary
```

Review synthetic calibration fixture coverage by track:

```bash
.venv/bin/techno-search calibration-track-summary
```

Review synthetic injection-recovery fixture coverage:

```bash
.venv/bin/techno-search injection-recovery-summary
```

Review synthetic reliability-curve fixture coverage:

```bash
.venv/bin/techno-search reliability-summary
```

Review synthetic precision-recall fixture coverage:

```bash
.venv/bin/techno-search precision-recall-summary
```

Review synthetic human-review queue fixture coverage:

```bash
.venv/bin/techno-search review-queue-summary
```

Review synthetic human-review consensus label coverage:

```bash
.venv/bin/techno-search consensus-summary
```

Review synthetic human-review consensus export coverage:

```bash
.venv/bin/techno-search consensus-export-summary
```

Review validation dataset manifest coverage:

```bash
.venv/bin/techno-search validation-dataset-summary
```

Review local synthetic benchmark metadata:

```bash
.venv/bin/techno-search benchmark-metadata-summary
```

Review local synthetic benchmark run-result metadata:

```bash
.venv/bin/techno-search benchmark-run-summary
```

Append one local synthetic benchmark run-result entry to an ignored output path:

```bash
.venv/bin/techno-search benchmark-run-append \
  --results-path artifacts/benchmark_run_results.json \
  --run-id pytest-coverage-local-001 \
  --command-name "pytest coverage gate" \
  --command-kind test \
  --status passed \
  --worker-count 1 \
  --input-case-count 194 \
  --duration-seconds 1.58 \
  --git-commit "$(git rev-parse --short HEAD)" \
  --config-version scoring_v0
```

Compare repeated local benchmark entries:

```bash
.venv/bin/techno-search benchmark-run-compare \
  --results-path artifacts/benchmark_run_results.json
```

Review fixture-backed background target prioritization:

```bash
.venv/bin/techno-search target-priority-summary
```

Run one explicit local-only background ledger append in an ignored output path:

```bash
.venv/bin/techno-search background-run-once \
  --ledger-path artifacts/background_search_ledger.json \
  --acknowledge-local-run
```

Review passive/background search ledger coverage:

```bash
.venv/bin/techno-search background-ledger-summary
```

`validate-all` and `validation-summary` include calibration-by-track, false-positive class, validation dataset, benchmark metadata, benchmark run-result metadata, background target-priority, background search ledger, injection-recovery, reliability, precision-recall, human-review queue, consensus-label, and consensus-export coverage. Benchmark append and compare commands are local workflow helpers for ignored output paths. The reported calibration-by-track coverage, false-positive class coverage, validation dataset coverage, benchmark metadata, benchmark run-result metadata, benchmark deltas, target-priority ranking, background ledger counts, recovery rate, false-alarm fraction, reliability errors, precision, recall, F1 score, review queue counts, consensus counts, and consensus export counts are synthetic development diagnostics only; they are not calibrated survey contamination, sensitivity, reliability, per-track survey performance, classification performance estimates, discovery claims, external validation, detections, or scientific performance claims.

Snapshot fixture:

```text
tests/fixtures/score_regressions.json
```

Injection-recovery fixture:

```text
tests/fixtures/injection_recovery_summary.json
```

Reliability fixture:

```text
tests/fixtures/reliability_curves.json
```

Precision-recall fixture:

```text
tests/fixtures/precision_recall_summary.json
```

False-positive class diagnostics currently reuse:

```text
tests/fixtures/calibration_false_positives.json
```

Human-review queue fixture:

```text
tests/fixtures/review_queue.json
```

Human-review consensus fixture:

```text
tests/fixtures/consensus_labels.json
```

Human-review consensus export fixture:

```text
tests/fixtures/consensus_exports.json
```

Validation dataset manifest fixture:

```text
tests/fixtures/validation_dataset_manifest.json
```

Benchmark metadata fixture:

```text
tests/fixtures/benchmark_metadata.json
```

Benchmark run-result fixture:

```text
tests/fixtures/benchmark_run_results.json
```

Background target-priority fixture:

```text
tests/fixtures/background_targets.json
```

Background search ledger fixture:

```text
tests/fixtures/background_search_ledger.json
```

Background priority config:

```text
configs/background_priority_v0.json
```

When scores change, review whether the scoring model, thresholds, or example inputs changed intentionally.

---

## Example Regeneration

Regenerate committed example artifacts:

```bash
.venv/bin/techno-search regenerate-examples
```

Regenerated examples should keep stable fields identical unless there is an intentional scoring, schema, or reporting change.

Report plot artifacts are optional review context. Current generated examples include dependency-free synthetic SVG diagnostics for radio, infrared, and anomaly tracks, but validators should continue to accept manifests where `plot_artifacts` is absent or empty.

Examples should be regenerated when:

- `schema_version` changes
- `config_version` changes
- report packet fields change
- manifest fields change
- plot artifact manifest fields change
- example candidate inputs change

Stable score, evidence, and pathway changes should be reviewed against `tests/fixtures/score_regressions.json`.
