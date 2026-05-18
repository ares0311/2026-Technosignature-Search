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
