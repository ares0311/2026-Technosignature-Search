# RFI Operator Review Protocol — GBT Provisional Catalog (v1)

**Status:** Required before any provisional catalog entry can be moved to `active: true`  
**Catalog:** `tests/fixtures/rfi_catalog/gbt_rfi_provisional_v1.json`  
**Admission record:** `rfi-admit-gbt-provisional-v1` in `tests/fixtures/rfi_database_admission.json`  
**Current blockers:** 2 (site monitoring context review + operator sign-off)

---

## Purpose

The GBT provisional RFI catalog was built from public regulatory documents
(ITU Radio Regulations, IS-GPS-200L, GLONASS ICD, ICAO Annex 10, FCC CFR 47).
Every entry carries `active: false` and `review_status: "provisional"`.

Before any entry can move to `active: true`, a human operator with access to
GBT site-monitoring data must verify each band against actual GBT observations.
This document is the checklist for that review.

---

## Reviewer Prerequisites

1. Access to GBT site-monitoring data (operator spectrum logs, interference logs,
   or turboSETI hit tables from real GBT L-band observations).
2. Ability to run `techno-search rfi-database-summary` and
   `techno-search rfi-database-admission-summary` after edits.
3. Familiarity with turboSETI hit table format (frequency, drift rate, SNR columns).

---

## Review Checklist — Per Entry

For each of the 15 entries in `gbt_rfi_provisional_v1.json`:

### Step 1 — Confirm frequency range in regulatory source

- [ ] Open the cited regulatory document (listed in `provenance.citation_url`).
- [ ] Confirm the frequency range in `frequency_low_hz` / `frequency_high_hz`
      matches the regulatory allocation (±1 MHz tolerance acceptable for ITU footnotes).
- [ ] Note any discrepancies in the entry's `notes` field.

### Step 2 — Check against GBT turboSETI hit distributions

- [ ] Query your GBT L-band hit tables for hits in the frequency range.
  Example (if you have a `.dat` file):
  ```bash
  awk -F',' '$3 >= <freq_low_MHz> && $3 <= <freq_high_MHz>' hits.dat | wc -l
  ```
  Or in Python:
  ```python
  hits = [r for r in rows if freq_low <= float(r['freq_start_mhz']) * 1e6 <= freq_high]
  print(len(hits), 'hits in band')
  ```
- [ ] Confirm hits are present and dense (RFI-like: broadband, zero drift, repeated
      across cadences). If the band appears clean at GBT, note this.

### Step 3 — Check source_class assignment

Verify the `source_class` is appropriate:

| Class | Meaning |
|---|---|
| `gps` | GPS/GNSS satellite signal (L1/L2/L5) |
| `aircraft` | Aircraft navigation/communication (DME, ADS-B, SSR) |
| `satellite` | Non-GPS satellite (Iridium, GLONASS, MSS) |
| `observatory_local` | WiFi/ISM from GBT site equipment |
| `unknown` | Cannot be confirmed from public docs alone |

- [ ] If `source_class` needs correction, update it in the catalog entry.

### Step 4 — Confirm confidence value

| Confidence | Meaning |
|---|---|
| 0.95 | Regulatory allocation confirmed; highly likely to appear at GBT |
| 0.80 | Probable presence; not yet confirmed from GBT data |
| 0.60 | Plausible allocation; sporadic or conditional use |

- [ ] After checking GBT hit data, adjust confidence if your observation data
      supports a higher or lower value. Record the rationale in `notes`.

### Step 5 — Site-monitoring context review (REQUIRED for blocker clearance)

This is the critical step that clears the first blocker:

- [ ] Confirm the signal source is consistent with the GBT site environment
      (e.g., GPS L1 is received at GBT; Iridium satellites pass overhead; the
      2.4 GHz ISM interference is from site WiFi infrastructure).
- [ ] Record confirmation evidence in the entry's `notes` field:
  ```
  "GBT site confirmation: confirmed in [source] on [date]. Hits at [freq_MHz] MHz
   observed in [N] cadences. Operator: [initials]."
  ```

### Step 6 — Sign off on the entry

When all 5 steps pass:

- [ ] Set `review_status: "reviewed"` (not yet `active: true`).
- [ ] Update `confidence` if it changed.
- [ ] Update `notes` with confirmation evidence and reviewer initials.

---

## Completing the Review — Admission Gate Steps

After all 15 entries have been reviewed per the per-entry checklist:

### Gate Step A — Update the catalog file

In `tests/fixtures/rfi_catalog/gbt_rfi_provisional_v1.json`:

- For each confirmed entry, update `review_status` from `"provisional"` to `"reviewed"`.
- Do NOT yet set `active: true` — that requires the second blocker to clear.

### Gate Step B — Run the admission test suite

```bash
.venv/bin/python -m pytest tests/test_gbt_rfi_provisional_catalog.py -q
```

All 38 tests must pass after edits.

### Gate Step C — Update the admission record

In `tests/fixtures/rfi_database_admission.json`, find `rfi-admit-gbt-provisional-v1`:

1. Set `monitoring_context_reviewed: true` (clears blocker 1).
2. Reduce `blocker_count` from `2` to `1`.
3. Update `notes` to reflect blocker 1 cleared.

### Gate Step D — Operator sign-off (clears blocker 2)

After the admission record reflects blocker 1 cleared, a second operator review
is required for sign-off:

1. Set `external_review_completed: true` if an external reviewer confirmed the
   catalog (optional but recommended for Tier 1 gap closure).
2. When ready for active use: set `admission_status: "ready_for_local_fixture"`.
3. Set `blocker_count: 0`.
4. Run `validate-all` to confirm gate passes.

### Gate Step E — Activate entries for scoring

Only after `admission_status: "ready_for_local_fixture"` and `blocker_count: 0`:

- Set `active: true` on confirmed entries in the catalog.
- Entries with `active: true` will be used by the pipeline RFI rejection guard.
- Re-run the full test suite:

```bash
caffeinate -i .venv/bin/python -m pytest --tb=short -q
.venv/bin/techno-search validate-all
```

---

## Quick Reference — All 15 Entries

| # | Entry ID | Band | Freq (MHz) | Source Class | Confidence | Status |
|---|---|---|---|---|---|---|
| 1 | gbt-rfi-gps-l1-v1 | GPS L1 / Galileo E1 | 1575.42 | gps | 0.95 | provisional |
| 2 | gbt-rfi-gps-l2-v1 | GPS L2 | 1227.60 | gps | 0.95 | provisional |
| 3 | gbt-rfi-gps-l5-v1 | GPS L5 | 1176.45 | gps | 0.80 | provisional |
| 4 | gbt-rfi-glonass-l1-v1 | GLONASS L1 | 1598–1606 | satellite | 0.90 | provisional |
| 5 | gbt-rfi-glonass-l2-v1 | GLONASS L2 | 1243–1249 | satellite | 0.85 | provisional |
| 6 | gbt-rfi-adsb-v1 | ADS-B 1090 | 1090 | aircraft | 0.95 | provisional |
| 7 | gbt-rfi-iridium-v1 | Iridium | 1616–1626.5 | satellite | 0.90 | provisional |
| 8 | gbt-rfi-lband-mss-downlink-v1 | L-band MSS downlink | 1525–1559 | satellite | 0.85 | provisional |
| 9 | gbt-rfi-dme-v1 | DME aircraft nav | 960–1215 | aircraft | 0.80 | provisional |
| 10 | gbt-rfi-ssr-v1 | SSR Mode S | 1030 | aircraft | 0.90 | provisional |
| 11 | gbt-rfi-lband-radar-eess-v1 | L-band radar/EESS | 1215–1300 | satellite | 0.75 | provisional |
| 12 | gbt-rfi-lband-mss-uplink-v1 | L-band MSS uplink | 1626.5–1660.5 | satellite | 0.80 | provisional |
| 13 | gbt-rfi-rnss-v1 | RNSS | 1559–1610 | gps | 0.85 | provisional |
| 14 | gbt-rfi-cellular-700mhz-v1 | Cellular 700 MHz | 700–800 | observatory_local | 0.70 | provisional |
| 15 | gbt-rfi-24ghz-ism-v1 | 2.4 GHz ISM/WiFi | 2400–2500 | observatory_local | 0.95 | provisional |

---

## Scientific Guardrails

- Activating RFI entries does not change candidate scores retroactively.
- The RFI rejection guard only suppresses hits that match an `active: true` entry
  at the time of pipeline execution.
- Activating an entry is not a detection claim or external submission.
- If an entry is activated in error, set `active: false` and re-run the pipeline.
  No scored candidate packets are modified automatically.

---

## Completion Criteria for Tier 1 RFI Gap

The "Real site-specific RFI database" Tier 1 gap is considered closed when:

1. `rfi-admit-gbt-provisional-v1` reaches `admission_status: "ready_for_local_fixture"`
2. `blocker_count: 0` for all admission records
3. `active: true` on at least the GPS L1, GPS L2, ADS-B, and Iridium entries
   (minimum confident set from public regulatory documentation)
4. `validate-all` reports `ok=True` with all RFI database gates passing
5. At least one real GBT observation cadence scores hits in these bands as expected
   (confirming the catalog is functioning for RFI rejection)
