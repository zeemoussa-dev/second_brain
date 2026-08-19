---
id: REQ-SB-49-US-02
title: Cockpit Person-Directed Instruction (@PersonName) — Agent Proposes a Gated Person-Note Edit
requirement_ids: [REQ-SB-49]
requirement_section: "REQ-SB-49: Cockpit @Mentions"
phase: P1
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-038 created) — the architect has resolved the analyst's own open composing-mechanism/ADR-036-tension question with a new, gate-preserving bound-tool interception (propose_person_note_update, mirrors ADR-032's record_knowledge_gap shape) reaching skill_registry.invoke_skill through a new 'cockpit_mention' trigger literal, plus a deliberate mode-scoped 'propose' deviation for Manual/Autonomous dispatch — see ADR-038 in Implementation/Architecture/ADR.md; human review still needed before tasks are locked (original analyst gate_reason, superseded by this resolution: material assumption + unclear-requirement re: the composing mechanism vs. ADR-036's own Cockpit-bypasses-gate finding)"
sprint: "SPRINT-046"
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-49-US-02 — Cockpit Person-Directed Instruction (@PersonName) — Agent Proposes a Gated Person-Note Edit

## Story

**As a** Second Brain user working inside a Cockpit chat with an Expert
already brought in
**I want** to direct an instruction at that Expert that names a specific
real person (`@AhmedMoussa`), and have the Expert propose the described
update to that person's real Person note
**So that** I can ask an agent to update someone's record in plain
language without leaving the chat, while staying certain nothing is ever
written to my vault without going through the same approval gate every
other mutating agent action already goes through

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-49: Cockpit @Mentions* — "...a
  message can additionally mention a specific PERSON by name (e.g.
  `@AhmedMoussa`) whose Person note the mentioned agent should update
  based on the instruction text." **Acceptance:** "...a message mentioning
  a specific person by name, directed at a brought-in agent, results in
  that agent locating the real matching Person note and proposing (never
  silently applying) an edit reflecting the instruction, subject to that
  agent's own working-mode gate."
- **PRD breadcrumb (2026-08-14, operator-directed, verbatim example):**
  `"@people Add The Following to @AhmedMoussa since now he is leaving the
  company and going to Core42."` The breadcrumb itself frames this as "a
  genuinely new, real vault-write capability (parsing an instruction,
  resolving a name to a real Person note, applying an edit)... very
  likely needs `REQ-SB-21` working-mode gating (a person-note edit is a
  real mutation, **unlike the Cockpit's existing research-save-with-
  explicit-confirm flow**)... left entirely to `/plan-tasks` to design,
  not guessed at here."
- **Bounded scope for THIS story — deliberately not full NLU-driven vault
  editing:** the mentioned agent's own LLM reasoning (already real,
  already tool-calling — `agent_orchestration/graph.py`'s
  `run_agent_conversation`) interprets the instruction text and PROPOSES
  one specific edit to the resolved Person note (e.g. a new fact/field
  value to add or change). It never silently applies the edit. This
  mirrors `REQ-SB-08`/`REQ-SB-35`'s own established "propose, then either
  auto-file or require approval depending on working mode" shape — not a
  new gating philosophy. What exactly counts as "the edit" (a single new
  body line/fact vs. a structured frontmatter change) is intentionally
  **not** asserted below at the prompt-engineering/NLU level — the
  Scenarios describe only the externally observable outcome (a proposal
  naming the real Person note and reflecting the instruction; gated by
  working mode), never a specific parsing algorithm.
- **The composing mechanism — resolved here to the most defensible single
  reading, NOT decided with full confidence (see `gate_reason` above):**
  a new mutating Skill (e.g. `propose_person_note_update`, `mutates:
  True`, alongside `skill_tools.py`'s existing `rebuild_person_note`
  entry) granted to the People Notes producer agent (`people-producer`),
  dispatched through `skill_registry.invoke_skill`'s already-real,
  already-shipped two-axis working-mode gate (`REQ-SB-39-US-02`,
  `ADR-029`, **Done**) — the SAME gate every other mutating Skill in this
  codebase already goes through (Supervised mode creates a Pending
  Approval the user must explicitly approve/decline before
  `vault_writer` is ever called; Manual/Autonomous dispatch immediately,
  exactly as they do for every other mutating Skill today). This is the
  most literal reading of the PRD's own "subject to that agent's own
  working-mode gate" acceptance text, and directly composes with an
  already-Done mechanism rather than inventing a new one.
  - **The real tension, not glossed over:** `ADR-036` (Cockpit,
    `REQ-SB-43-US-01`, **Done**, `MEMORY.md` 2026-08-14) found — by direct
    code inspection, live-verified — that the Cockpit's own real
    mechanisms (an Expert's chat/tool-calling reply, and the user's own
    explicit research-save) **never reach `skill_registry.invoke_skill`'s
    gated dispatch path at all today.** The operator's own resolution for
    `REQ-SB-43` was explicit: "bringing an Expert in on purpose is itself
    the approval" — working-mode gating does not apply inside a Cockpit
    session for the mechanisms that story built. This requirement's own
    PRD breadcrumb directly anticipates and pushes back on exactly this
    precedent for THIS specific new capability ("unlike the Cockpit's
    existing research-save-with-explicit-confirm flow"), implying a
    person-note mutation should NOT inherit that same bypass. Reconciling
    "Cockpit actions bypass the gate by design" with "this one new Cockpit
    action must be gated" is a genuine architectural decision — whether
    the new Skill is reached via a new, deliberately gate-preserving call
    path (e.g. a new graph node/tool that explicitly calls
    `invoke_skill(..., trigger="chat")`, analogous to how
    `route_hub_request`/`record_knowledge_gap` already intercept specific
    tool calls before the generic `execute_tools` node) rather than
    through the LLM's ordinary MCP-tool-calling path (which, per
    `ADR-036`'s own finding, would bypass the gate exactly like every
    other Cockpit tool call does today) — is left to `/plan-tasks`, not
    guessed at here.
  - **Alternative considered, not chosen:** extending `vault_write_tools.
    propose_vault_write`'s existing MCP-tool shape (`REQ-SB-04-US-01`, **In
    Progress**) — this always creates a Pending Approval unconditionally,
    bypassing `working_mode_registry` entirely regardless of mode
    (`vault_write_tools.py`'s own docstring). This does NOT match the
    PRD's own "subject to that agent's own working-mode gate" acceptance
    text (which implies mode-DEPENDENT behaviour, not always-gated), so
    it is not the reading carried forward here — named for completeness,
    since the PRD breadcrumb's own prose loosely says "composes with
    `REQ-SB-04`'s vault-write mechanism."
- **Honest handling when the mentioned person doesn't match a real Person
  note** — resolved directly, by direct precedent
  (`people_extraction.find_existing_person_note`'s own existing
  read-only, never-fabricate posture, and this project's standing
  honesty guardrail, `REQ-SB-33`): the agent reports it could not find a
  matching Person note; it never creates one as a side effect of a
  mention, and never guesses at the nearest-sounding name.
- **Depends on:** `[[REQ-SB-43-US-01]]`/`[[REQ-SB-44-US-01]]` (Cockpit
  shared thread + brought-in Experts, both **Done**) — a message must
  already be directed at a brought-in agent. `REQ-SB-39-US-02` (Skill
  mutating-action working-mode gate, **Done**) — the gate this story
  composes with. `REQ-SB-21-US-01` (Agent Working Modes, **Done**) — the
  Manual/Supervised/Autonomous modes this gate reads. `people_extraction.
  py`'s existing `find_existing_person_note` (read-only Person-note
  lookup, already real) — the resolution primitive for "the real matching
  Person note."

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then), at the observable-
behaviour level only — deliberately not asserting a specific NLU/prompt-
engineering mechanism, nor which exact call path reaches the working-mode
gate (an architect decision, per Context above). Do NOT add AC-IDs — the
decomposer assigns them at /plan-tasks. -->

### Scenario 1: A person-directed instruction proposes an edit to the real matching Person note — never silently applied

```gherkin
Given a Cockpit chat has the "people-producer" agent brought into the
    shared thread, and "Ahmed Moussa" has a real, existing Person note in
    the vault
When the user sends a message directed at "people-producer" that mentions
    "@AhmedMoussa" together with an instruction describing a change (e.g.
    "he is leaving the company and going to Core42, update his note")
Then "people-producer"'s reply proposes a specific edit to Ahmed Moussa's
    real Person note reflecting the instruction
  And the vault's actual Person note is NOT modified yet — the edit is a
    proposal only, never applied as a side effect of the chat reply itself
```
<!-- AC-ID: REQ-SB-49-US-02-AC-01 -->

### Scenario 2: In Supervised mode, the proposed edit requires explicit approval before the Person note is touched

```gherkin
Given "people-producer" is currently in Supervised working mode, and a
    person-directed instruction (Scenario 1) has produced a proposed edit
    to a real Person note
When the user views their pending approvals
Then a Pending Approval exists describing the proposed Person-note edit
When the user approves it
Then the real Person note is updated to reflect the approved edit, and not
    before
When, in a separate case, the user instead declines a pending proposal of
    this kind
Then the real Person note is left completely unchanged
```
<!-- AC-ID: REQ-SB-49-US-02-AC-02 -->

### Scenario 3: In Manual or Autonomous mode, the same gate applies as it already does for every other mutating action

```gherkin
Given "people-producer" is currently in Manual or Autonomous working mode
    (not Supervised)
When a person-directed instruction (Scenario 1) produces a proposed edit
    to a real Person note
Then the proposed edit is handled by that agent's own working-mode gate
    exactly as any other mutating action already is for that mode — never
    a special-cased, ungated bypass invented only for this capability
```
<!-- AC-ID: REQ-SB-49-US-02-AC-03 -->

### Scenario 4: A mentioned person who has no real, existing Person note is honestly reported — never fabricated

```gherkin
Given a Cockpit chat has an Expert brought into the shared thread
When the user sends a message mentioning "@SomeoneWithNoNote", a name that
    matches no real existing Person note in the vault
Then the agent's reply honestly states that no matching Person note was
    found for that name
  And no Person note is created, and no edit is proposed, for a name that
    does not resolve to a real, existing note
```
<!-- AC-ID: REQ-SB-49-US-02-AC-04 -->

### Scenario 5: A person mention with no accompanying instruction produces no proposal

```gherkin
Given a Cockpit chat has an Expert brought into the shared thread, and
    "Ahmed Moussa" has a real, existing Person note
When the user sends a message that mentions "@AhmedMoussa" but contains no
    discernible instruction to change anything about him
Then no proposed edit is produced — the agent may reply conversationally,
    but nothing resembling a vault-write proposal is generated from a bare
    mention alone
```
<!-- AC-ID: REQ-SB-49-US-02-AC-05 -->

### Scenario 6: A pending person-note-edit proposal renders as a distinct, confirmable/discardable region in the Cockpit chat thread (decomposer-authored structural AC, `/plan-tasks` step 2)

<!-- Not present in the analyst's original draft — added under the
decomposer's own structural-AC mandate (this story changes a screen: the
Cockpit chat thread gains a new pending-proposal region). Verifiable on
DOM structure alone (element/region presence, confirm/discard controls),
never on pixel-level visual polish. Mirrors the existing `.chat-proposal`
"Awaiting your decision" component the same screen already renders for a
quick-research result (REQ-SB-44-US-01/ADR-036), reused for this new
proposal kind per the story's own Notes. -->

```gherkin
Given a Manual- or Autonomous-mode person-directed instruction (Scenario 3)
    has produced a pending, not-yet-confirmed person-note-edit proposal for
    the currently open Cockpit thread
When the user views that Cockpit's chat thread
Then a distinct proposal region renders in the thread (the same
    `.chat-proposal`-shaped "Awaiting your decision" structural pattern the
    thread already uses for a quick-research result), naming the person and
    the proposed instruction
  And that region carries two distinct interactive controls — one to
    confirm the proposal, one to discard it
When the user clicks confirm
Then the real Person note is updated to reflect the proposal, and the
    proposal region no longer shows it as pending
When, in a separate case, the user instead clicks discard
Then the real Person note is left completely unchanged, and the proposal
    region no longer shows it as pending
```
<!-- AC-ID: REQ-SB-49-US-02-AC-06 -->

## Affected Screens

- `html-prototype/meeting-cockpit.html` / `html-prototype/inbox-cockpit.html`
  — the chat thread's existing `.chat-proposal` pending-decision pattern
  (already approved, used today for on-the-spot research save/discard) is
  the closest existing visual precedent for how a proposed Person-note
  edit would surface in-thread; whether it reuses that exact pattern or
  needs its own variant is left to `/plan-tasks`/the coder — see `## Notes`.
- `html-prototype/my-day-approvals.html` — the existing Pending Approvals
  surface (`REQ-SB-21`) is the likely destination for the Supervised-mode
  approval itself, reused unmodified.

## Dependencies

- **Blocked by:** `[[REQ-SB-43-US-01]]`, `[[REQ-SB-44-US-01]]` (Cockpit
  shared thread, both **Done**).
- **Blocked by:** `REQ-SB-39-US-02` (Skill working-mode gate, **Done**) —
  the mechanism this story composes with, per the resolved reading above.
- **Related to, genuinely unresolved:** `ADR-036` (Cockpit mechanism,
  **Accepted**) — its own "Cockpit actions bypass invoke_skill's gate by
  design" finding is in direct tension with this story's own gated
  requirement; an architect decision at `/plan-tasks` must reconcile the
  two (see Context).
- **Related to, not the chosen mechanism:** `REQ-SB-04-US-01` (Agent
  Vault Write Access / Hermes `propose_vault_write`, **In Progress**) —
  considered and set aside; its always-unconditionally-gated shape does
  not match this requirement's own mode-DEPENDENT acceptance text.
- **External:** none new.

## Constraints

- **Never silently applied.** Every proposed Person-note edit is a
  proposal first — no code path writes to a Person note as a direct,
  unconfirmed side effect of a chat instruction.
- **Subject to the SAME working-mode gate as every other mutating
  action** — no bespoke gating logic invented only for this capability;
  Supervised proposes-and-waits, Manual/Autonomous behave exactly as they
  already do for any other mutating Skill (`REQ-SB-39-US-02`/`ADR-029`).
- **Never fabricate a Person-note match.** A mentioned name that does not
  resolve to a real, existing Person note produces an honest "not found"
  outcome — never a created note, never a best-guess match.
- **No new Person note is ever created by a mention** — this story only
  edits an already-existing Person note; creating one from a bare
  `@mention` is out of scope (see Non-Goals).

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-49-US-02-T01 | backend | New `app/business/cockpit/person_note_proposals.py` module (create/list/confirm/discard, stored in `cockpit_threads.json`) + `cockpit_router.py` confirm/discard endpoints + `threads.py` public save wrapper | `src/backend/app/business/cockpit/person_note_proposals.py`, `src/backend/app/api/cockpit_router.py`, `src/backend/app/business/cockpit/threads.py` | `Implementation/Tasks/REQ-SB-49-US-02-T01-person-note-proposals-module-and-endpoints.md` |
| REQ-SB-49-US-02-T02 | backend | New mutating Skill `propose_person_note_update` — `skill_tools.SKILLS` entry + handler, granted to `people-producer` | `src/backend/app/business/skill_tools.py`, `src/backend/app/business/skill_registry.py`, `src/backend/app/data_access/vault_writer.py` | `Implementation/Tasks/REQ-SB-49-US-02-T02-propose-person-note-update-skill.md` |
| REQ-SB-49-US-02-T03 | backend | New `"cockpit_mention"` trigger literal on `skill_registry.invoke_skill` | `src/backend/app/business/skill_registry.py` | `Implementation/Tasks/REQ-SB-49-US-02-T03-cockpit-mention-trigger-literal.md` |
| REQ-SB-49-US-02-T04 | backend | `_dispatch_skill(..., already_approved=False)` seam + Approve-endpoint wiring | `src/backend/app/business/skill_registry.py`, `src/backend/app/api/pending_approvals_router.py` | `Implementation/Tasks/REQ-SB-49-US-02-T04-dispatch-skill-already-approved-seam.md` |
| REQ-SB-49-US-02-T05 | backend | `graph.py` conditional bound tool + `_propose_person_note_update` node; name-keyed read-only resolver (`people_extraction.py`); Cockpit-thread-ref threading (`state.py`, `threads.py`) | `src/backend/app/business/agent_orchestration/graph.py`, `src/backend/app/business/agent_orchestration/state.py`, `src/backend/app/business/people_extraction.py`, `src/backend/app/business/cockpit/threads.py` | `Implementation/Tasks/REQ-SB-49-US-02-T05-graph-propose-person-note-update-tool-and-node.md` |
| REQ-SB-49-US-02-T06 | frontend | In-thread pending-proposal confirm/discard UI (reuses `.chat-proposal`) | `src/frontend/src/features/cockpit/Cockpit.tsx`, `src/frontend/src/features/cockpit/cockpitApiClient.ts` | `Implementation/Tasks/REQ-SB-49-US-02-T06-cockpit-proposal-confirm-discard-ui.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — n/a, no backend/frontend test runner scaffolded yet; all ACs verified live (Python shell + real HTTP + real CDP browser session)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

**Coder's pass (2026-08-14, `/implement-sprint SPRINT-046`):** All 6
tasks (`T01`-`T06`) built and verified live end-to-end, including both
gate-behavior paths named in `ADR-038`: Supervised (existing
Pending-Approval Approve/Decline, unchanged — `T04`'s own `AC-02`
verification) and Manual/Autonomous (the new "propose" deviation —
`T02`'s `AC-01`/`AC-03`, `T05`'s `AC-01`/`AC-04`/`AC-05`, `T06`'s `AC-06`
in-thread confirm/discard UI, all confirmed real, never a silent write).
`ADR-038` held up exactly as designed under live verification — no
adr-deviation trigger fired.

**Two real, live-discovered defects found and fixed IN-SCOPE (both
disclosed in full on `T01`'s/`T02`'s own Implementation Logs, not silent
fixes):** (1) the new `SKILLS` entry was missing the `"tool"` field a
sibling, already-landed sprint (`REQ-SB-48-US-01`) had made mandatory for
every entry — fixed in `skill_tools.py`. (2) a real save race in
`threads.send_user_message` (reads `thread` once, saves once at the end
of a per-agent-reply loop) silently clobbered a mid-loop-created pending
proposal — fixed in `threads.py`, the same file this story's own `T01`/
`T05` already list under `## Files to Modify`.

**A real, disclosed vault data-quality observation, not a build defect
(logged on `T05`'s Implementation Log):** the real vault has two
independently-existing Person notes both named "Mahmoud Moussa"
(different email addresses); `find_person_note_by_name`'s own
first-match scan correctly resolves *a* real match and never fabricates
one, but does not disambiguate between two identically-named real
notes — no Scenario in this story asserts that behavior, so this is not
a locked-AC gap.

Story `status: Done`. `gate` **stays `flagged`** (trigger-3, `ADR-038`
created) — this is the standing human-review breadcrumb for the
architectural decision itself (see the updated `REVIEW-QUEUE.md` entry),
not a build-completion blocker; the pipeline's own rule is that this gate
does not halt forward work, and the coder does not clear a gate set by
the architect for an ADR the human has not yet explicitly reviewed.

## Non-Goals / Out of Scope

- **Full NLU-driven, unbounded vault editing** — explicitly not built;
  the scope is one proposed edit per person-directed instruction, to one
  already-existing Person note, never a general free-text vault-editing
  capability.
- **Creating a new Person note from a bare `@mention`** — this story only
  edits an existing note; a mention resolving to no note is honestly
  reported, not used to trigger note creation.
- **Asserting exact prompt-engineering/NLU internals** — the ACs describe
  only the observable proposal/gating outcome, never the specific
  instruction-parsing mechanism.
- **The inline `@agent_id` bring-in shortcut** — covered by the sibling
  story `[[REQ-SB-49-US-01]]`.
- **Resolving the `ADR-036` gate-bypass-vs.-this-requirement's-own-gating
  tension** — explicitly left to `/plan-tasks` (architect), not guessed
  at here.

## Notes

**Prototype parity (meeting-cockpit.html / inbox-cockpit.html):**

- The `.chat-proposal` "Awaiting your decision" pattern (currently used
  for on-the-spot research save/discard) — **Specced (reused)** as the
  most likely visual precedent for surfacing a proposed Person-note edit
  in-thread; exact reuse vs. a small variant is a coder-level call, not
  `/design`-gated (see below).
- No approved screen anywhere shows a Person-note-edit proposal
  specifically (as opposed to a research-result proposal) — judged NOT to
  need its own `/design` pass: the existing `.chat-proposal` component
  already establishes the "proposal card in-thread, explicit Save/
  Discard-shaped choice" visual language this new proposal kind can
  directly reuse or lightly extend, per this session's own established
  precedent of not gating small, pattern-consistent additions behind a
  fresh `/design` pass. If the coder finds the reuse genuinely
  insufficient (e.g. a structured diff view is needed), that is a
  scope-internal judgement call to log, not a blocking flag here.
- The Pending Approvals surface itself (`my-day-approvals.html`) is
  reused unmodified — no new screen.

**Why `gate: flagged`:** Both live triggers are named directly above, not
guessed past:

1. **Material assumption (trigger 1).** The composing mechanism — a new
   `mutates: True` Skill dispatched through `skill_registry.invoke_skill`
   — is this story's own best-reasoned single answer to "which existing
   mechanism does this compose with," per this task's own explicit
   instruction to resolve it rather than leave it fully open. It is not
   a certainty.
2. **Unclear requirement / real tension (trigger 8, adjacent to trigger
   7).** `ADR-036`'s own already-Done, already-verified finding is that
   Cockpit actions bypass `invoke_skill`'s gate entirely, and that
   "bringing an Expert in is itself the approval." This requirement's own
   PRD breadcrumb explicitly wants a DIFFERENT outcome for this one new
   capability. Reconciling the two is a genuine architecture decision,
   not a defensible-single-reading judgement call this analyst pass can
   settle alone.

No `ESCALATIONS.md` entry written — this is forward, original speccing
work (not a reopening of a `Done` story or an out-of-scope event); the
tension is surfaced here and in `REVIEW-QUEUE.md` for the architect to
resolve at `/plan-tasks`, mirroring how `REQ-SB-43-US-01`'s own
open working-mode question was handled at `/spec` time.

**What to do next:** before `/plan-tasks REQ-SB-49-US-02` runs, a human
should confirm: (a) whether a new Skill dispatched through
`invoke_skill`'s gate is the right composing mechanism, or whether
`ADR-036`'s "bring-in is itself the approval" precedent should instead be
read as extending to this capability too (i.e., this requirement's own
"subject to working-mode gate" language would then need a narrower
reading than taken here); (b) if a gate-preserving call path is
confirmed, whether it needs a superseding/amending ADR to `ADR-036` (the
architect's own call at `/plan-tasks`, trigger 3).

gate: flagged 2026-08-14 — material assumption (composing-mechanism
reading) plus unclear-requirement (real tension with `ADR-036`'s own
already-shipped Cockpit gate-bypass finding). A `REVIEW-QUEUE.md` entry
has been added.

---

**Architect's pass (2026-08-14, `/plan-tasks` step 1) — `ADR-038` written,
resolving the tension named above, per the operator's own relayed
resolution (not re-derived independently):**

- **Call path:** a new bound tool, `propose_person_note_update(person_name,
  instruction)`, intercepted in `graph.py`'s `_route_after_model` before
  the generic `execute_tools` node — mirrors `ADR-032`'s `record_
  knowledge_gap` shape exactly, but (unlike its two graph-level siblings)
  conditionally bound only to an agent with real `skill_registry.
  has_skill_access` grant, since it composes with a real, new `mutates:
  True` Skill of the same name (granted to `people-producer`), not a
  generic ungated graph capability. A real Person-note match dispatches
  through `skill_registry.invoke_skill(..., trigger="cockpit_mention")` —
  a NEW trigger literal (not a reuse of `"chat"`/`"direct"`/`"hub_
  routed"`/`ADR-037`'s `"scheduled"`), so the FULL existing `ADR-029`
  two-axis working-mode gate applies exactly as it would for any other
  mutating Skill. No match → an honest "not found" reply, no gate
  involvement at all (Scenario 4).
- **"Propose" deviation — deliberate, mode-scoped, documented in full in
  `ADR-038`:** Supervised needs no extra step (its own Pending-Approval
  "Approve" click already is the human confirmation — Scenario 2 exactly).
  Manual/Autonomous dispatch, which has zero human click in its own path
  today, gains a new opt-in `_dispatch_skill(..., already_approved=False)`
  seam (mirrors the existing `agent_id` auto-injection precedent, a no-op
  for every other handler) so this Skill's own handler never writes on an
  unconfirmed direct dispatch — it records an explicitly confirmable/
  discardable in-thread proposal instead (new `app/business/cockpit/
  person_note_proposals.py`, mirrors `cockpit/research.py`'s own
  scoped-list/direct-`vault_writer`-on-Save shape). This satisfies the
  story's own unqualified Constraint ("no code path writes... as a direct,
  unconfirmed side effect of a chat instruction") without contradicting
  Scenario 3's own "exactly as any other mutating action, never a
  special-cased, ungated bypass" wording — that wording describes the
  shared gate's own axis decision (untouched by this ADR), not a Skill's
  own per-handler dispatch behavior.
- **Not fully decided here (decomposer/coder latitude, per `ADR-038`):**
  the exact name-keyed read-only Person-note-resolution function (sibling
  of `people_extraction.find_existing_person_note`), the exact proposed-
  edit content shape (body line vs. structured frontmatter change), and
  the exact confirm/discard endpoint routes for the Manual/Autonomous
  in-thread proposal.

**Architecture scope: §Cockpit Person-Directed Instruction (`@PersonName`)
— gate-preserving proposed Person-note edit (`REQ-SB-49-US-02`, see
`ADR-038`), §Meeting & Inbox Cockpits — multi-agent shared-thread workspace
(`ADR-036`), §In-App Agent Orchestration (LangGraph) & Shared MCP Server
(`ADR-015`) → §Agent Knowledge-Gap Tracking & Expert Readiness (`ADR-032`,
the sibling bound-tool-interception precedent), §Skills Repository —
registration & per-agent access (`ADR-015`/`ADR-028`/`ADR-029`), §Agent
Working Modes & Pending Approvals (`ADR-018`/`ADR-020`/`ADR-029`).**

`gate: flagged` (trigger 3 — `ADR-038` created) — does not halt the
decomposer; the decomposer proceeds so the human reviews `ADR-038` and the
resulting tasks together in one pass, per `Implementation/Pipeline.md`.
See `REVIEW-QUEUE.md`'s updated `REQ-SB-49-US-02` entry.

---

**Decomposer's pass (2026-08-14, `/plan-tasks` step 2):**

All 6 scenarios locked: Scenario 1→`AC-01`, Scenario 2→`AC-02`, Scenario
3→`AC-03`, Scenario 4→`AC-04`, Scenario 5→`AC-05` (analyst's wording
tightened only for AC-ID placement, no semantic change — it was already
buildable as written). **Scenario 6 (`AC-06`) is new, decomposer-authored**
under the structural-AC mandate (this story changes a screen — the Cockpit
chat thread gains a new pending-proposal region) — a DOM-structure
assertion only (region presence, confirm/discard controls), never
visual/pixel polish; reuses the same `.chat-proposal` structural pattern
already approved for the sibling quick-research proposal.

Six tasks, `REQ-SB-49-US-02-T01`..`T06` (table above), decomposing
`ADR-038`'s own Decision points directly:

- `T01` — `person_note_proposals.py` (create/list/confirm/discard,
  `cockpit_threads.json`-backed per `ADR-038` point 7) + its two new
  confirm/discard endpoints + a small public `threads.save_thread`
  wrapper (the existing `_save_thread` is private). `depends_on: []`.
- `T02` — the new `mutates: True` Skill, `propose_person_note_update`
  (`skill_tools.SKILLS` + handler + `skill_registry` grant to
  `people-producer`), plus one new `vault_writer.
  append_person_note_update_line` write primitive. The handler's
  `already_approved=False` branch calls `T01`'s `create_proposal` via a
  **deferred, function-body-local import** — mirrors `build_knowledge`'s
  own already-documented precedent for the identical reason: a
  module-level import here would complete a real circular import
  (`skill_tools` → `person_note_proposals` → `threads` → `graph` (once
  `T05` lands) → `skill_registry` → `skill_tools`), confirmed by direct
  tracing of the real import graph, not assumed. `depends_on: [T01, T03]`
  (needs `T01`'s `create_proposal` and a real `trigger="cockpit_mention"`
  value to exercise `invoke_skill` directly in its own Tests, mirroring
  `ADR-037`'s already-established "new literal, verify via direct call"
  technique).
- `T03` — the `"cockpit_mention"` `Literal[...]` addition on
  `skill_registry.invoke_skill`. Genuinely independent at the Python
  runtime level (`Literal` is a static-typing hint only, not enforced at
  call time — confirmed by direct reading of `invoke_skill`'s own body),
  so `depends_on: []`; kept as its own task per the parent instruction
  and for the type-hygiene/audit-trail reasoning `ADR-038` point 5 itself
  gives, not because anything else's runtime behaviour requires it first.
- `T04` — the `_dispatch_skill(..., already_approved=False)` seam
  (signature-introspection-forwarded, mirrors the existing `agent_id`
  auto-injection) + `pending_approvals_router.py`'s Approve branch passing
  `already_approved=True` on its one `_dispatch_skill` call site (a no-op
  for the other 11 existing handlers, none of which declare this
  parameter). `depends_on: [T02]` — its own `AC-02` verification calls
  `invoke_skill`/the Approve endpoint directly against the real
  `propose_person_note_update` Skill, never through the graph/LLM layer
  (`AC-02`'s own Gherkin is fully testable at the `invoke_skill` layer
  alone, so this does NOT need `T05`).
- `T05` — `graph.py`'s third bound-tool interception
  (`propose_person_note_update`, **conditionally** bound only when
  `skill_registry.has_skill_access` is true — this graph's first
  conditionally-bound tool, `ADR-038` point 2), the
  `_propose_person_note_update` node, one more `_route_after_model`
  branch, a new read-only `people_extraction.find_person_note_by_name`
  resolver, and threading a new optional Cockpit-thread reference
  (`cockpit_subject_kind`/`cockpit_subject_note_stem`, additive on
  `AgentConversationState` and `run_agent_conversation`'s own signature,
  default `None`) from `threads.send_user_message` through to the node,
  so the node's own `invoke_skill` call can pass `subject_kind`/
  `subject_note_stem` into the Skill's `args` for `T01`'s proposal store
  to key off. `depends_on: [T02, T03]`.
- `T06` — the frontend confirm/discard UI (`AC-06`), reusing
  `.chat-proposal`. `depends_on: [T01, T05]`.

**A real, disclosed design gap beyond `ADR-038`'s own literal text,
resolved here (not a new MUST-FLAG trigger — a scope-internal
implementation-shape decision within already-authorized architecture,
documented per this project's own "log it explicitly" precedent,
`SPRINT-037`):** `run_agent_conversation` is called from TWO real sites —
`threads.py::send_user_message` (Cockpit) and `agents_router.py::chat`
(ordinary one-on-one agent chat, entirely outside any Cockpit thread).
`ADR-038`'s own conditional-binding rule (point 2) is keyed on
`has_skill_access` alone, not on calling context — so if `people-producer`
is ever chatted with one-on-one outside a Cockpit and independently calls
this tool there, `T05`'s node would have no owning Cockpit thread to
record an in-thread proposal against. `T05`'s handler (via `T02`) resolves
this with an honest, non-crashing `{"status": "unavailable", ...}` refusal
when `subject_kind`/`subject_note_stem` are absent — never a silent write,
never an unhandled error. This story's own 6 ACs are all Cockpit-scoped
(every Gherkin `Given` opens with "a Cockpit chat has..."), so this is a
disclosed, narrowly-scoped limitation, not a locked-AC gap — full
non-Cockpit support is explicitly out of this story's scope, named in
`T05`'s own Context/Notes for a future story to pick up if ever needed.

**`REQ-SB-49-US-01` dependency — checked directly, found CONCEPTUAL only,
no `depends_on` edge added:** `REQ-SB-49-US-01-T01` (real file read) is a
client-side, deterministic regex parse (`Cockpit.tsx`'s own
`resolveMentionedAgents`) that runs at SEND time and calls the existing
`bringInAgent` HTTP endpoint for every resolved `@agent_id` token — an
unmatched token (including a person-name-shaped one like `@AhmedMoussa`)
is left byte-for-byte in the message text that is still sent to
`sendCockpitMessage` unchanged. This story's own mechanism never reads
that frontend parse's output at all — `@AhmedMoussa` reaches the backend
as part of the raw message text, and `T05`'s bound tool is triggered by
the MODEL's own free-text interpretation of that raw text (an LLM tool
call), not by any shared parsing function, regex, or data structure. Both
stories independently reason about the same `@` human-facing convention,
at two different layers (deterministic frontend regex vs. backend LLM
tool-calling), with zero shared code — confirmed by direct reading of
both stories' own real/planned call chains, not assumed. The only REAL
code dependency this story has is on `REQ-SB-39-US-02`'s already-`Done`
gate mechanism (`skill_registry.invoke_skill`/`_dispatch_skill`) — no
`depends_on` edge is written for it since its own tasks are already
`Done` (nothing left to sequence against).

Every locked AC has at least one AC-tagged manual verification step
(`AC-01`→`T02`+`T05`; `AC-02`→`T04`; `AC-03`→`T02`; `AC-04`→`T05`;
`AC-05`→`T05`; `AC-06`→`T06`). `depends_on` graph: `T03`→(none);
`T01`→(none); `T02`→`[T01,T03]`; `T04`→`[T02]`; `T05`→`[T02,T03]`;
`T06`→`[T01,T05]` — acyclic (topological order `T01, T03, T02, T04, T05,
T06`).

**Status/gate:** story advances `Draft → Ready` — every AC is locked,
every locked AC has a tagged verification step, `depends_on` is acyclic.
`gate` **stays `flagged`** (trigger 3, `ADR-038` created, carried from the
architect's pass) — this is a breadcrumb only, per
`Implementation/Pipeline.md`'s "leave it `gate: flagged` — the human
reviews the ADR and your tasks together" rule; it does not block this
decomposer pass or the story's own `Ready` transition. No new
`REVIEW-QUEUE.md`/`ESCALATIONS.md` entry written by this pass — the
existing `REQ-SB-49-US-02` `REVIEW-QUEUE.md` row (from the architect's
pass) already covers `ADR-038`'s own human-review need; this pass adds no
new open question of its own.

gate: flagged (carried, trigger-3) 2026-08-14 (decomposer) — no NEW
decomposer-owned trigger fired (no material assumption beyond the
disclosed, narrowly-scoped non-Cockpit-refusal design note above, which is
a scope-internal implementation-shape call, not a gap-filling guess; no
new `ESCALATIONS.md` entry; not oversized — 6 tasks, each one file-area,
within one working session each; every locked AC has a tagged step;
`depends_on` acyclic). Story and all 6 tasks advance to `Ready`.
