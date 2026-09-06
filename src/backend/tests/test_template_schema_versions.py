"""The Template reader has to handle both schemas.

v1 is flat; v2 nests the same information under `root` and renames three
keys. Reading v1 names out of a v2 file never *fails* -- every `.get()`
just returns its default -- so until 2026-09-06 all 11 real templates
parsed to zero sections with `error=None`. Nothing surfaced it, and it
silently blocked any check that needs to know a template's real shape.

The last test here is the one that would have caught it.
"""
import json
from pathlib import Path

import pytest

from app.business.core.templates.template_manager import TemplateManager

_MASTERS = Path(__file__).resolve().parents[1] / "app" / "business" / "core" / "templates" / "masters"

_V1 = {
    "id": "legacy",
    "note_name": "Legacy",
    "sections": [{"name": "Summary"}, {"name": "Notes", "access": "human_only"}],
    "frontmatter_defaults": {"type": "Legacy"},
    "note_own_folder": True,
    "note_filename_plain": True,
    "on_existing_title": "always_new",
}

_V2 = {
    "id": "modern",
    "identity": {"strategy": "id"},
    "on_missing": "error",
    "root": {
        "own_folder": True,
        "plain_filename": True,
        "on_existing_title": "always_new",
        "frontmatter_defaults": {"type": "Modern"},
        "sections": [
            {"name": "Summary", "access": "machine_write", "allowed_callers": ["apply_review"]},
            {"name": "Personal Notes", "access": "human_only"},
            {"name": "Actions", "access": "machine_write", "required_non_empty": True},
        ],
    },
}


def _parse(data: dict):
    return TemplateManager()._to_template(data["id"], data)


def test_a_v2_template_yields_its_real_sections() -> None:
    """The actual regression: this returned zero sections."""
    template = _parse(_V2)

    assert template.schema_version == 2
    assert [s.name for s in template.sections] == ["Summary", "Personal Notes", "Actions"]
    assert template.frontmatter_defaults == {"type": "Modern"}


def test_v2_renamed_keys_are_read_from_root() -> None:
    """own_folder / plain_filename / on_existing_title moved and renamed."""
    template = _parse(_V2)

    assert template.note_own_folder is True
    assert template.note_filename_plain is True
    assert template.on_existing_title == "always_new"


def test_v2_section_only_keys_do_not_break_parsing() -> None:
    """allowed_callers and required_non_empty appear only in v2. Before
    this fix they were unreachable, so they had never been parsed."""
    sections = {s.name: s for s in _parse(_V2).sections}

    assert sections["Summary"].allowed_callers == ["apply_review"]
    assert sections["Actions"].required_non_empty is True
    assert sections["Personal Notes"].access == "human_only"


def test_v1_still_parses_flat() -> None:
    template = _parse(_V1)

    assert template.schema_version == 1
    assert [s.name for s in template.sections] == ["Summary", "Notes"]
    assert template.note_name == "Legacy"
    assert template.note_own_folder is True


def test_a_v2_template_legitimately_has_no_note_name() -> None:
    """v2 dropped note_name as a template key -- it became a create()
    parameter. Absent is correct here, not a parse failure."""
    assert _parse(_V2).note_name is None


def test_a_declared_version_beats_the_inferred_one() -> None:
    """Shape is only the fallback. A file that says what it is wins, which
    is what makes a future v3 readable rather than guessed at."""
    declared_v1_but_shaped_v2 = {**_V2, "schema_version": 1}

    assert _parse(declared_v1_but_shaped_v2).schema_version == 1


def test_a_template_with_no_declaration_is_inferred_from_shape() -> None:
    """Every file written before the field existed relies on this."""
    assert "schema_version" not in _V2
    assert _parse(_V2).schema_version == 2
    assert _parse(_V1).schema_version == 1


def test_an_unrecognised_section_key_is_surfaced_not_swallowed() -> None:
    """A broken template must stay visible. TemplateSection is explicit
    rather than **kwargs-tolerant precisely so this raises, and get_all()
    turns it into a Template carrying `error`."""
    bad = {"id": "bad", "root": {"sections": [{"name": "X", "no_such_key": 1}]}}

    with pytest.raises(TypeError):
        _parse(bad)


@pytest.mark.parametrize("path", sorted(_MASTERS.glob("*/Template.json")), ids=lambda p: p.parent.name)
def test_every_shipped_master_template_parses_with_real_content(path: Path) -> None:
    """The test that would have caught the original bug: each shipped
    Master Template must declare its schema and yield real sections."""
    data = json.loads(path.read_text(encoding="utf-8"))
    template = TemplateManager()._to_template(path.parent.name, data)

    assert data["schema_version"] == 2, "a shipped template must declare its schema"
    assert template.sections, "parsed to zero sections -- the v1/v2 mis-read is back"
    assert all(s.name for s in template.sections)
