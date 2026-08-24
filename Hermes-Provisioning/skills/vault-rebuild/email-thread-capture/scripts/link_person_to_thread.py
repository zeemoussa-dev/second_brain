"""CLI entry point: ensure a bare Person note exists for a message's
sender, then add a wikilink to it into the Thread's own "## Related"
section (accumulates across multiple senders, never overwrites).

Usage:
    python link_person_to_thread.py --vault-path P --conversation-id ID \\
        --sender-name NAME --sender-email EMAIL

Prints {"linked": bool, ...} to stdout. Idempotent -- calling twice for
the same sender on the same Thread adds the wikilink only once.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import vault_lib

_CALLER = "link_person_to_thread.link_person_to_thread"


def link_person_to_thread(vault_path: Path, conversation_id: str, sender_name: str, sender_email: str) -> dict:
    person_result = vault_lib.ensure_bare_person_note(vault_path, sender_name, sender_email)
    if person_result is None:
        return {"linked": False, "reason": "no sender_email"}

    person_note_path = person_result["note_path"]
    person_stem = Path(person_note_path).stem
    wikilink = f"[[{person_stem}]]"

    directory = vault_lib.resolve_thread_directory(vault_path, conversation_id)
    if directory is None:
        return {"linked": False, "reason": "no Thread found for this conversation_id"}
    concept_path = directory / f"{directory.name}.md"

    vault_lib.insert_body_section_if_missing(concept_path, "## Related")
    existing = vault_lib.read_body_section(concept_path, "## Related")
    if wikilink in existing:
        return {"linked": False, "reason": "already linked", "person_note_path": person_note_path}

    lines = [line for line in existing.splitlines() if line.strip()]
    lines.append(f"- {wikilink}")
    vault_lib.replace_body_section(concept_path, "## Related", "\n".join(lines), caller=_CALLER)
    return {"linked": True, "person_note_path": person_note_path}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--conversation-id", required=True)
    parser.add_argument("--sender-name", required=True)
    parser.add_argument("--sender-email", required=True)
    args = parser.parse_args()

    result = link_person_to_thread(Path(args.vault_path), args.conversation_id, args.sender_name, args.sender_email)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
