---
id: REQ-SB-95-US-05-T04
title: The scoped entity read — hub synthesis first, then tagged evidence newest first, nothing outside the tag
parent_story: REQ-SB-95-US-05
requirement_id: REQ-SB-95
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-95-US-05-T01, REQ-SB-95-US-05-T03]
created: 2026-10-16
updated: 2026-10-16
---

# REQ-SB-95-US-05-T04 — The Scoped Entity Read

## Parent Story

- Story: [[REQ-SB-95-US-05]] — `../UserStories/REQ-SB-95-US-05-entity-resolution-tag-keyed-index.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Answer "what is known about this entity" from the entity's own scope: its hub
synthesis first, then its tagged evidence newest first — reading nothing
outside its tag and running no whole-vault search.

---

## Starting State → End State

**Before / Inputs:**

- `T03` resolves a name to `(kind, tag, hub)`; `T01`'s projection says which
  notes carry that tag.
- **Recency fields are real and already known** — do not invent one.
  `business/logic/capture_freshness.py` (read it) records the live convention:
  a `Meeting` is dated by `start`, a `RawMessage` by `received`; a `Thread`
  carries `last_message_at`, kept current by the email-capture pipeline. Its
  `_parsed()` also handles both real stamp formats written into this vault
  (`2026-10-09 17:11:47.410000+00:00` with a space, and ISO), treating a naive
  stamp as UTC.
- `vault_manager.get_entries()` is the iteration surface; `get_index()` loses
  collisions (`BUG-076`).
- `app/business/core/vault/note_text.py` and the existing note-reading paths
  are how note bodies/sections are already read.

**After / Outputs:**

- A scoped-read function (in `tag_resolution.py` or a sibling business module —
  state which and why in the log) taking a resolved entity and returning:
  1. the **hub note's synthesis first** — the hub named by the resolved entry;
  2. then its **tagged evidence**, newest first by each note kind's own real
     recency field, with a stated, documented fallback for a note whose field
     is missing or unparseable (never a silent "treat as newest").
- Every returned item carries the entity's tag. Nothing outside the tag scope
  is read or returned.
- The vault is reached **only** through the tag-keyed projection; the search
  entry point is never called.
- An entity whose hub note does not exist, or which has no tagged evidence,
  returns that honestly rather than widening the scope.

---

## Files to Modify

- `src/backend/app/business/logic/tag_resolution.py` (or a sibling business
  module — one choice, logged)
- `src/backend/tests/test_scoped_entity_read.py` (new)

---

## Constraints

- Inherits from parent story.
- **Scoped reads only.** Widening to the whole vault is the exact failure this
  story exists to remove — not a fallback, not for an empty result.
- **Synthesis before evidence, newest first** is part of the requirement, not
  an implementation preference.
- Iterate `get_entries()`, never the by-stem map.
- No plugin named; `kind` stays opaque.
- Read-only: this task writes nothing to the vault.

---

## Tests

**Automated tests** — `src/backend/tests/test_scoped_entity_read.py`, run with
`pytest tests/test_scoped_entity_read.py` from `src/backend`; build the tmp
vault the way `tests/test_capture_freshness.py` seeds real-shaped frontmatter.

1. `[REQ-SB-95-US-05-AC-02]` Build a tmp vault with one hub note and several
   tagged Threads and Meetings for the same entity, plus notes for a different
   entity and untagged notes; perform the scoped read and assert the hub's
   synthesis is first and every subsequent item is tagged evidence.
2. `[REQ-SB-95-US-05-AC-02]` Assert the evidence order is strictly newest
   first, using a Thread's `last_message_at` and a Meeting's `start` with
   deliberately interleaved dates (including one stamp in the space-separated
   format and one ISO, so `_parsed`-style handling is genuinely exercised).
3. `[REQ-SB-95-US-05-AC-02]` Assert **every** returned item carries the
   entity's tag, and that no note belonging to the other entity, and no
   untagged note, appears anywhere in the result.
4. `[REQ-SB-95-US-05-AC-02]` Spy the vault search entry point across the whole
   read and assert **zero** calls — including for an entity with no evidence at
   all, where the honest empty result must not fall back to a search.
5. `[REQ-SB-95-US-05-AC-02]` Assert a note whose recency field is missing or
   unparseable is placed by the documented fallback rule (assert the rule, not
   an accident of list order) and is still inside the tag scope.

**Manual verification steps:**

1. `[REQ-SB-95-US-05-AC-02]` Against the real vault with a real registered
   namespace (or a throwaway local plugin registering one), perform a scoped
   read for a real entity that genuinely has a hub note and tagged evidence;
   confirm the hub content comes first, the evidence is in newest-first order
   against the real notes, and nothing outside the tag appears. Record the
   first five items verbatim in the Implementation Log. If the real vault has
   no registered namespace yet, say so and verify against a tmp vault instead —
   do not report a fabricated positive (this project's own standing rule).

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Hub synthesis first, then tagged evidence newest first
- [ ] Recency taken from each kind's real field, with a documented fallback
- [ ] Everything returned is inside the tag scope; nothing outside is read
- [ ] No whole-vault search on any path, including the empty case
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Replacing general vault search for non-entity questions — it stays as it is.
- Exposing this as a catalogued Action — `T05`.
- Any screen.

---

## Context / Notes

`architecture.md` → **§The One Tag-Keyed Index — a Projection, Not an
Artifact** (its scoped-read bullet) and `REQ-SB-54-US-01`'s knowledge model
(synthesis in hubs, evidence in tagged Threads/Meetings) are the authorities.
`ADR-032`'s own freshness consequence applies: the answer is exactly as fresh
as the vault index, and the freshness *surface* is deliberately `BUG-085`'s,
not this task's.

---

## Implementation Log

_(Filled in by the coder.)_
