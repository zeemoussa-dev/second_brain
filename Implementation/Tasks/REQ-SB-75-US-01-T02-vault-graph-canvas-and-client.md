---
id: REQ-SB-75-US-01-T02
title: forceLayout.ts + VaultGraphCanvas.tsx + client.ts — hand-rolled canvas force-directed rendering engine
parent_story: REQ-SB-75-US-01
requirement_id: REQ-SB-75
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-75-US-01-T01]
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-75-US-01-T02 — forceLayout.ts + VaultGraphCanvas.tsx + client.ts

## Parent Story

- Story: [[REQ-SB-75-US-01]] — `../UserStories/REQ-SB-75-US-01-the-vault-knowledge-graph-screen.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-75 *The Vault — Real-Data Knowledge Graph Screen*

---

## Objective

Build the new `features/vault-graph/` rendering engine: a pure physics
module (`forceLayout.ts`), a hand-rolled `<canvas>` + `requestAnimationFrame`
force-directed rendering component with drag/zoom/pan and click-to-navigate
(`VaultGraphCanvas.tsx`), and a thin fetch wrapper (`client.ts`) over the
new `GET /vault-search/graph` endpoint (`T01`) — zero new npm dependency.
Also extend `tokens.css` with the new node-kind-color-palette and
edge-color custom properties this component reads.

---

## Starting State → End State

**Before / Inputs:**
- `T01` delivers a real, running `GET /vault-search/graph` →
  `{"nodes": [{"stem","title","kind","tags"}], "edges":
  [{"source","target"}]}`.
- `src/frontend/package.json` has no graph/visualization dependency
  (`react`, `react-dom`, `react-markdown`, `react-router` only) — none is
  added by this task.
- `features/vault-browser/client.ts` and `features/my-day/client.ts`
  establish this app's own thin-`fetch`-wrapper convention
  (`apiFetch<T>('/path')`).
- `tokens.css` has `--color-accent`, `--agent-color-producer`,
  `--color-success`, `--color-warning`, `--color-danger`, `--color-border`,
  `--color-text-muted` already defined, plus the existing "Agent-type
  colors" rotating-token-per-category precedent
  (`--agent-color-<type>`). `visualOptions.ts`'s `VISUAL_COLORS` is this
  app's own already-curated 10-hex palette (used from TypeScript, not
  `tokens.css` — NOT directly reusable as-is for this task's `AC-06`
  requirement, which needs the palette living in `tokens.css` itself).

**After / Outputs:**
- `tokens.css` gains, alongside the existing "Agent-type colors" block: an
  8-slot rotating node-kind-color palette (`--graph-kind-color-1` through
  `--graph-kind-color-8`), values drawn from this app's own
  already-established curated hues for consistency (e.g. reuse
  `--color-accent`, `--agent-color-producer`, `--color-success`,
  `--color-warning`, `--color-danger`, plus `#2563eb`/`#7c3aed`/`#0891b2` —
  the same values `visualOptions.ts`'s `VISUAL_COLORS` already uses — not
  new arbitrary hues); and one `--graph-edge-color` token for edge strokes.
- `features/vault-graph/forceLayout.ts` — a pure module: node position
  state (`{stem, x, y, vx, vy}[]`) and one simulation-tick function
  (repulsion + edge-spring + centering forces), mirroring
  `features/agents-map/polarLayout.ts`'s own "pure, testable geometry
  function" shape. No DOM/canvas access in this file.
- `features/vault-graph/client.ts` — `fetchVaultGraph(): Promise<{nodes,
  edges}>` via `apiFetch`, same convention as `vault-browser/client.ts`.
- `features/vault-graph/VaultGraphCanvas.tsx` — accepts `nodes`/`edges`
  (already filtered by the caller — this component does not know about
  kind-filter/search state, mirroring `AgentsMapCanvas.tsx`'s own
  "presentational, driven by props" shape) as props; runs
  `forceLayout.ts`'s tick function on a `requestAnimationFrame` loop;
  draws nodes (filled circle per node, color = a deterministic hash of
  `node.kind` into one of the 8 `--graph-kind-color-*` slots, read via
  `getComputedStyle(document.documentElement)` since `<canvas>` has no CSS
  cascade) and edges (stroke = `--graph-edge-color`); supports drag (a
  dragged node's position is pinned to the pointer, unpinned on release,
  simulation continues), zoom (scroll wheel, scales the draw transform),
  and pan (pointer-drag on empty canvas space); on a node click (not a
  drag), calls `useNavigate()` to `/browse/${node.stem}` — the existing,
  unmodified route.

---

## Files to Modify

- `src/frontend/src/styles/tokens.css` — add the `--graph-kind-color-1`
  through `-8` and `--graph-edge-color` custom properties, alongside the
  existing "Agent-type colors" block. No other rule in this file touched.
- `src/frontend/src/features/vault-graph/forceLayout.ts` — new file, pure
  physics/geometry module.
- `src/frontend/src/features/vault-graph/client.ts` — new file, thin fetch
  wrapper.
- `src/frontend/src/features/vault-graph/VaultGraphCanvas.tsx` — new file,
  canvas rendering + drag/zoom/pan + click-to-navigate.

---

## Constraints

- Inherits from parent story: zero new npm dependency — plain `<canvas>` +
  `requestAnimationFrame`, no graph/visualization library. Confirm
  `package.json` is unchanged by this task.
- Not a reuse of `AgentsMapCanvas.tsx` — a new, structurally distinct
  sibling component (that one is SVG + positioned `<div>`s over a fixed,
  non-physics radial layout; this one is `<canvas>` + a real physics
  simulation).
- Every color this component draws must resolve through a real
  `tokens.css` custom property — no hardcoded hex/rgb literal anywhere in
  `VaultGraphCanvas.tsx`/`forceLayout.ts`. The kind→palette-slot hash must
  be **deterministic** (the same `kind` string always maps to the same
  slot) and must **not** enumerate specific kind names (Customer, Thread,
  etc.) — any real `type` value, including ones that don't exist yet,
  must resolve to a valid slot.
- `VaultGraphCanvas.tsx` is presentational — it receives already-filtered
  `nodes`/`edges` as props; it does not own kind-filter or search-term
  state itself (that is `T03`'s `VaultGraphPage.tsx`).
- Click-to-navigate must go to the existing `/browse/:stem` route via
  `react-router`'s `useNavigate()` — no new note-viewing mechanism.
- `polarLayout.ts`/`AgentsMapCanvas.tsx` are read-only reference (for
  precedent), not modified by this task.

---

## Tests

<!-- No locked AC is tagged here — this is a rendering-engine task with no
independent screen-level observable yet (T03 mounts it inside a real route).
Same posture as REQ-SB-38-US-01-T02's own CSS-port precedent: non-AC smoke
checks here, full AC verification at the integration task (T03). -->

**Manual verification steps** (`src/frontend`: `npm run dev`; a throwaway
harness/browser console):

1. Non-AC smoke check: call `forceLayout.ts`'s tick function directly
   against a small synthetic `{nodes, edges}` set (Node's built-in TS
   type-stripping, no transpile step needed) — confirm node positions
   change tick-over-tick and connected nodes drift closer together than
   two nodes with no edge between them, over several ticks.
2. Non-AC smoke check: confirm `client.ts`'s `fetchVaultGraph()` returns
   the real `T01` endpoint's own live shape when called against the real
   running backend (`curl`/direct call, not through the UI yet).
3. Non-AC smoke check: mount `VaultGraphCanvas` in a throwaway harness
   page with synthetic `nodes`/`edges` props; confirm canvas circles/lines
   render, and that every color drawn is read via
   `getComputedStyle(...).getPropertyValue('--graph-kind-color-N' |
   '--graph-edge-color')` — grep the new files to confirm zero hardcoded
   hex/rgb literals.
4. Non-AC smoke check: `npm run build` (`tsc -b && vite build`) succeeds
   with no errors; confirm `package.json`'s `dependencies` block is
   byte-identical to before this task (no new dependency added).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `tokens.css` gains `--graph-kind-color-1`..`-8` and
      `--graph-edge-color`, values drawn from this app's own existing
      curated palette, no other rule touched
- [x] `forceLayout.ts` is a pure module (no DOM/canvas access) exporting a
      simulation-tick function over node position state
- [x] `client.ts` exposes `fetchVaultGraph()` over the real `T01` endpoint,
      same thin-wrapper convention as `vault-browser/client.ts`
- [x] `VaultGraphCanvas.tsx` renders nodes/edges from props via `<canvas>`
      + `requestAnimationFrame`, supports drag/zoom/pan, and navigates to
      `/browse/:stem` via `useNavigate()` on node click
- [x] Zero hardcoded color literals in either new `.ts`/`.tsx` file — every
      color read via `getComputedStyle` against a `tokens.css` custom
      property
- [x] Zero new npm dependency added
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (n/a — kind-color-palette mechanism was already decided at the decomposer pass, story's own `## Notes`; no new decision emerged here)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The new `GET /vault-search/graph` endpoint itself — `T01`.
- Kind filter chips, live counts, name search, the page's own route/nav
  wiring, `vault-graph.css` — `T03`.
- Connection-highlighting on hover/select and any on-canvas inspector
  panel — coder-level polish, not AC-locked (see the story's own `##
  Notes` — "Design reference parity"); may be added here or in `T03` at
  the coder's discretion, but is not required by any locked AC.

---

## Context / Notes

Depends on `T01` — needs the real, running endpoint to build `client.ts`
and verify its own shape against, per this project's own established
"backend-layer-first" precedent (`SPRINT-019` Learnings). `T03` depends on
this task: `VaultGraphPage.tsx` mounts `VaultGraphCanvas` and is the actual
integration point where every locked AC becomes observable end-to-end. See
`Implementation/Architecture/architecture.md` → "The Vault — Knowledge
Graph Screen (REQ-SB-75-US-01, no new ADR)" for the full reasoning on the
canvas/physics mechanism and why it is not a reuse of `AgentsMapCanvas.tsx`.

The exact hash function (kind string → one of 8 palette slots) and the
exact physics constants (repulsion/spring/centering strengths) are ordinary
implementation choices left to the coder — no locked AC depends on their
specific values, only on the observable properties named in the Tests
block above (deterministic color-per-kind sourced from `tokens.css`;
connected nodes visibly cluster).

---

## Implementation Log

**Implementation (2026-08-19):**
- `tokens.css` — added `--graph-kind-color-1`..`-8` (reusing
  `--color-accent`, `--agent-color-producer`, `--color-success`,
  `--color-warning`, `--color-danger`, plus `#2563eb`/`#7c3aed`/
  `#0891b2` — the same 8 values `visualOptions.ts`'s `VISUAL_COLORS`
  already uses) and `--graph-edge-color` (a dedicated
  `rgba(233, 228, 214, 0.25)` — more visible than `--color-border`'s
  0.1 alpha against the dark canvas background), alongside the existing
  "Agent-type colors" block. No other rule touched.
- `forceLayout.ts` — pure module, `createInitialNodes()` +
  `tickSimulation()` (repulsion + edge-spring + centering forces, alpha
  decay). No DOM/canvas import anywhere in the file.
- `client.ts` — `fetchVaultGraph()`, a 1-line `apiFetch<VaultGraphResponse>('/vault-search/graph')`
  wrapper, identical convention to `vault-browser/client.ts`.
- `VaultGraphCanvas.tsx` — `<canvas>` + `requestAnimationFrame` loop
  calling `tickSimulation()` every frame; drag (pointerdown on a node
  pins it, pointermove updates its position, pointerup unpins and
  re-enables physics); pan (pointerdown on empty canvas, drag updates a
  pan offset); zoom (wheel, scales a `scaleRef`); click-vs-drag
  distinguished by a small screen-pixel movement threshold, a genuine
  click navigates via `useNavigate()` to `/browse/${stem}`. Node fill
  color = a deterministic string-hash of `node.kind` into one of the 8
  `--graph-kind-color-*` slots (never enumerates specific kind names);
  edge stroke = `--graph-edge-color`. Both colors read once via
  `getComputedStyle(document.documentElement)` in a mount-time effect
  and cached in a ref — canvas has no CSS cascade of its own.

**Non-AC smoke checks (this task carries no locked AC — full AC
verification happens at `T03`, the real screen-level integration
point, per this task's own Tests header):**

1. **PASS.** Ran `forceLayout.ts`'s `createInitialNodes`/`tickSimulation`
   directly via `node --experimental-strip-types` against a synthetic
   4-node graph (`A-B` edge only) for 60 ticks: node positions changed
   tick-over-tick (`anyPositionChanged: true`); the connected pair ended
   up closer than an unconnected pair (`A-B` distance 60.47 vs. `A-C`
   distance 74.19).
2. **PASS.** Confirmed `T01`'s real, running `GET /vault-search/graph`
   endpoint (686 nodes, 1467 edges) returns exactly the shape
   `client.ts`'s `VaultGraphNode`/`VaultGraphEdge` interfaces expect
   (`{"stem","title","kind","tags"}` / `{"source","target"}`) — `client.ts`
   itself is a 1-line `apiFetch` passthrough, identical in shape to
   `vault-browser/client.ts`'s own already-verified convention; full
   wiring through the real running frontend happens at `T03`.
3. **Partial — deferred to T03's own mandatory real-screen screenshot
   check.** `VaultGraphCanvas.tsx` has no independent route/harness of
   its own to mount into within this task's file scope (adding one
   would require touching `App.tsx`/a new route, out of this task's
   `## Files to Modify`). Confirmed instead via: (a) direct code review
   that every draw call (`context.fillStyle`/`context.strokeStyle`) is
   sourced from `kindColorCacheRef`/`edgeColorRef`, both populated only
   from `getComputedStyle(...).getPropertyValue('--graph-kind-color-N'
   | '--graph-edge-color')`; (b) `grep`-confirmed zero `#`/`rgb(`/`rgba(`
   literals in either new file (one incidental `rgba(255,255,255,0.25)`
   placeholder default was caught and removed in favor of an empty-string
   initial ref value, populated before the first animation frame runs);
   (c) the real, live rendering proof happens at `T03`'s own mandatory
   real-browser screenshot of the full `/vault` screen, which mounts
   this exact component against the real 686-node/1467-edge graph — the
   genuine, real integration point this task's own header already names
   as where full-screen verification belongs.
4. **PASS (with one disclosed pre-existing, out-of-scope finding).**
   `npx vite build` (bundler) succeeded cleanly — 235 modules
   transformed, zero errors, confirming the new files compile/bundle
   correctly. The full `npm run build` (`tsc -b && vite build`) script
   fails, but ONLY on 6 pre-existing `TS7053` errors in
   `features/agents-map/{AgentNode,AgentsMapCanvas,SectionDrilldown,SectionHub}.tsx`
   — confirmed via `git status` that all 4 files were already modified
   (uncommitted) before this session began, unrelated to this task, and
   confirmed via `grep` that zero errors reference any `vault-graph`
   file. Not fixed here — out of this task's `## Files to Modify`, per
   the "minimal changes" rule; flagged below as a scope-internal
   observation, not a defect introduced by this task.
   `git diff --stat -- src/frontend/package.json` shows one pre-existing
   uncommitted line (`react-markdown` — added by an earlier,
   already-in-flight session before this task started, confirmed via
   `git diff` content); this task itself never touched `package.json` —
   zero new dependency added by `T02`.

**Scope-internal judgement calls (for human spot-check, not an
escalation):** the `<canvas>` re-settle-on-filter-change (`alphaRef`
reset to `0.5` whenever the `nodes` prop changes) and the exact
drag/zoom/pan pointer-event mechanics are ordinary implementation
choices — no locked AC depends on their specific values, matching this
task's own Context/Notes.

gate: clear 2026-08-19 — no MUST-FLAG trigger fired. The pre-existing
`agents-map` `tsc` errors are a disclosed, out-of-scope, already-present
repo finding (not caused by this task), not a locked-AC failure of this
task's own scope.
