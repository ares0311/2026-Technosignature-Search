# Production Scan Runbook

## STOP — DO NOT CREATE LABELS

This runbook does not authorize any labeling or annotation work. Use only
pre-existing independent row-level labels with provenance for training,
calibration, threshold selection, or evaluation. Never ask the user or anyone
else to label data, and never construct a review queue. Unlabeled scan output
may be ranked and investigated but must remain unlabeled.

**Purpose:** Durable UX rules for operating a continuous, prioritized, history-aware
production scan pipeline. The rules here are project-agnostic and can be adapted to any
pipeline that processes a directory of input files with a CLI tool.

**Scope note:** Rule 4 below governs the **local re-scan scheduler** —
prioritizing already-acquired files sitting in a local directory. It is a
different, narrower scope than the **acquisition-level, detection-optimized
target selection** (which real targets to acquire/download and follow up on
next, across the full real catalog) — see `docs/SYSTEMATIC_SEARCH_PLAN.md`
Step 3 for that plan and its explicit distinction from this rule.

---

## Adversarial PROD-contract audit and v1.2.71 remediation — 2026-07-29

**Pre-remediation verdict:** not PROD under the full Hunter PROD-closure
directive supplied for this audit. The v1.2.69 live new/follow-up searches
remain valid scientific and lifecycle evidence, and the v1.2.70 terminology
delta remains correctly described. They did not, however, constitute one
fresh-state deterministic acceptance run through the installed persistent
Hunter that proved every required business branch on the exact current
implementation.

### Findings

1. The controlled acceptance evidence was fragmented across helper-level and
   fake-backed tests. No single installed `Techno-Hunter` invocation exercised
   slash-command routing, adaptive expansion, validation, exact selection,
   immutable execution, scoring, persistence, restart, and follow-up state.
2. The exact v1.2.70 release had not executed the scientific path. Its evidence
   combined v1.2.69 live searches with a terminology-only hash closure. That is
   useful compatibility evidence, but it is not exact-release end-to-end
   execution.
3. The v1.2.70 evidence contract was not self-contained. Its test deliberately
   ignored absent runtime artifacts, so it could pass in a fresh checkout
   without re-verifying the named search state.
4. No fresh-state installed-CLI acceptance run faulted and resumed the exact
   same pending follow-up search while proving no duplicate result, history, or
   lifecycle transition.
5. `CandidateStore` and its three CLI commands were a disconnected duplicate
   persistence path outside the canonical Hunter lifecycle. Its SQLite
   connections were not durably closed by callers and emitted 67
   `ResourceWarning`s under Python 3.14 during full validation.

These findings revoke reliance on the earlier bounded PROD declaration until
the remediation evidence below is generated and passes. They do not invalidate
the immutable v1.2.69 live-source smoke or authorize another raw download.

### Remediation plan

1. Add one deterministic, fresh-state acceptance mode to the installed
   persistent `Techno-Hunter` entry point.
2. Route it through the production CLI parsers, adaptive selector, immutable
   search lifecycle, stream/process/evict runner, turboSETI, candidate
   pipeline, production interpretation, history, follow-up lifecycle, and
   restart reads. Replace only the external archive transport with a loopback
   controlled adapter.
3. Make controlled fixture provenance explicit and fail-closed outside the
   dedicated acceptance process. Never represent controlled bytes as real
   observations, labels, or scientific performance evidence.
4. Seed the contract cases in one controlled universe: a best target beyond the
   initial partition, a weak best-available target, invalid and
   refresh-required exclusions, an alias, a prior-search exclusion, an exact
   manifested/executed target, and a follow-up whose first execution fails and
   resumes.
5. Emit one portable JSON evidence bundle containing the request, discovery
   coverage, validity report, provenance chain, ranking evidence, exact
   selections, search events, follow-up state, assertions, embedded durable
   records, release identity, and no-claim flags.
6. Delete the disconnected `CandidateStore` implementation and CLI surface.
7. Run focused regression tests, the installed acceptance command, the
   repo-native full validator, then require green PR CI before restoring the
   exact-release PROD statement.

### Implemented v1.2.71 closure path

The implementation is complete locally. The installed command is:

```bash
.venv/bin/Techno-Hunter \
  --acceptance-work-dir /tmp/techno-hunter-v1-2-71 \
  --acceptance-evidence docs/evidence/hunter_v1_2_71_controlled_acceptance.json
```

The command refuses a nonempty work directory and classifies its generated
radio input as `controlled_acceptance_fixture`. That classification is admitted
only while `TECHNO_CONTROLLED_ACCEPTANCE=1` is scoped inside the dedicated
acceptance process; it is rejected by default, cannot authorize real-data use,
and cannot authorize external submission. The normal real-observation
admission contract remains unchanged.

The acceptance executes one new and one follow-up search through the real
persistent slash-command router. It uses real adaptive score-bound expansion,
real immutable manifests/events, the real stream/process/evict shell runner,
turboSETI 2.3.2, the real radio pipeline and known-explanation resolution, the
production composite interpreter, append-only history, follow-up dispositions,
and restart reads. The follow-up runner returns exit 9 once, then resumes the
same search and run. The external archive is the only replacement: a bounded
loopback HTTP server supplies the controlled HDF5.

The first Linux/Python 3.11 CI execution exposed one additional production
defect before closure: the pinned turboSETI 2.3.2 implementation formats its
one-element `total_n_hits` array as an integer and raises `TypeError` after the
search. A developer environment had an untracked one-character site-package
correction, so Python 3.14 local acceptance did not expose the defect. Worse,
the stream runner continued from the partial zero-row `.dat`, produced a
zero-hit manifest, evicted the raw HDF5, and counted the target complete.

The v1.2.71 remediation now applies the exact scalar-index correction in
memory, fails closed if the pinned dependency source is neither the known
vulnerable nor corrected form, and treats any turboSETI or candidate-pipeline
failure as a failed target. Partial `.dat` output is removed, raw HDF5 is
retained, collection status records the failure, and the batch returns
non-zero. This closes the hidden-environment and partial-success paths without
changing scientific thresholds or treating a controlled injection as a label.

`src/techno_search/candidate_store.py` and the
`candidate-store-init`/`candidate-store-summary`/`candidate-store-list`
commands are removed. The canonical search manifest, append-only event ledger,
target-status ledger, history, and follow-up registry remain the only Hunter
persistence path.

**Closure state:** closed locally for v1.2.71. The installed command passed on
clean implementation commit `edb6e66` and wrote
`docs/evidence/hunter_v1_2_71_controlled_acceptance.json`. Both modes selected
`OUTSIDE`; new emitted `created`, `run_started`, `run_completed`; follow-up
emitted `created`, `run_started`, `run_failed`, `run_resumed`,
`run_completed` with one unchanged run ID. All 14 contract assertions passed,
two completed searches appended exactly two history rows, and no controlled
HDF5 remained.

Focused archive/fail-closed tests passed (94 tests), the combined Hunter
lifecycle/archive slice passed (125 tests), and the documentation/directive
slice passed (40 tests). The exact installed acceptance also passed under the
CI-matching Python 3.11 dependency set. Finally,
`caffeinate -i .venv/bin/python scripts/run_parallel_validation.py` passed
with 1,684 tests, seven skips, Ruff, mypy, app-version, `validate-all`,
directive-parity, and no-fake-completion green. PR CI and merge remain the
release gate; this closure is effective on green merge to `main`.

## Hunter PROD Acceptance Closure Loop — 2026-07-26

**Status:** Closed for the bounded Hunter PROD threshold on 2026-07-29.
Every required business scenario below has current, real,
installed-entry-point evidence. The wider scientific search loop remains
active and does not authorize labels, detection claims, expert contact, or
external submission.

**Closed phase:** Phase 1/5 integrated Hunter acceptance and
`SYSTEMATIC_SEARCH_PLAN.md` Step 3a/3b production mechanics. Learned
anomaly-score calibration remains ranking context, not a prerequisite for
deterministic `known` / `unknown` / `unresolved` routing or best-available-N
selection.

**Root cause of the premature stop:** release-remediation completion was
incorrectly treated as product completion even though PR #316 explicitly left
the positive-count current-release new-target run and qualifying follow-up
evidence open.

### Closure matrix

| Required business behavior | Current evidence | State required to close |
|---|---|---|
| Adaptive new-target discovery finds a displacing candidate outside the initial discovery sample | **Closed for v1.2.65:** installed search `SEARCH-20260728T042942Z-7572B240` selected and executed HIP61099 from real archive evidence with no synthetic output | Reconfirm on the exact final release only if selection/execution behavior changes |
| Weak absolute quality still returns best-available N | Real shortfall/exhaustion runs and low-score regression coverage | Closed unless the final real runs contradict it |
| Positive-count new-target lifecycle | **Closed:** canonical v1.2.69 search `SEARCH-20260729T055045Z-125D2215`, run `RUN-2026-07-29_055553Z-YI5F-hunter-search`, selected HIP3419 from 4,862 viable candidates, completed approved acquisition -> preprocessing -> scoring/interpretation -> one durable history row and follow-up registration, and evicted raw HDF5 | Preserve the immutable evidence and keep single-scan cadence absence loudly `unresolved` |
| Follow-up selection and execution | **Closed:** canonical v1.2.69 search `SEARCH-20260729T055057Z-7321B0CB`, run `RUN-2026-07-29_055650Z-G60U-hunter-search`, verified a six-scan later-epoch HIP103039 cadence, completed 10/10 known-explanation checks, reached local `unknown`, wrote the adversarial dossier, consumed eight originating follow-ups, appended history once, registered the next local action, and evicted all raw HDF5 files | Preserve `unknown` as a local exhausted-known-checks state and keep the Earth-drift blocker fail-closed |
| Restart/resume integrity | **Implementation proof for v1.2.62:** controlled cadence failure at exit 7 resumes the same search/run and byte-identical derived execution manifest, then completes with exactly one history/lifecycle transition | Repeat through the real bounded acquisition or leave the test-scoped limitation explicit if no safe deterministic real fault point exists |
| Validation/provenance/identity/history | v1.2.61 manifest authentication, source hashing, validity states, alias resolver, real EXO import | Closed unless live acceptance exposes a contradiction |
| No production bypass | Stream runner and direct downloader fail-closed tests | Re-audit every raw-acquisition command after final changes; all production commands must consume an authenticated durable search |
| Exact release verification | **Closed:** `docs/evidence/hunter_v1_2_70_acceptance.json` binds fifteen runtime hashes, exact lifecycle counts, collection status, raw eviction, idempotent completed-search refusal, the real `unresolved` and `unknown` branches, automatic adversarial review, and no-claim flags. v1.2.70 changes only the stale terminal-summary scope wording exposed by the exact v1.2.69 run. | Keep the evidence contract in CI and rerun bounded live acceptance only when selection/execution science changes |

### Execution loop

1. **Prepare without raw-data authority.** Rebuild current decision inputs,
   inspect durable history/status, run adaptive metadata discovery and HEAD
   preflight, identify the smallest scientifically valid new and follow-up
   acceptance searches, and record exact targets, products, roles, byte totals,
   storage headroom, and eviction rules.
2. **Request only the irreducible approval.** If a later release changes
   selection/execution science and reopens bounded acceptance, and raw data are
   required, pause
   only long enough to request approval for the exact bounded manifests. An
   approval pause leaves that reacceptance loop active; it is not a completion
   handoff.
3. **Execute exact durable searches.** Use installed `Create-New-Search` and
   `Run-New-Search`; never substitute a direct pipeline call. Preserve every
   selected target, acquisition attempt, transformation, score,
   interpretation, result, and history/follow-up transition.
4. **Exercise recovery.** Interrupt or fault-inject one bounded current-release
   attempt at a safe resumable boundary, resume the same durable search/run,
   and prove history/results are appended exactly once.
5. **Falsify after every result.** Compare the artifact to this matrix, find
   the highest-impact remaining gap, fix its root cause, run focused tests, and
   repeat. Do not broaden into labels, speculative model work, operational
   scaffolding, or external submission.
6. **Close only on exact evidence.** Run the repo-native parallel validator on
   the clean final commit, merge via green PR, sync the agent branch to
   `origin/main`, pass `check_verification_freshness.py`, and update this matrix
   with immutable search/run IDs and artifact hashes. Declare PROD only when
   every row is green.

### v1.2.69 exact execution and v1.2.70 closure

- New search `SEARCH-20260729T055045Z-125D2215` selected HIP3419 from
  6,879 queued and 4,862 viable candidates, downloaded the exact
  237,996,056-byte product, processed it with turboSETI 2.3.2, persisted one
  result/history/follow-up, and evicted the raw HDF5. The result is
  `unresolved` because its single scan cannot establish OFF-target absence.
- Follow-up search `SEARCH-20260729T055057Z-7321B0CB` selected HIP103039 with
  eight prior project searches, acquired the exact six-scan ABACAD cadence
  (1,455,568,892 bytes), preserved archive MD5 and per-scan provenance,
  produced a 72-row derived cadence table, and evicted all six raw files. The
  strongest surviving frequency/drift group appears in all three ON scans and
  zero OFF scans. All ten known-explanation checks completed, so the local
  state is `unknown`; its automatically generated adversarial dossier still
  blocks expert escalation on Earth-drift inconsistency.
- Both searches contain exactly `created`, `run_started`, and `run_completed`
  events and exactly one history append. Re-running either returns non-zero
  and leaves event and history counts unchanged.
- `Show-Follow-Ups` resolves HIP3419 and HIP103039, preserves prior provenance,
  and reports distinct actionable next steps. No output authorizes detection,
  discovery, expert review, external validation, or submission.
- Falsification found one stale citizen-science phrase in the terminal summary.
  Version 1.2.70 changes it to local production-triage scope and locks the
  correction with a regression test; scientific and lifecycle logic are
  unchanged.

### Approval and safety boundaries

- Metadata/catalog discovery, HEAD size preflight, durable search creation,
  focused tests, failure injection that does not corrupt evidence, and
  read-only sibling-history validation proceed autonomously.
- Raw public-archive acquisition requires explicit approval of the exact
  bounded manifest. `stream_process_evict` is mandatory under the permanent
  100GB project cap; projected free space must remain at least 10GB.
- No labeling, external scientific contact/submission, destructive cleanup, or
  fabricated identity/evidence is authorized by this loop.

### v1.2.64 live execution result and v1.2.65 checkpoint

The operator approved exactly the two v1.2.64 searches below:

- `SEARCH-20260728T041138Z-807379F8` completed as
  `RUN-2026-07-28_041452Z-BL8R-hunter-search`. HIP60759 produced an
  `unresolved` result because the single scan lacks complete ON/OFF cadence,
  appended history once, registered one follow-up, and evicted the raw HDF5.
- `SEARCH-20260728T041142Z-9D498DFF` completed as
  `RUN-2026-07-28_041604Z-RNMS-hunter-search`. Six checksum/provenance-bound
  HIP99427 later-epoch scans resolved `known` from the failed cadence
  condition, consumed `FU-2026-07-26_011410Z-P54N-001` exactly once, appended
  one history row, emitted no replacement follow-up, and evicted all six raw
  HDF5 files.
- Both immutable searches contain one created, one started, and one completed
  event with no failure; attempting to rerun either exits non-zero. The
  registry reports one completed follow-up and neither target remains eligible
  or scheduled.
- Falsification found a separate release defect: candidate reports still
  generated and labeled synthetic placeholder SVGs. Version 1.2.65 removes
  those fake visualizations and the radio candidate placeholder field. It
  renders only persisted numeric feature evidence and omits unsupported plots.

The v1.2.64 outputs remain immutable. After v1.2.65 merges and passes canonical
validation, create fresh immutable installed-entry-point searches, preflight
their exact products, obtain exact approval, and repeat the acceptance
lifecycle before closing Hunter PROD.

### Historical v1.2.63 execution result and v1.2.64 approval checkpoint

The operator approved exactly the two v1.2.63 searches below. That approval
did not authorize replacement manifests or a broader acquisition:

- `SEARCH-20260728T035648Z-A9FE6463` completed as
  `RUN-2026-07-28_040023Z-ZKN8-hunter-search`. It downloaded the exact
  242,170,450-byte KIC8462852 product, ran turboSETI 2.3.2, persisted scorer
  and interpretation provenance, evicted the raw HDF5, appended search history
  once, and registered a deterministic follow-up. The result is `unresolved`
  because complete ON/OFF cadence evidence is absent; it is not a detection,
  positive label, or external-submission authorization.
- `SEARCH-20260728T035656Z-F3762970` started as
  `RUN-2026-07-28_040147Z-DFBQ-hunter-search`. It selected the current
  deterministic best follow-up, GJ699, downloaded and processed the first
  ABACAD scan, then exited non-zero in
  `follow_up_cadence_acquisition_preprocessing` with
  `KeyError: 'observation_summary_url'`. The run is durably `failed` and
  resumable; it was not marked complete and produced no follow-up completion.
  The raw first scan remains locally available for verified reuse.
- Root cause: archive-discovered cadence manifests validly carry
  `archive_search_url` but not the legacy static-manifest-only
  `observation_summary_url`; the provenance writer indexed the latter
  unconditionally. Version 1.2.64 treats both source URLs according to the
  validated schema and preserves whichever evidence is present.

Because this fix changes release logic and the failed manifest pins v1.2.63
and commit `15f7702`, the old failed search must not be resumed under v1.2.64.
After v1.2.64 merges and passes canonical validation, the next action is to
create a new immutable follow-up search (and, if exact-final-release closure
requires it, a smallest valid new-target search), perform URL/size/storage
preflight, and request exact approval for those replacement products.

### Historical v1.2.62 pre-execution checkpoint

Release 1.2.62 metadata and implementation evidence as of
2026-07-26T01:51Z:

- **Unreachable follow-up completion fixed at the root.** The old manifest
  hard-coded `follow_up_observation_fulfilled: false`, while no production
  component emitted either completion field checked by the lifecycle resolver.
  Follow-up creation now discovers a provenance-complete later epoch; the
  installed runner derives an approved execution input only after
  `--approve-acquisition`, executes it before the canonical scorer, and marks
  completion only after the exact six frozen inputs appear in a checksum-bound
  derived cadence artifact. Reanalysis remains deferred.
- **Clean implementation identity:** both approval-pending manifests name
  version `1.2.62` and code commit `de143ef`; no raw execution will use the
  earlier dirty-tree provisional searches, which were moved intact to a
  recoverable `/tmp` quarantine.
- **Real follow-up selection:** `SEARCH-20260726T015438Z-1881A999` selected
  HIP99427 at follow-up priority `0.992456` and froze GBT archive products in
  ABACAD order from MJD `57885.3570` through `57885.3763`. The prior retained
  cadence ends at MJD `57752.981088`; the new epoch begins `132.375912` days
  later. Exact projected acquisition is `1,449,661,910` bytes (`1.449662 GB`).
- **Real adaptive new-target selection:**
  `SEARCH-20260726T015515Z-5C71AC51` constrained the request to KIC targets.
  KIC8462852 was outside the initially eligible sample, so the installed
  command executed one discovery round, found and HEAD-preflighted the current
  `.gpuspec.0002.h5` product, exhausted the constrained universe, and selected
  it as best available. Exact projected acquisition is `242,170,450` bytes
  (`0.242170 GB`).
- **Freshness/storage preflight:** all seven frozen URLs returned HTTP 200 and
  exact matching `Content-Length` values at 2026-07-26T01:51Z. The workspace
  filesystem had `325 GiB` available; tracked/ignored project science payload
  classes occupied about `10.8 GiB`, leaving ample headroom under both the
  permanent 100GB project cap and 10GB free-space reserve. Both runs use
  `stream_process_evict`.
- **Approval gate proved:** invoking installed `Run-New-Search` for either
  search without `--approve-acquisition` exited `2` before downloading raw
  bytes. No raw payload has been acquired for either acceptance search.
- **Focused verification:** 46 Hunter/follow-up/cadence tests pass; Ruff passes
  for every changed implementation/test file; mypy passes for the changed
  packaged Hunter modules. The controlled failure/resume regression preserves
  the byte-identical derived cadence manifest and reaches one completed
  disposition only after verified cadence provenance exists. The repo-native
  six-shard validator also passes on this working tree: 1,684 passed, seven
  skipped; Ruff, mypy, app-version gate, and `validate-all` passed. Because the
  tree is not yet committed, the exact-commit freshness marker and CI remain
  open.

Exact pending bounded approval scope:

| Search | Purpose | Files | Bytes | GiB (bytes / 2^30) |
|---|---|---:|---:|---:|
| `SEARCH-20260726T015515Z-5C71AC51` | new KIC8462852 search | 1 | 242,170,450 | 0.226 |
| `SEARCH-20260726T015438Z-1881A999` | HIP99427 later-epoch ABACAD follow-up | 6 | 1,449,661,910 | 1.350 |
| **Total** | current-release positive-count acceptance | **7** | **1,691,832,360** | **1.576** |

The next loop action is the irreducible human gate: explicit approval (or
denial) of those two immutable searches. Approval authorizes only their seven
listed public archive products and does not authorize labels, external
submission, broader acquisition, or retained raw hoarding.

---

## Hunter PROD Remediation Plan — 2026-07-25

**Status:** Implementation merged in PR #316 and verified on release 1.2.61.
This is implementation evidence only. It does not supersede the active PROD
acceptance closure matrix above.

**Current phase advanced:** Phase 1/5 integrated Hunter lifecycle and
`SYSTEMATIC_SEARCH_PLAN.md` Step 3a detection-optimized target selection. This
plan closes workflow-integrity gaps in the existing scientific path; it does
not create labels, alter learned-model promotion, claim a detection, authorize
external submission, or authorize a large raw download.

### Root causes and remediation loop

1. **Canonical adaptive discovery**
   - Root cause: `Create-New-Search` ranks only the current queue and reports a
     manual discovery/preflight command when the queue is short; the prior
     "adaptive" acceptance manually ran disconnected tools.
   - Remediation: make the installed new-search command own a bounded,
     metadata-first discover -> validate -> identity/history resolve -> rank ->
     sufficiency -> expand loop. Reuse existing discovery, HEAD-only size
     preflight, queue construction, provenance, rate-limit, and 100GB policies
     rather than duplicating them. Preserve deterministic ordering and
     checkpoint every completed expansion round.
   - Acceptance: a test candidate ranked outside the initial pool enters the
     final top-N after automatic expansion; a weak-quality pool still returns
     best-available N; fewer than N is allowed only after the configured
     reasonably accessible universe is exhausted or no valid expansion
     headroom remains.

2. **Durable-search acquisition authentication**
   - Root cause: the stream runner treats a copied Hunter schema string as
     proof that a manifest came from `Create-New-Search`, while the direct
     downloader remains a raw-acquisition bypass.
   - Remediation: validate the immutable manifest against its sibling
     `events.ndjson` creation record and SHA-256, require the canonical
     `results/searches/SEARCH-*/manifest.json` topology and artifact contract,
     and make every raw acquisition route require that validation. Metadata-only
     discovery remains separately callable; raw download mode does not.
   - Acceptance: a hand-built manifest with a copied schema is rejected; a
     modified durable manifest is rejected; a genuine created search is
     accepted; direct raw-download invocation without a durable search fails
     non-zero.

3. **Cross-project history validity**
   - Root cause: every imported sibling entry, including `failed` and
     incomplete/no-data attempts, currently reduces novelty; timestamps,
     freshness, source checksums, and validity are not enforced.
   - Remediation: admit only statuses that constitute applicable completed
     prior-search evidence, classify each source/entry as `valid`,
     `stale-but-usable`, `refresh-required`, `invalid`, or `unknown`, require
     timestamps and provenance fields, verify source hashes where the export
     contract permits, and fail closed on refresh-required/invalid inputs.
   - Acceptance: failed attempts never change ranking; stale-but-usable
     evidence remains visible and auditable; malformed, unknown, invalid, or
     refresh-required inputs cannot drive selection.

4. **Follow-up lifecycle fulfillment**
   - Root cause: follow-up execution is currently evidence reanalysis with
     `follow_up_observation_fulfilled` hard-coded false, yet completion appends
     another recommendation without a durable open/scheduled/completed/deferred
     disposition or consuming-search relationship.
   - Remediation: preserve reanalysis as a distinct action; add deterministic
     lifecycle state derived from existing ledgers and search events; schedule
     selected open follow-ups to the consuming search; complete only when the
     acquired evidence satisfies the recorded observation requirement; defer
     explicitly when it cannot be fulfilled. Do not imply a new observation
     from archive reuse.
   - Acceptance: selecting a follow-up makes it `scheduled`; a failed/resumed
     run preserves the same consuming search; reanalysis leaves it open or
     deferred; qualifying later-epoch evidence closes it exactly once and
     removes it from future open selection.

5. **Scalable identity resolution**
   - Root cause: every follow-up entry sorts all queue target IDs and compiles
     one regex per ID, producing superlinear production latency.
   - Remediation: build one deterministic alias/index structure per queue or
     manifest, reuse it for every lookup, preserve boundary-safe longest-match
     semantics, and expose unresolved/ambiguous identities without guessing.
   - Acceptance: correctness remains pinned for HIP/GJ/HD/BD/TIC names,
     ambiguity fails closed, and the real 6,879-target/retained-ledger registry
     completes within a bounded regression budget.

6. **Truthful release state**
   - Root cause: v1.2.60 completion claims and control-plane additions were
     written before the product contract was satisfied, and the work was never
     committed or verified as an exact release.
   - Remediation: remove unsupported PROD/shadow-closure/adaptive-acceptance
     claims; do not restore or expand MCP/Claude control-plane scaffolding when
     the product CLI already supplies the required read-only bridge; keep
     README, readiness, systematic plan, runbook, and version files consistent.
   - Acceptance: `git add --dry-run .` is artifact-safe; focused business
     validations and `caffeinate -i .venv/bin/python
     scripts/run_parallel_validation.py` pass on a clean commit; CI passes; the
     PR records objective, decisions, evidence, limitations, and exact next
     work; the merge is synced back to `main`.

### Execution rule

Execute the list above in highest-business-impact order. After each change,
rerun the smallest real or realistic acceptance that can falsify it, then
re-map the canonical path before continuing. A green unit suite is necessary
but cannot substitute for the new-target, follow-up, provenance, bypass, and
restart/resume business validations above. Stop only for an explicit
large-download approval, destructive action, credential failure, protected
external action, or a scientifically irreducible evidence gap.

### Remediation execution evidence

Release 1.2.61 implementation evidence:

- **Adaptive selection:** installed `Create-New-Search` automatically examined
  four initially unresolved TIC candidates, discovered four current archive
  URLs, HEAD-preflighted them, and selected the best constrained two in
  `SEARCH-20260726T005918Z-1FC2C8E1`. The round manifest, result, preflight,
  queue, and SHA-256 values are embedded in the immutable search manifest.
  On committed code `08bcb39`, durable request
  `SEARCH-20260726T011336Z-CCA7E409` explored the complete constrained LHS
  universe, found zero valid products, returned zero of one without an
  arbitrary threshold failure, and completed durably with
  `no_valid_targets: true`. A stale discovered URL that returned HTTP 404 is
  now `metadata_refresh_required`, not endlessly retried or silently accepted.
- **Weak quality:** adversarial tests use scores `0.01` and `0.001`; both are
  returned for N=2 and reported as relative, uncalibrated ranking quality.
- **Acquisition authority:** the stream runner accepts only canonical
  `SEARCH-*/manifest.json` plus its matching creation event/hash. Both a
  target-priority manifest and a schema-spoofed Hunter JSON are rejected.
  The direct downloader exits non-zero for raw mode unless explicitly marked
  `--calibration-corpus`; that mode is not a Hunter production path.
- **History validity:** the current real EXO sibling export loads in 0.10
  seconds with seven verified sources and 608 entries. Exactly 202 completed,
  hash-valid entries can affect ranking; 406 failed/no-data attempts are
  classified invalid and excluded. Hash mismatch is refresh-required and
  fails closed.
- **Follow-up lifecycle:** on committed code `08bcb39`,
  `SEARCH-20260726T011409Z-39A09771` executed exact
  retained HIP99427 evidence with zero raw downloads as
  `RUN-2026-07-26_011410Z-P54N-hunter-search`. Its source follow-up became
  scheduled, then deferred exactly once because no explicit later-epoch
  cadence evidence existed; the completion event preserves the consumed
  follow-up ID and reason. The live 6,879-target/3,833-entry registry now
  resolves in 1.3 seconds instead of exceeding 90 seconds.
- **Validation:** 111 focused Hunter/queue/downloader/docs tests passed; Ruff
  and mypy passed for every changed Hunter module. The full repo-native
  six-shard validator passed on the exact release tree (1,677 tests passed,
  seven skipped; Ruff, mypy, app-version gate, and `validate-all` passed).
  PR #316 merged through green CI as commit `b20bd82908c9a7e9c142361a7eec045b3d3d00c8`;
  the post-merge freshness marker names the same commit.

---

## The Five Rules of Correct Production Scan Orchestration

These rules were derived from operational failures observed when running `run_production_scan.sh`.
Each rule fixes a concrete class of bug.

### Rule 1 — The scan script must acquire new data, not just report on old data

**Anti-pattern:** A "scan" script that only reads already-processed results and
reports on them. This produces the same output every run even if new input files
have been added.

**Correct pattern:**
1. Accept a `--dat-dir` (or equivalent) argument pointing to the raw input file directory.
2. Discover all input files at runtime with `discover_dat_files(dat_dir)`.
3. Call the actual pipeline (`run-pipeline` or equivalent) on each selected file.
4. Write pipeline output to a separate `--output-dir`.
5. After all targets are processed, run post-processing (scan-summary, RFI flagging,
   escalation gate, dashboard) over the output directory.

Post-processing is a separate step that runs *after* acquisition.

### Rule 2 — Every scan of a target must carry a stable cross-run identity

**Anti-pattern:** Generating a new scan index (e.g., `NEG-RUN1-001`, `NEG-RUN2-001`)
each run, making it impossible to tell whether two scan entries refer to the same
physical target observation.

**Correct pattern:**
- The **target stem** (filename without extension, e.g., `HIP99427`) is the stable
  cross-run identity. It is derived from the input file name and never changes.
- The **run ID** identifies a single execution of the scan script. It changes each run.
- The **scan index** (e.g., `20260620-143022-HIP99427`) is a convenience label for
  display only. It encodes timestamp + target stem and is never used as a database key.
- Store target-level history keyed by `target_stem`, not by run-scoped index.

### Rule 3 — The scan must detect already-searched targets and handle re-scans explicitly

**Anti-pattern:** Processing the same target on every run, with no awareness that it
has been seen before.

**Correct pattern:**
1. Maintain a **scan history file** (`results/scan_history.ndjson`) — an append-only
   NDJSON file where each line records one completed scan:
   ```json
   {"target_stem": "HIP99427", "run_id": "PROD-RUN-001", "scanned_at_utc": "...",
    "score": 0.72, "pathway": "follow_up", "dat_file": "/data/HIP99427.dat",
    "parent_run_id": null}
   ```
2. Before selecting a target, check the history. If the target has been scanned before:
   - In one-shot mode (default): skip it (queue only contains never-scanned targets).
   - In `--force-rescan` mode: include it at lower priority and set `parent_run_id`
     to the current `run_id` to link the two scans together.
3. The `parent_run_id` field creates a chain: given any scan record, follow
   `parent_run_id` links to see the full search history for that target.

### Rule 4 — The target selection algorithm must be visible at runtime

**Anti-pattern:** Scanning targets in filesystem order or silently skipping targets,
with no explanation printed to the terminal.

**Correct pattern:**
1. Use a **selection score** that is computed and printed for every target in the queue:
   - Base score: `0.50`
   - First-scan bonus: `+0.08` (targets never seen before get priority)
   - Re-scan penalty: `-0.04` per prior scan, capped at `-0.12`
2. Before the scan loop starts, print the full ranked queue with selection scores and
   rationale strings, e.g.:
   ```
   [ 1]* HIP99427    score=0.5800  (never scanned +0.08 boost)
   [ 2]* HIP17147    score=0.5800  (never scanned +0.08 boost)
   [ 3]  Voyager1    score=0.4600  (scanned 1 time  -0.04 penalty)
   ```
3. Each target selected by the loop prints its rationale before processing begins.

The selection algorithm is defined in `src/techno_search/prod_scan_queue.py` and
surfaced via `techno-search prod-target-queue`.

### Rule 5 — The scan must run continuously until stopped, not exit after a finite queue

**Anti-pattern:** A scan script that exits after processing a fixed list of targets.
This makes the script useless for monitoring newly deposited data files.

**Correct pattern:**
1. Wrap the target selection and pipeline call in a `while true` loop.
2. Trap `SIGINT` and `SIGTERM` at the top of the script:
   ```bash
   STOPPING=0
   trap 'STOPPING=1; warn "Stopping after current target..."' INT TERM
   ```
3. Check `STOPPING` at the top of each loop iteration.
4. When the queue is exhausted:
   - **One-shot mode** (default): print a summary and exit normally.
   - **Continuous mode** (`--continuous`): sleep for `POLL_INTERVAL` seconds and then
     rebuild the queue, picking up any newly added input files.
5. Never use `exit` inside a pipeline sub-process; return exit codes to the wrapper.

---

## CLI Architecture

These CLI commands implement the runbook rules:

| Command | Purpose |
|---|---|
| `techno-search prod-target-queue --dat-dir PATH [--history-file F] [--force]` | Show ranked queue with selection scores and rationale |
| `techno-search prod-record-scan --target-stem T --run-id R --score S --pathway P --dat-file F --history-file H [--parent-run-id ID]` | Append a completed scan record to the history NDJSON |
| `techno-search scan-history-summary [--history-file H] [--dat-dir D]` | Show all prior scans; count pending targets |
| `techno-search prod-scan INPUT_DIR OUTPUT_DIR [--track radio] [--force]` | Single-run batch scan with Rich spinner (does not use history) |
| `techno-search prod-file-scan INPUT_DIR OUTPUT_DIR [--track TRACK]` | Per-file spinner scan; each completed line includes index, target kind, score, follow-up yes/no, and pathway |
| `techno-search prod-runs [--scans-dir PATH] [--json]` | Pick a prior run from compact unique-target and outcome-record counts; use `--json` for the machine-readable summaries |
| `techno-search prod-target-status [RUN_DIR | --latest] [--json]` | Review compact per-target rows by default; use `--json` for the full target-status ledger |
| `techno-search prod-follow-ups [RUN_DIR | --latest] [--json]` | Review compact follow-up rows by default; use `--json` for the full follow-up ledger |
| `techno-search prod-non-detections [RUN_DIR | --latest] [--json]` | Review compact non-detection rows by default; use `--json` for the full non-detection ledger |
| `techno-search review-dashboard [--run-dir RUN_DIR | --results-dir RESULTS_DIR]` | Review compact operator action counts from a run or active candidate manifests; exit 1 only when follow-up pathways need attention |
| `techno-search run-pipeline FILE TRACK OUTPUT_DIR [--semisupervised-model PATH]` | Process one input file through the pipeline; radio packets use the default local fitted scorer model when present |
| `techno-search radio-real-corpus-summary --dat-dir PATH [--dat-dir PATH2] [--hit-ndjson PATH] [--candidate-sample-limit N]` | Summarize local real `.dat` and normalized hit-NDJSON evidence for drift, cross-target RFI recurrence, fitted scorer integration, and bounded candidate-review survivors |
| `techno-search meerkat-frequency-neighbor-summary --raw-json PATH --frequency-hz HZ [--frequency-hz HZ2]` | Stream the complete local MeerKAT JSON/JSON.gz source for explicit ±500 Hz candidate-frequency neighbors without materializing another normalized corpus |
| `techno-search track-b-candidate-readiness CANDIDATE_JSON [--crossmatch-json CROSSMATCH_JSON] [--satellite-json SATELLITE_JSON]` | Fail-closed audit of whether a real candidate packet has the packet metadata and explicit evidence needed for Track B gate review; it never guesses missing sky position, observation time, telescope location, or catalog classifications |
| `techno-search track-b-unknown-candidate-gate CANDIDATE_JSON --crossmatch-json CROSSMATCH_JSON [--satellite-json SATELLITE_JSON]` | Combine explicit Track A crossmatch, optional satellite-match, RFI/artifact/cadence/anomaly/provenance evidence into the Phase 4 `unknown_candidate` gate without network lookups |
| `techno-search validate-all` | Must pass before any scan proceeds |

Candidate Markdown/JSON reports include an `operator_review` block that states
the recommended pathway, whether local follow-up review is required, the
operator action, and the guardrails (`detection_claimed: false`,
`external_submission_allowed: false`).
Production review dashboards now use `operator_review_dashboard_v1` and expose
`follow_up_required_count`, pathway-specific counts, cross-target RFI flag
counts, top follow-up targets, and operator action items without dumping raw
machine JSON into the terminal.

---

## Track A Known-Explanation Gate

`docs/technosignature_datasets_agent_brief.md` is the authoritative handoff for
the next model-hardening milestone. Before any production path emits a Track B
`unknown_candidate` label, the project must have a tested Track A baseline that
classifies or rejects known explanations: pulsars, FRBs, blazars/AGN, known
gamma-ray sources, satellite/transmitter matches, terrestrial RFI, instrument
artifacts, and noise.

Current status: versions 1.2.44-1.2.45 integrate the Track A catalog and satellite
components into the production radio runner and removes learned anomaly
calibration from the known/unknown decision. The retained real corpus verifies
`known` and `unresolved`; `unknown` and its automatic adversarial dossier are
dispatch-tested, but no retained real cadence-complete observation can yet
exercise that branch through an installed Hunter run. PROD remains open on
that real acceptance evidence, not on learned-score calibration.

Installed-path evidence: retained-data follow-up
`SEARCH-20260722T012732Z-759A1D93` completed from code commit `10dfb9e` without
a download and durably
propagated HIP103096 as `unresolved` through its candidate report, report
manifest, scan summary, target-status ledger, and follow-up registry. The
originally exposed three unresolved checks. Version 1.2.45 closes the discarded
archive/instrument and detector-threshold provenance bridges: an exact
committed-manifest HDF5 filename match recovers GBT identity, and a validated
hit-bearing turboSETI DAT proves detector-threshold passage. A fresh direct
HIP103096 run leaves only ON/OFF cadence unresolved. This does not substitute
for the required real `unknown`/adversarial acceptance.

Every hit-bearing radio run must durably finish as exactly one of:

- `known`: a completed check supplies a reliable known explanation;
- `unknown`: all required known-explanation checks completed and none matched;
- `unresolved`: no known explanation was found but at least one required check
  or input was unavailable.

Anomaly/OOD scores are optional ranking evidence and never decide this state.
The same `run-pipeline` path used by `Run-New-Search` must execute the checks,
persist the state and exact evidence, and automatically write an adversarial
dossier for `unknown`. Running sidecar CLI commands manually is not an
acceptable bridge. Until dispatch-level and installed-Hunter acceptance tests
prove this behavior, the Hunter workflow is not PROD.
The v1.2.69/v1.2.70 evidence recorded at the top of this runbook now satisfies
that condition.

Track A acquisition work must follow the brief's source order and disk cap. Raw
downloads and temporary extraction products stay local in ignored paths:
`data_cache/`, `tmp_training/`, `tmp_features/`, `artifacts/`, `models/`, and
`metrics/`. GitHub-visible continuity belongs in sanitized manifests,
checksums, schemas, tests, and documentation. Do not download Kaggle SETI,
install/use Setigen, or depend on pretrained models for the first Track A
milestone.

---

## File Layout

```
data/bl_hits/                  ← raw turboSETI .dat input files
data_cache/                    ← ignored Track A raw/catalog cache
tmp_training/                  ← ignored temporary training workspace
tmp_features/                  ← ignored temporary feature extraction workspace
results/
  scan_history.ndjson          ← append-only cross-run scan log (gitignored)
  scans/
    PROD-RUN-YYYYMMDD-HHMMSS/ ← per-run audit directory (committed)
      validate_all.json
      *_scan_summary.json
      *_review_dashboard.json
      *_follow_ups.json
      *_non_detections.json
      cross_target_rfi.json
      escalations/
  prod_scan_output/            ← pipeline outputs per target (gitignored)
    HIP99427/
      HIP99427.json            ← scored candidate packet
      HIP99427.md              ← Markdown report
      HIP99427.manifest.json   ← report manifest
    HIP17147/
      zero/
        HIP17147__zero.manifest.json ← zero-hit observation manifest
```

Curated `results/scans/` summaries can be committed to GitHub as a durable
audit trail. Generated local `results/scans/RUN-*` directories are ignored by
default so the user's standard `git add .` cadence does not stage
machine-specific scan outputs accidentally. Commit only reviewed, sanitized
summaries/manifests deliberately.

---

## Scan History Schema

Each line in `results/scan_history.ndjson` is one JSON object:

```json
{
  "schema_version": "prod_scan_history_v1",
  "target_stem": "HIP99427",
  "run_id": "PROD-RUN-20260620-143022",
  "scanned_at_utc": "2026-06-20T14:30:22Z",
  "score": 0.72,
  "pathway": "follow_up",
  "dat_file": "/Users/you/project/data/bl_hits/HIP99427.dat",
  "parent_run_id": null
}
```

- `parent_run_id` is `null` for first scans; set to the *current* run ID for re-scans
  to create a linked chain.
- The file is append-only. Never delete or rewrite lines; add a new record instead.
- Gitignored because it contains absolute local paths and grows without bound.

---

## Data Directories

| Directory | Contents | Source |
|---|---|---|
| `data/bl_hits/` | Voyager 1 GBT `.dat` hit table (pipeline calibration) | `scripts/download_bl_hits.sh` |
| `data/extended_corpus/<TARGET>/` | GBT HDF5/DAT cache selected by a durable Hunter search; separate calibration corpora are explicitly marked | `Create-New-Search` then `Run-New-Search --approve-acquisition`; `download_bl_extended_corpus.sh --calibration-corpus` is non-production only |
| `data_cache/raw/<SOURCE>/` | Ignored Track A source cache from `docs/technosignature_datasets_agent_brief.md` | Future Track A acquisition CLI |
| `tmp_training/`, `tmp_features/` | Ignored temporary Track A training/feature workspaces | Future Track A acquisition/training CLI |

HDF5 files in `data/extended_corpus/` must be processed with turboSETI before they can
enter the production scan queue.  Use `scripts/run_turboseti_on_extended_corpus.sh` (idempotent).

Zero-hit turboSETI `.dat` files are still evidence. `scripts/bl_fetch.py run-pipeline`
writes `zero_hit_observation_manifest_v1` records for hit tables with no non-comment
rows, and `prod-scan` turns those records into non-detection ledger entries with
score `0.0`, no follow-up requirement, and explicit negative evidence.

When `data/meerkat_hits/semisupervised_scorer.joblib` exists, radio
`run-pipeline` packets include local semi-supervised anomaly-score features and
provenance. Override the model with `--semisupervised-model PATH` when testing a
new fitted scorer. These scores are local triage evidence only; they do not
constitute detection, discovery, external validation, or external-submission
approval.

Check local scorer readiness with:

```bash
git pull origin main
.venv/bin/techno-search semisupervised-scorer-summary
```

The summary reads ignored local metadata/model artifacts by default and reports
`model_ready: true` only when both the real-corpus training metadata and fitted
joblib model are present.

Use the real-corpus summary after local radio data changes or scorer retraining:

```bash
git pull origin main
caffeinate -i .venv/bin/techno-search radio-real-corpus-summary \
  --dat-dir data/extended_corpus \
  --dat-dir data/bl_hits \
  --hit-ndjson data/meerkat_hits/meerkat_normalised_200000.ndjson \
  --max-hit-rows 5000 \
  --candidate-sample-limit 5
```

The command reads ignored local `.dat` payloads, the verified normalized
MeerKAT BLUSE hit corpus when present, and fitted models, but writes no payload
files. Treat its output as local validation evidence only. If the
`--hit-ndjson` file is omitted, the current local GBT `.dat` corpus remains
useful negative evidence but has only one hit-bearing target, so cross-target
RFI recurrence validation is expected to remain blocked.
Use a bounded `--max-hit-rows` value for routine operator checks; omit it only
for a full-corpus review. The scorer uses vectorized batch scoring, so the
current local 200,000-row MeerKAT review is practical as a diagnostic. Use
`--candidate-sample-limit 0` for counts-only checks, or a small value such as 5
to inspect the top automated review survivors plus a bounded rejected/control
sample. Rows labeled `needs_follow_up_review` are triage survivors only, not
detections or external-submission candidates. Known control targets such as
Voyager and stationary-frequency rows are counted separately and are not
promoted as follow-up candidates. Inspect `candidate_review.top_review_targets`
before individual rows; a survivor set concentrated on one target is a
source-context and instrumental-vetting task, not a discovery claim.

When a survivor frequency comes from the bounded normalized MeerKAT subset,
check the complete already-local raw source before concluding that cross-target
recurrence is absent:

```bash
git pull origin main
caffeinate -i .venv/bin/techno-search meerkat-frequency-neighbor-summary \
  --raw-json data/meerkat_hits/meerkat_bluse_hits.json \
  --frequency-hz CANDIDATE_FREQUENCY_HZ \
  --tolerance-hz 500 \
  --sample-limit 10
```

Repeat `--frequency-hz` for multiple explicit survivor frequencies. The command
streams the top-level JSON array and writes no corpus or report file. Its unique
target/artifact/beam counts are deterministic triage context only: absence of a
neighbor does not confirm a signal, and presence of a neighbor is RFI evidence,
not an independently supplied row label.

The retired `radio-review-sample` command and its unlabeled queue are not a
calibration path and must not be recreated. The available pre-existing labels
are insufficient for a global anomaly/OOD threshold, so that learned gate
remains fail-closed. Continue deterministic false-positive analysis without
converting completed search rows into ground truth.

Before expanding `data/extended_corpus/`, verify current BL Open Data
availability from the committed manifest. This command queries the official
search pages, prints only target-to-HDF5 URL rows, and downloads no payloads:

```bash
git pull origin main
caffeinate -i bash scripts/download_bl_extended_corpus.sh \
  --manifest data_selection/batch_manifests/local_coverage_top25_manifest.json \
  --discover-only \
  --availability-output /tmp/local_coverage_top25_availability.tsv
```

This metadata-discovery mode records a compact status entry under
`download_bl_extended_corpus_discovery` in `docs/data_collection_status.json`,
including `available_targets` with URLs and `skipped_targets` with reasons.
Review that manifest after `git pull` instead of asking the operator to paste
console output.

After URL discovery, run a HEAD-only size/storage preflight before any raw
download. This command downloads no payloads and keeps raw download
authorization disabled:

```bash
git pull origin main
.venv/bin/techno-search target-priority-size-preflight
```

The first local-coverage top-25 run verified 15/15 URL headers with content
lengths, estimated 3.803966 GB total, found no checksum headers, and wrote
`data_selection/batch_manifests/local_coverage_top25_size_preflight_report.json`.

For a bounded production download, first create and review the exact immutable
Hunter search. The standalone downloader is metadata-only or explicitly
non-production calibration; it is not a production acquisition path. Only run
the exact search after explicit operator approval of its projected acquisition:

```bash
git pull origin main
SEARCH_ID=$(.venv/bin/Create-New-Search --targets 5 --mode new --json | jq -r '.search_id')
jq '{search_id, selection, targets}' "results/searches/${SEARCH_ID}/manifest.json"
caffeinate -i .venv/bin/Run-New-Search \
  --search-id "$SEARCH_ID" \
  --approve-acquisition
```

---

## Data Collection Status Reporting — Non-Negotiable

Real data-acquisition scripts and CLI commands (BL extended-corpus
downloads, JWST/MAST searches, photometry light-curve searches,
satellite/catalog acquisitions, and any future ones) must update the
tracked `docs/data_collection_status.json` manifest after a real successful
run, via `techno-search record-data-collection-status --script NAME
--summary-json '{...}'` (`src/techno_search/data_collection_status.py`).
This replaces pasting console output for review: the agent reviews progress
by `git pull`-ing this one small tracked file instead.

By default this also runs `git add`/`git commit`/`git push` for just that
one file — but **only when the current branch is `main`**
(`commit_and_push_status()` checks `git branch --show-current` and no-ops
otherwise). This guard exists because a real integration test in this
project's own suite runs the real download script end-to-end, and without
it, running the test suite silently auto-committed and pushed a fake
status entry to whatever branch happened to be checked out (caught and
fixed 2026-07-03). Do not remove or weaken this guard without an equally
strong replacement safeguard — the acquisition scripts run on the user's
real machine where `main` is always the real working branch (per
`CLAUDE.md`'s GIT SYNC DIRECTIVES), so this reliably distinguishes a real
run from a test/CI/agent-branch invocation.

When adding a new data-acquisition script or CLI command, call
`record_and_publish_data_collection_status()` (or the CLI wrapper) both
on real success and on real failure (an `"ok": false` entry with an error
message -- a failed run with no manifest entry is invisible and looks
identical to "never run"), with a JSON summary that names *which* items
succeeded/failed and why (e.g. `download_bl_extended_corpus`'s
`downloaded_targets`/`reused_targets`/`skipped_targets` with a `reason`
per skip, and `download_bl_extended_corpus_discovery`'s
`available_targets`/`skipped_targets`) -- not raw payload contents, and not
just aggregate counts.
This is what makes the committed manifest alone sufficient to diagnose a
real problem without asking the operator to paste console output. Also
consider the `CLAUDE.md` "DATA COLLECTION PARALLELIZATION DIRECTIVE" when
building new acquisition scripts.

**The agent must check `docs/data_collection_status.json` via `git pull`
before asking the user to run or paste output from an acquisition
script.** Only ask the user to actually run a command when the manifest
doesn't yet reflect the needed run, or when live interaction with their
machine is genuinely required.

---

## Running the Script

### Full setup — extended corpus (recommended, 5 targets)

Run once after downloading the extended corpus:

```bash
git pull origin main

# Step 1: produce .dat hit tables (~5–15 min per target on M4 Max, one-time)
caffeinate -i bash scripts/run_turboseti_on_extended_corpus.sh

# Step 2: build candidate reports
caffeinate -i bash scripts/run_pipeline_on_bl_data.sh \
    --dat-dir data/extended_corpus

# Step 3: continuous production scan (5 targets)
caffeinate -i bash scripts/run_production_scan.sh \
    --dat-dir data/extended_corpus
```

### First run — Voyager calibration only (3 targets)

```bash
git pull origin main
caffeinate -i bash scripts/run_production_scan.sh \
    --dat-dir data/bl_hits
```

### Continuous mode (polls for new files every 60 s)

```bash
caffeinate -i bash scripts/run_production_scan.sh \
    --dat-dir data/extended_corpus \
    --continuous
```

### Re-scan all targets (e.g., after a model update)

```bash
caffeinate -i bash scripts/run_production_scan.sh \
    --dat-dir data/extended_corpus \
    --force-rescan
```

### Check what the queue looks like before running

```bash
.venv/bin/techno-search prod-target-queue \
    --dat-dir data/extended_corpus \
    --history-file results/scan_history.ndjson
```

### Inspect scan history

```bash
.venv/bin/techno-search scan-history-summary \
    --history-file results/scan_history.ndjson \
    --dat-dir data/extended_corpus
```

---

## Storage Cleanup — Non-Negotiable

Large intermediate files accumulate quickly. Before each new download batch,
plan cleanup for prior converted or ledgered runs to free storage space.

### Plan cleanup between batches

```bash
git pull origin main
.venv/bin/techno-search radio-corpus-cleanup
```

This dry run only proposes:

- HDF5 files under `data/extended_corpus/` after a same-stem non-empty `.dat`
  exists.
- Zero-hit `.dat` files under `data/extended_corpus/` after a zero-hit manifest
  in `results/` records the file's relative `source_data_path`.

Hit-bearing `.dat` files are never cleanup candidates.

### Apply cleanup

Review the dry-run JSON first. If the plan is correct:

```bash
git pull origin main
.venv/bin/techno-search radio-corpus-cleanup \
  --apply \
  --acknowledge-local-apply
```

### What to keep

| Keep | Reason |
|---|---|
| `results/scans/RUN-*/` | Local generated production run artifacts — ignored unless deliberately reviewed and force-added |
| `data/target_sample_manifest.json` | Reproduces the download list |
| `data/bl_hprc_seed_targets.csv` | Source of stratified sample |
| `data/meerkat_hits/*.ndjson` | Real MeerKAT corpus used for model training |
| Any `.dat` file with real hits above threshold | Needed for re-processing |

### Synthetic training data — delete permanently

Synthetic calibration data was never scientifically valid for training models
that will operate on real signals. Delete it:

```bash
# These files contain synthetic (fake) data and must not be used for training
rm -f tests/fixtures/calibration_false_positives.json
rm -f tests/fixtures/score_regressions.json

# After deletion, update any tests that import these fixtures to skip or remove
```

Do not replace synthetic training data with more synthetic data. Use real
labeled corpora only (MeerKAT BLUSE, real GBT hits, real turboSETI output).

---

## Scientific Guardrails (non-negotiable)

1. `validate-all` must pass before any scan proceeds. The script aborts on failure.
2. No scan result constitutes a detection claim or authorizes external submission.
3. All outputs are local production-scan evidence records only; they are not
   detection, discovery, expert-review, peer-review, external-validation, or
   external-submission claims.
4. Escalation candidates require `operator_cleared` and `external_review_authorized`
   to both be `True` before any external action — those fields start as `False` and
   require explicit human approval.
5. The scan history file is a provenance record, not a discovery log.

---

## Adapting This Runbook to Other Projects

The five rules above are project-agnostic. To adapt:

1. Replace `techno-search run-pipeline` with your pipeline CLI command.
2. Replace `.dat` discovery with your input file extension.
3. Replace `signal_reality_confidence` score extraction with your score field.
4. Keep the NDJSON history schema — it is minimal and self-describing.
5. Keep the `parent_run_id` chain for re-scan linking.
6. Keep the continuous loop + SIGINT trap pattern verbatim.
7. Keep `validate-all` (or equivalent) as a mandatory preflight gate.
