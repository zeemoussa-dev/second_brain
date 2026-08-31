---
id: SPRINT-080
title: Import — upload a .sbf bundle, per-artifact conflict resolution, real target-machine provisioning
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Retrospective drafted for human review/harvest into Learnings.md. The story's own standing ADR-015/ADR-014 human-review flag (REVIEW-QUEUE.md) is carried forward, not cleared by sprint close."
phase: P2                          # single phase only — a sprint never mixes phases
depends_on_sprints: [SPRINT-079]   # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~6 tasks, M"     # effort estimate; checked vs actual in retro
created: 2026-08-31
started: "2026-08-31"              # YYYY-MM-DD when status → In Progress
completed: "2026-09-01"            # YYYY-MM-DD when status → Done
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

# SPRINT-080 — Import (conflict resolution, real target-machine provisioning)

## Sprint Goal

Ship `REQ-SB-85-US-03` end-to-end: upload a real `.sbf` bundle, preview its
genuine contents and any per-artifact id conflicts against the target
machine, resolve each conflict explicitly (overwrite / skip / keep both),
and fully provision every deployed artifact — never leave a half-unpacked
archive behind.

---

## Grouping Rationale & Sizing

- **Why grouped as its own sprint:** `REQ-SB-85-US-03`'s 6 tasks form one
  connected dependency chain that also reaches back into `SPRINT-079`'s own
  output at multiple points, confirmed directly from the decomposer's own
  task frontmatter, not re-derived:
  - `US-03-T01` `depends_on: [REQ-SB-85-US-02-T04]` — shares the
    `sbf_archive.py` module `ADR-013` designates ("writer and reader share
    this one module"); the reader cannot be built before the writer exists.
  - `US-03-T02` `depends_on: [US-03-T01]`.
  - `US-03-T03`/`T04` are each independently buildable (`depends_on: []`)
    against their own already-`Done` read-side Manager.
  - `US-03-T05` `depends_on: [T01, T02, T03, T04, REQ-SB-85-US-02-T01]` —
    composes all four local tasks AND the shared `HermesCLI` edit (the same
    edit that adds both `export_profile` and `import_profile`); `T05` is
    the real first caller of the import half of that wrapper.
  - `US-03-T06` `depends_on: [T05, REQ-SB-85-US-01-T02]` — the Import
    entry point wires onto the SAME `SettingsArtifactsPage.tsx` `US-01`
    built.
  Per hard rule 7, this is honoured with an ordered `depends_on_sprints:
  [SPRINT-079]` edge rather than folded into one 13-task/3-story sprint —
  see `SPRINT-079`'s own Grouping Rationale for the full disclosed sizing
  judgement call and the project's own `Learnings.md` sizing-calibration
  ceiling (9 tasks/L largest exact match; 8 tasks/L confirmed four times)
  that makes a single 13-task sprint genuinely oversized by this project's
  own real evidence.
- **Precedent:** matches `REQ-SB-82`'s own 6-substory split across
  `SPRINT-076`/`SPRINT-077` — group by the graph's real dependency fault
  line, not one sprint per story and not one sprint for everything.
- **Sizing estimate:** ~6 tasks, M — matches this project's own most
  reliable sizing band, confirmed an exact match four separate times
  (`SPRINT-020`, `SPRINT-022`, `SPRINT-028`, `SPRINT-048`). `T05` (the
  4-kind multi-mechanism deployment orchestrator — Skill via
  `SkillManager.deploy`, Agent via `HermesCLI.import_profile` + Registry
  write, Template/Pipeline via `T03`/`T04`, seed files genuinely empty) and
  `T06` (upload/preview + per-artifact conflict-resolution UI, both
  `net-new-design-needed`, functional-first per the operator's own
  same-day override) are expected to be the heaviest of the six,
  consistent with this project's own repeated finding that
  live-verification effort, not code volume, drives real sprint cost.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-080 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-85-US-03](../UserStories/REQ-SB-85-US-03-import-conflict-resolution-and-provisioning.md) | Import — upload a `.sbf` bundle, per-artifact conflict resolution, real target-machine provisioning | P2 | Done (gate: flagged — ADR-015/ADR-014 human review pending, see Notes; all 6 tasks Done 2026-09-01, all 9 locked ACs verified live across T05/T06) |

---

## Dependencies / External Blockers

- **Depends on sprints:** `SPRINT-079` (must be `Done` before
  `/implement-sprint` may start this sprint — `US-03-T01` needs the real
  `sbf_archive.py` module `US-02-T04` writes; `US-03-T05` needs the real
  `HermesCLI.import_profile` wrapper `US-02-T01` adds; `US-03-T06` needs
  the real `SettingsArtifactsPage.tsx` `US-01-T02` builds).
- Internal task order (within this sprint, per the decomposer's own
  `depends_on`, plus the cross-sprint edges above): `US-03-T01` → `T02`;
  `T03`/`T04` independent (either order, or parallel with `T01`/`T02`);
  `T05` (needs `T01`/`T02`/`T03`/`T04` all done, plus `SPRINT-079`) → `T06`
  (needs `T05`, plus `SPRINT-079`).

---

## Out of Scope

- `REQ-SB-85-US-01`/`REQ-SB-85-US-02` — built in `SPRINT-079`, this
  sprint's own prerequisite.
- `REQ-SB-86` (Vault Data Sharing, `.sbd`) — a deliberately separate,
  later, real-data-sharing capability; this story never imports real
  operator data (its own Scenario 7).
- Everything the story's own Non-Goals section already excludes: undo/
  rollback of a completed import, automatic conflict resolution of any
  kind, cross-machine transport of the `.sbf` file itself.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact (no change this sprint — `T06` is a pure UI consumer of `T05`'s own already-architected endpoints)
- [ ] Any new ADRs recorded in `ADR.md` with status `Accepted` (`ADR-015`/`ADR-014` remain pending human review — see `REVIEW-QUEUE.md`, carried forward)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Notes (product-owner, `/plan-sprints`, 2026-08-31)

- **This sprint's own `gate: clear` is scoped to the GROUPING decision
  only** — no product-owner-level MUST-FLAG trigger fired: no assumption
  was made partitioning this single story into its own sprint (the real
  `depends_on` edges, both within `US-03` and reaching back into
  `SPRINT-079`, were read directly from the decomposer's own notes, never
  re-derived or guessed); `REQ-SB-85` is not `Draft`/unfinalised in the
  PRD; no ADR was created or changed by this pass (`ADR-014`/`ADR-015`
  were both appended at `/plan-tasks`, not here); no `ESCALATIONS.md`
  entry was written by this pass; the story is not judged oversized for
  its own sprint (6 tasks sits inside this project's own most-confirmed
  sizing band, and the decomposer itself already weighed and declined a
  further task-level split); the `depends_on_sprints: [SPRINT-079]` edge
  this pass introduces is a **disclosed, honoured** edge that directly
  matches three separate real task-level `depends_on` edges reaching back
  into that sprint, not a contradiction of the graph; the partition is
  unambiguous — there is no equally-valid alternative grouping once
  `SPRINT-079` is fixed as the prerequisite.
- **What this does NOT mean:** `REQ-SB-85-US-03` itself still carries
  `gate: flagged` at the story level (the architect appended `ADR-015`,
  and cited `ADR-014`, at `/plan-tasks`, trigger-3) with its own open
  `REVIEW-QUEUE.md` entry. That flag is carried forward here for
  visibility, not silently dropped — see the `Stories in Scope` status
  column above. Per `Pipeline.md`, a flagged story gate does not block
  `/plan-sprints` or `/implement-sprint` from proceeding; the human
  resolves the story's own flag independently, on its own timeline —
  exactly the same carry-forward shape `SPRINT-078` already established
  for `REQ-SB-82-US-06`'s own `ADR-011`/`ADR-012` review.
- **`/implement-sprint` will refuse to start this sprint until
  `SPRINT-079` is `Done`**, per hard rule 9 — this is intentional
  sequencing, not a defect; do not attempt to start this sprint's build
  out of order.
- No new `REVIEW-QUEUE.md` or `ESCALATIONS.md` entry was written by this
  pass — the existing `REQ-SB-85-US-03` entry in `REVIEW-QUEUE.md` already
  covers the open `ADR-015`/`ADR-014` review; duplicating it here would
  only fragment the same open item across two places.

---

## Retrospective

<!-- Filled in by the CODER when status: Done. The coder drafts this section and
sets gate: flagged. The HUMAN then skims it, approves, and copies anything under
"Patterns to carry forward" and "Antipatterns to avoid" verbatim (or expanded)
into Implementation/Learnings.md — that is the cross-sprint index future sprints
read. The retro here is a sprint-level snapshot; Learnings.md is the permanent
record. The coder does NOT write Learnings.md directly. -->

### Sizing accuracy

- **Estimated:** ~6 tasks, M — **Actual:** 6 tasks, M — matched exactly,
  extending the project's own most-confirmed sizing band a fifth time
  (`SPRINT-020`/`022`/`028`/`048`/now `080`). `T05` (the 4-kind
  multi-mechanism deployment orchestrator) and `T06` (the two
  `net-new-design-needed` frontend screens) were, as predicted, the
  heaviest of the six — not in code volume, but in real-verification
  effort (a real multi-kind `.sbf` round trip for `T05`; a real headless-
  browser CDP session driving a real file upload/conflict/commit cycle for
  `T06`).

### What worked

- **Stale `--reload` dev-server detection BEFORE writing any frontend
  code, not after a confusing failure** — `T06` started by hitting
  `/openapi.json` directly and confirmed `T05`'s own already-`Done` import
  routes were missing from the live backend, restarted it fresh, and only
  then began building. Caught a `SPRINT-019`/`022`/`035`-class staleness
  issue at its cheapest possible moment.
- **Producing the real `.sbf` test fixture via the SAME already-`Done`
  export path (`artifact_export.commit_export`), driven directly in-venv
  rather than through a UI flow** — real bundle bytes, real conflicts (the
  freshly-created scratch artifacts already existed on this machine at
  upload time), zero new fixture-generation code, and it let `T06`'s own
  live verification start immediately at the frontend layer instead of
  first having to drive the Export UI just to get a test file.
- **A minimal native `fetch`+`WebSocket` CDP driver, `DOM.setFileInputFiles`
  for the real upload, and a `window.fetch`-override for the one AC
  (`AC-09`) whose real failure mode wasn't cheaply inducible against the
  live backend** — all three techniques were already-established
  precedent from `SPRINT-036`/`038`; zero new tooling had to be invented,
  confirming those patterns keep generalizing to new screens.

### What didn't work

- **A first fetch-spy install got silently shadowed by a second, different
  spy installed later in the same session** (`window.fetch` was
  re-assigned by a body-capturing spy that didn't itself forward into the
  first spy's own tracking array) — cost one confused round of "the spy
  says zero calls happened" before noticing two independent spies had been
  stacked instead of composed. Fixed by folding both concerns (call-log +
  body-capture) into one spy function. Worth naming as its own explicit
  antipattern below.
- **Git Bash's automatic POSIX-path-to-Windows-path conversion silently
  mangled a plain command-line argument that happened to start with `/`**
  (`/artifacts/import/preview`, intended as a literal string key, got
  rewritten to a real filesystem path) — cost one confused round of
  "the spy captured nothing" before recognizing the argument itself never
  reached Node as typed. `MSYS_NO_PATHCONV=1` fixed it once identified.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Verify a task's own prerequisite endpoint is actually LIVE on the
  running dev server (`/openapi.json` route listing) before writing any
  code against it, whenever the prerequisite task's own `Done` status is
  more than a few tool-calls old** — cheaper than debugging a confusing
  404/empty-state later, and this project's Learnings already show
  `--reload` staleness recurring across many prior sprints.
- **Produce a live-verification test fixture via the target app's own
  already-`Done`, real, in-venv API/business-logic path (not a hand-built
  fixture, not a UI-driven detour) whenever an earlier, already-shipped
  feature produces exactly the artifact shape a later feature needs to
  consume** — real bytes, real edge cases (here, real conflicts, for
  free), and zero new fixture-generation code to maintain.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Installing a second `window.fetch` override in the same live CDP
  session without first checking whether an earlier override already
  wraps it** — the second override silently replaces (not composes with)
  the first, so any earlier spy's own tracking state quietly stops
  updating with no error of any kind. Always fold every tracking concern
  (call log, body capture, response mocking) into ONE spy function
  installed once per session, or explicitly chain through
  `window.__originalFetch`/whatever the first spy already exposed.
- **Passing a literal string command-line argument that happens to start
  with `/` to a Git-Bash-invoked Node script without `MSYS_NO_PATHCONV=1`**
  — MSYS's own automatic POSIX-path rewriting silently corrupts it into an
  unrelated Windows path with zero error, only a wrong downstream result.
  Set `MSYS_NO_PATHCONV=1` by default for any Git-Bash-invoked script whose
  own arguments are ever URL-path-shaped strings, not real filesystem
  paths.

### Open follow-ups

- `ADR-015`/`ADR-014` still await human review (`REVIEW-QUEUE.md`,
  standing since the architect pass) — the story/sprint being `Done` does
  NOT clear this; it is carried forward exactly as `SPRINT-078`/`079`
  already established for an analogous case.
- `T05`'s own two disclosed findings remain open: (1) a scope-internal
  Skill-metadata-parsing assumption (worth a quick look since it touches
  `ADR-013`'s own frozen manifest shape indirectly); (2) a real,
  pre-existing `SkillManager.delete()`/`.undeploy()` bug (bare-slug id
  passed where Hermes expects `"category/slug"`) — not fixed by either
  `T05` or `T06` (both worked around it for their own scratch cleanup
  only); worth a dedicated `/bug` capture + `BUGFIX-NN` story.
- A real `/design REQ-SB-85` pass (covering all of `US-01`/`US-02`/`US-03`'s
  own screens, including `T06`'s two `net-new-design-needed` screens) is
  still expected later, per the operator's own same-day override recorded
  at the story level — functional-first shipped now, visual polish is a
  deliberately separate, later pass.
- With this sprint's close, `REQ-SB-85` (Artifact Export/Import) is now
  fully built end-to-end across `SPRINT-079`/`SPRINT-080` — all 3
  substories, all 13 tasks, `Done`.
