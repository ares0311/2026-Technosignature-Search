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

Maintenance commands:

```bash
.venv/bin/techno-search sqlite-log-pragmas --db-path logs/techno_search.sqlite3
.venv/bin/techno-search sqlite-log-backup --db-path logs/techno_search.sqlite3
.venv/bin/techno-search sqlite-log-retention-summary --db-path logs/techno_search.sqlite3
.venv/bin/techno-search sqlite-log-vacuum --db-path logs/techno_search.sqlite3
```

## Rotation And Retention

- Keep generated databases local unless the project owner explicitly asks for an export.
- Prefer exporting small review-safe JSON summaries with `sqlite-log-export` instead of sharing a full database.
- Use `sqlite-log-backup` to create timestamped local backups under ignored `logs/backups/` before vacuuming or pruning.
- Use `sqlite-log-retention-summary` to review database age, size, and backup coverage before cleanup.
- Prune only generated databases and backups such as `*.sqlite`, `*.sqlite3`, `*.db`, `*-wal`, and `*-shm`; keep this README.
- Never remove a database that is the only record of a background run until its review status has been summarized elsewhere.

Generated SQLite logs remain provenance and workflow records only. They are not
detections, not discoveries, not external validation, and not submission
approval.
