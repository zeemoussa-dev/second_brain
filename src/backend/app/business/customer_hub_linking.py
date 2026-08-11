"""Shared "ensure this customer's hub note exists, then link this note to
it" orchestration (REQ-SB-14) — the one mechanism used by both the
one-time retrofit (retrofit_customer_hub_links, over every existing
customer-tagged note) and email_classification.py's per-write capture
hook (ensure_hub_note_and_link, going forward). Follows ADR-003's
layering and the tag_backfill.py / vault_restructure.py precedent of one
business module per maintenance operation.
"""
from __future__ import annotations

from pathlib import Path

from app.data_access import vault_writer

_UNSORTED_CUSTOMER = "Unsorted"


def ensure_customer_hub_note(customer: str) -> dict:
    """Ensures customer's hub note exists: creates a baseline note if
    missing, or tops up any missing baseline frontmatter keys if it
    already exists (REQ-SB-14 Scenario 4) without touching a key already
    present or the body. Returns {"hub_note_path": str, "created":
    bool}."""
    hub_path = vault_writer.hub_note_path(customer)
    if vault_writer.hub_note_exists(customer):
        vault_writer.ensure_hub_note_baseline_frontmatter(hub_path, customer)
        return {"hub_note_path": str(hub_path), "created": False}
    created_path = vault_writer.create_customer_hub_note_baseline(customer)
    return {"hub_note_path": created_path, "created": True}


def link_note_to_customer_hub(note_path, customer: str) -> bool:
    """Ensures note_path's body carries the inline
    `**Customer:** [[Hub]]` wikilink to customer's hub note, inserting it
    only if not already present. Returns True if newly added, False if
    already present (REQ-SB-14 Scenario 5 idempotency)."""
    note_path = Path(note_path)
    hub_stem = vault_writer.hub_note_path(customer).stem
    link_line = f"**Customer:** [[{hub_stem}]]"
    return vault_writer.insert_body_line_if_missing(note_path, link_line)


def ensure_hub_note_and_link(note_path, customer: str) -> dict:
    """The single shared operation, called by both the retrofit and the
    per-write capture hook: ensure customer's hub note exists, then
    ensure note_path is linked to it. "Unsorted" (the placeholder
    pseudo-customer list_known_customers() already excludes) and a blank
    customer are both skipped — there is no real customer to link to."""
    if not customer or customer == _UNSORTED_CUSTOMER:
        return {"skipped": True, "reason": "no_customer_or_unsorted"}
    note_path = Path(note_path)
    hub_result = ensure_customer_hub_note(customer)
    linked = link_note_to_customer_hub(note_path, customer)
    return {
        "skipped": False,
        "hub_note_path": hub_result["hub_note_path"],
        "hub_created": hub_result["created"],
        "linked": linked,
    }


def retrofit_customer_hub_links() -> list[dict]:
    """One-time batch: for every existing note carrying a real
    `customer:` frontmatter field, ensures that customer's hub note
    exists and that the note is linked to it. Idempotent — rerunning
    finds every hub note already created and every already-linked note
    left unchanged (REQ-SB-14 Scenarios 1 and 5). Never links a hub note
    to itself."""
    results: list[dict] = []
    for path in vault_writer.list_all_note_paths():
        frontmatter, _ = vault_writer.read_note(path)
        customer = frontmatter.get("customer")
        if not customer or customer == _UNSORTED_CUSTOMER:
            results.append({"note": str(path), "status": "skipped_no_customer"})
            continue
        if path == vault_writer.hub_note_path(customer):
            results.append({"note": str(path), "status": "skipped_is_hub_note"})
            continue
        outcome = ensure_hub_note_and_link(path, customer)
        status = "linked" if outcome["linked"] else "already_linked"
        results.append({"note": str(path), "status": status, **outcome})
    return results
