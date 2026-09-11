"""The backend must find a Person wherever the People pipeline filed them.

It searched Work/Customers/*/People only. The pipeline files people under
Partners too, and under an Affiliate one level deeper -- most filed people in a
real vault -- so the Cockpit would have stopped finding them.
"""
from types import SimpleNamespace

from app.data_access import vault_writer


def person(vault, *parts):
    path = vault.joinpath("Work", *parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('---\ntype: "Person"\n---\n', encoding="utf-8")
    return path


def use(monkeypatch, vault):
    monkeypatch.setattr(vault_writer, "settings", SimpleNamespace(vault_path=vault))


def test_a_person_filed_under_a_partner_is_found(tmp_path, monkeypatch):
    use(monkeypatch, tmp_path)
    filed = person(tmp_path, "Partners", "Microsoft", "People", "jane@microsoft.com.md")
    assert vault_writer.find_person_note_path("jane@microsoft.com") == filed


def test_a_person_filed_under_an_affiliate_is_found(tmp_path, monkeypatch):
    use(monkeypatch, tmp_path)
    filed = person(tmp_path, "Partners", "G42", "Affiliates", "M42", "People", "sam@m42.ae.md")
    assert vault_writer.find_person_note_path("sam@m42.ae") == filed


def test_a_person_filed_under_a_customer_is_still_found(tmp_path, monkeypatch):
    use(monkeypatch, tmp_path)
    filed = person(tmp_path, "Customers", "ADNOC", "People", "ali@adnoc.ae.md")
    assert vault_writer.find_person_note_path("ali@adnoc.ae") == filed


def test_the_flat_folder_is_still_the_fallback(tmp_path, monkeypatch):
    use(monkeypatch, tmp_path)
    flat = person(tmp_path, "People", "someone@gmail.com.md")
    assert vault_writer.find_person_note_path("someone@gmail.com") == flat


def test_an_unknown_person_is_not_found(tmp_path, monkeypatch):
    use(monkeypatch, tmp_path)
    (tmp_path / "Work" / "People").mkdir(parents=True)
    assert vault_writer.find_person_note_path("ghost@nowhere.com") is None
