"""Stage 1 of the redesigned Email Capture pipeline (`REQ-SB-71-US-02`,
`ADR-048` Decision 3) -- the fast, zero-Compass raw-capture half. Reuses
`email_pull.pull_and_stage_emails`/`email_staging` VERBATIM as its
raw-fetch substrate (the PRD's own explicit "matching this project's own
decoupled-pull lesson... extended one level deeper" instruction, taken
literally): every currently-staged email is written as an immutable,
verbatim raw message note under its Thread's own `messages/` directory,
and provisionally grouped into a Thread using Outlook's own
`conversation_id` alone -- no merge-vs-new-Thread judgment, no Compass
call, ever, anywhere in this module.

Zero `compass_client` import -- Stage 1 has zero dependency on Compass
being up, fast, or reachable (Scenario 3/AC-03). The real Compass-backed
judgment (customer/kind classification, `## Summary` regeneration) is
Stage 2's own separate, decoupled scope (`email_classification.
synthesize_thread`, `T05`).

Coder-disclosed composition choice (`REQ-SB-71-US-02-T03`/`T07`): `T01`'s
own `create_raw_message_note` primitive persists text content only --
attachment BYTES are never part of a raw message note's own frontmatter/
body. Since `email_staging`'s own staged copy (the only place a real
attachment's bytes exist once Outlook-COM fetch has completed) is removed
by THIS module immediately after each email's own raw message note is
written, `T07`'s later Files/OKF companion would have no durable source
of real bytes to work from at all unless Stage 1 itself persists them
somewhere durable first. This module reuses the EXISTING, unmodified
`vault_writer.write_attachments` primitive (no new attachment-saving
mechanism, per `T07`'s own Constraint) as that durable store --
`Work/Threads/attachments/<slug-of-conversation_id>/<slug-of-message_id>/
<filename>`, a location nothing in this codebase ever cleans up. `T07`'s
own composing function re-derives this SAME deterministic location to
read the real bytes back before producing the final `files/` OKF
companion."""
from __future__ import annotations

from app.data_access import email_staging, vault_writer
from app.business.pipelines import email_pull


def capture_raw_thread_messages(limit: int = 10) -> dict:
    """Stage 1 -- real Outlook-COM fetch (via `pull_and_stage_emails`),
    then drains every currently-staged, not-yet-message-noted email into
    its own immutable raw message note, ensuring each Thread's own
    distilled concept file exists (created empty -- Stage 1 itself never
    writes `## Summary`, per Scenario 1/AC-01). A staged email is removed
    from `email_staging` only AFTER its own raw message note has been
    durably written (never removed first -- avoids losing content on a
    mid-write crash). Every raw message note write is guarded by `raw_
    message_note_exists` first, so a re-run over an overlapping staged
    batch never double-writes the same `message_id` (Scenario 2/AC-02).

    Returns `{"pulled": <pull_and_stage_emails summary dict>, "processed":
    [<message_id>, ...], "skipped_already_noted": [<message_id>, ...],
    "conversation_ids_touched": [<conversation_id>, ...]}` -- the last key
    is additive (`BUGFIX-05-US-01`, `ADR-051`), the distinct
    `conversation_id`s of every item in `processed` this run (never
    `skipped_already_noted` -- if a message's own note already existed,
    nothing NEW happened this tick for that conversation), consumed by
    `run_email_capture_pipeline`'s own Stage-2 composition to know which
    Threads need re-synthesis. An honest per-run summary, never raising
    for an individual staged email's own processing (mirrors this
    codebase's own per-item resilience posture elsewhere)."""
    pull_summary = email_pull.pull_and_stage_emails(limit=limit)

    processed: list[str] = []
    skipped_already_noted: list[str] = []
    conversation_ids_touched: list[str] = []

    for staged_email in email_staging.list_staged_emails():
        message_id = staged_email["id"]
        conversation_id = staged_email["conversation_id"]
        received = staged_email["received"]

        if vault_writer.raw_message_note_exists(conversation_id, message_id, received):
            skipped_already_noted.append(message_id)
            email_staging.remove_staged_email(message_id)
            continue

        vault_writer.create_raw_message_note(
            conversation_id=conversation_id,
            message_id=message_id,
            received=received,
            sender=staged_email["sender_name"],
            sender_email=staged_email["sender_email"],
            subject=staged_email["subject"],
            body=staged_email["body"],
        )

        # Durable attachment-byte persistence -- see this module's own
        # docstring. Reuses write_attachments verbatim; a no-op (returns
        # []) when this email carries no real attachments.
        if staged_email.get("attachments"):
            vault_writer.write_attachments(
                subfolder="Work/Threads",
                note_stem=conversation_id,
                message_segment=message_id,
                attachments=staged_email["attachments"],
            )

        # Provisional grouping is ConversationID-only -- this function
        # never performs a merge-vs-new-Thread judgment (Stage 2's own
        # scope); it only ensures a Thread concept file exists somewhere,
        # nothing more. Existence check retargeted (REQ-SB-72-US-01-T02,
        # ADR-049 Decision 1) from directly composing thread_directory_
        # paths(conversation_id)["concept"] -- which silently resolves to
        # the WRONG, stale, since-renamed path once a Thread's own
        # directory has been renamed (T03's own Rename Job) -- to resolve_
        # thread_note_path, matching Stage 2's own existing semantics
        # exactly (zero behavior change for a not-yet-renamed Thread;
        # correct behavior for a renamed one).
        if vault_writer.resolve_thread_note_path(conversation_id) is None:
            vault_writer.create_thread_note_baseline(
                conversation_id, thread_name=staged_email["subject"]
            )

        email_staging.remove_staged_email(message_id)
        processed.append(message_id)
        if conversation_id not in conversation_ids_touched:
            conversation_ids_touched.append(conversation_id)

    return {
        "pulled": pull_summary,
        "processed": processed,
        "skipped_already_noted": skipped_already_noted,
        "conversation_ids_touched": conversation_ids_touched,
    }
