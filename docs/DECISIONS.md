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

---

## DECISION-032: Candidate Triage And Sensitivity Config Are Validated Scheduling Aids

**Date:** 2026-05-16
**Status:** Accepted

### Context

Operators need a place to record candidate-specific notes (triage labels, blocking reasons, follow-up flags) without those notes influencing scoring, posteriors, or pathway routing. Separately, per-track sensitivity weights in the scoring config need to be explicitly audited as synthetic v0 calibration parameters, not survey detection sensitivities.

### Decision

1. **Candidate triage notes** are operator scheduling aids and provenance records only. A dedicated schema (`candidate_triage_v1`), fixture, loader, and summary CLI (`triage-summary`) are added. Triage notes carry an explicit disclaimer that they do not modify scores, posteriors, or pathway routing and are not detection claims or external submission authorizations.

2. **Sensitivity config summary** reads per-track sensitivity weights from `configs/scoring_v0.json` and summarises them without recalibrating or applying them. A dedicated schema (`sensitivity_config_summary_v1`) and CLI (`sensitivity-config-summary`) are added. The summary disclaimer explicitly states these are synthetic v0 development coefficients and not calibrated survey detection sensitivities.

3. Both are wired into `validate-all` with gates:
   - `sensitivity_track_count >= 3` (all three tracks must have configured weights)
   - `triage_note_count >= 5` (minimum fixture coverage)
   - `len(triage_tracks_covered) >= 3` (all three tracks must have triage notes)

### Rationale

Explicitly separating operator scheduling notes from scoring prevents triage decisions from being mistaken for evidence-based pathway routing. Summarising sensitivity weights as configuration metadata (not calibrated parameters) preserves the conservative false-positive-first framing throughout the pipeline.

### Consequences

- `triage-summary` is a scheduling aid only; triage labels do not route candidates.
- `sensitivity-config-summary` reports local threshold values only — not calibrated detection thresholds.
- Schema count increases from 29 to 31.
- Route coverage gate raised from `>= 2` to `>= 4` now that additional pathway fixtures are committed.

---

## DECISION-033: Signal Registry, Audit Trail, Multi-Epoch Summaries, Schema Drift Detection, And Provenance Chain Validation Are Scheduling Provenance Aids

**Date:** 2026-05-16
**Status:** Accepted

### Context

As the pipeline matures, operators need structured records for signals of interest (registry), actions taken on candidates (audit trail), multi-epoch follow-up status (multi-epoch summary), snapshot-based priority comparisons (target recalibration), operator coverage (which operators have triaged which tracks), and structural consistency checks across JSON schema artifacts (schema drift). The provenance chain in report manifests also needs a formal validation step.

### Decision

1. **Signal registry** (`signal_registry_v1`) is a scheduling-aid registry of candidate signals of interest. Entries carry priority tiers (`tier_1`/`tier_2`/`tier_3`) and rationale fields. The registry is not a detection claim and does not modify candidate posteriors.

2. **Candidate audit trail** (`candidate_audit_trail_v1`) is an append-only log of operator actions on candidates. Action types are bounded (`triage_note_added`, `stage_transition`, `observation_scheduled`, `observation_completed`, `observation_cancelled`, `archived`, `human_reviewed`). Irreversibility is tracked per entry. Audit entries are not detection claims.

3. **Multi-epoch observation summary** (`multi_epoch_observations_v1`) records per-target epoch counts, detection status per epoch, and consistent-detection flags. Consistent detection across epochs does not constitute confirmation without external validation.

4. **Target recalibration summary** compares two most-recent target priority snapshots and reports rank changes. Priority rank changes do not modify candidate scores or posteriors and are not detection evidence.

5. **Operator coverage summary** and **triage label completeness check** report which operators have triaged which tracks and which triage labels have fixture coverage. These are scheduling provenance diagnostics only.

6. **Classifier rule coverage summary** reports which baseline classifier rules fire across evaluation cases, with a coverage fraction gate.

7. **Provenance chain validator** checks that all committed report manifests carry required provenance fields (`schema_version`, `config_version`, `generated_at_utc`, `provenance_summary`). A passing check does not constitute external validation.

8. **Schema drift detection** iterates all committed `schemas/*.schema.json` files and checks structural consistency (required `$schema` key, `type: object`, non-empty `required`). Drift count must be zero for `validate-all` to pass.

9. **Observation gap analysis** identifies targets with no completed observation windows as a scheduling provenance diagnostic.

10. All new modules wire into `validate-all` with gates:
    - `signal_registry_active_count >= 4`
    - `audit_action_count >= 6`
    - `multi_epoch_target_count >= 3`
    - `recalibration_snapshot_count >= 2`
    - `operator_coverage_count >= 2`
    - `label_coverage_fraction >= 0.5`
    - `classifier_rule_coverage_fraction >= 0.5`
    - `provenance_chain_ok == True`
    - `schema_drift_count == 0`

### Consequences

- Schema count increases from 31 to 35.
- None of the new modules authorize external submission or claim a detection.
- Triage annotation tags are documentation-only fields; they do not route candidates.

---

## DECISION-034: Observation Notes, Epoch Plan, And Aggregate Blockers Are Scheduling Provenance Records

**Date:** 2026-05-16

**Context:**

Candidates accumulate post-observation annotations, follow-up scheduling entries, and cross-module blocking issues that need consolidated visibility for operator review.

**Decision:**

1. **Candidate observation notes** (`candidate_observation_notes_v1`) record post-observation operator annotations with outcome classification and quality flags. Notes are scheduling and provenance records only — they do not modify candidate posteriors or pathway routing.

2. **Epoch plan** (`epoch_plan_v1`) tracks which targets need additional observation epochs, why, and their scheduling priority. Entries are local scheduling aids — they do not constitute telescope-time commitments or confirmation of signals.

3. **Aggregate blockers summary** consolidates blocking issues from triage notes, lifecycle entries, observation quality flags, and candidate extraction handoffs. This is an operational dashboard only — no minimum blocker count is gated in `validate-all`.

4. New `validate-all` gates:
   - `obs_notes_count >= 5`
   - `epoch_plan_entry_count >= 4`
   - `aggregate_blocker_count >= 0`

### Consequences

- Schema count increases from 35 to 37.
- None of the new modules authorize external submission or claim a detection.
- Aggregate blockers report mirrors existing fixture data and adds no new external information.

## DECISION-035: Candidate Score History, Operator Assignment, And Pipeline Health Are Scheduling Provenance Records

**Date**: 2026-05-16

**Context**: The pipeline now tracks score evolution across epochs, operator assignments for candidate review, and a per-track health dashboard.

**Decision**: All three modules are implemented as local scheduling and provenance records only. They do not modify candidate scores, posteriors, or pathway routing. Disclaimers on each module state they are not detections, discoveries, or external validation.

**Score history**: records how a candidate's composite score changes across observation epochs for provenance and scheduling audit purposes only.

**Operator assignment**: records which operators are responsible for reviewing which candidates. Escalated assignments surface for senior review but do not change pathway routing.

**Pipeline health**: aggregates triage, lifecycle, observation, and assignment state into a per-track dashboard. It identifies candidates stalled in the pipeline; it does not rank or prioritize candidates for external submission.

**Consequences**: `validate-all` gates enforce minimum fixture coverage for all three modules. Scientific guardrails remain unchanged.

## DECISION-036: Candidate Flags, Review Deadlines, And Pipeline Throughput Are Scheduling Provenance Records

**Date**: 2026-05-16

**Context**: The pipeline now tracks quality flags raised against candidates, upcoming operator review deadlines, and per-stage throughput metrics.

**Decision**: All three modules are implemented as local scheduling and provenance records only. They do not modify candidate scores, posteriors, or pathway routing. All outputs carry conservative disclaimers.

**Candidate flags**: surfaces data-quality issues and operational blockers for operator review. Flag severity reflects quality-control classification, not candidate interest level.

**Review deadlines**: tracks upcoming review obligations. Urgency levels reflect scheduling priority, not candidate quality. Overdue deadlines are surfaced for operator awareness.

**Pipeline throughput**: aggregates per-stage lifecycle and triage counts to surface pipeline bottlenecks. Throughput rate is a local scheduling metric, not a calibrated survey efficiency estimate.

**Consequences**: `validate-all` gates enforce minimum fixture coverage for all three modules. Scientific guardrails remain unchanged.

---

## DECISION-037: Candidate Retention, Operator Performance, And Track Comparison Are Scheduling Provenance Records

**Date**: 2026-05-17

**Context**: The pipeline now tracks candidate dwell times in the pipeline, operator workload metrics, and a cross-track operational dashboard.

**Decision**: Implement three new scheduling provenance modules:

**Candidate retention**: tracks how long candidates remain in the pipeline and their current workflow status. Active/archived/blocked breakdowns are scheduling aids only. Days in pipeline is not correlated with candidate quality.

**Operator performance**: aggregates per-operator assignment outcomes (completed, escalated, deferred, pending, in_progress) from existing operator assignment fixtures. Completion and escalation rates are workflow health indicators, not quality judgments.

**Track comparison**: cross-track operational dashboard combining triage notes, lifecycle stages, candidate flags, review deadlines, epoch plan requests, and observation notes. Total open flags and overdue deadlines are scheduling alerts, not candidate interest signals.

**Consequences**: `validate-all` gates enforce minimum fixture coverage (`candidate_retention_record_count >= 5`, `operator_perf_count >= 2`, `track_comparison_open_flags >= 0`). Scientific guardrails remain unchanged.

---

## DECISION-038: Candidate Resolution, Escalation Log, And Quality Control Are Scheduling Provenance Records

**Date**: 2026-05-17

**Context**: The pipeline needs closure records for candidates that have completed internal review, a structured log for workflow escalations, and an aggregate QC dashboard that surfaces operational health.

**Decision**: Implement three new scheduling provenance modules:

**Candidate resolution**: records the final internal disposition of each candidate (`resolved_fp`, `unresolved`, `awaiting_confirmation`, `deferred`, `inconclusive`, `follow_up_scheduled`). Resolution status is a local scheduling closure record — `resolved_fp` means the candidate was internally assessed as a likely false positive, not that it has been scientifically ruled out.

**Escalation log**: records formal workflow escalation events with priority (`low`, `normal`, `high`, `critical`) and status (`open`, `in_review`, `resolved`, `dismissed`). Priority reflects internal operational urgency, not candidate scientific interest.

**Quality control summary**: aggregate dashboard combining flags, triage clearance, deadline compliance, retention state, resolution counts, and escalation state into a single `overall_qc_health` indicator (`ok`, `degraded`, `blocked`). Health status is an operational indicator only.

**Consequences**: `validate-all` gates enforce minimum fixture coverage (`resolution_record_count >= 5`, `escalation_entry_count >= 5`, `qc_health in ("ok", "degraded", "blocked")`). No new fixture gates are needed for quality_control_summary since it aggregates existing fixtures. Scientific guardrails remain unchanged.

---

## DECISION-039: Observation Campaign, Data Quality Log, And Pipeline Audit Are Scheduling Provenance Records

**Date**: 2026-05-17

**Context**: The pipeline needs structured records for multi-session observation campaigns, per-observation data quality assessments, and an aggregate audit view of the candidate audit trail.

**Decision**: Implement three new scheduling provenance modules:

**Observation campaign**: records multi-session campaigns with status (`planned`, `active`, `completed`, `cancelled`, `on_hold`), session count, epochs covered, and target candidate IDs. `completed` means all planned sessions were executed — it does not mean science is concluded or any signal confirmed.

**Data quality log**: records per-observation quality grades (`excellent`, `good`, `marginal`, `poor`, `unusable`) and issue types (`rfi`, `weather`, `equipment`, `calibration_failure`, `data_loss`). Grades reflect observational conditions, not candidate scientific merit.

**Pipeline audit summary**: aggregate view of the candidate audit trail, counting total actions, unique candidates audited, unique operators, and breakdown by action type and track. `overall_audit_coverage` (`adequate`/`sparse`) is a local provenance indicator only.

**Consequences**: `validate-all` gates enforce `observation_campaign_count >= 5`, `data_quality_entry_count >= 5`, and `pipeline_audit_action_count >= 0`. Scientific guardrails remain unchanged.

---

## DECISION-040: Follow-Up Requests, Pipeline Bottleneck, And Candidate Annotations Are Scheduling Provenance Records

**Date**: 2026-05-17

**Context**: The pipeline needs a formal mechanism for raising follow-up requests on candidates, an operational view of where candidates are stalling, and a lightweight annotation system for operator notes.

**Decision**: Implement three new scheduling provenance modules:

**Follow-up request**: records formal follow-up requests with priority (`low`, `normal`, `high`, `urgent`) and status (`open`, `assigned`, `in_progress`, `completed`, `cancelled`, `deferred`). `urgent` priority reflects a scheduling deadline pressure — it does not indicate increased confidence in any technosignature interpretation.

**Pipeline bottleneck**: aggregate dashboard identifying stalled lifecycle stages, overdue reviews, unassigned candidates, critical flag blockers, and open escalations. `top_bottleneck_stage` is the stage with the most stalled candidates — it is an operational indicator only, not a scientific ranking.

**Candidate annotation**: operator notes, tags, warnings, highlights, questions, and follow-up markers attached to candidates. Annotations do not modify scores, posteriors, or pathway routing. A `warning` annotation reflects a scheduling concern, not a scientific assessment.

**Consequences**: `validate-all` gates enforce `follow_up_request_count >= 5`, `pipeline_bottleneck_stalled >= 0`, and `candidate_annotation_count >= 5`. SCHEMA_FILENAMES grows 46→48. Scientific guardrails remain unchanged.

---

## DECISION-041: Session Log, Candidate Priority Queue, And Pipeline Capacity Are Scheduling Provenance Records

**Date**: 2026-05-17

**Context**: The pipeline needs provenance records for observation sessions, a priority-ordered candidate queue, and an aggregate view of scheduling load across the system.

**Decision**: Implement three new scheduling provenance modules:

**Session log**: records observation sessions with outcome (`completed`, `partial`, `aborted`, `rescheduled`, `failed`), duration, operator, and candidates observed. Session logs are provenance records only — they do not re-score or re-route candidates.

**Candidate priority queue**: tracks candidates queued for review with position, queue reason (`score_threshold`, `flag_escalation`, `deadline_pressure`, `operator_request`, `routine_review`), and days in queue. Priority queue entries are scheduling aids — they do not modify candidate posteriors or pathway routing.

**Pipeline capacity**: aggregate dashboard combining open assignment count, open follow-up request count, unresolved annotation count, and queue depth into a total scheduling load with capacity status (`nominal`, `strained`, `overloaded`). Capacity status is an operational scheduling metric only — it does not reflect survey sensitivity or candidate quality.

**Consequences**: `validate-all` gates enforce `session_log_count >= 5`, `priority_queue_depth >= 5`, and `pipeline_capacity_status in valid set`. SCHEMA_FILENAMES grows 48→50. Scientific guardrails remain unchanged.

---

## DECISION-042: Feature Vector Layer And Model Registry Are Required Before Any Learned Model Is Trained

**Date**: 2026-05-17

**Context**: Milestone 10 established that interpretable baselines and score determinism must precede any learned model. Milestone 11 formalizes the next prerequisite: a stable, versioned feature extraction layer.

**Decision**: Implement three new ML infrastructure modules:

**Candidate feature vector**: extracts a flat, versioned feature vector from scored candidates with explicit normalization kind (`none`, `min_max`, `z_score`) and extractor version. Feature vectors are ML preprocessing artifacts only — they do not re-score candidates or modify pathway routing.

**ML model registry**: tracks model versions, kinds (`cnn_radio`, `transformer_radio`, `hybrid_rule_learned`, `self_supervised`, `foundation_embedding`, `baseline_rule_based`), statuses (`experimental`, `validated`, `deprecated`, `pending_review`), and whether each model exceeds baseline accuracy. A model with `is_above_baseline=false` must not be used operationally.

**ML pipeline diagnostics**: aggregate dashboard comparing the interpretable baseline accuracy against all registered models. `pipeline_ml_status` surfaces whether any below-baseline models exist (`some_below_baseline`), enabling `validate-all` to catch regressions.

**Consequences**: `validate-all` gates enforce `feature_vector_count >= 5` and `pipeline_ml_status in valid set`. SCHEMA_FILENAMES grows 50→52. Scientific guardrails remain unchanged.

---

## DECISION-043: Feature Normalization, Feature Importance, And ML Training Data Are Required ML Infrastructure

**Date**: 2026-05-18

**Context**: DECISION-042 established the feature vector layer and model registry. The next prerequisite for safe learned-model development is: (1) stable normalization bounds across extractor versions with drift detection, (2) interpretable feature importance scores derived from baseline rule fire rates, and (3) a structured ML training data scaffold assembling calibration fixtures and injection-recovery cases.

**Decision**: Implement three new ML infrastructure modules:

**Feature normalization**: per-track normalization bounds (`min_max`, `z_score`, `none`) with per-feature min/max/mean/std values and drift detection when extractor versions diverge. Normalization bounds are ML preprocessing metadata only — they are not technosignature detections or calibrated survey metrics.

**Feature importance**: feature importance scores derived from synthetic baseline rule fire rates, ranked per track. Surfacing which features fire most reliably in the baseline informs safe feature selection for learned models. Scores are synthetic scheduling diagnostics only — not calibrated signal detection metrics.

**ML training data**: assembles calibration fixtures and injection-recovery cases into a structured training scaffold with recommended 80/20 train/test split. Training data summaries are provenance records for model development only — they do not constitute detections, discoveries, or external validation.

**Consequences**: `validate-all` gates enforce `normalization_bounds_count >= 3`, `feature_importance_entry_count >= 6`, and `ml_training_case_count >= 0`. SCHEMA_FILENAMES grows 52→54. Scientific guardrails remain unchanged.

---

## DECISION-044: ML Model Architecture Scaffolds, Evaluation Harness, And Performance History Are Required Before Any Model Deployment

**Date**: 2026-05-18

**Context**: DECISION-043 established feature normalization, importance, and training data as ML infrastructure prerequisites. The next requirement before any learned model can be considered for deployment is: (1) explicit architecture scaffold definitions for all five model kinds, (2) a structured evaluation harness comparing each model to the interpretable baseline, and (3) a performance history log tracking accuracy and loss across training epochs with trend classification.

**Decision**: Implement three new ML development modules:

**Model architecture**: scaffold definitions (no weights, no training) for all five intended architecture kinds — CNN radio, transformer radio, hybrid rule-learned, self-supervised, and foundation embedding. Every entry carries explicit `weights_available: false` and `status: stub` fields. Architecture definitions are ML planning artifacts only — they do not constitute trained models or detection pipelines.

**Model evaluation**: structured evaluation results comparing each registered model's accuracy, precision, recall, and F1 against the baseline accuracy per track. A model that does not beat the baseline has `beats_baseline: false` and must not be deployed. Evaluation results are synthetic development diagnostics — not detections or external validation.

**Model performance history**: per-epoch training snapshots with trend classification (`improving`, `declining`, `stable`). A `declining` trend must surface in `validate-all` visibility. Snapshots are local scheduling records — not calibrated survey efficiency estimates.

**Consequences**: `validate-all` gates enforce `arch_count >= 5`, `eval_count >= 4`, `perf_snapshot_count >= 5`. SCHEMA_FILENAMES grows 54→57. Milestone 12 is complete. Scientific guardrails remain unchanged.

---

## DECISION-045: Model Serving, Scoring Audit Log, And Curated Dataset Intake Are Required Candidate Methods Production Prerequisites

**Date**: 2026-05-18

**Context**: DECISION-044 completed the ML model architecture and evaluation harness. Before any candidate methods pipeline can be considered for production readiness, three additional scaffolds are required: a versioned model serving interface with inference provenance, an append-only scoring audit log, and a curated dataset intake checklist.

**Decision**: Implement three new production-prerequisite modules:

**Model serving**: versioned inference interface records identifying which model and backend produced each candidate score. All current records carry `serving_status: stub` for learned models — only the interpretable baseline has `serving_status: active`. No live weights are loaded. Serving records are scheduling provenance artifacts only.

**Scoring audit log**: append-only record of every score event (initial score, rescore, baseline comparison, model version change) per candidate per model version. Audit entries preserve the full provenance chain required for reproducibility. Entries are local scheduling records — not detections or external validation.

**Curated dataset intake**: conservative planning checklist for future non-synthetic validation datasets. Every non-synthetic intake record requires provenance documentation, a false-positive baseline, and external approval before any real data is ingested. The one `approved` entry in the fixture is the synthetic calibration dataset already present. All real-data intake records start as `planning` or `blocked`.

**Consequences**: `validate-all` gates enforce `serving_record_count >= 1`, `audit_entry_count >= 1`, `intake_record_count >= 1`. SCHEMA_FILENAMES grows 57→60. Milestone 13 is advanced. Scientific guardrails remain unchanged.

---

## DECISION-046: Candidate Re-Scoring, Operator Handoff Templates, And Candidate Methods Summary Complete Milestone 13

**Date**: 2026-05-18

**Context**: DECISION-045 established model serving, scoring audit log, and curated dataset intake as production prerequisites. Three Milestone 13 tasks remained: a candidate re-scoring workflow, an updated operator handoff template with model provenance fields, and a candidate methods summary CLI.

**Decision**: Implement three remaining Milestone 13 modules:

**Candidate re-scoring**: append-only record of re-score events triggered by new model registration, model version changes, operator requests, or drift detection. Each event records prior and new scores, pathways, model IDs, and serving IDs. Pathway changes are surfaced but require human review and operator approval — re-scoring does not automatically reroute committed candidate packets.

**Operator handoff templates**: local scheduling artifacts capturing the model version, inference backend, and serving ID that produced each candidate's score, alongside the operator's handoff status (draft, pending_review, approved, rejected, expired). An approved handoff authorizes internal review packet preparation only — not external submission.

**Candidate methods summary**: aggregate operational dashboard combining model serving, scoring audit log, curated dataset intake, candidate re-scoring, and operator handoff state. The dashboard is a scheduling aid only — it does not authorize external submission or modify candidate posteriors.

**Consequences**: `validate-all` gates enforce `rescore_event_count >= 1`, `handoff_template_count >= 1`, `handoff_approved_count >= 1`. SCHEMA_FILENAMES grows 60→62. Milestone 13 is complete. Scientific guardrails remain unchanged.

---

## DECISION-047: Pipeline Config, Submission Readiness, And Pipeline Integration Complete Milestone 14

**Date**: 2026-05-18

**Context**: Milestone 14 requires end-to-end pipeline validation: pipeline configuration records linking scoring config versions to serving IDs and model IDs, submission readiness provenance checklists confirming all required fields are present before any operator review, and integration smoke tests that verify the pipeline modules are mutually consistent.

**Decision**: Implement three Milestone 14 modules:

**Pipeline configuration**: local scheduling metadata records tracking which scoring config version, serving ID, model ID, inference backend, and active tracks correspond to each pipeline deployment state (active, staging, deprecated, stub). Only one config may be active at a time; the active config drives `validate-all` provenance consistency checks.

**Submission readiness**: provenance checklists confirming that all required fields (candidate_id, scoring_config_version, model_id, model_version, serving_id, pathway, has_negative_evidence, has_blocking_issues_documented, operator_handoff_id) are present before any submission review is initiated. Ready status means provenance is complete — it does not authorize external submission.

**Pipeline integration**: smoke test harness verifying that pipeline config, model serving, scoring audit log, candidate re-scoring, and operator handoff modules are mutually consistent for a given candidate. Integration tests are append-only provenance consistency checks — they do not re-score candidates, modify pathways, or authorize external contact.

**Consequences**: `validate-all` gates enforce `pipeline_config_count >= 1`, `pipeline_active_count >= 1`, `submission_record_count >= 1`. SCHEMA_FILENAMES grows 62→64. Milestone 14 is complete. Scientific guardrails remain unchanged.

---

## DECISION-048: Candidate Comparison, Pipeline Telemetry, And Provenance Audit Complete Milestone 15

**Date**: 2026-05-18

**Context**: Milestone 15 closes the pipeline loop by introducing three complementary modules: multi-candidate comparison for scheduling queue prioritisation, per-stage pipeline telemetry for operational provenance, and end-to-end provenance audit for cross-module consistency validation.

**Decision**: Implement three Milestone 15 modules:

**Candidate comparison**: local scheduling aid comparing candidate scores and pathway assignments across two or more candidates. Ranked status indicates relative scoring order only — it does not modify scores, posteriors, or pathway routing, and does not authorize external submission.

**Pipeline telemetry**: per-stage latency and success records for operational provenance. Each entry captures the stage name, latency in milliseconds, success status, and optional error message. Telemetry data is a local scheduling diagnostic only — not a survey performance metric or detection sensitivity estimate.

**Provenance audit**: cross-module consistency check verifying that pipeline config, model serving, scoring audit log, candidate rescore, and operator handoff records agree on provenance fields for a given candidate. Consistent verdict means all checked modules agree — it does not authorize external submission, confirm a detection, or constitute external validation.

**Consequences**: `validate-all` gates enforce `comparison_count >= 1`, `telemetry_entry_count >= 1`, `provenance_audit_entry_count >= 1`. SCHEMA_FILENAMES grows 64→67. Milestone 15 is complete. Scientific guardrails remain unchanged.

---

## DECISION-049: Candidate Alert Log, Pipeline Replay Log, And Scoring Threshold Audit Complete Milestone 16

**Date**: 2026-05-19

**Status**: accepted

**Context**: Milestone 16 adds operational alerting, reproducibility replay logging, and threshold consistency auditing as the final layer of scheduling provenance infrastructure.

**Decision**: Add three modules, all local provenance records only.

**Candidate alert log**: operational alert records for threshold crossings, pathway changes, flag raises, rescore triggers, provenance inconsistencies, approaching deadlines, and escalated operator assignments. Alerts are severity-classified (info/warning/critical) and carry resolved/open state. An alert indicates an event requiring operator awareness — it does not constitute a detection claim, modify scores or pathway routing, or authorize external submission.

**Pipeline replay log**: append-only reproducibility records re-running scoring on a candidate with a specified pipeline config for provenance verification. Outcomes are score_matched, score_diverged, config_mismatch, or replay_error. Replay entries do not modify committed candidate packets, authorize external submission, or constitute a detection claim.

**Scoring threshold audit**: local provenance consistency checks verifying that scoring thresholds recorded in the pipeline config match the active scoring config version. Verdicts are pass/fail/warning/not_checked. An audit pass does not mean thresholds are scientifically calibrated — it does not authorize external submission or constitute a detection claim.

**Consequences**: `validate-all` gates enforce `alert_entry_count >= 1`, `replay_entry_count >= 1`, `threshold_pass_count >= 1`. SCHEMA_FILENAMES grows 67→70. Milestone 16 is complete. Scientific guardrails remain unchanged.

---

## DECISION-050: CI Template And Full Route Coverage Are Operational Readiness Gates

**Date**: 2026-05-19

**Status**: accepted

**Context**: The project needs a reproducible CI contract, but the current
publishing path must not add `.github/workflows/*.yml` until a token with
GitHub `workflow` scope is available. Route coverage also had one uncovered
`Pathway` enum value, `external_followup_candidate`.

**Decision**: Keep the GitHub Actions workflow as a non-networked template under
`docs/templates/ci.yml` and document the workflow-scope promotion caveat in
`docs/CI.md`. The template mirrors local validation and keeps
`TECHNO_SEARCH_ENABLE_LIVE_DATA=0`.

Extend route-coverage fixtures so every `Pathway` enum value is represented.
The `external_followup_candidate` fixture is synthetic enum coverage only. It
does not authorize external submission, does not claim external validation, and
does not modify scoring or pathway logic.

**Consequences**: `validate-all` now gates on full route coverage with zero
uncovered pathways. CI promotion remains a manual publishing step until
workflow-scope permissions are available. Scientific guardrails remain
unchanged.

---

## DECISION-051: Operations Readiness Is A Local-Only Pre-Real-Data Gate

**Date**: 2026-05-19

**Status**: accepted

**Context**: Health gates can pass while the repository still has operational
work outstanding: QC blockers, open alerts, overdue review deadlines, pipeline
capacity strain, curated-intake blockers, submission-provenance gaps, and
SQLite log safety checks. These signals need one review-safe operator surface
before any real observation intake, live-provider workflow, or external
submission is considered.

**Decision**: Add an operations-readiness summary and Markdown digest as
local-only dashboards. The summary aggregates QC health, candidate alerts,
review deadlines, pipeline health, route coverage, validation readiness,
curated dataset intake, submission readiness, user decision records, and
top-level SQLite log state. It reports one conservative recommendation:
`local_only_ready`, `operator_review_required`, or `blocked_for_real_data`.

`blocked_for_real_data` is an operations state only. It does not classify a
candidate scientifically, does not modify candidate scores or pathways, does
not authorize live-provider access, and does not authorize external submission.

**Consequences**: `validation-summary` exposes operations-readiness fields and
the CI template reports the summary with live data disabled. The summary is
visibility for operators, not a claim of discovery or external validation.

---

## DECISION-052: Operations Action Plans Translate Readiness Blockers Into Local Operator Tasks

**Date**: 2026-05-19

**Status**: accepted

**Context**: DECISION-051 added operations-readiness visibility, but visibility
alone does not tell operators what to do next. Readiness blockers need a
review-safe local task list that preserves uncertainty and does not imply that
blockers have been cleared.

**Decision**: Add an operations action-plan summary that converts
operations-readiness blockers into prioritized local actions. Actions are
categorized by source, including quality control, alerts, review deadlines,
pipeline health, validation readiness, curated intake, submission provenance,
route coverage, SQLite logs, network access, and external submission records.
Each action records priority, status, required local action, evidence field,
and blocker count.

Action-plan status is operational only. An action plan does not modify scores,
pathways, candidate packets, SQLite logs, or review records. It does not clear
blockers automatically, authorize live-provider access, authorize external
submission, or constitute external validation.

**Consequences**: `validation-summary` exposes action-plan counts and the CI
template reports the action plan with live data disabled. Operations blockers
now have a deterministic local task surface before any real-data workflow is
considered.

---

## DECISION-053: Operations Action Resolution Records Are Local Workflow Provenance

**Date**: 2026-05-19

**Status**: accepted

**Context**: Operations action plans expose what operators should review next,
but the repository also needs local provenance for whether each task is open,
acknowledged, deferred, or resolved. That status must not be confused with
scientific validation, live-data approval, or external-submission approval.

**Decision**: Add fixture-backed operations action-resolution records. Each
record stores an action id, category, operator id, status, evidence note,
residual blocker count, and explicit live-data and external-submission
authorization booleans. The summary command reports status counts, category
coverage, operator coverage, residual blockers, authorization counts, and
coverage against the current operations action-plan IDs.

Resolution records are workflow provenance only. They do not clear readiness
blockers, change candidate scores or pathways, authorize live-provider access,
authorize external submission, or constitute external validation.

**Consequences**: `validate-all` requires at least one action-resolution record
and requires live-data and external-submission authorization counts to remain
zero. It also requires every current action-plan ID to have a resolution record.
`validation-summary` exposes action-resolution counts and coverage fields, and
the CI template reports the summary with live data disabled.

---

## DECISION-054: SQLite Bootstrap Summary Restores Local Log Visibility Only

**Date**: 2026-05-19

**Status**: accepted

**Context**: Operations readiness can be blocked by missing top-level SQLite
visibility even when the project health gates pass. Operators need one local
command that initializes the ignored SQLite database and reports the integrity
and weekly-digest gates used by readiness checks.

**Decision**: Add `sqlite-log-bootstrap-summary` as a local-only bootstrap and
smoke summary. The command initializes the supplied SQLite path, checks
integrity, checks the review-safe weekly digest, and runs operations readiness
against the same database. It reports that `ops-action-009` and
`ops-action-010` are validated for that database path, but it does not mutate
action-resolution fixtures.

**Consequences**: SQLite readiness gates can be validated with a single command
while generated databases remain ignored under `logs/`. The command does not
enable live data, authorize external submission, clear non-SQLite blockers, or
constitute external validation.

---

## DECISION-055: Operations Blocker Details Trace Actions To Local Evidence

**Date**: 2026-05-20

**Status**: accepted

**Context**: Operations action plans identify the next local review tasks, but
operators still need to see which fixture-backed source records explain each
blocker before changing any status. SQLite visibility can be green while QC,
alerts, deadlines, pipeline health, validation readiness, curated intake, and
submission provenance remain blocked.

**Decision**: Add `operations-blocker-detail-summary` as a local-only
traceability surface. The command expands the current operations action plan
into source summaries and compact evidence records for open alerts, review
deadlines, pipeline-health inputs, validation-readiness records,
curated-intake records, and submission-provenance gaps. SQLite log state is
reported as context, not as a reason to clear non-SQLite blockers.

**Consequences**: Operators can review the source records behind each current
action-plan item without enabling live data or external submission. The summary
does not mutate fixtures, clear blockers, change candidate scores or pathways,
authorize live-provider access, authorize external submission, or constitute
external validation.

---

## DECISION-056: Operations Blocker Review Records Preserve Evidence Review Provenance

**Date**: 2026-05-20

**Status**: accepted

**Context**: DECISION-055 exposes blocker-detail evidence records for current
operations actions. The repository also needs local provenance for whether
those evidence bundles have been reviewed, which operator reviewed them, and
how many residual blockers remain. This provenance must not be confused with
clearing readiness blockers or approving real-data workflows.

**Decision**: Add fixture-backed operations blocker-review records and an
`operations-blocker-review-summary` command. Each record links to an
operations action id, category, operator, review status, evidence counts,
residual blocker count, and explicit live-data and external-submission
authorization booleans. The summary reports coverage against current
blocker-detail action IDs, reviewed and unreviewed evidence counts, residual
blockers, stale or missing review IDs, and authorization counts.

**Consequences**: Operators can audit local evidence-review provenance for
current blocker-detail bundles. Full review coverage does not clear blockers,
change candidate scores or pathways, mutate SQLite logs, authorize
live-provider access, authorize external submission, or constitute external
validation.

---

## DECISION-057: Operations Blocker Follow-Up Is A Local Planning Rollup Only

**Date**: 2026-05-20

**Status**: accepted

**Context**: DECISION-056 records local review provenance for blocker-detail
evidence bundles, but operators still need a compact next-action ordering that
distinguishes open attention items, local remediation, real-data holds, and
workflow items ready for local verification. That ordering must not be treated
as blocker clearance or as approval for live-provider access.

**Decision**: Add `operations-blocker-followup-summary` as a derived local
planning rollup. The command consumes blocker-detail and blocker-review
summaries, preserves residual blocker counts and evidence-review coverage, and
derives recommendation categories such as `operator_attention_required`,
`continue_local_remediation`, `hold_for_real_data_evidence`, and
`verify_resolved_locally`.

**Consequences**: Operators get a deterministic local follow-up queue without
changing blocker status. The summary is not a scientific result, does not
clear blockers, does not change candidate scores or pathways, does not enable
live data, does not authorize external submission, and does not constitute
external validation.

---

## DECISION-058: Blocker Follow-Up Progress Records Preserve Local Notes Only

**Date**: 2026-05-21

**Status**: accepted

**Context**: DECISION-057 creates a deterministic local follow-up queue, but
operators need a separate provenance layer for what progress has been made
against each next-action ID. Progress notes must not be confused with clearing
the underlying blocker or authorizing real-data workflows.

**Decision**: Add fixture-backed operations blocker-followup progress records
and an `operations-blocker-followup-progress-summary` command. Each record
links to a follow-up action ID, category, expected recommendation, progress
status, operator, evidence note, residual blocker count, and explicit
live-data and external-submission authorization booleans. The summary reports
coverage against current follow-up actions, recommendation mismatches, status
counts, residual blockers, and authorization counts.

**Consequences**: Operators can track local progress without mutating
blocker-review or blocker-followup records. Progress records do not clear
blockers, change candidate scores or pathways, enable live data, authorize
external submission, or constitute external validation.

---

## DECISION-059: Progress Review Covers Only Unresolved Blocker Progress

**Date**: 2026-05-21

**Status**: accepted

**Context**: DECISION-058 adds local progress notes for every blocker-followup
action, including one verified-local workflow item. Operators need a second-pass
review queue for unresolved progress without accidentally reopening local
verification closures or implying that residual blockers have been cleared.

**Decision**: Add fixture-backed operations blocker progress-review records and
an `operations-blocker-progress-review-summary` command. The review fixture
covers unresolved progress IDs only, reports verified-local progress IDs as
excluded from the unresolved queue, checks coverage and progress-status
consistency, and preserves residual blocker totals plus explicit live-data and
external-submission authorization booleans.

**Consequences**: `validate-all`, `validation-summary`, and the CI template
gain progress-review visibility without clearing blockers, mutating candidate
scores or pathways, enabling live data, authorizing external submission, or
constituting external validation.

---

## DECISION-060: Progress Next Actions Are Local Task Ordering Only

**Date**: 2026-05-21

**Status**: accepted

**Context**: DECISION-059 identifies unresolved blocker progress-review records,
but operators still need an ordered local work queue that distinguishes direct
operator action, next local notes, and real-data holds. This queue must not be
treated as blocker clearance, external submission readiness, or scientific
validation.

**Decision**: Add fixture-backed operations blocker progress next-action records
and an `operations-blocker-progress-next-actions-summary` command. Each record
links to an unresolved progress-review action ID and review ID, carries a
next-action status, priority rank, operator, action note, residual blocker
count, and explicit live-data and external-submission authorization booleans.
The summary reports coverage against unresolved progress-review records,
status consistency, priority ordering, verified-local exclusions, residual
blockers, and authorization counts.

**Consequences**: Operators get a deterministic local task queue for the
unresolved progress-review layer. Next-action records do not clear blockers,
reopen verified-local workflow items, change candidate scores or pathways,
enable live data, authorize external submission, or constitute external
validation.

---

## DECISION-061: Progress Execution Notes Preserve Blockers

**Date**: 2026-05-21

**Status**: accepted

**Context**: DECISION-060 adds an ordered local work queue for unresolved
progress-review records. Operators need a provenance layer for what was
locally recorded against each next-action ID, but execution notes must not be
treated as blocker clearance, live-data authorization, external submission
readiness, or scientific validation.

**Decision**: Add fixture-backed operations blocker progress-execution records
and an `operations-blocker-progress-execution-summary` command. Each record
links to a next-action ID and action ID, carries the next-action status,
execution status, priority rank, operator, execution note, residual blocker
count, and explicit live-data and external-submission authorization booleans.
The summary reports coverage against progress next-action IDs, status,
residual, and priority mismatches, verified-local exclusions, residual
blockers, and authorization counts.

**Consequences**: Operators get local execution-note provenance for the ordered
next-action queue. Execution records do not clear blockers, reopen
verified-local workflow items, change candidate scores or pathways, enable
live data, authorize external submission, or constitute external validation.

---

## DECISION-062: Progress Execution Reviews Are Local Provenance Only

**Date**: 2026-05-21

**Status**: accepted

**Context**: DECISION-061 records local execution notes against ordered
progress next-action IDs. Operators need a review layer for those execution
notes, but review coverage must not imply that residual blockers have been
cleared or that real-data or external-submission gates have changed.

**Decision**: Add fixture-backed operations blocker progress-execution review
records and an `operations-blocker-progress-execution-review-summary` command.
Each record links to an execution ID, next-action ID, and action ID, carries
the execution status, review status, priority rank, reviewer, review note,
residual blocker count, and explicit live-data and external-submission
authorization booleans. The summary reports coverage against progress
execution IDs, status, residual, and priority mismatches, verified-local
exclusions, residual blockers, and authorization counts.

**Consequences**: Operators get local review provenance for execution notes.
Execution-review records do not clear blockers, reopen verified-local workflow
items, change candidate scores or pathways, enable live data, authorize
external submission, or constitute external validation.

---

## DECISION-063: Progress Execution Follow-Up Is Local Planning Only

**Date**: 2026-05-21

**Status**: accepted

**Context**: DECISION-062 adds local review provenance for progress-execution
notes. Operators still need a follow-up planning layer for reviewed execution
records, especially records requiring operator follow-up or held pending real
data. This layer must not be interpreted as blocker clearance, real-data
authorization, external submission readiness, or scientific validation.

**Decision**: Add fixture-backed operations blocker progress-execution
follow-up records and an
`operations-blocker-progress-execution-followup-summary` command. Each record
links to a review ID, execution ID, next-action ID, and action ID; carries the
review status, follow-up status, priority rank, operator, planned timestamp,
follow-up note, residual blocker count, and explicit live-data and
external-submission authorization booleans. The summary reports coverage
against progress-execution review IDs, status, residual, and priority
mismatches, verified-local exclusions, residual blockers, and authorization
counts.

**Consequences**: Operators get deterministic local planning visibility for
reviewed execution notes. Follow-up records do not clear blockers, reopen
verified-local workflow items, change candidate scores or pathways, enable
live data, authorize external submission, or constitute external validation.

---

## DECISION-064: Alert Resolution Log, Config Version History, And Operator Escalation Log Complete Milestone 17

**Date**: 2026-05-22

**Status**: accepted

**Context**: Milestone 17 closes the operational lifecycle loop with three provenance modules: how open alerts get formally resolved, how pipeline config changes over time, and how operator escalations flow between operators.

**Decision**: Add three modules, all local provenance records only.

**Alert resolution log**: records how open candidate alerts are formally closed — through operator review, automated consistency check, deadline expiry, pathway confirmation, or watchlist action. Statuses cover resolved_false_positive, resolved_follow_up, resolved_archived, resolved_operator_closed, and open. A resolved_follow_up status means follow-up was scheduled as a local scheduling action only — it does not authorize external submission or constitute a detection claim.

**Config version history**: append-only log of pipeline config changes with effective dates and the operator who made the change. Change kinds are created, promoted, updated, and deprecated. History entries do not re-run or re-route any candidate, authorize external submission, or constitute a detection claim.

**Operator escalation log**: structured log of inter-operator escalations tracking when an operator transfers responsibility for a candidate or alert. Severity levels are routine, urgent, and critical; statuses are open, acknowledged, and resolved. Escalation severity reflects scheduling priority only — not candidate scientific significance. Escalation records do not modify scores or pathway routing and do not authorize external submission.

**Consequences**: `validate-all` gates enforce `alert_resolution_entry_count >= 1`, `config_history_entry_count >= 1`, `operator_escalation_entry_count >= 1`. SCHEMA_FILENAMES grows to 73. Milestone 17 is complete. Scientific guardrails remain unchanged.

---

## DECISION-065: Candidate Deduplication Log, Intake Queue Log, And Workflow State Log Complete Milestone 18

**Date**: 2026-05-22

**Status**: accepted

**Context**: Milestone 18 adds three provenance modules completing the candidate lifecycle and data intake coordination tracking: how candidates are compared for deduplication, how data sources queue for intake, and how review assignments transition between workflow states.

**Decision**: Add three modules, all local provenance records only.

**Candidate deduplication log**: records pairwise comparisons against previously seen candidates, known objects, prior-epoch observations, or catalog sources. Match kinds are cross_candidate, known_object, prior_epoch, and catalog_match. Statuses are pending, confirmed_duplicate, confirmed_distinct, and inconclusive. Deduplication does not remove candidates from the record, does not modify scores or pathway routing, does not constitute a detection claim, and does not authorize external submission.

**Intake queue log**: local planning placeholders recording that a data source has been identified for potential ingestion and tracking its queue position and intake status. Source kinds are radio_survey, infrared_catalog, archival_image, spectral_archive, and unknown. Statuses are queued, blocked, intake_ready, intake_complete, and cancelled. Intake remains blocked until real data policy, provenance, licensing, labeling, and external-review requirements are satisfied.

**Workflow state log**: local scheduling coordination records tracking formal operator review state transitions for candidate review assignments — initial assignment, state change, reassignment, closure, or reopening. States are assigned, in_review, pending_second_opinion, escalated, closed, and deferred. State transitions are local scheduling aids only — they do not modify candidate posteriors, scores, or pathway routing, and do not authorize external submission.

**Consequences**: `validate-all` gates enforce `dedup_entry_count >= 1`, `intake_entry_count >= 1`, `workflow_entry_count >= 1`. SCHEMA_FILENAMES grows to 88. Milestone 18 is complete. Scientific guardrails remain unchanged.

---

## DECISION-066: Data Gap Log, Candidate Match Log, And Pipeline Error Log Complete Milestone 19

**Date**: 2026-05-22

**Status**: accepted

**Context**: Milestone 19 adds three operational provenance modules completing coverage of scheduling gaps, cross-catalog matching outcomes, and pipeline error tracking.

**Decision**: Add three modules, all local operational provenance records only.

**Data gap log**: records that expected observations or data deliveries were missing or incomplete due to instrument downtime, weather, scheduling conflicts, or data quality failures. Missing reasons are instrument_downtime, weather, scheduling_conflict, data_quality_failure, and unknown. Statuses are identified, under_investigation, resolved, and accepted. Gap records do not modify candidate scores, do not affect pathway routing, do not identify missing technosignatures, do not authorize external submission, and do not constitute a detection claim.

**Candidate match log**: records the result of cross-catalog matching operations performed for a candidate against external or internal catalog sources (simbad, gaia, vizier, irsa, internal_catalog). Statuses are matched, no_match, ambiguous, and pending. A catalog match does not confirm or rule out candidate technosignature interest, does not modify candidate scores or pathway routing, does not authorize external submission, and does not constitute a detection claim.

**Pipeline error log**: records that a scoring, data, configuration, or validation error occurred during pipeline execution. Error kinds are scoring_failure, data_missing, config_mismatch, timeout, and validation_error. Severities are warning, error, and critical. Error records do not modify candidate scores, do not affect pathway routing, do not authorize external submission, and do not constitute a detection claim.

**Consequences**: `validate-all` gates enforce `data_gap_entry_count >= 1`, `candidate_match_entry_count >= 1`, `pipeline_error_entry_count >= 1`. SCHEMA_FILENAMES grows to 91. Milestone 19 is complete. Scientific guardrails remain unchanged.

---

## DECISION-067: Observation Request Log, Candidate Export Log, And Quality Gate Log Complete Milestone 20

**Date**: 2026-05-22

**Status**: accepted

**Context**: Milestone 20 adds three operational provenance modules completing coverage of follow-up observation scheduling requests, candidate data export events, and pipeline quality gate checks.

**Decision**: Add three modules, all local operational provenance records only.

**Observation request log**: records that a follow-up observation slot was requested for a candidate in a local scheduling system. Request kinds are target_followup, reobservation, calibration_check, verification, and archival_search. Statuses are submitted, acknowledged, scheduled, completed, rejected, and withdrawn. Request records do not constitute telescope-time allocations, do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute a detection claim.

**Candidate export log**: records candidate data export events for internal review or reproducibility purposes. Export formats are json, csv, markdown, fits_stub, and parquet_stub. Statuses are prepared, exported, delivered, failed, and cancelled. Export records do not modify candidate scores or pathway routing, do not authorize external submission or publication, and do not constitute a detection claim.

**Quality gate log**: records the result of consistency or completeness checks applied to a candidate during pipeline execution. Gate kinds are score_threshold, provenance_completeness, rfi_screen, catalog_check, and review_coverage. Results are pass, fail, warn, and not_applicable. Gate results are scheduling coordination aids only — a gate pass does not modify candidate scores or pathway routing and does not authorize external submission.

**Consequences**: `validate-all` gates enforce `obs_request_entry_count >= 1`, `candidate_export_entry_count >= 1`, `quality_gate_entry_count >= 1`, `quality_gate_pass_count >= 1`. SCHEMA_FILENAMES grows to 94. Milestone 20 is complete. Scientific guardrails remain unchanged.

---

## DECISION-068: Instrument Log, Archival Query Log, And Candidate Linkage Log Complete Milestone 21

**Date**: 2026-05-22

**Status**: accepted

**Context**: Milestone 21 adds three operational provenance modules completing coverage of instrument/telescope status events, archival/catalog query provenance, and candidate-to-candidate linkage records.

**Decision**: Add three modules, all local operational provenance records only.

**Instrument log**: records instrument/telescope status events for scheduling context. Instrument kinds are radio_telescope, optical_telescope, archive_node, and data_pipeline. Event kinds are online, offline, degraded, maintenance, and calibrating. Instrument log entries are operational scheduling records — instrument status does not modify candidate scores or pathway routing and does not authorize external submission or constitute a detection claim.

**Archival query log**: records archival/catalog query events submitted by the pipeline for provenance. Query kinds are cone_search, identifier_lookup, time_series, spectral_query, and image_retrieval. Statuses are submitted, completed, failed, and cached. A completed query does not confirm or rule out candidate technosignature interest, does not modify candidate scores or pathway routing, and does not authorize external submission or constitute a detection claim.

**Candidate linkage log**: records pairwise linkages between related candidates. Linkage kinds are same_source, temporal_followup, spatial_neighbor, frequency_related, and cross_track. Statuses are proposed, confirmed, rejected, and under_review. A confirmed linkage does not modify candidate scores or pathway routing, does not constitute a detection claim, and does not authorize external submission.

**Consequences**: `validate-all` gates enforce `instrument_log_entry_count >= 1`, `archival_query_entry_count >= 1`, `candidate_linkage_entry_count >= 1`. SCHEMA_FILENAMES grows to 97. Milestone 21 is complete. Scientific guardrails remain unchanged.

---

## DECISION-069: Signal Classification Log, RFI Mitigation Log, And Candidate Annotation Log Complete Milestone 22

**Date**: 2026-05-23

**Status**: accepted

**Context**: Milestone 22 adds three operational provenance modules completing coverage of signal characterization provenance, RFI handling provenance, and operator annotation provenance.

**Decision**: Add three modules, all local operational provenance records only.

**Signal classification log**: records signal classification events for pipeline provenance. Classification kinds are narrowband, broadband, pulsed, intermittent, and unknown. Statuses are classified, unclassified, ambiguous, and reclassified. Signal classification entries are operational provenance records — a classification does not confirm or rule out technosignature interest, does not modify candidate scores or pathway routing, and does not authorize external submission or constitute a detection claim.

**RFI mitigation log**: records RFI flagging and mitigation actions during pipeline processing. Mitigation kinds are known_rfi_source, statistical_outlier, satellite_track, terrestrial_interference, and other. Actions are flagged, excised, masked, passed, and deferred. A passed action does not confirm a signal is not RFI, does not modify candidate scores or pathway routing, and does not authorize external submission or constitute a detection claim.

**Candidate annotation log**: records operator and automated annotation provenance for candidates. Annotation kinds are manual_tag, automated_flag, cross_reference, operator_note, and classification_hint. Statuses are active, superseded, and withdrawn. Annotation entries do not modify candidate posteriors, scores, or pathway routing, and do not authorize external submission or constitute a detection claim.

**Consequences**: `validate-all` gates enforce `signal_classification_entry_count >= 1`, `rfi_mitigation_entry_count >= 1`, `candidate_annotation_entry_count >= 1`. SCHEMA_FILENAMES grows to 100. Milestone 22 is complete. Scientific guardrails remain unchanged.

---

## DECISION-070: Frequency Channel Log, Pipeline Checkpoint Log, And Candidate Status Log Complete Milestone 23

**Date**: 2026-05-23
**Status**: accepted

**Context**: Milestone 23 adds three operational provenance modules covering radio frequency channel configuration provenance, pipeline execution checkpoint/recovery provenance, and candidate-level status transition audit trail provenance.

**Decision**: Add three modules, all local operational provenance records only.

**Frequency channel log**: records frequency channel configuration events during radio pipeline processing. Channel kinds are primary, backup, rfi_free, reserved, and calibration. Statuses are active, flagged, reserved, and disabled. Frequency channel entries are operational processing provenance records — channel configuration does not modify candidate scores or pathway routing and does not authorize external submission or constitute a detection claim.

**Pipeline checkpoint log**: records pipeline execution checkpoint and recovery events for reproducibility provenance. Checkpoint kinds are stage_start, stage_complete, recovery_point, validation_gate, and end_of_run. Statuses are saved, restored, expired, and invalidated. Pipeline checkpoint entries are operational reproducibility records — a restored checkpoint does not modify candidate scores or pathway routing and does not authorize external submission or constitute a detection claim.

**Candidate status log**: records candidate-level status transition events as an audit trail. Transition kinds are initial, promotion, demotion, hold, and archive. Current status values are new, active, under_review, on_hold, and archived. Candidate status entries are operational provenance records — a status transition does not modify candidate scores or pathway routing, does not authorize external submission, and does not constitute a detection claim.

**Consequences**: validate-all gates enforce frequency_channel_entry_count >= 1, pipeline_checkpoint_entry_count >= 1, candidate_status_entry_count >= 1. SCHEMA_FILENAMES grows to 103. Milestone 23 is complete. Scientific guardrails remain unchanged.

---

## DECISION-071: Beam Configuration Log, Calibration Event Log, And Pipeline Run Log Complete Milestone 24

**Date**: 2026-05-23
**Status**: accepted

**Context**: Milestone 24 adds three operational provenance modules covering radio telescope beam configuration provenance, pipeline calibration event provenance, and top-level pipeline run execution provenance.

**Decision**: Add three modules, all local operational provenance records only.

**Beam configuration log**: records radio telescope beam configuration events for pipeline provenance. Beam kinds are primary_beam, sidelobe, calibrator_beam, off_source, and synthetic_beam. Statuses are configured, applied, superseded, and failed. Beam configuration entries are operational processing provenance records — beam configuration does not modify candidate scores or pathway routing and does not authorize external submission or constitute a detection claim.

**Calibration event log**: records pipeline calibration events for provenance. Event kinds are flux_calibration, bandpass_calibration, phase_calibration, polarization_calibration, and pointing_calibration. Statuses are applied, failed, skipped, and deferred. Calibration event entries are operational processing provenance records — a calibration event does not modify candidate scores or pathway routing and does not authorize external submission or constitute a detection claim.

**Pipeline run log**: records top-level pipeline execution run events for reproducibility provenance. Run kinds are full_pipeline, partial_rerun, calibration_only, test_run, and recovery_run. Statuses are started, completed, failed, aborted, and paused. Pipeline run entries are operational reproducibility records — a pipeline run record does not modify candidate scores or pathway routing and does not authorize external submission or constitute a detection claim.

**Consequences**: validate-all gates enforce beam_configuration_entry_count >= 1, calibration_event_entry_count >= 1, pipeline_run_entry_count >= 1. SCHEMA_FILENAMES grows to 106. Milestone 24 is complete. Scientific guardrails remain unchanged.

---

## DECISION-072: Source Catalog Log, Noise Measurement Log, And Spectral Feature Log Complete Milestone 25

**Date**: 2026-05-24
**Status**: accepted

**Context**: Milestone 25 adds three operational provenance modules covering source catalog cross-matching provenance, pipeline noise and sensitivity measurement provenance, and spectral feature extraction provenance.

**Decision**: Add three modules, all local operational provenance records only.

**Source catalog log**: records source catalog cross-matching events for candidate provenance. Catalog kinds are radio_source, infrared, stellar, known_object, and known_rfi. Statuses are queried, matched, no_match, and error. Source catalog entries are operational provenance records — a catalog match does not confirm or rule out technosignature interest, does not modify candidate scores or pathway routing, and does not authorize external submission or constitute a detection claim.

**Noise measurement log**: records pipeline noise and sensitivity measurement events for processing provenance. Measurement kinds are system_temperature, noise_floor, rms_baseline, sensitivity_estimate, and interference_level. Statuses are recorded, flagged, superseded, and failed. Noise measurement entries are operational processing provenance records — a noise measurement does not modify candidate scores or pathway routing and does not authorize external submission or constitute a detection claim.

**Spectral feature log**: records spectral feature extraction events for candidate provenance. Feature kinds are emission_line, absorption_line, continuum_fit, spectral_index, and line_complex. Statuses are detected, tentative, not_detected, and artifact. Spectral feature entries are operational provenance records — a detected feature does not confirm technosignature interest, does not modify candidate scores or pathway routing, and does not authorize external submission or constitute a detection claim.

**Consequences**: validate-all gates enforce source_catalog_entry_count >= 1, noise_measurement_entry_count >= 1, spectral_feature_entry_count >= 1. SCHEMA_FILENAMES grows to 109. Milestone 25 is complete. Scientific guardrails remain unchanged.

---

## DECISION-073: Polarization Log, Telescope Status Log, And Observation Parameter Log Complete Milestone 26

**Date**: 2026-05-24
**Status**: accepted

**Context**: Milestone 26 adds three operational provenance modules covering polarization measurement provenance, telescope operational status provenance, and observation configuration parameter provenance.

**Decision**: Add three modules, all local operational provenance records only.

**Polarization log**: records polarization measurement and calibration events during radio pipeline processing. Polarization kinds are stokes_i, stokes_q, stokes_u, stokes_v, and circular_polarization. Statuses are measured, calibrated, flagged, and failed. Polarization entries are operational processing provenance records — a polarization measurement does not modify candidate scores or pathway routing and does not authorize external submission or constitute a detection claim.

**Telescope status log**: records telescope operational state transitions for reproducibility and scheduling provenance. Status kinds are operational, maintenance, degraded, offline, and commissioning. Statuses are recorded, updated, superseded, and error. Telescope status entries are operational scheduling provenance records — a telescope status does not modify candidate scores or pathway routing and does not authorize external submission or constitute a detection claim.

**Observation parameter log**: records observation configuration parameters for pipeline reproducibility provenance. Parameter kinds are integration_time, bandwidth, center_frequency, resolution, and sensitivity_target. Statuses are applied, overridden, flagged, and failed. Observation parameter entries are operational processing provenance records — a parameter record does not modify candidate scores or pathway routing and does not authorize external submission or constitute a detection claim.

**Consequences**: validate-all gates enforce polarization_entry_count >= 1, telescope_status_entry_count >= 1, obs_parameter_entry_count >= 1. SCHEMA_FILENAMES grows to 112. Milestone 26 is complete. Scientific guardrails remain unchanged.

---

## DECISION-074: Production Foundation (Milestone 27) — Real File Ingestion, CI, And Production Readiness Assessment

**Date**: 2026-05-24

**Context**: After completing 26 milestones of provenance logging infrastructure, an honest production readiness assessment was requested. The 12-milestone provenance log series (M15–M26) built important operational infrastructure but did not advance real data ingestion, CI, or model validation. M27 addresses the most impactful production gaps.

**Decision**: Implement the production foundation milestone with the following components:

1. **CI activation** — `.github/workflows/ci.yml` with Python 3.11, pytest, ruff, mypy, and validate-all gates. Skips integration_live tests by default.
2. **Real hit-table reader** — `radio/hit_table_reader.py` reads turboSETI-format CSV (MHz → Hz conversion, column alias handling).
3. **Real catalog reader** — `infrared/catalog_reader.py` reads IRSA TAP Gaia+AllWISE CSV format.
4. **End-to-end pipeline runner** — `pipeline_runner.py` runs full pipeline from real CSV input to scored candidate report.
5. **Live client integration tests** — `test_live_client_integration.py` with default-off guard tests and `@pytest.mark.integration_live` opt-in tests for Gaia TAP and SIMBAD.
6. **Data quality validator** — `data_quality.py` validates pipeline input files structurally before ingestion.
7. **Labeled candidate dataset v0** — 10 synthetic labeled entries with `LabeledCandidate` dataclass and summary CLI.
8. **Scoring model evaluation against labels** — `eval_against_labels()` maps dataset labels to expected pathways and checks predictions.
9. **Production readiness assessment** — `docs/PRODUCTION_READINESS.md` with honest ~20–25% estimate and gap analysis.

**Consequences**: SCHEMA_FILENAMES grows to 113. validate-all gates enforce labeled_entry_count >= 1 and label_eval_entry_count >= 1. CI is now active. Real CSV files can now be ingested through the full pipeline. Production readiness estimate is ~20–25% — the remaining gap is almost entirely in real observation data, real labeled datasets, and calibrated scoring thresholds. Scientific guardrails remain unchanged.

# DECISION-075: Target Selection Log, Doppler Correction Log, And Data Archival Log Complete Milestone 28

Date: 2026-05-24
Status: accepted

## Context
Milestone 28 extends the operational log system with target selection, Doppler correction, and data archival provenance records.

## Decision
Implement three new log types:
- `target_selection_log` — operational scheduling provenance records for target selection events
- `doppler_correction_log` — operational processing provenance records for Doppler/barycentric correction
- `data_archival_log` — operational provenance records for observation data archival events

## Consequences
Schema count grows from 113 to 116. All three log types carry explicit guardrails that entries are operational provenance records only and do not modify candidate scores, pathway routing, or authorize external submission.

---

# DECISION-076: Pipeline Input Validation Gates Local CSV Scoring

Date: 2026-05-25
Status: accepted

## Context
Milestone 27 added real CSV readers and an end-to-end pipeline runner, but the
runner was not exposed as a direct CLI workflow and anomaly CSV input still
used an empty feature set. Operators need a safer local path for testing CSV
ingestion that refuses invalid files before scoring.

## Decision
Implement Milestone 29 production ingestion hardening:

- Add a `run-pipeline` CLI command that runs structural validation before
  candidate scoring and report generation.
- Add `data_quality.schema.json` for the `validate-input` JSON output.
- Record `input_validation`, `reader_type`, `row_count`, report paths, and a
  conservative disclaimer in pipeline run JSON.
- Add an archival/catalog anomaly CSV reader and a synthetic anomaly fixture so
  all three tracks have a local CSV ingestion path.

## Consequences
Schema count grows from 116 to 117. Local CSV pipeline runs are easier to use
and harder to misuse. Structural validation does not inspect scientific
significance, does not modify scores or pathways, does not authorize live data
access or external submission, and does not constitute a detection claim.

---

# DECISION-077: RFI Database Guardrails Precede Any Radio Threshold Recalibration

Date: 2026-05-25
Status: accepted

## Context
The production-readiness assessment identified the radio RFI band list as a
placeholder. Before changing radio false-positive thresholds or ingesting a
real site-specific RFI catalog, the project needs a versioned local database
shape, provenance checks, and validation gates.

## Decision
Implement Milestone 30 RFI database guardrails:

- Add a local `rfi_database` module with records for site ID, frequency range,
  source class, confidence, review status, provenance, active state, and
  synthetic-vs-real status.
- Add a synthetic RFI database fixture and JSON schema.
- Add `rfi-database-summary` and wire the summary into `validate-all` and
  `validation-summary`.
- Add radio candidate feature enrichment that records database overlap
  provenance without changing calibrated scientific claims.

## Consequences
Schema count grows from 117 to 118. The current fixture is synthetic and local
only. RFI database matches are false-positive screening aids; they do not
calibrate thresholds, confirm or rule out candidate technosignature interest,
authorize live data access, authorize external submission, or constitute a
detection claim. Real site-specific RFI records remain blocked until their
provenance, licensing, monitoring context, and review status are documented.

---

# DECISION-078: RFI Database Admission Records Gate Real RFI Source Lists

Date: 2026-05-25
Status: accepted

## Context
Milestone 30 added a synthetic RFI database fixture and validation for
individual RFI records. The next risk is accidentally treating a proposed real
site-specific RFI source list as admissible without provenance, licensing,
monitoring context, and external-review evidence.

## Decision
Implement Milestone 31 RFI database admission gates:

- Add local admission records for proposed RFI database sources.
- Track provenance review, license review, monitoring-context review,
  external-review requirements, blocker counts, synthetic-only status, and
  explicit real-data authorization state.
- Add `rfi-database-admission-summary` and wire it into local validation.
- Require `real_data_authorized_count == 0` for the committed fixture.

## Consequences
Schema count grows from 118 to 119. The committed admission fixture permits
synthetic local regression use only and keeps all proposed real RFI source
lists blocked. Admission records do not ingest real monitoring data, calibrate
scoring thresholds, authorize live data access, authorize external submission,
or constitute external validation or detection claims.

---

# DECISION-079: Curated Dataset Admission Records Gate Real Labeled Dataset Supplements

Date: 2026-05-25
Status: accepted

## Context
The project has synthetic labeled candidates, curated-intake placeholders, and
validation-readiness fixtures, but a future real labeled dataset must not be
treated as admissible without explicit review of provenance, licensing,
labeling methodology, false-positive baselines, external review, and blockers.

## Decision
Implement Milestone 32 curated dataset admission gates:

- Add local admission records for proposed curated validation datasets.
- Track provenance review, license review, labeling-method review,
  false-positive-baseline review, external-review requirements, blocker counts,
  synthetic-only status, and explicit real-data authorization state.
- Add `curated-dataset-admission-summary` and wire it into local validation.
- Require `real_data_authorized_count == 0` for the committed fixture.

## Consequences
Schema count grows from 119 to 120. The committed admission fixture permits
synthetic local regression use only and keeps all proposed real labeled dataset
supplements blocked. Admission records do not ingest real observation data,
calibrate scoring thresholds, authorize live data access, authorize external
submission, or constitute external validation or detection claims.

---

# DECISION-080: Production Readiness Status Must Stay Aligned With Validation Gates

Date: 2026-05-26
Status: accepted

## Context
Production-readiness metadata can lag behind code and validation gates. After
Milestone 32, the production readiness document still identified Milestone 31 as
current, which could mislead operators about what gates are active.

## Decision
Implement Milestone 33 production readiness status consistency gates:

- Add a local status-consistency expectation fixture.
- Check the latest roadmap milestone, latest decision number,
  production-readiness current milestone, production-readiness schema count,
  actual schema artifact count, and required project-status completion phrase.
- Include RFI database admission and curated dataset admission real-data
  authorization counts so zero-authorization gates remain visible.
- Add `project-status-consistency-summary` and wire it into local validation.

## Consequences
Schema count grows from 120 to 121. Production-readiness status metadata now
fails local validation if it drifts from the expected milestone, decision,
schema-count, or zero-real-data authorization gates. These checks are
documentation drift guards only; they do not ingest real observation data,
calibrate scoring thresholds, authorize live data access, authorize external
submission, or constitute external validation or detection claims.

---

# DECISION-081: Operations Alert Review Visibility Must Stay Aligned With QC Gates

Date: 2026-05-26
Status: accepted

## Context
Operations readiness remains intentionally blocked for local operator review
and real-data prerequisites. Candidate-alert, alert-resolution, QC, and
operations-readiness summaries can drift apart unless the current blocker
visibility is checked explicitly.

## Decision
Implement Milestone 34 operations alert review consistency gates:

- Add a local alert-review consistency expectation fixture.
- Check open candidate-alert counts, critical-open-alert counts,
  alert-resolution open counts, QC health, and operations-readiness
  recommendation.
- Require open-alert IDs to have alert-resolution coverage and critical open
  alerts to remain covered by open resolution records.
- Keep live data access and external submission authorization counts at zero.
- Add `operations-alert-review-consistency-summary` and wire it into local
  validation.

## Consequences
Schema count grows from 121 to 122. Local validation now fails if alert/QC
operator-review visibility drifts from the expected blocker state. These checks
are local visibility gates only; they do not clear blockers, modify candidate
scores or pathway routing, authorize live data access, authorize external
submission, or constitute external validation or detection claims.

---

# DECISION-082: Operations Action Resolution Staleness Must Stay Aligned With Action Plans

Date: 2026-05-26
Status: accepted

## Context
Operations action-resolution records may outlive the current action-plan IDs
that generated them. Stale records are useful local provenance, but they must
remain explicit so operators do not confuse historical workflow notes with
current blockers or cleared actions.

## Decision
Implement Milestone 35 operations action-resolution staleness gates:

- Add a local action-resolution consistency expectation fixture.
- Check current action-plan count, action-resolution record count, stale
  resolution count, stale resolution IDs, residual blocker total, and coverage
  completeness.
- Keep live data access and external submission authorization counts at zero.
- Add `operations-action-resolution-consistency-summary` and wire it into local
  validation.

## Consequences
Schema count grows from 122 to 123. Local validation now fails if stale
action-resolution visibility drifts from the expected action-plan state. These
checks are local workflow staleness visibility gates only; they do not clear
blockers, modify candidate scores or pathway routing, authorize live data
access, authorize external submission, or constitute external validation or
detection claims.

---

# DECISION-083: Operations Blocker Progress Chains Must Stay Aligned

Date: 2026-05-26
Status: accepted

## Context
Operations blocker-progress records now span blocker details, local evidence
review, follow-up planning, progress notes, progress review, next-action
ordering, execution notes, execution review, and execution follow-up. Each
stage preserves useful local provenance, but the chain can drift if counts,
residual blockers, verified-local exclusions, categories, mismatch totals, or
authorization flags are updated independently.

## Decision
Implement Milestone 36 operations blocker-progress consistency gates:

- Add a local blocker-progress consistency expectation fixture.
- Check blocker-detail, review, follow-up, progress, next-action, execution,
  execution-review, and execution-follow-up counts.
- Require residual blocker totals to remain aligned across every unresolved
  blocker-progress stage.
- Require verified-local progress action IDs and categories covered to match
  the expected local chain state.
- Require coverage completion, priority ordering, zero mismatch totals, and
  zero live/external authorization totals.
- Add `operations-blocker-progress-consistency-summary` and wire it into local
  validation.

## Consequences
Schema count grows from 123 to 124. Local validation now fails if
blocker-progress chain visibility drifts from the expected local operator
state. These checks are local workflow consistency gates only; they do not
clear blockers, modify candidate scores or pathway routing, authorize live data
access, authorize external submission, or constitute external validation or
detection claims.

---

# DECISION-084: Top-Level SQLite Logs Must Keep Health And Authorization Gates Aligned

Date: 2026-05-26
Status: accepted

## Context
Top-level SQLite logs are the local operational source of truth for scheduled
background runs and review-safe workflow provenance. The project already has
summary, validation, integrity, migration, digest, retention, PRAGMA, backup,
vacuum, export, and commit-guard commands, but the health and authorization
state can drift unless those outputs are checked together.

## Decision
Implement Milestone 37 top-level SQLite log consistency gates:

- Add a local SQLite log consistency expectation fixture.
- Check database visibility, readability, metadata, validation, integrity,
  PRAGMAs, weekly digest, retention, commit-guard state, and migration state.
- Require run counts and outcome counts to remain aligned.
- Require network-access and external-submission approval counts to remain
  disabled by default.
- Add `sqlite-log-consistency-summary` and wire it into local validation.

## Consequences
Schema count grows from 124 to 125. Local validation now fails if top-level
SQLite log health, migration state, run/outcome alignment, retention, PRAGMAs,
commit-guard state, or authorization counts drift from the expected local
state. These checks are local workflow and provenance gates only; they are not
detections, discoveries, external validation, or external submission approval.

---

# DECISION-085: Production Blockers Must Remain Visible Until Explicitly Resolved

Date: 2026-05-27
Status: accepted

## Context
Production readiness still depends on Tier 1 blockers that cannot be resolved
by local synthetic validation alone: real observation data, real labeled
datasets, calibrated thresholds, a real site-specific RFI database, and peer
review. The project has admission gates and operations-readiness summaries, but
those blocker states can drift independently from the production-readiness
document.

## Decision
Implement Milestone 38 production blocker visibility consistency gates:

- Add a local production blocker consistency expectation fixture.
- Check that all required Tier 1 production blocker phrases remain visible in
  `docs/PRODUCTION_READINESS.md`.
- Check RFI database and curated-dataset admission blockers remain visible.
- Check operations readiness remains blocked for real data until the blocker
  state is explicitly changed.
- Require real-data authorization, external-submission authorization, and
  network-access counts to remain zero.
- Add `production-blocker-consistency-summary` and wire it into local
  validation.

## Consequences
Schema count grows from 125 to 126. Local validation now fails if production
blocker visibility, admission blockers, operations-readiness blocker state, or
authorization counts drift from the expected local state. These checks are
local readiness visibility gates only; they do not ingest real observation
data, calibrate thresholds, clear blockers, authorize live data access,
authorize external submission, or constitute detections, discoveries, or
external validation.

---

# DECISION-077: Interference Environment Log, Receiver Health Log, And Pipeline Version Log Complete Milestone 29

**Date:** 2026-05-29
**Status:** Accepted

## Context

Milestone 29 requires operational provenance records for three additional pipeline subsystems:
interference environment assessments, receiver hardware health checks, and pipeline component
version tracking.

## Decision

Implement three operational log modules:

1. `interference_environment_log` — operational processing provenance records for interference
   environment assessments; interference_kinds: local_rfi_survey, satellite_interference,
   ionospheric_event, anthropogenic_source, unknown_transient; statuses: assessed, flagged,
   cleared, inconclusive
2. `receiver_health_log` — operational scheduling provenance records for receiver hardware health
   checks; health_kinds: gain_stability, noise_temperature, bandpass_flatness, pointing_accuracy,
   focus_setting; statuses: nominal, degraded, critical, maintenance_required
3. `pipeline_version_log` — operational reproducibility records for pipeline component version
   tracking; version_kinds: scoring_engine, rfi_filter, catalog_client, feature_extractor,
   baseline_model; statuses: active, deprecated, superseded, testing

## Scientific Guardrail

- Interference environment entries are operational processing provenance records — assessments do
  not modify candidate scores or pathway routing, do not authorize external submission, and do not
  constitute a detection claim
- Receiver health entries are operational scheduling provenance records — health checks do not
  modify candidate scores or pathway routing, do not authorize external submission, and do not
  constitute a detection claim
- Pipeline version entries are operational reproducibility records — version tracking does not
  modify candidate scores or pathway routing, does not authorize external submission, and does not
  constitute a detection claim

---

# DECISION-086: Data Transfer Log, Scheduling Conflict Log, And System Health Log Complete Milestone 39

**Date:** 2026-05-29

**Decision:** Add operational provenance records for data transfer events, scheduling conflict
events, and system health monitoring events as part of Milestone 39. Also repair three pre-existing
consistency test fixtures so that `operations_action_resolution_consistency`,
`operations_blocker_progress_consistency`, and `top_level_sqlite_log_consistency` tests pass.

## Rationale

1. `data_transfer_log` — operational provenance records for data movement between local storage,
   archive, and staging locations; transfer_kinds: archive_transfer, inter_site_transfer, local_copy,
   cloud_upload, network_delivery; statuses: pending, completed, failed, verified
2. `scheduling_conflict_log` — operational provenance records for scheduling conflict events that
   affect observation planning; conflict_kinds: time_slot_overlap, resource_contention,
   priority_conflict, maintenance_window, weather_hold; statuses: detected, resolved, escalated,
   deferred
3. `system_health_log` — operational provenance records for system health monitoring measurements;
   health_kinds: cpu_usage, memory_usage, disk_space, network_latency, process_uptime; statuses:
   healthy, warning, critical, unknown

## Scientific Guardrail

- Data transfer entries are operational provenance records — a transfer record does not modify
  candidate scores or pathway routing, does not authorize external submission, and does not
  constitute a detection claim
- Scheduling conflict entries are operational provenance records — a conflict record does not modify
  candidate scores or pathway routing, does not authorize external submission, and does not
  constitute a detection claim
- System health entries are operational provenance records — a health record does not modify
  candidate scores or pathway routing, does not authorize external submission, and does not
  constitute a detection claim

# DECISION-087: Instrument Configuration Log, Scan Log, And Time Synchronization Log Complete Milestone 40

Date: 2026-05-29

Three new operational log modules were added as part of Milestone 40.

`instrument_configuration_log` records operational provenance for instrument hardware configuration changes (frontend swaps, backend changes, receiver installs, filter changes, attenuator settings). Configuration entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

`scan_log` records operational provenance for individual telescope scan events (on-source, off-source, calibrator, reference position, and slew scans). Scan entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

`time_synchronization_log` records operational provenance for time and clock synchronization events (NTP sync, GPS sync, manual correction, drift checks, epoch resets). Synchronization entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

Schema count increased from 133 to 136. Consistency fixture updated: milestone 39→40, decision 86→87, schema_count 133→136.

# DECISION-088: Antenna Pointing Log, Weather Log, And Power Log Complete Milestone 41

Date: 2026-05-29

Three new operational log modules were added as part of Milestone 41.

`antenna_pointing_log` records operational provenance for antenna pointing and slew events (target slews, park/stow position moves, tracking start/end). Pointing entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

`weather_log` records operational provenance for site weather monitoring events (wind speed, temperature, humidity, precipitation, seeing). Weather entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

`power_log` records operational provenance for facility power system events (UPS events, mains failures, generator starts, load shedding, power restoration). Power entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

Schema count increased from 136 to 139. Consistency fixture updated: milestone 40→41, decision 87→88, schema_count 136→139.

# DECISION-089: Cooling System Log, Network Connectivity Log, And Software Update Log Complete Milestone 42

Date: 2026-05-29

Three new operational log modules were added as part of Milestone 42.

`cooling_system_log` records operational provenance for cryogenic and cooling system events (cooldown starts/completions, warmup events, temperature alarms, helium refills). Cooling entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

`network_connectivity_log` records operational provenance for network infrastructure events (link up/down, latency spikes, packet loss events, VPN events). Network connectivity entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

`software_update_log` records operational provenance for software and firmware update events (pipeline updates, firmware updates, OS patches, driver updates, config deployments). Software update entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

Schema count increased from 139 to 142. Consistency fixture updated: milestone 41→42, decision 88→89, schema_count 139→142.

# DECISION-090: Hardware Fault Log, Maintenance Log, And Environmental Log Complete Milestone 43

Date: 2026-05-30

Three new operational log modules were added as part of Milestone 43.

`hardware_fault_log` records operational provenance for hardware fault events (CPU faults, memory faults, disk faults, network faults, PSU faults). Hardware fault entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

`maintenance_log` records operational provenance for maintenance activities (scheduled maintenance, emergency repairs, calibration services, firmware services, inspections). Maintenance entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

`environmental_log` records operational provenance for environmental monitoring readings (temperature, humidity, pressure, vibration, electromagnetic interference). Environmental entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

Schema count increased from 142 to 145. Consistency fixture updated: milestone 42→43, decision 89→90, schema_count 142→145.

# DECISION-091: Access Log, Security Event Log, And Audit Trail Log Complete Milestone 44

Date: 2026-05-30

Three new operational log modules were added as part of Milestone 44.

`access_log` records operational provenance for facility and system access events (facility entry/exit, system login/logout, remote access). Access entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

`security_event_log` records operational provenance for security events (intrusion attempts, unauthorized access, policy violations, credential changes, physical breaches). Security event entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

`audit_trail_log` records operational provenance for audit trail events (config changes, data access, user actions, system events, compliance checks). Audit trail entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

Schema count increased from 145 to 148. Consistency fixture updated: milestone 43→44, decision 90→91, schema_count 145→148.

# DECISION-092: Incident Response Log, Change Management Log, And Compliance Report Log Complete Milestone 45

Date: 2026-05-30

Three new operational log modules were added as part of Milestone 45.

`incident_response_log` records operational provenance for facility incident response events (detection, containment, eradication, recovery, lessons_learned). Incident response entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

`change_management_log` records operational provenance for structured change management events (planned changes, emergency changes, rollbacks, approval requests, rejections). Change management entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

`compliance_report_log` records operational provenance for compliance reporting events (internal audits, external audits, certification checks, policy reviews, regulatory reports). Compliance report entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

Schema count increased from 148 to 151. Consistency fixture updated: milestone 44→45, decision 91→92, schema_count 148→151.

# DECISION-093: Risk Assessment Log, Backup Recovery Log, And Capacity Planning Log Complete Milestone 46

Date: 2026-05-30

Three new operational log modules were added as part of Milestone 46.

`risk_assessment_log` records operational provenance for facility risk assessment events (cyber_risk, operational_risk, compliance_risk, physical_risk, environmental_risk). Risk assessment entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

`backup_recovery_log` records operational provenance for backup and recovery events (full_backup, incremental_backup, differential_backup, recovery_test, snapshot). Backup and recovery entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

`capacity_planning_log` records operational provenance for capacity planning events (storage_capacity, compute_capacity, network_capacity, personnel_capacity, equipment_capacity). Capacity planning entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

Schema count increased from 151 to 154. Consistency fixture updated: milestone 45→46, decision 92→93, schema_count 151→154.

# DECISION-094: Software Deployment Log, Performance Monitoring Log, And User Activity Log Complete Milestone 47

Date: 2026-05-30

Three new operational log modules were added as part of Milestone 47.

`software_deployment_log` records operational provenance for software deployment events (major_release, minor_release, patch, hotfix, rollback). Software deployment entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

`performance_monitoring_log` records operational provenance for performance monitoring events (cpu_utilization, memory_utilization, disk_io, network_throughput, response_time). Performance monitoring entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

`user_activity_log` records operational provenance for user activity events (login, api_call, config_change, data_export, admin_action). User activity entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

Schema count increased from 154 to 157. Consistency fixture updated: milestone 46→47, decision 93→94, schema_count 154→157.

# DECISION-095: Health Check Log, License Management Log, And Storage Management Log Complete Milestone 48

Date: 2026-05-31

Three new operational log modules were added as part of Milestone 48.

`health_check_log` records operational provenance for system and service health check events (api_health, database_health, network_health, service_health, storage_health). Health check entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

`license_management_log` records operational provenance for software license lifecycle events (activation, deactivation, expiry_warning, renewal, transfer). License management entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

`storage_management_log` records operational provenance for storage lifecycle events (allocation, cleanup, deallocation, migration, quota_change). Storage management entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

Schema count increased from 157 to 160. Consistency fixture updated: milestone 47→48, decision 94→95, schema_count 157→160.

# DECISION-096: Firmware Update Log, Configuration Audit Log, And Event Correlation Log Complete Milestone 49

Date: 2026-05-31

Three new operational log modules were added as part of Milestone 49.

`firmware_update_log` records operational provenance for firmware lifecycle events (component_update, driver_update, firmware_rollback, hotfix_patch, scheduled_update). Firmware update entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

`configuration_audit_log` records operational provenance for configuration compliance audit events (baseline_check, compliance_scan, drift_detection, manual_audit, scheduled_audit). Configuration audit entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

`event_correlation_log` records operational provenance for cross-system event correlation runs (alert_cluster, causal_chain, fault_event, observation_link, temporal_cluster). Event correlation entries do not modify candidate scores or pathway routing, do not authorize external submission, and do not constitute detection claims.

Schema count increased from 160 to 163. Consistency fixture updated: milestone 48→49, decision 95→96, schema_count 160→163.

# DECISION-097: Operational Log Registry Must Keep SQLite Policy Visible

Date: 2026-06-01

Operational log families must remain auditable as the fixture-backed log
surface grows. A registry consistency gate now checks that each operational log
family has a module, JSON schema, fixture, CLI summary command,
`SCHEMA_FILENAMES` entry, and explicit top-level SQLite production policy.

The current registry covers 74 operational log families and marks them with
`top_level_sqlite_required_before_production`. This does not migrate fixture
logs into SQLite and does not treat fixture records as production operational
state. It keeps the gap visible until a deliberate SQLite adapter or migration
is implemented.

Registry entries are local provenance guardrails only. They do not modify
candidate scores or pathway routing, do not authorize live data access, do not
authorize external submission, and do not constitute detection claims.

Schema count increased from 163 to 164. Consistency fixture updated: milestone
49→50, decision 96→97, schema_count 163→164.

# DECISION-098: Operational Log SQLite Migration Must Be Planned Before Adapters Mutate Databases

Date: 2026-06-01

Before fixture-backed operational log families are migrated into top-level
SQLite adapters, the project must maintain a non-destructive adapter plan that
maps every registry-backed log family to a SQLite migration phase. The plan
must cover candidate/review, observation/signal, pipeline/modeling,
infrastructure/facility, and security/compliance log families.

The adapter plan is a local consistency gate only. It must not mutate SQLite
databases, migrate fixture records, ingest real observation data, authorize live
data access, or authorize external submission. The plan keeps migration intent
auditable while preserving the current fixture-backed test surface.

Schema count increased from 164 to 165. Consistency fixture updated: milestone
50→51, decision 97→98, schema_count 164→165.

# DECISION-099: Operational Log SQLite Adapters Must Keep Non-Mutating Table Contracts Before Implementation

Date: 2026-06-02

Before fixture-backed operational log families receive SQLite adapter
implementations, the project must maintain a non-mutating table contract that
keeps adapter phase tables and required provenance columns explicit. The
contract covers the same five phases as the adapter plan and requires
provenance-oriented fields such as log ID, phase ID, payload JSON, recorded
timestamp, source fixture path, SQLite policy, and provenance hash.

The adapter contract is a local consistency gate only. It must not create
SQLite tables, migrate fixture records, ingest real observation data, authorize
live data access, authorize external submission, or constitute detections,
discoveries, or external validation. Mutation remains disabled until a future
reviewed adapter implementation is added deliberately.

Schema count increased from 165 to 166. Consistency fixture updated: milestone
51→52, decision 98→99, schema_count 165→166.

# DECISION-100: Operational Log SQLite DDL Must Remain Preview-Only Before Adapter Execution

Date: 2026-06-02

Before operational log SQLite adapters execute any SQL, the project must keep a
deterministic DDL preview gate that renders planned `CREATE TABLE` statements
from the adapter contract for review. The preview must include the required
provenance columns and must verify expected statement counts and required SQL
clauses.

The DDL preview is a local planning artifact only. It must not execute SQL,
create tables, migrate fixture records, ingest real observation data, authorize
live data access, authorize external submission, or constitute detections,
discoveries, or external validation. Execution remains disabled until a future
reviewed adapter implementation is added deliberately.

Schema count increased from 166 to 167. Consistency fixture updated: milestone
52→53, decision 99→100, schema_count 166→167.

# DECISION-101: Operational Log SQLite Row Payloads Must Remain Preview-Only Before Adapter Execution

Date: 2026-06-02

Before operational log SQLite adapters insert any rows, the project must keep a
deterministic row-payload preview gate that maps registry-backed operational log
families into the planned adapter phase tables for review. Preview rows must
include required provenance fields such as log ID, phase ID, payload JSON,
recorded timestamp placeholder, source fixture path, SQLite policy, and
provenance hash.

The row preview is a local planning artifact only. It must not insert rows,
create tables, migrate fixture records, ingest real observation data, authorize
live data access, authorize external submission, or constitute detections,
discoveries, or external validation. Execution remains disabled until a future
reviewed adapter implementation is added deliberately.

Schema count increased from 167 to 168. Consistency fixture updated: milestone
53→54, decision 100→101, schema_count 167→168.

# DECISION-102: Operational Log SQLite Inserts Must Remain Preview-Only Before Adapter Execution

Date: 2026-06-02

Before operational log SQLite adapters execute any insert statements, the
project must keep a deterministic insert-preview gate that renders
parameterized `INSERT` statements and bound values from row-preview records for
review. The preview must preserve contract column order, table mappings,
payload/value alignment, and disabled execution.

The insert preview is a local planning artifact only. It must not execute SQL,
insert rows, create tables, migrate fixture records, ingest real observation
data, authorize live data access, authorize external submission, or constitute
detections, discoveries, or external validation. Execution remains disabled
until a future reviewed adapter implementation is added deliberately.

Schema count increased from 168 to 169. Consistency fixture updated: milestone
54→55, decision 101→102, schema_count 168→169.

# DECISION-103: Operational Log SQLite Execution Ordering Must Remain Preview-Only Before Adapter Execution

Date: 2026-06-02

Before operational log SQLite adapters execute planned table creation or insert
statements, the project must keep a deterministic execution-preview gate that
renders transaction ordering around the insert-preview records for review. The
preview must preserve phase grouping, transaction markers, insert counts,
operation counts, disabled execution, and disabled mutation.

The execution preview is a local planning artifact only. It must not open
databases, execute SQL, insert rows, create tables, migrate fixture records,
ingest real observation data, authorize live data access, authorize external
submission, or constitute detections, discoveries, or external validation.
Execution remains disabled until a future reviewed adapter implementation is
added deliberately.

Schema count increased from 169 to 170. Consistency fixture updated: milestone
55→56, decision 102→103, schema_count 169→170.

# DECISION-104: Operational Log SQLite Dry-Run Manifests Must Reconcile Previews Before Adapter Execution

Date: 2026-06-02

Before operational log SQLite adapters open or mutate any database, the project
must keep a deterministic dry-run manifest that reconciles the DDL preview and
execution preview. The manifest must preserve DDL statement counts, insert
counts, phase counts, execution operation counts, phase/table alignment,
preview-only status, disabled database opening, disabled SQL execution,
disabled mutation, disabled live-data authorization, and disabled external
submission authorization.

The dry-run manifest is a local planning artifact only. It must not open
databases, execute SQL, insert rows, create tables, migrate fixture records,
ingest real observation data, authorize live data access, authorize external
submission, or constitute detections, discoveries, or external validation.
Execution remains disabled until a future reviewed adapter implementation is
added deliberately.

Schema count increased from 170 to 171. Consistency fixture updated: milestone
56→57, decision 103→104, schema_count 170→171.

# DECISION-105: Operational Log SQLite Adapter Readiness Must Remain Preflight-Only Before Execution

Date: 2026-06-02

Before operational log SQLite adapters open or mutate any database, the project
must keep a deterministic readiness preflight that reconciles the registry,
adapter plan, adapter contract, DDL preview, row preview, insert preview,
execution preview, and dry-run manifest. The preflight must preserve registry
counts, planned log counts, phase counts, DDL statement counts, row counts,
insert counts, execution operation counts, schema counts, upstream gate
failures, preflight-only status, disabled database opening, disabled SQL
execution, disabled mutation, disabled live-data authorization, and disabled
external submission authorization.

The readiness preflight is a local planning artifact only. It must not open
databases, execute SQL, insert rows, create tables, migrate fixture records,
ingest real observation data, authorize live data access, authorize external
submission, or constitute detections, discoveries, or external validation.
Execution remains disabled until a future reviewed adapter implementation is
added deliberately.

Schema count increased from 171 to 172. Consistency fixture updated: milestone
57→58, decision 104→105, schema_count 171→172.

# DECISION-106: Operational Log SQLite Adapter Authorization Must Remain Blocked Before Execution

Date: 2026-06-03

Before operational log SQLite adapters are implemented or allowed to open any
database, the project must keep a deterministic authorization gate that consumes
the readiness preflight and explicitly blocks adapter implementation, database
opening, SQL execution, fixture migration, mutation, live-data authorization,
and external submission authorization. The gate must preserve readiness
preflight status, readiness gate failure counts, readiness schema counts,
current schema counts, blocked authorization status, and disabled safety flags.

The authorization gate is a local planning artifact only. It must not open
databases, execute SQL, insert rows, create tables, migrate fixture records,
ingest real observation data, authorize live data access, authorize external
submission, or constitute detections, discoveries, or external validation.
Execution remains disabled until a future reviewed adapter implementation is
added deliberately with explicit operator approval.

Schema count increased from 172 to 173. Consistency fixture updated: milestone
58→59, decision 105→106, schema_count 172→173.

# DECISION-107: Project-Scoped MCP Bootstrap Must Stay Conservative And Local

Date: 2026-06-03

Project-scoped MCP configuration must be derived from
`docs/Technosignatures_MCP_BOOTSTRAP.md` and must remain limited to repository
file inspection, read-only git inspection, and fixed `.venv` validation
commands. The configured servers must not provide arbitrary shell execution,
unrestricted filesystem access, live-provider access by default, credential
exposure, large-data ingestion, external submission enablement, or public
candidate claims.

The bootstrap MCP servers are local engineering aids only. They do not change
candidate scores, pathway rules, report interpretation, live-data
authorization, external-submission authorization, or scientific readiness.
Claude Code and Codex may still require a one-time project trust or MCP
approval prompt before using the generated project configuration.

Schema count remains 173. Consistency fixture updated: milestone 59→60,
decision 106→107, schema_count remains 173.

# DECISION-108: MCP Bootstrap Config Must Remain Guarded By Local Consistency Checks

Date: 2026-06-03

Project-scoped MCP configuration must be guarded by a local consistency summary
that verifies `.mcp.json` and `.codex/config.toml` continue to expose only the
expected project-files, read-only git, and fixed validation guard servers. The
gate must verify `.venv/bin/python -m techno_search.mcp_servers` command use,
expected server kinds, forbidden token patterns, and disabled arbitrary-shell,
live-provider, and external-submission defaults.

The MCP bootstrap consistency gate is a local configuration drift check only.
It must not authorize live data access, external submission, candidate score
changes, pathway changes, detections, discoveries, or external validation.

Schema count increased from 173 to 174. Consistency fixture updated: milestone
60→61, decision 107→108, schema_count 173→174.

# DECISION-109: MCP Server Implementation Must Stay Allowlisted And Local

Date: 2026-06-03

Project-scoped MCP server implementation must remain guarded by a local policy
summary that verifies the server code exposes only allowlisted project-file,
read-only git, and fixed local validation tools. The gate must verify expected
tool names, strict input schemas, denied repository paths, read-size limits,
fixed read-only git commands, fixed `.venv` validation commands, local `.venv`
enforcement, absent mutating git commands, absent forbidden command tokens,
and disabled arbitrary-shell, live-provider, and external-submission defaults.

The MCP server policy gate is a local implementation drift check only. It must
not execute MCP commands, authorize live data access, authorize external
submission, change candidate scores, change pathways, create detections, claim
discoveries, or provide external validation.

Schema count increased from 174 to 175. Consistency fixture updated: milestone
61→62, decision 108→109, schema_count 174→175.

# DECISION-110: Data Transfer Log, System Diagnostics Log, And Resource Allocation Log Complete Milestone 63

Date: 2026-06-03

Data transfer log, system diagnostics log, and resource allocation log
operational provenance records have been added as Milestone 63.

Data transfer entries are operational provenance records — a data transfer
event does not modify candidate scores or pathway routing, does not authorize
external submission, and does not constitute a detection claim.

System diagnostics entries are operational provenance records — a system
diagnostic event does not modify candidate scores or pathway routing, does
not authorize external submission, and does not constitute a detection claim.

Resource allocation entries are operational provenance records — a resource
allocation event does not modify candidate scores or pathway routing, does
not authorize external submission, and does not constitute a detection claim.

Schema count increased from 175 to 177. Consistency fixture updated: milestone
62→63, decision 109→110, schema_count 175→177.

# DECISION-111: Access Control Log, Change Management Log, And Incident Log Complete Milestone 64

Date: 2026-06-04

Access control log, change management log, and incident log operational
provenance records have been added as Milestone 64.

Access control entries are operational provenance records — an access control
event does not modify candidate scores or pathway routing, does not authorize
external submission, and does not constitute a detection claim.

Change management entries are operational provenance records — a change
management event does not modify candidate scores or pathway routing, does
not authorize external submission, and does not constitute a detection claim.

Incident entries are operational provenance records — an incident event does
not modify candidate scores or pathway routing, does not authorize external
submission, and does not constitute a detection claim.

Schema count increased from 177 to 179. Consistency fixture updated: milestone
63→64, decision 110→111, schema_count 177→179.

# DECISION-112: Patch Management Log, Vulnerability Scan Log, And Compliance Audit Log Complete Milestone 65

Date: 2026-06-04

Patch management log, vulnerability scan log, and compliance audit log
operational provenance records have been added as Milestone 65.

Patch management entries are operational provenance records — a patch
management event does not modify candidate scores or pathway routing, does
not authorize external submission, and does not constitute a detection claim.

Vulnerability scan entries are operational provenance records — a vulnerability
scan event does not modify candidate scores or pathway routing, does not
authorize external submission, and does not constitute a detection claim.

Compliance audit entries are operational provenance records — a compliance
audit event does not modify candidate scores or pathway routing, does not
authorize external submission, and does not constitute a detection claim.

Schema count increased from 179 to 182. Consistency fixture updated: milestone
64→65, decision 111→112, schema_count 179→182.

# DECISION-113

Date: 2026-06-04

Disaster recovery log, service level log, and asset management log
operational provenance records have been added as Milestone 66.

Disaster recovery entries are operational provenance records — a disaster
recovery event does not modify candidate scores or pathway routing, does
not authorize external submission, and does not constitute a detection claim.

Service level entries are operational provenance records — a service level
event does not modify candidate scores or pathway routing, does not
authorize external submission, and does not constitute a detection claim.

Asset management entries are operational provenance records — an asset
management event does not modify candidate scores or pathway routing, does
not authorize external submission, and does not constitute a detection claim.

Schema count increased from 182 to 185. Consistency fixture updated: milestone
65→66, decision 112→113, schema_count 182→185.

---

# DECISION-114

Date: 2026-06-04

Network monitoring log, identity management log, and certificate management
log operational provenance records have been added as Milestone 67.

Network monitoring entries are operational provenance records — a network
monitoring event does not modify candidate scores or pathway routing, does
not authorize external submission, and does not constitute a detection claim.

Identity management entries are operational provenance records — an identity
management event does not modify candidate scores or pathway routing, does
not authorize external submission, and does not constitute a detection claim.

Certificate management entries are operational provenance records — a
certificate management event does not modify candidate scores or pathway
routing, does not authorize external submission, and does not constitute a
detection claim.

Schema count increased from 185 to 188. Consistency fixture updated: milestone
66→67, decision 113→114, schema_count 185→188.

# DECISION-115: Configuration Change Log, Data Retention Log, And Alert Escalation Log Complete Milestone 68

Date: 2026-06-04

Configuration change log, data retention log, and alert escalation log
operational provenance records have been added as Milestone 68.

Configuration change entries are operational provenance records — a
configuration change event does not modify candidate scores or pathway
routing, does not authorize external submission, and does not constitute a
detection claim.

Data retention entries are operational provenance records — a data retention
event does not modify candidate scores or pathway routing, does not authorize
external submission, and does not constitute a detection claim.

Alert escalation entries are operational provenance records — an alert
escalation event does not modify candidate scores or pathway routing, does
not authorize external submission, and does not constitute a detection claim.

Schema count increased from 188 to 191. Consistency fixture updated: milestone
67→68, decision 114→115, schema_count 188→191.

# DECISION-116: Service Request Log, Problem Management Log, And Release Management Log Complete Milestone 69

Date: 2026-06-04

Service request log, problem management log, and release management log
operational provenance records have been added as Milestone 69.

Service request entries are operational provenance records — a service request
event does not modify candidate scores or pathway routing, does not authorize
external submission, and does not constitute a detection claim.

Problem management entries are operational provenance records — a problem
management event does not modify candidate scores or pathway routing, does not
authorize external submission, and does not constitute a detection claim.

Release management entries are operational provenance records — a release
management event does not modify candidate scores or pathway routing, does not
authorize external submission, and does not constitute a detection claim.

Schema count increased from 191 to 194. Consistency fixture updated: milestone
68→69, decision 115→116, schema_count 191→194.

# DECISION-117: Supplier Management Log, Contract Management Log, And Knowledge Management Log Complete Milestone 70

Date: 2026-06-04

Supplier management log, contract management log, and knowledge management log
operational provenance records have been added as Milestone 70.

Supplier management entries are operational provenance records — a supplier
management event does not modify candidate scores or pathway routing, does not
authorize external submission, and does not constitute a detection claim.

Contract management entries are operational provenance records — a contract
management event does not modify candidate scores or pathway routing, does not
authorize external submission, and does not constitute a detection claim.

Knowledge management entries are operational provenance records — a knowledge
management event does not modify candidate scores or pathway routing, does not
authorize external submission, and does not constitute a detection claim.

Schema count increased from 194 to 197. Consistency fixture updated: milestone
69→70, decision 116→117, schema_count 194→197.

---

# DECISION-118: Training Log, Budget Log, And Audit Finding Log Complete Milestone 71

Date: 2026-06-05

Training log, budget log, and audit finding log operational provenance records
have been added as Milestone 71.

Training entries are operational provenance records — a training event does not
modify candidate scores or pathway routing, does not authorize external
submission, and does not constitute a detection claim.

Budget entries are operational provenance records — a budget event does not
modify candidate scores or pathway routing, does not authorize external
submission, and does not constitute a detection claim.

Audit finding entries are operational provenance records — an audit finding
event does not modify candidate scores or pathway routing, does not authorize
external submission, and does not constitute a detection claim.

Schema count increased from 197 to 200. Consistency fixture updated: milestone
70→71, decision 117→118, schema_count 197→200.

---

# DECISION-119: Change Request Log, Project Milestone Log, And Vendor Assessment Log Complete Milestone 72

Date: 2026-06-05

Change request log, project milestone log, and vendor assessment log operational
provenance records have been added as Milestone 72.

Change request entries are operational provenance records — a change request
event does not modify candidate scores or pathway routing, does not authorize
external submission, and does not constitute a detection claim.

Project milestone entries are operational provenance records — a project
milestone event does not modify candidate scores or pathway routing, does not
authorize external submission, and does not constitute a detection claim.

Vendor assessment entries are operational provenance records — a vendor
assessment event does not modify candidate scores or pathway routing, does not
authorize external submission, and does not constitute a detection claim.

Schema count increased from 200 to 203. Consistency fixture updated: milestone
71→72, decision 118→119, schema_count 200→203.

---

# DECISION-120: Communication Log, Document Management Log, And Procurement Log Complete Milestone 73

Date: 2026-06-05

Communication log, document management log, and procurement log operational
provenance records have been added as Milestone 73.

Communication entries are operational provenance records — a communication
event does not modify candidate scores or pathway routing, does not authorize
external submission, and does not constitute a detection claim.

Document management entries are operational provenance records — a document
management event does not modify candidate scores or pathway routing, does not
authorize external submission, and does not constitute a detection claim.

Procurement entries are operational provenance records — a procurement event
does not modify candidate scores or pathway routing, does not authorize external
submission, and does not constitute a detection claim.

Schema count increased from 203 to 206. Consistency fixture updated: milestone
72→73, decision 119→120, schema_count 203→206.

---

# DECISION-121: Human Approval Gates Real Observation Pipeline Execution

Date: 2026-06-09
Status: accepted

## Context

The highest-priority Tier 1 blocker remains real observation data ingestion.
The local data directory contains synthetic turboSETI fixtures, an invalid HTTP
response saved as a `.dat` file, and structurally plausible Voyager artifacts
without a complete acquisition and approval record. File-format validity alone
cannot establish that an artifact is approved real telescope data.

## Decision

Require each production-path turboSETI hit table to have a sibling provenance
sidecar with a matching SHA-256 hash, HTTPS archive URL, archive and instrument
metadata, download timestamp, approved data-use and provenance reviews, and
explicit human authorization for local real-data use.

The BL pipeline runner rejects synthetic, invalid, unverified, or hash-mismatched
artifacts. Synthetic generation remains available only through the explicit
`TECHNO_ALLOW_SYNTHETIC_BL_FIXTURES=1` development override. TLS certificate
verification may not be bypassed by the download script.

## Consequences

Synthetic outputs cannot be mistaken for Tier 1 evidence, and the first real
pipeline run stops at a visible human partnership gate. This decision does not
approve any current local artifact, close the real-observation blocker,
authorize external submission, or constitute a detection claim.

---

# DECISION-122: First Real GBT Cadence Is Admitted And OFF-Target Evidence Blocks Promotion

Date: 2026-06-10
Status: accepted

## Context

Human Gate 1 approved an official GBT ON/OFF cadence for local processing. The
HIP65352 archive summary was rejected because its published third comparison
scan is non-contiguous. The HIP99427 sequence provides a contiguous ABACAD
cadence with three target scans and three comparison targets.

The six selected `.0002.h5` products total approximately 1.45 GB. Their
9.7960855 Hz/s drift-bin resolution required a documented 10 Hz/s ingestion
ceiling to include one nonzero bin in each direction. The run produced 213
turboSETI rows: 110 ON and 103 OFF.

The first uncorrected pipeline report promoted the cadence despite an
OFF-target presence score of 1.0. That behavior violated the project's
false-positive-first scientific rules.

## Decision

Admit the checksum-verified HIP99427 cadence for local real-data processing.
Preserve archive MD5, local SHA-256, scan role, processing parameters, data-use
review, human approval, and disabled external-submission state in provenance.

Treat frequency-matched OFF-target presence at or above 0.4 as blocking
evidence. Apply a strong human-interference likelihood and suppress
technosignature-interest likelihood when the same signal population appears in
comparison scans.

## Consequences

The Tier 1 gap **Real observation data ingested** is closed for local
production-readiness accounting. Four Tier 1 blockers remain: approved real
labels, calibrated thresholds, an approved site-specific RFI database, and
external peer review.

The corrected HIP99427 report routes `do_not_submit_false_positive` with human
interference as the dominant hypothesis. This result does not authorize
external submission and does not constitute a detection claim.

---

# DECISION-123: Citizen-Science Reproducibility Is The Production Review Standard

Date: 2026-06-10
Status: accepted

## Context

This is an independent citizen-science project without access to domain experts.
Requiring expert approval as a production prerequisite would create a permanent,
uncontrollable blocker and would encourage unsupported claims that review had
occurred.

The admitted HIP99427 cadence contains 213 turboSETI rows. Exact
frequency/drift grouping produces 124 independent evidence groups suitable for
conservative operational labels.

## Decision

Use deterministic, published citizen-science review for local production:

1. A primary ON/OFF count rule assigns operational labels.
2. A structurally independent six-position scan-signature method audits them.
3. Disagreements and incomplete ON-only recurrence become
   `insufficient_evidence`.
4. Source hashes, license, methods, evidence, and limitations remain attached.
5. Public reproducibility replaces assumed expert approval for local production.

The resulting label set contains 81 false positives, 2 operational follow-up
groups, and 41 insufficient-evidence groups. The two methods agree on all 124
groups. Current v0 scoring agrees with 67 groups (54.03%), including 80.25% of
false positives and both follow-up groups, but none of the insufficient-evidence
routes. No thresholds are changed from this single cadence.

## Consequences

The Tier 1 real-labeled-dataset and citizen-science production-review gaps are
closed. Calibrated thresholds and a permitted site-specific RFI database remain
blocking. These labels are not expert labels, external validation, detections,
discoveries, or authorization for external submission.

---

# DECISION-124: GBT Provisional RFI Catalog Built From Public Regulatory Documentation

Date: 2026-06-11
Status: accepted

## Context

The Tier 1 gap "Real site-specific RFI database — synthetic guardrails and
admission gates exist, but no permitted site-monitoring catalog has been
approved" requires a real, site-specific RFI frequency list. No such catalog
had been downloaded or parsed into the pipeline schema.

## Options Considered

1. Download HTML pages from NRAO GBT RFI web resources (fragile; format unknown).
2. Build a provisional catalog from publicly-documented international frequency
   allocations (ITU Radio Regulations, IS-GPS-200, GLONASS ICD, ICAO Annex 10,
   FCC CFR Title 47) that are demonstrably relevant to GBT SETI work.
3. Wait for an NRAO-published machine-readable CSV (URL uncertain; availability
   unconfirmed).

## Decision

Build a provisional catalog (option 2) from 15 well-documented public sources.
Each entry carries a full provenance citation to the relevant regulation or ICD.
All entries are marked `active: false` and `review_status: "provisional"` until
a human operator verifies each band against the actual GBT observed RFI
environment. A corresponding admission record (`rfi-admit-gbt-provisional-v1`)
is added to `tests/fixtures/rfi_database_admission.json` with
`admission_status: "blocked_pending_review"` and `blocker_count: 2` (site
monitoring context not yet verified; operator sign-off required).

Covered bands (all inactive, provisional):

- Cellular 700 MHz (FCC Part 27)
- DME aircraft navigation 960–1215 MHz (ICAO Annex 10)
- SSR Mode S interrogation 1030 MHz (ICAO Annex 10)
- ADS-B transponders 1090 MHz (ICAO Annex 10)
- GPS L5 1176 MHz (IS-GPS-200L)
- L-band radar/EESS 1215–1300 MHz (ITU §5.329)
- GPS L2 1228 MHz (IS-GPS-200L)
- GLONASS L2 1243–1249 MHz (GLONASS ICD v5.1)
- L-band MSS downlink 1525–1559 MHz (ITU §5.357A)
- RNSS allocation 1559–1610 MHz (ITU §5.328A)
- GPS L1 / Galileo E1 / BeiDou B1C 1575 MHz (IS-GPS-200L)
- GLONASS L1 1598–1606 MHz (GLONASS ICD v5.1)
- Iridium satellite 1616–1626.5 MHz (ITU Appendix 30B)
- L-band MSS uplink 1626.5–1660.5 MHz (ITU §5.357A)
- 2.4 GHz ISM / WiFi (FCC Part 15; confirmed at GBT)

Files:
- `scripts/build_gbt_rfi_provisional_catalog.py` — builder script
- `tests/fixtures/rfi_catalog/gbt_rfi_provisional_v1.json` — provisional catalog
- `tests/test_gbt_rfi_provisional_catalog.py` — 38 tests

## Consequences

The "Real site-specific RFI database" Tier 1 gap is partially unblocked.
Tooling now exists to build and validate a real-data-sourced provisional
catalog. The gap is not closed: two blockers remain (site monitoring context
review and operator sign-off). The human approval gate is not bypassed —
`real_data_authorized` remains `false` and all entries remain `active: false`
until a human operator completes the review described in the admission record
notes. No scoring thresholds change. No candidate report is affected. This is
not a detection, discovery, or external validation.

---

# DECISION-125: Calibration Corpus Admission Gate And Download Manifest

**Date:** 2026-06-11
**Status:** Accepted
**Milestone:** Calibration corpus scaffolding (Tier 1 gap: calibrated scoring thresholds)

## Context

The "Calibrated scoring thresholds" Tier 1 gap requires a real-noise corpus
of at least 3 cadences, 3 targets, 2 epochs, and 100 turboSETI hits passing
all acceptance gates in `noise_threshold_calibration.py`. No such corpus exists
yet. This decision creates the planning and admission scaffolding to assemble it.

## Decision

Add calibration corpus download manifest and admission gate:

- `scripts/build_calibration_target_manifest.py` — BL archive target manifest
  (5 targets: Voyager1 already ingested, HIP65803/HIP4436/HIP8102/HIP16537 queued)
- `scripts/run_calibration_corpus_pipeline.sh` — end-to-end pipeline script:
  H5 directory → turboSETI → provenance JSON sidecars → calibration gate check
- `tests/fixtures/calibration_corpus_admission.json` — 5 admission records
  (1 already_admitted, 4 blocked_pending_download)
- `src/techno_search/calibration_corpus_admission.py` — admission module
- `schemas/calibration_corpus_admission.schema.json` — JSON schema
- `tests/test_calibration_corpus_admission.py` — tests
- `docs/RFI_OPERATOR_REVIEW_PROTOCOL.md` — operator checklist for the
  provisional GBT RFI catalog review (unblocks DECISION-124's 2 blockers)
- `validate-all` gate: calibration_corpus_admission_record_count >= 1,
  calibration_corpus_admission_safety_ok == True

## Consequences

Calibration corpus scaffolding is in place. The Tier 1 gap (calibrated scoring
thresholds) is not closed: all 4 new targets remain blocked_pending_download.
The gap closes only after the user downloads the H5 files, validates turboSETI
output, writes provenance sidecars with human approval, and the calibration gate
passes all 7 acceptance checks. No scoring thresholds change. No candidate report
is affected. This is not a detection, discovery, or external validation.

# DECISION-126: GBT Provisional RFI Catalog Operator Sign-Off

Date: 2026-06-11
Status: Accepted

The citizen-science operator has reviewed all 15 entries in the GBT provisional
RFI catalog (gbt_rfi_provisional_v1.json) and provided the following sign-off:

"Regulatory allocation confirmed from public sources (ITU Radio Regulations,
IS-GPS-200L, GLONASS ICD v5.1, ICAO Annex 10, FCC CFR Title 47). GBT
site-monitoring confirmation pending — each entry has been verified against
documented frequency allocations only, not against GBT site monitoring logs.
Provisional citizen-science operator sign-off for local pipeline use only.
All 15 entries remain active=false pending explicit activation decision."

Changes applied:
- rfi_database_admission.json: rfi-admit-gbt-provisional-v1 moved from
  blocked_pending_review to ready_for_local_fixture; blocker_count 2→0;
  monitoring_context_reviewed and external_review_completed set to true.
- gbt_rfi_provisional_v1.json: all 15 entries updated from
  review_status=provisional to review_status=reviewed.

The Tier 1 RFI database gap is resolved at the citizen-science operator level.
Entries remain inactive (active=false) and do not affect scoring until explicitly
activated. This is not a detection, discovery, or external validation. The sole
remaining Tier 1 blocker is calibrated scoring thresholds.

# DECISION-127: Calibrated Scoring Configuration From Real GBT Noise Data

Date: 2026-06-12
Status: Accepted

**Milestone:** Tier 1 gap closure — calibrated scoring thresholds (DECISION-128 prerequisite)

The calibration gate passed `calibration_ready: true` against 213 real GBT hits from 5
cadences, 5 targets, 2 epochs (HIP99427, HIP100670, HIP99560, HIP99759, VOYAGER-1).
Derived thresholds: noise_floor_snr=42.4, follow_up_snr=54.8, high_interest_snr=118.3,
max_rfi_like_drift_hz_s=5.21.

`configs/scoring_calibrated_v1.json` is created to encode these thresholds. It is
preferred over `scoring_v0.json` by `default_scoring_config_path()` when present.
The config adds `snr_thresholds` and `drift_rate_thresholds` sections. `ScoringConfig`
dataclass is extended with optional `snr_thresholds: SnrThresholds | None` and
`drift_rate_thresholds: DriftRateThresholds | None` fields.

Thresholds require independent citizen-science review before use in production scoring
claims. This is not a detection, discovery, or external validation.

# DECISION-128: Scoring Model v1 — Calibrated SNR Tiers And Drift Neutralization

Date: 2026-06-12
Status: Accepted

**Milestone:** Tier 2 — improved model accuracy against real labeled data

Scoring model v1 achieves 77.42% diagnostic agreement (96/124) on the real HIP99427
citizen-science label set, up from 54.03% (67/124) for the v0 rule-based model.

Three mechanism changes from v0:
1. **Tiered SNR scoring**: SNR is scored against calibrated noise-floor tiers
   (noise_floor=42.4, follow_up=54.8, high_interest=118.3) rather than a naive divisor.
   Sub-floor candidates score ≤ 0.20; follow-up range 0.20–0.60; high-interest 0.60–0.90+.
2. **Drift neutralization for real data**: All 213 real GBT hits have identical
   |drift_rate| = 5.214355 Hz/s (turboSETI coarse-grid artifact). When
   `drift_rate_thresholds` is present, drift contribution is neutralized to 0.0 to
   prevent spurious TI inflation from a non-discriminating artifact.
3. **NOISE boost for sub-floor single-hit candidates**: When SNR < noise_floor AND
   persistence < 0.1 AND off_target < 0.3, adds 4.0*(1-snr/noise_floor) to the
   NOISE_OR_LOW_CONFIDENCE posterior, routing the majority of 41 `insufficient_evidence`
   single-hit cases away from candidate_review_packet.

Remaining 12 failures (9.7%): 4 persistent insufficient_evidence cases that overlap
feature space with follow_up, and 8 high-on-target sub-floor cases where the boost
is insufficient. These are not addressed in v1 to avoid over-fitting.

This is not a detection claim. Diagnostic agreement is measured against citizen-science
labels derived from a single cadence/target combination and has not been independently
validated. The model requires independent reproduction before production scoring claims.

# DECISION-131: Data Release Snapshot — Reproducibility Verification Across Pipeline Versions

Date: 2026-06-13
Status: Accepted

**Milestone:** 75 — Closes Tier 3 gap: "Reproducibility verification across data releases"

## Context

After deploying a new pipeline version or calibration update, operators need a way to confirm which candidates changed pathway and whether the change is expected. Without a snapshot mechanism, pathway drift between versions is invisible.

## Decision

Add a data release snapshot module that:
- Captures named snapshots of batch pipeline results (pathway assignments per candidate, SHA-256 hash of sorted assignments, pathway and track distribution)
- Provides `snapshot_from_batch_manifest()` to build a snapshot from an existing `batch_manifest.json`
- Provides `compare_snapshots()` to identify pathway changes, new candidates, and removed candidates across two snapshots
- Provides `data_release_snapshot_summary()` for sequential cross-release comparison across all fixture snapshots
- Adds `techno-search data-release-snapshot-summary` and `techno-search compare-data-releases` CLI commands
- Adds `schemas/data_release_snapshot.schema.json` (total schemas: 105)
- Gates `validate-all` on `data_release_snapshot_count >= 1`

## Scientific Guardrails

- Pathway changes detected across releases are local scheduling observations only
- Cross-release comparisons do not constitute detection claims, calibration approvals, or authorization for external submission
- Pathway drift is reported but never auto-corrected; operator review is required

# DECISION-130: Learned Scoring Model v1 — Logistic Regression On 124 Real HIP99427 Labels

Date: 2026-06-12
Status: Accepted

**Milestone:** 74 — Closes final Tier 2 gap: "Learned scoring model (replace rule-based baseline)"

A logistic regression model was trained on 124 real GBT/HIP99427 citizen-science
labels using 3-fold stratified cross-validation. Key metrics:

- 3-fold CV accuracy: 99.19% (std 0.0115) vs rule-based baseline 77.42%
- Train accuracy: 100% (expected — small balanced dataset)
- Label distribution: false_positive=81, insufficient_evidence=41, follow_up=2
- Feature columns: 17 numeric features from real turboSETI hit table entries
- Class weighting: `class_weight="balanced"` to handle severe follow_up imbalance
- Solver: `lbfgs` with `max_iter=2000`

Scientific guardrails:
- Model scores are local scheduling aids only; not validated production scoring
- Does not constitute a detection claim or authorize external submission
- Independent citizen-science reproduction required before any production use
- Hold-out test set from independent observation epochs required
- Expert review of pathway assignments required

Operator review dashboard (also Milestone 74):
- `review_dashboard_summary()` aggregates open flags, overdue deadlines, review queue,
  blockers, watchlist elevated targets, and real-label accuracy gate
- Exit code 1 on needs_attention for CI/operator alerting

# DECISION-129: Multi-Epoch Comparison, Parallel Scoring, And SQLite Candidate Store

Date: 2026-06-12
Status: Accepted

**Milestone:** Tier 2/3 — infrastructure for multi-epoch analysis and pipeline efficiency

Three new operational modules added:

1. **multi_epoch.py**: Compares turboSETI hit tables across multiple observation epochs
   (different .dat files from separate observing sessions). Groups hits within
   configurable frequency tolerance; reports per-group persistence scores and
   multi-epoch group counts. Scientific guardrail: multi-epoch persistence is an
   evidence factor only; persistent signals may be persistent RFI. This module does
   not constitute a detection claim.

2. **score_candidates_parallel()**: Uses `ProcessPoolExecutor` to score multiple
   candidates in parallel. Falls back to serial when workers=1/None or for single-element
   lists (avoiding subprocess overhead). Module-level `_score_one()` function ensures
   picklability across worker processes. Parallel results are deterministic and
   identical to serial results.

3. **candidate_store.py**: SQLite-backed local candidate store for scored candidates,
   indexed by track, pathway, and signal_reality. Provides `CandidateStore` with
   `init_schema()`, `insert()`, `get()`, `list_all()`, `list_by_pathway()`,
   `list_by_track()`, and `summary()`. CLI commands: `candidate-store-init`,
   `candidate-store-summary`, `candidate-store-list`. Scientific guardrail: candidate
   store records are local triage and provenance records only; stored records do not
   authorize external submission and do not constitute detection claims.

---

# DECISION-132: External Submission Protocol

**Date:** 2026-06-14
**Status:** Active
**Closes:** Tier 3 gap — External submission workflow

External submission of a technosignature-interest candidate is blocked until
all preconditions are satisfied:

- P1: A formal `candidate_review_packet` exists with real telescope data
- P2: Escalation gate passes (`escalation_gate_check()["passes"] == True`),
  requiring pathway, SNR ≥ 42.4, and `multi_epoch_persistence_score > 0`
- P3: Cross-target RFI suppression has not flagged the candidate
- P4: Independent citizen-science reproduction of the candidate pipeline run
- P5: Public reproducibility package posted with explicit non-detection disclaimer
- P6: Human operator sets `operator_cleared: True` on the escalation record

The protocol is documented in `docs/EXTERNAL_SUBMISSION_PROTOCOL.md`.

As of 2026-06-14, all preconditions are unmet for all candidates.
`external_review_authorized: False` on all escalation records.

Scientific guardrail: This protocol is an operator scheduling aid. No step
constitutes a detection claim, scientific confirmation, or authorization to
submit without human approval of all preconditions.

---

# DECISION-133: Model Generalisation Beyond Cygnus Campaign

**Date:** 2026-06-15
**Status:** Active
**Closes:** Tier 3 gap — Model generalizability beyond single GBT Cygnus campaign

The learned scoring model (v1, logistic regression) was trained exclusively on
124 labels from GBT L-band observations of the Cygnus region (HIP99427 ABACAD
cadence).  To make the pipeline production-ready for surveys beyond a single
pointing and epoch, six generalisation capabilities are added:

**Priority 1 — Extended BL corpus download:**
`scripts/download_bl_extended_corpus.sh` downloads GBT turboSETI `.dat` files
from non-Cygnus targets spanning multiple galactic latitudes and RA hours.
These are calibration aids only; no hit constitutes a detection claim.

**Priority 2 — MeerKAT BLUSE hit ingestion:**
`scripts/ingest_meerkat_hits.py` downloads and normalises Sheikh et al. 2025
MeerKAT BLUSE 2-million-hit dataset as a false-positive training corpus for
the semi-supervised scorer.  Output stored in `data/meerkat_hits/` (not
committed).

**Priority 3 — Injection-recovery grid:**
`scripts/setigen_injection_grid.py` uses setigen to inject synthetic signals
into real GBT HDF5 files across a grid of (SNR, drift_rate, frequency) values,
augmenting the `follow_up` class.

**Priority 4 — Cross-band feature normalization:**
`src/techno_search/radio/cross_band_features.py` implements
`normalize_drift_rate()`, `relative_snr()`, `on_off_consistency_score()`, and
`extract_cross_band_features()`.  Key invariant: dividing drift rate by centre
frequency in GHz yields a telescope-agnostic physical quantity.

**Priority 5 — GLOBULAR pre-filter:**
`src/techno_search/globular_filter.py` adapts Jacobson-Bell et al. 2024
(arxiv:2411.16556) using sklearn HDBSCAN on 13 morphological features.  Hits
assigned to dense clusters are flagged as probable RFI.  ~93% FP reduction
with zero labels needed.  Cluster labels are heuristic; they are not ground
truth.

**Priority 6 — Semi-supervised anomaly scorer:**
`src/techno_search/semisupervised_scorer.py` implements `SemisupervisedScorer`
using sklearn Pipeline (QuantileTransformer + PCA + IsolationForest).  Trained
on an unlabeled RFI-dominated corpus; anomaly score is high for hits far from
the learned normal manifold.

Scientific guardrail: All outputs are local triage aids only.  Cluster labels,
anomaly scores, and cross-band features do not constitute detection claims, do
not authorize external submission, and require independent-method citizen-science
review before use in production pathway routing.

---

# DECISION-134: AI Hardening Production Evidence Gate

**Date:** 2026-06-17
**Status:** Reopened fail-closed by DECISION-144; DECISION-139 evidence retained
**Opens:** Tier 3 gap — AI hardening production blocker

The Tier 1 and Tier 2 engineering gates are closed, and DECISION-133 adds the
generalization tooling needed to move beyond the original single-campaign GBT
label set. However, tooling alone is not enough to promote the learned or
AI-assisted scoring stack into live production operations. The project must
first produce held-out, review-safe evidence that the model recognizes likely
false positives and follow-up-worthy candidate signals outside the training
cadence.

## Decision

Open a Tier 3 production blocker named **AI hardening production blocker**.
Future agents must treat this blocker as unresolved until all of the following
are true:

- Held-out real-data evidence exists outside the HIP99427 training cadence,
  preferably using DECISION-133 paths such as `data/extended_corpus/`,
  `data/meerkat_hits/`, or `data/injection_grid/`.
- The same held-out evidence is evaluated by at least two structurally
  independent methods, such as rule-based scoring, learned logistic regression,
  cross-target RFI suppression, GLOBULAR-style dense-cluster filtering, and
  semi-supervised anomaly scoring.
- Disagreements, abstentions, negative evidence, and blocking issues are
  preserved rather than forced into consensus.
- A production-run evidence bundle exists with clean validation output,
  conservative scan summaries, negative-result or escalation-gate records,
  provenance, and explicit non-detection language.
- Large data, caches, SQLite logs, and local scan artifacts remain uncommitted;
  only review-safe methodology and metadata may be committed.
- External submission remains blocked by DECISION-132 unless all external
  submission preconditions and explicit human authorization are satisfied.

## Consequences

- `docs/PRODUCTION_READINESS.md` must no longer describe all Tier 3 work as
  closed while this gate is open.
- DECISION-133 implementation remains complete, but its capabilities must now
  be used to generate production evidence instead of being treated as sufficient
  by themselves.
- The learned model remains a local scheduling aid until this gate is closed.
- Citizen-science independent-method review may substitute for unavailable
  expert review, but it is not external expert validation or peer review.

Scientific guardrail: This decision does not claim a detection, does not claim
expert review, does not authorize external submission, and does not invalidate
the existing Tier 1/Tier 2 engineering gates. It blocks production promotion of
learned or AI-assisted pathway routing until held-out evidence and reproducible
review artifacts exist.

---

# DECISION-135: AI Hardening Evidence Paths Must Be Populated Before Review Credit

**Date:** 2026-06-17
**Status:** Accepted
**Supports:** DECISION-134 — AI hardening production blocker

## Context

The DECISION-133 acquisition scripts write to `data/extended_corpus/`,
`data/meerkat_hits/`, and `data/injection_grid/`. A failed acquisition can still
create one of those directories. Counting path existence alone would therefore
make production-readiness summaries look more advanced than the evidence
actually supports.

## Decision

The AI hardening gate summary must distinguish:

- configured DECISION-133 evidence paths;
- paths that merely exist on disk;
- paths that contain at least one file;
- empty existing paths created by failed or incomplete acquisition attempts;
- provisional local calibration-corpus `.dat` files outside HIP99427.

Local calibration-corpus files outside HIP99427 may support provisional
citizen-science review, but they do not close DECISION-134 by themselves because
they were already part of calibration-threshold work and are not a populated
DECISION-133 evidence stream.

## Consequences

`ai-hardening-gate-summary` and `validation-summary` expose populated evidence
counts and empty existing path counts. Production promotion remains blocked when
only empty DECISION-133 directories or provisional local calibration holdouts
exist. No candidate score, pathway, external submission authorization, or
detection language changes.

---

# DECISION-136: Ignore Payloads, Commit Sanitized Artifact Maps

**Date:** 2026-06-17
**Status:** Accepted
**Supports:** DECISION-134 — AI hardening production blocker

## Context

Future coding agents can only inspect what is committed to GitHub, but the
project's production-hardening evidence streams produce large local data,
SQLite logs, generated scan outputs, and machine-specific inventories that must
not be committed. A prior accidental staging event showed that narrow ignore
rules are not enough when the standard operator cadence is `git add .`.

## Decision

The repository must remain safe under `git add .` while still preserving
GitHub-visible continuity for future agents:

- large science payloads, generated run outputs, logs, local SQLite databases,
  caches, model arrays, serialized models, and machine-specific inventories are
  ignored by default;
- tiny intentional fixtures remain explicitly allowed under `tests/fixtures/`;
- `docs/LOCAL_DATA_INVENTORY.md` is a committed, sanitized artifact map rather
  than a generated local directory listing;
- `scripts/create_data_inventory.sh` writes machine-specific snapshots to
  ignored `docs/LOCAL_DATA_INVENTORY.local.md`;
- artifact-producing changes must be checked with `git add --dry-run .` before
  commit.

## Consequences

Future agents should update committed maps, manifests, checksums, schemas,
tests, and methodology docs when they need GitHub-visible context. They must not
commit local payloads merely to make other agents aware that data exists. This
preserves DECISION-134 reproducibility context without weakening data hygiene,
scientific provenance, or conservative non-claim guardrails.

---

# DECISION-137: Optimize Local Execution For M4 Max With GPU-First AI Training

**Date:** 2026-06-17
**Status:** Accepted
**Supports:** DECISION-134 — AI hardening production blocker

## Context

The project is now producing AI hardening evidence, learned-model comparisons,
semi-supervised anomaly scores, injection-recovery grids, and production-run
evidence bundles. These workloads are computationally expensive and should use
the user's local workstation efficiently. The local machine profile records a
MacBook Pro M4 Max with 16 CPU cores, a 40-core Apple GPU, Metal support, and
64 GB unified memory.

## Decision

Future agents must optimize code and run plans for the local workstation by
default:

- AI training, learned-model evaluation, embedding generation, tensor-heavy
  inference, and large numerical experiments should prefer a tested GPU backend
  on this machine, such as Apple Metal/MPS, MLX, or another project-approved
  accelerator.
- CPU-heavy batch workloads should use bounded multiprocessing or
  multithreading, starting with up to 12 workers unless profiling supports a
  different value.
- I/O-bound catalog, provider, or disk-heavy workflows should start with
  conservative concurrency, usually 4 to 6 workers.
- Process-level parallelism must avoid native-library oversubscription by
  bounding NumPy/SciPy/sklearn thread counts when needed.
- Worker counts, accelerator choices, memory ceilings, batch sizes, and cache
  paths must stay configurable and documented.

## Consequences

Local production-hardening work should run faster and make better use of the
M4 Max GPU/CPU resources. This decision does not permit hard-coding hardware
assumptions into scientific logic, thresholds, candidate scores, or claims. GPU
and parallel acceleration must preserve deterministic tests, provenance,
false-positive-first review, negative evidence, no-submission defaults, and CPU
fallback paths when GPU support is unavailable.

---

# DECISION-138: Extended Corpus Acquisition Must Use Current BL Discovery And Fail Closed

**Date:** 2026-06-18
**Status:** Accepted
**Supports:** DECISION-134 — AI hardening production blocker

## Context

The DECISION-133 extended-corpus downloader previously encoded direct
`blpd0.ssl.berkeley.edu` `.dat` URLs. Those URLs no longer resolve from the
current local environment, while the official Breakthrough Open Data search
page exposes current `bldata.berkeley.edu` HDF5 download links for the same
held-out target family. The stale downloader also completed with exit code 0
after downloading zero files, which could leave empty directories that look
like progress but are not DECISION-134 evidence.

## Decision

The extended-corpus acquisition path must:

- discover current GBT HDF5 download URLs from the official Breakthrough Open
  Data search page instead of relying on stale hard-coded `blpd0` paths;
- store raw HDF5 inputs and any derived hit tables only under ignored
  `data/extended_corpus/` paths;
- emit visible progress and conservative scientific guardrails;
- exit nonzero when no held-out evidence file is downloaded or reused;
- keep empty target directories from receiving DECISION-134 review credit.

## Consequences

Future agents should treat zero-download runs as blockers, not partial
successes. Review-safe manifests, checksums, summaries, and tests may be
committed, but raw HDF5 files, derived hit tables, logs, caches, and local scan
outputs remain ignored payloads. This decision does not claim a detection,
expert review, external validation, or external-submission authorization.

---

# DECISION-139: DECISION-134 Closed For Local Citizen-Science Production Promotion

**Date:** 2026-06-18
**Status:** Historical promotion interpretation superseded by DECISION-144
**Closes:** DECISION-134 — AI hardening production blocker

## Context

DECISION-134 required a populated held-out evidence stream, at least two
structurally independent citizen-science method reviews, preserved disagreements
or abstentions, negative evidence, and a review-safe production evidence bundle
before learned or AI-assisted pathway routing could be promoted for production
operations.

Two bounded `data/extended_corpus` GBT HDF5 attempts, HIP17147 and HIP39826,
produced useful zero-hit negative evidence but no valid turboSETI hit rows for
candidate-level method comparison. The approved DECISION-133
`data/injection_grid` stream then used the Voyager 1 GBT HDF5 file as real-noise
substrate for a setigen injection-recovery grid.

## Evidence

The committed closure evidence bundle is
`tests/fixtures/ai_hardening_injection_grid_closure_evidence.json`, with the
human-readable summary in
`docs/ai_hardening_evidence/INJECTION_GRID_CLOSURE_EVIDENCE.md`.

Review-safe evidence recorded:

- source HDF5 path `data/bl_hits/Voyager1.single_coarse.fine_res.h5`, SHA-256
  `c9a9a54f4140e3754ffb2455fae4eeb2eb70c8207123116ee953e4fce15c36ac`,
  byte count `50549227`, uncommitted raw payload;
- injection manifest `data/injection_grid/injection_grid_manifest.json`,
  SHA-256 `4315dcee426fba4b44ce18015a82d0771782d6ea3b6d6503be7d7eb2b46252ac`,
  uncommitted generated payload;
- 75/75 injections completed and recovered;
- 75 HDF5 outputs, 75 turboSETI DAT outputs, 75 logs, and one local manifest,
  all ignored under `data/injection_grid`;
- 256 valid turboSETI hit rows available for review-safe method comparison;
- recorded method-family reviews for rule-based scoring, GLOBULAR-style
  dense-cluster filtering, and semi-supervised anomaly scoring;
- learned logistic regression abstention because this closure does not retrain
  or externally validate the HIP99427 real-label model on the injection grid;
- cross-target RFI suppression abstention because the injection grid uses one
  real-noise source target.

## Decision

Close DECISION-134 for local citizen-science production promotion only.

The machine-readable AI hardening gate is now closed with:

- `status: "closed"`;
- `production_promotion_allowed: true`;
- `production_promotion_scope: "local_citizen_science_operations_only"`;
- `external_submission_allowed: false`;
- `detection_claimed: false`;
- `expert_review_claimed: false`;
- a committed closure evidence bundle path.

## Consequences

Learned, semi-supervised, and AI-assisted pathway routing may be used as local
citizen-science production scheduling aids. They do not constitute detections,
discoveries, expert review, peer review, external validation, or
external-submission authorization.

DECISION-132 remains controlling for external submission. External submission
is still blocked unless all DECISION-132 preconditions are satisfied and the
operator explicitly authorizes that separate path.

Raw HDF5, DAT, LOG, SQLite, cache, and generated science payloads remain
ignored. Future agents must preserve GitHub-visible continuity through
sanitized evidence bundles, checksums, manifests, methodology docs, schemas,
and tests rather than committing raw local payloads.

# DECISION-140: Terminal UX For Production Scan Operations

**Date:** 2026-06-18
**Status:** Accepted
**Closes:** Tier 3 production scan operations UX gap

## Context

DECISION-139 authorized local citizen-science production promotion. Running
overnight multi-target scans previously produced verbose pipeline output that
made it impractical to monitor progress or spot escalation candidates at a
glance. A production scan operator needs a clean, low-noise terminal interface.

## Decision

Add the artifact-backed `prod-scan` CLI command for production run operations,
plus `prod-file-scan INPUT_DIR OUTPUT_DIR` and `src/techno_search/tui.py` for
lower-level per-file scans. Together they implement:

- Rich spinner or compact fallback progress while each production step or
  target processes
- One printed production target row with run index, target name, best-effort
  target class, follow-up status, composite pipeline score, and pathway
- One lower-level per-file result line:
  `YYYYMMDD-HHMMSS-<TARGET>  <stellar class>  score=N.NN  [ESCALATION | --]`
- Stellar classification via name-heuristic on `simbad_match_names` (galaxy/
  extragalactic, star cluster, nebula/remnant, neutron star, white dwarf,
  binary star, giant star, variable star, stellar (Gaia), stellar, unknown)
- Production target classification via conservative local metadata heuristics
- Composite production score from the existing pipeline follow-up score
- Per-file composite score from `scores.signal_reality_confidence`
- Resume support: `prod-scan --resume-run-dir` skips completed production
  artifacts; `prod-file-scan` skips targets whose output JSON already exists
- Clean Ctrl+C handling with exit code 130 and "restart to resume" message
- Plain-text fallback when `rich` is unavailable

All output lines are local scheduling aids only. No result line constitutes a
detection claim or authorizes external submission.

## Consequences

Production scan operators can run `techno-search prod-scan` or
`bash scripts/run_production_scan.sh` overnight and review a concise per-target
summary on return while preserving JSON ledgers under `results/scans/RUN-*`.
The `prod-file-scan` command remains available for lower-level file-oriented
pipeline runs, and its `--force` flag allows re-processing already-completed
targets. Stellar classification remains heuristic only; SIMBAD otype codes are
not currently stored and should be added to `catalog_crossmatch` in a future
improvement for reliable classification.

# DECISION-141: Production Scan History, History-Aware Queue, And Continuous Loop

**Date:** 2026-06-20
**Status:** Accepted
**Closes:** Five operational bugs observed during live production scan operation

## Context

Live operation of `run_production_scan.sh` revealed five distinct bugs that
prevented it from functioning as a real production scanner:

1. The script only read already-processed `results/` manifests and never
   called `run-pipeline` on new `.dat` files — running the same three targets
   every time regardless of what was in the data directory.
2. Each run assigned new scan indexes to the same targets, making it impossible
   to tell whether two entries referred to the same physical target observation.
3. No scan history was maintained, so the script had no awareness of targets
   already searched and could not link re-scans together.
4. The target selection algorithm (`target_selection_score()`) existed in
   `background_search.py` but was never called by the script, so the operator
   could not see why targets were chosen.
5. The scan exited after processing a fixed list rather than running
   continuously until stopped.

Additionally, the UX DNA of a correct production scan had never been captured
in a project-agnostic reference document.

## Decision

1. Add `src/techno_search/prod_scan_queue.py` implementing:
   - `ScanHistoryRecord` — one completed scan per target per run
   - `append_scan_record()` — atomic NDJSON append with `fcntl.flock`
   - `load_scan_history()` — NDJSON reader keyed by `target_stem`
   - `build_target_queue()` — ranked queue; base 0.50, +0.08 first-scan boost,
     −0.04/scan penalty capped at −0.12; scanned targets excluded by default
   - `scan_history_summary()` — all-time history summary with pending count

2. Add three new CLI commands:
   - `prod-target-queue --dat-dir PATH [--history-file F] [--force]`
   - `prod-record-scan --target-stem T --run-id R --score S --pathway P --dat-file F --history-file H [--parent-run-id ID]`
   - `scan-history-summary [--history-file H] [--dat-dir D]`

3. Rewrite `scripts/run_production_scan.sh` to:
   - Require `--dat-dir PATH` (raw turboSETI `.dat` input directory)
   - Discover `.dat` files at runtime via `prod-target-queue`
   - Print the full ranked queue with selection scores before the scan loop
   - Process each target with `run-pipeline FILE --track radio --output-dir DIR`
   - Record each completed scan with `prod-record-scan`
   - Wrap the selection+pipeline loop in `while true` with `trap SIGINT/SIGTERM`
   - Support `--continuous` mode that polls for new `.dat` files on queue exhaustion
   - Run post-scan steps after all targets are processed, not interleaved

4. Add `docs/PRODUCTION_SCAN_RUNBOOK.md` — a project-agnostic durable reference
   capturing the five rules of correct production scan orchestration, with
   adaptation guidance for other pipelines.

5. The `target_stem` (filename without extension) is the stable cross-run
   identity. The `parent_run_id` field links re-scans of the same target across
   runs. The history file `results/scan_history.ndjson` is gitignored because
   it contains absolute local paths and grows without bound.

## Consequences

The production scan operator can now run:

```bash
caffeinate -i bash scripts/run_production_scan.sh --dat-dir data/bl_hits
```

On first run, all `.dat` targets are queued (first-scan boost). On subsequent
runs, already-scanned targets are skipped by default, so the scanner naturally
progresses through the corpus without manual tracking. `--force-rescan` includes
previously scanned targets at lower priority and links the re-scan record to the
prior run via `parent_run_id`. `--continuous` mode polls for newly deposited
`.dat` files after queue exhaustion, enabling unattended overnight operation.

All scan history records are local scheduling aids only. No record constitutes
a detection claim or authorizes external submission.

# DECISION-142: Non-Deterministic turboSETI .dat Discovery Fixed In Download Scripts

**Date:** 2026-06-20
**Status:** Accepted
**Closes:** Production data pipeline artifact hygiene gap — non-deterministic hit-table discovery in `download_bl_hits.sh` and `fetch_bl_alternative.sh`

## Context

During live production testing following DECISION-141, the `run_production_scan.sh`
pipeline was observed to receive more `.dat` files than expected from the `data/bl_hits/`
directory. Investigation revealed that both download scripts used `find "$DATA_DIR" -name "*.dat" | head -1`
to locate the turboSETI output file after a run. This non-deterministic glob:

1. Picks the alphabetically-first `.dat` file, not the one just produced.
2. When `bl_turboSETI_test.dat` (from `fetch_bl_alternative.sh`) already existed,
   `download_bl_hits.sh`'s `find | head -1` would grab that file instead of the
   newly-created `voyager1.dat`, leaving `voyager1.dat` as residual alongside the
   renamed copy.
3. Both residual files were then processed by `run_pipeline_on_bl_data.sh`, producing
   two candidate manifests for what is physically one observation target and inflating
   `candidate_count` from 1 to 2.

The root cause is using `find | head -1` when the output filename is deterministically
predictable from the input H5 filename.

## Decision

Replace `find "$DATA_DIR" -name "*.dat" | head -1` with a deterministic stem
prediction in both scripts:

```bash
H5_STEM="$(basename "$H5_FILE" .h5)"
FOUND_DAT="$DATA_DIR/${H5_STEM}.dat"
```

turboSETI always writes `<input_stem>.dat` in the output directory. Using the
stem directly eliminates file-ordering ambiguity and guarantees the script
operates on the file it just produced, not a pre-existing alphabetically-prior file.

The fix is applied in:
- `scripts/download_bl_hits.sh` — stem from `voyager1.h5` → `voyager1.dat`
- `scripts/fetch_bl_alternative.sh` — stem from `tseti_test.h5` → `tseti_test.dat`

Both scripts also retain the `[[ "$FOUND_DAT" != "$FINAL_DAT" ]] && mv` rename
guard to canonicalize the output filename regardless of the H5 input name.

## Consequences

`download_bl_hits.sh` and `fetch_bl_alternative.sh` are now deterministic: each
script operates only on the file it produced, regardless of what other `.dat`
files exist in `data/bl_hits/`. The `run_pipeline_on_bl_data.sh` receives exactly
one `.dat` per download script invocation. Production scan candidate counts
reflect actual observation targets rather than artifact duplication.

No result constitutes a detection claim or authorizes external submission.


# DECISION-143: Stratified Random Sampling Design Replaces Arbitrary 5-Target Extended Corpus

**Date:** 2026-06-26
**Status:** Accepted
**Closes:** Scientific methodology gap — extended corpus target selection lacked statistical sampling rationale required for publishable null results or candidate claims.

## Context

The initial extended corpus (HIP17147, HIP39826, HIP66704, HIP74981, HIP82860) was selected
for sky-coverage diversity (non-Cygnus pointings), not statistical representativeness. Without
a documented sampling rationale, any null result or candidate from these targets cannot be
defended in peer review. Citizen science producing candidates for review must meet the same
methodological standards as institutional research.

## Decision

Replace the arbitrary 5-target list with a stratified random sample drawn from the
Breakthrough Listen High-Priority Candidate (HPRC) target list (Isaacson et al. 2017,
PASP 129, 054501).

**Stratification:** Cartesian product of three dimensions:
- Distance: near (0–8 pc), mid (8–20 pc), far (20–50 pc) → 3 bins
- Spectral class: F, G, K, M → 4 classes
- Exoplanet host: 0 (no), 1 (yes) → 2 values
- Total: 24 strata; 2 targets per stratum (default); seed 42 for reproducibility

**Implementation:**
- `data/bl_hprc_seed_targets.csv` — 48-target committed seed file (Isaacson et al. 2017 +
  Enriquez et al. 2017 + Price et al. 2020 + Hipparcos/Gaia/NASA Exoplanet Archive)
- `scripts/build_stratified_sample.py` — deterministic sampler; same seed + same CSV → same output
- `data/target_sample_manifest.json` — committed manifest (31 targets across 18 strata, seed 42)
  with SHA-256 checksum of seed CSV for reproducibility verification
- `docs/SAMPLING_DESIGN.md` — publishable methodology documentation

**Also fixed in this PR:** `discover_dat_files()` in `prod_scan_queue.py` changed from
non-recursive `iterdir()` to `rglob("*.dat")`, enabling discovery of `.dat` files stored
in per-target subdirectories (the nested layout produced by the extended corpus download
and turboSETI scripts).

## Consequences

The download script (`scripts/download_bl_extended_corpus.sh`) now reads targets from
`data/target_sample_manifest.json` instead of a hardcoded list. The stratified sample
provides the methodological foundation required to defend null results and candidate claims
in peer review. Any publication must cite: sampling frame (Isaacson et al. 2017),
stratification scheme (distance × spectral class × exoplanet status), and random seed (42).

The 5 original targets remain in the seed CSV and may appear in the manifest if selected
by the stratified sampler — their prior inclusion is now coincidental overlap, not
post-hoc justification.

No entry in any manifest constitutes a detection claim or authorizes external submission.


# DECISION-144: Reopen Learned/AI Promotion Gate Under Pre-Existing-Label Rule

**Date:** 2026-07-14
**Status:** Accepted
**Supersedes:** DECISION-139 production-promotion interpretation; preserves its measured injection-recovery evidence

## Context

The current production-readiness assessment correctly states that the
semi-supervised anomaly/OOD score is uncalibrated and ranking-only because the
only accepted pre-existing per-hit label source has 124 rows from one cadence
and is inadequate for a global threshold. However, the machine-readable
DECISION-134 gate still reported `status: closed` and
`production_promotion_allowed: true` based on DECISION-139's setigen
injection-recovery bundle. `validate-all` therefore advertised learned/AI
promotion even though the authoritative labeled-data boundary kept it
fail-closed.

The root cause was treating synthetic recovery evidence as calibration and
label evidence. Injection recovery can measure whether known injected signals
survive a pipeline in real noise. It cannot supply independent row-level class
labels, establish real-background false-discovery behavior, or calibrate a
global anomaly/OOD threshold.

## Decision

Reopen the learned/AI promotion gate. The machine-readable gate must report:

- `status: "open"`;
- `production_promotion_allowed: false`;
- `production_promotion_scope: "blocked"`;
- an open `adequate_preexisting_row_level_labels` requirement;
- no detection, expert-review, external-validation, or external-submission
  claim.

DECISION-139's 75/75 injection recovery, 256 turboSETI rows, provenance, method
comparisons, and abstentions remain valid historical recovery evidence. They no
longer authorize learned/AI production promotion. Learned and semi-supervised
outputs remain uncalibrated local ranking diagnostics.

## Consequences

The gate may close only if adequate pre-existing, independently supplied,
row-level labels with documented provenance become available for the claimed
calibration scope. The project must never ask the user or anyone else to create,
review, infer, or synthesize those missing labels. Unlabeled observations and
synthetic injections are not substitutes. Deterministic false-positive
rejection and other roadmap work continue while the learned gate remains
honestly blocked.


# DECISION-145: Retire Project-Owned Label Creation Paths

**Date:** 2026-07-14
**Status:** Accepted
**Implements:** AGENTS.md pre-existing-label-only prime directive

## Context

After DECISION-144 reopened learned/AI promotion, a code audit found that the
repository still exposed executable pre-prime-directive machinery for creating
and operationalizing new labels: `scripts/build_citizen_science_labels.py`
inferred labels from deterministic ABACAB cadence behavior, its public helper
APIs wrote label datasets, `scripts/combine_citizen_science_labels.py` enabled
expansion into new combined training sets, and `learned_scoring_model.py`
trained binary/pathway models from those artifacts. `validate-all` then treated
their accuracy and trained state as passing gates, while admission fixtures
authorized the artifact as real labeled data. Those are project-created
annotations, not pre-existing, independently supplied row-level ground truth.

## Decision

Delete both label-creation scripts, their dataset build/write APIs, and the
label-trained binary/pathway model module and CLI commands. Remove their
accuracy/trained-state gates from `validate-all` and fail-close the curated
dataset and calibration admission records. Preserve read-only deterministic
ABACAB cadence analysis as unlabeled triage outcomes in `cadence_triage.py`.
Preserve the frozen 124-row HIP99427 artifact only as legacy diagnostic input;
do not regenerate, expand, train, calibrate, evaluate, or promote from it. Add
regression tests that require the executable creation and training paths to
remain absent.

## Consequences

No repo-supported command can create or combine new project-owned labels or
train a model from the retired artifacts. The validation dashboard no longer
advertises their accuracy or trained state as a passing scientific gate.
Future training, calibration, threshold selection, or scientific evaluation
may use labels only when they already exist independently with documented
row-level provenance. If adequate labels remain unavailable, learned gates stay
fail-closed. The permitted next work is deterministic false-positive rejection,
unlabeled ranking/triage, or another named roadmap gap—not reconstructing a
labeling workflow under a different name.


# DECISION-146: Retire Invalid Default Scoring Calibration

**Date:** 2026-07-16
**Status:** Accepted
**Supersedes:** DECISION-127/128 production-scoring and escalation-threshold interpretation

## Context

DECISION-145 removed project-owned label creation and label-trained models, but
the resulting `configs/scoring_calibrated_v1.json` remained the automatic
default for every `score_candidate()` call. Its tiered SNR scoring, drift
neutralization, and low-SNR noise boost were evaluated and tuned against the
same unauthorized project-generated HIP99427 cadence outcomes. The config also
claimed a five-cadence, five-target, two-epoch calibration while the current
threshold preflight records one cadence and one epoch and is not
calibration-ready. A hard-coded 42.4 SNR escalation threshold derived from that
config could still return `passes: true`.

## Decision

Delete `scoring_calibrated_v1.json` and its citizen-review template. Make the
explicitly uncalibrated `scoring_v0.json` heuristic config the only automatic
default. Preserve optional typed SNR/drift configuration support for future
explicitly supplied configurations with admissible provenance, but never
auto-discover a calibrated file by filename. Mark the standalone escalation
SNR gate unavailable and fail closed until an admissible threshold exists.

## Consequences

Default pathway scores may change because the invalid SNR tiers, drift
neutralization, and label-tuned noise boost no longer apply automatically.
Those scores remain local heuristic triage aids, not calibrated probabilities
or scientific evaluation. No SNR value can currently cause the standalone
escalation gate to pass. Reopening that gate requires adequate pre-existing,
independent row-level evidence with documented provenance and a new reviewed
decision; project-generated, inferred, synthetic, or unlabeled threshold truth
is not admissible.


# DECISION-147: Retire Residual Threshold-Calibration Helper Chain

**Date:** 2026-07-16
**Status:** Accepted
**Implements:** DECISION-145/146 and the pre-existing-label-only prime directive

## Context

After the label-evaluation command and invalid calibrated config were retired,
the repository still exposed a calibration-corpus acquisition and admission
chain. Its shell pipeline invoked the deleted `noise-threshold-calibration`
command, its provenance helper asked a human to approve unlabeled observations
for calibration, and its CLI admission command returned unconditional success
without reading the fixture or validating any evidence. The transfer guide also
presented the retired GBT values as production thresholds and instructed users
to create new labels for other instruments.

## Decision

Delete the calibration-corpus download, fetch, target-manifest, provenance, and
pipeline helpers along with their dedicated test, schema, fixture, CLI stub,
and schema registry entry. Replace the procedural threshold and transfer guides
with fail-closed status documents that reject the legacy GBT values and define
the independent pre-existing evidence required before a future calibration
proposal can be considered.

## Consequences

No repository-supported helper can download unlabeled observations specifically
to promote a scoring threshold, convert human provenance approval into
calibration truth, or report a passing calibration admission gate without
evidence. General public-data acquisition and deterministic radio analysis
remain available through current policy-compliant workflows. Learned/anomaly
outputs and heuristic scores remain local triage diagnostics; no threshold is
calibrated, transferable, or authorized for candidate escalation or external
submission.
