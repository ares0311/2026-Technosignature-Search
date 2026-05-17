"""Tests for observation campaign module."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from techno_search.observation_campaign import (
    ALLOWED_CAMPAIGN_STATUSES,
    OBSERVATION_CAMPAIGN_DISCLAIMER,
    OBSERVATION_CAMPAIGN_SCHEMA_VERSION,
    ObservationCampaign,
    load_observation_campaigns,
    observation_campaign_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "observation_campaign.json"


def test_load_campaigns_returns_list():
    result = load_observation_campaigns()
    assert isinstance(result, list)


def test_load_campaigns_returns_dataclass_instances():
    result = load_observation_campaigns()
    assert all(isinstance(c, ObservationCampaign) for c in result)


def test_fixture_has_five_campaigns():
    result = load_observation_campaigns()
    assert len(result) == 5


def test_campaigns_cover_all_three_tracks():
    result = load_observation_campaigns()
    tracks = {c.track for c in result}
    assert "radio" in tracks
    assert "infrared" in tracks
    assert "anomaly" in tracks


def test_campaign_statuses_are_allowed():
    result = load_observation_campaigns()
    for c in result:
        assert c.status in ALLOWED_CAMPAIGN_STATUSES


def test_session_count_non_negative():
    result = load_observation_campaigns()
    for c in result:
        assert c.session_count >= 0


def test_epochs_covered_non_negative():
    result = load_observation_campaigns()
    for c in result:
        assert c.epochs_covered >= 0


def test_target_candidate_ids_is_list():
    result = load_observation_campaigns()
    for c in result:
        assert isinstance(c.target_candidate_ids, list)


def test_as_dict_returns_expected_keys():
    c = load_observation_campaigns()[0]
    d = c.as_dict()
    assert "campaign_id" in d
    assert "track" in d
    assert "status" in d
    assert "session_count" in d
    assert "target_candidate_ids" in d


def test_summary_schema_version():
    result = observation_campaign_summary()
    assert result["schema_version"] == OBSERVATION_CAMPAIGN_SCHEMA_VERSION


def test_summary_disclaimer():
    result = observation_campaign_summary()
    assert result["disclaimer"] == OBSERVATION_CAMPAIGN_DISCLAIMER
    assert "scheduling" in result["disclaimer"]


def test_summary_campaign_count():
    result = observation_campaign_summary()
    assert result["campaign_count"] == 5


def test_summary_active_count():
    result = observation_campaign_summary()
    assert result["active_count"] == 1


def test_summary_completed_count():
    result = observation_campaign_summary()
    assert result["completed_count"] == 2


def test_summary_total_sessions():
    result = observation_campaign_summary()
    assert result["total_sessions"] == 13


def test_summary_by_track():
    result = observation_campaign_summary()
    assert result["by_track"]["radio"] == 2
    assert result["by_track"]["infrared"] == 2
    assert result["by_track"]["anomaly"] == 1


def test_summary_tracks_covered():
    result = observation_campaign_summary()
    assert set(result["tracks_covered"]) == {"radio", "infrared", "anomaly"}


def test_summary_unique_target_candidates():
    result = observation_campaign_summary()
    assert result["unique_target_candidates"] >= 1


def test_allowed_statuses_frozenset():
    assert "planned" in ALLOWED_CAMPAIGN_STATUSES
    assert "active" in ALLOWED_CAMPAIGN_STATUSES
    assert "completed" in ALLOWED_CAMPAIGN_STATUSES
    assert "cancelled" in ALLOWED_CAMPAIGN_STATUSES
    assert "on_hold" in ALLOWED_CAMPAIGN_STATUSES


def test_cli_campaign_summary_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "observation-campaign-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_campaign_summary_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "observation-campaign-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "campaign_count" in data
    assert "active_count" in data


def test_cli_campaign_summary_with_fixture_path():
    result = subprocess.run(
        [
            sys.executable, "-m", "techno_search.cli",
            "observation-campaign-summary",
            "--fixture-path", str(FIXTURE_PATH),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["campaign_count"] == 5
