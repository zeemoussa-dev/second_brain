---
id: REQ-SB-04-US-01
title: Agent Vault Write Access — scoped, confirmed writes from a Hermes-connected agent
requirement_ids: [REQ-SB-04]
requirement_section: "REQ-SB-04: Agent Vault Write Access"
phase: P1
status: In Progress
gate: clear
gate_reason: "trigger-3 (ADR-025 created) — /mcp shared-secret auth + write-capable MCP tool + trigger=\"hermes\" Pending Approval dispatch. T03 (scope enforcement, AC-01/AC-02) is individually held at status: Draft/gate: flagged, blocked on REQ-SB-29-US-01 (ESCALATIONS.md -> ESC-026); T01/T02 are Ready."
sprint: "SPRINT-029"
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-04-US-01 — Agent Vault Write Access — scoped, confirmed writes from a Hermes-connected agent

## Story

**As a** Second Brain user
**I want** a Hermes-connected agent to be able to create or modify a note in
my vault only within an explicitly bounded scope, and only after I've
confirmed it
**So that** I get real value from agent-assisted note-taking through Hermes
without an external channel gaining unrestricted, silent write access to my
trusted personal vault

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-04: Agent Vault Write Access* — "A
  Hermes-connected agent may write back into the vault — not read-only.
  Because the vault's trusted status rests on nothing but the user's own
  edits having touched it until now, this is a materially bigger trust
  surface than read access and needs explicit scoping (what an agent may
  create/modify, and under what confirmation) at spec time, not assumed
  permissive-by-default." Acceptance: "A Hermes-connected agent can create
  or modify a note in the vault under an explicitly defined scope/
  confirmation rule (defined at `/spec` time); writes outside that scope are
  rejected, not silently allowed."
- **Ported from `agentic-map` REQ-019 (`kb_write` tool)** — the underlying
  "allow writes, not read-only" product decision was resolved 2026-08-10
  (operator-directed, see `Implementation/Plans/
  2026-08-10-agentic-map-requirement-port.md`); the scope/confirmation rule
  itself is explicitly deferred to "this pass" by the PRD's own text — this
  IS that pass.
- **This story shares `REQ-SB-03-US-01`'s foundational finding**: no real
  Hermes connection exists anywhere in this codebase (confirmed by direct
  grep of `src/backend`/`Implementation/Architecture/`, 2026-08-13); the
  shared MCP server (`app/api/mcp_server.py`, `ADR-015`) is architecturally
  the mechanism Hermes would reach, but has zero authentication today and
  has never been exercised by any external client. Full detail:
  `REQ-SB-03-US-01`'s own `## Context`/`## Notes` and `ESCALATIONS.md` →
  `ESC-023`. **This story adds a further, independent trust-surface
  concern on top of that shared foundation** — a write-capable tool
  registered on an unauthenticated endpoint is a materially bigger exposure
  than the read-only tools REQ-SB-03 depends on, so the `/mcp` authentication
  decision that story flags is even more load-bearing here.
- **No write tool exists on the MCP server today.** Direct inspection of
  `app/api/mcp_server.py` (2026-08-13) confirms all four registered
  `@mcp.tool()`s (`list_known_customers`, `list_known_kinds`,
  `list_known_partners`, `list_notes_in_kind_folder`) are read-only.
  `app/data_access/vault_writer.py` has real note-creation/edit primitives
  (used by the email/meeting/todo/people capture pipelines and
  `REQ-SB-35`'s Vault Filing Expert), but none is exposed as an
  agent-invocable MCP tool, and none of the existing capture pipelines
  accepts arbitrary, agent-directed content the way this requirement
  describes — they each run a fixed, pre-defined classification/filing
  routine, not "an agent decides what to write, from an arbitrary Hermes
  conversation."
- **Scoping approach — operator-confirmed, 2026-08-13, as the accepted
  direction (originally proposed here as grounded-but-unconfirmed; see
  `## Notes` for the resolution history):**
  1. **Tag/folder scope, reusing `REQ-SB-29`'s concept** (Agent-to-Tag/
     Folder Scoping — an agent assigned a vault tag/folder can only
     retrieve/act within that slice), applied to writes: an agent may only
     create/modify notes within its assigned scope. **`REQ-SB-29-US-01` is
     itself still `Draft`/`gate: flagged`, unbuilt**, and its own PRD
     breadcrumb names "how an agent's tag/folder scope is assigned" as still
     genuinely open. **This creates a real, load-bearing dependency**: this
     story's own scope-enforcement (Scenarios 1/2) cannot be built for real
     until `REQ-SB-29-US-01` actually ships with its own assignment
     mechanism resolved — a sequencing fact for `/plan-tasks`/
     `/plan-sprints`/`/implement-sprint`, not a reason this story itself
     stays unspecced.
  2. **An explicit confirmation step before a write lands, reusing
     `REQ-SB-21`'s Supervised working-mode Pending-Approvals precedent**
     (`Done` — a real My Day "Pending Approvals" surface already exists for
     background-pipeline proposals awaiting user approval/decline). Given
     Hermes's own UI is out of this project's control (per `MEMORY.md`),
     and the operator confirmed reusing this *specific* precedent (not a
     new Hermes-native mechanism), the natural, intended reading is that a
     Hermes-originated write proposal surfaces through Second Brain's own
     (extended) in-app Pending Approvals surface — the same place a
     Supervised agent's background-pipeline proposal already appears —
     rather than a bespoke Hermes-channel-native confirmation UI this
     project has no precedent for and cannot build. The exact
     presentation detail (e.g. whether a Hermes-sourced proposal is visually
     distinguished from a background-pipeline one on that same surface) is
     ordinary `/plan-tasks`/`/design` latitude, not a remaining
     requirement-level ambiguity.

## Acceptance Criteria

<!-- Locked at /plan-tasks (decomposer step). AC-01/AC-02 are the
scope-dependent scenarios -- locked regardless of REQ-SB-29-US-01's own
unbuilt state (Pipeline.md "forward is autonomous by exception"), with
their real verification tagged onto the individually-blocked
REQ-SB-04-US-01-T03 (see ESCALATIONS.md -> ESC-026). AC-03/AC-04 are
independent of scope and are fully verified by REQ-SB-04-US-01-T02. -->

### Scenario 1: A write within the agent's assigned scope, after confirmation, lands in the vault

```gherkin
Given a Hermes-connected agent has an assigned vault tag/folder scope
  And the user has confirmed a proposed write that falls within that scope
When the write is applied
Then a new or modified note appears in the vault, within the agent's
    assigned scope
  And the note is indexed the same way any other vault note is
```

<!-- AC-ID: REQ-SB-04-US-01-AC-01 | locked: true -->

### Scenario 2: A write attempt outside the agent's assigned scope is rejected, not silently allowed

```gherkin
Given a Hermes-connected agent has an assigned vault tag/folder scope
When the agent attempts to write a note outside that scope
Then the write is rejected
  And the rejection is communicated back clearly, not silently dropped
  And no note is created or modified as a result of the attempt
```

<!-- AC-ID: REQ-SB-04-US-01-AC-02 | locked: true -->

### Scenario 3: A write within scope is held pending until the user confirms it

```gherkin
Given a Hermes-connected agent proposes a write that falls within its
    assigned scope
When the user has not yet confirmed the proposal
Then the write is held pending, not applied
  And no note is created or modified until an explicit confirmation occurs
```

<!-- AC-ID: REQ-SB-04-US-01-AC-03 | locked: true -->

### Scenario 4: A declined write is discarded, not applied

```gherkin
Given a Hermes-connected agent has proposed a write within its assigned
    scope
When the user explicitly declines the proposal
Then the write is discarded
  And no note is created or modified
  And the agent/user is informed the write did not happen
```

<!-- AC-ID: REQ-SB-04-US-01-AC-04 | locked: true -->

## Affected Screens

Most plausibly `html-prototype/my-day-approvals.html` (`REQ-SB-21`'s
existing Pending-Approvals drill-down), extended to also show
Hermes-originated write proposals alongside background-pipeline ones — the
scoping decision above confirms reuse of that precedent rather than a new
surface. Not yet reconciled against the approved prototype (no `/design`
pass has occurred for this requirement) — left to `/plan-tasks`/`/design`.

## Dependencies

- **Blocked by:** `REQ-SB-03` (Conversational Agent Access via Hermes) —
  `REQ-SB-03-US-01`, `Draft`/`gate: clear` (2026-08-13 — see that story's own
  Notes). Write access is a strictly bigger trust surface than read access
  and should not ship ahead of read access's own connectivity/security
  decisions; the shared `/mcp`-authentication requirement (see
  `## Constraints`) applies identically here, with higher stakes for a
  write-capable tool.
- **Blocked by (real, load-bearing — see Context):** `REQ-SB-29`
  (Agent-to-Tag/Folder Scoping) — `REQ-SB-29-US-01`, `Draft`/`gate:
  flagged`, unbuilt. The scoping approach above is now confirmed as this
  story's direction, but this story's own scope-enforcement scenarios
  (1/2) cannot be built for real until `REQ-SB-29-US-01` ships with its own
  "how scope is assigned" question resolved. This story can still proceed
  through `/plan-tasks` (architecture/task creation) now; `/implement-sprint`
  needs `REQ-SB-29-US-01` at least `Ready`/ideally `Done` first.
- **Related to:** `REQ-SB-21` (Agent Working Modes) — `REQ-SB-21-US-01`,
  `Done`. This story's confirmed confirmation step reuses that story's
  Supervised-mode/Pending-Approvals precedent — most plausibly by extending
  its existing surface, not building a parallel one (see Affected Screens).
- **External:** the same real Hermes deployment reachability unknown named
  in `REQ-SB-03-US-01`'s `## Notes` applies here too (does not block
  `/spec`/`/plan-tasks`, only `/implement-sprint`'s live end-to-end
  verification) — `/mcp` authentication itself is now resolved (see
  `## Constraints`), not an external unknown.

## Constraints

- **Writes outside an agent's assigned scope must be rejected, never
  silently allowed** — the PRD's own literal Acceptance text; matches this
  project's standing honesty posture (`ADR-011`, `ADR-014`, `REQ-SB-33`).
- **No write may land without an explicit confirmation step** — the PRD's
  own "under what confirmation" framing; confirmed (2026-08-13) to reuse
  `REQ-SB-21`'s Pending-Approvals mechanism, most plausibly by extending its
  existing surface (see `## Affected Screens`/Dependencies).
- **`/mcp` must require real authentication for any non-loopback caller
  before this story's write-capable tool(s) are reachable (operator
  decision, 2026-08-13, shared with `REQ-SB-03-US-01`).** Minimum-viable
  shape: a shared secret/API key check (`HERMES_MCP_SHARED_SECRET`-style
  config value, mirroring `COMPASS_API_KEY`/`ANTHROPIC_API_KEY`). Higher
  stakes here than for `REQ-SB-03` — a write-capable tool on an
  unauthenticated endpoint is a materially bigger exposure than read-only
  tools.
- **Do not build a second, parallel tool-registration mechanism** for the
  write-capable MCP tool(s) this story needs — per `ADR-015`'s "grow by
  registering, not a new server per capability" rule, they register on the
  existing `app/api/mcp_server.py` instance, not a new one.
- **The scope-assignment mechanism this story depends on (`REQ-SB-29`) is
  NOT re-decided here** — reused as confirmed direction; its own still-open
  assignment question must be resolved on its own terms (that story's own
  `/spec`/`/plan-tasks` pass), not guessed into this story.
- **The write tool's own safety envelope (can it overwrite existing user
  content, only append, or only create new files) is NOT decided here** —
  a real architecture-level decision, left to `/plan-tasks`.

## Implementation Tasks

- [[REQ-SB-04-US-01-T01]] — `/mcp` shared-secret authentication for
  non-loopback callers. `status: Ready`. No `REQ-SB-29-US-01` dependency.
  No AC of this story tagged (see `## Notes`).
- [[REQ-SB-04-US-01-T02]] — write-capable MCP tool
  (`propose_vault_write`) + Pending Approvals plumbing (`trigger=
  "hermes"`, `hermes_vault_write` Approve handler). `status: Ready`,
  `depends_on: [REQ-SB-04-US-01-T01]`. Verifies `AC-03`/`AC-04`.
- [[REQ-SB-04-US-01-T03]] — ⚠️ BLOCKED — real scope enforcement
  (`_is_within_assigned_scope`). `status: Draft`, `gate: flagged`,
  `depends_on: []` (real dependency `REQ-SB-29-US-01` has no task id
  yet — see `## Notes` / `ESCALATIONS.md` → `ESC-026`). Holds `AC-01`/
  `AC-02`'s own real verification.

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Read access** — covered by `REQ-SB-03`, a separate, narrower trust
  surface.
- **Content ingestion (attachments/uploads via a Hermes channel)** —
  `REQ-SB-05`.
- **Redesigning `REQ-SB-29`'s own scope-assignment mechanism** — reused as a
  concept here, not re-litigated; that story's own open question is
  resolved on its own terms, by its own `/spec`/`/plan-tasks` pass.
- **A new, Hermes-channel-native confirmation UI** — explicitly rejected as
  the direction (see Context/Constraints); this story extends Second
  Brain's own existing in-app Pending-Approvals surface instead.
- **Unscoped or unconfirmed writes of any kind** — explicitly rejected by
  this story's own Constraints; there is no "trusted agent, no confirmation
  needed" path in this story.

## Notes

**Prototype parity:** most plausibly extends `my-day-approvals.html`
(`REQ-SB-21`'s existing Pending-Approvals drill-down) to also show
Hermes-originated write proposals — not yet reconciled; a `/design` pass
is recommended once this story reaches `/plan-tasks` to confirm the exact
presentation (e.g. whether a Hermes-sourced proposal needs visual
distinction from a background-pipeline one).

**Update, 2026-08-13 — Operator decision, gate reset to `clear`.** The
scoping approach proposed above (tag/folder scope reusing `REQ-SB-29`'s
concept, plus a confirmation step reusing `REQ-SB-21`'s Supervised/
Pending-Approvals precedent) is **confirmed as the accepted direction** —
no longer a proposal awaiting confirmation. This resolves this story's own
original trigger-8 flag (multiple equally-valid confirmation-surface
designs): reusing `REQ-SB-21`'s *specific* precedent is read as confirming
an in-app (extended Pending-Approvals) surface, not a bespoke
Hermes-channel-native mechanism this project has no way to build. The
shared `/mcp`-authentication question (originally flagged jointly with
`REQ-SB-03-US-01`) is likewise resolved: yes, real authentication, in scope,
minimum-viable shared-secret shape (see `## Constraints`).

**What remains genuinely open, and is explicitly load-bearing, not a gate
flag (per the operator's own 2026-08-13 framing):** `REQ-SB-29-US-01`'s own
"how scope is assigned" question is still unresolved, and that story is
still `Draft`/unbuilt — this story's real scope-enforcement cannot be built
until it ships. This is recorded as an ordinary cross-story `depends_on`
sequencing concern for `/plan-tasks`/`/plan-sprints` (the same shape
`REQ-SB-20-US-01` already used waiting on `REQ-SB-18-US-01`), not a
spec-level ambiguity — this story's own scenarios are fully and confidently
specced. Separately, the same real-Hermes-deployment-reachability question
named in `REQ-SB-03-US-01`'s Notes applies here too, with the same
"blocks `/implement-sprint` live verification only" scoping.

With the scoping-approach and `/mcp`-authentication questions both resolved,
`gate:` is reset to `clear`.

**What to do:** run `/plan-tasks REQ-SB-04` once `REQ-SB-03` is `Ready`
(architecture/task creation may proceed now); sequence `/implement-sprint`
behind `REQ-SB-29-US-01` reaching at least `Ready` (ideally `Done`) for the
real scope-enforcement half of this story, and behind a confirmed reachable
real Hermes deployment for live end-to-end verification — track both as
ordinary sprint-sequencing/verification concerns at that time, not here.

gate: clear 2026-08-13 — scoping approach confirmed as accepted direction
(operator decision); `/mcp` authentication resolved (shared with
`REQ-SB-03-US-01`: yes, minimum-viable shared-secret shape). The
`REQ-SB-29-US-01` dependency and the real-Hermes-deployment-reachability
question both remain genuinely open but are explicitly scoped as
sequencing/live-verification concerns, not `/spec`/`/plan-tasks` blockers.
`ESCALATIONS.md` → `ESC-023` stays `Open` (partially resolved — see its own
2026-08-13 update) since `REQ-SB-05-US-01`'s own separate open question and
the shared Hermes-reachability question remain unanswered. `REVIEW-QUEUE.md`
updated accordingly.

---

**Update, 2026-08-13 — `/plan-tasks` step 1 (architect).** One new ADR,
`ADR-025`, written — decides (1) the `/mcp` shared-secret authentication
mechanism (an ASGI middleware wrapping only the `/mcp` mount, loopback
bypass, shared with `REQ-SB-03-US-01`'s own still-`Draft`, unbuilt
Constraint — that story's own future architecture pass should reference
this ADR rather than re-design it), (2) the write-capable MCP tool
(`propose_vault_write`, new `app/business/vault_write_tools.py`) never
writes directly — it always creates a Pending Approval via a new
`trigger="hermes"` value, dispatched through `ADR-021`'s own Tier-2
`action_id`/`_APPROVAL_HANDLERS` precedent, **unconditionally bypassing
`working_mode_registry`** regardless of the target agent's own working
mode (extends `ADR-021` point 5's own bypass-by-construction precedent to
a second case), (3) the write safety envelope — reuses
`vault_writer.write_note`'s existing unconditional-overwrite semantics
as-is (no new collision-avoidance/merge primitive; Scenario 1's own "new
or modified" text directly covers overwrite-in-place of an
agent-named, not LLM-guessed, target), and (4) scope enforcement is
resolved with a **fail-closed seam** — `_is_within_assigned_scope` returns
`False` unconditionally until `REQ-SB-29-US-01` ships a real scope
registry to query, never fail-open. This closes the "write tool's own
safety envelope... left to `/plan-tasks`" Constraint above: **resolved as
reuse of `write_note`'s existing overwrite semantics, no new mechanism.**

**Architecture scope:** §"Shared MCP server — vault-query tools, one
implementation reused both ways" and its new §"Addendum (REQ-SB-04-US-01,
2026-08-13) — `/mcp` shared-secret authentication + a write-capable MCP
tool..." in `Implementation/Architecture/architecture.md`; `ADR-025` in
`Implementation/Architecture/ADR.md`. The coder is bounded to these
sections plus each task's own `## Files to Modify`.

**Gating:** `gate: flagged`, `gate_reason: trigger-3 (ADR-025
created/changed)` — MUST-FLAG trigger 3. Does not halt this pass; the
decomposer step below still runs, per Pipeline.md, so the human reviews
`ADR-025` and the resulting tasks together in one pass. `REVIEW-QUEUE.md`
updated with a pointer.

---

**Update, 2026-08-13 — `/plan-tasks` step 2 (decomposer).** All 4
Scenarios locked as `AC-01`-`AC-04` (see `## Acceptance Criteria`). Three
tasks created: `REQ-SB-04-US-01-T01` (`/mcp` auth, `status: Ready`, no
`REQ-SB-29-US-01` dependency), `REQ-SB-04-US-01-T02` (write tool +
Pending Approvals plumbing, `status: Ready`, `depends_on: [T01]`, verifies
`AC-03`/`AC-04`), and `REQ-SB-04-US-01-T03` (the real scope-match
implementation, `status: Draft`/`gate: flagged`, `depends_on: []`, holds
`AC-01`/`AC-02`'s own real verification).

**The real, load-bearing `REQ-SB-29-US-01` dependency named throughout
this story's own Context/Dependencies is confirmed, by direct glob against
`Implementation/Tasks/` at this decomposition pass, to be exactly as
described: zero `REQ-SB-29-US-01-T*.md` files exist anywhere — that story
is still `status: Draft`, never decomposed.** Mirroring `ESC-011`'s and
`ESC-018`'s own established precedent — and the operator's own 2026-08-12
confirmation (`REVIEW-QUEUE.md` → `ESC-018` entry) that per-task blocking
is the correct going-forward default — this story advances to `status:
Ready` overall (its own literal Ready criteria are genuinely satisfied:
every AC locked, every locked AC has a tagged verification step,
`depends_on` acyclic) while only `T03` is individually held at `status:
Draft`/`gate: flagged`. `T01`/`T02` are `Ready` and buildable now. A new
`ESCALATIONS.md` entry, `ESC-026`, records this finding.

**What's buildable now vs. blocked:** `T01` (auth) and `T02` (the write
tool's own reject/propose/approve/decline plumbing, verified via a direct
`pending_approval_registry` seed rather than `propose_vault_write`'s own
front door, since that front door is deliberately fail-closed until `T03`)
are fully buildable and live-verifiable today. `T03` — and therefore
Scenarios 1/2's own real, honest end-to-end verification — remains
genuinely blocked until `REQ-SB-29-US-01` ships a real scope registry.

**What to do:** (1) review `ADR-025` in
`Implementation/Architecture/ADR.md` (approve or reject — in particular
the unconditional working-mode bypass and the fail-closed scope seam),
then re-run `/plan-tasks` if it changes; (2) confirm — or override — this
pass's own per-task-blocking judgement call (already precedented at
`ESC-018`); (3) once `REQ-SB-29-US-01` is decomposed, run a follow-up
decomposer pass to replace `REQ-SB-04-US-01-T03`'s own `depends_on: []`
with the real task id(s). Full detail: `ESCALATIONS.md` → `ESC-026`;
`REVIEW-QUEUE.md`.

gate: flagged 2026-08-13 — trigger-3 (`ADR-025` created). `T03`
individually flagged/`Draft`, blocked on `REQ-SB-29-US-01`
(`ESCALATIONS.md` → `ESC-026`, `Open`); `T01`/`T02` are `Ready`. Story
overall advances to `status: Ready`.

---

**Update, 2026-08-13 — `/implement-sprint` (`SPRINT-029`).** `T01`
(`/mcp` shared-secret authentication) and `T02` (write-capable
`propose_vault_write` MCP tool + Pending Approvals plumbing) both built
and verified live, per `ADR-025`, exactly as designed — no deviation. Full
build/verification detail in each task's own Implementation Log.

`AC-03`/`AC-04` (the confirm/decline plumbing, independent of scope) are
now `Done` — verified live via the seeded-`pending_approval_registry`
technique `T02`'s own Tests block specifies: a real approve produces a
real vault write with a real `run_event` history entry; a real decline
discards the proposal with no write and its own honest history entry.

`AC-01`/`AC-02` (the scope-dependent Scenarios) remain **honestly
unverified, not silently claimed** — `T03` (real
`_is_within_assigned_scope`) stays individually `Draft`/`gate: flagged`,
blocked on `REQ-SB-29-US-01`'s own still-unshipped scope registry
(`ESCALATIONS.md` → `ESC-026`, `Open`, unchanged). A real, additional
end-to-end MCP tool call against `propose_vault_write` (over the real
loopback transport, composing with `T01`'s own auth) confirmed the
fail-closed seam behaves exactly as `ADR-025` point 6 designed: every real
invocation today is honestly rejected with a clear "out of scope" message
(`{"status": "rejected", ...}`) — never silently allowed, never fabricated
as `"pending"`. This is Scenario 2's own shape, not Scenario 1/2's own
*real* scope-match decision (there is nothing real to match against yet)
— consistent with `T02`'s own Out of Scope section, this is not tagged
`AC-01`/`AC-02` here.

**Story stays `status: In Progress`, not `Done`** — `AC-01`/`AC-02` remain
open pending `T03`, the same shape `REQ-SB-36-US-02` already established
(`MEMORY.md`, 2026-08-13) for an identically-blocked composition with this
same `REQ-SB-29-US-01` dependency. `SPRINT-029` itself reaches `Done` per
its own deliberately-scoped Definition of Done (which does not require
`T03`/`AC-01`/`AC-02`), not this story.

gate: clear 2026-08-13 — no MUST-FLAG trigger fired during this build
pass: no material assumption beyond ordinary scope-internal judgement
calls (logged in each task's own Implementation Log), no new/changed ADR,
no new `ESCALATIONS.md` entry (`ESC-026` unchanged, already `Open`), both
locked ACs this pass could verify (`AC-03`/`AC-04`) verified live and
passing, `AC-01`/`AC-02` correctly left unclaimed rather than guessed.
