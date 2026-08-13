---
id: REQ-SB-01-US-01-T01
title: vault_writer.py frontmatter list-value round-trip fix + public wikilink-extraction primitive
parent_story: REQ-SB-01-US-01
requirement_id: REQ-SB-01
type: backend
status: Done
gate: clear
gate_reason: ""
phase: MVP
depends_on: []
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-01-US-01-T01 — vault_writer.py frontmatter list-value round-trip fix + public wikilink-extraction primitive

## Parent Story

- Story: [[REQ-SB-01-US-01]] — `../UserStories/REQ-SB-01-US-01-vault-indexing.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-01 *Vault Indexing*

---

## Objective

Fix a real, pre-existing gap in `vault_writer.read_note()` so a frontmatter
list value (e.g. `tags: ["a", "b"]`) round-trips back into a real Python
`list[str]` instead of an unparsed string, and add a public, reusable
primitive for extracting every `[[wikilink]]` target from a note's body —
both are load-bearing foundations `T02`'s index-build logic depends on.

---

## Starting State → End State

**Before / Inputs:**
- `vault_writer._parse_frontmatter_value(raw)` has exactly two branches: a
  quoted-string branch, and a raw-passthrough fallback. A `tags:
  ["customer/x", "kind/y"]` line's value therefore reads back as the
  **literal string** `'["customer/x", "kind/y"]'`, not a list — confirmed
  by direct reading of the function; every note ever written by this
  codebase's own `write_note()` (which always serializes `tags` as a list
  via `_format_frontmatter_value`) is affected.
- `vault_writer._WIKILINK_PATTERN` (`re.compile(r"\[\[([^\]]+)\]\]")`)
  already exists, but is private and only ever applied to one matched
  `**Attendees:**` line inside `upsert_attendee_links` — nothing in this
  codebase extracts every wikilink from a note's full body text.

**After / Outputs:**
- `_parse_frontmatter_value` gains one more branch (checked after the
  existing quoted-string branch, before the raw-passthrough fallback):
  a value starting with `[` and ending with `]` is parsed into a real
  `list[str]`, correctly unescaping each quoted item the same way the
  existing string branch already does. Every other existing branch/
  behaviour (quoted string, raw passthrough, the `REQ-SB-30`-added
  boolean branch) is unchanged.
- A new public function, `extract_wikilink_targets(body: str) ->
  list[str]`, returns every `[[target]]` wikilink target found anywhere in
  a note's body text, in first-seen order — reuses the existing
  `_WIKILINK_PATTERN` constant, does not duplicate the regex.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py`:
  - Add one constant near the top, alongside the existing pattern
    constants:
    ```python
    _LIST_ITEM_PATTERN = re.compile(r'"((?:[^"\\]|\\.)*)"')
    ```
  - In `_parse_frontmatter_value`, insert a new branch after the existing
    quoted-string check and before the final `return raw`:
    ```python
    def _parse_frontmatter_value(raw: str):
        raw = raw.strip()
        if raw.startswith('"') and raw.endswith('"'):
            return raw[1:-1].replace('\\"', '"').replace("\\\\", "\\")
        if raw.startswith("[") and raw.endswith("]"):
            # Real gap, found and fixed by REQ-SB-01-US-01: every list-shaped
            # frontmatter value this codebase writes (tags, via
            # _format_frontmatter_value's own list branch) is always a list
            # of quoted strings — mirrors REQ-SB-30-US-01's boolean-branch
            # precedent for the same class of round-trip gap. Still not a
            # general YAML parser (unchanged docstring caveat on read_note);
            # only this one recognized literal shape.
            inner = raw[1:-1]
            return [
                match.group(1).replace('\\"', '"').replace("\\\\", "\\")
                for match in _LIST_ITEM_PATTERN.finditer(inner)
            ]
        return raw
    ```
  - Add a new public function, placed directly after `read_note()`:
    ```python
    def extract_wikilink_targets(body: str) -> list[str]:
        """Every [[target]] wikilink target found anywhere in a note's body
        text, in first-seen order — reuses the same _WIKILINK_PATTERN
        upsert_attendee_links already relies on for one matched
        **Attendees:** line, generalized to the whole body (REQ-SB-01-US-01,
        the vault indexing layer's own outgoing-wikilink capture). Resolving
        a target against another note's own filename stem is the caller's
        job (app/business/vault_indexing.py), not this function's — this is
        a raw text-extraction primitive only, matching read_note()'s own
        "not a general parser" scope."""
        return _WIKILINK_PATTERN.findall(body)
    ```

---

## Constraints

- Inherits from parent story: read-only — this task never writes to the
  vault.
- Do not touch `_format_frontmatter_value` (the write-side list
  serialization is already correct — confirmed by direct reading; only the
  read side has the gap).
- Do not touch `_WIKILINK_PATTERN` itself or `upsert_attendee_links`'s
  existing behaviour — `extract_wikilink_targets` is additive, reusing the
  same constant, not a replacement.
- No new dependency — `re` is already imported.
- Every other existing `_parse_frontmatter_value` branch (quoted string,
  boolean, raw passthrough) must remain byte-for-byte unchanged in
  behaviour — this task is additive only.

---

## Tests

<!-- No AC from the parent story is tagged directly to this task — it is
foundational plumbing T02 depends on. Verified here as non-AC correctness
checks; T02's own AC-tagged steps are the ones that exercise this code
through the real index-build path against real vault notes. -->

**Manual verification steps** (in a Python shell against the backend
`.venv`, cwd `src/backend`):

1. Non-AC smoke check: call
   `vault_writer._parse_frontmatter_value('["customer/acme", "kind/email"]')`
   directly; expect the real Python list `["customer/acme", "kind/email"]`
   (`isinstance(result, list)`, `len(result) == 2`, exact string values),
   not the raw unparsed string.
2. Non-AC smoke check: call `vault_writer._parse_frontmatter_value('"a plain string"')`
   and `vault_writer._parse_frontmatter_value("true")` (if the boolean
   branch already exists from `REQ-SB-30-US-01`); confirm both still
   return their pre-existing correct values — no regression to the
   existing branches.
3. Non-AC smoke check: read a real note from the vault that has a `tags`
   frontmatter field (any real `Work/Emails/*.md` note) via
   `vault_writer.read_note(path)`; confirm `frontmatter["tags"]` is now a
   real `list[str]` matching the note's actual tags, not a string.
4. Non-AC smoke check: call
   `vault_writer.extract_wikilink_targets("some text [[Note A]] more text [[Note B]] end")`;
   expect `["Note A", "Note B"]`. Call it again on a body with no
   wikilinks at all; expect `[]`, not an error.
5. Non-AC smoke check: read a real note with a known `**Attendees:**
   [[Person A]], [[Person B]]` line (any real `Work/Meetings/*.md` note
   with attendees) via `read_note()`, then call
   `extract_wikilink_targets(body)` on its body; confirm the attendee
   targets appear in the result (proving the shared pattern still matches
   real, already-written wikilink syntax).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `_parse_frontmatter_value` correctly parses a bracketed list of
      quoted strings into a real `list[str]`
- [ ] Every pre-existing `_parse_frontmatter_value` branch (quoted string,
      boolean, raw passthrough) is unchanged in behaviour
- [ ] `extract_wikilink_targets(body)` returns every `[[target]]` found in
      a body string, in first-seen order, `[]` when none exist
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Wikilink target resolution against other notes' filename stems — `T02`.
- Any change to `_format_frontmatter_value` (write side) — already correct.
- A general YAML parser — explicitly out of scope per `read_note()`'s own
  existing docstring caveat, unchanged by this task.

---

## Context / Notes

Matches `architecture.md`'s "Vault Indexing Layer" section's "A real,
pre-existing gap in `vault_writer.read_note()`" and "Wikilink resolution"
points, and `ADR-024` point 4. Mirrors `REQ-SB-30-US-01`'s already-shipped
boolean-value-branch fix precedent exactly — same shape, one more literal
value type recognized, no new parsing format.

---

## Implementation Log

**2026-08-13 — Built and verified as written, no deviation.**
`src/backend/app/data_access/vault_writer.py`: added the `_LIST_ITEM_PATTERN`
constant next to `_FRONTMATTER_LINE`, added the bracketed-list branch to
`_parse_frontmatter_value` exactly as specified (before the final
`return raw`), and added the public `extract_wikilink_targets(body)`
function directly after `read_note()`, reusing the existing
`_WIKILINK_PATTERN` module constant (defined later in the file — safe,
since Python resolves the name at call time, after the whole module has
loaded).

**Note (real-codebase drift, not a deviation from this task):** at
verification time, `app/config.py`'s `Settings` class already carries a
`hermes_mcp_shared_secret: str` field (from concurrent `REQ-SB-04`/
`ADR-025` work landing in this same session) that this task's own
Starting-State description did not mention — confirms this project's own
"read the real current file, not a stale sample" pattern. Not in this
task's `## Files to Modify`, not touched.

**Manual verification (in a Python shell against the real backend
`.venv`, cwd `src/backend`, real vault at `VAULT_PATH`):**

- Step 1: `_parse_frontmatter_value('["customer/acme", "kind/email"]')` →
  `['customer/acme', 'kind/email']` (real `list[str]`, exact values). PASS.
- Step 2: `_parse_frontmatter_value('"a plain string"')` → `'a plain
  string'`; `_parse_frontmatter_value('true')` → `'true'` (no boolean
  branch exists in the real current file — `REQ-SB-30-US-01` referenced in
  this task's own Context has not actually landed in this codebase, per
  direct inspection; the raw-passthrough fallback correctly handles it,
  matching Step 2's own conditional "if the boolean branch already exists"
  phrasing). PASS, no regression.
- Step 3: real vault has 210 `Work/Emails/*.md` notes today (grown since
  the story's own 204-note count at spec time — expected, capture runs
  continuously). Sampled
  `2026-07-20-Involuntary Loss of Employment Insurance (ILOE)-5C830000.md`:
  `frontmatter["tags"]` reads back as the real list
  `['customer/core42', 'kind/emails']`, not a string. PASS.
- Step 4: `extract_wikilink_targets("some text [[Note A]] more text
  [[Note B]] end")` → `['Note A', 'Note B']`; no-wikilink body → `[]`.
  PASS.
- Step 5: real Meeting note
  `[Placeholder] Introducing PSS and Review Action Plan-2026-08-05-
  54B90000.md` has a `**Attendees:**` line; `extract_wikilink_targets`
  on its body returned `['Core42', 'mohamed.eltanany@core42.ai',
  'aalkindi@adnoc.ae']` — the real, already-written attendee wikilink
  targets. PASS.

All 5 non-AC smoke checks passed. No AC is tagged directly to this
foundational task (by design — see its own Tests block note).

`gate: clear` 2026-08-13 — no MUST-FLAG trigger fired (no material
assumption beyond the already-noted `Settings` field drift, which is a
read-only observation outside this task's files; no ADR change; no
escalation; every existing `_parse_frontmatter_value` branch unchanged).
