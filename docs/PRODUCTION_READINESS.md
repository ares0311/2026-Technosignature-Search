# Production Readiness Assessment

**Last updated:** 2026-06-03
**Current milestone:** 67 (Network Monitoring Log, Identity Management Log, And Certificate Management Log)

---

## Summary

The pipeline is approximately **20–25% of the way to real production** for a research-grade technosignature search system. The foundation is now in place; the remaining gap is almost entirely in real data, real models, and telescope access.

---

## What Is Complete

| Capability | Status |
|---|---|
| Synthetic scoring pipeline (radio, infrared, anomaly) | ✅ Complete |
| Candidate report generation (Markdown, JSON, manifest) | ✅ Complete |
| Calibration fixture set (15 false-positive classes) | ✅ Complete |
| Score regression + determinism checks | ✅ Complete |
| Interpretable baseline classifier | ✅ Complete |
| 188 JSON schema artifacts | ✅ Complete |
| Local validation gate (`validate-all`) | ✅ Complete |
| Provenance, audit trail, lifecycle tracking | ✅ Complete |
| Operational log system (68 log types) | ✅ Complete |
| CI workflow (GitHub Actions) | ✅ Complete |
| Real hit-table CSV reader (turboSETI format) | ✅ Complete |
| Real Gaia+WISE catalog CSV reader (IRSA TAP format) | ✅ Complete |
| End-to-end pipeline runner (CSV → scored report) | ✅ Complete |
| Data quality validator (`validate-input`) | ✅ Complete |
| Direct `run-pipeline` CLI with validation-first execution | ✅ Complete |
| Archival anomaly CSV reader scaffold | ✅ Complete |
| Synthetic/local RFI database guardrails | ✅ Complete |
| RFI database admission gates | ✅ Complete |
| Curated dataset admission gates | ✅ Complete |
| Project status consistency gates | ✅ Complete |
| Operations alert review consistency gates | ✅ Complete |
| Operations action resolution staleness gates | ✅ Complete |
| Operations blocker-progress consistency gates | ✅ Complete |
| Top-level SQLite log consistency gates | ✅ Complete |
| Production blocker visibility consistency gates | ✅ Complete |
| SQLite operational log registry consistency gate | ✅ Complete |
| SQLite operational log adapter plan gate | ✅ Complete |
| SQLite operational log adapter contract gate | ✅ Complete |
| SQLite operational log adapter DDL preview gate | ✅ Complete |
| SQLite operational log adapter row preview gate | ✅ Complete |
| SQLite operational log adapter insert preview gate | ✅ Complete |
| SQLite operational log adapter execution preview gate | ✅ Complete |
| SQLite operational log adapter dry-run manifest gate | ✅ Complete |
| SQLite operational log adapter readiness preflight gate | ✅ Complete |
| SQLite operational log adapter authorization gate | ✅ Complete |
| Project-scoped MCP bootstrap configuration | ✅ Complete |
| MCP bootstrap consistency gate | ✅ Complete |
| MCP server policy gate | ✅ Complete |
| Labeled candidate dataset v0 (10 synthetic entries) | ✅ Complete |
| Scoring model evaluation against labeled dataset | ✅ Complete |
| Live catalog clients (Gaia TAP, SIMBAD) with opt-in guard | ✅ Complete |
| Operational log system (68 log types) | ✅ Complete |

---

## What Is Missing for Production

### Tier 1 — Blockers (nothing ships without these)

| Gap | Effort estimate |
|---|---|
| **Real observation data** — no actual telescope data has been ingested | Large (requires telescope time or approved archive access) |
| **Real labeled dataset** — admission gates exist, but all committed labels are synthetic and no real labeled dataset has been approved | Medium (requires human expert labeling of real detections) |
| **Calibrated scoring thresholds** — current thresholds are synthetic v0 defaults | Medium (requires sensitivity analysis against real noise distributions) |
| **Real site-specific RFI database** — synthetic guardrails and admission gates exist, but no permitted site-monitoring catalog has been approved | Medium |
| **Peer review** — no external scientific review of pipeline logic or candidate reports | Large |

### Tier 2 — Required for Research-Grade Use

| Gap | Effort estimate |
|---|---|
| Real Gaia/WISE cross-match queries at scale | Small (client exists, needs real queries) |
| Multi-epoch observation support | Medium |
| Real turboSETI file ingestion from BL archive | Medium (requires BL data policy compliance) |
| Known object catalog integration (SIMBAD cross-match) | Small (client exists) |
| Learned scoring model (replace rule-based baseline) | Large |

### Tier 3 — Production Hardening

| Gap | Effort estimate |
|---|---|
| Parallelized batch processing | Small |
| Database-backed candidate store (not file-based) | Medium |
| Operator UI / review dashboard | Large |
| External submission workflow | Large (requires institutional policy approval) |
| Reproducibility verification across data releases | Medium |

---

## Production Readiness Estimate

- **Current state:** ~20–25%
- **After Tier 1 complete:** ~60%
- **After Tier 2 complete:** ~80%
- **After Tier 3 complete:** ~100%

---

## Scientific Guardrails (Non-Negotiable)

Regardless of engineering readiness:

1. No candidate report authorizes external submission without peer review.
2. No scoring result constitutes a detection claim.
3. Pathway routing is a local scheduling aid, not a scientific verdict.
4. All external catalog queries remain opt-in via `TECHNO_SEARCH_ENABLE_LIVE_DATA=1`.
5. The pipeline is a provenance and triage tool — human expert review gates every step.

---

## Decision Reference

See `docs/DECISIONS.md` (DECISION-074) for the formal production readiness
assessment, DECISION-080 for the status-consistency gate, DECISION-081 for the
alert/QC review consistency gate, DECISION-082 for the action-resolution
staleness gate, DECISION-083 for the blocker-progress consistency gate,
DECISION-084 for the top-level SQLite log consistency gate, and DECISION-085
for the production blocker visibility consistency gate, DECISION-097 for
the SQLite operational log registry consistency gate, DECISION-098 for
the SQLite operational log adapter plan gate, DECISION-099 for the SQLite
operational log adapter contract gate, DECISION-100 for the SQLite operational
log adapter DDL preview gate, DECISION-101 for the SQLite operational log
adapter row preview gate, DECISION-102 for the SQLite operational log adapter
insert preview gate, DECISION-103 for the SQLite operational log adapter
execution preview gate, DECISION-104 for the SQLite operational log adapter
dry-run manifest gate, DECISION-105 for the SQLite operational log adapter
readiness preflight gate, DECISION-106 for the SQLite operational log
adapter authorization gate, DECISION-107 for the project-scoped MCP
bootstrap, DECISION-108 for the MCP bootstrap consistency gate,
DECISION-109 for the MCP server policy gate, DECISION-110 for the data
transfer log, system diagnostics log, and resource allocation log,
DECISION-111 for the access control log, change management log, and
incident log, and DECISION-112 for the patch management log, vulnerability
scan log, and compliance audit log, and DECISION-113 for the disaster
recovery log, service level log, and asset management log.
