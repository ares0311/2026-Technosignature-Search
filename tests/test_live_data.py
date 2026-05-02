import os

import pytest

from techno_search.live_data import (
    LIVE_DATA_ENV_VAR,
    GaiaAdapter,
    LiveDataClient,
    LiveDataDisabledError,
    LiveDataRequest,
    live_data_enabled,
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
