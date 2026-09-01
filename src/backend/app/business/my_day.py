"""Read-only My Day aggregation (REQ-SB-12-US-02, extended by
REQ-SB-22-US-01 for rolling 7-day window date-filtering) — projects
captured Email/Meeting notes down to the fields My Day's dashboard and
drill-down pages need. No writes; api -> business -> data_access
layering (ADR-003).

Emails/Calendar read via `vault_indexing.get_index()` (2026-08-24 fix),
NOT `vault_writer.list_notes_in_kind_folder()` — confirmed live against
the real vault: `list_notes_in_kind_folder` is a flat, non-recursive
`glob("*.md")` (data_access/vault_writer.py), so it silently sees zero
of the real, dated Meeting occurrences (`Work/Meetings/<series_id>/
occurrences/*.md` — only the top-level, undated series-container note)
and zero of the real Thread notes (which moved to `Work/Threads/
<thread>/<thread>.md` once the Threads Builder pipeline replaced the
old flat `Work/Emails/` model this module was originally written
against — that folder no longer exists). `vault_indexing.get_index()`
already walks `list_all_note_paths()`, the SAME bounded-recursive scan
ADR-048 introduced for this exact "nested note kind" blind spot
elsewhere — reusing it here closes the same gap rather than
re-deriving a second recursive walk."""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from app.business.core.pipelines.pipeline_manager import PipelineManager
from app.business.core.vault.vault_manager import VaultManager
from app.business.hermes.client import get_client
from app.data_access import vault_writer

_vault_manager = VaultManager()
_pipeline_manager = PipelineManager()

# The two real Pipelines whose own cron job actually populates My Day's
# Emails/Calendar cards -- REQ-SB-?? manual-refresh button (operator,
# 2026-09-02: "I need a button to refresh the emails and meetings in the
# backend ... the Option to pull stuff manually", found live the same day
# the real Hermes gateway had been down, silently stalling every
# recurring job including these two).
_REFRESH_PIPELINE_IDS = ["threads-builder", "meeting-builder"]

_WINDOW_DAYS_BEFORE = 3
_WINDOW_DAYS_AFTER = 3


def _customer_or_null(frontmatter: dict) -> str | None:
    """Mirrors list_known_customers()'s existing truthiness convention for
    "not really classified" (2026-08-20: an empty `customer` field, not a
    written "Unsorted" placeholder — MEMORY.md) rather than inventing a
    second one; the frontend renders None as "unclassified"."""
    customer = frontmatter.get("customer")
    if not customer:
        return None
    return customer


def customer_name_by_tag() -> dict[str, str]:
    """`customer/<slug>` tag -> the real Customer/Partner hub note's own
    `name` field (e.g. "customer/adnoc" -> "Adnoc") — resolved from the
    ALREADY-real, already-indexed hub note rather than reconstructing a
    display name by reversing the slug (title-casing "al-ain" back to
    "Al Ain" is not always correct; the hub note's own `name` always is).
    Built fresh from the live index on every call, matching this
    module's existing no-caching convention (index rebuilds are cheap
    and already handled by vault_indexing's own trigger). Public (2026-08-27)
    -- `cockpit_router.py`'s own Inbox Cockpit info panel reuses this same
    pairing (a Thread's own frontmatter has no `customer` field at all,
    only the tag) rather than a second reimplementation."""
    mapping: dict[str, str] = {}
    for entry in _vault_manager.get_index().values():
        if entry["frontmatter"].get("type") not in ("Customer", "Partner"):
            continue
        name = entry["frontmatter"].get("name")
        if not name:
            continue
        for tag in entry["tags"]:
            mapping.setdefault(tag, name)
    return mapping


def customer_from_tags(tags: list[str], lookup: dict[str, str]) -> str | None:
    """Real bug, found live 2026-08-27: `lookup` (customer_name_by_tag())
    intentionally merges BOTH Customer and Partner hub notes' own tags
    into one dict, so a real Thread tagged `["partner/g42",
    "customer/mubadala"]` used to return "G42" -- whichever tag happened
    to appear first in the caller's own list, with no namespace check at
    all. Every real caller (this module's own Emails/Calendar
    projections, cockpit_router.py's Inbox Cockpit info panel) wants
    specifically THE Customer, never a Partner -- filtering to
    `customer/`-prefixed tags here fixes every one of them at once,
    matching the same filter moderator.py's own (separately correct)
    `_subject_customer` already applies."""
    for tag in tags:
        if tag.startswith("customer/") and tag in lookup:
            return lookup[tag]
    return None


def _latest_sender_by_conversation() -> dict[str, str]:
    """conversation_id -> the sender of that Thread's own most recent
    RawMessage — a Thread note itself has no single "sender" (it's a
    distilled summary of a whole conversation, potentially many senders),
    but My Day's own existing UI contract (MyDayEmailsPage.tsx's "from
    {sender}") expects one, so this surfaces the most RECENT real
    sender as a reasonable, honest best-effort answer rather than
    fabricating one or leaving the field permanently blank."""
    latest: dict[str, tuple[str, str]] = {}
    for entry in _vault_manager.get_index().values():
        frontmatter = entry["frontmatter"]
        if frontmatter.get("type") != "RawMessage":
            continue
        conversation_id = frontmatter.get("conversation_id")
        if not conversation_id:
            continue
        received = frontmatter.get("received", "")
        current = latest.get(conversation_id)
        if current is None or received > current[0]:
            latest[conversation_id] = (received, frontmatter.get("sender", ""))
    return {conversation_id: sender for conversation_id, (_, sender) in latest.items()}


def _meeting_series_lookup() -> dict[str, dict]:
    """Series-folder name -> that series' own top-level Meeting note's
    frontmatter — a real, dated Meeting OCCURRENCE note (`Work/Meetings/
    <series>/occurrences/*.md`) carries none of its own series'
    `customer`/tags (confirmed live: a real occurrence's own frontmatter
    is logistics-only — start/end/location/organizer/attendees — with
    no customer tag at all), while the series' own top-level note
    (`Work/Meetings/<series>/<series>.md`) DOES. Keyed by the series
    note's own real stem, which is exactly the occurrence's own parent
    folder name on disk (`_series_folder_name_for` below) — this is a
    structural filesystem relationship, not a shared id field, since the
    series folder name is a truncated prefix of the full
    `calendar_series_id` frontmatter value, not an exact match to it."""
    lookup: dict[str, dict] = {}
    for entry in _vault_manager.get_index().values():
        frontmatter = entry["frontmatter"]
        if frontmatter.get("type") != "Meeting" or frontmatter.get("start"):
            continue  # only the undated series-container note, never an occurrence
        lookup[entry["stem"]] = frontmatter
    return lookup


def _series_folder_name_for(path_str: str) -> str:
    return Path(path_str).parent.parent.name


def compute_window() -> tuple[str, str]:
    """Returns (window_start, window_end) as 'YYYY-MM-DD' strings, 3 days
    before through 3 days after the app/server host's current local
    calendar date (REQ-SB-22-US-01 Scenario 4/AC-04). Called fresh on
    every list_email_items()/list_calendar_items() invocation — never
    memoized at module or process level — so the window advances
    automatically as real days pass, and so a live verification pass can
    observe the window shift by monkeypatching this module's `datetime`
    reference rather than waiting for a real day to pass."""
    today = datetime.now().date()
    window_start = today - timedelta(days=_WINDOW_DAYS_BEFORE)
    window_end = today + timedelta(days=_WINDOW_DAYS_AFTER)
    return window_start.isoformat(), window_end.isoformat()


def _within_window(date_value: str, window_start: str, window_end: str) -> bool:
    """String-compares the note's ISO-8601 date prefix (first 10 chars,
    'YYYY-MM-DD') against the window bounds — ISO date strings sort and
    compare correctly as plain strings, the same received[:10]/start[:10]
    slicing precedent already used in email_classification.py and
    vault_writer.meeting_note_filename_stem(). No datetime.fromisoformat()
    parsing or timezone conversion is introduced. A missing/empty date
    value is treated as outside the window (excluded), not a crash."""
    if not date_value:
        return False
    date_prefix = date_value[:10]
    return window_start <= date_prefix <= window_end


def _resolve_day_bounds(day: str | None) -> tuple[str, str]:
    """Resolves the (start, end) date-string bounds a list function should
    filter against: the full 7-day window when `day` is None (existing
    REQ-SB-22-US-01 behavior, unchanged), or that single day (start == end
    == day) when a specific day is requested for the new day-navigator.
    `day` is trusted to already be a real 'YYYY-MM-DD' string within the
    current window — the router validates that, this function does not
    re-derive "today" or re-clamp, so a fresh call always reflects
    whatever the caller asked for."""
    if day is None:
        return compute_window()
    return day, day


def list_email_items(day: str | None = None) -> list[dict]:
    """[{"subject", "sender", "customer", "received", "stem"}] for real
    Thread notes (`type: "Thread"`, `Work/Threads/<thread>/<thread>.md`)
    whose `last_message_at` falls inside the current 7-day window
    (Scenarios 1, 3, 5), or inside just `day` when provided (the My Day
    day-navigator). "subject"/"received" are this projection's own
    stable field names, kept unchanged for the frontend even though the
    real underlying Thread fields are `thread_name`/`last_message_at` —
    `Work/Emails/` (this function's original 2026-08-07 data source) no
    longer exists; email capture moved to the Threads Builder pipeline
    (2026-08-21) and this projection was never updated to follow it
    (2026-08-24 fix, see module docstring). "sender" is a best-effort
    "most recent real sender on this conversation" (`_latest_sender_by_
    conversation`), since a Thread itself has no single sender of its
    own. `stem` (REQ-SB-44-US-01-T02) mirrors `list_calendar_items`'s
    own `"stem"` field exactly — the note identity the Inbox Cockpit
    route needs."""
    range_start, range_end = _resolve_day_bounds(day)
    customer_lookup = customer_name_by_tag()
    sender_lookup = _latest_sender_by_conversation()
    items = []
    for entry in _vault_manager.get_index().values():
        frontmatter = entry["frontmatter"]
        if frontmatter.get("type") != "Thread":
            continue
        received = frontmatter.get("last_message_at", "")
        if not _within_window(received, range_start, range_end):
            continue
        items.append({
            "subject": frontmatter.get("thread_name", ""),
            "sender": sender_lookup.get(frontmatter.get("conversation_id"), ""),
            "customer": customer_from_tags(entry["tags"], customer_lookup),
            "received": received,
            "stem": entry["stem"],
        })
    items.sort(key=lambda item: item["received"])
    return items


def list_calendar_items(day: str | None = None) -> list[dict]:
    """[{"subject", "start", "customer"}] for real, dated Meeting
    OCCURRENCE notes (`Work/Meetings/<series>/occurrences/*.md` —
    `type: "Meeting"` with a real `start`; the series' own top-level
    note is `type: "Meeting"` too but carries no `start` of its own, so
    it's excluded here, never double-counted) whose `start` falls inside
    the current 7-day window (Scenarios 2, 3, 5), or inside just `day`
    when provided. Response shape unchanged from REQ-SB-12-US-02.
    `customer` is inherited from the occurrence's own parent series note
    (`_meeting_series_lookup`) — confirmed live that a real occurrence's
    own frontmatter carries no customer tag of its own at all, only the
    series-level note does (2026-08-24 fix, see module docstring)."""
    range_start, range_end = _resolve_day_bounds(day)
    customer_lookup = customer_name_by_tag()
    series_lookup = _meeting_series_lookup()
    items = []
    for entry in _vault_manager.get_index().values():
        frontmatter = entry["frontmatter"]
        if frontmatter.get("type") != "Meeting":
            continue
        start = frontmatter.get("start", "")
        if not start:
            continue  # the series-container note itself, not a real occurrence
        if not _within_window(start, range_start, range_end):
            continue
        series = series_lookup.get(_series_folder_name_for(entry["path"])) or {}
        customer = customer_from_tags(entry["tags"], customer_lookup) or customer_from_tags(
            series.get("tags") or [], customer_lookup
        )
        items.append({
            "subject": frontmatter.get("subject") or series.get("subject") or entry["stem"],
            "start": start,
            "customer": customer,
            "stem": entry["stem"],
        })
    items.sort(key=lambda item: item["start"])
    return items


def list_todo_items() -> list[dict]:
    """[{"subject", "customer", "due"}] for notes under Work/Tasks/
    whose status is still open (Scenario 8's own "still-open" text) —
    "status" == "Completed" is excluded, not deleted; a completed
    task is still a real, captured Task note (Scenario 5), it is
    simply outside this particular read projection, the same
    "captured but filtered" shape REQ-SB-30-US-01's `important`
    filter already established for Emails. No date-window
    filtering is applied — unlike list_email_items/
    list_calendar_items's rolling 7-day window, a Task has no
    natural "occurred near now" framing (mirroring
    outlook_com.list_outlook_tasks's own no-date-window design,
    ADR-027); a far-future or undated task stays listed until it is
    completed, not until it ages out of a window."""
    items = []
    for path in vault_writer.list_notes_in_kind_folder("Tasks"):
        frontmatter, _ = vault_writer.read_note(path)
        if frontmatter.get("status") == "Completed":
            continue
        items.append({
            "subject": frontmatter.get("subject", ""),
            "customer": _customer_or_null(frontmatter),
            "due": frontmatter.get("due") or None,
        })
    items.sort(key=lambda item: (item["due"] is None, item["due"] or "", item["subject"]))
    return items


def trigger_refresh() -> list[dict]:
    """Manually fires the real cron job behind each of `threads-builder`/
    `meeting-builder` (operator: "the Option to pull stuff manually") --
    reuses the SAME `cron_job_id`/`cron_profile_id` fields those Pipelines
    already carry for cron-status display (`PipelineManager`/`ADR-005`),
    never a second hardcoded copy of the job names. Fire-and-forget, same
    as `HermesCLI.run_cron_job` itself -- this returns as soon as the
    trigger request is sent, not when the real capture run finishes (that
    can take a while; the caller's own next `/my-day/summary` poll will
    reflect it once it lands). A Pipeline with no `cron_job_id` configured
    is reported, not silently skipped -- the operator should see it, not
    guess why nothing happened for that card."""
    results = []
    for pipeline_id in _REFRESH_PIPELINE_IDS:
        pipeline = _pipeline_manager.get_by_id(pipeline_id)
        if pipeline is None or pipeline.cron_job_id is None:
            results.append({"pipeline_id": pipeline_id, "triggered": False, "detail": "no cron job configured"})
            continue
        triggered = get_client().cli.run_cron_job(pipeline.cron_job_id, pipeline.cron_profile_id)
        results.append({
            "pipeline_id": pipeline_id,
            "triggered": triggered,
            "detail": "triggered" if triggered else "Hermes CLI call failed",
        })
    return results


def summary(day: str | None = None) -> dict:
    """{"emails": {"count"}, "calendar": {"count"}, "todo": {"count": 0},
    "window": {"start", "end"}} — internally unchanged (still len() over
    list_email_items()/list_calendar_items()), but now naturally windowed
    since both list functions are (Scenario 5), or narrowed to just `day`
    when provided. `window` is always the full 7-day range regardless of
    `day` — it describes what the day-navigator may pick from, not what
    was just counted — so the frontend can always render the full
    available range alongside whichever single day is currently selected.
    todo.count now reflects real list_todo_items() data — unwindowed
    (unlike emails/calendar), since a Task has no natural "occurred
    near now" framing (REQ-SB-09, ADR-027)."""
    window_start, window_end = compute_window()
    return {
        "emails": {"count": len(list_email_items(day))},
        "calendar": {"count": len(list_calendar_items(day))},
        "todo": {"count": len(list_todo_items())},
        "window": {"start": window_start, "end": window_end},
    }
