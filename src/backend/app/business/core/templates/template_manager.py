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

No longer read-only-only: `import_template()` (ADR-015) is a real,
narrowly-scoped write path added ONLY to let `REQ-SB-85-US-03`'s import
orchestrator write a genuine Template.json onto the target machine --
still the sole gateway onto Template data (the new writer in
`data_access/templates.py` is never called directly by anything else).
No general Templates create/update/delete authoring UI exists or is
implied by this addition.
"""
from __future__ import annotations

from app.business.core.templates.template import Template, TemplateSection
from app.data_access import templates as templates_data


class TemplateManager:
    def _schema_version(self, data: dict) -> int:
        """Which Template schema this file was written against.

        Prefer what the file declares; fall back to its shape for the
        files written before `schema_version` existed. `root` is what
        defines v2 -- the two-layer split -- so its presence is the
        inference.

        This is resolved ONCE, explicitly, rather than per-field with
        `.get()` fallbacks, because that is exactly how the bug this
        replaces stayed invisible: reading v1 names out of a v2 file
        never raises, every `.get()` simply returns its default, and all
        11 real templates parsed to zero sections with error=None."""
        declared = data.get("schema_version")
        if isinstance(declared, int) and declared > 0:
            return declared
        return 2 if isinstance(data.get("root"), dict) else 1

    def _to_template(self, template_id: str, data: dict) -> Template:
        """v1 keeps everything flat; v2 nests the same information under
        `root` and renames three keys (`note_own_folder` -> `own_folder`,
        `note_filename_plain` -> `plain_filename`, and moves
        `on_existing_title` inside). `note_name` is not a rename: v2
        dropped it as a template key entirely, so a v2 template
        legitimately has none."""
        version = self._schema_version(data)
        source = (data.get("root") or {}) if version >= 2 else data
        if version >= 2:
            own_folder = source.get("own_folder", False)
            plain_filename = source.get("plain_filename", False)
        else:
            own_folder = source.get("note_own_folder", False)
            plain_filename = source.get("note_filename_plain", False)
        return Template(
            id=template_id,
            schema_version=version,
            note_name=data.get("note_name"),
            on_missing=data.get("on_missing", "create"),
            on_existing_title=source.get("on_existing_title", "update_section"),
            sections=[TemplateSection(**s) for s in source.get("sections", [])],
            frontmatter_defaults=source.get("frontmatter_defaults", {}),
            note_own_folder=own_folder,
            note_filename_plain=plain_filename,
        )

    def seed_shipped_masters(self) -> dict:
        """Installs every shipped Master Template this install does not
        already have. Returns {"seeded": [...], "kept": [...]}.

        **Never overwrites.** An id already present is left exactly as it
        is, whatever it contains: the operator's own edit to `thread`
        outranks the shipped copy, and this runs on every boot rather
        than once, so overwriting would silently revert local changes on
        every restart. Upgrading an existing template is a separate,
        deliberate act that has to reconcile operator edits -- not
        something a boot path does behind their back.

        Why this exists at all (2026-09-06): nothing shipped Entity
        Templates before, and nothing seeded them. A fresh install had no
        vault structure whatsoever, so every capture Skill would have
        failed on a missing template -- the framework shipped the engine
        and none of the contracts.

        Validates each shipped file through the existing `_to_template`
        parser before writing it, the same read-side shape check
        import_template applies, so a malformed shipped template raises
        here instead of landing on disk.
        """
        existing = set(templates_data.list_template_ids())
        seeded: list[str] = []
        kept: list[str] = []
        for template_id in templates_data.list_shipped_master_ids():
            if template_id in existing:
                kept.append(template_id)
                continue
            data = templates_data.read_shipped_master_json(template_id)
            self._to_template(template_id, data)
            templates_data.write_template_json(template_id, data)
            seeded.append(template_id)
        return {"seeded": seeded, "kept": kept}

    def get_by_id(self, template_id: str) -> Template | None:
        """None (never raises) if the id doesn't exist or its
        Template.json is malformed."""
        try:
            data = templates_data.read_template_json(template_id)
            return self._to_template(template_id, data)
        except (OSError, ValueError, TypeError):
            return None

    def import_template(self, template_id: str, data: dict) -> Template:
        """Real, narrowly-scoped write path for import provisioning only
        (ADR-015) -- validates `data` by round-tripping it through the
        SAME `_to_template` parser the read side already uses (a
        KeyError/TypeError there means `data` doesn't match the real
        Template/TemplateSection shape, propagated uncaught rather than
        writing invalid JSON to disk), then writes it and returns the
        freshly-written Template (read-your-own-write, matching
        AgentManager.create/update's own convention). Never applies a
        conflict decision itself -- the caller (the import orchestrator,
        T05) must already have decided overwrite/keep-both/skip before
        ever calling this; this method always writes, unconditionally."""
        self._to_template(template_id, data)
        templates_data.write_template_json(template_id, data)
        return self.get_by_id(template_id)

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
                # schema_version 0 = "could not be determined". Reading the
                # file is what failed, so `data` may never have been bound;
                # claiming v1 here would be a guess dressed as a fact.
                templates.append(Template(
                    id=template_id, schema_version=0, note_name=None, error=str(exc),
                ))
        return templates
