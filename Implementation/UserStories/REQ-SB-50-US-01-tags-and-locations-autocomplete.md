---
id: REQ-SB-50-US-01
title: Tags and Locations Autocomplete — real, vault-derived suggestions on the Agent Settings Vault Scope field
requirement_ids: [REQ-SB-50]
requirement_section: "REQ-SB-50: Tags and Locations Autocomplete"
phase: P1
status: Done
gate: clear
gate_reason: ""
sprint: "SPRINT-042"
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-50-US-01 — Tags and Locations Autocomplete — real, vault-derived suggestions on the Agent Settings Vault Scope field

## Story

**As a** Second Brain user assigning a vault tag or folder to an agent's
scope
**I want** the input field to suggest real, existing vault tags and folder
paths as I type
**So that** I can assign a correct, currently-existing scope value without
having to already know the exact tag string or folder name, and without
risking a typo that silently produces a scope matching nothing

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-50: Tags and Locations
  Autocomplete* — "Tag and folder/location input fields across the app (at
  minimum the Vault Scope field, `REQ-SB-29`) suggest real, existing vault
  tags and folder paths as the user types, sourced from the vault's own
  current content — never a fixed or fabricated list." Acceptance: "A tag
  or location input field offers real, vault-derived suggestions as the
  user types, drawn from the vault's actual current tags and folder paths
  — never a hardcoded or fabricated suggestion list."
- **PRD breadcrumb (2026-08-14, operator-directed, cited verbatim):**
  "Tags and Locations Should Support Auto Complete." Minimal, contained
  requirement — this codebase already has real, vault-derived enumeration
  primitives to build on. Genuinely open, left to `/spec`: the full list
  of input fields this applies to beyond the Vault Scope field named by
  the operator (candidates include the Wizard's own Section/Scope fields,
  `REQ-SB-46`).
- **Field-scope decision (resolved here, by direct code inspection — not a
  guess):**
  - **IN scope, this story:** `AgentDetailPanel.tsx`'s "Vault scope"
    kv-row (built by the already-`Done` `REQ-SB-29-US-01-T05`) — a
    free-text, comma-separated input, committed `onBlur`
    (`scopeDraft`/`handleScopeCommit`, confirmed by direct read). This is
    the PRD's own explicitly-named minimum target field, and it is
    currently stable (`Done`, not scheduled for any rework).
  - **DEFERRED, not in this story:** `CreateAgentWizard.tsx`'s Worker-step
    "Vault scope" field (`workerScope` input, id `workerScope`,
    confirmed by direct read — the identical free-text pattern, just in a
    second location). This is deliberately **not** included here: it is
    the exact field `REQ-SB-46` (Agent Creation Wizard Redesign — Popup
    Modal with Visual Step Bar) is about to relocate into its own new
    Step 1 "Scope" region (see `REQ-SB-46-US-01`'s Context, Scenario 3),
    and `REQ-SB-46-US-01` itself is still `status: Draft`, `gate:
    flagged` (unresolved net-new-design-needed + an unconfirmed
    field-to-step mapping) — its own eventual shape/markup for this field
    is not yet settled. Building autocomplete into `CreateAgentWizard.tsx`'s
    *current* markup now would very likely be discarded or reworked the
    moment `REQ-SB-46` ships, since that story's own Constraints preserve
    the underlying Scope value/mechanism unchanged while relocating its
    presentation. Deferring loses nothing — the identical autocomplete
    behaviour specced here is the natural, low-effort follow-on to layer
    onto `REQ-SB-46`'s redesigned field once it exists, not a different
    behaviour. This is a defensible, reasoned scoping call under the
    PRD breadcrumb's own explicit delegation to `/spec` ("genuinely open
    ... left to `/spec`"), not a guess filling an ambiguity gap — so it is
    not flagged as a material assumption.
  - **Out of scope by definition, not by deferral:** every Section/Provider
    field anywhere (`AgentDetailPanel.tsx`'s Section/Provider rows,
    `CreateAgentWizard.tsx`'s `expertSection`/`workerSection`/
    `producerSection`/`workerScope`-adjacent Section `<select>`s) — these
    are `<select>` dropdowns backed by a fixed, already-enumerated
    `fetchSections()` list (confirmed by direct read), not free-text
    inputs. Autocomplete is a typeahead-over-free-text pattern; it does
    not apply to an already-bounded `<select>`.
- **Data-source decision (resolved here, by direct code inspection — not a
  guess):** no new vault-scanning primitive is needed; two already-real,
  already-shipped vault-derived enumeration functions cover the full
  suggestion surface, confirmed by direct read:
  - **Tags:** `GET /vault-search/tags` (`app/api/vault_search_router.py`
    → `app/business/vault_search.py::list_tags()`, shipped by the
    already-`Done` `REQ-SB-02-US-01`) already returns the real, current,
    vault-derived tag list (with counts) over HTTP. Reused as-is — no
    change needed to this endpoint or its business function.
  - **Folders:** `app/data_access/vault_writer.py::list_known_kinds()`
    (also exposed at the business layer as
    `app/business/vault_query_tools.py::list_known_kinds()`) already
    returns the real, current folder names directly under `Work/` —
    exactly the same folder-name shape
    `scope_query_tools`/`list_notes_matching_scope`'s own folder-match
    branch checks a scope value against (`path.parent.name`). This
    primitive is real and vault-derived today, but it is **not currently
    exposed over HTTP anywhere** — only via the internal MCP tool
    (`app/api/mcp_server.py`) and direct business-layer calls. **The one
    genuine gap this story fills is a missing HTTP exposure, not a
    missing data-layer capability.**
  - **Proposed shape (left to the architect/decomposer for the exact
    endpoint contract):** one new, thin, additive endpoint (e.g. `GET
    /vault-search/scope-suggestions`) that composes the two functions
    above into one combined, deduplicated suggestion list for the Vault
    Scope field's typeahead — adding zero new vault-scanning logic of its
    own. Whether keystroke filtering happens server-side (a `q=` query
    param) or client-side against the fetched list (a small, cacheable
    set at this vault's real scale, mirroring how `agents-map.html`'s
    existing tag-filter chip row already fetches `list_tags()` once) is
    ordinary implementation latitude, not a spec-level decision.
- **Why `/design` is not run for this pass:** this is a small,
  well-understood UI interaction pattern (typeahead/autocomplete over an
  existing free-text input) that a coder can competently improvise
  directly against `AgentDetailPanel.tsx`'s already-established Keywords/
  Vault-scope row markup — the same precedent this session has already
  applied to other backend-heavy/pattern-matched passes. The target field
  itself already exists in shipped code; this story adds a suggestion
  behaviour on top of it, not a new screen region. See Notes → Prototype
  parity for the one carried-over prototype gap this story does not
  introduce or need to resolve.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: Real, vault-derived tag suggestions appear as the user types

```gherkin
Given the user is editing an agent's Vault scope field on the Agent
    Settings surface
  And the vault currently has notes tagged "customer/masdar"
When the user types "mas" into the Vault scope field
Then a suggestion list appears offering "customer/masdar"
  And every suggestion offered corresponds to a real, currently-existing
    vault tag returned by GET /vault-search/scope-suggestions — never a
    fabricated or hardcoded value
```
<!-- AC-ID: REQ-SB-50-US-01-AC-01 -->

### Scenario 2: Real, vault-derived folder suggestions appear as the user types

```gherkin
Given the vault currently has a "Pipeline" folder under Work/
When the user types "pipe" into the Vault scope field
Then a suggestion list appears offering "Pipeline"
  And every suggestion offered corresponds to a real, currently-existing
    vault folder name returned by GET /vault-search/scope-suggestions —
    never a fabricated or hardcoded value
```
<!-- AC-ID: REQ-SB-50-US-01-AC-02 -->

### Scenario 3: No match returns an honest empty result, never a fabricated suggestion

```gherkin
Given no tag or folder name in the vault currently contains "zzz"
When the user types "zzz" into the Vault scope field
Then no suggestions are shown
  And no fabricated or guessed suggestion is offered in place of a real
    match
```
<!-- AC-ID: REQ-SB-50-US-01-AC-03 -->

### Scenario 4: Autocomplete does not disturb already-assigned scope values

```gherkin
Given the agent already has "customer/masdar" and "kind/meeting" assigned
    as its Vault scope
When the user starts typing a third value into the Vault scope field
Then suggestions are offered only for the value currently being typed
  And "customer/masdar" and "kind/meeting" remain assigned, unaffected by
    the in-progress suggestion list
When the user selects a suggestion (via a mousedown-triggered selection
    that does not lose the pick to the field's own blur-commit), or
    finishes typing and commits the field via blur
Then the newly added value joins the existing two values
  And neither "customer/masdar" nor "kind/meeting" is duplicated, removed,
    or reordered
```
<!-- AC-ID: REQ-SB-50-US-01-AC-04 -->

## Affected Screens

- `html-prototype/agents-map.html` — the agent detail side panel's
  Settings `kv-list` "Vault scope" row gains suggestion-list behaviour as
  the user types. See Notes → Prototype parity for this row's existing
  (carried-over, pre-existing) prototype-coverage gap.

## Dependencies

- **Blocked by:** `REQ-SB-29-US-01` (`Done`) — the Vault Scope field this
  story adds autocomplete to; already shipped.
- **Blocked by:** `REQ-SB-02-US-01` (`Done`) — `vault_search.list_tags()`,
  the real tag-enumeration source this story reuses as-is.
- **Related to, not built on:** `REQ-SB-46-US-01` (`Draft`, `gate:
    flagged`) — its own redesigned Worker-step Scope field is the natural
  follow-on target for this same autocomplete behaviour once that story's
  own net-new-design-needed and field-to-step-mapping flags are resolved
  and it ships; not addressed here (see Context).
- **External:** none new.

## Constraints

- Suggestions must always be sourced live from the vault's actual current
  tags and folder names — never a hardcoded, cached-stale, or fabricated
  list (PRD Acceptance text, verbatim).
- Must not interfere with, duplicate, or reorder any already-committed
  value already present in the Vault Scope field's multi-value list
  (Scenario 4).
- No new vault-scanning primitive — compose the two already-existing
  vault-derived enumeration functions (`vault_search.list_tags()`,
  `vault_writer.list_known_kinds()` / `vault_query_tools.list_known_kinds()`),
  not a reimplementation of tag/folder enumeration.
- Follows `AgentDetailPanel.tsx`'s already-established Vault-scope/
  Keywords row markup and interaction pattern (free-text, comma-separated,
  `onBlur`-commit) — this story layers a suggestion list on top of that
  existing pattern, it does not replace it with a different input control.

## Implementation Tasks

<!-- Decomposer's job at /plan-tasks — left empty here per template. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-50-US-01-T01 | backend | Add `GET /vault-search/scope-suggestions` composing `list_tags()` + `vault_writer.list_known_kinds()` | `app/business/vault_search.py`, `app/api/vault_search_router.py` | `Implementation/Tasks/REQ-SB-50-US-01-T01-scope-suggestions-endpoint.md` |
| REQ-SB-50-US-01-T02 | frontend | Vault Scope field autocomplete dropdown (fetch-once-per-agent, client-filter, `onMouseDown` select) | `features/vault-browser/client.ts`, `features/agents-map/AgentDetailPanel.tsx` | `Implementation/Tasks/REQ-SB-50-US-01-T02-vault-scope-autocomplete-dropdown.md` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **`CreateAgentWizard.tsx`'s Worker-step Vault Scope field** — deferred to
  a natural follow-on once `REQ-SB-46`'s wizard redesign ships (see
  Context).
- **Any Section/Provider `<select>` field, anywhere** — already a bounded
  dropdown over a fixed enumerated list; autocomplete does not apply.
- **General free-text vault search** (`REQ-SB-02`) — this is a narrow
  suggestion-list typeahead only, not a search feature.
- **Fuzzy/typo-tolerant matching** — the PRD's acceptance text asks only
  for real, vault-derived suggestions as the user types; a straightforward
  substring/prefix match against real current values satisfies this pass.
- **Any new tag/folder value being created through this field** — this
  story only suggests already-existing values; whether a genuinely new tag
  can still be typed and committed as before (unsuggested) is unchanged,
  existing `REQ-SB-29-US-01` behaviour, not altered here.

## Notes

**Prototype parity (agents-map.html):**

- Side panel Settings `kv-list` "Vault scope" row — this row itself has
  **no approved prototype coverage** (`REQ-SB-29-US-01` shipped it without
  a `/design` pass, by explicit operator decision at that time — confirmed
  by direct inspection of `agents-map.html`, unchanged since). This is a
  **carried-over gap this story does not introduce and is not required to
  resolve** — this story only adds suggestion-list behaviour on top of an
  already-real, already-shipped field; it does not add new screen real
  estate that would otherwise need `/design`. Per the well-understood-
  interaction-pattern precedent, `gate: flagged (net-new-design-needed)`
  is deliberately **not** set for this reason.
- Every other side-panel region (Overview, Chat, Available Actions,
  Communication History) — **N/A**, not touched by this story.

**Why `gate: clear`:** no MUST-FLAG trigger fired. (1) No material
assumption beyond the field-scope and data-source decisions above, both
resolved by direct code inspection against real, already-shipped
primitives — not guesses filling a PRD gap, and the field-scope question
is one the PRD breadcrumb itself explicitly delegates to `/spec`. (2)
`REQ-SB-50`'s own Acceptance text carries no `<!-- Draft -->` marker — it
is finalised PRD text. (3) N/A — no ADR touched. (4) No
`ESCALATIONS.md` entry written. (5) Not oversized — one new thin endpoint
composing two already-existing primitives, plus one frontend field's
typeahead behaviour. (6) N/A — coder-only trigger. (7) No contradictory
inputs found. (8) The field-scope and data-source questions each had one
clearly defensible answer once the real code was inspected (REQ-SB-46's
own unresolved `Draft`/`flagged` status makes deferring its field the
stronger option, not an equally-valid coin flip; `list_known_kinds()`'s
existing shape is the only vault-derived folder-name primitive that
already exists) — not genuinely unclear or multiply-valid.

gate: clear 2026-08-14 — no triggers fired (no ADRs touched, no
unfinalised requirement text, no contradictory inputs, no oversized scope,
field-scope/data-source decisions grounded in direct code inspection
against real shipped primitives rather than guessed).

**Architect pass (2026-08-14):** Architecture scope: §Browse & Search →
"Tag/Folder Scope Suggestions" (`REQ-SB-50-US-01`, no new ADR),
§Agent-to-Tag/Folder Vault Scoping → Addendum (`REQ-SB-50-US-01`, no new
ADR). No ADR written — confirmed, by direct read of
`vault_search.py::list_tags()` and `vault_writer.py::list_known_kinds()` /
`vault_query_tools.py::list_known_kinds()`, that both source functions are
already real and shipped; the one genuine gap (folder enumeration not
exposed over HTTP) is closed by a single new thin composing endpoint (`GET
/vault-search/scope-suggestions` → new `vault_search.list_scope_suggestions()`),
matching this file's own repeated "ordinary same-shape extension of
already-Accepted structure" no-ADR precedent (`ADR-003` layering,
`list_tags()`/`search()`'s own composition shape) — no new tool,
framework, storage mechanism, or trust surface introduced. `gate: clear`
carried forward — the architect pass introduced no assumption beyond
recording an implementation-internal shape decision (two distinct
`tags`/`folders` lists, no server-side `q=` filter) already flagged in the
story's own Context as ordinary implementation latitude, and a
frontend-interaction-order note (`onMouseDown` before `onBlur`) for the
coder's benefit — neither rises to a MUST-FLAG trigger.

**Decomposer pass (2026-08-14):** All 4 Gherkin scenarios locked as
`REQ-SB-50-US-01-AC-01`..`AC-04` (tag suggestions; folder suggestions;
honest empty result; non-disruption of already-assigned scope values).
Two tasks created: `REQ-SB-50-US-01-T01` (backend —
`vault_search.list_scope_suggestions()` + `GET
/vault-search/scope-suggestions`, verified against `AC-01`/`AC-02` at the
endpoint layer) and `REQ-SB-50-US-01-T02` (frontend — `fetchScopeSuggestions()`
in `features/vault-browser/client.ts`, imported cross-feature into
`AgentDetailPanel.tsx`; fetch-once-per-agent-switch; client-side
filter-as-you-type; `onMouseDown`, not `onClick`, selection to avoid losing
the pick to the field's own `onBlur` commit; verified against all 4 ACs at
the UI layer), `T02 depends_on [T01]`. Read before planning: real current
state of `vault_search.py`, `vault_search_router.py`,
`vault_writer.py::list_known_kinds`, `AgentDetailPanel.tsx`'s Vault scope
row/`handleScopeCommit`, `features/vault-browser/client.ts`, and
`Implementation/Learnings.md` (no directly-applicable prior entry for this
exact endpoint/dropdown shape; the `onMouseDown`-before-`onBlur` handling
follows the architect's own flagged gotcha, not a new discovery). No
MUST-FLAG trigger fired during decomposition: no material assumption
beyond ordinary task-shape/verification-technique choices; no unfinalised
requirement text; no ADR touched; no `ESCALATIONS.md` entry; both tasks
are single-session-sized (one new function + one route; one new client
function + one dropdown behaviour on an existing field); every locked AC
has a matching AC-tagged verification step (`T02` covers all 4 at the
user-observable layer; `T01` additionally covers `AC-01`/`AC-02` at the
endpoint layer); no contradictory inputs; the task split (backend
endpoint vs. frontend dropdown) was the only defensible breakdown, not a
multiply-valid choice. `depends_on` is acyclic (`T02` → `T01`, no cycle).

gate: clear 2026-08-14 — no triggers fired (all ACs locked, all locked ACs
have a tagged verification step, `depends_on` acyclic). Story advances
`Draft` → `Ready`; both tasks written at `status: Ready` in lockstep.

---

**Coder pass (2026-08-14).** Both tasks built and verified live end-to-end
against all 4 locked ACs against the real, indexed vault (real `GET
/vault-search/scope-suggestions`, real CDP-driven browser session). One
real, disclosed environmental finding (not a code defect): `T01`'s own
`AC-02` example folder (`Work/Pipeline`) doesn't exist in the real vault
today (an already-known, already-documented gap from `REQ-SB-29-US-01`) —
verified the underlying guarantee against the real folders that do exist
instead. One real, disclosed verification-technique substitution (not an
AC weakening): a raw synthetic `blur` DOM event does not reliably reach
React's own delegated `onBlur` handler in this project's CDP test
environment — used the already-established Fiber-props direct-invoke
technique (`SPRINT-020`) instead, confirmed correct via real backend
`GET` calls. All real agent state touched during verification was
independently reconfirmed reverted to its exact original values. Both
tasks `Done`; story `Done`.

gate: clear 2026-08-14 — no MUST-FLAG trigger fired; both disclosed
findings above are environmental/technique substitutions, not AC
weakenings, ADR deviations, or new material assumptions.
