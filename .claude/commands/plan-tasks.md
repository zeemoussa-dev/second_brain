Run the **architect** then the **decomposer** to lock acceptance criteria and create
task files for user stories.

## Usage

- `/plan-tasks` — act on every `Draft` story with `gate: clear` and no tasks yet
- `/plan-tasks REQ-X.Y-US-01` — act on a specific story
- `/plan-tasks REQ-X.Y-US-01 REQ-X.Y-US-02` — act on a list

## What this does

1. Read `Implementation/Pipeline.md` and `Implementation/Learnings.md`.
2. **Step 1 — architect** (subagent_type: architect): updates `architecture.md`,
   appends any needed ADRs, records architecture scope in the story's `## Notes`.
   Any ADR change sets `gate: flagged` but does NOT halt — the decomposer still runs.
3. **Step 2 — decomposer** (subagent_type: decomposer): assigns AC-IDs to the
   story's untagged Gherkin, creates flat-root task files in
   `Implementation/Tasks/`, wires `depends_on` edges, adds AC-tagged verification
   steps, advances the story `Draft → Ready` when all checks pass.
4. Clear stories advance; flagged stories park in `REVIEW-QUEUE.md`.

Ready + ungrouped stories are eligible for `/plan-sprints`.
