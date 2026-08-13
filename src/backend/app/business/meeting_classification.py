"""Orchestrates the Meetings-capture pipeline (REQ-SB-08): fetch calendar
events in the sync window, exclude the vault owner's own email from the
attendee list, derive a customer via majority vote among attendee
companies, write/top-up the Meeting note, link the matched customer hub
and every attendee's Person note. Mirrors email_classification.py's shape
exactly (ADR-008) and reuses people_extraction.ensure_person_note /
customer_hub_linking's granular primitives as-is — no changes to either
module's existing public functions, per the story's Constraints.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from app.business import customer_hub_linking, people_extraction
from app.config import settings
from app.data_access import outlook_com, vault_writer


def _exclude_self(attendees: list[dict]) -> list[dict]:
    """Filters settings.self_email (case-insensitive) out of the attendee
    list before any attendee reaches Person-note creation or customer
    derivation (Scenario 11) — the vault owner is never captured as a
    Person and their own company never participates in the majority vote
    below."""
    self_email = settings.self_email.lower()
    return [a for a in attendees if (a.get("email") or "").lower() != self_email]


def _derive_meeting_customer(attendees: list[dict]) -> str | None:
    """Majority vote among each (post-exclusion) attendee's matched
    customer, via the unchanged derive_company_from_email/
    find_matching_customer; ties broken by whichever matched customer was
    first encountered in attendee order (To then Cc) — the
    architecture.md-recorded tie-break rule. No match among any attendee
    means no customer at all (Scenario 3)."""
    match_counts: Counter[str] = Counter()
    first_seen_order: list[str] = []
    for attendee in attendees:
        company = people_extraction.derive_company_from_email(attendee.get("email") or "")
        matched = people_extraction.find_matching_customer(company)
        if matched:
            if matched not in match_counts:
                first_seen_order.append(matched)
            match_counts[matched] += 1
    if not match_counts:
        return None
    max_votes = max(match_counts.values())
    for customer in first_seen_order:
        if match_counts[customer] == max_votes:
            return customer
    return None  # unreachable — defensive fallback only


def classify_recent_meetings(days_back: int = 7, days_ahead: int = 14, limit: int = 50) -> list[dict]:
    """The shared "ensure this calendar event's Meeting note exists and is
    up to date" operation — called once per fetched event, every run.
    Deliberately does not gate on load_processed_meeting_ids as a skip
    check (see this module's own module-level note below on why) —
    meeting_note_exists()'s deterministic-filename check is what prevents
    duplicate notes (Scenario 2, 7, 9); every in-window event still flows
    through the idempotent top-up path on every rerun (Scenario 2, 6).
    mark_meeting_processed is still called every run as an audit record."""
    events = outlook_com.list_calendar_events(days_back=days_back, days_ahead=days_ahead, limit=limit)
    results: list[dict] = []

    for event in events:
        attendees = _exclude_self(event["attendees"])
        customer = _derive_meeting_customer(attendees)

        note_path, already_existed = vault_writer.resolve_meeting_note_path(
            event["subject"], event["start"], event["id"],
        )
        note_path = Path(note_path)
        if already_existed:
            vault_writer.ensure_meeting_note_baseline_frontmatter(
                note_path, event["subject"], customer, event["start"], event["end"],
                event["location"], event["organizer"],
            )
            created = False
        else:
            vault_writer.create_meeting_note_baseline(
                event["subject"], customer, event["start"], event["end"],
                event["location"], event["organizer"],
            )
            created = True

        vault_writer.mark_meeting_processed(note_path.stem)

        # Attendee links are upserted BEFORE the customer link — each
        # insert lands at the very top of the body, so calling Attendees
        # first and Customer second is what puts the Customer line above
        # the Attendees line, matching the resolved schema's documented
        # order (**Customer:** ... followed by **Attendees:** ...).
        person_stems: list[str] = []
        for attendee in attendees:
            email = attendee.get("email") or ""
            if not email:
                continue
            person_result = people_extraction.ensure_person_note(attendee.get("name") or email, email)
            person_stems.append(Path(person_result["note_path"]).stem)
        if person_stems:
            vault_writer.upsert_attendee_links(note_path, person_stems)

        linked = False
        if customer:
            customer_hub_linking.ensure_customer_hub_note(customer)
            linked = customer_hub_linking.link_note_to_customer_hub(note_path, customer)

        results.append({
            "subject": event["subject"],
            "note_path": str(note_path),
            "created": created,
            "customer": customer,
            "linked": linked,
            "attendees": len(person_stems),
        })

    return results
