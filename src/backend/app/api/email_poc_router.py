from fastapi import APIRouter

from app.business.customer_hub_linking import retrofit_customer_hub_links
from app.business.email_classification import classify_recent_emails
from app.business.meeting_classification import classify_recent_meetings
from app.business.partner_hub_linking import migrate_customer_to_partner
from app.business.people_extraction import retrofit_email_sender_links, retrofit_people_from_emails
from app.business.tag_backfill import backfill_tags
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


@router.post("/classify-meetings")
def classify_meetings_endpoint(days_back: int = 7, days_ahead: int = 14, limit: int = 50) -> dict:
    results = classify_recent_meetings(days_back=days_back, days_ahead=days_ahead, limit=limit)
    return {"processed": len(results), "results": results}
