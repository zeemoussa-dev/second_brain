"""Partner hub-note orchestration (REQ-SB-16, ADR-009) — a parallel
sibling to customer_hub_linking.py, not an extension of it (full
reasoning: ADR-009 — keeps the Done, mechanism-Accepted REQ-SB-14 module
and its email_classification.py call site untouched). Structurally
mirrors customer_hub_linking.py's two granular primitives
(ensure_partner_hub_note, link_note_to_partner_hub) exactly, plus the
one-time Customer->Partner migration (migrate_customer_to_partner) —
see that function's own docstring for why one generic scan pass handles
both the moved hub note's own frontmatter rewrite and every other
mistagged note.
"""
from __future__ import annotations

from pathlib import Path

from app.data_access import vault_writer


def ensure_partner_hub_note(partner: str) -> dict:
    """Ensures partner's hub note exists: creates a baseline note if
    missing, or tops up any missing baseline frontmatter keys if it
    already exists, without touching a key already present or the body.
    Mirrors customer_hub_linking.ensure_customer_hub_note exactly, for
    Partner's shorter baseline-key set (no affiliate_of). Returns
    {"hub_note_path": str, "created": bool}."""
    hub_path = vault_writer.partner_hub_note_path(partner)
    if vault_writer.partner_hub_note_exists(partner):
        vault_writer.ensure_partner_hub_note_baseline_frontmatter(hub_path, partner)
        return {"hub_note_path": str(hub_path), "created": False}
    created_path = vault_writer.create_partner_hub_note_baseline(partner)
    return {"hub_note_path": created_path, "created": True}


def link_note_to_partner_hub(note_path, partner: str) -> bool:
    """Ensures note_path's body carries the inline `**Partner:** [[Hub]]`
    wikilink to partner's hub note, inserting it only if not already
    present. Mirrors customer_hub_linking.link_note_to_customer_hub
    exactly. Returns True if newly added, False if already present
    (idempotent rerun)."""
    note_path = Path(note_path)
    hub_stem = vault_writer.partner_hub_note_path(partner).stem
    link_line = f"**Partner:** [[{hub_stem}]]"
    return vault_writer.insert_body_line_if_missing(note_path, link_line)


def migrate_customer_to_partner(customer_name: str) -> dict:
    """One-time migration (ADR-009, match predicate extended by ADR-012):
    moves customer_name's Customer hub note into the Partner namespace,
    then retags every vault note matching either of two signals — a
    **generic, vault-wide scan**, never a hardcoded note list (ADR-009's
    rejected alternative), so it correctly picks up every mistagged note
    regardless of kind (Person/Email/Newsletter/Notification alike).

    Step 1 moves Work/Customers/<name>.md to Work/Partners/<name>.md via
    vault_writer.move_note_and_attachments (already exists), guarded by
    an existence check so a rerun — finding the Customer hub note
    already gone — skips the move entirely (this step's own idempotency
    mechanism). Deliberately does NOT rewrite the moved note's
    frontmatter here: step 2's single generic scan picks up the
    just-moved note too (list_all_note_paths() finds it at its new
    Work/Partners/ path, still carrying its old customer/type: Customer/
    tags/affiliate_of frontmatter until the scan rewrites it) — so
    exactly one retag mechanism handles both the hub note and every
    other mistagged note, with no duplicated rewrite logic between the
    two steps.

    Step 2 iterates every vault note via list_all_note_paths()/
    read_note() (the same pattern retrofit_customer_hub_links/
    retrofit_people_from_emails already use) and processes a note if
    either of two signals matches (ADR-012, extends ADR-009 point 4):
    Signal A — `customer` frontmatter equals customer_name (the original
    ADR-009 signal, catches Email/Newsletter/Notification notes and the
    hub note itself); or Signal B — the note's body contains the exact
    inline `**Customer:** [[<hub note filename stem>]]` wikilink line,
    regardless of whether `customer` frontmatter is present at all (the
    ADR-012 addition, catches Person notes, which never carry a
    `customer` frontmatter field or a `customer/<slug>` tag — only a
    `company/<slug>` tag plus this inline wikilink, written separately by
    customer_hub_linking.link_note_to_customer_hub). Both signals are
    read from the same read_note() call already made once per note — no
    second scan, no extra vault I/O. For a matched note: swaps
    `type: Customer` -> `type: Partner` (a no-op for every non-hub note,
    since their `type` is never "Customer"), drops `affiliate_of` if
    present (present only on the hub note — Partner has no such key),
    renames `customer` -> `partner` (same value, a no-op for a note
    matched only via Signal B, since it never had a `customer` key),
    swaps the `customer/<slug>` tag for `partner/<slug>` and
    `kind/customer` for `kind/partner` (both no-ops for a Signal-B-only
    note, which never carries either tag), and — only where present —
    relabels the inline `**Customer:** [[<name>]]` body line to
    `**Partner:** [[<name>]]` (this is the only primitive that actually
    fires for a Signal-B-only note, e.g. a Person note — exactly the
    "only the inline wikilink is relabeled, nothing else touched"
    behavior ADR-012 requires). Every primitive this step calls is
    itself a no-op-if-absent, so a second full run makes zero further
    changes anywhere (idempotent by construction — no separate "already
    migrated" tracking needed; a note already migrated no longer matches
    Signal A *or* Signal B, so the very first `if` below already
    excludes it on a rerun).

    Returns {"hub_note_moved": bool, "hub_note_path": str | None,
    "notes_retagged": list[dict]}.
    """
    old_hub_path = vault_writer.hub_note_path(customer_name)
    hub_note_moved = False
    new_hub_note_path: str | None = None
    if old_hub_path.exists():
        new_hub_dir = vault_writer.partner_hub_note_path(customer_name).parent
        new_hub_note_path = vault_writer.move_note_and_attachments(old_hub_path, new_hub_dir)
        hub_note_moved = True

    old_tag = f"customer/{vault_writer.tag_slug(customer_name)}"
    new_tag = f"partner/{vault_writer.tag_slug(customer_name)}"
    hub_stem = vault_writer.hub_note_path(customer_name).stem
    old_body_line = f"**Customer:** [[{hub_stem}]]"
    new_body_line = f"**Partner:** [[{hub_stem}]]"

    notes_retagged: list[dict] = []
    for path in vault_writer.list_all_note_paths():
        frontmatter, body = vault_writer.read_note(path)
        matches_frontmatter = frontmatter.get("customer") == customer_name
        matches_body_wikilink = old_body_line in body
        if not (matches_frontmatter or matches_body_wikilink):
            continue
        changed: list[str] = []
        if frontmatter.get("type") == "Customer":
            if vault_writer.rename_frontmatter_key(path, "type", "type", new_value="Partner"):
                changed.append("type")
        if vault_writer.remove_frontmatter_key_if_present(path, "affiliate_of"):
            changed.append("affiliate_of_dropped")
        if vault_writer.rename_frontmatter_key(path, "customer", "partner"):
            changed.append("customer_to_partner")
        if vault_writer.swap_tag(path, old_tag, new_tag):
            changed.append("tag_swapped")
        if vault_writer.swap_tag(path, "kind/customer", "kind/partner"):
            changed.append("kind_tag_swapped")
        if vault_writer.replace_body_line(path, old_body_line, new_body_line):
            changed.append("body_line_relabeled")
        notes_retagged.append({
            "note": str(path),
            "status": "retagged" if changed else "already_migrated",
            "changes": changed,
        })

    return {
        "hub_note_moved": hub_note_moved,
        "hub_note_path": new_hub_note_path,
        "notes_retagged": notes_retagged,
    }
