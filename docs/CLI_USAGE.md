# CLI USAGE

## Purpose

Document the `techno-search` command-line interface for synthetic candidate scoring.

The CLI is for reproducible review-packet generation. It does not claim a confirmed technosignature.

---

## Install

Use the project virtual environment:

```bash
source .venv/bin/activate
pip install -e ".[dev]"
```

After installation, the console script should be available as:

```bash
.venv/bin/techno-search --help
```

---

## Score One Candidate

Print a scored candidate packet to stdout:

```bash
.venv/bin/techno-search score examples/candidates/radio_clean_candidate.json
```

Write Markdown, JSON, and manifest files:

```bash
.venv/bin/techno-search score \
  examples/candidates/radio_clean_candidate.json \
  --output-dir examples/reports \
  --prefix example-radio-clean
```

Outputs:

```text
examples/reports/example-radio-clean.md
examples/reports/example-radio-clean.json
examples/reports/example-radio-clean.manifest.json
```

---

## Score A Directory

Write reports for every `.json` candidate packet in a directory:

```bash
.venv/bin/techno-search score-batch \
  examples/candidates \
  examples/batch_reports \
  --prefix batch-
```

This creates one Markdown packet, one JSON packet, and one manifest per candidate, plus:

```text
examples/batch_reports/batch_manifest.json
```

The aggregate manifest records:

- input directory
- output directory
- candidate count
- each candidate ID
- each track
- each recommended pathway
- each per-candidate report path

---

## Input Candidate JSON Shape

The CLI expects a normalized synthetic candidate packet:

```json
{
  "candidate_id": "example-radio-clean",
  "track": "radio",
  "source_ids": ["example-radio-hit-table"],
  "features": {
    "snr": 38.0,
    "bandwidth_hz": 1.5,
    "drift_rate_hz_per_sec": 2.0,
    "on_target_presence_score": 0.95,
    "off_target_presence_score": 0.05,
    "rfi_band_overlap_score": 0.02
  },
  "provenance": {
    "source_dataset": "synthetic-example",
    "processing_version": "v0",
    "config_version": "scoring_v0"
  }
}
```

Supported tracks:

- `radio`
- `infrared`
- `anomaly`

Feature values must be JSON scalar values: string, number, boolean, or null.

---

## Output Expectations

Every packet includes:

- candidate ID
- track
- source IDs
- original feature values
- posterior-style probabilities
- false-positive probability
- recommended pathway
- positive evidence
- negative evidence
- blocking issues
- provenance
- required conservative disclaimer
- false-positive discussion

Persisted reports also include a manifest with:

- candidate ID
- track
- recommended pathway
- Markdown path
- JSON path
- config version
- git commit when available
- UTC generation timestamp

---

## Scientific Guardrails

CLI output is a review artifact, not a discovery claim.

- Treat false positives as the default hypothesis.
- Preserve negative evidence and blocking issues.
- Do not remove the required disclaimer.
- Do not use CLI scores as calibrated probabilities until calibration work is complete.
- Do not submit candidates externally without human review and independent validation.
