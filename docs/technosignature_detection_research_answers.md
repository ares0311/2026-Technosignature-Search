# Technosignature Detection Research Answers

Date: 2026-07-03

Scope: Answers to four verification questions for atmospheric technosignature detection. This file only states values that were verified from accessible source text, live MAST/HITRAN queries, or downloaded HITRAN cross-section files. Where the original paper does not provide a literal table, that is stated explicitly.

## Executive Summary

| Question | Status | Answer |
|---|---:|---|
| Q1 Schwieterman et al. 2024 details | Partly verified; no paper table exists | The paper does not publish or use a complete numeric table of mid-IR band centers for all five gases. It models continuous cross sections from Sharpe et al. 2004 via Kochanov et al. 2019. The exact peak centers below were computed from corresponding HITRAN/Sharpe cross-section files downloaded on 2026-07-03 and must not be misquoted as a table copied from Schwieterman et al. |
| Q2 C3F8 strongest band | Verified | In the downloaded HITRAN/Sharpe C3F8 cross section, the global maximum is at `1262.065573 cm^-1`, equivalent to `7.923519 um`. |
| Q3 N2O secondary feature | Verified | HITRAN line data show a real separated N2O feature near `1181.779840 cm^-1` / `8.461813 um`, but it is much weaker than the main 7.5-8.1 um band. |
| Q4 MAST JWST MIRI LRS strings | Verified | MAST `instrument_name` values are `MIRI/SLIT` and `MIRI/SLITLESS`; `MIRI/LRS`, `MIRI/SLITLESSPRISM`, and `MIRI/LRS-FIXEDSLIT` returned zero results. `P750L` appears in `filters`, confirming LRS prism observations under those two names. |

## Sources Used

- Schwieterman et al. 2024, ["Artificial Greenhouse Gases as Exoplanet Technosignatures"](https://arxiv.org/abs/2405.11149), The Astrophysical Journal 969:20, arXiv:2405.11149, DOI `10.3847/1538-4357/ad4ce8`.
- HITRAN absorption cross-section search and cross-section definitions: [HITRAN xsc search](https://hitran.org/xsc/) and [HITRAN cross-section definitions](https://hitran.org/docs/cross-sections-definitions/).
- HAPI/HITRAN citation: Kochanov et al. 2016, ["HITRAN Application Programming Interface (HAPI): A comprehensive approach to working with spectroscopic data"](https://doi.org/10.1016/j.jqsrt.2016.03.005), JQSRT 177, 15-30.
- Sharpe et al. 2004, ["Gas-Phase Databases for Quantitative Infrared Spectroscopy"](https://doi.org/10.1366/0003702042641281), Applied Spectroscopy 58, 1452-1461.
- Kochanov et al. 2019, ["HITRAN Application Programming Interface (HAPI): An integrated approach to working with spectroscopic data"](https://doi.org/10.1016/j.jqsrt.2019.04.032), JQSRT 230, 172-221.
- STScI MAST JWST instrument-name documentation: [JWST Instrument Names](https://outerspace.stsci.edu/spaces/MASTDOCS/pages/176435458/JWST+Instrument+Names).
- astroquery MAST observation-query documentation: [Observation Queries](https://astroquery.readthedocs.io/en/stable/mast/mast_obsquery.html).
- Burch & Williams 1962, ["Total Absorptance by Nitrous Oxide Bands in the Infrared"](https://doi.org/10.1364/AO.1.000473), Applied Optics 1(4), 473-482.

## Question 1 - Schwieterman et al. 2024 Details

### Paper Identification

Schwieterman et al. 2024 is:

- Title: "Artificial Greenhouse Gases as Exoplanet Technosignatures"
- Journal: The Astrophysical Journal
- Volume/page: `969:20`
- Published: 2024 July 1
- arXiv: `2405.11149`
- DOI: `10.3847/1538-4357/ad4ce8`

Citation: Schwieterman et al. 2024, ["Artificial Greenhouse Gases as Exoplanet Technosignatures"](https://arxiv.org/abs/2405.11149).

### Important Caveat: No Literal Published Table of All Band Centers

The paper contains Figure 1 showing IR cross sections for `CF4`, `C2F6`, `C3F8`, `SF6`, and `NF3`, and prose describing key features. It does not contain a standalone numeric table listing exact band centers for all five gases.

The paper also does not state that the authors used a band-center table for modeling. It states that they used absorption cross sections. Therefore, the table below is not claimed to be a table copied from Schwieterman et al. or an exact table the authors used. It is a reproducible peak extraction from the same cited source family: HITRAN cross sections sourced from Sharpe et al. 2004 via Kochanov et al. 2019.

### Audit Against Original Question

| Requested item | No-guessing status | What this report provides |
|---|---:|---|
| Retrieve full paper text | Done | arXiv/ApJ text was read and cited by title, DOI, journal, and arXiv ID. |
| Exact table of mid-IR absorption band centers used by authors | Not present in paper | The paper used continuous cross sections, not a published band-center table. This report provides a computed peak table from matching HITRAN/Sharpe cross-section files and explicitly labels it as computed, not copied. |
| Absorption cross-section data sources cited | Done | Sharpe et al. 2004 via Kochanov et al. 2019; HITRAN line lists for ordinary molecules in SMART except artificial-gas cross sections. |
| Exact telescope/instrument combinations per gas | Done | MIRI LRS for all five gases and the `C2F6 + C3F8 + SF6` combination; NIRSpec only for `C2F6`, `C3F8`, `SF6`, and their combination; LIFE/LIFESIM for all five and combinations. |
| Detection significance / observation-time methodology | Done | PSG/PandExo transit S/N workflow, 1.17 out-of-transit factor, 5 sigma transit calculation, and LIFE band-integrated S/N definition. |

### Cross-Section Files Downloaded from HITRAN

Downloaded on 2026-07-03 through HITRAN cross-section search.

Citation: HITRAN cross-section interface and file-format definitions, [HITRAN xsc search](https://hitran.org/xsc/) and [HITRAN cross-section definitions](https://hitran.org/docs/cross-sections-definitions/). The source family used here is the same one Schwieterman et al. cite: Sharpe et al. 2004 via Kochanov et al. 2019.

| Gas | HITRAN common name | HITRAN molecule ID | HITRAN cross-section ID | Downloaded file |
|---|---:|---:|---:|---|
| `CF4` | `PFC-14` | `42` | `2827` | `CF4_298.1K-760.0Torr_570.0-6500.0_0.11_N2_207_43.xsc` |
| `C2F6` | `PFC-116` | `107` | `2885` | `C2F6_298.1K-760.0Torr_500.0-6500.0_0.11_N2_197_43.xsc` |
| `C3F8` | `PFC-218` | `401` | `2906` | `C3F8_298.1K-760.0Torr_600.0-6500.0_0.11_N2_208_43.xsc` |
| `SF6` | `Sulfur Hexafluoride` | `30` | `3032` | `SF6_298.1K-760.0Torr_560.0-6500.0_0.11_N2_220_43.xsc` |
| `NF3` | `Nitrogen Trifluoride` | `55` | `2987` | `NF3_298.1K-760.0Torr_600.0-6500.0_0.11_N2_186_43.xsc` |

### Extracted Peak Centers from Downloaded HITRAN/Sharpe Cross Sections

Peak criterion used: local maxima at least `2%` of each molecule's global maximum, separated by at least `20 cm^-1`. Values are from the downloaded `.xsc` grids.

| Gas | Peak wavenumber `cm^-1` | Wavelength `um` | Relative strength |
|---|---:|---:|---:|
| `CF4` | `1283.213506` | `7.792935` | `1.000` |
| `CF4` | `631.211562` | `15.842549` | `0.031` |
| `C2F6` | `1249.585915` | `8.002651` | `1.000` |
| `C2F6` | `1115.979454` | `8.960738` | `0.337` |
| `C2F6` | `713.653456` | `14.012403` | `0.139` |
| `C3F8` | `1262.065573` | `7.923519` | `1.000` |
| `C3F8` | `1007.024909` | `9.930241` | `0.203` |
| `C3F8` | `1154.372362` | `8.662716` | `0.170` |
| `C3F8` | `730.831297` | `13.683048` | `0.131` |
| `C3F8` | `1209.695456` | `8.266543` | `0.115` |
| `C3F8` | `1350.353516` | `7.405468` | `0.091` |
| `C3F8` | `1298.103928` | `7.703543` | `0.024` |
| `C3F8` | `1319.377405` | `7.579332` | `0.022` |
| `SF6` | `947.905963` | `10.549570` | `1.000` |
| `SF6` | `614.942647` | `16.261679` | `0.212` |
| `NF3` | `909.513125` | `10.994894` | `1.000` |
| `NF3` | `1031.970650` | `9.690198` | `0.328` |
| `NF3` | `889.505301` | `11.242204` | `0.154` |
| `NF3` | `929.581214` | `10.757532` | `0.036` |
| `NF3` | `1011.842297` | `9.882963` | `0.031` |

### Schwieterman Prose Band Mentions

The paper's prose states:

- `CF4`: strongest feature near `~7.9 um`; additional significant features at `5.25`, `5.9`, `6.5`, and `9.2 um`.
- `C2F6` and `C3F8`: numerous features throughout the MIR; much stronger absorption at `8-9 um`.
- `C3F8`: additional strong feature near `~9.9 um`.
- `SF6`: strongest feature near `~10.7 um`; weaker features at `5.8`, `6.3`, `6.9`, `7.2`, `8.0`, `8.8`, and `11.4 um`.
- `NF3`: strongest feature near `11 um`; weaker features at `5.2`, `5.6`, `6.5`, `7.2`, `8.8`, and `9.8 um`.

These prose values agree at first-order with the downloaded cross-section maxima above, allowing for broad bands, grid choice, and the fact that this report used one representative `298.1 K`, `760 Torr`, `N2` broadening dataset for each gas.

### Cross-Section Data Sources Cited by Schwieterman

Schwieterman et al. state that the opacities for the five artificial gases were sourced from:

- Sharpe et al. 2004 via Kochanov et al. 2019.
- They note that only cross sections, not line-by-line data, are available for these artificial gases, and that the data are limited in wavelength coverage and precision.

For normal atmospheric molecules in SMART emission simulations, Schwieterman et al. state that SMART uses HITRAN line lists via LBLABC, except for the artificial-gas cross-section data described above.

Citations: Schwieterman et al. 2024, [arXiv:2405.11149](https://arxiv.org/abs/2405.11149); Sharpe et al. 2004, [DOI `10.1366/0003702042641281`](https://doi.org/10.1366/0003702042641281); Kochanov et al. 2019, [DOI `10.1016/j.jqsrt.2019.04.032`](https://doi.org/10.1016/j.jqsrt.2019.04.032).

### Telescope / Instrument Combinations Modeled

Schwieterman et al. modeled:

| Use case | Instrument / model | Wavelength range / setup | Gases |
|---|---|---|---|
| Transmission spectra, MIR | JWST MIRI LRS | `5-12 um`, assumed `R = 100`, P750L disperser, SLITLESSPRISM subarray, FASTR1 readout, 20 groups/integration | `CF4`, `C2F6`, `C3F8`, `SF6`, `NF3`, and `C2F6 + C3F8 + SF6` combination |
| Transmission spectra, NIR | JWST NIRSpec prism | `1.5-5 um`, constant spectral resolution `0.022 um`; SUB512S, rapid readout, 2 groups/integration | `C2F6`, `C3F8`, `SF6`, and combination of those three. The paper's NIR detectability table does not include `CF4` or `NF3`. |
| Emission spectra / direct imaging | LIFE / LIFESIM concept | `4-18.5 um`, spectral resolution `R = 50`, four 2 m apertures, 5% throughput, baseline 10-100 m | `CF4`, `C2F6`, `C3F8`, `SF6`, `NF3`, and combinations |

### Detection Significance / Observation Time Methodology

For JWST transmission detectability, the paper describes this procedure:

1. Compute a spectrum without the molecule of interest.
2. Compute a spectrum with the molecule of interest.
3. Compute the difference across the whole instrument range.
4. Divide by one-transit noise in each spectral interval.
5. Apply an out-of-transit factor of `1.17`, assuming out-of-transit time equals 3 times in-transit time.
6. Compute total molecular S/N across the whole instrument range following Lustig-Yaeger et al. 2019.
7. Convert S/N to number of transits required for a `5 sigma` detection following Fauchez et al. 2019/2020.

For LIFE/LIFESIM direct-imaging detectability, the paper reports:

- Maximum difference in one band in units of sigma.
- Band-integrated S/N:

```text
S/N_band = sqrt(sum_i (Delta y_i / sigma(y_i))^2)
```

where `Delta y_i` is the difference between spectra with and without the technosignature feature in each spectral bin, and `sigma(y_i)` is the LIFE sensitivity in that bin.

### JWST MIRI LRS 5 Sigma Transit Counts from Schwieterman Table 3

| Atmosphere | 100 ppm | 10 ppm | 1 ppm |
|---|---:|---:|---:|
| `C2F6 + C3F8 + SF6` | `5` | `10` | `25` |
| `C2F6` | `6` | `13` | `38` |
| `C3F8` | `8` | `20` | `60` |
| `SF6` | `19` | `57` | `>100` |
| `NF3` | `16` | `52` | `>100` |

### JWST NIRSpec 5 Sigma Transit Counts from Schwieterman Table 4

| Atmosphere | 100 ppm | 10 ppm | 1 ppm |
|---|---:|---:|---:|
| `C2F6 + C3F8 + SF6` | `4` | `14` | `80` |
| `C2F6` | `36` | `>100` | `>100` |
| `C3F8` | `41` | `83` | `>100` |
| `SF6` | `>100` | `>100` | `>100` |

## Question 2 - Real Strongest Mid-IR Absorption Band of C3F8

### Verified Answer

Using the downloaded HITRAN/Sharpe cross-section file:

```text
C3F8_298.1K-760.0Torr_600.0-6500.0_0.11_N2_208_43.xsc
```

the global maximum is:

```text
1262.065573 cm^-1
7.923519 um
sigma = 1.145000e-17 cm^2/molecule
```

This is the strongest documented band in that downloaded gas-phase cross-section file.

Citation: HITRAN cross-section file downloaded from [HITRAN xsc search](https://hitran.org/xsc/) for `PFC-218` / `C3F8`, dataset ID `2906`, source reference Sharpe et al. 2004, [DOI `10.1366/0003702042641281`](https://doi.org/10.1366/0003702042641281).

### Additional C3F8 Peaks from Same File

| Wavenumber `cm^-1` | Wavelength `um` | Relative strength |
|---:|---:|---:|
| `1262.065573` | `7.923519` | `1.000` |
| `1007.024909` | `9.930241` | `0.203` |
| `1154.372362` | `8.662716` | `0.170` |
| `730.831297` | `13.683048` | `0.131` |
| `1209.695456` | `8.266543` | `0.115` |
| `1350.353516` | `7.405468` | `0.091` |
| `1298.103928` | `7.703543` | `0.024` |
| `1319.377405` | `7.579332` | `0.022` |

### Note on Other C3F8 Source Located

An Australian industrial chemicals public report for perfluoropropane lists IR maximum absorbance at:

```text
1010, 1150, 1220, 1280 cm^-1
```

That source verifies multiple maxima but does not rank a single strongest peak. The HITRAN/Sharpe cross-section file above supplies the ranked numerical maximum.

## Question 3 - Additional Infrared Absorption Bands of N2O in 5-14 um

### Verified HITRAN Query

HAPI/HITRAN query run locally:

```python
from hapi import *
db_begin("hitran_n2o")
fetch("N2O_main_700_2000", 4, 1, 700, 2000)
```

This returned `54049` HITRAN lines for the main N2O isotopologue over `700-2000 cm^-1`.

Citation: HITRAN/HAPI line-list query using HAPI; cite Kochanov et al. 2016, [DOI `10.1016/j.jqsrt.2016.03.005`](https://doi.org/10.1016/j.jqsrt.2016.03.005).

### Main Result

The strongest HITRAN lines in this range are all in the known 7.8 um region. The strongest line found was:

```text
nu = 1297.831450 cm^-1
wavelength = 7.705161 um
sw = 1.721000e-19
```

### Separated Feature Outside 7.5-8.1 um

After excluding `7.5-8.1 um`, the strongest separated HITRAN line found was:

```text
nu = 1181.779840 cm^-1
wavelength = 8.461813 um
sw = 5.766000e-21
```

Nearby separated lines cluster around roughly `8.4-8.7 um`.

### Band-Window Strength Comparison

| Window `um` | Lines | Total line strength | Max line strength |
|---:|---:|---:|---:|
| `5.0-6.0` | `15292` | `2.709707e-20` | `4.018000e-22` |
| `6.0-7.0` | `6471` | `2.786001e-21` | `4.488000e-23` |
| `7.0-7.5` | `2442` | `2.086808e-21` | `1.150000e-22` |
| `7.5-8.1` | `10605` | `9.673533e-18` | `1.721000e-19` |
| `8.1-9.0` | `9844` | `3.589333e-19` | `5.766000e-21` |
| `9.0-10.0` | `3256` | `4.287777e-22` | `6.584000e-24` |
| `10.0-11.0` | `1343` | `2.059887e-21` | `4.058000e-23` |
| `11.0-12.0` | `1645` | `1.819728e-22` | `1.210000e-23` |
| `12.0-13.0` | `114` | `1.692000e-26` | `2.754000e-28` |
| `13.0-14.0` | `1985` | `5.137903e-22` | `3.298000e-23` |

The `8.1-9.0 um` region has:

```text
3.589333e-19 / 9.673533e-18 = 0.0371
```

or about `3.7%` of the total line strength of the main `7.5-8.1 um` region.

### Answer

Yes, N2O has real documented HITRAN absorption lines outside the 7.8 um band within the `5-14 um` instrument range. The most useful separated cluster is around `8.46 um` / `1182 cm^-1`. However, this feature is far weaker than the main 7.8 um band. It may help distinguish N2O from CF4 only with sufficient SNR and spectral treatment; it should not be treated as an equal-strength backup diagnostic.

## Question 4 - MAST JWST MIRI LRS `instrument_name` Values

### Verified astroquery Counts

Local astroquery command:

```python
from astroquery.mast import Observations
Observations.TIMEOUT = 60

names = [
    "MIRI",
    "MIRI*",
    "MIRI/SLIT",
    "MIRI/SLITLESS",
    "MIRI/LRS",
    "MIRI/SLITLESSPRISM",
    "MIRI/LRS-FIXEDSLIT",
]

for name in names:
    n = Observations.query_criteria_count(
        obs_collection="JWST",
        instrument_name=name
    )
    print(f"{name}: {n}")
```

Output:

```text
MIRI: 0
MIRI*: 69594
MIRI/SLIT: 1526
MIRI/SLITLESS: 742
MIRI/LRS: 0
MIRI/SLITLESSPRISM: 0
MIRI/LRS-FIXEDSLIT: 0
```

Citations: STScI [JWST Instrument Names](https://outerspace.stsci.edu/spaces/MASTDOCS/pages/176435458/JWST+Instrument+Names) and astroquery [Observation Queries](https://astroquery.readthedocs.io/en/stable/mast/mast_obsquery.html).

### Verified Distinct `instrument_name` Values

```text
MIRI/SLIT
MIRI/SLITLESS
```

### Verified `filters` Values Include `P750L`

For `MIRI/SLIT`, `filters` included:

```text
--
F1000W
F1500W
F560W
F770W
FND
P750L
```

For `MIRI/SLITLESS`, `filters` included:

```text
--
F1000W
F1500W
F560W
F770W
FND
OPAQUE
P750L
```

### Answer

For `astroquery.mast.Observations.query_criteria()` searches of JWST MIRI LRS data, use:

```python
instrument_name="MIRI/SLIT"
instrument_name="MIRI/SLITLESS"
```

and filter/inspect for:

```python
filters="P750L"
```

Do not use these as `instrument_name` filters:

```text
MIRI/LRS
MIRI/SLITLESSPRISM
MIRI/LRS-FIXEDSLIT
```

They returned zero results in the verified query.

## Reproducibility Notes for Coding Agent

### Credential Handling

A free HITRAN account is required to download the cross-section `.xsc` files through the authenticated HITRAN web interface. Do not write HITRAN credentials into this Markdown file, source code, shell history, `.env` files, notebooks, commits, issue comments, or logs.

Use an interactive local prompt with `getpass.getpass()` when terminal automation is needed. The password should only be typed into the local terminal prompt and should never be printed.

Example safe pattern:

```python
import getpass

email = input("HITRAN email: ")
password = getpass.getpass("HITRAN password: ")
```

Browser login cookies do not automatically transfer to Python `requests.Session()`. To reproduce the authenticated downloads in terminal, log in inside the same Python `requests.Session()` and preserve its CSRF/session cookies for subsequent HITRAN requests.

### End-to-End Reproduction Checklist

1. Install dependencies in the active project environment:

```bash
python -m pip install astroquery astropy hitran-api beautifulsoup4 requests certifi
```

2. If Python certificate verification fails on macOS, update `certifi` and export the cert path:

```bash
python -m pip install --upgrade certifi
export SSL_CERT_FILE="$(python -m certifi)"
export REQUESTS_CA_BUNDLE="$(python -m certifi)"
```

3. Verify MAST MIRI LRS `instrument_name` values with `astroquery`.
4. Query HITRAN N2O line data with HAPI over `700-2000 cm^-1`.
5. Log into HITRAN in a local Python `requests.Session()` using interactive credential prompts.
6. Download the five `.xsc` files using the HITRAN cross-section dataset IDs below.
7. Parse the `.xsc` files using the peak-extraction script below.
8. Do not commit `hitran_n2o/`, `hitran_xsc_probe/`, or `hitran_xsc_downloads/` unless the project intentionally tracks raw spectroscopy data.

### HITRAN Cross-Section Dataset IDs

Use these IDs to retrieve the same files:

```text
C3F8 / PFC-218: 2906
CF4 / PFC-14: 2827
C2F6 / PFC-116: 2885
NF3: 2987
SF6: 3032
```

The corresponding HITRAN molecule IDs are:

```text
C3F8 / PFC-218: 401
CF4 / PFC-14: 42
C2F6 / PFC-116: 107
NF3: 55
SF6: 30
```

### Peak Extraction Script

```python
from pathlib import Path

def parse_xsc(path: Path):
    lines = path.read_text(errors="replace").splitlines()
    header = lines[0]
    parts = header.split()
    species = parts[0]
    numin = float(parts[1])
    numax = float(parts[2])
    npts = int(parts[3])

    values = []
    for line in lines[1:]:
        for tok in line.split():
            try:
                values.append(float(tok))
            except ValueError:
                pass

    values = values[:npts]
    step = (numax - numin) / (npts - 1)
    wn = [numin + i * step for i in range(npts)]
    return species, header, wn, values

def local_peaks(wn, y, min_rel=0.02, min_sep_cm=20.0):
    ymax = max(y)
    candidates = []
    for i in range(1, len(y) - 1):
        if y[i] >= y[i-1] and y[i] >= y[i+1] and y[i] >= min_rel * ymax:
            candidates.append((wn[i], y[i]))

    candidates.sort(key=lambda p: p[1], reverse=True)
    kept = []
    for w, v in candidates:
        if all(abs(w - wk) >= min_sep_cm for wk, _ in kept):
            kept.append((w, v))
    return kept
```

### Local Scratch Files Not to Commit

The following local folders/files are generated scratch data unless the project intentionally tracks downloaded spectroscopic data:

```text
hitran_n2o/
hitran_xsc_probe/
hitran_xsc_downloads/
```

Recommended `.gitignore` entries:

```text
# Local HITRAN scratch data
hitran_n2o/
hitran_xsc_probe/
hitran_xsc_downloads/
```
