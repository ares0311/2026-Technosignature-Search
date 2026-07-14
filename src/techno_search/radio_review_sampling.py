"""Build an unlabeled, diversity-balanced human-review queue from real radio hits."""

from __future__ import annotations

import csv
import hashlib
import io
import math
from collections import Counter, defaultdict, deque
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from techno_search.radio.hit_table_reader import hit_table_to_radio_hit_dicts
from techno_search.radio_real_corpus_summary import discover_dat_files
from techno_search.semisupervised_scorer import load_fitted_scorer_joblib

RADIO_REVIEW_SAMPLE_SCHEMA_VERSION = "radio_human_review_sample_v1"
RADIO_REVIEW_SAMPLE_DISCLAIMER = (
    "This queue contains unlabeled real radio hits selected for human calibration "
    "review. Scores and sampling strata are triage aids only. Empty review fields "
    "must be completed by a human; no row is a detection, discovery, expert review, "
    "external validation, or authorization for external submission."
)
DEFAULT_SAMPLE_SIZE = 1_000
DEFAULT_SAMPLING_SEED = "phase1-radio-review-v1"
DEFAULT_MODEL_PATH = Path("data/meerkat_hits/semisupervised_scorer.joblib")
REVIEW_COLUMNS = (
    "hit_id",
    "source_file",
    "target",
    "frequency_hz",
    "drift_rate_hz_s",
    "snr",
    "score",
    "score_decile",
    "frequency_bin_lower_ghz",
    "review_label",
    "reviewer_id",
    "review_timestamp_utc",
    "review_notes",
    "paper_or_dataset_source",
)


def build_radio_review_sample(
    dat_paths: list[Path],
    *,
    output_csv: Path,
    semisupervised_model_path: Path = DEFAULT_MODEL_PATH,
    sample_size: int = DEFAULT_SAMPLE_SIZE,
    sampling_seed: str = DEFAULT_SAMPLING_SEED,
    dataset_source: str = "local_completed_gbt_extended_corpus",
    overwrite: bool = False,
) -> dict[str, Any]:
    """Score real `.dat` hits and write an unlabeled decile-balanced review queue."""
    if sample_size <= 0:
        raise ValueError("sample_size must be greater than zero")
    if not sampling_seed.strip():
        raise ValueError("sampling_seed must not be empty")
    if not dataset_source.strip():
        raise ValueError("dataset_source must not be empty")
    output_path = Path(output_csv)
    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"review queue already exists: {output_path}; refusing to overwrite "
            "possible human labels without explicit overwrite=True"
        )

    dat_files = discover_dat_files(dat_paths)
    if not dat_files:
        raise ValueError("no .dat files were found")
    model_path = Path(semisupervised_model_path)
    if not model_path.is_file():
        raise FileNotFoundError(f"fitted semi-supervised model not found: {model_path}")

    rows, scorer_features, zero_hit_file_count = _load_review_rows(
        dat_files,
        dataset_source=dataset_source,
    )
    if not rows:
        raise ValueError("the selected .dat corpus contains no hit rows")
    scorer = load_fitted_scorer_joblib(model_path)
    scores = scorer.score_hits(scorer_features)
    if len(scores) != len(rows):
        raise RuntimeError("semi-supervised scorer returned an unexpected score count")
    for row, score in zip(rows, scores, strict=True):
        row["score"] = float(score)

    _assign_score_deciles(rows)
    selected = select_diverse_review_rows(
        rows,
        sample_size=min(sample_size, len(rows)),
        sampling_seed=sampling_seed,
    )
    _write_review_csv(output_path, selected)

    decile_counts = Counter(int(row["score_decile"]) for row in selected)
    frequency_bin_counts = Counter(
        int(row["frequency_bin_lower_ghz"]) for row in selected
    )
    target_counts = Counter(str(row["target"]) for row in selected)
    return {
        "schema_version": RADIO_REVIEW_SAMPLE_SCHEMA_VERSION,
        "disclaimer": RADIO_REVIEW_SAMPLE_DISCLAIMER,
        "ok": True,
        "output_csv": str(output_path),
        "source_dataset_role": "completed_live_search_evidence",
        "review_queue_role": "calibration",
        "blind_search_reuse_prohibited": True,
        "dataset_source": dataset_source,
        "semisupervised_model_path": str(model_path),
        "sampling_seed": sampling_seed,
        "requested_sample_size": sample_size,
        "available_hit_count": len(rows),
        "sampled_hit_count": len(selected),
        "dat_file_count": len(dat_files),
        "zero_hit_dat_file_count": zero_hit_file_count,
        "hit_bearing_dat_file_count": len(dat_files) - zero_hit_file_count,
        "sampled_target_count": len(target_counts),
        "sampled_frequency_bin_count": len(frequency_bin_counts),
        "score_decile_counts": {
            str(decile): decile_counts.get(decile, 0) for decile in range(1, 11)
        },
        "frequency_bin_counts": {
            str(key): frequency_bin_counts[key] for key in sorted(frequency_bin_counts)
        },
        "maximum_rows_from_one_target": max(target_counts.values(), default=0),
        "prepopulated_human_label_count": sum(
            1 for row in selected if str(row["review_label"]).strip()
        ),
        "review_columns": list(REVIEW_COLUMNS),
    }


def select_diverse_review_rows(
    rows: list[dict[str, Any]],
    *,
    sample_size: int,
    sampling_seed: str,
) -> list[dict[str, Any]]:
    """Select equal score-decile quotas with target/frequency-bin round robin."""
    if sample_size <= 0:
        return []
    by_decile: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        decile = int(row["score_decile"])
        if not 1 <= decile <= 10:
            raise ValueError(f"score_decile must be in 1..10; got {decile}")
        by_decile[decile].append(row)

    base, remainder = divmod(min(sample_size, len(rows)), 10)
    quotas = {
        decile: base + (1 if decile > 10 - remainder else 0)
        for decile in range(1, 11)
    }
    selected: list[dict[str, Any]] = []
    unfilled = 0
    leftovers: list[dict[str, Any]] = []
    for decile in range(1, 11):
        ordered = _round_robin_diversity_order(
            by_decile.get(decile, []), sampling_seed=sampling_seed
        )
        quota = quotas[decile]
        selected.extend(ordered[:quota])
        leftovers.extend(ordered[quota:])
        unfilled += max(0, quota - len(ordered))
    if unfilled:
        leftovers.sort(key=lambda row: _stable_key(row, sampling_seed))
        selected.extend(leftovers[:unfilled])
    return sorted(
        selected,
        key=lambda row: (
            -int(row["score_decile"]),
            str(row["target"]),
            str(row["hit_id"]),
        ),
    )


def _load_review_rows(
    dat_files: list[Path],
    *,
    dataset_source: str,
) -> tuple[list[dict[str, Any]], list[dict[str, float]], int]:
    rows: list[dict[str, Any]] = []
    scorer_features: list[dict[str, float]] = []
    zero_hit_file_count = 0
    repo_root = Path(__file__).resolve().parents[2]
    for dat_file in dat_files:
        hits = hit_table_to_radio_hit_dicts(dat_file)
        if not hits:
            zero_hit_file_count += 1
            continue
        source_file = _portable_path(dat_file, repo_root=repo_root)
        for row_number, hit in enumerate(hits, start=1):
            target = str(
                hit.get("target_id")
                or hit.get("source_name")
                or dat_file.parent.name
            )
            frequency_hz = _as_float(hit, "frequency_hz")
            drift_rate = _as_float(hit, "drift_rate_hz_per_sec")
            snr = _as_float(hit, "snr")
            hit_id = _hit_id(
                source_file=source_file,
                row_number=row_number,
                frequency_hz=frequency_hz,
                drift_rate_hz_s=drift_rate,
            )
            rows.append(
                {
                    "hit_id": hit_id,
                    "source_file": source_file,
                    "target": target,
                    "frequency_hz": frequency_hz,
                    "drift_rate_hz_s": drift_rate,
                    "snr": snr,
                    "score": 0.0,
                    "score_decile": 0,
                    "frequency_bin_lower_ghz": math.floor(frequency_hz / 1e9),
                    "review_label": "",
                    "reviewer_id": "",
                    "review_timestamp_utc": "",
                    "review_notes": "",
                    "paper_or_dataset_source": dataset_source,
                }
            )
            scorer_features.append(_scorer_features(hit, hits))
    return rows, scorer_features, zero_hit_file_count


def _scorer_features(
    hit: dict[str, Any],
    all_file_hits: list[dict[str, Any]],
) -> dict[str, float]:
    frequency_hz = _as_float(hit, "frequency_hz")
    drift_rate = _as_float(hit, "drift_rate_hz_per_sec")
    snr = _as_float(hit, "snr")
    same_frequency_hits = [
        other
        for other in all_file_hits
        if abs(_as_float(other, "frequency_hz") - frequency_hz) <= 5.0
    ]
    scan_roles = [str(other.get("scan_role", "")).lower() for other in same_frequency_hits]
    on_hit_count = sum(1 for role in scan_roles if not role.startswith("off"))
    off_hit_count = sum(1 for role in scan_roles if role.startswith("off"))
    total_role_hits = max(1, on_hit_count + off_hit_count)
    frequency_ghz = frequency_hz / 1e9
    normalized_drift = drift_rate / frequency_ghz if frequency_ghz > 0 else 0.0
    return {
        "snr": snr,
        "drift_rate_hz_per_sec": drift_rate,
        "frequency_hz": frequency_hz,
        "bandwidth_hz": _as_float(hit, "bandwidth_hz"),
        "normalized_drift_hz_s_per_ghz": normalized_drift,
        "relative_snr": snr / _median_positive_snr(all_file_hits),
        "on_off_consistency_score": off_hit_count / total_role_hits,
        "is_earth_drift_consistent": 1.0 if abs(normalized_drift) <= 0.44 else 0.0,
        "rfi_band_overlap_score": 0.0,
        "frequency_persistence_score": min(
            1.0,
            max(0, len(same_frequency_hits) - 1) / max(1, len(all_file_hits) - 1),
        ),
        "on_hit_count": float(on_hit_count),
        "off_hit_count": float(off_hit_count),
    }


def _assign_score_deciles(rows: list[dict[str, Any]]) -> None:
    ranked = sorted(rows, key=lambda row: (float(row["score"]), str(row["hit_id"])))
    count = len(ranked)
    for rank, row in enumerate(ranked):
        row["score_decile"] = min(10, (rank * 10) // count + 1)


def _round_robin_diversity_order(
    rows: Iterable[dict[str, Any]],
    *,
    sampling_seed: str,
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (str(row["target"]), int(row["frequency_bin_lower_ghz"]))
        groups[key].append(row)
    ordered_keys = sorted(
        groups,
        key=lambda key: hashlib.sha256(
            f"{sampling_seed}|{key[0]}|{key[1]}".encode()
        ).hexdigest(),
    )
    queues = {
        key: deque(sorted(groups[key], key=lambda row: _stable_key(row, sampling_seed)))
        for key in ordered_keys
    }
    ordered: list[dict[str, Any]] = []
    while queues:
        for key in list(ordered_keys):
            queue = queues.get(key)
            if queue is None:
                continue
            ordered.append(queue.popleft())
            if not queue:
                del queues[key]
        ordered_keys = [key for key in ordered_keys if key in queues]
    return ordered


def _write_review_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=REVIEW_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(buffer.getvalue(), encoding="utf-8")
    temporary.replace(path)


def _portable_path(path: Path, *, repo_root: Path) -> str:
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(repo_root.resolve()))
    except ValueError:
        return str(resolved)


def _hit_id(
    *,
    source_file: str,
    row_number: int,
    frequency_hz: float,
    drift_rate_hz_s: float,
) -> str:
    payload = (
        f"{source_file}|{row_number}|{frequency_hz:.9f}|{drift_rate_hz_s:.9f}"
    )
    return f"radio-hit-{hashlib.sha256(payload.encode()).hexdigest()[:20]}"


def _stable_key(row: dict[str, Any], sampling_seed: str) -> str:
    return hashlib.sha256(
        f"{sampling_seed}|{row['hit_id']}".encode()
    ).hexdigest()


def _median_positive_snr(rows: list[dict[str, Any]]) -> float:
    values = sorted(_as_float(row, "snr") for row in rows if _as_float(row, "snr") > 0)
    if not values:
        return 1.0
    midpoint = len(values) // 2
    if len(values) % 2:
        return values[midpoint]
    return (values[midpoint - 1] + values[midpoint]) / 2.0


def _as_float(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default) or default)
    except (TypeError, ValueError):
        return default
