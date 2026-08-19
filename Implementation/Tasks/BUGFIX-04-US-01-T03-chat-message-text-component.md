---
id: BUGFIX-04-US-01-T03
title: New shared ChatMessageText component wrapping react-markdown
parent_story: BUGFIX-04-US-01
requirement_id: BUG-025
type: frontend
status: Done
gate: clear
gate_reason: ""
depends_on: []
created: 2026-08-19
updated: 2026-08-19
---

# BUGFIX-04-US-01-T03 — New shared `ChatMessageText` component wrapping `react-markdown`

## Parent Story

- Story: [[BUGFIX-04-US-01]] — `../UserStories/BUGFIX-04-US-01-cockpit-chat-addressing-input-and-rendering-fixes.md`
- Requirement: `BUGS.md` → `BUG-025` (bugfix story; no PRD requirement anchor)

---

## Objective

Build the shared foundation `BUG-025`'s fix needs before either real chat
surface can consume it: add `react-markdown` as a real dependency and a
new `src/frontend/src/components/ChatMessageText.tsx` component, wired
exactly per `ADR-050`. This task has no consumer yet (`T04` wires it into
`Cockpit.tsx`/`AgentDetailPanel.tsx`) — it does not itself satisfy
`AC-04`, which needs a real chat surface actually rendering through it.

---

## Starting State → End State

**Before / Inputs:**
- `src/frontend/package.json` lists `react`, `react-dom`, `react-router`
  only — no markdown/rich-text dependency exists in this codebase today.
- `src/frontend/src/components/` — confirm by direct listing whether this
  directory exists yet; if not, this task creates it (the first
  cross-feature shared component at this location, per `ADR-050`'s own
  Consequences).

**After / Outputs:**
- `src/frontend/package.json` gains `react-markdown` (current stable
  v9.x) as a real dependency — no `remark-gfm`, `rehype-raw`, or
  `rehype-sanitize` added.
- `src/frontend/src/components/ChatMessageText.tsx` exports a
  `<ChatMessageText text={string} />` component that renders `text`
  through `react-markdown` with ZERO additional remark/rehype plugins and
  no custom `urlTransform` override (the library's own built-in
  `defaultUrlTransform` is left as-is).

---

## Files to Modify

- `src/frontend/package.json`:
  1. Add `"react-markdown"` to `dependencies` (current stable v9.x —
     pin-then-verify-at-real-`npm install`-time, this project's
     established `react-router`/`langgraph` pattern per `ADR-050`'s own
     Consequences).
- `src/frontend/src/components/ChatMessageText.tsx` (new file):
  ```tsx
  import ReactMarkdown from 'react-markdown';

  export interface ChatMessageTextProps {
    text: string;
  }

  /** Renders chat message text (user- or agent-authored, symmetric — no
   * speaker/role branch) as formatted rich text via react-markdown, zero
   * additional remark/rehype plugins (ADR-050): CommonMark's own default
   * feature set (bold/italic, bulleted/numbered lists, links, inline/block
   * code, headings) already covers the operator-resolved markdown subset.
   * Default-safe by omission -- react-markdown never invokes
   * dangerouslySetInnerHTML and never parses raw HTML embedded in `text`
   * unless the rehype-raw plugin is explicitly added, which this
   * component does not do; link/image URLs pass through react-markdown's
   * own built-in defaultUrlTransform unmodified. */
  export function ChatMessageText({ text }: ChatMessageTextProps) {
    return <ReactMarkdown>{text}</ReactMarkdown>;
  }
  ```

---

## Constraints

- Inherits from parent story — no raw `dangerouslySetInnerHTML` of
  unsanitized content (structurally true here: `react-markdown` with zero
  plugins never uses it).
- No additional remark/rehype plugin package (`remark-gfm`, `rehype-raw`,
  `rehype-sanitize`) — per `ADR-050`'s own Decision; a future story may
  add `remark-gfm` for GFM features, not this task.
- No custom `urlTransform` override — `react-markdown`'s own
  `defaultUrlTransform` (strips non-`http`/`https`/`mailto`/`tel` link
  schemes) is left as the library's own default.
- This component is presentational only — no fetch/state/side effects of
  its own; `text` is the only prop.

---

## Tests

<!-- No locked AC is tagged here -- the component alone, with no consumer
wired in yet, does not itself satisfy AC-04 (which requires a real chat
surface rendering through it). This is a non-AC-tagged smoke check
confirming the component itself is correctly wired before T04 consumes
it. -->

**Manual verification steps:**

1. (Not a locked AC — smoke-verifies the component itself in isolation,
   before any real consumer exists.) After `npm install` picks up the new
   `react-markdown` dependency, render `<ChatMessageText text={"**bold**
   and a list:\n- one\n- two"} />` in isolation (e.g. a throwaway
   temporary mount in `main.tsx`, or via the dev server's own React
   DevTools/inspect once mounted anywhere reachable) and confirm the
   rendered DOM contains a real `<strong>bold</strong>` element and two
   real `<li>` elements — no literal `**` or `- ` characters visible in
   the rendered text content. Remove any throwaway mounting code used
   for this check before finishing the task (this component's own file
   itself is the only permanent output).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `react-markdown` (current stable v9.x) added to `src/frontend/package.json`'s `dependencies`, no additional remark/rehype plugin package added
- [x] `src/frontend/src/components/ChatMessageText.tsx` exists, exports `ChatMessageText({ text }: { text: string })`, wraps `react-markdown` with zero plugins and no custom `urlTransform`
- [x] `npm install` completes cleanly against this project's real Node/Vite toolchain with the new dependency present
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Wiring `ChatMessageText` into `Cockpit.tsx` or `AgentDetailPanel.tsx` — that is `T04`.
- Any GFM feature (tables, strikethrough, task lists, footnotes) — explicitly deferred per `ADR-050`.
- A second sanitizer layer (`rehype-sanitize`/DOMPurify) — explicitly not added per `ADR-050`'s own "considered, not added this pass" reasoning.

---

## Context / Notes

Full reasoning, alternatives considered, and consequences:
`Implementation/Architecture/ADR.md` → `ADR-050`. Module-shape summary:
`Implementation/Architecture/architecture.md` → "Chat Rich-Text Rendering
— `react-markdown`". This is the first markdown/rich-text dependency in
this codebase, and the first component shared across features from a
top-level `components/` location (`Cockpit.tsx` lives under
`features/cockpit/`, `AgentDetailPanel.tsx` under `features/agents-map/`)
— per `ADR-050`'s own Consequences, this is decomposer/coder latitude,
not a new architectural layer.

---

## Implementation Log

**Coder pass, 2026-08-19.** Implemented exactly as specced — no deviation.

- `src/frontend/package.json`: added `"react-markdown": "^9.1.0"` to
  `dependencies`. No `remark-gfm`/`rehype-raw`/`rehype-sanitize` added.
- `src/frontend/src/components/` did not exist yet — created (first
  cross-feature shared component location, per `ADR-050`).
- `src/frontend/src/components/ChatMessageText.tsx`: new file, exports
  `ChatMessageText({ text }: { text: string })`, wraps `<ReactMarkdown>`
  with zero plugins, no custom `urlTransform`, verbatim per the task spec.

`npm install` (`src/frontend`) completed cleanly: "added 82 packages...
found 0 vulnerabilities". `npm ls react-markdown` confirms the resolved
version is `react-markdown@9.1.0` — current stable v9.x, matches the task's
own pin-then-verify-at-real-install convention.

**Smoke verification (not a locked AC — no consumer wired yet, `T04`'s own
scope):** verified as part of `T04`'s own real-browser DOM checks once the
component was actually wired into a real chat surface (`Cockpit.tsx`,
confirmed live: `**bold**` source text produced a real `<strong>` element,
a real bulleted-list source produced real `<li>` elements, no literal
`**`/`- ` characters visible in the rendered text) — see `T04`'s
Implementation Log for the full evidence. No separate throwaway-mount smoke
test was needed given `T04` was built and verified in the same session
immediately after.

`tsc -b --noEmit` (`src/frontend`): zero errors attributable to this file
or `package.json` (pre-existing, unrelated `CSSProperties` index-signature
errors in `AgentNode.tsx`/`AgentsMapCanvas.tsx`/`SectionDrilldown.tsx`/
`SectionHub.tsx` predate this task — confirmed via `git status`, those
files were already modified before this task began and are outside this
task's `## Files to Modify`).

All 3 locked ACs on this task's own checklist (package.json dependency,
component shape, `npm install` cleanliness) verified. No new
decision/pattern/constraint beyond what `ADR-050`/`architecture.md` already
record. `gate: clear` — no MUST-FLAG trigger fired.
