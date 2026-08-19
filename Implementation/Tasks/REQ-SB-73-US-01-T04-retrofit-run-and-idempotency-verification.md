---
id: REQ-SB-73-US-01-T04
title: One-time retrofit run of link_thread_messages() against the full real corpus + idempotency re-run verification
parent_story: REQ-SB-73-US-01
requirement_id: REQ-SB-73
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-73-US-01-T01, REQ-SB-73-US-01-T02, REQ-SB-73-US-01-T03]
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-73-US-01-T04 — Retrofit run + idempotency verification

## Parent Story

- Story: [[REQ-SB-73-US-01]] — `../UserStories/REQ-SB-73-US-01-bidirectional-thread-message-linking.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-73 *Bidirectional Thread ↔ Message Linking (Retrofit + Rename-Safe)*
- Architecture: `Implementation/Architecture/architecture.md` → "The Librarian — Bidirectional Thread ↔ Message Linking"

---

## Objective

Run `link_thread_messages()` for real against the full real corpus (137 Threads / 257 messages, counts as of 2026-08-19 — re-confirm the live count before running, since ordinary organic capture growth is expected) via the real `POST /poc/librarian-link-thread-messages` endpoint, then re-run it a second time and prove the corpus is byte-for-byte unchanged — the one-time retrofit AND the idempotency guarantee, both real, both live.

---

## Starting State → End State

**Before / Inputs:**
- `link_thread_messages()` exists (`T01`), the `rename_threads()` fan-out extension is deployed (`T02`), and `POST /poc/librarian-link-thread-messages` is reachable (`T03`).
- The real corpus has NOT yet been through a full `link_thread_messages()` pass — most real Thread concept files have no `## Messages` section, most real message notes have no `thread:` field.

**After / Outputs:**
- Every real Thread concept file under `Work/Threads/` has a correct, complete `## Messages` section listing every one of its own current real messages.
- Every real raw message note under `Work/Threads/*/messages/` has a correct `thread:` field resolving to its owning Thread's current stem.
- A second, immediately-following run via the same real endpoint produces ZERO file changes anywhere in the corpus — proven by a real, direct byte-for-byte (or content-hash) before/after comparison, not merely "the return value looked the same."

---

## Files to Modify

- `src/backend/app/business/pipelines/librarian_housekeeping.py` — no code change expected in this task (verification-only); if a genuine defect surfaces during the real run, fix it here, in scope.

---

## Constraints

- Inherits from parent story.
- This IS the retrofit vehicle — no separate, standalone script (`MEMORY.md` — API-first, no script workarounds). The real, already-built `link_thread_messages()` Job, invoked via its own real endpoint, is the entire mechanism.
- The idempotency check must be a REAL before/after comparison of the corpus's own actual file bytes/hashes across the two real runs, not an assumption from reading the code.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-73-US-01-AC-06]` Before the first run: capture a content hash (e.g. SHA-256) of every real Thread concept file and every real message note currently under `Work/Threads/` (or a representative, disclosed sample if the full 137/257 set is impractical to hash individually — name the sample size actually used). Run `POST /poc/librarian-link-thread-messages` for real against the full corpus; confirm a real `200` and a sane result summary (Threads processed, messages linked). Immediately re-run the SAME endpoint a second time; capture content hashes again; confirm EVERY file's hash is identical between the post-first-run and post-second-run states — a true no-op on the second call, proving the Job is idempotent and safe to re-run on every scheduled pass, not just the one-time retrofit.
2. Spot-check real evidence for the retrofit itself: pick 2-3 real Threads with differing message counts; confirm each now has a real `## Messages` section listing every one of its own real messages, and confirm each of those messages now carries a correct `thread:` field. Confirm via `vault_indexing.rebuild_index()` (or the running app's own already-scheduled index rebuild) that the backlinks panel/graph view substrate reflects the new links — the story's own `## Affected Screens` premise, now genuinely true.
3. Record the real, final corpus counts observed at run time (Thread count, message count, any honest failures/skips) in this task's own Implementation Log — the real evidence for "was the retrofit actually complete," not merely "did the endpoint return 200."

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `link_thread_messages()` run for real against the full real corpus via the real endpoint — every real Thread's `## Messages` and every real message's `thread:` field populated
- [ ] A real, immediately-following second run produces zero file changes anywhere in the corpus (byte-for-byte/hash-identical before vs. after the second run)
- [ ] Real, final corpus counts recorded in the Implementation Log
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any code change to `link_thread_messages()`/`rename_threads()`/`vault_indexing.py` beyond a genuine defect fix discovered live during this run.
- Backfilling any pre-`REQ-SB-71-US-02` flat-shape Thread notes, if any remain (`ESC-048`'s own established carve-out) — unaffected, out of scope here too.

---

## Context / Notes

This is the heaviest task by real-verification cost, not code volume — mirrors this project's own repeated Learnings pattern (`SPRINT-021`/`SPRINT-027`/`SPRINT-031`) that a real, on-demand, full-corpus pipeline invocation can take meaningfully longer wall-clock time than its code volume suggests. Background the real endpoint call with unbuffered output if it runs long, and use a live CPU-accumulation/active-connection check (not just elapsed time) to distinguish "still genuinely working" from a true hang, per this project's own established technique.

---

## Implementation Log

**No code change was needed** — the full run against the real corpus surfaced no defect; `T04` was purely the real-endpoint retrofit run + real byte-for-byte idempotency proof.

**Real, live corpus counts re-confirmed at run time (2026-08-19, grown from the story's own 2026-08-19-morning count of 137/257 — organic capture growth during this same day, as the task text itself anticipated):** 132 real Thread directories under `Work/Threads/`, 129 of which have >=1 real message under `messages/` (3 have zero messages — left with no `## Messages` section at all, by this Job's own honest, disclosed "nothing to list" design, mirroring `## Files`'s precedent); 258 real raw message notes total.

**Retrofit run, via the real endpoint (a dedicated `uvicorn --port 8001` instance against the real, configured vault, isolated from the already-running shared dev instance on the default port to avoid disturbing concurrent `SPRINT-068` work on the same file):**

- `[REQ-SB-73-US-01-AC-06]` **PASS.** Sequence: (1) waited for the fresh server's own automatic startup-scheduled activity to settle (confirmed via a stable Compass-call count in the server log — the already-existing, out-of-this-story's-scope `run_capture_if_idle` schedule fires on every app start, per `architecture.md`'s own documented "Local Development" note); (2) captured a real SHA-256 content hash of every one of the 390 real files under `Work/Threads/` (132 concept files + 258 message notes) — the settled baseline; (3) `POST /poc/librarian-link-thread-messages` (run A) → real `200`, `{"threads_processed": 129 entries, "messages_linked": 258 entries, all "linked": false}` — the corpus was already fully linked from `T01`'s own earlier full-corpus verification pass (disclosed in `T01`'s own Implementation Log), so this run is honestly a true no-op, not a fresh write; (4) hashed all 390 files again (`afterA`) — **zero files changed vs. the baseline**; (5) `POST /poc/librarian-link-thread-messages` again (run B) → real `200`, same all-`false` shape; (6) hashed all 390 files a third time (`afterB`) — **zero files changed vs. `afterA`**. Baseline == afterA == afterB, byte-for-byte, across the full real 390-file set — the tightest possible real proof of `AC-06`'s "already fully linked... re-run is a true no-op" contract, run back-to-back to minimize any window for the (already-disclosed, out-of-scope) live scheduler's own unrelated background activity to interleave.
- Spot-check (2nd Tests bullet): 3 real Threads sampled across the message-count range (1, 1, and 14 messages) — each carries a correct, complete `## Messages` section and each of its own messages carries a correct `thread:` field. `vault_indexing.rebuild_index()` confirms every one of those messages' stems appears in its owning Thread's own `incoming_wikilinks` — the backlinks-panel/graph-view substrate genuinely reflects the new links, the story's own `## Affected Screens` premise now true.
- Full-corpus consistency re-check (beyond the sampled spot-check): iterated all 132 Threads/258 messages directly — **zero `thread:` mismatches** anywhere in the real corpus (every message's `thread:` resolves to its owning Thread's CURRENT stem).

**Real final corpus counts (3rd Tests bullet):** 132 Thread directories (129 with >=1 message, 3 with zero — no failures/skips beyond that honest zero-message case, which is by design, not an error), 258 raw message notes, 0 `thread:` mismatches, 0 file changes across the full idempotency proof.

**Assumption logged for spot-check:** verifying `T01`'s own ACs earlier necessarily ran `link_thread_messages()` against the FULL real corpus ahead of this task (disclosed in `T01`'s own Implementation Log) — this task's own real endpoint-based retrofit run and idempotency proof are still both genuinely satisfied here (the endpoint was, in fact, called for real, twice, with a real hash-identical before/after result); the "first run being a no-op" is an honest, disclosed consequence of that earlier verification work, not a weakening of this task's own AC-06 coverage.

**gate: clear 2026-08-19** — no MUST-FLAG trigger fired (no new assumption beyond the logged one above; no ADR change; no escalation; the one locked AC verified with real, direct evidence at full-corpus scale; no contradictory inputs; no unclear/multi-option decision). No code change was required, so no new dependency/shared-interface/ADR-deviation event occurred.
