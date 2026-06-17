# AI Hardening Review Protocol

**Status:** Required before closing DECISION-134.
**Scope:** Citizen-science production evidence for learned and AI-assisted
pathway routing.

---

## Purpose

This protocol defines the minimum reproducible evidence needed to close the
Tier 3 **AI hardening production blocker** recorded in DECISION-134. It is a
local citizen-science review protocol, not expert review, peer review, external
validation, or external submission approval.

The goal is to test whether learned or AI-assisted pathway routing behaves
conservatively on held-out evidence outside the HIP99427 training cadence. The
default interpretation of unusual signals remains false positive or
insufficient evidence unless multiple independent checks preserve stronger
evidence for follow-up.

---

## Required Evidence Streams

At least one held-out real-data evidence stream must exist before this protocol
can be completed. Preferred DECISION-133 paths:

| Evidence path | Role | Current gate meaning |
|---|---|---|
| `data/extended_corpus/` | Non-Cygnus GBT L-band hit tables | Same telescope/band transfer evidence |
| `data/meerkat_hits/` | MeerKAT BLUSE false-positive corpus | Cross-instrument RFI behavior evidence |
| `data/injection_grid/` | Synthetic injections into real GBT noise | Recovery and false-negative stress test |

Large data, local caches, SQLite logs, generated scan outputs, and HDF5 files
must remain uncommitted. Only review-safe summaries, manifests, methodology,
and provenance may be committed.

---

## Operator Preflight

Every local run starts from current `main`:

```bash
git pull origin main
.venv/bin/techno-search ai-hardening-gate-summary
.venv/bin/techno-search validation-summary
```

The AI hardening gate must report:

- `status: "open"` until all requirements are complete
- `production_promotion_allowed: false`
- `external_submission_allowed: false`
- `detection_claimed: false`
- `expert_review_claimed: false`

If any of those safety fields differ, stop and fix the gate before running
evidence generation.

---

## Evidence Acquisition

Use existing local data only after confirming it is outside the HIP99427
training cadence and has usable provenance. If no admitted held-out evidence is
available, acquire one or more DECISION-133 streams:

```bash
git pull origin main
caffeinate -i bash scripts/download_bl_extended_corpus.sh
```

```bash
git pull origin main
caffeinate -i .venv/bin/python scripts/ingest_meerkat_hits.py \
  --output-dir data/meerkat_hits \
  --max-hits 200000
```

```bash
git pull origin main
caffeinate -i .venv/bin/python scripts/setigen_injection_grid.py \
  --h5-file data/bl_hits/Voyager1.single_coarse.fine_res.h5 \
  --output-dir data/injection_grid
```

If the HDF5 file for the injection grid is absent, do not substitute a file by
guessing. Record the missing-input blocker and use the file-location protocol
in `AGENTS.md` before asking the operator for help.

---

## Independent Method Review

Run at least two structurally independent methods on the same held-out evidence.
Use more when available.

Required comparison fields:

| Method family | Examples | Required record |
|---|---|---|
| Rule-based scoring | calibrated thresholds, pathway classifier, escalation gate | Pathway, blockers, negative evidence |
| Learned classifier | logistic regression real-label model | Predicted class and confidence |
| Cross-target suppression | repeated-frequency RFI flagging | Frequency matches across targets |
| Dense-cluster filtering | GLOBULAR-style HDBSCAN filter | Dense-cluster/outlier status |
| Semi-supervised anomaly scoring | PCA + IsolationForest scorer | Anomaly score and fitted corpus provenance |

Disagreements are evidence, not failures. Preserve:

- method outputs
- abstentions
- malformed or unusable inputs
- negative evidence
- blocker reasons
- conservative operator notes

Do not force consensus and do not tune thresholds on the held-out evaluation
set.

---

## Review-Safe Evidence Bundle

The completion bundle must include:

- AI hardening gate summary before and after the run
- `validate-all` output from the same checkout
- evidence inventory with relative paths, file counts, and checksums where
  practical
- method comparison table
- disagreement and abstention log
- negative-result summary or escalation-gate output
- provenance notes for all admitted data
- explicit statement that no detection, expert review, peer review, external
  validation, or external submission is claimed

Suggested local commands:

```bash
git pull origin main
.venv/bin/techno-search validate-all
```

```bash
git pull origin main
.venv/bin/techno-search ai-hardening-gate-summary
```

Generated raw outputs should stay local unless they are small, review-safe, and
explicitly intended as methodology or provenance artifacts.

---

## Closure Criteria

DECISION-134 can be proposed for closure only when all are true:

1. Held-out real-data evidence exists outside the HIP99427 training cadence.
2. At least two independent methods were run on the same evidence.
3. Disagreements, abstentions, negative evidence, and blockers are preserved.
4. The review-safe evidence bundle exists and is reproducible from current
   `main`.
5. `validate-all` passes.
6. The gate remains clear that production promotion is local citizen-science
   operations only, with no detection or external-validation claim.

Closing this gate does not authorize external submission. DECISION-132 remains
the controlling protocol for any external submission path.

---

## Permanent Guardrails

- No result from this protocol constitutes a confirmed technosignature.
- Learned, semi-supervised, and AI-assisted scores are local scheduling aids.
- False positives remain the default hypothesis.
- Citizen-science review is not expert review or peer review.
- External validation is unclaimed unless it actually occurs.
- External submission remains blocked unless DECISION-132 is separately
  satisfied and explicitly cleared by the operator.
