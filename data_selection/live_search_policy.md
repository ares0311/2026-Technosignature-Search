# Technosignatures Live Search Policy

Live-search target selection must maximize material scientific value while
preserving reproducibility and conservative claims.

Current live-search target queue:

- `data_selection/target_priority_queue.csv`

Rules:

1. Build or refresh the target queue from metadata before raw downloads.
2. Do not use model score alone to choose raw acquisition targets.
3. Prefer novel local-coverage targets, nearby stars, exoplanet hosts, complete
   cadence metadata, and targets where a null result would still be useful.
4. Treat already-acquired local targets as controls or reanalysis targets, not
   as novel acquisition targets.
5. Treat skipped targets as metadata-discovery work until a real archive product
   URI and size estimate are verified.
6. Keep live-search data separate from training, validation, calibration, and
   frozen-eval roles.
7. Preserve no-claim language in every queue summary and candidate artifact.

Portfolio target while there is no unresolved candidate backlog:

- 70% new local-coverage targets
- 20% controls or reanalysis of already-acquired targets after major pipeline
  changes
- 10% metadata-retry targets where the prior discovery run found no HDF5 URL

When a real unresolved candidate exists, create or refresh
`data_selection/followup_priority_queue.csv` from the candidate's actual missing
evidence conditions before scheduling follow-up data.

