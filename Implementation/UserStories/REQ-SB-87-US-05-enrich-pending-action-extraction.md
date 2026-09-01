---
id: REQ-SB-87-US-05
title: Enrich-stage pending-action extraction into Thread ## Actions
requirement_ids: [REQ-SB-87]
requirement_section: "REQ-SB-87: Email Thread Capture — a New, LLM-Driven Pipeline (Classify, Skip Noise, Summarize, Find Pending Actions)"
phase: P1
status: Ready
gate: clear
gate_reason: "Was flagged: trigger 8 (## Actions output shape + replace-vs-coexist, both explicitly left open by the PRD). Resolved 2026-09-01 by the architect: replace-vs-coexist is decided (replace, mirroring ## Summary — ADR-017, which flags REQ-SB-87-US-01, not this story); the exact entry PROSE shape is deliberately deferred to decomposer/coder-level prompt design, with reasoning, since it needs zero new engine capability and the one sub-question that WOULD be architectural (a dedicated Work/Tasks/ integration) is already ruled out by this story's own Non-Goals. See Notes."
sprint: "SPRINT-084"
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-05 — Enrich-stage Pending-action Extraction into Thread `## Actions`

## Story

**As** the operator relying on Threads to tell me what still needs a reply/decision
from me
**I want** the agent-driven Thread-review pass to also identify genuine pending
actions in a Thread's own messages and write them into its `## Actions` section
**So that** opening a Thread tells me not just what happened (`## Summary`) but what,
if anything, I (or someone else) still owe a reply/decision on — without having to
re-read every message myself.

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-87*, point 2 — "nothing today writes to a
  Thread's own `## Actions` section at all; a real, new LLM-driven mechanism is
  needed." Confirmed directly: `apply_thread_review.py`'s own real payload shape
  (`{thread_path, summary, short_summary, companies}`) has no `actions` key anywhere,
  and every real Thread checked directly — including freshly `job4`-processed ones
  with genuine `## Summary` content (Masdar Open Items, TAQA, Adnoc Energy AI,
  Masdar BoQ, Discuss with Mousa) — still shows a literally empty `## Actions`, even
  where the Summary content plainly implies a pending item (e.g. "asking if a Data
  CSA can engage", "suggests doing both tomorrow"). This is a genuine, currently
  100%-absent capability, not a bug — see [[REQ-SB-87-US-04]]'s own Context for the
  full diagnosis this story builds on.
- **Depends on** [[REQ-SB-87-US-04]] — this new write goes through the SAME migrated
  `apply_thread_review.py` → `vault_manager.py` call path, not a second, parallel
  writer (PRD point 7's own binding principle) — built on top of, not instead of,
  that migration.
- **Depends on** [[REQ-SB-87-US-01]] — the Thread template's own `## Actions`
  section-access declaration must be widened to permit this new mechanism's own
  caller identity. Today, `## Actions` is refused to every caller, machine or not —
  confirmed directly in BOTH `vault_lib.py`'s own `_HUMAN_OWNED_HEADERS` and
  `apply_thread_review.py`'s own separate, identically-named constant.
- PRD point 7 (prompt-driven, minimal code): pending-action extraction is real
  agent-prompt judgment over a Thread's own messages, the same "the agent decides,
  the script only applies" division of labor `apply_thread_review.py`'s own
  docstring already establishes for Summary/company-tagging — never a hand-written
  keyword/regex heuristic ("look for '?' or 'please'").
- **Still genuinely open, per the PRD's own text:** "how pending-action extraction's
  own output shape maps onto `## Actions` (a wikilink-style list? real due dates?
  tied to `Work/Tasks/`, this vault's own existing Task concept, or Thread-local
  only)" — deferred to `/plan-tasks`, not guessed here (see Notes / MUST-FLAG).

## Acceptance Criteria

### Scenario 1: A Thread with a genuine pending action gets one written into ## Actions
```gherkin
Given a Thread whose messages an agent has read and reasoned about, containing a
  genuine item still awaiting a reply/decision (a direct question, an unresolved
  ask, a "let me know by X")
When the agent-driven review pass runs (now able to write into ## Actions through the
  migrated engine)
Then that pending item is written into the Thread's own ## Actions section, in the
  agent's own real words describing what is actually pending and, where identifiable,
  who it's waiting on
  And this write goes through the exact same vault_manager.py-based mechanism
  REQ-SB-87-US-04 migrated Summary/tag writes onto — no second, bespoke write path
```
<!-- AC-ID: REQ-SB-87-US-05-AC-01 -->

### Scenario 2: A Thread with no genuine pending action gets no fabricated one
```gherkin
Given a Thread that is purely informational (an FYI, a closed/resolved item, a
  notification) with nothing genuinely still pending
When the review pass runs
Then ## Actions is left empty — no fabricated or vague "follow up" placeholder is
  ever written just to have something there
```
<!-- AC-ID: REQ-SB-87-US-05-AC-02 -->

### Scenario 3: An already-resolved item is not carried forward as still-pending
```gherkin
Given a Thread where an earlier message asked something and a later message in the
  SAME thread already answered/resolved it
When the review pass reads the whole Thread (not just its newest message)
Then that resolved item is not written into ## Actions as if it were still open
```
<!-- AC-ID: REQ-SB-87-US-05-AC-03 -->

### Scenario 4: Re-running the review pass on an unchanged Thread does not duplicate actions
```gherkin
Given a Thread already reviewed once, with a real pending action already written
  into ## Actions, and no new message has arrived since (last_summarized_at >=
  last_message_at, the Skill's own existing skip rule)
When a later job4 run reaches this Thread
Then it is skipped by the same existing skip rule REQ-SB-87-US-04 preserves —
  ## Actions is not re-written or duplicated
```
<!-- AC-ID: REQ-SB-87-US-05-AC-04 -->

### Scenario 5: A new message resolves or adds to an existing pending action
```gherkin
Given a Thread with an existing ## Actions entry, where a NEW message has since
  arrived that resolves it or adds a further genuine pending item
When the review pass re-processes this Thread (last_message_at newer than
  last_summarized_at, matching the Skill's own existing re-summarize rule)
Then ## Actions reflects the CURRENT real state of what's pending after reading the
  whole thread again — a resolved item is no longer listed, and any new genuine
  pending item is added
```
<!-- AC-ID: REQ-SB-87-US-05-AC-05 -->

### Scenario 6: ## Personal Notes is never touched by this mechanism
```gherkin
Given a Thread with content the operator has manually written into ## Personal Notes
When the review pass writes pending actions into ## Actions
Then ## Personal Notes is left completely untouched — pending-action extraction
  never reads from or writes to that section
```
<!-- AC-ID: REQ-SB-87-US-05-AC-06 -->

## Affected Screens

None — backend only; a future story may surface `## Actions` content in a Second
Brain frontend view (My Day, a Thread detail page), but that is not requested by the
PRD and not built here.

## Dependencies

- **Blocked by:** [[REQ-SB-87-US-04]] — the migrated engine call path this story's
  own new write builds on top of.
- **Blocked by:** [[REQ-SB-87-US-01]] — the Thread template's own `## Actions`
  access widening.
- **Related:** [[REQ-SB-87-US-03]] — the Capture-side sibling story; independent
  file scope, no shared files, both extend the same overall Thread concept.
- **External:** none.

## Constraints

- **Prompt-driven, minimal code (PRD point 7):** pending-action identification is
  real agent-prompt reasoning over a Thread's own messages — never a hand-written
  keyword/regex heuristic. New code here is limited to the mechanical acceptance/
  persistence of an already-agent-decided actions payload (extending
  `apply_thread_review.py`'s own input shape + one more machine-write call),
  mirroring exactly how it already applies an already-decided summary.
- `## Personal Notes` remains exclusively human-owned, untouched by this mechanism,
  in every case (Scenario 6).
- **Whether a fresh machine-written `## Actions` replaces the section's prior
  machine-written content wholesale** (mirroring `## Summary`'s own existing
  replace-not-append behavior) **or is designed to coexist with any human-added text
  in the same section is NOT decided here** — genuinely open, deferred to
  `/plan-tasks` (see Notes / MUST-FLAG). `## Actions` has never carried real content
  of either kind before this story, so there is no existing human data at risk yet,
  but the design choice itself still needs a decision before tasks are locked.
- **The exact shape a pending-action entry takes in `## Actions`** (plain bullet
  text vs. a due-date-tagged / `Work/Tasks/`-wikilinked structure) is left open per
  the PRD's own text — deferred to `/plan-tasks`.
- Same rollout/verification posture as [[REQ-SB-87-US-04]]: prove against a
  scratch-vault sample before cutting the live `job4` cron over.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-87-US-05-T01 | backend | Accept an `actions` payload field + write `## Actions` (replace-mode, `apply_thread_review` caller) | `Hermes-Provisioning/skills/company-review/summarize-and-tag-threads/scripts/apply_thread_review.py` | `REQ-SB-87-US-05-T01-write-actions-section.md` |
| REQ-SB-87-US-05-T02 | backend | Update the Thread-review pass's own prompt guidance for genuine pending-action extraction | `Hermes-Provisioning/skills/company-review/summarize-and-tag-threads/SKILL.md` | `REQ-SB-87-US-05-T02-pending-action-prompt-guidance.md` |
| REQ-SB-87-US-05-T03 | backend | Scratch-vault proving-phase verification | (verification only, real live agent pass) | `REQ-SB-87-US-05-T03-scratch-proving-verification.md` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- Any change to Summary-writing or company-tagging behavior — [[REQ-SB-87-US-04]]'s
  own scope, unchanged here.
- The new coarse Internal/Partner/Customer classification — [[REQ-SB-87-US-03]]'s
  own scope (Capture-time), not touched here.
- Surfacing `## Actions` content in any Second Brain frontend view (My Day, a Thread
  detail page) — not requested by the PRD; a real vault-note capability only.
- A dedicated `Work/Tasks/` integration (turning a pending action into a real,
  separate Task note) — one of the genuinely open shape questions above; not built
  unless/until that question is resolved in that direction.
- Fixing `BUG-042` — unrelated, already-tracked, separate Open bug.

## Notes

**Prototype parity:** not applicable — this story has no `html-prototype/` surface
(backend-only, no UI).

**MUST-FLAG triggers fired:** trigger 8 (multiple, genuinely open, PRD-acknowledged
design questions) — the exact `## Actions` output shape, and whether machine-written
actions coexist with or replace any future human-added content in the same section,
are both explicitly named as still-open in the PRD's own text ("still genuinely
open, left to `/spec`... how pending-action extraction's own output shape maps onto
`## Actions`") — not guessed here.

**Architect resolution (2026-09-01):** two sub-questions were open here;
both resolved, neither guessed:
1. **Replace vs. coexist with human-added content** — resolved: `## Actions`
   writes use `mode=replace`, mirroring `## Summary`'s own existing
   machine-write behavior exactly. `## Actions` carries no real content of
   either kind today (nothing to lose), and Scenario 5's own requirement
   that the section "reflect the CURRENT real state of what's pending after
   reading the whole thread again" — a resolved item must actually
   disappear — is something an append-only design could never represent.
   Recorded in `ADR-017` (flags `REQ-SB-87-US-01`, the story whose own
   template/engine work this decision lives inside — not re-flagged here,
   since this story introduces no separate ADR of its own).
2. **The exact entry PROSE shape** (plain bullet vs. wikilink/due-date/
   `Work/Tasks/`-linked structure) — deliberately DEFERRED, not decided,
   with reasoning: this story's own Scenario 1 AC already effectively locks
   the shape to "the agent's own real words describing what is actually
   pending and, where identifiable, who it's waiting on" — freeform prose
   needs ZERO new engine capability, since the same `modify-section` call
   `## Summary` already uses accepts arbitrary markdown text. The one
   sub-question that WOULD be a genuine architecture decision — a dedicated
   `Work/Tasks/` integration (a new note kind, a new hub-linking mechanism)
   — is already ruled OUT of this story by its own Non-Goals ("not built
   unless/until that question is resolved in that direction"). With that
   path already closed, the remaining choice is prompt-content design
   (plain bullets vs. an agent voluntarily wikilinking a Person the same way
   it already wikilinks companies into `## Summary`), correctly a
   decomposer/coder-level call, not an architecture one.

**Architecture scope:** `architecture.md` → §`vault_manager.py` Engine
Extensions — Dynamic Children & Per-Caller Access (`REQ-SB-87-US-01`,
`ADR-017`, specifically its `## Actions` write-mode + caller-identity
decisions), §Enrich-Stage Mechanics Migration & Pending-Action Extraction
(`REQ-SB-87-US-04`/`US-05`) — the decomposer and coder are bounded by these
sections plus `ADR-017`'s own full Decision text (this story touches no ADR
of its own).

gate: clear 2026-09-01 — both flagged sub-questions resolved above; the one
genuinely architectural piece is recorded in `ADR-017` (which already flags
`REQ-SB-87-US-01` for human review); the remaining open piece is correctly
non-architectural and deferred with disclosed reasoning, not guessed.

**Decomposer pass (2026-09-01):** all 6 scenarios locked
(`REQ-SB-87-US-05-AC-01`..`AC-06`), 3 tasks created (`T01`..`T03`, chain
`T01 (← REQ-SB-87-US-04-T03) → T02 → T03`). `T01`'s own mechanical write
path is verified against a hand-constructed `actions` payload (no live
agent call required to prove the write/replace-mode/access-refusal
mechanics); `T02` (prompt-only) and `T03` (the real, live agent pass
against the scratch-vault sample) are what actually prove the judgment
quality ACs (no-fabrication, resolved-item-dropped, current-state-on-
re-process). Every locked AC has at least one AC-tagged verification
step, `depends_on` is acyclic — `status` advances `Draft → Ready`, all 3
tasks written at `status: Ready`. `gate` left untouched (`clear`, both
sub-questions already resolved by the architect).
