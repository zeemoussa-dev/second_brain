"""Writes markdown notes into the Obsidian vault (app.config.settings.vault_path).
No staging/promotion step — per MEMORY.md's decision, anything written here is
immediately part of the trusted vault.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone

from app.config import settings

_SLUG_INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')
_TAG_INVALID_CHARS = re.compile(r"[^a-z0-9/]+")
_WORK_ROOT = "Work"
_STATE_DIR = ".second-brain"
_PROCESSED_EMAILS_FILE = "processed_email_ids.json"
_CONVERSATIONS_FILE = "conversation_index.json"
_LAST_CAPTURE_RUN_FILE = "last_capture_run.json"
_AGENT_HISTORY_FILE = "agent_communication_history.json"
_AGENT_SECTIONS_FILE = "agent_sections.json"
_AGENT_PROVIDERS_FILE = "agent_providers.json"
_AGENT_MEMORY_FILE = "agent_memory.json"
_AGENT_SKILLS_FILE = "agent_skills.json"
_AGENT_KEYWORDS_FILE = "agent_keywords.json"
_AGENT_WORKING_MODES_FILE = "agent_working_modes.json"
_AGENT_PENDING_APPROVALS_FILE = "agent_pending_approvals.json"
_FRONTMATTER_LINE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*):\s?(.*)$")
_LIST_ITEM_PATTERN = re.compile(r'"((?:[^"\\]|\\.)*)"')


def _slugify(text: str, max_len: int = 80) -> str:
    slug = _SLUG_INVALID_CHARS.sub("-", text).strip()
    return slug[:max_len] if slug else "untitled"


def tag_slug(text: str) -> str:
    """Obsidian tags can't contain spaces — lowercase, non-alphanumeric runs
    collapsed to a single hyphen, e.g. 'Department of Government Enablement'
    -> 'department-of-government-enablement'. Public (promoted from the
    former _tag_slug — REQ-SB-10 — so business-layer code has one shared
    normalization function instead of duplicating slug logic outside
    data_access; pure rename, no behavior change)."""
    slug = _TAG_INVALID_CHARS.sub("-", text.lower()).strip("-")
    return slug or "untitled"


def build_tags(customer: str, kind: str) -> list[str]:
    """Hierarchical Obsidian tags mirroring the folder structure, so notes
    stay findable by customer/kind via search/graph view independent of
    where they physically live — the point raised when a note sits in
    Unsorted/ but you already suspect which customer it's really for."""
    return [f"customer/{tag_slug(customer)}", f"kind/{tag_slug(kind)}"]


def _format_frontmatter_value(value) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(_format_frontmatter_value(v) for v in value) + "]"
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return str(value)


def _parse_frontmatter_value(raw: str):
    raw = raw.strip()
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if raw.startswith("[") and raw.endswith("]"):
        # Real gap, found and fixed by REQ-SB-01-US-01: every list-shaped
        # frontmatter value this codebase writes (tags, via
        # _format_frontmatter_value's own list branch) is always a list
        # of quoted strings. Still not a general YAML parser (unchanged
        # docstring caveat on read_note); only this one recognized literal
        # shape.
        inner = raw[1:-1]
        return [
            match.group(1).replace('\\"', '"').replace("\\\\", "\\")
            for match in _LIST_ITEM_PATTERN.finditer(inner)
        ]
    return raw


def read_note(path) -> tuple[dict, str]:
    """Splits a note into (frontmatter dict, body text). Parses only the
    simple key: "value" shape write_note itself produces — good enough for
    the backfill script, not a general YAML parser."""
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


def extract_wikilink_targets(body: str) -> list[str]:
    """Every [[target]] wikilink target found anywhere in a note's body
    text, in first-seen order — reuses the same _WIKILINK_PATTERN
    upsert_attendee_links already relies on for one matched
    **Attendees:** line, generalized to the whole body (REQ-SB-01-US-01,
    the vault indexing layer's own outgoing-wikilink capture). Resolving
    a target against another note's own filename stem is the caller's
    job (app/business/vault_indexing.py), not this function's — this is
    a raw text-extraction primitive only, matching read_note()'s own
    "not a general parser" scope."""
    return _WIKILINK_PATTERN.findall(body)


def insert_tags_line(path, tags: list[str]) -> None:
    """Surgical insert, not a full frontmatter rewrite — adds a single
    `tags: [...]` line just before the closing `---`, leaving every other
    line (including exact number formatting) byte-for-byte untouched. Used
    for backfilling notes written before `tags` existed."""
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---\n", 4)
    if end == -1:
        return
    insertion = f'tags: {_format_frontmatter_value(tags)}\n'
    path.write_text(text[: end + 1] + insertion + text[end + 1:], encoding="utf-8")


def list_all_note_paths() -> list:
    work_root = settings.vault_path / _WORK_ROOT
    if not work_root.exists():
        return []
    return sorted(work_root.glob("*/*.md"))


def list_notes_in_kind_folder(kind: str) -> list:
    """Same shape as list_all_note_paths(), scoped to one Work/<kind>/
    folder (REQ-SB-12-US-02) — avoids reading and discarding every
    Customer/Person/Partner/Notification/File note just to filter down to
    one kind (e.g. Emails, Meetings). Returns [] if the kind folder
    doesn't exist yet (e.g. Meetings before REQ-SB-08 has ever run) —
    same not-yet-created-folder handling list_all_note_paths() already
    has for Work/ itself."""
    kind_root = settings.vault_path / _WORK_ROOT / kind
    if not kind_root.exists():
        return []
    return sorted(kind_root.glob("*.md"))


def write_note(subfolder: str, filename_stem: str, frontmatter: dict, body: str) -> str:
    target_dir = settings.vault_path / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)

    frontmatter_lines = ["---"]
    for key, value in frontmatter.items():
        frontmatter_lines.append(f"{key}: {_format_frontmatter_value(value)}")
    frontmatter_lines.append("---")

    note_path = target_dir / f"{_slugify(filename_stem)}.md"
    note_path.write_text("\n".join(frontmatter_lines) + "\n\n" + body, encoding="utf-8")
    return str(note_path)


def list_known_customers() -> list[str]:
    """Dynamic replacement for a hardcoded customer list. Customer is no
    longer a folder level (per Beyond the Second Brain's "folders are the
    enemy of thinking" — a note's customer relevance is multidimensional
    and shouldn't force one physical home), so this reads the `customer`
    frontmatter field across every note instead of scanning folder names."""
    customers: set[str] = set()
    for path in list_all_note_paths():
        frontmatter, _ = read_note(path)
        customer = frontmatter.get("customer")
        if customer and customer != "Unsorted":
            customers.add(customer)
    return sorted(customers)


def list_known_kinds() -> list[str]:
    """Dynamic replacement for a hardcoded item-kind list — kind stays a
    folder level (Work/<Kind>/) since it's a genuinely stable, single-home
    property of a note (an email is always an email), unlike customer. This
    is the extensibility point for 'more filters in future': a new kind
    needs no code change, just Compass proposing a new label the first
    time."""
    work_root = settings.vault_path / _WORK_ROOT
    if not work_root.exists():
        return []
    return sorted(p.name for p in work_root.iterdir() if p.is_dir())


def write_attachments(subfolder: str, note_stem: str, attachments: list[dict]) -> list[dict]:
    """Saves each attachment next to its note, Obsidian-convention style:
    <subfolder>/attachments/<note_stem>/<filename>. Returns one entry per
    attachment with a vault-relative link (relative to the note's own
    location) for embedding in the note body — oversized attachments (content
    already None per outlook_com.py's size cap) are recorded but not written,
    same "filename-only, not silently dropped" precedent as agentic-map."""
    results: list[dict] = []
    if not attachments:
        return results

    note_slug = _slugify(note_stem)
    attachments_dir = settings.vault_path / subfolder / "attachments" / note_slug

    for attachment in attachments:
        filename = attachment["filename"]
        if attachment["content"] is None:
            results.append({"filename": filename, "size": attachment["size"], "saved": False})
            continue
        attachments_dir.mkdir(parents=True, exist_ok=True)
        file_path = attachments_dir / filename
        file_path.write_bytes(attachment["content"])
        relative_link = f"attachments/{note_slug}/{filename}"
        results.append({
            "filename": filename,
            "size": attachment["size"],
            "saved": True,
            "relative_link": relative_link,
        })

    return results


def move_note_and_attachments(note_path, target_dir) -> str:
    """Moves a note and its sibling attachments/<note_slug>/ folder (if any)
    into target_dir, preserving the note's own filename. Refuses to
    silently overwrite an existing file at the destination — a genuine
    collision should surface, not disappear one of the two notes."""
    target_dir.mkdir(parents=True, exist_ok=True)
    note_slug = note_path.stem
    new_note_path = target_dir / note_path.name
    if new_note_path.exists():
        raise FileExistsError(f"would overwrite existing note at {new_note_path}")
    note_path.rename(new_note_path)

    old_attachments_dir = note_path.parent / "attachments" / note_slug
    if old_attachments_dir.exists():
        new_attachments_dir = target_dir / "attachments" / note_slug
        new_attachments_dir.parent.mkdir(parents=True, exist_ok=True)
        old_attachments_dir.rename(new_attachments_dir)

    return str(new_note_path)


def remove_empty_dirs(root) -> None:
    if not root.exists():
        return
    for path in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()
    if root.is_dir() and not any(root.iterdir()):
        root.rmdir()


def _processed_emails_path():
    state_dir = settings.vault_path / _STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _PROCESSED_EMAILS_FILE


def load_processed_email_ids() -> set[str]:
    path = _processed_emails_path()
    if not path.exists():
        return set()
    return set(json.loads(path.read_text(encoding="utf-8")))


def mark_email_processed(entry_id: str) -> None:
    path = _processed_emails_path()
    processed = load_processed_email_ids()
    processed.add(entry_id)
    path.write_text(json.dumps(sorted(processed), indent=2), encoding="utf-8")


def _conversations_path():
    state_dir = settings.vault_path / _STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _CONVERSATIONS_FILE


def _load_conversation_index() -> dict[str, list[str]]:
    path = _conversations_path()
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def find_related_note_stems(conversation_id: str) -> list[str]:
    """Notes already written for the same Outlook thread (ConversationID),
    for linking a new note to them via wikilinks — Obsidian computes the
    reverse links automatically, so only the new note needs to link
    forward."""
    if not conversation_id:
        return []
    return _load_conversation_index().get(conversation_id, [])


def record_conversation_note(conversation_id: str, note_stem: str) -> None:
    if not conversation_id:
        return
    path = _conversations_path()
    index = _load_conversation_index()
    index.setdefault(conversation_id, []).append(_slugify(note_stem))
    path.write_text(json.dumps(index, indent=2), encoding="utf-8")


def _last_capture_run_path():
    state_dir = settings.vault_path / _STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _LAST_CAPTURE_RUN_FILE


def record_capture_run_completed() -> None:
    path = _last_capture_run_path()
    record = {"finished_at": datetime.now(timezone.utc).isoformat()}
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def load_last_capture_run() -> dict | None:
    path = _last_capture_run_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


_CUSTOMERS_SUBFOLDER = f"{_WORK_ROOT}/Customers"
_HUB_NOTE_BASELINE_KEYS = ("type", "customer", "tags", "affiliate_of")


def hub_note_path(customer: str):
    """Resolves the vault-absolute path a customer's hub note lives (or
    would live) at — Work/Customers/<Customer>.md — without checking
    whether it exists yet. Uses the same _slugify() write_note() applies
    to its own filename_stem, so this always points at exactly the file
    create_customer_hub_note_baseline()/write_note() would create."""
    return settings.vault_path / _CUSTOMERS_SUBFOLDER / f"{_slugify(customer)}.md"


def hub_note_exists(customer: str) -> bool:
    return hub_note_path(customer).exists()


def create_customer_hub_note_baseline(customer: str) -> str:
    """Creates a customer's hub note for the first time: baseline
    frontmatter (type/customer/tags/affiliate_of) plus a short
    auto-generated body stub inviting the user to add their own overview
    — REQ-SB-10's pattern extended to Customers (see architecture.md,
    'Customer Hub Notes & Graph Linking'). Always writes unconditionally,
    mirroring write_note()'s own contract — callers must check
    hub_note_exists() first (app/business/customer_hub_linking.py does)."""
    return write_note(
        subfolder=_CUSTOMERS_SUBFOLDER,
        filename_stem=customer,
        frontmatter={
            "type": "Customer",
            "customer": customer,
            "tags": build_tags(customer, "customer"),
            "affiliate_of": "",
        },
        body=(
            f"# {customer}\n\n"
            "_Add your own overview, key contacts, and current focus "
            "below — this section is never programmatically rewritten "
            "once you do._\n"
        ),
    )


def insert_frontmatter_key_if_missing(path, key: str, value) -> bool:
    """Surgical insert of one `key: value` frontmatter line just before
    the closing `---`, leaving every other line (including exact
    formatting) byte-for-byte untouched — generalizes insert_tags_line's
    "surgical insert, not full rewrite" precedent from a single
    hardcoded `tags` key to any key/value pair, and (unlike
    insert_tags_line) checks presence itself rather than relying on the
    caller. Returns True if inserted, False if the key was already
    present (no write performed)."""
    frontmatter, _ = read_note(path)
    if key in frontmatter:
        return False
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---\n", 4)
    if end == -1:
        return False
    insertion = f"{key}: {_format_frontmatter_value(value)}\n"
    path.write_text(text[: end + 1] + insertion + text[end + 1 :], encoding="utf-8")
    return True


def ensure_hub_note_baseline_frontmatter(path, customer: str) -> list[str]:
    """Tops up an already-existing hub note with any of the four baseline
    frontmatter keys it is missing (type/customer/tags/affiliate_of),
    inserting each surgically via insert_frontmatter_key_if_missing —
    never touches a key already present (so a real affiliate_of value,
    once set, is never reset to ""), and never touches the body. Returns
    the list of keys actually inserted (empty if the note already had
    all four) — REQ-SB-14 Scenario 4's baseline-preservation mechanism."""
    baseline_values = {
        "type": "Customer",
        "customer": customer,
        "tags": build_tags(customer, "customer"),
        "affiliate_of": "",
    }
    inserted: list[str] = []
    for key in _HUB_NOTE_BASELINE_KEYS:
        if insert_frontmatter_key_if_missing(path, key, baseline_values[key]):
            inserted.append(key)
    return inserted


def insert_body_line_if_missing(path, line: str) -> bool:
    """Surgical insert of a single line as the first line of a note's
    body if it is not already present anywhere in the file — used for
    the inline `**Customer:** [[Hub]]` wikilink (REQ-SB-14 Scenario 5's
    idempotency: an already-linked note must be left byte-for-byte
    unchanged on a rerun). Returns True if inserted, False if the line
    was already present (no write performed)."""
    text = path.read_text(encoding="utf-8")
    if line in text:
        return False
    end = text.find("\n---\n", 4)
    if end == -1:
        # No frontmatter block found (shouldn't happen for notes this
        # module writes) — prepend at the very top as a fallback.
        path.write_text(line + "\n\n" + text, encoding="utf-8")
        return True
    # write_note() always writes "---\n\n<body>" — end points at the
    # leading "\n" of the closing "\n---\n"; body starts 6 chars later
    # (past "---\n" itself, plus the blank-line separator).
    body_start = end + 6
    new_text = text[:body_start] + line + "\n\n" + text[body_start:]
    path.write_text(new_text, encoding="utf-8")
    return True


_PEOPLE_SUBFOLDER = f"{_WORK_ROOT}/People"
_PERSON_NOTE_BASELINE_KEYS = ("type", "name", "email", "phone", "linkedin", "tags")


def person_note_path(email: str):
    """Resolves the vault-absolute path a Person note lives (or would
    live) at — Work/People/<slug-of-lowercased-email>.md — without
    checking whether it exists yet. The dedup key is the sender's email
    address, lowercased before slugifying (never the display name, and
    never the raw-cased address): two Outlook items can report the same
    address with different casing, and lowercasing first prevents a
    second, spurious Person note for what is really the same person
    (REQ-SB-10, architecture.md). Uses the same _slugify() write_note()
    applies internally to its own filename_stem when passed the
    identical lowercased string, so this always points at exactly the
    file create_person_note_baseline()/write_note() would create."""
    return settings.vault_path / _PEOPLE_SUBFOLDER / f"{_slugify(email.lower())}.md"


def person_note_exists(email: str) -> bool:
    return person_note_path(email).exists()


def build_person_tags(company: str | None) -> list[str]:
    """Mirrors build_tags's shape for the People schema's separate
    company/ tag namespace — never customer/, since a person's employer
    isn't always a customer account (many real contacts are internal
    Core42 colleagues or third parties). Returns ["kind/person"] alone
    when no company was derived (Scenario 5 — a personal/free email
    domain, or no domain at all), or ["company/<slug>", "kind/person"]
    when one was (Scenarios 3 and 4 both get the tag; only Scenario 3
    also gets the wikilink, added separately by the orchestration
    layer)."""
    if not company:
        return ["kind/person"]
    return [f"company/{tag_slug(company)}", "kind/person"]


def create_person_note_baseline(name: str, email: str, tags: list[str]) -> str:
    """Creates a Person note for the first time: baseline frontmatter
    (type/name/email/phone/linkedin/tags) with an empty body — the
    REQ-SB-14 hub-note baseline pattern applied to People. The company
    wikilink line (when applicable) is never written here — it is
    inserted separately via insert_body_line_if_missing by the
    orchestration layer, the same way customer_hub_linking.
    link_note_to_customer_hub layers on top of ensure_customer_hub_note,
    so a Person note with no matching customer at creation time still
    gets the link retroactively once one exists (Scenario 8). Always
    writes unconditionally, mirroring write_note()'s own contract —
    callers must check person_note_exists() first (app/business/
    people_extraction.py does)."""
    return write_note(
        subfolder=_PEOPLE_SUBFOLDER,
        filename_stem=email.lower(),
        frontmatter={
            "type": "Person",
            "name": name,
            "email": email,
            "phone": "",
            "linkedin": "",
            "tags": tags,
        },
        body="",
    )


def ensure_person_note_baseline_frontmatter(path, name: str, email: str, tags: list[str]) -> list[str]:
    """Tops up an already-existing Person note with any of the six
    baseline frontmatter keys it is missing (type/name/email/phone/
    linkedin/tags), inserting each surgically via
    insert_frontmatter_key_if_missing — never touches a key already
    present (so a user-filled phone/linkedin value, once set, is never
    reset to ""), and never touches the body. Returns the list of keys
    actually inserted (empty if the note already had all six) —
    REQ-SB-10 Scenario 6's baseline-preservation mechanism, the same
    contract ensure_hub_note_baseline_frontmatter already established
    for Customer hub notes."""
    baseline_values = {
        "type": "Person",
        "name": name,
        "email": email,
        "phone": "",
        "linkedin": "",
        "tags": tags,
    }
    inserted: list[str] = []
    for key in _PERSON_NOTE_BASELINE_KEYS:
        if insert_frontmatter_key_if_missing(path, key, baseline_values[key]):
            inserted.append(key)
    return inserted


_MEETINGS_SUBFOLDER = f"{_WORK_ROOT}/Meetings"
_MEETING_NOTE_BASELINE_KEYS = (
    "type", "customer", "subject", "start", "end", "location", "organizer", "tags",
)
_PROCESSED_MEETINGS_FILE = "processed_meeting_ids.json"

_ATTENDEES_LINE_PATTERN = re.compile(r"^\*\*Attendees:\*\* (.+)$", re.MULTILINE)
_ATTENDEES_LINE_PREFIX = "**Attendees:** "
_WIKILINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")


def meeting_note_filename_stem(subject: str, start: str) -> str:
    """<subject>-<date>-<hash-suffix> — mirrors the EntryID-suffix
    disambiguation email filenames already use (MEMORY.md), but the
    suffix is now an 8-hex-char SHA-256 prefix of `f"{subject}|{start}"`
    (ADR-019) rather than any Outlook-provided identity field — both
    `EntryID` (ADR-008) and `AppointmentItem.GlobalAppointmentID`
    (ADR-013) were tried and live-confirmed non-unique across a real
    recurring series' expanded occurrences on this Outlook installation
    (ESC-002, ESC-012). The key is now a structural, not empirical,
    uniqueness guarantee: two distinct real occurrences of the same
    recurring series cannot share an identical exact start moment, so
    `start` (the full, precise timestamp string list_calendar_events
    returns, not the coarse `start[:10]` date-only slice used below for
    the filename's own display component) is the disambiguator. `subject`
    is combined into the hash input because two different, unrelated
    meetings can genuinely start at the exact same instant — a
    timestamp-only key would silently merge those two into one note.
    Hashing the complete combined string (not a raw slice) keeps ADR-013
    point 2's already-correct reasoning intact: any difference anywhere
    in the input changes the hash, so no positional assumption about
    where the "varying part" of a date/subject string lives is ever
    load-bearing."""
    date = start[:10]
    suffix = hashlib.sha256(f"{subject}|{start}".encode("utf-8")).hexdigest()[:8]
    return f"{subject}-{date}-{suffix}"


def meeting_note_path(subject: str, start: str):
    """Resolves the vault-absolute path a Meeting note lives (or would
    live) at — Work/Meetings/<subject>-<date>-<hash-suffix>.md — without
    checking whether it exists yet. Uses the same _slugify() write_note()
    applies to its own filename_stem, so this always points at exactly
    the file create_meeting_note_baseline()/write_note() would create."""
    stem = meeting_note_filename_stem(subject, start)
    return settings.vault_path / _MEETINGS_SUBFOLDER / f"{_slugify(stem)}.md"


def meeting_note_exists(subject: str, start: str) -> bool:
    return meeting_note_path(subject, start).exists()


def _legacy_meeting_note_path_by_entry_id(subject: str, start: str, entry_id: str):
    """Computes the PRE-ADR-013 filename scheme (EntryID[-8:] suffix) —
    kept only so resolve_meeting_note_path can recognize an
    already-captured note written before this fix, without migrating
    or renaming it. Never used to create a new note."""
    date = start[:10]
    stem = f"{subject}-{date}-{entry_id[-8:]}"
    return settings.vault_path / _MEETINGS_SUBFOLDER / f"{_slugify(stem)}.md"


def resolve_meeting_note_path(subject: str, start: str, entry_id: str):
    """Returns (path, already_existed) — two tiers only (ADR-019): checks
    the current precise-start-timestamp-hash path first; if not found,
    falls back to the legacy EntryID-suffix path (ADR-013 point 3,
    unmodified) so an already-captured, still-in-window event (from
    before either fix) is recognized and topped up rather than
    duplicated under a new filename. ADR-013's own middle
    GlobalAppointmentID-hash tier is deliberately not carried forward —
    zero real notes were ever created under it (confirmed live,
    REQ-SB-08-US-01-T06), so keeping it would be dead code carrying a
    live-confirmed defect (ESC-012), not a genuine safety net. Neither of
    the 39 pre-fix notes is renamed by this function — whichever path is
    found is returned as-is."""
    new_path = meeting_note_path(subject, start)
    if new_path.exists():
        return new_path, True
    legacy_path = _legacy_meeting_note_path_by_entry_id(subject, start, entry_id)
    if legacy_path.exists():
        return legacy_path, True
    return new_path, False


def build_meeting_tags(customer: str | None) -> list[str]:
    """Mirrors build_person_tags's shape for Meetings. Returns
    ["kind/meeting"] alone when no customer was derived (Scenario 3, 8), or
    ["customer/<slug>", "kind/meeting"] when one was (Scenario 1)."""
    if not customer:
        return ["kind/meeting"]
    return [f"customer/{tag_slug(customer)}", "kind/meeting"]


def create_meeting_note_baseline(
    subject: str,
    customer: str | None,
    start: str,
    end: str,
    location: str,
    organizer: str,
) -> str:
    """Creates a Meeting note for the first time: baseline frontmatter
    (type/customer/subject/start/end/location/organizer/tags) with an
    empty body — the REQ-SB-14/REQ-SB-10 baseline pattern applied to
    Meetings. The **Customer:**/**Attendees:** body lines are never
    written here — they are inserted separately by the orchestration
    layer (T03), the same way link_note_to_customer_hub layers on top of
    ensure_customer_hub_note. Always writes unconditionally, mirroring
    write_note()'s own contract — callers must check meeting_note_exists()
    first (T03 does)."""
    return write_note(
        subfolder=_MEETINGS_SUBFOLDER,
        filename_stem=meeting_note_filename_stem(subject, start),
        frontmatter={
            "type": "Meeting",
            "customer": customer or "",
            "subject": subject,
            "start": start,
            "end": end,
            "location": location,
            "organizer": organizer,
            "tags": build_meeting_tags(customer),
        },
        body="",
    )


def ensure_meeting_note_baseline_frontmatter(
    path,
    subject: str,
    customer: str | None,
    start: str,
    end: str,
    location: str,
    organizer: str,
) -> list[str]:
    """Tops up an already-existing Meeting note with any of the eight
    baseline frontmatter keys it is missing, inserting each surgically via
    insert_frontmatter_key_if_missing — never touches a key already
    present, and never touches the body. Returns the list of keys actually
    inserted (empty if the note already had all eight) — Scenario 2/6's
    baseline-preservation mechanism, the same contract
    ensure_person_note_baseline_frontmatter/ensure_hub_note_baseline_
    frontmatter already established."""
    baseline_values = {
        "type": "Meeting",
        "customer": customer or "",
        "subject": subject,
        "start": start,
        "end": end,
        "location": location,
        "organizer": organizer,
        "tags": build_meeting_tags(customer),
    }
    inserted: list[str] = []
    for key in _MEETING_NOTE_BASELINE_KEYS:
        if insert_frontmatter_key_if_missing(path, key, baseline_values[key]):
            inserted.append(key)
    return inserted


def _processed_meetings_path():
    state_dir = settings.vault_path / _STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _PROCESSED_MEETINGS_FILE


def load_processed_meeting_ids() -> set[str]:
    path = _processed_meetings_path()
    if not path.exists():
        return set()
    return set(json.loads(path.read_text(encoding="utf-8")))


def mark_meeting_processed(marker: str) -> None:
    """Mirrors mark_email_processed's exact shape (ADR-008) — a flat,
    idempotent set-of-IDs audit record. Adding an already-present marker
    is a no-op. Note: meeting_classification.py (T03) does not gate
    reprocessing on this file the way email capture gates on
    processed_email_ids — see T03's own Context/Notes for why (Scenario
    2/6 require an in-window event to still flow through the top-up path
    on every rerun). The caller now passes the resolved note's own
    filename stem (ADR-019) rather than a separately-computed
    identifier — once there is no single "the" per-occurrence Outlook
    identifier, computing one specially just for this audit-trail call is
    unnecessary busywork, and the note's own filename stem is already the
    exact per-occurrence disambiguator under whichever tier
    resolve_meeting_note_path actually resolved. The file's existing
    heterogeneous EntryID-era and GlobalAppointmentID-era entries
    (written by earlier code, ADR-008/ADR-013) are left untouched: still
    an audit trail for future observability (REQ-SB-11), never a
    schema-enforced lookup structure any code path depends on for
    uniqueness."""
    path = _processed_meetings_path()
    processed = load_processed_meeting_ids()
    processed.add(marker)
    path.write_text(json.dumps(sorted(processed), indent=2), encoding="utf-8")


def upsert_attendee_links(path, person_stems: list[str]) -> bool:
    """Upserts the growable **Attendees:** [[P1]], [[P2]], ...] body line —
    unlike the single-target insert_body_line_if_missing (a link is either
    present or not), this line can legitimately grow across reruns as new
    attendees are confirmed (Scenario 6). If no Attendees line exists yet,
    inserts one as the first line of the body (mirroring
    insert_body_line_if_missing's insert-at-body-start contract). If one
    already exists, merges in any person_stems not already linked —
    preserving existing wikilink order, appending new ones, updating the
    line in place rather than moving it — never removes an existing
    wikilink. Returns True if the line was created or grew, False if every
    stem in person_stems was already present (a true no-op rerun) or if
    person_stems is empty (Scenario 8 — no attendees, no Attendees line at
    all)."""
    if not person_stems:
        return False
    text = path.read_text(encoding="utf-8")
    match = _ATTENDEES_LINE_PATTERN.search(text)
    if match is None:
        new_line = _ATTENDEES_LINE_PREFIX + ", ".join(f"[[{stem}]]" for stem in person_stems)
        end = text.find("\n---\n", 4)
        if end == -1:
            path.write_text(new_line + "\n\n" + text, encoding="utf-8")
            return True
        body_start = end + 6
        new_text = text[:body_start] + new_line + "\n\n" + text[body_start:]
        path.write_text(new_text, encoding="utf-8")
        return True

    existing_stems = _WIKILINK_PATTERN.findall(match.group(1))
    merged_stems = list(existing_stems)
    changed = False
    for stem in person_stems:
        if stem not in merged_stems:
            merged_stems.append(stem)
            changed = True
    if not changed:
        return False
    new_line = _ATTENDEES_LINE_PREFIX + ", ".join(f"[[{stem}]]" for stem in merged_stems)
    new_text = text[: match.start()] + new_line + text[match.end() :]
    path.write_text(new_text, encoding="utf-8")
    return True


_PARTNERS_SUBFOLDER = f"{_WORK_ROOT}/Partners"
_PARTNER_HUB_NOTE_BASELINE_KEYS = ("type", "partner", "tags")


def partner_hub_note_path(partner: str):
    """Resolves the vault-absolute path a partner's hub note lives (or
    would live) at — Work/Partners/<Partner>.md — mirroring
    hub_note_path exactly, for the Partner namespace (ADR-009)."""
    return settings.vault_path / _PARTNERS_SUBFOLDER / f"{_slugify(partner)}.md"


def partner_hub_note_exists(partner: str) -> bool:
    return partner_hub_note_path(partner).exists()


def build_partner_tags(partner: str) -> list[str]:
    """Mirrors build_tags's shape for the Partner tag namespace —
    partner/<slug> is deliberately never customer/<slug> (ADR-009,
    partner/<slug> and customer/<slug> are mutually exclusive)."""
    return [f"partner/{tag_slug(partner)}", "kind/partner"]


def create_partner_hub_note_baseline(partner: str) -> str:
    """Creates a partner's hub note for the first time: baseline
    frontmatter (type/partner/tags — deliberately no affiliate_of,
    Partner has no Affiliate concept, ADR-009) plus the same
    auto-generated body stub convention create_customer_hub_note_baseline
    already uses. Always writes unconditionally, mirroring
    write_note()'s own contract — callers must check
    partner_hub_note_exists() first (app/business/partner_hub_linking.py
    does)."""
    return write_note(
        subfolder=_PARTNERS_SUBFOLDER,
        filename_stem=partner,
        frontmatter={
            "type": "Partner",
            "partner": partner,
            "tags": build_partner_tags(partner),
        },
        body=(
            f"# {partner}\n\n"
            "_Add your own overview, key contacts, and current focus "
            "below — this section is never programmatically rewritten "
            "once you do._\n"
        ),
    )


def ensure_partner_hub_note_baseline_frontmatter(path, partner: str) -> list[str]:
    """Tops up an already-existing partner hub note with any of the
    three baseline frontmatter keys it is missing (type/partner/tags),
    mirroring ensure_hub_note_baseline_frontmatter's exact contract for
    Partner's shorter key set. Never touches a key already present or
    the body. Returns the list of keys actually inserted."""
    baseline_values = {
        "type": "Partner",
        "partner": partner,
        "tags": build_partner_tags(partner),
    }
    inserted: list[str] = []
    for key in _PARTNER_HUB_NOTE_BASELINE_KEYS:
        if insert_frontmatter_key_if_missing(path, key, baseline_values[key]):
            inserted.append(key)
    return inserted


def list_known_partners() -> list[str]:
    """Dynamic, vault-derived replacement for a hardcoded partner list —
    mirrors list_known_customers()'s exact frontmatter-scan pattern,
    reading the `partner` field across every note instead of `customer`
    (ADR-009). Never hardcoded."""
    partners: set[str] = set()
    for path in list_all_note_paths():
        frontmatter, _ = read_note(path)
        partner = frontmatter.get("partner")
        if partner:
            partners.add(partner)
    return sorted(partners)


def rename_frontmatter_key(path, old_key: str, new_key: str, new_value=None) -> bool:
    """Generic frontmatter-key rename for the Customer->Partner
    migration's idempotent retag scan (ADR-009 point 5): renames
    old_key to new_key, preserving the existing value unless new_value
    is given explicitly (used for the hub note's own `type: Customer`
    -> `type: Partner` value swap, where the key name itself doesn't
    change but the value does). No-op (returns False, no write) if
    old_key is not present in the note's frontmatter — this absence
    check is what makes a rerun a true no-op once a note has already
    been migrated. Scoped strictly to the frontmatter block (never the
    body), leaving every other line byte-for-byte untouched, mirroring
    insert_frontmatter_key_if_missing's surgical-insert contract."""
    frontmatter, _ = read_note(path)
    if old_key not in frontmatter:
        return False
    value = new_value if new_value is not None else frontmatter[old_key]
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---\n", 4)
    if end == -1:
        return False
    frontmatter_block = text[: end + 1]
    rest = text[end + 1:]
    lines = frontmatter_block.splitlines(keepends=True)
    for i, line in enumerate(lines):
        match = _FRONTMATTER_LINE.match(line.rstrip("\n"))
        if match and match.group(1) == old_key:
            lines[i] = f"{new_key}: {_format_frontmatter_value(value)}\n"
            break
    path.write_text("".join(lines) + rest, encoding="utf-8")
    return True


def remove_frontmatter_key_if_present(path, key: str) -> bool:
    """Sibling to insert_frontmatter_key_if_missing — drops a
    frontmatter key's line entirely if present. Used to drop
    affiliate_of when a Customer hub note is migrated to Partner, which
    has no Affiliate concept (ADR-009's hub-note rewrite step). Scoped
    strictly to the frontmatter block. No-op (False) if the key is
    already absent — idempotent by construction."""
    frontmatter, _ = read_note(path)
    if key not in frontmatter:
        return False
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---\n", 4)
    if end == -1:
        return False
    frontmatter_block = text[: end + 1]
    rest = text[end + 1:]
    kept_lines = []
    for line in frontmatter_block.splitlines(keepends=True):
        match = _FRONTMATTER_LINE.match(line.rstrip("\n"))
        if match and match.group(1) == key:
            continue
        kept_lines.append(line)
    path.write_text("".join(kept_lines) + rest, encoding="utf-8")
    return True


def swap_tag(path, old_tag: str, new_tag: str) -> bool:
    """Generic tags-list swap for the Customer->Partner migration's
    retag scan (ADR-009 point 5): replaces `"old_tag"` with `"new_tag"`
    within the note's frontmatter `tags:` line only — write_note/
    _format_frontmatter_value always render tags as a single-line
    `tags: ["a", "b"]` list, so a scoped, single-line string replace is
    equivalent to a structural list-element swap without needing a real
    YAML parser (read_note's own documented "not a general YAML parser"
    limitation). Never touches the body or any other frontmatter line.
    No-op (False) if old_tag is not present in that line — idempotent
    by construction."""
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---\n", 4)
    if end == -1:
        return False
    frontmatter_block = text[: end + 1]
    rest = text[end + 1:]
    lines = frontmatter_block.splitlines(keepends=True)
    old_quoted = f'"{old_tag}"'
    new_quoted = f'"{new_tag}"'
    changed = False
    for i, line in enumerate(lines):
        match = _FRONTMATTER_LINE.match(line.rstrip("\n"))
        if match and match.group(1) == "tags" and old_quoted in line:
            lines[i] = line.replace(old_quoted, new_quoted)
            changed = True
            break
    if not changed:
        return False
    path.write_text("".join(lines) + rest, encoding="utf-8")
    return True


def replace_body_line(path, old_line: str, new_line: str) -> bool:
    """Generic body-line-label replace for the Customer->Partner
    migration's retag scan (ADR-009 point 5): replaces the exact line
    old_line with new_line wherever it appears in the note (used to
    relabel an existing inline `**Customer:** [[Name]]` wikilink to
    `**Partner:** [[Name]]`). No-op (False) if old_line is not present
    — idempotent by construction, mirroring insert_body_line_if_missing's
    presence-check style."""
    text = path.read_text(encoding="utf-8")
    if old_line not in text:
        return False
    path.write_text(text.replace(old_line, new_line), encoding="utf-8")
    return True


def _agent_history_path():
    state_dir = settings.vault_path / _STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _AGENT_HISTORY_FILE


def _load_agent_history_index() -> dict[str, list[dict]]:
    path = _agent_history_path()
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def append_agent_history_entry(
    agent_id: str, kind: str, text: str, pending_approval_id: str | None = None,
) -> None:
    """Appends one entry to agent_id's chronological history list
    (ADR-011) — kind is "chat_user" | "chat_agent" | "run_event" |
    "proposal" (ADR-018 point 7 adds "proposal"). pending_approval_id is
    new and optional, additive — every existing caller (positional
    agent_id/kind/text, no fourth argument) is unaffected; only a
    "proposal"-kind entry supplies it, carrying the pending-approval
    record's own id so the frontend can resolve the card's live
    Pending/Approved/Declined status via GET /pending-approvals/{id}.
    Entries are appended in call order and read back in that same
    order (load_agent_history does not re-sort) — every caller
    (scheduler, app-start, /poc/classify-emails,
    POST /agents/{id}/chat, POST /agents/{id}/actions/{action_id})
    already calls this at the moment the event actually happens, so
    append order already is chronological order."""
    path = _agent_history_path()
    index = _load_agent_history_index()
    entry = {
        "kind": kind,
        "text": text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if pending_approval_id is not None:
        entry["pending_approval_id"] = pending_approval_id
    index.setdefault(agent_id, []).append(entry)
    path.write_text(json.dumps(index, indent=2), encoding="utf-8")


def load_agent_history(agent_id: str) -> list[dict]:
    return _load_agent_history_index().get(agent_id, [])


def _sections_state_path():
    state_dir = settings.vault_path / _STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _AGENT_SECTIONS_FILE


def load_sections_state() -> dict | None:
    """Pure I/O — returns None if agent_sections.json doesn't exist yet
    (no default content is computed here, per ADR-003; the non-trivial
    starting-5-sections default is a business-layer decision, owned by
    app/business/section_registry.py, ADR-014 point 1)."""
    path = _sections_state_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_sections_state(state: dict) -> None:
    path = _sections_state_path()
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _providers_state_path():
    state_dir = settings.vault_path / _STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _AGENT_PROVIDERS_FILE


def load_providers_state() -> dict | None:
    """Pure I/O — returns None if agent_providers.json doesn't exist yet
    (no default content is computed here, per ADR-003; the non-trivial
    pre-seeded Compass entry is a business-layer decision, owned by
    app/business/provider_registry.py, ADR-014 point 1)."""
    path = _providers_state_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_providers_state(state: dict) -> None:
    path = _providers_state_path()
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _agent_memory_path():
    state_dir = settings.vault_path / _STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _AGENT_MEMORY_FILE


def _load_agent_memory_index() -> dict[str, list[dict]]:
    path = _agent_memory_path()
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_agent_memory(agent_id: str) -> list[dict]:
    return _load_agent_memory_index().get(agent_id, [])


def append_agent_memory_entries(agent_id: str, facts: list[str]) -> None:
    """Appends one entry per fact string to agent_id's growing memory
    list (ADR-016 point 3) -- a no-op (no file write at all, no file
    created) when facts is empty, so a reply that extracted nothing
    worth remembering (Scenario 3's own honest "no fact" outcome) never
    touches agent_memory.json. Flat, append-only -- no dedup/merge/
    consolidation this pass (ADR-016 point 3), mirroring
    append_agent_history_entry's own "already chronological because
    callers append at the moment the event happens" contract, extended
    to a list of facts arriving from one extraction call at once instead
    of one entry at a time."""
    if not facts:
        return
    path = _agent_memory_path()
    index = _load_agent_memory_index()
    recorded_at = datetime.now(timezone.utc).isoformat()
    index.setdefault(agent_id, []).extend(
        {"fact": fact, "recorded_at": recorded_at} for fact in facts
    )
    path.write_text(json.dumps(index, indent=2), encoding="utf-8")


def _skills_state_path():
    state_dir = settings.vault_path / _STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _AGENT_SKILLS_FILE


def load_skills_state() -> dict | None:
    """Pure I/O — returns None if agent_skills.json doesn't exist yet (no
    default content is computed here, per ADR-003; explicit-grant-only,
    no self-healing default assignment, is a business-layer decision
    owned by app/business/skill_registry.py)."""
    path = _skills_state_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_skills_state(state: dict) -> None:
    path = _skills_state_path()
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _agent_keywords_path():
    state_dir = settings.vault_path / _STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _AGENT_KEYWORDS_FILE


def _load_agent_keywords_index() -> dict[str, list[str]]:
    path = _agent_keywords_path()
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_agent_keywords(agent_id: str) -> list[str]:
    """Pure I/O — returns [] if agent_keywords.json doesn't exist yet, or
    if agent_id has no entry in it (ADR-017 point 2/4: an agent with no
    keywords is the ordinary, expected starting state — no seed list,
    unlike Sections/Providers, since free-text keywords have no sensible
    universal default)."""
    return _load_agent_keywords_index().get(agent_id, [])


def save_agent_keywords(agent_id: str, keywords: list[str]) -> None:
    """Whole-list replace for agent_id's own entry — mirrors the
    free-text kv-list editing UX the Settings panel already uses for
    other per-agent fields (ADR-017 point 3); no incremental
    add/remove-one-keyword primitive exists or is needed."""
    path = _agent_keywords_path()
    index = _load_agent_keywords_index()
    index[agent_id] = keywords
    path.write_text(json.dumps(index, indent=2), encoding="utf-8")


def load_all_agent_keywords() -> dict[str, list[str]]:
    """Whole-file read — needed because the routing node (REQ-SB-20-US-01-T05)
    must scan every OTHER agent's keywords, not one agent's own; no
    existing vault_writer primitive does a whole-file read for a
    per-agent-keyed store (ADR-017 point 2)."""
    return _load_agent_keywords_index()


def _working_modes_state_path():
    state_dir = settings.vault_path / _STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _AGENT_WORKING_MODES_FILE


def load_working_modes_state() -> dict | None:
    """Pure I/O — returns None if agent_working_modes.json doesn't exist
    yet (no default content is computed here, per ADR-003; the
    self-healing "autonomous" default is a business-layer decision,
    owned by app/business/working_mode_registry.py, ADR-018 point 1)."""
    path = _working_modes_state_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_working_modes_state(state: dict) -> None:
    path = _working_modes_state_path()
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _pending_approvals_state_path():
    state_dir = settings.vault_path / _STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _AGENT_PENDING_APPROVALS_FILE


def load_pending_approvals_state() -> dict | None:
    """Pure I/O — returns None if agent_pending_approvals.json doesn't
    exist yet (ADR-003; the empty-list seed and idempotency guard are
    app/business/pending_approval_registry.py's own concern, ADR-018
    point 2)."""
    path = _pending_approvals_state_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_pending_approvals_state(state: dict) -> None:
    path = _pending_approvals_state_path()
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def upsert_frontmatter_key(path, key: str, value) -> bool:
    """Ensures key: value is present with EXACTLY this value -- inserts
    if missing (mirroring insert_frontmatter_key_if_missing), or
    overwrites in place if already present but holding a different
    value (unlike insert_frontmatter_key_if_missing, which never
    touches an already-present key). Used for Task notes' due/status
    fields only (REQ-SB-09 Scenario 5/6) -- the one baseline-field pair
    this pipeline's own ACs require to reflect Outlook's CURRENT value
    on every top-up, not just fill a gap, unlike every other baseline
    key in this codebase so far (Customer/Person/Meeting all use strict
    insert-if-missing). Returns True if the file was written (inserted
    OR changed), False if the key was already present with an
    identical value (a true no-op)."""
    frontmatter, _ = read_note(path)
    if key not in frontmatter:
        return insert_frontmatter_key_if_missing(path, key, value)
    if frontmatter[key] == value:
        return False
    return rename_frontmatter_key(path, key, key, new_value=value)


_TASKS_SUBFOLDER = f"{_WORK_ROOT}/Tasks"
_TASK_NOTE_INDEX_FILE = "task_note_index.json"


def task_note_filename_stem(subject: str, capture_date: str, entry_id: str) -> str:
    """<subject>-<capture-date>-<entry-id-suffix>. capture_date is the
    date this note was FIRST written -- the caller (T03) passes today's
    date only when creating a note for the first time, never
    recomputed from Outlook's own (mutable) due field on a later run
    (ADR-027 point 3) -- this is the load-bearing reason a due-date
    edit between runs still resolves to the SAME note (Scenario 6),
    unlike Meeting's own recompute-from-start scheme. capture_date is
    expected as a 'YYYY-MM-DD' string, mirroring
    meeting_note_filename_stem's [:10]-sliced start convention applied
    one layer up by the caller instead."""
    return f"{subject}-{capture_date}-{entry_id[-8:]}"


def task_note_path_for_stem(stem: str):
    """Resolves the vault-absolute path for an ALREADY-KNOWN filename
    stem, looked up via task_note_index (lookup_task_note_stem, below)
    -- NOT a recompute-from-current-fields path resolver the way
    meeting_note_path works, since Task's own dedup key is the index
    entry itself, not a deterministic function of current field
    values (ADR-027 point 3). Uses the same _slugify() write_note()
    applies internally, so this always points at exactly the file
    create_task_note_baseline() would have created for that stem."""
    return settings.vault_path / _TASKS_SUBFOLDER / f"{_slugify(stem)}.md"


def task_note_exists_for_stem(stem: str) -> bool:
    return task_note_path_for_stem(stem).exists()


def build_task_tags(customer: str | None) -> list[str]:
    """Mirrors build_meeting_tags's shape for Tasks. Returns
    ["kind/task"] alone when no customer was derived (Scenario 3), or
    ["customer/<slug>", "kind/task"] when one was (Scenario 1)."""
    if not customer:
        return ["kind/task"]
    return [f"customer/{tag_slug(customer)}", "kind/task"]


def create_task_note_baseline(
    subject: str,
    customer: str | None,
    due: str | None,
    status: str,
    entry_id: str,
    capture_date: str,
) -> str:
    """Creates a Task note for the first time. Unlike Meeting's
    create_meeting_note_baseline (which always writes a customer key,
    "" when none), Task's resolved schema requires customer/due to be
    ABSENT from frontmatter entirely when not applicable (Scenario 3;
    "absent otherwise" per the story's own ## Context), not written as
    empty placeholders -- both keys are conditionally included in the
    frontmatter dict below, never written unconditionally. The
    **Customer:**/[[wikilink]] body line is never written here -- it is
    inserted separately by the orchestration layer (T03), the same way
    link_note_to_customer_hub layers on top of ensure_customer_hub_note
    for every other captured note type. Always writes unconditionally,
    mirroring write_note()'s own contract -- callers must consult
    lookup_task_note_stem() first (T03 does) to decide create vs.
    top-up."""
    frontmatter: dict = {
        "type": "Task",
    }
    if customer:
        frontmatter["customer"] = customer
    frontmatter["subject"] = subject
    if due:
        frontmatter["due"] = due
    frontmatter["status"] = status
    frontmatter["tags"] = build_task_tags(customer)
    frontmatter["source"] = "outlook-task"
    frontmatter["outlook_entry_id"] = entry_id
    return write_note(
        subfolder=_TASKS_SUBFOLDER,
        filename_stem=task_note_filename_stem(subject, capture_date, entry_id),
        frontmatter=frontmatter,
        body="",
    )


def ensure_task_note_baseline_frontmatter(
    path,
    subject: str,
    customer: str | None,
    due: str | None,
    status: str,
    entry_id: str,
) -> list[str]:
    """Tops up an already-existing Task note. type/subject/tags/source/
    outlook_entry_id/customer follow the established insert-only-if-
    missing contract (never overwritten once set, matching every other
    captured note type in this codebase) -- customer is only ever
    inserted, never re-derived-and-overwritten on a later run, the same
    accepted behavior Meeting's own ensure_meeting_note_baseline_
    frontmatter already established for its own customer field.
    due/status are the ONE deliberate exception (REQ-SB-09 Scenario
    5/6): upserted via upsert_frontmatter_key, so a status change (Not
    Started -> Completed) or a due-date edit in Outlook is reflected on
    the next capture run, not just filled in the first time a value
    exists. due is only touched when Outlook currently reports one
    (due is not None) -- a due date cleared in Outlook after being set
    is not a case any locked AC covers; the existing value is left
    untouched rather than guessing whether to remove it. Never touches
    the body -- the user's own manually-added content survives
    untouched regardless of which frontmatter keys change. Returns the
    list of keys actually inserted or changed (empty if nothing
    changed) -- Scenario 2/6's baseline-preservation mechanism."""
    changed: list[str] = []
    stable_values = {
        "type": "Task",
        "subject": subject,
        "tags": build_task_tags(customer),
        "source": "outlook-task",
        "outlook_entry_id": entry_id,
    }
    for key, value in stable_values.items():
        if insert_frontmatter_key_if_missing(path, key, value):
            changed.append(key)
    if customer and insert_frontmatter_key_if_missing(path, "customer", customer):
        changed.append("customer")
    if due is not None and upsert_frontmatter_key(path, "due", due):
        changed.append("due")
    if upsert_frontmatter_key(path, "status", status):
        changed.append("status")
    return changed


def _task_note_index_path():
    state_dir = settings.vault_path / _STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _TASK_NOTE_INDEX_FILE


def load_task_note_index() -> dict[str, str]:
    path = _task_note_index_path()
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def lookup_task_note_stem(entry_id: str) -> str | None:
    """The dedup/top-up lookup itself (ADR-027 point 3): consulted
    BEFORE any path is computed from current Outlook fields, not a
    recomputed-and-exists()-checked path the way Meeting's
    resolve_meeting_note_path works. Returns the note's own filename
    stem if entry_id has been seen before (regardless of what
    subject/due/status now read as in Outlook), or None if this is
    genuinely a new item never captured before."""
    return load_task_note_index().get(entry_id)


def record_task_note(entry_id: str, stem: str) -> None:
    """Records entry_id -> stem the first (and, by this pipeline's own
    contract, ONLY the first) time a Task note is created for it -- a
    real, load-bearing key->value lookup (unlike processed_meeting_
    ids.json's flat audit-only set), mirroring conversation_index.
    json's own real-lookup shape (find_related_note_stems/
    record_conversation_note), generalized from key -> list[value] to
    key -> value. The caller (T03) only calls this on first creation,
    never on top-up -- a stem is never reassigned once recorded."""
    path = _task_note_index_path()
    index = load_task_note_index()
    index[entry_id] = stem
    path.write_text(json.dumps(index, indent=2), encoding="utf-8")
