"""REST calls against Hermes' own local backend (`hermes serve`).

Real, confirmed protocol: auth is a per-install access token, embedded
server-side in `GET /`'s own HTML as `window.__HERMES_SESSION_TOKEN__ =
"..."`, sent back on every subsequent call as the `x-hermes-session-
token` header -- not a pre-issued API key, fetched and cached on first
use. `/api/status` is deliberately public (`auth_required: false`);
every other `/api/*` endpoint requires the token.
"""
from __future__ import annotations

import re

import httpx

from app.hermes.config import HermesConfig
from app.hermes.errors import HermesUnavailableError

_TOKEN_RE = re.compile(r"window\.__HERMES_SESSION_TOKEN__\s*=\s*\"([^\"]+)\"")


class HermesRestAPI:
    """One instance per `HermesClient` -- caches its own session token for
    the lifetime of that client, same as the module-level cache the
    original single-config version used."""

    def __init__(self, config: HermesConfig) -> None:
        self._config = config
        self._cached_token: str | None = None

    def get_session_token(self) -> str:
        if self._cached_token is not None:
            return self._cached_token
        if self._config.api_key:
            # Manual override, e.g. for a Hermes instance this process
            # can't reach directly to scrape `GET /` from.
            self._cached_token = self._config.api_key
            return self._cached_token
        try:
            response = httpx.get(self._config.base_url.rstrip("/") + "/", timeout=10.0)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise HermesUnavailableError(f"Hermes call failed (GET /, fetching session token): {exc}") from exc
        match = _TOKEN_RE.search(response.text)
        if not match:
            raise HermesUnavailableError(
                "Hermes call failed: GET / did not contain window.__HERMES_SESSION_TOKEN__ "
                "-- the real page shape may have changed."
            )
        self._cached_token = match.group(1)
        return self._cached_token

    def _headers(self) -> dict[str, str]:
        return {"x-hermes-session-token": self.get_session_token()}

    def _request(self, method: str, path: str, **kwargs) -> dict:
        url = f"{self._config.base_url.rstrip('/')}{path}"
        try:
            response = httpx.request(method, url, headers=self._headers(), timeout=30.0, **kwargs)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise HermesUnavailableError(f"Hermes call failed ({method} {path}): {exc}") from exc
        if not response.content:
            return {}
        return response.json()

    def get_status(self) -> dict:
        """GET /api/status -- deliberately public, no token required."""
        return self._request("GET", "/api/status")

    def list_sessions(self, limit: int = 50, offset: int = 0, profile: str | None = None) -> dict:
        """GET /api/sessions. `profile` is a real server-side filter --
        omitted entirely (not sent as an empty string) when the caller
        wants every session."""
        params: dict = {"limit": limit, "offset": offset, "order": "created"}
        if profile:
            params["profile"] = profile
        return self._request("GET", "/api/sessions", params=params)

    def get_session_stats(self) -> dict:
        return self._request("GET", "/api/sessions/stats")

    def get_config(self) -> dict:
        return self._request("GET", "/api/config")

    def get_active_profile(self) -> dict:
        return self._request("GET", "/api/profiles/active")
