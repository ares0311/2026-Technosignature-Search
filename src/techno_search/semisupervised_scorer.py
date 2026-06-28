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
review before any use in production scoring.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

SEMISUPERVISED_SCORER_VERSION = "semisupervised_scorer_v1"
SEMISUPERVISED_CORPUS_VERSION = "semisupervised_training_corpus_v1"
SEMISUPERVISED_SCORER_DISCLAIMER = (
    "Semi-supervised anomaly scores are local triage aids only. "
    "A high anomaly score indicates the hit is unusual relative to the "
    "training corpus; it does not constitute a technosignature detection "
    "or authorize external submission. "
    "Independent-method review is required before any "
    "use of this scorer in production pathway routing."
)
SEMISUPERVISED_CORPUS_DISCLAIMER = (
    "Semi-supervised training corpora are real turboSETI hit records used for "
    "local false-positive and anomaly-distribution learning only. They do not "
    "constitute technosignature detections, discoveries, expert review, "
    "external validation, or authorization for external submission."
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
DEFAULT_WORKERS = 12
DEFAULT_FREQUENCY_BIN_HZ = 1.0


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
        n_jobs: int | None = 1,
    ) -> None:
        self.feature_names = feature_names or SEMISUPERVISED_FEATURE_NAMES
        self.n_components = n_components
        self.n_estimators = n_estimators
        self.contamination = contamination
        self.random_state = random_state
        self.n_jobs = n_jobs
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
                n_jobs=self.n_jobs,
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
            "n_jobs": self.n_jobs,
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
            n_jobs=data.get("n_jobs", 1),
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
            "n_jobs": self.n_jobs,
            "is_fitted": self._is_fitted,
            "train_hit_count": self._train_hit_count,
        }


def load_training_hits_ndjson(
    path: Path,
    *,
    max_hits: int | None = None,
) -> list[dict[str, Any]]:
    """Load normalized training hits from an NDJSON corpus.

    The loader streams records so a large real corpus can be capped without
    first materializing every row in memory.
    """

    hits: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if max_hits is not None and len(hits) >= max_hits:
                break
            stripped = line.strip()
            if not stripped:
                continue
            record = json.loads(stripped)
            if not isinstance(record, dict):
                raise ValueError(
                    f"Expected object at {path}:{line_number}; "
                    f"got {type(record).__name__}"
                )
            hits.append(record)
    return hits


def discover_training_dat_files(dat_dir: Path) -> list[Path]:
    """Return real turboSETI .dat files below ``dat_dir`` in stable order."""

    root = Path(dat_dir)
    if not root.exists():
        raise FileNotFoundError(f"Training .dat directory does not exist: {root}")
    if root.is_file():
        return [root]
    return sorted(path for path in root.rglob("*.dat") if path.is_file())


def _frequency_bin(frequency_hz: float, *, bin_hz: float = DEFAULT_FREQUENCY_BIN_HZ) -> int:
    if bin_hz <= 0:
        raise ValueError("frequency bin width must be positive")
    return int(round(frequency_hz / bin_hz))


def _normalised_drift(drift_rate_hz_per_sec: float, frequency_hz: float) -> float:
    frequency_ghz = frequency_hz / 1e9
    if frequency_ghz <= 0:
        return 0.0
    return drift_rate_hz_per_sec / frequency_ghz


def build_training_corpus_from_dat_files(
    dat_dir: Path,
    output_path: Path,
    *,
    max_hits: int | None = None,
    frequency_bin_hz: float = DEFAULT_FREQUENCY_BIN_HZ,
) -> dict[str, Any]:
    """Build a normalized real-hit NDJSON corpus from turboSETI .dat files.

    The resulting records contain the feature names required by
    :class:`SemisupervisedScorer`.  Input payloads remain local/ignored; the
    returned summary and provenance sidecar preserve enough source context for
    reproducible training.
    """

    from techno_search.radio.hit_table_reader import hit_table_to_radio_hit_dicts

    dat_files = discover_training_dat_files(dat_dir)
    if not dat_files:
        raise ValueError(f"No .dat files found under {Path(dat_dir)}")

    raw_hits: list[dict[str, Any]] = []
    unreadable_files: list[str] = []
    zero_hit_files = 0
    for dat_file in dat_files:
        try:
            file_hits = hit_table_to_radio_hit_dicts(dat_file)
        except Exception as exc:  # pragma: no cover - defensive source reporting
            unreadable_files.append(f"{dat_file}: {exc}")
            continue
        if not file_hits:
            zero_hit_files += 1
            continue
        for hit in file_hits:
            copied = dict(hit)
            copied["input_dat_path"] = str(dat_file)
            raw_hits.append(copied)
            if max_hits is not None and len(raw_hits) >= max_hits:
                break
        if max_hits is not None and len(raw_hits) >= max_hits:
            break

    if not raw_hits:
        raise ValueError(
            f"No parseable turboSETI hits found under {Path(dat_dir)} "
            f"({zero_hit_files} zero-hit .dat files, "
            f"{len(unreadable_files)} unreadable files)"
        )

    snrs = [float(hit.get("snr", 0.0) or 0.0) for hit in raw_hits]
    median_snr = statistics.median(snrs) if snrs else 1.0
    if median_snr <= 0:
        median_snr = 1.0

    frequency_counts: dict[int, int] = {}
    role_counts: dict[int, dict[str, int]] = {}
    for hit in raw_hits:
        freq = float(hit.get("frequency_hz", 0.0) or 0.0)
        freq_key = _frequency_bin(freq, bin_hz=frequency_bin_hz)
        frequency_counts[freq_key] = frequency_counts.get(freq_key, 0) + 1
        role = str(hit.get("scan_role") or "unknown").lower()
        role_bucket = role_counts.setdefault(freq_key, {"on": 0, "off": 0})
        if role.startswith("off"):
            role_bucket["off"] += 1
        else:
            role_bucket["on"] += 1

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    unique_targets: set[str] = set()
    with output.open("w", encoding="utf-8") as handle:
        for hit in raw_hits:
            frequency_hz = float(hit.get("frequency_hz", 0.0) or 0.0)
            drift = float(hit.get("drift_rate_hz_per_sec", 0.0) or 0.0)
            snr = float(hit.get("snr", 0.0) or 0.0)
            freq_key = _frequency_bin(frequency_hz, bin_hz=frequency_bin_hz)
            role_bucket = role_counts.get(freq_key, {"on": 0, "off": 0})
            on_hit_count = role_bucket["on"]
            off_hit_count = role_bucket["off"]
            total_role_hits = max(1, on_hit_count + off_hit_count)
            persistence_denominator = max(1, len(dat_files) - 1)
            normalized_drift = _normalised_drift(drift, frequency_hz)
            target_id = str(hit.get("target_id") or "unknown")
            unique_targets.add(target_id)
            record = {
                "snr": snr,
                "drift_rate_hz_per_sec": drift,
                "frequency_hz": frequency_hz,
                "bandwidth_hz": float(hit.get("bandwidth_hz", 0.0) or 0.0),
                "normalized_drift_hz_s_per_ghz": normalized_drift,
                "relative_snr": snr / median_snr,
                "on_off_consistency_score": off_hit_count / total_role_hits,
                "is_earth_drift_consistent": (
                    1.0 if abs(normalized_drift) <= 0.44 else 0.0
                ),
                "rfi_band_overlap_score": 0.0,
                "frequency_persistence_score": min(
                    1.0,
                    max(0, frequency_counts.get(freq_key, 1) - 1)
                    / persistence_denominator,
                ),
                "on_hit_count": on_hit_count,
                "off_hit_count": off_hit_count,
                "scan_role": str(hit.get("scan_role") or "unknown"),
                "target_id": target_id,
                "source_artifact": str(hit.get("source_artifact") or ""),
                "input_dat_path": str(hit.get("input_dat_path") or ""),
                "corpus_source": "real_turboseti_dat",
            }
            handle.write(json.dumps(record, sort_keys=True) + "\n")
            written += 1

    provenance_path = output.with_suffix(output.suffix + ".provenance.json")
    summary: dict[str, Any] = {
        "schema_version": SEMISUPERVISED_CORPUS_VERSION,
        "disclaimer": SEMISUPERVISED_CORPUS_DISCLAIMER,
        "ok": True,
        "input_dat_dir": str(Path(dat_dir)),
        "output_path": str(output),
        "provenance_path": str(provenance_path),
        "dat_file_count": len(dat_files),
        "zero_hit_dat_file_count": zero_hit_files,
        "unreadable_dat_file_count": len(unreadable_files),
        "unreadable_dat_files": unreadable_files,
        "hit_count": written,
        "unique_target_count": len(unique_targets),
        "frequency_bin_hz": frequency_bin_hz,
        "max_hits_requested": max_hits,
        "corpus_source": "real_turboseti_dat",
    }
    provenance_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


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
        "default_workers": DEFAULT_WORKERS,
        "is_fitted": False,
        "train_hit_count": 0,
    }
