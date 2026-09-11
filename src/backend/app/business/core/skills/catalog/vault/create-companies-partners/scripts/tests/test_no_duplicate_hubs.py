"""Hub creation must never make a second copy of an entity that already exists.

The 30-minute hub job checked only the exact path Entities.md implies. Change an
entity's parent or section and it created the entity AGAIN at the new path; the
nightly reconcile then refused to move the original onto it, so the duplicate
was permanent (2026-09-11: AIQ, made an Affiliate of ADNOC, appeared twice).
These run the real build against the real shipped templates.
"""
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_MASTERS = Path(__file__).resolve().parents[6] / "templates" / "masters"


def entry(name: str, *, affiliate_of: str = "") -> str:
    return (f"### {name}\n\n\tCompany Name: {name}\n\n\tAliases: \n\n"
            f"\tAffiliate of: {affiliate_of}\n\n\tCreated: No\n\n\tIgnore: No\n\n"
            f"\tDomain: {name.lower()}.com\n\n\tDeleted: No\n\n")


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    config = tmp_path / "config"
    monkeypatch.setenv("SECOND_BRAIN_DATA_PATH", str(config))
    for template_id in ("customer", "partner"):
        target = config / "data" / "Templates" / template_id
        target.mkdir(parents=True)
        shutil.copy(_MASTERS / template_id / "Template.json", target / "Template.json")
    (config / "Settings").mkdir(parents=True)
    (tmp_path / "Work" / "People").mkdir(parents=True)
    return tmp_path, config / "Settings" / "Entities.md"


def build(vault_path: Path, entities: Path, companies: str, partners: str = "") -> dict:
    import create_companies_partners as ccp
    entities.write_text("## Companies\n\n" + companies + "\n## Partners\n\n" + partners,
                        encoding="utf-8")
    return ccp.build(vault_path, entities, move_people=False)


def hub_folders(vault_path: Path, name: str) -> list[str]:
    return sorted(str(p.relative_to(vault_path / "Work")).replace("\\", "/")
                  for p in (vault_path / "Work").rglob(name) if p.is_dir())


def test_becoming_an_affiliate_does_not_create_a_second_copy(vault):
    vault_path, entities = vault
    build(vault_path, entities, entry("ADNOC") + entry("AIQ"))
    assert hub_folders(vault_path, "AIQ") == ["Customers/AIQ"]

    result = build(vault_path, entities, entry("ADNOC") + entry("AIQ", affiliate_of="ADNOC"))

    assert hub_folders(vault_path, "AIQ") == ["Customers/AIQ"], "a second AIQ was created"
    assert result["waiting_to_move"] == ["AIQ"]


def test_a_reclassification_does_not_create_a_second_copy(vault):
    vault_path, entities = vault
    build(vault_path, entities, "", entry("Acme"))
    assert hub_folders(vault_path, "Acme") == ["Partners/Acme"]

    result = build(vault_path, entities, entry("Acme"), "")

    assert hub_folders(vault_path, "Acme") == ["Partners/Acme"], "a second Acme was created"
    assert result["waiting_to_move"] == ["Acme"]


def test_the_waiting_entity_is_then_moved_by_reconcile(vault):
    """The two halves together: creation leaves it, reconcile moves it."""
    import reconcile_entities as r
    vault_path, entities = vault
    build(vault_path, entities, entry("ADNOC") + entry("AIQ"))
    build(vault_path, entities, entry("ADNOC") + entry("AIQ", affiliate_of="ADNOC"))

    result = r.reconcile(vault_path, entities)

    assert hub_folders(vault_path, "AIQ") == ["Customers/ADNOC/Affiliates/AIQ"]
    assert result["reparented"] == ["AIQ: top-level -> ADNOC"]


def test_a_genuinely_new_entity_is_still_created(vault):
    vault_path, entities = vault
    result = build(vault_path, entities, entry("Newco"))
    assert hub_folders(vault_path, "Newco") == ["Customers/Newco"]
    assert result["waiting_to_move"] == []
