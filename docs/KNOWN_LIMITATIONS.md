# Known Limitations

**Last updated:** 2026-06-13

This document records known limitations of the 2026 Technosignature Search
citizen-science pipeline. It is part of the project's public provenance record.
No result produced by this pipeline constitutes a detection claim or authorizes
external submission.

---

## 1. Training Data — Single Target, 124 Labels

The learned scoring model v1 is trained on **124 labeled examples from a single
stellar target (HIP99427)** observed with the Green Bank Telescope (GBT) L-band
receiver. This is a small dataset from a single telescope/receiver combination.

**Implications:**
- The model's generalization to other targets, telescopes, receivers, or
  frequency bands is unknown and should not be assumed.
- Feature importance and decision boundaries are specific to GBT L-band RFI
  environment.
- 3-fold CV accuracy (99.19%) reflects performance on held-out HIP99427 data
  only — not on independent targets.

**Mitigation path:** Ingest cadence data from additional BL targets
(HIP100670, HIP99560, HIP99759 and others) to expand the training set and
validate cross-target generalization.

---

## 2. Single Telescope and Receiver

All real observation data in this pipeline comes from the **Green Bank Telescope
(GBT), L-band receiver (~1.1–1.9 GHz)**. The pipeline has not been tested on:

- Other GBT receivers (S-band, C-band, X-band)
- Other telescopes (Parkes, MeerKAT, FAST)
- Interferometric data
- Non-Breakthrough Listen datasets

Calibrated SNR thresholds (noise_floor_snr=42.4, follow_up_snr=54.8,
high_interest_snr=118.3) are derived from GBT L-band noise distributions and
**must be recalibrated for any other telescope or receiver** before use.
See `docs/CALIBRATION_TRANSFER_PROTOCOL.md`.

---

## 3. RFI Catalog is Provisional and Not Peer-Reviewed

The GBT RFI catalog (`tests/fixtures/rfi_catalog/`) contains **15 frequency
bands** derived from ITU Radio Regulations, GPS/GNSS allocations, ICAO
aeronautical bands, and FCC Part 25 allocations. It has **not been validated
against actual GBT L-band observations** and has not received external peer
review.

**Implications:**
- RFI flagging based on this catalog may miss actual observatory RFI.
- The catalog does not include transient or time-variable RFI sources.
- Bands marked `status: inactive_pending_review` require operator sign-off
  before admission to production scoring.

---

## 4. No External Expert Review

As of 2026-06-13, **no external SETI researcher, radio astronomer, or
institutional reviewer has independently audited** the pipeline logic, scoring
thresholds, or candidate reports. The independent reproduction noted in
`docs/PRODUCTION_READINESS.md` was performed within the citizen-science project,
not by an independent external team.

This is a Tier 3 gap. Until external review occurs, all pipeline outputs should
be treated as preliminary citizen-science triage results.

---

## 5. Calibrated Thresholds Require Independent-Method Review

The SNR thresholds (noise_floor=42.4, follow_up=54.8, high_interest=118.3)
were derived from the real GBT/HIP99427 noise distribution using the
calibration corpus. They **have not been validated by an independent method**
(e.g., injection-recovery at known SNR levels, comparison with published GBT
sensitivity estimates).

The `calibration_ready: true` gate confirms that the corpus meets coverage
requirements (cadences, targets, epochs, hit count) — it does not certify
that the derived thresholds are scientifically correct.

---

## 6. Multi-Epoch Persistence Score is Heuristic

The `multi_epoch_persistence_score` feature measures how frequently a signal
appears across ABACAD cadence observations. The scoring weight is heuristic
and has not been calibrated against known technosignature injection-recovery
experiments.

---

## 7. Cross-Target RFI Suppression Uses Fixed Frequency Tolerance

The cross-target RFI filter uses a fixed 500 Hz frequency tolerance window.
This value was chosen to match turboSETI frequency resolution at GBT L-band
but has not been validated for other observing configurations. Narrow-band
signals that drift significantly between targets may not be correctly grouped.

---

## 8. Infrared and Anomaly Tracks Are Synthetic Only

The infrared (Gaia+WISE) and archival anomaly scoring tracks have been
implemented and tested against synthetic fixtures only. No real Gaia or WISE
catalog cross-match has been scored through the full pipeline. These tracks
are engineering scaffolds pending real data ingestion.

---

## 9. External Catalog Queries Require Manual Opt-In

Live catalog queries (Gaia TAP, SIMBAD) require `TECHNO_SEARCH_ENABLE_LIVE_DATA=1`
and outbound network access. In the default (offline) mode, cross-match
features are zeroed out, which reduces scoring accuracy for candidates where
known-object rejection would be informative.

---

## 10. No Publication or External Submission Authorization

Nothing in this pipeline's output authorizes publication, journal submission,
press release, or external disclosure. All candidate reports explicitly state
this. The escalation gate (`escalation-gate-check`) requires `operator_cleared`
and `external_review_authorized` to be set to `true` by a human operator —
they are always `false` by default.

---

## Acknowledgement

These limitations are documented as part of the project's commitment to
transparent citizen-science practice. They do not prevent the pipeline from
being useful as a local triage and provenance tool; they bound the claims that
can responsibly be made from its output.
