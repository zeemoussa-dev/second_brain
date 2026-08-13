---
id: REQ-SB-02-US-01-T01
title: Index-readiness signal + browse/tag-filter/note-detail query logic
parent_story: REQ-SB-02-US-01
requirement_id: REQ-SB-02
type: backend
status: Done
gate: clear
gate_reason: ""
phase: MVP
depends_on: [REQ-SB-01-US-01-T02]
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-02-US-01-T01 — Index-readiness signal + browse/tag-filter/note-detail query logic

## Parent Story

- Story: [[REQ-SB-02-US-01]] — `../UserStories/REQ-SB-02-US-01-browse-and-search.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-02 *Browse & Search*

---

## Objective

Add the first read/query surface over `vault_indexing.get_index()`: a small
additive index-readiness accessor on `vault_indexing.py` (Scenario 7's
honest "nothing indexed yet" check) plus a new `app/business/
vault_search.py` module with browse-all/tag-filter (Scenarios 1, 2, 6) and
single-note forward-link/backlink resolution (Scenario 3). Ranked search
(Scenarios 4, 5) is `T02`, added to this same module.

---

## Starting State → End State

**Before / Inputs:**
- `REQ-SB-01-US-01-T02` (dependency, cross-story — must be `Done` first)
  provides `app.business.vault_indexing.rebuild_index()`/`get_index()` and
  the index entry shape: `{"path", "stem", "frontmatter", "tags",
  "outgoing_wikilinks", "incoming_wikilinks"}` (`ADR-024`).
- No browse/search/query surface exists anywhere in this codebase —
  confirmed by `REQ-SB-01-US-01`'s own Non-Goals and direct inspection of
  `vault_query_tools.py` (narrow, unrelated agent tool-calling helpers).
- `vault_indexing.py` has no way to distinguish "never rebuilt this process
  lifetime" from "rebuilt and genuinely empty."

**After / Outputs:**
- `app/business/vault_indexing.py` gains `get_last_rebuilt_at() -> str |
  None` (a second, independent accessor — does not touch `get_index()`'s
  own signature).
- New `app/business/vault_search.py`:
  - `list_notes(page=1, page_size=20, tag=None) -> {"total", "page",
    "page_size", "notes"}`.
  - `get_note_detail(stem) -> dict | None`.
  - `list_tags() -> {"tags": [{"tag", "count"}]}` — the real, current tag
    list the frontend's tag-filter UI renders (Scenario 2's own
    prerequisite: a real, discoverable tag list, not a fixed illustrative
    set the user must already know).

---

## Files to Modify

- `src/backend/app/business/vault_indexing.py` (existing — additive only,
  per `T02`'s already-established shape; do not reorder or remove any
  existing code):
  - Add near the top, alongside the existing `from app.data_access import
    vault_writer` import:
    ```python
    from datetime import datetime, timezone
    ```
  - Add a second module-level variable alongside the existing
    `_vault_index: dict[str, dict] = {}`:
    ```python
    _last_rebuilt_at: str | None = None
    ```
  - In `rebuild_index()`, extend the `global` statement and set the new
    variable immediately before the existing `return _vault_index`:
    ```python
        global _vault_index, _last_rebuilt_at
        ...
        _vault_index = new_index
        _last_rebuilt_at = datetime.now(timezone.utc).isoformat()
        return _vault_index
    ```
    (i.e. add the one new assignment line directly above the existing
    `return` — every other line of `rebuild_index()` stays exactly as
    `REQ-SB-01-US-01-T02` built it.)
  - Add a new accessor function, alongside the existing `get_index()`:
    ```python
    def get_last_rebuilt_at() -> str | None:
        """ISO-8601 UTC timestamp of the most recent successful
        rebuild_index() call this process lifetime, or None if the index
        has never been built yet -- REQ-SB-02-US-01 Scenario 7's own
        honest "nothing indexed yet" check. A second, independent
        accessor alongside get_index() -- extends ADR-024, does not
        reopen its "no filter/query parameters on get_index()" decision
        (this is a separate function, not a parameter)."""
        return _last_rebuilt_at
    ```

- `src/backend/app/business/vault_search.py` (new):
  ```python
  """Read-only browse/tag-filter/note-detail query logic over
  vault_indexing.get_index() (REQ-SB-02-US-01) -- composes vault_indexing
  only, never vault_writer/filesystem directly (ADR-003), mirroring
  my_day.py's/system_health.py's own "one-module-per-feature, read-only
  aggregation" shape. Ranked search (search()) is added by T02, in this
  same module -- see ADR-026."""
  from __future__ import annotations

  from app.business import vault_indexing

  _DEFAULT_PAGE_SIZE = 20


  def _title_for(entry: dict) -> str:
      """subject when present (Email/Meeting notes); otherwise the note's
      own filename stem -- Customer/Person/Partner hub notes carry no
      "subject" frontmatter field at all. Ordinary projection, not a new
      naming convention."""
      return entry["frontmatter"].get("subject") or entry["stem"]


  def _kind_for(entry: dict) -> str:
      return entry["frontmatter"].get("type", "Unknown")


  def _summary(entry: dict) -> dict:
      return {
          "stem": entry["stem"],
          "title": _title_for(entry),
          "kind": _kind_for(entry),
          "tags": entry["tags"],
      }


  def list_notes(
      page: int = 1,
      page_size: int = _DEFAULT_PAGE_SIZE,
      tag: str | None = None,
  ) -> dict:
      """Scenarios 1, 2, 6 -- browse all notes, or narrow to one exact tag
      (case-sensitive match against the tag strings this project's own
      capture pipelines already write, e.g. "customer/masdar",
      "kind/email"). Sorted by stem -- the one field every entry always
      has; no note-kind-specific date field is universal across every
      indexed kind. An empty result (no notes at all, or a real tag with
      zero matches) returns "notes": [] honestly -- Scenario 6 is this
      same function returning a correctly-empty list, not a distinct code
      path."""
      entries = list(vault_indexing.get_index().values())
      if tag is not None:
          entries = [entry for entry in entries if tag in entry["tags"]]
      entries.sort(key=lambda entry: entry["stem"])

      total = len(entries)
      start = (page - 1) * page_size
      page_entries = entries[start:start + page_size]
      return {
          "total": total,
          "page": page,
          "page_size": page_size,
          "notes": [_summary(entry) for entry in page_entries],
      }


  def list_tags() -> dict:
      """Scenario 2's own prerequisite -- the real, current list of tags
      that actually exist in the index (with counts), sorted by count
      descending then tag name. The frontend's tag-filter UI renders this
      real list rather than requiring the user to already know an exact
      tag string to type (the approved prototype's own fixed chip buttons
      are illustrative-only, not a real discovery mechanism)."""
      counts: dict[str, int] = {}
      for entry in vault_indexing.get_index().values():
          for tag in entry["tags"]:
              counts[tag] = counts.get(tag, 0) + 1
      tags = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
      return {"tags": [{"tag": tag, "count": count} for tag, count in tags]}


  def _resolve_forward_links(entry: dict, index: dict[str, dict]) -> list[dict]:
      """entry["outgoing_wikilinks"] is deliberately RAW, unresolved
      target text (REQ-SB-01-US-01-T02's own shape) -- resolution only
      happens in ADR-024's backlink-deriving pass, against the *target*'s
      own entry, never stored back onto the source. Applies the identical
      case-insensitive stem-matching rule a second time, at read time, to
      resolve each raw target for display. An unresolved target (a
      dangling link, or a manually-authored free-text wikilink -- ADR-024's
      own documented honest-handling case) is simply omitted -- no crash,
      no fabricated entry, the same posture ADR-024 already applies to
      backlink derivation, not a new rule."""
      stems_by_lower_stem = {stem.lower(): stem for stem in index}
      resolved = []
      for target in entry["outgoing_wikilinks"]:
          matched_stem = stems_by_lower_stem.get(target.lower())
          if matched_stem is None or matched_stem == entry["stem"]:
              continue
          resolved.append(_summary(index[matched_stem]))
      return resolved


  def _resolve_backlinks(entry: dict, index: dict[str, dict]) -> list[dict]:
      """entry["incoming_wikilinks"] is already a list of resolved source
      stems (ADR-024 point 3) -- a direct lookup, no re-matching needed."""
      return [_summary(index[stem]) for stem in entry["incoming_wikilinks"] if stem in index]


  def get_note_detail(stem: str) -> dict | None:
      """Scenario 3 -- one note's frontmatter/tags plus its resolved
      forward-link/backlink lists. None for an unknown stem -- T03's
      router translates this to a 404."""
      index = vault_indexing.get_index()
      entry = index.get(stem)
      if entry is None:
          return None
      return {
          "stem": entry["stem"],
          "title": _title_for(entry),
          "kind": _kind_for(entry),
          "frontmatter": entry["frontmatter"],
          "tags": entry["tags"],
          "forward_links": _resolve_forward_links(entry, index),
          "backlinks": _resolve_backlinks(entry, index),
      }
  ```

---

## Constraints

- Inherits from parent story: `api → business → data_access` layering
  (`ADR-003`) — `vault_search.py` calls `vault_indexing` only, never
  `vault_writer`/filesystem directly.
- Do not modify `vault_indexing.py`'s `get_index()` signature, `_build_entry`,
  or `rebuild_index()`'s own rebuild/backlink logic — additive only (the
  new `_last_rebuilt_at` variable/assignment/accessor).
- Do not add an HTTP route in this task — `T03` owns the router.
- No pagination/tag-filter parameters on `vault_indexing.get_index()`
  itself — `ADR-024`'s "no filter/query parameters" boundary stays on that
  function; all filtering/pagination logic lives in `vault_search.py`.
- `list_notes`/`get_note_detail` must never raise for an index with zero
  entries, a tag with zero matches, or an unknown stem — honest
  empty/`None` results, not exceptions.

---

## Tests

<!-- Covers AC-01, AC-02, AC-03, AC-06, and the readiness half of AC-07 (the
router in T03 is what actually surfaces AC-07's HTTP-level honest state;
this task's own scope is the get_last_rebuilt_at() accessor it depends on).
Exercised directly in a Python shell against the real, .env-configured
vault -- REQ-SB-01-US-01-T02/T03/T04 must be Done first so a real index
exists to query. -->

**Manual verification steps** (Python shell, `src/backend` `.venv`):

1. **[REQ-SB-02-US-01-AC-01]** `from app.business import vault_indexing,
   vault_search`; call `vault_indexing.rebuild_index()`, then
   `vault_search.list_notes(page=1, page_size=1000)`. Confirm `"total"`
   equals the real vault's note count and `"notes"` contains one summary
   per indexed note, sorted by `stem`.
2. **[REQ-SB-02-US-01-AC-02]** Pick a real tag from the index (e.g.
   `customer/masdar`). Call `vault_search.list_notes(tag=<that tag>)`;
   confirm every returned note's `tags` list actually contains it, and the
   count matches a direct count over `vault_indexing.get_index()` for that
   tag.
3. **[REQ-SB-02-US-01-AC-03]** Pick a real note with at least one
   real outgoing/incoming wikilink (e.g. an Email note linked to its
   Customer hub). Call `vault_search.get_note_detail(<that stem>)`;
   confirm `forward_links`/`backlinks` each resolve to the correct target
   note's own `title`/`kind`, matching a direct read of
   `vault_indexing.get_index()[<stem>]`.
4. **[REQ-SB-02-US-01-AC-06]** Call
   `vault_search.list_notes(tag="customer/_no_such_tag_exists_")`; confirm
   `{"total": 0, "notes": []}`, not an error.
5. **[REQ-SB-02-US-01-AC-07 — readiness half]** In a fresh Python process
   (before calling `rebuild_index()` at all), confirm
   `vault_indexing.get_last_rebuilt_at()` returns `None`. After calling
   `rebuild_index()` once, confirm it returns a real ISO-8601 UTC
   timestamp string.
6. Non-AC smoke check: `vault_search.get_note_detail("_no_such_stem_")`
   returns `None`, not an exception.
7. Non-AC smoke check (feeds AC-02's UI, not itself a locked AC):
   `vault_search.list_tags()` returns every real tag currently in the
   index with a correct count, sorted by count descending; cross-check one
   real tag's count against a direct `sum(1 for e in
   vault_indexing.get_index().values() if <tag> in e["tags"])`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `list_notes()` returns every indexed note, sorted by stem, correctly
      paginated (AC-01)
- [x] `list_notes(tag=...)` correctly narrows to notes carrying that exact
      tag (AC-02)
- [x] `get_note_detail(stem)` returns a note's resolved forward-links and
      backlinks, each with correct title/kind (AC-03)
- [x] `list_notes(tag=...)` for a tag with zero matches returns `{"total":
      0, "notes": []}`, not an error (AC-06)
- [x] `get_last_rebuilt_at()` returns `None` before the first
      `rebuild_index()` call, and a real timestamp after
- [x] `list_tags()` returns every real tag currently in the index with a
      correct count, sorted by count descending (feeds AC-02's frontend
      tag-filter UI; not itself a separately-locked AC)
- [x] `vault_indexing.py`'s existing `rebuild_index()`/`get_index()`
      behavior is unchanged beyond the one additive assignment
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Ranked search (`search()`) — `T02`, same module.
- Any HTTP route — `T03`.
- Any frontend — `T04`.
- Any change to `vault_indexing.rebuild_index()`'s own rebuild/backlink
  algorithm — untouched, per `ADR-024`.

---

## Context / Notes

Matches `architecture.md`'s "Browse & Search" section verbatim. Depends on
`REQ-SB-01-US-01-T02` (cross-story) — do not reimplement any part of
`vault_indexing.py`'s existing rebuild/backlink logic inline here.

---

## Implementation Log

**2026-08-13 — Built and live-verified against the real vault.** Read the
real, current `app/business/vault_indexing.py` (`REQ-SB-01-US-01`, `Done`,
`SPRINT-025`) before writing anything, per this task's own instruction —
its `rebuild_index()`/`get_index()` and entry shape (`path`/`stem`/
`frontmatter`/`tags`/`outgoing_wikilinks`/`incoming_wikilinks`) matched
this task's own sample exactly; implemented verbatim as specified:
- `vault_indexing.py` gained `_last_rebuilt_at`, the one additive
  assignment inside `rebuild_index()`, and `get_last_rebuilt_at()` —
  `rebuild_index()`'s own rebuild/backlink logic untouched (diff is
  strictly additive, confirmed by re-reading the file after editing).
- New `app/business/vault_search.py` with `list_notes`/`list_tags`/
  `get_note_detail` (`_title_for`/`_kind_for`/`_summary`/
  `_resolve_forward_links`/`_resolve_backlinks` helpers), exactly as
  specified.

**Verification (Python shell, `src/backend` `.venv`, real vault via
`.env`'s `VAULT_PATH`):**
- **[AC-01]** `vault_indexing.rebuild_index()` then
  `vault_search.list_notes(page=1, page_size=10000)` — real vault indexed
  **503 unique-stem notes** (504 real files on disk today; one duplicate
  filename-stem collision, the already-disclosed, out-of-scope, non-
  blocking `BUG-011` from `SPRINT-025` — vault grew by one file and one
  fewer than `SPRINT-025`'s own 502/503 snapshot count only because the
  vault is live and continuously captured against, not a regression).
  `"total"` matched the real note count, `"notes"` sorted by stem — PASS.
- **[AC-02]** Real tag `kind/emails` (199 real notes) — every returned
  note's `tags` contained it; count matched a direct scan — PASS.
- **[AC-03]** Real note
  `2026-07-21-RE- You have a new approval request-92E90000` (a
  Notifications note with a real outgoing link to a Person note and a
  real Customer hub) — `get_note_detail` resolved both forward links
  correctly (`teresita.apaya@core42.ai`, `Core42`) and 1 real backlink,
  matching a direct read of the index — PASS.
- **[AC-06]** `list_notes(tag="customer/_no_such_tag_exists_")` →
  `{"total": 0, "notes": []}`, no error — PASS.
- **[AC-07, readiness half]** Fresh process: `get_last_rebuilt_at()` →
  `None`; after `rebuild_index()` → a real ISO-8601 UTC timestamp — PASS.
- `list_tags()` (non-AC, feeds AC-02's UI) — real tag counts, sorted
  descending, cross-checked against a direct scan — PASS.
- `get_note_detail("_no_such_stem_")` → `None`, no exception — PASS.

No deviation from the plan. No new dependency. `MEMORY.md` updated (see
entry dated 2026-08-13, `REQ-SB-02-US-01`). `CHANGELOG.md` updated.

gate: clear 2026-08-13 — no new MUST-FLAG trigger fired in this task's own
build (the story's carried-forward `ADR-026` flag is tracked at the
story/sprint level, already `Approved` per `REVIEW-QUEUE.md`, not
reopened by this task).
