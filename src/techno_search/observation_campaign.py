"""Observation campaign — tracks formal multi-session observation campaigns."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

OBSERVATION_CAMPAIGN_SCHEMA_VERSION = "observation_campaign_v1"

OBSERVATION_CAMPAIGN_DISCLAIMER = (
    "Observation campaign records are local scheduling and provenance aids only. "
    "Campaign status reflects operational workflow state, not scientific conclusions. "
    "'completed' means all planned sessions were executed — it does not mean the "
    "science is concluded or any signal confirmed. Campaign records do not modify "
    "candidate posteriors or pathway routing."
)

ALLOWED_CAMPAIGN_STATUSES = frozenset(
    {"planned", "active", "completed", "cancelled", "on_hold"}
)


def _default_campaign_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "observation_campaign.json"
    )


@dataclass
class ObservationCampaign:
    campaign_id: str
    name: str
    track: str
    status: str
    target_candidate_ids: list[str]
    session_count: int
    epochs_covered: int
    start_utc: str
    end_utc: str
    operator_lead: str
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "name": self.name,
            "track": self.track,
            "status": self.status,
            "target_candidate_ids": self.target_candidate_ids,
            "session_count": self.session_count,
            "epochs_covered": self.epochs_covered,
            "start_utc": self.start_utc,
            "end_utc": self.end_utc,
            "operator_lead": self.operator_lead,
            "notes": self.notes,
        }


def load_observation_campaigns(
    fixture_path: Path | None = None,
) -> list[ObservationCampaign]:
    path = fixture_path if fixture_path is not None else _default_campaign_path()
    raw = json.loads(path.read_text())
    campaigns = raw.get("campaigns", [])
    result: list[ObservationCampaign] = []
    for c in campaigns:
        result.append(
            ObservationCampaign(
                campaign_id=str(c["campaign_id"]),
                name=str(c["name"]),
                track=str(c["track"]),
                status=str(c["status"]),
                target_candidate_ids=list(c.get("target_candidate_ids", [])),
                session_count=int(c["session_count"]),
                epochs_covered=int(c["epochs_covered"]),
                start_utc=str(c["start_utc"]),
                end_utc=str(c["end_utc"]),
                operator_lead=str(c["operator_lead"]),
                notes=str(c.get("notes", "")),
            )
        )
    return result


def observation_campaign_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    campaigns = load_observation_campaigns(fixture_path)

    by_track: dict[str, int] = {}
    by_status: dict[str, int] = {}
    active_count = 0
    completed_count = 0
    total_sessions = 0
    total_epochs = 0
    all_candidate_ids: set[str] = set()

    for c in campaigns:
        by_track[c.track] = by_track.get(c.track, 0) + 1
        by_status[c.status] = by_status.get(c.status, 0) + 1
        if c.status == "active":
            active_count += 1
        if c.status == "completed":
            completed_count += 1
        total_sessions += c.session_count
        total_epochs += c.epochs_covered
        all_candidate_ids.update(c.target_candidate_ids)

    return {
        "schema_version": OBSERVATION_CAMPAIGN_SCHEMA_VERSION,
        "disclaimer": OBSERVATION_CAMPAIGN_DISCLAIMER,
        "campaign_count": len(campaigns),
        "active_count": active_count,
        "completed_count": completed_count,
        "total_sessions": total_sessions,
        "total_epochs_covered": total_epochs,
        "unique_target_candidates": len(all_candidate_ids),
        "by_track": dict(sorted(by_track.items())),
        "by_status": dict(sorted(by_status.items())),
        "tracks_covered": sorted(by_track.keys()),
    }
