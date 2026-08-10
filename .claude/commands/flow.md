Run the full pipeline `/spec → /plan-tasks → /plan-sprints → /implement-sprint`
end-to-end, halting only at flagged exceptions.

## Usage

- `/flow` — process everything eligible from start to finish
- `/flow REQ-SB-01` — run the full pipeline for a specific requirement

## What this does

Runs in order: analyst → architect → decomposer → product-owner → coder (one task
at a time), all per the rules in their respective agent files.

**Per-item flow:** each artefact advances as far as its status + gate allow. Clean
items proceed all the way to implemented code; flagged items park at their flagged
stage in `REVIEW-QUEUE.md`. `/flow` never blocks clean items behind flagged ones.

**Resumable:** re-run after clearing flags and it advances whatever is now
unblocked. It stops when every item is `Done` or parked-flagged, with a consolidated
`REVIEW-QUEUE` summary.

Read `Implementation/Pipeline.md` before running.
