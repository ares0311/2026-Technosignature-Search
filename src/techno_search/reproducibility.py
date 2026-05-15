"""Reproducibility verification for persisted candidate report packets.

This module re-scores a candidate JSON packet using the current scoring
implementation and compares the recomputed result against the persisted
packet. It is read-only: it never rewrites the packet, manifest, or
disk artifacts. Drift is reported, not auto-corrected.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from techno_search.constants import DEFAULT_SCHEMA_VERSION, DEFAULT_SCORING_CONFIG_VERSION
from techno_search.reporting import candidate_packet
from techno_search.schemas import candidate_from_mapping
from techno_search.scoring import score_candidate

REPRODUCIBILITY_VERIFICATION_SCHEMA_VERSION = "reproducibility_verification_v1"
REPRODUCIBILITY_VERIFICATION_DISCLAIMER = (
    "Reproducibility verification reports drift between a persisted candidate "
    "packet and a recomputed score using the current implementation. It is "
    "not external validation, calibration, or a discovery claim, and it does "
    "not auto-correct historical artifacts."
)


def verify_packet_against_manifest(
    *,
    candidate_path: Path | str,
    persisted_packet_path: Path | str,
    manifest_path: Path | str,
) -> dict[str, object]:
    """Re-score a candidate JSON file and compare against a persisted packet."""

    candidate_path = Path(candidate_path)
    persisted_packet_path = Path(persisted_packet_path)
    manifest_path = Path(manifest_path)

    with candidate_path.open(encoding="utf-8") as handle:
        candidate_data = json.load(handle)
    with persisted_packet_path.open(encoding="utf-8") as handle:
        persisted_packet = json.load(handle)
    with manifest_path.open(encoding="utf-8") as handle:
        manifest = json.load(handle)

    candidate = candidate_from_mapping(candidate_data)
    recomputed_packet = candidate_packet(score_candidate(candidate))

    posterior_drift = _drift(
        recomputed_packet.get("posterior", {}),
        persisted_packet.get("posterior", {}),
    )
    score_drift = _drift(
        recomputed_packet.get("scores", {}),
        persisted_packet.get("scores", {}),
    )
    pathway_drift = (
        recomputed_packet.get("recommended_pathway")
        != persisted_packet.get("recommended_pathway")
    )

    schema_match = (
        manifest.get("schema_version", "") == DEFAULT_SCHEMA_VERSION
        and persisted_packet.get("schema_version", "") == DEFAULT_SCHEMA_VERSION
    )
    config_match = (
        manifest.get("config_version", "") == DEFAULT_SCORING_CONFIG_VERSION
        and persisted_packet.get("config_version", "") == DEFAULT_SCORING_CONFIG_VERSION
    )

    drift_detected = bool(posterior_drift) or bool(score_drift) or pathway_drift
    return {
        "schema_version": REPRODUCIBILITY_VERIFICATION_SCHEMA_VERSION,
        "disclaimer": REPRODUCIBILITY_VERIFICATION_DISCLAIMER,
        "candidate_path": str(candidate_path),
        "persisted_packet_path": str(persisted_packet_path),
        "manifest_path": str(manifest_path),
        "candidate_id": str(persisted_packet.get("candidate_id", "")),
        "ok": not drift_detected and schema_match and config_match,
        "drift_detected": drift_detected,
        "schema_version_match": schema_match,
        "config_version_match": config_match,
        "expected_schema_version": DEFAULT_SCHEMA_VERSION,
        "expected_config_version": DEFAULT_SCORING_CONFIG_VERSION,
        "manifest_schema_version": str(manifest.get("schema_version", "")),
        "manifest_config_version": str(manifest.get("config_version", "")),
        "persisted_schema_version": str(persisted_packet.get("schema_version", "")),
        "persisted_config_version": str(persisted_packet.get("config_version", "")),
        "recommended_pathway_drift": pathway_drift,
        "persisted_recommended_pathway": str(
            persisted_packet.get("recommended_pathway", "")
        ),
        "recomputed_recommended_pathway": str(
            recomputed_packet.get("recommended_pathway", "")
        ),
        "posterior_drift": posterior_drift,
        "score_drift": score_drift,
        "uncertainty_and_limitations": [
            "Recomputed values come from the current implementation only.",
            "Drift only describes local repository state, not survey performance.",
            "Reports are not auto-corrected; review and republish if needed.",
        ],
    }


def verify_report_directory(report_dir: Path | str) -> dict[str, object]:
    """Verify all candidate packets in a report directory against their manifests.

    The report directory is assumed to contain ``<stem>.manifest.json``,
    ``<stem>.json``, and a corresponding source candidate JSON under
    ``examples/candidates/`` matching the persisted ``candidate_id``.
    """

    directory = Path(report_dir)
    manifest_paths = sorted(directory.glob("*.manifest.json"))
    project_root = Path(__file__).resolve().parents[2]
    candidate_dir = project_root / "examples" / "candidates"

    per_packet: list[dict[str, object]] = []
    drift_count = 0
    for manifest_path in manifest_paths:
        with manifest_path.open(encoding="utf-8") as handle:
            manifest = json.load(handle)
        persisted_packet_path = Path(str(manifest.get("json_path", "")))
        if not persisted_packet_path.is_absolute():
            persisted_packet_path = project_root / persisted_packet_path
        candidate_id = str(manifest.get("candidate_id", ""))
        candidate_path = _candidate_source_path(candidate_dir, candidate_id)
        if candidate_path is None or not persisted_packet_path.exists():
            per_packet.append(
                {
                    "manifest_path": str(manifest_path),
                    "candidate_id": candidate_id,
                    "ok": False,
                    "drift_detected": False,
                    "skipped": True,
                    "reason": (
                        "matching candidate JSON or persisted packet not found"
                    ),
                }
            )
            continue
        verification = verify_packet_against_manifest(
            candidate_path=candidate_path,
            persisted_packet_path=persisted_packet_path,
            manifest_path=manifest_path,
        )
        if verification.get("drift_detected"):
            drift_count += 1
        per_packet.append(verification)

    return {
        "schema_version": REPRODUCIBILITY_VERIFICATION_SCHEMA_VERSION,
        "disclaimer": REPRODUCIBILITY_VERIFICATION_DISCLAIMER,
        "report_dir": str(directory),
        "manifest_count": len(manifest_paths),
        "verified_count": sum(1 for entry in per_packet if not entry.get("skipped")),
        "drift_count": drift_count,
        "ok": all(entry.get("ok", False) for entry in per_packet) and bool(per_packet),
        "verifications": per_packet,
    }


def _drift(
    recomputed: Mapping[str, object],
    persisted: Mapping[str, object],
) -> dict[str, dict[str, float]]:
    drift: dict[str, dict[str, float]] = {}
    keys = set(recomputed) | set(persisted)
    for key in sorted(keys):
        recomputed_value = recomputed.get(key)
        persisted_value = persisted.get(key)
        if not isinstance(recomputed_value, int | float) or not isinstance(
            persisted_value, int | float
        ):
            if recomputed_value != persisted_value:
                drift[key] = {
                    "recomputed": float("nan"),
                    "persisted": float("nan"),
                    "delta": float("nan"),
                }
            continue
        delta = float(recomputed_value) - float(persisted_value)
        if abs(delta) > 1e-9:
            drift[key] = {
                "recomputed": float(recomputed_value),
                "persisted": float(persisted_value),
                "delta": delta,
            }
    return drift


def _candidate_source_path(candidate_dir: Path, candidate_id: str) -> Path | None:
    if not candidate_id:
        return None
    for path in sorted(candidate_dir.glob("*.json")):
        try:
            with path.open(encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            continue
        if str(data.get("candidate_id", "")) == candidate_id:
            return path
    return None
