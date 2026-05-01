"""Opt-in live-data integration scaffold.

Default tests and workflows must not contact external services. This module only
provides a guarded interface for future live integrations.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from techno_search.provenance import ProvenanceRecord, build_provenance_record

LIVE_DATA_ENV_VAR = "TECHNO_SEARCH_ENABLE_LIVE_DATA"


@dataclass(frozen=True)
class LiveDataRequest:
    """Minimal request descriptor for future live-data adapters."""

    source_name: str
    query: str
    purpose: str
    parameters: dict[str, str] | None = None

    def provenance_record(self) -> ProvenanceRecord:
        """Return a provenance record for this request without network access."""

        return build_provenance_record(
            provider_name=self.source_name,
            query_parameters={"query": self.query, "purpose": self.purpose}
            | (self.parameters or {}),
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


@dataclass(frozen=True)
class LiveProviderAdapter:
    """Provider-specific interface that remains guarded by default."""

    provider_name: str
    service_url: str

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
            parameters=parameters,
        )

    def fetch_metadata(self, request: LiveDataRequest) -> dict[str, Any]:
        """Guard future provider access behind explicit opt-in."""

        require_live_data_enabled()
        msg = f"No live-data adapter is implemented for {self.provider_name!r}."
        raise NotImplementedError(msg)


class GaiaAdapter(LiveProviderAdapter):
    def __init__(self) -> None:
        super().__init__("gaia", "https://gea.esac.esa.int/archive/")


class IrsaAdapter(LiveProviderAdapter):
    def __init__(self) -> None:
        super().__init__("irsa", "https://irsa.ipac.caltech.edu/")


class VizierAdapter(LiveProviderAdapter):
    def __init__(self) -> None:
        super().__init__("vizier", "https://vizier.cds.unistra.fr/")


class SimbadAdapter(LiveProviderAdapter):
    def __init__(self) -> None:
        super().__init__("simbad", "https://simbad.cds.unistra.fr/")


class BreakthroughListenAdapter(LiveProviderAdapter):
    def __init__(self) -> None:
        super().__init__("breakthrough_listen", "https://breakthroughinitiatives.org/")


def provider_adapters() -> tuple[LiveProviderAdapter, ...]:
    """Return known provider adapters without performing network access."""

    return (
        GaiaAdapter(),
        IrsaAdapter(),
        VizierAdapter(),
        SimbadAdapter(),
        BreakthroughListenAdapter(),
    )
