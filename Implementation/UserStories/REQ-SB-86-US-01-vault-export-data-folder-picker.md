---
id: REQ-SB-86-US-01
title: Settings → Vault → Export Data — real folder-tree browser, multi-select, `.md` quick filter
requirement_ids: [REQ-SB-86]
requirement_section: "REQ-SB-86: Vault Data Sharing — Export a Real Slice of the Vault (`.sbd`)"
phase: P2
status: Done
gate: clear
gate_reason: "Was flagged net-new-design-needed (no html-prototype/ coverage). Resolved 2026-09-01: the operator's same-day REQ-SB-85 override (\"No Design we will design later\" / \"Follow the [P]ath design will be done after the task is working\") is extended to this sibling requirement, under the same standing autopilot authorization that scoped REQ-SB-86 itself (\"Once the current story is done work that one out ... otherwise auto pilot\"). Original analyst finding preserved below, not erased."
sprint: "SPRINT-081"
created: 2026-09-01
updated: 2026-09-01
---

<!-- Coder pass (2026-09-01): REQ-SB-86-US-01-T01 built and verified Done
(AC-01 confirmed live against the real vault directory — see the task's own
Implementation Log for the full verification record). status: Ready →
In Progress; story is not yet Done since T02 (the frontend picker page,
depends_on T01) remains Ready. -->

<!-- Coder pass (2026-09-01): REQ-SB-86-US-01-T02 built and verified Done
(AC-01..AC-05, all live against the real running app/backend/vault — see
the task's own Implementation Log for the full verification record). Both
tasks now Done, all 5 locked ACs verified. status: In Progress → Done. -->


# REQ-SB-86-US-01 — Settings → Vault → Export Data — real folder-tree browser, multi-select, `.md` quick filter

## Story

**As a** Second Brain operator
**I want** a new Settings → Vault → Export Data screen that shows my real
vault's own folder tree, lets me browse and select whichever folders and
files I want to share, and optionally filter the tree down to `.md` files
only
**So that** I have one place to build a real selection of vault content
(e.g. a Customer's own folder, an Industry KB) to hand to the Export flow
(`REQ-SB-86-US-02`)

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-86: Vault Data Sharing — Export a
  Real Slice of the Vault (`.sbd`)* — "A new **Settings → Vault → Export
  Data** section shows the real vault's own folder tree, browsable and
  selectable — the operator picks whichever folders/files they want to
  share, not a fixed export scope. A quick filter can narrow the tree to
  `.md` files only (for picking specific notes rather than whole folders
  indiscriminately)."
- **Deliberately separate from `REQ-SB-85`'s Settings → Artifacts** — the
  operator was explicit these are two different concepts: "*Right now
  moving my Deployment... Export the Basic Skills or Template or Agents*"
  (capability, `REQ-SB-85`) vs. "*I want to share my customer data or my
  Industry Knowledge*" (real vault data, this requirement). This story is
  the first of two this requirement splits into — matching this project's
  own established large-requirement precedent (`REQ-SB-85`'s own
  browser/export/import 3-way split) — a real folder-tree picker UI and
  the archive-production/attachment-resolution logic are each
  independently substantial; unlike `REQ-SB-85`, there is no third
  "Import" leg here (see Non-Goals).
- **PRD breadcrumb (2026-08-31, operator, verbatim):** "We can have the
  Data Export under settings Vault Export Data you can show the Folders
  and I can Select What to Export, may be a quick filter to show the Md
  file and i choose to export md file."
- **Settings → Vault already exists as a real, live area — confirmed
  directly, not assumed:** `src/frontend/src/pages/SettingsVaultPage.tsx`
  (landing/Overview) plus `SettingsVaultEntitiesPage.tsx`/
  `SettingsVaultTemplatesPage.tsx`/`SettingsVaultIndexFilteringPage.tsx`/
  `SettingsVaultIndexBuilderPage.tsx`, all routed under `/settings/vault/*`
  (`App.tsx`) and listed in one shared `VaultSettingsNav.tsx` sub-nav. This
  directly resolves the PRD's own still-open question — "whether Settings
  → Vault is a new top-level Vault settings area or an addition to an
  existing one" — it is confirmed to already exist; "Export Data" is a new
  entry added to the existing `VAULT_NAV_ITEMS` list, not a new area.
- **Same real, already-configured vault directory this whole project
  indexes** (`settings.vault_path`, `app/config.py`) — not a new data
  source. The real Manager gateway every other Settings → Vault page
  already routes through is `VaultManager`
  (`app/business/core/vault/vault_manager.py`, `app/api/vault_router.py`'s
  `/vault/overview`, `/vault/index-config`, `/vault/templates`,
  `/vault/entities`) — the natural place a new real filesystem-tree read
  is added, not a new Manager.
- **Must be a genuine, unfiltered filesystem walk — NOT the existing
  note-index primitives, confirmed by direct reading, not assumed:**
  `list_all_note_paths()`/`list_notes_in_kind_folder()`
  (`app/obsidian/notes.py`) deliberately EXCLUDE OKF-reserved files
  (`index.md`/`log.md`/`captures.md`) and any `_`-prefixed folder (this
  project's own "keep on disk, hide from live app" archive convention,
  e.g. `_assets`) from the ordinary note index — confirmed directly in
  `list_all_note_paths()`'s own docstring. A folder the operator wants to
  share (a whole Customer/Industry directory) genuinely includes these —
  the picker must show and allow selecting them too, not silently omit
  them the way the note index does. This is exactly what the PRD's own
  "the same way the vault's own `_assets` folders already work" line
  refers to.
- **Sibling precedent:** `REQ-SB-85-US-01` (Artifact Browser) — the same
  "browsable, multi-selectable inventory feeding an Export flow" shape,
  just over real vault filesystem content instead of artifact Managers.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then
edge cases and error states. Do NOT add AC-IDs — the decomposer assigns
them at /plan-tasks. -->

### Scenario 1: Opening Export Data shows the real vault's own folder tree

```gherkin
Given the operator's own configured vault directory (settings.vault_path)
    contains real folders and files
When the operator opens Settings → Vault → Export Data
Then the real folder tree of that vault directory is shown, browsable,
    reflecting the vault's actual current structure — never a fabricated
    or stale sample
```
<!-- AC-ID: REQ-SB-86-US-01-AC-01 -->

### Scenario 2: Selecting a folder includes every file within it

```gherkin
Given the Export Data folder tree is showing real folders and files
When the operator selects a folder (e.g. a Customer's own folder)
Then every file within that folder, including files in its nested
    subfolders, is included in the selection
  And the operator can also select individual files directly, independent
    of any folder selection
```
<!-- AC-ID: REQ-SB-86-US-01-AC-02 -->

### Scenario 3: The `.md` quick filter narrows the tree to markdown files only

```gherkin
Given the operator wants to pick specific notes rather than a whole folder
When the operator turns on the .md quick filter
Then the folder tree narrows to show only .md files (and the folders that
    contain at least one)
  And a folder that genuinely contains no .md files anywhere beneath it is
    shown honestly as filtered out, never presented as if it were empty by
    mistake or hidden without explanation
```
<!-- AC-ID: REQ-SB-86-US-01-AC-03 -->

### Scenario 4: Clearing a selection

```gherkin
Given the operator has selected one or more folders/files
When the operator activates the clear-selection control
Then no folder or file remains selected
  And the underlying folder tree itself, and the active .md filter state,
    are unchanged
```
<!-- AC-ID: REQ-SB-86-US-01-AC-04 -->

### Scenario 5: Reachable from Settings → Vault

```gherkin
Given the operator is on the Settings → Vault landing page (Overview)
When the operator looks for a way to share a slice of the vault
Then a new "Export Data" item is present in the existing Settings → Vault
    navigation, alongside Overview/Entities/Templates/Index Filtering/
    Index Builder
  And selecting it navigates to Settings → Vault → Export Data
```
<!-- AC-ID: REQ-SB-86-US-01-AC-05 -->

## Affected Screens

- New `src/frontend/src/pages/SettingsVaultExportDataPage.tsx` —
  genuinely new screen; **`net-new-design-needed`** — no `html-prototype/`
  screen shows a folder-tree multi-select picker anywhere (confirmed by
  direct inspection of the full prototype catalog, `html-prototype/
  index.html`).
- `src/frontend/src/features/settings/VaultSettingsNav.tsx` — gains one
  more `VAULT_NAV_ITEMS` entry ("Export Data"), reusing the exact existing
  nav-item pattern, no new component.
- `html-prototype/settings.html` — **not** the design authority (same
  "real code supersedes a stale prototype" situation `REQ-SB-85-US-01`
  already established for `SettingsPage.tsx`; the real Settings → Vault
  area lives entirely in `SettingsVaultPage.tsx`/`VaultSettingsNav.tsx`,
  not in the prototype). Not touched.

## Dependencies

- **Related to:** `REQ-SB-86-US-02` (Export) — this story's own selection
  is the entry point that story's export flow consumes.
- **Related to, not blocking:** `REQ-SB-85` (Artifact Export/Import,
  `.sbf`) — sibling capability-sharing mechanism; deliberately separate,
  no shared code expected beyond the general "Settings sub-area with a
  real listing + multi-select" shape.
- **External:** none new — this story adds zero new write path (read/
  list/select only).

## Constraints

- Read-only browsing/selection only — no file/folder create/edit/delete/
  rename happens from this screen.
- The tree reflects the real, current vault directory on disk
  (`settings.vault_path`) — never a cached/stale snapshot beyond whatever
  the underlying filesystem read naturally returns at request time.
- The multi-select selection itself is ephemeral, client-side state
  (mirrors `REQ-SB-85-US-01`'s own established precedent) — it exists
  only to be handed to the Export flow (`REQ-SB-86-US-02`), not persisted
  anywhere.
- The `.md` quick filter narrows visibility/selectability; it never
  deletes or alters selection state already made before the filter was
  toggled — the exact interaction mechanics of "an already-selected
  non-`.md` file while the filter is on" are left to `/plan-tasks` (a UI
  mechanics detail, not a locked business rule).

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-86-US-01-T01 | backend | New real, unfiltered vault-directory tree-listing endpoint (folders + files, includes OKF-reserved files and `_`-prefixed folders that `list_all_note_paths()` deliberately excludes) | `app/api/vault_router.py`, `app/business/core/vault/vault_manager.py` | `../Tasks/REQ-SB-86-US-01-T01-vault-export-tree-endpoint.md` |
| REQ-SB-86-US-01-T02 | frontend | `SettingsVaultExportDataPage.tsx` — folder-tree browse + multi-select + `.md` quick filter UI; new nav entry on `VaultSettingsNav.tsx`; new route | `src/frontend/src/pages/SettingsVaultExportDataPage.tsx` (new), `src/frontend/src/features/settings/VaultSettingsNav.tsx`, `src/frontend/src/features/settings/vaultApiClient.ts`, `src/frontend/src/App.tsx` | `../Tasks/REQ-SB-86-US-01-T02-export-data-tree-page.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Producing the `.sbd` archive itself, attachment resolution, flat/
  hierarchy extraction** — `REQ-SB-86-US-02`.
- **Import of a `.sbd` file** — explicitly out of scope for `REQ-SB-86`
  per the operator's own "we will get to it later" (confirmed against the
  PRD's own current entry, which is export-only).
- **Any create/edit/delete/rename of vault content** from this screen.
- **Persisting a selection across sessions/reloads.**
- **Secret-scanning selected content** — this is deliberately real,
  already-trusted vault data the operator is choosing to share on purpose
  (unlike `REQ-SB-85`'s capability bundles); no scan machinery applies
  (see sibling story's own Constraints).

## Notes

**Prototype parity:**

- Settings → Vault sub-nav (Overview/Entities/Templates/Index Filtering/
  Index Builder) — **Specced** (Scenario 5); the new "Export Data" item
  reuses the exact live `VaultSettingsNav.tsx` pattern, no new component.
- Folder-tree browse + multi-select + `.md` quick filter —
  **`net-new-design-needed`** (Scenarios 1-4) — no prototype screen
  anywhere shows a folder-tree picker (confirmed against the full
  `html-prototype/index.html` catalog).

**Why `gate: flagged`:**

1. No material assumption fills a genuine PRD gap in the Gherkin itself —
   every scenario asserts only what the PRD's own text and the operator's
   own same-day breadcrumb already resolve (folder tree, multi-select,
   `.md` quick filter, reachable under the existing Settings → Vault
   area). One grounding finding, not an assumption: the picker must be a
   genuine unfiltered filesystem walk, not the existing note-index
   primitives, since those deliberately exclude OKF-reserved files and
   `_`-prefixed folders a real folder share needs to include — confirmed
   directly by reading `list_all_note_paths()`'s own docstring, not
   guessed.
2. `REQ-SB-86` is not marked `<!-- Draft -->`/unfinalised in the PRD —
   its body text and the operator's own same-day breadcrumb are both
   fully resolved (confirmed by direct reading, `Documentation/PRD.md`
   line 4500 onward).
3. N/A directly (architect/ADR trigger) — this story composes only the
   already-real `VaultManager`/`settings.vault_path`, adding one new
   read-only listing method; not expected to need a new ADR on its own.
4. No `ESCALATIONS.md` entry written by this pass.
5. Not oversized — 2 tasks, a pure read/list backend endpoint plus one
   new frontend page, directly mirroring `REQ-SB-85-US-01`'s own
   (smallest-of-its-siblings) shape.
6. N/A (coder trigger).
7. No contradictory PRD inputs.
8. **The controlling flag: `net-new-design-needed`** — a folder-tree
   multi-select picker has no prior approved screen anywhere in
   `html-prototype/` (confirmed directly against the catalog's own full
   screen list before writing this story). Recommend a `/design
   REQ-SB-86` pass covering this story's picker alongside its sibling
   `REQ-SB-86-US-02`'s own export-options screen as one related flow,
   before `/plan-tasks` cuts either frontend task — OR the same
   operator-authorized "build functional-first, design after" override
   already applied to `REQ-SB-85`'s three siblings this same day, if the
   operator wants to extend that same call here (**not assumed on this
   story's own authority** — the launching task for this batch resolved
   `REQ-SB-86`'s content questions directly but did not address whether
   the design-first gate is waived for this requirement too, so it is
   flagged here rather than silently carried over).

gate: flagged 2026-09-01 — trigger-8/net-new-design-needed (folder-tree
multi-select picker, zero prototype coverage). See `REVIEW-QUEUE.md`.

**Resolved 2026-09-01 (orchestrator, on the operator's standing
authorization):** the operator's own same-day `REQ-SB-85` design-gate
override — "No Design we will design later" / "Follow the [P]ath design
will be done after the task is working" — is extended to this sibling
requirement. `REQ-SB-86` itself was scoped by the operator under the same
"ask now or auto pilot" framing, with no question raised at that time;
extending an already-decided, same-day precedent to the identical
`net-new-design-needed` trigger on a directly analogous sibling story is
squarely inside "trust your judgement," not a new open question. `gate`
set to `clear`; this analysis is preserved, not deleted.

**Architect pass (2026-09-01):** Verified directly against
`architecture.md`, `ADR.md`, and the real `vault_manager.py`/
`vault_router.py` code, not accepted on this story's own say-so — **no new
ADR needed.** The new folder-tree-listing method is a pure read-only
addition to the already-Accepted `VaultManager` gateway, following that
Manager's own already-established "one more dict/list-returning read
method" shape (`get_index_config()`/`list_templates()`/`list_entities()`
are the direct precedent — confirmed by reading `vault_manager.py`
directly). No new store, no new Manager, no structural boundary crossed.
`architecture.md` gained a new `## Vault Data Export` → `§Export Data
Folder-Tree Picker` section recording this.

**Architecture scope:** §Vault Data Export → §Export Data Folder-Tree
Picker (`architecture.md`) — bounds the coder to: one new read-only
tree-listing method on `VaultManager`
(`app/business/core/vault/vault_manager.py`), one new `GET` route on the
existing `app/api/vault_router.py`, and the new
`SettingsVaultExportDataPage.tsx`/`VaultSettingsNav.tsx` frontend pair. No
other architecture section applies.

gate: clear 2026-09-01 — architect pass, no ADR triggers fired (confirmed,
not assumed: pure read-only extension of the already-Accepted `VaultManager`
gateway; no assumption made beyond what the story's own prior resolution
already settled).

**Decomposer pass (2026-09-01):** Locked all 5 Gherkin scenarios as
`REQ-SB-86-US-01-AC-01`..`AC-05` (tags appended after each closing fence
above) — untagged Gherkin tightened only for AC-ID assignment, no wording
changes needed beyond that. Created `REQ-SB-86-US-01-T01`
(`vault_manager.py` tree-listing method + `GET` route on
`vault_router.py`) and `REQ-SB-86-US-01-T02` (`SettingsVaultExportDataPage.tsx`
+ nav entry + route), `T02 depends_on: [T01]` (needs the real endpoint to
render against). Every locked AC has at least one AC-tagged verification
step across the two tasks (`AC-01` appears on both — a real backend content
check on `T01`, a real rendered-screen check on `T02`). No cycles. `status`
advanced `Draft → Ready`; both tasks written at `status: Ready` in
lockstep. `gate` stays `clear` — no MUST-FLAG trigger fired at this step
(no new assumption, `REQ-SB-86` not `<!-- Draft -->`, no ADR
created/changed by this step, no `ESCALATIONS.md` entry, not oversized —
2 tasks matching the pre-sketched table, every locked AC verifiable via a
real observable outcome, no contradictory inputs, no genuinely unclear
work — the task breakdown was already pre-sketched and confirmed sound).
