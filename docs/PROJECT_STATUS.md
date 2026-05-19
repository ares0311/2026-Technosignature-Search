# PROJECT STATUS

## Project
Technosignature Search

## Status
Initial v0 Implementation

## Current Phase
Initial v0 Implementation / Synthetic Scoring Core

## Package Name
`techno_search`

---

## Current Scope

The project is a multi-modal citizen-science platform for searching existing astronomical datasets for possible technosignature-interest candidates.

The project will support three tracks from day one:

1. Radio SETI candidate search
2. Infrared waste-heat / Dyson-style candidate search
3. Archival and catalog anomaly search

---

## Completed

- [x] Project concept defined
- [x] Repository anchor selected
- [x] Multi-modal scope selected
- [x] Package name selected: `techno_search`
- [x] Documentation architecture defined
- [x] Scientific language policy defined
- [x] Testing policy defined
- [x] Agent operating rules defined
- [x] Local system profile documented
- [x] Initial Python package scaffold created
- [x] Development tool configuration added
- [x] First scoring and pathway modules implemented
- [x] Synthetic unit tests added for multi-modal scoring
- [x] Candidate Markdown and JSON reporting implemented
- [x] Candidate report file writers implemented
- [x] Dependency-free synthetic report plot artifacts added
- [x] Track-specific v0 config files added
- [x] Synthetic radio prototype added
- [x] Synthetic radio injection helpers added
- [x] Synthetic infrared prototype added
- [x] Synthetic archival anomaly prototype added
- [x] Example synthetic review packets added
- [x] Calibration false-positive fixtures added
- [x] CLI entry point for synthetic candidate scoring added
- [x] Report manifest generation added
- [x] Batch scoring CLI added
- [x] Installed console-script smoke test added
- [x] Batch example artifacts added
- [x] CLI and publishing docs drift tests added
- [x] Expanded calibration false-positive fixtures added
- [x] Candidate and report validation CLI commands added
- [x] JSON schema artifacts added
- [x] Score regression snapshots added
- [x] Opt-in live-data integration scaffold added
- [x] Conservative release checklist added
- [x] Validation guide added
- [x] Example regeneration CLI added
- [x] Schema versioning policy added
- [x] Explicit schema version fields added to generated artifacts
- [x] Live provider adapter scaffolds added
- [x] Mocked live provider implementations added with injected fetch functions
- [x] Live provider response normalization added as provenance-only metadata
- [x] Deterministic live-provider cache keys added
- [x] Live provider summary CLI added
- [x] Live provider metadata cache helper added
- [x] Live provider cache summary CLI added
- [x] Non-networked provider query-shape builders added
- [x] Cached live metadata fixtures added
- [x] Live metadata fixture summary CLI added
- [x] Live provider client protocol added
- [x] Disabled Gaia and IRSA live-client skeletons added
- [x] Fixture-driven live-client normalization tests added
- [x] Disabled VizieR, SIMBAD, and Breakthrough Listen live-client skeletons added
- [x] Breakthrough Listen local file metadata request shape added
- [x] Live client summary CLI added
- [x] Catalog cache metadata policy documented
- [x] Catalog cache policy CLI added
- [x] Catalog cache commit-path validator added
- [x] Catalog cache validator CLI added
- [x] Catalog cache validation wired into `validate-all`
- [x] Catalog cache metadata storage helper added
- [x] Catalog cache summary CLI added
- [x] Provider normalization contract added
- [x] Provider normalization regression fixtures added
- [x] Provider normalization summary wired into `validate-all`
- [x] Guarded Gaia live client added with mocked transport tests
- [x] Guarded IRSA live client added with mocked transport tests
- [x] Guarded VizieR live client added with mocked transport tests
- [x] Guarded SIMBAD live client added with mocked transport tests
- [x] Breakthrough Listen local-file metadata client added
- [x] Live client summary capability fields added
- [x] Provenance helper module added
- [x] Provenance summaries added to report manifests
- [x] Provenance summary CLI added
- [x] Validation summary CLI added
- [x] Optional plot artifact references added to report manifests
- [x] Plot artifact summary CLI added
- [x] Synthetic injection-recovery fixtures added
- [x] Injection-recovery summary CLI added
- [x] Injection-recovery summary wired into local validation
- [x] Synthetic reliability curve fixtures added
- [x] Reliability summary CLI added
- [x] Reliability summary wired into local validation
- [x] Synthetic precision-recall fixtures added
- [x] Precision-recall summary CLI added
- [x] Precision-recall summary wired into local validation
- [x] False-positive class analysis summary CLI added
- [x] False-positive class analysis wired into local validation
- [x] Human-review queue packet schema added
- [x] Human-review triage labels added
- [x] Reviewer notes scaffold added
- [x] Review queue summary CLI added
- [x] Review queue summary wired into local validation
- [x] Human-review consensus labels added
- [x] Consensus summary CLI added
- [x] Consensus summary wired into local validation
- [x] Consensus export examples added
- [x] Consensus export summary CLI added
- [x] Consensus export summary wired into local validation
- [x] Calibration-by-track summary CLI added
- [x] Calibration-by-track summary wired into local validation
- [x] Validation dataset manifest schema added
- [x] Validation dataset summary CLI added
- [x] Validation dataset summary wired into local validation
- [x] Validation readiness fixture, schema, and summary CLI added
- [x] Validation readiness summary wired into local validation
- [x] Benchmark metadata schema added
- [x] Benchmark metadata summary CLI added
- [x] Benchmark metadata summary wired into local validation
- [x] Benchmark run-result fixture and schema added
- [x] Benchmark run-result summary CLI added
- [x] Benchmark run-result summary wired into local validation
- [x] Benchmark run-result append workflow added
- [x] Benchmark repeated-run comparison workflow added
- [x] README public entrypoint refreshed with compact project overview
- [x] Background target-priority fixture, schema, and summary CLI added
- [x] Passive/background search ledger fixture, schema, and summary CLI added
- [x] Background target-priority and ledger summaries wired into local validation
- [x] Background target-priority weights promoted into a versioned config file
- [x] Explicit local-only passive runner added for ledger append tests
- [x] Reviewed background workflow ledger semantics added
- [x] Background reviewed-workflow summary CLI added
- [x] Background reviewed-workflow counts wired into local validation
- [x] Candidate-extraction handoff fixture, schema, and summary CLI added
- [x] Candidate-extraction handoff counts wired into local validation
- [x] Background reviewed and needs-follow-up outcome log schemas added
- [x] Reviewed and needs-follow-up outcome summaries wired into local validation
- [x] Scheduler target selection now accounts for never-reviewed boosts and prior-review penalties
- [x] Deterministic local follow-up test result schema, fixture, and summary CLI added
- [x] Report-readiness gate and top-three recommendation fixture added
- [x] Follow-up test and report-readiness counts wired into local validation
- [x] Conservative draft follow-up report schema, fixture, and summary CLI added
- [x] Explicit user decision schema, fixture, and summary CLI added
- [x] External scheduler templates added for cron and launchd with ignored artifact paths
- [x] Persisted Markdown writer and manifest for conservative draft follow-up reports added
- [x] Draft follow-up report validation wired into local validation
- [x] User-decision append helper added with explicit external-submission approval guard
- [x] Scheduler dry-run command added for temporary artifact directories
- [x] Top-level `logs/` policy added for local SQLite operational logs
- [x] SQLite log initialization, background-run mirroring, summary, and validation commands added
- [x] SQLite integrity, migration, recent-run, needs-follow-up, and review-safe export commands added
- [x] Generated top-level SQLite log commit guard added
- [x] SQLite PRAGMA diagnostics, ignored backups, retention summaries, and vacuum maintenance commands added
- [x] SQLite log non-destructive migration plan command added
- [x] SQLite log review-safe weekly digest command added
- [x] Persisted draft report example artifacts committed under `examples/background_draft_reports`
- [x] Local artifacts cleanup CLI with dry-run default and committed-path safety added
- [x] Cross-track candidate cross-reference schema, fixture, and summary CLI added
- [x] Persisted-report reproducibility verification helper and CLI added
- [x] Cross-track and reproducibility wiring added to `validate-all` and `validation-summary`
- [x] Non-networked CI template hardened under `docs/templates/ci.yml`
- [x] CI guidance added under `docs/CI.md`
- [x] Route coverage extended to all 6/6 `Pathway` enum values
- [x] `validate-all` route-coverage gate now requires zero uncovered pathways
- [x] Operations-readiness summary and review-safe digest added for local-only
      operator handoff
- [x] Operations-readiness visibility added to `validation-summary` and CI
      template without enabling live data

---

## In Progress

- [x] Add calibration fixture documentation and expansion plan
- [x] Add CLI usage documentation
- [x] Add live-data integration interfaces behind mocks
- [x] Add local live-provider metadata cache helper
- [x] Add non-networked provider query-shape builders
- [x] Add cached live metadata fixture coverage
- [x] Add disabled live provider client skeletons
- [x] Add fixture-driven live-client normalization coverage
- [x] Add catalog cache policy and commit-path guardrails
- [x] Add guarded Gaia live provider client
- [x] Add guarded IRSA live provider client
- [x] Add guarded VizieR live provider client
- [x] Add guarded SIMBAD live provider client
- [x] Add real live-data provider clients behind explicit integration gates
- [x] Add weekly review template assembling SQLite digest + cross-track summary
- [x] Add target watchlist scheduling aid with conflict detection
- [x] Add guarded SQLite log migration (v1 → v2 adding `target_notes`)
- [x] Add interpretable rule-based baseline classifier (Milestone 10 scaffold)
- [x] Add baseline evaluation harness with pathway accuracy gate in `validate-all`
- [x] Add per-track accuracy breakdown in baseline evaluation
- [x] Add rule fire-rate reporting for all 8 named baseline rules
- [x] Add misclassification log (candidate_id, expected, predicted, rule_trace) in baseline eval
- [x] Add baseline performance history fixture and `baseline-performance-history-summary` CLI
- [x] Add synthetic injection grid tests for radio SNR×drift and infrared excess routing
- [x] Add `baseline-pathway-drift-summary` CLI with zero-drift gate in `validate-all`
- [x] Add watchlist priority ordering by `priority_override_score`
- [x] Add weekly review template watchlist gate (elevated count, blocked count, prioritized targets)
- [x] Add `sqlite-log-track-summary` CLI for per-track run counts from local database
- [x] Add `health` CLI combining baseline accuracy, watchlist conflicts, and drift status
- [x] Add baseline eval and performance history JSON schema artifacts
- [x] Add DECISION-029: Weekly Review Template Is The Authoritative Operator Handoff

---

- [x] Baseline confusion matrix (per-pathway precision/recall/F1) in `evaluate_baseline()`
- [x] `baseline-confusion-matrix-summary` CLI
- [x] `score-determinism-check` CLI — gate: all example candidates produce deterministic outputs
- [x] Candidate lifecycle schema, fixture, and `candidate-lifecycle-summary` CLI
- [x] Observation schedule schema, fixture, and `observation-schedule-summary` CLI
- [x] False-negative summary from injection-recovery fixture and `false-negative-summary` CLI
- [x] DECISION-030: Scoring Must Be Deterministic Before Any Learned Model Is Introduced
- [x] Scoring config summary (`scoring-config-summary`) and `scoring_config_summary.schema.json`
- [x] Route coverage summary (`route-coverage-summary`) checking Pathway enum fixture coverage
- [x] Lifecycle transition validator (`lifecycle-transition-summary`) with stage ordering checks
- [x] Observation efficiency summary (`observation-efficiency-summary`) with per-track rates
- [x] DECISION-031: Scoring Config And Route Coverage Are Required Local Validation Gates
- [x] 29 JSON schema artifacts (added scoring_config_summary)
- [x] Route coverage extended to 6/6 Pathway values via dedicated route-coverage fixtures
- [x] Per-track sensitivity config summary (`sensitivity-config-summary`) — synthetic weights audit
- [x] Candidate triage notes schema (`candidate_triage_v1`), fixture, loader, and `triage-summary` CLI
- [x] DECISION-032: Candidate Triage And Sensitivity Config Are Validated Scheduling Aids
- [x] 31 JSON schema artifacts (added candidate_triage and sensitivity_config_summary)

---

## Recently Completed (this iteration)

- [x] CI template now runs pytest, Ruff, mypy, whitespace check, `validate-all`, and `health` with live data disabled
- [x] CI workflow-scope caveat documented in `docs/CI.md` and release checklist
- [x] Synthetic route coverage now includes `external_followup_candidate` without authorizing external submission
- [x] Route coverage summary reports 6/6 Pathway values covered and zero uncovered pathways
- [x] Operations readiness now reports local-only states: `local_only_ready`, `operator_review_required`, and `blocked_for_real_data`
- [x] Review-safe operations digest added without large payloads, live-provider results, or unsupported claims
- [x] `validate-all`, `validation-summary`, and `health` remain green

## Next 3 Actions

1. Keep resolving operations-readiness blockers before any real observation intake.
2. Copy `docs/templates/ci.yml` to `.github/workflows/ci.yml` only after confirming the publishing token has GitHub `workflow` scope.
3. Add curated validation intake examples only when provenance, licensing, labeling, and external-review requirements are satisfied.

---

## Next Milestone

**Milestone 1 — Multi-Modal Scoring Core**

Status: initial v0 implemented.

Input:
- synthetic radio candidate
- synthetic infrared candidate
- synthetic archival anomaly candidate

Output:
- posterior-style probabilities
- false-positive probability
- candidate-interest score
- recommended pathway
- explanation

---

## Current Risks

- Scope creep across too many technosignature concepts
- Weak false-positive handling
- Overclaiming candidate significance
- Large data files accidentally committed
- Live network tests becoming flaky
- Search tracks becoming inconsistent

---

## Mitigations

- Build scoring core first using synthetic examples.
- Keep all outputs conservative.
- Use config files for thresholds.
- Mock external services in default tests.
- Preserve provenance for every candidate.
- Maintain separate specs for radio, infrared, and anomaly tracks.

---

## Definition of Development-Ready

The project is ready for development when:

- documentation files are committed
- repo has `AGENTS.md` and `CONTRIBUTING.md`
- package scaffold exists
- tests directory exists
- `pyproject.toml` exists
- first implementation branch is created

---

## Recommended First Branch

```bash
git checkout -b feature/multimodal-scoring-core
```

Note: the initial scoring core is currently implemented on the working branch.

---

## Recommended First Code Targets

```text
src/techno_search/schemas.py
src/techno_search/scoring.py
src/techno_search/pathway.py

tests/test_scoring.py
tests/test_pathway.py
```
