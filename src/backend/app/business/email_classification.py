"""Orchestrates the email-classification POC: fetch mail (meeting invites
already excluded at the Outlook layer), classify each by customer AND kind
via Compass, save any attachments, link it to other notes in the same
Outlook thread, file the result into the vault.

Per Documentation/References/beyond-the-second-brain-methodology.md
("folders are the enemy of thinking" — a note's customer relevance is
multidimensional, not a single fixed home), only `kind` is a folder level
(Work/<Kind>/); `customer` is frontmatter + a tag only, never a folder.
Reclassifying which customer a note belongs to is a tag edit, not a file
move — this is also how the earlier Unsorted-→-Affiliate reorg problem
gets solved without ever building a dedicated merge operation.

Both the customer list and the kind list are dynamic — read from the vault
itself (app.data_access.vault_writer.list_known_customers / list_known_kinds),
never hardcoded. Each starts empty and grows as Compass proposes new values;
this is the extensibility point for adding new filters/kinds later without a
code change. Already-processed emails (tracked by Outlook EntryID) are
skipped so a rerun — including a full-inbox pull — never reclassifies the
same email twice.
"""
from __future__ import annotations

from app.business import (
    customer_hub_linking,
    meeting_classification,
    pending_approval_registry,
    people_extraction,
    todo_classification,
    vault_indexing,
    working_mode_registry,
)
from app.data_access import compass_client, outlook_com, vault_writer


def classify_recent_emails(limit: int = 10) -> list[dict]:
    emails = outlook_com.list_recent_mail(limit=limit)
    already_processed = vault_writer.load_processed_email_ids()
    results: list[dict] = []

    for email in emails:
        if email["id"] in already_processed:
            continue

        known_customers = vault_writer.list_known_customers()
        known_kinds = vault_writer.list_known_kinds()
        try:
            classification = compass_client.classify_email(
                subject=email["subject"],
                sender=email["sender_email"] or email["sender_name"],
                body=email["body"],
                known_customers=known_customers,
                known_kinds=known_kinds,
            )
        except compass_client.CompassError as exc:
            results.append({
                "subject": email["subject"],
                "error": str(exc),
            })
            continue

        customer = classification["customer"]
        kind = classification["kind"]
        subfolder = f"Work/{kind}"
        # Suffix with a short slice of the Outlook EntryID: same-subject,
        # same-day emails (a resend, a duplicate share notification) are
        # common enough that date+subject alone collides and silently
        # overwrites — EntryID is unique per item, so this can't.
        filename_stem = f"{email['received'][:10]}-{email['subject']}-{email['id'][-8:]}"

        saved_attachments = vault_writer.write_attachments(
            subfolder=subfolder,
            note_stem=filename_stem,
            attachments=email["attachments"],
        )
        related_note_stems = vault_writer.find_related_note_stems(email["conversation_id"])

        body = email["body"]
        if related_note_stems:
            body += "\n\n## Related Emails\n"
            for stem in related_note_stems:
                body += f"- [[{stem}]]\n"
        if saved_attachments:
            body += "\n\n## Attachments\n"
            for att in saved_attachments:
                if att["saved"]:
                    body += f"- [{att['filename']}]({att['relative_link']})\n"
                else:
                    body += f"- {att['filename']} (not saved — {att['size']} bytes exceeds the size cap)\n"

        note_path = vault_writer.write_note(
            subfolder=subfolder,
            filename_stem=filename_stem,
            frontmatter={
                "type": kind,
                "customer": customer,
                "tags": vault_writer.build_tags(customer, kind),
                "classification_confidence": classification["confidence"],
                "subject": email["subject"],
                "sender": email["sender_name"],
                "sender_email": email["sender_email"],
                "received": email["received"],
                "outlook_entry_id": email["id"],
                "conversation_id": email["conversation_id"],
            },
            body=body,
        )
        vault_writer.mark_email_processed(email["id"])
        vault_writer.record_conversation_note(email["conversation_id"], filename_stem)
        customer_hub_linking.ensure_hub_note_and_link(note_path, customer)
        person_result = people_extraction.ensure_person_note_for_captured_email(
            email["sender_name"], email["sender_email"]
        )
        if person_result is not None:
            people_extraction.link_email_to_person(note_path, person_result["note_path"])
        results.append({
            "subject": email["subject"],
            "customer": customer,
            "kind": kind,
            "confidence": classification["confidence"],
            "attachments": len(saved_attachments),
            "related_emails": len(related_note_stems),
            "note_path": note_path,
        })

    return results


def run_capture_for_agent(agent_id: str, limit: int = 10) -> list[dict]:
    """The one place both the scheduled tick below and a
    Pending-Approvals approval (app/api/pending_approvals_router.py,
    T06) resolve "which function does this agent_id's own background
    capture step call" — so the mapping is never duplicated (ADR-018
    point 4)."""
    if agent_id == "email-capture":
        return classify_recent_emails(limit=limit)
    if agent_id == "meeting-capture":
        return meeting_classification.classify_recent_meetings()
    if agent_id == "todo-capture":
        return todo_classification.classify_recent_todos()
    raise ValueError(f"No background capture step for agent_id={agent_id!r}")


def run_capture_and_record_completion(limit: int = 10) -> list[dict]:
    """Scheduling-layer entry point (ADR-005): runs the same capture
    pipeline the manual /poc/classify-emails endpoint uses, then records
    completion via vault_writer so the shared last-run record reflects
    every scheduled run, not just manual ones. Also runs Meetings
    capture (REQ-SB-08, ADR-008) on the same tick — no second scheduled
    job, no second concurrency guard; app/scheduling/capture_scheduler.py
    requires zero changes since it already treats this function as an
    opaque unit.

    REQ-SB-21/ADR-018 point 4: each of the two capture steps below is
    now independently gated by that agent's own working mode.
    Autonomous runs the step exactly as before this story (no change to
    the default-path behaviour or history-entry text for email-capture).
    Supervised creates a trigger="background" pending-approval record
    (idempotent per tick) plus a "proposal" history entry instead of
    running the step. Manual skips silently — no record, no history
    entry at all, the literal "stays dormant" PRD language for the one
    trigger context where Manual and Supervised are meant to differ (see
    app/api/agents_router.py, T04, for the chat/direct trigger context,
    where Manual does not gate).

    REQ-SB-11/architecture.md "Agent Activity & Error Observability":
    each Autonomous-mode capture step below is now independently
    wrapped in a try/except -- an exception escaping that step's own
    per-item handling (e.g. outlook_com.OutlookUnavailable) is caught
    here and recorded as a new "run_error"-kind history entry instead
    of propagating uncaught (mirrors ADR-015's own call-site
    honest-failure-funnel pattern, applied to this orchestration
    function). Meeting-capture's Autonomous branch also now writes its
    own "run_event" entry on success -- parity with email-capture,
    closing REQ-SB-11's confirmed "meeting-capture runs are silently
    omitted" gap. record_capture_run_completed() is only called when
    neither step's try/except fired this tick -- preserving its
    existing "only reached when nothing raised" semantics
    (REQ-SB-31-US-01's own documented last_capture_run.json signal)
    unchanged.

    Return shape is unchanged: still exactly the email-capture results
    list (REQ-SB-08-US-01-T04's own documented constraint) — empty when
    email-capture's own mode is non-Autonomous, and now also empty on a
    caught email-capture failure — both are the same honest "no items
    filed this tick" signal, new user-opted-into/failure-path behaviour,
    not a default-path regression, since Autonomous stays the default
    per this story's own behavior-preservation Constraint.
    """
    email_mode = working_mode_registry.get_agent_working_mode("email-capture")
    email_capture_failed = False
    results: list[dict] = []
    if email_mode == "autonomous":
        try:
            results = run_capture_for_agent("email-capture", limit=limit)
        except Exception as exc:  # noqa: BLE001 -- honest-failure-reporting funnel (REQ-SB-11 Scenario 2), extends ADR-015's existing pattern to this call site
            email_capture_failed = True
            results = []
            vault_writer.append_agent_history_entry(
                "email-capture",
                "run_error",
                f"Capture run failed — {exc}",
            )
        else:
            vault_writer.append_agent_history_entry(
                "email-capture",
                "run_event",
                f"Capture run completed — {len(results)} email(s) filed",
            )
    elif email_mode == "supervised":
        approval = pending_approval_registry.create_pending_approval(
            agent_id="email-capture",
            trigger="background",
            action_id=None,
            description="Run the scheduled email-capture step — checks the "
                        "inbox for new mail and files it into the vault.",
        )
        vault_writer.append_agent_history_entry(
            "email-capture",
            "proposal",
            f"Proposed — {approval['description']} Awaiting your approval.",
            pending_approval_id=approval["id"],
        )
        results = []
    else:  # manual — stays dormant this tick, no record, no history entry
        results = []

    meeting_mode = working_mode_registry.get_agent_working_mode("meeting-capture")
    meeting_capture_failed = False
    if meeting_mode == "autonomous":
        try:
            meeting_results = run_capture_for_agent("meeting-capture")
        except Exception as exc:  # noqa: BLE001 -- honest-failure-reporting funnel (REQ-SB-11 Scenario 2), extends ADR-015's existing pattern to this call site
            meeting_capture_failed = True
            vault_writer.append_agent_history_entry(
                "meeting-capture",
                "run_error",
                f"Capture run failed — {exc}",
            )
        else:
            vault_writer.append_agent_history_entry(
                "meeting-capture",
                "run_event",
                f"Capture run completed — {len(meeting_results)} meeting(s) filed",
            )
    elif meeting_mode == "supervised":
        approval = pending_approval_registry.create_pending_approval(
            agent_id="meeting-capture",
            trigger="background",
            action_id=None,
            description="Run the scheduled meeting-capture step — checks the "
                        "calendar for new events and files them into the vault.",
        )
        vault_writer.append_agent_history_entry(
            "meeting-capture",
            "proposal",
            f"Proposed — {approval['description']} Awaiting your approval.",
            pending_approval_id=approval["id"],
        )
    # else: manual — stays dormant this tick, no record, no history entry

    todo_mode = working_mode_registry.get_agent_working_mode("todo-capture")
    todo_capture_failed = False
    if todo_mode == "autonomous":
        try:
            todo_results = run_capture_for_agent("todo-capture")
        except Exception as exc:  # noqa: BLE001 -- honest-failure-reporting funnel (REQ-SB-11), same shape as the email/meeting branches above
            todo_capture_failed = True
            vault_writer.append_agent_history_entry(
                "todo-capture",
                "run_error",
                f"Capture run failed — {exc}",
            )
        else:
            vault_writer.append_agent_history_entry(
                "todo-capture",
                "run_event",
                f"Capture run completed — {len(todo_results)} task(s) filed",
            )
    elif todo_mode == "supervised":
        approval = pending_approval_registry.create_pending_approval(
            agent_id="todo-capture",
            trigger="background",
            action_id=None,
            description="Run the scheduled To-Do capture step — checks "
                        "the Outlook Tasks folder for new/changed tasks "
                        "and files them into the vault.",
        )
        vault_writer.append_agent_history_entry(
            "todo-capture",
            "proposal",
            f"Proposed — {approval['description']} Awaiting your approval.",
            pending_approval_id=approval["id"],
        )
    # else: manual — stays dormant this tick, no record, no history entry

    # Vault indexing (REQ-SB-01-US-01, ADR-024): runs on every tick,
    # unconditionally -- not gated by either capture step's own
    # working mode (ADR-018/ADR-020) NOR by whether a capture step
    # failed above (REQ-SB-11) -- indexing is core plumbing, not an
    # Agents Map agent action, and re-indexing after a partial-failure
    # tick still correctly reflects whatever the other, non-failing
    # step actually wrote. Satisfies Scenario 9 ("no separate,
    # independent schedule was needed for the index specifically")
    # with zero changes to capture_scheduler.py itself, which already
    # treats this whole function as an opaque unit.
    vault_indexing.rebuild_index()

    if not email_capture_failed and not meeting_capture_failed and not todo_capture_failed:
        vault_writer.record_capture_run_completed()
    return results
