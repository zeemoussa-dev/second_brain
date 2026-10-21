"""Raw data access for this install's branding -- the name it calls
itself and its logo (`REQ-SB-101` follow-on, operator 2026-10-21).

`<SECOND_BRAIN_DATA_PATH>/branding/`: `branding.json` beside the logo
file. Its own top-level child of the config folder, like `auth/`, so
anything that sweeps that folder can include or exclude branding as one
directory rather than a filename pattern.

**The logo keeps its own extension on disk.** One file, `logo.<ext>`,
and the extension IS the record of what the bytes are -- there is no
content-type column to disagree with the file. Replacing a PNG with an
SVG deletes the PNG, so there is never more than one logo and never a
stale one shadowing the current one.

Zero business interpretation, the same contract as every module here:
no default name is applied, no extension is judged acceptable, nothing
is resized or validated. `BrandingManager` owns all of that.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.config import settings

_BRANDING_DIR = "branding"
_RECORD = "branding.json"


def branding_dir() -> Path:
    return settings.second_brain_data_path / _BRANDING_DIR


def branding_path() -> Path:
    return branding_dir() / _RECORD


def branding_exists() -> bool:
    """Whether this install has ever set its branding. Lets the Manager
    tell "never customised, use the product's own name" from "customised
    to an empty string" -- two states an absent file and a blank record
    would otherwise collapse into one."""
    return branding_path().is_file()


def read_branding_json() -> dict:
    """Raises FileNotFoundError if nothing is saved, json.JSONDecodeError
    if it does not parse -- neither swallowed, and an unreadable record
    is never silently replaced with defaults."""
    path = branding_path()
    if not path.is_file():
        raise FileNotFoundError(f"No branding record at {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_branding_json(data: dict) -> None:
    path = branding_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def find_logo() -> Path | None:
    """The one logo file, whatever its extension, or None. Globs rather
    than reading an extension out of the record: the file on disk is the
    truth, and a record naming a logo that was deleted underneath it
    would otherwise serve a 404 as if it were a logo."""
    directory = branding_dir()
    if not directory.is_dir():
        return None
    for candidate in sorted(directory.glob("logo.*")):
        if candidate.is_file():
            return candidate
    return None


def write_logo(suffix: str, content: bytes) -> Path:
    """Writes `logo.<suffix>` and removes any logo of another extension,
    so the glob above can never find two."""
    directory = branding_dir()
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / f"logo{suffix}"
    for existing in directory.glob("logo.*"):
        if existing != destination and existing.is_file():
            existing.unlink()
    destination.write_bytes(content)
    return destination


def delete_logo() -> bool:
    """True when there was one to delete."""
    existing = find_logo()
    if existing is None:
        return False
    existing.unlink()
    return True
