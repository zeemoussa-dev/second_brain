---
id: SPRINT-087
title: Action as the sixth artifact kind — the catalogue, its CRUD API, plugin contributions and its screen
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "sprint Done 2026-10-18 — the retrospective below is DRAFTED and awaits the human's harvest into Implementation/Learnings.md (the standing close-out gate). Carried with it: T06's own four judgement calls, and ESC-071 (open) — /settings/actions is not in the backend's UI_FEATURE_KEYS. The story's upstream ADR-033 flag was cleared by the operator on 2026-10-17."
phase: P2                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~6 tasks, L"     # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-10-16
started: 2026-10-16                        # YYYY-MM-DD when status → In Progress
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

# SPRINT-087 — Action as the Sixth Artifact Kind

## Sprint Goal

Make `Action` a real, stored, validated, browsable and portable sixth artifact
kind — one catalogue of what this app can actually do, resolved at save time so a
broken action cannot sit waiting to fail, contributable by plugins, and rendered
in its own Settings screen.

---

## Grouping Rationale & Sizing

- **Why grouped (and why alone):** `REQ-SB-95-US-02` is the **root of
  `REQ-SB-95`'s dependency spine** — read from the task files' own frontmatter,
  eight cross-story edges point *into* it and none point out of it:
  `US-03-T01 → US-02-T01`, `US-03-T02 → US-02-T03`, `US-04-T01 → US-02-T01`,
  `US-04-T02 → US-02-T03`, `US-04-T04 → US-02-T04`, `US-04-T07 → US-02-T06`,
  `US-05-T05 → US-02-T02`. It therefore needs no `depends_on_sprints` edge of its
  own and must land before `SPRINT-088`, `SPRINT-089` and `SPRINT-090`.
- **Why nothing was folded in with it.** `US-03` (5 tasks) is the obvious
  candidate — it depends only on this story — but 6 + 5 = 11 tasks is well past
  this project's confirmed 8–9-task `L` ceiling, and `US-03`'s own story text
  states the split reason directly: "adding agent-side publication and call
  validation to it would not fit one working context." The only other edge-free
  story at this point is `US-01` (`SPRINT-086`); merging it here would make an
  11-task sprint out of two stories that share no file and no edge.
- **Sizing:** 6 tasks, sized `L`. Six tasks has repeatedly landed at `M` on this
  project (`SPRINT-020`, `SPRINT-022`, `SPRINT-028`, `SPRINT-048`), but this one
  is sized a notch up because adding an artifact **kind** is cross-cutting by
  nature: `T04` alone reaches `artifacts_inventory.py`, export, import, the
  secret scan and the dependency resolver — every one of which today hard-codes
  the five-kind set ("no 6th value is ever produced"). The `Index` precedent
  (2026-09-06) is the measured template, and `T06` adds a new Settings screen on
  top of it.
- **Deliberate ordering consequence — it closes an open plan gap.** `ADR-037`
  takes the `FRAMEWORK_API` 7 → 8 bump **once**, in whichever of the two
  plugin-contract stories lands last. `REQ-SB-95-US-05-T02` reads the real
  `plugin_api.py` first and bumps only if `register_action` is already there;
  `REQ-SB-95-US-02-T05` (here) carries no equivalent instruction, so if `US-02`
  landed last nobody would move the constant. **Sequencing `US-05`
  (`SPRINT-090`) strictly behind this sprint makes that moot** — the
  `depends_on_sprints` edge guarantees `register_action` exists before
  `US-05-T02` runs, so its conditional read takes the bump. This is the exact
  resolution option named in the `REVIEW-QUEUE.md` item, and no task file was
  edited to achieve it.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-087 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-95-US-02](../UserStories/REQ-SB-95-US-02-action-sixth-artifact-kind.md) | Action as the sixth artifact kind — one catalogue of what this app can actually do | P2 | Done 2026-10-18 (T01, T02, T04, T07 Done 2026-10-16; T03 Done 2026-10-17; T05 and T06 Done 2026-10-18. All seven locked ACs verified; `ESC-069` resolved by widening `T06`'s scope to `app/api/actions_router.py`) |

Build order inside the sprint, read from the task files' own `depends_on`:
`T01 → T02 → T03`, `T01 → T04`, `T02 → T05`, `(T03, T04, T05) → T06`.
`T07` (added 2026-10-16 to resolve `ESC-065`) hangs off `T04`: `T04 → T07`, with
nothing downstream of it.

---

## Dependencies / External Blockers

- **Depends on sprints:** None. This is the spine's root and can start
  immediately (as can `SPRINT-086`, which is independent of it).
- **Three sprints depend on this one:** `SPRINT-088` (`US-03`), `SPRINT-089`
  (`US-04`) and `SPRINT-090` (`US-05`). Per hard rule 9, `/implement-sprint`
  refuses each of them until this sprint is `Done`.
- **Story-level gate carried forward (`gate: flagged`, not resolved by this
  sprint):** `REQ-SB-95-US-02` is flagged under trigger 3 — `ADR-033` fixes two
  fields this story stores (`allowed_callers` as agent ids, and the confirmation
  flag's meaning) and awaits the operator's look. If `ADR-033` changes, the
  catalogue's stored shape changes with it, so this is the cheapest moment to
  read it. See `REVIEW-QUEUE.md`.
- **`ADR-032` is `Accepted` but has never had a human review entry.** Noted, not
  blocking.
- **BLOCKED TASK (2026-10-16, coder): `REQ-SB-95-US-02-T02`** — built, both its
  locked ACs (`AC-02`, `AC-07`) verified green on nine AC-tagged tests, but the
  new save-time resolution gate makes one pre-existing `T01` test fail
  (`tests/test_action_artifact_kind.py::test_a_saved_action_round_trips_everything_the_operator_authored`
  saves against the catalogued-but-undeployed `vault-search` Skill). That file
  is outside `T02`'s `## Files to Modify`, so the fix needs a human to authorise
  it — `ESC-064`, `REVIEW-QUEUE.md`. The backend suite is red (`423 passed, 1
  failed`) until then, and `T03` builds directly on `T02`, so the sprint cannot
  advance past this. `T04` (`depends_on: [T01]` only) is the one task still
  reachable without the decision.

  **Resolved 2026-10-16** — the fixture was authorised and corrected in `T01`'s
  test file (commit `a82273d`), the suite went green, and `T02` is `Done`.
  `ESC-064` is closed.
- **FLAGGED TASK (2026-10-16, coder): `REQ-SB-95-US-02-T04` is `Done` with
  `gate: flagged`** — both its locked ACs (`AC-04`, `AC-05`) are verified green
  on eight AC-tagged tests plus a live `GET /artifacts` check, and the suite is
  `432 passed`. It is flagged because it *found* and deliberately did not fix an
  out-of-scope defect: `artifact_import_conflicts._MANAGER_BY_KIND` knows only
  four kinds and raises for anything else, and `preview_import`/`commit_import`
  run it over the whole manifest first — so the real import route still rejects
  a bundle containing an `action`, **or an `index`**, which has carried the same
  hole since 2026-09-06. Two-line fix, needs a task that owns the file;
  `ESC-065`, `REVIEW-QUEUE.md`. **Nothing is blocked by it** — `T03`, `T05` and
  `T06` are all reachable.

  **Resolved 2026-10-16** — `REQ-SB-95-US-02-T07` was minted to own that file
  and is `Done` (commit `b2b09fe`): `index` and `action` are registered in
  `_MANAGER_BY_KIND`, a mixed-kind `.sbf` previews and commits through the real
  import route, an unknown kind still raises naming all six accepted kinds, and
  the four new tests drive `preview_import`/`commit_import` rather than
  `_deploy_one` — suite `436 passed`. `ESC-065` is closed and `T04`'s gate is
  `clear` (its `status` was and remains `Done`).

---

## Out of Scope

- **Publication into agent context and enforcement at the call** — `SPRINT-088`.
  This story stops at a stored, validated, browsable, portable Action and changes
  no agent behaviour.
- Workflows (`SPRINT-089`) and entity resolution (`SPRINT-090`).
- The `FRAMEWORK_API` 7 → 8 bump — owed by `SPRINT-090` under this ordering
  (see Grouping Rationale).

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — no change needed; the sprint built exactly §Action Catalogue / §Adding a Kind / §Plugin-Contributed Actions as written, and `T06`'s screen is the final bullet of the first of those
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — none created by this sprint; `ADR-032`/`ADR-033` pre-date it
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Notes

**gate: clear 2026-10-16 — no product-owner trigger fired.** No assumption (the
eight cross-story edges above are quoted from the task files, not inferred from
story order); requirement finalised; no ADR created or changed by this pass; no
`ESCALATIONS.md` entry; **not oversized** (6 tasks, inside the confirmed band);
**no `Blocked` story**; **no cross-sprint dependency on this sprint's side** — it
has none; no contradictory inputs; **no ambiguity** — as the root of the spine
with three dependants, this story's placement first is forced by the graph, and
the only merge candidate that would not import a dependency breaks the sizing
ceiling. The story's own upstream `ADR-033` flag is carried forward above rather
than cleared here.

---

## Retrospective

<!-- Filled in by the CODER when status: Done. The coder drafts this section and
sets gate: flagged. The HUMAN then skims it, approves, and copies anything under
"Patterns to carry forward" and "Antipatterns to avoid" verbatim (or expanded)
into Implementation/Learnings.md — that is the cross-sprint index future sprints
read. The retro here is a sprint-level snapshot; Learnings.md is the permanent
record. The coder does NOT write Learnings.md directly. -->

### Sizing accuracy

- **Estimated:** ~6 tasks, `L` — **Actual:** 7 tasks, `L`, across three days
  (2026-10-16 → 2026-10-18), backend suite `423 → 476 passed` — **Takeaway:**
  **accurate, and the `L`-not-`M` call was right for the stated reason.** The
  seventh task (`T07`) was not underestimation of known work: it was minted
  mid-sprint to own a file `T04` found broken and correctly refused to touch. The
  sizing note's own argument — that adding a *kind* is cross-cutting, because
  `T04` alone reaches inventory, export, import, the secret scan and the resolver,
  all of which hard-code five kinds — is exactly where the extra task came from.
  **The reusable number: adding an artifact kind to this codebase costs ~7 tasks
  and surfaces ~3 files nobody assigned**, and that is the second time it has been
  measured (the `Index` precedent, 2026-09-06, is the first).

### What worked

- **The `Index` precedent used as a literal checklist, not an analogy.** `T04`
  worked through §Adding a Kind — the Measured Touch Points file by file; the
  architecture section had been written by reading those files rather than
  estimating them, so no touch point in it turned out to be wrong. Where the plan
  was incomplete it was incomplete *beyond* what `Index` had ever exercised
  (`artifact_import_conflicts`, which has been broken for `index` too since
  2026-09-06 and nobody noticed).
- **Three escalations, three different resolutions, zero improvisation.**
  `ESC-064` (a `T01` test fixture that `T02`'s new gate legitimately invalidated)
  → the human authorised the file. `ESC-065` (`_MANAGER_BY_KIND` knows four kinds)
  → a new task, `T07`, minted to own the file. `ESC-069` (`actions_router.py`
  belonged to no remaining task) → `T06`'s scope widened by one file, scoped to
  two named changes. Each one cost minutes and left a record naming the resolving
  artefact. The alternative — a coder reaching one file past its boundary "because
  it is obviously needed" — is how the boundary stops meaning anything.
- **Refusing at save time, and saying what did not resolve.** `ADR-032`'s central
  bet paid off visibly at the end: because the Manager's refusal names the skill,
  route or feature key, the screen needed *no error vocabulary of its own* — it
  renders the sentence verbatim. Two of `T06`'s six AC checks are satisfied purely
  by that decision having been taken three tasks earlier.
- **Verifying a screen against a deliberately isolated copy of the app.** `T06`
  ran its own backend (8011, scratch vault/data/Hermes paths) and its own Vite
  (5199) so it could install and uninstall a real plugin and break a real Action.
  Six other sessions were using this checkout at the time; none was disturbed, and
  the verification was *more* real than it would have been against the live
  install, where undeploying something to prove `AC-07` was never an option.
- **Composing plugin contributions at read time.** `T05`'s "never written to
  `data/Actions/`" makes "uninstalling a plugin removes its Actions" true by
  construction. `T06` then observed it for free: the plugin's row vanished at the
  same restart that broke the stored Action pointing at its route.

### What didn't work

- **Three separate `## Files to Modify` lists were each missing exactly one file,
  and the pattern is the same every time: the file that *joins two layers*.**
  `T02`'s list missed the `T01` test its new rule invalidated; `T04`'s and `T05`'s
  missed the API-layer file between a Manager change and a screen; `T06`'s missed
  the third `Record<ArtifactKind, …>` that widening a union obliges. The
  decomposer writes each list from the layer the task is *about*; nobody writes it
  from "what else reads this".
- **`FRAMEWORK_API` was deliberately left at 11 while `register_action` was added
  to the facade.** Correct for the sprint (bumping refuses every installed plugin
  until all are republished — four went dark on 2026-10-17 doing exactly that),
  but it means the facade and its version number now disagree, and the bump is
  owed by a task in a later sprint whose instruction is conditional. It works, and
  it is held together by a note in this file rather than by anything executable.
- **A screen's route list exists twice and the copies have already drifted** —
  `UI_FEATURE_KEYS` claims to be "verbatim from `App.tsx`" and, one task later,
  is not (`ESC-071`). The `http` kind got this right by reading the live route
  table; the `ui` kind reads a tuple maintained by hand.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Adding an artifact kind — budget ~7 tasks and expect ~3 unassigned files**
  — when a story adds a kind to a set that other modules enumerate, size it a
  notch above the task count and expect the escalations to be files that *join*
  layers (API between Manager and screen; a test pinning a shape; an exhaustive
  map over a widened union). Walking the architecture's touch-point list is
  necessary and provably not sufficient.
- **A refusal is UI copy — word it where the rule lives** — when business logic
  refuses, have it name the concrete thing that failed and have every surface
  render that sentence verbatim. The screen then needs no error vocabulary, and
  the message cannot drift from the rule. Measured here: two of six screen ACs
  needed no screen-side wording at all.
- **Verify a screen against a disposable install, not the live one** — a second
  backend on another port with scratch `VAULT_PATH`/`SECOND_BRAIN_DATA_PATH`/
  `HERMES_HOME_PATH`, plus a second Vite pointed at it, costs ~10 minutes and buys
  destructive state induction (install/uninstall a plugin, break an
  implementation) that is simply unavailable against the operator's own data —
  and it is the only safe option when other sessions share the checkout.
- **Make an invariant structural before making it enforced** — the exactly-one
  implementation picker is one radio group, so "a second choice clears the first"
  is a property of the markup that cannot regress, and the DOM assertion for it
  is meaningful rather than circular.
- **When a change would break a test that pins a shape, first ask whether the
  shape is wrong** — `plugin_id: null` on every row broke a pinned assertion in a
  file this task did not own; sending the key only where it means something was
  both more faithful to the Manager and needed no test edit at all. The
  out-of-scope test edit was the obvious move and the second-best one.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Writing `## Files to Modify` from the layer the task is about** — ask "what
  else reads this shape?" before locking the list: the router that serialises it,
  the test that pins it, the exhaustive map keyed by it. Three of this sprint's
  five escalations are that one omission.
- **Hand-maintaining a mirror of another build's facts** — `UI_FEATURE_KEYS`
  copies the front end's route table into a Python tuple and drifted within one
  task of being written. Where the live source is readable (as `app_route_table()`
  reads FastAPI's own routes), read it.
- **Writing a JSON file the app reads with PowerShell's
  `Out-File -Encoding utf8`** — it emits a BOM, `json.loads` rejects it, and
  `installed.json` then reads as a corrupt ownership record, which the plugin host
  correctly reports as "no plugin was loaded". Cost ~15 minutes of a verification
  run and, worse, briefly produced a *right-looking* `AC-07` result for the wrong
  reason: the Action did break, but because the record was unreadable rather than
  because the plugin was uninstalled. The AC was re-run after the file was
  rewritten without a BOM. Now a `MEMORY.md` constraint.
- **Trusting a state induction that produces the expected observation** — the
  BOM case above passed its assertion while the mechanism under test was not the
  mechanism that fired. Check that the *cause* happened (here: that the plugin
  actually loaded before it was removed), not only that the effect appeared.

### Open follow-ups

- **`ESC-071` (open)** — `/settings/actions` is not in `UI_FEATURE_KEYS`, so an
  Action cannot name this sprint's own new screen as its `ui` implementation.
  Filed in `ESCALATIONS.md` + `REVIEW-QUEUE.md`; needs either a one-line task or
  folding into `REQ-SB-95-US-03`.
- **`FRAMEWORK_API` 11 → 12** — owed by `REQ-SB-95-US-05-T02` (`SPRINT-090`)
  under this sprint's ordering decision; its instruction is conditional on
  `register_action` already existing, which it now does. Confirmation, not a
  decision. `REVIEW-QUEUE.md`, `T05`'s entry, item (2).
- **`ADR-032` has never had a human review entry** — noted in Dependencies at
  sprint start, still true at close, still not blocking.
- **`ESC-070` (resolved)** — no action; recorded because a task that widens a
  shared union owns every exhaustive map over it, which is a decomposition
  lesson rather than a defect.
