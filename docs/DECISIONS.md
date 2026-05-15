# DECISIONS

## Purpose

This file records durable architectural, scientific, and engineering decisions for the Technosignature Search project.

This file should be append-only in spirit. If a decision changes, add a new decision that supersedes the earlier one rather than silently rewriting history.

---

## DECISION-001: Build a Multi-Modal Technosignature Search Platform

**Date:** 2026-04-25  
**Status:** Accepted

### Context

Technosignatures can take multiple possible forms, including radio signals, infrared waste heat, and unusual archival or catalog behavior. A single-track project would be easier to build but less aligned with the breadth of the field.

### Options Considered

1. Radio-only SETI search
2. Infrared-only waste-heat search
3. Archival anomaly search
4. Multi-modal platform

### Decision

Build the project as a multi-modal platform from day one.

Initial tracks:

- radio technosignatures
- infrared waste heat / Dyson-style candidates
- archival and catalog anomalies

### Rationale

- Reflects the diversity of technosignature concepts.
- Allows multiple citizen-science contribution modes.
- Avoids overcommitting to one narrow hypothesis.
- Encourages shared scoring, reporting, and provenance infrastructure.

### Consequences

- More design complexity.
- Requires disciplined modular architecture.
- Requires track-specific false-positive models.

---

## DECISION-002: Use `techno_search` as the Python Package Name

**Date:** 2026-04-25  
**Status:** Accepted

### Decision

Use `techno_search` as the package name.

### Rationale

- Short and readable.
- Suitable for imports.
- Broad enough for multi-modal technosignature work.
- Avoids overly long package names.

---

## DECISION-003: Mirror the Exoplanet Project Documentation Architecture

**Date:** 2026-04-25  
**Status:** Accepted

### Context

The exoplanet project established a useful documentation system for agent continuity and scientific planning.

### Decision

Mirror the same documentation pattern:

- `README.md`
- `AGENTS.md`
- `CONTRIBUTING.md`
- `docs/PROJECT_STATUS.md`
- `docs/ROADMAP.md`
- `docs/DECISIONS.md`
- `docs/PIPELINE_SPEC.md`
- `docs/SCORING_MODEL.md`
- track-specific specs
- `docs/DATA_POLICY.md`

### Rationale

- Reuses a proven workflow.
- Helps future agents orient quickly.
- Separates public project face, active work, durable decisions, and detailed specs.
- Reduces repeated planning work.

---

## DECISION-004: Use Conservative Scientific Language

**Date:** 2026-04-25  
**Status:** Accepted

### Decision

The project must not claim confirmed technosignatures.

Use:

- candidate signal
- anomaly
- follow-up target
- technosignature-interest candidate

Avoid unsupported claims:

- confirmed technosignature
- alien signal
- proof of extraterrestrial intelligence
- discovery of extraterrestrial intelligence

### Rationale

Technosignature searches are highly vulnerable to false positives and sensational interpretation. Conservative language protects scientific credibility.

---

## DECISION-005: Treat False Positives as the Default Hypothesis

**Date:** 2026-04-25  
**Status:** Accepted

### Decision

All candidate scoring and reporting should assume false-positive explanations are more likely than true technosignatures until evidence survives structured vetting.

### Rationale

Likely false-positive sources include:

- radio frequency interference
- satellites and aircraft
- instrumental artifacts
- catalog errors
- dust and astrophysical infrared excess
- galaxies and AGN
- stellar variability
- survey-depth differences
- moving objects
- image artifacts

---

## DECISION-006: Build Shared Scoring Before Large Data Ingestion

**Date:** 2026-04-25  
**Status:** Accepted

### Decision

The first implementation milestone should be the multi-modal scoring and pathway core using synthetic inputs.

### Rationale

- Avoids dependency on large external datasets too early.
- Makes testing easier.
- Establishes scientific guardrails first.
- Creates a stable interface for all search tracks.

---

## DECISION-007: Use Test-First or Test-Alongside Development

**Date:** 2026-04-25  
**Status:** Accepted

### Decision

Every meaningful code change must include unit tests, relevant integration tests, and scientific sanity tests.

### Rationale

The project involves scientific inference and anomaly detection. Untested code risks producing misleading candidates.

---

## DECISION-008: Mock External Services in Default Tests

**Date:** 2026-04-25  
**Status:** Accepted

### Decision

Default tests must not require live network access.

Live tests must be marked:

```python
@pytest.mark.integration_live
```

### Rationale

- Avoids flaky tests.
- Supports reproducible development.
- Makes agent work more reliable.

---

## DECISION-009: Use Config Files for Thresholds

**Date:** 2026-04-25  
**Status:** Proposed

### Proposed Decision

Store thresholds in versioned config files:

```text
configs/radio_search_v0.yaml
configs/infrared_search_v0.yaml
configs/anomaly_search_v0.yaml
configs/scoring_v0.yaml
```

### Rationale

- Makes scientific choices auditable.
- Supports reproducibility.
- Avoids hardcoded threshold drift.

---

## DECISION-010: Document Local System Profile for Performance Defaults

**Date:** 2026-05-01

**Status:** Accepted

### Decision

Maintain `docs/LOCAL_SYSTEM_PROFILE.md` as the source of truth for local workstation capabilities and default performance guidance.

### Rationale

- The project will eventually process synthetic search grids, catalog-like tables, and array-heavy radio or image products.
- Local defaults should make practical use of the available Apple Silicon workstation without starving the OS or interactive tools.
- Hardware-aware defaults help development speed, but scientific behavior must remain portable and reproducible.

### Consequences

- Worker counts, batch sizes, memory budgets, cache paths, and hardware acceleration must be configurable.
- Code may choose local defaults informed by `docs/LOCAL_SYSTEM_PROFILE.md`.
- Scoring thresholds, scientific claims, candidate provenance, and false-positive handling must not depend on this local hardware profile.

---

## DECISION-011: Defer Advanced AI Until Baselines and Calibration Exist

**Date:** 2026-05-01

**Status:** Accepted

### Decision

The project should eventually evaluate CNNs, Transformers, self-supervised learning, multimodal embeddings, and other state-of-the-art AI methods for candidate triage and feature extraction.

These methods must be deferred until interpretable baselines, candidate schemas, provenance, reporting, synthetic injection tests, and calibration datasets are in place.

### Rationale

- Modern AI may help identify subtle morphology, temporal structure, cross-survey patterns, and clusters of similar candidates.
- The project needs strong false-positive discipline before adding high-capacity models.
- Learned scores are useful only if they are calibrated, reproducible, and explained alongside conventional evidence.

### Consequences

- Initial implementations should remain interpretable and testable.
- Future AI models must record training data, model version, evaluation metrics, and runtime configuration.
- AI outputs must support, not replace, conservative pathway classification and human review.

---

## DECISION-012: Use JSON for Initial v0 Runtime Config

**Date:** 2026-05-01

**Status:** Accepted

### Decision

Use JSON for the initial v0 scoring config in `configs/scoring_v0.json`.

### Rationale

- JSON can be read with the Python standard library.
- The first implementation should avoid adding YAML parsing before the package scaffold and tests are stable.
- Thresholds and local performance defaults still remain versioned and auditable.

### Consequences

- Future YAML config files remain possible when a parser dependency is justified.
- Config readers should keep the public schema simple enough to migrate between JSON and YAML later.

---

## DECISION-013: Generate Conservative Reports From Scored Candidates

**Date:** 2026-05-01

**Status:** Accepted

### Decision

Generate Markdown reports and JSON packets directly from `ScoredCandidate` objects.

### Rationale

- Reporting should preserve the exact scores, pathway, evidence, and provenance emitted by the scoring core.
- Every packet must include the required disclaimer and false-positive discussion.
- The first reporting implementation should be deterministic and dependency-free.

### Consequences

- Reports are review packets, not claims of discovery.
- Future plotting or disk-writing helpers should build on the same canonical packet shape.
- Report tests must check for conservative language and required evidence sections.

---

## DECISION-014: Emit Manifests for Persisted Candidate Reports

**Date:** 2026-05-01

**Status:** Accepted

### Decision

When Markdown and JSON candidate packets are written to disk, also write a manifest JSON file.

### Rationale

- Persisted reports need provenance about where packet files were written.
- The manifest gives downstream review tools a stable index without parsing Markdown.
- Code version, config version, candidate ID, pathway, and timestamp help reproduce generated artifacts.

### Consequences

- Report writers emit three files: Markdown, JSON packet, and manifest JSON.
- Manifest code commit is best-effort and may be null when Git metadata is unavailable.
- Future batch report writers should aggregate these per-candidate manifests.

---

## DECISION-015: Separate Background Target Priority From Candidate Evidence

**Date:** 2026-05-08

**Status:** Accepted

### Decision

Background/passive search target priority is a scheduling aid only. It must remain separate from candidate scoring, discovery language, and external submission pathways.

### Rationale

An automated or semi-automated target selector can be useful for deciding what to inspect next, but a high-priority target can still be an ordinary false positive, a weak metadata packet, or a negative search result. The system must therefore log searched targets, expose blocking issues, and route any generated candidates through the normal conservative scoring and review packet workflow.

### Consequences

- Target-priority weights must be versioned and auditable.
- False-positive probability and blocking issues must penalize target priority.
- Passive/background search runs must append ledger entries, including negative searches.
- A selected target ID must not be presented as evidence of a technosignature-interest candidate.

---

## DECISION-016: Keep The v0 Passive Runner Local-Only And Explicitly Opt-In

**Date:** 2026-05-08

**Status:** Accepted

### Decision

The first passive/background runner must be local-only, fixture-backed, and explicitly opt-in. It may append a ledger entry for the selected target, but it must not query live providers, claim candidate extraction, or bypass the normal candidate scoring/reporting workflow.

### Rationale

Passive search infrastructure is useful only if it improves reproducibility. A background process that silently searches, silently drops negative results, or presents a target-selection score as candidate evidence would undermine the project's scientific guardrails.

### Consequences

- The runner records `candidate_count` as `0` until candidate extraction is implemented.
- The runner routes scheduling-only entries to `github_reproducibility_only`.
- The runner requires an explicit CLI acknowledgement flag.
- Generated local ledgers should be written to ignored paths unless reviewed as tiny fixtures.

---

## DECISION-017: Append Benchmark Runs Rather Than Rewriting Benchmark History

**Date:** 2026-05-08

**Status:** Accepted

### Decision

Local synthetic benchmark run results should be appended as new run entries instead of overwriting prior run metadata.

### Rationale

Benchmark metadata is useful for reproducibility only when it preserves execution context across repeated local validation runs. Rewriting prior runs would make local drift, worker-count changes, config changes, and status changes harder to audit.

### Consequences

- Each benchmark run requires a unique `run_id`.
- Each run records command name, command kind, status, worker count, input case count, duration, git commit, and config version.
- Repeated-run comparison reports deltas for local validation drift only.
- Benchmark deltas are not survey sensitivity estimates, candidate-quality metrics, discovery claims, or calibrated scientific performance claims.

---

## DECISION-018: Require Readiness Review Before Curated Non-Synthetic Calibration

**Date:** 2026-05-08

**Status:** Accepted

### Decision

Curated non-synthetic validation datasets must pass an explicit readiness review before they can be used to support calibration or performance claims.

### Rationale

Non-synthetic examples can improve scientific relevance, but they also introduce licensing, provenance, labeling, catalog ambiguity, and review risks. A dataset that is interesting is not automatically admissible for calibration. Readiness review forces the project to surface missing evidence and blocking issues before using non-synthetic data to tune or characterize the model.

### Consequences

- Readiness records must distinguish `ready`, `blocked`, and `not_yet_admissible` states.
- Readiness summaries must expose evidence requirements, satisfied evidence, blocking issues, and external-review requirements.
- A readiness status is a review gate only; it is not a detection, discovery, external validation, or calibrated survey-performance claim.

---

## DECISION-019: Preserve Reviewed Workflow Semantics In Background Search Ledgers

**Date:** 2026-05-09

**Status:** Accepted

### Decision

Passive/background search ledger entries must record reviewed-workflow semantics in addition to basic run metadata.

Required reviewed-workflow fields include execution mode, selected priority score, target-selection rationale, candidate packet IDs, negative-result logging, human-review requirement, and reviewed workflow status.

### Rationale

Background search infrastructure is useful only when another person can reconstruct what was searched, why it was searched, whether a candidate packet exists, and what ordinary blocking issues remain. A ledger that only records target IDs and counts is not enough for conservative review handoff.

### Consequences

- Scheduling-only local runs must be labeled as `local_scheduling_only`.
- No-candidate runs must preserve `negative_result_logged`.
- Candidate packet IDs must be listed separately from target-priority scores.
- Human-review requirements and blockers must be visible in summaries.
- Reviewed-workflow summaries remain operational diagnostics only; they are not detections, discoveries, external validation, or calibrated survey-performance claims.

---

## DECISION-020: Require Candidate-Extraction Handoffs Before Background Candidate Generation

**Date:** 2026-05-09

**Status:** Accepted

### Decision

Background-selected targets must pass through an explicit candidate-extraction handoff contract before they can generate or reference candidate packets.

The handoff must record required inputs, available inputs, expected candidate packet IDs, fixture paths, blocking issues, negative-result requirements, human-review requirements, execution mode, and network-access state.

### Rationale

Target selection, candidate extraction, candidate scoring, and reporting are separate scientific stages. Without a handoff contract, a scheduling recommendation could be mistaken for candidate evidence or a local fixture could quietly bypass provenance review.

### Consequences

- The v0 handoff fixture is local-only and has network access disabled.
- A ready handoff means only that local fixture inputs are present.
- Blocked and no-candidate handoffs must preserve blocking issues and negative-result requirements.
- Candidate packet IDs remain explicit outputs of extraction, not properties of target priority.
- Handoff summaries are operational diagnostics only; they are not detections, discoveries, external validation, or calibrated survey-performance claims.

---

## DECISION-021: Use External Scheduling With Bifurcated Background Outcome Logs

**Date:** 2026-05-09

**Status:** Accepted

### Decision

Operational background search should be driven by an external scheduler that invokes one bounded `background-run-once` command. The command must write one durable ledger entry and exactly one outcome entry: either a reviewed log entry or a needs-follow-up log entry.

Target selection should use the configured composite priority score plus review-history adjustment. Promising never-reviewed targets receive a bounded boost, and previously reviewed targets receive a bounded penalty so the scheduler explores useful unreviewed targets without erasing prior evidence.

### Rationale

External schedulers make each run auditable, restartable, and easier to reproduce. Separate reviewed and needs-follow-up logs make the operational decision explicit without overloading the durable ledger. Review-history scoring keeps the system from repeatedly selecting the same target when another promising target has not yet been assessed.

### Consequences

- The durable ledger remains the source of truth for every run.
- Reviewed logs preserve negative evidence and reasons no follow-up is currently required.
- Needs-follow-up logs preserve trigger types, reason codes, mandatory tests, report requirements, human-review requirements, and the user approval gate.
- The local runner remains fixture-only and non-networked by default.
- Needs-follow-up records are not detections, not discovery claims, and not submission approvals.

---

## DECISION-022: Gate Background Reports Behind Mandatory Follow-Up Tests

**Date:** 2026-05-09

**Status:** Accepted

### Decision

Needs-follow-up background records must pass through deterministic local follow-up test records before any draft report is considered ready. Required tests cover provenance, false-positive class, cross-source consistency, calibration confidence, reproducibility, and human-review checklist status.

Report-readiness records must state whether mandatory tests are complete, whether a conservative draft report may be prepared, whether more tests are required, and which top-three review or submission destinations are recommended. External submission must remain disabled until the user explicitly approves it.

### Rationale

A needs-follow-up queue is useful only if it leads to structured review rather than vague escalation. Mandatory tests force the system to preserve negative evidence, blockers, and uncertainty before drafting a report. Ranked recommendations help the user decide where the report might go, while preserving the human approval gate.

### Consequences

- Follow-up tests are local fixtures by default and do not access the network.
- A passed or ready local test is not external validation.
- Blocked and uncertain tests must remain visible in summaries.
- Top-three recommendations may include `Do not submit yet`.
- Report-readiness records are not discoveries, endorsements, or authorization to submit externally.

---

## DECISION-023: Preserve Draft Reports And User Decisions As Separate Gates

**Date:** 2026-05-09

**Status:** Accepted

### Decision

Background draft follow-up reports and user decisions must remain separate records.

Draft reports may summarize report-ready or blocked records conservatively, but they must not authorize external submission. User decisions may request more tests, close an item as reviewed, or explicitly approve submission. The committed v0 fixtures keep external submission approval false.

### Rationale

Report drafting and submission approval are different scientific workflow steps. A draft report helps a reviewer inspect evidence, negative evidence, uncertainty, limitations, and blockers. Approval requires an explicit human decision and should not be inferred from readiness, recommendations, or draft generation.

### Consequences

- Draft report summaries must preserve negative evidence, limitations, blocking issues, and conservative next steps.
- User decision records must expose whether external submission was explicitly approved.
- External submission remains blocked by default.
- Scheduler examples may produce logs and summaries, but they must not contact outside parties or enable live provider access by default.

---

## DECISION-024: Persist Draft Reports Only As Local Review Artifacts

**Date:** 2026-05-09

**Status:** Accepted

### Decision

Persisted background draft follow-up reports may be written as Markdown plus a manifest, but they remain local review artifacts. The writer should target ignored `artifacts/` paths by default in examples, and validation must require the conservative disclaimer, negative evidence, uncertainty, blocking issues, and disabled external-submission and network-access gates.

User-decision authoring may append local decision records. `request_more_tests` and `close_as_reviewed` must not imply submission approval. `approve_submission` requires explicit approval, destination, and rationale fields.

### Rationale

Operators need files they can read and review, but persisted reports create a higher risk of being mistaken for shareable scientific claims. The manifest and validator make the gate visible and machine-checkable.

### Consequences

- Draft report Markdown must include evidence, negative evidence, uncertainty, limitations, blocking issues, next steps, and gate states.
- Validation checks persisted draft report directories.
- Scheduler dry-runs write to temporary artifact directories without live provider access.
- External submission still requires explicit human approval outside ordinary report generation.

---

## DECISION-025: Use Top-Level SQLite Logs For Operational Background Runs

**Date:** 2026-05-09

**Status:** Accepted

### Decision

Operational background-search logs must live in a top-level SQLite database under `logs/`, with `logs/techno_search.sqlite3` as the default local path. JSON ledgers and outcome files may remain as small fixtures and compatibility artifacts, but SQLite is the operational source of truth for scheduled or local background runs.

The SQLite log must record each background run, exactly one reviewed or needs-follow-up outcome per run, schema metadata, code commit, config version, target-selection rationale, negative evidence, blocking issues, draft-report slots, user-decision slots, and validation events.

### Rationale

SQLite gives the project a durable, queryable, transactional log without adding a third-party dependency. A top-level `logs/` directory makes operational state obvious to operators while allowing generated databases to stay ignored by Git. This also reduces drift between scheduler output, review summaries, and validation checks.

### Consequences

- Generated SQLite databases are not committed.
- The local runner can mirror each bounded run into SQLite with `--sqlite-log-path`.
- Validation checks that every SQLite run has exactly one outcome.
- Network access remains disabled by default in SQLite logs.
- External submission approval must not appear unless directly recorded by the user.
- SQLite rows are workflow and provenance records only; they are not detections, discoveries, external validation, or submission approval.
- SQLite integrity summaries, migration checks, review-safe exports, and commit guards are part of the operational safety boundary.

---

## DECISION-026: Cross-Track References Are Operational Metadata Only

**Date:** 2026-05-15

**Status:** Accepted

### Decision

Cross-track candidate cross-references record that two or more independently-scored candidate packets share the same target across radio, infrared, or anomaly tracks. They are operational metadata only and must not modify candidate posteriors, false-positive probability, derived scores, or the recommended pathway. Each contributing track preserves its own evidence and blocking issues independently.

### Rationale

A target appearing in multiple tracks is operationally interesting because it can guide reviewer attention, but cross-track agreement is not by itself evidence for any candidate hypothesis. Allowing cross-references to boost scores would silently couple track outputs and weaken the false-positive-first scoring discipline.

### Consequences

- The cross-track summary command and fixture stay strictly descriptive.
- The fixture covers operational cross-references, conflicting evidence, single-track-only entries, and known-object cross-matches.
- Conflicting and known-object entries are recorded so the absence of a candidate claim is auditable.
- Tests assert that candidate scoring is byte-identical with and without loading cross-references.

---

## DECISION-027: Reproducibility Verification Reports Drift, Never Auto-Corrects

**Date:** 2026-05-15

**Status:** Accepted

### Decision

Persisted candidate report packets must be re-scoreable using the current scoring implementation. The reproducibility verification command compares recomputed scores, posteriors, and pathway against the persisted packet and reports drift. It must never overwrite persisted packets, manifests, or example artifacts.

### Rationale

Drift between persisted packets and current scoring can have many causes (intentional scoring change, schema bump, config bump, accidental regression). A tool that silently corrects historical artifacts would erase the audit trail. Operators must investigate the cause and re-publish artifacts deliberately.

### Consequences

- The verifier is read-only.
- Drift reports include schema-version and config-version mismatches.
- The verifier exits non-zero when drift is detected, and `validate-all` requires zero drift on the committed examples.
- A future migration is required when drift is intentional; this command is not a substitute for that migration.

---

## DECISION-028: Interpretable Rule-Based Baseline Must Precede Any Learned Model

**Date:** 2026-05-15

**Status:** Accepted

### Decision

Before any trained or learned model is introduced into the pathway routing system, an interpretable rule-based baseline classifier must be implemented, tested, and evaluated. The baseline (`RuleBasedBaselineClassifier`) must reproduce the current scoring pathway logic using explicitly named boolean rules, and it must achieve at least 80% pathway accuracy across the synthetic calibration and example candidate fixtures.

### Rationale

A learned model is opaque; without a rule-based reference implementation there is no way to audit whether the model is routing candidates for the right reasons. The baseline also serves as a regression anchor: if a future model underperforms the baseline on calibration false-positives or clean candidates, that is a red flag requiring investigation before the model can be promoted.

### Consequences

- `baseline_model.py` contains the rule-based classifier with named rule constants that map 1:1 to conditions in the scoring model pathway logic.
- `baseline_eval.py` evaluates the classifier against calibration false-positive fixtures and example clean candidates.
- The `baseline-eval-summary` CLI command exposes pathway accuracy, false-positive recall, and candidate precision as local synthetic diagnostics.
- `validate-all` enforces a minimum 80% pathway accuracy gate on every run.
- Baseline outputs carry an explicit disclaimer that they are not detections, discoveries, confirmations, or external validation.

---

## DECISION-029: Weekly Review Template Is The Authoritative Operator Handoff

**Date:** 2026-05-15

**Status:** Accepted

### Decision

The `weekly-review-template` CLI command is the authoritative local handoff artifact for operator scheduling review. It must explicitly confirm that `network_access_allowed_count == 0` and `external_submission_approved_count == 0` before any operator action is taken. The template is the only location where watchlist priority ordering, baseline drift status, and cross-track reference counts are combined into a single reviewable document.

### Rationale

Having multiple disparate summaries (watchlist, baseline drift, cross-track) scattered across separate CLI commands creates a fragmented review workflow. A weekly review template that gathers all operational signals into one document with explicit gate confirmations reduces the risk of an operator missing a blocking signal before scheduling follow-up observations.

### Consequences

- `weekly-review-template` consumes the SQLite digest, cross-track summary, and target watchlist summary as inputs.
- The template explicitly sets `network_access_confirmed_zero` and `external_submission_confirmed_zero` gate fields.
- Elevated watchlist targets appear in the recommended next-actions list.
- Baseline pathway drift is checked before committing any scheduled observation cycle.
- The template is a local internal review artifact only and must never be treated as a discovery claim or external submission.

---

## DECISION-030: Scoring Must Be Deterministic Before Any Learned Model Is Introduced

**Date:** 2026-05-15

**Status:** Accepted

### Decision

Before any trained or learned model is introduced into the pathway routing system, scoring must be verified as fully deterministic. The `score-determinism-check` CLI command must pass for all committed example candidates (identical `posterior`, `scores`, and `recommended_pathway` across three or more repeated runs) before any model-training or model-serving infrastructure is added.

### Rationale

Reproducibility is a prerequisite for scientific integrity. If scoring is non-deterministic, baseline evaluation results cannot be relied upon, regression snapshots become meaningless, and comparing trained model outputs against the baseline is impossible. Catching non-determinism early avoids downstream confusion between model variance and genuine signal variation.

### Consequences

- `score-determinism-check` is wired into `validate-all` and must return `all_deterministic: true`.
- Any introduction of randomness (sampling, stochastic inference, data augmentation) must be explicitly gated behind a separate opt-in flag and documented in DECISIONS.md.
- The scoring model must remain deterministic for a given input regardless of execution environment or call count.

---

## DECISION-031: Scoring Config And Route Coverage Are Required Local Validation Gates

**Date:** 2026-05-15

**Status:** Accepted

### Decision

Two new `validate-all` gates are introduced to support Milestone 10 interpretability and calibration work:

1. **Scoring config threshold count** — at least one pathway threshold must be present in `configs/scoring_v0.json`. This ensures the scoring configuration file is not accidentally empty or corrupt.

2. **Route coverage** — at least 2 Pathway enum values must have calibration fixture coverage. This confirms that both the primary positive pathway (`candidate_review_packet`) and primary negative pathway (`do_not_submit_false_positive`) are represented in the synthetic fixture set before any learned model is introduced.

### Rationale

A learned model trained only against fixtures covering a subset of pathways would have undefined behavior for uncovered classes. Requiring minimum route coverage makes gaps explicit before they affect calibration or evaluation.

### Consequences

- `scoring-config-summary` is wired into `validate-all` with a gate of `threshold_count >= 1`.
- `route-coverage-summary` is wired into `validate-all` with a gate of `covered_pathway_count >= 2`.
- `lifecycle-transition-summary` runs in `validate-all` and requires `invalid_transition_count == 0`.
- `observation-efficiency-summary` runs in `validate-all` as a health check with no hard failure gate beyond `completion_rate >= 0.0`.
- All four summaries are scheduling/provenance/diagnostic aids only. They do not authorize external submission or claim detection.
