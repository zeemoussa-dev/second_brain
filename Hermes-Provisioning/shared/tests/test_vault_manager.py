"""vault_manager.py regression tests (Implementation/Plans/2026-08-25-
vault-writer-standardization.md). Every scenario here was also verified
live via the real CLI against a scratch vault before this file was
written -- this locks that verification in as automated coverage.

vault_manager.py is stdlib-only and has no dependency on the FastAPI app
(deliberately -- it gets copied standalone into Hermes Skills), so this
test imports it directly by path rather than via the `app` package. Run
with the backend's own venv (has pytest already):
    src\\backend\\.venv\\Scripts\\python.exe -m pytest Hermes-Provisioning\\shared\\tests
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parent.parent / "vault_manager.py"
_spec = importlib.util.spec_from_file_location("vault_manager", _MODULE_PATH)
vm = importlib.util.module_from_spec(_spec)
sys.modules["vault_manager"] = vm
_spec.loader.exec_module(vm)


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    def _write_template(template_id: str, **fields) -> None:
        import json
        path = tmp_path / ".second-brain" / "data" / "Templates" / template_id / "Template.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"id": template_id, **fields}), encoding="utf-8")

    _write_template(
        "kb-doc", on_missing="create", on_existing_title="update_section",
        frontmatter_defaults={"type": "KBDoc"},
        sections=[{"name": "Summary", "access": "machine_write"}, {"name": "Details", "access": "machine_write"}],
    )
    _write_template(
        "dated-note", on_missing="create", on_existing_title="always_new",
        frontmatter_defaults={"type": "ResearchDoc"},
        sections=[{"name": "Summary", "access": "machine_write"}],
    )
    _write_template(
        "person-note", on_missing="error", on_existing_title="update_section",
        frontmatter_defaults={"type": "Person"},
        sections=[{"name": "Findings", "access": "machine_write"}, {"name": "Personal Notes", "access": "user_edit"}],
    )
    return tmp_path


def test_frontmatter_round_trips_lists_and_escaped_quotes(vault):
    path = vault / "Work" / "x" / "note.md"
    vm.write_note(path, {"title": 'A "quoted" title', "tags": ["a", "b"]}, "\nbody\n")
    frontmatter, body = vm.read_note(path)
    assert frontmatter["title"] == 'A "quoted" title'
    assert frontmatter["tags"] == ["a", "b"]
    assert body == "\nbody\n"


def test_create_places_note_under_hierarchical_note_name(vault):
    template = vm.load_template(vault, "kb-doc")
    result = vm.create(vault, template, note_name="Azure/Services/Storage", title="Blob Pricing", sections={"Summary": "cheap"})
    assert result["created"] is True
    path = Path(result["path"])
    assert path.parent == vault / "Work" / "Azure" / "Services" / "Storage"
    frontmatter, _ = vm.read_note(path)
    assert frontmatter["id"] == result["id"]
    assert frontmatter["type"] == "KBDoc"


def test_create_with_update_section_never_duplicates_on_same_title(vault):
    template = vm.load_template(vault, "kb-doc")
    first = vm.create(vault, template, note_name="Azure", title="Storage", sections={"Summary": "v1"})
    second = vm.create(vault, template, note_name="Azure", title="Storage", sections={"Summary": "v2"})

    assert second["created"] is False and second["updated"] is True
    assert second["id"] == first["id"]
    files = list((vault / "Work" / "Azure").rglob("*.md"))
    assert len(files) == 1
    frontmatter, _ = vm.read_note(files[0])
    assert vm.get_section_content(files[0], "Summary") == "v2"


def test_create_with_always_new_never_overwrites(vault):
    template = vm.load_template(vault, "dated-note")
    first = vm.create(vault, template, note_name="Research", title="GPU pricing", sections={"Summary": "v1"})
    second = vm.create(vault, template, note_name="Research", title="GPU pricing", sections={"Summary": "v2"})

    assert first["path"] != second["path"]
    assert first["id"] != second["id"]
    files = list((vault / "Work" / "Research").rglob("*.md"))
    assert len(files) == 2


def test_modify_section_replace_and_append(vault):
    template = vm.load_template(vault, "kb-doc")
    created = vm.create(vault, template, note_name="Azure", title="Storage", sections={"Details": "first"})

    vm.modify_section(vault, template, note_id=created["id"], section="Details", content="second", mode="append")
    path = Path(created["path"])
    assert vm.get_section_content(path, "Details") == "first\n\nsecond"

    vm.modify_section(vault, template, note_id=created["id"], section="Details", content="replaced entirely", mode="replace")
    assert vm.get_section_content(path, "Details") == "replaced entirely"


def test_modify_section_creates_when_missing_and_on_missing_is_create(vault):
    template = vm.load_template(vault, "kb-doc")
    result = vm.modify_section(
        vault, template, note_id="brand-new", section="Summary", content="fresh", mode="replace",
        note_name="Azure/Compute", title="VM Pricing",
    )
    assert result["created"] is True
    frontmatter, _ = vm.read_note(Path(result["path"]))
    assert frontmatter["id"] == "brand-new"


def test_modify_section_refuses_to_create_when_on_missing_is_error(vault):
    template = vm.load_template(vault, "person-note")
    with pytest.raises(vm.VaultManagerError):
        vm.modify_section(
            vault, template, note_id="no-such-person", section="Findings", content="x", mode="append",
            note_name="People", title="Someone",  # even WITH create-capable params, on_missing=error still refuses
        )
    assert vm.find_by_id(vault, "no-such-person") is None


def test_modify_section_refuses_a_user_edit_section(vault):
    template = vm.load_template(vault, "person-note")
    created = vm.create(vault, template, note_name="People", title="Jane Doe", sections={"Findings": "works at ACME"})

    with pytest.raises(vm.VaultManagerError, match="user_edit"):
        vm.modify_section(vault, template, note_id=created["id"], section="Personal Notes", content="sneaky", mode="append")

    # the section must be genuinely untouched, not partially written
    assert vm.get_section_content(Path(created["path"]), "Personal Notes") == ""


def test_undeclared_section_defaults_to_machine_write(vault):
    template = vm.load_template(vault, "kb-doc")
    created = vm.create(vault, template, note_name="Azure", title="Storage")
    # "Notes" was never declared in the kb-doc template's own sections list
    vm.modify_section(vault, template, note_id=created["id"], section="Notes", content="undeclared but allowed", mode="replace")
    assert vm.get_section_content(Path(created["path"]), "Notes") == "undeclared but allowed"


def test_rename_via_update_preserves_id_based_lookup(vault):
    template = vm.load_template(vault, "person-note")
    created = vm.create(vault, template, note_name="People", title="Jane Doe")
    note_id = created["id"]

    path_before = vm.find_by_id(vault, note_id)
    vm.update(vault, path_before, title="Jane A. Doe")

    path_after = vm.find_by_id(vault, note_id)
    assert path_after == path_before  # the file itself never moved
    frontmatter, _ = vm.read_note(path_after)
    assert frontmatter["title"] == "Jane A. Doe"
    assert frontmatter["id"] == note_id


def test_find_by_filename_and_folder(vault):
    template = vm.load_template(vault, "kb-doc")
    vm.create(vault, template, note_name="Azure", title="Storage")
    vm.create(vault, template, note_name="Azure", title="Compute")

    all_in_folder = vm.find_in_folder(vault, "Azure")
    assert len(all_in_folder) == 2

    by_filename = vm.find_by_filename(vault, all_in_folder[0].name, note_name="Azure")
    assert by_filename in all_in_folder


def test_find_returns_empty_or_none_on_a_folder_that_does_not_exist(vault):
    assert vm.find_by_id(vault, "anything", note_name="Nonexistent") is None
    assert vm.find_in_folder(vault, "Nonexistent") == []


def test_load_template_raises_on_unknown_id(vault):
    with pytest.raises(vm.VaultManagerError):
        vm.load_template(vault, "does-not-exist")


def test_note_own_folder_wraps_the_note_in_a_matching_folder(vault):
    """Operator, 2026-08-25: meetings "sometimes... will have Attachements,
    so we might have files" -- `note_own_folder` wraps the note as
    `<stem>/<stem>.md` instead of a bare `<stem>.md`, so an attachment has
    a real place to live as the note's own sibling."""
    import json
    template_path = vault / ".second-brain" / "data" / "Templates" / "meeting" / "Template.json"
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.write_text(json.dumps({
        "id": "meeting", "on_missing": "create", "on_existing_title": "always_new",
        "note_own_folder": True, "frontmatter_defaults": {},
        "sections": [{"name": "Summary", "access": "machine_write"}],
    }), encoding="utf-8")
    template = vm.load_template(vault, "meeting")

    result = vm.create(vault, template, note_name="Meetings", title="Standup")
    path = Path(result["path"])
    assert path.parent.name == path.stem  # folder named after the note itself
    assert Path(result["folder"]) == path.parent

    # A real attachment dropped alongside it is a plain sibling file --
    # no vault_manager involvement needed for that part.
    (path.parent / "screenshot.png").write_bytes(b"fake image bytes")
    assert (path.parent / "screenshot.png").is_file()

    # find(by="id"/"folder") must still resolve it -- rglob already
    # handles arbitrary nesting depth, confirmed rather than assumed.
    frontmatter, _ = vm.read_note(path)
    assert vm.find_by_id(vault, frontmatter["id"], note_name="Meetings") == path


def test_note_own_folder_truncates_a_long_title_to_stay_under_max_path(vault, monkeypatch):
    """Real bug, found live 2026-08-25: a real corporate meeting subject
    well past 80 characters, combined with own_folder's stem-appears-
    twice shape, blew past Windows' 260-char MAX_PATH and crashed with a
    plain FileNotFoundError."""
    import json
    template_path = vault / ".second-brain" / "data" / "Templates" / "meeting" / "Template.json"
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.write_text(json.dumps({
        "id": "meeting", "on_missing": "create", "on_existing_title": "always_new",
        "note_own_folder": True, "frontmatter_defaults": {},
        "sections": [{"name": "Summary", "access": "machine_write"}],
    }), encoding="utf-8")
    template = vm.load_template(vault, "meeting")

    long_title = "ADNOC Insight Private SaaS Deployment - Additional infra monitoring and managed services scope"
    result = vm.create(vault, template, note_name="Meetings", title=long_title)
    path = Path(result["path"])
    assert path.is_file()  # the real bug: this line raised FileNotFoundError
    assert len(path.stem) < len(long_title) + 11  # date prefix ("YYYY-MM-DD-") + truncated title, not the full 98 chars


def _write_series_template(vault: Path) -> dict:
    import json
    template_path = vault / ".second-brain" / "data" / "Templates" / "meeting-series" / "Template.json"
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.write_text(json.dumps({
        "id": "meeting-series", "on_missing": "create", "on_existing_title": "always_new",
        "note_own_folder": True, "note_filename_plain": True, "frontmatter_defaults": {},
        "sections": [{"name": "History", "access": "machine_write"}],
    }), encoding="utf-8")
    return vm.load_template(vault, "meeting-series")


def test_note_filename_plain_keeps_filename_undated_while_folder_is_dated(vault):
    """Operator, 2026-08-25: "the md for the Series shoud not have a date
    Just the Series name" -- the wrapping folder still carries the date
    (so it sorts), the file inside does not."""
    template = _write_series_template(vault)
    result = vm.create(vault, template, note_name="Meetings", title="Standup", folder_date="2026-08-21")
    path = Path(result["path"])
    assert path.name == "Standup.md"
    assert path.parent.name == "2026-08-21-Standup"


def test_bump_folder_date_moves_folder_forward_and_preserves_attachments(vault):
    template = _write_series_template(vault)
    created = vm.create(vault, template, note_name="Meetings", title="Standup", folder_date="2026-08-21")
    path = Path(created["path"])
    (path.parent / "screenshot.png").write_bytes(b"fake image bytes")

    bumped = vm.bump_folder_date(vault, path, "2026-08-24")
    assert bumped.parent.name == "2026-08-24-Standup"
    assert bumped.name == "Standup.md"
    assert bumped.is_file()
    assert (bumped.parent / "screenshot.png").is_file()  # moved with the folder, untouched
    assert not path.exists()  # the OLD dated folder is really gone, not duplicated

    # find(by="id") must still resolve it after the real folder move.
    frontmatter, _ = vm.read_note(bumped)
    assert vm.find_by_id(vault, frontmatter["id"], note_name="Meetings") == bumped


def test_bump_folder_date_is_a_no_op_for_an_earlier_or_equal_date(vault):
    template = _write_series_template(vault)
    created = vm.create(vault, template, note_name="Meetings", title="Standup", folder_date="2026-08-21")
    path = Path(created["path"])

    assert vm.bump_folder_date(vault, path, "2026-08-21") == path  # equal -- no-op
    assert vm.bump_folder_date(vault, path, "2026-08-19") == path  # earlier -- no-op
    assert path.is_file()


def test_own_folder_truncation_never_leaves_a_trailing_space(vault):
    """Real bug, found live 2026-08-25 processing the full real meeting
    history: the word-boundary truncation (rsplit(" ", 1)[0].rstrip("-"))
    could still land on a result ending in whitespace, which Windows then
    rejected as a path segment -- the exact same class of bug
    `_sanitize_note_name` already exists to prevent, just not reached
    here. Deeply nested folder (mirrors Meetings/<series>/Recurrences/)
    to force the same tight truncation budget that triggered it live."""
    import json
    template_path = vault / ".second-brain" / "data" / "Templates" / "meeting" / "Template.json"
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.write_text(json.dumps({
        "id": "meeting", "on_missing": "create", "on_existing_title": "always_new",
        "note_own_folder": True, "frontmatter_defaults": {},
        "sections": [{"name": "Summary", "access": "machine_write"}],
    }), encoding="utf-8")
    template = vm.load_template(vault, "meeting")

    deep_folder = "Meetings/2026-10-21-Core Account Team Weekly Cadenace (ADNOC - EDGE - POM Holding)/Recurrences"
    long_title = "Core Account Team Weekly Cadenace (ADNOC | EDGE | POM Holding)"

    result = vm.create(vault, template, note_name=deep_folder, title=long_title)
    path = Path(result["path"])
    assert path.is_file()  # the real bug: this raised FileNotFoundError
    assert not path.parent.name.endswith(" ")
    assert not path.stem.endswith(" ")


def test_note_name_with_trailing_space_and_invalid_chars_is_sanitized(vault):
    """Real bug, found live 2026-08-25 against real Outlook data: a
    calendar subject like "PSS Team Get together " (trailing space) used
    raw as a folder name crashed with FileNotFoundError -- Windows
    silently disallows a trailing space in a path segment."""
    template = vm.load_template(vault, "kb-doc")
    result = vm.create(vault, template, note_name="PSS Team Get together / Sub:Topic", title="X")
    path = Path(result["path"])
    assert " " != path.parent.name[-1]
    assert path.is_file()
