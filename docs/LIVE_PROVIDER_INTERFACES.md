# LIVE PROVIDER INTERFACES

## Purpose

Define responsibilities for future live-data provider adapters.

The repository currently provides adapter scaffolds only. They must not perform network access in default tests or normal local validation.

---

## Providers

Initial provider interfaces:

- Gaia
- IRSA
- VizieR
- SIMBAD
- Breakthrough Listen

Each adapter should:

- build provider-scoped request metadata without network access
- require `TECHNO_SEARCH_ENABLE_LIVE_DATA=1` before any external request
- preserve provider name, query, purpose, and query parameters
- return raw metadata separately from interpreted candidate features
- expose negative evidence and possible false-positive explanations downstream

---

## Mocked Provider Implementations

Adapters may accept injected fetch functions for tests and future provider clients.

Safe test pattern:

- build a request with `adapter.build_request(...)`
- assert request provenance and cache key fields locally
- leave `TECHNO_SEARCH_ENABLE_LIVE_DATA` unset and assert fetches are rejected
- set `TECHNO_SEARCH_ENABLE_LIVE_DATA=1` only in explicit tests
- use injected fetch functions that return small metadata dictionaries
- normalize responses as provenance-only metadata, not candidate interpretation

---

## Provider Client Protocol

Future real provider clients should implement the `LiveProviderClient` protocol:

- expose a `provider_name`
- implement `fetch_metadata(request)`
- call `require_live_data_enabled()` before any external request
- return raw provider metadata for normalization, not candidate interpretation

Adapters can wrap provider clients through the injected fetch function interface. This keeps real network clients separate from request construction, cache handling, scoring, and reporting.

Current clients:

- `GaiaLiveClient`
- `IrsaLiveClient`
- `VizierLiveClient`
- `SimbadLiveClient`
- `BreakthroughListenLiveClient`

`GaiaLiveClient` has a guarded TAP metadata implementation with injectable transport for tests.
`IrsaLiveClient` has a guarded catalog metadata implementation with injectable transport for tests.
The remaining skeletons require `TECHNO_SEARCH_ENABLE_LIVE_DATA=1` and then raise `NotImplementedError` until real provider implementations are added.

Inspect skeleton status without network access:

```bash
.venv/bin/techno-search live-client-summary
```

Recommended live-client lifecycle:

1. Add a non-networked query-shape builder.
2. Add a tiny normalized live-metadata fixture.
3. Add a disabled client skeleton that requires live opt-in.
4. Add fixture-driven normalization tests through `LiveProviderAdapter.from_client(...)`.
5. Only then add a real provider client, still behind explicit live opt-in and cache/provenance handling.

---

## Query Shape Builders

Provider adapters may expose request builders for common query shapes. These builders must create `LiveDataRequest` descriptors only; they must not perform network access or interpret provider matches.

Current non-networked query-shape builders include:

- Gaia cone search
- IRSA catalog cone search
- VizieR catalog cone search
- SIMBAD object lookup
- Breakthrough Listen local file metadata

The request parameters should preserve catalog names, coordinates, radii, object names, purpose, and any provenance-only interpretation markers needed for downstream audit.

---

## Provenance Fields

Provider-backed requests should record:

- provider name
- service URL
- query string
- query parameters
- deterministic cache key
- request purpose
- generated UTC timestamp
- schema version
- config version
- code commit when available

---

## Cache Policy

Live provider responses and catalog caches must not be committed.

Adapters should store normalized metadata caches under the configurable local cache directory:

```text
cache/live_providers/
```

The cache directory can be overridden with:

```bash
TECHNO_SEARCH_LIVE_CACHE_DIR=/path/to/local/cache
```

Cache files are local reproducibility aids only. They must not be treated as candidate interpretation, external validation, or evidence of confirmation. Cache contents should be reproducible from provider, query parameters, software version, and timestamp metadata where possible.

Inspect cache counts without reading payloads:

```bash
.venv/bin/techno-search live-cache-summary
```

Cleanup may safely remove local cache files when they can be regenerated from recorded provenance. Do not commit cache contents.

---

## Fixture Policy

Committed live metadata fixtures are allowed only when they are tiny, synthetic or redacted normalized metadata records. They should exercise provider request provenance and cache-handling code without requiring network access.

Allowed:

- fixture schema version
- provider name and service URL
- request provenance
- cache key
- response metadata such as field names and field count
- notes explaining that the fixture is synthetic or redacted

Not allowed:

- bulk catalog rows
- downloaded provider payloads
- API credentials or tokens
- candidate interpretation or confirmation language
- cache directories or live cache contents

---

## Scientific Guardrails

Live provider matches are evidence inputs, not discovery claims.

Adapters must not label candidates as confirmed technosignatures. They should preserve uncertainty and make false-positive explanations visible for downstream scoring and reporting.
