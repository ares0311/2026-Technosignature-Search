# Local Candidate Routing Pathways

## Purpose

These values are conservative local routing states. They do not authorize
label creation, candidate promotion, expert review, public disclosure, or
external submission. Some names are retained for compatibility with persisted
records and schemas; their current meaning is defined here.

## `known_object_annotation`

Use when a known source, cataloged object, RFI pattern, instrument artifact, or
other documented contaminant explains the observation. Preserve the match and
its provenance. Do not present the result as novel.

## `do_not_submit_false_positive`

Use when false-positive evidence is strong, such as OFF-target presence,
cross-target persistence, known RFI, a cataloged contaminant, or severe data
quality failure. Preserve enough evidence for regression and methodology
review; take no external action.

## `github_reproducibility_only`

Legacy-compatible route for weak, incomplete, exploratory, or method-development
artifacts. It may support clearly scoped code or methodology reproduction, but
it must not be used to publish a candidate claim or request follow-up.

## `human_review_queue`

Legacy-compatible name for local deterministic follow-up triage. It must not
create a labeling queue, ask a person to classify data, or convert an operator
opinion into ground truth. The permitted action is to inspect provenance,
re-run deterministic checks, identify missing evidence, and either explain the
result or leave it unresolved.

## `candidate_review_packet`

Local evidence-packaging route for an unresolved result that has survived the
currently available deterministic checks. A packet must include positive and
negative evidence, provenance, checksums, processing/config versions,
applicable false-positive tests, limitations, and abstentions.

This route does not mean the standalone escalation gate passed. That gate is
currently fail-closed because no admissible calibrated SNR threshold exists.
The packet is not a detection, discovery, expert review, external validation,
or submission authorization.

## `external_followup_candidate`

Disabled legacy-compatible value. No current pipeline result may be routed to
external action from this value. External scientific contact or submission is
governed by `docs/EXTERNAL_SUBMISSION_PROTOCOL.md`, requires the full automated
plus adversarial plus credentialed-expert review chain, and remains subject to
explicit user approval for the particular action.

## Routing Principle

```text
known explanation or artifact
  -> known_object_annotation or do_not_submit_false_positive

insufficient or ambiguous evidence
  -> github_reproducibility_only or human_review_queue
     (local deterministic triage only; no labels)

unresolved after available deterministic gates
  -> candidate_review_packet
     (local packet only; escalation remains fail-closed)

external action
  -> blocked
```

Every route must preserve the statement that no confirmed technosignature is
claimed and no external submission is authorized.
