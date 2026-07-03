# Research request: real JWST MIRI LRS target for a MAST download test

## Context (assume zero prior knowledge of this project)

I run a codebase called "Technosignature Search" that searches public
astronomical archives for candidate signals. It has a Python CLI command,
`techno-search jwst-miri-lrs-search <target>`, that queries NASA's MAST
archive via `astroquery.mast.Observations.query_criteria()` for real JWST
MIRI Low Resolution Spectrometer (LRS) transmission-spectrum observations
of a named astronomical object, then downloads the resulting "x1d"
(1D-extracted-spectrum) FITS product(s).

The query it runs is equivalent to:

```python
from astroquery.mast import Observations
obs = Observations.query_criteria(
    objectname="<TARGET>",
    obs_collection="JWST",
    instrument_name=["MIRI/SLIT", "MIRI/SLITLESS"],
    filters="P750L",
)
```

I need a **real target name that resolves via MAST's name resolver and
actually has at least one MIRI LRS observation with an x1d product
available**, so I can run and verify this command for the first time
against real data. I do not want a guessed name — the command has already
failed once against a placeholder string.

## What I need you to find and report back

1. **One (or a few) real, specific object identifiers** (e.g. a star name,
   "WASP-XX", "TOI-XXXX", a 2MASS/Gaia ID, etc.) that MAST's name resolver
   can resolve to a sky position, AND that has at least one real JWST
   MIRI LRS observation (`instrument_name` = `MIRI/SLIT` or
   `MIRI/SLITLESS`) with a corresponding x1d or x1dints data product
   available for download.
2. How you verified it (e.g. searched the MAST portal directly at
   https://mast.stsci.edu/portal/Mashup/Clients/Mast/Portal.html, or the
   JWST proposal/program information, or a paper that names the exact
   target and instrument mode used). I need a citable source or a
   direct verification method, not an inference from general astronomy
   knowledge.
3. If possible, the exact MAST **proposal ID / observation ID** for that
   x1d product, so I can cross-check it lines up with what my code
   downloads.

## What NOT to do

- Do not guess a plausible-sounding star name without checking it actually
  has MIRI LRS x1d data in MAST — many exoplanet hosts have *other*
  instrument modes (NIRSpec, NIRISS) but not MIRI LRS specifically.
- Do not assume Boyajian's Star (KIC 8462852) has MIRI LRS observations —
  that target was used in a *different* part of this project (Kepler
  photometry), not JWST spectroscopy, and I have no evidence it has JWST
  MIRI LRS data.
