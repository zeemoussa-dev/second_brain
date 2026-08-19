---
id: REQ-SB-67-US-01-T01
title: New vault_writer.py primitive — replace_body_opening_line (REQ-SB-54 point 11's first real implementation)
parent_story: REQ-SB-67-US-01
requirement_id: REQ-SB-67
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-17
updated: 2026-08-17
---

# REQ-SB-67-US-01-T01 — New `vault_writer.py` primitive: `replace_body_opening_line`

## Parent Story

- Story: [[REQ-SB-67-US-01]] — `../UserStories/REQ-SB-67-US-01-real-thread-summary-synthesis-and-backfill.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-67 *Real Per-Thread Summary Synthesis + Existing-Thread Backfill*

---

## Objective

Add `vault_writer.replace_body_opening_line(path, new_line: str) -> bool` — a mechanical generalization of the existing `replace_body_section` primitive that regenerates a note's own "opening region" (between the end of its frontmatter block and its first `## `-level header) wholesale on every call, so a Thread note's body can carry a one-line "current state at a glance" sentence ahead of `## Summary` (`REQ-SB-54` point 11's first real implementation, scoped to Threads only by this story).

---

## Starting State → End State

**Before / Inputs:**
- `replace_body_section(path, header, new_content) -> bool` (`app/data_access/vault_writer.py`) — the existing header-scoped, full-region-replace primitive (`ADR-042` point 2): locates a GIVEN header's own line as the region start (`header_match.end()`), the next `## `-level header line (or end of file) as the region end, and rewrites everything strictly between them. No-ops (returns `False`, no write) when `header` isn't found.
- `_BODY_SECTION_HEADER_PATTERN = re.compile(r"^## .+$", re.MULTILINE)` — the shared header-location regex `replace_body_section`/`read_body_section` both already use; reuse this SAME compiled pattern, do not define a second one.
- `read_note`'s own frontmatter/body boundary convention: `text.find("\n---\n", 4)` locates the file's own SECOND literal `---` line (the frontmatter's closing delimiter) — the exact same boundary `insert_tags_line` already uses for its own surgical frontmatter insert. `_write_frontmatter_note` writes every note as `<frontmatter lines joined by "\n", ending in a bare "---"> + "\n\n" + <body>` — so on disk, the closing `---` line is immediately followed by exactly one blank line, then the body.
- `create_thread_note_baseline`'s own body literal is exactly `"## Summary\n\n## Transcript\n"` — no line precedes `## Summary` today; this primitive's own region, on a freshly-created Thread note, is genuinely empty (nothing between the frontmatter close and the first `## ` header).

**After / Outputs:**
- `replace_body_opening_line(path, new_line: str) -> bool` exists in `vault_writer.py`, placed near `replace_body_section`/`read_body_section` (same primitive family).
- Calling it against a note whose opening region is currently empty inserts `new_line` as the file's own first body line, immediately followed by a blank line, then the existing first `## ` header — unchanged.
- Calling it again against the SAME note with a DIFFERENT `new_line` wholly replaces whatever was there (no residue of the prior call's own text) — a true regenerate, never a patch or append, mirroring `replace_body_section`'s own "regenerate, don't patch" contract (`REQ-SB-54` point 8).
- Frontmatter and every `## `-level section (and everything inside it) is left byte-for-byte untouched by this primitive — it only ever rewrites the bounded opening region.
- Returns `False` (no write) only when the file has no parseable `"\n---\n"` frontmatter-closing boundary at all (a malformed note) — mirrors `read_note`'s own same guard; unlike `replace_body_section`, this primitive does NOT no-op when the target region is merely empty, since a note's own opening region always structurally exists (even blank) the moment its frontmatter is well-formed.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — add `replace_body_opening_line`, placed directly after `replace_body_section`/`read_body_section` (same primitive family, same file region).

---

## Constraints

- Inherits from parent story: **regenerate, don't patch** (`REQ-SB-54` point 8) — every call wholly replaces the opening region; never append/insert relative to prior content.
- **Do not modify `replace_body_section`, `read_body_section`, `_BODY_SECTION_HEADER_PATTERN`, `read_note`, `create_thread_note_baseline`, or `insert_tags_line`** — this task only ADDS one new function, composing the existing `_BODY_SECTION_HEADER_PATTERN` and the same `"\n---\n"` frontmatter-boundary convention `insert_tags_line` already uses. Read them, don't touch them.
- The new primitive must be **general** (any note kind with a well-formed frontmatter block), not hardcoded to Thread notes specifically — this task's own scope is the primitive; wiring it into `thread_match_merge` for Threads specifically is `T02`'s job (`depends_on: [REQ-SB-67-US-01-T01]`).
- `new_line` may itself be a multi-sentence or multi-line string on input (defensive) — strip any leading/trailing newlines before writing, mirroring `replace_body_section`'s own `new_content.strip("\n")` handling, so the written region always has exactly one blank line before and after it, regardless of what the caller passes in.
- No new dependency, no new file, no new mechanism family — this is an ADDITIVE sibling to `replace_body_section`, not a rewrite of it.

---

## Tests

**Manual verification steps:**

1. Against a throwaway scratch vault (`VAULT_PATH` env-overridden, per this codebase's own established `T01`/`T02`-style protocol — never the real configured vault for this primitive-level check), create a Thread note via `create_thread_note_baseline` (body starts as `"## Summary\n\n## Transcript\n"`, no opening line). Call `replace_body_opening_line(path, "Current state: the customer has not yet replied.")`. Confirm the resulting file's body begins with exactly that sentence, followed by a blank line, then `## Summary` unchanged immediately after — and confirm the return value is `True`.
2. Call `replace_body_opening_line(path, "A different, later sentence — the customer confirmed the invoice.")` a second time against the SAME note. Confirm the FIRST sentence's own exact text is now completely absent from the file (a real whole-region replace, not residue/duplication), the new sentence is now the opening line, and `## Summary`/`## Transcript` (and their own current content, if any) are byte-for-byte unchanged by this call.
3. Write some real content into `## Summary`/`## Transcript` first (via `replace_body_section`/`append_body_section_line`), THEN call `replace_body_opening_line` again. Confirm that content is completely untouched — the opening-line call never reaches past the first `## ` header.
4. Confirm the frontmatter block itself (`type`/`conversation_id`/`tags`/any other key) is byte-for-byte unchanged across all calls above — read frontmatter via `read_note` before and after, compare directly.
5. Malformed-note guard: call `replace_body_opening_line` against a `Path` whose file content has no `"\n---\n"` frontmatter-closing boundary at all (e.g. a bare text file with no frontmatter). Confirm it returns `False` and the file is left completely unwritten (byte-for-byte unchanged).
6. `ast.parse()` the full `vault_writer.py` file after the edit — confirm no syntax error, and confirm no line outside this new function was touched (diff the edit against the pre-edit file).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `replace_body_opening_line(path, new_line)` exists, regenerates the opening region wholesale on every call (steps 1–2).
- [x] Frontmatter and every `## `-level section stay byte-for-byte untouched (steps 3–4).
- [x] Malformed-note guard returns `False` with zero write (step 5).
- [x] No existing `vault_writer.py` function's own behavior changed (step 6).
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Wiring this primitive into `thread_match_merge` or generating the opening line's own real content via Compass — `T02`'s job.
- Any note kind other than Thread ever actually calling this primitive — `REQ-SB-54` point 11's rollout to Meeting/Project/Customer concept files is explicitly out of this story's own scope (see the parent story's `## Non-Goals / Out of Scope`); this task only builds the general-purpose primitive itself.
- The backfill's own use of this primitive — `T03`'s job (composes it, does not modify it).

---

## Context / Notes

Full reasoning: `Implementation/Architecture/architecture.md` → "Real Thread Summary Synthesis + Opening-Line + One-Shot Backfill (`REQ-SB-67`, extends `ADR-043`/`ADR-044`, no new ADR)", the "New `vault_writer.py` primitive for the opening line" bullet — read it directly before implementing; it names the exact boundary logic (frontmatter's own second literal `---` line as region start, first `## `-level header as region end) this task's own `Starting State → End State` restates above. Mirror `replace_body_section`'s own exact coding style (region-start/region-end via the shared header regex, `text[:region_start] + "\n\n" + content.strip("\n") + "\n\n" + text[region_end:]` shape) rather than inventing a differently-styled implementation — this primitive is deliberately "the same mechanism, a different region-start rule," not a new mechanism family.

---

## Implementation Log

**Coder pass, 2026-08-17.**

- Added `replace_body_opening_line(path, new_line: str) -> bool` to
  `src/backend/app/data_access/vault_writer.py`, inserted directly after
  `read_body_section` and before `append_body_section_line` (same
  primitive family, same file region, per this task's own placement
  instruction). Implementation composes the SAME shared
  `_BODY_SECTION_HEADER_PATTERN` `replace_body_section`/`read_body_section`/
  `append_body_section_line` already use, and the SAME `text.find("\n---\n",
  4)` frontmatter-boundary convention `insert_tags_line`/
  `insert_body_line_if_missing` already use — region start is `end + 6`
  (the TRUE body-start offset, past the closing `---\n` line plus the
  blank-line separator; matches `insert_body_line_if_missing`'s own
  documented `body_start = end + 6`, deliberately NOT `read_note`'s
  slightly different `end + 5` body slice, which includes an extra
  leading `\n` not wanted here). Region end is the first `## `-level
  header match from there, or end of file if none exists. `new_line` is
  `.strip("\n")`-ed before writing, mirroring `replace_body_section`'s
  own `new_content.strip("\n")` handling. Returns `False` (no write) only
  when no `"\n---\n"` boundary is found at all (malformed note) — does
  NOT no-op on an empty-but-present opening region, per this task's own
  spec (unlike `replace_body_section`'s no-op-if-header-absent contract).
  No existing function's own code was touched — purely additive (confirmed
  via `git diff`: the new function appears only as added lines, with zero
  `-` lines in its vicinity; the file's pre-existing, unrelated uncommitted
  diff from an earlier session was left completely untouched).

- **No AC tag of its own** — this task is pure infrastructure, per its own
  Objective/Out-of-Scope. `AC-02` (Scenario 2, the opening line) is a
  Job-level behavior only observable once `T02` wires this primitive into
  `thread_match_merge` (`depends_on: [REQ-SB-67-US-01-T01]`), per the
  decomposer's own AC → task verification mapping in the parent story's
  `## Notes`.

- **Verification — the task's own 6 manual `## Tests` steps, run directly
  against a throwaway `VAULT_PATH`-overridden scratch vault (never the
  real, configured vault — this codebase's own established T01/T02-style
  protocol for a primitive-level check with no locked AC of its own):**
  - **Step 1 (insert into an empty opening region):** PASS. Created a
    Thread note via `create_thread_note_baseline` (body starts
    `"## Summary\n\n## Transcript\n"`, no opening line). Called
    `replace_body_opening_line(path, "Current state: the customer has not
    yet replied.")`. Return value `True`. Resulting file body began with
    exactly that sentence, one blank line, then `## Summary` unchanged
    immediately after — confirmed via direct file-text inspection.
  - **Step 2 (wholesale replace, no residue):** PASS. Called
    `replace_body_opening_line` a second time with a different sentence
    ("A different, later sentence — the customer confirmed the
    invoice."). The FIRST sentence's exact text was completely absent
    from the resulting file (verified via substring-absence check); the
    new sentence became the sole opening line; `## Summary`/`## Transcript`
    unchanged in shape.
  - **Step 3 (real section content + a third call, untouched):** PASS.
    Wrote real content into `## Summary` (`replace_body_section`) and
    `## Transcript` (`append_body_section_line`), then called
    `replace_body_opening_line` a third time. Both real section contents
    were confirmed present, byte-identical, in the post-call file; the
    prior (2nd) opening line's own text was confirmed completely gone;
    the new (3rd) opening line was confirmed present ahead of `## Summary`.
  - **Step 4 (frontmatter byte-for-byte unchanged):** PASS. Read
    frontmatter via `read_note` after all three calls — `type`/
    `conversation_id`/`tags` all matched the originally-written values.
    Additionally diffed the frontmatter block's own raw text (minus the
    intentionally-differing `conversation_id` value) against a
    freshly-created control Thread note's frontmatter block: identical,
    line-for-line.
  - **Step 5 (malformed-note guard):** PASS. Called
    `replace_body_opening_line` against a bare text file with no
    frontmatter at all (`"Just a bare text file with no frontmatter at
    all.\n"`). Return value `False`; file content confirmed byte-for-byte
    unchanged (direct before/after string equality).
  - **Step 6 (no syntax error, purely additive):** PASS. `ast.parse()`
    against the full post-edit `vault_writer.py` succeeded with no
    exception; `git diff` confirmed every changed line in the file is an
    addition (`+`), none is a removal (`-`), in the vicinity of the new
    function.
  - Full verification script run:
    `.venv/Scripts/python.exe` against a scratch vault under this
    session's own scratchpad directory (created fresh, deleted after the
    run — never the real `VAULT_PATH` from `src/backend/.env`). All 15
    individual checks across the 6 steps printed `PASS`; script exited 0.

- **Assumption (scope-internal judgement call, logged per Pipeline.md hard
  rule 5, not an escalation):** the task's Starting State text describes
  `insert_tags_line`'s boundary convention generically as "the exact same
  boundary `insert_tags_line` already uses," but `insert_tags_line` itself
  computes its insertion point as `end + 1` (it inserts a frontmatter LINE
  just before the closing `---`, a different target than a body-start
  offset). The task's own more specific guidance elsewhere — "the closing
  `---` line is immediately followed by exactly one blank line, then the
  body" — and `insert_body_line_if_missing`'s own explicit inline comment
  ("body starts 6 chars later") together make `end + 6` the unambiguous,
  correct choice for a TRUE body-start offset (which this primitive needs,
  unlike `insert_tags_line`'s frontmatter-line insertion point). Used
  `end + 6`, confirmed correct by all 6 passing verification steps above.

- **`MEMORY.md` updated** — new `## Constraints` entry: this primitive
  inherits the same already-documented `body_start = end + 6` fixed-offset
  risk class as `insert_body_line_if_missing` (`ESC-003`, `Open`) — not a
  new risk this task introduces (the task's own spec directs this exact
  convention), but worth recording since `T02`/`T03` will call this
  primitive against real, already-captured vault Thread notes.

- **`CHANGELOG.md` updated** — new entry for
  `REQ-SB-67-US-01-T01`/`SPRINT-054`.

- `gate: clear 2026-08-17` — no MUST-FLAG trigger fired: no new
  dependency, no shared-interface change (purely additive new function),
  no ADR deviation, no unanticipated file (only `vault_writer.py` touched,
  exactly as scoped), no unclear/contradictory requirement (the one open
  boundary-offset question above was resolved by direct, unambiguous
  existing-code precedent, not a guess between live options). No
  `REVIEW-QUEUE.md`/`ESCALATIONS.md` entry written by this task.
