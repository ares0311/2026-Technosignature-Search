"""Semi-supervised anomaly scorer using PCA + IsolationForest.

Adapts the reconstruction-error approach from Ma et al. 2023 (Nature
Astronomy, β-CVAE) using sklearn primitives only — no PyTorch, no GPU.

Workflow:
  1. Train on an unlabeled corpus dominated by RFI (e.g., MeerKAT BLUSE
     hits or GBT survey hits).  IsolationForest learns the normal RFI
     manifold.
  2. Score new hits: anomaly score = IsolationForest decision_function;
     high scores (closer to +1) indicate the hit lies far from the normal
     RFI cluster and deserves scrutiny.

Scientific guardrail: anomaly scores are local triage aids only.  A high
anomaly score means "unusual given the training corpus"; it does not mean
"technosignature".  This module does not constitute a detection claim,
does not authorize external submission, and requires independent-method
citizen-science review before any use in production scoring.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SEMISUPERVISED_SCORER_VERSION = "semisupervised_scorer_v1"
SEMISUPERVISED_SCORER_DISCLAIMER = (
    "Semi-supervised anomaly scores are local triage aids only. "
    "A high anomaly score indicates the hit is unusual relative to the "
    "training corpus; it does not constitute a technosignature detection "
    "or authorize external submission. "
    "Independent-method citizen-science review is required before any "
    "use of this scorer in production pathway routing."
)

# Features used for semi-supervised training and scoring
SEMISUPERVISED_FEATURE_NAMES = [
    "snr",
    "drift_rate_hz_per_sec",
    "frequency_hz",
    "bandwidth_hz",
    "normalized_drift_hz_s_per_ghz",
    "relative_snr",
    "on_off_consistency_score",
    "is_earth_drift_consistent",
    "rfi_band_overlap_score",
    "frequency_persistence_score",
    "on_hit_count",
    "off_hit_count",
]

# IsolationForest contamination parameter — expected fraction of outliers
# in the training corpus.  Conservative: assume 1% of RFI corpus may be
# genuine candidates.
DEFAULT_CONTAMINATION = 0.01
DEFAULT_N_COMPONENTS = 8   # PCA components; captures >95% variance in GBT data
DEFAULT_N_ESTIMATORS = 200  # IsolationForest trees


class SemisupervisedScorer:
    """PCA + IsolationForest anomaly scorer.

    Usage::

        scorer = SemisupervisedScorer()
        scorer.fit(training_hits)             # list[dict]
        score = scorer.score_hit(new_hit)     # float in [-1, +1]
        scorer.save(Path("model.json"))
        scorer2 = SemisupervisedScorer.load(Path("model.json"))
    """

    def __init__(
        self,
        feature_names: list[str] | None = None,
        n_components: int = DEFAULT_N_COMPONENTS,
        n_estimators: int = DEFAULT_N_ESTIMATORS,
        contamination: float = DEFAULT_CONTAMINATION,
        random_state: int = 42,
    ) -> None:
        self.feature_names = feature_names or SEMISUPERVISED_FEATURE_NAMES
        self.n_components = n_components
        self.n_estimators = n_estimators
        self.contamination = contamination
        self.random_state = random_state
        self._pipeline: Any = None
        self._is_fitted: bool = False
        self._train_hit_count: int = 0

    def _extract_row(self, hit: dict[str, Any]) -> list[float]:
        """Extract a numeric row from a hit dict."""
        row: list[float] = []
        for name in self.feature_names:
            val = hit.get(name, 0.0)
            try:
                row.append(float(val))
            except (TypeError, ValueError):
                row.append(0.0)
        return row

    def fit(self, training_hits: list[dict[str, Any]]) -> SemisupervisedScorer:
        """Fit the scorer on an unlabeled corpus of hits.

        Args:
            training_hits: List of hit dicts (expected to be RFI-dominated).

        Returns:
            self (for chaining).

        Raises:
            ImportError: If scikit-learn is not installed.
            ValueError: If fewer than 10 hits are provided.
        """
        try:
            from sklearn.decomposition import PCA
            from sklearn.ensemble import IsolationForest
            from sklearn.pipeline import Pipeline
            from sklearn.preprocessing import QuantileTransformer
        except ImportError as exc:
            raise ImportError(
                "scikit-learn is required for the semi-supervised scorer. "
                "Install it with: .venv/bin/pip install scikit-learn"
            ) from exc

        if len(training_hits) < 10:
            raise ValueError(
                f"Need at least 10 training hits; got {len(training_hits)}"
            )

        X = [self._extract_row(h) for h in training_hits]

        n_comp = min(self.n_components, len(self.feature_names), len(X))

        self._pipeline = Pipeline([
            ("scaler", QuantileTransformer(
                n_quantiles=min(1000, len(X)),
                output_distribution="normal",
                random_state=self.random_state,
            )),
            ("pca", PCA(n_components=n_comp, random_state=self.random_state)),
            ("iforest", IsolationForest(
                n_estimators=self.n_estimators,
                contamination=self.contamination,
                random_state=self.random_state,
            )),
        ])
        self._pipeline.fit(X)
        self._is_fitted = True
        self._train_hit_count = len(training_hits)
        return self

    def score_hit(self, hit: dict[str, Any]) -> float:
        """Return anomaly score for a single hit in [-1, +1].

        Higher (more positive) values indicate the hit is more anomalous
        relative to the training corpus.  Negative values indicate a hit
        that closely resembles the training distribution (typical RFI).

        Raises:
            RuntimeError: If the scorer has not been fitted.
        """
        if not self._is_fitted or self._pipeline is None:
            raise RuntimeError("SemisupervisedScorer must be fitted before scoring.")

        row = self._extract_row(hit)
        # decision_function returns negative for outliers in sklearn's convention;
        # we negate so that higher = more anomalous
        score: float = float(-self._pipeline.decision_function([row])[0])
        return score

    def score_hits(self, hits: list[dict[str, Any]]) -> list[float]:
        """Score a batch of hits. Returns scores in the same order."""
        return [self.score_hit(h) for h in hits]

    def save(self, path: Path) -> None:
        """Persist model metadata to a JSON file (not the model weights).

        Full sklearn model serialisation requires joblib and is handled
        separately.  This method saves provenance metadata only.

        Raises:
            RuntimeError: If the scorer has not been fitted.
        """
        if not self._is_fitted:
            raise RuntimeError("Cannot save: scorer has not been fitted.")
        meta = {
            "schema_version": SEMISUPERVISED_SCORER_VERSION,
            "disclaimer": SEMISUPERVISED_SCORER_DISCLAIMER,
            "feature_names": self.feature_names,
            "n_components": self.n_components,
            "n_estimators": self.n_estimators,
            "contamination": self.contamination,
            "random_state": self.random_state,
            "train_hit_count": self._train_hit_count,
        }
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> SemisupervisedScorer:
        """Load provenance metadata from a JSON file saved by save().

        Note: This restores hyperparameters but NOT the fitted model weights.
        To restore a fitted model, use joblib.load() on the .pkl file
        (if saved separately).
        """
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        scorer = cls(
            feature_names=data.get("feature_names"),
            n_components=data.get("n_components", DEFAULT_N_COMPONENTS),
            n_estimators=data.get("n_estimators", DEFAULT_N_ESTIMATORS),
            contamination=data.get("contamination", DEFAULT_CONTAMINATION),
            random_state=data.get("random_state", 42),
        )
        scorer._train_hit_count = data.get("train_hit_count", 0)
        return scorer

    def summary(self) -> dict[str, Any]:
        """Return a provenance summary dict."""
        return {
            "schema_version": SEMISUPERVISED_SCORER_VERSION,
            "disclaimer": SEMISUPERVISED_SCORER_DISCLAIMER,
            "feature_names": self.feature_names,
            "feature_count": len(self.feature_names),
            "n_components": self.n_components,
            "n_estimators": self.n_estimators,
            "contamination": self.contamination,
            "is_fitted": self._is_fitted,
            "train_hit_count": self._train_hit_count,
        }


def semisupervised_scorer_summary(scorer: SemisupervisedScorer | None = None) -> dict[str, Any]:
    """Return provenance summary for the semi-supervised scorer module."""
    if scorer is not None:
        return scorer.summary()
    return {
        "schema_version": SEMISUPERVISED_SCORER_VERSION,
        "disclaimer": SEMISUPERVISED_SCORER_DISCLAIMER,
        "feature_names": SEMISUPERVISED_FEATURE_NAMES,
        "feature_count": len(SEMISUPERVISED_FEATURE_NAMES),
        "default_n_components": DEFAULT_N_COMPONENTS,
        "default_n_estimators": DEFAULT_N_ESTIMATORS,
        "default_contamination": DEFAULT_CONTAMINATION,
        "is_fitted": False,
        "train_hit_count": 0,
    }
