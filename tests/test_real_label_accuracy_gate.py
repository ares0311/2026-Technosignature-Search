"""Tests for the real-label scoring accuracy regression gate in validate-all.

Closes Tier 2 gap: scoring model accuracy regression gate.
Gate: if examples/real_labeled/hip99427_citizen_science_labels_v1.json exists,
accuracy must be >= 0.70.  Current scoring model v1 achieves 77.42%.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from techno_search.baseline_eval import eval_against_labels

_REAL_LABEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "real_labeled"
    / "hip99427_citizen_science_labels_v1.json"
)
_ACCURACY_GATE = 0.70


class TestRealLabelAccuracyGate:
    """Real-label scoring accuracy must stay at or above the regression gate."""

    def test_real_label_file_exists(self) -> None:
        assert _REAL_LABEL_PATH.exists(), (
            f"Real label file missing: {_REAL_LABEL_PATH}"
        )

    def test_real_label_entry_count_is_124(self) -> None:
        result = eval_against_labels(_REAL_LABEL_PATH)
        assert int(result["entry_count"]) == 124

    def test_real_label_accuracy_meets_gate(self) -> None:
        result = eval_against_labels(_REAL_LABEL_PATH)
        accuracy = float(result["accuracy"])
        assert accuracy >= _ACCURACY_GATE, (
            f"Real-label accuracy {accuracy:.4f} below gate {_ACCURACY_GATE}. "
            "A scoring model change may have caused regression."
        )

    def test_real_label_accuracy_is_at_least_current_v1_level(self) -> None:
        """Accuracy should match scoring model v1 (77.42%) within tolerance."""
        result = eval_against_labels(_REAL_LABEL_PATH)
        accuracy = float(result["accuracy"])
        # Allow 5pp below current level before failing (provides headroom for fixes)
        assert accuracy >= 0.72, (
            f"Accuracy {accuracy:.4f} dropped >5pp below v1 baseline of 0.7742."
        )

    def test_validate_all_includes_real_label_accuracy(self) -> None:
        proc = subprocess.run(
            [".venv/bin/techno-search", "validate-all"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[1],
        )
        data = json.loads(proc.stdout)
        assert "real_label_accuracy" in data
        assert "real_label_accuracy_gate_ok" in data
        assert "real_label_entry_count" in data

    def test_validate_all_real_label_gate_passes(self) -> None:
        proc = subprocess.run(
            [".venv/bin/techno-search", "validate-all"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[1],
        )
        data = json.loads(proc.stdout)
        assert data.get("real_label_accuracy_gate_ok") is True
        assert data.get("ok") is True

    def test_validate_all_real_label_accuracy_value(self) -> None:
        proc = subprocess.run(
            [".venv/bin/techno-search", "validate-all"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[1],
        )
        data = json.loads(proc.stdout)
        accuracy = float(data.get("real_label_accuracy", 0.0))
        assert accuracy >= _ACCURACY_GATE

    def test_validation_summary_includes_real_label_fields(self) -> None:
        proc = subprocess.run(
            [".venv/bin/techno-search", "validation-summary"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[1],
        )
        data = json.loads(proc.stdout)
        assert "real_label_accuracy" in data
        assert "real_label_accuracy_gate_ok" in data
        assert "real_label_entry_count" in data
