# Research request: additional HITRAN temperature/pressure cross-section datasets

## Context (assume zero prior knowledge of this project)

I run a project that searches real JWST exoplanet transmission spectra for
absorption features of five specific industrial/artificial gases with no
natural planetary source: CF4, C2F6, C3F8, SF6, NF3. Band centers were
already derived from real HITRAN absorption cross-section files
(hitran.org), one file per gas, each measured at 298.1 K / 760.0 Torr
(room temperature, 1 atmosphere):

| Gas | HITRAN molecule ID | Cross-section dataset ID downloaded |
|---|---|---|
| CF4 | 42 | 2827 |
| C2F6 | 107 | 2885 |
| C3F8 | 401 | 2906 |
| SF6 | 30 | 3032 |
| NF3 | 55 | 2987 |

## What I need you to check

Real exoplanet atmospheres are not at 298 K / 760 Torr. I need to know
whether HITRAN's cross-section database (https://hitran.org/xsc/) has
**additional datasets for these same five gases at other temperature
and/or pressure conditions** (lower pressure especially, since exoplanet
atmospheres of interest are typically much lower pressure than 1 atm at
the altitudes relevant to transmission spectroscopy).

For each of the five gases above:
1. Search https://hitran.org/xsc/ for the molecule (by name or the
   molecule ID given above).
2. List every cross-section dataset ID available for that molecule, with
   its exact temperature and pressure condition (as labeled on the
   HITRAN site).
3. Note whether any of them are closer to typical hot-Jupiter/warm-Neptune
   transmission-spectroscopy conditions (very roughly: pressures around
   1 millibar to 1 bar, temperatures very roughly 500-2000 K depending on
   the planet) than the room-temperature/1-atm dataset already downloaded.

## What NOT to do

- Do not guess or estimate what conditions "should" exist based on general
  spectroscopy knowledge -- report only what you actually find listed on
  the real HITRAN site for these five specific molecules.
- Do not download anything yet -- I just need the inventory of what's
  available and at what conditions, so I can decide whether it's worth
  downloading before doing so.
- If a gas has only the single room-temperature/1-atm dataset already
  downloaded and nothing else, say so plainly rather than implying more
  exists.
