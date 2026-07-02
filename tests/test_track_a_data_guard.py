from techno_search.track_a_data_guard import (
    AcquisitionManifestRecord,
    append_acquisition_manifest,
    check_disk_budget_or_raise,
    load_acquisition_manifest,
    track_a_disk_usage,
)


def test_disk_usage_reports_zero_for_missing_dirs(tmp_path) -> None:
    report = track_a_disk_usage(project_root=tmp_path)

    assert report.total_bytes == 0
    assert report.within_budget is True
    assert set(report.dir_sizes_bytes) == {"data_cache", "tmp_training", "tmp_features"}


def test_disk_usage_sums_real_file_sizes(tmp_path) -> None:
    cache_dir = tmp_path / "data_cache" / "raw" / "htru2"
    cache_dir.mkdir(parents=True)
    (cache_dir / "features.parquet").write_bytes(b"0" * 1000)

    report = track_a_disk_usage(project_root=tmp_path)

    assert report.dir_sizes_bytes["data_cache"] == 1000
    assert report.total_bytes == 1000


def test_check_disk_budget_raises_when_projected_total_exceeds_budget(tmp_path) -> None:
    import pytest

    with pytest.raises(RuntimeError, match="disk budget would be exceeded"):
        check_disk_budget_or_raise(
            project_root=tmp_path,
            budget_bytes=100,
            additional_expected_bytes=200,
        )


def test_check_disk_budget_passes_within_budget(tmp_path) -> None:
    report = check_disk_budget_or_raise(
        project_root=tmp_path,
        budget_bytes=100,
        additional_expected_bytes=50,
    )
    assert report.within_budget is True


def test_manifest_append_and_load_round_trips(tmp_path) -> None:
    manifest_path = tmp_path / "artifacts" / "manifests" / "data_manifest.jsonl"
    record = AcquisitionManifestRecord(
        source_name="htru2",
        source_url="https://archive-beta.ics.uci.edu/dataset/372/htru2",
        access_method="ucimlrepo.fetch_ucirepo(id=372)",
        downloaded_at_utc="2026-07-02T00:00:00+00:00",
        local_path=str(tmp_path / "htru2_features.parquet"),
        file_size_bytes=12345,
        row_count=17898,
        auth_required=False,
        license_or_terms="CC BY 4.0",
    )

    append_acquisition_manifest(record, manifest_path)
    loaded = load_acquisition_manifest(manifest_path)

    assert len(loaded) == 1
    assert loaded[0]["source_name"] == "htru2"
    assert loaded[0]["row_count"] == 17898


def test_manifest_load_returns_empty_list_when_missing(tmp_path) -> None:
    assert load_acquisition_manifest(tmp_path / "nonexistent.jsonl") == []
