# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project

**Second Brain** — A personal knowledge base service that indexes and serves the
user's Obsidian vault directly (no staging/promotion gate — it's trusted personal
data, not agent-written scratch data), integrating with Hermes (an MCP-based
multi-channel communication tool) as a planned integration point.

Standalone project for now. Eventual integration with `agentic-map`'s agents (so
they can query this KB instead of, or alongside, their current Postgres/Qdrant KB)
is a deliberately separate, later decision — not scoped here.

The core loop: point Second Brain at an Obsidian vault directory → it parses and
indexes the markdown notes (frontmatter, wikilinks, tags) → the user (and later,
Hermes-connected channels) can browse, search, and query the notes directly, with
no promotion/approval step between "written" and "usable" — the vault is already
trusted.

## General Rules

- Ask clarifying questions before starting complex tasks.
- Don't make assumptions about requirements — if vague, ask and then update the
  requirements file.
- Create separate commits per logical change, not one giant commit.
- When unsure between two approaches, explain both and let the user choose.
- Add inline comments only when the WHY is non-obvious: a hidden constraint, a
  subtle invariant, a workaround for a specific bug. Never explain WHAT the code
  does — well-named identifiers do that.
- Use elaborate variable and function names so the code is self-documenting.
- **Update `MEMORY.md`** (repo root) when a task produces a new decision, pattern,
  or constraint that future tasks should know about — do NOT add empty or trivial
  entries.
- **Never rely on chat history.** All context must come from files in this project.
- **Read before writing.** Always read existing files before modifying them.
- Update `CHANGELOG.md` (repo root) with entries for everything created.
- **Minimal changes.** Only change what the task requires. Leave everything else
  untouched. No opportunistic refactoring, no features not in the task.
- When creating a new sprint, use the template in
  `Implementation/Sprints/sprint-template.md`.
- When creating a new task, use the template in
  `Implementation/Tasks/task-template.md`.
- When creating a new user story, use the template in
  `Implementation/UserStories/user-story-template.md`.
- **Host is Windows 11 / PowerShell 7+.** Always pair permission entries in
  `.claude/settings.json` across both `Bash(...)` and `PowerShell(...)`. Do not
  assume POSIX utilities (`grep`, `find`, `cat`, `head`, `tail`, `sed`, `awk`) — use
  the dedicated Grep/Glob/Read/Edit tools instead.
- **Before invoking any agent or running `/spec`, `/plan-tasks`, `/plan-sprints`,
  `/implement-sprint`, or `/flow`, read `Implementation/Pipeline.md`** — it is the
  authoritative pipeline contract.

## Commit Rules

- Create **separate commits per logical change** — never one giant commit.
- Prefer creating a **new commit** over amending an existing one. When a pre-commit
  hook fails, the commit did NOT happen — never use `--amend` in that case; fix the
  issue, re-stage, and create a new commit.
- **Never skip hooks** (`--no-verify`) unless explicitly asked.
- **Never force-push to main/master.** Warn the user if they request it.
- **Never stage sensitive files** (`.env`, credentials). Warn if asked to commit them.

## Memory Protocol

**Framework memory vs instance memory — decide this FIRST, before writing
anything down.**

| Memory | Where | Scope |
|---|---|---|
| **Framework** | repo `MEMORY.md` | true on every install; ships with the product |
| **Instance** | `<SECOND_BRAIN_DATA_PATH>/AGENT-MEMORY.md` | one machine's paths, vault, mailbox, model, keys, live state |
| **Another operator's instance** | their machine | never read or written from here |

**The test:** would this still be true on a fresh install with a different vault
and mailbox? **Yes → framework `MEMORY.md`. No → that machine's
`AGENT-MEMORY.md`.**

- "The backend serves port 8001" → framework.
- "The vault is at `C:\The-Vault\CBO-Vault`" → instance.
- **Fix something in the framework → record it in framework memory**, in the same
  change as the fix.

Never put a real vault path, mailbox, key or machine name in a repo file. Use
`<OPERATOR_VAULT>` / `<operator>` placeholders — mixing instance detail into
shared docs is what caused one install to act on another install's assumptions
(2026-09-04).

### Within framework `MEMORY.md`

- **Decisions** → `MEMORY.md` under `## Decisions` — format: `[date] Decision – Reason`
- **Patterns** → `MEMORY.md` under `## Patterns` — format: `Pattern name – description`
- **Constraints** → `MEMORY.md` under `## Constraints` — format: `Constraint – reason`
- Do NOT store logs, chat transcripts, or debugging output in `MEMORY.md`

**Three-way knowledge split — file new knowledge in the right place:**

- `MEMORY.md` → atomic hard rules ("X is forbidden / must always happen")
- `Implementation/Learnings.md` → sprint-level heuristics ("when X, prefer Y")
  — harvested from retros only
- `Implementation/Architecture/ADR.md` → architectural choices involving tools,
  frameworks, or structural boundaries

---

## Status

**Stack in one line:** Python + FastAPI backend (Obsidian vault indexing, no
staging/promotion gate) + TypeScript/React/Vite frontend, MCP-integrated
communication via Hermes.

**Architecture decisions:** `Implementation/Architecture/ADR.md` is the authoritative
source. Always read it alongside `Implementation/Architecture/architecture.md`
before writing application code.

**Current delivery state:** Check `REVIEW-QUEUE.md` for open review items,
`BACKLOG.md` for unstarted requirements, and `Implementation/Sprints/` for sprint
status.

**Key artefacts:**

- **`src/`** — the single root for all application code.
  `src/backend` (Python + FastAPI — vault parsing/indexing, KB API, Hermes MCP
  integration), `src/frontend` (TypeScript + React + Vite — notes browser/search
  UI).
- **`Documentation/Framework/`** — **How to Use the Framework.** The shared
  reference for the operator and for you: same document, no separate versions.
  Start at `README.md` (concepts and task recipes), then `Templates.md` before
  adding a new note type (a new note type is a new `Template.json`, never new
  code), `Artifacts.md` for Agent/Skill/Pipeline shapes and the
  `.sbf`/`.sbb`/`.sbd` formats, and `Hermes-Provisioning.md` for what depends on
  the folder held outside the working tree.
- **`Documentation/PRD.md`** — full product requirements document. Read
  before implementing any feature.
- **`html-prototype/`** — clickable HTML/CSS/JS prototype. No build step; open
  `html-prototype/index.html` directly in a browser. This is the **design
  authority** for any screen it covers — reconcile stories against it before
  speccing.
- **`MEMORY.md`** (repo root) — append-only log of Decisions / Patterns / Constraints.
- **`CHANGELOG.md`** (repo root) — append an entry for everything created.
- **`BACKLOG.md`** (repo root) — index of all PRD requirements with links to the
  stories that implement each. Also carries a `## Bugs` thin-mirror section of
  `BUGS.md` (id · title · area · status · fixed-by).
- **`BUGS.md`** (repo root) — append-only bug ledger and **source of truth** for
  bugs found through manual testing (UI + logic). Captured via `/bug`, batched into
  a `BUGFIX-NN-US-01` fix story via `/triage`.
- **`REVIEW-QUEUE.md`** (repo root) — live human inbox for flagged items.
- **`ESCALATIONS.md`** (repo root) — append-only log of backward pipeline steps and
  out-of-scope events. Resolved entries name a concrete resolving artefact (story ID,
  ADR number, or commit hash) and are never edited.
- **`Implementation/`** — all implementation-tracking artefacts.
- **`Implementation/Pipeline.md`** — authoritative multi-agent pipeline definition.
  Read before driving any agent or slash command.
- **`Implementation/UserStories/`** — user story files.
  Template: `Implementation/UserStories/user-story-template.md`.
- **`Implementation/Tasks/`** — per-task implementation files (flat root — no
  subfolders). Template: `Implementation/Tasks/task-template.md`.
- **`Implementation/Sprints/`** — sprint definitions.
  Template: `Implementation/Sprints/sprint-template.md`.
- **`Implementation/Architecture/`** — `architecture.md` (living system description)
  and `ADR.md` (append-only Architecture Decision Records).
- **`Implementation/Learnings.md`** — append-only cross-sprint index of patterns and
  antipatterns harvested from sprint retrospectives. Read before starting a new sprint;
  update at the end of every sprint's retro (human-only — the coder drafts the retro,
  the human propagates the learnings).
- **`Implementation/Plans/`** — longer-form implementation plans from planning
  sessions. Free-form by design — no template; plans vary too much in shape to
  standardise.
- **`README.md`** (repo root) — short public-facing overview of the project.
- **`.claudeignore`** — excludes build/dependency dirs, logs, and other noise from
  Claude's context.
- **`.claude/agents/`** — self-contained agent prompts (`designer.md`, `analyst.md`,
  `architect.md`, `decomposer.md`, `product-owner.md`, `coder.md`). Each file
  restates the hard rules that bound its role — including the MUST-FLAG list — so
  it remains correctly bounded in a fresh context where `Pipeline.md` is never
  opened. (`designer.md` is the design-first precursor: always flags for human
  browser sign-off; NOT a `/flow` stage.)
- **`.claude/commands/`** — slash-command definitions (`design.md`, `spec.md`,
  `plan-tasks.md`, `plan-sprints.md`, `implement-sprint.md`, `prep.md`, `flow.md`),
  the bug-tracking commands (`bug.md`, `triage.md`), plus the `load-context.md`
  cold-start context loader (a utility, not a pipeline stage). (`/prep` runs `/spec
  → /plan-tasks → /plan-sprints` and stops before coding; `/design` is the
  design-first precursor; `/bug` and `/triage` are bug tracking, not `/flow`
  stages.)

## Commands

| Command | Description | Working directory |
|---|---|---|
| `uvicorn app.main:app --reload` | Start backend server locally | `src/backend` |
| `pytest` | Run backend tests | `src/backend` |
| `npm run dev` | Start frontend dev server | `src/frontend` |
| `npx vitest` | Run frontend tests | `src/frontend` |

## Pipeline Commands (multi-agent delivery)

The repo drives delivery through a five-role autonomous pipeline
(`analyst → architect → decomposer → product-owner → coder`), preceded by a
design-first `designer` precursor. **Read `Implementation/Pipeline.md` before
invoking any of them.**

- `/design` — designer (design-first precursor, NOT a `/flow` stage): authors/updates
  prototype screens for a requirement batch; always flags for human browser sign-off
  before `/spec`.
- `/spec` — analyst drafts/extends story(ies) from the PRD with untagged Gherkin.
- `/plan-tasks` — architect updates `architecture.md`/ADRs, then the decomposer
  locks ACs (assigns AC-IDs), creates flat-root task files, wires `depends_on`.
- `/plan-sprints` — product-owner partitions Ready, ungrouped stories into sprints
  (honouring the dependency graph; never mixing phases).
- `/implement-sprint` — autonomous build loop: one task at a time in dependency
  order; marks stories/sprints Done when every locked AC is verified; drafts retro.
- `/prep` — runs `/spec → /plan-tasks → /plan-sprints` and stops before coding.
- `/flow` — runs the full pipeline `/spec → /plan-tasks → /plan-sprints →
  /implement-sprint`, halting only at flagged exceptions; resumable.
- `/bug` — **interactive** capture (no agent): asks clarifying questions, logs a
  manual-test finding to `BUGS.md` at `Open`, mirrors it into `BACKLOG.md` `## Bugs`.
  Not a `/flow` stage.
- `/triage` — analyst (reused, no new agent): batches chosen `Open` bugs into one
  `Draft BUGFIX-NN-US-01` story (one Gherkin scenario per bug); standalone, then the
  normal `/plan-tasks → /plan-sprints → /implement-sprint` stages drive it to `Done`.

**Gating is exception-based, not mandatory.** Agents auto-advance clear work and
pause only when a MUST-FLAG trigger fires. Flagged items land in `REVIEW-QUEUE.md`.
Status is the single source of truth — commands act on `status:` and skip anything
already past their stage. To redo a stage, reset the artefact's `status:`.

Two human surfaces: **`ESCALATIONS.md`** is the permanent append-only *log* of
backward/out-of-scope events (resolved entries name a concrete resolving artefact and
are never edited); **`REVIEW-QUEUE.md`** is the transient *inbox* of everything
currently awaiting a human decision before the pipeline can proceed.

## Delivery Workflow

The delivery hierarchy is: **Requirement → User Story → Sprint → Task**

- **Requirement** (`Documentation/PRD.md`) — what the product must do. Each
  requirement has a unique ID (e.g. `REQ-SB-XX`).
- **User Story** (`Implementation/UserStories/`) — refines a requirement into an
  atomic, implementation-ready feature with acceptance criteria. One requirement may
  split into multiple stories. Story ID: `REQ-X.Y-US-NN` (anchored on its primary
  requirement).
- **Sprint** (`Implementation/Sprints/`) — scope-boxed grouping of related stories
  small enough to fit in one working context. Sprint ID: `SPRINT-NNN` (sequential,
  never reused). Single phase; never mixes phases. Every sprint
  ends with a retrospective; patterns and antipatterns from the retro are harvested
  into `Implementation/Learnings.md` by the human for future sprints to reference.
- **Task** (`Implementation/Tasks/`) — the concrete implementation steps for one
  story. Flat root, no subfolders. Task ID: `REQ-X.Y-US-NN-T<NN>`. Tasks carry
  `depends_on:` edges (other task IDs).
- **Backlog** (`BACKLOG.md`) — index of every PRD requirement and which stories
  implement it. Source of truth for "what still needs a story."
- **Bug** (`BUGS.md`) — a defect found through manual testing, tracked outside the
  requirement hierarchy. Bug ID: `BUG-NNN`. Captured via `/bug`, batched into a fix
  via `/triage`, which mints a phase-agnostic **bugfix story** (`BUGFIX-NN-US-01`)
  that flows through `/plan-tasks → /plan-sprints → /implement-sprint` like any
  story. One regression-test AC per bug; closed when its fix story is `Done`.

**Status vocabulary (unified across stories, tasks, and sprints):**
`Draft | Ready | In Progress | Blocked | Done`

**Gate vocabulary (separate from status):**
`clear | flagged` — set by the agent; `flagged` means the artefact is parked in
`REVIEW-QUEUE.md` and awaits a human decision before the pipeline proceeds.

**Phase vocabulary** — describes *when* delivered on the roadmap, not urgency. A
sprint is always single-phase.

## Roadmap Phases

| Phase | Focus |
|---|---|
| **MVP** | Obsidian vault indexing + search/browse over personal notes, no staging gate |
| **P1** | Hermes MCP integration for multi-channel communication |
| **P2** | Integration surface for agentic-map's agents to query this KB (future, cross-project work) |

## Source Module Layout

All application code lives under `src/`. Do not create new top-level directories.

**Backend (`src/backend`):** [Describe the module layout — packages/folders and
their purpose — once `/architect` establishes it at `/plan-tasks`.]

**Frontend (`src/frontend`):** [Describe the module layout — directories and
their purpose — once `/architect` establishes it at `/plan-tasks`.]
