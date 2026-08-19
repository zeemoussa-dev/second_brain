"""The decoupled Pull step (`ADR-046` Decisions 2-3, `REQ-SB-69-US-01-T02`)
-- the ONE remaining module in the whole email path that imports
`outlook_com` directly. Owns `pull_and_stage_emails`, which fetches real
mail via `outlook_com.list_recent_mail` and durably stages every newly
fetched item via `email_staging.stage_email` -- called from INSIDE
`list_recent_mail`'s own per-item loop (its `on_item_fetched` callback,
`ADR-046` Decision 2), never buffered until the whole COM loop returns.
This is what makes a mid-loop Outlook stall leave every already-fetched
item durably staged: the callback for each item already fired before any
later item's own COM work (sender/attachment/recipient resolution) has a
chance to stall or raise.

`email_capture_pipeline.py`, `email_classification.py`'s other Jobs
(`classify_captured_email`, `summarize_attachment`, `thread_match_merge`,
`route_to_project`, `detect_recurring_pattern`, `consult_librarian`) never
import this module or `outlook_com` -- Pull's own output reaches them
exclusively through the `email_staging` store, never a direct call."""
from __future__ import annotations

from app.data_access import email_staging, outlook_com, vault_writer


def pull_and_stage_emails(limit: int = 10) -> dict:
    """Fetches up to `limit` recent emails from Outlook and durably stages
    every genuinely new one. A light pre-check (already-processed ids from
    `vault_writer.load_processed_email_ids()`, union'd with ids already
    sitting in `email_staging.list_staged_emails()`) skips re-staging a
    duplicate copy of mail a prior Pull run already staged-but-not-yet-
    processed, or mail a prior processing run already finished -- this is
    deliberately only a light PRE-check; `already_processed`/`mark_email_
    processed` themselves are unchanged and still consulted a SECOND time
    later, at processing time (`ADR-043` point 2's already-established
    "consulted a second time" contract, unaffected by this task).

    The skip-check runs inside the `on_item_fetched` callback itself
    (not as a separate post-fetch filter pass) so staging still happens
    per-item, live, exactly as each item is resolved by
    `outlook_com.list_recent_mail`'s own loop -- a mid-loop stall on a
    LATER item never undoes the staging already durably written for every
    EARLIER item this call has already seen.

    Returns an honest summary dict: `fetched` is every item
    `list_recent_mail` handed to the callback this call (regardless of
    whether it was newly staged or skipped); `newly_staged` is how many of
    those were genuinely new and staged; `already_staged_or_processed` is
    how many were skipped by the pre-check."""
    skip_ids = vault_writer.load_processed_email_ids() | {
        staged_email["id"] for staged_email in email_staging.list_staged_emails()
    }

    summary = {"fetched": 0, "newly_staged": 0, "already_staged_or_processed": 0}

    def _stage_if_genuinely_new(fetched_email: dict) -> None:
        summary["fetched"] += 1
        if fetched_email["id"] in skip_ids:
            summary["already_staged_or_processed"] += 1
            return
        email_staging.stage_email(fetched_email)
        skip_ids.add(fetched_email["id"])
        summary["newly_staged"] += 1

    outlook_com.list_recent_mail(limit=limit, on_item_fetched=_stage_if_genuinely_new)

    return summary
