---
id: REQ-SB-82-US-05-T01
title: Person-note web-lookup Skill — one-time eligibility check + real-findings append
parent_story: REQ-SB-82-US-05
requirement_id: REQ-SB-82
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: []
created: 2026-08-25
updated: 2026-08-25
---

# REQ-SB-82-US-05-T01 — Person-note web-lookup Skill — one-time eligibility check + real-findings append

## Parent Story

- Story: [[REQ-SB-82-US-05]] — `../UserStories/REQ-SB-82-US-05-meeting-preparation-agent.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-82 *Cockpit Mechanics — Prep, Research, and Moderation*

---

## Objective

Build the Skill scripts the Meeting Preparation Agent uses to check whether
an attendee's Person note is still empty (past frontmatter) and, when it
is, append real web-lookup findings to it — never re-running once real
content exists.

---

## Starting State → End State

**Before / Inputs:**
- Person notes already exist (`REQ-SB-10`, Done) — this task never creates one, only reads/appends to an existing note.
- No Skill exists to check emptiness or append findings.

**After / Outputs:**
- `Hermes-Provisioning/skills/librarian/person-lookup/scripts/check_person_note_empty.py` — `python check_person_note_empty.py --note-path P`. Reads the note's own body (everything after the closing `---` frontmatter fence); prints `{"empty": true|false}`. Whitespace-only body counts as empty.
- `Hermes-Provisioning/skills/librarian/person-lookup/scripts/append_person_findings.py` — `python append_person_findings.py --note-path P --input-file F`, `F: {"findings": str}`. Appends the real findings text to the note's own body (mirrors `app/business/cockpit/notes.py::add_person_note`'s established append-only-to-an-existing-note shape — never creates a new note, never overwrites existing body content). Prints `{"appended": true}`.
- `Hermes-Provisioning/skills/librarian/person-lookup/SKILL.md` — documents when to call each script (check emptiness FIRST; only if empty, perform a real web lookup for the attendee, then append genuine findings; never call `append_person_findings.py` when nothing real was found).

---

## Files to Modify

- `Hermes-Provisioning/skills/librarian/person-lookup/scripts/check_person_note_empty.py` (new)
- `Hermes-Provisioning/skills/librarian/person-lookup/scripts/append_person_findings.py` (new)
- `Hermes-Provisioning/skills/librarian/person-lookup/SKILL.md` (new)

---

## Constraints

- Inherits from parent story.
- The one-time gate IS the plain body-emptiness check — no separate "already looked up" tracking field or file (`ADR-010`).
- `append_person_findings.py` never creates a new note (it errors honestly if the given path doesn't exist) and never overwrites/removes existing body content — append only.
- Neither script performs the web lookup itself — that is the calling agent's own real `web_search` tool call, per `ADR-010`; these scripts are purely mechanical (check, then append what the agent already found).
- Never fabricate: `append_person_findings.py` must never be called by `SKILL.md`'s own documented flow when the agent found nothing real.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-82-US-05-AC-02] Create a scratch Person note with only frontmatter, no body. Run `check_person_note_empty.py` — expect `{"empty": true}`. Run `append_person_findings.py` with real findings text — expect the note's body now contains that text, confirmed by reading the file directly.
2. [REQ-SB-82-US-05-AC-03] Run `check_person_note_empty.py` again on the SAME note (now has real content from step 1). Expect `{"empty": false}` — confirms a later scheduled run's own gate would correctly skip re-lookup. Also confirm this holds for a note whose real content was added by the USER (not this agent) — same honest `{"empty": false}` result, no distinction made between who added it.
3. Confirm `check_person_note_empty.py` on a note with only whitespace after frontmatter also reports `{"empty": true}` (not falsely "has content").

**Automated tests:** `n/a — test tooling pending (only src/backend/tests/test_health_check.py exists today)`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `check_person_note_empty.py` implemented per Constraints
- [x] `append_person_findings.py` implemented per Constraints (append-only, never creates)
- [x] `SKILL.md` authored, documenting the check-then-append flow and the never-fabricate instruction
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (n/a — see Implementation Log)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The scheduled scan/cron itself (`T02`).
- The real web `web_search` lookup call (the calling agent's own tool use, not this script).
- KB-lookup delegation to the Research Agent (`T02`).
- WhatsApp delivery and suppression learning (`T02`).

---

## Context / Notes

`ADR-010` and `app/business/cockpit/notes.py::add_person_note` (the
established append-only-to-an-existing-note precedent this task mirrors)
are the reference points — read `notes.py` before starting, but note this
task's scripts operate directly on the vault via file I/O (a Hermes Skill,
`ADR-002`'s "no backend process at runtime" pattern), not via Second
Brain's own HTTP API.

---

## Implementation Log

**Coder pass, 2026-08-25.** Built exactly the three files in `## Files to
Modify`. Scripts are self-contained (no import of Second Brain's backend
package) since they run as a Hermes Skill against the vault directly via
file I/O, per `ADR-002`'s "no backend process at runtime" pattern — mirrors
`research-kb-writer/scripts/write_research_doc.py`'s own established
shape (`--note-path`/`--input-file`, scratch JSON payload, plain
`argparse`, `{"...": ...}`/`{"error": str}` JSON on stdout, exit 0/1). The
frontmatter/body split in both scripts mirrors
`app/data_access/vault_writer.py::read_note`'s own `text.find("\n---\n",
4)` convention exactly (read, not imported — the Skill has no dependency
on the backend package).

**Scope-internal judgement call (for human spot-check):** the task's own
Objective/End-State text does not prescribe a body format for the
appended findings text (no header, no date-stamp line — unlike
`add_person_note`'s own `## Personal Notes` + dated-bullet convention,
which is a DIFFERENT, human-facing feature this task explicitly does not
touch). Appended the findings text verbatim, separated from any existing
body content by a blank line — simplest interpretation consistent with
"appends the real findings text to the note's own body" and with never
fabricating additional structure the task didn't ask for.

**AC verification (manual mode, per `Implementation/Pipeline.md`'s
verification-mode default — no automated test tooling exists yet beyond
`test_health_check.py`):**

- **[REQ-SB-82-US-05-AC-02]** Created a real scratch Person note
  (`Work/People/zz-scratch-person-lookup-t01@example.com.md`) with only
  frontmatter, no body, in the real, configured vault
  (`C:\myWorx\Moussa MD\Moussa Brain`). Ran `check_person_note_empty.py
  --note-path <that note>` via the backend's own `.venv` Python (no
  system-wide `python` resolvable on this host/session — same class of
  environment gap as prior sprints' `npx`/`node` findings, worked around
  by locating a real, already-installed interpreter rather than assuming
  none exists) — got `{"empty": true}`. Then ran
  `append_person_findings.py --note-path <same note> --input-file
  <scratch JSON: {"findings": "..."}>` — got `{"appended": true}`.
  Directly read the note file back afterward: its body now literally
  contains the findings text verbatim. **PASS**, both halves, both
  confirmed against the real file, not just the script's own reported
  result.
- **[REQ-SB-82-US-05-AC-03]** Ran `check_person_note_empty.py` again on
  the SAME note (now carrying the real content just appended above) — got
  `{"empty": false}`, confirming a later scheduled run's own gate would
  correctly skip re-lookup. Separately created a second real scratch note
  with body content written directly (simulating a user adding real
  content themselves, never touching `append_person_findings.py`) — same
  honest `{"empty": false}` result, confirming no distinction is made by
  who added the content. **PASS**, both halves.
- **Test item 3 (whitespace-only body):** created a third real scratch
  note whose body was only blank/whitespace lines after frontmatter — 
  `check_person_note_empty.py` correctly reported `{"empty": true}`, not
  falsely "has content". **PASS**.
- **Extra, disclosed beyond the task's own named steps:** ran
  `append_person_findings.py` against a path that does not exist —
  confirmed `{"error": "note does not exist: ..."}`, exit code 1, and
  `Test-Path` on that path stayed `False` afterward — the script never
  creates a note, matching the Constraints exactly.

All three real scratch notes were deleted from the real vault's
`Work/People/` immediately after verification — none left behind (this
project's own established discipline; confirmed via a post-cleanup
directory listing).

`MEMORY.md`: no entry added. This task's real technique/precedent
(self-contained Hermes-Skill script mirroring an established sibling
script's CLI/frontmatter-split contract) is already documented as a
pattern by `research-kb-writer`'s own prior task and by `ADR-002`/`ADR-010`
directly — nothing new emerged worth a fresh, standalone `MEMORY.md`
entry (per CLAUDE.md's "do NOT add empty or trivial entries").

gate: clear 2026-08-25 — no MUST-FLAG trigger fired (no new dependency, no
shared-interface change, no ADR deviation, no unanticipated file; the one
judgement call above is scope-internal, logged for spot-check per hard
rule 5, not an escalation). Every locked AC this task owns (`AC-02`,
`AC-03`) was verified live with a real positive result against the real
vault.

`REQ-SB-82-US-05` stays `Ready`/`In Progress` as appropriate — it is NOT
marked `Done` by this task; `T02` (the cron/profile) remains open.
