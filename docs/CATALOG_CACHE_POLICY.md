# CATALOG CACHE POLICY

## Purpose

Define guardrails for future catalog cache metadata.

This policy is separate from the existing live-provider metadata cache. The live-provider cache stores normalized request metadata for guarded provider calls. Catalog cache metadata will eventually describe local catalog-like products produced by real provider clients.

No real catalog ingestion is implemented yet.

Print the current policy without creating files:

```bash
.venv/bin/techno-search catalog-cache-policy
```

---

## Metadata Schema

Future catalog cache metadata records should be small JSON objects with:

- `schema_version`
- `provider_name`
- `cache_key`
- `source_query`
- `query_parameters`
- `created_at_utc`
- `config_version`
- `code_commit`
- `source_dataset`
- `row_count`
- `byte_count`
- `content_path`

The metadata record must preserve provenance and must not interpret a source as a technosignature-interest candidate.

---

## Local Storage

Catalog cache metadata should default to:

```text
cache/catalog_metadata/
```

The location may be overridden locally when needed, but cache products and catalog-like data must remain out of version control.

The policy command is informational only. It does not create cache directories, download provider data, or validate real catalog contents.

---

## Boundaries

Allowed in Git:

- tiny synthetic fixtures
- metadata schema documentation
- tests that validate path and provenance rules

Not allowed in Git:

- catalog cache directories
- downloaded catalog rows
- bulk provider payloads
- generated catalog products under `data/`, `cache/`, or `artifacts/`
- API keys or credentials

---

## Scientific Guardrails

Catalog cache metadata is provenance, not evidence of confirmation.

Cached catalog records should support conservative review by preserving source context, negative evidence, and false-positive handling. They must not bypass scoring, pathway classification, or human review.
