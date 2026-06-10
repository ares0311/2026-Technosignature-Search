# Citizen-Science Review Protocol

## Scope

This project does not assume access to professional radio astronomers, telescope
staff, or institutional review. Local production-readiness decisions therefore
use transparent evidence and reproducibility rather than authority.

This protocol does not constitute external expert validation or peer review.
External submission and discovery claims remain prohibited.

## Review Standard

A real derived dataset may be approved for local evaluation only when:

1. The source data, license, processing parameters, and hashes are recorded.
2. The unit of analysis is defined without pseudo-replication.
3. Primary labels follow a versioned deterministic rule.
4. A structurally independent second method audits every label.
5. Disagreements are retained as `insufficient_evidence`.
6. The complete labeling method and aggregate outcomes are reproducible.
7. No label asserts a confirmed technosignature or astrophysical origin.
8. External submission remains disabled.

## HIP99427 Label Semantics

The unit of analysis is one exact turboSETI frequency/drift bin across the six
ABACAD scans, not one CSV row. Multiple rows for the same bin are repeated
measurements and must not be treated as independent examples.

Labels are operational:

- `false_positive`: the bin appears in any OFF-target scan. This includes
  ON/OFF recurrence and OFF-only groups.
- `follow_up`: the bin appears in all three ON-target scans and no OFF-target
  scan. This means only that the cadence pattern merits further review.
- `insufficient_evidence`: the bin appears in fewer than three ON-target scans
  and no OFF-target scan, or the two review methods disagree.
- `known_object`: reserved for independently documented catalog matches; it is
  not assigned from cadence behavior alone.

## Independent-Method Audit

The primary method labels from ON/OFF counts. The audit method independently
reconstructs the six-position cadence bitmask from source-artifact identities.
Agreement is required for admission. This is methodological independence, not
independent human expertise.

## Literature Context

The protocol follows the false-positive-first use of ON/OFF cadences described
in Breakthrough Listen searches and retains the stronger verification caveats
demonstrated by the analysis of blc1. Public references:

- Enriquez et al. 2017, ApJ 849:104.
- Sheikh et al. 2021, analysis of blc1, arXiv:2111.06350.
- Choza et al. 2023, GBT galaxy search, arXiv:2312.03943.

## Limits

One cadence cannot establish population-level calibration, site-wide RFI
coverage, or survey sensitivity. The resulting labels may support local
pipeline evaluation but cannot by themselves validate production thresholds.
