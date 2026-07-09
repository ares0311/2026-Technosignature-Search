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

Each acquisition round (`top25`, `next25`, ...) gets its own discovery
manifest, size-preflight manifest, and size-preflight report — this
preserves that round's real discovered URLs and measured sizes as a
distinct, reviewable artifact. `techno-search build-target-priority-queue`
merges **every** `*_size_preflight_report.json` file committed under this
directory (see `--extra-size-preflight-report-path`, default: auto-glob),
so a later round's report does not regress an earlier round's
`raw_download_approval_required` promotion.

Because of that merge, the raw-download **approval manifest** is not
per-round — it is regenerated as one consolidated, always-current file
covering every target currently promoted to
`raw_download_approval_required` across all rounds so far:
`local_coverage_raw_download_approval_manifest.json`. Regenerate it after
each new round's size preflight completes and the queue is rebuilt.

Current metadata-only manifests:

- `local_coverage_top25_manifest.json` / `local_coverage_next25_manifest.json`
  — the top 25 `queued_metadata_discovery` rows from
  `data_selection/target_priority_queue.csv` at the time each round ran
  (`next25` naturally picks up the next-highest-priority rows once the prior
  round's rows have left `queued_metadata_discovery` status). Each is
  downloader-compatible for
  `scripts/download_bl_extended_corpus.sh --manifest ... --discover-only` and
  is intended for product metadata discovery before any raw download.
- `local_coverage_top25_size_preflight_manifest.json` /
  `local_coverage_next25_size_preflight_manifest.json` — the URL-discovered
  rows from each round (15 and 14 respectively). Use these for URL header,
  checksum, size, and local-storage preflight before any raw download; they
  are not raw-download authorization.
- `local_coverage_top25_size_preflight_report.json` /
  `local_coverage_next25_size_preflight_report.json` — HEAD-only preflight
  results for each round. `top25`: 15/15 URLs verified, 3.803966 GB total.
  `next25`: 14/14 URLs verified, 3.608361 GB total. Neither found checksum
  headers, and both leave raw download authorization disabled.
- `local_coverage_raw_download_approval_manifest.json` — the consolidated,
  current set of sized HDF5 rows promoted to
  `raw_download_approval_required` across all rounds so far (29 targets,
  ~7.41 GB combined as of the `next25` round). This is the human-review
  input for an explicitly approved bounded raw download; it is not approval
  by itself.
