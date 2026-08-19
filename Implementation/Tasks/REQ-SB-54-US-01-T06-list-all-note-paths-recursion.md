---
id: REQ-SB-54-US-01-T06
title: list_all_note_paths() two-levels-deep recursion extension for the new OKF directory shape
parent_story: REQ-SB-54-US-01
requirement_id: REQ-SB-54
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-54-US-01-T04, REQ-SB-54-US-01-T05]
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-54-US-01-T06 — `list_all_note_paths()` recursion extension

## Parent Story

- Story: [[REQ-SB-54-US-01]] — `../UserStories/REQ-SB-54-US-01-vault-knowledge-model-redesign.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-54 *Vault Knowledge Model Redesign — Threads, Linked Meetings, Living Project & Customer Documents*

---

## Objective

Extend `vault_writer.list_all_note_paths()` to discover the new two-levels-deep Customer/Project OKF concept files, which its current one-level `Work/*/*.md` glob structurally cannot see — the flagged, explicitly-named consequence in `ADR-042`/`architecture.md`'s own Consequences section: "every OKF concept file is structurally invisible to `list_known_customers()`, `vault_indexing`, and search unless a task explicitly extends that scan."

---

## Starting State → End State

**Before / Inputs:**
- `list_all_note_paths()` (line 139): `sorted(work_root.glob("*/*.md"))` — finds every flat `Work/<kind>/<file>.md` note (Threads, Meetings, People, Partners, Tasks, and any still-existing OLD-shape flat Customer hub notes at `Work/Customers/<slug>.md`), but NOT `Work/Customers/<slug>/<slug>.md` (2 levels deep) or `Work/Customers/<slug>/projects/<slug>/<slug>.md` (4 levels deep).
- Every caller of `list_all_note_paths()` (`list_known_customers`, `list_known_partners`, `retrofit_customer_hub_links`, `migrate_customer_to_partner`'s own scan, `list_notes_matching_scope`, and any future vault-indexing/search consumer) is silently blind to every real Customer/Project concept file created by `T04`/`T05`.

**After / Outputs:**
- `list_all_note_paths()` also returns every Customer/Project concept file (`<slug>.md` at the directory root — NOT `index.md`/`log.md`/`captures.md`, which are OKF-reserved/non-note files, never meant to be treated as ordinary frontmatter notes).
- Every OTHER note kind's discovery (one-level `Work/<kind>/<file>.md`) is completely unaffected — same set, same order, same count as before this task, confirmed by regression test.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — `list_all_note_paths()` (line 139) only.

---

## Constraints

- Inherits from parent story.
- Do NOT generalize to "detect any directory-shaped kind dynamically" — hardcode the literal `Customers/*/*.md` and `Customers/*/projects/*/*.md` glob shapes. This is deliberate, matching `ADR-042`'s own explicit, non-generalized 2-kind scope (its Alternatives Considered reject generalizing the directory shape to every kind as scope creep) — Customer and Project are the ONLY two directory-shaped kinds by design.
- Explicitly EXCLUDE `index.md`, `log.md`, `captures.md` from the returned set by filename — these are OKF-reserved/append-only files with no ordinary `key: value` frontmatter shape; every existing caller expects `read_note(path)`-compatible notes.
- Every existing caller's own contract (a sorted list of `Path` objects) must be preserved exactly — do not change the return type.
- Do not touch `list_known_kinds()`, `list_notes_in_kind_folder()`, or any other discovery function — only `list_all_note_paths()` itself.

---

## Tests

**Manual verification steps:**
1. Using the real Customer (`Acme Test Co`) and Project (`Data Lake Migration`) directories created by `T04`'s/`T05`'s own test runs, call `list_all_note_paths()`. Confirm the returned list includes `Work/Customers/acme-test-co/acme-test-co.md` and `Work/Customers/acme-test-co/projects/data-lake-migration/data-lake-migration.md`. Confirm it explicitly does NOT include either directory's own `index.md`, `log.md`, or `captures.md`.
2. **Regression:** capture the real vault's `list_all_note_paths()` output (count + full path set) BEFORE this task's own edit is applied (or reconstruct it from the one-level glob alone), then compare AFTER — confirm every previously-discovered flat note (Threads, Meetings, People, Partners, Tasks, and any OLD-shape flat Customer hub notes) is still present, same count, nothing dropped or duplicated.
3. Call `list_known_customers()` (downstream consumer) after this task's change — confirm its own output is unaffected by the new concept files specifically (they carry no plain `customer:` frontmatter key per `T04`'s schema, so they contribute nothing new to this particular scan) — an honest, disclosed non-effect, not a regression.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `list_all_note_paths()` discovers every Customer/Project concept file (`<slug>.md`), never `index.md`/`log.md`/`captures.md`.
- [x] Every previously-discoverable flat note kind is unaffected (same set/count/order as before).
- [x] No other discovery function (`list_known_kinds`, `list_notes_in_kind_folder`) is modified.
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint. (Consolidated story-level entry added — this task closes `REQ-SB-54-US-01`, see Implementation Log.)
- [x] `CHANGELOG.md` entry appended.

---

## Out of Scope

- Any change to `vault_indexing`/`vault_search.py` themselves (not yet built against this new shape — future work once a story actually wires search/browse to consume it).
- Generalizing recursion to any note kind beyond Customer/Project.
- The disclosed, low-probability edge case where a customer/project's own slug literally equals `index`/`log`/`captures` (an OKF-convention-inherent ambiguity, not fixed here — see story `## Notes`).

---

## Context / Notes

No locked AC in this story directly names `list_all_note_paths()` (Scenario 3/5 assert directory contents via filesystem inspection, not via this specific function) — this task exists because `architecture.md`'s own Consequences section explicitly names it as "a real, load-bearing consequence the decomposer must turn into an explicit task under T04/T05, not an incidental side effect." Verification above is task-level, not AC-tagged.

Full reasoning: `Implementation/Architecture/architecture.md` → "Vault Knowledge Model Redesign..." § "Flagged consequence, not yet resolved by this pass."

Illustrative implementation shape (verify against the real current file — including `T04`'s/`T05`'s own final directory-shape details — before writing):

```python
_OKF_RESERVED_FILENAMES = {"index.md", "log.md", "captures.md"}

def list_all_note_paths() -> list:
    work_root = settings.vault_path / _WORK_ROOT
    if not work_root.exists():
        return []
    flat_notes = set(work_root.glob("*/*.md"))
    # Customer/Project are the only two note kinds with a directory shape
    # (ADR-042) -- deliberately not generalized to every kind (ADR-042
    # Alternatives: "rejected as scope creep").
    okf_concept_files = (
        set(work_root.glob("Customers/*/*.md"))
        | set(work_root.glob("Customers/*/projects/*/*.md"))
    )
    okf_concept_files = {p for p in okf_concept_files if p.name not in _OKF_RESERVED_FILENAMES}
    return sorted(flat_notes | okf_concept_files)
```

---

## Implementation Log

**What was built:**

- `src/backend/app/data_access/vault_writer.py::list_all_note_paths()` — extended, matching the task's own illustrative shape verbatim (field-for-field, function-for-function): a new module-level `_OKF_RESERVED_FILENAMES = {"index.md", "log.md", "captures.md"}` constant, and the function body now unions the existing one-level `work_root.glob("*/*.md")` (flat note kinds, unchanged) with two new hardcoded, two-levels-deep globs — `work_root.glob("Customers/*/*.md")` (Customer concept files) and `work_root.glob("Customers/*/projects/*/*.md")` (Project concept files) — filtered to exclude any path whose filename is in `_OKF_RESERVED_FILENAMES`, then returns the sorted union. No other function in the file was touched; `list_known_kinds()` and `list_notes_in_kind_folder()` are byte-for-byte unchanged (confirmed via `git diff`).

**No new decision/pattern/constraint from this task's own code alone** — it is a direct, literal implementation of the task's own illustrative shape, already fully reasoned about in `ADR-042`/`architecture.md`'s Consequences section and the story's own decomposer notes (hardcoded 2-kind scope, deliberately not generalized). A consolidated story-level `MEMORY.md` entry was added instead (below), since this task closes out `REQ-SB-54-US-01` end-to-end — see `MEMORY.md` → `[2026-08-16] REQ-SB-54-US-01`.

**Verification (manual mode, real backend venv `src/backend/.venv`, scratch vault dir under the session scratchpad, VAULT_PATH env-overridden — the real configured vault was never touched):**

A throwaway scratch vault was seeded with one flat note per previously-discoverable kind (Threads, Meetings, People, Partners, Tasks) plus one OLD-shape flat Customer hub note (`Work/Customers/old-flat-customer.md`, carrying a plain `customer:` frontmatter key) — 6 paths total, matching the one-level glob exactly (baseline `list_all_note_paths() == sorted(work_root.glob("*/*.md"))`, confirmed set- and count-equal before any OKF directory existed). Then `T04`'s `create_customer_directory_baseline("Acme Test Co")` and `T05`'s `create_project_directory_baseline("Acme Test Co", "Data Lake Migration")` were called for real, producing real 4-file OKF directories.

- **Test step 1** — `list_all_note_paths()` after the OKF directories existed returned 8 paths: the original 6 flat notes, PLUS `Work/Customers/Acme Test Co/Acme Test Co.md` (Customer concept file) and `Work/Customers/Acme Test Co/projects/Data Lake Migration/Data Lake Migration.md` (Project concept file, 4 levels deep). Directly confirmed both concept-file paths (from `customer_directory_paths(...)["concept"]`/`project_directory_paths(...)["concept"]`) were present in the result, and that none of `index.md`/`log.md`/`captures.md` for EITHER directory were present. **PASS.**
- **Test step 2 (regression)** — the pre-OKF baseline set (6 flat paths) was a strict subset of the post-OKF result set (all 6 still present, none dropped), the post-OKF result had exactly `6 + 2 = 8` paths (no duplicates — confirmed `len(result) == len(set(result))`), and every previously-discoverable flat note kind (Threads/Meetings/People/Partners/Tasks/OLD-shape flat Customer) was represented identically before and after. **PASS.**
- **Test step 3** — `list_known_customers()` called after the change returned exactly `["Old Flat Customer"]` — the two new OKF concept files contributed nothing (confirmed: `"Acme Test Co"` did NOT appear), because their frontmatter schema (`T04`'s `build_customer_concept_frontmatter`/`build_project_concept_frontmatter`) has no plain `customer:` key, exactly as the task's own Tests section predicted — an honest, disclosed non-effect, not a regression. **PASS.**

Full backend `pytest -q` (`src/backend`, real `VAULT_PATH`) re-run after the change: 1 passed, no regressions. `git diff`/read confirmed only `src/backend/app/data_access/vault_writer.py` was touched, and only inside `list_all_note_paths()` plus the one new module-level constant — no other function, no out-of-scope file.

No locked story AC is directly tagged to this task (per the task's own `## Context / Notes` — Scenario 3/5 assert directory contents via filesystem inspection, not via this function); the verification above is the task-level check `architecture.md`'s own Consequences section required.

No deviations from the task's own illustrative implementation shape. No new escalation, no new REVIEW-QUEUE item from this task's own work.
