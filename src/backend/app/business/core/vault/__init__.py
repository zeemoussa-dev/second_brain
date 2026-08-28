"""Vault entity -- the business-shaped representation of the vault
(never raw Obsidian file-system mechanics, which live in app/obsidian/
and app/vault/ -- note the naming closeness: THIS package is
app.business.core.vault, a business-entity representation; app.vault is
the low-level Obsidian writer engine (VaultClient/vault_manager.py).
Different layers, same word -- don't confuse the two). Today's real
code only has two thin dict views over one in-memory index
(vault_indexing.get_overview()/get_last_rebuilt_at()) -- no unified
entity exists yet; the shape in vault.py is a first draft based on
that, not a settled contract. See vault_manager.py for the
VaultManager (methods not yet wired -- scaffolding only; also not the
same thing as app.vault.vault_manager, the Obsidian writer engine).
"""
