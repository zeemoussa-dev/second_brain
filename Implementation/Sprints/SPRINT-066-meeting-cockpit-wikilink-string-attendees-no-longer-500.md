---
id: SPRINT-066
title: Meeting Cockpit resolves plain wikilink-string attendees to real Person info instead of 500ing (BUG-027 fix)
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Retro-harvest (standard Done-sprint flag) + BUGFIX-06-US-01-T01's own disclosed, non-blocking scope-internal judgement call — see REVIEW-QUEUE.md"
phase: ""                          # bugfix sprint — no single phase; BUGFIX-NN stories carry no phase: (Pipeline.md hard rule 8's exception)
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~1 task, XS"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-19
started: "2026-08-19"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-19"            # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — who drives each transition:
     Draft       → product-owner assembles the sprint. Bidirectional link is written
                   at creation: every story listed here already has sprint: SPRINT-NNN.
     Ready       → product-owner advances Draft→Ready when grouping is CLEAR (gate: clear).
                   Ambiguous, oversized, or blocked grouping stays Draft + gate: flagged.
                   Adding a story to a Ready sprint AUTO-REVERTS it to Draft.
     In Progress → /implement-sprint has started. Coder sets this + records started:.
     Blocked     → external dependency is unmet. Record it under Dependencies.
     Done        → every story is Done and every DoD box is checked. Coder sets this,
                   records completed:, DRAFTS the retrospective, and sets gate: flagged
                   for the human to skim and harvest Learnings.md.
-->

# SPRINT-066 — Meeting Cockpit resolves plain wikilink-string attendees to real Person info instead of 500ing (BUG-027 fix)

## Sprint Goal

Ship `BUGFIX-06-US-01` end to end: `cockpit/people.py`'s `_coerce_people_list`
normalizes a plain wikilink-string `attendees`/`recipients` list item to real
Person-note data (or the existing "no note yet" fallback), so the Meeting/Inbox
Cockpit no longer 500s on a real Meeting note whose `attendees` frontmatter is
the plain wikilink-string shape Meeting Capture actually writes today.

---

## Grouping Rationale & Sizing

- **Why grouped:** Single-story sprint — `BUGFIX-06-US-01` is the only `Ready`,
  ungrouped story this pass (confirmed by scanning every
  `Implementation/UserStories/*.md` for `status: Ready` + `sprint: ""`; the
  other two `Ready` stories found — `REQ-SB-59-US-01`, `REQ-SB-42-US-01` —
  already carry a `sprint:` value (`SPRINT-059`, `SPRINT-039` respectively)
  and are excluded as "not ungrouped"). The story has exactly one task,
  `BUGFIX-06-US-01-T01`, with `depends_on: []` — no dependency graph to
  honour, no ordering question, nothing to split.
- **No phase-mixing question:** `BUGFIX-06-US-01` carries no `phase:` — per
  `Pipeline.md` hard rule 8's bugfix exception, this sprint is exempt from
  phase homogeneity and is built standalone (`phase: ""` above, mirroring
  `SPRINT-005`/`SPRINT-016`/`SPRINT-064`/`SPRINT-065`'s own precedent for a
  single-bugfix-story sprint).
- **Sizing estimate:** ~1 task, XS. One small, single-business-file-scoped fix
  (`cockpit/people.py`, plus a one-line rename in `vault_writer.py`); the
  decomposer's own task file already confirms this fits one working session
  easily (mirrors `SPRINT-018`/`SPRINT-047`'s own "~1 task, XS" precedent for
  a small, well-scoped single-task batch). No task needs its own sprint or a
  cross-sprint `depends_on_sprints` edge.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-066 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [BUGFIX-06-US-01](../UserStories/BUGFIX-06-US-01-meeting-cockpit-wikilink-string-attendees-no-longer-500.md) | Meeting Cockpit resolves plain wikilink-string attendees to real Person info instead of 500ing (BUG-027 fix) | — (bugfix) | Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** None.
- No external blocker — `meeting_classification.py`'s current attendee write
  path (`REQ-SB-71-US-03`) and `resolve_people_chips`'s own read path
  (`REQ-SB-43-US-01`/`ADR-036` point 7) are both already `Done` and already
  live; this fix only makes the read path correctly handle the write path's
  own real, current output shape.
- **Note carried from the story:** verification needs to run against the
  user's real, live vault — at least one real Meeting note with plain
  wikilink-string attendees (two already confirmed live: "Alignment
  Mubadala-2026-08-17-a4737bc4", "PSS Team Weekly Meeting-2026-08-18-
  47a72b70"), ideally including at least one attendee wikilink with no
  matching Person note to exercise the fallback facet.

---

## Out of Scope

- Changing `meeting_classification.py`'s own attendee-write path — already
  correct; this fix only teaches the READ side to handle its real shape.
- Reconciling `_coerce_people_list`'s own docstring claim
  (`list[dict]`-designed, `ADR-036` point 7) against the real, shipped
  `list[wikilink-string]` write behaviour — a documentation-only correction,
  not a locked AC.
- Resolving the disclosed name-keyed-Person-note-with-no-email residual
  limitation (see `BUGFIX-06-US-01-T01`'s own `_normalize_person_item`
  docstring) — narrow, not exercised by `BUG-027`'s own confirmed real
  repros, not a locked AC.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — done at the architect's own `/plan-tasks` pass (see `BUGFIX-06-US-01`'s own frontmatter note); no further change needed by the coder
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — n/a, no ADR created or changed this sprint
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. The coder drafts this section and
sets gate: flagged. The HUMAN then skims it, approves, and copies anything under
"Patterns to carry forward" and "Antipatterns to avoid" verbatim (or expanded)
into Implementation/Learnings.md — that is the cross-sprint index future sprints
read. The retro here is a sprint-level snapshot; Learnings.md is the permanent
record. The coder does NOT write Learnings.md directly. -->

### Sizing accuracy

- **Estimated:** ~1 task, XS — **Actual:** 1 task, XS (one rename + one
  per-item normalization helper in a single business file) — **Takeaway:**
  exactly as sized. The decomposer's own upfront confirmation that this
  composes two already-`Accepted`, already-live primitives (`vault_writer`'s
  wikilink regex, `vault_indexing.get_index()`'s stem lookup) at a second
  call site — rather than inventing anything new — held true through
  build and verification; no scope surprises.

### What worked

- Reusing an already-live extraction pattern (`WIKILINK_PATTERN` +
  `vault_indexing.get_index()`) at a second call site, instead of writing
  a new parser, kept the fix small, low-risk, and fast to verify — the
  architect's own upfront framing ("compose, don't invent") was accurate.
- The task's own `## Tests` step already sanctioned "a direct, reverted
  file edit" as a verification technique for the orphan-stem facet; that
  same technique cleanly covered a second, unanticipated gap (no live
  note currently has a `recipients` field) without needing to invent a
  new workaround or block the task.
- Restarting the non-`--reload` `uvicorn` process and re-running
  `POST /vault-index/rebuild` after every vault-file edit (temp or revert)
  caught what would otherwise have been silent stale-index/stale-code
  false negatives — worth keeping as a standing verification habit for
  this codebase's manual-verification mode.

### What didn't work

- The story's own confirmed real repro meetings both happened to have
  every attendee resolvable — neither exercised the orphaned-wikilink
  fallback facet naturally, and the live vault currently has zero notes
  with a `recipients` field at all (the write path for that shape has
  moved to the Thread-based model). Both gaps needed a temporary, disclosed,
  fully-reverted vault edit to exercise. Not a defect in this sprint's own
  work, but a reminder that "confirmed real repro" doesn't always cover
  every locked AC facet — worth flagging at `/plan-tasks` time going
  forward when a story's own external dependencies note real repro data
  that may not span every facet.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Promote-on-second-use for `data_access` normalization helpers** —
  when a second layer needs the identical extraction/formatting logic a
  private `data_access` helper already implements, promote it to public
  (pure rename, no behaviour change) rather than duplicating the logic or
  reaching into the private name. Second confirmed instance of this
  project's own established pattern (`tag_slug`, now `WIKILINK_PATTERN`).
- **Reuse a task's own sanctioned "direct, reverted file edit" verification
  technique across sibling regression facets, not just the one it was
  written for** — if a locked AC's regression facet can't be exercised
  against a currently-existing real note (a write path has moved on, data
  has aged out), the same "temporarily add via a direct, reverted file
  edit, then confirm byte-identical revert" technique already sanctioned
  elsewhere in the same task's `## Tests` extends cleanly, without
  weakening the "real vault, no fixture" verification discipline — just
  disclose it as a scope-internal judgement call (`gate: flagged`,
  `REVIEW-QUEUE.md`) rather than silently substituting a mock.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Assuming a non-`--reload` local `uvicorn` process will pick up a code
  change on its own** — this codebase's dev server is started without
  `--reload` in this environment; a coder must explicitly restart the
  process (and re-run `POST /vault-index/rebuild`) before any live
  verification, or risk a false-negative (still-500ing) or false-positive
  (stale-code-passing) result.

### Open follow-ups

- None blocking. One disclosed, non-blocking residual limitation carried
  from the decomposer's own pass (a resolved wikilink whose Person note
  has no email still renders the non-clickable fallback chip state) —
  recorded in `_normalize_person_item`'s own docstring, not exercised by
  `BUG-027`'s own confirmed real repros, not a locked AC; no new follow-up
  filed.

---

## Gate breadcrumb

`gate: clear` 2026-08-19 — no MUST-FLAG trigger fired during grouping: exactly
one `Ready`, ungrouped story in scope (confirmed by scanning all
`Implementation/UserStories/*.md`), its single task has `depends_on: []` (no
graph edge to honour or contradict), the story carries no `phase:` per the
bugfix exception (hard rule 8) so no phase-mixing question arises, the story
is not oversized (decomposer's own gate already confirmed single-file-scoped),
it is not blocked, and no cross-sprint dependency was introduced (this sprint
has no `depends_on_sprints`). Partition is unambiguous — one story, one
sprint. Advanced `Draft → Ready`.
