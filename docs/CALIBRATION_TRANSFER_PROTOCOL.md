# Calibration Transfer Status

## Fail-Closed Boundary

There is no validated scoring calibration to transfer to another telescope,
frequency band, backend, or integration time. The legacy GBT values `42.4`,
`54.8`, `118.3`, and `5.21` were tied to a retired project-generated-label
workflow and must not be used as production thresholds or transfer baselines.

Instrument transfer cannot be performed by rescaling SNR cutoffs or collecting
new project-owned labels. Unlabeled observations remain unlabeled, and no
operator review may create calibration or evaluation truth.

## Requirements For Any Future Instrument-Specific Calibration

Any future proposal must begin with independently supplied, pre-existing,
row-level labels that are adequate for the exact instrument and frequency-band
scope. It must then satisfy the learned-model and data-role policies in
`AGENTS.md`, `docs/astrometrics_coding_agents_master_guide.md`, and
`docs/astrometrics_data_selection_policy.md`, including:

- explicit dataset manifests and provenance;
- strict separation of calibration, frozen-eval, and live-search data;
- grouped holdouts by target, cadence, band, and telescope/session;
- real-background calibration and false-discovery evidence;
- abstention or `low_confidence` when no known class is reliable;
- injection recovery reported separately from label-based performance;
- a new reviewed decision defining the permitted scope.

Until that evidence exists, all learned/anomaly outputs and heuristic scores
remain local triage diagnostics. They are not calibrated probabilities,
detection thresholds, expert review, external validation, or authorization for
external submission.
