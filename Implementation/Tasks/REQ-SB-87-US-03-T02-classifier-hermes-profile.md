---
id: REQ-SB-87-US-03-T02
title: Provision the dedicated Capture-classifier Hermes profile
parent_story: REQ-SB-87-US-03
requirement_id: REQ-SB-87
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-87-US-03-T01]
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-03-T02 — Provision the Dedicated Capture-Classifier Hermes Profile

## Parent Story

- Story: [[REQ-SB-87-US-03]] — `../UserStories/REQ-SB-87-US-03-capture-time-noise-definition-and-classification.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

Provision a new, dedicated, lightweight Hermes profile that answers ONE
bounded `chat -q` relay question per genuinely-new conversation — "is this
noise, and if not, what's its coarse classification?" — per `ADR-018`'s
Decision.

---

## Starting State → End State

**Before / Inputs:**
- No dedicated classifier profile exists.
- `T01`'s noise-definition artifact exists at
  `.second-brain/data/EmailCapture/noise_definition.json`.
- Real precedent for a lightweight, non-agentic-loop relay-target profile:
  `research-agent` (`REQ-SB-82-US-02`), provisioned via `hermes profile
  create <name> --clone` at `%LOCALAPPDATA%\hermes\profiles\<name>\`.

**After / Outputs:**
- A new, real, live Hermes profile (a disclosed name, e.g.
  `email-capture-classifier`) provisioned at
  `%LOCALAPPDATA%\hermes\profiles\<name>\`.
- Its own `SOUL.md` instructs it to: read the noise-definition artifact's
  own current content (passed in the relay call's own question text, or
  read directly if the profile has vault access — this task's own disclosed
  choice) plus the new email's own sender/subject/body (also passed in the
  question text); reason about whether it matches the noise definition;
  return ONE structured JSON verdict — conceptually `{"is_noise": bool,
  "classification": "internal" | "partner" | "customer" | null, "reasoning":
  str}` (exact field names this task's own call, matching `ADR-018`'s own
  illustrative shape) — and NOTHING ELSE (no tool-calling loop, no
  multi-turn follow-up expected; a single bounded `chat -q` reply).
- No cron job for this profile — it is invoked ONLY as a one-shot relay
  target from `ingest_email.py` (`T03`), never on its own schedule.
- No vault-write capability granted — this profile only ever answers a
  question; it never writes a note itself (the calling script does that).

---

## Files to Modify

- None new in the repo's own version control (mirrors
  `REQ-SB-82-US-05-T02`'s own established precedent — real, live Hermes-side
  profile provisioning has no further checked-in-repo file to diff, beyond
  whatever the coder discloses in this task's own Implementation Log).

---

## Constraints

- Inherits from parent story.
- **The agent decides, the script only applies** — this profile's own
  SOUL.md must instruct it to return a real, honest verdict based on actual
  reasoning over the definition + email content, never a rubber-stamp
  "not noise" default.
- The verdict's own `classification` value must be exactly one of
  Internal-only / Partner-related / Customer-related when `is_noise` is
  `false` — never fabricated, never `Noise` (a noise Thread is never
  created at all, so `classification` is meaningless/`null` when
  `is_noise` is `true`).
- No tool-calling loop — this is a bounded, single-reply relay target, not
  an agentic session with `search_files`/`terminal` access to the vault.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-87-US-03-AC-02]` Issue a real, direct relay call (`hermes -p
   <classifier-profile> chat -q "..."`) with a genuine non-noise email's
   content (sender/subject/body) plus the current noise definition;
   confirm the returned verdict has `is_noise: false` and a real
   `classification` value of exactly one of Internal-only/Partner-related/
   Customer-related.
2. `[REQ-SB-87-US-03-AC-01]` Issue the same relay call with content that
   genuinely matches the current noise definition (e.g. an obvious
   automated notification/newsletter pattern the definition names);
   confirm `is_noise: true`.
3. (Unlabeled, supporting) Confirm the profile has NO vault-write
   capability and no cron job of its own.

**Automated tests:** `n/a — real, live Hermes-side profile provisioning;
verified via real relay calls`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Real, live classifier profile provisioned
- [ ] Returns a real, structured `{is_noise, classification, reasoning}`
      verdict for both a noise and a non-noise real input
- [ ] No vault-write capability, no cron job of its own
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Wiring the actual relay CALL into `ingest_email.py` — `T03`.
- The noise-definition artifact itself — `T01`.

---

## Context / Notes

`ADR-018`'s own Decision + Alternatives Considered (the rejected
bespoke-direct-HTTP-client and static-system-prompt options) are
authoritative. `REQ-SB-82-US-05-T02`'s own Implementation Log is the
closest real precedent for how live Hermes profile provisioning is
disclosed in this pipeline's own task-file convention — read it before
starting.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
