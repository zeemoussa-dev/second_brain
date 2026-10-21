"""Which person an outside door belongs to (`REQ-SB-103`; operator
2026-10-21: "Yes an entry point belongs to a person").

A human step asks somebody. Over WhatsApp the agent is the one in the
conversation, so the app has to know whose conversation it is before it
can say who a run is waiting on -- and "what is waiting on me" cannot
exist until it can.

**The link lives on the declared entry point, not on the run.** A
declaration already says which agent answers a door (`REQ-SB-102`);
whose door it is belongs in the same place, for the same reason: it is
the operator's statement of intent about an entry point, and a second
map of numbers to people would be a second truth nobody checks.

**A reference on the declaration, a snapshot on the run.** The
declaration holds `owner_user_id` and is re-read every time, so renaming
a person fixes every door at once. The run stores what that resolved to
at the moment it started, because a run that re-read its owner would
quietly change who it had been waiting on all along.

**An unowned door is a real answer, not a failure.** Most doors have no
owner declared yet, and a run that came in through one is waiting on
"whoever is watching" rather than on a named person. That reads as
`None` here and is never back-filled with the operator: this install had
exactly one person for its whole life before sign-in existed, and
stamping their name on an unmapped door would turn "we do not know who
this is" into "it is them".
"""
from __future__ import annotations

from typing import Any

from app.business.core.users.user_manager import UserManager
from app.data_access import entry_points as entry_points_data

OWNER_FIELD = "owner_user_id"


def _key(source: Any, chat_id: Any) -> tuple[str, str]:
    """The same `(source, chat_id)` pair `entry_points.observe` joins
    on. One chat id means nothing without the platform it belongs to."""
    return (str(source or ""), str(chat_id or ""))


def declared_owner_id(source: Any, chat_id: Any) -> str | None:
    wanted = _key(source, chat_id)
    for entry in entry_points_data.read_entry_points():
        if _key(entry.get("source"), entry.get("chat_id")) == wanted:
            owner = str(entry.get(OWNER_FIELD) or "").strip()
            return owner or None
    return None


def owner_of(source: Any, chat_id: Any) -> dict | None:
    """The person this door belongs to, as the snapshot block a record
    carries -- the same shape the Action-call ledger's attribution uses,
    so one reader can display either.

    `None` covers three different situations on purpose: no declaration
    for this door, a declaration naming nobody, and a declaration naming
    a user this install no longer has. All three mean the same thing to
    everything downstream -- nobody can be named -- and distinguishing
    them here would invite a caller to guess at the other two.
    """
    owner_id = declared_owner_id(source, chat_id)
    if not owner_id:
        return None
    user = UserManager().get_by_id(owner_id)
    if user is None:
        return None
    return {
        "user_id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "role": user.role.value,
        "source": str(source or ""),
        "chat_id": str(chat_id or ""),
    }
