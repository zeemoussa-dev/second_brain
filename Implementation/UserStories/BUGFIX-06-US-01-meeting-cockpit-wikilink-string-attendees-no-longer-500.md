---
id: BUGFIX-06-US-01
title: Meeting Cockpit resolves plain wikilink-string attendees to real Person info instead of 500ing (BUG-027 fix)
requirement_ids: [BUG-027]
requirement_section: "BUGS.md → BUG-027"
status: Done
gate: clear
gate_reason: "Resolved directly, 2026-08-19: BUG-027's own root cause was independently re-confirmed by direct code reading (not just trusted from the bug's own note), and the fix direction is unambiguous -- it reuses an extraction pattern that already exists live in this codebase (vault_writer.py's own _WIKILINK_PATTERN regex, already used by upsert_attendee_links, plus vault_indexing.get_index()'s own stem-keyed lookup, the exact primitive resolve_people_chips already uses for the subject note itself) rather than inventing a new parser. No material assumption was needed to fill a gap, BUG-027 is a finalised ledger entry (not a Draft PRD requirement), no ADR is implicated (applying an already-established regex+index-lookup pattern to a second call site is not a new architectural decision), no ESCALATIONS.md entry was written, the story is small and single-file-scoped (not oversized), and there is exactly one workable interpretation once 'correctly displays real attendee info' (the task's own acceptance bar) is taken seriously -- a purely defensive per-item type check that skips or blanks a wikilink-string entry would avoid the crash but would NOT satisfy that bar, so it is not treated as an equally-valid alternative. See ## Notes for the full grounding."
sprint: "SPRINT-066"
created: 2026-08-19
updated: 2026-08-19
---

# BUGFIX-06-US-01 — Meeting Cockpit resolves plain wikilink-string attendees to real Person info instead of 500ing (BUG-027 fix)

## Story

**As a** Second Brain user opening a real Meeting in the Meeting Cockpit
**I want** the Cockpit to load and show my meeting's real attendees even
when that meeting's `attendees` frontmatter is a plain list of wikilink
strings (the shape Meeting Capture actually writes today) rather than a
list of dicts
**So that** I can see who was in the meeting and open their Person notes,
instead of the Cockpit hard-failing with a bare `500 Internal Server Error`

## Context

Triage batch: `BUG-027` only — logged `2026-08-19`, `Open` at triage time,
found incidentally during `SPRINT-064`'s own live verification, disclosed
via `REVIEW-QUEUE.md`, formally captured in `BUGS.md`.

### BUG-027 — `resolve_people_chips` 500s on a real Meeting note whose `attendees` frontmatter is a plain list of wikilink strings, not dicts (Logic, Minor)

- **Screen/route:** Meeting Cockpit — `GET /cockpit/meeting/<id>`.
- **Repro (`BUGS.md`'s own text):** open a real Meeting note whose
  `attendees` frontmatter is a plain list of wikilink strings (e.g.
  `["[[sandeep.penumadu@core42.ai]]", ...]`) in the Meeting Cockpit.
  Confirmed on 2 real meetings ("Alignment Mubadala-2026-08-17-a4737bc4",
  "PSS Team Weekly Meeting-2026-08-18-47a72b70").
- **Expected:** the Cockpit loads normally, showing the meeting's real
  attendees.
- **Actual:** `500 Internal Server Error`.

- **Root cause, re-confirmed this pass by direct code reading of the real,
  current source (not restated from the bug's own note alone):**
  - `app/business/cockpit/people.py::_coerce_people_list` only handles two
    shapes: a STRING `attendees` value (JSON-decoded) or an actual Python
    `list` (passed straight through, unexamined, as-is). It performs no
    per-item normalization at all.
  - `resolve_people_chips`'s own loop then runs `person.get("email", "")`
    on every item in that list unconditionally. When an item is a plain
    string (a wikilink like `"[[sandeep.penumadu@core42.ai]]"`, not a
    dict), this raises `AttributeError: 'str' object has no attribute
    'get'`, surfaced to the caller as a bare, unhandled `500`.
  - **This is confirmed to be the current, live write shape — not a stale,
    pre-redesign artifact.** Direct reading of `meeting_classification.py`
    (lines 452-466, the real, currently-running attendee-write path) shows
    every attendee reaching `people_extraction.ensure_person_note(...)`,
    then its returned Person-note-path `.stem` being collected into
    `person_stems`, and finally written to the Meeting note's own
    `attendees` frontmatter key as `[f"[[{stem}]]" for stem in
    person_stems]` — a plain list of wikilink STRINGS, by construction,
    every time a Meeting note's attendees are written today. There is no
    code path anywhere in this codebase that writes `attendees` as
    `list[dict]`. `_coerce_people_list`'s own docstring describes a
    `list[dict]` design intent (`ADR-036` point 7) that was never actually
    implemented this way for Meeting attendees — the real, shipped
    behaviour and the docstring's own claimed contract have diverged.
  - **Why the wikilink stem looks like an email address:**
    `vault_writer.person_note_dedup_key(name, email)` returns the
    lowercased email when one exists; `person_note_path` then slugifies
    that dedup_key into the Person note's own filename stem. For an
    email-resolvable attendee, the Person note's stem IS (a slugified
    form of) their email — matching the repro's own literal example
    verbatim.

- **The fix's real shape, grounded in an extraction pattern that already
  exists live in this codebase — not a new parser:**
  - `app/data_access/vault_writer.py` already defines `_WIKILINK_PATTERN =
    re.compile(r"\[\[([^\]]+)\]\]")` and already uses it
    (`upsert_attendee_links`, via `_WIKILINK_PATTERN.findall(...)`) to
    extract a wikilink's own stem from an `**Attendees:**` body line — the
    exact same "strip `[[...]]` down to a stem" operation this bug needs
    applied to the frontmatter list instead of a body line.
  - Once a wikilink string is stripped to its stem, that stem can be
    looked up directly via `vault_indexing.get_index().get(stem)` — the
    SAME stem-keyed index lookup `resolve_people_chips` already performs
    for the subject Meeting note itself (`entry =
    vault_indexing.get_index().get(subject_note_stem)`), just applied a
    second time, once per attendee stem. A found entry's own
    `frontmatter.get("name")`/`frontmatter.get("email")` are exactly the
    real name/email `create_person_note_baseline` wrote when that Person
    note was created (`app/data_access/vault_writer.py`,
    `create_person_note_baseline`) — real data, not fabricated.
  - **Correction to the bug's own `## Bug Details` note:** the note
    suggests reusing "the same extraction pattern `people_extraction.py`
    already uses elsewhere" — but direct reading of `people_extraction.py`
    in full finds no wikilink-stripping regex or pattern anywhere in that
    file. The actual reusable pattern (`_WIKILINK_PATTERN`) lives in
    `app/data_access/vault_writer.py` (data_access layer), not
    `people_extraction.py` (business layer). This is a factual correction,
    not a scope ambiguity — it does not change the fix direction, only
    where the reused regex actually lives; the architect/decomposer should
    confirm at `/plan-tasks` whether `cockpit/people.py` reuses
    `vault_writer`'s existing pattern directly, or a small business-layer
    helper is composed instead (`ADR-003` layering).
  - **A defensive per-item type check alone (the bug note's second
    suggested option) is explicitly NOT sufficient on its own** — it would
    stop the crash, but a wikilink-string attendee would then render with
    no real name/email at all, failing this story's own acceptance bar
    ("correctly displays real attendee info derived from those
    wikilinks"). The adopted direction normalizes to real Person-note data
    first; a defensive fallback (see Scenario below) is reserved only for
    the genuinely orphaned case — a wikilink stem with no matching vault
    entry at all.

- **Prototype parity — `html-prototype/meeting-cockpit.html` already
  designs both attendee-chip states this fix needs to reach, unchanged:**
  the RIGHT panel's own "Attendees" section (lines ~285-297) already shows
  a clickable `.tag-chip` (`<a class="btn tag-chip" href="note-detail.html">
  Alex Rivera</a>`) for an attendee with an existing Person note, and a
  plain, non-clickable `.tag-chip--static` pill (`Jordan Lee (no note
  yet)`) for one without. This fix makes the backend correctly reach BOTH
  of those already-approved states for a wikilink-string attendee — it
  does not design or add any new screen region. `resolve_people_chips`'s
  own existing return shape (`name`, `email`, `has_note`, `note_path`) is
  already exactly what those two chip states consume; only the crash
  standing in front of it is fixed.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then) by the analyst; the
decomposer locks and AC-IDs this at /plan-tasks. Per the triage-mode
contract: one scenario, one bug (BUG-027) -- the two facets below (a
resolvable wikilink, an orphaned one) are two aspects of the SAME
regression criterion, mirroring BUGFIX-05-US-01's/BUGFIX-03-US-01's own
"one scenario, several And clauses for one bug" precedent. -->

### Scenario 1: A real Meeting note with plain wikilink-string attendees loads without a 500, and a resolvable wikilink attendee renders as a chip carrying that Person note's real data

```gherkin
Given a real Meeting note whose `attendees` frontmatter is a plain list of
    wikilink strings (e.g. `["[[sandeep.penumadu@core42.ai]]",
    "[[some-other-stem]]"]`) -- the actual, real shape Meeting Capture
    writes today -- not a list of dicts
  And at least one of those wikilink stems resolves to a real, existing
    Person note already present in the vault
When the Meeting Cockpit is opened for that meeting
    (GET /cockpit/meeting/<meeting-note-stem>)
Then the request succeeds with 200, not a 500 Internal Server Error
  And the attendee whose wikilink resolves to a real Person note renders
    as a chip carrying that Person note's own real `name` and `email`
    frontmatter values -- derived from the wikilink via a vault lookup,
    never fabricated and never left blank
```
<!-- AC-ID: BUGFIX-06-US-01-AC-01 -->

### Scenario 2: A wikilink attendee with no matching Person note falls back to the existing "no note yet" chip, and the two already-working attendees/recipients shapes are unregressed

```gherkin
Given the same real Meeting note as Scenario 1, whose plain wikilink-string
    `attendees` list also contains at least one wikilink stem with no
    matching Person note anywhere in the vault
  And a real Meeting or Inbox subject note whose attendees/recipients
    frontmatter is already a JSON-encoded string of dicts, and another
    whose attendees/recipients field is empty or missing entirely -- the
    two shapes `_coerce_people_list` already handled before this fix
When the Meeting Cockpit is opened for that same meeting again, and for
    each of the other two subject notes
    (GET /cockpit/<meeting|email>/<subject-note-stem>)
Then the wikilink attendee with no matching Person note renders as the
    existing plain, non-clickable fallback chip (mirroring the
    already-designed "no note yet" state), and the request never crashes
  And the already-JSON-encoded and the empty/missing subject notes
    continue to resolve their people chips exactly as they did before
    this fix -- this fix adds a new supported shape, it does not change
    either of the two shapes `_coerce_people_list` already handled
```
<!-- AC-ID: BUGFIX-06-US-01-AC-02 -->

<!-- Decomposer pass, /plan-tasks step 2, 2026-08-19: split the analyst's
one scenario (one Given/When/Then with four And-clause facets) into two
locked-by-default ACs -- the "resolves + no 500" positive facet (AC-01)
and the "unresolved-stem fallback + two-existing-shapes regression" facet
(AC-02) -- mirroring BUGFIX-05-US-01's own "may split into two locked ACs
if that reads more verifiable" precedent. Wording tightened for
buildability only (explicit `GET /cockpit/meeting/<meeting-note-stem>`
route shape; "at least one" instead of "one... and one" so a real meeting
with only a resolvable OR only an unresolvable stem still satisfies its
own scenario); no requirement content added or removed. Both ACs locked
as authored -- no `locked: false` this pass. -->

## Affected Screens

- `html-prototype/meeting-cockpit.html` — no change. This story fixes the
  backend so the Attendees panel's own two already-approved chip states
  (clickable `.tag-chip` for a resolved Person note; non-clickable
  `.tag-chip--static` for an unresolved one) can be reached at all for a
  wikilink-string-shaped attendee, instead of the request 500ing before
  either state ever renders. No new/changed UI region.

## Dependencies

- **Blocked by:** none. `meeting_classification.py`'s current attendee
  write path (`REQ-SB-71-US-03`) and `resolve_people_chips`'s own read
  path (`REQ-SB-43-US-01`/`ADR-036` point 7) are both already `Done` and
  already live; this fix only makes the read path correctly handle the
  write path's own real, current output shape.
- **Related to:** `REQ-SB-71-US-03` (Meeting Capture redesign — the
  pipeline that writes `attendees` as a plain wikilink-string list, the
  shape this fix must correctly read), `REQ-SB-43-US-01` (Meeting Cockpit
  — owns `resolve_people_chips`'s own call site), `ADR-036` point 7 (the
  read-only, never-creates-a-Person-note contract this fix must not
  violate), `ADR-048` Decision 6 (`person_note_dedup_key`/`person_note_path`
  — the stem-shape this fix's lookup relies on).
- **External:** verification needs to run against the user's real, live
  vault — at least one real Meeting note with plain wikilink-string
  attendees (two already confirmed live: "Alignment
  Mubadala-2026-08-17-a4737bc4", "PSS Team Weekly Meeting-2026-08-18-
  47a72b70"), ideally including at least one attendee wikilink with no
  matching Person note to exercise the fallback facet.

## Constraints

- **Fix direction is adopted, not open:** normalize a plain wikilink-string
  attendees entry to real name/email data by stripping `[[...]]` (reusing
  `vault_writer.py`'s existing `_WIKILINK_PATTERN` extraction, the same
  regex `upsert_attendee_links` already uses) and looking the resulting
  stem up via `vault_indexing.get_index()` (the same stem-keyed index
  lookup `resolve_people_chips` already performs for the subject note) —
  not a purely defensive per-item type check that skips/blanks the entry.
  The exact call-site placement (inside `_coerce_people_list`, inside
  `resolve_people_chips`'s own loop, or a small new helper) is an
  implementation-shape detail for `/plan-tasks`, not decided here.
- **Must never create a Person note as a side effect of resolving chips**
  — `ADR-036` point 7's existing read-only contract is unchanged; an
  unresolvable wikilink stem falls back to the existing "no note yet"
  chip shape, it does not call `ensure_person_note` or write anything.
- **Must not change `_coerce_people_list`'s two already-working shapes**
  (a JSON-encoded string; an empty/missing field) — this fix only adds
  correct handling for a third, real shape (a list of plain wikilink
  strings), per Scenario 1's own trailing regression clause.
- **`_coerce_people_list`/`resolve_people_chips` stay scoped to
  `app/business/cockpit/people.py`** (plus, if the decomposer places the
  reused regex there, a small addition to that same file or a thin import
  from `vault_writer.py`) — this fix does not touch
  `meeting_classification.py`'s own write path, which is already correct
  and not the source of this bug.
- Applies to both `subject_kind` values `_ATTENDEE_FIELD_BY_KIND` names
  (`"meeting"` → `attendees`, `"email"` → `recipients`) — the fix is
  inside the shared `_coerce_people_list`/`resolve_people_chips` code
  path, not meeting-specific, even though `BUG-027`'s own repro is a
  Meeting note.

## Implementation Tasks

<!-- Analyst-authored starting point, non-authoritative -- the decomposer's
own table at /plan-tasks supersedes this. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| BUGFIX-06-US-01-T01 | backend | Promote `vault_writer._WIKILINK_PATTERN` to public `WIKILINK_PATTERN` (updating its own 2 internal call sites); normalize a plain wikilink-string `attendees`/`recipients` list entry to real name/email by stripping `[[...]]` via that promoted regex and resolving the stem via `vault_indexing.get_index()`, falling back to the existing "no note yet" chip shape for an unresolvable stem; verify live against real Meeting notes (`AC-01`, `AC-02`) | `src/backend/app/data_access/vault_writer.py` (rename only), `src/backend/app/business/cockpit/people.py` | `../Tasks/BUGFIX-06-US-01-T01-wikilink-string-attendee-resolution.md` |

<!-- Decomposer pass, /plan-tasks step 2, 2026-08-19: this table supersedes
the analyst's starting-point row above per the template contract -- one
task fully covers both locked ACs; see the task file itself for the exact
Files to Modify / Tests mapping. -->

**Dependency-graph summary:** `BUGFIX-06-US-01-T01` has `depends_on: []`
(no other task in this batch) -- a single-task story, no graph edges.

## Definition of Done

- [x] The acceptance-criteria scenario passes (verified live: a real
      Meeting note with plain wikilink-string attendees returns 200 from
      the Meeting Cockpit and shows real attendee info for a resolvable
      wikilink and the existing fallback chip for an unresolvable one)
- [x] Every Implementation Task above is complete (or explicitly dropped
      with reason)
- [x] All Constraints respected — including that no Person note is ever
      created as a side effect, and the two already-working
      `_coerce_people_list` shapes are unregressed
- [x] Automated tests added/updated and passing (once test tooling exists) — n/a, test tooling still pending; manual mode used per `Pipeline.md`
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] `BUG-027` flipped `In Sprint → Closed` in both `BUGS.md` and
      `BACKLOG.md`'s `## Bugs` mirror once this story is `Done`

## Non-Goals / Out of Scope

- Changing `meeting_classification.py`'s own attendee-write path — it
  already writes the correct, real, current shape; this fix only teaches
  the READ side to correctly handle that shape.
- Reconciling `_coerce_people_list`'s own docstring claim that `attendees`
  is designed as `list[dict]` (`ADR-036` point 7) against the real,
  shipped `list[wikilink-string]` write behaviour — the docstring itself
  is left as-is by this story; the decomposer/architect may choose to
  correct it as a documentation-only touch alongside the code fix, but
  that is not a locked AC here.
- Any change to `find_existing_person_note`/`find_person_note_by_name`'s
  own already-correct, already-read-only lookup contracts — this fix only
  adds one more caller pattern (stem lookup via `vault_indexing.get_index()`)
  inside `cockpit/people.py`, mirroring, not modifying, those existing
  primitives.
- Retrofitting `_coerce_people_list`'s own docstring-claimed `list[dict]`
  branch into actually being reachable/writable anywhere — no code path
  writes that shape today and none is added by this fix.

## Notes

**Prototype parity:** Specced — `html-prototype/meeting-cockpit.html`'s
Attendees panel (both the clickable `.tag-chip` and non-clickable
`.tag-chip--static` states) already covers every visual state this fix
needs to reach; no new region, no `Deferred`/`Superseded` items. See
`## Context`'s own prototype-parity paragraph above for the line
references.

**Why one scenario, two facets:** per the triage-mode contract, one
untagged Gherkin scenario per bug in this batch — this batch is `BUG-027`
only. Its two facets (a wikilink resolving to a real Person note; a
wikilink with no matching Person note) are two aspects of the SAME
regression criterion `BUG-027` itself names — one root cause
(`_coerce_people_list`/`resolve_people_chips` never handling a plain
wikilink-string list item) and one fix (normalize via the reused
wikilink-stripping + index-lookup pattern). This mirrors
`BUGFIX-05-US-01`'s own established "one scenario, several facets for one
bug with one root cause" precedent. The decomposer may split this into two
locked ACs at `/plan-tasks` if that reads more verifiable, same latitude
that story's own Notes invited.

**Why `gate: clear`:** no MUST-FLAG trigger fired this pass.
- Trigger 1 (material assumption): none — the root cause was re-confirmed
  by direct code reading (`_coerce_people_list`, `resolve_people_chips`,
  `meeting_classification.py`'s real write path, `vault_writer.py`'s
  `person_note_dedup_key`/`person_note_path`/`_WIKILINK_PATTERN`/
  `create_person_note_baseline`), not assumed from the bug note's text
  alone. The fix direction reuses an already-live pattern in this
  codebase rather than inventing one.
- Trigger 2 (Draft/unfinalised requirement relied on): not applicable —
  `BUG-027` is a finalised, non-Draft bug-ledger entry, not a PRD
  requirement.
- Trigger 3 (ADR created/changed): not applicable — applying an
  already-established regex-extraction + index-lookup pattern to a second
  call site is not a new architectural/tooling/structural-boundary
  decision; no ADR is touched by this pass.
- Trigger 4 (wrote an `ESCALATIONS.md` entry): not applicable — no
  escalation entry was written.
- Trigger 5 (oversized): no — one small, single-business-file-scoped fix
  (`cockpit/people.py`, possibly a one-line reuse from `vault_writer.py`);
  fits one working context easily.
- Trigger 7 (contradictory inputs): none — the bug's own repro and this
  pass's direct code reading agree on the root cause; the one
  discrepancy found (the bug note's suggestion that
  `people_extraction.py` already holds the reusable pattern, when it
  actually lives in `vault_writer.py`) is a factual correction recorded
  above, not a contradiction that changes the fix's own direction or
  creates ambiguity about what to build.
- Trigger 8 (multiple equally-valid interpretations / genuinely unclear):
  none — the bug note itself floated two candidate shapes (normalize vs.
  defensive type-check), but only one satisfies this story's own
  acceptance bar ("correctly displays real attendee info derived from
  those wikilinks") — a defensive-only fix would still leave attendee
  chips showing no real name/email, which is not "correct," so it is not
  treated as an equally-valid alternative; see `## Context`'s own
  "explicitly NOT sufficient" paragraph.

gate: clear 2026-08-19 — no triggers fired (no ADR touched, no material
assumption beyond direct code confirmation, `BUG-027` is a finalised
ledger entry, no escalation written, single-file-scoped fix, one
unambiguous fix direction once the acceptance bar is read literally).

---

**Architect pass (`/plan-tasks` step 1), 2026-08-19:**

**No ADR.** This fix composes two already-`Accepted`, already-live
primitives at a second call site — `vault_writer.py`'s existing
wikilink-stripping regex (promoted from private `_WIKILINK_PATTERN` to
public `WIKILINK_PATTERN`, per this project's own established
`MEMORY.md` pattern "promote a private `data_access` normalization
helper to public the moment a second layer needs the identical logic"
— the `vault_writer._tag_slug` → public `tag_slug` precedent,
`REQ-SB-10-US-01-T01`), and `vault_indexing.get_index()`'s existing
stem-keyed lookup (the same one `resolve_people_chips` already performs
for the subject note itself). No new tool, framework, or structural/
layering boundary is introduced; `ADR-003`'s `api → business →
data_access` boundary and `ADR-036` point 7's read-only cockpit contract
are both extended, not reopened. Confirmed live precedent for a
business-layer module importing a private, underscore-named
`data_access` helper directly (`app/business/pipelines/
librarian_housekeeping.py` already calls `vault_writer._slugify(...)`
this way) — but `MEMORY.md`'s own written policy (promote-on-second-use)
is the one followed here, matching the `_tag_slug` precedent rather than
the `_slugify` one, since a promotion this small carries no behaviour
change and keeps one canonical name instead of two call sites reaching
into a private module member.

**architecture.md updated** (`Last reviewed` footer + two content
additions, both appended, nothing rewritten):
1. "Meeting & Inbox Cockpits" section — new bullet directly after the
   existing `people.py` bullet, documenting the wikilink-string
   extension and the `_WIKILINK_PATTERN` → `WIKILINK_PATTERN` promotion.
2. REQ-SB-54 "OKF nested actor-provenance fields" section — a short
   correction bullet: that section's existing claim that Meeting
   `attendees` ships as a JSON-encoded `list[dict]` string (matching
   Email `recipients`) is stale/inaccurate — direct code reading (this
   story's own root-cause investigation) confirms Meeting `attendees`
   has always actually been a plain `list[str]` of wikilinks. Recorded
   as an append-only correction, not a rewrite of the original claim.

**Architecture scope (bounds the decomposer/coder):**
`Implementation/Architecture/architecture.md` → §"Meeting & Inbox
Cockpits — multi-agent shared-thread workspace" (the `people.py`
extended bullet specifically) is the primary section the coder is
bounded by, plus §"Source Layout" / the `api → business → data_access`
layering rule (`ADR-003`, unchanged) governing the `vault_writer.
WIKILINK_PATTERN` reuse from `cockpit/people.py`. The REQ-SB-54
correction bullet is background-context only (documentation fix, not a
scope the coder touches). No other `architecture.md` section is in
scope. Files: `src/backend/app/business/cockpit/people.py` (primary),
`src/backend/app/data_access/vault_writer.py` (one-line rename,
`_WIKILINK_PATTERN` → `WIKILINK_PATTERN`, plus updating its own two
existing internal call sites to the new public name — pure rename, no
behaviour change).

**Gate:** `gate: clear` — no MUST-FLAG trigger fired this pass (trigger
3 does not apply: no ADR created or changed).

---

**Decomposer pass (`/plan-tasks` step 2), 2026-08-19:**

Locked both ACs as authored (see the inline decomposer note directly
after the Acceptance Criteria section for the full split rationale):
`BUGFIX-06-US-01-AC-01` (resolves + no-500), `BUGFIX-06-US-01-AC-02`
(unresolved-stem fallback + two-existing-shapes regression). Neither is
`locked: false` — both have a real, observable outcome verifiable via a
live `GET /cockpit/meeting/<id>` call, per this project's own standing
API-only manual-verification discipline.

Created one task, `BUGFIX-06-US-01-T01` (`depends_on: []`), covering the
full fix: promotes `vault_writer._WIKILINK_PATTERN` to public
`WIKILINK_PATTERN` (updating its own 2 internal call sites, pure rename),
then normalizes a plain wikilink-string `attendees`/`recipients` item in
`cockpit/people.py::_coerce_people_list` via a new `_normalize_person_item`
helper that strips `[[...]]` and resolves the stem through
`vault_indexing.get_index()`. Both locked ACs are tagged in that task's
`## Tests` with real, live manual verification steps against the two
already-confirmed real Meeting notes named in this story's own
`## Dependencies` → External. `status: Ready` set on the task, in
lockstep with this story's own status transition below.

**Status transition:** `Draft → Ready` — every AC is locked (2 of 2), both
locked ACs have at least one AC-tagged manual verification step in
`BUGFIX-06-US-01-T01`'s `## Tests`, and `depends_on` is trivially acyclic
(the story's only task has no edges). No MUST-FLAG trigger fired during
this pass: no material assumption beyond direct code reading (re-confirmed
`vault_writer.py`'s real `_WIKILINK_PATTERN`/its 2 real call sites,
`vault_indexing.get_index()`'s real stem-keyed shape, and
`cockpit/people.py`'s real current `_coerce_people_list`/
`resolve_people_chips` bodies before writing the task); `BUG-027` is a
finalised ledger entry, not Draft; no ADR touched (architect's own pass
already confirmed this, unchanged here); no `ESCALATIONS.md` entry; the
task is single-session-sized (two small files, one rename + one per-item
normalization helper); both locked ACs have a real observable HTTP-level
outcome; no contradictory inputs; and the fix direction was already
unambiguous per the architect's own scope note, leaving no genuinely
unclear or multiple-equally-valid decomposition choice this pass.

**One disclosed, non-blocking residual limitation** (recorded in
`BUGFIX-06-US-01-T01`'s own `## Context / Notes`, not a locked-AC gap): a
resolved wikilink whose Person note has no email (a name-keyed
`person_note_dedup_key`, `ADR-048` Decision 6) still renders the existing
non-clickable "no note yet" chip state rather than a clickable one, since
`resolve_people_chips`'s own downstream `find_existing_person_note(email)`
re-lookup requires a non-empty email. Not exercised by either of `BUG-027`'s
own confirmed real repro meetings (both email-keyed); mirrors this
codebase's own established pattern of disclosing a narrow, out-of-scope
residual rather than silently ignoring it (`person_note_dedup_key`'s own
docstring carries an identical disclosure for a different, unrelated
facet).

`gate: clear` 2026-08-19 — no triggers fired this pass (no ADR touched, no
material assumption, `BUG-027` finalised, no escalation, single-task-sized,
both locked ACs verifiable, no contradiction, one unambiguous fix
direction).

---

**Product-owner pass (`/plan-sprints`), 2026-08-19:**

Confirmed the only `Ready` + ungrouped (`sprint: ""`) story this pass — the
other two `Ready` stories found (`REQ-SB-59-US-01`, `REQ-SB-42-US-01`) already
carry a `sprint:` value and were excluded as not ungrouped. Grouped into a new
single-story sprint, `SPRINT-066` (next sequential after `SPRINT-065`) —
`sprint: "SPRINT-066"` set above. Its single task (`BUGFIX-06-US-01-T01`,
`depends_on: []`) leaves no dependency graph to honour or contradict; the
story carries no `phase:` per the bugfix exception (hard rule 8), so no
phase-mixing question arises. `SPRINT-066` advanced `Draft → Ready`,
`gate: clear` — no MUST-FLAG trigger fired (not oversized, not blocked, no
cross-sprint dependency introduced, unambiguous single-story partition).

---

**Coder pass (`/implement-sprint`), 2026-08-19:**

`BUGFIX-06-US-01-T01` built and verified `Done` — both locked ACs PASS
live against the two real, confirmed repro meetings ("Alignment
Mubadala-2026-08-17-a4737bc4", "PSS Team Weekly Meeting-2026-08-18-
47a72b70"), plus the orphaned-wikilink and two pre-existing-shape
regression facets. Full verification record, including one disclosed
scope-internal judgement call (no live note currently carries a real
`recipients` field, so that regression facet was verified via a
temporary, fully-reverted edit reusing the task's own sanctioned
technique), is in the task's own `## Implementation Log`; also written to
`REVIEW-QUEUE.md` for optional human spot-check (not blocking). `BUG-027`
flipped `In Sprint → Closed` in `BUGS.md`/`BACKLOG.md`. `MEMORY.md` gained
one new Constraint (the three real `attendees`/`recipients` frontmatter
shapes `_coerce_people_list` must handle). `CHANGELOG.md` updated. Story
advances `Ready → Done`.
