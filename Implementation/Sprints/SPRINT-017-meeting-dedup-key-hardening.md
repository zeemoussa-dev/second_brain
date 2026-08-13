---
id: SPRINT-017
title: Replace EntryID with GlobalAppointmentID as the Meeting-occurrence dedup/filename key (ADR-013 hardening fix, resolves ESC-002)
status: Done                        # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "The live-discovered duplicate-note finding spot-checked and accepted 2026-08-12 — no longer a factor. Retrospective drafted below, awaiting human skim/harvest into Learnings.md."
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~1 task, XS"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-12
started: "2026-08-12"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-12"            # YYYY-MM-DD when status → Done
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

# SPRINT-017 — Replace EntryID with GlobalAppointmentID as the Meeting-occurrence dedup/filename key (ADR-013 hardening fix, resolves ESC-002)

## Sprint Goal

Build and live-verify `REQ-SB-08-US-01-T06`: replace Outlook `EntryID`
with `AppointmentItem.GlobalAppointmentID` as the Meeting-occurrence
dedup/filename disambiguator (per `ADR-013`), closing the live-confirmed
non-uniqueness risk `ESC-002` named, without regressing any of
`REQ-SB-08-US-01`'s 11 already-verified, locked ACs and without
migrating/renaming any of the 38 already-captured real Meeting notes.

---

## Grouping Rationale & Sizing

- **Why this needs its own new sprint:** `REQ-SB-08-US-01-T06` is a single,
  additive hardening task on `REQ-SB-08-US-01`, a story whose own sprint
  (`SPRINT-006`) is already `Done` and frozen (Pipeline.md hard rule 1 —
  a `Done` sprint is frozen the same way a `Done` story is). The task's
  own Notes name this directly: it needs the product-owner to assign it a
  new `SPRINT-NNN` at the next `/plan-sprints` pass before
  `/implement-sprint` can pick it up. `SPRINT-006` itself is not reopened
  or edited by this sprint's creation.
- **Why standalone rather than grouped with `BUGFIX-02-US-01`** (the other
  ungrouped item this pass): no shared file, module, or verification
  surface — this task is a backend-only Outlook calendar/vault-writer
  dedup-key fix (`outlook_com.py`, `vault_writer.py`,
  `meeting_classification.py`); `BUGFIX-02-US-01` is a frontend-only
  Agents Map layout/rendering fix. See `SPRINT-016`'s own Grouping
  Rationale for the same reasoning from that side. A single-task sprint is
  smaller than any prior sprint in this project, but nothing in
  Pipeline.md sets a minimum sprint size, and forcing an artificial
  pairing purely to avoid a small sprint would be a cohesion-free grouping
  — not a genuine dependency/shared-surface/cohesion reason, per this
  role's own grouping drivers.
- **Sizing estimate:** ~1 task, XS — smaller than `SPRINT-003`'s/
  `SPRINT-005`'s own ~2-task XS precedent (the smallest sprints to date);
  one self-contained task (`depends_on: []`), touching three already-
  existing files with a fully worked, line-level implementation already
  specified in the task file itself.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-017 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-08-US-01](../UserStories/REQ-SB-08-US-01-meeting-notes-from-calendar-capture.md) | Meeting notes from calendar capture — **scope note: this sprint covers only the additive `T06` hardening task below; the story's own original scope was already delivered and verified in `SPRINT-006` (Done)** | P1 | Done |

**Task in scope:** [[REQ-SB-08-US-01-T06]] — Replace `EntryID` with
`GlobalAppointmentID` as the Meeting-occurrence dedup/filename key
(`Implementation/Tasks/REQ-SB-08-US-01-T06-global-appointment-id-dedup-key-fix.md`).
This sprint does **not** reopen `REQ-SB-08-US-01`'s own `status:` (stays
`Done`) or reword any of its 11 locked ACs — per the task's own Constraints
and Pipeline.md hard rule 1.

---

## Dependencies / External Blockers

- **Depends on sprints:** None.
- `ADR-013` (supersedes `ADR-008` point 2) is `Accepted` — operator
  approved as written, `REVIEW-QUEUE.md` 2026-08-12 ("Operator approved
  `ADR-013` as written. `gate:` reset to `clear`. `T06` eligible for
  `/plan-sprints`."). No open ADR review blocks this sprint.
- **Frontmatter/`REVIEW-QUEUE.md` discrepancy, noted not silently
  resolved:** `REQ-SB-08-US-01-T06`'s own file frontmatter still literally
  reads `gate: flagged` (`gate_reason: "trigger-3 (ADR-013 created)...
  needs a new sprint at the next /plan-sprints pass"`) — it was not
  re-edited after the operator's 2026-08-12 approval recorded in
  `REVIEW-QUEUE.md`. Editing a task's own frontmatter is outside the
  product-owner's role (Forbidden: tasks). Grouping proceeds on the
  authority of `REVIEW-QUEUE.md`'s own explicit, dated resolution ("gate:
  reset to clear... T06 eligible for /plan-sprints"), which is this
  project's live human-decision record — the stale field on the task file
  itself is a bookkeeping gap for the coder/human to close (e.g. syncing
  the task's own frontmatter to `gate: clear`), not a live blocker to this
  grouping decision.
- No new external-integration surface — reuses the same live Outlook COM/
  vault mechanism `SPRINT-006` already built and verified.

---

## Out of Scope

- Migrating/renaming the 38 existing Meeting notes or rewriting
  `processed_meeting_ids.json`'s existing entries — explicitly rejected,
  `ADR-013` point 3.
- Any change to `people_extraction.py`, `customer_hub_linking.py`, or
  `app/scheduling/capture_scheduler.py`.
- Closing the narrow residual risk `ADR-013`'s Consequences section names
  (a genuinely new occurrence landing on the same date as one of the 38
  pre-fix notes, sharing that series' stale `EntryID`) — an accepted,
  bounded trade-off of the coexistence design.

---

## Definition of Done

- [x] The task's own Acceptance Criteria all pass (verified live against
      the real Outlook calendar and vault)
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact
      (already done at the `ADR-019` architect pass — "Occurrence dedup
      key" bullet rewritten to match; unchanged by this coder pass)
- [x] `ADR-013` stays `Accepted` for point 3; points 1/2 `Superseded by
      ADR-019` (already recorded at the architect pass; unchanged here)
- [x] `MEMORY.md` updated with this new decision/pattern
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [x] `ESCALATIONS.md` → `ESC-002` **and** `ESC-012` flipped to `Resolved`
      once this task's own live regression checks passed
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

- **Estimated:** ~1 task, XS — **Actual:** 1 task, but built (and
  live-verified) **three separate times** across this sprint's own
  lifetime: once against `ADR-013` (`Blocked`, `ESC-012` found), once at
  the `ADR-019` architect redesign (docs/ADR only, no code), and this
  final pass rebuilding the code against `ADR-019` and live-verifying it
  successfully. **Takeaway:** a single-task, XS-sized sprint can still
  legitimately take multiple full build-and-verify passes when the task's
  own subject matter is "does an external system's documented guarantee
  actually hold on this installation" — task *size* (files touched, lines
  changed) stayed genuinely XS the whole time; it was the *number of
  attempts* needed to find a design that survives live testing that grew,
  which `sizing_estimate:`'s single number doesn't capture. Future
  sprints hardening an external-system assumption that has already failed
  once should budget for "maybe more than one design iteration," not just
  "small code diff."

### What worked

- **Choosing a structural, not empirical, uniqueness guarantee ended the
  cycle.** Two consecutive designs (`ADR-008`'s `EntryID`, `ADR-013`'s
  `GlobalAppointmentID`) each trusted an Outlook-documented "guaranteed
  unique" claim, and each was independently live-falsified on this one
  real installation. `ADR-019`'s design (hash of `subject` + the
  occurrence's own precise start timestamp) needed no live COM
  re-verification of its own core premise at all, because the premise is
  a fact about what makes two calendar occurrences distinct in the first
  place, not a claim about any one vendor API's behaviour — this is why
  this pass's own live verification of the hashing/tiering *mechanism*
  passed cleanly with zero surprises on the uniqueness question itself.
- **Re-inventorying the real vault fresh at the start of this session,
  rather than trusting the prior session's own "39 notes" count,** is
  what surfaced the honestly-flagged 40th-note finding before it could
  silently corrupt the verification's own conclusions — a `Get-ChildItem`
  count-and-compare at session start, before writing any code, cost
  almost nothing and caught a real discrepancy the task file's own spec
  (written the prior session) could not have anticipated.
- **A read-only dry run (`resolve_meeting_note_path` with no
  `create_meeting_note_baseline` call) confirmed a predicted side effect
  before triggering it for real** — used to verify, without mutating the
  live vault, that the stray 40th note would not be recognized by either
  new tier before running the actual mandated mutating verification step,
  turning a "maybe this creates a duplicate" worry into a documented,
  confirmed, bounded fact ahead of time rather than a surprise discovered
  only after the fact.

### What didn't work

- **A CSV export/import round-trip for a before/after `LastWriteTime`
  comparison produced a false "everything changed" result**, from
  12-hour-vs-24-hour date-format drift introduced by the round-trip
  itself, not a real file mutation — caught by re-parsing both sides to
  real `DateTime` objects before drawing any conclusion, but it cost an
  extra verification pass and could have been avoided by comparing
  `DateTime` objects directly from the start rather than persisting
  through an intermediate string format.
- **Two consecutive design attempts (`ADR-008`→`ADR-013`) each assumed a
  vendor's own documented uniqueness guarantee would hold, without a way
  to test it except by shipping and live-verifying** — the real cost here
  wasn't code, it was two full Blocked→redesign cycles before landing on
  a design that didn't need that kind of empirical trust at all. Worth
  asking "does this key's uniqueness rest on trusting an external
  system's documentation, or on a fact that's true by construction?" at
  design time, before the first live-verification pass, for any future
  external-identity-as-dedup-key decision.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Prefer a structural uniqueness guarantee over an external system's
  documented-but-untested one for any dedup/identity key** — a claim like
  "two things cannot logically be identical by definition" (e.g. two
  distinct calendar occurrences cannot share an identical start instant)
  needs no live re-verification against a specific environment; a claim
  like "this vendor API property is guaranteed unique" does, and can fail
  silently until tested against real production data. When a design
  choice comes down to picking between the two, the structural one is
  worth the (often small) extra reasoning to construct, because it closes
  the entire class of "works in docs, not on this installation" risk
  permanently rather than just moving it to a different field.
- **Re-inventory real external state fresh at the start of any
  live-verification session that resumed after a gap, rather than
  trusting a prior session's own recorded count** — a real, scheduler-
  driven pipeline keeps running on its own between sessions (`ADR-005`);
  a task/ADR's own "N real notes exist" snapshot is only true as of when
  it was written.
- **Use a read-only dry run to confirm a predicted mutating side effect
  before triggering the real mutating call**, especially against live
  production data — cheap, avoids surprises, and turns "I think this will
  happen" into "I confirmed this will happen" before it's irreversible.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Comparing timestamps after a lossy round-trip (e.g. CSV export/
  import) instead of comparing native `DateTime` objects directly** — the
  round-trip's own format conversion can introduce apparent differences
  that have nothing to do with the real underlying data, producing a
  false positive that looks exactly like a real finding until you dig
  into it.

### Open follow-ups

- The honestly-flagged 40th-note / mid-session-reschedule duplicate —
  filed as a `REVIEW-QUEUE.md` spot-check item (`REQ-SB-08-US-01-T06 /
  SPRINT-017` entry, 2026-08-12 update), not a new `ESCALATIONS.md` entry
  or a blocker — human should delete/merge the one stale note by hand.
- `ADR-013`'s own honestly-named residual risk (a genuinely new occurrence
  landing on the exact same date as one of the 39 pre-`ADR-013` notes,
  sharing that series' stale `EntryID`) is unchanged by `ADR-019` — still
  open, still bounded, still only closeable by a full migration neither
  ADR undertakes. Not new to this sprint; recorded here only so it isn't
  mistaken for closed by this sprint's own completion.

---

## Notes

**gate: clear 2026-08-12** — no MUST-FLAG trigger fired: (1) no material
assumption — this sprint's own scope is read directly off the task file's
own already-fully-specified implementation; the gate-status question was
resolved by direct citation of `REVIEW-QUEUE.md`'s own dated operator
approval, not guessed; (2) `REQ-SB-08` is not `<!-- Draft -->`; (3) N/A
(product-owner does not touch ADRs — `ADR-013` was already `Accepted`
before this pass); (4) no new `ESCALATIONS.md` entry written by this pass
(`ESC-002` stays `Open`, to be flipped `Resolved` by the coder once `T06`
is built and live-verified, per its own Notes); (5) not oversized (the
smallest possible unit — one task), not `Blocked` (the operator's approval
already clears the one real blocker), no cross-sprint dependency
introduced (`depends_on_sprints: []`); (6) N/A (coder trigger); (7) no
contradictory inputs — the stale `gate: flagged` on the task's own
frontmatter is a bookkeeping gap, not a contradiction with
`REVIEW-QUEUE.md`'s own more-recent, more-authoritative resolution,
explicitly noted above rather than silently overridden; (8) not
genuinely ambiguous — single-task sprint, no real alternative partition.
Advances `Draft → Ready`.

**Sprint assembled (2026-08-12):** 1 story (additive task only), 1 task,
`status: Ready`, `gate: clear`. Eligible for `/implement-sprint`.

---

**Coder pass (`/implement-sprint`), 2026-08-12 — `status: In Progress`,
`gate: flagged` (trigger-6).** `REQ-SB-08-US-01-T06` was built exactly per
its own fully-specified `## Files to Modify`. Live verification against
the real Outlook calendar/vault found `ADR-013`'s own core premise
(`GlobalAppointmentID` is unique per occurrence) is **false** on this
Outlook installation, for the exact real recurring series `ESC-002`
originally found broken for `EntryID` — full detail in `T06`'s own
Implementation Log and `ESCALATIONS.md` → `ESC-012` (new). Everything
independent of that falsified premise (the SHA-256-hash filename-suffix
mechanism, the legacy-`EntryID`-path coexistence/no-duplicate check, zero
mutation of any of the 39 real pre-existing Meeting notes) is built
correctly and verified live-passing. `T06`'s own `status:` is set
`Blocked`, not `Done`. Per this role's own sprint-wrap rule ("if anything
is blocked, leave the sprint `In Progress` and flag the blocked list"):
this sprint stays `In Progress`, not `Done` — no retrospective is drafted
this pass, since the sprint's single task did not reach a verified,
unblocked completion. `REVIEW-QUEUE.md` carries the human decision point
needed to resume (`REQ-SB-08-US-01-T06 / SPRINT-017` entry, 2026-08-12).
`BACKLOG.md`'s `SPRINT-017` Status cell is set to `In Progress` to match.

---

**Coder pass (`/implement-sprint`), 2026-08-12 (resumed after the
`ADR-019` architect redesign) — `T06` rebuilt exactly per `ADR-019` and
live-verified against the real Outlook calendar/vault. `status: Done`.**
The real recurring series that triggered `ESC-002`/`ESC-012` now produces
6 structurally-distinct filename suffixes for its 6 real occurrences —
the exact clause that failed under the superseded `ADR-013` design now
passes cleanly, with no live-uniqueness-dependent finding possible this
time. Zero of the 39 originally-named pre-existing Meeting notes touched.
`ESCALATIONS.md` → `ESC-002` and `ESC-012` both flipped fully `Resolved`.
One honestly-flagged, non-blocking live discovery from this same
verification pass (a pre-existing 40th Meeting note, created between
sessions by the then-still-live old code, plus an independent mid-session
calendar reschedule, together producing one real, bounded, recoverable
duplicate note outside the 39 named notes) is documented in full in
`T06`'s own Implementation Log and in the `REQ-SB-08-US-01-T06 /
SPRINT-017` `REVIEW-QUEUE.md` entry — not a task blocker, per the
established `SPRINT-014` "document, flag, don't block" pattern. Per this
role's own sprint-wrap rule, every story in this sprint is now `Done` and
nothing is `Blocked`: sprint `status: Done`, `completed: "2026-08-12"`,
`gate: flagged` for the human to skim this Retrospective and harvest
`Implementation/Learnings.md`. `BACKLOG.md`'s `SPRINT-017` Status cell is
set to `Done` to match. `REQ-SB-08-US-01`'s own `status:` and
`SPRINT-006`'s own `status:` are both left untouched (`Done`), per this
task's own explicit instruction and Pipeline.md hard rule 1.
