from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Vault:
    total_notes: int
    last_rebuilt_at: str | None
    folder_counts: dict[str, int] = field(default_factory=dict)
