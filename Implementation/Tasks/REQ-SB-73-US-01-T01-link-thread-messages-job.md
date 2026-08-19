---
id: REQ-SB-73-US-01-T01
title: link_thread_messages() — new Librarian Job (## Messages + thread: backlink) + vault_indexing.py frontmatter-wikilink extension
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

# REQ-SB-73-US-01-T01 — `link_thread_messages()` — new Librarian Job + `vault_indexing.py` extension

## Parent Story

- Story: [[REQ-SB-73-US-01]] — `../UserStories/REQ-SB-73-US-01-bidirectional-thread-message-linking.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-73 *Bidirectional Thread ↔ Message Linking (Retrofit + Rename-Safe)*
- Architecture: `Implementation/Architecture/architecture.md` → "The Librarian — Bidirectional Thread ↔ Message Linking" (`ADR-054` Decisions 1, 3, 5)

---

## Objective

Add a new Job, `link_thread_messages()`, to `librarian_housekeeping.py` that regenerates every real Thread's own `## Messages` section from its current `messages/` glob and writes/self-heals every one of those messages' own `thread:` frontmatter backlink — and fix a genuinely independent, cross-cutting gap this story's correctness depends on: `vault_indexing.py::_build_entry` must also scan frontmatter string values for `[[...]]` targets, not body text alone, or the new `thread:` field stays invisible to the backlinks panel/graph view.

---

## Starting State → End State

**Before / Inputs:**
- `librarian_housekeeping.py` has `rename_threads`, `backfill_files`, `populate_thread_related_links`, `backfill_company_folders`, `ensure_librarian_agent_and_section`, `run_housekeeping_pass` — no `link_thread_messages`.
- No real Thread concept file has a `## Messages` section. No real `RawMessage` note has a `thread:` frontmatter field.
- `vault_writer.insert_body_section_if_missing(path, header) -> bool` and `vault_writer.replace_body_section(path, header, new_content, *, caller) -> bool` already exist (`REQ-SB-72-US-01-T04`) — the exact pair `backfill_files()` already uses for `## Files`.
- `vault_writer.upsert_frontmatter_key(path, key, value) -> bool` already exists (used live by `meeting_classification.py`'s own `thread:` field) — inserts if absent, overwrites in place if present with a different value, true no-op if the value already matches.
- `vault_writer.list_thread_notes() -> list[Path]` already exists — every real Thread's own current concept file path.
- `app/business/vault_indexing.py::_build_entry(path) -> dict` computes `"outgoing_wikilinks": vault_writer.extract_wikilink_targets(body)` — **body only**. No existing wikilink convention in this codebase lives in frontmatter, so this has never mattered until now.
- `app/data_access/section_ownership.py::_CALLER_ALLOW_LISTS` has no entry for a `## Messages` writer.

**After / Outputs:**
- New `link_thread_messages() -> dict` in `librarian_housekeeping.py`:
  - Iterates `vault_writer.list_thread_notes()`.
  - For each Thread, globs its own current `messages/*.md` (sorted by filename, mirroring every sibling Job's chronological-by-filename ordering).
  - Regenerates `## Messages` wholesale (never incrementally patched) as one `"- [[<message-stem>]]"` bullet per message, via `vault_writer.insert_body_section_if_missing(concept_path, "## Messages")` then `vault_writer.replace_body_section(concept_path, "## Messages", content, caller="librarian_housekeeping.link_thread_messages")` — mirrors `backfill_files()`'s own exact two-call sequence for `## Files`. A Thread with zero messages under `messages/` (should not occur in practice, but handle honestly) leaves `## Messages` untouched/absent rather than writing an empty section.
  - For every message under that same glob, calls `vault_writer.upsert_frontmatter_key(message_path, "thread", f"[[{concept_path.stem}]]")` — the Thread's own CURRENT stem. This one call satisfies write-new (a message with no `thread:` field yet gets one), self-heal (a message whose `thread:` points at a stale pre-rename slug gets corrected), and true-no-op-on-rerun (a message whose `thread:` already matches gets no write at all — `upsert_frontmatter_key` returns `False`, writes nothing).
  - Returns `{"threads_processed": [conversation_id, ...], "messages_linked": [{"conversation_id", "message_stem", "linked": bool}, ...]}` (or an equivalent honest, structured summary — exact key names are this task's own build-time judgement call, not asserted by the ADR).
- `section_ownership.py::_CALLER_ALLOW_LISTS` gains one new entry: `"librarian_housekeeping.link_thread_messages": frozenset({"## Messages"})`.
- `vault_indexing.py::_build_entry` is extended so `outgoing_wikilinks` is computed as `extract_wikilink_targets(body) + <targets found in any frontmatter string value or string-list element>`, reusing `vault_writer.extract_wikilink_targets` unchanged (already a pure regex match over any string, agnostic to origin) — strictly additive: a note with no wikilink-shaped frontmatter value contributes zero extra targets, byte-identical to today for every existing note.

---

## Files to Modify

- `src/backend/app/business/pipelines/librarian_housekeeping.py` — add `link_thread_messages()`.
- `src/backend/app/data_access/section_ownership.py` — add the new `_CALLER_ALLOW_LISTS` entry.
- `src/backend/app/business/vault_indexing.py` — extend `_build_entry`'s `outgoing_wikilinks` computation to also scan frontmatter.

---

## Constraints

- Inherits from parent story.
- `## Messages` is fully regenerated every pass, never incrementally patched — mirrors `## Files`'s own established contract.
- Do NOT write a new, dedicated `vault_writer.py` primitive for either the `## Messages` write or the `thread:` write — both are pure composition of `insert_body_section_if_missing`/`replace_body_section`/`upsert_frontmatter_key`, per `ADR-054`'s own explicit rejection of a dedicated primitive.
- Do NOT use `insert_frontmatter_key_if_missing` for the `thread:` write — it never touches an already-present key and cannot self-heal a stale post-rename value (Scenario 5 requires self-heal). `upsert_frontmatter_key` is the correct, load-bearing primitive.
- The `vault_indexing.py` fix must be a GENERIC frontmatter scan (any string/string-list value), never a `thread:`-named special case — per `ADR-054`'s own explicit rejection of a named-key special case.
- Must respect the `api → business → data_access` layer boundary (`ADR-003`).

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-73-US-01-AC-01]` Direct Python-shell check against the real vault: pick one real Thread directory with one or more real raw message notes under `messages/`. Call `librarian_housekeeping.link_thread_messages()`. Read the Thread's own concept file; confirm a `## Messages` section now lists one `- [[<message-stem>]]` bullet per real message currently under `messages/`, and confirm each bullet's target stem matches a real, existing message note's own filename stem (a real, resolvable wikilink).
2. `[REQ-SB-73-US-01-AC-02]` Re-run `link_thread_messages()` a second time over the SAME Thread after manually adding one more raw message note under its `messages/` directory (a disposable, hand-copied message note is fine). Confirm `## Messages` is fully rebuilt to include the new message alongside every prior one — never an incremental append (check there is exactly one `## Messages` header, not two, and the section's own content is the full current set, not the old set plus one line).
3. `[REQ-SB-73-US-01-AC-03]` Pick a real raw message note with no `thread:` field yet. After running `link_thread_messages()`, read its frontmatter; confirm it now carries `thread: "[[<owning-Thread's-current-stem>]]"`. Additionally, call `vault_indexing.rebuild_index()` and confirm this message's stem now appears in the owning Thread's own `incoming_wikilinks` list (or the Thread's stem appears in the message's own `outgoing_wikilinks`) — direct, real evidence the `vault_indexing.py` extension above closes the gap `ADR-054` names, not just that the frontmatter bytes look right.
4. `[REQ-SB-73-US-01-AC-05]` Hand-edit one real message note's `thread:` field to a deliberately wrong/stale value (e.g. `"[[some-other-thread-stem]]"`), then also test the "field absent entirely" case on a second message by deleting its `thread:` line. Run `link_thread_messages()` again; confirm both messages' `thread:` fields are corrected/written to the CURRENT owning Thread's real stem — self-healing, not merely "left as first-written."

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `link_thread_messages()` regenerates `## Messages` wholesale for every real Thread from its own current `messages/` glob
- [ ] Every message under that glob gets a correct `thread:` frontmatter backlink to its owning Thread's CURRENT stem — write-new, self-heal-stale, and true-no-op-on-already-correct, all from `upsert_frontmatter_key`
- [ ] `section_ownership.py` carries the new `librarian_housekeeping.link_thread_messages` → `{"## Messages"}` entry
- [ ] `vault_indexing.py::_build_entry` additionally scans frontmatter string/string-list values for `[[...]]` targets, strictly additive (zero behavior change for any note with no wikilink-shaped frontmatter value)
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The `rename_threads()` fan-out extension (the zero-staleness-window guarantee on rename) — `T02`.
- Wiring `link_thread_messages()` into `run_housekeeping_pass()`'s own Job chain and the new `/poc/librarian-link-thread-messages` endpoint — `T03`.
- The one-time retrofit run against the full real corpus + the full-corpus idempotency re-run (`AC-06`) — `T04`.

---

## Context / Notes

This task can be verified entirely via direct Python-shell calls against the real, configured vault — no HTTP endpoint exists yet (that's `T03`). This mirrors `REQ-SB-72-US-01`'s own established "function-level proof before HTTP-level proof" technique.

The `vault_indexing.py` extension is folded into this task rather than split into its own task (per the architect's own explicit either/or in `architecture.md`) — it is a small, additive helper with no independent Gherkin scenario of its own; this is the task where its correctness is actually exercised (Scenario 3's own "resolves to its owning Thread" requirement).

---

## Implementation Log

**Implemented (2026-08-19):** `link_thread_messages()` added to `librarian_housekeeping.py`, composing `list_thread_notes()` + `insert_body_section_if_missing`/`replace_body_section` (`## Messages`, wholesale regeneration, sorted-by-filename glob) + `upsert_frontmatter_key` (`thread:` write-new/self-heal/no-op) — zero new `vault_writer.py` primitives, per `ADR-054`. New `section_ownership.py` entry `librarian_housekeeping.link_thread_messages -> {"## Messages"}`. `vault_indexing.py::_build_entry` extended with a new `_frontmatter_wikilink_targets()` helper — generic scan of every frontmatter string/string-list value via the same `extract_wikilink_targets` primitive, additive to the existing body scan.

**Manual verification (direct Python-shell against the real, configured vault — no HTTP endpoint exists yet, per this task's own established technique):**

- `[REQ-SB-73-US-01-AC-01]` **PASS.** Ran `link_thread_messages()` against the full real corpus (129 Threads with >=1 message processed, 258 message-link operations). Picked `2026-07-28 Azerbaijan Engagement … Core42 Participation` (3 real messages under `messages/`): its concept file now carries `## Messages` with `- [[2026-07-28-889c5053]]`, `- [[2026-07-28-c524231c]]`, `- [[2026-07-28-dc8b2c18]]` — each bullet's target stem matches a real, existing message note filename stem.
- `[REQ-SB-73-US-01-AC-02]` **PASS.** Added one disposable hand-copied message note (`2026-07-28-testac02.md`) under the same Thread's `messages/`, re-ran `link_thread_messages()`. Confirmed exactly ONE `## Messages` header (regex count = 1, not 2) and its content was the full rebuilt 4-bullet set (3 prior + the new one), never an incremental append. Removed the disposable note and re-ran once more to restore the real 3-bullet state (confirmed byte-identical to the pre-test content).
- `[REQ-SB-73-US-01-AC-03]` **PASS.** Message `2026-07-28-889c5053.md` had no `thread:` field before the run; after running `link_thread_messages()` it carries `thread: "[[2026-07-28 Azerbaijan Engagement … Core42 Participation]]"`. Called `vault_indexing.rebuild_index()`: confirmed the Thread's own index entry's `incoming_wikilinks` includes the message's stem, AND the message's own `outgoing_wikilinks` includes the Thread's stem — direct, real evidence the `vault_indexing.py` frontmatter-scan extension closes the gap `ADR-054` names.
- `[REQ-SB-73-US-01-AC-05]` **PASS.** Hand-edited message `2026-07-28-889c5053.md`'s `thread:` to a deliberately stale value (`[[some-other-thread-stem]]`) and deleted message `2026-07-28-c524231c.md`'s `thread:` field entirely (absent case). Re-ran `link_thread_messages()`: both messages' `thread:` fields now correctly read the Thread's CURRENT stem — self-healing confirmed for both the stale-value case and the field-absent case.

**Side effect, disclosed (not a scope deviation):** verifying AC-01/02/03/05 against the real vault necessarily ran `link_thread_messages()` across the FULL real corpus (it has no per-Thread filter), so the real corpus is now substantially retrofitted ahead of `T04`. `T04` still performs the mandated real-endpoint run + real before/after hash-identical idempotency proof at full-corpus scale, per its own AC-06 — this pre-emptive run does not satisfy AC-06 itself (no endpoint existed yet, and no before/after hash comparison was captured here), so `T04` is not skipped or weakened.

**Assumption logged for spot-check:** the summary dict's exact key names (`threads_processed`, `messages_linked`, `linked`) were a build-time judgement call, as the task text itself flags as not asserted by the ADR — chosen to mirror `backfill_files()`'s own `{"companioned": ..., "threads_updated": ...}` shape (list-of-dicts with a boolean outcome flag) for consistency with sibling Jobs.

**gate: clear 2026-08-19** — no MUST-FLAG trigger fired (no new assumption beyond the logged build-time key-naming judgement call above; no ADR change; no escalation; every locked AC verified; no contradictory inputs; no unclear/multi-option decision).
