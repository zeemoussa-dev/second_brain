"""Compass fixes the typing and nothing else (operator, 2026-10-24).

The prompt asks for spelling only. The prompt is not the guard -- a model that
decides a note reads better rewritten will rewrite it, and this vault is
machine-written and machine-read. These pin what happens when it does: the
answer is refused and the note is left alone. A refusal costs a typo; a bad
accept costs the note.
"""
from __future__ import annotations

import pytest

from app.business.core.vault import text_tidy
from app.data_access.compass_client import CompassClientError

_NOTE = """## Summary

The renewal lands in March, acording to [[Masdar]].
See https://example.test/terms for the detail.

- first point
- second point
"""


def _answering(monkeypatch, reply: str) -> None:
    monkeypatch.setattr(text_tidy, "request_chat_completion", lambda *a, **k: reply)


def test_a_spelling_fix_is_applied(monkeypatch) -> None:
    _answering(monkeypatch, _NOTE.replace("acording", "according"))

    result = text_tidy.tidy(_NOTE)

    assert result["changed"] is True
    assert "according to [[Masdar]]" in result["text"]


def test_nothing_to_fix_is_an_answer_not_a_failure(monkeypatch) -> None:
    """A UI that cannot tell "nothing to fix" from "it worked" claims success
    on a note it never touched."""
    _answering(monkeypatch, _NOTE)

    result = text_tidy.tidy(_NOTE)

    assert result["changed"] is False
    assert result["text"] == _NOTE


def test_a_renamed_wikilink_is_refused(monkeypatch) -> None:
    """The failure that matters most: a link is an identity, and "fixing" its
    capitalisation points it at a note that does not exist."""
    _answering(monkeypatch, _NOTE.replace("[[Masdar]]", "[[masdar]]"))

    with pytest.raises(text_tidy.TidyRefused, match="link"):
        text_tidy.tidy(_NOTE)


def test_a_reworded_heading_is_refused(monkeypatch) -> None:
    _answering(monkeypatch, _NOTE.replace("## Summary", "## Executive Summary"))

    with pytest.raises(text_tidy.TidyRefused, match="heading"):
        text_tidy.tidy(_NOTE)


def test_a_changed_url_is_refused(monkeypatch) -> None:
    _answering(monkeypatch, _NOTE.replace("example.test/terms", "example.test/Terms"))

    with pytest.raises(text_tidy.TidyRefused, match="address"):
        text_tidy.tidy(_NOTE)


def test_a_summary_instead_of_a_correction_is_refused(monkeypatch) -> None:
    """What a model does when it decides the note is the task rather than the
    material."""
    _answering(monkeypatch, "The note says the renewal is in March.")

    with pytest.raises(text_tidy.TidyRefused):
        text_tidy.tidy(_NOTE)


def test_reflowing_the_lines_is_refused(monkeypatch) -> None:
    """Blank lines and line breaks are structure in markdown, and the agents
    read them as structure."""
    _answering(monkeypatch, _NOTE.replace("\n\n", "\n"))

    with pytest.raises(text_tidy.TidyRefused, match="reflowed"):
        text_tidy.tidy(_NOTE)


def test_an_empty_answer_is_refused(monkeypatch) -> None:
    _answering(monkeypatch, "   ")

    with pytest.raises(text_tidy.TidyRefused, match="empty"):
        text_tidy.tidy(_NOTE)


def test_a_fenced_answer_is_unwrapped(monkeypatch) -> None:
    """Models hand documents back inside a fence. One wrapping the WHOLE
    answer is packaging and comes off."""
    _answering(monkeypatch, f"```markdown\n{_NOTE.replace('acording', 'according')}\n```")

    result = text_tidy.tidy(_NOTE)

    assert result["text"].startswith("## Summary")
    assert "```" not in result["text"]


def test_a_code_block_inside_the_note_survives(monkeypatch) -> None:
    """A fence in the middle is the note's own content, not packaging."""
    note = "## Query\n\n```\nSELECT 1\n```\n\nThat is the quary.\n"
    _answering(monkeypatch, note.replace("quary", "query"))

    result = text_tidy.tidy(note)

    assert "```\nSELECT 1\n```" in result["text"]


def test_compass_being_unreachable_is_a_refusal_not_a_crash(monkeypatch) -> None:
    def refuse(*args, **kwargs):
        raise CompassClientError("no route to host")

    monkeypatch.setattr(text_tidy, "request_chat_completion", refuse)

    with pytest.raises(text_tidy.TidyRefused, match="Compass could not be reached"):
        text_tidy.tidy(_NOTE)


def test_an_oversized_note_is_refused_before_the_call(monkeypatch) -> None:
    """Refused without spending the call, and told what to do instead."""
    def never(*args, **kwargs):
        raise AssertionError("Compass should not have been called")

    monkeypatch.setattr(text_tidy, "request_chat_completion", never)

    with pytest.raises(text_tidy.TidyRefused, match="section at a time"):
        text_tidy.tidy("x" * (text_tidy.MAX_TIDY_CHARACTERS + 1))


def test_an_empty_draft_needs_no_call(monkeypatch) -> None:
    def never(*args, **kwargs):
        raise AssertionError("Compass should not have been called")

    monkeypatch.setattr(text_tidy, "request_chat_completion", never)

    assert text_tidy.tidy("   \n ") == {"text": "   \n ", "changed": False}
