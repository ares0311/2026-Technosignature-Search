import json

import pytest

from techno_search.background_search import load_background_priority_config
from techno_search.config import (
    default_scoring_config_path,
    load_scoring_config,
    load_track_config,
)
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


def test_scoring_config_rejects_physical_units_in_probability_fields(
    tmp_path,
) -> None:
    data = json.loads(default_scoring_config_path().read_text(encoding="utf-8"))
    data["pathway_thresholds"]["candidate_signal_reality"] = 45.1
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match=r"probability in \[0, 1\]"):
        load_scoring_config(path)


def test_scoring_config_rejects_descending_snr_thresholds(tmp_path) -> None:
    data = json.loads(default_scoring_config_path().read_text(encoding="utf-8"))
    data["snr_thresholds"] = {
        "noise_floor_snr": 20.0,
        "follow_up_snr": 15.0,
        "high_interest_snr": 40.0,
    }
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="noise_floor <= follow_up <= high_interest"):
        load_scoring_config(path)


def test_scoring_v1_template_is_unit_safe() -> None:
    template_path = (
        default_scoring_config_path().parent / "scoring_v1_template.json"
    )
    config = load_scoring_config(template_path)

    assert config.pathway_thresholds.candidate_signal_reality == 0.7
