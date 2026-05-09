import pytest

from techno_search.background_search import load_background_priority_config
from techno_search.config import load_scoring_config, load_track_config
from techno_search.schemas import Track


def test_scoring_config_loads_local_performance_defaults() -> None:
    config = load_scoring_config()

    assert config.local_performance_defaults.cpu_heavy_workers == 12
    assert config.local_performance_defaults.light_io_workers == 16
    assert config.local_performance_defaults.memory_budget_gb == 48
    assert config.pathway_thresholds.false_positive_probability == 0.8


@pytest.mark.parametrize(
    ("track", "expected_version"),
    [
        (Track.RADIO, "radio_search_v0"),
        (Track.INFRARED, "infrared_search_v0"),
        (Track.ANOMALY, "anomaly_search_v0"),
    ],
)
def test_track_configs_load(track: Track, expected_version: str) -> None:
    config = load_track_config(track)

    assert config.track == track
    assert config.config_version == expected_version
    assert config.thresholds
    assert config.feature_defaults
    assert config.assumptions


def test_radio_config_preserves_rfi_band_metadata() -> None:
    config = load_track_config(Track.RADIO)

    assert config.raw["rfi_bands_hz"][0]["name"] == "gps_l1"


def test_background_priority_config_is_versioned_and_local_only() -> None:
    config = load_background_priority_config()

    assert config.config_version == "background_priority_v0"
    assert config.weights["followup_value"] == 0.35
    assert config.passive_runner_requires_opt_in is True
    assert config.network_access_enabled is False
