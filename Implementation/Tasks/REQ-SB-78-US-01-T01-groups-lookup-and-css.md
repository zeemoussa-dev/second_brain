---
id: REQ-SB-78-US-01-T01
title: pendingApprovalGroups.ts lookup table + group-color CSS classes
parent_story: REQ-SB-78-US-01
requirement_id: REQ-SB-78
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: []
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-78-US-01-T01 — `pendingApprovalGroups.ts` + CSS

## Parent Story

- Story: [[REQ-SB-78-US-01]] — `../UserStories/REQ-SB-78-US-01-pending-approvals-grouped-color-coded-review.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-78 *Pending Approvals — Grouped, Color-Coded Review*
- Architecture: `Implementation/Architecture/architecture.md` → "Pending Approvals — Grouped, Color-Coded Review" §§ "Grouping key", "Label + color"

---

## Objective

Add the new, purely-presentational `pendingApprovalGroups.ts` module (label/color lookup by `action_id`, `Other` catch-all, branching-decision set) and the small set of new `.group-color-N` CSS classes it references — zero backend change.

---

## Starting State → End State

**Before / Inputs:**
- `MyDayApprovalsPage.tsx` has a local `const COMPANY_REVIEW_ACTION_ID = 'propose_company_review'`, no grouping concept.
- `src/frontend/src/styles/tokens.css` has a numbered-variant CSS-custom-property precedent (`--graph-kind-color-1` … `-8`).
- `src/frontend/src/styles/my-day.css` has `.item-list`/`.item-row`.

**After / Outputs:**
- New file `src/frontend/src/features/agents-map/pendingApprovalGroups.ts`:

  ```ts
  export const KNOWN_GROUPS: Record<string, { label: string; colorClass: string }> = {
    propose_company_review:              { label: 'Company Review',         colorClass: 'group-color-1' },
    propose_customer_backfill_routing:   { label: 'Customer Backfill',      colorClass: 'group-color-2' },
    propose_customer_archival_candidate: { label: 'Customer Archival',      colorClass: 'group-color-3' },
    propose_librarian_company_link:      { label: 'Company Link',           colorClass: 'group-color-4' },
    route_thread_to_project:             { label: 'Thread Routing',         colorClass: 'group-color-5' },
    propose_recurring_pipeline:          { label: 'Recurring Pipeline',     colorClass: 'group-color-6' },
    propose_cross_cutting_update:        { label: 'Cross-Cutting Update',   colorClass: 'group-color-7' },
    propose_background_amendment:        { label: 'Background Amendment',   colorClass: 'group-color-8' },
    propose_new_top_level_area:          { label: 'New Top-Level Area',     colorClass: 'group-color-9' },
    hermes_vault_write:                  { label: 'Hermes Write',           colorClass: 'group-color-10' },
    acknowledge_classification_failure:  { label: 'Classification Failure', colorClass: 'group-color-11' },
  };

  export const OTHER_GROUP = { label: 'Other', colorClass: 'group-color-other' };

  export const BRANCHING_DECISION_ACTION_IDS = new Set(['propose_company_review']);

  export function resolveGroup(actionId: string | null): { key: string; label: string; colorClass: string } {
    if (actionId && actionId in KNOWN_GROUPS) {
      return { key: actionId, ...KNOWN_GROUPS[actionId] };
    }
    return { key: 'other', ...OTHER_GROUP };
  }
  ```

  (`resolveGroup`'s exact shape is a scope-internal implementation choice — `T02` may call `KNOWN_GROUPS`/`OTHER_GROUP` directly instead if that reads cleaner; either satisfies this task's own Constraints, as long as the `key`/`label`/`colorClass` triple is derivable per item.)
- `src/frontend/src/styles/tokens.css` — new custom properties, mirroring the existing `--graph-kind-color-N` numbered-variant pattern: `--group-color-1` … `--group-color-11`, `--group-color-other`.
- `src/frontend/src/styles/my-day.css` — new `.pending-approval-group` block establishing a section wrapper, plus `.group-color-1` … `-11`/`.group-color-other` classes each setting a `--group-accent: var(--group-color-N)` custom property the wrapper's own border/heading-accent styles read (mirrors the existing `--node-color`/`--hub-color` per-item CSS-custom-property pattern the Agents Map canvas already uses).

---

## Files to Modify

- `src/frontend/src/features/agents-map/pendingApprovalGroups.ts` — new file.
- `src/frontend/src/styles/tokens.css` — new `--group-color-N` custom properties.
- `src/frontend/src/styles/my-day.css` — new `.pending-approval-group`/`.group-color-N` classes.

---

## Constraints

- Inherits from parent story.
- **No new backend field, no new endpoint** — this task is purely frontend/presentational.
- **Every `action_id` not in `KNOWN_GROUPS` (including `null`) resolves to the ONE `Other` catch-all** — never a second, undocumented fallback path.
- Reuses the existing `--color-accent`-family CSS-custom-property pattern — never a new, unrelated color system.
- `BRANCHING_DECISION_ACTION_IDS` starts as a superset-safe generalization of the existing `COMPANY_REVIEW_ACTION_ID` constant already in `MyDayApprovalsPage.tsx` — `T02`/`T03` reconcile the two (either import this module's own constant in place of the local one, or keep both in sync; `T02` decides).

---

## Tests

**Manual verification steps:**
1. Import `KNOWN_GROUPS`/`OTHER_GROUP`/`BRANCHING_DECISION_ACTION_IDS`/`resolveGroup` from a scratch script or the browser console once the dev server is running; confirm `resolveGroup('propose_company_review')` returns `{key: 'propose_company_review', label: 'Company Review', colorClass: 'group-color-1'}`.
2. Confirm `resolveGroup('some_future_unmapped_action_id')` and `resolveGroup(null)` both return `{key: 'other', ...OTHER_GROUP}`.
3. Confirm `BRANCHING_DECISION_ACTION_IDS.has('propose_company_review')` is `true` and `.has('route_thread_to_project')` is `false`.
4. Confirm the new CSS classes exist in the built stylesheet (inspect via dev server) and each numbered class sets a distinct `--group-accent` value.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `pendingApprovalGroups.ts` exports `KNOWN_GROUPS`/`OTHER_GROUP`/`BRANCHING_DECISION_ACTION_IDS`, every known `action_id` from the architecture's own lookup table present
- [x] Unmapped/null `action_id` resolves to the one `Other` catch-all
- [x] New `.group-color-N`/`.group-color-other` CSS classes exist and are visually distinct by custom-property value
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (n/a — no new decision/pattern/constraint; pure composition of already-established tokens/CSS-custom-property conventions per architecture.md)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Wiring this module into `MyDayApprovalsPage.tsx`'s own rendering — `T02`/`T03`.
- Any backend change.

---

## Context / Notes

None beyond the architecture reference above.

---

## Implementation Log

**2026-08-19, coder.** Built exactly per the task's own illustrative sample and
architecture.md's own "Label + color" section, with zero deviation to the data
shape:

- New `src/frontend/src/features/agents-map/pendingApprovalGroups.ts` —
  `KNOWN_GROUPS` (11 entries), `OTHER_GROUP`, `BRANCHING_DECISION_ACTION_IDS`
  (`Set(['propose_company_review'])`), `resolveGroup(actionId)`.
- `src/frontend/src/styles/tokens.css` — new `--group-color-1` … `-11` plus
  `--group-color-other` custom properties inside `:root`, reusing already-
  curated tokens where available (`--color-accent`/`--color-success`/
  `--color-warning`/`--color-danger`/`--agent-color-producer`, matching the
  existing `--graph-kind-color-N` reuse-first precedent) and 3 new hex values
  (`#db2777`/`#ca8a04`/`#64748b`) for the remaining named groups; `--group-
  color-other` reuses `--color-text-muted` (deliberately neutral, never
  competing visually with a real named group).
- `src/frontend/src/styles/my-day.css` — new `.pending-approval-group`/
  `.pending-approval-group-heading`/`.pending-approval-group-label` wrapper
  block plus `.group-color-1` … `-11`/`.group-color-other`, each setting
  `--group-accent` from its own token (mirrors the existing `--node-color`/
  `--hub-color` per-item CSS-custom-property pattern in `agents-map.css`).

**Verification (manual mode, this project's test tooling is still pending):**

- **Steps 1-3 (module logic).** No `tsx`/`ts-node` available in
  `node_modules/.bin`; used the running Vite dev server's own real
  on-the-fly TS→JS transform instead — fetched
  `http://127.0.0.1:5174/src/features/agents-map/pendingApprovalGroups.ts`
  (Vite dev server started for this worktree on port 5174, since 5173 was
  already bound by a concurrent session; 5174 is already in the backend's
  CORS allow-list, `main.py`), re-imported the transformed source as a
  `data:` URL from a throwaway Node script
  (`.scratch/t01-verify.mjs`, deleted after use), and ran real assertions
  against the REAL exported module (not a re-typed copy):
  - `resolveGroup('propose_company_review')` → `{key:
    'propose_company_review', label: 'Company Review', colorClass:
    'group-color-1'}` — matches exactly. **Confirmed.**
  - `resolveGroup('some_future_unmapped_action_id')` and
    `resolveGroup(null)` both → `{key: 'other', label: 'Other', colorClass:
    'group-color-other'}`. **Confirmed.**
  - `BRANCHING_DECISION_ACTION_IDS.has('propose_company_review')` → `true`;
    `.has('route_thread_to_project')` → `false`. **Confirmed.**
- **Step 4 (CSS).** Fetched the dev server's own served
  `/src/styles/my-day.css` — confirmed all 12 `.group-color-N`/
  `.group-color-other` classes present, each setting a distinct
  `--group-accent` value from `tokens.css`'s own distinct
  `--group-color-N` custom properties (read directly, not assumed).
  **Confirmed.**

**Environment note (not a product decision, not filed to `MEMORY.md`):** this
worktree had no `node_modules` and was several commits behind the shared
checkout's own uncommitted in-flight state (missing `SPRINT-072`'s already-
shipped Company Review control in `MyDayApprovalsPage.tsx`, and the sprint/
story/task files themselves). Synced the exact current content of every
file this story reads or writes from the shared checkout into this worktree
before starting (task/story/sprint files, `MEMORY.md`/`CHANGELOG.md`/
`BACKLOG.md`/`REVIEW-QUEUE.md`/`ESCALATIONS.md`, and the 4 real frontend
files this story's tasks touch), and junctioned `node_modules` from the
shared checkout rather than a full reinstall (same lockfile/commit, zero
version drift risk). Started this worktree's own Vite dev server on port
5174 against the shared, already-running real backend on port 8000 (real
vault data, confirmed live — the `~39` real `propose_company_review`
records the operator described are present).

**Gate: clear 2026-08-19** — no MUST-FLAG trigger fired: no new
assumption beyond the environment-sync note above (a scope-internal,
mechanical, zero-judgement sync, not a product decision); `REQ-SB-78` is
not `Draft`; no ADR created/changed; no `ESCALATIONS.md` entry; not
oversized; every locked AC this task owns (none — `T01` carries no
AC-tagged Gherkin scenario of its own, only the module/CSS Tests above)
independently confirmed; no contradictory inputs; nothing genuinely
ambiguous.
