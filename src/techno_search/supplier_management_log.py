from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SUPPLIER_MANAGEMENT_LOG_SCHEMA_VERSION = "supplier_management_log_v1"

ALLOWED_SUPPLIER_MANAGEMENT_KINDS = frozenset({
    "contractor",
    "consultant",
    "hardware_vendor",
    "service_provider",
    "software_vendor",
})

ALLOWED_SUPPLIER_MANAGEMENT_STATUSES = frozenset({
    "active",
    "inactive",
    "on_probation",
    "terminated",
})

_DISCLAIMER = (
    "Supplier management entries are operational provenance records — a supplier"
    " management event does not modify candidate scores or pathway routing, does not"
    " authorize external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "supplier_management_log.json"
)


@dataclass(frozen=True)
class SupplierManagementEntry:
    entry_id: str
    supplier_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str

    def __post_init__(self) -> None:
        if self.supplier_kind not in ALLOWED_SUPPLIER_MANAGEMENT_KINDS:
            raise ValueError(
                f"supplier_kind {self.supplier_kind!r} not in"
                f" {sorted(ALLOWED_SUPPLIER_MANAGEMENT_KINDS)}"
            )
        if self.status not in ALLOWED_SUPPLIER_MANAGEMENT_STATUSES:
            raise ValueError(
                f"status {self.status!r} not in"
                f" {sorted(ALLOWED_SUPPLIER_MANAGEMENT_STATUSES)}"
            )


def load_supplier_management_entries(
    fixture_path: Path | None = None,
) -> list[SupplierManagementEntry]:
    path = fixture_path or _DEFAULT_FIXTURE
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        SupplierManagementEntry(
            entry_id=e["entry_id"],
            supplier_kind=e["supplier_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes", ""),
        )
        for e in data["entries"]
    ]


def supplier_management_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    entries = load_supplier_management_entries(fixture_path)
    active_count = sum(1 for e in entries if e.status == "active")
    return {
        "schema_version": SUPPLIER_MANAGEMENT_LOG_SCHEMA_VERSION,
        "entry_count": len(entries),
        "active_count": active_count,
        "disclaimer": _DISCLAIMER,
    }
