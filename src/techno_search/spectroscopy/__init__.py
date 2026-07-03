"""Phase 4: real JWST transmission-spectrum ingest and technosignature-gas search."""

from techno_search.spectroscopy.jwst_spectrum_io import load_jwst_x1d_spectrum
from techno_search.spectroscopy.technosignature_gases import (
    GAS_ABSORPTION_BANDS_UM,
    BandFeatureResult,
    search_gas_absorption_bands,
)

__all__ = [
    "GAS_ABSORPTION_BANDS_UM",
    "BandFeatureResult",
    "load_jwst_x1d_spectrum",
    "search_gas_absorption_bands",
]
