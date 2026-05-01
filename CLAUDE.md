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
