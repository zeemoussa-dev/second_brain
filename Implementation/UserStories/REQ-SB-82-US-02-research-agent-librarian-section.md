---
id: REQ-SB-82-US-02
title: Research Agent — a Librarian-Section capability that looks something up and writes what it finds as new, additive notes, no approval needed
requirement_ids: [REQ-SB-82]
requirement_section: "REQ-SB-82: Cockpit Mechanics — Prep, Research, and Moderation"
phase: P2
status: Done
gate: clear
gate_reason: "trigger-3 (ADR-008 created) — architect pass, 2026-08-25. The two operator resolutions below (REQ-SB-63 carve-out; research mechanism) remain as resolved; the flag is solely for the new ADR-008 (Research Agent Hermes profile + research-kb-writer Skill design), which needs a human look per the pipeline's own ADR-creation rule."
sprint: "SPRINT-076"
created: 2026-08-25
updated: 2026-08-25
---

# REQ-SB-82-US-02 — Research Agent — a Librarian-Section capability that looks something up and writes what it finds as new, additive notes, no approval needed

## Story

**As a** Second Brain user (and as any other agent that needs help — the
Meeting Preparation Agent, the Meeting Moderator's own fallback, or a
direct request)
**I want** a Research Agent that can look something up and write what it
finds into its own, dedicated corner of the vault as a brand-new note,
without needing my approval every time
**So that** gaps in what the vault already knows — an unfamiliar
technology, a topic nobody's written up yet — get filled in automatically
and safely, without any risk of an automated write ever touching or
overwriting something I already have

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-82: Cockpit Mechanics — Prep,
  Research, and Moderation*, "Research Agent" bullet — "lives under the
  existing Librarian Section (not meeting-scoped; the Prep Agent is one
  caller among possibly others later), may itself grow into a full Expert
  over time the same way Compass/Azure Experts did. Writes new, additive
  notes into their own vault area (their own folder, never touching or
  overwriting anything else — no approval gate needed for that reason,
  unlike a write that could damage existing content). Reused directly
  from mid-meeting Chat too (see Moderator below)." PRD breadcrumb
  (verbatim, 2026-08-25 operator discussion): Research Agent "is not
  related to the meeting, as we might promote it later to Expert (Same as
  Azure for example)" and "is in the Liberian Section"; and, when
  challenged on whether promotion/writing needed an approval gate: "it
  doesn't affect anything else it is located in its own folder so I don't
  think any harm can be done there" (operator's own correction, accepted,
  distinct from `BUG-037`'s real data-loss case which involved
  overwriting existing content).
- **This is one of five substories `REQ-SB-82` splits into — see
  `REQ-SB-82-US-01`'s own Context for the full split rationale.** This
  story is a **hard dependency** for two of the other four:
  `REQ-SB-82-US-04` (Moderator live routing) falls back to this agent when
  no brought-in Expert knows an answer; `REQ-SB-82-US-05` (Meeting
  Preparation Agent) delegates KB lookups to it for any unfamiliar
  technology/topic on an upcoming meeting. Both are named in the PRD text
  itself as callers of this one shared capability, not separate
  copies — "the Prep Agent is one caller among possibly others later...
  Reused directly from mid-meeting Chat too."
- **The "Librarian" Section already exists in the real, current, post-
  Hermes-pivot codebase — confirmed by direct reading, not assumed.**
  `app/business/section_registry.py::_STARTING_SECTION_NAMES` includes
  `"Librarian"`; `app/business/hermes/agents_map_adapter.py`'s own
  `_AGENT_SECTION` dict already places `notes-manager`/`files-manager`
  under it (`"Librarian"`, per that file's own 2026-08-23 comment history).
  A new Research Agent placed in this same Section is a same-shape
  extension of an already-real, already-populated concept, not a new one.
- **Genuinely open, not resolved here — no real research/web-lookup
  mechanism exists anywhere in the current codebase to build this
  against.** A direct search for any existing "research"/web-search
  capability under `app/business/hermes/` and the wider backend found
  none — the pre-Hermes-pivot `REQ-SB-36` web-research Skill
  (`Done`, historical) belonged to the now-fully-retired Second-Brain-
  native agent/LangGraph model, archived in the pivot, and is not a live
  mechanism to extend. Whether this new agent's real research capability
  is built as a genuine new Hermes Skill (mirroring how `azure-calculator`
  got its own real `pricing/azure-cost-calculator` Skill querying a real
  external API, per `MEMORY.md`'s 2026-08-23 entry), reuses some other
  Hermes-bundled web-fetch/browse capability, or something else entirely,
  is a real, undecided architectural question — left to `/plan-tasks`.
- **Genuinely open, not resolved here — how a fixed-own-folder write
  relates to `REQ-SB-63`'s Librarian/Vault Filing Expert placement
  authority ("every agent that produces new content route[s] it through
  this capability rather than deciding placement themselves").** The PRD's
  own text for THIS requirement frames the Research Agent's write as
  needing no placement decision at all — always its own dedicated folder,
  which is precisely why it needs no approval gate ("no harm can be
  done there"). Whether this is a deliberate, narrow, PRD-sanctioned
  carve-out from `REQ-SB-63`'s otherwise-general "every agent routes
  through the Librarian" rule (a fixed, single-destination write has no
  real placement DECISION to make, unlike genuinely new content needing
  somewhere to belong), or whether it should still nominally route through
  `REQ-SB-63`'s Vault Filing Expert for consistency, is not settled by
  either requirement's own text. Flagged below, not guessed.
- **Depends on:** `REQ-SB-18-US-01`/`REQ-SB-20-US-01` (Dynamic Agent
  Sections & Section Hub Intelligence, both **Done**) — Sections and
  Expert-type agents already exist as a real, addressable concept for a
  new agent to join. `REQ-SB-33-US-01` (Agent Grounding & Honest-
  Uncertainty Guardrail, **Done**) — this agent's own "found nothing
  conclusive" case (Scenario 5 below) should honor the same standing
  never-fabricate posture every other real agent already does.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then
edge cases and error states. Do NOT add AC-IDs — the decomposer assigns them
at /plan-tasks. These scenarios describe only the externally observable
behaviour; they deliberately do not assert the underlying research
mechanism (web search, a specific API, etc.) or the exact destination
folder name — both left open per Context. -->

### Scenario 1: A research request produces a new, additive note in the agent's own dedicated vault area

```gherkin
Given the Research Agent exists as a real agent under the Librarian
    Section
When any caller asks it to research a topic or technology
Then the agent researches the topic and writes a new note into its own
    dedicated vault area — never into a folder or note anywhere else
```
<!-- AC-ID: REQ-SB-82-US-02-AC-01 -->

### Scenario 2: A research write never edits or overwrites any existing note

```gherkin
Given the Research Agent has just written a new note for a research
    request
When the vault is checked immediately afterward
Then no existing note anywhere in the vault was edited, overwritten, or
    removed by that write — only the one new note was added
```
<!-- AC-ID: REQ-SB-82-US-02-AC-02 -->

### Scenario 3: A research write requires no approval and proceeds autonomously

```gherkin
Given a caller has asked the Research Agent to research something
When the agent finishes and is ready to write its findings
Then the write proceeds immediately, with no approval/confirmation step
    required from the user — unlike a write that could affect existing
    content
```
<!-- AC-ID: REQ-SB-82-US-02-AC-03 -->

### Scenario 4: The Research Agent behaves the same regardless of who asked

```gherkin
Given the Research Agent exists under the Librarian Section
When it is asked to research the same kind of thing by two different
    kinds of caller (e.g. a scheduled background job, versus a live
    request made from inside a Cockpit's Chat)
Then it researches and writes the same way in both cases — it has no
    caller-specific or meeting-specific behavior of its own
```
<!-- AC-ID: REQ-SB-82-US-02-AC-04 -->

### Scenario 5: The Research Agent honestly reports finding nothing conclusive, rather than fabricating a note

```gherkin
Given the Research Agent has been asked to research a topic and its real
    lookup returns nothing conclusive
When it finishes
Then it honestly reports that it found nothing conclusive
  And no note is written for that request — it never fabricates content
    to fill the gap
```
<!-- AC-ID: REQ-SB-82-US-02-AC-05 -->

## Affected Screens

- None — backend only. This agent's own real output (once written) is
  intended to surface through the ALREADY-BUILT Cockpit Overview tab's
  "Related documents"/"Articles" sections
  (`src/frontend/src/features/cockpit/Cockpit.tsx`, `overview.
  related_documents`/`overview.articles` — currently honest empty-state
  stubs per `cockpit_router.py`'s own docstring) — that wiring is
  `REQ-SB-82-US-05`'s (Prep Agent) concern where it applies, not
  rebuilt here; this story only builds the Research Agent capability
  itself.

## Dependencies

- **Blocked by:** `REQ-SB-18-US-01`/`REQ-SB-20-US-01` (both **Done**) —
  Sections and Expert-type agents exist as a real concept. Satisfied.
- **Related to, not blocking:** `REQ-SB-33-US-01` (Agent Grounding &
  Honest-Uncertainty Guardrail, **Done**) — the same honesty posture
  should extend to this new agent (Scenario 5); not a hard code
  dependency.
- **Related to, genuinely unclear (not blocking, but not resolved):**
  `REQ-SB-63-US-01` (The Librarian — Vault Filing Expert Central
  Authority, **Done**) — whether this agent's fixed-own-folder write is a
  deliberate, narrow carve-out from that story's "every agent routes
  through the Librarian" rule, per the flag above.
- **Feeds into:** `REQ-SB-82-US-04` (Moderator live routing — the
  fallback target) and `REQ-SB-82-US-05` (Meeting Preparation Agent — one
  caller). Neither is a dependency of THIS story; both depend on it.
- **Historical, not a build dependency:** `REQ-SB-36-US-01` (web-research
  Skill, **Done**, pre-Hermes-pivot) — the prior generation's equivalent
  capability, belonging to a now-retired architecture; not reusable as-is
  (see Context).
- **External:** the real research/lookup mechanism itself depends on
  whatever external capability `/plan-tasks` selects (a new Hermes Skill
  calling a real API, a bundled Hermes web-fetch capability, or
  otherwise) — not yet provisioned or decided.

## Constraints

- The Research Agent writes ONLY into its own dedicated vault area — never
  edits, appends to, or overwrites any note outside that area (Scenario
  2). This is the entire reason its writes need no approval gate
  (Scenario 3); if a future change ever needed it to touch existing
  content, that would need its own approval-gating story, not an
  extension of this one.
- Every research write is a brand-new, additive note — this story does
  not build any merge/dedup logic against a prior research note on the
  same or a similar topic; repeated similar requests may produce more
  than one note (left open, not resolved here — see Non-Goals).
- The agent must never fabricate a note when its research genuinely finds
  nothing conclusive (Scenario 5) — matching this project's standing
  honesty posture (`REQ-SB-33-US-01`/`ADR-011`).
- The agent's behavior does not vary by caller or by which meeting/email
  (if any) prompted the request (Scenario 4) — it is a shared capability,
  not a meeting-scoped one.
- The exact destination folder/path, and the exact research mechanism, are
  left to `/plan-tasks` — not decided here (see Context).

## Implementation Tasks

<!-- Decomposer's own table (/plan-tasks step 2, 2026-08-25) -- supersedes
the analyst-authored starting point above. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-82-US-02-T01 | backend | Register `research-agent` under the Librarian Section in Second Brain's own presentation layer (mirrors `notes-manager`/`files-manager`'s own placement) | `app/business/hermes/agents_map_adapter.py` | `Implementation/Tasks/REQ-SB-82-US-02-T01-research-agent-registration.md` |
| REQ-SB-82-US-02-T02 | backend/skill | `research-kb-writer` Skill (`write_research_doc.py` + `SKILL.md`) + live `research-agent` Hermes profile provisioning | new `Hermes-Provisioning/skills/librarian/research-kb-writer/` | `Implementation/Tasks/REQ-SB-82-US-02-T02-research-kb-writer-skill.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — n/a, manual verification mode (test tooling still pending project-wide)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Growing the Research Agent into a full Expert** — the PRD explicitly
  frames this as a possible FUTURE evolution ("may itself grow into a
  full Expert over time"), not built in this pass.
- **Merge/dedup logic across repeated or similar research requests** —
  left open (see Constraints); this pass builds only the "always write a
  new, additive note" behavior the PRD's own text describes.
- **Wiring this agent's output into the Cockpit's Overview tab
  (`related_documents`/`articles`)** — that surface already exists as an
  honest empty stub; connecting it to real Research Agent output is
  `REQ-SB-82-US-05`'s (or a later story's) concern, not built here.
- **Resolving the `REQ-SB-63` placement-authority interaction** — left
  open, flagged for a human decision (see `## Notes`).
- **Building the Moderator's own fallback-trigger logic or the Prep
  Agent's own scheduling** — both are separate stories
  (`REQ-SB-82-US-04`/`US-05`) that CALL this capability; this story only
  builds the capability itself.

## Notes

**Prototype parity:** None — backend-only, no screen affected by this
story directly (see Affected Screens).

**Why `gate: flagged`:**

1. No material assumption was needed to write the Gherkin above — every
   scenario is directly grounded in the PRD's own explicit text
   ("own folder," "no approval gate," "reused... from mid-meeting Chat
   too"). The two open items below are genuine gaps in the PRD's own
   text, not filled by a guess.
2. `REQ-SB-82` is not marked `<!-- Draft -->`/unfinalised in the PRD.
3. N/A here (architect/ADR trigger) — but `/plan-tasks` should expect a
   real architectural decision for the research mechanism itself (no
   live equivalent exists in the current codebase, per Context).
4. No `ESCALATIONS.md` entry was written by this pass.
5. Not oversized — one bounded new agent + one write capability.
6. N/A (coder trigger).
7. No contradictory PRD inputs found — REQ-SB-63's own "every agent
   routes through the Librarian" framing and this requirement's "own
   folder, no placement decision needed" framing are not stated as
   contradicting each other by either requirement's own text; they are
   simply unreconciled, which is why this is flagged as unclear rather
   than as a contradiction.
8. **The controlling flag, twice over:** (a) the `REQ-SB-63` placement-
   authority interaction, genuinely unclear; (b) no real research/
   web-lookup mechanism exists anywhere in this codebase to build
   against — the underlying capability is genuinely new, not an
   extension of something real and working today, unlike most of this
   project's recent stories.

**Resolved 2026-08-25 (operator):**

1. **REQ-SB-63 interaction — deliberate carve-out, not routed through the
   Vault Filing Expert.** `vault_filing_expert.py` still exists as a file
   but its only real callers (`email_classification.py`,
   `librarian_housekeeping.py`, `knowledge_bootstrap.py`,
   `knowledge_gap_tracking.py`, `project_customer_synthesizer.py`,
   `skill_tools.py`) are themselves pre-Hermes-pivot orchestration-layer
   code `main.py` no longer wires into the running app — the same fate as
   `cockpit_router.py`/`agent_activity.py` (see `MEMORY.md`). It is not a
   live, reachable mechanism in the current Hermes-based agent model
   regardless of `REQ-SB-63`'s own general framing. The Research Agent
   writes directly via its own dedicated Skill, the ONLY pattern actually
   proven working today (Azure Expert's `azure-kb-writer`, Compass
   Expert's equivalent, and the 3 Customer Experts all write this way).
2. **Research mechanism — Hermes' own bundled `web_search`/`terminal`
   tools**, the same real, proven capability already powering
   azure-expert's and compass-expert's own research (no new lookup
   capability needed) — plus **one new writer Skill**, `research-kb-writer`,
   directly mirroring `azure-kb-writer`'s own real, working script
   contract (`write_*_doc.py` shape), writing into a new `Work/Research/`
   folder (singular, matching `Technology`/`Sales`/`Librarian`'s own
   naming convention — flag if a different name/plural is wanted).

**Architect pass, 2026-08-25 (`/plan-tasks` step 1):** designed the
concrete new-agent/writer-Skill shape — `ADR-008` (new). New Hermes
profile `research-agent` under the Librarian Section; new
`research-kb-writer` Skill (`write_research_doc.py`, mirrors
`azure-kb-writer`'s contract but NEVER overwrites — always a new file, a
deliberate divergence, see ADR); writes to `Work/Research/<slug>.md`. See
`Implementation/Architecture/architecture.md` §Research Agent & Librarian
Vault-Write Skill.

**Architecture scope:** §Research Agent & Librarian Vault-Write Skill
(`Implementation/Architecture/architecture.md`), `ADR-008`.

gate: flagged 2026-08-25 — trigger-3 (`ADR-008` created). REVIEW-QUEUE.md
entry added; `/plan-tasks` step 2 (decomposer) still proceeds per the
pipeline's own "ADR flags, doesn't halt" rule.

**Decomposer pass, 2026-08-25 (`/plan-tasks` step 2):** all 5 scenarios
tightened and locked as `AC-01`..`AC-05`. `T01`/`T02` are independent
(`depends_on: []` each) — `agents_map_adapter.py`'s registration is
Second Brain's OWN presentation-layer concern, never consumed by the real,
external Hermes profile itself. **Scope-internal judgment call, disclosed
here, not hidden:** `research-kb-writer`'s `SKILL.md`+scripts are authored
under `Hermes-Provisioning/skills/librarian/research-kb-writer/` — this
repo's own established (if inconsistently used) location for checked-in
Skill authoring, per `Hermes-Provisioning/skills/README.md`'s own stated
convention — a NEW `librarian` category folder, mirroring the existing
`vault-rebuild`/`company-review`/`notes-capture` categories. The real,
live `research-agent` Hermes profile itself (SOUL.md, tool grants, Skill
installation onto the running Hermes install) has no checked-in-repo
representation, matching this repo's own real precedent (`azure-kb-writer`/
`compass-kb-writer` and the 3 Customer Experts are likewise never checked
in) and `ADR-008`'s own Consequences ("must be provisioned outside this
repo... not part of this repo's own `src/` build") — provisioning it is a
real, live coder action (mirroring established precedent for real external-
system verification elsewhere in this project) needed to fully verify
`AC-01`/`AC-03`/`AC-04`/`AC-05` live, not a repo file change. Every locked
AC has at least one tagged step across `T01`/`T02`. `depends_on` is
acyclic. Status advanced `Draft -> Ready`; `gate` stays `flagged`
(`ADR-008` review is not cleared by this pass).

**Operator authorization, 2026-08-25:** "Start Coding" — reviewed the ADR against my own earlier resolution notes (matches exactly), authorized to proceed. gate: clear.

**Product-owner pass, 2026-08-25 (`/plan-sprints`):** grouped into
`SPRINT-076` alongside `REQ-SB-82-US-01` (the two independent foundations
`US-03`/`US-05` both depend on) — see `SPRINT-076`'s own Grouping
Rationale for the full split-vs-combine reasoning against `Learnings.md`'s
sizing calibration. `T01`/`T02` independence (`depends_on: []` each)
honoured — either build order is valid inside the sprint. gate: clear
2026-08-25 — no MUST-FLAG trigger fired at this stage.

**Coder pass, 2026-08-25 (`/implement-sprint`):** both tasks `Done` —
`T01` (registration, presentation-layer only) and `T02`
(`research-kb-writer` Skill + live `research-agent` Hermes profile
provisioning). All 5 locked ACs (`AC-01`-`AC-05`) verified live with real,
positive results via `T02`'s own Tests — see its `## Implementation Log`
for the full real-request/real-note evidence, including cross-caller
(`AC-04`) and honest-no-result (`AC-05`) live confirmation, plus the real
Agents Map now showing `research-agent` (`type: expert`,
`section_id: librarian`), confirming `T01`'s previously-inert registration
now activates correctly end-to-end. Status advanced `Ready -> Done`.
`BACKLOG.md`'s `REQ-SB-82` row updated for `US-02`. gate: clear 2026-08-25
— no MUST-FLAG trigger fired at this stage (no locked AC left
unverified, no new out-of-scope event, the live Hermes-side provisioning
was pre-authorized by `T02`'s own Constraints).
