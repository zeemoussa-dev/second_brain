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
    """Ensures customer's OKF-conformant directory (ADR-042 point 1,
    REQ-SB-54) exists: creates the 4-file baseline
    (index.md/<slug>.md/log.md/captures.md) if the concept file is
    missing, or tops up any missing baseline concept-file frontmatter
    keys if it already exists, without touching a key already present or
    the body. Restructured from the old single-flat-file hub note onto
    the new directory shape (ADR-042's own disclosed Consequence) — this
    function's OWN external contract is unchanged: still returns
    {"hub_note_path": str, "created": bool}, where hub_note_path now
    points at the concept file (Work/Customers/<slug>/<slug>.md) rather
    than the old flat Work/Customers/<slug>.md path. All 5 real call
    sites of this function/ensure_hub_note_and_link need zero changes —
    the concept file's filename stem is identical to the old flat file's
    stem, so link_note_to_customer_hub's own wikilink still resolves
    correctly regardless of which shape produced it. The old flat-file
    primitives (vault_writer.hub_note_path/hub_note_exists/
    create_customer_hub_note_baseline/ensure_hub_note_baseline_
    frontmatter) are no longer called here, but remain unmodified for
    app/business/partner_hub_linking.py's own separate, still-live use
    (Customer->Partner migration, out of this story's scope)."""
    if vault_writer.customer_concept_file_exists(customer):
        vault_writer.ensure_customer_directory_baseline(customer)
        created = False
    else:
        vault_writer.create_customer_directory_baseline(customer)
        created = True
    concept_path = vault_writer.customer_directory_paths(customer)["concept"]
    return {"hub_note_path": str(concept_path), "created": created}


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
