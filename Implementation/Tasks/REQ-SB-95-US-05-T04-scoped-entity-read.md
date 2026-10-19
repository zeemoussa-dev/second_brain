---
id: REQ-SB-95-US-05-T04
title: The scoped entity read — hub synthesis first, then tagged evidence newest first, nothing outside the tag
parent_story: REQ-SB-95-US-05
requirement_id: REQ-SB-95
type: backend
status: Done
gate: flagged
gate_reason: "trigger-6 (coder, 2026-10-19) — four scope-internal judgement calls for a human skim, none of them blocking and none an escalation: (1) the manual step's real-vault half was NOT performed and is disclosed rather than fabricated — no plugin anywhere in this checkout calls `register_tag_namespace`, so no install has a registered namespace, and the only way to create one would have been to install a throwaway plugin into the operator's live App Database Folder and read their real notes; verified instead against a synthetic vault through the real plugin/resolver/index seam; (2) the structural choice the task delegated — a sibling module `business/logic/scoped_entity_read.py` rather than more functions in `tag_resolution.py`; (3) a documented private import of `capture_freshness._parsed`, taken because the alternative was a second parser for this vault's stamp formats or an edit to a file outside `## Files to Modify`; (4) a default evidence cap with the real total always reported beside it. Plus: a new framework constraint was produced and could NOT be recorded — `MEMORY.md` is 86 KB against the 40 KB budget its own rule 1 sets, which forbids appending while over; the rule is written out in `REVIEW-QUEUE.md` instead."
phase: P2
depends_on: [REQ-SB-95-US-05-T01, REQ-SB-95-US-05-T03]
created: 2026-10-16
updated: 2026-10-19
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

- [x] Hub synthesis first, then tagged evidence newest first
- [x] Recency taken from each kind's real field, with a documented fallback
- [x] Everything returned is inside the tag scope; nothing outside is read
- [x] No whole-vault search on any path, including the empty case
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
      — **it did, and it could not be written.** `MEMORY.md` is 86 KB against the
      40 KB budget its own rule 1 sets, and that rule forbids appending while over.
      The rule is written out in full in the `REVIEW-QUEUE.md` entry for this task
      instead, for the human to place once the file is trimmed.
- [x] `CHANGELOG.md` entry appended

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

**Coder, 2026-10-19 — `Ready → Done`. `AC-02` verified. The story and
`SPRINT-090` stay `In Progress`: `T05` remains.**

### Baseline and final suite numbers

Measured before the first edit and again after, from a scratch CWD with
`VAULT_PATH` / `SECOND_BRAIN_DATA_PATH` / `HERMES_HOME_PATH` pointed at scratch
paths **before** anything imported `app.config`, so the operator's vault, store
and Hermes install were unreachable for the whole task (`tests/conftest.py`
sandboxes Hermes only, which was re-confirmed, not assumed).

| | Passed | Non-passing |
|---|---|---|
| Baseline, before any edit | **742** | 9 |
| Final | **757** | 9 |

The non-passing set is **identical** before and after, compared id by id, not by
count: `test_blueprint_install.py::test_a_failure_past_the_preconditions_rolls_back`,
`test_blueprints_api.py::test_preflight_creates_nothing_and_reports_peers`, three
in `test_skill_writes_declaration.py`, `test_vault_engine_is_single.py::test_a_real_shipped_template_loads`,
three in `test_versioning.py` — all nine are the known pre-existing failures of a
genuinely empty scratch data store with no seeded Templates. None of the four
known order-dependent tests appeared in either run.

One note for whoever measures next: a scratch CWD alone gives **98** failures, not
9, and that is an artefact of the measurement rather than a regression. Running
outside `src/backend` means no `.env` is found at all, so the five
`REQUIRED_FOR_STARTUP` settings are empty, `setup_required` is true and every
route answers `503`. Supplying synthetic non-path values for
`COMPASS_BASE_URL`/`COMPASS_API_KEY`/`COMPASS_MODEL`/`SELF_EMAIL` as environment
variables (which outrank `.env` in pydantic-settings) keeps the app out of setup
mode while the paths stay at scratch — that is the configuration both numbers
above were taken under, and it reproduces `T03`'s own 742.

### AC-02 — observed outcome, step by step

`[REQ-SB-95-US-05-AC-02]` is the only locked AC on this task, and all five
automated steps plus the manual step are below with what was actually observed.
15 AC-tagged tests in `src/backend/tests/test_scoped_entity_read.py`, all
passing.

1. **Hub synthesis first, every subsequent item tagged evidence — PASS.** A tmp
   vault with one hub note, two Threads and two Meetings for the entity, plus a
   second entity's hub and Thread, an untagged Thread and a note whose only tag
   has no namespace. `result.notes[0].role == "synthesis"`, its body really
   carries the hub's synthesis text, and the four items after it are all
   `"evidence"`.
2. **Strictly newest first, both kinds, both real stamp formats — PASS.** The
   four dated notes return `d-newest, c-second, b-third, a-oldest` — Meeting,
   Thread, Meeting, Thread — so kind order and date order disagree and only the
   dates can explain the result. Each item's `recency_field` is asserted to be
   its own kind's real one (`start` / `last_message_at`), and the two stamp
   formats are split across both kinds, so a reader that understood only ISO
   would order this wrongly rather than fail visibly. `recency_epoch` is
   asserted monotonically decreasing, not just the stem list.
3. **Everything inside the tag, nothing outside — PASS.** Every returned item
   carries `glyph/lumen-cartography`; the returned stems are asserted disjoint
   from the other entity's hub and Thread, the untagged Thread and the
   no-namespace note — and those four are separately asserted to really be in
   the index, so the fixture cannot pass by being empty. Two further tests
   harden it: one arms **both** `get_entries()` and `get_index()` to fail after
   the index is built and the read still succeeds (proving the projection is the
   only door), and one puts two tagged notes with the **same filename** in the
   vault and asserts both come back — the by-stem map would have dropped one
   (`BUG-076`).
4. **Zero search calls, including the empty entity — PASS.** All three vault
   search entry points (`VaultManager.search`, `hybrid_search.search`,
   `SemanticManager.search`) are replaced with counters for every test in the
   file, and the fixture's teardown asserts all three are zero for **every**
   test, not just this one. The dedicated test reads the counters explicitly
   after a populated read and again after a read for a tag no note in the vault
   carries: `{"keyword": 0, "hybrid": 0, "semantic": 0}` both times. The empty
   read comes back `performed=True`, `found_anything=False`, with the message
   *"no note in the vault carries glyph/nobody-has-written-about-this, and
   nothing else was searched"*. Two sibling tests cover the other two tempting
   paths: a name that did not resolve (`performed=False`, nothing searched) and
   a tag-keyed index that raises on read (`performed=False`, the failure named,
   nothing searched — a failed read may not borrow the look of an empty one).
5. **The fallback rule, asserted as a rule — PASS.** Three ways to be undated
   are present at once: a Thread with no `last_message_at`, a Thread whose
   `last_message_at` is `"last Tuesday"`, and a tagged note of a type with no
   known recency field at all. The test asserts the **relation** over
   `evidence_sort_key` — for every (undated, dated) pair, `key(undated) >
   key(dated)` — so no dated note, however old, can sort below an undated one by
   construction rather than by where this vault happened to put them. It also
   asserts each note's own `undated_because` sentence, that `recency_at` and
   `recency_epoch` are both `None`, and that all three are still inside the tag
   scope with their bodies read. A second test indexes the **same vault in the
   reversed walk order** and asserts a byte-identical answer, which is what
   separates the rule from an accident of list order.

**The tests were proved to bite, by four in-memory mutations** (no repo file was
mutated — each is a scratch pytest plugin that rebinds one attribute at
`pytest_configure`): neutralising `evidence_sort_key` fails 8 of 15; making an
empty result fall back to `VaultManager().search` fails exactly the three
no-search tests; widening `get_entries_for_tag` to the whole vault fails 12 of
15; and never promoting the hub to synthesis fails 10 of 15. A green suite that
stays green under all four would not have been evidence of anything.

**Manual step 1 — performed against a synthetic vault; the real-vault half was
NOT performed, and this is a disclosed gap rather than a positive.** The step
asks for a real-vault read "with a real registered namespace (or a throwaway
local plugin registering one)". Neither is available honestly:
`register_tag_namespace` is called by **nothing** in this checkout outside
`plugin_api.py` and three test files — no plugin, no Marketplace package — so no
install has a registered namespace, which is the exact condition the task file
anticipated. Creating one would have meant installing a throwaway plugin into
the operator's live App Database Folder and reading their real notes, which this
project's standing rule forbids outright, including from a probe. So the step
was run the way the task file itself prescribes for this case, on a synthetic
vault — and everything except the vault's contents is real: a real plugin
installed into a scratch App Database Folder with a real `installed.json`, the
real `PluginManager.load_all()`, the real vault walk and `rebuild_index()`, the
real `tag_resolution.resolve()` and the real scoped read.

Observed: `registered namespaces: ['glyph']`, 10 notes indexed, tag keys
`['glyph/lumen-cartography', 'glyph/tessellate-works']`. Asked by the **alias**
`"LC"`. **The first five items, verbatim:**

```
message: "LC" read from glyph/lumen-cartography alone: its hub synthesis comes
         first; 6 tagged evidence note(s), newest first
performed: True | tag: glyph/lumen-cartography | kind: Counterparty
hub_status: found | evidence_total: 6

  1. role=synthesis stem='Lumen Cartography' type='Glyph'
     title='Lumen Cartography'
     tags=['glyph/lumen-cartography']
     recency_field=None recency='undated' recency_at=None
     undated_because="no recency field is known for a note of type 'Glyph', and this read invents none"
     body='\n## Synthesis\n\nRenewal is in motion; two open questions on scope.\n'
  2. role=evidence stem='2026-10-13-review' type='Meeting'
     title='Quarterly review'
     tags=['glyph/lumen-cartography']
     recency_field='start' recency='dated' recency_at='2026-10-13T06:00:00+00:00'
     undated_because=None
     body='\nagenda and notes\n'
  3. role=evidence stem='m1' type='RawMessage'
     title='RE: Renewal terms'
     tags=['glyph/lumen-cartography']
     recency_field='received' recency='dated' recency_at='2026-10-11T09:30:11.120000+00:00'
     undated_because=None
     body='Happy to proceed.'
  4. role=evidence stem='renewal' type='Thread'
     title='Renewal terms'
     tags=['glyph/lumen-cartography']
     recency_field='last_message_at' recency='dated' recency_at='2026-10-11T09:30:00+00:00'
     undated_because=None
     body='\nthread summary\n'
  5. role=evidence stem='2026-10-09-kickoff' type='Meeting'
     title='Kickoff'
     tags=['glyph/lumen-cartography']
     recency_field='start' recency='dated' recency_at='2026-10-09T17:11:47+00:00'
     undated_because=None
     body='\nagenda\n'

every returned item carries glyph/lumen-cartography : True
any note of the other entity or untagged present: False
full order: [('synthesis', 'Lumen Cartography'), ('evidence', '2026-10-13-review'),
             ('evidence', 'm1'), ('evidence', 'renewal'),
             ('evidence', '2026-10-09-kickoff'), ('evidence', 'invoice'),
             ('evidence', 'no-stamp')]

a name the registry does not know: False | no scoped read was performed for
"Tessellate Works": it did not resolve to an entity, and nothing was searched
for in its place -- "Tessellate Works" did not resolve: no registered tag
namespace knows that name, alias or domain
```

Three things in that output are worth reading twice. The synthesis leads even
though it is the only **undated** note in the whole set — order by role first,
date second, exactly as the AC words it. Item 3 is a `RawMessage` whose body on
disk is `<html><body><p>Happy to proceed.</p></body></html>` and comes back as
prose, because the read converts on the way out like every other note view
(`BUG-081`). And the untagged Thread stamped **newer than everything here**
(`2026-10-18`) does not appear anywhere, which is the single clearest sign the
read is scoped rather than ranked.

### The structural choice the task delegated

**A sibling module: `src/backend/app/business/logic/scoped_entity_read.py`, not
more functions inside `tag_resolution.py`.**

`T03`'s module earns its central claim mechanically rather than by assertion:
its own test file arms `VaultManager.search`, `hybrid_search.search` **and**
`get_entries_for_tag` to fail every test in it, which is what makes "resolution
is a registry lookup, never a fuzzy search over note titles, and it reads no
note" a property of the code instead of a sentence in a docstring. A note reader
living in that file would delete that tripwire on the day it was added, and the
only proof of the property with it. Two modules keep both claims separately
checkable — resolution answers *which tag*, this answers *what the tag holds* —
and each file's whole-file tripwires stay honest. It is also where `CLAUDE.md`'s
own module layout puts it: `business/logic/` is cross-entity composition, and
this composes the resolver, `T01`'s projection and the note reader. `T03`'s
deliberate design — handing back the hub and the evidence *scope* and no notes
at all — is left exactly as it is and is in fact what this module consumes.

### The fallback rule, as written down

Stated once in the module docstring, repeated at the `UNDATED_EVIDENCE_RULE`
constant, and implemented in exactly one place (`evidence_sort_key`):

> A note whose recency field is missing, empty or unparseable — or whose note
> type has no known recency field at all — is **undated**, and every undated
> note sorts **after every dated note**, however old the dated one is. Undated
> notes are ordered among themselves by stem and then path, case-insensitively,
> so the order is a rule rather than whatever order the vault walk produced.

Last, never first, and never a silent "treat as newest": the read's one promise
is *newest first*, and a note that cannot be dated cannot be claimed to be the
newest without making that promise false in the one place a reader checks it.
Sorting it to the bottom makes a missing stamp visible as a degradation instead
of letting it impersonate today's news. The note is still returned — being
undated is not grounds to drop a note that carries the entity's tag.

### Assumptions and judgement calls (scope-internal — this is why `gate: flagged`)

1. **The manual step's real-vault half was not performed.** Disclosed above and
   in `REVIEW-QUEUE.md`. A disclosed gap, not a fabricated positive.
2. **`capture_freshness._parsed` is imported, not copied.** It is private at its
   own module, and this task may not rename it — `capture_freshness.py` is not
   in `## Files to Modify`, and asking for it would have been an escalation over
   a name. The two alternatives were worse: a second parser for "what a stamp in
   this vault looks like" is how one of them ends up not understanding the
   space-separated form capture really writes, and the task's own brief says
   that file is the live record of the convention. The import carries a comment
   saying so at both ends of the reasoning.
3. **The hub is matched INSIDE the tag scope**, against the notes carrying the
   entity's tag, rather than fetched from the vault by name. This is what makes
   "every note in the result carries that entity's tag" true by construction.
   The consequence is deliberate and is the half worth a human eye: a hub note
   that does not carry its own entity tag is reported `not_found_in_scope`
   rather than read, because reading it would mean reading outside the scope,
   which the AC forbids in those words. An untagged hub is a real vault defect
   and this surfaces it; if the operator would rather the hub be fetched by name
   regardless, that is a one-line change and a different AC.
4. **A default evidence cap of 20, with the real total always reported.** One
   entity on this install can carry thousands of message notes, and a read that
   materialised every body would be unusable. What keeps a cap from being a
   quiet lie is that `evidence_total` always reports how many tagged notes there
   really are and `evidence_truncated` says the list was cut; the message says
   "2 of 4", not "2". The cap is a parameter, and a negative value means no cap.
5. **A future-dated note is kept**, which is a deliberate divergence from
   `capture_freshness`, and is commented as such at the point of difference.
   That module drops future stamps because its question is "when did something
   last land" and next week's meeting would mask a capture that stopped. The
   question here is "what is known about this entity", and next week's meeting
   is legitimately the newest thing known. There is a test for it.
6. **`read_entity_named(name)` is included** alongside
   `read_scoped_entity(resolution)`, which the task specified. It is three lines
   — resolve, then read — and it exists so the "did not resolve ⇒ perform no
   read, and above all do not search instead" guard lives in one place rather
   than in every caller. `T05` is the first caller and would otherwise have had
   to re-implement exactly the rule this story exists to enforce.

### What was deliberately not touched

Nothing outside `## Files to Modify`. No route, no router registration, no
`plugin_api.py`, no `FRAMEWORK_API` move (`T02`'s `ESC-079` is untouched and
unaffected — the version gate governs only whether a *plugin* may declare the
capability, and nothing here is a plugin). Nothing imports this module yet,
which is correct: `T05` is its first caller and is the task that makes it
reachable. Per `.claude/agents/decomposer.md`'s switch-on-site rule, that was
checked rather than assumed — this task adds no validation, widens no shared
union, and joins no family of sibling modules, so none of the six variants
applies and no file outside the list is required to make the code run.

### One new framework constraint, which could not be recorded

A rule came out of this task that belongs in framework memory and **was not
written**, because `MEMORY.md` is 86 KB against the 40 KB budget its own rule 1
sets, and that rule forbids appending while over. It is written out in full in
the `REVIEW-QUEUE.md` entry for this task so it is not lost. In short: *a scoped
read addresses every note by its own `path` and never by its stem, because the
by-stem map can hand back a different note sharing a filename (`BUG-076`) —
which, in a reader whose contract is "nothing outside the scope", is the one way
to break that contract without ever calling a search.* This is the tenth task in
four days whose constraint has been diverted this way.
