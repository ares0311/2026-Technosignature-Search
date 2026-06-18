# HIP39826 DECISION-134 Held-Out Evidence Note

**Status:** Review-safe negative evidence, not production closure.

This note records the second bounded DECISION-134 held-out evidence acquisition
from the current Breakthrough Listen Open Data HDF5 archive. It was run only
after explicit operator approval for a second bounded attempt.

## Evidence Summary

| Field | Value |
|---|---|
| Evidence ID | `decision134-hip39826-zero-hit-heldout-v1` |
| Target | `HIP39826` |
| Evidence stream | `data/extended_corpus` |
| Source URL | `https://bldata.berkeley.edu/pipeline/AGBT17A_999_26/holding/spliced_blc0001020304050607_guppi_57829_11159_HIP39826_0032.gpuspec.0002.h5` |
| HDF5 SHA-256 | `573ef260d2a6d620dbfd7a80958a65edc5d8f8fb1d95b70868612b9b1f41b47c` |
| HDF5 size | 269075535 bytes |
| turboSETI output | Zero valid hits at SNR >= 10 |
| Raw payload committed | No |

The raw HDF5, turboSETI `.dat`, and turboSETI log remain ignored local
payloads. The committed evidence fixture is:

`tests/fixtures/ai_hardening_hip39826_zero_hit_evidence.json`

## Method Review Outcome

The run produced a valid held-out evidence file but no candidate rows. The
candidate-level methods therefore abstained:

| Method | Outcome | Reason |
|---|---|---|
| Rule-based scoring | Abstained | No valid hit rows for candidate feature extraction |
| Learned logistic regression | Abstained | No candidate feature vector can be produced |
| Cross-target RFI suppression | Abstained | Two populated targets exist, but neither has valid hit frequencies |
| GLOBULAR dense-cluster filter | Abstained | No morphology rows for clustering |
| Semi-supervised anomaly scorer | Abstained | No hit feature rows; scorer not fitted on a populated local corpus |

## Production Impact

This second bounded run strengthens the negative evidence for DECISION-134, but
it does not close DECISION-134. The specific remaining blocker is unchanged:
the project still needs valid held-out hit rows or an injection-recovery stream
in real noise so at least two independent methods can compare outputs on the
same evidence while preserving disagreements, abstentions, and negative
evidence.

No detection, discovery, expert review, peer review, external validation,
external submission authorization, or production promotion is claimed.
