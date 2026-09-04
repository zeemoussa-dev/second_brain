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
  "direction": str,   // optional, 2026-09-02 -- "sent" | "received", see below
  "recipients": [{"name": str, "email": str, "department": str,
                  "job_title": str, "company_name": str,
                  "type": str}, ...]   // optional, type: "to" | "cc"
}

sender_department/sender_job_title/sender_company_name and each
recipient's own department/job_title/company_name (2026-08-21, operator:
"People need more fields (Department, Role)") come straight from
list_recent_emails.py's own Outlook GAL lookup when present -- blank for
an external contact, which is correct (no GAL entry to read). Missing
entirely (older callers, or a hand-built payload) is treated the same as
blank.

`direction` and each recipient's own `type` (2026-09-02,
REQ-SB-87-US-02-T06) come straight from outlook_lib.py's own real
per-folder/per-recipient Outlook COM read (via list_recent_emails.py,
unmodified pass-through) -- the real VALUE is never re-derived here.
Missing entirely (older callers) is treated as an empty string / omitted
per-recipient type. `direction` is written straight through into
frontmatter; each recipient's own `type` is written into frontmatter as
two separate flat email-string lists,
`to_recipients`/`cc_recipients`, not one combined list of {email, type}
objects -- confirmed live (2026-09-02) that vault_manager.py's own
hand-rolled frontmatter writer (`_format_frontmatter_value`/
`_parse_frontmatter_value`) only round-trips scalars and homogeneous
string lists; a list of nested dicts silently parses back as an empty
list on read. Splitting by type keeps each recipient's own real type
structurally distinguishable (which list it's in) while staying inside
the real engine's own supported value shapes -- a real, disclosed shape
choice for this task's own `## Files to Modify`, not an engine change.

Prints {"thread_created", "message_created", "thread_path",
"message_path", "skipped_as_noise"} to stdout. Idempotent -- safe to call
more than once for the same message_id.

2026-09-02 (REQ-SB-87-US-03-T03, ADR-018): on a genuinely first-seen
`conversation_id` ONLY (the `if thread_path is None:` branch below), ONE
bounded `hermes -p email-capture-classifier chat -Q --query-file ...`
relay call judges the new conversation against the persisted
`.second-brain/data/EmailCapture/noise_definition.json` before any
Thread/RawMessage note is written. A `true` verdict returns early --
`skipped_as_noise: true`, nothing written anywhere for this email. A
`false` verdict (or a `direction: "sent"` first message, see below)
proceeds to create the Thread exactly as before, stamped with the
verdict's own real `classification` value. An ALREADY-existing Thread's
messages never reach this branch at all -- captured unconditionally, no
relay call, per the operator's own locked "if we already have a thread...
even if it counts as noise... need to be stored" rule.

Operator-locked, 2026-09-02: "No Sent Items are never noise" -- a
first-seen message whose own `direction` is `"sent"` is NEVER treated as
Noise, regardless of its own content. This is enforced here, the CALLER's
side (never the classifier's own job, per T02's own SOUL.md, which
documents this same rule only as a narrow secondary safety net) -- the
relay is still called (a real `classification` value is still needed,
never fabricated), but this function never reads/acts on that verdict's
own `is_noise` value when `direction == "sent"`; the skip branch is
structurally unreachable for it.

A relay failure/timeout, an unparseable response, or a missing/unreadable
noise-definition artifact all raise (uncaught) rather than silently
defaulting either way -- this conversation is treated as NOT YET
classified: no Thread is created, no permanent skip is recorded. The
SAME per-email `try/except ... continue` pattern already in both
orchestrators tolerates the resulting non-zero exit; since no Thread was
written, `existing_directory`/`find_by_id` stays `None` next tick, so the
conversation is naturally retried (ADR-018's own disclosed degrade
default).

2026-09-01 (REQ-SB-87-US-02-T01): Thread resolve/create and the
`last_message_at` advances-only stamp go through `vault_manager.py`
(`find_by_id`/`create`/`update`, `caller="ingest_email"` on the mutating
`create()` call) against the real `thread` Template.json
(`REQ-SB-87-US-01-T05`) -- the Thread's own stable `id` is its real
`conversation_id`, so `resolve_thread_directory`-style lookups by other
already-real Threads elsewhere keep working unchanged.

2026-09-01 (ESC-061 resolution, same-day follow-up): RawMessage creation
is now ALSO migrated, onto `vault_manager.create_dynamic_child()`'s new
`body=` flat-body mode (`Hermes-Provisioning/shared/vault_manager.py`) --
the real `thread/Template.json`'s own `messages` dynamic child declares
no `sections` at all, so the engine's original `sections`-only write path
always produced a genuinely EMPTY RawMessage body; `body=` writes the
real, flat, headerless email body exactly as `vault_lib.
create_raw_message_note` always did, byte-for-byte. Idempotency is now
the engine's own real `(conversation_id, message_id)` natural-key match
(the template's own declared `identity_fields`) instead of a bespoke
filename-existence pre-check -- `ensure_bare_person_note` (still entirely
untouched, per this story's own Constraints) is called unconditionally on
every ingest now rather than gated behind that stale pre-check, safe
because it is itself already documented idempotent
(insert-a-missing-key-only, never overwrites). One disclosed, real
divergence in the RawMessage note's own filename: `create_dynamic_child`
names a dynamic child from today's real ingestion date + a wall-clock
collision suffix (the SAME generic mechanism every other dynamic child
uses, `REQ-SB-87-US-01-T01`), not `vault_lib`'s own bespoke scheme (the
message's own `received` date/time + a message-id-keyed hash suffix) --
the identity-field match (not the filename) is what actually guarantees
idempotency, so this is a real naming-convention difference, never a
duplication risk. Logged as a scope-internal judgement call for human
spot-check (see this task's own Implementation Log), not silently
absorbed.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

import vault_lib
import vault_manager

# REQ-SB-87-US-03-T03 (ADR-018) -- the classify-or-skip relay target
# provisioned by T02; no cron job of its own, reached only from here.
_CLASSIFIER_PROFILE = "email-capture-classifier"
_HERMES_EXE = "hermes"
# A relay call's own real latency is genuinely variable (tens of seconds
# to several minutes, Learnings.md) -- never assume a hang from wall-clock
# alone; matches derive_noise_definition.py's own established timeout.
_CLASSIFIER_TIMEOUT_SECONDS = 420
# T01's own persisted artifact -- a real, structured file under the
# VAULT's own `.second-brain/data/` tree (ADR-018), never baked into the
# classifier profile's own static prompt, read fresh on every relay call.
_NOISE_DEFINITION_RELATIVE_PATH = Path("data") / "EmailCapture" / "noise_definition.json"
# T02's own locked lowercase verdict values (its Implementation Log,
# assumption 2) -- the only classification values ever written to a
# Thread's frontmatter.
_VALID_CLASSIFICATIONS = {"internal", "partner", "customer"}


def _read_noise_definition(vault_path: Path) -> dict:
    definition_path = vault_manager.data_root(vault_path) / _NOISE_DEFINITION_RELATIVE_PATH
    return json.loads(definition_path.read_text(encoding="utf-8"))


def _extract_json_object(raw: str) -> dict:
    """A real relay reply can carry leading/trailing prose or a fenced
    code block even when told not to -- locate the first '{' and let
    json.JSONDecoder.raw_decode find the matching close, rather than
    assuming the whole string is bare JSON. Same technique
    derive_noise_definition.py already uses for the same real reason."""
    start = raw.find("{")
    if start == -1:
        raise ValueError(f"no JSON object found in classify-or-skip relay response: {raw[:500]!r}")
    decoder = json.JSONDecoder()
    obj, _end = decoder.raw_decode(raw, start)
    return obj


def _build_classification_question(noise_definition: dict, data: dict, direction: str, recipients: list) -> str:
    recipient_lines = "\n".join(
        f"  - {(participant.get('name') or participant.get('email') or '').strip()} "
        f"<{(participant.get('email') or '').strip()}> "
        f"[{(participant.get('type') or 'unknown').strip()}] "
        f"({(participant.get('company_name') or 'unknown company').strip()})"
        for participant in recipients
    ) or "  (none given)"
    return (
        "Judge this real, new email conversation per your own SOUL.md and "
        "reply with exactly one JSON object.\n\n"
        "Current noise definition (the ONLY one that exists):\n"
        f"{json.dumps(noise_definition, ensure_ascii=False, indent=2)}\n\n"
        "New email:\n"
        f"  direction: {direction or '(not given)'}\n"
        f"  sender: {data.get('sender_name') or ''} <{data.get('sender_email') or ''}>\n"
        f"  recipients/participants:\n{recipient_lines}\n"
        f"  subject: {data.get('subject') or ''}\n"
        f"  body:\n{data.get('body') or ''}\n"
    )


def _classify_or_skip(vault_path: Path, data: dict, direction: str, recipients: list) -> dict:
    """ONE bounded, one-shot relay call -- ADR-018. Raises (never silently
    defaults) on any failure: relay non-zero exit, timeout, unparseable
    response, or a missing/unreadable noise-definition artifact."""
    noise_definition = _read_noise_definition(vault_path)
    question = _build_classification_question(noise_definition, data, direction, recipients)

    with tempfile.TemporaryDirectory(prefix="second_brain_classify_") as tmp_dir:
        query_path = os.path.join(tmp_dir, f"query_{uuid.uuid4().hex}.txt")
        Path(query_path).write_text(question, encoding="utf-8")
        args = [_HERMES_EXE, "-p", _CLASSIFIER_PROFILE, "chat", "-Q", "--query-file", query_path]
        # Explicit UTF-8 both sides -- same discipline as run_delta_capture.py's
        # own run_script()/derive_noise_definition.py's own _run_relay();
        # a real reply/body can carry a non-ASCII character the OS locale's
        # default encoding would otherwise mangle or crash on.
        proc = subprocess.run(
            args, capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=_CLASSIFIER_TIMEOUT_SECONDS,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"classify-or-skip relay failed (code {proc.returncode}): "
                f"{(proc.stderr or proc.stdout or '').strip()[:1000]}"
            )
        raw_response = (proc.stdout or "").strip()

    verdict = _extract_json_object(raw_response)
    if "is_noise" not in verdict:
        raise RuntimeError(f"classify-or-skip relay returned no 'is_noise' field: {raw_response[:500]!r}")
    return verdict


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
    # 2026-09-02 (REQ-SB-87-US-02-T06): threaded through unchanged from
    # outlook_lib.py's own real per-folder/per-recipient read -- never
    # inferred/re-derived here. Split into two flat email-string lists
    # (never one combined, undifferentiated list) because
    # vault_manager.py's own hand-rolled frontmatter writer only
    # round-trips scalars and homogeneous string lists, confirmed live --
    # see this task's own Implementation Log.
    direction = data.get("direction") or ""
    to_recipient_emails = [
        (participant.get("email") or "").strip()
        for participant in recipients
        if (participant.get("type") or "").lower() == "to" and (participant.get("email") or "").strip()
    ]
    cc_recipient_emails = [
        (participant.get("email") or "").strip()
        for participant in recipients
        if (participant.get("type") or "").lower() == "cc" and (participant.get("email") or "").strip()
    ]

    # 2026-08-21, operator: "messages (email) should have the Email title
    # not the sender name" -- readable_name is the message's own
    # (Re:-stripped) subject, not the sender; passed through as the
    # RawMessage's own `title` frontmatter (and create_dynamic_child's own
    # filename-slug hint, ESC-061 resolution, 2026-09-01) rather than the
    # sender's name.
    readable_name = vault_lib.clean_subject(subject)

    # Thread resolve/create mechanics now go through vault_manager.py
    # (REQ-SB-87-US-02-T01) -- the Thread's own real, stable id IS its
    # conversation_id (an already-unique, already-real external key, per
    # vault_manager.py's own "id" identity strategy docstring), so
    # find_by_id/create both key off it directly, no separate uuid
    # needed. `title=conversation_id` (not the subject) keeps the real
    # on-disk folder/filename keyed exactly as vault_lib's own
    # thread_directory_paths always has -- rename_thread.py (T02) is
    # still the only thing that ever relabels it to a human "<date>
    # <subject>" form, unchanged by this task.
    thread_template = vault_manager.load_template(vault_path, "thread")
    thread_path = vault_manager.find_by_id(vault_path, conversation_id, note_name="Threads")
    thread_created = False
    if thread_path is None:
        # 2026-09-02 (REQ-SB-87-US-02-T05, real-vault retrofit-safety
        # check, AC-06): a pre-migration Thread carries NO `id`
        # frontmatter field at all (vault_lib.py's own hand-rolled
        # implementation never wrote one) -- confirmed live against a
        # real pre-existing Thread before this fix -- so find_by_id's
        # strict id-match can never find it. Left unguarded, EVERY real
        # pre-existing conversation would look first-seen: a genuine
        # DUPLICATE Thread created (thread/Template.json's own
        # on_existing_title is "always_new", so create() would not
        # collide-refuse either), plus an unwanted classify-or-skip relay
        # call for content already captured, in some cases long before
        # this feature existed. vault_lib.resolve_thread_directory
        # (already imported, unchanged -- the SAME hand-written lookup
        # update_thread_last_message_at already relies on) is the real,
        # pre-existing way to find such a Thread by its own
        # `conversation_id` field, scoped to real Thread root notes only
        # (never a messages/ or files/ companion, which also carry a
        # conversation_id key). Found: mint-and-backfill its real `id` on
        # first touch -- the SAME pattern REQ-SB-87-US-04-T01's own
        # apply_thread_review.py migration already established live for
        # the identical no-id-on-real-pre-migration-content problem
        # (MEMORY.md, 2026-09-01) -- then treat it exactly like any other
        # already-existing Thread: no classify-or-skip relay call, no new
        # Thread created, its message captured unconditionally.
        legacy_directory = vault_lib.resolve_thread_directory(vault_path, conversation_id)
        if legacy_directory is not None:
            legacy_thread_path = legacy_directory / f"{legacy_directory.name}.md"
            vault_manager.update(vault_path, legacy_thread_path, frontmatter={"id": conversation_id})
            thread_path = legacy_thread_path

    if thread_path is None:
        # ADR-018 / REQ-SB-87-US-03-T03: the classify-or-skip relay call
        # fires HERE ONLY -- a genuinely first-seen conversation_id, BEFORE
        # any Thread/RawMessage note is written. An already-existing
        # Thread's own later messages never reach this branch at all (the
        # branch itself is the structural guarantee, not a runtime check
        # -- REQ-SB-87-US-03-AC-03/AC-09).
        verdict = _classify_or_skip(vault_path, data, direction, recipients)
        if direction != "sent" and verdict.get("is_noise"):
            # REQ-SB-87-US-03-AC-01: a genuine skip leaves zero vault
            # trace -- no Thread, no RawMessage, no Person-note side
            # effect, nothing written anywhere for this email.
            return {
                "thread_created": False,
                "message_created": False,
                "thread_path": None,
                "message_path": None,
                "skipped_as_noise": True,
            }
        # 2026-09-02, operator-locked ("No Sent Items are never noise"):
        # a first-seen `direction: "sent"` message's own `is_noise` verdict
        # is never read/acted on above -- this is the CALLER's own guard
        # (REQ-SB-87-US-03-AC-08), not the classifier's job. It still gets
        # a real classification value from the same relay call, never
        # fabricated.
        classification_value = verdict.get("classification")
        if classification_value not in _VALID_CLASSIFICATIONS:
            # Never fabricate a classification for a Thread that IS being
            # created -- an invalid/missing value degrades the same way
            # any other relay failure does (ADR-018's own Consequences):
            # raise, no Thread created, naturally retried next tick.
            raise RuntimeError(
                f"classify-or-skip relay returned an invalid classification "
                f"{classification_value!r} for a non-noise verdict "
                f"(conversation_id={conversation_id!r})"
            )
        create_result = vault_manager.create(
            vault_path,
            thread_template,
            title=conversation_id,
            note_name="Threads",
            note_id=conversation_id,
            frontmatter={
                "conversation_id": conversation_id,
                "thread_name": subject,
                "tags": [],
                "classification": classification_value,
            },
            caller="ingest_email",
        )
        thread_created = True
        thread_path = Path(create_result["path"])

    # ensure_bare_person_note is documented idempotent (only ever inserts
    # a genuinely MISSING frontmatter key, never overwrites a real value)
    # -- safe to call every ingest, not just a first-seen message. Kept
    # unconditional now that RawMessage idempotency is the engine's own
    # honest identity-field match below, not a bespoke pre-check on the
    # OLD filename scheme (which a migrated RawMessage would never match
    # anyway).
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

    # RawMessage creation via vault_manager.py's dynamic-child mechanism
    # (REQ-SB-87-US-01-T01), flat-body mode (ESC-061 resolution) -- the
    # real body is written as-is, no synthetic section header. The
    # engine's own idempotent (conversation_id, message_id) natural-key
    # match (thread/Template.json's declared identity_fields) is what
    # makes this call safe to repeat for the same message -- never a
    # second real note, regardless of this call's own filename output.
    message_result = vault_manager.create_dynamic_child(
        vault_path, thread_template, root_id=conversation_id, child_name="messages",
        identity={"conversation_id": conversation_id, "message_id": message_id},
        frontmatter={
            "title": readable_name,
            "sender": sender_name,
            "sender_email": sender_email,
            "subject": subject,
            "received": received,
            "participant_links": participant_links,
            "direction": direction,
            "to_recipients": to_recipient_emails,
            "cc_recipients": cc_recipient_emails,
        },
        body=body,
    )
    message_created = message_result["created"]
    message_path = Path(message_result["path"])

    # 2026-08-21, operator: Threads need a "last message" timestamp so a
    # recurring job can tell "already summarized, nothing new since" apart
    # from "needs a summary" -- kept current on every ingest call (not
    # just when message_created), idempotent since it only advances, never
    # regresses. Advances-only comparison stays the same hand-written
    # business logic vault_lib.update_thread_last_message_at always had
    # (REQ-SB-87-US-02's own Constraint) -- only the underlying
    # read/write mechanics move to vault_manager.py.
    thread_frontmatter, _ = vault_manager.read_note(thread_path)
    current_last_message_at = thread_frontmatter.get("last_message_at") or ""
    if received > current_last_message_at:
        vault_manager.update(vault_path, thread_path, frontmatter={"last_message_at": received})

    return {
        "thread_created": thread_created,
        "message_created": message_created,
        "thread_path": str(thread_path),
        "message_path": str(message_path),
        "skipped_as_noise": False,
    }


def main() -> int:
    # 2026-09-02 (REQ-SB-87-US-02-T05, found live during the real
    # ~100-email retrofit): a real subject/body can carry a Unicode
    # character (e.g. an emoji) Windows' default console codepage
    # (cp1252, not UTF-8) can't encode -- printing the JSON result below
    # without this crashed ingest_email.py outright on 2 of 100 real
    # retrofitted messages (subjects containing U+1F680). The SAME
    # pre-existing bug class list_recent_emails.py already fixed for
    # itself (2026-08-24, its own module docstring) was never applied
    # here -- this is the same one-line fix, not a new technique.
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--vault-path",
        # Defaults to what Second Brain's setup wizard writes into Hermes'
        # own .env, so a Skill never has to name a machine-specific
        # absolute path and a bundle never has to have one rewritten on
        # import. Pass it only to override.
        default=os.environ.get("SECOND_BRAIN_VAULT_PATH", ""),
    )
    parser.add_argument("--input-file", required=True)
    args = parser.parse_args()
    if not (args.vault_path or "").strip():
        # An empty value would become Path("") -> the CWD, which is exactly the
        # silent-wrong-folder failure this whole change exists to remove.
        raise SystemExit(
            "No vault path. Set SECOND_BRAIN_VAULT_PATH in Hermes' own .env "
            "(Second Brain's setup wizard writes it) or pass --vault-path."
        )

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
