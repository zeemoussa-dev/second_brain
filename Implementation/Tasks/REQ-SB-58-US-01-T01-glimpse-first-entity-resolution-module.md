---
id: REQ-SB-58-US-01-T01
title: New app/business/glimpse_first_qa.py — rank-1 entity resolution + Glimpse/Background read
parent_story: REQ-SB-58-US-01
requirement_id: REQ-SB-58
type: backend
status: Done
gate: flagged
gate_reason: "ESCALATIONS.md ESC-046 written (real, pre-existing vault-state collision found live, out-of-scope for this task) — see REVIEW-QUEUE.md pointer."
phase: P1
depends_on: []
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-58-US-01-T01 — `glimpse_first_qa.py` — rank-1 entity resolution + Glimpse/Background read

## Parent Story

- Story: [[REQ-SB-58-US-01]] — `../UserStories/REQ-SB-58-US-01-customer-project-aware-expert.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-58 *Customer/Project-Aware Expert (Glimpse-First Answers)*

---

## Objective

Build the new, standalone `app/business/glimpse_first_qa.py` module: one public
function, `resolve_glimpse_first_context(question: str) -> dict | None`, that
resolves a question to a Customer/Project via `vault_search.search()`'s own
rank-1 result only, then reads that entity's own OKF concept file `## Glimpse`
and `## Background` sections. This task builds and directly verifies the
module in isolation — `T02` wires it into the live chat graph and performs
all of the parent story's own locked-AC verification (this module has no
chat-facing behavior of its own until `T02` lands).

---

## Starting State → End State

**Before / Inputs:**
- No `app/business/glimpse_first_qa.py` file exists yet.
- `app/business/vault_search.py::search(query, limit=20) -> {"query": str,
  "results": [{"stem", "title", "kind", "tags", "rank", "score"}, ...]}` is
  real, `Done` (`ADR-026`) — confirmed by direct reading. `results` is
  already rank-sorted; `results[0]` (when non-empty) is the single
  highest-scoring note for `query` across the WHOLE vault. `"kind"` is
  `entry["frontmatter"].get("type", "Unknown")` — a Customer/Project OKF
  concept file's own `type` is literally `"customer"` / `"project"`
  (confirmed by direct reading of `vault_writer.build_customer_concept_
  frontmatter`/`build_project_concept_frontmatter`).
- `app/business/vault_indexing.py::get_index() -> dict[str, dict]` is real,
  `Done` (`ADR-024`) — keyed by stem; each entry carries `"path"` (the
  note's real on-disk path, as a string) and `"frontmatter"` (the full,
  real frontmatter dict, including `"title"` for a concept file).
- `app/data_access/vault_writer.py::read_body_section(path, header) ->
  str` is real, `Done` (`ADR-042` point 2) — returns the stripped text
  strictly between `header`'s own line and the next `## `-level header (or
  end of file), or `""` if `header` is not found at all. Never writes.

**After / Outputs:**
- New file `app/business/glimpse_first_qa.py` with one public function:
  `resolve_glimpse_first_context(question: str) -> dict | None`, returning
  `{"entity_type": "customer" | "project", "entity_name": str, "glimpse":
  str, "background": str}` on a real Customer/Project rank-1 match, `None`
  otherwise (no results at all, or the rank-1 result is some other note
  kind).

---

## Files to Modify

- `src/backend/app/business/glimpse_first_qa.py` (new file)

---

## Constraints

- Inherits from parent story:
  - **Entity resolution reuses `vault_search.search()` verbatim — no new
    matching/ranking logic** (story Constraint). Take `results[0]` only,
    never a filtered or re-ranked subset, never a second scoring pass.
  - **Read-only** — this module never calls `replace_body_section`/
    `append_person_note_update_line`/any other Glimpse/Background/History
    write primitive (`REQ-SB-54` point 7's ownership rule stays with
    `project_customer_synthesizer.py` alone).
  - Must respect the `api → business → data_access` layer boundary
    (`ADR-003`) — this module composes `vault_search`/`vault_indexing`
    (business) and `vault_writer.read_body_section` (data_access) only, no
    new external dependency.
- **Resolve the matched entity's own concept-file path from the search
  result's own `vault_indexing.get_index()` entry directly** — never
  recompute it via `customer_directory_paths`/`project_directory_paths`
  from a name/slug round-trip (architecture.md's own documented
  reasoning: by construction, the exact same on-disk file `project_
  customer_synthesizer.py` already owns and keeps current).
- This function is a plain business-layer call, never bound as a model
  tool and never registered on `app/api/mcp_server.py` — `T02`'s own new
  `graph.py` node is its only caller.
- Do not modify `vault_search.py`, `vault_indexing.py`, or
  `vault_writer.py` — every primitive this task composes already exists,
  unmodified.

---

## Tests

<!-- This module has no chat-facing behavior of its own — none of the
parent story's locked ACs are verifiable through a direct call to this
function alone (every Scenario names an actual vault-qa reply). T02 wires
this module into the live graph and carries every AC-tagged step. This
task's own steps are non-AC direct-call smoke checks confirming the
module's own contract before T02 composes around it. -->

**Manual verification steps:**

1. Non-AC smoke check: direct call against a real, existing Customer with
   real, non-empty `## Glimpse` content (any real Customer already
   synthesized by `REQ-SB-57`'s own Synthesizer, or a disposable one
   created via `vault_writer.create_customer_directory_baseline` plus a
   direct `vault_writer.replace_body_section(..., "## Glimpse", <text>)`
   call). Call `resolve_glimpse_first_context("what's the status of
   <that customer's exact title>?")`. Confirm the return value's
   `entity_type == "customer"`, `entity_name` matches the concept file's
   own `frontmatter["title"]` exactly, and `glimpse` matches a direct
   `vault_writer.read_body_section(concept_path, "## Glimpse")` call
   against the same file, byte-for-byte.
2. Non-AC smoke check: repeat step 1 against a real or disposable Project
   concept file (`vault_writer.create_project_directory_baseline`).
   Confirm `entity_type == "project"`.
3. Non-AC smoke check: call `resolve_glimpse_first_context(...)` with a
   question that does not name any real Customer/Project (e.g. a generic
   vault-structure question, or a nonsense token unlikely to appear
   anywhere in the vault). Confirm the return value is `None`.
4. Non-AC smoke check: against a concept file whose `## Background`
   section is still empty (the common, not-yet-amended case —
   `create_customer_directory_baseline`/`create_project_directory_
   baseline`'s own default body), confirm `background == ""` rather than
   raising — `read_body_section`'s own established empty-section
   contract, unchanged by this task.
5. Static check: confirm `glimpse_first_qa` does not appear anywhere in
   `app/api/mcp_server.py` or `app/business/agent_orchestration/
   mcp_client.py` — never registered as an MCP tool.
6. Clean up any disposable fixture created during verification; confirm
   pre-existing real vault content is byte-for-byte/mtime-unchanged
   afterward.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `resolve_glimpse_first_context` returns a real, correctly-shaped
      dict for both a Customer and a Project rank-1 match, and `None` for
      a non-match — confirmed via direct calls against real vault fixtures
- [x] `glimpse`/`background` values match direct `read_body_section` calls
      against the same concept file, byte-for-byte
- [x] No write primitive is ever called by this module
- [x] `glimpse_first_qa` is never registered as an MCP tool
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Wiring this function into `graph.py`, gating it to `vault-qa`, or
  injecting its result as a `SystemMessage` — `T02`.
- `state.py`'s grounding-text clause — `T02`.
- Any live, chat-facing verification of the parent story's own locked ACs
  — every Scenario names an actual vault-qa reply, which does not exist
  until `T02` lands; `T02` carries every AC-tagged verification step.
- Evidence drill-down (Scenario 3) — needs no new tool/function at all
  (`T02`'s own live-verification step only, per architecture.md).

---

## Context / Notes

`Implementation/Architecture/architecture.md` → "Glimpse-First `vault-qa`
Answers — entity resolution + Glimpse/Background context injection,
evidence drill-down unchanged" is the full architectural reasoning this
task implements point 1 of, operator-confirmed 2026-08-18 (see the parent
story's own `## Notes`). `ADR-026` (ranked search), `ADR-024` (search
index), `ADR-042` point 2 (`read_body_section`) are unchanged, referenced
— no new ADR.

`entity_name` reads `frontmatter["title"]` directly rather than
`vault_search`'s own `_title_for`/summary `"title"` field (which falls
back to the note's filename stem when no `"subject"` key is present — the
convention `vault_search.py` designed for Email/Meeting notes, not concept
files) — a decomposer-authored implementation-latitude choice, logged here
for the coder to follow rather than re-derive: the concept file's own
`frontmatter["title"]` is the exact, canonical Customer/Project name
`build_customer_concept_frontmatter`/`build_project_concept_frontmatter`
wrote it as, and is more accurate for this context-injection use.

---

## Implementation Log

**Built:** `src/backend/app/business/glimpse_first_qa.py` (new file) — one
public function, `resolve_glimpse_first_context(question: str) -> dict |
None`. Composes `app.business.vault_search.search` (rank-1 result only),
`app.business.vault_indexing.get_index` (resolves the matched entry's own
`"path"`/`frontmatter["title"]` directly — no `customer_directory_paths`/
`project_directory_paths` round-trip), and `app.data_access.vault_writer.
read_body_section` (both `## Glimpse` and `## Background`, read-only) —
exactly the mechanism architecture.md's "Glimpse-First `vault-qa` Answers"
section specifies. No deviation from the task's own End State/Constraints.

**This task has no locked story-level AC of its own** (per the story's
Implementation Tasks table and this task's own Tests-block preamble — all
6 locked ACs are carried by `T02`'s live graph-wiring verification). The
6 non-AC manual smoke-check steps below are this task's own module-level
contract verification, run against the REAL configured vault
(`VAULT_PATH`), via a throwaway Python script
(`app/business` imported directly, `vault_indexing.rebuild_index()` called
before/after each fixture change — no HTTP layer needed, this module has
no route).

- **Step 1 (Customer smoke check) — PASSED.** Real customers already
  synthesized by `REQ-SB-57` all turned out to collide with a stale
  legacy flat hub note in `vault_indexing`'s stem-keyed index (see
  `ESC-046` below) — used the task's own explicitly-sanctioned disposable-
  fixture alternative instead: `vault_writer.create_customer_directory_
  baseline("GlimpseFirstProbeCustomerZZ")` +
  `replace_body_section(..., "## Glimpse", "PROBE-CUSTOMER-GLIMPSE-VALUE-
  4d81a2")`. `resolve_glimpse_first_context("what's the status of
  GlimpseFirstProbeCustomerZZ?")` returned `entity_type == "customer"`,
  `entity_name == "GlimpseFirstProbeCustomerZZ"` (exact
  `frontmatter["title"]` match), `glimpse` byte-for-byte identical to a
  direct `read_body_section` call against the same file.
- **Step 2 (Project smoke check) — PASSED.** Disposable Project via
  `vault_writer.create_project_directory_baseline("GlimpseFirstProbeCustomerZZ",
  "GlimpseFirstProbeProjectZZ")` + `replace_body_section(..., "## Glimpse",
  "PROBE-PROJECT-GLIMPSE-VALUE-77f3c9")`.
  `resolve_glimpse_first_context("what's the status of
  GlimpseFirstProbeProjectZZ?")` returned `entity_type == "project"`,
  correct `entity_name`, `glimpse` byte-for-byte identical to a direct
  `read_body_section` call.
- **Step 3 (no-match case) — PASSED.** `resolve_glimpse_first_context(
  "zzqxvortexpluralnonexistenttoken998877 unrelated gibberish")` returned
  `None`.
- **Step 4 (empty `## Background` case) — PASSED.** The disposable
  Customer's own `## Background` is the untouched `create_customer_
  directory_baseline` default (empty); both the direct `read_body_section`
  call and `resolve_glimpse_first_context`'s own `"background"` field
  returned `""`, no raise.
- **Step 5 (static MCP-registration check) — PASSED.** `grep
  "glimpse_first_qa"` against `app/api/mcp_server.py` and `app/business/
  agent_orchestration/mcp_client.py` — zero matches in either file.
- **Step 6 (cleanup) — PASSED.** Removed the entire disposable
  `Work/Customers/GlimpseFirstProbeCustomerZZ/` directory (which also
  removed the nested disposable Project). Confirmed pre-existing real
  vault content (`Work/Customers/Core42.md` and `Work/Customers/Core42/
  Core42.md`, spot-checked) byte-for-byte/mtime-unchanged afterward — this
  module never wrote to either during any of the above steps.

**Scope-internal judgement call (not an escalation):** `path` is imported
as `pathlib.Path` and wraps `entry["path"]` (a string, per `vault_
indexing`'s own documented shape) before passing to `read_body_section`,
matching `vault_search.search`'s own identical `Path(entry["path"])`
usage one function up — not a new convention.

**Real, out-of-scope finding, disclosed rather than routed around
silently — `ESC-046` (`ESCALATIONS.md`, `Open`):** 14 of 17 real
Customers already migrated to the `ADR-042` OKF directory shape still
carry a stale, pre-migration flat `Work/Customers/<Name>.md` hub note on
disk, never retired by `customer_hub_linking.ensure_customer_hub_note`'s
own restructure. Both files share the same filename stem, and `vault_
indexing.rebuild_index()`'s stem-keyed dict lets the (later-visited,
per `list_all_note_paths()`'s sort order) legacy flat note silently win
— confirmed live for `Core42` (`get_index()["Core42"]["frontmatter"]
["type"] == "Customer"`, the legacy shape, not the real, current
`"customer"` OKF concept file). This module (and anything else reading
through `vault_indexing.get_index()[stem]`) reads the WRONG file for
those 14 Customers. Out of this task's own `## Files to Modify` (fixing
it means editing `vault_indexing.py`/`vault_writer.py`/`customer_hub_
linking.py`, all explicitly forbidden by this task's own Constraints, or
deleting real vault files, which this task's own scope has no mandate
to do). `REVIEW-QUEUE.md` entry written, directly informing `T02`'s own
real-Customer test-data choice (must use `Microsoft Azure`/`Azerbaijan
Ministry of Digital Development and Transport`, the two collision-free
real, migrated Customers, or a disposable fixture — never one of the 14
shadowed ones). `MEMORY.md` Constraints updated with the same finding for
future sessions.

**`gate: flagged`** — solely because this pass wrote an `ESCALATIONS.md`
entry (MUST-FLAG trigger 4); the finding itself does not block this
task's own Done status (verified via the task's own explicitly-sanctioned
disposable-fixture alternative) and required no design decision to
complete `T01`'s own build.
