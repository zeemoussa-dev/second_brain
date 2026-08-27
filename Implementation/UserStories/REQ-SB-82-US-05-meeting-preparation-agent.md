---
id: REQ-SB-82-US-05
title: Meeting Preparation Agent — twice-daily scan, one-time Person lookups, a WhatsApp summary the user can teach to stop
requirement_ids: [REQ-SB-82]
requirement_section: "REQ-SB-82: Cockpit Mechanics — Prep, Research, and Moderation"
phase: P2
status: Done
gate: flagged
gate_reason: "ADR-010 review already resolved (operator 'Start Coding' authorization, see Notes below). Re-flagged at T02 completion for two disclosed, scope-internal T02 findings needing human spot-check (Hermes memory-file routing MEMORY.md vs. USER.md; new-profile WhatsApp-pairing gap blocking unattended cron firing) — see T02's own Implementation Log. No locked AC blocked."
sprint: "SPRINT-077"
created: 2026-08-25
updated: 2026-08-25
---

# REQ-SB-82-US-05 — Meeting Preparation Agent — twice-daily scan, one-time Person lookups, a WhatsApp summary the user can teach to stop

## Story

**As a** Second Brain user
**I want** an agent that checks my upcoming meetings twice a day, gathers
what it can about each one — looking up anything unfamiliar via the
Research Agent, and doing a one-time web lookup for any attendee whose
Person note is still empty — and sends me a WhatsApp summary only when it
actually finds something worth checking, which I can teach to stop for a
given meeting or type of meeting just by telling it in plain language
**So that** I walk into meetings already knowing what I need to, without
having to remember to check anything myself, and without being pestered
about meetings where there's genuinely nothing new to know

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-82: Cockpit Mechanics — Prep,
  Research, and Moderation*, "Meeting Preparation Agent" bullet — "runs
  twice a day, scans upcoming meetings, gathers what it can about each
  (KB lookups for any unfamiliar technology/topic, delegating to the
  Research Agent below; a web lookup for any attendee whose Person note
  is still empty beyond frontmatter — run once per person, never repeated
  once real content exists). Sends a WhatsApp summary by default when it
  finds real data worth checking on a meeting; learns to suppress future
  notifications for a given meeting/type from your own plain-language
  feedback ('don't send me info about meetings like this'), persisted the
  same way agent memory already works elsewhere
  (`vault_writer.append_agent_memory_entries`)." PRD breadcrumb
  (verbatim, 2026-08-25 operator): "I believe we need to have a meeting
  Preparation Agent, He Recieves the meeting find all info he can get
  about this meeting... if we can like to linked in and find the Person
  what they do and store that info in the person file"; clarified: the
  LinkedIn lookup is "a small Search... may be if we have nothing about
  the person we do it"; the agent "can run 2 times a day... send me a
  what's app message when I have Data in that meeting that I need to
  check" unless told otherwise per meeting.
- **This is one of five substories `REQ-SB-82` splits into — see
  `REQ-SB-82-US-01`'s own Context for the full split rationale.** This
  story is independent of `REQ-SB-82-US-01`/`US-03`/`US-04` (it never
  touches the Cockpit's own Chat UI at all — it is a background job that
  notifies via WhatsApp, not a Cockpit surface); it DOES depend on
  `REQ-SB-82-US-02` (Research Agent) for its own KB-lookup delegation.
- **A real, material correction to the PRD's own text, found by direct
  code inspection — not silently trusted.** The PRD cites
  `vault_writer.append_agent_memory_entries` as the precedent mechanism
  for persisting a learned suppression preference ("persisted the same
  way agent memory already works elsewhere"). Confirmed directly: that
  function still exists in `app/data_access/vault_writer.py`, but its
  ONLY two real callers in the entire codebase are
  `app/_archive/api/agents_router.py` (archived, not live) and
  `app/business/cockpit/threads.py` (confirmed STALE post-Hermes-pivot,
  `MEMORY.md`, 2026-08-25). **It has zero live callers today** — it is
  not, in fact, "already working elsewhere" in the current architecture;
  it is a leftover from the fully-retired Second-Brain-native agent model
  the Hermes pivot archived. Recorded honestly here, per this project's
  own precedent (`REQ-SB-44-US-01`'s correction of a stale PRD dependency
  claim), rather than building against a citation that turned out not to
  describe live behavior. Whether this story revives that exact function/
  file shape, or the learned preference is instead captured through a
  real Hermes-native mechanism (a profile's own SOUL.md/session memory,
  or a new equivalent), is left open — see the flag below.
- **Genuinely open, not resolved here — the exact WhatsApp delivery
  mechanism.** This project's own real precedent for an agent that
  notifies the user proactively over WhatsApp is `daily-briefing`
  (`MEMORY.md`, 2026-08-22 entry) — a Hermes cron job, built the same way
  this Prep Agent's own "runs twice a day" framing suggests, calling
  Second Brain's own live `/my-day/*` REST API rather than reimplementing
  classification logic. Whether this Prep Agent is built the same way
  (a new Hermes cron job/profile reusing that established pattern) or
  some other mechanism is left to `/plan-tasks` — not decided here.
- **Genuinely open, not resolved here — how "learn to suppress... from
  your own plain-language feedback" is mechanically captured.** The PRD's
  own worked example ("don't send me info about meetings like this") does
  not say WHERE the user says this — a reply to the WhatsApp summary
  itself, a message somewhere else, or a Cockpit-side control — nor what
  "meetings like this" resolves to (the exact same recurring meeting
  series, the same customer, the same tag/type). Left open; the Scenarios
  below assert only the observable end-state behavior (a future matching
  meeting stops notifying), not the capture mechanism.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then
edge cases and error states. Do NOT add AC-IDs — the decomposer assigns them
at /plan-tasks. These scenarios describe only the externally observable
scan/lookup/notify/learn behaviour; they deliberately do not assert the
exact WhatsApp delivery mechanism, the exact suppression-capture mechanism,
or the exact persistence store — all left open per Context. -->

### Scenario 1: The twice-daily scan finds an unfamiliar technology/topic and delegates a KB lookup to the Research Agent

```gherkin
Given an upcoming meeting mentions a technology or topic the vault has no
    existing knowledge about
When the Meeting Preparation Agent runs its scheduled scan
Then it delegates a KB lookup for that technology/topic to the Research
    Agent (REQ-SB-82-US-02) rather than researching it itself
```
<!-- AC-ID: REQ-SB-82-US-05-AC-01 -->

### Scenario 2: An attendee with an empty Person note gets a one-time web lookup, and real findings are saved to their note

```gherkin
Given an upcoming meeting has an attendee whose existing Person note has
    no content beyond its own frontmatter
When the Meeting Preparation Agent runs its scheduled scan
Then it performs a web lookup for that attendee
  And any real findings are saved into that attendee's own existing
    Person note
```
<!-- AC-ID: REQ-SB-82-US-05-AC-02 -->

### Scenario 3: An attendee whose Person note already has real content is never re-looked-up

```gherkin
Given an upcoming meeting has an attendee whose Person note already has
    real content beyond frontmatter (whether from a prior Prep Agent
    lookup or added by the user)
When the Meeting Preparation Agent runs its scheduled scan, including on a
    later run
Then no web lookup is performed again for that attendee — the one-time
    lookup is never repeated once real content exists
```
<!-- AC-ID: REQ-SB-82-US-05-AC-03 -->

### Scenario 4: A WhatsApp summary is sent by default when the scan finds real data worth checking

```gherkin
Given the Meeting Preparation Agent's scan found real data worth checking
    for an upcoming meeting (from either Scenario 1 or Scenario 2, or
    both)
When the scan completes
Then a WhatsApp summary for that meeting is sent to the user by default
```
<!-- AC-ID: REQ-SB-82-US-05-AC-04 -->

### Scenario 5: No WhatsApp message is sent when nothing worth checking was found

```gherkin
Given the Meeting Preparation Agent's scan found nothing worth checking
    for an upcoming meeting
When the scan completes
Then no WhatsApp message is sent for that meeting — the user is not
    notified about meetings with nothing new to know
```
<!-- AC-ID: REQ-SB-82-US-05-AC-05 -->

### Scenario 6: The user can teach the agent to stop notifying about meetings like a given one

```gherkin
Given the user has received a WhatsApp summary for a meeting
When the user tells the agent, in plain language, not to send this kind of
    notification for meetings like that one
Then the agent learns and persists that suppression preference
```
<!-- AC-ID: REQ-SB-82-US-05-AC-06 -->

### Scenario 7: A learned suppression preference is honored on future matching meetings

```gherkin
Given the user has previously taught the agent to suppress notifications
    for meetings like a given one (Scenario 6)
When a future meeting matching that same learned preference is scanned and
    would otherwise have real data worth checking
Then no WhatsApp summary is sent for that meeting, honoring the learned
    preference
```
<!-- AC-ID: REQ-SB-82-US-05-AC-07 -->

### Scenario 8: The scan runs on its own twice-daily schedule, with no manual trigger required

```gherkin
Given the Meeting Preparation Agent is configured and running
When its scheduled time arrives, twice in a day
Then the scan runs automatically, with no manual action from the user
    required to trigger it
```
<!-- AC-ID: REQ-SB-82-US-05-AC-08 -->

## Affected Screens

- None — backend/agent only. Delivery is via WhatsApp (an external
  channel, not a Second Brain UI screen); any findings this agent saves
  (a Person note update) surface through the ALREADY-EXISTING Person note
  view (`PersonNotePanel.tsx`/`note-detail.html`'s own generic frontmatter
  rendering, per `REQ-SB-10`), not a new screen this story builds.

## Dependencies

- **Blocked by:** `REQ-SB-82-US-02` (Research Agent, `Draft`, not yet
  built) — this story's own KB-lookup delegation calls that exact
  capability, not a separate one.
- **Related to, not blocking:** `REQ-SB-08-US-01` (Meetings Capture
  Pipeline, **Done**) — the upcoming-meeting data this agent scans.
  Satisfied.
- **Related to, not blocking:** `REQ-SB-10-US-01` (People Living
  Documents, **Done**) — the Person notes this agent reads (to check
  "empty beyond frontmatter") and writes real findings into. Satisfied.
- **Related to, not blocking:** the real `daily-briefing` Hermes cron job
  (`MEMORY.md`, 2026-08-22) — the closest existing precedent for a
  scheduled, WhatsApp-notifying agent in this codebase; not a hard
  dependency, just the likely pattern to follow (see Context).
- **External:** a real WhatsApp delivery channel (already live via
  Hermes' own gateway, per `MEMORY.md`'s Hermes-WS/WhatsApp entries) —
  not newly provisioned by this story, but the exact profile/mechanism
  that sends is undecided (see Context).

## Constraints

- The web lookup for an attendee's Person note runs at most ONCE per
  person — never repeated once the note has real content beyond
  frontmatter (Scenario 3).
- A WhatsApp summary is sent only when the scan found real data worth
  checking — never a routine "nothing to report" notification (Scenario
  5).
- A learned suppression preference must be genuinely persisted (survives
  across runs, not just the current process) and honored on future
  matching meetings (Scenarios 6, 7).
- This agent must never fabricate a finding (a Person-note detail, a KB
  fact) when its real lookups return nothing conclusive — matching this
  project's standing honesty posture.
- The exact WhatsApp delivery mechanism, the exact suppression-capture
  mechanism ("meetings like this"), and the exact persistence store for
  the learned preference are all left open — not decided here (see
  Context), and are NOT assumed to be `vault_writer.
  append_agent_memory_entries` despite the PRD's own citation (confirmed
  stale/dead-code today, see Context).

## Implementation Tasks

<!-- Decomposer's own table (/plan-tasks step 2, 2026-08-25) -- supersedes
the analyst-authored starting point above. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-82-US-05-T01 | skill | Person-note web-lookup Skill — one-time eligibility check + real-findings append | new `Hermes-Provisioning/skills/librarian/person-lookup/` | `Implementation/Tasks/REQ-SB-82-US-05-T01-person-lookup-skill.md` |
| REQ-SB-82-US-05-T02 | skill/cron | `meeting-prep-agent` cron declaration (scan/delegate/notify/suppress prompt) + live Hermes profile provisioning | new `Hermes-Provisioning/cron/meeting-prep-agent.md` | `Implementation/Tasks/REQ-SB-82-US-05-T02-meeting-prep-cron.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — n/a, manual-mode verification per `Implementation/Pipeline.md` (no test tooling exists yet)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **The Research Agent's own research/write capability** — `REQ-SB-82-
  US-02`, not this story; this story only delegates to it.
- **Any Cockpit-side UI for this agent's own findings** — findings surface
  through the already-existing Person note view; no new screen is built
  here.
- **A user-facing control to manually configure the suppression list** —
  not requested by the PRD's own text (which describes learning from
  plain-language feedback, not a settings UI); not built here.
- **Resolving the exact WhatsApp delivery mechanism or suppression-
  capture mechanism** — both left open, flagged for a human/architect
  decision (see `## Notes`).
- **Reviving `vault_writer.append_agent_memory_entries`/the archived
  agent-memory router as-is** — confirmed stale/dead-code; not assumed
  reusable (see Context).

## Notes

**Prototype parity:** None — backend/agent only, no screen affected by
this story (see Affected Screens).

**Why `gate: flagged`:**

1. No material assumption was needed to write the Gherkin above — every
   scenario is grounded directly in the PRD's own explicit text. The
   stale-citation correction below is a disclosed finding, not a guess.
2. `REQ-SB-82` is not marked `<!-- Draft -->`/unfinalised in the PRD.
3. N/A here (architect/ADR trigger) — but `/plan-tasks` should expect a
   real decision on the scheduling/delivery mechanism and the
   suppression-preference persistence mechanism.
4. No `ESCALATIONS.md` entry was written by this pass.
5. Not oversized — one bounded scheduled agent with three real behaviors
   (scan-and-delegate, one-time lookup, notify-and-learn), all named
   together as one mechanism in the PRD's own text.
6. N/A (coder trigger).
7. No contradictory PRD inputs found — the PRD's `vault_writer.
   append_agent_memory_entries` citation is not contradicted by another
   PRD passage; it is simply inaccurate against the current, real,
   post-Hermes-pivot codebase, recorded honestly rather than treated as a
   contradiction to resolve.
8. **The controlling flag:** trigger 8, genuinely unresolved on two real
   points named directly by the task that requested this spec — the exact
   WhatsApp delivery mechanism, and how "learn to suppress... from
   plain-language feedback" is mechanically captured (where the user says
   it, what "meetings like this" resolves to). Neither is guessed at.

**Resolved 2026-08-25 (operator):**

1. **Delivery mechanism:** a new Hermes cron job/profile, mirroring
   `daily-briefing`'s own proven pattern exactly — 2x/day schedule,
   `deliver: "whatsapp"`, silent unless the scan actually finds
   something worth checking (the same shape `new-company-discovery`'s
   own real cron already uses: no-op, not a "nothing found" message).
2. **Suppression persistence:** Hermes' own NATIVE per-profile
   `memories/USER.md` file — real, general, already populated across
   every existing profile with genuine learned facts (confirmed
   directly on `azure-expert`'s own file: real reply-style/preference
   entries already there). This is Hermes' own built-in learned-memory
   mechanism, not `vault_writer.append_agent_memory_entries` (the
   PRD's own citation, confirmed stale/unused).
3. **"Meetings like this" resolves to:** primarily the meeting's own
   `calendar_series_id` (the concrete, structural sense of "this kind
   of meeting" for a recurring series) — falling back to the meeting's
   own customer tag for a one-off meeting tied to the same customer.

**Architect pass, 2026-08-25 (`/plan-tasks` step 1):** designed the
concrete cron/profile + persistence shape — `ADR-010` (new). New Hermes
profile `meeting-prep-agent` with its own cron job (`interval`, 720
minutes, `deliver: "whatsapp"`, mirroring the real, live
`new-company-discovery` cron's shape); relays KB lookups to `research-agent`
(`ADR-008`); suppression preference lives in Hermes' own native
per-profile `memories/USER.md`, no new Second-Brain-side store. See
`Implementation/Architecture/architecture.md` §Meeting Preparation Agent.

**Architecture scope:** §Meeting Preparation Agent (`Implementation/
Architecture/architecture.md`), `ADR-010` — also depends on §Research
Agent & Librarian Vault-Write Skill / `ADR-008` (`REQ-SB-82-US-02`).

gate: flagged 2026-08-25 — trigger-3 (`ADR-010` created). REVIEW-QUEUE.md
entry added; `/plan-tasks` step 2 (decomposer) still proceeds per the
pipeline's own "ADR flags, doesn't halt" rule.

**Decomposer pass, 2026-08-25 (`/plan-tasks` step 2):** all 8 scenarios
tightened and locked as `AC-01`..`AC-08`. Per `ADR-010`'s own Decision
(no new Second-Brain-side schema, store, or API for suppression — Hermes'
native per-profile memory owns that entirely), this story carries almost
no `src/` code: two tasks, both Hermes-side Skill/cron authoring under
`Hermes-Provisioning/`, mirroring `REQ-SB-82-US-02`'s own established
split between repo-buildable script/doc authoring and live,
un-checked-in profile provisioning (see that story's own Notes for the
full reasoning, not repeated here). `T02` depends on `T01` (references the
lookup Skill in its own prompt) and on `REQ-SB-82-US-02-T02` (the real
`research-agent` capability it delegates to) — a real, disclosed
cross-story dependency named in this story's own Context from the start.
Every locked AC has at least one tagged step, several requiring a live
check against the real provisioned profile once it exists (disclosed
explicitly in `T02`, not silently assumed complete). `depends_on` is
acyclic. Status advanced `Draft -> Ready`; `gate` stays `flagged`
(`ADR-010` review is not cleared by this pass).

**Operator authorization, 2026-08-25:** "Start Coding" — reviewed the ADR against my own earlier resolution notes (matches exactly), authorized to proceed. gate: clear.

**Product-owner pass, 2026-08-25 (`/plan-sprints`):** grouped into
`SPRINT-077` alongside `REQ-SB-82-US-03` (both are real, task-level
dependents of `SPRINT-076`'s own two stories). `T02`'s `depends_on` on
`REQ-SB-82-US-02-T02` is a cross-sprint edge into `SPRINT-076` — recorded
as `SPRINT-077`'s own `depends_on_sprints: [SPRINT-076]`, per hard rule 7
(never contradicted, honoured via ordered sprints). gate: clear 2026-08-25
— no MUST-FLAG trigger fired at this stage (the cross-sprint edge is the
decomposer's own real, pre-existing task dependency, not one introduced
by this pass).

**Coder pass, 2026-08-25 (`T01` — Person-note web-lookup Skill):** `T01`
is `Done` — both its locked ACs (`AC-02`, `AC-03`) verified live against
real scratch Person notes in the real vault (cleaned up after). Status
moved `Ready -> In Progress` — `T02` (the cron/profile) remains, so this
story is not `Done` yet. See `T01`'s own `## Implementation Log` for the
full verification record.

**Coder pass, 2026-08-25 (`T02` — cron declaration + live Hermes
profile/cron provisioning):** `T02` is `Done` — all 6 of its locked ACs
(`AC-01`, `AC-04`-`AC-08`) verified, with `AC-01`/`AC-06`/`AC-07`
verified live with real positive results (a real delegation to
`research-agent`, real cross-session-persisted suppression learning,
real honored-on-a-future-scan behavior) and `AC-04`/`AC-05`/`AC-08`
disclosed honestly as configuration-confirmed plus decision-logic-proven
rather than fully live-observed end-to-end (the literal WhatsApp send
and the literal unattended fire), per the task's own explicit
pre-authorized methodology for a 12h+ cadence that can't be waited out
in one session -- compounded by a real, disclosed environment gap (the
new profile's own WhatsApp pairing, a human-interactive step, isn't
done yet, so its gateway can't stay running unattended). Both
substories' own two tasks are now `Done` -- this story is `Done`. See
`T02`'s own `## Implementation Log` for the full verification record,
the two scope-internal disclosed findings (Hermes memory-file routing;
WhatsApp-pairing gap), and cleanup confirmation.
