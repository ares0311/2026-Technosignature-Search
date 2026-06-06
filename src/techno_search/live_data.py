"""Opt-in live-data integration scaffold.

Default tests and workflows must not contact external services. This module only
provides a guarded interface for future live integrations.
"""

from __future__ import annotations

import json
import os
import ssl
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib import parse
from urllib import request as urlrequest

from techno_search.provenance import (
    ProvenanceRecord,
    build_cache_key,
    build_provenance_record,
)

LIVE_DATA_ENV_VAR = "TECHNO_SEARCH_ENABLE_LIVE_DATA"
LIVE_CACHE_DIR_ENV_VAR = "TECHNO_SEARCH_LIVE_CACHE_DIR"
CATALOG_CACHE_DIR_ENV_VAR = "TECHNO_SEARCH_CATALOG_CACHE_DIR"
DEFAULT_LIVE_CACHE_DIR = Path("cache/live_providers")
DEFAULT_CATALOG_CACHE_DIR = Path("cache/catalog_metadata")
LIVE_METADATA_FIXTURE_SCHEMA_VERSION = "live_metadata_fixture_v1"
PROVIDER_NORMALIZATION_REGRESSION_SCHEMA_VERSION = "provider_normalization_regressions_v1"
DEFAULT_CATALOG_CACHE_METADATA_MAX_BYTES = 1_048_576
DEFAULT_CATALOG_CACHE_ALLOWED_SUFFIXES = (".metadata.json", ".json")
DEFAULT_CATALOG_CACHE_REQUIRED_PROVENANCE_FIELDS = (
    "schema_version",
    "provider_name",
    "cache_key",
    "source_query",
    "query_parameters",
    "created_at_utc",
    "config_version",
    "code_commit",
)
CATALOG_CACHE_FORBIDDEN_COMMITTED_ROOTS = ("data", "cache", "artifacts")


def configured_live_cache_dir(project_root: Path | str | None = None) -> Path:
    """Return the configured live-provider cache directory without creating it."""

    configured = os.environ.get(LIVE_CACHE_DIR_ENV_VAR)
    if configured:
        return Path(configured).expanduser()

    root = Path.cwd() if project_root is None else Path(project_root)
    return root / DEFAULT_LIVE_CACHE_DIR


def configured_catalog_cache_dir(project_root: Path | str | None = None) -> Path:
    """Return the configured catalog metadata cache directory without creating it."""

    configured = os.environ.get(CATALOG_CACHE_DIR_ENV_VAR)
    if configured:
        return Path(configured).expanduser()

    root = Path.cwd() if project_root is None else Path(project_root)
    return root / DEFAULT_CATALOG_CACHE_DIR


def default_live_metadata_fixture_dir(project_root: Path | str | None = None) -> Path:
    """Return the repository-local live metadata fixture directory."""

    root = Path(__file__).resolve().parents[2] if project_root is None else Path(project_root)
    return root / "tests" / "fixtures" / "live_metadata"


def default_provider_normalization_regression_path(
    project_root: Path | str | None = None,
) -> Path:
    """Return the repository-local provider normalization regression fixture path."""

    root = Path(__file__).resolve().parents[2] if project_root is None else Path(project_root)
    return root / "tests" / "fixtures" / "provider_normalization_regressions.json"


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


def load_provider_normalization_regressions(
    path: Path | str | None = None,
) -> dict[str, Any]:
    """Load provider normalization regression fixture metadata."""

    fixture_path = (
        default_provider_normalization_regression_path() if path is None else Path(path)
    )
    with fixture_path.open(encoding="utf-8") as handle:
        fixture = json.load(handle)
    if not isinstance(fixture, dict):
        msg = f"Provider normalization regression fixture is not an object: {fixture_path}"
        raise ValueError(msg)
    if fixture.get("schema_version") != PROVIDER_NORMALIZATION_REGRESSION_SCHEMA_VERSION:
        msg = f"Unsupported provider normalization regression schema: {fixture_path}"
        raise ValueError(msg)
    cases = fixture.get("cases")
    if not isinstance(cases, list):
        msg = f"Provider normalization regression fixture missing cases: {fixture_path}"
        raise ValueError(msg)
    return fixture


def provider_normalization_regression_summary(
    path: Path | str | None = None,
) -> dict[str, object]:
    """Summarize provider normalization regression fixture coverage."""

    fixture_path = (
        default_provider_normalization_regression_path() if path is None else Path(path)
    )
    fixture = load_provider_normalization_regressions(fixture_path)
    cases = fixture["cases"]
    provider_counts: dict[str, int] = {}
    expected_fields: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            continue
        provider = str(case.get("provider_name", "unknown"))
        provider_counts[provider] = provider_counts.get(provider, 0) + 1
        fields = case.get("expected_response_metadata_fields", [])
        if isinstance(fields, list):
            expected_fields.update(str(field) for field in fields)

    return {
        "fixture_path": str(fixture_path),
        "schema_version": fixture["schema_version"],
        "case_count": len(cases),
        "provider_count": len(provider_counts),
        "by_provider": dict(sorted(provider_counts.items())),
        "expected_response_metadata_fields": sorted(expected_fields),
    }


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


def live_client_summary() -> dict[str, object]:
    """Return configured live-client skeleton status without network access."""

    clients = (
        GaiaLiveClient(),
        IrsaLiveClient(),
        VizierLiveClient(),
        SimbadLiveClient(),
        BreakthroughListenLiveClient(),
    )
    return {
        "live_enabled": live_data_enabled(),
        "client_count": len(clients),
        "clients": [
            {
                "provider_name": client.provider_name,
                "service_url": client.service_url,
                "implemented": bool(getattr(client, "implemented", False)),
                "networked": bool(getattr(client, "networked", False)),
                "local_file_only": bool(getattr(client, "local_file_only", False)),
                "requires_live_opt_in": True,
            }
            for client in clients
        ],
    }


def validate_catalog_cache_commit_paths(
    paths: Sequence[Path | str],
    *,
    project_root: Path | str | None = None,
) -> dict[str, object]:
    """Validate that catalog cache paths are not being prepared for Git commits."""

    root = None if project_root is None else Path(project_root).resolve()
    errors: list[str] = []
    checked_paths: list[str] = []
    for path_value in paths:
        path = Path(path_value)
        checked_paths.append(str(path))
        relative = _relative_to_project(path, root)
        if relative.parts and relative.parts[0] in CATALOG_CACHE_FORBIDDEN_COMMITTED_ROOTS:
            errors.append(f"Catalog cache path must not be committed: {relative.as_posix()}")

    return {
        "ok": not errors,
        "checked_path_count": len(checked_paths),
        "checked_paths": checked_paths,
        "forbidden_roots": list(CATALOG_CACHE_FORBIDDEN_COMMITTED_ROOTS),
        "errors": errors,
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
class CatalogCachePolicy:
    """Guardrails for future catalog cache metadata."""

    cache_root: Path
    max_metadata_file_size_bytes: int = DEFAULT_CATALOG_CACHE_METADATA_MAX_BYTES
    allowed_suffixes: tuple[str, ...] = DEFAULT_CATALOG_CACHE_ALLOWED_SUFFIXES
    required_provenance_fields: tuple[str, ...] = (
        DEFAULT_CATALOG_CACHE_REQUIRED_PROVENANCE_FIELDS
    )

    @classmethod
    def from_config(cls, project_root: Path | str | None = None) -> CatalogCachePolicy:
        """Build the policy from environment or project-local defaults."""

        return cls(cache_root=configured_catalog_cache_dir(project_root=project_root))

    def as_dict(self) -> dict[str, object]:
        """Return a stable JSON-serializable representation."""

        return {
            "cache_root": str(self.cache_root),
            "max_metadata_file_size_bytes": self.max_metadata_file_size_bytes,
            "allowed_suffixes": list(self.allowed_suffixes),
            "required_provenance_fields": list(self.required_provenance_fields),
            "creates_directories": False,
            "implements_catalog_ingestion": False,
        }


@dataclass(frozen=True)
class CatalogCache:
    """Metadata-only storage for future catalog cache records."""

    policy: CatalogCachePolicy

    @classmethod
    def from_config(cls, project_root: Path | str | None = None) -> CatalogCache:
        """Build a catalog cache from configured local policy."""

        return cls(CatalogCachePolicy.from_config(project_root=project_root))

    def metadata_path(self, provider_name: str, cache_key: str) -> Path:
        """Return a provider-scoped metadata path without creating it."""

        return (
            self.policy.cache_root
            / _safe_cache_component(provider_name)
            / f"{_safe_cache_component(cache_key)}.metadata.json"
        )

    def write_metadata(
        self,
        metadata: Mapping[str, Any],
    ) -> Path:
        """Write a small catalog cache metadata record after policy validation."""

        provider_name = str(metadata.get("provider_name", ""))
        cache_key = str(metadata.get("cache_key", ""))
        if not provider_name or not cache_key:
            msg = "Catalog cache metadata requires provider_name and cache_key."
            raise ValueError(msg)

        self._validate_metadata(metadata)
        path = self.metadata_path(provider_name, cache_key)
        if not path.name.endswith(self.policy.allowed_suffixes):
            msg = f"Catalog cache metadata path has unsupported suffix: {path}"
            raise ValueError(msg)
        payload = json.dumps(dict(metadata), indent=2, sort_keys=True) + "\n"
        size_bytes = len(payload.encode("utf-8"))
        if size_bytes > self.policy.max_metadata_file_size_bytes:
            msg = (
                "Catalog cache metadata exceeds "
                f"{self.policy.max_metadata_file_size_bytes} bytes."
            )
            raise ValueError(msg)

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")
        return path

    def read_metadata(self, provider_name: str, cache_key: str) -> dict[str, Any] | None:
        """Read catalog cache metadata when present."""

        path = self.metadata_path(provider_name, cache_key)
        if not path.exists():
            return None
        if path.stat().st_size > self.policy.max_metadata_file_size_bytes:
            msg = f"Catalog cache metadata exceeds policy size: {path}"
            raise ValueError(msg)
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            msg = f"Catalog cache metadata is not an object: {path}"
            raise ValueError(msg)
        self._validate_metadata(data)
        return data

    def summary(self) -> dict[str, object]:
        """Summarize cache metadata files without interpreting catalog contents."""

        provider_counts: dict[str, int] = {}
        total_bytes = 0
        if self.policy.cache_root.exists():
            for metadata_path in self.policy.cache_root.glob("*/*.metadata.json"):
                provider = metadata_path.parent.name
                provider_counts[provider] = provider_counts.get(provider, 0) + 1
                total_bytes += metadata_path.stat().st_size

        return {
            "cache_root": str(self.policy.cache_root),
            "exists": self.policy.cache_root.exists(),
            "metadata_file_count": sum(provider_counts.values()),
            "metadata_total_bytes": total_bytes,
            "by_provider": dict(sorted(provider_counts.items())),
            "max_metadata_file_size_bytes": self.policy.max_metadata_file_size_bytes,
            "allowed_suffixes": list(self.policy.allowed_suffixes),
            "implements_catalog_ingestion": False,
        }

    def _validate_metadata(self, metadata: Mapping[str, Any]) -> None:
        missing = [
            field
            for field in self.policy.required_provenance_fields
            if field not in metadata
        ]
        if missing:
            msg = f"Catalog cache metadata missing required fields: {missing}"
            raise ValueError(msg)


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


def _relative_to_project(path: Path, project_root: Path | None) -> Path:
    if project_root is None:
        return path
    resolved = path.resolve()
    try:
        return resolved.relative_to(project_root)
    except ValueError:
        return path


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
HttpPostBytes = Callable[[str, bytes, float, int], bytes]
HttpGetBytes = Callable[[str, float, int], bytes]


class LiveProviderClient(Protocol):
    """Protocol for future provider clients that can be injected into adapters."""

    provider_name: str

    def fetch_metadata(self, request: LiveDataRequest) -> Mapping[str, Any]:
        """Fetch raw provider metadata for a guarded live-data request."""


class ProviderResponseNormalizer(Protocol):
    """Protocol for converting provider responses into provenance metadata."""

    def normalize(
        self,
        adapter: LiveProviderAdapter,
        request: LiveDataRequest,
        response: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Normalize provider output without scientific interpretation."""


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
        metadata = DEFAULT_PROVIDER_RESPONSE_NORMALIZER.normalize(self, request, response)
        if cache is not None:
            cache.write_metadata(request, metadata)
        return metadata


class GaiaAdapter(LiveProviderAdapter):
    def __init__(self, fetcher: ProviderFetch | None = None) -> None:
        super().__init__("gaia", "https://gea.esac.esa.int/archive/", fetcher)

    @classmethod
    def from_client(cls, client: LiveProviderClient) -> GaiaAdapter:  # type: ignore[override]
        return cls(fetcher_from_client(client))

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


@dataclass(frozen=True)
class GaiaLiveClient:
    """Guarded Gaia TAP client for provenance metadata requests."""

    provider_name = "gaia"
    service_url = "https://gea.esac.esa.int/archive/"
    implemented = True
    networked = True
    local_file_only = False
    tap_sync_url: str = "https://gea.esac.esa.int/tap-server/tap/sync"
    http_post_bytes: HttpPostBytes | None = None
    timeout_seconds: float = 30.0
    max_response_bytes: int = DEFAULT_CATALOG_CACHE_METADATA_MAX_BYTES

    def fetch_metadata(self, request: LiveDataRequest) -> Mapping[str, Any]:
        """Fetch Gaia TAP metadata only when live-data access is enabled."""

        require_live_data_enabled()
        if request.source_name != self.provider_name:
            msg = f"Gaia client cannot fetch request for {request.source_name!r}."
            raise ValueError(msg)

        payload = parse.urlencode(
            {
                "REQUEST": "doQuery",
                "LANG": "ADQL",
                "FORMAT": "json",
                "QUERY": request.query,
            }
        ).encode("utf-8")
        post_bytes = self.http_post_bytes or http_post_bytes
        response_bytes = post_bytes(
            self.tap_sync_url,
            payload,
            self.timeout_seconds,
            self.max_response_bytes,
        )
        decoded = json.loads(response_bytes.decode("utf-8"))
        if not isinstance(decoded, dict):
            msg = "Gaia TAP response must be a JSON object."
            raise ValueError(msg)
        return {
            "provider_status": "live",
            "query_endpoint": self.tap_sync_url,
            "response_format": "json",
            "content_bytes": len(response_bytes),
            "raw_field_names": sorted(str(key) for key in decoded),
            "rows": gaia_tap_rows(decoded),
        }


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


@dataclass(frozen=True)
class IrsaLiveClient:
    """Guarded IRSA catalog client for provenance metadata requests."""

    provider_name = "irsa"
    service_url = "https://irsa.ipac.caltech.edu/"
    implemented = True
    networked = True
    local_file_only = False
    gator_query_url: str = "https://irsa.ipac.caltech.edu/cgi-bin/Gator/nph-query"
    http_get_bytes: HttpGetBytes | None = None
    timeout_seconds: float = 30.0
    max_response_bytes: int = DEFAULT_CATALOG_CACHE_METADATA_MAX_BYTES

    def fetch_metadata(self, request: LiveDataRequest) -> Mapping[str, Any]:
        """Fetch IRSA catalog metadata only when live-data access is enabled."""

        require_live_data_enabled()
        if request.source_name != self.provider_name:
            msg = f"IRSA client cannot fetch request for {request.source_name!r}."
            raise ValueError(msg)
        if request.parameters is None:
            msg = "IRSA request missing query parameters."
            raise ValueError(msg)

        radius_arcsec = float(request.parameters["radius_arcsec"])
        query = parse.urlencode(
            {
                "catalog": request.parameters["catalog"],
                "spatial": "Cone",
                "objstr": (
                    f"{request.parameters['ra_deg']} "
                    f"{request.parameters['dec_deg']}"
                ),
                "radius": f"{radius_arcsec / 3600.0:.10f}",
                "outfmt": "csv",
            }
        )
        query_url = f"{self.gator_query_url}?{query}"
        get_bytes = self.http_get_bytes or http_get_bytes
        response_bytes = get_bytes(query_url, self.timeout_seconds, self.max_response_bytes)
        decoded = response_bytes.decode("utf-8")
        return {
            "provider_status": "live",
            "query_endpoint": self.gator_query_url,
            "response_format": "csv",
            "content_bytes": len(response_bytes),
            "rows": delimited_text_rows(decoded),
        }


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


@dataclass(frozen=True)
class VizierLiveClient:
    """Guarded VizieR catalog client for provenance metadata requests."""

    provider_name = "vizier"
    service_url = "https://vizier.cds.unistra.fr/"
    implemented = True
    networked = True
    local_file_only = False
    asu_tsv_url: str = "https://vizier.cds.unistra.fr/viz-bin/asu-tsv"
    http_get_bytes: HttpGetBytes | None = None
    timeout_seconds: float = 30.0
    max_response_bytes: int = DEFAULT_CATALOG_CACHE_METADATA_MAX_BYTES

    def fetch_metadata(self, request: LiveDataRequest) -> Mapping[str, Any]:
        """Fetch VizieR catalog metadata only when live-data access is enabled."""

        require_live_data_enabled()
        if request.source_name != self.provider_name:
            msg = f"VizieR client cannot fetch request for {request.source_name!r}."
            raise ValueError(msg)
        if request.parameters is None:
            msg = "VizieR request missing query parameters."
            raise ValueError(msg)

        query = parse.urlencode(
            {
                "-source": request.parameters["catalog"],
                "-c": f"{request.parameters['ra_deg']} {request.parameters['dec_deg']}",
                "-c.rs": request.parameters["radius_arcsec"],
                "-out.max": "50",
            }
        )
        query_url = f"{self.asu_tsv_url}?{query}"
        get_bytes = self.http_get_bytes or http_get_bytes
        response_bytes = get_bytes(query_url, self.timeout_seconds, self.max_response_bytes)
        decoded = response_bytes.decode("utf-8")
        return {
            "provider_status": "live",
            "query_endpoint": self.asu_tsv_url,
            "response_format": "tsv",
            "content_bytes": len(response_bytes),
            "rows": delimited_text_rows(decoded),
        }


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


@dataclass(frozen=True)
class SimbadLiveClient:
    """Guarded SIMBAD object-lookup client for provenance metadata requests."""

    provider_name = "simbad"
    service_url = "https://simbad.cds.unistra.fr/"
    implemented = True
    networked = True
    local_file_only = False
    sim_script_url: str = "https://simbad.cds.unistra.fr/simbad/sim-script"
    http_get_bytes: HttpGetBytes | None = None
    timeout_seconds: float = 30.0
    max_response_bytes: int = DEFAULT_CATALOG_CACHE_METADATA_MAX_BYTES

    def fetch_metadata(self, request: LiveDataRequest) -> Mapping[str, Any]:
        """Fetch SIMBAD object metadata only when live-data access is enabled."""

        require_live_data_enabled()
        if request.source_name != self.provider_name:
            msg = f"SIMBAD client cannot fetch request for {request.source_name!r}."
            raise ValueError(msg)

        script = "\n".join(
            [
                "format object \"main_id\\totype\\tra\\tdec\"",
                f"query id {request.query}",
            ]
        )
        query_url = f"{self.sim_script_url}?{parse.urlencode({'script': script})}"
        get_bytes = self.http_get_bytes or http_get_bytes
        response_bytes = get_bytes(query_url, self.timeout_seconds, self.max_response_bytes)
        decoded = response_bytes.decode("utf-8")
        return {
            "provider_status": "live",
            "query_endpoint": self.sim_script_url,
            "response_format": "tsv",
            "content_bytes": len(response_bytes),
            "rows": delimited_text_rows(decoded),
        }


class BreakthroughListenAdapter(LiveProviderAdapter):
    def __init__(self, fetcher: ProviderFetch | None = None) -> None:
        super().__init__("breakthrough_listen", "https://breakthroughinitiatives.org/", fetcher)

    def build_local_file_metadata_request(
        self,
        file_path: Path | str,
        *,
        purpose: str = "breakthrough-listen-file-metadata",
    ) -> LiveDataRequest:
        """Build a local file metadata descriptor without reading the file."""

        path = Path(file_path)
        return self.build_request(
            str(path),
            purpose=purpose,
            parameters={
                "file_name": path.name,
                "file_suffix": path.suffix,
                "query_type": "local_file_metadata",
                "interpretation": "provenance_only",
            },
        )


@dataclass(frozen=True)
class BreakthroughListenLiveClient:
    """Guarded Breakthrough Listen local-file metadata client."""

    provider_name = "breakthrough_listen"
    service_url = "https://breakthroughinitiatives.org/"
    implemented = True
    networked = False
    local_file_only = True

    def fetch_metadata(self, request: LiveDataRequest) -> Mapping[str, Any]:
        """Inspect local file metadata without reading observation contents."""

        require_live_data_enabled()
        if request.source_name != self.provider_name:
            msg = (
                "Breakthrough Listen client cannot fetch request for "
                f"{request.source_name!r}."
            )
            raise ValueError(msg)
        if request.parameters is None:
            msg = "Breakthrough Listen request missing query parameters."
            raise ValueError(msg)

        path = Path(request.query).expanduser()
        file_exists = path.exists()
        metadata: dict[str, object] = {
            "provider_status": "local_file_metadata",
            "query_endpoint": "local-filesystem",
            "response_format": "file-stat",
            "file_name": request.parameters.get("file_name", path.name),
            "file_suffix": request.parameters.get("file_suffix", path.suffix),
            "file_exists": file_exists,
            "content_read": False,
            "rows": [],
        }
        if file_exists:
            stat = path.stat()
            metadata["size_bytes"] = stat.st_size
            metadata["modified_unix_seconds"] = stat.st_mtime
        return metadata


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
        "response_metadata": provider_response_metadata(response),
    }


@dataclass(frozen=True)
class ProvenanceOnlyResponseNormalizer:
    """Default provider response normalizer for provenance-only metadata."""

    def normalize(
        self,
        adapter: LiveProviderAdapter,
        request: LiveDataRequest,
        response: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Normalize provider output without candidate interpretation."""

        return normalize_provider_response(adapter, request, response)


DEFAULT_PROVIDER_RESPONSE_NORMALIZER = ProvenanceOnlyResponseNormalizer()


def provider_response_metadata(response: Mapping[str, Any]) -> dict[str, object]:
    """Summarize provider response shape without interpreting rows scientifically."""

    metadata: dict[str, object] = {
        "response_type": type(response).__name__,
        "field_names": sorted(str(key) for key in response),
        "field_count": len(response),
    }
    rows = response.get("rows")
    if isinstance(rows, list):
        metadata["row_count"] = len(rows)
        row_field_names: set[str] = set()
        for row in rows:
            if isinstance(row, dict):
                row_field_names.update(str(key) for key in row)
        if row_field_names:
            metadata["row_field_names"] = sorted(row_field_names)
    provider_status = response.get("provider_status")
    if isinstance(provider_status, str):
        metadata["provider_status"] = provider_status
    response_format = response.get("response_format")
    if isinstance(response_format, str):
        metadata["response_format"] = response_format
    query_endpoint = response.get("query_endpoint")
    if isinstance(query_endpoint, str):
        metadata["query_endpoint"] = query_endpoint
    content_bytes = response.get("content_bytes")
    if isinstance(content_bytes, int):
        metadata["content_bytes"] = content_bytes
    raw_field_names = response.get("raw_field_names")
    if isinstance(raw_field_names, list):
        metadata["raw_field_names"] = sorted(str(field) for field in raw_field_names)
    for field_name in (
        "file_name",
        "file_suffix",
        "file_exists",
        "content_read",
        "size_bytes",
    ):
        if field_name in response:
            metadata[field_name] = response[field_name]
    return metadata


def _ssl_context() -> ssl.SSLContext:
    """Return an SSL context using certifi's CA bundle."""
    import certifi  # noqa: PLC0415
    return ssl.create_default_context(cafile=certifi.where())


def http_post_bytes(
    url: str,
    payload: bytes,
    timeout_seconds: float,
    max_response_bytes: int,
) -> bytes:
    """POST to a provider endpoint and return bounded response bytes."""

    post_request = urlrequest.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    ctx = _ssl_context()
    with urlrequest.urlopen(post_request, timeout=timeout_seconds, context=ctx) as response:
        data = bytes(response.read(max_response_bytes + 1))
    if len(data) > max_response_bytes:
        msg = f"Provider response exceeded {max_response_bytes} bytes."
        raise ValueError(msg)
    return data


def http_get_bytes(
    url: str,
    timeout_seconds: float,
    max_response_bytes: int,
) -> bytes:
    """GET from a provider endpoint and return bounded response bytes."""

    with urlrequest.urlopen(url, timeout=timeout_seconds, context=_ssl_context()) as response:
        data = bytes(response.read(max_response_bytes + 1))
    if len(data) > max_response_bytes:
        msg = f"Provider response exceeded {max_response_bytes} bytes."
        raise ValueError(msg)
    return data


def delimited_text_rows(text: str) -> list[dict[str, object]]:
    """Parse a tiny delimited provider table without interpreting values."""

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        return []
    delimiter = "," if "," in lines[0] else "\t"
    field_names = [field.strip() for field in lines[0].split(delimiter)]
    rows: list[dict[str, object]] = []
    for line in lines[1:]:
        values = [value.strip() for value in line.split(delimiter)]
        rows.append(
            {
                field_name: value
                for field_name, value in zip(field_names, values, strict=False)
            }
        )
    return rows


def gaia_tap_rows(response: Mapping[str, Any]) -> list[dict[str, object]]:
    """Extract Gaia TAP rows without assigning scientific meaning."""

    rows = response.get("data")
    if not isinstance(rows, list):
        return []

    field_names = gaia_tap_field_names(response)
    normalized_rows: list[dict[str, object]] = []
    for row in rows:
        if isinstance(row, dict):
            normalized_rows.append(dict(row))
        elif isinstance(row, list) and field_names:
            normalized_rows.append(
                {
                    field_name: value
                    for field_name, value in zip(field_names, row, strict=False)
                }
            )
    return normalized_rows


def gaia_tap_field_names(response: Mapping[str, Any]) -> list[str]:
    """Return Gaia TAP field names from JSON metadata when present."""

    metadata = response.get("metadata")
    if not isinstance(metadata, list):
        return []

    field_names: list[str] = []
    for field in metadata:
        if isinstance(field, dict) and isinstance(field.get("name"), str):
            field_names.append(str(field["name"]))
    return field_names


def provider_adapters() -> tuple[LiveProviderAdapter, ...]:
    """Return known provider adapters without performing network access."""

    return (
        GaiaAdapter(),
        IrsaAdapter(),
        VizierAdapter(),
        SimbadAdapter(),
        BreakthroughListenAdapter(),
    )
