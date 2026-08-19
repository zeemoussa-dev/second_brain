---
id: REQ-SB-71-US-02-T06
title: POST /poc/synthesize-thread?conversation_id= — Stage 2 endpoint, no shared lock with Stage 1
parent_story: REQ-SB-71-US-02
requirement_id: REQ-SB-71
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-71-US-02-T04, REQ-SB-71-US-02-T05]
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-71-US-02-T06 — Stage 2 endpoint

## Parent Story

- Story: [[REQ-SB-71-US-02]] — `../UserStories/REQ-SB-71-US-02-email-capture-raw-distilled-and-two-stage-pipeline.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-71, point 2 (two-stage pipeline)

---

## Objective

Expose `T05`'s `synthesize_thread()` as a real, directly-callable `POST
/poc/synthesize-thread?conversation_id=<id>` endpoint, sharing no lock
with the Stage 1 endpoint (`T04`) — this is the task whose own `## Tests`
carries the AC-tagged, real-endpoint verification for Scenarios 4-6,
including the decoupling proof (Scenario 5).

---

## Starting State → End State

**Before / Inputs:**
- `T05`'s `email_classification.synthesize_thread(conversation_id) ->
  dict` exists and is directly callable in Python, but not yet reachable
  over HTTP.
- `T04`'s `POST /poc/capture-raw-thread-messages` already exists.

**After / Outputs:**
- `POST /poc/synthesize-thread?conversation_id=<id>` (required query
  parameter) calls `synthesize_thread(conversation_id=conversation_id)`
  and returns its result dict.

---

## Files to Modify

- `src/backend/app/api/email_poc_router.py` — import `email_classification.
  synthesize_thread`; add:
  ```python
  @router.post("/synthesize-thread")
  def synthesize_thread_endpoint(conversation_id: str) -> dict:
      return synthesize_thread(conversation_id=conversation_id)
  ```
  placed near `/capture-raw-thread-messages`.

---

## Constraints

- Inherits from parent story.
- **No scheduler wiring, no `agent_schedule_registry` entry.**
- **Shares no lock with `/poc/capture-raw-thread-messages`** — this
  endpoint's own handler must not acquire `agent_schedule_registry.
  get_shared_dispatch_lock()` or any other lock the Stage 1 endpoint's
  own call chain joins.
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).

---

## Tests

**Manual verification steps:**

1. `[REQ-SB-71-US-02-AC-04]` With at least one real Thread whose
   `messages/` folder already has one or more raw message notes
   (via `T04`'s own endpoint), call `POST /poc/synthesize-thread?
   conversation_id=<id>`. Confirm a 2xx response, confirm the response
   reports the determined Customer, and confirm the Thread note's `##
   Summary` was regenerated from the real content of every raw message
   note under `messages/` — read it back and confirm it reflects content
   from ALL of them, not just the latest.
2. `[REQ-SB-71-US-02-AC-05]` Induce a real or deliberately-induced stall
   inside a `POST /poc/synthesize-thread` call for one Thread (e.g. a
   scoped, disclosed in-process monkeypatch delaying the Compass call this
   function makes, mirroring this project's own established
   failure/delay-induction technique — `Implementation/Learnings.md`,
   `SPRINT-018`). While that call is still in flight, call `POST /poc/
   capture-raw-thread-messages` for a DIFFERENT, unrelated real email.
   Confirm the Stage 1 call completes normally and writes its own new raw
   message note without waiting for the stalled Stage 2 call — proving the
   two share no lock.
3. `[REQ-SB-71-US-02-AC-06]` Manually add real, distinct content to a real
   Thread note's `## Personal Notes` and `## Actions` sections directly in
   the vault (simulating an operator's own Obsidian edit). Call `POST
   /poc/synthesize-thread?conversation_id=<id>` again for that same
   Thread (e.g. after a further raw message has been captured). Confirm
   `## Summary` is regenerated from the current full set of raw messages,
   and confirm `## Personal Notes`/`## Actions` are read back byte-for-
   byte unchanged from what was manually added — neither section was ever
   targeted by this call.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `REQ-SB-71-US-02-AC-04` — Stage 2 does the real Compass-backed
      judgment and regenerates the Thread's distilled `## Summary` from
      every raw message
- [ ] `REQ-SB-71-US-02-AC-05` — a stall in Stage 2 never blocks Stage 1
      from continuing to capture further raw mail
- [ ] `REQ-SB-71-US-02-AC-06` — a manually-added Personal Notes/Actions
      entry survives byte-for-byte across a Stage 2 re-synthesis
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any `agent_schedule_registry`/scheduler wiring.
- Registering this capability id against `skill_registry.py`'s own
  chat-agent tool-exposure dicts — same disclosed scoping decision as
  `T04`.
- Files/OKF companion handling — `T07`'s own scope.

---

## Context / Notes

`ADR-048` Decision 3 (`Implementation/Architecture/ADR.md`): *"Exposed as
`POST /poc/synthesize-thread?conversation_id=<id>` — a second new,
independent capability id ... sharing NO lock with `capture_raw_thread_
messages`."*

---

## Implementation Log

**2026-08-18, `/implement-sprint SPRINT-061`:**

`POST /poc/synthesize-thread?conversation_id=` added to `email_poc_
router.py` exactly as specified, calling `synthesize_thread(conversation_
id=conversation_id)`. Shares no lock with `/poc/capture-raw-thread-
messages` — neither endpoint's own handler (nor anything either calls)
acquires `agent_schedule_registry.get_shared_dispatch_lock()` or any
other lock; both are plain, independent FastAPI `def` endpoints dispatched
to separate `run_in_threadpool` worker threads by construction.

**Real, live AC verification — every call a real HTTP request against
the real backend server and the real, live operator Outlook mailbox/
vault:**

**`[REQ-SB-71-US-02-AC-04]` PASS.** `POST /poc/synthesize-thread?
conversation_id=059EC2A1E82879429DFF7124FD5F836F` (a real Thread with 12
real raw messages) → `200 OK` (real call took ~70s of genuine Compass
latency; confirmed complete via direct vault read once finished, not via
the client connection, which this project's own established `SPRINT-018`
Learnings pattern of independently confirming a long real-Provider call
rather than assuming a hang was applied here — the server access log and
a direct poll of the note's own `## Summary` region confirmed real,
successful completion). `## Summary` regenerated from the REAL, FULL
content of all 12 raw messages (see `T05`'s own Implementation Log for
the specific textual evidence proving both an early AND a late message's
content are reflected, not just the latest). Second real call against
`01D26A7530444A23803A002210620160` (2 messages) also confirmed correct
full-reconstruction synthesis.
**`[REQ-SB-71-US-02-AC-05]` PASS.** Real, live concurrency proof (no
artificial monkeypatch needed — this session's own real Compass latency,
60-90+ seconds per Stage 2 call against this mailbox's real content,
served as a genuine, naturally-occurring stall): fired `POST /poc/
synthesize-thread?conversation_id=059EC2A1E82879429DFF7124FD5F836F` (12
messages) with the client abandoning after 5s (server continues
regardless — confirmed via the server's own access/Compass-call log
lines continuing to accumulate for 12+ real seconds afterward, well
before that call's own eventual completion). Immediately fired `POST
/poc/capture-raw-thread-messages?limit=3` for unrelated, different real
mail — **completed in 0.83 real seconds, logged and returned normally,
while the Stage 2 call was still actively making its own Compass calls**
(confirmed: the Stage 1 request's own access-log line appears
interleaved between ongoing Stage 2 `HTTP Request: POST .../chat/
completions "200 OK"` log lines). The server itself also stayed fully
responsive to unrelated requests (`GET /agents/email-capture-pipeline` →
`200`) throughout. Real, direct proof the two share no lock.
**`[REQ-SB-71-US-02-AC-06]` PASS.** Manually added real, distinct content
to `01D26A7530444A23803A002210620160`'s own `## Personal Notes` (a
prose note) and `## Actions` (a 3-item checklist, one checked) directly
in the vault file, recorded each section's own SHA-256 content hash, then
called `POST /poc/synthesize-thread?conversation_id=...` again for that
same Thread (which also regenerated `## Summary` with new text and added
2 real Files/OKF companions, `AC-07` below). Re-read both sections
afterward: **byte-for-byte identical SHA-256 hashes** to the pre-call
values — neither section was ever touched.

**Real bug found and fixed live, in-scope, during this task's own
AC-07-adjacent verification (`T07`'s own `write_file_companion`,
`email_classification.py`, in scope for that task):** the file-slug
computed from an already-80-char-truncated message-id slug plus a real
filename silently exceeded `_slugify`'s own 80-char cap, dropping the
filename entirely and risking a same-message multi-attachment collision.
Fixed to a short `hash8(message_id)-<filename>` disambiguator; re-verified
live afterward — confirmed correct for a message with 2 real distinct
attachments (`0d25671f-20260508_Core42 Compass_Ewec.pdf` and
`0d25671f-AI Use cases - Compass.xlsx` both present, un-collided). Full
detail in `T07`'s own Implementation Log.

Status → `Done`. `gate: clear` — no MUST-FLAG trigger; all 3 locked ACs
verified with real, live evidence.
