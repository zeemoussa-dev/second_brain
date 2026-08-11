"""Writes markdown notes into the Obsidian vault (app.config.settings.vault_path).
No staging/promotion step — per MEMORY.md's decision, anything written here is
immediately part of the trusted vault.
"""
from __future__ import annotations

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
_FRONTMATTER_LINE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*):\s?(.*)$")


def _slugify(text: str, max_len: int = 80) -> str:
    slug = _SLUG_INVALID_CHARS.sub("-", text).strip()
    return slug[:max_len] if slug else "untitled"


def _tag_slug(text: str) -> str:
    """Obsidian tags can't contain spaces — lowercase, non-alphanumeric runs
    collapsed to a single hyphen, e.g. 'Department of Government Enablement'
    -> 'department-of-government-enablement'."""
    slug = _TAG_INVALID_CHARS.sub("-", text.lower()).strip("-")
    return slug or "untitled"


def build_tags(customer: str, kind: str) -> list[str]:
    """Hierarchical Obsidian tags mirroring the folder structure, so notes
    stay findable by customer/kind via search/graph view independent of
    where they physically live — the point raised when a note sits in
    Unsorted/ but you already suspect which customer it's really for."""
    return [f"customer/{_tag_slug(customer)}", f"kind/{_tag_slug(kind)}"]


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
