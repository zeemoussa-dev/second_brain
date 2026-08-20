"""One-off migration (REQ-SB-59, see ADR-047 in Implementation/Architecture/
ADR.md) -- the fifth instance of this codebase's existing one-off-migration-
module shape (tag_backfill.py, vault_restructure.py,
partner_hub_linking.migrate_customer_to_partner): wipes the legacy per-email
Work/Emails/ notes and their now-stale .second-brain/ cross-link stores,
re-runs capture over Outlook history through the already-Done Thread/
Meeting pipelines, and regenerates every legacy flat Customer hub note onto
the new OKF Background/History/Glimpse/Captures shape (ADR-042), preserving
durable pre-migration content through the existing Pending-Approval gate
rather than discarding or silently auto-writing it.

Archive, never delete: every note this migration removes from Work/ moves
into .second-brain/migration_backup/<UTC-run-timestamp>/ via the existing,
unmodified vault_writer.move_note_and_attachments primitive -- this
project's first soft-delete location (ADR-047 Decision 2). Each public
function below generates its own independent run_timestamp; there is no
shared "migration run" object across the three -- they are independently
operator-triggered, one-time, non-scheduled functions (ADR-047 Decision 7 --
no new "already ran" state marker, no dry-run flag; idempotency comes
entirely from "nothing left to act on" on a rerun).
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.business import customer_hub_linking, meeting_classification, project_customer_synthesizer
from app.business.pipelines import email_capture_pipeline, email_pull
from app.config import settings
from app.data_access import vault_writer

_STATE_DIR = ".second-brain"
_MIGRATION_BACKUP_DIR = "migration_backup"
_PROCESSED_EMAILS_FILE = "processed_email_ids.json"
_CONVERSATIONS_FILE = "conversation_index.json"
_EMAILS_KIND_FOLDER = "Emails"
_CUSTOMERS_KIND_FOLDER = "Customers"
_MEETING_DAYS_AHEAD = 14
# A generous technical safety cap on top of the real, operator-supplied
# `meeting_days_back` date gate below -- classify_recent_meetings' own
# `limit` parameter caps item COUNT, not date range, so this is not the
# "config, not constants" business value ADR-047 Decision 4 requires be
# operator-supplied (that's meeting_days_back itself); it only needs to be
# comfortably above any real, already-date-restricted calendar window's
# item count.
_MEETING_ITEM_LIMIT_CAP = 2000


def _new_run_timestamp() -> str:
    """One fresh UTC timestamp per call (this task's own Context) -- reused
    for every move inside that same call, so a single invocation's own
    archived notes/state files land under one shared <run-timestamp>/
    directory. A later, independent call generates its own timestamp."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def wipe_legacy_email_notes() -> dict:
    """T01 (ADR-047 Decision 2-3): archives (never deletes) every note
    currently under Work/Emails/ -- plus any sibling attachments/<slug>/
    folder, via the existing move_note_and_attachments primitive -- into
    .second-brain/migration_backup/<run-timestamp>/Emails/, then archives
    the two now-stale .second-brain/ JSON stores (processed_email_ids.json,
    conversation_index.json) into the same run root via a plain
    Path.rename. Archiving processed_email_ids.json is load-bearing, not
    merely tidy -- it is what resets recapture_outlook_history's own email
    dedup gate (ADR-047 Context point 1). Never touches Work/Meetings/
    (ADR-047 Context point 2 -- Scenario 5 is satisfied entirely by
    recapture_outlook_history's own wide-window meeting re-run). Naturally
    idempotent: a rerun finds zero notes under Work/Emails/ and both JSON
    stores already gone from their canonical paths, so it reports zero
    moves with no error."""
    run_timestamp = _new_run_timestamp()
    backup_root = settings.vault_path / _STATE_DIR / _MIGRATION_BACKUP_DIR / run_timestamp
    emails_root = settings.vault_path / "Work" / _EMAILS_KIND_FOLDER
    emails_backup_dir = backup_root / _EMAILS_KIND_FOLDER

    emails_moved: list[dict] = []
    if emails_root.exists():
        for note_path in sorted(emails_root.glob("*.md")):
            try:
                archived_to = vault_writer.move_note_and_attachments(note_path, emails_backup_dir)
                emails_moved.append({
                    "note": str(note_path),
                    "archived_to": archived_to,
                    "status": "archived",
                })
            except FileExistsError as exc:
                emails_moved.append({
                    "note": str(note_path),
                    "status": "collision",
                    "error": str(exc),
                })
        vault_writer.remove_empty_dirs(emails_root)

    state_dir = settings.vault_path / _STATE_DIR
    state_files_archived: list[dict] = []
    for filename in (_PROCESSED_EMAILS_FILE, _CONVERSATIONS_FILE):
        source_path = state_dir / filename
        if not source_path.exists():
            state_files_archived.append({"file": filename, "status": "not_found"})
            continue
        backup_root.mkdir(parents=True, exist_ok=True)
        target_path = backup_root / filename
        source_path.rename(target_path)
        state_files_archived.append({
            "file": filename,
            "archived_to": str(target_path),
            "status": "archived",
        })

    return {
        "run_timestamp": run_timestamp,
        "emails_moved": emails_moved,
        "state_files_archived": state_files_archived,
    }


def recapture_outlook_history(email_limit: int, meeting_days_back: int) -> dict:
    """T02 (ADR-047 Decision 4): re-runs the already-Done Email/Meeting
    capture pipelines, once each, over an operator-supplied full-history
    window -- no new Outlook-COM primitive, every underlying call is the
    same existing, unmodified, read-only-of-Outlook function the live
    hourly capture already uses. `email_limit`/`meeting_days_back` are
    required, never defaulted or hardcoded (this project's standing
    "config, not constants" convention) -- the caller must know or
    generously estimate their own real mailbox/calendar history size.

    Composes, each exactly once, in this order:
    1. `email_pull.pull_and_stage_emails(limit=email_limit)` -- an
       `email_limit` at/above the real Inbox item count fetches full
       history in this one call (`list_recent_mail` iterates until either
       `limit` is hit or the collection is exhausted).
    2. `email_capture_pipeline.run_email_capture_pipeline()` -- its own
       current body already drains every currently-staged, not-yet-
       processed email in one call.
    3. `meeting_classification.classify_recent_meetings(days_back=
       meeting_days_back, days_ahead=_MEETING_DAYS_AHEAD, limit=
       _MEETING_ITEM_LIMIT_CAP)` -- reaches genuinely full calendar
       history via `list_calendar_events`'s own real COM date `Restrict()`
       on `days_back`. This same call satisfies Scenario 5 on its own:
       `mark_meeting_processed` is a non-gating, top-up-only audit trail,
       so every pre-migration Meeting note is topped up in place, and
       `REQ-SB-56`'s `Link-to-Thread` Job (already unconditional inside
       this same call) re-links each one to its now-recaptured Thread,
       with zero code change here.

    Precondition: T01's `wipe_legacy_email_notes()` must already have run
    against this same vault -- without it, `processed_email_ids.json`
    still marks every real historical email as already-processed by its
    own stable Outlook EntryID, and step 1/2 above would silently process
    zero real emails (ADR-047 Context point 1). This function does not
    itself re-check or enforce that precondition; the operator sequences
    T01 before T02, per this story's own `depends_on` edge."""
    pull_result = email_pull.pull_and_stage_emails(limit=email_limit)
    capture_results = email_capture_pipeline.run_email_capture_pipeline()
    meeting_results = meeting_classification.classify_recent_meetings(
        days_back=meeting_days_back,
        days_ahead=_MEETING_DAYS_AHEAD,
        limit=_MEETING_ITEM_LIMIT_CAP,
    )
    return {
        "emails_staged": pull_result,
        "emails_processed": capture_results,
        "meetings_processed": meeting_results,
    }


def regenerate_customer_notes() -> dict:
    """T03 (ADR-047 Decision 5) -- also resolves ESC-046 as a direct,
    in-scope consequence, not a separately deferred bugfix. A generic,
    vault-wide scan (never a hardcoded Customer name list, mirroring
    partner_hub_linking.migrate_customer_to_partner's own established
    precedent): enumerates every note vault_writer.list_all_note_paths()
    returns whose frontmatter type == "Customer" AND whose parent
    directory name == "Customers" (the old flat shape -- an OKF concept
    file's own parent directory is instead the Customer's slug, never
    literally "Customers").

    For each: ensure_customer_hub_note guarantees the OKF directory exists
    (a no-op for an already-migrated Customer), then the flat note's own
    full pre-migration body is fed as evidence_text into the SAME,
    unmodified synthesize_customer the ongoing REQ-SB-57 Synthesizer
    already uses going forward -- never a migration-only auto-write
    bypass. Any durable fact synthesize_customer's own internal
    detect_customer_durable_fact call finds is routed through its existing
    propose_background_amendment Pending-Approval gate; `## Background`
    itself is never written here. Finally archives the flat file via
    move_note_and_attachments into
    .second-brain/migration_backup/<run-timestamp>/Customers/ -- once the
    flat file no longer exists anywhere under Work/, only the OKF concept
    file remains at that filename stem, resolving ESC-046's collision for
    that Customer.

    Naturally idempotent: a rerun's own scan finds zero remaining flat
    Customer notes (every previously-processed one is now archived), so it
    reports an empty customers_processed list with no error and proposes
    no duplicate Pending Approval."""
    run_timestamp = _new_run_timestamp()
    backup_root = settings.vault_path / _STATE_DIR / _MIGRATION_BACKUP_DIR / run_timestamp
    customers_backup_dir = backup_root / _CUSTOMERS_KIND_FOLDER

    customers_processed: list[dict] = []
    for note_path in vault_writer.list_all_note_paths():
        if note_path.parent.name != _CUSTOMERS_KIND_FOLDER:
            continue
        frontmatter, body = vault_writer.read_note(note_path)
        if frontmatter.get("type") != "Customer":
            continue

        customer_name = frontmatter.get("customer") or note_path.stem
        hub_result = customer_hub_linking.ensure_customer_hub_note(customer_name)
        synthesis_result = project_customer_synthesizer.synthesize_customer(
            customer_name, evidence_text=body,
        )
        archived_to = vault_writer.move_note_and_attachments(note_path, customers_backup_dir)

        customers_processed.append({
            "customer": customer_name,
            "flat_note": str(note_path),
            "hub_note_path": hub_result["hub_note_path"],
            "hub_created": hub_result["created"],
            "amendment_proposed": synthesis_result["amendment_proposed"],
            "archived_to": archived_to,
            "status": "regenerated",
        })

    return {
        "run_timestamp": run_timestamp,
        "customers_processed": customers_processed,
    }
