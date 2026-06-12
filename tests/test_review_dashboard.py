"""Tests for the operator review dashboard (Tier 2: operator review gap)."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from techno_search.review_dashboard import (
    REVIEW_DASHBOARD_DISCLAIMER,
    review_dashboard_summary,
)


class TestReviewDashboard:
    def test_summary_returns_dict(self) -> None:
        result = review_dashboard_summary()
        assert isinstance(result, dict)

    def test_required_fields_present(self) -> None:
        result = review_dashboard_summary()
        for field in (
            "needs_attention",
            "action_item_count",
            "action_items",
            "open_flags",
            "overdue_deadlines",
            "review_queue_depth",
            "pipeline_blocker_count",
            "real_label_accuracy",
            "real_label_entry_count",
            "real_label_accuracy_gate_ok",
            "disclaimer",
        ):
            assert field in result, f"missing field: {field}"

    def test_disclaimer_is_conservative(self) -> None:
        assert "scheduling aids only" in REVIEW_DASHBOARD_DISCLAIMER
        assert "detection claim" in REVIEW_DASHBOARD_DISCLAIMER

    def test_real_label_accuracy_present(self) -> None:
        result = review_dashboard_summary()
        assert result["real_label_accuracy"] is not None
        assert float(result["real_label_accuracy"]) >= 0.70

    def test_real_label_entry_count_matches_real_file(self) -> None:
        result = review_dashboard_summary()
        assert int(result["real_label_entry_count"]) == 124

    def test_real_label_accuracy_gate_ok(self) -> None:
        result = review_dashboard_summary()
        assert result["real_label_accuracy_gate_ok"] is True

    def test_action_items_is_list(self) -> None:
        result = review_dashboard_summary()
        assert isinstance(result["action_items"], list)

    def test_needs_attention_consistent_with_action_items(self) -> None:
        result = review_dashboard_summary()
        if result["action_item_count"] > 0:
            assert result["needs_attention"] is True
        else:
            assert result["needs_attention"] is False

    def test_cli_command_returns_json(self) -> None:
        proc = subprocess.run(
            [".venv/bin/techno-search", "review-dashboard"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[1],
        )
        data = json.loads(proc.stdout)
        assert "needs_attention" in data
        assert "real_label_accuracy" in data

    def test_cli_exit_code_reflects_needs_attention(self) -> None:
        proc = subprocess.run(
            [".venv/bin/techno-search", "review-dashboard"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[1],
        )
        data = json.loads(proc.stdout)
        if data["needs_attention"]:
            assert proc.returncode == 1
        else:
            assert proc.returncode == 0
