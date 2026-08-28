"""Raw data access for VaultManager's own Customer/Partner discovery
store (ADR-003's own api -> business -> data_access layering) --
second_brain_data_path/Settings/Entities.md. Zero business
interpretation here (no parsing of the `### <heading>` entry format,
no rendering) -- that's VaultManager's own job; this module only reads
and writes the raw file text.
"""
from __future__ import annotations

from pathlib import Path

from app.config import settings


def _entities_path() -> Path:
    return settings.second_brain_data_path / "Settings" / "Entities.md"


def read_raw() -> str | None:
    """None if the store has never been written yet."""
    path = _entities_path()
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8-sig")


def write_raw(content: str) -> None:
    path = _entities_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
