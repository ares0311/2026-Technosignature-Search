# Real Observation Intake

## Completed Production Gap

The Tier 1 gap **Real observation data ingested** was closed locally on
2026-06-10 with the approved HIP99427 GBT ABACAD cadence. This does not clear
the remaining Tier 1 blockers or authorize external submission.

Production-path pipeline execution accepts a `.dat` hit table only when:

1. The file is recognizable turboSETI output and has no synthetic marker.
2. A sibling `<filename>.provenance.json` file records its SHA-256 hash.
3. The sidecar records an HTTPS archive URL, archive name, instrument, and
   download timestamp.
4. Data-use, provenance, and human reviews are all `approved`.
5. `approved_for_local_real_data` is explicitly `true`.

This approval permits local scientific evaluation only. It does not authorize
external submission or support a detection claim.

## Current Local Audit

Audit date: 2026-06-09.

| Artifact group | Classification | Production status |
|---|---|---|
| `GBT_synth_*_hits.dat` | Explicitly synthetic | Rejected |
| `synth_bl_32step.dat` | Explicitly synthetic | Rejected |
| `blc1_2bit_hits.dat` | Invalid 14-byte HTTP error response | Rejected |
| `Voyager1_test.h5` | Structurally plausible GBT HDF5; provenance not approved | Pending |
| `Voyager1_test.dat` | turboSETI output with no reported hits; provenance not approved | Pending |

The local `Voyager1_test.h5` SHA-256 is
`a4f9d9da015b4d45054ef91a1d95dc27138e495d887f595970c13828a76c9412`.
Its header identifies source `VOYAGER-1`, telescope ID `6`, start MJD
`59046.92634259259`, and a 1,048,576-channel GBT-style coarse channel. These
facts are not sufficient to approve it as real observation evidence because
the acquisition record and data-use review are absent.

## Approved First Dataset

Human Gate 1 selected an official Green Bank Telescope ON/OFF cadence. The
approved set is the HIP99427 ABACAD cadence beginning at
`2016-12-30T23:03:45Z` (MJD 57752.9609). It contains three HIP99427 target
scans interleaved with HIP100670, HIP99560, and HIP99759 comparison scans.

The exact HTTPS URLs, byte sizes, archive MD5 checksums, timestamps, scan roles,
and processing parameters are recorded in
`configs/gbt_hip99427_cadence_v1.json`. The selected `.0002.h5` products total
approximately 1.45 GB. Raw HDF5 files and derived hit tables remain outside the
repository under `~/technosignature-data/`.

The archive's HIP65352 summary was rejected for this run because its published
third comparison scan is a HIP64577 observation from approximately two hours
earlier. Preserving that negative provenance finding avoids treating a
non-contiguous pair as a complete cadence.

## Human Gate 1

The project owner must approve:

- the selected archive record and local files;
- applicable data-use and citation requirements;
- the instrument and observation metadata;
- whether a single Voyager diagnostic observation is sufficient for the first
  ingestion, or whether an ON/OFF GBT cadence is required;
- local processing only, with external submission still disabled.

Human Gate 1 was approved on 2026-06-10 for local processing of the official
GBT ON/OFF option. Data are released under CC BY 4.0 according to the official
L-band download page. External submission remains disabled.

Run the manifest-driven intake with:

```bash
git pull origin main
caffeinate -i .venv/bin/python scripts/ingest_gbt_cadence.py
```

The command verifies archive size and MD5 before processing, records SHA-256
for local artifacts, runs turboSETI 2.3.2, writes reviewed provenance sidecars,
and builds one derived cadence CSV with explicit ON/OFF roles. The intake
applies a documented one-line turboSETI 2.3.2 compatibility patch that converts
its NumPy 2.x hit-counter array to a scalar only for debug formatting; it does
not alter search calculations.

The selected `.0002.h5` products report a 9.7960855 Hz/s drift-bin resolution.
An initial 4 Hz/s ceiling therefore produced no eligible nonzero drift bins.
The reviewed ingestion manifest uses a 10 Hz/s ceiling to include exactly the
first positive and negative resolvable bins. This is an ingestion evidence run,
not a calibrated scientific threshold; calibrated thresholds remain a separate
Tier 1 blocker.

## Local Result

All six archive files passed published byte-size and MD5 checks. Local SHA-256
hashes were recorded for each HDF5 and derived hit table. The reviewed 10 Hz/s
ingestion run produced 213 rows: 110 ON-target and 103 OFF-target.

The guarded report routes `do_not_submit_false_positive`, assigns the dominant
hypothesis to human interference, and records frequency-matched OFF-target
recurrence across all three comparison targets as a blocking issue. This is
negative evidence and a successful ingestion validation, not a candidate
requiring external follow-up.
