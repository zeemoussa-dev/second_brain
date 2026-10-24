"""Why a note matched, in the note's own words (operator, 2026-10-24).

A result list of titles and ranks cannot be read: nothing on the row says what
the note has to do with the query, so every result is a click to find out. The
snippet is the window of text the match sits in.

Plain text, never HTML. The highlight belongs to whoever renders it -- sending
markup through the API would mean escaping the note's own content on the way
out and trusting it on the way in, for a visual effect the frontend can do
from the query it already has.

A snippet with no term in it is normal and not a bug: a semantic hit matches on
meaning, and a keyword hit can score on title or tags alone. Those get the
note's opening instead, which still says what the note is about.
"""
from __future__ import annotations

import re

_WORD = re.compile(r"[a-z0-9]+")

#: Enough to carry a sentence either side of the match without turning a result
#: row into a paragraph.
_DEFAULT_WIDTH = 240

#: How much of the window sits BEFORE the match, so the term lands a third of
#: the way in rather than at the very start where it reads as truncated.
_LEAD_FRACTION = 3

_CODE_FENCE = re.compile(r"```.*?```", re.DOTALL)
_EMBED = re.compile(r"!\[\[[^\]]*\]\]")
_WIKILINK = re.compile(r"\[\[([^\]|]*)(?:\|([^\]]*))?\]\]")
#: Heading and blockquote markers, which are only markers at the START of a
#: line. Stripping `#` and `>` everywhere turned the note's own
#: `<script>alert(1)</script>` into `<script alert(1)</script` -- mangling
#: content to tidy syntax, which is the opposite of the job.
_LINE_MARKERS = re.compile(r"^[ \t]*[>#]+[ \t]*", re.MULTILINE)
#: Emphasis and code marks. `_` is deliberately absent: it is a normal
#: character inside the identifiers and file names these notes are full of.
_EMPHASIS = re.compile(r"[*`~]+")
_WHITESPACE = re.compile(r"\s+")


def plain_text(body: str) -> str:
    """Markdown flattened to the prose underneath it.

    Embeds go entirely (an image's filename says nothing about the note);
    wikilinks keep their display text, which is usually the name of the thing
    the sentence is about and so is exactly what a reader wants to see.
    """
    text = _CODE_FENCE.sub(" ", body or "")
    text = _EMBED.sub(" ", text)
    text = _WIKILINK.sub(lambda match: match.group(2) or match.group(1) or " ", text)
    text = _LINE_MARKERS.sub(" ", text)
    text = _EMPHASIS.sub(" ", text)
    return _WHITESPACE.sub(" ", text).strip()


def make_snippet(body: str, query: str, width: int = _DEFAULT_WIDTH) -> str:
    """The window of `body` around the first query term, or its opening."""
    text = plain_text(body)
    if not text:
        return ""

    lowered = text.lower()
    positions = [found for term in _WORD.findall(query.lower()) if (found := lowered.find(term)) >= 0]
    if not positions:
        return _clip(text, 0, width)
    return _clip(text, max(0, min(positions) - width // _LEAD_FRACTION), width)


def _clip(text: str, start: int, width: int) -> str:
    """`width` characters from `start`, cut at word boundaries and marked with
    ellipses on whichever side was actually cut."""
    if start > 0:
        space = text.find(" ", start)
        start = (space + 1) if 0 <= space < start + 20 else start
    end = start + width
    if end < len(text):
        space = text.rfind(" ", start, end)
        end = space if space > start else end
    return ("…" if start > 0 else "") + text[start:end].strip() + ("…" if end < len(text) else "")
