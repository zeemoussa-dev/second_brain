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


class CompassEmbeddingsUnavailableError(CompassClientError):
    """The embeddings route was reached but refused the request -- most
    often a subscription that lists an embedding model in its catalogue
    without being entitled to call it (confirmed live 2026-09-13: every
    real embedding model returns HTTP 400 "You may not have a quota or
    access to use this model", while an invented one returns 404). Kept
    distinct from CompassClientError so the semantic layer can report
    "embeddings are not enabled on this subscription" rather than the
    generic "the call failed", and so it never reads as a code defect."""


def request_embeddings(inputs: list[str], *, timeout: float = 60.0) -> list[list[float]]:
    """Embeds `inputs` in ONE request and returns one vector per input,
    in the order given. The provider is free to return `data` out of
    order, so entries are re-sorted by their own `index` field rather
    than trusted positionally -- an off-by-one here would silently
    attach every note to its neighbour's meaning, which no test of
    ranking quality would obviously catch."""
    endpoint = settings.compass_embeddings_endpoint
    if not endpoint or not settings.compass_api_key:
        raise CompassEmbeddingsUnavailableError(
            "Compass embeddings are not configured (compass_base_url/compass_api_key)"
        )

    payload: dict = {"model": settings.compass_embedding_model, "input": inputs}
    if settings.compass_embedding_dimensions > 0:
        payload["dimensions"] = settings.compass_embedding_dimensions
    headers = {
        "Authorization": f"Bearer {settings.compass_api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = httpx.post(endpoint, json=payload, headers=headers, timeout=timeout)
    except httpx.HTTPError as exc:
        raise CompassClientError(f"Compass embeddings call failed (POST {endpoint}): {exc}") from exc

    if response.status_code >= 400:
        # The provider's own message is the actionable part ("no quota",
        # "invalid input model") -- swallowing it for a tidy generic error
        # would send the operator to read code instead of a subscription.
        raise CompassEmbeddingsUnavailableError(
            f"Compass embeddings refused the request (HTTP {response.status_code}): "
            f"{response.text[:300]}"
        )

    try:
        rows = sorted(response.json()["data"], key=lambda row: row["index"])
        vectors = [[float(value) for value in row["embedding"]] for row in rows]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise CompassClientError(
            f"Compass embeddings returned an unexpected response shape: {exc}"
        ) from exc

    if len(vectors) != len(inputs):
        raise CompassClientError(
            f"Compass embeddings returned {len(vectors)} vectors for {len(inputs)} inputs"
        )
    return vectors
