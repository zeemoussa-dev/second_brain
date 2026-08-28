"""Raw data access for Provider definitions (ADR-003's own api ->
business -> data_access layering) -- second_brain_data_path/
agent_providers.json, PLUS the real .env-backed settings this store gets
seeded from on first read. Both are real external stores this app reads
Provider data out of (2026-08-28 correction: reading raw credential/
endpoint/model VALUES out of app.config.settings is exactly the same
class of I/O as reading the JSON file, so it belongs here too, not
inlined in ProviderManager -- a structural PATH read, like
settings.second_brain_data_path elsewhere, is not the same thing as
reading an entity's own real data values). ProviderManager still decides
WHEN to seed (only on a genuinely empty store) and owns the Provider
shape -- this file has zero business interpretation, just the two real
stores. Replaces vault_writer.py's own load_providers_state/
save_providers_state (vault_writer.py is a retirement target; a new
Manager owning its own data_access module rather than adding itself as
one more caller of it)."""
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


def seed_defaults() -> dict:
    """The real default Provider set, sourced from this app's own
    .env-backed settings -- Compass and Anthropic Claude, the two
    providers this install always knows about out of the box. Pure
    read of the settings store, no file I/O -- ProviderManager decides
    if/when this is actually persisted via save_state."""
    return {
        "providers": [
            {
                "id": "compass", "name": "Compass",
                "endpoint": settings.compass_base_url,
                "credential": settings.compass_api_key,
                "model": settings.compass_model,
            },
            {
                "id": "anthropic-claude", "name": "Anthropic Claude",
                "endpoint": "https://api.anthropic.com",
                "credential": settings.anthropic_api_key,
                "model": settings.anthropic_model,
            },
        ]
    }
