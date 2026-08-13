---
id: REQ-SB-24-US-01
title: Provider pricing fields, per-agent token consumption recording, and accumulated cost display
requirement_ids: [REQ-SB-24]
requirement_section: "REQ-SB-24: Per-Agent Token Consumption & Cost Tracking"
phase: P1
status: Draft
gate: flagged
gate_reason: "feasibility risk resolved 2026-08-11 — real live Compass call confirmed a usage field IS present (prompt_tokens/completion_tokens/total_tokens, standard OpenAI shape). Remaining triggers: net-new-design-needed (no pricing fields or cost display anywhere in html-prototype/) and REQ-SB-19 not yet Done — see Notes"
sprint: ""
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-24-US-01 — Provider pricing fields, per-agent token consumption recording, and accumulated cost display

## Story

**As a** Second Brain user
**I want** each configured LLM Provider to carry its cost-per-token
pricing, the app to record how many tokens each agent actually consumes,
and each agent's accumulated cost shown to me
**So that** I can see and understand what my agents are actually costing
me, based on real consumption rather than a guess

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-24: Per-Agent Token Consumption &
  Cost Tracking* — "Each configured LLM Provider (REQ-SB-19) has pricing
  information (cost per token), and the app tracks how many tokens each
  agent consumes. The UI shows, per agent, how much it has cost based on
  its actual token consumption and its selected Provider's pricing."
  Acceptance: "Each configured Provider has a cost-per-token field (or
  equivalent); the app records token consumption per agent as it performs
  LLM-backed work; the UI shows each agent's accumulated cost, computed
  from its actual consumption and its selected Provider's pricing."
- **PRD breadcrumb (2026-08-11, operator-directed):** extends REQ-SB-19's
  Provider schema with pricing fields, "likely input/output token cost,
  mirroring how most LLM providers price asymmetrically" — adopted as-is
  below (the breadcrumb's own suggested shape, not invented independently).
  Left open: exact consumption-tracking granularity/window, and where cost
  is surfaced. Both addressed below; **depends on REQ-SB-19 (Provider
  concept must exist first)** — the PRD's own stated dependency.
- **Pricing field shape, resolved from the breadcrumb's own suggestion:**
  two fields per Provider — cost per input (prompt) token and cost per
  output (completion) token — added alongside REQ-SB-19-US-01's existing
  name/endpoint/credential/model fields. Mirrors the asymmetric-pricing
  convention essentially every real LLM API (OpenAI, Anthropic, and
  Compass's own OpenAI-compatible shape) already uses.
- **Consumption window, resolved from the acceptance text's own wording:**
  "accumulated cost" (the literal word used) — an all-time cumulative
  total per agent, not a rolling/reset window. No PRD text anywhere
  suggests a reset or rolling period. Exact storage granularity (raw
  per-call token counts summed, vs. a running total updated per call) is
  an implementation detail left to `/plan-tasks`.
- **Where cost is surfaced, resolved by elimination:** the PRD breadcrumb
  suggests "the Agent Settings surface, alongside REQ-SB-11's observability
  work, or both" — `REQ-SB-11` (Agent Activity & Error Observability) has
  **no story and no built surface at all** to place anything "alongside,"
  so that half of the suggestion doesn't currently apply. This story
  surfaces accumulated cost on the Agent Settings surface only (the
  existing per-agent `kv-list`/detail panel built by `REQ-SB-13-US-01`) —
  the only existing UI surface with structured per-agent data today.
- **Feasibility risk found, then resolved with a real live check
  (2026-08-11).** `src/backend/app/data_access/compass_client.py`'s
  `classify_email` function currently reads only
  `data["choices"][0]["message"]["content"]` from Compass's JSON response
  — it never reads `data.get("usage")`. A real, live call to the real
  Compass endpoint (`compass_base_url`, same credentials this project
  already uses) confirmed the raw response **does** include a top-level
  `usage` object: `{"prompt_tokens": 13, "completion_tokens": 11,
  "total_tokens": 24, ...}` — the standard OpenAI-compatible shape,
  confirmed as fact for this specific deployment, not just a documented
  convention. Real per-call token tracking is feasible without any
  fallback/estimation mechanism — `compass_client.py` just needs to
  capture and return `usage.prompt_tokens`/`usage.completion_tokens`
  alongside its existing return value.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: A Provider entry carries cost-per-token pricing

```gherkin
Given the user is adding or editing a Provider entry in Global Settings
When the user supplies a cost-per-input-token and cost-per-output-token
    value
Then the Provider entry stores both pricing values alongside its existing
    name/endpoint/credential/model fields
```

### Scenario 2: Token consumption is recorded as an agent performs LLM-backed work

```gherkin
Given an agent whose selected Provider is configured and functional
When that agent performs a real piece of LLM-backed work (e.g. a
    classification call)
Then the number of tokens that call consumed is added to that agent's
    accumulated consumption total
```

### Scenario 3: The UI shows an agent's accumulated cost, computed from consumption and its Provider's pricing

```gherkin
Given an agent has accumulated some token consumption, and its selected
    Provider has pricing configured
When the user views that agent's Agent Settings surface
Then the agent's accumulated cost is shown, computed from its accumulated
    consumption and its selected Provider's pricing
```

### Scenario 4: An agent with no recorded consumption shows a clear zero/no-cost state

```gherkin
Given an agent has never performed any LLM-backed work
When the user views that agent's Agent Settings surface
Then its accumulated cost is shown as zero (or an equivalent "no usage
    yet" indication), not blank or an error
```

### Scenario 5: A Provider with no pricing configured shows cost as unavailable, not a fabricated number

```gherkin
Given an agent's selected Provider has no pricing configured (e.g. an
    older Provider entry created before pricing fields existed)
When the user views that agent's Agent Settings surface
Then the accumulated cost is shown as unavailable/not priced, rather than
    a computed value based on missing or zero pricing
```

## Affected Screens

- `html-prototype/settings.html` — the Providers card's add/edit forms
  (built for `REQ-SB-19-US-01`) **need two new pricing fields.** Not
  present in the currently-approved prototype — confirmed by direct
  inspection.
- `html-prototype/agents-map.html` — the agent detail side panel's
  Settings `kv-list` **needs a new accumulated-cost row.** Not present in
  the currently-approved prototype — confirmed by direct inspection.

## Dependencies

- **Blocked by:** `REQ-SB-19` (`REQ-SB-19-US-01`, `Ready`, not yet `Done`)
  — the Provider concept, and the Settings/Agent-panel surfaces this story
  extends, must exist first. Per the PRD's own explicit statement
  ("Depends on REQ-SB-19"). This story can be planned now but should not
  be built ahead of `REQ-SB-19-US-01` landing.
- **Related to:** `src/backend/app/data_access/compass_client.py` — the
  one place Compass's raw HTTP response is available to read a `usage`
  object from, if present (see Context's flagged feasibility risk).
- **Related to:** `REQ-SB-11` (Agent Activity & Error Observability, no
  story yet) — the PRD breadcrumb's alternate/additional surface
  suggestion; not available to build against yet (see Context).
- **External:** none new — no new dependency; whether the mechanism is
  feasible depends on Compass's actual (unverified) response shape, not a
  missing library.

## Constraints

- **Pricing fields:** cost-per-input-token and cost-per-output-token,
  added to the Provider schema `REQ-SB-19-US-01` establishes. Exact field
  names/types are left to `/plan-tasks`.
- **Consumption is all-time cumulative per agent**, not a rolling or
  resettable window (see Context) — no "reset usage" action is in scope.
- **Cost must never be fabricated when pricing is missing** (Scenario 5) —
  mirrors this project's standing "honest, not fabricated" posture
  (`ADR-011`, `REQ-SB-19-US-01`'s own unavailable-Provider behaviour).
- **No retroactive/historical backfill** — consumption tracking starts
  accumulating from when this story's mechanism ships; LLM calls made
  before it existed are not retroactively counted (no reliable way to
  reconstruct them).
- Token counts are captured by reading `usage.prompt_tokens`/
  `usage.completion_tokens` from Compass's real response (confirmed
  present, see Context) — no fallback/estimation mechanism is needed or
  in scope.
- No backend endpoint currently returns per-agent consumption/cost data —
  new API surface is required; exact shape left to `/plan-tasks`.

## Implementation Tasks

<!-- Left for the architect/decomposer at /plan-tasks. -->

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **A "reset usage" or rolling-window consumption view** — accumulated,
  all-time only, this pass.
- **Retroactively reconstructing consumption for LLM calls made before
  this story ships.**
- **Building a fallback token-estimation mechanism** (e.g. a local
  tokenizer) — not needed; Compass's real response confirmed to include
  `usage` (see Context).
- **Surfacing cost anywhere beyond the Agent Settings surface** — e.g. a
  dedicated cost-dashboard/observability page — out of scope until
  `REQ-SB-11` exists as a real story.
- **Per-call cost history/breakdown** — only the accumulated total is
  shown; a chronological log of individual calls and their cost is not
  requested by the acceptance text.

## Notes

**Prototype parity (settings.html, agents-map.html):**

- `settings.html`'s Providers card (name/endpoint/credential/model,
  add/edit/blocked-removal) — **N/A**, built by `REQ-SB-19-US-01`, not
  re-touched structurally here beyond adding the two pricing fields.
- `settings.html`'s Providers card pricing fields — **needs `/design`.**
  Confirmed absent from the currently-approved prototype.
- `agents-map.html`'s side panel Settings `kv-list` — **needs `/design`**
  for the new accumulated-cost row. Confirmed absent.

**The Compass `usage` feasibility risk — resolved 2026-08-11.** A real
live call confirmed `usage: {prompt_tokens, completion_tokens,
total_tokens, ...}` is present in Compass's actual response for this
deployment (see Context for the exact fields observed). No fallback
estimation mechanism is needed; the mechanism is a straightforward
`compass_client.py` extension.

**Why this remains flagged:** two conditions remain: (1)
`net-new-design-needed` — neither affected screen's new region (pricing
fields; cost display) exists in the approved prototype; (2) this story's
primary dependency, `REQ-SB-19`, is not yet `Done` (still `Ready`, itself
gate-flagged pending `ADR-014` review). The feasibility risk that was the
third original trigger is now closed.

`gate: flagged` 2026-08-11 — `net-new-design-needed` and the not-yet-`Done`
`REQ-SB-19` dependency remain; the feasibility risk is resolved (see
above). A `REVIEW-QUEUE.md` entry recommends `/design REQ-SB-24` (once
`REQ-SB-19-US-01`'s own Providers/agent-panel UI has actually landed,
since this story's new fields extend that UI rather than standing alone).
