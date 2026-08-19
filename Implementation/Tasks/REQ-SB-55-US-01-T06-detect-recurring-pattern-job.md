---
id: REQ-SB-55-US-01-T06
title: Detect-Recurring-Pattern branch Job — Pending Approval proposing a new Pipeline, wizard-seed payload, never builds it
parent_story: REQ-SB-55-US-01
requirement_id: REQ-SB-55
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-043 created) — carried from the parent story; the human reviews ADR-043 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: [REQ-SB-55-US-01-T02, REQ-SB-55-US-01-T04]
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-55-US-01-T06 — `Detect-Recurring-Pattern` branch Job

## Parent Story

- Story: [[REQ-SB-55-US-01]] — `../UserStories/REQ-SB-55-US-01-email-capture-and-threading-pipeline.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-55 *Email Capture & Threading Pipeline*

---

## Objective

Add `detect_recurring_pattern(email, classification) -> dict | None` to `email_classification.py` — this Pipeline's `Detect-Recurring-Pattern` branch Job: when `Classify`'s (`T02`) `recurring_candidate` outcome fires, creates a Pending Approval proposing a NEW standing Pipeline, seeded from the triggering email — a payload shaped to be usable as Agent Creation Wizard input (a suggested name, `type: "worker"`, and a purpose/description drawn from the email). The proposed Pipeline is NEVER built or executed by this task, on ANY code path, including Approve — approving only acknowledges the proposal; actually creating the new agent/Pipeline is the operator's own separate, manual completion of the existing wizard (`REQ-SB-37`, out of this story's scope, per its own Non-Goals).

---

## Starting State → End State

**Before / Inputs:**
- `T02`'s `classify_captured_email` returns `recurring_candidate: bool`.
- `T04`'s router generalization (`outcome_message = result.get("message") or f"Approved — filed at {result['path']}."`) already lands in `pending_approvals_router.py` — this task reuses it rather than re-editing that line a second time.
- `agents_router.py`'s `CreateAgentBody` shape (`name`, `type`, `domain`/`purpose`, `trigger`) is the real Agent Creation Wizard's own input contract — this task's payload should be shaped compatibly with it (`name`, `type: "worker"`, a `purpose`-style description), even though no code in this story actually calls `POST /agents` with it.

**After / Outputs:**
- `detect_recurring_pattern(email, classification) -> dict | None` exists: returns `None` immediately if `classification["recurring_candidate"]` is falsy. Otherwise, creates one Pending Approval (`agent_id="email-capture-pipeline"`, `trigger="direct"`, `action_id="propose_recurring_pipeline"`, `payload={"name": <suggested Pipeline/Agent name>, "type": "worker", "purpose": <a purpose/description derived from the triggering email — subject/customer/kind>, "seed_source": {"subject": email["subject"], "sender": ..., "received": ...}}`).
- `pending_approvals_router.py` gains `finalize_recurring_pipeline_proposal(payload) -> dict` — a deliberately lightweight acknowledgment (does NOT call `agent_registry.create_agent` or any agent-creation code path on any branch), returning `{"message": "Approved — seed data ready. Open the Agent Creation Wizard to complete the new Pipeline."}` — wired into `_APPROVAL_HANDLERS["propose_recurring_pipeline"]`.

---

## Files to Modify

- `src/backend/app/business/email_classification.py` — add `detect_recurring_pattern`.
- `src/backend/app/api/pending_approvals_router.py` — add `finalize_recurring_pipeline_proposal`, register it in `_APPROVAL_HANDLERS`.

---

## Constraints

- Inherits from parent story: **the proposed Pipeline is NEVER built or executed automatically** — no code path in this task (Job creation OR Approve-time finalize) may call `agent_registry.create_agent`, write any new Agent-tier registry entry, or otherwise instantiate the proposed Pipeline. This is a hard requirement, not a nice-to-have (Scenario 5's own explicit "not built or executed automatically" clause).
- `trigger="direct"`, never `"background"` — same reasoning as `T04` (multiple distinct proposals can legitimately coexist across one pipeline tick; `"background"`'s idempotency guard would silently collapse them).
- The detection mechanism itself stays wherever `T02` put it (`compass_client.classify_email`'s own extended prompt) — this task only ACTS on `recurring_candidate`, it must not duplicate or re-implement any detection logic of its own.
- The seed payload must be genuinely derived FROM the triggering email (subject/sender/customer/kind), never a generic/empty placeholder — "seeded from the triggering email" is a locked-AC requirement (Scenario 5), not decorative.
- Must remain a plain, LangGraph-ignorant function — ordinary Python data in/out.

---

## Tests

**Manual verification steps:**
1. **[REQ-SB-55-US-01-AC-05]** Against a throwaway scratch vault, call `detect_recurring_pattern(email, classification)` where `classification["recurring_candidate"]` is `True` (using a real structured/repeating test email, e.g. reusing `T02`'s own test fixture). Confirm exactly one new Pending Approval now exists, `action_id="propose_recurring_pipeline"`, with a payload whose `name`/`purpose` genuinely reflect the triggering email's own subject/customer/kind (not a generic placeholder), `type: "worker"`. Confirm — by direct code inspection of both this function AND `finalize_recurring_pipeline_proposal` — that NEITHER calls `agent_registry.create_agent` (or any agent-creation code path) anywhere. Call the Approve endpoint on this record — confirm the outcome message acknowledges the proposal without creating any new agent (`agent_registry.list_agents()`'s own count is unchanged before/after Approve).
2. Call `detect_recurring_pattern(email, classification)` where `classification["recurring_candidate"]` is `False` (an ordinary email) — confirm it returns `None` and creates NO Pending Approval.
3. **[REQ-SB-55-US-01-AC-06]** Repeat step 1 with a SECOND, structurally different test email from an unrelated customer (the same two fixtures `T02`'s own Test step 2 used) — confirm `detect_recurring_pattern` fires correctly for both, using the SAME code path (no branch keyed on either test email's own customer name or format), each producing its own distinct, correctly-seeded Pending Approval.
4. Confirm both Pending Approval records use `trigger="direct"` (read directly).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-05** (Scenario 5) — a recurring-candidate email produces a Pending Approval proposing a new Pipeline, seeded from the real triggering email; nothing builds/executes it on any code path, including Approve.
- [x] **AC-06** (Scenario 6, the Job-firing half) — the same mechanism correctly fires for two structurally different test emails from unrelated customers.
- [x] `trigger="direct"` used, never `"background"`.
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend wizard pre-fill wiring — the parent story's own Affected Screens is `None`; this task only produces and stores the seed payload (viewable via the already-existing `GET /pending-approvals/{id}`), it does not open or drive the Agent Creation Wizard UI.
- Actually building the proposed Pipeline through the wizard — the operator's own separate, manual, runtime action (`REQ-SB-37`, already `Done`), explicitly out of this story's own Non-Goals.
- The conditional graph edge deciding when `detect_recurring_pattern` runs — `T07`'s own job (this function's own `recurring_candidate`-falsy no-op is a defensive guard, not the primary gating mechanism).

---

## Context / Notes

Full reasoning: `Implementation/Architecture/ADR.md` → `ADR-043` points 3, 4, 5; `Implementation/Architecture/architecture.md` → "Email Capture & Threading Pipeline — First Concrete Pipeline". The parent story's own Notes ("Prototype parity") already confirm the Agent Creation Wizard needs no new screen for this — this task's own scope stops at producing a well-shaped seed payload, per the parent story's own Non-Goals ("Building whatever new Pipeline Detect-Recurring-Pattern proposes... not anticipated here").

**Why `finalize_recurring_pipeline_proposal` does almost nothing:** re-reading Scenario 5's own two Then-clauses together — "a Pending Approval is created... pre-filled into the existing Agent Creation Wizard" AND "the proposed Pipeline is NOT built or executed automatically... until the operator explicitly approves AND completes the wizard" — describes TWO separate human steps (approve the proposal; separately, later, manually complete the wizard), not one. Approving the Pending Approval is deliberately not the same action as completing the wizard.

---

## Implementation Log

**2026-08-16, coder pass.**

Two files edited, exactly as scoped under `## Files to Modify`:

- `src/backend/app/business/email_classification.py` — added
  `detect_recurring_pattern(email: dict, classification: dict) -> dict | None`
  and `finalize_recurring_pipeline_proposal(payload: dict) -> dict`, placed
  directly after `finalize_thread_project_routing` (before
  `classify_recent_emails`). `detect_recurring_pattern` returns `None`
  immediately when `classification.get("recurring_candidate")` is falsy —
  the detection signal itself lives entirely in `T02`
  (`compass_client.classify_email`'s own extended prompt); this function
  never re-implements or duplicates any detection logic. Otherwise builds a
  `suggested_name` (`f"{customer} {kind} Recurring Pipeline"`) and a
  `purpose` string naming the real customer/sender/subject/kind — both
  genuinely computed from `classification`/`email`'s own real values, never
  a generic placeholder — and calls
  `pending_approval_registry.create_pending_approval(agent_id=
  "email-capture-pipeline", trigger="direct", action_id=
  "propose_recurring_pipeline", payload={"name", "type": "worker",
  "purpose", "seed_source": {"subject", "sender", "received"}})`.
  `finalize_recurring_pipeline_proposal` accepts `payload` only to match
  every other `_APPROVAL_HANDLERS` entry's own call shape
  (`_APPROVAL_HANDLERS[action_id](record["payload"])`) but never reads it —
  returns exactly `{"message": "Approved — seed data ready. Open the Agent
  Creation Wizard to complete the new Pipeline."}`, with NO call to
  `agent_registry.create_agent` or any other agent-creation code path on
  any branch. Reused `pending_approval_registry`/`vault_writer` imports
  already present in this file — no new imports needed.
- `src/backend/app/api/pending_approvals_router.py` — imported
  `finalize_recurring_pipeline_proposal` from `email_classification.py`
  (alongside the already-imported `finalize_thread_project_routing`/
  `run_capture_for_agent`) and registered it as
  `_APPROVAL_HANDLERS["propose_recurring_pipeline"]`. Reused `T04`'s own
  `outcome_message = result.get("message") or f"Approved — filed at
  {result['path']}."` generalization directly — no second edit to that
  line, since `finalize_recurring_pipeline_proposal`'s own `"message"` key
  is always truthy and short-circuits the fallback branch (which would
  otherwise `KeyError` on the missing `"path"` key this handler
  intentionally never returns). No other line in this file touched.

No scope-internal judgement calls beyond the payload's own exact wording
(`suggested_name`/`purpose` construction) — the task file's own `##
Starting State → End State` and `## Constraints` sections fully resolved
the approval-outcome contract ("approving only acknowledges the
proposal... the operator's own separate, manual completion of the
existing wizard") before any code was written, so no genuine ambiguity
remained to escalate on. No out-of-scope files touched; `ast.parse()` of
both modified files confirmed clean.

**Verification (manual mode — no automated test stack exists yet for this
backend; real backend `.venv`, `VAULT_PATH` env-overridden to a
`tempfile.mkdtemp()` scratch vault, the real configured vault never
touched; real, configured Compass Provider — no HTTP mocking — per this
story's own established `T01`–`T05` protocol. Script + full transcript
kept in this session's own scratchpad, not committed; both fixtures reused
verbatim from `T02`'s own Test steps 1/2, re-classified live via
`classify_captured_email` rather than hand-constructed classification
dicts, so the whole `Classify → Detect-Recurring-Pattern` chain was
exercised, not just this Job in isolation):**

1. **[REQ-SB-55-US-01-AC-05]** Classified a real "Weekly Usage Report —
   Acme Corp — Period: 2026-W33" test email live via
   `classify_captured_email` — observed `recurring_candidate: True`.
   Called `detect_recurring_pattern(email, classification)` — observed
   exactly one new Pending Approval (`before=0`, `after=1` via
   `pending_approval_registry.list_pending_approvals(status="pending")`),
   `action_id == "propose_recurring_pipeline"`, `trigger == "direct"`,
   payload `{"name": "Acme Corp Reports Recurring Pipeline", "type":
   "worker", "purpose": "Proposed after a recurring, structured pattern
   was detected in an email from Acme Corp (reports@acmecorp.com) --
   subject \"Weekly Usage Report — Acme Corp — Period: 2026-W33\",
   classified as Reports. Automates this recurring artifact instead of
   manually re-filing it each time it recurs.", "seed_source": {"subject":
   ..., "sender": ..., "received": ...}}` — `name`/`purpose` genuinely
   reflect the real triggering email's own subject/customer/kind, not a
   placeholder. Confirmed by direct `inspect.getsource()` reading of BOTH
   `detect_recurring_pattern` and `finalize_recurring_pipeline_proposal`
   that neither contains an actual `create_agent(` call anywhere (only
   prose mentions of the name inside docstrings, which is not a call).
   Read `agent_registry.list_agents()` before Approve (`7` entries), then
   called `pending_approvals_router.approve_pending_approval(record_id)`
   directly — observed the outcome message recorded verbatim into
   `email-capture-pipeline`'s own agent history
   (`"Approved — seed data ready. Open the Agent Creation Wizard to
   complete the new Pipeline."`), acknowledging the proposal without
   creating any new agent. Re-read `agent_registry.list_agents()` after
   Approve — still `7` entries, unchanged. **PASS.**
2. Classified an ordinary "Lunch tomorrow?" conversational test email live
   — observed `recurring_candidate: False`. Called
   `detect_recurring_pattern(email, classification)` — returned `None`; a
   before/after `list_pending_approvals(status="pending")` count confirmed
   NO new Pending Approval was created. **PASS.**
3. **[REQ-SB-55-US-01-AC-06]** Classified a second, structurally DIFFERENT
   test email live — `T02`'s own "INVOICE #4471 — Zenith Manufacturing
   Ltd." fixture, an unrelated fictitious customer with an invoice-shaped
   layout, not a usage-report layout — observed `recurring_candidate:
   True`. Called `detect_recurring_pattern` — produced a second, distinct
   Pending Approval (`id` different from step 1's), payload `{"name":
   "Zenith Manufacturing Ltd. Invoices Recurring Pipeline", "purpose":
   "...email from Zenith Manufacturing Ltd. (billing@zenithmfg.example)
   -- subject \"INVOICE #4471 — Zenith Manufacturing Ltd.\", classified as
   Invoices...", ...}` — genuinely reflects THIS email's own real
   subject/customer/kind, confirming the same code path
   (`detect_recurring_pattern` has no branch keyed on either fixture's own
   customer name or format) correctly fires for both. **PASS.**
4. Confirmed directly from both created records (steps 1/3 above) that
   `trigger == "direct"` on both — never `"background"`. **PASS.**

**Acceptance criteria verified:**

- **AC-05** (Scenario 5) — **Verified**, step 1 above (Pending Approval
  created, genuinely seeded, Approve confirmed to acknowledge only —
  never build/execute the proposed Pipeline, `agent_registry.list_agents()`
  count unchanged).
- **AC-06** (Scenario 6, the Job-firing half) — **Verified**, step 3 above
  (same mechanism fires correctly for two structurally different test
  emails from unrelated customers, no format-/customer-specific branch).
- `trigger="direct"` used, never `"background"` — **Verified**, step 4.

No `ESCALATIONS.md` entry — nothing in this pass contradicts an `Accepted`
ADR, the PRD, or a `MEMORY.md` constraint; the task file's own Context/
Notes fully resolved the approval-outcome contract ambiguity flagged in
this task's own launch instructions before any code was written. No new
`REVIEW-QUEUE.md` entry either — this task's already-standing `gate:
flagged` (trigger-3, `ADR-043`) already carries it into the existing
human-review pass.
