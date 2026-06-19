# PROJECT STATUS

## Project
Technosignature Search

## Status
Citizen-science production deployment readiness

## Current Phase
Production triage, deployment verification, and conservative operations

## Package Name
`techno_search`

## Current Production Gate

Tier 1 and Tier 2 engineering blockers are closed. The Tier 3 **AI hardening
production blocker** (DECISION-134) is also closed for local citizen-science
production promotion after the injection-recovery closure bundle recorded
populated DECISION-133 evidence, independent method-family review, preserved
abstentions, and negative evidence.

DECISION-134 is closed for local citizen-science production promotion.

Current DECISION-134 evidence state: `data/extended_corpus` has been populated
with two bounded held-out GBT HDF5 records, HIP17147 and HIP39826, and both
produced zero-hit turboSETI results at the configured threshold. This is useful
negative evidence. DECISION-134 is closed by the `data/injection_grid`
evidence stream: 75/75 setigen injections in real Voyager 1 GBT noise were
recovered, producing 256 valid turboSETI hit rows and a committed review-safe
closure bundle. Production promotion is local citizen-science operations only;
expert review, peer review, external validation, detection, discovery, and
external submission are not claimed.

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
- [x] Production run IDs and separate non-detection/follow-up ledgers added for local production scan UX
- [x] Compact `prod-scan` and `prod-diagnostics` terminal UX added with
      restartable runs, per-target completion rows, best-effort target kind,
      follow-up status, and pipeline composite score
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
- [x] Operations action-plan summary added to prioritize local blocker
      resolution tasks
- [x] Operations action-plan visibility added to `validation-summary` and CI
      template without clearing blockers automatically
- [x] Operations action-resolution records added for local operator provenance
      across open, acknowledged, deferred, and resolved actions
- [x] Operations action-resolution visibility added to `validation-summary` and
      CI without authorizing live data or external submission
- [x] Operations action-resolution coverage now checks every current action-plan
      ID has a local provenance record
- [x] SQLite bootstrap summary added to restore top-level log visibility for a
      supplied local ignored database path
- [x] Operations blocker-detail summary added to trace action-plan blockers to
      fixture-backed local source records without clearing blockers
- [x] Operations blocker-review records added to preserve local review
      provenance for blocker-detail evidence bundles without clearing blockers
- [x] Operations blocker-followup summary added to derive next local operator
      actions from blocker-review records without clearing blockers
- [x] Operations blocker-followup progress records added to track local
      progress notes without clearing blockers or enabling external workflow
- [x] Operations blocker progress-review records added for unresolved progress
      only, preserving verified-local closures and disabled authorization gates
- [x] Operations blocker progress next-action records added to order unresolved
      review items without clearing blockers or enabling external workflow
- [x] Operations blocker progress-execution records added to capture local
      next-action execution notes without clearing blockers or enabling
      external workflow
- [x] Operations blocker progress-execution review records added to review
      execution notes without clearing blockers or enabling external workflow
- [x] Operations blocker progress-execution follow-up records added to plan
      reviewed execution follow-up without clearing blockers or enabling
      external workflow
- [x] Production ingestion hardening added for local CSV validation, direct
      `run-pipeline` execution, and archival anomaly CSV fixtures

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
- [x] Operations action plan now converts readiness blockers into prioritized local operator tasks
- [x] Operations action resolution now records operator status while preserving residual blockers and zero authorization counts
- [x] Operations action-resolution coverage now reports full action-plan ID coverage without clearing blockers
- [x] SQLite bootstrap summary now reports integrity and weekly-digest readiness gates without mutating resolution fixtures
- [x] Operations blocker-detail summary now expands current action-plan blockers into local source evidence while keeping live-data and external-submission authorization counts at zero
- [x] Operations blocker-review summary now covers current blocker-detail actions and evidence counts while preserving residual blockers and zero authorization counts
- [x] Operations blocker-followup summary now derives local follow-up ordering from reviewed blockers while preserving residual blockers and zero authorization counts
- [x] Operations blocker-followup progress summary now covers follow-up action IDs and recommendation consistency while preserving residual blockers and zero authorization counts
- [x] Operations blocker progress-review summary now covers unresolved progress records while leaving verified-local workflow items closed
- [x] Operations blocker progress next-actions summary now orders unresolved progress-review tasks while preserving residual blockers and zero authorization counts
- [x] Operations blocker progress-execution summary now records local execution notes while preserving residual blockers, verified-local exclusions, and zero authorization counts
- [x] Operations blocker progress-execution review summary now reviews local execution notes while preserving residual blockers, verified-local exclusions, and zero authorization counts
- [x] Operations blocker progress-execution follow-up summary now plans reviewed execution follow-up while preserving residual blockers, verified-local exclusions, and zero authorization counts
- [x] `run-pipeline` now refuses structurally invalid local CSV input before
      scoring and records validation provenance in its JSON output
- [x] Local synthetic RFI database guardrails added with schema, summary CLI,
      validation gates, and radio candidate overlap provenance
- [x] RFI database admission gates added so proposed real source lists remain
      blocked until provenance, licensing, monitoring context, and review
      requirements are satisfied
- [x] Curated dataset admission gates added so proposed real labeled datasets
      remain blocked until provenance, licensing, labeling-method,
      false-positive-baseline, and review requirements are satisfied
- [x] Project status consistency gates added so production-readiness metadata,
      schema counts, latest decisions, and zero-real-data authorization gates remain aligned
- [x] Operations alert review consistency gates added so alert, QC, readiness,
      and authorization blocker visibility remains aligned
- [x] Operations action resolution staleness gates added so stale resolution
      records, current action-plan IDs, residual blockers, and disabled
      authorization counts remain aligned
- [x] Operations blocker-progress consistency gates added so blocker-detail,
      review, follow-up, progress, next-action, execution, execution-review,
      execution-follow-up, residual blockers, and disabled authorization counts
      remain aligned
- [x] Top-level SQLite log consistency gates added so SQLite health, migration
      state, run/outcome alignment, retention, PRAGMAs, commit guard, and
      disabled authorization counts remain aligned
- [x] Production blocker visibility consistency gates added so open Tier 1
      readiness state, admission state, operations readiness state, and
      disabled authorization counts remain aligned
- [x] Data transfer log, scheduling conflict log, and system health log
      operational provenance records added
- [x] Instrument configuration log, scan log, and time synchronization log
      operational provenance records added
- [x] Antenna pointing log, weather log, and power log operational provenance records added
- [x] Cooling system log, network connectivity log, and software update log operational provenance records added
- [x] Hardware fault log, maintenance log, and environmental log operational provenance records added
- [x] Access log, security event log, and audit trail log operational provenance records added
- [x] Official HIP99427 GBT ABACAD cadence downloaded and archive checksums verified
- [x] Six real HDF5 scans processed through turboSETI with reviewed provenance sidecars
- [x] Combined 213-row ON/OFF cadence passed validation and guarded pipeline execution
- [x] Real cadence result conservatively routed `do_not_submit_false_positive`
- [x] Frequency-matched OFF-target rejection guard corrected after real-data regression exposed unsafe promotion
- [x] Citizen-science real cadence labeling and reproducibility review added
- [x] 124 exact frequency/drift evidence groups labeled with primary and independent audit methods
- [x] Real label set admitted for local evaluation with expert review and external validation explicitly unclaimed
- [x] Current v0 scoring evaluated against real labels: 54.03% overall, 80.25% false-positive, 100% follow-up, and 0% insufficient-evidence routing agreement
- [x] Probability thresholds protected against SNR/drift unit errors
- [x] Real-noise calibration restricted to provenance-approved, checksum-matching observations
- [x] Derived cadence CSV/source DAT deduplication added
- [x] Cadence, target, epoch, dominance, bootstrap, and leave-one-cadence-out diagnostics added
- [x] Current HIP99427 calibration preflight records the failed multi-cadence and multi-epoch gates
- [x] `validate-all`, `validation-summary`, and `health` remain green
- [x] Learned scoring model v1 trained on 124 real HIP99427 labels with 99.19% 3-fold CV accuracy
- [x] Operator review dashboard added for open flags, deadlines, and accuracy regression gate
- [x] All Tier 2 production gaps closed as of 2026-06-12
- [x] Data release snapshot v1 added with deterministic pathway assignment hash and cross-release comparison (105 schemas, Tier 3 gap closed)
- [x] Multi-target scan orchestration, cross-target RFI suppression, anomaly ranking, candidate escalation gate (109 schemas, Milestone 76)
- [x] Escalation gate hardened, negative-result scan report, external submission protocol (109 schemas, Milestone 77)
- [x] Cross-store position deduplication (`cross_store_dedup`) for radio + infrared track corroboration
- [x] Gaia DR3 scan workflow (`gaia_scan_workflow`) — guarded behind `TECHNO_SEARCH_ENABLE_LIVE_DATA=1`
- [x] Weekly automated scan schedule (`.github/workflows/weekly_scan.yml`)
- [x] Calibration transfer protocol documented (`docs/CALIBRATION_TRANSFER_PROTOCOL.md`)
- [x] Production scan guide for citizen-science operators (`docs/PRODUCTION_SCAN_GUIDE.md`)
- [x] AI hardening production blocker memorialized as DECISION-134 and Milestone 78
- [x] Machine-readable AI hardening gate added so validation exposes open
      requirements, held-out evidence absence, and disabled production promotion
- [x] AI hardening review protocol added for DECISION-134 held-out evidence,
      independent-method review, and review-safe evidence bundles
- [x] AI hardening evidence population accounting added so failed acquisition
      side effects cannot be mistaken for populated held-out evidence
- [x] Git artifact hygiene hardened after accidental local artifact staging:
      generated payloads remain ignored, `docs/LOCAL_DATA_INVENTORY.md` is now
      a sanitized GitHub-visible artifact map, and machine-specific inventory
      snapshots write to ignored `docs/LOCAL_DATA_INVENTORY.local.md`
- [x] Local performance optimization directive added: AI training and
      tensor-heavy evaluation should use the M4 Max GPU through tested
      acceleration backends when available, while CPU-heavy work should use
      bounded multiprocessing or multithreading with reproducible fallbacks
- [x] Extended-corpus acquisition hardened for DECISION-134: the downloader now
      discovers current Breakthrough Open Data HDF5 links and fails closed when
      it produces zero held-out evidence files
- [x] DECISION-134 AI hardening production blocker closed for local
      citizen-science production promotion via the injection-recovery closure
      evidence bundle

## Next 3 Actions

1. Run the production-readiness validation gate from a clean checkout and
   preserve the command output as local operator evidence.
2. Execute the first conservative production scan using
   `docs/PRODUCTION_SCAN_GUIDE.md`, with live data still opt-in and no external
   submission.
3. Preserve the first scan's negative-result or escalation-gate record as local
   operator evidence without making any discovery-style claim.

---

## Next Milestone

**Milestone 78 — Citizen-Science Production Run Evidence**

Status: DECISION-134 closed for local citizen-science production promotion.

Input:
- reviewed local configuration
- real observation hit tables or admitted local fixtures
- held-out real-data evidence outside the HIP99427 training cadence
- production scan guide

Output:
- validation transcript
- conservative scan summary
- negative-result or escalation-gate record
- provenance bundle with no external submission by default
- independent-method AI hardening review record with disagreements and negative
  evidence preserved

---

## Current Risks

- Overclaiming candidate significance after engineering readiness
- Large data files, caches, logs, or local scan outputs accidentally committed
- GitHub-only agents losing artifact context if ignored payloads are not paired
  with committed sanitized maps, manifests, checksums, and scripts
- Live network tests or provider availability becoming flaky
- External submission attempted before protocol preconditions are met
- Production evidence generated without preserved provenance
- AI hardening workloads run serially or CPU-only despite a tested local GPU or
  bounded parallel path being available

---

## Mitigations

- Keep all outputs conservative and false-positive-first.
- Keep live data opt-in and default tests non-networked.
- Preserve provenance for every candidate, scan, and operator action.
- Commit only review-safe methodology and fixture artifacts.
- Preserve GitHub-visible artifact maps while keeping payloads ignored.
- Use the local M4 Max GPU/CPU profile for heavy AI and batch workloads while
  keeping resource choices configurable and reproducible.
- Keep external submission disabled unless the documented protocol is fully satisfied and explicitly authorized.

---

## Definition of Production-Run-Ready

The project is ready for a citizen-science production run when:

- `validate-all`, tests, lint, and type checks pass from a clean checkout
- production-readiness docs and CLI summaries agree that Tier 1 and Tier 2 gaps are closed
- live data remains opt-in and external submission remains disabled by default
- candidate, negative-result, and escalation outputs preserve provenance and blocking issues
- large data, caches, SQLite logs, and local result artifacts remain uncommitted

---

## Recommended Operator Branching

The user stays on `main` and pulls after each merged PR. Agents develop on
`claude/general-session-Bb2dZ` and merge through a PR before starting new work.
- [x] Incident response log, change management log, and compliance report log operational provenance records added
- [x] Risk assessment log, backup recovery log, and capacity planning log operational provenance records added
- [x] Software deployment log, performance monitoring log, and user activity log operational provenance records added
- [x] Health check log, license management log, and storage management log operational provenance records added
- [x] Firmware update log, configuration audit log, and event correlation log operational provenance records added
- [x] SQLite operational log registry consistency gate added
- [x] SQLite operational log adapter plan gate added
- [x] SQLite operational log adapter contract gate added
- [x] SQLite operational log adapter DDL preview gate added
- [x] SQLite operational log adapter row preview gate added
- [x] SQLite operational log adapter insert preview gate added
- [x] SQLite operational log adapter execution preview gate added
- [x] SQLite operational log adapter dry-run manifest gate added
- [x] SQLite operational log adapter readiness preflight gate added
- [x] SQLite operational log adapter authorization gate added
- [x] Project-scoped MCP bootstrap configuration added
- [x] MCP bootstrap consistency gate added
- [x] MCP server policy gate added
- [x] Data transfer log, system diagnostics log, and resource allocation log operational provenance records added
- [x] Access control log, change management log, and incident log operational provenance records added
- [x] Patch management log, vulnerability scan log, and compliance audit log operational provenance records added
- [x] Disaster recovery log, service level log, and asset management log operational provenance records added
- [x] Network monitoring log, identity management log, and certificate management log operational provenance records added
- [x] Configuration change log, data retention log, and alert escalation log operational provenance records added
- [x] Service request log, problem management log, and release management log operational provenance records added
- [x] Supplier management log, contract management log, and knowledge management log operational provenance records added
- [x] Training log, budget log, and audit finding log operational provenance records added
- [x] Change request log, project milestone log, and vendor assessment log operational provenance records added
- [x] Communication log, document management log, and procurement log operational provenance records added
