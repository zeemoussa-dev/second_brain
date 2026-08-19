---
id: REQ-SB-57-US-01-T04
title: Background-amendment durable-fact detection + Pending Approval proposal/finalize
parent_story: REQ-SB-57-US-01
requirement_id: REQ-SB-57
type: backend
status: Done
gate: flagged
gate_reason: "scope-internal judgement calls only — see Implementation Log"
phase: P1
depends_on: [REQ-SB-57-US-01-T02]
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-57-US-01-T04 — Background-amendment durable-fact detection + Pending Approval

## Parent Story

- Story: [[REQ-SB-57-US-01]] — `../UserStories/REQ-SB-57-US-01-project-and-customer-status-synthesizer-agents.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-57 *Project & Customer Status Synthesizer Agents*

---

## Objective

Give the Customer Synthesizer its second, independent trigger: detecting
a genuinely new, durable fact in the evidence that just caused a
resynthesis pass, and routing it through a Pending Approval
(`propose_background_amendment`) — never a silent `## Background`
rewrite — mirroring the already-shipped "propose in the owning module,
finalize via `_APPROVAL_HANDLERS`" shape (`vault_filing_expert.py`'s
`_create_cross_cutting_proposal`/`finalize_cross_cutting_update`,
`Implementation/Learnings.md` `SPRINT-050`, 3x-confirmed canonical
shape).

---

## Starting State → End State

**Before / Inputs:**
- `T02` has shipped `synthesize_customer(customer, concluded_project=
  None, evidence_text="")`, which accepts `evidence_text` but does not
  yet consume it, and returns `{"customer": customer, "amendment_
  proposed": False}`.
- `app/data_access/compass_client.py::guess_project_for_thread` is the
  real, closest-precedent shape for a narrow, single-purpose Compass
  call: builds a JSON-object-returning prompt (with `prompt_override`
  support), posts via `httpx.post` to `settings.compass_base_url` with
  `settings.compass_model`/`settings.compass_api_key`, raises
  `CompassError` on any `httpx.HTTPError` or unparseable response.
- `app/business/vault_filing_expert.py::_create_cross_cutting_proposal`/
  `finalize_cross_cutting_update` (`REQ-SB-63-US-01`, `Done`) is the
  real "propose in the owning module, finalize via `_APPROVAL_HANDLERS`"
  precedent — `_create_cross_cutting_proposal` creates a `trigger=
  "direct"` Pending Approval with a structured payload;
  `finalize_cross_cutting_update` performs the one deferred write, only
  ever called on approval.
- `app/api/pending_approvals_router.py::_APPROVAL_HANDLERS` is the real
  dispatch table `approve_pending_approval` consults for any
  `action_id` not backed by an `agent_registry`-declared action.

**After / Outputs:**
- `app/data_access/compass_client.py` gains `detect_customer_durable_
  fact(evidence_text: str, customer: str, existing_background: str,
  prompt_override: str | None = None) -> dict` — mirrors `guess_
  project_for_thread`'s exact construction/`CompassError`-handling
  shape. Prompt is grounded in BOTH `evidence_text` (the new content)
  AND `existing_background` (the Customer's own current `## Background`
  prose) — explicitly instructed to answer "is this a NEW durable fact
  not already reflected below," so an already-recorded fact naturally
  yields `has_durable_fact: false` (the honest dedup boundary; no
  separate dedup mechanism is built). Returns `{"has_durable_fact":
  bool, "fact": str}` (`fact` may be `""` when `has_durable_fact` is
  `False`).
- `project_customer_synthesizer.py`:
  - `synthesize_customer` gains: when `evidence_text` is non-empty,
    calls `detect_customer_durable_fact` (reading the Customer's own
    current `## Background` first via `read_body_section`); on
    `has_durable_fact: True`, calls a new `_propose_background_
    amendment(customer, fact, source_description)` helper that creates
    ONE `trigger="direct"` Pending Approval (`action_id
    "propose_background_amendment"`, `agent_id "project-customer-
    synthesizer"`, payload `{"customer": customer, "fact": fact}`) and
    sets the returned dict's `"amendment_proposed"` to `True`. Any
    exception from the Compass call is caught (mirrors `consult_
    librarian`'s own honest, non-crashing `{"status": "unavailable",
    ...}` posture) and never aborts the rest of `synthesize_customer`'s
    own Glimpse/History work, which has already completed by this
    point in the function.
  - New `finalize_background_amendment_proposal(payload: dict) -> dict`
    — called only once the operator approves. Reads the Customer's own
    current `## Background` (`read_body_section`), appends the approved
    `fact` as one new bullet to the existing prose, writes the combined
    content back via `replace_body_section(concept_path, "##
    Background", <existing + new bullet>)`. Returns `{"path": ...,
    "message": "Approved — Background amended for <customer>."}`.
- `app/api/pending_approvals_router.py::_APPROVAL_HANDLERS` gains
  `"propose_background_amendment": project_customer_synthesizer.
  finalize_background_amendment_proposal` — one new import, one new
  dict entry, mirroring the existing `"propose_cross_cutting_update"`
  entry exactly.

---

## Files to Modify

- `src/backend/app/data_access/compass_client.py` — add `detect_
  customer_durable_fact`.
- `src/backend/app/business/project_customer_synthesizer.py` — extend
  `synthesize_customer`; add `_propose_background_amendment` and
  `finalize_background_amendment_proposal`.
- `src/backend/app/api/pending_approvals_router.py` — register the new
  `_APPROVAL_HANDLERS` entry and its import.

---

## Constraints

- Inherits from parent story — **`## Background` is NEVER written by
  the detection call itself** — only `finalize_background_amendment_
  proposal`, only on approval (same "never called for a declined
  record" contract as `finalize_cross_cutting_update`).
- **`trigger="direct"`, never `"background"`** — a single synthesis pass
  can legitimately coexist with other distinct proposals; `"background"`
  `create_pending_approval`'s own idempotency guard would silently
  collapse them (same reasoning already established for `route_to_
  project`/`detect_recurring_pattern`/`_create_cross_cutting_proposal`).
- **Distinct trigger from routine Glimpse regeneration** — detection
  only runs when `evidence_text` is non-empty (a real Thread/Meeting
  content delta this pass); a Customer resynthesis with no fresh
  evidence text (e.g. `T02`'s own first-routing call site, which passes
  `evidence_text=""`) never attempts detection.
- **Ground the detection prompt in the Customer's CURRENT `##
  Background`** so it naturally declines an already-recorded fact — this
  is the task's own real dedup mechanism; do not build a second,
  separate dedup/idempotency check.
- **One new Compass call only** — never re-derives `evidence_text` from
  anywhere else; uses exactly what `synthesize_project` →
  `synthesize_customer` already threaded through.
- **Never crashes `synthesize_customer`'s own Glimpse/History work** — a
  `CompassError` (or any exception) from the detection call is caught
  and results in `amendment_proposed: False`, nothing more; the
  Glimpse/History writes earlier in the same function are already
  durable by the time this runs.

---

## Tests

**Manual verification steps:**

1. `[REQ-SB-57-US-01-AC-03]` Using a real, disposable Customer with an
   existing (even blank) `## Background`, call `synthesize_customer`
   directly with a deliberately-engineered `evidence_text` containing an
   obvious, unambiguous new durable fact about that customer (e.g. "This
   customer signed a 3-year enterprise agreement on 2026-08-18") not
   already present in `## Background`. Confirm: (a) `## Background` is
   NOT changed by this call; (b) exactly one new Pending Approval exists
   with `action_id == "propose_background_amendment"` and a payload
   naming the real customer and a real, non-empty `fact`. Then call
   `POST /pending-approvals/{id}/approve` (or `finalize_background_
   amendment_proposal(payload)` directly) and confirm `## Background`
   now contains the approved fact, appended to whatever was already
   there.
2. Non-AC regression check: re-run `synthesize_customer` with the SAME
   `evidence_text` a second time (after the amendment above is already
   approved and reflected in `## Background`). Confirm the detection
   call, now grounded in the UPDATED `## Background`, does not propose
   a second, duplicate approval for the same already-recorded fact
   (`has_durable_fact: false`).
3. Non-AC regression check: call `synthesize_customer` with
   `evidence_text=""` (mirrors `T02`'s own first-routing call site).
   Confirm no Compass call is made and no Pending Approval is created.
4. Clean up every disposable fixture (Customer amendment content,
   Pending Approval records) created during verification.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `REQ-SB-57-US-01-AC-03` — a deliberately-introduced new durable
      fact produces a Pending Approval, never a silent `## Background`
      rewrite; approving it updates `## Background` with the approved
      amendment
- [x] A repeat observation of an already-recorded fact does not produce
      a duplicate proposal
- [x] An empty `evidence_text` makes no Compass call and proposes
      nothing
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any change to `vault_filing_expert.py`'s own cross-cutting-update
  mechanism (`REQ-SB-63-US-01`, `Done`) — this task adds a NEW, separate
  approval kind, never touches that one.
- Inferring a durable fact from anything other than the `evidence_text`
  this pass was already given — no separate vault-wide scan.
- This is the LAST task in this story's own dependency chain — nothing
  else depends on it.

---

## Context / Notes

Depends on `T02` for `synthesize_customer`'s own real signature/cascade
call to exist. `REQ-SB-54` point 5 ("Background... mirrors `agent_
memory.json`'s existing shape... folded into prose") is the narrative
precedent for "append, fold into existing prose" rather than a full
LLM-rewritten regeneration of `## Background` on every amendment —
this task's own `finalize_background_amendment_proposal` is
deliberately mechanical (read existing + append), not a second Compass
call, keeping the deferred write itself fully deterministic.

---

## Implementation Log

**Coder pass (2026-08-18).** Built exactly as specced, no deviations from
the `## Files to Modify` list.

- `app/data_access/compass_client.py`: added `detect_customer_durable_fact
  (evidence_text, customer, existing_background, prompt_override=None) ->
  dict` — byte-for-byte mirrors `guess_project_for_thread`'s own payload
  construction / `httpx.post` / `CompassError` handling shape. Prompt is
  grounded in BOTH the new `evidence_text` and the Customer's own current
  `## Background` prose, explicitly asking whether the evidence names a
  NEW durable fact not already reflected there. Returns
  `{"has_durable_fact": bool, "fact": str}`.
- `app/business/project_customer_synthesizer.py`:
  - `synthesize_customer` now runs the detection call only when
    `evidence_text` is non-empty, reading the Customer's own current `##
    Background` first (`read_body_section`) and passing it to `compass_
    client.detect_customer_durable_fact` alongside `evidence_text`/
    `customer`. On `has_durable_fact: True`, calls the new `_propose_
    background_amendment(customer, fact, source_description)` and sets
    `amendment_proposed: True` on the returned dict. The whole detection
    block is wrapped in a bare `try/except Exception: pass` — any Compass
    failure silently falls back to `amendment_proposed: False` without
    touching the Glimpse/History work already completed earlier in the
    function (mirrors `consult_librarian`'s own honest, non-crashing
    posture, `Implementation/Learnings.md` `SPRINT-050`).
  - New `_propose_background_amendment` — mirrors `vault_filing_expert.
    _create_cross_cutting_proposal`'s exact shape: local (not
    module-level) `pending_approval_registry` import, one `trigger=
    "direct"` `create_pending_approval` call, `action_id
    "propose_background_amendment"`, `agent_id "project-customer-
    synthesizer"`, payload `{"customer": customer, "fact": fact}`.
  - New `finalize_background_amendment_proposal(payload) -> dict` — reads
    the Customer's own current `## Background` (`read_body_section`),
    appends the approved `fact` as one new `"- <fact>"` bullet, writes
    the combined content back via `replace_body_section`. Deliberately
    mechanical (no second Compass call), returns
    `{"path": ..., "message": "Approved — Background amended for
    <customer>."}`.
  - Module docstring's own ownership statement extended to name `##
    Background` as owned by this module too (previously only named
    `## Glimpse`/`log.md`) — a factual-accuracy fix, not new behavior,
    made while already editing this file for this task.
- `app/api/pending_approvals_router.py`: added one import
  (`finalize_background_amendment_proposal` from
  `project_customer_synthesizer`) and one `_APPROVAL_HANDLERS` entry
  (`"propose_background_amendment"`), mirroring the existing
  `"propose_cross_cutting_update"` entry exactly.

**Scope-internal judgement calls (logged for human spot-check, not
escalations):**

1. **`source_description` construction.** The task's own End-State names
   `_propose_background_amendment(customer, fact, source_description)`
   but neither `synthesize_customer`'s own signature nor its real callers
   thread through an explicit human-readable description of WHERE
   `evidence_text` came from (a Thread subject/sender, a Meeting title,
   etc.) — `synthesize_customer` only receives the raw text itself. Used
   a generic, honest `f"evidence observed while resynthesizing
   \"{customer}\""` rather than fabricating a more specific provenance
   claim the function doesn't actually have. If a more specific
   provenance string is wanted later (e.g. threading the originating
   Thread's own subject line all the way through), that is a follow-up
   enhancement, not something this task's own real inputs support today.
2. **Module-level `compass_client` import vs. `vault_filing_expert`'s
   local-import convention for `pending_approval_registry`.** Imported
   `compass_client` at module level in `project_customer_synthesizer.py`
   (mirroring `email_classification.py`'s own module-level
   `compass_client` import) since no circular-import risk exists between
   these two modules; kept the LOCAL import specifically for `pending_
   approval_registry` inside `_propose_background_amendment`, mirroring
   `vault_filing_expert._create_cross_cutting_proposal`'s own precedent
   exactly, since that is the literal shape this task's own Objective
   names to mirror.
3. **Approval-time dispatch verified via the real `approve_pending_
   approval` router function called directly in-process** (not over
   HTTP) — equivalent real code path (no `Request`/`Depends` dependency
   in that function's signature), consistent with this project's own
   "skip the HTTP layer when it isn't load-bearing for the locked AC"
   precedent (`Implementation/Learnings.md` `SPRINT-023`).

**Live verification — `REQ-SB-57-US-01-AC-03`:** performed directly
against the real, configured vault (`C:\myWorx\Moussa MD\Moussa Brain`),
via a disposable throwaway Customer (`ZZZ-T04-Verify-Co`, created with
`vault_writer.create_customer_directory_baseline`, blank `## Background`
baseline).

1. Called `synthesize_customer("ZZZ-T04-Verify-Co", evidence_text=
   "This customer signed a 3-year enterprise agreement on 2026-08-18,
   committing to a company-wide platform rollout across all regional
   offices.")` directly — a REAL Compass call (`https://api.core42.ai/v1/
   chat/completions`, `200 OK`). Observed: `amendment_proposed: True`;
   `## Background` read immediately after was still `""` (unchanged —
   confirms no silent rewrite); exactly one new Pending Approval existed
   with `action_id == "propose_background_amendment"`, `agent_id ==
   "project-customer-synthesizer"`, payload `{"customer": "ZZZ-T04-
   Verify-Co", "fact": "On 2026-08-18, ZZZ-T04-Verify-Co signed a 3-year
   enterprise agreement committing to a company-wide platform rollout
   across all regional offices."}` — real customer name, real non-empty
   fact.
2. Called the real `approve_pending_approval(record["id"])` router
   function directly. Observed: record `status` flipped to `"approved"`;
   `## Background` read back afterward was `"- On 2026-08-18, ZZZ-T04-
   Verify-Co signed a 3-year enterprise agreement committing to a
   company-wide platform rollout across all regional offices."` — the
   approved fact, appended, exactly as specced. **AC-03: PASS, both
   halves (propose, then approve-and-write) directly observed.**

**Non-AC regression checks (both performed live, both pass):**

- Re-ran `synthesize_customer` with the IDENTICAL `evidence_text` a
  second time, now grounded in the just-updated `## Background`.
  Observed: `amendment_proposed: False`, zero new pending (unapproved)
  `propose_background_amendment` records for this customer — the
  detection call itself declined the already-recorded fact
  (`has_durable_fact: false`), confirming the "ground in current
  Background" dedup mechanism works as designed, live, not just by
  reasoning about the prompt.
- Called `synthesize_customer("ZZZ-T04-Verify-Co", evidence_text="")`
  with `compass_client.detect_customer_durable_fact` monkeypatched (on
  the `project_customer_synthesizer` module's own imported reference) to
  record whether it was ever invoked. Observed: the tracked call flag
  stayed `False` (Compass was never called), `amendment_proposed:
  False`, and no new Pending Approval was created — confirms the `if
  evidence_text:` guard is a real, structural no-op for an empty string,
  not just true by inspection.

**Cleanup (step 4 of the task's own Tests block):** removed the
disposable Customer directory (`shutil.rmtree` on `Work/Customers/
ZZZ-T04-Verify-Co/`) and the one disposable Pending Approval record (by
its own `id`, read-filter-write against the real
`agent_pending_approvals.json` state) at the end of the same script run.
Independently re-confirmed afterward, in a fresh process: the directory
no longer exists (`os.path.exists` → `False`) and zero pending-approval
records remain naming `"ZZZ-T04-Verify-Co"` — the real vault is left
exactly as it was found.

**No bug found this task.** Unlike several of tonight's other tasks, this
build's own first live run passed every check on the first attempt —
`guess_project_for_thread`'s own already-proven call shape generalized
cleanly to `detect_customer_durable_fact` with zero surprises.

**Story-level consequence:** this was the LAST task in `REQ-SB-57-US-01`'s
own dependency chain (`T01`/`T02`/`T03` already `Done`). All four tasks
are now `Done` — story `status: In Progress -> Done` (see story file's
own closing pass, below).

gate: flagged 2026-08-18 — scope-internal judgement calls only (items 1-3
above), no MUST-FLAG trigger fired (no new dependency, no shared-interface
change beyond the one `_APPROVAL_HANDLERS` dict entry the task's own
End-State explicitly specced, no ADR deviation, no unanticipated file, no
unclear/contradictory requirement) — logged for human spot-check per the
Pipeline's own "scope-internal judgement calls go in the Implementation
Log as assumptions" rule, not an escalation.
