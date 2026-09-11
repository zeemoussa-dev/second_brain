"""The extraction applier: the contract checks that stop a half-understood
shape being written at all, and the one-owner rule -- Enrichment writes only
onto the Thread, and saves the read for everything else.

What one read then fans out to is tested with its owner: People details and
each company's History and Captures in the Company pipeline's tests.
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


def test_person_fields_are_saved_not_written(vault):
    """People details belong to the Company pipeline, which files them from the
    saved extraction. Two writers on one Person note is how they start
    overwriting each other."""
    vault_path, _ = vault
    import apply_thread_extract as a
    import vault_manager as vm
    p = person(vault_path, "someone@adnoc.ae", name="Someone")
    result = a.apply_extract(vault_path, extraction(people=[
        {"email": "someone@adnoc.ae", "job_title": "Head of Data"}]))
    assert vm.read_note(p)[0]["role"] == ""
    assert result["people_deferred"] == 1
    saved = json.loads(Path(result["extraction_saved_to"]).read_text(encoding="utf-8"))
    assert saved["people"][0]["job_title"] == "Head of Data", "it must survive in the saved read"


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
    """It belongs on a company's captures note, filed by the Company pipeline.
    Two scripts writing one note is how they start overwriting each other."""
    vault_path, _ = vault
    import apply_thread_extract as a
    result = a.apply_extract(vault_path, extraction(important_info=[
        {"text": "Budget approved for Q1", "company": "ADNOC"}]))
    assert result["important_info_deferred"] == 1
    saved = json.loads(Path(result["extraction_saved_to"]).read_text(encoding="utf-8"))
    assert saved["important_info"], "it must survive in the persisted extraction"


def test_a_thread_given_by_id_is_found_in_code_and_its_path_saved(vault):
    """The agent names a Thread by id, never by a path it types. The saved read
    still carries the path, because Tagging and Company resolve it."""
    vault_path, _ = vault
    import apply_thread_extract as a
    data = extraction(thread_id="conv-1")
    del data["thread_path"]
    result = a.apply_extract(vault_path, data)
    saved = json.loads(Path(result["extraction_saved_to"]).read_text(encoding="utf-8"))
    assert saved["thread_path"] == "Work/Threads/2026-09-10 Example/2026-09-10 Example.md"
    assert result["summary_written"]


def test_an_unknown_thread_id_is_refused(vault):
    vault_path, _ = vault
    import apply_thread_extract as a
    data = extraction(thread_id="conv-nope")
    del data["thread_path"]
    with pytest.raises(SystemExit, match="no Thread with id"):
        a.apply_extract(vault_path, data)


def test_a_thread_without_an_id_is_refused(vault):
    """The extraction is keyed on the id and section writes resolve through it.
    Minting one silently would file the extraction under a key nothing else
    knows."""
    vault_path, thread_note = vault
    thread_note.write_text('---\ntype: "Thread"\n---\n\n## Summary\n\n', encoding="utf-8")
    import apply_thread_extract as a
    with pytest.raises(SystemExit, match="no `id`"):
        a.apply_extract(vault_path, extraction())
