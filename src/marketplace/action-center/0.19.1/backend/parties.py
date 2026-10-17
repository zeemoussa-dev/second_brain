"""How many people one owner field names, and which words in a name mean anything.

One rule, read by the screen that COUNTS the actions asked of several people and
by the writer that REFUSES to put one address on two of them. It was two copies
for an afternoon, and they drifted the same day: "A with B" was two parties on
one side and one on the other.

Nothing here decides who anybody IS -- that is the split and owner agents' work,
which reads the ask and the thread. This only takes the field apart.
"""
from __future__ import annotations

import re

# "Maiyas / Ahmed", "Will Badr; Ahmed Labib", "Core42 (Will, Mohammed)",
# "Fares Hassanieh with Mohammed Retmi". Word boundaries matter: without them
# "Alexander" contains "and".
SEPARATOR = re.compile(r"\s*(?:[,;/+&()]|\b(?:and|with)\b)\s*", re.I)

# Words that pair owners with nothing to do with each other: every team here
# shares "Core42", and half the desks share "office" or "team".
WEAK = {"core42", "g42", "team", "office", "group", "the", "and", "of", "ltd", "llc"}


# `Name (Company)` -- what the extraction writes when it knows where somebody
# works. The brackets qualify the name; they do not add a party, unless what is
# inside is a list of its own.
QUALIFIER = re.compile(r"\s*\(([^()]*)\)\s*")


def parties(owner) -> list[str]:
    """The parties named in one owner field, in order. One name gives one.

    `Rishav Agarwal (PwC)` is ONE person. Counting "PwC" as a second party is
    how one upload came to stand open four times, owned by "Finance",
    "MiddleEast", a PwC address and Rishav (operator, 2026-09-26). A bracket
    lists parties only when it contains a separator of its own:
    `Core42 (Will Badr, Mohammed Retmi)`."""
    text = str(owner or "").strip()

    def _keep_or_drop(match: re.Match) -> str:
        inside = match.group(1)
        return ", " + inside + ", " if SEPARATOR.search(inside) else " "

    text = QUALIFIER.sub(_keep_or_drop, text)
    return [p for p in (part.strip("()[] ") for part in SEPARATOR.split(text)) if p]


def naming_words(name) -> set[str]:
    """What a name is ABOUT, for asking whether two names could be one person.

    Punctuation is not part of a name: "Sherif Tawfik (Core42)" is about the
    same two words as "Sherif Tawfik", and keeping the brackets made it a
    different person -- or, on the Action Center, not a person at all."""
    plain = re.sub(r"[^\w\s]", " ", str(name or ""))
    return {w.lower() for w in plain.split()
            if len(w) > 2 and w.lower() not in WEAK}
