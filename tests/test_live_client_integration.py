"""Integration tests for live catalog clients (default off, opt-in via env var)."""
from __future__ import annotations

import os

import pytest

from techno_search.live_data import (
    GaiaAdapter,
    GaiaLiveClient,
    LiveDataDisabledError,
    SimbadAdapter,
    SimbadLiveClient,
)

# ---------------------------------------------------------------------------
# Default-off guard tests (always run)
# ---------------------------------------------------------------------------


def test_gaia_live_client_disabled_by_default() -> None:
    client = GaiaLiveClient()
    adapter = GaiaAdapter.from_client(client)
    request = adapter.build_cone_search_request(
        ra_deg=83.8221, dec_deg=22.0145, radius_arcsec=36.0
    )
    with pytest.raises(LiveDataDisabledError):
        client.fetch_metadata(request)


def test_simbad_live_client_disabled_by_default() -> None:
    client = SimbadLiveClient()
    request_obj = SimbadAdapter().build_object_lookup_request(object_name="Vega")
    with pytest.raises(LiveDataDisabledError):
        client.fetch_metadata(request_obj)


def test_gaia_adapter_request_shape() -> None:
    adapter = GaiaAdapter()
    req = adapter.build_cone_search_request(
        ra_deg=83.8221, dec_deg=22.0145, radius_arcsec=180.0
    )
    assert req.source_name == "gaia"
    assert "83.8221" in req.query or "83" in req.query
    assert req.cache_key() != ""


def test_simbad_adapter_request_shape() -> None:
    adapter = SimbadAdapter()
    req = adapter.build_object_lookup_request(object_name="HIP 27989")
    assert req.source_name == "simbad"
    assert "HIP 27989" in req.query
    assert req.cache_key() != ""


# ---------------------------------------------------------------------------
# Live integration tests (only run when TECHNO_SEARCH_ENABLE_LIVE_DATA=1)
# ---------------------------------------------------------------------------


@pytest.mark.integration_live
def test_gaia_tap_live_query_returns_metadata() -> None:
    """Query Gaia TAP for a bright star cone search — requires live network."""
    os.environ["TECHNO_SEARCH_ENABLE_LIVE_DATA"] = "1"
    try:
        client = GaiaLiveClient()
        adapter = GaiaAdapter.from_client(client)
        request = adapter.build_cone_search_request(
            ra_deg=83.8221, dec_deg=22.0145, radius_arcsec=36.0
        )
        metadata = client.fetch_metadata(request)
        assert metadata["provider_status"] == "live"
        assert "content_bytes" in metadata
        assert metadata["content_bytes"] > 0
    finally:
        del os.environ["TECHNO_SEARCH_ENABLE_LIVE_DATA"]


@pytest.mark.integration_live
def test_simbad_live_object_lookup_returns_metadata() -> None:
    """Query SIMBAD for Vega — requires live network."""
    os.environ["TECHNO_SEARCH_ENABLE_LIVE_DATA"] = "1"
    try:
        client = SimbadLiveClient()
        adapter = SimbadAdapter()
        request = adapter.build_object_lookup_request(object_name="Vega")
        metadata = client.fetch_metadata(request)
        assert metadata["provider_status"] == "live"
        assert metadata["content_bytes"] > 0
    finally:
        del os.environ["TECHNO_SEARCH_ENABLE_LIVE_DATA"]
