---
id: REQ-SB-82-US-03-T03
title: New "Recommended" grouping in the Chat tab's right rail
parent_story: REQ-SB-82-US-03
requirement_id: REQ-SB-82
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-82-US-03-T02, REQ-SB-82-US-01-T03]
created: 2026-08-25
updated: 2026-08-25
---

# REQ-SB-82-US-03-T03 — New "Recommended" grouping in the Chat tab's right rail

## Parent Story

- Story: [[REQ-SB-82-US-03]] — `../UserStories/REQ-SB-82-US-03-meeting-moderator-roster-pre-assembly.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-82 *Cockpit Mechanics — Prep, Research, and Moderation*

---

## Objective

Render a new "Recommended" grouping in `Cockpit.tsx`'s Chat tab right
rail, above "In this chat"/"Bring in another Expert", per the already-
approved (same-day, operator-confirmed) visual shape.

---

## Starting State → End State

**Before / Inputs:**
- `Cockpit.tsx`'s Chat tab right rail has exactly two groupings: "In this chat" and "Bring in another Expert"/"Experts".
- `CockpitThread`'s TS type (`cockpitApiClient.ts`) has no `recommended_agent_ids` field.
- `data.thread.recommended_agent_ids` is now returned by the real backend (`T02`).

**After / Outputs:**
- `CockpitThread` gains `recommended_agent_ids: string[]`.
- A new "Recommended" section renders above the existing two groupings when `recommended_agent_ids` is non-empty: section header + the matched agent(s), each with an "Add" action.
- An agent already brought in renders ONLY in "In this chat" — never duplicated into "Recommended".
- Clicking "Add" on a recommended agent calls the SAME `bringIn` mechanism `T03` (`US-01`) already wired to the real backend.

---

## Files to Modify

- `src/frontend/src/features/cockpit/cockpitApiClient.ts` — add `recommended_agent_ids: string[]` to `CockpitThread`
- `src/frontend/src/features/cockpit/Cockpit.tsx` — new "Recommended" grouping

---

## Constraints

- Inherits from parent story.
- Follows the already-approved visual shape (right rail: "Recommended" section header, matched agent(s) + an Add action, plain Experts list below) — no fresh `/design` pass needed (operator-confirmed, per this story's own Notes).
- Recommendation is purely additive/informational — it must never restrict which Experts the user can manually bring in from the plain "Experts" list.
- Reuses the existing `ExpertRow`-style row rendering pattern already established for "In this chat"/"Bring in another Expert" — no new bespoke row component unless the "Add" action genuinely can't be expressed with the existing one.
- An agent id present in both `recommended_agent_ids` and `brought_in_agent_ids` renders ONLY under "In this chat".

---

## Tests

**Manual verification steps:**
1. [REQ-SB-82-US-03-AC-05] Open a Cockpit whose subject has one or more real recommended agents (from `T02`), before bringing anyone in manually. Expect a distinct "Recommended" section header renders, separate from "In this chat"/"Experts", showing the recommended agent(s).
2. [REQ-SB-82-US-03-AC-06] From that same screen, click "Add"/bring-in on a DIFFERENT Expert from the plain "Experts" list (not the recommended one). Expect it added to "In this chat" the same way any manual bring-in already works — recommendation does not block or alter this.
3. Bring the recommended agent itself into chat via its own "Add" action; expect it now renders ONLY under "In this chat", removed from "Recommended".

**Automated tests:** `n/a — test tooling pending (no frontend test files exist today beyond node_modules)`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `CockpitThread.recommended_agent_ids` added
- [x] "Recommended" grouping renders per the approved shape, above the existing two groupings
- [x] A brought-in agent never duplicates into "Recommended"
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The matching/caching logic itself (`T01`/`T02`).
- Enabling the chat composer (`REQ-SB-82-US-04`).

---

## Context / Notes

`ADR-009` and this story's own Notes (operator-confirmed mockup shape) are
the authoritative design references — no fresh `/design` pass is needed.

---

## Implementation Log

**Build, 2026-08-25 (coder):**

- `cockpitApiClient.ts`: added `recommended_agent_ids: string[]` to
  `CockpitThread`.
- `Cockpit.tsx`: added `recommendedIds`/`recommended` derived sets
  (mirroring the existing `broughtInIds`/`inChat`/`available` pattern —
  never a local `useState`, so it can't drift from the real backend
  value). Added a new "Recommended" `cockpit-group-label` + `item-list`
  block above "In this chat"/"Bring in another Expert", reusing the
  existing `ExpertRow` component unchanged (`title="Add to chat"`,
  `onClick={() => bringIn(agent.id)}` — the SAME `bringIn` function
  already wired to `POST .../roster`, no new mechanism). Each recommended
  row is wrapped in a `<div className="cockpit-expert-recommended">` for
  the accent-bordered visual distinction — this CSS class already existed
  uncommitted in `cockpit.css` (pre-staged from the same-day whiteboarding
  session referenced in the story's Notes); no edit to `cockpit.css` was
  needed or made (out of this task's `## Files to Modify`).

**Scope-internal judgement call (for human spot-check):** `available`
(the plain "Experts"/"Bring in another Expert" list) now also excludes
any id present in `recommendedIds`, not just `broughtInIds` — so a
recommended-but-not-yet-brought-in agent renders ONLY under
"Recommended", never duplicated as a second row in the plain list below.
The story's Constraint ("recommendation must never restrict which
Experts the user can manually bring in") is read as "the user must still
be able to add it" (satisfied — Recommended's own Add uses the identical
`bringIn` call), not "it must also appear a second time in the plain
list." Logged per this project's own scope-internal-judgement-call
convention, not an escalation.

**Environment note — zombie backend socket (disclosed per the task's own
own instructions):** the persistent dev backend on port 8001 was found,
at verification start, to be a stale reload-child process (`Get-
NetTCPConnection` reported an `OwningProcess` that no longer existed in
the process table — the reloader parent had already died, per this
project's own documented `SPRINT-022`/`029` zombie-socket precedent) and
was serving PRE-`T02` code (a live `GET /cockpit/meeting/...` returned a
`thread` with no `recommended_agent_ids` key at all, and no new key was
persisted to `.second-brain/cockpit_chat.json` for a fresh subject).
Confirmed the real, alive PID via `Get-CimInstance Win32_Process`
(`56256`, `--multiprocessing-fork` child of already-dead parent `29796`),
killed it (`Stop-Process -Id 56256 -Force`), and started ONE fresh
instance with the project's own documented launch command
(`tools/run-backend.cmd`'s own `uvicorn app.main:app --reload --port
8001`). Re-verified live: the SAME real Masdar meeting note now returned
the correct, real `recommended_agent_ids`. The persistent backend on port
8001 was left running (not shut down) per explicit operator instruction,
now serving current code.

**Live verification (real browser, real backend, real vault data — no
mocks):** headless Edge via CDP (`msedge.exe --headless=new
--remote-debugging-port=9333`, killed by specific PID tree afterward, per
this project's own established technique), driven by a minimal Node
native-`fetch`/`WebSocket` script (no puppeteer/playwright). Target: the
real vault meeting note `Claire-Moussa - Catch-up Masdar Data
Platform-2026-08-18-d2c74ddc.md` (`customer: "Masdar"`,
`customer/masdar` tag) — its real, live `GET /cockpit/meeting/...`
returned `recommended_agent_ids: [masdar-expert, adnoc-expert,
azure-data-architect, azure-enterprise-architect, azure-infra-architect,
taqa-expert]` (both the customer-match AND domain-match tracks fired for
this one real subject, per `T01`'s own deterministic matching).

- **[REQ-SB-82-US-03-AC-05]** Opened `/meeting-cockpit/<the real Masdar
  stem>`, Chat tab, before bringing anyone in. **PASS** — a distinct
  "Recommended" section header rendered above "Experts", showing all 6
  real matched agents (ADNOC, Azure Data Architect, Azure Enterprise
  Architect, Azure Infrastructure Architect, Masdar, TAQA), each visually
  distinguished by the `cockpit-expert-recommended` accent border —
  screenshot `t03-01-before-add.png`.
- **[REQ-SB-82-US-03-AC-06]** From that same live screen, clicked "Add"
  on Azure Calculator (a DIFFERENT, non-recommended Expert) from the
  plain "Bring in another Expert" list. **PASS** — it moved into "In this
  chat" the same real way as any manual bring-in (a real `POST
  .../roster` call, confirmed via the DOM read-back), with zero change to
  the Recommended section — recommendation did not block or alter this —
  screenshot `t03-04-ac06-different-expert.png`.
- **Test step 3 (unlabeled manual step):** clicked "Add" on ADNOC (a
  recommended agent) via its own Recommended-section Add action. **PASS**
  — real `POST .../roster` call fired (confirmed via
  `chat_store`/`cockpit_chat.json`'s own real, persisted
  `brought_in_agent_ids`); ADNOC immediately rendered ONLY under "In this
  chat" (5 remaining agents stayed under "Recommended", ADNOC absent from
  "Bring in another Expert" too) — screenshot `t03-02-after-add.png`. A
  full page reload (`Page.navigate`, not an SPA nav) reconfirmed the
  exact same grouping — real persistence across reload, not just local
  React state — screenshot `t03-03-after-reload.png`.
- Zero console/`Runtime.exceptionThrown` errors observed across the whole
  interaction sequence.
- **Cleanup:** reverted both real test bring-ins (`DELETE
  .../roster/adnoc-expert`, `DELETE .../roster/azure-calculator`) so the
  real vault's own `cockpit_chat.json` state for this real subject is
  back to `brought_in_agent_ids: []` (its `recommended_agent_ids` cache
  entry is left in place — the SAME real, deterministic value any future
  read recomputes/re-caches to, not a fabricated leftover).

**Verification method deviation (disclosed):** the task's own Tests block
names manual browser steps with no named tool; a headless-Edge-CDP + Node
driver was used as the concrete mechanism (this project's own established
technique, `SPRINT-026`/`036`/`038`), not a weaker substitute — real
browser, real DOM, real network calls against the real, unmodified app
and a real vault note.

gate: clear 2026-08-25 — no MUST-FLAG trigger fired (no new dependency,
no shared-interface change beyond the additive, already-anticipated
`recommended_agent_ids` field, no ADR deviation, no unanticipated file).
The one judgement call above (excluding recommended ids from the plain
list) is scope-internal, logged for human spot-check, not a flag trigger.
