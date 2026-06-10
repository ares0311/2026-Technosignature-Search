from __future__ import annotations

import json
from pathlib import Path

from techno_search.observation_artifact import (
    OBSERVATION_ARTIFACT_SCHEMA_VERSION,
    approved_observation_artifacts,
    assess_observation_artifact,
    provenance_path_for,
    sha256_file,
)


def _write_dat(path: Path, *, source: str = "HIP12345") -> Path:
    path.write_text(
        "\n".join(
            (
                f"# Source:{source}",
                "# MJD:59000.0",
                "# Top_Hit_#\tDrift_Rate\tSNR\tUncorrected_Frequency",
                "1\t0.25\t15.0\t1420.0",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _write_approved_provenance(path: Path) -> None:
    provenance_path_for(path).write_text(
        json.dumps(
            {
                "schema_version": OBSERVATION_ARTIFACT_SCHEMA_VERSION,
                "artifact_filename": path.name,
                "sha256": sha256_file(path),
                "classification": "real_observation",
                "source_archive": "Breakthrough Listen Open Data Archive",
                "source_url": "https://example.org/archive/observation.dat",
                "instrument": "Green Bank Telescope",
                "downloaded_utc": "2026-06-09T12:00:00Z",
                "data_use_review_status": "approved",
                "provenance_review_status": "approved",
                "human_approval_status": "approved",
                "approved_for_local_real_data": True,
            }
        ),
        encoding="utf-8",
    )


def test_synthetic_marker_blocks_artifact(tmp_path: Path) -> None:
    artifact = _write_dat(tmp_path / "synth_hits.dat", source="SYNTH_TEST")

    result = assess_observation_artifact(artifact)

    assert result.classification == "synthetic"
    assert result.approved_for_pipeline is False


def test_invalid_download_is_rejected(tmp_path: Path) -> None:
    artifact = tmp_path / "missing_hits.dat"
    artifact.write_text("404: Not Found", encoding="utf-8")

    result = assess_observation_artifact(artifact)

    assert result.classification == "invalid"
    assert result.approved_for_pipeline is False


def test_plausible_real_artifact_stays_unverified_without_sidecar(tmp_path: Path) -> None:
    artifact = _write_dat(tmp_path / "HIP12345_hits.dat")

    result = assess_observation_artifact(artifact)

    assert result.classification == "unverified_real_observation"
    assert result.approved_for_pipeline is False
    assert result.warnings


def test_hash_mismatch_blocks_approval(tmp_path: Path) -> None:
    artifact = _write_dat(tmp_path / "HIP12345_hits.dat")
    _write_approved_provenance(artifact)
    artifact.write_text(artifact.read_text(encoding="utf-8") + "# changed\n", encoding="utf-8")

    result = assess_observation_artifact(artifact)

    assert result.approved_for_pipeline is False
    assert any("SHA-256" in issue for issue in result.issues)


def test_complete_human_approved_provenance_allows_pipeline(tmp_path: Path) -> None:
    artifact = _write_dat(tmp_path / "HIP12345_hits.dat")
    _write_approved_provenance(artifact)

    result = assess_observation_artifact(artifact)

    assert result.classification == "approved_real_observation"
    assert result.approved_for_pipeline is True
    assert approved_observation_artifacts(tmp_path) == [artifact]


def test_pending_human_review_blocks_pipeline(tmp_path: Path) -> None:
    artifact = _write_dat(tmp_path / "HIP12345_hits.dat")
    _write_approved_provenance(artifact)
    provenance_path = provenance_path_for(artifact)
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    provenance["human_approval_status"] = "pending"
    provenance_path.write_text(json.dumps(provenance), encoding="utf-8")

    result = assess_observation_artifact(artifact)

    assert result.approved_for_pipeline is False
    assert any("Human approval" in issue for issue in result.issues)
