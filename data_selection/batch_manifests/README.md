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

Current metadata-only manifests:

- `local_coverage_top25_manifest.json` — top 25
  `queued_metadata_discovery` rows from
  `data_selection/target_priority_queue.csv`. This is downloader-compatible for
  `scripts/download_bl_extended_corpus.sh --manifest ... --discover-only` and is
  intended for product metadata discovery before any raw download.
- `local_coverage_top25_size_preflight_manifest.json` — the 15 rows from the
  top-25 discovery run with current BL HDF5 URLs. Use this for URL header,
  checksum, size, and local-storage preflight before any raw download; it is not
  raw-download authorization.
- `local_coverage_top25_size_preflight_report.json` — HEAD-only preflight for
  the 15 URL-discovered HDF5 files. The first run verified 15/15 URLs with
  content lengths, estimated 3.803966 GB total, found no checksum headers, and
  leaves raw download authorization disabled.
- `local_coverage_top25_raw_download_approval_manifest.json` — the same 15
  sized HDF5 rows after queue promotion to `raw_download_approval_required`.
  This is the human-review input for an explicitly approved bounded raw
  download; it is not approval by itself.
