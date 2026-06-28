# CALIBRATION FIXTURES

## Phase 0 Status

The synthetic false-positive fixture set was deleted in Phase 0. It must not be
used for production model training, calibration claims, or validation evidence.

Future calibration work must use real labeled corpora, real turboSETI output, or
realistic non-training fixtures with explicit provenance and limitations.

---

## Fixture File

Removed fixture set:

```text
tests/fixtures/calibration_false_positives.json
```

Removed validation test:

```bash
.venv/bin/python -m pytest tests/test_calibration_fixtures.py
```

---

## Historical Covered False-Positive Classes

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

## Future Real-Data Requirements

Each fixture should include:

- stable fixture name
- expected pathway
- normalized candidate JSON packet
- real-data provenance
- explicit false-positive class
- enough feature evidence to make the rejection scientifically understandable

Every fixture should preserve negative evidence. Do not use a fixture that only manipulates final scores without corresponding explanatory features.

---

## Adding New Real-Data Fixtures

1. Do not restore `tests/fixtures/calibration_false_positives.json`.
2. Add new real-data fixture sources only after documenting provenance,
   admission criteria, and whether they are training or held-out validation data.
3. Include `provenance.false_positive_class` when applicable.
4. Make the expected pathway explicit.
5. Add or update a real-data test that names the source dataset and verifies
   conservative routing without using synthetic training data.

If a fixture fails, first inspect whether the feature packet contains enough
false-positive evidence. Only adjust model weights when multiple real-data
fixtures reveal a systematic scoring weakness.

---

## Future Calibration Expansion

Near-term real-data fixture classes to add:

- infrared saturation or duplicate source association
- archival crowded-field catalog mismatches with multiple plausible counterparts
- weak low-SNR radio noise cases
- radio gain-instability or backend-pattern artifact variants
- moving-object fixtures tied to future ephemeris metadata

Longer-term calibration should use:

- known RFI examples
- known catalog artifacts
- known infrared contaminants
- known archival false positives
- human-reviewed labels

Score calibration should eventually report reliability curves, precision-recall, false-positive class confusion, and track-specific score stability.
