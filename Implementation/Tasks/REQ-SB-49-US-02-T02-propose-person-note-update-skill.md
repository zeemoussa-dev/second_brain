---
id: REQ-SB-49-US-02-T02
title: New mutating Skill propose_person_note_update — skill_tools.py entry/handler + skill_registry.py grant to people-producer
parent_story: REQ-SB-49-US-02
requirement_id: REQ-SB-49
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-038 created) — carried from the parent story; the human reviews ADR-038 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: [REQ-SB-49-US-02-T01, REQ-SB-49-US-02-T03]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-49-US-02-T02 — New Mutating Skill `propose_person_note_update`

## Parent Story

- Story: [[REQ-SB-49-US-02]] — `../UserStories/REQ-SB-49-US-02-cockpit-person-mention-proposed-note-edit.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-49 *Cockpit @Mentions*

---

## Objective

Register a new `mutates: True` Skill, `propose_person_note_update`, on `skill_tools.SKILLS` with a real `@mcp_server.tool()`-decorated handler that branches on the new `already_approved` flag (`T04`'s own seam) — writes directly via `vault_writer` when `True` (Supervised-approved), or records a `T01`-backed in-thread proposal when `False` (Manual/Autonomous direct dispatch) — and grant it to `people-producer` via `skill_registry.py`'s existing migration-seed/`_SKILL_HANDLERS` pattern (`ADR-038` point 3).

---

## Starting State → End State

**Before / Inputs:**
- `skill_tools.SKILLS` has 11 entries; `skill_registry._SKILL_HANDLERS`/`_MIGRATION_GRANT_SEED` mirror them 1:1 (see real current files, both already read in full for this pass).
- `T01` has landed `person_note_proposals.create_proposal(subject_kind, subject_note_stem, note_path, person_name, instruction) -> dict`.
- `T03` has landed the `"cockpit_mention"` trigger literal (used only by this task's own direct-call Tests, not by the handler's own body).
- `vault_writer.append_person_note_update_line(note_path, line) -> None` (`T01`) exists.

**After / Outputs:**
- `skill_tools.SKILLS["propose_person_note_update"]` exists, `"mutates": True`.
- `skill_tools.propose_person_note_update(note_path, person_name, instruction, agent_id, subject_kind=None, subject_note_stem=None, already_approved=False) -> dict` is a real, working `@mcp_server.tool()`-decorated handler.
- `skill_registry._SKILL_HANDLERS["propose_person_note_update"]` is wired; `_MIGRATION_GRANT_SEED["propose_person_note_update"] = ["people-producer"]` grants it.

---

## Files to Modify

- `src/backend/app/business/skill_tools.py`:
  - Add one new `SKILLS` entry, placed after `summarize-file`:
    ```python
    "propose_person_note_update": {
        "id": "propose_person_note_update",
        "name": "Propose a Person-Note Update",
        "description": (
            "Given a real, existing Person note and a described change, "
            "propose an edit reflecting it -- subject to the invoking "
            "agent's own working-mode gate; never silently applied."
        ),
        "mutates": True,
    },
    ```
  - Add the new handler, placed after `write_to_vault_draft`:
    ```python
    @mcp_server.tool()
    def propose_person_note_update(
        note_path: str,
        person_name: str,
        instruction: str,
        agent_id: str,
        subject_kind: str | None = None,
        subject_note_stem: str | None = None,
        already_approved: bool = False,
    ) -> dict:
        """Proposes (or, once already_approved, applies) one described edit
        to an already-resolved, real, existing Person note (ADR-038 points
        3/6/7). NEVER creates a Person note, NEVER guesses a match -- the
        caller (graph.py's own _propose_person_note_update node, T05) has
        already resolved note_path via a real, read-only name lookup
        before this handler is ever reached.

        already_approved=True (T04's own seam, reached only via a
        just-approved Supervised Pending Approval) -- the user's own
        "Approve" click already IS the human confirmation (Scenario 2);
        writes directly via vault_writer.append_person_note_update_line
        and returns {"status": "written", ...}.

        already_approved=False (default -- the gate's own Manual/
        Autonomous fallthrough, which has zero human click of any kind in
        its own dispatch path) -- never writes as a direct, unconfirmed
        side effect (this story's own unqualified Constraint). Records an
        explicitly confirmable/discardable in-thread proposal via
        person_note_proposals.create_proposal (T01) instead, and returns
        {"status": "proposed", "proposal_id": ..., ...}.

        The import of person_note_proposals is deliberately INSIDE this
        function body, not at module top level -- mirrors build_knowledge's
        own already-documented reason one layer over: a module-level
        import here would complete a real circular import (skill_tools ->
        person_note_proposals -> threads -> graph (T05) -> skill_registry
        -> skill_tools), confirmed by direct tracing of the real import
        graph. By the time this handler actually runs, every module in
        that chain has already finished loading, so the deferred import is
        safe.

        subject_kind/subject_note_stem are None when this handler is
        reached from a context with no owning Cockpit thread (e.g. a
        one-on-one agent chat outside any Cockpit, agents_router.py's own
        chat() -- the SAME run_agent_conversation function serves both
        call sites) -- this story's own 6 ACs are all Cockpit-scoped, so
        that case gets an honest, non-crashing refusal, never a silent
        write and never an unhandled error."""
        if already_approved:
            vault_writer.append_person_note_update_line(note_path, f"- {instruction}")
            return {
                "status": "written",
                "message": f"Updated {person_name}'s note.",
                "note_path": note_path,
            }
        if not subject_kind or not subject_note_stem:
            return {
                "status": "unavailable",
                "message": "Proposing a Person-note edit is only available inside a Cockpit chat today.",
            }
        from app.business.cockpit import person_note_proposals

        proposal = person_note_proposals.create_proposal(
            subject_kind, subject_note_stem, note_path, person_name, instruction
        )
        return {
            "status": "proposed",
            "proposal_id": proposal["id"],
            "message": f"Proposed an update to {person_name}'s note — awaiting confirmation.",
            "note_path": note_path,
        }
    ```
  - Add import: `from app.data_access import anthropic_client, compass_client, vault_writer` (merge `vault_writer` into the existing `from app.data_access import anthropic_client, compass_client` line — do not duplicate the import statement).
- `src/backend/app/business/skill_registry.py`:
  - `_SKILL_HANDLERS`: add `"propose_person_note_update": skill_tools.propose_person_note_update,` after the existing `"summarize-file": skill_tools.summarize_file,` line.
  - `_MIGRATION_GRANT_SEED`: add `"propose_person_note_update": ["people-producer"],` after the existing `"build_knowledge": ["compass-expert"],` line — mirrors `ADR-029` point 7's exact per-id, per-agent-list seeding shape, one more row, not a new mechanism.

---

## Constraints

- Inherits from parent story.
- `mutates: True` on this `SKILLS` entry — this is what makes the two-axis gate (`ADR-029` point 2) defer it under Supervised mode.
- Never write to `note_path` in the `already_approved=False` branch, under any condition — the ONLY write path in this handler is the `already_approved=True` branch.
- The deferred, function-body-local `person_note_proposals` import is mandatory (not a style choice) — a module-level import creates a real circular import; confirm this by direct import-graph tracing before writing the diff, do not assume.
- Never fabricate a match or create a Person note in this handler — `note_path` is trusted as already-resolved by the caller (`T05`'s node); this handler's own job is gate-adjacent propose/write behaviour only.
- `_MIGRATION_GRANT_SEED`/`_SKILL_HANDLERS` additions follow the exact existing dict-literal shape — no refactor of either dict's surrounding entries.

---

## Tests

<!-- AC-01 and AC-03 are both directly, deterministically verifiable at
this handler/invoke_skill layer (no LLM/model call needed) -- mirrors
REQ-SB-40-US-01-T04's own "layer-by-layer" precedent (function calls
first, real HTTP/model layer covered by T05 separately). -->

**Manual verification steps:**

1. **[REQ-SB-49-US-02-AC-01]** In a Python shell against the backend `.venv` (real vault, real `.second-brain/agent_skills.json`). Ensure `people-producer` is in Manual or Autonomous working mode (`working_mode_registry`). Pick a real, existing Person note; read and record its current body text. Call `skill_registry.invoke_skill("people-producer", "propose_person_note_update", args={"note_path": "<that note's real path>", "person_name": "<its real name>", "instruction": "test instruction — no-op check", "subject_kind": "email", "subject_note_stem": "<a real captured email note stem>"}, trigger="cockpit_mention")`. Confirm the return is `{"status": "proposed", "proposal_id": ..., ...}`. Re-read the same Person note's body — confirm it is BYTE-FOR-BYTE unchanged from the recorded value (never applied as a side effect of the dispatch itself). Clean up via `person_note_proposals.discard_proposal(...)` with the returned `proposal_id` afterward (leaves the note untouched, resolves the test proposal).
2. **[REQ-SB-49-US-02-AC-03]** Confirm, in the SAME session, that this call behaved exactly like `invoke_skill`'s existing dispatch for any other mutating Skill for Manual/Autonomous mode — no refusal, no special-cased branch: repeat step 1's `invoke_skill` call once with `people-producer` in Manual mode and once in Autonomous mode; both return `{"status": "proposed", ...}` (never `{"status": "refused", ...}`), matching the gate's own documented "falls straight through to `_dispatch_skill`" behaviour for every other mutating Skill in this codebase (cross-check: call `invoke_skill("people-producer", "rebuild_person_note", args=None, trigger="direct")` in the same Manual-mode session and confirm it also falls through, i.e. is NOT refused for a `mode == "manual"` reason — the only real Manual-mode refusal condition is `trigger == "hub_routed"`, which this capability never uses).
3. Non-AC smoke check: confirm `skill_registry.list_skills()` includes `propose_person_note_update`, `"mutates": True`. Confirm `skill_registry.has_skill_access("people-producer", "propose_person_note_update")` is `True` after the migration seed runs (any `_load_state()`-triggering call, e.g. `list_agent_skills`).
4. Static check: confirm `person_note_proposals` is imported inside `propose_person_note_update`'s own function body in `skill_tools.py`, not at module top level (grep the file).

**Automated tests:** `n/a — no backend test runner scaffolded yet (no pytest suite exists under src/backend as of this task)`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] **AC-01** (Scenario 1, handler layer) — a Manual/Autonomous dispatch never writes to the real Person note; returns a real `{"status": "proposed", "proposal_id": ...}`
- [ ] **AC-03** (Scenario 3) — Manual and Autonomous mode both dispatch this Skill exactly like any other mutating Skill (no refusal, no special-cased bypass or block)
- [ ] `propose_person_note_update` registered on `SKILLS` (`mutates: True`) and `_SKILL_HANDLERS`; granted to `people-producer` via `_MIGRATION_GRANT_SEED`
- [ ] `already_approved=True` branch writes via `vault_writer.append_person_note_update_line`; `already_approved=False` branch never writes
- [ ] `person_note_proposals` imported only inside the handler's own function body (no circular import)
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The `"cockpit_mention"` `Literal[...]` type addition itself — `T03`'s scope (this task's own Tests pass a `trigger="cockpit_mention"` string regardless, since `Literal` is not runtime-enforced — confirmed directly).
- The `_dispatch_skill(..., already_approved=...)` seam's own signature/forwarding mechanics, and the Approve-endpoint wiring that ever actually passes `already_approved=True` in production — `T04`'s scope. This task's own handler declares and branches on the parameter; it does not need `T04` landed to compile or to be tested for the `False` branch (its default).
- The real graph-level bound tool/node/name resolution that produces `note_path`/`person_name`/`instruction` from a real chat message — `T05`'s scope.
- The frontend confirm/discard UI — `T06`'s scope.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-038` created at `/plan-tasks` step 1, carried) — the human reviews `ADR-038` and the task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

**Read the REAL current `skill_tools.py`/`skill_registry.py` first** (both already read in full for this decomposer pass; re-confirm at build time per this project's own repeated Learnings finding that shared registries can drift between sibling stories) — this task's own diff is additive only: one new `SKILLS` entry, one new handler function, one new `_SKILL_HANDLERS` row, one new `_MIGRATION_GRANT_SEED` row. No existing entry/handler is touched.

**Why `already_approved`/`subject_kind`/`subject_note_stem` are all declared with defaults on this handler even though `T04` (the seam that ever passes `already_approved=True`) and `T05` (the caller that ever passes real `subject_kind`/`subject_note_stem`) build the wiring separately:** `_dispatch_skill`'s own signature-introspection auto-injection (`ADR-038` point 7, `T04`'s scope) only forwards a keyword when the resolved handler's OWN signature declares it — declaring these three keywords here, with safe defaults, is what makes both `T04`'s and `T05`'s later wiring correctly reach this handler with zero further change to this file.

---

## Implementation Log

Built exactly as specced: `SKILLS["propose_person_note_update"]`
(`mutates: True`), the `@mcp_server.tool()`-decorated handler (deferred
`person_note_proposals` import inside the function body, confirmed by
direct grep — appears nowhere else), `_SKILL_HANDLERS`/
`_MIGRATION_GRANT_SEED` rows in `skill_registry.py` (grants
`people-producer`).

**One real, disclosed reconciliation against the REAL current file:**
the task's own illustrative `SKILLS` entry sample omitted a `"tool"`
field — but the REAL current `skill_tools.SKILLS` (as landed by
`REQ-SB-48-US-01-T01`, before this sprint) requires every entry to carry
one: `skill_registry.list_agent_capabilities` does
`skill["tool"]` unconditionally for every granted Skill. Confirmed live
(`KeyError: 'tool'` on a real `PATCH /agents/people-producer` call the
moment `people-producer` was granted this Skill via the migration seed)
— added `"tool": "Vault"` (mirrors `rebuild_person_note`'s own
Vault-tool classification, the closest existing precedent for a
Person-note-mutating Skill). Fixed directly in this task's own file
(`skill_tools.py`), logged here per this project's own "compose around
the REAL current file" precedent.

**Verification — Python shell against the real backend `.venv`, real
vault, real `people-producer` agent:**
- **AC-01** — PASS, both Manual and Autonomous mode: `invoke_skill(...,
  trigger="cockpit_mention")` returns `{"status": "proposed",
  "proposal_id": ...}` in both modes; the real target Person note's body
  is confirmed byte-for-byte unchanged immediately after each dispatch.
- **AC-03** — PASS: neither Manual nor Autonomous mode refuses this
  Skill (`status` is `"proposed"` in both, never `"refused"`); a
  same-session cross-check dispatching `rebuild_person_note` via
  `trigger="direct"` in Manual mode also falls through (not refused for
  a `mode == "manual"` reason) — confirms Manual mode alone never
  special-cases this capability, exactly Scenario 3's own wording.
- Static checks — PASS: `list_skills()` includes the entry with
  `mutates: True`; `has_skill_access("people-producer",
  "propose_person_note_update")` is `True` after the migration seed;
  `person_note_proposals` import confirmed function-body-local only
  (grep).
- Clean-up: every test `proposal_id` created during this task's own
  verification was discarded (`person_note_proposals.discard_proposal`),
  leaving the real Person note(s) used untouched; working mode restored
  to its original value afterward.

gate: flagged (carried, trigger-3 — `ADR-038`) 2026-08-14 — no NEW
coder-owned trigger fired (the missing `"tool"` field is a scope-internal
reconciliation against the real current file, same file this task
already owns, logged for human spot-check; no `ESCALATIONS.md` entry;
AC-01/AC-03 both verified live with a real, observed outcome).
