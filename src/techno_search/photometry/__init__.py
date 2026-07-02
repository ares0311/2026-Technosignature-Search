"""Phase 2: real Transit Photometry (Kepler/TESS) ingest and detection."""

from techno_search.photometry.aperiodic_dip import DipEvent, detect_aperiodic_dips
from techno_search.photometry.bls_detection import BlsTransitResult, run_bls_transit_search
from techno_search.photometry.lightcurve_io import load_lightcurve_file
from techno_search.photometry.lightcurve_search import (
    LightcurveSearchResult,
    search_and_download_lightcurves,
)
from techno_search.photometry.prototype import build_transit_photometry_candidate

__all__ = [
    "BlsTransitResult",
    "DipEvent",
    "LightcurveSearchResult",
    "build_transit_photometry_candidate",
    "detect_aperiodic_dips",
    "load_lightcurve_file",
    "run_bls_transit_search",
    "search_and_download_lightcurves",
]
