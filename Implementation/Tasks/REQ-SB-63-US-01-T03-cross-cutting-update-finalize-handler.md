---
id: REQ-SB-63-US-01-T03
title: finalize_cross_cutting_update — additive customer/partner tag write, dispatched via _APPROVAL_HANDLERS, never captures.md
parent_story: REQ-SB-63-US-01
requirement_id: REQ-SB-63
type: backend
status: Done
gate: flagged
gate_reason: "trigger-1 (material assumption) — carried from the parent story's architect pass (the concrete write shape this handler performs was designed, not spec'd by the PRD). No decomposer-owned trigger fired on this task itself. See REVIEW-QUEUE.md."
phase: P1
depends_on: [REQ-SB-63-US-01-T01, REQ-SB-55-US-01-T01]
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-63-US-01-T03 — `finalize_cross_cutting_update`

## Parent Story

- Story: [[REQ-SB-63-US-01]] — `../UserStories/REQ-SB-63-US-01-the-librarian-vault-expert-central-authority.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-63 *The Librarian — Vault Expert as the Central Placement/Restructuring/Enrichment Authority for the New KB Pipelines*

---

## Objective

Add `finalize_cross_cutting_update(payload: dict) -> dict` to `vault_filing_expert.py` (mirrors `finalize_new_top_level_area`'s own dispatched-on-Approve shape) and register it in `pending_approvals_router.py`'s existing `_APPROVAL_HANDLERS` table under `"propose_cross_cutting_update"` — performs the deferred write as an additive `customer/<slug>`/`partner/<slug>` tag on the already-filed note, reusing `REQ-SB-55-US-01-T01`'s new unconditional frontmatter-key setter, and NEVER writes to `captures.md` (`ADR-042`'s operator-only invariant).

---

## Starting State → End State

**Before / Inputs:**
- `T01`'s `_create_cross_cutting_proposal`, creating a Pending Approval with `action_id="propose_cross_cutting_update"` and a payload carrying `already_filed_path`, `entity_type` (`"customer"`|`"partner"`), `entity_name`, `reason`, `source_description`.
- `pending_approvals_router.py`'s real, current `_APPROVAL_HANDLERS = {"propose_new_top_level_area": vault_filing_expert.finalize_new_top_level_area, "hermes_vault_write": vault_write_tools.finalize_hermes_write}` and the Approve endpoint's own dispatch branch: `result = _APPROVAL_HANDLERS[record["action_id"]](record["payload"]); outcome_message = f"Approved — filed at {result['path']}."`
- `vault_filing_expert.finalize_new_top_level_area(payload) -> dict` — the real, already-shipped precedent this task mirrors: reuses the module's own private write primitives, operates on the payload's own stored fields, returns `{"status": "written", "path": ..., ...}`.
- `REQ-SB-55-US-01-T01`'s new unconditional frontmatter-key setter in `vault_writer.py` (overwrite-or-insert, handles list values, reused for tag-union rewrites) — read the REAL, current `vault_writer.py` at build time to confirm this function's own shipped name/signature; do not assume a name from that task's own descriptive prose.
- `vault_writer.tag_slug(text) -> str` — the public slugging function `build_tags` already uses for `customer/<slug>`/`partner/<slug>` tags; the same convention this task's own new tag must follow.
- `vault_writer.read_note(path) -> tuple[dict, str]` — real, already-shipped; returns `(frontmatter, body)`.

**After / Outputs:**
- `vault_filing_expert.finalize_cross_cutting_update(payload: dict) -> dict` — reads the note at `payload["already_filed_path"]`'s current `tags` (via `read_note`), unions in `f"{payload['entity_type']}/{vault_writer.tag_slug(payload['entity_name'])}"` (only if not already present — idempotent), writes the updated `tags` list back via `REQ-SB-55-US-01-T01`'s unconditional frontmatter-key setter, and returns a dict including at minimum `{"path": payload["already_filed_path"]}` plus an additive `"message"` key naming the entity and tag for a clearer Approve-endpoint outcome text.
- `pending_approvals_router.py` imports `finalize_cross_cutting_update` (alongside the existing `finalize_new_top_level_area` import) and adds `"propose_cross_cutting_update": vault_filing_expert.finalize_cross_cutting_update` to `_APPROVAL_HANDLERS` — a pure, additive dict entry; the two pre-existing entries are untouched.

---

## Files to Modify

- `src/backend/app/business/vault_filing_expert.py` — add `finalize_cross_cutting_update`.
- `src/backend/app/api/pending_approvals_router.py` — import `finalize_cross_cutting_update`, add the new `_APPROVAL_HANDLERS` entry.

---

## Constraints

- Inherits from parent story: NEVER writes to `captures.md` (`ADR-042`'s operator-only invariant) — the only write this handler performs is an additive tag on the note at `payload["already_filed_path"]`.
- Dispatched ONLY via the Approve endpoint's existing `_APPROVAL_HANDLERS` branch (never via `skill_registry`/`_execute_action`) — mirrors `ADR-021` point 5/`ADR-043` point 4's precedent, exactly as `REQ-SB-55-US-01-T04`'s `finalize_thread_project_routing` does.
- Must reuse `REQ-SB-55-US-01-T01`'s own new unconditional frontmatter-key setter for the tags write — read the real, current `vault_writer.py` at build time to confirm that function's real, shipped name/signature (this codebase's own established "compose around the REAL current file" precedent, `Learnings.md`, `SPRINT-020`/`021`/`027`/`048`) — never a raw file write, never `insert_frontmatter_key_if_missing` (which would silently no-op if `tags` is already present).
- The tag write must be additive/idempotent — union the new `customer/<slug>` or `partner/<slug>` tag into the note's EXISTING `tags` list, never replacing or dropping any already-present tag, and never duplicating the tag if this handler runs twice for the same note/entity (e.g. a re-approval retry).
- Must use `vault_writer.tag_slug` for the entity-name-to-slug conversion — the SAME public slugging function `build_tags` already uses — never a second, divergent slugging implementation.
- Return shape must include a `"path"` key at minimum (the Approve endpoint's own current `outcome_message` fallback reads `result['path']`) — a `"message"` key is additive/optional (used automatically once `REQ-SB-55-US-01-T04`'s own `outcome_message` generalization lands). This task's own correctness must not depend on whether that generalization has already landed at build time — its return dict must produce a correct, non-crashing outcome message either way; disclose in the Implementation Log which case was actually observed live.
- Do not modify `_create_tier_2_proposal`, `finalize_new_top_level_area`, `determine_placement_and_file`, `_create_cross_cutting_proposal`, or `_maybe_create_cross_cutting_proposal` — compose `T01`'s payload shape as-is.
- Do not modify `list_pending_approvals`/`get_pending_approval`/`resolve_pending_approval`/`decline_pending_approval` or either pre-existing `_APPROVAL_HANDLERS` entry — additive dict entry only.

---

## Tests

**Manual verification steps:**
1. **[REQ-SB-63-US-01-AC-03]** Against a real scratch-vault note with an existing `tags` list, create a real `propose_cross_cutting_update` Pending Approval (via `T01`'s `_create_cross_cutting_proposal`, or a synthetic record shaped identically) naming that note's path as `already_filed_path`. Call `finalize_cross_cutting_update(payload)` directly (or via `POST /pending-approvals/{id}/approve`) — confirm the note's `tags` now include the new `customer/<slug>` or `partner/<slug>` tag, confirm every previously-present tag is still present (union, not replace), and confirm `captures.md` (if present in the scratch vault) was not touched at all — read its own mtime/content before and after to confirm.
2. Confirm idempotency: call `finalize_cross_cutting_update` a second time with the SAME payload — confirm the tag is not duplicated in the resulting `tags` list.
3. Regression: confirm approving an EXISTING, already-shipped `propose_new_top_level_area` or `hermes_vault_write` Pending Approval still resolves correctly and that `_APPROVAL_HANDLERS`' two pre-existing entries are unaffected — the dict has exactly one new key added, nothing else changed.
4. Confirm the returned dict includes a `"path"` key naming the already-filed note, and that a real `POST /pending-approvals/{id}/approve` call against this new record produces a real, non-crashing `outcome_message` string — record in the Implementation Log whether `REQ-SB-55-US-01-T04`'s own `outcome_message` generalization had already landed at the time this was verified (both outcomes are correct; disclose which was actually observed, per this codebase's own honest-disclosure discipline).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-03** (finalize half) — approving a `propose_cross_cutting_update` record writes the additive tag onto the already-filed note, never touches `captures.md`.
- [x] The tag write is additive/idempotent — no previously-present tag lost, no duplicate on a repeat approval.
- [x] `vault_writer.tag_slug` reused for slugging — no divergent slug logic.
- [x] The router's `_APPROVAL_HANDLERS` addition is strictly additive — both pre-existing entries unaffected.
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The cross-cutting detection/proposal-creation logic itself (the "propose" half) — `T01`'s own scope.
- The `Consult-Librarian` pipeline Job / graph wiring — `T02`'s own scope.
- Any UI affordance for reviewing a cross-cutting proposal beyond the existing generic Pending Approvals card — no new screen (parent story's own Affected Screens: None).
- Whether `REQ-SB-57`'s own future Synthesizer actually scans for this tag convention — an honest, disclosed forward dependency named in the parent story's own `## Notes`, not this task's own scope to resolve.

---

## Context / Notes

Full reasoning: `Implementation/Architecture/architecture.md` → "The Librarian — Vault Filing Expert generalized to a Pipeline-Job caller + cross-cutting-update detection"; `Implementation/Architecture/ADR.md` → `ADR-021` point 5 (the propose/finalize dispatch-table pattern this task reuses verbatim), `ADR-004` (the tag/folder split — `customer`/`partner` are tags, never folders), `ADR-042` (`captures.md`'s operator-only invariant this task must not violate). Real precedent to mirror: `finalize_new_top_level_area`'s own `_APPROVAL_HANDLERS`-dispatched, payload-driven "finish the deferred write on Approve" shape — confirmed by direct reading of the real, current `vault_filing_expert.py` this pass, not assumed.

The gate stays `flagged` (trigger-1, carried from the parent story's architect pass). See the story's own `## Notes` and `REVIEW-QUEUE.md` for the human-review item.

---

## Implementation Log

**2026-08-16 — coder pass.**

**Real, current state read before writing (per this codebase's own
"compose around the REAL current file" precedent):**
- `vault_filing_expert.py`'s `_create_cross_cutting_proposal` payload
  shape confirmed by direct reading: `{"entity_type", "entity_name",
  "reason", "already_filed_path", "source_description"}` — exactly what
  `finalize_cross_cutting_update` was built against.
- `REQ-SB-55-US-01-T01`'s unconditional frontmatter-key setter confirmed
  as the real, already-shipped `vault_writer.upsert_frontmatter_key(path,
  key, value) -> bool` (overwrite-or-insert; `False` only when the key
  is already present with an identical value) — NOT a new function, as
  the parent task's own `depends_on` note anticipated.
- `pending_approvals_router.py`'s real `_APPROVAL_HANDLERS` table
  confirmed to already carry 4 entries (`propose_new_top_level_area`,
  `hermes_vault_write`, `route_thread_to_project`,
  `propose_recurring_pipeline`) at build time, and its Approve branch
  already reads `result.get("message") or f"Approved — filed at
  {result['path']}."` — the `REQ-SB-55-US-01-T04` `outcome_message`
  generalization was ALREADY LANDED at build time (disclosed per the
  task's own Constraints section — this task's correctness does not
  depend on this fact either way, but this is the case actually
  observed live).
- `email_classification.py`'s `finalize_thread_project_routing` read as
  the real, exact "payload-driven deferred write" precedent to mirror —
  including its `Path(payload["..._path"])` conversion pattern (since
  `vault_writer.read_note`/`upsert_frontmatter_key` require a `Path`,
  not a bare string).

**Built:** `vault_filing_expert.finalize_cross_cutting_update(payload)`
— reads the already-filed note's current `tags` via `read_note`, unions
in `f"{entity_type}/{tag_slug(entity_name)}"` only if absent, writes back
via `upsert_frontmatter_key` only when a write is actually needed (skips
entirely on the idempotent no-op case), returns `{"path": ...,
"message": ...}`. Registered `"propose_cross_cutting_update":
vault_filing_expert.finalize_cross_cutting_update` as a pure, additive
`_APPROVAL_HANDLERS` dict entry in `pending_approvals_router.py` — no
new import statement needed since `vault_filing_expert` was already
imported as a module (mirroring how `finalize_new_top_level_area` is
already referenced via `vault_filing_expert.finalize_new_top_level_area`
rather than a separate name import).

**Verification (manual mode — `n/a — test tooling pending`, no automated
suite exists for this dispatch table yet):** ran a scratch script against
a temp-directory vault (`settings.vault_path` pointed at a throwaway
`tempfile.mkdtemp()` dir via env var, never the real vault) —

- **[REQ-SB-63-US-01-AC-03]** PASS. Created a real
  `propose_cross_cutting_update` Pending Approval (via
  `pending_approval_registry.create_pending_approval`, payload shaped
  identically to `_create_cross_cutting_proposal`'s own real output)
  naming a scratch note with pre-existing `tags: ["kind/project",
  "customer/acme-corp"]`. Called `finalize_cross_cutting_update(payload)`
  directly. Observed: the note's `tags` became `["kind/project",
  "customer/acme-corp", "partner/globex-partners"]` — both
  previously-present tags intact, new tag present, correctly slugged.
  A `captures.md` placed in the same scratch vault was confirmed
  byte-identical in content AND unchanged `mtime` before/after the call
  — never touched.
- **Idempotency (Tests step 2).** PASS. Called
  `finalize_cross_cutting_update` a second time with the SAME payload —
  resulting `tags` list unchanged (`partner/globex-partners` appears
  exactly once, no duplicate, no write performed on the second call
  since the union found it already present).
- **Regression (Tests step 3).** PASS. Confirmed
  `pending_approvals_router._APPROVAL_HANDLERS` holds exactly 5 keys
  after the change (`propose_new_top_level_area`, `hermes_vault_write`,
  `route_thread_to_project`, `propose_recurring_pipeline`,
  `propose_cross_cutting_update`), and that
  `_APPROVAL_HANDLERS["propose_new_top_level_area"] is
  vault_filing_expert.finalize_new_top_level_area` (object identity,
  unchanged) — the 4 pre-existing entries are untouched, one new key
  added.
- **Full Approve round trip (Tests step 4).** PASS. Called
  `pending_approvals_router.approve_pending_approval(approval_id)`
  directly (the real function the `POST /pending-approvals/{id}/approve`
  route delegates to) against a fresh, second scratch note/record —
  resolved to `"approved"` with no crash, the note's `tags` correctly
  gained `customer/initech` alongside its pre-existing `kind/project`
  tag. The returned handler dict included `"path"` (required minimum)
  and an additive `"message"` key; confirmed live that the router's own
  `outcome_message` generalization (`REQ-SB-55-US-01-T04`) had ALREADY
  LANDED at the time of this verification, so the richer
  entity/tag-naming message text is what actually renders in
  `outcome_message` — not the generic `f"Approved — filed at
  {result['path']}."` fallback (both are disclosed-correct per the
  task's own Constraints; this is the case actually observed).

Scratch vault removed after verification (`shutil.rmtree`) — no
persistent state left outside the temp directory; the real vault was
never touched by this verification pass.

**Assumption logged for spot-check (scope-internal judgement call, not
an escalation):** the write is skipped entirely (no `upsert_frontmatter_
key` call at all) when the union find the tag already present, rather
than always calling `upsert_frontmatter_key` unconditionally with the
same resulting list. Both are correct/idempotent; skipping the call
avoids an unnecessary file rewrite on a no-op repeat-approval, matching
`upsert_frontmatter_key`'s own documented "returns False ... a true
no-op" contract one layer up.

**Files touched (exactly the two named in `## Files to Modify`, nothing
else):** `src/backend/app/business/vault_filing_expert.py`,
`src/backend/app/api/pending_approvals_router.py`. `_create_tier_2_
proposal`, `finalize_new_top_level_area`, `determine_placement_and_file`,
`_create_cross_cutting_proposal`, `_maybe_create_cross_cutting_proposal`,
`list_pending_approvals`/`get_pending_approval`/`resolve_pending_
approval`/`decline_pending_approval`, and both pre-existing
`_APPROVAL_HANDLERS` entries were only read, never modified — confirmed
by direct diff review.

**Outcome: all locked ACs tagged to this task verified. Task marked
`Done`.** `gate` stays `flagged` (trigger-1, carried unchanged from the
parent story's architect pass — a standing breadcrumb awaiting human
confirmation of the designed write-shape, not a build blocker; no new
`ESCALATIONS.md`/`REVIEW-QUEUE.md` entry from this task itself). The
parent story `REQ-SB-63-US-01` is NOT yet marked `Done` — `T02` (the
`Consult-Librarian` pipeline wiring) remains `status: Ready`, still
outstanding.
