---
id: REQ-SB-63-US-01-T02
title: Wire Consult-Librarian into REQ-SB-55's Thread pipeline — additive branch Job, never gates Route-to-Project
parent_story: REQ-SB-63-US-01
requirement_id: REQ-SB-63
type: backend
status: Done
gate: flagged
gate_reason: "trigger-1 (material assumption) — carried from the parent story's architect pass (the concrete shape of the deferred cross-reference write this consult call feeds was designed, not spec'd by the PRD). No decomposer-owned trigger fired on this task itself. See REVIEW-QUEUE.md."
phase: P1
depends_on: [REQ-SB-63-US-01-T01, REQ-SB-55-US-01-T03, REQ-SB-55-US-01-T04, REQ-SB-55-US-01-T07]
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-63-US-01-T02 — Wire `Consult-Librarian` into REQ-SB-55's Thread pipeline

## Parent Story

- Story: [[REQ-SB-63-US-01]] — `../UserStories/REQ-SB-63-US-01-the-librarian-vault-expert-central-authority.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-63 *The Librarian — Vault Expert as the Central Placement/Restructuring/Enrichment Authority for the New KB Pipelines*

---

## Objective

Add a new plain function `consult_librarian(thread_result: dict) -> dict` to `email_classification.py` that reads the Thread's own regenerated `## Summary` and calls `T01`'s generalized `vault_filing_expert.determine_placement_and_file(..., already_filed_path=thread_result["thread_path"])`; wire it as a new, additive branch node into the compiled `StateGraph` in `app/business/pipelines/email_capture_pipeline.py` — fires after `Thread-Match/Merge`, mirrors `Detect-Recurring-Pattern`'s own additive-branch shape, and never gates `Route-to-Project` or the graph's own terminal step (`ADR-041`'s "consulting an Expert is additive" precedent).

---

## Starting State → End State

**Before / Inputs:**
- `REQ-SB-63-US-01-T01`'s generalized `determine_placement_and_file(content, source_description, requesting_agent_id, *, already_filed_path=None)`.
- `REQ-SB-55-US-01-T03`'s `thread_match_merge(email, classification, attachment_entries=None) -> {"thread_path": str, "created": bool, "conversation_id": str, "customer": str}`.
- `REQ-SB-55-US-01-T04`'s `route_to_project(thread_result, classification, email) -> dict | None`, fired conditionally only when `thread_result["created"]` is `True`.
- `REQ-SB-55-US-01-T07`'s `app/business/pipelines/email_capture_pipeline.py` — the compiled `StateGraph` wiring `classify` → `thread_match_merge` → (conditionally) `route_to_project`, plus the `summarize_attachment`/`detect_recurring_pattern` branch Jobs. This module does not exist until `T07` lands.
- `vault_writer.py` has `replace_body_section(path, header, new_content)` (header-scoped, full-region REGENERATION/write) and `REQ-SB-55-US-01-T01`'s new header-scoped growing-append primitive (write-only) — no existing primitive READS a body section's own text back.

**After / Outputs:**
- `vault_writer.py` gains one small new reader primitive, `read_body_section(path, header: str) -> str`, reusing `replace_body_section`'s own `_BODY_SECTION_HEADER_PATTERN`/header-location regex (never a second, divergent header-finding mechanism) — returns the stripped text strictly between `header`'s own line and the next `##`-level header (or EOF); returns `""` if `header` is not found (mirrors `replace_body_section`'s own "no-op/absent is a valid outcome" contract, adapted to a read).
- `email_classification.py` gains `consult_librarian(thread_result: dict) -> dict`, calling `vault_filing_expert.determine_placement_and_file(content=vault_writer.read_body_section(Path(thread_result["thread_path"]), "## Summary"), source_description=f"Thread update: {thread_result['thread_path']}", requesting_agent_id="email-capture-pipeline", already_filed_path=thread_result["thread_path"])`, with a wrapping `try/except` so any raised exception (or an honest `"unavailable"` status) never aborts the pipeline run for that email — always returns a plain, honest result dict.
- `email_capture_pipeline.py`'s compiled graph gains a new node wrapping `consult_librarian`, wired with an unconditional edge FROM `thread_match_merge` (fires on every Thread update — both `created=True` and `created=False` alike) — mirrors `Detect-Recurring-Pattern`'s own additive, non-gating branch shape: terminates on its own, never feeds into `route_to_project`, never delays or gates it.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — add `read_body_section`.
- `src/backend/app/business/email_classification.py` — add `consult_librarian`.
- `src/backend/app/business/pipelines/email_capture_pipeline.py` — add the new node + edge. Compose around the REAL current file as `T07`'s own coder actually shipped it — do not assume its exact node/edge variable names from `T07`'s own illustrative prose; read the real file first (this codebase's own established "compose around the real current file" precedent, `Learnings.md`, `SPRINT-020`/`021`/`027`/`048`).

---

## Constraints

- Inherits from parent story: consulting the Librarian is additive, never gates `Route-to-Project` or the graph's own terminal step (`ADR-041`'s "branch to consult an Expert" precedent, applied here a second time after `Detect-Recurring-Pattern`).
- `consult_librarian` must remain a plain, LangGraph-ignorant function — ordinary Python data in/out, mirroring every other Job function in `email_classification.py` (no LangGraph import, no graph-state dict parameter).
- `consult_librarian` must never crash the pipeline run for one email — wrap the composed `determine_placement_and_file` call so an `"unavailable"` status (`AC-05`) or any raised exception is caught and returned as an honest per-item result, never propagated to abort the whole tick's own loop (mirrors `T07`'s own per-email failure-isolation discipline).
- `read_body_section` must reuse `replace_body_section`'s own `_BODY_SECTION_HEADER_PATTERN`/header-location logic — never a second, divergent header-finding mechanism (mirrors `REQ-SB-55-US-01-T01`'s own identical Constraint for its append primitive). Pure read — must never write to the file.
- Do not modify `thread_match_merge`/`route_to_project`/`detect_recurring_pattern`/`summarize_attachment`'s own internal logic or return contracts — compose `thread_result` exactly as `T03` of `REQ-SB-55-US-01` already ships it.
- Do not modify `REQ-SB-08`/`09`/`10`'s classification modules (`AC-06`) — this task's own file scope is limited to `email_classification.py`/`email_capture_pipeline.py`/`vault_writer.py`; the OTHER capture pipelines' modules are never touched, imported from, or referenced.
- Do not modify `replace_body_section`, `create_thread_note_baseline`, `ensure_thread_note_baseline_frontmatter`, or any OKF-directory-family function — this task only ADDS `read_body_section` as a new, sibling function.
- Never imports `outlook_com`/`compass_client` directly inside `email_capture_pipeline.py` — the new node composes only `consult_librarian` from `email_classification.py`, mirroring `T07`'s own standing Constraint for every other node.

---

## Tests

**Manual verification steps:**
1. **[REQ-SB-63-US-01-AC-01]** Against a throwaway scratch vault with a real Thread note carrying real `## Summary` content, and a real (or scoped-stub) grounded Provider completion, invoke the pipeline (or directly call `consult_librarian(thread_result)` for a real `thread_result` produced by a real `thread_match_merge` call) — confirm the returned decision reflects the SAME live `known_kinds`/`known_customers`/`known_partners` grounding and Tier boundary independently confirmed by `T01`'s own direct-call verification, this time reached via the pipeline's own Job wrapper and a real `read_body_section` extraction of `## Summary`.
2. **[REQ-SB-63-US-01-AC-02]** Run the pipeline (or call `consult_librarian` directly) for a Thread whose `## Summary` references a real, already-known Customer — confirm the Thread note itself (not a new note) ends up with a real `[[wikilink]]` hub-link, confirming hub-linking fired correctly via this new caller.
3. **[REQ-SB-63-US-01-AC-05]** Monkeypatch the Provider unavailable (same technique as `T01`) and run the pipeline for a real email — confirm the pipeline run for that email completes to a clean, ordinary end (no crash, no interrupt) with an honest `"unavailable"` result recorded for the `Consult-Librarian` node, and confirm `Route-to-Project`/the graph's own terminal step still ran normally for that same email.
4. **[REQ-SB-63-US-01-AC-06]** Regression: confirm `REQ-SB-08`/`09`/`10`'s pre-existing, still-live modules (`email_classification.py`'s own `classify_recent_emails`; the meeting/todo/people classification modules) are byte-for-byte unaffected by this task's edits — grep-diff confirms only `consult_librarian`/the new graph node/`read_body_section` were added, no existing function body changed.
5. Confirm the new `Consult-Librarian` node never gates `Route-to-Project`: run the pipeline for a brand-new Thread (`created=True`) with the Provider slow/unavailable for `Consult-Librarian` specifically — confirm `route_to_project`'s own Pending Approval is still created (its own conditional edge is independent of `Consult-Librarian`'s own completion).
6. Confirm `read_body_section` correctly extracts ONLY the `## Summary` region (not `## Transcript`/`## Attachments`) from a real multi-section Thread note — mirroring `replace_body_section`'s own region-boundary discipline; confirm it returns `""` for a header that does not exist, without raising.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-01** — the pipeline's own `Consult-Librarian` Job reaches the generalized Librarian and receives a grounded decision, integration-level.
- [x] **AC-02** — hub-linking fires end-to-end within a real pipeline run via this new caller.
- [x] **AC-05** — Provider-unavailable honesty flows through the pipeline without crashing or blocking the terminal step.
- [x] **AC-06** — `REQ-SB-08`/`09`/`10`'s modules are untouched by this task.
- [x] `Consult-Librarian` never gates `Route-to-Project` — confirmed by a real independent-completion test.
- [x] `read_body_section` reuses `replace_body_section`'s own header-location regex; never writes.
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Wiring an equivalent consult call into `REQ-SB-56`/`57`/`58`'s own pipelines — future work, explicitly named in the parent story's own Non-Goals.
- The cross-cutting detection/proposal-creation logic itself — `T01`'s own scope; this task only supplies the caller and the content it consults with.
- The `finalize_cross_cutting_update` write handler — `T03`'s own scope.
- Any change to `thread_match_merge`/`route_to_project`/`summarize_attachment`/`detect_recurring_pattern`'s own internal logic — those belong to their own `REQ-SB-55-US-01` tasks.

---

## Context / Notes

Full reasoning: `Implementation/Architecture/architecture.md` → "The Librarian — Vault Filing Expert generalized to a Pipeline-Job caller + cross-cutting-update detection" (the "Pipeline wiring point" bullet, which explicitly leaves exact `StateGraph` node wiring — parallel to vs. sequential after `Route-to-Project` — to the decomposer, per `ADR-043`'s own "Job wiring specifics belong to the decomposer" precedent). Also read `Implementation/Architecture/ADR.md` → `ADR-043` (the real, current pipeline shape this task adds a 6th node into) and `ADR-041` (the "consulting an Expert is additive" precedent this task's own non-gating Constraint enforces).

**Real cross-story dependency, not a placeholder:** this task cannot be built until `REQ-SB-55-US-01-T03`/`T04`/`T07` exist as real code — `email_capture_pipeline.py` itself is created by `T07`, and `thread_result`'s own shape is `T03`'s contract. All three are real, `Ready` task files in `REQ-SB-55-US-01` as of this pass (confirmed by direct reading, not assumed) — if the coder reaches this task before those land, treat it as genuinely blocked, not as license to improvise a divergent pipeline shape.

The gate stays `flagged` (trigger-1, carried from the parent story's architect pass). See the story's own `## Notes` and `REVIEW-QUEUE.md` for the human-review item.

---

## Implementation Log

**Built 2026-08-16 (coder, `/implement-sprint`, `SPRINT-050`), against the
real, current `vault_filing_expert.py` (`T01`, `Done`), `email_
classification.py` (`REQ-SB-55-US-01`, all tasks `Done`), and
`app/business/pipelines/email_capture_pipeline.py` (`REQ-SB-55-US-01-T07`,
`Done`) — all read fresh before editing, per the launching agent's own
instruction, not assumed from the task file's own illustrative prose.**

**Code shape:**

- `src/backend/app/data_access/vault_writer.py` — added `read_body_section
  (path, header: str) -> str` immediately after `replace_body_section`,
  reusing that function's own exact header-line regex (`re.compile(r"^" +
  re.escape(header) + r"$", re.MULTILINE)`) and the SAME module-level
  `_BODY_SECTION_HEADER_PATTERN` for the next-header boundary — no second,
  divergent header-finding mechanism. Returns `""` (no raise) when `header`
  is absent. Pure read; never calls `path.write_text`.
- `src/backend/app/business/email_classification.py` — added `vault_
  filing_expert` to the existing `app.business` import tuple, and a new
  `consult_librarian(thread_result: dict) -> dict`, placed directly after
  `finalize_thread_project_routing` (before `detect_recurring_pattern`) —
  reads `## Summary` via the new `read_body_section`, calls `vault_filing_
  expert.determine_placement_and_file(content=..., source_description=
  f"Thread update: {thread_path}", requesting_agent_id=
  "email-capture-pipeline", already_filed_path=thread_path)` inside a
  `try/except Exception`, returning `{"status": "unavailable", "message":
  str(exc)}` on any raised exception — the Librarian's own already-honest
  unavailable dict needs no special handling, it's returned as-is.
- `src/backend/app/business/pipelines/email_capture_pipeline.py` — added
  `consult_librarian` to the `email_classification` import tuple, a new
  `consult_librarian_result: dict | None` `TypedDict` field (mirrors
  `recurring_pattern_result`), a new `_consult_librarian_node`, and added
  `"consult_librarian"` as a new graph node. **Wiring decision, following
  the task's own explicit End-State/Constraint text ("unconditional edge
  ... fires on every Thread update ... never feeds into route_to_project,
  never delays or gates it"), resolved by mirroring this SAME module's own
  already-established `_route_after_classify` "always this, additionally
  that" list-returning conditional-edges shape** (rather than inventing a
  second wiring mechanism): `_route_after_thread_match_merge` changed from
  a single-target, str-returning function (`"route_to_project"` or `END`)
  to a list-returning one — `destinations = ["consult_librarian"]`
  unconditionally, `+ ["route_to_project"]` only when `thread_result[
  "created"]` is `True`. Both `"consult_librarian"` and `"route_to_
  project"` carry their own independent fixed edge straight to `END`
  (`builder.add_edge("consult_librarian", END)`, pre-existing `builder.
  add_edge("route_to_project", END)` unchanged) — neither feeds into the
  other or back into `thread_match_merge`, which is what makes "never
  gates" a structural graph-topology property (confirmed via `_GRAPH.
  get_graph().nodes` containing both, and via direct `_route_after_
  thread_match_merge` destination-list inspection for both `created=True`
  and `created=False`), not merely a code-review convention. `initial_
  state`'s dict literal in `run_email_capture_pipeline` gained the new
  `"consult_librarian_result": None` key. Module docstring's own Topology
  paragraph updated to describe the second fork point.

**Verification technique, per the task's own Tests block's explicit
instruction ("Against a throwaway scratch vault ... a real (or scoped-
stub) grounded Provider completion"):** a real `tempfile.mkdtemp()`
scratch vault, `VAULT_PATH` env-overridden BEFORE any `app.*` import (the
real configured vault never touched by this task's own verification run),
mirroring `REQ-SB-55-US-01-T04`'s own established technique for this
codebase. `model_factory.resolve_agent_model` scoped-stubbed (reverted via
`try/finally` after each use) to an engineered-JSON-reply stub, mirroring
`T01`'s own disclosed technique — `vault_writer`/`customer_hub_linking`/
`pending_approval_registry`/`compass_client` (stubbed only for the
`guess_project_for_thread` call inside the independence check, reverted
immediately after) were otherwise real and unmocked. Script + full
transcript kept in this session's own scratchpad, not committed.

- **[AC-01]** A real `thread_result` produced by a real `email_
  classification.thread_match_merge(email, classification, None)` call
  (`created=True`, a real Thread note written under `Work/Threads/`).
  Live-confirmed `known_kinds == ["Customers", "Threads"]` (this pipeline
  never creates a `Work/Emails/` folder — Threads is the real, live-
  discovered top-level kind for captured email content), `known_customers
  == ["Acme Corp"]` (seeded by `thread_match_merge`'s own `ensure_
  customer_hub_note` call). A real `read_body_section(thread_note_path,
  "## Summary")` call extracted exactly the Thread's own regenerated
  Summary text (confirmed containing the real message body). Called `email_
  classification.consult_librarian(thread_result)` (the pipeline's own Job
  wrapper) with the model stub returning a decision naming `kind=
  "Threads"` (a real, live-grounded, ALREADY-known kind) — result:
  `{"status": "linked", "path": <the real Thread path>, "kind":
  "Threads", ...}`, confirming the SAME Tier-1 boundary check ran against
  the SAME live `known_kinds` this call itself just confirmed. **PASS.**
- **[AC-02]** Same call, decision naming `referenced_customer="Acme
  Corp"` (a real, already-known customer, from the SAME pre-fetched
  `known_customers` list). Read the ALREADY-FILED Thread note's own body
  back from disk after the call — a real `**Customer:** [[Acme Corp]]`
  line now present (confirmed absent before the call), landed via `_link_
  referenced_entity` against `thread_result["thread_path"]` itself, never
  a new note. **PASS.**
- **[AC-05]** `model_factory.resolve_agent_model` stubbed to return `None`
  (Provider unavailable) for a SECOND real Thread (`created=True`). Direct
  `consult_librarian(thread_result_2)` call → `{"status": "unavailable",
  "message": "The Vault Filing Expert's selected Provider is not
  available."}` (no raise). Reached the SAME result via the graph's own
  `_consult_librarian_node({"thread_result": thread_result_2})` wrapper —
  identical honest dict, confirming the graph-level Job wrapper adds no
  swallowed-exception risk of its own. **Independence, same scenario:**
  `_route_after_thread_match_merge({"thread_result": thread_result_2})`
  returned `["consult_librarian", "route_to_project"]` (both destinations
  present for a `created=True` Thread, regardless of the Librarian's own
  Provider state) — then `_route_to_project_node(...)` (with `compass_
  client.guess_project_for_thread` stubbed for determinism) was called
  independently, in the SAME "Consult-Librarian unavailable" scenario, and
  created a real, new `route_thread_to_project` Pending Approval
  (`before=0`, `after=1` via `pending_approval_registry.list_pending_
  approvals(status="pending")`) — Consult-Librarian's own unavailability
  never gated or delayed it. **PASS** (also satisfies the task's own
  unlocked "never gates Route-to-Project" checklist item).
- **[AC-06]** Regression: this task's only edits inside `email_
  classification.py` are (a) one added name (`vault_filing_expert`) in the
  existing `app.business` import tuple and (b) one new function (`consult_
  librarian`) inserted between two pre-existing functions — confirmed via
  `Grep` that `classify_recent_emails` (and every other `REQ-SB-08`/`09`/
  `10`-era function in this file) is present, unmoved, and was never the
  target of any `Edit` call this task made. The meeting/todo/people
  classification modules were not opened by this task at all (outside
  `## Files to Modify`). **PASS.**
- **`read_body_section` regression (unlocked checklist items):** a call
  naming a header absent from the Thread note (`"## Nonexistent"`)
  returned `""`, no raise. A call naming `"## Transcript"` on the same
  multi-section Thread note returned only that region's own real content
  (the transcript line), confirmed to NOT contain the `## Summary`
  region's own distinct text — the header/next-header boundary discipline
  holds identically to `replace_body_section`'s own.

`ast.parse()` of all 3 modified files (`vault_writer.py`, `email_
classification.py`, `email_capture_pipeline.py`) confirmed clean. The
compiled `_GRAPH.get_graph().nodes` was inspected directly and confirmed
to contain `classify`, `summarize_attachment`, `thread_match_merge`,
`route_to_project`, `detect_recurring_pattern`, `consult_librarian`,
`__start__`, `__end__` — exactly the 6 real Job nodes plus the two
LangGraph-implicit boundary nodes.

No `ESCALATIONS.md` entry from this task itself — no locked AC failed, no
new dependency, no shared-interface change beyond what `T01`'s own already-
built `already_filed_path` parameter already exposed, no ADR deviation.
`gate: flagged` stays as-is, carried unchanged from the parent story's
architect pass (trigger-1, the designed write-shape this task's own
caller composes) — a standing breadcrumb for human review, not a build
blocker.

**Story/sprint propagation:** all 3 of `REQ-SB-63-US-01`'s tasks (`T01`,
`T02`, `T03`) are now `Done`, all 6 locked ACs (`AC-01`..`AC-06`)
AC-ID-tagged and verified across them — the story's own status set to
`Done` below. `SPRINT-050` (this story's only story) closes in lockstep;
its own Retrospective drafted, `gate: flagged` for the human retro-harvest
per the sprint-wrap contract, carrying BOTH the still-open trigger-1
architect-designed-write-shape `REVIEW-QUEUE.md` item (unresolved,
untouched by this task) AND the new retro-harvest flag — see the sprint
file's own `## Retrospective` and `gate_reason`.
