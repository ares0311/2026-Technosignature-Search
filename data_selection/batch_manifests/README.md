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

**Third round (`batch3`) completed, 2026-07-10:** the user ran discovery
from their own machine (real network access; `breakthroughinitiatives.org`/
`bldata.berkeley.edu` are not reachable from this agent's sandbox proxy for
the search-page discovery step, though the direct `bldata.berkeley.edu`
HEAD-only size-preflight requests were reachable). Discovery checked 25/25
targets: 14 available, 11 skipped, written durably via
`--discovery-result-output` to `local_coverage_batch3_discovery_result.json`
(no reconstruction needed for this round — it was captured live). Queue
rebuild correctly grew `metadata_discovery_required` by exactly 11 (25→36)
and moved all 25 `batch3` rows out of `queued_metadata_discovery`,
confirming the merge fix above works end-to-end on a real round. Size
preflight then verified 14/14 URLs, 3.481361 GB total, no checksum headers.
Queue rebuild promoted all 14 to `raw_download_approval_required` (29→43
total across all three rounds).

Current metadata-only manifests:

- `local_coverage_top25_manifest.json` / `local_coverage_next25_manifest.json`
  / `local_coverage_batch3_manifest.json` — the top 25
  `queued_metadata_discovery` rows from
  `data_selection/target_priority_queue.csv` at the time each round ran
  (each round naturally picks up the next-highest-priority rows once the
  prior rounds' rows have left `queued_metadata_discovery` status). Each is
  downloader-compatible for
  `scripts/download_bl_extended_corpus.sh --manifest ... --discover-only` and
  is intended for product metadata discovery before any raw download.
- `local_coverage_top25_discovery_result.json` /
  `local_coverage_next25_discovery_result.json` /
  `local_coverage_batch3_discovery_result.json` — the full per-round
  discovery outcome (available + skipped targets with reasons), durably
  committed so a later round's discovery cannot lose an earlier round's
  result. `top25`: 15 available, 10 skipped (reconstructed from committed
  evidence, see above). `next25`: 14 available, 11 skipped (reconstructed).
  `batch3`: 14 available, 11 skipped (captured live via
  `--discovery-result-output`).
- `local_coverage_top25_size_preflight_manifest.json` /
  `local_coverage_next25_size_preflight_manifest.json` /
  `local_coverage_batch3_size_preflight_manifest.json` — the URL-discovered
  rows from each round (15, 14, and 14 respectively). Use these for URL
  header, checksum, size, and local-storage preflight before any raw
  download; they are not raw-download authorization.
- `local_coverage_top25_size_preflight_report.json` /
  `local_coverage_next25_size_preflight_report.json` /
  `local_coverage_batch3_size_preflight_report.json` — HEAD-only preflight
  results for each round. `top25`: 15/15 URLs verified, 3.803966 GB total.
  `next25`: 14/14 URLs verified, 3.608361 GB total. `batch3`: 14/14 URLs
  verified, 3.481361 GB total. None found checksum headers, and all leave
  raw download authorization disabled.
- `local_coverage_raw_download_approval_manifest.json` — the consolidated,
  current set of sized HDF5 rows promoted to
  `raw_download_approval_required` across all rounds so far (43 targets,
  ~10.89 GB combined as of the `batch3` round). This is the human-review
  input for an explicitly approved bounded raw download; it is not approval
  by itself.
