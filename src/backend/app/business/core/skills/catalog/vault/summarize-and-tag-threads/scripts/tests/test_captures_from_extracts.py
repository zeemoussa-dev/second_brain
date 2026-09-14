"""The Company pipeline's Captures: each saved important fact filed under its
company's `## Captured`, with the Thread it came from -- and never a word of
the operator's own `## Notes`.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_THREAD = "2026-09-10 Example"
_NOTES = "## Notes\n\nMy own note about them.\n"


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    monkeypatch.setenv("SECOND_BRAIN_DATA_PATH", str(tmp_path / "config"))
    thread_dir = tmp_path / "Work" / "Threads" / _THREAD
    thread_dir.mkdir(parents=True)
    (thread_dir / f"{_THREAD}.md").write_text(
        '---\ntype: "Thread"\nid: "conv-1"\nlast_message_at: "2026-06-18 13:05:39+00:00"\n'
        '---\n\n## Summary\n', encoding="utf-8")
    return tmp_path


def hub(vault: Path, root: str, name: str, *, aliases=(), note_type=None,
        captures_body=None) -> Path:
    folder = vault / "Work" / root / name
    folder.mkdir(parents=True)
    kind = note_type or ("Customer" if root == "Customers" else "Partner")
    alias_line = ("aliases: [" + ", ".join(f'"{a}"' for a in aliases) + "]\n") if aliases else ""
    (folder / f"{name}.md").write_text(f'---\ntype: "{kind}"\nname: "{name}"\n{alias_line}---\n',
                                       encoding="utf-8")
    captures = folder / f"{name}-captures.md"
    if captures_body is not None:
        captures.write_text(f'---\ntype: "Captures"\nname: "{name} Captures"\n---\n{captures_body}',
                            encoding="utf-8")
    return captures


def saved(*facts) -> None:
    import apply_thread_extract as a
    a.persist({"schema_version": 1, "thread_path": f"Work/Threads/{_THREAD}/{_THREAD}.md",
               "summary": "s", "companies": [], "people": [], "actions": [],
               "important_info": list(facts)}, "conv-1")


def captured(note: Path) -> list[str]:
    after = note.read_text(encoding="utf-8").split("## Captured", 1)[1]
    return [line for line in after.splitlines() if line.startswith("- 2")]


def test_a_fact_is_filed_under_its_company_by_alias(vault):
    import captures_from_extracts as c
    note = hub(vault, "Customers", "Abu Dhabi Commercial Bank", aliases=["ADCB"],
               captures_body=f"\n# ADCB\n\n{_NOTES}\n## Captured\n")
    saved({"text": "Budget approved for the Q1 pilot.", "company": "ADCB"},
          {"text": "Unrelated", "company": "Nowhere Holdings"},
          {"text": "Names no company"})
    result = c.run(vault)
    assert captured(note) == [f"- 2026-06-18: Budget approved for the Q1 pilot -- [[{_THREAD}]]"]
    assert (result["facts_filed"], result["facts_unresolved"]) == (1, 2)


def test_the_operators_notes_are_never_touched(vault):
    import captures_from_extracts as c
    note = hub(vault, "Partners", "G42", captures_body=(
        f"\n# G42\n\n{_NOTES}\n## Captured\n\n- a line someone wrote\n"))
    saved({"text": "New CEO appointed", "company": "G42"})
    c.run(vault)
    text = note.read_text(encoding="utf-8")
    assert "My own note about them." in text.split("## Captured")[0]
    assert "- a line someone wrote" in text, "a hand-written line under Captured is kept"


def test_a_rerun_is_idempotent_and_a_reread_replaces_the_threads_facts(vault):
    import captures_from_extracts as c
    note = hub(vault, "Partners", "G42", captures_body=f"\n# G42\n\n{_NOTES}\n## Captured\n")
    saved({"text": "First fact", "company": "G42"})
    first, second = c.run(vault), c.run(vault)
    assert (first["captures_notes_written"], second["captures_notes_written"]) == (1, 0)
    saved({"text": "Revised fact", "company": "G42"})
    c.run(vault)
    assert captured(note) == [f"- 2026-06-18: Revised fact -- [[{_THREAD}]]"]


def test_a_bare_captures_note_gains_its_sections(vault):
    """A hub created after the migration ran has a captures note with no
    sections at all."""
    import captures_from_extracts as c
    note = hub(vault, "Customers", "ADAA", captures_body="\n# ADAA\n")
    saved({"text": "Audit scope agreed", "company": "ADAA"})
    c.run(vault)
    text = note.read_text(encoding="utf-8")
    assert text.index("## Notes") < text.index("## Captured")
    assert captured(note) == [f"- 2026-06-18: Audit scope agreed -- [[{_THREAD}]]"]


def test_an_opportunity_never_gets_captures(vault):
    import captures_from_extracts as c
    note = hub(vault, "Customers", "Pilot Deal", note_type="Opportunity",
               captures_body=f"\n{_NOTES}\n## Captured\n")
    saved({"text": "x", "company": "Pilot Deal"})
    assert c.run(vault)["facts_unresolved"] == 1 and captured(note) == []


def test_a_dry_run_writes_nothing(vault):
    import captures_from_extracts as c
    note = hub(vault, "Partners", "G42", captures_body=f"\n# G42\n\n{_NOTES}\n## Captured\n")
    before = note.read_text(encoding="utf-8")
    saved({"text": "Fact", "company": "G42"})
    assert c.run(vault, dry_run=True)["facts_filed"] == 1
    assert note.read_text(encoding="utf-8") == before
