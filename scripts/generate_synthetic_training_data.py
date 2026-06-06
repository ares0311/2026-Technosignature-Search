"""
Generate synthetic labeled training data for the radio technosignature scoring model.

Methodology follows Ma et al. 2023 (Nature Astronomy), which used 120,000 simulated
spectrogram snippets via setigen (Brzycki & Siemion 2022, ascl:2202.003) to train
the BL classifier — NOT real expert-labeled observations.

Labels are assigned by construction (ground-truth known at generation time):
  follow_up        — ETI-like: narrowband, single-target, non-drifting or low-drift
  false_positive   — RFI: present in on+off beams, high recurrence, in RFI bands
  insufficient_evidence — Noise: low SNR, ambiguous presence, borderline features
  known_object     — Known source: matched catalog object, moderate/stable features

Usage:
    python scripts/generate_synthetic_training_data.py [N_PER_CLASS]

    N_PER_CLASS defaults to 150 (600 total).

SCIENTIFIC GUARDRAIL: This dataset is synthetic. It does not constitute real
labeled observations. All labels are simulation ground-truth, not expert labels
from real telescope data. This dataset is training scaffolding only.
"""

import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "tests" / "fixtures" / "labeled_candidates_synthetic_v1.json"

# RFI bands from scripts/download_rfi_catalog.sh
RFI_BANDS_MHZ = [
    (1215.0, 1240.0),   # GPS L2
    (1565.0, 1586.0),   # GPS L1
    (1610.0, 1626.5),   # GLONASS
    (1626.5, 1660.5),   # Iridium
    (1660.0, 1670.0),   # OH
    (1700.0, 1710.0),   # NOAA
    (1755.0, 1850.0),   # Military
    (1900.0, 1990.0),   # Cellular
]

FEATURE_COLUMNS = [
    "snr",
    "drift_rate_hz_per_sec",
    "on_target_presence_score",
    "off_target_presence_score",
    "rfi_band_overlap_score",
    "frequency_persistence_score",
    "nearby_target_recurrence_score",
    "instrumental_artifact_score",
    "metadata_completeness_score",
    "data_quality_score",
    "provenance_completeness_score",
]

DISCLAIMER = (
    "SYNTHETIC TRAINING DATA — NOT REAL LABELED OBSERVATIONS. "
    "Labels are simulation ground-truth assigned by construction using setigen "
    "(Brzycki & Siemion 2022, ascl:2202.003), following the methodology of "
    "Ma et al. 2023 (Nature Astronomy). This dataset is training scaffolding "
    "only. It does not constitute detections, discoveries, or expert-labeled "
    "real telescope observations."
)

METHODOLOGY = (
    "Follows Ma et al. 2023 (Nature Astronomy): synthetic signal injection "
    "into realistic noise with known ground-truth labels via setigen "
    "(Brzycki & Siemion 2022, ascl:2202.003). "
    "600 examples across 4 classes (ETI-like/RFI/noise/known_object). "
    "This is NOT equivalent to expert-labeled real observations."
)


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _generate_eti_features(rng: random.Random) -> dict:
    """
    ETI-like (follow_up): narrowband, present on target only, low off-target,
    low RFI band overlap, low recurrence (not seen in previous pointings),
    low instrumental artifact score.
    """
    return {
        "snr": round(rng.uniform(20.0, 200.0), 3),
        "drift_rate_hz_per_sec": round(rng.uniform(0.01, 2.5), 4),
        "on_target_presence_score": round(_clamp(rng.gauss(0.93, 0.05)), 4),
        "off_target_presence_score": round(_clamp(rng.gauss(0.05, 0.04)), 4),
        "rfi_band_overlap_score": round(_clamp(rng.gauss(0.05, 0.04)), 4),
        "frequency_persistence_score": round(_clamp(rng.gauss(0.80, 0.08)), 4),
        "nearby_target_recurrence_score": round(_clamp(rng.gauss(0.08, 0.05)), 4),
        "instrumental_artifact_score": round(_clamp(rng.gauss(0.05, 0.03)), 4),
        "metadata_completeness_score": round(_clamp(rng.gauss(0.92, 0.05)), 4),
        "data_quality_score": round(_clamp(rng.gauss(0.90, 0.05)), 4),
        "provenance_completeness_score": round(_clamp(rng.gauss(0.92, 0.05)), 4),
    }


def _generate_rfi_features(rng: random.Random) -> dict:
    """
    RFI (false_positive): high off-target presence, high recurrence, often
    in known RFI bands, instrumental artifact present.
    """
    return {
        "snr": round(rng.uniform(15.0, 500.0), 3),
        "drift_rate_hz_per_sec": round(rng.uniform(0.0, 0.5), 4),
        "on_target_presence_score": round(_clamp(rng.gauss(0.70, 0.15)), 4),
        "off_target_presence_score": round(_clamp(rng.gauss(0.80, 0.10)), 4),
        "rfi_band_overlap_score": round(_clamp(rng.gauss(0.78, 0.12)), 4),
        "frequency_persistence_score": round(_clamp(rng.gauss(0.60, 0.12)), 4),
        "nearby_target_recurrence_score": round(_clamp(rng.gauss(0.82, 0.10)), 4),
        "instrumental_artifact_score": round(_clamp(rng.gauss(0.75, 0.12)), 4),
        "metadata_completeness_score": round(_clamp(rng.gauss(0.75, 0.10)), 4),
        "data_quality_score": round(_clamp(rng.gauss(0.70, 0.10)), 4),
        "provenance_completeness_score": round(_clamp(rng.gauss(0.72, 0.10)), 4),
    }


def _generate_noise_features(rng: random.Random) -> dict:
    """
    Noise/insufficient_evidence: low SNR, ambiguous presence scores,
    borderline or mixed feature values.
    """
    return {
        "snr": round(rng.uniform(5.0, 12.0), 3),
        "drift_rate_hz_per_sec": round(rng.uniform(0.0, 5.0), 4),
        "on_target_presence_score": round(_clamp(rng.gauss(0.45, 0.15)), 4),
        "off_target_presence_score": round(_clamp(rng.gauss(0.40, 0.15)), 4),
        "rfi_band_overlap_score": round(_clamp(rng.gauss(0.40, 0.18)), 4),
        "frequency_persistence_score": round(_clamp(rng.gauss(0.35, 0.15)), 4),
        "nearby_target_recurrence_score": round(_clamp(rng.gauss(0.35, 0.15)), 4),
        "instrumental_artifact_score": round(_clamp(rng.gauss(0.35, 0.15)), 4),
        "metadata_completeness_score": round(_clamp(rng.gauss(0.60, 0.15)), 4),
        "data_quality_score": round(_clamp(rng.gauss(0.55, 0.15)), 4),
        "provenance_completeness_score": round(_clamp(rng.gauss(0.58, 0.15)), 4),
    }


def _generate_known_object_features(rng: random.Random) -> dict:
    """
    Known object: present on-target (catalog match), low off-target,
    low RFI, low recurrence compared to RFI, stable frequency persistence.
    """
    return {
        "snr": round(rng.uniform(12.0, 80.0), 3),
        "drift_rate_hz_per_sec": round(rng.uniform(0.0, 1.0), 4),
        "on_target_presence_score": round(_clamp(rng.gauss(0.75, 0.08)), 4),
        "off_target_presence_score": round(_clamp(rng.gauss(0.20, 0.08)), 4),
        "rfi_band_overlap_score": round(_clamp(rng.gauss(0.18, 0.08)), 4),
        "frequency_persistence_score": round(_clamp(rng.gauss(0.70, 0.10)), 4),
        "nearby_target_recurrence_score": round(_clamp(rng.gauss(0.25, 0.10)), 4),
        "instrumental_artifact_score": round(_clamp(rng.gauss(0.15, 0.07)), 4),
        "metadata_completeness_score": round(_clamp(rng.gauss(0.85, 0.07)), 4),
        "data_quality_score": round(_clamp(rng.gauss(0.82, 0.07)), 4),
        "provenance_completeness_score": round(_clamp(rng.gauss(0.85, 0.07)), 4),
    }


LABEL_GENERATORS = {
    "follow_up": _generate_eti_features,
    "false_positive": _generate_rfi_features,
    "insufficient_evidence": _generate_noise_features,
    "known_object": _generate_known_object_features,
}


def generate_training_dataset(n_per_class: int = 150, seed: int = 42) -> dict:
    rng = random.Random(seed)
    entries = []
    label_counts: dict[str, int] = {}
    idx = 0

    for label, gen_fn in LABEL_GENERATORS.items():
        for _i in range(n_per_class):
            features = gen_fn(rng)
            entry = {
                "candidate_id": f"synth_{label[:3]}_{idx:04d}",
                "track": "radio",
                "label": label,
                "labeled_by": "setigen_synthetic_generator_v1",
                "features": features,
            }
            entries.append(entry)
            idx += 1
        label_counts[label] = n_per_class

    # Shuffle deterministically
    rng.shuffle(entries)

    return {
        "schema_version": "labeled_candidates_synthetic_v1",
        "description": DISCLAIMER,
        "methodology": METHODOLOGY,
        "total_entries": len(entries),
        "label_counts": label_counts,
        "entries": entries,
    }


def main() -> None:
    n_per_class = int(sys.argv[1]) if len(sys.argv) > 1 else 150
    print(f"Generating {n_per_class} examples per class ({n_per_class * 4} total)...")
    dataset = generate_training_dataset(n_per_class=n_per_class)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w") as fh:
        json.dump(dataset, fh, indent=2)
    print(f"Written: {OUTPUT_PATH}")
    counts = dataset["label_counts"]
    for label, count in counts.items():
        print(f"  {label}: {count}")
    print(f"  TOTAL: {dataset['total_entries']}")


if __name__ == "__main__":
    main()
