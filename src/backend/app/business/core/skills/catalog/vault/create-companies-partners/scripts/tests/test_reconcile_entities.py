"""The reconciler, tested where being wrong is expensive.

This is the only step in the nightly pass that MOVES and DELETES real folders,
and it runs unattended. Every test here pins a way it could destroy or duplicate
something rather than merely fail: a merge that swallows an existing folder, a
tag left behind so one company answers to two names, a deletion that takes a
Person note's enrichment with it.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def entities(*blocks: str) -> str:
    return "\n".join(blocks)


def entry(name: str, *, domain: str = "", affiliate_of: str = "",
          deleted: str = "No", ignore: str = "No") -> str:
    # Tab-indented fields, exactly as render_entities writes them. A "- " list
    # prefix makes every key miss _KNOWN_FIELDS, so the entry parses with an
    # EMPTY fields dict -- which reads downstream as "nothing to do" rather than
    # as a malformed file, and silently passed four of these tests.
    return (f"### {name}\n\n"
            f"\tCompany Name: {name}\n\n"
            f"\tAliases: \n\n"
            f"\tAffiliate of: {affiliate_of}\n\n"
            f"\tCreated: Yes\n\n"
            f"\tIgnore: {ignore}\n\n"
            f"\tDomain: {domain}\n\n"
            f"\tDeleted: {deleted}\n\n")


def hub(root: Path, kind: str, name: str, *, parent: str | None = None) -> Path:
    base = root / "Work" / ("Customers" if kind == "customer" else "Partners")
    folder = (base / parent / "Affiliates" / name) if parent else (base / name)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{name}.md").write_text(
        f'---\ntype: "{"Customer" if kind == "customer" else "Partner"}"\n'
        f'name: "{name}"\naffiliate_of: ""\n'
        f'tags: ["{kind}/{name.lower()}"]\n---\n\n## Affiliates\n\n\n## Related\n',
        encoding="utf-8")
    return folder


def person(folder: Path, email: str, kind: str, hub_name: str) -> Path:
    people = folder / "People"
    people.mkdir(parents=True, exist_ok=True)
    path = people / f"{email}.md"
    label = "Customer" if kind == "customer" else "Partner"
    path.write_text(
        f'---\ntype: "Person"\nemail: "{email}"\nrole: "Head of Data"\n'
        f'tags: ["{kind}/{hub_name.lower()}", "kind/person"]\n---\n\n'
        f"**{label}:** [[{hub_name}]]\n",
        encoding="utf-8")
    return path


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    monkeypatch.setenv("SECOND_BRAIN_DATA_PATH", str(tmp_path / "config"))
    settings = tmp_path / "config" / "Settings"
    settings.mkdir(parents=True)
    (tmp_path / "Work" / "People").mkdir(parents=True)
    return tmp_path, settings / "Entities.md"


def run(vault_path, entities_path, **kwargs):
    import reconcile_entities as r
    return r.reconcile(vault_path, entities_path, **kwargs)


def test_a_partner_becoming_a_customer_moves_and_never_duplicates(vault):
    vault_path, entities_path = vault
    folder = hub(vault_path, "partner", "Acme")
    person(folder, "someone@acme.com", "partner", "Acme")
    entities_path.write_text("## Companies\n" + entry("Acme", domain="acme.com")
                             + "\n## Partners\n", encoding="utf-8")

    result = run(vault_path, entities_path)

    assert not (vault_path / "Work" / "Partners" / "Acme").exists(), \
        "the old folder must be GONE, not left as a second copy"
    assert (vault_path / "Work" / "Customers" / "Acme" / "Acme.md").is_file()
    assert result["reclassified"] == ["Acme: partner -> customer"]


def test_the_stale_company_tag_is_replaced_vault_wide_not_merged(vault):
    """Leaving `partner/acme` beside `customer/acme` is exactly the double the
    move exists to prevent -- every tag-driven view would list it twice."""
    vault_path, entities_path = vault
    folder = hub(vault_path, "partner", "Acme")
    person(folder, "someone@acme.com", "partner", "Acme")
    thread = vault_path / "Work" / "Threads" / "t1"
    thread.mkdir(parents=True)
    (thread / "t1.md").write_text(
        '---\ntype: "Thread"\ntags: ["partner/acme", "kind/thread"]\n---\n\n## Summary\n',
        encoding="utf-8")
    entities_path.write_text("## Companies\n" + entry("Acme") + "\n## Partners\n",
                             encoding="utf-8")

    run(vault_path, entities_path)

    import vault_manager as vm
    fm, _ = vm.read_note(thread / "t1.md")
    assert "customer/acme" in fm["tags"]
    assert "partner/acme" not in fm["tags"]
    assert "kind/thread" in fm["tags"], "unrelated tags must survive"


def test_the_person_label_line_follows_the_reclassification(vault):
    vault_path, entities_path = vault
    folder = hub(vault_path, "partner", "Acme")
    person(folder, "someone@acme.com", "partner", "Acme")
    entities_path.write_text("## Companies\n" + entry("Acme") + "\n## Partners\n",
                             encoding="utf-8")

    run(vault_path, entities_path)

    moved = vault_path / "Work" / "Customers" / "Acme" / "People" / "someone@acme.com.md"
    text = moved.read_text(encoding="utf-8")
    assert "**Customer:** [[Acme]]" in text
    assert "**Partner:**" not in text, "a stale label contradicts the note's own tag"


def test_an_affiliate_named_later_is_moved_under_its_parent(vault):
    vault_path, entities_path = vault
    hub(vault_path, "customer", "Mubadala")
    hub(vault_path, "customer", "Masdar")
    entities_path.write_text(
        "## Companies\n" + entry("Mubadala") + entry("Masdar", affiliate_of="Mubadala")
        + "\n## Partners\n", encoding="utf-8")

    result = run(vault_path, entities_path)

    assert (vault_path / "Work" / "Customers" / "Mubadala" / "Affiliates"
            / "Masdar" / "Masdar.md").is_file()
    assert not (vault_path / "Work" / "Customers" / "Masdar").exists()
    assert result["reparented"] == ["Masdar: top-level -> Mubadala"]
    parent_text = (vault_path / "Work" / "Customers" / "Mubadala" / "Mubadala.md"
                   ).read_text(encoding="utf-8")
    assert "- [[Masdar]]" in parent_text, "the parent must link down to it"


def test_an_affiliate_whose_parent_has_no_folder_is_refused_not_guessed(vault):
    vault_path, entities_path = vault
    hub(vault_path, "customer", "Masdar")
    entities_path.write_text("## Companies\n" + entry("Masdar", affiliate_of="Nowhere")
                             + "\n## Partners\n", encoding="utf-8")

    result = run(vault_path, entities_path)

    assert (vault_path / "Work" / "Customers" / "Masdar" / "Masdar.md").is_file()
    assert any("Nowhere" in r for r in result["refused"])


def test_a_move_onto_an_existing_folder_is_refused_never_merged(vault):
    """Two folders for one slug means the operator has real notes in both.
    Silently merging them loses whichever file collides."""
    vault_path, entities_path = vault
    hub(vault_path, "partner", "Acme")
    hub(vault_path, "customer", "Acme")
    entities_path.write_text("## Companies\n" + entry("Acme") + "\n## Partners\n",
                             encoding="utf-8")

    result = run(vault_path, entities_path)

    assert (vault_path / "Work" / "Partners" / "Acme").exists()
    assert (vault_path / "Work" / "Customers" / "Acme").exists()
    assert any("refusing to merge" in r for r in result["refused"])


def test_a_deletion_needs_allow_delete(vault):
    vault_path, entities_path = vault
    hub(vault_path, "partner", "Gone")
    entities_path.write_text("## Companies\n\n## Partners\n"
                             + entry("Gone", deleted="Yes"), encoding="utf-8")

    result = run(vault_path, entities_path)

    assert (vault_path / "Work" / "Partners" / "Gone").exists()
    assert any("--allow-delete" in r for r in result["refused"])


def test_people_are_rescued_before_the_folder_is_deleted(vault):
    """Capture would recreate the Person note but not the role or department
    enrichment filled in. A folder deletion was never asked to destroy that."""
    vault_path, entities_path = vault
    folder = hub(vault_path, "partner", "Gone")
    person(folder, "someone@gone.com", "partner", "Gone")
    entities_path.write_text("## Companies\n\n## Partners\n"
                             + entry("Gone", deleted="Yes"), encoding="utf-8")

    result = run(vault_path, entities_path, allow_delete=True)

    assert not (vault_path / "Work" / "Partners" / "Gone").exists()
    rescued = vault_path / "Work" / "People" / "someone@gone.com.md"
    assert rescued.is_file()
    assert "Head of Data" in rescued.read_text(encoding="utf-8")
    assert result["people_rescued_from_deleted_folders"] == 1


def test_a_dry_run_changes_nothing_on_disk(vault):
    vault_path, entities_path = vault
    hub(vault_path, "partner", "Acme")
    entities_path.write_text("## Companies\n" + entry("Acme") + "\n## Partners\n",
                             encoding="utf-8")

    result = run(vault_path, entities_path, dry_run=True)

    assert (vault_path / "Work" / "Partners" / "Acme").exists()
    assert not (vault_path / "Work" / "Customers" / "Acme").exists()
    assert result["reclassified"] == ["Acme: partner -> customer"]


def test_an_entity_already_in_the_right_place_is_left_alone(vault):
    vault_path, entities_path = vault
    hub(vault_path, "customer", "Acme")
    entities_path.write_text("## Companies\n" + entry("Acme") + "\n## Partners\n",
                             encoding="utf-8")

    result = run(vault_path, entities_path)

    assert result["reclassified"] == []
    assert result["reparented"] == []
    assert result["refused"] == []
