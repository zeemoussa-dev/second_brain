---
id: REQ-SB-55-US-01-T01
title: vault_writer.py new primitives — header-scoped growing body-section append, unconditional frontmatter-key set, Customer's open-Projects enumeration
parent_story: REQ-SB-55-US-01
requirement_id: REQ-SB-55
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-043 created) — carried from the parent story; the human reviews ADR-043 alongside this task breakdown. No decomposer-owned trigger fired on this task itself. Stays flagged post-completion for the additional scope-internal judgement call logged in the Implementation Log below (primitive #2 already existed under a different name) — for human spot-check, not a blocker."
phase: P1
depends_on: []
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-55-US-01-T01 — `vault_writer.py` new primitives

## Parent Story

- Story: [[REQ-SB-55-US-01]] — `../UserStories/REQ-SB-55-US-01-email-capture-and-threading-pipeline.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-55 *Email Capture & Threading Pipeline*

---

## Objective

Add three mechanical, data_access-layer primitives to `app/data_access/vault_writer.py` that every later Job task in this story needs and none of them should reinvent: (1) a header-SCOPED, growing body-section append (`## Transcript` and the new `## Attachments` section are both independently growing, and only one section can be "physically last" for the existing EOF-blind `append_person_note_update_line` to correctly target); (2) an unconditional frontmatter-key set (overwrite-or-insert — `insert_frontmatter_key_if_missing` only ever inserts, it cannot update an already-present key, which `participants`/`last_message_at`/tag-union writes all need); (3) an enumeration of one Customer's own `projects/*/` subdirectories and each one's `status`, for `Route-to-Project`'s "currently open Projects" guess (`ADR-043` Consequences).

---

## Starting State → End State

**Before / Inputs:**
- `replace_body_section(path, header, new_content)` (`T01` of `REQ-SB-54-US-01`, `ADR-042` point 2) exists — full-region regeneration, header-scoped, no-op if the header is absent. This task's own append primitive REUSES its header/next-header location logic, generalized to insert-before-region-end instead of replace-region.
- `insert_frontmatter_key_if_missing(path, key, value)` exists — inserts only if the key is absent; never overwrites an already-present value.
- `okf_directory_paths`/`_project_directory_root`/`project_directory_paths`/`project_concept_file_exists` (`REQ-SB-54-US-01`, `ADR-042` point 4) exist — the deterministic path family a Customer's Project directories already live under.
- Thread's baseline body (`create_thread_note_baseline`, `REQ-SB-54-US-01-T02`) is exactly `## Summary` (empty) + `## Transcript` (empty) — there is no `## Attachments` header on a freshly-created Thread note; this story is the first to grow that section.

**After / Outputs:**
- A new function that appends one line into a header-scoped, growing body region — creating the header itself (at end of file) on the FIRST call for a note that doesn't have it yet, and inserting before the next `##`-level header (or EOF) on every subsequent call. Both `## Transcript` (already has its header from baseline) and `## Attachments` (doesn't, until the first attachment) go through this same function.
- A new function that unconditionally sets one frontmatter `key: value` — overwriting the value if the key is already present, inserting it (same position `insert_frontmatter_key_if_missing` would use) if absent. Handles scalar and list values identically (reuses `_format_frontmatter_value`), so it also covers a tags-union rewrite.
- A new function, `list_customer_projects(customer: str) -> list[dict]`, returning one `{"project": <title>, "slug": <concept_slug>, "status": <status>}` entry per real Project directory nested under that Customer — `[]` if the customer has no `projects/` subdirectory yet (mirrors `list_notes_in_kind_folder`'s own "not-yet-created folder returns `[]`" contract).

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — add all three functions, placed near the existing Thread/OKF-directory primitives (after `replace_body_section` for the append primitive and the frontmatter setter; after `ensure_project_directory_baseline` for the Projects enumeration).

---

## Constraints

- Inherits from parent story.
- The header-scoped append primitive must reuse `replace_body_section`'s own `_BODY_SECTION_HEADER_PATTERN`/header-location logic (a literal, whole-line regex match — never a raw substring search) rather than inventing a second, divergent header-finding mechanism.
- The header-scoped append primitive's "header not found" branch must CREATE the header (unlike `replace_body_section`'s own documented no-op-if-absent contract, which is a deliberately different case — a REGENERATED section always already has its header from baseline; a GROWING section like `## Attachments` may not yet exist on a note's first attachment). Do not change `replace_body_section`'s own no-op behavior to accommodate this — write a new function.
- The unconditional frontmatter-key setter must never touch the body or any OTHER frontmatter key — scoped strictly to the one named key, mirroring `insert_frontmatter_key_if_missing`'s/`rename_frontmatter_key`'s own surgical-edit discipline.
- `list_customer_projects` must read each Project's own concept-file frontmatter directly (`read_note`) — never assume a fixed field order, never hardcode a status value; return whatever `status` the concept file actually carries (including a blank/missing one, read back as `None` or `""`, honestly — never fabricate `"active"` for a Project whose frontmatter doesn't actually say so).
- Do not modify `replace_body_section`, `insert_frontmatter_key_if_missing`, `create_thread_note_baseline`, `ensure_thread_note_baseline_frontmatter`, or any OKF-directory-family function — this task only ADDS new functions.
- Pure `data_access` — no business-logic decisions (e.g. no "which Project is currently open" filtering here; that judgement belongs to `Route-to-Project`, `T04`).

---

## Tests

<!-- No locked AC of the parent story is verified directly by this
foundational data_access task alone — every AC-tagged step lives in the
later Job tasks that consume these primitives. This task's own Tests
verify the three new primitives' own direct correctness, which those
later tasks' own AC-tagged steps then rely on. -->

**Manual verification steps:**
1. Against a throwaway scratch vault (`VAULT_PATH` env-overridden to a `tempfile.mkdtemp()` directory, never the real configured vault), create a Thread note via `create_thread_note_baseline("test-conv-append", tags=["kind/thread"])`. Call the new header-scoped append primitive twice against `## Transcript` with two different lines — confirm both lines appear inside `## Transcript`, in call order, and `## Summary` is completely untouched.
2. On the SAME note, call the header-scoped append primitive against `## Attachments` (a header that does not exist yet) with one line — confirm a NEW `## Attachments` header is created (at the end of the file, after `## Transcript`) containing exactly that one line, and confirm `## Summary`/`## Transcript` (including the two lines from step 1) are completely unchanged. Call it again against `## Attachments` with a second line — confirm both attachment lines now appear under the SAME single `## Attachments` header (no second header created).
3. On a note with an existing `tags: ["a", "b"]` frontmatter value, call the new unconditional frontmatter-key setter with `key="tags", value=["a", "b", "c"]` — confirm the note's `tags` now reads back as exactly `["a", "b", "c"]` and every other frontmatter key/the body are unchanged. Call the setter again with `key="project", value="Some Project"` on a note that has no `project` key yet — confirm it is inserted correctly (readable via `read_note`). Call the setter a THIRD time on the SAME `project` key with a different value — confirm it overwrites (not duplicates) the existing line.
4. Create a Customer directory (`create_customer_directory_baseline("Acme Corp")`) with zero Projects — confirm `list_customer_projects("Acme Corp")` returns `[]`. Create two real Project directories under it (`create_project_directory_baseline("Acme Corp", "Project Alpha")`, `create_project_directory_baseline("Acme Corp", "Project Beta")`) — confirm `list_customer_projects("Acme Corp")` now returns exactly 2 entries, each with the correct `project`/`slug`/`status` (`"active"`, the OKF baseline default) read directly from each concept file's own frontmatter, not fabricated.
5. Regression check: `ast.parse()` the full `vault_writer.py` file after this edit — confirm no syntax error. Confirm every pre-existing function this task did not touch (`replace_body_section`, `create_thread_note_baseline`, `insert_frontmatter_key_if_missing`, the full OKF-directory family) is byte-for-byte unchanged.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Header-scoped append primitive grows an EXISTING header's own region correctly, in call order, leaving every other section untouched.
- [x] Header-scoped append primitive CREATES a missing header (unlike `replace_body_section`'s own no-op contract) and grows it correctly on subsequent calls.
- [x] Unconditional frontmatter-key setter both inserts (absent key) and overwrites (present key, including a list value) correctly, touching nothing else.
- [x] `list_customer_projects(customer)` returns `[]` for a customer with no Projects yet, and one accurate `{project, slug, status}` entry per real Project directory otherwise — reading real frontmatter, never fabricating a default.
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Actually calling any of these three primitives from a real Job — `T03`/`T04`/`T05` wire them into `Thread-Match/Merge`/`Route-to-Project`/`Summarize-Attachment`.
- Any business-logic judgement about which Projects count as "currently open" — `list_customer_projects` returns every Project with its raw `status`; filtering to "open" ones is `T04`'s own job.
- Renaming/generalizing `append_person_note_update_line` — left exactly as `REQ-SB-54-US-01-T02` shipped it; this task adds a NEW, header-scoped sibling rather than modifying it.

---

## Context / Notes

Full reasoning: `Implementation/Architecture/ADR.md` → `ADR-043` Consequences (both new primitives named explicitly as "mechanical extensions of already-shipped shapes, no new mechanism family"); `Implementation/Architecture/architecture.md` → "Email Capture & Threading Pipeline — First Concrete Pipeline". Real precedent to mirror: `replace_body_section` (header/next-header location logic), `insert_frontmatter_key_if_missing`/`rename_frontmatter_key` (surgical single-key frontmatter edits), `list_known_customers`/`list_notes_in_kind_folder` (dynamic, vault-derived enumeration, never hardcoded, `[]` for a not-yet-created folder).

**Why this needs its own task, not folded into `T03`:** `T04`/`T05` also depend on primitives this task adds (the Projects enumeration; the header-scoped append for `## Attachments`), and `T03`/`T04`/`T05` can be built in parallel once this one foundational task lands — matching this codebase's own established "generic-primitive-first, kind-specific-wrapper-second" precedent (`MEMORY.md`, `SPRINT-048`).

---

## Implementation Log

**2026-08-16, coder pass.**

**Scope-internal judgement call, logged for human spot-check (not an
escalation — no ADR/PRD/`MEMORY.md` constraint contradicted):** primitive
#2 (the unconditional frontmatter-key setter) already existed in
`vault_writer.py` before this task, under the name `upsert_frontmatter_key(path,
key, value)` — added by `REQ-SB-09-US-01-T01` (`SPRINT-028`, `MEMORY.md`'s own
[2026-08-13] entry) for Task's `due`/`status` top-up fields. Read directly
(lines ~1678-1697 pre-edit): inserts if the key is absent (delegates to
`insert_frontmatter_key_if_missing`), overwrites in place via
`rename_frontmatter_key(path, key, key, new_value=value)` if present and the
value differs, and no-ops (returns `False`, no write) if present with an
identical value. It is fully generic over `key`/`value` (no `due`/`status`
hardcoding in the function body itself — MEMORY.md's own "due/status only"
phrasing describes its only CALLERS so far, not an enforced restriction),
and it already handles list values identically to scalars (via
`_format_frontmatter_value`, reused inside `rename_frontmatter_key`) — this
is exactly the shape this task's own Objective/Constraints describe for
primitive #2, including the "never touch the body or any OTHER frontmatter
key" surgical-edit discipline (it's built directly from
`insert_frontmatter_key_if_missing`/`rename_frontmatter_key`, the same two
primitives this task's own Constraints name as the mirror to follow).

Writing a second, functionally-duplicate primitive under a new name would
violate this project's own "Minimal changes... no opportunistic
duplication" rule and create two divergent unconditional-setter mechanisms
for future tasks to choose between with no real difference between them.
**Decision: primitive #2 is NOT re-implemented under a new name — `T01`'s
own AC-03 is verified directly against the already-existing
`vault_writer.upsert_frontmatter_key`.** Every later task in this story
(`T03`/`T04`/`T05`) and `REQ-SB-63-US-01-T03` (`SPRINT-050`, which the
sprint's own Notes confirm depends on "`T01`'s own unconditional
frontmatter-key setter" for its cross-cutting tag write) should call
`vault_writer.upsert_frontmatter_key(path, key, value)` for
`participants`/`last_message_at`/tag-union writes — not a new function
this task did not add. `vault_writer.py` was NOT modified for this part
of the task at all — only primitives #1 and #3 below required new code.

**Primitive #1 — `append_body_section_line(path, header, line)`,** added
immediately after `replace_body_section` (same file location the task
specifies). Reuses `replace_body_section`'s own `_BODY_SECTION_HEADER_
PATTERN` (generic next-`##`-header lookup) and the identical literal,
whole-line `re.escape(header)` regex technique for locating the target
header itself — no second, divergent header-finding mechanism. Missing-
header branch creates the header at the end of the file (deliberately the
opposite of `replace_body_section`'s own no-op-if-absent contract, per this
task's own Constraint) containing exactly the one appended line.
Existing-header branch appends `line` as the new last line of that
header's own bounded region (computed the same way `replace_body_section`
bounds its own replace region — up to the next `## `-level header or EOF),
leaving every other section — including one now physically positioned
after this header — untouched.

**Primitive #3 — `list_customer_projects(customer)`,** added immediately
after `ensure_project_directory_baseline` (same file location the task
specifies). Reuses the existing `_project_directory_root(customer)` helper
(`ADR-042` point 4) to resolve the Customer's own `projects/` subtree;
returns `[]` if that directory doesn't exist yet (mirrors
`list_notes_in_kind_folder`'s own not-yet-created-folder contract); for
each real Project subdirectory, reads its own concept file
(`<slug>/<slug>.md`) directly via `read_note` and returns `{"project":
<title>, "slug": <dir-name>, "status": <status>}` verbatim from that
file's own frontmatter (`None` if a field happens to be absent) — no
"currently open" filtering, no fabricated default, per this task's own
Constraint and Out-of-Scope note.

**Manual verification (scratch vault, `VAULT_PATH` env-overridden to a
`tempfile.mkdtemp()` directory, real configured vault never touched —
script + full transcript kept in this session's own scratchpad, not
committed):**

- **Step 1 (`AC` — Header-scoped append grows an EXISTING header, applies
  to this task's own unlocked "grows existing header" criterion, feeds
  forward into the parent story's `REQ-SB-55-US-01-AC-01`/`AC-07`, verified
  for real in `T03`):** created a Thread note via
  `create_thread_note_baseline("test-conv-append", tags=["kind/thread"])`,
  called `append_body_section_line` twice against `"## Transcript"` with
  two distinct lines. Observed: both lines present inside `## Transcript`,
  in call order (`"first message"` before `"second message"`), exactly one
  `## Transcript` header (no duplicate), `## Summary` byte-for-byte
  unchanged (`.strip() == "## Summary"`). PASS.
- **Step 2 (header-scoped append CREATES a missing header, then grows the
  SAME header on a second call — feeds forward into `AC-02`, verified for
  real in `T05`):** called `append_body_section_line` against
  `"## Attachments"` (not yet present) with one line — observed a NEW `##
  Attachments` header created at the end of the file (positioned after
  `## Transcript`), containing exactly that one line, `## Summary`/`##
  Transcript` (including both Step-1 lines) completely unchanged. Called it
  again with a second attachment line — observed both attachment lines now
  under the SAME single `## Attachments` header (exactly one occurrence in
  the file), in call order. PASS.
- **Step 3 (unconditional frontmatter-key setter, verified against the
  pre-existing `upsert_frontmatter_key`, per the judgement call above):** on
  a note with `tags: ["a", "b"]`, called `upsert_frontmatter_key(path,
  "tags", ["a", "b", "c"])` — observed `tags` reads back as exactly `["a",
  "b", "c"]` via `read_note`, `type`/`conversation_id` and the body
  byte-for-byte unchanged. Called it with `key="project",
  value="Some Project"` on a note with no `project` key — observed it
  inserted correctly. Called it a third time on the same `project` key with
  a different value — observed the value overwritten in place (raw file
  text contains exactly one `project:` line, not two). PASS.
- **Step 4 (`list_customer_projects`):** created a Customer directory with
  zero Projects — `list_customer_projects("Acme Corp")` returned `[]`.
  Created two real Project directories (`"Project Alpha"`, `"Project
  Beta"`) — `list_customer_projects("Acme Corp")` returned exactly 2
  entries, each with the correct `project` (title) and `status`
  (`"active"`, the OKF baseline default, read directly from each concept
  file's own frontmatter — not hardcoded in the enumeration function
  itself). PASS.
- **Step 5 (regression):** `ast.parse()` of the full `vault_writer.py`
  file after this edit succeeded with no syntax error. Confirmed via the
  `Edit` tool's own exact-`old_string`-match contract (every edit matched
  and replaced only the intended block) that no pre-existing function body
  was altered; `replace_body_section`/`create_thread_note_baseline`/
  `insert_frontmatter_key_if_missing`/the OKF-directory family/
  `upsert_frontmatter_key` were read but not written to. PASS.

No locked parent-story AC (`REQ-SB-55-US-01-AC-01`..`AC-09`) is verified
directly by this foundational task, per its own `## Tests` note — the
5 manual steps above verify this task's own three (now two-new-plus-one-
reused) primitives' direct correctness only; `T03`/`T04`/`T05` consume them
and carry the real AC-tagged verification.

No `ESCALATIONS.md` entry — nothing here contradicts an `Accepted` ADR, the
PRD, or a `MEMORY.md` constraint; the one judgement call above is a
scope-internal "which existing primitive already satisfies this task's own
described need" reading, not a deviation from `ADR-043`. No new
`REVIEW-QUEUE.md` entry either — the task's already-flagged `gate:
flagged` (trigger-3, `ADR-043`) already carries this task into the
existing human-review pass; the judgement call above is called out inline
in that same standing flag rather than a second, separate queue item.
