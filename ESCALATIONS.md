# ESCALATIONS

Append-only log of every backward pipeline step (re-spec, re-architect, re-plan)
and out-of-scope event. Never edit a resolved entry. Every resolved entry names a
concrete resolving artefact (story ID, ADR number, or commit hash).

Categories: `unclear-requirement | out-of-scope | new-dependency |
shared-interface-change | adr-deviation | unanticipated-file | oversized-story |
other`

<!-- Entry format:
## ESC-NNN: [Short description] — YYYY-MM-DD
**Category:** [category from list above]
**Trigger:** What caused the escalation
**Resolution:** What was decided
**Resolving artefact:** story-id / ADR-NNN / commit abc123
**Status:** Resolved | Open
-->

> **Emptied 2026-09-06 (operator-directed), starting a clean cross-device build.**
> This file carried 63 entries / 5,035 lines, 36 still `Open`, the oldest from
> 2026-08-11.
>
> **This one is a deliberate exception to the file's own rule.** It is designed
> append-only precisely so the record of backward steps survives; emptying it is
> the operator's call for a fresh build phase, not a change to that rule. The
> rule still stands for everything logged from here on.
>
> **Nothing is lost** — the full log is in git at `d64dcb4`:
>
> ```bash
> git show d64dcb4:ESCALATIONS.md
> ```
>
> **The next id is `ESC-063`.** Ids are never reused; the historical ones are
> still referenced from stories, tasks and ADRs.

---
