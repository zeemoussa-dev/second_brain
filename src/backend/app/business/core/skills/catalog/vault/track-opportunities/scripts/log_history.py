"""CLI entry point: writes ONE dated entry into an Opportunity's History.

Job 2's History step (2026-09-14). It replaced a
`vault_manager.py modify-section --child_suffix history` call so that an
Opportunity's History is written by the SAME engine that writes a company's
History (`history_log.py`, shared): one entry format, one ordering rule, one
definition of when an entry is a rewrite rather than a new event. Two
implementations of "a dated line in a History note" is precisely the drift
this vault has been bitten by before.

It writes the same file the `opportunity` Template already declares as its
`history` child -- `<Title>-history.md`, `type: "History"`,
`tags: ["kind/history"]` -- so a History note created by either route is the
same note. Nothing here invents a second place to log.

Usage:
    python log_history.py --note-path N --line "what happened"
                          [--date YYYY-MM-DD] [--link "[[Some Note]]"] [--dry-run]

N: the Opportunity's own root .md path -- whatever path the agent's own
`read_file` call used when it located the note (the `obsidian` Skill's job,
see SKILL.md). This script never searches for the note itself: resolving
"which Opportunity" is a judgment the agent has already made, and a script
that guessed could log onto the wrong deal.

--link makes the entry re-writable: an existing entry ending in that same
`-- [[link]]` is replaced rather than duplicated, so re-running after a
source note grew updates its line instead of stacking a second one. Omit it
for a plain operator log ("spoke to procurement") -- two such entries on one
day are two real events, and collapsing them would discard one.

Prints {"written": bool, "history": str, ...} or {"error": str}.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import history_log
import vault_manager as vm


def main() -> int:
    parser = argparse.ArgumentParser(description="Write one dated entry into an Opportunity's History.")
    parser.add_argument("--note-path", required=True)
    parser.add_argument("--line", required=True)
    parser.add_argument("--date", default="")
    parser.add_argument("--link", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    note_path = Path(args.note_path)
    # `long_path` first: past Windows' 260-char limit a plain `is_file()`
    # silently returns False, which would report a real Opportunity as
    # missing -- the exact trap that emptied three Indexes on 2026-09-06.
    import os
    if not os.path.isfile(vm.long_path(note_path)):
        print(json.dumps({"error": f"no note at {args.note_path!r}"}))
        return 2

    frontmatter, _ = vm.read_note(note_path)
    note_type = str(frontmatter.get("type") or "")
    if note_type != "Opportunity":
        # A History entry belongs on the Opportunity's ROOT note, not on its
        # own History or Captures child -- pointing this at a child would
        # create `<Title>-history-history.md`.
        print(json.dumps({
            "error": f"{note_path.stem!r} is a {note_type or 'typeless'} note, not an Opportunity"
        }))
        return 2

    result = history_log.append_entry(
        note_path, args.line,
        date=args.date or None, link=args.link or None, dry_run=args.dry_run,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
