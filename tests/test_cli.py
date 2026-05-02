import json
from io import StringIO

from techno_search.cli import main, score_batch


def _candidate_json() -> dict[str, object]:
    return {
        "candidate_id": "cli-radio",
        "track": "radio",
        "source_ids": ["synthetic-cli"],
        "features": {
            "snr": 35.0,
            "bandwidth_hz": 1.5,
            "drift_rate_hz_per_sec": 2.0,
            "on_target_presence_score": 0.9,
            "off_target_presence_score": 0.05,
            "rfi_band_overlap_score": 0.05,
            "frequency_persistence_score": 0.05,
            "instrumental_artifact_score": 0.05,
            "metadata_completeness_score": 0.9,
            "data_quality_score": 0.9,
            "provenance_completeness_score": 0.9,
        },
        "provenance": {"source_dataset": "synthetic-cli"},
    }


def test_cli_scores_candidate_json_to_stdout(tmp_path) -> None:
    input_path = tmp_path / "candidate.json"
    input_path.write_text(json.dumps(_candidate_json()), encoding="utf-8")
    stdout = StringIO()

    exit_code = main(["score", str(input_path)], stdout=stdout)
    packet = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert packet["candidate_id"] == "cli-radio"
    assert packet["schema_version"] == "techno_search_packet_v1"
    assert packet["recommended_pathway"]
    assert packet["disclaimer"]


def test_cli_writes_reports(tmp_path) -> None:
    input_path = tmp_path / "candidate.json"
    output_dir = tmp_path / "reports"
    input_path.write_text(json.dumps(_candidate_json()), encoding="utf-8")
    stdout = StringIO()

    exit_code = main(
        ["score", str(input_path), "--output-dir", str(output_dir), "--prefix", "cli-radio"],
        stdout=stdout,
    )

    assert exit_code == 0
    assert (output_dir / "cli-radio.md").exists()
    assert (output_dir / "cli-radio.json").exists()
    assert (output_dir / "cli-radio.manifest.json").exists()
    assert "cli-radio.md" in stdout.getvalue()


def test_cli_scores_batch_directory(tmp_path) -> None:
    input_dir = tmp_path / "candidates"
    output_dir = tmp_path / "reports"
    input_dir.mkdir()
    (input_dir / "candidate-a.json").write_text(json.dumps(_candidate_json()), encoding="utf-8")
    candidate_b = _candidate_json() | {"candidate_id": "cli-radio-b"}
    (input_dir / "candidate-b.json").write_text(json.dumps(candidate_b), encoding="utf-8")
    stdout = StringIO()

    exit_code = main(
        ["score-batch", str(input_dir), str(output_dir), "--prefix", "batch-"],
        stdout=stdout,
    )

    manifest_path = output_dir / "batch_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert stdout.getvalue().strip() == str(manifest_path)
    assert manifest["candidate_count"] == 2
    assert manifest["schema_version"] == "techno_search_packet_v1"
    assert manifest["config_version"] == "scoring_v0"
    assert (output_dir / "batch-cli-radio.md").exists()
    assert (output_dir / "batch-cli-radio-b.md").exists()
    assert len(manifest["reports"]) == 2


def test_score_batch_regenerates_expected_example_candidate_set(tmp_path) -> None:
    manifest_path = score_batch("examples/candidates", tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["candidate_count"] == 3
    assert {report["candidate_id"] for report in manifest["reports"]} == {
        "example-radio-clean",
        "example-infrared-clean",
        "example-anomaly-clean",
    }
    for report in manifest["reports"]:
        assert report["config_version"] == "scoring_v0"
        assert (tmp_path / f"{report['candidate_id']}.md").exists()
        assert (tmp_path / f"{report['candidate_id']}.json").exists()
        assert (tmp_path / f"{report['candidate_id']}.manifest.json").exists()


def test_cli_calibration_summary_outputs_fixture_counts() -> None:
    stdout = StringIO()

    exit_code = main(["calibration-summary"], stdout=stdout)
    summary = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert summary["total"] == 15
    assert summary["by_track"] == {"anomaly": 6, "infrared": 5, "radio": 4}
    assert summary["by_expected_pathway"] == {"do_not_submit_false_positive": 15}


def test_cli_validate_candidate_accepts_normalized_candidate(tmp_path) -> None:
    input_path = tmp_path / "candidate.json"
    input_path.write_text(json.dumps(_candidate_json()), encoding="utf-8")
    stdout = StringIO()

    exit_code = main(["validate-candidate", str(input_path)], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["ok"] is True
    assert result["errors"] == []


def test_cli_validate_candidate_rejects_unsupported_language(tmp_path) -> None:
    input_path = tmp_path / "candidate.json"
    candidate = _candidate_json() | {"candidate_id": "alien signal claim"}
    input_path.write_text(json.dumps(candidate), encoding="utf-8")
    stdout = StringIO()

    exit_code = main(["validate-candidate", str(input_path)], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 1
    assert result["ok"] is False
    assert "alien signal" in result["errors"][0]


def test_cli_validate_reports_accepts_generated_reports(tmp_path) -> None:
    input_path = tmp_path / "candidate.json"
    output_dir = tmp_path / "reports"
    input_path.write_text(json.dumps(_candidate_json()), encoding="utf-8")
    main(["score", str(input_path), "--output-dir", str(output_dir)], stdout=StringIO())
    stdout = StringIO()

    exit_code = main(["validate-reports", str(output_dir)], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["ok"] is True
    assert result["errors"] == []


def test_cli_schema_paths_outputs_schema_artifacts() -> None:
    stdout = StringIO()

    exit_code = main(["schema-paths"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert set(result) == {"batch_manifest", "candidate_packet", "report_manifest"}
    assert result["candidate_packet"].endswith("schemas/candidate_packet.schema.json")


def test_cli_score_regression_summary_outputs_snapshot_counts() -> None:
    stdout = StringIO()

    exit_code = main(["score-regression-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["candidate_count"] == 3
    assert result["by_track"] == {"anomaly": 1, "infrared": 1, "radio": 1}
    assert result["by_recommended_pathway"] == {"candidate_review_packet": 3}


def test_cli_validate_all_outputs_local_summary() -> None:
    stdout = StringIO()

    exit_code = main(["validate-all"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["ok"] is True
    assert result["calibration_summary"]["total"] == 15
    assert result["score_regression_summary"]["candidate_count"] == 3
    assert result["catalog_cache_validation"]["ok"] is True
    assert result["catalog_cache_validation"]["forbidden_roots"] == [
        "data",
        "cache",
        "artifacts",
    ]
    assert all(result["schema_paths_exist"].values())


def test_cli_regenerate_examples_writes_relative_example_outputs(tmp_path, monkeypatch) -> None:
    candidate_dir = tmp_path / "examples" / "candidates"
    candidate_dir.mkdir(parents=True)
    (candidate_dir / "candidate.json").write_text(json.dumps(_candidate_json()), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    stdout = StringIO()

    exit_code = main(["regenerate-examples"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["candidate_count"] == 1
    assert result["reports_dir"] == "examples/reports"
    assert (tmp_path / "examples" / "reports" / "cli-radio.json").exists()
    assert (tmp_path / "examples" / "batch_reports" / "batch_manifest.json").exists()


def test_cli_provenance_summary_outputs_example_report_counts() -> None:
    stdout = StringIO()

    exit_code = main(["provenance-summary", "examples/reports"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["manifest_count"] == 3
    assert result["by_track"] == {"anomaly": 1, "infrared": 1, "radio": 1}
    assert result["by_schema_version"] == {"techno_search_packet_v1": 3}
    assert result["by_config_version"] == {"scoring_v0": 3}


def test_cli_provenance_summary_outputs_batch_report_counts() -> None:
    stdout = StringIO()

    exit_code = main(["provenance-summary", "examples/batch_reports"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["manifest_count"] == 3
    assert result["by_track"] == {"anomaly": 1, "infrared": 1, "radio": 1}
    assert result["by_source_dataset"] == {"synthetic-example": 3}


def test_cli_live_provider_summary_lists_default_off_providers(monkeypatch) -> None:
    monkeypatch.delenv("TECHNO_SEARCH_ENABLE_LIVE_DATA", raising=False)
    stdout = StringIO()

    exit_code = main(["live-provider-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["live_enabled"] is False
    assert result["provider_count"] == 5
    assert {provider["provider_name"] for provider in result["providers"]} == {
        "breakthrough_listen",
        "gaia",
        "irsa",
        "simbad",
        "vizier",
    }


def test_cli_live_cache_summary_outputs_cache_counts(tmp_path) -> None:
    cache_dir = tmp_path / "cache" / "live_providers"
    provider_dir = cache_dir / "gaia"
    provider_dir.mkdir(parents=True)
    (provider_dir / "abc.metadata.json").write_text("{}", encoding="utf-8")
    stdout = StringIO()

    exit_code = main(["live-cache-summary", "--cache-dir", str(cache_dir)], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["cache_dir"] == str(cache_dir)
    assert result["exists"] is True
    assert result["metadata_file_count"] == 1
    assert result["by_provider"] == {"gaia": 1}


def test_cli_live_fixture_summary_outputs_committed_fixture_counts() -> None:
    stdout = StringIO()

    exit_code = main(["live-fixture-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["fixture_schema_version"] == "live_metadata_fixture_v1"
    assert result["fixture_count"] == 8
    assert result["by_provider"] == {
        "breakthrough_listen": 1,
        "gaia": 2,
        "irsa": 2,
        "simbad": 1,
        "vizier": 2,
    }


def test_cli_live_client_summary_outputs_disabled_skeleton_status(monkeypatch) -> None:
    monkeypatch.delenv("TECHNO_SEARCH_ENABLE_LIVE_DATA", raising=False)
    stdout = StringIO()

    exit_code = main(["live-client-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["live_enabled"] is False
    assert result["client_count"] == 5
    assert {client["provider_name"] for client in result["clients"]} == {
        "breakthrough_listen",
        "gaia",
        "irsa",
        "simbad",
        "vizier",
    }
    implemented_by_provider = {
        client["provider_name"]: client["implemented"] for client in result["clients"]
    }
    assert implemented_by_provider == {
        "breakthrough_listen": False,
        "gaia": True,
        "irsa": True,
        "simbad": False,
        "vizier": True,
    }
    assert all(client["requires_live_opt_in"] is True for client in result["clients"])


def test_cli_catalog_cache_policy_outputs_policy_without_creating_dir(tmp_path) -> None:
    cache_root = tmp_path / "catalog-cache"
    stdout = StringIO()

    exit_code = main(
        ["catalog-cache-policy", "--cache-root", str(cache_root)],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["cache_root"] == str(cache_root)
    assert result["allowed_suffixes"] == [".metadata.json", ".json"]
    assert result["creates_directories"] is False
    assert result["implements_catalog_ingestion"] is False
    assert not cache_root.exists()


def test_cli_catalog_cache_validate_accepts_fixture_paths() -> None:
    stdout = StringIO()

    exit_code = main(
        [
            "catalog-cache-validate",
            "tests/fixtures/live_metadata/gaia_cone_search.metadata.json",
            "docs/CATALOG_CACHE_POLICY.md",
        ],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["ok"] is True
    assert result["errors"] == []
    assert result["checked_path_count"] == 2


def test_cli_catalog_cache_validate_rejects_forbidden_paths() -> None:
    stdout = StringIO()

    exit_code = main(
        [
            "catalog-cache-validate",
            "cache/catalog_metadata/gaia/example.metadata.json",
            "data/raw/catalog.csv",
        ],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 1
    assert result["ok"] is False
    assert result["errors"] == [
        (
            "Catalog cache path must not be committed: "
            "cache/catalog_metadata/gaia/example.metadata.json"
        ),
        "Catalog cache path must not be committed: data/raw/catalog.csv",
    ]
