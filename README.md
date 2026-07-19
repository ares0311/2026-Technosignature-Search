# 2026 Technosignature Search

![Status](https://img.shields.io/badge/status-active%20development-blue)
![License](https://img.shields.io/badge/license-Apache--2.0-green)
![Focus](https://img.shields.io/badge/focus-multimodal%20technosignature%20search-purple)

This repository searches public astronomical data for candidate signals and
anomalies that survive conservative natural, instrumental, and human-made
false-positive checks. It supports radio, transit-photometry, infrared, and
spectroscopy workflows and preserves negative evidence as a scientific output.

It does not claim detections or discoveries. A result can advance only from the
automated pipeline to a deterministic adversarial-review dossier and then, if
it survives, to credentialed third-party scientific review.

## Scientific boundary

The project uses labeled data for training, calibration, threshold selection,
or scientific evaluation only when independent row-level labels already exist
with documented provenance.

- No confirmed positive technosignature labels exist.
- Nobody is asked to label, annotate, classify, or review observations to
  create project labels.
- Unlabeled observations may be searched, ranked, and investigated, but they
  remain unlabeled.
- An anomaly score is a ranking diagnostic, not a class probability or a
  detection claim.
- `unknown_candidate` is a local Track B triage state, not a positive label,
  discovery, or authorization for external submission.
- Missing calibration evidence keeps the dependent learned-model gate
  fail-closed. Synthetic injections may test recovery behavior but cannot
  replace independent labels.

The full rules are in [AGENTS.md](AGENTS.md). The current status is in
[docs/PRODUCTION_READINESS.md](docs/PRODUCTION_READINESS.md), and the sequenced
execution plan is in
[docs/SYSTEMATIC_SEARCH_PLAN.md](docs/SYSTEMATIC_SEARCH_PLAN.md).

## Current status

Phase 0 is complete. Phases 1–5 have real, tested baseline implementations,
with the remaining gaps either fail-closed on unavailable evidence, blocked by
network/data access, or correctly deferred until a real surviving candidate
exists.

| Area | Current state |
|---|---|
| Radio | Real GBT/MeerKAT ingestion, ABACAB cadence checks, Track A known-explanation checks, cross-target recurrence, drift analysis, frequency-family diagnostics, and corpus summaries are implemented. The semi-supervised score remains ranking-only. |
| Transit photometry | BLS, aperiodic-dip, ingress/egress asymmetry, and transit-shape checks are wired end to end. The real KIC 8462852 run recovered the known rotational signal and rejected it as transit-like evidence. |
| Infrared | AllWISE ingest, W1/W2 photosphere fitting, W3/W4 excess significance, and AGN-color checks are implemented. Live IRSA execution remains network-dependent. |
| Spectroscopy | JWST MIRI LRS `x1d`/`x1dints` ingest and five HITRAN-derived artificial-gas band checks are implemented. A corrected real WASP-43 integration produced negative evidence, not a detection. |
| Multi-modal | Sky-position crossmatching and deterministic adversarial-review dossiers are implemented. No real candidate has advanced through them. |
| Learned calibration | Permanently fail-closed with currently available data: no adequate pre-existing independent row-level calibration set was found. |
| Operator UI | Compact review surfaces are substantially hardened; workflow-level audit work remains open. |
| Novel-target selection | The durable Hunter create/run lifecycle uses the real configured rank and freezes exact selections. The current 1,703-target queue has 358 size-preflighted acquisition candidates totaling 89.274678 GB; this inventory is not a raw-download authorization. |
| Follow-up selection | Durable run ledgers now feed an identity-resolved, deterministic follow-up registry with evidence, provenance, priority, and recommended next actions. Unresolved outputs remain excluded rather than guessed. |

The current real combined radio review leaves unresolved unlabeled triage rows
but zero independently escalation-ready candidates. No current result is ready
for external submission.

## Pipeline architecture

```text
public archive metadata and selected observations
  -> provenance and structural validation
  -> modality-specific candidate generation
  -> Track A known-explanation rejection or low-confidence abstention
  -> deterministic RFI / cadence / artifact / natural-source checks
  -> fail-closed Track B eligibility review
  -> cross-modal position matching
  -> deterministic adversarial-review dossier
  -> credentialed third-party scientific review, only if a candidate survives
```

The four modality baselines are intentionally different:

- Radio: turboSETI hit tables, drift/cadence evidence, known-source catalogs,
  satellite/transmitter matching, recurrence, and RFI-family diagnostics.
- Photometry: periodic BLS search plus aperiodic dips, shape, odd/even,
  harmonic, and ingress/egress checks.
- Infrared: WISE photometry, a first-pass photospheric model, W3/W4 excess,
  and known-contaminant indicators.
- Spectroscopy: JWST MIRI LRS spectra and laboratory-derived HITRAN templates
  and band centers.

## Data and target-selection policy

Training, validation, calibration, frozen evaluation, live search, and
follow-up live-search data have distinct roles. Live-search data is never
silently reused for training and later described as a blind search.

Target selection is detection-probability-driven, not primarily
stratified-random. Stratification is retained only as a way to make null
results less vulnerable to cherry-picking concerns. Acquisition follows this
order:

1. Build or update a metadata target queue.
2. Discover archive products without downloading raw payloads.
3. Run size and storage preflight.
4. Obtain explicit approval for any substantial raw acquisition.
5. Use bounded `stream_process_evict` batches when raw data is approved.
6. Preserve manifests, archive URIs, checksums, derived evidence, and status;
   evict re-downloadable raw cache after processing.

The entire project-managed local data footprint is capped at 100 GB. There is
no external-drive or cloud-storage assumption for this repository. The
approximately 289 GB preflighted target inventory is a priority-ranked
wishlist, not a download plan.

Relevant policies:

- [Systematic search plan](docs/SYSTEMATIC_SEARCH_PLAN.md)
- [Data-selection policy](docs/astrometrics_data_selection_policy.md)
- [Storage policy](docs/astrometrics_external_and_cloud_storage_policy.md)
- [Detection-agent guide](docs/astrometrics_coding_agents_master_guide.md)
- [Production scan runbook](docs/PRODUCTION_SCAN_RUNBOOK.md)

## Environment

The repository expects a local `.venv` running Python 3.14.3. Do not create or
modify environments unless the existing environment is absent or a documented
task requires it. The complete development/science environment uses all
declared extras:

```bash
git pull origin main
source .venv/bin/activate
.venv/bin/python -m pip install -e ".[dev,radio,science,ml,track_a,photometry]"
bash scripts/patch_turbo_seti_numpy2_compat.sh
```

The turboSETI compatibility patch is required after reinstalling the `radio`
extra. See [AGENTS.md](AGENTS.md) for the pinned-version rationale.

## Quick start

Inspect the installed version and available commands:

```bash
git pull origin main
source .venv/bin/activate
.venv/bin/techno-search version
.venv/bin/techno-search --help
```

Run the canonical local validation suite:

```bash
git pull origin main
source .venv/bin/activate
caffeinate -i .venv/bin/python scripts/run_parallel_validation.py
```

The launcher uses six non-overlapping pytest-xdist workers, then runs the app
version gate, Ruff, mypy, and the scientific `validate-all` gate. Small focused
tests may run directly inside `.venv` when launcher startup would cost more
than it saves.

## Real-data workflows

Summarize the corrected local radio corpus without writing data:

```bash
git pull origin main
source .venv/bin/activate
.venv/bin/techno-search radio-real-corpus-summary \
  --dat-dir data/extended_corpus \
  --dat-dir data/bl_hits
```

Inspect a ranked local production queue and run a bounded existing-data scan:

```bash
git pull origin main
source .venv/bin/activate
.venv/bin/techno-search prod-target-queue --dat-dir data/extended_corpus
.venv/bin/techno-search prod-scan data/extended_corpus results/current_scan --track radio
```

Review compact production outputs:

```bash
git pull origin main
source .venv/bin/activate
.venv/bin/techno-search prod-runs
.venv/bin/techno-search prod-target-status --latest
.venv/bin/techno-search prod-follow-ups --latest
.venv/bin/techno-search prod-non-detections --latest
.venv/bin/techno-search review-dashboard --run-dir results/scans/LATEST_RUN
```

Replace `LATEST_RUN` with a real run directory reported by `prod-runs`.
Machine-readable variants use the documented `--json` flags. Full production
or acquisition instructions live in
[docs/PRODUCTION_SCAN_RUNBOOK.md](docs/PRODUCTION_SCAN_RUNBOOK.md); do not infer
raw-download authorization from these examples.

Track B remains fail-closed and consumes explicit precomputed evidence:

```bash
git pull origin main
source .venv/bin/activate
.venv/bin/techno-search track-b-candidate-readiness candidate.json \
  --crossmatch-json track_a_crossmatch.json \
  --satellite-json satellite_match.json
```

The readiness result is an audit of missing evidence, not a candidate claim.

## Validation and release discipline

Every release-relevant change must advance the semantic version relative to
`origin/main`. These surfaces must agree:

- `pyproject.toml`
- `src/techno_search/__init__.py`
- `docs/PRODUCTION_READINESS.md`

Feature work is committed on `claude/general-session-Bb2dZ`, pushed, reviewed
through a pull request, merged to `main`, and then synchronized back to the
agent branch. The user runs from `main`.

Before committing data-ingestion, artifact, logging, calibration, or scan-output
changes, verify that `git add --dry-run .` cannot stage generated science
payloads. The continuity rule is: ignore payloads, commit the map.

See also:

- [Validation guide](docs/VALIDATION.md)
- [CI guide](docs/CI.md)
- [Local system profile](docs/LOCAL_SYSTEM_PROFILE.md)
- [Track A dataset handoff](docs/technosignature_datasets_agent_brief.md)

## Repository layout

```text
src/techno_search/       application and scientific pipeline code
scripts/                 bounded acquisition, processing, and validation tools
tests/                   regression, scientific, and integration tests
docs/                    authoritative status, policies, methods, and runbooks
data_selection/          metadata queues, manifests, and decision records
schemas/                 active machine-readable contracts
data/                    ignored or selectively tracked local science inputs
results/                 local scan and report outputs
```

Large raw HDF5, FITS, filterbank, cache, fitted-model, and generated result
payloads are not committed. Small manifests, checksums, schemas, sanitized
status records, and reproducibility evidence are committed when policy allows.

## Scientific guardrails

- False positive is always the default hypothesis.
- Track A known-explanation checks precede Track B triage.
- Track A may abstain with `low_confidence`; abstention is not a positive class.
- Unlabeled data is never treated as negative ground truth.
- Accuracy alone is not promotion evidence for rare-event search.
- Learned-model promotion requires provenance, grouped leakage-safe evaluation,
  calibration context, and injection-recovery evidence in real backgrounds.
- Candidate reports expose negative evidence, uncertainty, provenance, and
  blockers.
- No automated or AI component makes a final detection decision.
- No result authorizes public disclosure or external submission.

## Disclaimer

This is research software under active development. Its outputs are local
triage evidence, candidate-interest reports, and documented null results. They
are not confirmed technosignatures, detections, discoveries, expert review,
external validation, or authority-facing notifications.

## License

Apache-2.0. See [LICENSE](LICENSE).
