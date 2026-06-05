from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROCUREMENT_LOG_SCHEMA_VERSION = "procurement_log_v1"

ALLOWED_PROCUREMENT_KINDS = frozenset(
    {
        "contract_renewal",
        "emergency_procurement",
        "framework_order",
        "purchase_order",
        "requisition",
    }
)

ALLOWED_PROCUREMENT_STATUSES = frozenset(
    {
        "approved",
        "cancelled",
        "completed",
        "pending",
    }
)

_DISCLAIMER = (
    "Procurement entries are operational provenance records — a procurement "
    "event does not modify candidate scores or pathway routing, does not authorize "
    "external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent / "tests" / "fixtures" / "procurement_log.json"
)


@dataclass(frozen=True)
class ProcurementEntry:
    entry_id: str
    procurement_kind: str
    status: str
    requester_id: str
    description: str
    notes: str = ""

    def __post_init__(self) -> None:
        if self.procurement_kind not in ALLOWED_PROCUREMENT_KINDS:
            raise ValueError(
                f"invalid procurement_kind {self.procurement_kind!r}; "
                f"allowed: {sorted(ALLOWED_PROCUREMENT_KINDS)}"
            )
        if self.status not in ALLOWED_PROCUREMENT_STATUSES:
            raise ValueError(
                f"invalid status {self.status!r}; "
                f"allowed: {sorted(ALLOWED_PROCUREMENT_STATUSES)}"
            )


def load_procurement_entries(path: Path | None = None) -> list[ProcurementEntry]:
    fixture = path if path is not None else _DEFAULT_FIXTURE
    raw = json.loads(fixture.read_text(encoding="utf-8"))
    return [
        ProcurementEntry(
            entry_id=e["entry_id"],
            procurement_kind=e["procurement_kind"],
            status=e["status"],
            requester_id=e["requester_id"],
            description=e["description"],
            notes=e.get("notes", ""),
        )
        for e in raw["entries"]
    ]


def procurement_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_procurement_entries(path)
    completed_count = sum(1 for e in entries if e.status == "completed")
    kind_counts = {k: 0 for k in ALLOWED_PROCUREMENT_KINDS}
    status_counts = {s: 0 for s in ALLOWED_PROCUREMENT_STATUSES}
    for e in entries:
        kind_counts[e.procurement_kind] += 1
        status_counts[e.status] += 1
    return {
        "schema_version": PROCUREMENT_LOG_SCHEMA_VERSION,
        "entry_count": len(entries),
        "completed_count": completed_count,
        "kind_counts": kind_counts,
        "status_counts": status_counts,
        "disclaimer": _DISCLAIMER,
    }
