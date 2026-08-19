---
id: REQ-SB-55-US-01-T02
title: Classify Job extension — general/structural recurring-pattern-candidate outcome
parent_story: REQ-SB-55-US-01
requirement_id: REQ-SB-55
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-043 created) — carried from the parent story; the human reviews ADR-043 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: []
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-55-US-01-T02 — `Classify` Job extension

## Parent Story

- Story: [[REQ-SB-55-US-01]] — `../UserStories/REQ-SB-55-US-01-email-capture-and-threading-pipeline.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-55 *Email Capture & Threading Pipeline*

---

## Objective

Extend the existing `compass_client.classify_email` call with one new outcome — `recurring_candidate: bool` — a GENERAL, structural signal ("does this look like a recurring, structured artifact — an invoice, a weekly export, a consumption report, anything else patterned and repeating — regardless of which specific format"), never a rule hardcoded to one known customer's format (Scenario 6/`AC-06`, the operator's own explicit reusability requirement). Wrap the extended call in one new plain function in `email_classification.py`, `classify_captured_email(email, known_customers, known_kinds) -> dict`, this Pipeline's own `Classify` Job — independently callable/testable outside any LangGraph context, taking/returning ordinary Python data (`ADR-043` point 1).

---

## Starting State → End State

**Before / Inputs:**
- `compass_client.classify_email(subject, sender, body, known_customers, known_kinds) -> {"customer", "kind", "confidence"}` — real, already-shipped, used today by `classify_recent_emails`.
- No recurring-pattern signal exists anywhere in this codebase.

**After / Outputs:**
- `compass_client.classify_email`'s own prompt/response-parsing gains one additive field: `recurring_candidate: bool` (default `False` if the model omits it, mirroring the existing `customer`/`kind` fallback-on-missing convention) — the SAME single Compass call, no second/parallel classification chain (parent story's own Constraint).
- `email_classification.classify_captured_email(email, known_customers, known_kinds) -> dict` exists, returning `{"customer", "kind", "confidence", "recurring_candidate"}` — a thin, LangGraph-ignorant wrapper the Pipeline's `Classify` node (`T07`) calls; also directly callable/testable on its own.

---

## Files to Modify

- `src/backend/app/data_access/compass_client.py` — extend `classify_email`'s own prompt text with the new axis, extend its own JSON response-object description, extend its own response-parsing dict with `"recurring_candidate": bool(parsed.get("recurring_candidate", False))`.
- `src/backend/app/business/email_classification.py` — add `classify_captured_email(email: dict, known_customers: list[str], known_kinds: list[str]) -> dict`, a thin wrapper around `compass_client.classify_email(subject=email["subject"], sender=email["sender_email"] or email["sender_name"], body=email["body"], known_customers=known_customers, known_kinds=known_kinds)` returning the classification dict unchanged (propagates `compass_client.CompassError` — the caller, `T07`'s pipeline assembly, decides how to handle a classification failure for one email, mirroring `classify_recent_emails`'s own existing per-email `try/except`+skip pattern).

---

## Constraints

- Inherits from parent story: **no second, independent Compass/classification call chain** — this is the SAME `classify_email` call, extended, never a separate new Compass call for the recurring-pattern signal.
- The new prompt language must ask Compass to reason structurally/generally (patterns, repetition, structured layout) — never name a specific customer, format, or example document as the detection rule itself. A one- or two-sentence general illustrative example (e.g. "an invoice, a weekly usage/consumption report, an automated recurring export") is acceptable as ILLUSTRATION of the general category, not as the actual matching rule.
- `classify_email`'s existing `customer`/`kind`/`confidence` fields, their own fallback-on-missing behavior, and every existing caller's contract (`email_classification.py`'s original inline call, if any callers remain after `T08`'s rewiring) must be preserved unchanged — this is an ADDITIVE field, not a reshaping of the function's return contract.
- `classify_captured_email` must never itself write to the vault or create a Pending Approval — purely a classification read, matching the Job-tier "plain function, ordinary data in/out" contract (`ADR-043` point 1).

---

## Tests

**Manual verification steps:**
1. Against the real backend `.venv`, real Compass Provider: call `compass_client.classify_email(...)` with a deliberately structured/repeating test email body (e.g. a synthetic "Weekly Usage Report — Customer X — Period: 2026-W33" with a clear tabular/structured layout) — confirm the returned dict includes `recurring_candidate: True`.
2. **[REQ-SB-55-US-01-AC-06]** Call `compass_client.classify_email(...)` a second time with a DIFFERENT structured/repeating test email, from an unrelated fictitious customer, using a genuinely different structural pattern (e.g. an invoice-shaped layout rather than a usage-report layout) — confirm `recurring_candidate: True` fires for this one too, via the SAME prompt/mechanism (no code branch keyed on either test email's own customer name or specific format), directly confirming the detection is structural/general, not hardcoded to one known shape.
3. Call `compass_client.classify_email(...)` with an ordinary, one-off conversational email (e.g. "Hey, are we still on for lunch tomorrow?") — confirm `recurring_candidate: False`.
4. Call `email_classification.classify_captured_email(email, known_customers, known_kinds)` directly with a real or synthetic email dict — confirm it returns the same 4-key dict shape, and confirm (by direct reading, not just live behavior) it makes exactly one `compass_client.classify_email` call, never a second Compass call of any kind.
5. Regression check: confirm the existing `customer`/`kind`/`confidence` fields still classify correctly for an ordinary test email exactly as before this change (no regression from the prompt edit).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-06** (Scenario 6, partial — the underlying detection mechanism) — the SAME general, structural prompt/mechanism correctly flags two different structured/repeating test emails from two unrelated customers with genuinely different formats; no format- or customer-specific code branch exists.
- [x] `recurring_candidate` is additive on `classify_email`'s return contract — every existing field/fallback behavior unchanged.
- [x] `classify_captured_email` makes exactly one Compass call per invocation.
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Actually acting on `recurring_candidate` (creating a Pending Approval, proposing a Pipeline) — `T06`'s own job (`Detect-Recurring-Pattern`).
- The "existing Thread vs. new Thread" outcome the parent story's own Context loosely attributes to `Classify` — resolved structurally by `Thread-Match/Merge`'s own `thread_note_exists(conversation_id)` check (`T03`), not an LLM outcome; no code for this belongs in this task.
- Wiring this function as a graph node — `T07`'s own job.

---

## Context / Notes

Full reasoning: `Implementation/Architecture/ADR.md` → `ADR-043` point 1 ("`Classify` extends the existing `compass_client.classify_email` call with two new outcomes"); `Implementation/Architecture/architecture.md` → "Email Capture & Threading Pipeline — First Concrete Pipeline". The parent story's own Constraint ("Detect-Recurring-Pattern must be general/structural, never a rule hardcoded to one customer's known format") is a hard requirement from the operator's own reusability framing, not a nice-to-have — Test step 2 above is this task's own direct proof of it.

---

## Implementation Log

Implemented exactly the two edits scoped under `## Files to Modify`:

- `src/backend/app/data_access/compass_client.py::classify_email` — the
  prompt now asks for a third JSON axis, `recurring_candidate: <true/false>`,
  worded structurally/generally ("a repeating, patterned layout — consistent
  structure, labeled fields, tabular or itemized data — rather than a
  one-off free-form conversation"), with three general illustrative
  examples (invoice, weekly usage/consumption report, automated recurring
  export) explicitly framed as "examples of the shape to recognize, not an
  exhaustive or matching list" — never a rule naming a specific customer or
  document format. The response-parsing dict gained one additive key,
  `"recurring_candidate": bool(parsed.get("recurring_candidate", False))`,
  mirroring the existing `customer`/`kind` fallback-on-missing convention.
  `customer`/`kind`/`confidence` keys/fallbacks are byte-unchanged.
- `src/backend/app/business/email_classification.py` — added
  `classify_captured_email(email, known_customers, known_kinds) -> dict`, a
  thin wrapper that calls `compass_client.classify_email` exactly once with
  the same argument mapping `classify_recent_emails` already uses
  (`subject`, `sender=email["sender_email"] or email["sender_name"]`,
  `body`, `known_customers`, `known_kinds`) and returns the classification
  dict unchanged. No vault write, no Pending Approval — a pure read, per
  this task's own Constraint.

**Verification (manual mode — no automated test stack exists yet for this
backend):** ran all 5 steps live against the real backend `.venv` and the
real, configured Compass Provider (no mocking of the HTTP call itself) via
a throwaway scratch script, then deleted it.

1. `compass_client.classify_email(...)` with a synthetic "Weekly Usage
   Report — Acme Corp — Period: 2026-W33" (clear tabular/structured
   layout) → observed `{'customer': 'Acme Corp', 'kind': 'Reports',
   'confidence': 0.99, 'recurring_candidate': True}`. **Pass.**
2. **[REQ-SB-55-US-01-AC-06]** Second, structurally DIFFERENT test email —
   an invoice-shaped layout ("INVOICE", line items, subtotal/tax/total) from
   an unrelated fictitious customer ("Zenith Manufacturing Ltd.", not in
   the `known_customers` list passed for either call) → observed
   `{'customer': 'Zenith Manufacturing', 'kind': 'Invoices', 'confidence':
   0.86, 'recurring_candidate': True}`. Both calls went through the exact
   same `classify_email` function/prompt — no code branch keyed on either
   test email's customer name or specific format (confirmed by direct
   reading: the prompt's `recurring_candidate` instruction contains no
   customer- or format-specific conditional anywhere). **Pass — confirms
   the detection is structural/general, not hardcoded to one known shape.**
3. Ordinary one-off conversational email ("Hey, are we still on for lunch
   tomorrow?") → observed `{'customer': 'Unsorted', 'kind': 'Emails',
   'confidence': 0.9, 'recurring_candidate': False}`. **Pass.**
4. `email_classification.classify_captured_email(email, known_customers,
   known_kinds)` called directly with a synthetic email dict (the same
   Weekly Usage Report body) → returned the same 4-key dict shape
   (`{'customer': 'Acme Corp', 'kind': 'Reports', 'confidence': 0.99,
   'recurring_candidate': True}`); a `mock.patch.object` spy around
   `compass_client.classify_email` confirmed exactly 1 call
   (`spy.call_count == 1`) for one `classify_captured_email` invocation —
   never a second Compass call of any kind. **Pass.**
5. Regression check — an ordinary test email ("Hi team, just checking in
   on the project status... Thanks, Sam (Acme Corp)") → observed
   `{'customer': 'Acme Corp', 'kind': 'Emails', 'confidence': 0.99,
   'recurring_candidate': False}` — `customer`/`kind`/`confidence` classify
   exactly as this codebase's existing behavior would (correct customer
   match, correct `kind`, sane confidence), confirming no regression from
   the prompt edit. **Pass.**

No scope-internal judgement calls beyond ordinary prompt wording (not an
assumption filling a real requirements gap — Test step 2 already directly
proves the structural/general requirement). No out-of-scope files touched;
`ast.parse()` of both modified files confirmed clean. No `ESCALATIONS.md`/
`REVIEW-QUEUE.md` entry needed.

**Acceptance criteria verified:**
- **AC-06** (Scenario 6, partial — the detection mechanism) — **Verified**,
  Test step 2 above.
- `recurring_candidate` additive on `classify_email`'s return contract,
  every existing field/fallback unchanged — **Verified**, Test steps 1/3/5
  plus direct reading of the parsing dict.
- `classify_captured_email` makes exactly one Compass call per invocation —
  **Verified**, Test step 4 (spy `call_count == 1`).
