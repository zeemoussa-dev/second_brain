---
id: REQ-SB-17-US-01-T01
title: Author the Research Obsidian core-Templates template
parent_story: REQ-SB-17-US-01
requirement_id: REQ-SB-17
type: content
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-17-US-01-T01 — Author the Research Obsidian core-Templates template

## Parent Story

- Story: [[REQ-SB-17-US-01]] — `../UserStories/REQ-SB-17-US-01-research-notes-template-and-guide.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-17 *Research Notes (Books & Reads)*

---

## Objective

Author the fifth Obsidian core-Templates-plugin template file
(`Templates/Research.md`), sibling to the four `REQ-SB-15-US-01` already
established, pre-filling the resolved Research schema field-for-field, with
a free-form body and deliberately **no** customer/company frontmatter
field, tag, or wikilink placeholder anywhere in the file.

**This is vault-content authoring, not application code.** No
`src/backend`/`src/frontend` file is touched by this task — the path below
is vault-relative, resolved against `VAULT_PATH` in `src/backend/.env` (the
coder reads that value, then writes the file directly at
`<VAULT_PATH>/Templates/Research.md` with the Write tool).

---

## Starting State → End State

**Before / Inputs:**
- `Templates/Customer.md`, `Templates/Opportunity.md`,
  `Templates/Agreement.md`, `Templates/Consumption-Snapshot.md` already
  exist (`REQ-SB-15-US-01`, `Done`), each using the `REPLACE_WITH_...`
  placeholder convention and the `{{title}}` core-Templates heading.
- `Templates/Research.md` does not yet exist.

**After / Outputs:**
- `Templates/Research.md` exists, vault-relative, matching the resolved
  Research schema field-for-field, with a free-form body and no
  customer/company link of any kind.

---

## Files to Modify

<!-- Vault-relative path, resolved against VAULT_PATH in src/backend/.env
— not a src/backend or src/frontend path. -->

- `Templates/Research.md` (new file):

  ```markdown
  ---
  type: Research
  title: REPLACE_WITH_TITLE
  author: REPLACE_WITH_AUTHOR
  tags: [kind/research]
  ---

  # {{title}}

  _Add your own summary, takeaways, and quotes below — a distilled digest
  of what you actually want to remember, not a raw dump of the source
  material._
  ```

  No `customer`/`company` frontmatter field, tag, or wikilink placeholder
  anywhere in this file — a deliberate absence (Scenario 4), not an
  oversight.

---

## Constraints

- Must use only Obsidian's **core** Templates plugin syntax (`{{title}}` —
  no Templater-style dynamic scripting), matching the four existing
  templates.
- Frontmatter keys/shape must match the resolved Research schema
  field-for-field (`Implementation/Plans/
  2026-08-10-vault-taxonomy-draft.md` → "Researches") — do not add, rename,
  or drop a key.
- `REPLACE_WITH_TITLE` / `REPLACE_WITH_AUTHOR` placeholders must remain
  valid YAML as-written (Scenario 3) — no placeholder may break frontmatter
  parsing.
- No customer/company frontmatter field, tag, or wikilink placeholder may
  be added anywhere in this file (Scenario 4, Constraints).
- Body must be free-form — no forced section headings.
- No `src/backend`/`src/frontend` file may be touched by this task.

---

## Tests

<!-- Obsidian's own "Insert Template" UI action is a manual human step this
coder subagent cannot drive interactively — verification here means
inspecting the written template file directly and cross-checking
field-for-field against the resolved schema. -->

**Manual verification steps:**
1. [REQ-SB-17-US-01-AC-01] Read `Templates/Research.md` from the real vault
   (`VAULT_PATH` in `src/backend/.env`). Confirm its frontmatter block
   parses as valid YAML and contains exactly `type: Research`, `title:`,
   `author:`, `tags: [kind/research]` — matching the resolved Research
   schema field-for-field. Confirm the body contains no forced section
   headings, ready for free-form user content.
2. [REQ-SB-17-US-01-AC-03] Confirm `title: REPLACE_WITH_TITLE` and
   `author: REPLACE_WITH_AUTHOR` (both left at their template-provided
   placeholder defaults) parse as valid YAML on their own — i.e. the
   frontmatter block is syntactically complete and correct with both left
   unfilled, not requiring them to be filled in for the block to parse or
   for the note to be otherwise well-formed.
3. [REQ-SB-17-US-01-AC-04] Confirm `Templates/Research.md` contains no
   `customer`/`company` frontmatter key, no `customer/<slug>` or
   `company/<slug>` tag, and no hub-note wikilink placeholder anywhere in
   the file — the deliberate absence Scenario 4 requires.

**Automated tests:** `n/a — test tooling pending; this is vault content, not
application code, so no pytest/vitest coverage applies`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `Templates/Research.md` exists at the vault root, matching the
      resolved schema field-for-field
- [x] `title`/`author` placeholders remain valid YAML as-written, unfilled
- [x] No customer/company frontmatter field, tag, or wikilink placeholder
      anywhere in the file
- [x] Body is free-form, no forced section headings
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The in-vault guide note's Research entry — that is T02.
- Configuring Obsidian's Settings → Templates → "Template folder location"
  — already a one-time completed step from `REQ-SB-15-US-01` (ADR-006).
- Any `src/backend`/`src/frontend` code change — none is implied.
- An optional `topic/<slug>` tag or any Topic/Industry note-type
  integration — out of scope per the story's own Non-Goals.

---

## Context / Notes

`REPLACE_WITH_TITLE` / `REPLACE_WITH_AUTHOR` follow the exact
`REPLACE_WITH_...` placeholder convention `REQ-SB-15-US-01-T01` already
established for the other four templates. The guide note (T02) explains
what to replace them with.

---

## Implementation Log

**2026-08-11, coder.** Authored `Templates/Research.md` in the real vault
(`VAULT_PATH = C:\myWorx\Moussa MD\Moussa Brain`) exactly per this task's
`## Files to Modify` spec, verbatim. Vault content only — no `src/backend`/
`src/frontend` file touched.

**[REQ-SB-17-US-01-AC-01] verified, PASS.** Read the written file back
(`vault_writer.read_note`); frontmatter is exactly `type: Research`,
`title: REPLACE_WITH_TITLE`, `author: REPLACE_WITH_AUTHOR`, `tags:
[kind/research]` — field-for-field match to the resolved schema. Body has
no forced section headings, free-form.

**[REQ-SB-17-US-01-AC-03] verified, PASS.** Parsed the frontmatter block
with a real YAML parser (`yaml.safe_load`) — `{'type': 'Research', 'title':
'REPLACE_WITH_TITLE', 'author': 'REPLACE_WITH_AUTHOR', 'tags':
['kind/research']}` — valid YAML with both placeholders left unfilled at
their template defaults.

**[REQ-SB-17-US-01-AC-04] verified, PASS.** Read the raw file text and
confirmed no `customer` or `company` substring appears anywhere in the
file — no frontmatter key, no tag, no wikilink placeholder.

**Status:** `Done`. `gate: clear` — no new trigger fired.
