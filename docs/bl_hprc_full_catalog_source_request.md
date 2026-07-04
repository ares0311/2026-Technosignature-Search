# Research request: real machine-readable Breakthrough Listen HPRC target list

## Context (assume zero prior knowledge of this project)

I run a project that does a real technosignature (SETI) search over
Breakthrough Listen (BL) radio data from the Green Bank Telescope (GBT).
The target list currently used is a hand-picked 48-star subset
(`data/bl_hprc_seed_targets.csv`) of a much larger real published target
list from:

> Isaacson, H. et al. 2017, "The Breakthrough Listen Search for
> Intelligent Life: Target Selection of Nearby Stars and Galaxies",
> PASP, 129, 054501, arXiv:1701.06227

That paper's real target list has 1,702 stars total (60 nearest stars
within 5.1 pc, plus 1,649 stars from the Hipparcos catalog spanning the
Hertzsprung-Russell diagram). I want to replace/extend our 48-star seed
file with the real, full list so I can run a much larger real stratified
sample against BL's public data archive (I now have real storage budget
to support several hundred additional real downloads).

## What I need you to find

1. **A real, downloadable, machine-readable version of this full
   1,702-star target list** -- ideally as a table with columns I can
   parse programmatically (star name/HIP identifier, RA/Dec, distance,
   spectral type at minimum). Check:
   - VizieR (https://vizier.cds.unistra.fr) -- search for "Isaacson 2017"
     or the journal reference PASP 129, 054501. Report the exact VizieR
     catalog identifier if one exists (e.g. something of the form
     `J/PASP/129/054501`) -- do not guess this identifier, confirm it by
     actually finding it on the VizieR site or in a source that cites it
     directly.
   - The IOPscience article page for the paper
     (https://iopscience.iop.org/article/10.1088/1538-3873/aa5800) --
     check for a "Data behind the Figure" or supplementary machine-readable
     table link.
   - The arXiv page (https://arxiv.org/abs/1701.06227) -- check whether
     ancillary files (data tables) are attached to the arXiv submission.
2. **The real Breakthrough Listen Open Data Archive's documented
   concurrent-request / rate-limit policy**, if any is published (check
   https://breakthroughinitiatives.org/opendatasearch and any associated
   API/usage documentation, and seti.berkeley.edu/opendata). I need to
   know whether it's safe to run multiple simultaneous discovery/download
   requests against it, and if so how many, per any real documented
   guidance -- not an assumption.
3. If the full 1,702-star table isn't available in a clean machine-readable
   form anywhere, report that plainly, and instead find any other real,
   larger (more than 48 stars) published BL HPRC-adjacent target list that
   is available in machine-readable form (e.g. from a related BL paper's
   supplementary data), citing exactly where it came from.

## What NOT to do

- Do not guess or construct a plausible-looking VizieR catalog ID --
  confirm it by actually finding it referenced or by finding it on the
  VizieR site itself.
- Do not fabricate or estimate star properties (RA/Dec/distance/spectral
  type) for any star in the list -- only report what's in the real
  source table.
- Do not assume a specific concurrent-request limit for the BL archive
  if none is actually published -- report "no published limit found"
  if that's the case, rather than inventing a number.
