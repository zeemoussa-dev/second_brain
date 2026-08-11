# BACKLOG

Index of all PRD requirements and the user stories that implement them. Updated by
the analyst at `/spec` and by the product-owner at `/plan-sprints`.

## How to read this

- **No story link** = not yet started (run `/spec REQ-SB-XX` to begin)
- **Story link** = story exists; check its status
- **Sprint** = which sprint this requirement is being built in

---

## MVP

| Req ID | Description | Story | Story Status | Sprint | Sprint Status |
|---|---|---|---|---|---|
| REQ-SB-01 | Vault Indexing | — | — | — | — |
| REQ-SB-02 | Browse & Search | — | — | — | — |

## P1

| Req ID | Description | Story | Story Status | Sprint | Sprint Status |
|---|---|---|---|---|---|
| REQ-SB-03 | Conversational Agent Access via Hermes | — | — | — | — |
| REQ-SB-04 | Agent Vault Write Access | — | — | — | — |
| REQ-SB-05 | Content Ingestion Path | — | — | — | — |
| REQ-SB-07 | Scheduled Recurring Agent Capture | [REQ-SB-07-US-01](Implementation/UserStories/REQ-SB-07-US-01-scheduled-recurring-capture.md) | Done | [SPRINT-001](Implementation/Sprints/SPRINT-001-scheduled-recurring-capture.md) | Done |
| REQ-SB-08 | Meetings Capture Pipeline | — | — | — | — |
| REQ-SB-09 | To-Do Task Capture Pipeline | — | — | — | — |
| REQ-SB-10 | People Living Documents | — | — | — | — |
| REQ-SB-11 | Agent Activity & Error Observability | — | — | — | — |
| REQ-SB-12 | Primary Application UI Shell — Agents Map & My Day | — | — | — | — |
| REQ-SB-13 | Embedded Agent Chat & Communication History | — | — | — | — |
| REQ-SB-14 | Vault Graph Connectivity | [REQ-SB-14-US-01](Implementation/UserStories/REQ-SB-14-US-01-vault-graph-connectivity.md) | Done | [SPRINT-002](Implementation/Sprints/SPRINT-002-vault-graph-connectivity.md) | Done |
| REQ-SB-15 | Manual-Entry Templates & Guidelines | [REQ-SB-15-US-01](Implementation/UserStories/REQ-SB-15-US-01-manual-entry-templates-and-guide.md) | Done | [SPRINT-003](Implementation/Sprints/SPRINT-003-manual-entry-templates-and-guide.md) | Done |

## P2

| Req ID | Description | Story | Story Status | Sprint | Sprint Status |
|---|---|---|---|---|---|
| REQ-SB-06 | Search Quality Enhancements | — | — | — | — |

---

## Sprint Status

| Sprint | Title | Phase | Status | Depends On | Sizing |
|---|---|---|---|---|---|
| [SPRINT-001](Implementation/Sprints/SPRINT-001-scheduled-recurring-capture.md) | Scheduled recurring email capture (hourly + app-start + catch-up) | P1 | Done | None | ~4 tasks, S |
| [SPRINT-002](Implementation/Sprints/SPRINT-002-vault-graph-connectivity.md) | Automated Customer hub notes and wikilinking for vault graph connectivity | P1 | Done | None | ~4 tasks, S |
| [SPRINT-003](Implementation/Sprints/SPRINT-003-manual-entry-templates-and-guide.md) | Obsidian manual-entry templates and in-vault guide note | P1 | Done | None | ~2 tasks, XS |

---

## Bugs

Thin status **mirror** of [`BUGS.md`](BUGS.md) (the source of truth — repro steps,
expected/actual, and screenshots live there, not here). Never edit by hand: `/bug`
adds rows at `Open`, the analyst flips them to `In Sprint` at `/triage` (writing the
fix-story link), and the coder flips them to `Closed` when the `BUGFIX-NN` story is
`Done`. The actor that changes a bug's status updates `BUGS.md` and this table in the
same touch. Status: `Open | In Sprint | Closed | Won't Fix`.

| ID | Title | Area | Status | Fixed by |
|---|---|---|---|---|
| _none yet_ | | | | |
