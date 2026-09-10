"""The extraction applier, tested where fan-out makes a mistake expensive.

One model read writes to several places, so a bad extraction no longer produces
one bad summary -- it can put a hallucinated job title permanently onto a Person
note that other threads reference. These tests pin the conservatism that
prevents that, plus the contract checks that stop a half-understood shape being
written at all.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# The REAL shipped master, not a hand-written stand-in: these tests assert
# writes into named sections, and a local copy would drift from the template the
# vault actually uses without anything noticing.
_SHIPPED_THREAD_TEMPLATE = (Path(__file__).resolve().parents[6]
                            / "templates" / "masters" / "thread" / "Template.json")


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    monkeypatch.setenv("SECOND_BRAIN_DATA_PATH", str(tmp_path / "config"))
    (tmp_path / "Work" / "People").mkdir(parents=True)
    templates = tmp_path / "config" / "data" / "Templates" / "thread"
    templates.mkdir(parents=True)
    (templates / "Template.json").write_text(
        _SHIPPED_THREAD_TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
    thread_dir = tmp_path / "Work" / "Threads" / "2026-09-10 Example"
    (thread_dir / "messages").mkdir(parents=True)
    (thread_dir / "2026-09-10 Example.md").write_text(
        '---\ntype: "Thread"\nid: "conv-1"\ntags: ["kind/thread"]\n---\n\n'
        "## Summary\n\n\n## Personal Notes\n\n\n## Actions\n\n\n"
        "## Conversation\n\n\n## Related\n\n\n## Files\n\n",
        encoding="utf-8")
    return tmp_path, thread_dir / "2026-09-10 Example.md"


def person(vault_path: Path, email: str, **fields):
    lines = ['---', 'type: "Person"', f'name: "{fields.pop("name", email)}"',
             f'email: "{email}"']
    for key in ("phone", "linkedin", "department", "role", "company"):
        lines.append(f'{key}: "{fields.get(key, "")}"')
    lines += ['tags: ["kind/person"]', '---', '', '## Notes', '']
    path = vault_path / "Work" / "People" / f"{email}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def extraction(**overrides):
    base = {"schema_version": 1, "thread_path": "Work/Threads/2026-09-10 Example/2026-09-10 Example.md",
            "summary": "They agreed to run the pilot in October.",
            "companies": [], "people": [], "actions": [], "important_info": []}
    base.update(overrides)
    return base


def test_a_blank_person_field_is_filled(vault, monkeypatch):
    vault_path, _ = vault
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parent.parent))
    import apply_thread_extract as a
    p = person(vault_path, "someone@adnoc.ae", name="Someone")
    a.apply_extract(vault_path, extraction(people=[
        {"email": "someone@adnoc.ae", "job_title": "Head of Data", "department": "IT"}]))
    import vault_manager as vm
    fm, _ = vm.read_note(p)
    assert fm["role"] == "Head of Data"
    assert fm["department"] == "IT"


def test_an_existing_person_value_is_never_overwritten(vault):
    """The rule inherited from the regex parser this replaces: a false positive
    writing a wrong job title onto a real Person note is worse than leaving it
    blank -- and fan-out makes that permanent."""
    vault_path, _ = vault
    import apply_thread_extract as a
    import vault_manager as vm
    p = person(vault_path, "someone@adnoc.ae", role="Chief Data Officer")
    result = a.apply_extract(vault_path, extraction(people=[
        {"email": "someone@adnoc.ae", "job_title": "Intern"}]))
    fm, _ = vm.read_note(p)
    assert fm["role"] == "Chief Data Officer", "an existing value must survive"
    assert result["fields_left_alone"] >= 1


def test_a_person_not_already_in_the_vault_is_not_created(vault):
    """Capture owns Person creation, from real message headers. A person a model
    inferred from a signature must not be conjured into existence here."""
    vault_path, _ = vault
    import apply_thread_extract as a
    result = a.apply_extract(vault_path, extraction(people=[
        {"email": "ghost@nowhere.com", "job_title": "VP"}]))
    assert result["people_not_in_vault"] == 1
    assert not (vault_path / "Work" / "People" / "ghost@nowhere.com.md").exists()


def test_name_and_email_are_never_written_back(vault):
    """They are the note's identity, set at capture. A model restating them is
    an opportunity to corrupt them for no gain."""
    vault_path, _ = vault
    import apply_thread_extract as a
    import vault_manager as vm
    p = person(vault_path, "someone@adnoc.ae", name="Real Name")
    a.apply_extract(vault_path, extraction(people=[
        {"email": "someone@adnoc.ae", "name": "Wrong Name", "job_title": "Head"}]))
    fm, _ = vm.read_note(p)
    assert fm["name"] == "Real Name"


def test_a_wrong_schema_version_is_refused(vault):
    """The JSON is a contract between one model pass and several appliers.
    Writing a shape only partly understood is worse than refusing."""
    vault_path, _ = vault
    import apply_thread_extract as a
    with pytest.raises(SystemExit, match="schema_version"):
        a.apply_extract(vault_path, extraction(schema_version=2))


def test_the_extraction_is_persisted_before_it_is_applied(vault):
    """So an applier bug can be fixed and re-applied without re-reading
    thousands of threads through a model."""
    vault_path, _ = vault
    import apply_thread_extract as a
    result = a.apply_extract(vault_path, extraction())
    saved = Path(result["extraction_saved_to"])
    assert saved.is_file()
    assert json.loads(saved.read_text(encoding="utf-8"))["thread_path"]


def test_actions_become_checkboxes_with_owner_and_due(vault):
    vault_path, thread_note = vault
    import apply_thread_extract as a
    import vault_manager as vm
    a.apply_extract(vault_path, extraction(actions=[
        {"text": "Send the revised SOW", "owner": "Sherif", "due": "Friday"},
        {"text": "Confirm the pilot dates"},
        {"text": "   "},                       # blank -- must be dropped
    ]))
    content = vm.get_section_content(thread_note, "Actions")
    assert "- [ ] Send the revised SOW (Sherif — Friday)" in content
    assert "- [ ] Confirm the pilot dates" in content
    assert content.count("- [ ]") == 2


def test_important_info_is_deferred_not_written_here(vault):
    """It belongs on a Customer hub's captures note, owned by
    create-companies-partners. Two scripts writing one note is how they start
    overwriting each other."""
    vault_path, _ = vault
    import apply_thread_extract as a
    result = a.apply_extract(vault_path, extraction(important_info=[
        {"text": "Budget approved for Q1", "company": "ADNOC"}]))
    assert result["important_info_deferred"] == 1
    saved = json.loads(Path(result["extraction_saved_to"]).read_text(encoding="utf-8"))
    assert saved["important_info"], "it must survive in the persisted extraction"


def test_a_thread_without_an_id_is_refused(vault):
    """The extraction is keyed on the id and section writes resolve through it.
    Minting one silently would file the extraction under a key nothing else
    knows."""
    vault_path, thread_note = vault
    thread_note.write_text('---\ntype: "Thread"\n---\n\n## Summary\n\n', encoding="utf-8")
    import apply_thread_extract as a
    with pytest.raises(SystemExit, match="no `id`"):
        a.apply_extract(vault_path, extraction())
