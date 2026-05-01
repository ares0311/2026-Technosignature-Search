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

---

## In Progress

- [ ] Add calibration fixture documentation and expansion plan
- [ ] Add CLI usage documentation
- [ ] Add live-data integration interfaces behind mocks

---

## Next 3 Actions

1. Add CLI usage documentation with a complete example command.
2. Add calibration fixture documentation and expansion plan.
3. Add validation tests for CLI-installed console script behavior.

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
