---
id: REQ-SB-96-US-01
title: Deployment truth — what the install actually has, measured against what the framework holds
requirement_ids: [REQ-SB-96]
requirement_section: "REQ-SB-96: Know What Is Actually Deployed Into the Hermes Install, and Deploy From the Framework"
phase: P2
status: Draft
gate: flagged
gate_reason: "trigger-7 + trigger-4 (contradictory input: REQ-SB-96's Findings 1 and 4 state the framework 'cannot deploy at all' and that its Hermes surface is 'entirely read-only', but SkillManager.deploy/undeploy, HermesSkills.create/update/delete, deploy_shared_managers and AgentManager's SOUL.md writes already write into the install, and SkillManager.check_deployment_drift already computes a Skill drift report with no caller but a test — logged as ESC-066, which changes this story from 'build drift' to 'fix, widen and surface an existing one')"
sprint: ""
created: 2026-10-17
updated: 2026-10-17
---

# REQ-SB-96-US-01 — Deployment truth — what the install actually has, measured against what the framework holds

## Story

**As a** Second Brain operator
**I want** one view that tells me, per artifact and per real profile, whether the
Hermes install is running what the framework holds — and says so honestly when it
has never been deployed at all
**So that** the stale-copy class of failure is visible before a job dies, instead
of being found by hand after 41 nights of silent failure

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-96* — Findings 1–3 and the first and third
  **What is wanted** bullets (the drift view; honest absence). Raised 2026-10-17 by
  the operator ("I need to know What is Deployed to Hermes and What is not") after
  three stale-copy incidents were found and fixed by hand in one day.
- **Measured findings this story must answer**, verbatim from the PRD: a
  `deployed_to:` list naming 41 profiles while every deployed `SKILL.md` was the
  7 September build and the repository's was 0.9.0; the install's own
  `<HERMES_HOME>/skills/<tool>/<slug>/` copy — the one a profile-less cron job
  resolves against — being in no list at all; `create_companies_partners.py`
  existing in three versions at once and failing nightly for 41 days.
- **Grounded against the real code, not the PRD's own summary of it.** This matters
  enough to be the story's gate reason:
  - `SkillManager.check_deployment_drift()` (`business/core/skills/skill_manager.py`)
    **already exists** and already returns `missing | stale | modified | current`
    per skill/profile pair, caching one filesystem listing per profile. Its only
    caller in the repository is `tests/test_versioning.py` — **no API route, no
    screen**. Confirmed: nothing under `app/api/` mentions drift or deploy.
  - It iterates `skill.deployed_to` — i.e. it asks the very claim Finding 1 proves
    untrustworthy, so a profile missing from the list is never examined at all.
  - It covers **Skills only**. Agents, Templates and Indexes have no equivalent.
  - The install's own `<HERMES_HOME>/skills/` tree is never read; only
    `deploy_shared_managers()` writes into `<HERMES_HOME>`, and only the shared
    managers directory.
  - `reconcile_deployed_to(dry_run=True)` and `sync_from_hermes()` already
    implement the *adopt* direction for Skills — relevant to the source-of-truth
    question `REQ-SB-96-US-02` carries, not to this story.
- **The framework already writes into the install.** `HermesSkills.create/update/
  delete` write under `<HERMES_HOME>/profiles/<profile>/skills/...`,
  `HermesProfiles.write_soul` writes `SOUL.md`, `AgentManager.create` calls it, and
  `hermes/cli.py` creates profiles and cron jobs. The PRD's "first time the
  framework would *write* into the Hermes install" is therefore not accurate as a
  statement of fact — logged as `ESC-066`. It does not weaken the PRD's conclusion
  that a deployment *operation* deserves an ADR; it changes what that ADR is about.
- **Sibling story.** `REQ-SB-96-US-02` is the write half (deploy to one profile or
  all, backup, report). This story is read-only and ships standalone: a drift view
  with no deploy button is already the thing that would have caught all three
  incidents. The split exists because one story covering both would exceed this
  project's confirmed 8–9-task sprint ceiling (recorded in `BACKLOG.md` for
  `REQ-SB-95`).

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: Per artifact, per real profile, what the install actually has

```gherkin
Given a Hermes install with real profiles carrying real deployed artifacts
When the operator opens the deployment view
Then every artifact the framework holds is listed against every profile that
    really exists on the install, enumerated from the install itself rather than
    from the framework's own deployed_to claim
  And each pairing carries a verdict of current, stale, modified or missing,
    with the framework's version, the deployed version, a content hash of each
    and the deployed copy's modified time
  And a pairing whose two sides are byte-identical reports current
  And a pairing whose deployed copy differs while claiming the same version
    reports modified, distinctly from stale
```

### Scenario 2: The copy a profile-less cron job runs is a first-class row

```gherkin
Given the install keeps its own <HERMES_HOME>/skills/<tool>/<slug>/ tree, which a
    cron job binding no profile resolves against
When the deployment view is read
Then that install-level copy appears as its own target alongside the per-profile
    copies, with the same four verdicts
  And an artifact that is current in every profile but stale in the install's own
    tree is reported as drifted, not as fully deployed
```

### Scenario 3: Never deployed says never deployed

```gherkin
Given an artifact the framework holds and has never deployed anywhere
When the deployment view is read
Then it is listed with an explicit never-deployed state
  And it is not shown as current, and not omitted from the view
  And an artifact whose deployed_to claims a profile that does not have it is
    reported as missing on that profile rather than silently dropped
```

### Scenario 4: The claim is reported beside the measurement, never instead of it

```gherkin
Given a Skill whose deployed_to names profiles that do not match what is on disk
When the deployment view is read
Then the recorded claim and the measured reality are both shown, and the verdict
    is computed from the measurement
  And the view names which profiles the claim is wrong about, in both directions —
    claimed-but-absent and present-but-unclaimed
  And nothing in this story rewrites deployed_to to make the claim agree
```

### Scenario 5: More than Skills

```gherkin
Given this install has deployed Agents (their SOUL.md and config), Templates and
    Indexes as well as Skills
When the deployment view is read
Then each of those kinds is reported with the same verdicts and the same evidence
    as Skills
  And a kind the view cannot yet compare is listed as not-compared with the reason,
    rather than being reported as current or being hidden
```

### Scenario 6: Something on the install the framework does not know about

```gherkin
Given a profile carries a deployed artifact with no counterpart in the framework
When the deployment view is read
Then that artifact is listed as install-only, naming the profile it was found in
  And nothing about it is deleted, adopted, or rewritten by viewing it
```

### Scenario 7: An unreachable install is reported, not papered over

```gherkin
Given the Hermes install is unreachable, or <HERMES_HOME> does not exist
When the operator opens the deployment view
Then the view says the install could not be read, and why
  And no artifact is reported as current on the strength of an unread install
```

## Affected Screens

- **New** deployment view (surface named by the architect — a Settings page beside
  `SettingsArtifactsPage.tsx` is the obvious candidate, as is a section of
  `SystemHealthPage.tsx`). It reuses the live approved `.item-list`/`.item-row`
  list family and the `badge badge-success` / `badge-warning` / `badge-danger`
  verdict-badge convention already live on `AgentActivityPage.tsx` and
  `SystemHealthPage.tsx`.
- `src/frontend/src/pages/SettingsPage.tsx` — one more card in the live
  `SETTINGS_SECTIONS` grid, if the architect lands it in Settings.
- `html-prototype/settings.html`, `html-prototype/system-health.html` — **not** the
  design authority for this screen (see Notes → Prototype parity).

## Dependencies

- **Blocked by:** none. This story reads; it needs nothing from `REQ-SB-95`.
- **Related to:** `REQ-SB-96-US-02` (the write half, which consumes this story's
  comparison); `REQ-SB-97-US-01` and `REQ-SB-98-US-01` (both answer "can that agent
  actually do this?" from this story's per-profile truth); `REQ-SB-99-US-01` (the
  per-profile debugger shows the same skills-with-versions facts from the profile's
  side rather than the artifact's).
- **External:** a real Hermes install to measure against.

## Constraints

- **Read-only.** Nothing in this story writes into `<HERMES_HOME>`, and nothing
  rewrites `deployed_to`, `Skill.json` or any artifact metadata — including as a
  side effect of looking. The write half is `REQ-SB-96-US-02`.
- **Measure, never trust.** No verdict may be derived from `deployed_to`; the list
  is evidence *about the framework's claim*, not about the install.
- **One Manager is the sole gateway** onto each kind's data; raw I/O stays in
  `data_access/` — the standing backend layering rule.
- **Extend `check_deployment_drift()`, do not fork it.** A second, parallel drift
  implementation is exactly the three-copies failure this requirement exists to
  stop.
- **Keep its per-profile listing discipline.** The existing code caches one
  filesystem listing per profile precisely because this is O(artifacts × profiles)
  over real trees on a 40+-profile install; a naive per-pair walk is not acceptable.
- **Windows host.** Deployed paths on this install have already broken on the
  260-character `MAX_PATH` limit (`MEMORY.md`); path handling here uses the
  established long-path helper and pruned walks.

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

- **Deploying anything** — `REQ-SB-96-US-02`.
- **Adopting the install's version into the framework** (the "adopt" direction).
  `reconcile_deployed_to()` and `sync_from_hermes()` already exist and are left
  exactly as they are; whether either becomes the default is `REQ-SB-96-US-02`'s
  open question, not this story's.
- **Drift for Actions and Workflows** — the PRD says "and (later) Action and
  Workflow"; those kinds are not fully built yet (`SPRINT-087`/`SPRINT-089`).
  `REQ-SB-97-US-01` and `REQ-SB-98-US-01` carry them.
- **Alerting, scheduling or auto-remediation of drift.** This story makes drift
  visible when looked at; nothing watches it on a timer.
- **Changing how any artifact is stored or versioned.**
- **Fixing the three incidents the PRD cites.** They were fixed by hand on
  2026-10-16; this story makes their class visible.

## Notes

**Prototype parity.** No approved prototype screen covers deployment state at all.
Enumerating the two nearest approved screens:

- `html-prototype/settings.html` — *Vault*, *Connections*, *Sections*, *Providers*
  cards: **Superseded**. The real `SettingsPage.tsx` icon-card grid replaced the
  prototype's flat card stack on 2026-08-27; a new card reuses the live grid.
- `html-prototype/system-health.html` — current-snapshot status board:
  **Deferred (not this story's surface)**. It is a right-now health board; this is
  a per-artifact comparison table. If the architect lands the view there instead,
  the status-board region gains one section and nothing else changes.
- The drift table itself (per-artifact rows, per-target verdict badges, the
  claim-vs-measurement pair) — **Specced functional-first** (Scenarios 1–6), as a
  composition of the already-approved `.item-list`/`.item-row`/`.item-row-meta` and
  badge families rather than a new visual system. This follows the operator's own
  2026-08-31 precedent (recorded in `REQ-SB-85-US-01`'s `gate_reason`, applied again
  on `REQ-SB-78`, `REQ-SB-95-US-02` and `REQ-SB-95-US-04`): build functional-first
  with existing app conventions, take the visual pass afterwards. If the human
  disagrees, `/design REQ-SB-96` before `/plan-tasks` is the cheap correction.
- Unreachable-install and empty states (Scenario 7) — **Specced** on the approved
  `.empty-state` + honest-failure convention already live on `AgentActivityPage.tsx`.

**Architect pointers for `/plan-tasks` (context, not decisions):**

- `SkillManager.check_deployment_drift()` is the seam to widen; its docstring
  already records why the per-profile cache exists and why matching is on **slug**,
  not `<category>/<slug>` (the catalog was regrouped by Tool on 2026-09-06 and
  deployed copies still sit under their old category).
- Enumerating real profiles: `HermesProfiles.get_all()` / `is_real_profile()` in
  `app/hermes/profiles.py` already distinguishes a real profile from a stray
  directory.
- "Content hash" is not a field anything stores today; the existing comparison is a
  full-text equality check on `SKILL.md`. Whether hashes are computed on read or
  recorded is the architect's call — every AC here asserts observable behaviour.
- The install's own `<HERMES_HOME>/skills/` tree has no reader at all;
  `data_access/skills.py::shared_managers_target()` is the nearest precedent for
  addressing `<HERMES_HOME>` directly.
- Whether an Agent's drift is measured on `SOUL.md`, `config.yaml` or both is open;
  note that `REQ-SB-95-US-01` publishes an operator-facts marker block into every
  `SOUL.md`, so a framework-written block inside a deployed soul is an expected
  difference, not drift — worth settling here rather than in a bug later.

**Audit breadcrumb:**

gate: flagged 2026-10-17 — trigger 7 (contradictory inputs) and trigger 4
(`ESCALATIONS.md` entry `ESC-066` written). `REQ-SB-96` is finalised in the PRD and
carries no `<!-- Draft -->` marker; no ADR was created or changed by this pass
(`REQ-SB-96`'s ADR is the architect's, at `/plan-tasks`); not oversized — the
requirement is split in two for exactly that reason; no material assumption was
made beyond what the code was read to confirm.
