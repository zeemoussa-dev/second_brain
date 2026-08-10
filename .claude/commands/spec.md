Run the **analyst** agent to draft or extend user stories from the PRD.

## Usage

- `/spec` — act on every PRD requirement in `BACKLOG.md` that has no story yet
- `/spec REQ-SB-01` — act on a specific requirement
- `/spec REQ-SB-01 REQ-SB-02` — act on a list

## What this does

1. Read `Implementation/Pipeline.md`.
2. Invoke the analyst agent (subagent_type: analyst).
3. Read `Documentation/PRD.md` and existing stories to avoid duplication.
4. For each target requirement, draft a user story with untagged Gherkin ACs.
5. Auto-advance clear stories (`gate: clear`, `status: Draft`).
6. Park unclear stories with `gate: flagged` and append to `REVIEW-QUEUE.md`.
7. Update `BACKLOG.md` to link each requirement to its story ID(s).

Clear stories are ready for `/plan-tasks`. Flagged stories wait for the human.
