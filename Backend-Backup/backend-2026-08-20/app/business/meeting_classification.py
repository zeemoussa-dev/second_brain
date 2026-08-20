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
from datetime import datetime
from pathlib import Path

from app.business import (
    agent_prompts,
    customer_hub_linking,
    meeting_thread_link_config,
    people_extraction,
    project_customer_synthesizer,
)
from app.config import settings
from app.data_access import compass_client, outlook_com, vault_writer


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


def _link_to_thread_by_conversation_id(event: dict, note_path: Path) -> bool:
    """`Link-to-Thread` Job's primary strategy (REQ-SB-56-US-01 Scenario
    1): if this event's own conversation_id is non-empty AND an
    already-existing Thread note carries that exact conversation_id,
    writes it into the Meeting note's own `thread` frontmatter field and
    reports a link was made. Never creates a Thread note itself — false-
    positive links are worse than no link (the story's own Constraint) —
    so a non-empty conversation_id with no matching Thread, or an empty/
    absent one (including the ESC-040 recurring-occurrence fraction
    outlook_com.list_calendar_events already resolves safely to ""),
    simply leaves `thread` at its reserved empty string, falling through
    to T02's own fallback strategy untouched.

    Existence check via resolve_thread_note_path() (BUG-019, found live
    during REQ-SB-69-US-01-T06's own verification), not the retired
    thread_note_exists()/thread_note_path() pair (ADR-042 point 5,
    superseded by ADR-046 Decision 7) -- a Thread's real, current file no
    longer lives at the conversation_id-derived path those two check once
    its filename is human-readable/renamable, so thread_note_exists()
    silently returns False for every genuinely-existing post-ADR-046
    Thread, permanently starving this primary strategy in favor of T02's
    own weaker date-proximity fallback."""
    conversation_id = event.get("conversation_id") or ""
    if not conversation_id or vault_writer.resolve_thread_note_path(conversation_id) is None:
        return False
    vault_writer.upsert_frontmatter_key(note_path, "thread", conversation_id)
    return True


def _exclude_self_from_participant_emails(participants: list[str]) -> list[str]:
    """Mirrors _exclude_self exactly, applied to a Thread's own
    `participants` field — a plain list of sender email strings
    (email_classification.thread_match_merge's own shape), not the
    {"name","email"} dict pairs _exclude_self itself expects, so a small
    local equivalent is used here instead of reusing _exclude_self
    directly (this task's own Constraint)."""
    self_email = settings.self_email.lower()
    return [p for p in participants if (p or "").lower() != self_email]


def _date_proximity_gap_days(meeting_start: str, thread_last_message_at: str) -> int | None:
    """Absolute calendar-day gap between a meeting's own `start` (an
    Outlook-COM-stringified timestamp, e.g. "2026-08-10 10:00:00+00:00")
    and a candidate Thread's own `last_message_at` (an ISO-8601 string) —
    parses only the leading 'YYYY-MM-DD' date prefix, mirroring this
    codebase's own established date_value[:10] string-slicing precedent
    (my_day.py's _within_window), but computes a real day-count
    difference via datetime.strptime rather than a window-boundary string
    compare, since the fallback's own tie-break (Scenario 3/4) needs an
    actual gap magnitude, not just an in/out-of-window boolean. Returns
    None if either prefix fails to parse as a real calendar date — treated
    by the caller as not clearing the proximity bar, never a crash."""
    try:
        meeting_date = datetime.strptime(meeting_start[:10], "%Y-%m-%d").date()
        thread_date = datetime.strptime(thread_last_message_at[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None
    return abs((meeting_date - thread_date).days)


def _attendee_overlap_bar_clears(meeting_emails: set[str], thread_emails: set[str]) -> bool:
    """Both clauses of the overlap bar (REQ-SB-56-US-01 Scenario 2), read
    fresh from meeting_thread_link_config's own get_* functions on every
    call — never a hardcoded literal (explicit operator instruction,
    2026-08-17): clears at >= the configured floor shared attendees, OR
    at exactly 1 shared attendee that is the entirety of the smaller of
    the two sets, when the 1:1 carve-out is enabled."""
    overlap_count = len(meeting_emails & thread_emails)
    if overlap_count >= meeting_thread_link_config.get_attendee_overlap_floor():
        return True
    if (
        meeting_thread_link_config.get_one_on_one_carve_out_enabled()
        and overlap_count == 1
        and min(len(meeting_emails), len(thread_emails)) == 1
    ):
        return True
    return False


def _link_to_thread_by_fallback_heuristic(event: dict, self_excluded_attendees: list[dict]) -> str | None:
    """`Link-to-Thread` Job's fallback strategy (REQ-SB-56-US-01 Scenario
    2/3) — tried ONLY when the primary conversation_id-match strategy
    (above) did not link. Scans every candidate Thread note
    (vault_writer.list_thread_notes()); a Thread missing either
    `participants` or `last_message_at` entirely is skipped outright, never
    treated as a zero-overlap non-match that could still win a tie. Both
    the attendee-overlap bar and the date-proximity bar (within the
    configured day window of the Thread's own last_message_at, inclusive,
    either direction) must clear (AND) for a candidate to qualify — false-
    positive links are worse than no link (the story's own Constraint), so
    either bar failing excludes that candidate entirely. Multiple
    qualifying candidates tie-break by higher overlap count, then smaller
    date gap; a tie surviving both leaves the meeting unlinked (Scenario 3),
    never an arbitrary pick. Returns the winning Thread's own
    conversation_id, or None."""
    meeting_emails = {
        (attendee.get("email") or "").lower()
        for attendee in self_excluded_attendees
        if attendee.get("email")
    }
    if not meeting_emails:
        return None

    best_conversation_id: str | None = None
    best_overlap_count = -1
    best_date_gap: int | None = None
    tie_survives = False

    for thread_path in vault_writer.list_thread_notes():
        frontmatter, _ = vault_writer.read_note(thread_path)
        if "participants" not in frontmatter or "last_message_at" not in frontmatter:
            continue

        thread_emails = {
            email.lower()
            for email in _exclude_self_from_participant_emails(frontmatter.get("participants") or [])
            if email
        }
        if not thread_emails:
            continue

        if not _attendee_overlap_bar_clears(meeting_emails, thread_emails):
            continue

        date_gap = _date_proximity_gap_days(event.get("start") or "", frontmatter.get("last_message_at") or "")
        if date_gap is None or date_gap > meeting_thread_link_config.get_date_proximity_days():
            continue

        overlap_count = len(meeting_emails & thread_emails)

        if overlap_count > best_overlap_count:
            best_conversation_id = frontmatter.get("conversation_id")
            best_overlap_count = overlap_count
            best_date_gap = date_gap
            tie_survives = False
        elif overlap_count == best_overlap_count:
            if date_gap < best_date_gap:
                best_conversation_id = frontmatter.get("conversation_id")
                best_date_gap = date_gap
                tie_survives = False
            elif date_gap == best_date_gap:
                tie_survives = True

    if best_conversation_id is None or tie_survives:
        return None
    return best_conversation_id


def _trigger_project_resynthesis(conversation_id: str) -> None:
    """The THIRD, and last, real evidence-change trigger (REQ-SB-57-US-01-
    AC-06) -- fires immediately after a Meeting successfully links to a
    Thread. Resolves that Thread's own current path and calls the SAME
    shared `resync_project_from_thread` helper T01's Thread-pipeline node
    calls, so a Meeting link-in resynthesizes its linked Thread's own
    Project exactly the same way a Thread update does. Never assembles or
    writes Glimpse/log.md content itself -- only calls through the shared
    helper (REQ-SB-54 point 7's ownership rule).

    Wrapped in a broad, honest non-crashing try/except, mirroring
    consult_librarian's own posture -- one Synthesizer failure must never
    abort the rest of a classify_recent_meetings run for every other
    meeting in the same batch."""
    try:
        thread_path = vault_writer.resolve_thread_note_path(conversation_id)
        if thread_path is not None:
            project_customer_synthesizer.resync_project_from_thread(thread_path)
    except Exception:
        pass


# REQ-SB-71-US-03-T01's own new Compass call site must ALWAYS pass a
# non-None prompt_override into compass_client.summarize_content (mirrors
# _THREAD_SUMMARY_SYNTHESIS_DEFAULT_INSTRUCTIONS'/_THREAD_FULL_
# RECONSTRUCTION_DEFAULT_INSTRUCTIONS' own established contract in
# email_classification.py) -- summarize_content's own generic built-in
# default instructions do not know about this Job's own calendar-
# logistics-only grounding (subject/time/location/organizer/attendees;
# no transcript or notes content exists yet at capture time).
_MEETING_SUMMARY_SYNTHESIS_DEFAULT_INSTRUCTIONS = (
    "You are synthesizing a concise summary of a calendar meeting for a "
    "personal knowledge base, from its own real logistics only (subject, "
    "time, location, organizer, customer, attendees) -- no transcript or "
    "notes content is available yet. Respond with a single JSON object: "
    "{\"summary\": <string>}. Base the summary strictly on the real "
    "logistics given below -- never invent, generalize, or pad with "
    "placeholder content.\n\n"
)

# REQ-SB-71-US-03-T02's own new Compass call site -- the per-occurrence
# ## History entry, grounded in calendar logistics AND, when linked, the
# Thread's own current ## Summary (read via read_body_section, never a
# second, divergent Thread-summarization call).
_MEETING_HISTORY_SYNTHESIS_DEFAULT_INSTRUCTIONS = (
    "You are synthesizing ONE dated diary-style History entry for a "
    "personal knowledge base, covering a SINGLE real occurrence of a "
    "meeting, from that occurrence's own calendar logistics and -- when "
    "present -- its linked email Thread's own current summary of what "
    "was discussed. Respond with a single JSON object: {\"summary\": "
    "<string>}, a short, real paragraph. Base the entry strictly on the "
    "real content given below -- never invent, generalize, pad with "
    "placeholder content, or fabricate a Thread reference when none is "
    "linked.\n\n"
)


def _format_attendees_for_synthesis(attendees: list[dict]) -> str:
    names = [attendee.get("name") or attendee.get("email") or "" for attendee in attendees]
    return ", ".join(name for name in names if name) or "(none)"


def _synthesize_meeting_summary(event: dict, customer: str | None, attendees: list[dict]) -> dict:
    """T01's own real, new Compass call (ADR-048 Decision 5) -- mirrors
    email_classification._synthesize_thread_summary's/synthesize_thread's
    own verbatim reuse of compass_client.summarize_content. Grounded
    ENTIRELY in the occurrence's own calendar logistics (subject/start/
    end/location/organizer/customer/attendees) -- the linked-Thread half
    of Meeting synthesis is `## History`'s own job (T02), not `##
    Summary`'s. Honest, non-fabricating failure posture mirroring
    summarize_attachment's/_synthesize_thread_summary's own
    "summary_error" pattern: compass_client.CompassError is caught
    locally; on failure this returns {"summary_error": str} instead of
    {"summary": ...} -- never raises, so the caller leaves the note's
    existing ## Summary untouched rather than writing a fabricated or
    partial result."""
    content = (
        f"Subject: {event['subject']}\n"
        f"Start: {event['start']}\nEnd: {event['end']}\n"
        f"Location: {event['location']}\nOrganizer: {event['organizer']}\n"
        f"Customer: {customer or '(none derived)'}\n"
        f"Attendees: {_format_attendees_for_synthesis(attendees)}"
    )
    try:
        return compass_client.summarize_content(
            content, "Meeting logistics synthesis",
            prompt_override=(
                agent_prompts.get_prompt("classify_recent_meetings")
                or _MEETING_SUMMARY_SYNTHESIS_DEFAULT_INSTRUCTIONS
            ),
        )
    except compass_client.CompassError as exc:
        return {"summary_error": f"Meeting summary synthesis failed: {exc}"}


def _synthesize_history_entry(
    event: dict, customer: str | None, attendees: list[dict], linked_conversation_id: str | None,
) -> dict:
    """T02's own real, new Compass call (ADR-048 Decision 5) -- reads the
    linked Thread's own CURRENT `## Summary` via read_body_section against
    `resolve_thread_note_path(...)` (retargeted `REQ-SB-72-US-01-T02`,
    `ADR-049` Decision 1 -- was a direct `thread_directory_paths(...)
    ["concept"]` existence check, which silently resolves to the WRONG,
    stale, since-renamed path once a linked Thread's own directory has
    been renamed, `T03`'s own Rename Job) -- never triggers a second,
    independent Thread-summarization call. When no Thread is linked, the
    entry is synthesized honestly from calendar logistics alone -- never
    blocked, never fabricated. Same honest "summary_error" non-fabricating
    failure posture as _synthesize_meeting_summary."""
    content_sections = [
        "Occurrence logistics:\n"
        f"Subject: {event['subject']}\nStart: {event['start']}\nEnd: {event['end']}\n"
        f"Location: {event['location']}\nOrganizer: {event['organizer']}\n"
        f"Customer: {customer or '(none derived)'}\n"
        f"Attendees: {_format_attendees_for_synthesis(attendees)}"
    ]
    if linked_conversation_id:
        thread_concept_path = vault_writer.resolve_thread_note_path(linked_conversation_id)
        thread_summary = (
            vault_writer.read_body_section(thread_concept_path, "## Summary")
            if thread_concept_path is not None else ""
        )
        content_sections.append(
            "Linked email Thread's own current Summary (may be empty if "
            "not yet synthesized):\n" + (thread_summary or "(empty)")
        )
    else:
        content_sections.append("No email Thread is linked to this occurrence.")
    content = "\n\n".join(content_sections)
    try:
        return compass_client.summarize_content(
            content, "Meeting occurrence History-entry synthesis",
            prompt_override=(
                agent_prompts.get_prompt("meeting_history_synthesis")
                or _MEETING_HISTORY_SYNTHESIS_DEFAULT_INSTRUCTIONS
            ),
        )
    except compass_client.CompassError as exc:
        return {"summary_error": f"Meeting History-entry synthesis failed: {exc}"}


def _append_history_entry_if_new_occurrence(
    note_path: Path, event: dict, customer: str | None, attendees: list[dict],
    linked_conversation_id: str | None,
) -> bool:
    """Content-based per-occurrence idempotency (T02) -- mirrors this
    module's/codebase's own established "no separate hidden state file,
    check the note's own real content" precedent (insert_body_line_if_
    missing, upsert_attendee_links): the dated marker
    (vault_writer.format_human_readable_datetime(event["start"]), unique
    per real occurrence -- two distinct occurrences of the same series
    cannot share an identical exact start moment, meeting_note_filename_
    stem's own ADR-019 reasoning applied here) is checked against the
    note's own CURRENT `## History` region before appending. A one-time
    meeting (captured once, ever, at a fixed start) therefore ends up
    with exactly one entry no matter how many times classify_recent_
    meetings reruns against the same in-window event; a recurring series
    accumulates one new entry per genuinely distinct occurrence. Returns
    True if a new entry was appended, False on a genuine rerun no-op OR
    an honest synthesis failure (never appends a fabricated/error
    placeholder entry)."""
    date_marker = vault_writer.format_human_readable_datetime(event["start"])
    marker = f"**{date_marker}**"
    existing_history = vault_writer.read_body_section(note_path, "## History")
    if marker in existing_history:
        return False
    synthesis = _synthesize_history_entry(event, customer, attendees, linked_conversation_id)
    if "summary" not in synthesis:
        return False
    vault_writer.append_body_section_line(note_path, "## History", f"{marker} — {synthesis['summary']}")
    return True


def classify_recent_meetings(days_back: int = 7, days_ahead: int = 14, limit: int = 50) -> list[dict]:
    """The shared "ensure this calendar event's Meeting note exists and is
    up to date" operation — called once per fetched event, every run.
    Deliberately does not gate on load_processed_meeting_ids as a skip
    check (see this module's own module-level note below on why) —
    meeting_note_exists()'s deterministic-filename check (one-time) /
    the series concept file's own existence (recurring) is what prevents
    duplicate notes (Scenario 2, 7, 9); every in-window event still flows
    through the idempotent top-up path on every rerun (Scenario 2, 6).
    mark_meeting_processed is still called every run as an audit record.

    Rewritten in place (REQ-SB-71-US-03-T01/T02/T03, ADR-048 Decisions 5-6)
    for the new shape: one-time stays the unchanged filename scheme;
    recurring becomes ONE ongoing note per series
    (meeting_series_directory_paths, keyed by GlobalAppointmentID);
    frontmatter is logistics-only, raw invite boilerplate dropped
    entirely; `## Summary` regenerates from calendar logistics via the
    allow-list-checked replace_body_section; a new, dated `## History`
    entry is appended per real occurrence, synthesized from calendar
    logistics plus, when linked, the Thread's own current Summary; every
    attendee (email-resolvable or not) reaches ensure_person_note, nested
    under the meeting's own derived Customer when they have no email
    domain of their own to derive one from."""
    events = outlook_com.list_calendar_events(days_back=days_back, days_ahead=days_ahead, limit=limit)
    results: list[dict] = []

    for event in events:
        attendees = _exclude_self(event["attendees"])
        customer = _derive_meeting_customer(attendees)
        is_recurring = bool(event.get("is_recurring")) and bool(event.get("series_id"))

        if is_recurring:
            note_path = vault_writer.meeting_series_directory_paths(event["series_id"])["concept"]
            already_existed = note_path.exists()
            calendar_id = event["series_id"]
        else:
            resolved_path, already_existed = vault_writer.resolve_meeting_note_path(
                event["subject"], event["start"], event["id"],
            )
            note_path = Path(resolved_path)
            calendar_id = event["id"]

        if already_existed:
            vault_writer.ensure_meeting_note_baseline_frontmatter(
                note_path, customer, event["organizer"], event["teams_link"], event["dial_in"],
                is_recurring, calendar_id,
            )
            created = False
        else:
            vault_writer.create_meeting_note_baseline(
                note_path, customer, event["organizer"], event["teams_link"], event["dial_in"],
                is_recurring, calendar_id,
            )
            created = True

        vault_writer.mark_meeting_processed(note_path.stem)

        # Attendee links are upserted BEFORE the customer link — each
        # insert lands at the very top of the body, so calling Attendees
        # first and Customer second is what puts the Customer line above
        # the Attendees line, matching the resolved schema's documented
        # order (**Customer:** ... followed by **Attendees:** ...).
        #
        # No attendee is skipped for lack of an email address (REQ-SB-71-
        # US-03-T03, ADR-048 Decision 6, closing the real `if not email:
        # continue` gap this module's own prior version had here) — every
        # attendee reaches ensure_person_note, with the meeting's own
        # derived customer threaded through as the ONLY Customer signal
        # available for one with no email domain of their own.
        person_stems: list[str] = []
        for attendee in attendees:
            email = attendee.get("email") or ""
            name = attendee.get("name") or email or "Unknown Attendee"
            person_result = people_extraction.ensure_person_note(name, email or None, customer=customer)
            person_stems.append(Path(person_result["note_path"]).stem)
        if person_stems:
            vault_writer.upsert_attendee_links(note_path, person_stems)
            existing_frontmatter, _ = vault_writer.read_note(note_path)
            merged_wikilinks = list(existing_frontmatter.get("attendees") or [])
            for stem in person_stems:
                wikilink = f"[[{stem}]]"
                if wikilink not in merged_wikilinks:
                    merged_wikilinks.append(wikilink)
            vault_writer.upsert_frontmatter_key(note_path, "attendees", merged_wikilinks)

        linked = False
        if customer:
            customer_hub_linking.ensure_customer_hub_note(customer)
            linked = customer_hub_linking.link_note_to_customer_hub(note_path, customer)

        thread_linked = _link_to_thread_by_conversation_id(event, note_path)
        linked_conversation_id = (event.get("conversation_id") or "") if thread_linked else None
        if not thread_linked:
            fallback_conversation_id = _link_to_thread_by_fallback_heuristic(event, attendees)
            if fallback_conversation_id:
                vault_writer.upsert_frontmatter_key(note_path, "thread", fallback_conversation_id)
                thread_linked = True
                linked_conversation_id = fallback_conversation_id

        if thread_linked and linked_conversation_id:
            _trigger_project_resynthesis(linked_conversation_id)

        summary_synthesis = _synthesize_meeting_summary(event, customer, attendees)
        summary_error = summary_synthesis.get("summary_error")
        if "summary" in summary_synthesis:
            vault_writer.replace_body_section(
                note_path, "## Summary", summary_synthesis["summary"],
                caller="meeting_classification.classify_recent_meetings",
            )

        history_appended = _append_history_entry_if_new_occurrence(
            note_path, event, customer, attendees,
            linked_conversation_id if thread_linked else None,
        )

        result = {
            "subject": event["subject"],
            "note_path": str(note_path),
            "created": created,
            "customer": customer,
            "linked": linked,
            "attendees": len(person_stems),
            "thread_linked": thread_linked,
            "history_appended": history_appended,
        }
        if summary_error is not None:
            result["summary_error"] = summary_error
        results.append(result)

    return results
