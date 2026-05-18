"""ML model evaluation harness — synthetic development diagnostics only."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

MODEL_EVALUATION_SCHEMA_VERSION = "model_evaluation_v1"

MODEL_EVALUATION_DISCLAIMER = (
    "Model evaluation results are synthetic development diagnostics only. "
    "They do not constitute detections, discoveries, or external validation. "
    "No evaluated model has been deployed or used on real observation data."
)


def _default_evaluation_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "model_evaluation.json"
    )


@dataclass
class ModelEvaluationResult:
    eval_id: str
    model_id: str
    track: str
    accuracy: float
    precision: float
    recall: float
    f1: float
    baseline_accuracy: float
    beats_baseline: bool
    eval_utc: str
    notes: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "eval_id": self.eval_id,
            "model_id": self.model_id,
            "track": self.track,
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "baseline_accuracy": self.baseline_accuracy,
            "beats_baseline": self.beats_baseline,
            "eval_utc": self.eval_utc,
            "notes": self.notes,
        }


def load_model_evaluation_results(
    fixture_path: Path | None = None,
) -> list[ModelEvaluationResult]:
    import json

    path = fixture_path or _default_evaluation_path()
    with path.open(encoding="utf-8") as fh:
        raw = json.load(fh)

    results = []
    for item in raw.get("evaluations", []):
        results.append(
            ModelEvaluationResult(
                eval_id=item["eval_id"],
                model_id=item["model_id"],
                track=item["track"],
                accuracy=float(item["accuracy"]),
                precision=float(item["precision"]),
                recall=float(item["recall"]),
                f1=float(item["f1"]),
                baseline_accuracy=float(item["baseline_accuracy"]),
                beats_baseline=bool(item["beats_baseline"]),
                eval_utc=item["eval_utc"],
                notes=item["notes"],
            )
        )
    return results


def model_evaluation_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    results = load_model_evaluation_results(fixture_path)

    by_track: dict[str, int] = {}
    above_baseline = 0
    below_baseline = 0
    best_accuracy = 0.0
    best_model_id = ""
    worst_accuracy = 1.0
    worst_model_id = ""

    for r in results:
        by_track[r.track] = by_track.get(r.track, 0) + 1
        if r.beats_baseline:
            above_baseline += 1
        else:
            below_baseline += 1
        if r.accuracy > best_accuracy:
            best_accuracy = r.accuracy
            best_model_id = r.model_id
        if r.accuracy < worst_accuracy:
            worst_accuracy = r.accuracy
            worst_model_id = r.model_id

    return {
        "disclaimer": MODEL_EVALUATION_DISCLAIMER,
        "schema_version": MODEL_EVALUATION_SCHEMA_VERSION,
        "evaluation_count": len(results),
        "above_baseline_count": above_baseline,
        "below_baseline_count": below_baseline,
        "by_track": by_track,
        "best_model_id": best_model_id,
        "best_accuracy": round(best_accuracy, 6),
        "worst_model_id": worst_model_id,
        "worst_accuracy": round(worst_accuracy, 6),
    }
