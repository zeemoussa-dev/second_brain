---
id: SPRINT-047
title: App-wide dark palette + typeface swap (tokens.css)
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "sprint retro drafted — human to skim and harvest Learnings.md"
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~1 task, XS"     # effort estimate; checked vs actual in retro
created: 2026-08-15
started: "2026-08-15"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-15"            # YYYY-MM-DD when status → Done
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

# SPRINT-047 — App-wide dark palette + typeface swap (tokens.css)

## Sprint Goal

Swap `tokens.css`'s `--color-*` values to the SkillTree-inspired dark
palette and wire in real, locally-hosted Plus Jakarta Sans / Marcellus
fonts, so every existing screen picks up the new look via the shared
token cascade with zero per-screen CSS edits.

---

## Grouping Rationale & Sizing

- **Why grouped:** Single-story sprint. `REQ-SB-52-US-01` is the only
  `Ready`, ungrouped story at this `/plan-sprints` run (all other
  `sprint: ""` stories found in `Implementation/UserStories/` —
  `REQ-SB-05-US-01`, `REQ-SB-03-US-01`, `REQ-SB-30-US-01`,
  `REQ-SB-23-US-01`, `REQ-SB-24-US-01` — are `status: Draft`, not yet
  eligible for sprint planning). The story itself is fully
  self-contained: one task (`REQ-SB-52-US-01-T01`), no `depends_on`
  edges, and its own scope note explicitly confirms it does not depend
  on or block any other in-flight work (the still-open Agents Map
  structural reskin is explicitly out of scope and unrelated). A
  single-story, single-task sprint is legitimate here per the sprint
  contract ("a sprint may hold one large story or several small related
  ones") — there is no other `Ready` P1 work to co-locate it with, and
  forcing a merge with a still-`Draft` story would require pulling that
  story through `/plan-tasks` first, which is out of scope for
  `/plan-sprints`.
- **Sizing estimate:** ~1 task, XS — one CSS-token-value swap + two
  static font-file copies + one `@font-face`/one `font-family` rule
  application. Matches the decomposer's own task-level sizing recorded
  in the story's `## Notes`.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-047 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-52-US-01](../UserStories/REQ-SB-52-US-01-app-wide-dark-palette-and-typeface-swap.md) | App-wide dark palette + real Plus Jakarta Sans / Marcellus typefaces (tokens.css swap only) | P1 | Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** None
- No external dependency — both WOFF2 font files already exist locally
  in `html-prototype/fonts/`; no network fetch, license purchase, or
  other team's work required.

---

## Out of Scope

- The Agents Map structural reskin (starfield, glass detail cards, zoom
  toolbar, drill-down animation set) — explicitly deferred by the
  story's own Non-Goals, pending `html-prototype/agents-map-skilltree-
  exploration.html`'s own browser sign-off; will need its own future
  story and sprint once that prototype is approved.
- Re-tuning `--agent-color-*` / `--color-success`/`-warning`/`-danger`
  for contrast against the new dark background — disclosed follow-on
  concern in the story, not solved here.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — n/a, no architectural fact changed (values-only change inside already-Accepted ADR-010)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — n/a, no new ADR
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

- **Estimated:** ~1 task, XS — **Actual:** 1 task, XS — matched exactly.
  The code diff was genuinely tiny (one token-value swap, two static
  font-file copies, one 3-line CSS rule), and the two prior operator
  rounds (Marcellus placement, surface/border derivation) meant zero
  in-build ambiguity was left to resolve. The real cost was live
  verification breadth (6 real routes × screenshots + computed-style +
  network evidence), not code volume or judgement-call friction — a
  now-familiar shape for this project's CSS/token-only stories.

### What worked

- **Grounding every "missing" mapping value in a real, already-committed
  file** (`html-prototype/styles.css`'s own `body.theme-skilltree`
  block) instead of inventing anything — every one of the 9 target
  tokens traced to either a directly-named PRD source value, the
  operator's own resolved Note, or a mechanical alpha/reuse derivation
  from one of those two. Zero fresh assumptions needed during the build
  itself; the decomposer had already closed every gap at `/plan-tasks`.
- **`git diff -U0` as the exact-verification tool for a "must stay
  byte-identical" regression AC** (AC-06) — a precise, unambiguous
  pass/fail rather than an eyeballed diff read, confirmed before any
  live-browser check ran at all.
- **The now-standard minimal-CDP-WebSocket-driver technique
  (SPRINT-032/033/036/038 lineage) generalized cleanly to a pure CSS/
  network verification task with no interaction sequencing at all** —
  navigate, evaluate computed styles, capture network log, screenshot,
  repeat across 6 routes in one script run. No new technique needed.
- **Byte-size comparison (`Get-ChildItem`'s `Length`) as a cheap,
  exact "verbatim copy" proof for binary font-file assets** — faster and
  more conclusive than a visual "does it look like the file copied"
  check.

### What didn't work

- **A single fixed post-navigate wait (1800ms) was too short for one
  screen's own slower app-level data-loading step** — `/system-health`
  was still showing "Loading..." at capture time on the first pass,
  requiring a second, longer-wait (4000ms) targeted recapture. Not a
  defect in this task's own code (the underlying cause was a genuine,
  pre-existing backend `500` on `GET /system-health`, unrelated to any
  file this task touched), but the first screenshot pass didn't
  distinguish "still loading" from "this is the final state" without a
  second look.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Ground every "gap" value in an existing, already-committed reference
  file's own real values before treating it as a fresh assumption** —
  when a decomposer or coder needs a value the PRD/story doesn't name
  directly, check whether a sibling prototype/reference file already
  carries a disclosed, reasoned value for the same palette/config before
  inventing one; cite it explicitly rather than guessing.
- **`git diff -U0 | grep <exact-token-names>` as the go-to technique for
  any "these specific N values must stay byte-identical" regression
  AC** — faster and more precise than reading a full diff for the
  absence of a change.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Trusting a single post-navigate wait duration is enough for every
  screen in a multi-route screenshot pass** — one screen's own slower
  (or, here, actually-failing) data-fetch left it in a transient
  "Loading..." state at the original wait's capture time. When any
  route in a batch renders unexpectedly sparse content, re-capture that
  one route with a longer wait before concluding the palette/behavior
  is wrong — don't let one route's own unrelated timing/backend issue
  contaminate the read on the others.

### Open follow-ups

- **`GET /system-health` returns a real backend `500 Internal Server
  Error`** on the currently-running dev backend — observed live during
  this task's AC-02 verification pass, unrelated to any file this task
  touched (no backend file is in `REQ-SB-52-US-01-T01`'s `## Files to
  Modify`). Worth a `/bug` capture and its own fix story; not filed here
  since this coder pass is scoped to the CSS/font task only.
- **The Agents Map structural reskin** (starfield, glass detail cards,
  zoom toolbar, drill-down animation set) remains deferred, pending
  `html-prototype/agents-map-skilltree-exploration.html`'s own browser
  sign-off — unchanged from this sprint's own Out of Scope section, not
  a new finding.

---

## Notes

**Product-owner grouping (2026-08-15, `/plan-sprints`):** Read
`Implementation/Pipeline.md` and `Implementation/Learnings.md` per
contract before grouping. Scanned `Implementation/UserStories/*.md` for
`status: Ready` + `sprint: ""` — `REQ-SB-52-US-01` was the only match;
the other 5 stories carrying `sprint: ""` are all `status: Draft` and
therefore not eligible for this pass. No dependency graph to honour (the
story's single task has no `depends_on` edges) and no phase-mixing risk
(single story, single phase, `P1`). Grouping is unambiguous — no
MUST-FLAG trigger fired (no assumption made, no ADR touched, no
escalation, sizing is clear, no cross-sprint dependency introduced, no
blocked story, only one valid partition of one story).

gate: clear 2026-08-15 (product-owner) — sprint advanced Draft → Ready;
no triggers fired.

**Coder close-out (2026-08-15, `/implement-sprint`):** Read
`Implementation/Pipeline.md` and `Implementation/Learnings.md` per
contract before building. Built and verified `REQ-SB-52-US-01-T01` live
against all 6 real routes — all 6 locked ACs PASS (full evidence in the
task's own Implementation Log). Story `REQ-SB-52-US-01` flipped to
`Done`; this is the sprint's only story, so the sprint itself flips to
`Done` too. Retrospective drafted above. One unrelated, pre-existing
backend finding (`GET /system-health` → real `500`) surfaced during live
verification, logged under Open follow-ups — not a blocker on this
sprint's own scope.

gate: flagged 2026-08-15 (coder) — sprint status: In Progress -> Done;
retrospective drafted, `gate: flagged` per Pipeline.md so a human skims
it and propagates the "Patterns to carry forward"/"Antipatterns to
avoid" entries into `Implementation/Learnings.md`. This is the expected
sprint-close gate, not an error.
