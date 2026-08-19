---
id: REQ-SB-73-US-01-T02
title: rename_threads() fan-out extension — zero-staleness-window thread: correction on every rename
parent_story: REQ-SB-73-US-01
requirement_id: REQ-SB-73
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-73-US-01-T02 — `rename_threads()` fan-out extension

## Parent Story

- Story: [[REQ-SB-73-US-01]] — `../UserStories/REQ-SB-73-US-01-bidirectional-thread-message-linking.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-73 *Bidirectional Thread ↔ Message Linking (Retrofit + Rename-Safe)*
- Architecture: `Implementation/Architecture/architecture.md` → "The Librarian — Bidirectional Thread ↔ Message Linking" → "`rename_threads()` fan-out extension" (`ADR-054` Decision 2)

---

## Objective

Extend the already-shipped `rename_threads()` Job (`REQ-SB-72-US-01-T03`, `ADR-049` Decision 2) so that, on every successful directory rename, every one of that Thread's own messages has its `thread:` field rewritten to the new slug in the SAME operation — a zero-staleness-window guarantee, not "eventually consistent via the next scheduled pass."

---

## Starting State → End State

**Before / Inputs:**
- `rename_threads()` (in `librarian_housekeeping.py`) renames a Thread's whole directory via `vault_writer.rename_thread_directory(directory, new_directory)` — confirmed by direct reading, it "touches nothing INSIDE `messages/`."
- `vault_writer.upsert_frontmatter_key(path, key, value) -> bool` already exists.

**After / Outputs:**
- `rename_threads()`'s per-Thread loop body is extended: immediately after a successful `new_concept_path = vault_writer.rename_thread_directory(directory, new_directory)` call (i.e. inside the `try` block, after the call succeeds, in the SAME loop iteration — never a separate pass, never deferred to `link_thread_messages()`'s own next scheduled run), globs the renamed Thread's own now-current `messages/*.md` and calls `vault_writer.upsert_frontmatter_key(message_path, "thread", f"[[{new_concept_path.stem}]]")` for each.
- `rename_threads()`'s own external contract (return shape, per-Thread `FileExistsError` collision handling, idempotent-skip-if-already-renamed) is otherwise UNCHANGED — this is a bounded addition, not a rewrite.

---

## Files to Modify

- `src/backend/app/business/pipelines/librarian_housekeeping.py` — extend `rename_threads()`.

---

## Constraints

- Inherits from parent story.
- The fan-out write happens ONLY after `rename_thread_directory` has already succeeded for that Thread — a genuine `<date> <subject>` collision (caught, skip-and-report) must never leave any message mid-way through a fan-out.
- No new `vault_writer.py` primitive — reuses `upsert_frontmatter_key` unchanged, the SAME primitive `T01`'s `link_thread_messages()` uses.
- `rename_threads()`'s own existing collision handling, idempotent-skip behavior, and return shape must stay byte-for-byte unchanged beyond the new fan-out side effect.
- Must respect the `api → business → data_access` layer boundary (`ADR-003`).

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-73-US-01-AC-04]` Direct Python-shell check against the real vault: pick a real, not-yet-renamed Thread whose `messages/` already carries one or more real raw message notes with a correct `thread:` field pointing at the Thread's own current (pre-rename) slug (use `T01`'s `link_thread_messages()` first if none yet have one). Call `librarian_housekeeping.rename_threads()`. Immediately after the SAME call returns, read every one of that Thread's own (now-renamed) messages' `thread:` field; confirm every one already points at the Thread's own NEW slug — no message is ever observed pointing at the stale, pre-rename slug, even momentarily, since the fan-out happens inside the same call that performs the rename.
2. Confirm `rename_threads()`'s own pre-existing behavior is unaffected: re-run against an already-renamed Thread and confirm it is still reported in `skipped_already_renamed`, not `renamed`, with no fan-out side effect attempted (nothing to fan out — the directory didn't move). Construct a genuine stem collision (or reuse one from the real corpus, if any remain from `REQ-SB-72-US-01-T03`'s own real collisions) and confirm it is still caught and reported in `collisions`, with none of that Thread's own messages' `thread:` fields touched.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] On a successful rename, every one of that Thread's own current messages has its `thread:` field rewritten to the new slug, in the SAME `rename_threads()` call
- [ ] A genuine stem collision leaves every one of that Thread's own messages' `thread:` fields untouched (rename itself never happened, so no fan-out is attempted)
- [ ] `rename_threads()`'s own pre-existing return shape, collision handling, and idempotent-skip behavior are unchanged
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- `link_thread_messages()` itself (the retrofit + ongoing self-healing Job) — `T01`.
- Wiring/endpoint changes — `T03`.
- The full-corpus retrofit run — `T04`.

---

## Context / Notes

Independent of `T01` — this task extends `rename_threads()`, a DIFFERENT function than `link_thread_messages()`, composing the same already-shipped `upsert_frontmatter_key` primitive `T01` also uses, but with no call into `T01`'s own new function. Both `T01` and `T02` may be built in either order; no `depends_on` edge exists between them.

---

## Implementation Log

**Implemented (2026-08-19):** `rename_threads()`'s per-Thread loop body extended: immediately after a successful `rename_thread_directory` call (inside the `try` block, same loop iteration), globs the renamed Thread's own now-current `messages/*.md` and calls `vault_writer.upsert_frontmatter_key(message_path, "thread", f"[[{new_concept_path.stem}]]")` for each — reuses the SAME primitive `T01` uses, no new `vault_writer.py` code. Positioned strictly after the `except FileExistsError` continue, so a genuine collision never reaches the fan-out block.

**Manual verification (direct Python-shell against the real, configured vault):**

- `[REQ-SB-73-US-01-AC-04]` **PASS.** Picked real, not-yet-renamed Thread `43E73DADE94C4B41B829E332C81CD2D2` (1 real message, `thread:` already correctly pointing at its own pre-rename slug via `T01`'s earlier corpus run). Called `rename_threads()`: it renamed to `2026-08-19 ADNOC Visit Details-SKEC 1 - ADNOC HQ`. Immediately after that SAME call returned, read the message's own (now-relocated) `thread:` field: `[[2026-08-19 ADNOC Visit Details-SKEC 1 - ADNOC HQ]]` — already the NEW slug, zero-staleness-window confirmed.
- Pre-existing behavior unaffected: re-ran `rename_threads()` — the just-renamed Thread was reported in `skipped_already_renamed`, not `renamed` (0 renames this pass), no fan-out re-attempted. This second real run also surfaced 5 genuine real `<date> <subject>` stem collisions already present in the live corpus (e.g. `5CCF9A061B967E4B9BF1F377BE53BF3B` vs. an already-renamed sibling Thread with the same computed stem) — all correctly caught and reported in `collisions`, none aborting the run. Confirmed directly: `5CCF9A061B967E4B9BF1F377BE53BF3B`'s own message `thread:` field is untouched (`[[5CCF9A061B967E4B9BF1F377BE53BF3B]]`, still its own pre-rename slug) and its directory is still hex-named — the rename never happened, so no fan-out was attempted, exactly as required.

**gate: clear 2026-08-19** — no MUST-FLAG trigger fired (no new assumption; no ADR change; no escalation; the one locked AC verified; the real, live collisions encountered are the exact class of event `rename_threads()`'s own pre-existing collision handling — unchanged by this task — was already built to handle, not a new/unclear situation).
