# Documentation Archive — 2026-08-20

Full pre-redesign copies of `MEMORY.md`, `CHANGELOG.md`, `Implementation/
Architecture/ADR.md`, and `Implementation/Architecture/architecture.md` —
archived, not deleted (`MEMORY.md`'s own "archive never delete" value,
carried forward here even while archiving `MEMORY.md` itself).

**Why:** operator decision, 2026-08-20, during the backend architecture
redesign (`Implementation/Plans/2026-08-20-backend-architecture-redesign.md`,
executing `ADR-059`). These 4 files had grown into a large, detailed record
of the *old* system — most of it describing the hand-built Agent/Skill/
Schedule/Approval orchestration layer now being replaced. Rather than carry
that weight forward into the new architecture, fresh minimal versions were
started at the original paths; anything from here that turns out to still
matter gets pulled back in deliberately, not by default.

**Still authoritative, NOT archived:** `BACKLOG.md`, `BUGS.md`,
`REVIEW-QUEUE.md`, `ESCALATIONS.md` — these track live, still-relevant
state (open bugs, pending review items) independent of the architecture
itself.

**Use this archive for:** looking up how or why something in the old
system worked, recovering a specific historical Decision/Pattern/
Constraint/ADR that turns out to still apply, or auditing what changed.
