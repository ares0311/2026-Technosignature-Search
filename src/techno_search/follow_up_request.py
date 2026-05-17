"""Follow-up request module — formal follow-up requests raised on candidates."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

FOLLOW_UP_REQUEST_SCHEMA_VERSION = "follow_up_request_v1"

FOLLOW_UP_REQUEST_DISCLAIMER = (
    "Follow-up request records are local scheduling coordination aids only. "
    "Request priority reflects operational timeline pressure, not candidate "
    "scientific interest level. An 'urgent' request means a scheduling deadline "
    "is imminent — it does not indicate increased confidence in any technosignature "
    "interpretation. Follow-up requests are provenance records, not detection claims."
)

ALLOWED_REQUEST_PRIORITIES = frozenset({"low", "normal", "high", "urgent"})

ALLOWED_REQUEST_STATUSES = frozenset(
    {"open", "assigned", "in_progress", "completed", "cancelled", "deferred"}
)


def _default_fixture_path() -> Path:
    return Path(__file__).parent.parent.parent / "tests" / "fixtures" / "follow_up_requests.json"


@dataclass
class FollowUpRequest:
    request_id: str
    candidate_id: str
    track: str
    priority: str
    status: str
    requested_by: str
    assigned_to: str
    request_reason: str
    requested_utc: str
    due_utc: str
    days_open: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "candidate_id": self.candidate_id,
            "track": self.track,
            "priority": self.priority,
            "status": self.status,
            "requested_by": self.requested_by,
            "assigned_to": self.assigned_to,
            "request_reason": self.request_reason,
            "requested_utc": self.requested_utc,
            "due_utc": self.due_utc,
            "days_open": self.days_open,
        }


def load_follow_up_requests(fixture_path: Path | None = None) -> list[FollowUpRequest]:
    path = fixture_path or _default_fixture_path()
    with Path(path).open(encoding="utf-8") as fh:
        data = json.load(fh)
    requests = []
    for item in data.get("requests", []):
        requests.append(
            FollowUpRequest(
                request_id=item["request_id"],
                candidate_id=item["candidate_id"],
                track=item["track"],
                priority=item["priority"],
                status=item["status"],
                requested_by=item["requested_by"],
                assigned_to=item.get("assigned_to", ""),
                request_reason=item.get("request_reason", ""),
                requested_utc=item["requested_utc"],
                due_utc=item.get("due_utc", ""),
                days_open=int(item.get("days_open", 0)),
            )
        )
    return requests


def follow_up_request_summary(fixture_path: Path | None = None) -> dict[str, Any]:
    requests = load_follow_up_requests(fixture_path)

    open_statuses = {"open", "assigned", "in_progress"}
    open_count = sum(1 for r in requests if r.status in open_statuses)
    urgent_count = sum(1 for r in requests if r.priority == "urgent")
    overdue_count = sum(
        1 for r in requests if r.status in open_statuses and r.days_open > 14
    )

    total_days = sum(r.days_open for r in requests)
    average_days_open = round(total_days / len(requests), 1) if requests else 0.0

    by_track: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    by_status: dict[str, int] = {}
    requestor_ids: set[str] = set()

    for r in requests:
        by_track[r.track] = by_track.get(r.track, 0) + 1
        by_priority[r.priority] = by_priority.get(r.priority, 0) + 1
        by_status[r.status] = by_status.get(r.status, 0) + 1
        if r.requested_by:
            requestor_ids.add(r.requested_by)

    return {
        "schema_version": FOLLOW_UP_REQUEST_SCHEMA_VERSION,
        "disclaimer": FOLLOW_UP_REQUEST_DISCLAIMER,
        "request_count": len(requests),
        "open_count": open_count,
        "urgent_count": urgent_count,
        "overdue_count": overdue_count,
        "average_days_open": average_days_open,
        "by_track": dict(sorted(by_track.items())),
        "by_priority": dict(sorted(by_priority.items())),
        "by_status": dict(sorted(by_status.items())),
        "tracks_covered": sorted(by_track.keys()),
        "unique_requestors": len(requestor_ids),
    }
