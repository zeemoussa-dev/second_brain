from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TemplateSection:
    name: str
    access: str = "machine_write"


@dataclass
class Template:
    id: str
    note_name: str | None
    on_missing: str = "create"
    on_existing_title: str = "update_section"
    sections: list[TemplateSection] = field(default_factory=list)
    frontmatter_defaults: dict = field(default_factory=dict)
    note_own_folder: bool = False
    note_filename_plain: bool = False
