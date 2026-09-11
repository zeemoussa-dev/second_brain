"""The Company pipeline's People step: what a Thread's reader saw about each
person, onto their note -- wherever the People pipeline has filed it.

One model read fans out to Person notes other threads reference, so a
hallucinated job title would otherwise land permanently. These pin the rule
that prevents it: blanks are filled, a differing value is LOGGED and the
existing one kept, and nobody is created or renamed.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import vault_manager as vm

_THREAD = "2026-09-10 Example"


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    monkeypatch.setenv("SECOND_BRAIN_DATA_PATH", str(tmp_path / "config"))
    (tmp_path / "Work" / "People").mkdir(parents=True)
    thread_dir = tmp_path / "Work" / "Threads" / _THREAD
    thread_dir.mkdir(parents=True)
    (thread_dir / f"{_THREAD}.md").write_text(
        '---\ntype: "Thread"\nid: "conv-1"\nlast_message_at: "2026-06-18 13:05:39+00:00"\n'
        '---\n\n## Summary\n', encoding="utf-8")
    return tmp_path


def person(vault: Path, email: str, *, folder: Path | None = None, **fields) -> Path:
    lines = ["---", 'type: "Person"', f'name: "{fields.pop("name", email)}"', f'email: "{email}"']
    for key in ("phone", "linkedin", "department", "role", "company"):
        lines.append(f'{key}: "{fields.get(key, "")}"')
    lines += ['tags: ["kind/person"]', "---", "", "## Notes", ""]
    folder = folder or vault / "Work" / "People"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{email}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def saved(*people) -> None:
    import apply_thread_extract as a
    a.persist({"schema_version": 1, "thread_path": f"Work/Threads/{_THREAD}/{_THREAD}.md",
               "summary": "s", "companies": [], "people": list(people),
               "actions": [], "important_info": []}, "conv-1")


def history(note: Path) -> list[str]:
    lines = [line.strip() for line in vm.read_note(note)[1].splitlines()]
    if "## History" not in lines:
        return []
    return [line for line in lines[lines.index("## History") + 1:] if line.startswith("- ")]


def test_a_blank_field_is_filled(vault):
    import people_from_extracts as p
    note = person(vault, "someone@adnoc.ae")
    saved({"email": "someone@adnoc.ae", "job_title": "Head of Data", "department": "IT"})
    result = p.run(vault)
    fm, _ = vm.read_note(note)
    assert (fm["role"], fm["department"]) == ("Head of Data", "IT")
    assert result["fields_filled"] == 2 and history(note) == []


def test_a_person_filed_under_a_company_is_found(vault):
    """The People pipeline moves people into their hub; a lookup of the flat
    folder alone would stop filling every one of them."""
    import people_from_extracts as p
    note = person(vault, "someone@adnoc.ae",
                  folder=vault / "Work" / "Customers" / "ADNOC" / "Affiliates" / "ADNOC Gas" / "People")
    saved({"email": "someone@adnoc.ae", "phone": "+971 2 000 0000"})
    p.run(vault)
    assert vm.read_note(note)[0]["phone"] == "+971 2 000 0000"


def test_a_different_value_is_logged_and_the_existing_one_kept(vault):
    import people_from_extracts as p
    note = person(vault, "someone@adnoc.ae", role="Chief Data Officer")
    saved({"email": "someone@adnoc.ae", "job_title": "Intern"})
    result = p.run(vault)
    assert vm.read_note(note)[0]["role"] == "Chief Data Officer"
    assert history(note) == ['- 2026-06-18 · role: "Chief Data Officer" → "Intern" '
                             f"(read in [[{_THREAD}]]; the existing value was kept)"]
    assert result["changes_logged"] == 1


def test_the_same_value_in_another_case_is_not_a_change(vault):
    import people_from_extracts as p
    note = person(vault, "someone@adnoc.ae", role="Head of Data")
    saved({"email": "someone@adnoc.ae", "job_title": "head of data"})
    assert p.run(vault)["changes_logged"] == 0 and history(note) == []


def test_a_rerun_fills_and_logs_nothing_twice(vault):
    import people_from_extracts as p
    note = person(vault, "someone@adnoc.ae", role="Director")
    saved({"email": "someone@adnoc.ae", "job_title": "VP", "department": "Sales"})
    first, second = p.run(vault), p.run(vault)
    assert (first["changes_logged"], first["fields_filled"]) == (1, 1)
    assert (second["changes_logged"], second["fields_filled"]) == (0, 0)
    assert len(history(note)) == 1


def test_the_same_change_seen_elsewhere_is_logged_once(vault):
    """Two Threads carrying one signature are one change, not two entries."""
    import people_from_extracts as p
    note = person(vault, "someone@adnoc.ae", role="Director")
    p.apply_people(vault, {"people": [{"email": "someone@adnoc.ae", "job_title": "VP"}]},
                   "[[Thread A]]", "2026-06-01")
    p.apply_people(vault, {"people": [{"email": "someone@adnoc.ae", "job_title": "VP"}]},
                   "[[Thread B]]", "2026-07-01")
    assert len(history(note)) == 1


def test_a_person_not_in_the_vault_is_not_created(vault):
    """Capture owns Person creation, from real message headers -- not a
    model's reading of a signature."""
    import people_from_extracts as p
    saved({"email": "ghost@nowhere.com", "job_title": "VP"})
    assert p.run(vault)["people_not_in_vault"] == 1
    assert not (vault / "Work" / "People" / "ghost@nowhere.com.md").exists()


def test_name_and_email_are_never_written(vault):
    import people_from_extracts as p
    note = person(vault, "someone@adnoc.ae", name="Real Name")
    saved({"email": "someone@adnoc.ae", "name": "Wrong Name", "job_title": "Head"})
    p.run(vault)
    fm, _ = vm.read_note(note)
    assert (fm["name"], fm["email"]) == ("Real Name", "someone@adnoc.ae")
    assert history(note) == []


def test_a_dry_run_writes_nothing(vault):
    import people_from_extracts as p
    note = person(vault, "someone@adnoc.ae", role="Director")
    before = note.read_text(encoding="utf-8")
    saved({"email": "someone@adnoc.ae", "job_title": "VP", "phone": "1"})
    result = p.run(vault, dry_run=True)
    assert (result["changes_logged"], result["fields_filled"]) == (1, 1)
    assert note.read_text(encoding="utf-8") == before
