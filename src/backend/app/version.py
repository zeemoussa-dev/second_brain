"""Reads the repo-root `VERSION` file -- the single source of truth for
Second Brain's own version number (2026-09-03, operator: "I want to have
the current version number in the UI"). Semver (MAJOR.MINOR.PATCH):
MAJOR = a breaking change (read CHANGELOG.md before assuming a pulled
update just works), MINOR = a new feature, PATCH = a fix. Bumped by hand
alongside every real push, together with a CHANGELOG.md entry -- no
automated bump here, by design (2026-09-03 operator instruction covers
both, not a build-time computed value).
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_VERSION_FILE = _REPO_ROOT / "VERSION"


def get_version() -> str:
    if not _VERSION_FILE.is_file():
        return "0.0.0"
    return _VERSION_FILE.read_text(encoding="utf-8").strip()


def _read_checkout_commit() -> str | None:
    git = shutil.which("git")
    if git is None:
        return None
    try:
        result = subprocess.run(
            [git, "rev-parse", "HEAD"], cwd=_REPO_ROOT, capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


# Read once, when this process loads the code -- not per request. A backend that
# kept serving after a pull then reports the commit it is actually running, which
# is how `tools\backend.cmd` tells a stale process from a current one (`BUG-068`).
_LOADED_COMMIT = _read_checkout_commit()


def get_loaded_commit() -> str | None:
    """The commit this process's code was loaded from; None outside a git checkout."""
    return _LOADED_COMMIT
