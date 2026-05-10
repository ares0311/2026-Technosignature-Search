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
