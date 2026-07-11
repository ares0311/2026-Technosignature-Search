# Batch Manifests

Raw acquisition batches must be planned here before download when the batch is
driven by the target-priority queue.

Required fields are defined by `docs/astrometrics_data_selection_policy.md`:

- `batch_id`
- `project`
- `role`
- `acquisition_mode`
- `target_queue_snapshot`
- `source_archive`
- `query`
- `estimated_download_gb`
- `max_allowed_download_gb`
- `expected_raw_files`
- `expected_derived_gb`
- `free_space_before_gb`
- `free_space_required_after_gb`
- `eviction_rule`
- `pin_rule`
- `stop_condition`
- `manifest_owner`
- `created_at`

Do not use a batch manifest as approval to download raw files until archive
product metadata, size estimates, and local free-space constraints have been
verified.

## Batch naming convention

Each acquisition round (`top25`, `next25`, `batch3`, ...) gets its own
discovery manifest, discovery-result file, size-preflight manifest, and
size-preflight report — this preserves that round's real discovered URLs,
skipped targets, and measured sizes as a distinct, reviewable artifact.
`techno-search build-target-priority-queue` merges **every**
`*_size_preflight_report.json` and every `*_discovery_result.json` file
committed under this directory (see `--extra-size-preflight-report-path` /
`--extra-discovery-result-path`, both default: auto-glob), so a later
round's report/result does not regress an earlier round's promotion or
"no HDF5 URL found" outcome.

Because of that merge, the raw-download **approval manifest** is not
per-round — it is regenerated as one consolidated, always-current file
covering every target currently promoted to
`raw_download_approval_required` across all rounds so far:
`local_coverage_raw_download_approval_manifest.json`. Regenerate it after
each new round's size preflight completes and the queue is rebuilt.

**Real bug found and fixed, 2026-07-10:** `docs/data_collection_status.json`
keeps only the single most recent `download_bl_extended_corpus_discovery`
run, so once `next25`'s discovery ran, `top25`'s 10 "no HDF5 URL found"
targets were no longer visible to `build-target-priority-queue` and
silently fell back to `queued_metadata_discovery` — they resurfaced as
10 of the 25 targets in a first `batch3` manifest attempt, which would have
wasted a repeat live-network check on targets already known to have no
current URL. This is the same class of bug already fixed for size-preflight
reports (`--extra-size-preflight-report-path`, see the `next25` entry in
`docs/LOCAL_DATA_INVENTORY.md`) — just not yet applied to discovery
results. Fixed with the analogous mechanism
(`--extra-discovery-result-path` / `*_discovery_result.json`, see
`scripts/download_bl_extended_corpus.sh --discovery-result-output` for how
future rounds should persist their own result durably). `top25`'s and
`next25`'s original discovery outcomes were reconstructed from
already-committed evidence (each round's discovery manifest minus that
round's size-preflight manifest is exactly the checked-but-no-URL set) —
not guessed — and committed as
`local_coverage_top25_discovery_result.json` /
`local_coverage_next25_discovery_result.json`. `batch3` was then
regenerated cleanly with zero overlap against `top25`/`next25`.

Starting with `batch3`, `breakthroughinitiatives.org` discovery still needs
the user's own machine (not reachable from this agent's sandbox proxy), but
`bldata.berkeley.edu` HEAD-only size-preflight requests are reachable from
here, so this agent runs preflight/queue-rebuild/manifest-regen itself once
the user pastes back a discovery-result file.

Every round follows the same four files:
`local_coverage_<round>_manifest.json` (the round's 25
`queued_metadata_discovery` targets, downloader-compatible for
`scripts/download_bl_extended_corpus.sh --manifest ... --discover-only`),
`local_coverage_<round>_discovery_result.json` (durable available+skipped
outcome), `local_coverage_<round>_size_preflight_manifest.json` (the
URL-discovered subset), and `local_coverage_<round>_size_preflight_report.json`
(HEAD-only size/checksum results). None of these authorize a raw download by
themselves.

| Round | Checked | Available (URL found) | Skipped (no URL) | Preflight verified | Size (GB) | Notes |
|---|---|---|---|---|---|---|
| `top25` | 25 | 15 | 10 | 15/15 | 3.803966 | discovery result reconstructed from committed evidence, 2026-07-10 (see below) |
| `next25` | 25 | 14 | 11 | 14/14 | 3.608361 | discovery result reconstructed from committed evidence, 2026-07-10 (see below) |
| `batch3` | 25 | 14 | 11 | 14/14 | 3.481361 | first round captured live via `--discovery-result-output` |
| `batch4` | 25 | 19 | 6 | 19/19 | 4.79346 | captured live |
| `batch5` | - | - | - | - | - | manifest built, zero overlap confirmed against prior rounds; discovery not yet run |

`local_coverage_raw_download_approval_manifest.json` — the consolidated,
always-current set of sized HDF5 rows promoted to
`raw_download_approval_required` across all rounds so far: **62 targets,
~15.69 GB combined** (as of the `batch4` round). This is the human-review
input for an explicitly approved bounded raw download; it is not approval
by itself. Regenerate it after each new round's size preflight completes and
the queue is rebuilt.
