"""Tests for candidate escalation gate (Task 9)."""
from __future__ import annotations

from techno_search.candidate_escalation import (
    ESCALATION_DISCLAIMER,
    ESCALATION_MULTI_EPOCH_GATE,
    ESCALATION_SCHEMA_VERSION,
    ESCALATION_SNR_GATE,
    create_escalation_record,
    escalation_gate_check,
    escalation_summary,
)


def _candidate(
    pathway: str,
    snr: float,
    multi_epoch_persistence_score: float = 0.5,
) -> dict:
    return {
        "candidate_id": f"cand-{snr:.0f}",
        "recommended_pathway": pathway,
        "snr": snr,
        "frequency_hz": 1420e6,
        "multi_epoch_persistence_score": multi_epoch_persistence_score,
    }


class TestEscalationGateCheck:
    def test_fails_closed_when_review_packet_has_high_snr(self) -> None:
        c = _candidate("candidate_review_packet", 50.0, 0.5)
        result = escalation_gate_check(c)
        assert result["passes"] is False
        assert "calibrated SNR gate is unavailable" in result["reason"]

    def test_fails_for_human_review_queue(self) -> None:
        c = _candidate("human_review_queue", 100.0, 0.5)
        result = escalation_gate_check(c)
        assert result["passes"] is False

    def test_fails_for_false_positive_pathway(self) -> None:
        c = _candidate("do_not_submit_false_positive", 200.0, 0.5)
        result = escalation_gate_check(c)
        assert result["passes"] is False

    def test_fails_for_low_snr_without_inventing_a_gate(self) -> None:
        c = _candidate("candidate_review_packet", 1.0, 0.5)
        result = escalation_gate_check(c)
        assert result["passes"] is False

    def test_fails_missing_pathway(self) -> None:
        c = {"candidate_id": "x", "snr": 100.0, "multi_epoch_persistence_score": 0.5}
        result = escalation_gate_check(c)
        assert result["passes"] is False

    def test_calibrated_gate_is_unavailable(self) -> None:
        assert ESCALATION_SNR_GATE is None

    def test_result_is_dict_with_required_keys(self) -> None:
        c = _candidate("candidate_review_packet", 50.0, 0.5)
        result = escalation_gate_check(c)
        for key in (
            "passes",
            "reason",
            "snr",
            "multi_epoch_persistence_score",
            "pathway",
            "calibrated_snr_gate_available",
            "snr_gate",
        ):
            assert key in result, f"missing key: {key}"

    def test_reason_present_on_failure(self) -> None:
        c = _candidate("candidate_review_packet", 1.0, 0.5)
        result = escalation_gate_check(c)
        assert result["passes"] is False
        assert isinstance(result["reason"], str)
        assert len(result["reason"]) > 0

    def test_snr_reflected_in_result(self) -> None:
        c = _candidate("candidate_review_packet", 55.0, 0.5)
        result = escalation_gate_check(c)
        assert result["snr"] == 55.0

    def test_pathway_reflected_in_result(self) -> None:
        c = _candidate("candidate_review_packet", 55.0, 0.5)
        result = escalation_gate_check(c)
        assert result["pathway"] == "candidate_review_packet"

    def test_multi_epoch_gate_constant_is_zero(self) -> None:
        assert ESCALATION_MULTI_EPOCH_GATE == 0.0

    def test_escalation_gate_fails_without_multi_epoch(self) -> None:
        """Missing multi-epoch evidence cannot bypass unavailable calibration."""
        c = _candidate("candidate_review_packet", 100.0, 0.0)
        result = escalation_gate_check(c)
        assert result["passes"] is False
        assert result["multi_epoch_persistence_score"] == 0.0
        assert result["calibrated_snr_gate_available"] is False

    def test_multi_epoch_evidence_does_not_bypass_missing_calibration(self) -> None:
        c = _candidate("candidate_review_packet", 100.0, 0.5)
        result = escalation_gate_check(c)
        assert result["passes"] is False
        assert result["calibrated_snr_gate_available"] is False


class TestCreateEscalationRecord:
    def test_operator_cleared_defaults_false(self) -> None:
        c = _candidate("candidate_review_packet", 60.0)
        record = create_escalation_record(c, "HIP99427", "abc123", "scoring_v0")
        assert record.operator_cleared is False

    def test_external_review_authorized_defaults_false(self) -> None:
        c = _candidate("candidate_review_packet", 60.0)
        record = create_escalation_record(c, "HIP99427", "abc123", "scoring_v0")
        assert record.external_review_authorized is False

    def test_reproduction_checklist_non_empty(self) -> None:
        c = _candidate("candidate_review_packet", 60.0)
        record = create_escalation_record(c, "HIP99427", "sha256abc", "scoring_v0")
        assert len(record.reproduction_checklist) >= 1
        assert any("sha256abc" in item for item in record.reproduction_checklist)

    def test_target_name_stored(self) -> None:
        c = _candidate("candidate_review_packet", 60.0)
        record = create_escalation_record(c, "HIP99427", "x", "scoring_v0")
        assert record.target_name == "HIP99427"

    def test_schema_version(self) -> None:
        c = _candidate("candidate_review_packet", 60.0)
        record = create_escalation_record(c, "T", "x", "v0")
        assert record.schema_version == ESCALATION_SCHEMA_VERSION

    def test_disclaimer(self) -> None:
        c = _candidate("candidate_review_packet", 60.0)
        record = create_escalation_record(c, "T", "x", "v0")
        assert record.disclaimer == ESCALATION_DISCLAIMER
        assert "detection claim" in record.disclaimer

    def test_as_dict_serialisable(self) -> None:
        import json
        c = _candidate("candidate_review_packet", 60.0)
        record = create_escalation_record(c, "T", "x", "v0")
        json.dumps(record.as_dict())  # must not raise

    def test_as_dict_has_required_fields(self) -> None:
        c = _candidate("candidate_review_packet", 60.0)
        record = create_escalation_record(c, "T", "x", "v0")
        d = record.as_dict()
        for field in (
            "escalation_id",
            "candidate_id",
            "target_name",
            "frequency_hz",
            "snr",
            "recommended_pathway",
            "operator_cleared",
            "external_review_authorized",
            "reproduction_checklist",
            "schema_version",
            "disclaimer",
        ):
            assert field in d, f"missing field: {field}"


class TestEscalationSummary:
    def test_empty_list(self) -> None:
        result = escalation_summary([])
        assert result["total_count"] == 0
        assert result["operator_cleared_count"] == 0
        assert result["external_review_authorized_count"] == 0

    def test_counts_cleared(self) -> None:
        c = _candidate("candidate_review_packet", 60.0)
        r1 = create_escalation_record(c, "T", "x", "v0")
        r2 = create_escalation_record(c, "T", "x", "v0")
        r1.operator_cleared = True
        result = escalation_summary([r1, r2])
        assert result["total_count"] == 2
        assert result["operator_cleared_count"] == 1

    def test_external_review_authorized_stays_zero(self) -> None:
        c = _candidate("candidate_review_packet", 60.0)
        records = [create_escalation_record(c, "T", "x", "v0") for _ in range(3)]
        result = escalation_summary(records)
        assert result["external_review_authorized_count"] == 0
