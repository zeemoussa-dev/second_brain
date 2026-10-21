"""Entry points: the outside doors into this install, and which agent
answers each one (`REQ-SB-102`; operator 2026-10-21: "Entry Point is
bounded to an Agent maybe we can do the link somewhere in the app").

**Hermes does not expose this, so it is OBSERVED and optionally
DECLARED.** `/api/messaging/platforms` turned out to be the catalogue of
platform *types* -- forty-odd of them, none reporting `configured` on
this install even though WhatsApp demonstrably works -- so there is no
configuration to read. What there is, is traffic: every session carries
`source` (`whatsapp`, `cli`, `second-brain`, `cron`), a `profile` that
answered it, and an `origin_json` naming the chat and the person
(`chat_id`, `chat_name`, `user_name`).

So an entry point is derived from what actually happened, and the
operator's declaration sits beside it rather than instead of it. That
ordering is the point: a hand-written map of numbers to agents is a
second truth that nobody checks, and the day Hermes is rewired it
becomes a confident lie. Here the declaration is always shown against
the observation, and a disagreement is reported as `drifted` rather than
silently resolved in favour of either.

**An entry point that has never been used is still real**, and an
observation with no declaration is still real. Both appear, labelled for
what they are: `declared_only` has never been seen in traffic (new, or
wrong, or simply quiet), `observed_only` is a door nobody wrote down.
Neither is an error and neither is hidden.

**`chat_id` is not a phone number.** WhatsApp gives a LID
(`151471081435270@lid`); the operator will recognise `chat_name` long
before they recognise that. So the identifier is kept as the join key
and the human name is carried alongside for reading.
"""
from __future__ import annotations

import json
from typing import Any

# Sources that are this app or the machine talking to itself rather than
# an outside door. Excluded from the observed set by default: a scheduled
# job is not an entry point in the sense the operator means, and 3540 of
# them would bury the one WhatsApp chat that is.
INTERNAL_SOURCES = frozenset({"cron", "cli", "second-brain"})


def _origin_of(session: dict) -> dict:
    """`origin_json` arrives as a dict on some rows and a JSON string on
    others. Unparseable is reported as empty rather than raised: one
    malformed row must not cost the operator the whole view."""
    raw = session.get("origin_json")
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except (ValueError, TypeError):
            return {}
    return {}


def observe(sessions: list[dict], include_internal: bool = False) -> list[dict]:
    """Which doors have actually been used, and which agent answered.

    Keyed on `(source, chat_id)` -- the pair, not either alone. One
    WhatsApp account can hold many chats and one chat id means nothing
    without knowing the platform it belongs to.

    `answered_by` is a LIST, deliberately. If two profiles have answered
    the same chat, that is a fact worth seeing rather than a conflict to
    resolve by picking the most recent -- it usually means the routing
    changed, which is exactly what the operator is trying to see.
    """
    doors: dict[tuple[str, str], dict] = {}
    for session in sessions:
        source = session.get("source") or "unknown"
        if not include_internal and source in INTERNAL_SOURCES:
            continue
        origin = _origin_of(session)
        chat_id = session.get("chat_id") or origin.get("chat_id") or ""
        key = (source, str(chat_id))
        door = doors.setdefault(key, {
            "source": source,
            "chat_id": str(chat_id),
            "chat_name": origin.get("chat_name") or origin.get("user_name"),
            "chat_type": session.get("chat_type") or origin.get("chat_type"),
            "answered_by": [],
            "session_count": 0,
            "last_seen": None,
            "last_session_id": None,
        })
        door["session_count"] += 1
        profile = session.get("profile") or session.get("profile_name")
        if profile and profile not in door["answered_by"]:
            door["answered_by"].append(profile)
        # Sessions arrive newest-first, so the first one wins the
        # "last seen" slot without needing a date comparison.
        if door["last_session_id"] is None:
            door["last_session_id"] = session.get("id")
            door["last_seen"] = session.get("created_at") or session.get("updated_at")
        if not door["chat_name"]:
            door["chat_name"] = origin.get("chat_name") or origin.get("user_name")
    return sorted(doors.values(), key=lambda d: (-d["session_count"], d["source"]))


def reconcile(declared: list[dict], observed: list[dict]) -> list[dict]:
    """The operator's declaration and the traffic, side by side.

    `status` is the whole output of this function:
      `agrees`        -- declared agent is the one that answers
      `drifted`       -- declared one agent, a different one answered
      `declared_only` -- written down, never seen in traffic
      `observed_only` -- a door nobody wrote down

    Nothing is corrected. The app does not know which side is right --
    the declaration might be the intent and the traffic the bug, or the
    other way round -- and quietly preferring either would destroy the
    one signal the operator came here for.
    """
    by_key = {(str(d.get("source")), str(d.get("chat_id"))): d for d in observed}
    rows: list[dict] = []
    claimed: set[tuple[str, str]] = set()

    for entry in declared:
        key = (str(entry.get("source")), str(entry.get("chat_id")))
        claimed.add(key)
        seen = by_key.get(key)
        expected = entry.get("agent_id")
        if seen is None:
            status = "declared_only"
        elif expected and expected in seen["answered_by"]:
            status = "agrees" if len(seen["answered_by"]) == 1 else "drifted"
        else:
            status = "drifted"
        rows.append({
            **entry,
            "status": status,
            "observed": seen,
            "answered_by": (seen or {}).get("answered_by", []),
        })

    for key, seen in by_key.items():
        if key not in claimed:
            rows.append({
                "label": seen.get("chat_name") or seen["chat_id"],
                "source": seen["source"],
                "chat_id": seen["chat_id"],
                "agent_id": None,
                "status": "observed_only",
                "observed": seen,
                "answered_by": seen["answered_by"],
            })

    order = {"drifted": 0, "observed_only": 1, "declared_only": 2, "agrees": 3}
    return sorted(rows, key=lambda r: (order.get(r["status"], 9), r.get("source", "")))


def summarise(rows: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return {
        "by_status": counts,
        # The two the operator should look at, named rather than left to
        # be counted off a list.
        "needs_attention": [
            r for r in rows if r["status"] in ("drifted", "observed_only")
        ],
    }


def build(rest: Any, declared: list[dict], scan: int = 400) -> dict:
    """Reads a window of recent sessions and reconciles it.

    The internal sources are excluded BY HERMES, not here. That is the
    difference between working and not: this install holds 3546 sessions
    of which 3540 are cron, so a client-side filter over the newest few
    hundred rows returns nothing at all -- measured, and the reason this
    function was rewritten. `scanned` reports what came back so a quiet
    door can be told from one that fell off the end of the window.
    """
    sessions: list[dict] = []
    page_size = 100
    excluded = ",".join(sorted(INTERNAL_SOURCES))
    for offset in range(0, max(scan, page_size), page_size):
        payload = rest.list_sessions_excluding(excluded, limit=page_size, offset=offset)
        page = payload.get("sessions") or []
        if not page:
            break
        sessions.extend(page)
    observed = observe(sessions)
    rows = reconcile(declared, observed)
    return {
        "entry_points": rows,
        "summary": summarise(rows),
        "scanned": {
            "sessions_read": len(sessions),
            "window": scan,
            "internal_sources_excluded": sorted(INTERNAL_SOURCES),
        },
    }
