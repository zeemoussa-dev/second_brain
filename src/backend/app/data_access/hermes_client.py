"""Client for Hermes' own real local backend (`hermes serve`,
https://github.com/nousresearch/hermes-agent) -- REBUILT 2026-08-20
against the actual, live-verified protocol, replacing an earlier version
built from research that did not match this installed version at all
(wrong port, wrong auth shape, wrong endpoint paths -- none of it
verified against a real running instance until today).

Real, confirmed protocol (verified live, 2026-08-20, against a real
running `hermes serve` process):
- Base URL: http://127.0.0.1:9119 (NOT 8642 -- that was never real).
- Auth: a per-install access token, embedded server-side in `GET /`'s own
  HTML as `window.__HERMES_SESSION_TOKEN__ = "..."`, sent back on every
  subsequent call as the `x-hermes-session-token` header. Not a
  pre-issued API key -- fetched and cached on first use. Confirmed by
  directly inspecting a real browser session's own network requests
  (captured via a monkey-patched window.fetch) and independently
  replaying the same header from a plain `curl` outside the browser --
  both succeeded against real endpoints returning real data.
- `/api/status` is deliberately public (`auth_required: false`) -- works
  with no token at all. Every other `/api/*` endpoint below requires the
  token.
"""
from __future__ import annotations

import re

import httpx

from app.config import settings

_TOKEN_RE = re.compile(r"window\.__HERMES_SESSION_TOKEN__\s*=\s*\"([^\"]+)\"")

# Cached after first fetch -- confirmed live to be stable across requests
# within one `hermes serve` process lifetime (the same value came back
# from a real browser session AND a fresh, independent curl call). Not
# confirmed to survive a `hermes serve` restart; a stale cached token
# would surface as a real 401/403 from the endpoints below, at which
# point re-fetching is the correct fix -- not yet wired as an automatic
# retry, since no restart has been observed to actually rotate it yet.
_cached_token: str | None = None


class HermesUnavailableError(Exception):
    """Hermes' backend did not respond, or responded with an error -- never
    raised for "the feature doesn't exist yet"; only for a real, attempted
    call that failed."""


def _fetch_session_token() -> str:
    global _cached_token
    if _cached_token is not None:
        return _cached_token
    if settings.hermes_api_key:
        # Manual override, e.g. for a Hermes instance this process can't
        # reach directly to scrape `GET /` from. Not the default path --
        # the real mechanism below is what this server actually uses.
        _cached_token = settings.hermes_api_key
        return _cached_token
    try:
        response = httpx.get(settings.hermes_base_url.rstrip("/") + "/", timeout=10.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HermesUnavailableError(f"Hermes call failed (GET /, fetching session token): {exc}") from exc
    match = _TOKEN_RE.search(response.text)
    if not match:
        raise HermesUnavailableError(
            "Hermes call failed: GET / did not contain window.__HERMES_SESSION_TOKEN__ "
            "-- the real page shape may have changed."
        )
    _cached_token = match.group(1)
    return _cached_token


def _headers() -> dict[str, str]:
    return {"x-hermes-session-token": _fetch_session_token()}


def _request(method: str, path: str, **kwargs) -> dict:
    url = f"{settings.hermes_base_url.rstrip('/')}{path}"
    try:
        response = httpx.request(method, url, headers=_headers(), timeout=30.0, **kwargs)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HermesUnavailableError(f"Hermes call failed ({method} {path}): {exc}") from exc
    if not response.content:
        return {}
    return response.json()


def get_status() -> dict:
    """GET /api/status -- deliberately public, no token required. Real
    version/health/gateway-state info, e.g. {"version", "gateway_running",
    "active_agents", "active_sessions", "nous_session_valid", ...}."""
    return _request("GET", "/api/status")


def list_sessions(limit: int = 50, offset: int = 0, profile: str | None = None) -> dict:
    """GET /api/sessions -- Hermes' own real Agent/session activity: id,
    source, model, message_count, token/cost accounting, timestamps.
    Requires the session token. `profile` is a real server-side filter
    (confirmed live, 2026-08-23 -- comparing an unfiltered call's own
    `total` against `profile=opp-manager`'s dropped it from every session
    to only that profile's own 6, every returned row's own `profile` field
    matching) -- omitted entirely (not sent as an empty string) when the
    caller wants every session, matching every other optional-filter
    convention already used across this file."""
    params: dict = {"limit": limit, "offset": offset, "order": "created"}
    if profile:
        params["profile"] = profile
    return _request("GET", "/api/sessions", params=params)


def get_session_stats() -> dict:
    """GET /api/sessions/stats."""
    return _request("GET", "/api/sessions/stats")


def get_config() -> dict:
    """GET /api/config."""
    return _request("GET", "/api/config")


def get_active_profile() -> dict:
    """GET /api/profiles/active."""
    return _request("GET", "/api/profiles/active")
