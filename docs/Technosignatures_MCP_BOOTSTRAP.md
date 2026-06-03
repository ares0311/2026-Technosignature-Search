# MCP Bootstrapper — Technosignature Search

> **Use:** Place this file at the repository root as `MCP_BOOTSTRAP.md` or keep this descriptive filename and instruct the coding agent to read it immediately after `AGENTS.md`.
>
> **Purpose:** Give Claude Code and Codex enough repo-local instructions to generate safe, project-scoped MCP configuration files for the Technosignature Search project without using manual application settings as the source of truth.

---

## 1. Objective

Bootstrap a conservative, project-scoped MCP setup for the **Technosignature Search** repository.

The rollout must generate, validate, and hand off these files:

```text
.mcp.json
.codex/config.toml
```

This repository is vulnerable to false-positive inflation, sensational language, large-data mistakes, live-provider drift, and unsupported discovery claims. MCP must therefore help coding agents inspect files, run fixed local validation commands, and generate review-only artifacts while preventing arbitrary shell access, live provider access by default, large data commits, credential exposure, external submission, or unsupported technosignature claims.

This file is the source-of-truth rollout instruction. The generated config files are implementation artifacts derived from this policy.

---

## 2. Required Reading Before Any Change

Before creating or modifying MCP config, read these files in this order:

```text
AGENTS.md
README.md
docs/PROJECT_STATUS.md
docs/PIPELINE_SPEC.md
docs/SCORING_MODEL.md
docs/ROADMAP.md
docs/DECISIONS.md
docs/DATA_POLICY.md
CONTRIBUTING.md
docs/LOCAL_SYSTEM_PROFILE.md
pyproject.toml
```

If a listed file is missing, record the missing file in the rollout handoff and continue only if the remaining files are sufficient to preserve safety.

If files conflict, preserve the repository's documented priority order: `docs/DECISIONS.md`, then `docs/SCORING_MODEL.md`, then `docs/PIPELINE_SPEC.md`, then `docs/PROJECT_STATUS.md`.

Do not rely on chat history, prior memory, or unstated assumptions as the source of truth.

---

## 3. Existing Project Constraints To Preserve

The MCP rollout must preserve the repository's standing rules:

- Python 3.11+.
- Package: `techno-search`.
- Import package: `techno_search`.
- CLI entry point: `techno-search`.
- Local environment: `.venv`.
- Do not commit `.venv/`.
- Do not rely on system Python packages.
- Default tests must use synthetic fixtures and mocked services.
- Live-data tests must be marked `integration_live`.
- Never claim a confirmed technosignature.
- Never use sensational language such as `alien signal`.
- Use conservative terms such as `candidate signal`, `anomaly`, `follow-up target`, or `technosignature-interest candidate`.
- Treat false positives as the default hypothesis.
- Preserve uncertainty, negative evidence, blocking issues, and data provenance in outputs and reports.
- Do not claim discovery without external validation.
- Do not commit large data, catalogs, caches, generated intermediate products, private credentials, or API tokens.

---

## 4. Files To Generate Or Update

Generate or conservatively merge the following files:

```text
.mcp.json
.codex/config.toml
```

Create parent directories as needed.

If either file already exists:

1. Read it fully.
2. Preserve unrelated existing servers and comments where possible.
3. Do not overwrite existing user configuration.
4. Add only the Technosignature Search MCP entries required by this bootstrap.
5. If merge safety is uncertain, stop and write a clear handoff instead of replacing the file.

Do not modify `AGENTS.md` unless the human explicitly asks.

---

## 5. MCP Server Design

Configure only a small, conservative MCP set.

### 5.1 Required Server: Project Files

Purpose:

- Read project files.
- Inspect docs, source, tests, schemas, configs, examples, and small synthetic fixtures.
- Limit file access to this repository root.

Rules:

- Repository-root scope only.
- No access to parent directories.
- No access to global home directories.
- No access to `.venv/`, `.env`, `data/raw/`, `data/interim/`, `data/external/`, large caches, live-provider caches, generated artifacts, credential files, or bulk data unless the current human task explicitly requires read-only inspection.
- Never expose token values, password values, Keychain exports, or credential file contents.

### 5.2 Required Server: Git Read / Limited Git

Purpose:

- Inspect `git status`, diffs, branches, and recent history.
- Help avoid overwriting unrelated user changes.

Allowed operations:

```text
git status --short --branch
git diff
git diff --staged
git log --oneline --decorate -n 20
git branch --show-current
```

Forbidden operations through MCP unless the human explicitly approves in the current task:

```text
git push
git push --force
git push --force-with-lease
git reset --hard
git clean -fd
git checkout -- .
git rebase
git merge
git tag
git remote set-url
```

### 5.3 Required Server: `techno_guard`

Create or configure a narrow local validation guard named:

```text
techno_guard
```

The guard must expose fixed commands only. It must not provide arbitrary shell access.

Allowed `techno_guard` commands:

```bash
.venv/bin/python -m pytest
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/ruff check .
.venv/bin/mypy src
.venv/bin/techno-search --help
.venv/bin/techno-search validate-all
.venv/bin/techno-search validation-summary
.venv/bin/techno-search operations-readiness-summary
.venv/bin/techno-search score examples/candidates/radio_clean_candidate.json
.venv/bin/techno-search score-batch examples/candidates artifacts/mcp_bootstrap_batch_reports
```

Rules for `techno_guard`:

- Use `.venv/bin/...` commands by default.
- If `.venv` is missing, report the missing environment instead of falling back to system Python.
- If dependencies are missing, install only inside `.venv` and only after checking the dependency files.
- Write generated review-only outputs under ignored artifact paths such as `artifacts/mcp_bootstrap_*`.
- Do not run any command that contacts live providers unless the current human task explicitly asks for it.

### 5.4 Optional Server: GitHub Read-Only

Configure GitHub MCP only if credentials are already available through the approved local mechanism and the human has authorized GitHub access for the task.

Allowed:

- Read issues.
- Read pull requests.
- Read workflow status.
- Read repository metadata.

Forbidden unless explicitly approved:

- Publishing reports.
- Creating releases.
- Editing branch protections.
- Deleting branches.
- Force-pushing.
- Writing secrets.
- Opening external submission records.
- Posting candidate claims publicly.

---

## 6. Forbidden MCP Capabilities

Do not configure MCP tools that allow:

- arbitrary shell execution;
- unrestricted filesystem access;
- package installation outside `.venv`;
- credential reading, printing, exporting, or modification;
- live provider access by default;
- large data ingestion by default;
- Breakthrough Listen raw or reduced radio data commits;
- HDF5, filterbank, large FITS, bulk catalog dump, downloaded survey-image, or generated intermediate-product commits;
- live-provider metadata cache commits;
- external submission enablement;
- unsupported claims of discovery or confirmation;
- use of `alien signal` or similar sensational language in generated reports;
- bypassing failing tests;
- editing scoring thresholds or pathway rules without documenting the decision;
- treating target priority, review readiness, or cross-track references as evidence of a technosignature.

---

## 7. Live Provider Policy

Default MCP operation is offline and fixture-backed.

Live provider access is allowed only when all of the following are true:

1. The current human task explicitly asks for live provider access.
2. The provider is named: Breakthrough Listen, MAST, Gaia, NASA/IPAC IRSA, VizieR, SIMBAD, WISE, AllWISE, CatWISE, 2MASS, or another specific archive.
3. Query scope, cache location, provider terms, and rate limits are documented.
4. Any provider cache remains ignored and reproducible from recorded request provenance.
5. Credentials are referenced by environment variable or approved local secret store, never pasted into config.
6. Tests that require live data remain marked `integration_live` and are not part of default validation.
7. Outputs remain candidate-review artifacts, not discovery claims.

MCP must never turn synthetic fixture tests into live provider calls by silently changing config.

---

## 8. Secrets, Data, And Cache Policy

Never store secrets in:

```text
.mcp.json
.codex/config.toml
AGENTS.md
MCP_BOOTSTRAP.md
docs/
tests/
examples/
```

Never commit:

```text
.venv/
.env
data/raw/
data/interim/
data/external/
cache/live_providers/
cache/catalog_metadata/
large HDF5 files
filterbank files
large FITS files
downloaded survey images
bulk catalog dumps
generated intermediate products
API tokens
private credentials
```

Allowed local cache references:

```text
env:TECHNO_SEARCH_LIVE_CACHE_DIR
env:TECHNO_SEARCH_CATALOG_CACHE_DIR
cache/live_providers/       # ignored local artifact
cache/catalog_metadata/     # ignored local artifact
```

Small synthetic fixtures and tiny normalized live metadata fixtures are allowed only if they contain no bulk provider data, no credentials, and no unsupported candidate interpretation.

---

## 9. Generated Configuration Requirements

### 9.1 Claude Code: `.mcp.json`

Generate project-scoped Claude Code MCP configuration in:

```text
.mcp.json
```

Requirements:

- Keep server scope project-local.
- Use environment-variable references for secrets.
- Prefer stdio transports for local guard servers.
- Include only the approved servers from this file.
- Avoid global, user-home, or parent-directory file access.
- Do not include any server that can execute arbitrary shell commands.
- Include comments only if the target format supports them; JSON generally does not.

After writing `.mcp.json`, tell the human that Claude Code may require a one-time project trust / MCP approval prompt before using the servers.

### 9.2 Codex: `.codex/config.toml`

Generate project-scoped Codex MCP configuration in:

```text
.codex/config.toml
```

Requirements:

- Use project-local MCP server entries.
- Keep secrets out of TOML; use environment-variable references only.
- Do not modify global `~/.codex/config.toml`.
- Do not assume application UI settings are the source of truth.
- If Codex CLI syntax has changed, consult current local help or official docs and record any deviation in the handoff.

---

## 10. Validation Procedure

Run the safest available checks in this order:

```bash
git status --short --branch
.venv/bin/python --version
.venv/bin/python -m pytest
.venv/bin/ruff check .
.venv/bin/mypy src
.venv/bin/techno-search validate-all
.venv/bin/techno-search validation-summary
.venv/bin/techno-search operations-readiness-summary
```

Do not run live-provider tests during bootstrap.

Do not generate public-facing claims.

Do not write outputs outside ignored artifact paths unless the current human task explicitly asks.

If any validation fails:

1. Do not hide the failure.
2. Record the exact command and failure summary.
3. Fix only failures directly caused by the MCP bootstrap changes.
4. If the failure predates the bootstrap or is unrelated, report it as an existing blocker.

---

## 11. Acceptance Criteria

The rollout is complete only when all of the following are true:

- `.mcp.json` exists or an existing file was safely merged.
- `.codex/config.toml` exists or an existing file was safely merged.
- Configured MCP servers are limited to project files, safe git inspection, and fixed validation commands.
- No arbitrary shell MCP is configured.
- No secrets are present in config files.
- No live provider access is enabled by default.
- No large data or cache paths are made committable.
- No external submission path is enabled.
- No unsupported technosignature, discovery, or `alien signal` language is generated.
- Default validation commands have been run or blockers are documented.
- The handoff states whether Claude Code and Codex require a one-time trust/approval action.
- No candidate score, pathway, report interpretation, or external-submission status has been changed by this rollout.

---

## 12. Handoff Format

At the end, report:

```text
MCP Bootstrap Handoff — Technosignature Search

Files created/modified:
- ...

Servers configured:
- ...

Validation run:
- command: PASS/FAIL/SKIPPED — note

Live provider status:
- disabled by default

External submission status:
- disabled by default

Language safety status:
- no confirmed-technosignature language
- no alien-signal language

Data/secrets status:
- no secrets stored in repo config
- no large data/caches made committable

Human actions required:
- approve Claude Code project MCP config if prompted
- trust Codex project config if prompted
- provide any needed credentials through environment variables or local secret store only
- explicitly approve any live provider access separately

Known blockers:
- ...
```

Do not claim the repository is scientifically ready for live discovery, external publication, or confirmed technosignature reporting merely because MCP bootstrap succeeded.
