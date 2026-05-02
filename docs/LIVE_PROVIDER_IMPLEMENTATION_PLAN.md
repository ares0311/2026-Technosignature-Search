# LIVE PROVIDER IMPLEMENTATION PLAN

## Purpose

Define a conservative plan for adding real provider clients after the mocked live-data interfaces, provenance records, catalog cache policy, and validation gates are in place.

Real provider clients must not change the default test contract: default validation remains non-networked, fixture-driven, and reproducible.

---

## Shared Requirements

Every real provider client must:

- require `TECHNO_SEARCH_ENABLE_LIVE_DATA=1` before external access
- preserve provider name, service URL, query parameters, cache key, and code/config provenance
- normalize responses as metadata first, not scientific interpretation
- record negative evidence and blocking issues in later candidate reporting layers
- support injected/mocked fetch behavior for default tests
- keep catalog caches outside committed paths under `data/`, `cache/`, and `artifacts/`
- expose small deterministic fixtures for contract tests
- mark live network tests with `integration_live`

---

## Provider Rollout

1. Gaia
   - Start with TAP-style cone-search metadata.
   - Normalize row count, field names, source query, and provider status.
   - Keep default tests mocked; live tests opt-in only.

2. IRSA
   - Add catalog cone-search metadata for WISE/2MASS-style lookup.
   - Normalize table names, request parameters, row count, and provider status.
   - Reuse the Gaia normalization contract where possible.

3. VizieR
   - Add catalog cone-search metadata for literature catalog context.
   - Preserve catalog identifier and query shape.

4. SIMBAD
   - Add object lookup metadata for known-object context.
   - Treat known-object matches as conservative annotations, not candidate confirmation.

5. Breakthrough Listen
   - Add local file metadata ingestion before any remote data access.
   - Preserve file provenance without committing large observations.

---

## Done Criteria

A provider is implementation-ready when:

- the client is guarded by `TECHNO_SEARCH_ENABLE_LIVE_DATA`
- default tests pass without network access
- mocked fixture tests cover normalization contracts
- `catalog-cache-validate` remains green for committed paths
- release checklist commands pass
- documentation states that provider metadata is provenance support, not discovery evidence
