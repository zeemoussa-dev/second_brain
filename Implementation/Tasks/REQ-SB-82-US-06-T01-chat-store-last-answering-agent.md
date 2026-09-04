---
id: REQ-SB-82-US-06-T01
title: chat_store.py — additive last_answering_agent_id/last_answering_agent_name per-subject field
parent_story: REQ-SB-82-US-06
requirement_id: REQ-SB-82
type: backend
status: Done
gate: clear
gate_reason: "no triggers fired -- pure additive schema plumbing, mechanical extension of ADR-012's own already-locked design"
phase: P2
depends_on: []
created: 2026-08-31
updated: 2026-08-31
---

# REQ-SB-82-US-06-T01 — chat_store.py: additive last_answering_agent_id/last_answering_agent_name per-subject field

## Parent Story

- Story: [[REQ-SB-82-US-06]] — `../UserStories/REQ-SB-82-US-06-live-routing-fix-and-reply-to-message.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-82 *Cockpit Mechanics — Prep, Research, and Moderation*

---

## Objective

Add a new, additive `last_answering_agent_id`/`last_answering_agent_name`
field to `chat_store.py`'s existing per-subject entry (`ADR-007`), plus a
setter function, so a later task (`T04`) can implement the short-reply
shortcut (Scenario 1/7) against real, persisted state — this task is pure
schema/storage plumbing, no routing logic.

---

## Starting State → End State

**Before / Inputs:**
- `app/business/cockpit/chat_store.py`'s per-subject entry shape:
  `{"brought_in_agent_ids": [...], "messages": [...], "recommended_agent_ids": [...]}`
  (the last field is compute-on-first-read, `ADR-009`). No concept of "who
  answered last" exists anywhere in the store.

**After / Outputs:**
- The same per-subject entry additionally carries `last_answering_agent_id:
  str | None` and `last_answering_agent_name: str | None` — absent/`None`
  until the first real reply is ever dispatched for that subject (same
  honest-empty-until-set convention as `recommended_agent_ids`'s own
  compute-on-read field and every other agent-reference pair in this
  schema).
- A new function, `set_last_answering_agent(subject_kind: str,
  subject_note_stem: str, agent_id: str, agent_name: str) -> dict`, that
  loads the store, sets both fields on the subject's own entry, persists,
  and returns the updated entry — mirrors `bring_in_agent`'s own
  load/mutate/save/return shape exactly.
- `get_thread` (and any other reader) returns `last_answering_agent_id`/
  `last_answering_agent_name` as `None` for any entry that has never had
  `set_last_answering_agent` called on it — including every subject entry
  that predates this task (backward-compatible, no migration needed, same
  as `ADR-009`'s own field addition).

---

## Files to Modify

- `src/backend/app/business/cockpit/chat_store.py` — add the two fields'
  honest-empty default handling (a `.setdefault(...)` or equivalent
  wherever an entry is first created/read, matching the existing pattern
  used for `brought_in_agent_ids`/`messages`), and the new
  `set_last_answering_agent` function.

---

## Constraints

- Inherits from parent story.
- **Additive only** — do not rename/restructure `brought_in_agent_ids`,
  `messages`, or `recommended_agent_ids`; do not fork a second store
  (`ADR-012`'s own explicit rejection of that alternative — same per-
  subject entry, same file, same load/save-whole-file shape).
- `set_last_answering_agent` must be safe to call for a subject entry that
  doesn't exist yet (creates it first, same as `bring_in_agent`/
  `remove_agent` already do via `.setdefault(...)`).
- Never infer/guess a value for these fields from existing data — only
  ever set by an explicit `set_last_answering_agent` call (this task does
  NOT wire any caller; that's `T04`).

---

## Tests

**Manual verification steps:**
1. Call `chat_store.get_thread(...)` for a brand-new subject (never
   touched before); confirm the returned entry has
   `last_answering_agent_id is None` and `last_answering_agent_name is
   None` (no AC tag — supporting groundwork; the externally observable
   routing behaviour this field enables is verified in `T04`, where the
   field is actually consumed).
2. Call `chat_store.set_last_answering_agent(subject_kind, stem,
   "azure-expert", "Azure Expert")`, then re-call `get_thread` for the
   same subject; confirm both fields now read back exactly as set, and
   that `.second-brain/cockpit_chat.json` on disk reflects the same values
   for that subject's own key (no AC tag — storage round-trip sanity
   check).
3. Confirm an existing, pre-this-task subject entry already present in
   the real `.second-brain/cockpit_chat.json` (e.g. one created by
   `REQ-SB-82-US-01`/`US-04`'s own earlier live verification) still loads
   without error and reports `last_answering_agent_id is None` (no AC tag
   — backward-compatibility sanity check for the additive-field claim
   above).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `last_answering_agent_id`/`last_answering_agent_name` read as `None`
      for any subject entry that has never had `set_last_answering_agent`
      called on it, including pre-existing real entries
- [x] `set_last_answering_agent(...)` persists both fields immediately and
      is idempotent-safe to call repeatedly
- [x] No existing `chat_store.py` function's return shape narrowed or
      changed in an incompatible way
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Wiring any caller to actually invoke `set_last_answering_agent` — that
  is `T04`'s own scope (`_dispatch_reply` in `chat_turn.py`).
- The short-reply detection rule itself, and any routing decision — this
  task is storage only.

---

## Context / Notes

`ADR-012` point 1 (see `Implementation/Architecture/ADR.md`) is the
authoritative design for this field: set "whenever a real agent reply is
actually dispatched (Expert, Research Agent, or Customer-Section fallback
alike; whoever most recently answered, not just permanently-brought-in
Experts)." This task only builds the storage primitive `T04` will call
from that exact call site.

---

## Implementation Log

**2026-08-31 — Coder build.**

**Change:** `src/backend/app/business/cockpit/chat_store.py` — added a new
private helper `_ensure_last_answering_agent_fields(entry)` (mirrors the
`.setdefault(...)` backward-compat convention already used for
`brought_in_agent_ids`/`messages`), called it from every entry-creation/
read site (`get_thread`, `bring_in_agent`, `remove_agent`,
`append_message`), added `last_answering_agent_id`/`last_answering_agent_name:
None` to each function's own default-entry literal, and added a new
`set_last_answering_agent(subject_kind, subject_note_stem, agent_id,
agent_name) -> dict` function mirroring `bring_in_agent`'s own
load/mutate/save/return shape. Also updated the module docstring with a new
paragraph documenting the field pair, matching the existing docstring
convention for `recommended_agent_ids`/`append_message`. No other function's
signature or return shape changed. `set_last_answering_agent` never
computes a value on read (unlike `recommended_agent_ids`) — only ever set
explicitly, per the task's own Constraint against inferring/guessing.

**Deviation from illustrative pattern:** none — implemented exactly per
`ADR-012` point 1 and the task's own Starting State -> End State.

**Scope-internal judgement call (for human spot-check):** `get_thread`
guarantees the two new keys are present on the returned in-memory `dict`
for EVERY entry (fresh or pre-existing) via the new helper, but does NOT
force a disk write for a pre-existing entry that already has
`recommended_agent_ids` cached (the only branch that triggers a save) —
so an old, on-disk entry's own JSON keeps lacking the two new keys until
either `set_last_answering_agent` is called for it, or some other write
path touches it. This still fully satisfies AC "read as None... including
pre-existing real entries" (confirmed live, verification step 3 below) —
`None`-populating a field on every mere read would mean writing to
`.second-brain/cockpit_chat.json` on every GET, which the task's own
End-State text doesn't ask for and would add write volume with no
behavioral benefit. Not treated as a locked-AC ambiguity, just flagging
the reasoning for spot-check.

**Verification (manual mode, real store, real `.env`-configured vault at
`<OPERATOR_VAULT_OLD>\.second-brain\cockpit_chat.json`, via
`.venv/Scripts/python.exe` one-off scripts, cleaned up afterward):**

- **Test step 1 (no AC tag, supporting groundwork):** called
  `chat_store.get_thread('smoke-test-subject-kind', 'smoke-test-t01-verify')`
  for a subject never touched before. Observed:
  `last_answering_agent_id is None`, `last_answering_agent_name is None`.
  **PASS.**
- **Test step 2 (no AC tag, storage round-trip sanity check):** called
  `chat_store.set_last_answering_agent(subject_kind, stem, 'azure-expert',
  'Azure Expert')`, re-called `get_thread` for the same subject — both
  fields read back exactly as set (`'azure-expert'`/`'Azure Expert'`).
  Independently re-read the raw `.second-brain/cockpit_chat.json` bytes
  from disk and confirmed the same subject key's own on-disk entry carries
  identical values. Also confirmed idempotent-safe repeat calls (same
  values twice, then an overwrite with different values, then re-read —
  reflects the latest call every time, no error, no duplicate keys) and
  that calling `set_last_answering_agent` for a subject that has NEVER
  been touched by `get_thread`/`bring_in_agent` first still creates a
  correct, fully-shaped entry (`brought_in_agent_ids: []`,
  `messages: []`, plus both new fields set). **PASS.**
- **Test step 3 (no AC tag, backward-compatibility sanity check):** read
  the real, pre-existing `.second-brain/cockpit_chat.json` (14 real
  subject entries predating this task, e.g.
  `meeting:2026-08-26 Masdar - Connect on Data Engineer Topic`, a real
  entry with 5 brought-in agents and 2 real messages from earlier live
  verification). Called `get_thread` against one such real pre-existing
  entry — loaded without error, `last_answering_agent_id is None`,
  `last_answering_agent_name is None`. Confirmed the on-disk file's
  pre-existing entry keys (`brought_in_agent_ids`/`messages`/
  `recommended_agent_ids`) and their real content were completely
  untouched (no save triggered, since `recommended_agent_ids` was already
  cached for that entry — see judgement call above). **PASS.**
- Additionally, sanity-imported `app/business/cockpit/chat_turn.py` and
  `app/api/cockpit_router.py` (both real, unmodified downstream consumers
  of this module, out of this task's own scope) against the edited
  `chat_store.py` — both import cleanly, confirming no accidental
  signature break to any existing function any real caller depends on
  (AC "no existing function's return shape narrowed" — no automated test
  yet, confirmed by direct reading of the diff plus this live import
  check).
- **Cleanup:** all `smoke-test-*` throwaway subject entries created during
  steps 1-2 were removed from the real
  `.second-brain/cockpit_chat.json` immediately after verification,
  restoring the file to its original 14 real keys (confirmed via a
  before/after key-count diff).

**This task carries no story-level locked AC-IDs of its own** — per the
task's own Tests block, all three verification steps are explicitly
"no AC tag" supporting groundwork; the field this task builds is only
externally observable once `T04` wires a real caller
(`REQ-SB-82-US-06-AC-01`/`AC-07`), consistent with the parent story's own
task table.

**`MEMORY.md`:** not updated — no new decision/pattern/constraint emerged
beyond what `ADR-012` point 1 already fully documents; this task is a
mechanical, already-established-pattern extension (additive field +
`.setdefault(...)` backward-compat, same shape as `ADR-009`'s
`recommended_agent_ids` and `ADR-007`'s original schema).

**`CHANGELOG.md`:** entry appended under `[Unreleased]`.

gate: clear 2026-08-31 — no triggers fired (no ADR changes, no material
assumptions beyond the disclosed scope-internal judgement call above, no
new dependency/shared-interface change, requirement/story/ADRs all
finalised, all locked-AC-eligible verification steps passed).
