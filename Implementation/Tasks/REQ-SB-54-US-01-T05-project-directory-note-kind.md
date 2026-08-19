---
id: REQ-SB-54-US-01-T05
title: Project directory-shaped note kind — reuses T04's generic OKF directory family
parent_story: REQ-SB-54-US-01
requirement_id: REQ-SB-54
type: backend
status: Done
gate: flagged
gate_reason: "Coder-logged scope-internal assumption on a small private path-resolution helper — see Implementation Log for human spot-check."
phase: P1
depends_on: [REQ-SB-54-US-01-T04]
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-54-US-01-T05 — Project directory-shaped note kind

## Parent Story

- Story: [[REQ-SB-54-US-01]] — `../UserStories/REQ-SB-54-US-01-vault-knowledge-model-redesign.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-54 *Vault Knowledge Model Redesign — Threads, Linked Meetings, Living Project & Customer Documents*

---

## Objective

Add the Project directory-shaped note kind, nested one level inside its own Customer's directory (`Work/Customers/<customer-slug>/projects/<project-slug>/`, `ADR-042` point 4 — operator-confirmed 2026-08-16, "Yes, Project gets the same directory shape as Customer"), reusing `T04`'s generic `okf_directory_paths`/`create_okf_directory_baseline`/`ensure_okf_directory_baseline` family unchanged — zero duplicated 4-file-creation logic.

---

## Starting State → End State

**Before / Inputs:**
- `T04`'s generic OKF directory family and `customer_directory_paths(customer)` exist.
- No Project note kind exists anywhere in the codebase — this is the first.

**After / Outputs:**
- `project_directory_paths(customer, project)`, `project_concept_file_exists(customer, project)`, `build_project_concept_frontmatter(customer, project)`, `create_project_directory_baseline(customer, project)`, `ensure_project_directory_baseline(customer, project)` exist in `vault_writer.py`, mirroring Customer's own wrapper shape exactly, all delegating to `T04`'s generic family.
- A Project's directory sits at `Work/Customers/<customer-slug>/projects/<project-slug>/`, containing the identical 4-file shape (`index.md`/`<project-slug>.md`/`log.md`/`captures.md`) as a Customer directory.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — add `project_directory_paths`, `project_concept_file_exists`, `build_project_concept_frontmatter`, `create_project_directory_baseline`, `ensure_project_directory_baseline`, placed immediately after the Customer wrappers `T04` adds.

---

## Constraints

- Inherits from parent story.
- Reuse `okf_directory_paths`/`create_okf_directory_baseline`/`ensure_okf_directory_baseline`/`format_okf_provenance` from `T04` UNCHANGED — do not duplicate the 4-file creation logic, do not write a second, parallel implementation (`ADR-042` point 1's explicit "one shared mechanism" requirement).
- Project's own `directory_root` for a given customer is `customer_directory_paths(customer)["directory"] / "projects"` — computed via `T04`'s own function, never a separately-hardcoded path string.
- No new business-layer orchestration module (no `project_hub_linking.py`) — no real caller in this codebase classifies content into Projects yet (that's future work, likely `REQ-SB-57`/a later story); this task builds the data_access-layer primitives only, matching this story's own "data shape, not pipeline" scope.
- `vault_writer.py` stays pure I/O (`ADR-003`).

---

## Tests

**Manual verification steps:**
1. [REQ-SB-54-US-01-AC-05] Using the same throwaway `"Acme Test Co"` customer from `T04`'s own test run (or a freshly created one), call `project_concept_file_exists("Acme Test Co", "Data Lake Migration")` — expect `False`. Call `create_project_directory_baseline("Acme Test Co", "Data Lake Migration")`. Confirm the resulting directory sits at `Work/Customers/acme-test-co/projects/data-lake-migration/`, containing all 4 files (`index.md`, `data-lake-migration.md`, `log.md`, `captures.md`) — identical shape to `T04`'s own verified Customer directory (frontmatter carries at minimum `type: "project"`, `title`, `description`, `tags`, `status`, `stale_after`, `generated`, `verified`, `sources`; body has exactly two `##` sections, `## Glimpse` and `## Background`).
2. [REQ-SB-54-US-01-AC-02] Mirror `T04`'s Manual Captures test for Project: append a line directly to `data-lake-migration/captures.md`. Call `replace_body_section` (`T01`) against `data-lake-migration.md`'s `## Glimpse` section with new content. Confirm `captures.md` (including the manual line) is byte-for-byte unchanged; confirm `## Glimpse` shows only the new content, `## Background` and frontmatter untouched.
3. Call `ensure_project_directory_baseline("Acme Test Co", "Data Lake Migration")` on the SAME project — confirm it's a true top-up (no already-set frontmatter value or body content changes).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Project's directory shape is byte-for-byte identical in structure to Customer's (same 4 filenames, same concept-file body-section shape).
- [x] Zero duplicated 4-file-creation logic — Project's wrappers delegate to `T04`'s generic family.
- [x] Project nests correctly at `Work/Customers/<customer-slug>/projects/<project-slug>/`.
- [x] `captures.md` is structurally unreachable from `<project-slug>.md` regeneration, same as Customer.
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint. (N/A — no new decision/pattern/constraint; pure reuse of `T04`'s already-recorded mechanism, see Implementation Log.)
- [x] `CHANGELOG.md` entry appended.

---

## Out of Scope

- Any real caller that creates/updates Projects from actual captured content — future work, not this story.
- `list_all_note_paths()`'s discovery gap — `T06`.

---

## Context / Notes

Full reasoning: `Implementation/Architecture/ADR.md` → `ADR-042` point 4; `Implementation/Architecture/architecture.md` → "Vault Knowledge Model Redesign..." § Synthesis layer.

Illustrative implementation shape (verify against the real current file — including `T04`'s own final function names/signatures — before writing):

```python
def project_directory_paths(customer: str, project: str) -> dict:
    projects_root = customer_directory_paths(customer)["directory"] / "projects"
    return okf_directory_paths(projects_root, project)

def project_concept_file_exists(customer: str, project: str) -> bool:
    return project_directory_paths(customer, project)["concept"].exists()

def build_project_concept_frontmatter(customer: str, project: str) -> dict:
    return {
        "type": "project",
        "title": project,
        "description": "",
        "tags": [f"customer/{tag_slug(customer)}", "kind/project"],
        "status": "active",
        "stale_after": "",
        "generated": format_okf_provenance(by="", at=""),
        "verified": format_okf_provenance(by="", at=""),
        "sources": [],
    }

def create_project_directory_baseline(customer: str, project: str) -> dict:
    projects_root = customer_directory_paths(customer)["directory"] / "projects"
    return create_okf_directory_baseline(
        projects_root, project, build_project_concept_frontmatter(customer, project),
        index_listing_body=f"# {project}\n\n- [[{_slugify(project)}]]\n",
    )

def ensure_project_directory_baseline(customer: str, project: str) -> list[str]:
    projects_root = customer_directory_paths(customer)["directory"] / "projects"
    return ensure_okf_directory_baseline(
        projects_root, project, build_project_concept_frontmatter(customer, project),
        index_listing_body=f"# {project}\n\n- [[{_slugify(project)}]]\n",
    )
```

---

## Implementation Log

**What was built:**

- `src/backend/app/data_access/vault_writer.py` — added, immediately after `T04`'s Customer wrappers (`ensure_customer_directory_baseline`) and immediately before `list_known_customers`: a small private `_project_directory_root(customer)` helper returning `customer_directory_paths(customer)["directory"] / "projects"` (the Constraints-mandated computation, factored into one place instead of repeated inline in each of the four functions below — see logged assumption); `project_directory_paths(customer, project)`, `project_concept_file_exists(customer, project)`, `build_project_concept_frontmatter(customer, project)`, `create_project_directory_baseline(customer, project)`, `ensure_project_directory_baseline(customer, project)`. All five delegate to `T04`'s generic `okf_directory_paths`/`okf_concept_file_exists`/`create_okf_directory_baseline`/`ensure_okf_directory_baseline`/`format_okf_provenance` — zero duplicated 4-file-creation logic, matching the task's own illustrative shape field-for-field (only `tags` differs from Customer's own frontmatter: `[f"customer/{tag_slug(customer)}", "kind/project"]`, so a Project stays findable both by its own kind and by its parent Customer).

**Assumption logged for human spot-check (scope-internal, not an escalation):** the task's own illustrative implementation code repeats `customer_directory_paths(customer)["directory"] / "projects"` inline inside each of the four customer/project-taking functions. I instead factored that one-line computation into a private `_project_directory_root(customer)` helper called by all four, to avoid the same three-line duplication existing four times in one file — a minor DRY-style judgement call, not a behavior change: it still computes the identical value via `T04`'s own `customer_directory_paths` function on every call (never a separately-hardcoded path string, per the task's own Constraints), and every one of the five public function names/signatures listed in `## Files to Modify` is unchanged from the illustrative shape. Flagging in case the illustrative inline-repetition shape was actually intended verbatim.

**Note (inherited from `T04`, not re-flagged as a new item):** `T04`'s own `REVIEW-QUEUE.md` entry already covers directory/concept-file slug casing (`vault_writer._slugify` strips only filesystem-invalid characters — no lowercasing/hyphenation of spaces, unlike `tag_slug`) and explicitly states `T05`/`T06` are unaffected either way. Confirmed still true here: for `"Acme Test Co"`/`"Data Lake Migration"`, the live directory is `Work/Customers/Acme Test Co/projects/Data Lake Migration/` (spaces preserved), not `Work/Customers/acme-test-co/projects/data-lake-migration/` as the Tests section's own prose illustrates — same precedent, same no-locked-AC-names-exact-casing reasoning, no new REVIEW-QUEUE item needed.

**Verification (manual mode, real backend venv `src/backend/.venv`, scratch vault dir under the session scratchpad, customer `"Acme Test Co"`, project `"Data Lake Migration"`):**

- **[REQ-SB-54-US-01-AC-05]** `project_concept_file_exists("Acme Test Co", "Data Lake Migration")` returned `False` before creation (after first creating the Customer directory baseline via `T04`'s own `create_customer_directory_baseline`, its own real dependency). `create_project_directory_baseline("Acme Test Co", "Data Lake Migration")` created the directory at `Work/Customers/Acme Test Co/projects/Data Lake Migration/` (nested one level inside the Customer's own resolved directory, confirmed via `customer_directory_paths(...)["directory"] / "projects"`), containing all 4 files (`index.md`, `Data Lake Migration.md`, `log.md`, `captures.md`) — identical shape to `T04`'s own verified Customer directory. The concept file's frontmatter contained all of `type` (`"project"`), `title`, `description`, `tags`, `status`, `stale_after`, `generated`, `verified`, `sources`; its body contained exactly two `##` sections, `## Glimpse` and `## Background`, in that order. `project_concept_file_exists` returned `True` after creation. Cross-checked structurally: `project_directory_paths(...)` and `customer_directory_paths(...)` return the identical key set (`directory`/`index`/`concept`/`log`/`captures`). **PASS.**
- **[REQ-SB-54-US-01-AC-02]** Appended `"manual capture line 1"` directly to `Data Lake Migration/captures.md`. Called `replace_body_section` (`T01`) against `Data Lake Migration.md`'s `## Glimpse` section with new content. Read `captures.md` back — byte-for-byte unchanged, including the manually-appended line. Read the concept file back — `## Glimpse` showed only the new content, `## Background` and the frontmatter block were untouched (dict-equal to before). **PASS.**
- Called `ensure_project_directory_baseline("Acme Test Co", "Data Lake Migration")` on the same, already-existing project — returned `[]` (no keys inserted, every baseline key already present); confirmed byte-for-byte that the concept file, `log.md`, and `captures.md` were all unchanged by the call (true idempotent top-up, no already-set frontmatter value or body content changed). **PASS.**

All 3 Test steps verified live (script run twice — first against the Tests section's own literal lowercase-hyphenated prose example, which failed for the reason already covered by `T04`'s inherited, non-blocking casing note above; re-run and passed against the actual live directory naming). `git diff`/read confirmed only `src/backend/app/data_access/vault_writer.py` was touched, and only by insertion (no existing line changed) — no out-of-scope file touched. Full backend test suite (`pytest -q`, `src/backend`) re-run after the change: 1 passed, no regressions.
