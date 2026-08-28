"""TemplateManager -- the sole business-layer gateway onto Template data
(mirrors Section/Agent/Pipeline/Vault Manager's own "one real gateway"
rule), delegating raw I/O to `data_access/templates.py` (ADR-003's
api -> business -> data_access layering) rather than reading
Template.json itself -- unlike Section/Agent/Vault's own Managers, which
own their raw I/O directly, this one was deliberately kept layered
(operator's own explicit call, 2026-08-28: restore the literal
api -> business -> data_access shape here rather than follow the other
Managers' precedent).

Real, narrow scope: Second Brain's own system data (which section-write-
access/frontmatter-default RULES exist), never the vault itself.
Deliberately NOT the same thing as `app/vault/vault_manager.py`'s own
`load_template()` -- that is a different, lower-level, stdlib-only
loader belonging to the standalone write engine (also copy-deployed into
Hermes skill folders, which cannot import this backend at all); real
callers of a Template for an actual vault WRITE (e.g.
business/cockpit/documents.py) go through that engine's own loader, not
this Manager. `get_by_id()` below currently has zero real callers of its
own (found live, 2026-08-28) -- kept anyway since it's the natural
single-Template counterpart to `get_all()`, and Section/Agent/Pipeline/
Vault all expose the same shape.
"""
from __future__ import annotations

from app.business.core.templates.template import Template, TemplateSection
from app.data_access import templates as templates_data


class TemplateManager:
    def _to_template(self, template_id: str, data: dict) -> Template:
        return Template(
            id=template_id,
            note_name=data.get("note_name"),
            on_missing=data.get("on_missing", "create"),
            on_existing_title=data.get("on_existing_title", "update_section"),
            sections=[TemplateSection(**s) for s in data.get("sections", [])],
            frontmatter_defaults=data.get("frontmatter_defaults", {}),
            note_own_folder=data.get("note_own_folder", False),
            note_filename_plain=data.get("note_filename_plain", False),
        )

    def get_by_id(self, template_id: str) -> Template | None:
        """None (never raises) if the id doesn't exist or its
        Template.json is malformed."""
        try:
            data = templates_data.read_template_json(template_id)
            return self._to_template(template_id, data)
        except (OSError, ValueError, TypeError):
            return None

    def get_all(self) -> list[Template]:
        """Every real Template found on disk, for the Settings > Vault
        Templates page. A malformed Template.json (unparsable JSON, or a
        `sections` entry with an unexpected shape) is still listed (as a
        Template with only `id`/`error` set) rather than silently
        skipped or crashing the whole listing, so a broken template is
        visible instead of invisible."""
        templates: list[Template] = []
        for template_id in templates_data.list_template_ids():
            try:
                data = templates_data.read_template_json(template_id)
                templates.append(self._to_template(template_id, data))
            except (OSError, ValueError, TypeError) as exc:
                templates.append(Template(id=template_id, note_name=None, error=str(exc)))
        return templates
