Load the full working context at the start of a session — or any time context has
been lost. **Never rely on chat history; everything comes from files.**

**Arguments (positional):** an optional integer = how many recent `CHANGELOG.md`
entries to read. Bare (`/load-context`) = last **10**.

Do all of the following yourself (no subagents), in order:

1. **Refresh, then read `CLAUDE.md` (repo root).** Audit `CLAUDE.md` against the
   current repo state and apply corrections for any drift (stale ADR ranges,
   incorrect sprint statuses, wrong paths). This is a **correction pass, not a
   rewrite** — honour the Minimal-changes rule; preserve curated prose. Leave the
   file **uncommitted** for the human to review. Then read it in full.

2. **Read `MEMORY.md` (repo root) in full** — every Decisions, Patterns, and
   Constraints entry. These are atomic hard rules; they override defaults.

3. **Read the last N `CHANGELOG.md` entries** (newest at the bottom — append-only).
   N is the positional argument, default 10.

4. **Read the live pipeline surfaces:**
   - `REVIEW-QUEUE.md` — open gate-flags and escalation pointers awaiting action.
   - `ESCALATIONS.md` — note any **open** (unresolved) entries.
   - `Implementation/Pipeline.md` — the authoritative six-role pipeline contract.
   - `BACKLOG.md` — requirement → story coverage index; spot what still needs a story.

5. **Confirm back to the human** with a concise report:
   - **Loaded:** files read; CLAUDE.md corrections applied (name them) or "no drift".
   - **State:** current phase/status, where the pipeline stands (Draft/Ready/In
     Progress stories, Ready sprints), most recent CHANGELOG activity.
   - **Needs attention:** every open `REVIEW-QUEUE.md` item and unresolved
     `ESCALATIONS.md` entry.
   - **Missing / stale / contradictory:** anything expected but absent, internally
     inconsistent, or out of date (e.g. BACKLOG rows pointing at missing stories,
     CHANGELOG claims contradicted by the repo). Say "nothing found" if all is clean.

Read-only except for the CLAUDE.md correction pass. Make no other repo changes.
