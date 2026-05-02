import json
import os

import pytest

from techno_search.live_data import (
    CATALOG_CACHE_DIR_ENV_VAR,
    LIVE_CACHE_DIR_ENV_VAR,
    LIVE_DATA_ENV_VAR,
    BreakthroughListenAdapter,
    BreakthroughListenLiveClient,
    CatalogCachePolicy,
    GaiaAdapter,
    GaiaLiveClient,
    IrsaAdapter,
    IrsaLiveClient,
    LiveDataClient,
    LiveDataDisabledError,
    LiveDataRequest,
    LiveProviderAdapter,
    LiveProviderCache,
    ProvenanceOnlyResponseNormalizer,
    SimbadAdapter,
    SimbadLiveClient,
    VizierAdapter,
    VizierLiveClient,
    configured_catalog_cache_dir,
    configured_live_cache_dir,
    default_live_metadata_fixture_dir,
    fetcher_from_client,
    live_data_enabled,
    load_live_metadata_fixture,
    provider_adapters,
    provider_response_metadata,
    require_live_data_enabled,
    validate_catalog_cache_commit_paths,
)


class FixtureMetadataClient:
    def __init__(self, provider_name: str, fixture_name: str) -> None:
        self.provider_name = provider_name
        self.fixture_name = fixture_name

    def fetch_metadata(self, request: LiveDataRequest) -> dict[str, object]:
        fixture_path = default_live_metadata_fixture_dir() / self.fixture_name
        fixture = load_live_metadata_fixture(fixture_path)
        return {
            "fixture_provider_name": fixture["provider_name"],
            "fixture_cache_key": fixture["request"]["cache_key"],
            "request_cache_key": request.cache_key(),
        }


def test_live_data_integrations_are_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv(LIVE_DATA_ENV_VAR, raising=False)

    assert live_data_enabled() is False
    with pytest.raises(LiveDataDisabledError):
        require_live_data_enabled()


def test_provider_adapters_build_requests_without_network(monkeypatch) -> None:
    monkeypatch.delenv(LIVE_DATA_ENV_VAR, raising=False)

    adapters = provider_adapters()

    assert {adapter.provider_name for adapter in adapters} == {
        "breakthrough_listen",
        "gaia",
        "irsa",
        "simbad",
        "vizier",
    }
    for adapter in adapters:
        request = adapter.build_request(
            "synthetic target",
            purpose="unit-test",
            parameters={"radius_arcsec": "5"},
        )

        assert request.source_name == adapter.provider_name
        assert request.parameters == {"radius_arcsec": "5"}
        assert request.service_url == adapter.service_url
        assert request.provenance_record().as_dict()["provider_name"] == adapter.provider_name
        with pytest.raises(LiveDataDisabledError):
            adapter.fetch_metadata(request)


def test_breakthrough_listen_live_metadata_fixture_loads_without_network(monkeypatch) -> None:
    monkeypatch.delenv(LIVE_DATA_ENV_VAR, raising=False)

    fixture = load_live_metadata_fixture(
        default_live_metadata_fixture_dir()
        / "breakthrough_listen_file_metadata.metadata.json"
    )

    assert live_data_enabled() is False
    assert fixture["provider_name"] == "breakthrough_listen"
    assert fixture["request"]["query_parameters"]["query_type"] == "local_file_metadata"
    assert fixture["request"]["cache_key"] == "fixture-breakthrough-listen-file-metadata-v1"


def test_breakthrough_listen_local_file_request_shape_does_not_read_file(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.delenv(LIVE_DATA_ENV_VAR, raising=False)
    missing_file = tmp_path / "synthetic_observation.h5"

    request = BreakthroughListenAdapter().build_local_file_metadata_request(missing_file)

    assert request.source_name == "breakthrough_listen"
    assert request.query == str(missing_file)
    assert request.parameters == {
        "file_name": "synthetic_observation.h5",
        "file_suffix": ".h5",
        "query_type": "local_file_metadata",
        "interpretation": "provenance_only",
    }
    assert not missing_file.exists()
    with pytest.raises(LiveDataDisabledError):
        BreakthroughListenAdapter().fetch_metadata(request)


def test_breakthrough_listen_live_client_skeleton_is_disabled_and_unimplemented(
    monkeypatch,
) -> None:
    request = BreakthroughListenAdapter().build_request(
        "synthetic_observation.h5",
        purpose="breakthrough-listen-file-metadata",
        parameters={"query_type": "local_file_metadata"},
    )
    client = BreakthroughListenLiveClient()

    monkeypatch.delenv(LIVE_DATA_ENV_VAR, raising=False)
    with pytest.raises(LiveDataDisabledError):
        client.fetch_metadata(request)

    monkeypatch.setenv(LIVE_DATA_ENV_VAR, "1")
    with pytest.raises(NotImplementedError):
        client.fetch_metadata(request)


def test_injected_provider_fetcher_is_called_only_when_live_enabled(monkeypatch) -> None:
    calls: list[str] = []

    def fetcher(request: LiveDataRequest) -> dict[str, object]:
        calls.append(request.query)
        return {"rows": 1, "provider_status": "mocked"}

    adapter = GaiaAdapter(fetcher=fetcher)
    request = adapter.build_request(
        "synthetic target",
        purpose="mocked-unit-test",
        parameters={"radius_arcsec": "5"},
    )

    monkeypatch.delenv(LIVE_DATA_ENV_VAR, raising=False)
    with pytest.raises(LiveDataDisabledError):
        adapter.fetch_metadata(request)
    assert calls == []

    monkeypatch.setenv(LIVE_DATA_ENV_VAR, "1")
    metadata = adapter.fetch_metadata(request)

    assert calls == ["synthetic target"]
    assert metadata["provider_name"] == "gaia"
    assert metadata["response_metadata"]["field_names"] == ["provider_status", "rows"]
    assert metadata["request"]["cache_key"] == request.cache_key()


def test_provider_response_metadata_summarizes_rows_without_interpretation() -> None:
    response = {
        "provider_status": "mocked",
        "rows": [{"source_id": "synthetic-a"}, {"source_id": "synthetic-b"}],
    }

    metadata = provider_response_metadata(response)

    assert metadata == {
        "response_type": "dict",
        "field_names": ["provider_status", "rows"],
        "field_count": 2,
        "row_count": 2,
        "provider_status": "mocked",
    }


def test_provenance_only_response_normalizer_preserves_request_context() -> None:
    adapter = GaiaAdapter()
    request = adapter.build_cone_search_request(
        ra_deg=12.5,
        dec_deg=-4.25,
        radius_arcsec=3.0,
    )

    metadata = ProvenanceOnlyResponseNormalizer().normalize(
        adapter,
        request,
        {"provider_status": "mocked", "rows": []},
    )

    assert metadata["provider_name"] == "gaia"
    assert metadata["service_url"] == adapter.service_url
    assert metadata["request"]["cache_key"] == request.cache_key()
    assert metadata["response_metadata"]["row_count"] == 0
    assert metadata["response_metadata"]["provider_status"] == "mocked"


def test_configured_live_cache_dir_uses_env_or_project_default(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv(LIVE_CACHE_DIR_ENV_VAR, raising=False)

    assert configured_live_cache_dir(project_root=tmp_path) == tmp_path / "cache/live_providers"

    explicit_cache_dir = tmp_path / "local-live-cache"
    monkeypatch.setenv(LIVE_CACHE_DIR_ENV_VAR, str(explicit_cache_dir))

    assert configured_live_cache_dir(project_root=tmp_path) == explicit_cache_dir


def test_catalog_cache_policy_defaults_do_not_create_cache_dirs(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv(CATALOG_CACHE_DIR_ENV_VAR, raising=False)

    policy = CatalogCachePolicy.from_config(project_root=tmp_path)
    data = policy.as_dict()

    assert configured_catalog_cache_dir(project_root=tmp_path) == (
        tmp_path / "cache/catalog_metadata"
    )
    assert policy.cache_root == tmp_path / "cache/catalog_metadata"
    assert data["allowed_suffixes"] == [".metadata.json", ".json"]
    assert data["max_metadata_file_size_bytes"] == 1_048_576
    assert data["creates_directories"] is False
    assert data["implements_catalog_ingestion"] is False
    assert not policy.cache_root.exists()


def test_catalog_cache_policy_uses_local_env_override(tmp_path, monkeypatch) -> None:
    cache_dir = tmp_path / "local-catalog-cache"
    monkeypatch.setenv(CATALOG_CACHE_DIR_ENV_VAR, str(cache_dir))

    policy = CatalogCachePolicy.from_config(project_root=tmp_path)

    assert configured_catalog_cache_dir(project_root=tmp_path) == cache_dir
    assert policy.cache_root == cache_dir
    assert not cache_dir.exists()


def test_catalog_cache_commit_path_validator_rejects_cache_roots(tmp_path) -> None:
    result = validate_catalog_cache_commit_paths(
        [
            tmp_path / "cache/catalog_metadata/gaia/example.metadata.json",
            tmp_path / "data/raw/catalog.csv",
            tmp_path / "artifacts/catalog-cache/rows.json",
        ],
        project_root=tmp_path,
    )

    assert result["ok"] is False
    assert result["checked_path_count"] == 3
    assert result["forbidden_roots"] == ["data", "cache", "artifacts"]
    assert result["errors"] == [
        (
            "Catalog cache path must not be committed: "
            "cache/catalog_metadata/gaia/example.metadata.json"
        ),
        "Catalog cache path must not be committed: data/raw/catalog.csv",
        "Catalog cache path must not be committed: artifacts/catalog-cache/rows.json",
    ]


def test_catalog_cache_commit_path_validator_allows_small_fixture_paths(tmp_path) -> None:
    result = validate_catalog_cache_commit_paths(
        [
            tmp_path / "tests/fixtures/live_metadata/gaia_cone_search.metadata.json",
            tmp_path / "docs/CATALOG_CACHE_POLICY.md",
        ],
        project_root=tmp_path,
    )

    assert result["ok"] is True
    assert result["errors"] == []
    assert result["checked_path_count"] == 2


def test_live_provider_cache_writes_metadata_outside_committed_report_paths(tmp_path) -> None:
    request = GaiaAdapter().build_request(
        "synthetic target",
        purpose="cache-path-test",
        parameters={"radius_arcsec": "5"},
    )
    cache = LiveProviderCache(tmp_path / "cache" / "live_providers")

    metadata_path = cache.write_metadata(request, {"provider_name": "gaia"})

    assert metadata_path == cache.metadata_path(request)
    assert metadata_path.read_text(encoding="utf-8")
    assert cache.read_metadata(request) == {"provider_name": "gaia"}
    assert cache.summary()["by_provider"] == {"gaia": 1}
    assert "examples/reports" not in metadata_path.as_posix()
    assert "examples/batch_reports" not in metadata_path.as_posix()


def test_live_provider_fetch_writes_and_reuses_configured_cache(tmp_path, monkeypatch) -> None:
    calls: list[str] = []

    def fetcher(request: LiveDataRequest) -> dict[str, object]:
        calls.append(request.cache_key())
        return {"rows": 1}

    cache = LiveProviderCache(tmp_path / "cache" / "live_providers")
    adapter = GaiaAdapter(fetcher=fetcher)
    request = adapter.build_request("synthetic target", purpose="cache-fetch-test")

    monkeypatch.setenv(LIVE_DATA_ENV_VAR, "1")

    first = adapter.fetch_metadata(request, cache=cache)
    second = adapter.fetch_metadata(request, cache=cache)

    assert calls == [request.cache_key()]
    assert second == first
    assert cache.metadata_path(request).exists()


def test_provider_client_protocol_can_be_adapted_to_fetcher(monkeypatch) -> None:
    class StubClient:
        provider_name = "stub"

        def fetch_metadata(self, request: LiveDataRequest) -> dict[str, object]:
            return {"query": request.query, "provider_name": self.provider_name}

    client = StubClient()
    adapter = LiveProviderAdapter.from_client(
        provider_name="stub",
        service_url="https://example.invalid/",
        client=client,
    )
    request = adapter.build_request("synthetic target", purpose="client-protocol-test")

    monkeypatch.setenv(LIVE_DATA_ENV_VAR, "1")
    metadata = adapter.fetch_metadata(request)

    assert fetcher_from_client(client)(request)["provider_name"] == "stub"
    assert metadata["provider_name"] == "stub"
    assert metadata["response_metadata"]["field_names"] == ["provider_name", "query"]


def test_gaia_fixture_client_normalizes_through_adapter(monkeypatch) -> None:
    request = GaiaAdapter().build_cone_search_request(
        ra_deg=123.45,
        dec_deg=-54.321,
        radius_arcsec=5.0,
    )
    adapter = LiveProviderAdapter.from_client(
        provider_name="gaia",
        service_url="https://gea.esac.esa.int/archive/",
        client=FixtureMetadataClient("gaia", "gaia_cone_search.metadata.json"),
    )

    monkeypatch.setenv(LIVE_DATA_ENV_VAR, "1")
    metadata = adapter.fetch_metadata(request)

    assert metadata["provider_name"] == "gaia"
    assert metadata["request"]["provider_name"] == "gaia"
    assert metadata["response_metadata"]["field_names"] == [
        "fixture_cache_key",
        "fixture_provider_name",
        "request_cache_key",
    ]


def test_gaia_cone_search_query_shape_is_metadata_only(monkeypatch) -> None:
    monkeypatch.delenv(LIVE_DATA_ENV_VAR, raising=False)

    request = GaiaAdapter().build_cone_search_request(
        ra_deg=123.45,
        dec_deg=-54.321,
        radius_arcsec=5.0,
    )

    assert request.source_name == "gaia"
    assert request.purpose == "gaia-source-crossmatch"
    assert request.parameters == {
        "catalog": "gaiadr3.gaia_source",
        "query_type": "cone_search",
        "ra_deg": "123.45000000",
        "dec_deg": "-54.32100000",
        "radius_arcsec": "5.000000",
    }
    assert "CONTAINS" in request.query
    with pytest.raises(LiveDataDisabledError):
        GaiaAdapter().fetch_metadata(request)


def test_gaia_live_metadata_fixture_loads_without_network(monkeypatch) -> None:
    monkeypatch.delenv(LIVE_DATA_ENV_VAR, raising=False)

    fixture = load_live_metadata_fixture(
        default_live_metadata_fixture_dir() / "gaia_cone_search.metadata.json"
    )

    assert live_data_enabled() is False
    assert fixture["fixture_schema_version"] == "live_metadata_fixture_v1"
    assert fixture["provider_name"] == "gaia"
    assert fixture["request"]["provider_name"] == "gaia"
    assert fixture["request"]["cache_key"] == "fixture-gaia-cone-search-v1"
    assert fixture["response_metadata"]["response_type"] == "dict"


def test_gaia_tap_mock_response_fixture_loads_without_network(monkeypatch) -> None:
    monkeypatch.delenv(LIVE_DATA_ENV_VAR, raising=False)

    fixture = load_live_metadata_fixture(
        default_live_metadata_fixture_dir() / "gaia_tap_mock_response.metadata.json"
    )

    assert live_data_enabled() is False
    assert fixture["provider_name"] == "gaia"
    assert fixture["request"]["cache_key"] == "fixture-gaia-tap-mock-response-v1"
    assert fixture["response_metadata"]["provider_status"] == "mocked"
    assert fixture["response_metadata"]["row_count"] == 1


def test_gaia_live_client_requires_opt_in_and_uses_injected_http(monkeypatch) -> None:
    request = GaiaAdapter().build_cone_search_request(
        ra_deg=123.45,
        dec_deg=-54.321,
        radius_arcsec=5.0,
    )
    calls: list[tuple[str, bytes, float, int]] = []

    def post_bytes(
        url: str,
        payload: bytes,
        timeout_seconds: float,
        max_response_bytes: int,
    ) -> bytes:
        calls.append((url, payload, timeout_seconds, max_response_bytes))
        return json.dumps(
            {
                "metadata": [{"name": "source_id"}, {"name": "ra"}],
                "data": [["123", 123.45]],
            }
        ).encode("utf-8")

    client = GaiaLiveClient(http_post_bytes=post_bytes, timeout_seconds=5.0)

    monkeypatch.delenv(LIVE_DATA_ENV_VAR, raising=False)
    with pytest.raises(LiveDataDisabledError):
        client.fetch_metadata(request)
    assert calls == []

    monkeypatch.setenv(LIVE_DATA_ENV_VAR, "1")
    metadata = client.fetch_metadata(request)

    assert metadata["provider_status"] == "live"
    assert metadata["query_endpoint"] == client.tap_sync_url
    assert metadata["response_format"] == "json"
    assert metadata["rows"] == [{"source_id": "123", "ra": 123.45}]
    assert calls
    assert calls[0][0] == client.tap_sync_url
    assert b"REQUEST=doQuery" in calls[0][1]
    assert b"FORMAT=json" in calls[0][1]


def test_irsa_catalog_query_shape_is_metadata_only(monkeypatch) -> None:
    monkeypatch.delenv(LIVE_DATA_ENV_VAR, raising=False)

    request = IrsaAdapter().build_catalog_cone_request(
        catalog="allwise_p3as_psd",
        ra_deg=123.45,
        dec_deg=-54.321,
        radius_arcsec=10.0,
    )

    assert request.source_name == "irsa"
    assert request.purpose == "irsa-catalog-crossmatch"
    assert request.parameters == {
        "catalog": "allwise_p3as_psd",
        "query_type": "cone_search",
        "ra_deg": "123.45000000",
        "dec_deg": "-54.32100000",
        "radius_arcsec": "10.000000",
    }
    assert "allwise_p3as_psd" in request.query
    with pytest.raises(LiveDataDisabledError):
        IrsaAdapter().fetch_metadata(request)


def test_irsa_live_metadata_fixture_loads_without_network(monkeypatch) -> None:
    monkeypatch.delenv(LIVE_DATA_ENV_VAR, raising=False)

    fixture = load_live_metadata_fixture(
        default_live_metadata_fixture_dir() / "irsa_catalog_cone.metadata.json"
    )

    assert live_data_enabled() is False
    assert fixture["provider_name"] == "irsa"
    assert fixture["request"]["query_parameters"]["catalog"] == "allwise_p3as_psd"
    assert fixture["request"]["cache_key"] == "fixture-irsa-catalog-cone-v1"
    assert fixture["response_metadata"]["field_count"] == 2


def test_irsa_live_client_skeleton_is_disabled_and_unimplemented(monkeypatch) -> None:
    request = IrsaAdapter().build_catalog_cone_request(
        catalog="allwise_p3as_psd",
        ra_deg=123.45,
        dec_deg=-54.321,
        radius_arcsec=10.0,
    )
    client = IrsaLiveClient()

    monkeypatch.delenv(LIVE_DATA_ENV_VAR, raising=False)
    with pytest.raises(LiveDataDisabledError):
        client.fetch_metadata(request)

    monkeypatch.setenv(LIVE_DATA_ENV_VAR, "1")
    with pytest.raises(NotImplementedError):
        client.fetch_metadata(request)


def test_irsa_fixture_client_normalizes_through_adapter(monkeypatch) -> None:
    request = IrsaAdapter().build_catalog_cone_request(
        catalog="allwise_p3as_psd",
        ra_deg=123.45,
        dec_deg=-54.321,
        radius_arcsec=10.0,
    )
    adapter = LiveProviderAdapter.from_client(
        provider_name="irsa",
        service_url="https://irsa.ipac.caltech.edu/",
        client=FixtureMetadataClient("irsa", "irsa_catalog_cone.metadata.json"),
    )

    monkeypatch.setenv(LIVE_DATA_ENV_VAR, "1")
    metadata = adapter.fetch_metadata(request)

    assert metadata["provider_name"] == "irsa"
    assert metadata["request"]["provider_name"] == "irsa"
    assert metadata["response_metadata"]["field_count"] == 3


def test_vizier_catalog_query_shape_uses_provenance_only_metadata(monkeypatch) -> None:
    monkeypatch.delenv(LIVE_DATA_ENV_VAR, raising=False)

    request = VizierAdapter().build_catalog_cone_request(
        catalog="II/328/allwise",
        ra_deg=123.45,
        dec_deg=-54.321,
        radius_arcsec=10.0,
    )

    assert request.source_name == "vizier"
    assert request.parameters is not None
    assert request.parameters["interpretation"] == "provenance_only"
    assert request.provenance_record().as_dict()["provider_name"] == "vizier"
    with pytest.raises(LiveDataDisabledError):
        VizierAdapter().fetch_metadata(request)


def test_vizier_live_metadata_fixture_loads_without_network(monkeypatch) -> None:
    monkeypatch.delenv(LIVE_DATA_ENV_VAR, raising=False)

    fixture = load_live_metadata_fixture(
        default_live_metadata_fixture_dir() / "vizier_catalog_cone.metadata.json"
    )

    assert live_data_enabled() is False
    assert fixture["provider_name"] == "vizier"
    assert fixture["request"]["query_parameters"]["interpretation"] == "provenance_only"
    assert fixture["request"]["cache_key"] == "fixture-vizier-catalog-cone-v1"
    assert "candidate" not in fixture


def test_vizier_fixture_client_normalizes_through_adapter(monkeypatch) -> None:
    request = VizierAdapter().build_catalog_cone_request(
        catalog="II/328/allwise",
        ra_deg=123.45,
        dec_deg=-54.321,
        radius_arcsec=10.0,
    )
    adapter = LiveProviderAdapter.from_client(
        provider_name="vizier",
        service_url="https://vizier.cds.unistra.fr/",
        client=FixtureMetadataClient("vizier", "vizier_catalog_cone.metadata.json"),
    )

    monkeypatch.setenv(LIVE_DATA_ENV_VAR, "1")
    metadata = adapter.fetch_metadata(request)

    assert metadata["provider_name"] == "vizier"
    assert metadata["request"]["query_parameters"]["interpretation"] == "provenance_only"
    assert metadata["response_metadata"]["field_count"] == 3


def test_vizier_live_client_skeleton_is_disabled_and_unimplemented(monkeypatch) -> None:
    request = VizierAdapter().build_catalog_cone_request(
        catalog="II/328/allwise",
        ra_deg=123.45,
        dec_deg=-54.321,
        radius_arcsec=10.0,
    )
    client = VizierLiveClient()

    monkeypatch.delenv(LIVE_DATA_ENV_VAR, raising=False)
    with pytest.raises(LiveDataDisabledError):
        client.fetch_metadata(request)

    monkeypatch.setenv(LIVE_DATA_ENV_VAR, "1")
    with pytest.raises(NotImplementedError):
        client.fetch_metadata(request)


def test_simbad_object_lookup_shape_uses_provenance_only_metadata(monkeypatch) -> None:
    monkeypatch.delenv(LIVE_DATA_ENV_VAR, raising=False)

    request = SimbadAdapter().build_object_lookup_request(object_name="synthetic-target")

    assert request.source_name == "simbad"
    assert request.parameters == {
        "object_name": "synthetic-target",
        "query_type": "object_lookup",
        "interpretation": "provenance_only",
    }
    assert request.provenance_record().as_dict()["service_url"] == (
        "https://simbad.cds.unistra.fr/"
    )
    with pytest.raises(LiveDataDisabledError):
        SimbadAdapter().fetch_metadata(request)


def test_simbad_live_metadata_fixture_loads_without_network(monkeypatch) -> None:
    monkeypatch.delenv(LIVE_DATA_ENV_VAR, raising=False)

    fixture = load_live_metadata_fixture(
        default_live_metadata_fixture_dir() / "simbad_object_lookup.metadata.json"
    )

    assert live_data_enabled() is False
    assert fixture["provider_name"] == "simbad"
    assert fixture["request"]["query_parameters"]["object_name"] == "synthetic-target"
    assert fixture["request"]["query_parameters"]["interpretation"] == "provenance_only"
    assert fixture["request"]["cache_key"] == "fixture-simbad-object-lookup-v1"


def test_simbad_fixture_client_normalizes_through_adapter(monkeypatch) -> None:
    request = SimbadAdapter().build_object_lookup_request(object_name="synthetic-target")
    adapter = LiveProviderAdapter.from_client(
        provider_name="simbad",
        service_url="https://simbad.cds.unistra.fr/",
        client=FixtureMetadataClient("simbad", "simbad_object_lookup.metadata.json"),
    )

    monkeypatch.setenv(LIVE_DATA_ENV_VAR, "1")
    metadata = adapter.fetch_metadata(request)

    assert metadata["provider_name"] == "simbad"
    assert metadata["request"]["query_parameters"]["interpretation"] == "provenance_only"
    assert metadata["response_metadata"]["field_names"] == [
        "fixture_cache_key",
        "fixture_provider_name",
        "request_cache_key",
    ]


def test_simbad_live_client_skeleton_is_disabled_and_unimplemented(monkeypatch) -> None:
    request = SimbadAdapter().build_object_lookup_request(object_name="synthetic-target")
    client = SimbadLiveClient()

    monkeypatch.delenv(LIVE_DATA_ENV_VAR, raising=False)
    with pytest.raises(LiveDataDisabledError):
        client.fetch_metadata(request)

    monkeypatch.setenv(LIVE_DATA_ENV_VAR, "1")
    with pytest.raises(NotImplementedError):
        client.fetch_metadata(request)


@pytest.mark.integration_live
@pytest.mark.skipif(
    os.environ.get(LIVE_DATA_ENV_VAR) != "1",
    reason="live-data integration scaffold is opt-in",
)
def test_gaia_live_client_integration_marker_uses_injected_transport() -> None:
    request = GaiaAdapter().build_cone_search_request(
        ra_deg=123.45,
        dec_deg=-54.321,
        radius_arcsec=5.0,
    )

    def post_bytes(
        url: str,
        payload: bytes,
        timeout_seconds: float,
        max_response_bytes: int,
    ) -> bytes:
        return json.dumps({"metadata": [{"name": "source_id"}], "data": [["123"]]}).encode(
            "utf-8"
        )

    metadata = GaiaLiveClient(http_post_bytes=post_bytes).fetch_metadata(request)

    assert metadata["provider_status"] == "live"
    assert metadata["rows"] == [{"source_id": "123"}]


@pytest.mark.integration_live
@pytest.mark.skipif(
    os.environ.get(LIVE_DATA_ENV_VAR) != "1",
    reason="live-data integration scaffold is opt-in",
)
def test_live_data_scaffold_requires_concrete_adapter() -> None:
    request = LiveDataRequest(
        source_name="example-provider",
        query="synthetic target",
        purpose="adapter scaffold test",
    )

    with pytest.raises(NotImplementedError):
        LiveDataClient().fetch_metadata(request)
