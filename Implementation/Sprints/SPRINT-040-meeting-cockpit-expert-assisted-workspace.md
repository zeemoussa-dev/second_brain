---
id: SPRINT-040
title: Meeting Cockpit — shared cockpit module, 3-panel prep-and-live workspace with attendee chips, unified Expert chat, and on-the-spot research
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "retro drafted for human skim; 2 scope-internal judgment calls on T03/T08 logged for spot-check (see REVIEW-QUEUE.md); no blocked work."
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~9 tasks, L"      # effort estimate; checked vs actual in retro
created: 2026-08-14
started: "2026-08-14"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-14"            # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-040 — Meeting Cockpit

## Sprint Goal

Build `REQ-SB-43-US-01` end to end per `ADR-036`: the SHARED
`app/business/cockpit/` module (thread store, multi-party chat composition,
people-chip lookup, on-the-spot research) and the shared `Cockpit.tsx`
3-panel frontend component, wired into a clickable My Day Calendar row that
opens the real Meeting Cockpit.

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — `REQ-SB-43-US-01` is the only
  story here. Its 9 tasks form one mostly-linear chain (`T01 → T02 → T04 →
  T05 → T07 → T08 → T09`, with `T03` feeding `T05` independently and `T06`
  feeding `T09` independently) — confirmed acyclic, no cross-story
  `depends_on` edge (every one of this story's own Done prerequisites —
  `REQ-SB-08-US-01`, `REQ-SB-10-US-01`, `REQ-SB-18-US-01`,
  `REQ-SB-20-US-01`, `REQ-SB-36-US-01` — is already `Done`, needing no
  sprint-level edge).
- **Why NOT combined with `REQ-SB-44-US-01`**, despite the real, genuine
  dependency the other direction (`REQ-SB-44-US-01`'s own `T04`/`T05`/`T06`
  `depends_on` this story's `T05`/`T07`/`T08` per `ADR-036` point 3's
  "SHARE, do not fork" instruction): combining would produce a ~15-task
  sprint (9 + 6), well past this project's own observed sizing ceiling
  (`Implementation/Learnings.md`'s largest matched precedent is
  `SPRINT-021`, 9 tasks/L, estimated-vs-actual matched exactly — no XL
  precedent exists anywhere in this project's history). Per
  `Implementation/Pipeline.md` hard rule 7, a dependency-linked story may
  instead go in an **ordered sprint** with a recorded `depends_on_sprints`
  edge — chosen here over a combined sprint specifically because it keeps
  both sprints within this project's own proven sizing band.
  `REQ-SB-44-US-01` is sequenced into its own sprint, `SPRINT-041`,
  ordered after this one (`depends_on_sprints: [SPRINT-040, ...]`) — see
  that sprint's own Grouping Rationale.
- **Why NOT combined with `REQ-SB-42-US-01`:** no dependency, no shared
  architecture scope (`ADR-036` vs. `ADR-035`), no shared file surface —
  see `SPRINT-039`.
- **Sizing estimate:** ~9 tasks, L — matches this project's own largest
  confirmed-accurate precedent (`SPRINT-021`, 9 tasks/L, estimated-vs-
  actual matched exactly) exactly. Kept as one story per its own "no
  independent value alone" test (attendee chips with no chat has no value,
  a chat with no research/save mechanism has no value, and vice versa).

---

## Stories in Scope

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-43-US-01](../UserStories/REQ-SB-43-US-01-meeting-cockpit-expert-assisted-workspace.md) | Meeting Cockpit — 3-panel prep-and-live workspace with attendee chips, a unified multi-agent Expert chat, and explicit-save on-the-spot research | P1 | Done |

**Tasks in scope** (dependency order): `T01` (`vault_writer.py` cockpit
thread state, `depends_on: []`) → `T02` (`cockpit/threads.py`, `depends_on:
[T01]`) → `T04` (`cockpit/research.py`, `depends_on: [T02]`) → `T05`
(`cockpit_router.py`, `depends_on: [T02, T03, T04]`) → `T07`
(`cockpitApiClient.ts`, `depends_on: [T05]`) → `T08` (shared `Cockpit.tsx`,
`depends_on: [T07]`) → `T09` (`MeetingCockpitPage.tsx` + clickable Calendar
rows, `depends_on: [T08, T06]`); `T03` (`cockpit/people.py`, `depends_on:
[]`) independently feeds `T05`; `T06` (`my_day.list_calendar_items` gains
`"stem"`, `depends_on: []`) independently feeds `T09`.

---

## Dependencies / External Blockers

- **Depends on sprints:** None.
- **Downstream note (not a blocker for this sprint):** `REQ-SB-44-US-01`
  (`SPRINT-041`) builds directly ON TOP of this story's `T02`/`T05`/`T07`/
  `T08` — those tasks must reach `Done` before `SPRINT-041` can start, per
  its own `depends_on_sprints: [SPRINT-040, ...]` edge. This sprint's own
  Definition of Done is unaffected by that downstream consumer.

---

## Out of Scope

- `REQ-SB-44-US-01` — the Inbox Cockpit, built ON TOP of this sprint's
  shared module in its own ordered sprint (`SPRINT-041`), not duplicated
  here.
- `REQ-SB-42-US-01` — no dependency relationship to this story (see
  `SPRINT-039`).

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — N/A, this sprint built exactly the module shape `ADR-036`/architecture.md already recorded; no new architectural fact emerged
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — N/A, `ADR-036` already `Accepted` before this sprint started
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

### Sizing accuracy

- **Estimated:** ~9 tasks, L — **Actual:** 9 tasks, L — matched exactly. No
  task was split, dropped, or merged. The heaviest real-world cost was NOT
  code volume (every module stayed small — `threads.py`/`people.py`/
  `research.py` each under ~100 lines) but live-verification complexity: a
  brand-new multi-party conversation-store shape (`T02`), a real Anthropic
  web-search round trip needing a temporary, reverted real-state
  reconfiguration to reach its positive path three separate times (`T04`,
  `T05`, `T07`), and a full 3-panel real-browser click-through (`T08`/`T09`).

### What worked

- **Composing `ADR-015`'s existing, unmodified `run_agent_conversation` once
  per brought-in Expert, sequentially, appending each real reply to one
  shared thread before the next Expert's own call is built** — worked
  exactly as designed on the first real, live, two-Expert round trip; no
  cross-talk, no misattribution, the relay-framing (`"[{agent_name} said]:
  "`) held up under direct inspection.
- **The temporary-real-state-change-then-revert-then-reconfirm protocol**
  (`SPRINT-022`/`SPRINT-035` precedent) — reused three times this sprint
  (`T04`, `T05`, `T07`) for the identical real gap (no agent in this vault's
  real configuration is both Hub-routable for research AND already
  Provider/Skill-equipped for it) — each time cleanly reverted and
  independently reconfirmed via a fresh `GET`/`list_agent_skills` call.
- **Reconciling against the REAL approved prototype file, not just a task's
  own illustrative code sample, per its own explicit Context/Notes
  directive** — caught a real class-name mismatch (`.cockpit-grid`, never
  defined anywhere, vs. the real `.cockpit-layout`) and a missing
  per-Expert attribution-color mechanism before either became a visual
  defect only caught at screenshot time.
- **A minimal, from-scratch CDP WebSocket driver (no Playwright/Puppeteer)
  against a real headless-Edge instance, combined with the project's own
  established React-controlled-input and Fiber-`onClick`-direct-invoke
  techniques** — drove a genuinely real, multi-step, multi-agent,
  multi-real-Provider-call browser session (bring in 2 Experts, send a
  message, trigger research, save, discard) end-to-end with zero new
  dependencies.

### What didn't work

- **Trusting a stray, already-running `--reload` dev-server process without
  first confirming what code it was actually serving** — cost one
  investigation cycle (a real, indexed Meeting note 404'd against an old
  worker that never finished restarting after `T05`'s own `main.py` edit).
  Resolved immediately per the already-documented specific-PID-kill/restart
  protocol; a **non**-`--reload` instance was used for the rest of the
  sprint's own HTTP-level verification specifically to avoid a repeat.
- **A `hash()`-based before/after file-content comparison across two
  separate Python process invocations** (`T04`'s own first attempt at
  confirming the real Meeting note was untouched by a Save) silently
  produced a false "changed" signal, due to Python's own per-process hash
  randomization for `str`/`bytes` — not a real content difference. Caught
  immediately by switching to a direct string comparison; no incorrect
  result was ever recorded.

### Patterns to carry forward

- **When an ADR's own factual premise about "already-established" data
  disagrees with the real, current codebase, verify the underlying
  read/write primitive directly (not just the higher-level claim) before
  building against it** — `ADR-036` point 7's claim that Meeting notes
  already carry an `attendees` frontmatter field was not just absent from
  real data (an "empty for now" case, cheap to work around) but
  structurally unwritable at all through this project's own real
  `vault_writer.py` frontmatter parser (a list-of-dicts literal silently
  round-trips to `[]`) — a materially different, deeper finding that a
  shallower "just check if the field exists" investigation would have
  missed. Worth generalizing: when a task's own "Before/Inputs" section
  cites an ADR's factual claim about an existing data shape, spend one
  extra real write+read round trip confirming the SERIALIZATION actually
  works, not just that the claim reads plausibly.
- **Never trust Python's built-in `hash()` for a cross-process
  before/after content-identity check** — always compare the real string/
  bytes content directly (or a stable digest like `hashlib.sha256`, not
  the builtin `hash()`, which is intentionally randomized per-process for
  security reasons since Python 3.3). Generalizes this project's own
  already-documented "naive CSV-round-tripped string compare produced
  false positives" antipattern (`REQ-SB-08-US-01-T06`) to a second,
  independently-discovered instance of the same underlying class of
  mistake (an unreliable identity-comparison technique).
- **When a UI action's own trigger uses "the first item in a list" as an
  implicit parameter (here, `brought_in_agent_ids[0]` as the Hub-routing
  requester), construct the live test scenario with that exact ordering
  constraint in mind** — an otherwise-correct positive-path test silently
  produced an honest `no_match` on the first attempt because the
  "first-brought-in" Expert happened to be the ONLY real keyword-matching
  Hub-routing candidate for its own request (excluded as its own
  requester). Not a defect; a test-construction lesson.

### Antipatterns to avoid

- **Assuming a stray, already-running dev-server process is safe to build
  HTTP-level verification against without confirming what code it's
  actually serving** — reconfirmed a further time this project's history
  (`SPRINT-021`/`022`/`028`/`029`/`035`'s own precedent); this time
  specifically the `--reload` WORKER-staleness variant (`SPRINT-035`'s own
  documented fix), not a stuck/orphaned process.

### Open follow-ups

- **A saved Cockpit research result does not appear in the left panel's own
  list until the next `vault_indexing` rebuild** (scheduler tick or an
  explicit `POST /vault-index/rebuild`) — matches this project's own
  already-established index-freshness precedent (`ADR-024`) rather than a
  defect unique to this story, and no locked AC asserts a specific latency,
  but it is a real, live-observed UX rough edge a real user would notice.
  Candidate future polish: have `cockpit/research.py::save_research_result`
  call `vault_indexing.rebuild_index()` itself after a successful write.
- **Whether an attendee chip with no Person note should offer a
  create-Person-note flow** — already named as a deliberately separate,
  additive product decision in the story's own Context; still open, not
  decided or built by this sprint.
- **This sprint's own `T03` disclosed finding (`vault_writer.py`'s
  frontmatter parser cannot round-trip a list-of-dicts value) is a real,
  reusable gap beyond just this story** — any FUTURE story that wants a
  native structured-list frontmatter field (not just a JSON-encoded
  string worked around here) will hit the same wall; worth a dedicated
  small fix to `_format_frontmatter_value`/`_parse_frontmatter_value` at
  some point, not scoped to this story.

---

## Notes

**Sprint assembled 2026-08-14 (`/plan-sprints`).** `REQ-SB-43-US-01`'s own
`ADR-036` (shared `app/business/cockpit/` module + shared `Cockpit.tsx`
component, composing `run_agent_conversation` once per brought-in Expert)
was approved 2026-08-14; this story enters `/plan-sprints` fully `Ready`,
`gate: clear`. Sequenced deliberately FIRST among the two cockpit stories —
it has no external blocker of its own, while `REQ-SB-44-US-01` has a real,
currently-unmet `REQ-SB-28-US-01` dependency in addition to depending on
this story's own shared-module tasks — mirroring the decomposer's own
"sequence here since this story has no external blocker" note on
`REQ-SB-43-US-01-T02`.

**Gate: `gate: clear` 2026-08-14.** No MUST-FLAG trigger fires for this
product-owner pass: (1) no material assumption — the standalone grouping
and the choice of two ordered sprints (over one combined 15-task sprint)
are read directly off the decomposer's own recorded `depends_on` graph and
this project's own sizing calibration (`Implementation/Learnings.md`), not
guessed; (2) `REQ-SB-43` is not `<!-- Draft -->`/unfinalised; (3)
product-owner does not write ADRs — `ADR-036` was already reviewed and
approved before this pass; (4) no new `ESCALATIONS.md` entry; (5) not
oversized (9 tasks, L, matching this project's own largest confirmed-
accurate precedent exactly); not a blocked story; the cross-sprint
dependency `SPRINT-041` carries onto this sprint is a pre-existing
decomposer-recorded task edge (`ADR-036` point 3), not introduced by this
pass; (6) N/A (coder-only trigger); (7) no contradictory inputs; (8) not
genuinely ambiguous — the two-ordered-sprints-vs-one-combined-15-task-
sprint choice has one clearly better answer given this project's own
sizing ceiling, not two equally-valid options. Advances `Draft → Ready`.
