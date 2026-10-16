---
id: REQ-SB-95-US-01
title: Operator Profile — one record of who the agent acts for, published into every agent's context
requirement_ids: [REQ-SB-95]
requirement_section: "REQ-SB-95: An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution"
phase: P2
status: Draft
gate: clear
gate_reason: ""
sprint: ""
created: 2026-10-16
updated: 2026-10-16
---

# REQ-SB-95-US-01 — Operator Profile — one record of who the agent acts for, published into every agent's context

## Story

**As a** Second Brain operator
**I want** one place that records who I am, which mail addresses are mine, and
who is on my team
**So that** every agent acts for a known person with a known team, and a request
naming my own organisation ("the actions assigned to my team") can be served
instead of refused

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-95: An Agent Can Only Do What the App Can
  Do* — Finding 1 ("the agent does not know who it acts for") and the first
  **What is wanted** bullet ("An Operator Profile. One place for who the agent
  acts for: the operator's identity and mail addresses, and their team as a list
  of emails and roles. Published into every agent's context. It holds
  *membership*, not copies of people").
- **Architecture is already settled — `ADR-032`** (Accepted 2026-10-16, pending a
  human look): the Operator Profile is **configuration, not a catalogue** — one
  record at `<DATA_PATH>/data/Operator/Profile.json`, edited in Settings,
  published into every agent's context; it **absorbs `self_email`**; it holds the
  team as emails and roles, never copies of people, because the vault's Person
  notes are filenamed by email; and it is **excluded from artifact export by
  default** because it carries personal data about named colleagues.
- **Sibling stories.** `REQ-SB-95` is specced as five stories because its four
  named pieces share a spine (publish real facts into agent context, then enforce
  against them) but are not one unit of work — the same large-requirement
  precedent as `REQ-SB-82` (six-way), `REQ-SB-87` (five-way) and `REQ-SB-85`
  (three-way). This story is the **first and smallest**: a singleton record and
  the seam that publishes real operator facts into agent context.
  `REQ-SB-95-US-03` reuses that same publication seam for the Action catalogue,
  so this story deliberately lands first.
- **Grounded against the real code, not guessed.** An agent's SOUL.md text is
  composed from `prompt` + `guardrails` + `scope` in
  `AgentManager._soul_text()` (`app/business/core/agents/agent_manager.py`) —
  confirmed by direct reading. That is the one real place agent context is
  composed today, and nothing in it carries an operator fact.
- **`self_email` is not a greenfield field.** It exists as a real System setting
  (`system_settings.py`: label "Your Email Address", `env_key: SELF_EMAIL`, with
  its own `_check_email` validation), it is listed in `app/config.py`'s
  `REQUIRED_FOR_STARTUP`, it has a setup-wizard step
  (`app/business/setup_wizard.py`), and it is read by capture scripts that are
  **payload deployed into live Hermes worker profiles**. "Absorbs" therefore has
  real blast radius — see the gate flag.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: The operator records their own identity and team in one place

```gherkin
Given the operator opens the Operator Profile in Settings
When the operator records their own name, their own mail addresses, and their
    team as a list of email addresses each with a role
Then the profile is saved as one single record for this install
  And reopening the screen shows exactly what was saved, with no second place in
    the app offering to record the same facts
```

### Scenario 2: An agent answers "who is my team" from the profile, without asking

```gherkin
Given the Operator Profile records the operator's identity and a team of
    colleagues with their roles
When the operator asks any agent who their team is
Then the agent answers from the Operator Profile — naming the real recorded
    colleagues and their roles
  And the agent does not ask the operator to supply the team, and does not invent
    a colleague who is not in the profile
```

### Scenario 3: A team member's email resolves to the real person already in the vault

```gherkin
Given the Operator Profile lists a team member only as an email address and a
    role
  And the vault already holds a Person note filenamed by that same email address
When an agent is asked about that team member
Then the agent reaches the real Person note through the email address
  And the Operator Profile itself still holds only the membership entry — it does
    not hold a copy of that person's details
```

### Scenario 4: The operator's own email address lives in exactly one place

```gherkin
Given the operator's own email address was configured before the Operator
    Profile existed
When the Operator Profile becomes the place that holds it
Then exactly one surface in the app offers to edit the operator's own email
    address, and it is the Operator Profile
  And every existing consumer of that address still resolves the same real value
    — thread capture still tells the operator's own messages apart from everyone
    else's, meeting capture still recognises the operator as an attendee, and the
    setup wizard still asks for the address exactly once
```

### Scenario 5: An unconfigured profile is answered honestly, not invented around

```gherkin
Given this install has no Operator Profile recorded yet
When the operator asks an agent who their team is
Then the agent states that no Operator Profile is configured and points at where
    to configure it
  And the agent does not guess a team from mail traffic, vault notes, or anything
    else
```

### Scenario 6: The profile does not travel in an exported bundle

```gherkin
Given the Operator Profile records named colleagues and their email addresses
When the operator exports artifacts from this install as a portable bundle
Then the Operator Profile is excluded from the export by default
  And the exported bundle contains no colleague's name or email address that came
    from the profile
```

## Affected Screens

- **New** `src/frontend/src/pages/SettingsOperatorPage.tsx` (name indicative) —
  the Operator Profile editor: identity, own mail addresses, and the team as
  email+role rows. Reuses the already-approved live Settings conventions
  (`.card.settings-card` grid entry on `SettingsPage.tsx`,
  `.item-list`/`.item-row`/`.input` as used on `SettingsSystemPage.tsx`).
- `src/frontend/src/pages/SettingsPage.tsx` — one more card in the live
  `SETTINGS_SECTIONS` grid.
- `src/frontend/src/pages/SettingsSystemPage.tsx` — the "Your Email Address"
  field moves out of (or becomes a read-only pointer into) the Operator Profile,
  depending on how the flagged `self_email` absorption question is answered.
- `html-prototype/settings.html` — **not** the design authority here; the real
  `SettingsPage.tsx` card grid superseded it on 2026-08-27 (see Notes →
  Prototype parity).

## Dependencies

- **Blocked by:** none.
- **Related to:** `REQ-SB-95-US-03` (published catalogue + enforcement) — reuses
  this story's agent-context publication seam; `REQ-SB-85-US-02` (artifact
  export) — Scenario 6 constrains its default inclusion set.
- **External:** the live install's own `SELF_EMAIL` value and the Hermes worker
  profiles that already carry capture scripts reading it (see the gate flag).

## Constraints

- **One record, not a catalogue.** The Operator Profile is a singleton — no
  list/create/delete surface, no artifact kind, no id namespace.
- **Membership, not copies.** The profile stores an email and a role per team
  member and nothing else about them; the vault's Person notes remain the one
  place a person is described.
- **Excluded from artifact export by default** (`ADR-032`).
- **No second source of truth for the operator's own email.** Whichever side wins
  the flagged question, the other must stop being independently editable — a
  second place for the same fact is exactly the drift `ADR-032` names.
- Publication into agent context must be **derived**, not hand-copied into any
  agent's prompt text — editing the profile must be enough.

## Implementation Tasks

<!-- Indicative only — the decomposer owns the final split and the real IDs. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-95-US-01-T01 | backend | Operator Profile entity + Manager + data access over `<DATA_PATH>/data/Operator/Profile.json` | `src/backend/app/business/core/operator/`, `src/backend/app/data_access/` | — |
| REQ-SB-95-US-01-T02 | backend | `self_email` absorption — config/startup/setup-wizard reconciliation and consumer cutover | `src/backend/app/config.py`, `src/backend/app/business/system_settings.py`, `src/backend/app/business/setup_wizard.py` | — |
| REQ-SB-95-US-01-T03 | backend | Publish operator facts into composed agent context | `src/backend/app/business/core/agents/agent_manager.py` | — |
| REQ-SB-95-US-01-T04 | backend | Exclude the profile from artifact export by default | `src/backend/app/business/logic/artifact_export.py` | — |
| REQ-SB-95-US-01-T05 | frontend | Operator Profile Settings page + landing-grid card | `src/frontend/src/pages/` | — |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Actions, Workflows, and entity resolution** — `REQ-SB-95-US-02`/`US-03`/
  `US-04`/`US-05`.
- **Org-chart modelling** — reporting lines, hierarchies, multiple teams. One
  flat team list of email+role is what the PRD asks for.
- **Creating or editing Person notes** from this screen — the vault owns those.
- **Multi-operator installs.** One install, one operator.

## Notes

**Operator decision, 2026-10-16 — flag cleared.** Operator, 2026-10-16: `self_email` is written at provisioning and belongs in BOTH Hermes' `.env` and the Profile -- one editable source, two written locations, kept in step by the existing `setup_wizard.sync_settings_to_hermes(..., self_email)`. Deployed capture scripts keep reading the variable they read today; nothing redeploys. Accepted limitation: a running gateway does not re-read `.env`, so a changed address reaches running agents after a restart ("you don't change your email every day"). Recorded in `ADR-035`.

**Prototype parity (`html-prototype/settings.html` is the only prototype screen
in scope):**

- Settings landing navigation — **Superseded**: the real `SettingsPage.tsx`
  icon-card grid replaced the prototype's flat card stack on 2026-08-27 (its own
  header comment records the operator's instruction), and the prototype is
  additionally stale on Providers. The new Operator Profile card reuses the live
  approved grid.
- The Operator Profile editor itself — **Specced** (Scenarios 1, 4) using the
  already-approved `.item-list`/`.item-row`/`.input`/`Save changes` pattern live
  on `SettingsSystemPage.tsx`. The only genuinely new interaction is the
  repeating email+role team row, which is a list of the same approved input
  controls rather than a new visual system.
- **No `/design` pass is being requested for this story.** Following the operator's
  own 2026-08-31 precedent (recorded in `REQ-SB-85-US-01`'s `gate_reason`, applied
  again on `REQ-SB-78`): build functional-first using existing app conventions,
  and take the visual pass afterwards. If the human disagrees, `/design REQ-SB-95`
  before `/plan-tasks` is the cheap correction.

**Architect pointers for `/plan-tasks` (context, not decisions):**

- Agent context is composed in `AgentManager._soul_text()` from
  `prompt`+`guardrails`+`scope` — that is where "published into every agent's
  context" has to land, and `REQ-SB-95-US-03` will want the same seam.
- `self_email` consumers found by direct search: `app/config.py`,
  `app/business/system_settings.py`, `app/business/setup_wizard.py`,
  `app/api/setup_router.py`, and three **deployed payload** scripts under
  `business/core/skills/catalog/graph/*` (`ingest_email.py`, `ingest_meeting.py`,
  `retrofit_conversation_index.py`). The payload copies already live inside real
  Hermes worker profiles, so any cutover has a redeployment component.

**Why `gate: flagged`** (MUST-FLAG review, trigger by trigger):

1. **Material assumption** — avoided rather than made: Scenario 4 asserts the
   observable outcome ("exactly one editable place, every existing consumer still
   resolves the same value") without choosing which store wins, precisely because
   choosing would be a material assumption.
2. **Unfinalised requirement** — no. `REQ-SB-95` carries no `<!-- Draft -->`
   marker (the PRD uses none anywhere) and has a complete **Acceptance**
   paragraph.
3. N/A (architect/ADR trigger). No ADR created or changed by this pass; `ADR-032`
   is pre-existing. Noted for the human: `ADR-032` is itself still awaiting a
   look and is not in `REVIEW-QUEUE.md`.
4. No `ESCALATIONS.md` entry written for this story.
5. **Oversized** — no, and avoided by the five-way split; this is the smallest
   piece (~5 tasks, S/M).
6. N/A (coder trigger).
7. **Contradictory inputs** — not contradictory, but see trigger 8.
8. **FIRED — the controlling flag.** `self_email` absorption has two defensible
   readings and real live blast radius. See the frontmatter `gate_reason` and
   `REVIEW-QUEUE.md`.
