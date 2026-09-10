"""Backfills the `## Conversation` section onto Threads captured before it existed,
and removes the mailbox owner's own participant links.

Why this exists rather than a re-capture: both changes are presentational, and
every fact they need is already in the vault. Re-capturing would re-spend one
classifier relay per Thread to reproduce data we already hold, and would
re-download every attachment -- for a section that can be rebuilt by reading the
message notes that are already sitting there.

Idempotent. The Conversation section is REBUILT from the message notes on every
run rather than appended to, so running it twice is the same as running it once,
and a Thread that already has a correct section is simply rewritten identically.

    python retrofit_conversation_index.py [--vault-path P] [--dry-run]

Prints a JSON summary. `--dry-run` reports what would change and writes nothing.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import vault_manager


def _self_email() -> str:
    return (os.environ.get("SECOND_BRAIN_SELF_EMAIL")
            or os.environ.get("SELF_EMAIL") or "").strip().lower()


def _conversation_line(frontmatter: dict, message_path: Path) -> str:
    direction = (frontmatter.get("direction") or "").strip()
    arrow = "->" if direction == "sent" else "<-"
    who = frontmatter.get("sender") or frontmatter.get("sender_email") or "unknown"
    when = (frontmatter.get("received") or "")[:16]
    subject = frontmatter.get("subject") or "(no subject)"
    return f"- `{when}` {arrow} **{who}** — [[{message_path.stem}|{subject}]]"


def _strip_self_links(links, self_email: str) -> list:
    """Drops the owner's own wikilink. Person notes are named by email address,
    so the link stem IS the address -- matched case-folded."""
    if not self_email:
        return list(links or [])
    return [link for link in (links or []) if self_email not in str(link).lower()]


def retrofit(vault_path: Path, *, dry_run: bool) -> dict:
    threads_root = vault_path / "Work" / "Threads"
    if not threads_root.is_dir():
        return {"status": "nothing to do", "reason": f"no {threads_root}"}

    template = vault_manager.load_template(vault_path, "thread")
    self_email = _self_email()
    conversations_written = 0
    self_links_removed = 0
    messages_cleaned = 0
    threads_seen = 0
    kind_tags_added = 0
    email_tags_added = 0
    file_tags_added = 0

    for thread_dir in sorted(p for p in threads_root.iterdir() if p.is_dir()):
        thread_note = thread_dir / f"{thread_dir.name}.md"
        if not thread_note.is_file():
            continue
        threads_seen += 1

        lines = []
        for message in sorted((thread_dir / "messages").glob("*.md")):
            frontmatter, _ = vault_manager.read_note(message)
            lines.append(((frontmatter.get("received") or ""),
                          _conversation_line(frontmatter, message)))
            # `kind/email` on the message note (2026-09-10) -- the thread
            # template's `messages` child carried no kind tag until then.
            if "kind/email" not in (frontmatter.get("tags") or []):
                email_tags_added += 1
                if not dry_run:
                    vault_manager.merge_tags(message, ["kind/email"])

            kept = _strip_self_links(frontmatter.get("participant_links"), self_email)
            if kept != list(frontmatter.get("participant_links") or []):
                messages_cleaned += 1
                if not dry_run:
                    vault_manager.update(vault_path, message,
                                         frontmatter={"participant_links": kept})

        # Ordered by the real received stamp, never by filename -- filenames are
        # subject-based and say nothing about when a message actually arrived.
        lines.sort(key=lambda pair: pair[0])
        content = "\n".join(line for _, line in lines)

        thread_frontmatter, _ = vault_manager.read_note(thread_note)
        conversation_id = thread_frontmatter.get("id") or ""

        # `kind/thread` (2026-09-10). Every other note type already carried its
        # own kind tag -- `kind/meeting`, `kind/notes`, `kind/file`,
        # `kind/person` -- and the thread template alone was missing one, so
        # "every Thread" was the one thing not answerable as a tag query.
        # Threads captured before the template default was added need it merged
        # in; `merge_tags` only adds what is absent, so this is idempotent.
        if "kind/thread" not in (thread_frontmatter.get("tags") or []):
            kind_tags_added += 1
            if not dry_run:
                vault_manager.merge_tags(thread_note, ["kind/thread"])
        if content and not dry_run:
            vault_manager.modify_section(
                vault_path, template, section="Conversation", content=content,
                mode="replace", note_id=conversation_id, note_name="Threads",
                caller="retrofit_conversation_index",
            )
        if content:
            conversations_written += 1

        # `kind/file` on each attachment's companion note. These are written
        # directly rather than through the `file` template, so the template's
        # own default never reached them -- they carried `type/<ext>` alone.
        for companion in (thread_dir / "files").glob("*/*.md"):
            companion_frontmatter, _ = vault_manager.read_note(companion)
            if "kind/file" not in (companion_frontmatter.get("tags") or []):
                file_tags_added += 1
                if not dry_run:
                    vault_manager.merge_tags(companion, ["kind/file"])

        related = vault_manager.get_section_content(thread_note, "Related") or ""
        kept_rows = [row for row in related.splitlines()
                     if row.strip() and (not self_email or self_email not in row.lower())]
        if len(kept_rows) != len([r for r in related.splitlines() if r.strip()]):
            self_links_removed += 1
            if not dry_run:
                vault_manager.modify_section(
                    vault_path, template, section="Related",
                    content="\n".join(kept_rows), mode="replace",
                    note_id=conversation_id, note_name="Threads",
                    caller="retrofit_conversation_index",
                )

    return {
        "status": "dry-run" if dry_run else "complete",
        "self_email": self_email or "<unset -- self-link removal skipped>",
        "threads_seen": threads_seen,
        "conversation_sections_written": conversations_written,
        "threads_with_self_link_removed": self_links_removed,
        "message_notes_cleaned": messages_cleaned,
        "kind_tags_added": kind_tags_added,
        "email_tags_added": email_tags_added,
        "file_tags_added": file_tags_added,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-path", default=os.environ.get("SECOND_BRAIN_VAULT_PATH", ""))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not args.vault_path:
        print("SECOND_BRAIN_VAULT_PATH is not set and --vault-path was not given")
        return 2
    print(json.dumps(retrofit(Path(args.vault_path), dry_run=args.dry_run), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
