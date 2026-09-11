"""Enrichment's Customer Logs: a dated line in each named company's History.

The extraction applier wrote none -- not one company History in the vault had
a single entry. These pin the entry's shape and placement, one entry per
Thread, the fallback for extractions saved before `history_line` existed, and
the backfill from those saved extractions.
"""
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import vault_manager as vm

_THREAD_TEMPLATE = (Path(__file__).resolve().parents[6]
                    / "templates" / "masters" / "thread" / "Template.json")
_THREAD = "2026-09-10 Example"


def hub(vault: Path, root: str, name: str, *, aliases=(), note_type=None, parent=None,
        history_entries=()) -> Path:
    base = vault / "Work" / root
    folder = (base / parent / "Affiliates" / name) if parent else (base / name)
    folder.mkdir(parents=True)
    kind = note_type or ("Customer" if root == "Customers" else "Partner")
    alias_line = ("aliases: [" + ", ".join(f'"{a}"' for a in aliases) + "]\n") if aliases else ""
    (folder / f"{name}.md").write_text(f'---\ntype: "{kind}"\nname: "{name}"\n{alias_line}---\n',
                                       encoding="utf-8")
    entries = "".join(f"- {e}\n" for e in history_entries)
    (folder / f"{name}-history.md").write_text(
        f'---\ntype: "History"\nname: "{name} History"\nparent: "[[{name}]]"\n'
        f'tags: ["kind/history"]\n---\n\n# {name}\n\n{entries}', encoding="utf-8")
    return folder / f"{name}-history.md"


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    monkeypatch.setenv("SECOND_BRAIN_DATA_PATH", str(tmp_path / "config"))
    templates = tmp_path / "config" / "data" / "Templates" / "thread"
    templates.mkdir(parents=True)
    shutil.copy(_THREAD_TEMPLATE, templates / "Template.json")
    (tmp_path / "Work" / "People").mkdir(parents=True)
    thread_dir = tmp_path / "Work" / "Threads" / _THREAD
    (thread_dir / "messages").mkdir(parents=True)
    (thread_dir / f"{_THREAD}.md").write_text(
        '---\ntype: "Thread"\nid: "conv-1"\nlast_message_at: "2026-06-18 13:05:39.000000+00:00"\n'
        'tags: ["kind/thread"]\n---\n\n## Summary\n\n\n## Personal Notes\n\n\n## Actions\n\n\n'
        "## Conversation\n\n\n## Related\n\n\n## Files\n\n", encoding="utf-8")
    return tmp_path


def extraction(companies, *, summary="They agreed the pilot. Pricing follows.", history_line=None):
    data = {"schema_version": 1, "thread_path": f"Work/Threads/{_THREAD}/{_THREAD}.md",
            "summary": summary, "companies": companies,
            "people": [], "actions": [], "important_info": []}
    if history_line is not None:
        data["history_line"] = history_line
    return data


def entries(history: Path) -> list[str]:
    return [line for line in history.read_text(encoding="utf-8").splitlines() if line.startswith("- ")]


def test_each_named_company_gets_a_dated_entry_linking_the_thread(vault):
    import apply_thread_extract as a
    adcb = hub(vault, "Customers", "Abu Dhabi Commercial Bank", aliases=["ADCB"])
    hub(vault, "Partners", "G42")
    khazna = hub(vault, "Partners", "Khazna Data Centres", aliases=["Khazna"], parent="G42")

    result = a.apply_extract(vault, extraction(["ADCB", "Khazna", "Nowhere Holdings"],
                                               history_line="Facility term sheet signed."))

    line = f"- 2026-06-18: Facility term sheet signed -- [[{_THREAD}]]"
    assert entries(adcb) == [line], "by alias, dated by the Thread's last message"
    assert entries(khazna) == [line], "an Affiliate gets its own entry"
    assert sorted(result["history_entries"]) == ["Abu Dhabi Commercial Bank", "Khazna Data Centres"]


def test_entries_are_newest_first_and_the_header_is_kept(vault):
    import apply_thread_extract as a
    history = hub(vault, "Partners", "G42",
                  history_entries=["2026-07-01: Later -- [[T2]]", "2026-05-01: Earlier -- [[T1]]"])
    a.apply_extract(vault, extraction(["G42"], history_line="Middle"))
    assert [e[2:12] for e in entries(history)] == ["2026-07-01", "2026-06-18", "2026-05-01"]
    text = history.read_text(encoding="utf-8")
    assert text.startswith("---\ntype: \"History\"") and "# G42" in text


def test_one_entry_per_thread_replaced_when_the_thread_is_read_again(vault):
    import apply_thread_extract as a
    history = hub(vault, "Partners", "G42")
    a.apply_extract(vault, extraction(["G42"], history_line="First read"))
    a.apply_extract(vault, extraction(["G42"], history_line="Second read after it grew"))
    assert entries(history) == [f"- 2026-06-18: Second read after it grew -- [[{_THREAD}]]"]


def test_without_a_history_line_the_first_sentence_of_the_summary_is_used(vault):
    import apply_thread_extract as a
    history = hub(vault, "Partners", "G42")
    a.apply_extract(vault, extraction(["G42"]))
    assert entries(history) == [f"- 2026-06-18: They agreed the pilot -- [[{_THREAD}]]"]


def test_a_long_line_is_cut_at_a_word(vault):
    import apply_thread_extract as a
    history = hub(vault, "Partners", "G42")
    a.apply_extract(vault, extraction(["G42"], history_line="word " * 60))
    text = entries(history)[0].split(": ", 1)[1].split(" -- ")[0]
    assert len(text) <= 161 and text.endswith("…")


def test_an_opportunity_never_gets_a_history_entry(vault):
    import apply_thread_extract as a
    history = hub(vault, "Customers", "Pilot Deal", note_type="Opportunity")
    a.apply_extract(vault, extraction(["Pilot Deal"], history_line="x"))
    assert entries(history) == []


def test_the_backfill_writes_from_saved_extractions_idempotently(vault):
    import apply_thread_extract as a
    import history_from_extracts as h
    history = hub(vault, "Partners", "G42")
    a.persist(extraction(["G42"]), "conv-1")          # saved before History existed

    dry = h.run(vault, dry_run=True)
    assert dry["history_entries_written"] == 1 and entries(history) == []
    first, second = h.run(vault), h.run(vault)

    assert entries(history) == [f"- 2026-06-18: They agreed the pilot -- [[{_THREAD}]]"]
    assert first["history_entries_written"] == 1 and second["history_entries_written"] == 0
