from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SERVICE_REQUEST_LOG_SCHEMA_VERSION = "service_request_log_v1"

ALLOWED_SERVICE_REQUEST_KINDS = frozenset({
    "access_request",
    "hardware_request",
    "information_request",
    "service_catalog_request",
    "software_request",
})

ALLOWED_SERVICE_REQUEST_STATUSES = frozenset({
    "cancelled",
    "fulfilled",
    "in_progress",
    "open",
})

_DISCLAIMER = (
    "Service request entries are operational provenance records — a service request"
    " event does not modify candidate scores or pathway routing, does not authorize"
    " external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "service_request_log.json"
)


@dataclass(frozen=True)
class ServiceRequestEntry:
    entry_id: str
    request_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str

    def __post_init__(self) -> None:
        if self.request_kind not in ALLOWED_SERVICE_REQUEST_KINDS:
            raise ValueError(
                f"request_kind {self.request_kind!r} not in"
                f" {sorted(ALLOWED_SERVICE_REQUEST_KINDS)}"
            )
        if self.status not in ALLOWED_SERVICE_REQUEST_STATUSES:
            raise ValueError(
                f"status {self.status!r} not in"
                f" {sorted(ALLOWED_SERVICE_REQUEST_STATUSES)}"
            )


def load_service_request_entries(
    fixture_path: Path | None = None,
) -> list[ServiceRequestEntry]:
    path = fixture_path or _DEFAULT_FIXTURE
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        ServiceRequestEntry(
            entry_id=e["entry_id"],
            request_kind=e["request_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes", ""),
        )
        for e in data["entries"]
    ]


def service_request_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    entries = load_service_request_entries(fixture_path)
    fulfilled_count = sum(1 for e in entries if e.status == "fulfilled")
    return {
        "schema_version": SERVICE_REQUEST_LOG_SCHEMA_VERSION,
        "entry_count": len(entries),
        "fulfilled_count": fulfilled_count,
        "disclaimer": _DISCLAIMER,
    }
