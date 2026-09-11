"""Select Threads that still need `topic/*` tags, and emit each one's
existing summary so a whole batch can be classified from a single call.

Reads the note's own `## Summary` -- written earlier by
`summarize-and-tag-threads` -- rather than the raw `messages/`. Two
reasons, and the first is the operator's own design rule: Threads are
RAW evidence, retrieved on demand, deliberately excluded from the vault
index. A tagging pass has no business dragging the raw layer back
through an LLM. The second is cost: a summary is a short paragraph where
a thread is dozens of messages.

Read-only. Decides nothing about topics -- that judgment is the agent's,
and `apply_topic_tags.py` is what records it.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import vault_manager as vm

# `files/` and `messages/` hold per-attachment and per-message notes.
# Only a folder's own same-named hub note is the Thread itself.
_SKIP_DIRS = {"messages", "files", "_archive"}


def _iter_hub_notes(root: Path):
    """Yields PLAIN paths, never the extended-length form.

    os.walk is given the long-path root so traversal survives paths past
    260 characters -- the `files/` subtree genuinely exceeds it and an
    unprefixed walk dies there mid-scan. But every path os.walk then
    yields carries that prefix, and handing those back breaks callers a
    second way (`relative_to()` raises, and every path compares unequal
    to the plain one the caller holds -- `iter_md_files` hit exactly this
    on 2026-09-06). Each result is therefore rebuilt against the original
    root rather than having its prefix stripped by hand.
    """
    walk_root = vm.long_path(root)
    if not Path(walk_root).is_dir():
        return
    for current, dirs, files in os.walk(walk_root):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS and not d.startswith("_")]
        folder_name = os.path.basename(current)
        relative = os.path.relpath(current, walk_root)
        for filename in files:
            if filename.endswith(".md") and filename[:-3] == folder_name:
                yield (root / filename) if relative == "." else (root / relative / filename)


def _topics_of(frontmatter: dict) -> list[str]:
    return [str(t) for t in (frontmatter.get("tags") or []) if str(t).startswith("topic/")]


def _needs_tagging(frontmatter: dict) -> tuple[bool, str]:
    """(due, why). A note is due either because it has never been tagged,
    or because new messages landed after the last pass -- the same
    watermark rule `summarize-and-tag-threads` already uses, so both
    passes stay idempotent in the same way."""
    if not _topics_of(frontmatter):
        return True, "never-tagged"
    tagged_at = str(frontmatter.get("topics_tagged_at") or "")
    if not tagged_at:
        return True, "never-tagged"
    last_message_at = str(frontmatter.get("last_message_at") or "")
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
            "and only '## Related' populated, so there is no text to classify "
            "them from. Meetings need a summarization pass of their own "
            "before topic tagging can mean anything for them."
        ),
    )
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--summary-chars", type=int, default=1200)
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
            frontmatter, _ = vm.read_note(note_path)
            if not frontmatter:
                continue
            due, why = _needs_tagging(frontmatter)
            if not due:
                counts["current"] += 1
                continue
            summary = vm.get_section_content(note_path, "Summary").strip()
            if not summary:
                # Nothing to classify from. Reported and skipped, never
                # guessed at from the filename -- a topic invented from a
                # subject line is exactly the confidently-wrong tag the
                # closed list exists to prevent, and the taxonomy says so
                # itself: a wrong tag makes retrieval confidently
                # incomplete.
                counts["no_summary"] += 1
                continue
            candidates.append({
                "path": str(note_path),
                "type": note_type,
                "reason": why,
                "existing_tags": [str(t) for t in (frontmatter.get("tags") or [])],
                "summary": summary[: args.summary_chars],
            })

    json.dump(
        {
            "counts": {**counts, "due": len(candidates),
                       "remaining_after_batch": max(0, len(candidates) - args.limit)},
            "candidates": candidates[: args.limit],
        },
        sys.stdout, indent=2,
    )
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
