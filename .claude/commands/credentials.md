# credentials

Check live-data credential availability and inject them for pipeline commands.

## What this does

Reads ATLAS_TOKEN, ZTF_IRSA_USERNAME, and ZTF_IRSA_PASSWORD from the current
shell environment, reports their status, and provides ready-to-run commands
that inject the credentials for live-provider pipeline operations.

## Steps

1. Run this Bash block to check credential presence:

```bash
echo "ATLAS_TOKEN:       ${ATLAS_TOKEN:+PRESENT (${#ATLAS_TOKEN} chars)}"
echo "ZTF_IRSA_USERNAME: ${ZTF_IRSA_USERNAME:+PRESENT}"
echo "ZTF_IRSA_PASSWORD: ${ZTF_IRSA_PASSWORD:+PRESENT}"
```

2. If credentials are present, enable live data with:

```bash
TECHNO_SEARCH_ENABLE_LIVE_DATA=1 \
  ATLAS_TOKEN="${ATLAS_TOKEN}" \
  ZTF_IRSA_USERNAME="${ZTF_IRSA_USERNAME}" \
  ZTF_IRSA_PASSWORD="${ZTF_IRSA_PASSWORD}" \
  .venv/bin/techno-search prod-diagnostics
```

3. For a full live-data production scan (extended corpus):

```bash
TECHNO_SEARCH_ENABLE_LIVE_DATA=1 \
  ATLAS_TOKEN="${ATLAS_TOKEN}" \
  ZTF_IRSA_USERNAME="${ZTF_IRSA_USERNAME}" \
  ZTF_IRSA_PASSWORD="${ZTF_IRSA_PASSWORD}" \
  caffeinate -i bash scripts/run_production_scan.sh \
    --dat-dir data/extended_corpus
```

## Scientific guardrail

No live query result constitutes a detection claim or authorizes external
submission. All results are local citizen-science scheduling aids only.
`validate-all` must pass before any live-data scan proceeds.
