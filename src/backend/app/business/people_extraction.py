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

from pathlib import Path

from app.business import customer_hub_linking, partner_hub_linking
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


def ensure_person_note(name: str, email: str) -> dict:
    """The shared "ensure this sender's Person note exists and is up to
    date" operation, called once as a one-time batch
    (retrofit_people_from_emails) and once as a per-write hook
    (ensure_person_note_for_captured_email). Creates a baseline note if
    missing, or tops up any missing baseline frontmatter keys if it
    already exists (Scenarios 2 and 6), without touching a key already
    present or the body. Derives the sender's company from their email
    domain and checks it against known Customers first (unchanged) —
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
    company = derive_company_from_email(email)
    tags = vault_writer.build_person_tags(company)
    note_path = vault_writer.person_note_path(email)

    if vault_writer.person_note_exists(email):
        vault_writer.ensure_person_note_baseline_frontmatter(note_path, name, email, tags)
        created = False
    else:
        vault_writer.create_person_note_baseline(name, email, tags)
        created = True

    matched_customer = find_matching_customer(company)
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
