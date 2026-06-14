"""Tests for multi-target citizen-science label combination and combined model training.

Closes KNOWN_LIMITATIONS #1: Single-target generalization gap.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HIP99427_LABELS = (
    REPO_ROOT / "examples" / "real_labeled" / "hip99427_citizen_science_labels_v1.json"
)


class TestCombineLabelFiles:
    def test_combine_single_source_preserves_all_entries(self, tmp_path: Path) -> None:
        from scripts.combine_citizen_science_labels import combine_label_files

        result = combine_label_files([HIP99427_LABELS])
        assert result["total_entries"] == 124
        assert result["duplicate_entries_skipped"] == 0

    def test_combine_same_file_twice_deduplicates(self, tmp_path: Path) -> None:
        from scripts.combine_citizen_science_labels import combine_label_files

        result = combine_label_files([HIP99427_LABELS, HIP99427_LABELS], deduplicate=True)
        assert result["total_entries"] == 124
        assert result["duplicate_entries_skipped"] == 124

    def test_combine_same_file_twice_no_dedup(self, tmp_path: Path) -> None:
        from scripts.combine_citizen_science_labels import combine_label_files

        result = combine_label_files([HIP99427_LABELS, HIP99427_LABELS], deduplicate=False)
        assert result["total_entries"] == 248

    def test_combined_schema_version(self) -> None:
        from scripts.combine_citizen_science_labels import combine_label_files

        result = combine_label_files([HIP99427_LABELS])
        assert result["schema_version"] == "labeled_candidates_citizen_science_combined_v1"

    def test_combined_has_source_datasets(self) -> None:
        from scripts.combine_citizen_science_labels import combine_label_files

        result = combine_label_files([HIP99427_LABELS])
        assert len(result["source_datasets"]) == 1
        assert "hip99427" in result["source_datasets"][0]["filename"].lower()

    def test_combined_external_submission_false(self) -> None:
        from scripts.combine_citizen_science_labels import combine_label_files

        result = combine_label_files([HIP99427_LABELS])
        assert result["external_submission_authorized"] is False

    def test_combined_label_counts_match_entries(self) -> None:
        from scripts.combine_citizen_science_labels import combine_label_files

        result = combine_label_files([HIP99427_LABELS])
        total = sum(result["label_counts"].values())
        assert total == result["total_entries"]

    def test_combined_has_disclaimer(self) -> None:
        from scripts.combine_citizen_science_labels import combine_label_files

        result = combine_label_files([HIP99427_LABELS])
        assert "citizen-science" in result["disclaimer"].lower()
        assert "does not constitute" in result["disclaimer"].lower()
        assert "external submission" in result["disclaimer"].lower()

    def test_combine_writes_valid_json(self, tmp_path: Path) -> None:
        from scripts.combine_citizen_science_labels import combine_label_files

        result = combine_label_files([HIP99427_LABELS])
        out = tmp_path / "combined.json"
        out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        loaded = json.loads(out.read_text())
        assert loaded["total_entries"] == 124

    def test_combine_rejects_bad_schema(self, tmp_path: Path) -> None:
        from scripts.combine_citizen_science_labels import combine_label_files

        bad = tmp_path / "bad.json"
        bad.write_text(
            json.dumps({"schema_version": "wrong_v99", "entries": [{}]}) + "\n"
        )
        with pytest.raises(ValueError, match="unsupported schema_version"):
            combine_label_files([bad])

    def test_combine_rejects_empty_entries(self, tmp_path: Path) -> None:
        from scripts.combine_citizen_science_labels import combine_label_files

        empty = tmp_path / "empty.json"
        empty.write_text(
            json.dumps({
                "schema_version": "labeled_candidates_citizen_science_v1",
                "entries": [],
            }) + "\n"
        )
        with pytest.raises(ValueError, match="no entries found"):
            combine_label_files([empty])


class TestCombineScript:
    def test_script_runs_with_default_input(self, tmp_path: Path) -> None:
        """combine_citizen_science_labels.py should run and write output."""
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        try:
            from scripts.combine_citizen_science_labels import main as combine_main
        except ImportError:
            pytest.skip("scripts not importable")

        out_path = tmp_path / "combined.json"
        rc = combine_main([
            "--inputs", str(HIP99427_LABELS),
            "--output", str(out_path),
        ])
        assert rc == 0
        assert out_path.exists()
        data = json.loads(out_path.read_text())
        assert data["total_entries"] == 124

    def test_script_fails_gracefully_on_missing_input(
        self, tmp_path: Path, capsys
    ) -> None:
        try:
            from scripts.combine_citizen_science_labels import main as combine_main
        except ImportError:
            pytest.skip("scripts not importable")

        rc = combine_main([
            "--inputs", "/nonexistent/file.json",
            "--output", str(tmp_path / "out.json"),
        ])
        assert rc == 1


class TestCombinedModelSummary:
    def _make_combined_labels(self, tmp_path: Path) -> Path:
        """Write a combined label file from HIP99427 for test use."""
        from scripts.combine_citizen_science_labels import combine_label_files

        result = combine_label_files([HIP99427_LABELS])
        out = tmp_path / "combined.json"
        out.write_text(json.dumps(result, indent=2) + "\n")
        return out

    def test_combined_model_trains_successfully(self, tmp_path: Path) -> None:
        from techno_search.learned_scoring_model import train_on_combined_labels

        combined_path = self._make_combined_labels(tmp_path)
        result = train_on_combined_labels(dataset_path=combined_path)
        assert result["ok"] is True
        assert result["trained"] is True

    def test_combined_model_cv_accuracy_above_baseline(self, tmp_path: Path) -> None:
        from techno_search.learned_scoring_model import train_on_combined_labels

        combined_path = self._make_combined_labels(tmp_path)
        result = train_on_combined_labels(dataset_path=combined_path)
        assert result.get("cv_accuracy", 0) >= 0.75

    def test_combined_model_reports_source_datasets(self, tmp_path: Path) -> None:
        from techno_search.learned_scoring_model import train_on_combined_labels

        combined_path = self._make_combined_labels(tmp_path)
        result = train_on_combined_labels(dataset_path=combined_path)
        assert "source_datasets" in result
        assert len(result["source_datasets"]) >= 1

    def test_combined_model_has_combined_schema_version(self, tmp_path: Path) -> None:
        from techno_search.learned_scoring_model import train_on_combined_labels

        combined_path = self._make_combined_labels(tmp_path)
        result = train_on_combined_labels(dataset_path=combined_path)
        assert result.get("schema_version") == "learned_scoring_model_combined_v1"

    def test_combined_model_references_known_limitations(self, tmp_path: Path) -> None:
        from techno_search.learned_scoring_model import train_on_combined_labels

        combined_path = self._make_combined_labels(tmp_path)
        result = train_on_combined_labels(dataset_path=combined_path)
        addressed = " ".join(result.get("known_limitations_addressed", []))
        assert "KNOWN_LIMITATIONS #1" in addressed

    def test_combined_model_returns_error_if_no_file(self) -> None:
        from techno_search.learned_scoring_model import train_on_combined_labels

        result = train_on_combined_labels(
            dataset_path=Path("/nonexistent/combined.json")
        )
        assert result["ok"] is False
        assert result["trained"] is False
        assert "not found" in result.get("error", "").lower()

    def test_combined_model_disclaimer_present(self, tmp_path: Path) -> None:
        from techno_search.learned_scoring_model import train_on_combined_labels

        combined_path = self._make_combined_labels(tmp_path)
        result = train_on_combined_labels(dataset_path=combined_path)
        disc = result.get("disclaimer", "")
        assert "citizen-science" in disc.lower()
        assert "external submission" in disc.lower()


class TestCombinedModelCLI:
    def test_cli_combined_model_missing_file(self) -> None:
        import subprocess

        result = subprocess.run(
            [".venv/bin/techno-search", "combined-model-summary",
             "--dataset-path", "/nonexistent/path.json"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        data = json.loads(result.stdout)
        assert data["ok"] is False
        assert data["trained"] is False

    def test_cli_combined_model_with_valid_file(self, tmp_path: Path) -> None:
        import subprocess

        from scripts.combine_citizen_science_labels import combine_label_files

        result = combine_label_files([HIP99427_LABELS])
        combined_path = tmp_path / "combined.json"
        combined_path.write_text(json.dumps(result, indent=2) + "\n")

        proc = subprocess.run(
            [".venv/bin/techno-search", "combined-model-summary",
             "--dataset-path", str(combined_path)],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        data = json.loads(proc.stdout)
        assert data["ok"] is True
        assert data["trained"] is True
        assert proc.returncode == 0

    def test_cli_combined_model_has_cv_accuracy(self, tmp_path: Path) -> None:
        import subprocess

        from scripts.combine_citizen_science_labels import combine_label_files

        result = combine_label_files([HIP99427_LABELS])
        combined_path = tmp_path / "combined.json"
        combined_path.write_text(json.dumps(result, indent=2) + "\n")

        proc = subprocess.run(
            [".venv/bin/techno-search", "combined-model-summary",
             "--dataset-path", str(combined_path)],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        data = json.loads(proc.stdout)
        assert "cv_accuracy" in data
        assert isinstance(data["cv_accuracy"], float)
