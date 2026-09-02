"""CLI entry point: ensure a bare Person note exists for a message's
sender, then add a wikilink to it into the Thread's own "## Related"
section (accumulates across multiple senders, never overwrites).

Usage:
    python link_person_to_thread.py --vault-path P --conversation-id ID \\
        --sender-name NAME --sender-email EMAIL

Prints {"linked": bool, ...} to stdout. Idempotent -- calling twice for
the same sender on the same Thread adds the wikilink only once.

2026-09-02 (REQ-SB-87-US-02-T03): Thread resolution now goes through
`vault_manager.find_by_id` (matching `ingest_email.py`/`rename_thread.py`'s
own established pattern) instead of `vault_lib.resolve_thread_directory`,
and the "## Related" accumulation now goes through
`vault_manager.get_section_content`/`vault_manager.modify_section(...,
caller="link_person_to_thread")` instead of `vault_lib`'s own
`insert_body_section_if_missing`/`read_body_section`/`replace_body_section`
-- the Thread template's own `## Related` `allowed_callers` declaration
(`REQ-SB-87-US-01-T05`) now enforces this section's per-caller restriction,
replacing `vault_lib.py`'s own hardcoded `_CALLER_ALLOW_LISTS`.
`ensure_bare_person_note` stays entirely hand-written, unchanged.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import vault_lib
import vault_manager

_CALLER = "link_person_to_thread"


def link_person_to_thread(vault_path: Path, conversation_id: str, sender_name: str, sender_email: str) -> dict:
    person_result = vault_lib.ensure_bare_person_note(vault_path, sender_name, sender_email)
    if person_result is None:
        return {"linked": False, "reason": "no sender_email"}

    person_note_path = person_result["note_path"]
    person_stem = Path(person_note_path).stem
    wikilink = f"[[{person_stem}]]"

    thread_template = vault_manager.load_template(vault_path, "thread")
    concept_path = vault_manager.find_by_id(vault_path, conversation_id, note_name="Threads")
    if concept_path is None:
        return {"linked": False, "reason": "no Thread found for this conversation_id"}

    existing = vault_manager.get_section_content(concept_path, "Related")
    if wikilink in existing:
        return {"linked": False, "reason": "already linked", "person_note_path": person_note_path}

    lines = [line for line in existing.splitlines() if line.strip()]
    lines.append(f"- {wikilink}")
    vault_manager.modify_section(
        vault_path, thread_template, section="Related", content="\n".join(lines), mode="replace",
        note_id=conversation_id, note_name="Threads", caller=_CALLER,
    )
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
