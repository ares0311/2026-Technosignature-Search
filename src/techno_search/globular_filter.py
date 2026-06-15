"""GLOBULAR-inspired pre-filter for radio hit tables.

Implements a density-based clustering pre-filter adapted from
Jacobson-Bell et al. 2024 (arxiv:2411.16556).  Uses HDBSCAN on 13
morphological features to identify dense clusters of hits that are
characteristic of terrestrial RFI, achieving ~93% false-positive
reduction with zero hand-crafted labels.

This is a citizen-science adaptation:
- Uses sklearn's HDBSCAN (no GPU or JAX required).
- Cluster labels are heuristic only — they are not ground truth.
- A hit labelled rfi_cluster is *probably* RFI; it is not confirmed.

Scientific guardrail: GLOBULAR filter outputs are local triage aids only.
No cluster label constitutes a confirmed detection, a false-positive
ruling, or authorization for external submission.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

GLOBULAR_FILTER_VERSION = "globular_filter_v1"
GLOBULAR_FILTER_DISCLAIMER = (
    "GLOBULAR filter outputs are local triage aids only. "
    "Cluster labels are density-based heuristics applied to morphological "
    "features; they are not confirmed classifications. "
    "A hit labelled rfi_cluster is probably RFI but has not been "
    "independently verified. No filter output constitutes a detection claim "
    "or authorizes external submission."
)

# 13 morphological features adapted from Jacobson-Bell et al. 2024 Table 1
GLOBULAR_FEATURE_NAMES = [
    "frequency_hz",
    "drift_rate_hz_per_sec",
    "snr",
    "bandwidth_hz",
    "normalized_drift_hz_s_per_ghz",
    "relative_snr",
    "on_off_consistency_score",
    "is_earth_drift_consistent",
    "rfi_band_overlap_score",
    "frequency_persistence_score",
    "hit_count",
    "on_hit_count",
    "off_hit_count",
]

# Minimum cluster size for HDBSCAN; tuned for GBT cadence sizes (~200 hits)
DEFAULT_MIN_CLUSTER_SIZE = 5
# Minimum number of samples in a neighbourhood for core point status
DEFAULT_MIN_SAMPLES = 3


@dataclass
class GlobularResult:
    """Result of the GLOBULAR pre-filter for a single hit."""

    hit_index: int
    cluster_label: int           # -1 = noise (candidate), ≥0 = RFI cluster
    is_rfi_cluster: bool
    cluster_size: int
    features_used: list[str]
    disclaimer: str = field(default=GLOBULAR_FILTER_DISCLAIMER, compare=False)

    def as_dict(self) -> dict[str, Any]:
        return {
            "hit_index": self.hit_index,
            "cluster_label": self.cluster_label,
            "is_rfi_cluster": self.is_rfi_cluster,
            "cluster_size": self.cluster_size,
            "features_used": self.features_used,
            "disclaimer": self.disclaimer,
        }


def _build_feature_matrix(
    hits: list[dict[str, Any]],
    feature_names: list[str],
) -> list[list[float]]:
    """Extract a numeric feature matrix from a hit list.

    Missing or non-numeric values are filled with 0.0.  Each row is
    quantile-normalised independently to [0, 1] to suppress scale differences
    across bands.

    Returns list of feature rows (same length as hits).
    """
    # Raw extraction
    matrix: list[list[float]] = []
    for h in hits:
        row: list[float] = []
        for name in feature_names:
            val = h.get(name, 0.0)
            try:
                row.append(float(val))
            except (TypeError, ValueError):
                row.append(0.0)
        matrix.append(row)

    if not matrix:
        return matrix

    # Per-column min-max normalisation (robust to different frequency scales)
    n_cols = len(feature_names)
    for col_idx in range(n_cols):
        col_vals = [matrix[r][col_idx] for r in range(len(matrix))]
        col_min = min(col_vals)
        col_max = max(col_vals)
        col_range = col_max - col_min
        if col_range == 0.0:
            # All values identical — set to 0
            for r in range(len(matrix)):
                matrix[r][col_idx] = 0.0
        else:
            for r in range(len(matrix)):
                matrix[r][col_idx] = (matrix[r][col_idx] - col_min) / col_range

    return matrix


def apply_globular_filter(
    hits: list[dict[str, Any]],
    *,
    feature_names: list[str] | None = None,
    min_cluster_size: int = DEFAULT_MIN_CLUSTER_SIZE,
    min_samples: int = DEFAULT_MIN_SAMPLES,
) -> list[GlobularResult]:
    """Apply the GLOBULAR pre-filter to a hit table.

    Uses HDBSCAN from sklearn.  Hits assigned to a cluster (label ≥ 0) are
    flagged as probable RFI.  Hits in the noise set (label == -1) survive as
    candidates.

    Args:
        hits: List of dicts, each a turboSETI-style hit with numeric fields.
        feature_names: Override the default 13-feature set.
        min_cluster_size: Minimum size of an HDBSCAN cluster.
        min_samples: Minimum samples for a core point.

    Returns:
        List of GlobularResult, one per hit, in the same order.

    Raises:
        ImportError: If scikit-learn is not installed.
    """
    try:
        from sklearn.cluster import HDBSCAN
    except ImportError as exc:
        raise ImportError(
            "scikit-learn is required for the GLOBULAR filter. "
            "Install it with: .venv/bin/pip install scikit-learn"
        ) from exc

    if feature_names is None:
        feature_names = GLOBULAR_FEATURE_NAMES

    if not hits:
        return []

    matrix = _build_feature_matrix(hits, feature_names)

    # HDBSCAN requires at least min_cluster_size points
    if len(matrix) < min_cluster_size:
        # Too few hits to cluster — treat all as noise (candidates)
        return [
            GlobularResult(
                hit_index=i,
                cluster_label=-1,
                is_rfi_cluster=False,
                cluster_size=0,
                features_used=feature_names,
            )
            for i in range(len(hits))
        ]

    clusterer = HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
    )
    labels: list[int] = list(clusterer.fit_predict(matrix))

    # Compute cluster sizes
    cluster_sizes: dict[int, int] = {}
    for lbl in labels:
        if lbl >= 0:
            cluster_sizes[lbl] = cluster_sizes.get(lbl, 0) + 1

    results: list[GlobularResult] = []
    for i, lbl in enumerate(labels):
        size = cluster_sizes.get(lbl, 0) if lbl >= 0 else 0
        results.append(
            GlobularResult(
                hit_index=i,
                cluster_label=int(lbl),
                is_rfi_cluster=bool(lbl >= 0),
                cluster_size=size,
                features_used=feature_names,
            )
        )
    return results


def globular_filter_summary(results: list[GlobularResult]) -> dict[str, Any]:
    """Summarise GLOBULAR filter results for a hit table."""
    total = len(results)
    rfi_cluster_count = sum(1 for r in results if r.is_rfi_cluster)
    noise_count = total - rfi_cluster_count
    reduction_fraction = rfi_cluster_count / total if total > 0 else 0.0
    cluster_ids = sorted({r.cluster_label for r in results if r.cluster_label >= 0})

    return {
        "schema_version": GLOBULAR_FILTER_VERSION,
        "disclaimer": GLOBULAR_FILTER_DISCLAIMER,
        "total_hits": total,
        "rfi_cluster_hits": rfi_cluster_count,
        "noise_hits": noise_count,
        "rfi_reduction_fraction": reduction_fraction,
        "cluster_count": len(cluster_ids),
        "features_used": results[0].features_used if results else GLOBULAR_FEATURE_NAMES,
    }
