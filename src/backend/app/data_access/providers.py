"""Raw data access for Provider definitions (ADR-003's own api ->
business -> data_access layering) -- second_brain_data_path/
agent_providers.json. Zero business interpretation here (no seeding, no
defaults) -- that's ProviderManager's own job. Replaces vault_writer.py's
own load_providers_state/save_providers_state (vault_writer.py is a
retirement target; a new Manager owning its own data_access module
rather than adding itself as one more caller of it)."""
from __future__ import annotations

import json
from pathlib import Path

from app.config import settings

_STATE_FILE = "agent_providers.json"


def _state_path() -> Path:
    return settings.second_brain_data_path / _STATE_FILE


def load_state() -> dict | None:
    """None if the store has never been written yet."""
    path = _state_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(state: dict) -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")
