"""Opt-in live-data integration scaffold.

Default tests and workflows must not contact external services. This module only
provides a guarded interface for future live integrations.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from techno_search.provenance import (
    ProvenanceRecord,
    build_cache_key,
    build_provenance_record,
)

LIVE_DATA_ENV_VAR = "TECHNO_SEARCH_ENABLE_LIVE_DATA"


@dataclass(frozen=True)
class LiveDataRequest:
    """Minimal request descriptor for future live-data adapters."""

    source_name: str
    query: str
    purpose: str
    service_url: str | None = None
    parameters: dict[str, str] | None = None

    def cache_key(self) -> str:
        """Return a deterministic cache key for this request."""

        return build_cache_key(
            provider_name=self.source_name,
            query=self.query,
            purpose=self.purpose,
            parameters=self.parameters,
        )

    def provenance_record(self) -> ProvenanceRecord:
        """Return a provenance record for this request without network access."""

        return build_provenance_record(
            provider_name=self.source_name,
            service_url=self.service_url,
            query_parameters={"query": self.query, "purpose": self.purpose}
            | (self.parameters or {}),
            cache_key=self.cache_key(),
        )


class LiveDataDisabledError(RuntimeError):
    """Raised when live-data access is requested without explicit opt-in."""


def live_data_enabled() -> bool:
    """Return whether live-data integrations are explicitly enabled."""

    return os.environ.get(LIVE_DATA_ENV_VAR) == "1"


def require_live_data_enabled() -> None:
    """Require explicit live-data opt-in before any external access is attempted."""

    if not live_data_enabled():
        msg = (
            f"Live-data integrations are disabled. Set {LIVE_DATA_ENV_VAR}=1 only for "
            "explicitly marked integration_live runs."
        )
        raise LiveDataDisabledError(msg)


class LiveDataClient:
    """Base scaffold for future live-data clients."""

    def fetch_metadata(self, request: LiveDataRequest) -> dict[str, str]:
        """Fetch metadata for a live-data request.

        The base implementation never performs network access. Concrete adapters must
        implement provider-specific behavior behind `require_live_data_enabled()`.
        """

        require_live_data_enabled()
        msg = f"No live-data adapter is implemented for {request.source_name!r}."
        raise NotImplementedError(msg)


ProviderFetch = Callable[[LiveDataRequest], Mapping[str, Any]]


@dataclass(frozen=True)
class LiveProviderAdapter:
    """Provider-specific interface that remains guarded by default."""

    provider_name: str
    service_url: str
    fetcher: ProviderFetch | None = None

    def build_request(
        self,
        query: str,
        *,
        purpose: str,
        parameters: dict[str, str] | None = None,
    ) -> LiveDataRequest:
        """Build a provider-scoped live-data request without network access."""

        return LiveDataRequest(
            source_name=self.provider_name,
            query=query,
            purpose=purpose,
            service_url=self.service_url,
            parameters=parameters,
        )

    def fetch_metadata(self, request: LiveDataRequest) -> dict[str, Any]:
        """Guard future provider access behind explicit opt-in."""

        require_live_data_enabled()
        if self.fetcher is None:
            msg = f"No live-data adapter is implemented for {self.provider_name!r}."
            raise NotImplementedError(msg)

        response = self.fetcher(request)
        return normalize_provider_response(self, request, response)


class GaiaAdapter(LiveProviderAdapter):
    def __init__(self, fetcher: ProviderFetch | None = None) -> None:
        super().__init__("gaia", "https://gea.esac.esa.int/archive/", fetcher)


class IrsaAdapter(LiveProviderAdapter):
    def __init__(self, fetcher: ProviderFetch | None = None) -> None:
        super().__init__("irsa", "https://irsa.ipac.caltech.edu/", fetcher)


class VizierAdapter(LiveProviderAdapter):
    def __init__(self, fetcher: ProviderFetch | None = None) -> None:
        super().__init__("vizier", "https://vizier.cds.unistra.fr/", fetcher)


class SimbadAdapter(LiveProviderAdapter):
    def __init__(self, fetcher: ProviderFetch | None = None) -> None:
        super().__init__("simbad", "https://simbad.cds.unistra.fr/", fetcher)


class BreakthroughListenAdapter(LiveProviderAdapter):
    def __init__(self, fetcher: ProviderFetch | None = None) -> None:
        super().__init__("breakthrough_listen", "https://breakthroughinitiatives.org/", fetcher)


def normalize_provider_response(
    adapter: LiveProviderAdapter,
    request: LiveDataRequest,
    response: Mapping[str, Any],
) -> dict[str, Any]:
    """Normalize provider responses as provenance metadata only."""

    return {
        "provider_name": adapter.provider_name,
        "service_url": adapter.service_url,
        "request": request.provenance_record().as_dict(),
        "response_metadata": {
            "response_type": type(response).__name__,
            "field_names": sorted(str(key) for key in response),
            "field_count": len(response),
        },
    }


def provider_adapters() -> tuple[LiveProviderAdapter, ...]:
    """Return known provider adapters without performing network access."""

    return (
        GaiaAdapter(),
        IrsaAdapter(),
        VizierAdapter(),
        SimbadAdapter(),
        BreakthroughListenAdapter(),
    )
