from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Tool:
    id: str
    name: str
    description: str
    icon: str | None = None
