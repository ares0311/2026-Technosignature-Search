"""Tests for per-track sensitivity config summary."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

from techno_search.cli import main
from techno_search.sensitivity_config import (
    ALLOWED_TRACKS,
    ALLOWED_WEIGHT_KEYS,
    SENSITIVITY_CONFIG_SCHEMA_VERSION,
    sensitivity_config_summary,
)


def test_sensitivity_config_schema_version() -> None:
    summary = sensitivity_config_summary()
    assert summary["schema_version"] == SENSITIVITY_CONFIG_SCHEMA_VERSION
    assert summary["schema_version"] == "sensitivity_config_summary_v1"


def test_sensitivity_config_disclaimer_is_conservative() -> None:
    from techno_search.sensitivity_config import SENSITIVITY_CONFIG_DISCLAIMER

    summary = sensitivity_config_summary()
    disclaimer = summary["disclaimer"]
    assert isinstance(disclaimer, str)
    assert disclaimer == SENSITIVITY_CONFIG_DISCLAIMER
    assert "scheduling" in disclaimer.lower() or "calibration" in disclaimer.lower()
    assert "not" in disclaimer.lower()
    assert "detection" in disclaimer.lower() or "survey" in disclaimer.lower()


def test_sensitivity_config_covers_all_tracks() -> None:
    summary = sensitivity_config_summary()
    assert set(summary["tracks_present"]) == ALLOWED_TRACKS
    assert summary["track_count"] == 3
    assert summary["missing_tracks"] == []


def test_sensitivity_config_per_track_weights_present() -> None:
    summary = sensitivity_config_summary()
    per_track = summary["per_track_weights"]
    assert isinstance(per_track, dict)
    for track in ALLOWED_TRACKS:
        assert track in per_track
        weights = per_track[track]
        assert set(weights.keys()) == ALLOWED_WEIGHT_KEYS


def test_sensitivity_config_weight_count() -> None:
    summary = sensitivity_config_summary()
    assert isinstance(summary["weight_count"], int)
    assert summary["weight_count"] == len(ALLOWED_TRACKS) * len(ALLOWED_WEIGHT_KEYS)


def test_sensitivity_config_all_weights_in_range() -> None:
    summary = sensitivity_config_summary()
    assert summary["all_weights_in_range"] is True
    per_track = summary["per_track_weights"]
    for track, weights in per_track.items():
        for key, val in weights.items():
            assert 0.0 <= val <= 10.0, f"{track}.{key} = {val} out of range"


def test_sensitivity_config_radio_weights() -> None:
    summary = sensitivity_config_summary()
    radio = summary["per_track_weights"]["radio"]
    assert "signal_weight" in radio
    assert "false_positive_weight" in radio
    assert "provenance_weight" in radio


def test_sensitivity_config_infrared_weights() -> None:
    summary = sensitivity_config_summary()
    infrared = summary["per_track_weights"]["infrared"]
    assert "signal_weight" in infrared
    assert "false_positive_weight" in infrared
    assert "provenance_weight" in infrared


def test_sensitivity_config_anomaly_weights() -> None:
    summary = sensitivity_config_summary()
    anomaly = summary["per_track_weights"]["anomaly"]
    assert "signal_weight" in anomaly
    assert "false_positive_weight" in anomaly
    assert "provenance_weight" in anomaly


def test_sensitivity_config_config_path_is_string() -> None:
    summary = sensitivity_config_summary()
    assert isinstance(summary["config_path"], str)
    assert summary["config_path"].endswith(".json")


def test_sensitivity_config_custom_path(tmp_path: Path) -> None:
    custom_config = {
        "schema_version": "scoring_config_v0",
        "disclaimer": "test",
        "track_sensitivity": {
            "radio": {
                "signal_weight": 0.5,
                "false_positive_weight": 0.8,
                "provenance_weight": 0.6,
            },
            "infrared": {
                "signal_weight": 0.7,
                "false_positive_weight": 0.9,
                "provenance_weight": 0.5,
            },
            "anomaly": {
                "signal_weight": 0.4,
                "false_positive_weight": 0.7,
                "provenance_weight": 0.6,
            },
        },
    }
    config_path = tmp_path / "custom_scoring.json"
    config_path.write_text(json.dumps(custom_config), encoding="utf-8")

    summary = sensitivity_config_summary(config_path)
    assert summary["track_count"] == 3
    assert summary["per_track_weights"]["radio"]["signal_weight"] == 0.5


def test_sensitivity_config_missing_track_sensitivity(tmp_path: Path) -> None:
    custom_config = {
        "schema_version": "scoring_config_v0",
        "disclaimer": "test",
    }
    config_path = tmp_path / "no_sensitivity.json"
    config_path.write_text(json.dumps(custom_config), encoding="utf-8")

    summary = sensitivity_config_summary(config_path)
    assert summary["track_count"] == 0
    assert summary["tracks_present"] == []
    assert set(summary["missing_tracks"]) == ALLOWED_TRACKS


def test_cli_sensitivity_config_summary_exits_zero() -> None:
    stdout = StringIO()
    exit_code = main(["sensitivity-config-summary"], stdout=stdout)
    assert exit_code == 0


def test_cli_sensitivity_config_summary_outputs_json() -> None:
    stdout = StringIO()
    main(["sensitivity-config-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())
    assert result["schema_version"] == "sensitivity_config_summary_v1"
    assert result["track_count"] == 3
    assert "per_track_weights" in result
    assert "disclaimer" in result
