from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CONTRACT_MANAGEMENT_LOG_SCHEMA_VERSION = "contract_management_log_v1"

ALLOWED_CONTRACT_MANAGEMENT_KINDS = frozenset({
    "hardware_contract",
    "service_contract",
    "software_license",
    "support_agreement",
    "vendor_agreement",
})

ALLOWED_CONTRACT_MANAGEMENT_STATUSES = frozenset({
    "active",
    "expired",
    "pending_renewal",
    "terminated",
})

_DISCLAIMER = (
    "Contract management entries are operational provenance records — a contract"
    " management event does not modify candidate scores or pathway routing, does not"
    " authorize external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "contract_management_log.json"
)


@dataclass(frozen=True)
class ContractManagementEntry:
    entry_id: str
    contract_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str

    def __post_init__(self) -> None:
        if self.contract_kind not in ALLOWED_CONTRACT_MANAGEMENT_KINDS:
            raise ValueError(
                f"contract_kind {self.contract_kind!r} not in"
                f" {sorted(ALLOWED_CONTRACT_MANAGEMENT_KINDS)}"
            )
        if self.status not in ALLOWED_CONTRACT_MANAGEMENT_STATUSES:
            raise ValueError(
                f"status {self.status!r} not in"
                f" {sorted(ALLOWED_CONTRACT_MANAGEMENT_STATUSES)}"
            )


def load_contract_management_entries(
    fixture_path: Path | None = None,
) -> list[ContractManagementEntry]:
    path = fixture_path or _DEFAULT_FIXTURE
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        ContractManagementEntry(
            entry_id=e["entry_id"],
            contract_kind=e["contract_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes", ""),
        )
        for e in data["entries"]
    ]


def contract_management_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    entries = load_contract_management_entries(fixture_path)
    active_count = sum(1 for e in entries if e.status == "active")
    return {
        "schema_version": CONTRACT_MANAGEMENT_LOG_SCHEMA_VERSION,
        "entry_count": len(entries),
        "active_count": active_count,
        "disclaimer": _DISCLAIMER,
    }
