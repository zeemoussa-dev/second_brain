"""The closed `topic/*` vocabulary, read from the operator's own
`Settings/Tag Taxonomy.md` rather than hard-coded here.

The taxonomy file is the single authority (its own words: "Extend the
list here first; never in the prompt"), so this module never carries a
fallback copy of the list -- a missing or unreadable taxonomy is a hard
error, not a cue to invent a default. A silent default would let the
classifier write tags the operator never declared, which is precisely
the failure the closed list exists to prevent.

Shared by both scripts so the selector and the applier can never drift
onto two different vocabularies.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

# Only the section under this heading is the vocabulary. The namespace
# table earlier in the file also mentions `topic/<subject>`, and the
# repair table below it names tags that are explicitly NOT topics --
# scanning the whole file would swallow both.
_CLOSED_LIST_HEADING = "## `topic/*` -- the closed list"

_TOPIC_TAG = re.compile(r"`(topic/[a-z0-9][a-z0-9-]*)`")


def taxonomy_path() -> Path:
    """`Settings/Tag Taxonomy.md` under the configured data root.

    SECOND_BRAIN_DATA_PATH is exported by the backend's own config on
    load and is present in a Hermes worker's environment; there is no
    sensible guess if it is unset, so this raises rather than falling
    back to a path that would silently be wrong on another machine.
    """
    data_root = os.environ.get("SECOND_BRAIN_DATA_PATH")
    if not data_root:
        raise RuntimeError(
            "SECOND_BRAIN_DATA_PATH is not set -- cannot locate "
            "Settings/Tag Taxonomy.md, and this script must never guess "
            "a vocabulary."
        )
    return Path(data_root) / "Settings" / "Tag Taxonomy.md"


def load_closed_topics(path: Path | None = None) -> list[str]:
    """Every declared `topic/*` value, in the order the file declares
    them. Raises if the file or its closed-list section is missing."""
    path = path or taxonomy_path()
    if not path.is_file():
        raise FileNotFoundError(f"Tag taxonomy not found at {path}")

    text = path.read_text(encoding="utf-8")
    # The heading is written with an em dash in the real file; match on
    # the stable prefix so a punctuation change does not break loading.
    marker = text.find("## `topic/*`")
    if marker == -1:
        raise ValueError(
            f"{path} declares no '## `topic/*`' closed-list section -- "
            "refusing to fall back to an invented vocabulary."
        )
    # Stop at the next top-level heading so the repair table below is
    # never read as vocabulary.
    end = text.find("\n## ", marker + 1)
    section = text[marker : end if end != -1 else len(text)]

    seen: dict[str, None] = {}
    for tag in _TOPIC_TAG.findall(section):
        seen.setdefault(tag, None)
    if not seen:
        raise ValueError(f"{path} declares no topic values in its closed list")
    return list(seen)
