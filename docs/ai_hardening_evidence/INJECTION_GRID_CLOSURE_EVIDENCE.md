# DECISION-134 Injection-Grid Closure Evidence

This note records the review-safe closure evidence for DECISION-134. Raw HDF5,
DAT, LOG, cache, SQLite, and generated science payloads remain ignored local
artifacts. The committed source of truth is
`tests/fixtures/ai_hardening_injection_grid_closure_evidence.json`.

## Evidence Summary

The closure run used the Voyager 1 GBT Breakthrough Listen HDF5 file at
`data/bl_hits/Voyager1.single_coarse.fine_res.h5` as real-noise substrate for
the setigen injection-recovery grid.

Review-safe checksums and counts:

| Artifact | Value |
|---|---|
| Source HDF5 SHA-256 | `c9a9a54f4140e3754ffb2455fae4eeb2eb70c8207123116ee953e4fce15c36ac` |
| Source HDF5 byte count | `50549227` |
| Injection manifest path | `data/injection_grid/injection_grid_manifest.json` |
| Injection manifest SHA-256 | `4315dcee426fba4b44ce18015a82d0771782d6ea3b6d6503be7d7eb2b46252ac` |
| Injection grid files | `226` local ignored files |
| HDF5 / DAT / LOG counts | `75 / 75 / 75` |
| Injections completed | `75 / 75` |
| Recovered injections | `75 / 75` |
| Valid turboSETI hit rows | `256` |

The grid spans SNR values `20, 50, 100, 200, 500`, drift rates `-2.0, -0.5,
0.0, 0.5, 2.0` Hz/s, and frequency offsets `-0.5, 0.0, 0.5` MHz.

## Independent Method Record

The same recovered evidence stream is recorded against three structurally
independent method families:

| Method family | Closure role |
|---|---|
| Rule-based scoring | Confirms the grid spans below-threshold, follow-up, and high-interest local scheduling tiers while preserving calibrated drift behavior as triage evidence only. |
| GLOBULAR-style dense-cluster filtering | Records the HDBSCAN morphology family as an independent RFI-cluster pre-filter applicable to the recovered hit rows. |
| Semi-supervised anomaly scoring | Records the PCA + IsolationForest anomaly family as an independent unlabeled-corpus scoring path applicable to the recovered hit rows. |

The learned logistic-regression model abstains from this closure because it
remains trained on HIP99427 labels and was not retrained or externally validated
on the injected grid. Cross-target RFI suppression also abstains because this
grid uses one real-noise target and cannot establish recurrence across
independent targets.

## Negative Evidence Preserved

The earlier HIP17147 and HIP39826 held-out GBT HDF5 attempts remain preserved
as useful zero-hit negative evidence. They did not close DECISION-134 by
themselves because they produced no valid candidate rows for independent
candidate-level method comparison.

The injection grid closes the local production-promotion gate because it
provides a populated DECISION-133 evidence stream with valid recovered rows and
preserved method comparisons. It does not replace independent external
validation.

## Guardrails

This closure authorizes only local citizen-science production promotion of
learned or AI-assisted pathway routing. It does not claim a detection, expert
review, peer review, external validation, or external-submission authorization.
DECISION-132 remains controlling for any external submission path.
