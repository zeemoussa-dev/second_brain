"""Raw data access for seed/blank-data files -- files under
`<SECOND_BRAIN_DATA_PATH>` that a Skill needs to exist before it first runs
(e.g. a plugin's `Settings/<store>.md`). Zero business interpretation: which
files are seed data, and when one is written, is decided by the caller.
"""
from __future__ import annotations

from pathlib import Path

from app.config import settings


def _path(relative_path: str) -> Path:
    if settings.second_brain_data_path is None:
        raise FileNotFoundError("No App Database Folder is configured")
    return Path(settings.second_brain_data_path) / relative_path


def exists(relative_path: str) -> bool:
    return _path(relative_path).exists()


def write_blank(relative_path: str) -> None:
    write_text(relative_path, "")


def read_text(relative_path: str) -> str | None:
    """None when the file does not exist yet."""
    path = _path(relative_path)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8-sig")


def write_text(relative_path: str, content: str) -> None:
    path = _path(relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
