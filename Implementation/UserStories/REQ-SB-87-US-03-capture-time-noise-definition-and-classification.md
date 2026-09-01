---
id: REQ-SB-87-US-03
title: Capture-time noise definition, skip, and Internal/Partner/Customer classification
requirement_ids: [REQ-SB-87]
requirement_section: "REQ-SB-87: Email Thread Capture — a New, LLM-Driven Pipeline (Classify, Skip Noise, Summarize, Find Pending Actions)"
phase: P1
status: Ready
gate: flagged
gate_reason: "trigger-3 (ADR-018 created — Capture-stage classify-or-skip mechanism: bounded one-shot relay call embedded in the existing deterministic loop, not a job4-style restructure) — see REVIEW-QUEUE.md"
sprint: "SPRINT-084"
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-03 — Capture-time Noise Definition, Skip, and Internal/Partner/Customer Classification

## Story

**As** the operator relying on `email-delta-capture` to keep the vault current
**I want** the Capture stage to judge each newly-seen email conversation against a
real, inspectable, LLM-derived noise definition, skip creating any Thread/RawMessage
at all for content that definition marks as noise, and stamp a real Internal-only /
Partner-related / Customer-related classification value on every Thread it does
create
**So that** Threads land already usefully labeled instead of undifferentiated, and my
vault stops accumulating Threads I never wanted captured in the first place — instead
of capturing everything and hiding the noise later.

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-87*, points 3 ("Real classification, as
  structured data, not prose... Think Data"), 4 ("Noise is filtered at CAPTURE time,
  not Enrich time"), 5/6 ("Use LLM to Define what noise is Not just a Judge"), 7
  (prompt-driven, minimal-code principle), 8 (Sent+Inbox stay combined, unchanged).
- **Depends on** [[REQ-SB-87-US-01]] — the Thread template must declare the new
  classification frontmatter field before this story can write it.
- **Depends on** [[REQ-SB-87-US-02]] — this story's own judgment step is layered onto
  `ingest_email.py`'s already-migrated, `vault_manager.py`-based flow, not built
  against the soon-to-be-retired `vault_lib.py` code path.
- **Real code read directly, not assumed:** `ingest_email.py`'s own
  `if existing_directory is None: create_thread_note_baseline(...)` branch is the
  ONE place a first-seen-conversation decision is made today — the natural
  insertion point for a classify-or-skip judgment.
- **A genuine architecture fork found by reading the real code, not decided here:**
  `run_delta_capture.py`/`run_full_capture.py` (the live, recurring
  `email-delta-capture` cron's own real code path) implement the entire per-email
  loop as ONE non-agentic Python process today — confirmed directly, `SKILL.md`'s
  own words: "one long-running `terminal` call instead of ~4 calls x every single
  email," zero LLM/agent involvement per email. There is no live judgment call
  anywhere in today's real recurring capture path. `summarize-and-tag-threads`'s own
  sibling recurring cron (`job4-summarize-tag-threads`), by direct contrast, DOES run
  as a live Hermes agent session every time it fires (`SKILL.md`'s own "this runs
  across MULTIPLE sessions" resumability design, batch-by-batch, skip-rule-gated) —
  real, working, ALREADY-PROVEN precedent in this SAME codebase for a
  cron-triggered live LLM-judgment loop. Two structurally different, both real,
  both precedented shapes exist side by side in this project today; which one
  Capture's own new judgment step should follow (embed a lightweight real
  Provider/LLM call directly inside the existing non-agentic Python loop, vs.
  restructure Capture's recurring path into an agent-driven, batch-by-batch shape
  mirroring `job4`) is a genuine fork with real, differently-shaped consequences —
  not guessed here (see MUST-FLAG below).
- **Real, confirmed evidence the operator already hand-probed this exact idea:**
  `Work/Threads/2026-08-31 Masdar Open Items/...md`, `2026-08-31 TAQA/...md`, and
  other real, recently-processed Threads already carry a bare `"internal"` string in
  their real `tags` list, alongside the genuine `customer/<slug>`/`partner/<slug>`
  tags `apply_thread_review.py` also wrote — confirming the classification concept
  was already being hand-tested as a plain tag before this story existed. The PRD's
  own "Think Data" instruction (point 3) argues for a real, dedicated, structured
  frontmatter field going forward, not a continuation of that ad hoc tag.
- `outlook_lib.py`'s own 2026-08-24 Sent Mail inclusion design (Sent + Inbox combined
  into the same Thread) is confirmed correct and wanted (PRD point 8) — this story
  must not regress it.
- `BUG-042` (Open) — the EXISTING, separate, fine-grained `customer/<slug>`/
  `partner/<slug>` company-matching mechanism `apply_thread_review.py` performs is
  currently mis-resolving some real Threads. This story's new coarse classification
  is deliberately DISTINCT from and does not fix that bug — see Non-Goals.

## Acceptance Criteria

### Scenario 1: A genuinely noisy email produces no Thread and no RawMessage at all
```gherkin
Given an email whose conversation_id has never been captured before, and its content
  matches the current noise definition
When the Capture stage processes it
Then no Thread note and no RawMessage note are ever written for it
  And nothing about it lands anywhere in the vault as a permanent captured note —
  never a "capture then hide" outcome
```
<!-- AC-ID: REQ-SB-87-US-03-AC-01 -->

### Scenario 2: A non-noise email creates a Thread stamped with exactly one real classification value
```gherkin
Given a first-seen conversation_id whose content does not match the noise definition
When the Capture stage creates its Thread
Then the Thread's own frontmatter carries a real classification value of exactly one
  of Internal-only, Partner-related, or Customer-related — never Noise (a Thread that
  would be Noise is never created at all, per Scenario 1)
  And this value is a real, structured, queryable frontmatter field — never embedded
  only in prose, and never conflated with the tags list
```
<!-- AC-ID: REQ-SB-87-US-03-AC-02 -->

### Scenario 3: Classification is decided once, at first sight of a conversation
```gherkin
Given a Thread that already exists with a real classification value already stamped
When a further email arrives on that same conversation_id
Then the existing RawMessage-creation/capture flow proceeds exactly as it does today
  for that Thread
  And the Thread's own classification value is left unchanged — it is never
  re-evaluated or overwritten by a later message on the same conversation
```
<!-- AC-ID: REQ-SB-87-US-03-AC-03 -->

### Scenario 4: The noise definition is a real, structured, inspectable artifact
```gherkin
Given the noise definition has already been derived at least once
When Capture classifies a new email
Then the classify-or-skip decision is made against that already-derived, persisted
  definition, not a brand-new, un-recorded judgment invented from scratch for this
  one email
  And the definition itself can be read/inspected independently of any capture run
```
<!-- AC-ID: REQ-SB-87-US-03-AC-04 -->

### Scenario 5: The noise definition can be tweaked and re-applied without touching Capture-stage code
```gherkin
Given the operator wants to broaden or narrow what counts as noise (e.g. during the
  100-email scratch-sample proving phase)
When the noise definition is updated
Then the very next capture run classifies against the updated definition
  And no change to any Capture-stage script's own code is required to make that
  happen
```
<!-- AC-ID: REQ-SB-87-US-03-AC-05 -->

### Scenario 6: Sent and Inbox items are still captured together, unaffected by the new judgment step
```gherkin
Given both Sent Mail and Inbox items exist for the same conversation
When Capture runs with the new classify-or-skip step in place
Then both folders' items continue to be combined into the same Thread exactly as
  today's 2026-08-24 design already does
  And the new judgment step never excludes a Sent item merely because it originated
  from the user's own mailbox
```
<!-- AC-ID: REQ-SB-87-US-03-AC-06 -->

### Scenario 7: A capture run reports what it skipped
```gherkin
Given one or more emails were classified as noise and skipped during a capture run
When that run completes
Then its own printed/returned summary (the same JSON shape
  run_full_capture.py/run_delta_capture.py already report) includes a count of how
  many were skipped as noise, so the operator is never left wondering why a
  captured-email count looks lower than the real mailbox
```
<!-- AC-ID: REQ-SB-87-US-03-AC-07 -->

## Affected Screens

None — backend only (Hermes-Provisioning Skill scripts + a new noise-definition
artifact; no `src/frontend` or `html-prototype/` surface).

## Dependencies

- **Blocked by:** [[REQ-SB-87-US-01]] — the Thread template's own classification
  frontmatter field must exist first.
- **Blocked by:** [[REQ-SB-87-US-02]] — this story's own judgment step is layered
  onto the already-migrated `ingest_email.py` flow.
- **Related:** [[REQ-SB-87-US-04]] / [[REQ-SB-87-US-05]] — the Enrich-side sibling
  stories; independent file scope, no shared files, both extend the same overall
  Thread concept.
- **External:** none.

## Constraints

- **Prompt-driven, minimal code (PRD point 7):** the classify-or-skip judgment and
  the noise-definition's own derivation are agent-prompt/LLM reasoning, never a
  hand-written keyword/sender heuristic. Any new CODE this story adds is limited to
  the mechanical persistence of a judgment already made (writing the classification
  frontmatter field, reading/writing the noise-definition artifact, the skip branch
  itself) plus whatever minimal, disclosed wrapper is needed to actually invoke that
  judgment from within Capture's own real, currently non-agentic recurring loop —
  the exact shape of that wrapper is the open architecture fork below.
- **The exact mechanism by which a live LLM judgment gets invoked inside Capture's
  own currently non-agentic recurring loop is a genuine, unresolved architecture
  fork — not decided here.** See Context and MUST-FLAG.
- **The exact shape/location/regeneration mechanism of the noise-definition
  artifact** (a config file under the Skill's own `scripts/` directory? a
  Template-adjacent data file? regenerated wholesale each tweak, or incrementally
  amended?) is left open, per the PRD's own explicit "still genuinely open, left to
  `/spec`" framing — deferred to `/plan-tasks`.
- **The exact frontmatter field name/shape for the new coarse classification** (e.g.
  `classification: "internal" | "partner" | "customer"`) is left to `/plan-tasks` —
  Scenario 2's own constraint is only that it is a real, structured, queryable
  frontmatter value, distinct from `tags` and distinct from the existing
  fine-grained `customer/<slug>`/`partner/<slug>` tag-matching.
- A Thread genuinely about BOTH a Partner and a Customer at once (a real, if
  uncommon, case) still gets exactly ONE coarse classification value — the
  precedence rule for that tie-break is an implementation detail, not locked here.
- A Thread's own fine-grained `customer/<slug>`/`partner/<slug>` tags
  (`apply_thread_review.py`'s own job, `BUG-042`) are untouched by this story — the
  new coarse classification complements, never replaces, that mechanism.
- Never regress the already-confirmed-correct Sent+Inbox combined capture design
  (`outlook_lib.py`, 2026-08-24).
- This story only governs a NEW first-seen conversation's own classify-or-skip
  decision going forward — no backfill/retrofit/reclassification of already-existing
  Threads.
- Same production-risk posture as [[REQ-SB-87-US-02]]: prove the new judgment step
  against a real scratch-vault sample (the operator's own already-locked 100-email
  proving-phase rollout, per the PRD's own raised-context point 2) before it runs
  against the real, live vault via the cutover `--vault-path` change.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-87-US-03-T01 | backend | Noise-definition artifact + out-of-band derivation mechanism | `.second-brain/data/EmailCapture/noise_definition.json` (or equivalent), a new derivation script | `REQ-SB-87-US-03-T01-noise-definition-artifact-and-derivation.md` |
| REQ-SB-87-US-03-T02 | backend | Provision the dedicated classifier Hermes profile | `Hermes-Provisioning/profiles/<new classifier profile>/` (exact location decomposer/coder-level) | `REQ-SB-87-US-03-T02-classifier-hermes-profile.md` |
| REQ-SB-87-US-03-T03 | backend | Wire the classify-or-skip relay call into `ingest_email.py` | `Hermes-Provisioning/skills/vault-rebuild/email-thread-capture/scripts/ingest_email.py` | `REQ-SB-87-US-03-T03-wire-classify-or-skip-relay.md` |
| REQ-SB-87-US-03-T04 | backend | Report skip count through the orchestrators' JSON summary | `.../scripts/run_full_capture.py`, `.../scripts/run_delta_capture.py` | `REQ-SB-87-US-03-T04-report-skip-count.md` |
| REQ-SB-87-US-03-T05 | backend | Scratch-vault proving-phase verification + noise-definition retune pass + cutover | (verification + `--vault-path` cutover, no code changes) | `REQ-SB-87-US-03-T05-scratch-proving-and-cutover.md` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- Retrofitting/reclassifying already-captured Threads with the new coarse
  classification value — this story only governs new captures going forward.
- Any change to the existing fine-grained `customer/<slug>`/`partner/<slug>`
  tag-matching `apply_thread_review.py` performs — `BUG-042` stays a separate,
  already-tracked Open bug, not silently absorbed here.
- Any change to Enrich-stage summary/action extraction — see [[REQ-SB-87-US-04]] /
  [[REQ-SB-87-US-05]].
- A UI surface for reviewing or overriding a skip decision — not requested by the
  PRD.
- A per-message (rather than per-Thread, first-sight-only) classification/skip
  re-evaluation — see the Constraints entry on classification being decided once.

## Notes

**Prototype parity:** not applicable — this story has no `html-prototype/` surface
(backend-only, no UI).

**MUST-FLAG triggers fired:**
- Trigger 8 (multiple, genuinely equally-valid, real architecture options) — the
  live-LLM-judgment-inside-a-currently-non-agentic-recurring-loop fork (embed a
  lightweight Provider call directly in `run_delta_capture.py`'s own Python loop, vs.
  restructure Capture's recurring path into an agent-driven, batch-by-batch shape
  mirroring `job4-summarize-tag-threads`'s own already-proven recurring-agent-session
  shape) — both real, both precedented in THIS codebase, genuinely different in
  consequence. Also the noise-definition artifact's own shape/regeneration
  mechanism, explicitly named as still-open in the PRD's own text. Neither is
  guessed here; both are deferred to `/plan-tasks`'s architect step, matching
  [[REQ-SB-87-US-01]]'s own precedent for the growing-children question.
- Trigger 1 (material assumption) — classification is scoped as decided ONCE, at
  first sight of a conversation, never re-evaluated on a later message on the same
  Thread. A reasonable, minimal reading consistent with how every other Thread-level
  frontmatter field already works, but disclosed as a scoping choice rather than
  silently picked among other readings (e.g. per-message re-evaluation).

gate: flagged 2026-09-01 — see `gate_reason` and the trigger notes above.

**Architect resolution (2026-09-01):** the architecture fork is resolved —
Capture's own recurring loop STAYS the existing deterministic,
subprocess-orchestrated design; the classify-or-skip judgment is invoked as
ONE bounded, one-shot `hermes -p <profile> chat -q "..."` relay subprocess
call per newly-first-seen `conversation_id` only, embedded directly inside
`ingest_email.py`'s existing flow — NOT a `job4`-style restructure into a
live, multi-turn, resumable agent session. `job4`'s own resumability design
solves a different problem (a one-time 209-Thread backlog too large for one
session's context); Capture's own judgment is comparatively tiny (one
email's content, once per new conversation) on a short, unattended,
recurring cadence, where the existing pipeline's own deliberately-engineered
O(1)-LLM-round-trips-per-tick property is worth preserving, especially given
this same pipeline's own real, same-day gateway-down incident. The
noise-definition artifact's own shape is also resolved: a real, structured,
persisted file under the vault's own `.second-brain/data/` tree (a new
sibling to `Templates/`), read directly (zero deploy step) by every Capture
script that already receives `--vault-path` — mirroring `Template.json`'s
own already-established live-vault-path convention. Its DERIVATION (the
LLM-driven definition-building step) is a separate, out-of-band act,
decoupled from the recurring tick. Full reasoning, Alternatives Considered,
and Consequences in `ADR-018`.

**Architecture scope:** `architecture.md` → §Capture-Time Classification &
Noise-Skip (`REQ-SB-87-US-03`, `ADR-018`) — the decomposer and coder are
bounded by this section plus `ADR-018`'s own full Decision text. This story
also depends on `ADR-017`'s Thread template classification frontmatter
field declaration (`US-01`).

**MUST-FLAG trigger 3 fired (ADR created):** `ADR-018` — `gate` stays
`flagged` for human review of the ADR alongside the resulting tasks (the
decomposer still runs; see `REVIEW-QUEUE.md`).

**Decomposer pass (2026-09-01):** all 7 scenarios locked
(`REQ-SB-87-US-03-AC-01`..`AC-07`), 5 tasks created (`T01`..`T05`, chain
`T01 → T02 → T03 (also ← REQ-SB-87-US-02-T01) → T04 → T05`). `T03`'s own
disclosed relay-failure degrade default (per `ADR-018`'s own Consequences,
left decomposer/coder-level): a relay failure/timeout for one
conversation's classify-or-skip call is treated as NOT YET classified —
no Thread is created, no permanent skip is recorded — letting the SAME
per-email `try/except ... continue` pattern already in the orchestrators
retry that conversation on the NEXT tick, since `existing_directory` stays
`None` until a Thread is actually written. Every task's own `## Tests`
names the real ~100-email scratch-vault proving-phase sample explicitly;
`T05` is the one task that performs the real-vault cutover. Every locked
AC has at least one AC-tagged verification step, `depends_on` is acyclic
— `status` advances `Draft → Ready`, all 5 tasks written at `status:
Ready`. `gate` left untouched (`flagged`, per `ADR-018`'s own human-review
requirement).
