---
id: SPRINT-077
title: Meeting Moderator Roster Recommendation + Meeting Preparation Agent — the two substories that build on SPRINT-076's foundations
status: Done
gate: flagged
gate_reason: "sprint complete — both stories Done; flagged per the standing coder-drafts-retro convention so the human skims the retro and propagates patterns into Learnings.md. US-05-T02 also carries two disclosed, non-blocking scope-internal findings (Hermes memory-file routing; new-profile WhatsApp-pairing gap) — see its own Implementation Log."
phase: P2
depends_on_sprints: [SPRINT-076]
sizing_estimate: "~5 tasks, M"
created: 2026-08-25
started: "2026-08-25"
completed: "2026-08-25"
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

# SPRINT-077 — Meeting Moderator Roster Recommendation + Meeting Preparation Agent

## Sprint Goal

Build the two `REQ-SB-82` substories that consume `SPRINT-076`'s
foundations: the Meeting Moderator's "before you arrive" roster
pre-assembly (`US-03`, built on `US-01`'s persisted chat store) and the
Meeting Preparation Agent (`US-05`, built on `US-02`'s Research Agent).

---

## Grouping Rationale & Sizing

- **Why grouped:** both stories are real, task-level dependents of
  `SPRINT-076`'s own two stories — confirmed directly from the
  decomposer's own frontmatter, not re-derived: `REQ-SB-82-US-03-T02`
  `depends_on: [REQ-SB-82-US-03-T01, REQ-SB-82-US-01-T01,
  REQ-SB-82-US-01-T02]`; `REQ-SB-82-US-03-T03` `depends_on:
  [REQ-SB-82-US-03-T02, REQ-SB-82-US-01-T03]`; `REQ-SB-82-US-05-T02`
  `depends_on: [REQ-SB-82-US-05-T01, REQ-SB-82-US-02-T02]`. Per hard rule
  7, dependency-linked stories go in the same sprint or in ordered sprints
  with a `depends_on_sprints` edge — this sprint records that edge back
  onto `SPRINT-076` rather than contradicting the graph. `US-03` and
  `US-05` have no dependency on each other (confirmed: neither's task IDs
  appear in the other's `depends_on`), so they are grouped here purely
  because they share the same prerequisite sprint and both round out
  `REQ-SB-82`'s currently-`Ready` scope, not because of a direct edge
  between them.
- **Why NOT one combined sprint with `SPRINT-076`:** see `SPRINT-076`'s own
  Grouping Rationale — the full 10-task/4-story set sits past this
  project's own largest confirmed-accurate sizing precedent (9 tasks/L);
  splitting along the graph's real fault line (independent foundations
  first, their dependents second) keeps both sprints inside the proven
  ~5-task/M envelope. A disclosed sizing judgement call, not a
  dependency-graph requirement — reasoned openly rather than picked
  silently.
- **Sizing estimate:** ~5 tasks, M (`US-03`: 3 tasks; `US-05`: 2 tasks).
  `US-03-T03` (new "Recommended" frontend grouping) and `US-05-T02`
  (real, live cron/Hermes-profile provisioning, per the decomposer's own
  note) both carry real live-verification cost beyond code volume; expect
  those two to be the heaviest of the five.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-077 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-82-US-03](../UserStories/REQ-SB-82-US-03-meeting-moderator-roster-pre-assembly.md) | Meeting Moderator — recommends the right Experts (Customer + Domain matching) | P2 | Done |
| [REQ-SB-82-US-05](../UserStories/REQ-SB-82-US-05-meeting-preparation-agent.md) | Meeting Preparation Agent — twice-daily scan, one-time Person lookups, WhatsApp summary | P2 | Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** `SPRINT-076` (must be `Done` before
  `/implement-sprint` may start this sprint — its own `US-01`/`US-02`
  build the `chat_store`/`research-agent` this sprint's tasks depend on
  directly).
- Internal task order (within this sprint, per the decomposer's own
  `depends_on`): `REQ-SB-82-US-03-T01` → `T02` → `T03` (linear, plus the
  cross-sprint edges into `SPRINT-076` above); `REQ-SB-82-US-05-T01` →
  `T02` (linear, plus its own cross-sprint edge into `SPRINT-076`'s
  `US-02-T02`).
- `REQ-SB-82-US-03`'s own customer-match track additionally depends, IN
  PRACTICE (not via a formal task edge — `REQ-SB-83` has no story or task
  of its own), on the real, already-deployed Masdar/Adnoc/TAQA Customer
  Experts. Satisfied today; recorded here for visibility, not as a sprint
  gate (see `REQ-SB-82-US-03`'s own Context/`T01` for the full disclosure).

---

## Out of Scope

- `REQ-SB-82-US-01`/`REQ-SB-82-US-02` — built in `SPRINT-076`, this
  sprint's own prerequisite.
- `REQ-SB-82-US-04` (Meeting Moderator live routing + async research) —
  still `Draft`/`gate: flagged`; not `Ready`, so not eligible for any
  sprint yet. Once it clears its own flags and reaches `Ready`, it will
  need its own `depends_on_sprints` edge onto both `SPRINT-076`
  (persisted chat + Research Agent, both hard dependencies of `US-04`
  per that story's own Dependencies) and, if the routing mechanism ends
  up sharing any of this sprint's own moderator surface, possibly this
  sprint too — not decided here, left to a future `/plan-sprints` pass.
- Resolving `REQ-SB-82-US-02`'s own open `REQ-SB-63` placement-authority
  question, or `REQ-SB-82-US-03`'s own domain-match data-source question —
  both already resolved by the operator/architect ahead of `/plan-tasks`
  (see each story's own Notes); nothing left open for this sprint to
  re-decide.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — n/a, no new architectural fact this sprint beyond what the architect pass already recorded (`ADR-009`/`ADR-010`, already `Accepted` before this sprint's build began)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — n/a, no new ADR created during `/implement-sprint` itself (both `ADR-009`/`ADR-010` predate this sprint, from `/plan-tasks`)
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

- **Estimated:** ~5 tasks, M — **Actual:** 5 tasks, M — matched exactly
  (`US-03`: `T01`/`T02`/`T03` all `Done`; `US-05`: `T01`/`T02` both
  `Done`). The estimate's own reasoning (`US-03-T03`'s new frontend
  grouping and `US-05-T02`'s real, live cron/Hermes-profile
  provisioning would be the two heaviest tasks) held up — `US-05-T02`
  in particular carried the sprint's single largest real-world
  verification cost, not code volume (one checked-in declaration file
  vs. an entire live profile/cron/Skill-copy/gateway provisioning pass
  plus multi-session live-agent verification).

### What worked

- **Scoped, disposable scratch data for live-verifying a
  cron-scheduled, WhatsApp-notifying agent** (`US-05-T02`) — real
  Meeting/Person notes created, exercised through the real agent/real
  Skill/real relay, then fully cleaned up — proved every real mechanism
  (delegation, suppression memory, attendee gate, decision logic)
  without ever risking an uncontrolled real WhatsApp ping or a
  real-colleague Person-note mutation from a verification pass. Extends
  this project's own established "closest-to-real substitute, bounded,
  reversible" precedent to a genuinely proactive/notifying agent for
  the first time.
- **Cross-session (not just cross-turn) persistence proof for a
  learned-memory feature** — re-testing the suppression preference in a
  brand-new session with zero prior conversation turns (rather than
  just continuing the same session) turned "an entry appeared" into a
  real, load-bearing proof that the preference is genuinely durable and
  actually consulted on a later, independent run — exactly what AC-07
  needed proven.

### What didn't work

- **Assuming a named memory-file convention (`memories/USER.md`,
  cited directly in `ADR-010`) is the literal file Hermes' own
  "remember" tool will write to** — the real tool auto-routed the same
  instructed fact into a sibling file (`memories/MEMORY.md`) instead;
  both are equally real, always-injected, native per-profile memory, so
  the functional mechanism ADR-010 actually cared about (Hermes-native,
  not Second-Brain-owned) held up fine, but the exact filename named in
  an ADR/task shouldn't be assumed literally true without a live check.
- **A freshly-cloned profile's config/credentials inheriting from
  `default` does NOT include an inherited, already-paired platform
  connection** — WhatsApp needs its own real, human-interactive
  QR-pairing step per profile, discovered only once the new profile's
  gateway was actually started for real. A cron job can be perfectly
  registered/scheduled and still not fire unattended until that
  separate step is done.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Bounded, disposable scratch data (Meeting + Person notes, cleaned
  up after) is the correct default for live-verifying any NEW
  proactive/notifying agent** — never let a first-time live
  verification pass run unscoped against the real production data a
  scheduled agent would otherwise touch (real colleagues' Person notes,
  real customer meetings), even when the underlying mechanism is fully
  authorized to run for real in production going forward. Found live,
  `REQ-SB-82-US-05-T02`.
- **Re-verify a learned-memory feature's persistence in a genuinely
  fresh session, not just a continued one** — the only way to
  distinguish "remembered because it's still in this conversation's own
  context" from "actually durable, read back from disk on a later,
  independent run." Found live, `REQ-SB-82-US-05-T02`.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Trusting an ADR's own named implementation detail (a specific file
  path, a specific tool call shape) as ground truth without a live
  check, even when the ADR's own broader DECISION is correct** — an
  ADR can be right about the mechanism/architecture while still naming
  a specific file that isn't the one the real tool actually uses; verify
  the literal artefact live before reporting a locked AC's own exact
  wording as satisfied. Found live, `REQ-SB-82-US-05-T02` (`MEMORY.md`
  vs. `USER.md`).
- **Assuming a cloned Hermes profile is immediately ready for
  unattended, proactive delivery the moment its cron job is created** —
  a real platform pairing/connection step is a separate, human-gated
  prerequisite that doesn't clone along with config/credentials. Found
  live, `REQ-SB-82-US-05-T02`.

### Open follow-ups

- **Operator action needed, outside this pipeline's own reach:** pair
  WhatsApp for the real `meeting-prep-agent` Hermes profile
  (`hermes -p meeting-prep-agent whatsapp`, a real QR-code scan) so its
  already-correctly-registered `every 720m` cron job can actually start
  firing unattended. Filed here, not `REVIEW-QUEUE.md` (not a pipeline
  decision blocker — a one-time real-world setup action).
- **Worth a human decision, not urgent:** whether `SOUL.md` should be
  updated to explicitly instruct writing the suppression preference to
  `memories/USER.md` specifically (forcing the exact file `ADR-010`
  names) versus leaving it to Hermes' own auto-routing (functionally
  equivalent today, per the finding above) — no action taken this
  sprint, disclosed for awareness only.
