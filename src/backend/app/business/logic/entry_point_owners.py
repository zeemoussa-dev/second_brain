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

# How the app came to believe a person decided something. Carried in
# every attribution block, because the two are NOT the same evidence
# and a record that read identically for both would be the fabricated
# certainty `REQ-SB-103` exists against:
#
#   in_person -- they were signed in and clicked it here. The app
#                watched them do it.
#   relayed   -- an agent says the owner of this door said it. The app
#                watched an AGENT say so, which is a weaker claim, and
#                the record names the agent that made it so the
#                transcript can be read back.
DECIDED_IN_PERSON = "in_person"
DECIDED_BY_RELAY = "relayed"


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


def owner_of_the_sender(source: Any, chat_id: Any, sender_id: Any = None) -> dict | None:
    """Whose words these are, when an agent relays them.

    **The sender is looked up before the chat, and that is the whole
    point of this function** (operator, 2026-10-21: the link is per
    SENDER). In a direct message the chat IS the person, so the two
    answers agree and the distinction costs nothing. In a group they do
    not: the chat belongs to whoever the operator declared for the
    group, and attributing a group member's "yes" to that person would
    put one person's name on another's decision -- which is the exact
    failure the whole attribution rule exists to prevent.

    So a declaration for the sender wins where one exists, and the
    chat's owner is the fallback for the direct-message case the
    operator described. Where neither is declared the answer is `None`
    and the caller must refuse: an unowned door cannot produce an
    attributable approval.
    """
    if sender_id:
        spoke_for_themselves = owner_of(source, sender_id)
        if spoke_for_themselves is not None:
            return spoke_for_themselves
    return owner_of(source, chat_id)


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


class NobodyOwnsThatDoorError(Exception):
    """An agent relayed an answer through a door no person is declared
    for. Carries the sentence the agent relays onward; the router turns
    it into a status without rewording it."""


def relayed_attribution(
    agent_id: str, source: Any, chat_id: Any, sender_id: Any = None,
) -> dict:
    """The attribution block for an answer an agent relays.

    Three facts, all of them true, and none of them collapsed into the
    others: WHO is the person the operator declared for this door, HOW
    is `relayed` rather than `in_person`, and WHICH AGENT said so.

    **The agent names the door, never the person.** That asymmetry is
    the design: a worker that could put a name in the field could put
    any name in the field, and an approval is worth exactly as much as
    the hardest thing to forge about it. The app resolves the person
    from its own declarations, so relabelling who may approve what is
    an Admin editing entry points, not an agent choosing.

    Refuses rather than guessing when the door is unowned. An
    unattributable approval reads as authority it never had, which is
    worse than no approval at all -- and the question is still there,
    on everybody's "Waiting on You", for a person to answer in the app.
    """
    owner = owner_of_the_sender(source, chat_id, sender_id)
    if owner is None:
        raise NobodyOwnsThatDoorError(
            f"agent {agent_id!r} relayed an answer from {source!r}/"
            f"{sender_id or chat_id!r}, and this install has nobody declared as the owner of "
            "that door -- so there is no person to record this decision as, and nothing was "
            "recorded. An Admin can say whose door it is on the Entry points screen; until "
            "then the question is still waiting and can be answered in the app by anyone."
        )
    return {
        **owner,
        "how": DECIDED_BY_RELAY,
        "relayed_by_agent": agent_id,
        "sender_id": str(sender_id) if sender_id else None,
    }
