"""Second Brain's own Customer/Project/Person/Meeting/Thread/Partner/Task
business logic for the Obsidian vault (app.config.settings.vault_path).
No staging/promotion step — per MEMORY.md's decision, anything written
here is immediately part of the trusted vault.

The raw Obsidian-format mechanics this module used to define directly
(frontmatter parsing, tags, `## ` section read/write, the generic OKF
4-file directory pattern, whole-vault scanning) moved to app/obsidian/
(2026-08-27, backend architecture refactor) — this module now imports
them and adds the Second-Brain-specific knowledge on top (which
frontmatter keys a Customer needs, tag conventions, note-kind path
layout). None of these note kinds have a real Template.json yet (the
Templates/VaultClient path — app/vault/, app/data_access/templates/ —
is the target for note kinds that do), so they stay here, hand-written,
until one is authored for each. Re-exported below with their original
names/signatures so every existing caller across app/business/ keeps
working unchanged; new code should prefer importing app.obsidian
directly for anything that doesn't need this module's own Second-Brain
business logic.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings
from app.obsidian import attachments as _obsidian_attachments
from app.obsidian import directory_baseline as _okf
from app.obsidian import notes as _obsidian_notes
from app.obsidian.formatting import format_human_readable_datetime
from app.obsidian.frontmatter import (
    insert_frontmatter_key_if_missing,
    insert_tags_line,
    read_note,
    remove_frontmatter_key_if_present,
    rename_frontmatter_key,
    upsert_frontmatter_key,
    write_frontmatter_note as _write_frontmatter_note,
)
from app.obsidian.notes import WIKILINK_PATTERN, extract_wikilink_targets
from app.obsidian.sections import (
    append_body_line as append_person_note_update_line,
    append_body_section_line,
    insert_body_line_if_missing,
    insert_body_section_if_missing,
    read_body_section,
    replace_body_line,
    replace_body_opening_line,
    replace_body_section,
)
from app.obsidian.tags import swap_tag, tag_slug

# format_okf_provenance/okf_directory_paths/okf_concept_file_exists/
# move_okf_directory/create_okf_directory_baseline/
# ensure_okf_directory_baseline are re-exported as module-level names
# further down (right where the old inline definitions used to be) so
# every existing `vault_writer.create_okf_directory_baseline(...)`-style
# call keeps working unchanged.
_slugify = _obsidian_notes.slugify
format_okf_provenance = _okf.format_okf_provenance
okf_directory_paths = _okf.okf_directory_paths
okf_concept_file_exists = _okf.okf_concept_file_exists
move_okf_directory = _okf.move_okf_directory
create_okf_directory_baseline = _okf.create_okf_directory_baseline
ensure_okf_directory_baseline = _okf.ensure_okf_directory_baseline

_WORK_ROOT = "Work"
_PROCESSED_EMAILS_FILE = "processed_email_ids.json"
_CONVERSATIONS_FILE = "conversation_index.json"
_LAST_CAPTURE_RUN_FILE = "last_capture_run.json"
_AGENT_HISTORY_FILE = "agent_communication_history.json"
_AGENT_MEMORY_FILE = "agent_memory.json"
_AGENT_SKILLS_FILE = "agent_skills.json"
_AGENT_KEYWORDS_FILE = "agent_keywords.json"
_AGENT_WORKING_MODES_FILE = "agent_working_modes.json"
_AGENT_PENDING_APPROVALS_FILE = "agent_pending_approvals.json"
_AGENT_KNOWLEDGE_GAPS_FILE = "agent_knowledge_gaps.json"
_COCKPIT_THREADS_FILE = "cockpit_threads.json"
_COCKPIT_CHAT_FILE = "cockpit_chat.json"
_AGENT_BACKGROUND_FLAGS_FILE = "agent_background_flags.json"
_AGENT_VISUALS_FILE = "agent_visuals.json"
_AGENT_SCHEDULES_FILE = "agent_schedules.json"
_JOB_RUN_STATE_FILE = "job_run_state.json"


def build_tags(customer: str, kind: str) -> list[str]:
    """Hierarchical Obsidian tags mirroring the folder structure, so notes
    stay findable by customer/kind via search/graph view independent of
    where they physically live — the point raised when a note sits in
    Unsorted/ but you already suspect which customer it's really for."""
    return [f"customer/{tag_slug(customer)}", f"kind/{tag_slug(kind)}"]


def write_note(subfolder: str, filename_stem: str, frontmatter: dict, body: str) -> str:
    return _obsidian_notes.write_note(settings.vault_path, subfolder, filename_stem, frontmatter, body)


def list_all_note_paths() -> list:
    return _obsidian_notes.list_all_note_paths(settings.vault_path, _WORK_ROOT)


def list_notes_in_kind_folder(kind: str) -> list:
    return _obsidian_notes.list_notes_in_kind_folder(settings.vault_path, kind, _WORK_ROOT)


def customer_directory_paths(customer: str) -> dict:
    return okf_directory_paths(settings.vault_path / _CUSTOMERS_SUBFOLDER, customer)


def customer_concept_file_exists(customer: str) -> bool:
    return okf_concept_file_exists(settings.vault_path / _CUSTOMERS_SUBFOLDER, customer)


def build_customer_concept_frontmatter(customer: str) -> dict:
    """OKF-required concept-file frontmatter for a Customer directory
    (ADR-042 point 1, REQ-SB-54-US-01 Scenario 3): type/title/description/
    tags/status/stale_after/generated/verified/sources. `status`/
    `stale_after` default values ("active"/"") are a reasonable-default
    choice only — no locked AC tests specific field values, only field
    presence. `generated`/`verified` start blank (format_okf_provenance
    with empty by/at) — populating them with a real agent id/timestamp is
    REQ-SB-57's own synthesis-layer job, out of this data_access
    function's scope."""
    return {
        "type": "customer",
        "title": customer,
        "description": "",
        "tags": build_tags(customer, "customer"),
        "status": "active",
        "stale_after": "",
        "generated": format_okf_provenance(by="", at=""),
        "verified": format_okf_provenance(by="", at=""),
        "sources": [],
        "affiliate_of": "",
    }


def create_customer_directory_baseline(customer: str) -> dict:
    return create_okf_directory_baseline(
        settings.vault_path / _CUSTOMERS_SUBFOLDER, customer,
        build_customer_concept_frontmatter(customer),
        identifying_name=customer,
        index_listing_body=f"# {customer}\n\n- [[{_slugify(customer)}]]\n",
    )


def ensure_customer_directory_baseline(customer: str) -> list[str]:
    return ensure_okf_directory_baseline(
        settings.vault_path / _CUSTOMERS_SUBFOLDER, customer,
        build_customer_concept_frontmatter(customer),
        identifying_name=customer,
        index_listing_body=f"# {customer}\n\n- [[{_slugify(customer)}]]\n",
    )


def _project_directory_root(customer: str) -> Path:
    """A Project's own directory_root, one level inside its Customer's
    directory (ADR-042 point 4) — always computed via
    customer_directory_paths()'s own resolved "directory" path, never a
    separately-hardcoded 'Work/Customers/<slug>/projects' string, so a
    future change to Customer's own directory location is never silently
    out of sync with where Project nests underneath it."""
    return customer_directory_paths(customer)["directory"] / "projects"


def project_directory_paths(customer: str, project: str) -> dict:
    return okf_directory_paths(_project_directory_root(customer), project)


def project_concept_file_exists(customer: str, project: str) -> bool:
    return okf_concept_file_exists(_project_directory_root(customer), project)


def build_project_concept_frontmatter(customer: str, project: str) -> dict:
    """OKF-required concept-file frontmatter for a Project directory
    (ADR-042 point 4), mirroring build_customer_concept_frontmatter's own
    field set and reasonable-default choices exactly — only `tags` differs,
    carrying both the owning customer/<slug> tag and kind/project (so a
    Project stays findable both by its own kind and by its parent
    Customer, the same customer/-plus-kind/ pairing build_tags/build_
    meeting_tags already establish elsewhere). `last_synthesized_status`
    (`REQ-SB-57-US-01-T01`) is the Project Synthesizer's own History-line
    idempotency marker — defaults to the SAME value `status` itself
    defaults to ("active"), so a brand-new Project's first-ever synthesis
    pass naturally compares `status` against `"active"` with zero
    special-casing (`architecture.md` → "Project & Customer Synthesizer")."""
    return {
        "type": "project",
        "title": project,
        "description": "",
        "tags": [f"customer/{tag_slug(customer)}", "kind/project"],
        "status": "active",
        "stale_after": "",
        "generated": format_okf_provenance(by="", at=""),
        "verified": format_okf_provenance(by="", at=""),
        "sources": [],
        "last_synthesized_status": "active",
    }


def create_project_directory_baseline(customer: str, project: str) -> dict:
    return create_okf_directory_baseline(
        _project_directory_root(customer), project,
        build_project_concept_frontmatter(customer, project),
        identifying_name=project,
        index_listing_body=f"# {project}\n\n- [[{_slugify(project)}]]\n",
    )


def ensure_project_directory_baseline(customer: str, project: str) -> list[str]:
    return ensure_okf_directory_baseline(
        _project_directory_root(customer), project,
        build_project_concept_frontmatter(customer, project),
        identifying_name=project,
        index_listing_body=f"# {project}\n\n- [[{_slugify(project)}]]\n",
    )


def list_customer_projects(customer: str) -> list[dict]:
    """Enumerates one Customer's own `projects/*/` subdirectories (ADR-042
    point 4's directory shape), for Route-to-Project's "currently open
    Projects" guess (REQ-SB-55-US-01-T01, ADR-043 Consequences) — a
    mechanical extension of list_known_customers()'s own frontmatter-scan
    shape, bounded to one customer's own projects subtree rather than the
    whole vault. Returns [] if the customer has no `projects/`
    subdirectory yet at all — mirrors list_notes_in_kind_folder()'s own
    "not-yet-created folder returns []" contract; never raises for a
    genuinely new Customer with zero Projects. Each real Project
    directory's own concept file is read directly via read_note (never a
    hardcoded/assumed status) — returns whatever `title`/`status` that
    file's own frontmatter actually carries, including a blank or missing
    status, honestly, as None/"" rather than fabricating "active". No
    "which Project counts as currently open" judgement is made here —
    that filtering is Route-to-Project's own business-logic job (T04),
    out of this pure data_access enumeration primitive's scope."""
    projects_root = _project_directory_root(customer)
    if not projects_root.exists():
        return []
    results: list[dict] = []
    for project_dir in sorted(p for p in projects_root.iterdir() if p.is_dir()):
        concept_slug = project_dir.name
        concept_path = project_dir / f"{concept_slug}.md"
        if not concept_path.exists():
            continue
        frontmatter, _ = read_note(concept_path)
        results.append({
            "project": frontmatter.get("title"),
            "slug": concept_slug,
            "status": frontmatter.get("status"),
        })
    return results


def list_customer_folders() -> list[dict]:
    """Every real Customer OKF directory under Work/Customers/ (REQ-SB-74-
    US-01-T01, ADR-055 Decision 3) — mirrors list_customer_projects()'s own
    "enumerate this directory level, read title from concept file" shape
    one level up (a Customer's own sibling directly under Work/Customers/,
    rather than a Customer's own projects/ subdirectory). Deliberately
    DIFFERENT from list_known_customers(), which scans `customer:`
    frontmatter USAGE across every note, not folder existence — the two
    answer two different questions and are never merged (ADR-055
    Consequences). Returns [] if Work/Customers/ does not exist yet, same
    not-yet-created-folder contract every sibling enumeration primitive
    already has."""
    customers_root = settings.vault_path / _CUSTOMERS_SUBFOLDER
    if not customers_root.exists():
        return []
    results: list[dict] = []
    for customer_dir in sorted(p for p in customers_root.iterdir() if p.is_dir()):
        concept_slug = customer_dir.name
        concept_path = customer_dir / f"{concept_slug}.md"
        if not concept_path.exists():
            continue
        frontmatter, _ = read_note(concept_path)
        results.append({
            "customer": frontmatter.get("title"),
            "slug": concept_slug,
            "directory": customer_dir,
        })
    return results


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
        if customer:
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


def write_attachments(subfolder: str, note_stem: str, message_segment: str, attachments: list[dict]) -> list[dict]:
    return _obsidian_attachments.write_attachments(settings.vault_path, subfolder, note_stem, message_segment, attachments)


def staged_attachment_files(conversation_id: str, message_id: str) -> list:
    return _obsidian_attachments.staged_attachment_files(settings.vault_path, _THREADS_SUBFOLDER, conversation_id, message_id)


def write_file_companion(
    subfolder: str, note_stem: str, file_slug: str, original_filename: str, content: bytes, summary: str,
    source_thread: str | None = None, source_email: str | None = None,
) -> dict:
    # note_stem accepted for interface parity only -- the real path shape
    # never incorporated it (see app.obsidian.attachments' own docstring).
    return _obsidian_attachments.write_file_companion(
        settings.vault_path, subfolder, file_slug, original_filename, content, summary, source_thread, source_email,
    )


def write_file_link_companion(
    subfolder: str, file_slug: str, url: str, source_thread: str | None = None, source_email: str | None = None,
) -> dict:
    return _obsidian_attachments.write_file_link_companion(
        settings.vault_path, subfolder, file_slug, url, source_thread, source_email,
    )


def move_note_and_attachments(note_path, target_dir) -> str:
    return _obsidian_notes.move_note_and_attachments(note_path, target_dir)


def remove_empty_dirs(root) -> None:
    return _obsidian_notes.remove_empty_dirs(root)


def _processed_emails_path():
    state_dir = settings.second_brain_data_path
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
    state_dir = settings.second_brain_data_path
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
    state_dir = settings.second_brain_data_path
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


_PEOPLE_SUBFOLDER = f"{_WORK_ROOT}/People"
_PERSON_NOTE_BASELINE_KEYS = ("type", "name", "email", "phone", "linkedin", "tags")


def person_note_dedup_key(name: str, email: str | None) -> str:
    """Lowercased email when one exists (REQ-SB-10's own original,
    unchanged convention) — or a slug of the display name when it does
    not (REQ-SB-71-US-03-T03, ADR-048 Decision 6), closing meeting_
    classification.py's own silent no-email-attendee `if not email:
    continue` gap. A name-based key cannot structurally distinguish two
    different real no-email people who share an exact display name — a
    real, disclosed, narrow residual limitation, not resolved further by
    this task."""
    return email.lower() if email else _slugify(name.lower())


def person_note_path(dedup_key: str, customer: str | None):
    """Resolves the vault-absolute path a Person note lives (or would
    live) at (REQ-SB-71-US-03-T03, ADR-048 Decision 6) — SIGNATURE CHANGE
    from the prior person_note_path(email): Work/Customers/<slug-of-
    customer>/People/<slug-of-dedup_key>.md when customer is a real,
    non-empty, matched Customer name; the existing flat Work/People/
    <slug-of-dedup_key>.md otherwise (operator-confirmed 2026-08-18
    fallback for a Person with no derivable/matched Customer at all).
    Does not check whether the file exists yet."""
    if customer:
        return (
            settings.vault_path / _CUSTOMERS_SUBFOLDER / _slugify(customer)
            / "People" / f"{_slugify(dedup_key)}.md"
        )
    return settings.vault_path / _PEOPLE_SUBFOLDER / f"{_slugify(dedup_key)}.md"


def person_note_exists(dedup_key: str, customer: str | None) -> bool:
    return person_note_path(dedup_key, customer).exists()


def find_person_note_path(dedup_key: str) -> Path | None:
    """Vault-wide lookup by dedup_key alone, regardless of which Customer
    (if any) the note is nested under (REQ-SB-71-US-03-T03, ADR-048
    Decision 6) — mirrors resolve_thread_note_path's own "no persisted
    index, a live bounded scan" precedent for the identical class of
    problem: a Person's home is no longer deterministic from dedup_key
    alone once nesting depends on a per-caller Customer match that can
    legitimately differ across callers/time. Scans Work/Customers/*/
    People/<stem>.md first, then the flat Work/People/<stem>.md fallback.
    Purely read-only; never creates, writes, or renames anything."""
    stem = _slugify(dedup_key)
    customers_root = settings.vault_path / _CUSTOMERS_SUBFOLDER
    if customers_root.exists():
        nested_matches = sorted(customers_root.glob(f"*/People/{stem}.md"))
        if nested_matches:
            return nested_matches[0]
    flat_path = settings.vault_path / _PEOPLE_SUBFOLDER / f"{stem}.md"
    return flat_path if flat_path.exists() else None


def build_person_tags(company: str | None) -> list[str]:
    """Mirrors build_tags's shape for the People schema's separate
    company/ tag namespace — never customer/, since a person's employer
    isn't always a customer account (many real contacts are internal
    Core42 colleagues or third parties). Returns ["kind/person"] alone
    when no company was derived (Scenario 5 — a personal/free email
    domain, or no domain at all), or ["company/<slug>", "kind/person"]
    when one was (Scenarios 3 and 4 both get the tag; only Scenario 3
    also gets the wikilink, added separately by the orchestration
    layer)."""
    if not company:
        return ["kind/person"]
    return [f"company/{tag_slug(company)}", "kind/person"]


def create_person_note_baseline(note_path: Path, name: str, email: str | None, tags: list[str]) -> str:
    """Creates a Person note for the first time, at the already-resolved
    note_path (REQ-SB-71-US-03-T03, ADR-048 Decision 6 — SIGNATURE CHANGE
    from the prior create_person_note_baseline(name, email, tags), which
    derived its own flat path internally): baseline frontmatter (type/
    name/email/phone/linkedin/tags, `email` written as "" when None —
    the no-email-attendee case) with an empty body — the REQ-SB-14
    hub-note baseline pattern applied to People, now usable for either
    the flat Work/People/ location or a Work/Customers/<slug>/People/
    nested one, since the caller (people_extraction.ensure_person_note)
    already resolved note_path via the retargeted person_note_path. The
    company wikilink line (when applicable) is never written here — it
    is inserted separately via insert_body_line_if_missing by the
    orchestration layer, the same way customer_hub_linking.
    link_note_to_customer_hub layers on top of ensure_customer_hub_note.
    Always writes unconditionally, mirroring write_note()'s own contract
    — callers must resolve/check note_path's own existence first."""
    _write_frontmatter_note(
        note_path,
        {
            "type": "Person",
            "name": name,
            "email": email or "",
            "phone": "",
            "linkedin": "",
            "tags": tags,
        },
        "",
    )
    return str(note_path)


def ensure_person_note_baseline_frontmatter(path, name: str, email: str | None, tags: list[str]) -> list[str]:
    """Tops up an already-existing Person note with any of the six
    baseline frontmatter keys it is missing (type/name/email/phone/
    linkedin/tags), inserting each surgically via
    insert_frontmatter_key_if_missing — never touches a key already
    present (so a user-filled phone/linkedin value, once set, is never
    reset to ""), and never touches the body. `email` may now be
    None/"" (REQ-SB-71-US-03-T03) for the no-email-attendee case, topped
    up as "" like every other never-yet-set value. Returns the list of
    keys actually inserted (empty if the note already had all six) —
    REQ-SB-10 Scenario 6's baseline-preservation mechanism, the same
    contract ensure_hub_note_baseline_frontmatter already established
    for Customer hub notes."""
    baseline_values = {
        "type": "Person",
        "name": name,
        "email": email or "",
        "phone": "",
        "linkedin": "",
        "tags": tags,
    }
    inserted: list[str] = []
    for key in _PERSON_NOTE_BASELINE_KEYS:
        if insert_frontmatter_key_if_missing(path, key, baseline_values[key]):
            inserted.append(key)
    return inserted


_MEETINGS_SUBFOLDER = f"{_WORK_ROOT}/Meetings"
# REQ-SB-71-US-03-T01 (ADR-048 Decision 5) reconciliation, logged in this
# task's own Implementation Log: the story's own Scenario 1 text and this
# task's own more precise End-State text ("drops subject/start/end/
# location as persisted fields... adds teams_link/dial_in/recurrence/
# calendar_event_id/calendar_series_id") disagree on whether this app's
# own internal bookkeeping fields (type/customer/tags/thread) also drop --
# reconciled by following the End-State text (Implementation/Learnings.md
# SPRINT-049 precedent): only subject/start/end/location (the raw
# calendar-logistics fields with no internal meaning of their own) are
# dropped; type/customer/tags/thread (this app's own derived bookkeeping,
# relied on by customer_hub_linking/meeting-thread-linking/list_known_
# customers) are unaffected and continue to persist.
_MEETING_NOTE_BASELINE_KEYS = (
    "type", "customer", "tags", "thread", "teams_link", "dial_in",
    "organizer", "recurrence", "attendees",
)
_PROCESSED_MEETINGS_FILE = "processed_meeting_ids.json"

_ATTENDEES_LINE_PATTERN = re.compile(r"^\*\*Attendees:\*\* (.+)$", re.MULTILINE)
_ATTENDEES_LINE_PREFIX = "**Attendees:** "
# WIKILINK_PATTERN itself now lives in app.obsidian.notes (imported at
# the top of this file) -- kept importable from here under its original
# name for every existing caller.


def meeting_note_filename_stem(subject: str, start: str) -> str:
    """<subject>-<date>-<hash-suffix> — mirrors the EntryID-suffix
    disambiguation email filenames already use (MEMORY.md), but the
    suffix is now an 8-hex-char SHA-256 prefix of `f"{subject}|{start}"`
    (ADR-019) rather than any Outlook-provided identity field — both
    `EntryID` (ADR-008) and `AppointmentItem.GlobalAppointmentID`
    (ADR-013) were tried and live-confirmed non-unique across a real
    recurring series' expanded occurrences on this Outlook installation
    (ESC-002, ESC-012). The key is now a structural, not empirical,
    uniqueness guarantee: two distinct real occurrences of the same
    recurring series cannot share an identical exact start moment, so
    `start` (the full, precise timestamp string list_calendar_events
    returns, not the coarse `start[:10]` date-only slice used below for
    the filename's own display component) is the disambiguator. `subject`
    is combined into the hash input because two different, unrelated
    meetings can genuinely start at the exact same instant — a
    timestamp-only key would silently merge those two into one note.
    Hashing the complete combined string (not a raw slice) keeps ADR-013
    point 2's already-correct reasoning intact: any difference anywhere
    in the input changes the hash, so no positional assumption about
    where the "varying part" of a date/subject string lives is ever
    load-bearing."""
    date = start[:10]
    suffix = hashlib.sha256(f"{subject}|{start}".encode("utf-8")).hexdigest()[:8]
    return f"{subject}-{date}-{suffix}"


def meeting_note_path(subject: str, start: str):
    """Resolves the vault-absolute path a Meeting note lives (or would
    live) at — Work/Meetings/<subject>-<date>-<hash-suffix>.md — without
    checking whether it exists yet. Uses the same _slugify() write_note()
    applies to its own filename_stem, so this always points at exactly
    the file create_meeting_note_baseline()/write_note() would create."""
    stem = meeting_note_filename_stem(subject, start)
    return settings.vault_path / _MEETINGS_SUBFOLDER / f"{_slugify(stem)}.md"


def meeting_note_exists(subject: str, start: str) -> bool:
    return meeting_note_path(subject, start).exists()


def meeting_series_directory_paths(series_id: str) -> dict:
    """Resolves the deterministic path set for a recurring Meeting
    series' own ONE ongoing note (REQ-SB-71-US-03-T01, ADR-048 Decision
    5) — Work/Meetings/<slug-of-series_id>/<slug-of-series_id>.md,
    series_id keyed by Outlook's own GlobalAppointmentID (constant across
    every occurrence of a series — ADR-013/ESC-012's own live-confirmed
    fact, rejected once as a per-OCCURRENCE dedup key for the one-time
    filename scheme, exactly right here for series identity instead).
    Mirrors thread_directory_paths' own shape — a directory plus one
    concept file inside it, no index/log/captures (ADR-042 point 1's own
    Customer/Project-only 4-file scope-lock is not reopened by this
    addition). Pure, deterministic, no I/O — does not check whether
    either path exists yet."""
    concept_slug = _slugify(series_id)
    base = settings.vault_path / _MEETINGS_SUBFOLDER / concept_slug
    return {"directory": base, "concept": base / f"{concept_slug}.md"}


def _legacy_meeting_note_path_by_entry_id(subject: str, start: str, entry_id: str):
    """Computes the PRE-ADR-013 filename scheme (EntryID[-8:] suffix) —
    kept only so resolve_meeting_note_path can recognize an
    already-captured note written before this fix, without migrating
    or renaming it. Never used to create a new note."""
    date = start[:10]
    stem = f"{subject}-{date}-{entry_id[-8:]}"
    return settings.vault_path / _MEETINGS_SUBFOLDER / f"{_slugify(stem)}.md"


def resolve_meeting_note_path(subject: str, start: str, entry_id: str):
    """Returns (path, already_existed) — two tiers only (ADR-019): checks
    the current precise-start-timestamp-hash path first; if not found,
    falls back to the legacy EntryID-suffix path (ADR-013 point 3,
    unmodified) so an already-captured, still-in-window event (from
    before either fix) is recognized and topped up rather than
    duplicated under a new filename. ADR-013's own middle
    GlobalAppointmentID-hash tier is deliberately not carried forward —
    zero real notes were ever created under it (confirmed live,
    REQ-SB-08-US-01-T06), so keeping it would be dead code carrying a
    live-confirmed defect (ESC-012), not a genuine safety net. Neither of
    the 39 pre-fix notes is renamed by this function — whichever path is
    found is returned as-is."""
    new_path = meeting_note_path(subject, start)
    if new_path.exists():
        return new_path, True
    legacy_path = _legacy_meeting_note_path_by_entry_id(subject, start, entry_id)
    if legacy_path.exists():
        return legacy_path, True
    return new_path, False


def build_meeting_tags(customer: str | None) -> list[str]:
    """Mirrors build_person_tags's shape for Meetings. Returns
    ["kind/meeting"] alone when no customer was derived (Scenario 3, 8), or
    ["customer/<slug>", "kind/meeting"] when one was (Scenario 1)."""
    if not customer:
        return ["kind/meeting"]
    return [f"customer/{tag_slug(customer)}", "kind/meeting"]


def create_meeting_note_baseline(
    note_path: Path,
    customer: str | None,
    organizer: str,
    teams_link: str,
    dial_in: str,
    is_recurring: bool,
    calendar_id: str,
) -> str:
    """Creates a Meeting note for the first time, at the already-resolved
    note_path (REQ-SB-71-US-03-T01, ADR-048 Decision 5) — one-time:
    meeting_note_path(subject, start)'s own unchanged path; recurring:
    meeting_series_directory_paths(series_id)["concept"]. Baseline
    frontmatter is logistics-only: type/customer/tags/thread (this app's
    own internal bookkeeping, unchanged) plus teams_link/dial_in/
    organizer/recurrence and EXACTLY ONE of calendar_event_id (one-time)
    or calendar_series_id (recurring) — subject/start/end/location and the
    raw invite body are never persisted (the deliberate, operator-
    authorized "raw calendar invite is noise, not data" exception to this
    project's own archive-not-delete discipline). `attendees` starts as an
    empty wikilink list, topped up by the SAME call classify_recent_
    meetings already makes for the body's own **Attendees:** line (T03).
    Body is the new shared shape for both one-time and recurring: `##
    Summary` (agent-owned, regenerated) + `## History` (agent-owned,
    growing, one dated entry per occurrence) + `## Personal Notes`/
    `## Actions` (human-owned), all empty at creation. Always writes
    unconditionally, mirroring every other create_*_baseline's own
    contract — callers must resolve/check note_path's own existence
    first."""
    frontmatter: dict = {
        "type": "Meeting",
        "customer": customer or "",
        "tags": build_meeting_tags(customer),
        "thread": "",
        "teams_link": teams_link,
        "dial_in": dial_in,
        "organizer": organizer,
        "recurrence": is_recurring,
        "attendees": [],
    }
    frontmatter["calendar_series_id" if is_recurring else "calendar_event_id"] = calendar_id
    _write_frontmatter_note(
        note_path, frontmatter,
        "## Summary\n\n## History\n\n## Personal Notes\n\n## Actions\n",
    )
    return str(note_path)


def ensure_meeting_note_baseline_frontmatter(
    path,
    customer: str | None,
    organizer: str,
    teams_link: str,
    dial_in: str,
    is_recurring: bool,
    calendar_id: str,
) -> list[str]:
    """Tops up an already-existing Meeting note (one-time or recurring)
    with any of the new baseline frontmatter keys it is missing —
    REQ-SB-71-US-03-T01's own retarget of the prior nine-key baseline to
    the new logistics-only shape — inserting each surgically via insert_
    frontmatter_key_if_missing, never touching a key already present, and
    never touching the body. `calendar_event_id`/`calendar_series_id` top
    up whichever ONE applies to this note's own shape (one-time vs.
    recurring), mirrored by is_recurring. Returns the list of keys
    actually inserted (empty if the note already had all of them) — the
    same baseline-preservation contract every other note kind's own
    ensure_*_baseline_frontmatter already established."""
    baseline_values = {
        "type": "Meeting",
        "customer": customer or "",
        "tags": build_meeting_tags(customer),
        "thread": "",
        "teams_link": teams_link,
        "dial_in": dial_in,
        "organizer": organizer,
        "recurrence": is_recurring,
        "attendees": [],
    }
    inserted: list[str] = []
    for key in _MEETING_NOTE_BASELINE_KEYS:
        if insert_frontmatter_key_if_missing(path, key, baseline_values[key]):
            inserted.append(key)
    calendar_key = "calendar_series_id" if is_recurring else "calendar_event_id"
    if insert_frontmatter_key_if_missing(path, calendar_key, calendar_id):
        inserted.append(calendar_key)
    return inserted


def _processed_meetings_path():
    state_dir = settings.second_brain_data_path
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _PROCESSED_MEETINGS_FILE


def load_processed_meeting_ids() -> set[str]:
    path = _processed_meetings_path()
    if not path.exists():
        return set()
    return set(json.loads(path.read_text(encoding="utf-8")))


def mark_meeting_processed(marker: str) -> None:
    """Mirrors mark_email_processed's exact shape (ADR-008) — a flat,
    idempotent set-of-IDs audit record. Adding an already-present marker
    is a no-op. Note: meeting_classification.py (T03) does not gate
    reprocessing on this file the way email capture gates on
    processed_email_ids — see T03's own Context/Notes for why (Scenario
    2/6 require an in-window event to still flow through the top-up path
    on every rerun). The caller now passes the resolved note's own
    filename stem (ADR-019) rather than a separately-computed
    identifier — once there is no single "the" per-occurrence Outlook
    identifier, computing one specially just for this audit-trail call is
    unnecessary busywork, and the note's own filename stem is already the
    exact per-occurrence disambiguator under whichever tier
    resolve_meeting_note_path actually resolved. The file's existing
    heterogeneous EntryID-era and GlobalAppointmentID-era entries
    (written by earlier code, ADR-008/ADR-013) are left untouched: still
    an audit trail for future observability (REQ-SB-11), never a
    schema-enforced lookup structure any code path depends on for
    uniqueness."""
    path = _processed_meetings_path()
    processed = load_processed_meeting_ids()
    processed.add(marker)
    path.write_text(json.dumps(sorted(processed), indent=2), encoding="utf-8")


def upsert_attendee_links(path, person_stems: list[str]) -> bool:
    """Upserts the growable **Attendees:** [[P1]], [[P2]], ...] body line —
    unlike the single-target insert_body_line_if_missing (a link is either
    present or not), this line can legitimately grow across reruns as new
    attendees are confirmed (Scenario 6). If no Attendees line exists yet,
    inserts one as the first line of the body (mirroring
    insert_body_line_if_missing's insert-at-body-start contract). If one
    already exists, merges in any person_stems not already linked —
    preserving existing wikilink order, appending new ones, updating the
    line in place rather than moving it — never removes an existing
    wikilink. Returns True if the line was created or grew, False if every
    stem in person_stems was already present (a true no-op rerun) or if
    person_stems is empty (Scenario 8 — no attendees, no Attendees line at
    all)."""
    if not person_stems:
        return False
    text = path.read_text(encoding="utf-8")
    match = _ATTENDEES_LINE_PATTERN.search(text)
    if match is None:
        new_line = _ATTENDEES_LINE_PREFIX + ", ".join(f"[[{stem}]]" for stem in person_stems)
        end = text.find("\n---\n", 4)
        if end == -1:
            path.write_text(new_line + "\n\n" + text, encoding="utf-8")
            return True
        body_start = end + 6
        new_text = text[:body_start] + new_line + "\n\n" + text[body_start:]
        path.write_text(new_text, encoding="utf-8")
        return True

    existing_stems = WIKILINK_PATTERN.findall(match.group(1))
    merged_stems = list(existing_stems)
    changed = False
    for stem in person_stems:
        if stem not in merged_stems:
            merged_stems.append(stem)
            changed = True
    if not changed:
        return False
    new_line = _ATTENDEES_LINE_PREFIX + ", ".join(f"[[{stem}]]" for stem in merged_stems)
    new_text = text[: match.start()] + new_line + text[match.end() :]
    path.write_text(new_text, encoding="utf-8")
    return True


_THREADS_SUBFOLDER = f"{_WORK_ROOT}/Threads"
_THREAD_NOTE_BASELINE_KEYS = ("type", "conversation_id", "tags", "thread_name")


def thread_note_path(conversation_id: str):
    """Resolves the vault-absolute path a Thread note lives (or would
    live) at — Work/Threads/<slug-of-conversation_id>.md — without
    checking whether it exists yet. Pure, deterministic function of
    conversation_id alone (ADR-042 point 5), mirroring hub_note_path/
    meeting_note_path's own "deterministic path from a stable key, no
    separate lookup index" precedent — never conversation_index.json,
    which stays owned by today's still-live email_classification.py until
    REQ-SB-55 replaces it. Work/Threads/ needs no list_known_kinds()
    change — it is discovered dynamically by directory name, same as
    every other Work/<kind>/ folder."""
    return settings.vault_path / _THREADS_SUBFOLDER / f"{_slugify(conversation_id)}.md"


def thread_note_exists(conversation_id: str) -> bool:
    return thread_note_path(conversation_id).exists()


def thread_directory_paths(conversation_id: str) -> dict:
    """Resolves the deterministic path set for the redesigned Thread
    directory shape (`REQ-SB-71-US-02`, `ADR-048` Decision 3) —
    `Work/Threads/<slug-of-conversation_id>/`, permanently deterministic
    from `conversation_id` alone, reverting `ADR-042` point 5's ORIGINAL
    scheme and superseding `ADR-046`'s own human-readable/renamable-
    filename mechanism (no longer needed: the human-readable identity now
    lives in the concept file's own `thread_name` frontmatter, not the
    directory/file name). Mirrors `okf_directory_paths`'s own shape but
    WITHOUT `index.md`/`log.md`/`captures.md` — a genuinely different,
    simpler 2-part convention; `ADR-042` point 1's own "Customer and
    Project are the ONLY two 4-file-OKF-shaped kinds" scope-lock is not
    reopened by this addition. Pure, deterministic, no I/O — does not
    check whether any of the three paths exist yet."""
    concept_slug = _slugify(conversation_id)
    base = settings.vault_path / _THREADS_SUBFOLDER / concept_slug
    return {
        "directory": base,
        "concept": base / f"{concept_slug}.md",
        "messages": base / "messages",
    }


def create_thread_note_baseline(
    conversation_id: str, thread_name: str, tags: list[str] | None = None
) -> str:
    """Creates a Thread's distilled concept file for the first time, under
    the redesigned 2-part directory shape (`REQ-SB-71-US-02`, `ADR-048`
    Decision 3) — REWRITES this function's own prior single-file/
    renamable-filename shape (`ADR-046` Decisions 6/7): baseline
    frontmatter (type/conversation_id/tags/thread_name) with a body of
    four sections, `## Summary` (agent-owned, regenerated) + `##
    Personal Notes` (human-owned) + `## Actions` (human-owned, a literal
    checklist) + `## Related` (agent-owned, regenerated) — `##
    Transcript` is RETIRED, superseded by the `messages/` directory
    itself, which now carries the full verbatim content `##
    Transcript`'s own terse one-liners never did. `thread_name` (`ADR-046`
    Decision 6's own "captured once, stable across the Thread's life"
    property, preserved) is the FIRST message's own subject, captured
    once here and never recomputed on a later message. `date` is no
    longer a parameter — the new scheme needs no filename-date component,
    since the concept file's own path is deterministic from
    `conversation_id` alone via `thread_directory_paths`. Always writes
    unconditionally, mirroring every other `create_*_baseline`'s own
    contract — callers must resolve whether the Thread already exists
    first (via `resolve_thread_note_path()`)."""
    paths = thread_directory_paths(conversation_id)
    _write_frontmatter_note(
        paths["concept"],
        {
            "type": "Thread",
            "conversation_id": conversation_id,
            "tags": tags or [],
            "thread_name": thread_name,
        },
        "## Summary\n\n## Personal Notes\n\n## Actions\n\n## Related\n",
    )
    return str(paths["concept"])


def raw_message_note_path(
    conversation_id: str, message_id: str, received: str, readable_name: str | None = None,
) -> Path:
    """Resolves the vault-absolute path one raw message note lives (or
    would live) at — `<thread's own current messages/ directory>/
    "<received[:10]>-<hash8(message_id)>.md"` (`REQ-SB-71-US-02`, `ADR-048`
    Decision 3; retargeted `REQ-SB-72-US-01-T01`, `ADR-049` Decision 1) —
    without checking whether it exists yet. Mirrors `meeting_note_filename_
    stem`'s own hash-suffix disambiguation shape: `message_id` is the
    email's own `id`/EntryID field, already unique per message, hashed
    (`sha256(message_id)[:8]`) so two messages received on the same day
    never collide. Resolve-first, deterministic-fallback (mirrors `resolve_
    meeting_note_path`'s own established two-tier shape): composes `resolve_
    thread_directory` first — if the Thread's directory already exists
    (possibly renamed), the note is written under THAT directory's own
    `messages/`; only for a genuinely brand-new Thread (no directory yet)
    does this fall back to the deterministic `thread_directory_paths(
    conversation_id)["messages"]` path, the directory `create_thread_note_
    baseline` is about to create it at.

    `readable_name` (2026-08-21, additive, operator: "messages inside the
    thread same title issue") — when given (e.g. the sender's own name),
    the filename becomes `"<received[:10]> <slug-of-readable_name>.md"`
    instead of the hash-suffixed form, unless that exact path is already
    taken by a DIFFERENT message (a genuine same-day-same-sender
    collision — checked by reading the existing candidate's own
    `message_id` frontmatter and comparing, not just path existence; a
    real bug found live, 2026-08-21: re-resolving a message's OWN already-
    written path via this same readable-name branch, e.g. to build a
    cross-link elsewhere, was wrongly treating "a file already exists
    here" as a collision even when it was this exact message's own note,
    silently shifting the resolved path to the hash-suffixed form),
    in which case the hash suffix is appended to the readable stem rather
    than silently colliding. Every existing caller that passes nothing
    (raw_message_capture.py's own Stage 1) sees zero behavior change —
    purely additive, same discipline as `list_recent_mail`'s own `since`/
    `before` parameters."""
    directory = resolve_thread_directory(conversation_id)
    messages_dir = (
        directory / "messages" if directory is not None
        else thread_directory_paths(conversation_id)["messages"]
    )
    if readable_name is not None:
        # 2026-08-21 bug fix: date-only + sender name collapses back into
        # indistinguishable filenames whenever the SAME sender posts more
        # than once in a thread on the same day (the common back-and-forth
        # case) -- both land on the same stem, and the hash-suffix
        # fallback below then makes the second one "Name-a1b2c3d4.md",
        # which in Obsidian's file view still just reads "Name" -- no way
        # to tell them apart or that there are two (found live against the
        # Hermes-native port of this same function, `Hermes-Provisioning/
        # skills/vault-rebuild/email-thread-capture/scripts/vault_lib.py`,
        # ported back here for consistency). Including time-of-day (HH:MM,
        # almost always unique per message) fixes this directly and is
        # more informative than a hash ever was. The hash-suffix fallback
        # stays as a safety net for a genuine same-minute tie, now a rare
        # edge case instead of the common one.
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
    conversation_id: str, message_id: str, received: str, readable_name: str | None = None,
) -> bool:
    """Existence check the caller (Stage 1) MUST call before ever calling
    `create_raw_message_note` — mirrors `person_note_exists`'s own
    "callers must check first" contract; enforces the write-once
    guarantee by caller discipline, since `create_raw_message_note`
    itself does not defensively re-check. `readable_name` must match
    whatever `create_raw_message_note` will be called with, or this check
    resolves a different candidate path than the write will actually use."""
    return raw_message_note_path(conversation_id, message_id, received, readable_name).exists()


def create_raw_message_note(
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
    """Writes ONE immutable, verbatim raw message note (`REQ-SB-71-US-02`,
    `ADR-048` Decision 3) — the operator's own root pain (losing real
    email content across a stalled/imperfect re-synthesis) is what this
    primitive structurally resolves: the message's own real body is
    preserved byte-for-byte, forever, regardless of what any later Stage 2
    re-synthesis does. Frontmatter carries `message_id`/`sender`/
    `sender_email`/`subject`/`received`/`conversation_id`; body is the raw
    message content verbatim, unmodified. Always writes unconditionally —
    no existence-check inside (the caller already checked via `raw_
    message_note_exists`), mirroring every other `create_*_baseline`'s own
    "always writes unconditionally, caller checks first" contract. Never
    edited again once written by any caller in this codebase — write-once
    is a contract enforced by caller discipline, not a file-permission
    mechanism.

    `participant_links` (2026-08-21, additive, operator: "like the People
    to Emails as well not only thread" then "not only Sender everyone in
    the email") — a list of already-formed wikilink strings (e.g.
    `["[[shadi.shaat@core42.ai]]", "[[mohammed.retmi@core42.ai]]"]`) to
    every participant's own Person note (sender AND every recipient),
    added to frontmatter as `participant_links` when given. MUST be
    embedded here, at creation time — this note is write-once, so there
    is no later "patch in the link" step the way `## Related` on a
    Thread note can be. Every existing caller that passes nothing
    (`raw_message_capture.py`'s own Stage 1) sees zero behavior change."""
    path = raw_message_note_path(conversation_id, message_id, received, readable_name)
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


def ensure_thread_note_baseline_frontmatter(
    path, conversation_id: str, thread_name: str, tags: list[str] | None = None
) -> list[str]:
    """Tops up an already-existing Thread note with any of the four
    baseline frontmatter keys it is missing, inserting each surgically via
    insert_frontmatter_key_if_missing — never touches a key already
    present, and never touches the body. Returns the list of keys actually
    inserted (empty if the note already had all four baseline keys) —
    same baseline-preservation contract every other note kind's own
    ensure_*_baseline_frontmatter already established. `thread_name`
    mirrors the same top-up-only-if-missing contract as `type`/
    `conversation_id`/`tags` — an already-present thread_name (the
    original first-message subject) is never overwritten by a later
    message's own subject, preserving ADR-046 Decision 6's "captured once,
    stable across the Thread's life" property even for a pre-REQ-SB-69
    note being topped up for the first time. Tag accumulation/union logic
    across updates is explicitly out of this task's own scope (REQ-SB-55's
    own job, per REQ-SB-54-US-01's Constraints) — this only tops up the
    initial `tags` value if the key is missing entirely, it never merges
    into an already-present one."""
    baseline_values = {
        "type": "Thread",
        "conversation_id": conversation_id,
        "tags": tags or [],
        "thread_name": thread_name,
    }
    inserted: list[str] = []
    for key in _THREAD_NOTE_BASELINE_KEYS:
        if insert_frontmatter_key_if_missing(path, key, baseline_values[key]):
            inserted.append(key)
    return inserted


def list_thread_notes() -> list[Path]:
    """Every Thread's own distilled CONCEPT file under the redesigned
    2-level directory shape (`REQ-SB-71-US-02`, `ADR-048` Decision 7) —
    globs `Work/Threads/*/*.md`, filtered to `path.parent.name ==
    path.stem` (matches only `<slug>/<slug>.md`; a raw message note's own
    parent directory is literally named `messages`, never equal to its own
    stem, so every raw message note is correctly excluded). Composed by
    `list_threads_for_project`, Meeting's own fallback linker
    (`meeting_classification.py`), and `resolve_thread_note_path` below —
    never a second, independent Thread-enumeration mechanism. Returns []
    if `Work/Threads/` doesn't exist yet — same not-yet-created-folder
    contract this function always had."""
    threads_root = settings.vault_path / _THREADS_SUBFOLDER
    if not threads_root.exists():
        return []
    return sorted(
        path for path in threads_root.glob("*/*.md")
        if path.parent.name == path.stem
    )


def list_threads_for_project(customer: str, project: str) -> list[Path]:
    """Every currently-linked Thread for one Project (`REQ-SB-57-US-01-T01`)
    -- composes `list_thread_notes()` directly (never a new, second
    `Work/Threads/` glob), filtering by reading each Thread's own current
    `customer`/`project` frontmatter for an exact match. Returns `[]` if
    none match -- never raises for a Project with no linked Threads yet,
    mirroring every other "not-yet-linked" contract already established in
    this module (e.g. `list_customer_projects`)."""
    matches: list[Path] = []
    for path in list_thread_notes():
        frontmatter, _ = read_note(path)
        if frontmatter.get("customer") == customer and frontmatter.get("project") == project:
            matches.append(path)
    return matches


def thread_note_filename_stem(thread_name: str, date: str, conversation_id: str) -> str:
    """<thread_name>-<date>-<hash8> — mirrors meeting_note_filename_stem's
    own <subject>-<date>-<hash-suffix> shape exactly (ADR-046 Decision 6),
    with one deliberate divergence from Meeting's own scheme: the hash
    suffix here is derived from `conversation_id` ALONE
    (`sha256(conversation_id)[:8]`), never `f"{thread_name}|{date}"` the
    way Meeting hashes `f"{subject}|{start}"`. This is load-bearing, not a
    style choice: a Thread's own `date` component is the mutable
    last_message_at[:10], which changes on every later message in the same
    conversation (Scenario 7) — if the hash suffix depended on `date` too,
    every later message would also change the disambiguator, defeating the
    whole point of a stable, renamable-in-place filename. Hashing
    conversation_id alone keeps the suffix constant across the Thread's
    entire life, so renaming (rename_thread_note, below) only ever changes
    the date component, never the identity-bearing suffix."""
    suffix = hashlib.sha256(conversation_id.encode("utf-8")).hexdigest()[:8]
    return f"{thread_name}-{date}-{suffix}"


def thread_note_path_for(thread_name: str, date: str, conversation_id: str):
    """Resolves the vault-absolute path a Thread note with this
    thread_name/date/conversation_id would live at —
    Work/Threads/<slug-of-stem>.md — without checking whether it exists
    yet. Mirrors meeting_note_path's own "resolves without checking
    existence" shape, composing thread_note_filename_stem above the same
    way meeting_note_path composes meeting_note_filename_stem. Uses the
    same _slugify() write_note() applies to its own filename_stem, so this
    always points at exactly the file a write under this stem would
    create."""
    stem = thread_note_filename_stem(thread_name, date, conversation_id)
    return settings.vault_path / _THREADS_SUBFOLDER / f"{_slugify(stem)}.md"


def migrate_flat_thread_to_directory(flat_path: Path) -> Path:
    """One-time, idempotent, self-healing migration (BUGFIX-05-US-01,
    ADR-052) of a legacy, pre-redesign FLAT Work/Threads/<name>.md
    Thread note (zero intermediate directory segments) to the
    standard 2-level directory shape thread_directory_paths(
    conversation_id) already establishes for every Thread created
    after ADR-048 -- the SAME deterministic location a brand-new
    Thread is always first created at, reused unchanged, never a
    second naming derivation. Mirrors rename_thread_directory's own
    refuse-to-overwrite discipline one level up: raises
    FileExistsError if the deterministic target directory already
    exists (a structurally near-impossible conversation_id-slug
    collision), never silently overwriting. Reads conversation_id
    from flat_path's own frontmatter directly -- the caller
    (resolve_thread_directory's own second scan tier) has already
    matched on it, but this function re-derives it independently so
    it stays a correct, callable-on-its-own primitive, not one that
    silently trusts an unchecked caller-supplied id. Creates the
    target directory, moves/renames the flat file to
    <slug>/<slug>.md, creates an empty messages/ subdirectory
    alongside it -- touches only filesystem SHAPE (one directory
    creation, one file move/rename, one empty subdirectory
    creation), never note body or frontmatter content -- EXCEPT for
    one narrow, disclosed exception (BUGFIX-05-US-01, ADR-053):
    BEFORE the rename, reads the flat note's own pre-migration
    ## Summary via the existing read_body_section primitive (no new
    reader) and, if non-empty, writes it VERBATIM to a new sidecar
    file, <new-directory>/pre_migration_summary.md -- plain text, no
    frontmatter, created AFTER the target directory but BEFORE the
    flat file is renamed, living OUTSIDE messages/ so it is
    structurally invisible to list_thread_notes() and to
    synthesize_thread's own messages_dir glob. If the flat note's
    own ## Summary is empty, no sidecar file is written -- a true
    no-op. synthesize_thread folds this sidecar into its own next
    real synthesis as prior-history grounding and archives it to
    pre_migration_summary.consumed.md on success. Returns the new
    concept file path."""
    frontmatter, _ = read_note(flat_path)
    conversation_id = frontmatter["conversation_id"]
    paths = thread_directory_paths(conversation_id)
    if paths["directory"].exists():
        raise FileExistsError(
            f"would overwrite existing Thread directory at {paths['directory']}"
        )
    paths["directory"].mkdir(parents=True, exist_ok=True)
    pre_migration_summary = read_body_section(flat_path, "## Summary")
    if pre_migration_summary:
        (paths["directory"] / "pre_migration_summary.md").write_text(
            pre_migration_summary, encoding="utf-8"
        )
    flat_path.rename(paths["concept"])
    paths["messages"].mkdir(parents=True, exist_ok=True)
    return paths["concept"]


def resolve_thread_directory(conversation_id: str) -> Path | None:
    """The ONE place "does a Thread for this conversation_id already
    exist, and if so, where" is answered going forward (`REQ-SB-72-
    US-01-T01`, `ADR-049` Decision 1) -- a frontmatter-based scan,
    composing the existing `list_thread_notes()` (never a second,
    independent Thread-enumeration mechanism), matching `frontmatter.
    get("conversation_id") == conversation_id`. Returns the Thread's
    own DIRECTORY (`path.parent`), or `None` if no directory-shaped
    Thread matches.

    On a miss, a SECOND scan tier (`BUGFIX-05-US-01`, `ADR-052`)
    globs `Work/Threads/*.md` directly -- flat, pre-redesign notes
    only, deliberately NOT folded into `list_thread_notes()` itself
    (`ADR-052` Decision 4) -- for the SAME `conversation_id`
    frontmatter match. On a match, immediately calls `migrate_flat_
    thread_to_directory` and returns the NEW directory -- never a
    flat file's own path or parent directly. This is the ONE
    deliberate exception to this function's own otherwise
    purely-read-only contract: a one-time, idempotent, self-healing
    WRITE for this legacy flat-shape case only (`ADR-052` Decision
    5, narrowing `ADR-049` Decision 1's "purely read-only" framing
    for this one case).

    Ordering is load-bearing: the directory-shaped scan always runs
    FIRST, so a `conversation_id` that already has BOTH a flat note
    and a directory-shaped duplicate correctly, silently no-ops on
    the second tier -- the existing duplicate is returned, the
    already-orphaned flat note is left alone (a deliberate,
    disclosed non-goal, `ADR-052` Consequences / `ESC-055`)."""
    for path in list_thread_notes():
        frontmatter, _ = read_note(path)
        if frontmatter.get("conversation_id") == conversation_id:
            return path.parent

    threads_root = settings.vault_path / _THREADS_SUBFOLDER
    if threads_root.exists():
        for flat_path in threads_root.glob("*.md"):
            frontmatter, _ = read_note(flat_path)
            if frontmatter.get("conversation_id") == conversation_id:
                migrated_concept_path = migrate_flat_thread_to_directory(flat_path)
                return migrated_concept_path.parent

    return None


def resolve_thread_note_path(conversation_id: str) -> Path | None:
    """PUBLIC SIGNATURE UNCHANGED — retargeted a SECOND time (`REQ-SB-72-
    US-01-T01`, `ADR-049` Decision 1, partially superseding `ADR-048`
    Decision 3/7's own "permanent deterministic-path" sub-decision only)
    to a thin wrapper over `resolve_thread_directory`:
    `directory / f"{directory.name}.md"` if a match is found, else `None`.
    This is what lets every real existing caller
    (`_link_to_thread_by_conversation_id`, `_trigger_project_resynthesis`,
    `synthesize_thread`'s own create-vs-update check,
    `meeting_classification.py`'s linked-Thread lookups) keep working with
    ZERO change to its own call site — it still calls `resolve_thread_note_
    path(conversation_id)` and gets back a `Path | None`, exactly as
    before. Reverts to composing `list_thread_notes()` (via `resolve_
    thread_directory`) once again — a Thread's own directory name is no
    longer guaranteed to match its `conversation_id` slug once it has been
    renamed (`rename_thread_directory`, below), so a deterministic-path
    existence check alone would silently miss any already-renamed Thread.
    Purely read-only: never creates, writes, or renames anything."""
    directory = resolve_thread_directory(conversation_id)
    if directory is None:
        return None
    return directory / f"{directory.name}.md"


def rename_thread_note(old_path, new_path) -> None:
    """Physically renames a Thread note in place (old_path.rename(new_path)
    after ensuring new_path's parent directory exists) — the mechanism
    ADR-046 Decision 7 needs whenever thread_match_merge computes a freshly
    -derived filename (the date component changed) for an already-existing
    Thread. Mirrors move_note_and_attachments's own refuse-to-silently-
    overwrite discipline: raises FileExistsError if new_path already
    exists and is not old_path itself, rather than silently destroying an
    unrelated Thread's content at a genuine filename collision (Scenario
    6). A no-op (returns without touching the filesystem) when
    old_path == new_path — a Thread whose freshly-derived filename didn't
    actually change on this call, the common case for two updates landing
    on the same calendar day. Unlike move_note_and_attachments, this never
    moves a sibling attachments/<note_slug>/ folder — Thread notes don't
    have their own attachments subfolder (Attachments are recorded inline
    in the note's own body, per REQ-SB-55), so there is nothing sibling to
    carry over."""
    if old_path == new_path:
        return
    if new_path.exists():
        raise FileExistsError(f"would overwrite existing note at {new_path}")
    new_path.parent.mkdir(parents=True, exist_ok=True)
    old_path.rename(new_path)


def rename_thread_directory(old_directory: Path, new_directory: Path) -> Path:
    """A real, atomic whole-directory move (`REQ-SB-72-US-01-T01`, `ADR-049`
    Decision 2) — one level up from `rename_thread_note`'s own existing
    single-file discipline, above. No-op if `old_directory == new_
    directory` — returns the (unchanged) concept path directly, no
    filesystem operation performed. Raises `FileExistsError` if `new_
    directory` already exists (a genuine `<date> <subject>` collision —
    surfaced, never silently overwritten, mirroring `rename_thread_note`'s
    own refuse-to-overwrite discipline one level up). Otherwise `old_
    directory.rename(new_directory)` moves the WHOLE tree — concept file,
    `messages/`, any `files/` — in one atomic filesystem op, then the
    concept file inside is itself renamed from `<old-slug>.md` to
    `<new-slug>.md`, preserving the `<slug>/<slug>.md` invariant `list_
    thread_notes()` depends on. Returns the new concept file path."""
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


_PARTNERS_SUBFOLDER = f"{_WORK_ROOT}/Partners"
_PARTNER_HUB_NOTE_BASELINE_KEYS = ("type", "partner", "tags", "affiliate_of")


def partner_hub_note_path(partner: str):
    """Resolves the vault-absolute path a partner's hub note lives (or
    would live) at — Work/Partners/<Partner>.md — mirroring
    hub_note_path exactly, for the Partner namespace (ADR-009)."""
    return settings.vault_path / _PARTNERS_SUBFOLDER / f"{_slugify(partner)}.md"


def partner_hub_note_exists(partner: str) -> bool:
    return partner_hub_note_path(partner).exists()


def build_partner_tags(partner: str) -> list[str]:
    """Mirrors build_tags's shape for the Partner tag namespace —
    partner/<slug> is deliberately never customer/<slug> (ADR-009,
    partner/<slug> and customer/<slug> are mutually exclusive)."""
    return [f"partner/{tag_slug(partner)}", "kind/partner"]


def create_partner_hub_note_baseline(partner: str) -> str:
    """Creates a partner's hub note for the first time: baseline
    frontmatter (type/partner/tags/affiliate_of — Partner now legitimately
    carries affiliate_of, narrowly revising ADR-009 point 3, ADR-057
    Decision 4/REQ-SB-76-US-01-T02) plus the same auto-generated body stub
    convention create_customer_hub_note_baseline already uses. Always
    writes unconditionally, mirroring write_note()'s own contract —
    callers must check partner_hub_note_exists() first
    (app/business/partner_hub_linking.py does)."""
    return write_note(
        subfolder=_PARTNERS_SUBFOLDER,
        filename_stem=partner,
        frontmatter={
            "type": "Partner",
            "partner": partner,
            "tags": build_partner_tags(partner),
            "affiliate_of": "",
        },
        body=(
            f"# {partner}\n\n"
            "_Add your own overview, key contacts, and current focus "
            "below — this section is never programmatically rewritten "
            "once you do._\n"
        ),
    )


def ensure_partner_hub_note_baseline_frontmatter(path, partner: str) -> list[str]:
    """Tops up an already-existing partner hub note with any of the four
    baseline frontmatter keys it is missing (type/partner/tags/
    affiliate_of), mirroring ensure_hub_note_baseline_frontmatter's exact
    contract for Partner's key set. Never touches a key already present or
    the body. Returns the list of keys actually inserted."""
    baseline_values = {
        "type": "Partner",
        "partner": partner,
        "tags": build_partner_tags(partner),
        "affiliate_of": "",
    }
    inserted: list[str] = []
    for key in _PARTNER_HUB_NOTE_BASELINE_KEYS:
        if insert_frontmatter_key_if_missing(path, key, baseline_values[key]):
            inserted.append(key)
    return inserted


def list_known_partners() -> list[str]:
    """Dynamic, vault-derived replacement for a hardcoded partner list —
    mirrors list_known_customers()'s exact frontmatter-scan pattern,
    reading the `partner` field across every note instead of `customer`
    (ADR-009). Never hardcoded."""
    partners: set[str] = set()
    for path in list_all_note_paths():
        frontmatter, _ = read_note(path)
        partner = frontmatter.get("partner")
        if partner:
            partners.add(partner)
    return sorted(partners)


def _agent_history_path():
    state_dir = settings.second_brain_data_path
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _AGENT_HISTORY_FILE


def _load_agent_history_index() -> dict[str, list[dict]]:
    path = _agent_history_path()
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def append_agent_history_entry(
    agent_id: str, kind: str, text: str, pending_approval_id: str | None = None,
) -> None:
    """Appends one entry to agent_id's chronological history list
    (ADR-011) — kind is "chat_user" | "chat_agent" | "run_event" |
    "proposal" (ADR-018 point 7 adds "proposal"). pending_approval_id is
    new and optional, additive — every existing caller (positional
    agent_id/kind/text, no fourth argument) is unaffected; only a
    "proposal"-kind entry supplies it, carrying the pending-approval
    record's own id so the frontend can resolve the card's live
    Pending/Approved/Declined status via GET /pending-approvals/{id}.
    Entries are appended in call order and read back in that same
    order (load_agent_history does not re-sort) — every caller
    (scheduler, app-start, /poc/classify-emails,
    POST /agents/{id}/chat, POST /agents/{id}/actions/{action_id})
    already calls this at the moment the event actually happens, so
    append order already is chronological order."""
    path = _agent_history_path()
    index = _load_agent_history_index()
    entry = {
        "kind": kind,
        "text": text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if pending_approval_id is not None:
        entry["pending_approval_id"] = pending_approval_id
    index.setdefault(agent_id, []).append(entry)
    path.write_text(json.dumps(index, indent=2), encoding="utf-8")


def load_agent_history(agent_id: str) -> list[dict]:
    return _load_agent_history_index().get(agent_id, [])




def _agent_memory_path():
    state_dir = settings.second_brain_data_path
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _AGENT_MEMORY_FILE


def _load_agent_memory_index() -> dict[str, list[dict]]:
    path = _agent_memory_path()
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_agent_memory(agent_id: str) -> list[dict]:
    return _load_agent_memory_index().get(agent_id, [])


def append_agent_memory_entries(agent_id: str, facts: list[str]) -> None:
    """Appends one entry per fact string to agent_id's growing memory
    list (ADR-016 point 3) -- a no-op (no file write at all, no file
    created) when facts is empty, so a reply that extracted nothing
    worth remembering (Scenario 3's own honest "no fact" outcome) never
    touches agent_memory.json. Flat, append-only -- no dedup/merge/
    consolidation this pass (ADR-016 point 3), mirroring
    append_agent_history_entry's own "already chronological because
    callers append at the moment the event happens" contract, extended
    to a list of facts arriving from one extraction call at once instead
    of one entry at a time."""
    if not facts:
        return
    path = _agent_memory_path()
    index = _load_agent_memory_index()
    recorded_at = datetime.now(timezone.utc).isoformat()
    index.setdefault(agent_id, []).extend(
        {"fact": fact, "recorded_at": recorded_at} for fact in facts
    )
    path.write_text(json.dumps(index, indent=2), encoding="utf-8")


def _skills_state_path():
    state_dir = settings.second_brain_data_path
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _AGENT_SKILLS_FILE


def load_skills_state() -> dict | None:
    """Pure I/O — returns None if agent_skills.json doesn't exist yet (no
    default content is computed here, per ADR-003; explicit-grant-only,
    no self-healing default assignment, is a business-layer decision
    owned by app/business/skill_registry.py)."""
    path = _skills_state_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_skills_state(state: dict) -> None:
    path = _skills_state_path()
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _agent_keywords_path():
    state_dir = settings.second_brain_data_path
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _AGENT_KEYWORDS_FILE


def _load_agent_keywords_index() -> dict[str, list[str]]:
    path = _agent_keywords_path()
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_agent_keywords(agent_id: str) -> list[str]:
    """Pure I/O — returns [] if agent_keywords.json doesn't exist yet, or
    if agent_id has no entry in it (ADR-017 point 2/4: an agent with no
    keywords is the ordinary, expected starting state — no seed list,
    unlike Sections/Providers, since free-text keywords have no sensible
    universal default)."""
    return _load_agent_keywords_index().get(agent_id, [])


def save_agent_keywords(agent_id: str, keywords: list[str]) -> None:
    """Whole-list replace for agent_id's own entry — mirrors the
    free-text kv-list editing UX the Settings panel already uses for
    other per-agent fields (ADR-017 point 3); no incremental
    add/remove-one-keyword primitive exists or is needed."""
    path = _agent_keywords_path()
    index = _load_agent_keywords_index()
    index[agent_id] = keywords
    path.write_text(json.dumps(index, indent=2), encoding="utf-8")


def load_all_agent_keywords() -> dict[str, list[str]]:
    """Whole-file read — needed because the routing node (REQ-SB-20-US-01-T05)
    must scan every OTHER agent's keywords, not one agent's own; no
    existing vault_writer primitive does a whole-file read for a
    per-agent-keyed store (ADR-017 point 2)."""
    return _load_agent_keywords_index()


def _working_modes_state_path():
    state_dir = settings.second_brain_data_path
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _AGENT_WORKING_MODES_FILE


def load_working_modes_state() -> dict | None:
    """Pure I/O — returns None if agent_working_modes.json doesn't exist
    yet (no default content is computed here, per ADR-003; the
    self-healing "autonomous" default is a business-layer decision,
    owned by app/business/working_mode_registry.py, ADR-018 point 1)."""
    path = _working_modes_state_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_working_modes_state(state: dict) -> None:
    path = _working_modes_state_path()
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _agent_visuals_state_path():
    state_dir = settings.second_brain_data_path
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _AGENT_VISUALS_FILE


def load_agent_visuals_state() -> dict | None:
    """Pure I/O — returns None if agent_visuals.json doesn't exist yet
    (no default content computed here, per ADR-003; the "no override yet"
    default is a business-layer decision, owned by app/business/
    agent_visual_registry.py)."""
    path = _agent_visuals_state_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_agent_visuals_state(state: dict) -> None:
    path = _agent_visuals_state_path()
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _background_agent_flags_state_path():
    state_dir = settings.second_brain_data_path
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _AGENT_BACKGROUND_FLAGS_FILE


def load_background_agent_flags_state() -> dict | None:
    """Pure I/O — returns None if agent_background_flags.json doesn't
    exist yet (no default content is computed here, per ADR-003; the
    self-healing default per agent is a business-layer decision, owned
    by app/business/background_agent_registry.py)."""
    path = _background_agent_flags_state_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_background_agent_flags_state(state: dict) -> None:
    path = _background_agent_flags_state_path()
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _agent_schedules_state_path():
    state_dir = settings.second_brain_data_path
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _AGENT_SCHEDULES_FILE


def load_agent_schedules_state() -> dict | None:
    """Pure I/O — returns None if agent_schedules.json doesn't exist yet
    (no default content is computed here, per ADR-003; the composite-key
    shape and every CRUD/refusal decision is a business-layer concern,
    owned by app/business/agent_schedule_registry.py, ADR-037 point 3)."""
    path = _agent_schedules_state_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_agent_schedules_state(state: dict) -> None:
    path = _agent_schedules_state_path()
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _job_run_state_path():
    state_dir = settings.second_brain_data_path
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _JOB_RUN_STATE_FILE


def load_job_run_state() -> dict | None:
    """Pure I/O -- returns None if job_run_state.json doesn't exist
    yet (no default content computed here, per ADR-003; the composite-
    key shape and every start/finish/read decision is a business-layer
    concern, owned by app/business/agent_schedule_registry.py,
    ADR-045 point 4)."""
    path = _job_run_state_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_job_run_state(state: dict) -> None:
    path = _job_run_state_path()
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _pending_approvals_state_path():
    state_dir = settings.second_brain_data_path
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _AGENT_PENDING_APPROVALS_FILE


def load_pending_approvals_state() -> dict | None:
    """Pure I/O — returns None if agent_pending_approvals.json doesn't
    exist yet (ADR-003; the empty-list seed and idempotency guard are
    app/business/pending_approval_registry.py's own concern, ADR-018
    point 2)."""
    path = _pending_approvals_state_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_pending_approvals_state(state: dict) -> None:
    path = _pending_approvals_state_path()
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _cockpit_threads_state_path():
    state_dir = settings.second_brain_data_path
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _COCKPIT_THREADS_FILE


def load_cockpit_threads_state() -> dict | None:
    """Pure I/O -- returns None if cockpit_threads.json doesn't exist yet
    (ADR-003; the empty-dict seed is app/business/cockpit/threads.py's own
    concern, mirroring load_pending_approvals_state's precedent)."""
    path = _cockpit_threads_state_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_cockpit_threads_state(state: dict) -> None:
    path = _cockpit_threads_state_path()
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _cockpit_chat_state_path():
    state_dir = settings.second_brain_data_path
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _COCKPIT_CHAT_FILE


def load_cockpit_chat_state() -> dict | None:
    """Pure I/O -- returns None if cockpit_chat.json doesn't exist yet
    (ADR-003; the empty-dict seed and per-subject-key default are
    app/business/cockpit/chat_store.py's own concern, ADR-007 -- a
    genuinely new store, never the stale cockpit_threads.json above)."""
    path = _cockpit_chat_state_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_cockpit_chat_state(state: dict) -> None:
    path = _cockpit_chat_state_path()
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


_TASKS_SUBFOLDER = f"{_WORK_ROOT}/Tasks"
_TASK_NOTE_INDEX_FILE = "task_note_index.json"


def task_note_filename_stem(subject: str, capture_date: str, entry_id: str) -> str:
    """<subject>-<capture-date>-<entry-id-suffix>. capture_date is the
    date this note was FIRST written -- the caller (T03) passes today's
    date only when creating a note for the first time, never
    recomputed from Outlook's own (mutable) due field on a later run
    (ADR-027 point 3) -- this is the load-bearing reason a due-date
    edit between runs still resolves to the SAME note (Scenario 6),
    unlike Meeting's own recompute-from-start scheme. capture_date is
    expected as a 'YYYY-MM-DD' string, mirroring
    meeting_note_filename_stem's [:10]-sliced start convention applied
    one layer up by the caller instead."""
    return f"{subject}-{capture_date}-{entry_id[-8:]}"


def task_note_path_for_stem(stem: str):
    """Resolves the vault-absolute path for an ALREADY-KNOWN filename
    stem, looked up via task_note_index (lookup_task_note_stem, below)
    -- NOT a recompute-from-current-fields path resolver the way
    meeting_note_path works, since Task's own dedup key is the index
    entry itself, not a deterministic function of current field
    values (ADR-027 point 3). Uses the same _slugify() write_note()
    applies internally, so this always points at exactly the file
    create_task_note_baseline() would have created for that stem."""
    return settings.vault_path / _TASKS_SUBFOLDER / f"{_slugify(stem)}.md"


def task_note_exists_for_stem(stem: str) -> bool:
    return task_note_path_for_stem(stem).exists()


def build_task_tags(customer: str | None) -> list[str]:
    """Mirrors build_meeting_tags's shape for Tasks. Returns
    ["kind/task"] alone when no customer was derived (Scenario 3), or
    ["customer/<slug>", "kind/task"] when one was (Scenario 1)."""
    if not customer:
        return ["kind/task"]
    return [f"customer/{tag_slug(customer)}", "kind/task"]


def create_task_note_baseline(
    subject: str,
    customer: str | None,
    due: str | None,
    status: str,
    entry_id: str,
    capture_date: str,
) -> str:
    """Creates a Task note for the first time. Unlike Meeting's
    create_meeting_note_baseline (which always writes a customer key,
    "" when none), Task's resolved schema requires customer/due to be
    ABSENT from frontmatter entirely when not applicable (Scenario 3;
    "absent otherwise" per the story's own ## Context), not written as
    empty placeholders -- both keys are conditionally included in the
    frontmatter dict below, never written unconditionally. The
    **Customer:**/[[wikilink]] body line is never written here -- it is
    inserted separately by the orchestration layer (T03), the same way
    link_note_to_customer_hub layers on top of ensure_customer_hub_note
    for every other captured note type. Always writes unconditionally,
    mirroring write_note()'s own contract -- callers must consult
    lookup_task_note_stem() first (T03 does) to decide create vs.
    top-up."""
    frontmatter: dict = {
        "type": "Task",
    }
    if customer:
        frontmatter["customer"] = customer
    frontmatter["subject"] = subject
    if due:
        frontmatter["due"] = due
    frontmatter["status"] = status
    frontmatter["tags"] = build_task_tags(customer)
    frontmatter["source"] = "outlook-task"
    frontmatter["outlook_entry_id"] = entry_id
    return write_note(
        subfolder=_TASKS_SUBFOLDER,
        filename_stem=task_note_filename_stem(subject, capture_date, entry_id),
        frontmatter=frontmatter,
        body="",
    )


def ensure_task_note_baseline_frontmatter(
    path,
    subject: str,
    customer: str | None,
    due: str | None,
    status: str,
    entry_id: str,
) -> list[str]:
    """Tops up an already-existing Task note. type/subject/tags/source/
    outlook_entry_id/customer follow the established insert-only-if-
    missing contract (never overwritten once set, matching every other
    captured note type in this codebase) -- customer is only ever
    inserted, never re-derived-and-overwritten on a later run, the same
    accepted behavior Meeting's own ensure_meeting_note_baseline_
    frontmatter already established for its own customer field.
    due/status are the ONE deliberate exception (REQ-SB-09 Scenario
    5/6): upserted via upsert_frontmatter_key, so a status change (Not
    Started -> Completed) or a due-date edit in Outlook is reflected on
    the next capture run, not just filled in the first time a value
    exists. due is only touched when Outlook currently reports one
    (due is not None) -- a due date cleared in Outlook after being set
    is not a case any locked AC covers; the existing value is left
    untouched rather than guessing whether to remove it. Never touches
    the body -- the user's own manually-added content survives
    untouched regardless of which frontmatter keys change. Returns the
    list of keys actually inserted or changed (empty if nothing
    changed) -- Scenario 2/6's baseline-preservation mechanism."""
    changed: list[str] = []
    stable_values = {
        "type": "Task",
        "subject": subject,
        "tags": build_task_tags(customer),
        "source": "outlook-task",
        "outlook_entry_id": entry_id,
    }
    for key, value in stable_values.items():
        if insert_frontmatter_key_if_missing(path, key, value):
            changed.append(key)
    if customer and insert_frontmatter_key_if_missing(path, "customer", customer):
        changed.append("customer")
    if due is not None and upsert_frontmatter_key(path, "due", due):
        changed.append("due")
    if upsert_frontmatter_key(path, "status", status):
        changed.append("status")
    return changed


def _task_note_index_path():
    state_dir = settings.second_brain_data_path
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _TASK_NOTE_INDEX_FILE


def load_task_note_index() -> dict[str, str]:
    path = _task_note_index_path()
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def lookup_task_note_stem(entry_id: str) -> str | None:
    """The dedup/top-up lookup itself (ADR-027 point 3): consulted
    BEFORE any path is computed from current Outlook fields, not a
    recomputed-and-exists()-checked path the way Meeting's
    resolve_meeting_note_path works. Returns the note's own filename
    stem if entry_id has been seen before (regardless of what
    subject/due/status now read as in Outlook), or None if this is
    genuinely a new item never captured before."""
    return load_task_note_index().get(entry_id)


def record_task_note(entry_id: str, stem: str) -> None:
    """Records entry_id -> stem the first (and, by this pipeline's own
    contract, ONLY the first) time a Task note is created for it -- a
    real, load-bearing key->value lookup (unlike processed_meeting_
    ids.json's flat audit-only set), mirroring conversation_index.
    json's own real-lookup shape (find_related_note_stems/
    record_conversation_note), generalized from key -> list[value] to
    key -> value. The caller (T03) only calls this on first creation,
    never on top-up -- a stem is never reassigned once recorded."""
    path = _task_note_index_path()
    index = load_task_note_index()
    index[entry_id] = stem
    path.write_text(json.dumps(index, indent=2), encoding="utf-8")


def _knowledge_gaps_state_path():
    state_dir = settings.second_brain_data_path
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _AGENT_KNOWLEDGE_GAPS_FILE


def load_knowledge_gaps_state() -> dict | None:
    """Pure I/O — returns None if agent_knowledge_gaps.json doesn't
    exist yet (no default content is computed here, per ADR-003; the
    {"gaps": []} default shape is a business-layer decision owned by
    app/business/knowledge_gap_tracking.py, mirroring
    skill_registry.py's own _load_state() pattern)."""
    path = _knowledge_gaps_state_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_knowledge_gaps_state(state: dict) -> None:
    path = _knowledge_gaps_state_path()
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def list_notes_matching_scope(scope: list[str]) -> list:
    """Mirrors list_known_customers()'s/list_notes_in_kind_folder()'s
    exact frontmatter-scan pattern (REQ-SB-29-US-01) -- a note matches
    when its `tags` list intersects `scope` (tag-scoped, e.g.
    "customer/masdar") OR its immediate Work/<kind>/ folder name is
    itself named in `scope` (folder-scoped, e.g. "Pipeline"). Must NOT
    compose vault_indexing.get_index()/vault_search.py (ADR-024/
    ADR-026, REQ-SB-01/REQ-SB-02) -- this story's own Constraints reject
    building against the general indexer or any embeddings/ranking; this
    stays a narrow, independent frontmatter/folder scan, same shape as
    the two precedent functions above. An empty `scope` returns [] --
    never the whole vault, never a silent fallback."""
    if not scope:
        return []
    matches = []
    for path in list_all_note_paths():
        frontmatter, _ = read_note(path)
        tags = frontmatter.get("tags") or []
        kind_folder = path.parent.name
        if any(tag in scope for tag in tags) or kind_folder in scope:
            matches.append(path)
    return sorted(matches)
