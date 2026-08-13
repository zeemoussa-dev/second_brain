---
id: BUGFIX-02-US-01
title: Agents Map — semantic-zoom overview + per-Section Agents Tree drill-down (BUG-002 fix, ported to the real app)
requirement_ids: [BUG-002]
requirement_section: "BUGS.md → BUG-002"
status: Done
gate: clear
gate_reason: "Resolved 2026-08-12 — T06's verification-methodology judgement call spot-checked and accepted (real DOM rect-intersection, stricter than the task's own draft heuristic, zero overlap confirmed by screenshot)."
sprint: "SPRINT-016"
created: 2026-08-12
updated: 2026-08-12
---

# BUGFIX-02-US-01 — Agents Map — semantic-zoom overview + per-Section Agents Tree drill-down (BUG-002 fix, ported to the real app)

## Story

**As a** Second Brain user viewing the Agents Map
**I want** every agent to always render within its own Section's visual
territory — as a small, unlabeled dot at the overview level regardless of how
many agents share that Section, revealing its label on hover/focus, and
letting me click a Section's Hub to zoom into that Section's own fully-labeled
"Agents Tree" drill-down
**So that** dense Sections (today: all 5 real seeded agents sitting in
"Technical") never visually spill into a neighboring Section's Hub, agents, or
title text, at any agent count

## Context

- Bug ledger: `BUGS.md` → `BUG-002` — "Agents Map: sections with 4+ agents
  visually spill into neighboring sections" (UI, Major, `Open` at triage
  time).
  - **Repro:** have (or move) 4+ agents into the same Section via Settings'
    Sections area or the Agent Settings surface's Section picker, then view
    the Agents Map — agent nodes and their labels render outside their own
    section's angular wedge, overlapping neighboring sections' nodes, Hub
    labels, and section-title text.
  - **Expected:** an agent always renders within its own section's visual
    territory, regardless of how many agents share that section or how many
    sections currently exist; labels never overlap another section's nodes
    or text.
  - **Actual (root cause, confirmed live in the real code):**
    `src/frontend/src/features/agents-map/layoutAgents.ts`'s
    `SECTION_ARC_SPAN_DEG` is a fixed 80° arc that every section's agents fan
    out across regardless of how many sections actually exist or how many
    agents share one section. With `N` sections evenly spaced around 360°
    (per `ADR-014` point 6, already ported), each section only owns `360/N`
    degrees (72° at today's real `N=5`) — a fixed 80° span already exceeds
    that before even accounting for agent count, and gets worse as more
    agents pile into one section. Confirmed via live browser screenshot
    against the real running app, 2026-08-11: all 5 real seeded agents
    currently sit in "Technical", visually spilling into "Customers"/
    "Products" territory with heavy label collision.
  - Read live (not guessed) as part of this story's authoring:
    `AgentNode.tsx` and `SectionHub.tsx` today always render every agent
    fully labeled and every Hub as a plain non-interactive `<div>` — neither
    the compact-dot-with-hover-label rendering mode nor the click-to-drill-
    down interaction described below exists yet in the real app.
- **The fix is already fully designed, approved, and live-browser-verified —
  this story's job is to port it into the real app, not to design it.**
  `REVIEW-QUEUE.md`'s "BUG-002 layout exploration" entry (full history) is
  the design record:
  - Four candidate layout approaches (A–D) were explored live/toggleable in
    `html-prototype/agents-map-exploration.html`; the operator picked
    **Option D — semantic zoom / drill-down** as the accepted direction
    (2026-08-11 update). Two refinements were then requested and built
    (drill-down Hub-sizing rebalance; a new overview entrance animation) and
    approved (2026-08-12 update).
  - The approved Option D design (+ both refinements) was then ported into
    the **canonical** `html-prototype/agents-map.html` /
    `html-prototype/agents-map.js` (2026-08-12 designer-pass update),
    replacing that screen's old fixed-position-only rendering. This is now
    the **design-of-record** for `BUG-002` — `agents-map-exploration.html`
    is kept only as historical comparison, no longer authoritative.
  - The canonical port was **approved and live-verified in a real browser**
    (2026-08-12, final update): the "Dense section (BUG-002 fix demo)" state
    — mirroring `BUG-002`'s own literal original repro (5 real agents, all
    in "Technical") — was confirmed live to keep all 5 agent dots visually
    contained inside Technical's own territory with no spillover, and
    clicking the Technical Hub was confirmed live to correctly zoom into its
    own fully-labeled "Agents Tree" drill-down with a correctly-sized Hub
    node at the center.
- **This story's real build target is the real application code, not the
  prototype:** `src/frontend/src/features/agents-map/layoutAgents.ts` (the
  containment-math half — a dynamic, section-count- and density-aware arc/
  compact-dot fallback, replacing the fixed `SECTION_ARC_SPAN_DEG = 80`) and
  `src/frontend/src/features/agents-map/AgentsMapCanvas.tsx` (plus its
  `AgentNode.tsx`/`SectionHub.tsx` children — the rendering/interaction
  half: always-compact dots with hover/focus label reveal at the overview
  level, a clickable Hub per Section, and that Section's own drill-down
  "Agents Tree" view). Per this project's own established convention (every
  other frontend story this session), the now-fully-approved
  `html-prototype/agents-map.html` / `html-prototype/agents-map.js` are the
  **design-of-record this story ports from** — the eventual `/plan-tasks`
  architect/decomposer and the coder should build against the real
  `.tsx`/`.ts` files named above, using the prototype's already-approved
  markup/class structure (`.agent-node--compact`, the Hub-as-button +
  `.explore-drilldown`/`.explore-zoom-overview`/`.zooming-out` zoom
  mechanism, the drill-down's own narrower `.hub-node` sizing, and the
  overview entrance animation) as the reference to reproduce in React, not
  as literal HTML to embed.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then) by the analyst; locked and
AC-ID-assigned by the decomposer at /plan-tasks (2026-08-12). One scenario,
one locked AC — this batch is BUG-002 only, and the two `When` clauses are
both facets of the same regression criterion (containment, then drill-down),
per the story's own Notes inviting either a single AC or a split — kept as
one AC here since both facets share one end-to-end live-browser verification
pass in the final integration task. -->

### Scenario 1: A dense Section's agents stay within its own territory at the overview level, and drill into that Section's own fully-labeled Agents Tree on click

```gherkin
Given a Section (e.g. "Technical") has 4 or more agents assigned to it in the
    real application — matching today's real seed data, where all 5 seeded
    agents sit in "Technical" (the "Dense section" case)
When the user views the Agents Map overview
Then every agent in that Section renders as a small, unlabeled compact dot
    positioned within that Section's own visual territory
  And no agent node or label visually overlaps a neighboring Section's Hub,
    agents, or section-title text — regardless of how many agents share the
    Section or how many Sections currently exist
  And hovering or giving keyboard focus to an agent dot reveals its label,
    without moving the dot outside its own Section's territory
When the user clicks that Section's own Hub
Then the Agents Map zooms into that Section's own dedicated "Agents Tree"
    drill-down view, spreading all of that Section's agents across the full
    360° of the drill-down, each one fully labeled at ordinary size
  And the Hub node rendered at the drill-down's center is visibly smaller
    than the agent nodes surrounding it
  And a "Back to Agents Map" control returns the user to the overview,
    restoring the compact/hover-reveal overview rendering unchanged
```
<!-- AC-ID: BUGFIX-02-US-01-AC-01 -->

## Affected Screens

- `html-prototype/agents-map.html` (+ its companion
  `html-prototype/agents-map.js`) — the **approved design-of-record** this
  story ports into the real app; not itself modified by this story. Already
  built and live-browser-verified (see `REVIEW-QUEUE.md`'s "BUG-002 layout
  exploration" entry, 2026-08-12 final update) — no further `/design` pass
  is needed before `/plan-tasks`.
- Real target (not a prototype file, listed here for traceability):
  `src/frontend/src/features/agents-map/AgentsMapCanvas.tsx`,
  `AgentNode.tsx`, `SectionHub.tsx`, `layoutAgents.ts` — this is the code
  the fix actually changes.

## Dependencies

- **Blocked by:** none. `ADR-014`'s dynamic N-section hub-angle math is
  already ported into `layoutAgents.ts` — this fix extends the same file's
  agent-fan-out logic, it does not depend on any not-yet-built story.
- **Related to:** `REQ-SB-18-US-01` (Dynamic Agent Sections) — the dynamic
  section count this fix's containment math must scale with (`N` sections,
  user-editable) is that story's own delivered mechanism, already `Done`
  (`SPRINT-011`).
- **External:** none new.

## Constraints

- The exact containment algorithm (dynamic angular budget per Section,
  density threshold before falling back to compact dots, drill-down layout
  math) is an architecture-level detail for `/plan-tasks`, not decided here
  — this story specs the observable outcome (never-spilling containment +
  working drill-down), not the exact geometry formula. The approved
  prototype's own JS/CSS (`agents-map.js`, `styles.css`'s additive BUG-002
  section) is the reference implementation to reproduce, not a literal
  spec to copy line-for-line into React.
- Must preserve `AgentNode.tsx`'s existing `onSelect` click-through to the
  Agent Detail Panel (`REQ-SB-13-US-01`) for a compact dot at the overview
  level — this fix changes how an agent dot looks/labels, not its existing
  click-to-open-detail behaviour. (Note: in the approved prototype, an
  overview-level agent dot's click target and a Hub's click target are
  visually distinct controls — the Hub opens the drill-down, the agent dot
  opens its detail panel; this distinction must be preserved, not merged.)
- Must not regress `REQ-SB-18-US-01`'s already-`Done` empty-Section handling
  (a Section with 0 agents) — the drill-down for an empty Section must
  render its own empty-state, matching the approved prototype's own
  "No agents in this section yet" pattern.
- Frontend-only change — no backend/API contract change. `layoutAgents.ts`
  already receives the real `GET /agents` + `GET /sections` shapes; this fix
  only changes how that data is turned into on-screen geometry/interaction.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| BUGFIX-02-US-01-T01 | frontend | `layoutSectionDrilldown()` full-360deg geometry + `DRILLDOWN_AGENT_RADIUS` | `layoutAgents.ts`, `polarLayout.ts` | `../Tasks/BUGFIX-02-US-01-T01-layout-section-drilldown-geometry.md` |
| BUGFIX-02-US-01-T02 | frontend | Port click-to-zoom / drill-down CSS subset from the approved prototype | `src/frontend/src/styles/agents-map.css` | `../Tasks/BUGFIX-02-US-01-T02-css-zoom-drilldown-port.md` |
| BUGFIX-02-US-01-T03 | frontend | `AgentNode.tsx` — optional `compact`/`radiusOverride` props | `AgentNode.tsx` | `../Tasks/BUGFIX-02-US-01-T03-agent-node-compact-radius-override.md` |
| BUGFIX-02-US-01-T04 | frontend | `SectionHub.tsx` — optional `onActivate`/`radiusOverride` props | `SectionHub.tsx` | `../Tasks/BUGFIX-02-US-01-T04-section-hub-onactivate.md` |
| BUGFIX-02-US-01-T05 | frontend | New `SectionDrilldown.tsx` — one Section's full-360deg Agents Tree | `src/frontend/src/features/agents-map/` | `../Tasks/BUGFIX-02-US-01-T05-section-drilldown-component.md` |
| BUGFIX-02-US-01-T06 | frontend | `AgentsMapCanvas.tsx` — wire `activeSectionId` drill-down state, always-compact overview, Hub-click zoom | `AgentsMapCanvas.tsx` | `../Tasks/BUGFIX-02-US-01-T06-agents-map-canvas-drilldown-wiring.md` |

- [x] The acceptance-criteria scenario passes (verified live against the
      real running app, using the real seed data's **"Productivity"**
      Section with 4 agents — the real assignment drifted from "Technical"
      since this story was drafted, but still today's actual `BUG-002`-
      shaped repro condition, 4+ agents sharing one Section, not a
      synthetic case — see `T06`'s Implementation Log)
- [x] Every Implementation Task above is complete (or explicitly dropped
      with reason) — all 6 (`T01`-`T06`) `Done`, none dropped
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) —
      manual mode per Pipeline.md until then
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] `BUG-002` flipped `In Sprint → Closed` in both `BUGS.md` and
      `BACKLOG.md`'s `## Bugs` mirror once this story is `Done`

## Non-Goals / Out of Scope

- Option C's (not the accepted direction) communication-affinity clustering
  or cross-Section affinity lines — not part of the approved Option D
  design, out of scope entirely.
- Any change to `REQ-SB-20`'s Hub routing logic — this fix is purely visual/
  layout; a Hub already exists and already conceptually "owns" its
  Section's agents, this story only changes how that is rendered and
  navigated.
- Re-theming Hub coloring or any other visual convention beyond what the
  approved prototype already settled (e.g. the prototype's own now-neutral
  Hub coloring, ported uniformly) — reproduce the approved design as-is, no
  new visual decisions.
- Replaying the overview entrance animation from the drill-down's own "Back
  to Agents Map" button — the approved design explicitly scoped the
  entrance animation to initial-load/state-switch/manual-replay only (noted
  in the prototype's own `playIntro()` comment as a future extension, not
  built there either); this story does not build that extension.

## Notes

**Prototype parity** (`html-prototype/agents-map.html`, the approved
design-of-record):

- **Specced** — overview-level always-compact agent dots with hover/focus
  label reveal, per-Section containment at any agent count: Scenario 1.
- **Specced** — Hub-as-button click → zoom-out transition → per-Section
  "Agents Tree" drill-down, fully labeled, correctly-sized Hub, "Back to
  Agents Map" control: Scenario 1.
- **Deferred (reason: out of scope, not a design gap)** — the overview
  entrance animation (flat row → hold → glide into circular position, KB
  grow-in), replayable via each state's own "Replay intro" button. This is
  part of the approved prototype but is a polish/motion affordance, not
  load-bearing for `BUG-002`'s own containment/drill-down defect — left for
  the architect to decide at `/plan-tasks` whether to fold into this
  story's scope or split into a separate follow-on story. Not asserted as
  a locked AC here since the operator's own bug repro/expected text
  (`BUGS.md`) only ever concerns containment, not entrance motion.
- **Deferred (reason: no design gap, not this bug)** — the empty-Section
  drill-down state and the "0 agents — empty" Hub sub-label are already
  covered by `REQ-SB-18-US-01`'s own `Done` empty-Section handling; this
  story only needs to not regress it (see Constraints), not re-spec it.
- No screen region in the approved prototype goes unspecced or
  Superseded — the whole screen (overview + drill-down + entrance
  animation) was reconciled above.

**Why one scenario:** per the triage-mode contract, one untagged Gherkin
scenario per bug in the batch — this batch is `BUG-002` only. The scenario's
two `When` clauses (overview containment, then drill-down-on-click) are both
facets of the same regression criterion `BUG-002` describes ("an agent always
renders within its own section's visual territory... labels never overlap
another section's nodes or text") — the decomposer may choose to split them
into separate locked ACs at `/plan-tasks` if that reads more verifiable, same
as `BUGFIX-01-US-01`'s precedent of splitting one analyst scenario into
multiple locked ACs.

gate: clear 2026-08-12 — no triggers fired: no material assumption was made
— the fix's design, approval, and live-browser verification are all already
recorded verbatim in `REVIEW-QUEUE.md`'s "BUG-002 layout exploration" entry
and the canonical `html-prototype/agents-map.html`/`.js`, not guessed by this
story; `BUG-002` is a finalised, non-`Draft` bug-ledger entry (trigger 2
doesn't apply — sourced from `BUGS.md`, not an unfinalised PRD requirement);
no ADR created/changed (analyst scope, and no new architectural boundary is
implied — this is a rendering/layout change within the already-`Accepted`
React/Vite frontend); no `ESCALATIONS.md` entry needed; the story is small
and well-bounded (one existing layout file's containment math + three
existing components' rendering/interaction, all with a fully worked reference
implementation already approved) — not oversized; no contradictory inputs
between `BUGS.md`, the real code, and the approved design record; the one
scoping call made (deferring the entrance animation as a Non-Goal rather than
folding it into this story) has one clearly-better answer given `BUG-002`'s
own repro/expected text never mentions entrance motion, not a genuinely
unclear or multiple-equally-valid choice — the architect may still choose to
fold it in at `/plan-tasks` without that being a re-flag of this story.

---

**Architect pass (`/plan-tasks` step 1), 2026-08-12:**

Architecture scope: §Frontend Application Architecture → Source structure
(the updated `AgentsMapCanvas.tsx`/`SectionHub.tsx`/`AgentNode.tsx`/
`layoutAgents.ts`/`polarLayout.ts` entries, plus the new `SectionDrilldown.tsx`
entry), §Agents Map — semantic zoom / drill-down containment fix
(`BUGFIX-02-US-01`, `BUG-002`) — both in
`Implementation/Architecture/architecture.md`.

Read the real current source (`layoutAgents.ts`, `AgentsMapCanvas.tsx`,
`AgentNode.tsx`, `SectionHub.tsx`, `polarLayout.ts`, `mockAgents.ts`,
`agentsApiClient.ts`, `AgentsMapPage.tsx`) and the approved
`html-prototype/agents-map.html`/`agents-map.js` (the "Dense section (BUG-002
fix demo)" state specifically) before deciding the concrete React port,
confirmed against the real code rather than assumed. Decisions recorded in
architecture.md, not repeated here in full — summary:

- Drill-down zoom/containment state (`activeSectionId` + a transient
  zoom-transition flag) is **local to `AgentsMapCanvas.tsx`**, plain
  `useState` — not lifted to `AgentsMapPage.tsx` (no sibling needs it) and
  not a new state-management mechanism.
- **New sibling component `SectionDrilldown.tsx`** (same "container composes
  small presentational children" shape `ADR-010` already established one
  view over) renders one Section's own full-360°, fully-labeled Agents Tree
  — Hub (via `SectionHub`, reused, no `onActivate`) at center, that
  Section's agents (via `AgentNode`, reused, `compact` omitted,
  `radiusOverride={DRILLDOWN_AGENT_RADIUS}`) spread around it, Hub->agent
  cluster-lines only, the established `.empty-state` pattern for a 0-agent
  Section, and a "Back to Agents Map" control.
- **`SectionHub.tsx`** gains an optional `onActivate` prop — supplied (a
  real `<button>`, opens the drill-down) at the overview call site, omitted
  (the original non-interactive `<div>`) inside `SectionDrilldown`. One
  component, two call sites — not two components.
- **`AgentNode.tsx`** gains two optional props: `compact` (applies the
  already-shipped-but-unused `.agent-node--compact` CSS modifier
  unconditionally at the overview level — this *is* Option D: always
  compact, never a density threshold) and `radiusOverride` (lets
  `SectionDrilldown` place a node at a fixed radius instead of
  `polarLayout.ts`'s Type-keyed `RING_RADIUS`). `onSelect` click-through to
  `AgentDetailPanel` is unchanged and reused as-is at both call sites — the
  story's own Constraint against regressing it is satisfied by construction
  (same component, same prop), not by separately re-wiring it.
- **`layoutAgents.ts`** gains a new sibling function, `layoutSectionDrilldown()`
  — a full-360°-spread geometry, deliberately **not** a branch inside the
  existing `layoutAgents()`/`SECTION_ARC_SPAN_DEG` fan-out, since conflating
  the overview's per-Section wedge model and the drill-down's full-circle
  model into one function/one constant is exactly `BUG-002`'s own root-cause
  shape. `polarLayout.ts` gains a co-located `DRILLDOWN_AGENT_RADIUS`
  constant alongside its existing `RING_RADIUS`/`HUB_RADIUS`/
  `BOUNDARY_RADIUS`.
- **CSS:** `agents-map.css` gains the prototype's already-written
  `.explore-zoom-overview`/`.zooming-out`/`.explore-drilldown`/
  `.explore-drilldown .hub-node` rules (ported verbatim, class names
  unchanged, per `ADR-010`'s "no renaming/translation step" convention).
  `.agent-node--compact` needs no porting — it already exists in this
  file (`ADR-010`'s own "ready to apply, not yet instantiated" primitive).
  The entrance-animation-only rules (`.agent-node--intro-move`,
  `.agents-intro-fade`, `@keyframes kbGrowIn`) are **not** ported — the
  story's own Non-Goals already scoped the entrance animation out, and
  nothing in `BUG-002`'s repro/expected text concerns it; confirmed, not
  reopened, per the story's own note inviting the architect to make this
  call.

**No ADR created or changed.** Every decision above is ordinary component/
prop/function decomposition within `ADR-010`'s already-`Accepted`
"container + small presentational children + one shared geometry module"
shape and `ADR-014` point 6's already-`Accepted` N-section-generic layout —
no new tool, framework, state-management library, or structural boundary.
Nothing above contradicts any `Accepted` ADR, the PRD, or a `MEMORY.md`
constraint. `gate: clear 2026-08-12` carries forward unchanged from the
analyst pass above — trigger 3 (ADR created/changed) did not fire, so no
`REVIEW-QUEUE.md` entry was written by this pass. Hands off to the
decomposer next, within this same `/plan-tasks` run.

---

**Decomposer pass (`/plan-tasks` step 2), 2026-08-12:**

Locked the analyst's single Gherkin scenario as `BUGFIX-02-US-01-AC-01`
(tightened wording only: an explicit "restoring the compact/hover-reveal
overview rendering unchanged" clause was added to the final `Then`, since
the story's own Constraint against regressing the overview's rendering on
Back needed an observable, testable assertion, not just an implicit
expectation) — kept as one AC, not split, since both `When` facets
(containment, then drill-down) share one end-to-end live-browser
verification pass in `T06`, per the story's own Notes explicitly allowing
either choice.

Created 6 flat-root tasks, `BUGFIX-02-US-01-T01`..`T06` (all `frontend`,
`phase: P1`), covering exactly the architect's named files:
`layoutAgents.ts`/`polarLayout.ts` (`T01` — `layoutSectionDrilldown()` +
`DRILLDOWN_AGENT_RADIUS`), `agents-map.css` (`T02` — the click-to-zoom/
drill-down CSS subset ported verbatim from `html-prototype/styles.css`,
plus its own `@keyframes fadeIn` dependency, confirmed absent from the real
app's CSS and added alongside), `AgentNode.tsx` (`T03` — `compact`/
`radiusOverride`), `SectionHub.tsx` (`T04` — `onActivate` plus a
`radiusOverride` prop added by this decomposition — see below),
`SectionDrilldown.tsx` (`T05` — new component), `AgentsMapCanvas.tsx`
(`T06` — final integration: local `activeSectionId`/`zoomTargetSectionId`
state, always-`compact` overview dots, Hub-click zoom wiring). `depends_on`
graph: `T01`/`T02`/`T03`/`T04` have no dependencies (independent building
blocks); `T05` depends on `T01`+`T02`+`T03`+`T04`; `T06` depends on
`T02`+`T03`+`T04`+`T05` — acyclic, confirmed by inspection (a strict DAG,
4 roots -> `T05` -> `T06`).

**One task-level implementation-mechanism decision made, not flagged:** the
architect's Notes describe `SectionDrilldown`'s Hub as rendered "via
`SectionHub`, reused... at center" without naming a mechanism, and the
approved prototype's own drill-down markup places the Hub at the canvas's
literal center (`top:50%; left:50%`), not at the overview's
`hubAngleDeg`-derived position `SectionHub` computes today. Reusing
`SectionHub` unmodified would have placed the drill-down's Hub off-center
(at its overview position), visually inconsistent with agents spread around
the canvas's true center — a real defect against the story's own locked AC
text ("the Hub node rendered at the drill-down's center"). Resolved by
giving `SectionHub` (`T04`) a `radiusOverride` prop mirroring `AgentNode`'s
own `T03` prop of the same name/shape (`polarToCartesian(0, anyAngle)`
collapses to the exact canvas center) — a small, symmetric, low-risk
implementation-mechanism choice with one clearly-better answer given the
approved design's own literal rendering, not a genuine ambiguity or
multiple-equally-valid fork (trigger 8 does not apply); logged here per
Pipeline.md's "scope-internal judgement calls are not escalations" rule,
same as the precedent this project already set at `REQ-SB-18-US-01-T06`'s
own section-title-accent fix.

**Gate checks:** every AC is locked (the one `AC-01`); it has a matching
`[BUGFIX-02-US-01-AC-01]`-tagged live-browser verification step in `T06`'s
`## Tests` (step 1); `depends_on` is acyclic (confirmed above). Story
`status:` advances `Draft -> Ready`; all 6 tasks are written at
`status: Ready` in lockstep, per Pipeline.md's "task status moves in
lockstep with the story" rule.

`gate: clear 2026-08-12` — no MUST-FLAG trigger fired this pass: no
material assumption filled a real gap (the one implementation-mechanism
choice above has a single clearly-correct answer, not a guess); `BUG-002`
is a finalised, non-`Draft` ledger entry; no ADR created/changed by this
pass; no `ESCALATIONS.md` entry needed; all 6 tasks are single-file-or-
single-new-file, one-working-session-sized (confirmed against this
project's own `REQ-SB-18-US-01-T05`/`T06` frontend-task precedent, similar
scope); no contradictory inputs; the one AC-splitting choice available
(one AC vs. two) had a clearly-better answer given the shared end-to-end
verification pass, not a genuine multiple-equally-valid fork. No
`REVIEW-QUEUE.md` entry written. Eligible for `/plan-sprints` (ungrouped,
`sprint: ""`).

---

**Coder pass (`/implement-sprint SPRINT-016`), 2026-08-12:**

All 6 tasks (`T01`-`T06`) built and verified in dependency order
(`T01`/`T02`/`T03`/`T04` → `T05` → `T06`), each `status: Done`. `AC-01`
verified live end-to-end in `T06` against the real running app (backend
port 8001, frontend port 5173, both already running and reused, not
restarted) via headless-Chrome-over-CDP (this project's own established
zero-dependency frontend-verification pattern) — full evidence, including
screenshots and rect-level DOM measurements, is in `T06`'s own
Implementation Log; not repeated here.

**Real-data drift, not a defect:** the real `.second-brain/
agent_sections.json` assignment has drifted since this story/`BUG-002`
were authored (then: all 5 agents in "Technical"; now: 4 in "Productivity",
1 in "Customers") — verification used "Productivity" as the real dense
Section instead, since it already satisfies the locked AC's actual
condition ("a Section... has 4 or more agents," "Technical" being the
story's own illustrative example only). No `PATCH /agents/{id}`
reassignment was needed or performed.

**One scope-internal judgement call, flagged on `T06` (not an
escalation):** `T06`'s own manual-test wording used a "nearest-hub-center
distance" heuristic to operationalize containment, which does not
literally hold for 2 of the real Productivity Section's 4 agents — traced
to the pre-existing, explicitly-out-of-scope global (not per-Section) ring
radii this story's own `T01` forbids touching, not to any defect in this
story's actual diff. Re-verified against the locked AC's own literal text
("no agent node or label visually overlaps...") via direct DOM
rect-intersection: zero real overlaps found, confirmed visually via
screenshot. `gate: flagged` on `T06` and this story for human spot-check;
noted as an "Open follow-up" in `SPRINT-016`'s Retrospective (a possible
future per-Section-scoped ring-radius tightening), not built here.

`BUG-002` flipped `In Sprint -> Closed` in both `BUGS.md` and `BACKLOG.md`'s
`## Bugs` mirror, in the same touch as this story's own `Done` transition.
Story `status:` advances `Ready -> Done`.
