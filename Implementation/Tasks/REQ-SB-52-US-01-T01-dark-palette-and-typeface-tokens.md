---
id: REQ-SB-52-US-01-T01
title: Swap tokens.css to dark palette + load Plus Jakarta Sans / Marcellus locally
parent_story: REQ-SB-52-US-01
requirement_id: REQ-SB-52
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-15
updated: 2026-08-15
---

# REQ-SB-52-US-01-T01 — Swap tokens.css to dark palette + load Plus Jakarta Sans / Marcellus locally

## Parent Story

- Story: [[REQ-SB-52-US-01]] — `../UserStories/REQ-SB-52-US-01-app-wide-dark-palette-and-typeface-swap.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-52 *Agents Map Visual Redesign — SkillTree-Inspired Theme* (`<!-- Update, 2026-08-15 -->` block)

---

## Objective

Replace `tokens.css`'s `--color-*` values with the dark SkillTree palette,
load Plus Jakarta Sans and Marcellus from local WOFF2 files (no CDN), and
apply `--font-serif` to one real, visible element — with zero per-screen
CSS edits for the palette itself and zero markup/behavior changes.

---

## Starting State → End State

**Before / Inputs:**
- `src/frontend/src/styles/tokens.css` carries the current light/green
  `--color-*` palette and a system-font-only `--font-sans` stack; no
  `--font-serif` token exists.
- The two real WOFF2 files already exist at
  `html-prototype/fonts/PlusJakartaSans-Variable.woff2` and
  `html-prototype/fonts/Marcellus-Regular.woff2` (verified present).
- `src/frontend/public/` has no `fonts/` subfolder yet.
- No element anywhere in the app uses a serif font.

**After / Outputs:**
- `tokens.css`'s `--color-*` tokens carry the new dark-palette values (see
  mapping table below); `--agent-color-*` and `--color-success/-warning/
  -danger` are byte-identical to their pre-change values.
- `--font-sans` is repointed to lead with `"Plus Jakarta Sans"`; a new
  `--font-serif` token exists, leading with `"Marcellus"`.
- Two `@font-face` rules in `tokens.css` load both fonts from
  `/fonts/PlusJakartaSans-Variable.woff2` and `/fonts/Marcellus-Regular.woff2`
  — no network request to any external font host.
- `src/frontend/public/fonts/PlusJakartaSans-Variable.woff2` and
  `src/frontend/public/fonts/Marcellus-Regular.woff2` exist (copied
  verbatim from `html-prototype/fonts/`).
- Exactly one real, visible UI element carries `font-family:
  var(--font-serif)` (coder's choice — see Constraints).
- Every existing screen (My Day, Settings, System Health, Agent Activity,
  Browse & Search, Agents Map) renders the new dark palette and both
  fonts with zero edits to any CSS file other than `tokens.css` (plus the
  one file touched for the Marcellus target element).

---

## Files to Modify

- `src/frontend/src/styles/tokens.css` — `--color-*` value swap, `--font-sans`
  repoint, new `--font-serif` token, two new `@font-face` rules.
- `src/frontend/public/fonts/PlusJakartaSans-Variable.woff2` (new) — copy
  verbatim from `html-prototype/fonts/PlusJakartaSans-Variable.woff2`.
- `src/frontend/public/fonts/Marcellus-Regular.woff2` (new) — copy verbatim
  from `html-prototype/fonts/Marcellus-Regular.woff2`.
- **One** existing screen-scoped CSS file, to add a single `font-family:
  var(--font-serif)` rule for the coder's chosen Marcellus target element.
  Default suggestion: `src/frontend/src/styles/shell.css`, targeting
  `.sidebar-header h2` (the "Second Brain" wordmark) — matches the Agents
  Map redo-pass prototype's own precedent (see Context/Notes). The coder
  may pick a different single real element/file if a stronger candidate
  emerges while building; record whichever is chosen, and why, in this
  task's `## Implementation Log` per Pipeline.md hard rule 5 (scope-
  internal judgement call). CSS-only in whichever file is chosen — no
  `.tsx` markup edit is needed or permitted (the target element's markup
  already exists on every candidate screen).

---

## Constraints

- Inherits from parent story: no new/renamed color tokens; `--agent-color-*`
  and `--color-success/-warning/-danger` are untouched; no CDN/network font
  request; zero markup/routing/data-fetching changes; no per-screen CSS
  edit may be needed for the *palette* to cascade (Scenario 1/2).
- The Marcellus target-element edit (Scenario 4) is explicitly exempted
  from the "no per-screen CSS" constraint — it is inherently a single,
  named screen's own CSS file, but must still be CSS-only, one property,
  one file.
- `--color-*` mapping (source → target), all grounded in either the PRD's
  8 named source values, the story's own resolved Note #2, or a mechanical
  derivation from one of those two — see the story's own decomposer Notes
  breadcrumb and the table below. Do not deviate from these values.

### Color mapping table (apply verbatim)

| Target token (existing name in `tokens.css`) | New value | Source |
|---|---|---|
| `--color-bg` | `#0E1118` | PRD `--bg` |
| `--color-surface` | `#171A22` | Story Note #2 (tint of `--bg`, ordering locked); literal value reused from `html-prototype/styles.css`'s own `body.theme-skilltree` block |
| `--color-surface-raised` | `#1F2430` | Story Note #2 (tint of `--bg`, lighter than `--color-surface`); same source as above |
| `--color-border` | `rgba(233, 228, 214, 0.1)` | PRD `--line` |
| `--color-text` | `#E9E4D6` | PRD `--ivory` |
| `--color-text-muted` | `#B9B4A6` | PRD `--ivory-2` |
| `--color-accent` | `#C58B5F` | PRD `--copper` |
| `--color-accent-muted` | `rgba(197, 139, 95, 0.16)` | mechanical alpha variant of `--copper`'s own RGB |
| `--color-on-accent` | `#0E1118` | `--bg` reused verbatim (dark ink on the lighter copper accent) |
| `--agent-color-worker` / `-producer` / `-expert` | **unchanged** | Scenario 6 — do not touch |
| `--color-success` / `-warning` / `-danger` | **unchanged** | Scenario 6 — do not touch |

Font tokens:

```css
--font-sans: "Plus Jakarta Sans", -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
--font-serif: "Marcellus", Georgia, "Times New Roman", serif;
```

`@font-face` rules (add to `tokens.css`, root-relative `src`, matching
`html-prototype/styles.css`'s own established recipe):

```css
@font-face {
  font-family: "Plus Jakarta Sans";
  font-style: normal;
  font-weight: 200 800;
  font-display: swap;
  src: url("/fonts/PlusJakartaSans-Variable.woff2") format("woff2");
}

@font-face {
  font-family: "Marcellus";
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url("/fonts/Marcellus-Regular.woff2") format("woff2");
}
```

---

## Tests

**Manual verification steps:**

1. [REQ-SB-52-US-01-AC-01] After editing `tokens.css`, read the file and
   confirm `--color-bg`/`--color-surface`/`--color-surface-raised`/
   `--color-border`/`--color-text`/`--color-text-muted`/`--color-accent`/
   `--color-accent-muted`/`--color-on-accent` all match the mapping table
   above exactly. Confirm (e.g. via `git diff --stat` against the working
   tree) that no CSS file other than `tokens.css` was touched to achieve
   the palette swap itself (the one Marcellus-target CSS edit is a
   separate, disclosed exception scoped to AC-04, not part of this check).
2. [REQ-SB-52-US-01-AC-02] With the dev server running, load each of the
   6 real routes (`/`, `/my-day`, `/settings`, `/system-health`,
   `/agent-activity`, `/browse`) in a real browser (headless-Edge/CDP or
   equivalent) and screenshot each. Confirm each screen's background,
   surfaces, text, and accent render in the new dark palette, and that
   cards, buttons, form controls, tables, the agent detail panel, and the
   sidebar nav remain visible and legible.
3. [REQ-SB-52-US-01-AC-03] With the dev server running and the browser's
   Network domain observed (CDP or devtools), load a page and confirm: (a)
   a successful (200) request for `/fonts/PlusJakartaSans-Variable.woff2`;
   (b) computed `font-family` on `document.body` (or a representative text
   element) resolves to `"Plus Jakarta Sans"` as the first family, not a
   fallback; (c) zero requests to any host containing `fonts.googleapis.com`
   or `fonts.gstatic.com` across the whole page load.
4. [REQ-SB-52-US-01-AC-04] Confirm a successful (200) request for
   `/fonts/Marcellus-Regular.woff2`. Confirm the coder's chosen target
   element (recorded in the Implementation Log) has a computed
   `font-family` resolving to `"Marcellus"`, and that `--font-serif` is
   defined and readable via `getComputedStyle` on `:root` (or the target
   element) anywhere in the app.
5. [REQ-SB-52-US-01-AC-05] From the same 6 screenshots taken for AC-02,
   visually confirm body text, muted/secondary text, form labels, and
   button text are all clearly readable against their surface/background,
   and that buttons/links/inputs/the selected sidebar nav item remain
   visually distinguishable from their surrounding surface (not flattened
   into the background).
6. [REQ-SB-52-US-01-AC-06] Diff `tokens.css` before/after this task's
   change and confirm `--agent-color-worker`, `--agent-color-producer`,
   `--agent-color-expert`, `--color-success`, `--color-warning`, and
   `--color-danger` are byte-identical pre/post. Cross-check visually: the
   Agents Map's Worker/Producer/Expert node ring colors in the AC-02
   screenshot match their pre-change values.

**Automated tests:** `n/a — these ACs are visual/network outcomes (computed
CSS, font rendering, network requests); jsdom-based component tests cannot
observe them, and this task makes no markup change for structural DOM
tests to target. Manual/live-browser verification is the correct mode per
Pipeline.md, not a placeholder pending tooling.`

> On test failure: read the error, fix the root cause, re-run. After 3
> attempts, stop and report the failure to the user.

---

## Acceptance Criteria

- [x] REQ-SB-52-US-01-AC-01 — tokens.css palette swap, zero other CSS edits
- [x] REQ-SB-52-US-01-AC-02 — every screen renders the dark palette
- [x] REQ-SB-52-US-01-AC-03 — Plus Jakarta Sans loads locally, no CDN
- [x] REQ-SB-52-US-01-AC-04 — Marcellus loads and is genuinely applied
- [x] REQ-SB-52-US-01-AC-05 — text/interactive elements remain legible
- [x] REQ-SB-52-US-01-AC-06 — agent-type/status colors unchanged
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Starfield background, glass detail cards, zoom toolbar, and the named
  drill-down animation set — deferred to the future Agents Map structural
  pass (Non-Goals).
- Re-tuning `--agent-color-*` or `--color-success/-warning/-danger` for
  contrast against the new dark background — disclosed follow-on, not this
  task.
- Any `.tsx` markup, routing, or data-fetching change.
- Any `html-prototype/*.html` file edit.

---

## Context / Notes

- Architecture scope: `architecture.md` § "Frontend Application
  Architecture" > "Styling" (ADR-010, Accepted) — plain CSS, `:root`
  tokens in `tokens.css`, app-wide cascade, no CSS Modules/Tailwind/
  CSS-in-JS. This task stays entirely inside that mechanism: only token
  *values* change, plus one new additive token (`--font-serif`) following
  the same convention `tokens.css`'s own standing comment already
  documents for `--agent-color-<type>`.
- The `--color-surface`/`--color-surface-raised`/`--color-accent-muted`/
  `--color-on-accent` values in the mapping table are not independently
  invented by this task — they are reused verbatim from
  `html-prototype/styles.css`'s `body.theme-skilltree` block (~line
  1360), the CSS backing the same `agents-map.html`/
  `agents-map-skilltree-exploration.html` reference this story's own
  Context already cites for the 8 core PRD source values. See the
  parent story's decomposer Notes breadcrumb for the full reasoning.
- Marcellus target element: the sidebar "Second Brain" wordmark
  (`.sidebar-header h2` in `src/frontend/src/components/shell/Sidebar.tsx`,
  styled via `src/frontend/src/styles/shell.css`) is the reasonable
  default per the story's own resolved Note #1 and matches the Agents Map
  redo-pass prototype's own precedent (`.sidebar-header h2` in
  `html-prototype/styles.css`) — but this is explicitly a coder judgement
  call, not a locked requirement. Whichever element is chosen, record the
  choice and reasoning in this task's Implementation Log.
- `src/frontend/public/` is this app's established static-asset
  convention (already serves `favicon.svg`/`icons.svg` at the site root
  via Vite, no build-time processing) — copy both WOFF2 files there
  verbatim, no transformation needed.

---

## Implementation Log

**What was changed:**

- `src/frontend/src/styles/tokens.css` — replaced the 9 light/green
  `--color-*` values with the dark-palette mapping table verbatim; added
  two `@font-face` rules (`Plus Jakarta Sans` weight range `200 800`,
  `Marcellus` weight `400`) pointing at `/fonts/...woff2`; repointed
  `--font-sans` to lead with `"Plus Jakarta Sans"`; added a new
  `--font-serif` token leading with `"Marcellus"`. `--agent-color-worker/
  -producer/-expert` and `--color-success/-warning/-danger` left
  completely untouched (verified via `git diff -U0` — zero added/removed
  lines touch those tokens).
- `src/frontend/public/fonts/PlusJakartaSans-Variable.woff2` (new),
  `src/frontend/public/fonts/Marcellus-Regular.woff2` (new) — copied
  verbatim from `html-prototype/fonts/`; byte-size-confirmed identical
  (27,348 / 14,552 bytes respectively) to the source files.
- `src/frontend/src/styles/shell.css` — added one CSS-only rule,
  `.sidebar-header h2 { font-family: var(--font-serif); font-weight: 400;
  letter-spacing: 0.02em; }`. No `.tsx` markup edit.

**Scope-internal judgement call (Pipeline.md hard rule 5):** kept the
story's own default suggestion for the Marcellus target element — the
sidebar "Second Brain" wordmark (`.sidebar-header h2` in
`src/frontend/src/components/shell/Sidebar.tsx`, styled via `shell.css`).
No stronger candidate emerged while building: it is the one element on
every screen that reads as a literal brand/app name (the same reasoning
`html-prototype/styles.css`'s own `.theme-skilltree .sidebar-header h2`
precedent already used), and it is present identically on all 6 real
routes, so applying it there satisfies Scenario 4's "at least one real,
visible element" on every screen with a single, minimal, one-file CSS
change.

**Verification method:** live browser, real dev server (`http://127.0.0.1:5173`,
already running), driven via a minimal CDP WebSocket client (no
puppeteer/playwright) against a dedicated headless-Edge instance
(`msedge.exe --headless=new --remote-debugging-port=9333
--user-data-dir=<scratch>`), per this project's own established
Learnings pattern (SPRINT-032/033/036/038). Bundled project Node
(`tools/node/node.exe`) resolved via the real running dev-server
process's own executable path. All 6 real routes (`/`, `/my-day`,
`/settings`, `/system-health`, `/agent-activity`, `/browse`) were
navigated, screenshotted, and had `getComputedStyle`/`Network.
responseReceived` evidence captured. Headless Edge cleaned up via
specific-PID-tree kill afterward (port 9333 confirmed no longer
listening).

**AC-by-AC observed outcomes:**

- **AC-01** (tokens.css palette swap, zero other CSS edits) — PASS.
  Read `tokens.css` post-edit: all 9 target tokens match the mapping
  table exactly (`--color-bg: #0e1118`, `--color-surface: #171a22`,
  `--color-surface-raised: #1f2430`, `--color-border: rgba(233, 228,
  214, 0.1)`, `--color-text: #e9e4d6`, `--color-text-muted: #b9b4a6`,
  `--color-accent: #c58b5f`, `--color-accent-muted: rgba(197, 139, 95,
  0.16)`, `--color-on-accent: #0e1118`). `git diff --stat` against the
  working tree confirms only `tokens.css` and `shell.css` (the
  disclosed AC-04 exception) changed under `src/frontend/src/styles/`;
  pre-existing `agents-map.css`/`my-day.css` diffs predate this session
  (already `M` in git status before this task started) and are
  untouched by this task.
- **AC-02** (every screen renders the dark palette) — PASS. Screenshotted
  all 6 real routes live. Every screen shows the `#0e1118` background,
  `#171a22`/`#1f2430` surfaces, `#e9e4d6` text, and `#c58b5f` copper
  accent; cards, buttons, form controls, the Sections/Providers tables
  on Settings, the Agent Activity log rows, the Browse & Search tag
  chips/note cards, the sidebar nav, and the Agents Map hub/agent nodes
  all remain visible and legible. Confirmed via `getComputedStyle`:
  `document.body` background resolves to `rgb(14, 17, 24)` and color to
  `rgb(233, 228, 214)` on all 6 routes. One unrelated, pre-existing
  finding: `/system-health` shows a persistent "Loading..." state
  because `GET http://127.0.0.1:8001/system-health` returns a real
  `500 Internal Server Error` from the already-running backend — a
  pre-existing backend defect, not caused by this CSS/font-only task (no
  backend file is in this task's `## Files to Modify`, and none was
  touched). The dark palette itself renders correctly on that screen's
  header/loading text; the underlying data error is out of scope here.
- **AC-03** (Plus Jakarta Sans loads locally, no CDN) — PASS. Network
  log on every route's first load shows `GET /fonts/PlusJakartaSans-
  Variable.woff2` → `200` (subsequent same-session navigations show
  `304`, the browser's own local cache — still a same-origin, no-CDN
  response, not a fallback). `getComputedStyle(document.body).
  fontFamily` resolves to `"Plus Jakarta Sans", -apple-system, "Segoe
  UI", Roboto, Helvetica, Arial, sans-serif` (Plus Jakarta Sans first)
  on all 6 routes. Zero requests to any host containing
  `fonts.googleapis.com` or `fonts.gstatic.com` observed across all 6
  routes' full network logs.
- **AC-04** (Marcellus loads and is genuinely applied) — PASS. `GET
  /fonts/Marcellus-Regular.woff2` → `200` (then `304` on subsequent
  navigations) on every route. `getComputedStyle(document.querySelector(
  '.sidebar-header h2')).fontFamily` resolves to `Marcellus, Georgia,
  "Times New Roman", serif` (Marcellus first) on all 6 routes — visibly
  confirmed in every screenshot (the "Second Brain" wordmark renders in
  a distinct serif face, not the sans body font). `getComputedStyle(
  document.documentElement).getPropertyValue('--font-serif')` returns
  `"Marcellus", Georgia, "Times New Roman", serif` on every route,
  confirming the token is defined and readable app-wide, not just on the
  one target element.
- **AC-05** (text/interactive elements remain legible) — PASS. Visual
  review of all 6 screenshots: body text (`#e9e4d6` on `#0e1118`/
  `#171a22`) and muted text (`#b9b4a6`) are both clearly readable;
  Settings' form labels/inputs, Agent Activity's Success/Failed status
  badges, Browse & Search's tag chips and note-card list, and My Day's
  metric cards all read clearly against their surfaces. Interactive
  elements stay visually distinguishable from their surrounding surface:
  the selected sidebar nav item ("Agents Map"/"My Day"/etc.) shows a
  `--color-accent-muted` background with `--color-accent` (copper) text;
  primary buttons ("Create section", "Add provider") render solid
  copper; destructive actions ("Delete", "Remove") render in the
  unchanged `--color-danger` red, clearly set off from the dark surface.
- **AC-06** (agent-type/status colors unchanged) — PASS. `git diff -U0`
  on `tokens.css` shows zero added/removed lines touching
  `--agent-color-worker`, `--agent-color-producer`, `--agent-color-
  expert`, `--color-success`, `--color-warning`, or `--color-danger` —
  byte-identical pre/post. Visual cross-check on the Agents Map
  screenshot: Worker nodes render blue (`#2563eb`), Producer nodes
  render purple (`#7c3aed`), Expert nodes render pink/magenta
  (`#db2777`) — unchanged from their pre-swap values. The Agent Activity
  screenshot's green "Success" / red "Failed" badges also read as the
  unchanged `--color-success`/`--color-danger` hex values, still clearly
  legible against the new dark surface.

**Assumption/judgement calls recorded above (not MUST-FLAG triggers):**
the Marcellus target-element choice (AC-04) was a scope-internal
judgement call per Pipeline.md hard rule 5, already anticipated and
pre-authorized by the story's own resolved Note #1 ("let the coder
decide") — not a new material assumption requiring `gate: flagged`. No
other MUST-FLAG trigger fired: no new dependency, no shared-interface
change, no ADR deviation, no unanticipated file, no contradictory input.
The `/system-health` backend 500 is a pre-existing, out-of-scope
finding, noted for visibility, not a blocker on this task's own locked
ACs (all 6 of which are about the palette/font swap, independently
verified true regardless of that unrelated backend error).

gate: clear 2026-08-15 (coder) — all 6 locked ACs verified live and
PASS; one scope-internal judgement call (Marcellus target element,
pre-authorized by the story); one unrelated pre-existing backend finding
noted for visibility only.
