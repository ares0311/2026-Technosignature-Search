# MeerKAT BLUSE Hit-Table Source Research

Research date: 2026-06-29

Repository: `ares0311/2026-Technosignature-Search`

## Executive Decision

The public MeerKAT BLUSE hit metadata source has been found and verified at the HTTP/file level.

Verified source:

```text
https://bldata.berkeley.edu/ATLAS/MeerKAT/atlas_hits_2025_11_dups.json.gz
```

This is the file described by the Berkeley SETI / Breakthrough Listen 3I/ATLAS public-data page as a 90 MB gzipped JSON file containing metadata for just over 2 million MeerKAT hits from November observations.

Production status:

- The source URL is real, stable enough to document, and reproducible.
- The file is gzip-compressed JSON, top-level JSON array.
- `scripts/ingest_meerkat_hits.py` now supports this schema through `--use-verified-atlas-source`, validates required fields, and records source checksum/provenance.
- Explicit license text for this exact JSON artifact was not identified. Treat as public Breakthrough Listen research data for local, non-redistributed training/evaluation with attribution unless/until a clearer license is found.
- No detections, discoveries, expert review, or external validation are implied by this dataset.

Implementation status:

`scripts/ingest_meerkat_hits.py` supports the verified schema, validates
required fields, maps SETICORE-style fields into scorer-ready normalized
features, and records source checksum/provenance. On 2026-06-29, the verified
payload was downloaded to ignored local storage, 200,000 rows were normalized,
and `semisupervised_scorer` was trained locally with 12 workers. Do not commit
the payload or fitted model.

## Repo Files Read

Per repo instructions, these files were read first:

- [`AGENTS.md`](https://github.com/ares0311/2026-Technosignature-Search/blob/main/AGENTS.md)
- [`docs/PRODUCTION_READINESS.md`](https://github.com/ares0311/2026-Technosignature-Search/blob/main/docs/PRODUCTION_READINESS.md)
- [`scripts/ingest_meerkat_hits.py`](https://github.com/ares0311/2026-Technosignature-Search/blob/main/scripts/ingest_meerkat_hits.py)
- [`src/techno_search/semisupervised_scorer.py`](https://github.com/ares0311/2026-Technosignature-Search/blob/main/src/techno_search/semisupervised_scorer.py)

Relevant repo state:

- Local GBT/turboSETI training is already working and fitted on 259 real hits.
- MeerKAT-specific training is no longer blocked on source discovery or schema mapping; the next work is real-corpus evaluation and downstream candidate-packet validation.
- `scripts/ingest_meerkat_hits.py` intentionally has no implicit network default; use `--use-verified-atlas-source` to select the verified URL and SHA256.
- The earlier Zenodo concept `10987642` must not be used; the repo states it resolves to unrelated content.

## Verified File Metadata

User-side verification command:

```bash
git pull origin main
curl -L -I https://bldata.berkeley.edu/ATLAS/MeerKAT/atlas_hits_2025_11_dups.json.gz
```

Observed headers:

```text
HTTP/1.1 200 OK
Server: nginx/1.21.0
Date: Mon, 29 Jun 2026 05:35:00 GMT
Content-Type: application/octet-stream
Content-Length: 94246793
Last-Modified: Fri, 19 Dec 2025 22:53:44 GMT
ETag: "6945d778-59e1789"
Accept-Ranges: bytes
```

Downloaded file:

```text
/tmp/atlas_hits_2025_11_dups.json.gz
```

SHA256:

```text
f0ba629077825097b1c247cf94131858992636d5bf8cea3b5bfde23b0384ea17
```

Size:

- HTTP `Content-Length`: `94,246,793` bytes
- Decimal MB: about `94.25 MB`
- Binary MiB: about `89.88 MiB`

## Sample Schema

Verification command:

```bash
git pull origin main
gzip -dc /tmp/atlas_hits_2025_11_dups.json.gz | head -c 2000
```

Observed structure:

- Top-level JSON array.
- Records are JSON objects.
- First observed fields:

```json
{
  "frequency": 924.9910576790571,
  "index": 81977,
  "driftSteps": 12,
  "driftRate": 0.06052830194730198,
  "snr": 15.208671,
  "coarseChannel": 10,
  "beam": 0,
  "power": 4.6325947e16,
  "incoherentPower": 0.0,
  "sourceName": "Atlas",
  "fch1": 924.9909939020872,
  "foff": 0.0000015944242477416992,
  "tstart": 60984.176537959574,
  "tsamp": 5.017485158878505,
  "ra": 13.255836111111112,
  "dec": -5.825555555555555,
  "telescopeId": 64,
  "numTimesteps": 57,
  "numChannels": 91,
  "startChannel": 81937,
  "fileindex": 1,
  "hostname": "blpn37",
  "filename": "/scratch/data/20251105T041412Z-20251027-0004/seticore_search/guppi_60984_15252_001942_Atlas_0001.hits"
}
```

Important schema notes:

- `frequency` appears to be in MHz, not Hz. Convert to Hz for `SemisupervisedScorer`: `frequency_hz = frequency * 1_000_000`.
- `driftRate` appears to be Hz/s and maps to `drift_rate_hz_per_sec`.
- `snr` is already lowercase and maps to `snr`.
- `foff` appears to be MHz/channel. A derived bandwidth estimate can use `abs(foff) * numChannels * 1_000_000`.
- `sourceName` maps to target/source identity.
- `beam`, `hostname`, `filename`, `tstart`, `ra`, and `dec` should be preserved as provenance.
- Filename paths are original pipeline paths and should not be treated as local paths.
- The filename includes `seticore_search` and `.hits`, so this is BLUSE/SETICORE-style hit metadata rather than a classic turboSETI `.dat` table.
- The file name includes `dups`, so duplicate hits across beams or processing outputs may be present. For training, decide whether to deduplicate or intentionally retain duplicates as an RFI-density signal.

## Mapping to `scripts/ingest_meerkat_hits.py`

Earlier script versions did not map this schema correctly. The old
turboSETI-style field map expected fields such as:

| Current expected field | Verified file field |
|---|---|
| `Drift_Rate` | `driftRate` |
| `SNR` | `snr` |
| `Uncorrected_Frequency` / `Corrected_Frequency` | `frequency` |
| `Coarse_Channel_Number` | `coarseChannel` |
| no current mapping | `beam` |
| no current mapping | `sourceName` |
| no current mapping | `foff`, `numChannels` |

If an older branch ingests this file without the schema-specific mapper, it will
likely emit low-information records with fallback zeros for key features such as
frequency and drift. That would poison training.

Recommended normalization:

| Verified field | Normalized field | Transform |
|---|---|---|
| `frequency` | `frequency_hz` | `float(frequency) * 1_000_000` |
| `driftRate` | `drift_rate_hz_per_sec` | `float(driftRate)` |
| `snr` | `snr` | `float(snr)` |
| `coarseChannel` | `coarse_channel` | integer |
| `sourceName` | `target_id` | string |
| `beam` | `beam` | integer |
| `foff`, `numChannels` | `bandwidth_hz` | `abs(foff) * numChannels * 1_000_000` |
| `ra` | `ra_deg` | float |
| `dec` | `dec_deg` | float |
| `filename` | `source_artifact` | string provenance only |
| `tstart` | `tstart_mjd` | float |
| `hostname` | `backend_host` | string provenance |

Recommended required fields for schema validation:

- `frequency`
- `driftRate`
- `snr`
- `sourceName`
- `beam`
- `foff`
- `numChannels`
- `filename`

Records missing required fields should be counted and skipped or fail the run, depending on CLI option. The default production behavior should fail loudly if the first sample lacks core fields.

## Source and Scientific Context

Primary/public sources:

- Berkeley SETI / Breakthrough Listen 3I/ATLAS public-data page: [https://seti.berkeley.edu/atlas/](https://seti.berkeley.edu/atlas/)
- Verified Berkeley BL data URL: [https://bldata.berkeley.edu/ATLAS/MeerKAT/atlas_hits_2025_11_dups.json.gz](https://bldata.berkeley.edu/ATLAS/MeerKAT/atlas_hits_2025_11_dups.json.gz)
- The Astronomer's Telegram #17499: [https://www.astronomerstelegram.org/?read=17499](https://www.astronomerstelegram.org/?read=17499)
- Sheikh et al. ATA 3I/ATLAS paper, relevant context but not the MeerKAT source: [https://arxiv.org/abs/2512.18142](https://arxiv.org/abs/2512.18142)
- Breakthrough Listen public-data-format background: [https://arxiv.org/abs/1906.07391](https://arxiv.org/abs/1906.07391)

Context distinctions:

- ATel #17499 reports a MeerKAT/BLUSE technosignature search on 2025-11-05, 23,689 detected signals, and likely anthropogenic RFI after spatial consistency checks.
- The Berkeley public-data page describes a much larger "just over 2 million hits" gzip JSON file. The verified `atlas_hits_2025_11_dups.json.gz` appears to be this larger hit metadata table, not merely the final ATel #17499 signal count.
- Sheikh et al. 2025/2026 is primarily an Allen Telescope Array search using `bliss`, not the MeerKAT BLUSE dataset. It should be cited as related 3I/ATLAS technosignature context, not as the source of this MeerKAT file.

## Licensing and Use Constraints

No explicit license text for `atlas_hits_2025_11_dups.json.gz` was identified from the available page text or file headers.

Conservative production policy:

- Store only the URL, checksum, file size, retrieval date, and schema notes in the repo.
- Do not commit the downloaded gzip, decompressed JSON, derived large NDJSON, or fitted model payload unless the repo policy explicitly allows that artifact class.
- Use the dataset locally as public Breakthrough Listen research data for false-positive/anomaly-distribution training and evaluation only.
- Attribute Berkeley SETI / Breakthrough Listen and the 3I/ATLAS public-data page in provenance.
- Preserve the scientific guardrail: no row in this dataset is a detection, discovery, expert-reviewed candidate, externally validated signal, or submission authorization.

## Recommended Next Production Task

The next production task should now evaluate the trained MeerKAT scorer in the
radio pipeline:

1. Keep the patched `scripts/ingest_meerkat_hits.py` support for the verified `atlas_hits_2025_11_dups.json.gz` schema.
2. Keep the schema validator and parser-contract test in place. Do not use synthetic training data; the fixture is parser contract data only.
3. Preserve provenance output fields:
   - `source_url`
   - `sha256`
   - `content_length_bytes`
   - `etag`
   - `last_modified`
   - `retrieved_at_utc`
   - `source_page`
4. Evaluate `run-pipeline` on real GBT candidate packets with the local MeerKAT-trained scorer.
5. Compare scorer outputs against existing drift/cadence/RFI evidence and ensure no claim language changes.
6. Update `docs/PRODUCTION_READINESS.md` only with measured validation results.

Suggested local verification commands:

```bash
git pull origin main
curl -L -o data/meerkat_hits/atlas_hits_2025_11_dups.json.gz \
  https://bldata.berkeley.edu/ATLAS/MeerKAT/atlas_hits_2025_11_dups.json.gz

shasum -a 256 data/meerkat_hits/atlas_hits_2025_11_dups.json.gz
gzip -dc data/meerkat_hits/atlas_hits_2025_11_dups.json.gz | head -c 2000

caffeinate -i .venv/bin/python scripts/ingest_meerkat_hits.py \
  --use-verified-atlas-source \
  --output-dir data/meerkat_hits \
  --max-hits 200000
```

Expected SHA256:

```text
f0ba629077825097b1c247cf94131858992636d5bf8cea3b5bfde23b0384ea17
```

## Final Answer

The remaining Phase 0/1 blocker is no longer "find a public MeerKAT URL." A verified public Berkeley BL data URL exists:

```text
https://bldata.berkeley.edu/ATLAS/MeerKAT/atlas_hits_2025_11_dups.json.gz
```

The remaining production work is to evaluate the locally trained MeerKAT scorer
against real radio pipeline outputs, preserve checksum/provenance, apply
conservative non-redistribution/attribution handling because explicit license
text was not found, and avoid detection or external-validation claims.
