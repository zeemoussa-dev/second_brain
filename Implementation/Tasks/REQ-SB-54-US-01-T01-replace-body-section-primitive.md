---
id: REQ-SB-54-US-01-T01
title: New `replace_body_section` header-scoped full-region regeneration primitive
parent_story: REQ-SB-54-US-01
requirement_id: REQ-SB-54
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-54-US-01-T01 — New `replace_body_section` header-scoped full-region regeneration primitive

## Parent Story

- Story: [[REQ-SB-54-US-01]] — `../UserStories/REQ-SB-54-US-01-vault-knowledge-model-redesign.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-54 *Vault Knowledge Model Redesign — Threads, Linked Meetings, Living Project & Customer Documents*

---

## Objective

Add `replace_body_section(path, header, new_content)` to `app/data_access/vault_writer.py` (`ADR-042` point 2): locates a `##`-level header line (e.g. `"## Glimpse"`) and the next `##`-level header (or end of file) that follows it, and replaces everything strictly between them — leaving every byte outside that bounded region (frontmatter, other sections, the header lines themselves) untouched, regardless of how many times the file has already been edited. This is the canonical mechanism for **every** full-regeneration write this story (and later `REQ-SB-57`) introduces — a Thread's `## Summary` (`T02`), a Customer/Project concept file's `## Glimpse`/`## Background` (`T04`/`T05`).

---

## Starting State → End State

**Before / Inputs:**
- No `vault_writer.py` primitive can regenerate a bounded region of an already-written note's body. `insert_body_line_if_missing` computes a fixed byte offset from the frontmatter's closing `---` — an already-documented fragility for a note touched many times over its life (`MEMORY.md`, `BUG-003`/`ESC-003`, `Open`).
- `_FRONTMATTER_LINE` (line 37) and the existing body-editing primitives (`insert_body_line_if_missing`, `replace_body_line`, `upsert_attendee_links`) are the closest real precedent for locating/rewriting a bounded region of a note's text — none of them are header-scoped.

**After / Outputs:**
- `replace_body_section(path, header: str, new_content: str) -> bool` exists in `vault_writer.py`. Returns `True` if `header` was found and its region replaced, `False` if `header` was not found anywhere in the file (no write performed).

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — add `replace_body_section`, placed alongside the other generic body-editing primitives (near `replace_body_line`, line ~969).

---

## Constraints

- Inherits from parent story: regenerate, don't patch, for anything meant to reflect current state — this primitive is the general mechanism that principle stands on.
- Locate `header` by an exact, literal line match (not a byte offset, not a cached position) — must work identically no matter how many times the file has already been edited.
- The "next `##`-level header" boundary means a line that is itself a `##`-headed section start (matching `^## ` at the start of a line) — a nested `###`/deeper subheader inside the same section is NOT a boundary; it stays part of the replaced region.
- If `header` is the LAST section in the file (no following `##`-level header), the replaced region correctly extends to end-of-file.
- If `header` is not found anywhere in the file, this is a no-op: return `False`, perform no write. Do not raise, do not create the section — mirrors this codebase's own established `insert_*_if_missing`-family "no-op is a valid, expected outcome" contract.
- Pure I/O, no business-layer judgement (`ADR-003`) — this primitive has no opinion about WHAT `new_content` should say; that decision belongs to whichever business-layer synthesis mechanism calls it (out of this story's own scope, `REQ-SB-57`'s job).
- Must not alter `insert_body_line_if_missing`/`replace_body_line`/any other existing primitive's own behavior — purely additive.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-54-US-01-AC-04] In a throwaway test file (`Path.write_text`, NOT a real vault note), write:
   ```
   ---
   type: "x"
   ---

   ## Glimpse

   old glimpse text

   ## Background

   background text
   ```
   Call `replace_body_section(path, "## Glimpse", "new glimpse text")`. Read the file back — confirm the region between `## Glimpse` and `## Background` now reads exactly `new glimpse text` (old text gone, no trace of it anywhere in the file), confirm `## Background`'s own content (`background text`) and the frontmatter block (`---\ntype: "x"\n---`) are byte-for-byte unchanged, confirm both header lines (`## Glimpse`, `## Background`) are preserved verbatim. Call `replace_body_section` a SECOND time on the SAME file with different content (`"newer glimpse text"`) — confirm it again replaces correctly (proving it works on a file already touched once, with no incremental/positional drift) and `## Background` is still untouched.
2. [REQ-SB-54-US-01-AC-04] Repeat against a file where `## Glimpse` is the LAST section (nothing follows it) — confirm the replacement correctly extends to end-of-file and the function does not error.
3. Call `replace_body_section(path, "## NoSuchHeader", "text")` against either test file above — confirm it returns `False` and the file is byte-for-byte unchanged (no write occurred).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `replace_body_section(path, header, new_content)` replaces exactly the region between `header` and the next `##`-level header (or EOF), leaving everything else byte-for-byte untouched.
- [x] Works correctly on repeated calls against the same file (no fixed-offset drift, no residue of prior content).
- [x] Returns `False` and performs no write when `header` is not found.
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint.
- [x] `CHANGELOG.md` entry appended.

---

## Out of Scope

- Any actual synthesis content (what Glimpse/Background/Summary text should say) — `REQ-SB-57`'s scope.
- Wiring this primitive into Thread/Customer/Project (`T02`/`T04`/`T05`, separate tasks).

---

## Context / Notes

Full reasoning: `Implementation/Architecture/ADR.md` → `ADR-042` point 2; `Implementation/Architecture/architecture.md` → "Vault Knowledge Model Redesign — Threads, Manual Captures, OKF-Conformant Customer & Project Directories". This is this story's own foundational primitive — `T02`, `T04`, and `T05` all depend on it.

Illustrative implementation shape (verify against the real current file before writing — `_FRONTMATTER_LINE`/existing helpers may have shifted line numbers since this was written):

```python
_SECTION_HEADER_PATTERN = re.compile(r"^## .+$", re.MULTILINE)

def replace_body_section(path, header: str, new_content: str) -> bool:
    text = path.read_text(encoding="utf-8")
    start = text.find(header)
    if start == -1:
        return False
    region_start = start + len(header)
    next_header_match = _SECTION_HEADER_PATTERN.search(text, region_start)
    region_end = next_header_match.start() if next_header_match else len(text)
    new_text = text[:region_start] + "\n\n" + new_content.strip("\n") + "\n\n" + text[region_end:]
    path.write_text(new_text, encoding="utf-8")
    return True
```

(Illustrative only — reconcile exact whitespace/newline handling against a real round-trip test; the locked AC cares about section-boundary correctness, not a specific blank-line convention.)

---

## Implementation Log

**Coder pass (2026-08-16).**

- Added `replace_body_section(path, header: str, new_content: str) -> bool`
  to `src/backend/app/data_access/vault_writer.py`, placed directly after
  `replace_body_line` (real line ~987 — shifted from the task's
  illustrative `~969` estimate by pre-existing unrelated content earlier
  in the file; purely a location shift, no scope change). A new local
  module-level pattern, `_BODY_SECTION_HEADER_PATTERN = re.compile(r"^## .+$",
  re.MULTILINE)`, sits immediately above it, mirroring this file's own
  established convention of defining a regex pattern local to the block
  that uses it (e.g. `_ATTENDEES_LINE_PATTERN` beside its own usage) rather
  than promoting it to the shared pattern block at the top of the file.
- **One deliberate refinement over the task's own illustrative code,
  logged as a scope-internal judgement call, not an escalation:** the
  illustrative snippet locates `header` via `text.find(header)` (a
  substring search, which would also match `header` as a mid-line
  fragment, e.g. `"## Glimpse"` inside a line reading `"### Old Glimpse Notes"`
  is NOT actually a risk given the `re.escape` line-anchor below, but a
  line like `"See ## Glimpse for details"` would false-positive under a
  raw substring search). The task's own Constraints section is explicit
  that header location must be "an exact, literal line match," so the
  real implementation locates `header` via
  `re.compile(r"^" + re.escape(header) + r"$", re.MULTILINE).search(text)`
  instead — the header must be the ENTIRE line, not merely a substring
  anywhere in the file. This is a tightening in favor of the task's own
  written constraint, not a deviation from it.
- Confirmed by direct reading that `insert_body_line_if_missing`,
  `replace_body_line`, and every other existing primitive in the file are
  byte-for-byte unmodified — this addition is purely additive, inserted
  as new code between two existing, untouched functions.

**Verification (manual mode — automated test tooling still pending, per
this task's own `Tests` section):**

- **[REQ-SB-54-US-01-AC-04]** Ran a throwaway script (not a real vault
  note) via the real backend venv
  (`src/backend/.venv/Scripts/python.exe`), importing the real
  `app.data_access.vault_writer.replace_body_section` unmodified from the
  real module (not a reimplementation) against a `tempfile.mkdtemp()`
  file. **Step 1 (first call):** wrote the exact fixture from the task's
  own `Tests` section (frontmatter + `## Glimpse` / `## Background`),
  called `replace_body_section(path, "## Glimpse", "new glimpse text")`.
  Observed: returned `True`; read-back text was
  `'---\ntype: "x"\n---\n\n## Glimpse\n\nnew glimpse text\n\n## Background\n\nbackground text\n'`
  — old text (`old glimpse text`) gone with no trace anywhere in the
  file; `## Background`'s own content (`background text`) and the
  frontmatter block (`---\ntype: "x"\n---`) byte-for-byte unchanged; both
  header lines (`## Glimpse`, `## Background`) preserved verbatim. **Step
  1 (second call, same file, different content):** called
  `replace_body_section(path, "## Glimpse", "newer glimpse text")` again
  on the SAME already-modified file. Observed: returned `True`; read-back
  text correctly showed `newer glimpse text` (no residue of `new glimpse
  text` or `old glimpse text`, proving no fixed-offset/positional drift
  across a second regeneration), `## Background`/`background text` still
  untouched. **Outcome: PASS**, both against the task's own literal
  fixture and an additional nested-`###`-subheader fixture (confirmed the
  nested subheader and its own content are correctly swallowed into the
  replaced region, not treated as a boundary — per the task's own
  Constraints wording).
- **[REQ-SB-54-US-01-AC-04]** Repeated against a second fixture where
  `## Glimpse` is the LAST section in the file (`## Background` comes
  first, `## Glimpse` last, nothing follows it). Observed: returned
  `True`, no exception raised; read-back text correctly extended the
  replacement to end-of-file
  (`...## Glimpse\n\neof glimpse text\n\n`), `## Background`'s own
  content untouched, frontmatter untouched. **Outcome: PASS.**
- **[unlabeled, Test step 3 — `False`/no-op contract]** Called
  `replace_body_section(path, "## NoSuchHeader", "text")` against BOTH
  fixtures above (the twice-regenerated file and the last-section file).
  Observed: both calls returned `False`; a direct before/after string
  comparison of the full file contents confirmed byte-for-byte identical
  — no write occurred on either fixture. **Outcome: PASS.**
- Regression check: confirmed via direct reading (not just absence of a
  diff) that `insert_body_line_if_missing`/`replace_body_line`/every
  other existing `vault_writer.py` primitive's own source is unchanged;
  `ast.parse` against the full file confirmed no syntax error was
  introduced.

No `ESCALATIONS.md`/`REVIEW-QUEUE.md` entries — no out-of-scope event,
no ambiguous requirement, all three locked-AC-tagged manual steps
verified with an observed `PASS` outcome. `MEMORY.md` and `CHANGELOG.md`
updated per project convention (see their own entries dated 2026-08-16
for this task).
