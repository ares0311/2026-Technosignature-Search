# PUBLISHING

## Purpose

Document safe publication options for local commits.

This project may contain unpublished research workflow code and local workspace context. Publishing should be intentional and reviewed by the project owner.

---

## Current State

As of 2026-05-01, local `main` contains commits that may be ahead of `origin/main`.

Check with:

```bash
git status --short --branch
git log --oneline --decorate --max-count=5
```

Recent local commits:

```text
c3b31c5 Add quickstart batch examples and fixture coverage
121f33d Add CLI docs and batch scoring
cb24d55 Add CLI examples calibration and manifests
5c1c6ae Build synthetic scoring foundation
```

---

## Automated Push Status

An attempted automated push was blocked by the execution environment because pushing `main` mutates an external remote.

Blocked command:

```bash
git push origin main
```

No workaround should be attempted by agents without explicit project-owner direction.

Current recommended publication decision:

- Keep the commits local until the project owner manually reviews the synthetic examples and generated reports.
- If publishing is desired, prefer a branch and pull request over a direct `main` push.
- Direct automated pushing remains out of scope for agents in this environment.

---

## Safe Publication Options

The project owner can choose one of these paths:

1. Push `main` manually after reviewing the staged local commits.
2. Create a feature branch from local `main`, push that branch manually, and open a pull request.
3. Keep working locally until the next stable checkpoint.
4. Export a patch for offline review:

   ```bash
   git format-patch origin/main..main
   ```

---

## Pre-Publish Checklist

Before publishing, run:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src
git diff --check
git status --short --branch
```

Confirm:

- no large data files are included
- no credentials or API tokens are included
- generated example reports use synthetic data only
- candidate reports preserve conservative language
- `CLAUDE.md`, `AGENTS.md`, and project docs are consistent
