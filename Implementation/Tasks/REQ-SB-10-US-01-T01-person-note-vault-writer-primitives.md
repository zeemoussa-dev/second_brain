---
id: REQ-SB-10-US-01-T01
title: Add person-note file-I/O primitives to vault_writer.py; promote _tag_slug to public tag_slug
parent_story: REQ-SB-10-US-01
requirement_id: REQ-SB-10
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-10-US-01-T01 — Add person-note file-I/O primitives to vault_writer.py; promote _tag_slug to public tag_slug

## Parent Story

- Story: [[REQ-SB-10-US-01]] — `../UserStories/REQ-SB-10-US-01-people-notes-from-email-capture.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-10 *People Living Documents*

---

## Objective

Add the low-level file-I/O primitives `app/business/people_extraction.py`
(T02) will orchestrate on top of: resolving/checking a Person note's path
(keyed by the sender's lowercased-then-slugified email address), building the
People schema's separate `company/`-namespace tags, creating a Person note's
baseline for the first time, and topping up missing baseline frontmatter keys
on an existing Person note without touching the rest of the file. Also
promotes the existing private `_tag_slug` helper to a public `tag_slug`
function so T02's business-layer company-to-known-customer matching has one
shared, public normalization function instead of duplicating slug logic
outside `data_access` (per `architecture.md`'s "Person Notes & Email-Sender
Extraction" section).

---

## Starting State → End State

**Before / Inputs:**
- `vault_writer.py` already has `write_note`, `build_tags`, `read_note`,
  `insert_frontmatter_key_if_missing`, `insert_body_line_if_missing` (the
  REQ-SB-14 hub-note primitives this task mirrors for People), and a private
  `_tag_slug` helper used only inside `build_tags`.

**After / Outputs:**
- `_tag_slug` renamed to public `tag_slug` (pure rename, no behavior change;
  `build_tags`'s two call sites updated).
- Five new items appended to `vault_writer.py`: `_PEOPLE_SUBFOLDER`,
  `_PERSON_NOTE_BASELINE_KEYS`, `person_note_path`, `person_note_exists`,
  `build_person_tags`, `create_person_note_baseline`,
  `ensure_person_note_baseline_frontmatter` — no existing function's
  behavior changed beyond the `_tag_slug`→`tag_slug` rename.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py`:

  1. Rename `_tag_slug` to `tag_slug` and update `build_tags`'s two call
     sites. Replace this exact block:

     ```python
     def _tag_slug(text: str) -> str:
         """Obsidian tags can't contain spaces — lowercase, non-alphanumeric runs
         collapsed to a single hyphen, e.g. 'Department of Government Enablement'
         -> 'department-of-government-enablement'."""
         slug = _TAG_INVALID_CHARS.sub("-", text.lower()).strip("-")
         return slug or "untitled"


     def build_tags(customer: str, kind: str) -> list[str]:
         """Hierarchical Obsidian tags mirroring the folder structure, so notes
         stay findable by customer/kind via search/graph view independent of
         where they physically live — the point raised when a note sits in
         Unsorted/ but you already suspect which customer it's really for."""
         return [f"customer/{_tag_slug(customer)}", f"kind/{_tag_slug(kind)}"]
     ```

     with:

     ```python
     def tag_slug(text: str) -> str:
         """Obsidian tags can't contain spaces — lowercase, non-alphanumeric runs
         collapsed to a single hyphen, e.g. 'Department of Government Enablement'
         -> 'department-of-government-enablement'. Public (promoted from the
         former _tag_slug — REQ-SB-10 — so business-layer code has one shared
         normalization function instead of duplicating slug logic outside
         data_access; pure rename, no behavior change)."""
         slug = _TAG_INVALID_CHARS.sub("-", text.lower()).strip("-")
         return slug or "untitled"


     def build_tags(customer: str, kind: str) -> list[str]:
         """Hierarchical Obsidian tags mirroring the folder structure, so notes
         stay findable by customer/kind via search/graph view independent of
         where they physically live — the point raised when a note sits in
         Unsorted/ but you already suspect which customer it's really for."""
         return [f"customer/{tag_slug(customer)}", f"kind/{tag_slug(kind)}"]
     ```

  2. Append at the end of the file (after `insert_body_line_if_missing`,
     REQ-SB-14's last function):

     ```python
     _PEOPLE_SUBFOLDER = f"{_WORK_ROOT}/People"
     _PERSON_NOTE_BASELINE_KEYS = ("type", "name", "email", "phone", "linkedin", "tags")


     def person_note_path(email: str):
         """Resolves the vault-absolute path a Person note lives (or would
         live) at — Work/People/<slug-of-lowercased-email>.md — without
         checking whether it exists yet. The dedup key is the sender's email
         address, lowercased before slugifying (never the display name, and
         never the raw-cased address): two Outlook items can report the same
         address with different casing, and lowercasing first prevents a
         second, spurious Person note for what is really the same person
         (REQ-SB-10, architecture.md). Uses the same _slugify() write_note()
         applies internally to its own filename_stem when passed the
         identical lowercased string, so this always points at exactly the
         file create_person_note_baseline()/write_note() would create."""
         return settings.vault_path / _PEOPLE_SUBFOLDER / f"{_slugify(email.lower())}.md"


     def person_note_exists(email: str) -> bool:
         return person_note_path(email).exists()


     def build_person_tags(company: str | None) -> list[str]:
         """Mirrors build_tags's shape for the People schema's separate
         company/ tag namespace — never customer/, since a person's employer
         isn't always a customer account (many real contacts are internal
         Core42 colleagues or third parties). Returns ["kind/person"] alone
         when no company was derived (Scenario 5 — a personal/free email
         domain, or no domain at all), or ["company/<slug>", "kind/person"]
         when one was (Scenarios 3 and 4 both get the tag; only Scenario 3
         also gets the wikilink, added separately by the orchestration
         layer)."""
         if not company:
             return ["kind/person"]
         return [f"company/{tag_slug(company)}", "kind/person"]


     def create_person_note_baseline(name: str, email: str, tags: list[str]) -> str:
         """Creates a Person note for the first time: baseline frontmatter
         (type/name/email/phone/linkedin/tags) with an empty body — the
         REQ-SB-14 hub-note baseline pattern applied to People. The company
         wikilink line (when applicable) is never written here — it is
         inserted separately via insert_body_line_if_missing by the
         orchestration layer, the same way customer_hub_linking.
         link_note_to_customer_hub layers on top of ensure_customer_hub_note,
         so a Person note with no matching customer at creation time still
         gets the link retroactively once one exists (Scenario 8). Always
         writes unconditionally, mirroring write_note()'s own contract —
         callers must check person_note_exists() first (app/business/
         people_extraction.py does)."""
         return write_note(
             subfolder=_PEOPLE_SUBFOLDER,
             filename_stem=email.lower(),
             frontmatter={
                 "type": "Person",
                 "name": name,
                 "email": email,
                 "phone": "",
                 "linkedin": "",
                 "tags": tags,
             },
             body="",
         )


     def ensure_person_note_baseline_frontmatter(path, name: str, email: str, tags: list[str]) -> list[str]:
         """Tops up an already-existing Person note with any of the six
         baseline frontmatter keys it is missing (type/name/email/phone/
         linkedin/tags), inserting each surgically via
         insert_frontmatter_key_if_missing — never touches a key already
         present (so a user-filled phone/linkedin value, once set, is never
         reset to ""), and never touches the body. Returns the list of keys
         actually inserted (empty if the note already had all six) —
         REQ-SB-10 Scenario 6's baseline-preservation mechanism, the same
         contract ensure_hub_note_baseline_frontmatter already established
         for Customer hub notes."""
         baseline_values = {
             "type": "Person",
             "name": name,
             "email": email,
             "phone": "",
             "linkedin": "",
             "tags": tags,
         }
         inserted: list[str] = []
         for key in _PERSON_NOTE_BASELINE_KEYS:
             if insert_frontmatter_key_if_missing(path, key, baseline_values[key]):
                 inserted.append(key)
         return inserted
     ```

---

## Constraints

- Inherits from parent story (ADR-003 layering; People never nested under a
  `Company` folder — a straight extension of ADR-004's folder-vs-tag
  reasoning; idempotency is load-bearing since this runs against the real
  live vault).
- This file lives in `data_access/` only — no business rules (company
  derivation, customer matching, and the "create vs. top-up" decision belong
  to T02's `people_extraction.py`), no HTTP concerns.
- Must NOT modify `write_note`, `read_note`, `insert_frontmatter_key_if_missing`,
  `insert_body_line_if_missing`, `list_all_note_paths`, `list_known_customers`,
  or any other existing function's behavior beyond the `_tag_slug`→`tag_slug`
  rename — additive only.
- `person_note_path()` must use the same `_slugify()` call `write_note()`
  applies internally to `filename_stem`, on the identical lowercased email
  string in both places, so the two always resolve to the same file for the
  same email address regardless of casing.
- `email:` frontmatter itself stores the sender's address exactly as
  captured (not lowercased) — only the filename/lookup key is normalized.

---

## Tests

<!-- This task's own functions are exercised end-to-end, live, by T04 (the
retrofit endpoint — most of this story's locked ACs) and T03 (the per-write
hook — AC-07), which is where this story's locked ACs are tagged. The smoke
checks below are non-AC-tagged confirmations that this module's new
primitives (and the tag_slug rename) behave correctly in isolation before
T02/T03/T04 build on them. -->

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv`
   (`.venv\Scripts\python.exe`, real configured `vault_path`), confirm
   `tag_slug("Core42") == tag_slug("CORE42") == tag_slug("core42") ==
   "core42"`, and that `build_tags("ADNOC", "Emails")` still returns
   `["customer/adnoc", "kind/emails"]` exactly as before the rename (no
   behavior change, only the function's name and visibility changed).
2. Non-AC smoke check: call
   `create_person_note_baseline("Verify T01 Person", "Verify.T01@Example.COM",
   build_person_tags("Example"))`. Confirm a file is created at
   `Work/People/verify-t01-example-com.md` (lowercased before slugifying)
   with frontmatter `type: Person`, `name: "Verify T01 Person"`,
   `email: "Verify.T01@Example.COM"` (exact casing preserved), `phone: ""`,
   `linkedin: ""`, `tags: [company/example, kind/person]`, and an empty
   body. Confirm `person_note_exists("Verify.T01@example.com")` (different
   casing) also returns `True`, and `person_note_path(...)` with either
   casing resolves to the identical file — confirming the lowercase-before-
   slugify dedup key. Delete the test file afterward (throwaway
   verification data, not part of Scenario 1's real retrofit — that runs
   live in T04).
3. Non-AC smoke check: on the same throwaway note, manually remove the
   `linkedin` frontmatter line, then call
   `ensure_person_note_baseline_frontmatter(path, "Verify T01 Person",
   "Verify.T01@Example.COM", build_person_tags("Example"))` and confirm
   only the missing `linkedin: ""` line is (re-)inserted — the other five
   existing keys and the (empty) body are byte-for-byte unchanged. Re-run
   the same call and confirm nothing changes the second time (already-
   present keys are never re-inserted). Delete the test file and, if now
   empty, the `Work/People/` directory it created, restoring the vault to
   its pre-task state.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `tag_slug` is a public rename of `_tag_slug` with no behavior change;
      `build_tags`'s two call sites updated
- [x] `person_note_path`/`person_note_exists`/`create_person_note_baseline`
      resolve to and create the exact schema from
      `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md` → "People",
      keyed by the lowercased-then-slugified email address
- [x] `build_person_tags` returns `["kind/person"]` alone when `company` is
      falsy, or `["company/<slug>", "kind/person"]` otherwise
- [x] `ensure_person_note_baseline_frontmatter` tops up missing baseline keys
      only, never resets a present value, never touches the body
- [x] No existing `vault_writer.py` function's behavior changed beyond the
      `_tag_slug`→`tag_slug` rename
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Deciding company derivation, customer matching, or which sender's Person
  note to create/update — that is T02 (`people_extraction.py`).
- Wiring the per-write hook into `email_classification.py` — that is T03.
- The retrofit HTTP endpoint — that is T04.

---

## Context / Notes

`vault_writer.py` currently ends with `insert_body_line_if_missing` (added by
REQ-SB-14-US-01-T01); append the new People primitives directly after it, in
the order shown above (each new function references only prior functions in
the file, no forward references). No new imports are required — `settings`,
`write_note`, `read_note`, `insert_frontmatter_key_if_missing`, `_slugify`,
`_WORK_ROOT` all already exist in this module. The `_tag_slug`→`tag_slug`
rename must land as a single localized edit (function definition + its two
call sites inside `build_tags`) — do not touch anything else in the file
while doing it.

---

## Implementation Log

**What was changed** (2026-08-11, coder): `src/backend/app/data_access/
vault_writer.py` only, exactly per `## Files to Modify`:
1. `_tag_slug` → public `tag_slug`, `build_tags`'s two internal call sites
   updated. Localized to that one block; nothing else in the function
   touched.
2. Five new items appended after `insert_body_line_if_missing`:
   `_PEOPLE_SUBFOLDER`, `_PERSON_NOTE_BASELINE_KEYS`, `person_note_path`,
   `person_note_exists`, `build_person_tags`, `create_person_note_baseline`,
   `ensure_person_note_baseline_frontmatter`. No new imports needed (all
   verified pre-existing in the module). No other existing function's body
   was touched.

This task carries no story-level locked AC-IDs of its own — this task's
`## Tests` header states its functions are exercised end-to-end, live, by
T02/T03/T04, and the three verification steps below are explicitly
non-AC-tagged smoke checks. All three were run manually against the real
backend `.venv` (`.venv\Scripts\python.exe`) and the real configured vault
(`VAULT_PATH` from `src/backend/.env`, not read/printed).

**Smoke check 1 (tag_slug/build_tags — no behavior change) — PASS.**
`tag_slug("Core42") == tag_slug("CORE42") == tag_slug("core42") ==
"core42"` confirmed; `build_tags("ADNOC", "Emails") ==
["customer/adnoc", "kind/emails"]` confirmed, identical to pre-rename
behavior.

**Smoke check 2 (create_person_note_baseline / person_note_path /
person_note_exists) — PASS, with one noted narrative discrepancy (see
Assumptions below).** Called `create_person_note_baseline("Verify T01
Person", "Verify.T01@Example.COM", build_person_tags("Example"))` against
the real vault. A file was created under `Work/People/` with frontmatter
`type: "Person"`, `name: "Verify T01 Person"`,
`email: "Verify.T01@Example.COM"` (exact casing preserved), `phone: ""`,
`linkedin: ""`, `tags: ["company/example", "kind/person"]`, and an empty
body — confirmed by reading the file back. `person_note_exists
("Verify.T01@example.com")` (different casing) returned `True`, and
`person_note_path(...)` with either casing resolved to the identical
`Path` object — confirming the lowercase-before-slugify dedup key works as
specified. The actual filename created was `verify.t01@example.com.md`,
not the `verify-t01-example-com.md` the Tests section's narrative
predicted — see Assumptions below; this did not affect the pass/fail of
the check itself (dedup/resolution/frontmatter all correct). Deleted
afterward.

**Smoke check 3 (ensure_person_note_baseline_frontmatter top-up +
idempotency) — PASS.** Removed the `linkedin: ""` line from the throwaway
note, then called `ensure_person_note_baseline_frontmatter(path, "Verify
T01 Person", "Verify.T01@Example.COM", build_person_tags("Example"))`.
Returned `["linkedin"]`; confirmed all five pre-existing keys
(`type`/`name`/`email`/`phone`/`tags`) and the empty body were unchanged,
and `linkedin: ""` was (re-)inserted — surgically, just before the closing
`---`, per `insert_frontmatter_key_if_missing`'s documented insert-position
contract (not appended in its original position — expected, matches the
same contract `ensure_hub_note_baseline_frontmatter` already established
for Customer hub notes). Re-ran the identical call: returned `[]`
(no-op), and the file's bytes were unchanged before/after (verified via
direct string comparison) — confirming already-present keys are never
re-inserted. Deleted the throwaway note afterward; `Work/People/` was
then empty, so the directory itself was also removed, restoring the vault
to its exact pre-task state (confirmed via `git status` showing no
tracked/untracked changes under the vault, and directory listing showing
`Work/People/` no longer exists).

**Assumptions (scope-internal judgement call, logged for human
spot-check per Pipeline.md's non-escalation-trigger path — this is why
`gate: flagged` above, not a blocker):** The task's `## Tests` step 2
narrative states the created filename would be
`Work/People/verify-t01-example-com.md`, implying `_slugify()` collapses
dots/`@` into hyphens. It does not — `_slugify()` (pre-existing,
out-of-scope-to-modify function) only strips Windows-illegal path
characters (`\/:*?"<>|`); the fuller hyphenation behavior belongs to
`tag_slug()`, used for tags, not filenames. The actual code I wrote is
verbatim what the task's own `## Files to Modify` code block specifies
(`_slugify(email.lower())`), so this is a discrepancy in the Tests
section's narrative prediction, not a deviation from the specified
implementation. Functionally nothing is broken: the dedup key still
works correctly regardless of casing (verified above), `@`/`.` are valid
Windows filename characters, and no locked story AC or task AC-level
checkbox depends on the literal filename string — T02's own smoke-check
narrative (`Implementation/Tasks/REQ-SB-10-US-01-T02-...md`, step
referencing `"verify.t02@example.com"`) does not assume hyphenation
either, so this is self-consistent going forward. Recorded as a MEMORY.md
constraint (`_slugify()` vs `tag_slug()` normalize differently) so future
tasks don't repeat the assumption. No ADR deviation, no new dependency,
no shared-interface change — a narrative/prose inaccuracy in one task's
Tests section, not a functional or architectural issue, so not written to
`ESCALATIONS.md`/`REVIEW-QUEUE.md` as a blocker; flagged here for human
awareness only.

**Task-level Acceptance Criteria (checkboxes, not story AC-IDs):**
- [x] `tag_slug` is a public rename of `_tag_slug` with no behavior
      change; `build_tags`'s two call sites updated — smoke check 1, PASS
- [x] `person_note_path`/`person_note_exists`/`create_person_note_baseline`
      resolve to and create the exact schema, keyed by the
      lowercased-then-slugified email address — smoke check 2, PASS (see
      Assumptions re: literal filename hyphenation narrative)
- [x] `build_person_tags` returns `["kind/person"]` alone when `company`
      is falsy, or `["company/<slug>", "kind/person"]` otherwise — smoke
      check 2 exercised the non-falsy branch (`["company/example",
      "kind/person"]`), confirmed correct; the falsy-`company` branch is a
      one-line early return read-verified by inspection
- [x] `ensure_person_note_baseline_frontmatter` tops up missing baseline
      keys only, never resets a present value, never touches the body —
      smoke check 3, PASS
- [x] No existing `vault_writer.py` function's behavior changed beyond
      the `_tag_slug`→`tag_slug` rename — confirmed by diff review: only
      the renamed block and the new appended block changed
- [x] `MEMORY.md` updated — one Pattern entry (helper promotion) and one
      Constraint entry (`_slugify()` vs `tag_slug()` normalization
      difference)
- [x] `CHANGELOG.md` entry appended

gate: flagged 2026-08-11 — non-blocking assumption logged above (Tests
section's filename narrative vs. actual `_slugify()` behavior); everything
else auto-advanced clean (no ADR deviation, no new dependency, no
unanticipated file, no contradictory requirement, no locked story AC
verification failure — this task carries none of its own).

---

**Orchestrator review (2026-08-11):** the discrepancy is narrative-only (the
task's own Tests section predicted a hyphenated filename string; `_slugify()`
doesn't hyphenate `.`/`@`, unlike `tag_slug()`) — dedup-by-lowercased-email,
frontmatter correctness, and idempotency all verified correct regardless.
Reviewed and approved — `gate: flagged → clear`.
