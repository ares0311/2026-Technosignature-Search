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

Future adapters should store caches under a configurable local cache directory and record cache keys in provenance. Cache contents should be reproducible from provider, query parameters, software version, and timestamp metadata where possible.

---

## Scientific Guardrails

Live provider matches are evidence inputs, not discovery claims.

Adapters must not label candidates as confirmed technosignatures. They should preserve uncertainty and make false-positive explanations visible for downstream scoring and reporting.
