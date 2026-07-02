import pandas as pd
import pytest

from techno_search.track_a_crossmatch import cross_match_known_sources


def _write_catalog(tmp_path, *, name, rows):
    pytest.importorskip("pyarrow")
    out_dir = tmp_path / "data_cache" / "normalized"
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(out_dir / f"{name}.parquet", index=False)


def test_cross_match_finds_known_pulsar_within_radius(tmp_path) -> None:
    _write_catalog(
        tmp_path,
        name="atnf",
        rows=[
            {
                "source_id": "J0534+2200",
                "ra_deg": 83.633208,
                "dec_deg": 22.014472,
                "object_class": "pulsar",
                "catalog_name": "atnf",
            }
        ],
    )

    result = cross_match_known_sources(
        83.6332,
        22.0145,
        catalogs=("atnf",),
        project_root=tmp_path,
    )

    assert result["classification"] == "known_pulsar"
    assert result["match_count"] == 1
    assert result["best_match"]["source_id"] == "J0534+2200"
    assert result["best_match"]["separation_arcsec"] < 5.0
    assert result["catalogs_missing"] == []


def test_cross_match_reports_low_confidence_when_catalog_missing(tmp_path) -> None:
    result = cross_match_known_sources(
        10.0,
        10.0,
        catalogs=("atnf", "chime_frb"),
        project_root=tmp_path,
    )

    assert result["classification"] == "low_confidence"
    assert set(result["catalogs_missing"]) == {"atnf", "chime_frb"}
    assert result["match_count"] == 0


def test_cross_match_reports_no_known_match_when_all_catalogs_loaded_but_empty(
    tmp_path,
) -> None:
    _write_catalog(
        tmp_path,
        name="atnf",
        rows=[
            {
                "source_id": "J9999+0000",
                "ra_deg": 200.0,
                "dec_deg": -40.0,
                "object_class": "pulsar",
                "catalog_name": "atnf",
            }
        ],
    )

    result = cross_match_known_sources(
        10.0,
        10.0,
        catalogs=("atnf",),
        project_root=tmp_path,
    )

    assert result["classification"] == "no_known_match"
    assert result["catalogs_missing"] == []
    assert result["match_count"] == 0


def test_cross_match_picks_closest_match_across_catalogs(tmp_path) -> None:
    _write_catalog(
        tmp_path,
        name="atnf",
        rows=[
            {
                "source_id": "far_pulsar",
                "ra_deg": 10.05,
                "dec_deg": 10.05,
                "object_class": "pulsar",
                "catalog_name": "atnf",
            }
        ],
    )
    _write_catalog(
        tmp_path,
        name="romabzcat",
        rows=[
            {
                "source_id": "close_blazar",
                "ra_deg": 10.0001,
                "dec_deg": 10.0001,
                "object_class": "blazar_agn",
                "catalog_name": "romabzcat",
            }
        ],
    )

    result = cross_match_known_sources(
        10.0,
        10.0,
        radius_arcsec=60.0,
        catalogs=("atnf", "romabzcat"),
        project_root=tmp_path,
    )

    assert result["classification"] == "known_blazar_agn"
    assert result["best_match"]["source_id"] == "close_blazar"
    assert result["match_count"] == 1


def test_cross_match_disclaimer_present() -> None:
    result = cross_match_known_sources(0.0, 0.0, catalogs=())
    assert "does not confirm" in result["disclaimer"]
