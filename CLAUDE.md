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
