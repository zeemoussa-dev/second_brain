"""Issuing and revoking the credentials Hermes workers authenticate
with (`REQ-SB-103`, `ADR-062`).

Every route requires `MANAGE_AGENTS`, declared once on the router
rather than repeated per route -- the same reasoning
`admin_users_router` states, one level down from the middleware.
`MANAGE_AGENTS` rather than `MANAGE_USERS` because the subject is an
agent, not a person; it is Admin-only either way, and issuing a key
that lets a machine reach this install is not a thing a Power User
does.

**The token text exists in exactly one response and nowhere else.**
Minting answers with it; nothing else ever can, because only its
SHA-256 is stored. That is the reason the create route's response
shape differs from the list route's, and the reason the screen tells
the operator to copy it before leaving the page.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.auth_guard import current_identity, requires
from app.business.core.users.agent_token import AgentTokenRecord
from app.business.core.users.agent_token_manager import AgentTokenError, AgentTokenManager
from app.business.core.users.user import Capability, Identity

router = APIRouter(
    prefix="/admin/agent-tokens",
    tags=["admin"],
    dependencies=[Depends(requires(Capability.MANAGE_AGENTS))],
)
_tokens = AgentTokenManager()


class MintTokenBody(BaseModel):
    agent_id: str = Field(min_length=1)
    # What this key is for, in the operator's own words -- "the WhatsApp
    # worker on the laptop". Revoking a key six months from now means
    # knowing which one it was, and a list of digests answers that for
    # nobody.
    label: str = ""


def _as_row(record: AgentTokenRecord) -> dict:
    return {
        "token_sha256": record.token_sha256,
        "agent_id": record.agent_id,
        "label": record.label,
        "created_at": record.created_at,
        "created_by": record.created_by,
        "last_seen_at": record.last_seen_at,
        "revoked_at": record.revoked_at,
        "is_revoked": record.is_revoked,
        "has_ever_been_used": record.has_ever_been_used,
    }


@router.get("")
def list_agent_tokens() -> list[dict]:
    """Every credential this install has issued, revoked ones included
    and labelled as such. None of them carries its token text."""
    return [_as_row(record) for record in _tokens.get_all()]


@router.post("")
def mint_agent_token(
    body: MintTokenBody, identity: Identity = Depends(current_identity),
) -> dict:
    """Issue one credential for one agent.

    `token` in the response is the only time this install can produce
    it. The operator puts it in that worker's environment as
    `SECOND_BRAIN_AGENT_TOKEN`; if it is lost, the honest answer is to
    revoke this one and mint another, which is why revoking is cheap.
    """
    try:
        record, token_text = _tokens.mint(
            body.agent_id, body.label, created_by=identity.user.username,
        )
    except AgentTokenError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {
        **_as_row(record),
        "token": token_text,
        "shown_once": (
            "Copy this now and put it in that worker's environment as "
            "SECOND_BRAIN_AGENT_TOKEN. Only its fingerprint is stored, so this app cannot "
            "show it again -- if it is lost, revoke it and mint another."
        ),
    }


@router.delete("/{token_sha256}")
def revoke_agent_token(token_sha256: str) -> dict:
    """Revoke one credential. Dated, not deleted: after a key has
    leaked, "was it revoked, and when" is the question that matters,
    and a row that vanished answers it for nobody."""
    try:
        return _as_row(_tokens.revoke(token_sha256))
    except AgentTokenError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
