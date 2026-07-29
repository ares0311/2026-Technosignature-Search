"""Persistent slash-command shell for the canonical Techno-Hunter lifecycle."""

from __future__ import annotations

import argparse
import os
import shlex
import sys
import threading
import time
from collections.abc import Callable, Sequence
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.text import Text

from techno_search import __version__
from techno_search.hunter_cli import (
    create_new_search,
    run_new_search,
    show_follow_ups,
)

try:  # readline is optional on some Python platforms.
    import readline
except ImportError:  # pragma: no cover - platform-specific fallback
    readline = None  # type: ignore[assignment]


SHELL_DISCLAIMER = (
    "Local scientific triage only — no detection, discovery, expert-review, "
    "external-validation, or submission claim."
)
REQUIRED_COMMANDS = (
    "/Create-New-Search",
    "/Run-New-Search",
    "/Show-Follow-Ups",
    "/New-Search",
    "/Follow-Up-Search",
    "/Run-Search",
    "/Help",
    "/Exit",
)
_COMMAND_ALIASES = {
    "/": "/help",
    "/help": "/help",
    "/exit": "/exit",
    "/quit": "/exit",
    "/new-search": "/new-search",
    "/create-new-search": "/create-new-search",
    "/follow-up-search": "/follow-up-search",
    "/run-search": "/run-search",
    "/run-new-search": "/run-search",
    "/show-follow-ups": "/show-follow-ups",
}
_SIGNAL_FRAMES = (
    "▁▂▄▆█▆▄▂▁",
    "▂▄▆█▆▄▂▁▂",
    "▄▆█▆▄▂▁▂▄",
    "▆█▆▄▂▁▂▄▆",
    "█▆▄▂▁▂▄▆█",
    "▆▄▂▁▂▄▆█▆",
)

CommandHandler = Callable[[Sequence[str] | None], int]


@dataclass(frozen=True)
class CommandHandlers:
    """Canonical one-shot adapters used by the persistent shell."""

    create: CommandHandler = create_new_search
    run: CommandHandler = run_new_search
    show_follow_ups: CommandHandler = show_follow_ups


@dataclass(frozen=True)
class DispatchResult:
    """Outcome of one slash command."""

    exit_code: int
    exit_requested: bool = False


class SignalSweep:
    """Technosignature-specific live spectrum animation for real command work."""

    def __init__(self, console: Console, *, enabled: bool) -> None:
        self.console = console
        self.enabled = enabled
        self._label = "Tuning array"
        self._frame_index = 0
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._live: Live | None = None

    def __enter__(self) -> SignalSweep:
        if not self.enabled:
            return self
        self._live = Live(
            self._render(),
            console=self.console,
            refresh_per_second=12,
            transient=True,
            redirect_stdout=True,
            redirect_stderr=True,
        )
        self._live.start()
        self._thread = threading.Thread(
            target=self._animate,
            name="techno-hunter-signal-sweep",
            daemon=True,
        )
        self._thread.start()
        return self

    def __exit__(self, *_args: object) -> None:
        if not self.enabled:
            return
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        if self._live is not None:
            self._live.stop()

    def event(self, label: str) -> None:
        """Update the animation label from a real lifecycle event."""
        self._label = label
        if self._live is not None:
            self._live.update(self._render(), refresh=True)
        elif not self.enabled:
            self.console.print(f"... {label}", style="cyan")

    def _animate(self) -> None:
        while not self._stop.wait(0.09):
            self._frame_index = (self._frame_index + 1) % len(_SIGNAL_FRAMES)
            if self._live is not None:
                self._live.update(self._render(), refresh=True)

    def _render(self) -> Text:
        return Text.assemble(
            ("  ≋ ", "bold cyan"),
            (_SIGNAL_FRAMES[self._frame_index], "bright_magenta"),
            (f"  {self._label}", "cyan"),
        )


class HunterShell:
    """Parse slash commands and delegate to the canonical Hunter entry points."""

    def __init__(
        self,
        *,
        handlers: CommandHandlers | None = None,
        stdin: TextIO = sys.stdin,
        stdout: TextIO = sys.stdout,
        stderr: TextIO = sys.stderr,
        interactive: bool | None = None,
        no_animation: bool = False,
        no_color: bool = False,
        history_path: Path = Path("artifacts/techno_hunter_history"),
    ) -> None:
        self.handlers = handlers or CommandHandlers()
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.interactive = (
            bool(stdin.isatty() and stdout.isatty())
            if interactive is None
            else interactive
        )
        terminal_capable = bool(
            self.interactive
            and stdout.isatty()
            and os.environ.get("TERM", "") != "dumb"
        )
        color_enabled = terminal_capable and not no_color and "NO_COLOR" not in os.environ
        reduce_motion = bool(
            os.environ.get("REDUCE_MOTION")
            or os.environ.get("TECHNO_HUNTER_REDUCE_MOTION")
            or os.environ.get("CI")
        )
        self.animation_enabled = bool(
            terminal_capable and not no_animation and not reduce_motion
        )
        self.console = Console(
            file=stdout,
            color_system="auto" if color_enabled else None,
            highlight=False,
        )
        self.history_path = history_path

    def run(self, commands: Sequence[str] = ()) -> int:
        """Run explicit commands, piped commands, or the persistent prompt."""
        if commands:
            return self._run_lines(commands)
        if not self.interactive:
            return self._run_lines(self.stdin)

        self._configure_readline()
        self._print_banner()
        exit_code = 0
        try:
            while True:
                try:
                    line = input("TechnoHunter> ")
                except EOFError:
                    self.console.print()
                    break
                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Command cancelled; search state is unchanged.[/]")
                    continue
                result = self.dispatch(line)
                exit_code = result.exit_code
                if result.exit_requested:
                    break
        finally:
            self._save_history()
        return exit_code

    def dispatch(self, line: str) -> DispatchResult:
        """Execute one slash command without duplicating scientific logic."""
        stripped = line.strip()
        if not stripped:
            return DispatchResult(0)
        try:
            tokens = shlex.split(stripped)
        except ValueError as exc:
            self._error(f"could not parse command: {exc}")
            return DispatchResult(1)
        raw_command = tokens[0].casefold()
        command = _COMMAND_ALIASES.get(raw_command)
        if command is None:
            self._error(
                f"unknown command {tokens[0]!r}; type / or /Help to list commands"
            )
            return DispatchResult(1)
        if command == "/help":
            self._print_help()
            return DispatchResult(0)
        if command == "/exit":
            self.console.print("Array idle. Durable searches remain on disk.", style="dim")
            return DispatchResult(0, exit_requested=True)
        if command == "/create-new-search":
            return DispatchResult(self._dispatch_canonical_create(tokens[1:]))
        if command == "/new-search":
            return DispatchResult(self._dispatch_create(tokens[1:], mode="new"))
        if command == "/follow-up-search":
            return DispatchResult(self._dispatch_create(tokens[1:], mode="follow-up"))
        if command == "/run-search":
            return DispatchResult(self._dispatch_run(tokens[1:]))
        return DispatchResult(self._dispatch_show(tokens[1:]))

    def complete(self, text: str, state: int) -> str | None:
        """Return readline completions for the required slash commands."""
        prefix = text.casefold()
        matches = [
            command + " "
            for command in REQUIRED_COMMANDS
            if command.casefold().startswith(prefix)
        ]
        return matches[state] if state < len(matches) else None

    def _run_lines(self, lines: Sequence[str] | TextIO) -> int:
        exit_code = 0
        for line in lines:
            result = self.dispatch(line)
            exit_code = result.exit_code
            if result.exit_requested or exit_code != 0:
                break
        return exit_code

    def _dispatch_create(self, args: list[str], *, mode: str) -> int:
        if not args or args[0].startswith("-"):
            self._error(
                f"{'/New-Search' if mode == 'new' else '/Follow-Up-Search'} "
                "requires a positive target count"
            )
            return 1
        try:
            count = int(args[0])
        except ValueError:
            self._error(f"target count must be an integer, got {args[0]!r}")
            return 1
        if count <= 0:
            self._error("target count must be positive")
            return 1
        command_args = ["--targets", str(count), "--mode", mode, *args[1:]]
        label = (
            "Adaptive discovery → identity/history → new-target ranking"
            if mode == "new"
            else "Durable evidence → follow-up value ranking"
        )
        with SignalSweep(self.console, enabled=self.animation_enabled) as sweep:
            sweep.event(label)
            return self.handlers.create(command_args)

    def _dispatch_canonical_create(self, args: list[str]) -> int:
        with SignalSweep(self.console, enabled=self.animation_enabled) as sweep:
            sweep.event("Candidate pool → deterministic ranking → immutable manifest")
            return self.handlers.create(list(args))

    def _dispatch_run(self, args: list[str]) -> int:
        command_args = list(args)
        if command_args and not command_args[0].startswith("-"):
            command_args = ["--search-id", command_args[0], *command_args[1:]]
        self._animate_transition("Authenticating immutable search → signal pipeline")
        return self.handlers.run(command_args)

    def _dispatch_show(self, args: list[str]) -> int:
        return self.handlers.show_follow_ups(args)

    def _animate_transition(self, label: str) -> None:
        if not self.animation_enabled:
            return
        with SignalSweep(self.console, enabled=True) as sweep:
            sweep.event(label)
            time.sleep(0.45)

    def _print_banner(self) -> None:
        self.console.print(
            Text.assemble(
                ("≋ ", "bold cyan"),
                ("TechnoHunter", "bold bright_magenta"),
                (f" v{__version__}", "cyan"),
            )
        )
        self.console.print(SHELL_DISCLAIMER, style="dim")
        self.console.print("Type / and press Tab, or enter /Help.", style="cyan")

    def _print_help(self) -> None:
        table = Table(title="TechnoHunter commands", show_header=True)
        table.add_column("Command", style="bold cyan", no_wrap=True)
        table.add_column("Purpose", overflow="fold")
        table.add_row(
            "/Create-New-Search --targets N --mode new|follow-up [options]",
            "Canonical selection command; freeze the exact ranked targets.",
        )
        table.add_row(
            "/Run-New-Search --search-id SEARCH-ID [options]",
            "Canonical execution command; run the exact pending search.",
        )
        table.add_row("/Show-Follow-Ups [options]", "Show actionable durable follow-ups.")
        table.add_row(
            "/New-Search <N> [options]",
            "Convenience alias for a canonical new-target search.",
        )
        table.add_row(
            "/Follow-Up-Search <N> [options]",
            "Convenience alias for a canonical follow-up search.",
        )
        table.add_row(
            "/Run-Search [SEARCH-ID] [options]",
            "Convenience alias for canonical exact-search execution.",
        )
        table.add_row("/Help", "Show this command table.")
        table.add_row("/Exit", "Exit without changing durable search state.")
        self.console.print(table)
        self.console.print(
            "Options after a slash command are the same as its one-shot executable. "
            "Use --json for machine-readable output.",
            style="dim",
        )

    def _configure_readline(self) -> None:
        if readline is None:
            return
        readline.set_completer(self.complete)
        readline.set_completer_delims(" \t\n")
        readline.parse_and_bind("tab: complete")
        if self.history_path.is_file():
            with suppress(OSError):
                readline.read_history_file(self.history_path)

    def _save_history(self) -> None:
        if readline is None:
            return
        try:
            self.history_path.parent.mkdir(parents=True, exist_ok=True)
            readline.set_history_length(500)
            readline.write_history_file(self.history_path)
        except OSError as exc:
            self._error(f"could not persist command history: {exc}")

    def _error(self, message: str) -> None:
        print(f"ERROR: {message}", file=self.stderr)


def main(
    argv: Sequence[str] | None = None,
    *,
    stdin: TextIO = sys.stdin,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    """Launch the persistent shell or execute scriptable slash commands."""
    parser = argparse.ArgumentParser(prog="Techno-Hunter")
    parser.add_argument(
        "--command",
        action="append",
        default=[],
        help="Execute one slash command non-interactively (repeatable).",
    )
    parser.add_argument("--no-animation", action="store_true")
    parser.add_argument("--no-color", action="store_true")
    parser.add_argument(
        "--history-file",
        type=Path,
        default=Path("artifacts/techno_hunter_history"),
    )
    parser.add_argument(
        "--acceptance-work-dir",
        type=Path,
        help=(
            "Run the fresh-state controlled PROD acceptance harness in this "
            "directory instead of opening the operator shell."
        ),
    )
    parser.add_argument(
        "--acceptance-evidence",
        type=Path,
        help="Write the portable controlled PROD acceptance evidence bundle here.",
    )
    args = parser.parse_args(argv)
    if bool(args.acceptance_work_dir) != bool(args.acceptance_evidence):
        parser.error(
            "--acceptance-work-dir and --acceptance-evidence must be supplied together"
        )
    if args.acceptance_work_dir is not None:
        from techno_search.hunter_acceptance import run_controlled_prod_acceptance

        return run_controlled_prod_acceptance(
            work_dir=args.acceptance_work_dir,
            evidence_path=args.acceptance_evidence,
            stdout=stdout,
            stderr=stderr,
        )
    shell = HunterShell(
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
        no_animation=args.no_animation,
        no_color=args.no_color,
        history_path=args.history_file,
    )
    return shell.run(args.command)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
