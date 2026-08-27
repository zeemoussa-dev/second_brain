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
