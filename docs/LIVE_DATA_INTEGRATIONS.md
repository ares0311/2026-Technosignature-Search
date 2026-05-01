# LIVE DATA INTEGRATIONS

## Purpose

Define the opt-in policy for future live data integrations.

Default development, tests, and report generation must remain deterministic and offline. Live data access is a future capability for provider-specific adapters, not a default behavior.

---

## Opt-In Guard

Live integrations are disabled unless this environment variable is set:

```bash
export TECHNO_SEARCH_ENABLE_LIVE_DATA=1
```

Code should call:

```python
from techno_search.live_data import require_live_data_enabled

require_live_data_enabled()
```

before any external request is attempted.

---

## Test Policy

Live tests must be marked:

```python
@pytest.mark.integration_live
```

Default validation should continue to use:

```bash
.venv/bin/python -m pytest
```

Live tests should only run when explicitly requested and when the opt-in environment variable is set.

---

## Scientific Guardrails

- Preserve provenance for every live query and response.
- Record provider, query parameters, timestamps, cache keys, and software versions.
- Do not commit live data caches or credentials.
- Treat live results as inputs for conservative review, not as discovery claims.
- Keep negative evidence, blocking issues, and false-positive explanations visible in all outputs.

---

## Current Status

The repository currently includes only a scaffold:

```text
src/techno_search/live_data.py
```

No provider adapter performs network access by default.
