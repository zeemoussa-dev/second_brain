"""Thin business-layer wrapper over hermes_client.py (ADR-005 point 5's own
"router never reaches into data_access/ directly" shape) -- turns a raw
connection failure into an honest, structured "unavailable" result rather
than a 500. Rebuilt 2026-08-20 to match hermes_client.py's real, verified
function names (get_status/list_sessions/get_session_stats/get_config/
get_active_profile), replacing the earlier, unverified health/
capabilities/jobs shape."""
from __future__ import annotations

from app.data_access import hermes_client


def get_status() -> dict:
    try:
        return {"reachable": True, **hermes_client.get_status()}
    except hermes_client.HermesUnavailableError as exc:
        return {"reachable": False, "error": str(exc)}


def get_sessions(limit: int = 50, offset: int = 0, profile: str | None = None) -> dict:
    try:
        return {"reachable": True, **hermes_client.list_sessions(limit=limit, offset=offset, profile=profile)}
    except hermes_client.HermesUnavailableError as exc:
        return {"reachable": False, "error": str(exc)}


def get_session_stats() -> dict:
    try:
        return {"reachable": True, **hermes_client.get_session_stats()}
    except hermes_client.HermesUnavailableError as exc:
        return {"reachable": False, "error": str(exc)}
