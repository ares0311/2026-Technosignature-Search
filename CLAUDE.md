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
