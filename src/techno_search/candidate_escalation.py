"""Candidate escalation gate: gate checks and reproduction checklist."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

ESCALATION_DISCLAIMER = (
    "Escalation records are operator scheduling aids only. "
    "An escalation record does not constitute a detection claim, "
    "does not authorize external submission, and does not imply "
    "scientific confirmation. Independent review requires explicit "
    "operator approval."
)
ESCALATION_SCHEMA_VERSION = "candidate_escalation_v1"
ESCALATION_SNR_GATE = 42.4
ESCALATION_MULTI_EPOCH_GATE = 0.0  # exclusive lower bound; must be > 0.0 to pass


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class CandidateEscalationRecord:
    """Escalation record for a single candidate."""

    escalation_id: str
    candidate_id: str
    target_name: str
    frequency_hz: float
    snr: float
    recommended_pathway: str
    multi_epoch_confirmed: bool
    cross_store_corroborated: bool
    reproduction_checklist: list[str] = field(default_factory=list)
    operator_cleared: bool = False
    external_review_authorized: bool = False
    created_at: str = field(default_factory=_utc_now_iso)
    schema_version: str = ESCALATION_SCHEMA_VERSION
    disclaimer: str = ESCALATION_DISCLAIMER

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "disclaimer": self.disclaimer,
            "escalation_id": self.escalation_id,
            "candidate_id": self.candidate_id,
            "target_name": self.target_name,
            "frequency_hz": self.frequency_hz,
            "snr": self.snr,
            "recommended_pathway": self.recommended_pathway,
            "multi_epoch_confirmed": self.multi_epoch_confirmed,
            "cross_store_corroborated": self.cross_store_corroborated,
            "reproduction_checklist": self.reproduction_checklist,
            "operator_cleared": self.operator_cleared,
            "external_review_authorized": self.external_review_authorized,
            "created_at": self.created_at,
        }


def create_escalation_record(
    candidate_dict: dict[str, Any],
    target_name: str,
    source_data_sha256: str,
    pipeline_config_version: str,
) -> CandidateEscalationRecord:
    """Create an escalation record for a candidate.

    Args:
        candidate_dict: Scored candidate dict with at least
            ``candidate_id``, ``recommended_pathway``, ``snr``,
            ``frequency_hz``.
        target_name: Name of the target being escalated.
        source_data_sha256: SHA-256 of the source data file.
        pipeline_config_version: Version string for the pipeline config.

    Returns:
        A new ``CandidateEscalationRecord`` with operator_cleared and
        external_review_authorized both False.
    """
    cid = candidate_dict.get("candidate_id", "unknown")
    freq = float(candidate_dict.get("frequency_hz", 0.0))
    snr = _get_snr(candidate_dict)
    pathway = candidate_dict.get("recommended_pathway", "unknown")
    multi_epoch = bool(
        candidate_dict.get("multi_epoch_confirmed", False)
    )
    cross_store = bool(
        candidate_dict.get("cross_store_corroborated", False)
    )

    checklist = [
        f"Download data: sha256={source_data_sha256}",
        (
            "Run: techno-search run-pipeline <dat_file> "
            "--track radio --output-dir <output>"
        ),
        f"Config version: {pipeline_config_version}",
        "Verify: pathway matches candidate_review_packet",
        "Independent reviewer confirms SNR measurement",
        (
            "Verify multi-epoch persistence: run pipeline on both epoch .dat files "
            "and confirm multi_epoch_persistence_score > 0 in the scored candidate. "
            "Single-epoch candidates do not pass the escalation gate."
        ),
    ]

    return CandidateEscalationRecord(
        escalation_id=f"esc-{cid}",
        candidate_id=cid,
        target_name=target_name,
        frequency_hz=freq,
        snr=snr,
        recommended_pathway=pathway,
        multi_epoch_confirmed=multi_epoch,
        cross_store_corroborated=cross_store,
        reproduction_checklist=checklist,
        operator_cleared=False,
        external_review_authorized=False,
    )


def _get_snr(candidate_dict: dict[str, Any]) -> float:
    """Extract SNR from a candidate dict, trying multiple field paths."""
    if "snr" in candidate_dict:
        return float(candidate_dict["snr"])
    features = candidate_dict.get("features", {})
    if isinstance(features, dict) and "snr_peak" in features:
        return float(features["snr_peak"])
    return 0.0


def escalation_gate_check(candidate_dict: dict[str, Any]) -> dict[str, Any]:
    """Check whether a candidate passes the escalation gate.

    Returns a structured dict with the result and the reason for pass/fail.
    Passes only if ALL of:
    - ``recommended_pathway`` is ``"candidate_review_packet"``
    - SNR >= ESCALATION_SNR_GATE (42.4)
    - multi_epoch_persistence_score > ESCALATION_MULTI_EPOCH_GATE (0.0)

    Args:
        candidate_dict: Scored candidate dict.

    Returns:
        Dict with keys: ``passes`` (bool), ``reason`` (str), ``snr`` (float),
        ``multi_epoch_persistence_score`` (float), ``pathway`` (str).
    """
    pathway = candidate_dict.get("recommended_pathway", "")
    snr = _get_snr(candidate_dict)
    multi_epoch_persistence_score = float(
        candidate_dict.get("multi_epoch_persistence_score", 0.0)
    )

    if pathway != "candidate_review_packet":
        return {
            "passes": False,
            "reason": (
                f"pathway '{pathway}' is not 'candidate_review_packet'"
            ),
            "snr": snr,
            "multi_epoch_persistence_score": multi_epoch_persistence_score,
            "pathway": pathway,
        }
    if snr < ESCALATION_SNR_GATE:
        return {
            "passes": False,
            "reason": (
                f"SNR {snr:.2f} is below gate {ESCALATION_SNR_GATE}"
            ),
            "snr": snr,
            "multi_epoch_persistence_score": multi_epoch_persistence_score,
            "pathway": pathway,
        }
    if multi_epoch_persistence_score <= ESCALATION_MULTI_EPOCH_GATE:
        return {
            "passes": False,
            "reason": (
                "multi_epoch_persistence_score "
                f"{multi_epoch_persistence_score} is not > "
                f"{ESCALATION_MULTI_EPOCH_GATE}; "
                "single-epoch candidates do not pass the escalation gate"
            ),
            "snr": snr,
            "multi_epoch_persistence_score": multi_epoch_persistence_score,
            "pathway": pathway,
        }
    return {
        "passes": True,
        "reason": "all gates passed",
        "snr": snr,
        "multi_epoch_persistence_score": multi_epoch_persistence_score,
        "pathway": pathway,
    }


def escalation_summary(
    records: list[CandidateEscalationRecord],
) -> dict[str, Any]:
    """Summarise a list of escalation records.

    Args:
        records: List of ``CandidateEscalationRecord`` instances.

    Returns:
        Summary dict with total_count, operator_cleared_count,
        external_review_authorized_count, disclaimer, schema_version.
    """
    return {
        "schema_version": ESCALATION_SCHEMA_VERSION,
        "disclaimer": ESCALATION_DISCLAIMER,
        "total_count": len(records),
        "operator_cleared_count": sum(
            1 for r in records if r.operator_cleared
        ),
        "external_review_authorized_count": sum(
            1 for r in records if r.external_review_authorized
        ),
    }
