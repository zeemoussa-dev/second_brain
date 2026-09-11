"""Select Threads and Meetings that still need `topic/*` tags, and emit
each one's existing summary so a whole batch can be classified from a
single script call.

Reads the note's own `## Summary` -- written earlier by
`summarize-and-tag-threads` / `meeting-capture` -- rather than the raw
`messages/`. Two reasons, and the first is the operator's own design
rule: Threads are RAW evidence, retrieved on demand, deliberately
excluded from the vault index. A tagging pass has no business dragging
the raw layer back through an LLM. The second is cost: a summary is a
short paragraph where a thread is dozens of messages.

Read-only. Decides nothing about topics -- that judgment is the agent's,
and `apply_topic_tags.py` is what records it.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from note_frontmatter import (
    long_path,
    parse_tags,
    read_field,
    read_note,
    section_text,
    topics_of,
)

# `files/` and `messages/` hold per-attachment and per-message notes.
# Only the folder's own same-named hub note is a Thread/Meeting.
_SKIP_DIRS = {"messages", "files", "_archive"}


def _iter_hub_notes(root: Path):
    """Yields PLAIN paths, never the extended-length form.

    os.walk is given the `\\\\?\\` root so traversal survives paths past
    260 characters, which means every path it yields carries that prefix
    -- and handing those back to a caller breaks them a second way
    (`relative_to()` raises, and every path compares unequal to the plain
    one the caller holds). The vault manager hit exactly this on
    2026-09-06; each result is therefore rebuilt against the original
    root rather than having its prefix stripped by hand.
    """
    walk_root = long_path(root)
    if not Path(walk_root).is_dir():
        return
    for current, dirs, files in os.walk(walk_root):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS and not d.startswith("_")]
        folder_name = os.path.basename(current)
        relative = os.path.relpath(current, walk_root)
        for filename in files:
            if filename.endswith(".md") and filename[:-3] == folder_name:
                yield (root / relative / filename) if relative != "." else (root / filename)


def _needs_tagging(frontmatter_block: str) -> tuple[bool, str]:
    """(needs_tagging, why). A note is due either because it has never
    been tagged, or because new messages landed after the last pass --
    the same watermark rule `summarize-and-tag-threads` already uses, so
    both passes stay idempotent in the same way."""
    if not topics_of(parse_tags(frontmatter_block)):
        return True, "never-tagged"
    tagged_at = read_field(frontmatter_block, "topics_tagged_at")
    if not tagged_at:
        return True, "never-tagged"
    last_message_at = read_field(frontmatter_block, "last_message_at")
    if last_message_at and last_message_at > tagged_at:
        return True, "new-messages-since"
    return False, "current"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault-path", required=True)
    parser.add_argument(
        "--include", choices=["threads", "meetings", "both"], default="threads",
        help=(
            "Which corpus to select from. Defaults to threads: as at "
            "2026-09-08, 207 of 208 Meeting notes have an EMPTY '## Summary' "
            "and only '## Related' populated, so there is no text to "
            "classify them from. Meetings need a summarization pass of "
            "their own before topic tagging can mean anything for them."
        ),
    )
    parser.add_argument(
        "--limit", type=int, default=25,
        help="Maximum candidates to return in this batch.",
    )
    parser.add_argument(
        "--summary-chars", type=int, default=1200,
        help="Truncate each summary to this many characters.",
    )
    args = parser.parse_args()

    vault = Path(args.vault_path)
    candidates: list[dict] = []
    counts = {"scanned": 0, "current": 0, "no_summary": 0}

    folders = {
        "threads": [("Work/Threads", "Thread")],
        "meetings": [("Work/Meetings", "Meeting")],
        "both": [("Work/Threads", "Thread"), ("Work/Meetings", "Meeting")],
    }[args.include]

    for folder, note_type in folders:
        for note_path in _iter_hub_notes(vault / folder):
            counts["scanned"] += 1
            _, frontmatter_block, body = read_note(note_path)
            if not frontmatter_block:
                continue
            due, why = _needs_tagging(frontmatter_block)
            if not due:
                counts["current"] += 1
                continue
            summary = section_text(body, "Summary")
            if not summary:
                # Nothing to classify from. Reported and skipped, never
                # guessed at from the filename -- a topic invented from a
                # subject line is exactly the confidently-wrong tag the
                # closed list exists to prevent, and the taxonomy says so
                # itself: a wrong tag is worse than no tag because it
                # makes retrieval confidently incomplete.
                counts["no_summary"] += 1
                continue
            candidates.append({
                "path": str(note_path),
                "type": note_type,
                "reason": why,
                "existing_tags": parse_tags(frontmatter_block),
                "summary": summary[: args.summary_chars],
            })

    remaining = max(0, len(candidates) - args.limit)
    json.dump(
        {
            "counts": {**counts, "due": len(candidates), "remaining_after_batch": remaining},
            "candidates": candidates[: args.limit],
        },
        sys.stdout,
        indent=2,
    )
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
