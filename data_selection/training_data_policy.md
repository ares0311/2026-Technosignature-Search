# Technosignatures Training Data Policy

Training data hardens models; live-search data looks for candidates. Do not mix
the two roles.

Rules:

1. Do not train on live-search data and later claim a blind search on that same
   data.
2. Do not treat unlabeled hit rows as negatives.
3. Do not infer row-level labels from a paper-level null result.
4. Prefer real corpora, real review labels, hard negatives, and manifest-backed
   provenance.
5. Do not promote learned models without grouped/leakage-safe evaluation,
   calibration context, and injection-recovery evidence in real backgrounds.
6. Keep model outputs as local triage evidence only.

Current known limitation:

The project does not have enough real per-hit labeled ground truth to calibrate
a reliable global anomaly/OOD threshold. The project-owned human review set
described in `docs/SYSTEMATIC_SEARCH_PLAN.md` Step 1 remains required.

