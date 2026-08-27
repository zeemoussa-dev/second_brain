"""Cockpit people-chip resolution (ADR-036 point 7) -- reads a subject
note's attendees/recipients frontmatter list directly, resolving each
person via people_extraction's new read-only lookup. Never creates a
Person note.

**2026-08-27 fix (operator: "Fix the People/Received field gap on
Threads")**: a real Thread's own concept note has NO `recipients`
frontmatter field at all -- confirmed live by direct reading of a real
Thread (`type, conversation_id, tags, last_message_at,
last_summarized_at, thread_name`, nothing resembling recipients) -- so
`resolve_people_chips` always returned `[]` for every email/Thread
subject. A Thread's REAL participants are recorded as wikilinks in its
own `## Related` section (the same body-wikilink convention Meeting
attendee links also use, just with no frontmatter mirror for Threads).
Scoped to JUST that section, not the whole body/`outgoing_wikilinks`,
and filtered to `type: "Person"` -- a Thread's own `## Related` section
also links Customer/Partner hubs (confirmed live: a real Thread's
Summary/Related mentions `[[Masdar]]`), which must never show up as a
"person" chip."""
from __future__ import annotations

import json
from pathlib import Path

from app.business import people_extraction, vault_indexing
from app.data_access import vault_manager as vm
from app.data_access import vault_writer

_ATTENDEE_FIELD_BY_KIND = {"meeting": "attendees", "email": "recipients"}


def _normalize_person_item(raw_item) -> dict:
    """A plain wikilink-string attendees/recipients item (BUG-027 -- the
    real, current shape meeting_classification.py's own attendee-write
    path writes today, list[str] of "[[<person-note-stem>]]", not the
    ADR-036 point 7-designed list[dict]) is normalized here to the SAME
    {"name", "email"} shape a list[dict] item already carries, so
    resolve_people_chips's own downstream loop needs no per-item type
    branching. Strips [[...]] via vault_writer.WIKILINK_PATTERN (the
    same regex upsert_attendee_links already uses) to recover the
    wikilink's stem, then resolves it via vault_indexing.get_index()
    (the SAME stem-keyed lookup resolve_people_chips already performs
    for the subject note itself) -- a found entry's real name/email
    frontmatter (create_person_note_baseline's own written values,
    never fabricated). An unresolved stem (no matching vault entry) or
    a malformed item returns {} -- deliberately falls through to the
    existing "no note yet" chip shape below; NEVER calls
    ensure_person_note (ADR-036 point 7's read-only contract,
    unchanged). A dict item (the originally-designed shape) passes
    through unmodified -- this function only handles the plain-string
    case.

    Known, disclosed, narrow residual limitation (mirrors person_note_
    dedup_key's own documented one, see BUGFIX-06-US-01's own Notes):
    a resolved wikilink whose Person note has no email (a name-keyed
    dedup_key, ADR-048 Decision 6) still round-trips through
    resolve_people_chips's own downstream find_existing_person_note
    (email) re-lookup, which requires a non-empty email -- such an
    attendee renders with its real name but the non-clickable "no note
    yet" chip state, not the clickable one, even though a real Person
    note exists. Not exercised by BUG-027's own confirmed real repros
    (both email-keyed); not resolved further by this fix."""
    if not isinstance(raw_item, str):
        return raw_item
    match = vault_writer.WIKILINK_PATTERN.fullmatch(raw_item.strip())
    if match is None:
        return {}
    entry = vault_indexing.get_index().get(match.group(1))
    if entry is None:
        return {}
    frontmatter = entry["frontmatter"]
    return {"name": frontmatter.get("name"), "email": frontmatter.get("email")}


def _coerce_people_list(raw_value) -> list[dict]:
    """The attendees/recipients frontmatter value is designed (ADR-036
    point 7) as a native list[dict]. vault_writer.py's own real
    frontmatter parser (_parse_frontmatter_value) does not support a
    list-of-dicts literal today -- confirmed live: it only recognizes a
    quoted string or a list of quoted strings, so a Python dict written
    through write_note()'s own list branch round-trips back as an empty
    list, silently losing the data. A caller that writes this field must
    therefore JSON-encode it as a single quoted string for it to survive
    a read_note() round trip. Accepts both shapes so this function works
    correctly today (JSON string) and remains forward-compatible if a
    future vault_writer.py change ever adds real list-of-dicts support
    (a real list, used as-is).

    A THIRD real shape (BUG-027, confirmed by direct reading of
    meeting_classification.py's own current, live attendee-write path)
    is also handled here: a plain Python list[str] of wikilinks
    (["[[stem]]", ...]) -- the shape Meeting attendees actually ships
    as today, never list[dict]. Every item is passed through
    _normalize_person_item, which normalizes a plain wikilink string to
    a {"name", "email"} dict (or {} if unresolvable) and passes a dict
    item through unchanged -- so this function's own return contract
    (list[dict]) holds for all three input shapes."""
    if isinstance(raw_value, str):
        try:
            people = json.loads(raw_value) or []
        except (json.JSONDecodeError, ValueError):
            return []
    else:
        people = raw_value or []
    return [_normalize_person_item(item) for item in people]


def _related_section_people(path: str) -> list[dict]:
    """A Thread's own real participants -- wikilinks in `## Related`,
    never a `recipients` frontmatter field (see module docstring). Scoped
    to that ONE section (via vault_manager's own read-only
    `get_section_content`, reused rather than a second body-wikilink
    parser) so a Customer/Partner hub mentioned in `## Summary` prose is
    never swept in; `type: "Person"` is a second, belt-and-suspenders
    filter for the same reason, since `## Related` itself can also link
    a Company."""
    section_text = vm.get_section_content(Path(path), "Related")
    people = []
    for target in vault_writer.extract_wikilink_targets(section_text):
        entry = vault_indexing.get_index().get(target)
        if entry is None or entry["frontmatter"].get("type") != "Person":
            continue
        people.append({"name": entry["frontmatter"].get("name"), "email": entry["frontmatter"].get("email")})
    return people


def resolve_people_chips(subject_kind: str, subject_note_stem: str) -> list[dict]:
    entry = vault_indexing.get_index().get(subject_note_stem)
    if entry is None:
        return []
    if subject_kind == "email":
        people = _related_section_people(entry["path"])
    else:
        field = _ATTENDEE_FIELD_BY_KIND.get(subject_kind, "attendees")
        people = _coerce_people_list(entry["frontmatter"].get(field))
    chips = []
    for person in people:
        existing = people_extraction.find_existing_person_note(person.get("email", ""))
        chips.append({
            "name": person.get("name") or person.get("email") or "Unknown",
            "email": person.get("email"),
            "has_note": existing is not None,
            "note_path": existing["note_path"] if existing else None,
        })
    return chips
