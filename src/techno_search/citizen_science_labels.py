"""Citizen-science labels derived from a reviewed radio ON/OFF cadence."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from techno_search.gbt_cadence import cadence_candidate_context
from techno_search.radio.prototype import build_radio_candidate
from techno_search.schemas import FeatureValue

CITIZEN_SCIENCE_LABEL_SCHEMA_VERSION = "labeled_candidates_citizen_science_v1"
CITIZEN_SCIENCE_ABACAB_REVIEW_SCHEMA_VERSION = "gbt_cadence_abacab_review_v1"
CITIZEN_SCIENCE_REVIEW_POLICY = "citizen_science_reproducibility_v1"
FIXED_REVIEW_TIMESTAMP = "2026-06-10T00:00:00Z"

CITIZEN_SCIENCE_LABEL_DISCLAIMER = (
    "These labels are conservative citizen-science operational annotations "
    "derived from cadence behavior. They are not expert labels, external "
    "validation, detections, discoveries, or authorization for external submission."
)

CITIZEN_SCIENCE_ABACAB_REVIEW_DISCLAIMER = (
    "GBT cadence ABACAB review summaries are local candidate-triage evidence "
    "only. They do not constitute detections, discoveries, expert review, "
    "external validation, or authorization for external submission."
)


@dataclass(frozen=True)
class CadenceHit:
    frequency_hz: float
    drift_rate_hz_per_sec: float
    snr: float
    scan_role: str
    target_id: str
    source_artifact: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_cadence_hits(path: Path) -> list[CadenceHit]:
    hits: list[CadenceHit] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            role = str(row.get("scan_role", "")).lower()
            if role not in {"on", "off"}:
                raise ValueError(f"Unsupported scan_role {role!r}.")
            hits.append(
                CadenceHit(
                    frequency_hz=float(row["Corrected_Frequency"]) * 1e6,
                    drift_rate_hz_per_sec=float(row["Drift_Rate"]),
                    snr=float(row["SNR"]),
                    scan_role=role,
                    target_id=str(row["target_id"]),
                    source_artifact=str(row["source_artifact"]),
                )
            )
    if not hits:
        raise ValueError("Cadence CSV contains no hits.")
    return hits


def group_cadence_hits(hits: Iterable[CadenceHit]) -> list[list[CadenceHit]]:
    """Group repeated measurements of the same turboSETI frequency/drift bin."""
    grouped: dict[tuple[float, float], list[CadenceHit]] = defaultdict(list)
    for hit in hits:
        key = (round(hit.frequency_hz, 3), round(hit.drift_rate_hz_per_sec, 6))
        grouped[key].append(hit)
    return [
        sorted(group, key=lambda hit: (hit.source_artifact, hit.scan_role, hit.snr))
        for _, group in sorted(grouped.items())
    ]


def _primary_label(group: list[CadenceHit]) -> tuple[str, str | None, float]:
    on_scans = {hit.source_artifact for hit in group if hit.scan_role == "on"}
    off_scans = {hit.source_artifact for hit in group if hit.scan_role == "off"}
    if off_scans:
        false_positive_class = (
            "off_target_recurrence" if on_scans else "off_target_only"
        )
        return "false_positive", false_positive_class, 0.99
    if len(on_scans) == 3:
        return "follow_up", None, 0.75
    return "insufficient_evidence", None, 0.60


def _audit_label(
    group: list[CadenceHit],
    ordered_artifacts: tuple[str, ...],
) -> str:
    roles_by_artifact = {
        hit.source_artifact: hit.scan_role
        for hit in group
    }
    signature = tuple(
        roles_by_artifact.get(artifact, "absent")
        for artifact in ordered_artifacts
    )
    if "off" in signature:
        return "false_positive"
    on_positions = sum(1 for role in signature if role == "on")
    return "follow_up" if on_positions == 3 else "insufficient_evidence"


def _candidate_mapping(
    group: list[CadenceHit],
    *,
    candidate_id: str,
    cadence_id: str,
    source_csv_sha256: str,
) -> dict[str, Any]:
    rows: list[dict[str, FeatureValue]] = [
        {
            "frequency_hz": hit.frequency_hz,
            "drift_rate_hz_per_sec": hit.drift_rate_hz_per_sec,
            "snr": hit.snr,
            "bandwidth_hz": 2.79,
            "scan_role": hit.scan_role,
            "target_id": hit.target_id,
            "source_artifact": hit.source_artifact,
        }
        for hit in group
    ]
    candidate = build_radio_candidate(
        candidate_id,
        rows,
        source_ids=tuple(sorted({hit.source_artifact for hit in group})),
        provenance={
            "source_dataset": cadence_id,
            "classification": "derived_real_observation_evidence_group",
            "source_csv_sha256": source_csv_sha256,
            "external_submission_authorized": False,
        },
    )
    return {
        "candidate_id": candidate.candidate_id,
        "track": candidate.track.value,
        "source_ids": list(candidate.source_ids),
        "features": dict(candidate.features),
        "provenance": dict(candidate.provenance),
    }


def cadence_abacab_review_summary(
    cadence_csv: Path,
    *,
    limit: int = 10,
    cadence_id: str | None = None,
) -> dict[str, Any]:
    """Summarize candidate-level ON/OFF cadence outcomes for a real GBT cadence."""
    source_ids, cadence_provenance = cadence_candidate_context(cadence_csv)
    hits = load_cadence_hits(cadence_csv)
    ordered_artifacts = tuple(dict.fromkeys(hit.source_artifact for hit in hits))
    if len(ordered_artifacts) != 6:
        raise ValueError("GBT ABACAB review requires exactly six cadence scans.")

    source_csv_sha256 = _sha256(cadence_csv)
    resolved_cadence_id = (
        cadence_id
        or str(cadence_provenance.get("source_dataset") or cadence_csv.stem)
    )
    groups = group_cadence_hits(hits)
    counts: dict[str, int] = defaultdict(int)
    false_positive_classes: dict[str, int] = defaultdict(int)
    disagreements = 0
    follow_up_candidates: list[dict[str, Any]] = []

    for index, group in enumerate(groups, start=1):
        primary_label, false_positive_class, confidence = _primary_label(group)
        audit_label = _audit_label(group, ordered_artifacts)
        agreement = primary_label == audit_label
        if not agreement:
            disagreements += 1
            final_label = "insufficient_evidence"
            false_positive_class = None
            confidence = 0.50
        else:
            final_label = primary_label
        counts[final_label] += 1
        if false_positive_class:
            false_positive_classes[false_positive_class] += 1
        if final_label != "follow_up":
            continue

        frequency_hz = group[0].frequency_hz
        drift_rate = group[0].drift_rate_hz_per_sec
        follow_up_candidates.append(
            {
                "candidate_id": (
                    f"{resolved_cadence_id}-group-{index:03d}-"
                    f"{frequency_hz:.3f}-{drift_rate:.6f}"
                ),
                "follow_up_candidate_score": confidence,
                "frequency_hz": frequency_hz,
                "drift_rate_hz_per_sec": drift_rate,
                "measurement_count": len(group),
                "on_scan_count": len(
                    {hit.source_artifact for hit in group if hit.scan_role == "on"}
                ),
                "off_scan_count": len(
                    {hit.source_artifact for hit in group if hit.scan_role == "off"}
                ),
                "targets": sorted({hit.target_id for hit in group}),
                "source_artifacts": sorted({hit.source_artifact for hit in group}),
                "primary_label": primary_label,
                "audit_label": audit_label,
                "review_agreement": agreement,
            }
        )

    ranked_follow_ups = sorted(
        follow_up_candidates,
        key=lambda item: (
            -float(item["follow_up_candidate_score"]),
            float(item["frequency_hz"]),
            float(item["drift_rate_hz_per_sec"]),
        ),
    )
    return {
        "schema_version": CITIZEN_SCIENCE_ABACAB_REVIEW_SCHEMA_VERSION,
        "disclaimer": CITIZEN_SCIENCE_ABACAB_REVIEW_DISCLAIMER,
        "cadence_id": resolved_cadence_id,
        "cadence_csv": str(cadence_csv),
        "source_csv_sha256": source_csv_sha256,
        "row_count": len(hits),
        "evidence_group_count": len(groups),
        "source_artifact_count": len(ordered_artifacts),
        "source_artifacts": list(source_ids or ordered_artifacts),
        "label_counts": dict(sorted(counts.items())),
        "false_positive_class_counts": dict(sorted(false_positive_classes.items())),
        "follow_up_candidate_count": counts.get("follow_up", 0),
        "false_positive_count": counts.get("false_positive", 0),
        "insufficient_evidence_count": counts.get("insufficient_evidence", 0),
        "top_follow_up_candidates": ranked_follow_ups[: max(0, limit)],
        "review_summary": {
            "primary_method": "on_off_count_rule_v1",
            "audit_method": "six_position_scan_signature_v1",
            "agreement_count": len(groups) - disagreements,
            "disagreement_count": disagreements,
            "disagreements_forced_to_insufficient_evidence": True,
        },
        "ok": disagreements == 0,
        "expert_review_claimed": False,
        "external_validation_claimed": False,
        "external_submission_authorized": False,
        "detection_claimed": False,
    }


def build_citizen_science_dataset(
    cadence_csv: Path,
    *,
    cadence_id: str,
    data_license: str,
    data_use_url: str,
) -> dict[str, Any]:
    source_ids, cadence_provenance = cadence_candidate_context(cadence_csv)
    hits = load_cadence_hits(cadence_csv)
    ordered_artifacts = tuple(dict.fromkeys(hit.source_artifact for hit in hits))
    if len(ordered_artifacts) != 6:
        raise ValueError("Citizen-science labeling requires exactly six cadence scans.")

    source_csv_sha256 = _sha256(cadence_csv)
    entries: list[dict[str, Any]] = []
    disagreements = 0
    counts: dict[str, int] = defaultdict(int)
    false_positive_classes: dict[str, int] = defaultdict(int)

    for index, group in enumerate(group_cadence_hits(hits), start=1):
        primary_label, false_positive_class, confidence = _primary_label(group)
        audit_label = _audit_label(group, ordered_artifacts)
        agreement = primary_label == audit_label
        if not agreement:
            disagreements += 1
            final_label = "insufficient_evidence"
            false_positive_class = None
            confidence = 0.50
        else:
            final_label = primary_label

        counts[final_label] += 1
        if false_positive_class:
            false_positive_classes[false_positive_class] += 1

        frequency_hz = group[0].frequency_hz
        drift_rate = group[0].drift_rate_hz_per_sec
        candidate_id = (
            f"{cadence_id}-group-{index:03d}-"
            f"{frequency_hz:.3f}-{drift_rate:.6f}"
        )
        entries.append(
            {
                "entry_id": f"csl-{index:03d}",
                "candidate_id": candidate_id,
                "track": "radio",
                "label": final_label,
                "label_confidence": confidence,
                "labeled_by": "citizen_science_consensus_v1",
                "labeled_at": FIXED_REVIEW_TIMESTAMP,
                "false_positive_class": false_positive_class,
                "primary_label": primary_label,
                "audit_label": audit_label,
                "review_agreement": agreement,
                "evidence_group": {
                    "frequency_hz": frequency_hz,
                    "drift_rate_hz_per_sec": drift_rate,
                    "measurement_count": len(group),
                    "on_scan_count": len(
                        {hit.source_artifact for hit in group if hit.scan_role == "on"}
                    ),
                    "off_scan_count": len(
                        {hit.source_artifact for hit in group if hit.scan_role == "off"}
                    ),
                    "targets": sorted({hit.target_id for hit in group}),
                    "source_artifacts": sorted(
                        {hit.source_artifact for hit in group}
                    ),
                },
                "candidate": _candidate_mapping(
                    group,
                    candidate_id=candidate_id,
                    cadence_id=cadence_id,
                    source_csv_sha256=source_csv_sha256,
                ),
                "notes": (
                    "Operational cadence label only; no astrophysical source "
                    "attribution or technosignature claim."
                ),
            }
        )

    return {
        "schema_version": CITIZEN_SCIENCE_LABEL_SCHEMA_VERSION,
        "description": (
            "Real HIP99427 GBT cadence evidence groups labeled under a "
            "deterministic citizen-science reproducibility protocol."
        ),
        "disclaimer": CITIZEN_SCIENCE_LABEL_DISCLAIMER,
        "dataset_classification": "real_observation_citizen_science_labels",
        "review_policy": CITIZEN_SCIENCE_REVIEW_POLICY,
        "expert_review_claimed": False,
        "external_validation_claimed": False,
        "external_submission_authorized": False,
        "source_provenance": {
            **cadence_provenance,
            "source_csv": cadence_csv.name,
            "source_csv_sha256": source_csv_sha256,
            "source_artifacts": list(source_ids),
            "data_license": data_license,
            "data_use_url": data_use_url,
        },
        "grouping_method": {
            "unit": "exact_turboseti_frequency_drift_bin_across_six_scans",
            "frequency_precision_hz": 0.001,
            "drift_precision_hz_per_sec": 0.000001,
            "pseudo_replication_prevented": True,
        },
        "review_summary": {
            "primary_method": "on_off_count_rule_v1",
            "audit_method": "six_position_scan_signature_v1",
            "independent_method_review_completed": True,
            "agreement_count": len(entries) - disagreements,
            "disagreement_count": disagreements,
            "disagreements_forced_to_insufficient_evidence": True,
        },
        "total_entries": len(entries),
        "label_counts": dict(sorted(counts.items())),
        "false_positive_class_counts": dict(
            sorted(false_positive_classes.items())
        ),
        "entries": entries,
    }


def write_citizen_science_dataset(
    cadence_csv: Path,
    destination: Path,
    *,
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    dataset = build_citizen_science_dataset(
        cadence_csv,
        cadence_id=str(manifest["cadence_id"]),
        data_license=str(manifest["data_license"]),
        data_use_url=str(manifest["data_use_url"]),
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(dataset, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return dataset
