import pandas as pd
import pytest

from techno_search.track_a_catalogs import (
    fits_table_to_pandas,
    normalize_atnf_pulsars,
    normalize_chime_frb,
    normalize_fermi_4fgl,
    normalize_romabzcat,
)


def test_normalize_atnf_pulsars_parses_sexagesimal_coordinates() -> None:
    df = pd.DataFrame(
        {
            "PSRJ": ["J0534+2200"],
            "RAJ": ["05:34:31.97"],
            "DECJ": ["+22:00:52.1"],
        }
    )

    normalized = normalize_atnf_pulsars(df)

    assert normalized.loc[0, "source_id"] == "J0534+2200"
    assert normalized.loc[0, "object_class"] == "pulsar"
    assert normalized.loc[0, "catalog_name"] == "atnf"
    assert normalized.loc[0, "ra_deg"] == pytest.approx(83.633208, abs=1e-3)
    assert normalized.loc[0, "dec_deg"] == pytest.approx(22.014472, abs=1e-3)


def test_normalize_atnf_pulsars_rejects_missing_columns() -> None:
    df = pd.DataFrame({"PSRJ": ["J0534+2200"]})

    with pytest.raises(ValueError, match="RAJ, DECJ"):
        normalize_atnf_pulsars(df)


def test_normalize_chime_frb_maps_repeater_flag() -> None:
    df = pd.DataFrame(
        {
            "TNS": ["FRB20180814A", "FRB20181017A"],
            "RAJ2000": [16.61, 55.0],
            "DEJ2000": [73.66, 30.0],
            "Rep": ["R", ""],
        }
    )

    normalized = normalize_chime_frb(df)

    assert normalized.loc[0, "object_class"] == "repeating_frb"
    assert normalized.loc[1, "object_class"] == "nonrepeating_frb_candidate"
    assert normalized.loc[0, "catalog_name"] == "chime_frb"


def test_normalize_chime_frb_without_repeater_column_defaults_to_frb() -> None:
    df = pd.DataFrame({"TNS": ["FRB20180814A"], "RAJ2000": [16.61], "DEJ2000": [73.66]})

    normalized = normalize_chime_frb(df)

    assert normalized.loc[0, "object_class"] == "frb"


def test_normalize_romabzcat_assigns_blazar_agn_class() -> None:
    df = pd.DataFrame({"Name": ["5BZQJ0006-0623"], "RAJ2000": [1.55], "DEJ2000": [-6.39]})

    normalized = normalize_romabzcat(df)

    assert normalized.loc[0, "object_class"] == "blazar_agn"
    assert normalized.loc[0, "catalog_name"] == "romabzcat"


def test_normalize_fermi_4fgl_assigns_gamma_ray_source_class() -> None:
    df = pd.DataFrame(
        {"Source_Name": ["4FGL J0000.3+7218"], "RAJ2000": [0.85], "DEJ2000": [72.31]}
    )

    normalized = normalize_fermi_4fgl(df)

    assert normalized.loc[0, "object_class"] == "gamma_ray_source"
    assert normalized.loc[0, "catalog_name"] == "fermi_4fgl"


def test_normalize_rejects_missing_coordinate_columns() -> None:
    df = pd.DataFrame({"Name": ["x"]})

    with pytest.raises(ValueError, match="coordinate columns"):
        normalize_romabzcat(df)


def test_fits_table_to_pandas_drops_multidimensional_columns() -> None:
    """Regression test: Fermi 4FGL-DR4 has per-band array columns that crash
    astropy.Table.to_pandas() directly (real failure observed acquiring the
    live catalog: 'Cannot convert a table with multidimensional columns')."""
    astropy_table = pytest.importorskip("astropy.table")
    table = astropy_table.Table(
        {
            "Source_Name": ["4FGL J0000.3+7218"],
            "RAJ2000": [0.85],
            "DEJ2000": [72.31],
            "Flux_Band": [[1.0, 2.0, 3.0]],
            "Sqrt_TS_Band": [[0.1, 0.2, 0.3]],
        }
    )

    df = fits_table_to_pandas(table)

    assert list(df.columns) == ["Source_Name", "RAJ2000", "DEJ2000"]
    assert len(df) == 1
