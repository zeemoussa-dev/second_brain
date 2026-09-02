"""CLI entry point: Step 3 of the company/partner discovery sequence --
reads the operator's own curated .second-brain/Settings/Entities.md (Step 1's mechanical
output, hand-edited: Ignore/Created flags set, Aliases/Affiliate of
filled in) and creates the real Customer/Partner (and their Affiliate)
hub notes from it. Never touches Threads, never summarizes -- that's
Step 4, separate and later.

`vault_manager.py`-based replacement for the original hand-rolled version
(2026-08-31, operator: "Full migration" -- the same "Why we need to create
script everytime we add a skill We Generalized so we don't do that" fix
already applied to Opportunities). The hub+log+captures note itself, the
Affiliate<->parent resolution (including the real "Add the Parent if it's
not in the file" auto-create), and the "## Affiliates" back-link are all
now the engine's own real `create()` (a `customer`/`partner` Template.json,
`parent.required: false`, `parent.on_missing: "auto_create"`,
`root.children` for log/captures, `parent.link_back_section`) instead of
this file's own hand-rolled slugify/collision/frontmatter/linking logic.
Entities.md's own parsing/rendering, the domain-based Person/Thread/
Meeting retag passes, and the engagement-type classifier are UNCHANGED,
reused as-is -- real, working, company-review-specific business logic,
not part of the write-mechanics problem `vault_manager.py` solves. Tag/
line-insert writes (`merge_tags`, `upsert_namespaced_tag`,
`insert_body_line_if_missing`) now call the engine's own shared, generic
versions of the same real primitives this file's own copies were
independently reimplementing (confirmed by direct reading, 2026-08-30).

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

import vault_manager as vm

_SLUG_INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')
_BODY_SECTION_HEADER_PATTERN = re.compile(r"^## .+$", re.MULTILINE)

_KNOWN_FIELDS = {"Company Name", "Aliases", "Affiliate of", "Created", "Ignore", "Domain", "Deleted"}

_CUSTOMER_TEMPLATE_ID = "customer"
_PARTNER_TEMPLATE_ID = "partner"

# REQ-SB-87-US-01-T04 -- one stable caller identity per SCRIPT, reused
# across every vm.create()/vm.modify_section() call site in this file
# (ADR-017's own per-caller section-access trust boundary).
_VM_CALLER = "create_companies_partners"

# Section-ownership guard, matching the same discipline every other
# Skill's own vault_lib.py uses -- kept LOCAL (not promoted into
# vault_manager.py) since it's about which FUNCTION IN THIS SCRIPT may
# write which header on a Thread/Meeting note that isn't even created
# through a Customer/Partner template, not a generic engine concern.
# "## Affiliates" no longer needs a caller here at all -- vault_manager's
# own `create()` writes that back-link itself now, via
# `parent.link_back_section`.
_THREAD_RELATED_CALLER = "create_companies_partners.retag_threads_by_participant_company"
_MEETING_RELATED_CALLER = "create_companies_partners.retag_meetings_by_attendee_company"
_CALLER_ALLOW_LISTS = {
    _THREAD_RELATED_CALLER: frozenset({"## Related"}),
    _MEETING_RELATED_CALLER: frozenset({"## Related"}),
}


def _slugify(text: str, max_len: int = 80) -> str:
    slug = _SLUG_INVALID_CHARS.sub("-", text).strip()
    return slug[:max_len] if slug else "untitled"


def insert_body_section_if_missing(path: Path, header: str) -> bool:
    text = path.read_text(encoding="utf-8")
    header_line_pattern = re.compile(r"^" + re.escape(header) + r"$", re.MULTILINE)
    if header_line_pattern.search(text) is not None:
        return False
    separator = "" if text.endswith("\n") else "\n"
    path.write_text(text + separator + f"\n{header}\n", encoding="utf-8")
    return True


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


# ── hub note creation (vault_manager.py's own create(), not hand-rolled) ─

def _entry_name(entry: dict) -> str:
    return (entry["fields"].get("Company Name") or entry["heading"]).strip()


def _hub_root(section: str) -> str:
    return "Customers" if section == "customer" else "Partners"


def _hub_path(vault_path: Path, name: str, section: str) -> Path:
    folder = vault_path / "Work" / _hub_root(section) / _slugify(name)
    return folder / f"{_slugify(name)}.md"


def _affiliate_path(parent_folder: Path, name: str) -> Path:
    folder = parent_folder / "Affiliates" / _slugify(name)
    return folder / f"{_slugify(name)}.md"


def _hub_frontmatter(name: str, domain: str, aliases: str) -> dict:
    frontmatter: dict = {"name": name}
    if domain:
        frontmatter["domain"] = domain
    alias_list = [a.strip() for a in aliases.split(",") if a.strip()]
    if alias_list:
        frontmatter["aliases"] = alias_list
    return frontmatter


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


def _ensure_frontmatter(path: Path, frontmatter: dict) -> None:
    """Backfills a frontmatter block onto a file that doesn't have one
    yet (a hub note's own log.md/captures.md, created by a PRE-migration
    run of this script, was originally a bare identifying header with no
    frontmatter at all) -- a no-op once it already has one, so this is
    safe to call on every run, not just fresh creation. Kept local -- a
    narrow, one-off legacy-repair shape (plain string fields only:
    `type`/`name`/`parent`), not a general enough primitive to promote
    into vault_manager.py."""
    if not path.exists():
        vm.write_note(path, frontmatter, "")
        return
    text = path.read_text(encoding="utf-8")
    if text.startswith("---\n"):
        return
    lines = ["---"]
    for key, value in frontmatter.items():
        escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'{key}: "{escaped}"')
    lines.append("---")
    path.write_text("\n".join(lines) + "\n\n" + text, encoding="utf-8")


def _iter_hub_notes(vault_path: Path):
    """Real bug, found live 2026-08-31: an Opportunity's own real path
    (`Work/Customers/<Customer>/Opportunities/<Title>/<Title>.md`) matches
    the SAME "folder named after itself" shape a Customer/Partner hub note
    has -- without a real `type` check, this wrongly caught every
    Opportunity too (bogus self-tag, spurious blank -log/-captures
    siblings), confirmed live against 10 of the operator's own real
    Opportunities. `type` is the one field that actually distinguishes a
    hub note from anything else nested under Work/Customers or
    Work/Partners that happens to share its own-folder shape."""
    expected_type = {"customer": "Customer", "partner": "Partner"}
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
            frontmatter, _ = vm.read_note(md_path)
            if frontmatter.get("type") != expected_type[kind]:
                continue
            yield md_path, kind


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
        frontmatter, _ = vm.read_note(person_path)
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
        vm.insert_body_line_if_missing(new_path, f"**{link_label}:** {wikilink}")
        vm.merge_tags(new_path, [tag])
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
        frontmatter, _ = vm.read_note(hub_md)
        domains = _split_domains(frontmatter.get("domain") or "")
        if not domains:
            continue
        tag = f"{kind}/{_tag_slug(hub_md.stem)}"
        link_label = "Customer" if kind == "customer" else "Partner"
        wikilink = f"[[{hub_md.stem}]]"
        for person_path in vault_path.rglob("*.md"):
            if not person_path.is_file():
                continue
            person_frontmatter, _ = vm.read_note(person_path)
            if person_frontmatter.get("type") != "Person":
                continue
            email = (person_frontmatter.get("email") or "").strip().lower()
            if not email or "@" not in email or email.rsplit("@", 1)[1] not in domains:
                continue
            if vm.merge_tags(person_path, [tag]):
                tagged.append(str(person_path))
            if vm.insert_body_line_if_missing(person_path, f"**{link_label}:** {wikilink}"):
                linked.append(str(person_path))
    return {"tagged": tagged, "linked": linked}


_WIKILINK_STEM = re.compile(r"^\[\[(.+)\]\]$")


def _wikilink_stem(link: str) -> str:
    match = _WIKILINK_STEM.match(link.strip())
    return match.group(1) if match else link.strip()


def merge_list_field(path: Path, field_name: str, new_values: list[str]) -> bool:
    """Unions new_values into path's own `field_name` frontmatter list
    (creating it if absent), never overwriting existing entries -- same
    contract as vault_manager's own `merge_tags`, generalized to any
    list-valued field (used for `company_links` on RawMessage notes,
    below). Kept local -- vault_manager.py's own `merge_tags` is
    specifically the `tags` field; there's no real caller elsewhere in
    this vault yet for an arbitrary-field version, so it hasn't been
    promoted."""
    frontmatter, body = vm.read_note(path)
    existing = list(frontmatter.get(field_name) or [])
    merged = existing + [v for v in new_values if v not in existing]
    if merged == existing:
        return False
    frontmatter[field_name] = merged
    vm.write_note(path, frontmatter, body)
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
        frontmatter, _ = vm.read_note(path)
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
        frontmatter, _ = vm.read_note(hub_md)
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
        frontmatter, _ = vm.read_note(thread_md)
        if frontmatter.get("type") != "Thread":
            continue
        messages_dir = thread_md.parent / "messages"
        if not messages_dir.exists():
            continue
        thread_companies: set[str] = set()
        for message_path in sorted(messages_dir.glob("*.md")):
            if not message_path.is_file():
                continue
            message_frontmatter, _ = vm.read_note(message_path)
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
        existing = vm.get_section_content(thread_md, "## Related")
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
        frontmatter, _ = vm.read_note(concept_path)
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
    changed = vm.merge_tags(path, tags)
    insert_body_section_if_missing(path, "## Related")
    existing = vm.get_section_content(path, "## Related")
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
        frontmatter, _ = vm.read_note(meeting_path)
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
    """2026-08-21 bug fix: hub-note self-tagging and log/captures-
    frontmatter only applied at CREATION time in the pre-migration
    script -- a hub note created by an EARLIER run, before those fixes
    existed, never got touched again and stayed missing both (operator:
    "Mubadala for example wasn't tagged customer/mubadala", "log and
    Capture file doesn't contain the Front Matter"). This is the
    retroactive, idempotent, re-runnable backfill for every hub note
    that already exists -- including ones now created via
    vault_manager.py's own `create()`, which doesn't self-tag a hub note
    at creation time either (no `parent.derived_tag` fits "tag with your
    OWN name", only "tag with your PARENT's name") -- using the same
    non-destructive primitives (vm.merge_tags, local _ensure_frontmatter)
    so a hub note's own body content (once someone starts adding real
    notes to it) is never touched."""
    self_tagged: list[str] = []
    log_captures_backfilled: list[str] = []
    for hub_md, kind in _iter_hub_notes(vault_path):
        tag = f"{kind}/{_tag_slug(hub_md.stem)}"
        if vm.merge_tags(hub_md, [tag]):
            self_tagged.append(str(hub_md))
        frontmatter, _ = vm.read_note(hub_md)
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
        frontmatter, _ = vm.read_note(hub_md)
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

    def _already_classified(tags: list[str], classification: str) -> bool:
        return f"engagement/{classification}" in tags

    threads_updated: list[str] = []
    for thread_md in _iter_thread_notes(vault_path):
        frontmatter, _ = vm.read_note(thread_md)
        if frontmatter.get("type") != "Thread":
            continue
        tags = frontmatter.get("tags") or []
        classification = classify(tags)
        if _already_classified(tags, classification):
            continue  # vm.upsert_namespaced_tag has no idempotency check of its own -- skip a real no-op write
        vm.upsert_namespaced_tag(thread_md, "engagement", classification)
        threads_updated.append(str(thread_md))

    meetings_updated: list[str] = []
    for meeting_path, _is_series_concept in _iter_meeting_notes(vault_path):
        frontmatter, _ = vm.read_note(meeting_path)
        if frontmatter.get("type") != "Meeting":
            continue
        tags = frontmatter.get("tags") or []
        classification = classify(tags)
        if _already_classified(tags, classification):
            continue
        vm.upsert_namespaced_tag(meeting_path, "engagement", classification)
        meetings_updated.append(str(meeting_path))

    return {"threads_updated": threads_updated, "meetings_updated": meetings_updated}


def build(vault_path: Path, entities_path: Path) -> dict:
    content = entities_path.read_text(encoding="utf-8-sig")
    entries = parse_entities(content)

    customer_template = vm.load_template(vault_path, _CUSTOMER_TEMPLATE_ID)
    partner_template = vm.load_template(vault_path, _PARTNER_TEMPLATE_ID)

    def _template_for(section: str) -> dict:
        return customer_template if section == "customer" else partner_template

    created: list[str] = []
    skipped_ignored: list[str] = []
    skipped_already: list[str] = []
    skipped_unresolved: list[str] = []  # a real cycle in its own Affiliate-of chain -- never fabricated, always reported
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
        section = entry["section"]
        md_path = _hub_path(vault_path, name, section)
        already = entry["fields"].get("Created", "No").strip().lower() == "yes"
        if not md_path.exists():
            vm.create(
                vault_path, _template_for(section), title=name, note_name=_hub_root(section),
                frontmatter=_hub_frontmatter(name, entry["fields"].get("Domain", ""), entry["fields"].get("Aliases", "")),
                caller=_VM_CALLER,
            )
        top_level_paths[name.lower()] = (md_path.parent, md_path, section)
        if already:
            skipped_already.append(name)
            continue
        moved = move_people_for_domain(vault_path, entry["fields"].get("Domain", ""), md_path.parent / "People", md_path, section)
        people_moved_total += moved
        entry["fields"]["Created"] = "Yes"
        created.append(name)

    # Pass 2: affiliates (recursive resolution -- an entry's own "Affiliate
    # of" parent may ITSELF be another affiliate, not just a top-level
    # entry: real, live data has genuine 3-level chains, e.g.
    # G42 -> M42 -> Diaverum. The original flat single-pass version only
    # ever checked already-resolved top-level entries, so a real
    # affiliate-of-an-affiliate silently fell into the "unknown parent"
    # branch below and crashed trying to re-create an already-existing
    # note (found live 2026-09-02). `_resolve_affiliate_entry` resolves
    # (and creates, if needed) on demand, memoizing into `top_level_paths`
    # so file order between a child and its own multi-level parent never
    # matters, and refuses to recurse through a real cycle
    # (A affiliate-of B affiliate-of ... A) rather than looping forever.
    entries_by_name: dict[str, dict] = {}
    for entry in entries:
        entries_by_name.setdefault(_entry_name(entry).lower(), entry)

    def _resolve_affiliate_entry(entry: dict, resolving: set[str]) -> tuple[Path, Path, str] | None:
        """Returns this entry's real (folder, md_path, section), creating
        it -- and, recursively, any of its own unresolved affiliate
        parents -- as needed. Returns None if this entry cannot be
        resolved at all: a real cycle in its own Affiliate-of chain
        (A affiliate-of B affiliate-of ... A), or a chain that runs
        through an Ignored entry. Critically, None here means NOTHING is
        created for this entry -- the caller must never treat None as
        "unknown, go auto-create a placeholder" once the parent NAME was
        found among real entries; that distinction is what stops a real
        cycle from silently producing a duplicate/orphaned placeholder
        note instead of a clean refusal (found live testing this fix,
        2026-09-02 -- the first version of this recursion conflated the
        two and duplicated a note under a fabricated placeholder for
        exactly this case)."""
        name = _entry_name(entry)
        key = name.lower()
        if key in top_level_paths:
            return top_level_paths[key]
        if key in resolving:
            return None  # real cycle -- refuse to recurse forever
        if entry["fields"].get("Ignore", "No").strip().lower() == "yes":
            return None  # same precedent Pass 1 already sets: an ignored entry is never a usable parent
        resolving.add(key)
        try:
            affiliate_of = (entry["fields"].get("Affiliate of") or "").strip()
            if not affiliate_of:
                return None  # a blank-Affiliate-of entry only ever gets here via the placeholder path below, which returns before recursing further; kept honest, not expected in practice
            parent_key = affiliate_of.lower()
            parent = top_level_paths.get(parent_key)
            if parent is None:
                parent_entry = entries_by_name.get(parent_key)
                if parent_entry is not None:
                    # A REAL, known entry names this parent -- resolve it
                    # recursively. If THAT fails (cycle/ignore), this entry
                    # is unresolvable too -- refuse cleanly, never fall
                    # through to auto-creating a placeholder under a name
                    # that's already a real, known (if currently stuck)
                    # entry elsewhere in the file.
                    parent = _resolve_affiliate_entry(parent_entry, resolving)
                    if parent is None:
                        skipped_unresolved.append(name)
                        return None
                else:
                    # Genuinely unknown parent name -- not a single entry
                    # anywhere in the file references it. 2026-08-21,
                    # operator: "Add the Parent if it's not in the file, it
                    # will come later when we start Parsing the files" --
                    # auto-create a bare top-level placeholder (no domain,
                    # no aliases -- we don't know them yet) rather than
                    # skip the child.
                    parent_section = entry["section"]
                    parent_md = _hub_path(vault_path, affiliate_of, parent_section)
                    if not parent_md.exists():
                        vm.create(
                            vault_path, _template_for(parent_section), title=affiliate_of, note_name=_hub_root(parent_section),
                            caller=_VM_CALLER,
                        )
                    placeholder_entry = {
                        "section": parent_section,
                        "heading": affiliate_of,
                        "fields": {"Company Name": affiliate_of, "Aliases": "", "Affiliate of": "", "Created": "Yes", "Ignore": "No", "Domain": ""},
                    }
                    entries.append(placeholder_entry)
                    entries_by_name.setdefault(parent_key, placeholder_entry)
                    parent = (parent_md.parent, parent_md, parent_section)
                    top_level_paths[parent_key] = parent
                    created.append(affiliate_of)
                    auto_created_parents.append(affiliate_of)
            parent_folder, parent_md, parent_section = parent
            affiliate_md = _affiliate_path(parent_folder, name)
            already = entry["fields"].get("Created", "No").strip().lower() == "yes"
            if not affiliate_md.exists():
                # parent_value=affiliate_of -- the engine's own resolve_parent
                # finds parent_md (already guaranteed to exist above), auto-
                # derives note_name from it (_child_note_name), and writes
                # the "## Affiliates" back-link onto parent_md itself
                # (parent.link_back_section) -- replaces this file's own
                # former hand-rolled link_affiliate_to_parent entirely.
                vm.create(
                    vault_path, _template_for(parent_section), title=name,
                    frontmatter=_hub_frontmatter(name, entry["fields"].get("Domain", ""), entry["fields"].get("Aliases", "")),
                    parent_value=affiliate_of,
                    caller=_VM_CALLER,
                )
            result = (affiliate_md.parent, affiliate_md, parent_section)
            top_level_paths[key] = result
            if already:
                skipped_already.append(name)
            else:
                nonlocal people_moved_total
                people_moved_total += move_people_for_domain(
                    vault_path, entry["fields"].get("Domain", ""), affiliate_md.parent / "People", affiliate_md, parent_section,
                )
                entry["fields"]["Created"] = "Yes"
                created.append(name)
            return result
        finally:
            resolving.discard(key)

    for entry in entries:
        affiliate_of = (entry["fields"].get("Affiliate of") or "").strip()
        if not affiliate_of:
            continue
        name = _entry_name(entry)
        if entry["fields"].get("Ignore", "No").strip().lower() == "yes":
            skipped_ignored.append(name)
            continue
        _resolve_affiliate_entry(entry, set())

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
        # dict.fromkeys, not set() -- a cycle's own entries can each be
        # visited more than once (direct outer-loop traversal AND
        # recursion from the other cycle member), appending the same name
        # more than once; de-duped here, preserving first-seen order,
        # rather than at every append site.
        "skipped_unresolved": list(dict.fromkeys(skipped_unresolved)),
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
