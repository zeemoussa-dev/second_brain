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
  customer account; many real contacts are internal Core42 colleagues or
  third parties). Same reasoning as ADR-004's customer-as-tag decision.
  Backfilled from already-captured Email notes' sender fields (deduped by
  email address); the Meeting-based half is real but blocked on REQ-SB-08
  not existing yet. Full schema:
  `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md`.
- [2026-08-10] Reversed the earlier "Drop" call on agentic-map's REQ-079/
  080/081 (pipeline_items/customer_entitlements tables + tools) – real
  captured email data confirmed Second Brain's actual customer domain is
  Azure MACC/consumption business (ADNOC/TAQA/Masdar/Core42), exactly what
  those requirements were built for in agentic-map. Reshaped for notes
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
  `SPRINT-024`) shipped and verified live, per `ADR-023` — the
  culmination of the 5-sprint "Compass Expert" business chain
  (`SPRINT-020`…`024`). This is the first code path in this project that
  actually ACTS on a Hub-routing match (`ADR-017`) rather than only
  reporting it. New pilot agent `"compass-expert"`
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

## Patterns

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

## Constraints

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
