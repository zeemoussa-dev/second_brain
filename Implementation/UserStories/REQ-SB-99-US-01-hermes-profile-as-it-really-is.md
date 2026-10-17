---
id: REQ-SB-99-US-01
title: See a Hermes profile as it really is — the full soul, skills with versions, config, jobs and toolsets
requirement_ids: [REQ-SB-99]
requirement_section: "REQ-SB-99: See a Hermes Profile As It Really Is — Soul, Skills, Config, Jobs"
phase: P2
status: Ready
gate: clear
gate_reason: "RESOLVED operator approved ADR-043, 2026-10-17 — was: trigger-3 (ADR-043 created)"
sprint: "SPRINT-091"
created: 2026-10-17
updated: 2026-10-17
---

# REQ-SB-99-US-01 — See a Hermes profile as it really is — the full soul, skills with versions, config, jobs and toolsets

## Story

**As a** Second Brain operator debugging an agent
**I want** one read-only view of what a Hermes profile is actually made of right
now — its soul exactly as written, every skill it carries at the version it
carries, its real config, the cron jobs bound to it and the toolsets enabled
**So that** the questions I answered this week by opening files on the machine are
answerable in the app

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-99* — raised 2026-10-17 by the operator:
  "I need to see the Structure of Hermes Agents and Souls and Stuff in the
  framework So I can Debug". Finding 3 is the case for it: which profile had which
  Skill version, whether a job bound a profile at all, and what a profile's soul
  says about who it acts for were each answered by hand during this week's
  incidents.
- **Grounded against the real code.** The PRD's findings check out, with one
  nuance worth recording:
  - `app/hermes/profiles.py::_soul_excerpt(profile_dir, max_len=280)` is real, and
    its output is what becomes an agent's `description`.
  - `HermesProfiles.read_soul()` returns the full `SOUL.md` and **is** called —
    by `AgentManager._to_agent()` — but it is immediately passed through
    `_split_soul_sections()` and surfaced only as the Registry's composed
    `prompt` / `guardrails` / `scope` fields. So the soul is exposed **decomposed
    into known marker blocks, never as written**, and anything outside those
    blocks is not shown anywhere. For debugging, "as written" is the whole point.
  - A profile's enabled toolsets are already readable (`hermes tools list` via
    `get_client().cli.list_tools`) but are deliberately fetched only for a single
    agent, never in the bulk `GET /agents` listing, because each one is a
    subprocess spawn. A per-profile view is exactly the right place to pay that.
  - Cron jobs are already readable (`GET /hermes/cron/jobs`,
    `business/hermes/cron_status.py`) but are not presented per profile.
  - `agents_map_adapter.py` is, as the PRD's Finding 2 says, Second Brain's own
    presentation of Hermes' definitions, shaped for a now-retired richer agent
    model — it answers what the agents are and how they relate, not what one agent
    is made of right now.
- **Read-only, and independent.** This story needs nothing from `REQ-SB-96`,
  `REQ-SB-97` or `REQ-SB-98`, and nothing from `REQ-SB-95`. It is the cheapest of
  the five requirements raised on 2026-10-17 and the one that would have shortened
  every incident this week.
- **One overlap worth naming, not duplicating.** `REQ-SB-96-US-01` answers
  "does the install match the framework?" from the *artifact's* side, across every
  profile. This story answers "what is in this profile?" from the *profile's*
  side. The skills-with-versions region is the same fact seen from the other end;
  it must be computed once, in one place, whichever story lands first.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: The soul exactly as written

```gherkin
Given a Hermes profile with a real SOUL.md
When the operator opens that profile's view
Then the full SOUL.md is shown as one verbatim document — byte-for-byte what is
    on disk, with its section order and its `## Scope` body intact
  And it is not truncated to the 280-character excerpt used elsewhere, and is
    not reassembled from the Registry's prompt/guardrails/scope fields
  And `_soul_excerpt`, `description` and `short_description` keep behaving
    exactly as they do today everywhere they are already used
```
<!-- AC-ID: REQ-SB-99-US-01-AC-01 -->

### Scenario 2: Every skill the profile carries, at the version it carries

```gherkin
Given a profile carrying several deployed skills
When the operator opens that profile's view
Then every skill really present in that profile's own skills/ tree is listed
    with its deployed version
  And each carries a verdict against what the framework holds — current, stale,
    modified or missing — produced by the same rule the framework's existing
    drift check uses, not a second implementation of it
  And a skill present in the profile that the framework's catalog does not have
    is listed with an explicit unknown-to-framework verdict, rather than omitted
```
<!-- AC-ID: REQ-SB-99-US-01-AC-02 -->

### Scenario 3: The config as it really is

```gherkin
Given a profile with its own config.yaml
When the operator opens that profile's view
Then its real configuration is shown as written — the profile's own config.yaml
    and, for a non-default profile, the install root's config.yaml — and every
    value shown names the file it was read from
  And the model, the provider and the enabled toolsets recorded for that profile
    are among what is shown
  And a key set only at the install root is labelled as inherited from the
    install root, and a key set in neither file is labelled as not set
  And no single merged "effective" value is presented, because Hermes' own
    precedence is not readable from this repository
```
<!-- AC-ID: REQ-SB-99-US-01-AC-03 -->

### Scenario 4: The cron jobs bound to this profile

```gherkin
Given cron jobs exist on the install, some in this profile's own cron/ directory
    and some only at the install root
When the operator opens that profile's view
Then exactly the jobs in this profile's own cron/ directory are listed, with
    their schedule and their last run outcome
  And a job that lives only at the install root is not attributed to a named
    profile
  And install-level jobs — the ones that run with no -p — are visible as such
    from this view, rather than invisible everywhere
  And GET /hermes/cron/jobs and the Hermes Ops screen return exactly what they
    return today
```
<!-- AC-ID: REQ-SB-99-US-01-AC-04 -->

### Scenario 5: Reading a profile changes nothing

```gherkin
Given any profile on the install
When the operator opens, refreshes and leaves that profile's view
Then nothing in <HERMES_HOME> is written, created or modified
  And no Registry record, Skill metadata or deployed_to list is updated as a side
    effect of looking
```
<!-- AC-ID: REQ-SB-99-US-01-AC-05 -->

### Scenario 6: A profile that cannot be fully read says so

```gherkin
Given a profile whose SOUL.md or config.yaml is missing or unreadable, or whose
    enabled toolsets cannot be read
When the operator opens that profile's view
Then the piece that could not be read is reported as such, naming the file it
    would have come from
  And a failed toolsets read is reported as a failed read, never as "no toolsets
    are enabled"
  And every region that could be read is still shown
  And nothing is fabricated to fill the gap, and no excerpt is presented as the
    full soul
```
<!-- AC-ID: REQ-SB-99-US-01-AC-06 -->

### Scenario 7: An unreachable install is reported, not papered over

```gherkin
Given <HERMES_HOME> is absent or is not a directory
When the operator opens a profile's view
Then the view says the install itself could not be read, and names why
  And no region is rendered as if it had been read successfully
```
<!-- AC-ID: REQ-SB-99-US-01-AC-07 -->

<!-- All seven ACs are locked (decomposer, 2026-10-17). -->


## Affected Screens

- **New** per-profile view (surface named by the architect — a dedicated page, or
  a region of the existing `AgentDetailPanel.tsx` on `AgentsMapPage.tsx`, are both
  live candidates). Reuses the live approved `.item-list`/`.item-row` list family,
  the `badge` verdict convention and the `.empty-state` honest-failure convention.
- `src/frontend/src/features/agents-map/AgentDetailPanel.tsx` — at minimum, the
  way in to this view.
- `html-prototype/agents-map.html` — the approved agent detail panel; see Notes →
  Prototype parity.

## Dependencies

- **Blocked by:** none.
- **Related to:** `REQ-SB-96-US-01` — the skills-with-versions comparison is the
  same fact from the artifact's side; whichever story is built first owns the
  comparison and the other consumes it. `REQ-SB-100-US-01` (the session transcript)
  is the other half of debugging an ask that went wrong, and is independent of this.
- **External:** a real Hermes install to read.

## Constraints

- **Strictly read-only.** No write into `<HERMES_HOME>`, no Registry mutation, no
  `deployed_to` reconciliation triggered by viewing. Editing a soul already exists
  elsewhere and is not reached from here by this story.
- **Honest absence over a plausible default.** A missing file is reported as
  missing; an excerpt is never presented as the full text.
- **Do not change the existing short description.** `_soul_excerpt`'s 280-character
  output is used as an agent's `description` across the Agents Map and must keep
  behaving exactly as it does.
- **Pay the subprocess cost only here.** Reading a profile's enabled toolsets is a
  real `hermes tools list` subprocess per agent; it must not be added to the bulk
  `GET /agents` listing path.
- **One Manager is the sole gateway**; raw I/O stays in `data_access/` and
  `app/hermes/`.
- **Windows host.** Profile trees on this install have already hit the
  260-character `MAX_PATH` limit (`MEMORY.md`); use the established long-path
  helper and pruned walks.

## Implementation Tasks

| Task | Title | Type | Depends on | ACs covered |
|---|---|---|---|---|
| `REQ-SB-99-US-01-T01` | Shared four-status verdict rule + `compare_profile_skills(profile_id)` with `unknown_to_framework` | backend | — | AC-02, AC-05 |
| `REQ-SB-99-US-01-T02` | `cron_status.list_cron_jobs()` gains an optional `profile_id`, default-unchanged | backend | — | AC-04 |
| `REQ-SB-99-US-01-T03` | An honest toolsets read — `HermesCLI` reports read failure separately from "nothing enabled" | backend | — | AC-03, AC-06 |
| `REQ-SB-99-US-01-T04` | The soul as one verbatim document, and config as two labelled layers | backend | — | AC-01, AC-03, AC-06 |
| `REQ-SB-99-US-01-T05` | `business/hermes/profile_detail.py` + one route on the view-only mirror router | backend | T01, T02, T03, T04 | AC-01 … AC-07 |
| `REQ-SB-99-US-01-T06` | The profile debug page, its route, its API client and the way in from the agent panel | frontend | T05 | AC-01 … AC-07 |

Dependency graph: `T01`, `T02`, `T03`, `T04` are four independent roots →
`T05` (composition) → `T06` (screen). Acyclic; no edge leaves this story — in
particular none into `REQ-SB-96`, which this story is independent of by
construction (`ADR-043`: `deployed_to` is not consulted on this path at all).

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Editing anything from this view** — soul, config, skills or jobs. It is a
  debugger, not a second editor; `AgentDetailPanel.tsx` already edits what is
  editable.
- **Deploying or repairing a mismatched skill** — `REQ-SB-96-US-02`.
- **Reworking the Agents Map** or retiring `agents_map_adapter.py`.
- **Session transcripts** — `REQ-SB-100-US-01`.
- **Cron job authoring or scheduling.** Jobs are listed, not managed.
- **A cross-profile comparison table** — that is `REQ-SB-96-US-01`, from the other
  side.

## Notes

**Prototype parity (`html-prototype/agents-map.html` is the prototype screen this
story touches):**

- *Settings* region of the agent detail panel — **Superseded**: the real
  `AgentDetailPanel.tsx` has moved well past the prototype's panel (scope,
  guardrails, tools, depends_on and preferred indexes were all added through
  2026-08-29 and 2026-09-03). The way in to this view attaches to the live panel.
- *Available actions* region — **Deferred (different concern)**: untouched by this
  story; `REQ-SB-95-US-02`'s Action catalogue is what gives that region meaning.
- *Chat* region — **Deferred (different concern)**: untouched.
- *Communication history* region — **Deferred (different concern)**: untouched;
  the session-level debugging the operator asked for is `REQ-SB-100-US-01`.
- The profile-detail regions themselves (full soul, skills-with-versions, config,
  bound jobs, toolsets) — **Specced functional-first** (Scenarios 1–4). No
  approved prototype screen covers them; they are a composition of the already
  approved `.item-list`/`.item-row`, `badge` and `.empty-state` families rather
  than a new visual system, following the operator's own 2026-08-31 precedent
  (recorded in `REQ-SB-85-US-01`'s `gate_reason`, applied again on `REQ-SB-78`,
  `REQ-SB-95-US-02` and `REQ-SB-95-US-04`): functional-first, visual pass
  afterwards. If the human disagrees, `/design REQ-SB-99` before `/plan-tasks` is
  the cheap correction.

**Architect pointers for `/plan-tasks` (context, not decisions):**

- Everything this story shows has an existing reader: `read_soul()`,
  `HermesSkills.get_all(profile_id)` + `read()`, `_read_yaml_file`/`_deep_merge`
  for config inheritance (Scenario 3's "inherited, not absent" is exactly what
  `_deep_merge` already models), `cli.list_tools`, and
  `business/hermes/cron_status.py`. The work is composition and a screen, not new
  access.
- Scenario 2's match verdict is `REQ-SB-96-US-01`'s comparison seen per profile —
  decide once which side owns it.
- Scenario 4's "a job that binds no profile" is the PRD's Finding 2 of
  `REQ-SB-96`, and is the one region here with real diagnostic value beyond
  listing; how unbound jobs are surfaced without inventing a profile page for them
  is the architect's call.
- Whether this is a new route or a tab inside `AgentDetailPanel.tsx` is open; the
  ACs assert content, not placement.

**Architecture scope (architect, 2026-10-17 — the coder is bounded by these
sections of `Implementation/Architecture/architecture.md`):**

Architecture scope: §What Already Answers This, and What Does Not, §One Composed
Read, §Skills With Versions — Install-First Enumeration, One Shared Verdict,
§Cron Jobs — Binding Is a Directory, Not a Field, §Config as Two Labelled Layers,
§Honest Absence — Three Different Failures, §Surface — a Page, Not an Eighth Tab
(all under `## A Hermes Profile As It Really Is — the Read-Only Debug View
(REQ-SB-99)`), plus `ADR-043`, and `ADR-003` (the view-only mirror this stays
inside).

**Three of this story's own architect pointers were corrected against the code**
— recorded in §What Already Answers This, not as a change to any scenario:

- *"`_read_yaml_file`/`_deep_merge` for config inheritance — Scenario 3's
  'inherited, not absent' is exactly what `_deep_merge` already models."*
  It does not. `_deep_merge` is `update()`'s write-patch merge; no parent
  overlay exists anywhere in this codebase, and `_read_agent` reads the
  profile's own `config.yaml` only. Scenario 3 is met by showing two labelled
  layers and naming each value's source file — never a merged "effective" value,
  which would be a guess at Hermes' own precedence.
- *"the soul is exposed decomposed into marker blocks, and anything outside
  those blocks is not shown anywhere."* Text outside `## Guardrails`/`## Scope`
  **is** exposed, inside `Agent.prompt`. What is genuinely lost is `## Scope`'s
  own body (parsed down to `folders`/`tags`) and the document's integrity.
  Scenario 1 still stands as written — a reassembled soul is not evidence.
- *"Cron jobs are already readable (`GET /hermes/cron/jobs`)."* Only the
  root/`default` profile's. `cron_status.list_cron_jobs()` passes no
  `profile_id`, so every named profile's jobs are invisible in the app today.
  Scenario 4 therefore needs the additive `profile_id` pass-through, not just a
  filter over an existing list.

Two further code facts the decomposer should size against: `GET /hermes/agents/
{id}` already returns each skill **with its version**, so Scenario 2 is a verdict
over data already served; and `GET /agents/{id}/jobs` is the **Pipeline** job
tree, unrelated to Hermes cron — do not extend it or reuse the name.

**AC authoring (decomposer, 2026-10-17):** all seven scenarios are locked
(`AC-01`…`AC-07`); none is marked non-locked. Three were **tightened** against
the architect's code-verified corrections, so each asserts something buildable
and observable rather than something the code cannot do:

- `AC-01` now says "one verbatim document, section order and `## Scope` body
  intact, not reassembled from prompt/guardrails/scope" — the original's
  "anything outside the known marker blocks" would have been satisfied by
  `Agent.prompt`, which already exposes that text, and would have missed the
  genuine loss.
- `AC-03` now asserts two labelled layers, each value naming its source file,
  with *inherited from the install root* / *not set* labels and **no** merged
  effective value. The original's "the model and provider actually in effect"
  assumed a config-inheritance model that does not exist anywhere in this
  codebase; claiming an effective value would be a guess at Hermes' own
  precedence (`ADR-043`).
- `AC-04` now names the directory as the binding ("this profile's own `cron/`
  directory"), keeps install-level jobs visible as such, and adds the
  regression clause that `GET /hermes/cron/jobs` and the Hermes Ops screen are
  unchanged — the app's cron reader has only ever seen the root profile, so
  Scenario 4 needs the additive `profile_id` pass-through, not a filter.
- `AC-06` additionally covers a **failed toolsets read**, because
  `cli.list_tools` returns `{}` both on failure and on "nothing enabled". That
  distinction is built in `T03`, not assumed.

Sizing: six tasks, M — four independent backend roots, one composition, one
screen. Inside this project's confirmed 8–9-task ceiling; the screen task
(`T06`) is the cost centre by verification effort, the established pattern for
every frontend task in `Learnings.md`.

**Audit breadcrumb:**

gate: clear 2026-10-17 (product-owner) — grouped alone into `SPRINT-091` (P2,
`~6 tasks, M`, `depends_on_sprints: []`), advanced `Draft → Ready`. No trigger
fired: the partition was forced (this was the only story both `Ready` and
ungrouped, and no sprint was in `Draft` to append to); not oversized at 6 tasks
against the 8–9 ceiling; not `Blocked`; **no cross-sprint dependency to
introduce** — all six `depends_on` edges were re-read from the task files
themselves and every one is internal, in particular none into `REQ-SB-96`, so
nothing holds this sprint behind another. `ADR-043`'s trigger-3 flag was
resolved by the operator earlier today and is not re-raised.

Earlier — gate: flagged 2026-10-17 (decomposer) — flag **carried forward unchanged** from
the architect's trigger 3 (`ADR-043` created), so the human reviews the ADR and
these six tasks in one pass. No decomposer trigger fired on its own: no material
assumption (every tightening above is traceable to the architect's
code-verified corrections in §What Already Answers This); the requirement is
finalised; no new/changed ADR; no `ESCALATIONS.md` entry; not oversized (6
tasks, each one session); every locked AC has at least one AC-tagged
verification step; `depends_on` is acyclic and no edge leaves this story — in
particular none into `REQ-SB-96`, whose `deployed_to` is deliberately not
consulted on this path. The existing `REVIEW-QUEUE.md` entry for this story was
updated in place rather than duplicated.

Earlier — gate: flagged 2026-10-17 (architect) — trigger 3 fired: `ADR-043` was created.
No other trigger. No material assumption (every claim above was read off the
code); the requirement is finalised in the PRD; no `ESCALATIONS.md` entry — the
decision contradicts no Accepted ADR, no PRD text and no `MEMORY.md` constraint,
and deliberately does not pre-empt `REQ-SB-96`'s open "which side is the source
of truth when they differ" question (enumeration direction for a read is not
authority for a write). The decomposer still runs; the human reviews `ADR-043`
and the resulting tasks in one pass.

Earlier — gate: clear 2026-10-17 (analyst) — no triggers fired. No material assumption: every scenario
restates something `REQ-SB-99` asks for, and each was checked against the real
code before being written (the 280-character excerpt, `read_soul`'s
marker-block-only exposure, the per-agent `hermes tools list` cost, the existing
cron readers). `REQ-SB-99` is finalised in the PRD with a complete Acceptance
paragraph and carries no `<!-- Draft -->` marker, and names no open question. No
ADR created or changed (the story is read-only composition over existing readers).
No `ESCALATIONS.md` entry. Not oversized — read-only, one view, roughly four or
five tasks. No contradictory inputs: the PRD's findings matched the code, with one
refinement recorded in Context rather than contradicting it. No second
equally-valid scoping — the requirement names its five regions explicitly.
