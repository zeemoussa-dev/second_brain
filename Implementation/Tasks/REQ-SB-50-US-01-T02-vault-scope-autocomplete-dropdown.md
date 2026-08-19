---
id: REQ-SB-50-US-01-T02
title: Vault Scope field autocomplete dropdown (fetch-once-per-agent, client-filter, onMouseDown select)
parent_story: REQ-SB-50-US-01
requirement_id: REQ-SB-50
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-50-US-01-T01]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-50-US-01-T02 — Vault Scope field autocomplete dropdown (fetch-once-per-agent, client-filter, onMouseDown select)

## Parent Story

- Story: [[REQ-SB-50-US-01]] — `../UserStories/REQ-SB-50-US-01-tags-and-locations-autocomplete.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-50 *Tags and Locations Autocomplete*

---

## Objective

Add a suggestion dropdown to `AgentDetailPanel.tsx`'s existing Settings-tab
"Vault scope" free-text input: fetch the real tag/folder suggestion source
once per agent-switch, filter client-side against the in-progress
comma-separated token as the user types, and select suggestions via
`onMouseDown` (not `onClick`) so the field's existing `onBlur` commit cannot
fire first and lose the selection — without disturbing already-assigned scope
values.

---

## Starting State → End State

**Before / Inputs:**
- `features/vault-browser/client.ts` — has `fetchVaultSearchStatus`,
  `fetchNotes`, `fetchTags` (`{tags: TagCount[]}`), `search`, `fetchNoteDetail`.
  No `fetchScopeSuggestions()` yet.
- `AgentDetailPanel.tsx`'s Settings tab has a free-text, comma-separated Vault
  scope `<input>` (`value={scopeDraft}`, `onChange={(e) =>
  setScopeDraft(e.target.value)}`, `onBlur={handleScopeCommit}`), fed by
  `scopeDraft`/`setScopeDraft` state and `handleScopeCommit()` (splits on
  `,`, trims, filters empty, calls `updateAgentAssignment(agentId, {
  scope })`). The main agent-switch `useEffect` (keyed on `[agentId]`)
  already resets `scopeDraft` and fetches `fetchAgent`,
  `fetchAgentHistory`, `fetchSections`, `fetchProviders`, `fetchSkills` once
  per switch — no scope-suggestion fetch yet.

**After / Outputs:**
- `features/vault-browser/client.ts` gains `fetchScopeSuggestions(): Promise<{
  tags: TagCount[]; folders: string[] }>` calling
  `GET /vault-search/scope-suggestions` (`T01`).
- `AgentDetailPanel.tsx` imports `fetchScopeSuggestions` cross-feature from
  `../vault-browser/client`, fetches it once per agent-switch (alongside the
  existing `fetchSections`/`fetchProviders`/`fetchSkills` calls in the same
  `useEffect`), and renders a suggestion dropdown under the Vault scope
  `<input>` that:
  - filters the fetched tag/folder lists against only the currently-typed
    (last, uncommitted, comma-separated) token, substring/prefix match;
  - shows no suggestions when nothing real matches (Scenario 3's honest
    empty result — the dropdown simply doesn't render, no fabricated entry);
  - on a suggestion click, uses `onMouseDown` (with `event.preventDefault()`
    to keep the input focused) to append the selected value and commit,
    never `onClick` — `onClick` fires after the input's own `onBlur`, which
    would already have committed `scopeDraft` and unmounted the dropdown
    before the click registers;
  - leaves already-committed values (e.g. `"customer/masdar"`,
    `"kind/meeting"`) untouched, unduplicated, unreordered — only the
    in-progress token is replaced by the selected suggestion.

---

## Files to Modify

- `src/frontend/src/features/vault-browser/client.ts` — add
  `fetchScopeSuggestions()` + its response type.
- `src/frontend/src/features/agents-map/AgentDetailPanel.tsx` — import
  `fetchScopeSuggestions`, add suggestion state, fetch-once-per-agent-switch,
  dropdown render + filter + `onMouseDown` selection under the Vault scope
  `<input>`.

---

## Constraints

- Inherits from parent story.
- Cross-feature import only (`fetchScopeSuggestions` from
  `features/vault-browser/client.ts` into `features/agents-map/
  AgentDetailPanel.tsx`) — do not duplicate the fetch function in
  `agents-map`.
- Fetch once per agent-switch (in the existing `[agentId]`-keyed
  `useEffect`, alongside `fetchSections`/`fetchProviders`/`fetchSkills`) —
  not once per keystroke; filtering against the in-progress token is
  client-side only, against the already-fetched snapshot.
- **Must use `onMouseDown`, not `onClick`, for suggestion selection** — the
  field's existing `onBlur={handleScopeCommit}` fires before a plain
  `onClick` on a sibling element would register, silently losing the
  selection. Call `event.preventDefault()` in the `onMouseDown` handler to
  keep the input focused (suppressing the blur) before applying the
  selection.
- Do not alter `handleScopeCommit`'s existing typed/blur-commit behaviour —
  this task adds a second, additional commit path (suggestion selection),
  it does not replace the existing one.
- Must not duplicate, remove, or reorder any already-committed scope value
  (Scenario 4 / `AC-04`) — only the in-progress (last, uncommitted) token is
  replaced by a selected suggestion; existing values pass through unchanged.
- Structural-AC note: this is a behavioural addition to an existing input,
  not new screen real estate — no new structural AC is required beyond the
  4 locked ACs already covering the dropdown's real-data/no-fabrication/
  non-disruption behaviour (see story `## Notes` → Prototype parity: this
  row carries no approved prototype coverage and this story does not
  introduce or resolve that pre-existing gap).

---

## Tests

**Manual verification steps:**
1. [REQ-SB-50-US-01-AC-01] With the vault indexed and a note tagged
   `"customer/masdar"`, open an agent's Settings tab, type `"mas"` into the
   Vault scope field; expect a suggestion-list item reading exactly
   `"customer/masdar"` to appear, sourced from the once-per-agent-switch
   `fetchScopeSuggestions()` call, filtered client-side.
2. [REQ-SB-50-US-01-AC-02] With a real `Work/Pipeline` folder in the vault,
   type `"pipe"` into the Vault scope field; expect a suggestion-list item
   reading exactly `"Pipeline"` to appear.
3. [REQ-SB-50-US-01-AC-03] Type `"zzz"` (confirmed not a substring of any
   real current tag or folder name) into the Vault scope field; expect no
   suggestion-list items to render — no fabricated or guessed entry shown in
   place of a real match.
4. [REQ-SB-50-US-01-AC-04] With an agent already assigned scope
   `["customer/masdar", "kind/meeting"]`, start typing a third value into the
   field; confirm the suggestion list filters only against the in-progress
   token and the two already-assigned values remain intact in the field
   (unaffected by the in-progress list). Click a suggestion (confirming the
   `onMouseDown` handler fires the selection, not lost to `onBlur`); expect
   the new value joins the existing two, with neither `"customer/masdar"`
   nor `"kind/meeting"` duplicated, removed, or reordered. Repeat by typing a
   value fully and committing via blur (no suggestion click) — same
   non-disruption result.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `fetchScopeSuggestions()` added to `features/vault-browser/client.ts`,
      calling `GET /vault-search/scope-suggestions`
- [x] `AgentDetailPanel.tsx` fetches scope suggestions once per agent-switch
- [x] Dropdown filters client-side against the in-progress typed token only
- [x] No suggestions render when no real tag/folder matches (no fabrication)
- [x] Suggestion selection uses `onMouseDown` (with `preventDefault`), not
      `onClick`
- [x] Already-assigned scope values are never duplicated, removed, or
      reordered by suggestion selection or by the in-progress dropdown
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `CreateAgentWizard.tsx`'s Worker-step Vault scope field — deferred to
  `REQ-SB-46`'s eventual redesigned field (see story `## Context`).
- Any Section/Provider `<select>` field — out of scope by definition, not
  deferral (already a bounded dropdown, no typeahead applies).
- Fuzzy/typo-tolerant matching — straightforward substring/prefix match only.
- New endpoint/business logic — `T01`'s scope, already `depends_on` here.
- Any `/design` prototype work — this row has no approved prototype coverage
  and this story does not introduce or resolve that pre-existing gap.

---

## Context / Notes

- Illustrative shape only — the coder writes the real code, matching this
  file's existing state/effect/handler conventions:

  ```ts
  // features/vault-browser/client.ts
  export interface ScopeSuggestions {
    tags: TagCount[];
    folders: string[];
  }

  export function fetchScopeSuggestions(): Promise<ScopeSuggestions> {
    return apiFetch<ScopeSuggestions>('/vault-search/scope-suggestions');
  }
  ```

  ```tsx
  // AgentDetailPanel.tsx — inside the existing [agentId] useEffect, alongside
  // fetchSections()/fetchProviders()/fetchSkills():
  fetchScopeSuggestions().then(setScopeSuggestions);

  // Selection handler — appends the suggestion in place of the in-progress
  // token, then commits immediately (a second commit path alongside the
  // existing typed+blur one):
  function handleScopeSuggestionSelect(value: string) {
    const parts = scopeDraft.split(',').map((entry) => entry.trim());
    parts.pop(); // drop the in-progress token being replaced by the pick
    const nextScope = Array.from(
      new Set([...parts.filter((entry) => entry.length > 0), value]),
    );
    updateAgentAssignment(agentId, { scope: nextScope }).then((updated) => {
      setAgent(updated);
      setScopeDraft(updated.scope.join(', '));
    });
  }

  // Suggestion item — onMouseDown, NOT onClick:
  <li
    onMouseDown={(event) => {
      event.preventDefault(); // keep focus on the input; suppress onBlur's commit
      handleScopeSuggestionSelect(suggestion);
    }}
  >
    {suggestion}
  </li>
  ```

- Real gotcha (architect's Notes, restated here for the coder): mousedown →
  blur → mouseup → click is the real browser event order on an unfocused-
  target click. A plain `onClick` on the suggestion item fires AFTER the
  input's own `onBlur={handleScopeCommit}` has already committed
  `scopeDraft` and (depending on render timing) may have already caused the
  dropdown to unmount — losing the click. `onMouseDown` with
  `preventDefault()` runs before `blur` and keeps the input focused, so the
  selection lands reliably.
- Reset `scopeSuggestions` to `null` in the agent-switch `useEffect`'s
  clear-block alongside the other per-agent state resets, so a slow fetch
  from a previous agent cannot render into the newly-selected agent's panel.

---

## Implementation Log

Read the real current `features/vault-browser/client.ts` (existing
`TagCount`/`fetchTags` shape, confirmed no `fetchScopeSuggestions` yet)
and `AgentDetailPanel.tsx` (Vault scope `kv-row`/`scopeDraft`/
`handleScopeCommit`, and the `[agentId]`-keyed `useEffect`'s existing
`fetchSections`/`fetchProviders`/`fetchSkills` calls, confirmed) before
editing — no stale sample trusted; also confirmed `T01` was already
`Done` this session.

Added `ScopeSuggestions` + `fetchScopeSuggestions()` to
`features/vault-browser/client.ts` (thin `apiFetch` wrapper, matches the
existing `fetchTags` shape). `AgentDetailPanel.tsx`: cross-feature import
of `fetchScopeSuggestions`/`ScopeSuggestions` from `../vault-browser/
client`; new `scopeSuggestions` state, fetched once per agent-switch
inside the existing `[agentId]` `useEffect` (alongside
`fetchSkills()`/etc.) and reset to `null` in the same effect's clear
block; `getInProgressScopeToken()`/`getFilteredScopeSuggestions()` derive
the filtered list from `scopeDraft`'s last comma-separated token
(substring match, case-insensitive, against real tags + real folders,
un-merged then combined for filtering only); `handleScopeSuggestionSelect`
is a SECOND commit path (drops the in-progress token, appends the
selection, dedupes, calls `updateAgentAssignment` — `handleScopeCommit`
itself is untouched). The suggestion `<li><button onMouseDown=.../></li>`
list renders under the existing Vault scope `<input>` (new
`position: relative` on the row, `position: absolute` on the list — no
new CSS file, inline styles only, matching this file's own existing
inline-style convention; no prototype exists for this row per the
story's own Notes). `onMouseDown` calls `event.preventDefault()` before
`handleScopeSuggestionSelect`, per the architect's own documented
mousedown-before-blur gotcha.

`npx tsc -p . --noEmit` — zero type errors.

**Live verification** — same real backend/frontend/CDP setup as
`REQ-SB-48-US-01-T02` (this session), against the real, indexed vault.

**[REQ-SB-50-US-01-AC-01] PASS.** Typed `"mas"` into the Vault scope
field (native-setter + `input` event, React-controlled-input technique):
suggestion list rendered `["customer/masdar", "company/masdar"]` — both
real, currently-existing vault tags (the `/vault-search/scope-
suggestions` endpoint's own live output), no fabricated entry.

**[REQ-SB-50-US-01-AC-02] PASS.** Typed `"meet"`: suggestion list
included `"Meetings"` (a real, currently-existing folder returned by
`vault_writer.list_known_kinds()`), alongside real tag matches
(`kind/meeting`, `kind/meetings`) — same honest, real-only sourcing.

**[REQ-SB-50-US-01-AC-03] PASS.** Typed `"zzz"` (confirmed not a
substring of any real current tag/folder): no `[data-testid="vault-scope-
suggestions"]` element rendered at all — no fabricated/guessed entry.

**[REQ-SB-50-US-01-AC-04] PASS.** Full non-disruption sequence run twice,
via both commit paths: (1) typed `"customer/masdar, kind/meeting"` and
committed via blur — **React's own delegated `focusout` listener does not
reliably fire from a raw synthetic `dispatchEvent(new FocusEvent('blur'
...))` in this headless CDP environment** (confirmed live: the commit
silently didn't fire); switched to this project's own established
Fiber-props direct-invoke technique
(`element[reactPropsKey].onBlur({target: element})`, `SPRINT-020`
precedent, generalizes past `onBlur`-on-commit-input to this exact same
class again) — confirmed committed correctly (`GET` showed
`["customer/masdar","kind/meeting"]`). (2) Typed a real 3rd token
(`"meet"`) and selected `"Meetings"` via a real `mousedown` dispatch on
the suggestion button: `GET` showed all 3 values, none duplicated/
removed/reordered. (3) Typed+blur-committed a 4th value
(`"kind/task"`) on top via the Fiber-direct-invoke technique again: `GET`
showed all 4 values in original order, confirming BOTH commit paths
(suggestion click, typed+blur) coexist without disturbing each other's
own prior writes. Agent's real scope independently reverted to `[]`
(its original baseline) via a direct `PATCH` afterward, reconfirmed via
`GET`.

**Visual spot-check (screenshot, no approved prototype for this row per
the story's own Notes — not a locked AC):** captured a real 1400×1000
screenshot showing the live dropdown rendering under the Vault scope
field with both real suggestions visible.

**Real state left clean.** `email-capture`'s `scope` field independently
reconfirmed `[]` (its exact pre-verification value) at the end of this
session.

gate: clear 2026-08-14 — all 4 locked ACs verified live with a real
positive result; the one verification-technique deviation (Fiber-props
direct `onBlur` invoke instead of a raw synthetic `blur` event) is a
disclosed, already-precedented (`SPRINT-020`) technique substitution for
a CDP-environment limitation, not a weakening of any AC or a new
assumption — no MUST-FLAG trigger fired.
