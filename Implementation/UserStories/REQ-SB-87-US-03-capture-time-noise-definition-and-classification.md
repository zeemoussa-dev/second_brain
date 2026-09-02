---
id: REQ-SB-87-US-03
title: Capture-time noise definition, skip, and Internal/Partner/Customer classification
requirement_ids: [REQ-SB-87]
requirement_section: "REQ-SB-87: Email Thread Capture — a New, LLM-Driven Pipeline (Classify, Skip Noise, Summarize, Find Pending Actions)"
phase: P1
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-018 created — Capture-stage classify-or-skip mechanism: bounded one-shot relay call embedded in the existing deterministic loop, not a job4-style restructure) — see REVIEW-QUEUE.md; standing human-review flag, unresolved by story completion"
sprint: "SPRINT-084"
created: 2026-09-01
updated: 2026-09-02
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
- **Added 2026-09-02 (PRD `REQ-SB-87` point 7 + its own "Second expanded-scope
  raised-context pass," operator's own direct answers, verbatim):** three real
  business rules, now locked, not open questions:
  1. Sent items are NEVER classified as noise — a message the operator
     themselves wrote is real signal by definition (operator: "No Sent Items
     are never noise").
  2. The noise judgment fires only ONCE, on a genuinely NEW `conversation_id`
     — this already matches `ADR-018`'s own locked mechanism (the classify-
     or-skip relay call is invoked only from `ingest_email.py`'s own
     `if existing_directory is None:` branch); the operator's own confirmation
     ("if we already have a thread and I kept it that means that the emails
     that comes to this thread even if it counts as noise need to be stored")
     makes this an explicit, tagged business rule rather than an implicit
     consequence of the architecture alone — see Scenario 9 below.
  3. The real noise definition: anything automated/broadcast — NOT limited to
     literal meeting-invite `.ics` items (those are already filtered upstream
     via `MessageClass`, `_MEETING_MESSAGE_CLASS_PREFIX`, confirmed directly
     in `outlook_lib.py`, before classification ever runs) but the broader
     category: system/HR/security notifications, broadcast newsletters,
     workshop/event-announcement blasts. Real, live example subjects already
     in the vault, operator-confirmed noise-shaped: "Learning Assignment
     Changes Email Notification", "New Payslip available for
     viewing-download", "Core42 Information Security Awareness Training",
     "Compass Alert- Failed API Calls", "CRM Enhancements - Weekly Release
     Summary" — real seed examples/criteria to ground the LLM-derived
     definition against (per `ADR-018`'s own already-settled "LLM derives a
     structured definition, not a fresh per-email judge" design), not a
     hardcoded rule list replacing that design. See Scenario 10 below.
  None of these three change `ADR-018`'s own already-resolved architecture
  (the one-bounded-relay-call mechanism, the noise-definition-as-structured-
  artifact design) — they are real, additive business-rule content layered on
  top of it, not a re-litigation.
- **Added 2026-09-02 (PRD point 8, real cross-story sequencing):** the real
  100-message retrofit [[REQ-SB-87-US-02]]'s own `T05` performs must include
  real classification for every one of the 100 messages, written into
  frontmatter, even where the ultimate decision on a given message is "keep"
  (operator: "the Classification SHould Exist in the front matter"). This
  means THIS story's own classification-writing capability must exist and be
  verified working BEFORE `REQ-SB-87-US-02-T05` runs — see Dependencies below.

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

### Scenario 8: Sent items are never classified as noise (added 2026-09-02)
```gherkin
Given an email read from the Sent Mail folder (direction: "sent"), regardless
  of what its own subject/sender content looks like in isolation
When the Capture stage classifies it as part of a genuinely new
  conversation_id
Then it is never classified as Noise and never skipped
  And the resulting Thread is created and stamped with exactly one real
  classification value (Internal-only, Partner-related, or Customer-related)
  exactly as any other non-noise email would be
```
<!-- AC-ID: REQ-SB-87-US-03-AC-08 -->

### Scenario 9: Noise judgment fires only once, on a genuinely new conversation_id (added 2026-09-02)
```gherkin
Given a Thread that already exists for a given conversation_id, created
  because its first-seen message was judged not-noise
When a further email arrives on that same conversation_id whose own content,
  taken in isolation, would match the current noise definition (e.g. an
  automated reply-all notification landing inside an otherwise-real customer
  thread)
Then the classify-or-skip judgment is NOT re-run for this message — the
  classify-or-skip relay call is only ever invoked from the genuinely
  first-seen-conversation branch
  And the message is still captured into the existing Thread exactly as any
  other subsequent message would be — never silently dropped just because it
  would look noise-shaped on its own
```
<!-- AC-ID: REQ-SB-87-US-03-AC-09 -->

### Scenario 10: The noise definition is grounded against real, concrete seed examples (added 2026-09-02)
```gherkin
Given the noise definition has been derived or re-derived
When it is evaluated against real, live vault examples the operator has
  already confirmed noise-shaped (subjects: "Learning Assignment Changes
  Email Notification", "New Payslip available for viewing-download", "Core42
  Information Security Awareness Training", "Compass Alert- Failed API
  Calls", "CRM Enhancements - Weekly Release Summary")
Then each of these is classified as Noise
  And the definition's own real category is anything automated/broadcast
  (system/HR/security notifications, broadcast newsletters, event-
  announcement blasts) — broader than, and not limited to, literal
  meeting-invite .ics items, which are already filtered upstream via
  MessageClass before classification ever runs
```
<!-- AC-ID: REQ-SB-87-US-03-AC-10 -->

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
- **Blocks (added 2026-09-02, real cross-story sequencing, PRD point 8):**
  [[REQ-SB-87-US-02]] — specifically, **its own `T05`** (the real 100-message
  retrofit + live cron cutover) may not run until THIS story's own
  classification-writing capability exists and is verified working, since
  `T05`'s own retrofit must write a real classification value into every one
  of the 100 retrofitted messages' frontmatter (even where the ultimate
  decision is "keep everything," per the operator's own instruction). This is
  a genuine new dependency edge, not just an ordering preference —
  `/plan-tasks` should record it as a real `depends_on` from
  `REQ-SB-87-US-02-T05` onto whichever task of THIS story actually delivers
  working classification (not merely the noise-definition artifact or
  `hermes` relay plumbing on its own).
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
- **Sent items are never noise (added 2026-09-02, operator-locked):** the
  classify-or-skip judgment must never mark a `direction: "sent"` message as
  Noise, regardless of its own subject/body content — see Scenario 8. Real,
  concrete dependency: this Constraint can only be enforced once
  [[REQ-SB-87-US-02]]'s own Scenario 8 (the real `direction` field) exists on
  the data being classified.
- **Noise judgment is once-per-new-conversation, now an explicit locked rule
  (added 2026-09-02):** the classify-or-skip relay call fires ONLY from
  `ingest_email.py`'s own first-seen-conversation branch (`ADR-018`'s own
  already-resolved mechanism) — every subsequent message on an already-
  existing Thread is captured unconditionally, never re-judged, never
  skipped, regardless of how noise-shaped that individual message would look
  on its own. See Scenario 9. This restates `ADR-018`'s own mechanism as an
  explicit business-rule Constraint, per the operator's own direct
  confirmation — it does not change `ADR-018`'s own design.
- **Real seed criteria for the noise definition (added 2026-09-02,
  operator-confirmed, grounds but does not replace the LLM-derived
  definition per `ADR-018`):** anything automated/broadcast — system/HR/
  security notifications, broadcast newsletters, workshop/event-announcement
  blasts. NOT limited to literal meeting-invite `.ics` items (already
  filtered upstream via `MessageClass` before classification ever runs). Real
  seed example subjects, already in the vault, operator-confirmed
  noise-shaped: "Learning Assignment Changes Email Notification", "New
  Payslip available for viewing-download", "Core42 Information Security
  Awareness Training", "Compass Alert- Failed API Calls", "CRM Enhancements -
  Weekly Release Summary". See Scenario 10. These are seed examples/criteria
  for whatever derives the noise definition to be grounded against, not a
  hardcoded rule list substituting for the LLM-derived, structured-artifact
  design `ADR-018` already settled.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-87-US-03-T01 | backend | Noise-definition artifact + out-of-band derivation mechanism | `.second-brain/data/EmailCapture/noise_definition.json` (or equivalent), a new derivation script | `REQ-SB-87-US-03-T01-noise-definition-artifact-and-derivation.md` |
| REQ-SB-87-US-03-T02 | backend | Provision the dedicated classifier Hermes profile | `Hermes-Provisioning/profiles/<new classifier profile>/` (exact location decomposer/coder-level) | `REQ-SB-87-US-03-T02-classifier-hermes-profile.md` |
| REQ-SB-87-US-03-T03 | backend | Wire the classify-or-skip relay call into `ingest_email.py` | `Hermes-Provisioning/skills/vault-rebuild/email-thread-capture/scripts/ingest_email.py` | `REQ-SB-87-US-03-T03-wire-classify-or-skip-relay.md` |
| REQ-SB-87-US-03-T04 | backend | Report skip count through the orchestrators' JSON summary | `.../scripts/run_full_capture.py`, `.../scripts/run_delta_capture.py` | `REQ-SB-87-US-03-T04-report-skip-count.md` |
| REQ-SB-87-US-03-T05 | backend | Scratch-vault proving-phase verification + noise-definition retune pass + cutover | (verification + `--vault-path` cutover, no code changes) | `REQ-SB-87-US-03-T05-scratch-proving-and-cutover.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — n/a, no test-stack ADR Accepted yet for this Skill; verified via real scratch-vault CLI/direct-call runs, per this project's own manual→automated upgrade path
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

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

**Analyst pass (2026-09-02, real new business rules locked — PRD `REQ-SB-87`
point 7 + its own "Second expanded-scope raised-context pass," operator's own
direct answers, verbatim):** three new untagged Gherkin scenarios added
(Scenario 8: Sent items never noise; Scenario 9: noise judgment fires only
once, on a genuinely new `conversation_id`, now an explicit locked rule
rather than an implicit consequence; Scenario 10: the noise definition
grounded against 5 real, live, operator-confirmed seed example subjects) —
none decomposer-locked yet (no `AC-ID` tags — that remains the decomposer's
job at the next `/plan-tasks` pass). Constraints updated with the same three
rules. Dependencies updated with a new, real cross-story sequencing edge:
this story now also **Blocks** [[REQ-SB-87-US-02]]'s own `T05` (its real
100-message retrofit may not run until this story's own classification-
writing capability is built and verified, PRD point 8). `ADR-018`'s own
already-resolved architecture (the one-bounded-relay-call mechanism, the
noise-definition-as-structured-artifact design) is UNCHANGED — none of these
three additions re-litigate it, all are additive business-rule content layered
on top. No NEW MUST-FLAG trigger fired by this addition — these are concrete,
already-resolved-by-the-operator business rules (PRD's own verbatim quotes),
not open interpretation questions. `gate` stays `flagged` exactly as it
already was (the pre-existing `ADR-018` human-review requirement, trigger 3,
is unaffected and unresolved by this addition — see `REVIEW-QUEUE.md`).

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

**Architect pass (2026-09-02, Scenario 8/Scenario 9/Scenario 10
reviewed):** confirmed `ADR-018`'s already-Accepted mechanism needs no
adjustment and no new/superseding ADR for these three additions.
`ADR-018`'s own Decision locks the relay call to fire exactly once, from
`ingest_email.py`'s own `if existing_directory is None:` branch, per
newly-first-seen `conversation_id` — that is already, structurally,
"decided once, at first sight" (Scenario 3, already-locked `AC-03`);
Scenario 9 restates this as an explicit business rule but changes no
code-shape, no call-site, no invocation count — the mechanism the coder
builds is identical either way. Scenario 8 (Sent items never Noise) and
Scenario 10 (the five real seed-example subjects grounding "anything
automated/broadcast") are both real content that flows into the relay's
own request (the email's `direction` field, once `REQ-SB-87-US-02`
Scenario 8 delivers it; the seed examples/criteria the noise-definition
derivation is grounded against) and/or the classifier profile's own
prompt design — not a change to `ADR-018`'s own one-bounded-relay-call
mechanism, its subprocess dispatch technique, its structured-JSON-verdict
shape, or the noise-definition-as-persisted-vault-file design. This
matches the operator's own expectation exactly: refined BUSINESS RULES for
an already-designed mechanism, not a new structural/engine decision. One
concrete implementation note for the decomposer/coder, not an architecture
question: enforcing "Sent is never Noise" can be done as a deterministic
guard in `ingest_email.py` BEFORE the relay call is even made for a
Sent-sourced first message (skip the judgment entirely, classify directly)
or as an instruction inside the relay's own prompt — either satisfies
Scenario 8 without touching `ADR-018`'s mechanism; left open here as
`/plan-tasks`-level, not locked by this pass. No `architecture.md` edit
made — nothing structural changed. Existing Architecture scope
(§Capture-Time Classification & Noise-Skip, `ADR-018`, plus `ADR-017`'s
Thread template classification field) still fully bounds this story,
including its new Scenario 8/9/10.

gate: clear 2026-09-02 — this architect pass: no ADR touched/superseded,
no assumption made, no architecture.md edit needed for Scenario 8/9/10.
The story's own overall `gate: flagged` (pre-existing trigger-3, `ADR-018`
itself still awaiting human review alongside its tasks) is untouched and
unresolved by this pass.

**Decomposer pass (2026-09-02, Scenario 8/9/10 locked):** all three new
scenarios locked (`REQ-SB-87-US-03-AC-08`..`AC-10`), text unchanged from
the analyst's own already-precise wording. None of `T01`-`T05` are `Done`
yet (all still `Ready`, `SPRINT-084` not started) — per this pass's own
judgement, extending the existing, not-yet-built tasks directly is cleaner
than minting redundant siblings:
- `REQ-SB-87-US-03-AC-08` (Sent items are never Noise) → added to `T03`
  ("Wire the classify-or-skip relay call into `ingest_email.py`") — this is
  where the classify-or-skip decision itself is made, the natural home for
  a "never classify this input as Noise" guard. `T03` also gains a new
  `depends_on` edge onto `REQ-SB-87-US-02-T06` (the sibling story's own new
  task delivering the real `direction` field this guard needs — see that
  story's own Constraints, "this Constraint can only be enforced once
  `REQ-SB-87-US-02`'s own Scenario 8 ... exists on the data being
  classified").
- `REQ-SB-87-US-03-AC-09` (noise judgment fires only once, now explicit)
  → added to `T03` as well — its own existing Tests block already has an
  unlabeled step confirming "no second relay call is made" for a further
  message on an already-classified conversation; extended to explicitly
  engineer a message that WOULD look noise-shaped on its own, per
  Scenario 9's own wording, and tagged `AC-09`.
- `REQ-SB-87-US-03-AC-10` (five real seed-example subjects) → added to
  `T02` ("Provision the dedicated Capture-classifier Hermes profile") —
  the AC's own assertion ("each of these is classified as Noise") is only
  actually OBSERVABLE once a real classifier can return a verdict; `T02`'s
  own Tests block already issues real relay calls and checks `is_noise`
  values, the natural place to add the five named subjects as a concrete
  positive-case batch, cross-checked against `T01`'s own persisted
  definition content for the "automated/broadcast" category framing.
  `T01` itself was considered (it derives the definition's own content)
  but was not the right home for THIS AC specifically, since "classified as
  Noise" cannot be observed without T02's own classifier existing —
  `T01`'s own Tests are updated instead with a lighter, complementary,
  unlabeled step confirming the derivation sample/guidance for its next
  (re)run includes these five real subjects as seed content, so the
  definition it produces is actually grounded against them in the first
  place, not just checked after the fact.

Every locked AC (including the 3 new ones) has at least one AC-tagged
verification step; `depends_on` (including the two new cross-story edges
below) is acyclic. `status` stays `Ready` (already past `Draft`, unchanged
by this addition) — all 5 tasks stay `Ready`. `gate` left untouched
(`flagged`, `ADR-018`'s own pre-existing human-review requirement,
unaffected by this addition).

**Real cross-story dependency edges recorded (2026-09-02):**
1. `REQ-SB-87-US-03-T03`'s own `depends_on` updated to
   `[REQ-SB-87-US-03-T02, REQ-SB-87-US-02-T01, REQ-SB-87-US-02-T06]` — the
   new edge onto `REQ-SB-87-US-02-T06` is required for the new `AC-08`
   guard (needs the real `direction` field `T06` delivers).
2. Per this story's own already-disclosed 2026-09-02 Dependencies entry
   (PRD point 8): `REQ-SB-87-US-02-T05` (real-vault retrofit + cutover) is
   blocked on THIS story's own classification-writing capability existing
   and being verified working. Reading this story's own 5 task files
   directly: `T03` is the task that both builds AND individually,
   live-verifies that mechanism (its own `[REQ-SB-87-US-03-AC-02]` Tests
   step already confirms a real classification value lands on a Thread's
   frontmatter) — `T04` only adds JSON-summary reporting, `T05` is a
   combined proving/retune pass, neither is where the capability first
   exists. `REQ-SB-87-US-02-T05`'s own `depends_on` frontmatter updated
   accordingly (see that task file). This is a genuine cross-sprint edge
   (`SPRINT-084` → `SPRINT-083`, in this direction) — already disclosed as
   expected in both stories' own Dependencies sections, not a new
   discovery this pass; left to `/plan-sprints`'s own `depends_on_sprints`
   handling.

**Coder pass (2026-09-02, `T01` built and verified `Done`):** the
noise-definition artifact (`.second-brain/data/EmailCapture/
noise_definition.json`, under the real vault) and its own out-of-band
derivation script (`derive_noise_definition.py`) are real and live.
`[REQ-SB-87-US-03-AC-04]` verified live in full — two real derivation
runs against the real Hermes CLI and the real vault, the persisted
artifact grounded in the operator's exact 5 locked seed subjects, framed
as "anything automated/broadcast" with no mention of meeting invites,
and confirmed genuinely re-derivable (not frozen) against a second,
different real sample. `status` → `In Progress` (this story's first task
is `Done`; `T02`-`T05` remain `Ready`). `gate` stays `flagged` — the
pre-existing `ADR-018` human-review flag is unresolved and unaffected by
this pass; `T01` itself also carries its OWN task-level `gate: flagged`
for 3 disclosed scope-internal judgement calls (derivation relay target
profile, the `definition`'s own JSON schema, and building `T01` ahead of
`SPRINT-084`'s own formal `depends_on_sprints: [SPRINT-083]` start gate
under the launching agent's own explicit instruction) — see `T01`'s own
Implementation Log and the new `REVIEW-QUEUE.md` entry. `MEMORY.md`
updated with 1 new Pattern (the artifact's real vault-only location +
default-profile-is-sufficient-for-derivation finding) and 1 new
Constraint (a sandboxed Bash-tool session's `python`/`py` PATH entries
can be a non-functional Microsoft Store stub even when a real Python is
installed — resolve via `py -0p`).

**Coder pass (2026-09-02, `T02` built and verified `Done`):** the real,
live `email-capture-classifier` Hermes profile (`ADR-018`'s anticipated
one-shot classify-or-skip relay target) is provisioned, structurally
stripped of every skill and toolset so "no vault-write capability, no
tool-calling loop" is a real property, not just prompt discipline, and
authored with a `SOUL.md` that reads the persisted noise definition +
one email's content and replies with exactly one JSON verdict.
`[REQ-SB-87-US-03-AC-10]` and `[REQ-SB-87-US-03-AC-02]` (this story's own
two ACs mapped to `T02`) both verified live in full — 7 real relay
calls, all 5 real seed subjects correctly judged Noise, a real
content-rich non-noise Thread correctly judged not-Noise with a real,
accurate `classification` (after a live-discovered `SOUL.md` widening to
pass real recipients/participants, not sender-only — disclosed for
`T03`'s own relay-call construction to account for). `status` stays `In
Progress` (`T03`-`T05` remain `Ready`). `gate` stays `flagged` — the
pre-existing `ADR-018` human-review flag is unresolved and unaffected;
`T02` itself also carries its OWN task-level `gate: flagged` for 4
disclosed scope-internal judgement calls (structural toolset/skill
stripping beyond a plain clone, the lowercase `classification` value
choice, the SOUL.md recipients/participants widening, and leaving
`reasoning_effort` at `medium`) — see `T02`'s own Implementation Log and
the new `REVIEW-QUEUE.md` entry.

**Coder pass (2026-09-02, `T03` built and verified `Done`):** the
classify-or-skip relay call is now live inside `ingest_email.py`'s own
first-seen-conversation branch (`ADR-018`). Six of this story's own
locked ACs verified live against a fresh scratch vault and the real,
installed classifier profile — `[REQ-SB-87-US-03-AC-01]` (a genuinely
new noise conversation left zero vault trace, independently confirmed
via a directory listing), `[REQ-SB-87-US-03-AC-02]` (a genuinely new
signal conversation captured and correctly classified `"customer"`),
`[REQ-SB-87-US-03-AC-03]`/`[REQ-SB-87-US-03-AC-09]` (a further,
deliberately noise-shaped message on an already-classified conversation
was captured unconditionally with a confirmed zero-relay-call count, via
a real subprocess-call-count wrap, not just an end-state inference),
`[REQ-SB-87-US-03-AC-06]` (a real Inbox+Sent pair combined into one
Thread, the Sent item never excluded), `[REQ-SB-87-US-03-AC-08]` (a
first-seen Sent message with deliberately noise-shaped content was never
skipped and got a real classification — enforced structurally on the
CALLER's side, not by trusting the classifier's own SOUL.md safety net).
An engineered relay failure (scoped, reverted monkeypatch) raised as
designed with no Thread created, and a real, unpatched retry of the same
conversation then succeeded, confirming the natural-retry degrade
default. `status` stays `In Progress` (`T04`/`T05` remain `Ready`,
`T05`'s own real-vault cutover still explicitly out of this task's
scope). `gate` stays `flagged` — the pre-existing `ADR-018` human-review
flag is unresolved and unaffected; `T03` itself also carries its OWN
task-level `gate: flagged` for 5 disclosed scope-internal judgement
calls (the Sent-guard mechanism choice, a real `direction` value
doc/reality mismatch found between `T02`'s deployed `SOUL.md` and `T06`'s
real field, a duplicated JSON-extraction helper, the relay's own
question-text wording, and treating an invalid/missing classification as
a relay failure) — see `T03`'s own Implementation Log and the new
`REVIEW-QUEUE.md` entry.

**Coder pass (2026-09-02, `T04` built and verified `Done`):** both
orchestrators (`run_full_capture.py`/`run_delta_capture.py`) now report a
real, aggregated `skipped_as_noise` count in their own final JSON summary
and each per-page `progress` entry, mirroring the EXACT existing
`threads_created`/`messages_created` aggregation shape — zero other
orchestration logic changed (confirmed via `git diff`).
`[REQ-SB-87-US-03-AC-07]` verified live on both scripts against their own
real, unmodified `main()` (a scoped, disclosed monkeypatch of only the
`run_script` subprocess boundary, per this project's own established
in-process-monkeypatch technique — the classify-or-skip judgment itself
is `T03`'s scope, not re-tested here), with a real scratch `VAULT_PATH`
across two pages engineered with genuine noise-skips, a genuine new
capture, and a reply into an already-existing Thread: both scripts'
final summaries correctly reported `skipped_as_noise: 2` distinct from
`threads_created: 1`/`messages_created: 2`, and each page's own
`skipped_as_noise` value summed correctly to the total. `status` stays
`In Progress` (`T05` remains `Ready`, the real-vault cutover). `gate`
stays `flagged` — the pre-existing `ADR-018` human-review flag is
unresolved and unaffected by this pass; `T04` itself carries `gate:
clear` (no scope-internal judgement call beyond the disclosed, already-
precedented verification technique). No `MEMORY.md` update — a
mechanical mirror of an already-established pattern, no new decision.

**Coder pass (2026-09-02, `T05` built and verified `Done` — story closes):**
scratch-vault-only closing proving pass, per the launching agent's own
explicit boundary (the real-vault retrofit/cutover, owned by the sibling
`REQ-SB-87-US-02-T05`, was explicitly held — not built, not touched).
`[REQ-SB-87-US-03-AC-04]`/`[REQ-SB-87-US-03-AC-05]`/`[REQ-SB-87-US-03-
AC-06]` verified live, plus a closing, combined real run re-verifying all
10 currently-locked ACs (`AC-01`..`AC-10`) together: a real, unmodified
~100-email/12-day scratch sample (55 unique conversations) processed with
ZERO errors — 45 real Threads created (each with exactly one valid
`classification`, confirmed both via returned JSON and a direct,
independent on-disk directory count), 10 correctly skipped as noise with
literal zero vault trace, all 12 real Sent messages correctly never
skipped, every repeat message on an already-classified conversation
triggering zero relay calls. A real, disclosed reconstruction of a
"pre-`T03`" baseline (in-process monkeypatch of `_classify_or_skip`, no
literal pre-change git commit exists to diff against) confirmed ZERO
Sent+Inbox-combining regressions across all 45 non-noise conversations,
side-by-side against the SAME byte-identical sample. A SEPARATE, real,
fully-unmocked pass through the TRUE production entry point
(`run_delta_capture.py`, genuine subprocess-to-subprocess dispatch, never
direct-imported) against a freshly bounded scratch vault independently
reproduced 5 of the same 45 Thread-creation decisions and 2 correct
noise-skips, with an accurate `skipped_as_noise: 2` written to a real
`SUMMARY_PATH` JSON file — the first fully-unmocked, orchestrator-level
proof of the whole chain (`T03` used direct import, `T04` mocked the
`ingest_email.py` subprocess boundary itself). The real vault's own
already-persisted `noise_definition.json` (`T01`'s work) was found to
need NO retune — zero apparent false positives across a genuinely unseen
real sample, including several live, unplanned recurrences of its own
original seed content, all correctly caught; the `AC-05` retune-CYCLE
mechanism itself was proven separately, entirely inside a scratch vault.
One real, disclosed finding RECONFIRMED (not new — already open at
`REVIEW-QUEUE.md` → `REQ-SB-87-US-02-T06`): the real orchestrators still
don't forward `direction` to `ingest_email.py`, so `AC-08`'s guard isn't
yet reliably reachable through the live cron path specifically (though
fully proven correct at the `ingest_email()` function level) — not fixed
here (outside this task's own `## Files to Modify`), tracked for
`REQ-SB-87-US-02-T05`'s own future cutover pass. `status` → `Done` (all
5 tasks `T01`-`T05` Done, all 10 locked ACs verified live). `gate` stays
`flagged` — the pre-existing `ADR-018` human-review flag (trigger-3) is a
standing architecture-level flag a human must still resolve independently;
story completion does not clear it. `T05` itself carries `gate: clear` (no
new scope-internal judgement call beyond established, already-precedented
verification techniques — see its own Implementation Log). `MEMORY.md`:
2 new entries (a Constraint on Windows `subprocess.run` PATH/extension
resolution; a Pattern on reconstructing a pre-change regression baseline
via in-process monkeypatch when no literal git commit exists).
`SPRINT-084` stays `In Progress` — its sibling story `REQ-SB-87-US-05`
remains `Ready`, untouched by this task.
