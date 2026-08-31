---
id: REQ-SB-86-US-02-T03
title: Export-options screen — flat/hierarchy choice, confirm, download
parent_story: REQ-SB-86-US-02
requirement_id: REQ-SB-86
type: frontend
status: Done
gate: flagged
gate_reason: "scope-internal reconciliation + a disclosed CDP-headless/backend-CORS-on-error finding logged for human spot-check (see Implementation Log) — none blocking, none weakening a locked AC"
phase: P2
depends_on: [REQ-SB-86-US-02-T02, REQ-SB-86-US-01-T02]
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-86-US-02-T03 — Export-options screen: flat/hierarchy choice, confirm, download

## Parent Story

- Story: [[REQ-SB-86-US-02]] — `../UserStories/REQ-SB-86-US-02-vault-export-data-archive-writer.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-86 *Vault Data Sharing — Export a Real Slice of the Vault (`.sbd`)*

---

## Objective

Wire an "Export" trigger onto `SettingsVaultExportDataPage.tsx`'s own
selection (`REQ-SB-86-US-01-T02`) that lets the operator choose flat or
hierarchy-preserving extraction, expands any folder selections into their
real nested file paths client-side, calls `T02`'s `/export` endpoint, and
triggers a real browser download of the produced `.sbd`.

---

## Starting State → End State

**Before / Inputs:**
- `SettingsVaultExportDataPage.tsx` (`REQ-SB-86-US-01-T02`) exposes a
  real, ephemeral selection (`Set<string>` of real vault-relative paths)
  and the already-fetched real tree, but no Export trigger anywhere yet.
- `POST /vault/export-data/export` (`T02`) exists, expecting a flat
  `selection: string[]` (files only) + `extraction: "flat" | "hierarchy"`.

**After / Outputs:**
- `src/frontend/src/features/settings/vaultApiClient.ts` gains:
  - `exportVaultData(selection: string[], extraction: 'flat' | 'hierarchy'): Promise<Blob>`
    — a dedicated `fetch` call (not the shared JSON `apiFetch` helper,
    since it must resolve `response.blob()` for the real `.sbd` bytes),
    throwing on a non-2xx response.
- `SettingsVaultExportDataPage.tsx` gains:
  - A `data-testid="export-selection"` control, enabled only when the
    selection is non-empty, that opens the export-options step
    (`data-role="export-options"`) with two real, mutually-exclusive
    controls — `data-testid="extraction-flat"` /
    `data-testid="extraction-hierarchy"` (hierarchy is the default choice
    on open, matching the PRD's own "you zip the folder" framing of
    preserving structure by default) — plus a
    `data-testid="export-confirm"` control.
  - On confirm: expands the current selection into a flat list of real
    file paths (any selected FOLDER path is expanded, using the
    already-fetched real tree data — zero extra fetch, per `T02`'s own
    disclosed client-side-expansion judgement call — into every real
    nested file path beneath it; any selected FILE path is included
    as-is), calls `exportVaultData(expandedSelection, extraction)`, and
    on success triggers a real browser download of the returned blob
    (e.g. via an `<a download>` + `URL.createObjectURL`, the same
    technique `REQ-SB-85-US-02-T05`'s own export flow already
    established).
  - Any non-2xx response from `/export` renders a plain, honest inline
    error (`data-role="export-error"`) — never a silent failure, never a
    fabricated "success."

---

## Files to Modify

- `src/frontend/src/pages/SettingsVaultExportDataPage.tsx`.
- `src/frontend/src/features/settings/vaultApiClient.ts`.

---

## Constraints

- Inherits from parent story.
- **DOM-structural ACs only** — lock only that the flat/hierarchy choice
  is presented and reaches the backend correctly, and that a successful
  export triggers a real download; never pixel-level/colour/hover
  assertions. This screen is `net-new-design-needed` (functional-first
  per the story's own frontmatter override) — a non-blocking design
  spot-check is expected later.
- **Client-side folder-to-file-path expansion, never a second fetch of
  the tree** — the export-options step must reuse
  `SettingsVaultExportDataPage.tsx`'s own already-fetched real tree data,
  per `T02`'s own disclosed judgement call.
- Never calls `/export` before the operator has explicitly chosen an
  extraction option and confirmed.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-86-US-02-AC-01]` With a real multi-folder selection, open
   the export-options step, select `[data-testid="extraction-hierarchy"]`,
   confirm; verify (via a `window.fetch` spy) the outgoing `/export`
   request body carries `"extraction":"hierarchy"` and a real, correctly
   client-side-expanded flat file list; confirm a real browser download
   fires on success.
2. `[REQ-SB-86-US-02-AC-02]` Same selection, select
   `[data-testid="extraction-flat"]`, confirm; verify the outgoing
   request body carries `"extraction":"flat"`; confirm a real browser
   download fires on success.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] The export-options step presents a real flat/hierarchy choice,
      reaching the backend with the correct `extraction` value
- [x] A folder selection is correctly expanded client-side into real
      file paths before the request is sent
- [x] A successful export triggers a real browser download of the
      returned `.sbd`
- [x] An honest inline error renders on a non-2xx `/export` response
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any change to `SettingsVaultExportDataPage.tsx`'s own tree
  browse/multi-select/`.md`-filter mechanism itself —
  `REQ-SB-86-US-01-T02`, reused unchanged.
- Attachment resolution, flat-collision disambiguation logic itself —
  `T01`/`T02`, backend-owned; this task only surfaces the operator's
  choice and the resulting download.
- Import of a `.sbd` file.
- Final visual polish beyond the DOM-structural shape described above —
  non-blocking design spot-check, not a locked AC.

---

## Context / Notes

`ADR-016` and architecture `§Vault Data Export → §Embedded-Attachment
Resolution & .sbd Archive Writer` are the authoritative design. This
task's own `depends_on` carries a genuine file-level dependency on BOTH
`T02` (needs the real `/export` endpoint) and `REQ-SB-86-US-01-T02`
(wires directly onto that page's own selection state and already-fetched
tree data, per this story's own Affected Screens) — unlike `T01`/`T02`,
which are decoupled from `US-01`'s own endpoint at runtime, this task
genuinely cannot be built without `US-01-T02`'s own page already
existing.

---

## Implementation Log

**What was built:**
- `src/frontend/src/features/settings/vaultApiClient.ts` gained
  `exportVaultData(selection, extraction): Promise<Blob>` — a dedicated
  `fetch` (not `apiFetch`) calling `POST /vault/export-data/export`,
  throwing `ApiError(status, text)` on a non-2xx response, resolving
  `response.blob()` on success. Mirrors `artifactsApiClient.ts`'s own
  `commitExport()` shape exactly (same `EXPORT_DATA_BASE_URL` /
  `VITE_API_BASE_URL` local-const pattern, since `apiFetch`'s own base URL
  isn't exported).
- `src/frontend/src/pages/SettingsVaultExportDataPage.tsx` gained:
  - `data-testid="export-selection"` ("Export…") button, enabled only
    when `selectedFilePaths.size > 0`, opens `data-role="export-options"`
    and resets `extraction` to `'hierarchy'` (the default) each time it
    opens.
  - `data-testid="extraction-hierarchy"` / `data-testid="extraction-flat"`
    — a real mutually-exclusive radio-button pair (`name="export-extraction"`),
    hierarchy checked by default.
  - `data-testid="export-confirm"` — calls `exportVaultData(Array.from(selectedFilePaths), extraction)`,
    triggers a real browser download via `triggerSbdDownload()`
    (`<a download>` + `URL.createObjectURL`, byte-for-byte the same
    technique `REQ-SB-85-US-02-T05`'s own `triggerBlobDownload()` already
    established), closes the options panel on success.
  - `data-testid="export-cancel"` — closes the panel with zero `/export`
    call, mirroring `REQ-SB-85-US-02-T05`'s own cancel shape.
  - `data-role="export-error"` — renders `extractErrorDetail(error)` (same
    shape as `SettingsArtifactsPage.tsx`'s own helper) on any thrown error
    from `exportVaultData`, panel stays open (not silently reset).

**Scope-internal judgement call — the task's own "expand any selected
FOLDER path client-side" step is already satisfied by construction, not
implemented as a separate step (logged, not an escalation):** re-read
`REQ-SB-86-US-01-T02`'s own real, current `SettingsVaultExportDataPage.tsx`
before building against it (per this project's own "compose around the
REAL current file" precedent) — `selectedFilePaths` already holds ONLY
real file paths; a folder checkbox already expands to its descendant file
paths at SELECT time (`toggleFolderSelected`), never storing the folder's
own path (confirmed directly against `T02`'s own `MEMORY.md` Pattern entry
this task's Objective itself names). By the time Export is reached, the
selection is already the flat, expanded file list this task's End-State
describes producing "on confirm" — so `handleConfirmExport` passes
`Array.from(selectedFilePaths)` straight through with zero additional
expansion logic, and `AC`-relevant behavior ("a folder selection is
correctly expanded client-side into real file paths before the request is
sent") is satisfied by the already-`Done` upstream task's own design, not
by new code added here.

**Live verification (real running app, `localhost:5173`, real running
backend `localhost:8001` serving `T02`'s real `/export` route against the
real, currently-configured vault) — headless Edge via a minimal native
`fetch`+`WebSocket` CDP driver (`msedge.exe --headless=new
--remote-debugging-port`), killed by its own specific PID tree afterward
each session, no `/IM` mass-kill:**

- Confirmed the backend was serving `T02`'s real, fresh `/export` route
  (not stale `--reload` output) via a direct `curl.exe` call before any
  browser-level check: `POST /vault/export-data/export` with a real
  selection returned `200`, correct `Content-Disposition`, and the
  returned bytes opened as a real zip (`zipfile.ZipFile`) containing
  exactly the one selected file — confirmed BEFORE trusting the route for
  UI-level verification.
- `[REQ-SB-86-US-02-AC-01]` (UI-observable echo) Navigated to
  `/settings/vault/export-data`; expanded a real top-level folder,
  selected its own checkbox (5 real nested files selected, confirmed via
  the real selection-summary DOM text); clicked `export-selection`;
  confirmed `export-options` rendered with `extraction-hierarchy` checked
  by default; clicked `export-confirm`. A `window.fetch` spy (calling
  through to the REAL `fetch`, not a mock) recorded the outgoing request
  body: `{"selection":[".obsidian/app.json",".obsidian/appearance.json",
  ".obsidian/core-plugins.json",".obsidian/graph.json",
  ".obsidian/workspace.json"],"extraction":"hierarchy"}` — the real,
  correctly client-side-expanded flat file list (5 real files nested under
  the selected folder), `extraction:"hierarchy"` exactly as chosen. The
  same spy independently captured the real response bytes: `byteLength:
  3122`, zip-signature `504b0304` (`"PK\x03\x04"`) — a genuine, complete
  zip, byte-length matching the browser's own real download-interception
  report (below) exactly. **PASS** (request shape + response-byte
  integrity both confirmed real).
- `[REQ-SB-86-US-02-AC-02]` (UI-observable echo) Reopened `export-options`
  on the same 5-file selection, selected `extraction-flat` (confirmed
  `.checked === true` via a real DOM read), clicked `export-confirm`.
  Outgoing body: `{"selection":[...same 5 real files...],
  "extraction":"flat"}`. Response bytes: `byteLength: 3022`, zip-signature
  `504b0304` — real, complete, correctly (slightly smaller, since flat
  strips folder-path prefixes from archive member names) sized zip.
  **PASS.**
- **Real browser download mechanism, genuinely engaged (both rounds
  above):** `Browser.downloadWillBegin` fired for each confirm with the
  exact real filename pattern this task's own `triggerSbdDownload()`
  generates (`second-brain-vault-export-<ISO-8601-with-dashes>.sbd`);
  `Browser.downloadProgress` reported `receivedBytes` reaching
  `totalBytes` exactly (3122/3122, then 3022/3022) — the browser received
  the FULL real blob content before any further state change. **Disclosed
  finding, not a defect in this task's own code:** in this specific
  headless-Edge + CDP `Browser.setDownloadBehavior` combination, the
  download event then transitions from fully-received `inProgress`
  straight to `canceled` (no partial byte loss reported — `receivedBytes`
  resets to 0 only in the terminal "canceled" event itself, after having
  already shown the full count), and no file lands in the configured
  `downloadPath`. **Isolated as a genuine environment/tooling quirk, not a
  regression from this task's own new code:** a control check against
  `REQ-SB-85-US-02-T05`'s own already-`Done`, byte-identical
  `<a download>` + `URL.createObjectURL` + synchronous `URL.revokeObjectURL`
  technique (`SettingsArtifactsPage.tsx`'s Export flow, unmodified, in the
  SAME headless-Edge session) reproduced the IDENTICAL
  fully-received-then-canceled pattern (`second-brain-export-*.sbf`,
  6213/6213 bytes received, then canceled). A speculative fix (delaying
  `URL.revokeObjectURL` by 1s) was tried and did NOT change the outcome,
  then reverted (kept the code identical to the established, already-
  approved `triggerBlobDownload()` precedent — no unrequested deviation
  for an unconfirmed fix). Given (a) the exact correct real request fires
  per extraction mode, (b) the exact correct, complete, valid-zip response
  bytes are received client-side, and (c) the browser's real download
  mechanism is genuinely invoked with the correct filename and receives
  100% of the real bytes — and this exact terminal-state quirk is
  independently reproduced on an already-shipped, independently-verified
  sibling flow using identical code — this AC's own controlling intent ("a
  successful export triggers a real browser download of the returned
  `.sbd`") is treated as **verified**, with the specific final
  disk-write-completion step named as environment-blocked rather than
  silently claimed. Logged for human spot-check, not a locked-AC weakening.
- **Honest inline error (Constraint, not itself its own separate AC-ID —
  covered as part of the story's own controlling posture):** forced a REAL
  `422` from the real backend (a genuinely invalid `extraction` value,
  intercepted client-side via a `window.fetch` wrapper that still calls
  through to the real backend) — `data-role="export-error"` rendered the
  real, honest backend detail text (`"Input should be 'flat' or
  'hierarchy'"` JSON), the `export-options` panel stayed open (no silent
  reset, no fabricated success). **PASS.** Separately attempted to force a
  real backend `500` (a genuinely non-existent selected path) and found —
  **a disclosed, out-of-scope finding, not caused by this task's own
  code:** the raw browser `fetch` call itself throws `TypeError: Failed to
  fetch` rather than exposing a readable `500` status, because
  Starlette/FastAPI's default behavior does not attach `CORSMiddleware`
  response headers to a response built from an unhandled exception —
  confirmed directly (a controlled `curl.exe` call to the same broken
  selection DOES return a real `500 Internal Server Error` body; the SAME
  request from the browser is opaque-CORS-blocked). This task's own
  `extractErrorDetail()`/`catch` still renders an honest, non-fabricated
  error in this case too (`"Request failed."`, the function's own
  `!(error instanceof ApiError)` fallback branch) — so the Constraint's
  controlling intent ("never a silent failure, never a fabricated
  success") holds regardless — but the specific wording differs from a
  normal `ApiError`-detail render, and the ROOT CAUSE (a backend-side CORS
  gap on the unhandled-exception path, `app/api/vault_router.py`/backend
  CORS config) is entirely outside this task's own `## Files to Modify`.
  Logged for human spot-check as a real, separately-actionable backend
  finding — not fixed here (out of scope), not silently absorbed into this
  task's own gate.

gate: flagged 2026-09-01 — no MUST-FLAG trigger fired directly at this
task's OWN code (no new dependency, no shared-interface change, no ADR
deviation — this task builds exactly what its own Objective/End-State
describe; every locked AC verified live with a real positive result,
including real request/response-byte integrity and a real, engaged browser
download mechanism). Set to `flagged`, not `clear`, per this pipeline
run's own explicit coder instruction that scope-internal judgement calls
and disclosed non-blocking findings make a task `gate: flagged` for human
spot-check — two items logged above: (1) the CDP-headless/`blob:`-URL
download-interception terminal-state quirk (environment/tooling, also
reproduced live against an already-`Done` sibling flow using identical
code — no code change indicated), and (2) the backend's own CORS-header
gap on an unhandled-exception response path (out of this task's `## Files
to Modify`, a real, separately-actionable finding for
`app/api/vault_router.py`/backend CORS config). A `REVIEW-QUEUE.md` entry
was added accordingly.
