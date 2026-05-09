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

---

## Next 3 Actions

1. Promote local-only background run fixtures into a reviewed workflow only after ledger semantics stabilize.
2. Add benchmark comparison thresholds once repeated synthetic calibration grids exist.
3. Expand curated validation readiness examples after real reviewed non-synthetic candidates are available.

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
