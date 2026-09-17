"""history_log.py -- the one engine that writes a dated History entry.

Extracted from `summarize-and-tag-threads`'s own `apply_thread_extract.py`
(2026-09-14), where it had been private, so that every writer of a History
note shares one implementation of the entry format, the ordering and the
replace-rather-than-repeat rule. It joins `vault_manager.py` as a shared
engine: one copy, deployed onto the
install's `PYTHONPATH` by `deploy_shared_managers`, never bundled into a
Skill's own `scripts/` folder (`ADR-019` -- a local copy silently wins over
the shared one, which is how 228 stale `vault_manager.py` copies once ran
across 41 profiles).

The History note it writes is the SAME file the Entity Templates already
declare as their `history` child: `<root-stem>-history.md`, carrying
`type: "History"` and `tags: ["kind/history"]`. `name_template` in a
Template sets that note's `name` FRONTMATTER field, not its filename --
`vault_manager.modify_section` derives the filename as
`<root-stem>-<suffix>.md` -- so a note created by either route is the same
note, and the two mechanisms cannot produce two rival files.

Stdlib only, `vault_manager` aside -- it runs inside a Hermes worker with
no Second Brain backend available.
"""
from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path

import vault_manager as vm

_HISTORY_ENTRY = re.compile(r"^- (\d{4}-\d{2}-\d{2}): (.+)$")
_WHITESPACE = re.compile(r"\s+")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s")
# Long enough for a real one-line event, short enough that a History note
# stays scannable as a list rather than becoming prose.
_HISTORY_LINE_MAX = 160


def history_path_for(note_md: Path) -> Path:
    return note_md.parent / f"{note_md.stem}-history.md"


def condense(text: str, fallback: str = "") -> str:
    """One clean line: whitespace collapsed, trailing period dropped,
    truncated on a word boundary. `fallback`'s first sentence is used when
    `text` is empty -- an extraction saved before `history_line` existed
    has only its summary to offer."""
    line = _WHITESPACE.sub(" ", str(text or "")).strip()
    if not line:
        summary = _WHITESPACE.sub(" ", str(fallback or "")).strip()
        line = _SENTENCE_END.split(summary, 1)[0] if summary else ""
    line = line.rstrip(". ")
    if len(line) > _HISTORY_LINE_MAX:
        line = line[:_HISTORY_LINE_MAX].rsplit(" ", 1)[0].rstrip(",;: ") + "…"
    return line


def update_history(note_md: Path, date: str, line: str, link: str | None = None):
    """`(history note, frontmatter, new body)` for `vm.write_note`, or None
    when nothing would change.

    `link` is what makes an entry re-writable: an existing entry ending in
    that same `-- [[link]]` is REPLACED rather than joined by a second, so a
    source re-read after it grew gets its latest line at its latest date
    instead of the History reading like a changelog of one conversation.

    **`link=None` appends**, since a human logging "spoke to procurement"
    has no source note to key on -- with one exception: an entry identical
    in BOTH date and text to one already there is not written twice, and
    the caller is told so. A retried script call re-logging the same line
    is far likelier here than someone deliberately writing the same
    sentence twice in one day, and this vault's expensive bugs have all
    been duplicates rather than omissions.
    """
    history = history_path_for(note_md)
    if os.path.isfile(vm.long_path(history)):
        frontmatter, body = vm.read_note(history)
    else:
        frontmatter = {"type": "History", "name": f"{note_md.stem} History",
                       "parent": f"[[{note_md.stem}]]", "tags": ["kind/history"]}
        body = f"\n# {note_md.stem}\n"

    lines = body.splitlines()
    kept = [line_ for line_ in lines if not _HISTORY_ENTRY.match(line_)]
    entries = [m.groups() for line_ in lines if (m := _HISTORY_ENTRY.match(line_))]

    suffix = f" -- {link}" if link else ""
    updated = [(d, t) for d, t in entries if not (link and t.endswith(suffix))]
    updated.append((date, f"{line}{suffix}"))
    # Compared as SETS, not lists: `updated` has the rewritten entry appended
    # at the end while `entries` still holds it in date order, so a list
    # comparison would call an unchanged History changed and rewrite the file
    # on every pass.
    if set(updated) == set(entries):
        return None

    # Newest first, and a same-day entry keeps the order it was written in
    # (sort is stable) rather than being reshuffled against its siblings.
    updated.sort(key=lambda entry: entry[0], reverse=True)
    while kept and not kept[-1].strip():
        kept.pop()
    new_body = "\n".join(kept) + "\n\n" + "\n".join(f"- {d}: {t}" for d, t in updated) + "\n"
    return history, frontmatter, new_body


def append_entry(note_md: Path, line: str, *, date: str | None = None,
                 link: str | None = None, dry_run: bool = False) -> dict:
    """Writes one dated entry into `note_md`'s History and reports what
    happened. Defaults to today in UTC -- a caller that knows when the event
    actually happened (a Thread's own last message, say) must pass `date`
    rather than letting it default to when it was processed."""
    entry_date = (date or "").strip() or datetime.now(timezone.utc).date().isoformat()
    condensed = condense(line)
    if not condensed:
        return {"written": False, "reason": "empty history line"}

    update = update_history(note_md, entry_date, condensed, link)
    if update is None:
        return {"written": False, "reason": "identical entry already present",
                "history": str(history_path_for(note_md))}
    if not dry_run:
        vm.write_note(*update)
    return {"written": True, "history": str(update[0]), "date": entry_date, "line": condensed}
