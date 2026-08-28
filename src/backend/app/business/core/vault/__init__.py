"""Vault entity -- the business-shaped representation of the vault
(never raw Obsidian file-system mechanics, which live in app/obsidian/
and app/vault/ -- note the naming closeness: THIS package is
app.business.core.vault, a business-entity representation; app.vault is
the low-level Obsidian writer engine (VaultClient/vault_manager.py).
Different layers, same word -- don't confuse the two).

VaultManager (2026-08-28) is the sole gateway onto Vault data -- folded
in and retired the four previously-separate modules that had no single
owning door: vault_indexing.py, vault_index_config.py,
vault_templates.py, vault_entities.py. `Vault` (vault.py) itself stays
the singleton overview/stats shape `get_overview()` returns -- a
deliberate deviation from the other Core entities' own Array<Entity>
convention, since there is exactly one vault, not many.
"""
