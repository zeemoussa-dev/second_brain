"""Business-layer wrapper over the Hermes library's REST status/session
calls -- turns a raw connection failure into an honest, structured
"unavailable" result rather than a 500."""
from __future__ import annotations

from app.business.hermes.client import HermesUnavailableError, get_client


def get_status() -> dict:
    try:
        return {"reachable": True, **get_client().rest.get_status()}
    except HermesUnavailableError as exc:
        return {"reachable": False, "error": str(exc)}


def get_sessions(limit: int = 50, offset: int = 0, profile: str | None = None) -> dict:
    try:
        return {"reachable": True, **get_client().rest.list_sessions(limit=limit, offset=offset, profile=profile)}
    except HermesUnavailableError as exc:
        return {"reachable": False, "error": str(exc)}


def get_session_stats() -> dict:
    try:
        return {"reachable": True, **get_client().rest.get_session_stats()}
    except HermesUnavailableError as exc:
        return {"reachable": False, "error": str(exc)}


def get_session_transcript(session_id: str, limit: int = 200, offset: int = 0) -> dict:
    """REQ-SB-100 -- one session read as a conversation. Unreachable
    Hermes is reported the way every other call here reports it, rather
    than as a 500: a transcript you cannot fetch is a known state, and
    the screen says so."""
    from app.business.hermes.session_transcript import read_session_transcript

    try:
        return {"reachable": True, **read_session_transcript(
            get_client().rest, session_id, limit=limit, offset=offset)}
    except HermesUnavailableError as exc:
        return {"reachable": False, "session_id": session_id, "error": str(exc)}


def search_sessions(query: str, limit: int = 50) -> dict:
    try:
        return {"reachable": True, **get_client().rest.search_sessions(query, limit=limit)}
    except HermesUnavailableError as exc:
        return {"reachable": False, "error": str(exc)}
