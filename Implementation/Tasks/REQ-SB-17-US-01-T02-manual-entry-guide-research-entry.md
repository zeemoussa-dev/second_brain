---
id: REQ-SB-17-US-01-T02
title: Add the Research entry to the in-vault Manual Entry Guide note
parent_story: REQ-SB-17-US-01
requirement_id: REQ-SB-17
type: content
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-17-US-01-T01]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-17-US-01-T02 — Add the Research entry to the in-vault Manual Entry Guide note

## Parent Story

- Story: [[REQ-SB-17-US-01]] — `../UserStories/REQ-SB-17-US-01-research-notes-template-and-guide.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-17 *Research Notes (Books & Reads)*

---

## Objective

Add a fifth section to the existing in-vault guide note
(`Work/Guides/Manual-Entry-Guide.md`, authored by `REQ-SB-15-US-01`,
`Done`) explaining what a Research note is for and how to insert its
template — **additive only**, never editing or removing the four existing
sections that `Done` story wrote.

**This is vault-content authoring, not application code.** The path below
is vault-relative, resolved against `VAULT_PATH` in `src/backend/.env`.

---

## Starting State → End State

**Before / Inputs:**
- T01 has authored `Templates/Research.md`, which this guide entry
  describes and references by exact path/name.
- `Work/Guides/Manual-Entry-Guide.md` already exists with an opening
  paragraph naming "four note types," a "How to insert a template" section,
  and four `## <Type>` sections (Customer, Opportunity, Agreement,
  Consumption-Snapshot) — all from `REQ-SB-15-US-01`, `Done`.

**After / Outputs:**
- The guide note's opening paragraph now names "five note types," listing
  Research alongside the existing four.
- A new `## Research` section is appended after the existing
  `## Consumption-Snapshot` section, matching the same
  `**Folder:** ... · **Template:** ...` + short explanatory-paragraph shape
  the four existing sections use.
- The four existing sections and the "How to insert a template" numbered
  steps are byte-for-byte untouched otherwise.

---

## Files to Modify

<!-- Vault-relative path, resolved against VAULT_PATH in src/backend/.env
— not a src/backend or src/frontend path. -->

- `Work/Guides/Manual-Entry-Guide.md` (existing file — two additive edits):

  1. In the opening paragraph, change:
     ```markdown
     This vault has four note types you enter by hand — Customer, Opportunity
     (Pipeline), Agreement, and Consumption-Snapshot — one Obsidian template
     per type, all living in the `Templates/` folder. Automated email capture
     already creates and links Customer hub notes for you (see
     `Work/Customers/`); the other three types have no automated capture yet
     — you enter them here.
     ```
     to:
     ```markdown
     This vault has five note types you enter by hand — Customer, Opportunity
     (Pipeline), Agreement, Consumption-Snapshot, and Research — one Obsidian
     template per type, all living in the `Templates/` folder. Automated
     email capture already creates and links Customer hub notes for you (see
     `Work/Customers/`); the other four types have no automated capture yet
     — you enter them here.
     ```
     (Only the count and list change — "four"→"five", the type list gains
     "and Research", and "other three"→"other four". No other word in this
     paragraph changes.)

  2. Append, immediately after the existing `## Consumption-Snapshot`
     section (at the end of the file):
     ```markdown

     ## Research

     **Folder:** `Work/Researches/` · **Template:** `Templates/Research.md`

     One note per book summary or article/read worth memorizing — manual
     entry only, no automated capture. No `customer`/`company` link is
     expected or added; a book/read isn't inherently tied to a customer
     relationship, so this is a deliberate absence, not a missed link.
     Keep the body a distilled digest of your own takeaways/quotes, not a
     raw dump of the source material.
     ```

---

## Constraints

- Must remain at `Work/Guides/Manual-Entry-Guide.md` — deliberately outside
  `Templates/`, so it is never listed by Obsidian's "Insert Template"
  picker (ADR-006, unchanged).
- Must be **additive only** — the four existing sections, their content,
  and the "How to insert a template" section must not be removed or
  altered beyond the exact opening-paragraph count/list edit specified
  above.
- Must accurately describe T01's actual template file path
  (`Templates/Research.md`) and target folder (`Work/Researches/`).
- Must not describe or imply any customer/company link for Research notes
  — matching T01's own Constraints.
- No `src/backend`/`src/frontend` file may be touched by this task.

---

## Tests

<!-- The user opening this note "in Obsidian" is a manual human action;
verification here inspects the written file's content directly, the
observable proxy available to a coder subagent. -->

**Manual verification steps:**
1. [REQ-SB-17-US-01-AC-02] Read `Work/Guides/Manual-Entry-Guide.md` from
   the real vault. Confirm the opening paragraph now says "five note
   types" and lists Research alongside the existing four. Confirm a new
   `## Research` section exists, explaining what a Research note is for
   (book summaries and articles/reads worth memorizing) and when to use
   it, plus how to insert its template (via the shared "How to insert a
   template" section above it, referencing `Templates/Research.md` and
   `Work/Researches/` by exact name). Confirm the four existing sections
   (`## Customer`, `## Opportunity (Pipeline)`, `## Agreement`,
   `## Consumption-Snapshot`) and the "How to insert a template" numbered
   steps are present and unchanged from `REQ-SB-15-US-01-T02`'s original
   content.

**Automated tests:** `n/a — test tooling pending; this is vault content, not
application code, so no pytest/vitest coverage applies`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Guide note's opening paragraph names five note types, including
      Research
- [x] A new `## Research` section exists, explaining purpose and template
      usage
- [x] Folder/template names cited match T01's actual file exactly
      (`Templates/Research.md`, `Work/Researches/`)
- [x] The four pre-existing sections and the "How to insert a template"
      steps are unchanged
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The `Templates/Research.md` file itself — that is T01.
- Any `src/backend`/`src/frontend` code change — none is implied.
- A second, Research-specific guide note — the story's own Scoping
  decision extends the single existing guide note instead.

---

## Context / Notes

Read `Work/Guides/Manual-Entry-Guide.md`'s current real content before
editing, to confirm the opening paragraph's exact current wording and the
exact end-of-file position of the `## Consumption-Snapshot` section, so
both edits land precisely and nothing else in the file shifts. Use the
Edit tool for the opening-paragraph change (surgical, matches only the
specified sentence) and either the Edit tool (appending after the last
line) or a targeted append for the new `## Research` section — never a
full-file rewrite, to guarantee the four existing sections stay
byte-for-byte untouched.

---

## Implementation Log

**2026-08-11, coder.** Read `Work/Guides/Manual-Entry-Guide.md`'s current
real content first, then made exactly the two additive edits this task
specifies: the opening-paragraph count/list sentence ("four" -> "five",
"Research" added to the list, "other three" -> "other four" — no other word
changed), and a new `## Research` section appended immediately after the
existing `## Consumption-Snapshot` section, matching that section's own
`**Folder:** ... · **Template:** ...` + short-paragraph shape exactly.
Vault content only — no `src/backend`/`src/frontend` file touched.

**[REQ-SB-17-US-01-AC-02] verified, PASS.** Read the file back in full: the
opening paragraph now reads "five note types... Customer, Opportunity
(Pipeline), Agreement, Consumption-Snapshot, and Research"; the new
`## Research` section explains what a Research note is for (book summaries/
articles worth memorizing), states manual-entry-only, and cites
`Work/Researches/` and `Templates/Research.md` by exact name (matching
T01's actual output) — reachable via the shared "How to insert a template"
section above it. The four pre-existing sections (`## Customer`,
`## Opportunity (Pipeline)`, `## Agreement`, `## Consumption-Snapshot`) and
the "How to insert a template" numbered steps are present, unchanged from
`REQ-SB-15-US-01-T02`'s original content.

**Status:** `Done`. `gate: clear` — no new trigger fired.
