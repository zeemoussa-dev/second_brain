Run the **product-owner** to partition Ready, ungrouped stories into sprints.

## Usage

- `/plan-sprints` — act on all `Ready` stories with no `sprint:` assigned
- `/plan-sprints "merge SPRINT-002 and 003"` — pass optional free-text guidance

## What this does

1. Read `Implementation/Pipeline.md`.
2. Invoke the product-owner agent (subagent_type: product-owner).
3. Read all `Ready` stories with `sprint: ""` and build the dependency graph from
   task `depends_on` edges.
4. Partition stories into one-or-more sprint files in `Implementation/Sprints/`.
5. Set `sprint: SPRINT-NNN` in each story's frontmatter (bidirectional link).
6. Advance clear groupings `Draft → Ready`; flag ambiguous/oversized ones.
7. Update `BACKLOG.md` Sprint Status table and per-requirement Sprint column.

`Ready` sprints are eligible for `/implement-sprint`. Flagged sprints park in
`REVIEW-QUEUE.md`.
