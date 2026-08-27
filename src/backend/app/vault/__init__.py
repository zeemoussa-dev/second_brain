"""Vault Manager -- a Template-driven writer built on top of
app/obsidian/'s raw primitives. `VaultClient` is constructed with a
Template (from app/data_access/templates/) and the vault root, does one
scoped job, then is disposed. `vault_manager.py` is the actual engine
underneath -- kept standalone/stdlib-only since it is also physically
copy-deployed into Hermes skill folders that cannot import this backend
at all.
"""
from app.vault.client import VaultClient

__all__ = ["VaultClient"]
