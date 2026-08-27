"""CLI entry point: Step 3 of the company/partner discovery sequence --
reads the operator's own curated .second-brain/Settings/Entities.md (Step 1's mechanical
output, hand-edited: Ignore/Created flags set, Aliases/Affiliate of
filled in) and creates the real Customer/Partner (and their Affiliate)
hub notes from it. Never touches Threads, never summarizes -- that's
Step 4, separate and later.

Structure built (operator's own spec, 2026-08-21):

    Work/Customers/<Name>/
        <Name>.md              -- hub file; "## Affiliates" lists any
                                   Affiliates below (wikilinks down).
                                   Deliberately NO People list here --
                                   Obsidian's own backlinks panel shows
                                   who belongs to it, since every moved
                                   Person note carries a link UP instead.
        People/
            <person>.md         -- existing Work/People/ notes on this
                                   entity's own domain, moved here, each
                                   with a "**Customer:** [[Name]]" (or
                                   **Partner:**) line inserted.
        Affiliates/
            <Affiliate>/
                <Affiliate>.md   -- same shape one level deeper.
                People/
                    <person>.md

    Work/Partners/<Name>/        -- identical shape; Partners can have
                                     Affiliates too.

Two-pass: every top-level entry (blank "Affiliate of") is created first,
THEN every Affiliate. An Affiliate whose named parent has no top-level
entry anywhere in Entities.md (Companies or Partners) does NOT get
skipped (operator, 2026-08-21: "Add the Parent if it's not in the file,
it will come later when we start Parsing the files") -- a bare
placeholder top-level entry (blank Domain/Aliases) is auto-created for
it in the same section as the child that named it, reported separately
in the result as `auto_created_parents` so the operator knows to fill in
its real details later (Step 4, or by hand). Idempotent: an entry
already `Created: Yes` is skipped for creation (its path is still
resolved, so its own Affiliates can still be processed); an
already-moved Person note (target path already exists) is left alone.
Rewrites Entities.md at the end, flipping `Created: No` -> `Yes` for
everything this run actually created (including auto-created parents) --
every other field (including any hand-typed Aliases/Affiliate of text)
is preserved byte-faithfully by re-rendering from the same parsed
values, not by blind find-replace.

Usage:
    python create_companies_partners.py --vault-path P [--entities-name Entities.md]

Prints a summary: created / skipped_ignored / skipped_already /
skipped_unconfirmed_parent / people_moved.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

_SLUG_INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')
_FRONTMATTER_LINE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*):\s?(.*)$")
_LIST_ITEM_PATTERN = re.compile(r'"((?:[^"\\]|\\.)*)"')
_BODY_SECTION_HEADER_PATTERN = re.compile(r"^## .+$", re.MULTILINE)

_KNOWN_FIELDS = {"Company Name", "Aliases", "Affiliate of", "Created", "Ignore", "Domain", "Deleted"}

# Section-ownership guard, matching the same discipline every other
# Skill's own vault_lib.py uses. Kept as a per-header allow-list (not one
# single caller) since 2026-08-21: this module now writes two different
# headers on two different note kinds -- "## Affiliates" on a hub note
# (link_affiliate_to_parent) and "## Related" on a Thread's own concept
# note (retag_threads_by_participant_company, alongside the Person
# wikilinks email-thread-capture's own link_person_to_thread.py already
# puts there -- a different Skill's own module, so this is a deliberate
# cross-skill write onto the same header, not a conflict: both add
# wikilinks, never remove either's).
_CALLER = "create_companies_partners.link_affiliate_to_parent"
_THREAD_RELATED_CALLER = "create_companies_partners.retag_threads_by_participant_company"
_MEETING_RELATED_CALLER = "create_companies_partners.retag_meetings_by_attendee_company"
_CALLER_ALLOW_LISTS = {
    _CALLER: frozenset({"## Affiliates"}),
    _THREAD_RELATED_CALLER: frozenset({"## Related"}),
    _MEETING_RELATED_CALLER: frozenset({"## Related"}),
}

def _slugify(text: str, max_len: int = 80) -> str:
    slug = _SLUG_INVALID_CHARS.sub("-", text).strip()
    return slug[:max_len] if slug else "untitled"


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
    if header not in _CALLER_ALLOW_LISTS.get(caller, frozenset()):
        raise PermissionError(f"caller {caller!r} is not allowed to write {header!r}")
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


# ── Entities.md parsing / re-rendering ──────────────────────────────────

def parse_entities(content: str) -> list[dict]:
    section = None
    entries: list[dict] = []
    current: dict | None = None
    for line in content.splitlines():
        if line.startswith("## Companies"):
            section = "customer"
            continue
        if line.startswith("## Partners"):
            section = "partner"
            continue
        if line.startswith("### "):
            if current is not None:
                entries.append(current)
            current = {"section": section, "heading": line[4:].strip(), "fields": {}}
            continue
        stripped = line.strip()
        if current is not None and stripped and ":" in stripped:
            key, _, value = stripped.partition(":")
            key = key.strip()
            if key in _KNOWN_FIELDS:
                current["fields"][key] = value.strip()
    if current is not None:
        entries.append(current)
    return entries


def render_entities(entries: list[dict]) -> str:
    lines = [
        "# Entities",
        "",
        "Step 1 of the company/partner discovery sequence -- mechanical,",
        "domain-based grouping only, no LLM, no judgment about which of",
        "these are real Customers vs. Partners vs. noise.",
        "",
        "**Edit this file by hand.** `Created`/`Ignore` are Yes/No flags a",
        "later pipeline reads -- set `Ignore: Yes` instead of deleting an",
        "entry (a notification sender, a one-off vendor -- not a real",
        "business relationship); leave `Created: No` until that later,",
        "separate pipeline has actually made the hub note for it. Use",
        "`Aliases` to merge a duplicate that slipped through under a",
        "different domain (rare -- domain grouping already prevents most",
        "of this). Move real partners into `## Partners` below.",
        "",
        "## Companies",
        "",
    ]
    for entry in entries:
        if entry["section"] != "customer":
            continue
        _render_entry(lines, entry)
    lines.append("## Partners")
    lines.append("")
    for entry in entries:
        if entry["section"] != "partner":
            continue
        _render_entry(lines, entry)
    return "\n".join(lines)


def _render_entry(lines: list[str], entry: dict) -> None:
    f = entry["fields"]
    lines.append(f"### {entry['heading']}")
    lines.append("")
    lines.append(f"\tCompany Name: {f.get('Company Name', '')}")
    lines.append("")
    lines.append(f"\tAliases: {f.get('Aliases', '')}")
    lines.append("")
    lines.append(f"\tAffiliate of: {f.get('Affiliate of', '')}")
    lines.append("")
    lines.append(f"\tCreated: {f.get('Created', 'No')}")
    lines.append("")
    lines.append(f"\tIgnore: {f.get('Ignore', 'No')}")
    lines.append("")
    lines.append(f"\tDomain: {f.get('Domain', '')}")
    lines.append("")
    # Deleted: Yes -- soft-delete field (2026-08-27, see the matching
    # comment in find_new_entities.py's own _render_entry for the full
    # reasoning). A Deleted: Yes row also always carries Ignore: Yes
    # (set together by the app's own Settings > Vault > Entities UI), so
    # the existing Ignore: Yes checks in Pass 1/Pass 2 above already skip
    # it -- no separate Deleted check needed in the hub-creation logic.
    lines.append(f"\tDeleted: {f.get('Deleted', 'No')}")
    lines.append("")
    lines.append("")


# ── hub note creation / linking ─────────────────────────────────────────

def _entry_name(entry: dict) -> str:
    return (entry["fields"].get("Company Name") or entry["heading"]).strip()


def _write_or_backfill_identifying_header(path: Path, identifying_name: str) -> None:
    """Mirrors Second Brain's own vault_writer.py primitive of the same
    name exactly (operator, 2026-08-21: "Like we had in Second Brain"):
    fresh creation writes `# {name}\n\n` as the whole file; an
    already-existing, already-headered file (first line already starts
    with "# ") is left untouched -- idempotent on a re-run, and never
    clobbers real content a later job (not built yet) writes into log.md/
    captures.md."""
    header = f"# {identifying_name}\n\n"
    if not path.exists():
        path.write_text(header, encoding="utf-8")
        return
    text = path.read_text(encoding="utf-8")
    if text.split("\n", 1)[0].startswith("# "):
        return
    path.write_text(header + text, encoding="utf-8")


def _tag_slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9/]+", "-", text.lower()).strip("-")
    return slug or "untitled"


def _split_domains(domain_field: str) -> list[str]:
    """A hub note's own `Domain:`/`domain` field can name more than one
    domain, comma-separated (operator, 2026-08-21: "I want both
    core42.ai and core42.ae to be Partner Core42" -- two real registrar
    domains for the same organization). Every match site treats this
    field as a set, not a single string."""
    return [d.strip().lower() for d in domain_field.split(",") if d.strip()]


def create_hub_note(md_path: Path, name: str, kind_section: str, domain: str, aliases: str, affiliate_of_name: str) -> None:
    entity_type = "Customer" if kind_section == "customer" else "Partner"
    alias_list = [a.strip() for a in aliases.split(",") if a.strip()]
    # 2026-08-21 bug fix: a hub note never carried its own self-tag
    # (operator: "Mubadala for example wasn't tagged customer/mubadala")
    # -- matches every other note kind in this vault, which always tags
    # itself (e.g. a Person note's own "kind/person").
    self_tag = f"{kind_section}/{_tag_slug(md_path.stem)}"
    frontmatter = {"type": entity_type, "name": name, "tags": [self_tag]}
    if domain:
        frontmatter["domain"] = domain
    if alias_list:
        frontmatter["aliases"] = alias_list
    frontmatter["affiliate_of"] = affiliate_of_name or ""

    # Name-prefixed (operator, 2026-08-21: "[Customer Name]-log.md and
    # same for Capture so I can see the files later") -- a bare "log.md"/
    # "captures.md" would collide across every Customer/Partner (same
    # filename, different folders), both as an ambiguous [[log]] wikilink
    # target AND when just browsing a flat file listing. The name prefix
    # fixes both at once.
    slug = md_path.stem
    log_path = md_path.parent / f"{slug}-log.md"
    captures_path = md_path.parent / f"{slug}-captures.md"
    body = (
        "## Affiliates\n\n"
        f"## Log & Captures\n\n- [[{log_path.stem}|Log]]\n- [[{captures_path.stem}|Captures]]\n"
    )
    _write_frontmatter_note(md_path, frontmatter, body)
    # 2026-08-21 bug fix: log.md/captures.md had no frontmatter at all
    # (operator: "log and Capture file doesn't contain the Front
    # Matter") -- every other note in this vault has one.
    _ensure_frontmatter(log_path, {"type": "Log", "name": f"{name} Log", "parent": f"[[{md_path.stem}]]"})
    _ensure_frontmatter(captures_path, {"type": "Captures", "name": f"{name} Captures", "parent": f"[[{md_path.stem}]]"})
    _write_or_backfill_identifying_header(log_path, name)
    _write_or_backfill_identifying_header(captures_path, name)


def _ensure_frontmatter(path: Path, frontmatter: dict) -> None:
    """Backfills a frontmatter block onto a file that doesn't have one
    yet (log.md/captures.md were originally created as a bare identifying
    header with no frontmatter at all) -- a no-op once it already has
    one, so this is safe to call on every run, not just fresh creation."""
    if not path.exists():
        _write_frontmatter_note(path, frontmatter, "")
        return
    text = path.read_text(encoding="utf-8")
    if text.startswith("---\n"):
        return
    frontmatter_lines = ["---"]
    for key, value in frontmatter.items():
        frontmatter_lines.append(f"{key}: {_format_frontmatter_value(value)}")
    frontmatter_lines.append("---")
    path.write_text("\n".join(frontmatter_lines) + "\n\n" + text, encoding="utf-8")


def link_affiliate_to_parent(parent_md: Path, affiliate_md: Path) -> None:
    wikilink = f"[[{affiliate_md.stem}]]"
    insert_body_section_if_missing(parent_md, "## Affiliates")
    existing = read_body_section(parent_md, "## Affiliates")
    if wikilink in existing:
        return
    lines = [line for line in existing.splitlines() if line.strip()]
    lines.append(f"- {wikilink}")
    replace_body_section(parent_md, "## Affiliates", "\n".join(lines), caller=_CALLER)


def _iter_hub_notes(vault_path: Path):
    for root_name, kind in (("Customers", "customer"), ("Partners", "partner")):
        root = vault_path / "Work" / root_name
        if not root.exists():
            continue
        for md_path in root.rglob("*.md"):
            if not md_path.is_file():
                continue
            if md_path.stem.endswith("-log") or md_path.stem.endswith("-captures"):
                continue
            if md_path.parent.name != md_path.stem:
                continue
            yield md_path, kind


def merge_tags(path: Path, new_tags: list[str]) -> bool:
    """Unions new_tags into path's own `tags` frontmatter list, never
    overwriting existing ones. Returns True if the file changed."""
    frontmatter, _ = read_note(path)
    existing = list(frontmatter.get("tags") or [])
    merged = existing + [t for t in new_tags if t not in existing]
    if merged == existing:
        return False
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---\n", 4)
    if end == -1:
        return False
    frontmatter_block = text[: end + 1]
    rest = text[end + 1:]
    lines = frontmatter_block.splitlines(keepends=True)
    new_line = f"tags: {_format_frontmatter_value(merged)}\n"
    replaced = False
    for i, line in enumerate(lines):
        match = _FRONTMATTER_LINE.match(line.rstrip("\n"))
        if match and match.group(1) == "tags":
            lines[i] = new_line
            replaced = True
            break
    if not replaced:
        lines.insert(-1, new_line)
    path.write_text("".join(lines) + rest, encoding="utf-8")
    return True


def move_people_for_domain(vault_path: Path, domain: str, target_people_dir: Path, entity_md: Path, kind_section: str) -> int:
    domains = _split_domains(domain)
    if not domains:
        return 0
    flat_people_dir = vault_path / "Work" / "People"
    if not flat_people_dir.exists():
        return 0
    link_label = "Customer" if kind_section == "customer" else "Partner"
    wikilink = f"[[{entity_md.stem}]]"
    tag = f"{kind_section}/{_tag_slug(entity_md.stem)}"
    moved = 0
    for person_path in sorted(flat_people_dir.glob("*.md")):
        if not person_path.is_file():
            continue
        frontmatter, _ = read_note(person_path)
        email = (frontmatter.get("email") or "").strip().lower()
        if not email or "@" not in email:
            continue
        if email.rsplit("@", 1)[1] not in domains:
            continue
        target_people_dir.mkdir(parents=True, exist_ok=True)
        new_path = target_people_dir / person_path.name
        if new_path.exists():
            continue  # already moved on a prior run -- idempotent
        person_path.rename(new_path)
        insert_body_line_if_missing(new_path, f"**{link_label}:** {wikilink}")
        merge_tags(new_path, [tag])
        moved += 1
    return moved


def retag_people_by_domain(vault_path: Path) -> dict:
    """2026-08-21 bug fix: a Person note already moved into its own
    Customer/Partner/Affiliate People/ folder (by a prior run of THIS
    script, or manually) never got its own `tags`/wikilink -- only newly
    MOVED people did, via move_people_for_domain above. This is the
    retroactive, idempotent, re-runnable version of the same rule,
    scanning every Person note vault-wide by ITS OWN email domain against
    every real hub note's own domain -- never by "was this person a
    participant on a thread that got tagged with company X" (that was
    apply_thread_review.py's own wrong logic, removed 2026-08-21: an
    internal @core42.ai person got tagged with every customer/partner
    mentioned on every thread they were ever CC'd on, which is not what
    "this person belongs to this company" means). A person whose own
    domain matches nothing real (internal Core42 staff, personal email
    domains, etc.) is correctly never tagged at all -- no fallback, no
    guess. Returns {"tagged": [...], "linked": [...]}."""
    tagged: list[str] = []
    linked: list[str] = []
    for hub_md, kind in _iter_hub_notes(vault_path):
        frontmatter, _ = read_note(hub_md)
        domains = _split_domains(frontmatter.get("domain") or "")
        if not domains:
            continue
        tag = f"{kind}/{_tag_slug(hub_md.stem)}"
        link_label = "Customer" if kind == "customer" else "Partner"
        wikilink = f"[[{hub_md.stem}]]"
        for person_path in vault_path.rglob("*.md"):
            if not person_path.is_file():
                continue
            person_frontmatter, _ = read_note(person_path)
            if person_frontmatter.get("type") != "Person":
                continue
            email = (person_frontmatter.get("email") or "").strip().lower()
            if not email or "@" not in email or email.rsplit("@", 1)[1] not in domains:
                continue
            if merge_tags(person_path, [tag]):
                tagged.append(str(person_path))
            if insert_body_line_if_missing(person_path, f"**{link_label}:** {wikilink}"):
                linked.append(str(person_path))
    return {"tagged": tagged, "linked": linked}


_WIKILINK_STEM = re.compile(r"^\[\[(.+)\]\]$")


def _wikilink_stem(link: str) -> str:
    match = _WIKILINK_STEM.match(link.strip())
    return match.group(1) if match else link.strip()


def merge_list_field(path: Path, field_name: str, new_values: list[str]) -> bool:
    """Unions new_values into path's own `field_name` frontmatter list
    (creating it if absent), never overwriting existing entries -- same
    contract as merge_tags, generalized to any list-valued field (used
    for `company_links` on RawMessage notes, below)."""
    frontmatter, _ = read_note(path)
    existing = list(frontmatter.get(field_name) or [])
    merged = existing + [v for v in new_values if v not in existing]
    if merged == existing:
        return False
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---\n", 4)
    if end == -1:
        return False
    frontmatter_block = text[: end + 1]
    rest = text[end + 1:]
    lines = frontmatter_block.splitlines(keepends=True)
    new_line = f"{field_name}: {_format_frontmatter_value(merged)}\n"
    replaced = False
    for i, line in enumerate(lines):
        match = _FRONTMATTER_LINE.match(line.rstrip("\n"))
        if match and match.group(1) == field_name:
            lines[i] = new_line
            replaced = True
            break
    if not replaced:
        lines.insert(-1, new_line)
    path.write_text("".join(lines) + rest, encoding="utf-8")
    return True


def _iter_thread_notes(vault_path: Path):
    threads_root = vault_path / "Work" / "Threads"
    if not threads_root.exists():
        return
    for md_path in sorted(threads_root.glob("*/*.md")):
        if not md_path.is_file() or md_path.parent.name != md_path.stem:
            continue
        yield md_path


def _build_person_email_index(vault_path: Path) -> dict[str, str]:
    """stem (lowercased) -> email, for every real Person note vault-wide
    -- built once so retag_threads_by_participant_company doesn't rescan
    the whole vault per participant_links entry."""
    index: dict[str, str] = {}
    for path in vault_path.rglob("*.md"):
        if not path.is_file():
            continue
        frontmatter, _ = read_note(path)
        if frontmatter.get("type") != "Person":
            continue
        email = (frontmatter.get("email") or "").strip().lower()
        if email:
            index[path.stem.lower()] = email
    return index


def _build_domain_company_index(vault_path: Path) -> list[tuple[list[str], str, str]]:
    """[(domains, kind, hub_stem), ...] for every real hub note with a
    domain. `kind` ("customer"/"partner") is carried so callers that need
    to build a `customer/<slug>`/`partner/<slug>` tag (not just a
    "## Related" wikilink, which doesn't care) don't have to re-derive it
    themselves."""
    entries: list[tuple[list[str], str, str]] = []
    for hub_md, kind in _iter_hub_notes(vault_path):
        frontmatter, _ = read_note(hub_md)
        domains = _split_domains(frontmatter.get("domain") or "")
        if domains:
            entries.append((domains, kind, hub_md.stem))
    return entries


def retag_threads_by_participant_company(vault_path: Path) -> dict:
    """2026-08-21, operator: "Threads and Emails now need to contain in
    Related the Company as we included before in Related Section" --
    mirrors retag_people_by_domain's own domain-match rule one hop
    further out: a Thread genuinely involves a company if one of its own
    participants' own email domain matches that company's own domain.
    This is a real, mechanical fact about who's actually on the thread --
    not the wrong "cascade every company mentioned onto every
    participant" logic that was removed from apply_thread_review.py
    earlier the same day; here the direction is reversed (thread -> its
    real participants' real companies), which is legitimate and exactly
    what "Related" already means for the Person wikilinks
    link_person_to_thread.py puts there.

    Writes:
      - each RawMessage's own `company_links` frontmatter list (that
        message's own participants only, via merge_list_field).
      - each Thread's own "## Related" body section (the union across
        every message under it) -- alongside whatever Person wikilinks
        are already there, never removing them.

    Every internal Core42 person is core42.ai or core42.ae, and Core42 is
    now a real Partner hub note (2026-08-21) -- so yes, [[Core42]] will
    show up in "## Related" on nearly every Thread. That's not a bug:
    nearly every real Thread genuinely does have a Core42 participant
    (whoever's mailbox this is, if no one else on the other side).

    Idempotent, re-runnable via --retag-only as new hub notes, domains,
    or messages show up. Returns {"threads_updated": [...],
    "messages_updated": [...]}."""
    person_emails = _build_person_email_index(vault_path)
    domain_index = _build_domain_company_index(vault_path)
    threads_updated: list[str] = []
    messages_updated: list[str] = []

    for thread_md in _iter_thread_notes(vault_path):
        frontmatter, _ = read_note(thread_md)
        if frontmatter.get("type") != "Thread":
            continue
        messages_dir = thread_md.parent / "messages"
        if not messages_dir.exists():
            continue
        thread_companies: set[str] = set()
        for message_path in sorted(messages_dir.glob("*.md")):
            if not message_path.is_file():
                continue
            message_frontmatter, _ = read_note(message_path)
            participant_links = message_frontmatter.get("participant_links") or []
            message_companies: set[str] = set()
            for link in participant_links:
                email = person_emails.get(_wikilink_stem(link).lower())
                if not email or "@" not in email:
                    continue
                domain = email.rsplit("@", 1)[1]
                for domains, _kind, hub_stem in domain_index:
                    if domain in domains:
                        message_companies.add(hub_stem)
            if message_companies:
                new_links = [f"[[{stem}]]" for stem in sorted(message_companies)]
                if merge_list_field(message_path, "company_links", new_links):
                    messages_updated.append(str(message_path))
            thread_companies |= message_companies

        if not thread_companies:
            continue
        insert_body_section_if_missing(thread_md, "## Related")
        existing = read_body_section(thread_md, "## Related")
        lines = [line for line in existing.splitlines() if line.strip()]
        changed = False
        for stem in sorted(thread_companies):
            wikilink = f"[[{stem}]]"
            if wikilink in existing:
                continue
            lines.append(f"- {wikilink}")
            changed = True
        if changed:
            replace_body_section(thread_md, "## Related", "\n".join(lines), caller=_THREAD_RELATED_CALLER)
            threads_updated.append(str(thread_md))

    return {"threads_updated": threads_updated, "messages_updated": messages_updated}


def _iter_meeting_notes(vault_path: Path):
    """Yields (path, is_series_concept) for every real Meeting note --
    a one-time meeting's own single file, a recurring series' own
    concept file, and every occurrence file under its own occurrences/
    (mirrors _iter_thread_notes' "directory name == file stem" concept-
    file test, plus a second pass into occurrences/ for a series)."""
    meetings_root = vault_path / "Work" / "Meetings"
    if not meetings_root.exists():
        return
    for concept_path in sorted(meetings_root.glob("*/*.md")):
        if not concept_path.is_file() or concept_path.parent.name != concept_path.stem:
            continue
        frontmatter, _ = read_note(concept_path)
        if frontmatter.get("type") != "Meeting":
            continue
        is_series = bool(frontmatter.get("recurrence"))
        yield concept_path, is_series
        if is_series:
            occurrences_dir = concept_path.parent / "occurrences"
            if occurrences_dir.exists():
                for occurrence_path in sorted(occurrences_dir.glob("*.md")):
                    if occurrence_path.is_file():
                        yield occurrence_path, False


def _resolve_companies_for_wikilinks(wikilinks: list[str], person_emails: dict[str, str], domain_index) -> set[tuple[str, str]]:
    resolved: set[tuple[str, str]] = set()
    for link in wikilinks:
        email = person_emails.get(_wikilink_stem(link).lower())
        if not email or "@" not in email:
            continue
        domain = email.rsplit("@", 1)[1]
        for domains, kind, hub_stem in domain_index:
            if domain in domains:
                resolved.add((kind, hub_stem))
    return resolved


def _apply_company_resolution(path: Path, resolved: set[tuple[str, str]], updated: list[str]) -> None:
    """Shared tag + "## Related" application, used both for a meeting's
    own real attendees and for a recurring series' concept note's own
    rolled-up union across its occurrences."""
    if not resolved:
        return
    tags = [f"{kind}/{_tag_slug(stem)}" for kind, stem in resolved]
    changed = merge_tags(path, tags)
    insert_body_section_if_missing(path, "## Related")
    existing = read_body_section(path, "## Related")
    lines = [line for line in existing.splitlines() if line.strip()]
    for _kind, stem in sorted(resolved, key=lambda kv: kv[1]):
        wikilink = f"[[{stem}]]"
        if wikilink in existing:
            continue
        lines.append(f"- {wikilink}")
        changed = True
    if changed:
        replace_body_section(path, "## Related", "\n".join(lines), caller=_MEETING_RELATED_CALLER)
    if changed and str(path) not in updated:
        updated.append(str(path))


def retag_meetings_by_attendee_company(vault_path: Path) -> dict:
    """2026-08-21: the Meetings equivalent of retag_threads_by_
    participant_company -- a meeting genuinely involves a company if one
    of its own attendees' own email domain matches that company's own
    domain. One-time meetings and recurring occurrence files carry real
    attendees directly (their own `attendees` frontmatter, populated at
    capture time by meeting-capture's own ingest_meeting.py) and get
    tagged/linked from those. A recurring series' own concept note has no
    attendees of its own (`attendees` stays `[]` by design -- attendance
    can vary occurrence to occurrence) -- its tags/"## Related" instead
    roll up the UNION of every occurrence captured so far, mirroring how
    a Thread's own concept note accumulates from its messages.

    Idempotent, re-runnable via --retag-only as new hub notes, domains,
    or meetings show up. Returns {"meetings_updated": [...]}."""
    person_emails = _build_person_email_index(vault_path)
    domain_index = _build_domain_company_index(vault_path)
    meetings_updated: list[str] = []
    series_rollup: dict[Path, set[tuple[str, str]]] = {}

    for meeting_path, is_series_concept in _iter_meeting_notes(vault_path):
        if is_series_concept:
            continue  # handled after its occurrences, via series_rollup below
        frontmatter, _ = read_note(meeting_path)
        resolved = _resolve_companies_for_wikilinks(frontmatter.get("attendees") or [], person_emails, domain_index)
        _apply_company_resolution(meeting_path, resolved, meetings_updated)

        if meeting_path.parent.name == "occurrences":
            series_directory = meeting_path.parent.parent
            concept_path = series_directory / f"{series_directory.name}.md"
            if concept_path.exists():
                series_rollup.setdefault(concept_path, set()).update(resolved)

    for concept_path, resolved in series_rollup.items():
        _apply_company_resolution(concept_path, resolved, meetings_updated)

    return {"meetings_updated": meetings_updated}


def backfill_hub_note_metadata(vault_path: Path) -> dict:
    """2026-08-21 bug fix: create_hub_note's own self-tag and log/
    captures-frontmatter fixes only apply at CREATION time (guarded by
    `if not md_path.exists()` at every call site) -- a hub note created
    by an EARLIER run, before those fixes existed, never gets touched
    again and stays missing both (operator: "Mubadala for example wasn't
    tagged customer/mubadala", "log and Capture file doesn't contain the
    Front Matter"). This is the retroactive, idempotent, re-runnable
    backfill for every hub note that already exists, using the same
    non-destructive primitives (merge_tags, _ensure_frontmatter) so a
    hub note's own body content (once someone starts adding real notes
    to it) is never touched."""
    self_tagged: list[str] = []
    log_captures_backfilled: list[str] = []
    for hub_md, kind in _iter_hub_notes(vault_path):
        tag = f"{kind}/{_tag_slug(hub_md.stem)}"
        if merge_tags(hub_md, [tag]):
            self_tagged.append(str(hub_md))
        frontmatter, _ = read_note(hub_md)
        name = frontmatter.get("name") or hub_md.stem
        log_path = hub_md.parent / f"{hub_md.stem}-log.md"
        captures_path = hub_md.parent / f"{hub_md.stem}-captures.md"
        before = (log_path.exists() and not log_path.read_text(encoding="utf-8").startswith("---\n"))
        _ensure_frontmatter(log_path, {"type": "Log", "name": f"{name} Log", "parent": f"[[{hub_md.stem}]]"})
        _ensure_frontmatter(captures_path, {"type": "Captures", "name": f"{name} Captures", "parent": f"[[{hub_md.stem}]]"})
        if before:
            log_captures_backfilled.append(str(hub_md))
    return {"self_tagged": self_tagged, "log_captures_backfilled": log_captures_backfilled}


_ENGAGEMENT_CONFIG_FILE = "engagement_classification_config.json"


def _load_engagement_config(vault_path: Path) -> dict:
    """Real, accessible config (never a hardcoded literal) for WHICH hub
    note(s) are the root of "internal", per the operator's own explicit
    2026-08-22 rule ("G42 and its Affiliates are internal"). Self-heals a
    missing file to the operator-confirmed default on first read, same
    pattern as meeting_thread_link_config.py/person_ignore_list.json."""
    path = vault_path / ".second-brain" / _ENGAGEMENT_CONFIG_FILE
    default = {"internal_roots": ["G42"]}
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(default, indent=2), encoding="utf-8")
        return default
    data = json.loads(path.read_text(encoding="utf-8"))
    if "internal_roots" not in data or not data["internal_roots"]:
        data["internal_roots"] = default["internal_roots"]
    return data


def _compute_internal_hub_stems(vault_path: Path) -> set[str]:
    """The configured internal_roots (default: G42) plus every hub whose
    own `affiliate_of` chain resolves to one of them, transitively -- an
    Affiliate-of-an-Affiliate is still internal. Real hub note data, not
    a hardcoded name list -- Core42/Inception/Presight fall out of this
    automatically today because their own `affiliate_of` field already
    says "G42", not because they're named here."""
    config = _load_engagement_config(vault_path)
    roots = {r.strip().lower() for r in config.get("internal_roots", [])}
    internal: set[str] = set()
    affiliate_of_map: dict[str, str] = {}
    for hub_md, _kind in _iter_hub_notes(vault_path):
        if hub_md.stem.lower() in roots:
            internal.add(hub_md.stem)
        frontmatter, _ = read_note(hub_md)
        affiliate_of = (frontmatter.get("affiliate_of") or "").strip()
        if affiliate_of:
            affiliate_of_map[hub_md.stem] = affiliate_of
    changed = True
    while changed:
        changed = False
        for stem, parent in affiliate_of_map.items():
            if stem in internal:
                continue
            if parent in internal or parent.strip().lower() in roots:
                internal.add(stem)
                changed = True
    return internal


def _upsert_namespaced_tag(path: Path, namespace: str, value: str) -> bool:
    """Like merge_tags, but for a namespace that only ever holds ONE
    value at a time (engagement/customer vs. engagement/partner vs.
    engagement/internal are mutually exclusive) -- removes any existing
    tag in this namespace before adding the new one, so a Thread/Meeting
    whose real classification changes over time (a customer joins a
    previously internal-only thread) doesn't end up wearing two
    contradictory tags forever."""
    frontmatter, _ = read_note(path)
    existing = list(frontmatter.get("tags") or [])
    new_tag = f"{namespace}/{value}"
    filtered = [t for t in existing if not t.startswith(f"{namespace}/")]
    merged = filtered + [new_tag]
    if merged == existing:
        return False
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---\n", 4)
    if end == -1:
        return False
    frontmatter_block = text[: end + 1]
    rest = text[end + 1:]
    lines = frontmatter_block.splitlines(keepends=True)
    new_line = f"tags: {_format_frontmatter_value(merged)}\n"
    replaced = False
    for i, line in enumerate(lines):
        m = _FRONTMATTER_LINE.match(line.rstrip("\n"))
        if m and m.group(1) == "tags":
            lines[i] = new_line
            replaced = True
            break
    if not replaced:
        lines.insert(-1, new_line)
    path.write_text("".join(lines) + rest, encoding="utf-8")
    return True


def tag_engagement_type(vault_path: Path) -> dict:
    """2026-08-22, operator's own explicit rule: classify every Thread
    and Meeting as exactly one of `engagement/customer`,
    `engagement/partner`, or `engagement/internal` --

      - customer: at least one real Customer company is involved.
      - partner: at least one real (non-internal) Partner company is
        involved, AND no Customer is.
      - internal: neither -- the operator's own explicit fallback, not
        "zero external domains present" as a separate hard gate (a
        Thread whose only non-internal participants are noise/Ignore:Yes
        domains, or that already has no resolvable participants at all,
        correctly falls through to internal too).
      - "If there is a Partner and Customer engaged then its Customer"
        (verbatim) -- Customer always wins the tie.

    Mechanical only -- reads the `customer/<slug>`/`partner/<slug>` tags
    retag_threads_by_participant_company/retag_meetings_by_attendee_
    company already maintain, never re-derives company membership itself
    from participants. MUST run after both of those in the same pass --
    depends on their tags being current. G42's own Affiliates (Core42,
    Inception, Presight -- anything whose own `affiliate_of` chain
    resolves to G42, see _compute_internal_hub_stems) never count as a
    real Partner for this classification, even though they're filed
    under Entities.md's own `## Partners` section -- "G42 and its
    Affiliates are internal" (operator, verbatim).

    Idempotent, re-runnable via --retag-only. Returns
    {"threads_updated": [...], "meetings_updated": [...]}."""
    internal_slugs = {_tag_slug(stem) for stem in _compute_internal_hub_stems(vault_path)}

    def classify(tags: list[str]) -> str:
        if any(t.startswith("customer/") for t in tags):
            return "customer"
        if any(t.startswith("partner/") and t.split("/", 1)[1] not in internal_slugs for t in tags):
            return "partner"
        return "internal"

    threads_updated: list[str] = []
    for thread_md in _iter_thread_notes(vault_path):
        frontmatter, _ = read_note(thread_md)
        if frontmatter.get("type") != "Thread":
            continue
        classification = classify(frontmatter.get("tags") or [])
        if _upsert_namespaced_tag(thread_md, "engagement", classification):
            threads_updated.append(str(thread_md))

    meetings_updated: list[str] = []
    for meeting_path, _is_series_concept in _iter_meeting_notes(vault_path):
        frontmatter, _ = read_note(meeting_path)
        if frontmatter.get("type") != "Meeting":
            continue
        classification = classify(frontmatter.get("tags") or [])
        if _upsert_namespaced_tag(meeting_path, "engagement", classification):
            meetings_updated.append(str(meeting_path))

    return {"threads_updated": threads_updated, "meetings_updated": meetings_updated}


def build(vault_path: Path, entities_path: Path) -> dict:
    content = entities_path.read_text(encoding="utf-8-sig")
    entries = parse_entities(content)

    created: list[str] = []
    skipped_ignored: list[str] = []
    skipped_already: list[str] = []
    auto_created_parents: list[str] = []
    people_moved_total = 0

    top_level_paths: dict[str, tuple[Path, Path, str]] = {}  # name.lower() -> (folder, md_path, section)

    # Pass 1: top-level entries (blank "Affiliate of")
    for entry in entries:
        if (entry["fields"].get("Affiliate of") or "").strip():
            continue  # handled in pass 2
        name = _entry_name(entry)
        if entry["fields"].get("Ignore", "No").strip().lower() == "yes":
            skipped_ignored.append(name)
            continue
        root = vault_path / ("Work/Customers" if entry["section"] == "customer" else "Work/Partners")
        folder = root / _slugify(name)
        md_path = folder / f"{_slugify(name)}.md"
        already = entry["fields"].get("Created", "No").strip().lower() == "yes"
        if not md_path.exists():
            create_hub_note(md_path, name, entry["section"], entry["fields"].get("Domain", ""), entry["fields"].get("Aliases", ""), "")
        top_level_paths[name.lower()] = (folder, md_path, entry["section"])
        if already:
            skipped_already.append(name)
            continue
        moved = move_people_for_domain(vault_path, entry["fields"].get("Domain", ""), folder / "People", md_path, entry["section"])
        people_moved_total += moved
        entry["fields"]["Created"] = "Yes"
        created.append(name)

    # Pass 2: affiliates (needs pass 1's resolved parent paths)
    for entry in entries:
        affiliate_of = (entry["fields"].get("Affiliate of") or "").strip()
        if not affiliate_of:
            continue
        name = _entry_name(entry)
        if entry["fields"].get("Ignore", "No").strip().lower() == "yes":
            skipped_ignored.append(name)
            continue
        parent = top_level_paths.get(affiliate_of.lower())
        if parent is None:
            # 2026-08-21, operator: "Add the Parent if it's not in the
            # file, it will come later when we start Parsing the files"
            # -- auto-create a bare top-level placeholder (no domain, no
            # aliases -- we don't know them yet) in the SAME section as
            # the child that named it, rather than skipping the child.
            # Step 4 (or the operator by hand) fills in the placeholder's
            # own details later; it's still real enough to nest an
            # Affiliate under today.
            parent_entry = {
                "section": entry["section"],
                "heading": affiliate_of,
                "fields": {"Company Name": affiliate_of, "Aliases": "", "Affiliate of": "", "Created": "No", "Ignore": "No", "Domain": ""},
            }
            entries.append(parent_entry)
            parent_root = vault_path / ("Work/Customers" if entry["section"] == "customer" else "Work/Partners")
            parent_folder = parent_root / _slugify(affiliate_of)
            parent_md = parent_folder / f"{_slugify(affiliate_of)}.md"
            if not parent_md.exists():
                create_hub_note(parent_md, affiliate_of, entry["section"], "", "", "")
            top_level_paths[affiliate_of.lower()] = (parent_folder, parent_md, entry["section"])
            parent_entry["fields"]["Created"] = "Yes"
            created.append(affiliate_of)
            auto_created_parents.append(affiliate_of)
            parent = top_level_paths[affiliate_of.lower()]
        parent_folder, parent_md, parent_section = parent
        affiliate_folder = parent_folder / "Affiliates" / _slugify(name)
        affiliate_md = affiliate_folder / f"{_slugify(name)}.md"
        already = entry["fields"].get("Created", "No").strip().lower() == "yes"
        if not affiliate_md.exists():
            create_hub_note(affiliate_md, name, parent_section, entry["fields"].get("Domain", ""), entry["fields"].get("Aliases", ""), affiliate_of)
        link_affiliate_to_parent(parent_md, affiliate_md)
        if already:
            skipped_already.append(name)
            continue
        moved = move_people_for_domain(vault_path, entry["fields"].get("Domain", ""), affiliate_folder / "People", affiliate_md, parent_section)
        people_moved_total += moved
        entry["fields"]["Created"] = "Yes"
        created.append(name)

    entities_path.write_text(render_entities(entries), encoding="utf-8")

    # Always retag/relink at the end -- catches BOTH people this run just
    # moved AND any already-placed people from an earlier run that never
    # got their own tag/link (see retag_people_by_domain's own docstring).
    retag_result = retag_people_by_domain(vault_path)
    backfill_result = backfill_hub_note_metadata(vault_path)
    thread_result = retag_threads_by_participant_company(vault_path)
    meeting_result = retag_meetings_by_attendee_company(vault_path)
    engagement_result = tag_engagement_type(vault_path)

    return {
        "created": created,
        "auto_created_parents": auto_created_parents,
        "skipped_ignored": skipped_ignored,
        "skipped_already": skipped_already,
        "people_moved": people_moved_total,
        "people_retagged": len(retag_result["tagged"]),
        "people_relinked": len(retag_result["linked"]),
        "hub_notes_self_tagged": len(backfill_result["self_tagged"]),
        "hub_notes_log_captures_backfilled": len(backfill_result["log_captures_backfilled"]),
        "threads_related_updated": len(thread_result["threads_updated"]),
        "messages_company_linked": len(thread_result["messages_updated"]),
        "meetings_updated": len(meeting_result["meetings_updated"]),
        "engagement_threads_tagged": len(engagement_result["threads_updated"]),
        "engagement_meetings_tagged": len(engagement_result["meetings_updated"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--entities-name", default="Entities.md")
    parser.add_argument(
        "--retag-only", action="store_true",
        help="Skip Entities.md entirely -- just re-run the domain-based Person tag/link pass "
             "against whatever Customer/Partner/Affiliate hub notes already exist.",
    )
    args = parser.parse_args()

    vault_path = Path(args.vault_path)

    if args.retag_only:
        retag_result = retag_people_by_domain(vault_path)
        backfill_result = backfill_hub_note_metadata(vault_path)
        thread_result = retag_threads_by_participant_company(vault_path)
        meeting_result = retag_meetings_by_attendee_company(vault_path)
        engagement_result = tag_engagement_type(vault_path)
        print(json.dumps({
            "people_tagged": len(retag_result["tagged"]),
            "people_linked": len(retag_result["linked"]),
            "hub_notes_self_tagged": len(backfill_result["self_tagged"]),
            "hub_notes_log_captures_backfilled": len(backfill_result["log_captures_backfilled"]),
            "threads_related_updated": len(thread_result["threads_updated"]),
            "messages_company_linked": len(thread_result["messages_updated"]),
            "meetings_updated": len(meeting_result["meetings_updated"]),
            "engagement_threads_tagged": len(engagement_result["threads_updated"]),
            "engagement_meetings_tagged": len(engagement_result["meetings_updated"]),
        }, ensure_ascii=False))
        return 0

    # Settings/Entities.md under .second-brain -- see find_new_entities.py's
    # own comment for the full 2026-08-27 relocation reasoning.
    entities_path = vault_path / ".second-brain" / "Settings" / args.entities_name
    if not entities_path.exists():
        print(json.dumps({"error": f"{entities_path} does not exist -- run entity-domain-extraction first"}))
        return 1

    result = build(vault_path, entities_path)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
