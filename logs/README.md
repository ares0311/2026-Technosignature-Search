# Top-Level SQLite Logs

This directory is the default location for local operational SQLite logs.

Generated databases are intentionally ignored by Git. Commit only small policy
or documentation files from this directory. Runtime log databases may contain
local paths, run IDs, timestamps, configuration versions, provenance summaries,
negative evidence, blocking issues, and explicit user decisions.

These logs are workflow and provenance records only. They are not detections,
not external validation, not discoveries, and not authorization to submit
anything externally.

Default local database path:

```text
logs/techno_search.sqlite3
```

## Rotation And Retention

- Keep generated databases local unless the project owner explicitly asks for an export.
- Prefer exporting small review-safe JSON summaries with `sqlite-log-export` instead of sharing a full database.
- Back up or archive old databases outside the repository before pruning them.
- Prune only generated databases such as `*.sqlite`, `*.sqlite3`, `*.db`, `*-wal`, and `*-shm`; keep this README.
- Never remove a database that is the only record of a background run until its review status has been summarized elsewhere.

Generated SQLite logs remain provenance and workflow records only. They are not
detections, not discoveries, not external validation, and not submission
approval.
