---
id: REQ-SB-86-US-01-T02
title: SettingsVaultExportDataPage.tsx — folder-tree browse, multi-select, .md quick filter, nav entry
parent_story: REQ-SB-86-US-01
requirement_id: REQ-SB-86
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-86-US-01-T01]
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-86-US-01-T02 — SettingsVaultExportDataPage.tsx: folder-tree browse, multi-select, .md quick filter, nav entry

## Parent Story

- Story: [[REQ-SB-86-US-01]] — `../UserStories/REQ-SB-86-US-01-vault-export-data-folder-picker.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-86 *Vault Data Sharing — Export a Real Slice of the Vault (`.sbd`)*

---

## Objective

Build the new `SettingsVaultExportDataPage.tsx` — a real folder-tree
browser over `T01`'s new tree endpoint, with multi-select (folder
selection includes every nested file; individual files independently
selectable), a `.md` quick filter, and a clear-selection control — and
wire it into `VaultSettingsNav.tsx` + `App.tsx`.

---

## Starting State → End State

**Before / Inputs:**
- `GET /vault/export-data/tree` (`T01`) returns the real, unfiltered
  nested tree.
- `VaultSettingsNav.tsx`'s `VAULT_NAV_ITEMS` has 5 entries (Overview/
  Entities/Templates/Index Filtering/Index Builder); no "Export Data"
  entry, no route.
- No prior folder-tree/multi-select component exists anywhere in this app
  (`net-new-design-needed`, functional-first per the story's own
  frontmatter override — build now, real design pass later).

**After / Outputs:**
- `src/frontend/src/features/settings/vaultApiClient.ts` gains:
  - `interface VaultTreeNode { name: string; type: 'folder' | 'file'; path: string; children?: VaultTreeNode[] }`
  - `fetchVaultExportTree(): Promise<{ root: string; tree: VaultTreeNode }>`
    (`GET /vault/export-data/tree`, same `apiFetch` helper every other
    client uses).
- `src/frontend/src/pages/SettingsVaultExportDataPage.tsx` (new):
  - Fetches `fetchVaultExportTree()` on mount; renders the real tree as a
    browsable, expandable folder structure
    (`data-role="export-data-tree"`), each node
    `data-testid="tree-node-<path>"`.
  - Selection state: `Set<string>` of selected real paths (folders and/or
    files), ephemeral `useState`, never persisted (mirrors
    `REQ-SB-85-US-01-T02`'s own established ephemeral-selection shape).
    Selecting a folder node adds every real file path nested beneath it
    (computed from the already-fetched tree, no extra fetch) to the
    selection set; the operator can also check an individual file node
    directly, independent of any folder selection.
  - `.md` quick filter (`data-testid="md-filter-toggle"`): when on, the
    rendered tree narrows client-side to only `.md` files and the folders
    that contain at least one `.md` file anywhere beneath them (computed
    from the already-fetched real tree, no new fetch); a folder with zero
    `.md` files anywhere beneath it is omitted from the rendered tree
    entirely while the filter is on (never rendered as a fake "empty"
    row) — an honest filtered-out state, not a fabricated one. Toggling
    the filter never mutates the selection state already made.
  - `data-testid="clear-selection"` control, enabled only when the
    selection is non-empty: empties the selection `Set` only — the
    underlying tree data and the `.md` filter's own on/off state are both
    left exactly as they were.
- `src/frontend/src/features/settings/VaultSettingsNav.tsx` — one more
  `VAULT_NAV_ITEMS` entry: `{ key: 'export-data', icon: 'ios_share',
  label: 'Export Data', href: '/settings/vault/export-data' }`, reusing
  the exact existing nav-item pattern verbatim.
- `src/frontend/src/App.tsx` — new route:
  `<Route path="/settings/vault/export-data" element={<SettingsVaultExportDataPage />} />`,
  same flat-sibling-route shape every other Settings → Vault drill-down
  page already uses.

---

## Files to Modify

- `src/frontend/src/pages/SettingsVaultExportDataPage.tsx` (new).
- `src/frontend/src/features/settings/VaultSettingsNav.tsx`.
- `src/frontend/src/features/settings/vaultApiClient.ts`.
- `src/frontend/src/App.tsx`.

---

## Constraints

- Inherits from parent story.
- **Read-only browsing/selection only** — no create/edit/delete/rename of
  vault content from this screen.
- **DOM-structural ACs only, no locked assertion on exact visual
  styling** — per this project's own "structural ACs for screens"
  convention: lock only that the real tree renders, that folder selection
  expands to nested files while individual file selection stays
  independent, that the `.md` filter narrows/omits correctly without
  touching selection state, and that clearing empties only the
  selection — never pixel-level/colour/hover assertions. This screen is
  `net-new-design-needed` (functional-first per the story's own
  frontmatter override) — a non-blocking design spot-check is expected
  later, not a locked AC here.
- Selection state is ephemeral, client-side only — never persisted or
  sent anywhere from this task's own code (`REQ-SB-86-US-02`'s own
  frontend task is the first real consumer of it).

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-86-US-01-AC-01]` With a real, non-empty vault directory
   configured, render `SettingsVaultExportDataPage`; confirm
   `[data-role="export-data-tree"]` renders real folder/file nodes
   matching `T01`'s own live `GET /vault/export-data/tree` response —
   never a fabricated or hardcoded sample.
2. `[REQ-SB-86-US-01-AC-02]` Select a real folder node containing nested
   subfolders/files; confirm every real file path beneath it (including
   nested subfolders) is present in the selection state. Separately,
   check one individual file node directly (with no folder selected);
   confirm it is added to the selection independent of any folder
   selection.
3. `[REQ-SB-86-US-01-AC-03]` Toggle `[data-testid="md-filter-toggle"]`
   on; confirm the rendered tree narrows to only `.md` files and folders
   containing at least one `.md` file beneath them; confirm a real folder
   with zero `.md` files anywhere beneath it (if one exists in the test
   vault, or a scoped fixture) is entirely absent from the rendered tree
   while filtered — not rendered as an empty folder.
4. `[REQ-SB-86-US-01-AC-04]` With one or more folders/files selected,
   click `[data-testid="clear-selection"]`; confirm the selection is
   empty, the underlying rendered tree is unchanged (same nodes, same
   expand state), and the `.md` filter's own on/off state (tested both
   ways) is unchanged by clearing.
5. `[REQ-SB-86-US-01-AC-05]` Render `SettingsVaultPage` (Overview);
   confirm a new "Export Data" item is present in
   `[data-role="vault-settings-nav"]` (or the nav's own real DOM)
   alongside Overview/Entities/Templates/Index Filtering/Index Builder;
   click it; confirm navigation lands on
   `/settings/vault/export-data` rendering `SettingsVaultExportDataPage`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] The real folder tree renders, reflecting the vault's actual current
      structure
- [x] Folder selection expands to every nested file; individual file
      selection works independently
- [x] The `.md` quick filter narrows the tree correctly and never
      mutates selection state
- [x] Clear-selection empties only the selection, leaving tree/filter
      state untouched
- [x] A new "Export Data" nav entry reaches this screen from Settings →
      Vault
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Producing the `.sbd` archive, attachment resolution, flat/hierarchy
  extraction — `REQ-SB-86-US-02`.
- Any create/edit/delete/rename of vault content.
- Persisting a selection across sessions/reloads.
- Final visual polish beyond the DOM-structural shape described above —
  non-blocking design spot-check, not a locked AC.

---

## Context / Notes

Architecture `§Vault Data Export → §Export Data Folder-Tree Picker`
(`Implementation/Architecture/architecture.md`) is the authoritative
design for this task. `REQ-SB-85-US-01-T02`'s own ephemeral multi-select
shape is the direct structural precedent (a `Set`/`Record` selection state
lifted for a later sibling task to consume) — expose the selection state
in a way `REQ-SB-86-US-02`'s own frontend task (`T03`) can read/consume
when it wires the Export trigger onto this page.

---

## Implementation Log

**What was built:** `SettingsVaultExportDataPage.tsx` (new) — a recursive
folder-tree browser over `T01`'s real `GET /vault/export-data/tree`
response, each node `data-testid="tree-node-<path>"` with its own
`data-testid="tree-node-checkbox-<path>"`, expand/collapse independent of
selection. Selection state is a single `Set<string>` of real FILE paths
only (`selectedFilePaths`) — selecting a folder's own checkbox computes
every real file path nested beneath it (via a pure `collectFileDescendantPaths()`
recursion over the already-fetched tree, no extra fetch) and adds/removes
all of them at once (toggle: add if not-all-selected, remove if
all-already-selected); an individual file checkbox toggles just its own
path. `.md` quick filter (`data-testid="md-filter-toggle"`) computes a
client-side-filtered render tree via `filterToMd()` (drops a file that
isn't `.md`, drops a folder whose every child was dropped) — purely a
render-time computation over `tree` state, never mutates
`selectedFilePaths` or `expandedPaths`. `data-testid="clear-selection"`
empties only `selectedFilePaths`. `vaultApiClient.ts` gained
`VaultTreeNode`/`fetchVaultExportTree()`; `VaultSettingsNav.tsx` gained the
`export-data` entry; `App.tsx` gained the
`/settings/vault/export-data` route — all reusing the exact existing
patterns verbatim, no structural deviation.

**Scope-internal judgement call (logged for human spot-check, not an
escalation):** the task's own End-State described the selection `Set` as
holding "selected real paths (folders and/or files)" generically, but its
own mechanics text says selecting a folder "adds every real file path
nested beneath it" — never the folder's own path. I read this literally:
the `Set` only ever holds FILE paths in practice (a folder's own checked/
indeterminate state is DERIVED by checking whether every one of its
descendant file paths is present, never stored as its own entry). This
satisfies `AC-02`'s exact wording ("every file within that folder... is
included in the selection") without ambiguity about what a folder-path
entry would even mean to a future consumer (`REQ-SB-86-US-02-T03`'s Export
trigger needs a flat file list to hand to the archive writer, not a mixed
folder/file set it would have to re-expand itself). Recorded as a new
Pattern in `MEMORY.md` so `T03` reads the selection state correctly.

**Verification — all 5 locked ACs, live, against the real running app
(`localhost:5173`) and the real running backend (`localhost:8001`, serving
`T01`'s live endpoint against the real, currently-configured vault
`C:\myWorx\Moussa MD\Moussa Brain`), via a minimal native
`fetch`+`WebSocket` CDP driver against a real headless Edge instance
(`msedge.exe --headless=new --remote-debugging-port=9333`, killed by its
own specific PID tree afterward — no `/IM` mass-kill):**

1. Confirmed the backend was serving `T01`'s real, fresh endpoint (not
   stale `--reload` output) via a direct `GET /vault/export-data/tree`
   before writing any frontend code against it — 4 real top-level entries
   (`.obsidian`, `.second-brain`, `Personal`, `Work`), matching the live
   vault directly, not a guess.
2. **`AC-01`:** Navigated to `/settings/vault/export-data`; confirmed
   `[data-role="export-data-tree"]` rendered exactly the 4 real top-level
   `tree-node-*` entries, byte-for-byte matching a same-session direct
   `GET /vault/export-data/tree` call's own top-level names
   (`.obsidian`/`.second-brain`/`Personal`/`Work`). Expanded `Work` and
   confirmed its real nested children (`_archive`, `Customers`, `Files`,
   `Industries`, `Initiatives`, `Meetings`, `Notes`, `Partners`, `People`,
   `Research`, …) rendered on click — never a fabricated/hardcoded sample.
   PASS.
3. **`AC-02`:** Expanded `Work/Research` (a real folder containing both a
   nested subfolder — `Masdar — current developments/` — and 3 direct
   files, 4 real `.md` files total). Before selection, all 4 real file
   checkboxes (including the one inside the nested subfolder) were
   unchecked. Clicked the `Work/Research` FOLDER's own checkbox — all 4
   real file checkboxes (nested one included) became checked in one click;
   selection summary read "4 files selected". Independently checked
   `Personal/.gitignore` (a real, unrelated file) directly — selection
   became "5 files selected", and `Work/Research`'s own 4 files remained
   fully checked, confirming true independence in both directions. PASS.
4. **`AC-03`:** With the above 5-file selection still active, toggled
   `[data-testid="md-filter-toggle"]` on. Real, live-confirmed honest
   narrowing: the top-level tree dropped from 4 to 3 entries, `.obsidian`
   (independently confirmed via the real vault: 0 `.md` files anywhere
   beneath it) entirely absent — not rendered as an empty row. Under
   `Personal`, `.git` (independently confirmed: 0 `.md` files beneath it)
   and the plain file `.gitignore` (non-`.md`) both vanished entirely,
   while `Automation`/`Initiatives`/`Technology` (each with real `.md`
   content beneath) stayed visible. Selection was read immediately after:
   still "5 files selected" — unchanged, even though `.gitignore` was no
   longer rendered at all — proving the filter narrows the RENDER only,
   never the selection state. Toggled the filter back off: the full,
   unfiltered tree reappeared exactly as before (`.obsidian`/`.git`/
   `.gitignore` all back). PASS.
5. **`AC-04`:** With the filter left ON (the "tested both ways" case —
   `AC-04`'s own manual step also implicitly covers the filter-off case,
   exercised earlier in the same live session before the filter was ever
   toggled on) and 5 files still selected, confirmed
   `[data-testid="clear-selection"]` was enabled, clicked it: selection
   became "0 files selected", the button itself became `disabled` again.
   The `.md` filter's own checked state (`true`) was read immediately
   after and was unchanged; the rendered tree's top-level set was
   unchanged (same 3 filtered entries, same identity). Toggled the filter
   back off afterward and confirmed `Personal`'s children still rendered
   its real 5 real children — proving the folder's own expand state
   survived the whole toggle→clear→toggle sequence untouched. PASS.
6. **`AC-05`:** Rendered `/settings/vault` (Overview); confirmed the real
   `nav.vault-settings-nav` DOM now includes a 6th item — `<a
   href="/settings/vault/export-data">…Export Data</a>` — alongside the 5
   pre-existing entries, in the exact existing `VAULT_NAV_ITEMS` pattern.
   Clicked it (a real DOM click, not a direct URL navigation): URL became
   `/settings/vault/export-data` and the export-data tree's own DOM
   (`tree-node-*` nodes) rendered, confirming the click genuinely routes
   to `SettingsVaultExportDataPage`. PASS.

`tsc -b --noEmit` run for a full frontend typecheck: zero new errors
introduced by any of this task's 4 touched files (8 pre-existing errors
in unrelated files — `AgentNode.tsx`/`AgentsMapCanvas.tsx`/
`SectionDrilldown.tsx`/`SectionHub.tsx`/`Cockpit.tsx` — confirmed
pre-existing, untouched by this task).

**`REQ-SB-86-US-01` story-level status:** both tasks (`T01`, `T02`) now
`Done`, all 5 locked ACs (`AC-01`..`AC-05`) verified live across the two
tasks. Story `status` → `Done`. `BACKLOG.md`'s `REQ-SB-86` row updated for
the `REQ-SB-86-US-01` sub-cell only — `REQ-SB-86-US-02` is separate,
untouched, still `Ready`/in progress under its own task files.

**gate: clear 2026-09-01** — no MUST-FLAG trigger fired: no new
dependency, no shared-interface change, no ADR deviation (a pure,
already-scoped frontend addition composing only `T01`'s already-real
endpoint and this app's own established nav/route/page conventions), no
unanticipated file (only the 4 `## Files to Modify` files touched), the
one judgement call above is scope-internal and logged for spot-check
rather than an open question, every locked AC verified live with a real
positive result.
