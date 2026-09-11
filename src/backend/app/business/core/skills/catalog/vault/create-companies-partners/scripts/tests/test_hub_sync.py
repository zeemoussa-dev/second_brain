"""Hub notes keep up with Entities.md, and the owner's own company stays off
Threads and Meetings.

A hub took its Domain and Aliases at creation and never again, so a domain
added afterwards (sa.ey.com on EY, taqa.com on TAQA) never reached the note
People and Tagging read -- nobody at it was ever filed. And Tagging matched a
hub's `domain` only, never its aliases.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import vault_manager as vm  # noqa: E402


def entry(name: str, *, domain: str = "", aliases: str = "", ignore: str = "No") -> str:
    return (f"### {name}\n\n"
            f"\tCompany Name: {name}\n\n"
            f"\tAliases: {aliases}\n\n"
            f"\tAffiliate of: \n\n"
            f"\tCreated: Yes\n\n"
            f"\tIgnore: {ignore}\n\n"
            f"\tDomain: {domain}\n\n"
            f"\tDeleted: No\n\n")


def hub(root: Path, kind: str, name: str, *, domain: str = "", aliases=()) -> Path:
    folder = root / "Work" / ("Customers" if kind == "customer" else "Partners") / name
    folder.mkdir(parents=True, exist_ok=True)
    alias_line = ("aliases: [" + ", ".join(f'"{a}"' for a in aliases) + "]\n") if aliases else ""
    path = folder / f"{name}.md"
    path.write_text(f'---\ntype: "{"Customer" if kind == "customer" else "Partner"}"\n'
                    f'name: "{name}"\ndomain: "{domain}"\n{alias_line}---\n', encoding="utf-8")
    return path


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    monkeypatch.setenv("SECOND_BRAIN_DATA_PATH", str(tmp_path / "config"))
    monkeypatch.delenv("SECOND_BRAIN_SELF_EMAIL", raising=False)
    settings = tmp_path / "config" / "Settings"
    settings.mkdir(parents=True)
    (tmp_path / "Work" / "People").mkdir(parents=True)
    return tmp_path, settings / "Entities.md"


def test_entities_domains_and_aliases_reach_an_existing_hub(vault):
    import create_companies_partners as ccp
    vault_path, entities_path = vault
    note = hub(vault_path, "partner", "EY", domain="parthenon.ey.com", aliases=["es.ey.com"])
    entities_path.write_text("## Partners\n" + entry(
        "EY", domain="parthenon.ey.com, ey.com", aliases="es.ey.com, sa.ey.com"), encoding="utf-8")

    added = ccp.sync_hub_domains(vault_path, entities_path)

    frontmatter, _ = vm.read_note(note)
    assert ccp._split_domains(frontmatter["domain"]) == ["parthenon.ey.com", "ey.com"]
    assert frontmatter["aliases"] == ["es.ey.com", "sa.ey.com"]
    assert sorted(added) == ["EY: +ey.com", "EY: +sa.ey.com"]
    assert ccp.sync_hub_domains(vault_path, entities_path) == [], "nothing is added twice"


def test_a_value_entities_no_longer_lists_is_kept(vault):
    """Adding only: removing a domain is the operator's call, not a guess."""
    import create_companies_partners as ccp
    vault_path, entities_path = vault
    note = hub(vault_path, "customer", "Acme", domain="old-acme.com")
    entities_path.write_text("## Companies\n" + entry("Acme", domain="acme.com"), encoding="utf-8")
    ccp.sync_hub_domains(vault_path, entities_path)
    assert ccp._split_domains(vm.read_note(note)[0]["domain"]) == ["old-acme.com", "acme.com"]


def test_an_ignored_entry_changes_nothing(vault):
    import create_companies_partners as ccp
    vault_path, entities_path = vault
    note = hub(vault_path, "customer", "Acme", domain="acme.com")
    entities_path.write_text("## Companies\n" + entry("Acme", domain="acme.com, more.com",
                                                      ignore="Yes"), encoding="utf-8")
    assert ccp.sync_hub_domains(vault_path, entities_path) == []
    assert vm.read_note(note)[0]["domain"] == "acme.com"


def test_a_person_is_tagged_by_an_alias_domain(vault):
    import create_companies_partners as ccp
    vault_path, _ = vault
    hub(vault_path, "customer", "TAQA", domain="taqadistribution.com", aliases=["taqa.com"])
    person = vault_path / "Work" / "People" / "someone@taqa.com.md"
    person.write_text('---\ntype: "Person"\nemail: "someone@taqa.com"\ntags: ["kind/person"]\n---\n',
                      encoding="utf-8")
    ccp.retag_people_by_domain(vault_path)
    assert "customer/taqa" in vm.read_note(person)[0]["tags"]


def test_the_owners_own_company_is_left_off_threads_and_meetings(vault, monkeypatch):
    """Its staff are on nearly every Thread, so its link would say nothing --
    the same reason the owner's own Person links were removed."""
    import create_companies_partners as ccp
    vault_path, _ = vault
    hub(vault_path, "partner", "Core42", domain="core42.ai")
    hub(vault_path, "customer", "Acme", domain="acme.com")
    monkeypatch.setenv("SECOND_BRAIN_SELF_EMAIL", "owner@core42.ai")
    assert [stem for *_, stem in ccp._build_domain_company_index(vault_path)] == ["Acme"]
    monkeypatch.delenv("SECOND_BRAIN_SELF_EMAIL")
    assert "Core42" in [stem for *_, stem in ccp._build_domain_company_index(vault_path)]
