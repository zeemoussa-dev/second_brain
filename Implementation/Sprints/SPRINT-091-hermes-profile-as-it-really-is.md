---
id: SPRINT-091
title: A Hermes profile as it really is — the read-only debug view
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Sprint closed — the human skims the drafted ## Retrospective and harvests Patterns/Antipatterns into Implementation/Learnings.md (the coder drafts, the human harvests). Two follow-ups also need a decision: (1) profile_detail.py labels a config key found in the one READABLE layer with that layer's name even when the other layer could not be read — the page states the limit in its own words rather than relabelling a Done task's answer; (2) MEMORY.md is 86 KB against the 40 KB budget its own rule 1 sets, so this sprint's one new reusable rule could not be appended and sits in the retro instead. Nothing is blocked."
phase: P2                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~6 tasks, M"     # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-10-17
started: 2026-10-18                        # YYYY-MM-DD when status → In Progress
completed: 2026-10-18              # YYYY-MM-DD when status → Done
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

# SPRINT-091 — A Hermes Profile As It Really Is — the Read-Only Debug View

## Sprint Goal

Give the operator one read-only page that answers, for a single Hermes profile,
the five questions this week's incidents were answered by hand: what its soul
actually says, which skills it carries at which versions and whether each
matches the framework, what its config really is, which cron jobs are bound to
it, and which toolsets are enabled — reporting each failed read honestly rather
than papering over it.

---

## Grouping Rationale & Sizing

- **Why grouped (and why alone):** `REQ-SB-99-US-01` is the **only** story that
  is both `status: Ready` and `sprint: ""` at this pass. Of the 17 ungrouped
  story files, the other 16 are all `Draft`; of the 8 `Ready` stories, the other
  7 already carry a sprint (`SPRINT-086`–`SPRINT-090`, plus older sprints). The
  partition is therefore **forced, not chosen** — there is exactly one story to
  place, and it fills a sprint on its own at 6 tasks.
- **Why not appended to an existing sprint.** No sprint is in `Draft` — the only
  status a story may be added to freely. `SPRINT-086`, `SPRINT-088`, `SPRINT-089`
  and `SPRINT-090` are all `Ready`, and appending to a `Ready` sprint
  auto-reverts it to `Draft` and re-gates it; those four became human-unblocked
  only today (the operator cleared every open review-queue item on 2026-10-17)
  and there is no dependency reason to disturb them. `SPRINT-087` is
  `In Progress` and must not be touched at all. On size alone the merges fail
  too: 6 + 5 = 11 and 6 + 7 = 13, both well past the confirmed 8–9-task ceiling.
- **Sizing:** 6 tasks, `M` — the decomposer's own estimate, and squarely on this
  project's 6-task precedent (`SPRINT-073` at `M`; two further 6-task sprints in
  `Learnings.md` estimated `~6 tasks, M` and came in at exactly that). Four
  independent backend roots are each small and local; `T05` is a five-region
  composition over readers that already exist; `T06` is the cost centre, as every
  frontend task in `Learnings.md` has been — by verification effort, not code
  volume. Not `L`: this story adds **no** new access path, writes nothing, and
  touches no shared spine.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-091 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-99-US-01](../UserStories/REQ-SB-99-US-01-hermes-profile-as-it-really-is.md) | See a Hermes profile as it really is — the full soul, skills with versions, config, jobs and toolsets | P2 | Done |

Build order inside the sprint, read from the task files' own `depends_on`:
`(T01, T02, T03, T04) → T05 → T06`. The four roots carry `depends_on: []` and
may be built in any order; `T05` needs all four; `T06` needs `T05`.

---

## Dependencies / External Blockers

- **Depends on sprints:** None. Every one of the six `depends_on` edges is
  internal to `REQ-SB-99-US-01` — verified by reading all six task files'
  frontmatter, not taken from the story's prose: `T01`/`T02`/`T03`/`T04` are
  `depends_on: []`, `T05` is
  `[REQ-SB-99-US-01-T01, …-T02, …-T03, …-T04]`, `T06` is `[REQ-SB-99-US-01-T05]`.
  **No edge leaves this story**, so there is no `depends_on_sprints` edge to
  record and hard rule 9 does not hold this sprint behind anything. It is
  startable now, in parallel with `SPRINT-087`'s remaining work.
- **In particular, no edge into `REQ-SB-96`.** `REQ-SB-96-US-01` (deployment
  drift) is still `Draft`, ungrouped and itself `gate: flagged` (`ESC-066`).
  Had this story depended on it, this sprint could not have been planned at all.
  It does not, by construction: `ADR-043` settles that `deployed_to` is not
  consulted on this read path, and the profile's own `skills/` tree is the
  enumeration source.
- **The skills-verdict overlap is a sequencing fact, not a dependency.** The
  story records that the skills-with-versions comparison is the same fact
  `REQ-SB-96-US-01` needs from the artifact's side, and that *whichever story
  lands first owns it*. This sprint lands first, so `T01`'s shared four-status
  verdict rule becomes the one implementation; when `REQ-SB-96-US-01` is specced
  into a sprint it consumes `T01`'s rule rather than writing a second one. That
  is a note for the later sprint, and imposes nothing on this one.
- **External:** a real Hermes install to read — the same standing precondition
  every Hermes-touching sprint in this repo has had. `AC-07` makes an absent or
  unreadable `<HERMES_HOME>` an asserted, verifiable outcome rather than a
  blocker.
- **Story-level gate — already resolved, carried forward as context only:**
  `REQ-SB-99-US-01` was flagged under trigger 3 for `ADR-043`. The operator
  approved `ADR-043` on 2026-10-17 and the story now reads `status: Ready`,
  `gate: clear`. Nothing about it is re-flagged here.

---

## Out of Scope

- **Editing anything from this view** — soul, config, skills or jobs. This is a
  debugger; `AgentDetailPanel.tsx` already owns what is editable.
- **Deploying or repairing a mismatched skill** — `REQ-SB-96-US-02`.
- **The cross-profile drift table** — `REQ-SB-96-US-01`, the same fact from the
  artifact's side.
- **Session transcripts** — `REQ-SB-100-US-01` (`Draft`, ungrouped).
- **Cron job authoring or scheduling** — jobs are listed, never managed.
- **Reworking the Agents Map** or retiring `agents_map_adapter.py`.
- Everything in the `REQ-SB-95` spine — `SPRINT-086` through `SPRINT-090`.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact —
      **no change needed.** The six tasks built exactly what the
      `## A Hermes Profile As It Really Is` sections and `ADR-043` already
      describe; nothing architectural was decided differently along the way.
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — `ADR-043`,
      written by the architect at `/plan-tasks` and approved by the operator
      on 2026-10-17. None added during the build.
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints —
      **deliberately not updated**; see the retro's *Open follow-ups*.
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Notes

**gate: clear 2026-10-17 — no product-owner trigger fired.** No material
assumption: the partition is forced (one eligible story) and every dependency
claim above was read from the six task files' own frontmatter rather than from
the story's prose. The requirement is finalised in the PRD. No ADR created or
changed by this pass — `ADR-043` was the architect's, and the operator approved
it today, which is why the story arrives `gate: clear`. No `ESCALATIONS.md`
entry. **Not oversized:** 6 tasks against a confirmed 8–9-task ceiling. **No
`Blocked` story.** **No cross-sprint dependency introduced** — `depends_on_sprints`
is empty because no task edge leaves the story; there was nothing to record.
No contradictory inputs. On trigger 8: with exactly one eligible story and no
`Draft` sprint to append to, there is no second equally-valid partition to
choose between.

**Why this sprint can start immediately, unlike its neighbours.** Every other
planned-but-unstarted sprint in the repo sits behind `SPRINT-087`
(`SPRINT-088`, and `SPRINT-089`/`SPRINT-090` behind both `087` and `088`), or is
independent-but-already-planned (`SPRINT-086`). `SPRINT-091` joins `SPRINT-086`
as free of any `depends_on_sprints` edge, so it may be built now or at any point
alongside the `REQ-SB-95` spine. The numbering carries no ordering claim over
`SPRINT-086`, `SPRINT-089` or `SPRINT-090`.

---

## Retrospective

<!-- Filled in by the CODER when status: Done. The coder drafts this section and
sets gate: flagged. The HUMAN then skims it, approves, and copies anything under
"Patterns to carry forward" and "Antipatterns to avoid" verbatim (or expanded)
into Implementation/Learnings.md — that is the cross-sprint index future sprints
read. The retro here is a sprint-level snapshot; Learnings.md is the permanent
record. The coder does NOT write Learnings.md directly. -->

### Sizing accuracy

- **Estimated:** `~6 tasks, M` — **Actual:** 6 tasks, `M`, one day
  (2026-10-17 planned, 2026-10-18 built end to end) — **Takeaway:** matched
  exactly, and for the predicted reason. The decomposer called `T06` the cost
  centre "by verification effort, not code volume" and that is what happened:
  the screen's own diff is one new file plus three one-or-two-line edits, while
  proving its seven locked ACs took two running environments, a scratch Hermes
  install built to order, a CDP session and roughly a dozen DOM reads. The four
  backend roots were each genuinely small because every reader they needed
  already existed — `ADR-043`'s "the work is composition and a screen, not new
  access" held true all the way through.

### What worked

- **Writing the honesty contract into the data shape, not into the prose.**
  Every region crosses the wire with its own `read` flag and a payload that is
  `null` when unread, so "could not be read" and "read, and empty" are
  different *values* and not different sentences a screen has to interpret.
  That one decision is why the screen task could not accidentally flatten the
  distinction: the frontend types carry `| null` on every payload, and the
  three failures came out as three different renderings on the first attempt.
  `BUG-085` and `BUG-088` were both cases of a screen choosing the reassuring
  reading of an ambiguous value; this sprint removed the ambiguity instead of
  asking the screen to be careful.
- **Refusing to produce an answer the codebase cannot know.** Hermes' own
  precedence between the two `config.yaml` files is not readable from this
  repository, so the view shows both layers, names both files, and reports a
  key set in both as set in both. On the operator's real install that is 109 of
  110 keys — a merged "effective value" would have looked tidier and been a
  guess 109 times over.
- **Enumerating from the disk rather than from the Registry's claim**
  (`ADR-043`). On the real install the page shows **62 skills the framework
  catalog has never heard of** in one profile. Driven from `deployed_to`, every
  one of them would have been invisible — and invisible is exactly the failure
  the operator was debugging by hand.
- **A disposable backend over a scratch Hermes home, as the default place to
  break things.** `T05` and `T06` both used it, and `T06` ran a second Vite on
  `:5174` with `VITE_API_BASE_URL` overridden so a real browser drove the real
  page against it. Renaming a `SOUL.md`, corrupting a `config.yaml`, adding and
  removing a skill folder and pointing the home at a non-existent path were all
  real, observable events, and the operator's own install and `:8001` were
  never touched. Vite gives shell `VITE_*` variables precedence over
  `.env.local`, so no file had to be edited to retarget the second dev server.
- **Reading the DOM back rather than trusting the screenshot, and looking at
  the screenshot rather than just capturing it.** Both mattered and neither
  substitutes for the other: the DOM reads caught counts and labels a picture
  could not (`0` toolset rows beside a failure element, `emptyStates: 0`), and
  the screenshots caught the opposite — the first attempt at per-region
  screenshots silently produced five identical images because `scrollIntoView`
  did nothing inside the app shell's own scroll container. Clipping each region
  from its real bounding box in a very tall viewport is what fixed it.
- **Six tasks, zero escalations.** No task in this sprint was `Blocked` and
  `ESCALATIONS.md` gained nothing — against five switch-on escalations
  (`ESC-069`, `ESC-071`…`ESC-075`) across the two preceding sprints. Each task
  here ran the file-list check *before writing code* and found its switch-on
  site already inside its own `## Files to Modify` (`T05`'s was
  `include_router` in `main.py`, already mounted; `T06`'s was the `<Route>` in
  `App.tsx`, which was listed). The rule recorded in `MEMORY.md` on 2026-10-18
  was paying for itself within a day.

### What didn't work

- **The honesty rule was applied one level deep, not two.** `T05` correctly
  reports a key missing from *every* layer as `unknown` rather than `not_set`
  when some layer could not be read — but a key found in the one *readable*
  layer is still labelled with that layer's name, as though the unreadable file
  were known not to set it. Seen live with a broken profile `config.yaml`: the
  page said `model.default` was inherited from the install root as
  `"gpt-5-root"`, while the profile's own unreadable file really did set it to
  `"gpt-5-profile"`. Root cause: the rule was written against the case the AC
  named (absent everywhere) rather than against the general shape (any
  conclusion drawn from an incomplete read). `T06` could not fix it — a `Done`
  task's file, outside its list — so the page states the limit in its own words
  instead and the decision is queued for the human.
- **`MEMORY.md` could not accept this sprint's one new rule.** The file is
  **86 KB against the 40 KB budget its own rule 1 sets**, and that rule forbids
  appending while over budget unless the new entry replaces one it supersedes.
  This one supersedes nothing, so nothing was written. The budget has been
  silently exceeded for some time; a limit that every author has to step over
  is not functioning as a limit.
- **The soul the app reports is already not the soul that was written.** On the
  disposable install, the app's own startup Action-catalogue publication
  rewrote the fixture `SOUL.md` before either task could read it — deleting the
  whole `## Scope` section in `T05`'s run, appending a block in `T06`'s. The
  view reported the file faithfully both times, which is how it became visible,
  but it means `REQ-SB-99`'s premise ("the soul is lossy on the way *out*") was
  only half the story: it is also lossy on the way *in*. Already raised by
  `T05`; `BUG-093`'s same-day fix addresses the splice path, and this sprint is
  the evidence that the fix is worth re-checking against the publication path.
- **Visual consistency was accepted rather than chosen.** The new way-in control
  is a `<Link className="btn">`, which renders underlined because `.btn` sets no
  `text-decoration` — true of all five existing instances in the app. Matching
  the precedent was the right call inside this task's file list, but it means a
  small, real inconsistency got re-shipped rather than fixed; the fix belongs in
  `settings.css` and belongs to nobody.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Encode "could not be read" in the shape, not in the wording** — when a
  surface must distinguish *absent* / *unreadable* / *read-and-empty*, give
  every region its own success flag and make the payload `null` when unread, so
  a client cannot collapse the cases by being careless. Carry the `| null`
  through the frontend types too. The alternative — one error string a screen
  has to read — is how `BUG-085` and `BUG-088` happened.
- **`.empty-state` means "we read it and it was empty." A failed read may never
  borrow that look** — give a failure its own element with the backend's
  verbatim message. This is the rule `MEMORY.md` would have gained if it had
  room; it is worth putting there (or in whatever replaces the over-budget
  file) because the convention is currently described two ways in two places:
  `REQ-SB-99-US-01`'s own Affected Screens calls `.empty-state` the
  "honest-failure convention", while `T06`'s constraints reserve it for a
  genuinely-read empty region. The narrower reading is the correct one.
- **Refuse to compute an answer whose rule lives outside this repository** —
  show the inputs, name their sources, and say plainly that no single answer is
  being given. Applied here to two config layers; the same test applies to
  anything resolved by Hermes, by a plugin, or by a model rather than by code
  this repo can read.
- **A disposable backend over a scratch home is the default place to break
  things, and a second Vite on another port makes it a real screen** —
  `VITE_API_BASE_URL` as a shell variable outranks `.env.local`, so retargeting
  a dev server needs no file edit. Everything destructive an AC asks for
  (renaming a file, corrupting a file, deleting a directory, pointing config at
  a path that does not exist) belongs there; the operator's own install is for
  read-only confirmation that the same page works against real data.
- **Clip each region from its bounding box in a very tall viewport, instead of
  scrolling to it** — inside an app shell with its own scroll container,
  `scrollIntoView` + `captureScreenshot` can silently return the same image
  every time. A full-page strip is unreadable at 20 000 px; per-region clips at
  1:1 are what you can actually look at.
- **Snapshot the whole tree, files *and* directories, by hash and mtime, around
  the read being proved** — and take the "before" snapshot *after* startup has
  settled, because this app writes into `<HERMES_HOME>` at boot. A residual
  directory-mtime difference from your own fixture surgery is expected; a single
  file-hash difference is not.
- **Prove "this page adds no cost" with a `fetch` spy installed before any app
  code runs** (`Page.addScriptToEvaluateOnNewDocument`), and assert both halves:
  one request per load *and* zero requests from the surface that merely links to
  it. `BUG-086` was a cost nobody measured until it was six seconds.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Writing an honesty rule against the case the AC names instead of against the
  shape of the problem** — `not_set`-vs-`unknown` was handled for "absent from
  every layer" and missed for "found in the one layer we could read". When a
  rule exists because a read may be incomplete, apply it to *every* conclusion
  drawn from that read, not just the one the scenario happened to describe.
- **Treating a passing build as evidence that a screen is right** — `tsc` and
  `oxlint` were clean on the first run of a page that had not yet been looked
  at. They say nothing about whether a region rendered, what a badge says, or
  whether an unread region drew itself as empty. For any screen task, the DOM
  read and the reviewed screenshot are the evidence.
- **Capturing screenshots without opening them** — five identical images were
  produced and would have been filed as "five regions verified" by anyone who
  only checked that the files existed.
- **Appending to a shared file that is over its own stated budget** — the
  budget is in the file, in rule 1, and ignoring it is how the file got to
  86 KB. Either replace a superseded rule, route the entry elsewhere, or fix
  the budget; do not append and promise to trim.

### Open follow-ups

- **Decide the partially-read config label** — should `profile_detail.py`
  report `unknown` for a key found only in the readable layer when the other
  layer failed, matching the rule it already applies when the key is absent
  everywhere? Filed in `REVIEW-QUEUE.md` under `REQ-SB-99-US-01-T06 /
  SPRINT-091`. Not blocking; the page states the limit in its own words today.
- **`MEMORY.md` is 86 KB against its own 40 KB budget**, so this sprint's one
  reusable rule could not be filed there. Filed in `REVIEW-QUEUE.md` with the
  same entry. Needs a human decision on whether to trim, re-budget, or split
  the file — until then every author faces the same refusal.
- **The soul-rewriting write path** — `T05` raised it in `REVIEW-QUEUE.md`
  (whether it becomes a `BUG`); `T06` saw it again in its milder appending form
  on a fresh disposable install, after `BUG-093` had landed. Worth re-checking
  the publication path specifically rather than only the splice.
- **`<Link className="btn">` renders underlined** across all six instances in
  the app, because `.btn` sets no `text-decoration`. A one-line `settings.css`
  change, owned by nobody, deliberately not taken inside this task's file list.
- **`REQ-SB-96-US-01` inherits a decided seam, as `ADR-043` intended** —
  `T01`'s shared four-status verdict rule exists and is already callable per
  profile, so that story consumes it rather than writing a second comparison.
  Nothing is owed by this sprint; recording it so the next planner does not
  re-open the question.
