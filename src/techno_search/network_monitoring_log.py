"""Operational provenance records for network monitoring events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

NETWORK_MONITORING_LOG_SCHEMA_VERSION = "network_monitoring_log_v1"
NETWORK_MONITORING_LOG_DISCLAIMER = (
    "Network monitoring log entries are operational provenance records — "
    "a network monitoring event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)
ALLOWED_NETWORK_MONITORING_KINDS = frozenset(
    {
        "bandwidth_check",
        "connectivity_check",
        "latency_probe",
        "packet_loss_check",
        "routing_check",
    }
)
ALLOWED_NETWORK_MONITORING_STATUSES = frozenset(
    {
        "alert",
        "degraded",
        "healthy",
        "unreachable",
    }
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "network_monitoring_log.json"
)


@dataclass(frozen=True)
class NetworkMonitoringEntry:
    entry_id: str
    network_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.network_kind not in ALLOWED_NETWORK_MONITORING_KINDS:
            raise ValueError(f"Invalid network_kind: {self.network_kind!r}")
        if self.status not in ALLOWED_NETWORK_MONITORING_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_network_monitoring_entries(
    path: Path | None = None,
) -> list[NetworkMonitoringEntry]:
    fixture_path = path if path is not None else _DEFAULT_FIXTURE
    raw = json.loads(Path(fixture_path).read_text())
    return [
        NetworkMonitoringEntry(
            entry_id=e["entry_id"],
            network_kind=e["network_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def network_monitoring_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_network_monitoring_entries(path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    healthy_count = 0
    for e in entries:
        by_kind[e.network_kind] = by_kind.get(e.network_kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
        if e.status == "healthy":
            healthy_count += 1
    return {
        "schema_version": NETWORK_MONITORING_LOG_SCHEMA_VERSION,
        "disclaimer": NETWORK_MONITORING_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "healthy_count": healthy_count,
        "by_kind": by_kind,
        "by_status": by_status,
    }
