---
id: REQ-SB-82-US-03
title: Meeting Moderator — recommends the right Experts (Customer + Domain matching) before the user even opens the Cockpit
requirement_ids: [REQ-SB-82]
requirement_section: "REQ-SB-82: Cockpit Mechanics — Prep, Research, and Moderation"
phase: P2
status: Done
gate: clear
gate_reason: "trigger-3 (ADR-009 created) — architect pass, 2026-08-25. The two operator resolutions below (no fresh /design pass; domain-match data source) remain as resolved; the flag is solely for the new ADR-009 (roster-recommendation compute/persistence mechanism), which needs a human look per the pipeline's own ADR-creation rule."
sprint: "SPRINT-077"
created: 2026-08-25
updated: 2026-08-25
---

# REQ-SB-82-US-03 — Meeting Moderator — recommends the right Experts (Customer + Domain matching) before the user even opens the Cockpit

## Story

**As a** Second Brain user about to prep for or join a meeting
**I want** the Meeting Cockpit's Chat roster to already have the right
Experts recommended before I even open it — matched both against the
meeting's own customer and against its topic/technology — so that I don't
have to figure out and manually bring in who I need, every single time

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-82: Cockpit Mechanics — Prep,
  Research, and Moderation*, "Meeting Moderator" bullet (first half) —
  "assembles the Chat's roster before you arrive (the 'Recommended' slot
  the UI already reserves) by matching the meeting's own `customer`
  tag/folder against a Customer Expert (see REQ-SB-83) AND matching
  topic/tags against a domain Expert's own KB scope (Azure/MACC's own
  categories) — both tracks, not one." REQ-SB-82's own PRD context also
  records: "the Moderator's roster-assembly signal was missing a
  Customer-Expert track entirely, which the operator then scoped as its
  own requirement (REQ-SB-83)."
- **This is one of five substories `REQ-SB-82` splits into — see
  `REQ-SB-82-US-01`'s own Context for the full split rationale.** This
  story covers ONLY roster pre-assembly (the "before you arrive" half of
  the Moderator). Live, per-question routing during the chat, the
  fallback to the Research Agent, and async/threaded replies are
  `REQ-SB-82-US-04` — a separate story, since roster pre-assembly has
  real, independent value even before any per-question routing
  intelligence exists (a recommended-but-not-yet-smart roster still saves
  the user the trouble of remembering who's relevant), and vice versa
  (live targeted routing is valuable against a manually-assembled roster
  too, per today's existing bring-in mechanism).
- **A real, material correction to the PRD's own text, found by direct
  inspection of the current, live code — not assumed:** the PRD's
  parenthetical, "the 'Recommended' slot the UI already reserves,"
  describes something that does NOT exist in the real, current
  `Cockpit.tsx` (2026-08-25 UI makeover — the SAME session this
  requirement was raised in). The Chat tab's right-rail roster today has
  exactly two groupings, `"In this chat"` and (`"Bring in another
  Expert"`/`"Experts"`) — no "Recommended" concept anywhere in the
  component, its CSS, or `cockpitApiClient.ts`'s `CockpitData` contract
  (confirmed by a direct search of `src/frontend/src/features/cockpit/`
  for "recommend", zero matches). Either the operator was describing the
  STALE, pre-2026-08-25 `html-prototype/meeting-cockpit.html` mockup (an
  `.item-list`/badge concept that was never literally a "Recommended"
  group either — it shows `In this chat`/`+ Bring in` rows, same as
  today's real code) or anticipating a slot this same-day UI rewrite was
  expected to already have and didn't. Recorded honestly here, per this
  project's own precedent (`REQ-SB-44-US-01`'s own correction of a stale
  PRD dependency-status claim) rather than silently trusted or silently
  "corrected" without a note. **This means building a visible
  "Recommended" grouping is real, net-new UI work this pass, not a
  fill-in-the-blank against something that already exists.**
- **Depends on `REQ-SB-82-US-01` (Persisted Cockpit Chat) — a real,
  disclosed dependency, not merely related.** A roster recommended
  "before you arrive" needs somewhere durable to be written to BEFORE the
  user ever opens the Cockpit — the same persisted roster store
  `REQ-SB-82-US-01` builds. Without it, "pre-assembled" would only be
  achievable by computing the recommendation live on every page open,
  which contradicts the PRD's own "before you arrive" framing (a
  recommendation the user's own agents have already acted on, not one
  freshly computed the moment the page loads — though the PRD's own text
  does not rule out a live-computed-on-open recommendation either; this
  is left to `/plan-tasks` to resolve mechanically, the observable
  behavior in the Scenarios below holds either way).
- **The customer-match track's own real dependency, `REQ-SB-83`, is an
  unusual shape: real deployed code, no formal story.** Confirmed by
  direct inspection: `app/business/hermes/agents_map_adapter.py`'s
  `_AGENT_TYPE`/`_AGENT_SECTION` dicts already carry real entries for
  `masdar-expert`/`adnoc-expert`/`taqa-expert` (`type: "expert"`,
  `Section: "Sales"`), matching REQ-SB-83's own PRD text ("any Tag that
  Contains Masdar, and the Masdar folder in Customers same for Adnoc and
  Same for TAQA"). But REQ-SB-83's own PRD Acceptance text says plainly:
  "Not yet specced formally as Gherkin... built directly this same
  session." There is no `REQ-SB-83-US-01` story file, and `BACKLOG.md`
  lists it with no Story column entry at all ("Built directly (Masdar/
  Adnoc/TAQA) — see CHANGELOG.md"). This story's customer-match track is
  therefore satisfied IN PRACTICE (the real agents exist and are
  addressable) but has no story-level traceability to point `/plan-tasks`
  at — recorded honestly, not treated as a normal `Done`-story
  dependency.
- **Genuinely open, not resolved here — the domain-match track's own
  underlying data does not exist yet, for any real agent.**
  `agents_map_adapter.py`'s own module docstring states explicitly:
  "Fields with no honest Hermes equivalent (settings, keywords, scope,
  guardrails, color, depends_on, branch_target_agent_id) are left empty/
  null rather than fabricated." There is today NO real per-agent
  keyword/domain-scope data structure for `azure-expert`/`macc-expert`
  (or any Expert) that a "matching topic/tags against a domain Expert's
  own KB scope" mechanism could read — this is a genuine, confirmed gap,
  not an assumption. Building the domain-match track therefore requires
  either inventing this data structure fresh (a real, new per-agent
  field) or reusing `REQ-SB-20`'s own existing per-agent keyword concept
  (`section_registry`-adjacent, built for cross-Section Hub routing) —
  neither option is chosen here; left to `/plan-tasks`.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then
edge cases and error states. Do NOT add AC-IDs — the decomposer assigns them
at /plan-tasks. These scenarios describe only the externally observable
recommendation behaviour; they deliberately do not assert the exact
domain-match data source or the exact visual mechanism for a "Recommended"
distinction — both left open per Context. -->

### Scenario 1: A meeting tagged for a known customer gets that customer's Customer Expert recommended

```gherkin
Given an upcoming meeting is tagged/foldered for a customer that has a
    real Customer Expert (e.g. Masdar, Adnoc, or TAQA, per REQ-SB-83)
When the Meeting Moderator assembles that meeting's roster ahead of the
    user opening its Cockpit
Then that customer's own Customer Expert is recommended for this
    meeting's Chat
```
<!-- AC-ID: REQ-SB-82-US-03-AC-01 -->

### Scenario 2: A meeting matching a domain Expert's own KB scope gets that domain Expert recommended

```gherkin
Given an upcoming meeting's own topic/tags match a real domain Expert's
    known KB scope (e.g. an Azure- or MACC-related topic)
When the Meeting Moderator assembles that meeting's roster
Then that domain Expert is recommended for this meeting's Chat
```
<!-- AC-ID: REQ-SB-82-US-03-AC-02 -->

### Scenario 3: A meeting matching both a customer and a domain gets both Experts recommended — both tracks run, not either/or

```gherkin
Given an upcoming meeting matches BOTH a known customer (Scenario 1) AND
    a domain Expert's own KB scope (Scenario 2)
When the Meeting Moderator assembles that meeting's roster
Then both the Customer Expert and the domain Expert are recommended
    together — neither track suppresses or is skipped in favor of the
    other
```
<!-- AC-ID: REQ-SB-82-US-03-AC-03 -->

### Scenario 4: A meeting matching neither track gets no fabricated recommendation

```gherkin
Given an upcoming meeting matches neither a known customer nor any domain
    Expert's own KB scope
When the Meeting Moderator assembles that meeting's roster
Then no Expert is recommended for this meeting — the roster starts
    genuinely empty, never a fabricated or generic guess
```
<!-- AC-ID: REQ-SB-82-US-03-AC-04 -->

### Scenario 5: A recommended Expert is distinguishable from the rest of the available roster

```gherkin
Given a meeting has one or more Experts recommended by the Moderator
When the user opens that meeting's Cockpit Chat tab, before bringing
    anyone in manually
Then the recommended Expert(s) are visibly distinguishable as
    recommendations, separate from the plain "available to bring in" list
```
<!-- AC-ID: REQ-SB-82-US-03-AC-05 -->

### Scenario 6: The user can still bring in any other Expert beyond what's recommended

```gherkin
Given a meeting has one or more Experts recommended by the Moderator
When the user brings in a DIFFERENT Expert that was not recommended
Then that Expert is added to the chat the same way any manually brought-in
    Expert already works — recommendation never restricts the user's own
    choice
```
<!-- AC-ID: REQ-SB-82-US-03-AC-06 -->

### Scenario 7: A customer without a matching Customer Expert yet produces no fabricated customer-track match

```gherkin
Given an upcoming meeting is tagged/foldered for a customer that has no
    real Customer Expert yet (a customer beyond the first three named in
    REQ-SB-83)
When the Meeting Moderator assembles that meeting's roster
Then the customer-match track produces no recommendation for that
    meeting — never a fabricated or best-guess substitute
```
<!-- AC-ID: REQ-SB-82-US-03-AC-07 -->

## Affected Screens

- `src/frontend/src/features/cockpit/Cockpit.tsx` — the REAL, current
  screen (see `REQ-SB-82-US-01`'s own Context for why the stale
  `html-prototype/meeting-cockpit.html` is not the design authority
  here). Needs a genuinely NEW "Recommended" grouping in the Chat tab's
  right rail — confirmed, by direct inspection, not to exist today (see
  Context). **No prototype or approved design covers this new region —
  `net-new-design-needed`.**

## Dependencies

- **Blocked by:** `REQ-SB-82-US-01` (Persisted Cockpit Chat, `Draft`,
  not yet built) — the recommended roster needs the same durable roster
  store that story builds. See that story's own Context for the reverse
  edge.
- **Blocked by (in practice, not by a formal story):** `REQ-SB-83`
  (Customer Experts, real deployed code, no story of its own) — the
  customer-match track's real target agents. Satisfied IN PRACTICE, not
  traceable to a `Done` story — see the flag above.
- **Blocked by:** `REQ-SB-18-US-01`/`REQ-SB-20-US-01` (both **Done**) —
  domain Experts (`azure-expert`, `macc-expert`) already exist as real,
  addressable agents. Satisfied for the agents themselves; NOT satisfied
  for the domain-match track's own underlying keyword/scope data, which
  does not yet exist (see the flag above).
- **Related to, not blocking:** `REQ-SB-82-US-04` (Moderator live routing)
  — shares the same overall "Meeting Moderator" concept and the same
  roster, but neither story requires the other to exist first (see
  Context).
- **External:** none new.

## Constraints

- Both matching tracks (customer, domain) run independently — a meeting
  matching both must recommend both Experts, never only one (Scenario 3).
- A recommendation must never be fabricated when neither track finds a
  real match (Scenarios 4, 7) — this project's standing never-fabricate
  honesty posture applies here too.
- Recommendation never restricts what the user can manually bring in
  (Scenario 6).
- The exact domain-match data source (a new per-agent field, or reuse of
  `REQ-SB-20`'s existing keyword concept) is left open, not decided here
  — see Context.
- The exact visual mechanism for the "Recommended" distinction (a badge, a
  separate group heading, etc.) is left to `/design`/`/plan-tasks` — not
  decided here, mirroring `REQ-SB-43-US-01`'s own precedent for leaving a
  visual mechanism open while asserting only the observable requirement
  (Scenario 5).

## Implementation Tasks

<!-- Decomposer's own table (/plan-tasks step 2, 2026-08-25) -- supersedes
the analyst-authored starting point above. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-82-US-03-T01 | backend | `moderator.py` — `match_customer_expert`/`match_domain_experts`, both tracks (`ADR-009`) | `app/business/cockpit/moderator.py` (new) | `Implementation/Tasks/REQ-SB-82-US-03-T01-moderator-matching.md` |
| REQ-SB-82-US-03-T02 | backend | Compute-on-first-read, cache `recommended_agent_ids` additively on `ADR-007`'s per-subject entry | `app/business/cockpit/chat_store.py` | `Implementation/Tasks/REQ-SB-82-US-03-T02-recommendation-caching.md` |
| REQ-SB-82-US-03-T03 | frontend | New "Recommended" grouping in the Chat tab's right rail (already-approved shape) | `src/frontend/src/features/cockpit/Cockpit.tsx` | `Implementation/Tasks/REQ-SB-82-US-03-T03-recommended-grouping-frontend.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists) — n/a, test tooling still pending project-wide, per every task's own Tests block
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Live, per-question routing during the chat, the Research Agent
  fallback, or async/threaded replies** — all `REQ-SB-82-US-04`, not this
  story (see Context).
- **Building `REQ-SB-83`'s own Customer Experts** — already real,
  deployed code; this story only consumes them.
- **Inventing a new domain-scope data model outright** — the underlying
  data-source decision is left to `/plan-tasks`, not decided here.
- **Removing or restricting the user's own manual bring-in ability** — the
  recommended roster is additive, never a restriction (Scenario 6).

## Notes

**Prototype parity (Cockpit.tsx's real current layout):**

- The existing "In this chat"/"available Experts" grouping — **Specced,
  unchanged** — this story adds a new grouping alongside it, does not
  modify the existing two.
- A new "Recommended" grouping — **`net-new-design-needed`.** Confirmed,
  by direct code inspection, NOT to exist anywhere in the real, current
  Cockpit.tsx despite the PRD's own claim that the UI "already reserves"
  this slot (see Context's correction). Recommend running `/design` for
  this specific region before `/plan-tasks` locks its visual shape.

**Why `gate: flagged`:**

1. No material assumption was made filling a genuine PRD gap — the PRD's
   own "Recommended slot" claim was checked directly against the real
   code and found not to exist; this is a disclosed correction, not a
   guess.
2. `REQ-SB-82` is not marked `<!-- Draft -->`/unfinalised in the PRD.
3. N/A here (architect/ADR trigger) — but `/plan-tasks` should expect a
   real design decision for the domain-match data source.
4. No `ESCALATIONS.md` entry was written by this pass.
5. Not oversized — deliberately split out of the larger Moderator
   mechanism as the one bounded "before you arrive" pre-assembly piece.
6. N/A (coder trigger).
7. No contradictory PRD inputs found — the PRD's "Recommended slot the UI
   already reserves" claim is not contradicted by another PRD passage; it
   is simply inaccurate against the real, current code, recorded
   honestly rather than treated as a contradiction to resolve.
8. **The controlling flag:** `net-new-design-needed` (the "Recommended"
   grouping genuinely does not exist, confirmed by direct inspection) —
   the primary reason for the flag. A secondary, real `unclear-
   requirement` factor: the domain-match track's own underlying data does
   not exist for any real agent today.

**Resolved 2026-08-25 (operator):**

1. **No fresh `/design` pass needed.** The "Recommended" grouping's
   visual shape was already designed and approved in the same-day live
   whiteboarding session that produced this requirement — an interactive
   mockup (right rail: "Recommended" section with the relevant agent +
   an Add action, plain Experts list below) was shown and the operator
   confirmed it ("Good") before `Cockpit.tsx` was ever built. It's real,
   approved design that simply wasn't wired into the shipped code because
   no real recommendation data existed yet to populate it — `/plan-tasks`
   builds against that approved shape directly, not a fresh design pass.
2. **Domain-match data source:** lightweight keyword overlap between the
   meeting's own tags/subject and each Expert's already-exposed `GET
   /agents` `name`/`description` fields — no new structured per-agent
   scope-tagging schema for v1. Refine later if this proves too coarse in
   practice.

**Architect pass, 2026-08-25 (`/plan-tasks` step 1):** designed the
concrete compute/persistence mechanism — `ADR-009` (new). Both match
tracks are deterministic and run entirely inside Second Brain's own
backend (`app/business/cockpit/moderator.py`, new) — no new Hermes
profile. Computed on the subject's first real `GET /cockpit/...` read and
cached as a new, additive `recommended_agent_ids` field on `ADR-007`'s
own per-subject roster entry. See `Implementation/Architecture/
architecture.md` §Meeting Moderator Roster Recommendation.

**Architecture scope:** §Meeting Moderator Roster Recommendation
(`Implementation/Architecture/architecture.md`), `ADR-009` — also depends
on §Cockpit Persisted Chat / `ADR-007` (`REQ-SB-82-US-01`).

gate: flagged 2026-08-25 — trigger-3 (`ADR-009` created). REVIEW-QUEUE.md
entry added; `/plan-tasks` step 2 (decomposer) still proceeds per the
pipeline's own "ADR flags, doesn't halt" rule.

**Decomposer pass, 2026-08-25 (`/plan-tasks` step 2):** all 7 scenarios
tightened and locked as `AC-01`..`AC-07`. `depends_on` crosses story
boundaries by task ID, per this project's own "task IDs, never story IDs"
rule: `T02` depends on `REQ-SB-82-US-01-T01`/`T02` (the `chat_store`
persistence layer + router `GET` it extends additively); `T03` depends on
`REQ-SB-82-US-01-T03` (the real frontend roster-reading wiring the new
"Recommended" grouping builds alongside). **The customer-match track's own
real dependency on `REQ-SB-83`'s deployed Masdar/Adnoc/TAQA Customer
Experts cannot be encoded as a `depends_on` task-ID edge — `REQ-SB-83` has
no story or task of its own** (real, deployed code, "Built directly this
same session," per its own PRD Acceptance text and this story's own
Context). Recorded honestly here rather than silently omitted or invented
as a fake task ID; `T01`'s own Context names this explicitly. Every locked
AC has at least one tagged step across `T01`-`T03`. `depends_on` is
acyclic. Status advanced `Draft -> Ready`; `gate` stays `flagged`
(`ADR-009` review is not cleared by this pass).

**Operator authorization, 2026-08-25:** "Start Coding" — reviewed the ADR against my own earlier resolution notes (matches exactly), authorized to proceed. gate: clear.

**Product-owner pass, 2026-08-25 (`/plan-sprints`):** grouped into
`SPRINT-077` alongside `REQ-SB-82-US-05` (both are real, task-level
dependents of `SPRINT-076`'s own two stories). `T02`'s `depends_on` on
`REQ-SB-82-US-01-T01`/`T02` and `T03`'s `depends_on` on
`REQ-SB-82-US-01-T03` are cross-sprint edges into `SPRINT-076` — recorded
as `SPRINT-077`'s own `depends_on_sprints: [SPRINT-076]`, per hard rule 7
(never contradicted, honoured via ordered sprints). gate: clear 2026-08-25
— no MUST-FLAG trigger fired at this stage (the cross-sprint edge is the
decomposer's own real, pre-existing task dependency, not one introduced
by this pass).

**Coder pass, 2026-08-25 (`/implement-sprint`, `T03`):** all 3 tasks now
`Done`; all 7 locked ACs (`AC-01`..`AC-07`) verified live across
`T01`/`T02`/`T03` — see each task's own `## Implementation Log`. `T03`'s
live verification (real headless-Edge CDP session against the real
running frontend/backend and a real vault Masdar meeting note) confirmed
the "Recommended" grouping renders distinctly, a recommended agent moves
to "In this chat" (never duplicated) on Add and persists across reload,
and manual bring-in of a different Expert stays unrestricted. Status
advanced `Ready -> Done`; gate stays `clear`. `SPRINT-077` stays `In
Progress` — its sibling story `REQ-SB-82-US-05` is not yet `Done`.
