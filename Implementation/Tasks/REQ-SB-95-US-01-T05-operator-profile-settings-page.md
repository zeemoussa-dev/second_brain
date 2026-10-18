---
id: REQ-SB-95-US-01-T05
title: Operator Profile Settings page + landing-grid card, with the own address read-only
parent_story: REQ-SB-95-US-01
requirement_id: REQ-SB-95
type: frontend
status: Done
gate: flagged
gate_reason: "Both locked ACs (AC-01, AC-04) verified in a real browser; nothing in this task's own scope is unresolved. FLAGGED for one finding made while performing Tests step 6, which is PRE-EXISTING and outside this task's files: Settings > System renders `Your Email Address` (and the three Compass fields) as editable inputs and answers `Saved.`, but `app/api/settings_system_router.py`'s `UpdateSystemSettingsBody` declares only 5 of `system_settings._FIELDS`' 9 fields, so a `PUT /settings/system` carrying `self_email` is silently dropped (`{\"ok\":true,\"restart_required\":false}`) and nothing is written. Confirmed live on a disposable backend; that file last changed 2026-08-27 and is untouched by this task. AC-04's `changing the address on Settings > System changes what the Profile returns` was therefore verified through the app's own working setting-write path (`POST /setup/save`, the wizard the System page itself links to), which does write `SELF_EMAIL`. The human decides whether the dropped-field defect becomes a `/bug`. See REVIEW-QUEUE.md."
phase: P2
depends_on: [REQ-SB-95-US-01-T03]
created: 2026-10-16
updated: 2026-10-18  # coder: Ready -> Done; both locked ACs verified in a real browser
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

- [x] New Settings page on the approved `.item-list`/`.item-row`/`.input` families
- [x] One more card in the live `SETTINGS_SECTIONS` grid, plus its route
- [x] Team recorded as repeating email+role rows; nothing else about a person
- [x] The own address is read-only and points at Settings → System
- [x] `SettingsSystemPage.tsx` unmodified
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
      — **not appended**: `MEMORY.md` is 86 KB against the 40 KB budget its own
      rule 1 sets, which forbids appending while over. Two candidates are
      recorded in `REVIEW-QUEUE.md` instead (see the log below).
- [x] `CHANGELOG.md` entry appended

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

**Coder, 2026-10-18 — `Ready → Done`, `gate: flagged`. Both locked ACs
verified in a real browser; exactly the four listed files touched.**

Built: `src/frontend/src/pages/SettingsOperatorPage.tsx` (new),
`src/frontend/src/features/settings/operatorProfileApiClient.ts` (new — the
feature API client the Files-to-Modify line asks for), one
`SETTINGS_SECTIONS` entry in `src/frontend/src/pages/SettingsPage.tsx`, and
one import + one `<Route>` in `src/frontend/src/App.tsx` (the real current
router file — found by reading, not assumed; it is where every other
`/settings/...` path is mapped).

### How the page is built, and what it refuses to pretend

- **The own address is a MIRROR and is drawn as one.** It lives in its own
  card above the editor, as a `<span>` — not a disabled input, which reads
  as "editable, just not now" — carrying the backend's own
  `own_address.setting_key` and `own_address.edited_at` rather than a second
  hardcoded copy of "Settings > System", plus a link to `/settings/system`.
  The write body has **no field for it by type**
  (`OperatorProfileWriteBody`), so normal use cannot provoke the backend's
  `409`.
- **Three renderings, never two.** *Read and configured* → the form, badged
  `Saved`. *Read and `is_configured: false`* → the form, badged
  `Not saved yet`, saying in words that the fields are empty because nothing
  is stored. *Could not be read* → **no editor at all**, its own
  `Could not be read` element carrying the backend's message verbatim, and a
  `Try again`. `.empty-state` is not used anywhere on this page
  (`SPRINT-091`'s rule: a failed read may never borrow that look).
- **It states a limit it inherited rather than relabelling it.** The
  Manager (`T01`, `Done`) deliberately reports a stored `Profile.json` it
  could not parse the same way as one that was never written —
  `is_configured: false`. The page says so in its own words instead of
  claiming "never saved" as a fact it cannot know.
- **A save re-renders from the `PUT`'s own response, never from the draft**,
  because the backend drops a team entry with no email; a row that was not
  stored would otherwise stay on screen looking saved. The page warns on the
  row *before* the save and counts the dropped rows in the save message
  after it.
- **Refusals are rendered, not summarised.** `describeOperatorProfileRefusal`
  handles both of this router's deliberately different shapes: a `409`'s
  `detail` string verbatim, and a `422`'s `detail` LIST rendered as the field
  path FastAPI named (`team.1.email — Field required`), so the operator is
  told which row and which field.

### Verification — manual mode, in a real browser

Environment, per this sprint's standing rule: a **disposable** backend on
`127.0.0.1:8125` over scratch `SECOND_BRAIN_DATA_PATH`/`VAULT_PATH`/
`HERMES_HOME_PATH`, started with its **CWD in a scratch folder carrying its
own `.env`** (`system_settings._ENV_PATH` is `Path(".env")`, resolved against
the process CWD — starting it in `src/backend` would have let step 5 write
the operator's real `.env`), plus a **second Vite on `:5174`** with
`VITE_API_BASE_URL` overridden as a shell variable. The operator's `:8001`
and `:5173` were never driven, every value is fictitious
(`operator@example.test`, `Robin Fictional`), and the repository `.env` was
SHA-256-hashed before and after the whole pass: **unchanged**
(`4818D3DD…AD9BCDA`). Headless Edge over CDP; each region clipped from its
own bounding box in a 1500×4000 viewport (`SPRINT-091`: `scrollIntoView`
inside the app shell silently repeats images); ≥600 ms between every
dispatched change and the DOM read; controlled inputs set through the native
`HTMLInputElement.prototype.value` setter. Screenshots in the session
scratchpad under `t05-shots/`, all reviewed.

- **`[REQ-SB-95-US-01-AC-01]` — PASS** (Tests steps 1, 2, 3).
  - *Step 1.* `/settings` renders 16 grid cards; the new one is **position 2**
    with `class="card settings-card"`, icon `badge`, title *Operator Profile*
    — its class list and child element list are **identical** to the System
    card's (`SPAN.material-symbols-outlined settings-card-icon`,
    `H2.settings-card-title`, `P.settings-card-desc`), asserted equal rather
    than eyeballed. Clicking it navigated to `/settings/operator` and the
    editor rendered. (`01-settings-grid.png`.)
  - *Step 2.* Typed a name, a timezone, two other addresses and three team
    rows (email + role each) and saved. The fetch spy recorded a real
    `PUT http://127.0.0.1:8125/operator/profile`; the backend's own
    `GET /operator/profile` then returned exactly those values with
    `is_configured: true`; the badge flipped `Not saved yet → Saved`.
    Navigating away to `/settings` and back fired a real
    `GET /operator/profile` and rendered **every value exactly as entered**
    — name, timezone, both addresses in order, all three email+role pairs.
    (`04-filled-before-save.png`, `05-after-save.png`, `06-reopened.png`.)
  - *Step 3.* `.item-row` count inside `[data-testid="operator-team"]`:
    **3 → Add colleague → 4 → Remove (row 1) → 3**, exactly one each way.
    Saving persisted the new list: the stored record is
    `alex…/Delivery Lead`, `jo…/Analyst`, `kim…/Operations` — the removed
    `sam…` is gone from disk. (`07-team-add-remove.png`,
    `08-after-add-remove-save.png`.)
- **`[REQ-SB-95-US-01-AC-04]` — PASS** (Tests steps 4, 5, 6), with one
  pre-existing defect found at step 6 and flagged rather than worked around.
  - *Step 4.* `[data-testid="operator-own-address"]` is a **`SPAN`**, not an
    `INPUT`, reading `operator@example.test`. The own-address card contains
    **0** `input`/`textarea`/`select` elements, and at that moment the whole
    page's editable elements were exactly `operator-name` and
    `operator-timezone`. The pointer beside it reads *"The Operator Profile
    does not store this address — it shows the `SELF_EMAIL` setting, which is
    edited on Settings > System"*, with a `/settings/system` link and an
    `Edit on Settings › System` button. (`03-own-address-readonly.png`.)
  - *Step 5.* The setting was changed to `robin.moved@example.test` through
    the app's own setting-write path, the backend restarted as the System
    page's own save message instructs (pydantic loads settings once per
    process), and the Profile page reloaded with **no edit made on it**: the
    mirror shows `robin.moved@example.test`, the Profile's own facts are
    unchanged, no save message is present, and `Profile.json`'s bytes are
    identical before and after — the file holds neither address.
    (`11-mirror-after-setting-change.png`, `12-profile-unchanged.png`.)
  - *Step 6.* `SettingsSystemPage.tsx` still renders **Your Email Address**
    with its `_check_email` badge, its description and its real value in an
    `INPUT` (`09-system-page-own-field.png`), and `git status` reports both
    it and `settings_system_router.py` **unmodified** by this task. The
    *"and still saves it"* half is **FALSE, and was already false before this
    task** — see the finding below.

### The finding at step 6 — pre-existing, out of scope, flagged

Settings > System accepts an edit to **Your Email Address**, reports
*"Saved. Restart the backend for these changes to take effect."*, and writes
nothing. Root cause, read directly: `app/api/settings_system_router.py`'s
`UpdateSystemSettingsBody` declares only `hermes_base_url`,
`hermes_home_path`, `second_brain_data_path`, `vault_path` and
`cors_allowed_origins`, while `system_settings._FIELDS` renders **nine**
editable fields. Pydantic drops the undeclared ones, `exclude_none=True`
leaves an empty patch, and `update_system_settings` returns early
`{"ok": true, "restart_required": false}` — which the page renders as a
successful save. Observed live on the disposable backend: the browser sent
`PUT /settings/system {"self_email":"robin.moved@example.test"}` → `200` →
the `.env` `SELF_EMAIL` line unchanged. The same is true of
`compass_base_url`, `compass_api_key` and `compass_model`.

Not this task's to fix: `settings_system_router.py` is not in
`## Files to Modify`, `SettingsSystemPage.tsx` is explicitly *untouched*
(`ADR-038`), and the file last changed **2026-08-27**, seven weeks before
this story existed. AC-04's *"changing the address on Settings → System
changes what the Profile returns"* was therefore verified through the app's
own working setting-write path — `POST /setup/save`, the setup wizard that
the System page itself links to, which passes a free dict to
`update_system_settings` and does write `SELF_EMAIL`. Written to
`REVIEW-QUEUE.md` with a recommendation to capture it via `/bug`.

### Beyond the ACs — the two refusals, rendered

The page cannot normally send either one, so both were induced by rewriting
the outgoing `PUT` body in the page and letting the **real** backend answer:

- `409` → rendered verbatim: *"The operator's own email address is not stored
  in the Operator Profile and cannot be set here: it is the SELF_EMAIL
  setting, edited on Settings > System. Send the Profile without it; nothing
  was saved."* (`14-refusal-409-own-address.png`.)
- `422` → rendered as **`team.1.email — Field required`**, naming the row and
  the field rather than "invalid input". (`15-refusal-422-field-path.png`.)
- After both, the stored record was byte-for-byte what it was before, and the
  editor kept what was authored. (`13-could-not-be-read.png` covers the third
  rendering: a failed read of `/operator/profile`, induced in-page with the
  backend up, draws **no editor, no `.empty-state`, zero inputs** and the
  backend's own message; `Try again` recovers it in place.)

### Checks

- `npx tsc --noEmit` — **clean**. `npx oxlint src` — **12 warnings, all
  pre-existing and none in any file this task touched** (the four files lint
  silently on their own).
- Backend suite, `src/backend`: **685 passed / 0 failed before**, **685
  passed / 0 failed after** — moved by zero, as a frontend-only task should.
  The two failures the brief warned about
  (`test_workflow_action_integrity.py`, `test_workflow_artifact_kind.py`) were
  **already green** when this task started; none of the four known
  order-dependent tests failed in either run.
- The frontend has no test runner and does not declare `vitest`, so no
  automated test was added (`CLAUDE.md`).

### Scope-internal judgement calls, for human spot-check

1. **The other mail addresses are repeating `.item-row`s too**, not one
   comma-separated input. The task specifies repeating rows only for the
   team; a delimiter-parsed field would have invented a syntax the backend
   does not have (it takes a JSON list), and reuses nothing.
2. **A failed read renders no editor at all.** The alternative — an empty
   form plus an error line — is exactly the "empty form that implies a saved
   blank" the brief rules out. Cost: the operator cannot author into a form
   that could not load; `Try again` is offered instead.
3. **The page names the backend's unreadable-vs-never-saved conflation**
   rather than relabelling a `Done` task's answer (`SPRINT-091`'s precedent
   for `profile_detail.py`).
4. **Save is never disabled to pre-empt a refusal**, matching the Workflows
   page: a blank-email row is flagged inline and counted in the save
   message, but the backend's own answer is what the operator reads.
5. **Every list edit uses the functional `setDraft(previous => …)` form.**
   Two rows changed before React re-renders would otherwise both start from
   the same stale list and the second would undo the first — a real hazard
   with double-clicks, and the exact failure the CDP driving would have hit.

### MEMORY.md — not appended

`MEMORY.md` is 86 KB against the 40 KB budget its own rule 1 sets, which
forbids appending while over. Two candidates are recorded in
`REVIEW-QUEUE.md` instead: (a) *a settings page whose router body model does
not declare every field it renders will report a save it did not perform —
the body model and the field registry must be checked against each other*;
(b) *a mirrored read-only value is rendered as text carrying the name of the
surface that owns it, taken from the payload, never as a disabled input*.

### Out of scope, untouched, confirmed

No backend change of any kind (`T01`–`T04`). `SettingsSystemPage.tsx`,
`system_settings.py`, `config.py`, `setup_wizard.py` and `setup_router.py`
are untouched (`ADR-038`), as are the `REQ-SB-95-US-04-T06` files live in
this shared checkout. Nothing outside `## Files to Modify` was edited, so no
`ESCALATIONS.md` entry was written.
