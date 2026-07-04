# Research request: real per-hit labeled BL/SETI classification data for calibration

## Context (assume zero prior knowledge of this project)

I run a project that does a real technosignature (SETI) search over
Breakthrough Listen (BL) radio data from the Green Bank Telescope (GBT).
The pipeline includes a semisupervised anomaly/out-of-distribution scorer
(`semisupervised_anomaly_score`) fit on 200,000 real hit rows from the
MeerKAT BLUSE survey (Sheikh et al. 2025). It is meant to help flag which
detected radio "hits" (candidate narrowband signals surviving RFI/cadence
filtering) look statistically unusual versus routine.

I need to calibrate what a "high" or "meaningful" score actually means —
i.e. set a real, evidence-based threshold, not an invented one. The only
real ground-truth labels I currently have are from a small citizen-science
review of one target (HIP99427): 124 total hits, only 81 labeled
`false_positive`, 41 `insufficient_evidence`, and just **2** labeled
`follow_up` (the positive class that actually matters). That is far too
small a sample to calibrate a threshold from — I need to find more real,
independently labeled data before I can trust any cutoff.

## What I need you to find

I need real, human-reviewed, per-hit or per-candidate classification
labels from published SETI/BL work — not aggregate statistics, not
example plots, and not synthetic/simulated data. Specifically:

1. **Enriquez et al. 2017** ("The Breakthrough Listen Search for
   Intelligent Life: 1.1-1.9 GHz Observations of 692 Nearby Stars", ApJ
   849, 104, arXiv:1709.03491). Does the paper or its supplementary data
   include a real, downloadable table with **per-hit or per-candidate**
   classification labels (e.g. RFI/candidate/rejected/follow-up), rather
   than just summary hit counts? Check the arXiv ancillary files, the
   ApJ/IOPscience article's supplementary/machine-readable data links, and
   any linked GitHub/Zenodo repository from the paper or its authors
   (e.g. `UCBerkeleySETI` on GitHub).

2. **Price et al. 2020** ("The Breakthrough Listen Search for Intelligent
   Life: Observations of 1327 Nearby Stars Over 1.10-3.45 GHz", AJ 159, 86,
   arXiv:1906.07750). Same question — real per-hit labeled data, not just
   aggregate hit counts.

3. **Sheikh et al. 2021** (the "BLC1" candidate paper covering the
   Proxima Centauri candidate signal, arXiv:2111.06350) and any of its
   companion/follow-up papers. Did this work publish a labeled table of
   the many candidate signals it reviewed and rejected (it's known to have
   manually reviewed a large number of candidates before isolating BLC1) —
   with real per-candidate verdicts, in a machine-readable, downloadable
   form?

4. **A 2024/2025 unsupervised or semi-supervised RFI-classification paper**
   (possible arXiv ID 2411.16556 — verify this is real and relevant, don't
   assume it from the ID alone) — does it publish a labeled evaluation set
   with real per-hit ground truth (not just its own model's predictions)?

5. **The "Breakthrough Listen Exotica Catalog"** (possibly hosted on
   Zenodo, record ID around 5744996) — confirm what this actually contains.
   I suspect from search snippets it's a catalog of *target selection
   categories* (types of astrophysical sources chosen for observation), not
   per-hit signal classifications — please confirm or correct this.

6. **Any other real, specific published SETI/technosignature paper** with
   a genuine per-hit or per-candidate labeled dataset usable as
   ground-truth for training or calibrating a false-positive/candidate
   classifier — cite the exact paper and the exact real location the data
   is hosted (VizieR, Zenodo, GitHub, journal supplementary data URL).

For each source, I need:
- Confirmation the labeled table is real and machine-readable (not just
  described in prose or shown as a figure)
- The real hosting URL/DOI/repository location
- The real row count (number of labeled hits/candidates)
- What the real label categories are (e.g. RFI vs. candidate vs.
  something else) and whether they map meaningfully onto
  false_positive/follow_up/insufficient_evidence

## What NOT to do

- Do not report a paper as having "labeled data" based only on it
  describing filtering/classification methodology in prose — I need an
  actual downloadable table with individual verdicts, not a description of
  a process.
- Do not guess a hosting URL, DOI, or row count — confirm by actually
  opening/fetching the real page or file.
- Do not treat aggregate hit counts (e.g. ">51 million hits processed") as
  evidence of per-hit labels — that is a processing volume statistic, not
  ground truth.
- If none of the above sources turn out to have real usable per-hit labels,
  say so plainly rather than stretching a weak match — a clear "this list
  is exhausted, no real per-hit labeled data exists in these sources" is a
  valid and useful answer.
