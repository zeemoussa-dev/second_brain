"""The backend must find a Person wherever the People pipeline filed them.

It searched Work/Customers/*/People only. The pipeline files people under
Partners too, and under an Affiliate one level deeper -- most filed people in a
real vault -- so the Cockpit would have stopped finding them.

Which folders hold People is no longer compiled into the framework: plugins
register them, and until one does, Customers and Partners are still searched
(Entities plan Phase 2).
"""
from types import SimpleNamespace

import pytest

from app.business import people_extraction
from app.business.core.plugins import plugin_manager as plugin_manager_module
from app.data_access import vault_writer

_COMPANY_FOLDERS = ["Work/Customers", "Work/Partners"]


def person(vault, *parts):
    path = vault.joinpath("Work", *parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('---\ntype: "Person"\nname: "Someone"\n---\n', encoding="utf-8")
    return path


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    monkeypatch.setattr(vault_writer, "settings", SimpleNamespace(vault_path=tmp_path))
    return tmp_path


def test_a_person_filed_under_a_partner_is_found(vault):
    filed = person(vault, "Partners", "Microsoft", "People", "jane@microsoft.com.md")
    assert vault_writer.find_person_note_path("jane@microsoft.com", _COMPANY_FOLDERS) == filed


def test_a_person_filed_under_an_affiliate_is_found(vault):
    filed = person(vault, "Partners", "G42", "Affiliates", "M42", "People", "sam@m42.ae.md")
    assert vault_writer.find_person_note_path("sam@m42.ae", _COMPANY_FOLDERS) == filed


def test_a_person_filed_under_a_customer_is_still_found(vault):
    filed = person(vault, "Customers", "ADNOC", "People", "ali@adnoc.ae.md")
    assert vault_writer.find_person_note_path("ali@adnoc.ae", _COMPANY_FOLDERS) == filed


def test_the_flat_folder_is_still_the_fallback(vault):
    flat = person(vault, "People", "someone@gmail.com.md")
    assert vault_writer.find_person_note_path("someone@gmail.com", _COMPANY_FOLDERS) == flat


def test_an_unknown_person_is_not_found(vault):
    (vault / "Work" / "People").mkdir(parents=True)
    assert vault_writer.find_person_note_path("ghost@nowhere.com", _COMPANY_FOLDERS) is None


def test_only_the_given_folders_are_searched(vault):
    person(vault, "Customers", "ADNOC", "People", "ali@adnoc.ae.md")
    assert vault_writer.find_person_note_path("ali@adnoc.ae", ["Work/Clients"]) is None


def test_cockpit_searches_the_folders_plugins_register(vault, monkeypatch):
    filed = person(vault, "Clients", "Acme", "People", "bo@acme.com.md")
    monkeypatch.setattr(plugin_manager_module, "_plugin_people_folders", ["Work/Clients"])

    assert people_extraction.find_existing_person_note("bo@acme.com") == {"note_path": str(filed), "name": "Someone"}


def test_until_a_plugin_registers_folders_customers_and_partners_are_searched(vault, monkeypatch):
    filed = person(vault, "Customers", "ADNOC", "People", "ali@adnoc.ae.md")
    monkeypatch.setattr(plugin_manager_module, "_plugin_people_folders", [])

    assert people_extraction.people_folders() == _COMPANY_FOLDERS
    assert people_extraction.find_existing_person_note("ali@adnoc.ae")["note_path"] == str(filed)
