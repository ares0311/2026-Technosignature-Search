# RADIO SEARCH SPEC

## Purpose

Define the radio technosignature search track.

The radio track searches existing radio astronomy datasets for candidate signals while aggressively rejecting radio frequency interference, instrumental artifacts, and low-confidence events.

---

## Initial Search Focus

- narrowband signals
- Doppler-drifting signals
- structured radio hits
- ON/OFF target cadence filtering
- RFI rejection
- waterfall visualization
- synthetic signal injection and recovery

---

## Planned Data Types

- filterbank files
- HDF5 files
- hit tables
- waterfall arrays
- synthetic spectrogram fixtures

---

## Candidate Features

Radio candidates should include:

```text
frequency_hz
drift_rate_hz_per_sec
snr
bandwidth_hz
duration_sec
on_target_presence_score
off_target_presence_score
rfi_band_overlap_score
frequency_persistence_score
nearby_target_recurrence_score
instrumental_artifact_score
injection_recovery_score
```

---

## Evidence Supporting Candidate Interest

- narrowband morphology
- nonzero drift rate
- present in ON scans
- absent in OFF scans
- not persistent across unrelated targets
- not in known RFI bands
- not associated with obvious instrument patterns
- repeat observation possible or available

---

## Evidence Supporting RFI

- appears in OFF scans
- appears across many sky positions
- known RFI frequency band
- zero drift or suspiciously stable drift
- persistent local frequency
- satellite or aircraft band overlap

---

## Evidence Supporting Instrumental Artifact

- band-edge location
- quantization pattern
- gain instability
- broadband impulse
- repeated backend pattern
- corrupted metadata

---

## Minimum v0 Workflow

```text
synthetic radio features
→ radio score
→ false-positive class estimate
→ pathway classification
→ Markdown/JSON report
```

No live radio data is required for v0.

---

## Future Workflow

```text
radio file
→ load waterfall
→ run narrowband/drift search
→ parse hits
→ RFI cluster
→ ON/OFF cadence filter
→ score candidates
→ generate review packet
```

---

## Scientific Guardrails

- Do not claim detection of extraterrestrial intelligence.
- Do not claim confirmed technosignature.
- Always list RFI evidence.
- Always list missing observations.
- Always identify whether OFF scans were available.
- Always preserve observing metadata.
