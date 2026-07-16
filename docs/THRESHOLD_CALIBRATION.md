# Scoring Threshold Calibration Status

## STOP — THIS GUIDE DOES NOT AUTHORIZE NEW LABELING

Only pre-existing, independent, row-level labels with documented provenance
may support threshold selection or scientific evaluation. Never ask the user
or anyone else to review, annotate, classify, or label rows for this purpose.
Never infer labels from filters, cadence outcomes, anomalies, follow-up states,
paper-level conclusions, or synthetic injections. There are no confirmed
positive technosignature labels.

## Current Status

No production scoring threshold is calibrated. The available project evidence
does not support a global anomaly/OOD threshold or an SNR escalation cutoff.
Default candidate scoring therefore uses `configs/scoring_v0.json`, an
explicitly uncalibrated set of conservative local-routing heuristics. The
standalone escalation gate reports that no calibrated SNR gate is available
and fails closed.

The retired calibration workflow must not be reconstructed from historical
commands or decision records. In particular:

- project-generated HIP99427 cadence outcomes are legacy diagnostic evidence,
  not admissible threshold truth;
- unlabeled Breakthrough Listen observations are not negative labels;
- noise percentiles alone do not establish false-discovery behavior or a
  candidate-promotion threshold;
- Voyager and synthetic injections may test recovery behavior but cannot
  supply missing class labels;
- human approval of provenance cannot turn an unlabeled observation into
  calibration ground truth.

## Evidence Required To Reopen The Gate

A future proposal may reopen threshold work only after the repository has all
of the following for the exact claimed scope:

1. adequate pre-existing, independently supplied, row-level labels with
   documented source provenance;
2. explicit separation of training, validation, calibration, frozen-eval,
   live-search, and follow-up data roles;
3. grouped and leakage-safe evaluation by target, cadence, frequency band,
   and telescope/session;
4. calibration and false-discovery evidence on real backgrounds, with
   abstention behavior preserved;
5. injection-recovery evidence used only for recovery characterization, not
   as label or false-discovery evidence;
6. a reviewed decision that defines the threshold's scope and updates the
   fail-closed production gates.

If those conditions are not met, the correct work is deterministic
false-positive rejection, unlabeled ranking/triage, or another named roadmap
gap. No local score or SNR authorizes candidate promotion, expert review,
external validation, or external submission.
