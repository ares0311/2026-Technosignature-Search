# Data Selection Decision Log

## 2026-07-09 - HPRC Local-Coverage Target Priority Queue

Repo: `2026 Technosignature Search`

Data: Breakthrough Listen HPRC full target metadata from the committed full
seed CSV (`data/bl_hprc_full_seed_targets.csv`) plus tracked local acquisition
provenance (`docs/data_collection_status.json`).

Role: `live_search`

Acquisition mode: `metadata_only`

Decision: Build and commit `data_selection/target_priority_queue.csv` before
future raw live-search pulls. This queue ranks targets using metadata-first
local-coverage novelty, not model score and not stratified-random sampling.

Reason: `docs/SYSTEMATIC_SEARCH_PLAN.md` Step 3a requires a detection-optimized
novel-target selector. The project already has real full HPRC metadata and a
tracked record of targets acquired or skipped by the current extended-corpus
process, but that information was not assembled into a GitHub-visible target
queue.

Guardrails:
- This queue is a scheduling aid only.
- Raw download is not authorized from this queue alone.
- Product type, cadence, URI, estimated download size, and storage impact must
  be verified before any raw acquisition batch.
- Follow-up scoring remains zero until a real unresolved candidate exists.
- Live-search rows must not be used for model training unless demoted into a
  future training manifest and excluded from later blind-search claims.

Artifacts:
- `data/bl_hprc_full_seed_targets.csv`
- `data/bl_hprc_full_targets_vizier.csv`
- `data_selection/target_priority_queue.csv`
- `src/techno_search/target_priority_queue.py`

