# PROJECT STATUS

## Project
Technosignature Search

## Status
Initial v0 Implementation

## Current Phase
Phase 1 — Synthetic Scoring Core

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
- [x] Provider normalization contract added
- [x] Guarded Gaia live client added with mocked transport tests
- [x] Provenance helper module added
- [x] Provenance summaries added to report manifests
- [x] Provenance summary CLI added

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
- [ ] Add real live-data provider clients behind explicit integration gates

---

## Next 3 Actions

1. Push local commits to GitHub from an approved local environment with the required token scopes.
2. Repeat the guarded live-client pattern for IRSA behind explicit integration gates.
3. Add VizieR, SIMBAD, and Breakthrough Listen clients only after Gaia/IRSA contracts stay green.

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
