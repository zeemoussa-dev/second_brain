# MEMORY

Append-only log of decisions, patterns, and constraints discovered during delivery.
Updated by Claude when a task produces a new rule or constraint worth preserving
across sessions.

**Protocol (from CLAUDE.md):**
- Decisions → `## Decisions` — format: `[date] Decision – Reason`
- Patterns → `## Patterns` — format: `Pattern name – description`
- Constraints → `## Constraints` — format: `Constraint – reason`
- Do NOT add logs, chat transcripts, or debugging output.

---

## Decisions

- [2026-08-16] `REQ-SB-66-US-01-T01` (`SPRINT-052`, "Real, Editable
  Per-Agent/Job Prompt + a Guardrails Placeholder in Settings", `ADR-044`)
  shipped and verified live — first task of the story. New sibling
  `.second-brain/agent_prompts.json` store, composed alongside
  `agent_registry.py` (never inside it, `ADR-011` point 2 applied a
  further time), a further mechanical application of `agent_keywords.py`/
  `working_mode_registry.py`'s own already-established shape — no new
  ADR needed for this part. `app/business/agent_prompts.py` (new) exposes
  `get_prompt(id)`/`set_prompt(id, prompt)`/`get_guardrails(id)`/
  `set_guardrails(id, guardrails)`, composed ONLY through 2 new
  `vault_writer.py` primitives (`load_agent_prompt_record(id)`/
  `save_agent_prompt_record(id, record)`, a whole-record `{"prompt":
  str | None, "guardrails": str}` shape per id — never touching
  `agent_prompts.json` directly from the business layer, `ADR-003`).
  **A real Agent id and a real Job id share one flat namespace with zero
  special-casing** — the SAME store/functions serve both, no "kind"
  field distinguishing them anywhere. **Two DIFFERENT self-healing
  defaults live in the same one record, deliberately not the same
  no-raise style for both fields** — `get_prompt` returns `None` when
  unset (no sensible universal default prompt text exists, mirrors
  `load_agent_keywords`'s own "no assignment yet" reasoning), while
  `get_guardrails` returns `""` when unset (Guardrails is always
  present/structure-only, `ADR-044` point 2) — never conflate the two:
  a future consumer must not treat an unset Prompt as `""` (that would
  be indistinguishable from an operator explicitly saving an empty
  override) nor an unset Guardrails as `None`. Verified live directly
  against the real, configured vault (`.second-brain/agent_prompts.json`
  is a new internal state file, same trust tier as
  `agent_keywords.json`/`agent_scopes.json` — not a vault note, no
  scratch-vault isolation needed): `AC-08` (`set_prompt`/`set_guardrails`
  on a real Agent id AND a real Job id both landed in the SAME flat
  top-level JSON object, each holding its own `{"prompt", "guardrails"}`
  shape, no distinguishing field; `agent_registry.py` confirmed
  byte-for-byte unmodified by `git status`, both before and after);
  `AC-09` (editing `"classify"`'s own `prompt` left
  `"vault-filing-expert"`'s own `prompt`/`guardrails` completely
  unchanged — no cross-id bleed); regression (`get_prompt`/
  `get_guardrails` for a never-saved id returned `None`/`""`, never
  raised). This task does NOT wire the override into any real call
  site (`T02`/`T03`'s own scope) or expose any HTTP endpoint
  (`T04`/`T06`'s own scope) — store + get/set surface only. Full
  reasoning: task's own Implementation Log, `Implementation/Tasks/
  REQ-SB-66-US-01-T01-agent-prompts-sibling-store.md`.

- [2026-08-16] `REQ-SB-66-US-01-T03` (`SPRINT-052`, `ADR-044`) shipped and
  verified live — wired the Prompt override into the story's remaining 2
  real call sites. `agent_orchestration/state.py`'s
  `history_entries_to_messages` gained an optional `agent_id: str | None
  = None` parameter, resolving `agent_prompts.get_prompt(agent_id)`
  internally and using the override as the Chat `SystemMessage`'s own
  content when set, byte-for-byte hardcoded text when unset/absent;
  `graph.py`'s `run_agent_conversation` passes its own already-in-scope
  `agent_id` through — no new fetch needed. **The `record_knowledge_gap`
  tool-call mechanism (`REQ-SB-33-US-01`'s honest-uncertainty enforcement)
  is a completely separate wiring path from this SystemMessage's own
  text** — the tool is bound onto every turn's tools list and every graph
  node is untouched by this task; only the DEFAULT TEXT of the
  SystemMessage became overridable, never the mechanism. Confirmed live:
  the tool registration line in `run_agent_conversation` was unaffected by
  this task's one-line call-site change.
  `vault_filing_methodology.build_placement_prompt` gained an optional
  `prompt_override: str | None = None`, replacing `_METHODOLOGY_EXCERPT`
  as the `SystemMessage`'s own content when set; its `HumanMessage`
  (known-lists/schema/content) stays permanently non-overridable — built
  identically regardless. `vault_filing_expert.determine_placement_and_file`
  resolves `agent_prompts.get_prompt("vault-filing-expert")` unconditionally
  (never keyed off `requesting_agent_id`, which stays Pending-Approval
  bookkeeping-only) — this single resolution point covers ALL 4 real
  callers of `determine_placement_and_file` (`agents_router.py` Hub
  routing, `email_classification.consult_librarian`,
  `knowledge_gap_tracking.py`, `agent_orchestration/knowledge_bootstrap.py`)
  uniformly, since the override lookup lives at the one shared function,
  not duplicated per caller. Verified live against a scratch vault
  directory (`settings.vault_path` redirected, avoiding the real vault's
  own `.second-brain/agent_prompts.json`): `AC-02` (3 distinct marker
  overrides, one per Worker/Producer/Expert-style agent id, each replaced
  the SystemMessage verbatim; a 4th, un-overridden id stayed on the exact
  hardcoded default text — no cross-id bleed); `AC-03` (a
  `"vault-filing-expert"` marker override replaced
  `build_placement_prompt`'s SystemMessage verbatim, with its HumanMessage
  byte-identical to the no-override case); `AC-04` (both call sites,
  no override present, produced byte-for-byte identical output to the
  real pre-task text, confirmed via a captured "before" string).
  `agent_chat.py` was not opened for editing — confirmed out of this
  task's scope, per the parent story's own verified PRD discrepancy.
  Full reasoning: task's own Implementation Log, `Implementation/Tasks/
  REQ-SB-66-US-01-T03-chat-and-vault-filing-prompt-override-wiring.md`.

- [2026-08-16] **`REQ-SB-65-US-01-T02` / ESC-038 (Resolved) — spliced Job
  `AgentSummary` entries never inherit `is_background_agent` verbatim from
  their parent pipeline agent.** Operator decision: "Jobs always render,
  regardless of parent's flag." `layoutAgents.ts` excludes every
  `is_background_agent: true` entry from the Agents Map ring entirely
  (`REQ-SB-51-US-01`) — a synthetic/adapted entry that inherits that flag
  verbatim from a Background Agent parent (e.g. `email-capture-pipeline`)
  is silently invisible even though the whole point of splicing it in was
  to make it independently visible. `pipelineJobTreeAdapter.ts` now
  hardcodes `is_background_agent: false` on every spliced Job entry while
  still inheriting every other field (`type`/`icon`/`color`/
  `working_mode`/`description`) verbatim from the parent.

- [2026-08-16] **Live-discovered defect, fixed directly (operator-approved
  "quick fix now" over filing a bug):** `GET /agents` never populated
  `depends_on`/`branch_target_agent_id` for real agents — only the
  separate demo-backend's synthetic `demo_taxonomy.py` data ever set
  them. The frontend's already-shipped `layoutAgents.ts` (tree/pipeline
  visualization) treats both as required, non-optional fields and calls
  `.length`/`.map()` on `depends_on` unconditionally — so ANY real,
  non-demo `GET /agents` response crashed inside the Agents Map's own
  `Promise.all(...).then()` chain, silently caught by its own `.catch()`
  (no console error), collapsing the whole map to "0 sections · 0 agents
  mapped." This had likely been true since whichever story first made
  `layoutAgents.ts` read `depends_on` — never caught before because this
  project's frontend verification has mostly run against the demo-backend
  (port 8090), not the real one, until this session switched to and
  started genuinely exercising the real backend end-to-end. Fixed with
  honest empty defaults (`agents_router.py::list_agents`) — no real
  `depends_on` SOURCE exists anywhere in `agent_registry.py` yet, so `[]`/
  `null` is correct, not a stopgap fabrication. **Standing lesson:** any
  frontend field a demo/mock backend populates but the real backend
  doesn't is a live landmine that stays invisible until the real backend
  is actually exercised through that UI path — worth a deliberate check
  whenever a frontend TypeScript interface field has no matching real
  backend write site.

- [2026-08-16] `REQ-SB-63-US-01-T02` (`SPRINT-050`, "The Librarian" —
  wiring `Consult-Librarian` into `REQ-SB-55`'s Thread pipeline) shipped
  and verified live — this story's own last task; story and `SPRINT-050`
  both close on this task. New `email_classification.consult_librarian
  (thread_result: dict) -> dict`: reads the Thread's own just-
  regenerated `## Summary` via a new `vault_writer.read_body_section
  (path, header) -> str` reader (the read counterpart to `replace_body_
  section` — reuses that function's own exact header/next-header
  location regex verbatim, never a second, divergent header-finding
  mechanism; returns `""` if `header` is absent, mirrors `replace_body_
  section`'s own no-op-if-absent contract, adapted to a read; never
  writes), then calls `T01`'s generalized `vault_filing_expert.
  determine_placement_and_file(..., already_filed_path=thread_result[
  "thread_path"])`. Wrapped in a `try/except Exception` that returns an
  honest `{"status": "unavailable", "message": str(exc)}` — the
  Librarian's own already-honest `{"status": "unavailable", ...}` result
  needs no special handling, it's returned as-is; this Job NEVER raises,
  so a Consult-Librarian failure can never crash the pipeline run for
  one email. **New, reusable `StateGraph` wiring pattern for "add an
  unconditional additional branch alongside an existing single-choice
  conditional edge from the same source node," worth reusing for any
  future Librarian-consult wiring into `REQ-SB-56`/`57`/`58`'s own
  pipelines:** `email_capture_pipeline.py`'s own `_route_after_thread_
  match_merge` was changed from a single-target, str-returning
  conditional-edges function (`"route_to_project"` or `END`) to a
  list-returning one, mirroring `_route_after_classify`'s own already-
  established "always this, additionally that" shape (`REQ-SB-55-US-01-
  T07`, `SPRINT-049`) — `consult_librarian` is ALWAYS in the returned
  list (fires on both `created=True` and `created=False`), `route_to_
  project` is an ADDITIONAL list member only when `created` is `True`;
  each destination has its own fixed edge straight to `END`, so neither
  branch feeds into the other or back into `thread_match_merge` — this
  is what makes "never gates" a structural graph-topology guarantee, not
  just a code-review convention, confirmed live via `_GRAPH.get_graph().
  nodes`/direct destination-list inspection. Verified live end-to-end
  (manual mode, `tempfile.mkdtemp()` scratch vault, `VAULT_PATH` env-
  overridden — the real configured vault never touched, per this task's
  own Tests block's explicit "throwaway scratch vault" instruction; a
  scoped `model_factory.resolve_agent_model` stub returning an engineered
  JSON decision, mirroring `T01`'s own disclosed verification technique):
  `AC-01` (a real `thread_result` from a real `thread_match_merge` call,
  a real `read_body_section` extraction of `## Summary`, consult_
  librarian's own grounded `"linked"` decision reflecting the SAME live
  `known_kinds`/`known_customers` grounding); `AC-02` (a real `[[Acme
  Corp]]` wikilink landed in the ALREADY-FILED Thread note's own body,
  confirmed by reading it back from disk); `AC-05` (Provider unavailable
  → honest `{"status": "unavailable", ...}`, confirmed both via a direct
  `consult_librarian` call AND via the graph's own `_consult_librarian_
  node`, with `_route_to_project_node` confirmed to still create its own
  real Pending Approval independently in the SAME scenario — Consult-
  Librarian's own failure never gated it); `AC-06` (grep-confirmed
  `classify_recent_emails` and the 3 imports added — `vault_filing_
  expert` module-level, no other line touched — the only edits inside
  `email_classification.py`); `read_body_section`'s own absent-header
  (`""`, no raise) and region-boundary (`## Summary` extraction excludes
  `## Transcript` content) contracts both confirmed live. `ast.parse()`
  of all 3 modified files confirmed clean. `gate: flagged` carried
  unchanged from the parent story's architect pass (trigger-1, the
  designed write-shape this task's own caller composes) — a standing
  breadcrumb, not a blocker; no new `ESCALATIONS.md`/`REVIEW-QUEUE.md`
  entry from this task itself. Full reasoning: task's own Implementation
  Log, `Implementation/Tasks/
  REQ-SB-63-US-01-T02-thread-pipeline-consult.md`.

- [2026-08-16] `REQ-SB-63-US-01-T01` (`SPRINT-050`, "The Librarian" —
  generalizing `ADR-021`'s Vault Filing Expert) shipped and verified live.
  `vault_filing_expert.determine_placement_and_file` gained an additive,
  keyword-only `already_filed_path: str | None = None` param — when set
  and the decision resolves Tier 1, `vault_writer.write_note` is NEVER
  called; `_link_referenced_entity` instead runs against the caller-
  supplied already-filed path, and the return dict's `"status"` becomes
  `"linked"` (vs. `"written"`) with `"path"` echoing the supplied path.
  The Tier-2 (`is_new_top_level_area`) branch is completely unaffected by
  this param — still always calls `_create_tier_2_proposal` exactly as
  before, cross-cutting detection deliberately NOT evaluated on that
  branch (no locked AC of this task exercises that combination). All 3
  pre-existing callers (`agents_router.py`, `knowledge_bootstrap.py`,
  `knowledge_gap_tracking.py`) omit the new param and are confirmed
  byte-for-byte unaffected. Second, independent addition: the model's own
  JSON decision (`vault_filing_methodology._JSON_SCHEMA_INSTRUCTIONS`)
  gained an additive `"cross_cutting_implication": {"customer": str|null,
  "partner": str|null, "reason": str} | null` field, evaluated in the SAME
  completion (never a second `model.invoke`) — re-checked in Python by a
  new `_maybe_create_cross_cutting_proposal` helper against the SAME
  pre-fetched `known_customers`/`known_partners` lists AND against the
  SAME decision's own `referenced_customer`/`referenced_partner`, never
  trusted from the model's naming alone; silently discards (returns
  `None`, never raises/fabricates) whenever the named entity is absent
  from those lists or identical to the decision's own primary reference.
  A new `_create_cross_cutting_proposal` (mirrors `_create_tier_2_
  proposal`'s exact shape — LOCAL, not module-level, `pending_approval_
  registry` import; `trigger="direct"`, never `"background"`, since a
  single pipeline tick can legitimately produce multiple distinct
  cross-cutting proposals) creates a `propose_cross_cutting_update`
  Pending Approval whose payload carries `entity_type`/`entity_name`/
  `reason`/`already_filed_path`/`source_description`. `determine_
  placement_and_file`'s own return dict gains an additive `"cross_
  cutting_approval_id"` key, present only when a proposal was actually
  created — independent of, never mutually exclusive with, the primary
  Tier-1 write/linked outcome (both can happen on the same call).
  **T02/T03's own future work should reuse this exact shape verbatim** —
  `T02` wires a real `already_filed_path=` call into `REQ-SB-55`'s Thread
  pipeline; `T03` owns only `finalize_cross_cutting_update`, the deferred
  write half dispatched via `pending_approvals_router.py`'s
  `_APPROVAL_HANDLERS`, keyed off this task's own `propose_cross_cutting_
  update` `action_id`. Verified live end-to-end against the real,
  configured vault and a real, already-filed scratch Thread note
  (`Work/Threads/`), model calls monkeypatched to an engineered-JSON stub
  (disclosed technique, per the task's own Tests option) so the
  known-vs-unknown-entity/same-entity/null cross-cutting cases could be
  deterministically engineered: `AC-01` (grounded Tier-1 linked decision,
  plus a Tier-2 case confirming the boundary is unchanged with
  `already_filed_path` set); `AC-02` (a real customer wikilink landed
  in the already-filed note's body; `vault_writer.write_note` call count
  confirmed `0` via a live spy); `AC-03` (exactly one new `propose_cross_
  cutting_update` Pending Approval, payload/returned `cross_cutting_
  approval_id` both confirmed matching); `AC-04` all 3 cases (null,
  unknown entity, same-entity) confirmed zero spurious proposals via a
  live before/after pending-count check, ordinary linked outcome still
  occurred in each; `AC-05` (Provider-unavailable dict byte-for-byte
  identical to the unmodified caller's shape); regression (an ordinary,
  un-parametered call still calls `vault_writer.write_note` exactly once
  and returns `"status": "written"`). Both test-created Pending Approvals
  were declined afterward for cleanliness (no source/state pollution
  beyond the two labelled scratch notes left in the real vault, mirroring
  `REQ-SB-35-US-01-T02`'s own established precedent of leaving verification
  artifacts in place). `ast.parse()` of both modified files confirmed
  clean; no file outside `## Files to Modify` (`vault_filing_expert.py`,
  `vault_filing_methodology.py`) was touched — the 3 existing callers
  were only read, confirmed unedited via direct `Grep`. `gate: flagged`
  carried unchanged from the parent story's architect pass (trigger-1,
  the designed write-shape this task implements) — a standing breadcrumb,
  not a blocker; no new `ESCALATIONS.md`/`REVIEW-QUEUE.md` entry from this
  task itself. Full reasoning: task's own Implementation Log,
  `Implementation/Tasks/REQ-SB-63-US-01-T01-generalize-entry-point.md`.

- [2026-08-16] `REQ-SB-63-US-01-T03` (`SPRINT-050`, "The Librarian") —
  shipped `vault_filing_expert.finalize_cross_cutting_update(payload) ->
  dict`, the deferred-write half of `T01`'s `propose_cross_cutting_update`
  Pending Approval, dispatched via `pending_approvals_router.py`'s
  `_APPROVAL_HANDLERS["propose_cross_cutting_update"]` (a pure, additive
  dict entry — the 4 pre-existing entries untouched). Mirrors `REQ-SB-55-
  US-01-T04`'s `finalize_thread_project_routing` shape exactly: reads the
  already-filed note's current `tags` via `vault_writer.read_note`,
  unions in `f"{entity_type}/{vault_writer.tag_slug(entity_name)}"` only
  if absent (idempotent — a repeat approval never duplicates the tag),
  and writes back via `vault_writer.upsert_frontmatter_key` (`REQ-SB-55-
  US-01-T01`'s real, shipped, unconditional overwrite-or-insert setter —
  confirmed the real name at build time, NOT `insert_frontmatter_key_if_
  missing`, which would silently no-op since `tags` is already present).
  Never writes to `captures.md` (`ADR-042`). Return dict: `{"path":
  payload["already_filed_path"], "message": "Approved — tagged ..."}` —
  the `"message"` key is read by the Approve endpoint's own already-
  landed `REQ-SB-55-US-01-T04` `outcome_message` generalization
  (`result.get("message") or f"Approved — filed at {result['path']}."`),
  confirmed live at build time to already be present, so the richer
  message text is what actually renders. Verified live against a
  temp scratch vault (never the real vault): additive-tag write with
  pre-existing tags preserved, idempotent re-approval (no duplicate),
  `captures.md` byte-identical + mtime-unchanged before/after, and a full
  `POST /pending-approvals/{id}/approve`-equivalent round trip (the
  router function called directly) producing a correct, non-crashing
  outcome. `_APPROVAL_HANDLERS` confirmed to hold exactly 5 keys after
  the change, the 4 pre-existing handler identities unchanged. `gate:
  flagged` carried unchanged from the parent story's architect pass
  (trigger-1) — a standing breadcrumb, not a blocker. Full reasoning:
  task's own Implementation Log, `Implementation/Tasks/REQ-SB-63-US-01-
  T03-cross-cutting-update-finalize-handler.md`.

- [2026-08-16] `REQ-SB-55-US-01` (`SPRINT-049`, `ADR-043`) — story-level
  entry, written on `T08` (the story's own final task, all 8 tasks
  `T01`-`T08` `Done`, all 9 ACs verified — 8 live/manual, 1 defensive).
  Shipped this codebase's first concrete Pipeline under `ADR-041`'s
  Agent/Pipeline/Job/Hub model: a new `app/business/pipelines/` subpackage
  (`email_capture_pipeline.py`, a code-defined, compiled-once
  `langgraph.graph.StateGraph`) composes 6 plain, LangGraph-ignorant Job
  functions already living in `email_classification.py`
  (`classify_captured_email`/`thread_match_merge`/`route_to_project`/
  `summarize_attachment`/`detect_recurring_pattern`, plus `Fetch` staying
  a pre-graph batch step) — replacing the former single-stage
  `email-capture` Worker's `classify_recent_emails` end to end for the
  scheduled/on-demand path. Two new Pending-Approval kinds were added,
  both using `trigger="direct"` (never `"background"`, whose idempotency
  guard would silently collapse multiple distinct same-tick proposals):
  `route_thread_to_project` (Thread → Project routing, ALWAYS a Pending
  Approval, never auto-committed — `ADR-021`'s "independent of working
  mode" precedent applied a second time) and `propose_recurring_pipeline`
  (a detected recurring/structured email pattern proposes a NEW standing
  Pipeline, seeded from the real triggering email and shaped to match
  `CreateAgentBody`, but NEVER built/executed on any code path including
  Approve — only the operator's own separate, later, manual completion of
  the existing Agent Creation Wizard, `REQ-SB-37`, actually creates it).
  Mid-pipeline human approval deliberately uses NO LangGraph
  `interrupt()`/checkpointer — both approval-creating Jobs run to a clean,
  ordinary completion on every invocation, reusing the existing flat-JSON
  Pending Approval mechanism instead (`ADR-043` point 4). The former
  `email-capture` Agent-tier identity was retired and replaced 1:1 by a
  genuinely new id, `email-capture-pipeline` (`type: "worker"`, same type
  as the retired entry so no type-keyed code needed further changes) —
  confirmed live that `agent_registry.get_agent("email-capture")` now
  returns `None` and the new id resolves everywhere the old one used to
  (`GET /agents`, background-agent default set, the 3 migrated
  `Skills`-tier grants, `agents_router.py`'s `_ACTION_HANDLERS`).
  Verified end-to-end against the REAL, live, configured Outlook mailbox
  and vault (not mocked/simulated): a real new email produced a real
  Thread note with correct real frontmatter/`## Summary`/`## Transcript`
  and a real, genuinely-derived `route_thread_to_project` Pending
  Approval (`is_new_project: True`, since the matched customer had zero
  currently-open Projects) — `meeting-capture`/`todo-capture`'s own
  branches in the shared `run_capture_and_record_completion` function are
  byte-for-byte unchanged and ran normally in the same real tick.
  `classify_recent_emails`/`record_conversation_note`/
  `find_related_note_stems`/`conversation_index.json`/the `## Related
  Emails` body region are now dead code for the email-capture-pipeline
  path specifically but were deliberately NOT deleted — `app/api/
  email_poc_router.py`'s own standalone `/poc/classify-emails` manual
  endpoint still calls `classify_recent_emails` directly, a real
  remaining caller outside this story's own scope.

- [2026-08-16] `REQ-SB-55-US-01-T07` (`SPRINT-049`) — this codebase's
  FIRST genuine fork/merge/conditional-branch DAG, `app/business/
  pipelines/email_capture_pipeline.py` (new `app/business/pipelines/`
  subpackage, `ADR-043` point 1), shipped and verified live. Compiled
  once at module load (`_GRAPH`, mirrors `agent_orchestration/graph.py`'s
  own singleton convention). **The `summarize_attachment` branch is
  wired as a MANDATORY pass-through node (runs for every email, loops
  0-or-more times over real attachments), not a genuinely conditional
  LangGraph fan-out** — this is the concrete mechanism that structurally
  guarantees `ADR-043` point 3's own fan-in ordering requirement
  (`thread_match_merge` runs only once `summarize_attachment`'s branch
  has completed): a real LangGraph conditional fan-out to both
  `summarize_attachment` and `thread_match_merge` from `classify` in the
  same superstep would let them race in parallel, breaking that ordering
  guarantee. `detect_recurring_pattern` IS a genuinely conditional,
  independent parallel branch off `classify` (routed only when
  `recurring_candidate` is true), with a fixed edge straight to `END` —
  it never feeds back into `thread_match_merge`. `thread_match_merge`
  conditionally routes to `route_to_project` only when its own returned
  `created` is `True`, confirmed live via a real call-count spy (exactly
  1 call across 2 messages in the same conversation) — the concrete
  mechanism behind `AC-04`. **Any future Pipeline built under this same
  `app/business/pipelines/` subpackage that needs a "collect N results
  from a variable-length list, then continue" shape should follow this
  same pattern** (a single mandatory node that internally loops, with a
  fixed non-conditional outgoing edge) rather than a real per-item
  LangGraph fan-out, whenever downstream ordering must be guaranteed —
  LangGraph's own per-item `Send` fan-out was not used and is not needed
  for this shape. No `MemorySaver`/`SqliteSaver`/`interrupt()` anywhere
  (`ADR-043` point 4) — `route_to_project`/`detect_recurring_pattern`
  each run to a clean, ordinary completion on every invocation, creating
  their own Pending Approval internally. `run_email_capture_pipeline
  (limit=10) -> list[dict]` is the public entry point `T08` wires the new
  `email-capture-pipeline` agent identity to call — a per-email failure
  (any Job's own exception, including a real `CompassError`) is caught
  at the `run_email_capture_pipeline` LOOP level (`except Exception`,
  never inside the graph itself, per this task's own Constraint), left
  unmarked so a future run retries it, while every other fetched email
  in the same tick is still processed normally — confirmed live with a
  real, scoped, `finally`-reverted `compass_client.classify_email`
  failure induction. **Scope-internal judgement call, logged for spot-
  check:** the task's own Constraints text read, taken as two isolated
  sentences, as if `outlook_com` could never be imported into this
  module at all — reconciled against the same task's own explicit
  End-State text (`run_email_capture_pipeline`... fetches via `outlook_
  com.list_recent_mail`) and `ADR-043` point 1's own parenthetical: the
  "never imports directly" rule binds the GRAPH NODES only, never `run_
  email_capture_pipeline`'s own pre-graph Fetch step, which does import
  `outlook_com`/`vault_writer` directly, exactly as documented. `compass_
  client` itself is never imported into this module at all — the
  loop-level `except Exception` needs no specific exception class import.
  Verified live end-to-end (manual mode, scratch vault, `VAULT_PATH`
  env-overridden, real Compass Provider, only `outlook_com.
  list_recent_mail` monkeypatched): `AC-01` (two real messages in one
  real conversation collapse into exactly one Thread note, `##
  Transcript` grows to 2 lines in call order, `## Summary` regenerates
  with zero residue of the first message's own wording); `AC-04` (a real
  call-count spy confirms `route_to_project` fires exactly once across
  both messages, never on the second/already-routed one, plus exactly 1
  `route_thread_to_project` Pending Approval end-state); fan-in ordering
  (a real `.txt` attachment: `summarize_attachment` confirmed to run
  before `thread_match_merge`, which received a resolved 1-entry `
  attachment_entries` list on that same call); per-email failure
  isolation (1 honest error result + 1 real successful result from the
  same tick, failed email left unmarked, revert confirmed via a real
  follow-up successful call); dedup rerun (0 new Thread notes/approvals).
  Graph node set confirmed to contain exactly the 5 real Job names plus
  `__start__`/`__end__`. `ast.parse()` of both new files clean; no file
  outside `## Files to Modify` (`app/business/pipelines/__init__.py`,
  `app/business/pipelines/email_capture_pipeline.py`) was edited — `email_
  classification.py`/`outlook_com.py`/`compass_client.py` were only read,
  confirmed unedited via direct `Grep` for any reverse reference. Full
  reasoning: task's own Implementation Log, `Implementation/Tasks/
  REQ-SB-55-US-01-T07-pipeline-assembly.md`.

- [2026-08-16] `REQ-SB-55-US-01-T06` (`SPRINT-049`) — new `email_classification.
  detect_recurring_pattern(email, classification) -> dict | None` (the
  `Detect-Recurring-Pattern` branch Job, `ADR-043` point 3/5) and its paired
  `finalize_recurring_pipeline_proposal(payload) -> dict` deferred-write
  handler shipped and verified live. `detect_recurring_pattern` returns
  `None` immediately when `classification["recurring_candidate"]` is falsy —
  the detection signal itself lives entirely in `T02`
  (`compass_client.classify_email`'s own extended prompt); this Job never
  re-implements or duplicates any detection logic of its own. Otherwise
  creates exactly one Pending Approval (`agent_id="email-capture-pipeline"`,
  `trigger="direct"`, `action_id="propose_recurring_pipeline"`), with a
  payload shaped compatibly with `agents_router.py`'s real
  `CreateAgentBody` contract (`name`, `type: "worker"`, `purpose`) — `name`
  derived as `f"{customer} {kind} Recurring Pipeline"` and `purpose` a
  prose description naming the real customer/sender/subject/kind, both
  genuinely computed from the triggering email's own real classification
  output, never a generic/empty placeholder; a `seed_source` sub-dict
  (`subject`/`sender`/`received`) carries the raw triggering-email fields
  alongside the wizard-shaped ones. **`finalize_recurring_pipeline_proposal`
  deliberately does almost nothing** — re-reading Scenario 5's own two
  Then-clauses together ("a Pending Approval is created... pre-filled into
  the existing Agent Creation Wizard" AND "the proposed Pipeline is NOT
  built or executed automatically... until the operator explicitly
  approves AND completes the wizard") describes TWO separate human steps;
  approving this Pending Approval is deliberately not the same action as
  completing the wizard. It returns only
  `{"message": "Approved — seed data ready. Open the Agent Creation Wizard
  to complete the new Pipeline."}` — confirmed live, by direct source
  inspection of BOTH functions, that neither calls
  `agent_registry.create_agent(...)` (or any other agent-creation code
  path) on any branch, and confirmed live that `agent_registry.
  list_agents()`'s own count is byte-identical before and after a real
  Approve call. **Any future `Detect-Recurring-Pattern`-adjacent work
  (e.g. actually wiring the wizard's frontend to pre-fill from this
  payload) should read `name`/`type`/`purpose` directly off this Job's own
  payload shape — it already matches `CreateAgentBody` field-for-field, no
  reshaping needed.** Verified live end-to-end (manual mode, scratch
  vault, `VAULT_PATH` env-overridden, real Compass Provider, no mocking,
  reusing `T02`'s own two real structurally-different test fixtures — a
  "Weekly Usage Report — Acme Corp" tabular report and a
  "INVOICE #4471 — Zenith Manufacturing Ltd." invoice-shaped email, both
  independently re-classified live via `classify_captured_email` rather
  than hand-constructed classification dicts): each of the two fixtures
  independently produced exactly one new, correctly-seeded Pending
  Approval (`AC-05`/`AC-06`, same code path, no branch keyed on either
  fixture's own customer name or format); an ordinary conversational email
  produced `recurring_candidate: False` and `detect_recurring_pattern`
  returned `None` with zero new Pending Approvals created; both created
  records confirmed `trigger="direct"`; a real Approve call against the
  first record recorded the exact deliberately-minimal outcome message
  into `email-capture-pipeline`'s own agent history, with
  `agent_registry.list_agents()`'s count unchanged (7 before, 7 after).
  `ast.parse()` of both modified files confirmed clean; no file outside
  `## Files to Modify` (`email_classification.py`,
  `pending_approvals_router.py`) was edited. Full reasoning: task's own
  Implementation Log, `Implementation/Tasks/
  REQ-SB-55-US-01-T06-detect-recurring-pattern-job.md`.

- [2026-08-16] `REQ-SB-55-US-01-T05` (`SPRINT-049`) — new `email_classification.
  summarize_attachment(attachment, conversation_id, received) -> dict` (the
  `Summarize-Attachment` branch Job, `ADR-043` point 3) shipped and verified
  live. Composes exactly two existing primitives, unchanged, no new
  attachment-saving or summarization mechanism: `vault_writer.
  write_attachments(subfolder="Work/Threads", note_stem=conversation_id,
  attachments=[attachment])` (saves under `Work/Threads/attachments/
  <slug-of-conversation_id>/`, reusing its own existing `"saved": False`
  outcome for an oversized attachment rather than a second size check —
  Outlook's own upstream size cap already sets `attachment["content"]` to
  `None` before this function ever sees it); then, if saved,
  `REQ-SB-28-US-01`'s own `upload_storage.save_upload`/
  `extract_text_content`/`delete_upload` DIRECTLY against the attachment's
  own real, already-in-memory bytes for text extraction — the identical
  temporary-save-then-extract-then-delete technique `REQ-SB-44-US-01`'s own
  `app/business/cockpit/attachments.py` already established for a
  vault-saved email attachment, confirmed live as the correct reuse point
  by direct reading before writing this task's own code. Summarization
  calls `compass_client.summarize_content(extracted_text, ...)` DIRECTLY —
  the same primitive `REQ-SB-28`'s own `summarize-file` Skill composes —
  never through `skill_registry`/`invoke_skill` dispatch, keeping this Job a
  plain, LangGraph-ignorant, independently callable/testable function with
  no graph-state parameter. Return contract: `{"filename", "saved",
  "relative_link" (only when saved), "dated_entry" (only when a real
  summary was produced), "summary_error" (when saved but no usable summary
  could be produced — unsaved/oversized, non-text-bearing, or a real
  `CompassError`)}`. **An unsaved/oversized attachment reports via
  `summary_error`, never a `dated_entry`** — the task's own Constraint
  offered either "a `dated_entry` noting it wasn't saved, or an equivalent
  honest signal"; `summary_error` was chosen as the equivalent honest
  signal since the task's own Tests step literally required "no
  `dated_entry` implying a summary that never happened." This function
  never calls `replace_body_section`, `thread_match_merge`, or any other
  `## Summary`-touching primitive itself — it only ever PRODUCES a
  `dated_entry` string; **`T07`'s own future pipeline wiring is the piece
  that threads the collected `dated_entry` strings into
  `thread_match_merge`'s own `attachment_entries` parameter** — this
  function runs before/alongside `Thread-Match/Merge`, never after it, and
  never calls it directly. Verified live end-to-end (manual mode, scratch
  vault, `VAULT_PATH` env-overridden, real Compass Provider, no mocking
  except a scoped/reverted `CompassError` induction): a real `.txt`
  attachment produces a genuine `dated_entry` (`"2026-08-16 — <filename>:
  <real Compass summary genuinely reflecting the attachment's own actual
  content>"`), the file itself confirmed byte-identical on disk at the
  correct Thread-scoped path (`AC-02`); a deliberately oversized attachment
  (`content=None`) returns `saved: False` + an honest `summary_error`, zero
  `dated_entry`; a real, scoped, in-process `compass_client.
  summarize_content` monkeypatch (reverted in a `finally` block) confirms a
  real `CompassError` is caught and reported honestly via `summary_error`
  rather than raised uncaught or fabricated, with a follow-up real call
  confirming the revert actually took effect. `ast.parse()` clean; no file
  outside `## Files to Modify` (`email_classification.py` only) was
  edited — `vault_writer.py`/`compass_client.py`/`upload_storage.py` were
  only read. Full reasoning: task's own Implementation Log, `Implementation/
  Tasks/REQ-SB-55-US-01-T05-summarize-attachment-job.md`.

- [2026-08-16] `REQ-SB-55-US-01-T04` (`SPRINT-049`) — new `email_classification.
  route_to_project(thread_result, classification, email) -> dict | None` (the
  `Route-to-Project` Job, `ADR-043` point 4/5) and its paired
  `finalize_thread_project_routing(payload) -> dict` deferred-write handler
  shipped and verified live. `route_to_project` no-ops (`None`) unconditionally
  when `thread_result["created"]` is `False` (`AC-04`'s own defensive half);
  for a brand-new Thread it filters `vault_writer.list_customer_projects
  (customer)` to `status == "active"` (the "currently open" judgement this
  primitive's own docstring explicitly deferred to this task), asks the new
  `compass_client.guess_project_for_thread(thread_summary, open_projects) ->
  {"project", "confidence"}` to pick an exact existing name or propose a new
  one, and ALWAYS creates a Pending Approval (`trigger="direct"`, `action_id=
  "route_thread_to_project"`) — `is_new_project` is computed business-side (a
  plain `guessed_project not in open_projects` membership check), never
  returned by Compass itself, keeping `guess_project_for_thread`'s own return
  contract to exactly the two keys the task specified. **`finalize_thread_
  project_routing` lives in `email_classification.py` (business layer),
  imported into `pending_approvals_router.py`'s `_APPROVAL_HANDLERS` dict** —
  the task file offered either home as acceptable; this mirrors `vault_filing_
  expert.finalize_new_top_level_area`'s own precedent exactly (a business-
  layer function, not router-embedded logic) rather than introducing a second
  shape for the same dispatch table. **Real, confirmed-live finding, worth
  remembering for any future `_APPROVAL_HANDLERS` deferred-write handler
  operating on a path stored in a Pending-Approval `payload`:** a payload's
  own stored path is always a plain `str` (JSON-serializable), never a `Path`
  — `finalize_thread_project_routing` must re-wrap it (`Path(payload[
  "thread_path"])`) before calling `vault_writer.upsert_frontmatter_key`/
  `read_note`, both of which require a real `Path` (`.read_text`/
  `.write_text`), confirmed by the exact same `AttributeError` class `T03`'s
  own Implementation Log already documented for `create_thread_note_
  baseline`'s return value. The router's own `outcome_message` construction
  is now additive: `result.get("message") or f"Approved — filed at
  {result['path']}."` — confirmed live that both pre-existing handlers
  (`finalize_new_top_level_area`, `finalize_hermes_write`, neither of which
  returns a `"message"` key) still fall through to the byte-for-byte original
  fallback text. Verified live end-to-end (manual mode, scratch vault,
  `VAULT_PATH` env-overridden, real Compass Provider, no mocking): a Customer
  with one real open Project produces exactly one Pending Approval naming
  that Project, the Thread's `project` key is confirmed absent before Approve
  and correctly set after; a Customer with zero open Projects produces a
  Pending Approval proposing a genuine new Project name, and Approve both
  creates the real Project directory (`project_concept_file_exists` flips
  `False`→`True`) and sets the Thread's `project` key; `created=False`
  confirmed as a true no-op via a before/after `list_pending_approvals`
  count; both Pending Approval records confirmed `trigger="direct"`; the
  pre-existing `propose_new_top_level_area` handler's own outcome text
  reconfirmed unchanged via a real live Approve + agent-history read-back.
  Full reasoning: task's own Implementation Log, `Implementation/Tasks/
  REQ-SB-55-US-01-T04-route-to-project-job.md`.

- [2026-08-16] `REQ-SB-55-US-01-T03` (`SPRINT-049`) — new `email_classification.
  thread_match_merge(email, classification, attachment_entries=None) -> dict`
  (the `Thread-Match/Merge` Job, `ADR-043` point 3) shipped and verified
  live. **Two real findings worth remembering for `T04`/`T05`/`T07`, this
  Pipeline's remaining Job/assembly tasks:** (1) `vault_writer.
  create_thread_note_baseline`'s own return value is a plain `str`
  (`write_note`'s contract) — it cannot be passed directly to
  `replace_body_section`/`append_body_section_line`/`upsert_frontmatter_key`/
  `read_note`, all four of which require a real `Path` (`.read_text`/
  `.write_text`). The correct pattern, confirmed live, is to resolve
  `path = vault_writer.thread_note_path(conversation_id)` once and use that
  same `Path` for every primitive call on both the create AND update
  branch — never the create call's own return value. (2) A Thread's `##
  Summary` region has no specified exact wording anywhere in `ADR-043`/
  `architecture.md` — this task deliberately builds it as a plain,
  deterministic rendering of the LATEST message only (timestamp/sender/
  subject/body), never an AI-abstracted synthesis (no second Compass call
  is available to this Job, per the parent story's own Constraint;
  `REQ-SB-57` owns real Glimpse-style synthesis later). **Never render a
  `**Customer:**`-labeled line inside a Thread's `## Summary`** — even a
  plain-text (non-wikilink) one is close enough to this story's own
  forbidden `**Customer:** [[Hub]]` inline convention to be a real footgun;
  `customer`/`kind` already live in the Thread's own frontmatter and need
  no body-level label. `thread_match_merge` writes `customer` ONCE (create
  only, never contradicted by a later message, per this task's own
  Constraint), unions tags via `T01`'s `upsert_frontmatter_key` (read
  current, union with `build_tags(customer, kind)`, write back — nothing
  previously present ever removed), accumulates `participants`, and
  unconditionally overwrites `last_message_at` on every call. Verified live
  end-to-end (manual mode, scratch vault, `VAULT_PATH` env-overridden): a
  first message creates exactly one Thread note with real `## Summary`
  content; a second message in the same conversation resolves to the
  identical path, regenerates `## Summary` with zero residue of the first
  message's own exact wording, and grows `## Transcript` in call order
  (`AC-01`); an attachment sub-entry lands in its own `## Attachments`
  region kept separate from `## Summary` (`AC-02`); tags union across a
  kind change with no previously-present tag removed (`AC-07`);
  `participants` accumulates 3 distinct senders and `last_message_at`
  reflects the most recent message; `ensure_customer_hub_note` confirmed
  called, no inline Customer wikilink ever written. `ast.parse()` clean; no
  file outside `## Files to Modify` (`email_classification.py` only) was
  edited — `vault_writer.py`/`customer_hub_linking.py` were only read. Full
  reasoning: task's own Implementation Log, `Implementation/Tasks/
  REQ-SB-55-US-01-T03-thread-match-merge-job.md`.

- [2026-08-16] `REQ-SB-55-US-01-T02` (`SPRINT-049`) — `compass_client.
  classify_email`'s return contract gained one additive field,
  `recurring_candidate: bool` (default `False` on missing/unparseable,
  mirroring the existing `customer`/`kind` fallback convention), and a new
  `email_classification.classify_captured_email(email, known_customers,
  known_kinds) -> dict` thin wrapper exists as this Pipeline's own `Classify`
  Job — the SAME single `classify_email` call, never a second/parallel
  Compass call. **The general/structural detection requirement (Scenario 6/
  `AC-06` — never a rule hardcoded to one customer's known format) is
  satisfied entirely through prompt wording, not code branching**: the
  prompt instructs Compass to judge purely from structural signals
  (repeating/patterned layout, labeled fields, tabular/itemized data) and
  explicitly frames its illustrative examples (invoice, weekly usage
  report, automated export) as non-exhaustive shape examples, never a
  matching rule — confirmed live that the SAME mechanism correctly flags
  two structurally different test artifacts from two unrelated (fictitious,
  not-in-`known_customers`) senders. **Any future consumer of
  `recurring_candidate` (`T06`'s own `Detect-Recurring-Pattern` Job) should
  read this field directly off `classify_email`'s/`classify_captured_email`'s
  return dict — do not add a second classification call or a second
  structural-detection mechanism.** Full reasoning: task's own
  Implementation Log, `Implementation/Tasks/
  REQ-SB-55-US-01-T02-classify-recurring-pattern-detection.md`.

- [2026-08-16] `REQ-SB-55-US-01-T01` (`SPRINT-049`, first task of the Email
  Capture & Threading Pipeline, `ADR-043`) shipped and verified live. Two
  genuinely new `vault_writer.py` primitives added: `append_body_section_
  line(path, header, line)` — a header-SCOPED, growing body-section append,
  generalizing `replace_body_section`'s own header/next-header location
  logic (the identical literal, whole-line regex match) from full-region
  REPLACE to insert-just-before-the-region's-own-end; unlike
  `replace_body_section`'s documented no-op-if-absent contract, this
  primitive CREATES a missing header at end-of-file on first use (a
  GROWING section, e.g. a Thread's `## Attachments`, may not exist yet,
  unlike a REGENERATED section which always already has its header from
  baseline) — this is now the canonical mechanism for any note section that
  grows by accumulation rather than full regeneration, the sibling to
  `replace_body_section`'s "regenerate, don't patch" contract for sections
  that instead "accumulate, don't replace." `list_customer_projects
  (customer) -> list[dict]` — enumerates one Customer's own `projects/*/`
  subdirectories, returning `{"project", "slug", "status"}` read directly
  from each Project's own concept-file frontmatter (never fabricated),
  `[]` for a Customer with no Projects yet; mirrors `list_known_customers`'s
  own dynamic, vault-derived, never-hardcoded enumeration style. **Real
  finding, logged as a scope-internal judgement call (not an escalation):
  this task's own third named primitive — an unconditional frontmatter-key
  setter (overwrite-if-present, insert-if-absent) — already existed in this
  codebase before this task, as `vault_writer.upsert_frontmatter_key(path,
  key, value)` (`REQ-SB-09-US-01-T01`, `SPRINT-028`, see this file's own
  [2026-08-13] entry).** It is fully generic (no `due`/`status` hardcoding
  in the function body — the [2026-08-13] entry's "due/status only"
  phrasing described its only callers at the time, not an enforced scope),
  and already handles list values identically to scalars via
  `_format_frontmatter_value`. Rather than write a second, functionally-
  duplicate primitive under a new name, `T01` reused
  `upsert_frontmatter_key` directly and did not modify `vault_writer.py`
  for that part of its own scope at all. **Any future
  `participants`/`last_message_at`/tag-union write in this pipeline
  (`T03`/`T04`/`T05`) or in `REQ-SB-63-US-01-T03` (`SPRINT-050`) should call
  `vault_writer.upsert_frontmatter_key`, not a new function** — there is
  only ONE unconditional frontmatter-key-setter primitive in this codebase,
  under that name. Verified live end-to-end (manual mode, scratch vault,
  `VAULT_PATH` env-overridden): two sequential appends to an existing `##
  Transcript` region land in call order with `## Summary` untouched; a
  first append to an absent `## Attachments` header creates it at EOF with
  exactly that one line, a second append grows the SAME single header
  (never a duplicate); `upsert_frontmatter_key` overwrites an existing
  `tags` list value, inserts an absent `project` key, then overwrites that
  same key again in place (no duplicate frontmatter line); `list_customer_
  projects` returns `[]` for a Customer with zero Projects and 2 accurate
  entries once 2 real Project directories exist. `ast.parse()` of the full
  file confirmed clean; no pre-existing function was altered. No locked
  parent-story AC is verified by this foundational task directly — its own
  Tests verify the primitives' own correctness, consumed by `T03`/`T04`/
  `T05`'s real AC-tagged steps. Full reasoning: `Implementation/
  Architecture/ADR.md` → `ADR-043` Consequences; task's own Implementation
  Log: `Implementation/Tasks/
  REQ-SB-55-US-01-T01-vault-writer-thread-primitives.md`.

- [2026-08-16] `REQ-SB-54-US-01` (Vault Knowledge Model Redesign — Threads/
  Meetings/Manual Captures evidence layer, OKF-conformant Customer/Project
  synthesis directories, `SPRINT-048`) shipped end-to-end and verified
  live, per `ADR-042`. All 6 tasks Done, all 5 locked ACs
  (`AC-01`..`AC-05`) verified: `AC-01` (a multi-message Outlook
  conversation collapses into exactly one Thread note, `## Summary`
  regenerated / `## Transcript` appended, `T02`); `AC-02` (Manual Captures
  in `captures.md` are appended directly, never rewritten by any
  concept-file regeneration code path — structurally, not just
  conventionally, unreachable, `T04`/`T05`); `AC-03` (a real Customer
  directory carries the full 4-file OKF shape — `index.md`/`<slug>.md`/
  `log.md`/`captures.md` — with the update-ownership boundary
  structurally enforced, `T04`); `AC-04` (`replace_body_section` locates
  a `##`-headed section by literal header text, never a cached byte
  offset, and replaces the bounded region wholesale, `T01`); `AC-05` (a
  Project directory, nested at `Work/Customers/<slug>/projects/<slug>/`,
  carries the identical OKF shape as Customer, `T05`). **New primitive
  family, this codebase's canonical mechanism going forward for any
  "regenerate, don't patch" full-region body rewrite:**
  `vault_writer.replace_body_section(path, header, new_content)` (`T01`,
  see its own dedicated entry below) plus a generic, reusable
  directory-shaped-note-kind family — `okf_directory_paths`/
  `okf_concept_file_exists`/`create_okf_directory_baseline`/
  `ensure_okf_directory_baseline` (`T04`) — applied to Customer (`T04`)
  and then reused UNCHANGED for Project (`T05`, five thin wrappers, zero
  duplicated 4-file-creation logic). **Customer and Project are now the
  ONLY two directory-shaped note kinds in this codebase, by deliberate,
  non-generalized design** (`ADR-042`'s own Alternatives Considered
  reject extending the directory shape to any other kind as scope
  creep) — every other note kind (Threads, Meetings, People, Partners,
  Tasks) stays a flat file. `list_all_note_paths()` (`T06`, the flagged
  `architecture.md` Consequence) now discovers both the flat one-level
  note kinds AND the two-/four-levels-deep Customer/Project concept
  files via two additional HARDCODED globs
  (`Customers/*/*.md`/`Customers/*/projects/*/*.md`) unioned with the
  original one-level glob, excluding `index.md`/`log.md`/`captures.md`
  by filename (OKF-reserved, no ordinary frontmatter shape) — every
  downstream consumer of this function (`list_known_customers`,
  `list_known_partners`, `retrofit_customer_hub_links`,
  `list_notes_matching_scope`) now sees these concept files without
  further code changes. **A real, live-discovered architectural
  consequence found and disclosed, deliberately NOT fixed by this
  story:** `app/business/partner_hub_linking.py::migrate_customer_to_
  partner` (`REQ-SB-16`, already `Done`) still depends on the OLD
  flat-file Customer hub-note primitives (`hub_note_path`/
  `hub_note_exists`), left completely untouched by `T04` — any Customer
  onboarded AFTER this story ships gets ONLY the new OKF directory
  shape, so a future real Customer→Partner reclassification for such a
  customer will silently no-op its hub-note-move step; re-filed as its
  own `REVIEW-QUEUE.md` item (not fixed here, `ADR-042`'s own scope
  excludes generalizing the directory shape to Partner). `customer_hub_
  linking.ensure_customer_hub_note`'s external return contract
  (`{"hub_note_path": str, "created": bool}`) is UNCHANGED — all 5 real
  call sites (`email_classification.py`, `meeting_classification.py`,
  `people_extraction.py`, `todo_classification.py`,
  `vault_filing_expert.py`) keep working with zero modification.
  Verified live end-to-end via a throwaway scratch vault (session
  scratchpad, `VAULT_PATH` env-overridden — the real configured vault
  never touched by any test run in this story). Two open, non-blocking
  `REVIEW-QUEUE.md` spot-check items remain from `T04`/`T05` (Customer/
  Project directory slug casing uses the codebase's existing
  case/space-preserving `_slugify()`, not a lowercase-hyphenated slug;
  a small private `_project_directory_root` helper factors out a
  three-line computation the task's own illustrative code repeated
  inline) — neither affects any locked AC or blocks downstream work.
  Full reasoning: `Implementation/Architecture/ADR.md` → `ADR-042`;
  `Implementation/Architecture/architecture.md` → "Vault Knowledge Model
  Redesign..."; each task's own Implementation Log under
  `Implementation/Tasks/REQ-SB-54-US-01-T01`..`T06`;
  `Implementation/Sprints/SPRINT-048-vault-knowledge-model-redesign.md`'s
  own Retrospective.

- [2026-08-16] `REQ-SB-54-US-01-T01` (`SPRINT-048`) — new
  `vault_writer.replace_body_section(path, header, new_content)` primitive
  shipped and verified live, per `ADR-042` point 2. This is now the
  canonical mechanism for every "regenerate, don't patch" full-region body
  rewrite in this codebase (a Thread's `## Summary`, a Customer/Project
  concept file's `## Glimpse`/`## Background`) — it replaces
  `insert_body_line_if_missing`'s fixed-byte-offset-from-frontmatter
  approach for any section meant to reflect current state, which is
  fragile against a note touched many times over its life (`BUG-003`/
  `ESC-003`, still `Open` — that primitive itself is unchanged, just no
  longer the right tool for regenerated sections going forward). One
  refinement over the task's own illustrative sketch, worth remembering as
  a standing pattern: locate the header via a literal, whole-LINE regex
  match (`re.compile(r"^" + re.escape(header) + r"$", re.MULTILINE)`),
  never a raw substring `str.find(header)` — a substring search would
  false-positive on a header string appearing mid-line elsewhere in the
  file. A nested `###`+ subheader inside the same section is deliberately
  NOT a section boundary, only another `## `-level header is. Full
  reasoning: `Implementation/Architecture/ADR.md` → `ADR-042`; task's own
  Implementation Log: `Implementation/Tasks/
  REQ-SB-54-US-01-T01-replace-body-section-primitive.md`.

- [2026-08-15] `ADR-041` — Agent/Pipeline/Job/Hub domain-model taxonomy
  adopted, superseding `ADR-040`'s fixed Pull/Tag/Link/Store agent-chain
  shape (`REQ-SB-53`, now parked). Trigger: `ADR-040` forced 4 pipeline
  stages into the existing Worker/Producer/Expert Type model and the
  4th stage (Linker) was genuinely, structurally ambiguous across all 3
  — not a values-question, a sign the taxonomy had no correct slot for
  what a pipeline stage actually is. Operator stopped all forward
  implementation and drove a from-scratch taxonomy discussion instead:
  "this is getting messy... let's discuss all types of Agents." **The
  model going forward has two independent axes, not one flat type
  list:** *kind of work* (Expert = answers questions; Producer =
  composes/generates a deliverable — file, email reply, to-do action;
  the mechanical pipeline verbs = fetch/classify/link/store/etc.) crossed
  with *structural tier* (Agent = full, independently-addressable —
  own chat/history/Working Mode/Map node; Job = lightweight, lives
  inside a Pipeline's own DAG — own prompt + Skill(s), no guaranteed own
  chat/Map/Working-Mode). A Producer can be either tier (standalone
  Agent OR a Job embedded in someone else's Pipeline); Expert is always
  the Agent tier; the mechanical pipeline verbs are always the Job
  tier. **Hub** = a Section's own manager (routes to its Pipelines/
  Experts) AND database (holds its own file/vault-scope + agent/pipeline
  registry) — not a new tier, the existing Section concept with an
  explicit job description. **Pipeline** = a user-extensible DAG of
  Jobs (fork/merge/branch-to-Expert-consultation, confirmed via a real
  worked example: an email forks into body-classify + attachment-
  classify Jobs, merges back, optionally branches to consult an "Opps
  Expert" mid-flow, always terminates in Store) — NOT a fixed N-stage
  chain engineers hardcode per pipeline type; the user adds/removes/
  rewires Jobs themselves via a builder. **Prompt customization is
  universal** — one "edit this thing's own instructions" mechanism
  across every Agent and every Job. **Execution engine: LangGraph** — a
  Pipeline's own author-defined DAG compiles to a `langgraph.graph.
  StateGraph` at runtime; this narrows `ADR-007`'s original "simple
  linear pipelines stay outside any orchestration framework" carve-out
  FURTHER than `ADR-015` already did (which bounded LangGraph to in-app
  AGENT behavior — chat/Hub-routing/memory/skill-invocation — and left
  linear classification pipelines outside it, unreconsidered until now).
  `langgraph` is already a real, installed dependency (`ADR-015`) — this
  is a scope widening of an existing tool, not a new one; confirmed via
  direct reconsideration against the operator's own real question
  ("shouldn't LangGraph handle this agent-to-agent retry and stuff?",
  `ESC-036`) which had, notably, been answered "no, stay hand-rolled"
  for `ADR-040`'s OWN narrower, non-branching, no-visual-authoring
  scope — the answer flipped once the real scope grew to include
  genuine forking/merging/conditional branching and a visual builder.
  **Builder: a native React Flow canvas inside the existing frontend**,
  not an external tool (LangFlow/Flowise-style options explicitly
  considered and declined) — keeps one cohesive product sharing the
  same Hub/Section/Agent/Skill data model and the Agents Map's own
  visual language. **This is directional/foundational, not
  implementation-complete** — the DAG's own persisted data model, the
  checkpointer's own cross-restart durability backend (a real open
  question: LangGraph's own `SqliteSaver` would be this project's FIRST
  departure from flat-JSON `.second-brain/` persistence, a standing
  convention nothing has broken yet), the canvas UI/UX, and whether/how
  a Job ever earns its own Agent-like surface are all explicitly left
  open for whatever requirement formally specs the Pipeline Builder.
  `REQ-SB-53` and its 3 sibling stories stay `Draft`/parked (not
  cancelled) in `BACKLOG.md` until re-specced against this model. Full
  reasoning: `Implementation/Architecture/ADR.md` → `ADR-041`;
  `Implementation/Architecture/architecture.md` → "Agent / Pipeline /
  Job / Hub Domain Model — Taxonomy" (near the top of the file, by
  design — this is meant to be read before any future agent-shaped
  addition anywhere in this codebase). **Sequencing, decided the same
  day immediately after this ADR: the Builder is explicitly deferred
  until at least ONE real Pipeline is hand-built under this model
  first** — "We will build the pipeline Builder once we build actual
  Pipeline and know what we need to do." Do not start the Builder before
  a concrete Pipeline (most likely Email capture, the fully worked
  example) is real. See `ADR-041`'s own Consequences for the full note.

- [2026-08-15] `REQ-SB-52` real Agents Map (`src/frontend/src/features/
  agents-map/`) — operator directed a deliberately NARROW direct port from
  the still-in-progress exploration prototype (`html-prototype/agents-map-
  skilltree-exploration.html`) straight into the canonical app, bypassing
  `/spec`/`/plan-tasks` for this one scoped visual change: "Port the CSS,
  the KB new Design and KB new Lines we Built Leave the Rest till We
  finish the prototype." Three pieces ported: `KnowledgeBaseNode.tsx`'s
  hand-authored 23-neuron mesh replaced by a seeded-random 220-dot
  constellation (same LCG recipe) with hover-rotate-and-freeze; `.hub-node`
  CSS replaced dashed-border/tinted-fill with a thin-ring + soft-halo
  treatment (still keyed off the existing `--hub-color` custom property,
  zero change to Worker/Producer/Expert color-keying); `.spoke-line`s
  (`AgentsMapCanvas.tsx`) moved from center-to-center to real edge-to-edge
  endpoints plus two `<animateMotion>` traveling dots per line, timing
  derived from each Section's own array index (not hardcoded — the real
  app's Section count is dynamic, unlike the prototype's fixed 6).
  **Colors were adapted, not copied** — the prototype is a dark theme
  (ivory/copper), the real app is light-theme/green
  (`--color-accent`/`--agent-color-*`, `tokens.css`); every ported value
  reused the real app's own existing tokens. The Sections View/Agent-in-
  Focus work stays prototype-only, explicitly deferred by the operator
  until finished there. **A separate, larger ask surfaced in the same
  conversation — an icon-library feature (assignable icons for Agents and
  Section Hubs) — was explicitly NOT built ad hoc**: operator confirmed
  via AskUserQuestion this should go through the normal `/spec ->
  /plan-tasks` pipeline instead, once scoped as its own story. Verified
  live: `tsc -b --noEmit` clean, zero console errors, 220 constellation
  dots confirmed via direct DOM query, hub border/shadow computed styles
  matched target values exactly, spoke-line endpoints confirmed at real
  edge coordinates (not center), hover-spin-freeze confirmed by measuring
  actual rotation advance over a real hover then a frozen post-mouseleave
  value, Hub-click -> Section drill-down reconfirmed unaffected.

- [2026-08-14] `REQ-SB-49-US-01` (Cockpit Inline `@agent_id` Mention
  bring-in) and `REQ-SB-49-US-02` (Cockpit `@PersonName` Person-Directed
  Instruction → proposed Person-note edit, `SPRINT-046`) both shipped
  end-to-end and verified live. `US-01`: send-time `@token` extraction/
  exact-match resolution against `Cockpit.tsx`'s own `bringInCandidates`
  list, calling the existing `bringInAgent` unmodified before
  `sendCockpitMessage`; the chat `<input>`'s `disabled={!hasExperts}` is
  gone (Send alone carries the now-relaxed gate); a live prefix-filtered
  suggestion dropdown reads the same list. `US-02`, per `ADR-038`: a new
  bound tool `propose_person_note_update`, intercepted in `graph.py`
  before `execute_tools` (mirrors `record_knowledge_gap`), this graph's
  first CONDITIONALLY-bound tool (`skill_registry.has_skill_access`-
  gated); resolves the real Person note read-only first
  (`people_extraction.find_person_note_by_name`, new), then dispatches
  through `skill_registry.invoke_skill(..., trigger="cockpit_mention")`
  — a new trigger literal, zero new gate branches. A new `mutates: True`
  Skill (granted to `people-producer`) branches on a new
  `_dispatch_skill(..., already_approved: bool = False)` seam
  (signature-introspection-forwarded, mirrors `agent_id`): Supervised's
  existing Pending-Approval Approve click is already the confirmation
  (unchanged); Manual/Autonomous (zero human click in its own dispatch
  path) records an in-thread confirmable/discardable proposal instead of
  writing immediately — new `app/business/cockpit/
  person_note_proposals.py` (create/list/confirm/discard, stored inside
  the owning thread's own `cockpit_threads.json` record, never a new
  top-level state file), two new confirm/discard endpoints, a new
  `.chat-proposal`-shaped pending-proposal region reusing the existing
  quick-research visual pattern verbatim. **Two real, live-discovered
  integration bugs found and fixed in-scope, both worth remembering as
  standing hazards for future work on these same shared files:** (1) any
  new `skill_tools.SKILLS` entry MUST carry a `"tool"` field —
  `skill_registry.list_agent_capabilities` (`REQ-SB-48-US-01`) requires
  it unconditionally for every granted Skill; omitting it only surfaces
  as a live `KeyError` once an agent is actually granted the new Skill
  and its capabilities are listed via the HTTP layer, never from an
  isolated business-layer smoke check. (2) `threads.send_user_message`
  reads its own `thread` dict ONCE and saves it ONCE, at the very end,
  after its whole per-agent reply loop — any future capability that lets
  a nested call (a Skill dispatched mid-loop) do its own independent
  `get_thread`/`save_thread` round trip on a NEW field of the SAME thread
  record will have that write silently clobbered unless
  `send_user_message` is taught to re-read and carry that specific field
  forward immediately before its own final save (now done for
  `person_note_proposals`) — any FUTURE such field needs the same
  treatment, not just this one. Verified live end-to-end: all 5 `US-01`
  ACs and all 6 `US-02` ACs, including both gate-behavior paths (real
  Supervised Approve/Decline via direct `invoke_skill`/HTTP calls; real
  Manual/Autonomous "propose" via real live Compass model calls) and a
  real CDP-driven browser session confirming the actual confirm/discard
  UI writes/doesn't-write to a real Person note. `ADR-038` held up
  exactly as designed under live verification — no adr-deviation trigger
  fired; the story's own `gate: flagged` (trigger-3, `ADR-038` human
  review) stays open as a standing breadcrumb, not resolved by this pass.
  Full reasoning: `Implementation/Architecture/ADR.md` → `ADR-038`; each
  task's own Implementation Log under `Implementation/Tasks/
  REQ-SB-49-US-01-T01`, `REQ-SB-49-US-02-T01`..`T06`.

- [2026-08-14] `REQ-SB-47-US-01` (Per-Agent Scheduler — Schedule tab
  configure/edit/remove/run-now/run-history, generalized across every
  agent's own granted mutating capabilities, built together with
  `REQ-SB-45`'s shared Outlook-COM dispatch lock, `SPRINT-045`) shipped
  end-to-end and verified live, per `ADR-037`. New `app/business/
  agent_schedule_registry.py` is the single canonical home for: persisted
  composite-key (`"<agent_id>::<capability_id>"`) schedule CRUD, backed by
  a new sibling `.second-brain/agent_schedules.json` and paired
  `vault_writer.py` I/O primitives; the live `AsyncIOScheduler` reference
  (`capture_scheduler.lifespan()` calls `set_live_scheduler(scheduler)`
  once at startup, before `scheduler.start()` — `app/business/` gains its
  first dependency on a live third-party scheduler INSTANCE, never on
  `app.scheduling` itself, keeping `ADR-005` point 5's one-directional
  `scheduling → business` edge intact); and the shared, in-process
  dispatch lock (`dispatch_with_shared_lock`, generalizing
  `capture_scheduler.py`'s former private `_capture_run_lock` — explicitly
  in-process only, a disclosed non-solution for the cross-process
  `SPRINT-030` collision class). `skill_registry.invoke_skill` gained a
  new `"scheduled"` trigger literal + one Manual-mode silent-skip branch
  (zero history entries); on-demand "run now" reuses the existing
  `"direct"` literal, unchanged. New `app/api/agent_schedules_router.py`
  (`GET`/`POST`/`PATCH`/`DELETE` + `POST .../run-now`); run history reuses
  `REQ-SB-11`'s existing `GET /agents/{id}/history`, no new endpoint.
  **Real, live-discovered defect found and fixed in-scope (not present in
  `ADR-037`'s own illustrative text):** `dispatch_with_shared_lock`'s
  generic outcome-recording double-recorded two real cases — a Supervised
  Skill's own "proposal" entry (already written by `invoke_skill` itself)
  and `run_capture_now`'s real `email-capture` dispatch (already recorded
  internally by `email_classification.run_capture_and_record_completion`,
  with no `"history_recorded"` flag on its return value, unlike
  `build_knowledge`) — confirmed live, then fixed generically via a
  before/after history-length comparison instead of a hardcoded exclusion
  list, so it also covers any future self-recording handler. **The
  shared-lock property (this story's own single highest-risk guarantee)
  was confirmed live via two independent techniques**: an in-process
  `asyncio.gather` call with explicit start/end timing markers (zero
  overlap, exactly one real dispatch + one honest skip), and a genuinely
  real, unplanned HTTP-layer race — a concurrent `run-now` request for a
  second agent arriving while `email-capture`'s own real, multi-minute
  Outlook-COM blob tick (a large real backlog: 2 emails, 35 meetings, 100
  tasks) was still in flight, honestly skipped and recorded. The Schedule
  tab (`AgentDetailPanel.tsx`'s 6th tab) shipped without a `/design` pass —
  a disclosed, non-blocking flag carried from the story's own Notes — real
  CDP-driven verification (creation/edit/remove/run-now/capability-
  scoping/run-history-parity) plus a real screenshot confirmed it renders
  correctly against the panel's existing visual language. Full reasoning:
  `Implementation/Architecture/ADR.md` → `ADR-037`; each task's own
  Implementation Log under `Implementation/Tasks/REQ-SB-47-US-01-T01`..
  `T06`.

- [2026-08-14] `REQ-SB-51-US-01` (Background Agents — explicit opt-in
  flag, excluded from Hub-routing and Cockpit addressing, displayed in a
  separate Agents Map area, `SPRINT-044`) shipped end-to-end and verified
  live, no new ADR (ordinary CRUD-pattern extension of `ADR-014`'s/
  `ADR-018`'s already-Accepted "new persisted concern composed alongside
  `agent_registry.py`, self-healing default, `PATCH`-endpoint-plus-edit-
  control" shape). New `app/business/background_agent_registry.py`
  mirrors `working_mode_registry.py`'s exact self-healing shape (default
  folded into `_load_state()`, no separate seed step), backed by a new
  sibling `.second-brain/agent_background_flags.json` — the one
  deviation from that precedent's uniform default: a literal 3-id
  exception set (`email-capture`/`meeting-capture`/`todo-capture`)
  self-heals to `True`, every other known agent to `False`, so the 3
  real capture-pipeline Workers are already correctly flagged with zero
  manual migration step. `GET`/`PATCH /agents` merge/accept
  `is_background_agent` the same way `working_mode` already does.
  **Exclusion is enforced at exactly 2 real points, never a second
  independently-filtered copy:** `agent_keywords.
  list_candidate_agents_for_keyword_match` skips a Background Agent
  inside its existing per-agent loop (confirmed live: never a
  Hub-routing candidate even with a real matching keyword assigned;
  `graph.py::_route_hub_request` — the confirmed sole call site — needed
  no change); a new shared `isBackgroundAgent(agent)` predicate
  (`agentsApiClient.ts`) is consumed by `Cockpit.tsx` (filters the
  Available Agents bring-in list) and `layoutAgents.ts` (partitions
  Background Agents out of ring placement/`REQ-SB-38-US-01` density
  clustering into a new `backgroundAgents` field, before
  `agentsBySection` is built) — `REQ-SB-49-US-01`'s own not-yet-built
  `@mention` suggestion list inherits this filter automatically once it
  ships, since it's specced to reuse the same `fetchAgentList()` source.
  `AgentsMapCanvas.tsx` gained a new, purely additive "Background Agents"
  `.card`/`.item-list` rail (no fresh `/design` pass — reused the
  screen's own existing visual vocabulary, per this session's own
  established "small, standard, vocabulary-reusing addition" convention)
  — clicking a row opens the identical `AgentDetailPanel` via the
  existing `onSelectAgent` callback. `AgentDetailPanel.tsx`'s Settings
  tab gained one new "Background Agent" checkbox row mirroring the
  Working-mode row's own handler shape. **A Background Agent's own
  direct reachability is never restricted** — confirmed live: its
  Overview/Chat/History/Settings tabs, a real direct chat message
  (genuine LLM reply), and a real direct action-trigger request all
  behave identically to any non-Background agent; only OTHER agents' and
  the Cockpit's own addressing paths exclude it. **Full end-to-end
  restoration (un-marking) independently confirmed live, no restart:**
  toggling `email-capture`'s flag off via the real Settings UI
  simultaneously restored its Hub-routing candidacy (backend-layer), its
  presence in a real Meeting Cockpit's Available Agents list, and its
  placement on the Agents Map's main ring instead of the rail — all 3
  checked live in one continuous session, then reverted and
  independently reconfirmed back to the original backfilled state. All 9
  locked ACs verified live with a real, observed outcome; no
  `ESCALATIONS.md`/`REVIEW-QUEUE.md` entries. Full reasoning:
  `Implementation/Architecture/architecture.md` → "Background Agents —
  explicit opt-in exclusion from Hub-routing and Cockpit addressing";
  each task's own Implementation Log under `Implementation/Tasks/
  REQ-SB-51-US-01-T01`..`T06`.

- [2026-08-14] `REQ-SB-46-US-01` (Agent Creation Wizard Redesign — Agents
  Map FAB, popup modal, visual 4-step progress bar, reorganized field
  groupings, additive Trigger metadata, `SPRINT-043`) shipped end-to-end
  and verified live, per `ADR-039`. Entry point relocated from Settings'
  `+ Create agent` `<details>` disclosure (now deleted, `CreateAgentCard.tsx`)
  to a new bottom-right `.map-fab` on the Agents Map, opening
  `CreateAgentWizard.tsx` (renamed `CreateAgentWizardModal.tsx`) as a
  centered popup modal — deliberately NOT reusing `.side-panel-overlay`/
  `.side-panel`'s class names or edge-anchored slide-in behavior (confirmed
  live: zero shared class names between the two overlays). A new
  `.wizard-step-bar` (4 circles, current-step highlighted via
  `color-mix(...)` against `--color-accent`, matching `.hub-node`/
  `.map-overflow-marker`'s own existing glow idiom) replaces the old
  three-branch `step === 'type'|'expert'|'worker'|'producer'` screen with
  ONE shared field set per step: Step 1 (Name/Type/conditional
  Description-Expert-only-or-Scope-Worker-only/Section), Step 2
  (Working-mode selector for every Type + Producer-only Purpose/output
  Skill), Step 3 (the REAL shared `SkillsTree.tsx`, `mode="select"`,
  required ≥1 for Worker, optional for Expert/Producer — extending
  multi-select Skills selection to Expert/Producer for the first time),
  Step 4 (read-only summary + Trigger choice + Create). **`SkillsTree.tsx`'s
  real shipped shape (from `REQ-SB-48-US-01-T02`/`SPRINT-042`) was
  reconciled directly before writing Step 3** — its real `mode="select"`
  props (`skills`/`selectedIds`/`onChange`, each skill object needing a
  `granted: boolean` field even though unused there) differ from
  `ADR-039`'s own illustrative `tools={...} skills={...}` guess; no second,
  divergent Skills-tree implementation was written. Backend: `POST
  /agents`'s `CreateAgentBody` gains one additive `trigger: str | None =
  None`, appended uniformly to every type's own `settings` kv-list
  (`{"key": "Trigger", "value": trigger or "user"}`) — no new endpoint, no
  schema change; Schedule/Agent Trigger values are purely metadata (no new
  mechanism, confirmed live: a Trigger="agent" agent's chat behaves
  byte-identically to any other agent). Every per-type submit call
  sequence stays unchanged in count/order/shape from today's shipped
  wizard (verified live via a real `window.fetch` spy filtered to non-`GET`
  calls, isolating the submit sequence from `AgentsMapPage.tsx`'s own new,
  legitimate post-create map-refresh `GET` calls), extended only with
  `trigger` + a now-sent `working_mode` (additive param on the existing
  `updateAgentAssignment` PATCH, not a new call). **Regression guard
  verified for all 3 types**, including one Expert agent cross-checked
  byte-for-byte against a parallel, independent direct `POST /agents` +
  `PATCH` call with identical inputs. **Two disclosed scope-internal
  judgement calls, not escalations:** (1) all 4 steps were built in one
  coherent pass over the single tightly-coupled file rather than 5
  separate non-compiling checkpoints, each task still verified and marked
  `Done` independently against its own locked ACs only; (2) Expert's own
  optional Step-3 Skills selections are granted at submit time (a
  structural no-op when none are selected, satisfying AC-07's literal
  2-call Expert case exactly) rather than silently discarded, extending
  Worker's/Producer's own existing "loop-grant selected Skills" shape
  uniformly to Expert too. Full reasoning: `Implementation/Architecture/
  ADR.md` → `ADR-039`; each task's own Implementation Log under
  `Implementation/Tasks/REQ-SB-46-US-01-T01`..`T05`.

- [2026-08-14] `REQ-SB-48-US-01` (Skills Capabilities Tree — collapsible,
  icon-bearing, multi-select, grouped by Tool, `SPRINT-042`) and
  `REQ-SB-50-US-01` (Tags/Locations Autocomplete on the Vault Scope field,
  `SPRINT-042`) both shipped end-to-end and verified live, no new ADR for
  either. `skill_tools.SKILLS` gained a `"tool"` field
  (`Outlook`/`Vault`/`Web`/`Compass`) on all 11 entries, the single
  source of truth the frontend groups by (server-side, not a frontend
  static map — avoids catalog/UI drift as Skills grow). **New standalone,
  mode-parameterized `src/frontend/src/features/agents-map/
  SkillsTree.tsx`** (`<SkillsTree mode="manage" | "select" ...>`) is this
  codebase's first genuinely cross-story-shared UI component built ahead
  of its second consumer: `mode="manage"` (this sprint's own scope, a
  collapsible/icon/same-grant-state-only-multi-select tree over
  `AgentDetailPanel.tsx`'s Capabilities section) ships now;
  `mode="select"` is a real, working, but explicitly-provisional seam
  `REQ-SB-46-US-01-T04`/`SPRINT-043` depends on directly (`ADR-039`,
  this codebase's first cross-story frontend task dependency) — do not
  inline a future consumer of this exact filename/shape; extend the
  existing mode union instead. `vault_search.list_scope_suggestions()`
  composes the already-real `list_tags()`/`vault_writer.
  list_known_kinds()` into one `GET /vault-search/scope-suggestions`
  endpoint (no server-side `q=` filter — full snapshot, client filters);
  the Vault Scope field's suggestion dropdown reconfirms
  `SPRINT-020`'s own **Fiber-props direct-invoke technique for
  `onBlur`-driven React commit handlers** is still required in this
  project's CDP test environment (a raw synthetic `blur` `dispatchEvent`
  does not reliably reach React's own delegated listener), and adds
  `onMouseDown` + `preventDefault()` (not `onClick`) as the correct
  selection mechanism for any future click target that must register
  before a sibling input's own `onBlur` commit fires. **Found and
  disclosed, not fixed here (out of scope):** `BUG-013` —
  `skill_registry._load_state()` unconditionally re-applies its ENTIRE
  `_MIGRATION_GRANT_SEED` on every single state read, not just once, so
  an explicit revoke of any of the 7 migration-seeded Skill/agent pairs
  (from `REQ-SB-39-US-02`/`SPRINT-031`) never actually sticks — confirmed
  live via both a real browser round trip and a UI-free, direct
  Python-shell `skill_registry.revoke_skill_access(...)` call. See
  `BUGS.md` → `BUG-013`, `ESCALATIONS.md` → `ESC-035`. Full reasoning:
  each task's own Implementation Log under `Implementation/Tasks/
  REQ-SB-48-US-01-T01`/`T02`, `REQ-SB-50-US-01-T01`/`T02`.

- [2026-08-14] `REQ-SB-43-US-01` (Meeting Cockpit — 3-panel prep-and-live
  workspace with attendee chips, a unified multi-agent Expert chat, and
  explicit-save on-the-spot research, `SPRINT-040`) shipped end-to-end and
  verified live, per `ADR-036`: a new shared `app/business/cockpit/`
  sub-package (`threads.py`/`people.py`/`research.py`, generic over
  `subject_kind`/`subject_note_stem`, never two per-kind modules) and a
  new shared `Cockpit.tsx` frontend component, built as genuinely reusable
  infrastructure — `REQ-SB-44-US-01`/`SPRINT-041`'s own Inbox Cockpit
  builds directly on top via `depends_on` edges onto this sprint's own
  `T02`/`T05`/`T07`/`T08`, not a duplicate. **Multi-agent shared thread
  mechanism:** `threads.send_user_message` composes `ADR-015`'s existing,
  UNMODIFIED `run_agent_conversation` once per currently brought-in Expert
  per user message, sequentially, appending each real reply to the SAME
  shared `.second-brain/cockpit_threads.json` thread (this codebase's
  first multi-party, not per-agent, conversation store) tagged with its
  own `agent_id`/`agent_name`; each OTHER Expert's own prior turn is
  relayed into the CALLED Expert's own history view as a `chat_user`-kind
  entry prefixed `"[{agent_name} said]: "` — framed as relayed context,
  never as if the called Expert once said it itself — confirmed live with
  two real Experts (Vault Q&A, People Notes) replying distinctly inside
  one genuinely shared thread. **Working-mode gate:** confirmed live,
  by direct code inspection, that the Cockpit's own real mechanisms
  (an Expert's chat/tool-calling reply; the user's own explicit
  research-save) never reach `skill_registry.invoke_skill`'s gated
  dispatch path at all — no new `"cockpit"` trigger value was needed
  (`ADR-036` point 4). **Real, disclosed gap found live, worked around
  within task scope, not fixed at the primitive level:** `ADR-036` point
  7's claim that Meeting notes already carry an `attendees:
  list[{"name","email"}]` frontmatter field is factually wrong against the
  real codebase — no captured Meeting note has this field (attendee data
  lives only as body wikilinks, per `REQ-SB-08`), and `vault_writer.py`'s
  own real frontmatter parser cannot round-trip a list-of-dicts value at
  all (a Python-dict-repr write silently reads back as `[]`). Worked
  around entirely inside `cockpit/people.py` (accepts a JSON-encoded
  string as well as a native list) — no `vault_writer.py` change, so every
  real captured Meeting note today honestly shows zero attendee chips
  until a future story either writes `attendees` using this JSON-string
  convention or `vault_writer.py` itself gains native list-of-dicts
  support. Attendee-chip verification (AC-02/AC-03) used a real,
  hand-constructed test Meeting note for this reason, disclosed directly,
  not presented as organic production data. **On-the-spot research:** a
  decomposer-level mechanism choice (`trigger_research` Hub-routes from
  the requesting Expert to a real Research Expert, mirroring
  `knowledge_bootstrap.bootstrap_agent_knowledge`'s own proven Hop 1
  exactly, then invokes the already-`Done` `web-research` Skill) — verified
  live with a real Anthropic web-search call, both an honest refusal path
  (no grant) and a genuine positive result (temporary grant/Provider swap,
  reverted and independently reconfirmed, mirroring `SPRINT-035`'s own
  established protocol). Saving a research result is always a direct
  `vault_writer.write_note` call, never through `skill_registry` — verified
  live that the real Meeting note's own body is byte-for-byte unchanged
  after a save, and the new note carries a real `[[wikilink]]` to it.
  `REQ-SB-20`'s own Hub-routing behavior for a brought-in Expert was
  independently reconfirmed byte-identical before/after being brought into
  a real Cockpit chat. Full reasoning: `Implementation/Architecture/ADR.md`
  → `ADR-036`; each task's own Implementation Log under
  `Implementation/Tasks/REQ-SB-43-US-01-T01`..`T09`.

- [2026-08-14] `REQ-SB-44-US-01` (Inbox Cockpit — the Meeting Cockpit's
  3-panel pattern adapted for email, attachment review, reviewable draft
  replies, `SPRINT-041`) shipped end-to-end and verified live, per
  `ADR-036`, built directly ON TOP of `REQ-SB-43-US-01`'s SHARED
  `app/business/cockpit/`/`cockpit_router.py`/`cockpitApiClient.ts`/
  `Cockpit.tsx` — no duplication anywhere. **New Email `recipients`
  field hit the identical `vault_writer.py` list-of-dicts round-trip gap
  `REQ-SB-43-US-01-T03` already found for `attendees` — confirmed this is
  a REAL, general limitation of `_format_frontmatter_value`/
  `_parse_frontmatter_value`, not a one-off:** `email_classification.py`
  writes `recipients` as `json.dumps(...)` (a JSON-encoded STRING), the
  exact same workaround convention `cockpit/people.py` already accepts —
  confirmed live via a real, monkeypatched-Outlook `classify_recent_emails()`
  run that a real captured Email note's `recipients` field round-trips
  correctly through `read_note()`/`json.loads()`, and that `cockpit/
  people.py` (zero code changes) correctly renders real sender/CC chips
  from it — a real existing Person note as a clickable chip, a real
  non-existent one as the honest `.tag-chip--static` fallback. **Attachment
  review composes `REQ-SB-28-US-01`'s own `upload_storage`/
  `summarize_file` DIRECTLY** (never that story's own chat-upload HTTP
  endpoint, which auto-files via the Vault Filing Expert — not wanted for
  an already-vault-saved email attachment reviewed in chat), posting an
  honest result (or an honest failure — an induced extraction failure was
  verified to post honestly, never fabricate) into the shared thread as an
  ordinary chat turn, never a second skill-trigger surface — verified live
  against a real captured email's real PDF attachment, including a real
  Compass summarization call. **On-the-spot research reuses
  `REQ-SB-43-US-01-T04`'s own `research.py` UNCHANGED** — confirmed by
  direct reading (already generic over `subject_kind`) and live: a real
  Anthropic-backed research call, Save/Discard, and per-email research-list
  scoping (a second email's cockpit never showed the first email's saved
  result) all worked with zero new research code. **A drafted reply needs
  no new backend concept** — every Expert reply in the Inbox Cockpit gets a
  frontend-only Copy button (`enableDraftCopyAffordance`); confirmed live
  that clicking it copies the exact reply text, and confirmed by direct
  whole-codebase reading that no send/outbound-email code path exists
  anywhere. Full reasoning: `Implementation/Architecture/ADR.md` →
  `ADR-036`; each task's own Implementation Log under
  `Implementation/Tasks/REQ-SB-44-US-01-T01`..`T06`.

- [2026-08-14] `REQ-SB-28-US-01` (File upload on agent chat — Compass
  summarization + Vault Filing Expert handoff, `SPRINT-038`) shipped
  end-to-end and verified live, per `ADR-034`: a new
  `app/data_access/upload_storage.py` extends the `.second-brain/`
  flat-file convention to raw bytes for the first time
  (`.second-brain/uploads/`, one file per upload keyed by a generated
  id, deleted once summarized or on validation rejection — never the
  raw original filename alone, mirroring this project's own standing
  filename-uniqueness Constraint); accepted types are narrowed to
  text-bearing files only (`.pdf` via a new `pypdf` dependency, `.txt`,
  `.md`, 20 MB cap) — PNG/JPG image support is explicitly deferred
  (neither Compass nor `diagram-understanding` produces usable text
  today, confirmed by direct inspection). `compass_client.
  summarize_content(content, source_description)` follows
  `classify_email`/`classify_task`'s exact payload/`CompassError`
  shape. **`summarize-file` is this project's first real (non-stub)
  Skill implementation**, registered through the already-`Accepted`
  `ADR-015` Skills extensibility path with zero new architecture for
  that part — its own handler never raises for ordinary control flow,
  returning an honest `{"status": "error", ...}` on `CompassError`
  instead of a fabricated summary. The new additive `POST
  /agents/{agent_id}/chat/attachment` (`agents_router.py`) composes
  upload validation/storage/extraction → the auto-granted (mandatory
  default capability, unconditional/idempotent grant — deliberately
  NOT `skill_registry.py`'s own default "explicit-grant-only" posture,
  a documented one-Skill exception) `summarize-file` Skill → the
  already-`Done` Vault Filing Expert's `determine_placement_and_file`,
  deleting the temporary upload on every reachable path regardless of
  downstream filing outcome, and preserving/showing the real summary
  text (never discarding it) when filing itself fails. The existing
  `POST /agents/{agent_id}/chat` JSON contract is confirmed untouched.
  Verified live end-to-end against all 10 locked ACs with real files: a
  real `.txt` and a real, hand-built `.pdf` (no PDF-authoring library
  available in this environment) both flowed through extraction → a
  real Compass summary genuinely reflecting the file's own content →
  filing into the vault with real tags/frontmatter/a real `[[wikilink]]`
  to a freshly-created hub note, for a genuinely new (not previously
  known) customer; both honest-rejection paths (unsupported type, size
  limit) confirmed with zero storage/API calls; a real induced Compass
  failure and a real induced Vault-Filing-Expert-unavailable outcome
  both confirmed honest, non-fabricating, with the latter's real
  summary confirmed preserved in the reply rather than silently
  dropped. Frontend (`AgentDetailPanel.tsx` Chat tab + `agentsApiClient.
  ts`'s new `sendChatMessageWithAttachment`, a raw `fetch` bypassing
  `client.ts`'s hardcoded JSON `Content-Type`) verified via a
  from-scratch Python `websockets`-based CDP driver against a real
  headless Edge browser (no Playwright/Puppeteer installed in this
  repo) — `DOM.setFileInputFiles` is the correct CDP primitive for
  real file-input interaction (a native-setter/dispatchEvent technique
  cannot set `.files` on a file input at all). Full reasoning:
  `Implementation/Architecture/ADR.md` → `ADR-034`; each task's own
  Implementation Log under `Implementation/Tasks/REQ-SB-28-US-01-T01`..
  `T05`.

- [2026-08-14] `REQ-SB-40-US-01` (Agent Knowledge-Gap Tracking & Expert
  Readiness, `SPRINT-035`) shipped end-to-end and verified live, per
  `ADR-032`: every honest "I don't know" reply is now recorded as a real,
  closeable knowledge gap, via a second bound-tool interception on the
  same shared `graph.py` conversation graph (`record_knowledge_gap`,
  mirroring `ADR-017`'s `request_cross_section_help` exactly) — the new
  `_record_knowledge_gap` node reads the turn's real `HumanMessage`, never
  the model's own paraphrased `topic` argument, confirmed live. New `app/
  business/knowledge_gap_tracking.py` + tenth `.second-brain/
  agent_knowledge_gaps.json` compose, never modify, the already-`Done`
  Vault Filing Expert (human-answer closing path) and the delegated
  knowledge-bootstrap chain (research closing path) — both confirmed
  byte-for-byte unmodified after this sprint. `AgentDetailPanel.tsx`
  gains a fourth "Knowledge gaps" tab, gated to `agent.type === 'expert'`
  and genuinely omitted (not hidden) for Worker/Producer agents. **The
  sprint's own explicit highest-risk check — that this graph change left
  ordinary chat completely unaffected — was confirmed live on 2 separate
  existing agents** (`vault-qa`, `compass-expert`) via the real `POST
  /agents/{id}/chat` endpoint, both producing real, correct, non-error
  replies. **Real end-to-end AC-04 verification** (a genuine `"written"`
  research outcome closing a gap) needed 3 temporary, real, fully-reverted
  state changes through the app's own already-`Done` APIs (a `web-research`
  skill grant, a Provider swap to `anthropic-claude`, a Section
  reassignment) because the real vault's current agent configuration has
  no single agent that is simultaneously a real Hub-routing candidate for
  both the research and filing hops — confirmed reverted via independent
  `GET` calls afterward. Full reasoning: `Implementation/Architecture/
  ADR.md` → `ADR-032`; each task's own Implementation Log under
  `Implementation/Tasks/REQ-SB-40-US-01-T01`..`T08`.
- [2026-08-14] `REQ-SB-37-US-02` + `REQ-SB-37-US-03` (Agent Creation
  Wizard — Worker-type and Producer-type flows, `SPRINT-034`) shipped
  end-to-end and verified live, completing the 3-way `REQ-SB-37` split
  (`ADR-030` Expert, no-new-ADR Worker, `ADR-031` Producer). `POST
  /agents` (`app/api/agents_router.py`) now dispatches on all three types
  from one function: Worker calls `create_agent(name, "worker",
  settings=[])` (no Domain-equivalent setting — its real configuration is
  Skills/Vault-Scope/Section, all separate follow-up calls); Producer
  requires a non-blank `purpose`, stored via the same generic `settings`
  kv-list Expert's Domain already uses (`settings=[{"key": "Purpose",
  "value": purpose}]`, `ADR-031` point 3). A new placeholder output
  Skill, `write-to-vault-draft` (`mutates: True`, honest-unavailable
  stub, mirrors `diagram_understanding` exactly), was seeded into
  `skill_tools.SKILLS`/`skill_registry._SKILL_HANDLERS` (`ADR-031` point
  2) — confirmed live that it is gated by the already-real two-axis
  working-mode gate with zero new gating code. Frontend:
  `CreateAgentWizard.tsx` gained a Worker step (Skills multi-select +
  Vault Scope free-text field + Section, submitting via `POST /agents` →
  one Skill grant per selected Skill → one COMBINED `PATCH` carrying
  `section_id` + `scope` together) and a Producer step (Purpose field + a
  genuinely single-select radio-input output-Skill control, never
  checkboxes + Section, submitting via `POST /agents` → exactly one Skill
  grant → a `PATCH` carrying `section_id` ALONE — the one deliberate
  structural difference from Worker's combined call, `ADR-031` point 4).
  Both steps validate every required field client-side before any call
  fires, mirroring `REQ-SB-37-US-01-T04`'s own established pattern
  exactly. `agentsApiClient.ts`'s `CreateAgentBody` gained optional
  `domain`/`purpose` fields. Verified live end-to-end against all 12
  locked ACs (6 per story): a real Worker (`ops-helper`, two granted
  Skills — one read-only, one migrated mutating — a Vault Scope, and a
  Section) and a real Producer (`vault-scribe`, a Purpose, the granted
  `write-to-vault-draft` output Skill, and a Section) were each created
  through the actual wizard UI (CDP-driven headless Edge, native-setter
  React-controlled-input technique + a `window.fetch` spy confirming
  exact call count/order/body for every multi-call sequence) and
  independently reconfirmed via direct `GET` calls to match the UI's own
  claimed outcome exactly — including both agents rendering correctly on
  their own Type ring in their self-healed Section on the real Agents
  Map, and both behaving identically to an existing, already-shipped
  agent in Chat/History and in Supervised-mode Skill gating (cross-
  checked directly against `email-capture`/`meeting-capture`). Neither
  creation path allows a partial agent on validation failure — confirmed
  live via a `window.fetch` spy showing zero calls fired on every
  missing-field rejection path, including Producer's own dedicated
  "only the output Skill is missing" rejection (`AC-05`). Full reasoning:
  `Implementation/Architecture/ADR.md` → `ADR-031`; each task's own
  Implementation Log under `Implementation/Tasks/REQ-SB-37-US-02-T01`/
  `T02`, `REQ-SB-37-US-03-T01`..`T03`.

- [2026-08-14] `REQ-SB-37-US-01` (Agent Creation Wizard — entry point,
  type selector, Expert-type flow, `SPRINT-033`) shipped end-to-end and
  verified live, per `ADR-030` — this is the first-ever runtime agent
  creation in the codebase (previously only 7 static, deployment-time
  agents existed). `app/business/agent_registry.py`'s module-level
  `AGENTS` dict is renamed `_SEED_AGENTS` (byte-identical, unchanged — the
  7 shipped agents stay in-code, never migrated); a new
  `.second-brain/agents_registry.json` (`{"created_agents": {}}`), owned
  by new `vault_writer.py` primitives `load_agents_registry_state`/
  `save_agents_registry_state` mirroring `skill_registry.py`'s
  `_load_state`/`_save_state` shape exactly, holds runtime-created agents.
  `get_agent`/`list_agents` become seed-then-persisted merges (seed always
  first); new `create_agent(name, type, settings=None)` derives `agent_id`
  via `vault_writer.tag_slug(name)`, disambiguating on collision with a
  numeric suffix against the union of seed + created ids — deliberately
  NOT `create_section`'s idempotent-collapse semantic (two distinct
  creation calls must never silently collide into one identity, and a
  created agent must never shadow a shipped agent's id). New
  `POST /agents` (`app/api/agents_router.py`) accepts only `type ==
  "expert"` this pass (Worker/Producer honestly refused with `400` —
  `REQ-SB-37-US-02`/`US-03`, hard-blocked on `REQ-SB-39`), and never
  accepts a `section_id` — Section assignment stays the existing, separate
  `PATCH /agents/{id}` call (`agent_registry.py` stays ignorant of
  Sections, `ADR-014`'s "composed alongside, not inside" layering
  unchanged). **Confirmed live, the concrete mechanism `ADR-030` predicted:
  zero code changes were needed in any of the five already-`Done`
  self-healing per-agent registries** (`section_registry.py`/
  `provider_registry.py`/`working_mode_registry.py`/`skill_registry.py`/
  `agent_keywords.py`) for a created agent to get a default Section/
  Provider/working-mode and be Skill-grantable — each already reads
  `agent_registry.list_agents()` fresh, uncached, on every call. Frontend:
  new `CreateAgentWizard.tsx` (type selector, Expert step) + new
  `CreateAgentCard.tsx` (Settings "+ Create agent" affordance, mirroring
  `SectionsCard.tsx`/`ProvidersCard.tsx`'s own `<details>` pattern);
  `SettingsPage.tsx`/`agentsApiClient.ts` extended additively. Verified
  live end-to-end against all 8 locked ACs — AC-01/02/03/07 via a real
  CDP-driven headless-browser session (native-setter React-controlled-
  input technique, a `window.fetch` spy confirming exact call counts/zero
  calls on the honest-rejection path); AC-04/05/06/08 via real HTTP calls
  against every already-`Done` downstream surface (Agents Map, Provider/
  Working-mode/Skill-grant configuration, Chat, History) — plus an
  additional sprint-level end-to-end pass (beyond any single task's own
  scope): a freshly created Expert agent's own real detail panel (Settings/
  Chat/History tabs) confirmed fully functional, its Chat tab honestly
  declining an out-of-domain question (`REQ-SB-33`'s guardrail, zero new
  code) rather than fabricating an answer, and the 7 pre-existing static
  agents independently reconfirmed byte-identical (same ids/types/
  sections/behavior) before and after this build. One scope-internal,
  non-blocking correction logged for human spot-check: the task's own
  informal `/agents-map` verification-step reference does not exist as a
  real route — the Agents Map is actually mounted at `/` (root),
  confirmed directly from `App.tsx`'s route table; no locked AC's own
  wording names a literal URL. Full reasoning: `Implementation/
  Architecture/ADR.md` → `ADR-030`; each task's own Implementation Log
  under `Implementation/Tasks/REQ-SB-37-US-01-T01`..`T04`.

- [2026-08-14] `REQ-SB-29-US-01` (Agent-to-Tag/Folder Vault Scoping —
  assignment on the Agent Settings surface + scope-bounded retrieval,
  `SPRINT-032`) shipped end-to-end and verified live, no new ADR (the
  architect confirmed additive extension of already-`Accepted` precedent
  — `ADR-017`'s per-agent-list storage shape, `ADR-015`/`ADR-025`'s
  MCP-tool-registration/server-side-agent_id-resolution shape). Scope is
  a new sibling `.second-brain/agent_scopes.json`
  (`{agent_id: [tag_or_folder, ...]}`), owned by new `vault_writer.py`
  primitives (`load_agent_scope`/`save_agent_scope`/
  `load_all_agent_scopes`, mirroring `agent_keywords.json`'s exact
  shape) and a new `app/business/scope_registry.py` (`get_agent_scope`/
  `set_agent_scope`), composed alongside — not inside — `agent_registry.py`
  (unmodified). A new, independent `vault_writer.list_notes_matching_scope
  (scope: list[str])` retrieval primitive matches a note whose `tags`
  intersect `scope` or whose immediate `Work/<kind>/` folder name is in
  `scope` — deliberately does NOT compose `vault_indexing.get_index()`/
  `vault_search.py` (`REQ-SB-01`/`REQ-SB-02`), per this story's own
  operator-resolved 2026-08-12 decision to build a narrower, story-scoped
  ad hoc primitive rather than wait on those still-unbuilt requirements
  (`ESC-008`, `Resolved`). `PATCH`/`GET /agents/{agent_id}` gained an
  additive `scope: list[str]` field (whole-list-replace; explicit `[]`
  clears, omitted is a no-op), mirroring `keywords`'s own established
  shape. A new, scope-aware `retrieve_notes_in_agent_scope(agent_id)`
  `@mcp_server.tool()` (`app/business/scope_query_tools.py`, a sibling to
  `vault_write_tools.py`, not `vault_query_tools.py`'s thin passthrough
  shape) resolves and enforces the calling agent's own assigned scope
  server-side — the tool's own parameter list is exactly `agent_id: str`,
  never a freeform `tags`/`folders` argument the model could use to widen
  its own reach — returning real note content, an honest `"no_scope"`
  result for an unassigned agent, or an honest `"empty"` result for a
  non-empty scope with zero matches, both composing with `REQ-SB-33`'s
  already-live grounding/honest-uncertainty instruction. `scope_registry.
  get_agent_scope` is also the real per-agent lookup `ADR-025` point 6's
  fail-closed `vault_write_tools._is_within_assigned_scope` seam
  (`ESC-026`) needs as a future stable contract — exposed here, but
  wiring that seam is still `REQ-SB-04-US-01`'s own separate, still-
  blocked future task, not closed by this story. Frontend:
  `AgentDetailPanel.tsx` gained a "Vault scope" kv-row matching the
  Keywords row's exact free-text/comma-separated/`onBlur`-commit pattern
  (no `/design` pass — operator-decided skip for this story);
  `agentsApiClient.ts`'s `AgentDetail`/`updateAgentAssignment` gained an
  additive `scope: string[]` field. **Honest, disclosed finding, not a
  defect:** the real configured vault has zero notes under
  `Work/Pipeline`/`Agreements`/`Consumption` — those subfolders don't
  exist at all yet, consistent with this file's own 2026-08-10
  "structure only, no ingestion/agent code" entry, still true as of this
  build; the retrieval scenarios' "produces a real positive result" half
  was verified against the closest real substitute the vault actually
  has (the `customer/<slug>` tag dimension of the same schema), while a
  literal `["Pipeline"]` scope was independently confirmed to correctly
  produce the honest empty-result path today. Verified live end-to-end
  against all 6 locked ACs, including a real headless-Edge/CDP-driven
  browser round trip (assignment) and a real chat round-trip through the
  new MCP tool (retrieval) referencing genuine vault content, not
  fabricated. Full reasoning: `Implementation/Architecture/architecture.
  md` → "Agent-to-Tag/Folder Vault Scoping"; each task's own
  Implementation Log under `Implementation/Tasks/REQ-SB-29-US-01-T01`..
  `T05`.

- [2026-08-14] `REQ-SB-39-US-02` (Extend the working-mode approval gate to
  Skills + migrate every existing mutating Action to a Skill, `SPRINT-031`)
  shipped end-to-end and verified live, per `ADR-029`: `app/business/
  skill_registry.py::invoke_skill` gained `ADR-020`'s own two-axis
  working-mode gate one layer over (Manual+`hub_routed` refuses; Supervised
  + a Skill's own `"mutates"` flag creates a real Pending Approval; else
  falls through), with a new `_dispatch_skill` primitive extracted as the
  raw, ungated fallthrough — the ONE function every real call site
  (`skills_router.py`, `agents_router.py`'s dispatch fork,
  `knowledge_bootstrap.py`'s Hub-routed call) already passes through,
  making "never a route around the gate" true by construction, not caller
  discipline. `app/api/pending_approvals_router.py`'s Approve endpoint
  gained a `skill_tools.SKILLS`-aware branch calling `_dispatch_skill`
  directly (never `invoke_skill` — re-entering the gate on Approve would
  defer forever), with a `skip_history` guard for self-recording handlers.
  The 4 formerly-hardcoded mutating Action ids (`run_capture_now`,
  `pause_schedule`, `rebuild_person_note`, `build_knowledge`) migrated into
  `skill_tools.SKILLS`/`skill_registry._SKILL_HANDLERS` (all `"mutates":
  True`), preserving today's exact real/honest-unavailable split with zero
  new real behavior (`run_capture_now` real only for `email-capture`;
  `build_knowledge`'s real handler needed a deferred import to avoid a
  circular import plus a dedicated single-use thread bridge —
  `concurrent.futures.ThreadPoolExecutor(...).submit(asyncio.run,
  coro).result()` — to avoid a "cannot be called from a running event
  loop" crash under FastAPI's own real async caller). Retrofit-seeded the
  5 real, already-shipped agents onto the equivalent Skill access via the
  same `_MIGRATION_GRANT_SEED` mechanism `REQ-SB-39-US-01-T05` established.
  **The operator's own explicitly-named single highest-risk check for this
  sprint — a real migrated mutating Skill under Supervised mode creates a
  real Pending Approval rather than executing immediately — was confirmed
  live in 0.008s, with zero Outlook/Compass calls made**, independent of
  the (much longer) full real-capture round trip, which was also verified
  live end-to-end (Autonomous execution → real result; Supervised → defer;
  Approve → the same real handler genuinely re-running). **Live-discovered,
  disclosed finding, not a defect in this sprint's own code:** a real,
  already-running stray dev-server process (alive since before this
  session, listening on `localhost:8000`) independently fired its own real
  hourly background-capture tick during live testing, creating an
  unrelated, correctly-gated `background`-triggered pending-approval
  record via the pre-existing `email_classification.py`/`ADR-018`
  mechanism — left `pending` for human review rather than silently
  resolved by the coder. See `REVIEW-QUEUE.md` and each task's own
  Implementation Log under `Implementation/Tasks/REQ-SB-39-US-02-T01`..
  `T04`.

- [2026-08-14] `BUG-008` (app-start capture blocking FastAPI's own startup
  completion, hence all HTTP traffic, on the full catch-up run finishing)
  was fixed directly, same urgency precedent as the `REQ-SB-25` chat bug
  below — it was actively blocking live verification for a large batch of
  sprints then in flight (`SPRINT-030`–`038`). `capture_scheduler.py`'s
  `lifespan()` now schedules `run_capture_if_idle()` via
  `asyncio.create_task(...)` instead of `await`-ing it directly. Capture
  still fires unconditionally on every start (`REQ-SB-07`'s own spec,
  unchanged); only the blocking-on-HTTP-traffic side effect is gone. See
  `BUGS.md` → `BUG-008` for the full live-observed evidence (100+
  sequential real Compass calls before startup completed, pre-fix).

- [2026-08-12] Real conversational chat (`REQ-SB-25`) was completely
  broken end-to-end in the real running app until fixed directly (not
  through the formal pipeline — a critical bug found via live operator
  testing, fixed with the same urgency as any other production-breaking
  defect). Root cause: `agents_router.py::chat` was sync, run via
  `run_in_threadpool`; `graph.py`'s `run_agent_conversation`/
  `_execute_tools` each nested their own `asyncio.run()` call to bridge
  into the MCP client's async loopback call — a second event loop, in a
  worker thread, self-connecting back into the same single-process
  server, which reliably failed on this host even though the identical
  MCP call succeeded instantly as a standalone script. Fixed by making
  the whole chain genuinely `async def` end-to-end (`chat` →
  `run_agent_conversation` → `_GRAPH.ainvoke()` → the `_execute_tools`
  node), eliminating the nested event loop entirely. See `CHANGELOG.md`
  for full detail.

- [2026-08-11] `REQ-SB-13-US-01` (Embedded agent detail panel — settings,
  actions, chat, and unified communication history, `SPRINT-010`) shipped
  end-to-end and verified live, per `ADR-011`: `app/data_access/
  vault_writer.py` gained `append_agent_history_entry`/
  `load_agent_history` (new `.second-brain/agent_communication_history.
  json`), `app/business/agent_registry.py` (new — static 5-agent registry:
  `email-capture`/`meeting-capture`/`todo-capture`/`people-producer`/
  `vault-qa`, each with settings/actions/`trigger_phrases`), `app/
  business/agent_chat.py` (new — keyword-substring trigger-phrase
  matching, first match wins, deliberately not NLU/LLM per `ADR-007`),
  one additional call in `email_classification.
  run_capture_and_record_completion` (appends a `run_event` history entry
  alongside its existing `record_capture_run_completed()` call), and new
  `app/api/agents_router.py` (`GET /agents/{id}`, `POST /agents/{id}/
  actions/{action_id}`, `POST /agents/{id}/chat`, `GET /agents/{id}/
  history`). Frontend: `AgentNode.tsx`/`AgentsMapCanvas.tsx` gained
  `onSelect`/`onSelectAgent` click wiring, new `AgentDetailPanel.tsx`
  (settings/actions/chat/history sections), new `agentsApiClient.ts`, new
  `styles/agent-panel.css`. Verified live: both trust-surface-defining
  scenarios (a chat message triggering a real backend action; chat + run
  events unified in one chronological history) confirmed with a single
  real Outlook/Compass/vault-write capture run triggered through the
  actual chat UI. Only `email-capture`'s `run_capture_now` has a real
  handler this pass — every other declared action returns an honest "not
  yet available" response, per `ADR-011` point 3. Full reasoning:
  `Implementation/Architecture/ADR.md` → `ADR-011`.
- [2026-08-11] `REQ-SB-12-US-02` (My Day dashboard + Emails/Calendar/To-Do
  drill-down pages, `SPRINT-009`) shipped end-to-end and verified live:
  `app/data_access/vault_writer.list_notes_in_kind_folder(kind)` (new),
  `app/business/my_day.py` (new — `summary`/`list_email_items`/
  `list_calendar_items`), `app/api/my_day_router.py` (new — `GET
  /my-day/summary|emails|calendar|todo`), and the frontend
  `MyDayPage`/`MyDayEmailsPage`/`MyDayCalendarPage`/`MyDayTodoPage`
  (`features/my-day/client.ts`, `styles/my-day.css`). Added
  `fastapi.middleware.cors.CORSMiddleware` to `app/main.py` — the first
  task in the codebase to make a real browser-to-FastAPI fetch call
  (`REQ-SB-12-US-01`'s `api/client.ts` had gone unused until now); without
  it every such call fails outright. Scoped to the Vite dev server's own
  default origins rather than a wildcard. Flagged for a possible future
  ADR formalizing the allowed-origins policy — see `REVIEW-QUEUE.md`.
- [2026-08-11] `REQ-SB-08` (Meetings Capture Pipeline, `SPRINT-006`) shipped
  end-to-end and verified live: `app/data_access/outlook_com.py::
  list_calendar_events` (new, ADR-008, ported from agentic-map's
  `list_upcoming_events`/`list_calendar_since` COM mechanics), `app/
  business/meeting_classification.py` (new — fetch → exclude vault owner
  → derive customer via majority vote → write/top-up Meeting note → link
  customer hub + attendee Person notes), new Meeting-note primitives in
  `vault_writer.py` (incl. the growable per-attendee `upsert_attendee_links`,
  distinct from the single-target `insert_body_line_if_missing`), scheduler
  wiring (one additional call inside `email_classification.
  run_capture_and_record_completion`, zero changes to
  `capture_scheduler.py`), and `POST /poc/classify-meetings`. Verified live
  against the real Outlook calendar and vault: 38 real Meeting notes
  captured correctly, classified, and linked; vault-owner self-exclusion
  (Scenario 11) confirmed on real self-organized meetings, not a throwaway
  construction. New required `Settings.self_email` config field (`.env`-
  sourced) — its value was determined via a one-time, read-only Outlook
  `Namespace.CurrentUser` COM probe rather than guessed or asked blind (see
  Patterns, below). One genuine architectural finding surfaced and
  escalated, not silently patched — see the EntryID Constraint entry below
  and `ESCALATIONS.md` → `ESC-002`. Full verification detail:
  `Implementation/Tasks/REQ-SB-08-US-01-T05-manual-classify-meetings-endpoint.md`.
- [2026-08-11] `SPRINT-007` `Done` — both stories shipped end-to-end and
  verified live. `REQ-SB-17-US-01` (Research notes template + guide):
  `Templates/Research.md` and a fifth guide-note section, matching the
  resolved schema, no customer/company link (by design). `REQ-SB-16-US-01`
  (Partner hub notes + Microsoft migration): `partner_hub_linking.py`
  (new — `ensure_partner_hub_note`/`link_note_to_partner_hub`/
  `migrate_customer_to_partner`), Partner hub-note primitives + four
  generic rename/remove/swap/replace primitives in `vault_writer.py`,
  `people_extraction.ensure_person_note`'s Partner branch (Customer
  checked first, Partner second, mutually exclusive). The migration's own
  match predicate needed a mid-flight correction (`ADR-012`, extends
  `ADR-009` point 4 — resolved `ESCALATIONS.md` → `ESC-001`): the original
  frontmatter-equality-only scan structurally could never reach Person
  notes, which never carry a `customer` frontmatter field, only a
  `company/<slug>` tag plus a separate inline body wikilink; the corrected
  scan unions frontmatter-equality with inline-body-wikilink-presence,
  both read from the same existing per-note `read_note()` call. Once
  corrected, the real live migration ran successfully: `Work/Customers/
  Microsoft.md` → `Work/Partners/Microsoft.md`, and all 15 real
  Microsoft-related notes found by the generic scan (1 hub note, 2 Email,
  1 Meeting, 1 Newsletter, 4 Notification, 6 Person — one more Person note
  than the story's original count of 5, picked up correctly by the
  generic, not-hardcoded design) correctly retagged, idempotent on rerun.
  A separate, unrelated, real primitive-level bug
  (`vault_writer.insert_body_line_if_missing`'s fixed body-start byte
  offset, which corrupts notes whose body lacks the standard blank line
  after frontmatter) was found live and worked around by directly
  repairing the one affected real note — logged as `ESCALATIONS.md` →
  `ESC-003` (`Open`), not yet fixed at the primitive level, recommended
  for a formal `/bug` capture.
- [2026-08-11] No agent-orchestration framework (LangGraph named
  specifically) in Second Brain's own stack — Hermes already owns agent
  typing/orchestration on its side of the integration boundary, and no
  Accepted requirement asks Second Brain to orchestrate agents itself.
  Full reasoning: `Implementation/Architecture/ADR.md` → `ADR-007`.
- [2026-08-11] Three new/extended vault-taxonomy entities resolved,
  operator-directed: **Notes** (generic customer-related content that
  doesn't fit an existing `kind` — zero code change, just a new `kind/`
  value, no requirement ID needed), **Partners** (`REQ-SB-16`, new) — same
  hub-note/tag/wikilink graph-connectivity mechanism as Customer
  (`REQ-SB-14`) but deliberately *not* the Pipeline/Agreements/Consumption
  sub-entities; `partner/<slug>` is mutually exclusive with
  `customer/<slug>` (operator's explicit choice — a company is one or the
  other, never both); real migration needed, not speculative —
  `Work/Customers/Microsoft.md` plus 5 Person notes and 2 Email notes are
  already mistagged `customer/microsoft` from before this distinction
  existed — and **Researches** (`REQ-SB-17`, new) — manual-entry-only book/
  read notes, minimal frontmatter (`title`, `author`, `tags`), no
  AI-assisted capture pipeline (explicitly deferred). Full schemas:
  `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md`.
- [2026-08-11] `BUG-001` closed (`BUGFIX-01-US-01`, `SPRINT-005`) — Email
  notes now carry an actual `[[PersonName]]` wikilink to their sender's
  Person note (`**Sender:** [[PersonStem]]`, via new
  `people_extraction.link_email_to_person`), both going forward
  (`email_classification.classify_recent_emails`) and backfilled over
  every already-captured Email note (new one-time
  `people_extraction.retrofit_email_sender_links` /
  `POST /poc/retrofit-email-sender-links`, mirroring
  `retrofit_customer_hub_links`'s/`retrofit_people_from_emails`'s shape).
  This closes the specific inbound (Email→Person) gap the
  tags-and-wikilinks standing constraint below was found to have missed;
  the constraint itself remains standing for any future entity
  relationship, this is just confirmation this one instance is resolved,
  not a reason to stop checking new relationships in both directions.
- [2026-08-11] Meeting notes (REQ-SB-08) resolved as one note type, not a
  separate Meeting-Minutes type — `Work/Meetings/<subject>-<date>-<entry-
  id-suffix>.md`, same EntryID-collision-suffix rule as Email notes.
  Attendees get the exact `ensure_person_note` treatment `REQ-SB-10` built
  for email senders (extended from "sender" to "attendee"), and a
  meeting's `customer` is derived from attendee company matches using the
  same `people_extraction.py` logic. This activates the "Meeting-based
  half" of People backfill that REQ-SB-10 left blocked. Full schema:
  `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md`.
- [2026-08-11] People (REQ-SB-10) are flat notes at `Work/People/<Person>.md`
  with Company as a `company/<slug>` tag — never a folder, and a separate
  namespace from `customer/<slug>` (a person's employer isn't always a
  customer account; many real contacts are internal colleagues at the
  operator's own employer, or third parties). Same reasoning as ADR-004's
  customer-as-tag decision.
  Backfilled from already-captured Email notes' sender fields (deduped by
  email address); the Meeting-based half is real but blocked on REQ-SB-08
  not existing yet. Full schema:
  `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md`.
- [2026-08-10] Reversed the earlier "Drop" call on agentic-map's REQ-079/
  080/081 (pipeline_items/customer_entitlements tables + tools) – real
  captured email data confirmed Second Brain's actual customer domain is
  an Azure MACC/consumption business with a small set of real, named
  enterprise customer accounts, exactly what those requirements were
  built for in agentic-map. Reshaped for notes
  instead of DB rows: `Work/Pipeline/`, `Work/Agreements/`, `Work/
  Consumption/` (one note per snapshot, atomic) plus a `Work/Customers/`
  hub note per customer. Full schema:
  `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md`. Structure
  only — no ingestion/agent code for these yet.
- [2026-08-10] Adopted *Beyond the Second Brain* (Mo Elkholy) as a standing
  architecture reference – the operator supplied the book (`Documentation/
  References/beyond-the-second-brain-methodology.md` is the condensed
  summary); read it before making vault-structure or AI-integration
  decisions. It surfaced real tensions with what the email-classification
  POC had already shipped (folder-heavy structure, no AI-output review
  gate, non-atomic notes) — flagged in that file, not silently reconciled;
  awaiting an operator decision on how much of the method to adopt.
- [2026-08-10] No staging/promotion gate on ingested vault data – Second Brain
  indexes the user's own trusted Obsidian vault, not agent-written scratch data;
  the two-tier staging→canonical model `agentic-map` uses (its invariant 4) does
  not apply here and is intentionally not replicated.
- [2026-08-10] Standalone project, no agentic-map integration built yet – future
  integration (agentic-map's agents querying this KB) is a deliberately separate,
  later decision, not part of this project's initial scope.
- [2026-08-10] Second Brain's PRD requirements (REQ-SB-01..06) were seeded by
  walking agentic-map's 76-entry REQUIREMENTS.md and classifying each as
  Port/Adapt/Drop/Already-covered – the overwhelming majority dropped (sales
  pipeline, Outlook/mail, the agent-routing console, multi-agent orchestration
  are all out of scope). Full classification and reasoning:
  `Implementation/Plans/2026-08-10-agentic-map-requirement-port.md`.
- [2026-08-10] Agents may write to the vault (REQ-SB-04) and content may enter
  the vault via a non-Obsidian ingestion path (REQ-SB-05) – both were open
  product questions, resolved permissively by the operator rather than
  defaulting to read-only/Obsidian-only. Scope/confirmation rules for writes
  are deferred to `/spec` time, not decided here.
- [2026-08-10] Email-classification POC validated end-to-end (Outlook COM →
  Compass classify-by-customer → vault note write) against a real inbox –
  confirms the Hermes-skill-wrapping approach from the earlier Outlook
  integration-sourcing constraint is workable. Code lives at
  `src/backend/app/{data_access/outlook_com.py,data_access/compass_client.py,
  data_access/vault_writer.py,business/email_classification.py}`, exposed at
  `POST /poc/classify-emails`.
- [2026-08-10] Resolved the *Beyond the Second Brain* tension above,
  partially – (a) no AI Staging/review gate for now (classification
  accuracy spot-checked as good this session; revisit if real
  misclassifications show up), (b) folder-vs-links restructuring started
  immediately: `Work/Customers/<Customer>/<Kind>/` flattened to
  `Work/<Kind>/`, customer demoted from folder level to frontmatter + tag
  only. Not fully reconciled — atomic notes and output-orientation are
  still open.
- [2026-08-11] `REQ-SB-18-US-01` (User-editable agent Sections, decoupled
  from agent Type, with per-agent section reassignment, `SPRINT-011`)
  shipped end-to-end and verified live, per `ADR-014`: Section is now a
  new, persisted, user-mutable concern living in a sixth `.second-brain/`
  state file (`agent_sections.json`), owned by a new `app/business/
  section_registry.py` composed *alongside* — not inside —
  `app/business/agent_registry.py` (`agent_registry.py` itself was not
  modified; `ADR-011` point 2's "agent identity/type/actions stay
  hardcoded" reasoning is untouched). The starting 5 sections (Technical,
  Sales, Productivity, Customers, Products) seed on first read, and every
  known agent self-heals to the first section if absent from
  `assignments` — this is what makes `GET /agents`/`GET /sections` always
  return a real value with zero manual migration step. A section's `id`
  is a slug fixed at creation and never regenerated on rename, which is
  what makes "rename doesn't change assignment" true by construction, no
  extra propagation code needed. Section deletion is blocked (not
  cascaded) while any agent is still assigned — `section_registry.
  delete_section` returns a `{"deleted": bool, "blocked_by_agent_ids":
  [...]}` result dict (never raises for this ordinary case), and
  `app/api/sections_router.py` translates a blocked result into `HTTP
  409` with a name-resolved message. New `PATCH /agents/{agent_id}` verb
  on the existing `agents_router.py` handles per-agent reassignment.
  Frontend: `layoutAgents.ts` became genuinely N-section-generic (hub
  angles evenly spaced around the full circle from the real `GET
  /sections` list, replacing the old fixed 3-entry `SECTION_META`/
  `TYPE_TO_SECTION` lookup); a Section's Hub, spoke-lines, and
  cluster-lines all render one neutral color now that a Section can hold
  agents of any Type (Type still drives ring placement, untouched).
  Verified live end-to-end, including both trust-defining scenarios:
  `AC-05` (blocked deletion — the exact `409` message renders in Settings'
  Sections card) and `AC-09` (the Agents Map reflects a just-reassigned
  agent's new grouping with no code change/restart). Full reasoning:
  `Implementation/Architecture/ADR.md` → `ADR-014`.
- [2026-08-11] `REQ-SB-19-US-01` (Global LLM Provider CRUD in Settings,
  with a per-agent Provider picker defaulting to Compass, `SPRINT-012`)
  shipped end-to-end and verified live, per `ADR-014`, as a diff on top of
  `REQ-SB-18-US-01`/`SPRINT-011`'s already-landed shared surface. Provider
  is now a seventh `.second-brain/` state file (`agent_providers.json`),
  owned by a new `app/business/provider_registry.py` composed *alongside*
  — not inside — `agent_registry.py` (unmodified, `ADR-011` point 2
  untouched), mirroring `section_registry.py`'s exact shape. A "Compass"
  entry seeds on first read from `app.config.settings.compass_base_url/
  compass_api_key/compass_model`, and every known agent self-heals to
  `"compass"` if absent from `assignments`. **Credential handling:**
  plaintext at rest (same trust boundary as `.env`'s existing
  `compass_api_key`), never returned by any endpoint — `list_providers()`
  never puts a `credential` key in its returned dicts at all, so
  `providers_router.py` has nothing to strip. **The pre-seeded "Compass"
  entry is CRUD-editable but inert** — editing it from Settings never
  changes the real, live Compass call path (`app/data_access/
  compass_client.py` keeps reading `.env`/`Settings.compass_*` directly,
  unconditionally); confirmed live by editing the Compass Provider entry's
  endpoint, then triggering one real `run_capture_now`, which completed
  normally using the real `.env` endpoint, not the edited representation.
  **Provider-unavailability enforcement** lives in `agents_router.py::
  _invoke_action`, reusing `ADR-011` point 3's "declared but not yet
  backed by a real handler" pattern one layer up — before ever calling a
  real handler, it checks `provider_registry.has_real_client()` for the
  agent's selected Provider and returns an honest "not available yet"
  result if false, with the handler never invoked (no silent fallback to
  Compass, no fabricated response); confirmed live by pointing
  `email-capture` at a real-client-less test Provider and confirming, via
  its own `/history` log, that no real Outlook/Compass call occurred for
  that trigger. Frontend: new `ProvidersCard.tsx` (Settings) and a new
  Provider `<select>` kv-row on `AgentDetailPanel.tsx`, alongside
  `REQ-SB-18-US-01`'s Section equivalents, both built from the same
  "always-visible inline edit inputs" convention `SectionsCard.tsx`
  established. Full reasoning: `Implementation/Architecture/ADR.md` →
  `ADR-014`.
- [2026-08-11] `REQ-SB-22-US-01` (My Day drill-downs and dashboard counts
  scoped to a rolling 7-day window, `SPRINT-013`) shipped end-to-end and
  verified live: `app/business/my_day.py` gained the first date-range
  filtering ever added to My Day's read path — `_compute_window()`/
  `_within_window()` (3-days-before/3-days-after `datetime.now()`,
  recomputed fresh on every call; `[:10]` ISO-date-string-prefix compare,
  same precedent as `email_classification.py`/`vault_writer.
  meeting_note_filename_stem`), applied to both `list_email_items()`
  (which also gains a `received` field it previously omitted) and
  `list_calendar_items()`. `app/api/my_day_router.py` unchanged — additive
  field + narrower result set only, no contract change. Frontend:
  `MyDayEmailItem` gains `received: string`
  (`features/my-day/client.ts`), rendered in `MyDayEmailsPage.tsx`'s
  existing `.item-row-meta` line; `MyDayCalendarPage.tsx`/`MyDayPage.tsx`
  needed zero code change, verified live as already-correct consumers of
  the narrower backend response. Verified live against the real vault
  (179 Email notes, 39 Meeting notes; windowed to 21/17): a real
  out-of-window note of each kind confirmed genuinely absent from the
  returned lists, and a monkeypatched `datetime` simulating 10 days later
  (then reverted, exact restoration confirmed) proved the window
  recomputes on every call with zero caching. Full reasoning:
  `Implementation/UserStories/REQ-SB-22-US-01-my-day-rolling-7-day-window.md`.
- [2026-08-12] `REQ-SB-25-US-01-T01` (`SPRINT-014`) confirmed `ADR-015`'s
  own honestly-flagged Windows `cp314` wheel-availability risk is clear —
  a real `pip install` of `langgraph>=1,<2`/`langchain-openai`/`mcp`/
  `langchain-mcp-adapters` against `src/backend`'s real `.venv` completed
  with no missing-wheel/build-toolchain failure (resolved versions
  `langgraph==1.2.11`, `langchain-openai==1.4.3`, `mcp==1.29.0`,
  `langchain-mcp-adapters==0.3.2`). Worth knowing for `SPRINT-015`
  (`REQ-SB-26-US-01`/`REQ-SB-27-US-01`), which both build directly on this
  same install without needing to re-verify it.
- [2026-08-12] `BUG-002` closed (`BUGFIX-02-US-01`, `SPRINT-016`) — the
  already-approved, already-live-browser-verified Option D (semantic zoom
  / drill-down) design was ported into the real app end-to-end and
  verified live. `layoutAgents.ts` gained a new sibling
  `layoutSectionDrilldown()` (full-360° spread for one Section's own
  drill-down), deliberately kept separate from the existing `layoutAgents()`/
  `SECTION_ARC_SPAN_DEG` overview fan-out — conflating the two models was
  `BUG-002`'s own root-cause shape, so both are untouched. `AgentNode.tsx`/
  `SectionHub.tsx` each gained two optional, backward-compatible props
  (`compact`/`radiusOverride` and `onActivate`/`radiusOverride`
  respectively) rather than becoming two components — one component, two
  call sites (overview vs. the new `SectionDrilldown.tsx`). Verified live
  against real seed data (real `.second-brain/agent_sections.json`:
  "Productivity" now holds 4 agents, "Customers" 1 — this has drifted from
  `BUG-002`'s original "all 5 in Technical" filing over the course of this
  session's other concurrent work; still today's real 4+-in-one-Section
  repro condition, verified against Productivity instead, no reassignment
  needed): zero real DOM bounding-box overlap between any agent/Hub/
  section-title across Sections; Hub-click correctly zooms into a
  fully-labeled, correctly-smaller-Hub drill-down; Back restores the
  overview unchanged. One scope-internal finding, not a defect: the
  overview's ring radii remain global (not per-Section, pre-existing,
  explicitly out of this story's scope) — a purely-distance-based
  containment heuristic can diverge from actual visual overlap at this
  geometry, so any future containment verification should check real DOM
  rect intersection directly, not a center-distance proxy (see Patterns,
  below). Full reasoning: `Implementation/Tasks/BUGFIX-02-US-01-T06-
  agents-map-canvas-drilldown-wiring.md`'s Implementation Log.
- [2026-08-12] Meetings occurrence dedup/filename key changed a **second**
  time in two days (`ADR-019`, supersedes `ADR-013` points 1/2) – live
  verification of `ADR-013`'s own fix (`REQ-SB-08-US-01-T06`, `SPRINT-017`)
  found `AppointmentItem.GlobalAppointmentID` has the exact same
  non-uniqueness defect on this Outlook installation that `EntryID` had
  (`ESCALATIONS.md` → `ESC-012`) — two of two Outlook-native identity
  fields tried have now independently failed the same live test. `ADR-019`
  stops depending on any Outlook-provided identity field for occurrence
  disambiguation and uses a SHA-256 hash of `subject` + the occurrence's
  own full, precise start timestamp instead — a structural uniqueness
  guarantee (two distinct occurrences cannot share an identical start
  moment) rather than an empirical claim about a specific COM property's
  behaviour, so it needs no further live re-verification against this
  installation the way both prior attempts did. `ADR-013`'s legacy-
  `EntryID`-path coexistence check (so none of the 39 pre-existing real
  Meeting notes needs migrating) is reused unmodified; its own middle
  `GlobalAppointmentID`-hash fallback tier is dropped (confirmed live that
  zero real notes were ever created under it). See the Constraints entry
  below for the reusable lesson.
- [2026-08-12] `REQ-SB-26-US-01` (Agent Memory, `SPRINT-015`) shipped
  end-to-end and verified live, per `ADR-016`: memory is an **LLM-based
  extracted/summarized fact store**, not raw cross-conversation replay.
  Two new nodes on the same compiled `langgraph.graph.StateGraph`
  `app/business/agent_orchestration/graph.py` builds for `REQ-SB-25` —
  `retrieve_memory` (read path, folds stored facts into the message list
  as a second `SystemMessage` before `call_model`) and `extract_memory`
  (write path, reuses the already-resolved model for one additional,
  narrowly-scoped completion after the model produces a final reply,
  honestly returning no facts rather than inventing one). New sibling
  `.second-brain/agent_memory.json` (`{agent_id: [{"fact": str,
  "recorded_at": iso8601}, ...]}`), owned by new `vault_writer.py`
  primitives `load_agent_memory`/`append_agent_memory_entries` mirroring
  `load_agent_history`/`append_agent_history_entry`'s exact shape.
  `agents_router.py::chat`'s no-trigger-phrase-match branch loads memory
  once per call and persists any extracted facts afterward — memory is
  strictly per-agent (a separate `agent_memory.json` key per `agent_id`,
  never shared across a Section), confirmed live: a fact stated to one
  agent is correctly recalled in a later, separate conversation with that
  same agent (isolated from `REQ-SB-25`'s own history-replay mechanism);
  a different agent shows zero awareness of it; an agent asked to recall
  something never actually shared honestly says so rather than
  fabricating an answer; the fact survives a full backend restart. Full
  reasoning: `Implementation/Architecture/ADR.md` → `ADR-016`.
- [2026-08-12] `REQ-SB-08-US-01-T06` (`SPRINT-017`) rebuilt exactly per
  `ADR-019` and **live-verified this time** — this is the **second**
  dedup-key fix for the same finding class (`EntryID` → `ADR-013`'s
  `GlobalAppointmentID` → `ADR-019`'s structural precise-start-timestamp
  hash), and the first one to actually hold up under live testing, since
  it no longer depends on any Outlook-provided field's uniqueness at all.
  The real recurring series that originally triggered `ESC-002`/`ESC-012`
  ("Weekly Forecast l Strategic/Major Clients") now produces 6 distinct
  filename suffixes for its 6 real occurrences, confirmed live; zero of
  the 39 originally-named pre-existing Meeting notes were touched
  (`LastWriteTime` unchanged, confirmed via real `DateTime` comparison,
  not a naive CSV-round-tripped string compare which produced false
  positives on first attempt). `ESCALATIONS.md` → `ESC-002` and `ESC-012`
  both flipped to `Resolved`. One honestly-flagged, non-blocking live
  discovery from this same verification pass: the vault held a **40th**
  Meeting note at session start, not the 39 this task's own spec and
  `ADR-019`'s own Consequences section both assumed — created by the
  then-still-live, not-yet-rebuilt `ADR-013` code during a real scheduled
  capture run that happened *between* sessions, for a genuinely new
  (non-recurring) meeting whose `GlobalAppointmentID` happened to resolve
  successfully (the live-confirmed defect is non-uniqueness *within* a
  recurring series, not resolution failure for a one-off item) —
  falsifying `ADR-019`'s own "zero real notes were ever created under
  [the `GlobalAppointmentID`-hash] scheme" premise by one note. That same
  meeting was also independently rescheduled mid-session (a real,
  unrelated calendar edit), and running this task's own mandated live
  Tests step 3 (which processes every in-window event, not a hand-picked
  subset) predictably created one additional new note for it under the
  new scheme — a real, bounded, one-meeting duplicate outside the 39
  named notes, recoverable by a human deleting/merging the stale one by
  hand. Full evidence and reasoning: `Implementation/Tasks/
  REQ-SB-08-US-01-T06-global-appointment-id-dedup-key-fix.md`'s own
  Implementation Log.
- [2026-08-12] `REQ-SB-27-US-01` (Skills Repository — registration and
  per-agent access, plumbing only, `SPRINT-015`) shipped end-to-end and
  verified live, per `ADR-015`: a skill's actual capability is a
  code-registered `@mcp.tool()`-decorated Python function (new
  `app/business/skill_tools.py`, a sibling to `vault_query_tools.py`,
  registered on the same shared `FastMCP` instance `app/api/mcp_server.py`
  exposes) — never a runtime, user-created entry — while an agent's
  *access* to a registered skill is a new, persisted, user-mutable
  concern (new `app/business/skill_registry.py`, mirroring
  `section_registry.py`/`provider_registry.py`'s `ADR-014` shape exactly:
  `list_skills`/`list_agent_skills`/`grant_skill_access`/
  `revoke_skill_access`/`has_skill_access`/`invoke_skill`, backed by a new
  `.second-brain/agent_skills.json`) composed *alongside* the catalog, not
  inside it. **Deliberately no self-healing default assignment** — an
  agent only gets skill access via an explicit grant, unlike
  `section_registry.py`/`provider_registry.py`'s own self-healing
  precedent. This story registers exactly one illustrative stub skill
  (`diagram-understanding`) whose body unconditionally returns an honest
  "not yet available" response — invoking a skill an agent has access to,
  but which has no real handler yet, is deliberately distinct (`200`,
  honest-unavailable body) from invoking a skill the agent has no access
  to at all (`403` refusal) — new `app/api/skills_router.py` (`GET
  /skills`, `GET`/`POST`/`DELETE /agents/{id}/skills[/{skill_id}]`, `POST
  .../invoke`). This story is plumbing only — the first real skill's
  implementation and any UI are explicit follow-on work. Full reasoning:
  `Implementation/Architecture/ADR.md` → `ADR-015`.
- [2026-08-12] `REQ-SB-33-US-01` (Agent grounding & honest-uncertainty
  guardrail, `SPRINT-018`) shipped end-to-end and verified live: a
  grounding/honest-uncertainty instruction was appended to
  `history_entries_to_messages`'s existing single prepended
  `SystemMessage` (`app/business/agent_orchestration/state.py`) — still
  exactly one `SystemMessage`, no new node/tool/ADR, per the story's own
  scoped Constraints. Verified live against all 4 locked ACs, including
  two real induced-tool-failure passes via a throwaway in-process
  monkeypatch (no file edited, no revert needed) — see the Patterns entry
  below and the task's own Implementation Log for full transcripts. One
  surprising, not-fully-diagnosed live finding during this verification
  (recorded honestly, not silently worked around): the shared dev
  backend became fully unresponsive to a plain, unrelated `GET /agents`
  for several minutes while one real Compass chat call was in flight —
  well past this project's own documented "Compass calls take a while"
  latency precedent (`REQ-SB-26-US-01-T04`). Plausible cause,
  **unconfirmed**: `graph.py::_call_model` is a synchronous `def` node
  (unmodified by this task, out of its file scope) making a blocking
  `model.invoke(...)` call inside `_GRAPH.ainvoke()`'s otherwise-async
  graph — if confirmed, this would be in tension with this file's own
  standing async-graph-node Constraint below. Recovered via that same
  Constraint's specific-PID-kill-and-restart protocol; not filed as a
  `/bug` yet (root cause not confirmed, only a strong live correlation) —
  see `SPRINT-018`'s own Retrospective "Open follow-ups."
- [2026-08-12] `REQ-SB-31-US-01` (System Health View — read-only status
  aggregation + chat-path crash-gap fix, `SPRINT-019`) shipped end-to-end
  and verified live, no new ADR: `app/business/agent_orchestration/
  graph.py::run_agent_conversation`'s own outer body (`mcp_client.
  load_vault_query_tools()`, `_GRAPH.ainvoke(initial_state)`) is now
  wrapped in the same honest-failure-funnel `try/except` pattern
  `_call_model` already used, closing the last unwrapped crash gap in the
  chat path (Scenario 8). New `app/business/system_health.py` (read-only
  aggregation, no new persisted state — `get_system_health()`,
  `mcp_mount_reachable()`, `list_disabled_agents()`, composing
  `provider_registry`/`agent_registry`/`vault_writer` as-is, mirroring
  `my_day.py`'s own "no ADR" read-only shape) and `app/api/
  system_health_router.py` (`GET /system-health`), registered in
  `main.py`. New frontend `SystemHealthPage.tsx` + `features/
  system-health/client.ts`, wired into `App.tsx`/`Sidebar.tsx` — zero new
  CSS, composed entirely from already-ported `.card`/`.badge*`/
  `.kv-list`/`.item-list`/`.empty-state` classes. Verified live against
  all 8 locked ACs: the real "everything healthy" state; a real induced
  "issues present" state (MCP mount pointed at an unreachable port + a
  throwaway no-real-client Provider assigned to one agent, both reverted
  after); the real vault's `last_capture_run.json` temporarily moved
  aside and restored to prove the honest "no run has completed yet"
  empty state; every state change reflected fresh on the very next call,
  no caching. `run_agent_conversation`'s crash-gap fix verified via a
  real in-process-monkeypatch-induced exception (see Patterns below).
  One real, live-discovered bug found and fixed in-scope — see the
  Constraints entry below (`httpx.get()`'s redirect-following default).
  Full reasoning: each task's own Implementation Log under
  `Implementation/Tasks/REQ-SB-31-US-01-T01`..`T04`.
- [2026-08-12] `REQ-SB-20-US-01` (Section Hub Intelligence & Cross-Section
  Routing — per-agent keywords, Hub-to-Hub routing node, `SPRINT-020`)
  shipped end-to-end and verified live, per `ADR-017`: keywords are a new
  sibling `.second-brain/agent_keywords.json` (`{agent_id: [keyword, ...]}`),
  owned by new `vault_writer.py` primitives (`load_agent_keywords`/
  `save_agent_keywords`/`load_all_agent_keywords`) and a new business
  module `app/business/agent_keywords.py` (`get_agent_keywords`/
  `set_agent_keywords`/`list_candidate_agents_for_keyword_match` — cross-
  Section, deterministic, case-insensitive keyword-substring matching,
  reusing `ADR-011`'s exact posture one layer up). `PATCH`/`GET
  /agents/{id}` gained a `keywords` field, additive, explicit-empty-list
  clears / omitted is a no-op. `agent_orchestration/graph.py` gained one
  new node, `route_hub_request`, and a new local (never-MCP-registered)
  tool, `request_cross_section_help` — this codebase's first real
  tool-execution loop that is intercepted before the graph's own generic
  `_execute_tools` node (the routing tool's own body intentionally raises
  `NotImplementedError`; the conditional edge must route to
  `route_hub_request` before the generic per-tool-call execution path, or
  that error would be genuinely triggered). The mandatory "own Hub, then
  target Hub" two-hop relay is two sequential lookups inside that one node,
  both hops recorded as explicit fields (`from_section_id`/
  `matched_section_id`) on the result — a directly-callable
  `route_cross_section_request(requesting_agent_id, need_description)`
  function was built specifically so the routing decision itself could be
  verified live without needing `REQ-SB-25-US-01-T08`'s own live
  chat-wiring reachable. Frontend: `AgentDetailPanel.tsx` gained a
  Keywords kv-row (commit-on-blur, free-text comma-separated, whitespace/
  empty entries dropped). Verified live end-to-end against all 4 locked
  ACs: a cross-Section match with both hops explicit; an honest,
  byte-identical-across-repeats no-match; an empty-keyword agent
  structurally never selected across 5 varied need-descriptions (even one
  textually overlapping its own name); the Keywords field's full
  round-trip (empty state → commit → persisted across panel close/reopen
  → independent backend `GET`). `graph.py`/`state.py`/`agents_router.py`
  had each grown materially beyond this story's own task samples by build
  time (sibling stories' intervening changes) — composed around the real
  current files throughout, not the stale samples, per the established
  Learnings pattern below. Full reasoning: `Implementation/Architecture/
  ADR.md` → `ADR-017`; each task's own Implementation Log under
  `Implementation/Tasks/REQ-SB-20-US-01-T01`..`T06`.
- [2026-08-12] `REQ-SB-21-US-01` (Agent Working Modes —
  Autonomous/Supervised/Manual gating + Pending Approvals surface,
  `SPRINT-021`) shipped end-to-end and verified live, per `ADR-018`/
  `ADR-020` (`ADR-020` supersedes `ADR-018` points 3/5 only). Working
  mode is a new, persisted, per-agent property (eighth `.second-brain/`
  state file, `agent_working_modes.json`, self-healing default
  `"autonomous"`), owned by new `app/business/working_mode_registry.py`.
  A Pending Approvals workflow (ninth state file,
  `agent_pending_approvals.json`, this project's first use of `uuid`) is
  owned by a genuinely separate new module, `app/business/
  pending_approval_registry.py` — idempotent per `agent_id`+
  `trigger="background"` only, never for `"chat"`/`"direct"`.
  **The corrected, two-axis gate (`ADR-020`):** `agent_registry.py`
  gained a static `"mutates": bool` field on every action definition
  (classified from real current behaviour, not guessed —
  `pause_schedule` is `True`/mutating despite having no real handler
  yet) plus a `get_action(agent_id, action_id)` lookup helper, fail-safe
  to `mutates: True` for an unresolvable action.
  `agents_router.py::_invoke_action` (split from the unconditional
  dispatch, renamed `_execute_action`) now checks BOTH axes: **Supervised**
  gates on the resolved action's own `mutates` flag, regardless of
  trigger (`"chat"`/`"direct"`/`"hub_routed"`) — a read-only action
  (`view_last_run`/`ask_question`/`view_channel_status`) proceeds
  immediately even while Supervised; only a mutating one proposes and
  waits. **Manual** gates on trigger source only — a direct human ask
  (`"chat"`/`"direct"`) always executes immediately regardless of the
  action's nature, but `"hub_routed"` (a new trigger value, currently a
  no-op since no real call site produces it yet — `ADR-017`'s routing
  node never itself invokes a target agent's action) is refused
  outright. The background-pipeline gate (`email_classification.py::
  run_capture_and_record_completion`, two explicit per-agent checks, new
  shared `run_capture_for_agent` helper) needed no structural change —
  both real background steps are unconditionally mutating today, so the
  corrected rule produces an identical outcome to the pre-correction
  design there. New `app/api/pending_approvals_router.py`
  (`GET`/`POST /pending-approvals...`) — Approve calls `_execute_action`/
  `run_capture_for_agent` directly, bypassing the gate entirely (the
  approval itself is the authorization; re-entering the gate would
  create an infinite-defer bug). Frontend: `AgentDetailPanel.tsx` gained
  a Working-mode `<select>` kv-row and a `.chat-proposal` card
  (live-resolved Pending/Approved/Declined status via `GET
  /pending-approvals/{id}`, not inferred from the entry's own static
  text) rendered inline in Communication History; new standalone
  `/my-day/approvals` page + a 5th My Day card, fetching `GET
  /pending-approvals` directly (`my_day.py`/`my_day_router.py`
  untouched). Verified live end-to-end against all 8 locked ACs,
  including several real Outlook/Compass capture runs and a real
  39-meeting `classify_recent_meetings()` sweep triggered via a live
  Approve click in the browser. `agents_router.py`/`main.py`/
  `MyDayPage.tsx` had each drifted beyond their own task samples by
  build time (sibling stories' intervening work — `SPRINT-020`'s
  keywords support, `system_health_router`/`mcp_server`,
  `REQ-SB-22-US-01`'s rolling-7-day-window navigator) — composed around
  the real current files throughout, never the stale samples. One real,
  live-discovered defect found and fixed in scope: an unresolvable
  `pending_approval_id` on a `"proposal"`-kind history entry (leftover
  smoke-check debris) produced an unhandled promise rejection once the
  new card-resolving effect started fetching every such entry's live
  status — fixed with a `.catch(() => {})` and the one stale entry
  pruned from the real vault state. Full reasoning:
  `Implementation/Architecture/ADR.md` → `ADR-018`/`ADR-020`; each
  task's own Implementation Log under
  `Implementation/Tasks/REQ-SB-21-US-01-T01`..`T09`.
- [2026-08-12] `REQ-SB-35-US-01` (Vault Filing Expert — methodology-
  grounded placement/tag decision and write, two-tier approval,
  `SPRINT-023`) shipped end-to-end and verified live, per `ADR-021`. A
  new registry agent, `"vault-filing-expert"` (`agent_registry.py`, data
  only), reachable exclusively via `REQ-SB-20`'s Hub-to-Hub cross-Section
  routing, never a shared skill. New `app/business/
  vault_filing_methodology.py` (`build_placement_prompt`) grounds one
  `model_factory.resolve_agent_model("vault-filing-expert")` completion
  in a condensed excerpt of the vault's own design methodology plus
  `ADR-004`'s tag/folder split, alongside three deterministically
  pre-fetched `list_known_kinds`/`list_known_customers`/
  `list_known_partners` lists (never left to the model to tool-call —
  this project's own "prefer a real deterministic call over hoping the
  model tool-calls correctly" precedent). New `app/business/
  vault_filing_expert.py` (`determine_placement_and_file`,
  `finalize_new_top_level_area`): `is_new_top_level_area` is always
  re-checked in Python (`kind not in known_kinds`), never trusted from
  the model's own boolean. **Tier 1** (existing category, or a new tag/
  subfolder within an existing top-level area) writes immediately, with
  a numeric-suffix filename-collision guard and a visible, honest
  low-confidence marker that never pauses placement. **Tier 2** (a
  genuinely new top-level area) unconditionally calls `pending_approval_
  registry.create_pending_approval(...)` — `working_mode_registry` is
  never referenced anywhere in `vault_filing_expert.py` (confirmed by
  `grep`, zero matches), bypassing the working-mode gate **by
  construction**, not a conditional check on it — content is written
  only once the operator approves, via a new `_APPROVAL_HANDLERS`
  dispatch table on `pending_approvals_router.py`'s Approve endpoint
  (`{"propose_new_top_level_area": vault_filing_expert.
  finalize_new_top_level_area}`), consulted before the existing
  `_execute_action`/`run_capture_for_agent` re-dispatch; decline needed
  no new code. `pending_approval_registry.create_pending_approval` gained
  an additive `payload: dict | None = None` parameter (every existing
  zero-payload caller unaffected). **A written note's referenced
  customer/partner is linked mechanically, not left to the model's own
  free-text body:** `_placement_frontmatter`/`_link_referenced_entity`
  add a real `customer`/`partner` frontmatter field plus a real
  `[[wikilink]]` (reusing `customer_hub_linking`/`partner_hub_linking`
  as-is) whenever the model names a referenced entity — **required**,
  not optional, because `list_known_customers()`/`list_known_partners()`
  scan a `customer:`/`partner:` frontmatter field, never the `tags`
  list; a tags-only write is invisible to those lookups even though it
  looks correctly tagged. Verified live end-to-end against all 8 locked
  ACs with a real Compass Provider call, including the critical
  Tier-1/Tier-2 axis (`AC-03`: an identical genuinely-new-top-level-area
  proposal produces the identical pending-approval outcome with the
  agent set to both `"autonomous"` and `"supervised"`) and the honest-
  uncertainty axis (`AC-06`). Full reasoning: `Implementation/
  Architecture/ADR.md` → `ADR-021`; each task's own Implementation Log
  under `Implementation/Tasks/REQ-SB-35-US-01-T01`..`T03`.
- [2026-08-12] `REQ-SB-36-US-01` (Real Anthropic Provider integration +
  `web-research` skill, `SPRINT-022`) shipped end-to-end and verified
  live, per `ADR-022` — **corrected mid-build, operator-directed, not
  built as originally designed:** a new `anthropic` SDK dependency, two
  new required `Settings` fields (`anthropic_api_key`/`anthropic_model`),
  a new `app/data_access/anthropic_client.py` (plain SDK client, not
  LangChain-wrapped — this skill never touches
  `run_agent_conversation`'s graph), and `provider_registry.py` extended
  with a real `"anthropic-claude"` Provider id/auto-seed plus a new
  `get_provider(provider_id)` by-id lookup, all built and verified
  exactly per `ADR-022`'s original design. **`web_research(query,
  agent_id)` itself was corrected mid-build**, per a direct operator
  instruction ("if I linked the Research Agent to Compass, use Compass"):
  it resolves the INVOKING AGENT'S OWN linked Provider
  (`provider_registry.get_agent_provider(agent_id)`), not a single
  hardcoded Provider id — real Anthropic search when linked to
  `"anthropic-claude"`, the same honest "not yet available" response for
  any other linked Provider, never a fabricated result. `skill_registry.
  invoke_skill` additively injects `agent_id` into a handler's call
  whenever that handler's own signature declares it (zero-arg handlers,
  e.g. `diagram-understanding`, unaffected). This correction required
  investigating — not assuming — whether Compass/GPT-5 has any real
  hosted web-search capability; it does not (see the Constraints entry
  below). Fixed the same live-discovered skill-access tool-binding gap
  `ADR-022` point 6 names: `mcp_client.py` gained `load_agent_tools(
  agent_id)` (per-agent-gated by `skill_registry.has_skill_access`,
  replacing the unfiltered `load_vault_query_tools()`), with `graph.py`'s
  one call site updated to match. Verified live end-to-end (real HTTP +
  direct calls): the corrected Provider-resolution dispatch, `AC-02`'s
  `403` access refusal, and the tool-binding gap fix (via in-process
  monkeypatch, since this project's documented MCP-loopback port `8001`
  was held by an unkillable stale listener no available tool could
  clear). **Honest, operator-acknowledged verification gap:** `AC-01`/
  `AC-03`'s own "produces a real relevant result"/"produces a real
  honest-empty result" branches remain unverified — no genuine
  `ANTHROPIC_API_KEY` was available in this environment; a clearly-
  labeled, provably-inert placeholder was added to the real, gitignored
  `.env` solely so the app could boot for every other check (confirmed
  inert — every real call against it honestly failed with a real `401`).
  Full reasoning: `Implementation/Architecture/ADR.md` → `ADR-022`
  (original + its own "Correction" addendum); `ESCALATIONS.md` →
  `ESC-019`; each task's own Implementation Log under
  `Implementation/Tasks/REQ-SB-36-US-01-T01`..`T06`.
- [2026-08-13] `REQ-SB-36-US-02-T01`/`T02`/`T03` (Agent knowledge
  bootstrapping — delegated-research chain, Compass Expert pilot,
  `SPRINT-024`) shipped and verified live, per `ADR-023`. This is the
  first code path in this project that actually ACTS on a Hub-routing
  match (`ADR-017`) rather than only reporting it. New pilot agent
  `"compass-expert"`
  (`agent_registry.py`, data only) with one new action,
  `"build_knowledge"`. New `app/business/agent_orchestration/
  knowledge_bootstrap.py::bootstrap_agent_knowledge(agent_id, subject)`
  — a deterministic (never recursive/model-driven) three-hop composition:
  Hub routing (`ADR-017`) → an Autonomous-mode check
  (`working_mode_registry`) → research (`skill_registry.invoke_skill`,
  `ADR-022`) → Hub routing again → filing
  (`vault_filing_expert.determine_placement_and_file`, `ADR-021`,
  Tier 1/Tier 2). **A real, live-verified finding, not theoretical:** the
  composed `skill_registry.invoke_skill` call can genuinely raise (its
  own real dependency, `anthropic_client.web_search`, raises on any real
  external-API failure rather than returning a result dict) — wrapped in
  a `try/except` converting this into the honest `no_results` outcome;
  confirmed live via a real, unmocked call against the real (provably-
  inert-credentialed) `"anthropic-claude"` Provider that genuinely
  produced a real `401`, correctly caught. `app/api/agents_router.py`'s
  existing `_ACTION_HANDLERS`/`_invoke_action` funnel reused as-is for
  dispatch (no new endpoint), but its own `_execute_action` helper is
  narrowly hardcoded to `run_capture_now`'s own zero-arg/list-returning
  shape — rather than modify it (relied on synchronously by
  `pending_approvals_router.py`, outside this task's own files), added a
  new sibling `_execute_async_action` for the new async, `agent_id`-
  taking handler shape; `_invoke_action` became `async def` (both its
  only call sites already `async def`). A new, generic
  `"history_recorded"` envelope flag prevents the existing generic
  post-call history append from double-recording an outcome
  `knowledge_bootstrap`'s own internal `_record()` calls already logged.
  Verified live end-to-end against the real backend/vault/Compass
  Provider: real Hub-routing hops, a real Tier-2 pending-approval record
  (content reframed to genuinely warrant a new top-level area, since the
  vault's own `"Notes"` catch-all has since materialized — a real,
  live-discovered environmental drift vs. `REQ-SB-35-US-01-T03`'s own
  earlier precedent), real no-match/no-results/not-autonomous honest
  branches, and genericity confirmed via a second, throwaway pilot
  agent. **Honest, disclosed verification gap (same shape as
  `SPRINT-022`):** no real `ANTHROPIC_API_KEY` exists in this
  environment, so the Tier-1 "written"/Tier-2 "pending_approval" full
  chain-composition outcomes were proven via the established, disclosed,
  reverted in-process-monkeypatch technique substituting only the
  externally-credential-gated research step; every other step (both Hub
  hops, the mode check, the real Vault Filing Expert invocation with a
  real Compass LLM call and a real vault write/pending-approval record)
  is fully real. `REQ-SB-36-US-02-T04` (Scenario 3, "draw on afterward")
  remains blocked on `REQ-SB-29-US-01`'s own decomposition (`ESC-018`,
  `Open`) — the story stays `In Progress`, not `Done`; the sprint itself
  reaches `Done` per its own deliberately-scoped Definition of Done.
  `vault-qa` (real runtime config, not code) is now this pilot's real
  Research-Expert candidate (keywords + `web-research` skill access);
  `vault-filing-expert` gained one additional real keyword (`"vault"`)
  for Hop 2 to route to it. Full reasoning:
  `Implementation/Architecture/ADR.md` → `ADR-023`; each task's own
  Implementation Log under `Implementation/Tasks/REQ-SB-36-US-02-T01`..
  `T03`.
- [2026-08-13] `REQ-SB-01-US-01` (Vault Indexing, `SPRINT-025`) shipped
  end-to-end and verified live, per `ADR-024` — **the first real,
  persistent, re-runnable index of the vault's notes anywhere in this
  codebase.** New `app/business/vault_indexing.py`: an in-memory,
  module-level singleton (`_vault_index`), `rebuild_index()`/
  `get_index()`, full rebuild + atomic swap on every trigger — never
  incrementally diffed, so add/edit/delete all reconcile for free with no
  separate code path. Backlinks (incoming wikilinks) are derived in a
  second pass over the freshly-built dict, matched against each note's
  own filename stem case-insensitively — the same identity this
  project's own capture pipelines already write wikilinks against. Folds
  in a real, pre-existing gap fix in `vault_writer._parse_frontmatter_
  value` (a bracketed list value, e.g. `tags: [...]`, now round-trips
  into a real `list[str]`, not the raw unparsed string) and a new public
  `vault_writer.extract_wikilink_targets(body)`. Two trigger surfaces,
  both resolved (`ESC-021`): a new `POST /vault-index/rebuild` endpoint
  (`app/api/vault_index_router.py`), and one new, unconditional
  `vault_indexing.rebuild_index()` call inside `email_classification.
  run_capture_and_record_completion` — not gated by either capture
  step's own working mode, zero changes to `capture_scheduler.py`.
  Deliberately no `.second-brain/` persistence file and no database —
  the index is transient, repopulated by the next trigger (in practice
  bounded by the existing app-start trigger). Verified live against the
  real vault (502-503 real notes across the build): frontmatter/tags/
  outgoing-wikilinks captured exactly, backlinks correctly derived,
  add/edit/delete all correctly reconciled with a temp note, empty-tag/
  no-wikilink notes indexed with real empty lists not an error,
  `.obsidian`/`Templates` correctly excluded, the on-demand endpoint
  reflects a change immediately, and the real app-start scheduler tick
  (a real Outlook COM + Compass capture run) genuinely populated the
  index with no separate call. **One real, live-discovered, disclosed,
  non-blocking exception:** a pre-existing filename-stem collision
  between two distinct real notes (`_slugify`'s 80-char truncation
  silently eats `email_classification.py`'s own trailing disambiguating
  id-suffix when a long subject alone fills the budget) — escalated, not
  silently patched or hidden, `ESCALATIONS.md` → `ESC-027` (Open),
  `/bug` capture recommended; root-caused to already-`Done`, out-of-scope
  code, not to this story's own new indexing logic. `BUGS.md` → `BUG-008`
  (the app-start Outlook-COM capture's own real, already-logged
  indefinite-hang risk) cost two disclosed verification-method
  workarounds this sprint (`TestClient` without the lifespan context for
  the HTTP endpoint; calling the real app-start trigger function directly
  via `asyncio.run` instead of a full server) — both exercised the real
  code path each AC needed, not a weaker substitute. Full reasoning:
  `Implementation/Architecture/ADR.md` → `ADR-024`; each task's own
  Implementation Log under `Implementation/Tasks/REQ-SB-01-US-01-T01`..
  `T04`.
- [2026-08-13] `REQ-SB-04-US-01-T01`/`T02` (`SPRINT-029`, Agent Vault
  Write Access — buildable scope) shipped and verified live, per
  `ADR-025`: `/mcp` now requires a real shared secret
  (`X-Hermes-Shared-Secret`, new `Settings.hermes_mcp_shared_secret`) for
  any non-loopback caller, enforced by a new ASGI middleware
  (`app/api/mcp_auth.py::require_hermes_shared_secret`) wrapping only the
  `/mcp` mount — Second Brain's own in-app loopback MCP client stays
  unaffected by real TCP-peer-address exemption, never anything the
  caller sends. New `app/business/vault_write_tools.py::
  propose_vault_write` never writes directly — it always creates a new
  `trigger="hermes"` Pending Approval (`_APPROVAL_HANDLERS` gains
  `"hermes_vault_write"`), unconditionally bypassing
  `working_mode_registry` (a second instance of `ADR-021` point 5's
  bypass-by-construction precedent). **Scope enforcement is a deliberate,
  documented fail-closed seam** (`_is_within_assigned_scope` always
  returns `False`) until `REQ-SB-29-US-01` ships a real scope registry —
  confirmed live via a real end-to-end MCP tool call: every real
  `propose_vault_write` invocation today is honestly rejected as out of
  scope, never silently allowed and never fabricated as `"pending"`.
  `AC-03`/`AC-04` (confirm/decline plumbing, independent of scope) fully
  verified live via the seeded-`pending_approval_registry` technique;
  `AC-01`/`AC-02` (the real scope-match Scenarios) remain open, tracked on
  the individually-blocked `REQ-SB-04-US-01-T03` (`ESCALATIONS.md` →
  `ESC-026`, `Open`) — the story stays `status: In Progress`, not `Done`;
  `SPRINT-029` reaches `Done` per its own deliberately-scoped Definition
  of Done. Full reasoning: `Implementation/Architecture/ADR.md` →
  `ADR-025`; each task's own Implementation Log under
  `Implementation/Tasks/REQ-SB-04-US-01-T01`/`T02`.
- [2026-08-13] `REQ-SB-11-US-01` (Agent Activity & Error Observability,
  `SPRINT-027`) shipped end-to-end and verified live, no new ADR.
  `email_classification.py::run_capture_and_record_completion`'s two
  Autonomous capture branches are each now independently wrapped in a
  `try/except`, closing both confirmed gaps: meeting-capture now writes
  its own `"run_event"` success entry (parity with email-capture), and
  an exception escaping either step (e.g. `outlook_com.
  OutlookUnavailable`) is caught and recorded as a new `"run_error"`-kind
  history entry instead of propagating uncaught —
  `record_capture_run_completed()` fires only when neither step failed
  this tick. Composed directly around the REAL current file, which had
  already gained `SPRINT-025`'s own unconditional `vault_indexing.
  rebuild_index()` call between `/plan-tasks` and this build — preserved
  unconditionally, ahead of the newly-gated completion call. New
  `outlook_com.py::check_reachable()` (reuses `_connect_namespace()`,
  never raises) and new `app/business/agent_activity.py`
  (`get_agent_activity()` — read-only, no new persisted state, composes
  `agent_registry`/`vault_writer`/`outlook_com` as-is, mirroring
  `system_health.py`'s own shape) plus `GET /agent-activity`
  (`app/api/agent_activity_router.py`). New frontend
  `AgentActivityPage.tsx` + nav wiring, zero new CSS. Verified live
  end-to-end against all 7 locked ACs with real Outlook/vault data: the
  real app-start scheduler tick alone produced the first-ever
  `meeting-capture` success entry; a real in-process-monkeypatched
  email-capture failure proved the `"run_error"` path, cross-agent
  independence, and the completion-gating behaviour (`last_capture_run.
  json`'s `finished_at` unchanged on the failed tick, advancing again on
  a genuine successful one). **Live finding: physically closing Outlook
  desktop does not produce a genuine "unreachable" state on this
  machine** — Windows COM's `Dispatch("Outlook.Application")` silently
  auto-relaunches Outlook.exe on the next connection attempt (confirmed
  via the process's own `StartTime` advancing immediately after a forced
  kill) — the task's own named induction technique had to be substituted
  with this project's established in-process-monkeypatch technique,
  applied to a temporary, port-identical, immediately-reverted backend
  swap so the resulting `badge-danger` "Unreachable" state stayed
  genuinely screen-observable (screenshot-confirmed via the OS-installed
  Edge browser's own headless mode, the closest-to-real substitute
  available since no visual-harness/CDP tool was provided to this Coder
  session). Full reasoning: each task's own Implementation Log under
  `Implementation/Tasks/REQ-SB-11-US-01-T01`..`T04`.
- [2026-08-13] `REQ-SB-02-US-01` (Browse & Search — list/filter by tag,
  wikilink-graph link-list navigation, ranked keyword search,
  `SPRINT-026`) shipped end-to-end and verified live, per `ADR-026`. New
  `app/business/vault_search.py`: `list_notes`/`list_tags`/
  `get_note_detail` compose `vault_indexing.get_index()` read-only
  (`ADR-003`); `search()` is a small, self-contained, field-weighted
  BM25-style ranking function (title=3x/tags=2x/body=1x, standard `k1`/`b`
  constants) computed fresh at query time, no persisted ranking index, no
  new runtime dependency — body text is read fresh per candidate via
  `vault_writer.read_note()` since `vault_indexing`'s own index entries
  (`ADR-024`) never store it. `vault_indexing.py` gained one small,
  additive, independent accessor, `get_last_rebuilt_at()`, alongside
  `get_index()` — an ISO-8601 UTC timestamp set at the end of every
  `rebuild_index()` call, `None` if the index has never been built this
  process lifetime — the honest "nothing indexed yet" signal
  `GET /vault-search/status` and the frontend's whole-page empty state
  both key off. New `app/api/vault_search_router.py` (`GET /vault-search/
  status|notes|notes/{stem}|search|tags`). Frontend: new
  `VaultBrowserPage.tsx` (search box + ranked results, tag-filter chip row
  + paginated browse list) and `NoteDetailPage.tsx` (a note's frontmatter/
  tags plus clickable forward-link/backlink navigation — a link list, not
  a visual graph canvas, per the story's own resolved scope), new
  `features/vault-browser/client.ts`, new `styles/vault-browser.css`
  (`a.item-row`/`button.item-row`, `.tag-chip`, ported verbatim from the
  approved prototype), new `/browse`/`/browse/:stem` routes + sidebar nav
  item. Verified live against the real vault (503 unique-stem notes;
  `BUG-011`'s already-disclosed filename-stem collision unaffected, not a
  new finding) and a real browser: all 7 locked ACs pass, including the
  ranking-relevance guarantee (`AC-04` — a temporary note with only a
  20x-repeated incidental body mention of a rare token ranked strictly
  *below* a temporary note with a genuine title match for the same token,
  confirmed with real, then-deleted, temp notes) and genuine multi-hop
  wikilink click-through navigation between real notes. One scope-internal
  finding: the story's own literal AC-05 example query
  (`"qwzxjklmnop_nonexistent_token_zzz"`) does not actually produce an
  empty result against this real, ~500-note vault — its underscore-
  separated sub-tokens ("nonexistent", "token") are real English words
  that genuinely appear in real work-email bodies, and `search()`'s
  multi-term query is correctly a term-union (any one matching term
  contributes a score) — not a defect; a genuinely opaque single
  alphanumeric token was substituted for the live check instead. Full
  reasoning: `Implementation/Architecture/ADR.md` → `ADR-026`; each task's
  own Implementation Log under `Implementation/Tasks/REQ-SB-02-US-01-T01`
  ..`T04`.
- [2026-08-13] `REQ-SB-09-US-01` (To-Do Task Capture Pipeline,
  `SPRINT-028`) shipped end-to-end and verified live, per `ADR-027` — the
  third capture pipeline after Email/Meeting, and the first to key its
  dedup/top-up mechanism on a stable Outlook-identity LOOKUP INDEX rather
  than a recomputed-and-`exists()`-checked path. New
  `app/data_access/outlook_com.py::list_outlook_tasks` (Tasks-folder
  COM read, `GetDefaultFolder(13)`, no date-window params — a task has
  no "occurs near now" framing). New `vault_writer.py` primitives:
  `upsert_frontmatter_key` (the one genuinely UPSERT-not-insert-only-if-
  missing baseline primitive in this codebase — `due`/`status` only, per
  Scenario 5/6's own "reflect Outlook's current value on every top-up"
  requirement) and the load-bearing `.second-brain/task_note_index.json`
  (`entry_id -> note_filename_stem`, consulted BEFORE any path is
  computed from current fields — the tenth `.second-brain/` state file,
  and the first genuinely load-bearing, not merely audit-trail, one of
  its kind since `conversation_index.json`). New
  `compass_client.classify_task` (customer-only sibling to
  `classify_email`, no `kind` axis, no sender). New
  `app/business/todo_classification.py::classify_recent_todos`. Third
  gated block in `email_classification.py::run_capture_and_record_completion`,
  composed on top of `REQ-SB-11-US-01-T01`'s honest-failure-recording fix
  (own `try/except`/`todo_capture_failed` boolean, extending the trailing
  three-boolean gate) and `SPRINT-025`'s unconditional
  `vault_indexing.rebuild_index()` call — zero changes to
  `capture_scheduler.py`, the third pipeline in a row to prove
  `ADR-005`'s "generalizing the one job" scales. Real `GET /my-day/todo`
  + dashboard count (`my_day.py::list_todo_items`, unwindowed, unlike
  Email/Calendar's rolling 7-day window); populated To-Do drill-down +
  `.badge`/`.badge-warning` ("Due today"/"Upcoming") on `MyDayTodoPage.tsx`.
  **`ADR-027`'s own honestly-disclosed gap is now EMPIRICALLY CLOSED, not
  just structurally reasoned:** the architect role could not live-verify
  `EntryID` stability against the real mailbox; the coder's own mandated
  live check (`T01`'s isolated read→edit→re-read, `T03`'s full
  capture→edit→rerun→confirm-topup cycle) confirmed it holds — zero
  duplicate `EntryID`s across the real 235-item Tasks folder, before or
  after a real due-date/status edit. No superseding ADR needed. One real,
  disclosed, non-blocking finding along the way (see the Constraints
  entry below) — `BUG-011`'s own `_slugify` 80-char-truncation defect
  also affects Task notes, with a worse (same-subfolder literal
  overwrite) consequence than its already-documented case, since Task
  notes share one flat `Work/Tasks/` subfolder with no `kind` split.
  `ESCALATIONS.md` → `ESC-028`. Full reasoning:
  `Implementation/Architecture/ADR.md` → `ADR-027`; each task's own
  Implementation Log under `Implementation/Tasks/REQ-SB-09-US-01-T01`
  ..`T06`.

- [2026-08-15] `REQ-SB-52-US-01` app-wide dark palette + real Plus Jakarta
  Sans / Marcellus typefaces, `tokens.css`-only swap
  (`src/frontend/src/styles/tokens.css`) — reverses the 2026-08-10
  light/green-theme decision on a fresh, explicit operator instruction
  ("Whole app," not "Agents Map only"), not a silent flip-flop. All 9
  `--color-*` tokens now carry the dark SkillTree palette (`--color-bg:
  #0e1118` through `--color-on-accent: #0e1118`); `--font-sans` repointed
  to lead with `"Plus Jakarta Sans"`; new `--font-serif` token added,
  leading with `"Marcellus"`. Both fonts load from real local WOFF2 files
  under `src/frontend/public/fonts/` via two new `@font-face` rules — no
  CDN/network font request. `--agent-color-worker/-producer/-expert` and
  `--color-success/-warning/-danger` are deliberately UNCHANGED (their
  contrast against the new near-black background is a disclosed,
  deferred follow-on, not solved by this story). Because every screen's
  own CSS consumes color exclusively via `var(--color-*)`/
  `var(--agent-color-*)` (verified by grep — zero literal hex colors
  outside `tokens.css`), the swap cascaded app-wide with a single-file
  edit; zero screens needed their own CSS change. Full reasoning:
  `Implementation/UserStories/REQ-SB-52-US-01-app-wide-dark-palette-and-
  typeface-swap.md`; verification evidence:
  `Implementation/Tasks/REQ-SB-52-US-01-T01-dark-palette-and-typeface-
  tokens.md`.

- [2026-08-16] `REQ-SB-54-US-01-T04` generic directory-shaped OKF
  note-kind primitive family (`app/data_access/vault_writer.py`:
  `okf_directory_paths`/`okf_concept_file_exists`/
  `create_okf_directory_baseline`/`ensure_okf_directory_baseline`, plus
  `format_okf_provenance`), applied to Customer via thin wrappers
  (`customer_directory_paths`/`customer_concept_file_exists`/
  `build_customer_concept_frontmatter`/`create_customer_directory_
  baseline`/`ensure_customer_directory_baseline`) — one shared
  mechanism per `ADR-042` point 1, reused unchanged by `T05` for
  Project. `write_note`'s own inline frontmatter-rendering logic was
  extracted into a new private `_write_frontmatter_note(path,
  frontmatter, body)` helper so both `write_note` (flat note kinds) and
  the new directory family's concept-file creation share it —
  behavior-preserving, verified byte-identical output for an existing
  caller (`create_meeting_note_baseline`) before/after. `customer_hub_
  linking.ensure_customer_hub_note` was restructured to build/top-up the
  new directory shape internally while its OWN external contract
  (`{"hub_note_path": str, "created": bool}`) stayed byte-identical, so
  all 5 real call sites (`email_classification.py`,
  `meeting_classification.py`, `people_extraction.py`,
  `todo_classification.py`, `vault_filing_expert.py`) needed zero
  changes. The OLD flat-file primitives (`vault_writer.hub_note_path`/
  `hub_note_exists`/`create_customer_hub_note_baseline`/
  `ensure_hub_note_baseline_frontmatter`) and `app/business/partner_hub_
  linking.py` were deliberately left untouched — confirmed byte-for-byte
  identical via diff — since `partner_hub_linking.migrate_customer_to_
  partner` still depends on the old flat path and teaching it the new
  directory shape is explicitly out of `ADR-042`'s own scope (a
  disclosed, deferred gap: a customer onboarded after this story ships
  won't have its OKF directory migrated to Partners on a Customer->
  Partner reclassification). Directory/concept-file naming reuses the
  codebase's existing `_slugify()` (filesystem-invalid-char stripping
  only — no lowercasing/space-hyphenation, unlike the separate
  `tag_slug()`), matching every other note kind's own path-resolution
  precedent (`hub_note_path`/`meeting_note_path`/`person_note_path`);
  the task file's own manual-test prose used a lowercase-hyphenated
  example folder name (`acme-test-co`) purely as illustrative shorthand,
  not a literal requirement — no locked AC names an exact slug casing.
  Full reasoning: `Implementation/Architecture/ADR.md` → `ADR-042`;
  verification evidence: `Implementation/Tasks/REQ-SB-54-US-01-T04-okf-
  directory-family-and-customer.md`.

- [2026-08-16] `REQ-SB-65-US-01-T01` (`SPRINT-051`) — the first real
  read-only `StateGraph` introspection endpoint. New
  `email_capture_pipeline.get_job_tree() -> list[dict]` calls
  `.get_graph()` on the module's own already-compiled `_GRAPH` singleton
  (never recompiles) and shapes the real `Graph.nodes`/`Graph.edges` into
  `{"id", "name", "depends_on"}`, filtering `langgraph.graph.START`/`END`
  (`"__start__"`/`"__end__"`). New `GET /agents/{agent_id}/jobs` in
  `agents_router.py` (mirrors the `/history`/`/knowledge-gaps` per-agent
  sub-resource shape) returns this tree + a fresh
  `section_registry.get_agent_section` lookup for `email-capture-pipeline`,
  and `[]` (never a 404) for any other real, known agent — 404 only for a
  genuinely unknown `agent_id`. Verified live via FastAPI `TestClient`
  against the real installed `langgraph==1.2.11`: 6 real Job nodes
  returned with the graph's real fork/merge/branch `depends_on` shape
  intact (not flattened to a chain); source contains no hardcoded Job-name
  list; `section_id` tracked a live `PATCH .../section_id` reassignment
  with zero code change. **No new ADR** — extends `ADR-043` point 1's
  module boundary, a new READ path over an already-compiled object;
  `ADR-043` point 6 (Jobs stay tier-less/non-addressable) stays fully
  intact. Full reasoning: `Implementation/Architecture/architecture.md` →
  "Pipeline Job Tree Visualization — read-only `StateGraph`
  introspection"; verification evidence: `Implementation/Tasks/REQ-SB-65-
  US-01-T01-job-tree-data-source.md`.

- [2026-08-17] `REQ-SB-56-US-01-T02` (`SPRINT-053`) — the `Link-to-Thread`
  Job's attendee-overlap + date-proximity fallback strategy, and the fourth
  real instance of this codebase's sibling-JSON-store config convention.
  New `app/business/meeting_thread_link_config.py` +
  `.second-brain/meeting_thread_link_config.json` (self-healing per-key
  defaults, mirroring `working_mode_registry._load_state()`'s own seeded-
  default shape) hold the attendee-overlap floor (`2`), the 1:1 carve-out
  toggle (`true`), and the date-proximity window (`7` days) as REAL,
  `get_*`/`set_*`-backed config values — never Python constants inside
  `meeting_classification.py` (explicit operator instruction, 2026-08-17).
  New `vault_writer.py` primitives: `load_meeting_thread_link_config()` /
  `save_meeting_thread_link_config()` (pure I/O, mirrors
  `load_working_modes_state`/`save_working_modes_state`), and
  `list_thread_notes()` (thin composition over the already-existing
  `list_notes_in_kind_folder("Threads")`, not a new glob). New
  `meeting_classification._link_to_thread_by_fallback_heuristic`, called
  only when `T01`'s primary `conversation_id` strategy left a meeting
  unlinked: both the overlap bar and the date-proximity bar must clear
  (AND); multiple qualifying Threads tie-break by higher overlap then
  smaller date gap; a tie surviving both leaves the meeting unlinked.
  Verified live via a `VAULT_PATH`-scratch vault: overlap+proximity link,
  the 1:1 carve-out firing specifically (not just the raw `>=2` floor),
  both individual bar failures leaving the meeting unlinked, a genuine
  tie-on-both-axes leaving it unlinked, and reconfiguring the floor via
  `set_attendee_overlap_floor` actually changing the outcome (proving the
  comparison reads the configured value, never a baked-in literal). Full
  reasoning: `Implementation/Architecture/architecture.md` → "Meeting →
  Thread Linking — ConversationID Primary Strategy, Attendee-Overlap/
  Date-Proximity Fallback"; verification evidence: `Implementation/Tasks/
  REQ-SB-56-US-01-T02-link-to-thread-fallback-strategy.md`.

- `REQ-SB-67-US-01-T03` (2026-08-17) added the one-shot
  `POST /poc/backfill-thread-summaries` (`app/business/thread_summary_backfill.py`)
  by directly composing `T02`'s own `_synthesize_thread_summary` helper with
  `new_message_body=None` (a pure resynthesis of a Thread's own currently
  persisted `## Summary` + `## Transcript`, no fabricated delta) — no second,
  divergent synthesis implementation was written. Discovery reuses
  `vault_writer.list_all_note_paths()` filtered by
  `frontmatter.get("type") == "Thread"`, mirroring `tag_backfill.py`'s own
  iterate-and-filter shape exactly rather than adding a new
  `list_thread_note_paths()` primitive. Sequential, one real Compass call per
  Thread, no batching/rate-limit config — the architect's own resolved
  posture, matching `classify_recent_emails`'/`summarize_attachment`'s
  already-established no-rate-limit precedent at this data volume.

- [2026-08-18] `REQ-SB-71-US-02` (`SPRINT-061`, `ADR-048` Decision 3/4)
  shipped and verified live against the real operator mailbox/vault — the
  redesigned Thread raw/distilled split, two-stage (`capture_raw_thread_
  messages`/`synthesize_thread`) operator-triggered pipeline, and the
  generic Files/OKF companion convention. `Work/Threads/<slug>/` becomes a
  directory (`{<slug>.md, messages/<date>-<hash8>.md}`), permanently
  deterministic from `conversation_id` alone — `create_thread_note_
  baseline`'s signature dropped its own `date` parameter, and `resolve_
  thread_note_path`/`list_thread_notes` were retargeted from a
  frontmatter scan to a direct existence check. This retargeting is a
  real, disclosed regression risk to the still-live, scheduled `thread_
  match_merge` pipeline (`REQ-SB-55`/`REQ-SB-69`, both `Done`) for any
  pre-redesign, flat-shape Thread — see `ESC-048`/`REVIEW-QUEUE.md`;
  `email-capture-pipeline`'s working mode was deliberately left
  `supervised` (not `autonomous`) as the interim protective measure.
  Stage 1 durably persists real attachment bytes via the EXISTING,
  unmodified `write_attachments` (never a new save mechanism) SPECIFICALLY
  because `email_staging`'s own copy is deleted by Stage 1 itself before
  Stage 2 ever runs — without this, Files/OKF companions would have no
  durable byte source at Stage 2 time. `synthesize_thread` uses
  `classify_captured_email_with_fallback` (never the raw `classify_
  captured_email`), matching `run_email_capture_pipeline`'s own
  established `BUG-015` posture for a real, live Compass classification-
  parse failure.

- [2026-08-18] `REQ-SB-71-US-03` (`SPRINT-062`, `ADR-048` Decisions 5-6)
  shipped and verified live against the real operator Outlook calendar/
  vault — the last story in the `ADR-048` 4-story redesign batch. Meeting
  Capture: one-time stays the unchanged `meeting_note_filename_stem`
  scheme; a recurring series becomes ONE ongoing note,
  `Work/Meetings/<slug-of-series_id>/<slug-of-series_id>.md`, keyed by
  `GlobalAppointmentID` (used ONLY as a series key, never a per-occurrence
  identifier — `ADR-013`/`ESC-012` already live-confirmed it constant
  across a series' own occurrences). Frontmatter drops `subject`/`start`/
  `end`/`location` (raw calendar logistics) — this app's own internal
  bookkeeping fields (`type`/`customer`/`tags`/`thread`) are UNCHANGED,
  still persisted (a real reconciliation between the story's own broader
  Scenario prose and the task's own more precise End-State text, resolved
  by following the End-State text). `teams_link`/`dial_in` are extracted
  via regex from `item.Body` TRANSIENTLY inside `outlook_com.list_
  calendar_events` — the raw body string itself is never returned by that
  function, never persisted anywhere. A new, dated `## History` entry is
  appended per real occurrence (never regenerated/replaced) via the
  unguarded `append_body_section_line`, synthesized from calendar
  logistics plus, when linked, the Thread's own current `## Summary`
  (read via `read_body_section`, never a second Thread-summarization
  call) — idempotency is content-based (the dated marker checked against
  the note's own current `## History` region), no new hidden state file.
  People: `vault_writer.person_note_path` signature changed from `(email)`
  to `(dedup_key, customer)` — `person_note_dedup_key(name, email)` is
  email-when-present else a name-slug, closing the real, previously-
  shipped `meeting_classification.py` `if not email: continue` silent-
  skip gap. A Person nests at `Work/Customers/<slug>/People/<slug>.md`
  when `customer` is a real, matched Customer name, else the existing
  flat `Work/People/<slug>.md` (operator-confirmed 2026-08-18 fallback).
  `people_extraction.ensure_person_note`'s new `customer=` keyword
  (default `None`, so `email_classification.py`'s own 3 existing call
  sites need zero change) is used ONLY as the nesting Customer for the
  no-email case — an email-resolvable person's own email-domain-matched
  Customer is NEVER overridden by it, which is what keeps "never
  force-nested under a Customer they don't genuinely belong to" true.
  `find_person_note_path` (vault-wide scan, mirrors `resolve_thread_note_
  path`'s own precedent) is checked FIRST by `ensure_person_note` — an
  already-existing note is topped up in place, never moved or duplicated,
  regardless of which Customer a later call derives. A real, disclosed,
  non-blocking regression was found (not fixed, out of this story's own
  `## Files to Modify`): `app/business/my_day.py::list_calendar_items`
  reads Meeting `subject`/`start` frontmatter directly (also used for its
  own 7-day window filter) — every new-shape Meeting note is silently
  excluded from My Day's Calendar tab going forward. See `ESC-049`/
  `REVIEW-QUEUE.md`.

- [2026-08-19] `BUGFIX-04-US-01` (`BUG-022`/`023`/`024`/`025`) shipped and
  verified live. `threads.py::send_user_message` gained an optional
  `addressed_agent_ids: list[str] | None = None` parameter — its dispatch
  loop iterates `addressed_agent_ids or thread["brought_in_agent_ids"]`,
  so an empty/omitted list preserves today's broadcast-to-every-brought-in-
  agent behavior byte-for-byte. The addressee list is computed exactly
  once, frontend-side (`Cockpit.tsx`'s existing `resolveMentionedAgents`,
  built for `REQ-SB-49-US-01`) — never a second, independently-maintained
  Python mention parser. `Cockpit.tsx`'s `chat-input-row` became a real
  `<form onSubmit={handleSendMessage}>` (mirrors `AgentDetailPanel.tsx`'s
  own precedent exactly); `handleSendMessage` now applies
  `sendCockpitMessage`'s own returned `CockpitThread` directly via
  `setData(...)` instead of firing a redundant `reload()` GET — no SSE/
  polling/websocket introduced, `send_user_message` already returns
  complete post-turn state synchronously. `REQ-SB-32` ("Rich Text
  Rendering in Agent Chat") is delivered for the first time via `ADR-050`:
  one new shared `src/frontend/src/components/ChatMessageText.tsx`
  wrapping `react-markdown` v9.x with ZERO remark/rehype plugins
  (default-safe by omission — no `dangerouslySetInnerHTML` path exists),
  consumed identically by both `Cockpit.tsx` and `AgentDetailPanel.tsx`'s
  chat-thread renders, applied symmetrically to user- AND agent-authored
  messages (no speaker/role branch). Full verification evidence (real
  Meeting Cockpit, real `@mention` addressing, real Enter-to-send, real
  pending-state/live-update, real `<strong>`/`<li>` DOM across all 3 named
  chat surfaces): `Implementation/Tasks/BUGFIX-04-US-01-T01`
  through `-T04`'s own Implementation Logs.

- [2026-08-19] `BUGFIX-05-US-01` (`BUG-026`) partially shipped:
  `process_staged_email`'s real, live implementation
  (`email_capture_pipeline.run_email_capture_pipeline`) is retargeted off
  the old `StateGraph`/`thread_match_merge` path onto a plain composition
  of `capture_raw_thread_messages` + `synthesize_thread`, closing the
  directory-shape orphaning facet (`AC-02`) by construction — verified
  live. `email-capture-pipeline`'s working mode STAYS `supervised` — the
  flat-shape duplication facet (`AC-01`) does NOT yet close: live
  verification found `ADR-052`'s migration mechanism does not preserve a
  freshly-migrated flat Thread's own real, pre-migration `## Summary`
  content once the same pipeline tick's `synthesize_thread` call next
  regenerates it from the Thread's own now-migrated-but-empty `messages/`
  directory — a genuine, not-yet-resolved interaction gap between `ADR-051`
  and `ADR-052` (`ESC-056`). Do NOT flip the working mode to `autonomous`
  until a future story re-locks `AC-01` against a design that actually
  preserves prior content and re-verifies it live.

- [2026-08-19] `BUGFIX-05-US-01` (`BUG-026`) fully shipped, `Done`.
  `ADR-053`'s one-time, self-consuming `pre_migration_summary.md` sidecar
  (`migrate_flat_thread_to_directory` writes it verbatim before the
  rename; `synthesize_thread` folds it into its SAME existing Compass call
  as prior-history grounding and archives it to `pre_migration_summary.
  consumed.md` on success, fed exactly once) closed the remaining
  flat-shape content-loss gap `ESC-056` found. `AC-01` and `AC-02` both
  verified PASS live against the real `process_staged_email` capability
  endpoint. `email-capture-pipeline`'s working mode is now flipped
  `autonomous` (confirmed via `GET /agents/email-capture-pipeline`) — the
  final undo of `ESC-048`'s protective `supervised` measure; do not revert
  it without a new, disclosed reason.

- [2026-08-19] `BUGFIX-07-US-01` (`BUG-028`) shipped, `Done`. `create_okf_
  directory_baseline`/`ensure_okf_directory_baseline`
  (`src/backend/app/data_access/vault_writer.py`) now take a required
  `identifying_name: str` parameter and write/backfill a bare
  `# {identifying_name}\n\n` header onto `log.md`/`captures.md` via one
  shared `_write_or_backfill_identifying_header` helper — used identically
  on the fresh-creation path and the top-up/backfill path, so a real,
  already-existing, pre-fix headerless file (empty or already carrying
  real appended content) is backfilled without losing anything, and an
  already-headered file is left byte-for-byte untouched (idempotent). The
  headerless-detection rule is exactly "current first line does not start
  with `# `" — confirmed against every real caller that ever appends into
  these files (`append_person_note_update_line`'s three real call sites).
  All four Customer/Project wrapper functions pass their own real display
  name. Verified live against both a synthetic throwaway directory and a
  read-only scan of every real Customer/Project folder in the live vault
  (all confirmed genuinely empty — no real content-bearing candidate
  existed to backfill against yet); `REQ-SB-74`'s own backfill pass will
  apply this to real data naturally going forward.

- [2026-08-19] `BUGFIX-08-US-01` (`BUG-029`, `BUG-030`) shipped, `Done`.
  `pending_approval_registry.create_pending_approval` gained an additive,
  optional `dedupe_key: str | None = None` (`ADR-056`) — a second,
  independent idempotency check, alongside (never replacing) `ADR-018`
  point 2's existing `trigger == "background"` guard, matching an existing
  `status == "pending"` record on the same `agent_id` + `dedupe_key`
  regardless of `trigger`. Wired into `skill_registry.py::invoke_skill`'s
  own central Supervised+mutates gate (`dedupe_key =
  f"{agent_id}:{skill_id}"`, computed internally — zero change to any
  caller, closing `BUG-029`'s scheduled-vs-direct race for every
  Supervised mutating Skill, not just `meeting-capture`), and into the
  four real `BUG-030` call sites (`email_classification.py::
  route_to_project`/`_create_classification_failure_pending_approval`,
  `librarian_housekeeping.py::propose_customer_backfill`/
  `propose_customer_archival_candidates`), each namespaced
  `"{action_id}:{stable_target_identifier}"`. Both `AC-01`/`AC-02`
  verified live against the real backend/vault/store — a real
  scheduled-vs-direct `invoke_skill` race collapsed to one record; two
  real `route_to_project`/`_create_classification_failure_pending_
  approval` calls collapsed to one; two real (bounded, disclosed)
  `propose_customer_backfill`/`propose_customer_archival_candidates` Job
  re-runs produced zero duplicate growth. `agent_schedule_registry.py`'s
  shared dispatch lock was NOT touched (`ADR-056` Decision 3) — the fix is
  deliberately independent of lock timing.

- [2026-08-20] **Hermes replaces Second Brain's own hand-built Agent/Skill/
  Schedule/Approval orchestration layer.** Operator decision, made after a
  cascading sequence of real data-quality incidents (`BUG-031`/`032`/`033`,
  a Partner-vs-Customer directory-shape asymmetry, a full tag revert) and
  a direct challenge to hand-writing scheduling/skill/agent machinery
  ("we are building a framework this is not acceptable"). LangGraph
  (already `langgraph>=1,<2` in this codebase, previously used only for
  the in-app chat loop, `agent_orchestration/graph.py`) narrows to an
  execution-engine role within tasks; Hermes (a full, previously
  under-described agent framework, https://github.com/nousresearch/
  hermes-agent — subagent spawning, its own cron scheduler, a documented
  REST API gateway at `127.0.0.1:8642`) becomes the real agent/skill/
  schedule/approval runtime. Second Brain's own web UI stays the PRIMARY
  frontend (not replaced); its backend narrows to a "data layer" (vault
  capture/indexing, Outlook, MCP tools) organized as discrete Tools
  exposing Skills, called both by Second Brain's own remaining LangGraph
  use and by Hermes' external orchestration via the existing `/mcp` mount.
  First concrete step (2026-08-20, autonomous overnight session, operator
  asleep): archived the 9 now-dead orchestration-layer HTTP routers
  (`agents_router`, `agent_schedules_router`, `agent_activity_router`,
  `cockpit_router`, `demo_taxonomy_router`, `pending_approvals_router`,
  `providers_router`, `sections_router`, `skills_router` — see
  `src/backend/app/_archive/README.md`) and added a real Hermes REST
  client + status router (`data_access/hermes_client.py`, `business/
  hermes_status.py`, `api/hermes_router.py`, mounted at `/hermes/*`) —
  honestly "unreachable" until a real Hermes gateway is configured
  (`HERMES_BASE_URL`/`HERMES_API_KEY` in `config.py`), never a fake/
  fabricated response. Deliberately did NOT archive the underlying
  business-layer registries (`agent_registry`, `agent_schedule_registry`,
  `skill_registry`, `skill_tools`, `pending_approval_registry`, `working_
  mode_registry`, `provider_registry`, `section_registry`, `scope_
  registry`/`scope_query_tools`, `agent_prompts`, `agent_orchestration/`,
  `cockpit/`) or split `librarian_housekeeping.py` into the confirmed
  Outlook/Housekeeping/Vault/Vault Write/Company-Partner/People/Vault
  Admin Tool grouping — real, live dependents were found by tracing actual
  imports (not the original file-classification list alone) that make
  that surgery unsafe to attempt unsupervised: `capture_scheduler.py`'s
  hourly Outlook pull, `mcp_server.py`'s tool-registration chain,
  `vault_write_tools.py`'s write-approval safety gate, and
  `librarian_housekeeping.py`'s Company Review pipeline, which has real,
  unresolved Pending Approvals awaiting the operator's own review right
  now (`BUG-032`). That split also depends on an explicitly operator-
  deferred question (does Hermes' own approval mechanism replace
  `pending_approval_registry`/`working_mode_registry`, or does Second
  Brain keep its own gate regardless of trigger source) — not answered
  yet, so not assumed.

## Patterns

- **When changing a shared save-path/data-shape a producer function
  writes, grep for every real reader of that CONVENTION, not just
  every caller of the producer function itself** — a consumer can
  depend on the shape without ever calling the function that creates
  it. Found live 2026-08-17 twice in the same sprint (`SPRINT-055`):
  `ESC-042` (`provider_registry.py`'s JSON-key shape had a stale-key
  consumer, `system_health.py`, that never called `provider_registry`'s
  own write path) and `ESC-043`/`BUG-018` (`vault_writer.
  write_attachments`'s new per-message-nested save path broke
  `cockpit/attachments.py::_attachments_dir`, which hardcodes the same
  path CONVENTION but never calls `write_attachments` itself). When a
  fix changes where/how something gets saved, also grep for every
  reader that assumes the OLD shape, not just for the writer's own
  direct callers. The `BUG-018` fix itself supported BOTH the old and
  new shape simultaneously (a generator checking flat-then-nested)
  rather than migrating existing data, avoiding any migration step
  entirely — a reusable technique when a path-shape change needs to
  stay backward-compatible with already-saved real data.

- **A MIME `Content-ID` property being present on a COM `Attachment` is
  NOT proof it's genuinely inline — verify it's actually referenced via
  a `cid:` URL in the message's own `HTMLBody` first.** Found live
  2026-08-17 (`BUG-017`, direct fix during `BUGFIX-03-US-01-T01`'s own
  investigation): `outlook_com.py::_is_inline_attachment` treated any
  non-empty `PR_ATTACH_CONTENT_ID` as sufficient proof of inline usage,
  silently dropping real, standalone attachments some mail systems
  happen to stamp a Content-ID on too (confirmed: a real 4.96MB PDF).
  Fix: `f"cid:{content_id}" in html_body` as the actual inline test,
  falling through to the existing filename-based heuristics when the
  Content-ID exists but isn't referenced. Verified live both directions
  against the real mailbox (81 real attachments now recognized, 1747
  genuinely-inline images still correctly filtered).

- **A day-count date-gap computation (not just an in/out-of-window string
  compare) legitimately needs real `datetime.strptime` parsing, even
  though this codebase's established default is to avoid
  `datetime.fromisoformat` and instead string-slice/compare
  `date_value[:10]` prefixes (`my_day.py`'s `_within_window`,
  `email_classification.py`).** Found live 2026-08-17,
  `REQ-SB-56-US-01-T02`: a symmetric tie-break ("smaller date gap wins")
  needs an actual magnitude, which a boundary string-compare cannot give.
  `meeting_classification._date_proximity_gap_days` parses only the
  leading `YYYY-MM-DD` prefix via `datetime.strptime(...,
  "%Y-%m-%d").date()` (never the full COM-stringified timestamp, and
  never `fromisoformat`, which the mixed `"YYYY-MM-DD HH:MM:SS+00:00"` /
  ISO-8601-with-`T` shapes this task reads from both sides would not
  parse identically) then computes `abs((date_a - date_b).days)`. Use
  this narrower parse-the-prefix-only approach, not a wholesale
  reintroduction of full-timestamp parsing, the next time a real gap
  magnitude (not just a window-boundary check) is needed against one of
  this codebase's own COM-stringified or ISO-8601 timestamp fields.

- **A "connect every node to its container's own anchor" convention (a
  Hub-to-agent spoke line) only makes sense when nodes are flat/
  independent — the moment nodes gain a real internal tree/dependency
  structure, only the tree's own ROOT (no incoming edge) should still
  connect to that outer anchor; every other node's real predecessor edge
  already accounts for how it connects into the whole.** `AgentsMapCanvas.tsx`
  drew a Hub line for every agent unconditionally (correct when every
  agent in a Section was independent) — once Jobs with real `depends_on`
  edges existed (`REQ-SB-65`), every non-root Job got a redundant second
  line back to the Hub on top of its real tree edge. Fix: gate the Hub
  line on "has no incoming dependency edge within this Section" — this
  generalizes cleanly, since a standalone agent with no tree at all is
  trivially its own root and keeps its Hub line unchanged. Apply this
  same "only the entry point still connects to the outer anchor" check
  whenever a flat-node visual convention gets extended to cover nodes
  that can now have real internal structure.

- **When a tree-layout algorithm applies a positional offset to a node
  (e.g. a zigzag jitter) and that SAME node is also a branch point, any
  child-partitioning math must re-center on the node's own ACTUAL
  (offset) position, never on the un-offset range it inherited.**
  `layoutAgents.ts::assignTreeAngles`'s `place()` function computed a
  branch's children territory from the original `[lo, hi]` passed into
  the call, not from `center + offset` (the angle the node itself was
  actually drawn at) — a branch reached via an odd `zigzagIndex` (pulled
  off-center by the zigzag) handed its own children a territory centered
  on a point the parent was never drawn at, visually tearing the fork
  away from its own parent. Found live validating `REQ-SB-65`'s real
  6-Job pipeline tree ("all over the place," not a clean fan). Fix:
  recompute a same-width `[branchLo, branchHi]` window centered on the
  node's own placed angle before partitioning branch children; leave
  single-child straight-run continuation on the original `[lo, hi]`
  unchanged (that's the run's own fixed band, working as designed). Any
  future zigzag/jitter + branch-point combination in this codebase should
  apply the same "re-center on where I was ACTUALLY drawn" rule.

- **A `width:0;height:0;overflow:visible` SVG root does NOT reliably let
  its own child shapes paint outside that box in this environment's
  rendering engine, even though the identical zero-size-anchor pattern
  DOES work for plain HTML elements** — this codebase uses a
  "zero-size-anchor" positioning convention throughout (an absolutely-
  positioned `width:0;height:0` box, children self-center/offset via
  `transform`), which is reliable for ordinary HTML elements in every
  browser. An `<svg>` root is a stricter case: browsers clip an SVG's own
  content to its declared viewport as a SEPARATE rule from ordinary CSS
  overflow, and this specific rendering engine clips to a literal 0x0
  viewport regardless of `overflow:visible` on the `<svg>` element —
  confirmed live via a blunt `stroke:red;stroke-width:10px;opacity:1`
  override on a real connector line that still painted nothing, despite a
  real, correctly-positioned non-zero `getBoundingClientRect`. Fix: give
  the `<svg>` genuine non-zero pixel dimensions, offset via `left/top` so
  its center still lands on the original anchor point, paired with a
  matching `viewBox="<-halfW> <-halfH> <W> <H>"` so the internal
  coordinate system's origin still means the same thing — zero changes
  needed to any already-authored child shape coordinates. Found live,
  `html-prototype/agents-map-skilltree-exploration.html`'s
  `.skillmap-tree-lines` (hub-to-agent connector lines never painted at
  all, in ANY state, until this fix — not an opacity/color/animation
  issue, despite those being real, separately-fixed secondary problems
  found during the same investigation). Any FUTURE zero-size-anchored SVG
  in this environment needs the same treatment, not the plain-HTML
  convention.
- **A one-shot CSS `animation` (`@keyframes`) that gets attached to an
  element AFTER page load (e.g. via a class toggled by a click handler)
  gets stuck at its `from`/starting keyframe forever in this rendering
  environment and never completes — even with `animation-fill-mode:
  both`.** This extends an earlier-documented finding (this file's own
  note on `document.getAnimations()[i].currentTime` staying frozen at 0)
  from merely a MY-OWN-VERIFICATION artifact (worked around via
  `.finish()` before reading computed styles) to a REAL user-facing
  rendering bug: a real user interacting with this same Browser-pane
  surface will also never see the animation complete, so anything whose
  BASE visibility depends on an animation reaching its `to` keyframe
  (e.g. a `stroke-dashoffset` "draw-in" effect starting from "fully
  undrawn") will appear to have silently failed/be invisible, permanently
  — confirmed live (a `skillmapDrawLine` connector-line entrance
  animation left the lines invisible in every screenshot, animation
  "finished" or not). CSS `transition`s (state changes, not `@keyframes`)
  do NOT have this problem — they progress correctly over real elapsed
  wall-clock time even without any `.finish()` call (confirmed live: a
  0.4s+0.1s-delay opacity transition genuinely completed after a real
  2-second wait). **Rule of thumb for this environment: prefer
  `transition` over `animation` for anything whose end-state must be
  reliably visible; reserve `animation`/`@keyframes` for effects where
  never-completing is cosmetically acceptable (e.g. an `infinite` ambient
  pulse).** Found live, same investigation as the SVG-clipping pattern
  above.
- **Generic before/after length comparison to detect "did this handler
  already self-record its own outcome," instead of a per-handler flag or
  hardcoded exclusion list** — a shared, catalog-spanning dispatch wrapper
  that must append exactly one outcome record per real call, without
  double-recording a handler that already writes its own history entry
  internally, can compare the target log's own length immediately before
  and after the real call rather than trusting every handler to
  consistently set a `"history_recorded"`-style flag (some do,
  `build_knowledge`; some don't, `run_capture_now`'s real `email-capture`
  path — a real, live-discovered inconsistency). Catches any current or
  future self-recording handler generically. Found live,
  `REQ-SB-47-US-01-T02` (`agent_schedule_registry.
  dispatch_with_shared_lock`).
- **Verify a story's own single highest-risk guarantee via two
  independently-derived techniques when the opportunity arises naturally**
  — a controlled, synthetic proof (e.g. `asyncio.gather` with explicit
  timing markers) and a genuinely real, unplanned production-shaped race
  (e.g. a concurrent HTTP call arriving while a real background job
  happens to be in flight) are complementary, not redundant confirmations
  of the same property. Found live, `REQ-SB-47-US-01-T02`/`T05` (the
  shared dispatch lock).
- **Agents Map overview and drill-down consume two deliberately different
  agent lists — never conflate them** — `AgentsMapPage.tsx` fetches once
  but derives two separate `MockAgent[]` lists for `AgentsMapCanvas.tsx`:
  `agents` (`layoutAgents()`'s `mapAgents`, which REQ-SB-38-US-01's
  clustering deliberately reduces — excludes any agent a cluster marker
  now represents) for the overview's own compact dots, and `fullAgents`
  (every fetched agent, unreduced) for `SectionDrilldown`/
  `ClusterDrilldown`, whose own "show everything this view is scoped to,
  never collapsed/hidden" contract would otherwise silently lose agents.
  Any future change to what `mapAgents` includes must re-check both
  drill-down consumers against this same distinction. Found live,
  `REQ-SB-38-US-01-T04`.
- **Agents Map layout is computed, not hardcoded** — `layoutAgents.ts`
  derives each agent's section (from `type`) and ring angle (evenly
  spaced across a fixed arc centered on its section's hub angle) from
  whatever the real `GET /agents` list contains, replacing
  `mockAgents.ts`'s static per-agent coordinates (2026-08-11, operator-
  directed, outside the formal pipeline as a small wiring task). Adding/
  removing an agent in `agent_registry.py` now reflows the map
  automatically — no frontend coordinate math to hand-update, avoiding
  the prototype's own ~6 rounds of manual per-node re-derivation
  (ADR-010's Decision 4 rationale, applied one layer further).
- **Backend-layer-first live verification, frontend last, for any story
  spanning both** – smoke-check each `data_access` → `business` → `api`
  layer directly (a Python shell / raw HTTP call) against the real vault
  *before* writing any frontend code against it, so any later frontend
  defect is isolated to rendering, not upstream data shape. Found live
  2026-08-11, `SPRINT-009` (`T01`→`T02`→`T03` each smoke-checked before
  `T04` wrote a line of React).
- **Temporary client-side stub-and-revert for AC states real vault data
  can no longer produce naturally** – when a locked AC needs an
  all-zero/empty state but a capture pipeline already has real data,
  temporarily replace the relevant `features/*/client.ts` fetch function's
  body with a fixed literal return value, verify the rendered state, then
  revert and re-confirm the real populated state is restored exactly — no
  vault file is ever created or needs cleanup. First established
  `REQ-SB-12-US-01-T02`; reused three times in `SPRINT-009`
  (`T04`/`T05`/`T06`) once real Email and (mid-sprint) real Meeting data
  both existed.
- **COM-assisted, one-time determination of a "no safe default" config
  value** – when a required config value has no safe default and an ADR
  has already rejected sourcing it *dynamically* at runtime (e.g.
  `Settings.self_email`, ADR-008), a one-time, **read-only** probe of the
  same external system (here, Outlook's `Namespace.CurrentUser` →
  `GetExchangeUser().PrimarySmtpAddress`) to determine *what static value
  to configure* is a legitimate middle path between guessing and blocking
  on a human question — as long as it's read-only (no side effects), the
  determination is logged, and it's clearly distinguished from the
  rejected dynamic-lookup alternative (the ADR rejected sourcing the value
  *at every call*, not a one-time bootstrap determination of the value to
  write into `.env`). Found live 2026-08-11, `REQ-SB-08-US-01-T01`/`T03`.
- **Pin dependency versions explicitly when an ADR names a specific major
  version** – `npm install <pkg>` (no version specifier) resolves to
  whatever is currently latest, which can silently drift past the major
  version an ADR actually analyzed. Found live 2026-08-11
  (`REQ-SB-12-US-01-T01`): `npm install react-router` resolved to `v8.3.0`
  (released after ADR-010 was written the same day), not the `v7.x`
  ADR-010's Decision 1 explicitly names — corrected by reinstalling
  pinned (`react-router@^7.0.0`, resolved `^7.18.2`). Always pin to the
  ADR's stated major when installing a dependency an ADR already named.
- **Headless-Chrome-via-CDP as this project's zero-dependency frontend
  verification tool, until a real test-stack ADR lands** – no
  Playwright/Puppeteer/test-runner exists in `src/frontend` yet (first
  frontend build, `REQ-SB-12-US-01`/`SPRINT-008`). A small driver script
  using Node's built-in `WebSocket`/`fetch` against a locally-launched
  `chrome.exe --headless=new --remote-debugging-port=<port>` is enough to
  drive real DOM interaction (clicks, `classList`/`aria-*` inspection,
  screenshots) against the real `npm run dev` server for manual-mode AC
  verification, with zero new project dependencies. Reuse this approach
  for future frontend sprints (`SPRINT-009`/`SPRINT-010`) until a formal
  Playwright/Puppeteer test-stack ADR replaces it.
- Both `list_known_customers` and `list_known_kinds` in `app/data_access/
  vault_writer.py` derive their lists from the vault itself (frontmatter
  scan / folder scan respectively) — never hardcode a customer or kind
  list in business logic. This replaced an earlier `_KNOWN_CUSTOMERS`
  hardcoded placeholder in `email_classification.py`, since removed.
- Promote a private `data_access` normalization helper to public the
  moment a second layer needs the identical logic, instead of
  duplicating it — `vault_writer._tag_slug` → public `tag_slug`
  (`REQ-SB-10-US-01-T01`), reused by `app/business/people_extraction.py`
  for company-to-known-customer slug matching. Pure rename, no behavior
  change; keeps one normalization function per concern instead of two
  copies drifting apart.

- **Reserve one untouched "fixture" entity up front whenever a locked AC
  needs to observe genuinely empty state, and route every unrelated
  smoke-check of the same category away from it** — decided at
  build-planning time, not discovered as a test collision afterward.
  Found live 2026-08-11, `REQ-SB-13-US-01`/`SPRINT-010`: kept the
  `meeting-capture` agent's communication history completely untouched by
  substituting a different no-real-handler agent (`todo-capture`) for an
  earlier non-AC smoke check, so a later locked AC (empty-state
  communication history) could use `meeting-capture` exactly as its own
  task file specified, with no risk of a same-run collision. Generalizes
  beyond agents to any locked AC asserting "nothing recorded/created yet."
- **Consolidate a real-side-effect verification step across sibling
  tasks into one live invocation, instead of triggering the same
  real-world action multiple times in immediate succession** — when more
  than one task's own `## Tests` exercises the identical real endpoint/
  action (e.g. a direct-HTTP smoke check in a backend task, plus a
  UI-driven check of the same action in a frontend task), perform the
  real trigger once and use its outcome as evidence for both tasks' own
  contracts, logging the consolidation in each task's Implementation Log.
  Found live 2026-08-11, `REQ-SB-13-US-01-T05`/`T07`/`SPRINT-010` — the
  "trigger `run_capture_now` via chat" real capture run was performed once
  (through the actual browser UI) rather than once via direct HTTP (`T05`)
  and again via the UI (`T07`), matching both tasks' own "be deliberate"
  instruction.
- **React Fiber-props direct-invoke for verifying a `disabled`-gated
  click handler** — a native click dispatched (via `.click()` or
  `dispatchEvent(new MouseEvent(...))`) at a DOM button element does NOT
  reach React's `onClick` handler if React's own Fiber props still say
  `disabled={true}`, even after removing the DOM `disabled` attribute
  directly — React's event system checks its own prop state, not the raw
  DOM attribute, for click/mouseover-family events on form controls. To
  exercise the exact handler a real click would call once genuinely
  unblocked (e.g. confirming a blocked-delete's error path renders
  correctly), read it directly off the element's React Fiber props
  (`el[Object.keys(el).find(k => k.startsWith('__reactProps$'))].onClick`)
  and invoke it directly, rather than fighting the DOM-attribute
  workaround. Verify the technique first against a known-*enabled* control
  element in the same session to rule out a harness bug before concluding
  it's this React behavior. Found live 2026-08-11,
  `REQ-SB-18-US-01-T07`/`SPRINT-011`.
- **Server-side monkeypatch-and-revert for "recomputes fresh on every
  call, never cached" ACs** — extends the existing client-side
  stub-and-revert pattern one layer server-side: to prove a value derived
  from `datetime.now()` (or any other live-clock dependency) truly
  recomputes on every call rather than being cached, temporarily
  monkeypatch the module's own reference to the dependency (e.g.
  `my_day.datetime = FakeDatetimeSubclass`) in a live shell, capture the
  shifted result, revert to the real reference, and re-confirm the
  original result is restored byte-exact — no real day needs to pass, no
  vault/DB fixture needs writing or cleanup. Found live 2026-08-11,
  `REQ-SB-22-US-01-T01`/`SPRINT-013`.
- **Prefer a process-only environment-variable override over editing a
  committed local dev-config file when only the current verification
  session's port needs to differ** — e.g. set `$env:VITE_API_BASE_URL`
  before `npm run dev` rather than editing `.env.local`, when the
  frontend's committed dev-server target port is already occupied by a
  concurrent session and the file itself isn't in the current task's
  `## Files to Modify`. Zero risk of an out-of-scope file edit, zero
  cleanup needed. Found live 2026-08-11, `REQ-SB-22-US-01-T02`/
  `SPRINT-013`.
- **Scope DOM queries to the specific card/component, never
  `document`-wide, once a page composes two structurally-identical list
  components** — `SectionsCard`/`ProvidersCard` both render a
  `form.item-row-actions` with a `button[type="submit"]`; an unscoped
  `document.querySelector(...)` silently matches the *first* sibling in
  document order, producing a misleading "nothing happened" result rather
  than an error. Disambiguate via the nearest ancestor carrying a unique
  heading/button-text/data-attribute before querying inside it. Found live
  2026-08-11, `REQ-SB-19-US-01-T05`/`SPRINT-012`.
- **Verify a real side-effect's *absence* via the domain's own audit
  trail, not just the triggering call's response** — confirming "no real
  Outlook/Compass call happened" for a gated action by reading the agent's
  own `GET /agents/{id}/history` (checking the most recent entry is the
  honest-unavailable message, with no new success entry appended after it)
  is stronger evidence than trusting the HTTP response alone. Found live
  2026-08-11, `REQ-SB-19-US-01-T04`/`SPRINT-012`.
- **A "field X must never appear in response Y" guarantee needs a
  precise, literal-key substring check, not a loose one** — `grep -o
  "credential"` false-positives on `credential_set`; scoping the check to
  the exact quoted JSON key (`"credential"` with its quotes) is what
  actually proves a never-returned-field trust-surface guarantee
  (`ADR-014` point 5) rather than merely looking like it does. Found live
  2026-08-11, `REQ-SB-19-US-01-T03`/`SPRINT-012`.
- **Verify a visual-containment AC via real DOM `getBoundingClientRect()`
  intersection, not a distance-to-a-reference-point proxy** — when a
  locked AC's own wording asserts "no element visually overlaps X," the
  load-bearing check is literal bounding-box intersection between the real
  rendered elements at their real computed positions; a "nearest center
  distance" heuristic can diverge from it whenever elements sit at
  different radii/sizes from their reference point. Found live 2026-08-12,
  `BUGFIX-02-US-01-T06`/`SPRINT-016`: 2 of 4 real dense-Section agent nodes
  were geometrically nearer a neighboring Section's Hub center than their
  own (global, not per-Section, pre-existing ring radii), yet zero real
  bounding-box overlap existed anywhere — the distance heuristic was never
  a sound proxy for the AC's own literal "no visual overlap" text.
  Cross-check with a full-page (`captureBeyondViewport`) screenshot when a
  headless-Chrome-via-CDP session is in play, since content that scrolls
  out of the default viewport can otherwise look like a blank-page failure.
- **When a task's own literal "full replacement" code sample targets a
  file that a later, already-`Done` sibling task has since extended,
  compose the new change around the REAL current file, never overwrite
  it with the stale sample** — `REQ-SB-26-US-01-T03`'s own sample for
  `agent_orchestration/graph.py` was written against an earlier, simpler
  single-node shape; the real file (`REQ-SB-25-US-01-T08`'s own live
  correction) had since grown a `call_model`⇄`execute_tools` tool-calling
  loop. Blindly applying the sample would have silently regressed a
  sibling story's own already-verified, `Done` mechanism. Diff the task's
  intent (which nodes/edges are genuinely new) against the file's actual
  current contents first, and re-derive any node logic that implicitly
  assumed the file's old shape (e.g. whether the model's own response is
  already appended onto the message list by the time a later node runs)
  rather than trusting the sample's own internal assumptions. Found live
  2026-08-12, `REQ-SB-26-US-01-T03`/`SPRINT-015`.
- **A `FastMCP` `@tool()` decorator registers on the shared server
  *object*, not by editing that object's own defining module's source** —
  a sibling module (e.g. `skill_tools.py`) can import the already-mounted
  `FastMCP` instance from `mcp_server.py` and decorate its own function
  with it; the tool becomes live/listed on the shared server with zero
  edit to `mcp_server.py` itself, as long as the sibling module is
  imported (directly or transitively) before the server starts serving
  requests. Confirmed live via `await mcp_server.list_tools()` showing the
  new tool alongside the pre-existing ones. Found live 2026-08-12,
  `REQ-SB-27-US-01-T02`/`SPRINT-015`.
- **A `uvicorn --reload` worker can survive its own reloader dying,
  silently serving stale code forever.** After a very large watched-file
  change event (e.g. a fresh `pip install` touching thousands of
  `.venv` files, as `REQ-SB-25-US-01-T01`'s LangGraph/MCP install did),
  the reloader parent process can crash or exit while its
  `multiprocessing`-spawned worker child keeps the listening socket —
  `Get-Process <parentPid>` returns nothing, but the port is still
  answering real requests, and further file edits never trigger a
  reload (`WatchFiles` lives in the dead parent). Symptom: an edited
  endpoint keeps returning its old response shape indefinitely, with no
  error anywhere. Diagnosis: `Get-CimInstance Win32_Process -Filter
  "Name='python.exe'"` and look for a `--multiprocessing-fork` child
  whose `ParentProcessId` no longer exists; kill that specific child PID
  (not a blanket image-name kill, `SPRINT-009`'s own antipattern), then
  restart the server normally. Found live 2026-08-12 debugging
  `my_day.py`'s window-display fix appearing to have no effect.
- **In-process monkeypatch of a real, already-loaded dependency to induce
  a failure condition, instead of editing a file outside the current
  task's own scope.** When a locked AC needs a real failure (e.g. a real
  tool-call error, per `_execute_tools`'s existing "Tool call failed:
  {exc}" path) but the obvious way to induce it would mean editing a file
  outside the task's `## Files to Modify`, a throwaway script (kept only
  in the session scratchpad, never written into `src/`) can load the real
  dependency (e.g. the real MCP tools via the real running server),
  monkeypatch just the one call that needs to fail in-process, and invoke
  the real, unmodified production function directly — exercising the
  genuine code path end-to-end with zero file edits and zero revert step
  needed. Found live 2026-08-12, `REQ-SB-33-US-01-T01`/`SPRINT-018`.
- **Native `input.focus()`/`input.blur()` DOM-API calls are not a reliable
  substitute for a real user-driven blur in a headless-Chrome-via-CDP
  session — prefer the Fiber-props-direct-invoke technique for any React
  `onBlur`/commit-on-blur handler by default.** Even a real `.blur()` call
  (confirmed via `document.activeElement` genuinely changing, not a no-op)
  did not reliably deliver the native `focusout` bubbling event React's
  `onBlur` prop depends on in this environment — confirmed via the CDP
  `Network` domain that no request the handler should have fired ever
  appeared. Reading the real handler off the element's own React Fiber
  props (`el[Object.keys(el).find(k =>
  k.startsWith('__reactProps$'))].onBlur({ target: el })`) — the same
  technique already established for a `disabled`-gated `onClick`
  (`REQ-SB-18-US-01-T07`) — works reliably; confirm it fires the real,
  unmodified production code path (e.g. a real network request observed)
  before trusting it. Found live 2026-08-12, `REQ-SB-20-US-01-T06`/
  `SPRINT-020`.
- **Set a React-controlled `<input>`'s value via the native
  `HTMLInputElement.prototype.value` setter, not a plain `.value =`
  assignment, when driving it from a CDP session.** Plain `input.value =
  'x'` followed by a dispatched `'input'` event silently no-ops against
  React's own internal value-tracking (the tracker already reads the
  newly-assigned value as "unchanged," so `onChange` never fires) — use
  `Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,
  'value').set.call(input, value)` before dispatching `'input'` instead.
  Found live 2026-08-13, `REQ-SB-02-US-01-T04`/`SPRINT-026` (a search box
  silently never submitted the typed query).
- **A CDP `Page.reload()` wipes any in-page `window.fetch`/monkeypatch
  stub (fresh JS execution context); prefer an SPA-internal client-side
  remount (nav away, then back) to re-trigger a component's mount-time
  effect while keeping the stub alive.** Needed whenever a locked AC
  requires re-fetching a stubbed endpoint on (re)mount, e.g. an honest
  "not yet indexed" whole-page empty state gated on a status call. Found
  live 2026-08-13, `REQ-SB-02-US-01-T04`/`SPRINT-026`.
- **Run the real console/network-error check via CDP as its own explicit
  step, after all click-driven interaction, whenever a task adds new UI
  that iterates and fetches against an existing store unconditionally**
  (e.g. rendering every entry of a given `kind` in an append-only history
  list) — a prior task's own explicitly-authorized "harmless" throwaway
  test entry can become a real, live-reproducible unhandled-promise-
  rejection once later code starts resolving every such entry's live
  status. The console/network check is what surfaces this, not code
  inspection; fix by making the new fetch chain degrade gracefully
  (`.catch(() => {})`) and, where practical, pruning the stale artefact
  from the real store. Found live 2026-08-12, `REQ-SB-21-US-01-T07`/
  `SPRINT-021`.
- **A real background/scheduled pipeline call can take 1.5–5 minutes
  end to end (Outlook COM + Compass, especially a full multi-item
  sweep) — background the verification shell call with unbuffered
  (`flush=True`/`python -u`) output from the start, rather than a
  blocking call that hits the shell's own default timeout.** A killed-
  mid-flight attempt can silently leave shared mutable state (e.g. an
  agent's working mode) already changed by the time a differently-
  labelled retry runs against it — always re-assert the intended
  precondition explicitly at the top of a retry script rather than
  trusting the label. Found live 2026-08-12, `REQ-SB-21-US-01-T04`/
  `SPRINT-021`.
- **When no visual-harness/CDP/screenshot tool is available in a Coder
  session, the OS-installed Edge browser's own headless screenshot mode
  (`msedge.exe --headless=new --disable-gpu --window-size=<W>,<H>
  --screenshot=<path>.png <url>`) is a legitimate, zero-new-dependency
  substitute for "LOOK before Done"** — it renders the real app through a
  real browser engine against the real dev server, producing a real PNG
  the Read tool can view directly (not a mock, not a code-reading-only
  claim). For a page whose content grows past one viewport (e.g. a
  `.log-list` with no max-height), request a very tall `--window-size`
  height and crop the result with PowerShell's `System.Drawing.Bitmap`
  rather than trying to simulate a real scroll interaction. Found live
  2026-08-13, `REQ-SB-11-US-01-T04`/`SPRINT-027`.
- **To genuinely screen-verify a real external dependency's "down" state
  when the dependency itself silently self-heals (e.g. Windows COM
  auto-relaunching a killed target application on the next `Dispatch()`
  call), temporarily swap the running backend process for one with the
  dependency's connection function monkeypatched in-process, on the SAME
  port the frontend is already wired to** — stop the real server, run a
  tiny bootstrap script that patches the target function before
  importing/serving the real, otherwise-unmodified app, screenshot, then
  stop it and restart the real server normally. Keeps the check genuinely
  end-to-end (a real rendered badge) rather than dropping to a
  backend-only substitute. Found live 2026-08-13,
  `REQ-SB-11-US-01-T02`/`T04`/`SPRINT-027`.
- **Browser-pane `computer` clicks (coordinate- AND `ref`-based) can
  silently no-op on a plain static HTML prototype page, and its
  `screenshot` can misrepresent real layout (content rendered tiny/
  mispositioned vs. actual computed rects)** — found live 2026-08-14
  building `agents-map-skilltree-exploration.html`: a `left_click` on a
  button's own `ref` reported success, but `document.getElementById(...).
  hidden` stayed unchanged immediately after; a follow-up screenshot showed
  the whole page's content clustered near the top-left at a fraction of its
  real size, while `getBoundingClientRect()` on the same elements confirmed
  correct real-viewport-centered positions. Before concluding this is a
  real page bug, rule it out first: cross-check with `document.
  elementsFromPoint(cx, cy)` at the target's own real computed-rect center
  — if the intended element comes back topmost, a genuine user click there
  would work, and the tool's own click/screenshot delivery is the suspect,
  not the page. Reliable verification path once ruled out: dispatch the
  real `.click()` method directly on the element (exercises the identical
  event-listener code path a genuine click would, unlike simulating
  low-level mouse events) and confirm the resulting state via
  `getComputedStyle`/`getBoundingClientRect` rather than trusting the
  screenshot. Note a CSS-transitioned property read via `getComputedStyle`
  immediately after the triggering DOM mutation, in the same synchronous
  script, returns the value AT THAT INSTANT (mid-transition, often still
  ~equal to the pre-change value) — not the transition's target value; wait
  for the transition or re-check output in a later tool call before
  concluding the CSS rule itself is broken.

- **Additive Prompt-override wiring for a function whose hardcoded prompt
  string interleaves static instructions with per-call dynamic data (no
  separate SystemMessage/HumanMessage split) — split the ORIGINAL literal
  into two locals at its own existing `"\n\n"` boundary
  (`default_instructions` = the static portion, unchanged; `dynamic_content`
  = the trailing per-call f-string, unchanged), then branch on the new
  `prompt_override: str | None = None` parameter: `None` →
  `default_instructions + dynamic_content` (byte-for-byte identical to the
  original single literal, since the two locals are literally its own split
  halves); not-`None` → `f"{prompt_override}\n\n{dynamic_content}"` (override
  text, then the same real per-call dynamic data appended verbatim).**
  Guarantees the regression bar (unset override → byte-for-byte unchanged
  output) essentially for free, since no new derivation logic touches the
  default path at all — only a mechanical split of the existing literal.
  Found live 2026-08-16, `REQ-SB-66-US-01-T02`, applied to all 4 of
  `compass_client.py`'s hardcoded-prompt functions
  (`classify_email`/`classify_task`/`guess_project_for_thread`/
  `summarize_content`); reusable wherever a future task wires an override
  into another single-combined-string prompt builder in this codebase.

- **Additive Prompt-override wiring when the prompt builder ALREADY keeps
  a separate SystemMessage (static instructions) from a HumanMessage
  (per-call dynamic content)** — no string-splitting needed at all: branch
  directly on the new `prompt_override: str | None = None` parameter to
  pick the SystemMessage's own `content` (`prompt_override if
  prompt_override is not None else <existing hardcoded constant/f-string>`),
  and leave the HumanMessage's own construction completely untouched.
  Simpler than the T02 pattern above precisely because the static/dynamic
  split already exists at the message-list level, not just within one
  string. Found live 2026-08-16, `REQ-SB-66-US-01-T03`, applied to
  `agent_orchestration/state.py`'s `history_entries_to_messages` (Chat
  SystemMessage) and `vault_filing_methodology.build_placement_prompt`
  (`_METHODOLOGY_EXCERPT` SystemMessage) — check which of these two
  shapes (interleaved single string vs. already-separate
  SystemMessage/HumanMessage) a given call site has BEFORE picking a
  split strategy; do not force the string-split technique onto a call
  site that doesn't need it.

- **A third Prompt-override wiring shape: when the callee's own generic
  built-in default instructions cannot know about a NEW, caller-specific
  response-format requirement, resolve the fallback in the CALLER, not
  the callee — always pass a non-`None` `prompt_override` down.** Neither
  of the two shapes above fits when `compass_client.summarize_content`'s
  own built-in `default_instructions` has no idea a particular call site
  needs its `"summary"` string split into two parts (an opening-line
  sentence + a fuller abstract). Fix: the caller computes `prompt_override
  = agent_prompts.get_prompt(id) or <caller's own hardcoded
  default-instructions literal that DOES know about the required
  format>` and always passes that resolved, non-`None` value into
  `summarize_content` — never `agent_prompts.get_prompt(id)` bare, which
  would silently fall back to `summarize_content`'s own generic,
  format-unaware default the moment no override is saved. Found live
  2026-08-17, `REQ-SB-67-US-01-T02`,
  `email_classification._synthesize_thread_summary`'s own
  `_THREAD_SUMMARY_SYNTHESIS_DEFAULT_INSTRUCTIONS` fallback for
  `thread_match_merge`. Use this shape (not the two above) whenever a new
  call site needs a response format/contract the shared callee's own
  built-in default doesn't already produce.

- **Frontend consumption of a backend contract that genuinely OMITS a JSON
  key (vs. sending it as `null`) must gate rendering on key PRESENCE
  (`'field' in response`), never on the field's own value/truthiness.**
  Collapsing "key absent" and "key present but empty/falsy" into the same
  rendering branch silently reintroduces the exact "shown but inert field"
  outcome the backend's own omission was designed to avoid — an absent
  Prompt key (no real runtime call site to wire an override into) and an
  empty-but-present Prompt override (a real call site, just not yet
  customized) are semantically different and must render differently (no
  row at all vs. an empty, editable row). Found live 2026-08-17,
  `REQ-SB-66-US-01-T07`, `JobSettingsPanel.tsx`'s `showPromptRow = 'prompt'
  in settings` check against `T06`'s own omitted-key `GET .../settings`
  contract (`thread_match_merge`/`detect_recurring_pattern`); reusable
  wherever a future frontend task consumes a backend response that
  similarly omits a key to mean "no real value/mechanism exists here,"
  rather than `null`/`""` meaning "unset but valid."

- **`IncludeRecurrences`-expanded recurring-occurrence calendar items are
  unreliable for per-item Outlook COM identity/relationship properties on
  this installation — check live before trusting a NEW one, don't assume
  a property that works for single-occurrence items also works for
  expanded occurrences.** Three independent, live-confirmed failures on
  the exact same real recurring series/mechanism so far, each breaking
  differently: `EntryID` (`ESC-002`) — identical across all occurrences
  of a series, not unique; `GlobalAppointmentID` (`ESC-012`) — same
  non-uniqueness, both the native property and its documented
  `PropertyAccessor`/DASL fallback; `ConversationID`
  (`REQ-SB-56-US-01-T00`, `ESC-040`, 2026-08-17) — worse still: resolves
  to a non-string bound-method object via `getattr()` (raises `Member not
  found.` if invoked) and the raw MAPI `PropertyAccessor` read of
  `PR_CONVERSATION_ID` also fails (`Type mismatch.`); `bool()` of the
  broken bound-method object is truthy, so the codebase's own established
  `getattr(item, "X", None) or ""` fallback pattern (used for mail's
  `conversation_id`) does NOT safely degrade this to an empty string —
  it silently passes the broken object through as if it were real data.
  Any future `list_calendar_events` (or similar `IncludeRecurrences =
  True`) code that reads a new per-item COM property must live-verify it
  specifically against a real recurring series before trusting it, and
  must not assume `getattr(...) or ""`-style truthiness checks are
  sufficient to detect this class of breakage.

- **Never trust a bound-method/non-string COM property return as
  truthy — guard with `isinstance(value, str)`, not `or ""`.** Fixing
  the `ConversationID` finding above (`REQ-SB-56-US-01-T01`, 2026-08-17):
  `getattr(item, "X", None) or ""` only filters a FALSY broken value; a
  COM property that resolves to a bound-method object instead of raising
  on attribute access is truthy, so `or ""` lets it through unchanged.
  The safe pattern this task established
  (`outlook_com._resolve_conversation_id`): read the attribute inside a
  narrow `try/except` (covers a property that raises on access itself),
  then require `isinstance(value, str)` before returning it, else `""`.
  This is now the third independent, live-confirmed instance of this
  exact class of finding on this Outlook installation (`EntryID` —
  `ESC-002`; `GlobalAppointmentID` — `ESC-012`; `ConversationID` —
  `ESC-040`) — apply this same `try/except` + `isinstance(str)` guard to
  any future per-item COM identity/relationship property read on an
  `IncludeRecurrences`-expanded item, not the codebase's older
  `getattr(...) or ""` convenience shorthand.
- **A "one-shot maintenance operation reuses a live-capture-path synthesis
  helper with the delta parameter set to `None`/absent" shape** —
  `REQ-SB-67-US-01-T03`'s `backfill_thread_summaries()` calls the exact
  same `_synthesize_thread_summary(existing_summary, transcript,
  new_message_body, prompt_override)` helper `thread_match_merge` (live
  capture) calls, just with `new_message_body=None`. Apply this shape
  whenever a backfill/maintenance operation needs to reproduce a live
  call site's own synthesis logic without a new/duplicate implementation
  — design the live call site's own helper to already accept an
  optional-delta parameter up front (as `T02` did), so the backfill task
  never has to fork it.
- **A read-side accessor that must emit an honest placeholder for every
  member of a small covered-id set (not just the ids with real records)
  enumerates that set from the SAME real source its write-side gate
  already uses -- never a second, independently-hardcoded id list, and
  never pushed onto the frontend to re-derive.**
  `REQ-SB-68-US-01-T02`'s `agent_schedule_registry.get_job_run_states()`:
  the write side gates run-state tracking structurally
  (`capability_id == "run_capture_now"`, no agent-id check at all), but
  the read side needs to know WHICH covered agent ids to emit an honest
  `"has_run": false` placeholder for when no record exists yet -- sourced
  directly from `skill_registry._MIGRATION_GRANT_SEED["run_capture_now"]`
  (the same real grant-seed source that already, structurally, defines
  "the three covered agents"), not a second hardcoded tuple/list
  anywhere in the new run-state code, and not left for the frontend to
  hold its own copy of the same id list just to detect an absent row.
  Apply this shape whenever a read accessor must show "no data yet" for
  every member of a bounded set the codebase already defines
  authoritatively elsewhere -- enumerate from that source, don't
  re-literal it, and don't defer the enumeration to a downstream
  consumer that has no other reason to know the set.

- **A pipeline node that only forwards a downstream Job's own "success"
  outcome and silently discards every other honest outcome the Job
  already returns is a regression, not a no-op — restore the honest
  fallback at the NODE layer, never re-fabricate a success at the Job
  layer.** Found live 2026-08-17, `BUGFIX-03-US-01-T01` (`BUG-014` gap 1):
  `email_classification.py::summarize_attachment` already returned an
  honest `{"filename", "saved", "summary_error", ...}` dict on every
  non-`dated_entry` path (correct, unchanged), but
  `email_capture_pipeline.py::_summarize_attachment_node` only appended
  to `attachment_entries` when `dated_entry` was present — every
  oversized/unsaved/unsummarizable outcome vanished with no trace, no
  exception, no log. New `_fallback_attachment_entry(result, received)`
  (module-level, placed directly after the node) synthesizes a
  visibly-distinct fallback line — `"{date} — {filename} (not saved —
  {summary_error})"` or, when the file WAS saved but only failed to
  summarize, `"{date} — [{filename}]({relative_link}) (saved but could
  not be summarized — {summary_error})"` — mirroring the wording
  convention `classify_recent_emails` already established
  (`f"- {att['filename']} (not saved — {att['size']} bytes exceeds the
  size cap)"`). Apply this shape whenever a new pipeline/graph node
  wraps an existing Job whose return contract already distinguishes
  success from honest-failure: the node's job is to surface EVERY real
  outcome, not just the happy path.

- **When a save-path primitive shares a filename namespace across
  multiple real-world "events" writing into the SAME parent (a Thread's
  many messages; a recurring series' many occurrences), nest one level
  deeper by the event's own stable identifier rather than adding
  rename/hash-check collision logic.** Applied 2026-08-17,
  `BUGFIX-03-US-01-T02` (`BUG-014` gap 2):
  `vault_writer.py::write_attachments` gained a required
  `message_segment: str` parameter, nesting
  `attachments/<note_slug>/<slug-of-message_segment>/<filename>` instead
  of the old flat `attachments/<note_slug>/<filename>` — two different
  messages in the same Thread sharing an attachment filename (e.g.
  recurring `image001.png` signature images) now save to genuinely
  distinct paths instead of silently overwriting each other. The
  segment's own FULL value (a message's complete `received` timestamp,
  not a day-only date) is what actually closes the collision window — a
  coarser segment just relocates it one level down. Matches this
  codebase's existing "dated sub-entry per attachment" convention
  (`summarize_attachment`'s own `dated_entry` wording) rather than
  inventing a second, divergent collision mechanism.

- **Before retiring/superseding a "deterministic path from a stable key"
  helper for a broader lookup mechanism, grep the WHOLE business layer
  for every real caller of the OLD helper, not just the one call site the
  story/ADR names.** Applied 2026-08-17, `REQ-SB-69-US-01-T06` (`ADR-046`
  Decision 7, `BUG-019`): `ADR-046`'s own Consequences section
  characterized `vault_writer.thread_note_path`/`thread_note_exists` as
  "becoming dead code" once `thread_match_merge` moved to
  `resolve_thread_note_path` — a factually wrong premise. A grep-across-
  `src/backend` (not just the one file the task named) found a second,
  real, live caller: `meeting_classification.py::
  _link_to_thread_by_conversation_id` (`REQ-SB-56-US-01`'s own Link-to-
  Thread PRIMARY strategy), whose own `thread_note_exists(conversation_id)`
  check silently returns `False` for every genuinely-existing Thread
  created after the filename scheme changed — permanently starving the
  primary strategy in favor of the weaker date-proximity fallback, with
  no exception, no log. Fixed directly, same pass (`BUG-019`, mirroring
  `BUG-018`'s own "resolved directly, same day" precedent) — the fix
  itself was a one-line swap to `resolve_thread_note_path(...) is not
  None`, but finding it required a repo-wide grep of the OLD helper's own
  name, not trusting an ADR's own Consequences section as a complete
  caller inventory.

- **Additive human-readable display sibling, never replacing the
  machine-parseable field — the first time this codebase renders a
  human-readable date, so worth naming as the reusable shape.** Applied
  2026-08-17, `REQ-SB-69-US-01-T07` (`ADR-046` Decision 10):
  `vault_writer.format_human_readable_datetime(raw: str) -> str` parses a
  raw, COM-stringified timestamp via `datetime.fromisoformat` (with a
  date-only `strptime` fallback) and renders `"<Mon> <day>, <year>,
  <hour>:<min> <AM/PM>"` (leading zeros stripped from the day and the
  12-hour hour only — minutes stay zero-padded), never raising — a
  genuinely unparseable input is returned unchanged. Written to a NEW,
  separate frontmatter key (`last_message_at_display`) alongside the
  existing machine-parseable field (`last_message_at`, left byte-for-byte
  unchanged), and used at `## Transcript`-entry write time — never a
  replacement of the machine-parseable value anywhere it's already
  consumed programmatically (`meeting_classification.py::
  _date_proximity_gap_days`'s own `last_message_at[:10]` parsing).
  Reuse this exact additive-sibling-field shape (never rename/repurpose an
  already-consumed machine-parseable field) the next time a raw
  timestamp anywhere in this codebase needs a human-readable rendering.

- **A header-scoped, whole-region primitive that owns a fixed position
  (`replace_body_opening_line`) can never safely coexist with an
  insert-if-missing primitive (`insert_body_line_if_missing`) targeting
  that SAME position — reach for a NEW, dedicated `## `-level body
  section (`replace_body_section`) instead of retrofitting an inline
  line into an already-owned region.** Applied 2026-08-17,
  `REQ-SB-69-US-01-T08` (`ADR-046` Decision 9, Context point 6): Thread's
  own body already has `replace_body_opening_line` (`REQ-SB-67-US-01`)
  unconditionally, wholesale-regenerating the pre-first-header region on
  every `thread_match_merge` call. Email's existing inline-wikilink
  primitives (`customer_hub_linking.link_note_to_customer_hub`/
  `people_extraction.link_email_to_person`) insert their own `**Label:**
  [[Stem]]` line via `insert_body_line_if_missing` at that SAME
  pre-first-header position — reusing them for Threads as-is would mean
  `replace_body_opening_line`'s own next call silently erases whatever
  line `insert_body_line_if_missing` had just written, a genuine
  primitive conflict found by direct reading, not assumed. Resolved by
  giving Threads a new, dedicated `## Related` body section instead,
  fully regenerated from scratch via `replace_body_section` on every
  call (never a patch) — the same "regenerate, don't patch" invariant
  `## Summary` already established, extended to a new content class
  (wikilinks). Any future note kind that already owns a
  `replace_body_opening_line`-style fixed region must apply the same
  check before reusing an `insert_*_if_missing` primitive at that
  position — a dedicated `## `-level section is the safe default, not a
  style preference.

- **When one Agent-tier identity gains a second, independently-dispatched
  capability that must never be blocked by (or block) the first, give it
  its OWN dedicated `asyncio.Lock` and a sibling dispatch function
  mirroring the existing one's exact shape — never a flag/branch on the
  existing shared-lock dispatcher.** Applied 2026-08-17,
  `REQ-SB-69-US-01-T04` (`ADR-046` Decision 4): `pull_email` (Outlook-
  touching, stays on the existing shared Outlook-COM `_dispatch_lock`/
  `dispatch_with_shared_lock`) and `process_staged_email` (Outlook-free)
  are two capabilities of the SAME `email-capture-pipeline` Agent-tier
  identity. `process_staged_email` got a second, dedicated
  `_processing_lock` and a new `dispatch_with_dedicated_processing_lock`
  — mirroring `dispatch_with_shared_lock`'s own skip-not-queue/
  `asyncio.to_thread`/run-state-marking/outcome-recording shape exactly,
  never touching the shared lock. This makes "a stalled Pull can't block
  already-staged Process, and vice versa" true BY CONSTRUCTION (no lock
  is ever shared between the two), not by convention/discipline — proven
  live via two controlled, deterministic induced-stall dispatches
  (`0.53s`/`0.01s` completions fully inside a known 15s/58.5s stall
  window on the other side). `_RUN_STATE_TRACKED_CAPABILITY_ID` (a single
  string) widened to a plain tuple of tracked ids for the SAME reason —
  extending shared observability state to a new capability without a
  second, independently-hardcoded id list. Any future Agent that gains a
  second independently-schedulable capability needing this same
  guarantee should reuse this exact dual-lock/sibling-dispatch-function
  shape, not invent a new mechanism.

- **Checking only the DIRECT one-hop import edges is not enough to rule
  out a circular import in this codebase — verify by actually importing
  the new edge from more than one real entry point.** Found live
  2026-08-17, independently by TWO different tasks the same night
  (`REQ-SB-69-US-01-T04` and `T06`): `skill_tools.py -> email_
  classification -> vault_filing_expert -> agent_orchestration -> graph
  -> knowledge_gap_tracking -> knowledge_bootstrap -> skill_registry ->
  skill_tools` is a REAL transitive cycle back into `skill_tools.py`
  through `email_classification.py`'s own OTHER imports — not the direct
  one-hop edge either task's own docstring precedent describes. A new
  top-level import added to `skill_tools.py` that completes this cycle
  can compile and even RUN successfully under one real import order
  (whichever module happens to get imported first in a given process)
  while raising a genuine `ImportError: cannot import name '...' from
  partially initialized module` under a different, equally-real order —
  silently order-dependent, not caught by a single successful test run.
  Verify a "no circular import" claim by importing the new module
  directly first, AND by importing the real app entry point (`app.main`)
  first — the second is what matters for production correctness (real
  `uvicorn` startup order); the first is what actually exercises the
  worst-case order. Fix a confirmed real cycle with a deferred
  (inside-function) import, mirroring `build_knowledge`'s/`propose_
  person_note_update`'s own established precedent — never assumed
  pre-emptively without confirming the risk is real first.

- **Never count a raw `run_*_pipeline()`/`run_capture_*` results list with
  bare `len(results)` as a success count** — this project's own honest
  per-item failure funnel (a failed item returns `{"subject": ..., "error":
  ...}` instead of raising) means `results` mixes successes and failures in
  one list; `len(results)` silently reports failures as successes. Always
  split `filed = [r for r in results if "error" not in r]` / `failed = [r
  for r in results if "error" in r]` and report both. This exact bug class
  was fixed once already (`email_classification.run_capture_and_record_
  completion`'s `history_text`, 2026-08-17 morning) and reintroduced hours
  later in a brand-new sibling capability (`skill_tools.process_staged_
  email`, `BUG-020`, 2026-08-17 night) — any NEW handler wrapping one of
  these pipeline functions must apply this same filter from the start, not
  copy the older, still-present `len(results)` shape some other call sites
  (`skill_tools.run_capture_now`, `agents_router._execute_action`) still
  carry pre-existing.

- **When a story adds a NEW frontmatter key that a later pass reads back
  (`frontmatter.get("new_key")`), always test against a real note written
  BEFORE that key existed** — `.get()` returning `None` for an absent key
  is easy to miss in review because it never raises; it just silently
  produces a `None` that can flow all the way into a user-visible artifact
  (`BUG-021`: a legacy Thread's missing `thread_name` key produced a real,
  literal `"None-2026-08-17-<hash>.md"` filename on its next update, found
  live the same night the feature shipped). Backfill the missing value
  once, using the same top-up-only-if-missing convention this codebase
  already uses for other baseline keys, rather than assuming every note
  the new code will ever touch was written after the schema changed.

- **`create_okf_directory_baseline`/`create_customer_directory_baseline`/
  `create_project_directory_baseline` return a STRINGIFIED path dict (their
  own documented contract, `{key: str(value) ...}`) — never pass that
  return value straight into `replace_body_section`/`read_body_section`/
  `read_note`/`upsert_frontmatter_key`, all of which require a real `Path`
  object (`.read_text`/`.write_text`). Use `okf_directory_paths`/
  `customer_directory_paths`/`project_directory_paths` directly instead
  (same resolver `synthesize_project` itself composes internally) whenever
  real `Path` objects are needed for a follow-up read/write — this exact
  `AttributeError: 'str' object has no attribute 'read_text'` was hit live
  writing `REQ-SB-57-US-01-T01`'s own verification script. Same class of
  gotcha as the already-documented `create_thread_note_baseline` case
  above, now confirmed for the whole OKF directory family too.

- **Manual live-vault verification against a shared Customer/Project
  directory can legitimately race a DIFFERENT concurrent coder session
  also verifying against the same real Customer — this is safe, not test
  pollution, when every write in the shared path is a full-rebuild
  (`replace_body_section`, never a patch).** Found live,
  `REQ-SB-57-US-01-T02`: mid-verification, real Customer `Core42`'s own
  `## Glimpse` picked up a `"REQ-SB-57-T03 Verification Project"` rollup
  line this task's own script never created — a concurrent `T03` coder
  session's own live fixture, cascaded in through the very
  `synthesize_project` → `synthesize_customer` call chain this task just
  wired. Do not attempt to clean up / assert byte-for-byte on content you
  did not yourself write; scope cleanup and the "pre-existing content
  unchanged" check strictly to the fixtures/sections your OWN task's own
  verification created, and restore only what your own before-snapshot
  actually captured.

- **A slug built by concatenating an already-`_slugify`-truncated value
  (e.g. another slug, itself already clamped to `_slugify`'s own default
  80-char `max_len`) with further real content (e.g. a filename) can
  silently exceed 80 chars again and lose the newly-appended part
  entirely on the SECOND truncation — always derive a NEW, short,
  purpose-built disambiguator (a `hash8` prefix, mirroring `meeting_note_
  filename_stem`'s own convention) from the ORIGINAL, un-truncated value
  instead of chaining onto an already-slugified string.** Found live,
  `REQ-SB-71-US-02-T07`: `f"{attachment_path.parent.name}-{filename}"`
  (where `attachment_path.parent.name` was itself already an 80-char-
  truncated `_slugify(message_id)` result) silently dropped the real
  filename on the second `_slugify` call inside `write_file_companion`,
  and would have collided two different attachments on the same message
  onto one companion note. Fixed to `f"{hash8(message_id)}-{filename}"`.

- **When a locked AC's own real-world precondition genuinely does not
  exist in current live data (confirmed by an exhaustive, disclosed
  direct scan, not assumed), verify via a scoped, disclosed monkeypatch
  of ONLY the external, uncontrollable data-source boundary, called
  through the REAL endpoint (e.g. Starlette's `TestClient` against the
  real FastAPI route) — never a raw internal-function bypass of the
  capability itself. Always fully clean up every fixture/engineered
  artifact afterward and confirm the cleanup (a vault-wide name-pattern
  scan returning zero matches) before considering the task done.** Found
  live, `REQ-SB-71-US-03-T02`/`T03` — real Outlook calendar has zero
  real no-email-attendee instances across a 240-day scan and the real
  vault currently carries zero notes with a real `customer` frontmatter
  value; `outlook_com.list_calendar_events` was the ONLY boundary
  monkeypatched, extending `SPRINT-050`'s own "scoped monkeypatch of an
  external dependency" precedent (there: Compass's model factory) to a
  second, different external boundary.

- **One shared `<ChatMessageText text={string} />` component for every
  real chat-message render call site, not per-file inline
  `<ReactMarkdown>` calls** — `BUGFIX-04-US-01`/`ADR-050`, mirrors this
  project's own "generic-primitive-first, kind-specific-wrapper-second"
  precedent (`SPRINT-048`) applied to a component instead of a shared
  function. `src/frontend/src/components/` is the first cross-feature
  shared-component location in this codebase (siblings live under
  `features/<name>/`) — decomposer/coder latitude, not a new architectural
  layer.

- **Before trusting ANY live-endpoint verification against the running
  backend, confirm the server process actually started AFTER your own
  code changes landed on disk** (check its real `CreationDate`/PID
  ancestry, not just that something answers on the port) — a
  long-running `uvicorn` process started without `--reload` never
  re-reads edited source files; calling a real HTTP endpoint against a
  stale process silently exercises the OLD code while looking like a
  genuine live test. Found live, `BUGFIX-05-US-01-T02`: the first live-
  verification attempt ran against a pre-fix server process and briefly
  reproduced the exact bug (`BUG-026`'s own orphaning failure) the task
  existed to verify was fixed, against the real vault — self-detected (the
  OLD response wording was the tell), fully repaired from a pre-test
  backup, then correctly re-verified after confirming the freshly-
  restarted process was running the corrected code. When in doubt, prove
  which code is loaded with one cheap, safe, no-op real dispatch before
  running the real test.

- **A migration that changes a Thread's own filesystem SHAPE and a
  synthesis step that regenerates a Thread's own body CONTENT are
  logically separate concerns, but chaining them in the SAME pipeline
  tick can silently lose real content if the shape-migration step doesn't
  also carry the pre-migration content forward into whatever the content
  step reads from.** Found live, `BUGFIX-05-US-01-T04`/`ESC-056`:
  `migrate_flat_thread_to_directory` (`ADR-052`) correctly, deliberately
  touches only filesystem shape, creating an empty `messages/` directory;
  `synthesize_thread` (`ADR-051`, unmodified) regenerates `## Summary`
  purely from `messages/` — so a freshly-migrated flat Thread's real,
  substantive pre-migration `## Summary` is silently overwritten and lost
  the FIRST time the two are chained together, even though each function
  is individually correct against its own, narrower contract. When one
  fix touches a shared primitive several other real functions compose,
  re-verify the FULL composed, real-world call chain end-to-end — not just
  each function's own isolated unit behavior — before treating the
  primitive fix as complete.

- **Job-level failure isolation around a real external call is a
  DIFFERENT concern from that call's own per-call retry, and a new Job
  can need the former even when its own detection call correctly mirrors
  a sibling's "no retry" contract.** Found live, `REQ-SB-74-US-01-T05`:
  `compass_client.detect_customer_for_thread` deliberately carries no
  retry loop (`ADR-055` Decision 2, correctly mirroring `classify_task`'s
  own established contract) — but `propose_customer_backfill()`'s own
  JOB-level loop had no per-Thread failure isolation around that call, so
  one real, transient Compass connection drop among 100+ sequential real
  calls in the same pass discarded every OTHER Thread's already-good
  classification and crashed the whole HTTP request. Fixed additively (a
  new `"failed"` return key, per-item `try/except` + `continue`) —
  mirrors this codebase's own already-established `backfill_files`/
  `detect_mentioned_companies_for_thread` honest-degradation pattern.
  When a new Job's own real, live-run scale (dozens-to-hundreds of
  sequential external calls in one pass) is materially larger than the
  sibling function whose retry contract it mirrors, add this Job-level
  isolation even when the ADR correctly decided the call itself needs no
  retry — one does not substitute for the other.

## Constraints

- **`outlook_com.py::_is_inline_attachment`'s `PR_ATTACH_CONTENT_ID`
  check can false-positive on a genuine, non-inline attachment.** Found
  live 2026-08-17, `BUGFIX-03-US-01-T01`'s own live-diagnostic sub-step:
  the historical "Presight Agent Academy Demo" message's real PDF
  attachment (`260816 Agentic academy v06_shared.pdf`, ~4.96 MB, well
  under the 20 MB cap, a genuine by-value COM attachment — not a
  OneDrive/SharePoint link) has Outlook's own `PR_ATTACH_CONTENT_ID`
  MAPI property set to a real MIME-style Content-ID, distinct in shape
  from the message's 13 truly-inline signature/logo images (whose own
  content-ids literally echo their own filenames) — so
  `_is_inline_attachment`'s first, highest-priority check returned
  `True` and `_extract_attachments` silently dropped the PDF before it
  ever reached the pipeline. Do not assume every attachment with a
  non-empty `PR_ATTACH_CONTENT_ID` is truly inline — some sending mail
  systems assign a Content-ID to every MIME part of a message, not just
  ones actually referenced inline in the body. **Fixed same day
  (`BUG-017`, direct fix, 2026-08-17):** `_is_inline_attachment` now
  requires the Content-ID to genuinely appear as a `cid:` reference in
  the message's own `HTMLBody`, not just be present as a property.

- **A Windows Outlook COM automation client only gets TEMPORARY,
  time-boxed access via the "Object Model Guard" security prompt ("A
  program is trying to access...") unless the client is explicitly
  trusted — once that window lapses, automated calls into sensitive
  parts of the object model (sender/recipient addresses, MAPI property
  reads like `PR_ATTACH_CONTENT_ID`) can silently BLOCK/HANG waiting on
  a security dialog nobody is watching for, rather than failing
  cleanly.** Confirmed live, 2026-08-17: the operator had granted
  10-minute access that morning; hours later, in the same running
  session, the email-capture pipeline hung for 20+ minutes with
  near-zero CPU (blocked on I/O, not computing) before a manual process
  restart was needed — consistent with a stalled COM call, not a
  Compass-side issue (Compass itself, tested in isolation via raw HTTP
  during the same window, responded normally). Restarting the backend
  after a fresh PC restart re-triggered the real access-request dialog
  on the very first COM call (the app-start capture trigger) —
  confirms this is the real, load-bearing mechanism behind at least
  some of that night's intermittent stalls, previously misattributed
  to Compass API contention alone. **No code fix applied** — this is
  an OS/Outlook Trust Center configuration matter (permanently trusting
  the automation client, or registering as a recognized security
  provider), outside what this app's own code can control, and outside
  what Claude may configure directly (prohibited: modifying system/
  security settings) — the operator must configure this themselves if
  they want to eliminate the recurring prompt permanently. Until then,
  expect this exact class of stall to recur roughly every time the
  access grant lapses during a long-running/overnight session.

- **When the operator asks Claude to DO something in the running app
  (create/rename/move/delete a real entity — a Section, an Agent, a
  vault note, etc.), always go through the app's own real surface —
  the actual HTTP API endpoint, or the UI — never a throwaway script
  that calls the business layer directly, even when a real endpoint
  already exists for it.** Reason, stated directly by the operator after
  watching this happen: "When I ask you to do something in the App you
  don't do it by coding, you tell me we don't have the API in the
  Backend for it — this will help a lot with the mess we have in
  here." Concrete example of the mistake: `POST /sections` /
  `PATCH /sections/{id}` / `DELETE /sections/{id}` (`sections_router.py`)
  already existed, but a Section rename/create/delete was done via a
  direct Python script calling `section_registry.py` functions —
  bypassing the real request path, harder to audit, and inconsistent
  with what the actual app/UI can reproduce. How to apply: before acting
  on an "in-app" request, check whether a real endpoint exists (grep the
  relevant `app/api/*_router.py`). If yes, call that real endpoint (or
  drive the real UI). If no, say so plainly and ask whether to build it
  (through the normal `/spec`→`/plan-tasks`→...→`/implement-sprint`
  pipeline) or do something else — never quietly reach into the business
  layer as a workaround. This does not apply to genuine backend
  debugging/diagnosis (e.g. reading state to investigate a bug) — only to
  actions that CHANGE real app state on the operator's behalf.
- **Prefer a prompt (a Compass call) over hand-written code for any
  classification/extraction/judgment-shaped step, when a prompt can do the
  job.** Reason, stated directly by the operator while SPRINT-048 was
  running: Compass is a free API for them, so LLM-based steps carry no
  marginal cost, and prompt-based logic is easier to steer/extend/re-scope
  later than hardcoded branching — matches `ADR-041`'s own "designing for a
  long run, not a one-time build" framing for the Job/Pipeline model.
  Applies going forward to every new Job in `REQ-SB-55`/`56`/`57` (Classify,
  Thread-Match/Merge, Route-to-Project, Detect-Recurring-Pattern, Summarize-
  Attachment, and the Project/Customer synthesizers) — default to a Compass
  prompt for the actual judgment call, and reserve hand-written code for the
  parts that are genuinely mechanical (deterministic path construction,
  frontmatter I/O, the `replace_body_section`-style file primitives). Not a
  constraint on THIS sprint's own tasks (`SPRINT-048` is pure data-model
  plumbing, no classification/judgment steps in scope) — recorded now so it
  governs `REQ-SB-55` onward once those parked stories are picked back up.
  Also reconfirmed the same day, no new decision needed: agents already run
  on a LangGraph pipeline (`ADR-041`), and a capture Job (e.g. Email Fetch)
  can already be dispatched either on-demand or via the existing per-agent
  Scheduler (`REQ-SB-47-US-01`/`ADR-037`) — both are standing, already-built
  capabilities, not new requirements.
- **Every `capture_scheduler.py` backend restart unconditionally
  re-triggers a real app-start capture tick (`REQ-SB-05`/`ADR-005` point
  2) — never assume a mid-session restart to load new code is free.** On a
  vault with a genuine unprocessed backlog this can run for several real
  minutes (Outlook COM + Compass calls across email/meeting/todo capture)
  and, per `ADR-037`, now acquires the SAME shared dispatch lock any
  concurrently-issued verification call also needs — budget for this
  explicitly when a task's own verification plan requires more than one
  server restart in one session. Found live, `REQ-SB-47-US-01-T02`/`T05`.
- **`vault_writer.py`'s own real frontmatter serializer
  (`_format_frontmatter_value`/`_parse_frontmatter_value`) cannot
  round-trip a list-of-dicts value.** It only recognizes a quoted string
  or a list of quoted strings — writing `{"some_key": [{"a": 1}, {"b": 2}]}`
  via `write_note`/`upsert_frontmatter_key` produces an invalid,
  unparseable Python-dict-repr line that silently reads back as `[]`,
  losing the data with no error. Any future frontmatter field that needs a
  structured list-of-objects shape must either (a) JSON-encode the whole
  value as a single string (the interim convention `cockpit/people.py`
  established, `REQ-SB-43-US-01-T03`) or (b) extend the parser itself
  first. Found live, `REQ-SB-43-US-01-T03`.
- **`.second-brain/` state files (any `agent_*.json`,
  `agents_registry.json`, etc.) live at the real, `.env`-configured
  `VAULT_PATH`, never at a path relative to `src/backend`** —
  `src/backend/.second-brain` does not exist. Any task's own "delete
  leftover state files first" verification step means the real, external
  vault directory (read `VAULT_PATH` from `src/backend/.env`), not a
  guessed in-repo path. Found live, `SPRINT-034`.
- **Every node on `app/business/agent_orchestration/graph.py`'s shared
  compiled graph, and every function in its own call chain
  (`run_agent_conversation` and anything it calls), must be genuinely
  `async def` and reached via `.ainvoke()`/`await` — never a sync
  function bridged with `asyncio.run()`.** This graph is invoked from
  `agents_router.py::chat`, itself now `async def`, on FastAPI's own
  event loop directly. A `asyncio.run()` call anywhere in this chain
  creates a second, nested event loop that can self-connect-fail back
  into this same single-process server (confirmed live 2026-08-12 — see
  `## Decisions`). `REQ-SB-20` (Hub routing), `REQ-SB-26` (memory — the
  two nodes it already added are correctly sync-only, no I/O), and
  `REQ-SB-27` (skill invocation) are all expected to extend this same
  graph — any new node that makes its own real I/O call (an MCP tool
  call, a Provider call, a future skill invocation) must be `async def`.
- Hermes's own internal architecture (not Second Brain's to build or track,
  per the dependency constraint just below): agents are categorized by Type
  (`Expert`, `Worker`, `Hub`, more to come) and belong to a Section/
  Department; LLM access is multi-provider (currently Compass backed by
  GPT-5, with Compass+GPT-OSS and Anthropic planned). Recorded 2026-08-10
  as context only — if a future requirement needs Second Brain to track
  which agent/section/provider handled something, that's new scope, not
  implied by this note.
- Hermes (external MCP-based multi-channel communication tool) is an integration
  point, not something this project builds — treat it as a dependency with its own
  interface, not code to implement here.
- Hermes integration-sourcing precedence: for any external system Second Brain
  needs to reach (starting with Outlook mail/calendar), prefer a native Hermes
  skill or MCP server if one already exists; otherwise wrap an existing working
  implementation as a Hermes skill rather than building fresh. Concretely for
  Outlook — no Graph API (company-blocked, no Azure AD app registration
  possible) — wrap agentic-map's existing `outlook_com` skill (COM automation
  against locally-running desktop Outlook; see agentic-map's ADR-0018) as a
  Hermes skill, don't reimplement it. Same single-laptop-with-Outlook-desktop-
  running constraint carries over.
- No admin rights on the development host – both backend and frontend toolchains
  must be usable without a system installer. Python runs via the `py` launcher
  (3.14.6 is what's actually present, not 3.12 as originally assumed — see
  ADR-001); Node.js is a portable zip extracted to `tools/node/`, never a system
  install (see ADR-002).
- Vault note filenames must never be built from date+subject alone — two
  Outlook items can share both (a resend, a duplicate share notification),
  and a plain `date-subject.md` scheme silently overwrites one with the
  other. Always include a uniqueness slice (e.g. the source EntryID) in the
  filename stem. Found live in the email-classification POC 2026-08-10,
  fixed in `app/business/email_classification.py`.
- Known data-quality wrinkle (not yet fixed): the `type`/`kind` value for
  regular email notes is inconsistently `"email"` (singular, from an earlier
  Compass response) vs `"Emails"` (plural, current) across existing notes —
  same wrinkle shows up in their `kind/email` vs `kind/emails` tags. Harmless
  today (both are valid, dynamically-discovered kinds) but will read as two
  different kinds until reconciled; don't silently merge them without the
  operator's say-so, since agentic-map's own precedent for this kind of
  taxonomy drift is a real, judged decision, not a mechanical fix.
- Backend code must respect the `api → business → data_access` layer boundary
  (ADR-003) — a router calling `data_access` directly, or `business` doing its
  own filesystem/HTTP I/O, is a scope violation, not a style nitpick.
- The vault has two top-level roots, `Personal/` and `Work/` — everything
  Second Brain writes (email classification and onward) goes under `Work/`,
  never `Personal/`. Concretely: `email_classification.py` writes to
  `Work/<Kind>/` (e.g. `Work/Emails/`), not `Personal/...`.
- Customer is never a folder level — only frontmatter (`customer:`) and a
  `customer/<slug>` tag. Per *Beyond the Second Brain*'s "folders are the
  enemy of thinking," an email's customer relevance is multidimensional and
  shouldn't force one physical location; reclassifying is a tag edit, not a
  file move. `Kind` (Emails/Files/Notifications/...) remains a folder level
  since it's a genuinely stable, single-home property of a note.
- Since `REQ-SB-07-US-01-T04` wired `capture_scheduler.lifespan` into
  `app/main.py`'s `FastAPI(...)`, **every backend dev-server start/restart
  fires a real capture run** (live Outlook fetch → Compass classify → vault
  write) via the unconditional app-start trigger — `uvicorn --reload`
  triggers this on every reload, not just the first start. Do not restart
  the dev server repeatedly while working in `src/backend` without
  expecting real side effects (Outlook COM calls, Compass API calls, and
  vault writes against the live `.env`-configured vault).
- **Standing design rule (operator directive, 2026-08-11): every note-type
  schema must define both tags AND wikilinks, always** — never ship a
  schema with one but not the other. Tags alone (no links) leave Obsidian's
  graph view showing disconnected dots, exactly the bug REQ-SB-14 fixed for
  Customer-tagged content; links alone (no tags) lose tag-pane/search
  discoverability independent of physical location. This is a mandatory
  design-time checklist item for every future note type (People, Meetings,
  Industry, and anything after), not a one-off fix — check both before
  calling a schema resolved. Applied immediately to People (see the
  Decisions entry above): Person notes wikilink to their Company's Customer
  hub note when the company matches an existing customer (reusing
  REQ-SB-14's existing hub-note mechanism, no new concept introduced); when
  the company isn't a known customer, there is no hub note yet to link to,
  so the tag alone stands honestly until one exists — that is a real
  absence of a link target, not an overlooked link.
- Port `8000` (uvicorn's default) is not reliably free on this development
  host — an unrelated `agentic-map` process (`services.control_plane`) may
  already be bound to it. Before starting the Second Brain dev server for
  live verification, check with `Get-NetTCPConnection -LocalPort 8000` /
  `Get-CimInstance Win32_Process` and use an alternate port (e.g. `--port
  8001`) if occupied, rather than assuming a bind failure means Second
  Brain's own server is already running. Found live 2026-08-11 verifying
  `REQ-SB-10-US-01-T04`. **Extended 2026-08-11 (`SPRINT-009`):** with
  multiple sprints running concurrently, even the "alternate" port `8001`
  can already be occupied by a *different* concurrent sprint's own live
  backend dev server, not just `agentic-map`'s process — always check the
  specific port you're about to bind to fresh (don't assume `8001` is
  safe just because `8000` is the documented conflict), and pick the next
  free one (`8002`, ...) rather than guessing.
- Every browser-originated `fetch` call from `src/frontend` to
  `src/backend` requires `fastapi.middleware.cors.CORSMiddleware` on the
  FastAPI app — they run as separate processes/origins in every
  deployment shape this architecture has established. No CORS middleware
  existed until `REQ-SB-12-US-02-T03` (`SPRINT-009`) added it, because no
  earlier task had ever made a real fetch call (`REQ-SB-12-US-01`'s
  `api/client.ts` went unused). Before writing the *first* real fetch call
  in any future frontend-integration task, confirm `CORSMiddleware` is
  already registered in `app/main.py` — don't assume a correct endpoint
  response (verified via direct HTTP call) means the browser can actually
  reach it.
- **Never run a process-kill command by image name (e.g. `taskkill /IM
  <name>.exe /F /T`) in this environment — always target the specific
  PID already identified** (e.g. via `Get-NetTCPConnection`/
  `Get-CimInstance Win32_Process`). Multiple coder sessions can run
  concurrently, each launching their own same-named helper processes
  (e.g. a headless Chrome instance for CDP-based verification) — killing
  by image name risks terminating another concurrent session's own
  verification process, or a real user application window. Found live
  2026-08-11, `SPRINT-009` — `taskkill /IM chrome.exe /F /T` was run in
  error while cleaning up this sprint's own headless-Chrome instance; no
  harm was confirmed, but the specific-PID-only rule is now standing.
- `vault_writer._slugify()` (used for **filenames**) and `vault_writer.
  tag_slug()` (used for **tags**) normalize differently — do not assume
  one implies the other. `_slugify()` only strips Windows-illegal path
  characters (`\/:*?"<>|`); it does NOT collapse dots, `@`, or spaces into
  hyphens. `tag_slug()` does the fuller lowercase+hyphenate-non-alphanumeric
  normalization. Consequence: a filename built from an email address (e.g.
  `person_note_path()`/`create_person_note_baseline()`, REQ-SB-10) keeps
  the literal dots/`@` — `verify.t01@example.com.md`, not
  `verify-t01-example-com.md` — valid on Windows, just not hyphenated.
  Found live 2026-08-11 verifying `REQ-SB-10-US-01-T01`, where the task's
  own Tests-section narrative had assumed the hyphenated form; the actual
  code (matching the task's own `## Files to Modify` spec verbatim) does
  not hyphenate, and no locked AC depended on the literal filename string.
- **Standing constraint (operator directive, 2026-08-11 — tightens the
  tags-and-wikilinks rule above): every note that *references* another
  vault entity must carry an actual `[[wikilink]]` to that entity's own
  note — not just an identifying frontmatter field, and not just
  triggering that entity's note to be created as a side effect.** Found
  live 2026-08-11 as `BUG-001`: Email notes create/update the sender's
  Person note via `people_extraction.ensure_person_note_for_captured_email`,
  but the Email note itself never links back to it — `sender`/
  `sender_email` are plain frontmatter strings, no `[[PersonName]]`
  anywhere in the body. Person notes render as disconnected graph nodes
  relative to every Email that actually mentions them, despite the
  standing tags-and-wikilinks rule already existing when People was
  designed — the rule checked the outbound direction (Person→Company)
  but not the inbound one (Email→Person). **Applies to every future
  entity relationship, checked in both directions, before calling any
  schema resolved:** does the *referencing* note link out, not just does
  the *referenced* note get created/exist. A gap found after the fact is
  forward work (a `BUGFIX-NN` story per `BUGS.md`'s rules), including a
  one-time backfill retrofit over already-captured notes — not just a
  forward-only code fix — mirroring the retrofit pattern `REQ-SB-14`/
  `REQ-SB-10` already established.
- **Outlook `EntryID` is NOT guaranteed unique per occurrence of a
  recurring meeting under `items.IncludeRecurrences = True`** — confirmed
  live 2026-08-11 verifying `REQ-SB-08-US-01-T03`/`T05` (Scenario 9): a
  real recurring meeting's 3 distinct occurrences (different dates) all
  returned the exact same, full `EntryID` string, not just a coincidental
  8-char-suffix match. This falsifies ADR-008's own stated assumption that
  each expanded occurrence carries its own EntryID — a risk ADR-008's
  Consequences section had already honestly flagged as unverified and
  pre-authorized a superseding-ADR response for, "not a silent workaround,"
  if ever observed. Today's Meeting notes are all still correct only
  because `meeting_note_filename_stem` also incorporates the event's date,
  and today's real recurring occurrences happen to fall on different
  dates — a future recurring meeting with two occurrences on the *same*
  date would produce an identical filename for both and silently merge two
  distinct meetings into one note. Open, not resolved: `ESCALATIONS.md` →
  `ESC-002`, `REVIEW-QUEUE.md` pointer on `REQ-SB-08-US-01`. Do not treat
  Outlook `EntryID` as a safe universal per-occurrence dedup key for any
  future recurring-calendar-item work without first checking this finding.
- A "generic scan" migration keyed on frontmatter-field equality only
  finds notes that carry that exact field — it silently misses notes that
  reference the same entity by tag plus inline wikilink alone, with no
  matching frontmatter field. Found live 2026-08-11 verifying
  `REQ-SB-16-US-01-T04`: `migrate_customer_to_partner`'s scan (matching
  `frontmatter.get("customer") == customer_name`, per `ADR-009`) correctly
  catches every Email/Newsletter/Notification note (they carry a real
  `customer:` field) but structurally cannot reach the 5 real Microsoft
  Person notes — Person notes have never carried a `customer:` frontmatter
  field (only a `company/<slug>` tag plus an inline
  `**Customer:** [[Hub]]` body wikilink, written by a different mechanism,
  `customer_hub_linking.link_note_to_customer_hub`). Before designing any
  future rename/retag/migration scan, enumerate every mechanism that
  writes a reference to the entity being migrated (frontmatter field, tag,
  and inline wikilink each independently), not just the one the target
  note-kind happens to use — a scan tuned to one referencing shape will
  silently skip notes using another. Resolved for `REQ-SB-16-US-01-T04` via
  `ADR-012` (unions the frontmatter-equality signal with an inline-body-
  wikilink-presence signal, both read from the same existing per-note
  `read_note()` call); `ESCALATIONS.md` → `ESC-001` closed.
- `vault_writer.insert_body_line_if_missing` computes its insertion point
  as a **fixed byte offset** from the frontmatter's closing `---`
  (`body_start = end + 6`), which assumes `write_note()`'s own
  `"---\n\n<body>"` convention (exactly one blank line between frontmatter
  and body). A note whose body was ever hand-edited outside that
  convention (no blank line after the closing `---`) causes every
  subsequent insertion via this primitive to land at the same fixed
  offset regardless of what has already been inserted — typically
  mid-word, silently, with no error — compounding further with each call
  rather than being a one-off. Found live 2026-08-11 verifying
  `REQ-SB-16-US-01-T04`: one real note
  (`Work/People/karimlouis@microsoft.com.md`, structurally malformed
  since an old `REQ-SB-10-US-01-T04` verification pass) was corrupted
  further by this session's own, otherwise-correct `partner_hub_linking.
  link_note_to_partner_hub` call. Manually repaired directly; the
  underlying primitive is not yet fixed — this is a standing risk for any
  other note that was ever hand-edited outside the standard convention,
  not limited to this one instance. See `ESCALATIONS.md` → `ESC-003`
  (`Open`) — recommended for a formal `/bug` capture and a proper
  `BUGFIX-NN-US-01` fix (e.g. compute the true body-start position
  dynamically rather than assuming a fixed offset).
- **Extended further 2026-08-11 (`REQ-SB-13-US-01`/`SPRINT-010`):** with
  4+ concurrent sessions in flight, ports 8000 **through 8002** were all
  simultaneously occupied (the known `agentic-map` process plus two
  concurrent Second Brain verification sessions) — this pass needed 8003.
  Scan a small range (`8000..8010`) rather than assuming any single
  fallback port is free. The frontend's default port (5173) can be
  similarly occupied by a concurrent session's own `npm run dev`; Vite
  auto-increments (e.g. to 5174) but the backend's `CORSMiddleware`
  `allow_origins` list must be extended to match whatever port Vite
  actually lands on, or every browser-originated fetch fails silently
  from a CORS rejection despite the endpoint itself working correctly
  when called directly.
- A single chat-triggered action invocation can produce **two**
  `run_event` history entries, not one, when the invoked handler already
  self-reports its own completion via a dedicated hook (e.g.
  `email_classification.run_capture_and_record_completion`'s own
  `T04`-added history append) *and* the generic router wrapper
  (`agents_router._invoke_action`'s caller) also appends its own
  `run_event` after the handler returns. Found live 2026-08-11,
  `REQ-SB-13-US-01-T05`/`SPRINT-010` — harmless against every locked AC
  (the unified-history scenario only requires entries to appear together,
  not exactly-once per event) but worth knowing before wiring the next
  real action handler that already self-reports via its own completion
  hook, to decide deliberately whether the doubling is acceptable or the
  router's generic append should become conditional.
- `provider_registry.create_provider` (unlike `section_registry.
  create_section`) has no same-slug-collision guard — calling it twice
  with the same `name` appends two Provider entries sharing one `id`,
  rather than returning the existing entry. Found live 2026-08-11,
  `REQ-SB-19-US-01-T06`/`SPRINT-012` (a test script's own accidental
  double-POST, not a real usage path) — implemented exactly per the
  decomposer's own literal task code, not yet fixed. No locked AC depends
  on idempotent-on-name creation. Worth mirroring
  `section_registry.create_section`'s existing-entry check the next time
  `provider_registry.py` is touched, especially if Provider creation is
  ever exposed to a retry-prone client path.
- **Outlook `AppointmentItem.GlobalAppointmentID` is NOT confirmed unique
  per occurrence of a recurring meeting on this Outlook installation
  either** — live-falsified 2026-08-12 verifying `REQ-SB-08-US-01-T06`
  (`SPRINT-017`), the very fix that adopted it (`ADR-013`) specifically to
  replace `EntryID` after `EntryID` failed this same test (see the
  `EntryID` constraint entry above, `ESC-002`). The native COM property
  itself (`item.GlobalAppointmentID`, read the same direct-attribute way
  as `item.EntryID`) returned the **exact same, full value** across all 3
  real occurrences of two separate real recurring series ("Weekly Forecast
  l Strategic Clients" and "Weekly Forecast l Major Clients"). The
  documented `PropertyAccessor`/DASL fallback for this property
  (`PidLidGlobalObjectId`'s Extended MAPI tag) also **errors on every
  occurrence** on this installation ("property... is unknown or cannot be
  found") — not a usable disambiguator either. Practical consequence: the
  same-calendar-date recurring-occurrence collision risk `ADR-013` was
  built to close is **not actually closed** — do not treat
  `GlobalAppointmentID` as a safe, verified-unique per-occurrence dedup
  key for any future recurring-calendar-item work on this Outlook
  installation without first re-testing it live. Open, not resolved:
  `ESCALATIONS.md` → `ESC-012`, `REVIEW-QUEUE.md` pointer on
  `REQ-SB-08-US-01-T06` / `SPRINT-017`. `T06` itself is `Blocked`, not
  `Done` — its build (the SHA-256-hash filename-suffix mechanism and the
  legacy-`EntryID`-path coexistence/no-duplicate check) is otherwise
  correct and left in place, since neither of those parts depends on the
  falsified uniqueness premise and both are independently verified
  regression-safe.
- A blocked (in-use) Remove/Delete button in this codebase's Settings
  cards (`SectionsCard.tsx`, `ProvidersCard.tsx`) is genuinely React-
  Fiber-`disabled` — a real user cannot click it, and a test driver's
  native `.click()` on it silently no-ops (same finding as `MEMORY.md`'s
  existing React-Fiber-props-direct-invoke pattern, re-confirmed live
  2026-08-11, `REQ-SB-19-US-01-T05`/`SPRINT-012`). To exercise the
  blocked-removal error path in live verification, invoke the button's
  handler directly off its React Fiber props, not a simulated click.
- **Mounting an MCP `FastMCP` server (`mcp.server.fastmcp.FastMCP`) as a
  Starlette sub-application via `app.mount(path, mcp_server.
  streamable_http_app())` needs two corrections beyond the bare mount
  call, both found live 2026-08-12 (`REQ-SB-25-US-01-T05`/`SPRINT-014`):
  (1) `FastMCP`'s own `streamable_http_path` constructor kwarg defaults to
  `"/mcp"` — mounting at `app.mount("/mcp", ...)` without overriding it
  nests the real, reachable route at `/mcp/mcp`, not `/mcp` (confirmed via
  a real `GET /mcp` → `404`); pass `streamable_http_path="/"` to the
  `FastMCP(...)` constructor so the externally-reachable path matches the
  mount path exactly. (2) The returned sub-app carries its own `lifespan`
  (`session_manager.run()`, which the SDK's Streamable HTTP transport
  needs to initialize its task group) — **FastAPI/Starlette does not
  cascade lifespan startup into a `Mount()`-ed sub-application
  automatically**; every real request 500'd with `RuntimeError: Task
  group is not initialized. Make sure to use run().` until the parent
  app's own `lifespan` was rewritten to explicitly enter
  `mcp_server.session_manager.run()` (via `AsyncExitStack`) alongside
  whatever lifespan the app already had. Apply both corrections any time
  a `FastMCP` server is mounted as a sub-application in this codebase
  (`REQ-SB-27`'s future skills-as-tools reuse this same mount).
- **Port `8000` and `8001` were both live-occupied and effectively
  unmanageable during `REQ-SB-25-US-01`/`SPRINT-014`'s own live
  verification (2026-08-12), extending the standing port-conflict
  constraint above.** `8000` was the already-known `agentic-map`
  `services.control_plane` process. `8001` — this project's own usual
  `tools/run-backend.cmd`/`.claude/launch.json` convention — was found
  bound to a process this coder session could not identify or terminate
  via any available process-management tool (`Get-Process`/
  `Get-CimInstance`/`tasklist` each reported "not found" for the exact PID
  `netstat`/`Get-NetTCPConnection` attributed the port to, even though
  that port kept answering real, coherent HTTP requests reflecting this
  session's own code) — most plausibly a process-visibility boundary
  specific to a coder session's own tool sandbox (e.g. an externally-
  managed preview/dev-server harness), not a second genuine Second Brain
  instance. Verification proceeded on port `8002` instead, self-started
  and self-restarted directly by the coder session (not relying on
  `--reload`, which was also found live to not reliably pick up file
  edits in this same sandboxed environment — explicit kill-and-restart
  was used instead for every code change needing to go live). If a future
  session hits an unresponsive or unmanageable port-8001 process again,
  don't assume it's safe to keep retrying against it — move to the next
  free port in the small-range-scan convention and self-manage the
  process directly.
- **`provider_registry`'s stored `endpoint` field (the FULL Compass
  completions URL, `.../v1/chat/completions`) is not directly usable as
  `langchain_openai.ChatOpenAI`'s `base_url` kwarg** — `ChatOpenAI` wraps
  the OpenAI Python SDK client, which itself appends `/chat/completions`
  onto whatever `base_url` it's given (it expects a root URL, `.../v1`),
  unlike `app/data_access/compass_client.py`'s own plain
  `httpx.post(settings.compass_base_url, ...)` call, which posts directly
  to the full URL with no path appended. Passing `provider["endpoint"]`
  straight into `ChatOpenAI(base_url=...)` double-appends the suffix and
  404s. Found live 2026-08-12, `REQ-SB-25-US-01-T07`/`SPRINT-014` — fixed
  in `agent_orchestration/model_factory.py` via
  `provider["endpoint"].removesuffix("/chat/completions")`. Any future
  `ChatOpenAI`/OpenAI-SDK-based consumer of `provider_registry` must do
  the same strip; `provider_registry.py`'s own stored shape was
  deliberately left unchanged (`compass_client.py`'s existing call path
  still needs the full URL as-is).
- **Tools loaded via `langchain_mcp_adapters` (`MultiServerMCPClient.
  get_tools()`) are async-only** — calling `.invoke(args)` on one raises
  `"StructuredTool does not support sync invocation."`; a synchronous
  LangGraph node (or any other sync caller) must use
  `asyncio.run(tool.ainvoke(args))` (or run inside an already-async
  context and `await tool.ainvoke(args)` directly) instead. Found live
  2026-08-12, `REQ-SB-25-US-01-T07`/`SPRINT-014` — a real tool-call loop
  otherwise never converges (the same tool call repeats every round,
  each one silently failing with that error string fed back to the model
  as if it were the tool's own result) until a round ceiling trips it.
- **A per-turn "too many tool calls" round guard must count only the
  CURRENT turn's own model↔tool round-trips, never every `AIMessage` in
  the full replayed message list** — the latter also counts every prior
  real conversation turn's own `"chat_agent"` history entry (each mapped
  to a plain, tool_calls-less `AIMessage` by `state.py`'s own
  `history_entries_to_messages`), so the count grows with conversation
  length regardless of this turn's own tool activity, eventually
  false-tripping the guard on a perfectly ordinary later turn. Found live
  2026-08-12, `REQ-SB-25-US-01-T08`/`SPRINT-014` verifying `AC-03`: a
  second, unrelated turn on an agent that already had a few real prior
  exchanges immediately hit the false trip. Fixed in `agent_orchestration/
  graph.py` via a backward walk from the end of `messages` that stops at
  the first message marking the true start of the current turn (a
  `HumanMessage`, a plain `AIMessage`, or a `SystemMessage`) — any future
  per-turn round/step guard over a full replayed-history message list
  needs the same current-turn-only scoping, not a naive full-list count.
- **`provider_registry.has_real_client(provider_id)` only ever returns
  `True` for the hardcoded id `"compass"`** (`_REAL_CLIENT_PROVIDER_IDS =
  {"compass"}`, `REQ-SB-19-US-01`) — a newly created Provider (via `POST
  /providers`) is structurally never able to reach a real network call
  through any code path gated by this check (e.g.
  `agent_orchestration.model_factory.resolve_agent_model`,
  `agents_router.py::_invoke_action`), regardless of how genuinely
  reachable or unreachable its own endpoint is; it always short-circuits
  to the "not available" branch first. Found live 2026-08-12,
  `REQ-SB-25-US-01-T08`/`SPRINT-014` verifying `AC-05`: a throwaway
  Provider pointed at a guaranteed-dead port never produced a real
  connection-failure message, only the unavailability one. **To test a
  genuine real-Provider-call-failure path, temporarily repoint the real
  `"compass"` Provider's own `endpoint` (`PATCH /providers/compass`) at an
  unreachable address, trigger the call, then restore it immediately** —
  not a new throwaway Provider. Since `"compass"` is shared by every
  agent, keep this window as short as possible and always confirm the
  real endpoint is restored afterward.
- **Do not trust an Outlook Object Model property's documented
  "guaranteed unique" claim without live-testing it against a real
  recurring calendar series on the actual installation in use, and do not
  assume a second Outlook-native identity field is a safe fallback just
  because the first one failed.** Confirmed twice on this Outlook
  installation: `EntryID` (`ESC-002`, `ADR-008`→`ADR-013`) and then
  `AppointmentItem.GlobalAppointmentID` itself, its documented
  "guaranteed-unique-per-occurrence identifier" replacement (`ESC-012`,
  `ADR-013`→`ADR-019`) — both returned the identical value across every
  real occurrence of the same recurring series on this machine, despite
  Outlook's own Object Model documentation. The durable fix
  (`ADR-019`) does not trust any Outlook-provided identity field at all —
  it derives uniqueness structurally, from the occurrence's own precise
  start timestamp (two distinct occurrences cannot begin at the same
  instant), which needs no live re-verification against this or any other
  installation to trust. Prefer a structural guarantee over an
  Outlook-documented empirical one for any future recurring-calendar-item
  dedup/identity work in this codebase.
- **When a live-verification session resumes work on a real, scheduler-
  driven pipeline after a gap (a `Blocked` task left its prior code in
  place, not reverted), re-inventory the real vault state fresh before
  trusting a prior session's own "N real notes exist" count — an
  unattended scheduled capture run can genuinely change it in between
  sessions.** Found live 2026-08-12, `REQ-SB-08-US-01-T06`/`SPRINT-017`'s
  second build pass: the vault held 40 real Meeting notes at this
  session's start, not the 39 both this task's own spec and `ADR-019`'s
  own Consequences section assumed (written during the *prior* session,
  before an unattended scheduled capture run created one more under the
  then-still-live old code — `.second-brain/last_capture_run.json`'s own
  `finished_at` timestamp confirmed the gap). This is not a defect in
  either the task file or the ADR at the time each was written — it is a
  live production system that keeps running on its own hourly schedule
  between coder sessions (`ADR-005`), so any "as of right now" count in a
  task/ADR file is a snapshot, not a standing guarantee. Re-count/re-scan
  the real vault at the start of any live-verification session rather
  than trusting a prior session's own recorded count, especially for any
  task whose own Constraints depend on an exact "zero"/"N" claim about
  real data.
- **A raw `LastWriteTime`-before/after comparison via a CSV export/import
  round-trip can produce false "changed" positives from date-format
  drift alone (12-hour `AM/PM` vs. 24-hour), not a real file mutation —
  always re-parse both sides to real `DateTime` objects (or compare
  within a tolerance) before concluding a file was touched.** Found live
  2026-08-12, `REQ-SB-08-US-01-T06`/`SPRINT-017`: an initial before/after
  `LastWriteTime` check (CSV-exported "before" snapshot, string-compared
  against a freshly-queried "after" list) flagged all 40 pre-existing
  Meeting notes as "changed," which would have wrongly suggested every
  one had been rewritten; re-running the comparison with both sides
  parsed to `[datetime]`/`DateTime` and a small tolerance showed zero
  real changes. Caught before being reported as a finding — a reminder to
  sanity-check a surprising "everything changed" result against a
  simpler mechanism (format drift) before trusting it as evidence of real
  mutation.
- **`httpx.get(url)`/`httpx.post(url)` (the module-level shortcut
  functions) do NOT follow HTTP redirects by default
  (`follow_redirects=False`) — a redirecting endpoint's real "alive"
  status code is only reached with `follow_redirects=True` explicitly
  passed.** Found live 2026-08-12, `REQ-SB-31-US-01-T02`/`SPRINT-019`:
  the shared FastMCP mount's own `GET /mcp` (no trailing slash) actually
  307-redirects to `GET /mcp/` before answering its documented `406 Not
  Acceptable` "alive" signal — a bare `httpx.get(_MCP_MOUNT_URL,
  timeout=3.0)` call (the task's own literal code sample) stopped at the
  `307` and reported the mount unreachable even when it was genuinely
  healthy, a real false-negative that would have broken the System
  Health view's own "everything healthy" state. A redirect-following
  client (a browser, PowerShell's `Invoke-WebRequest`, `curl`'s own
  default) masks this — which is almost certainly why the story's own
  "confirmed live" `406` finding didn't record the discrepancy at the
  time. Before writing any future `httpx.get()`/`httpx.post()` call
  against an endpoint whose exact redirect behavior hasn't been directly
  confirmed with `httpx` itself, pass `follow_redirects=True` explicitly
  or verify the endpoint never redirects.
- **A dev port can stay bound to a PID that neither `Get-Process` nor
  `taskkill` can find** — an OS-level stale-listener condition distinct
  from the already-documented "surviving `--reload` worker" antipattern
  (that one has a real, findable `--multiprocessing-fork` child process;
  this one has no findable process at all, on either query). Found live
  2026-08-12, `REQ-SB-21-US-01`/`SPRINT-021`: port 8001 stayed `Listen`-
  bound to PID `5648` throughout an entire verification session even
  after `Stop-Process -Force`/`taskkill /F` both reported that PID as
  not found. Not root-caused; worked around by verifying against a
  second instance on a different port instead of losing time fighting
  an unkillable handle. If it recurs, worth a deeper OS-level
  investigation rather than routing around it again.
  **Recurred, 2026-08-12, `REQ-SB-36-US-01`/`SPRINT-022`, one sprint
  later, with the literal SAME PID (`5648`)** — confirmed via five
  independent mechanisms this time (`Get-NetTCPConnection`/`Get-Process`/
  `tasklist`/`wmic process where...`/.NET `[System.Diagnostics.Process]::
  GetProcessById`), all agreeing the PID is not found, while the port
  keeps answering real HTTP traffic with stale (pre-that-session's-own-
  code-changes) responses. The identical PID surviving across sessions/
  sprints rules out "a normal orphaned process, still technically alive
  somewhere" as the explanation — this is very likely a genuinely stale
  kernel-level TCP listener/table entry (or a virtualization/NAT-layer
  artifact specific to this host) that ordinary user-mode process tools
  cannot see or clear at all, not a process any tool will ever
  successfully target. `netstat -anob` (which can sometimes resolve what
  `Get-NetTCPConnection` cannot) requires admin rights, unavailable on
  this host. **Standing guidance updated: do not spend further time
  trying to kill port `8001`'s own stuck listener with user-mode tooling
  — start a fresh instance on an alternate port immediately** (accepting
  that anything hardcoded to `127.0.0.1:8001`, e.g. `mcp_client.py`'s own
  MCP-loopback URL, will still reach the stale listener until a human
  with elevated access clears it or reboots the host).
- **A model-generated tag alone does not make an entity discoverable
  through a vault-derived lookup that scans frontmatter, not tags** —
  `vault_writer.list_known_customers()`/`list_known_partners()` read the
  `customer:`/`partner:` FRONTMATTER field, never the `tags` list; a note
  written with only `{"tags": ["customer/<slug>"]}` looks correctly
  tagged but is structurally invisible to those lookups. Whenever a new
  write path introduces a `customer`/`partner`/similarly-multidimensional
  attribute via tags, also set the matching frontmatter field (and reuse
  `customer_hub_linking`/`partner_hub_linking`'s existing granular
  primitives for the hub note + `[[wikilink]]`, never a new mechanism).
  Found live 2026-08-12, `REQ-SB-35-US-01-T02`/`SPRINT-023`.
- **A model prompt instruction phrased "return X only if the content is
  about a KNOWN Y" silently means "skip X for a genuinely new Y" to the
  model, even when the surrounding schema clearly allows a new value** —
  found live 2026-08-12, `REQ-SB-35-US-01-T02`/`SPRINT-023`: a real
  Compass completion reliably tagged `customer/<new-slug>` for a
  brand-new customer, but left the paired `referenced_customer` field
  `null` under a first-draft prompt that only asked for "the exact known
  customer name... or null" — the word "known" was read as scoping the
  whole field to already-known entities, not just describing the reuse
  case. Fixed by making the field's presence conditional on the tag
  alone ("REQUIRED whenever a `customer/<slug>` tag is set, known or new
  alike") and re-verifying live against a genuinely-new-entity case
  specifically, not just an already-known one. When a prompt asks a
  model to conditionally return a value, test both the "already known"
  and "genuinely new" branches independently before trusting either.
- **A Provider's persisted `credential` in `.second-brain/
  agent_providers.json` does NOT auto-resync from `.env`/`Settings` once
  the file has already been seeded — editing `.env` alone is not enough
  to pick up a new/corrected credential.** `provider_registry._load_state()`
  only calls `_seed_state()` (which reads `app_settings.*` fresh) when
  the state file doesn't exist yet; once it exists, every subsequent read
  returns the value baked in at first-seed time forever, regardless of
  later `.env` edits. Found live twice: `REQ-SB-36-US-01-T03`'s own build
  (documented as a required manual "delete the file first" step in its
  own Tests) and again 2026-08-13 during this story's real-credential
  re-verification pass (a real Anthropic `401 invalid x-api-key` persisted
  even after `.env` was fixed, traced to the stale placeholder still
  living in the persisted JSON). Whenever a Provider's real `.env`-sourced
  credential changes after first boot, delete `.second-brain/
  agent_providers.json` to force a clean re-seed (safe — it also resets
  every agent's Provider assignment to the default `"compass"`; confirm
  that's acceptable, or re-apply any non-default assignments after).
  Skill grants (`.second-brain/agent_skills.json`) are a separate file,
  unaffected by this reset.
- **Killing the real Outlook desktop process does not produce a genuine
  "Outlook unreachable" state on this host — Windows COM silently
  auto-relaunches Outlook.exe the next time any code calls
  `win32com.client.Dispatch("Outlook.Application")`.** Confirmed live
  2026-08-13, `REQ-SB-11-US-01-T02`/`T04`/`SPRINT-027`: `Stop-Process
  outlook -Force` followed immediately by a real `check_reachable()`
  call still returned `{"reachable": True}`, and Outlook's own process
  `StartTime` had advanced to a moment after the kill — proving COM
  relaunched it transparently. Any future task whose own Tests block
  names "physically close Outlook" as the way to induce an unreachable
  state on THIS host must substitute the established in-process-
  monkeypatch-of-`_connect_namespace` technique instead (see Patterns).
- **Anthropic's Messages API, even with the server-side web-search tool
  enabled, essentially always returns some non-empty explanatory text —
  including an honest "I can't find/won't fabricate that" refusal — so a
  `found`/"has a result" check based purely on "is the text response
  non-empty" cannot distinguish a real, grounded result from an honest
  no-results refusal; only the presence of real `sources`/citations does.**
  `app/data_access/anthropic_client.py::web_search`'s own `{"found": False,
  "summary": "", "sources": []}` branch (triggered only when the response
  has zero text) appears to be effectively unreachable in practice with
  the current model/tool combination — the real honest-empty shape
  observed live is `{"found": True, "summary": <honest refusal text>,
  "sources": []}`. Confirmed live 2026-08-13, `REQ-SB-36-US-01`
  re-verification, against two queries engineered to have no real answer.
  Not a fabrication defect (the text itself never invents a plausible
  answer), but any future caller of this function that branches on
  `found` alone (not also checking `sources`) will misclassify an honest
  refusal as a "real result."
- **`BUG-011`'s `_slugify` 80-char-truncation defect is confirmed to
  affect more than Email/Notification notes — Task notes too, with a
  worse consequence.** Found live 2026-08-13, `REQ-SB-09-US-01-T03`/
  `SPRINT-028` (`ESCALATIONS.md` → `ESC-028`): three real Outlook Tasks
  sharing one 72-character subject produced three correctly-distinct
  `task_note_index.json` entries, but the shared filename stem exceeded
  `_slugify`'s 80-char cap, silently truncating away each one's
  disambiguating entry-id suffix — since Task notes share ONE flat
  `Work/Tasks/` subfolder (no Compass-classified `kind` split, unlike
  Email/Notification), this causes a literal same-path file OVERWRITE
  (real content loss), not just `BUG-011`'s own documented cross-
  subfolder index-invisibility case. Any future note type that also
  shares one flat subfolder (no `kind` split) carries this same,
  worse-than-`BUG-011`'s-original-finding risk until the underlying
  `_slugify`/stem-construction fix lands.
- **Outlook's own "no due date set" sentinel for `TaskItem.DueDate`
  renders as `"4501-01-01 00:00:00+00:00"` on this installation (an
  ISO-shaped `pywintypes.Time` `str()` rendering), not the US-locale-
  shaped `"1/1/4501"` initially guessed.** Confirmed live 2026-08-13,
  `REQ-SB-09-US-01-T01`/`SPRINT-028`. Setting `TaskItem.DueDate` back to
  "no date" via COM only accepts the literal string `"1/1/4501"` as a
  write value, though it reads back in the ISO-shaped form above — worth
  knowing for any future code that both reads and writes this field.
- **`start "Title" cmd /k "path with spaces"` needs exactly ONE pair of
  quotes around the path — doubling them (`""path""`) silently breaks
  it.** Found 2026-08-13 building `start.bat` (repo root, one-click
  backend+frontend launcher). Since the repo root itself has a space
  ("Second Brain"), a doubled-quote path gets cmd-parsed as an unquoted,
  space-split token list; the window still opens (its `conhost.exe`
  child exists) but the intended command never actually runs inside it —
  no uvicorn/vite process, no visible error, just an idle prompt. This is
  the same failure *symptom* as the earlier documented `Start-Process
  -ArgumentList` array-form bug (window opens, no real child process) but
  a different, batch-specific root cause — check for it the same way:
  confirm a real child process exists under the spawned `cmd.exe`, not
  just that the window/process itself exists.
- **This sandboxed tool-execution shell cannot spawn a real interactive
  Windows console window at all** (confirmed 2026-08-13: even a bare
  `start notepad.exe` produces no running `notepad` process, and `start
  cmd /k ...` leaves only a `conhost.exe` child with nothing inside it
  actually executing). A `start`/`Start-Process`-based launcher script
  cannot be fully live-verified from this shell — only its non-GUI logic
  (path resolution, `.env` existence checks) can be. Final verification
  of any such script requires the user to actually run it from their own
  real desktop session.
- **A `/implement-sprint` coder run in an isolated git worktree is missing
  two whole classes of file the main checkout has, and both must be
  synced in before any live verification is trustworthy.** Found live
  2026-08-13, `SPRINT-030`/`REQ-SB-39-US-01-T01`. (1) `src/backend/.env`
  and `src/backend/.venv` are both gitignored, never committed — copy
  `.env` directly from the main checkout (same trusted local machine) and
  build a fresh `.venv` via `pip install -r requirements.txt` in the
  worktree (a clean install cost ~a few minutes here, no build-toolchain
  issues) rather than assuming either exists. (2) **Any file that is
  merely `M`/`??` (uncommitted) in the main checkout's own `git status` —
  not just `.env`/`.venv` — is ALSO absent from a worktree built off the
  last real commit,** including task/story/sprint files never yet
  committed, and ADRs/`MEMORY.md`/`CHANGELOG.md`/`BACKLOG.md`/
  `REVIEW-QUEUE.md`/`ESCALATIONS.md` edits still sitting uncommitted in
  the main tree. Before trusting a worktree's copy of any artefact this
  pipeline reads or appends to, diff it against the main checkout's real
  current content (a plain filesystem `cp`, not a git operation, is fine
  — this isolation is about git operations, not filesystem reads) and
  sync it in if it's stale. Backend business/API source files that were
  genuinely clean (`git status` clean) in the main checkout matched the
  worktree's git-checked-out state exactly, with zero drift — the risk is
  specifically real for files the main checkout's own `git status` already
  flags as dirty.
- **`tools/node/` (the portable Node.js toolchain) is ALSO gitignored
  (`ADR-002`) and therefore ALSO absent from a fresh git worktree** — a
  `SPRINT-030`/`REQ-SB-39-US-01-T09` coder run isolated in
  `.claude/worktrees/agent-a0ff2ea4ae24d5621` found no Node.js anywhere
  reachable from inside that worktree and concluded (incorrectly, as a
  host-wide claim) that "Node.js is not installed anywhere on this host."
  **Corrected same-day, from the main checkout directly:** `tools/node/
  node.exe` is real and present on this host — the frontend build/type
  check IS runnable here, just not from an isolated worktree that never
  had `tools/node/` (also gitignored, same root cause as point 1 above)
  copied in. Do not trust a worktree-run coder's "X is not installed on
  this host" claim without confirming from the main checkout — restate it
  as "X was not reachable from this isolated worktree" instead. This
  correction also means `REQ-SB-39-US-01-T09`'s frontend change was never
  actually build/type-verified — see the `SPRINT-030` retro follow-up for
  the real verification run against the main checkout.
- **The backend dev server's `uvicorn --reload` file watcher does not
  reliably pick up new/edited `.py` files in this environment** — found
  live 2026-08-15 adding `demo_taxonomy_router.py` and
  `agent_visual_registry.py`: `GET /demo/agents` and the new `icon`/
  `color` fields on `GET /agents/{id}` both kept 404ing / silently
  missing from the response after editing source and waiting several
  seconds, even though a standalone `python -c "import ..."` proved the
  code itself was correct. Root cause each time was a stale, already-
  running backend process the reload watcher never actually noticed the
  change against — not a code bug. **Fix: after any backend `.py` edit,
  don't trust `--reload` — explicitly stop the tracked server
  (`preview_stop` with its `serverId`) and start it again
  (`preview_start {name: "second-brain-backend"}`); calling
  `preview_start` again on an already-running server just reuses it
  (`reused: true`), it does not restart it.** Confirm the fix landed by
  hitting the endpoint directly (`Invoke-RestMethod`) before trusting any
  further browser-level verification. Remember the adjacent, already-
  documented constraint above this one too: every real restart re-triggers
  `capture_scheduler.py`'s own app-start capture tick.
- **The same `--reload` unreliability documented just above for
  `src/backend` also applies to `src/demo-backend`** — found live
  2026-08-16 adding a `description` field to `main.py`'s
  `_agent_summary()`: `WatchFiles` logged a real "Reloading..." line for
  an earlier `sample_data.py` edit the same session (so the watcher
  clearly CAN fire), but a subsequent `main.py` edit produced no such
  log line and the running server kept serving the OLD response shape
  (`description` missing from `GET /agents`) for several direct
  `curl`-verified checks after the edit landed on disk. Explicit
  `preview_stop` + `preview_start {name: "second-brain-demo-backend"}`
  fixed it immediately. Don't trust `--reload` for ANY backend process
  in this repo (real or demo) — always stop/start explicitly after a
  `.py` edit and confirm via a direct HTTP call before trusting further
  browser-level verification.
- **This repo's root `src/frontend/tsconfig.json` has `"files": []` and
  only `references` (`tsconfig.app.json`/`tsconfig.node.json`) — running
  plain `tsc --noEmit -p .` against it type-checks NOTHING (no error,
  no output, looks identical to "passed clean").** Found live 2026-08-16:
  a genuine `ReferenceError: hoveredAgentPoint is not defined` runtime
  crash in `SectionDrilldown.tsx` (a variable's declaration accidentally
  dropped in an edit) shipped straight to the browser — hovering any
  Agent in the Section View unmounted the whole page — despite `tsc
  --noEmit -p .` reporting clean immediately after that exact edit. Vite
  itself never type-checks (esbuild/SWC strips types without checking),
  so this was the ONLY verification step that could have caught it, and
  it was silently a no-op the entire session. **Use `tsc -b --force`
  (or `tsc -b` incrementally) instead — this actually builds/checks the
  referenced projects and would have caught this as a `TS2304: Cannot
  find name` compile error before it ever reached the browser.** Note:
  `tsc -b` on this repo currently reports 6 pre-existing `TS7053`
  ("implicitly has an 'any' type") warnings from the established
  `style['--custom-prop' as string] = value` CSS-custom-property
  pattern used throughout `agents-map.css`'s own React components
  (present even in files never touched this session, e.g.
  `SectionHub.tsx`) — treat that specific warning shape as an accepted,
  known baseline, not a new regression, when it reappears unchanged
  after a fresh `tsc -b` run.
- **When a coder session has no `preview_stop`/`preview_start` tools
  available (found live 2026-08-16, `REQ-SB-65-US-01-T02`), a
  `tools/run-backend.cmd`-launched dev server is unreliable to
  stop/restart via plain OS process management, and the mismatch is
  worse than the already-documented `--reload`-doesn't-reload constraint
  above.** The `uvicorn.exe --reload` child process's own PID is
  invisible to `Get-Process`/`tasklist`/`Get-CimInstance Win32_Process`
  filtered by that PID, and `taskkill /F /PID <that-pid>` reports "process
  not found" even though the port keeps answering real, live (but stale)
  FastAPI responses throughout. Root cause: `run-backend.cmd` launches via
  a `cmd.exe /c` wrapper — kill THAT wrapper's PID instead (find it via
  `Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match
  'run-backend' }`), with `taskkill /F /T` (the `/T` tree flag) so its
  child survives-the-parent orphaned worker is also killed — a single
  `Stop-Process -Force` on the wrapper alone was NOT enough, the orphaned
  worker child kept serving stale responses for several more attempts
  after that. Confirm the restart actually landed by checking `GET
  /openapi.json` for the specific new route, not just that the port
  answers SOME response — a stale process answers real, valid-looking
  JSON for every OTHER route the whole time, which reads as "it's
  working" unless you check the ONE new route specifically.
- **`layoutAgents.ts`'s own already-shipped `is_background_agent` filter
  (`REQ-SB-51-US-01`) excludes an agent from the Agents Map ring
  entirely — worth checking BEFORE designing any future feature that
  splices/derives new `AgentSummary`-shaped entries from an existing
  agent and expects them to render on the ring.** Found live 2026-08-16,
  `REQ-SB-65-US-01-T02`: `email-capture-pipeline` (the real pipeline
  agent) is itself `is_background_agent: true` and therefore already
  renders NOTHING on the Agents Map today (moved to the separate
  `CrawlersPage.tsx` a prior sprint). A design that inherits
  `is_background_agent` verbatim from such an agent onto derived entries
  (Jobs, sub-tasks, etc.) silently makes every derived entry invisible
  too — `layoutAgents()`'s own `addressableAgents = agents.filter(agent
  => !isBackgroundAgent(agent))` runs BEFORE `agentsBySection` is built,
  so this isn't a rendering nuance, it's a hard exclusion upstream of
  everything else in that function. Check an agent's real
  `is_background_agent` value (`GET /agents`) before assuming "it renders
  as one node today" from a story/PRD's own prose.
- `vault_writer.replace_body_opening_line` (`REQ-SB-67-US-01-T01`) locates
  its region start via the SAME fixed `body_start = end + 6` byte-offset
  convention `insert_body_line_if_missing`/`insert_tags_line` already use
  — and therefore inherits the SAME already-documented risk class as the
  `body_start = end + 6` entry above (`ESC-003`, `Open`): a note whose
  body was ever hand-edited outside `write_note()`'s own exactly-one-
  blank-line-after-`---` convention would make this primitive land its
  region-start computation at the wrong offset too, silently. Not a new
  risk introduced by this task — the task's own spec explicitly directs
  mirroring this exact, already-established convention — but every
  Thread note this new primitive is actually called against (`T02`/`T03`,
  via `create_thread_note_baseline`/`write_note`) is written by this
  same codebase's own convention-following code, so no currently-known
  malformed Thread note is at risk today. Future callers extending this
  primitive to a different note kind should confirm that kind's notes
  are never hand-edited outside the standard convention first.
- **A story-level Constraint recorded in a `Done` story's own text is
  reversible by a NEW story — it is not the same weight as an Accepted
  ADR's own Decision, and reversing it never requires a new ADR.**
  `REQ-SB-55-US-01`'s own `thread_match_merge` Job carried a documented
  Constraint, "this Job never makes a second Compass call" — but
  `ADR-043`'s own seven numbered Decision points never asserted that as
  an architectural rule themselves; it was `REQ-SB-55-US-01`'s own
  story-level scoping choice only. `REQ-SB-67-US-01-T02` (2026-08-17)
  reversed it directly — `thread_match_merge` now makes exactly ONE new
  real `compass_client.summarize_content` call per invocation, added via
  a NEW story rather than any edit to the `Done` `REQ-SB-55-US-01`
  (`Implementation/Pipeline.md` hard rule 1, specs are append-only) — the
  architect pass confirmed no ADR needed touching. Before treating any
  story's own documented Constraint as permanent/unchangeable, check
  whether it's actually an ADR Decision (needs a new/amended ADR to
  reverse) or just that story's own scoping text (reversible by a new
  story, same append-only mechanism used here).
- **Never spin up a second full `uvicorn app.main:app` instance against a
  `VAULT_PATH`-overridden scratch vault for manual verification** —
  `app/main.py`'s own `lifespan` unconditionally starts
  `capture_scheduler`'s background tick, which polls the REAL configured
  Outlook mailbox on a timer regardless of which `VAULT_PATH` the process
  was started with. Discovered live during `REQ-SB-67-US-01-T03`
  (2026-08-17): a scratch-vault verification server left running for
  ~10 minutes pulled several real Outlook conversations into the scratch
  vault in the background (real Compass calls, real Customer-hub notes
  created), unrelated to the test data under verification. No real vault
  or real backend data was affected (the real, already-running production
  backend on its own port/`VAULT_PATH` was untouched), but this wasted
  real Compass calls and produced confusing stray files in the scratch
  vault. For any future scratch-vault manual verification: call the
  target business/Job function directly in-process (`python -c` / a
  throwaway script importing the module, as `T01`/`T02` already did) —
  never start a second full app instance via `uvicorn`/`TestClient`
  unless the scheduler itself is the thing under test, in which case
  explicitly disable/mock `capture_scheduler`'s tick first.

- **`POST /agents/email-capture-pipeline/actions/run_capture_now` runs
  fully synchronously inside the single-threaded asyncio event loop —
  while it's running, the ENTIRE backend stops responding to every other
  request, not just this one.** Discovered live 2026-08-17: manually
  triggering it (to check why the vault only had 2 real Threads) blocked
  `GET /agents` and every other endpoint for several minutes; a plain
  `curl` to an unrelated route returned no response at all until the
  capture run finished. Root cause: `_execute_action` (the sync handler
  path `run_capture_now` uses, per `agents_router.py`'s own
  `_ACTION_HANDLERS` dispatch) calls `handler()` directly with no
  thread-pool offload, so any real, slow work inside it (Outlook COM
  scan, per-message Compass calls) blocks the whole event loop.
  **Correction, 2026-08-17 (caught by REQ-SB-68's own `/spec` pass via
  direct code reading — this entry originally claimed otherwise,
  wrongly):** the scheduled/automatic hourly runs
  (`capture_scheduler.py::run_capture_if_idle`) do NOT hit this same
  bug — that function already wraps the identical underlying pipeline
  call in `asyncio.to_thread(...)`, a deliberate 2026-08-14 bugfix
  (see its own inline comment, and `BUGS.md`) applied after an earlier
  version of this exact class of bug once froze all HTTP traffic at
  startup. Only the MANUAL action-dispatch path never received that
  same fix — this is a real gap specific to `run_capture_now`'s manual
  trigger, not a general characteristic of every capture code path.
  **Further correction, `/plan-tasks` architect pass, 2026-08-17
  (`ADR-045`):** the manual blocking call site named above
  (`_execute_action`) was itself wrong — `_execute_action`/
  `_ACTION_HANDLERS` are confirmed dead code for both their entries
  (every real caller branches away to the `skill_tools.SKILLS` path
  first); the REAL manual dispatch path was `agents_router.py::
  trigger_action`/`chat` → `_invoke_capability` → `skill_registry.
  invoke_skill` → `_dispatch_skill` → `skill_tools.run_capture_now` →
  `email_classification.run_capture_and_record_completion`, fully
  synchronous end-to-end, no thread offload anywhere in that chain.
  **CLOSED, `REQ-SB-68-US-01-T01`, 2026-08-17:** `_invoke_capability`
  is now `async def` and routes `run_capture_now` through
  `agent_schedule_registry.dispatch_with_shared_lock` (already
  `asyncio.to_thread`-wrapped, `ADR-037`) instead of calling
  `skill_registry.invoke_skill` directly — closing this gap for both
  real manual-trigger surfaces (the REST action button and the chat
  keyword match). Verified live against the real running backend: a
  genuinely in-flight manual `run_capture_now` no longer blocks a
  concurrent `GET /agents` (sustained over 250+ concurrent probes
  across two real, multi-minute in-flight capture windows, zero
  failures/slow responses). This Constraint no longer applies to any
  current real trigger source — scheduled, manual REST, and manual
  chat are all non-blocking as of this fix.

- **`email-capture-pipeline`'s scheduled runs (`capture_scheduler.py`)
  were already running correctly, roughly hourly, the whole time —
  before assuming a pipeline was never run at scale, check its own
  `GET /agents/{id}/history` first.** A low real Thread count (2, plus
  a stray leftover test note that inflated the visible count to 3) was
  initially mis-read as "the pipeline has never been run broadly" — the
  real explanation, confirmed via `history`, is that the scheduler has
  been firing continuously since `2026-08-16 14:50` and has correctly
  found 0 new emails on every run since the first two real Threads were
  captured. A manually-triggered extra run (2026-08-17) confirmed the
  same — 0 new emails, not a missed-capture bug. The inbox was already
  fully caught up; the low count was simply the honest, correct number.

- **Before trusting a live "does this request block the event loop"
  verification against an already-running `uvicorn --reload` dev
  server, confirm the live worker process's own start time postdates
  your code edit — do not assume `--reload`'s file-watcher caught the
  change.** Discovered live, `REQ-SB-68-US-01-T01` (2026-08-17): an
  already-running backend on port 8001 did not restart after
  `agents_router.py`/`agent_schedule_registry.py` were edited (confirmed
  via `Get-CimInstance Win32_Process`'s own `CreationDate` predating the
  edit), so an initial concurrency probe against it reproduced the OLD,
  pre-fix blocking bug — momentarily indistinguishable from a real
  regression in the just-shipped fix. Always cross-check the serving
  process's own start time (`Get-CimInstance Win32_Process -Filter
  "ProcessId=<pid>" | Select CreationDate` / `netstat -ano` to find the
  PID) against the edit's own timestamp before treating a live-blocking
  test result as evidence about the CURRENT code; when in doubt, kill
  the process and start a fresh one (`uvicorn app.main:app --port
  <free-port>`, no `--reload`) for the specific verification run.

- **FIXED, 2026-08-17 (`REQ-SB-68-US-01-T03` resume, `ESC-042`) —
  `provider_registry.py`'s persisted `agent_providers.json` `"assignments"`
  map now self-heals on every read: `_load_state()` prunes any assignment
  key whose agent id is no longer in `agent_registry.list_agents()`,
  symmetric with that same function's existing add-missing-assignment
  loop.** Originally discovered live, `REQ-SB-68-US-01-T03` (2026-08-17):
  `agent_registry.py`'s `"email-capture"` seed id was renamed to
  `"email-capture-pipeline"` by the already-`Done`
  `REQ-SB-55-US-01-T08`/`ADR-043` point 6, but `_load_state()` at the time
  only ever added a missing assignment for a currently-known agent id —
  it never pruned one for an id that no longer existed after a rename.
  The orphaned `"email-capture": "compass"` key sat silently in
  `.second-brain/agent_providers.json` with no consumer until
  `system_health.py::_providers_with_agent_names()` (`REQ-SB-31-US-01`,
  already `Done`) started calling `agent_registry.get_agent(agent_id)["name"]`
  for every assigned id with no `None`-guard, crashing `GET /system-health`
  with a real `HTTP 500` for an unrelated, unbounded amount of time before
  it was noticed. **Now closed by construction, not just for this one id:**
  any future agent-id rename self-heals the next time `_load_state()` runs
  — no other consumer needs its own defensive guard against this specific
  defect class. Live-verified: the stale key was confirmed present in
  `agent_providers.json`, then confirmed pruned automatically on the next
  `GET /system-health` call, with the endpoint returning a real `200`
  afterward. Root-cause write-up and live-verification evidence:
  `ESCALATIONS.md` → `ESC-042` (`Status: Resolved`).

- **`meeting-capture`/`todo-capture`'s own `run_capture_now` on-demand
  dispatch (manual REST button, chat, or a real scheduled tick) always
  returns an honest `{"available": False, "message": "This skill is not
  yet available -- no real handler has been built for it."}` -- only
  `email-capture-pipeline`'s is real.** `skill_tools.py::run_capture_now`
  branches on `agent_id == "email-capture-pipeline"` specifically (lines
  242-261); the other two covered jobs' own real classification logic
  exists but is wired to the background scheduler tick only, never this
  on-demand path (a deliberate scope boundary, not a bug --
  `REQ-SB-39-US-02`/`ADR-029` point 5's own migration explicitly
  preserved this real/honest-unavailable split, and `REQ-SB-68-US-01` did
  not change it). Confirmed live, `REQ-SB-68-US-01-T04` (2026-08-17):
  dispatching either job's `run_capture_now` on demand always produces a
  genuine, real `last_outcome: "error"` run-state record in under 20ms --
  useful, not a bug to chase, but means neither job can produce a genuine
  multi-minute "currently running with growing elapsed duration" live
  test case; only `email-capture-pipeline` can. Any future test of the
  Scheduling view's running/duration states must use
  `email-capture-pipeline`; any future test of its honest-failure
  rendering can use either `meeting-capture` or `todo-capture` for free,
  with zero induction/monkeypatching needed.

- **`app/business/cockpit/attachments.py::_attachments_dir` now assumes a
  STALE, flat save-path convention for `classify_recent_emails`-sourced
  email attachments — a real, live regression, not yet fixed.** Found
  2026-08-17, `BUGFIX-03-US-01-T02`: that function hardcodes
  `Work/Emails/attachments/<email_note_stem>/<filename>` (flat, no
  per-message segment), justified by its own docstring's claim of being
  "byte-identical to `write_attachments`' own `note_slug`." As of `T02`,
  `write_attachments` requires `message_segment`, and
  `classify_recent_emails`'s own call site now passes
  `message_segment=email["id"]`, nesting one level deeper — so any
  attachment captured through the still-live `/poc/classify-emails` path
  AFTER this fix is silently invisible to Cockpit's
  `list_attachments`/`hand_off_attachment_to_chat` (empty/not-found, no
  error, no log). Already-saved historical attachments at the old flat
  path are unaffected. Left unfixed (outside `T02`'s own `## Files to
  Modify`) — tracked at `ESCALATIONS.md` → `ESC-043` (`Status: Open`) and
  `REVIEW-QUEUE.md`, a `/bug` capture recommended. Any future change to
  `write_attachments`'s own save-path convention must re-check
  `cockpit/attachments.py` for the same class of drift — it is a real,
  live consumer of that convention that does not call `write_attachments`
  itself, so a `grep write_attachments` alone will not surface it.

- **`agent_schedules_router.py::run_now` hardcodes `agent_schedule_
  registry.dispatch_with_shared_lock` for EVERY `capability_id`,
  unconditionally — a real, disclosed, not-yet-fixed lock-sharing gap for
  one specific manual trigger path.** Found 2026-08-17,
  `REQ-SB-69-US-01-T04`: once `process_staged_email` became a granted,
  schedulable skill (`ADR-046` Decision 4), a human manually `POST
  /agents/{agent_id}/schedules/process_staged_email/run-now` would
  incorrectly route through the shared Outlook-COM lock instead of the
  new dedicated `_processing_lock` — reintroducing exactly the lock-
  sharing `T04` exists to eliminate, for this one manual trigger only. The
  structurally more important half of this same gap — a PERSISTED
  recurring schedule for `process_staged_email` — was fixed, in both real
  locations (`agent_schedule_registry.py::_make_scheduled_tick_callback`,
  `capture_scheduler.py::_build_scheduled_tick`), since both were inside
  `T04`'s own `## Files to Modify`; `agent_schedules_router.py` was not.
  Left unfixed — tracked at `REVIEW-QUEUE.md`, a small follow-up task
  recommended (a one-line conditional mirroring the two fixes already
  made). Any future change to how `process_staged_email` (or any future
  capability needing its own dedicated, non-shared lock) is dispatched
  must also check this one remaining call site.
  **CLOSED, `ESC-045` direct-fix pass, 2026-08-17:**
  `agent_schedules_router.py::run_now` now selects `dispatch_with_
  dedicated_processing_lock` for `capability_id == "process_staged_email"`
  and `dispatch_with_shared_lock` for every other id, mirroring `_make_
  scheduled_tick_callback`'s/`_build_scheduled_tick`'s own shape. The SAME
  pass also found — not previously disclosed anywhere — that `agents_
  router.py::_invoke_capability` (the OTHER real manual-dispatch entry
  point, `POST /agents/{agent_id}/actions/{action_id}`, reachable for
  `pull_email`/`process_staged_email` because both are real `skill_tools.
  SKILLS` members) special-cased only `capability_id == "run_capture_now"`
  for lock routing — `pull_email`/`process_staged_email` fell through to
  the generic, UN-locked `skill_registry.invoke_skill` branch entirely
  (no lock at all, not merely the wrong one). Fixed identically. Verified
  live both ways: a real 15s-induced `pull_email` stall did not block a
  separately-dispatched `process_staged_email` (0.55s via `run_now`,
  0.64s via `_invoke_capability`) — see `ESCALATIONS.md` → `ESC-045`,
  `Status: Resolved`, for full verification detail.

- **When a capability id gains its own dedicated (non-shared) dispatch
  lock, every real manual-dispatch entry point for that id must be
  audited and fixed, not just the ones already inside the introducing
  task's own `## Files to Modify`** — this project has real, distinct
  capability-dispatch surfaces (today: the scheduled-tick callback in
  `agent_schedule_registry.py`, the cold-start job builder in
  `capture_scheduler.py`, the `run-now` HTTP endpoint in
  `agent_schedules_router.py`, AND the generic action-dispatch endpoint in
  `agents_router.py::_invoke_capability`) and a lock-routing fix applied
  to only some of them leaves the rest silently wrong, in either
  direction (routed through the wrong lock, per `ESC-045`'s original
  `run_now` gap, or routed through no lock at all, per `_invoke_
  capability`'s undisclosed twin gap found while closing `ESC-045`).
  `grep`ping for the OLD dispatch function's own name alone is not
  sufficient to find every affected call site — a capability id can reach
  a lock-differentiated dispatch decision through a call site that never
  mentions the lock function by name (e.g. a generic `if capability_id ==
  ...` branch keyed on a DIFFERENT id, with everything else falling
  through to an unlocked default).

- **A disposable Project fixture nested under a REAL (pre-existing)
  Customer, used to verify any `REQ-SB-57` Synthesizer trigger, cascades
  a real write into that real Customer's own `## Glimpse` via
  `synthesize_project`'s always-on `synthesize_customer(...)` cascade
  (`REQ-SB-54` point 7's ownership rule) — deleting the disposable
  Project directory alone is NOT sufficient cleanup, since it leaves the
  real Customer's `## Glimpse` stale (referencing a Project that no
  longer exists on disk).** After removing every disposable Project
  fixture, always call the real, already-`Done` `synthesize_customer(
  customer)` once more — this self-heals the real Customer's `##
  Glimpse` to reflect current true state via the app's own real
  mechanism, rather than leaving a stale artefact or attempting a manual
  byte-level revert. Found live, `REQ-SB-57-US-01-T03` (verified against
  the real `Core42` customer). `log.md` is unaffected by this cascade
  UNLESS a genuine `won`/`lost`/`renewed` transition was engineered
  (`concluded_project` stays `None` otherwise), so it needs no
  equivalent self-heal call.
- **A sibling coder session building a concurrent `REQ-SB-57` task
  against the SAME real Customer note (`Core42`) produces genuine,
  independent content/mtime drift on that Customer's own `log.md`/
  `index.md`/Thread notes mid-verification** — not a defect in either
  session's own code. Reconfirms `SPRINT-025`/`SPRINT-029`'s own "shared
  dev vault can carry real concurrent-session drift" entry one level up,
  at the Customer-concept-file layer specifically. When a live
  before/after fixture-cleanup diff flags an unexpected change on a
  REAL, non-disposable shared note during concurrent multi-task work,
  root-cause via direct content inspection before assuming it is a
  self-caused regression. Found live, `REQ-SB-57-US-01-T03`.

- **A real Customer that carries BOTH a stale, pre-`ADR-042` flat
  `Work/Customers/<Name>.md` hub note AND its migrated OKF directory
  concept file (`Work/Customers/<slug>/<slug>.md`) collides on filename
  stem in `vault_indexing.get_index()` — the STALE legacy flat note wins
  (visited last by `vault_writer.list_all_note_paths()`'s sorted-path
  order), never the real, current OKF concept file.** Confirmed live for
  14 of 17 already-migrated real Customers in the configured vault
  (including `Core42`, `Masdar`, `ADNOC`) — only `Microsoft Azure`/
  `Azerbaijan Ministry of Digital Development and Transport`/`Unsorted`
  are collision-free. Editing one of the 14 shadowed Customers' real OKF
  concept file (e.g. its `## Glimpse`) has ZERO observable effect on
  anything reading through `vault_indexing.get_index()` (search, this
  story's own `glimpse_first_qa.py`, etc.) — the index entry for that
  stem never points at it. Any future live verification/fixture choice
  that needs a real, already-migrated Customer must pick one of the
  3 collision-free names above, or use a disposable Customer instead,
  until the underlying gap is fixed. Found live, `REQ-SB-58-US-01-T01`
  (`ESC-046`, `Open`).

- **`retrieve_notes_in_agent_scope`'s own MCP tool schema requires the
  CALLING model to self-report its own literal internal `agent_id` as a
  tool-call argument — no agent's own system message anywhere in this
  graph states that literal id string (only the human-readable display
  name, e.g. `"Vault Q&A"`, is ever named), so a model reliably guesses
  wrong (confirmed live: `"vault_qa_agent"`) and the server honestly
  rejects the call.** Any future live verification that needs a genuine,
  organic (not manually-supplied) real call to this tool via chat should
  expect this to fail intermittently for reasons unrelated to whatever
  feature is under test — root-cause via a captured-tool-call-arguments
  diagnostic before attributing the failure to new code. Found live,
  `REQ-SB-58-US-01-T02` (`ESC-047`, `Open`).

- **`vault_writer.replace_body_section` now requires a keyword-only
  `caller: str` argument with NO default (`REQ-SB-71-US-01`,
  `ADR-048` Decision 2)** — every call site, present and future, must
  declare its own identity (`"module.function"`, matching the calling
  FUNCTION, not module) and be registered in `app/data_access/
  section_ownership.py`'s `_CALLER_ALLOW_LISTS` with the exact header(s)
  it's allowed to write, or the call raises `section_ownership.
  SectionWriteNotAllowed` (a `PermissionError`) before any file I/O.
  `## Personal Notes`/`## Actions` are unconditionally unwritable by ANY
  caller, vault-wide, by header text alone — never overridable by a
  caller's own registry entry. A forgotten `caller=` at any future call
  site is a loud `TypeError` at call time, by design — never a silent gap.

- **Starting the real backend app (`uvicorn app.main:app`) always fires
  its own pre-existing, unconditional app-start capture trigger
  (`app/scheduling/capture_scheduler.py`, `ADR-005`) once per process
  start, regardless of the reason the app was started** — this makes real
  Outlook/Compass calls and writes real Meeting/People/Thread/Customer
  content into whichever vault `VAULT_PATH` points at. Any future live
  verification that needs a demonstrably clean/empty `Work/` directory
  listing for the FULL duration of a session should capture its "before"/
  "after" snapshots immediately around the one specific call under test,
  and treat that call's own machine-readable return value as the
  authoritative evidence of its own action — not a broader directory
  listing, which may include this unrelated concurrent activity. Found
  live, `REQ-SB-70-US-01-T01` (`SPRINT-060`).

- **`vault_writer.person_note_path` now takes `(dedup_key: str, customer:
  str | None)` — SIGNATURE CHANGE from `(email: str)`** (`REQ-SB-71-US-03`,
  `ADR-048` Decision 6). `dedup_key` comes from `vault_writer.person_note_
  dedup_key(name, email)` (lowercased email when present, else a
  name-slug). `people_extraction.ensure_person_note(name, email,
  customer=None)` gained an optional `customer=` keyword (backward-
  compatible, existing 2-positional-argument callers unaffected) and
  checks `vault_writer.find_person_note_path(dedup_key)` FIRST,
  vault-wide, before ever creating a new note — an already-existing
  Person note is topped up in place, never moved or duplicated, even when
  a later call derives a different Customer for the same person.

- **`app/business/my_day.py::list_calendar_items` reads Meeting `subject`/
  `start` frontmatter directly (also using `start` for its own 7-day
  window filter) — both are no longer persisted on a new-shape Meeting
  note (`REQ-SB-71-US-03`)** — every NEW-shape Meeting note is silently
  excluded from My Day's own Calendar tab until `my_day.py` is updated
  (disclosed, not fixed — out of `REQ-SB-71-US-03`'s own `## Files to
  Modify`). See `ESC-049`.

- **A native `<input type="text">` chat box's own browser-level value-
  sanitization algorithm strips embedded newline characters, even when the
  value is set programmatically via the controlled-input native-setter
  technique (not just real keyboard typing/paste)** — a multi-line
  markdown source string (e.g. a `"- one\n- two"` bulleted list) collapses
  to one line before it ever reaches a `react-markdown`-based renderer, so
  a single-line chat `<input>` cannot exercise list-syntax rendering for a
  USER-typed message; only `**bold**`/inline markdown survives. Found
  live, `BUGFIX-04-US-01-T04` verification (`Cockpit.tsx`'s and
  `AgentDetailPanel.tsx`'s own pre-existing `<input type="text">` chat
  boxes, both untouched by that task). Not a defect in `ChatMessageText`/
  `react-markdown` (list rendering itself is independently confirmed via
  agent-authored content, which does not pass through that input) — a
  property of the input control's own type. A future story wanting a
  user-typeable multi-line/list-capable chat input would need a
  `<textarea>` or similar, a real, disclosed UI change, not decided here.

- **`fastapi.middleware.cors.CORSMiddleware` (this codebase's real,
  unmodified CORS config, `app/main.py`) 400s any OPTIONS preflight that
  carries an `Access-Control-Request-Private-Network` header, regardless
  of origin** — headless Edge 151+ sends this header on preflighted
  cross-port loopback fetches (any real app-triggered `apiFetch` call
  that sets `Content-Type: application/json`), so every such call fails
  client-side with a generic `TypeError: Failed to fetch` in a headless-
  Edge-via-CDP verification session specifically; an unheadered manual
  `fetch()` (no preflight triggered) and `curl` both succeed against the
  same endpoint. Found live, `BUGFIX-04-US-01-T02`/`T04` verification —
  worked around harness-side only (a throwaway local proxy answering the
  preflight with the one extra header, paired with an additional Vite dev-
  server instance on the CORS config's own already-whitelisted `5174`
  origin), no app/CORS-config file touched. If a REAL end user's own
  browser ever enforces PNA the same way against this app's real
  cross-port (Vite:5173 → uvicorn:8000) local-dev setup, this same 400
  would surface for them too — a genuine, pre-existing, currently-
  undisclosed-elsewhere gap in `CORSMiddleware`'s own configuration, not
  yet filed as a `BUG` (not reproduced against a non-headless, real
  end-user browser this pass; recommended follow-up if it ever is).

- **A bulk housekeeping Job with no per-call scope/limit that makes one
  real external (Compass) call per real vault item is a genuinely
  30-90+ minute single HTTP call once the vault reaches this project's
  own real size (126 real Threads)** — a coding session's own
  background-process tooling can reclaim the backend process it started
  partway through such a call (confirmed live, `REQ-SB-72-US-01-T06`/
  `T07`/`T09`, `SPRINT-063`: 3 separate reclaims at ~35/40/55 minutes of
  process age, every time while the Compass calls were still succeeding
  — never a server crash, never an application error). This is an
  infrastructure constraint of a coding session's own tool sandbox, not
  of a normally-launched, operator-run backend process. When verifying a
  future bulk Job of this shape from inside a coding session: (1) prove
  correctness first via a real, targeted single-item call, never require
  a full-corpus run to complete before trusting the mechanism; (2) if a
  client-side call times out, poll read-only (log tailing / disk-state
  re-scans) to check whether the server-side work is still genuinely
  progressing before assuming failure or retrying; (3) never issue a
  second call to the same mutating function until process-absence + log
  evidence together confirm the prior one has actually ended. See
  `ESC-054`.

- **RESOLVED, 2026-08-19 (`BUGFIX-05-US-01`, `T04`/`T05`, `ADR-053`) —
  `email-capture-pipeline`'s working mode was required to stay `supervised`
  until BOTH `BUGFIX-05-US-01-AC-01` (flat-shape duplication) AND `AC-02`
  (directory-shape orphaning) were genuinely verified passing live; both
  now are, and the working mode is flipped `autonomous`, permanently. Kept
  here for historical context: `AC-02` closed live first (`T02`, `ADR-051`'s
  rewire); `AC-01` needed a second architectural pass (`ADR-053`'s
  `pre_migration_summary.md` sidecar) after its first live-verification
  attempt found `ADR-052`'s migration mechanism alone lost a
  freshly-migrated flat Thread's own real, pre-migration content the
  moment `synthesize_thread` next regenerated `## Summary` from its own
  now-empty `messages/` directory (`ESC-056`). Do not flip the working
  mode back to `supervised` without a new, disclosed reason.**

- **A shared lookup primitive with a documented, disclosed write side
  effect (e.g. `vault_writer.resolve_thread_directory`/`resolve_thread_
  note_path`'s legacy flat-shape migration exception, `ADR-052` Decision
  5) can be triggered by an innocuous "just re-confirm current state"
  diagnostic call during live verification, not only by the tracked
  verification step itself.** Found live, `BUGFIX-05-US-01-T04`
  (2026-08-19): a diagnostic call to `resolve_thread_note_path`, made
  purely to re-confirm a verification candidate's own clean flat-note
  state before the tracked test run, silently migrated it — no data was
  lost (the migration itself is a safe, idempotent rename plus a
  content-preserving sidecar write), but it happened outside the real
  capability endpoint the task's own methodology required, and had to be
  manually reversed before the tracked run could proceed correctly. When a
  function's own docstring discloses a write side effect, prefer a plain
  file read (never calling that function) for any "just checking" aside
  during verification — reserve the side-effecting call for the actual,
  tracked verification step alone.

- **`cockpit/people.py`'s `_coerce_people_list` must handle THREE real
  `attendees`/`recipients` frontmatter shapes, not the two originally
  designed (`ADR-036` point 7).** Found live, `BUGFIX-06-US-01-T01`/
  `BUG-027` (2026-08-19): direct reading of `meeting_classification.py`'s
  real, current attendee-write path confirmed Meeting `attendees` has
  never actually shipped as `list[dict]` — it always writes a plain
  `list[str]` of wikilinks (`["[[stem]]", ...]`). `_coerce_people_list`
  now normalizes every item through `_normalize_person_item` (dict item
  passes through unchanged; a wikilink-string item is stripped via the
  now-public `vault_writer.WIKILINK_PATTERN` and resolved via
  `vault_indexing.get_index()`, falling back to `{}` — the existing
  "no note yet" chip — for an unresolvable stem or malformed item) so all
  three real shapes (JSON-encoded string, real `list[dict]`, plain
  wikilink-string list) resolve to the same `{"name", "email"}` contract.
  Any future caller writing a NEW `attendees`/`recipients`-shaped field
  must be checked against this three-shape reality, not against the
  stale two-shape docstring alone.

- **`librarian_housekeeping.py::propose_customer_archival_candidates` treats `propose_
  customer_backfill`'s own `matched_existing_customer_names` return value as its ONLY
  real evidence signal for "this Customer folder has zero real Thread matches" — never
  call it against a partial/bounded/manually-filtered `propose_customer_backfill` run
  for a real business decision.** Found live, `BUGFIX-08-US-01-T02` (2026-08-19): during
  verification, bounding `propose_customer_backfill`'s own input to 3 real Threads (to
  control real Compass call volume) starved `matched_existing_customer_names` down to 3
  real customers, which in turn made `propose_customer_archival_candidates` propose 24
  OTHER real Customer folders as archival candidates — technically correct against the
  narrowed input, but factually wrong against the real vault (those folders likely do
  have real matches across the FULL Thread corpus; the bounded pass simply never computed
  them). The two Jobs' data dependency is one-directional and silent — narrowing the
  first Job's input degrades the second Job's own correctness, not just its runtime, with
  no error or warning surfaced anywhere.

- **`librarian_housekeeping.finalize_company_review`'s Merge outcome can cause the SAME
  duplicate company name to be re-proposed by a later `propose_company_review()` pass,
  even though it was already correctly resolved.** Found live, `REQ-SB-76-US-01-T09`
  (2026-08-19): Merge applies the CANONICAL entity's own tag (`customer/<canonical-slug>`)
  to every batch Thread — never a `customer/<duplicate-slug>`-shaped tag for the duplicate
  name itself — so a future pass's per-mention idempotency check (keyed on the exact
  proposed company name's own tag, `ADR-057`'s own already-disclosed "coarser than
  exact-content tracking" Consequence) finds no tag under the duplicate's own name and
  correctly, if unhelpfully, re-surfaces it. Confirmed harmless — re-resolving (Merge or
  Decline) a re-surfaced duplicate a second time is a safe, idempotent no-op (`_existing_
  duplicate_shape` correctly finds nothing left to archive) — but real, disclosed, not
  fixed (would need a new duplicate-name-tracking mechanism, a real design question left
  open for a future story if this proves recurring/annoying in practice).

- **`librarian_housekeeping._apply_company_to_threads`'s additive branch regenerates a
  Thread's whole `## Related` section from ONLY the current call's own single
  `mentioned_companies=[target_name]` — it does not accumulate across multiple separate
  Company Review resolutions on the same Thread.** Found live, `REQ-SB-76-US-01-T09`
  (2026-08-19): a real Thread that received three separate additive resolutions in one
  session (Core42-partner, then Mubadala-customer, then Sindan-customer) ended with all
  three tags correctly present in `tags`, but `## Related` showing only the LAST
  resolution's own wikilink — the earlier two were silently overwritten, not accumulated.
  Every individual AC-09-shaped resolution is still correct at the moment it runs (the
  Related section DOES gain the new company's link); only the rare 3-plus-companies
  cumulative case loses the earlier links. Not fixed (a real design decision — accumulate
  from the Thread's own current `tags` vs. a new persisted list — out of any single task's
  narrow scope); flag this if a future story touches `## Related` regeneration again.

- **A git worktree's own branch can be missing whole task/story/sprint files the main
  checkout genuinely has, even when the main checkout's `git status` is fully CLEAN —
  because the worktree's own branch is simply BEHIND `master` by real, already-committed
  commits, not because of the already-documented `M`/`??` uncommitted-file staleness
  above.** Found live, `SPRINT-073`/`REQ-SB-79-US-01` coder run (2026-08-19): a worktree
  branched off `master` earlier in the session had zero unique commits of its own and was
  a pure ancestor of the current `master` (several commits behind, including the one that
  created this exact sprint's own task/story/sprint files) — `Implementation/Tasks/
  REQ-SB-79-US-01-T01...md` etc. simply did not exist in the worktree at all, while
  `Test-Path` against the SAME path in the main checkout returned `True`. **Fix:** from
  inside the worktree, run `git log --oneline master..HEAD` (should be empty) and `git log
  --oneline HEAD..master` (commits missing from the worktree); if the worktree branch has
  zero unique commits (a pure ancestor), `git merge master --ff-only` is safe and
  non-destructive — this repo's own worktrees share one object database, so `master` is
  always reachable from any worktree without a remote fetch. Do this BEFORE trusting any
  "file does not exist in this worktree" result, not just before trusting a stale file's
  CONTENT.

- **A real, latent circular import exists across `email_classification.py` ->
  `vault_filing_expert.py` -> `agent_orchestration/` (`__init__.py` -> `graph.py`) ->
  `knowledge_gap_tracking.py` -> `agent_orchestration/knowledge_bootstrap.py` ->
  `skill_registry.py` -> `skill_tools.py` -> `thread_summary_backfill.py` -> back to
  `email_classification.py` — it has never been fixed at the source, only masked by
  import order.** Found live, 2026-08-20 (archiving the 9 dead orchestration-layer
  routers): `main.py`'s own import order previously "worked" only because `agents_
  router.py`/`agent_schedules_router.py` (both now archived) happened to import `agent_
  schedule_registry` — and therefore `skill_registry`/`skill_tools` — before anything
  imported `email_classification.py` directly; removing them and importing `email_poc_
  router` (which imports `email_classification`) first instead made `thread_summary_
  backfill.py`'s own `from app.business.email_classification import
  _THREAD_SUMMARY_SYNTHESIS_DEFAULT_INSTRUCTIONS` fail with `ImportError: cannot import
  name ... from partially initialized module` — confirmed via `git stash` that this exact
  failure does NOT reproduce on the prior committed `main.py`, ruling out "always-broken,
  never noticed." **Current fix (main.py only, not the cycle itself):** `from app.business
  import agent_registry, agent_schedule_registry` is now the FIRST import in `main.py`,
  restoring the same resolution order the archived routers used to provide as a side
  effect — do not reorder or remove this import without re-testing `python -c "import
  app.main"` first. The cycle itself is still real and will resurface the moment this
  ordering is disturbed again (e.g. by the still-pending business-layer archive/split,
  Tasks #163/#164) — worth a real source-level fix (breaking one of these edges, most
  plausibly `vault_filing_expert.py`'s module-level `agent_orchestration.model_factory`
  import) whenever that layer is next restructured, not another order-dependent patch.
