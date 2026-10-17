---
id: REQ-SB-96-US-02
title: Deploy from the framework — every real target, a timestamped backup, and a report of what changed
requirement_ids: [REQ-SB-96]
requirement_section: "REQ-SB-96: Know What Is Actually Deployed Into the Hermes Install, and Deploy From the Framework"
phase: P2
status: Draft
gate: flagged
gate_reason: "trigger-8 (multiple equally-valid options, named by the PRD itself: when the framework and the install differ, 'deploy' and 'adopt' are both reasonable defaults and only one can be it — and the install already has BOTH directions half-built, SkillManager.deploy one way, reconcile_deployed_to/sync_from_hermes the other, with no decision recorded about which wins)"
sprint: ""
created: 2026-10-17
updated: 2026-10-17
---

# REQ-SB-96-US-02 — Deploy from the framework — every real target, a timestamped backup, and a report of what changed

## Story

**As a** Second Brain operator
**I want** to deploy what the framework holds into the Hermes install — to one
profile or all of them, every real target included — and see exactly what changed
**So that** deployment stops being a hand-written script that someone remembers to
run over the right folders, and the drift view reads clean afterwards

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-96* — Finding 4 and the second
  **What is wanted** bullet: "Deploy from the framework, to one profile or all,
  doing what the hand-written scripts did: write every target including the
  install's own `skills/` tree, keep a timestamped backup of what was replaced, and
  report what changed."
- **The sibling story is the measurement.** `REQ-SB-96-US-01` builds the drift view
  this story acts on and reads clean afterwards. This story is the write half, and
  is deliberately separate: one story covering both would exceed this project's
  confirmed 8–9-task sprint ceiling (recorded in `BACKLOG.md` for `REQ-SB-95`).
- **What already exists, read from the code rather than from the PRD's summary of
  it** (see `ESC-066`):
  - `SkillManager.deploy(skill_id, profile_id)` already pushes one Skill's current
    content into one real profile, refreshing the install's shared managers first
    and deliberately **not** bundling `vault_manager.py` — a local copy wins over
    `PYTHONPATH` because `sys.path[0]` is the script's own directory, which is what
    let 228 stale copies run across 41 profiles.
  - `SkillManager.update()` already re-pushes to every profile in `deployed_to`;
    `undeploy()` and `delete()` already remove from real profiles.
  - **No API route and no screen exposes any of it** — confirmed: nothing under
    `app/api/` mentions deploy. Its only callers are `artifact_import.py` and
    `AgentManager`.
  - **No target outside `<HERMES_HOME>/profiles/<profile>/skills/`** is ever
    written except the shared managers directory — so the install's own
    `<HERMES_HOME>/skills/<tool>/<slug>/` tree, the one a profile-less cron job
    resolves against, is written by nothing today. That is Finding 2.
  - **No backup is taken** of what a deploy replaces. `business/logic/
    hermes_backup.py::create_backup()` exists as a whole-install backup and is the
    nearest precedent, not the same thing.
  - **The opposite direction already exists too**: `reconcile_deployed_to()` and
    `sync_from_hermes()` pull the install's reality back into the framework. That
    is why the source-of-truth question below is a real fork and not a formality.
- **The open decision this story cannot take** (PRD, *Worth knowing before
  choosing*): which side is the source of truth when they differ — the framework's
  catalog, or the install. "Deploy" and "adopt" are both reasonable; only one can
  be the default. This story's ACs are written so the *mechanics* are verifiable
  either way, and so that a deploy over a locally-modified copy is never silent —
  but the default itself is the operator's and the architect's to settle.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: Deploy one artifact to one profile, from the framework

```gherkin
Given the drift view shows an artifact as stale on one profile
When the operator deploys it to that profile from the framework
Then the profile's copy becomes byte-identical to the framework's
  And the operation reports what it wrote, where, and what the previous version was
  And re-reading the drift view reports that pairing as current
```

### Scenario 2: Deploy to every target, including the install's own tree

```gherkin
Given an artifact deployed across many profiles, and an install that also keeps
    its own <HERMES_HOME>/skills/<tool>/<slug>/ copy
When the operator deploys that artifact to all targets
Then every profile copy is written and the install's own tree is written too
  And no real target is skipped because it was absent from deployed_to
  And a run of the drift view afterwards reports no drift for that artifact
    anywhere, including the install's own tree
```

### Scenario 3: Whatever is replaced is kept

```gherkin
Given a deploy that will overwrite existing content on a target
When the deploy runs
Then a timestamped backup of exactly what was replaced is written before the
    overwrite, and the report names where that backup is
  And a deploy that writes a target for the first time records that there was
    nothing to back up, rather than writing an empty backup
  And the backup survives the next deploy rather than being overwritten by it
```

### Scenario 4: Report what changed, not what was attempted

```gherkin
Given a deploy to many targets
When it finishes
Then the report lists, per target, whether it was written, already identical and
    skipped, or failed — with the reason for each failure
  And one target failing does not silently abandon the remaining targets
  And a deploy in which every target was already identical reports exactly that
    and writes nothing
```

### Scenario 5: A locally-modified copy is never overwritten silently

```gherkin
Given a target whose deployed copy was edited in place — same version, different
    content, the drift view's "modified" verdict
When the operator deploys over it
Then the operator is told that this target carries local modifications before
    anything is written
  And the backup taken for that target is what makes the edit recoverable
  And the report distinguishes targets that were modified from targets that were
    merely stale
```

### Scenario 6: A deploy that cannot be done honestly is refused

```gherkin
Given an artifact whose preconditions do not hold — the Hermes install is
    unreachable, a target path cannot be written, or the artifact fails the
    existing declared-writes validation
When a deploy is attempted
Then it is refused with a message naming what failed
  And nothing is partially written to that target, and no success is reported
  And the framework's own record of where the artifact is deployed is not updated
    for a target that was not actually written
```

## Affected Screens

- The deployment view from `REQ-SB-96-US-01` — gains the deploy affordance (one
  target, or all), a confirmation for the modified-copy case (Scenario 5), and the
  per-target result report (Scenario 4). Reuses the live approved `.btn`/
  `.btn-primary` and badge conventions.
- `html-prototype/settings.html`, `html-prototype/system-health.html` — **not** the
  design authority (see `REQ-SB-96-US-01` → Notes → Prototype parity, which this
  story inherits unchanged).

## Dependencies

- **Blocked by:** `REQ-SB-96-US-01` — a deploy that cannot say what it is fixing,
  and cannot be checked afterwards, is the hand-written script this requirement
  exists to replace.
- **Related to:** `REQ-SB-97-US-01` / `REQ-SB-98-US-01` (an Action's and a
  Workflow's deploy state become actionable once this exists);
  `REQ-SB-85-US-03` (`artifact_import.py` already calls `SkillManager.deploy` and
  must keep working unchanged).
- **External:** a real Hermes install, writable.

## Constraints

- **The source-of-truth default is not decided here.** Until it is recorded (ADR,
  at `/plan-tasks`), this story must not make "the framework wins" implicit by
  building only one direction into the screen without saying so.
- **Extend `SkillManager.deploy()`, do not fork it.** Its two hard-won behaviours
  are non-negotiable: refresh the install's shared managers on every deploy, and
  never bundle `vault_manager.py` into a Skill (a local copy silently wins over
  `PYTHONPATH`).
- **Backups are additive and never pruned by this story.** A backup that the next
  deploy overwrites is not a backup.
- **No partial writes.** A target is written completely or not at all.
- **Nothing is deleted from the install.** Removal stays `undeploy()`/`delete()`'s
  job, unchanged.
- **Windows host.** The 260-character `MAX_PATH` limit has already silently broken
  real deployments on this install (`MEMORY.md`); timestamped backup paths make
  paths *longer*, so this is a live risk, not a theoretical one.
- **One Manager is the sole gateway**; raw I/O stays in `data_access/`.

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

- **The drift view itself** — `REQ-SB-96-US-01`.
- **Adopting the install's copy into the framework.** `reconcile_deployed_to()` and
  `sync_from_hermes()` already do this and are not changed here; if the operator
  decides "adopt" is the default, that is a new story, not an edit to this one.
- **Automatic deployment** — on save, on a schedule, or on drift being detected.
  Every deploy in this story is one the operator asked for.
- **Restoring from a backup.** This story writes backups; a restore flow is
  separate work.
- **Deploying Actions and Workflows** — those kinds are not finished
  (`SPRINT-087`/`SPRINT-089`); `REQ-SB-97-US-01` and `REQ-SB-98-US-01` carry their
  deploy state.
- **Provisioning or repairing cron jobs.** A job that binds no profile is a real
  cause of the PRD's Finding 2, but fixing job definitions is not deployment.

## Notes

**Prototype parity.** Inherited from `REQ-SB-96-US-01` unchanged — no approved
prototype screen covers deployment; the deploy affordance is **Specced
functional-first** on already-approved `.btn`/`.btn-primary`/badge controls, under
the operator's 2026-08-31 functional-first precedent. If the human disagrees,
`/design REQ-SB-96` before `/plan-tasks` is the cheap correction.

**Architect pointers for `/plan-tasks` (context, not decisions):**

- The source-of-truth decision is the ADR this requirement's PRD text asks for.
  Note it is **narrower than the PRD frames it**: the write boundary into
  `<HERMES_HOME>` is already crossed in several places (`ESC-066`), so the decision
  is about *default direction and precedence*, not about whether to write at all.
- `business/logic/hermes_backup.py::create_backup()` is the nearest backup
  precedent; whether a per-deploy backup lives beside it or under `<HERMES_HOME>`
  is open.
- `artifact_import.py` already calls `SkillManager.deploy(artifact_id, profile_id)`
  — any signature change is a shared-interface change and escalates.
- Scenario 2's "all targets" needs the real target enumeration from
  `REQ-SB-96-US-01`, not `deployed_to`.

**Audit breadcrumb:**

gate: flagged 2026-10-17 — trigger 8 (multiple equally-valid options: the
deploy-vs-adopt default, named as open by the PRD itself and already half-built in
both directions in the code). `REQ-SB-96` is finalised in the PRD with no
`<!-- Draft -->` marker; no ADR created or changed by this pass; no new
`ESCALATIONS.md` entry (`ESC-066`, written for `REQ-SB-96-US-01`, covers the
read-only-premise correction this story also relies on); not oversized — the
requirement is split in two for that reason.
