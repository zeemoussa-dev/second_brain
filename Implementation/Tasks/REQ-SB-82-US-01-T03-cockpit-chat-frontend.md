---
id: REQ-SB-82-US-01-T03
title: Cockpit.tsx — roster reads/writes go through the real backend, not local useState
parent_story: REQ-SB-82-US-01
requirement_id: REQ-SB-82
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-82-US-01-T02]
created: 2026-08-25
updated: 2026-08-25
---

# REQ-SB-82-US-01-T03 — Cockpit.tsx — roster reads/writes go through the real backend, not local useState

## Parent Story

- Story: [[REQ-SB-82-US-01]] — `../UserStories/REQ-SB-82-US-01-persisted-cockpit-chat.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-82 *Cockpit Mechanics — Prep, Research, and Moderation*

---

## Objective

Move `Cockpit.tsx`'s `broughtInIds` from local-only `useState` to state
derived from the real, persisted `thread` returned by `T02`'s endpoints —
no new visual region, only a data-source change.

---

## Starting State → End State

**Before / Inputs:**
- `Cockpit.tsx`'s `broughtInIds: Set<string>` is local component state; `bringIn`/`remove` only mutate it in memory.
- `cockpitApiClient.ts` has no functions calling the new roster endpoints.

**After / Outputs:**
- `broughtInIds` is derived from `data.thread.brought_in_agent_ids` (the real, fetched `CockpitData`).
- `bringIn(id)`/`remove(id)` call new `cockpitApiClient.ts` functions (`bringInAgent`/`removeAgent`) against the real endpoints, then update `data` with the returned thread (or refetch).
- The existing "In this chat"/"Bring in another Expert" markup and `chat-message`/`chat-message-author` rendering (already wired to `data.thread.messages`) are reused unchanged.

---

## Files to Modify

- `src/frontend/src/features/cockpit/cockpitApiClient.ts` — add `bringInAgent(subjectKind, stem, agentId): Promise<CockpitThread>` (`POST .../roster`) and `removeAgent(subjectKind, stem, agentId): Promise<CockpitThread>` (`DELETE .../roster/{agentId}`)
- `src/frontend/src/features/cockpit/Cockpit.tsx` — remove local `broughtInIds` `useState`; derive `inChat`/`available` from `data?.thread.brought_in_agent_ids`; `bringIn`/`remove` call the new client functions

---

## Constraints

- Inherits from parent story.
- No new visual region — reuse the existing "In this chat"/"Bring in another Expert" grouping and `ChatMessageText`/`chat-message-author` rendering exactly as-is.
- The chat composer (`<input>`/`<button type="submit">`) stays `disabled` — enabling send/receive is `REQ-SB-82-US-04`'s concern, explicitly out of scope here.
- `broughtInIds` must never be reintroduced as local-only state that can drift from the real backend value.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-82-US-01-AC-01] In a real browser, open a Cockpit's Chat tab, click "Bring into this chat" on an available Expert, then hard-reload the page. Expect that Expert now shown under "In this chat" (not reset to the plain available list).
2. [REQ-SB-82-US-01-AC-02] From the state left by step 1, click "Remove from chat" on that Expert, then hard-reload. Expect it back under "Experts"/"Bring in another Expert", not "In this chat".
3. [REQ-SB-82-US-01-AC-04] After bringing an Expert into chat, use in-app navigation (not a hard reload) to a different page, then navigate back to the same Cockpit. Expect the roster (and any message history) identical to before navigating away — confirms the SPA remount's mount-time fetch re-reads the real persisted state, not a stale local cache.

**Automated tests:** `n/a — test tooling pending (no frontend test files exist today beyond node_modules)`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `broughtInIds` local `useState` removed; roster derived from real fetched data
- [x] `bringInAgent`/`removeAgent` client functions implemented and wired to `bringIn`/`remove`
- [x] Existing markup/rendering reused unchanged; composer stays disabled
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Enabling the chat composer to send/receive (`REQ-SB-82-US-04`).
- Any new "Recommended" grouping (`REQ-SB-82-US-03-T03`).

---

## Context / Notes

`ADR-007`/architecture.md §Cockpit Persisted Chat are the authoritative
design references. The per-Expert attribution rendering
(`chat-message-author`, reusing `ChatMessageText`) already works today
against the always-empty stub — once `T02` returns real messages, no
change is needed to that rendering path.

---

## Implementation Log

**Built 2026-08-25 (coder).** Read the real, current `T02`-shipped
`cockpit_router.py`/`chat_store.py` directly before writing any frontend
code (both confirmed unchanged from the story's own Context summary).
Changes:
- `cockpitApiClient.ts`: added `bringInAgent(subjectKind, stem, agentId)`
  (`POST .../roster`, body `{agent_id}`) and `removeAgent(subjectKind,
  stem, agentId)` (`DELETE .../roster/{agentId}`), both typed
  `Promise<CockpitThread>` — the real endpoint's own response shape
  (`{brought_in_agent_ids, messages}`) matches `CockpitThread` exactly, no
  reshaping needed.
- `Cockpit.tsx`: removed the local `broughtInIds` `useState` and its
  "no bring-in/remove endpoint yet" comment entirely. `broughtInIds` is
  now computed inline every render from `data?.thread.brought_in_agent_ids
  ?? []` — never held as its own state, so it cannot drift from the real
  fetched value. `bringIn`/`remove` now call `bringInAgent`/`removeAgent`
  and merge the returned real thread back into `data` via `setData`
  (preserving `subject`/`people`/`overview` unchanged). Existing "In this
  chat"/"Bring in another Expert" markup, `chat-message`/
  `chat-message-author` rendering, and the disabled composer are
  untouched.

**Real, live verification — real backend + real browser, not a mock**
(fresh `.venv` uvicorn instance; **found and killed a genuinely stale,
real, still-running backend process already bound to port 8001** — not a
ghost listener this time, unlike `T02`'s own note: `Get-CimInstance`
resolved a real, live `python.exe`/`multiprocessing-fork` process tree,
confirmed serving PRE-`T02` code — its own `/openapi.json` was missing
the `roster` POST/DELETE routes entirely, even though a fresh
`.venv\Scripts\python.exe -c "from app.api.cockpit_router import
router..."` import in the same working tree showed all 4 routes
registered correctly. Killed the real PID tree, started a genuinely fresh
instance, re-confirmed the roster routes now respond `200`, then
proceeded. **New environment fact, recorded in `MEMORY.md`:** this
repo's frontend `.env.local` pins `VITE_API_BASE_URL=http://127.0.0.1:8001`,
not the CLAUDE.md command table's implied default `8000` — future coders
must start the backend on `--port 8001` for the running Vite dev server
to actually reach it, and must not trust a prior session's own backend
process left listening there without confirming what code it serves.
Frontend: the project's own already-running `npm run dev` Vite instance
(port 5173, confirmed via `Get-CimInstance`/`node.exe` path match before
trusting it) picked up both edited files via HMR with no restart needed.
Verification driven via a minimal Node native-`fetch`+native-`WebSocket`
CDP client against a headless Edge instance (`--headless=new
--remote-debugging-port=9333`), driving the REAL running frontend against
the REAL running backend against a REAL vault meeting note (`kind/meeting`
stem "2026-08-17 1500 Discuss with Mousa", found live via a direct
`vault_indexing.rebuild_index()` call — confirmed the vault's frontmatter
uses `type`, not `kind`, as the discriminator field):

- **[REQ-SB-82-US-01-AC-01]** Opened the real Cockpit's Chat tab (empty
  roster baseline confirmed). Clicked "Bring into this chat" on ADNOC
  (available list) — DOM read back confirmed it moved to "In this chat"
  immediately (pre-reload). **Hard-reloaded the page** (`Page.navigate`
  to the same URL, a genuine fresh page load, not an SPA transition),
  re-opened the Chat tab: ADNOC still shown under "In this chat" (group
  label "In this chat" present, `Remove from chat :: apartmentADNOC` row
  present) — not reset to the plain available list. Screenshot evidence
  captured before and after the hard reload; both frames show ADNOC under
  "In this chat" with the composer still disabled/"Chat isn't wired up
  yet…" — PASS.
- **[REQ-SB-82-US-01-AC-02]** From that state, clicked "Remove from chat"
  on ADNOC. Hard-reloaded again, re-opened Chat tab: group label back to
  plain "Experts" (not "In this chat"/"Bring in another Expert"), ADNOC
  back under the available list as "Bring into this chat" — PASS.
- **[REQ-SB-82-US-01-AC-04]** Brought ADNOC in again (DOM-confirmed "In
  this chat" state). Used real in-app SPA navigation — clicked the
  Cockpit's own `<Link to="/my-day/calendar">` (NOT a hard reload;
  confirmed `window.location.pathname` changed to `/my-day/calendar`
  with no full page navigation event) — then navigated back via
  `window.history.back()` (client-side, same SPA session). Re-opened the
  Chat tab: ADNOC still shown under "In this chat" with the group labels
  and roster rows byte-identical to the pre-navigation state — confirms
  the mount-time `fetchCockpit` effect re-fetches real persisted state on
  every remount, never relies on a stale local cache — PASS.
- **Composer/markup constraint** — confirmed in every screenshot: the
  `<input>`/`<button type="submit">` stayed disabled with the unchanged
  "Chat isn't wired up yet…" placeholder throughout; no new visual region
  was added; the "In this chat"/"Bring in another Expert" grouping and
  `chat-message-author`/`ChatMessageText` rendering are the exact
  pre-existing markup, now fed real data.
- **Cleanup:** removed both roster entries left by verification
  (`adnoc-expert`, and `azure-calculator` picked up by a second,
  wide-viewport screenshot pass) via real `DELETE .../roster/{agent_id}`
  calls; a final real `GET` confirmed the real vault's
  `.second-brain/cockpit_chat.json` entry for this meeting is back to the
  honest empty `{"brought_in_agent_ids":[],"messages":[]}` baseline — no
  scratch data left in the real, operational vault state. Killed the
  headless-Edge CDP instance by its own specific PID tree (`taskkill /PID
  9412 /T /F`), not `/IM msedge.exe`, per this project's own established
  precedent.

**AC-03/AC-05/AC-06/AC-07** were already verified live by `T01`
(storage-layer, AC-05/AC-06) and `T02` (real-HTTP-layer, AC-03/AC-06/AC-07)
per their own Implementation Logs — this task's frontend wiring changes
nothing about how those are produced or read, and the same rendering path
(`chat-message-author`/`ChatMessageText`) that already displayed them
correctly against the old stub is reused completely unchanged here, now
fed real data. No new frontend-specific risk to those ACs was introduced.

**Scope-internal judgement calls (for human spot-check, not
escalations):** none beyond what the task's own Files to Modify already
covered — no out-of-scope file was touched.

gate: clear 2026-08-25 — no MUST-FLAG trigger fired (all locked ACs this
task owns verified live with a real positive result over the real
browser/backend/vault stack; no new dependency, no shared-interface
change, no ADR deviation, no unanticipated file; composer stayed
disabled per Constraints).
