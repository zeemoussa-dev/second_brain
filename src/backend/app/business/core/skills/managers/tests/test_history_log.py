"""The shared History engine (`history_log.py`).

Extracted from `apply_thread_extract.py` on 2026-09-14 so Opportunities and
companies write History the same way. `summarize-and-tag-threads`'s own
`tests/test_history_logs.py` still pins the Thread-side behaviour through
its wrapper; these pin the engine itself, including the case that side has
no use for -- an entry with NO source link, which a human logging into an
Opportunity from WhatsApp always is.
"""
from pathlib import Path

import pytest

import history_log
import vault_manager as vm


@pytest.fixture()
def opportunity(tmp_path: Path) -> Path:
    folder = tmp_path / "Work" / "Customers" / "Adnoc" / "Opportunities" / "Alarm Management"
    folder.mkdir(parents=True)
    note = folder / "Alarm Management.md"
    note.write_text(
        '---\ntype: "Opportunity"\ntitle: "Alarm Management"\n---\n\n## Summary\n\nPlaceholder.\n',
        encoding="utf-8",
    )
    return note


def _entries(history: Path) -> list[str]:
    return [line for line in history.read_text(encoding="utf-8").splitlines() if line.startswith("- ")]


def test_creates_the_history_child_with_template_frontmatter(opportunity):
    result = history_log.append_entry(opportunity, "Spoke to procurement", date="2026-09-14")

    history = opportunity.parent / "Alarm Management-history.md"
    assert result["written"] is True
    assert Path(result["history"]) == history
    frontmatter, body = vm.read_note(history)
    # The same shape the `opportunity` Template declares for its history
    # child -- either route must produce the same note, not two rivals.
    assert frontmatter["type"] == "History"
    assert frontmatter["name"] == "Alarm Management History"
    assert frontmatter["parent"] == "[[Alarm Management]]"
    assert frontmatter["tags"] == ["kind/history"]
    assert "- 2026-09-14: Spoke to procurement" in body


def test_unlinked_entries_append_but_an_identical_one_does_not_repeat(opportunity):
    history_log.append_entry(opportunity, "Spoke to procurement", date="2026-09-14")
    second = history_log.append_entry(opportunity, "Spoke to procurement", date="2026-09-14")
    history_log.append_entry(opportunity, "Sent the proposal", date="2026-09-14")

    history = opportunity.parent / "Alarm Management-history.md"
    # A retried script call re-logging the same line must not double it, and
    # the caller is told rather than left to assume it landed. A genuinely
    # different line on the same day is a second entry.
    assert second["written"] is False
    assert second["reason"] == "identical entry already present"
    assert len(_entries(history)) == 2


def test_a_linked_entry_is_rewritten_not_repeated(opportunity):
    history_log.append_entry(opportunity, "Kickoff call", date="2026-09-01", link="[[Thread A]]")
    history_log.append_entry(opportunity, "Kickoff call, scope agreed", date="2026-09-14",
                             link="[[Thread A]]")

    entries = _entries(opportunity.parent / "Alarm Management-history.md")
    assert entries == ["- 2026-09-14: Kickoff call, scope agreed -- [[Thread A]]"]


def test_an_unchanged_linked_entry_rewrites_nothing(opportunity):
    history_log.append_entry(opportunity, "Kickoff call", date="2026-09-01", link="[[Thread A]]")
    history_log.append_entry(opportunity, "Later call", date="2026-09-02", link="[[Thread B]]")
    history_log.append_entry(opportunity, "Newest", date="2026-09-03", link="[[Thread C]]")

    # Re-writing the MIDDLE entry identically: `updated` holds it last while
    # the file holds it in date order, so comparing as lists would call an
    # unchanged History changed and rewrite the file on every pass.
    assert history_log.append_entry(opportunity, "Later call", date="2026-09-02",
                                    link="[[Thread B]]")["written"] is False


def test_entries_are_newest_first(opportunity):
    history_log.append_entry(opportunity, "Oldest", date="2026-09-01", link="[[A]]")
    history_log.append_entry(opportunity, "Newest", date="2026-09-14", link="[[B]]")
    history_log.append_entry(opportunity, "Middle", date="2026-09-07", link="[[C]]")

    entries = _entries(opportunity.parent / "Alarm Management-history.md")
    assert [entry[2:12] for entry in entries] == ["2026-09-14", "2026-09-07", "2026-09-01"]


def test_an_existing_history_keeps_its_header_and_entries(opportunity):
    history = opportunity.parent / "Alarm Management-history.md"
    history.write_text(
        '---\ntype: "History"\nname: "Alarm Management History"\n---\n\n'
        "# Alarm Management\n\n- 2026-08-30: Created\n", encoding="utf-8",
    )

    history_log.append_entry(opportunity, "Consumption confirmed", date="2026-09-14")

    body = history.read_text(encoding="utf-8")
    assert "# Alarm Management" in body
    assert "- 2026-08-30: Created" in body
    assert len(_entries(history)) == 2


def test_a_blank_line_writes_nothing(opportunity):
    result = history_log.append_entry(opportunity, "   ")

    assert result["written"] is False
    assert not (opportunity.parent / "Alarm Management-history.md").exists()


def test_condense_truncates_on_a_word_boundary():
    condensed = history_log.condense("word " * 60)

    assert len(condensed) <= 161  # 160 plus the ellipsis
    assert condensed.endswith("…")
    assert "  " not in condensed


def test_condense_falls_back_to_the_first_sentence():
    assert history_log.condense("", fallback="First one. Second one.") == "First one"


def test_dry_run_writes_nothing(opportunity):
    result = history_log.append_entry(opportunity, "Spoke to procurement", dry_run=True)

    assert result["written"] is True
    assert not (opportunity.parent / "Alarm Management-history.md").exists()
