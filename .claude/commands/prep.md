Run `/spec → /plan-tasks → /plan-sprints` end-to-end and stop before any coding.

## Usage

- `/prep` — prepare everything eligible through the planning stage
- `/prep REQ-SB-01` — prepare a specific requirement

## What this does

Runs: analyst (`/spec`) → architect + decomposer (`/plan-tasks`) → product-owner
(`/plan-sprints`) in sequence.

Produces a fully-planned sprint (stories + tasks + sprint assignment) ready for
human review before any code is written. Same exception-gating and resumability
as `/flow` — clean work auto-advances, flagged work parks. Re-run at any time to
pick up from the current state.
