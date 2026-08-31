---
id: REQ-SB-85-US-02-T02
title: artifact_dependency_resolver.py — real cross-artifact dependency-closure resolution (ADR-013)
parent_story: REQ-SB-85-US-02
requirement_id: REQ-SB-85
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: []
created: 2026-08-31
updated: 2026-08-31
---

# REQ-SB-85-US-02-T02 — artifact_dependency_resolver.py: real cross-artifact dependency-closure resolution (ADR-013)

## Parent Story

- Story: [[REQ-SB-85-US-02]] — `../UserStories/REQ-SB-85-US-02-export-dependency-closure-and-secret-scan.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-85 *Artifact Export/Import — Portable Capability Bundles (`.sbf`)*

---

## Objective

Given an initial `(kind, id)` selection, resolve and return the FULL real
dependency closure — Skill shared-file copies, Agent `skill_ids`/
`depends_on` (transitively), Skill→Template implicit coupling, Pipeline
step Agents — each with a human-readable reason it was included.

---

## Starting State → End State

**Before / Inputs:**
- `SkillManager`/`TemplateManager`/`AgentManager`/`PipelineManager` are
  all real, `Done`, composable directly. `data_access.skills.
  list_scripts(skill_id)` already returns `{rel_path: content}` for a
  Skill's own real `scripts/` folder. No cross-artifact traversal exists
  anywhere today.

**After / Outputs:**
- `app/business/logic/artifact_dependency_resolver.py` (new) exposes
  `resolve_closure(selection: list[dict]) -> list[dict]` — `selection` is
  `[{"kind": str, "id": str}, ...]` (same shape `T01`'s `GET /artifacts`
  entries use, minus `name`/`description`). Returns one entry per
  resolved artifact: `{"kind": str, "id": str, "included_reason":
  "selected" | "dependency", "depends_via": str | None}` — `depends_via`
  names the parent artifact + relationship for a dependency-only entry
  (e.g. `"skill:create-companies-partners (shared file:
  vault_manager.py)"`, `"agent:compass-pricing-expert (depends_on)"`,
  `"skill:create-companies-partners (implicit Template coupling)"`,
  `"pipeline:meeting-capture (step agent)"`), `None` for a directly-
  selected artifact. Every original selection entry is always present
  with `included_reason: "selected"`, even if also reachable as a
  dependency of another selected artifact (never duplicated — one entry
  per unique `(kind, id)`, `"selected"` wins over `"dependency"` if both
  apply).
- Traversal rules (per `ADR-013`):
  - **Skill → shared-file copies:** disclosure only (the bytes already
    travel with the Skill's own payload) — no separate artifact is added
    to the closure for this; `T04`'s own archive writer includes the
    Skill's real `scripts/` content regardless. This resolver's own job
    here is limited to what's genuinely a SEPARATE artifact addition
    (Template/Agent/Pipeline below), not re-listing the Skill's own files
    as pseudo-artifacts.
  - **Agent → Registry `skill_ids`/`depends_on`:** for a selected/
    resolved Agent, every id in both real fields is added as
    `kind: "agent"` (from `depends_on`) or `kind: "skill"` (from
    `skill_ids`), recursed transitively (a dependency's own dependencies
    are resolved too, cycle-safe — track visited `(kind, id)` pairs).
  - **Skill → implicit Template.json coupling:** a static text scan of
    the Skill's own `SKILL.md` + every real script's content (via
    `list_scripts`) for any real `TemplateManager().get_all()` id
    appearing as a literal substring; each match adds that Template as a
    dependency (`depends_via` names the literal match).
  - **Pipeline → step Agents:** every real Agent id named in
    `pipeline.steps[].id` is added as `kind: "agent"` and recursed exactly
    like a directly-selected Agent (its own `skill_ids`/`depends_on` chain
    included too).
  - An id that doesn't resolve against its own kind's Manager (a stale/
    unknown reference) is skipped silently from the closure additions —
    never raises, never adds a fabricated placeholder entry — but the
    original selected entry is never dropped just because ONE of its
    dependencies failed to resolve.

---

## Files to Modify

- `src/backend/app/business/logic/artifact_dependency_resolver.py` (new file).

---

## Constraints

- Inherits from parent story.
- **Pure composition over the 4 already-`Done` Managers** — no owned
  store, no file write of any kind (this module never writes anything;
  `T04` does).
- **The Skill→Template heuristic is a disclosed, acceptable v1
  limitation** (`ADR-013`'s own Consequences: false negatives possible
  for a non-literal Template reference) — do not attempt a more
  sophisticated detector than the plain literal-substring scan; a missed
  Template degrades to "the operator manually adds it via `US-01`'s own
  multi-select," never silent data loss.
- Never import `app.hermes` directly — reach Hermes-backed data only
  through `SkillManager`/`AgentManager` (which already go through
  `get_client()`).
- Cycle-safe: an `Agent A depends_on Agent B depends_on Agent A` real
  loop (however unlikely) must terminate, not infinite-recurse.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-85-US-02-AC-01]` Call `resolve_closure([{"kind": "pipeline",
   "id": "<a real Pipeline id whose steps name at least one real
   Agent>"}])` (or the closest available real equivalent); confirm the
   returned closure includes the Pipeline itself
   (`included_reason: "selected"`) plus every real step Agent
   (`included_reason: "dependency"`, `depends_via` naming the pipeline),
   and that each of those Agents' own real `skill_ids`/`depends_on` are
   further recursed into the closure.
2. `[REQ-SB-85-US-02-AC-01]` Call `resolve_closure([{"kind": "skill",
   "id": "create-companies-partners"}])` (the PRD's own named real
   example); confirm the real `customer`/`partner` Template ids appear in
   the closure as `kind: "template"`, `included_reason: "dependency"`,
   `depends_via` naming the literal Skill→Template text-scan match —
   confirming the PRD's own real example genuinely pulls in its own
   Templates, per `ADR-013`'s own Consequences.
3. Call `resolve_closure` with a selection whose Agent's own
   `depends_on` chain forms a real cycle (construct one via 2 disposable
   test Agents if no real cycle exists, `AgentManager().create(...)`,
   cleaned up after); confirm the call terminates and each Agent appears
   exactly once in the closure (no AC tag — supports the cycle-safety
   Constraint, no Gherkin scenario names this directly).
4. Call `resolve_closure` with an id that doesn't exist under its own
   kind's Manager; confirm the closure still contains every OTHER
   resolvable entry, with no raised exception and no fabricated
   placeholder for the unresolved one (no AC tag — supports the
   "skipped silently, never drops the rest" Constraint).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `resolve_closure` recurses Agent `skill_ids`/`depends_on`
      transitively, cycle-safe
- [x] `resolve_closure` detects a Skill's own implicit Template coupling
      via literal text scan, confirmed live against `create-companies-partners`
- [x] `resolve_closure` recurses Pipeline step Agents the same way as a
      direct Agent selection
- [x] Every entry carries a human-readable `included_reason`/`depends_via`
- [x] An unresolvable dependency id is skipped, never crashes the whole call
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Writing anything to disk / the archive — `T04`.
- The secret scan — `T03`.
- Rendering the resolved closure to the operator — `T05` (frontend).

---

## Context / Notes

`ADR-013` (`Implementation/Architecture/ADR.md`), architecture
`§Dependency Closure, Secret Scan & .sbf Archive Format`, are the
authoritative design for this task — read both in full before starting.

---

## Implementation Log

**Built:** `src/backend/app/business/logic/artifact_dependency_resolver.py`
(new file) — `resolve_closure(selection)` composes `SkillManager`/
`TemplateManager`/`AgentManager`/`PipelineManager` plus
`data_access.skills.read_skill_md`/`list_scripts` (named directly in this
task's own Starting State/Inputs). Single recursive `visit(kind, id,
reason, depends_via)` closure, cycle-guarded via a `visited: set[(kind,
id)]`, upserting into a `results: dict[(kind, id), entry]` where a later
`"selected"` visit always upgrades an already-resolved `"dependency"`
entry in place (never duplicated, `"selected"` wins regardless of visit
order). Every candidate id — selected or discovered as a dependency — is
uniformly validated against its own kind's Manager before being added;
an unresolvable one is skipped silently, entirely, at every level (no
partial/placeholder entry either way).

**Real, live-confirmed data-shape finding (in-scope fix, this file
only):** `Agent.skill_ids` (`AgentManager._to_agent`) is populated from
Hermes' own raw `"<category>/<slug>"` skill ids (confirmed live against
every one of the 40 real Agents in this deployment — e.g.
`compass-expert.skill_ids == ['knowledge-base/compass-kb-writer']`), not
the bare slug `SkillManager`/`data_access.skills` key everything by
(confirmed live: `SkillManager().get_by_id('knowledge-base/compass-kb-writer')`
is `None`; `SkillManager().get_by_id('compass-kb-writer')` resolves).
Without normalizing, the Agent→Skill dependency edge would silently
resolve to nothing for every real Agent that has any Skill at all. Fixed
by taking the id's own last `/`-segment before the Skill lookup — the
exact same "HermesSkill.id is category/slug; ours is the plain slug"
convention `SkillManager.sync_from_hermes()` already establishes
elsewhere in this codebase, not a new one invented here. Logged as a
scope-internal judgement call (an in-file interpretation of real data,
not a deviation from any locked AC's own wording) for human spot-check.

**Scope-internal judgement call:** the Objective section's own
illustrative `depends_via` example list includes a "shared file:
vault_manager.py" string, but the more detailed Traversal Rules bullet
right below it is explicit that a Skill's own shared-file copies are
"disclosure only... no separate artifact is added to the closure for
this" (T04's archive writer includes that content regardless). Followed
the more specific Traversal Rules text — no shared-file entries are
added by this resolver. Logged for human spot-check, non-blocking (every
locked AC's own externally-observable wording is satisfied either way).

**Real, live-confirmed environment finding (not a defect, informs
verification method below):** none of the 3 real Pipelines in this
deployment (`company-discovery`, `meeting-builder`, `threads-builder`)
have `steps[].id` values that are real Agent ids — every real Pipeline's
own steps are pipeline-internal data-capture stage identifiers (e.g.
`scan-threads`, `fetch-emails`) with their own separate `depends_on` used
purely for step-ordering, not Agent references. Likewise, no real Agent
in this deployment currently has a non-empty `depends_on` (all 40 are
`[]`) — the compass-pricing-expert/compass-expert "specialist" relay the
story's own Context describes is accomplished via hand-written SOUL.md
text, not the structured `depends_on` field. `AC-01` Test 1's own prose
explicitly anticipates this ("or the closest available real equivalent")
— verified via an in-process monkeypatch of the real, already-loaded
`_pipeline_manager`/`_agent_manager` module-level instances (matching
this project's own established Learnings pattern, `SPRINT-018`), driving
the real, unmodified `resolve_closure` against real `Pipeline`/`Agent`
dataclass instances substituted only at the one Manager lookup point,
reverted immediately after. Zero permanent state changes; zero disposable
real Hermes profiles created.

**Verification (manual mode, all against the real, live-configured
vault/Hermes install — `VAULT_PATH=C:\myWorx\Moussa MD\Moussa Brain`):**

- `[REQ-SB-85-US-02-AC-01]` (Test 1, Pipeline recursion) — PASS. Real
  `Pipeline`/`PipelineStep` dataclass substituted in-process for one call
  (id `test-pipeline-with-real-agent-steps`, steps naming the 2 real
  Agent ids `compass-expert`/`azure-calculator`); reverted immediately
  after. Observed: the Pipeline itself present
  (`included_reason: "selected"`); both real step Agents present
  (`"dependency"`, `depends_via: "pipeline:test-pipeline-with-real-agent-steps
  (step agent)"`); each Agent's own real `skill_ids` recursed further —
  `compass-expert` → real Skill `compass-kb-writer` → its own real
  Template coupling (7 real Templates, `customer` included); `azure-calculator`
  → real Skill `azure-cost-calculator` (no further Template match). No
  fabricated data — every id in the output resolved against its real
  Manager.
- `[REQ-SB-85-US-02-AC-01]` (Test 2, Skill→Template coupling) — PASS.
  `resolve_closure([{"kind": "skill", "id": "create-companies-partners"}])`
  against the real Skill. Observed: `create-companies-partners` present
  (`"selected"`); real Templates `customer` and `partner` both present
  (`"dependency"`, `depends_via: "skill:create-companies-partners (implicit
  Template coupling)"`) — confirming the PRD's own named real example
  genuinely pulls in its own Templates. (Also observed, honestly: the
  plain literal-substring scan additionally matched `file`/`meeting`/
  `meeting-series`/`note`/`opportunity` — short, common-word Template ids
  that also appear as ordinary text in the script's own content; this is
  the disclosed heuristic behaving exactly as ADR-013 designed it — "do
  not attempt a more sophisticated detector than the plain
  literal-substring scan" — not a defect, and the AC only requires
  `customer`/`partner` to be present, which they are.)
- Cycle-safety (no AC tag, supports the Constraint) — PASS. Two
  in-process, real-shaped `Agent` dataclass instances substituted for one
  call (`cycle-agent-a.depends_on == ["cycle-agent-b"]`,
  `cycle-agent-b.depends_on == ["cycle-agent-a"]`), reverted immediately
  after. Observed: call terminated, returned exactly 2 entries, each
  Agent present exactly once.
- Unresolvable id (no AC tag, supports the Constraint) — PASS.
  `resolve_closure([{"kind": "agent", "id": "definitely-does-not-exist-xyz"},
  {"kind": "skill", "id": "create-companies-partners"}])` against the
  real, unmodified Managers. Observed: no exception raised; no entry (not
  even a placeholder) for the unresolvable agent id; every entry for the
  other, resolvable selection (the Skill plus its 7 real Template
  dependencies) present and correct.
- Additional sanity check (not one of the 4 named steps, directly
  supports the Objective's own "selected wins, never duplicated" wording)
  — PASS. `resolve_closure` called with BOTH `compass-expert` (agent) and
  `compass-kb-writer` (skill, also reachable as compass-expert's own
  dependency) selected together. Observed: exactly one `compass-kb-writer`
  entry, `included_reason: "selected"`, `depends_via: null` — no
  duplicate.

gate: clear 2026-08-31 — no MUST-FLAG trigger fired at this task's own
step (no new ADR/assumption/contradictory input/unresolved AC; the two
disclosed items above are scope-internal judgement calls made while
composing strictly within this file's own `## Files to Modify`, not
escalation triggers). The story's own `gate: flagged` (trigger-3,
`ADR-013`/`ADR-014` pending human review) is unaffected — this task does
not clear that flag, it stays parked in `REVIEW-QUEUE.md` for the human.
