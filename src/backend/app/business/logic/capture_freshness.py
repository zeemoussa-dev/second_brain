"""How long ago each capture actually captured something (`BUG-085`).

Email capture failed for four days while every status on the machine said `ok`:
the Graph refresh token was gone, the script exited 2 on its first page, and the
cron job -- agent-mediated -- recorded a successful run anyway. Nothing on screen
contradicted it, because "0 emails this week" looks exactly like a quiet week.

So the question this answers is not "did the job run" (Hermes already claims
that, and was wrong) but "when did a note last arrive". It is read from the vault
rather than from any job's own report, so a pipeline that lies, a Skill that
cannot authenticate and a Hermes that never fired all produce the same honest
answer: nothing has come in since X.

`BUG-082` was the same shape -- a stale index behind healthy-looking services --
which is why this is a screen, not a log line.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.business.core.vault.vault_manager import VaultManager

_vault_manager = VaultManager()

# Deliberately generous: a quiet weekend is not a failure, and a check that cries
# wolf gets ignored, which is how a real four-day outage goes unnoticed. These
# catch a stall, not a slow day.
CAPTURES = (
    {
        "id": "emails",
        "label": "Email capture",
        "note_type": "RawMessage",
        "timestamp_field": "received",
        "stale_after_hours": 48,
    },
    {
        "id": "meetings",
        "label": "Meeting capture",
        "note_type": "Meeting",
        "timestamp_field": "start",
        "stale_after_hours": 168,  # a week: a diary can legitimately be empty for days
    },
)


def _parsed(stamp: object) -> datetime | None:
    """A frontmatter timestamp as an aware datetime, or None.

    Capture writes `2026-10-09 17:11:47.410000+00:00` (a space, not a `T`) while
    other writers use ISO; both arrive here. A stamp without a timezone is read as
    UTC, which is what every writer in this vault means by one."""
    text = str(stamp or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _latest_captured(note_type: str, field: str, now: datetime) -> datetime | None:
    """The newest timestamp among notes of this kind that is not in the future.

    A meeting is scheduled ahead, so next week's occurrence would otherwise mask a
    capture that stopped last week -- the question is when something last landed,
    not what is on the calendar.

    Reads `get_entries()`, never `get_index()`: the by-name map holds one note per
    name (`BUG-076`), and the newest note is exactly the kind that loses a
    collision to its own invitation email."""
    latest = None
    for entry in _vault_manager.get_entries():
        frontmatter = entry.get("frontmatter") or {}
        if frontmatter.get("type") != note_type:
            continue
        stamp = _parsed(frontmatter.get(field))
        if stamp is None or stamp > now:
            continue
        if latest is None or stamp > latest:
            latest = stamp
    return latest


def get_capture_freshness() -> list[dict]:
    """One row per capture: when it last brought something in, and whether that
    is long enough ago to be a problem.

    `state` is `fresh`, `stale`, or `nothing` for a vault that has never held a
    note of that kind -- which is a fresh install, not a failure."""
    now = datetime.now(timezone.utc)
    rows = []
    for capture in CAPTURES:
        latest = _latest_captured(capture["note_type"], capture["timestamp_field"], now)
        if latest is None:
            rows.append({
                "id": capture["id"], "label": capture["label"], "last_captured_at": None,
                "age_hours": None, "state": "nothing", "stale_after_hours": capture["stale_after_hours"],
            })
            continue
        age_hours = (now - latest).total_seconds() / 3600
        rows.append({
            "id": capture["id"],
            "label": capture["label"],
            "last_captured_at": latest.isoformat(),
            "age_hours": round(age_hours, 1),
            "state": "stale" if age_hours > capture["stale_after_hours"] else "fresh",
            "stale_after_hours": capture["stale_after_hours"],
        })
    return rows
