# BUGS.md

The append-only **source of truth** for bugs found through manual testing — UI
issues and logic issues alike. Detail lives here; `BACKLOG.md`'s `## Bugs` section
is a thin status mirror of the index table below.

- **Capture:** `/bug` (interactive — asks clarifying questions, then writes a row
  here at `Open`).
- **Fix:** `/triage` batches chosen `Open` bugs into one `BUGFIX-NN-US-01` story;
  that story then flows through `/plan-tasks → /plan-sprints → /implement-sprint`.
- **Full contract:** `Implementation/Pipeline.md` → "Bug tracking".

## Rules

- **Append-only.** Never delete a row or a detail subsection.
- `BUG-NNN` ids are **sequential and never reused** (even for `Won't Fix` bugs).
- This file is the source of truth; the `BACKLOG.md` `## Bugs` mirror is derived.
  Whoever changes a bug's status updates **both** in the same touch.
- **Area:** `UI | Logic`. **Severity:** `Blocker | Major | Minor | Cosmetic`.
- **Status:** `Open` (logged, no fix story) → `In Sprint` (a `BUGFIX-NN` story
  covers it, set at `/triage`) → `Closed` (covering story `Done`). Terminal:
  `Won't Fix` (with a reason in the detail subsection; never auto-set).
- A bug against already-`Done` work becomes **new forward work** (a `BUGFIX-NN`
  story), never a reopening of the original story.

---

## Index

| ID | Title | Area | Severity | Status | Found | Fixed by |
|---|---|---|---|---|---|---|

> **Emptied 2026-09-06 (operator-directed), starting a clean cross-device build.**
> This file carried 42 bugs / 2,054 lines, 19 of them still `Open` and the oldest
> from 2026-08-11 — against a codebase that has since been restructured
> (`ADR-019`), with several naming code that no longer exists (`graph.py::_call_model`,
> `_MIGRATION_GRANT_SEED`, `compass_client.classify_email`, `propose_person_note_update`
> are all gone). Re-verifying each against the current build would have cost more
> than re-finding whichever still reproduce.
>
> **Nothing is lost** — the full ledger is in git at `d64dcb4`:
>
> ```bash
> git show d64dcb4:BUGS.md
> ```
>
> **The next id is `BUG-043`.** Ids are sequential and never reused, so do NOT
> restart at 001: the historical ids above are still referenced from
> `BACKLOG.md`, sprints, and commit messages.
>
> This empties the ledger; it does not close the bugs. Anything still real will
> be found again by the build it affects, and logged fresh via `/bug`.

---
