"""System Data Access block (2026-08-20 architecture pass, ADR-059 follow-up).

Owns Second Brain's own operational state needed to run -- not Vault
content, not Hermes/LangGraph's own execution data (out of our control).
Today this data lives as vault_writer.py's ~600 lines of `_STATE_DIR =
".second-brain"` JSON-store functions, and is physically stored INSIDE the
vault path itself (<vault>/.second-brain/) alongside real Vault content --
a real, disclosed conflation this block exists to resolve. Empty skeleton
for now.
"""
