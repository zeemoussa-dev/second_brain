---
description: Batch chosen Open bugs into one Draft BUGFIX-NN-US-01 fix story (drives the analyst in triage mode). Standalone — not part of /flow; the resulting story flows through /plan-tasks → /plan-sprints → /implement-sprint.
argument-hint: [BUG-NNN …]
---

Turn a batch of `Open` bugs into a single bugfix story. Full contract:
`Implementation/Pipeline.md` → "Bug tracking" + the analyst's "Triage mode".

**Arguments (positional):** zero or more `BUG-NNN` ids (e.g. `BUG-007 BUG-009`).
**Bare** (`/triage`) = list all `Open` bugs from `BUGS.md` and ask the user to pick
the batch to fix together (keep the user in control of what's "fixed together").

Steps:

1. Resolve the batch: use the passed `BUG-NNN` ids, or (bare) read `BUGS.md`, list
   every `Open` bug, and ask the user which to include. Only `Open` bugs are
   eligible.
2. **Invoke the `analyst` subagent in triage mode** on that batch. It:
   - reads each chosen bug's index row + `## Bug Details`,
   - authors **one** `Draft BUGFIX-NN-US-01` story (next sequential `NN`) with **one
     untagged Gherkin scenario per bug** (each = that bug's regression criterion),
     `requirement_ids:` = the covered `BUG-NNN` ids, and **no `phase:`** (bugfix
     stories are phase-agnostic),
   - flips each covered bug `Open → In Sprint` and writes `Fixed by: BUGFIX-NN-US-01`
     in **both** `BUGS.md` and `BACKLOG.md`'s `## Bugs` mirror,
   - sets the story's `gate:` (`flagged` if any bug is ambiguous/contradictory).
3. **Halt with a summary:** the `BUGFIX-NN-US-01` story path, the bugs it covers,
   scenario count, and **explicitly anything written to `REVIEW-QUEUE.md` /
   `ESCALATIONS.md`**.

**Standalone:** `/triage` is **not** part of `/flow`. It produces a `Draft` story;
from there run `/plan-tasks` (or `/flow` / `/prep`) — those stages key off `status:`,
not how the story was created, so they advance the `BUGFIX-NN` story to `Done`
unchanged. The decomposer locks one AC per bug-scenario; the coder flips the covered
bugs to `Closed` when the story is `Done`. **No new agent** — `/triage` reuses the
analyst.
