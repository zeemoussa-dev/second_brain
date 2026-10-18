"""Raw data access for seed/blank-data files -- files under
`<SECOND_BRAIN_DATA_PATH>` that a Skill needs to exist before it first runs
(e.g. a plugin's `Settings/<store>.md`). Zero business interpretation: which
files are seed data, and when one is written, is decided by the caller.
"""
from __future__ import annotations

import os
import threading
import time
from pathlib import Path

from app.config import settings

_REPLACE_ATTEMPTS = 5


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
    """Atomic: the new content goes to a temporary file beside the target, which
    then replaces it in one step. Writing in place left a half-written file when
    the backend stopped mid-write, and a plugin reads a broken file as empty --
    a 27 MB cache of synced history is lost that way (2026-10-18)."""
    path = _path(relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    try:
        with open(temporary, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        _replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _replace(source: Path, target: Path) -> None:
    # OneDrive and antivirus hold a file open for a moment after it changes, and
    # Windows refuses to replace an open file; the lock is gone within a second.
    for attempt in range(_REPLACE_ATTEMPTS):
        try:
            os.replace(source, target)
            return
        except PermissionError:
            if attempt == _REPLACE_ATTEMPTS - 1:
                raise
            time.sleep(0.1 * 2 ** attempt)
