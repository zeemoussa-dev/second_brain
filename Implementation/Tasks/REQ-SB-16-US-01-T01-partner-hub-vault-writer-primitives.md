---
id: REQ-SB-16-US-01-T01
title: Add Partner hub-note baseline primitives and generic rename/swap/replace primitives to vault_writer.py
parent_story: REQ-SB-16-US-01
requirement_id: REQ-SB-16
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-16-US-01-T01 — Add Partner hub-note baseline primitives and generic rename/swap/replace primitives to vault_writer.py

## Parent Story

- Story: [[REQ-SB-16-US-01]] — `../UserStories/REQ-SB-16-US-01-partner-hub-notes-and-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-16 *Partner Hub Notes & Graph Connectivity*

---

## Objective

Add the low-level file-I/O primitives `app/business/partner_hub_linking.py`
(T02) will orchestrate on top of: resolving/checking a partner's hub-note
path, creating a hub note's Partner-schema baseline for the first time,
topping up missing baseline frontmatter keys, deriving Partner tags, a
vault-derived `list_known_partners()`, and the three new **generic**
rename/swap/replace primitives ADR-009 calls for (a frontmatter-key rename,
a tags-list swap, a body-line-label replace), plus one small sibling —
a frontmatter-key removal — needed to drop `affiliate_of` when a Customer
hub note becomes a Partner hub note (Partner has no Affiliate concept).

---

## Starting State → End State

**Before / Inputs:**
- `vault_writer.py` already has the Customer hub-note baseline family
  (`hub_note_path`, `hub_note_exists`, `create_customer_hub_note_baseline`,
  `insert_frontmatter_key_if_missing`, `ensure_hub_note_baseline_frontmatter`,
  `insert_body_line_if_missing`) and `list_known_customers`/`tag_slug`/
  `build_tags`/`read_note`/`write_note`/`move_note_and_attachments`/
  `list_all_note_paths` — this task mirrors the first family for Partner and
  adds four new generic primitives beyond the existing insert-if-missing
  family.

**After / Outputs:**
- Ten new functions appended to `vault_writer.py`: `partner_hub_note_path`,
  `partner_hub_note_exists`, `build_partner_tags`,
  `create_partner_hub_note_baseline`,
  `ensure_partner_hub_note_baseline_frontmatter`, `list_known_partners`,
  `rename_frontmatter_key`, `remove_frontmatter_key_if_present`, `swap_tag`,
  `replace_body_line` — no existing function's behavior changed.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — append at the end of the
  file (after `ensure_person_note_baseline_frontmatter`):

  ```python
  _PARTNERS_SUBFOLDER = f"{_WORK_ROOT}/Partners"
  _PARTNER_HUB_NOTE_BASELINE_KEYS = ("type", "partner", "tags")


  def partner_hub_note_path(partner: str):
      """Resolves the vault-absolute path a partner's hub note lives (or
      would live) at — Work/Partners/<Partner>.md — mirroring
      hub_note_path exactly, for the Partner namespace (ADR-009)."""
      return settings.vault_path / _PARTNERS_SUBFOLDER / f"{_slugify(partner)}.md"


  def partner_hub_note_exists(partner: str) -> bool:
      return partner_hub_note_path(partner).exists()


  def build_partner_tags(partner: str) -> list[str]:
      """Mirrors build_tags's shape for the Partner tag namespace —
      partner/<slug> is deliberately never customer/<slug> (ADR-009,
      partner/<slug> and customer/<slug> are mutually exclusive)."""
      return [f"partner/{tag_slug(partner)}", "kind/partner"]


  def create_partner_hub_note_baseline(partner: str) -> str:
      """Creates a partner's hub note for the first time: baseline
      frontmatter (type/partner/tags — deliberately no affiliate_of,
      Partner has no Affiliate concept, ADR-009) plus the same
      auto-generated body stub convention create_customer_hub_note_baseline
      already uses. Always writes unconditionally, mirroring
      write_note()'s own contract — callers must check
      partner_hub_note_exists() first (app/business/partner_hub_linking.py
      does)."""
      return write_note(
          subfolder=_PARTNERS_SUBFOLDER,
          filename_stem=partner,
          frontmatter={
              "type": "Partner",
              "partner": partner,
              "tags": build_partner_tags(partner),
          },
          body=(
              f"# {partner}\n\n"
              "_Add your own overview, key contacts, and current focus "
              "below — this section is never programmatically rewritten "
              "once you do._\n"
          ),
      )


  def ensure_partner_hub_note_baseline_frontmatter(path, partner: str) -> list[str]:
      """Tops up an already-existing partner hub note with any of the
      three baseline frontmatter keys it is missing (type/partner/tags),
      mirroring ensure_hub_note_baseline_frontmatter's exact contract for
      Partner's shorter key set. Never touches a key already present or
      the body. Returns the list of keys actually inserted."""
      baseline_values = {
          "type": "Partner",
          "partner": partner,
          "tags": build_partner_tags(partner),
      }
      inserted: list[str] = []
      for key in _PARTNER_HUB_NOTE_BASELINE_KEYS:
          if insert_frontmatter_key_if_missing(path, key, baseline_values[key]):
              inserted.append(key)
      return inserted


  def list_known_partners() -> list[str]:
      """Dynamic, vault-derived replacement for a hardcoded partner list —
      mirrors list_known_customers()'s exact frontmatter-scan pattern,
      reading the `partner` field across every note instead of `customer`
      (ADR-009). Never hardcoded."""
      partners: set[str] = set()
      for path in list_all_note_paths():
          frontmatter, _ = read_note(path)
          partner = frontmatter.get("partner")
          if partner:
              partners.add(partner)
      return sorted(partners)


  def rename_frontmatter_key(path, old_key: str, new_key: str, new_value=None) -> bool:
      """Generic frontmatter-key rename for the Customer->Partner
      migration's idempotent retag scan (ADR-009 point 5): renames
      old_key to new_key, preserving the existing value unless new_value
      is given explicitly (used for the hub note's own `type: Customer`
      -> `type: Partner` value swap, where the key name itself doesn't
      change but the value does). No-op (returns False, no write) if
      old_key is not present in the note's frontmatter — this absence
      check is what makes a rerun a true no-op once a note has already
      been migrated. Scoped strictly to the frontmatter block (never the
      body), leaving every other line byte-for-byte untouched, mirroring
      insert_frontmatter_key_if_missing's surgical-insert contract."""
      frontmatter, _ = read_note(path)
      if old_key not in frontmatter:
          return False
      value = new_value if new_value is not None else frontmatter[old_key]
      text = path.read_text(encoding="utf-8")
      end = text.find("\n---\n", 4)
      if end == -1:
          return False
      frontmatter_block = text[: end + 1]
      rest = text[end + 1:]
      lines = frontmatter_block.splitlines(keepends=True)
      for i, line in enumerate(lines):
          match = _FRONTMATTER_LINE.match(line.rstrip("\n"))
          if match and match.group(1) == old_key:
              lines[i] = f"{new_key}: {_format_frontmatter_value(value)}\n"
              break
      path.write_text("".join(lines) + rest, encoding="utf-8")
      return True


  def remove_frontmatter_key_if_present(path, key: str) -> bool:
      """Sibling to insert_frontmatter_key_if_missing — drops a
      frontmatter key's line entirely if present. Used to drop
      affiliate_of when a Customer hub note is migrated to Partner, which
      has no Affiliate concept (ADR-009's hub-note rewrite step). Scoped
      strictly to the frontmatter block. No-op (False) if the key is
      already absent — idempotent by construction."""
      frontmatter, _ = read_note(path)
      if key not in frontmatter:
          return False
      text = path.read_text(encoding="utf-8")
      end = text.find("\n---\n", 4)
      if end == -1:
          return False
      frontmatter_block = text[: end + 1]
      rest = text[end + 1:]
      kept_lines = []
      for line in frontmatter_block.splitlines(keepends=True):
          match = _FRONTMATTER_LINE.match(line.rstrip("\n"))
          if match and match.group(1) == key:
              continue
          kept_lines.append(line)
      path.write_text("".join(kept_lines) + rest, encoding="utf-8")
      return True


  def swap_tag(path, old_tag: str, new_tag: str) -> bool:
      """Generic tags-list swap for the Customer->Partner migration's
      retag scan (ADR-009 point 5): replaces `"old_tag"` with `"new_tag"`
      within the note's frontmatter `tags:` line only — write_note/
      _format_frontmatter_value always render tags as a single-line
      `tags: ["a", "b"]` list, so a scoped, single-line string replace is
      equivalent to a structural list-element swap without needing a real
      YAML parser (read_note's own documented "not a general YAML parser"
      limitation). Never touches the body or any other frontmatter line.
      No-op (False) if old_tag is not present in that line — idempotent
      by construction."""
      text = path.read_text(encoding="utf-8")
      end = text.find("\n---\n", 4)
      if end == -1:
          return False
      frontmatter_block = text[: end + 1]
      rest = text[end + 1:]
      lines = frontmatter_block.splitlines(keepends=True)
      old_quoted = f'"{old_tag}"'
      new_quoted = f'"{new_tag}"'
      changed = False
      for i, line in enumerate(lines):
          match = _FRONTMATTER_LINE.match(line.rstrip("\n"))
          if match and match.group(1) == "tags" and old_quoted in line:
              lines[i] = line.replace(old_quoted, new_quoted)
              changed = True
              break
      if not changed:
          return False
      path.write_text("".join(lines) + rest, encoding="utf-8")
      return True


  def replace_body_line(path, old_line: str, new_line: str) -> bool:
      """Generic body-line-label replace for the Customer->Partner
      migration's retag scan (ADR-009 point 5): replaces the exact line
      old_line with new_line wherever it appears in the note (used to
      relabel an existing inline `**Customer:** [[Name]]` wikilink to
      `**Partner:** [[Name]]`). No-op (False) if old_line is not present
      — idempotent by construction, mirroring insert_body_line_if_missing's
      presence-check style."""
      text = path.read_text(encoding="utf-8")
      if old_line not in text:
          return False
      path.write_text(text.replace(old_line, new_line), encoding="utf-8")
      return True
  ```

---

## Constraints

- Inherits from parent story (ADR-003 layering; ADR-004's tag-not-folder
  pattern extended to Partner; ADR-009's exact Partner schema — no
  `affiliate_of`-equivalent key; idempotency is load-bearing since the
  migration this unblocks runs against the real live vault).
- This file lives in `data_access/` only — no business rules (which
  partner/customer, which note — that is T02/T03), no HTTP concerns.
- Must NOT modify any existing `vault_writer.py` function's behavior —
  additive only.
- `rename_frontmatter_key`, `remove_frontmatter_key_if_present`, `swap_tag`,
  `replace_body_line` must all be **generic** (no Partner-specific
  parameter or hardcoded string inside any of the four) — usable by any
  future migration of this same rename/replace shape, per ADR-009's
  explicit reasoning.
- `partner_hub_note_path()` must use the same `_slugify()`
  `hub_note_path()` applies, so a customer name and the same string used
  as a partner name always resolve predictably (needed for T02's move
  step, which resolves both paths for the same name).

---

## Tests

**Manual verification steps:**
1. [REQ-SB-16-US-01-AC-01] In a Python shell against the backend `.venv`
   (`.venv\Scripts\python.exe`, real configured `vault_path`), call
   `create_partner_hub_note_baseline("Verify-T01-Partner")`. Confirm a file
   is created at `Work/Partners/Verify-T01-Partner.md` with frontmatter
   `type: Partner`, `partner: "Verify-T01-Partner"`, `tags:
   [partner/verify-t01-partner, kind/partner]` — and **no** `affiliate_of`
   key anywhere in the file. Confirm `partner_hub_note_exists
   ("Verify-T01-Partner")` returns `True` and `partner_hub_note_path
   ("Verify-T01-Partner")` matches the file just written. Confirm
   `list_known_partners()` now includes `"Verify-T01-Partner"`. Delete the
   test file afterward (throwaway verification data).
2. Non-AC smoke check: on the same throwaway note, manually remove the
   `tags` frontmatter line, then call
   `ensure_partner_hub_note_baseline_frontmatter(path, "Verify-T01-Partner")`
   and confirm only the missing `tags` line is (re-)inserted — `type`/
   `partner` and the body are byte-for-byte unchanged. Re-run and confirm
   nothing changes the second time.
3. Non-AC smoke check (`rename_frontmatter_key`): on a throwaway note with
   `customer: "Verify-T01-Customer"` frontmatter, call
   `rename_frontmatter_key(path, "customer", "partner")`. Confirm the line
   becomes `partner: "Verify-T01-Customer"` (value preserved), every other
   line unchanged. Call it again and confirm it returns `False` (no-op,
   `customer` key now absent). Separately, call `rename_frontmatter_key
   (path, "type", "type", new_value="Partner")` on a note with `type:
   "Customer"` and confirm the line becomes `type: "Partner"`.
4. Non-AC smoke check (`remove_frontmatter_key_if_present`): on a throwaway
   note with `affiliate_of: ""`, call
   `remove_frontmatter_key_if_present(path, "affiliate_of")`. Confirm the
   line is gone, every other line unchanged. Call it again and confirm it
   returns `False`.
5. Non-AC smoke check (`swap_tag`): on a throwaway note with `tags:
   ["customer/verify-t01", "kind/person"]`, call `swap_tag(path,
   "customer/verify-t01", "partner/verify-t01")`. Confirm the tags line
   becomes `tags: ["partner/verify-t01", "kind/person"]`. Call it again
   with the same arguments and confirm it returns `False` (no-op).
6. Non-AC smoke check (`replace_body_line`): on a throwaway note whose body
   contains `**Customer:** [[Verify-T01]]`, call `replace_body_line(path,
   "**Customer:** [[Verify-T01]]", "**Partner:** [[Verify-T01]]")`. Confirm
   the line is replaced. Call it again with the same arguments and confirm
   it returns `False` (no-op) — the mechanism Scenario 6/7's idempotency
   depends on.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `partner_hub_note_path`/`partner_hub_note_exists`/
      `create_partner_hub_note_baseline`/`build_partner_tags` resolve to and
      create the exact schema from `architecture.md`'s "Partner Hub Notes &
      Mutually-Exclusive Company Taxonomy (REQ-SB-16)" section — no
      `affiliate_of` key
- [x] `ensure_partner_hub_note_baseline_frontmatter` tops up missing
      baseline keys only, never touches the body
- [x] `list_known_partners` is vault-derived (reads `partner` frontmatter
      across every note), never hardcoded
- [x] `rename_frontmatter_key`/`remove_frontmatter_key_if_present`/
      `swap_tag`/`replace_body_line` are each idempotent (a second call
      with identical arguments is a no-op) and generic (no Partner-specific
      literal inside any of them)
- [x] No existing `vault_writer.py` function's behavior changed
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Deciding which customer/partner to link, or the migration's move/scan
  orchestration — that is T02 (`partner_hub_linking.py`).
- Extending `people_extraction.py` — that is T03.
- The migration HTTP endpoint — that is T04.

---

## Context / Notes

`vault_writer.py` currently ends with
`ensure_person_note_baseline_frontmatter`; append the new
constants/functions directly after it, in the order shown above (each new
function references only prior functions in the file, no forward
references). No new imports are required — `settings`, `write_note`,
`build_tags`, `tag_slug`, `read_note`, `_slugify`, `_format_frontmatter_value`,
`_FRONTMATTER_LINE`, `insert_frontmatter_key_if_missing`, `_WORK_ROOT`,
`list_all_note_paths` all already exist in this module.

`remove_frontmatter_key_if_present` is one small addition beyond the three
generic primitives ADR-009's Decision text names explicitly (rename, tags
swap, body-line replace) — it is the natural, obviously-needed sibling to
`insert_frontmatter_key_if_missing` needed to literally implement
`architecture.md`'s explicit "the affiliate_of key is dropped" step for the
migrated hub note; it is equally generic (no Partner-specific literal), so
it does not narrow or contradict ADR-009's own reasoning.

---

## Implementation Log

**2026-08-11, coder.** Appended the ten functions verbatim, per this task's
`## Files to Modify` spec, to the end of `src/backend/app/data_access/
vault_writer.py`. Note: by the time this edit landed, the file already
contained additional, unrelated Meeting-note primitives (from the
concurrently-in-flight `SPRINT-006`/`REQ-SB-08` work) between
`ensure_person_note_baseline_frontmatter` and this task's own append point —
this task's ten functions still landed as the true tail of the file (after
that Meeting content, not interleaved with it), so "append at the end of the
file" is satisfied in spirit even though it's no longer immediately after
`ensure_person_note_baseline_frontmatter` by line number. No forward
references, no existing function touched — confirmed via `ast.parse` and a
function-count check (each of the ten new names defined exactly once).
Logged as a scope-internal observation, not an escalation — no file outside
`## Files to Modify` was touched, and no existing function's behavior
changed.

**[REQ-SB-16-US-01-AC-01] verified live** (Python shell,
`.venv\Scripts\python.exe`, real `VAULT_PATH`):
`create_partner_hub_note_baseline("Verify-T01-Partner")` created
`Work/Partners/Verify-T01-Partner.md` with `type: "Partner"`,
`partner: "Verify-T01-Partner"`, `tags: ["partner/verify-t01-partner",
"kind/partner"]`, no `affiliate_of` key. `partner_hub_note_exists(...)` ==
`True`; `partner_hub_note_path(...)` matched the written path exactly;
`list_known_partners()` included the new partner. Throwaway file deleted
afterward. **PASS.**

**Non-AC smoke checks (all PASS):**
- `ensure_partner_hub_note_baseline_frontmatter`: removed the `tags` line
  manually, called the function — only `tags` was re-inserted (returned
  `["tags"]`), `type`/`partner`/body byte-for-byte unchanged; a second call
  inserted nothing and left the file byte-identical.
- `rename_frontmatter_key`: `customer` -> `partner` on a throwaway note
  preserved the value, returned `True`; a second call returned `False`
  (no-op, key now absent). `type`/`type` with `new_value="Partner"` swapped
  the value in place as expected.
- `remove_frontmatter_key_if_present`: dropped `affiliate_of` cleanly,
  returned `True`; second call returned `False`.
- `swap_tag`: `customer/verify-t01` -> `partner/verify-t01` swapped in
  place within the `tags` line, returned `True`; second call returned
  `False`.
- `replace_body_line`: `**Customer:** [[Verify-T01]]` ->
  `**Partner:** [[Verify-T01]]` replaced in place, returned `True`; second
  call returned `False`.

All throwaway files (`Work/Partners/Verify-T01-Partner.md`,
`Work/_Verify/*`) deleted after verification — no residue left in the real
vault.

No new decision/pattern/constraint beyond what `MEMORY.md`'s existing
2026-08-11 Partner/ADR-009 entry and `ADR-009` itself already capture;
`MEMORY.md` not further amended by this task specifically (a combined
sprint-level entry is added once the whole sprint's outcome — including the
T04 blocker — is known).

**Status:** `Done`. `gate: clear` — no new trigger fired by this task in
isolation (the file was already `flagged` at the story level for ADR-009).
