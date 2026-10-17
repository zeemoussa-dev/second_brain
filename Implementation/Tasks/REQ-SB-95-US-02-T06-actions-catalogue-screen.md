---
id: REQ-SB-95-US-02-T06
title: Actions catalogue screen + Action editor, Settings card, route, and the sixth Artifacts tab
parent_story: REQ-SB-95-US-02
requirement_id: REQ-SB-95
type: frontend
status: Done
gate: flagged
gate_reason: "trigger 1/7 — four scope-internal judgement calls to spot-check (plugin_id sent as an ABSENT key rather than null for a stored Action; a radio group as the exactly-one picker; allowed_callers as a comma-separated field; the new /settings/actions route deliberately NOT added to the backend's UI_FEATURE_KEYS, whose file is out of scope — logged as ESC-071), plus one out-of-scope file carried into the frontend commit: ArtifactExportModal.tsx's KIND_LABELS needed an `action` entry the moment the ArtifactKind union widened, or tsc -b fails for the whole checkout — logged as ESC-070"
phase: P2
depends_on: [REQ-SB-95-US-02-T03, REQ-SB-95-US-02-T04, REQ-SB-95-US-02-T05]
created: 2026-10-16
updated: 2026-10-18
---

# REQ-SB-95-US-02-T06 — Actions Catalogue Screen + Action Editor

## Parent Story

- Story: [[REQ-SB-95-US-02]] — `../UserStories/REQ-SB-95-US-02-action-sixth-artifact-kind.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Give the operator the one screen the catalogue is for: a list of Actions with
their broken/resolving state, and an editor for one Action — plus the Settings
card, the route, and the sixth kind tab on the Artifacts page.

---

## Starting State → End State

**Before / Inputs:**

- `src/frontend/src/pages/SettingsPage.tsx` holds a `SETTINGS_SECTIONS` const
  array rendered as an icon-card grid (`card settings-card`), ten entries today.
- `src/frontend/src/App.tsx` declares one flat `<Route path="/settings/...">`
  per settings page.
- `src/frontend/src/pages/SettingsArtifactsPage.tsx` holds `KIND_NAV` (five
  entries: template / skill / agent / pipeline / index) plus a `KIND_ORDER`-built
  per-kind record, and renders `.item-row` / `.item-row-main` /
  `.item-row-title` / `.item-row-meta` rows with `data-testid` attributes.
- The frontend has **no test runner** (it does not declare `vitest`), so this
  task verifies structurally in a real browser, not with a unit test runner.

**After / Outputs:**

- `src/frontend/src/pages/SettingsActionsPage.tsx` — the catalogue list
  (`.item-list` / `.item-row` family) showing per Action: id, description,
  implementation kind, the contributing plugin id where there is one, and a
  broken badge naming what no longer resolves; plus the one-Action editor
  (`.input` / `.btn` / `Save changes` conventions) with typed-input rows each
  carrying a required toggle, an `allowed_callers` field, a
  `needs_confirmation` toggle and a single implementation picker that allows
  exactly one of skill / http / ui.
- `src/frontend/src/features/settings/actionsApiClient.ts` — the API client,
  same shape as the existing `artifactsApiClient.ts`.
- One more `SETTINGS_SECTIONS` entry and one more `<Route>`.
- `SettingsArtifactsPage.tsx` gains the sixth `KIND_NAV` entry (`action`).
- A refused save renders the backend's own message naming the cause; the screen
  never invents its own wording for it.

---

## Files to Modify

- `src/frontend/src/pages/SettingsActionsPage.tsx` (new)
- `src/frontend/src/features/settings/actionsApiClient.ts` (new)
- `src/frontend/src/pages/SettingsPage.tsx` (one `SETTINGS_SECTIONS` entry)
- `src/frontend/src/App.tsx` (one route)
- `src/frontend/src/pages/SettingsArtifactsPage.tsx` (sixth `KIND_NAV` entry + the `ArtifactKind` union)
- `src/frontend/src/features/settings/artifactsApiClient.ts` (the `ArtifactKind` type, if the union lives there)
- `src/backend/app/api/actions_router.py` — **added 2026-10-18, authorised against `ESC-069`.**
  Two changes only, both needed for this task's own `AC-06` step to pass:
  (a) the list response must carry `plugin_id` for a plugin-contributed Action — it is
  dropped today because the list builds an explicit dict while the detail route returns
  the `Action` model; (b) map `PluginContributedActionIsReadOnlyError` to **409** with the
  error's own message, matching how `T03` mapped the Manager's other refusals — without it
  a PUT on a plugin Action returns 500 and the screen cannot say why it is read-only.
  Nothing else in that file is in scope.

---

## Constraints

- Inherits from parent story.
- **Functional-first on already-approved conventions** (story Notes → Prototype
  parity): reuse the live `.item-list`/`.item-row` and `.input`/`Save changes`
  families; introduce no new visual system. Visual polish is an out-of-band
  spot-check, never a locked AC.
- Every assertion below is on **DOM structure**, not on computed CSS, colour or
  hover state.
- The implementation picker enforces exactly one choice in the UI, but the
  backend refusal is still rendered when it fires — the screen is not the
  enforcement point.
- Plugin-contributed Actions render read-only (no edit/delete controls), matching
  the backend refusal from `T05`.

---

## Tests

**Manual verification steps** (real backend on `127.0.0.1:8001` + `npm run dev`;
headless-Edge/CDP screenshot and DOM reads are this project's established
technique — read the DOM back at least ~500ms after any dispatched state
change):

1. `[REQ-SB-95-US-02-AC-01]` Open `/settings` and confirm an Actions card is
   present in the `settings-grid`; click it and confirm it routes to the Actions
   page. Create an Action through the editor with two typed inputs (one
   required, one optional), an `allowed_callers` value and the confirmation
   toggle on; save; confirm a new `.item-row` renders with its id, description
   and implementation kind, and that reopening it shows exactly the inputs,
   required flags, callers and confirmation setting that were saved.
2. `[REQ-SB-95-US-02-AC-02]` Save an Action naming an implementation that does
   not resolve; confirm an error region renders carrying the backend's own
   message naming what did not resolve, and that no new `.item-row` appears.
   Correct the implementation, save, confirm the row appears.
3. `[REQ-SB-95-US-02-AC-03]` Attempt to save with no implementation selected and
   confirm the save is refused with the exactly-one message rendered; confirm
   the picker structurally cannot hold two implementations at once (assert on
   the DOM that selecting a second clears the first).
4. `[REQ-SB-95-US-02-AC-04]` Open `/settings/artifacts`; confirm an
   `[data-testid="artifacts-tab-action"]` nav item is present beside the five
   existing tabs, that selecting it lists the real Actions as `.item-row`
   entries, and that each pre-existing tab still lists exactly what it listed
   before.
5. `[REQ-SB-95-US-02-AC-06]` With a plugin installed that registers an Action,
   confirm its row renders in the same list, shows the contributing plugin id,
   and exposes no edit/delete control.
6. `[REQ-SB-95-US-02-AC-07]` Break a saved Action's implementation (undeploy the
   Skill it names), reload the catalogue, and confirm the row renders a broken
   indicator naming what no longer resolves — without anything having called the
   Action.

**Automated tests:** `n/a — the frontend declares no test runner (CLAUDE.md:
"no tests and does not declare vitest"); verified structurally in a real
browser as above.`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Actions catalogue page + one-Action editor on existing approved conventions
- [x] Settings card and route added; sixth `KIND_NAV` tab on the Artifacts page
- [x] Backend refusal messages rendered verbatim
- [x] Broken state and plugin attribution visible in the list
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The Workflows screen and the seventh Artifacts tab — `REQ-SB-95-US-04-T07`.
- Any confirmation / call surface — `REQ-SB-95-US-03`.
- Visual polish beyond reusing the approved families (out-of-band spot-check).

---

## Context / Notes

`architecture.md` → **§Action Catalogue — the Sixth Artifact Kind**, final
bullet: a new Settings page on the already-approved `.item-list`/`.item-row` +
`.input`/`Save changes` families plus one more card in the live
`SETTINGS_SECTIONS` grid. The story's Notes record the operator's own
2026-08-31 functional-first precedent that makes this the right order.

---

## Implementation Log

**Built 2026-10-18.** Backend suite **476 passed** before the first edit (measured
in this session, not quoted) and **476 passed** after — no test added, none broken.
Frontend: `npx tsc --noEmit` exit 0 and `npx oxlint src` exit 0, with no warning in
either new file (the twelve oxlint warnings it reports are all pre-existing, in
files this task did not touch).

### How this was verified

The frontend declares no test runner, so every AC below is a **real-browser DOM
read**, not an assertion about source. Verification ran against a deliberately
**isolated install** — its own uvicorn on `127.0.0.1:8011` with a scratch
`VAULT_PATH` / `SECOND_BRAIN_DATA_PATH` / `HERMES_HOME_PATH`, and its own Vite on
`5199` pointed at it with `VITE_API_BASE_URL` — so that installing and uninstalling
a plugin, and creating and breaking real Actions, could not touch the operator's
live vault, data path or Hermes install. Six other sessions share this checkout and
had a backend on `8001` and a dev server on `5173` running throughout; neither was
touched. Driving was headless Edge over CDP (this project's established technique),
reading the DOM back ≥500ms after every dispatched state change.

A throwaway plugin (`demo-reporter`) mounted `GET /plugins/demo-reporter/report`
and registered one Action through `api.register_action` — the real facade, not a
stub — which is what makes `AC-06` and `AC-07` real rather than simulated.

### Locked ACs — observed outcomes

- **`REQ-SB-95-US-02-AC-01` — PASS.** `/settings` renders 11 cards in
  `.settings-grid`; the Actions card is present (`bolt`, `href="/settings/actions"`)
  and clicking it routes to `/settings/actions` (`location.pathname` read back,
  `<h1>Actions</h1>`). Created `weekly-digest` through the editor with two typed
  inputs (`week`/string/**required**, `include_drafts`/boolean/optional),
  `allowed_callers` = `research-hub, inbox-triage`, confirmation **on**, and a `ui`
  implementation. After save a new `.item-row` rendered carrying its id, its
  description and its implementation kind ("In-app feature"). Reopening it read back
  **exactly** what was saved: both inputs in order with `required` true/false
  respectively, the same callers string, `needs_confirmation` checked, the `ui`
  radio checked and `/settings/artifacts` in its field, plus `created_at` rendered
  as a fact.
- **`REQ-SB-95-US-02-AC-02` — PASS.** Saving `nightly-rollup` against
  `ui feature_key = /nowhere-at-all` rendered the backend's own sentence verbatim in
  `[data-testid="action-editor-error"]`: *"this Action's ui implementation does not
  resolve on this install: ui feature key '/nowhere-at-all' is not registered in
  this app's front end"*. The row count stayed at 2 and no `nightly-rollup` row
  appeared; the editor stayed open holding what was typed. Correcting the key to
  `/browse` and saving again produced the row.
- **`REQ-SB-95-US-02-AC-03` — PASS.** With no implementation chosen (all three
  radios read `false`), saving was refused and the screen rendered the backend's own
  *"an Action has exactly one implementation -- one of skill, http or ui, never zero
  and never two; this one names none"*; no row appeared. Exclusivity asserted on the
  DOM: after clicking `skill`, `{skill:true, http:false, ui:false}`; after clicking
  `http`, `{skill:false, http:true, ui:false}`; after `ui`,
  `{skill:false, http:false, ui:true}` — and the previous kind's own field is gone
  from the DOM each time (read back as `null`), so a second choice clears the first
  structurally rather than by a handler.
- **`REQ-SB-95-US-02-AC-04` — PASS.** `/settings/artifacts` renders six nav items,
  `artifacts-tab-action` ("Actions", `bolt`) beside the five existing ones;
  selecting it lists the real Actions as `.item-row` entries. Each pre-existing tab
  was then compared **row-for-row against the backend's own `GET /artifacts`**
  grouped by kind: template 6/6, skill 10/10, agent 1/1 all matched exactly, and
  pipeline and index (both genuinely empty on this install) rendered their honest
  `No Pipelines yet.` / `No Indexes yet.` empty states rather than being hidden.
  *Judgement call, recorded for spot-check:* "lists exactly what it listed before"
  was proved as DOM-equals-backend rather than by a literal before/after capture —
  the only changes to that page are additive (one `KIND_NAV` entry, one
  `KIND_ORDER` member, one label), and the five pre-existing kinds' inventory is
  `T04`'s already-tested backend code, untouched here.
- **`REQ-SB-95-US-02-AC-06` — PASS.** With `demo-reporter` installed, its
  `demo-weekly-report` row renders in the same list as the install's own, shows
  **"From the demo-reporter plugin"**, and exposes **no** edit and **no** delete
  control (`hasEdit:false, hasDelete:false`, against `true/true` on every stored
  row). A `PUT` issued from the page's own origin returns **409** with the Manager's
  sentence naming the plugin, so the screen has something true to say rather than a
  500.
- **`REQ-SB-95-US-02-AC-07` — PASS.** `plugin-backed-report` was saved **through the
  editor** against `http GET /plugins/demo-reporter/report` — it resolved, which
  also proves save-time resolution sees a plugin's mounted routes. The plugin was
  then uninstalled (its entry removed from `plugins/installed.json`) and the backend
  restarted; reloading the catalogue rendered that row with a **Broken** badge and
  the reason *"http route GET '/plugins/demo-reporter/report' is not on this app's
  route table"* — with nothing having called the Action. The plugin's own
  `demo-weekly-report` row vanished at the same moment, leaving the install's own
  Actions untouched (`AC-06`'s third clause, observed as a side effect).

`AC-05` is not this task's; it was verified by `T04`/`T07`.

### The two authorised backend changes (`ESC-069`)

Both shipped in commit `a015b95`, and nothing else in `actions_router.py` was
touched.

1. `GET /actions` carries `plugin_id` on a contributed entry. **Judgement call:** the
   key is **absent** on a stored Action rather than `null`. Three reasons, in order:
   the authorisation is worded "carry `plugin_id` **for a plugin-contributed
   Action**"; `ActionManager` deliberately gives a stored Action *no such attribute
   at all* ("rather than an empty one"), so an absent key is the wire shape that
   tells the truth; and it leaves the stored-Action list shape `T03` pinned in
   `tests/test_actions_api.py` byte-for-byte intact. The first attempt sent
   `plugin_id: None` on every row and broke that test — `tests/test_actions_api.py`
   is in no task's `## Files to Modify`, and rather than reach into it, the response
   was reshaped to the reading that needs no test change at all.
2. `PluginContributedActionIsReadOnlyError` → **409** with the error's own message,
   on both `PUT` and `DELETE` (the Manager raises it from both). Verified live:
   409 + the Manager's sentence, where both were 500 before.

### Judgement calls made inside scope (spot-check these)

1. **The exactly-one picker is a radio group**, not three toggles with a handler
   clearing the others. The browser enforces the invariant, so "selecting a second
   clears the first" is a property of the markup rather than of code that could
   regress — and `AC-03`'s DOM assertion is then meaningful.
2. **`allowed_callers` is one comma-separated field**, split and trimmed on save,
   joined with `, ` on read. An empty field saves an empty list, which the entity
   documents as a real state ("a catalogued Action nothing may call yet") — it is
   not treated as "unset".
3. **Save is never disabled.** A draft naming no implementation is sent and refused
   by the backend, because the Manager's sentence is the only wording that names the
   actual cause. The screen's only authored text around it is a `Save refused`
   badge; the message itself is rendered verbatim.
4. **`/settings/actions` was deliberately NOT added to `UI_FEATURE_KEYS`.** That
   tuple lives in `business/core/actions/action.py`, which is not in this task's
   `## Files to Modify`, and its comment claims to be "verbatim from
   `src/frontend/src/App.tsx`" — it is now one route stale, so an Action whose `ui`
   implementation names this new screen would be refused as unregistered. No AC
   needs it. Logged as **`ESC-071`** rather than reached for.

### Out-of-scope file carried into the commit (`ESC-070`)

`src/frontend/src/features/settings/ArtifactExportModal.tsx` holds a second
`Record<ArtifactKind, string>`. Widening the union to `'action'` — which this task's
file list explicitly authorises — makes that map fail `TS2741` and breaks `tsc -b`
for the whole shared checkout. The one-line `action: 'Action'` entry was already in
the working tree, authored by a parallel session unblocking its own build; it is
committed here (`b590b1a`) so the union and its maps land together, since either
alone leaves a clean checkout broken in one direction. All five
`Record<ArtifactKind, …>` / `ArtifactKind[]` sites were then checked by hand and by
`tsc`: the export modal, this page's own `KIND_LABELS`, `KIND_ORDER`, `byKind<T>()`
and `SelectionState` — the last three are built *from* `KIND_ORDER`, which is why
adding the kind there (not only to `KIND_NAV`) is what keeps `groupedByKind` from
silently dropping every Action.

### Scope

Only the seven files in `## Files to Modify` plus `ArtifactExportModal.tsx` above,
and the standing `CHANGELOG.md` / `MEMORY.md` / status propagation. No ADR created
or deviated from; no new dependency; `app/business/` was not touched.

gate: flagged 2026-10-18 — triggers 1 and 7: the four judgement calls above, and
the out-of-scope map entry (`ESC-070`, resolved in this commit) plus the stale
feature-key list (`ESC-071`, open).
