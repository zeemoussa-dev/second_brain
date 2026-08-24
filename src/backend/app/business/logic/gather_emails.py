"""Business Logic (2026-08-20 architecture pass) -- the first real Action
in the new Tools registry (data_access/system/tools/registry.json,
Outlook Tool -> Email Category). Purpose-named, not nested under an
outlook/ folder (operator correction, 2026-08-20: "outlook is not a
business Object... The Business Logic will be the Get outlook emails").

Thin wrapper over pipelines/email_pull.py's own real, unmodified
pull_and_stage_emails -- no reimplementation, no new logic. Bounded by
`limit`, per the Bulk data principle (Implementation/Plans/2026-08-20-
backend-architecture-redesign.md): this Action never loops unboundedly:
routine capture calls it with a small limit on a schedule; a bulk/retrofit
pull is the SAME Action called repeatedly by whatever orchestrates that
(a Hermes cron job, page by page), never a second, unbounded code path.
"""
from __future__ import annotations

from app.business.pipelines import email_pull


def gather_emails(limit: int = 10) -> dict:
    """Fetches up to `limit` recent emails from Outlook and durably stages
    every genuinely new one. Returns {"fetched", "newly_staged",
    "already_staged_or_processed"} -- see pull_and_stage_emails's own
    docstring for the full contract; this wrapper adds nothing beyond the
    Action-shaped entry point the Tools registry needs."""
    return email_pull.pull_and_stage_emails(limit=limit)
