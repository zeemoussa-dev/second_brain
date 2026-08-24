"""Meeting -> email Thread linking (ported from the source project's own
meeting_classification.py `Link-to-Thread` job, REQ-SB-56-US-01),
adapted to THIS vault's real Thread schema (`participant_links` wikilinks
+ `last_message_at`, not the source's own bare `participants` email-string
list). Two strategies, tried in order -- false-positive links are worse
than no link, so either strategy failing to clear its own bar leaves the
meeting unlinked, never a guess:

  1. Primary: exact match on conversation_id -- if the calendar event's
     own conversation_id is non-empty and an existing Thread carries that
     exact conversation_id, link immediately, no heuristic needed.
  2. Fallback: attendee-overlap + date-proximity heuristic -- a candidate
     Thread must clear BOTH an attendee-overlap bar (>= a configured
     floor shared attendees, OR exactly 1 shared attendee that is the
     entirety of the smaller side, when the 1:1 carve-out is enabled) AND
     a date-proximity bar (within a configured day window of the
     Thread's own last_message_at). Multiple qualifying candidates
     tie-break by higher overlap, then smaller date gap; a tie surviving
     both leaves the meeting unlinked.

Both thresholds come from meeting_thread_link_config.py -- never a
hardcoded literal.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import meeting_thread_link_config
import vault_lib

_WIKILINK_STEM_PREFIX = "[["


def _wikilink_stem(link: str) -> str:
    text = link.strip()
    if text.startswith(_WIKILINK_STEM_PREFIX) and text.endswith("]]"):
        return text[2:-2]
    return text


def _iter_thread_notes(vault_path: Path):
    threads_root = vault_path / "Work" / "Threads"
    if not threads_root.exists():
        return
    for path in sorted(threads_root.glob("*/*.md")):
        if path.is_file() and path.parent.name == path.stem:
            yield path


def _build_person_email_index(vault_path: Path) -> dict[str, str]:
    index: dict[str, str] = {}
    for path in vault_path.rglob("*.md"):
        if not path.is_file():
            continue
        frontmatter, _ = vault_lib.read_note(path)
        if frontmatter.get("type") != "Person":
            continue
        email = (frontmatter.get("email") or "").strip().lower()
        if email:
            index[path.stem.lower()] = email
    return index


def _resolve_thread_by_conversation_id(vault_path: Path, conversation_id: str) -> Path | None:
    if not conversation_id:
        return None
    for thread_path in _iter_thread_notes(vault_path):
        frontmatter, _ = vault_lib.read_note(thread_path)
        if frontmatter.get("conversation_id") == conversation_id:
            return thread_path
    return None


def _date_proximity_gap_days(meeting_start: str, thread_last_message_at: str) -> int | None:
    try:
        meeting_date = datetime.strptime(meeting_start[:10], "%Y-%m-%d").date()
        thread_date = datetime.strptime(thread_last_message_at[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None
    return abs((meeting_date - thread_date).days)


def _attendee_overlap_bar_clears(config: dict, meeting_emails: set[str], thread_emails: set[str]) -> bool:
    overlap_count = len(meeting_emails & thread_emails)
    if overlap_count >= config["attendee_overlap_floor"]:
        return True
    if (
        config["one_on_one_carve_out_enabled"]
        and overlap_count == 1
        and min(len(meeting_emails), len(thread_emails)) == 1
    ):
        return True
    return False


def _link_by_fallback_heuristic(
    vault_path: Path, event_start: str, meeting_emails: set[str], person_email_index: dict[str, str],
) -> str | None:
    if not meeting_emails:
        return None
    config = meeting_thread_link_config.load_config(vault_path)

    best_conversation_id: str | None = None
    best_overlap_count = -1
    best_date_gap: int | None = None
    tie_survives = False

    for thread_path in _iter_thread_notes(vault_path):
        frontmatter, _ = vault_lib.read_note(thread_path)
        participant_links = frontmatter.get("participant_links")
        last_message_at = frontmatter.get("last_message_at")
        if not participant_links or not last_message_at:
            continue

        thread_emails = {
            person_email_index[_wikilink_stem(link).lower()]
            for link in participant_links
            if _wikilink_stem(link).lower() in person_email_index
        }
        if not thread_emails:
            continue

        if not _attendee_overlap_bar_clears(config, meeting_emails, thread_emails):
            continue

        date_gap = _date_proximity_gap_days(event_start, last_message_at)
        if date_gap is None or date_gap > config["date_proximity_days"]:
            continue

        overlap_count = len(meeting_emails & thread_emails)
        conversation_id = frontmatter.get("conversation_id")

        if overlap_count > best_overlap_count:
            best_conversation_id, best_overlap_count, best_date_gap = conversation_id, overlap_count, date_gap
            tie_survives = False
        elif overlap_count == best_overlap_count:
            if date_gap < best_date_gap:
                best_conversation_id, best_date_gap = conversation_id, date_gap
                tie_survives = False
            elif date_gap == best_date_gap:
                tie_survives = True

    if best_conversation_id is None or tie_survives:
        return None
    return best_conversation_id


def link_meeting_to_thread(
    vault_path: Path, meeting_note_path: Path, event_conversation_id: str, event_start: str,
    attendee_emails: list[str],
) -> str | None:
    """Attempts to link meeting_note_path's own `thread` frontmatter to a
    matching Thread's conversation_id. Returns the linked conversation_id,
    or None if neither strategy found a confident match. Idempotent --
    upsert_frontmatter_key-style insert only fills the key if not already
    set, so a meeting already linked (by a prior run) is never
    reconsidered or overwritten."""
    existing_frontmatter, _ = vault_lib.read_note(meeting_note_path)
    if existing_frontmatter.get("thread"):
        return existing_frontmatter["thread"]  # already linked, never reconsidered

    thread_path = _resolve_thread_by_conversation_id(vault_path, event_conversation_id)
    if thread_path is not None:
        conversation_id = event_conversation_id
        vault_lib.upsert_frontmatter_key(meeting_note_path, "thread", conversation_id)
        return conversation_id

    person_email_index = _build_person_email_index(vault_path)
    meeting_emails = {e.lower() for e in attendee_emails if e}
    conversation_id = _link_by_fallback_heuristic(vault_path, event_start, meeting_emails, person_email_index)
    if conversation_id:
        vault_lib.upsert_frontmatter_key(meeting_note_path, "thread", conversation_id)
        return conversation_id
    return None
