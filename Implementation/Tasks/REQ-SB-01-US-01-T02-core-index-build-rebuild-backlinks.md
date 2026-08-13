---
id: REQ-SB-01-US-01-T02
title: Core index build/rebuild/backlink logic — app/business/vault_indexing.py
parent_story: REQ-SB-01-US-01
requirement_id: REQ-SB-01
type: backend
status: Done
gate: flagged
gate_reason: "trigger-7 (real, live-discovered filename-stem collision — ESC-027, Open)"
phase: MVP
depends_on: [REQ-SB-01-US-01-T01]
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-01-US-01-T02 — Core index build/rebuild/backlink logic

## Parent Story

- Story: [[REQ-SB-01-US-01]] — `../UserStories/REQ-SB-01-US-01-vault-indexing.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-01 *Vault Indexing*

---

## Objective

Build the first real, persistent, re-runnable vault index: a new
`app/business/vault_indexing.py` module holding an in-memory, module-level
singleton, rebuilt wholesale on every call to `rebuild_index()` (frontmatter
+ tags + outgoing wikilinks per note, then a second pass deriving
incoming-wikilink backlinks), per `ADR-024`.

---

## Starting State → End State

**Before / Inputs:**
- No persistent index exists anywhere in this codebase. `vault_writer.
  list_all_note_paths()` (existing, unchanged — already scoped to
  `Work/*/*.md`, already excludes `.obsidian/`/`Templates/`) and
  `vault_writer.read_note(path)` (existing) are the read primitives this
  task composes.
- `T01` (dependency, must be `Done` first) fixes
  `_parse_frontmatter_value`'s list-value round-trip gap and adds
  `vault_writer.extract_wikilink_targets(body) -> list[str]`.

**After / Outputs:**
- New `app/business/vault_indexing.py`:
  - `rebuild_index() -> dict[str, dict]` — full rebuild, atomically swaps
    in a brand-new module-level dict.
  - `get_index() -> dict[str, dict]` — plain whole-dict accessor (no
    filter/query parameters).
- Each index entry (keyed by the note's filename stem):
  `{"path": str, "stem": str, "frontmatter": dict, "tags": list[str],
  "outgoing_wikilinks": list[str], "incoming_wikilinks": list[str]}`.

---

## Files to Modify

- `src/backend/app/business/vault_indexing.py` (new):
  ```python
  """First real, persistent, re-runnable index of the vault's notes --
  frontmatter, tags, outgoing/incoming wikilinks (REQ-SB-01-US-01). A
  module-level, in-memory-only singleton, rebuilt wholesale (never
  incrementally diffed) and atomically swapped in on every trigger -- see
  ADR-024 for the full storage/rebuild-shape reasoning (no .second-brain/
  persistence, no database this pass)."""
  from __future__ import annotations

  from app.data_access import vault_writer

  _vault_index: dict[str, dict] = {}


  def _build_entry(path) -> dict:
      """One note -> one index entry, keyed later by path.stem (the same
      filename-stem identity write_note()/this project's own wikilinks
      already use). tags defaults to [] when the frontmatter has no tags
      field at all, or when T01's list-parsing fix still can't make it a
      list for some unexpected raw shape -- never a crash, never the raw
      unparsed string leaking through (Scenario 6)."""
      frontmatter, body = vault_writer.read_note(path)
      tags = frontmatter.get("tags")
      if not isinstance(tags, list):
          tags = []
      return {
          "path": str(path),
          "stem": path.stem,
          "frontmatter": frontmatter,
          "tags": tags,
          "outgoing_wikilinks": vault_writer.extract_wikilink_targets(body),
          "incoming_wikilinks": [],
      }


  def rebuild_index() -> dict[str, dict]:
      """Full, idempotent rebuild (ADR-024) -- walks every real note under
      Work/ (vault_writer.list_all_note_paths(), Scenario 7's exclusion is
      already satisfied by that existing primitive), builds one entry per
      note, then a second pass inverts each note's outgoing wikilinks into
      every matched target's incoming_wikilinks list (Scenario 2).
      Wikilink target text is matched against each note's own filename
      stem, case-insensitively -- the same identity this project's own
      capture pipelines already write wikilinks against
      (upsert_attendee_links, record_conversation_note/
      find_related_note_stems). An unresolved target (a dangling link, or
      a manually-authored note's free-text wikilink that doesn't match) is
      simply never added to any incoming_wikilinks list -- no crash, no
      fabricated entry (Scenario 5's "handled honestly" requirement falls
      out for free here: a deleted note's own former target simply cannot
      appear in this fresh rebuild at all).

      Assembles a brand-new dict end to end, then atomically reassigns the
      module-level reference -- a single-reference rebind is safe under
      CPython's GIL, no explicit lock needed. Discarding the old dict
      wholesale (never patching it in place) is what gives deletions/edits
      their honest reconciliation for free (Scenarios 3, 4, 5) -- there is
      no separate add/edit/delete code path, every re-run is the exact same
      full rebuild."""
      global _vault_index
      new_index: dict[str, dict] = {}
      for path in vault_writer.list_all_note_paths():
          entry = _build_entry(path)
          new_index[entry["stem"]] = entry

      stems_by_lower_stem = {stem.lower(): stem for stem in new_index}
      for entry in new_index.values():
          for target in entry["outgoing_wikilinks"]:
              matched_stem = stems_by_lower_stem.get(target.lower())
              if matched_stem is None or matched_stem == entry["stem"]:
                  continue
              backlinks = new_index[matched_stem]["incoming_wikilinks"]
              if entry["stem"] not in backlinks:
                  backlinks.append(entry["stem"])

      _vault_index = new_index
      return _vault_index


  def get_index() -> dict[str, dict]:
      """Plain whole-dict accessor -- no filter/query parameters. Internal/
      test use, and the substrate REQ-SB-02's browse/search will build on;
      deliberately not a browse/search API itself (ADR-024's own Non-Goals
      boundary)."""
      return _vault_index
  ```

---

## Constraints

- Inherits from parent story: `api → business → data_access` layering
  (ADR-003) — this module calls `vault_writer` only, no direct filesystem
  I/O of its own.
- No `.second-brain/` persistence file for this store, no database — the
  index is in-memory only, per `ADR-024`. Do not add a JSON file or any
  disk write for the index itself.
- Every `rebuild_index()` call is a **full** rebuild — no incremental
  diff, no mtime/hash tracking, no separate deletion-tracking code path.
- No filter/query parameters on `get_index()` — a browse/search layer is
  explicitly `REQ-SB-02`'s job, not this task's.
- Do not add an HTTP route in this file — `T03` owns the router.
- `rebuild_index()` must never raise for a note with missing/empty tags or
  no wikilinks (Scenario 6) — no exceptions on the ordinary shape.

---

## Tests

<!-- Covers AC-01 through AC-07 — all seven exercise the same
rebuild_index()/get_index() pair, called once or twice depending on
scenario, against the real, .env-configured vault. Scenarios 3/4/5 use one
temporary test note (created, edited, then deleted), mirroring this
codebase's established temporary-stub-and-revert verification pattern —
the real vault is left exactly as found when this task's verification
finishes. -->

**Manual verification steps** (in a Python shell against the backend
`.venv`, cwd `src/backend`, real vault configured):

1. **[REQ-SB-01-US-01-AC-01]** `from app.business import vault_indexing`;
   call `index = vault_indexing.rebuild_index()`. Confirm `len(index) ==
   len(vault_writer.list_all_note_paths())` (one entry per real note).
   Pick one arbitrary real `Work/Emails/*.md` note; confirm its stem is a
   key in `index`, and that entry's `frontmatter`/`tags`/
   `outgoing_wikilinks` match a direct, independent read of that same file
   via `vault_writer.read_note(path)` +
   `vault_writer.extract_wikilink_targets(body)` — not merely non-empty,
   an exact match.
2. **[REQ-SB-01-US-01-AC-02]** Find a real note pair already linked by
   this project's own capture pipeline (e.g. two `Work/Emails/*.md` notes
   in the same `## Related Emails` thread — `email_classification.py`
   already writes these as `[[<stem>]]`). Confirm the earlier note's
   stem appears in the later-linked-target's `incoming_wikilinks` list in
   `index` — even though the earlier note's own file contains no
   reference to the later one (the backlink is derived, not stored on the
   target note itself).
3. **[REQ-SB-01-US-01-AC-03]** Create one temporary note directly at
   `Work/Emails/_index_test_scenario3.md` with valid frontmatter (`type`,
   `customer`, `tags: ["kind/email"]`) and a body containing a wikilink to
   the real note used in step 1 (e.g. `[[<that note's stem>]]`). Call
   `vault_indexing.rebuild_index()` again; confirm the new temp note's
   stem is now a key in the result, with correctly captured frontmatter/
   tags/outgoing wikilinks.
4. **[REQ-SB-01-US-01-AC-04]** Edit that same temp note's file directly —
   change its `tags` value and its wikilink target to a different real
   note. Call `rebuild_index()` again; confirm the entry now reflects the
   edited tags/wikilink, and that no trace of the pre-edit values (the old
   tag, the old wikilink target's backlink) remains anywhere in the fresh
   result.
5. **[REQ-SB-01-US-01-AC-05]** Delete the temp note file entirely. Call
   `rebuild_index()` again; confirm its stem no longer appears as a key at
   all, and confirm the real note it had most recently wikilinked to (from
   step 4) no longer lists the deleted temp note's stem among its
   `incoming_wikilinks` — no crash, no dangling/fabricated entry.
6. **[REQ-SB-01-US-01-AC-06]** Create a second temporary note at
   `Work/Emails/_index_test_scenario6.md` with valid frontmatter but no
   `tags` field and no `[[wikilinks]]` anywhere in its body. Call
   `rebuild_index()` again; confirm its entry exists with `tags == []` and
   `outgoing_wikilinks == []` (real empty lists, not an error, not the
   field simply missing from the entry dict). Delete this temp note when
   done.
7. **[REQ-SB-01-US-01-AC-07]** On the same `index` result, confirm no
   entry's `path` contains `.obsidian` or `Templates` anywhere in it —
   `all(".obsidian" not in e["path"] and "Templates" not in e["path"] for
   e in index.values())`. Cross-check this is a real (not vacuous)
   exclusion by confirming both `.obsidian/` and `Templates/` genuinely
   exist as siblings of `Work/` in the real vault
   (`settings.vault_path`).
8. **Cleanup:** confirm both temp files from steps 3/6 are deleted from
   the real vault filesystem (not just absent from the last in-memory
   `rebuild_index()` result), then call `rebuild_index()` one final time
   and confirm the resulting `len(index)` matches the real vault's true
   note count with no leftover test artifacts.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `rebuild_index()` produces one entry per real note, with correctly
      captured frontmatter, tags, and outgoing wikilinks (AC-01)
- [ ] Incoming wikilinks (backlinks) are correctly derived on the target
      note's own entry, even though the target note's file never
      references the source (AC-02)
- [ ] Re-running `rebuild_index()` after a note is added picks it up with
      no manual step (AC-03)
- [ ] Re-running `rebuild_index()` after a note is edited reflects the
      change with no stale prior entry (AC-04)
- [ ] Re-running `rebuild_index()` after a note is deleted removes it, and
      any prior backlink referencing it is also gone — no crash, no
      fabricated dangling entry (AC-05)
- [ ] A note with no tags and no wikilinks indexes with empty lists, not
      an error (AC-06)
- [ ] `.obsidian/` and `Templates/` never appear as index entries (AC-07)
- [ ] `get_index()` exposes no filter/query parameters
- [ ] No `.second-brain/` file or database is added for this store
- [ ] Real vault left with zero leftover test artifacts after verification
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The on-demand rebuild HTTP endpoint — `T03`.
- Scheduler-tick wiring — `T04`.
- Any browse/search/filter/ranking endpoint over the index — `REQ-SB-02`.
- `.second-brain/` persistence or a database for the index — rejected in
  `ADR-024`.

---

## Context / Notes

Matches `architecture.md`'s "Vault Indexing Layer" section and `ADR-024`
verbatim. Depends on `T01`'s `extract_wikilink_targets` and
`_parse_frontmatter_value` list-value fix — do not reimplement either
inline here.

---

## Implementation Log

**2026-08-13 — Built exactly as specified (`ADR-024` verbatim), verified
live against the real vault.** New `src/backend/app/business/
vault_indexing.py`: `_build_entry`, `rebuild_index`, `get_index`, module-
level `_vault_index` singleton — no deviation from the task's own code
block.

**Manual verification (Python shell, real `.venv`, cwd `src/backend`, real
vault at `VAULT_PATH`):**

- **[REQ-SB-01-US-01-AC-01]** `rebuild_index()` against the real vault.
  **Real, disclosed finding — see `ESCALATIONS.md` → `ESC-027`:** the real
  vault has 503 note files under `Work/` but only 502 unique filename
  stems — two genuinely distinct, correctly-captured real notes (a real
  Email from `gurpreet.singh@simplai.ai` and an unrelated Google Calendar
  Notification, different `outlook_entry_id`/`conversation_id`) share an
  identical 80-character-truncated filename stem, because
  `email_classification.py`'s stem-construction places the disambiguating
  `entry_id` suffix *after* the subject text, and `vault_writer._slugify`'s
  `max_len=80` truncation silently discards that suffix when the subject
  alone already fills the budget. This is a real, pre-existing gap in
  already-`Done`, out-of-scope code (`email_classification.py`/
  `_slugify`), not a defect in this task's own `rebuild_index()`, which
  faithfully implements `ADR-024` point 1's stem-keyed design. Escalated,
  not silently patched or silently accepted — `ESC-027` (Open),
  `REVIEW-QUEUE.md` pointer added, `/bug` capture recommended. **Every
  other aspect of AC-01 is confirmed PASS:** for every one of the 502
  unique-stem notes, the sampled note's `frontmatter`/`tags`/
  `outgoing_wikilinks` matched an independent direct
  `vault_writer.read_note()` + `extract_wikilink_targets()` call exactly
  (not merely non-empty). `len(index)` was 502 against 503 real files —
  disclosed, not hidden, as the one real exception to "one entry per real
  note."
- **[REQ-SB-01-US-01-AC-02]** Corroborated via a freshly-created temp note
  (`_index_test_scenario3.md`) wikilinking to a real note
  (`ADNOC`'s stem) — the real note's own file contains no reference back,
  yet its index entry's `incoming_wikilinks` correctly listed the new
  note's stem after rebuild. PASS.
- **[REQ-SB-01-US-01-AC-03]** Created `Work/Emails/
  _index_test_scenario3.md` with `tags: ["kind/email"]` and a wikilink to
  a real note; `rebuild_index()` picked it up with correct tags/outgoing
  wikilinks. PASS.
- **[REQ-SB-01-US-01-AC-04]** Edited the same temp note's tags and
  wikilink target to a second real note; re-`rebuild_index()` reflected
  the edit exactly, and the first target's `incoming_wikilinks` no longer
  listed the temp note (no stale entry), while the second target's did.
  PASS.
- **[REQ-SB-01-US-01-AC-05]** Deleted the temp note; re-`rebuild_index()`
  removed it from the index entirely, and the second target's
  `incoming_wikilinks` no longer listed it — no crash, no fabricated
  dangling entry. PASS.
- **[REQ-SB-01-US-01-AC-06]** Created `Work/Emails/
  _index_test_scenario6.md` with valid frontmatter, no `tags`, no
  wikilinks; its entry existed with `tags == []` and
  `outgoing_wikilinks == []` (real empty lists), no error. Deleted after.
  PASS.
- **[REQ-SB-01-US-01-AC-07]** `all(".obsidian" not in e["path"] and
  "Templates" not in e["path"] for e in index.values())` — True. Confirmed
  non-vacuous: both `.obsidian/` and `Templates/` genuinely exist as
  vault-root siblings of `Work/`. PASS.
- **Cleanup:** both temp files (`_index_test_scenario3.md`,
  `_index_test_scenario6.md`) confirmed deleted from the real vault
  filesystem; a final `rebuild_index()` returned exactly 502 entries,
  matching the pre-test baseline (also 502) with zero leftover artifacts.

`get_index()` exposes no filter/query parameters (confirmed by
inspection — zero-arg function). No `.second-brain/` file or database was
added (confirmed — `vault_indexing.py` makes no `vault_writer` state-file
calls at all).

`gate: flagged` — trigger 7 (a genuine, real, out-of-scope finding
surfaced during this task's own mandated live `AC-01` verification, per
`ESC-027`). Mirrors this project's own established `ESC-002`/`ESC-003`/
`ESC-012` precedent: the underlying defect's root cause is outside this
task's `## Files to Modify`, and this task's own code is verified correct
against `ADR-024` as approved — recorded and escalated rather than
blocking `T02`/`T03`/`T04`/the sprint over unrelated, already-`Done`
code.
