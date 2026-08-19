---
id: REQ-SB-52-US-01
title: App-wide dark palette + real Plus Jakarta Sans / Marcellus typefaces (tokens.css swap only)
requirement_ids: [REQ-SB-52]
requirement_section: "REQ-SB-52: Agents Map Visual Redesign — SkillTree-Inspired Theme (Update, 2026-08-15 — scope widened to whole app, colors + fonts only)"
phase: P1
status: Done
gate: clear
sprint: SPRINT-047
created: 2026-08-15
updated: 2026-08-15
---

# REQ-SB-52-US-01 — App-wide dark palette + real Plus Jakarta Sans / Marcellus typefaces (tokens.css swap only)

## Story

**As a** Second Brain user
**I want** every screen (My Day, Settings, System Health, Agent Activity,
Browse & Search, Agents Map) to render in the dark SkillTree-inspired
color palette and typefaces, sourced from one shared `tokens.css`
swap rather than a per-screen restyle
**So that** the whole app reads as one visually consistent product ahead
of (and independent from) the still-in-progress Agents Map structural
reskin (starfield, glass cards, zoom toolbar, drill-down animations),
which stays scoped to a later pass

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-52: Agents Map Visual Redesign —
  SkillTree-Inspired Theme*, specifically the **`<!-- Update, 2026-08-15 -->`**
  block (the most recent, right before the requirement's closing `-->`).
  That update is a genuine, operator-confirmed scope widening: "Go full
  Sprint, Colors and fonts need to follow the prototype," confirmed via a
  direct clarifying question ("Whole app" over "Agents Map only"). This
  story specs **only** that update's own named scope: `tokens.css`'s
  `--color-*` custom properties + the font stack. Every other element the
  requirement's earlier `<!-- Update, 2026-08-14 -->` blocks describe
  (starfield, glass panels, zoom toolbar, `nodepop`/`treein`/`drawline`/
  `npulse`/`livepulse`/`hspin`/`hdrift`/`chevnudge`/`bpulse`, full-viewport
  canvas, node styling/positioning) is **explicitly excluded** from this
  story — it stays scoped to the Agents Map specifically and to the
  `html-prototype/agents-map-skilltree-exploration.html` exploration work,
  which the operator has directly deferred: "Leave the Rest till We
  finish the prototype." That later pass will need its own story once the
  exploration prototype and its `REVIEW-QUEUE.md` browser-sign-off items
  (the two still-open "Prototype update"/"Prototype rebuild" entries for
  `agents-map.html`/`agents-map-skilltree-exploration.html`) are resolved.

- **This reverses a previous deliberate decision** — `tokens.css`'s own
  standing comment records the app was switched FROM a dark theme TO the
  current light/green theme "per operator browser review" (2026-08-10).
  The PRD's own 2026-08-15 update block explicitly addresses this: "this
  update supersedes that reversal with a fresh, explicit operator
  instruction, not a silent flip-flop." Per the MUST-FLAG list, a bare
  reversal-of-a-prior-decision is not itself a listed trigger, and this
  one is already checked against contradictory-input concerns (trigger 7)
  in the PRD text itself, with the operator's fresh instruction resolving
  it, not leaving it open. It is **not** the reason this story is flagged
  below — the two items that are the reason are named there.

- **Grounded, not assumed:** confirmed by direct inspection of
  `src/frontend/src/styles/*.css` that every stylesheet other than
  `tokens.css` itself consumes color exclusively via `var(--color-*)` /
  `var(--agent-color-*)` — a search for literal hex colors across
  `src/frontend/src/styles/` returns matches only inside `tokens.css`'s
  own `:root` block (15 occurrences, all there). This confirms the
  requirement's own premise that a `tokens.css`-level swap cascades to
  every screen with zero per-screen CSS edits — this is not an assumption,
  it is a verified fact about the current codebase.

- **Font asset location, grounded not assumed:** the real WOFF2 files
  already exist at `html-prototype/fonts/PlusJakartaSans-Variable.woff2`
  and `html-prototype/fonts/Marcellus-Regular.woff2`, live-verified real
  (SIL Open Font License, legitimately redistributable — see
  `html-prototype/styles.css`'s own `@font-face` breadcrumb, ~line 1900).
  `src/frontend/public/` is this app's own existing convention for
  statically-served assets (`favicon.svg`, `icons.svg`, served at the
  site root by Vite with no build-time processing) — the natural, already-
  established location to copy the two font files into (e.g.
  `src/frontend/public/fonts/`), then reference via root-relative
  `@font-face src: url("/fonts/...")`, matching `html-prototype/styles.css`'s
  own `@font-face` recipe (variable-font weight range `200 800` for Plus
  Jakarta Sans, `font-display: swap`, no CDN/network fetch for either).

- **Already shipped — not re-specced here, for continuity only:** per
  `CHANGELOG.md`'s `[Unreleased]` section and `MEMORY.md`'s most recent
  Decision entry (both 2026-08-15), `KnowledgeBaseNode.tsx`'s dot-
  constellation redesign, `.hub-node`'s new ring treatment, and the
  KB↔Hub connector lines with traveling dots were already ported directly
  from the exploration prototype, operator-authorized outside `/spec`.
  Both entries explicitly note their colors were **adapted to this app's
  own existing tokens** (`--color-accent`/`--agent-color-*`/`--hub-color`),
  not hardcoded — meaning once this story's palette swap lands, those
  already-shipped elements pick up the new dark palette automatically
  through the same token indirection, with no rework. This story's
  Definition of Done does not depend on or re-verify that prior work.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: tokens.css's color palette is replaced app-wide, with zero per-screen CSS edits

```gherkin
Given tokens.css's --color-* custom properties currently define the
    light/green theme
When the dark palette is applied (--color-bg/--color-surface/
    --color-surface-raised/--color-border/--color-text/--color-text-muted/
    --color-accent/--color-accent-muted/--color-on-accent mapped from the
    PRD's --bg/--ivory/--ivory-2/--ink-2/--ink-3/--copper/--line/--glass
    values)
Then the app's page background, surfaces, borders, body text, muted text,
    and accent color all render as the new dark palette
  And no CSS file other than tokens.css needed to change for this to take
    effect
```
<!-- AC-ID: REQ-SB-52-US-01-AC-01 -->

### Scenario 2: Every existing screen visibly renders in the new dark palette

```gherkin
Given the palette swap from Scenario 1 has been applied
When the user visits My Day, Settings, System Health, Agent Activity,
    Browse & Search, and the Agents Map in turn
Then each screen's background, surfaces, text, and accent elements render
    in the new dark palette
  And every existing element on each screen (cards, buttons, form
    controls, tables, the agent detail panel, the sidebar navigation)
    remains visible and legible against the new background
  And no screen requires its own CSS change to achieve this
```
<!-- AC-ID: REQ-SB-52-US-01-AC-02 -->

### Scenario 3: Plus Jakarta Sans loads locally and applies as the app's primary sans font

```gherkin
Given the Plus Jakarta Sans WOFF2 file has been copied into the app's own
    static asset location and wired into a real @font-face rule
When any page in the app loads, with no network access to any external
    font CDN
Then body text and UI controls across the app render in Plus Jakarta Sans,
    not the previous system-font stack
  And the font glyphs are visibly present (not silently falling back to a
    system font)
  And no request to any external font host (e.g. fonts.googleapis.com,
    fonts.gstatic.com) is made
```
<!-- AC-ID: REQ-SB-52-US-01-AC-03 -->

### Scenario 4: Marcellus loads locally and is available as a serif token, applied to at least one real element

```gherkin
Given the Marcellus WOFF2 file has been copied into the app's own static
    asset location and wired into a real @font-face rule, exposed as a new
    --font-serif token
When the app renders
Then at least one real, visible UI element displays in Marcellus (the
    specific element is a coder judgement call at /implement-sprint,
    recorded in that task's own Implementation Log — the sidebar "Second
    Brain" wordmark, matching the Agents Map prototype's own redo-pass
    precedent, is a reasonable default if no stronger candidate emerges)
  And --font-serif is available for use by name on any future element
  And the font is not loaded but silently left unused anywhere (a real,
    observable application, not just a declared @font-face rule)
```
<!-- AC-ID: REQ-SB-52-US-01-AC-04 -->

### Scenario 5: Text remains readable across the whole app on the new dark background

```gherkin
Given the dark palette and both fonts have been applied app-wide
When the user views body text, muted/secondary text, form labels, and
    button text on My Day, Settings, System Health, Agent Activity,
    Browse & Search, and the Agents Map
Then --color-text and --color-text-muted both read clearly against
    --color-bg and --color-surface without requiring the user to guess at
    obscured content
  And interactive elements (buttons, links, form inputs, the currently-
    selected sidebar nav item) remain visually distinguishable from their
    surrounding surface
```
<!-- AC-ID: REQ-SB-52-US-01-AC-05 -->

### Scenario 6: Per-type agent colors and semantic status colors are visibly unchanged by this pass (regression guard)

```gherkin
Given the palette swap from Scenario 1 has been applied
When the user views the Agents Map's Worker/Producer/Expert agent nodes,
    and any success/warning/danger-colored element anywhere in the app
Then --agent-color-worker, --agent-color-producer, --agent-color-expert,
    --color-success, --color-warning, and --color-danger all keep their
    pre-swap hex values, unchanged by this story
  And no agent-type or status color was silently altered as a side effect
    of the accent/background/text token changes
```
<!-- AC-ID: REQ-SB-52-US-01-AC-06 -->

## Affected Screens

- All 6 real app screens share one CSS entry point (`tokens.css`), so this
  story is app-wide by construction rather than per-screen. No individual
  `html-prototype/*.html` file is edited by this story — the prototype
  files already carry the target palette/font values (extracted live from
  the reference site, `html-prototype/agents-map.html`/
  `agents-map-skilltree-exploration.html`/`styles.css`) that this story
  applies to the **real app's** `src/frontend/src/styles/tokens.css`.
- `src/frontend/src/styles/tokens.css` — the actual file changed:
  `--color-*` palette swap, `--font-sans` repoint, new `--font-serif`
  token, new `@font-face` rules.
- `src/frontend/public/fonts/` (new) — the two WOFF2 files copied in.
- `src/frontend/src/components/shell/Sidebar.tsx` (or its CSS) — the
  "Second Brain" wordmark gains `font-family: var(--font-serif)`
  (Scenario 4).

## Dependencies

- **Not blocked by:** the still-open Agents Map structural reskin
  (starfield, glass cards, zoom toolbar, drill-down animation set) — that
  work is explicitly out of scope here and awaits its own future story
  once `html-prototype/agents-map-skilltree-exploration.html` is signed
  off (see the two still-open `REVIEW-QUEUE.md` entries dated 2026-08-14).
- **Related to:** the already-shipped `KnowledgeBaseNode.tsx`/`.hub-node`/
  spoke-line port (`MEMORY.md` 2026-08-15 Decision, `CHANGELOG.md`
  `[Unreleased]`) — composes automatically via shared token indirection,
  no rework needed in either direction.
- **External:** none. Both font files already exist locally in
  `html-prototype/fonts/`; no download, license purchase, or network
  fetch required.

## Constraints

- The palette swap must be expressed as `--color-*` value changes on the
  **existing token names** in `tokens.css` — no new, differently-named
  color tokens, and no per-screen CSS file may need to change for the
  swap to take effect (verified premise, see Context).
- `--agent-color-worker`/`-producer`/`-expert` and `--color-success`/
  `-warning`/`-danger` are **not** touched by this story — the PRD's own
  2026-08-15 update block names only the 8 dark-palette values against
  the 3 core-token examples (`--color-bg`/`--color-surface`/`--color-text`/
  `--color-accent`, "etc."); it does not name a source value for status
  colors or confirm they're in scope. They keep their current hex values
  (Scenario 6) until a dedicated follow-on decides otherwise.
- No CDN or network font request of any kind — both fonts load from a
  file already committed to this repo, matching `html-prototype/styles.css`'s
  own established `@font-face` convention.
- Zero interaction/behavior change anywhere — this is a CSS-token-and-
  font-loading-only story. No component markup, routing, or data-fetching
  logic changes.
- The starfield background, glass detail cards, zoom toolbar, and the
  named drill-down animation set (`nodepop`/`treein`/`drawline`/`npulse`/
  `livepulse`/`hspin`/`hdrift`/`chevnudge`/`bpulse`) are explicitly out of
  scope — do not implement any of them under this story.

## Implementation Tasks

<!-- Decomposer's job at /plan-tasks — left empty here per template. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-52-US-01-T01 | frontend | Swap `tokens.css` dark palette + load Plus Jakarta Sans/Marcellus locally + apply `--font-serif` to one real element | `src/frontend/src/styles/tokens.css`, `src/frontend/public/fonts/` (new), one existing screen-CSS file for the Marcellus target (default `shell.css`) | `Implementation/Tasks/REQ-SB-52-US-01-T01-dark-palette-and-typeface-tokens.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — n/a, manual/live-browser verification is the correct mode per Pipeline.md (visual/network outcomes, no markup change)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **The animated starfield background** — deferred to the future Agents
  Map structural pass.
- **Translucent "glass" detail cards** — deferred to the future Agents
  Map structural pass.
- **The zoom toolbar** — deferred to the future Agents Map structural
  pass.
- **The named drill-down animation set** (`nodepop`/`treein`/`drawline`/
  `npulse`/`livepulse`/`hspin`/`hdrift`/`chevnudge`/`bpulse`) and any
  other Agents-Map-specific structural/visual element from the PRD's
  earlier 2026-08-14 update blocks — deferred to the future Agents Map
  structural pass, pending `html-prototype/agents-map-skilltree-
  exploration.html`'s own browser sign-off.
- **Re-tuning `--agent-color-worker`/`-producer`/`-expert` for contrast
  against the new dark background** — a real, disclosed follow-on
  concern (these hex values were originally darkened specifically for
  contrast on a *white* background per `tokens.css`'s own standing
  comment; against the new near-black background the same reasoning may
  need to run in reverse), but not solved here — the PRD's own update
  block calls this "a designer/coder judgment call, not re-litigated
  here." Flagging it for awareness, not gating this story's Definition
  of Done on it.
- **Re-tuning `--color-success`/`-warning`/`-danger`** for contrast
  against the new dark background — same disclosed-but-deferred category
  as above; the PRD's update block does not name source values for these,
  so they are left unchanged (see Constraints, Scenario 6).
- **Semantic ring-per-Type reordering** (Producer innermost, Worker
  middle, Expert outermost) — a separate, already-deferred follow-on per
  the PRD's own 2026-08-14 breadcrumb, unrelated to color/typography.

## Notes

**Prototype parity:**

This story does not touch any `html-prototype/*.html` screen file — it
applies already-extracted, already-prototyped color/font values to the
**real app's** `src/frontend/src/styles/tokens.css`. Treating the real
app's 6 screens as the "regions" being reconciled against the prototype:

- **My Day, Settings, System Health, Agent Activity, Browse & Search** —
  **Specced.** These screens have no SkillTree-specific prototype
  treatment of their own; they inherit the new palette purely through
  shared `tokens.css` tokens (Scenario 2). Their layout/structure is
  untouched.
- **Agents Map (overview canvas, agent detail panel)** — **Specced**
  (palette/font only, via the same token cascade) **and Deferred**
  (structural elements — see Non-Goals). The already-approved
  `agents-map.html` prototype's own palette values are exactly what this
  story sources (`--bg`/`--ivory`/`--ivory-2`/`--ink-2`/`--ink-3`/
  `--copper`/`--line`/`--glass`), but the still-open
  `REVIEW-QUEUE.md` browser-sign-off items for that prototype's own
  **structural** redesign (full-viewport canvas, starfield, node
  pop-in/glass/zoom-toolbar/edge-nav) remain open and unrelated to this
  narrower color/font story — do not treat this story's shipping as
  implicit sign-off on that pending structural work.
- **Sidebar "Second Brain" wordmark** — **Specced** (Scenario 4),
  reusing the exact placement the Agents Map redo-pass prototype already
  proposed for Marcellus (per `CHANGELOG.md`'s "designer REDO pass"
  entry) — but that placement itself was never independently confirmed
  by the operator (it sits inside the still-open, unresolved structural
  sign-off item), which is exactly why this story is flagged rather than
  auto-advanced (see below).

**Resolved 2026-08-15, `gate: flagged` -> `gate: clear`:** the two
material assumptions below were put directly to the operator via
`AskUserQuestion` and both are now settled, so this story auto-advances
to `/plan-tasks` rather than waiting in `REVIEW-QUEUE.md`.

1. **Marcellus's specific placement — resolved: "Let the coder decide
   when building it."** Scenario 4 no longer locks the sidebar wordmark
   as the required target; it requires only that Marcellus actually
   renders on at least one real element (not just declared-but-unused),
   with the specific element left as a scope-internal coder judgement
   call at `/implement-sprint`, recorded in that task's own
   Implementation Log per Pipeline.md hard rule 5. The sidebar wordmark
   remains a reasonable default suggestion, not a requirement.
2. **The `--color-surface`/`--color-surface-raised`/`--color-border`
   derivation from an 8-value source palette against a 9-token target
   set — resolved: "A lighter tint of --bg."** `--color-surface-raised`
   derives as `--bg` mixed lighter (e.g. `color-mix(in srgb, var(--bg)
   85%, var(--ivory) 15%)` or an equivalent literal hex one step up from
   `--bg`), consistent with how `--color-surface`/`--color-surface-raised`
   already relate to `--color-bg` in the current light theme (each a
   progressively lighter/raised tier, not a flat reuse of one existing
   source value for two different token roles). `--color-surface` itself
   should sit between `--color-bg` and `--color-surface-raised` on the
   same lightening curve (also a tint of `--bg`, lighter than `--bg` but
   less than `--color-surface-raised`) — `/plan-tasks` may pick the exact
   intermediate percentage; the ORDERING (bg < surface < surface-raised,
   all tints of the same base) is the locked part of this decision, not
   the literal percentage.

Both were genuine gaps in the PRD's own extraction, not invented scope —
now closed by direct operator confirmation rather than analyst guesswork.

**Not flagged for the theme reversal itself:** the MUST-FLAG list has no
"reverses a prior decision" trigger, and the PRD's own 2026-08-15 update
block already carries the operator's fresh, explicit, directly-confirmed
instruction ("Whole app," not "Agents Map only") superseding the
2026-08-10 light-theme decision — this is a resolved instruction, not an
open question, so it does not independently justify a flag here (trigger
7, contradictory inputs, does not fire: the two decisions are sequential
and both attributed, not simultaneously live and unreconciled).

gate: clear 2026-08-15 — both material-assumption triggers (Marcellus
placement; --color-surface/-surface-raised/-border derivation) resolved
directly by the operator via AskUserQuestion the same day; see the
"Resolved" note above for both answers.

**Architect review (2026-08-15, `/plan-tasks` step 1):**

Architecture scope: `Implementation/Architecture/architecture.md` §
"Frontend Application Architecture" > "Styling" (governed by
[ADR-010](../Architecture/ADR.md), Accepted 2026-08-11) — plain CSS,
`:root` custom-property tokens in `tokens.css`, no CSS Modules/Tailwind/
CSS-in-JS, cascading app-wide with zero per-screen edits. This is the
architecture the coder is bounded by for this story's task; no other
section applies (routing, data-fetching, and component-structure sections
of ADR-010/architecture.md are untouched by this story).

**No ADR created or changed.** Reasoning: ADR-010 already establishes the
exact mechanism this story operates entirely inside — a single
`tokens.css` `:root` block of `--color-*`/`--font-*` custom properties
that every screen consumes exclusively via `var(...)` (independently
re-confirmed via grep during this review, matching the story's own
Context claim word-for-word). This story:

- changes only the **values** of already-existing `--color-*` tokens
  (light/green → dark palette) — no new token names, no new mechanism;
- adds one new token, `--font-serif`, following the exact same
  additive-token convention `tokens.css`'s own standing comment already
  documents for `--agent-color-<type>` ("a new X is a new token here...
  never a layout change") — an application of an existing pattern, not a
  new one;
- adds `@font-face` rules and two static WOFF2 files under
  `src/frontend/public/fonts/` — native CSS, no new library/build-tool/
  dependency, using the already-established `public/` static-asset
  convention (architecture.md's "Data-fetching" section already names
  `public/` as this app's convention for `favicon.svg`/`icons.svg`).

No new tool, framework, dependency, or structural boundary is introduced,
and no `Accepted` ADR is contradicted, deviated from, or superseded
(ADR-010's routing/data-fetching/component-structure decisions are all
untouched; the 2026-08-10 light-theme choice recorded only as a comment in
`tokens.css` itself was never an ADR-level decision — a design-level value
choice, same category as this story's own reversal of it). This is
therefore a values-only change fully inside already-Accepted architectural
boundaries — MUST-FLAG trigger 3 (ADR created/changed) does not fire.
`architecture.md` itself needs no edit either: its existing "Styling"
section description (plain-CSS, single-`tokens.css`, app-wide cascade)
remains word-for-word accurate after this story ships — only the values
inside the described mechanism change, not the mechanism.

gate: clear 2026-08-15 (architect) — no ADR trigger fired; architecture.md
left unedited (already accurate); architecture scope recorded above.
Handing off to the decomposer.

**Decomposer AC-lock + task-out (2026-08-15, `/plan-tasks` step 2):**

All 6 scenarios locked as `REQ-SB-52-US-01-AC-01` through `AC-06`,
untightened beyond the AC-ID tag — the analyst's own wording was already
buildable and precise (unusually so, reflecting the two prior resolved
operator rounds). One task, `REQ-SB-52-US-01-T01`, covers the whole
story — the story's own scope (one CSS file's values + two static font
copies + one CSS rule for the Marcellus target) does not warrant a split;
no `depends_on` edges (no sibling tasks to depend on).

**Completing the 8-source-value -> 9-target-token mapping.** The story's
own resolved Note #2 covers `--color-surface`/`--color-surface-raised`
(tints of `--bg`, ordering locked, literal percentage left to
`/plan-tasks`) but is silent on `--color-accent-muted` and
`--color-on-accent` — the true remaining gap between the PRD's 8 named
source values and the app's 9 target `--color-*` tokens. Rather than
invent fresh values, the decomposer located the closest available
grounding: `html-prototype/styles.css`'s own `body.theme-skilltree` block
(~line 1360) — the CSS backing the same `agents-map.html`/
`agents-map-skilltree-exploration.html` reference this story's Context
already cites for the 8 core values — already carries a full, disclosed
`--color-*` alias set for exactly this palette. Concretely:

- `--color-bg: var(--bg)` = `#0E1118`
- `--color-surface: #171A22`, `--color-surface-raised: #1F2430` —
  reused verbatim from that block (both are lighter tints of `--bg`, in
  the locked bg<surface<surface-raised order per Note #2; the block's own
  comment discloses these two specifically as the prototype designer's
  own derived-not-extracted shades, so this task's Tests step verifies
  the ordering/legibility property the operator actually locked, not the
  literal hex as if it were an extracted "true" value).
- `--color-border: var(--line)` = `rgba(233, 228, 214, 0.1)`
- `--color-text: var(--ivory)` = `#E9E4D6`; `--color-text-muted:
  var(--ivory-2)` = `#B9B4A6`
- `--color-accent: var(--copper)` = `#C58B5F`
- `--color-accent-muted: rgba(197, 139, 95, 0.16)` — a mechanical alpha
  variant of `--copper`'s own already-extracted RGB triplet, not an
  independent judgement call.
- `--color-on-accent: #0E1118`  — literally `--bg` reused verbatim, not
  an independent judgement call.

This is grounding, not a fresh material assumption (MUST-FLAG trigger 1
does not fire): every value traces to either a directly-named PRD source
value, the operator's own Note #2 resolution, or a mechanical derivation
from one of those two categories, already recorded in a real repo file
predating this task. `--ink-2`/`--ink-3`/`--glass` (the 3 of the 8 PRD
source values with no corresponding existing app token slot) are
correctly left unmapped, per the Constraint against introducing new,
differently-named color tokens. Full mapping table and literal values are
in the task's own `## Context / Notes`.

**Verification mode:** manual (live default per Pipeline.md — this
story's ACs are inherently visual/network outcomes; frontend
structural-DOM testing does not apply since no markup changes).

**Status:** `Draft -> Ready`; all 6 ACs locked, all 6 have a tagged
verification step in `REQ-SB-52-US-01-T01`'s `## Tests`, and
`depends_on` is trivially acyclic (empty). `gate: clear` — no MUST-FLAG
trigger fired at this step (no new assumption beyond the grounded mapping
above, no ADR/architecture touch, no escalation, one clearly-sized task,
every AC verifiable, no contradiction, no genuinely unclear work).

gate: clear 2026-08-15 (decomposer) — story advanced to Ready; task
REQ-SB-52-US-01-T01 written at status: Ready in lockstep.

**Product-owner sprint grouping (2026-08-15, `/plan-sprints`):** the
only `Ready`, `sprint: ""` story found this pass; grouped alone into a
new single-story, single-task sprint (self-contained scope, no
`depends_on` edges, `P1`). See
`Implementation/Sprints/SPRINT-047-app-wide-dark-palette-and-typeface-swap.md`.

gate: clear 2026-08-15 (product-owner) — no triggers fired.

**Coder build + verify (2026-08-15, `/implement-sprint`):** Built the
sole task, `REQ-SB-52-US-01-T01`, entirely within its own `## Files to
Modify`. All 6 locked ACs verified live against the real running dev
server (`http://127.0.0.1:5173`) across all 6 real routes via a headless-
Edge CDP session — full AC-by-AC evidence (computed styles, network
requests, screenshots) recorded in the task's own Implementation Log.
Marcellus applied to the sidebar "Second Brain" wordmark, confirming the
story's own resolved Note #1 default suggestion — logged as the
scope-internal judgement call the story itself anticipated, not a new
assumption. One unrelated, pre-existing finding surfaced during live
verification: `/system-health` returns a real backend `500` from
`GET /system-health` (no backend file touched by this task) — noted for
visibility, does not block any of this story's own locked ACs.

gate: clear 2026-08-15 (coder) — story status: Ready -> Done; all 6
locked ACs verified live and PASS; no MUST-FLAG trigger fired during the
build.
