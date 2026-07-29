from __future__ import annotations

from io import StringIO
from pathlib import Path

from techno_search.hunter_shell import (
    REQUIRED_COMMANDS,
    CommandHandlers,
    HunterShell,
)


class _Recorder:
    def __init__(self, exit_code: int = 0) -> None:
        self.calls: list[list[str]] = []
        self.exit_code = exit_code

    def __call__(self, argv: object = None) -> int:
        self.calls.append(list(argv or []))  # type: ignore[arg-type]
        return self.exit_code


def _shell(
    tmp_path: Path,
) -> tuple[HunterShell, _Recorder, _Recorder, _Recorder, StringIO, StringIO]:
    create = _Recorder()
    run = _Recorder()
    show = _Recorder()
    stdout = StringIO()
    stderr = StringIO()
    shell = HunterShell(
        handlers=CommandHandlers(create=create, run=run, show_follow_ups=show),
        stdin=StringIO(),
        stdout=stdout,
        stderr=stderr,
        interactive=False,
        history_path=tmp_path / "history",
    )
    return shell, create, run, show, stdout, stderr


def test_slash_autocomplete_exposes_required_workflow(tmp_path: Path) -> None:
    shell, *_ = _shell(tmp_path)

    matches: list[str] = []
    state = 0
    while (match := shell.complete("/", state)) is not None:
        matches.append(match.strip())
        state += 1

    assert matches == list(REQUIRED_COMMANDS)


def test_new_and_follow_up_commands_delegate_to_canonical_create(
    tmp_path: Path,
) -> None:
    shell, create, *_ = _shell(tmp_path)

    assert shell.dispatch("/New-Search 12 --target-prefix HIP").exit_code == 0
    assert shell.dispatch("/Follow-Up-Search 3 --json").exit_code == 0

    assert create.calls == [
        ["--targets", "12", "--mode", "new", "--target-prefix", "HIP"],
        ["--targets", "3", "--mode", "follow-up", "--json"],
    ]


def test_canonical_create_command_preserves_exact_cli_contract(tmp_path: Path) -> None:
    shell, create, *_ = _shell(tmp_path)

    assert (
        shell.dispatch("/Create-New-Search --targets 12 --mode new --json").exit_code
        == 0
    )
    assert (
        shell.dispatch(
            "/Create-New-Search --targets 3 --mode follow-up --target-prefix HIP"
        ).exit_code
        == 0
    )

    assert create.calls == [
        ["--targets", "12", "--mode", "new", "--json"],
        [
            "--targets",
            "3",
            "--mode",
            "follow-up",
            "--target-prefix",
            "HIP",
        ],
    ]


def test_run_and_follow_up_view_delegate_without_regenerating_targets(
    tmp_path: Path,
) -> None:
    shell, _create, run, show, *_ = _shell(tmp_path)

    assert (
        shell.dispatch(
            "/Run-Search SEARCH-20260727T120000Z-ABCDEF12 --approve-acquisition"
        ).exit_code
        == 0
    )
    assert shell.dispatch("/Show-Follow-Ups --json").exit_code == 0

    assert run.calls == [
        [
            "--search-id",
            "SEARCH-20260727T120000Z-ABCDEF12",
            "--approve-acquisition",
        ]
    ]
    assert show.calls == [["--json"]]


def test_canonical_run_command_preserves_exact_cli_contract(tmp_path: Path) -> None:
    shell, _create, run, *_ = _shell(tmp_path)

    assert (
        shell.dispatch(
            "/Run-New-Search --search-id SEARCH-20260727T120000Z-ABCDEF12"
        ).exit_code
        == 0
    )

    assert run.calls == [["--search-id", "SEARCH-20260727T120000Z-ABCDEF12"]]


def test_help_and_bare_slash_are_discoverable(tmp_path: Path) -> None:
    shell, *_rest, stdout, _stderr = _shell(tmp_path)

    assert shell.dispatch("/").exit_code == 0
    output = stdout.getvalue()

    for command in REQUIRED_COMMANDS:
        assert command in output
    assert "--json" in output


def test_useful_errors_do_not_exit_the_persistent_shell(tmp_path: Path) -> None:
    shell, create, *_rest, stderr = _shell(tmp_path)

    unknown = shell.dispatch("/Launch-Probe 4")
    missing_count = shell.dispatch("/New-Search")

    assert unknown.exit_code == 1
    assert not unknown.exit_requested
    assert missing_count.exit_code == 1
    assert not create.calls
    assert "unknown command" in stderr.getvalue()
    assert "requires a positive target count" in stderr.getvalue()


def test_exit_requests_clean_shell_shutdown(tmp_path: Path) -> None:
    shell, *_ = _shell(tmp_path)

    result = shell.dispatch("/Exit")

    assert result.exit_code == 0
    assert result.exit_requested


def test_redirected_operation_disables_color_and_animation(tmp_path: Path) -> None:
    shell, *_ = _shell(tmp_path)

    assert not shell.interactive
    assert not shell.animation_enabled
    assert not shell.console.is_terminal


def test_scripted_commands_stop_on_first_failure(tmp_path: Path) -> None:
    create = _Recorder(exit_code=2)
    run = _Recorder()
    shell = HunterShell(
        handlers=CommandHandlers(create=create, run=run, show_follow_ups=_Recorder()),
        stdin=StringIO(),
        stdout=StringIO(),
        stderr=StringIO(),
        interactive=False,
        history_path=tmp_path / "history",
    )

    exit_code = shell.run(
        [
            "/New-Search 1",
            "/Run-Search SEARCH-20260727T120000Z-ABCDEF12",
        ]
    )

    assert exit_code == 2
    assert len(create.calls) == 1
    assert not run.calls
