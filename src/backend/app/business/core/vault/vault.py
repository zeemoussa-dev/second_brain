from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Vault:
    """The vault's own overview/stats snapshot -- a singleton, unlike
    every other Core entity (there is exactly one vault). VaultManager's
    other real responsibilities (the index itself, index-filtering
    config, Templates, Entities) don't fit this one shape and are
    exposed as their own dict-returning methods instead of forced
    through this dataclass -- see vault_manager.py's own docstring."""
    total_notes: int
    last_rebuilt_at: str | None
    folder_counts: dict[str, int] = field(default_factory=dict)
