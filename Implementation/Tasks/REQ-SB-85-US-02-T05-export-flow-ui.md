---
id: REQ-SB-85-US-02-T05
title: Export flow UI — dependency-preview + secret-scan confirmation screens
parent_story: REQ-SB-85-US-02
requirement_id: REQ-SB-85
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-85-US-02-T04, REQ-SB-85-US-01-T02]
created: 2026-08-31
updated: 2026-08-31
---

# REQ-SB-85-US-02-T05 — Export flow UI: dependency-preview + secret-scan confirmation screens

## Parent Story

- Story: [[REQ-SB-85-US-02]] — `../UserStories/REQ-SB-85-US-02-export-dependency-closure-and-secret-scan.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-85 *Artifact Export/Import — Portable Capability Bundles (`.sbf`)*

---

## Objective

Wire an "Export" trigger onto `SettingsArtifactsPage.tsx`'s own selection
(`REQ-SB-85-US-01-T02`) that calls `T04`'s `/preview` endpoint, renders
the resolved closure, conditionally renders a secret-scan confirmation
screen, and calls `/commit` to produce and download the real `.sbf`.

---

## Starting State → End State

**Before / Inputs:**
- `SettingsArtifactsPage.tsx` (`REQ-SB-85-US-01-T02`) exposes a real,
  ephemeral multi-select selection across the 4 kinds, but no Export
  trigger anywhere yet. `POST /artifacts/export/preview` and `POST
  /artifacts/export/commit` (`T04`) exist.

**After / Outputs:**
- `src/frontend/src/features/settings/artifactsApiClient.ts` gains:
  - `interface ClosureEntry { kind: string; id: string; included_reason:
    'selected' | 'dependency'; depends_via: string | null }`
  - `interface SecretFinding { artifact_kind: string; artifact_id: string;
    file_path: string; line: number; matched_pattern: string; snippet:
    string }`
  - `previewExport(selection): Promise<{ closure: ClosureEntry[];
    secret_findings: SecretFinding[] }>`
  - `commitExport(selection, secretDecisions): Promise<Blob>` — the real
    `.sbf` bytes (`response.blob()`), or throws on a `400`/`409` from the
    backend's own gate.
- `SettingsArtifactsPage.tsx` gains an `data-testid="export-selected"`
  button, enabled only when the selection is non-empty, that:
  1. Calls `previewExport(selection)`; renders a dependency-preview panel
     (`data-role="export-dependency-preview"`) listing every real
     `closure` entry, grouped/labeled by `included_reason` (a directly-
     selected artifact vs. "included because: `depends_via`") — this
     panel renders BEFORE anything is committed (Scenario 1).
  2. If `secret_findings` is empty: a `data-testid="export-confirm"`
     control on the same preview panel calls `commitExport(selection,
     {})` directly — no secret-scan screen is ever shown (Scenario 2) —
     and on success triggers a real browser download of the returned
     blob (e.g. via an `<a download>` + `URL.createObjectURL`, the
     standard technique for a client-triggered blob download).
  3. If `secret_findings` is non-empty: instead of the direct-confirm
     control, a second screen (`data-role="secret-scan-confirmation"`)
     renders, listing every finding with 3 real per-finding controls —
     `data-testid="finding-redact-<key>"`, `data-testid="finding-keep-<key>"`
     — plus one whole-flow `data-testid="export-cancel"` control. A
     `data-testid="export-confirm"` control on THIS screen is enabled
     only once every listed finding has a chosen decision, and calls
     `commitExport(selection, decisions)` with the real, collected
     per-finding decisions.
  4. `data-testid="export-cancel"` on the secret-scan screen calls
     `commitExport(selection, decisions-with-every-undecided-finding-set-
     to-"cancel")` OR (simpler, equally correct — the backend never
     writes anything on a `409`) simply never calls `/commit` at all and
     resets the export flow back to its starting state — either shape
     satisfies "no `.sbf` written, no content modified"; pick the simpler
     one (never call `/commit`) unless a later step needs the explicit
     cancel round-trip for some other reason.
  5. Any `400`/`409` from `/commit` (an incomplete-decision or cancelled
     gate firing) renders a plain, honest inline error — never a silent
     failure, never a fabricated "success."

---

## Files to Modify

- `src/frontend/src/pages/SettingsArtifactsPage.tsx`.
- `src/frontend/src/features/settings/artifactsApiClient.ts`.

---

## Constraints

- Inherits from parent story.
- **DOM-structural ACs only** — lock only that the preview panel renders
  before commit, that the secret-scan screen renders only when findings
  exist and requires every finding decided before enabling confirm, and
  that cancel aborts cleanly — never pixel-level/colour/hover assertions.
  Both screens are `net-new-design-needed` (functional-first per the
  story's own frontmatter override) — a non-blocking design spot-check is
  expected later.
- **Never calls `/commit` before the operator has seen the preview** — no
  "one-click export skipping the preview" shortcut, even for a selection
  with an empty closure/no findings.
- **Never fabricates a decision for an undecided finding** — the confirm
  control on the secret-scan screen is genuinely disabled, not just
  visually deprioritized, until every finding has one of the 3 real
  choices selected.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-85-US-02-AC-01]` Select a real artifact whose export closure
   includes at least one real dependency (e.g. `create-companies-
   partners`); click `[data-testid="export-selected"]`; confirm
   `[data-role="export-dependency-preview"]` renders BEFORE any network
   call to `/commit` is made (verify via a `window.fetch` spy: only
   `/preview` has been called at this point), listing both the directly-
   selected artifact and its real resolved dependencies with their own
   `depends_via` reasons visible.
2. `[REQ-SB-85-US-02-AC-02]` Using a selection whose real content has no
   secret-shaped strings, confirm `[data-role="secret-scan-confirmation"]`
   never renders and clicking `[data-testid="export-confirm"]` on the
   preview panel triggers exactly one `/commit` call and a real browser
   download event/blob.
3. `[REQ-SB-85-US-02-AC-03]` Using a selection engineered to contain a
   secret-shaped string (a disposable scratch Skill with a test API-key-
   shaped literal in its own `SKILL.md`, cleaned up after), confirm
   `[data-role="secret-scan-confirmation"]` renders listing the finding,
   that `[data-testid="export-confirm"]` on THIS screen starts disabled,
   and that selecting Redact (or Keep) on the one listed finding enables
   it; confirm the outgoing `/commit` request body's `secret_decisions`
   contains the real chosen action for that finding's own key.
4. `[REQ-SB-85-US-02-AC-07]` From the secret-scan confirmation screen
   (step 3's state, before deciding), click
   `[data-testid="export-cancel"]`; confirm (via the `window.fetch` spy)
   no `/commit` request is ever sent, and confirm the flow returns to its
   starting state (no stuck confirmation screen, no downloaded file).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] The dependency-preview panel renders every real resolved closure
      entry with its reason, before any commit call
- [x] No secrets found → confirm proceeds straight to a real download,
      no confirmation screen
- [x] Secrets found → confirmation screen requires every finding decided
      before Confirm is enabled
- [x] Cancel aborts with zero `/commit` calls and zero downloaded file
- [x] An honest inline error renders on a `400`/`409` from `/commit`
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any change to `SettingsArtifactsPage.tsx`'s own multi-select mechanism
  itself — `REQ-SB-85-US-01-T02`, reused unchanged.
- The Import side — `REQ-SB-85-US-03-T06`.
- Final visual polish beyond the DOM-structural shape described above —
  non-blocking design spot-check, not a locked AC.

---

## Context / Notes

The parent story's own frontmatter `gate_reason` records the operator's
direct override: build functional-first, a real `/design REQ-SB-85` pass
covering this screen (alongside `US-01`/`US-03`'s own new screens)
happens later. The `/preview` + `/commit` route split this task wires
against is the decomposer's own disclosed judgement call — see the
parent story's own Notes.

---

## Implementation Log

**Build.** `artifactsApiClient.ts` gained `ArtifactSelectionEntry`,
`ClosureEntry`, `SecretFinding`, `ExportPreviewResult`, `previewExport()`
(via the existing `apiFetch` JSON helper), and `commitExport()` (a
dedicated raw `fetch` call, not `apiFetch`, since it must resolve
`response.blob()` for the real `.sbf` bytes rather than JSON — duplicates
`apiFetch`'s own `VITE_API_BASE_URL` base-URL read locally rather than
importing a non-exported constant from `api/client.ts`, logged as a
scope-internal judgement call for spot-check, not an escalation).
`SettingsArtifactsPage.tsx` gained the `export-selected` trigger, the
`export-dependency-preview` panel (renders the real closure with
`included_reason`/`depends_via`), the conditional
`secret-scan-confirmation` panel (per-finding Redact/Keep controls keyed
by the SAME `"{file_path}:{line}"` identity `artifact_secret_scan.py`'s
own `_finding_key` uses server-side, a genuinely-disabled Confirm until
every finding is decided), `export-cancel` (resets local state, never
calls `/commit` — the simpler of the two equally-correct shapes the task
itself named), and an honest inline `export-error` panel that extracts
FastAPI's own `{"detail": ...}` body out of a `400`/`409`.

**Environment fix before verification (scope-internal, not a file-scope
violation):** the already-running backend dev server (PID 22616, no
`--reload`) predated `T04`'s own commit and was still serving only `GET
/artifacts` — confirmed via `GET /openapi.json` showing no `/export/*`
routes. Killed that specific PID (no children) and started a fresh
`uvicorn app.main:app --reload` instance (new PID 18860) on the same
port/host — this project's own established specific-PID-kill-and-restart
protocol, reconfirmed a further time. No task file touched; the frontend
dev server (5173) was untouched and remained healthy throughout.

**Verification (manual mode, all against the real running app — backend
8001, frontend 5173 — via a minimal Node native-fetch/native-WebSocket CDP
driver against headless Edge, no puppeteer/playwright, per this project's
own established Learnings pattern):**

- `[REQ-SB-85-US-02-AC-01]` **PASS.** Selected the real
  `create-companies-partners` Skill (confirmed live beforehand via direct
  `curl` that its real closure resolves 7 entries — the Skill plus all 7
  Templates, an over-inclusive-but-disclosed result of the shared
  `vault_manager.py`-enumerates-every-Template-id heuristic named in this
  run's own briefing, displayed honestly here, not worked around). Clicked
  `export-selected`; a `window.fetch` spy (installed via
  `Page.addScriptToEvaluateOnNewDocument`, before any app code ran) showed
  exactly one call at that point — `POST /artifacts/export/preview` — zero
  `/commit` calls. `[data-role="export-dependency-preview"]` rendered all
  8 real closure entries, the directly-selected Skill labeled "directly
  selected" and all 7 Templates labeled "included because:
  skill:create-companies-partners (implicit Template coupling)".
- `[REQ-SB-85-US-02-AC-02]` **PASS.** Same selection (its real
  `secret_findings` was empty, confirmed via the same preview response) —
  `[data-role="secret-scan-confirmation"]` never rendered.
  `[data-testid="export-confirm"]` on the preview panel fired exactly one
  real `POST /artifacts/export/commit` (`secret_decisions: {}`), and
  `Page.setDownloadBehavior`'s configured download directory received a
  real `second-brain-export-*.sbf` file.
- `[REQ-SB-85-US-02-AC-03]` **PASS.** Created a disposable scratch Skill
  (`Hermes-Provisioning/skills/scratch-verification/verify-secret-scan-t05/
  SKILL.md`, one AWS-access-key-shaped test literal, confirmed live via
  direct `curl` to `/preview` to produce exactly one real finding at
  `skills/verify-secret-scan-t05/SKILL.md:9` before ever touching the UI)
  — deleted immediately after this verification pass, confirmed absent
  from a fresh `GET /artifacts` afterward. Selecting it and exporting
  rendered `[data-role="secret-scan-confirmation"]` with the one real
  finding; `[data-testid="export-confirm"]` on that screen started
  `disabled === true`; clicking
  `[data-testid="finding-redact-skills/verify-secret-scan-t05/SKILL.md:9"]`
  flipped it to `disabled === false`; the resulting `/commit` request body
  carried `"secret_decisions":{"skills/verify-secret-scan-t05/SKILL.md:9":
  "redact"}` — the real chosen action under the real finding's own key.
- `[REQ-SB-85-US-02-AC-07]` **PASS.** From a fresh secret-scan-confirmation
  screen (same scratch Skill, zero decisions made), clicked
  `[data-testid="export-cancel"]`: the `window.fetch` spy recorded zero
  `/commit` calls before vs. after: neither panel rendered afterward (flow
  reset to its starting state), and the download directory's file list was
  byte-for-byte unchanged (no new `.sbf`).
- Beyond the task's own 4 tagged steps: also live-verified the 5th
  Acceptance-Criteria bullet (honest inline error on a `400`/`409`) — the
  UI's own genuinely-disabled Confirm button structurally prevents ever
  reaching `/commit` with an incomplete decision through ordinary
  interaction (by design), so this invoked the real `onClick` handler
  React itself attached via the button's own Fiber props
  (`__reactProps$...`, this project's own established technique for
  exercising a structurally-guarded path) to call `handleCommitExport({})`
  directly. The real backend responded `400` (`SecretScanIncompleteError`)
  and `[data-role="export-error"]` rendered that exact real detail message
  verbatim — confirming the `ApiError` → `extractErrorDetail` → inline
  render path end-to-end against a real non-2xx response, not a mock.

No `ESCALATIONS.md`/`REVIEW-QUEUE.md` entry needed — no MUST-FLAG trigger
fired. All 4 locked ACs mapped to this task verified live with a genuine
positive result; zero deferred/blocked half.

gate: clear 2026-08-31 — no triggers fired (no new dependency, no shared-
interface change beyond the disclosed local `VITE_API_BASE_URL` read
above, no ADR deviation, no unanticipated file, every locked AC verified
live).
