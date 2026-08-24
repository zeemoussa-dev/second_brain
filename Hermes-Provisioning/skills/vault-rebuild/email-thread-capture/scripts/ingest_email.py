"""CLI entry point: create a Thread (on first sight of its
conversation_id) and write one message into it, ensuring a bare Person
note + wikilink for the sender AND every recipient.

Usage:
    python ingest_email.py --vault-path P --input-file F

F is a JSON file (write it with the `write_file` tool before calling --
email bodies can be up to 50,000 chars, too large for a safe CLI arg):
{
  "conversation_id": str, "message_id": str, "received": str,
  "sender_name": str, "sender_email": str, "subject": str, "body": str,
  "sender_department": str, "sender_job_title": str,
  "sender_company_name": str,   // optional, 2026-08-21 -- see below
  "recipients": [{"name": str, "email": str, "department": str,
                  "job_title": str, "company_name": str}, ...]   // optional
}

sender_department/sender_job_title/sender_company_name and each
recipient's own department/job_title/company_name (2026-08-21, operator:
"People need more fields (Department, Role)") come straight from
list_recent_emails.py's own Outlook GAL lookup when present -- blank for
an external contact, which is correct (no GAL entry to read). Missing
entirely (older callers, or a hand-built payload) is treated the same as
blank.

Prints {"thread_created", "message_created", "thread_path",
"message_path"} to stdout. Idempotent -- safe to call more than once for
the same message_id.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import vault_lib


def ingest_email(vault_path: Path, data: dict) -> dict:
    conversation_id = data["conversation_id"]
    message_id = data["message_id"]
    received = data["received"]
    sender_name = data["sender_name"]
    sender_email = data["sender_email"]
    subject = data["subject"]
    body = data["body"]
    recipients = data.get("recipients") or []
    sender_department = data.get("sender_department") or ""
    sender_job_title = data.get("sender_job_title") or ""
    sender_company_name = data.get("sender_company_name") or ""

    # 2026-08-21, operator: "messages (email) should have the Email title
    # not the sender name" -- readable_name is now the message's own
    # (Re:-stripped) subject, not the sender. This does NOT reintroduce
    # the original "every message in a thread looks the same" bug: the
    # readable-name stem already carries time-of-day (see vault_lib.
    # raw_message_note_path's own 2026-08-21 fix), which distinguishes
    # same-subject replies on its own regardless of what text follows it.
    readable_name = vault_lib.clean_subject(subject)

    existing_directory = vault_lib.resolve_thread_directory(vault_path, conversation_id)
    thread_created = False
    if existing_directory is None:
        vault_lib.create_thread_note_baseline(vault_path, conversation_id, thread_name=subject, tags=[])
        thread_created = True
        existing_directory = vault_lib.thread_directory_paths(vault_path, conversation_id)["directory"]

    message_created = False
    if not vault_lib.raw_message_note_exists(vault_path, conversation_id, message_id, received, readable_name=readable_name):
        participant_links: list[str] = []
        seen_emails: set[str] = set()
        sender_participant = {
            "name": sender_name, "email": sender_email,
            "department": sender_department, "job_title": sender_job_title, "company_name": sender_company_name,
        }
        all_participants = [sender_participant] + list(recipients)
        for participant in all_participants:
            email = (participant.get("email") or "").strip().lower()
            if not email or email in seen_emails:
                continue
            seen_emails.add(email)
            person_result = vault_lib.ensure_bare_person_note(
                vault_path, participant.get("name") or email, participant["email"],
                department=participant.get("department") or "",
                role=participant.get("job_title") or "",
                company=participant.get("company_name") or "",
            )
            if person_result is not None:
                participant_links.append(f"[[{Path(person_result['note_path']).stem}]]")

        vault_lib.create_raw_message_note(
            vault_path,
            conversation_id=conversation_id,
            message_id=message_id,
            received=received,
            sender=sender_name,
            sender_email=sender_email,
            subject=subject,
            body=body,
            readable_name=readable_name,
            participant_links=participant_links,
        )
        message_created = True

    # 2026-08-21, operator: Threads need a "last message" timestamp so a
    # recurring job can tell "already summarized, nothing new since" apart
    # from "needs a summary" -- kept current on every ingest call (not
    # just when message_created), idempotent since it only advances, never
    # regresses (see update_thread_last_message_at's own docstring).
    vault_lib.update_thread_last_message_at(vault_path, conversation_id, received)

    message_path = vault_lib.raw_message_note_path(vault_path, conversation_id, message_id, received, readable_name=readable_name)
    return {
        "thread_created": thread_created,
        "message_created": message_created,
        "thread_path": str(existing_directory / f"{existing_directory.name}.md"),
        "message_path": str(message_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--input-file", required=True)
    args = parser.parse_args()

    vault_path = Path(args.vault_path)
    # utf-8-sig: tolerates a leading BOM, which Windows tooling (PowerShell
    # redirection, some editors) routinely stamps on a "UTF-8" file --
    # plain "utf-8" would reject it as invalid JSON. Same defensive parse
    # Hermes' own SKILL.md frontmatter loader uses, for the same reason.
    data = json.loads(Path(args.input_file).read_text(encoding="utf-8-sig"))
    result = ingest_email(vault_path, data)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
