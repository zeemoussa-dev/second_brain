"""Second Brain's own singleton Hermes client. This is the ONLY file in
the entire app allowed to import from app/hermes -- every other module,
anywhere in the codebase, reaches Hermes exclusively through
`get_client()` here (or through the thin business/hermes/* wrappers that
themselves call it). That boundary is what keeps app/hermes a portable
library: it never sees app.config, and nothing outside this one file
ever constructs a HermesConfig by hand.

`HermesUnavailableError` is re-exported here for the same reason -- a
caller catching it should never need to import app.hermes directly just
for the exception type.
"""
from __future__ import annotations

from app.config import settings
from app.hermes import HermesAgent, HermesClient, HermesSkill, HermesUnavailableError
from app.hermes.chat_session import HermesChatSession

__all__ = [
    "get_client", "HermesUnavailableError", "HermesChatSession",
    "HermesAgent", "HermesSkill",
]

_client: HermesClient | None = None


def get_client() -> HermesClient:
    global _client
    if _client is None:
        _client = HermesClient.init(
            base_url=settings.hermes_base_url,
            home_path=settings.hermes_home_path,
            api_key=settings.hermes_api_key,
        )
    return _client
