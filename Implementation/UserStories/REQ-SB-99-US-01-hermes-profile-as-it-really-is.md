---
id: REQ-SB-99-US-01
title: See a Hermes profile as it really is — the full soul, skills with versions, config, jobs and toolsets
requirement_ids: [REQ-SB-99]
requirement_section: "REQ-SB-99: See a Hermes Profile As It Really Is — Soul, Skills, Config, Jobs"
phase: P2
status: Draft
gate: clear
gate_reason: ""
sprint: ""
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
Then the full SOUL.md is shown as written, including anything outside the known
    marker blocks
  And it is not truncated to the 280-character excerpt used elsewhere as the
    agent's description
  And the existing short description keeps working unchanged everywhere it is
    already used
```

### Scenario 2: Every skill the profile carries, at the version it carries

```gherkin
Given a profile carrying several deployed skills
When the operator opens that profile's view
Then every skill really present in that profile is listed with its deployed
    version
  And each is marked as matching or not matching what the framework holds
  And a skill present in the profile that the framework does not know about is
    listed too, rather than omitted
```

### Scenario 3: The config as it really is

```gherkin
Given a profile with its own config.yaml
When the operator opens that profile's view
Then its real configuration is shown — including the model and provider actually
    in effect and the toolsets enabled
  And a value inherited rather than set on this profile is shown as inherited,
    not as absent
```

### Scenario 4: The cron jobs bound to this profile

```gherkin
Given cron jobs exist on the install, some bound to this profile and some not
When the operator opens that profile's view
Then exactly the jobs bound to this profile are listed, with their schedule and
    last run outcome
  And a job that binds no profile at all is not attributed to this profile
  And the view makes it possible to tell that unbound jobs exist, rather than
    leaving them invisible everywhere
```

### Scenario 5: Reading a profile changes nothing

```gherkin
Given any profile on the install
When the operator opens, refreshes and leaves that profile's view
Then nothing in <HERMES_HOME> is written, created or modified
  And no Registry record, Skill metadata or deployed_to list is updated as a side
    effect of looking
```

### Scenario 6: A profile that cannot be fully read says so

```gherkin
Given a profile whose SOUL.md or config.yaml is missing or unreadable
When the operator opens that profile's view
Then the missing piece is reported as missing, naming which file
  And the regions that could be read are still shown
  And nothing is fabricated to fill the gap, and no excerpt is presented as the
    full soul
```

### Scenario 7: An unreachable install is reported, not papered over

```gherkin
Given the Hermes install is unreachable
When the operator opens a profile's view
Then the view says the install could not be read, and why
  And no region is rendered as if it had been read successfully
```

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

<!-- Owned by the decomposer at /plan-tasks. -->

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

**Audit breadcrumb:**

gate: clear 2026-10-17 — no triggers fired. No material assumption: every scenario
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
