"""A failed toolsets read is not "nothing enabled" (`REQ-SB-99-US-01`, `ADR-043`).

`cli.list_tools()` returns `{}` when `hermes tools list` fails and `{}` when the
profile really has nothing enabled, so a screen built on it says "no toolsets
enabled" when the truth is "we could not find out" -- the class of dishonesty
`BUG-085` (a job reporting `ok` for four days while capture was dead) and
`BUG-088` (a refused plugin rendering as a broken page) were both about. This
pins the three outcomes `read_tools()` now keeps apart: enabled set, empty set,
and could-not-read with the real reason.

What is pinned: the mapping parsed off the real 2026-08-29 output shape, with
the `MCP servers:` lines excluded; `list_tools()` unchanged in name, signature
and value for its three existing callers; the `-p <profile>` targeting, and
`None`/`default` taking no flag at all; and the cost -- one call is exactly one
subprocess with exactly that argv, and a failing read is returned rather than
retried (`BUG-086` is the measured precedent for a per-profile subprocess that
nobody counted).

No test here touches the operator's real install: `subprocess.run`/`Popen` are
refused for the whole file by an autouse fixture, the semantic tests replace
`_run` outright, and the two cost tests point the executable at a path under
`tmp_path`. Both seams of conftest's suite-wide sandbox are asserted rather
than assumed, in the last two tests -- including the `shutil.which("hermes")`
fallback that a sandboxed `HERMES_HOME` alone does not close.
"""
from __future__ import annotations

import shutil
import subprocess

import pytest

from app.config import settings
from app.hermes.cli import HermesCLI
from app.hermes.config import HermesConfig

# Captured at import time, before conftest's autouse fixture replaces it with
# the sandbox's None -- the real resolver, needed to prove which seam of that
# sandbox does what.
_REAL_HERMES_EXE = HermesCLI._hermes_exe

PROFILE = "adnoc-expert"

# `hermes tools list`'s own real output shape (2026-08-29): a checkmark per
# toolset under two sections, then an `MCP servers:` section whose lines carry
# no checkmark and are therefore not toolsets at all.
REAL_TOOLS_LIST_OUTPUT = """Built-in toolsets:
  ✓ enabled  web  🔍 Web Search & Scraping
  ✗ disabled  shell  🖥 Shell Commands

Plugin toolsets:
  ✓ enabled  obsidian  📓 Obsidian Vault

MCP servers:
  outlook  all tools enabled
"""

REAL_TOOLSETS = {"web": True, "shell": False, "obsidian": True}

NO_INSTALL_MESSAGE = "No real Hermes install found at the configured home path"


class RecordedRun:
    """Stands in for `HermesCLI._run`, recording the real argv it was handed."""

    def __init__(self, result: tuple[bool, str]) -> None:
        self._result = result
        self.argv: list[list[str]] = []

    def __call__(self, args: list[str], timeout: float = 30.0) -> tuple[bool, str]:
        self.argv.append(list(args))
        return self._result


class RecordedSubprocessRun:
    """Stands in for `subprocess.run`, recording every real spawn attempt."""

    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self._completed = subprocess.CompletedProcess([], returncode, stdout, stderr)
        self.spawns: list[list[str]] = []

    def __call__(self, args: list[str], **kwargs) -> subprocess.CompletedProcess:
        self.spawns.append(list(args))
        self._completed.args = list(args)
        return self._completed


@pytest.fixture(autouse=True)
def no_real_process_escapes_this_file(monkeypatch):
    """The file under test is the one that spawns processes -- refusing both
    entry points by default means a test that forgets its own seam fails
    loudly instead of reaching the operator's install."""

    def refuse(*args, **kwargs):
        raise AssertionError(f"a toolsets test spawned a real process: {args!r}")

    monkeypatch.setattr(subprocess, "run", refuse)
    monkeypatch.setattr(subprocess, "Popen", refuse)


@pytest.fixture()
def cli(tmp_path) -> HermesCLI:
    return HermesCLI(HermesConfig(base_url="http://127.0.0.1:9119", home_path=tmp_path))


# [REQ-SB-99-US-01-AC-03]
def test_a_real_read_reports_what_is_enabled_and_what_is_not(cli):
    cli._run = RecordedRun((True, REAL_TOOLS_LIST_OUTPUT))

    succeeded, toolsets, message = cli.read_tools(PROFILE)

    assert succeeded is True
    assert toolsets == REAL_TOOLSETS
    assert "outlook" not in toolsets, "an MCP server is not a toolset -- it carries no checkmark"
    assert message == "", "a successful read has nothing to report beyond its mapping"


# [REQ-SB-99-US-01-AC-03]
def test_list_tools_returns_exactly_what_the_read_found(cli):
    """`list_tools()` delegates: same name, same signature, same value, so its
    three existing callers are untouched (`ADR-014`'s same-shape extension)."""
    cli._run = RecordedRun((True, REAL_TOOLS_LIST_OUTPUT))

    assert cli.list_tools(PROFILE) == REAL_TOOLSETS
    assert cli.list_tools(PROFILE) == cli.read_tools(PROFILE)[1]


# [REQ-SB-99-US-01-AC-06]
def test_a_failed_read_says_so_and_carries_the_real_reason(cli):
    cli._run = RecordedRun((False, NO_INSTALL_MESSAGE))

    succeeded, toolsets, message = cli.read_tools()

    assert succeeded is False
    assert toolsets == {}, "a failure must never fabricate a toolset"
    assert message == NO_INSTALL_MESSAGE, "the real captured reason, not a rewritten one"


# [REQ-SB-99-US-01-AC-06]
def test_the_existing_callers_still_see_an_empty_mapping_on_failure(cli):
    """The dishonesty is contained, not propagated: `list_tools()` keeps
    returning `{}` on failure exactly as it did before this task."""
    cli._run = RecordedRun((False, NO_INSTALL_MESSAGE))

    assert cli.list_tools() == {}


# [REQ-SB-99-US-01-AC-06]
def test_nothing_enabled_is_a_successful_read_not_a_failure(cli):
    """The whole point: output matching no toolset line at all is `True, {}` --
    told apart from the failure above by the flag alone, since the mapping and
    `list_tools()`'s value are identical in both cases."""
    cli._run = RecordedRun((True, "No toolsets are enabled for this profile.\n"))

    succeeded, toolsets, message = cli.read_tools()

    assert succeeded is True
    assert toolsets == {}
    assert message == ""
    assert cli.list_tools() == {}, "indistinguishable to the old caller, as intended"


# [REQ-SB-99-US-01-AC-03]
def test_a_named_profile_is_targeted_and_the_root_profile_is_not(cli):
    """`-p` is how a profile other than the root one is reached; `None` and
    `default` both mean `<HERMES_HOME>` itself and take no flag at all."""
    recorded = RecordedRun((True, REAL_TOOLS_LIST_OUTPUT))
    cli._run = recorded

    cli.read_tools(PROFILE)
    cli.read_tools()
    cli.read_tools("default")

    assert recorded.argv == [
        ["-p", PROFILE, "tools", "list"],
        ["tools", "list"],
        ["tools", "list"],
    ]


# [constraint: cost]
def test_one_read_costs_exactly_one_subprocess_with_exactly_that_argv(cli, tmp_path, monkeypatch):
    """`hermes tools list` is a subprocess spawn per profile, and `BUG-086` is
    the measured precedent for a per-profile read whose cost nobody pinned."""
    fake_exe = tmp_path / "bin" / "hermes.exe"
    spawned = RecordedSubprocessRun(0, stdout=REAL_TOOLS_LIST_OUTPUT)
    monkeypatch.setattr(HermesCLI, "_hermes_exe", lambda self: fake_exe)
    monkeypatch.setattr(subprocess, "run", spawned)

    assert cli.read_tools(PROFILE) == (True, REAL_TOOLSETS, "")
    assert spawned.spawns == [[str(fake_exe), "-p", PROFILE, "tools", "list"]]

    spawned.spawns.clear()
    cli.list_tools(PROFILE)
    assert spawned.spawns == [[str(fake_exe), "-p", PROFILE, "tools", "list"]], (
        "delegating must not double the subprocess cost of the existing callers"
    )


# [constraint: cost]
def test_a_failing_read_is_reported_once_and_never_retried(cli, tmp_path, monkeypatch):
    """A retry would turn one unreachable profile into several spawns and would
    still have nothing honest to report at the end of them."""
    fake_exe = tmp_path / "bin" / "hermes.exe"
    spawned = RecordedSubprocessRun(1, stderr="Error: profile 'adnoc-expert' not found\n")
    monkeypatch.setattr(HermesCLI, "_hermes_exe", lambda self: fake_exe)
    monkeypatch.setattr(subprocess, "run", spawned)

    succeeded, toolsets, message = cli.read_tools(PROFILE)

    assert (succeeded, toolsets) == (False, {})
    assert message == "Error: profile 'adnoc-expert' not found"
    assert spawned.spawns == [[str(fake_exe), "-p", PROFILE, "tools", "list"]]


def test_the_sandboxed_install_is_the_honest_failure_path(cli):
    """conftest's sandbox leaves `_hermes_exe()` returning None, which is the
    real "no install" failure -- so the sandbox itself exercises this task's
    failure branch, with no subprocess at all (the autouse fixture above would
    refuse one)."""
    assert cli.read_tools(PROFILE) == (False, {}, NO_INSTALL_MESSAGE)
    assert cli.list_tools(PROFILE) == {}


def test_no_test_here_can_see_the_operators_real_install(tmp_path, monkeypatch):
    """Stated rather than assumed, and specifically the second seam: a
    sandboxed `HERMES_HOME` alone would NOT contain a subprocess, because
    `_hermes_exe()` falls back to whatever `hermes` is on PATH -- the real
    install's own launcher. Here the fallback is asked and answered with None,
    so nothing resolves and nothing spawns."""
    assert not settings.hermes_home_path.exists(), "conftest's sandboxed home must not exist"

    which_queries: list[str] = []

    def record_the_path_lookup_and_find_nothing(name: str) -> str | None:
        which_queries.append(name)
        return None

    monkeypatch.setattr(shutil, "which", record_the_path_lookup_and_find_nothing)
    monkeypatch.setattr(HermesCLI, "_hermes_exe", _REAL_HERMES_EXE)
    home_sandboxed_but_path_not = HermesCLI(
        HermesConfig(base_url="http://127.0.0.1:9119", home_path=tmp_path),
    )

    assert home_sandboxed_but_path_not.read_tools(PROFILE) == (False, {}, NO_INSTALL_MESSAGE)
    assert which_queries == ["hermes"], "the PATH fallback is the seam conftest closes"
    assert not (tmp_path / "bin").exists(), "resolving an executable must create nothing"
