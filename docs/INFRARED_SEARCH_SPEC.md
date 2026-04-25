# INFRARED SEARCH SPEC

## Purpose

Define the infrared waste-heat and Dyson-style candidate search track.

This track searches catalog data for unusual infrared excess or SED behavior that may deserve follow-up.

---

## Initial Search Focus

- Gaia stellar context
- 2MASS near-infrared photometry
- WISE / AllWISE / CatWISE mid-infrared photometry
- SED consistency checks
- mid-infrared excess features
- dust, galaxy, AGN, YSO, AGB, and blending rejection

---

## Candidate Features

Infrared candidates should include:

```text
gaia_source_id
ra
dec
parallax
proper_motion
g_mag
bp_rp
j_mag
h_mag
k_mag
w1
w2
w3
w4
ir_excess_score
sed_fit_residual_score
stellar_solution_quality
galaxy_agn_indicator_score
dust_indicator_score
confusion_score
photometric_quality_score
```

---

## Evidence Supporting Waste-Heat Interest

- strong mid-infrared excess
- stellar-like Gaia solution
- plausible parallax and proper motion
- clean photometric flags
- isolated source
- SED inconsistent with normal stellar emission alone
- no obvious natural contaminant class

---

## Evidence Supporting Natural Explanation

- debris disk or dust-like SED
- young stellar object indicators
- AGB-like colors
- star-forming region context
- known variable or dusty source class

---

## Evidence Supporting Galaxy / AGN

- extended morphology
- extragalactic catalog match
- AGN-like colors
- weak or absent stellar parallax/proper motion
- poor Gaia stellar solution

---

## Evidence Supporting Blending / Confusion

- crowded field
- nearby bright source
- poor WISE image quality
- large positional mismatch
- inconsistent cross-match
- large photometric uncertainties

---

## Minimum v0 Workflow

```text
synthetic infrared source features
→ IR-excess score
→ contaminant checks
→ posterior-style score
→ pathway classification
```

No live catalog queries are required for v0.

---

## Future Workflow

```text
Gaia source sample
→ cross-match WISE / 2MASS
→ compute SED features
→ reject obvious contaminants
→ score candidates
→ generate report
```

---

## Scientific Guardrails

- Do not claim Dyson sphere detection.
- Use “infrared-excess candidate” or “waste-heat-interest candidate.”
- Always include natural explanations.
- Always include confusion/blending risk.
- Always include catalog and photometric quality flags.
