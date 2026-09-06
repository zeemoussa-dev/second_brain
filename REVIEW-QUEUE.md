# REVIEW QUEUE

Live human inbox. Items here are awaiting a human decision before the pipeline can
proceed. Remove an item when it is resolved; add an `ESCALATIONS.md` entry if the
resolution involved a backward step.

<!-- Entry format:
- [ ] YYYY-MM-DD · **STORY-ID or SPRINT-ID** · one-line summary of what's needed
  Plain English: what's blocked, why, what the impact is if left unresolved.
  **What to do:** the concrete next step — command to run or decision to make.
  → `Implementation/UserStories/<file>.md` or `Implementation/Sprints/<file>.md`
-->

> **Emptied 2026-09-06 (operator-directed).** This file had grown to 9,101 lines
> / 612 KB carrying **134 unresolved items**, the oldest from 2026-08-10, and was
> not being read. An inbox nobody opens is worse than no inbox: agents kept
> flagging into it, and each flag read as "a human will decide this" when nobody
> would.
>
> **Nothing is lost.** The full contents are in git at `7db3968`:
>
> ```bash
> git show 7db3968:REVIEW-QUEUE.md
> ```
>
> The discarded items were mostly retro-harvest reminders, scope-internal
> judgement-call spot-checks, ADR reviews, and three design sign-offs — all
> against work that has since shipped.
>
> **The real issue is upstream, and is not fixed by emptying this.** Six agents
> and four commands write here (`analyst`, `architect`, `coder`, `decomposer`,
> `designer`, `product-owner`; `/design`, `/flow`, `/implement-sprint`,
> `/load-context`). They will refill it at the same rate unless either the
> MUST-FLAG triggers are narrowed, or this file is actually reviewed. If it fills
> up unread again, the flagging rules are what need changing — not this file.

