"""Configuration this library needs to reach a real Hermes install --
deliberately the ONLY thing the app/hermes package accepts from its
caller. Nothing under app/hermes imports application settings directly;
every value it needs arrives here, so this library stays a portable
Hermes client with zero awareness of Second Brain (or any other app
that might embed it)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class HermesConfig:
    # Hermes' own live local backend (`hermes serve`), e.g.
    # "http://127.0.0.1:9119" -- REST + WS chat both derive from this.
    base_url: str
    # Local filesystem root of the real Hermes install -- profiles,
    # SOUL.md/config.yaml files, skills/, cron/, logs/.
    home_path: Path
    # Optional manual override for the session token this library
    # otherwise fetches live from `GET /`'s own HTML. Empty string means
    # "use the real fetch-and-cache mechanism" -- not a required field.
    api_key: str = ""
    # The shared secret an INBOUND request (Hermes calling back into the
    # embedding app) must present -- only used by inbound_auth.py. Empty
    # string means inbound verification is not configured; callers that
    # need it should treat an empty secret as "reject everything", never
    # "allow everything".
    inbound_shared_secret: str = ""
