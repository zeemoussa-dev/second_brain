---
id: REQ-SB-99-US-01-T06
title: The profile debug page — route, API client, five regions, honest failures, and the way in from the agent panel
parent_story: REQ-SB-99-US-01
requirement_id: REQ-SB-99
type: frontend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-99-US-01-T05]
created: 2026-10-17
updated: 2026-10-17
---

# REQ-SB-99-US-01-T06 — A Page You Can Paste Into an Incident Note

## Parent Story

- Story: [[REQ-SB-99-US-01]] — `../UserStories/REQ-SB-99-US-01-hermes-profile-as-it-really-is.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-99 *See a Hermes Profile As It Really Is — Soul, Skills, Config, Jobs*

---

## Objective

Put `T05`'s composed read on its own read-only page, reached from the agent
panel and addressable by URL, rendering five regions and the three failure
kinds exactly as the backend reports them.

---

## Starting State → End State

**Before / Inputs:**

- `T05` serves `GET /hermes/agents/{agent_id}/profile-detail`.
- `src/frontend/src/App.tsx` declares one flat `<Route>` per page under
  `AppShell`; pages live in `src/frontend/src/pages/`.
- `src/frontend/src/features/agents-map/agentsApiClient.ts` is the agents-map
  API client (`fetchAgent`, `fetchAgentJobs`, … ) — the new call belongs here.
- `src/frontend/src/components/Breadcrumbs.tsx` (`ADR-042`) renders the trail;
  the last crumb is never a link.
- `src/frontend/src/features/agents-map/AgentDetailPanel.tsx` has seven tabs
  that fetch on mount; its overview tab already carries a navigation link
  precedent (`data-testid="overview-chat-link"`).
- The live approved families are `.item-list` / `.item-row` /
  `.item-row-main` / `.item-row-title` / `.item-row-meta`, `badge`, `kv-row`
  and `.empty-state`.
- The frontend has **no test runner** (it does not declare `vitest`), so this
  task verifies structurally in a real browser.

**After / Outputs:**

- `src/frontend/src/pages/HermesProfileDetailPage.tsx` (new) — route
  `/agents/:agentId/profile`, rendering five regions, each with its own
  `data-testid`:
  - `profile-soul-region` — the full soul in one `<pre>`-style verbatim block
    (`data-testid="profile-soul-text"`), never excerpted, never reassembled.
  - `profile-skills-region` — one `.item-row` per skill
    (`data-testid="profile-skill-row"`) carrying the deployed version and a
    `badge` with its verdict, including `unknown_to_framework`.
  - `profile-config-region` — one row per config key
    (`data-testid="profile-config-row"`) showing the value, the source label
    (*set here* / *inherited from the install root* / *not set*) and the file
    it came from; the two layers are shown as two labelled layers, never merged.
    The enabled toolsets render here as `data-testid="profile-toolset-row"`.
  - `profile-jobs-region` — the profile's own jobs
    (`data-testid="profile-job-row"`) with schedule and last-run outcome, and a
    separately labelled install-level group
    (`data-testid="profile-install-job-row"`).
  - Each region renders a per-region failure element
    (`data-testid="profile-<region>-error"`) when the backend reports one, and
    `.empty-state` only for a genuinely-read empty region.
- A whole-page unread state (`data-testid="profile-install-error"`) when the
  install itself could not be read — no region rendered as if read.
- Breadcrumbs: Agents → *<profile name>* → Profile detail.
- `src/frontend/src/features/agents-map/agentsApiClient.ts` — one typed
  `fetchHermesProfileDetail(agentId)`.
- `src/frontend/src/App.tsx` — one route.
- `AgentDetailPanel.tsx` — **only the way in**: one link
  (`data-testid="overview-profile-detail-link"`) on the overview tab for a
  Hermes-backed agent, navigating to the page. No new fetch on panel mount.

---

## Files to Modify

- `src/frontend/src/pages/HermesProfileDetailPage.tsx` (new)
- `src/frontend/src/features/agents-map/agentsApiClient.ts` (one call + its types)
- `src/frontend/src/App.tsx` (one route)
- `src/frontend/src/features/agents-map/AgentDetailPanel.tsx` (the link only)

---

## Constraints

- Inherits from parent story.
- **Read-only screen.** No edit control, no save, no deploy, no job action
  anywhere on this page; opening or refreshing it writes nothing.
- **The panel must not pay this page's cost**: no `profile-detail` fetch on
  `AgentDetailPanel.tsx` mount, and nothing added to the Agents Map's
  mount-time fetches (`BUG-086`).
- **Functional-first on approved conventions** (story Notes → Prototype
  parity): reuse `.item-list`/`.item-row`, `badge`, `kv-row` and
  `.empty-state`; introduce no new visual system. Visual polish is an
  out-of-band spot-check against the prototype, never a locked AC.
- Every assertion below is on **DOM structure** — jsdom and a headless browser
  see no computed CSS, layout, colour or `:hover`.
- **Render the backend's own words.** A failed region shows the message `T05`
  returned, naming the file; the screen never invents wording, never
  substitutes an empty list for a failed read, and never shows an excerpt where
  the full soul belongs.
- The soul block preserves whitespace and line breaks exactly as served.

---

## Tests

**Manual verification steps** (real backend on `127.0.0.1:8001` + `npm run dev`;
headless-Edge/CDP screenshot and DOM reads are this project's established
technique — read the DOM back at least ~500ms after any dispatched state
change; check the backend's CORS allow-list before picking a frontend port):

1. `[REQ-SB-99-US-01-AC-01]` Open the Agents Map, open a real Hermes agent's
   panel, click `[data-testid="overview-profile-detail-link"]`, and confirm it
   routes to `/agents/<id>/profile`. Assert
   `[data-testid="profile-soul-text"]`'s text equals the profile's real
   `SOUL.md` on disk byte-for-byte (read the file to compare), is longer than
   280 characters, and shows the `## Scope` body and section order. Confirm the
   Agents Map still shows that agent's existing short description unchanged.
2. `[REQ-SB-99-US-01-AC-02]` Confirm one
   `[data-testid="profile-skill-row"]` per skill in that profile's own
   `skills/` tree, each showing its deployed version and a verdict `badge`.
   Copy one skill folder into the profile under a slug the framework's catalog
   does not have, reload, and confirm it renders as a row with an
   unknown-to-framework badge rather than being omitted; remove it again.
3. `[REQ-SB-99-US-01-AC-03]` Confirm `[data-testid="profile-config-row"]`
   entries render the two layers as two labelled layers — each value naming its
   source file, a root-only key labelled *inherited from the install root*, a
   key in neither labelled *not set* — with no single merged "effective" value
   anywhere on the page. Confirm the model, the provider and the enabled
   toolsets (`[data-testid="profile-toolset-row"]`) are present.
4. `[REQ-SB-99-US-01-AC-04]` On a profile with its own `cron/jobs.json`,
   confirm `[data-testid="profile-job-row"]` lists exactly those jobs with
   schedule and last-run outcome, that a job living only at the install root
   appears **only** in the install-level group
   (`[data-testid="profile-install-job-row"]`), and that the Hermes Ops cron
   screen still lists exactly what it listed before.
5. `[REQ-SB-99-US-01-AC-05]` Snapshot `<HERMES_HOME>` (recursive path → sha256
   + mtime, PowerShell) before opening; open the page, refresh it, navigate
   away and back; re-snapshot and confirm the two are identical. In the same
   session, confirm via a `window.fetch` spy that the page issues exactly one
   `profile-detail` request per load and that opening the agent panel alone
   issues none.
6. `[REQ-SB-99-US-01-AC-06]` Temporarily rename that profile's `SOUL.md` and
   break its `config.yaml`, and induce a toolsets read failure (the established
   in-process monkeypatch of `HermesCLI._run` against the real running app).
   Confirm the page renders the missing file by name in
   `[data-testid="profile-soul-error"]`, the unreadable config file by name,
   and a toolsets **read-failure** message — explicitly not an empty
   "no toolsets enabled" state — while the skills and jobs regions still render
   their real content. Restore every file and confirm the page returns to its
   read state.
7. `[REQ-SB-99-US-01-AC-07]` Point the backend's Hermes home at a path that
   does not exist, restart it, and confirm the page renders
   `[data-testid="profile-install-error"]` naming why, and that **no**
   region-level content element (`profile-skill-row`, `profile-config-row`,
   `profile-job-row`, `profile-soul-text`) is present in the DOM. Restore the
   real path.

**Automated tests:** `n/a — the frontend declares no test runner (CLAUDE.md:
"no tests and does not declare vitest"); verified structurally in a real
browser as above. The backend behaviour behind every step above is pinned by
T05's pytest suite.`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] A dedicated, addressable read-only page with the five regions
- [ ] Breadcrumbs trail and a way in from the agent panel's overview tab
- [ ] Per-region failures and the whole-install failure rendered in the
      backend's own words
- [ ] No new fetch on panel mount or on any listing path
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Editing anything from this view — soul, config, skills or jobs.
- Reworking the Agents Map, the agent panel's seven tabs, or
  `agents_map_adapter.py`.
- Session transcripts — `REQ-SB-100-US-01`.
- A cross-profile comparison table — `REQ-SB-96-US-01`.
- Visual polish beyond reusing the approved families (out-of-band spot-check).

---

## Context / Notes

`architecture.md` → **§Surface — a Page, Not an Eighth Tab** and `ADR-043`: a
dedicated route and page, because this view is deliberately expensive and worth
a URL that can be pasted into an incident note; the panel gains only the way in,
and `ADR-042`'s breadcrumbs give the way back. The story's Notes record the
operator's 2026-08-31 functional-first precedent — compose from already-approved
families now, visual pass afterwards.

---

## Implementation Log

_(Filled in by the coder.)_
