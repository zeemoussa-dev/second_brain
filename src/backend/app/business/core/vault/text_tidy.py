"""Fixing the typing, and nothing else (operator, 2026-10-24: "Can we Use
Compass to Clean the Text after you edit it Instead of Having Lots of Spelling
Mistakes").

A model asked to improve text will improve it: it rewrites a blunt sentence
into a polite one, turns a note into prose, renames `[[Masdar]]` to
`[[masdar]]` because that reads better, and reflows a list that an agent
parses. This vault is machine-written and machine-read, so the prompt asks for
spelling only -- and the prompt is not the guard. The guard is below: the
result is COMPARED to the original and refused outright if anything
structural moved, because a refusal costs a typo and a bad accept costs the
note.
"""
from __future__ import annotations

import re

from app.data_access.compass_client import CompassClientError, request_chat_completion

_WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")
_HEADING = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)
_URL = re.compile(r"https?://\S+")

#: Long enough for a real note, short enough that nobody waits on it. A note
#: past this is left alone rather than half-corrected.
MAX_TIDY_CHARACTERS = 12_000

_INSTRUCTION = """You correct typing mistakes in a note. You are not an editor.

Fix ONLY:
- misspelled words
- obviously wrong capitalisation of ordinary words
- doubled words, and missing or doubled spaces
- missing sentence-ending punctuation

Change NOTHING else. Specifically, keep every one of these exactly as it is,
character for character:
- text inside [[double brackets]] -- these are links and renaming one breaks it
- headings, including their wording and their # markers
- lists, their order, their markers and their indentation
- URLs, file names, code, and anything inside backticks
- tags, dates, numbers, names of people, companies and products
- line breaks and blank lines

Never add a sentence. Never remove one. Never rephrase one. Never translate.
Never explain what you changed.

Reply with the corrected note and nothing else."""


class TidyRefused(Exception):
    """The model's answer was not a corrected copy of the note."""


def tidy(text: str) -> dict:
    """The note with its typos fixed, or a refusal.

    `changed` is false when there was nothing to fix, which is a real and
    common answer -- a UI that cannot tell "nothing to fix" from "it worked"
    reports success on a note it never touched.
    """
    original = text or ""
    if not original.strip():
        return {"text": original, "changed": False}
    if len(original) > MAX_TIDY_CHARACTERS:
        raise TidyRefused(
            f"This note is {len(original):,} characters and the limit is "
            f"{MAX_TIDY_CHARACTERS:,}. Tidy a section at a time."
        )

    try:
        answer = request_chat_completion(
            [
                {"role": "system", "content": _INSTRUCTION},
                {"role": "user", "content": original},
            ],
            timeout=60.0,
        )
    except CompassClientError as exc:
        raise TidyRefused(f"Compass could not be reached: {exc}") from exc

    cleaned = _with_the_edges_of(original, _unwrap(answer))
    _refuse_if_structure_moved(original, cleaned)
    return {"text": cleaned, "changed": cleaned != original}


def _unwrap(answer: str) -> str:
    """Models like to hand a document back inside a fence. One wrapping fence
    around the WHOLE answer is the model's packaging and comes off; a fence in
    the middle is the note's own code block and stays."""
    text = (answer or "").strip("\n")
    lines = text.splitlines()
    if len(lines) >= 2 and lines[0].startswith("```") and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1])
    return text


def _with_the_edges_of(original: str, cleaned: str) -> str:
    """The note's own leading and trailing blank lines, put back.

    A model answers with the text and no particular opinion about the newline
    at the end, and unwrapping a fence takes one off regardless. That is not a
    reflow, but the line-count check below cannot tell the difference -- so the
    edges are restored before anything is compared, and a note that ended with
    a newline still ends with one on disk.
    """
    body = cleaned.strip("\n")
    leading = len(original) - len(original.lstrip("\n"))
    trailing = len(original) - len(original.rstrip("\n"))
    return "\n" * leading + body + "\n" * trailing


def _refuse_if_structure_moved(original: str, cleaned: str) -> None:
    """Everything a typo fix must not touch, checked rather than trusted."""
    if not cleaned.strip():
        raise TidyRefused("Compass returned an empty note, so nothing was changed.")

    for name, found in (
        ("link", _WIKILINK),
        ("heading", _HEADING),
        ("address", _URL),
    ):
        before = found.findall(original)
        after = found.findall(cleaned)
        if before != after:
            raise TidyRefused(
                f"Compass changed a {name} in the note, which a spelling fix must not do. "
                "Nothing was changed."
            )

    # Length is the blunt check that catches a rewrite the others miss: a model
    # that summarised, translated or answered the note instead of correcting it
    # lands far from where it started.
    if abs(len(cleaned) - len(original)) > max(80, len(original) * 0.15):
        raise TidyRefused(
            "Compass returned something too different from the note to be a spelling fix. "
            "Nothing was changed."
        )

    if cleaned.count("\n") != original.count("\n"):
        raise TidyRefused(
            "Compass reflowed the note's lines, which a spelling fix must not do. "
            "Nothing was changed."
        )
