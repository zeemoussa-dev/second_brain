"""CLI entry point: relabel a Thread's directory from its raw
conversation_id slug to a readable "<date> <subject>" one. No-op if
already renamed -- safe to call more than once.

Usage:
    python rename_thread.py --vault-path P --conversation-id ID

Prints {"renamed": bool, "new_path"/"reason": str} to stdout.

2026-09-02 (REQ-SB-87-US-02-T02): Thread resolution now goes through
`vault_manager.find_by_id` (the Thread's own real, stable `id` -- its
`conversation_id`, per `REQ-SB-87-US-02-T01` -- not a directory-name
scan), and the concept note's own `thread_name`, every RawMessage's own
`thread` backlink, and every file companion's own `source_thread` field
now go through `vault_manager.update` instead of
`vault_lib.upsert_frontmatter_key`. The physical directory rename and the
`sha256(conversation_id)[:8]` collision-suffix disambiguation stay
HAND-WRITTEN, unchanged, still via `vault_lib.rename_thread_directory`/
`vault_lib._slugify` -- `vault_manager.py` has no primitive for
physically renaming a note's own directory/file stem (see this task's own
Implementation Log for the full disclosed judgement call).

**Scope-internal judgement call (logged for human spot-check):** the
"already renamed" no-op check now compares `directory.name` against
`vault_manager._slugify(conversation_id)`, not `vault_lib._slugify(...)`
-- because the Thread's own directory is now actually named by
`vault_manager.create()`'s own slug convention (`REQ-SB-87-US-02-T01`),
not `vault_lib`'s. Using the wrong slugify here would misdetect the
not-yet-renamed state for a conversation_id long enough that the two
functions' differing max-length caps (120 vs. 80) disagree. This is a
correctness fix for the migrated resolution path, not a change to the
preserved physical-rename/collision logic below (which still uses
`vault_lib._slugify`, matching its own explicitly-preserved 80-char
collision-suffix budget).
"""
from __future__ import annotations

import argparse
import os
import hashlib
import json
from pathlib import Path

import vault_lib
import vault_manager


def rename_thread(vault_path: Path, conversation_id: str) -> dict:
    concept_path = vault_manager.find_by_id(vault_path, conversation_id, note_name="Threads")
    if concept_path is None:
        return {"renamed": False, "reason": "no Thread found for this conversation_id"}
    directory = concept_path.parent
    if directory.name != vault_manager._slugify(conversation_id):
        return {"renamed": False, "reason": "already renamed"}

    frontmatter, _ = vault_manager.read_note(concept_path)

    messages_dir = directory / "messages"
    message_paths = sorted(messages_dir.glob("*.md")) if messages_dir.exists() else []
    if not message_paths:
        return {"renamed": False, "reason": "no messages yet"}

    latest_frontmatter, _ = vault_manager.read_note(message_paths[-1])
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
    vault_manager.update(vault_path, new_concept_path, frontmatter={"thread_name": subject})

    new_messages_dir = new_concept_path.parent / "messages"
    for message_path in sorted(new_messages_dir.glob("*.md")):
        vault_manager.update(vault_path, message_path, frontmatter={"thread": f"[[{new_concept_path.stem}]]"})

    new_files_dir = new_concept_path.parent / "files"
    if new_files_dir.exists():
        for companion_path in sorted(new_files_dir.glob("*/*.md")):
            # is_file() guard: a captured attachment whose own original
            # filename ends in ".md" (e.g. a real "project-scaffold.md"
            # attachment) produces a files/<slug>.md/ COMPANION DIRECTORY,
            # not a file -- this glob matches it too, and
            # vault_manager.update's own read_note()'s read_text() on a
            # directory raises PermissionError on Windows. Found live
            # 2026-08-21 (a real "project-scaffold.md" attachment in the
            # vault-rebuild pull).
            if not companion_path.is_file():
                continue
            # 2026-09-02 (REQ-SB-87-US-02-T02, found live): the SAME
            # ".md"-named-attachment case above also makes this glob match
            # the raw attachment BYTES copy sitting alongside the real
            # companion note (both end in ".md" at this level) -- the raw
            # attachment file itself never has a frontmatter fence.
            # `vault_lib.upsert_frontmatter_key` safely no-ops on a
            # fence-less file (its own `insert_frontmatter_key_if_missing`
            # finds no "\n---\n" and returns without writing);
            # `vault_manager.update` has no such guard -- it always writes
            # a frontmatter block, which would silently PREPEND a
            # synthetic fence onto a real, unrelated attachment's raw
            # content. Confirmed live: without this guard, a real
            # "# Project Scaffold..." attachment body got a
            # "---\nsource_thread: ...\n---\n" block injected ahead of its
            # real content. Skipping any match with no real frontmatter
            # fence reproduces upsert_frontmatter_key's own no-op safety
            # exactly, matching this task's own "matching today's real
            # upsert_frontmatter_key calls exactly" Constraint.
            if not companion_path.read_text(encoding="utf-8").startswith("---\n"):
                continue
            vault_manager.update(vault_path, companion_path, frontmatter={"source_thread": f"[[{new_concept_path.stem}]]"})

    return {"renamed": True, "new_path": str(new_concept_path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--vault-path",
        # Defaults to what Second Brain's setup wizard writes into Hermes'
        # own .env, so a Skill never has to name a machine-specific
        # absolute path and a bundle never has to have one rewritten on
        # import. Pass it only to override.
        default=os.environ.get("SECOND_BRAIN_VAULT_PATH", ""),
    )
    parser.add_argument("--conversation-id", required=True)
    args = parser.parse_args()
    if not (args.vault_path or "").strip():
        # An empty value would become Path("") -> the CWD, which is exactly the
        # silent-wrong-folder failure this whole change exists to remove.
        raise SystemExit(
            "No vault path. Set SECOND_BRAIN_VAULT_PATH in Hermes' own .env "
            "(Second Brain's setup wizard writes it) or pass --vault-path."
        )

    result = rename_thread(Path(args.vault_path), args.conversation_id)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
