---
id: REQ-SB-95-US-05-T03
title: The generic tag resolver — name/alias/domain to (kind, tag, hub), ambiguity and non-resolution reported
parent_story: REQ-SB-95-US-05
requirement_id: REQ-SB-95
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-95-US-05-T01, REQ-SB-95-US-05-T02]
created: 2026-10-16
updated: 2026-10-16
---

# REQ-SB-95-US-05-T03 — The Generic Tag Resolver

## Parent Story

- Story: [[REQ-SB-95-US-05]] — `../UserStories/REQ-SB-95-US-05-entity-resolution-tag-keyed-index.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Turn a name, an alias or an email domain into `(kind, tag, hub)` by asking the
registered namespaces at that moment — reporting ambiguity and non-resolution
honestly, and never guessing from note titles.

---

## Starting State → End State

**Before / Inputs:**

- `T01`'s tag-keyed projection (which tags exist, and which notes carry them).
- `T02`'s registered namespaces, each with its `entries()` callable and its
  owning plugin id.
- Nothing resolves a name to anything today; the only verb is search.

**After / Outputs:**

- `app/business/logic/tag_resolution.py` (name indicative) — generic over any
  `<namespace>/<slug>` tag, knowing nothing of Customers, Partners or Entities
  and naming **no** plugin.
- `resolve(name)` asks every registered namespace's `entries()` **at call
  time** and matches case-insensitively against each entry's `name`, its
  `aliases`, and its `domains` (a bare domain, and the domain part of an email
  address). On exactly one match it returns that entry's `kind` (opaque,
  pass-through), its `<namespace>/<slug>` tag and its `hub`.
- **Zero matches** → an explicit "did not resolve" result repeating the name as
  it was given. Not an exception, not an empty entity, not a fallback search.
- **Two or more matches** → an explicit "ambiguous" result naming every
  candidate. Never silently picked.
- **A callable that raises** → that namespace is skipped and logged; the
  remaining namespaces still answer, and if nothing else matches the result is
  "did not resolve", never a wrong answer.
- **Zero registered namespaces** → nothing resolves, honestly.
- An "unknown tags" report over `T01`'s projection: every tag key in the vault
  with no registered entry behind it, named rather than dropped.

---

## Files to Modify

- `src/backend/app/business/logic/tag_resolution.py` (new)
- `src/backend/tests/test_tag_resolution.py` (new)

---

## Constraints

- Inherits from parent story.
- **A registry lookup, never a fuzzy search over note titles.** If this module
  reaches into vault search, it is wrong.
- **Core names no plugin** and never enumerates `kind` (`ADR-022`, `ADR-035`,
  `ADR-037`).
- **Ask the callable at resolution time**, every time. Do not memoise entries
  across calls — the plugin's registry is edited while the app runs.
- Ambiguity is a first-class result, not a logged warning plus a guess.
- Degrade to nothing, never to a wrong answer (`ADR-035`).

---

## Tests

**Automated tests** — `src/backend/tests/test_tag_resolution.py`, run with
`pytest tests/test_tag_resolution.py` from `src/backend`. Register fake
namespaces the way `tests/test_plugin_host.py` builds fake plugins, over a tmp
vault built like `tests/test_vault_index_collisions.py`.

1. `[REQ-SB-95-US-05-AC-01]` Register a namespace whose `entries()` knows one
   entity; resolve its primary name and assert the result carries that
   entity's `kind`, its `<namespace>/<slug>` tag and its `hub`.
2. `[REQ-SB-95-US-05-AC-01]` Assert the `entries()` callable was invoked during
   the resolve call and that changing what it returns changes the next
   resolve's answer with no re-registration — i.e. it is asked at that moment,
   never read from a list captured earlier.
3. `[REQ-SB-95-US-05-AC-01]` Assert resolution never consults note titles:
   spy the vault search entry point and assert zero calls, and assert a name
   that matches a note title but no registered entry does **not** resolve.
4. `[REQ-SB-95-US-05-AC-01]` Supply a `kind` string the framework has never
   seen (e.g. `"Counterparty"`) and assert it is returned byte-identically,
   with no validation against any list.
5. `[REQ-SB-95-US-05-AC-03]` Resolve by an alias, and by an email domain, and
   by an address at that domain, each in mixed letter case; assert all three
   return the same kind, tag and hub as the primary name.
6. `[REQ-SB-95-US-05-AC-03]` Register two entries matching the same name (and,
   separately, the same domain); assert each resolve reports **ambiguous** and
   names both candidates, and never returns one of them.
7. `[REQ-SB-95-US-05-AC-05]` Resolve a name no namespace knows; assert the
   result says plainly that it did not resolve and repeats the name exactly as
   given, and that no scoped read and no search was performed.
8. `[REQ-SB-95-US-05-AC-05]` Resolve with **zero** namespaces registered;
   assert the same honest "did not resolve".
9. `[REQ-SB-95-US-05-AC-05]` Register two namespaces where one `entries()`
   raises; assert the raising one is skipped and logged (assert on the log
   record), the other still resolves its own names, and a name only the broken
   one knew returns "did not resolve" rather than anything else.
10. `[REQ-SB-95-US-05-AC-07]` With a tmp vault carrying tags from an
    unregistered namespace, assert the unknown-tag report names every such tag
    key and that none was dropped from the index.

**Manual verification steps:**

1. `[REQ-SB-95-US-05-AC-05]` With the backend running and no entities plugin
   installed, ask the resolver for a real entity name from the vault and
   confirm it answers "did not resolve" rather than returning search results —
   the CFO test, observed live.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `(kind, tag, hub)` from a name, an alias or a domain, case-insensitively
- [ ] `entries()` asked at resolution time, never captured
- [ ] Ambiguity reported naming both candidates, never silently resolved
- [ ] Non-resolution honest; raising callable skipped and logged
- [ ] Unknown tag keys reported, never dropped
- [ ] No plugin named; `kind` opaque; no title search anywhere
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Reading the entity's notes — `T04`.
- Exposing this as an Action — `T05`.
- Populating or curating any registry — that is the plugin's own work.

---

## Context / Notes

`architecture.md` → **§Entity Resolution — a Generic Tag Resolver, No Plugin
Named** and `ADR-037`'s "framework behaviour at the seam" bullet are
authoritative; each behaviour there is borrowed from an existing precedent
(`provide_service` for duplicate ownership, `register_agent_matcher` for a
raising callable), so read those before inventing a new shape.

---

## Implementation Log

_(Filled in by the coder.)_
