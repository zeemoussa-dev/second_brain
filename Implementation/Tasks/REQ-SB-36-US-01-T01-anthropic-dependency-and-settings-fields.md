---
id: REQ-SB-36-US-01-T01
title: New anthropic dependency + ANTHROPIC_API_KEY/ANTHROPIC_MODEL Settings fields
parent_story: REQ-SB-36-US-01
requirement_id: REQ-SB-36
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-022 created, then amended mid-build by an operator correction — see Implementation Log) — carried from the parent story; the human reviews ADR-022 alongside this task breakdown."
phase: P1
depends_on: []
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-36-US-01-T01 — `anthropic` dependency + Settings fields

## Parent Story

- Story: [[REQ-SB-36-US-01]] — `../UserStories/REQ-SB-36-US-01-web-research-skill.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-36 *Agent Knowledge Bootstrapping via Delegated Research*

---

## Objective

Add the official `anthropic` Python SDK as a new backend dependency (`ADR-022` point 1 — deliberately not `langchain-anthropic`, since this skill never touches the LangGraph conversational graph), and two new required `Settings` fields (`anthropic_api_key`, `anthropic_model`) mirroring `compass_api_key`/`compass_model`'s existing shape exactly.

---

## Starting State → End State

**Before / Inputs:**
- `src/backend/requirements.txt` has no `anthropic`/`langchain-anthropic` entry.
- `app/config.py`'s `Settings` has no Anthropic-related field; `.env.example` has no `ANTHROPIC_*` key.

**After / Outputs:**
- `requirements.txt` gains `anthropic` (unpinned major, mirroring this project's existing precedent for `httpx`/`fastapi` etc. — pin only where an ADR names a specific major, per `MEMORY.md`'s own Pattern; `ADR-022` names no specific major).
- `Settings` gains `anthropic_api_key: str` and `anthropic_model: str`, both required (no default) — mirrors `compass_api_key`/`compass_model` exactly, so any environment missing either fails `Settings` construction at startup, the same behaviour a missing `COMPASS_*` value already has.
- `.env.example` gains `ANTHROPIC_API_KEY=` and `ANTHROPIC_MODEL=`.

---

## Files to Modify

- `src/backend/requirements.txt` — add `anthropic` (new line, after `langchain-mcp-adapters`).
- `src/backend/app/config.py` — add, alongside the existing `compass_*` fields:
  ```python
      anthropic_api_key: str
      anthropic_model: str
  ```
- `src/backend/.env.example` — add:
  ```
  ANTHROPIC_API_KEY=
  ANTHROPIC_MODEL=
  ```

---

## Constraints

- Inherits from parent story and `ADR-022` point 1.
- `anthropic`, not `langchain-anthropic` — this skill is never routed through `run_agent_conversation`'s LangGraph loop.
- Both new `Settings` fields are required (no default value) — mirrors `compass_api_key`/`compass_model`'s existing required-field shape, not an optional/None-defaulted pattern.
- Do not touch `model_factory.py` — explicitly out of scope per the parent story's own Architecture scope.

---

## Tests

**Manual verification steps:**
1. Non-AC smoke check: in `src/backend`'s real `.venv`, run `pip install -r requirements.txt`. Confirm `anthropic` installs with no missing-wheel/build-toolchain failure on this Windows host (mirrors `MEMORY.md`'s own `REQ-SB-25-US-01-T01` precedent of confirming a new dependency's real installability, not assuming it). Record the resolved version.
2. Non-AC smoke check: with a real `ANTHROPIC_API_KEY`/`ANTHROPIC_MODEL` set in the real `.env`, confirm `from app.config import settings; settings.anthropic_api_key` / `settings.anthropic_model` both resolve to the configured values.
3. Non-AC smoke check: temporarily rename/comment out `ANTHROPIC_API_KEY` in a throwaway copy of `.env` (not the real one), confirm `Settings()` construction raises a validation error (the same fail-fast behaviour a missing `COMPASS_*` value already has) — then confirm the real `.env` is restored and the app starts normally again.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `anthropic` installs cleanly in the real backend `.venv`
- [x] `Settings.anthropic_api_key`/`anthropic_model` are both required, mirroring `compass_*`'s exact shape
- [x] `.env.example` documents both new keys
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The Anthropic client itself — `T02`.
- Provider-registry seeding — `T03`.
- A real, operational `ANTHROPIC_API_KEY` value — provisioning the actual key is an operational step, not a code dependency (the parent story's own `## Dependencies`).

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-022` created at `/plan-tasks` step 1) — the human reviews `ADR-022` and this task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

This task carries no AC-tagged step of its own — it is purely foundational (dependency + config), mirroring `REQ-SB-21-US-01-T01`'s/`T02`'s own precedent for a non-AC-tagged primitives task.

---

## Implementation Log

Built exactly per spec — `requirements.txt` gained `anthropic` (new line,
after `langchain-mcp-adapters`); `config.py`'s `Settings` gained
`anthropic_api_key: str`/`anthropic_model: str` (required, no default,
mirroring `compass_api_key`/`compass_model` exactly); `.env.example`
gained `ANTHROPIC_API_KEY=`/`ANTHROPIC_MODEL=`.

**No AC-ID tagged to this task** (purely foundational, per its own
Context/Notes). All 3 manual verification steps performed live:

1. `pip install -r requirements.txt` against the real backend `.venv` —
   `anthropic` installed cleanly, no missing-wheel/build-toolchain
   failure. Resolved version: `anthropic==0.121.0` (pulled in one new
   transitive dependency, `docstring-parser==0.18.0`).
2. With `ANTHROPIC_API_KEY`/`ANTHROPIC_MODEL` set (see the credential
   note below), `Settings().anthropic_api_key`/`.anthropic_model` both
   resolved to the configured values; `compass_api_key` still resolved
   correctly alongside (no regression).
3. Confirmed directly against the REAL `src/backend/.env` (which
   genuinely lacked both new keys at the start of this task):
   `Settings()` raised a `pydantic.ValidationError` — "Field required" —
   for both `anthropic_api_key`/`anthropic_model`, the same fail-fast
   behaviour a missing `COMPASS_*` value already has. No throwaway copy
   was needed; the real file's own starting state already reproduced the
   exact missing-field condition step 3 asks for.

**Credential gap, honestly recorded, not fabricated:** no genuine
`ANTHROPIC_API_KEY` was available in this environment (operator-
confirmed: "do not guess or fabricate an API key"). A syntactically-valid,
clearly-labeled placeholder (`ANTHROPIC_API_KEY=NOT-PROVISIONED-PLACEHOLDER`,
`ANTHROPIC_MODEL=claude-sonnet-4-5-20250929`) was added to the real,
gitignored `.env` — purely so `Settings()`/the app could construct and
boot for this story's own downstream live verification (`T03`-`T06`), per
`ADR-022`'s own already-Accepted Consequences ("any environment missing
`ANTHROPIC_API_KEY` fails `Settings` construction at startup... an
operational step, not a code dependency"). This is provably inert — every
real Anthropic API call attempted against it during this build honestly
failed with a real `401 invalid x-api-key` (never a fabricated success).
Flagged in `REVIEW-QUEUE.md` for the operator to replace with a genuine
key. `.env` is `git`-ignored (confirmed via `git check-ignore -v`) — zero
commit/leak risk.

**Mid-build operator correction (not this task's own scope, recorded here
for context):** after this task and `T02`/`T03` were already built and
verified, the operator corrected `ADR-022` point 3's own Provider-
resolution design (`T04`/`T05` own the actual correction — see their own
Implementation Logs, `ADR-022`'s "Correction" addendum, and
`ESCALATIONS.md` → `ESC-019`). This task's own deliverables (the
dependency, the two `Settings` fields, `.env.example`) are unaffected by
that correction — they stay exactly as built.

`gate: clear` reasoning does not apply here — carried `flagged` from the
parent story (trigger 3, `ADR-022`, plus this same date's Correction
addendum) for combined human review.
