"""A search result says why it matched (operator, 2026-10-24).

A list of titles and ranks cannot be read: nothing on the row connects the note
to the query, so every result is a click to find out. These pin the window of
text that goes on the row, and the cases where there is no term to point at --
which are normal, not failures.
"""
from __future__ import annotations

from app.business.core.vault import snippets

_NOTE = (
    "The renewal was discussed on Tuesday. Procurement want the support tier "
    "unbundled before they will sign anything, and the current discount lapses "
    "at the end of the quarter. Nobody has priced the alternative yet."
)


def test_the_snippet_is_the_window_the_match_sits_in() -> None:
    snippet = snippets.make_snippet(_NOTE, "unbundled")

    assert "unbundled" in snippet
    # Context on BOTH sides -- a snippet starting at the term reads as
    # truncated and says nothing about what came before it.
    assert "support tier" in snippet


def test_a_match_with_no_term_in_the_body_falls_back_to_the_opening() -> None:
    """Normal, not a failure: a semantic hit matches on meaning, and a keyword
    hit can score on title or tags alone. The opening still says what the note
    is about, which is the job."""
    snippet = snippets.make_snippet(_NOTE, "procurement strategy for aviation")

    assert snippet.startswith("The renewal was discussed")


def test_a_long_note_is_clipped_at_word_boundaries_and_marked() -> None:
    body = "alpha " * 200 + "needle " + "omega " * 200

    snippet = snippets.make_snippet(body, "needle")

    assert "needle" in snippet
    assert snippet.startswith("…") and snippet.endswith("…")
    assert len(snippet) < 300
    assert " alph…" not in snippet, "a word should not be cut in half"


def test_an_empty_note_has_nothing_to_quote() -> None:
    assert snippets.make_snippet("", "anything") == ""
    assert snippets.make_snippet("   \n\n  ", "anything") == ""


def test_markdown_is_flattened_to_the_prose_underneath() -> None:
    """The row shows text, not source. A snippet full of ``##`` and ``[[`` is
    harder to read than the sentence it is quoting."""
    body = "## Heading\n\nSee [[Masdar Renewal|the renewal note]] and **this**.\n"

    snippet = snippets.make_snippet(body, "renewal")

    assert "##" not in snippet
    assert "[[" not in snippet
    assert "**" not in snippet
    # The display text survives: it is usually the name of the thing the
    # sentence is about.
    assert "the renewal note" in snippet


def test_an_image_embed_contributes_nothing() -> None:
    """A filename is not prose, and a snippet made of one says nothing."""
    body = "![[diagram-final-v3.png]] The contract renews in March."

    snippet = snippets.make_snippet(body, "contract")

    assert "diagram-final-v3" not in snippet
    assert "The contract renews in March." in snippet


def test_a_code_fence_is_not_quoted_as_prose() -> None:
    body = "```\nSELECT * FROM renewals;\n```\nThe renewal is signed."

    snippet = snippets.make_snippet(body, "renewal")

    assert "SELECT" not in snippet
    assert "The renewal is signed." in snippet


def test_the_snippet_is_plain_text_never_markup() -> None:
    """The highlight belongs to whoever renders it. Markup from here would
    mean escaping the note's own content on the way out and trusting it on the
    way in, for an effect the frontend can do from the query it already has."""
    body = "A <script>alert(1)</script> renewal & terms."

    snippet = snippets.make_snippet(body, "renewal")

    assert "<mark>" not in snippet and "<b>" not in snippet
    # The note's own characters are passed through untouched, not escaped:
    # escaping here would double-escape in the browser.
    assert "<script>" in snippet
