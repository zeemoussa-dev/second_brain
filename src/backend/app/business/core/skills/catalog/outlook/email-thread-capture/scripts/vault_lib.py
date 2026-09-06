"""Self-contained vault-writing primitives for the email-thread-capture
Skill (2026-08-21, "fully hosted in Hermes" pivot -- see
Implementation/Plans/2026-08-20-backend-architecture-redesign.md, "MCP
server vs. Hermes-native Skill scripts").

Trimmed port of Second Brain's own app/data_access/vault_writer.py --
only the primitives this Skill's five scripts actually call, per the
operator's own "one Skill per task, pull only what you need" scope
decision. Two deliberate narrowings from the source, both because this
Skill only ever runs against a freshly-rebuilt vault (operator cleared it
before this pipeline began):

  1. resolve_thread_directory() drops the source's legacy flat-Thread-
     note migration fallback tier -- a freshly rebuilt vault can never
     contain a pre-redesign flat Thread note, so that tier is dead code
     here.
  2. Person-note creation (ensure_bare_person_note) skips Customer/
     Partner company-matching and hub-linking entirely -- Capture-phase
     scope only. Second Brain's own existing retrofit_people_from_emails()
     job backfills that enrichment afterward, as a separate whole-vault
     pass, once this pipeline finishes.

No third-party dependencies -- stdlib only.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

_SLUG_INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')
_LEADING_RE_PREFIX = re.compile(r"^(?:re:\s*)+", re.IGNORECASE)
_FRONTMATTER_LINE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*):\s?(.*)$")
_LIST_ITEM_PATTERN = re.compile(r'"((?:[^"\\]|\\.)*)"')
_BODY_SECTION_HEADER_PATTERN = re.compile(r"^## .+$", re.MULTILINE)

_WORK_ROOT = "Work"
_THREADS_SUBFOLDER = f"{_WORK_ROOT}/Threads"
_PEOPLE_SUBFOLDER = f"{_WORK_ROOT}/People"
_CUSTOMERS_SUBFOLDER = f"{_WORK_ROOT}/Customers"

_PERSON_IGNORE_LIST_FILE = "person_ignore_list.json"


def _load_person_ignore_list(vault_path: Path) -> set[str]:
    """2026-08-21, operator: the vault owner's own address and a
    truncation-collision-prone unresolved Exchange DN ("Commercial - All
    Staff", raw X.500 path with no real SMTP address) were both showing
    up as Person notes and links "everywhere" -- neither is ever a real,
    useful contact. A real, accessible config file (never a hardcoded
    Python literal, matching this codebase's own established discipline
    -- see meeting_thread_link_config.py's own docstring for the same
    rule applied elsewhere), so the operator can add more later without
    another code change. Missing file -> empty set, not an error (a
    freshly-cloned Skill install with no ignore list yet is valid)."""
    # Resolved through vault_manager.data_root() rather than a hardcoded
    # <vault>/.second-brain: after the 2026-09-03 config/vault split this
    # file moved with the rest of the App Database Folder, and reading the
    # old location silently returned an EMPTY ignore list -- so every
    # address the operator had deliberately ignored started getting a
    # Person note again, with nothing reporting it.
    import vault_manager
    path = vault_manager.data_root(vault_path) / _PERSON_IGNORE_LIST_FILE
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    return {entry.strip().lower() for entry in data.get("identifiers", []) if entry.strip()}

# Section-ownership guard (trimmed from app/data_access/section_ownership.py
# -- only this Skill's own caller is registered; everything else this
# module writes goes through the unconditional create_*/write_* paths,
# never replace_body_section).
_HUMAN_OWNED_HEADERS = frozenset({"## Personal Notes", "## Actions"})
_CALLER_ALLOW_LISTS = {
    "link_person_to_thread.link_person_to_thread": frozenset({"## Related"}),
    "capture_attachments.capture_attachments": frozenset({"## Files"}),
    "capture_file_link.capture_file_link": frozenset({"## Files"}),
}


class SectionWriteNotAllowed(PermissionError):
    pass


def _is_header_allowed(caller: str, header: str) -> bool:
    if header in _HUMAN_OWNED_HEADERS:
        return False
    return header in _CALLER_ALLOW_LISTS.get(caller, frozenset())


# ── slugs / frontmatter formatting ─────────────────────────────────────

def _slugify(text: str, max_len: int = 80) -> str:
    slug = _SLUG_INVALID_CHARS.sub("-", text).strip()
    return slug[:max_len] if slug else "untitled"


def clean_subject(subject: str) -> str:
    """Strips a leading "Re:"/"RE:" (repeated, case-insensitive) --
    shared by rename_thread.py (Thread directory naming) and
    ingest_email.py (message filename naming, 2026-08-21: operator wants
    the email's own title there, not the sender's name)."""
    return _LEADING_RE_PREFIX.sub("", subject).strip()


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


def rename_frontmatter_key(path: Path, old_key: str, new_key: str, new_value=None) -> bool:
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


def upsert_frontmatter_key(path: Path, key: str, value) -> bool:
    frontmatter, _ = read_note(path)
    if key not in frontmatter:
        return insert_frontmatter_key_if_missing(path, key, value)
    if frontmatter[key] == value:
        return False
    return rename_frontmatter_key(path, key, key, new_value=value)


# ── body-section primitives ─────────────────────────────────────────────

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
        raise SectionWriteNotAllowed(
            f"caller {caller!r} is not allowed to write header {header!r}"
        )
    text = path.read_text(encoding="utf-8")
    header_line_pattern = re.compile(r"^" + re.escape(header) + r"$", re.MULTILINE)
    header_match = header_line_pattern.search(text)
    if header_match is None:
        return False
    region_start = header_match.end()
    next_header_match = _BODY_SECTION_HEADER_PATTERN.search(text, region_start)
    region_end = next_header_match.start() if next_header_match else len(text)
    new_text = (
        text[:region_start] + "\n\n" + new_content.strip("\n") + "\n\n" + text[region_end:]
    )
    path.write_text(new_text, encoding="utf-8")
    return True


# ── Thread primitives ────────────────────────────────────────────────────

def list_thread_notes(vault_path: Path) -> list[Path]:
    threads_root = vault_path / _THREADS_SUBFOLDER
    if not threads_root.exists():
        return []
    return sorted(
        path for path in threads_root.glob("*/*.md")
        # is_file() guard: a captured attachment whose own original
        # filename ends in ".md" produces a files/<slug>.md/ COMPANION
        # DIRECTORY (write_file_companion's own naming convention) --
        # this glob matches it too, and read_text() on a directory raises
        # PermissionError on Windows. Same known gap already documented
        # and guarded in Second Brain's own list_all_note_paths.
        if path.parent.name == path.stem and path.is_file()
    )


def resolve_thread_directory(vault_path: Path, conversation_id: str) -> Path | None:
    for path in list_thread_notes(vault_path):
        frontmatter, _ = read_note(path)
        if frontmatter.get("conversation_id") == conversation_id:
            return path.parent
    return None


def thread_directory_paths(vault_path: Path, conversation_id: str) -> dict:
    concept_slug = _slugify(conversation_id)
    base = vault_path / _THREADS_SUBFOLDER / concept_slug
    return {
        "directory": base,
        "concept": base / f"{concept_slug}.md",
        "messages": base / "messages",
    }


def create_thread_note_baseline(
    vault_path: Path, conversation_id: str, thread_name: str, tags: list[str] | None = None
) -> str:
    paths = thread_directory_paths(vault_path, conversation_id)
    _write_frontmatter_note(
        paths["concept"],
        {
            "type": "Thread",
            "conversation_id": conversation_id,
            "tags": tags or [],
            "thread_name": thread_name,
            # 2026-08-21, operator: recurring capture jobs need to tell
            # "already summarized, nothing new" apart from "needs a
            # summary" without re-reading every Thread's body -- these two
            # timestamps are that signal. last_message_at is this Skill's
            # own field (kept current by update_thread_last_message_at,
            # below); last_summarized_at belongs to summarize-and-tag-
            # threads's own apply_thread_review.py -- never written here,
            # just reserved empty so every Thread has a consistent schema
            # regardless of which job touches it first.
            "last_message_at": "",
            "last_summarized_at": "",
        },
        "## Summary\n\n## Personal Notes\n\n## Actions\n\n## Related\n",
    )
    return str(paths["concept"])


def update_thread_last_message_at(vault_path: Path, conversation_id: str, received: str) -> bool:
    """Keeps a Thread's own `last_message_at` at the newest `received`
    timestamp seen across every ingest_email call for it -- messages can
    arrive out of order across pages, so this always takes the max rather
    than blindly overwriting. No-op (returns False) if the Thread doesn't
    exist yet or `received` isn't actually newer than what's already
    there. `received`'s own string form (`str(item.ReceivedTime)`, e.g.
    "2026-07-16 11:28:00.221000+00:00") sorts correctly as a plain string
    -- fixed-width, zero-padded, consistent UTC offset -- no datetime
    parsing needed."""
    directory = resolve_thread_directory(vault_path, conversation_id)
    if directory is None:
        return False
    concept_path = directory / f"{directory.name}.md"
    frontmatter, _ = read_note(concept_path)
    current = frontmatter.get("last_message_at") or ""
    if received <= current:
        return False
    return upsert_frontmatter_key(concept_path, "last_message_at", received)


def raw_message_note_path(
    vault_path: Path, conversation_id: str, message_id: str, received: str,
    readable_name: str | None = None,
) -> Path:
    directory = resolve_thread_directory(vault_path, conversation_id)
    messages_dir = (
        directory / "messages" if directory is not None
        else thread_directory_paths(vault_path, conversation_id)["messages"]
    )
    if readable_name is not None:
        # 2026-08-21 bug fix: date-only + sender name collapses right back
        # into indistinguishable filenames whenever the SAME sender posts
        # more than once in a thread on the same day (the common
        # back-and-forth case) -- both land on the same stem, and the
        # hash-suffix fallback below then makes the second one look like
        # "Name-a1b2c3d4.md", which in Obsidian's file view still just
        # reads "Name" -- no way to tell them apart or that there are two.
        # Including time-of-day (HH:MM, almost always unique per message)
        # fixes this directly and is more informative than a hash ever
        # was. The hash-suffix fallback stays as a safety net for a
        # genuine same-minute tie, now a rare edge case instead of the
        # common one.
        time_of_day = received[11:16].replace(":", "")
        parts = [received[:10]]
        if time_of_day:
            parts.append(time_of_day)
        parts.append(_slugify(readable_name))
        stem = " ".join(parts)
        candidate = messages_dir / f"{stem}.md"
        if not candidate.exists():
            return candidate
        existing_frontmatter, _ = read_note(candidate)
        if existing_frontmatter.get("message_id") == message_id:
            return candidate
        suffix = hashlib.sha256(message_id.encode("utf-8")).hexdigest()[:8]
        return messages_dir / f"{stem}-{suffix}.md"
    suffix = hashlib.sha256(message_id.encode("utf-8")).hexdigest()[:8]
    filename = f"{received[:10]}-{suffix}.md"
    return messages_dir / filename


def raw_message_note_exists(
    vault_path: Path, conversation_id: str, message_id: str, received: str,
    readable_name: str | None = None,
) -> bool:
    return raw_message_note_path(
        vault_path, conversation_id, message_id, received, readable_name
    ).exists()


def create_raw_message_note(
    vault_path: Path,
    conversation_id: str,
    message_id: str,
    received: str,
    sender: str,
    sender_email: str,
    subject: str,
    body: str,
    readable_name: str | None = None,
    participant_links: list[str] | None = None,
) -> str:
    path = raw_message_note_path(vault_path, conversation_id, message_id, received, readable_name)
    frontmatter = {
        "type": "RawMessage",
        "conversation_id": conversation_id,
        "message_id": message_id,
        "sender": sender,
        "sender_email": sender_email,
        "subject": subject,
        "received": received,
    }
    if participant_links is not None:
        frontmatter["participant_links"] = participant_links
    _write_frontmatter_note(path, frontmatter, body)
    return str(path)


def rename_thread_directory(old_directory: Path, new_directory: Path) -> Path:
    if old_directory == new_directory:
        return new_directory / f"{new_directory.name}.md"
    if new_directory.exists():
        raise FileExistsError(
            f"would overwrite existing Thread directory at {new_directory}"
        )
    old_slug = old_directory.name
    new_slug = new_directory.name
    old_directory.rename(new_directory)
    old_concept_path = new_directory / f"{old_slug}.md"
    new_concept_path = new_directory / f"{new_slug}.md"
    old_concept_path.rename(new_concept_path)
    return new_concept_path


# ── Files/OKF companion primitives ──────────────────────────────────────

def _file_type_tag(filename: str) -> str | None:
    """`type/<ext>` (e.g. `type/pdf`), matching this codebase's own
    established namespace/value tag convention (`customer/<slug>`,
    `kind/person`). None when the filename has no extension to derive one
    from -- never fabricated (e.g. an inline-image GUID filename with no
    suffix)."""
    ext = Path(filename).suffix.lstrip(".").lower()
    return f"type/{ext}" if ext else None


def write_file_companion(
    vault_path: Path,
    subfolder: Path,
    file_slug: str,
    original_filename: str,
    content: bytes,
    summary: str,
    source_thread: str | None = None,
    source_email: str | None = None,
) -> dict:
    slug = _slugify(file_slug)
    files_dir = subfolder / "files" / slug
    files_dir.mkdir(parents=True, exist_ok=True)
    file_path = files_dir / original_filename
    file_path.write_bytes(content)
    companion_path = files_dir / f"{slug}.md"
    frontmatter = {
        "type": "File",
        "file_slug": file_slug,
        "original_filename": original_filename,
    }
    type_tag = _file_type_tag(original_filename)
    if type_tag:
        frontmatter["tags"] = [type_tag]
    if source_thread is not None:
        frontmatter["source_thread"] = source_thread
    if source_email is not None:
        frontmatter["source_email"] = source_email
    _write_frontmatter_note(
        companion_path, frontmatter, f"## Summary\n\n{summary}\n\n## Personal Notes\n",
    )
    return {"file_path": str(file_path), "companion_path": str(companion_path)}


def link_file_to_thread(directory: Path, wikilink: str, *, caller: str) -> bool:
    """2026-08-21 bug fix: capture_attachments/capture_file_link were
    writing real file companion notes with zero reference back from the
    Thread's own concept note -- opening a Thread in Obsidian gave no
    indication it had any captured files at all, discoverable only by
    manually browsing into its files/ subfolder. Mirrors link_person_to_
    thread's own accumulate-into-a-section pattern, applied to a new
    `## Files` section instead of `## Related`. Idempotent -- calling
    twice for the same file adds the wikilink only once."""
    concept_path = directory / f"{directory.name}.md"
    insert_body_section_if_missing(concept_path, "## Files")
    existing = read_body_section(concept_path, "## Files")
    if wikilink in existing:
        return False
    lines = [line for line in existing.splitlines() if line.strip()]
    lines.append(f"- {wikilink}")
    replace_body_section(concept_path, "## Files", "\n".join(lines), caller=caller)
    return True


def write_file_link_companion(
    subfolder: Path,
    file_slug: str,
    url: str,
    source_thread: str | None = None,
    source_email: str | None = None,
) -> dict:
    slug = _slugify(file_slug)
    files_dir = subfolder / "files" / slug
    files_dir.mkdir(parents=True, exist_ok=True)
    companion_path = files_dir / f"{slug}.md"
    frontmatter = {"type": "File", "file_slug": file_slug, "url": url}
    if source_thread is not None:
        frontmatter["source_thread"] = source_thread
    if source_email is not None:
        frontmatter["source_email"] = source_email
    _write_frontmatter_note(
        companion_path, frontmatter, f"[{url}]({url})\n\n## Summary\n\n\n\n## Personal Notes\n",
    )
    return {"companion_path": str(companion_path)}


# ── Bare Person-note primitive (Capture-phase scope only -- see module
# docstring point 2: no company/Customer/Partner matching or hub-linking
# here, deliberately) ────────────────────────────────────────────────────

def _looks_like_real_email(value: str) -> bool:
    """A LegacyExchangeDN (Outlook's own fallback address when
    GetExchangeUser() resolution fails for an EX-type sender, e.g.
    "/o=ExchangeLabs/ou=Exchange Administrative Group
    (FYDIBOHF23SPDLT)/cn=Recipients/cn=...") has no "@" and starts with
    "/" -- trusting it as a real address is the same live BUG-036 the
    meeting-capture Skill's own identical copy of this function hit
    (found live 2026-08-23 on a meeting attendee); guarded here too per
    this file's own "kept in sync by hand" convention, even though no
    email-sourced instance has manifested on disk yet."""
    return "@" in value and not value.startswith("/")


def person_note_dedup_key(name: str, email: str | None) -> str:
    if email and _looks_like_real_email(email):
        return email.lower()
    return _slugify(name.lower())


def find_person_note_path(vault_path: Path, dedup_key: str) -> Path | None:
    """2026-08-21 bug fix: the original glob (`Customers/*/People/`, one
    level, and no Partners check at all) never matched a Person note
    create-companies-partners had moved into an AFFILIATE's own People/
    folder (e.g. Customers/Mubadala/Affiliates/Masdar/People/) or
    anywhere under Work/Partners/ -- live-confirmed to create a real,
    ambiguously-named duplicate bare Person note back in flat
    Work/People/ on a rerun after Job 3 had already filed that person
    (caught via meeting-capture's own first real run creating 3 such
    duplicates for already-filed Masdar contacts). `**/People/` (fully
    recursive, both roots) is the correct check -- a Person note can now
    live at any depth under either Customers/ or Partners/."""
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
    """Trimmed sibling of Second Brain's own
    people_extraction.ensure_person_note_for_captured_email -- creates or
    tops up a bare Person note (type/name/email/phone/linkedin/
    department/role/company/tags=["kind/person"]) at the flat Work/People/
    location, with NO Customer/Partner matching or hub-linking (that
    stays create-companies-partners's own job, see that Skill's own
    retag_people_by_domain). Skips (returns None) when email is blank,
    same contract as the source.

    department/role/company (2026-08-21, operator: "People need more
    fields (Department, Role)") come from Outlook's own GAL lookup when
    the caller has it (GetExchangeUser() only resolves for internal,
    Exchange-known senders/recipients -- blank for anyone external, which
    is correct, not a gap). `company` is the raw Exchange CompanyName
    string, a plain-text field distinct from -- and never a substitute
    for -- the real wikilinked Customer/Partner relationship
    retag_people_by_domain establishes separately; it's a redundant,
    human-readable signal for the many people who never resolve to a
    known hub note's own domain. insert_frontmatter_key_if_missing only
    ever adds a KEY that's entirely absent -- it never overwrites a real
    value that's already there, blank or not -- so re-running this with
    blank department/role/company on a note that already has real ones
    is always safe.

    2026-08-21, operator: skips (returns None) for any identifier in
    `.second-brain/person_ignore_list.json` -- the vault owner's own
    address, and a truncation-collision-prone unresolved Exchange DN,
    were showing up as Person notes and links on nearly every Thread/
    Meeting. Checked by exact, case-insensitive match on the raw `email`
    value (never a substring/prefix match -- a real similarly-named
    contact must never be silently swallowed by this list)."""
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
