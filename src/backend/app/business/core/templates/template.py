from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TemplateSection:
    name: str
    access: str = "machine_write"
    # v2-only, and deliberately explicit rather than **kwargs-tolerant:
    # an unrecognised section key raises TypeError, which get_all()
    # catches and surfaces as Template.error -- a broken template stays
    # visible instead of parsing into something plausible but wrong.
    required_non_empty: bool = False
    # Names the Skill Actions permitted to write this section. A reverse
    # edge (structure depending on capability) that is on its way out --
    # see the Master Template README. Read here only so v2 files parse.
    allowed_callers: list[str] = field(default_factory=list)


@dataclass
class Template:
    id: str
    # Which Template schema this was written against. v1 is flat; v2 nests
    # the same information under `root` and renames three keys. A template
    # that does not declare it is inferred from its shape -- see
    # TemplateManager._schema_version.
    schema_version: int
    note_name: str | None
    on_missing: str = "create"
    on_existing_title: str = "update_section"
    sections: list[TemplateSection] = field(default_factory=list)
    frontmatter_defaults: dict = field(default_factory=dict)
    note_own_folder: bool = False
    note_filename_plain: bool = False
    # Set only when this Template's own Template.json failed to parse --
    # still returned (never silently skipped) so a broken template is
    # visible instead of invisible, same discipline TemplateManager's
    # own list-all always applied.
    error: str | None = None
