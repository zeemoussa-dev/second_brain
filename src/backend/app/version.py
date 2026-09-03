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

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_VERSION_FILE = _REPO_ROOT / "VERSION"


def get_version() -> str:
    if not _VERSION_FILE.is_file():
        return "0.0.0"
    return _VERSION_FILE.read_text(encoding="utf-8").strip()
