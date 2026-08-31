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
    def _write_template(template_id: str, on_missing="create", root_fields=None, **template_fields) -> None:
        import json
        path = tmp_path / ".second-brain" / "data" / "Templates" / template_id / "Template.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "id": template_id, "on_missing": on_missing,
            "root": root_fields or {}, **template_fields,
        }), encoding="utf-8")

    _write_template(
        "kb-doc", root_fields={
            "on_existing_title": "update_section",
            "frontmatter_defaults": {"type": "KBDoc"},
            "sections": [{"name": "Summary", "access": "machine_write"}, {"name": "Details", "access": "machine_write"}],
        },
    )
    _write_template(
        "dated-note", root_fields={
            "on_existing_title": "always_new",
            "frontmatter_defaults": {"type": "ResearchDoc"},
            "sections": [{"name": "Summary", "access": "machine_write"}],
        },
    )
    _write_template(
        "person-note", on_missing="error", root_fields={
            "on_existing_title": "update_section",
            "frontmatter_defaults": {"type": "Person"},
            "sections": [{"name": "Findings", "access": "machine_write"}, {"name": "Personal Notes", "access": "user_edit"}],
        },
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


def test_plain_filename_without_own_folder_keeps_date_out_of_the_filename(vault):
    """2026-08-30 (operator: "Notes are organized in folders by Date") --
    Work/Notes/<date>/<slug>.md: the date lives in the caller's own
    date-scoped note_name (the FOLDER), never repeated in the filename,
    and there's no wrapping own_folder either (a real attachment-less
    plain note, unlike meeting-series' dateless-file-inside-a-dated-
    folder shape)."""
    import json
    template_path = vault / ".second-brain" / "data" / "Templates" / "plain-note" / "Template.json"
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.write_text(json.dumps({
        "id": "plain-note", "on_missing": "create",
        "root": {
            "on_existing_title": "always_new", "own_folder": False, "plain_filename": True,
            "frontmatter_defaults": {}, "sections": [{"name": "Body", "access": "machine_write"}],
        },
    }), encoding="utf-8")
    template = vm.load_template(vault, "plain-note")

    result = vm.create(vault, template, note_name="Notes/2026-08-30", title="QA smoke test note")
    path = Path(result["path"])
    assert path.name == "QA smoke test note.md"
    assert path.parent.name == "2026-08-30"

    # a real same-day title collision still disambiguates, off the plain
    # title alone (no date prefix to build the retry suffix from)
    second = vm.create(vault, template, note_name="Notes/2026-08-30", title="QA smoke test note")
    second_path = Path(second["path"])
    assert second_path != path
    assert second_path.name != path.name
    assert "QA smoke test note" in second_path.name
    assert not second_path.name.startswith("2026-08-30-")


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


def test_allow_create_folder_defaults_true_and_still_creates(vault):
    """Every real template today omits allow_create_folder -- load_template's
    own default (True) must keep today's exact behavior (auto-create a
    missing folder), not silently start refusing."""
    template = vm.load_template(vault, "kb-doc")
    assert template["allow_create_folder"] is True
    result = vm.create(vault, template, note_name="BrandNewFolder", title="X")
    assert Path(result["path"]).is_file()


def test_allow_create_folder_false_refuses_when_folder_missing(vault):
    """2026-08-30 (operator: 'Allow Create folder... in Customer its a
    no') -- a template can declare its own record's containing folder
    must already exist; a missing folder is then a real error, not
    something to silently paper over."""
    import json
    template_path = vault / ".second-brain" / "data" / "Templates" / "strict-folder" / "Template.json"
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.write_text(json.dumps({
        "id": "strict-folder", "on_missing": "create", "allow_create_folder": False,
        "root": {
            "on_existing_title": "always_new", "frontmatter_defaults": {},
            "sections": [{"name": "Summary", "access": "machine_write"}],
        },
    }), encoding="utf-8")
    template = vm.load_template(vault, "strict-folder")

    with pytest.raises(vm.VaultManagerError, match="allow_create_folder"):
        vm.create(vault, template, note_name="Customers", title="Acme")
    assert not (vault / "Work" / "Customers").exists()

    # once the folder genuinely exists, the same call succeeds
    (vault / "Work" / "Customers").mkdir(parents=True)
    result = vm.create(vault, template, note_name="Customers", title="Acme")
    assert Path(result["path"]).is_file()


def _write_opportunity_template(vault: Path, on_missing: str = "create", with_children: bool = False) -> dict:
    import json
    template_path = vault / ".second-brain" / "data" / "Templates" / "opportunity" / "Template.json"
    template_path.parent.mkdir(parents=True, exist_ok=True)
    root = {
        "on_existing_title": "always_new",
        "frontmatter_defaults": {"type": "Opportunity"},
        "sections": [{"name": "Summary", "access": "machine_write"}],
    }
    if with_children:
        # 2026-08-31, real shape (operator: "the Opp has one file it
        # should have Capture and log as well") -- Log/Captures split
        # off the root note the same way Customer/Partner's own log/
        # captures already do.
        root["children"] = [
            {"suffix": "log", "frontmatter_defaults": {"type": "Log"}, "name_template": "{title} Log"},
            {"suffix": "captures", "frontmatter_defaults": {"type": "Captures"}, "name_template": "{title} Captures"},
        ]
    template_path.write_text(json.dumps({
        "id": "opportunity", "on_missing": on_missing,
        "parent": {
            "note_name": "Customers", "match_fields": ["name", "title"],
            "alias_field": "aliases", "frontmatter_field": "customer",
            "link_back_section": "## Opportunities",
            "child_subpath": "Opportunities", "derived_tag": "customer/{slug}",
        },
        "root": root,
    }), encoding="utf-8")
    return vm.load_template(vault, "opportunity")


def _write_customer_hub(vault: Path, name: str, aliases: list[str] | None = None) -> Path:
    path = vault / "Work" / "Customers" / name / f"{name}.md"
    vm.write_note(path, {"type": "Customer", "name": name, "title": name, "aliases": aliases or []}, "\n# " + name + "\n")
    return path


def test_create_with_required_parent_refuses_when_parent_missing(vault):
    """2026-08-30 (operator's own real Opportunity->Customer case) -- a
    template's own declared `parent` must already exist; a missing one
    is a real error, nothing gets written, never a fabricated stand-in."""
    template = _write_opportunity_template(vault)
    with pytest.raises(vm.VaultManagerError, match="Acme"):
        vm.create(vault, template, note_name="Customers/Acme/Opportunities", title="Renewal", parent_value="Acme")
    assert not (vault / "Work" / "Customers").exists()


def test_create_with_required_parent_but_no_parent_value_refuses(vault):
    template = _write_opportunity_template(vault)
    with pytest.raises(vm.VaultManagerError, match="parent_value"):
        vm.create(vault, template, note_name="Customers/Acme/Opportunities", title="Renewal")


def test_create_with_required_parent_resolves_and_links_back(vault):
    template = _write_opportunity_template(vault)
    customer_hub = _write_customer_hub(vault, "Acme")

    result = vm.create(
        vault, template, note_name="Customers/Acme/Opportunities", title="Renewal",
        parent_value="Acme", sections={"Summary": "Real renewal deal"},
    )
    child_path = Path(result["path"])
    assert child_path.is_file()

    # the resolved parent's own stem lands in the declared frontmatter field
    child_frontmatter, _ = vm.read_note(child_path)
    assert child_frontmatter["customer"] == "Acme"

    # a real wikilink was idempotently accumulated on the PARENT note
    backlink_section = vm.get_section_content(customer_hub, "## Opportunities")
    assert f"[[{child_path.stem}]]" in backlink_section


def test_create_with_required_parent_resolves_via_alias(vault):
    """create_opportunity.py's own real alias-fallback (`resolve_customer_hub`
    checks name/title, then a real `aliases` list) -- generalized here."""
    template = _write_opportunity_template(vault)
    _write_customer_hub(vault, "Acme Corp", aliases=["Acme", "ACME Corporation"])

    result = vm.create(
        vault, template, note_name="Customers/Acme Corp/Opportunities", title="Renewal",
        parent_value="ACME Corporation",
    )
    child_frontmatter, _ = vm.read_note(Path(result["path"]))
    assert child_frontmatter["customer"] == "Acme Corp"


def test_create_auto_derives_note_name_and_tag_from_resolved_parent(vault):
    """2026-08-30 (operator: "Why we need to create script everytime we
    add a skill We Generalized so we don't do that") -- note_name is no
    longer something the CALLING script has to compute by hand from the
    resolved parent; `parent.child_subpath` does it here. Same for a
    dynamic tag built from the parent's own name (`parent.derived_tag`)."""
    template = _write_opportunity_template(vault)
    _write_customer_hub(vault, "Acme")

    result = vm.create(vault, template, title="Renewal", parent_value="Acme")
    path = Path(result["path"])
    assert path.parent == vault / "Work" / "Customers" / "Acme" / "Opportunities"

    frontmatter, _ = vm.read_note(path)
    assert frontmatter["customer"] == "Acme"
    assert "customer/acme" in frontmatter["tags"]


def test_modify_section_by_title_and_parent_value_finds_the_real_note(vault):
    """The actual fix for "why do we need a script every time" -- this
    used to require a whole new wrapper script (find the parent, find
    the child by title, THEN modify_section by id); now it's one call."""
    template = _write_opportunity_template(vault)
    _write_customer_hub(vault, "Acme")
    created = vm.create(vault, template, title="Renewal", parent_value="Acme", sections={"Summary": "v1"})

    result = vm.modify_section(
        vault, template, section="Summary", content="v2", mode="replace",
        title="Renewal", parent_value="Acme",
    )
    assert result["id"] == created["id"]
    assert vm.get_section_content(Path(created["path"]), "Summary") == "v2"

    # alias resolution works here too, same as create's own
    result2 = vm.modify_section(
        vault, template, section="Log", content="first entry", mode="append",
        title="Renewal", parent_value="Acme",
    )
    assert result2["id"] == created["id"]


def test_modify_section_by_title_refuses_to_fabricate_when_on_missing_is_error(vault):
    """The real bug this generalization pass caught: the live opportunity
    Template.json had on_missing="create" -- fine for the old id-based
    modify_section, but a genuine "silently create an Opportunity" hole
    once title+parent_value became a real way to reach modify_section.
    on_missing="error" (matching person-note's own precedent) is what
    actually enforces "never fabricate an Opportunity via an update"."""
    template = _write_opportunity_template(vault, on_missing="error")
    _write_customer_hub(vault, "Acme")

    with pytest.raises(vm.VaultManagerError):
        vm.modify_section(
            vault, template, section="Log", content="should never write",
            mode="append", title="Does Not Exist", parent_value="Acme",
        )
    assert not (vault / "Work" / "Customers" / "Acme" / "Opportunities").exists()


def test_modify_section_with_child_suffix_writes_the_sibling_file_not_the_root(vault):
    """2026-08-31 (operator: "the Opp has one file it should have Capture
    and log as well") -- a Log/Captures append now redirects to the real
    child file instead of a section inside the root note."""
    template = _write_opportunity_template(vault, with_children=True)
    _write_customer_hub(vault, "Acme")
    created = vm.create(vault, template, title="Renewal", parent_value="Acme", sections={"Summary": "v1"})
    root_path = Path(created["path"])

    result = vm.modify_section(
        vault, template, section="Log", content="2026-08-31: first entry", mode="append",
        title="Renewal", parent_value="Acme", child_suffix="log",
    )
    assert result["id"] == created["id"]
    log_path = root_path.parent / f"{root_path.stem}-log.md"
    assert result["path"] == str(log_path)
    assert vm.get_section_content(log_path, "Log") == "2026-08-31: first entry"
    # the root's own Summary is untouched -- the write really landed on the child
    assert vm.get_section_content(root_path, "Summary") == "v1"
    assert vm.get_section_content(root_path, "Log") == ""


def test_modify_section_with_child_suffix_appends_across_repeated_calls(vault):
    template = _write_opportunity_template(vault, with_children=True)
    _write_customer_hub(vault, "Acme")
    created = vm.create(vault, template, title="Renewal", parent_value="Acme")
    root_path = Path(created["path"])

    vm.modify_section(
        vault, template, section="Log", content="entry one", mode="append",
        title="Renewal", parent_value="Acme", child_suffix="log",
    )
    vm.modify_section(
        vault, template, section="Log", content="entry two", mode="append",
        title="Renewal", parent_value="Acme", child_suffix="log",
    )
    log_path = root_path.parent / f"{root_path.stem}-log.md"
    content = vm.get_section_content(log_path, "Log")
    assert "entry one" in content
    assert "entry two" in content
    assert content.index("entry one") < content.index("entry two")


def test_modify_section_with_unknown_child_suffix_refuses(vault):
    """A template that never declared this child (or a real typo in the
    suffix) is a real error, not a silent no-op or a fabricated file."""
    template = _write_opportunity_template(vault, with_children=True)
    _write_customer_hub(vault, "Acme")
    vm.create(vault, template, title="Renewal", parent_value="Acme")

    with pytest.raises(vm.VaultManagerError, match="typo"):
        vm.modify_section(
            vault, template, section="Log", content="x", mode="append",
            title="Renewal", parent_value="Acme", child_suffix="typo",
        )


def test_plain_folder_with_own_folder_keeps_date_out_of_the_folder_too(vault):
    """2026-08-30 (Opportunity's own real Opportunities/<slug>/<slug>.md
    -- no date anywhere, unlike Meeting/File's dated folder or
    meeting-series' dated-folder-plain-file)."""
    import json
    template_path = vault / ".second-brain" / "data" / "Templates" / "durable-entity" / "Template.json"
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.write_text(json.dumps({
        "id": "durable-entity", "on_missing": "create",
        "root": {
            "on_existing_title": "error", "own_folder": True,
            "plain_filename": True, "plain_folder": True,
            "frontmatter_defaults": {}, "sections": [{"name": "Summary", "access": "machine_write"}],
        },
    }), encoding="utf-8")
    template = vm.load_template(vault, "durable-entity")

    result = vm.create(vault, template, note_name="Opportunities", title="Renewal")
    path = Path(result["path"])
    assert path.name == "Renewal.md"
    assert path.parent.name == "Renewal"  # no date prefix on the folder either


def test_create_with_on_existing_title_error_refuses_a_duplicate(vault):
    """create_opportunity.py's own real guard -- "an Opportunity named X
    already exists for this Customer" -- a duplicate TITLE is a mistake
    to refuse outright, not a filename collision `always_new` should
    silently disambiguate around."""
    import json
    template_path = vault / ".second-brain" / "data" / "Templates" / "strict-title" / "Template.json"
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.write_text(json.dumps({
        "id": "strict-title", "on_missing": "create",
        "root": {
            "on_existing_title": "error", "frontmatter_defaults": {},
            "sections": [{"name": "Summary", "access": "machine_write"}],
        },
    }), encoding="utf-8")
    template = vm.load_template(vault, "strict-title")

    vm.create(vault, template, note_name="Opportunities", title="Renewal")
    with pytest.raises(vm.VaultManagerError, match="Renewal"):
        vm.create(vault, template, note_name="Opportunities", title="Renewal")
    files = list((vault / "Work" / "Opportunities").rglob("*.md"))
    assert len(files) == 1


def test_link_child_into_parent_section_is_idempotent(vault):
    parent_path = _write_customer_hub(vault, "Acme")
    vm._link_child_into_parent_section(parent_path, "## Opportunities", "[[Renewal]]")
    vm._link_child_into_parent_section(parent_path, "## Opportunities", "[[Renewal]]")
    content = vm.get_section_content(parent_path, "## Opportunities")
    assert content.count("[[Renewal]]") == 1


def test_note_own_folder_wraps_the_note_in_a_matching_folder(vault):
    """Operator, 2026-08-25: meetings "sometimes... will have Attachements,
    so we might have files" -- `note_own_folder` wraps the note as
    `<stem>/<stem>.md` instead of a bare `<stem>.md`, so an attachment has
    a real place to live as the note's own sibling."""
    import json
    template_path = vault / ".second-brain" / "data" / "Templates" / "meeting" / "Template.json"
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.write_text(json.dumps({
        "id": "meeting", "on_missing": "create",
        "root": {
            "on_existing_title": "always_new", "own_folder": True,
            "frontmatter_defaults": {},
            "sections": [{"name": "Summary", "access": "machine_write"}],
        },
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
        "id": "meeting", "on_missing": "create",
        "root": {
            "on_existing_title": "always_new", "own_folder": True,
            "frontmatter_defaults": {},
            "sections": [{"name": "Summary", "access": "machine_write"}],
        },
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
        "id": "meeting-series", "on_missing": "create",
        "root": {
            "on_existing_title": "always_new", "own_folder": True, "plain_filename": True,
            "frontmatter_defaults": {},
            "sections": [{"name": "History", "access": "machine_write"}],
        },
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
        "id": "meeting", "on_missing": "create",
        "root": {
            "on_existing_title": "always_new", "own_folder": True,
            "frontmatter_defaults": {},
            "sections": [{"name": "Summary", "access": "machine_write"}],
        },
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


# ── children (fixed sibling files) + optional-parent (Customer/Partner's
# real hub+log+captures+Affiliates shape, 2026-08-30 "full migration") ──

def _write_customer_style_template(vault: Path, **parent_overrides) -> dict:
    import json
    template_path = vault / ".second-brain" / "data" / "Templates" / "customer" / "Template.json"
    template_path.parent.mkdir(parents=True, exist_ok=True)
    parent_config = {
        "note_name": "Customers", "match_fields": ["name", "title"],
        "alias_field": "aliases", "frontmatter_field": "affiliate_of",
        "link_back_section": "## Affiliates", "required": False,
        "on_missing": "auto_create", "child_subpath": "Affiliates",
    }
    parent_config.update(parent_overrides)
    template_path.write_text(json.dumps({
        "id": "customer", "on_missing": "error",
        "parent": parent_config,
        "root": {
            "on_existing_title": "error", "own_folder": True,
            "plain_filename": True, "plain_folder": True,
            "frontmatter_defaults": {"type": "Customer", "affiliate_of": ""},
            "sections": [{"name": "Affiliates", "access": "machine_write"}],
            "children": [
                {"suffix": "log", "frontmatter_defaults": {"type": "Log"}, "name_template": "{title} Log"},
                {"suffix": "captures", "frontmatter_defaults": {"type": "Captures"}, "name_template": "{title} Captures"},
            ],
        },
    }), encoding="utf-8")
    return vm.load_template(vault, "customer")


def test_create_with_children_writes_fixed_sibling_files(vault):
    template = _write_customer_style_template(vault)
    result = vm.create(vault, template, title="Adnoc", note_name="Customers")
    root_path = Path(result["path"])
    assert root_path.name == "Adnoc.md"
    assert root_path.parent.name == "Adnoc"  # own_folder + plain_folder -- no date

    log_path = root_path.parent / "Adnoc-log.md"
    captures_path = root_path.parent / "Adnoc-captures.md"
    assert log_path.is_file()
    assert captures_path.is_file()

    log_frontmatter, log_body = vm.read_note(log_path)
    assert log_frontmatter["type"] == "Log"
    assert log_frontmatter["name"] == "Adnoc Log"
    assert log_frontmatter["parent"] == "[[Adnoc]]"
    assert log_body.strip() == "# Adnoc"
    # frontmatter comes BEFORE the heading -- deliberate correction of
    # the original hand-rolled script's own header-above-frontmatter bug
    assert log_path.read_text(encoding="utf-8").startswith("---\n")

    captures_frontmatter, _ = vm.read_note(captures_path)
    assert captures_frontmatter["name"] == "Adnoc Captures"


def test_create_top_level_with_optional_parent_needs_no_parent_value(vault):
    """Customer/Partner's own real shape -- `parent.required: False` --
    a top-level entity has no parent at all; a bare create() with no
    parent_value must NOT raise the way Opportunity's own required
    parent would."""
    template = _write_customer_style_template(vault)
    result = vm.create(vault, template, title="Aldar", note_name="Customers")
    frontmatter, _ = vm.read_note(Path(result["path"]))
    assert frontmatter["affiliate_of"] == ""  # the static default, untouched


def test_create_affiliate_resolves_real_parent_and_derives_note_name(vault):
    template = _write_customer_style_template(vault)
    vm.create(vault, template, title="Adnoc", note_name="Customers")

    result = vm.create(vault, template, title="Adnoc Gas", parent_value="Adnoc")
    path = Path(result["path"])
    assert path.parent.parent == vault / "Work" / "Customers" / "Adnoc" / "Affiliates"

    frontmatter, _ = vm.read_note(path)
    assert frontmatter["affiliate_of"] == "Adnoc"

    parent_path = vault / "Work" / "Customers" / "Adnoc" / "Adnoc.md"
    backlink_section = vm.get_section_content(parent_path, "## Affiliates")
    assert "[[Adnoc Gas]]" in backlink_section


def test_create_affiliate_with_unknown_parent_auto_creates_a_blank_one(vault):
    """create_companies_partners.py's own real "Add the Parent if it's
    not in the file" behavior -- the parent never existed as its own
    Entities.md row, only inferred from the child's own Affiliate-of
    text."""
    template = _write_customer_style_template(vault)
    result = vm.create(vault, template, title="Presight", parent_value="G42")

    auto_parent_path = vault / "Work" / "Customers" / "G42" / "G42.md"
    assert auto_parent_path.is_file()
    auto_parent_frontmatter, _ = vm.read_note(auto_parent_path)
    assert auto_parent_frontmatter["affiliate_of"] == ""  # blank, never fabricated beyond its own title

    child_path = Path(result["path"])
    assert child_path.parent.parent == vault / "Work" / "Customers" / "G42" / "Affiliates"

    backlink_section = vm.get_section_content(auto_parent_path, "## Affiliates")
    assert "[[Presight]]" in backlink_section


def test_children_index_section_auto_lists_child_wikilinks(vault):
    import json
    template_path = vault / ".second-brain" / "data" / "Templates" / "customer2" / "Template.json"
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.write_text(json.dumps({
        "id": "customer2", "on_missing": "error",
        "root": {
            "on_existing_title": "error", "own_folder": True,
            "plain_filename": True, "plain_folder": True,
            "frontmatter_defaults": {"type": "Customer"},
            "sections": [{"name": "Log & Captures", "access": "machine_write"}],
            "children_index_section": "Log & Captures",
            "children": [
                {"suffix": "log", "display_label": "Log"},
                {"suffix": "captures", "display_label": "Captures"},
            ],
        },
    }), encoding="utf-8")
    template = vm.load_template(vault, "customer2")
    result = vm.create(vault, template, title="Adnoc", note_name="Customers")
    section = vm.get_section_content(Path(result["path"]), "Log & Captures")
    assert section == "- [[Adnoc-log|Log]]\n- [[Adnoc-captures|Captures]]"


def test_merge_tags_is_additive_and_idempotent(vault):
    path = vault / "Work" / "People" / "jane.md"
    vm.write_note(path, {"type": "Person", "tags": ["kind/person"]}, "\nJane\n")
    changed_first = vm.merge_tags(path, ["customer/adnoc"])
    changed_second = vm.merge_tags(path, ["customer/adnoc"])
    frontmatter, _ = vm.read_note(path)
    assert frontmatter["tags"] == ["kind/person", "customer/adnoc"]
    assert changed_first is True
    assert changed_second is False  # already present -- no real write needed


def test_upsert_namespaced_tag_replaces_same_namespace_only(vault):
    path = vault / "Work" / "Threads" / "t.md"
    vm.write_note(path, {"type": "Thread", "tags": ["engagement/partner", "kind/thread"]}, "\n")
    vm.upsert_namespaced_tag(path, "engagement", "engagement/customer")
    frontmatter, _ = vm.read_note(path)
    assert frontmatter["tags"] == ["kind/thread", "engagement/customer"]


def test_insert_body_line_if_missing_is_idempotent(vault):
    path = vault / "Work" / "People" / "jane.md"
    vm.write_note(path, {"type": "Person"}, "\nExisting content.\n")
    first = vm.insert_body_line_if_missing(path, "**Customer:** [[Adnoc]]")
    second = vm.insert_body_line_if_missing(path, "**Customer:** [[Adnoc]]")
    _, body = vm.read_note(path)
    assert body.count("**Customer:** [[Adnoc]]") == 1
    assert "Existing content." in body
    assert first is True
    assert second is False
