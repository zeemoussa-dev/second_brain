from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Skill:
    id: str  # "<category>/<slug>"
    name: str
    description: str
    category: str
    mutates: bool = True
