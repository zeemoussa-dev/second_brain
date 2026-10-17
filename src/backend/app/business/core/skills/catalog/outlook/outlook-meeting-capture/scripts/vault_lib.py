"""Self-contained vault-writing primitives for the meeting-capture Skill
(2026-08-21). Trimmed/adapted port of Second Brain's own
app/data_access/vault_writer.py's Meeting-note primitives -- but the
folder shape itself is a deliberate DIVERGENCE from that source, per the
operator's own explicit correction: the source used a flat file for a
one-time meeting and one ever-growing note for an entire recurring
series (its own `## History` section). The operator instead wants the
same folder-per-concept shape this codebase's own Thread pipeline
already uses -- every meeting gets its own folder; a recurring series'
folder holds a real file PER OCCURRENCE (an `occurrences/` subfolder,
mirroring Threads' own `messages/` subfolder), not one section inside a
single file.

Structure:
    Work/Meetings/<date> <Subject>/
        <date> <Subject>.md          -- one-time meeting: this IS the
                                         only occurrence, no subfolder.
    Work/Meetings/<Subject>/          -- recurring: no date in the
                                         series folder name (it spans
                                         many dates).
        <Subject>.md                  -- series concept note; "## History"
                                         lists every occurrence (wikilinks
                                         down), mirroring a Thread concept
                                         note's own "## Related".
        occurrences/
            <date> <time> <Subject>.md  -- one real file per occurrence,
                                             mirrors Thread's own message
                                             filename shape exactly.

Dedup is by SCANNING existing Meeting notes' own frontmatter
(calendar_event_id / calendar_series_id), never by recomputing a path
from a raw Outlook id and assuming that path is authoritative -- the
same discipline resolve_thread_directory already established (a Thread's
own subject can be renamed later without breaking dedup; a Meeting's
folder name is fixed at creation here, but the scan-first discipline is
kept identical for consistency and because Outlook's own identity fields
for calendar items are independently known to be unreliable -- see this
Skill's own outlook_lib.py).

No third-party dependencies -- stdlib only.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import vault_manager

_SLUG_INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')
_FRONTMATTER_LINE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*):\s?(.*)$")
_LIST_ITEM_PATTERN = re.compile(r'"((?:[^"\\]|\\.)*)"')
_BODY_SECTION_HEADER_PATTERN = re.compile(r"^## .+$", re.MULTILINE)

_WORK_ROOT = "Work"
_MEETINGS_SUBFOLDER = f"{_WORK_ROOT}/Meetings"
_PEOPLE_SUBFOLDER = f"{_WORK_ROOT}/People"
_CUSTOMERS_SUBFOLDER = f"{_WORK_ROOT}/Customers"

_PERSON_IGNORE_LIST_FILE = "person_ignore_list.json"


def _load_person_ignore_list(vault_path: Path) -> set[str]:
    """2026-08-21, operator: the vault owner's own address and a
    truncation-collision-prone unresolved Exchange DN were showing up as
    Person notes/attendee links "everywhere". Real, accessible config
    (never a hardcoded literal) -- identical contract to email-thread-
    capture's own copy of this function, duplicated per this codebase's
    established per-Skill self-containment convention. Missing file ->
    empty set."""
    path = vault_manager.data_root(vault_path) / _PERSON_IGNORE_LIST_FILE
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    return {entry.strip().lower() for entry in data.get("identifiers", []) if entry.strip()}

_CALLER_ALLOW_LISTS = {
    "link_person_to_meeting.link_person_to_meeting": frozenset({"## Related"}),
    "link_occurrence_to_series.link_occurrence_to_series": frozenset({"## History"}),
}


class SectionWriteNotAllowed(PermissionError):
    pass


def _is_header_allowed(caller: str, header: str) -> bool:
    return header in _CALLER_ALLOW_LISTS.get(caller, frozenset())


# ── slugs / frontmatter formatting (identical shape to every other
# Skill's own copy in this codebase) ────────────────────────────────────

def _slugify(text: str, max_len: int = 80) -> str:
    slug = _SLUG_INVALID_CHARS.sub("-", text).strip()
    return slug[:max_len] if slug else "untitled"


def _format_frontmatter_value(value) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(_format_frontmatter_value(v) for v in value) + "]"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return str(value)


def _parse_frontmatter_value(raw: str):
    raw = raw.strip()
    if raw in ("true", "false"):
        return raw == "true"
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1]
        return [
            match.group(1).replace('\\"', '"').replace("\\\\", "\\")
            for match in _LIST_ITEM_PATTERN.finditer(inner)
        ]
    return raw


def read_note(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    frontmatter_block = text[4:end]
    body = text[end + 5:]
    frontmatter: dict = {}
    for line in frontmatter_block.splitlines():
        match = _FRONTMATTER_LINE.match(line)
        if match:
            frontmatter[match.group(1)] = _parse_frontmatter_value(match.group(2))
    return frontmatter, body


def _write_frontmatter_note(path: Path, frontmatter: dict, body: str) -> None:
    frontmatter_lines = ["---"]
    for key, value in frontmatter.items():
        frontmatter_lines.append(f"{key}: {_format_frontmatter_value(value)}")
    frontmatter_lines.append("---")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(frontmatter_lines) + "\n\n" + body, encoding="utf-8")


def insert_frontmatter_key_if_missing(path: Path, key: str, value) -> bool:
    frontmatter, _ = read_note(path)
    if key in frontmatter:
        return False
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---\n", 4)
    if end == -1:
        return False
    insertion = f"{key}: {_format_frontmatter_value(value)}\n"
    path.write_text(text[: end + 1] + insertion + text[end + 1:], encoding="utf-8")
    return True


def upsert_frontmatter_key(path: Path, key: str, value) -> bool:
    """Sets key to value regardless of whether it's already present --
    unlike insert_frontmatter_key_if_missing, this OVERWRITES an
    already-present value (needed for `thread`, which every Meeting note
    is pre-seeded with as "" at creation, so "insert only if absent"
    could never fill it in later). Returns False, no-op, if the key
    already holds this exact value."""
    frontmatter, _ = read_note(path)
    if key in frontmatter and frontmatter[key] == value:
        return False
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---\n", 4)
    if end == -1:
        return False
    frontmatter_block = text[: end + 1]
    rest = text[end + 1:]
    lines = frontmatter_block.splitlines(keepends=True)
    new_line = f"{key}: {_format_frontmatter_value(value)}\n"
    replaced = False
    for i, line in enumerate(lines):
        match = _FRONTMATTER_LINE.match(line.rstrip("\n"))
        if match and match.group(1) == key:
            lines[i] = new_line
            replaced = True
            break
    if not replaced:
        lines.insert(-1, new_line)
    path.write_text("".join(lines) + rest, encoding="utf-8")
    return True


def insert_body_line_if_missing(path: Path, line: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if line in text:
        return False
    end = text.find("\n---\n", 4)
    if end == -1:
        path.write_text(line + "\n\n" + text, encoding="utf-8")
        return True
    body_start = end + 6
    new_text = text[:body_start] + line + "\n\n" + text[body_start:]
    path.write_text(new_text, encoding="utf-8")
    return True


def insert_body_section_if_missing(path: Path, header: str) -> bool:
    text = path.read_text(encoding="utf-8")
    header_line_pattern = re.compile(r"^" + re.escape(header) + r"$", re.MULTILINE)
    if header_line_pattern.search(text) is not None:
        return False
    separator = "" if text.endswith("\n") else "\n"
    path.write_text(text + separator + f"\n{header}\n", encoding="utf-8")
    return True


def read_body_section(path: Path, header: str) -> str:
    text = path.read_text(encoding="utf-8")
    header_line_pattern = re.compile(r"^" + re.escape(header) + r"$", re.MULTILINE)
    header_match = header_line_pattern.search(text)
    if header_match is None:
        return ""
    region_start = header_match.end()
    next_header_match = _BODY_SECTION_HEADER_PATTERN.search(text, region_start)
    region_end = next_header_match.start() if next_header_match else len(text)
    return text[region_start:region_end].strip("\n")


def replace_body_section(path: Path, header: str, new_content: str, *, caller: str) -> bool:
    if not _is_header_allowed(caller, header):
        raise SectionWriteNotAllowed(f"caller {caller!r} is not allowed to write {header!r}")
    text = path.read_text(encoding="utf-8")
    header_line_pattern = re.compile(r"^" + re.escape(header) + r"$", re.MULTILINE)
    header_match = header_line_pattern.search(text)
    if header_match is None:
        return False
    region_start = header_match.end()
    next_header_match = _BODY_SECTION_HEADER_PATTERN.search(text, region_start)
    region_end = next_header_match.start() if next_header_match else len(text)
    new_text = text[:region_start] + "\n\n" + new_content.strip("\n") + "\n\n" + text[region_end:]
    path.write_text(new_text, encoding="utf-8")
    return True


# ── Meeting primitives ───────────────────────────────────────────────────

def list_meeting_concept_notes(vault_path: Path) -> list[Path]:
    """Every Meeting concept note -- one-time (<slug>/<slug>.md) and
    recurring series (<slug>/<slug>.md) alike, both match the same
    "directory name == file stem" shape Threads already use. Explicitly
    excludes anything under an `occurrences/` subfolder."""
    meetings_root = vault_path / _MEETINGS_SUBFOLDER
    if not meetings_root.exists():
        return []
    return sorted(
        path for path in meetings_root.glob("*/*.md")
        if path.parent.name == path.stem and path.is_file()
    )


def resolve_meeting_directory(vault_path: Path, calendar_id: str, is_recurring: bool) -> Path | None:
    key = "calendar_series_id" if is_recurring else "calendar_event_id"
    for path in list_meeting_concept_notes(vault_path):
        frontmatter, _ = read_note(path)
        if frontmatter.get(key) == calendar_id:
            return path.parent
    return None


def _unique_meeting_directory(vault_path: Path, base_stem: str, calendar_id: str) -> Path:
    """Picks a not-yet-existing Work/Meetings/<slug>/ directory for a
    brand-new meeting, appending a short hash-of-calendar_id suffix on a
    genuine name collision (two distinct meetings whose own base_stem
    slugifies identically) -- reserves room for the suffix BEFORE
    truncating to 80 chars (2026-08-21 lesson from rename_thread.py's own
    first, buggy collision fix: appending a suffix AFTER _slugify's own
    truncation can silently swallow it when the base stem is already at
    the limit)."""
    meetings_root = vault_path / _MEETINGS_SUBFOLDER
    slug = _slugify(base_stem)
    candidate = meetings_root / slug
    if not candidate.exists():
        return candidate
    suffix = hashlib.sha256(calendar_id.encode("utf-8")).hexdigest()[:8]
    reserved = len(suffix) + 1  # "-" + suffix
    truncated = base_stem[: max(1, 80 - reserved)]
    return meetings_root / _slugify(f"{truncated}-{suffix}")


def meeting_directory_for_new(vault_path: Path, subject: str, start: str, is_recurring: bool, calendar_id: str) -> Path:
    """Computes the directory a BRAND NEW meeting should be created at --
    only call this after resolve_meeting_directory() has confirmed no
    existing note already claims this calendar_id. One-time: "<date>
    <Subject>" (mirrors a Thread's own "<date> <Subject>" naming, so a
    one-time meeting reads consistently alongside Threads in a flat file
    listing). Recurring: "<Subject>" alone -- no date, since the series
    folder spans every occurrence, not one moment."""
    if is_recurring:
        base_stem = subject
    else:
        base_stem = f"{start[:10]} {subject}"
    return _unique_meeting_directory(vault_path, base_stem, calendar_id)


def rename_meeting_series_if_needed(vault_path: Path, directory: Path, subject: str, series_id: str) -> Path:
    """Self-healing repair for a recurring series' own concept
    directory+file, mirroring email-thread-capture's own rename_thread.py
    (BUG-036, found live 2026-08-23): a series first captured before this
    Skill's 2026-08-21 rewrite (or by any future code path that ever again
    passes a raw Outlook id through as the folder name) gets stuck at that
    raw name FOREVER, because resolve_meeting_directory's own dedup-by-
    calendar_series_id scan always finds and reuses that same directory on
    every later occurrence -- new occurrence files land inside it, real
    and correctly named, but the series' own folder+concept-file never
    self-corrects. Called on every ingest (idempotent, cheap no-op once
    already correct) rather than as a one-off migration, so any future
    regression of this kind heals itself on the next capture run instead
    of silently persisting like the original bug did.

    No other note in the vault wikilinks a Meeting concept note by its own
    stem (attendee/thread links all point the other way, or store a bare
    conversation_id string -- see link_meeting_to_thread.py), so unlike
    rename_thread_directory this never needs to touch any file outside
    `directory` itself."""
    correct_slug = _slugify(subject)
    if directory.name == correct_slug:
        return directory  # already correct -- the common case, every run
    new_directory = directory.parent / correct_slug
    if new_directory.exists() and new_directory != directory:
        suffix = hashlib.sha256(series_id.encode("utf-8")).hexdigest()[:8]
        reserved = len(suffix) + 1  # "-" + suffix
        truncated = subject[: max(1, 80 - reserved)]
        new_directory = directory.parent / _slugify(f"{truncated}-{suffix}")
    old_slug = directory.name
    directory.rename(new_directory)
    (new_directory / f"{old_slug}.md").rename(new_directory / f"{new_directory.name}.md")
    return new_directory


def build_meeting_tags(customer: str | None) -> list[str]:
    """Mirrors every other note kind's own self-tag shape. Deliberately
    does NOT derive `customer` at capture time (operator, 2026-08-21:
    company tagging is the same later, deliberate job Threads already
    use -- create-companies-partners's own retag pass -- never guessed
    here). Always ["kind/meeting"] at capture; a customer/partner tag is
    added later, by that other job, via merge_tags-style union, never
    here."""
    return ["kind/meeting"]


def create_meeting_note_baseline(
    concept_path: Path, subject: str, is_recurring: bool, calendar_id: str,
    organizer: str, teams_link: str, dial_in: str,
) -> None:
    """Creates a Meeting concept note for the first time -- a one-time
    meeting's own single file, or a recurring series' own concept file
    (created alongside its first captured occurrence). Frontmatter is
    logistics-only at this level; per-occurrence start/end/location live
    on the occurrence file itself for a recurring series (one-time: this
    same file IS the occurrence, so it carries them directly -- see
    create_or_update_meeting_occurrence_fields, called right after this
    for the one-time case)."""
    frontmatter: dict = {
        "type": "Meeting",
        "recurrence": is_recurring,
        "organizer": organizer,
        "teams_link": teams_link,
        "dial_in": dial_in,
        "attendees": [],
        "tags": build_meeting_tags(None),
        "thread": "",
    }
    frontmatter["calendar_series_id" if is_recurring else "calendar_event_id"] = calendar_id
    body = (
        "## Summary\n\n## Quick Notes\n\n## Personal Notes\n\n"
        "## Actions\n\n## Related\n"
    )
    if is_recurring:
        body += "\n## History\n"
    _write_frontmatter_note(concept_path, frontmatter, body)


def set_occurrence_logistics(path: Path, start: str, end: str, location: str) -> None:
    """Fills in start/end/location on a note that carries its own
    occurrence data directly -- a one-time meeting's own concept file, or
    a recurring series' own occurrence file. Never overwrites an
    already-present value (insert_frontmatter_key_if_missing's own
    contract) -- these are logged once, at first capture, and not
    expected to change (an Outlook reschedule produces this Skill's own
    same dedup-by-calendar-id path recognizing the SAME meeting and
    topping it up, not a rewrite of already-recorded logistics)."""
    for key, value in (("start", start), ("end", end), ("location", location)):
        insert_frontmatter_key_if_missing(path, key, value)


# ── recurring-series occurrence files ───────────────────────────────────

def occurrence_note_path(series_directory: Path, subject: str, start: str, calendar_id: str) -> Path:
    """<date> <time> <Subject>.md under the series' own occurrences/ --
    mirrors raw_message_note_path's own shape exactly (date + time +
    readable name), including its hash-suffix fallback for the
    vanishingly rare case two occurrences of the SAME series resolve to
    the identical minute."""
    occurrences_dir = series_directory / "occurrences"
    time_of_day = start[11:16].replace(":", "")
    parts = [start[:10]]
    if time_of_day:
        parts.append(time_of_day)
    parts.append(_slugify(subject))
    stem = " ".join(parts)
    candidate = occurrences_dir / f"{stem}.md"
    if not candidate.exists():
        return candidate
    existing_frontmatter, _ = read_note(candidate)
    if existing_frontmatter.get("calendar_event_id") == calendar_id:
        return candidate
    suffix = hashlib.sha256(calendar_id.encode("utf-8")).hexdigest()[:8]
    return occurrences_dir / f"{stem}-{suffix}.md"


def occurrence_note_exists(series_directory: Path, subject: str, start: str, calendar_id: str) -> bool:
    return occurrence_note_path(series_directory, subject, start, calendar_id).exists()


def create_occurrence_note(
    occurrence_path: Path, subject: str, calendar_id: str, start: str, end: str, location: str,
    organizer: str, teams_link: str, dial_in: str,
) -> None:
    frontmatter = {
        "type": "Meeting",
        "calendar_event_id": calendar_id,
        "start": start,
        "end": end,
        "location": location,
        "organizer": organizer,
        "teams_link": teams_link,
        "dial_in": dial_in,
        "attendees": [],
        "tags": build_meeting_tags(None),
        "thread": "",
    }
    body = "## Summary\n\n## Quick Notes\n\n## Personal Notes\n\n## Actions\n\n## Related\n"
    _write_frontmatter_note(occurrence_path, frontmatter, body)


def link_occurrence_to_series(series_concept_path: Path, occurrence_path: Path, date: str, *, caller: str) -> bool:
    """Accumulates one dated wikilink per occurrence into the series
    concept note's own "## History" -- mirrors link_file_to_thread's own
    accumulate-into-a-section pattern. Idempotent -- calling twice for
    the same occurrence adds the wikilink only once."""
    wikilink = f"[[{occurrence_path.stem}]]"
    insert_body_section_if_missing(series_concept_path, "## History")
    existing = read_body_section(series_concept_path, "## History")
    if wikilink in existing:
        return False
    lines = [line for line in existing.splitlines() if line.strip()]
    lines.append(f"- {date}: {wikilink}")
    replace_body_section(series_concept_path, "## History", "\n".join(lines), caller=caller)
    return True


# ── attendee linking (mirrors link_person_to_thread's own contract) ─────

def link_person_to_meeting(meeting_note_path: Path, person_stem: str, *, caller: str) -> bool:
    wikilink = f"[[{person_stem}]]"
    insert_body_section_if_missing(meeting_note_path, "## Related")
    existing = read_body_section(meeting_note_path, "## Related")
    if wikilink in existing:
        return False
    lines = [line for line in existing.splitlines() if line.strip()]
    lines.append(f"- {wikilink}")
    replace_body_section(meeting_note_path, "## Related", "\n".join(lines), caller=caller)
    return True


def add_attendee_to_frontmatter(meeting_note_path: Path, person_stem: str) -> bool:
    """Unions one wikilink into the meeting note's own `attendees` list,
    same union-never-overwrite contract as merge_tags elsewhere in this
    codebase."""
    frontmatter, _ = read_note(meeting_note_path)
    existing = list(frontmatter.get("attendees") or [])
    wikilink = f"[[{person_stem}]]"
    if wikilink in existing:
        return False
    merged = existing + [wikilink]
    text = meeting_note_path.read_text(encoding="utf-8")
    end = text.find("\n---\n", 4)
    if end == -1:
        return False
    frontmatter_block = text[: end + 1]
    rest = text[end + 1:]
    lines = frontmatter_block.splitlines(keepends=True)
    new_line = f"attendees: {_format_frontmatter_value(merged)}\n"
    replaced = False
    for i, line in enumerate(lines):
        match = _FRONTMATTER_LINE.match(line.rstrip("\n"))
        if match and match.group(1) == "attendees":
            lines[i] = new_line
            replaced = True
            break
    if not replaced:
        lines.insert(-1, new_line)
    meeting_note_path.write_text("".join(lines) + rest, encoding="utf-8")
    return True


# ── Bare Person-note primitive (identical contract to
# email-thread-capture's own vault_lib.py -- duplicated, not shared, per
# this codebase's own per-Skill self-containment convention) ────────────

def _looks_like_real_email(value: str) -> bool:
    """A LegacyExchangeDN (Outlook's own fallback address when
    GetExchangeUser() resolution fails for an EX-type meeting attendee,
    e.g. "/o=ExchangeLabs/ou=Exchange Administrative Group
    (FYDIBOHF23SPDLT)/cn=Recipients/cn=...") has no "@" and starts with
    "/" -- trusting it as a real address produced a real, live Person
    note filed under its own raw DN as filename/dedup key (BUG-036,
    found live 2026-08-23: "Work/People/-o=exchangelabs-ou=exchange
    administrative group (fydibohf23spdlt)-cn=recipients.md", even
    though the SAME note's own `name` field already held the real,
    readable "nalsulaimani")."""
    return "@" in value and not value.startswith("/")


def person_note_dedup_key(name: str, email: str | None) -> str:
    if email and _looks_like_real_email(email):
        return email.lower()
    return _slugify(name.lower())


def find_person_note_path(vault_path: Path, dedup_key: str) -> Path | None:
    """2026-08-21 bug fix (caught live, this Skill's own first real run):
    the Customers-side check was only one level deep (`Customers/*/
    People/`), which never matched a Person note create-companies-
    partners had moved into an AFFILIATE's own People/ folder (e.g.
    Customers/Mubadala/Affiliates/Masdar/People/) -- 3 real duplicate
    bare Person notes landed back in flat Work/People/ for already-filed
    Masdar contacts before this fix. `**/People/` (fully recursive) on
    BOTH roots is the correct check -- a Person note can live at any
    depth under either Customers/ or Partners/."""
    stem = _slugify(dedup_key)
    for root_name in (_CUSTOMERS_SUBFOLDER, f"{_WORK_ROOT}/Partners"):
        root = vault_path / root_name
        if not root.exists():
            continue
        nested_matches = sorted(root.glob(f"**/People/{stem}.md"))
        if nested_matches:
            return nested_matches[0]
    flat_path = vault_path / _PEOPLE_SUBFOLDER / f"{stem}.md"
    return flat_path if flat_path.exists() else None


def ensure_bare_person_note(
    vault_path: Path, name: str, email: str | None,
    department: str = "", role: str = "", company: str = "",
) -> dict | None:
    """Identical contract to email-thread-capture's own
    ensure_bare_person_note (2026-08-21) -- see that Skill's own
    vault_lib.py docstring for the full rationale. Duplicated here
    verbatim rather than imported cross-Skill, matching this codebase's
    established convention; kept in sync by hand if either ever changes.
    Skips (returns None) when email is blank, or when it matches
    `.second-brain/person_ignore_list.json` (2026-08-21 -- see that
    Skill's own vault_lib.py docstring)."""
    if not email:
        return None
    # A garbage-DN "email" (see _looks_like_real_email) still counts as
    # "present" for the blank check above -- Outlook DID return
    # something -- but from here on it's cleaned to "" so neither the
    # dedup key nor the stored frontmatter value ever trusts it as a real
    # address (BUG-036).
    clean_email = email if _looks_like_real_email(email) else ""
    if clean_email.strip().lower() in _load_person_ignore_list(vault_path):
        return None
    dedup_key = person_note_dedup_key(name, clean_email or None)
    existing_path = find_person_note_path(vault_path, dedup_key)
    tags = ["kind/person"]
    baseline = {
        "type": "Person", "name": name, "email": clean_email,
        "phone": "", "linkedin": "",
        "department": department or "", "role": role or "", "company": company or "",
        "tags": tags,
    }
    if existing_path is not None:
        note_path = existing_path
        for key, value in baseline.items():
            insert_frontmatter_key_if_missing(note_path, key, value)
        created = False
    else:
        note_path = vault_path / _PEOPLE_SUBFOLDER / f"{_slugify(dedup_key)}.md"
        _write_frontmatter_note(note_path, baseline, "")
        created = True
    return {"note_path": str(note_path), "created": created}
