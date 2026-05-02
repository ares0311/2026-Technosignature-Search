import os

import pytest

from techno_search.live_data import (
    LIVE_CACHE_DIR_ENV_VAR,
    LIVE_DATA_ENV_VAR,
    GaiaAdapter,
    GaiaLiveClient,
    IrsaAdapter,
    IrsaLiveClient,
    LiveDataClient,
    LiveDataDisabledError,
    LiveDataRequest,
    LiveProviderAdapter,
    LiveProviderCache,
    SimbadAdapter,
    VizierAdapter,
    configured_live_cache_dir,
    default_live_metadata_fixture_dir,
    fetcher_from_client,
    live_data_enabled,
    load_live_metadata_fixture,
    provider_adapters,
    require_live_data_enabled,
)


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


def test_configured_live_cache_dir_uses_env_or_project_default(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv(LIVE_CACHE_DIR_ENV_VAR, raising=False)

    assert configured_live_cache_dir(project_root=tmp_path) == tmp_path / "cache/live_providers"

    explicit_cache_dir = tmp_path / "local-live-cache"
    monkeypatch.setenv(LIVE_CACHE_DIR_ENV_VAR, str(explicit_cache_dir))

    assert configured_live_cache_dir(project_root=tmp_path) == explicit_cache_dir


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


def test_gaia_live_client_skeleton_is_disabled_and_unimplemented(monkeypatch) -> None:
    request = GaiaAdapter().build_cone_search_request(
        ra_deg=123.45,
        dec_deg=-54.321,
        radius_arcsec=5.0,
    )
    client = GaiaLiveClient()

    monkeypatch.delenv(LIVE_DATA_ENV_VAR, raising=False)
    with pytest.raises(LiveDataDisabledError):
        client.fetch_metadata(request)

    monkeypatch.setenv(LIVE_DATA_ENV_VAR, "1")
    with pytest.raises(NotImplementedError):
        client.fetch_metadata(request)


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
