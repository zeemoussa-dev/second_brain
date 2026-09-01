---
id: REQ-SB-87-US-03-T03
title: Wire the classify-or-skip relay call into ingest_email.py
parent_story: REQ-SB-87-US-03
requirement_id: REQ-SB-87
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-87-US-03-T02, REQ-SB-87-US-02-T01]
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-03-T03 — Wire the Classify-or-Skip Relay Call into ingest_email.py

## Parent Story

- Story: [[REQ-SB-87-US-03]] — `../UserStories/REQ-SB-87-US-03-capture-time-noise-definition-and-classification.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

Insert ONE bounded, one-shot classify-or-skip relay call into
`ingest_email.py`'s own `if existing_directory is None:` branch, BEFORE any
Thread/RawMessage note is written — per `ADR-018`'s Decision — and stamp
the resulting classification onto every genuinely-created Thread.

---

## Starting State → End State

**Before / Inputs:**
- `REQ-SB-87-US-02-T01`'s migrated `ingest_email.py`:
  `existing_directory = vault_lib.resolve_thread_directory(...)` /
  `vault_manager.find_by_id(...)`; `if existing_directory is None:` creates
  the Thread unconditionally.
- `T02`'s classifier profile answers one bounded relay question.
- `T01`'s noise-definition artifact is readable via `--vault-path`.

**After / Outputs:**
- Inside the SAME `if existing_directory is None:` branch, BEFORE the
  Thread-creation call:
  1. Read the current noise-definition artifact
     (`.second-brain/data/EmailCapture/noise_definition.json`).
  2. Issue ONE `hermes -p <classifier-profile> chat -q "..."` subprocess
     call (the SAME `subprocess.run()`-style dispatch technique
     `run_delta_capture.py` already uses for every other per-email step),
     passing the definition's own content + this email's own sender/
     subject/body.
  3. Parse the structured JSON verdict.
  4. If `is_noise` is `true`: return early — no Thread, no RawMessage, no
     Person-note side effect, nothing written anywhere for this email — and
     the function's own returned dict gains a new `"skipped_as_noise":
     true` field (alongside `thread_created: false, message_created:
     false`) so the caller (`T04`, aggregating in
     `run_full_capture.py`/`run_delta_capture.py`'s own real per-email loop
     — confirmed directly, both read `ingest_email.py`'s own returned JSON
     via `result.get(...)`) can count it. Every OTHER (non-skip) return
     path keeps `"skipped_as_noise": false`.
  5. If `is_noise` is `false`: proceed to create the Thread exactly as
     today, additionally stamping the returned `classification` value into
     the Thread's own new frontmatter field (`REQ-SB-87-US-01-T05`'s own
     declared field).
- **Classification happens exactly once, at first sight of a
  conversation_id** — this branch only ever runs when `existing_directory
  is None`; an already-existing Thread's classification is never
  re-evaluated by a later message on the same conversation (a structural
  guarantee, not a runtime check — the branch itself is the guard).
- **Disclosed relay-failure degrade default (decomposer-level decision,
  per `ADR-018`'s own Consequences):** if the relay call fails or times
  out, treat this conversation as NOT YET classified — do not create a
  Thread, do not skip permanently. Let the SAME per-email
  `try/except ... continue` pattern already present in the orchestrators
  catch it, so this conversation is naturally retried on the NEXT capture
  tick (since `existing_directory` stays `None` until a Thread is actually
  written). Never silently default to "not noise" (fabricates a positive
  create) nor "is noise" (silently, permanently discards real content the
  operator never decided to skip).
- Sent Mail items are never excluded merely because they originated from
  the user's own mailbox — the classify-or-skip judgment only evaluates
  content, never the sender-is-self flag `outlook_lib.py`'s own 2026-08-24
  design already uses for combining Sent+Inbox into one Thread.

---

## Files to Modify

- `Hermes-Provisioning/skills/vault-rebuild/email-thread-capture/scripts/ingest_email.py`

---

## Constraints

- Inherits from parent story.
- One relay call per newly-first-seen `conversation_id` ONLY — never per
  message, never for an already-existing Thread.
- Never regress the Sent+Inbox combined-capture design.
- The relay call must run BEFORE any Thread/RawMessage note is written —
  a genuine skip must leave zero trace in the vault.
- Verify against the SAME scratch vault/100-email sample `REQ-SB-87-US-02`'s
  own tasks used — never the live vault for this task.

---

## Tests

**Manual verification steps (scratch vault, distinct `--vault-path`, real
~100-email sample):**
1. `[REQ-SB-87-US-03-AC-01]` Find (or engineer, within the scratch sample)
   a genuinely first-seen conversation whose content matches the current
   noise definition; run the migrated `ingest_email.py` against it.
   Confirm NO Thread note and NO RawMessage note are written anywhere for
   it.
2. `[REQ-SB-87-US-03-AC-02]` Run against a genuinely first-seen,
   non-noise conversation; confirm the created Thread's own frontmatter
   carries a real classification value of exactly one of Internal-only/
   Partner-related/Customer-related.
3. `[REQ-SB-87-US-03-AC-03]` Run `ingest_email.py` a SECOND time for a
   FURTHER message on the SAME already-classified conversation_id; confirm
   the existing RawMessage-creation/capture flow proceeds exactly as
   before, and the Thread's own classification value is unchanged — no
   second relay call is made for it (confirm via a log/print statement or
   subprocess-call count, not just the end-state value).
4. `[REQ-SB-87-US-03-AC-06]` Confirm a real Sent Mail item combining into
   an existing Thread (or forming a new one) is still combined with its
   Inbox counterpart exactly as `outlook_lib.py`'s own 2026-08-24 design
   already does — the new judgment step never excludes it.
5. (Unlabeled, supporting) Engineer a relay failure/timeout (e.g. a
   scoped, disclosed in-process monkeypatch of the relay call, reverted
   after); confirm the conversation is NOT classified as noise, no Thread
   is created, and it is naturally retried on the next call — matching
   the disclosed degrade default above.

**Automated tests:** `n/a — no existing pytest harness for this Skill;
verified via scratch-vault CLI runs`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Classify-or-skip relay call fires exactly once per newly-first-seen
      conversation_id, before any note is written
- [ ] Noise verdict → zero vault trace
- [ ] Non-noise verdict → Thread created with a real classification value
- [ ] Already-classified Thread never re-evaluated
- [ ] Sent+Inbox combined-capture design unaffected
- [ ] Relay failure degrades to "retry next tick," never a silent
      fabricated default
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Reporting the skip count through the orchestrators' own JSON summary —
  `T04`.
- Deriving/tweaking the noise-definition artifact's own content — `T01`/`T05`.
- Real-vault cutover — `T05`.

---

## Context / Notes

`ADR-018`'s own Decision, Alternatives Considered, and Consequences are
authoritative — read in full before implementing, especially the
Consequences' own note on assuming multi-minute relay latency is possible
and never assuming a hang.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
