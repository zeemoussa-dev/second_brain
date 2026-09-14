"""What the three lookup scripts all need: the engines, and reading a hub.

Nothing here writes. Everything here answers a question about a company from
the company's own notes, so the agent reports what the vault says instead of
what it remembers from a note it happened to open.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path


def add_engines_to_path() -> None:
    """Find the shared engines whatever layout this runs in.

    In the repo they are `skills/managers/`; deployed, Hermes puts them in
    `<hermes>/managers/` several levels above the flat Skill folder. Searching
    upward for the folder that actually holds vault_manager.py means a caller
    never has to set PYTHONPATH -- an interactive agent cannot."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "managers" / "vault_manager.py"
        if candidate.is_file():
            if str(candidate.parent) not in sys.path:
                sys.path.insert(0, str(candidate.parent))
            return


add_engines_to_path()

import vault_manager as vm  # noqa: E402

DATED = re.compile(r"^- (\d{4}-\d{2}-\d{2}): (.+)$")
OPEN_ACTION = re.compile(r"^- \[ \] (.+)$")


def vault_from(argument: str) -> Path:
    path = (argument or os.environ.get("SECOND_BRAIN_VAULT_PATH") or "").strip()
    if not path:
        raise SystemExit("SECOND_BRAIN_VAULT_PATH is not set and --vault-path was not given")
    return Path(path)


def read(path: Path) -> tuple[dict, str]:
    """Frontmatter and body, or empty ones when the note is not there. A hub
    without a History file yet is a normal state, not an error."""
    if not os.path.isfile(vm.long_path(path)):
        return {}, ""
    try:
        return vm.read_note(path)
    except OSError:
        return {}, ""


def dated_lines(path: Path) -> list[tuple[str, str]]:
    """Every `- YYYY-MM-DD: ...` line, newest first."""
    _, body = read(path)
    found = [m.groups() for line in body.splitlines() if (m := DATED.match(line.strip()))]
    return sorted(found, key=lambda entry: entry[0], reverse=True)


def captured_lines(path: Path) -> list[tuple[str, str]]:
    """Dated lines under `## Captured` only -- never the operator's `## Notes`,
    which is his own handwriting and not ours to report as a vault fact."""
    _, body = read(path)
    lines = body.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == "## Captured")
    except StopIteration:
        return []
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    found = [m.groups() for line in lines[start + 1:end] if (m := DATED.match(line.strip()))]
    return sorted(found, key=lambda entry: entry[0], reverse=True)


def open_actions(hub_md: Path) -> list[str]:
    _, body = read(hub_md)
    lines = body.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == "## Actions")
    except StopIteration:
        return []
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return [m.group(1) for line in lines[start + 1:end] if (m := OPEN_ACTION.match(line.strip()))]


def people_of(hub_md: Path) -> list[dict]:
    folder = hub_md.parent / "People"
    if not folder.is_dir():
        return []
    found = []
    for note in sorted(folder.glob("*.md")):
        frontmatter, _ = read(note)
        if frontmatter.get("type") != "Person":
            continue
        found.append({
            "name": str(frontmatter.get("name") or note.stem),
            "email": str(frontmatter.get("email") or note.stem),
            "role": str(frontmatter.get("role") or ""),
        })
    return found


def history_path(hub_md: Path) -> Path:
    return hub_md.parent / f"{hub_md.stem}-history.md"


def captures_path(hub_md: Path) -> Path:
    return hub_md.parent / f"{hub_md.stem}-captures.md"
