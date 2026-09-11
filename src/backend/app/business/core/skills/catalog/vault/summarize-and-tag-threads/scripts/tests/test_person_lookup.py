"""Enrichment must still find a person after the People pipeline files them.

It looked in the flat Work/People folder only. Once people are moved under
their company, every one of them would read as "not in the vault" and their
job title and department would silently never be filled again.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_a_filed_person_is_found(tmp_path):
    import apply_thread_extract as a
    filed = tmp_path / "Work" / "Partners" / "Acme" / "People" / "jane@acme.com.md"
    filed.parent.mkdir(parents=True)
    filed.write_text('---\ntype: "Person"\n---\n', encoding="utf-8")
    assert a._person_note(tmp_path, "Jane@Acme.com") == filed


def test_a_person_filed_under_an_affiliate_is_found(tmp_path):
    import apply_thread_extract as a
    filed = (tmp_path / "Work" / "Partners" / "G42" / "Affiliates" / "M42"
             / "People" / "sam@m42.ae.md")
    filed.parent.mkdir(parents=True)
    filed.write_text('---\ntype: "Person"\n---\n', encoding="utf-8")
    assert a._person_note(tmp_path, "sam@m42.ae") == filed


def test_the_flat_copy_is_still_found_first(tmp_path):
    import apply_thread_extract as a
    flat = tmp_path / "Work" / "People" / "jane@acme.com.md"
    flat.parent.mkdir(parents=True)
    flat.write_text('---\ntype: "Person"\n---\n', encoding="utf-8")
    assert a._person_note(tmp_path, "jane@acme.com") == flat


def test_an_unknown_person_is_still_not_found(tmp_path):
    import apply_thread_extract as a
    (tmp_path / "Work" / "People").mkdir(parents=True)
    assert a._person_note(tmp_path, "ghost@nowhere.com") is None
