---
id: REQ-SB-04-US-01-T02
title: Write-capable MCP tool (`propose_vault_write`) + Pending Approvals plumbing (`trigger="hermes"`, `hermes_vault_write` Approve handler)
parent_story: REQ-SB-04-US-01
requirement_id: REQ-SB-04
type: backend
status: Done
gate: clear
gate_reason: "Individually clear (no MUST-FLAG trigger of its own); parent story's own trigger-3 flag (ADR-025 created) was already resolved before this build pass began (ADR-025 Accepted, reviewed 2026-08-13). AC-03/AC-04 verified live against the real backend via the seeded-pending-approval technique this task's own Tests block specifies; the fail-closed scope gate was additionally confirmed live via a real end-to-end MCP tool call (Scenario 2's own shape — honest rejection, not fabricated pending). No new trigger fired during the build itself."
phase: P1
depends_on: [REQ-SB-04-US-01-T01]
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-04-US-01-T02 — Write-capable MCP tool + Pending Approvals plumbing

## Parent Story

- Story: [[REQ-SB-04-US-01]] — `../UserStories/REQ-SB-04-US-01-agent-vault-write-access.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-04 *Agent Vault Write Access*

---

## Objective

Register a write-capable MCP tool that never writes directly — it always
proposes a Pending Approval (new `trigger="hermes"`) — and wire the
Approve/Decline mechanics so an approved proposal actually lands via
`vault_writer.write_note`, and a declined one is honestly discarded
(`ADR-025` points 4-5). Includes a fail-closed scope-check seam whose real
implementation is `T03`'s own (currently blocked) scope.

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed the `/mcp` shared-secret auth mechanism this tool's
  own reachability depends on.
- `app/business/pending_approval_registry.py`
  (`create_pending_approval(agent_id, trigger, action_id, description,
  payload=None)`, `resolve_pending_approval`) and `app/api/
  pending_approvals_router.py` (`_APPROVAL_HANDLERS` dispatch table,
  `approve_pending_approval`/`decline_pending_approval` endpoints) already
  exist and are `Done` (`REQ-SB-21-US-01`, `ADR-018`/`ADR-020`/`ADR-021`).
- `app/data_access/vault_writer.write_note(subfolder, filename_stem,
  frontmatter, body) -> str` already exists — the generic write primitive
  this task's Approve handler calls.
- `app/business/agent_registry.get_agent(agent_id) -> dict | None`
  already exists — the known-agent lookup this task's tool uses.

**After / Outputs:**
- New `app/business/vault_write_tools.py`:
  - `propose_vault_write(agent_id: str, subfolder: str, filename_stem:
    str, frontmatter: dict, body: str) -> dict` — rejects an unknown
    `agent_id` outright (`{"status": "rejected", "message": ...}`); for a
    known agent, calls `_is_within_assigned_scope(agent_id, subfolder,
    frontmatter)` (this task's own stub — see Constraints); if `False`,
    rejects with an honest message naming the missing scope assignment;
    if `True` (unreachable until `T03`), calls
    `pending_approval_registry.create_pending_approval(agent_id,
    trigger="hermes", action_id="hermes_vault_write", description=...,
    payload={"subfolder": subfolder, "filename_stem": filename_stem,
    "frontmatter": frontmatter, "body": body})` and returns
    `{"status": "pending", "message": ..., "pending_approval_id":
    record["id"]}`.
  - `_is_within_assigned_scope(agent_id: str, subfolder: str,
    frontmatter: dict) -> bool` — **always returns `False`** (fail-closed
    stub, per `ADR-025` point 6 — see Constraints). `T03` replaces this
    function's body once `REQ-SB-29-US-01` ships a real scope registry.
  - `finalize_hermes_write(payload: dict) -> dict` — calls
    `vault_writer.write_note(payload["subfolder"], payload
    ["filename_stem"], payload["frontmatter"], payload["body"])`, returns
    `{"path": <the written path>}`.
- `app/api/mcp_server.py` registers `propose_vault_write` as a fifth
  `@mcp_server.tool()` (docstring explains the fail-closed scope gate
  honestly, per `ADR-025` point 4).
- `app/api/pending_approvals_router.py`'s `_APPROVAL_HANDLERS` gains
  `"hermes_vault_write": vault_write_tools.finalize_hermes_write`.

---

## Files to Modify

- `src/backend/app/business/vault_write_tools.py` (new) — as described
  above.
- `src/backend/app/api/mcp_server.py` — register the new tool.
- `src/backend/app/api/pending_approvals_router.py` — one new
  `_APPROVAL_HANDLERS` entry.

---

## Constraints

- Inherits from parent story and `ADR-025` points 4-6.
- `_is_within_assigned_scope` **must return `False` unconditionally** in
  this task — this is a deliberate, documented fail-closed placeholder,
  not a bug. Do not implement any real scope-matching logic here; do not
  make it return `True` for any input, including a hardcoded test agent —
  that would silently reopen the exact "fail-open" hazard `ADR-025`'s own
  Alternatives Considered explicitly rejected. `T03` (blocked on
  `REQ-SB-29-US-01`) owns the real implementation.
- `propose_vault_write` must never call `vault_writer.write_note`
  directly, under any code path — every real write happens exclusively
  through `finalize_hermes_write`, invoked only by the Approve endpoint.
- `propose_vault_write` must never consult `working_mode_registry` —
  Hermes-originated writes are unconditionally gated by Pending Approvals
  regardless of the target agent's own working mode (`ADR-025` point 4).
- `create_pending_approval`'s call here uses `trigger="hermes"` exactly —
  do not reuse `"chat"`/`"direct"`/`"background"`/`"hub_routed"`.
- Do not modify `pending_approval_registry.py`'s own idempotency logic —
  `"hermes"` is never deduplicated (the existing `trigger ==
  "background"`-only guard already excludes it with zero code change).

---

## Tests

<!-- AC-03/AC-04 do not depend on the scope check (Scenario 3/4's own
substance is the confirm/decline mechanic, not scope-matching) -- verified
here directly against the pending_approval_registry/router layer, seeding
a "hermes" record directly rather than through propose_vault_write's own
(deliberately fail-closed) front door. Honest, disclosed scope: this
verifies the confirm/decline PLUMBING for a hermes-triggered proposal, not
propose_vault_write's own real end-to-end scope decision, which is
structurally unreachable until T03. AC-01/AC-02 (the scope-dependent
Scenarios) are NOT tested here -- see T03. -->

**Manual verification steps:**
1. Non-AC smoke check: call `vault_write_tools.propose_vault_write(
   "vault-qa", "Notes", "test-hermes-write", {"kind": "Note"}, "body")`.
   Confirm `{"status": "rejected", ...}` is returned (the fail-closed
   scope stub) and confirm no file was created under
   `Work/Notes/test-hermes-write.md`.
2. Non-AC smoke check: call `vault_write_tools.propose_vault_write(
   "not-a-real-agent", "Notes", "x", {}, "body")`. Confirm
   `{"status": "rejected", ...}` naming the unknown agent, and that this
   path is reached before any scope-check code runs (e.g. via a temporary
   print/log, removed before commit).
3. **[REQ-SB-04-US-01-AC-03]** Directly seed a pending record:
   `pending_approval_registry.create_pending_approval("vault-qa",
   "hermes", "hermes_vault_write", "Hermes-proposed write: Notes/
   test-hermes-write", payload={"subfolder": "Notes", "filename_stem":
   "test-hermes-write", "frontmatter": {"kind": "Note"}, "body": "Test
   body."})`. Call `GET /pending-approvals/{id}` — confirm `status:
   "pending"`. Confirm no file exists yet at
   `Work/Notes/test-hermes-write.md`. Call
   `POST /pending-approvals/{id}/approve` — confirm the response's
   `status: "approved"`, confirm `Work/Notes/test-hermes-write.md` now
   exists with the exact frontmatter/body supplied, and confirm a
   `run_event` history entry was appended for `vault-qa` naming the
   written path.
4. **[REQ-SB-04-US-01-AC-04]** Seed a second pending record (same shape
   as step 3, a different `filename_stem`, e.g. `test-hermes-write-2`).
   Call `POST /pending-approvals/{id}/decline` — confirm the response's
   `status: "declined"`, confirm **no** file was created at
   `Work/Notes/test-hermes-write-2.md`, and confirm a `run_event` history
   entry ("Declined — no action taken") was appended for `vault-qa`.
5. Clean-up: delete both `Work/Notes/test-hermes-write*.md` files and any
   `.second-brain/agent_pending_approvals.json` records this step's own
   test created (or leave the resolved records — matching the existing
   precedent that resolved records are not pruned automatically).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-03** — a proposed write held as `"pending"` is not applied
      until an explicit approval; approving it calls
      `vault_writer.write_note` with the record's own stored payload and
      the resulting note appears in the vault
- [x] **AC-04** — declining a pending proposal discards it; no note is
      created or modified, and the agent/user is informed via a history
      entry
- [x] `propose_vault_write` rejects an unknown `agent_id` outright, with
      no pending record created
- [x] `propose_vault_write` never calls `vault_writer.write_note`
      directly under any code path
- [x] `propose_vault_write` never consults `working_mode_registry`
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `/mcp` authentication — `T01`.
- The real scope-match implementation (`_is_within_assigned_scope`'s real
  body) — `T03`, blocked on `REQ-SB-29-US-01`.
- **AC-01 (Scenario 1) and AC-02 (Scenario 2) — both require a real
  in-scope/out-of-scope decision, which does not exist until `T03`
  ships.** This task's own Tests block deliberately does not attempt to
  verify either through `propose_vault_write`'s own front door — see
  `T03`.
- Frontend presentation of a Hermes-sourced proposal on the Pending
  Approvals surface (visual distinction from a background-pipeline
  proposal) — left to `/design`, not this task; the `trigger` field is
  already present on every record `GET /pending-approvals` returns, so no
  further backend change is needed for a future frontend task to consume
  it.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-025` created at
`/plan-tasks` step 1) — the human reviews `ADR-025` and this story's task
breakdown together; the pipeline does not halt, so this task proceeds to
`Ready` alongside `T01` (and holds `T03` individually blocked — see that
task's own Notes).

**Why AC-01/AC-02 are not tagged here despite Scenario 1's own "lands in
the vault" language overlapping this task's own Approve-mechanics
test:** the parent story's own `## Notes` (and `ESCALATIONS.md` →
`ESC-026`) are explicit that Scenarios 1 and 2 specifically are the two
scope-dependent scenarios — this task's step 3 above exercises the exact
same Approve code path Scenario 1 describes, but does so by directly
seeding a `"hermes"` pending record rather than through
`propose_vault_write`'s own real scope decision (which is structurally
unreachable in this task, by design). Tagging `AC-01` here would
overstate what was actually verified; the honest tag lives on `T03`,
where the real scope decision exists.

---

## Implementation Log

**Built exactly per `ADR-025` points 4-6, no deviation.** New
`app/business/vault_write_tools.py`: `propose_vault_write(agent_id,
subfolder, filename_stem, frontmatter, body)` — rejects an unknown
`agent_id` outright (checked via `agent_registry.get_agent`, before any
scope-check code runs); for a known agent, calls
`_is_within_assigned_scope(agent_id, subfolder, frontmatter)` (this task's
own stub — **always returns `False`**, per `ADR-025` point 6, with a
docstring naming exactly why and what `T03` replaces it with — never
implements real matching logic, never returns `True` for any input); if
`False` (today, unconditionally), rejects with an honest message naming
the missing scope assignment; if `True` (structurally unreachable until
`T03`), calls `pending_approval_registry.create_pending_approval(agent_id,
trigger="hermes", action_id="hermes_vault_write", ...)` and returns
`{"status": "pending", ..., "pending_approval_id": ...}`.
`finalize_hermes_write(payload)` calls `vault_writer.write_note(...)` and
returns `{"path": ...}` — the ONLY function in this module that ever calls
`write_note`; `propose_vault_write` itself never does, under any code
path (confirmed by direct code inspection — zero references). No
reference to `working_mode_registry` anywhere in this module (confirmed by
grep, zero matches — mirrors `vault_filing_expert.py`'s own `ADR-021`
precedent). `app/api/mcp_server.py` registers `propose_vault_write` as a
fifth `@mcp_server.tool()`, docstring honestly explains the fail-closed
scope gate. `app/api/pending_approvals_router.py`'s `_APPROVAL_HANDLERS`
gained `"hermes_vault_write": vault_write_tools.finalize_hermes_write` —
`create_pending_approval`'s own `trigger == "background"`-only idempotency
guard needed zero code change to leave `"hermes"` un-deduplicated (already
true by construction); decline needed zero new code (the existing
`decline_pending_approval` endpoint already resolves any `"pending"`
record regardless of `action_id`/`trigger`).

**Live verification (same real backend/port 8001 as `T01`, restarted once
to load this task's new code — a real, unrelated real-vault race
condition, an already-deleted file another concurrent session's own
throwaway artifact had briefly left referenced during one boot attempt's
own app-start capture pass, caused one transient boot failure entirely
outside this task's own file scope; a plain retry against the now-stable
vault state booted cleanly, confirming it was a one-off race, not a defect
in this task's own code):**

1. *Non-AC smoke check 1* — direct call,
   `vault_write_tools.propose_vault_write("vault-qa", "Notes",
   "test-hermes-write", {"kind": "Note"}, "body")` →
   `{"status": "rejected", "message": "'vault-qa' has no assigned vault
   scope covering 'Notes' -- write refused (no REQ-SB-29 scope registry
   exists yet, so every write is currently out of scope)."}`; confirmed no
   file at `Work/Notes/test-hermes-write.md`. **PASS**.
2. *Non-AC smoke check 2* — direct call,
   `propose_vault_write("not-a-real-agent", "Notes", "x", {}, "body")` →
   `{"status": "rejected", "message": "Unknown agent 'not-a-real-agent' --
   write refused."}`, naming the unknown agent; confirmed by direct code
   reading (not a temporary print) that the `agent_registry.get_agent`
   check is the first statement in the function, before
   `_is_within_assigned_scope` is ever called. **PASS**.
3. **`[REQ-SB-04-US-01-AC-03]`** — seeded a `"hermes"` pending record
   directly via `pending_approval_registry.create_pending_approval`
   (`vault-qa`, payload `{subfolder: "Notes", filename_stem:
   "test-hermes-write", frontmatter: {"kind": "Note"}, body: "Test
   body."}`). `GET /pending-approvals/{id}` → `status: "pending"`;
   confirmed no file existed yet at `Work/Notes/test-hermes-write.md`.
   `POST /pending-approvals/{id}/approve` → response `status: "approved"`;
   `Work/Notes/test-hermes-write.md` now exists, contents exactly
   `---\nkind: "Note"\n---\n\nTest body.` (the exact supplied
   frontmatter/body); `GET /agents/vault-qa/history` shows a new
   `run_event` entry, `"Approved — filed at
   C:\myWorx\Moussa MD\Moussa Brain\Notes\test-hermes-write.md."`.
   **PASS — fully verified.**
4. **`[REQ-SB-04-US-01-AC-04]`** — seeded a second `"hermes"` pending
   record (`test-hermes-write-2`). `POST /pending-approvals/{id}/decline`
   → response `status: "declined"`; confirmed **no** file at
   `Work/Notes/test-hermes-write-2.md`; `GET /agents/vault-qa/history`
   shows a new `run_event` entry, `"Declined — no action taken"`.
   **PASS — fully verified.**
5. *Clean-up* — `Work/Notes/test-hermes-write.md` deleted (the declined
   case never created one). Both resolved pending-approval records left
   in place, matching the existing precedent that resolved records are not
   pruned automatically.

**Additional real end-to-end check, beyond this task's own named Tests
(requested explicitly for this build pass, honest disclosure of exactly
what it does and doesn't prove):** a genuine `propose_vault_write` MCP
tool call, over the real loopback client
(`streamablehttp_client("http://127.0.0.1:8001/mcp")`, the same real
transport an in-app agent or a real Hermes caller would use), with
`agent_id="vault-qa"`, a real subfolder/filename/frontmatter/body →
`isError: false`, `content: {"status": "rejected", "message": "'vault-qa'
has no assigned vault scope covering 'Notes' -- write refused (no
REQ-SB-29 scope registry exists yet, so every write is currently out of
scope)."}`; confirmed no file was created for that attempt. This is
honestly **Scenario 2's own shape** (a real invocation, real rejection,
clear message, no note created) — it is NOT Scenario 1/2's own *real*
scope-match decision (there is no real scope to violate or satisfy yet),
and it is deliberately not tagged `AC-01`/`AC-02` here — that honest
tagging distinction is `T03`'s own, per the parent story's `## Notes` and
`ESCALATIONS.md` → `ESC-026`. What this additional check DOES prove,
concretely: `propose_vault_write` is reachable end-to-end through the real
MCP transport (composing with `T01`'s own auth-wrapped mount) and its
fail-closed rejection is honest and clearly worded, never silently
allowed and never fabricated as `"pending"` — the exact property `ADR-025`
point 6's own Consequences section names as the honest, safe,
buildable-now state.

gate: clear 2026-08-13 — no MUST-FLAG trigger fired: no material
assumption, no ADR created/changed, no `ESCALATIONS.md` entry, both locked
ACs this task owns (`AC-03`/`AC-04`) verified live and passing; `AC-01`/
`AC-02` are correctly NOT claimed here (they remain `T03`'s own, blocked,
per the story's own already-recorded, confirmed-acceptable judgement
call).
