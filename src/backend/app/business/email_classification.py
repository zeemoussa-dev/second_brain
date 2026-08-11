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

from app.business import customer_hub_linking
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


def run_capture_and_record_completion(limit: int = 10) -> list[dict]:
    """Scheduling-layer entry point (ADR-005): runs the same capture
    pipeline the manual /poc/classify-emails endpoint uses, then records
    completion via vault_writer so the shared last-run record (read by
    the future REQ-SB-11 observability UI) reflects every scheduled run,
    not just manual ones."""
    results = classify_recent_emails(limit=limit)
    vault_writer.record_capture_run_completed()
    return results
