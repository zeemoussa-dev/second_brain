---
description: Interactively log a bug found through manual testing into BUGS.md (asks clarifying questions until the entry is complete). Not a /flow stage; no subagent.
argument-hint: [short title]
---

Capture a bug found through manual testing into the ledger. Full contract:
`Implementation/Pipeline.md` → "Bug tracking".

**Run this yourself on the main thread — do NOT spawn a subagent.** Capture is
interactive: a subagent runs cold and cannot ask you questions, and the whole point
of `/bug` is to remove ambiguity *now* so the eventual fix is correct.

**Arguments (positional, optional):** a short bug title. If omitted, ask for one.

Steps:

1. **Read `BUGS.md`** and compute the next `BUG-NNN` (max existing + 1; sequential,
   never reused). If `BUGS.md` does not exist yet, start at `BUG-001`.
2. **Ask clarifying questions** (use `AskUserQuestion` for the closed-choice ones)
   for anything missing or unclear — do not guess:
   - **Title** (if not given).
   - **Area** — `UI` or `Logic`.
   - **Severity** — `Blocker | Major | Minor | Cosmetic`.
   - **Screen / route** where it occurs.
   - **Repro steps** — the exact steps to reproduce.
   - **Expected** vs **Actual** behaviour.
   - **Screenshot path** (optional) for UI bugs.
   Keep asking until the entry is complete enough that someone else could reproduce
   and fix it.
3. **Append to `BUGS.md`:** add the index-table row (`BUG-NNN | Title | Area |
   Severity | Open | <today YYYY-MM-DD> | —`) **and** a `### BUG-NNN — <title>`
   subsection under `## Bug Details` (screen/route · repro · expected · actual ·
   screenshot path).
4. **Mirror into `BACKLOG.md`:** add the row to its `## Bugs` section
   (`BUG-NNN | Title | Area | Open | —`).
5. **Report:** the new `BUG-NNN`, its area/severity, and a one-line confirmation.
   Remind the user that fixing happens via `/triage` once they've collected a batch.

This command only ever creates `Open` bugs. It never writes a story, task, or
sprint, and it is not part of `/flow`.
