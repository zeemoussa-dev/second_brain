"""Vault > Templates (Settings, 2026-08-27) -- read-only listing of the
Template.json files that already control vault_manager.py's real write
behavior (note_name shape, per-section write access, frontmatter
defaults). Hand-edited JSON with zero UI today; this surfaces what
exists without adding an edit path yet (operator: "stop the
functionality, it's fine" carried over from the System settings pass)."""
from __future__ import annotations

from app.data_access.templates import registry as template_registry


def list_templates() -> list[dict]:
    return template_registry.list_templates()
