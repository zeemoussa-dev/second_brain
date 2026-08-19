from fastapi import APIRouter

from app.business.customer_hub_linking import retrofit_customer_hub_links
from app.business.email_classification import classify_recent_emails, synthesize_thread
from app.business.meeting_classification import classify_recent_meetings
from app.business.partner_hub_linking import migrate_customer_to_partner
from app.business.people_extraction import retrofit_email_sender_links, retrofit_people_from_emails
from app.business.pipelines.librarian_housekeeping import (
    backfill_company_folders,
    backfill_files,
    link_thread_messages,
    populate_thread_related_links,
    propose_company_review,
    propose_customer_archival_candidates,
    propose_customer_backfill,
    rename_threads,
    run_housekeeping_pass,
)
from app.business.pipelines.raw_message_capture import capture_raw_thread_messages
from app.business.tag_backfill import backfill_tags
from app.business.thread_summary_backfill import backfill_thread_summaries
from app.business.vault_migration import (
    recapture_outlook_history,
    regenerate_customer_notes,
    wipe_legacy_email_notes,
)
from app.business.vault_provisioning import provision_vault_base
from app.business.vault_restructure import flatten_customer_folders

router = APIRouter(prefix="/poc")


@router.post("/classify-emails")
def classify_emails(limit: int = 10) -> dict:
    results = classify_recent_emails(limit=limit)
    return {"processed": len(results), "results": results}


@router.post("/backfill-tags")
def backfill_tags_endpoint() -> dict:
    results = backfill_tags()
    tagged = sum(1 for r in results if r["status"] == "tagged")
    return {"notes_checked": len(results), "tagged": tagged, "results": results}


@router.post("/flatten-customer-folders")
def flatten_customer_folders_endpoint() -> dict:
    results = flatten_customer_folders()
    moved = sum(1 for r in results if r["status"] == "moved")
    return {"notes_checked": len(results), "moved": moved, "results": results}


@router.post("/retrofit-customer-hub-links")
def retrofit_customer_hub_links_endpoint() -> dict:
    results = retrofit_customer_hub_links()
    linked = sum(1 for r in results if r["status"] == "linked")
    hub_notes_created = sum(1 for r in results if r.get("hub_created"))
    return {
        "notes_checked": len(results),
        "linked": linked,
        "hub_notes_created": hub_notes_created,
        "results": results,
    }


@router.post("/retrofit-people-from-emails")
def retrofit_people_from_emails_endpoint() -> dict:
    results = retrofit_people_from_emails()
    created = sum(1 for r in results if r["status"] == "created")
    linked = sum(1 for r in results if r.get("linked"))
    return {
        "notes_checked": len(results),
        "created": created,
        "linked": linked,
        "results": results,
    }


@router.post("/retrofit-email-sender-links")
def retrofit_email_sender_links_endpoint() -> dict:
    results = retrofit_email_sender_links()
    linked = sum(1 for r in results if r["status"] == "linked")
    return {
        "notes_checked": len(results),
        "linked": linked,
        "results": results,
    }


@router.post("/migrate-customer-to-partner")
def migrate_customer_to_partner_endpoint(customer_name: str) -> dict:
    result = migrate_customer_to_partner(customer_name)
    retagged = sum(1 for r in result["notes_retagged"] if r["status"] == "retagged")
    return {
        "hub_note_moved": result["hub_note_moved"],
        "hub_note_path": result["hub_note_path"],
        "notes_checked": len(result["notes_retagged"]),
        "notes_retagged": retagged,
        "results": result["notes_retagged"],
    }


@router.post("/backfill-thread-summaries")
def backfill_thread_summaries_endpoint() -> dict:
    results = backfill_thread_summaries()
    regenerated = sum(1 for r in results if r["status"] == "regenerated")
    return {"notes_checked": len(results), "regenerated": regenerated, "results": results}


@router.post("/classify-meetings")
def classify_meetings_endpoint(days_back: int = 7, days_ahead: int = 14, limit: int = 50) -> dict:
    results = classify_recent_meetings(days_back=days_back, days_ahead=days_ahead, limit=limit)
    return {"processed": len(results), "results": results}


@router.post("/wipe-legacy-email-notes")
def wipe_legacy_email_notes_endpoint() -> dict:
    result = wipe_legacy_email_notes()
    archived = sum(1 for r in result["emails_moved"] if r["status"] == "archived")
    return {
        "run_timestamp": result["run_timestamp"],
        "emails_checked": len(result["emails_moved"]),
        "emails_archived": archived,
        "state_files_archived": result["state_files_archived"],
        "results": result["emails_moved"],
    }


@router.post("/recapture-outlook-history")
def recapture_outlook_history_endpoint(email_limit: int, meeting_days_back: int) -> dict:
    result = recapture_outlook_history(email_limit=email_limit, meeting_days_back=meeting_days_back)
    return {
        "emails_staged": result["emails_staged"],
        "emails_processed_count": len(result["emails_processed"]),
        "meetings_processed_count": len(result["meetings_processed"]),
        "emails_processed": result["emails_processed"],
        "meetings_processed": result["meetings_processed"],
    }


@router.post("/regenerate-customer-notes")
def regenerate_customer_notes_endpoint() -> dict:
    result = regenerate_customer_notes()
    regenerated = sum(1 for r in result["customers_processed"] if r["status"] == "regenerated")
    amendments_proposed = sum(1 for r in result["customers_processed"] if r["amendment_proposed"])
    return {
        "run_timestamp": result["run_timestamp"],
        "customers_checked": len(result["customers_processed"]),
        "customers_regenerated": regenerated,
        "amendments_proposed": amendments_proposed,
        "results": result["customers_processed"],
    }


@router.post("/provision-vault-base")
def provision_vault_base_endpoint() -> dict:
    return provision_vault_base()


@router.post("/capture-raw-thread-messages")
def capture_raw_thread_messages_endpoint(limit: int = 10) -> dict:
    return capture_raw_thread_messages(limit=limit)


@router.post("/synthesize-thread")
def synthesize_thread_endpoint(conversation_id: str) -> dict:
    return synthesize_thread(conversation_id=conversation_id)


@router.post("/librarian-rename-threads")
def librarian_rename_threads_endpoint() -> dict:
    return rename_threads()


@router.post("/librarian-link-thread-messages")
def librarian_link_thread_messages_endpoint() -> dict:
    return link_thread_messages()


@router.post("/librarian-backfill-files")
def librarian_backfill_files_endpoint() -> dict:
    return backfill_files()


@router.post("/librarian-populate-related")
def librarian_populate_related_endpoint() -> dict:
    return populate_thread_related_links()


@router.post("/librarian-backfill-company-folders")
def librarian_backfill_company_folders_endpoint() -> dict:
    return backfill_company_folders()


@router.post("/librarian-run-housekeeping-pass")
def librarian_run_housekeeping_pass_endpoint() -> dict:
    return run_housekeeping_pass()


@router.post("/librarian-propose-customer-backfill")
def librarian_propose_customer_backfill_endpoint() -> dict:
    """REQ-SB-74-US-01-T05, ADR-055 Decision 5 -- runs propose_customer_
    backfill() then propose_customer_archival_candidates() in ONE
    orchestrating call, passing the first Job's own real result directly
    into the second (one evidence pass, never two independently-run
    Compass sweeps that could disagree). Deliberately NOT added to run_
    housekeeping_pass()'s own scheduled chain -- manually-triggered only,
    per the story's own explicit Constraint."""
    backfill_result = propose_customer_backfill()
    archival_result = propose_customer_archival_candidates(
        backfill_result["matched_existing_customer_names"]
    )
    return {
        "propose_customer_backfill": backfill_result,
        "propose_customer_archival_candidates": archival_result,
    }


@router.post("/librarian-propose-company-review")
def librarian_propose_company_review_endpoint() -> dict:
    """REQ-SB-76-US-01-T04, ADR-057 Decision 10 -- runs propose_company_
    review(). Deliberately NOT added to run_housekeeping_pass()'s own
    scheduled chain -- manually-triggered only, mirroring ADR-055's own
    explicit precedent for propose_customer_backfill above."""
    return propose_company_review()
