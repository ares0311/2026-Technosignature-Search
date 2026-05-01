# SCHEMA VERSIONING

## Purpose

Define how JSON schema versions evolve for candidate packets, report manifests, and batch manifests.

Schema versions support reproducibility. They are not scientific confidence scores and must not be used as evidence for a candidate.

---

## Current Version

```text
techno_search_packet_v1
```

This version applies to:

- candidate packet JSON
- per-candidate report manifests
- batch manifests

---

## Compatibility Policy

Patch-compatible changes may:

- add optional fields
- clarify field descriptions
- add examples

Version-changing updates should be considered when a change:

- removes a field
- renames a field
- changes a field type
- changes required fields
- changes pathway or posterior field names
- changes how provenance, negative evidence, or blocking issues are represented

---

## Required Fields

Generated candidate packets, report manifests, and batch manifests must include:

```json
{
  "schema_version": "techno_search_packet_v1"
}
```

When schema versions change, update:

- `src/techno_search/reporting.py`
- `schemas/*.schema.json`
- committed example artifacts
- validation tests
- release checklist documentation
