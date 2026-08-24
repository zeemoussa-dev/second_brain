"""Vault Data Access block (2026-08-20 architecture pass, ADR-059 follow-up).

Owns everything that is real, trusted Obsidian vault content -- OKF
directories/notes with frontmatter on top -- and nothing else. Empty
skeleton for now; vault_writer.py's own vault-content functions (~2,300 of
its 2,933 lines) are the migration source once this block starts filling.
"""
