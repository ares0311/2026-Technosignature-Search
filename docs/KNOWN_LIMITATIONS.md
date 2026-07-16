# Known Limitations

**Last updated:** 2026-07-16

This project has real, tested baseline implementations across radio,
photometry, infrared, and spectroscopy, but those baselines do not establish a
technosignature detection capability with calibrated scientific performance.
No result authorizes external submission or public disclosure of a candidate.

## 1. No Confirmed Positive Labels

There are no confirmed positive technosignature labels. The frozen HIP99427
artifact contains project-generated cadence outcomes and is legacy diagnostic
evidence only. It cannot support training, calibration, threshold selection, or
scientific evaluation.

The available pre-existing row-level labels are not adequate for a global
anomaly/OOD calibration. Learned and semi-supervised outputs therefore remain
fail-closed ranking diagnostics. The project must not ask anyone to create the
missing labels.

## 2. No Calibrated Scoring Or Escalation Threshold

`configs/scoring_v0.json` contains conservative heuristic routing values, not
calibrated probabilities or survey sensitivity. The legacy GBT SNR values were
retired because they were tuned against inadmissible project-generated outcomes
and their claimed corpus coverage conflicted with the current preflight record.
The standalone escalation gate reports no calibrated SNR gate and fails closed.

## 3. Track A Coverage Is Incomplete

The HTRU2 pulsar baseline is a valid known-explanation component with
pre-existing labels, not a comprehensive Track A classifier. Catalog and
deterministic checks cover additional known sources, RFI, cadence behavior,
drift, satellites/transmitters, and artifacts, but their combined coverage does
not prove that every mundane explanation has been modeled.

`low_confidence` and abstention remain required when no known class is reliable.

## 4. Radio Evidence Is Instrument And Coverage Limited

The strongest real-observation evidence is concentrated in Breakthrough Listen
GBT products plus a local MeerKAT BLUSE false-positive corpus used for
semisupervised ranking. Results do not automatically transfer across telescope,
receiver, frequency band, backend, cadence, or integration time. Random-only
splits and synthetic-only benchmarks are not promotion evidence.

## 5. RFI Knowledge Is Provisional

The committed GBT RFI catalog is derived from public regulatory allocations and
is useful for local rejection checks, but it is not a complete observatory
monitoring record and has not received external validation. It may miss
transient, site-specific, time-variable, or unregistered interference.
Cross-target frequency matching and drift tolerances are useful heuristics, not
proof of origin.

## 6. Multi-Modal Baselines Have Uneven Real-Data Depth

Photometry, infrared, and spectroscopy have real-data search paths and tested
deterministic methods, but available observations, band coverage, target
coverage, contaminant knowledge, and sensitivity differ by modality. A
cross-modal coincidence is a prioritization signal only; it does not establish
a common cause or an artificial origin.

## 7. Live Providers Are Explicit And Drift-Prone

Gaia, SIMBAD, IRSA, MAST, JWST, satellite, and other live-provider queries
require explicit opt-in and outbound access. Offline runs may lack current
catalog rejection evidence. Provider schemas, product availability, and rate
limits can change, so live results require current primary-source verification
and preserved provenance.

## 8. No Candidate Has Cleared The Review Chain

There are zero independently escalation-ready candidates. No candidate-specific
adversarial review has been required or completed, and no credentialed
third-party expert has confirmed a candidate. Local operator triage is not
expert review, peer review, external validation, or permission to submit.

## 9. Storage Constrains Search Scale

Project-managed local data must remain below 100 GB until an approved external
drive is connected. Metadata-first inventories, bounded manifests, size
preflights, small samples, and streaming/eviction are therefore preferred over
broad archive mirrors or speculative raw downloads.

These limitations bound every score, ranking, candidate packet, and negative
result. They should be preserved in any scientific interpretation.
