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


def get_entry_points(scan: int = 400) -> dict:
    """REQ-SB-102 -- the outside doors, as declared and as observed.

    Unreachable Hermes still answers usefully: the declarations are
    local and are shown with nothing to check them against, flagged as
    exactly that. A door the operator wrote down does not stop existing
    because the runtime is down.
    """
    from app.business.hermes import entry_points as entry_points_logic
    from app.data_access import entry_points as entry_points_data

    declared = entry_points_data.read_entry_points()
    try:
        return {"reachable": True, **entry_points_logic.build(
            get_client().rest, declared, scan=scan)}
    except HermesUnavailableError as exc:
        rows = entry_points_logic.reconcile(declared, [])
        return {
            "reachable": False,
            "error": str(exc),
            "entry_points": rows,
            "summary": entry_points_logic.summarise(rows),
            "scanned": None,
        }


def set_entry_points(entries: list[dict]) -> dict:
    """Replaces the whole declaration. A list, not a per-row edit: the
    set is small and the operator is editing a map, so saving the map
    they are looking at is the honest operation."""
    from app.data_access import entry_points as entry_points_data

    entry_points_data.write_entry_points(entries)
    return get_entry_points()

