"""CLI entry point: relabel a Thread's directory from its raw
conversation_id slug to a readable "<date> <subject>" one. No-op if
already renamed -- safe to call more than once.

Usage:
    python rename_thread.py --vault-path P --conversation-id ID

Prints {"renamed": bool, "new_path"/"reason": str} to stdout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import vault_lib


def rename_thread(vault_path: Path, conversation_id: str) -> dict:
    directory = vault_lib.resolve_thread_directory(vault_path, conversation_id)
    if directory is None:
        return {"renamed": False, "reason": "no Thread found for this conversation_id"}
    if directory.name != vault_lib._slugify(conversation_id):
        return {"renamed": False, "reason": "already renamed"}

    concept_path = directory / f"{directory.name}.md"
    frontmatter, _ = vault_lib.read_note(concept_path)

    messages_dir = directory / "messages"
    message_paths = sorted(messages_dir.glob("*.md")) if messages_dir.exists() else []
    if not message_paths:
        return {"renamed": False, "reason": "no messages yet"}

    latest_frontmatter, _ = vault_lib.read_note(message_paths[-1])
    date = (latest_frontmatter.get("received") or "")[:10]
    subject = vault_lib.clean_subject(frontmatter.get("thread_name", ""))
    new_stem = f"{date} {subject}".strip()
    new_directory = directory.parent / vault_lib._slugify(new_stem)

    # 2026-08-21 bug fix: two genuinely different real conversation_ids
    # can clean to the exact same "<date> <subject>" (Outlook sometimes
    # splits what looks like one human conversation into two
    # ConversationIDs -- found live). rename_thread_directory correctly
    # refuses to overwrite an existing directory; before this fix that
    # raised straight through, silently leaving the Thread stuck on its
    # raw conversation_id slug forever (never retried, since the
    # early-exit check above only fires once a rename has ALREADY
    # succeeded). A short hash-of-conversation_id suffix disambiguates,
    # mirroring raw_message_note_path's own identical-stem-collision
    # precedent.
    if new_directory.exists():
        # Reserve room for the suffix BEFORE slugifying, not after -- a
        # base new_stem already at/near _slugify's own 80-char max_len
        # (found live: exactly 80 chars) gets the appended suffix
        # silently truncated away by that SAME 80-char cutoff, leaving
        # the "disambiguated" name byte-for-byte identical to the one
        # that just collided.
        suffix = hashlib.sha256(conversation_id.encode("utf-8")).hexdigest()[:8]
        reserved = len(suffix) + 1  # "-" + suffix
        truncated_stem = new_stem[: max(1, 80 - reserved)]
        new_directory = directory.parent / vault_lib._slugify(f"{truncated_stem}-{suffix}")

    new_concept_path = vault_lib.rename_thread_directory(directory, new_directory)
    vault_lib.upsert_frontmatter_key(new_concept_path, "thread_name", subject)

    new_messages_dir = new_concept_path.parent / "messages"
    for message_path in sorted(new_messages_dir.glob("*.md")):
        vault_lib.upsert_frontmatter_key(message_path, "thread", f"[[{new_concept_path.stem}]]")

    new_files_dir = new_concept_path.parent / "files"
    if new_files_dir.exists():
        for companion_path in sorted(new_files_dir.glob("*/*.md")):
            # is_file() guard: a captured attachment whose own original
            # filename ends in ".md" (e.g. a real "project-scaffold.md"
            # attachment) produces a files/<slug>.md/ COMPANION DIRECTORY,
            # not a file -- this glob matches it too, and
            # upsert_frontmatter_key's read_text() on a directory raises
            # PermissionError on Windows. Found live 2026-08-21 (a real
            # "project-scaffold.md" attachment in the vault-rebuild pull).
            if not companion_path.is_file():
                continue
            vault_lib.upsert_frontmatter_key(companion_path, "source_thread", f"[[{new_concept_path.stem}]]")

    return {"renamed": True, "new_path": str(new_concept_path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--conversation-id", required=True)
    args = parser.parse_args()

    result = rename_thread(Path(args.vault_path), args.conversation_id)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
