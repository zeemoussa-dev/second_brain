"""Shared "ensure this email sender's Person note exists and is up to
date, linking it to their company's Customer hub note when that company
is a known customer" orchestration (REQ-SB-10) — the one mechanism used
by both the one-time retrofit (retrofit_people_from_emails, over every
already-captured Email note) and email_classification.py's per-write
capture hook (ensure_person_note_for_captured_email, going forward).
Follows ADR-003's layering and the tag_backfill.py / vault_restructure.py
/ customer_hub_linking.py precedent of one business module per
maintenance operation — and is the first business module that composes
another business module (customer_hub_linking.py's granular hub-note
primitives) rather than only data_access; see architecture.md's explicit
note that this is an intentional, permitted horizontal call within the
business layer, not an ADR-003 boundary violation.
"""
from __future__ import annotations

import re
from pathlib import Path

from app.business import customer_hub_linking, partner_hub_linking, vault_indexing
from app.data_access import vault_writer

# Well-known personal/free email-provider domains — deliberately a fixed,
# hardcoded set (unlike list_known_customers/list_known_kinds, which are
# vault-derived): the universe of major personal email providers is a
# small, externally-stable set with no relationship to this vault's own
# content, so there is no vault signal that could ever grow or shrink it
# the way real customer/kind values do (architecture.md). Extend this
# constant directly if a real captured sender surfaces one that's missing.
_PERSONAL_EMAIL_DOMAINS = frozenset({
    "gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com",
    "msn.com", "yahoo.com", "ymail.com", "icloud.com", "me.com", "aol.com",
    "protonmail.com", "proton.me", "gmx.com", "mail.com", "yandex.com",
    "zoho.com",
})


def derive_company_from_email(sender_email: str) -> str | None:
    """Derives a display-name company from a sender's email domain — the
    only company signal available on a captured Email note (there is no
    separate "company" field anywhere in the existing schema). Takes the
    substring after "@", lowercases it, and checks it against
    _PERSONAL_EMAIL_DOMAINS; a match yields no company at all (Scenario 5
    — tag and link both absent). Otherwise the company display name is
    derived from the domain's first label — "core42.ai" -> "Core42"
    (label[0].upper() + label[1:]) — matching the resolved schema's own
    worked example verbatim. Returns None when sender_email is blank or
    has no "@" (Scenario 9's blank-sender_email case is actually filtered
    one layer up, before this function is ever called, but this guard
    keeps the function safe to call standalone)."""
    if not sender_email or "@" not in sender_email:
        return None
    domain = sender_email.rsplit("@", 1)[1].lower()
    if domain in _PERSONAL_EMAIL_DOMAINS:
        return None
    label = domain.split(".", 1)[0]
    if not label:
        return None
    return label[0].upper() + label[1:]


def find_matching_customer(company: str | None) -> str | None:
    """Compares company against every name vault_writer.list_known_customers()
    returns, by tag-slug equality (e.g. "core42" vs "Core42" vs "CORE42"
    all match) rather than exact string equality — reuses the exact
    slugging rule tags already use (vault_writer.tag_slug) instead of
    inventing a second normalization scheme. Returns the matching known
    customer's original (non-slugified) name — the exact string
    customer_hub_linking's hub-note primitives expect — or None when
    company is blank or matches no known customer."""
    if not company:
        return None
    target_slug = vault_writer.tag_slug(company)
    for customer in vault_writer.list_known_customers():
        if vault_writer.tag_slug(customer) == target_slug:
            return customer
    return None


def find_matching_partner(company: str | None) -> str | None:
    """Mirrors find_matching_customer exactly, against
    vault_writer.list_known_partners() instead of
    vault_writer.list_known_customers() (ADR-009). Returns the
    matching known partner's original (non-slugified) name, or None
    when company is blank or matches no known partner."""
    if not company:
        return None
    target_slug = vault_writer.tag_slug(company)
    for partner in vault_writer.list_known_partners():
        if vault_writer.tag_slug(partner) == target_slug:
            return partner
    return None


def ensure_person_note(name: str, email: str | None, customer: str | None = None) -> dict:
    """The shared "ensure this person's Person note exists and is up to
    date" operation, called once as a one-time batch
    (retrofit_people_from_emails) and once as a per-write hook
    (ensure_person_note_for_captured_email, meeting_classification.py's
    own attendee loop). Creates a baseline note if missing, or tops up
    any missing baseline frontmatter keys if it already exists (Scenarios
    2 and 6), without touching a key already present or the body.

    `email` may now be None/"" (REQ-SB-71-US-03-T03, ADR-048 Decision 6)
    — the real, no-longer-silently-skipped no-email-attendee case
    (meeting_classification.py's own former `if not email: continue`
    gap). `customer` (new, optional, defaults to None — PUBLIC SIGNATURE
    otherwise unchanged, so email_classification.py's own existing
    2-positional-argument calls need zero change) is the CALLER's own
    already-derived Customer, used ONLY as the nesting Customer for the
    no-email case (there is no email domain of this person's own to
    derive one from — the ONLY Customer signal available for them at
    all); an email-resolvable person always nests under their OWN
    email-domain-matched Customer (or the flat fallback if it doesn't
    match one), exactly per Scenario 6's own "never force-nested under a
    Customer they don't genuinely belong to" — `customer` is never used
    to override an email-resolvable person's own matched_customer, even
    when the two differ. Logged as a scope-internal judgement call
    (Implementation Log) — the task's own Notes leave the exact parameter
    shape open, locking only the outcome (Scenario 4).

    `find_person_note_path` is checked FIRST, vault-wide — an
    already-existing note (email-keyed or name-keyed) is topped up in
    place, NEVER moved or duplicated, even when this call's own newly-
    derived Customer differs from where the note already lives
    (Scenario 5 — the existing note stays put; the calling Meeting's own
    unchanged upsert_attendee_links wikilink mechanism is what actually
    links the OTHER Customer's relevant note to it, no new linking
    mechanism). Only when no note exists anywhere yet is a NEW one
    created, nested under the matched Customer or, absent one, at the
    flat Work/People/ fallback (Scenario 6, operator-confirmed
    2026-08-18).

    Derives the person's company from their email domain (None when no
    email) and checks it against known Customers first (unchanged) —
    only when no Customer match is found does it check known Partners
    (ADR-009: customer/<slug> and partner/<slug> are mutually
    exclusive, so at most one of customer_matched/partner_matched is
    ever non-None). On a confirmed match (either kind), ensures that
    company's hub note exists and links this Person note to it, calling
    the matching module's two granular primitives directly (never a
    combined unconditional-creation entry point), since an arbitrary
    derived company is very often not a real customer or partner. A
    company matching neither gets its company/<slug> tag and nothing
    else; no company at all gets neither. Re-checking both matches on
    every call (not just at creation) is what makes Scenario 8 work — a
    company that later becomes a known customer or partner gets its
    wikilink added retroactively on the next call, without touching
    anything else. Returns {"note_path": str, "created": bool,
    "company": str | None, "customer_matched": str | None,
    "partner_matched": str | None, "linked": bool}."""
    company = derive_company_from_email(email) if email else None
    tags = vault_writer.build_person_tags(company)
    dedup_key = vault_writer.person_note_dedup_key(name, email)
    matched_customer = find_matching_customer(company)
    nesting_customer = matched_customer if email else (matched_customer or customer)

    existing_note_path = vault_writer.find_person_note_path(dedup_key)
    if existing_note_path is not None:
        note_path = existing_note_path
        vault_writer.ensure_person_note_baseline_frontmatter(note_path, name, email, tags)
        created = False
    else:
        note_path = vault_writer.person_note_path(dedup_key, nesting_customer)
        vault_writer.create_person_note_baseline(note_path, name, email, tags)
        created = True

    matched_partner = None
    linked = False
    if matched_customer:
        customer_hub_linking.ensure_customer_hub_note(matched_customer)
        linked = customer_hub_linking.link_note_to_customer_hub(note_path, matched_customer)
    else:
        matched_partner = find_matching_partner(company)
        if matched_partner:
            partner_hub_linking.ensure_partner_hub_note(matched_partner)
            linked = partner_hub_linking.link_note_to_partner_hub(note_path, matched_partner)

    return {
        "note_path": str(note_path),
        "created": created,
        "company": company,
        "customer_matched": matched_customer,
        "partner_matched": matched_partner,
        "linked": linked,
    }


def ensure_person_note_for_captured_email(sender_name: str, sender_email: str) -> dict | None:
    """Per-write hook: called immediately after a new Email note is
    written, ensuring its sender's Person note exists and is up to date
    — the same ensure_person_note operation the retrofit uses, applied
    to one sender at a time going forward (Scenario 7). Skips (returns
    None), without erroring, when sender_email is blank (Scenario 9)."""
    if not sender_email:
        return None
    return ensure_person_note(sender_name or sender_email, sender_email)


def retrofit_people_from_emails() -> list[dict]:
    """One-time batch: for every already-captured Email note carrying a
    real sender_email, ensures that sender's Person note exists and is up
    to date, deduped by email address (case-insensitively) so multiple
    Email notes from the same sender within this run produce exactly one
    Person note, not one per email (Scenario 1). Idempotent — rerunning
    finds every Person note already created and every already-linked note
    left unchanged (Scenario 2). Person and Customer hub notes are
    silently skipped by construction (neither carries a sender_email
    field). An Email note with no sender_email is skipped, not errored
    (Scenario 9)."""
    results: list[dict] = []
    seen_emails: set[str] = set()
    for path in vault_writer.list_all_note_paths():
        frontmatter, _ = vault_writer.read_note(path)
        sender_email = frontmatter.get("sender_email")
        if not sender_email:
            results.append({"note": str(path), "status": "skipped_no_sender_email"})
            continue
        dedup_key = sender_email.lower()
        if dedup_key in seen_emails:
            results.append({"note": str(path), "status": "skipped_duplicate_sender_this_run"})
            continue
        seen_emails.add(dedup_key)
        sender_name = frontmatter.get("sender") or sender_email
        outcome = ensure_person_note(sender_name, sender_email)
        status = "created" if outcome["created"] else "already_existed"
        results.append({"note": str(path), "status": status, **outcome})
    return results


def relink_people_for_thread_paths(thread_paths: list[str]) -> list[dict]:
    """Bounded, per-Thread sibling of retrofit_people_from_emails() (REQ-SB-77-
    US-01 Scenario 6's instant-trigger half) -- for each given Thread concept-
    note path, reads that Thread's own messages/*.md raw notes (the same
    directory-derivation librarian_housekeeping._thread_full_content/
    backfill_files already use: Path(thread_path).parent / "messages"),
    extracts sender/sender_email from each message's frontmatter, dedupes by
    lower-cased sender_email WITHIN THIS ONE CALL ONLY (mirrors retrofit_
    people_from_emails's own dedup exactly -- not a cross-call/global dedup;
    the two functions' dedup sets are independent by design, since a bounded
    per-Thread call and a whole-vault call may legitimately re-process the
    same sender), and calls ensure_person_note(sender_name, sender_email)
    once per unique sender. A message with no sender_email is skipped, not
    errored (mirrors retrofit_people_from_emails's own skipped_no_sender_email
    status). Returns a list of per-sender result dicts, same shape as
    retrofit_people_from_emails's own return -- zero new linking primitive."""
    results: list[dict] = []
    seen_emails: set[str] = set()
    for thread_path in thread_paths:
        messages_dir = Path(thread_path).parent / "messages"
        message_paths = sorted(messages_dir.glob("*.md")) if messages_dir.exists() else []
        for message_path in message_paths:
            frontmatter, _ = vault_writer.read_note(message_path)
            sender_email = frontmatter.get("sender_email")
            if not sender_email:
                results.append({"note": str(message_path), "status": "skipped_no_sender_email"})
                continue
            dedup_key = sender_email.lower()
            if dedup_key in seen_emails:
                results.append({"note": str(message_path), "status": "skipped_duplicate_sender_this_run"})
                continue
            seen_emails.add(dedup_key)
            sender_name = frontmatter.get("sender") or sender_email
            outcome = ensure_person_note(sender_name, sender_email)
            status = "created" if outcome["created"] else "already_existed"
            results.append({"note": str(message_path), "status": status, **outcome})
    return results


def find_existing_person_note(email: str) -> dict | None:
    """Read-only -- returns {"note_path": str, "name": str} if a Person
    note already exists for this email, else None. NEVER creates a
    Person note (unlike ensure_person_note) -- the Cockpit must not
    mutate the vault as a side effect of merely opening (ADR-036 point
    7). Retargeted (REQ-SB-71-US-03-T03, ADR-048 Decision 6) to
    person_note_dedup_key/find_person_note_path's own vault-wide scan --
    finds a real Person note regardless of whether it's nested under a
    Customer or at the flat fallback location."""
    if not email:
        return None
    dedup_key = vault_writer.person_note_dedup_key("", email)
    note_path = vault_writer.find_person_note_path(dedup_key)
    if note_path is None:
        return None
    frontmatter, _ = vault_writer.read_note(note_path)
    return {"note_path": str(note_path), "name": frontmatter.get("name") or frontmatter.get("subject") or email}


def find_person_note_by_name(person_name: str) -> dict | None:
    """Read-only, name-keyed sibling of find_existing_person_note
    (ADR-038 point 4) -- resolves an @PersonName mention (e.g.
    "AhmedMoussa" or "Ahmed Moussa") against every real Person note's
    own frontmatter "name" field, by case-insensitive,
    whitespace-stripped equality. Scans vault_indexing.get_index() for
    entries with frontmatter.get("type") == "Person" -- NEVER creates a
    note, never guesses at the nearest-sounding name (Scenario 4).
    Returns {"note_path": str, "name": str} or None."""
    normalized_target = re.sub(r"\s+", "", person_name).lower()
    for entry in vault_indexing.get_index().values():
        frontmatter = entry["frontmatter"]
        if frontmatter.get("type") != "Person":
            continue
        candidate_name = frontmatter.get("name") or ""
        if re.sub(r"\s+", "", candidate_name).lower() == normalized_target:
            return {"note_path": entry["path"], "name": candidate_name}
    return None


def link_email_to_person(email_note_path, person_note_path) -> bool:
    """Ensures email_note_path's body carries the inline
    `**Sender:** [[PersonStem]]` wikilink to person_note_path's own
    Person note, inserting it only if not already present. Mirrors
    customer_hub_linking.link_note_to_customer_hub's shape exactly —
    the same insert_body_line_if_missing primitive, applied to the
    inbound Email→Person direction (BUGFIX-01, closes BUG-001) that
    the original REQ-SB-10 pass only ever created/updated the Person
    note as a side effect of, never linking the Email note's own body
    back to it (MEMORY.md's 2026-08-11 standing constraint — a
    referencing note must link out, not just cause the referenced
    note to be created). Returns True if newly added, False if
    already present (idempotent rerun, BUGFIX-01 Scenario 2)."""
    email_note_path = Path(email_note_path)
    person_stem = Path(person_note_path).stem
    link_line = f"**Sender:** [[{person_stem}]]"
    return vault_writer.insert_body_line_if_missing(email_note_path, link_line)


def retrofit_email_sender_links() -> list[dict]:
    """One-time batch: for every already-captured Email note carrying
    a real sender_email, ensures that sender's Person note exists and
    is up to date (safe and idempotent to call even if
    retrofit_people_from_emails already ran), then ensures the Email
    note's own body carries the [[PersonName]] wikilink back to it —
    the inbound Email→Person direction retrofit_people_from_emails
    never wrote (BUGFIX-01, closes BUG-001). Mirrors
    retrofit_customer_hub_links's and retrofit_people_from_emails's
    exact shape. Deliberately does not dedup by sender the way
    retrofit_people_from_emails does — every Email note from a given
    sender needs its own body link, not just the first one processed.
    A note with a blank/missing sender_email is skipped (status
    skipped_no_sender_email), never errored — Person and Customer hub
    notes are skipped by construction (neither carries a sender_email
    field)."""
    results: list[dict] = []
    for path in vault_writer.list_all_note_paths():
        frontmatter, _ = vault_writer.read_note(path)
        sender_email = frontmatter.get("sender_email")
        if not sender_email:
            results.append({"note": str(path), "status": "skipped_no_sender_email"})
            continue
        sender_name = frontmatter.get("sender") or sender_email
        person_result = ensure_person_note(sender_name, sender_email)
        linked = link_email_to_person(path, person_result["note_path"])
        status = "linked" if linked else "already_linked"
        results.append({"note": str(path), "status": status, **person_result})
    return results
