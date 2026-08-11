from fastapi import APIRouter

from app.business.customer_hub_linking import retrofit_customer_hub_links
from app.business.email_classification import classify_recent_emails
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
