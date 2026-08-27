"""Vault > Templates (Settings, 2026-08-27) -- read-only listing of the
Template.json files that already control vault_manager.py's real write
behavior (note_name shape, per-section write access, frontmatter
defaults). Hand-edited JSON with zero UI today; this surfaces what
exists without adding an edit path yet (operator: "stop the
functionality, it's fine" carried over from the System settings pass)."""
from __future__ import annotations

import json

from app.config import settings


def list_templates() -> list[dict]:
    templates_root = settings.second_brain_data_path / "data" / "Templates"
    if not templates_root.exists():
        return []
    templates: list[dict] = []
    for template_dir in sorted(p for p in templates_root.iterdir() if p.is_dir()):
        template_file = template_dir / "Template.json"
        if not template_file.is_file():
            continue
        try:
            data = json.loads(template_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            templates.append({"id": template_dir.name, "error": str(exc)})
            continue
        templates.append({
            "id": template_dir.name,
            "note_name": data.get("note_name"),
            "on_missing": data.get("on_missing", "create"),
            "on_existing_title": data.get("on_existing_title", "update_section"),
            "sections": data.get("sections", []),
            "frontmatter_defaults": data.get("frontmatter_defaults", {}),
            "note_own_folder": data.get("note_own_folder", False),
            "note_filename_plain": data.get("note_filename_plain", False),
        })
    return templates
