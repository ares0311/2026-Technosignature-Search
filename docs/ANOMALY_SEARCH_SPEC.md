# ANOMALY SEARCH SPEC

## Purpose

Define the archival and catalog anomaly search track.

This track searches historical and modern datasets for unusual source behavior, including vanishing sources, appearing sources, extreme photometric changes, and cross-survey inconsistencies.

---

## Initial Search Focus

- vanishing source candidates
- appearing source candidates
- unusual photometric changes
- unusual astrometric behavior
- catalog cross-match failures
- artifact and proper-motion rejection

---

## Candidate Features

Archival anomaly candidates should include:

```text
historical_source_id
modern_source_id
ra
dec
historical_epoch
modern_epoch
historical_magnitude
modern_magnitude
crossmatch_distance_arcsec
crossmatch_confidence
proper_motion_explanation_score
survey_depth_explanation_score
artifact_score
moving_object_score
variability_score
catalog_mismatch_score
```

---

## Evidence Supporting Anomaly Interest

- strong historical detection
- strong modern non-detection or major change
- no plausible proper-motion explanation
- no survey-depth explanation
- no obvious image artifact
- no known moving-object explanation
- consistent local source context

---

## Evidence Supporting Artifact

- plate defect
- saturation
- diffraction spike
- cosmic ray
- edge artifact
- poor image quality
- known bad region

---

## Evidence Supporting Proper Motion

- plausible modern counterpart offset
- offset aligns with expected motion vector
- high proper-motion source nearby
- epoch difference explains displacement

---

## Evidence Supporting Survey Depth / Bandpass Effect

- historical and modern surveys have incompatible depths
- source color explains detection difference
- local background difference
- bandpass mismatch

---

## Evidence Supporting Catalog Mismatch

- multiple possible counterparts
- large coordinate uncertainty
- duplicate source association
- crowded field ambiguity

---

## Minimum v0 Workflow

```text
synthetic archival anomaly features
→ artifact checks
→ natural explanation checks
→ score
→ pathway classification
```

No live survey queries are required for v0.

---

## Future Workflow

```text
historical catalog entry
→ modern cross-match
→ artifact/proper-motion/depth checks
→ anomaly score
→ human review packet
```

---

## Scientific Guardrails

- Do not claim a vanished civilization or artificial event.
- Use “archival anomaly candidate.”
- Always list artifact explanations.
- Always list proper-motion explanations.
- Always list survey-depth and bandpass caveats.
