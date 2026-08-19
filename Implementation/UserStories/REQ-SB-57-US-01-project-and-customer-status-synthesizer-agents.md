---
id: REQ-SB-57-US-01
title: Project & Customer Status Synthesizer Agents — regenerate Glimpse on evidence change, append History on conclusion, propose Background amendments via Pending Approvals
requirement_ids: [REQ-SB-57]
requirement_section: "REQ-SB-57: Project & Customer Status Synthesizer Agents"
phase: P1
status: Done
gate: flagged
gate_reason: "scope-internal judgement calls logged across T01-T04's own Implementation Logs — see story closing pass below"
sprint: SPRINT-057
created: 2026-08-16
updated: 2026-08-18
---

# REQ-SB-57-US-01 — Project & Customer Status Synthesizer Agents — regenerate Glimpse on evidence change, append History on conclusion, propose Background amendments via Pending Approvals

## Story

**As a** Second Brain user
**I want** a Project's Glimpse (and a Customer's rollup Glimpse) to update
automatically whenever new evidence lands under it — a Thread update, a
Meeting link-in, a manual Capture — with History only growing when
something genuinely concludes, and Background only changing through an
approved, durable-fact proposal
**So that** my Project and Customer notes are always trustworthy without me
or anyone manually maintaining them — the operator's own complaint about
today's Customer notes: "no one update this file"

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-57: Project & Customer Status
  Synthesizer Agents*. Builds the two Producer agents/mechanisms that
  actually keep `REQ-SB-54`'s Glimpse/History sections current — the piece
  that turns "a nicely structured file" into "a file that's actually
  trustworthy."
- Raised 2026-08-16, same discussion as `REQ-SB-54`/`REQ-SB-55`/`REQ-SB-56`.
- **Project Synthesizer** — triggered whenever evidence changes under a
  Project (a linked Thread updates, a Meeting links in, the operator adds a
  Capture — NOT on a fixed schedule). Rewrites that Project's Glimpse in
  full (`REQ-SB-54` point 8); appends to its History only when something
  concludes, per whatever bar this story settles on (see below).
- **Customer Synthesizer** — same mechanism, one level up: triggered
  whenever a Project underneath a Customer changes. Rewrites the Customer's
  Glimpse as a rollup (one line per active Project — "by one doc get an
  idea about what happened," the operator's own framing); appends History
  when a Project concludes; separately proposes Background amendments
  through Pending Approvals when it detects a new durable fact (distinct
  trigger from routine Glimpse regeneration — a permanent claim about the
  customer is a bigger deal than routine status noise, same reasoning as
  gating new-Project proposals).
- **Ownership enforcement — this is where `REQ-SB-54` point 7 actually gets
  built:** no other Job or Agent in this batch writes to a Glimpse or
  History section directly — a Thread update TRIGGERS Project resynthesis,
  it doesn't perform it; a Project update TRIGGERS Customer resynthesis,
  same rule. This is what prevents two agents racing to rewrite the same
  file when, e.g., a Thread update and a Meeting link-in happen close
  together.
- **Architect's own implementation choice, not flagged here (trigger 3, not
  applicable to the analyst):** whether "Project Synthesizer" and "Customer
  Synthesizer" are two distinct Agent identities or one generalized
  synthesizer Job parameterized by scope (Project vs. Customer) is left
  open by the PRD itself — "the operator's own design conversation treated
  them as the same mechanism applied at two levels, not two independently
  designed things." This story's Gherkin scenarios are written to be true
  regardless of which the architect picks — no scenario asserts a specific
  agent count or identity.
- **Genuinely open, flagged (MUST-FLAG trigger 8) — the exact bar for
  "worth a History line":** the PRD's own text (`REQ-SB-54` point 5) says
  "A line is added only when something genuinely concludes (a Project
  closes, a renewal lands) — NOT on every routine update... Exact bar for
  'worth a History line' is left to the architect/decomposer to propose
  and the operator to confirm." This is where that bar is actually
  exercised — the story cannot lock a specific, numeric or exhaustive
  "concludes" definition without either the architect proposing one and
  the operator confirming it, or the operator naming it directly. This
  story's own scenarios describe the OBSERVABLE behavior (a real,
  deliberately-conclusive test signal produces one History line; routine
  evidence changes never do) without asserting the general-purpose bar.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: A real Thread update triggers a Glimpse rewrite on its linked Project, without any other Job writing to it directly

```gherkin
Given a Project has a linked Thread (the Thread's own `project`
    frontmatter key populated, set only by `finalize_thread_project_routing`)
When that Thread receives a new message (captured under REQ-SB-55) and
    `thread_match_merge` updates it
Then the Project's own `<project-slug>.md` concept file `## Glimpse`
    section is rewritten in full, within the same pipeline run,
    reflecting the new evidence
  And no Job other than the Project Synthesizer wrote to `## Glimpse` —
    the Thread-capture pipeline only triggered resynthesis (a call into
    the Synthesizer), it did not perform the write itself
```
<!-- AC-ID: REQ-SB-57-US-01-AC-01 -->

### Scenario 2: A concluded Project produces a Customer History line and drops out of the Customer's active Glimpse rollup, in the same pass

```gherkin
Given a Customer has an active Project whose `status` frontmatter field
    is later set (by the operator, directly in Obsidian) to `won`,
    `lost`, or `renewed` — the confirmed conclusion values
    (`architecture.md` → "Project & Customer Synthesizer")
When the Project Synthesizer next processes that Project and observes
    the transition into one of those values
Then a new, dated line is appended to the Customer's own `log.md`
  And the Customer's own concept-file `## Glimpse` (rewritten in the
    same synthesis pass) no longer lists that Project among its active
    rollup
```
<!-- AC-ID: REQ-SB-57-US-01-AC-02 -->

### Scenario 3: A deliberately-introduced new durable fact produces a Pending Approval proposing a Background amendment, not a silent rewrite

```gherkin
Given a test Customer's evidence (the content of a Thread that just
    triggered resynthesis) contains a deliberately-introduced new,
    durable fact about that customer (not routine activity)
When the Customer Synthesizer processes that evidence
Then a Pending Approval is created (action_id
    `propose_background_amendment`) proposing the Background amendment —
    the Customer's own concept-file `## Background` section is NOT
    rewritten automatically
When the operator approves the proposal
Then `## Background` is updated with the approved amendment
```
<!-- AC-ID: REQ-SB-57-US-01-AC-03 -->

### Scenario 4: Routine evidence changes update Glimpse without ever adding a History line

```gherkin
Given a Project receives an ordinary, non-concluding evidence update (a
    routine Thread reply, an ordinary Meeting link-in) whose `status`
    frontmatter stays unchanged, or moves only between `active` and
    `on_hold`
When the Synthesizer processes that update
Then the Project's own `## Glimpse` is rewritten to reflect it
  And no new line is added to that Project's own `log.md` for this
    update — `log.md` only grows when `status` transitions into `won`,
    `lost`, or `renewed`, never on routine activity
```
<!-- AC-ID: REQ-SB-57-US-01-AC-04 -->

### Scenario 5: A Customer's Glimpse rollup shows one line per active Project, regenerated fresh

```gherkin
Given a Customer has multiple Projects whose `status` is `active` or
    `on_hold`, each with its own current status
When the Customer Synthesizer runs (triggered by any one Project's own
    change)
Then the Customer's own `## Glimpse` shows exactly one line per
    active/on_hold Project, reflecting each Project's own current status
  And the whole `## Glimpse` is rebuilt fresh from current state
    (`replace_body_section`), not incrementally patched (per REQ-SB-54
    point 8)
```
<!-- AC-ID: REQ-SB-57-US-01-AC-05 -->

### Scenario 6: Two evidence changes for the same Project close together do not race or corrupt the Glimpse

```gherkin
Given a Project receives two independent evidence changes in close
    succession (a Thread update via `thread_match_merge` AND a Meeting
    link-in via `meeting_classification`'s Link-to-Thread mechanism, both
    for the same Project)
When both trigger resynthesis
Then the Project's own `## Glimpse` correctly reflects BOTH pieces of
    evidence once both have settled — no corrupted, partial, or lost
    write occurs
  And at no point did either the Thread-capture pipeline or the
    Meeting-Link Job write to `## Glimpse` directly — only the Project
    Synthesizer ever wrote to it
```
<!-- AC-ID: REQ-SB-57-US-01-AC-06 -->

## Affected Screens

None — backend only. Whatever new agent identity/identities this story
introduces (per the architect's own open implementation choice on
Project-vs-Customer-Synthesizer agent count) render on the Agents Map's
already agent-count-agnostic canvas with zero bespoke code, per the
established precedent (`REQ-SB-53-US-01`'s own Context). Any new Background-
amendment Pending Approval reuses the existing generic Pending Approvals
card (`my-day-approvals.html`), same as `REQ-SB-55-US-01`'s own two new
approval kinds.

## Dependencies

- **Blocked by:** `REQ-SB-54-US-01` (Vault Knowledge Model Redesign,
  `Draft`, `gate: flagged`) — the data model this story synthesizes into,
  including the ownership rule (point 7) this story is the actual
  mechanism for.
- **Blocked by:** `REQ-SB-55-US-01` (Email Capture & Threading Pipeline,
  `Draft`, `gate: clear`) — one of the two evidence-change triggers this
  story keys off (a Thread update).
- **Blocked by:** `REQ-SB-56-US-01` (Meeting Capture & Thread Linking,
  `Draft`, `gate: flagged`) — the second evidence-change trigger this
  story keys off (a Meeting link-in).
- **Related to:** `REQ-SB-21` (Agent Working Modes / Pending Approvals,
  `Done`) — the existing approval surface Background-amendment proposals
  reuse.
- **Related to:** `REQ-SB-58-US-01` (Customer/Project-Aware Expert) —
  depends on THIS story to keep Glimpse current; this story does not itself
  read Glimpse back out for chat answering.
- **External:** none beyond the already-live vault-write mechanisms this
  story extends.

## Constraints

- **Exactly one owner writes Glimpse/History per note** (`REQ-SB-54` point
  7) — no other Job/Agent in this codebase may write to a Glimpse or
  History section directly; every other capture/link mechanism only
  triggers resynthesis.
- **Glimpse is always fully regenerated, never incrementally patched**
  (`REQ-SB-54` point 8, Scenario 5).
- **History is append-only and grows only on genuine conclusion** — the
  exact bar for "genuine conclusion" is NOT locked by this story; do not
  silently invent a specific rule (e.g. "any `status` field change") at
  `/plan-tasks` without the architect proposing it and the operator
  confirming it first (see Notes).
- **A new durable fact about a Customer routes through Pending Approvals**
  — never a silent Background rewrite (Scenario 3), same reasoning as a
  new-Project proposal (`REQ-SB-55`).
- **Whether Project Synthesizer and Customer Synthesizer are one or two
  agent identities is an architect-level call** — this story's scenarios
  must remain true under either choice; do not write a task or AC that
  hardcodes a specific agent count.
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).

## Implementation Tasks

<!-- Decomposer's own table (/plan-tasks step 2) — supersedes the
analyst's non-authoritative starting point above. The History-line bar is
resolved (see `## Notes`, "Resolved 2026-08-18"), so the conclusion-
trigger logic is folded directly into T01/T02 rather than kept as its own
task — there is no separately-buildable "History-line trigger" unit once
the concrete rule is known: it is one comparison inside `synthesize_project`
(T01) and one parameter threaded into `synthesize_customer` (T02). The two
real evidence-change TRIGGER call sites the analyst's own table didn't
separately name (`thread_match_merge`'s pipeline node, `meeting_
classification.py`'s Link-to-Thread mechanism) are wired directly into
T01 (Thread pipeline — Scenario 1's own literal trigger point) and T03
(Meeting link-in — its own separate, small, independently-verifiable
task, since it touches a different file/module than T01/T02 and has no
other reason to block on the Customer-level work in T02). -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-57-US-01-T01 | backend | Project Synthesizer core (Glimpse regeneration + History-line conclusion trigger) + Thread-pipeline trigger wiring + new Agent identity | `app/business/project_customer_synthesizer.py` (new), `app/data_access/vault_writer.py`, `app/business/agent_registry.py`, `app/business/pipelines/email_capture_pipeline.py` | `../Tasks/REQ-SB-57-US-01-T01-project-synthesizer-core-and-thread-trigger.md` |
| REQ-SB-57-US-01-T02 | backend | Customer Synthesizer core (rollup Glimpse + History-line cascade + drop-from-rollup) + Route-to-Project-approval trigger wiring | `app/business/project_customer_synthesizer.py`, `app/business/email_classification.py` | `../Tasks/REQ-SB-57-US-01-T02-customer-synthesizer-and-route-to-project-trigger.md` |
| REQ-SB-57-US-01-T03 | backend | Meeting-link-in trigger wiring | `app/business/meeting_classification.py` | `../Tasks/REQ-SB-57-US-01-T03-meeting-link-trigger.md` |
| REQ-SB-57-US-01-T04 | backend | Background-amendment durable-fact detection + Pending Approval proposal/finalize | `app/business/project_customer_synthesizer.py`, `app/data_access/compass_client.py`, `app/api/pending_approvals_router.py` | `../Tasks/REQ-SB-57-US-01-T04-background-amendment-proposal.md` |

`depends_on`: `T02`→`T01`; `T03`→`T01`; `T04`→`T02`. `T01`/`T03` sit on
one independent build lane, `T01`→`T02`→`T04` on the other; `T02`/`T03`
may build in either order relative to each other once `T01` lands.

## Definition of Done

- [x] The History-line "conclusion" bar has been proposed by the architect
      and confirmed by the operator, recorded in this story's `## Notes`
      (resolved 2026-08-18) — the decomposer's own task table folds this
      rule directly into `T01`/`T02`; there is no longer a separate
      "History-line trigger" task named `T03` (that id now names the
      Meeting-link-in trigger task instead)
- [x] All acceptance-criteria scenarios pass (`AC-01`/`AC-04` — `T01`;
      `AC-02`/`AC-05` — `T02`; `AC-06` — `T03`; `AC-03` — `T04`; all
      verified live against the real configured vault, see each task's
      own `## Implementation Log`)
- [x] Every Implementation Task above is complete (`T01`-`T04` all `Done`)
- [x] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists) — n/a, manual-mode verification only; test tooling still pending project-wide
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Producing the evidence itself** (Thread updates, Meeting links, manual
  Captures) — `REQ-SB-54`/`REQ-SB-55`/`REQ-SB-56`'s own scope; this story
  only reacts to it.
- **Glimpse-first chat answering** — `REQ-SB-58`'s own scope; this story
  only keeps Glimpse current, it does not read it back out for chat.
- **Backfilling historical evidence** — `REQ-SB-59`'s own scope.
- **Locking the exact History-line "conclusion" bar** — genuinely open,
  flagged for architect proposal + operator confirmation (see Notes).
- **Deciding Project-vs-Customer-Synthesizer agent identity count** — an
  architect-level implementation choice, not resolved here.

## Notes

**Prototype parity:** N/A — no new `html-prototype/` screen region; any new
agent identity or Pending Approval kind reuses already-generic, already-
approved surfaces (see Affected Screens).

**Why `gate: flagged` (MUST-FLAG trigger 8):**

The exact bar for "worth a History line" is explicitly, verbatim left open
by the PRD itself (`REQ-SB-54` point 5): "Exact bar for 'worth a History
line' is left to the architect/decomposer to propose and the operator to
confirm — flagged open below." `REQ-SB-54-US-01` only establishes that
History exists and is append-only; THIS story is where that bar becomes
concretely load-bearing (`T03`, Scenario 4's own boundary). No PRD text,
code precedent, or resolved clarifying answer supplies a specific,
buildable definition of "genuinely concludes" — a Project's `stage`
frontmatter field reaching some particular value is a plausible mechanical
signal, but the PRD never confirms which value(s) count, so this story does
not invent one.

No other trigger fired: no other material assumption was made (the
Project-vs-Customer-Synthesizer agent-count question is explicitly framed
by the PRD as an architect implementation choice with no product-level
ambiguity, not a MUST-FLAG item for the analyst — trigger 3, not
applicable); `REQ-SB-57` carries no `<!-- Draft -->` marker; no ADR was
created by this pass; no `ESCALATIONS.md` entry was written — this is a
forward, PRD-acknowledged design question awaiting architect proposal plus
operator confirmation, not a backward pipeline step or a genuinely unclear
PRODUCT requirement; not oversized — two synthesis mechanisms sharing one
ownership-enforcement rule and one evidence-reaction shape, kept as one
story since (per the PRD's own framing) they are "the same mechanism
applied at two levels," not two independently-designed things; no
contradictory PRD inputs.

**What to do next:** at `/plan-tasks`, the architect proposes a specific,
concrete bar for "worth a History line" (e.g. a named set of `stage`
transitions); the operator then confirms it before `T03` is built. See
`REVIEW-QUEUE.md` for the action item.

gate: flagged 2026-08-16 — trigger-8 (the History-line "conclusion" bar is
explicitly undecided by the operator per the PRD's own text). A
`REVIEW-QUEUE.md` entry has been added.

---

**Architect pass (2026-08-16) — `/plan-tasks` step 1:**

- **Architecture scope: §"Project & Customer Synthesizer — the
  'genuinely concludes' History-line bar"**
  (`Implementation/Architecture/architecture.md`, under `## Data Model`,
  appended directly after "Meeting → Thread Linking..."), §`ADR-042`
  (unchanged, referenced — no new ADR, see below). The coder is bounded
  by that section for `T03` (History-line trigger) and the Customer
  rollup half of `T02`.
- **No new ADR.** Defining a concrete `status` enum and a transition-based
  trigger rule is a parameter/business-rule choice made WITHIN `ADR-042`'s
  already-`Accepted` OKF data model (which already established `status`
  as a generic concept-file frontmatter field, just left its allowed
  values/semantics undefined) — it introduces no new tool, framework, or
  structural boundary. Trigger-3 does not fire from this pass.
- **PROPOSAL — awaiting operator confirmation, NOT yet final.** Concrete
  definition (full reasoning in `architecture.md`'s new "Project &
  Customer Synthesizer..." section):
  - **Note:** the analyst's own Notes above use "a Project's `stage`
    field" loosely, echoing the PRD's own pre-OKF draft wording
    (`REQ-SB-54` point 4's earlier "stage, open items, key facts"
    phrasing). `ADR-042`'s own LOCKED concept-file frontmatter field list
    (point 1) uses `status`, not `stage` — this proposal uses the actual
    field name, `status`, not the analyst's now-superseded term.
  - **Project `status` enum:** `active | on_hold | won | lost | renewed`.
    `active` = default/ongoing; `on_hold` = paused, explicitly NOT a
    conclusion.
  - **Trigger:** append a dated `log.md` line iff `status` at the START
    of this Synthesizer pass differs from `status` DURING this pass, AND
    the new value is one of `won`/`lost`/`renewed`. Never on
    `active`/`on_hold`; never re-appends on repeated observation of an
    already-terminal value (idempotent).
  - **Maps directly onto the operator's own two named examples**
    (`REQ-SB-54` point 5: "a Project closes, a renewal lands"): `won`/
    `lost` together cover "closes" (a loss is exactly as much a genuine
    conclusion as a win — the bar is FINALITY, not favorability);
    `renewed` is the operator's own second case verbatim.
  - **Customer rollup:** Glimpse "active" rollup = Projects with `status`
    ∈ `{active, on_hold}`; a transition into `{won, lost, renewed}` drops
    the Project from the rollup AND appends the Customer's own `log.md`
    line, same synthesis pass (Scenario 2).
  - **`status` is operator-authored** (direct Obsidian frontmatter edit,
    same authoring convention as the rest of a concept file's narrative
    content) — the Synthesizer reads and reacts to it; it does not infer
    a conclusion from evidence text itself (out of this story's scope, a
    materially larger classification problem).
- **Gate stays `flagged` — this pass does NOT resolve trigger-8.** The
  enum and trigger rule above are the architect's proposal only; the
  operator must confirm or correct them before `T03` is built. See
  `REVIEW-QUEUE.md` for the updated pointer.

---

**Resolved 2026-08-18 — operator confirmed directly.** The architect's
proposal (Project `status` enum `active|on_hold|won|lost|renewed`;
`log.md` line appended only on transition INTO `won`/`lost`/`renewed`,
never on `active`/`on_hold`, never re-appended on repeat observation) is
confirmed as-is, no correction — it maps directly onto the operator's own
two named examples from `REQ-SB-54` point 5 ("a Project closes, a renewal
lands") with no gap. `gate: clear` as of this resolution. `T03` is now
unblocked. `REVIEW-QUEUE.md`'s corresponding entry is resolved. This also
unblocks `REQ-SB-58`/`REQ-SB-59` downstream, per the operator's own
explicit direction to properly unblock `REQ-SB-59` through the full
pipeline rather than route around it.

---

**Decomposer pass (2026-08-18) — `/plan-tasks` step 2:**

- All 6 scenarios tightened and locked as `REQ-SB-57-US-01-AC-01`
  through `-AC-06` (see `## Acceptance Criteria`) — field/mechanism
  names made concrete now that the History-line bar is resolved
  (`status` enum, `won`/`lost`/`renewed`, `log.md`, `<slug>.md`'s own
  `## Glimpse`/`## Background`). No AC marked `locked: false`.
- **Real code read directly before task-writing** (not assumed): `app/
  business/email_classification.py::thread_match_merge` (never writes
  Glimpse; the real Thread-update trigger point is its own pipeline
  node), `::route_to_project`/`::finalize_thread_project_routing` (the
  real moment a Thread's `project` frontmatter key first gets set — an
  approval-time call path entirely outside the LangGraph pipeline, so it
  needs its own separate trigger call site), `app/business/pipelines/
  email_capture_pipeline.py`'s `_build_graph`/`_route_after_thread_
  match_merge` (the real fork point `consult_librarian` already proves
  out — the new Project-resynthesis node mirrors that exact "always an
  additional destination" wiring shape), `app/business/meeting_
  classification.py`'s `_link_to_thread_by_conversation_id`/`_link_to_
  thread_by_fallback_heuristic` call sites (the real Meeting-link-in
  trigger point), and `app/data_access/vault_writer.py`'s real OKF
  primitives (`okf_directory_paths`, `create_okf_directory_baseline`'s
  `## Glimpse`/`## Background` baseline body, `replace_body_section`,
  `read_body_section`, `list_customer_projects`, `list_thread_notes`/
  `resolve_thread_note_path`, `append_person_note_update_line` as the
  `log.md` append primitive, `upsert_frontmatter_key`). Also confirmed
  `REQ-SB-63-US-01`'s `consult_librarian`/`propose_cross_cutting_update`
  → `finalize_cross_cutting_update` mechanism resolves its own
  cross-cutting-update case as a plain additive tag, NEVER a direct call
  into this story's Synthesizer (`REQ-SB-63-US-01`'s own locked
  Scenario 3/AC-03) — confirming this story's Thread/Meeting evidence
  triggers are genuinely independent of the Librarian, no wiring needed
  there. And `app/business/vault_filing_expert.py`'s `_create_cross_
  cutting_proposal`/`finalize_cross_cutting_update` pair as the
  "propose in the owning module, finalize via `_APPROVAL_HANDLERS`"
  canonical shape (`Implementation/Learnings.md`, `SPRINT-050`,
  3x-confirmed) — reused for `T04`'s own new `propose_background_
  amendment` approval kind.
- **Task-granularity judgement calls made directly, per the operator's
  own explicit direction to resolve rather than flag (documented here,
  not escalated):**
  - **One new Agent-tier identity (`project-customer-synthesizer`),
    not two** — the story's own Constraints explicitly leave this an
    implementation choice and require every AC to hold under either
    choice (confirmed: none of the 6 ACs name an agent identity or
    count). One identity, with `synthesize_project`/`synthesize_customer`
    as its own tier-less Jobs underneath it, most directly matches the
    PRD's own framing ("the same mechanism applied at two levels, not
    two independently designed things") and needs no new ADR — it
    extends `ADR-043`'s already-`Accepted` "one Agent-tier identity per
    mechanism, Jobs stay tier-less" shape via `agent_registry.py`'s own
    existing, already-established extensibility point, the same class
    of registration `email-capture-pipeline`/`meeting-capture` already
    used — not a new tool, framework, or structural boundary (trigger-3
    does not fire).
  - **The History-line bar is folded into T01 (Project) and threaded
    into T02 (Customer), not kept as its own separate task** — once the
    concrete rule is known (operator-confirmed 2026-08-18), it is one
    frontmatter comparison inside `synthesize_project`, not an
    independently buildable/verifiable unit; splitting it out would
    produce a task with no observable behavior of its own.
  - **Meeting-link-in trigger wiring is its own task (T03), not folded
    into T01 or T02** — it edits a different file/module
    (`meeting_classification.py`) than either, is small and
    independently verifiable, and has no build dependency on T02's
    Customer-level work — only on T01's shared `resync_project_from_
    thread` helper. Kept separate rather than bundled so a
    Meeting-capture-side regression is never entangled with Thread- or
    Customer-side changes in the same task's own verification.
  - **`evidence_text` is threaded through `synthesize_project` →
    `synthesize_customer` starting at T01/T02, even though nothing
    consumes it until T04** — avoids T04 having to retrofit already-
    `Done` T01/T02 call sites; mirrors this codebase's own established
    "accepted only to match every other Job's own call shape" precedent
    (`route_to_project`'s own now-mostly-unused `email` parameter).
- **`depends_on` graph is acyclic** (`T02`→`T01`; `T03`→`T01`;
  `T04`→`T02`) — confirmed by direct inspection of the table above; no
  cross-story task dependency needed (`REQ-SB-54`/`55`/`56`/`63`/`69`
  are all already `Done`).
- **Every locked AC has a matching AC-tagged manual verification step**
  in at least one task's `## Tests`: `AC-01`/`AC-04` → `T01`; `AC-02`/
  `AC-05` → `T02`; `AC-06` → `T03`; `AC-03` → `T04`. Confirmed directly
  against each task file's own `## Tests` section below.
- **No MUST-FLAG trigger fired this pass.** No new material assumption
  (every design choice above is either operator-confirmed, a direct
  reading of real code, or an explicitly-delegated implementation
  choice the story's own Constraints already authorized); no `<!--
  Draft -->` requirement relied upon; no ADR created or changed (`ADR-
  042` extended per the architect's own already-recorded reasoning,
  not reopened); no `ESCALATIONS.md` entry needed; no task exceeds one
  working session (each of T01-T04 touches 1-4 files with a single,
  bounded mechanism); every locked AC has a real, observable
  verification path (a file read-back, per the story's own manual-mode
  Tests); no contradictory inputs; no genuinely unclear work remained
  once the real call sites were read directly.

gate: clear 2026-08-18 (decomposer) — no trigger fired this pass; see
itemized reasoning above. Story `status: Draft → Ready`; all four task
files created at `status: Ready` (see `Implementation/Tasks/REQ-SB-57-
US-01-T01` through `-T04`). Eligible for `/plan-sprints`.

---

**Coder pass (2026-08-18) — `T01` built and verified.** `REQ-SB-57-US-01-T01`
→ `status: Done` (gate: flagged — scope-internal judgement calls only, see
that task's own `## Implementation Log`). `AC-01`/`AC-04` both verified live
against the real configured vault (`Core42`, disposable Project/Thread
fixtures, fully cleaned up afterward). Story `status: Ready → In Progress`
— `T02`/`T03`/`T04` remain to build before this story can reach `Done`.

**Coder pass (2026-08-18) — `T02` built and verified.** `REQ-SB-57-US-01-T02`
→ `status: Done` (gate: flagged — scope-internal judgement calls only, see
that task's own `## Implementation Log`). `AC-02`/`AC-05` both verified live
against the real configured vault (`Core42`, disposable Project/Thread
fixtures, fully cleaned up afterward); `T01`'s own `AC-01`/`AC-04` and the
`finalize_thread_project_routing` end-to-end non-AC checks also re-verified
and still pass after this task's edits. `T03`/`T04` remain to build before
this story can reach `Done` — story stays `In Progress`.

**Coder pass (2026-08-18) — `T03` built and verified.** `REQ-SB-57-US-01-T03`
→ `status: Done` (gate: flagged — scope-internal judgement calls plus a
real, disclosed concurrent-session finding against the shared real
`Core42` Customer note, both logged in that task's own `##
Implementation Log`, and in `MEMORY.md` for future `REQ-SB-57`-family
verification). `AC-06` and the non-AC "no Thread match" regression check
both verified live against the real configured vault (`Core42`, a
disposable Project + Thread + two Meeting notes, fully cleaned up
afterward; the real `Core42.md` Glimpse was self-healed via the
already-`Done` `synthesize_customer("Core42")` after cleanup, since the
disposable Project's own real Customer-cascade write is expected,
already-`Done` behavior, not a defect of this task). `T04` remains to
build before this story can reach `Done` — story stays `In Progress`.

**Coder pass (2026-08-18) — `T04` built and verified; story closes.**
`REQ-SB-57-US-01-T04` → `status: Done` (gate: flagged — scope-internal
judgement calls only, see that task's own `## Implementation Log`).
`AC-03` verified live against the real configured vault (`Core42`, a
disposable `ZZZ-T04-Verify-Co` Customer fixture, fully cleaned up and
independently reconfirmed clean afterward): a deliberately-introduced
durable fact produced exactly one `propose_background_amendment` Pending
Approval without touching `## Background`; approving it appended the
fact to `## Background`. Both non-AC regression checks (no duplicate
proposal on a repeat observation of the same, now-recorded fact; no
Compass call and no proposal on empty `evidence_text`) also verified
live and pass. `T01`/`T02`/`T03` are all already `Done` — with `T04` now
`Done`, every task in this story's own dependency chain is complete and
every locked AC (`AC-01` through `AC-06`) has been verified live.
**Story `status: In Progress → Done`.** `gate: flagged` (not `clear`) —
carried forward from the scope-internal judgement calls logged across
`T01`-`T04`'s own Implementation Logs (none rose to a MUST-FLAG trigger;
all are spot-check items, not blockers). `BACKLOG.md`'s `REQ-SB-57` row
updated to `Done` in the same pass.
