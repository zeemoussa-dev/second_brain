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


def _retag_company_references(
    old_name: str, old_kind: str, new_name: str, new_kind: str,
) -> list[dict]:
    """old_kind/new_kind in {"customer", "partner"} -- the SAME two-signal
    scan (frontmatter-field-equals-old_name / inline **<Old label>:**
    [[old hub stem]] body wikilink, ADR-012's own extension of ADR-009
    point 4) and the SAME four per-note rewrite primitives
    (rename_frontmatter_key/swap_tag/replace_body_line, plus the type
    swap) migrate_customer_to_partner used to hardcode, generalized from
    literal "Customer"/"Partner"/"customer"/"partner" values to the four
    parameters -- REQ-SB-76-US-01-T03, ADR-057 Decisions 5/6. The
    affiliate_of-drop step from the original hardcoded version is REMOVED
    (Partner now legitimately carries affiliate_of -- ADR-057 Decision
    4/REQ-SB-76-US-01-T02); an entity's own affiliate_of value, real or
    empty, always carries forward untouched. Every primitive is itself
    no-op-if-nothing-to-change (and a same-kind/same-label branch is
    skipped outright when old==new, so it never produces a spurious
    "changed" flag for a value that is already correct) -- idempotent by
    construction, mirroring the original function's own discipline.
    Returns a list of {"note": str, "status": "retagged" |
    "already_migrated", "changes": list[str]} entries, one per note that
    matched either signal."""
    old_label = "Customer" if old_kind == "customer" else "Partner"
    new_label = "Customer" if new_kind == "customer" else "Partner"
    old_tag = f"{old_kind}/{vault_writer.tag_slug(old_name)}"
    new_tag = f"{new_kind}/{vault_writer.tag_slug(new_name)}"
    old_hub_stem = (
        vault_writer.hub_note_path(old_name).stem if old_kind == "customer"
        else vault_writer.partner_hub_note_path(old_name).stem
    )
    new_hub_stem = (
        vault_writer.hub_note_path(new_name).stem if new_kind == "customer"
        else vault_writer.partner_hub_note_path(new_name).stem
    )
    old_body_line = f"**{old_label}:** [[{old_hub_stem}]]"
    new_body_line = f"**{new_label}:** [[{new_hub_stem}]]"

    notes_retagged: list[dict] = []
    for path in vault_writer.list_all_note_paths():
        frontmatter, body = vault_writer.read_note(path)
        matches_frontmatter = frontmatter.get(old_kind) == old_name
        matches_body_wikilink = old_body_line in body
        if not (matches_frontmatter or matches_body_wikilink):
            continue
        changed: list[str] = []
        if old_label != new_label and frontmatter.get("type") == old_label:
            if vault_writer.rename_frontmatter_key(path, "type", "type", new_value=new_label):
                changed.append("type")
        if vault_writer.rename_frontmatter_key(path, old_kind, new_kind, new_value=new_name):
            changed.append(f"{old_kind}_to_{new_kind}" if old_kind != new_kind else f"{old_kind}_renamed")
        if old_tag != new_tag and vault_writer.swap_tag(path, old_tag, new_tag):
            changed.append("tag_swapped")
        if old_kind != new_kind and vault_writer.swap_tag(path, f"kind/{old_kind}", f"kind/{new_kind}"):
            changed.append("kind_tag_swapped")
        if old_body_line != new_body_line and vault_writer.replace_body_line(path, old_body_line, new_body_line):
            changed.append("body_line_relabeled")
        notes_retagged.append({
            "note": str(path),
            "status": "retagged" if changed else "already_migrated",
            "changes": changed,
        })

    return notes_retagged


def retarget_company_references(
    old_name: str, old_kind: str, new_name: str, new_kind: str,
) -> list[dict]:
    """One-line pass-through to _retag_company_references -- the Merge
    outcome's own entry point (REQ-SB-76-US-01-T06, ADR-057 Decision 7),
    supporting a same-kind (Customer->Customer/Partner->Partner) or
    cross-kind name change alike, never a new, third move/retag
    primitive."""
    return _retag_company_references(old_name, old_kind, new_name, new_kind)


def migrate_customer_to_partner(customer_name: str) -> dict:
    """One-time migration (ADR-009, match predicate extended by ADR-012,
    OKF-directory-shape gap fixed by REQ-SB-76-US-01-T03/ADR-057 Decision
    5): moves customer_name's Customer hub note/directory into the
    Partner namespace, then retags every vault note referencing it — a
    thin wrapper over _retag_company_references, behaviourally IDENTICAL
    to the original hardcoded version by construction (same name in,
    same name out, kind flips customer->partner), its own external
    contract/return shape unchanged, zero call-site changes anywhere.

    Step 1 resolves the hub note/directory to move, trying the CURRENT
    OKF directory shape FIRST (mirrors resolve_thread_directory's own
    "directory-shaped scan first, flat-note scan second" ordering,
    ADR-052): if customer_name has a real OKF concept file
    (vault_writer.customer_concept_file_exists), the WHOLE OKF directory
    is moved via vault_writer.move_okf_directory — every file inside
    (index.md/<slug>.md/log.md/captures.md, any nested subdirectory)
    preserved byte-for-byte, in one atomic move. Only when no OKF concept
    file exists does the LEGACY flat-file branch run — moves
    Work/Customers/<name>.md to Work/Partners/<name>.md via
    vault_writer.move_note_and_attachments, guarded by an existence check
    so a rerun (finding the Customer hub note already gone, in either
    shape) skips the move entirely (this step's own idempotency
    mechanism). Deliberately does NOT rewrite the moved note's
    frontmatter here: Step 2's single generic scan picks up the
    just-moved note too — so exactly one retag mechanism handles both the
    hub note and every other mistagged note, with no duplicated rewrite
    logic between the two steps.

    Step 2 is _retag_company_references(customer_name, "customer",
    customer_name, "partner") — the same generic, vault-wide two-signal
    scan (Signal A: `customer` frontmatter equals customer_name; Signal
    B: the note's body contains the exact inline `**Customer:**
    [[<hub note filename stem>]]` wikilink, regardless of whether
    `customer` frontmatter is present at all — catches Person notes) this
    function has always used, now shared with the new Merge outcome
    (retarget_company_references, above) instead of duplicated.

    Returns {"hub_note_moved": bool, "hub_note_path": str | None,
    "notes_retagged": list[dict]}.
    """
    hub_note_moved = False
    new_hub_note_path: str | None = None
    if vault_writer.customer_concept_file_exists(customer_name):
        source_directory = vault_writer.customer_directory_paths(customer_name)["directory"]
        target_parent_directory = vault_writer.partner_hub_note_path(customer_name).parent
        new_directory = vault_writer.move_okf_directory(source_directory, target_parent_directory)
        new_hub_note_path = str(new_directory / f"{new_directory.name}.md")
        hub_note_moved = True
    else:
        old_hub_path = vault_writer.hub_note_path(customer_name)
        if old_hub_path.exists():
            new_hub_dir = vault_writer.partner_hub_note_path(customer_name).parent
            new_hub_note_path = vault_writer.move_note_and_attachments(old_hub_path, new_hub_dir)
            hub_note_moved = True

    notes_retagged = _retag_company_references(customer_name, "customer", customer_name, "partner")

    return {
        "hub_note_moved": hub_note_moved,
        "hub_note_path": new_hub_note_path,
        "notes_retagged": notes_retagged,
    }
