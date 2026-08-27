"""Template Manager -- reads the Template.json files that control
vault_manager.py's/VaultClient's real write behavior (note_name shape,
per-section write access, frontmatter defaults). Second Brain's own
system data, under second_brain_data_path -- not the vault, not raw
Obsidian mechanics. Pure I/O, no caching: a Template edited on disk
takes effect on the very next read.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.config import settings

_TEMPLATES_SUBPATH = ("data", "Templates")


def _templates_root() -> Path:
    return settings.second_brain_data_path.joinpath(*_TEMPLATES_SUBPATH)


def _template_file(template_id: str) -> Path:
    return _templates_root() / template_id / "Template.json"


def get_template(template_id: str) -> dict | None:
    """Fetches one Template by id, with the same defaults
    vault_manager.load_template applies -- None (never raises) if the
    id doesn't exist or its Template.json is malformed."""
    path = _template_file(template_id)
    if not path.is_file():
        return None
    try:
        template = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    template.setdefault("id", template_id)
    template.setdefault("on_missing", "create")
    template.setdefault("on_existing_title", "update_section")
    template.setdefault("frontmatter_defaults", {})
    template.setdefault("sections", [])
    template.setdefault("note_own_folder", False)
    template.setdefault("note_filename_plain", False)
    return template


def list_templates() -> list[dict]:
    """Every real Template found on disk, for the Settings > Vault
    Templates page. A malformed Template.json is still listed (with an
    "error" field) rather than silently skipped, so a broken template is
    visible instead of invisible."""
    templates_root = _templates_root()
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
