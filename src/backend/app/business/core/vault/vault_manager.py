"""VaultManager -- returns Array<Vault> (or the single business-shaped
Vault representation) to whatever business-logic caller needs it.
Methods not implemented yet (scaffolding only, per operator:
"type_manager as the methods getting to that part later")."""
from __future__ import annotations

from app.business.core.vault.vault import Vault


class VaultManager:
    def get_all(self) -> list[Vault]:
        raise NotImplementedError
