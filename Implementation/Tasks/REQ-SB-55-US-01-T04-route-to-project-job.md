---
id: REQ-SB-55-US-01-T04
title: Route-to-Project Job — currently-open-Projects guess or new-Project proposal, always via Pending Approval
parent_story: REQ-SB-55-US-01
requirement_id: REQ-SB-55
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-043 created) — carried from the parent story; the human reviews ADR-043 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: [REQ-SB-55-US-01-T01, REQ-SB-55-US-01-T03]
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-55-US-01-T04 — `Route-to-Project` Job

## Parent Story

- Story: [[REQ-SB-55-US-01]] — `../UserStories/REQ-SB-55-US-01-email-capture-and-threading-pipeline.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-55 *Email Capture & Threading Pipeline*

---

## Objective

Add `route_to_project(thread_result, classification, email) -> dict` to `email_classification.py` — guesses which of the matched Customer's currently-open Projects a brand-new Thread belongs to (or proposes a new Project if none fit), and ALWAYS creates a Pending Approval for that decision, never auto-committing the placement. Wire the deferred "commit on Approve" side effect as a new `_APPROVAL_HANDLERS` entry in `pending_approvals_router.py`, generalizing that router's own hardcoded outcome-message construction so a future, differently-shaped handler (`T06`) can supply its own message too.

---

## Starting State → End State

**Before / Inputs:**
- `T01`'s `list_customer_projects(customer)` and unconditional frontmatter setter; `T03`'s `thread_match_merge` returns `{"thread_path", "created", "conversation_id", "customer"}`.
- `pending_approval_registry.create_pending_approval(agent_id, trigger, action_id, description, payload=None)` — real, already-shipped.
- `pending_approvals_router.py`'s `_APPROVAL_HANDLERS` dict and its Approve endpoint's own hardcoded `outcome_message = f"Approved — filed at {result['path']}."` line (the ONLY existing shape for this dispatch branch, written for `vault_filing_expert.finalize_new_top_level_area`/`vault_write_tools.finalize_hermes_write`, both of which return `{"path": ...}` with no `"message"` key).

**After / Outputs:**
- `route_to_project(thread_result, classification, email) -> dict | None` exists — returns `None` immediately (no-op) if `thread_result["created"]` is `False` (an update to an already-routed Thread never re-routes, `AC-04`'s own mechanism lives in `T07`'s conditional graph edge, but this function's own contract also defends the same invariant defensively). For a brand-new Thread: reads `list_customer_projects(classification["customer"])`, guesses the best-fitting currently-open Project (or determines none fit and proposes a new one), and calls `pending_approval_registry.create_pending_approval(agent_id="email-capture-pipeline", trigger="direct", action_id="route_thread_to_project", description=..., payload={"thread_path", "customer", "guessed_project", "is_new_project"})`.
- `pending_approvals_router.py` gains `finalize_thread_project_routing(payload) -> dict` (creates the new Project directory first if `is_new_project`, then sets the Thread's `project` frontmatter key via `T01`'s setter, returns `{"path": <thread_path>, "message": f"Approved — Thread filed under project '{...}'."}`) wired into `_APPROVAL_HANDLERS["route_thread_to_project"]`.
- `approve_pending_approval`'s own `_APPROVAL_HANDLERS` branch now reads `outcome_message = result.get("message") or f"Approved — filed at {result['path']}."` — additive, backward-compatible (the two existing handlers return no `"message"` key, so their own outcome text is byte-for-byte unchanged).

---

## Files to Modify

- `src/backend/app/business/email_classification.py` — add `route_to_project`.
- `src/backend/app/data_access/compass_client.py` — add one new function, `guess_project_for_thread(thread_summary: str, open_projects: list[str]) -> dict`, returning `{"project": <name>, "confidence": <0-1 float>}` — reuses this file's own existing prompt/parse/`CompassError` shape (mirrors `classify_task`'s own "narrower sibling of `classify_email`" precedent), asking Compass to pick the best-fitting name from `open_projects` or propose a new, concise proper-noun Project name if none genuinely fit (same "don't guess wildly, propose a new one instead" posture `classify_email`'s own `customer` axis already uses).
- `src/backend/app/api/pending_approvals_router.py` — add `finalize_thread_project_routing` (or import it from `email_classification.py` if the coder judges that the more natural home — either is acceptable, this is this story's own business logic, not a new architectural layer; log the choice), register it in `_APPROVAL_HANDLERS`, and generalize the one outcome-message line as described above.

---

## Constraints

- Inherits from parent story: Thread → Project routing is ALWAYS a Pending Approval — never an auto-committed write, regardless of the Pipeline's own top-level working-mode gate (`ADR-021`'s "independent of working mode" precedent, applied a second time per `ADR-043` point 5). `route_to_project` must create the Pending Approval unconditionally whenever it runs (i.e. whenever `thread_result["created"]` is `True`) — it never silently skips creating one because the guess looks "obvious."
- `route_to_project` must use `trigger="direct"`, never `"background"` — `create_pending_approval`'s own idempotency guard only dedupes `"background"` triggers, and a single pipeline tick can legitimately produce multiple distinct routing proposals across different new Threads; `"background"` would silently collapse them into one.
- `route_to_project` must return `None`/no-op (create nothing) when `thread_result["created"]` is `False` — defends `AC-04` even if a future caller mistakenly invokes it on an update.
- `finalize_thread_project_routing` must be dispatched ONLY via the Approve endpoint's existing `_APPROVAL_HANDLERS` branch (never via `skill_registry`/`_execute_action`) — mirrors the Vault Filing Expert Tier-2 precedent exactly (`ADR-021` point 5, `ADR-043` point 4).
- The `outcome_message` generalization must be STRICTLY additive — `vault_filing_expert.finalize_new_top_level_area`/`vault_write_tools.finalize_hermes_write` (both pre-existing `_APPROVAL_HANDLERS` entries) must produce byte-for-byte the same outcome message text after this change as before it.
- `guess_project_for_thread` must never fabricate a match not present in `open_projects` when at least one genuinely fits, and must never force a bad fit — proposing a new Project name when none of `open_projects` fit is the correct, expected outcome, not an error.
- Do not modify `list_pending_approvals`/`get_pending_approval`/`resolve_pending_approval`/`decline_pending_approval` — this task only adds a new dict entry and generalizes one message-construction line.

---

## Tests

**Manual verification steps:**
1. **[REQ-SB-55-US-01-AC-03]** Against a throwaway scratch vault with a Customer that has at least one real, currently-open Project directory (`T01`'s `list_customer_projects` returns a non-empty list), call `route_to_project(thread_result, classification, email)` for a brand-new Thread (`thread_result["created"] = True`). Confirm exactly one new Pending Approval now exists (`pending_approval_registry.list_pending_approvals(status="pending")`), with `action_id="route_thread_to_project"` and a payload naming the Thread's own path and a guessed Project. Confirm the Thread note's own `project` frontmatter key is STILL absent at this point (not silently pre-filed). Call `POST /pending-approvals/{id}/approve` (or the equivalent direct function call, `approve_pending_approval`) — confirm the response's outcome message names the approved Project, and confirm the Thread note's `project` frontmatter key now reads back as the approved Project's name.
2. Repeat step 1 for a Customer with ZERO currently-open Projects — confirm the Pending Approval's payload proposes a NEW Project (a concise, real proper-noun name, `is_new_project: True`) rather than forcing a bad fit from an empty list. On Approve, confirm a real new Project directory now exists (`project_concept_file_exists(customer, proposed_name)` is `True`) AND the Thread's `project` key is set to it.
3. **[REQ-SB-55-US-01-AC-04]** Call `route_to_project(thread_result, classification, email)` with `thread_result["created"] = False` (simulating a later message in an already-routed conversation) — confirm it returns `None`/no-op and confirms (via a before/after `list_pending_approvals` count) that NO new Pending Approval was created.
4. Regression check: call `POST /pending-approvals/{id}/approve` against an EXISTING, already-shipped Vault Filing Expert Tier-2 proposal or Hermes-write proposal (or a synthetic record shaped identically) — confirm the outcome message text is byte-for-byte identical to its pre-this-task wording (the `result.get("message")` generalization does not alter either existing handler's own output).
5. Confirm `route_to_project`'s own Pending Approval record uses `trigger="direct"` (read directly from the created record) — never `"background"`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-03** (Scenario 3) — a new Thread's Project routing always creates a Pending Approval, never an auto-committed write; approving it places the Thread under the approved Project (existing or newly created).
- [x] **AC-04** (Scenario 4, defensive half) — `route_to_project` never creates a second approval when called for an update to an already-routed Thread.
- [x] `trigger="direct"` used, never `"background"`.
- [x] The router's `outcome_message` generalization is additive — both pre-existing `_APPROVAL_HANDLERS` entries unaffected.
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The actual conditional graph edge that decides WHETHER `route_to_project` is invoked at all (only for a brand-new Thread) — `T07`'s own job; this task's own defensive `created`-check is a belt-and-suspenders guard, not the primary mechanism.
- Any UI affordance for reviewing/choosing among multiple candidate Projects — this Job always proposes exactly ONE guess (or one new-Project proposal) per Pending Approval, matching Scenario 3's own literal wording; no new screen (parent story's own Affected Screens: None).
- Declining a routing proposal's own downstream handling beyond the existing generic `decline_pending_approval` — no new behavior needed there.

---

## Context / Notes

Full reasoning: `Implementation/Architecture/ADR.md` → `ADR-043` points 4, 5; `Implementation/Architecture/architecture.md` → "Email Capture & Threading Pipeline — First Concrete Pipeline". Real precedent to mirror: `vault_filing_expert.finalize_new_top_level_area`'s own `_APPROVAL_HANDLERS`-dispatched, payload-driven "finish the deferred write on Approve" shape (`ADR-021` point 5).

**The `trigger="direct"` choice is a decomposer-level judgement call, not spelled out by `ADR-043` itself** — see the parent story's own `## Notes` (Decomposer pass) for the full reasoning: `create_pending_approval`'s existing idempotency guard only dedupes `trigger == "background"`, which would silently collapse multiple distinct routing proposals from the same pipeline tick into one.

---

## Implementation Log

**2026-08-16, coder pass.**

Three files edited, exactly as scoped under `## Files to Modify`:

- `src/backend/app/data_access/compass_client.py` — added
  `guess_project_for_thread(thread_summary: str, open_projects: list[str]) ->
  {"project": str, "confidence": float}`, mirroring `classify_email`/
  `classify_task`'s existing prompt/payload/`CompassError`-parsing shape
  exactly (same `httpx.post`, same JSON-object response contract, same
  `except (KeyError, IndexError, ValueError, json.JSONDecodeError)` parse
  guard). The prompt lists the currently-open Projects and instructs Compass
  to reuse an exact existing name when it clearly fits, or propose a
  concise, new proper-noun name when none genuinely do — explicitly framed
  as "never force a bad fit onto an existing Project just because the list
  is non-empty," and an empty `open_projects` list is worded as "(none
  currently open)" so a zero-Project Customer still gets a real proposal,
  never a forced/empty guess. Raises `CompassError` on an empty/missing
  `"project"` key in the parsed response (mirrors `summarize_content`'s own
  "never fabricate" empty-result guard) — propagated uncaught, same
  "caller decides" posture `classify_captured_email` already established.

- `src/backend/app/business/email_classification.py` — added
  `route_to_project(thread_result, classification, email) -> dict | None`
  and `finalize_thread_project_routing(payload: dict) -> dict`, placed
  directly after `thread_match_merge` (before `classify_recent_emails`).
  `route_to_project` returns `None` immediately when
  `thread_result["created"]` is `False` (Scenario 4/`AC-04`'s own defensive
  half — the primary routing decision is `T07`'s own conditional graph
  edge, out of this task's scope). For a brand-new Thread: reads
  `vault_writer.list_customer_projects(customer)`, filters to
  `status == "active"` (the "currently open" judgement `T01`'s own
  primitive explicitly left to this task — no other status value is ever
  written anywhere in this codebase today, so "active" is the only real
  signal available), calls `compass_client.guess_project_for_thread` with
  the same deterministic `_build_thread_summary_content(email)` rendering
  `thread_match_merge` already uses for `## Summary` (no second, divergent
  summary-building helper), and computes `is_new_project` business-side
  as a plain `guessed_project not in open_projects` membership check
  (never returned by Compass itself — keeps `guess_project_for_thread`'s
  own return contract to exactly the two keys this task's `## Files to
  Modify` entry specified). ALWAYS calls
  `pending_approval_registry.create_pending_approval(agent_id=
  "email-capture-pipeline", trigger="direct", action_id=
  "route_thread_to_project", ...)` — unconditional on every brand-new-Thread
  call, per this task's own Constraint; `trigger="direct"` exactly as the
  parent story's own decomposer-pass judgement call specifies (never
  `"background"`, whose idempotency guard would silently collapse multiple
  distinct routing proposals from the same pipeline tick). `payload` carries
  `thread_path`/`customer`/`guessed_project`/`is_new_project` exactly as
  specified. `finalize_thread_project_routing` mirrors `vault_filing_expert.
  finalize_new_top_level_area`'s own "payload-driven deferred write" shape:
  creates the Project directory first when `is_new_project`
  (`vault_writer.create_project_directory_baseline`), then sets the Thread's
  `project` frontmatter key unconditionally via `upsert_frontmatter_key`
  (never `insert_frontmatter_key_if_missing`, which would no-op since
  `project` is absent-by-design on every newly created Thread), returning
  `{"path": <thread_path str>, "message": f"Approved — Thread filed under
  project '{project}'."}`. Added `from pathlib import Path` to this file's
  imports — needed because a Pending-Approval `payload` value is always a
  plain, JSON-round-tripped `str` (never a `Path`), so
  `finalize_thread_project_routing` must re-wrap `payload["thread_path"]`
  as `Path(...)` before handing it to `upsert_frontmatter_key`/`read_note`
  (both require a real `Path`, confirmed live by the exact same
  `AttributeError` class `T03`'s own Implementation Log already documented
  for `create_thread_note_baseline`'s return value — see judgement call
  below for where this was actually caught).

- `src/backend/app/api/pending_approvals_router.py` — imported
  `finalize_thread_project_routing` from `email_classification.py`
  (alongside the already-imported `run_capture_for_agent`) and registered
  it as `_APPROVAL_HANDLERS["route_thread_to_project"]`. Generalized the
  `_APPROVAL_HANDLERS` branch's own `outcome_message` line from the
  hardcoded `f"Approved — filed at {result['path']}."` to
  `result.get("message") or f"Approved — filed at {result['path']}."` —
  additive only; no other line in `approve_pending_approval`/
  `decline_pending_approval`/`list_pending_approvals`/`get_pending_approval`
  touched.

**One scope-internal judgement call, logged for human spot-check (not an
escalation — the task file itself explicitly left this choice to the
coder):**

1. **`finalize_thread_project_routing`'s home** — placed in
   `email_classification.py` (business layer), imported into
   `pending_approvals_router.py`'s `_APPROVAL_HANDLERS`, rather than defined
   inline in the router file. The task's own `## Files to Modify` entry for
   `pending_approvals_router.py` explicitly named both as acceptable
   ("or import it from `email_classification.py` if the coder judges that
   the more natural home"). Chose the business-layer home because it
   mirrors `vault_filing_expert.finalize_new_top_level_area`'s own real,
   already-shipped precedent exactly (a business-layer function imported
   into the router's dispatch table, never router-embedded business logic)
   — introducing a second shape for the same `_APPROVAL_HANDLERS` pattern
   would be a real, avoidable inconsistency.

**Verification (manual mode — no automated test stack exists yet for this
backend; real backend `.venv`, `VAULT_PATH` env-overridden to a
`tempfile.mkdtemp()` scratch vault, the real configured vault never touched;
real, configured Compass Provider — no HTTP mocking — per this story's own
established `T01`/`T02`/`T03` protocol. Script + full transcript kept in
this session's own scratchpad, not committed.):**

1. **[`REQ-SB-55-US-01-AC-03`]** Created a real `Project Alpha` directory
   under Customer `Acme Corp` (`vault_writer.create_project_directory_
   baseline`) — `list_customer_projects("Acme Corp")` confirmed one
   `status: "active"` entry. Called `thread_match_merge` for a brand-new
   message (`conversation_id="conv-route-1"`) — `created is True`. Called
   `route_to_project(thread_result_1, classification_1, email_1)` —
   observed exactly one new pending record (`before=0`, `after=1` via
   `list_pending_approvals(status="pending")`), `action_id ==
   "route_thread_to_project"`, `payload["thread_path"]` matching the
   Thread's own path, `payload["guessed_project"] == "Project Alpha"`,
   `payload["is_new_project"] is False`. Read the Thread note's own
   frontmatter directly BEFORE approving — `"project" not in frontmatter`
   confirmed (not silently pre-filed). Called
   `pending_approvals_router.approve_pending_approval(approval_id)`
   directly — re-read the Thread note's frontmatter AFTER — `project ==
   "Project Alpha"`, matching the approved guess exactly. **PASS.**
2. Repeated for Customer `Globex Inc` with ZERO Project directories —
   `list_customer_projects("Globex Inc") == []` confirmed. `route_to_project`
   for a brand-new Thread in that conversation returned a pending record
   with `is_new_project is True` and a real, concise proper-noun proposed
   name (`"Globex Inc Engagement"`, live Compass output — not forced from
   an empty list). Confirmed `project_concept_file_exists("Globex Inc",
   "Globex Inc Engagement") is False` before Approve. Called
   `approve_pending_approval` — confirmed `project_concept_file_exists(...)
   is True` afterward (a real new Project directory now exists) AND the
   Thread's `project` frontmatter key reads back as that same name. **PASS.**
3. **[`REQ-SB-55-US-01-AC-04`]** Called `route_to_project` with a copy of
   `thread_result_1` whose `"created"` key was overridden to `False`
   (simulating a later message in an already-routed conversation) —
   observed the function returns `None`, and a before/after
   `list_pending_approvals(status="pending")` count confirmed NO new
   Pending Approval was created (`before == after == 0`, the two Step 1/2
   approvals having already resolved to `"approved"` by this point).
   **PASS.**
4. Regression check: created a synthetic, already-shipped-shaped
   `propose_new_top_level_area` pending record (real `vault-filing-expert`
   `agent_id`, a real payload matching `finalize_new_top_level_area`'s own
   required keys) and called `approve_pending_approval` against it directly
   — confirmed live, via the agent's own history read-back
   (`vault_writer.load_agent_history("vault-filing-expert")`), that the
   recorded outcome text still exactly matches the pre-this-task
   `f"Approved — filed at {result['path']}."` fallback shape (starts with
   `"Approved — filed at "`, ends with `"."`, contains the real written
   note's own path) — `finalize_new_top_level_area` returns no `"message"`
   key, so `result.get("message") or ...` falls straight through to the
   original text, byte-for-byte. Confirmed by direct reading that
   `finalize_hermes_write` (`vault_write_tools.py`) also returns only
   `{"path": path}`, no `"message"` key — the same fallback branch applies
   to it identically; not re-run live a second time since the code path
   exercised is the exact same `outcome_message` line, already confirmed
   dynamically for the first handler. **PASS.**
5. Confirmed directly from both created records (Steps 1/2 above) that
   `trigger == "direct"` on both — never `"background"`. **PASS.**

**Acceptance criteria verified:**

- **AC-03** (Scenario 3) — **Verified**, steps 1/2 above.
- **AC-04** (Scenario 4, defensive half) — **Verified**, step 3 above.
- `trigger="direct"` used, never `"background"` — **Verified**, step 5.
- The router's `outcome_message` generalization is additive — **Verified**,
  step 4 (live for `propose_new_top_level_area`; confirmed by direct code
  reading for `hermes_vault_write`, both handlers sharing the identical
  `{"path": ...}`-only return shape and the identical dispatch line).

No `ESCALATIONS.md` entry — nothing here contradicts an `Accepted` ADR, the
PRD, or a `MEMORY.md` constraint; the one judgement call above is a
scope-internal implementation-detail decision the task file itself left
open, logged inline for human spot-check per this task's already-standing
`gate: flagged` (trigger-3, `ADR-043`). No new `REVIEW-QUEUE.md` entry
either — the task's already-flagged gate already carries it into the
existing human-review pass.
