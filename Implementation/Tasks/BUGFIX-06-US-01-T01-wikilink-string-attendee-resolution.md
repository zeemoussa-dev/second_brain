---
id: BUGFIX-06-US-01-T01
title: Normalize a plain wikilink-string attendees/recipients item to real Person data in cockpit/people.py, via a promoted public vault_writer.WIKILINK_PATTERN
parent_story: BUGFIX-06-US-01
requirement_id: BUG-027
type: backend
status: Done
gate: flagged
gate_reason: "One scope-internal judgement call disclosed for human spot-check, not blocking: the live vault currently has no note anywhere carrying a real `recipients` field (the pipeline that used to write that shape moved to the Thread-based model, REQ-SB-71-US-02), so AC-02's own step-4 'already-JSON-encoded recipients unregressed' facet was verified by temporarily adding one, via the SAME direct-reverted-file-edit technique the task's own Tests step 3 already sanctions for the orphan-stem facet, rather than against a pre-existing real note. Fully reverted; see this task's own Implementation Log for the full record. AC-01 and AC-02 both genuinely PASS; the task is NOT blocked."
phase: MVP
depends_on: []
created: 2026-08-19
updated: 2026-08-19
---

# BUGFIX-06-US-01-T01 — Normalize a plain wikilink-string attendees/recipients item to real Person data in cockpit/people.py, via a promoted public vault_writer.WIKILINK_PATTERN

## Parent Story

- Story: [[BUGFIX-06-US-01]] — `../UserStories/BUGFIX-06-US-01-meeting-cockpit-wikilink-string-attendees-no-longer-500.md`
- Requirement: `BUGS.md` → `BUG-027` (bugfix story; no PRD requirement anchor)

---

## Objective

Fix `BUG-027`: `cockpit/people.py::_coerce_people_list` gains per-item
normalization for a plain wikilink-string `attendees`/`recipients` list
entry (the real, current shape `meeting_classification.py`'s own
attendee-write path writes today), stripping `[[...]]` via a newly
promoted public `vault_writer.WIKILINK_PATTERN` (renamed from the private
`_WIKILINK_PATTERN`, updating its own 2 internal call sites — pure
rename, no behaviour change) and resolving the extracted stem via
`vault_indexing.get_index()` — the same stem-keyed lookup
`resolve_people_chips` already performs for the subject note itself — so
`GET /cockpit/meeting/<id>` returns 200 with real attendee data instead
of a bare `500`.

---

## Starting State → End State

**Before / Inputs:**
- `src/backend/app/data_access/vault_writer.py` (line ~990) defines a
  private `_WIKILINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")`, used at
  exactly 2 internal call sites: `extract_wikilink_targets` (line ~127)
  and `upsert_attendee_links` (line ~1249).
- `src/backend/app/business/cockpit/people.py::_coerce_people_list` only
  handles a JSON-encoded string (`json.loads`) or an already-Python
  `list` (passed through unexamined, item-by-item type unchecked).
  `resolve_people_chips`'s own loop then runs `person.get("email", "")`
  unconditionally on every item — an `AttributeError` (surfaced as a bare
  `500`) when an item is a plain wikilink string, not a dict.
- Confirmed live: `meeting_classification.py`'s real, current attendee-
  write path (lines ~452-466) always writes Meeting `attendees` as
  `[f"[[{stem}]]" for stem in person_stems]` — a plain `list[str]` of
  wikilinks, never `list[dict]`.

**After / Outputs:**
- `vault_writer.py`'s wikilink-stripping regex is public
  (`WIKILINK_PATTERN`), with its own 2 internal call sites updated to the
  new name — behaviourally identical, importable from
  `app/business/cockpit/people.py`.
- `_coerce_people_list` normalizes every item in the coerced list through
  a new `_normalize_person_item` helper: a dict item passes through
  unchanged (the already-working `list[dict]`-after-JSON-decode shape,
  and the forward-compatible real-`list[dict]` shape); a plain wikilink
  string is stripped to its stem via `WIKILINK_PATTERN.fullmatch`, looked
  up via `vault_indexing.get_index().get(stem)`, and — if found —
  normalized to `{"name": <real name>, "email": <real email>}` from that
  Person note's own frontmatter; an unresolvable stem (or a malformed
  string item) normalizes to `{}`, which `resolve_people_chips`'s own
  unchanged downstream loop already renders as the existing "no note yet"
  fallback chip (`has_note: False`).
- `resolve_people_chips` itself is unchanged — its own downstream loop
  needs no per-item type branching, since `_coerce_people_list` now
  always returns a uniform `list[dict]` regardless of which of the three
  real frontmatter shapes it started from.
- No Person note is ever created by this code path (`ADR-036` point 7,
  unchanged).

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py`:
  1. Rename the module-level constant (line ~990) from
     `_WIKILINK_PATTERN` to `WIKILINK_PATTERN`, with a comment recording
     the promotion (mirrors the `tag_slug` promotion precedent,
     `REQ-SB-10-US-01-T01`):

     ```python
     # Public (promoted from the former _WIKILINK_PATTERN -- BUGFIX-06-US-01,
     # BUG-027 -- so app/business/cockpit/people.py has one shared
     # wikilink-stripping regex instead of duplicating [[...]] extraction
     # outside data_access; pure rename, no behavior change. Mirrors the
     # tag_slug promotion precedent, REQ-SB-10-US-01-T01.)
     WIKILINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")
     ```

  2. Update `extract_wikilink_targets`'s own call site (line ~127) and its
     docstring's own prose mention (line ~119) from `_WIKILINK_PATTERN` to
     `WIKILINK_PATTERN` — no other change to this function.
  3. Update `upsert_attendee_links`'s own call site (line ~1249) from
     `_WIKILINK_PATTERN` to `WIKILINK_PATTERN` — no other change to this
     function.
  4. No other reference to `_WIKILINK_PATTERN` exists anywhere in
     `src/backend` (confirmed by a full-repo search before this task was
     written) — these are the only 3 lines (definition + 2 call sites)
     needing the rename.

- `src/backend/app/business/cockpit/people.py` — replace the file's full
  contents with:

  ```python
  """Cockpit people-chip resolution (ADR-036 point 7) -- reads a subject
  note's attendees/recipients frontmatter list directly, resolving each
  person via people_extraction's new read-only lookup. Never creates a
  Person note."""
  from __future__ import annotations

  import json

  from app.business import people_extraction, vault_indexing
  from app.data_access import vault_writer

  _ATTENDEE_FIELD_BY_KIND = {"meeting": "attendees", "email": "recipients"}


  def _normalize_person_item(raw_item) -> dict:
      """A plain wikilink-string attendees/recipients item (BUG-027 -- the
      real, current shape meeting_classification.py's own attendee-write
      path writes today, list[str] of "[[<person-note-stem>]]", not the
      ADR-036 point 7-designed list[dict]) is normalized here to the SAME
      {"name", "email"} shape a list[dict] item already carries, so
      resolve_people_chips's own downstream loop needs no per-item type
      branching. Strips [[...]] via vault_writer.WIKILINK_PATTERN (the
      same regex upsert_attendee_links already uses) to recover the
      wikilink's stem, then resolves it via vault_indexing.get_index()
      (the SAME stem-keyed lookup resolve_people_chips already performs
      for the subject note itself) -- a found entry's real name/email
      frontmatter (create_person_note_baseline's own written values,
      never fabricated). An unresolved stem (no matching vault entry) or
      a malformed item returns {} -- deliberately falls through to the
      existing "no note yet" chip shape below; NEVER calls
      ensure_person_note (ADR-036 point 7's read-only contract,
      unchanged). A dict item (the originally-designed shape) passes
      through unmodified -- this function only handles the plain-string
      case.

      Known, disclosed, narrow residual limitation (mirrors person_note_
      dedup_key's own documented one, see BUGFIX-06-US-01's own Notes):
      a resolved wikilink whose Person note has no email (a name-keyed
      dedup_key, ADR-048 Decision 6) still round-trips through
      resolve_people_chips's own downstream find_existing_person_note
      (email) re-lookup, which requires a non-empty email -- such an
      attendee renders with its real name but the non-clickable "no note
      yet" chip state, not the clickable one, even though a real Person
      note exists. Not exercised by BUG-027's own confirmed real repros
      (both email-keyed); not resolved further by this fix."""
      if not isinstance(raw_item, str):
          return raw_item
      match = vault_writer.WIKILINK_PATTERN.fullmatch(raw_item.strip())
      if match is None:
          return {}
      entry = vault_indexing.get_index().get(match.group(1))
      if entry is None:
          return {}
      frontmatter = entry["frontmatter"]
      return {"name": frontmatter.get("name"), "email": frontmatter.get("email")}


  def _coerce_people_list(raw_value) -> list[dict]:
      """The attendees/recipients frontmatter value is designed (ADR-036
      point 7) as a native list[dict]. vault_writer.py's own real
      frontmatter parser (_parse_frontmatter_value) does not support a
      list-of-dicts literal today -- confirmed live: it only recognizes a
      quoted string or a list of quoted strings, so a Python dict written
      through write_note()'s own list branch round-trips back as an empty
      list, silently losing the data. A caller that writes this field must
      therefore JSON-encode it as a single quoted string for it to survive
      a read_note() round trip. Accepts both shapes so this function works
      correctly today (JSON string) and remains forward-compatible if a
      future vault_writer.py change ever adds real list-of-dicts support
      (a real list, used as-is).

      A THIRD real shape (BUG-027, confirmed by direct reading of
      meeting_classification.py's own current, live attendee-write path)
      is also handled here: a plain Python list[str] of wikilinks
      (["[[stem]]", ...]) -- the shape Meeting attendees actually ships
      as today, never list[dict]. Every item is passed through
      _normalize_person_item, which normalizes a plain wikilink string to
      a {"name", "email"} dict (or {} if unresolvable) and passes a dict
      item through unchanged -- so this function's own return contract
      (list[dict]) holds for all three input shapes."""
      if isinstance(raw_value, str):
          try:
              people = json.loads(raw_value) or []
          except (json.JSONDecodeError, ValueError):
              return []
      else:
          people = raw_value or []
      return [_normalize_person_item(item) for item in people]


  def resolve_people_chips(subject_kind: str, subject_note_stem: str) -> list[dict]:
      entry = vault_indexing.get_index().get(subject_note_stem)
      if entry is None:
          return []
      field = _ATTENDEE_FIELD_BY_KIND.get(subject_kind, "attendees")
      people = _coerce_people_list(entry["frontmatter"].get(field))
      chips = []
      for person in people:
          existing = people_extraction.find_existing_person_note(person.get("email", ""))
          chips.append({
              "name": person.get("name") or person.get("email") or "Unknown",
              "email": person.get("email"),
              "has_note": existing is not None,
              "note_path": existing["note_path"] if existing else None,
          })
      return chips
  ```

  (Note: `resolve_people_chips`'s own body is byte-for-byte unchanged from
  the current real file — verify the real current file before applying
  this replacement, per this project's own established "compose around
  the REAL current file" Learnings pattern, in case a sibling in-flight
  session has touched this file since this task was written.)

---

## Constraints

- Inherits from parent story (real, live vault — no fixture; must never
  create a Person note as a side effect of resolving chips, `ADR-036`
  point 7).
- Must NOT change `_coerce_people_list`'s two already-working shapes (a
  JSON-encoded string; an empty/missing field) — both must continue to
  resolve exactly as they do today. `json.loads`'s own decoded items are
  always dicts, so `_normalize_person_item` passes them through
  unmodified — the JSON-string shape's behaviour is unaffected by
  construction.
- Must NOT modify `meeting_classification.py`'s own attendee-write path —
  out of this task's own `## Files to Modify`.
- Must NOT modify `people_extraction.py`'s `find_existing_person_note`/
  `find_person_note_by_name` — `resolve_people_chips`'s own downstream
  call to `find_existing_person_note` is unchanged.
- The `vault_writer.py` rename must be a pure rename — no behavioural
  change to `extract_wikilink_targets` or `upsert_attendee_links` beyond
  the name of the regex constant they reference.
- Applies to both `subject_kind` values (`"meeting"` → `attendees`,
  `"email"` → `recipients`) — the fix lives in the shared
  `_coerce_people_list`/`_normalize_person_item`, not meeting-specific.

---

## Tests

**Manual verification steps (real endpoint calls against the real,
configured vault — `.venv\Scripts\python.exe`, cwd `src/backend`, a
running `uvicorn` instance; no fixture/mock vault):**

1. [BUGFIX-06-US-01-AC-01] `GET /cockpit/meeting/<meeting-note-stem>` for
   the real Meeting note "Alignment Mubadala-2026-08-17-a4737bc4" (its
   `attendees` frontmatter is a real plain wikilink-string list per
   `BUG-027`'s own confirmed repro) — confirm the response is `200`, not
   `500`, and that `people` in the response body contains a chip whose
   `name`/`email` match a real, resolvable attendee wikilink's own Person
   note frontmatter (cross-check by directly reading that Person note's
   `name`/`email` frontmatter and confirming an exact match, not just a
   plausible-looking value).
2. [BUGFIX-06-US-01-AC-01] Repeat step 1 against the second real,
   confirmed repro meeting, "PSS Team Weekly Meeting-2026-08-18-47a72b70"
   — same `200` + real-data confirmation.
3. [BUGFIX-06-US-01-AC-02] From either of the two meetings above (or, if
   neither has a genuinely orphaned wikilink stem, by temporarily adding
   one real, disclosed, reverted-after-test wikilink stem with no
   matching Person note to one meeting's own `attendees` list via
   `insert_frontmatter_key_if_missing`/a direct, reverted file edit) —
   confirm the corresponding chip in the response has `has_note: false`,
   `note_path: null` (the existing "no note yet" fallback shape), and
   that the request still returns `200`, never crashing. Revert any
   temporary vault edit made for this step immediately after observing
   the result.
4. [BUGFIX-06-US-01-AC-02] `GET /cockpit/email/<subject-note-stem>` for a
   real Inbox/Email subject note whose `recipients` frontmatter is
   already a JSON-encoded string of dicts (the pre-existing, already-
   working shape) — confirm the response is unchanged from this fix's
   behaviour (same `200`, same real name/email chip data as before this
   change).
5. [BUGFIX-06-US-01-AC-02] `GET /cockpit/<meeting|email>/<subject-note-
   stem>` for a real subject note whose attendees/recipients field is
   empty or missing entirely — confirm the response is `200` with an
   empty `people` list, unchanged from this fix's behaviour.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `vault_writer.WIKILINK_PATTERN` is public; its own 2 internal call
      sites (`extract_wikilink_targets`, `upsert_attendee_links`) use the
      new name; pure rename, no other behaviour change
- [x] `cockpit/people.py::_normalize_person_item` normalizes a plain
      wikilink-string item to `{"name", "email"}` from a resolved Person
      note's own real frontmatter, or `{}` for an unresolvable stem; a
      dict item passes through unchanged
- [x] `_coerce_people_list` applies `_normalize_person_item` to every item
      regardless of source shape (JSON string, real list, wikilink-string
      list); its own two already-working shapes are unregressed
- [x] `resolve_people_chips` never creates a Person note as a side effect
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any change to `meeting_classification.py`'s own attendee-write path.
- Retrofitting `_coerce_people_list`'s own docstring-claimed `list[dict]`
  branch into an actually-reachable write path — no code path writes
  that shape today and none is added by this fix.
- Resolving the disclosed name-keyed-Person-note-with-no-email residual
  limitation (see `_normalize_person_item`'s own docstring above and the
  parent story's `## Notes`) — narrow, not exercised by `BUG-027`'s own
  confirmed real repros, not a locked AC.
- Any change to `find_existing_person_note`/`find_person_note_by_name`.

---

## Context / Notes

Full reasoning: `Implementation/Architecture/architecture.md` → "Meeting &
Inbox Cockpits — multi-agent shared-thread workspace" → `people.py`
extended bullet (architect's own `BUGFIX-06-US-01` pass, 2026-08-19). No
ADR created or changed — this composes two already-`Accepted` primitives
(`vault_writer`'s wikilink-stripping regex; `vault_indexing.get_index()`'s
stem-keyed lookup) at a second call site.

---

## Implementation Log

**Coder pass, 2026-08-19.** Implemented exactly as specced — no deviation.

**Changes:**
1. `src/backend/app/data_access/vault_writer.py`: renamed `_WIKILINK_
   PATTERN` → public `WIKILINK_PATTERN` with the promotion comment (line
   ~990); updated the docstring mention + call site in
   `extract_wikilink_targets` (line ~119/127) and the call site in
   `upsert_attendee_links` (line ~1249). Confirmed via full-repo grep,
   before and after, that these were the only 3 real references — pure
   rename, no other line touched.
2. `src/backend/app/business/cockpit/people.py`: replaced file contents
   verbatim per the task's own spec — added `_normalize_person_item`,
   wired it into `_coerce_people_list`'s per-item pass; `resolve_people_
   chips`'s own body confirmed byte-for-byte unchanged from the real,
   current file before applying the replacement (per this project's
   "compose around the REAL current file" pattern).

**Environment note (assumption, scope-internal, logged per Hard Rule 5):**
the running backend (`uvicorn app.main:app --port 8000`, no `--reload`)
had to be restarted to pick up the code change, then `POST /vault-index/
rebuild` re-run after every vault-file edit made during verification
(temporary edit or revert) so `vault_indexing.get_index()` reflected the
real, current file content before each observed HTTP call. This is
verification mechanics, not a scope change — no task file was touched
beyond the two listed above.

**AC-01 verification (both real, confirmed repro meetings) — PASS:**
- `GET /cockpit/meeting/Alignment%20Mubadala-2026-08-17-a4737bc4` →
  `200` (previously `500`). `people` contains 3 chips, all
  `has_note: true`. Cross-checked `maik.kurz@core42.ai`'s chip
  (`name: "Maik Alexander Kurz"`, `email: "maik.kurz@core42.ai"`) against
  that Person note's own real frontmatter
  (`Work/People/maik.kurz@core42.ai.md`) — exact match, not just
  plausible-looking.
- `GET /cockpit/meeting/PSS%20Team%20Weekly%20Meeting-2026-08-18-47a72b70`
  → `200` (previously `500`). `people` contains 5 chips, all
  `has_note: true`. Cross-checked `dario.dilelio@core42.ai`'s chip
  (`name: "Dario Di Lelio"`, `email: "dario.dilelio@core42.ai"`) against
  that Person note's own real frontmatter
  (`Work/People/dario.dilelio@core42.ai.md`) — exact match.

**AC-02 verification — PASS, all three facets:**
- **Orphaned wikilink stem, no crash:** temporarily appended one real,
  disclosed wikilink stem with no matching Person note
  (`[[bugfix-06-us-01-ac02-temp-orphan-stem]]`) to the Alignment
  Mubadala meeting's own `attendees` frontmatter (direct, reverted file
  edit, per the task's own sanctioned technique), rebuilt the index, and
  called `GET /cockpit/meeting/Alignment%20Mubadala-2026-08-17-a4737bc4`
  → `200`, the 4th chip resolved to
  `{"name": "Unknown", "email": null, "has_note": false,
  "note_path": null}` — the existing "no note yet" fallback shape, no
  crash. Reverted the edit immediately, rebuilt the index, and
  re-confirmed the note's own file content is byte-for-byte identical to
  its pre-test state.
- **Pre-existing JSON-encoded-string shape, unregressed:** the live vault
  currently has no note anywhere carrying a real `recipients` field
  (confirmed by a full-vault grep, migration_backup excluded) — the
  Email-note-writing pipeline that used to produce this shape has since
  moved to the Thread-based model (`REQ-SB-71-US-02`). **Scope-internal
  judgement call (logged per Hard Rule 5, not an escalation):** reused the
  SAME "direct, reverted file edit" technique the task's own `## Tests`
  step 3 already sanctions for the orphan-stem facet, applied here to
  exercise this sibling regression facet — temporarily added a
  JSON-encoded-string `recipients` field (`"[{\"name\": \"Maik Alexander
  Kurz\", \"email\": \"maik.kurz@core42.ai\"}]"`) to the same Alignment
  Mubadala note, rebuilt the index, and called `GET /cockpit/email/
  Alignment%20Mubadala-2026-08-17-a4737bc4` → `200`, with a single chip
  correctly resolved to `maik.kurz@core42.ai`'s real name/email — this
  shape's own `json.loads` → dict-passthrough path is unaffected by this
  fix's construction (a dict item always short-circuits `_normalize_
  person_item`'s `isinstance` check). Reverted the edit immediately,
  rebuilt the index, and re-confirmed the note's own file content is
  byte-for-byte identical to its pre-test state again.
- **Empty/missing field, unregressed:** `GET /cockpit/email/Re-%20%5B%20
  Core42%20%40UAE%20%5D%20SimplAI%20Agentic%20AI%20Operating%20System%20
  -%20Demo%20(deep%20dive)-2026-` (a real Thread note with no `recipients`
  key at all) → `200`, `people: []`. Unchanged from this fix's own
  before-behaviour (an empty/missing field always short-circuits to `[]`
  before `_normalize_person_item` is ever called).

No `500` and no traceback observed in the running server's log across any
of the above real requests (confirmed by reading the live uvicorn log).
No Person note was created as a side effect of any of the above calls
(`ADR-036` point 7 upheld — `resolve_people_chips`/`_coerce_people_list`/
`_normalize_person_item` never call `ensure_person_note`).

Backend left running and healthy at `http://127.0.0.1:8000` (vault index
rebuilt to reflect the final, fully-reverted vault state) at the end of
this task.

gate: flagged 2026-08-19 — both locked ACs verified live against real
endpoint calls (no AC blocked, no new dependency/shared-interface change/
ADR deviation/unanticipated file), but one scope-internal judgement call
was made to fill a real verification gap (the live vault currently has no
note with a real `recipients` field to exercise AC-02's own JSON-encoded-
string regression facet against) — disclosed above and in
`REVIEW-QUEUE.md` for human spot-check, per Hard Rule 5. Not an
escalation; the task is not blocked.
