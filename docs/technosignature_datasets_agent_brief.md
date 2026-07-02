# Technosignature Dataset Handoff for Coding Agent

## Objective

Build a practical training and candidate-vetting corpus for an AI system that searches for possible radio technosignature candidates. Do **not** train a binary "alien vs not alien" classifier. There are no confirmed positive alien technosignature labels.

The agreed first milestone is a **Track A working classifier** for known explanations. Track B anomaly/candidate ranking comes later.

Track A:

1. Classify known explanations: pulsars, FRBs, blazars/AGN, known gamma-ray sources, satellites, terrestrial RFI, instrument artifacts, and noise.
2. Use tabular features, catalog cross-matches, and small extracted hit/candidate tables first.
3. Produce `low_confidence` when no known class is reliable.

Track B:

1. Search real SETI observations for events that do not fit known classes.
2. Emit `unknown_candidate` only after known-source, RFI, satellite, cadence, and instrument checks fail.
3. Treat `unknown_candidate` as a triage label, not a discovery claim.

Do not start Track B until Track A has a tested, reproducible baseline.

## Operational Constraints

These are hard constraints unless the user explicitly approves a change.

```text
Max local disk use for raw data + temp files + training cache: about 100 GB.
Machine free-space context: about 400 GB free, but do not use it all.
No synthetic data for training.
No pretrained model dependency for the first milestone.
No large Breakthrough Listen raw-data sweep for the first milestone.
Delete raw downloaded training data and temporary extraction products after training/evaluation.
Preserve model artifacts, feature schemas, manifests, hashes, metrics, code, and a small golden validation set.
```

For every pipeline step that downloads or materializes data, estimate expected disk use before running. If expected disk use could exceed 100 GB at any one time, stop and ask the user.

After training, keep only:

```text
models/
metrics/
manifests/
schemas/
feature_generation_code/
small_golden_validation_set/
```

Do not keep:

```text
large raw HDF5/FILTERBANK/baseband downloads
temporary spectrogram patches
temporary decompressed archives
throwaway training caches
```

## Recommended Label Taxonomy

```text
pulsar
frb
blazar_agn
known_gamma_source
satellite_transmitter
terrestrial_rfi
instrument_artifact
noise
low_confidence
unknown_candidate
```

`unknown_candidate` is reserved for Track B. Track A should normally emit a known class or `low_confidence`.

Do not use `synthetic_injection` in training because the user has explicitly selected **no synthetic data**. Keep a `synthetic_flag` in schemas only to prevent accidental mixing if a future agent encounters synthetic data.

## Dataset Stack

Use the first group for the first milestone. Treat the later groups as references or future work.

| Priority | Dataset | Track | Size | Purpose | Auth/API Key | Format |
|---:|---|---|---:|---|---|---|
| 1 | [HTRU2 Pulsar Candidates](https://archive-beta.ics.uci.edu/dataset/372/htru2) | A | 17,898 rows | Clean supervised starter set: pulsar vs RFI/noise | No | CSV / ARFF |
| 2 | [ATNF Pulsar Catalog via HEASARC](https://heasarc.gsfc.nasa.gov/W3Browse/all/atnfpulsar.html) | A | Dynamic catalog | Known pulsar cross-match catalog | No | HEASARC table/API |
| 3 | [CHIME/FRB Catalog 1](https://doi.org/10.3847/1538-4365/ac33ab) | A | 536 bursts | Known FRB labels and repeater/non-repeater metadata | No | Published tables |
| 4 | [Roma-BZCAT Blazar Catalog](https://catalog.data.gov/dataset/roma-bzcat-multi-frequency-catalog-of-blazars) | A | 3,561 sources | Blazar/AGN cross-match catalog | No | HEASARC table/API |
| 5 | [Fermi LAT 4FGL-DR4](https://fermi.gsfc.nasa.gov/ssc/data/access/lat/14yr_catalog/) | A | 7,194 sources | Gamma-ray source classes and associations | No | FITS / XML / HEASARC table |
| 6 | [CelesTrak SATCAT](https://celestrak.org/satcat/) | A | 34,081 total tracked objects as of 2026-07-01 | Satellite/debris/orbital-object rejection | No | CSV / text / GP data |
| 7 | [SatNOGS DB API](https://docs.satnogs.org/projects/satnogs-db/en/latest/api.html) | A | Dynamic catalog | Satellite transmitter frequencies, modes, TLE, telemetry metadata | No key for public reads. Key only for protected/write calls. | REST JSON |
| 8 | [ML_GBT_SETI](https://github.com/PetchMa/ML_GBT_SETI) | Reference | 820 targets / 480+ hours in paper | Published ML workflow reference only | No | Code + target/candidate data |
| 9 | [Breakthrough Listen Data Release 1](https://seti.berkeley.edu/listen2019/overview.html) | B later | Almost 1 PB public release; 1327-star data products also reported as about 219 TB | Real SETI observations and ON/OFF cadence search substrate | No | HDF5 / FILTERBANK / raw |
| 10 | [Breakthrough Listen Open Data Archive](https://seti.berkeley.edu/opendata) | B later | Variable; individual files can be multiple GB | Main public SETI data archive | No | HDF5 / FILTERBANK / FITS / baseband |
| Excluded | [Kaggle SETI Breakthrough Listen](https://www.kaggle.com/competitions/seti-breakthrough-listen) | Excluded for now | Large competition dataset | Synthetic/injected signal benchmark only | Yes for CLI download | NPZ / CSV labels |
| Excluded | [Setigen](https://arxiv.org/abs/2203.09668) | Excluded for now | Generated/arbitrary | Synthetic signal injection/recovery tests only | No | Python package |

Do not download the excluded datasets. They are listed only to prevent future confusion.

## Resource Acquisition Checklist

Run Phase 0 disk/provenance guards before using this checklist. Save every acquired file under `data_cache/raw/<source_name>/` and record it in `artifacts/manifests/data_manifest.jsonl`.

Do not improvise alternate sources if a command fails. Use the fallback listed for that source, then stop and ask the user if the fallback fails.

### Acquisition Summary

| Source | First Method | Save As | Expected Size | Fallback | Track A? |
|---|---|---|---:|---|---|
| HTRU2 | `ucimlrepo.fetch_ucirepo(id=372)` | `data_cache/raw/htru2/htru2_features.parquet`, `htru2_labels.parquet` | Small, ~MB scale | UCI page manual CSV/ARFF download | Yes |
| ATNF Pulsars | `psrqpy.QueryATNF(...)` | `data_cache/raw/atnf/atnf_pulsars.parquet` | Small, MB scale | HEASARC table page | Yes |
| CHIME/FRB Catalog 1 | VizieR `J/ApJS/257/59/table2` via `astroquery.vizier` | `data_cache/raw/chime_frb/chime_frb_catalog1.parquet` | Small, MB scale | VizieR TSV URL | Yes |
| Roma-BZCAT | VizieR `VII/274/bzcat5` via `astroquery.vizier` | `data_cache/raw/romabzcat/romabzcat.parquet` | Small, MB scale | HEASARC `romabzcat` table | Yes |
| Fermi 4FGL-DR4 | Direct FSSC FITS URL | `data_cache/raw/fermi_4fgl_dr4/gll_psc_v32.fit` and converted parquet | Small/medium, MB scale | FSSC catalog page manual FITS link | Yes |
| CelesTrak SATCAT | `records.php?FORMAT=CSV` | `data_cache/raw/celestrak/satcat.csv` | Small, MB scale | CelesTrak SATCAT page raw CSV link | Yes |
| CelesTrak active GP | `gp.php?GROUP=active&FORMAT=json` | `data_cache/raw/celestrak/gp_active.json` | Small/medium, MB scale | Use only SATCAT until GP access is fixed | Yes |
| SatNOGS satellites/transmitters/TLE | Public REST API endpoints | JSONL/Parquet under `data_cache/raw/satnogs/` | Small/medium, MB scale | Stop and ask if API pagination/auth blocks public reads | Yes |
| ML_GBT_SETI | `git clone --depth 1` metadata/code only | `data_cache/raw/ml_gbt_seti/` | Small if repo only | Project page | Reference only |
| Breakthrough Listen | Do not download for Track A | None | Can exceed GB/TB quickly | Ask user before any BL raw data download | No, later |
| Kaggle SETI | Do not download | None | Large | None; excluded | No |
| Setigen | Do not install/use | None | Generated | None; excluded | No |

### Shared Acquisition Script Skeleton

The coding agent should implement one acquisition script per source or a single CLI with source subcommands. Each acquisition must:

```text
1. Check current size of data_cache/ + tmp_training/ + tmp_features/.
2. Estimate new download size where possible.
3. Stop if total raw/temp/cache use could approach 100 GB.
4. Download or query the resource.
5. Save raw copy and normalized parquet/CSV copy.
6. Write one manifest JSONL record per raw and normalized file.
7. Validate row count and required columns.
```

Suggested manifest record:

```json
{
  "source_name": "htru2",
  "source_url": "https://archive-beta.ics.uci.edu/dataset/372/htru2",
  "access_method": "ucimlrepo.fetch_ucirepo(id=372)",
  "downloaded_at_utc": "YYYY-MM-DDTHH:MM:SSZ",
  "local_path": "data_cache/raw/htru2/htru2_features.parquet",
  "file_size_bytes": 0,
  "sha256": "optional_but_preferred",
  "row_count": 17898,
  "auth_required": false,
  "license_or_terms": "CC BY 4.0",
  "notes": ""
}
```

### HTRU2 Acquisition

Use this first. Do not scrape the web page.

```bash
pip install ucimlrepo pandas pyarrow scikit-learn
```

```python
from pathlib import Path
from ucimlrepo import fetch_ucirepo

out = Path("data_cache/raw/htru2")
out.mkdir(parents=True, exist_ok=True)

htru2 = fetch_ucirepo(id=372)
X = htru2.data.features
y = htru2.data.targets

assert len(X) == 17898
assert "class" in y.columns

X.to_parquet(out / "htru2_features.parquet", index=False)
y.to_parquet(out / "htru2_labels.parquet", index=False)
```

Required columns:

```text
Profile_mean
Profile_stdev
Profile_skewness
Profile_kurtosis
DM_mean
DM_stdev
DM_skewness
DM_kurtosis
class
```

### ATNF Pulsar Acquisition

Use `psrqpy`. Do not manually scrape the ATNF or HEASARC pages.

```bash
pip install psrqpy pandas pyarrow astropy
```

```python
from pathlib import Path
from psrqpy import QueryATNF

out = Path("data_cache/raw/atnf")
out.mkdir(parents=True, exist_ok=True)

params = ["PSRJ", "RAJ", "DECJ", "P0", "P1", "DM", "BINARY", "DIST"]
query = QueryATNF(params=params)
table = query.table
df = table.to_pandas()

assert len(df) > 1000
df.to_parquet(out / "atnf_pulsars.parquet", index=False)
```

Fallback if `psrqpy` fails:

```text
Use HEASARC table page only to diagnose access:
https://heasarc.gsfc.nasa.gov/W3Browse/all/atnfpulsar.html
Do not invent a scraper. Stop and ask the user if programmatic access remains blocked.
```

### CHIME/FRB Catalog 1 Acquisition

Use VizieR catalog `J/ApJS/257/59`, table `table2`.

```bash
pip install astroquery pandas pyarrow astropy
```

```python
from pathlib import Path
from astroquery.vizier import Vizier

out = Path("data_cache/raw/chime_frb")
out.mkdir(parents=True, exist_ok=True)

Vizier.ROW_LIMIT = -1
tables = Vizier.get_catalogs("J/ApJS/257/59")
table = tables["J/ApJS/257/59/table2"]
df = table.to_pandas()

assert len(df) >= 536
df.to_parquet(out / "chime_frb_catalog1.parquet", index=False)
```

Fallback TSV URL:

```text
https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=J/ApJS/257/59/table2
```

Expected VizieR table note: the table can contain about 600 rows due to component/sub-burst representation, while the paper describes 536 bursts. Preserve the table as provided and document the row count in the manifest.

### Roma-BZCAT Acquisition

Use VizieR catalog `VII/274`, table `bzcat5`.

```bash
pip install astroquery pandas pyarrow astropy
```

```python
from pathlib import Path
from astroquery.vizier import Vizier

out = Path("data_cache/raw/romabzcat")
out.mkdir(parents=True, exist_ok=True)

Vizier.ROW_LIMIT = -1
tables = Vizier.get_catalogs("VII/274")
table = tables["VII/274/bzcat5"]
df = table.to_pandas()

assert len(df) == 3561
df.to_parquet(out / "romabzcat.parquet", index=False)
```

Fallback TSV URL:

```text
https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=VII/274/bzcat5
```

### Fermi LAT 4FGL-DR4 Acquisition

Use the direct FITS file from FSSC.

```bash
pip install requests astropy pandas pyarrow
```

```python
from pathlib import Path
import requests
from astropy.table import Table

out = Path("data_cache/raw/fermi_4fgl_dr4")
out.mkdir(parents=True, exist_ok=True)

url = "https://fermi.gsfc.nasa.gov/ssc/data/access/lat/14yr_catalog/gll_psc_v32.fit"
fits_path = out / "gll_psc_v32.fit"

r = requests.get(url, timeout=120)
r.raise_for_status()
fits_path.write_bytes(r.content)

tbl = Table.read(fits_path)
df = tbl.to_pandas()

assert len(df) == 7194
df.to_parquet(out / "fermi_4fgl_dr4.parquet", index=False)
```

Fallback:

```text
Open the FSSC catalog page and use the current FITS link if the filename changed:
https://fermi.gsfc.nasa.gov/ssc/data/access/lat/14yr_catalog/
Do not use an older 4FGL release unless the user approves.
```

### CelesTrak Acquisition

Use CSV/JSON endpoints. Do not use legacy fixed-width text.

```bash
pip install requests pandas pyarrow
```

```python
from pathlib import Path
import requests
import pandas as pd

out = Path("data_cache/raw/celestrak")
out.mkdir(parents=True, exist_ok=True)

satcat_url = "https://celestrak.org/satcat/records.php?FORMAT=CSV"
satcat_path = out / "satcat.csv"
r = requests.get(satcat_url, timeout=120)
r.raise_for_status()
satcat_path.write_bytes(r.content)
satcat = pd.read_csv(satcat_path)
assert len(satcat) > 30000
satcat.to_parquet(out / "satcat.parquet", index=False)

gp_url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=json"
gp_path = out / "gp_active.json"
r = requests.get(gp_url, timeout=120)
r.raise_for_status()
gp_path.write_bytes(r.content)
gp = pd.read_json(gp_path)
assert len(gp) > 10000
gp.to_parquet(out / "gp_active.parquet", index=False)
```

Fallback:

```text
If active GP download fails, keep SATCAT and skip propagation until GP access is fixed.
Do not switch to random third-party satellite mirrors.
```

### SatNOGS Acquisition

Use public API reads only. Do not create an API key or write to SatNOGS.

```bash
pip install requests pandas pyarrow
```

```python
from pathlib import Path
import requests
import pandas as pd

out = Path("data_cache/raw/satnogs")
out.mkdir(parents=True, exist_ok=True)

def fetch_paginated(endpoint: str):
    url = f"https://db.satnogs.org/api/{endpoint}/"
    rows = []
    while url:
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        payload = r.json()
        if isinstance(payload, dict) and "results" in payload:
            rows.extend(payload["results"])
            url = payload.get("next")
        elif isinstance(payload, list):
            rows.extend(payload)
            url = None
        else:
            raise RuntimeError(f"Unexpected SatNOGS payload for {endpoint}")
    return rows

for endpoint in ["satellites", "transmitters", "tle", "modes"]:
    rows = fetch_paginated(endpoint)
    assert len(rows) > 0
    df = pd.DataFrame(rows)
    df.to_json(out / f"{endpoint}.jsonl", orient="records", lines=True)
    df.to_parquet(out / f"{endpoint}.parquet", index=False)
```

Fallback:

```text
If public API pagination or rate limits block access, stop and ask the user.
Do not create an account or API key unless the user explicitly approves.
```

### ML_GBT_SETI Acquisition

Reference only. Clone code and small metadata only; do not download the full BL dataset.

```bash
mkdir -p data_cache/raw/ml_gbt_seti
git clone --depth 1 https://github.com/PetchMa/ML_GBT_SETI data_cache/raw/ml_gbt_seti/repo
```

After clone:

```text
Inspect README, environment files, and small metadata/candidate files.
Do not run scripts that download large Breakthrough Listen data.
Do not assume pretrained weights exist.
```

### Breakthrough Listen Acquisition

Do not download BL data for Track A.

For Track B or a small historical replay, the agent must first produce a download plan and ask the user. The plan must include:

```text
target name or observation set
exact archive query URL or file URL
file type
estimated file count
estimated total bytes
expected temporary storage
delete-after-use plan
why this subset is needed
```

If the plan exceeds about 100 GB raw/temp/cache usage, ask the user before downloading.

## 1. HTRU2 Pulsar Candidate Dataset

### Use

Use as the first supervised baseline for `pulsar` vs `terrestrial_rfi/noise`.

### Access

- Main page: <https://archive-beta.ics.uci.edu/dataset/372/htru2>
- API key: **No**
- License: CC BY 4.0
- Size: 17,898 rows
- Labels:
  - `class = 1`: real pulsar
  - `class = 0`: spurious example caused by RFI/noise

### Schema

```text
Profile_mean: float
Profile_stdev: float
Profile_skewness: float
Profile_kurtosis: float
DM_mean: float
DM_stdev: float
DM_skewness: float
DM_kurtosis: float
class: int  # 0 = RFI/noise, 1 = pulsar
```

### Python Access

```bash
pip install ucimlrepo pandas scikit-learn
```

```python
from ucimlrepo import fetch_ucirepo

htru2 = fetch_ucirepo(id=372)
X = htru2.data.features
y = htru2.data.targets["class"]
```

## 2. Breakthrough Listen DR1 and Open Data Archive

### Use

Do **not** use this for the first milestone except as a small manual smoke test if storage permits. This is the future Track B real SETI search substrate, not a clean supervised-label dataset.

When Track B begins, generate candidate examples through `turboSETI`, cadence filtering, anomaly scoring, and cross-matching against known-source catalogs.

### Access

- DR1 overview: <https://seti.berkeley.edu/listen2019/overview.html>
- Open Data Archive: <https://seti.berkeley.edu/opendata>
- API key: **No**
- Data can be very large: individual files may be multiple GB; DR1 is near PB scale.
- Hard storage rule: do not download raw BL data that would push local raw/temp/cache usage above about 100 GB without asking the user first.

### Archive Search Fields

```text
telescope: GBT | Parkes | APF
file_type: Filterbank | HDF5 | Baseband | FITS
data_type: Fine | Mid | Time
quality: A | B | C | F | Ungraded
cadence: On / off-source metadata where available
target: string
ra_deg: float
dec_deg: float
radius_deg: float
```

### Recommended Libraries

```bash
pip install blimpy turbo-seti h5py astropy pandas numpy scipy scikit-learn
```

### Typical Workflow

```text
Track B only:
1. Query or manually select Breakthrough Listen HDF5/FILTERBANK files.
2. Read with blimpy.
3. Run turboSETI narrowband Doppler drift search.
4. Export hit tables.
5. Apply ON/OFF cadence filtering.
6. Remove known RFI frequency regions and instrument artifacts.
7. Cross-match against ATNF, CHIME/FRB, BZCAT, Fermi, CelesTrak, and SatNOGS.
8. Score remaining events with anomaly/OOD model.
9. Emit only high-quality survivors as unknown_candidate.
```

### Minimal Reading Pattern

```python
from blimpy import Waterfall

wf = Waterfall("example.h5")
header = wf.header
data = wf.data
```

## 3. ML_GBT_SETI Reference Workflow

### Use

Use this as a reference only. Do not assume there are reusable pretrained weights. Do not make it a dependency for the first milestone.

### Access

- Project page: <https://seti.berkeley.edu/ml_gbt/>
- GitHub: <https://github.com/PetchMa/ML_GBT_SETI>
- Related paper: <https://www.nature.com/articles/s41550-022-01872-z>
- API key: **No**

### Notes

The published search used 820 stars and 480+ hours of GBT data. Follow-up observations did not re-detect the reported signals, so these are not confirmed technosignatures.

Use for:

- Model architecture reference
- Data preprocessing reference
- Candidate ranking logic
- Evaluation approach

Do not treat candidates as positive alien labels.
Do not download the full associated BL dataset during Track A.

## 4. ATNF Pulsar Catalog

### Use

Use for known pulsar cross-matching and label enrichment.

### Access

- HEASARC table: <https://heasarc.gsfc.nasa.gov/W3Browse/all/atnfpulsar.html>
- NASA dataset page: <https://data.nasa.gov/dataset/atnf-pulsar-catalog>
- HEASARC API guide: <https://heasarc.gsfc.nasa.gov/docs/xamin-api.html>
- API key: **No**

### HEASARC API Pattern

```text
https://heasarc.gsfc.nasa.gov/xamin/query?table=atnfpulsar
```

For cone searches, use HEASARC/Xamin query parameters such as:

```text
table=atnfpulsar
position=<ra>,<dec>
radius=<arcminutes>
```

### Suggested Fields to Preserve

```text
source_name
ra
dec
period
period_derivative
dispersion_measure
binary_flag
catalog_source
```

### Python Option

```bash
pip install psrqpy astropy pandas
```

```python
from psrqpy import QueryATNF

query = QueryATNF(params=["PSRJ", "RAJ", "DECJ", "P0", "P1", "DM"])
table = query.table
```

## 5. CHIME/FRB Catalog 1

### Use

Use for `frb` labels and known transient-radio-source behavior.

### Access

- Paper/catalog: <https://doi.org/10.3847/1538-4365/ac33ab>
- API key: **No**
- Size: 536 bursts in Catalog 1

### Suggested Fields

```text
frb_name
ra
dec
event_time_utc
dispersion_measure
width_ms
fluence
flux
peak_frequency
repeater_flag
instrument
```

### Label Mapping

```text
frb -> known astrophysical transient
repeater_flag=true -> repeating_frb
repeater_flag=false -> nonrepeating_frb_candidate
```

## 6. Roma-BZCAT Blazar Catalog

### Use

Use for blazar/AGN cross-matching so variable natural sources are not promoted to `unknown_candidate`.

### Access

- NASA/Data.gov page: <https://catalog.data.gov/dataset/roma-bzcat-multi-frequency-catalog-of-blazars>
- HEASARC table: <https://heasarc.gsfc.nasa.gov/W3Browse/all/romabzcat.html>
- API key: **No**

### HEASARC API Pattern

```text
https://heasarc.gsfc.nasa.gov/xamin/query?table=romabzcat
```

### Core Classes

```text
BZB: BL Lac object
BZQ: flat-spectrum radio quasar
BZG: galaxy-dominated blazar
BZU: uncertain/transitional blazar
```

### Suggested Fields

```text
source_name
ra
dec
bzcat_class
redshift
radio_flux
xray_flux
gamma_flux
catalog_source
```

## 7. Fermi LAT 4FGL-DR4

### Use

Use for high-energy source associations: pulsars, AGN/blazars, unidentified gamma-ray sources, and multiwavelength vetting.

### Access

- FSSC catalog page: <https://fermi.gsfc.nasa.gov/ssc/data/access/lat/14yr_catalog/>
- NASA/Data.gov page: <https://data.nasa.gov/dataset/fermi-lat-14-year-point-source-catalog-4fgl-dr4>
- API key: **No**
- Formats: FITS, XML, HEASARC Browse table

### Download Notes

Prefer the FITS file from FSSC for local reproducibility. Use `astropy` to inspect and convert.

```bash
pip install astropy pandas
```

```python
from astropy.table import Table

tbl = Table.read("gll_psc_v32.fit")  # filename may differ by catalog release
df = tbl.to_pandas()
```

### Suggested Fields

```text
source_name
ra
dec
class1
class2
association_name
significance
energy_flux
variability_index
spectrum_type
data_release
```

## 8. CelesTrak SATCAT and Orbital Data

### Use

Use for satellite/debris rejection. Cross-match observation time, pointing direction, frequency behavior, and Doppler drift against known orbital objects.

### Access

- SATCAT: <https://celestrak.org/satcat/>
- API key: **No**
- Formats: CSV, legacy text, GP/TLE-style orbital data

### Suggested Fields

```text
norad_cat_id
object_name
object_type
country
launch_date
launch_site
decay_date
orbital_status
tle_or_gp_epoch
inclination
mean_motion
eccentricity
```

### Implementation Notes

Use an SGP4-capable library to propagate satellite position at observation time.

```bash
pip install sgp4 skyfield pandas astropy
```

## 9. SatNOGS DB

### Use

Use for satellite transmitter-frequency matching. This complements CelesTrak, which is about orbital objects.

### Access

- API docs: <https://docs.satnogs.org/projects/satnogs-db/en/latest/api.html>
- Wiki: <https://wiki.satnogs.org/DB>
- Base API: <https://db.satnogs.org/api/>
- API key: **No for public read access. Yes for some protected/write operations.**

### Important Endpoints

```text
GET https://db.satnogs.org/api/satellites/
GET https://db.satnogs.org/api/transmitters/
GET https://db.satnogs.org/api/tle/
GET https://db.satnogs.org/api/modes/
```

### Suggested Fields

```text
sat_id
norad_cat_id
name
status
transmitter_uuid
transmitter_type
downlink_low
downlink_high
uplink_low
uplink_high
mode
baud
service
```

### Matching Rule

If an event frequency overlaps a known SatNOGS transmitter range and CelesTrak propagation places that object near the telescope beam at observation time, label as:

```text
satellite_transmitter
```

## 10. Kaggle SETI Breakthrough Listen Competition

### Use

Excluded for now because the user specified **no synthetic data**. Do not download or train on this dataset.

It may be reconsidered later only as a clearly marked synthetic benchmark if the user explicitly approves.

### Access

- Competition: <https://www.kaggle.com/competitions/seti-breakthrough-listen>
- API key: **Yes for Kaggle CLI download**

### Caveat

The positive labels are simulated/injected "needles" in real telescope data. They are not real extraterrestrial technosignature labels.

Do not download this dataset during Track A. Do not add Kaggle credentials or setup steps unless the user explicitly approves synthetic benchmarking later.

## 11. Setigen

### Use

Excluded for now because the user specified **no synthetic data**. Do not generate Setigen training data.

It may be reconsidered later only for injection/recovery validation if the user explicitly approves.

### Access

- Paper: <https://arxiv.org/abs/2203.09668>
- Package: <https://github.com/bbrzycki/setigen>
- API key: **No**

### Install

Do not install or use during the current Track A milestone unless explicitly approved.

### Caveat

Use for validation only if explicitly approved later. Never use Setigen outputs as real observational labels.

## Minimal Agent Build Plan

### Phase 0: Disk and Provenance Guardrails

Implement these before downloading data.

1. Create a local data root such as `data_cache/`.
2. Add a disk-usage guard that checks total raw/temp/cache usage before each download.
3. Stop and ask the user if expected or actual raw/temp/cache usage approaches 100 GB.
4. Write a manifest for every downloaded file:
   - source URL
   - download time UTC
   - local path
   - file size
   - checksum/hash when feasible
   - license/auth notes
5. After training and evaluation, delete raw downloaded data and temporary extraction products.
6. Keep only models, metrics, schemas, manifests, feature-generation code, and a small golden validation set.

Suggested retained layout:

```text
artifacts/
  models/
  metrics/
  manifests/
  schemas/
  golden_validation/
src/
  feature_generation/
  training/
  inference/
```

Suggested disposable layout:

```text
data_cache/
tmp_training/
tmp_features/
```

The disposable layout should be safe to delete and regenerate.

### Phase 1: Track A Known-Class Baseline

1. Download HTRU2.
2. Train a supervised classifier for `pulsar` vs `terrestrial_rfi/noise`.
3. Evaluate precision/recall and calibrate confidence thresholds.
4. Save the model, schema, metrics, and manifest.
5. Delete raw HTRU2 download/cache if it is no longer needed.

Recommended first models:

```text
LogisticRegression
RandomForestClassifier
HistGradientBoostingClassifier
```

Do not start with deep learning. HTRU2 is small tabular data; simple auditable models are the right first baseline.

### Phase 2: Catalog Cross-Matching

1. Build local normalized tables for:
   - ATNF pulsars
   - CHIME/FRB
   - Roma-BZCAT
   - Fermi 4FGL-DR4
   - CelesTrak SATCAT/GP
   - SatNOGS transmitters
2. Normalize coordinates to ICRS RA/Dec degrees.
3. Preserve source provenance for every label.
4. Add deterministic rule/cross-match outputs before adding more ML.

Track A should answer:

```text
Is this candidate plausibly explained by a known pulsar, FRB, blazar/AGN, gamma-ray source, satellite transmitter, RFI, instrument artifact, or noise?
```

### Phase 3: Small Historical Replay

Use historical replay as the first end-to-end test. Keep it small enough to stay well under the 100 GB cap.

1. Select a small set of known historical events or public candidate/hit examples.
2. Re-run the pipeline from ingestion through classification.
3. Confirm that known explanations are recovered where expected.
4. Confirm that the pipeline emits `low_confidence` rather than unsupported claims when evidence is insufficient.
5. Save replay inputs, outputs, metrics, and manifests.
6. Delete raw replay data after evaluation unless it is part of the small golden validation set.

If using Breakthrough Listen files for replay:

```text
Download the smallest feasible subset.
Prefer hit tables or narrow windows over full raw files when possible.
Do not exceed about 100 GB raw/temp/cache usage without asking.
```

### Phase 4: Track B Unknown Candidate Gate

Only emit `unknown_candidate` when all of the following are true:

```text
not confidently pulsar
not confidently FRB
not cross-matched to known blazar/AGN/gamma source
not known satellite/transmitter at observation time and beam direction
not known RFI region
not instrument/band-edge/notch artifact
passes ON/OFF cadence checks
has high anomaly/OOD score
has preserved provenance and reproducible extraction script
```

Do not implement this as the first milestone. Track B starts only after Track A and historical replay work.

## Pretrained Model Policy

Do not depend on pretrained models for the first milestone. Train small, auditable models from scratch.

| Option | Current Policy | Reason |
|---|---|---|
| ML_GBT_SETI | Reference only | Good published workflow, but do not assume reusable pretrained weights exist. |
| SAM-RFI / other RFI pretrained models | Do not use in Track A | Available examples may rely on synthetic RFI data; user selected no synthetic data. |
| Astronomaly | Framework only, optional later | Useful for active anomaly workflows, not a ready technosignature classifier. |
| General astronomy foundation models | Do not use in Track A | Usually optical/image-domain and not aligned with the tabular/crossmatch first milestone. |
| Third-party HTRU2 weights | Do not use | HTRU2 is small; training from scratch is safer and more reproducible. |

If a future agent proposes a pretrained model, require:

```text
public source
documented training data
documented license
no synthetic-data contamination unless user explicitly approves
local test against the historical replay set
clear improvement over the from-scratch baseline
```

## Unified Output Schema

Use this schema for every candidate/event row.

```text
event_id: string
source_dataset: string
source_file: string
source_url: string
observation_time_utc: datetime
telescope: string
instrument: string
target_name: string
ra_deg: float
dec_deg: float
frequency_hz: float
bandwidth_hz: float
drift_rate_hz_s: float | null
snr: float | null
duration_s: float | null
cadence_pattern: string | null
on_source_detected: bool | null
off_source_detected: bool | null
class_label: string
class_confidence: float
anomaly_score: float | null
crossmatch_catalogs_checked: list[string]
crossmatch_hits: list[dict]
satellite_match: bool
rfi_flag: bool
instrument_artifact_flag: bool
synthetic_flag: bool
review_status: string  # unreviewed | machine_rejected | human_rejected | followup_needed | promoted_candidate
notes: string
provenance_hash: string
created_at_utc: datetime
```

## API Key Summary

| Source | API Key Needed? | Notes |
|---|---:|---|
| HTRU2/UCI | No | Direct download or `ucimlrepo`. |
| Breakthrough Listen Archive | No | Public archive; very large files. |
| ML_GBT_SETI GitHub | No | Public clone unless GitHub rate limits apply. |
| HEASARC ATNF | No | Xamin public query API. |
| CHIME/FRB Catalog 1 | No | Published table access. |
| Roma-BZCAT HEASARC | No | Xamin public query API. |
| Fermi 4FGL-DR4 | No | FITS/XML public download. |
| CelesTrak | No | Public SATCAT/GP data. |
| SatNOGS | No for public reads | Key required only for protected/write actions. |
| Kaggle SETI | Excluded | Do not configure Kaggle credentials during Track A. |
| Setigen | Excluded | Do not install/use during Track A. |

## Hard Rules

1. Never label anything as `alien` or `confirmed_technosignature`.
2. Preserve data provenance for every row.
3. Do not use synthetic data for Track A training.
4. Do not install, download, or train on Kaggle SETI or Setigen unless the user explicitly approves a later synthetic benchmark.
5. Do not use pretrained models as a first-milestone dependency.
6. Do not exceed about 100 GB of raw/temp/cache data without asking the user.
7. Delete raw downloaded data and temporary extraction products after training/evaluation.
8. Do not promote a candidate before satellite, RFI, instrument, and known-source checks.
9. Treat `unknown_candidate` as a review queue state.
10. Prefer reproducible scripts over manual downloads where APIs exist.
