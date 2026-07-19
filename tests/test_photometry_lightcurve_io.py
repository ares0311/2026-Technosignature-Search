from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from astropy.io import fits

from techno_search.photometry.lightcurve_io import load_lightcurve_file

FIXTURE = Path(__file__).parent / "fixtures" / "photometry" / "sample_lightcurve.fits"


def test_generic_fits_table_uses_explicit_time_metadata() -> None:
    pytest.importorskip("lightkurve")

    light_curve = load_lightcurve_file(FIXTURE)

    assert len(light_curve) == 480
    assert light_curve.time.format == "jd"


def test_generic_fits_table_fails_closed_on_ambiguous_time_unit(tmp_path: Path) -> None:
    lightkurve = pytest.importorskip("lightkurve")
    ambiguous = tmp_path / "ambiguous_time.fits"
    shutil.copyfile(FIXTURE, ambiguous)
    with fits.open(ambiguous, mode="update") as hdus:
        hdus[1].header["TUNIT1"] = "d"

    with pytest.raises(lightkurve.LightkurveError, match="Not recognized"):
        load_lightcurve_file(ambiguous)
