---
id: REQ-SB-63-US-01-T01
title: Generalize determine_placement_and_file — already_filed_path param + cross_cutting_implication detection/proposal
parent_story: REQ-SB-63-US-01
requirement_id: REQ-SB-63
type: backend
status: Done
gate: flagged
gate_reason: "trigger-1 (material assumption) — carried from the parent story's architect pass (the concrete shape of the deferred cross-reference write this task implements was designed, not spec'd by the PRD). No decomposer-owned trigger fired on this task itself. See REVIEW-QUEUE.md."
phase: P1
depends_on: []
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-63-US-01-T01 — Generalize `determine_placement_and_file`

## Parent Story

- Story: [[REQ-SB-63-US-01]] — `../UserStories/REQ-SB-63-US-01-the-librarian-vault-expert-central-authority.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-63 *The Librarian — Vault Expert as the Central Placement/Restructuring/Enrichment Authority for the New KB Pipelines*

---

## Objective

Add an additive, keyword-only `already_filed_path: str | None = None` parameter to `vault_filing_expert.determine_placement_and_file` (skips the Tier-1/Tier-2 write branch when set, linking the already-filed note instead), and an additive `cross_cutting_implication` field to the model's own JSON placement decision — re-checked in Python against the live vault structure, never trusted from the model's own naming alone — creating a new, independent `propose_cross_cutting_update` Pending Approval via a new `_create_cross_cutting_proposal` sibling function whenever a valid cross-cutting implication is detected.

---

## Starting State → End State

**Before / Inputs:**
- `app/business/vault_filing_expert.py`'s `determine_placement_and_file(content, source_description, requesting_agent_id) -> dict` — reads `known_kinds`/`known_customers`/`known_partners` fresh, builds a prompt via `vault_filing_methodology.build_placement_prompt`, parses the model's JSON reply, re-checks the Tier 1/Tier 2 boundary in Python (`decision["kind"] not in known_kinds`), and either writes immediately (Tier 1, via `_unique_filename_stem`/`_placement_frontmatter`/`vault_writer.write_note`/`_link_referenced_entity`) or creates a Tier-2 Pending Approval (`_create_tier_2_proposal`, `action_id="propose_new_top_level_area"`).
- Three real, existing callers of `determine_placement_and_file`, confirmed by direct reading during the architect pass: `agents_router.py`'s chat-attachment handler, `agent_orchestration/knowledge_bootstrap.py`'s delegated-research chain, `knowledge_gap_tracking.py`'s human-answer/research-closing paths. None pass any keyword beyond the three positional args today.
- `app/business/vault_filing_methodology.py`'s `build_placement_prompt(...)` — builds the `_JSON_SCHEMA_INSTRUCTIONS` the model must reply against; has no `cross_cutting_implication` field today.
- `app/business/pending_approval_registry.create_pending_approval(agent_id, trigger, action_id, description, payload=None)` — real, already-shipped; `_create_tier_2_proposal` already composes it via a LOCAL import (never module-level, so this module loads cleanly even before that registry exists — preserve this local-import discipline for the new sibling function).

**After / Outputs:**
- `determine_placement_and_file(content, source_description, requesting_agent_id, *, already_filed_path: str | None = None) -> dict` — when `already_filed_path` is supplied and the decision resolves Tier 1 (the real, common case for this new caller — a Thread's own `kind` is always already known), skips `vault_writer.write_note` entirely and instead runs `_link_referenced_entity(already_filed_path, decision)` against that path, returning a dict shaped like the Tier-1 write result but with `"status": "linked"` and `"path": already_filed_path`. All 3 existing callers omit the new parameter — behavior byte-for-byte unchanged for them.
- `vault_filing_methodology.build_placement_prompt` and `_JSON_SCHEMA_INSTRUCTIONS` gain instructions for an additive, optional `"cross_cutting_implication"` field: `{"customer": str|null, "partner": str|null, "reason": str} | null` — set only when the content ALSO implies a KB update for a DIFFERENT, already-known customer/partner than its own primary placement; `null` otherwise. Evaluated in the SAME model completion — no second Provider round-trip.
- A new private helper (e.g. `_maybe_create_cross_cutting_proposal`) re-checks the model's own `cross_cutting_implication` in Python: the named customer/partner must (a) already appear in the SAME pre-fetched `known_customers`/`known_partners` lists, and (b) differ from the SAME decision's own `referenced_customer`/`referenced_partner`. Failing either silently discards the field (returns `None`) rather than raising or fabricating a proposal.
- A new `_create_cross_cutting_proposal(*, entity_type, entity_name, reason, already_filed_path, source_description, requesting_agent_id) -> dict`, mirroring `_create_tier_2_proposal`'s own shape exactly (local `pending_approval_registry` import, `trigger="direct"`, `action_id="propose_cross_cutting_update"`, a payload carrying `already_filed_path` (or the just-written Tier-1 path), `entity_type` (`"customer"`|`"partner"`), `entity_name`, `reason`, `source_description`).
- `determine_placement_and_file`'s own return dict gains an additive `"cross_cutting_approval_id"` key (only present when a proposal was actually created) — independent of whichever Tier-1/linked outcome the primary axis produced; both can happen for the same call.

---

## Files to Modify

- `src/backend/app/business/vault_filing_expert.py` — add the `already_filed_path` parameter, the cross-cutting re-check helper, `_create_cross_cutting_proposal`, and wire both into `determine_placement_and_file`.
- `src/backend/app/business/vault_filing_methodology.py` — add the `cross_cutting_implication` field to `_JSON_SCHEMA_INSTRUCTIONS`.

---

## Constraints

- Inherits from parent story: never a second, divergent placement implementation (`ADR-021` point 2's own precedent); the Tier 1/Tier 2 boundary stays re-checked in Python against the live vault structure, never trusted from the model's own boolean alone — apply the identical discipline to `cross_cutting_implication`.
- All 3 existing callers (`agents_router.py`, `knowledge_bootstrap.py`, `knowledge_gap_tracking.py`) must remain byte-for-byte unaffected — do not modify their own call sites; confirm by reading them, not assuming.
- When `already_filed_path` is supplied, `vault_writer.write_note` must NEVER be called — writing a second, redundant note for content the caller says is already filed would be wrong (the architect's own explicit reasoning).
- `cross_cutting_implication` is evaluated in the SAME model completion as the rest of the decision — never issue a second `model.invoke(...)` call for it.
- A `cross_cutting_implication` naming an entity NOT already present in the pre-fetched `known_customers`/`known_partners` lists must be silently discarded — a genuinely new entity is not "elsewhere"; ordinary Tier 1/2 new-entity handling already covers that case. Never raise, never fabricate a proposal for it.
- A `cross_cutting_implication` naming the SAME entity as the SAME decision's own `referenced_customer`/`referenced_partner` must be silently discarded — that entity is already mechanically hub-linked by `_link_referenced_entity`, not "elsewhere."
- `_create_cross_cutting_proposal` must mirror `_create_tier_2_proposal`'s exact shape: a LOCAL (not module-level) `pending_approval_registry` import, `trigger="direct"` (never `"background"` — a single pipeline tick can legitimately produce multiple distinct cross-cutting proposals across different content, and `"background"`'s idempotency guard would silently collapse them).
- A Tier-1 write/link outcome and a cross-cutting proposal are independent — the code must not prevent both from occurring for the same call when both conditions are genuinely met (Scenario 4's own regression guard tests only the "no spurious extra event" direction, not a false mutual exclusivity).
- The Tier-2 branch (`is_new_top_level_area`) still returns immediately via `_create_tier_2_proposal`, exactly as today — this task does NOT add cross-cutting detection inside the Tier-2 branch. No locked AC of this story exercises a chat-attachment caller's Tier-2-plus-cross-cutting combination; log this as a disclosed, non-blocking scope note in the Implementation Log, not a gap.
- Do not modify `_create_tier_2_proposal`, `finalize_new_top_level_area`, `_link_referenced_entity`, `_placement_frontmatter`, `_unique_filename_stem`, or `_parse_decision` — compose them as-is.

---

## Tests

**Manual verification steps:**
1. **[REQ-SB-63-US-01-AC-01]** Against a real, grounded `model.invoke` call (or a scoped, disclosed monkeypatch of `model_factory.resolve_agent_model` returning a stub whose `.invoke` returns a real, engineered JSON reply), call `determine_placement_and_file(content=..., source_description=..., requesting_agent_id="test", already_filed_path="/some/real/scratch-vault/thread.md")` for content resolving to a KNOWN kind. Confirm the returned dict reflects the SAME live `known_kinds`/`known_customers`/`known_partners` grounding (read fresh via `vault_writer` at call time, not hardcoded) as the unchanged, no-`already_filed_path` caller. Then engineer a reply naming a `kind` NOT in `known_kinds` — confirm it still routes to `_create_tier_2_proposal` exactly as the unmodified caller would (the Tier boundary is unchanged by this generalization).
2. **[REQ-SB-63-US-01-AC-02]** With `already_filed_path` set to a real scratch-vault note path and a decision naming a real `referenced_customer`, confirm `_link_referenced_entity` is invoked against THAT path (a real `[[wikilink]]` lands in the already-filed note's hub-linking chain) and confirm `vault_writer.write_note` was NOT called (no new note written anywhere).
3. **[REQ-SB-63-US-01-AC-03]** Engineer a model reply whose `cross_cutting_implication` names a DIFFERENT, already-known customer than the decision's own `referenced_customer` (both customers present in a real, pre-seeded `known_customers` list). Confirm a new Pending Approval now exists (`pending_approval_registry.list_pending_approvals(status="pending")`) with `action_id="propose_cross_cutting_update"` and a payload naming the entity, `reason`, and `already_filed_path` (or the just-written Tier-1 path). Confirm the returned dict's `"cross_cutting_approval_id"` matches the created record's id.
4. **[REQ-SB-63-US-01-AC-04]** Three cases, each confirming NO `propose_cross_cutting_update` approval is created (via a before/after `list_pending_approvals(status="pending")` count): (a) the engineered reply sets `cross_cutting_implication: null`; (b) it names an entity absent from the pre-fetched `known_customers`/`known_partners` lists; (c) it names the SAME entity as the SAME decision's own `referenced_customer`/`referenced_partner`. Confirm the ordinary Tier-1/linked (or Tier-2) outcome still occurs normally in each case — only the extra event is suppressed.
5. **[REQ-SB-63-US-01-AC-05]** Monkeypatch `model_factory.resolve_agent_model("vault-filing-expert")` to return `None` (the existing, already-proven Provider-unavailable induction technique for this exact function) and call `determine_placement_and_file(..., already_filed_path="/some/path.md")` — confirm the SAME `{"status": "unavailable", "message": ...}` dict already returned for the no-`already_filed_path` caller, byte-for-byte the same shape.
6. Regression: grep-confirm all 3 existing callers' call sites (`agents_router.py`, `knowledge_bootstrap.py`, `knowledge_gap_tracking.py`) are unmodified by this task, and confirm a real, un-parametered call (no `already_filed_path`) still writes a note via Tier 1 exactly as before — `vault_writer.write_note` IS called in that case.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-01** — a Job caller supplying `already_filed_path` receives a grounded placement decision governed by the SAME Tier 1/Tier 2 boundary as the unmodified caller.
- [x] **AC-02** — hub-linking runs against the ALREADY-filed note when `already_filed_path` is set; no second note is ever written.
- [x] **AC-03** — a valid cross-cutting implication (known entity, different from the decision's own primary reference) creates exactly one `propose_cross_cutting_update` Pending Approval.
- [x] **AC-04** — an absent, unknown-entity, or same-entity `cross_cutting_implication` creates NO proposal.
- [x] **AC-05** — Provider-unavailable honesty is unchanged for the new `already_filed_path` caller.
- [x] All 3 existing callers are byte-for-byte unaffected.
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The `finalize_cross_cutting_update` write handler that performs the deferred tag write on Approve — `T03`'s own job.
- The `Consult-Librarian` pipeline Job / graph wiring that actually calls this generalized function from inside `REQ-SB-55`'s pipeline — `T02`'s own job.
- Cross-cutting detection inside the Tier-2 (new-top-level-area) branch — disclosed non-blocking scope note above; no locked AC exercises this combination.

---

## Context / Notes

Full reasoning: `Implementation/Architecture/architecture.md` → "The Librarian — Vault Filing Expert generalized to a Pipeline-Job caller + cross-cutting-update detection"; `Implementation/Architecture/ADR.md` → `ADR-021` (the unmodified base mechanism, points 2 and 5), `ADR-004` (tag/folder split, applied to the new `customer/<slug>`/`partner/<slug>` cross-cutting tag convention `T03` writes). Real precedent to mirror: `_create_tier_2_proposal`/`finalize_new_top_level_area`'s own propose/finalize split — this task owns only the "propose" half for the new cross-cutting case; `T03` owns "finalize."

The gate stays `flagged` (trigger-1, carried from the parent story's architect pass) — the concrete write shape this task implements was architect-designed to fill a gap the story/PRD left open, not itself a new decomposer-owned trigger. See the story's own `## Notes` and `REVIEW-QUEUE.md` for the human-review item.

---

## Implementation Log

**Built 2026-08-16 (coder, `/implement-sprint`, `SPRINT-050`), against the
real, current `vault_filing_expert.py`/`vault_filing_methodology.py`
(`ADR-021`, `Done`) read fresh before editing, per the launching agent's
own instruction — not trusted from any stale sample.**

**Code shape:** `determine_placement_and_file` gained the additive,
keyword-only `already_filed_path: str | None = None` param exactly as
designed — when set and the decision resolves Tier 1, `vault_writer.
write_note` is never called; `_link_referenced_entity` runs against the
supplied path instead, and the result dict's `"status"` is `"linked"`
(vs. `"written"`), `"path"` echoing the supplied path. The Tier-2
(`is_new_top_level_area`) branch is untouched — still unconditionally
`_create_tier_2_proposal`, no cross-cutting evaluation on that branch
(per this task's own disclosed, non-blocking scope note). Two new
functions added: `_maybe_create_cross_cutting_proposal` (re-checks the
model's own `cross_cutting_implication` against the SAME pre-fetched
`known_customers`/`known_partners` lists and against the SAME decision's
own `referenced_customer`/`referenced_partner`, silently returns `None`
on any failure rather than raising/fabricating) and
`_create_cross_cutting_proposal` (mirrors `_create_tier_2_proposal`'s
exact shape — local `pending_approval_registry` import, `trigger=
"direct"`, `action_id="propose_cross_cutting_update"`, payload carrying
`entity_type`/`entity_name`/`reason`/`already_filed_path`/
`source_description`). Both are called from the Tier-1 write/linked
branch only, after the primary outcome is resolved — independent of it,
never mutually exclusive (both can fire on the same call).
`vault_filing_methodology._JSON_SCHEMA_INSTRUCTIONS` gained the additive
`"cross_cutting_implication"` key description, evaluated in the SAME
completion (no second `model.invoke`).

**Scope-internal judgement call, logged for spot-check (not an
escalation — no locked AC weakened, no new dependency, no ADR
deviation):** when the model's engineered `cross_cutting_implication`
names BOTH `"customer"` and `"partner"` non-null (a malformed reply the
prompt instructs against but does not mechanically prevent), the helper
picks `"customer"` and silently ignores the `"partner"` value, rather
than raising or discarding the whole implication. Not exercised by any
locked AC either way; a reasonable, conservative interpretation of "never
raise, never fabricate" applied to a case the task's own text did not
explicitly enumerate.

**Verification technique, disclosed per the task's own Tests block
option:** all scenarios below used a scoped, in-process monkeypatch of
`model_factory.resolve_agent_model` returning a stub whose `.invoke(...)`
returns an engineered JSON reply (reverted after each run) — chosen over
a real live model call so the known-vs-unknown-entity / same-entity /
null cross-cutting cases could be deterministically engineered rather
than hoped for from a real completion. `vault_writer` /
`customer_hub_linking` / `partner_hub_linking` / `pending_approval_
registry` were all REAL and unmocked throughout — only the model call
itself was stubbed. Run against the real, configured vault
(`<OPERATOR_VAULT_OLD>`), mirroring `REQ-SB-35-US-01-T02`'s
own established precedent for this exact module. A real, already-filed
scratch "Thread" note was created first at
`Work/Threads/test-librarian-t01-scratch-thread.md` (mirrors `REQ-SB-55`'s
own `Work/Threads/<slug>.md` shape) to stand in for the new Job caller's
own already-filed content.

- **[AC-01]** Real, live-fetched `known_kinds`/`known_customers`/
  `known_partners` confirmed (`Emails` in `known_kinds`, `ADNOC`/`Masdar`
  in `known_customers`). Engineered decision `kind="Emails"` (a known
  kind) with `already_filed_path` set → `{"status": "linked", "path":
  <the scratch Thread path>, "kind": "Emails", ...}`. Engineered decision
  `kind="Totally-New-Unseen-Kind-T01Test"` (absent from `known_kinds`),
  same `already_filed_path` set → `{"status": "pending_approval",
  "approval_id": ...}`; the real created record's `action_id` confirmed
  `"propose_new_top_level_area"` — the Tier boundary is unaffected by
  `already_filed_path`. **PASS.**
- **[AC-02]** Engineered decision `referenced_customer="ADNOC"`,
  `already_filed_path` set to the real scratch Thread path. A live spy on
  `vault_writer.write_note` confirmed **0 calls** during this call. The
  scratch Thread note's own body, read back from disk after the call,
  now contains a real `**Customer:** [[ADNOC]]` line (confirmed present
  before was absent) — `_link_referenced_entity` ran against the
  ALREADY-FILED path, no second note was ever written anywhere. **PASS.**
- **[AC-03]** Engineered decision `referenced_customer="ADNOC"`,
  `cross_cutting_implication={"customer": "Masdar", "partner": null,
  "reason": "..."}` (both real, already-known, genuinely different
  customers). A before/after `list_pending_approvals(status="pending")`
  diff confirmed exactly one new record, `action_id=
  "propose_cross_cutting_update"`, payload `{"entity_type": "customer",
  "entity_name": "Masdar", "reason": "...", "already_filed_path": <the
  scratch Thread path>, "source_description": "TEST-AC03"}`. The
  returned dict's `"cross_cutting_approval_id"` matched the created
  record's real `"id"`. **PASS.**
- **[AC-04]** Three cases, each via a live before/after pending-count
  check: (a) `cross_cutting_implication: null` → count unchanged,
  ordinary `"linked"` outcome occurred, no `cross_cutting_approval_id`
  key present; (b) `cross_cutting_implication` naming `"Totally Unknown
  Customer T01Test"` (absent from `known_customers`) → count unchanged,
  same ordinary outcome; (c) `cross_cutting_implication` naming `"ADNOC"`
  — the SAME entity as this SAME decision's own `referenced_customer`
  → count unchanged, same ordinary outcome. All three: only the extra
  event was suppressed, the ordinary Tier-1/linked outcome occurred
  normally in every case. **PASS.**
- **[AC-05]** `model_factory.resolve_agent_model` monkeypatched to return
  `None`; called with `already_filed_path` set to a real path → `{
  "status": "unavailable", "message": "The Vault Filing Expert's selected
  Provider is not available."}` — confirmed byte-for-byte identical to
  the dict literal this same function already returns for the unmodified,
  no-`already_filed_path` caller (direct source comparison, same literal
  string). **PASS.**
- **Regression (all 3 existing callers, and the ordinary no-param
  path):** `Grep` across `src/backend` confirmed the only 3 real call
  sites of `determine_placement_and_file` outside this module
  (`agents_router.py:528`, `agent_orchestration/knowledge_bootstrap.
  py:73`, `knowledge_gap_tracking.py:91`) are unmodified — each still
  calls with exactly `content=`/`source_description=`/
  `requesting_agent_id=`, no new keyword argument added by this task. A
  real, un-parametered call (engineered `kind="Emails"`, no
  `already_filed_path`) confirmed `vault_writer.write_note` called
  exactly once (live spy) and the result `{"status": "written", "path":
  <a real new Work/Emails/*.md path>, ...}` — Tier 1 for the unmodified
  caller shape is byte-for-byte unaffected. **PASS.**

Both test-created Pending Approval records (`AC-01`'s Tier-2 case,
`AC-03`'s cross-cutting case) were declined afterward
(`pending_approval_registry.resolve_pending_approval(..., "declined")`)
for cleanliness — no lingering test noise in the real operator-facing
approval queue. Two real, labelled scratch notes remain in the vault
(`Work/Threads/test-librarian-t01-scratch-thread.md`, `Work/Emails/
test-librarian-t01-regression-note.md`), left in place as live evidence
of the verification, mirroring `REQ-SB-35-US-01-T02`'s own established
precedent of not deleting verification artifacts from the trusted,
no-staging vault.

`ast.parse()` of both modified files confirmed clean. `Grep` confirms no
file outside `## Files to Modify` was edited — the 3 existing caller
files were only read.

All 5 locked ACs tagged to this task (`AC-01`..`AC-05`) verified live;
the 2 remaining checklist items ("all 3 existing callers byte-for-byte
unaffected") verified above via direct `Grep` + a live regression call.

No `ESCALATIONS.md`/`REVIEW-QUEUE.md` entry from this task itself — no
locked AC failed, no new dependency, no shared-interface change beyond
what the parent story's architect pass already designed, no ADR
deviation. `gate: flagged` stays as-is, carried unchanged from the
parent story's architect pass (trigger-1, the designed write-shape this
task implements) — a standing breadcrumb for human review, not a build
blocker.
