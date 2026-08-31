---
id: REQ-SB-82-US-06-T02
title: app/data_access/compass_client.py — new raw-HTTP Compass gpt-oss-120b client (ADR-011)
parent_story: REQ-SB-82-US-06
requirement_id: REQ-SB-82
type: backend
status: Done
gate: flagged
gate_reason: "Built and verified per scope; AC-06 (this task's one locked AC) passed live. A real, disclosed contradictory-input finding surfaced during verification (ESC-060): the real .env-backed Settings() has NON-blank Compass credentials (COMPASS_MODEL=gpt-5, not gpt-oss-120b), contradicting ADR-011's Consequences and the story's own Dependencies (both only checked .env.example). Not resolved by this task -- flagged to REVIEW-QUEUE.md/ESCALATIONS.md for human review; does not block this task's own Done status since AC-06 is independently verifiable regardless of the credential-blank premise."
phase: P2
depends_on: []
created: 2026-08-31
updated: 2026-08-31
---

# REQ-SB-82-US-06-T02 — app/data_access/compass_client.py: new raw-HTTP Compass gpt-oss-120b client (ADR-011)

## Parent Story

- Story: [[REQ-SB-82-US-06]] — `../UserStories/REQ-SB-82-US-06-live-routing-fix-and-reply-to-message.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-82 *Cockpit Mechanics — Prep, Research, and Moderation*

---

## Objective

Build `app/data_access/compass_client.py` — the first direct-to-LLM HTTP
client in the post-2026-08-20 backend (`ADR-011`) — raw request/response I/O
only, no business interpretation, raising a dedicated error on any failure.

---

## Starting State → End State

**Before / Inputs:**
- No live HTTP client to any LLM provider exists anywhere in `src/backend`
  today. `app/config.py`'s `Settings` already carries `compass_base_url:
  str`, `compass_api_key: str`, `compass_model: str` (required fields,
  currently blank in `.env.example`/the real `.env`). `app/hermes/rest.py`
  is the direct architectural precedent for "an HTTP client module at this
  layer, using `httpx` directly, raising a dedicated exception type on any
  `httpx.HTTPError`."

**After / Outputs:**
- `app/data_access/compass_client.py` (new file) exposing:
  - `class CompassClientError(Exception)` — mirrors
    `app/hermes/errors.py::HermesUnavailableError`'s own shape: raised for
    a real, attempted call that failed (network error, timeout, non-2xx
    response, or a response whose body doesn't match the expected shape)
    — never for "the feature doesn't exist yet."
  - A function that sends one chat-completion request to
    `settings.compass_base_url` using `settings.compass_api_key`/
    `settings.compass_model` via `httpx`, and returns the model's reply
    text on success. Suggested signature:
    `def request_chat_completion(messages: list[dict[str, str]], *,
    timeout: float = 20.0) -> str` — `messages` is an OpenAI-compatible
    `[{"role": "system"|"user", "content": "..."}]` list (the working
    assumption for `gpt-oss-120b`'s own request shape; **not yet
    confirmed against the real endpoint — see Constraints/Notes**).
  - Consumes `app.config.settings` directly (imported at call time, same
    pattern `providers.py`'s own `seed_defaults()` already uses) — never
    routes through `ProviderManager` (`ADR-011` point 3: `ProviderManager`
    is a CRUD/data Manager for the Provider entity, not a runtime call
    dispatcher).

---

## Files to Modify

- `src/backend/app/data_access/compass_client.py` (new file).

---

## Constraints

- Inherits from parent story.
- **Lives in `app/data_access/`, never `app/hermes/`** — `app/hermes` is
  reserved exclusively for calls to the Hermes gateway itself (2026-08-27's
  own hard rule: "exactly ONE file, `app/business/hermes/client.py`, may
  import from `app/hermes`"); a direct-to-Compass call is a categorically
  different integration (`ADR-011` point 1).
- **Raises `CompassClientError` on every real failure path** — network
  error, timeout, non-success HTTP status, or a response body that doesn't
  contain the expected reply content — never returns a bare `None` and
  never silently swallows an exception.
- **The exact request/response JSON contract is NOT confirmed against
  Compass's real API by this task** — real credentials
  (`COMPASS_BASE_URL`/`COMPASS_API_KEY`/`COMPASS_MODEL`) are still blank
  placeholders as of this pass (story Dependencies, disclosed, not
  re-investigated here). Build against the OpenAI-compatible chat-
  completions shape as the working assumption (widely-used convention for
  a `gpt-oss-*`-named model served behind an HTTP gateway), wrap response
  parsing in a `try/except` that raises `CompassClientError` on any
  unexpected shape (`KeyError`/`IndexError`/JSON-decode failure) rather
  than crashing — this is what makes `AC-06`'s degrade path safe today
  even though the happy path (`AC-02`) can't be live-confirmed yet
  (`ADR-011`'s own disclosed Consequence). Log this as a scope-internal
  judgement call in the Implementation Log; do not block the task on it.
- Never import `app.business.*` from this module (data_access is the
  lowest layer, `ADR-003`'s established `api -> business -> data_access`
  layering).

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-82-US-06-AC-06]` With `settings.compass_base_url`/
   `compass_api_key` left at their real, currently-blank values (or a
   deliberately unreachable URL), call `request_chat_completion([...])`;
   confirm it raises `CompassClientError` (not a bare `httpx` exception,
   not a silent `None`) with a message naming the real failure (connection
   refused / DNS failure / timeout). This is a REAL induced failure
   against a real (mis)configured client, not a mock.
2. In-process monkeypatch `httpx.post` (or the module's own request
   function) to return an engineered, well-formed OpenAI-compatible
   response body; confirm `request_chat_completion` returns the expected
   reply text extracted from it (no AC tag — build-time correctness check
   for the parsing path; the real end-to-end reasoning outcome this
   enables is `AC-02`, verified in `T03`/`T05` where this function is
   actually composed).
3. Monkeypatch the request function to return a malformed/unexpected body
   shape (e.g. missing the expected reply field); confirm
   `CompassClientError` is raised rather than an unhandled `KeyError`/
   `IndexError` (no AC tag — supports `AC-06`'s degrade-path safety net at
   the layer where a malformed real response would otherwise crash the
   caller).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `CompassClientError` is raised on every real failure path (network,
      timeout, non-2xx, malformed response) — never a bare exception, never
      a silent `None`
- [x] `request_chat_completion(...)` returns real reply text on a
      well-formed engineered success response
- [x] Module only imports `app.config`/`httpx`/stdlib — no `app.business.*`
      import
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Confirming the real Compass `gpt-oss-120b` request/response contract
  live — blocked pending real credentials (story Dependencies); disclosed
  explicitly above, not silently assumed correct.
- Any business-level prompt construction (roster/history/message
  composition) — that's `T03`.
- `ProviderManager`/Provider CRUD changes — explicitly out of scope per the
  story's own Non-Goals.

---

## Context / Notes

`ADR-011` (`Implementation/Architecture/ADR.md`) is the authoritative
design for this task — read it in full before starting. Cite `ADR-011`
going forward for any `has_real_client`/direct-LLM-client question; the
`ADR-022` several existing code comments (`provider_manager.py`) still cite
is confirmed orphaned/dead (pre-2026-08-20 history) — do not treat it as
live guidance.

---

## Implementation Log

**Built:** `src/backend/app/data_access/compass_client.py` (new file) —
`CompassClientError(Exception)`, and
`request_chat_completion(messages, *, timeout=20.0) -> str`. Sends one
OpenAI-compatible chat-completion `POST` to `settings.compass_base_url`
(`Authorization: Bearer {settings.compass_api_key}`, `model:
settings.compass_model`) via `httpx.post`. `httpx.HTTPError` (network
error, timeout, non-2xx via `raise_for_status()`) is caught and re-raised
as `CompassClientError`, chained (`from exc`) with the real underlying
message. Response-body parsing (`body["choices"][0]["message"]
["content"]`) is wrapped in `try/except (KeyError, IndexError, TypeError,
ValueError)` (`ValueError` also covers `httpx`'s JSON-decode failure) and
re-raised as `CompassClientError` — never an unhandled crash on a
malformed body. Consumes `app.config.settings` directly (module-level
import, matching `data_access/providers.py::seed_defaults()`'s own
pattern); no `ProviderManager` import. No `app.business.*` import
anywhere in the file (confirmed by an AST walk over the real file, see
below).

**Verification (manual mode) — run against the real `.venv` interpreter,
from `src/backend`, via a throwaway script
(`verify_compass_client.py`, not committed — scratch-only, in-process
monkeypatches/overrides on the already-imported `settings`/`httpx.post`
singleton, reverted after each block, zero permanent file edits beyond
`compass_client.py` itself):**

- **`REQ-SB-82-US-06-AC-06` — PASS, verified live.** In-process override
  of `settings.compass_base_url` to a deliberately unreachable address
  (`http://127.0.0.1:1/unreachable-compass-endpoint`, the task's own
  named Test-step alternative to "real, currently-blank values" — see the
  credential-discrepancy finding below for why the blank-value framing no
  longer matches reality), then called `request_chat_completion(...)`.
  Observed: a genuine `WinError 10061` ("No connection could be made
  because the target machine actively refused it") surfaced cleanly as
  `CompassClientError` — not a bare `httpx.ConnectError`, not a silent
  `None`. This is a real induced failure against a real (deliberately
  mis-)configured client, not a mock, per the task's own Test-step 1.
- **Build-time parsing check (no AC tag), Test-step 2 — PASS.**
  Monkeypatched `compass_client.httpx.post` to return an engineered,
  well-formed OpenAI-compatible body (`{"choices": [{"message":
  {"content": "engineered reply text"}}]}`); `request_chat_completion`
  returned exactly `"engineered reply text"`.
- **Build-time parsing check (no AC tag), Test-step 3 — PASS.**
  Monkeypatched the same call to return a malformed body (`{"unexpected":
  "shape"}`); `request_chat_completion` raised `CompassClientError`
  (`"...unexpected response shape: 'choices'"`), not an unhandled
  `KeyError`.
- **Import-scope check (AC-03 of this task's own DoD list) — PASS.** An
  `ast`-based walk of the real, saved `compass_client.py` found zero
  `app.business.*` imports.

**A real, disclosed scope-internal finding — NOT this task's own
`AC-02`/happy-path verification (that's `T03`/`T05`'s job, out of scope
here), logged for the record and escalated, not silently acted on:**
while setting up Test-step 1, printed `settings.compass_base_url ==
""`/`settings.compass_api_key == ""` to confirm the "currently-blank"
premise the task's Constraints/Tests describe — both came back `False`.
The real, `.env`-backed `Settings()` object (`src/backend/.env`, the file
`config.py` actually loads at runtime) has a real-looking
`COMPASS_BASE_URL`/`COMPASS_API_KEY`, and `COMPASS_MODEL=gpt-5` (not
`gpt-oss-120b`). Tracing the source: `ADR-011`'s own Consequences
paragraph and the parent story's own Dependencies section both cite
`.env.example` specifically (which genuinely IS blank) — neither checked
the real runtime `.env`. This task did **not** spend that real credential
on a live Compass call (explicitly `T03`/`T05`'s scope, not `T02`'s;
spending a real, possibly-paid/production key without explicit human
authorization is not this task's call to make unilaterally) — `AC-06`
was verified via the deliberately-unreachable-URL alternative instead,
which needed no real credential at all. Logged as `ESC-060`
(`ESCALATIONS.md`) plus a `REVIEW-QUEUE.md` continuation on this story's
own existing entry, since it may change how `T03`/`T05` scope their own
`AC-02` verification (possibly live-verifiable now, not
"blocked-pending-credentials" as both currently assume) — flagged for
human review, not resolved here, and does not block this task's own
`Done` status (`AC-06` is independently, fully verified regardless of the
credential-blank premise).

**MEMORY.md:** a new Pattern entry added — "raw-HTTP direct-to-LLM client
shape" (`app/data_access/<provider>_client.py`, dedicated error type,
consumes `app.config.settings` directly, never through a CRUD Manager) —
generalizes `ADR-011`'s own precedent for any future direct-LLM-provider
client.

**CHANGELOG.md:** entry appended under today's date.
