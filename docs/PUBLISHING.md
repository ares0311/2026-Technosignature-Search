# PUBLISHING

## Purpose

Document safe publication options for local commits.

This project may contain unpublished research workflow code and local workspace context. Publishing should be intentional and reviewed by the project owner.

---

## Current State

As of 2026-05-08, local `main` is expected to track `origin/main`.

Check with:

```bash
git status --short --branch
git log --oneline --decorate --max-count=5
```

Recent pushed commits:

```text
fa1ebcf Add benchmark run result summaries
0e94ea9 Add validation dataset and benchmark metadata summaries
887775f Record consensus calibration push
```

GitHub reported that the repository moved to:

```text
https://github.com/ares0311/2026-Technosignature-Search.git
```

If local `origin` still points at the previous URL, update it intentionally:

```bash
git remote set-url origin https://github.com/ares0311/2026-Technosignature-Search.git
```

---

## Automated Push Status

Agents may push only when the project owner explicitly requests publication. The current validated push command is:

```bash
git push origin main
```

No workaround should be attempted if credentials, remote access, or repository ownership is unclear.

---

## Safe Publication Options

The project owner can choose one of these paths:

1. Push `main` after reviewing the staged local commits.
2. Create a feature branch from local `main`, push that branch, and open a pull request.
3. Keep working locally until the next stable checkpoint.
4. Export a patch for offline review:

   ```bash
   git format-patch origin/main..main
   ```

---

## Pre-Publish Checklist

Before publishing, run:

```bash
git pull origin main
caffeinate -i .venv/bin/python scripts/run_parallel_validation.py
git diff --check
git status --short --branch
```

Confirm:

- no large data files are included
- no credentials or API tokens are included
- generated example reports use synthetic data only
- candidate reports preserve conservative language
- operations readiness does not report live-provider access or external submission approval
- operations action plan does not imply blockers are cleared
- operations action resolution keeps live-data and external-submission authorization counts at zero
- `CLAUDE.md`, `AGENTS.md`, and project docs are consistent
- `.github/workflows/*.yml` is not added unless the publishing token has GitHub `workflow` scope
- CI examples remain under `docs/templates/` until workflow-scope publishing is available
