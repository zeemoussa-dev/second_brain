"""The Chat page's conversations (operator, 2026-10-24: "Introduce Multiple
Chats, An Option to delete a Chat").

Signed in, and nothing finer. These are the operator's own conversations with
Primary on their own install -- there is no sharing model to enforce and
inventing one here would be inventing a requirement. The guard that matters is
the one every route has: a signed-out caller sees none of them.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.auth_guard import current_identity
from app.business.core.chats.chat_manager import ChatError, ChatManager

router = APIRouter(prefix="/chats", tags=["chats"])

_signed_in = Depends(current_identity)


class MessagesBody(BaseModel):
    """The whole thread as the page now has it -- see `replace_messages` for
    why this is a replace and not an append."""

    messages: list[dict]


def _as_dict(summary) -> dict:
    return {
        "id": summary.id,
        "title": summary.title,
        "created_at": summary.created_at,
        "updated_at": summary.updated_at,
        "message_count": summary.message_count,
    }


@router.get("", dependencies=[_signed_in])
def list_conversations() -> dict:
    """Most recently used first. Summaries only: a list of twenty threads
    should not carry twenty threads' worth of text to draw twenty rows."""
    return {"conversations": [_as_dict(summary) for summary in ChatManager().list()]}


@router.post("", dependencies=[_signed_in])
def create_conversation() -> dict:
    return _as_dict(ChatManager().create())


@router.get("/{conversation_id}", dependencies=[_signed_in])
def read_conversation(conversation_id: str) -> dict:
    conversation = ChatManager().get(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="That conversation no longer exists.")
    return conversation


@router.put("/{conversation_id}/messages", dependencies=[_signed_in])
def replace_messages(conversation_id: str, body: MessagesBody) -> dict:
    try:
        return ChatManager().replace_messages(conversation_id, body.messages)
    except ChatError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{conversation_id}", dependencies=[_signed_in])
def delete_conversation(conversation_id: str) -> dict:
    """Idempotent: deleting a conversation that is already gone is the state
    the caller wanted, not an error to show them."""
    return {"deleted": ChatManager().delete(conversation_id)}
