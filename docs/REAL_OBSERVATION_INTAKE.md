# Real Observation Intake

## Production Gap

The highest-priority unresolved Tier 1 gap is **Real observation data ingested**.
Synthetic turboSETI output verifies file-format compatibility but does not close
that gap.

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

## Proposed First Dataset

Use a small Breakthrough Listen Green Bank Telescope observation set from the
official Open Data Archive. Prefer an ON/OFF cadence when available so the same
intake can later support false-positive and RFI analysis. The existing local
Voyager file may be used as the first minimal observation only after its exact
archive URL, checksum, and terms are verified and approved.

Official starting points:

- `https://breakthroughinitiatives.org/opendatasearch`
- `https://seti.berkeley.edu/listen/data.html`

## Human Gate 1

The project owner must approve:

- the selected archive record and local files;
- applicable data-use and citation requirements;
- the instrument and observation metadata;
- whether a single Voyager diagnostic observation is sufficient for the first
  ingestion, or whether an ON/OFF GBT cadence is required;
- local processing only, with external submission still disabled.

Until that decision is recorded, `scripts/run_pipeline_on_bl_data.sh` stops
without processing synthetic or unverified artifacts.
