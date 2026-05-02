"""Opt-in live-data integration scaffold.

Default tests and workflows must not contact external services. This module only
provides a guarded interface for future live integrations.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from techno_search.provenance import (
    ProvenanceRecord,
    build_cache_key,
    build_provenance_record,
)

LIVE_DATA_ENV_VAR = "TECHNO_SEARCH_ENABLE_LIVE_DATA"
LIVE_CACHE_DIR_ENV_VAR = "TECHNO_SEARCH_LIVE_CACHE_DIR"
DEFAULT_LIVE_CACHE_DIR = Path("cache/live_providers")
LIVE_METADATA_FIXTURE_SCHEMA_VERSION = "live_metadata_fixture_v1"


def configured_live_cache_dir(project_root: Path | str | None = None) -> Path:
    """Return the configured live-provider cache directory without creating it."""

    configured = os.environ.get(LIVE_CACHE_DIR_ENV_VAR)
    if configured:
        return Path(configured).expanduser()

    root = Path.cwd() if project_root is None else Path(project_root)
    return root / DEFAULT_LIVE_CACHE_DIR


def default_live_metadata_fixture_dir(project_root: Path | str | None = None) -> Path:
    """Return the repository-local live metadata fixture directory."""

    root = Path(__file__).resolve().parents[2] if project_root is None else Path(project_root)
    return root / "tests" / "fixtures" / "live_metadata"


def load_live_metadata_fixture(path: Path | str) -> dict[str, Any]:
    """Load and validate a normalized live metadata fixture."""

    fixture_path = Path(path)
    with fixture_path.open(encoding="utf-8") as handle:
        fixture = json.load(handle)
    if not isinstance(fixture, dict):
        msg = f"Live metadata fixture is not an object: {fixture_path}"
        raise ValueError(msg)
    _validate_live_metadata_fixture(fixture, fixture_path)
    return fixture


def iter_live_metadata_fixtures(
    fixture_dir: Path | str | None = None,
) -> tuple[dict[str, Any], ...]:
    """Load all repository-local normalized live metadata fixtures."""

    directory = default_live_metadata_fixture_dir() if fixture_dir is None else Path(fixture_dir)
    return tuple(
        load_live_metadata_fixture(path)
        for path in sorted(directory.glob("*.metadata.json"))
    )


def live_metadata_fixture_summary(
    fixture_dir: Path | str | None = None,
) -> dict[str, object]:
    """Summarize committed normalized live metadata fixtures."""

    directory = default_live_metadata_fixture_dir() if fixture_dir is None else Path(fixture_dir)
    fixtures = iter_live_metadata_fixtures(directory)
    provider_counts: dict[str, int] = {}
    for fixture in fixtures:
        provider = str(fixture["provider_name"])
        provider_counts[provider] = provider_counts.get(provider, 0) + 1

    return {
        "fixture_dir": str(directory),
        "fixture_schema_version": LIVE_METADATA_FIXTURE_SCHEMA_VERSION,
        "fixture_count": len(fixtures),
        "by_provider": dict(sorted(provider_counts.items())),
    }


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


@dataclass(frozen=True)
class LiveProviderCache:
    """Small local cache for normalized live-provider metadata records."""

    cache_dir: Path

    @classmethod
    def from_config(cls, project_root: Path | str | None = None) -> LiveProviderCache:
        """Build a cache using the configured live-provider cache directory."""

        return cls(configured_live_cache_dir(project_root=project_root))

    def metadata_path(self, request: LiveDataRequest) -> Path:
        """Return the local cache path for a request metadata record."""

        return (
            self.cache_dir
            / _safe_cache_component(request.source_name)
            / f"{request.cache_key()}.metadata.json"
        )

    def read_metadata(self, request: LiveDataRequest) -> dict[str, Any] | None:
        """Read cached normalized metadata if present."""

        path = self.metadata_path(request)
        if not path.exists():
            return None
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            msg = f"Cached metadata is not an object: {path}"
            raise ValueError(msg)
        return data

    def write_metadata(
        self,
        request: LiveDataRequest,
        metadata: Mapping[str, Any],
    ) -> Path:
        """Write normalized metadata for a live-provider request."""

        path = self.metadata_path(request)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(dict(metadata), indent=2, sort_keys=True) + "\n")
        return path

    def summary(self) -> dict[str, object]:
        """Return cache-directory metadata without reading cached payloads."""

        provider_counts: dict[str, int] = {}
        if self.cache_dir.exists():
            for metadata_path in self.cache_dir.glob("*/*.metadata.json"):
                provider = metadata_path.parent.name
                provider_counts[provider] = provider_counts.get(provider, 0) + 1

        return {
            "cache_dir": str(self.cache_dir),
            "exists": self.cache_dir.exists(),
            "metadata_file_count": sum(provider_counts.values()),
            "by_provider": dict(sorted(provider_counts.items())),
        }


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


def _safe_cache_component(value: str) -> str:
    normalized = value.lower().replace(" ", "_")
    safe = "".join(
        character for character in normalized if character.isalnum() or character in "_-"
    )
    return safe or "unknown"


def _validate_live_metadata_fixture(fixture: Mapping[str, Any], path: Path) -> None:
    if fixture.get("fixture_schema_version") != LIVE_METADATA_FIXTURE_SCHEMA_VERSION:
        msg = f"Unsupported live metadata fixture schema in {path}"
        raise ValueError(msg)

    provider_name = fixture.get("provider_name")
    request = fixture.get("request")
    response_metadata = fixture.get("response_metadata")
    if not isinstance(provider_name, str) or not provider_name:
        msg = f"Live metadata fixture missing provider_name: {path}"
        raise ValueError(msg)
    if not isinstance(request, dict):
        msg = f"Live metadata fixture missing request object: {path}"
        raise ValueError(msg)
    if request.get("provider_name") != provider_name:
        msg = f"Live metadata fixture provider mismatch: {path}"
        raise ValueError(msg)
    if not request.get("cache_key"):
        msg = f"Live metadata fixture missing request cache_key: {path}"
        raise ValueError(msg)
    if not isinstance(response_metadata, dict):
        msg = f"Live metadata fixture missing response_metadata object: {path}"
        raise ValueError(msg)


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


class LiveProviderClient(Protocol):
    """Protocol for future provider clients that can be injected into adapters."""

    provider_name: str

    def fetch_metadata(self, request: LiveDataRequest) -> Mapping[str, Any]:
        """Fetch raw provider metadata for a guarded live-data request."""


def fetcher_from_client(client: LiveProviderClient) -> ProviderFetch:
    """Adapt a provider client object to the injected fetch function interface."""

    return client.fetch_metadata


@dataclass(frozen=True)
class LiveProviderAdapter:
    """Provider-specific interface that remains guarded by default."""

    provider_name: str
    service_url: str
    fetcher: ProviderFetch | None = None

    @classmethod
    def from_client(
        cls,
        *,
        provider_name: str,
        service_url: str,
        client: LiveProviderClient,
    ) -> LiveProviderAdapter:
        """Build an adapter from a provider client without performing network access."""

        return cls(provider_name, service_url, fetcher_from_client(client))

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

    def fetch_metadata(
        self,
        request: LiveDataRequest,
        *,
        cache: LiveProviderCache | None = None,
    ) -> dict[str, Any]:
        """Guard future provider access behind explicit opt-in."""

        require_live_data_enabled()
        if cache is not None:
            cached_metadata = cache.read_metadata(request)
            if cached_metadata is not None:
                return cached_metadata

        if self.fetcher is None:
            msg = f"No live-data adapter is implemented for {self.provider_name!r}."
            raise NotImplementedError(msg)

        response = self.fetcher(request)
        metadata = normalize_provider_response(self, request, response)
        if cache is not None:
            cache.write_metadata(request, metadata)
        return metadata


class GaiaAdapter(LiveProviderAdapter):
    def __init__(self, fetcher: ProviderFetch | None = None) -> None:
        super().__init__("gaia", "https://gea.esac.esa.int/archive/", fetcher)

    def build_cone_search_request(
        self,
        *,
        ra_deg: float,
        dec_deg: float,
        radius_arcsec: float,
        purpose: str = "gaia-source-crossmatch",
        catalog: str = "gaiadr3.gaia_source",
    ) -> LiveDataRequest:
        """Build a Gaia cone-search query descriptor without network access."""

        radius_deg = radius_arcsec / 3600.0
        query = (
            f"SELECT * FROM {catalog} WHERE "
            "1=CONTAINS("
            "POINT('ICRS', ra, dec), "
            f"CIRCLE('ICRS', {ra_deg:.8f}, {dec_deg:.8f}, {radius_deg:.10f})"
            ")"
        )
        return self.build_request(
            query,
            purpose=purpose,
            parameters={
                "catalog": catalog,
                "query_type": "cone_search",
                "ra_deg": f"{ra_deg:.8f}",
                "dec_deg": f"{dec_deg:.8f}",
                "radius_arcsec": f"{radius_arcsec:.6f}",
            },
        )


class GaiaLiveClient:
    """Disabled Gaia live-client skeleton for future provider integration."""

    provider_name = "gaia"
    service_url = "https://gea.esac.esa.int/archive/"

    def fetch_metadata(self, request: LiveDataRequest) -> Mapping[str, Any]:
        """Require live opt-in before future Gaia network implementation."""

        require_live_data_enabled()
        msg = "Gaia live client is not implemented yet."
        raise NotImplementedError(msg)


class IrsaAdapter(LiveProviderAdapter):
    def __init__(self, fetcher: ProviderFetch | None = None) -> None:
        super().__init__("irsa", "https://irsa.ipac.caltech.edu/", fetcher)

    def build_catalog_cone_request(
        self,
        *,
        catalog: str,
        ra_deg: float,
        dec_deg: float,
        radius_arcsec: float,
        purpose: str = "irsa-catalog-crossmatch",
    ) -> LiveDataRequest:
        """Build an IRSA catalog cone-search descriptor without network access."""

        query = f"{catalog} cone search at ra={ra_deg:.8f}, dec={dec_deg:.8f}"
        return self.build_request(
            query,
            purpose=purpose,
            parameters={
                "catalog": catalog,
                "query_type": "cone_search",
                "ra_deg": f"{ra_deg:.8f}",
                "dec_deg": f"{dec_deg:.8f}",
                "radius_arcsec": f"{radius_arcsec:.6f}",
            },
        )


class IrsaLiveClient:
    """Disabled IRSA live-client skeleton for future provider integration."""

    provider_name = "irsa"
    service_url = "https://irsa.ipac.caltech.edu/"

    def fetch_metadata(self, request: LiveDataRequest) -> Mapping[str, Any]:
        """Require live opt-in before future IRSA network implementation."""

        require_live_data_enabled()
        msg = "IRSA live client is not implemented yet."
        raise NotImplementedError(msg)


class VizierAdapter(LiveProviderAdapter):
    def __init__(self, fetcher: ProviderFetch | None = None) -> None:
        super().__init__("vizier", "https://vizier.cds.unistra.fr/", fetcher)

    def build_catalog_cone_request(
        self,
        *,
        catalog: str,
        ra_deg: float,
        dec_deg: float,
        radius_arcsec: float,
        purpose: str = "vizier-catalog-crossmatch",
    ) -> LiveDataRequest:
        """Build a VizieR catalog cone-search descriptor without network access."""

        query = f"{catalog} cone search at ra={ra_deg:.8f}, dec={dec_deg:.8f}"
        return self.build_request(
            query,
            purpose=purpose,
            parameters={
                "catalog": catalog,
                "query_type": "cone_search",
                "ra_deg": f"{ra_deg:.8f}",
                "dec_deg": f"{dec_deg:.8f}",
                "radius_arcsec": f"{radius_arcsec:.6f}",
                "interpretation": "provenance_only",
            },
        )


class SimbadAdapter(LiveProviderAdapter):
    def __init__(self, fetcher: ProviderFetch | None = None) -> None:
        super().__init__("simbad", "https://simbad.cds.unistra.fr/", fetcher)

    def build_object_lookup_request(
        self,
        *,
        object_name: str,
        purpose: str = "simbad-object-context",
    ) -> LiveDataRequest:
        """Build a SIMBAD object lookup descriptor without network access."""

        return self.build_request(
            object_name,
            purpose=purpose,
            parameters={
                "object_name": object_name,
                "query_type": "object_lookup",
                "interpretation": "provenance_only",
            },
        )


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
