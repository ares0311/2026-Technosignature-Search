# Console Output Design Spec

**Version:** 1.0  
**Source implementation:** `src/techno_search/production_scan.py` → `ProductionConsole`  
**Purpose:** Portable DNA for the live-run terminal UX. Copy this spec to any project
that runs long multi-step jobs and needs a compact, operator-friendly console.

---

## Core Philosophy

1. **Artifacts are the source of truth.** The terminal is a progress indicator, not a
   log file. Full JSON, provenance, and diagnostic detail belong in files under a run
   directory. Never stream large payloads to stdout.

2. **One line per event.** Each lifecycle event (step start, step done, skip, warn,
   interrupt) produces at most one line in the plain-text fallback and at most one
   status replacement or table row in Rich mode. No multi-paragraph inline output.

3. **Alive proof without noise.** A spinner (Rich) or a single `... <label>` prefix
   (fallback) proves the process is running. The spinner disappears and is replaced by
   an `OK <label> (<elapsed>s)` line when done. The operator can tell the job is alive
   and how long each step took without scrolling.

4. **Graceful degradation.** Rich is a soft dependency wrapped in a `try/import`. If it
   is absent, every behaviour falls back to plain `print()` lines with consistent
   prefixes (`...`, `OK`, `SKIP`, `WARN`, `ERROR`). Tests exercise the fallback path
   deterministically; the Rich path is covered by integration runs.

5. **Ctrl+C is clean.** A `KeyboardInterrupt` writes a `WARN` message naming the exact
   resume command, then re-raises. Completed step artifacts remain on disk. No partial
   writes are left without a warning.

---

## Lifecycle Prefixes (plain-text fallback)

| Prefix  | Meaning                                      | Example                                    |
|---------|----------------------------------------------|--------------------------------------------|
| `...`   | Step started, work in progress               | `... validate-all`                         |
| `OK`    | Step completed successfully                  | `OK validate-all (2.3s)`                  |
| `SKIP`  | Step skipped; artifact already exists        | `SKIP validate-all (existing artifact)`   |
| `WARN`  | Non-fatal operator notice                    | `WARN Interrupted by operator. Re-run...` |
| `ERROR` | Fatal pre-flight failure; no run was started | `ERROR no candidate manifests found in …` |
| `Done`  | Run-level completion summary                 | `Done RUN-2026-…: 5 target(s), 1 follow-up candidate target(s).` |

---

## Rich Mode Behaviours

| Event              | Rich behaviour                                              |
|--------------------|-------------------------------------------------------------|
| Step in progress   | `console.status(label, spinner="dots")` — replaces in place |
| Step done          | Status context exits; `OK <label> (<elapsed>s)` is printed  |
| Step skipped       | Plain `SKIP <label> (existing artifact)` line               |
| Warn               | Plain `WARN <message>` line                                 |
| Completion table   | `rich.table.Table` with one row per evaluated target        |

Rich is imported lazily at module load with a `try/except ImportError`. Both
`RichConsole` and `RichTable` are guarded by `is not None` checks before use.

---

## Header Block

Printed once at run start, before any steps:

```
Production scan <run_id>
Artifacts: <run_dir>
Guardrail: local scheduling aid only; no detection or submission claim.
```

The guardrail line is mandatory. It prevents the terminal from being misread as
authoritative output.

---

## Step Contract

Every unit of work is wrapped in `ProductionConsole.step(label)`:

```python
@contextmanager
def step(self, label: str) -> Iterator[None]:
    started = time.monotonic()
    if self._rich_console is not None:
        with self._rich_console.status(label, spinner="dots"):
            yield
    else:
        self.write(f"... {label}")
        yield
    elapsed = time.monotonic() - started
    self.write(f"OK {label} ({elapsed:.1f}s)")
```

Rules:
- The label is a short human-readable step name, not a command string.
- Elapsed time is always printed in seconds with one decimal place.
- No output is emitted inside the `yield` body. Side effects write to files only.
- If the step is skipped (artifact exists), call `console.skipped(label)` instead and
  return early without entering the context manager.

---

## Skip Contract

```python
def skipped(self, label: str) -> None:
    self.write(f"SKIP {label} (existing artifact)")
```

A step is skipped when its output artifact already exists on disk. This is the
`--resume-run-dir` mechanism: re-running with the same run directory replays only
missing steps. The skip message names the step, not the artifact path, to keep lines
short.

---

## Completion Table

After all steps finish, a table is printed with one row per evaluated target:

| Column      | Content                                           |
|-------------|---------------------------------------------------|
| `Index`     | Sequential index (string, e.g. `"001"`)           |
| `Target`    | Target name (e.g. `"HIP66704"`)                   |
| `Kind`      | Track or target kind (e.g. `"radio"`)             |
| `Follow-up` | `"yes"` or `"no"`                                 |
| `Score`     | Composite score formatted to 3 decimal places     |
| `Pathway`   | Top recommended pathway string                    |

In fallback mode the same fields are printed pipe-separated on one line per target:

```
001 | HIP66704 | radio | follow-up=no | score=0.000 | do_not_submit_false_positive
```

---

## Interrupt Handling

```python
except KeyboardInterrupt:
    interrupted = True
    console.warn(
        "Interrupted by operator. Re-run with "
        f"`prod-scan --resume-run-dir {resolved_run_dir}` to continue."
    )
    # load partial target status from disk, fall through to result
```

Rules:
- Never silence `KeyboardInterrupt`. Re-raise it after cleanup.
- Completed step artifacts remain on disk and are reusable on resume.
- The warn message names the exact command to resume.

---

## Run-Level Completion Line

```
Done <run_id>: <N> target(s), <M> follow-up candidate target(s).
```

Printed once at the end of a successful (non-interrupted) run. Uses natural-language
counts so the operator can assess the run at a glance without reading JSON.

---

## What Must Never Appear in the Terminal

- Raw JSON blobs (use `console.write()` only for short status strings).
- File paths longer than necessary (prefer relative paths or run-dir references).
- Stack traces or exception messages (handle errors inside steps and write to artifacts).
- Progress percentages or ETA estimates (step timing is sufficient).
- Repetitive per-item lines during a step (aggregate into the completion table).

---

## Porting Checklist

When applying this spec to a new project:

- [ ] Create a `Console` class with `step()`, `skipped()`, `warn()`, `write()` methods.
- [ ] Wrap Rich import in `try/except ImportError`; guard every Rich call with `is not None`.
- [ ] Use `time.monotonic()` for elapsed; format as `f"({elapsed:.1f}s)"`.
- [ ] Print a guardrail line in `print_header()` appropriate to the domain.
- [ ] Implement `--resume-run-dir` (skip steps whose artifact exists).
- [ ] Catch `KeyboardInterrupt`, print resume command via `warn()`, re-raise.
- [ ] Emit a completion table (Rich `Table` or pipe-separated fallback) after all steps.
- [ ] Print a single `Done <run_id>: …` summary line at the end.
- [ ] Never call `console.write()` inside a step's `yield` body.
- [ ] Test the fallback path (Rich absent) in automated tests.
