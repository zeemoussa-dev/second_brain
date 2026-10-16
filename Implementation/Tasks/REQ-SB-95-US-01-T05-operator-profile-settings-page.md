---
id: REQ-SB-95-US-01-T05
title: Operator Profile Settings page + landing-grid card, with the own address read-only
parent_story: REQ-SB-95-US-01
requirement_id: REQ-SB-95
type: frontend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-95-US-01-T03]
created: 2026-10-16
updated: 2026-10-16
---

# REQ-SB-95-US-01-T05 — The Operator Profile Screen

## Parent Story

- Story: [[REQ-SB-95-US-01]] — `../UserStories/REQ-SB-95-US-01-operator-profile.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Give the operator the one place to record who they are and who is on their
team — a new Settings page on the live Settings conventions, plus one more card
in the landing grid — with their own email address shown **read-only**,
pointing at Settings → System.

---

## Starting State → End State

**Before / Inputs:**

- `src/frontend/src/pages/SettingsPage.tsx` holds the live `SETTINGS_SECTIONS`
  icon-card grid (`key`/`icon`/`label`/`desc`/`href` per entry — read it
  directly; it is the approved design authority here, superseding
  `html-prototype/settings.html`, which is stale).
- `src/frontend/src/pages/SettingsSystemPage.tsx` is the approved pattern for
  an editable settings form: `.card.settings-card`, `.item-list`/`.item-row`,
  `.input`, `Save changes`. It owns the "Your Email Address" field.
- `T03`'s `GET` / `PUT /operator/profile`.

**After / Outputs:**

- A new page (e.g. `src/frontend/src/pages/SettingsOperatorPage.tsx`) with:
  - the operator's name, their other mail addresses and timezone as editable
    fields;
  - the **team as repeating `email` + `role` rows** — add a row, remove a row —
    built from the same `.item-row`/`.input` controls, not a new visual system;
  - the operator's own address rendered as **read-only text, not an input**,
    with a visible pointer to Settings → System as the place to change it;
  - one `Save changes` action that `PUT`s the whole record and re-renders from
    the response.
- One more card in `SETTINGS_SECTIONS` and its route, following the existing
  entries exactly.
- `SettingsSystemPage.tsx` is **not modified**.

---

## Files to Modify

- `src/frontend/src/pages/SettingsOperatorPage.tsx` (new)
- `src/frontend/src/pages/SettingsPage.tsx` (one more `SETTINGS_SECTIONS` entry)
- the frontend route table that maps `/settings/...` paths to pages (read the
  real current router file; add one route, change nothing else)
- a feature API client for the two routes, following the existing
  `features/<area>/` client convention

---

## Constraints

- Inherits from parent story.
- **`SettingsSystemPage.tsx` is untouched** (`ADR-038`). It keeps "Your Email
  Address" and stays the one editor of that address. A second editable input
  for the same fact anywhere on the new page is the failure this story exists
  to prevent.
- Reuse the already-approved families (`.card.settings-card`, `.item-list`,
  `.item-row`, `.input`, `Save changes`). No new visual system; the only new
  interaction is the repeating email+role row.
- No `/design` pass was requested for this story (operator's 2026-08-31
  functional-first precedent). Visual polish is a non-blocking spot-check
  against the live Settings pages, never a locked AC.
- The page records membership only: an email and a role per colleague. Do not
  add a name/title/avatar field — the vault's Person notes own that.

---

## Tests

**Automated tests:** `n/a — the frontend has no test runner and does not
declare `vitest` (`CLAUDE.md`). Verify structurally in a real browser, below.`

**Manual verification steps** — drive a real browser against the running dev
server and record what was observed (per this project's Learnings: allow a real
~500–1000 ms wait between any dispatched state change and reading the DOM back;
set controlled-input values through the native `HTMLInputElement.prototype.value`
setter before dispatching `input`).

1. `[REQ-SB-95-US-01-AC-01]` Open `/settings`; confirm the new Operator Profile
   card renders inside the existing `SETTINGS_SECTIONS` grid (same card markup
   as its siblings) and navigates to the new page.
2. `[REQ-SB-95-US-01-AC-01]` On the new page, enter a name, two other
   addresses, a timezone and three team rows (each an email input and a role
   input), save, navigate away and back; confirm every value is rendered back
   exactly as entered, and confirm the real `PUT` then `GET` fired (watch the
   network calls).
3. `[REQ-SB-95-US-01-AC-01]` Add a team row and remove one; confirm the DOM
   gains/loses exactly one `.item-row` and that saving persists the new list.
4. `[REQ-SB-95-US-01-AC-04]` Confirm the operator's own address renders as
   **text, not an `<input>`** (assert on the element type), and that a visible
   pointer to Settings → System is present beside it.
5. `[REQ-SB-95-US-01-AC-04]` Change the address on Settings → System, return to
   the Operator Profile page, and confirm the displayed mirror shows the new
   value — with no edit made on the Profile page itself.
6. `[REQ-SB-95-US-01-AC-04]` Confirm `SettingsSystemPage.tsx` still renders its
   "Your Email Address" field and still saves it (the untouched-by-this-story
   regression check), and that `git status` shows that file unmodified.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] New Settings page on the approved `.item-list`/`.item-row`/`.input` families
- [ ] One more card in the live `SETTINGS_SECTIONS` grid, plus its route
- [ ] Team recorded as repeating email+role rows; nothing else about a person
- [ ] The own address is read-only and points at Settings → System
- [ ] `SettingsSystemPage.tsx` unmodified
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Editing the operator's own email address here (`ADR-038`).
- Creating or editing Person notes from this screen — the vault owns those.
- Org-chart modelling: reporting lines, hierarchies, multiple teams.
- Any backend change — `T01`/`T02`/`T03`/`T04`.

---

## Context / Notes

`architecture.md` → **§Operator Profile — the Singleton Record, and the Address
It Mirrors** (its Frontend bullet) is authoritative. `html-prototype/
settings.html` is **not** the design authority for the landing grid — the real
`SettingsPage.tsx` card grid superseded it on 2026-08-27, as the story's
*Prototype parity* note records.

Backend CORS allows `5173`/`5174` only — pick a verification port accordingly
(a Learnings entry records a confusing empty state caused by starting on
`5180`).

---

## Implementation Log

_(Filled in by the coder.)_
