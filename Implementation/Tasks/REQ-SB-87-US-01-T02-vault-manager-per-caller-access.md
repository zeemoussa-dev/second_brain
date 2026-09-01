---
id: REQ-SB-87-US-01-T02
title: vault_manager.py — Template.json-declared per-caller section-write access
parent_story: REQ-SB-87-US-01
requirement_id: REQ-SB-87
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-87-US-01-T01]
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-01-T02 — vault_manager.py: Template.json-Declared Per-Caller Section-Write Access

## Parent Story

- Story: [[REQ-SB-87-US-01]] — `../UserStories/REQ-SB-87-US-01-vault-manager-resync-and-thread-templates.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

Give `vault_manager.py`'s section-access model real per-caller granularity —
a section's `Template.json` declaration gains an optional
`allowed_callers` list, and `create()`/`modify_section()` gain a
caller-identity argument that is checked against it — per `ADR-017`'s
Decision.

---

## Starting State → End State

**Before / Inputs:**
- `_section_access()`/`_require_machine_write()` (confirmed directly,
  `vault_manager.py`) implement only a BINARY `machine_write`/anything-else
  flag per section — no notion of WHICH caller may write a `machine_write`
  section.
- `create()` and `modify_section()` accept no caller-identity argument at
  all today.

**After / Outputs:**
- A section entry in `template["root"]["sections"]` gains an optional
  `"allowed_callers": [str, ...]` list, alongside its existing `"access"`
  key.
- `create()` and `modify_section()` gain a new optional parameter (e.g.
  `caller: str | None = None`) — CLI gains a matching `--caller` argument.
- `_require_machine_write(template, section, caller)` (extended signature):
  after the existing `machine_write` check, if the section's own
  `allowed_callers` is present and non-empty, additionally require
  `caller in allowed_callers` — raise `VaultManagerError` (same style as
  today's existing "no automated write is allowed here" message, naming the
  refusing section + the caller that was refused) if not.
- **A section with no `allowed_callers` key stays open to any caller
  carrying `machine_write` access — zero behavior change for every
  already-`Done` template** (Customer, Partner, Opportunity, Meeting,
  meeting-series, Note, File, azure-kb-doc, compass-kb-doc,
  research-kb-doc) — this is the specific guarantee `T06`'s own regression
  pass confirms.
- Every mutating CALL SITE inside `vault_manager.py` itself (`create()`'s
  own internal section-write loop, `modify_section()`) is updated to thread
  the `caller` argument through to `_require_machine_write`. Retrofitting
  the EXISTING callers of `create`/`modify_section` in already-deployed
  Skills (`meeting-capture`, `create-companies-partners`) to actually PASS
  their own caller identity is `T04`'s own scope, not this task's.

---

## Files to Modify

- `Hermes-Provisioning/shared/vault_manager.py`.
- `Hermes-Provisioning/shared/tests/test_vault_manager.py` (new automated
  test coverage).

---

## Constraints

- Inherits from parent story.
- **`allowed_callers` is `Template.json` data, not hardcoded Python** —
  `ADR-017`'s own explicitly rejected alternative (a hardcoded per-Skill
  exception dict inside `vault_manager.py`) must not be reintroduced.
- Backward-compatible signature: `caller` defaults to `None`/omittable so
  every existing call site (until `T04` retrofits it) keeps working exactly
  as before against any template with no `allowed_callers` declared
  anywhere.
- The refusal error must be a real, explicit `VaultManagerError` — never a
  silent no-op, never a swallowed write.

---

## Tests

Extends `Hermes-Provisioning/shared/tests/test_vault_manager.py`:

```
src\backend\.venv\Scripts\python.exe -m pytest Hermes-Provisioning\shared\tests\test_vault_manager.py -v
```

**Automated tests (new):**
1. (Unlabeled, infra — supports `REQ-SB-87-US-01-AC-02`, whose own
   real-Thread-template proof is `T05`'s) Using a scratch `Template.json`
   fixture whose `Summary` section declares `"allowed_callers":
   ["writer_a"]`, call `modify_section(..., caller="writer_a")`; assert it
   succeeds. Call the SAME write with `caller="writer_b"`; assert a
   `VaultManagerError` is raised naming the section and the refused caller.
2. (Unlabeled, infra) Using a section with NO `allowed_callers` key
   declared, call `modify_section()` with `caller=None` and again with an
   arbitrary `caller="anything"`; assert BOTH succeed — undeclared stays
   open to any `machine_write` caller.
3. (Unlabeled, regression) Run the full existing `test_vault_manager.py`
   suite (including `T01`'s new tests); confirm every test still passes.

**Manual verification steps:** none required.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] A section's `Template.json` declaration accepts an optional
      `allowed_callers: [str, ...]` list
- [x] `create()`/`modify_section()` accept a `caller` argument and refuse a
      write when `caller` is not on the section's own `allowed_callers`
      (when declared)
- [x] A section with no `allowed_callers` declared stays open to any
      `machine_write` caller — zero behavior change
- [x] CLI exposes `--caller`
- [x] Every pre-existing test still passes
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Declaring the Thread template's own real `allowed_callers` values (`##
  Related` → `link_person_to_thread`, etc.) — `T05`.
- Retrofitting `meeting-capture`/`create-companies-partners`'s own real call
  sites to pass their caller identity — `T04`.
- `## Actions`' own `mode=replace` write-mode decision — a `modify_section`
  caller-supplied `mode` argument already exists today (`replace`/
  `append`); no new engine capability is needed for that decision, it is
  purely a caller-side choice `US-05`'s own task makes.

---

## Context / Notes

`ADR-017` (`Implementation/Architecture/ADR.md`) — read the full Decision
and "Alternatives Considered" (the rejected hardcoded-Python-dict option)
before implementing.

---

## Implementation Log

**What was built** (`Hermes-Provisioning/shared/vault_manager.py`, the
canonical source only):
- New `_section_allowed_callers(template, section)` helper — reads a
  section's optional `allowed_callers` list from `root.sections`, `None`
  when absent/empty (open to any `machine_write` caller).
- `_require_machine_write(template, section, caller=None)` (extended
  signature): after the existing binary `machine_write` check, if
  `allowed_callers` is declared and non-empty, additionally requires
  `caller in allowed_callers` — raises `VaultManagerError` naming both
  the refusing section and the refused caller otherwise.
- `create(...)` and `modify_section(...)` both gain an optional
  `caller: str | None = None` parameter, threaded to
  `_require_machine_write` at their own two existing call sites:
  `create()`'s `on_existing_title="update_section"` early-return
  section-write loop, and `modify_section()`'s own update-path write.
  (`create()`'s OTHER section-write loop — the initial-content loop at
  root-creation time — has never called `_require_machine_write` at
  all, pre-existing behavior this task did not change or expand.)
- CLI gained `--caller`, threaded into the `create` and `modify-section`
  commands.
- Module docstring updated (the `sections` shape description, plus a new
  paragraph after the dynamic-children documentation) to describe
  `allowed_callers` and the new `caller` parameter/`--caller` flag.
- `Hermes-Provisioning/shared/tests/test_vault_manager.py`: 2 new tests
  added (`_write_caller_access_template` fixture + allowed/disallowed
  caller coverage, undeclared-`allowed_callers` stays-open coverage).

**Scope-internal judgement call** (logged for human spot-check): the
nested `create(...)` call `modify_section()` makes on its own
create-if-missing path (when the target note doesn't exist yet) is NOT
threaded with `caller` — it writes through the OTHER, unchecked
section-write loop noted above, which this task's own End-State names
as out of scope ("create()'s own internal section-write loop" refers
specifically to the `update_section` early-return path, the only one
that already called `_require_machine_write` before this task). No
locked AC required changing that loop's own gating; flagged here rather
than silently expanding scope.

**Verification (automated,
`Hermes-Provisioning/shared/tests/test_vault_manager.py`):**
- (Unlabeled, infra — supports `REQ-SB-87-US-01-AC-02`, `T05`'s own
  real-Thread-template proof) PASS —
  `test_modify_section_allowed_caller_succeeds_disallowed_caller_refused`:
  a `Summary` section declaring `allowed_callers: ["writer_a"]` accepted
  `caller="writer_a"`'s write; the same write with `caller="writer_b"`
  raised `VaultManagerError` naming both `Summary` and `writer_b`; the
  section's content after the refused call was confirmed unchanged
  (`writer_a`'s content only — the refused write never landed even
  partially).
- (Unlabeled, infra) PASS —
  `test_undeclared_allowed_callers_stays_open_to_any_caller`: a section
  with no `allowed_callers` key accepted both `caller=None` and
  `caller="anything"`.
- (Unlabeled, regression) PASS — full `test_vault_manager.py` suite:
  **52/52 passed** (50 pre-existing + 2 new), run via
  `src\backend\.venv\Scripts\python.exe -m pytest
  Hermes-Provisioning\shared\tests\test_vault_manager.py -v`. Zero
  pre-existing test needed modification.

**Additional live verification (real scratch-vault CLI session, per the
operator's own explicit instruction)** — a throwaway `thread-scratch`
template (own_folder root, sections mirroring the real Thread shape:
`## Related` → `["link_person_to_thread"]`, `## Files` →
`["capture_attachments", "capture_file_link"]`, `## Summary` →
`["apply_thread_review"]`, `## Personal Notes` → `"access":
"human_only"`; plus a fixed `log` child, a T01 dynamic `messages`
child, and an optional auto-creating `parent` to Customers), under a
scratch vault at `<session scratchpad>/scratch-vault-t02`, driven via
the real `vault_manager.py` CLI, not pytest:
1. Created the root Thread note (`parent_value: "Acme Corp"`,
   `on_missing: "auto_create"`) — root created, fixed `log` sibling
   written atomically, Customer parent auto-created with a correct
   `## Threads` link-back — the existing `parent`/fixed-children
   mechanisms fired unchanged alongside the new caller-access code.
2. `link_person_to_thread` wrote `## Related` — succeeded.
   `capture_attachments` then tried to write `## Related` — refused,
   real error naming `Related` and `capture_attachments`.
3. `capture_attachments` wrote `## Files` — succeeded.
   `link_person_to_thread` then tried to write `## Files` — refused,
   real error naming `Files` and `link_person_to_thread`.
4. `apply_thread_review` wrote `## Summary` — succeeded.
5. `apply_thread_review` (a real, otherwise-valid machine caller) tried
   to write `## Personal Notes` — refused with the existing
   `human_only` error (unaffected by `allowed_callers`, confirms the
   two guards compose correctly).
6. Read the real note file on disk directly: `## Related` held only
   `[[Jane Doe]]` (the allowed write), `## Files` held only
   `[[attachment1.pdf]]`, `## Summary` held only the allowed caller's
   sentence, `## Personal Notes` stayed empty — every refused write's
   own content confirmed never landed, not even partially.
7. Composition with `T01`'s dynamic-child primitive on the SAME root:
   `create-child` for `messages` (msg-1) created a real file; the exact
   same identity called again returned `created: false` with the same
   path (idempotent); a genuinely new identity (msg-2) created a second
   real file — the caller-access change made zero difference to this
   primitive's own behavior.
8. Zero-regression check on a plain template declaring NO
   `allowed_callers` anywhere, with `--caller` omitted from the CLI
   entirely: `create` (with initial section content) and
   `modify-section` both succeeded exactly as before this task.

Scratch vault deleted after verification (not a repo artefact). No file
outside `## Files to Modify` was touched.

**No `ESCALATIONS.md` / `REVIEW-QUEUE.md` entries written by this
task** — no new dependency, no shared-interface change beyond what
`ADR-017` already governs, no ADR deviation, no unanticipated file, and
every locked AC verified with a real positive result. `gate: clear`.

gate: clear 2026-09-01 — no triggers fired (ADR-017 already governs this
task's own scope; the one scope-internal judgement call above is
non-blocking and logged for spot-check, not an assumption filling a
requirement gap; no ESCALATIONS entry; task not oversized; both the
automated suite and the real scratch-vault CLI session verified this
task's locked ACs live).
