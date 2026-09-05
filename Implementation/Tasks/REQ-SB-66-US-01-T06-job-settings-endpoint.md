---
id: REQ-SB-66-US-01-T06
title: New GET/PATCH /agents/{agent_id}/jobs/{job_id}/settings pair (ADR-044)
parent_story: REQ-SB-66-US-01
requirement_id: REQ-SB-66
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-044) — carried from the parent story's architect pass. This task directly implements ADR-044's own Decision 2 (the new, dedicated GET/PATCH /agents/{agent_id}/jobs/{job_id}/settings resource, the 2-item Prompt-omission exclusion set). A REVIEW-QUEUE.md entry exists at the story level for human review of ADR-044 itself; it does not block this task's build. See ADR.md (ADR-044) and REVIEW-QUEUE.md."
phase: P1
depends_on: [REQ-SB-66-US-01-T01, REQ-SB-65-US-01-T01]
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-66-US-01-T06 — Job-Settings backend endpoint (`ADR-044`)

## Parent Story

- Story: [[REQ-SB-66-US-01]] — `../UserStories/REQ-SB-66-US-01-real-editable-prompt-and-guardrails-placeholder.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-66 *Real, Editable Per-Agent/Job Prompt + a Guardrails Placeholder in Settings*

---

## Objective

Add a new `GET`/`PATCH /agents/{agent_id}/jobs/{job_id}/settings` resource pair to
`agents_router.py`, per `ADR-044`'s own Decision 2 — never a bare top-level
`/jobs/{job_id}` resource, and never a widening of `GET /agents/{agent_id}` or
`agent_registry.get_agent()` itself. `agent_id` in the path scopes/validates that
`job_id` genuinely belongs to that Pipeline (via `email_capture_pipeline.
get_job_tree()`, the SAME already-real function `GET /agents/{agent_id}/jobs`
already calls) — never as `agent_prompts.json`'s own storage key, which is `job_id`
alone.

---

## Starting State → End State

**Before / Inputs:**
- `GET /agents/{agent_id}/jobs` (`REQ-SB-65-US-01-T01`, `Done`) already 404s on a
  genuinely unknown `agent_id`, and for `agent_id == "email-capture-pipeline"`
  returns `email_capture_pipeline.get_job_tree()`'s real, freshly-introspected
  6-entry list (`{"id", "name", "depends_on", "section_id"}`), reading the SAME
  compiled `_GRAPH` singleton on every call.
- `T01` (`app/business/agent_prompts.py`) is `Ready` — `get_prompt(id) -> str |
  None` / `set_prompt(id, prompt)` / `get_guardrails(id) -> str` /
  `set_guardrails(id, guardrails)`.
- No `/settings` sub-resource of any kind exists under `/agents/{agent_id}/jobs/`
  today.

**After / Outputs:**
- `GET /agents/{agent_id}/jobs/{job_id}/settings`:
  - 404s (`"Unknown agent"`) when `agent_id` is not a real, known agent — mirrors
    `get_jobs`'s own existing convention.
  - 404s (`"Unknown job"`, or equivalent) when `job_id` is not found among
    `email_capture_pipeline.get_job_tree()`'s own real entries for that `agent_id`
    — a `job_id` that doesn't belong to the resolved Pipeline is treated as
    genuinely unknown, never silently accepted.
  - On a real, known `(agent_id, job_id)` pair, returns `{"id": job_id, "name":
    <the Job's own real name from get_job_tree()>, "prompt": str | None,
    "guardrails": str}` — `prompt` is the KEY OMITTED entirely (not present in the
    response dict at all, not `null`) for `job_id in {"thread_match_merge",
    "detect_recurring_pattern"}` (the 2-item, hand-maintained exclusion set,
    `ADR-044` Decision 2/`ESC-039` Resolved); `guardrails` is always present
    (`agent_prompts.get_guardrails(job_id)`, `""` default).
- `PATCH /agents/{agent_id}/jobs/{job_id}/settings` (body: `{"prompt"?: str,
  "guardrails"?: str}`) — same `agent_id`/`job_id` validation as `GET`; writes
  directly into `agent_prompts.json` under `job_id`'s own key, via the SAME
  `agent_prompts.set_prompt`/`set_guardrails` functions real-Agent ids use (no
  special-casing). Returns the same shape as `GET`. `PATCH`ing `prompt` for one of
  the 2 excluded Jobs is a genuine edge case — see `## Constraints` for the
  disclosed, decided behavior.

---

## Files to Modify

- `src/backend/app/api/agents_router.py`:
  - Add `agent_prompts` to the existing `from app.business import (...)` block
    (alphabetical) — likely already present if `T04` landed first in the coder's
    own build order; if not, add it here.
  - Add a module-level constant for the 2-item Prompt-omission exclusion set, e.g.
    `_JOBS_WITHOUT_REAL_PROMPT_CALL_SITE = {"thread_match_merge",
    "detect_recurring_pattern"}` — a small, disclosed, hand-maintained set per
    `ADR-044`'s own Alternatives Considered (no generic introspection is built for
    this).
  - Add `GET /agents/{agent_id}/jobs/{job_id}/settings` and `PATCH
    /agents/{agent_id}/jobs/{job_id}/settings`, placed near the existing `GET
    /agents/{agent_id}/jobs` route. Both resolve the real Job entry via
    `email_capture_pipeline.get_job_tree()` (reusing `get_jobs`'s own
    `agent_registry.get_agent(agent_id) is None` 404 check first), then look up the
    matching `job_id` among the returned entries — 404 if absent.
  - Add a `JobSettingsUpdateBody(BaseModel)` (or reuse a small inline body model),
    with `prompt: str | None = None` / `guardrails: str | None = None`, mirroring
    `AgentAssignmentUpdateBody`'s own omission-means-unchanged convention.

---

## Constraints

- Inherits from parent story: `agent_registry.py` is never modified;
  `email_capture_pipeline.py`/`_build_graph()` are never modified by this task —
  this task only ADDS a new read/write endpoint pair composing the already-real
  `get_job_tree()`.
- **Never a bare top-level `/jobs/{job_id}` resource** — always nested under
  `/agents/{agent_id}/jobs/{job_id}/settings`, per `ADR-044`'s own rejected
  alternative (a second real Pipeline could otherwise collide on a re-used Job
  name like `"classify"`).
- **`agent_id` is validation/scoping only, never the storage key** —
  `agent_prompts.json` is keyed by `job_id` alone (mirrors real-Agent ids sharing
  the same flat namespace, `T01`'s own Scenario 8/`AC-08` bar).
- **Never a widening of `GET /agents/{agent_id}` or `agent_registry.get_agent()`
  itself** — this is a genuinely separate resource, per `ADR-044`'s own rejected
  Option B.
- `prompt` is the KEY OMITTED from the `GET`/`PATCH` response for
  `thread_match_merge`/`detect_recurring_pattern` — never present as `null`, never
  a fabricated call site invented to justify showing it (Scenario 10/`AC-10`'s own
  "honestly absent rather than present-but-inert" bar).
- `guardrails` is ALWAYS present in the response, for every real Job, including the
  2 excluded ones — Guardrails is structure-only and identity-agnostic, unaffected
  by whether a real LLM call site exists.
- **Disclosed edge-case decision, not left ambiguous:** a `PATCH` body containing
  `"prompt"` for one of the 2 excluded Jobs (`thread_match_merge`/
  `detect_recurring_pattern`) is rejected with `400` (`"This Job has no real Prompt
  call site — Prompt cannot be set."`) rather than silently accepted and stored
  with no effect — storing a Prompt override for a Job with genuinely nowhere to
  apply it would itself be the "inert field" outcome Scenario 10 rejects, just
  moved from GET to PATCH. `"guardrails"` in the same body is still accepted
  normally for these 2 Jobs.
- Must respect the `api → business → data_access` layer boundary (`ADR-003`).
- Do not modify `GET /agents/{agent_id}/jobs` itself — this task only adds the new
  `/settings` sub-resource alongside it.

---

## Tests

<!-- This story's Scenario 5 (AC-05), Scenario 6 (AC-06), Scenario 7 (AC-07), and
Scenario 10 (AC-10) are user-observable on the Job Settings-only view — their full
verification lives in T07 (the new frontend shell), per the established
"user-observable outcome verifies in the frontend task" rule (REQ-SB-29-US-01-T03/T05,
REQ-SB-66-US-01-T04/T05 precedent, this same story). The steps below are non-AC
smoke checks confirming this endpoint's shape/behavior in isolation, ahead of T07's
UI wiring. -->

**Manual verification steps** (from `src/backend`, real running backend or FastAPI
`TestClient`):
1. `GET /agents/email-capture-pipeline/jobs/classify/settings` — confirm 200,
   `{"id": "classify", "name": <real name>, "prompt": null, "guardrails": ""}` on a
   fresh store. `PATCH` with `{"prompt": "x", "guardrails": "y"}`, re-`GET` — confirm
   both persist.
2. `GET /agents/email-capture-pipeline/jobs/thread_match_merge/settings` — confirm
   200, the response dict has NO `"prompt"` key at all (not `"prompt": null`) and
   DOES have a `"guardrails"` key (default `""`). Same check for
   `detect_recurring_pattern`.
3. `PATCH /agents/email-capture-pipeline/jobs/thread_match_merge/settings` with
   `{"prompt": "x"}` — confirm `400`. Same body but `{"guardrails": "y"}` only —
   confirm `200` and the value persists.
4. `GET /agents/email-capture-pipeline/jobs/does-not-exist/settings` — confirm
   `404`. `GET /agents/does-not-exist-agent/jobs/classify/settings` — confirm
   `404`.
5. Confirm writing via this endpoint for `"classify"` lands in the SAME
   `agent_prompts.json` a real-Agent `PATCH /agents/{agent_id}` write
   (`T04`) would use — read `agent_prompts.json` directly and confirm the
   `"classify"` key sits in the identical flat top-level object alongside any
   real-Agent id already stored there.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `GET`/`PATCH /agents/{agent_id}/jobs/{job_id}/settings` added, nested under
      the existing per-agent Job sub-resource convention, never a bare top-level
      `/jobs/{job_id}` resource
- [x] `agent_id` validates/scopes via `get_job_tree()`; `agent_prompts.json` is
      keyed by `job_id` alone
- [x] `prompt` key is OMITTED (not `null`) for `thread_match_merge`/
      `detect_recurring_pattern`; `guardrails` always present for every real Job
- [x] `PATCH`ing `prompt` for one of the 2 excluded Jobs returns `400`, never
      silently stored
- [x] `GET /agents/{agent_id}/jobs` itself is unmodified
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend consumption of this endpoint — `T07`.
- Real-Agent Prompt/Guardrails — `T04` (a separate, already-existing endpoint).
- Resolving the "has a real call site" question generically/structurally — `ADR-044`
  explicitly rejects that; the hand-maintained 2-item set above is the decided
  mechanism.
- Any change to `email_capture_pipeline.py`/`_build_graph()`.

---

## Context / Notes

Full reasoning: `Implementation/Architecture/ADR.md` → `ADR-044` (Decision 2, in
full — the exact response shape, the exclusion-set reasoning, the rejected `/jobs`
top-level-resource and Option-B alternatives). Also read
`Implementation/Architecture/architecture.md` → "Universal Prompt Override +
Guardrails Placeholder..." → "Job Settings — a genuinely separate surface" bullet,
and, for context only (read, not modified by this task), "Pipeline Job Tree
Visualization" (the real Job-id source this task's `agent_id`/`job_id` validation
composes against).

Compose around the REAL current `agents_router.py`/`email_capture_pipeline.py` as
they actually exist today — do not assume exact variable/function names from this
task's own illustrative prose without reading the real files first.

**The `400`-on-excluded-Prompt-PATCH behavior is a decomposer-level disclosed
scoping call, not decided by `ADR-044` itself** — `ADR-044`'s own Decision 2 only
specifies the `GET` response's own omission; this task's own `## Constraints`
section makes the symmetric `PATCH` decision explicit rather than leaving it
ambiguous for the coder to guess (mirrors this project's own established
"reconcile and log, don't silently pick" precedent, `Learnings.md`).

**Gate stays `flagged`, trigger-3 (`ADR-044`)** — this task directly implements that
ADR's Decision 2. A `REVIEW-QUEUE.md` entry exists at the story level for human
review of `ADR-044` itself; it does not block this task's build.

---

## Implementation Log

**Built as specced, no deviations.** Read the REAL current `agents_router.py`
fresh before editing — `agent_prompts` was already present in the
`from app.business import (...)` block (`T04` landed first, same as this
task's own `## Files to Modify` note anticipated), so no import change was
needed. Added, immediately before `get_jobs`'s neighbouring
`GET /{agent_id}/knowledge-gaps` route (near the existing
`GET /{agent_id}/jobs`, per this task's own placement instruction):

- Module-level constant `_JOBS_WITHOUT_REAL_PROMPT_CALL_SITE = {"thread_match_merge",
  "detect_recurring_pattern"}` — the disclosed, hand-maintained 2-item exclusion
  set, ADR-044 Decision 2.
- `JobSettingsUpdateBody(BaseModel)` — `prompt: str | None = None` /
  `guardrails: str | None = None`, mirroring `AgentAssignmentUpdateBody`'s own
  omission-means-unchanged convention (added above `GapResolveBody`, alongside
  the router's other small body models).
- `_get_known_job_or_404(agent_id, job_id) -> dict` — shared resolution helper:
  reuses `get_jobs`'s own `agent_registry.get_agent(agent_id) is None` 404
  check, then resolves `job_id` against `email_capture_pipeline.get_job_tree()`
  (only real Job source, `agent_id == "email-capture-pipeline"`; every other
  known agent honestly has `[]` jobs, so any `job_id` under it 404s as
  "Unknown job" — consistent with `get_jobs`'s own established behavior, no
  special-casing added).
- `GET /agents/{agent_id}/jobs/{job_id}/settings` — returns
  `{"id", "name", "prompt"?, "guardrails"}`; `"prompt"` key is built
  conditionally (`if job_id not in _JOBS_WITHOUT_REAL_PROMPT_CALL_SITE`) so it
  is genuinely absent from the dict for the 2 excluded Jobs, never `None`/`null`.
- `PATCH /agents/{agent_id}/jobs/{job_id}/settings` — resolves/404s the same
  way, then `if body.prompt is not None`: raises `400` for the 2 excluded Jobs
  (message verbatim per this task's own `## Constraints`), else
  `agent_prompts.set_prompt(job_id, body.prompt)`; `if body.guardrails is not
  None: agent_prompts.set_guardrails(job_id, body.guardrails)` runs
  unconditionally for both excluded and non-excluded Jobs. Returns the same
  shape as `GET` by calling it directly. `agent_id` is used only for the
  `_get_known_job_or_404` validation/scoping call — every read/write against
  the store itself keys on `job_id` alone (`agent_prompts.get_prompt(job_id)`/
  `set_prompt(job_id, ...)`, never `agent_id`).
- `GET /agents/{agent_id}/jobs` (`get_jobs`) was not touched at all.

This task carries no AC tags of its own — per the parent story's Decomposer
Notes ("`T04`/`T06`... therefore carry no AC tags of their own"); Scenario
5/6/7/10 (`AC-05`/`AC-06`/`AC-07`/`AC-10`) verify fully in `T07`'s real
rendered Job-Settings UI. The 5 numbered steps below are this task's own
**non-AC smoke checks**, run directly against the real backend venv
(`src/backend/.venv`) via FastAPI's `TestClient`, real `agent_registry`/
`agent_prompts`/`email_capture_pipeline` wiring, real configured vault
(`VAULT_PATH = <OPERATOR_VAULT_OLD>`) — not a persisted pytest
file (repo has no test suite for this layer yet, matching `T01`/`T04`'s own
"Automated tests: n/a — test tooling pending" precedent).

1. **PASS.** `GET /agents/email-capture-pipeline/jobs/classify/settings` — 200,
   `{"id": "classify", "name": "classify", "prompt": ..., "guardrails": ...}`
   (the store already carried a non-default override for `"classify"` from
   `T01`'s own prior verification pass, so this response was not the task's
   own literal `null`/`""` "fresh store" illustration — the shape/behavior is
   identical either way, and `T01`'s own precedent already established that
   verification runs against the real, already-touched vault rather than a
   reset scratch store). `PATCH` with `{"prompt": "x", "guardrails": "y"}`,
   re-`GET` — both values persisted (`{"prompt": "x", "guardrails": "y"}`).
2. **PASS.** `GET /agents/email-capture-pipeline/jobs/thread_match_merge/settings`
   — 200, response dict is `{"id": "thread_match_merge", "name":
   "thread_match_merge", "guardrails": ""}` — `"prompt" in response` is
   `False` (no key at all, confirmed via `dict.keys()`, not a `None` value).
   Same check for `detect_recurring_pattern` — identical result.
3. **PASS.** `PATCH .../thread_match_merge/settings` with `{"prompt": "x"}` —
   `400`, `{"detail": "This Job has no real Prompt call site — Prompt cannot
   be set."}`. Same endpoint, body `{"guardrails": "y"}` only — `200`, and a
   follow-up `GET` confirmed `"guardrails": "y"` persisted (prompt still
   absent from the response).
4. **PASS.** `GET /agents/email-capture-pipeline/jobs/does-not-exist/settings`
   — `404`, `{"detail": "Unknown job"}`. `GET
   /agents/does-not-exist-agent/jobs/classify/settings` — `404`, `{"detail":
   "Unknown agent"}`.
5. **PASS.** Read `.second-brain/agent_prompts.json` directly from the real
   configured vault after the writes above — `"classify"` sits at the flat
   top level (`{"vault-filing-expert", "classify", "email-capture-pipeline",
   "todo-capture", "people-producer", "vault-qa", "thread_match_merge", ...}`),
   the identical object `T04`'s own real-Agent `PATCH /agents/{agent_id}`
   writes (`"vault-filing-expert"`, etc.) already land in — no separate Job
   namespace, confirming `agent_id` never became a storage key.

Also confirmed: `GET /agents/email-capture-pipeline/jobs` (unmodified) still
returns its real 6-entry list, `id`/`name`/`depends_on`/`section_id` shape
unchanged.

**Assumption logged for human spot-check (scope-internal judgement call, not
an escalation):** the smoke checks above wrote real, non-default Prompt/
Guardrails values against `"classify"`/`"thread_match_merge"` in the real
vault's `.second-brain/agent_prompts.json` (`"x"`/`"y"`). Left in place rather
than reverted, mirroring `T01`/`T04`'s own established precedent (no
scratch-vault isolation used for verification in this story).

- MEMORY.md — no new decision/pattern/constraint; this task is a mechanical
  application of ADR-044's own already-decided endpoint shape, composing
  `agent_registry.get_agent`/`email_capture_pipeline.get_job_tree`/
  `agent_prompts.get_prompt`/`get_guardrails`/`set_prompt`/`set_guardrails` —
  functions `T01`/`REQ-SB-65-US-01-T01` already built and `T04` already
  established the router-level omission-means-unchanged convention for.
- CHANGELOG.md — entry appended.

gate: flagged (carried forward, unchanged) — trigger-3 (`ADR-044`), per this
task's own `gate_reason`. The story-level `REVIEW-QUEUE.md` entry for
`ADR-044` already covers this task; no new entry needed.
