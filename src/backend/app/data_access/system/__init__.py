"""System Data Access block (2026-08-20 architecture pass, ADR-059 follow-up).

Owns Second Brain's own operational state needed to run -- not Vault
content, not Hermes/LangGraph's own execution data (out of our control).
Today this data lives as vault_writer.py's ~600 lines of JSON-store
functions, all reading/writing under `settings.second_brain_data_path`.
That path is independent of `settings.vault_path` since the System
settings page (2026-08-27) -- it defaults to `<vault>/.second-brain/` for
a fresh install (the original, still-disclosed conflation this block
exists to fully resolve) but is relocatable from there without moving the
vault. Empty skeleton for now.
"""
