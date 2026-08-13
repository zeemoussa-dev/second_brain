---
id: SPRINT-005
title: Email notes wikilink to their sender's Person note (BUG-001 fix)
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "sprint retro drafted — human to skim and harvest Learnings.md"
phase: ""                          # bugfix sprint — no single phase; BUGFIX-NN stories carry no phase: (Pipeline.md hard rule 8's exception)
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~2 tasks, XS"    # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-11
started: "2026-08-11"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-11"            # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — who drives each transition:
     Draft       → product-owner assembles the sprint. Bidirectional link is written
                   at creation: every story listed here already has sprint: SPRINT-NNN.
     Ready       → product-owner advances Draft→Ready when grouping is CLEAR (gate: clear).
                   Ambiguous, oversized, or blocked grouping stays Draft + gate: flagged.
                   Adding a story to a Ready sprint AUTO-REVERTS it to Draft.
     In Progress → /implement-sprint has started. Coder sets this + records started:.
     Blocked     → external dependency is unmet. Record it under Dependencies.
     Done        → every story is Done and every DoD box is checked. Coder sets this,
                   records completed:, DRAFTS the retrospective, and sets gate: flagged
                   for the human to skim and harvest Learnings.md.
-->

# SPRINT-005 — Email notes wikilink to their sender's Person note (BUG-001 fix)

## Sprint Goal

Close `BUG-001`: give every Email note — going forward and via a one-time
retrofit over already-captured notes — an actual `[[PersonName]]` wikilink
to its sender's Person note, so Person notes show up as connected nodes in
Obsidian's graph/backlinks instead of disconnected dots.

---

## Grouping Rationale & Sizing

- **Why grouped:** Single-story sprint — `BUGFIX-01-US-01` is the only
  `Ready`, ungrouped story this pass (confirmed via a repo-wide scan of
  `Implementation/UserStories/*.md`: `REQ-SB-08-US-01` is `Draft`, not
  `Ready`, so it is not eligible; every other story is already `Done` and
  sprint-linked). Its two tasks form one acyclic dependency edge
  (`T02 → [T01]` — the retrofit calls the primitive T01 adds) implementing
  one cohesive fix (forward hook + backfill retrofit for the same
  Email→Person link gap). There is no partition question: one story, one
  small dependency chain, nothing to split across sprints without inventing
  an artificial cross-sprint edge through the middle of it (would
  contradict hard rule 7).
- **Sizing estimate:** ~2 tasks, XS — smaller than the ~4-tasks/S shape
  seen in SPRINT-001/002/004 (no new `data_access` primitive needed;
  `insert_body_line_if_missing`, `list_all_note_paths`, and `read_note` are
  all reused as-is), closer in shape to SPRINT-003's ~2 tasks/XS precedent
  (also two small, well-bounded tasks with one dependency edge). Both tasks
  mirror direct existing precedents verbatim per the architect's/
  decomposer's notes on the story itself (T01 mirrors
  `customer_hub_linking.link_note_to_customer_hub`'s shape; T02 mirrors
  `retrofit_customer_hub_links`'s/`retrofit_people_from_emails`'s batch
  shape and the existing `/poc/retrofit-*` endpoint pattern) — low novelty,
  low risk of rework.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-005 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [BUGFIX-01-US-01](../UserStories/BUGFIX-01-US-01-email-notes-wikilink-to-sender-person-note.md) | Email notes wikilink to their sender's Person note (forward fix + backfill retrofit) | — (bugfix, phase-agnostic) | Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** None.
- The story's own `## Dependencies` section confirms it is not blocked: the
  per-write Person-note creation hook (`app/business/people_extraction.py`,
  `REQ-SB-10-US-01`, Done — shipped in `SPRINT-004`) and the email-capture
  pipeline (`app/business/email_classification.py`, `REQ-SB-07-US-01`,
  Done — shipped in `SPRINT-001`) this fix wires into both already exist
  and work. No open blocker.
- T02 (the retrofit endpoint) runs live against the real, configured
  Obsidian vault (`VAULT_PATH`) — no fixture/mock environment, same as the
  `SPRINT-001`/`SPRINT-002`/`SPRINT-004` precedents. Not a sprint-blocking
  dependency, noted here for the coder's awareness going into
  `/implement-sprint`.

---

## Out of Scope

- The not-yet-built Meeting→Attendees wikilink — depends on `REQ-SB-08`
  (Meetings Capture Pipeline), which is still `Draft`/not built. Not part
  of this bug's scope, per the story's own Non-Goals.
- Any other note-relationship direction beyond Email→Person — no broader
  audit of every entity relationship is implied by this single-bug fix.
- Redesigning the People or Email note schemas — both are already
  resolved; this story only adds the missing link.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — n/a,
      no architectural fact changed (direct application of the already-Accepted
      inline-body-wikilink convention, per the architect's own pass note)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — n/a, no new ADR
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. The coder drafts this section and
sets gate: flagged. The HUMAN then skims it, approves, and copies anything under
"Patterns to carry forward" and "Antipatterns to avoid" verbatim (or expanded)
into Implementation/Learnings.md — that is the cross-sprint index future sprints
read. The retro here is a sprint-level snapshot; Learnings.md is the permanent
record. The coder does NOT write Learnings.md directly. -->

### Sizing accuracy

- **Estimated:** ~2 tasks, XS — **Actual:** 2 tasks, XS, both built and
  verified in one live session with zero rework, zero escalations, zero
  deviations from either task's `## Files to Modify` spec. **Takeaway:**
  spot-on. The estimate's own reasoning ("both tasks mirror direct
  existing precedents verbatim") held exactly — this is the second
  bugfix-shaped sprint sized this way and it landed exactly as predicted,
  reinforcing that "mirrors an existing precedent verbatim" is a reliable
  XS signal, not just an optimistic label.

### What worked

- **Reusing the unavoidable app-start capture side effect as a live test
  fixture, not just a known nuisance.** `MEMORY.md`'s standing constraint
  says every dev-server start fires a real capture run; rather than
  separately invoking `classify_recent_emails` in a throwaway shell to
  verify T01's going-forward half, starting the server for T02's endpoint
  verification produced a genuinely new captured email
  (`Rudra.Potturu@tadweer.ae`) that exercised the exact same code path
  live, for free, in the same session. One live session verified both
  tasks' AC-01 halves instead of two.
- **Preferring a naturally-occurring vault example over a throwaway note
  when one already exists.** AC-03 (blank `sender_email`) needed a note
  with no `sender_email` field; rather than writing a throwaway note
  under `Work/Emails/` (which the story's own Context/Notes permitted as
  a fallback), a real one already existed —
  `Work/Guides/Manual-Entry-Guide.md`. Using it meant zero cleanup risk
  and zero chance of leaving vault pollution behind, at no extra cost.
- **The retrofit's single live run closed the entire real backlog in one
  call** — 249 already-captured Email notes gained their missing
  `**Sender:**` wikilink in one `POST` (84 correctly skipped as
  non-Email/no-sender notes, 1 already handled by the forward hook that
  fired moments earlier in the same session). No batching, pagination,
  or partial-run logic was needed for a backlog this size.

### What didn't work

- Nothing of note. Both tasks mirrored direct existing precedents
  (`link_note_to_customer_hub`, `retrofit_customer_hub_links`,
  `retrofit_people_from_emails`, the `/poc/retrofit-*` endpoint shape)
  closely enough that there was no ambiguity to resolve and no dead end
  encountered during implementation or verification.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Verify a forward hook using the app-start capture side effect, not a
  separate manual invocation** — when a task's AC needs live proof a
  going-forward code path fires correctly, and the dev server is already
  being started for another verification step in the same task/sprint,
  let that unavoidable real capture run (per the standing app-start
  scheduler constraint) exercise it rather than duplicating the
  verification with a second manual call. One live event, two ACs
  covered.
- **Prefer a real, naturally-occurring vault example over a constructed
  throwaway note whenever the live vault already contains one** — search
  for the natural case first (even an unrelated note type, as long as it
  satisfies the AC's actual condition, e.g. "no `sender_email` field")
  before falling back to creating-and-deleting a fixture note. Zero
  cleanup, zero risk of an incomplete rollback leaving vault pollution.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- _(none identified this sprint — no friction encountered worth
  recording as an antipattern)_

### Open follow-ups

- The story's own Non-Goals flag the Meeting→Attendees wikilink
  direction as explicitly out of scope here, blocked on `REQ-SB-08`
  (still `Draft`). Not a follow-up from this sprint's own work — already
  tracked at the requirement level, noted here only so it isn't
  mistaken for a gap this sprint should have covered.
- `MEMORY.md`'s 2026-08-11 standing constraint (every referencing note
  must link out, checked in both directions) was applied surgically to
  this one bug; no broader audit of every other entity relationship was
  performed or is implied — if the operator wants one, that is new,
  separate forward work, not a follow-up owed by this sprint.

---

## Notes

gate: clear 2026-08-11 — no triggers fired for this grouping decision:
`BUGFIX-01-US-01` is the only story `Ready` with `sprint: ""` this pass, so
there is no partition question at all. Its two tasks form one acyclic
dependency edge (`T02 → [T01]`), not splittable without inventing an
artificial cross-sprint edge (would contradict hard rule 7). Not oversized —
smaller than every prior sprint's task count, and both tasks mirror direct
existing precedents per the decomposer's own notes on the story. Not
blocked — both tasks are `status: Ready`, the story itself is
`status: Ready, gate: clear`, and its own `## Dependencies` section
confirms both upstream mechanisms it reuses (`REQ-SB-07-US-01`,
`REQ-SB-10-US-01`) are already `Done`. No cross-sprint dependency was
introduced (`depends_on_sprints: []`). Phase rule: this is a bugfix-only
sprint (`BUGFIX-01-US-01` carries no `phase:`), which Pipeline.md hard rule
8 explicitly exempts from single-phase homogeneity — `phase:` left blank on
this sprint accordingly rather than forced to `MVP`/`P1`/`P2`. Advanced
`Draft → Ready`.

---

**Sprint assembled (2026-08-11):** 1 story, 2 tasks, `status: Ready`,
`gate: clear`. Eligible for `/implement-sprint`.

---

**Coder pass (`/implement-sprint`), 2026-08-11:** Built T01 then T02 in
dependency order, both `status: Done`, all three locked ACs
(`BUGFIX-01-US-01-AC-01/02/03`) verified live against the real,
configured vault. Story `status: Ready → Done`. `BUG-001` flipped
`In Sprint → Closed` in both `BUGS.md` and `BACKLOG.md`'s `## Bugs`
mirror. No `ESCALATIONS.md`/`REVIEW-QUEUE.md` entries — nothing blocked,
no out-of-scope event, no ambiguity. Sprint `status: In Progress → Done`,
`completed: 2026-08-11`. Retrospective drafted above; `gate: flagged` per
the standard sprint-wrap pattern so the human skims it and propagates any
patterns into `Implementation/Learnings.md`.
