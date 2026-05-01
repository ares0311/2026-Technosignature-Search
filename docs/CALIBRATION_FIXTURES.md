# CALIBRATION FIXTURES

## Purpose

Document the synthetic false-positive fixture set used by v0 calibration sanity tests.

These fixtures are not empirical calibration data. They are conservative regression examples that ensure obvious false-positive classes do not route as strong candidates.

---

## Fixture File

Current fixture set:

```text
tests/fixtures/calibration_false_positives.json
```

Validation test:

```bash
.venv/bin/python -m pytest tests/test_calibration_fixtures.py
```

---

## Covered False-Positive Classes

| Fixture | Track | Expected pathway |
|---|---|---|
| `radio_rfi_off_target` | radio | `do_not_submit_false_positive` |
| `infrared_agn_blend` | infrared | `do_not_submit_false_positive` |
| `infrared_dust_contaminant` | infrared | `do_not_submit_false_positive` |
| `anomaly_image_artifact` | anomaly | `do_not_submit_false_positive` |
| `anomaly_proper_motion` | anomaly | `do_not_submit_false_positive` |
| `anomaly_survey_depth` | anomaly | `do_not_submit_false_positive` |
| `radio_band_edge_artifact` | radio | `do_not_submit_false_positive` |
| `radio_instrumental_artifact` | radio | `do_not_submit_false_positive` |
| `infrared_agb_like_colors` | infrared | `do_not_submit_false_positive` |
| `infrared_bad_photometry` | infrared | `do_not_submit_false_positive` |
| `anomaly_moving_object` | anomaly | `do_not_submit_false_positive` |
| `anomaly_catalog_mismatch` | anomaly | `do_not_submit_false_positive` |

---

## Fixture Requirements

Each fixture should include:

- stable fixture name
- expected pathway
- normalized candidate JSON packet
- synthetic provenance
- explicit false-positive class
- enough feature evidence to make the rejection scientifically understandable

Every fixture should preserve negative evidence. Do not use a fixture that only manipulates final scores without corresponding explanatory features.

---

## Adding New Fixtures

1. Add a new entry to `tests/fixtures/calibration_false_positives.json`.
2. Include `provenance.false_positive_class`.
3. Make the expected pathway explicit.
4. Run:

   ```bash
   .venv/bin/python -m pytest tests/test_calibration_fixtures.py
   ```

5. If a fixture fails, first inspect whether the feature packet contains enough false-positive evidence. Only adjust model weights when multiple fixtures reveal a systematic scoring weakness.

---

## Future Calibration Expansion

Near-term fixture classes to add:

- infrared saturation or duplicate source association
- archival crowded-field catalog mismatches with multiple plausible counterparts
- weak low-SNR radio noise cases
- radio gain-instability or backend-pattern artifact variants
- moving-object fixtures tied to future ephemeris metadata

Longer-term calibration should use:

- synthetic injection and recovery
- known RFI examples
- known catalog artifacts
- known infrared contaminants
- known archival false positives
- human-reviewed labels

Score calibration should eventually report reliability curves, precision-recall, false-positive class confusion, and track-specific score stability.
