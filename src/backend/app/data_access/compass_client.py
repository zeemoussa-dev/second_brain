"""Raw HTTP client for Compass `gpt-oss-120b` (`ADR-011`) -- the first
direct-to-LLM client in the post-2026-08-20 backend. Raw request/response
I/O only, no business interpretation: builds and sends one OpenAI-
compatible chat-completion request to `settings.compass_base_url` using
`settings.compass_api_key`/`settings.compass_model`, mirroring
`app/hermes/rest.py`'s own httpx-direct precedent at this layer.
Deliberately lives here, NOT in `app/hermes/` -- that package is reserved
exclusively for calls to the Hermes gateway itself (`ADR-011` Decision 1).
Consumes `app.config.settings` directly, the same class of structural
VALUE read `data_access/providers.py::seed_defaults()` already performs --
never routes through `ProviderManager` (`ADR-011` Decision 3).

The exact Compass request/response JSON contract is NOT confirmed against
the real endpoint by this module (`ADR-011` Consequences, `REQ-SB-82-US-06-
T02`'s own Constraints) -- built against the widely-used OpenAI-compatible
chat-completions shape as the working assumption. Response parsing is
wrapped so any unexpected shape degrades to `CompassClientError` rather
than an unhandled `KeyError`/`IndexError`/JSON-decode failure -- this is
what makes the degrade path (`REQ-SB-82-US-06-AC-06`) safe today even
though the happy path can't be live-confirmed by this module alone.
"""
from __future__ import annotations

import httpx

from app.config import settings


class CompassClientError(Exception):
    """Raised for a real, attempted Compass call that failed -- network
    error, timeout, non-success HTTP response, or a response body that
    doesn't match the expected chat-completion shape. Mirrors
    `app/hermes/errors.py::HermesUnavailableError`'s own shape; never
    raised for "the feature doesn't exist yet"."""


def request_chat_completion(messages: list[dict[str, str]], *, timeout: float = 20.0) -> str:
    """Sends one OpenAI-compatible chat-completion request to Compass and
    returns the model's reply text. `messages` is
    `[{"role": "system"|"user", "content": "..."}]`. Raises
    `CompassClientError` on every real failure path -- never returns a
    bare `None`, never silently swallows an exception."""
    payload = {"model": settings.compass_model, "messages": messages}
    headers = {
        "Authorization": f"Bearer {settings.compass_api_key}",
        "Content-Type": "application/json",
    }
    try:
        response = httpx.post(settings.compass_base_url, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise CompassClientError(f"Compass call failed (POST {settings.compass_base_url}): {exc}") from exc

    try:
        body = response.json()
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise CompassClientError(
            f"Compass call returned an unexpected response shape: {exc}"
        ) from exc
