# Multi-Agent Delivery Pipeline

## Purpose

A six-role autonomous pipeline — **designer (precursor) → analyst → architect →
decomposer → product-owner → coder** — that collaborates exclusively via files on
disk. The filesystem is the bus; agents never talk to each other directly. Slash
commands drive it (seven forward-pipeline + two for bug tracking):

| Command | Agent(s) | Output | Batches |
|---|---|---|---|
| `/design` | designer | requirement(s) → approved prototype screens (precursor) | requirement batch |
| `/spec` | analyst | requirement → `Draft` story (untagged Gherkin) | many requirements |
| `/plan-tasks` | architect → decomposer | story → architecture + locked ACs + tasks | many stories |
| `/plan-sprints` | product-owner | ungrouped Ready stories → sprint partition | all ungrouped |
| `/implement-sprint` | coder | sprint → built, verified code | many sprints |
| `/prep` | analyst → architect → decomposer → product-owner | requirement → Ready sprint | everything eligible |
| `/flow` | all of the above | requirement → code, end-to-end | everything eligible |
| `/bug` | — (interactive, no agent) | manual-test finding → `Open` bug in `BUGS.md` | one bug per run |
| `/triage` | analyst | a batch of `Open` bugs → `Draft BUGFIX-NN` story | a chosen bug-batch |

The two bug-tracking commands are documented in full under **"Bug tracking"** below;
they run alongside the forward pipeline (not inside `/flow`).

Forward steps run **autonomously by default**. The pipeline pauses for a human
**only by exception** — when an agent hits the MUST-FLAG list. Backward steps and
out-of-scope events always escalate.

This file is the **canonical human-and-reference copy** of the pipeline contract.
The agent prompts under `.claude/agents/` each restate inline the subset of rules
that bound them, so they remain correctly bounded even in a fresh context window
where this file is never opened. Nothing here overrides `CLAUDE.md`.

---

## Roles

| Role | Stage | Reads | Writes | Must NOT |
|---|---|---|---|---|
| designer | `/design` | PRD (scoped), prototype, design system, data-model ADRs | Prototype screens, REVIEW-QUEUE, CHANGELOG | src/ code; stories; tasks; sprints; architecture |
| analyst | `/spec` | PRD, BACKLOG, existing stories, MEMORY, architecture (context) | Story files, BACKLOG rows; REVIEW-QUEUE + ESCALATIONS (on trigger) | AC-IDs; architecture; tasks; CHANGELOG; MEMORY; Learnings |
| architect | `/plan-tasks` step 1 | PRD, target story, architecture.md, ADR.md, MEMORY | architecture.md, ADR.md, story `## Notes`; REVIEW-QUEUE + ESCALATIONS (on ADR or contradiction) | Story ACs; tasks; code; Learnings |
| decomposer | `/plan-tasks` step 2 | Target story, architecture (read-only), MEMORY, **Learnings** | Task files (flat root), story ACs + locked IDs, story status; REVIEW-QUEUE + ESCALATIONS (on trigger) | Sprints; code; architecture; Learnings |
| product-owner | `/plan-sprints` | Ready ungrouped stories, task deps, BACKLOG, MEMORY, **Learnings** | Sprint files, story `sprint:`, BACKLOG Sprint columns; REVIEW-QUEUE + ESCALATIONS (on flag) | Tasks; ACs; code; In Progress / Done sprints; Learnings |
| coder | `/implement-sprint` | One task file, parent story, architecture scope, MEMORY, **Learnings** | src/ files (task-scoped), CHANGELOG, MEMORY (if warranted), task log, story/sprint/BACKLOG status; REVIEW-QUEUE + ESCALATIONS (on block or escalation) | Files outside `## Files to Modify` (except DoD updates); Done tasks; **Learnings** (human-only) |

---

## ID Scheme

| Kind | Format | Assigned by |
|---|---|---|
| Story | `REQ-X.Y-US-NN` | analyst (anchored on primary PRD requirement) |
| Acceptance criterion | `REQ-X.Y-US-NN-AC-NN` | decomposer |
| Task | `REQ-X.Y-US-NN-T<NN>` | decomposer |
| Sprint | `SPRINT-NNN` | product-owner (sequential, never reused) |
| Bug | `BUG-NNN` | `/bug` (interactive capture; sequential, never reused) |
| Bugfix story | `BUGFIX-NN-US-01` | analyst (at `/triage`; sequential `NN`) |

A story may satisfy multiple requirements — `requirement_ids:` is a list; the story
is *anchored* to one primary requirement for its ID. `BACKLOG.md` links it from every
requirement row it covers.

---

## Status vs. Gate — Two Distinct Concepts

- **`status:`** = artefact lifecycle: `Draft | Ready | In Progress | Blocked | Done`
- **`gate:`** = whether a human must look before the pipeline proceeds: `clear | flagged`
  plus `gate_reason:` naming the trigger.

A command does its status transition **and** sets the gate. `gate: clear` means the
next stage may proceed untouched. `gate: flagged` means the item halts and is written
to `REVIEW-QUEUE.md`.

Status is the **single source of truth.** Claude Code custom commands take
**positional arguments only — no `--flags`**, so behaviour keys off `status:`, not
options. Commands act on `status:` and skip anything already past their stage. To redo
a stage, reset the artefact's `status:` and re-run.

---

## The MUST-FLAG List (the safety spine)

An agent sets `gate: flagged` if **any** of these fired while producing the artefact.
If **none** fired, it sets `gate: clear` and leaves an audit breadcrumb.

1. **Material assumption** made to fill a gap ("I assumed X").
2. The underlying requirement is still **`<!-- Draft -->`/unfinalised** in the PRD.
   (A product-constraint / non-specable item is *never* eligible — do not spec it at
   all; skip it entirely.)
3. It **created or changed an ADR** (architectural decisions always get a human look).
4. It wrote an **`ESCALATIONS.md`** entry.
5. **Oversized** story or sprint; a **`Blocked`** story; or a **cross-sprint
   dependency** had to be introduced.
6. A locked **AC could not be verified** (coder only).
7. **Contradictory inputs**, or any escalation trigger (new dependency, shared-
   interface change, ADR deviation, unanticipated file).
8. **Multiple equally-valid options** or the work is genuinely **unclear** — flag
   rather than guess.

**This list is self-regulating.** Early foundational work trips triggers 1–3
constantly (new ADRs, `Draft` requirements, first-time assumptions), so it stays
heavily gated exactly when oversight matters most; as the codebase matures and
patterns settle, fewer triggers fire and more work flows untouched.

---

## Audit Breadcrumb on Auto-advance

Even when skipping the gate, an agent records a one-line breadcrumb in the artefact's
`## Notes` or `## Implementation Log`:

```

gate: clear YYYY-MM-DD — no triggers fired (ADRs unchanged, no assumptions, requirement finalised)

```

"Reduce attention" must never become "zero visibility."

---

## Console Summary (mandatory)

Every agent's closing console output **explicitly lists**:
- What it wrote to `ESCALATIONS.md` and `REVIEW-QUEUE.md` (IDs + trigger)
- Which items it auto-advanced (`gate: clear`)

The human sees the inbox at review time without hunting through files.

---

## Two Human Surfaces

**`REVIEW-QUEUE.md`** — the transient human inbox. Items here are awaiting a human
decision before the pipeline can proceed. Clean when resolved.

**`ESCALATIONS.md`** — the permanent append-only log. Every backward step (re-spec,
re-architect, re-plan) and out-of-scope event is recorded here. Resolved entries
name a concrete resolving artefact (story ID, ADR number, commit hash) and are never
edited.

Escalation categories: `unclear-requirement | out-of-scope | new-dependency |
shared-interface-change | adr-deviation | unanticipated-file | oversized-story |
other`

---

## Hard Rules

1. **Specs are append-only.** A requirement change is a NEW story; completed tasks
   and done stories are frozen.
2. **Story IDs are the join key** across stories, architecture, tasks, sprints,
   and verification.
3. **Locked ACs.** The analyst writes untagged Gherkin. The **decomposer**
   authors/tightens the final wording, assigns each a `REQ-X.Y-US-NN-AC-NN` ID, and
   locks it by default; it may exceptionally mark one non-locked via
   `<!-- AC-ID: <id> | locked: false -->` with the reason in the story's `## Notes`.
   The coder may not weaken, omit, or delete a locked AC.
4. **AC → verification mapping is mandatory.** Every locked AC must have a matching
   ID-tagged verification step. A locked AC with no tagged step is a hard failure.
5. **Coder is scope-bounded.** ONE task at a time, within `## Files to Modify` and
   the architecture sections named in its Context. Any out-of-scope event → immediate
   escalation, no improvisation. Scope-internal judgement calls go in the
   `## Implementation Log` as assumptions.
6. **Forward is autonomous by exception; backward always escalates.**
7. **Product-owner honours the dependency graph.** It may not contradict the
   decomposer's `depends_on` task edges; dependency-linked stories go in the same
   sprint **or** in ordered sprints with a recorded `depends_on_sprints` edge.
8. **Sprints never mix phases.** *Exception — bugfix sprints.* A sprint composed of
   `BUGFIX-NN` stories is exempt from phase homogeneity: bug remediation is *current*
   work, not roadmap-phased, so a bugfix sprint may span the phases of the features
   its bugs affect (`BUGFIX-NN` stories carry no `phase:`).
9. **`/implement-sprint` routes around blocked work** and refuses to start a sprint
   whose `depends_on_sprints` are not all `Done`.
10. **Gates are exception-based.** No mandatory per-stage review.

---

## Batching and Resumability

All commands are batch-capable. Run bare to act on all eligible artefacts, or pass
explicit IDs. A batch advances clean items and parks flagged ones — it never blocks
clean items behind flagged ones.

All commands are **resumable.** Re-run after clearing flags and the command picks up
from the current `status:` of each artefact.

---

## Human Gates (exception-based)

There is no mandatory gate after every stage. A human is pulled in **only** when an
artefact is `gate: flagged`. The human's worklist is `REVIEW-QUEUE.md`. Three
touchpoints remain lightly human regardless of automation level:

- **Design sign-off (`/design`)** — the designer is a design-first precursor that
  **always** flags; the human reviews the prototype screen(s) in a browser and
  approves before `/spec` runs on those requirements. This is up front, not mid-flow,
  so the autonomous pipeline stays uninterrupted.
- **Promotion of a flagged item** — the human resolves the flag (edits, or resets
  `status:` to redo), then the pipeline resumes.
- **The sprint retro** — the coder auto-marks a sprint `Done` when every locked AC is
  verified and nothing is blocked, and **drafts** the `## Retrospective`; the human
  skims it and propagates patterns/antipatterns into `Implementation/Learnings.md`.
  Harvesting learnings is reflective judgement, not automated.

---

## Coder Verification Mode (manual → automated upgrade)

The coder is **active** — there is no inactive state. Verification runs in **manual
mode** by default: for each locked AC the coder performs the manual step the
decomposer authored in the task's `## Tests` block and records the observed outcome
(pass/fail, with what was seen) in the task's `## Implementation Log`, keyed by AC-ID.
A locked AC it cannot verify blocks the task.

This is a **manual → automated upgrade path.** Once the project is scaffolded and the
test-stack ADRs are Accepted, the decomposer and coder emit AC-tagged **automated**
tests with real runner commands in place of AC-tagged manual steps. No agent file
needs an "activate" edit — manual mode is the live default until real test files can
actually run.

---

## Bug tracking

Bugs found through manual testing — UI issues and logic issues alike — are captured,
batched into a fix, and tracked to closure through the same file-on-disk machinery.
A bug against already-`Done` work is **new forward work** (a new story), never a
reopening of the completed story (hard rule 1). The mechanism adds **two commands and
zero new agents**; `/triage` reuses the analyst.

### Surfaces

- **`BUGS.md`** (repo root) — the **source of truth**: an append-only ledger with an
  index table (`ID | Title | Area | Severity | Status | Found | Fixed by`) plus a
  `## Bug Details` section holding screen/route, repro steps, expected vs actual, and
  screenshot paths. IDs are `BUG-NNN`, sequential and never reused.
- **`BACKLOG.md` → `## Bugs`** — a **thin status mirror** of the ledger
  (`ID | Title | Area | Status | Fixed by`), exactly as `BACKLOG.md` already mirrors
  story/sprint status. Detail lives only in `BUGS.md`.

### Fields and status

- **Area:** `UI | Logic`. **Severity:** `Blocker | Major | Minor | Cosmetic`.
- **Status** (3 live + 1 terminal): **Open** (logged, no fix story) → **In Sprint**
  (a `BUGFIX-NN` story covers it, set at `/triage`) → **Closed** (covering story
  `Done`); **Won't Fix** (closed with a reason; never auto-set).

### Lifecycle — who writes what (same actor writes both surfaces, in one touch)

There is **no separate sync step**. Whoever owns a status transition updates `BUGS.md`
**and** the `BACKLOG.md` mirror together — the rule already used for `BACKLOG.md`.

| Stage | Command / actor | Transition |
|---|---|---|
| **Capture** | `/bug` (interactive, no agent) | adds the bug → `Open` |
| **Triage** | `/triage` → **analyst** | batches selected bugs into one `Draft BUGFIX-NN-US-01` story (one Gherkin scenario per bug); flips rows → `In Sprint`; writes `Fixed by` links |
| **Fix shipped** | `/implement-sprint` → **coder** | when the `BUGFIX-NN` story is `Done`, flips its bugs → `Closed` |
| **Won't Fix** | human (or `/triage`) | sets `Won't Fix` + reason |

### /bug

`/bug` — **interactive capture, run on the main thread (NOT a subagent — it must ask
you questions in real time).** It reads `BUGS.md`, computes the next `BUG-NNN`, and
**asks clarifying questions** for anything missing or ambiguous (title, Area, Severity,
screen/route, repro steps, expected, actual) so the eventual fix can be correct. It
then appends the index row **and** the `## Bug Details` subsection at `Open`, and adds
the mirror row to `BACKLOG.md`'s `## Bugs` section. Not a `/flow` stage.

### /triage

`/triage [BUG-NNN …]` — the analyst in **triage mode**. Bare = it lists all `Open`
bugs and asks you to pick the batch. It mints one `Draft BUGFIX-NN-US-01` story (one
scenario per bug), flips the chosen bugs to `In Sprint` with `Fixed by` links across
both surfaces, and sets the story's `gate:` as usual. **Standalone:** `/triage` does
not run inside `/flow`; it produces a `Draft` story that the normal `/plan-tasks →
/plan-sprints → /implement-sprint` stages then advance unchanged (they key off
`status:`, not off how the story was born). The decomposer locks one AC per
bug-scenario (its regression criterion), so a bug cannot reach `Closed` until "the
repro no longer reproduces" has a passing test. The product-owner groups `Ready`
`BUGFIX-NN` stories into sprints like any other story (subject to hard rule 8's bugfix
exception). Neither the decomposer nor the product-owner needs bug-specific logic.

### Review queue & escalations (reused, not reinvented)

The bug flow does **not** add new gate, review-queue, or escalation machinery — it
plugs into the existing surfaces the moment it produces a story:

- **`/triage`** runs in the analyst's normal gate machinery: it sets
  `gate: clear | flagged`, writes flagged work (ambiguous/contradictory bug, or a
  "this is a requirement change, not a bug" judgement) to `REVIEW-QUEUE.md`, and
  appends backward/out-of-scope events to `ESCALATIONS.md` — same entry formats as any
  `/spec` run, and it reports both in its closing summary.
- **`/plan-tasks → /plan-sprints → /implement-sprint`** gate and escalate the
  `BUGFIX-NN` story exactly as for any story (e.g. the coder blocks + flags a bug whose
  regression AC it cannot verify, per trigger 6).
- **`/bug`** is the only step outside the gates — it is pure intake that removes
  ambiguity by *asking the user questions*, so it records an `Open` bug without
  flagging. Gating begins at `/triage`, the first point a decision is made.

---

## Relationship to Existing Files

- **Three-way knowledge split:** `MEMORY.md` = atomic hard rules; `Learnings.md` =
  sprint heuristics (human-harvested from retros only); `ADR.md` = architectural
  choices involving tools, frameworks, or structural boundaries.
- **Per-task Definition of Done:** the coder updates `MEMORY.md` (when a new
  decision/pattern/constraint emerged) and `CHANGELOG.md` (always) as part of marking
  a task `Done`.
- **`BACKLOG.md`** is a PRD-coverage index, **not** a build queue. The coder moves
  requirement rows to `Done` as stories complete; the pipeline reads `status:` from
  task/story files, not BACKLOG.
- **Foldering retired.** Task files live in the **flat root** `Implementation/Tasks/`.
  Sprint membership is read from the story's `sprint:` + the task's `parent_story:`
  frontmatter — never from a folder. Never create `Tasks/SPRINT-NNN/` subfolders.
- **Sprints** are authored by the **product-owner** at `/plan-sprints`; the human
  still gates flagged partitions and harvests the retro.

---

## Host Environment

- Host: `Windows 11 / PowerShell 7+`.
- Agents use **forward slashes** inside artefacts (task `## Files to Modify`, story
  references, etc.).
- Agents never assume POSIX utilities (`grep`, `find`, `cat`, etc.) — use the
  Grep/Glob/Read/Edit tools.
- Destructive shell commands (`Remove-Item -Recurse -Force`, `rm -rf`) are denied.
- `.claude/settings.json` pairs every shell-invoking permission across both `Bash(...)`
  and `PowerShell(...)` entries (Windows requirement).
