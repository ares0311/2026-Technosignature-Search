"""Rich-based terminal UX for technosignature search production scans.

Provides spinner progress display and single-line result output. All outputs
are local triage aids only — no result line constitutes a detection claim or
authorizes external submission.

NOTE on stellar classification: SIMBAD object type codes (otype) are not
currently stored in candidate provenance; classification here uses name-based
heuristics only and is approximate. A future improvement should fetch and
store the SIMBAD otype field in catalog_crossmatch so classification is
reliable across all object classes.
"""

from __future__ import annotations

import re
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any

TUI_DISCLAIMER = (
    "Terminal UX output is a local scheduling aid only. "
    "No result line constitutes a detection claim or authorizes external submission."
)

try:
    from rich.console import Console as _RichConsole
    from rich.live import Live as _Live
    from rich.spinner import Spinner as _Spinner
    from rich.text import Text as _Text

    _RICH = True
except ImportError:  # pragma: no cover
    _RICH = False

# Shared console — one instance avoids interleaving on concurrent use.
_console: Any = _RichConsole(highlight=False) if _RICH else None

# ---------------------------------------------------------------------------
# Stellar classification heuristics
# ---------------------------------------------------------------------------

_GALAXY_RE = re.compile(
    r"\b(galaxy|NGC|UGC|MCG|AGN|Seyfert|quasar|QSO|blazar|LINER)\b"
    r"|\bIC\s+\d",
    re.IGNORECASE,
)
_CLUSTER_RE = re.compile(
    r"\b(star\s+cluster|open\s+cluster|globular\s+cluster|\bOC\b|\bGC\b)\b",
    re.IGNORECASE,
)
_NEBULA_RE = re.compile(
    r"\b(nebula|planetary\s+nebula|\bPN\b|SNR|supernova\s+remnant|HII\s+region)\b",
    re.IGNORECASE,
)
_PULSAR_RE = re.compile(
    r"\b(pulsar|PSR|magnetar|neutron\s+star|millisecond\s+pulsar)\b",
    re.IGNORECASE,
)
_WD_RE = re.compile(r"\b(white\s+dwarf|\bWD\b)\b", re.IGNORECASE)
_BINARY_RE = re.compile(
    r"\b(binary|double\s+star|SB\d?|visual\s+binary|spectroscopic\s+binary|eclipsing)\b",
    re.IGNORECASE,
)
_GIANT_RE = re.compile(
    r"\b(giant|supergiant|AGB|red\s+giant|asymptotic\s+giant)\b",
    re.IGNORECASE,
)
_VARIABLE_RE = re.compile(
    r"\b(variable|Cepheid|RR\s+Lyrae|Mira|BY\s+Dra|Delta\s+Sct|pulsating)\b",
    re.IGNORECASE,
)


def classify_stellar(
    simbad_match_names: str,
    simbad_match_count: int = 0,
    gaia_match_count: int = 0,
) -> str:
    """Return best-effort object classification from available candidate metadata.

    Classification is name-heuristic only (see module docstring for limitation).
    Returns "unknown" when no match names are available and no catalog hit exists.
    """
    names = simbad_match_names or ""
    if not names or names == "none":
        if gaia_match_count > 0:
            return "stellar (Gaia)"
        return "unknown"

    if _CLUSTER_RE.search(names):
        return "star cluster"
    if _GALAXY_RE.search(names):
        return "galaxy/extragalactic"
    if _NEBULA_RE.search(names):
        return "nebula/remnant"
    if _PULSAR_RE.search(names):
        return "neutron star"
    if _WD_RE.search(names):
        return "white dwarf"
    if _BINARY_RE.search(names):
        return "binary star"
    if _GIANT_RE.search(names):
        return "giant star"
    if _VARIABLE_RE.search(names):
        return "variable star"
    return "stellar" if (simbad_match_count > 0 or gaia_match_count > 0) else "unknown"


# ---------------------------------------------------------------------------
# Index generation
# ---------------------------------------------------------------------------


def make_scan_index(target_name: str) -> str:
    """Return a YYYYMMDD-HHMMSS-<TARGET> index string (UTC)."""
    ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", target_name)
    return f"{ts}-{safe}"


# ---------------------------------------------------------------------------
# Score extraction
# ---------------------------------------------------------------------------


def extract_composite_score(candidate_dict: dict[str, Any]) -> float:
    """Extract signal_reality_confidence as the composite display score."""
    scores = candidate_dict.get("scores", {})
    val = scores.get("signal_reality_confidence")
    if val is not None:
        try:
            return float(val)
        except (TypeError, ValueError):
            pass
    return 0.0


def extract_stellar_from_candidate(candidate_dict: dict[str, Any]) -> str:
    """Pull classification fields out of a scored candidate dict."""
    prov = candidate_dict.get("provenance", {})
    names = str(prov.get("simbad_match_names", "none") or "none")
    features = candidate_dict.get("features", {})
    simbad_count = int(features.get("simbad_match_count", 0) or 0)
    gaia_count = int(features.get("gaia_match_count", 0) or 0)
    return classify_stellar(names, simbad_count, gaia_count)


# ---------------------------------------------------------------------------
# Spinner context
# ---------------------------------------------------------------------------

_INDEX_W = 32
_STELLAR_W = 22


@contextmanager
def scan_spinner(label: str) -> Generator[None, None, None]:
    """Show a spinner while the body executes; replace it on exit."""
    if _RICH:
        spinner = _Spinner("dots", text=f"  {label}")
        with _Live(spinner, console=_console, refresh_per_second=12, transient=True):
            yield
    else:
        print(f"  {label}...", end="", flush=True)
        yield
        print()


# ---------------------------------------------------------------------------
# Result line printer
# ---------------------------------------------------------------------------


def print_result_line(
    *,
    index: str,
    stellar: str,
    score: float,
    escalation: bool,
    ok: bool,
    error: str | None = None,
) -> None:
    """Print the single completed-target summary line."""
    if _RICH:
        if ok:
            line = _Text.assemble(
                _Text("✓ ", style="bold green"),
                _Text(f"{index:<{_INDEX_W}}", style="cyan"),
                _Text(f"  {stellar:<{_STELLAR_W}}", style="white"),
                _Text(f"  score={score:.2f}", style="yellow"),
                _Text("  ⚡ ESCALATION", style="bold red")
                if escalation
                else _Text("  —", style="dim"),
            )
        else:
            line = _Text.assemble(
                _Text("✗ ", style="bold red"),
                _Text(f"{index:<{_INDEX_W}}", style="cyan dim"),
                _Text(f"  error: {error or 'pipeline failed'}", style="red"),
            )
        _console.print(line)
    else:
        if ok:
            esc = "⚡ ESCALATION" if escalation else "—"
            print(f"✓ {index:<{_INDEX_W}}  {stellar:<{_STELLAR_W}}  score={score:.2f}  {esc}")
        else:
            print(f"✗ {index:<{_INDEX_W}}  error: {error or 'pipeline failed'}")


# ---------------------------------------------------------------------------
# Header / footer / interrupt helpers
# ---------------------------------------------------------------------------


def print_scan_header(n_targets: int, db_path: str, resume: bool) -> None:
    mode = "resuming" if resume else "fresh"
    msg = f"[dim]Scanning {n_targets} target(s) · mode: {mode} · checkpoint: {db_path}[/dim]"
    if _RICH:
        _console.print(msg)
    else:
        print(f"Scanning {n_targets} target(s) · mode: {mode} · checkpoint: {db_path}")


def print_scan_footer(succeeded: int, failed: int, escalations: int) -> None:
    if _RICH:
        esc_part = f"  [bold red]⚡ {escalations} escalation(s)[/bold red]" if escalations else ""
        _console.print(f"\n[dim]Done: {succeeded} succeeded  {failed} failed{esc_part}[/dim]")
    else:
        esc_part = f"  ⚡ {escalations} escalation(s)" if escalations else ""
        print(f"\nDone: {succeeded} succeeded  {failed} failed{esc_part}")


def print_interrupted() -> None:
    if _RICH:
        _console.print(
            "\n[yellow]Interrupted — restart to resume from last completed target[/yellow]"
        )
    else:
        print("\nInterrupted — restart to resume from last completed target")
