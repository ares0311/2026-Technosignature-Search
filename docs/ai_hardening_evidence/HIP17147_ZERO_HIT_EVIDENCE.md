# HIP17147 DECISION-134 Held-Out Evidence Note

**Status:** Review-safe negative evidence, not production closure.

This note records the first bounded DECISION-134 held-out evidence acquisition
after the extended-corpus downloader was hardened to discover current
Breakthrough Listen Open Data HDF5 URLs.

## Evidence Summary

| Field | Value |
|---|---|
| Evidence ID | `decision134-hip17147-zero-hit-heldout-v1` |
| Target | `HIP17147` |
| Evidence stream | `data/extended_corpus` |
| Source URL | `https://bldata.berkeley.edu/pipeline/AGBT16B_999_39/holding/spliced_blc0001020304050607_guppi_57668_28900_HIP17147_0009.gpuspec.0002.h5` |
| HDF5 SHA-256 | `43470e490ebc15be4865757e19ee441f8c36a7392c5bc1f4694128df751b47b6` |
| HDF5 size | 264087094 bytes |
| turboSETI output | Zero valid hits at SNR >= 10 |
| Raw payload committed | No |

The raw HDF5, turboSETI `.dat`, and turboSETI log remain ignored local
payloads. The committed evidence fixture is:

`tests/fixtures/ai_hardening_hip17147_zero_hit_evidence.json`

## Method Review Outcome

The run produced a valid held-out evidence file but no candidate rows. The
candidate-level methods therefore abstained rather than manufacturing a
comparison:

| Method | Outcome | Reason |
|---|---|---|
| Rule-based scoring | Abstained | No valid hit rows for candidate feature extraction |
| Learned logistic regression | Abstained | No candidate feature vector can be produced |
| Cross-target RFI suppression | Abstained | One populated target and no hit frequencies |
| GLOBULAR dense-cluster filter | Abstained | No morphology rows for clustering |
| Semi-supervised anomaly scorer | Abstained | No hit feature rows; scorer not fitted on a populated local corpus |

## Production Impact

This run partially unblocks DECISION-134 by proving that `data/extended_corpus`
can be populated from current Breakthrough Listen Open Data URLs and by
preserving a real zero-hit negative result. It does not close DECISION-134.

The remaining blocker is specific: DECISION-134 still needs a held-out
DECISION-133 evidence stream with valid hit rows, or an injection-recovery
stream in real noise, so at least two independent methods can compare outputs
on the same evidence while preserving disagreements, abstentions, and negative
evidence.

No detection, discovery, expert review, peer review, external validation,
external submission authorization, or production promotion is claimed.
