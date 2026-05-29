"""Operational provenance records for observatory network connectivity events."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

NETWORK_CONNECTIVITY_LOG_SCHEMA_VERSION = "network_connectivity_log_v1"

NETWORK_CONNECTIVITY_LOG_DISCLAIMER = (
    "Network connectivity log entries are operational provenance records — "
    "a network event record does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

ALLOWED_NETWORK_KINDS = frozenset(
    {
        "link_up",
        "link_down",
        "latency_spike",
        "packet_loss",
        "vpn_event",
    }
)

ALLOWED_NETWORK_STATUSES = frozenset(
    {
        "connected",
        "degraded",
        "disconnected",
        "restored",
    }
)


@dataclass
class NetworkConnectivityEntry:
    entry_id: str
    network_kind: str
    status: str
    recorded_by: str
    timestamp_utc: str
    interface_id: str | None
    latency_ms: float | None
    notes: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "network_kind": self.network_kind,
            "status": self.status,
            "recorded_by": self.recorded_by,
            "timestamp_utc": self.timestamp_utc,
            "interface_id": self.interface_id,
            "latency_ms": self.latency_ms,
            "notes": self.notes,
        }


def load_network_connectivity_entries(
    path: Path | None = None,
) -> list[NetworkConnectivityEntry]:
    if path is None:
        path = (
            Path(__file__).parent.parent.parent
            / "tests"
            / "fixtures"
            / "network_connectivity_log.json"
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        NetworkConnectivityEntry(
            entry_id=e["entry_id"],
            network_kind=e["network_kind"],
            status=e["status"],
            recorded_by=e["recorded_by"],
            timestamp_utc=e["timestamp_utc"],
            interface_id=e.get("interface_id"),
            latency_ms=e.get("latency_ms"),
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def network_connectivity_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_network_connectivity_entries(path)
    counts_by_status: dict[str, int] = {}
    for e in entries:
        counts_by_status[e.status] = counts_by_status.get(e.status, 0) + 1
    counts_by_kind: dict[str, int] = {}
    for e in entries:
        counts_by_kind[e.network_kind] = counts_by_kind.get(e.network_kind, 0) + 1
    return {
        "schema_version": NETWORK_CONNECTIVITY_LOG_SCHEMA_VERSION,
        "disclaimer": NETWORK_CONNECTIVITY_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "connected_count": counts_by_status.get("connected", 0),
        "degraded_count": counts_by_status.get("degraded", 0),
        "disconnected_count": counts_by_status.get("disconnected", 0),
        "restored_count": counts_by_status.get("restored", 0),
        "counts_by_status": counts_by_status,
        "counts_by_kind": counts_by_kind,
    }
