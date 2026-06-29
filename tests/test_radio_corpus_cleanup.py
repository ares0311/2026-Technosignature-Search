from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

from techno_search.cli import main
from techno_search.radio_corpus_cleanup import (
    apply_radio_corpus_cleanup,
    plan_radio_corpus_cleanup,
)


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    (root / "data" / "extended_corpus").mkdir(parents=True)
    (root / "results").mkdir()
    return root


def _write_zero_hit_manifest(results_dir: Path, source_data_path: str) -> None:
    manifest_dir = results_dir / "HIPZERO" / "obs"
    manifest_dir.mkdir(parents=True)
    (manifest_dir / "HIPZERO__obs.manifest.json").write_text(
        json.dumps({
            "schema_version": "zero_hit_observation_manifest_v1",
            "artifact_kind": "zero_hit_observation_manifest",
            "source_data_path": source_data_path,
        }),
        encoding="utf-8",
    )


def test_radio_corpus_cleanup_plans_hdf5_and_zero_hit_dat_only(tmp_path: Path) -> None:
    root = _project(tmp_path)
    corpus = root / "data" / "extended_corpus"
    results = root / "results"
    converted = corpus / "HIPCONV"
    converted.mkdir()
    (converted / "obs.h5").write_bytes(b"hdf5 payload")
    (converted / "obs.dat").write_text("hit rows\n", encoding="utf-8")
    zero_hit = corpus / "HIPZERO"
    zero_hit.mkdir()
    (zero_hit / "obs.dat").write_text("# header only\n", encoding="utf-8")
    hit_bearing = corpus / "HIPHIT"
    hit_bearing.mkdir()
    (hit_bearing / "obs.dat").write_text("hit rows\n", encoding="utf-8")
    _write_zero_hit_manifest(results, "HIPZERO/obs.dat")

    plan = plan_radio_corpus_cleanup(corpus, results_dir=results, project_root=root)

    assert plan["ok"] is True
    assert plan["candidate_count"] == 2
    reasons = {entry["reason"] for entry in plan["candidates"]}
    paths = {entry["relative_path"] for entry in plan["candidates"]}
    assert reasons == {"hdf5_converted_to_dat", "zero_hit_dat_manifested"}
    assert "data/extended_corpus/HIPCONV/obs.h5" in paths
    assert "data/extended_corpus/HIPZERO/obs.dat" in paths
    assert "data/extended_corpus/HIPHIT/obs.dat" not in paths
    zero_hit_entries = [
        entry for entry in plan["candidates"]
        if entry["reason"] == "zero_hit_dat_manifested"
    ]
    assert zero_hit_entries[0]["evidence_relative_path"].endswith(
        "HIPZERO__obs.manifest.json"
    )


def test_radio_corpus_cleanup_apply_requires_acknowledgement(tmp_path: Path) -> None:
    root = _project(tmp_path)
    corpus = root / "data" / "extended_corpus"
    target = corpus / "HIPCONV"
    target.mkdir()
    h5_path = target / "obs.h5"
    h5_path.write_bytes(b"hdf5 payload")
    (target / "obs.dat").write_text("hit rows\n", encoding="utf-8")

    blocked = apply_radio_corpus_cleanup(corpus, project_root=root)

    assert blocked["apply_blocked"] is True
    assert h5_path.exists()


def test_radio_corpus_cleanup_apply_deletes_only_candidates(tmp_path: Path) -> None:
    root = _project(tmp_path)
    corpus = root / "data" / "extended_corpus"
    target = corpus / "HIPCONV"
    target.mkdir()
    h5_path = target / "obs.h5"
    dat_path = target / "obs.dat"
    h5_path.write_bytes(b"hdf5 payload")
    dat_path.write_text("hit rows\n", encoding="utf-8")

    result = apply_radio_corpus_cleanup(
        corpus,
        project_root=root,
        acknowledge_local_apply=True,
    )

    assert result["ok"] is True
    assert result["deleted_count"] == 1
    assert not h5_path.exists()
    assert dat_path.exists()


def test_radio_corpus_cleanup_refuses_non_extended_corpus_path(tmp_path: Path) -> None:
    root = _project(tmp_path)
    outside = root / "data" / "bl_hits"
    outside.mkdir()

    plan = plan_radio_corpus_cleanup(outside, project_root=root)

    assert plan["ok"] is False
    assert plan["refused"] is True


def test_cli_radio_corpus_cleanup_dry_run_default(tmp_path: Path) -> None:
    root = _project(tmp_path)
    corpus = root / "data" / "extended_corpus"
    target = corpus / "HIPCONV"
    target.mkdir()
    h5_path = target / "obs.h5"
    h5_path.write_bytes(b"hdf5 payload")
    (target / "obs.dat").write_text("hit rows\n", encoding="utf-8")
    stdout = StringIO()

    import techno_search.cli as cli

    original = cli.default_project_root
    cli.default_project_root = lambda: root  # type: ignore[assignment]
    try:
        exit_code = main(
            ["radio-corpus-cleanup", "--corpus-dir", str(corpus)],
            stdout=stdout,
        )
    finally:
        cli.default_project_root = original  # type: ignore[assignment]
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["candidate_count"] == 1
    assert "applied" not in result
    assert h5_path.exists()
