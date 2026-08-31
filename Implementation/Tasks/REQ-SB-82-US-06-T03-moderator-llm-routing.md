---
id: REQ-SB-82-US-06-T03
title: moderator.py — new LLM-based routing function composing compass_client (ADR-012 point 2)
parent_story: REQ-SB-82-US-06
requirement_id: REQ-SB-82
type: backend
status: Done
gate: flagged
gate_reason: "Built and verified per scope; both locked ACs (AC-02, AC-03) passed via the task's own mandated engineered/monkeypatched steps. A scope-internal judgement call (empty-candidates short-circuit) logged below for human spot-check. Additionally, per this build pass's own explicit authorization, used the REAL .env-backed Compass credentials (COMPASS_MODEL=gpt-5, not gpt-oss-120b -- ESC-060) for two bonus, disclosed, non-destructive live confirmation calls beyond what the task required -- both succeeded, genuinely reasoning over the given roster. Logged as a REVIEW-QUEUE.md continuation on the story's existing ESC-060 item, not a new escalation (no new dependency/interface/ADR deviation/unanticipated file)."
phase: P2
depends_on: [REQ-SB-82-US-06-T02]
created: 2026-08-31
updated: 2026-08-31
---

# REQ-SB-82-US-06-T03 — moderator.py: new LLM-based routing function composing compass_client (ADR-012 point 2)

## Parent Story

- Story: [[REQ-SB-82-US-06]] — `../UserStories/REQ-SB-82-US-06-live-routing-fix-and-reply-to-message.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-82 *Cockpit Mechanics — Prep, Research, and Moderation*

---

## Objective

Add a new function to `app/business/cockpit/moderator.py` that reasons over
the brought-in roster's own name/description, recent conversation history,
the new message's own text, and an optional reply-to hint, via
`compass_client`, to decide which one brought-in agent should answer.

---

## Starting State → End State

**Before / Inputs:**
- `moderator.py` owns two purely deterministic routing tracks today
  (`route_question`, `match_domain_experts`) — no LLM call anywhere in the
  module. `T02`'s `app/data_access/compass_client.py` now exists.

**After / Outputs:**
- A new function, sibling to `route_question`/`match_domain_experts` in the
  SAME `moderator.py` file (`ADR-012` point 2 — "one more real routing
  TRACK this module already owns the concept of," not a new file).
  Suggested signature:
  `def route_question_llm(question_text: str, candidates: list[dict],
  recent_messages: list[dict], reply_to_text: str | None = None) -> str |
  None` — `candidates` is `[{"id": ..., "name": ..., "description": ...},
  ...]` for the brought-in roster (same shape `agents_map_adapter.
  list_agent_summaries()` already returns per entry), `recent_messages` is
  the thread's own recent `messages` list (speaker/agent_name/text), and
  `reply_to_text` is the resolved text of the message being replied to,
  when present.
- Internally: builds a system+user prompt instructing the model to pick
  EXACTLY ONE of the given candidate agent ids (or explicitly signal "none
  of these fit") given the roster's own name/description, the recent
  history, the new question, and the reply-to hint when present (context,
  never a forced answer — the model's own reasoning decides, `ADR-012`
  point 4). Calls `compass_client.request_chat_completion(...)`; parses the
  model's reply to extract exactly one of the given candidate ids, or
  `None` if the model indicates no good match or its reply can't be parsed
  into one of the given ids (never a fabricated/guessed id outside the
  given candidate list).
- Raises nothing of its own on a `CompassClientError` — that exception
  propagates up to the caller (`T05`'s `chat_turn.py`), which is the layer
  that owns the degrade decision (`ADR-012` point 3) — this function does
  NOT catch-and-degrade itself.

---

## Files to Modify

- `src/backend/app/business/cockpit/moderator.py` — add the new function
  and its own prompt-building helper(s); import `compass_client` from
  `app.data_access`.

---

## Constraints

- Inherits from parent story.
- **Same module, not a new file** (`ADR-012` point 2).
- **Never returns an agent id outside the given `candidates` list** — a
  parsed model reply that doesn't map to exactly one candidate id is
  treated as `None` (no good match), never guessed/coerced to the nearest
  string.
- **Does not catch `CompassClientError`** — the degrade decision belongs to
  the caller (`T05`), not this function; catching and silently returning
  `None` here would make a real Compass failure indistinguishable from an
  honest "no good match" LLM answer, defeating `AC-06`'s own distinct
  degrade-path requirement.
- The reply-to hint (`reply_to_text`) is ONE MORE prompt input, never a
  separate branch/shortcut that could short-circuit the reasoning call
  (`ADR-012` point 4, Scenario 5's own "moderator retains final say").

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-82-US-06-AC-02]` In-process monkeypatch
   `compass_client.request_chat_completion` to return an engineered reply
   naming one specific candidate id from a 2+-candidate roster (e.g. two
   fictitious Experts, "azure-expert" and "masdar-expert", with distinct
   `description`s, and a question whose text is clearly about Azure);
   confirm `route_question_llm(...)` returns that candidate's own id
   (proving the function reasons over the real roster/message text it was
   given, not a hardcoded/keyword shortcut) and that exactly one id comes
   back, never a list/broadcast. Disclosed: this monkeypatch is necessary
   because real Compass `gpt-oss-120b` credentials are still blank
   placeholders as of this pass — the real live call is blocked-pending-
   credentials, not silently skipped (see `T02`'s own Tests block).
2. `[REQ-SB-82-US-06-AC-03]` Same setup as step 1, but pass a non-empty
   `reply_to_text` naming a DIFFERENT topic than the question itself (e.g.
   the replied-to message was about Masdar, the new question is clearly
   about Azure); inspect the actual prompt/messages payload handed to
   `compass_client.request_chat_completion` (via the monkeypatch's own
   captured call arguments) and confirm `reply_to_text`'s content is
   present in it — proves the hint genuinely reaches the reasoning pass as
   context.
3. Monkeypatch `compass_client.request_chat_completion` to return a reply
   that names an agent id NOT in `candidates` (or unparseable prose);
   confirm `route_question_llm(...)` returns `None` rather than fabricating
   or coercing to a candidate (no AC tag — supports `AC-02`'s "real
   reasoning, never a broadcast/guess" guarantee at this function's own
   boundary).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `route_question_llm(...)` composes `compass_client` with the given
      roster/history/message/reply-to-hint and returns exactly one
      candidate id or `None`
- [x] Never returns an id outside the given `candidates` list
- [x] Does not catch `CompassClientError` — propagates to the caller
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Deciding when to call this function vs. the deterministic degrade path,
  and resolving `reply_to_message_id` into `reply_to_text` from the real
  thread — both `T05`.
- The short-reply shortcut — `T04`.

---

## Context / Notes

`ADR-012` point 2 (`Implementation/Architecture/ADR.md`) is the
authoritative design. The exact prompt wording is left to the coder — no
locked AC asserts specific prompt phrasing, only the observable routing
outcome.

---

## Implementation Log

**Built:** `src/backend/app/business/cockpit/moderator.py` — added
`route_question_llm(question_text, candidates, recent_messages,
reply_to_text=None) -> str | None`, plus two private helpers,
`_build_routing_prompt(...)` (composes the OpenAI-compatible `messages`
payload: a system message naming the roster's own real `id`/`name`/
`description` and instructing the model to answer with exactly one
candidate id or `NONE`; a user message with the thread's recent history,
the optional reply-to hint, and the new question) and
`_parse_routing_reply(reply_text, candidates)` (word-boundary-scoped
regex match against the given `candidates`' own ids only — returns the one
id found, or `None` when zero or 2+ candidate ids appear in the reply,
never a fabricated/coerced id). `route_question_llm` itself has NO
`try/except` around `compass_client.request_chat_completion(...)` — a
`CompassClientError` propagates untouched to the caller, per this task's
own Constraint. Import added: `from app.data_access import
compass_client, vault_writer` (was `vault_writer` alone). Module docstring
updated to name the module's now-three routing/matching tracks (`ADR-012`
Consequences' own documentation-pass note).

**Scope-internal judgement call (logged for human spot-check, not an
escalation):** added `if not candidates: return None` as the function's
first line — a roster with zero brought-in Experts has nothing to choose
between; returning `None` immediately avoids a nonsensical Compass call
over an empty roster and costs nothing extra (the caller's own existing
"nobody matched" fallback chain — `T05` — already handles a `None`
return identically either way). Not asserted by any locked AC; a pure
short-circuit with no behavior change to any AC-observable outcome.

**Verification (manual mode) — run against the real `.venv` interpreter,
from `src/backend`, via two throwaway scratch scripts (not committed,
in-process monkeypatch of the already-imported `compass_client` module's
`request_chat_completion` attribute, reverted after each block; zero
permanent file edits beyond `moderator.py` itself):**

- **`REQ-SB-82-US-06-AC-02` — PASS, verified via engineered monkeypatch
  (task's own mandated technique) AND live.** Monkeypatch: with a
  2-candidate roster (`azure-expert`/`masdar-expert`, distinct real
  `description`s) and an Azure-topic question, `compass_client.
  request_chat_completion` engineered to return `"azure-expert"`;
  `route_question_llm(...)` returned exactly `"azure-expert"` (a single
  string, never a list/broadcast). **Bonus live confirmation** (see note
  below on real-credential use): the SAME call, unmonkeypatched, against
  the real `.env`-backed Compass endpoint (`COMPASS_MODEL=gpt-5`) also
  returned `"azure-expert"`; a second live call with the SAME roster but a
  Masdar-topic question returned `"masdar-expert"` — rules out an
  always-pick-first-candidate artifact, confirming genuine reasoning over
  the given roster/message, not a hardcoded/keyword shortcut.
- **`REQ-SB-82-US-06-AC-03` — PASS, verified via engineered monkeypatch.**
  Same 2-candidate setup; `reply_to_text` set to a Masdar-topic sentence
  while the question itself was Azure-topic. Captured the actual
  `messages` payload handed to `compass_client.request_chat_completion`
  via the monkeypatch's own captured call arguments — the exact
  `reply_to_text` string was present verbatim in the payload's `content`,
  confirming the hint genuinely reaches the reasoning pass as context.
- **No-AC-tag check (Test-step 3) — PASS.** Monkeypatched a reply naming
  an agent id NOT in `candidates` (`"gcp-expert"`); `route_question_llm`
  returned `None`, not a fabricated/coerced id.
- **Extra own-initiative checks — PASS.** An unparseable prose reply
  ("I think maybe none of these really fit well.") and an explicit `NONE`
  reply both returned `None`, confirming `_parse_routing_reply`'s honest
  no-match behavior beyond the task's own minimum bar.
- **Constraint check (does not catch `CompassClientError`) — PASS.**
  Monkeypatched `compass_client.request_chat_completion` to raise
  `CompassClientError("engineered failure")`; `route_question_llm(...)`
  raised the SAME exception uncaught to the caller — confirmed by
  `except CompassClientError` at the caller's own scope, not swallowed
  anywhere inside `route_question_llm`/its helpers.

**A disclosed, non-destructive use of the real `.env` Compass
credentials, per this build pass's own explicit authorization (not a
repeat of `T02`'s own declined unilateral spend):** the task's own Tests
block frames the monkeypatch as necessary because "real Compass
`gpt-oss-120b` credentials are still blank placeholders" — `ESC-060`
(logged by `T02`) already disclosed this premise is stale: the real,
`.env`-backed `Settings()` has non-blank `COMPASS_BASE_URL`/
`COMPASS_API_KEY`, with `COMPASS_MODEL=gpt-5` (not `gpt-oss-120b`). This
build pass's own launch instructions explicitly authorized judging
whether a genuine, disclosed, non-destructive live call was appropriate
here. Judged yes: two real chat-completion HTTP calls (read-only, no
vault/state mutation, small token cost) against the real, currently-
configured `gpt-5` deployment, both confirming `route_question_llm`
genuinely reasons correctly over a real roster (see `AC-02` above) — used
the REAL `.env` (not `.env.example`), model actually configured is
`gpt-5`. Logged as a `REVIEW-QUEUE.md` continuation on the story's
existing `ESC-060` item (not a new escalation — no new dependency, shared-
interface change, ADR deviation, or unanticipated file). The engineered/
monkeypatched steps alone were already fully sufficient to pass both
locked ACs per the task's own Tests block; the live calls are additional,
disclosed strengthening, not a substitute for the mandated technique.

**MEMORY.md:** a new Pattern entry added — "LLM-routing-function shape:
compose a data_access LLM client, build the prompt in a private helper,
parse the reply with a strict candidate-id-only regex match, never catch
the client's own dedicated error" — generalizes `ADR-012`'s own precedent
for any future LLM-composing routing/decision function in this codebase.

**CHANGELOG.md:** entry appended under today's date.

gate: flagged 2026-08-31 — a scope-internal judgement call (empty-
candidates short-circuit) plus a disclosed real-credential live-
verification use, both logged above for human spot-check; no locked AC
failed or was left unverified.
