# External Submission Protocol

**Status:** Blocked. No candidate may be externally submitted under this protocol
until all preconditions below are satisfied.

**Last updated:** 2026-06-14

---

## Purpose

This document defines the citizen-science protocol for external submission of a
technosignature-interest candidate report. It is a scheduling aid and operator
reference only. No step in this protocol constitutes a detection claim, scientific
confirmation, or authorization to submit. All gates must be satisfied and explicitly
cleared by a human operator before any submission contact is made.

---

## What "External Submission" Means Here

External submission means transmitting a candidate report or supporting data to:

- A peer-reviewed journal
- A preprint server (arXiv, etc.)
- A formal telescope facility or follow-up coordination network
- Any public forum intended to communicate a candidate signal claim

It does NOT include:

- Posting the pipeline source code, schema artifacts, or negative-result summaries
  to public repositories (already permitted and encouraged)
- Sharing the reproducibility review package with citizen-science communities for
  independent validation (already permitted; see `docs/CALIBRATION_TRANSFER_PROTOCOL.md`)
- Publishing this document or pipeline documentation

---

## Preconditions (All Required)

### P1 — Candidate Review Packet Exists

A formal `candidate_review_packet` (as defined in `docs/PIPELINE_SPEC.md`) must
exist for the candidate. The packet must include:

- turboSETI hit table with real telescope data (not synthetic)
- Scored candidate JSON with `recommended_pathway: candidate_review_packet`
- Escalation record from `create_escalation_record()` with `operator_cleared: False`
  as-created (clearing happens in P6)
- SHA-256 of the source data file
- Pipeline config version

### P2 — Escalation Gate Passes

`escalation_gate_check(candidate_dict)["passes"]` must return `True`, meaning:

- `recommended_pathway == "candidate_review_packet"`
- SNR ≥ 42.4 (noise floor threshold from calibrated GBT noise data)
- `multi_epoch_persistence_score > 0` (signal must persist across ≥2 epochs)

Single-epoch candidates do not pass and must not be submitted.

### P3 — Cross-Target RFI Suppression Cleared

`flag_cross_target_rfi()` must NOT have flagged the candidate as likely terrestrial.
If the same frequency appears in ≥2 independent targets, it is RFI — stop.

### P4 — Independent Citizen-Science Reproduction

At least one independent citizen-science environment must have:

1. Downloaded the same source data (verified by SHA-256 match)
2. Run the same pipeline version
3. Produced a `validate-all ok: True` result
4. Reproduced the same pathway assignment and SNR (within scoring determinism bounds)

This is the citizen-science analog of independent confirmation. It is NOT peer review.
Document the reproduction in a `reproduction_record` with the reproducer's environment
details and the `validate-all` output.

### P5 — Public Reproducibility Package Posted

The following must be publicly posted before any submission contact:

- The candidate review packet (Markdown report + JSON manifest)
- The turboSETI hit table (the `.dat` file)
- The pipeline version and `validate-all` output
- The reproduction record from P4
- This protocol document and the `CALIBRATION_TRANSFER_PROTOCOL.md`

Acceptable public venues: GitHub release, Zenodo archive, Breakthrough Listen
community forum, or equivalent indexed public repository.

The posting must be timestamped and include the explicit disclaimer:

> "This is a citizen-science candidate report. It has not been peer reviewed
> and does not constitute a confirmed technosignature. Independent scientific
> review has not occurred."

### P6 — Operator Sign-Off

A human operator must review all preceding preconditions and explicitly set
`operator_cleared: True` on the escalation record. This must be done manually —
no automated process may set this flag.

The operator must record in the escalation record's notes:

- Date of clearance
- Confirmation that P1–P5 are satisfied
- Name or handle of the operator (for accountability)
- Name or handle of the P4 reproducer (must be a different person)

### P7 — External Review Contact (Advisory)

Before formal submission to a journal or facility, consider contacting:

- The Breakthrough Listen team (if the candidate originates from BL data)
- The SETI Institute candidate coordination process (if applicable)
- A radio astronomy collaborator who can perform an independent frequency/RFI check

This step is advisory. Citizen-science production does not assume expert access.
If no contact is possible, document the attempt and proceed only if P1–P6 are
fully satisfied and the public reproducibility package (P5) has received
substantive public scrutiny (comments, independent downloads, questions answered).

---

## What Is Currently Blocked

As of 2026-06-14, external submission is blocked because:

1. No candidate has passed the escalation gate on real multi-epoch data beyond
   the HIP99427 calibration corpus.
2. P4 (independent reproduction) has been completed for `validate-all` only;
   no specific candidate has been independently reproduced end-to-end.
3. P5 (public reproducibility package) has been posted for the pipeline methodology
   but not for any specific high-interest candidate.
4. P6 (operator sign-off) has not occurred for any candidate.
5. `external_review_authorized: False` on all escalation records (as required).

---

## Submission Document Checklist

When preconditions P1–P6 are satisfied, prepare:

- [ ] Cover letter stating citizen-science origin, pipeline version, and methodology
- [ ] Candidate review packet (PDF or Markdown)
- [ ] turboSETI hit table and source data SHA-256
- [ ] `validate-all` output at time of submission
- [ ] Public reproducibility package URL
- [ ] Reproduction record from P4
- [ ] Escalation record with `operator_cleared: True`
- [ ] Explicit disclaimer that no detection is claimed pending peer review

---

## Scientific Guardrails (Permanent)

Regardless of precondition status:

1. No candidate report constitutes a confirmed technosignature.
2. No submission implies scientific confirmation or discovery.
3. Extraordinary claims require extraordinary evidence; the burden remains on the
   submitters to demonstrate that all mundane explanations have been addressed.
4. Expert review and peer review remain unclaimed until they actually occur.
5. This protocol may be updated, but no update retroactively clears any gate.

---

## Decision Reference

See `docs/DECISIONS.md` DECISION-132 for the formal record of this protocol.
