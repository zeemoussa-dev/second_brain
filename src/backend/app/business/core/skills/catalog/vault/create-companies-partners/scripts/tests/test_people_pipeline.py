"""The People pipeline: move, and -- when capture recreated a filed person --
fill, log what changed, delete the duplicate. Every test pins a way the pass
could lose or duplicate a person rather than merely fail."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import vault_manager as vm


def hub(vault: Path, kind: str, name: str, domain: str, aliases=()) -> Path:
    folder = vault / "Work" / ("Customers" if kind == "customer" else "Partners") / name
    folder.mkdir(parents=True)
    alias_line = "aliases: [" + ", ".join(f'"{a}"' for a in aliases) + "]\n" if aliases else ""
    (folder / f"{name}.md").write_text(
        f'---\ntype: "{"Customer" if kind == "customer" else "Partner"}"\nname: "{name}"\n'
        f'domain: "{domain}"\n{alias_line}---\n\n## Summary\n', encoding="utf-8")
    return folder


def person(folder: Path, email: str, body: str = "", **fields) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    lines = ["---", 'type: "Person"', f'email: "{email}"']
    for key in ("name", "department", "role", "company", "phone", "linkedin"):
        lines.append(f'{key}: "{fields.get(key, "")}"')
    lines += ['tags: ["kind/person"]', "---", "", body]
    path = folder / f"{email}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


@pytest.fixture()
def vault(tmp_path):
    (tmp_path / "Work" / "People").mkdir(parents=True)
    return tmp_path


def flat(vault: Path) -> Path:
    return vault / "Work" / "People"


def test_a_person_is_moved_under_their_company(vault):
    import people_pipeline as p
    acme = hub(vault, "partner", "Acme", "acme.com")
    person(flat(vault), "jane@acme.com", name="Jane")

    result = p.run(vault)

    moved = acme / "People" / "jane@acme.com.md"
    assert moved.is_file() and not (flat(vault) / "jane@acme.com.md").exists()
    fm, body = vm.read_note(moved)
    assert "partner/acme" in fm["tags"]
    assert "**Partner:** [[Acme]]" in body
    assert result["moved_into_hubs"] == 1


def test_an_alias_domain_files_the_person_too(vault):
    import people_pipeline as p
    ms = hub(vault, "partner", "Microsoft", "microsoft.com", aliases=["techsupport.microsoft.com"])
    person(flat(vault), "desk@techsupport.microsoft.com")
    p.run(vault)
    assert (ms / "People" / "desk@techsupport.microsoft.com.md").is_file()


def test_a_person_with_no_company_stays_flat(vault):
    import people_pipeline as p
    person(flat(vault), "me@core42.ai")
    result = p.run(vault)
    assert (flat(vault) / "me@core42.ai.md").is_file()
    assert result["left_flat_no_hub"] == 1


def test_an_identical_duplicate_is_deleted_and_nothing_is_logged(vault):
    import people_pipeline as p
    acme = hub(vault, "partner", "Acme", "acme.com")
    filed = person(acme / "People", "jane@acme.com", "**Partner:** [[Acme]]", role="CTO")
    person(flat(vault), "jane@acme.com", role="CTO")

    result = p.run(vault)

    assert not (flat(vault) / "jane@acme.com.md").exists()
    assert "## History" not in filed.read_text(encoding="utf-8")
    assert result["duplicates_removed"] == 1 and result["changes_logged"] == 0


def test_a_blank_field_on_the_filed_note_is_filled(vault):
    import people_pipeline as p
    acme = hub(vault, "partner", "Acme", "acme.com")
    filed = person(acme / "People", "jane@acme.com", "**Partner:** [[Acme]]")
    person(flat(vault), "jane@acme.com", department="Data")

    p.run(vault)

    assert vm.read_note(filed)[0]["department"] == "Data"


def test_a_changed_value_goes_to_history_and_the_existing_one_is_kept(vault):
    """The operator's rule: a change goes to a log. Neither silently
    overwritten nor silently dropped."""
    import people_pipeline as p
    acme = hub(vault, "partner", "Acme", "acme.com")
    filed = person(acme / "People", "jane@acme.com", "**Partner:** [[Acme]]", role="Director")
    person(flat(vault), "jane@acme.com", role="VP Engineering")

    result = p.run(vault)

    fm, body = vm.read_note(filed)
    assert fm["role"] == "Director", "the existing value must be kept"
    assert "## History" in body
    assert 'role: "Director" → "VP Engineering"' in body
    assert not (flat(vault) / "jane@acme.com.md").exists()
    assert result["changes_logged"] == 1


def test_history_entries_accumulate_in_the_history_section(vault):
    import people_pipeline as p
    acme = hub(vault, "partner", "Acme", "acme.com")
    filed = person(acme / "People", "jane@acme.com",
                   "**Partner:** [[Acme]]\n\n## History\n\n- 2026-01-01 · role: \"A\" → \"B\"\n\n## Other\n\nkeep",
                   role="Director")
    person(flat(vault), "jane@acme.com", role="VP")

    p.run(vault)

    body = vm.read_note(filed)[1]
    history = body.split("## History", 1)[1].split("## Other", 1)[0]
    assert '"A" → "B"' in history and '"Director" → "VP"' in history
    assert body.rstrip().endswith("keep"), "the section after History must be untouched"


def test_a_duplicate_someone_wrote_in_is_never_deleted(vault):
    import people_pipeline as p
    acme = hub(vault, "partner", "Acme", "acme.com")
    person(acme / "People", "jane@acme.com", "**Partner:** [[Acme]]")
    person(flat(vault), "jane@acme.com", "Met her at GITEX -- follow up on the pilot.")

    result = p.run(vault)

    assert (flat(vault) / "jane@acme.com.md").is_file()
    assert result["needs_review"] == ["jane@acme.com.md"]


def test_a_dry_run_changes_nothing(vault):
    import people_pipeline as p
    acme = hub(vault, "partner", "Acme", "acme.com")
    person(flat(vault), "jane@acme.com")
    result = p.run(vault, dry_run=True)
    assert (flat(vault) / "jane@acme.com.md").is_file()
    assert not (acme / "People").exists()
    assert result["moved_into_hubs"] == 1
