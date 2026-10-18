"""The Operator Profile's HTTP surface (`REQ-SB-95-US-01-T03`) -- flat
and single-purpose, the same one-router-per-entity convention
index_router.py / actions_router.py / workflows_router.py already use.

**Two routes, and there is deliberately no third** (`ADR-032`: the
Profile is configuration, not a catalogue). Read the one record, replace
the one record. No `POST` create, no `DELETE`, and no id segment in any
path -- a singleton has nothing to list and nothing to tell apart, and a
collection-shaped API is exactly how that decision would quietly erode.
The route table is asserted over in `tests/test_operator_profile_api.py`
rather than left to reviewer vigilance.

This router composes; it does not decide. What the Profile owns, what a
team entry may hold and what "configured" means are all
`OperatorProfileManager`'s own rules (`ADR-003`), so the only things
that happen here are turning a payload into the Manager's call and
refusing one that cannot be stored honestly.

**Two refusals, and they are deliberately different shapes:**

- *An unowned key, including an attempt to set the operator's own
  address, is REFUSED -- it is never accepted-and-dropped.* `save()`
  drops unowned keys so the FILE's guarantee cannot depend on any
  caller's good behaviour, but a route has a second obligation the
  Manager does not: a `200` is a client's only evidence that what it
  sent was stored. Answering `200` to "set my own address to X" would
  be true about the Profile and false about what the operator asked
  for, and the Profile page would then show the old value with no
  explanation. The own address is `SELF_EMAIL` (`ADR-038`), so the
  refusal names that setting and the surface that edits it rather than
  saying only "no".
- *A malformed team entry is refused by the request model itself*
  (`extra="forbid"`), so a missing `email` and a smuggled `name`/
  `title` both come back as FastAPI's own `422` naming the offending
  field by position -- `team.1.email`. That is the one thing the
  operator can act on, and it is also what keeps `ADR-032`'s
  membership-not-copies from being silently coerced into a dropped
  field. Nothing reaches the Manager, so nothing is partially saved.

`409` for the own-address refusal, not `422`: it carries a sentence, and
FastAPI owns `422` for its own validation errors whose `detail` is a
LIST of error objects -- a hand-written refusal sent under the same code
would force the Profile page to tell two `detail` shapes apart before it
could show anything. `409` is what sections_router.py,
blueprints_router.py, actions_router.py and workflows_router.py already
return when a write is refused.

Nothing here publishes anything into agent context. The save-side
trigger belongs to the Manager (`REQ-SB-95-US-01-T02`), so this router
gets it for free and must not fire it a second time.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from app.business.core.operator.operator_profile import (
    OWN_ADDRESS_EDITED_AT,
    OWN_ADDRESS_SETTING_KEY,
    OperatorProfile,
)
from app.business.core.operator.operator_profile_manager import OperatorProfileManager

router = APIRouter(prefix="/operator")
_operator_profile_manager = OperatorProfileManager()


class TeamMemberBody(BaseModel):
    """One colleague as MEMBERSHIP: the email that reaches their real
    Person note in the vault, and the role they hold.

    `email` is required and extras are forbidden, which is the whole
    point of declaring this at all -- a team entry carrying a `name` or
    a `title` is a second copy of a person that the vault already
    describes (`ADR-032`), and one carrying no email is membership in
    nothing, since the email IS the join key onto the Person note.
    `role` stays optional: a colleague whose role has not been written
    down yet is a real state, and refusing it would make the operator
    invent one.
    """
    model_config = ConfigDict(extra="forbid")

    email: str
    role: str = ""


class OperatorProfileBody(BaseModel):
    """A replacement of the whole record -- this is a `PUT`, so an
    omitted field means "empty", never "leave what was there". There is
    no partial-update convention here on purpose: the Profile is one
    small record the operator edits as a whole on one page, and a merge
    could not tell "the operator removed a colleague" from "the client
    only sent what it changed".

    `own_address` and `self_email` are declared only so they can be
    refused BY NAME (see the module docstring). Leaving them to
    `extra="forbid"` would answer the one payload most likely to be
    sent in good faith -- a `GET` body posted straight back -- with a
    generic "extra inputs are not permitted" that says nothing about
    where the address really lives.
    """
    model_config = ConfigDict(extra="forbid")

    name: str = ""
    other_email_addresses: list[str] = []
    timezone: str = ""
    team: list[TeamMemberBody] = []
    own_address: Any = None
    self_email: Any = None


def _refuse_an_attempt_to_write_the_own_address(body: OperatorProfileBody) -> None:
    if body.own_address is None and body.self_email is None:
        return
    raise HTTPException(
        status_code=409,
        detail=(
            "The operator's own email address is not stored in the Operator "
            f"Profile and cannot be set here: it is the {OWN_ADDRESS_SETTING_KEY} "
            f"setting, edited on {OWN_ADDRESS_EDITED_AT}. Send the Profile "
            "without it; nothing was saved."
        ),
    )


@router.get("/profile")
def get_operator_profile() -> OperatorProfile:
    """The one record, plus `own_address` -- read live from the setting,
    flagged `read_only`, and naming Settings > System as its editor so
    no reader has to hardcode that answer a second time -- plus
    `is_configured`, the honest answer to whether this install has ever
    saved a Profile."""
    return _operator_profile_manager.get()


@router.put("/profile")
def replace_operator_profile(body: OperatorProfileBody) -> OperatorProfile:
    """Replaces the one record and returns it exactly as `GET` would, so
    a client never has to re-read to find out what was stored.

    A refused payload leaves the stored Profile exactly as it was: every
    refusal above happens before the Manager is called, so there is
    nothing to roll back and no half-written record to read back."""
    _refuse_an_attempt_to_write_the_own_address(body)
    return _operator_profile_manager.save(
        {
            "name": body.name,
            "other_email_addresses": body.other_email_addresses,
            "timezone": body.timezone,
            "team": [member.model_dump() for member in body.team],
        }
    )
