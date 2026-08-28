"""Index entity -- a real, user-defined, scoped vault index (which
Work/ folders, which tags, how deep, where the built output lands, on
what real Hermes cron schedule), distinct from VaultManager's own single
in-memory note index (rebuild/read/overview -- the whole vault, always,
in-process, never scheduled). IndexManager (2026-08-28) is the sole
gateway onto this data. See index.py for the shape, index_manager.py for
IndexManager itself.
"""
