# CHANGELOG

All notable changes to Second Brain.

**2026-08-20:** Previous history (through the Hermes/LangGraph architecture
pivot) archived, not deleted — see `Documentation-Archive-2026-08-20/
CHANGELOG.md`. Starting fresh alongside the backend redesign
(`Implementation/Plans/2026-08-20-backend-architecture-redesign.md`,
`ADR-059`).

<!-- Format:
## YYYY-MM-DD — Sprint NNN / task description
- feat: what was added
- fix: what was fixed
- refactor: what was restructured
- docs: documentation changes
-->

## [Unreleased]

- feat: long free-text panel fields (Description, Purpose, Guardrails
  on Agents; Subtitle/Description on Sections and Pipelines) now clamp
  to 3 lines with a real "Read more"/"Show less" toggle instead of
  running on unbounded and pushing the rest of the panel out of view.
  Short values that never overflow 3 lines show no toggle at all.
- feat: rebuilt Create Agent from scratch — the old wizard's `POST /agents`
  payload never matched the real backend contract (missing required
  `id`/`section_id`, wrong field names, an inert Trigger step), so
  every submission 422'd; nothing about it worked.
  - The "+" FAB now opens a real type-select menu (`AgentTypeMenu.tsx`)
    — Expert, Producer, Worker, Pipeline, Section — with only Expert
    wired to a real flow; the other four are visibly disabled
    "Coming soon" entries, not hidden.
  - New `CreateExpertWizardModal.tsx`, 6 grouped steps (Identity →
    Knowledge & access → Tools & skills → Behavior → Appearance →
    Review), each with its own icon and one-line context, reusing
    every existing picker (`TagTreePicker`, `ChecklistPicker`,
    `SkillsTree`, `VisualPicker`) rather than rebuilding them.
  - Id auto-derives from Name as a real slug, always valid, updating
    live even if manually edited.
  - `createAgent()`'s request body now matches `AgentCreateBody`
    field-for-field — `id`/`section_id`/`type` required, everything
    else (description, prompt, guardrails, scope, tools, preferred
    indexes, background-agent) optional and real.
- fix: long text in side-panel list rows (Skills/tools names,
  Pipeline Step descriptions, and every other `.item-row` user) now
  wraps and grows its row instead of ellipsis-clipping or overflowing
  the panel's fixed width.
- feat: real Pipeline-level access on the Agents Map — a Pipeline (name,
  description, real cron schedule/status, Steps) was completely
  unreachable from the UI before this; Steps just spliced into ordinary
  Agent nodes with no pipeline-level affordance anywhere.
  - New `pipelines_router.py` (extracted out of `agents_router.py`,
    matching the one-router-per-entity convention) — `GET /pipelines`
    unchanged, new `GET /pipelines/{id}` returns the real `Pipeline`
    dataclass (cron status + Steps included).
  - New `PipelineDetailPanel.tsx` — Overview (description/section/cron
    schedule+status+last/next-run) + a Steps list, each row opening the
    existing `JobSettingsPanel`.
  - New floating `.pipeline-title` label, Section drill-down only,
    above each Pipeline's real entry-point Step — `.section-title`'s
    own font, opacity dialed 0.6 → 0.9 on hover. Hovering/clicking it
    highlights every node in that Pipeline's own chain
    (`.agent-node--pipeline-hover`) and pans+zooms the camera to fit
    the WHOLE chain end to end (not hiding under the open panel),
    with the entry-point Step's own ring + description card shown by
    default.
  - Hovering a Step row inside `PipelineDetailPanel` zooms the camera
    to that one Step specifically, at a DYNAMIC scale (not a fixed
    3x) that keeps its own description card fully on screen — a real
    measurement of the card's own rendered height, so a long
    description gets a smaller zoom than a short one. Moving off the
    row reverts to the whole-chain view.
  - Same real, measured panel-clearance fix applies throughout (the
    description card never overlaps the open panel's own edge).
  - Flagged, not fixed: clicking a Step to edit its own settings hits a
    real 404 — `GET/PATCH /agents/{id}/jobs/{job_id}/settings` was
    never rebuilt after the Hermes pivot.
- feat: faded dot-grid background, system-wide, replacing the flat
  `--color-bg` fill — moves/scales with the Agents Map canvas's own
  pan+zoom (a real second copy of the same pattern on the canvas
  itself, not just inherited from the page).
- fix: connector lines (`.spoke-line`/`.cluster-line`, Hub↔Agent,
  Agent↔Agent, and KB↔Hub) genuinely desyncing from their connected
  nodes on rotate — a `<line>`'s `x1/y1/x2/y2` were never CSS-stylable
  properties in the first place, so an earlier CSS-only `transition`
  fix (above, now corrected) never actually fired. Replaced with real
  `requestAnimationFrame` interpolation of the line endpoints, matching
  the nodes' own 500ms timing; the KB↔Hub spoke line's own traveling
  pulse dots share the same interpolated points so their path stays in
  sync too.
- feat: Agents Map visual polish batch — themed scrollbars, corrected
  node sizing, and a drill-down hover effect.
  - Global themed, slim scrollbars (`tokens.css`) — `scrollbar-width:
    thin`/`scrollbar-color` for Firefox, `::-webkit-scrollbar*` (8px,
    muted thumb) for Chromium; no scrollbar CSS existed anywhere
    before this.
  - Agent node sizing now anchored to real Hub-size percentages
    instead of ad-hoc multipliers: Expert/Producer = 40% of Hub size,
    Worker = 22% of Hub size (both overview and Section drill-down).
    `SectionDrilldown.tsx`'s own connector-line edge-trim radius
    constants were updated to match.
  - New zoom + glow + secondary-border hover effect on Agent nodes in
    the Section drill-down view (unchanged in the crowded overview map
    per a standing 2026-08-16 decision) — a layered box-shadow (blur +
    a further-out crisp ring), tinted from each node's own real color.
- feat: "big popup" field editors for every cramped list/long-text field
  in the Agent/Section detail side panels — a small expand icon next to
  Vault scope, Tools, Relays to, Preferred indexes, Prompt, Guardrails
  (Agent) and Folders, Description, Subtitle (Section) opens a real,
  wider modal (`FieldEditorModal.tsx`) instead of editing in a
  single-line inline input.
  - New generic `ChecklistPicker.tsx` (flat checkbox list) and
    `TagTreePicker.tsx` (the vault's real flat tag list, grouped into a
    real hierarchy by `/` segments client-side, select + save).
  - New backend endpoints, both real gaps that had no HTTP surface
    before: `GET /tools` (`tools_router.py`, the full agent-independent
    Hermes toolset catalog) and `GET /indexes` (`index_router.py`,
    `IndexManager` had Manager-level `get_all()` since 2026-08-28 but no
    route until now).
  - Vault Scope combines a tag tree + a folder checklist into one
    picker (both real, from `vault-search/scope-suggestions`); Tools,
    Relays to, and Preferred indexes each get a checklist over their
    own real catalog; Section Folders reuses the same real folder list.
  Verified live against real production data (`adnoc-expert`, the
  Customers section) — a real save/revert round trip confirmed via
  direct API calls, restoring the only real data touched. `npx tsc
  --noEmit` clean on every touched/new file.
- fix: 5 real UI bugs/usability issues in the Agent/Section detail side
  panels, reported by the operator from live use:
  - Both panels rendered fully blank (not even header/tabs) while their
    detail fetch was in flight — added a real `.side-panel-loading`
    spinner state.
  - `AgentDetailPanel.tsx`'s Capabilities section is now a collapsible
    `.section-collapse-header` (bigger label, filling rule, trailing
    arrow), defaulting collapsed, expanding on click to reveal the
    built-in list + `SkillsTree`.
  - `SkillsTree.tsx` had no dedicated CSS at all — added a real
    stylesheet, and redesigned the per-row action per spec: a single
    Grant button docked right, disabling + relabeling "Granted" once
    held, instead of toggling to a per-row Revoke button (revoke now
    happens only via the existing checkbox + bulk-action bar). Removed
    the now-dead `onRevokeSkill` prop/`handleRevokeSkill` handler.
  - Fixed the Vault Scope suggestions dropdown staying permanently
    visible and overlapping the Tools row beneath it — it rendered
    whenever the committed value happened to match a real tag/folder
    (e.g. `"customer/adnoc"` matching itself), with no focus guard at
    all. Now gated on real input focus.
  - `.kv-list .kv-row` (`settings.css`) gained `flex-wrap` so a long
    comma-joined value (Vault scope, Tools, a Section's Agent list) wraps
    onto its own line(s) instead of overflowing/getting clipped on a
    single line.
  Verified live against the real `adnoc-expert` agent; `npx tsc --noEmit`
  clean on every touched file.
- fix: `SectionDetailPanel.tsx` audit — added `subtitle`/`folders`/
  `fallback_agent_id` (all already real, already-wired fields the panel
  never rendered) and a real `agent_ids` list (was a bare count).
  Backend/type already fully supported all of this; only the panel
  component needed updating. Verified live in the browser. Found (not
  fixed — separate, pre-existing, out of scope) a real bug in
  `AgentsMapPage.tsx`: `selectedAgentId`/`selectedSectionId` are
  independent state, so a Section Hub click never clears a previously-
  open Agent panel and both can render at once.
- fix: `AgentDetailPanel.tsx` audit — added `tools`/`depends_on`/
  `preferred_index_ids` to `to_detail_dict()` and the panel (Overview +
  editable Settings fields); fixed the Overview Guardrails row (was
  showing a hardcoded generic sentence instead of the real value);
  converted the non-functional Working Mode and Keywords controls to
  honest read-only display (neither has any real backend field or
  storage — both silently dropped every edit before this).
- feat: `tools` wired as a real 3rd `Agent` field, alongside `section_id`
  and `scope` — real, per-profile Hermes toolset state
  (`HermesCLI.list_tools/enable_tools/disable_tools`, `HermesCLI`'s
  first-ever per-profile `-p` targeting). `get_by_id()` reads real
  state; `get_all()` skips it for performance (one subprocess call per
  agent otherwise). `create()`/`update(tools=[...])` both take a full
  declarative replace, diffed against real current state. Wired through
  `POST /agents`/`PATCH /agents/{id}`/`to_detail_dict`. Verified live at
  both the Manager and HTTP layers.
- fix: real production change — disabled `web`/`browser`/`image_gen`/
  `bfl`/`tts`/`computer_use`/`code_execution` toolsets on all 30 real
  non-Primary agents (kept `terminal`/`file`/`skills`/`cronjob`/`todo`/
  `memory`/`session_search`/`clarify`/`delegation`). `default` (Primary)
  kept at full capability. A real, durable Hermes-side change
  (`hermes tools enable/disable`), not yet tracked by this app's own
  data model.
- feat: `POST /agents/{agent_id}/specialists/regenerate` added — wires
  `AgentManager.regenerate_specialists_section()` to the API; previously
  callable only via direct Python, with no way to trigger it from the
  frontend after `depends_on` changes.
- fix: real data-corruption bug — `AgentManager.update()` could write a
  duplicate `Agent.json` under the wrong Section when called as the
  first `update()` in a fresh process (stale Registry cache fallback).
  Caused "Customers had 3 Experts, now I can see only 1" (`adnoc-expert`/
  `masdar-expert`/`customer-hub` all affected). Fixed at the root
  (`update()` now reloads the Registry before reading current state);
  the 3 real stray duplicates found and removed, their only genuinely
  new data merged back into the correct copy first.
- feat: `POST /agents` added — real Agent creation, previously missing
  entirely (`CreateAgentWizardModal.tsx` had been 404ing). Thin wrapper
  over the already-working `AgentManager.create()`.
- fix: `AgentManager.create()`/`update()`/`delete()` now force a
  Registry cache reload (`_reload_registry()`) right after writing,
  before their own read-back — without this, a just-created/updated
  agent's own response (and any immediate follow-up read) could show
  stale pre-write data for up to the hot-reload poll's ~2s window.
  Confirmed live via `POST /agents`.
- fix: `POST /agents` with a duplicate id now returns a clean 409
  instead of an uncaught `HermesUnavailableError` surfacing as a raw
  500 with an exposed stack trace.
- feat: Vault Scope extended to 13 more real agents (4 Section Hubs +
  9 Domain Experts), each mapped individually against the real, current
  vault tag landscape rather than a uniform rule — `technology-hub` is
  folder-scoped instead of tag-scoped (future-proof as new tags get
  added under it); `azure-calculator`/`compass-solutions` left unscoped
  (no real matching tag exists for either); the 7 cross-cutting/utility
  agents left unscoped by design (each needs cross-customer reach).
  Verified live: every agent's scope round-trips correctly and each real
  `SOUL.md` has exactly one `## Scope` heading, no duplication.
- feat: real per-customer Indexes (`Adnoc`, `Masdar`, `TAQA`) created and
  linked to their respective Customer Expert agents via
  `preferred_index_ids`; each agent given a "say you don't know rather
  than guessing" guardrail and a customer-tag-only Vault Scope. Verified
  live against all 3 real agents via direct `hermes chat` calls.
- fix: Vault Scope + Guardrails agent editing (`AgentDetailPanel.tsx`/
  `CreateAgentWizardModal.tsx`) had never actually worked for any real
  agent — two stacked bugs. `PATCH /agents/{agent_id}`'s request body
  model only declared `icon`/`color`, so `scope`/`guardrails`/
  `section_id`/`is_background_agent` were silently dropped by FastAPI
  (always 200 OK, never an error). Separately, `AgentManager._to_agent()`
  hardcoded `guardrails=None`/`scope={}` on every read regardless of real
  SOUL.md content. Fixed both: `agent_manager.py` gained
  `_split_soul_sections()` (real parsing, the exact inverse of the
  existing `_soul_text()` composer); `agents_router.py`'s body model
  renamed `AgentUpdateBody` and extended with the real, already-backed
  fields, plus a new `_classify_scope()` that splits the frontend's flat
  scope list back into `{folders, tags}` by real membership against the
  live vault's own tag/folder snapshot. Verified live via disposable
  scratch agents at both the Manager layer and the real HTTP route.
  `POST /agents` (real Agent creation) is still a confirmed, separate,
  unfixed 404 — out of scope for this pass.
- design: `html-prototype/first-run-onboarding.html` — new prototype screen
  for REQ-SB-84's one UI-facing part (Fresh-Machine Provisioning's
  first-run onboarding wizard). Collects only the vault path (the one
  Settings field with no default/auto-seed path); shows Providers
  (Compass, Anthropic Claude — auto-seeded from required `.env` settings)
  and Sections (the real starting 6) read-only rather than as forms, since
  both already auto-seed in code and provider-credential collection is the
  provisioning script's job per the requirement text, not the frontend's;
  adds a boot-stage checklist step matching `registry/loader.py`'s real
  5-stage cold-boot order. `html-prototype/index.html` updated with a new
  catalog card linking it. Flagged in `REVIEW-QUEUE.md` for human browser
  sign-off (designer always flags) — pending approval before `/spec` runs
  on REQ-SB-84.

- feat: `SkillManager`/`ToolManager` (`app/business/core/skills/`,
  `app/business/core/tools/`) built as real Core entities. Skill content
  (`SKILL.md`+`scripts/`) lives in the checked-in `Hermes-Provisioning/
  skills/` template repo (`data_access/skills.py`); metadata (name,
  description, Tool grouping, `deployed_to`, `mutates`, `origin`) lives
  in the pre-existing Registry `Tools/<tool>/Skills/` tree
  (`data_access/tools.py`), the same tree the Agents Map's Skills panel
  already reads. `SkillManager` supports create/update/deploy/undeploy/
  delete (fanning out to `app.hermes.skills.HermesSkills` per deployed
  profile) and `sync_from_hermes()` — a cron-callable drift-catcher that
  sweeps every real Hermes profile for skills under an already-known
  category and files a genuinely new one under the catch-all "jarvis"
  Tool. `ToolManager` is a generic create/update/delete gateway; Tools
  are user-creatable, not a fixed set.
- fix: reconciled real drift between `Hermes-Provisioning/skills/` and
  live Hermes state across all 25 real profiles, found during the
  pre-build sweep above — 2 skills missing `SKILL.md` entirely, 9 stale
  script/doc files, and 2 real skills (`pricing/azure-cost-calculator`,
  `sales/macc-forecast-generator`) that existed live under categories
  never checked into the repo at all. Deleted 2 dead Registry catalog
  entries (`outlook/gather_emails`, `web/web-search`) backing no real
  skill anywhere.
- fix: `ProviderManager._seed_state()` was reading its real .env-backed
  seed values (`compass_api_key`, `anthropic_api_key`, etc.) directly
  from `app.config.settings`, bypassing `data_access` — moved into a new
  `data_access/providers.py::seed_defaults()`; the Manager now holds no
  raw settings/file access at all.
- refactor: second stray-file pass over `app/business/`. Deleted
  `demo_taxonomy.py` (old ADR-041 taxonomy fixture data, zero mentions
  anywhere), `tag_backfill.py` (one-off migration, only ever referenced
  as a naming precedent in other docstrings), and the whole
  `business/langgraph/` (a 2026-08-20 LangGraph proof-of-concept,
  already flagged dead in an earlier pass but never actually deleted)
  and `business/pipelines/` (a 0-byte empty package, superseded by
  `business/core/pipelines/`) packages.
- feat: `ProviderManager` (`app/business/core/provider/`) built as a
  real Core entity — the sole gateway onto Second Brain's own known LLM
  provider credentials (Compass, Anthropic Claude), kept for a
  not-yet-built future use (provisioning a brand-new Hermes install),
  not for live per-agent routing (Hermes owns that directly now).
  Folds in `provider_registry.py`'s real credential/endpoint/model data
  while dropping its dead per-agent assignment tracking entirely — that
  mechanism silently deleted every real assignment on every read
  because it reconciled against `agent_registry.py`, the retired
  pre-Hermes agent model (empty since 2026-08-22). Also found: `/providers`
  has had no backend route since the Hermes-pivot cleanup — the real
  frontend Providers panel has been calling a 404 in production.
  Deleted `agent_registry.py` and `provider_registry.py` outright
  (fully superseded), and the dead frontend `ProvidersCard.tsx`/
  `SettingsProvidersPage.tsx`/`/settings/providers` route+nav entry.
- refactor: `system_health.py` moved to `business/logic/`, sourcing
  real data from `ProviderManager` instead of the two retired
  registries above. Dropped `disabled_agents` entirely — no real
  equivalent exists in the Hermes world (every real Hermes agent has
  some real model configured by construction). Also cleaned up orphaned
  `vault_writer.py` state functions found in passing:
  `load_providers_state`/`save_providers_state`/
  `load_agents_registry_state`/`save_agents_registry_state` (dead once
  their only callers were removed) and `load_sections_state`/
  `save_sections_state` (already-orphaned leftovers from the earlier
  SectionManager retrofit). Verified live: `GET /system-health` returns
  real Provider data, a full scratch Provider CRUD lifecycle via
  `ProviderManager`, the System Health and Settings pages render
  correctly with the dead UI removed, zero real network requests to
  `/providers` anywhere in the frontend.
- refactor: cleaned up the last stray `business/vault_*.py` files.
  Deleted 3 confirmed-dead one-off/retired scripts —
  `vault_filing_methodology.py` (orphaned when the old LangGraph "Vault
  Filing Expert" was retired), `vault_provisioning.py`, and
  `vault_restructure.py` (both already zero-caller one-off migrations).
  Folded the 4th, `vault_search.py` (browse/tag-filter/note-detail/
  ranked-search/graph), into `VaultManager` the same way earlier
  vault_*.py modules were — its one real caller
  (`vault_search_router.py`) migrated, the module deleted. Verified
  live: `/vault-search/*` (status/notes/note-detail/asset/search/tags/
  scope-suggestions/graph) all still correct against real data.
- refactor: `PipelineManager`'s own raw I/O fixed — new
  `data_access/pipelines.py` owns the real `pipelines/<id>.json` reads;
  `PipelineManager` itself holds zero raw file calls now, only
  section-name resolution and cron composition. Verified live: all 3
  real pipelines still resolve correctly with live cron status, `GET
  /agents` unchanged.
- feat: `IndexManager` (`app/business/core/index/`) built — a real,
  user-defined, scoped vault index (folders, tags, depth, storage path,
  a real Hermes cron schedule), distinct from `VaultManager`'s own
  single whole-vault in-memory index. `create()` deploys a generalized
  build engine (new `Hermes-Provisioning/skills/vault-rebuild/vault-index/
  scripts/index_builder_lib.py`, parameterizing the existing
  `build_vault_index.py`'s own logic) plus a tiny per-Index stub script,
  then creates a real `hermes cron create --script --no-agent` job (new
  `HermesCli.create_cron_job`/`edit_cron_job`/`remove_cron_job`,
  verified live against the real installed CLI). `delete()` removes the
  cron job, the built output file, the stub script, and the definition,
  in that order. The pre-existing global structural index
  (`vault-index-rebuild`) was registered as a real Index record via the
  new `register_existing()` (definition-only, zero cron mutation — the
  real job keeps running exactly as it already did) rather than
  replaced. `Agent` gained `preferred_index_ids`, plus
  `AgentManager.regenerate_index_guidance_section()` — same explicit,
  idempotent, marker-delimited SOUL.md shape as the existing
  `regenerate_specialists_section`. All raw I/O lives in the new
  `data_access/indexes.py`, following the layering correction from the
  start. This same commit also completes `AgentManager`'s own layering-
  correction retrofit (its Agent.json/soul.md writes and folder deletes
  now go through `data_access/registry/writer.py`, introduced alongside
  `SectionManager`'s own equivalent fix in the previous commit) — landed
  together since both touch `agent_manager.py`. Verified live
  end-to-end: a full disposable Index's create→list→get→delete
  lifecycle (cron job and deployed script both confirmed to actually
  appear/disappear), a real triggered run producing a real,
  correctly-scoped 105-note output file, the Agent guidance block
  generating/re-running idempotently/clearing correctly, and the real
  `vault-index-rebuild` job confirmed completely untouched after
  registration. Not yet built (disclosed, not silently skipped): no
  HTTP router/API surface yet, no dedicated consult-index tool for an
  agent (guidance-text-only, as scoped).
- refactor: layering correction — `SectionManager`, `AgentManager`, and
  `VaultManager` no longer do raw file I/O directly; each now calls a
  dedicated `data_access/` module instead (operator: "Managers
  understand Entities, Data Access understands stores... I/O always
  happens in Data Access"). New `data_access/sections.py`
  (`agent_sections.json`), `data_access/registry/writer.py`
  (Section.json/Agent.json/soul.md writes + folder deletes — shared
  between Section/Agent since both write into the same Registry tree,
  also owns the write-target `agent_dir()` path formula moved out of
  `AgentManager`), `data_access/vault_index_config.py`
  (`index_config.json`), `data_access/entities.py` (`Entities.md`'s raw
  text — the `### <heading>` parse/render stays in `VaultManager`, that
  part is business shaping, not I/O). `VaultManager`'s note-index
  rebuild was already compliant (routed through `vault_writer.py` from
  the start). Verified live: a full scratch Section→Hub-Agent
  create/update/delete round-trip (confirmed the real `Agent.json` on
  disk correctly gets `type: "hub"`), a `/vault/index-config` toggle
  round-trip, and a scratch `/vault/entities` create+delete.
- refactor: `TemplateManager` (`app/business/core/templates/`) built as
  the sole business-layer gateway onto Template data, folding in and
  retiring `data_access/templates/registry.py`'s `get_template`/
  `list_templates` — only one real caller existed
  (`VaultManager.list_templates()`, now delegating to it instead of
  re-reading `Template.json` itself). Found live: `get_template()` had
  ZERO real callers anywhere — the actual template-loading path for
  every real vault write (e.g. `business/cockpit/documents.py`) goes
  through a completely different function, `app/vault/vault_manager.py`'s
  own low-level `load_template()`; both packages' docstrings now
  explicitly warn not to confuse the two. Raw I/O lives in a new, thin
  `data_access/templates.py` (`list_template_ids`/`read_template_json`)
  — a correction to this session's own earlier "Managers own their file
  I/O directly" precedent (operator: "Managers understand Entities, Data
  Access understands stores... I/O always happens in Data Access"), so
  `TemplateManager` itself holds zero raw file calls, only entity-shaping
  and the malformed-entry error-visibility policy (a `sections` entry
  with an unexpected shape, or unparsable JSON, still returns a visible
  `Template(error=...)` rather than crashing the whole listing or
  disappearing silently). `SectionManager`/`AgentManager`/`VaultManager`
  (built earlier this session, before this correction) still do raw I/O
  directly — known, disclosed, not yet retrofitted. Verified live: `GET
  /vault/templates` returns all 7 real templates with correct section
  counts, `TemplateManager().get_by_id('meeting')` returns correctly
  typed `TemplateSection` objects, an unknown id returns `None`.
- refactor: `VaultManager` (`app/business/core/vault/`) built as the
  sole gateway onto Vault data — fully absorbs and retires
  `vault_indexing.py`, `vault_index_config.py`, `vault_templates.py`,
  and `vault_entities.py`. All real call sites migrated (24 across 13
  files, including `main.py`'s boot-time rebuild, the Registry loader's
  reachability, `moderator.py`, `vault_search.py`, `people_extraction.py`,
  and several `business/cockpit/*` modules) — no second door left onto
  the same data. `Vault` stays a genuine singleton (`get_overview() ->
  Vault`), a deliberate deviation from the other Core entities'
  `Array<Entity>` convention since there's exactly one vault. The note
  index's own real in-memory state is kept as module-level globals
  inside the new file (not instance attributes) so every one of the 13
  independently-instantiated `VaultManager()` calls shares the same
  index — confirmed live. Also deleted `business/glimpse_first_qa.py`,
  a fully orphaned dead module (zero real callers anywhere, left over
  from `app/api/mcp_server.py`'s earlier deletion). `app.business.core.
  vault` and `app.vault` (the real, untouched low-level Obsidian write
  engine) are two unrelated things sharing the word "vault" — both
  packages' own docstrings now explicitly warn not to confuse them.
  Verified live: `GET /vault/overview`, `/vault-search/status`,
  `/vault/index-config` (round-tripping toggle), `/vault/templates`,
  full `/vault/entities` CRUD (including the soft-delete landing on
  disk), and downstream consumers `GET /my-day/summary`/`GET /cockpit/
  meeting/<real stem>` all correct against real data.
- refactor: `app/api/*.py` routers now hold zero business logic. Audited
  all 14 router files; extracted real logic out of the 5 that had any
  into new `business/logic/` modules — `my_day_window.py` (the day-in-
  window validation `my_day_router.py` used to compute inline),
  `vault_index_rebuild.py` (the dual in-process + agent-facing-Hermes-
  cron rebuild orchestration), `section_agents.py` (the cross-manager
  Section↔Agent composition and blocked-delete message-building),
  `agent_chat_stream.py` (the SSE chat-stream event interpretation and
  the lock/session orchestration around one streamed turn), and
  `cockpit_view.py` (subject/customer resolution, the 4-source Cockpit
  view composition, and document-upload validation + its chat
  confirmation side effect). Each router's own remaining job is calling
  the extracted function once and mapping its domain exception to an
  HTTP status — that mapping stays in the router; it's the API layer's
  actual job, not business logic. Router line counts: 333→218
  (`agents_router.py`), 129→73 (`sections_router.py`), 140→112
  (`cockpit_router.py`), 42→33 (`my_day_router.py`), 53→27
  (`vault_index_router.py`). Verified live against real data for every
  extraction: sections still compose `agent_ids` correctly, an
  out-of-window `day` still 400s, a blocked section delete still 409s
  with correct real agent names, a real Cockpit view still composes all
  4 sources, a vault-index rebuild still triggers both real paths, an
  unknown-agent chat stream still 404s before reaching the stream logic.
- refactor: `agents_map_adapter.py`'s own hand-rolled real-agent
  composition (a second, parallel derivation of type/section/
  depends_on/is_background_agent straight from the Registry) is now
  delegated to `AgentManager` — new shared
  `business/core/agents/agent_presentation.py` (`to_summary_dict`/
  `to_detail_dict`) replaces the two independent copies of this same
  dict-shaping that used to live separately in `agents_router.py` and
  `agents_map_adapter.py`. `list_agent_summaries()`/`get_agent_detail()`
  now exclude Hub agents too (same reasoning as the map — a Hub isn't a
  real @mention/routing target), fixing the same class of duplication
  for Cockpit's own moderator/mention-resolution system
  (`business/cockpit/chat_turn.py`/`moderator.py`) that `GET /agents`
  was already fixed for. Deleted the now-fully-dead per-field helpers
  this exposed (`_is_background_agent`/`_agent_display_name`/
  `_section_id_by_name`/`_agent_section`/`_agent_section_id`/
  `_agent_type`/`_agent_depends_on`/`_skill_to_capability`); Pipeline
  composition (`_visual`/`_short_excerpt`/`_pipeline_to_summary`) is
  unchanged, still this file's own concern.
- feat: `AgentManager.get_expert_agents()` — every real `type: "expert"`
  Agent. `moderator.py`'s `match_customer_expert`/
  `suggest_expert_for_question`/`match_domain_experts` (all three "which
  real Expert" scans) call it directly instead of pulling the full
  agent+Pipeline roster and filtering `type != "expert"` themselves;
  `route_question` (needs the full brought-in roster, which can include
  non-Expert types) correctly stayed on the full roster. Verified live
  against real Registry/Hermes data: 15 real experts (0 hubs),
  `suggest_expert_for_question` correctly matches a real Azure-costing
  question to `azure-calculator`, `chat_turn._resolve_mention`/
  `_agent_name` resolve correctly (exact id, case-insensitive name,
  honest `None` on no match), `get_agent_detail` correct for a real
  agent/a real Pipeline/an unknown id.
- fix: the Agents Map's Hub-agent duplication (a Hub rendering both as
  its Section's own SectionHub center node AND an ordinary ring/fan
  dot) is now fixed on the backend, not the frontend. Added
  `AgentManager.get_all(*, exclude_types=None)` and a new general-purpose
  `AgentManager.get_section_agents(section_id, *, include_types=None,
  exclude_types=None)`; `agents_router.py`'s `GET /agents` now calls
  `get_all(exclude_types=["hub"])`, so a Hub agent is never returned to
  any caller as an ordinary agent in the first place. A first attempt at
  this fix lived in the frontend (a type filter in `layoutAgents.ts`/
  `SectionDrilldown.tsx`) and was fully reverted — "which agents a given
  caller should see" is business logic and belongs on `AgentManager`, not
  duplicated as a one-off UI filter. Verified live: `GET /agents` returns
  24 (21 real agents + 3 pipelines, 0 hub-type, down from 28), all 9
  backend tests pass, and the Sales section drilldown's DOM shows only
  its 2 real agents in the ring with no hub-type `agent-node` while the
  `hub-node hub-node--large` center node still renders correctly.
- feat: creating a Section now creates its own Hub Agent —
  `SectionManager.create()` calls `AgentManager.create()` (a deliberate
  Manager-to-Manager exception, lazily imported to avoid a circular
  import) to make a `type="hub"` agent, then links it back as the
  Section's own `fallback_agent_id`. `AgentManager.create()` also
  defaults a new agent's `depends_on` to its Section's Hub agent when
  omitted, so every new agent is a specialist of its Hub by default.
  Retroactively fixed the 4 pre-existing hand-built hub agents
  (`customer-hub`/`industry-hub`/`technology-hub`/`sales-hub`), which
  were all `type: worker` and mis-placed under `data-gatherer` — now
  correctly typed `hub` and placed under their real sections. Verified
  live end-to-end (scratch section→hub→specialist chain, zero leftover
  artifacts) and against real production data (`GET /sections` shows
  correct per-section counts summing to the same 28 total agents,
  `customer-hub` renders as type HUB on the Agents Map).
- feat: `Pipeline` now links to its real Hermes cron job —
  `cron_job_id`/`cron_profile_id` (stored on the 3 real pipeline JSON
  files) compose live `cron_enabled`/`cron_schedule`/`cron_last_run_at`/
  `cron_next_run_at`/`cron_last_status` via `HermesCron`, replacing what
  used to be unstructured prose inside `description`. `HermesCron`
  (`app/hermes/cron.py`) gained an optional `profile_id` param on all 4
  methods — confirmed live that not every cron job lives on the default
  profile (`meeting-capture-recurring` runs under `meeting-prep-agent`'s
  own cron), backward compatible with the existing caller. Verified
  live: all 3 pipelines resolve correct real cron status including the
  cross-profile case, `GET /agents` unchanged (28 total), Agents Map
  unchanged in the browser.
- feat: `AgentManager.regenerate_specialists_section(agent_id)` —
  generates/updates a marker-delimited `## Your own specialists` block
  in an agent's real SOUL.md, listing every agent whose `depends_on`
  points at it, matching the exact hand-written relay format
  (`terminal(hermes -p ...)` template + one bullet per child). Explicit,
  separate call only — never automatic inside `create`/`update`.
  Idempotent (safe to re-run as `depends_on` changes; a re-run with the
  same children is byte-identical; zero children removes the block
  entirely). Verified live against disposable scratch agents through
  generate/re-run/shrink/remove, zero leftover artifacts.
- fix: `azure-expert`'s real SOUL.md now instructs it to chain a real
  architecture from `azure-enterprise-architect` into `azure-calculator`
  for sizing when a request needs both design and cost — previously the
  two specialists were relayed to independently with no hand-off.
  Verified against the real Hermes profile file (180 → 190 lines,
  rest byte-identical).
- refactor: every real agent's Registry data is now ONE file,
  `Agent.json`, replacing the separate `Agent-config.json`/
  `Agent-visual.json` pair — `AgentVisual` deleted from
  `registry/schemas.py` (icon/color are now plain fields on
  `AgentConfig`; confirmed nothing real ever read the Registry's own
  `Agent.visual`, same as the earlier `Agent.soul` finding).
  `loader.py`/`AgentManager`/`agent_visual_registry.py` all updated to
  read/write the merged file. All 21 real agent folders migrated live
  (old two-file format merged into `Agent.json`, old files deleted) —
  confirmed the Registry genuinely fails to boot beforehand, then boots
  clean afterward with real data intact. `tests/test_registry_loader.py`
  fixture updated to match. Verified live: `GET /agents` unchanged (28
  total), a real icon/color PATCH round-tripped correctly, Agents Map
  unchanged in the browser.
- fix: `GET /sections` now returns real `agent_ids` per section —
  `sections_router.py` composes `AgentManager.get_all()` grouped by
  `section_id` (cross-manager business logic, not something
  `SectionManager` computes itself). The dead `assignments` dict (empty
  since 2026-08-27) is fully removed from `SectionManager`'s persisted
  state, not just unused. `delete_section`'s blocking check upgraded to
  use `AgentManager`'s fuller picture (catches an agent not yet migrated
  into the Registry) ahead of `SectionManager.delete()`'s own
  Registry-only check, which still runs underneath as an independent
  safety net. Verified live: Settings → Sections shows real "N agent(s)
  assigned" counts for the first time.
- feat: `PipelineManager` (`app/business/core/pipelines/pipeline_manager.py`)
  built, read-only. Folds in and replaces
  `data_access/system/pipelines/{registry,schema}.py` (both deleted —
  zero write methods, exactly one real caller). `Pipeline.section` (a
  raw Section name string on disk) is now `Pipeline.section_id`,
  resolved once at read time via `SectionManager` instead of every
  caller re-resolving it. `agents_map_adapter.py` migrated onto it at
  all 5 of its real pipeline call sites. Verified live: `/pipelines`,
  `/agents` (28 total, unchanged), `/agents/{id}/jobs`, and
  `/agents/{id}` detail for a pipeline all correct; Agents Map unchanged
  in the browser.
- feat: `agents_router.py` migrated onto `AgentManager`. `GET /agents`
  composes real agents (via `AgentManager.get_all()`) plus Pipelines
  (via a new small `agents_map_adapter.list_pipeline_summaries()`
  wrapper — Pipelines aren't covered by `AgentManager`). `GET
  /agents/{id}`/`PATCH /agents/{id}` try `AgentManager` first, falling
  through to the pre-existing Pipeline-aware path unchanged for a
  Pipeline id. `AgentDetail.provider_id`/`provider_name` now reflects
  `managed_by` (`"hermes"`) instead of Hermes' raw provider string, per
  the already-approved schema change. Verified live: 25 real agents + 3
  pipelines = 28 total (matches exactly), the Agents Map is unchanged in
  the browser, PATCH works for both a real agent and a Pipeline id.
- feat: `AgentManager` (`app/business/core/agents/agent_manager.py`) built
  out, read and write sides. `get_all`/`get_by_id` compose a real `Agent`
  from Hermes profiles (name/description/model/reasoning_effort/skills/
  the real SOUL.md text as `prompt`), the Registry (section_id/type/
  depends_on/is_background_agent), and `agent_visual_registry.py`
  (icon/color, kept as its own module, not folded in).
  `create`/`update`/`delete` wire up real `HermesClient`/`HermesProfiles`
  library primitives (`create_profile`/`delete_profile`/
  `describe_profile`/`update`/`write_soul`) that existed but had zero
  callers until now, plus a new writer for `Agent-config.json`/
  `Agent-visual.json`/`soul.md` (nothing in the app ever wrote these
  before). `type` gained a 4th value, `hub` (the agent representing a
  Section) — `data_access/registry/loader.py`'s fail-loud type
  validation and `registry/schemas.py` updated to accept it, otherwise
  the Registry would fail to boot on the first real hub agent.
  `working_mode` (`autonomous`/`human_in_loop`) and `managed_by`
  (`hermes`) are real fields now, not fabricated. `prompt`+`guardrails`+
  `scope` compose into one real Hermes `SOUL.md` write. Verified live:
  created/updated (including a real section move)/deleted a disposable
  Hermes profile end-to-end, confirmed zero leftover artifacts in both
  the real Hermes profile directory and the Registry tree afterward.
- refactor: deleted `business/agent_prompts.py` (fully dead, zero
  callers) and `vault_writer.py`'s `load_agent_scope`/`save_agent_scope`/
  `load_all_agent_scopes` (zero callers) — both disconnected fragments
  of the prompt/guardrails/scope concept `AgentManager`'s SOUL.md
  composer now actually implements.
- feat: `SectionManager` (`app/business/core/sections/section_manager.py`)
  is now the sole gateway for Section data — `Section` gained the
  missing `agent_ids` field, `GET /sections` now returns typed
  `list[Section]` (real OpenAPI schema instead of `dict`), and
  `POST`/`PATCH`/`DELETE /sections/{id}` were rewired through the
  Manager too. The old standalone `business/section_registry.py` was
  folded into `SectionManager` and deleted — its 3 real callers
  (`sections_router.py`, `cockpit/moderator.py`,
  `hermes/agents_map_adapter.py`) now go through `SectionManager`
  instead. `SectionManager` owns its own `agent_sections.json` I/O
  directly rather than routing through `vault_writer.py` (a retirement
  target — new Managers shouldn't deepen its reach), and imports
  `tag_slug` from its real home (`app.obsidian.tags`). Dropped, not
  ported forward: the dead self-heal loop in `_load_state` and
  `get_agent_section`/`set_agent_section` (zero callers). Verified
  live: all 6 real sections still load correctly through the relocated
  file I/O, Agents Map renders unchanged, all 9 backend tests pass.
- refactor: deleted the last 2 dead root-level `data_access/` files —
  `email_staging.py` (Outlook-fetched-but-not-yet-processed email
  staging store, orphaned once the old email-capture pipeline was
  removed) and `upload_storage.py` (ephemeral chat-attachment
  upload/summarize buffer, `REQ-SB-28-US-01`, superseded by Cockpit
  Documents' `vault_manager.py`-based persistent upload) — both
  confirmed zero real callers anywhere in the app. `data_access/` root
  now holds only `vault_writer.py` (the live, heavily-used JSON state
  store) alongside its already-organized `registry/`/`system/`/
  `templates/`/`vault/` subpackages.
- fix: `tests/test_registry_loader.py`'s `_isolated_vault` fixture only
  monkeypatched `settings.vault_path`, but `loader.data_root()` reads
  `settings.second_brain_data_path` (decoupled from `vault_path` in an
  earlier pass) — so 8 of 9 tests in that file silently ran against the
  real vault's real data instead of an isolated temp tree. Fixture now
  also monkeypatches `settings.second_brain_data_path` to the temp dir;
  all 9 tests pass, verified the real vault received no writes from the
  run.
- refactor: "fully agentic" cleanup pass — deleted every Second-Brain-native
  orchestration mechanism now superseded by Hermes' own native
  scheduling/dispatch/agent-orchestration. Removed the in-process `/mcp`
  MCP tool server (`api/mcp_server.py` + its 6 registered tools,
  `vault_write_tools.py`, `scope_query_tools.py`, `vault_query_tools.py`),
  the custom skill-dispatch registry (`skill_tools.py`, `skill_registry.py`,
  `agent_schedule_registry.py`), the LangGraph-based `agent_orchestration/`
  package, the now-vestigial `scheduling/` package
  (`capture_scheduler.py` + `default_schedules.json`, orphaned once its only
  reader was gone), the dead Compass/Anthropic/Outlook DAL clients
  (`data_access/{compass,anthropic,outlook_com}_client.py`), and a further
  cascade of orphaned business-layer modules confirmed to have zero live
  callers app-wide (`project_customer_synthesizer.py`,
  `todo_classification.py`, `email_classification.py`,
  `thread_summary_backfill.py`, `knowledge_gap_tracking.py`,
  `working_mode_registry.py`, `pending_approval_registry.py`,
  `vault_filing_expert.py`, `agent_chat.py`, `background_agent_registry.py`,
  `agent_keywords.py`, `scope_registry.py`,
  `cockpit/{threads,person_note_proposals,attachments}.py`) — 26 files plus
  1 package, all confirmed dead via a full reachability trace, not import
  proximity. `main.py`'s lifespan no longer enters the `/mcp` mount's
  session manager or dispatches default schedules; `obsidian/permissions.py`
  dropped its now-dead `_CALLER_ALLOW_LISTS` entries for the deleted
  modules.
- fix: `data_access/registry/loader.py`'s boot `"checking_hermes"` stage
  was calling `system_health.mcp_mount_reachable()` — a leftover that
  actually probed the backend's own (now-deleted) `/mcp` mount, never
  Hermes itself. Replaced with a real reachability check against
  `settings.hermes_base_url`. `GET /system-health` no longer returns
  `mcp`/`scheduling` keys (both backed by deleted modules);
  `SystemHealthPage.tsx` dropped its "MCP / Agent-orchestration path" card
  and "Scheduling" section to match — Hermes' own reachability is already
  covered by that page's separate "Hermes Status" tab.
- fix: three follow-up bugs found earlier this session, fixed directly.
  (1) `hermes_client.py`'s only session-token mechanism (scraping
  `window.__HERMES_SESSION_TOKEN__` out of `GET /`'s HTML) silently
  broke for EVERY live Hermes chat feature whenever Hermes ran via
  `hermes serve` (headless) — confirmed via the real Hermes source
  (`hermes_cli/web_server.py`) that the session token itself is always
  generated (`_resolve_session_token()`), it's just no longer embedded
  in HTML in headless mode; that same function reads
  `HERMES_DASHBOARD_SESSION_TOKEN` from the environment if set, instead
  of generating a random one. Set a fixed value there (Hermes' own root
  `.env`) and the matching `HERMES_API_KEY` in this app's own `.env` —
  `hermes_client.py`'s existing manual-override path picks it up
  directly, no HTML scraping ever needed again. Verified live: the
  static key authenticates correctly against a real protected endpoint
  through genuinely headless `hermes serve`. (2) `vault_manager.py`'s
  `find_by_id`/`find_by_filename`/`find_in_folder` fallback scan now
  excludes `_`-prefixed (archived) folders and tolerates an unreadable
  file instead of crashing the whole scan — fixes the dormant unscoped-
  call crash found live under `Work/_archive/`, propagated to all 17
  real deployed locations. (3) `my_day.customer_from_tags` now only
  matches `customer/`-prefixed tags — fixes a real Thread tagged both
  `partner/g42` and `customer/mubadala` resolving to "G42" instead of
  "Mubadala" in the Inbox Cockpit's own info panel; verified live.
- Found while verifying these fixes (not a Second Brain code bug —
  flagging for awareness): port 8001 (the real backend port) ended up
  with zombie TCP LISTEN entries after repeated backend restarts this
  session — three independent process tools (`Get-Process`,
  `Win32_Process`, `tasklist`) all agree the owning PIDs no longer
  exist, but Windows hasn't released the socket. Verification for fix
  (3) had to move to a scratch port (8002) to get a clean result. A
  reboot would clear this (this machine has needed one before this
  session for a similar reason); not attempting any system-level
  network reset without asking first.

- feat: Replicated the Phase 5 Section fallback agent pattern to
  Technology, Sales, and Industry — three new real Hermes profiles
  (`technology-hub`, `sales-hub`, `industry-hub`; `--no-skills`,
  deliberately read-only, cloned config from `research-agent` same as
  `customer-hub`), each with a SOUL.md tailored to its own folder's real
  structure (`Work/Technology/<Tech>/<Sub-topic>/`,
  `Work/Sales/<Deal>/`, `Work/Industries/<Industry>/<Sub-vertical>/` —
  hierarchical KB-reference docs, not per-entity hub folders like
  Customer's own `<slug>/index.md`/`log.md`/`captures.md` shape) plus
  the matching per-folder structural index. `fallback_agent_id` wired on
  all three Sections. **Live routing is deliberately NOT wired for
  these three yet** — confirmed live before building: unlike Customer
  (`customer/<slug>` tags on real Meetings/Threads), Technology/Sales/
  Industry tags (`technology/<slug>`, `sales/<slug>`, `industry/<slug>`)
  exist only on each entity's own hub note, never on a conversation that
  discusses it — there is no real "this conversation is about Technology
  X" signal to key routing off yet (operator, confirming scope: "Build
  the profiles now, routing later"). Verified `technology-hub` live via
  `@mention` (the same underlying chat mechanism automatic routing will
  eventually use, since automatic fallback has nothing to trigger it
  yet) — asked about Azure architecture, got back a complete, accurate
  answer citing 7 real reference notes under
  `Work/Technology/Azure/Architecture/` by real path and real content.
  `sales-hub`/`industry-hub` built identically, not independently
  re-verified given the pattern is now proven twice (Customer's
  hub-folder shape, Technology's hierarchical-KB shape).

- feat: Phase 5 of the vault structural index — Section fallback agent,
  built and verified live end-to-end with a real reply. Sections gained
  a `fallback_agent_id` field (the Hermes profile that answers when a
  mentioned entity has no dedicated Expert), editable from Settings >
  Sections. New moderator function `match_customer_fallback_agent`
  (`moderator.py`) generalizes the existing `match_customer_expert`
  pattern: given a conversation's own subject note, if it's tagged to a
  Customer with NO dedicated `<slug>-expert` registered, returns the
  Customer Section's own configured fallback agent instead — never
  fabricated, `None` whenever the subject isn't Customer-tagged, a
  dedicated Expert already covers it, or no fallback is configured.
  Wired into `chat_turn.py`'s live routing at BOTH points where it
  previously fell straight to the hardcoded `_RESEARCH_AGENT_ID`: the
  "roster has agents but none match" case, and — found live, a real gap
  in the first wiring — the "no Experts brought in yet" case too, since
  a brand-new conversation about an uncovered Customer is the exact
  motivating scenario ("only a few that are Important"). Created a real
  new Hermes profile, `customer-hub` (`hermes profile create ...
  --no-skills`, no bundled write-capable Skills — deliberately
  read-only), with a SOUL.md pointing it at the Customer folder's own
  structural index plus direct vault reads, no new Skill needed.
  Verified live: asked a real question about Mubadala (a real Customer
  with no dedicated Expert) on a real Thread with no roster yet —
  routed correctly to `customer-hub`, which returned a complete, real,
  accurate answer citing `Mubadala.md`'s actual content (financials,
  affiliates, named people).
- Found and fixed a real compatibility gap along the way (not part of
  this feature, but blocking all live verification): `hermes serve`
  (the documented headless way to run Hermes) now returns 404 for
  `GET /` — Hermes' own web UI is deliberately disabled in that mode —
  which silently breaks `hermes_client.py`'s only session-token-fetch
  mechanism for EVERY live Hermes chat feature in this app, not just
  new ones. Worked around by running `hermes dashboard --no-open`
  instead (same port/backend, web UI enabled) to unblock verification;
  a real fix (giving the backend a token-fetch path that works against
  a genuinely headless instance) is flagged as a separate follow-up,
  since `hermes dashboard` isn't documented as a supported way to run
  this app's own production chat backend long-term.
- Found (not fixed here — flagged for follow-up) while live-testing:
  the Inbox Cockpit's own "Customer" info field can show a Partner's
  name instead of the real Customer when a Thread carries both tags —
  confirmed live, root-caused to `my_day.py`'s `customer_from_tags`
  matching the first tag found in a dict merging Customer AND Partner
  names together, with no namespace filtering (unlike `moderator.py`'s
  own correct `_subject_customer`, which does filter for `customer/`).

- feat: Phase 4 of the vault structural index — Section → folder
  mapping, built and verified live. Sections gained a real `folders:
  string[]` field (`section_registry.py`, `PATCH /sections/{id}`) — a
  Section can own zero, one, or several top-level `Work/` folders, no
  hardcoded table. Settings > Sections now shows a checkbox list of
  every real folder (reusing the same live list Vault Overview/Index
  Filtering already fetch) in each Section's expanded row, toggling
  instantly (same immediate-apply pattern as Icon & Color). The
  Registry's own `Section.json` disk mirror now includes `folders` too
  — the real reason this field exists: a future Section fallback agent
  (Phase 5) is a standalone Hermes-side process with no way to call this
  backend's API, so it reads its own folder scope straight off this
  file, same pattern already established for Index Filtering and
  `build_vault_index.py`. Mapped live: Customer→Customers,
  Technology→Technology, Sales→Sales, Industry→Industries;
  Librarian/Data Gatherer intentionally left empty (workforce roles, not
  content domains); Partners intentionally left unassigned for now
  (operator: "Don't include Partners for now").

- feat: Phase 3 of the vault structural index — capture-pipeline cutover,
  built and verified live. `find_by_id`/`find_by_filename`/
  `find_in_folder` (`Hermes-Provisioning/shared/vault_manager.py` and its
  7 byte-identical copies) now try the new per-folder index first, but
  a stale or missing index can only ever make a lookup SLOWER, never
  WRONG: a "not found" result — from a missing index file, an unindexed
  scope, or the id genuinely not being in the index — always falls
  through to the original `rglob` scan, and even an index HIT is
  verified with a real `is_file()` check before being trusted (catches a
  since-moved/deleted indexed entry). `ingest_meeting.py` is the only
  confirmed real, live, active external caller (all 3 call sites,
  correctly folder-scoped) — verified live against the real vault: a
  real meeting id resolves via the fast path in ~0.002s (was ~0.06s+ for
  the equivalent scoped scan), a genuinely-missing id still correctly
  falls through and returns `None`. Redeployed to all 17 real, active
  deployed locations (11 meeting-capture profiles, azure-kb-writer,
  compass-kb-writer, capture-files, capture-notes, research-kb-writer,
  vault-index), each verified byte-identical to source, including a
  final check run directly from the actual deployed
  `meeting-prep-agent` copy (not just the repo source).
- Found (not fixed here — flagged for follow-up) while testing the
  fallback path: `find_by_id`/`find_by_filename` called unscoped
  (`note_name=None`) crashes on a real file under `Work/_archive/` —
  confirmed live. Currently dormant (no real caller passes
  `note_name=None` today), pre-existing, unrelated to this change.

- feat: Phase 2 of the vault structural index — cron wiring, built and
  verified live end-to-end. New Hermes Skill
  `Hermes-Provisioning/skills/vault-rebuild/vault-index/` (SKILL.md +
  `build_vault_index.py`/`vault_manager.py` scripts, deployed to the
  default/Primary profile, whose gateway is confirmed currently running
  — `meeting-prep-agent`'s own gateway, hosting the existing
  `meeting-capture-recurring` job, was found down during this work).
  Registered as `vault-index-rebuild`, `every 30m`, `--deliver local`.
  `hermes cron run vault-index-rebuild` (job triggered by *name*, no
  need to look up its hex id) confirmed working both directly and via a
  new subprocess trigger added to the existing `POST /vault-index/rebuild`
  endpoint — clicking the app's own "Rebuild index" button now refreshes
  BOTH the backend's in-memory index (fast, synchronous, unchanged) and
  this new disk index (fire-and-forget — an agent-mediated run took
  ~60s in live testing, confirmed via `generated_at` advancing after the
  triggering process exited, so the HTTP response never blocks on it).
  One real rebuild path, two triggers (schedule + button), matching the
  plan's own "no drift" goal.

- feat: Settings > Vault > Index Filtering — real, editable config for
  which top-level `Work/` folders the agent-facing structural indexer
  covers, instead of it walking every folder unconditionally (operator:
  "Index Filtering a new settings feature... instead of Hardcoding
  files"). New `vault_index_config.py`/`GET,PATCH /vault/index-config`
  on the backend (folder list reuses the existing `get_overview()` live
  folder discovery, no re-scan); `build_vault_index.py` reads the same
  `.second-brain/index_config.json` file directly off disk (no backend
  dependency, matching its own standalone design) before deciding which
  folders to walk. A folder with no saved preference defaults to
  included, so this is fully backward-compatible with Phase 1's original
  "index everything" behavior. Verified live end-to-end: excluding
  "Files" through the UI removed `Files.json` from the generated index
  and dropped the total note count by exactly 4; re-including it
  restored both.

- feat: Phase 1 of the vault structural index
  (`Implementation/Plans/2026-08-27-vault-index-and-section-agents.md`)
  built and verified live: `Hermes-Provisioning/shared/build_vault_index.py`
  — a standalone (stdlib-only, no backend dependency, same deployment
  model as `vault_manager.py`) script that walks `Work/` once and writes
  one JSON file per real top-level folder plus one whole-vault JSON,
  under `.second-brain/index/`. Mirrors the backend's own three exclusion
  rules exactly (OKF-reserved filenames, Thread-sidecar files, any
  `_`-prefixed folder anywhere in the path) so this index doesn't
  resurface an archived duplicate. Verified against the real vault:
  12 of 14 folder counts matched the backend's own live index exactly
  (People/Technology/Tasks/Meetings/Research/Files/Notes/Sales/Templates/
  Initiatives all identical); Partners/Customers/Threads/Industries
  differed because of a real, pre-existing, unrelated bug this
  cross-check surfaced in the backend's own index (see next entry) — this
  new index's higher counts are the correct ones.
- Found (not fixed here — flagged for follow-up): `vault_indexing.py`'s
  `rebuild_index()` keys its whole-vault dict by bare filename stem
  globally, so any two notes anywhere in the vault that share a filename
  silently overwrite each other. Confirmed real: the same person's note
  linked under both a Customer's and a Partner's own `People/` folder
  (`zishan.naviwala@core42.ai.md`, et al.), and a repeated per-hub
  subsection filename (`Market Relevance.md`, 14 occurrences) — both
  collide and undercount. Affects the React frontend's own Vault
  Browser/search today, not just this new index. Out of scope for the
  index-and-Section-agents plan; spawned as a separate follow-up task.

- fix: two rendering bugs in the just-added collapsible-row pattern
  (Settings > Sections, Settings > Vault > Entities), found live
  (operator: "The Icon in Industry is wrong, and the Title of the
  Section... in the entities in vault is very dark not visible"). (1) A
  section's `icon` field can hold a VisualPicker *picker id* (e.g.
  `compass`), not necessarily its real Material Symbols ligature name
  (e.g. `explore`) — Industry was set to the id `compass`, which isn't a
  real ligature, so it rendered as literal text instead of a glyph.
  Fixed by resolving through the existing `getVisualIconName()` helper
  (already used by `AgentNode.tsx`/`SectionHub.tsx` for the exact same
  id-vs-ligature gap) instead of rendering `section.icon` raw. (2)
  Wrapping each collapsible row's header in a plain `<button>` picked up
  the browser's own default button text color instead of the app's theme
  text color — invisible-dark against this app's dark surfaces. Fixed by
  adding `color: inherit` to both buttons.
- refactor: Settings > Sections redesigned to match the rest of the new
  Settings structure — rows collapse to icon/name/agent-count by default
  (`chevron_right`/`expand_more`), expanding to Name, Description, and
  Icon & Color editors, all with persistent labels via a new shared
  `Field` component (`features/settings/Field.tsx`, extracted from the
  Vault > Entities page so both share one implementation). Icon/Color
  editing reuses the existing `VisualPicker` component and
  `PATCH /sections/{id}` endpoint verbatim — the same ones the Agents
  Map's own `SectionDetailPanel.tsx` already uses when you click a Hub —
  no new backend code, no duplicate icon/color picker. Verified live:
  icon and description edits round-trip to the real `agent_sections.json`
  store and back; both reverted after testing.

- fix: Cockpit Documents upload confirmation hardcoded "this meeting"
  regardless of `subject_kind` — wrong for the Inbox Cockpit (email/
  Thread subjects). Found verifying the Documents feature across Meeting
  and Inbox Cockpits after the earlier meeting-capture/routing fixes;
  now reads "this email" for `subject_kind == "email"`.
- fix: Inbox Cockpit's People/Received/Customer fields were all reading
  frontmatter keys a real Thread never actually carries — People always
  showed 0 (looked for a `recipients` field that doesn't exist; a
  Thread's real participants are wikilinks in its own `## Related`
  section instead), Received was always blank (`received` vs. the real
  `last_message_at`), Customer was always blank (a raw `customer` field
  vs. the real `customer/<slug>` tag). `people.py` now reads `##
  Related` for email/Thread subjects (`type: "Person"` filtered, so a
  linked Customer/Partner hub is never mistaken for a person);
  `cockpit_router.py` now resolves a real Customer name from the tag
  server-side (reusing `my_day.py`'s own existing tag→hub-name lookup,
  now made public); `InboxCockpitPage.tsx` points at the real
  `last_message_at` key. Verified live against a real Thread; a Meeting
  Cockpit re-checked immediately after, confirmed unaffected.
- refactor: Global App Settings redesigned from a flat, unstyled stack
  of two cards into a Google-style icon-card landing grid
  (`SettingsPage.tsx`) with six flat sibling drill-down routes —
  `/settings/{system,sections,providers,vault,config,ui}` — mirroring
  My Day's own landing-grid/sub-page convention. `SectionsCard`/
  `ProvidersCard` moved unchanged onto their own new pages
  (`SettingsSectionsPage.tsx`/`SettingsProvidersPage.tsx`); System/
  Vault/Config/UI ship as honest "Not built yet" stubs — no
  functionality was added or changed, only presentation. New
  `.settings-grid`/`.settings-card*` rules in `settings.css` give the
  grid its own deliberate, smaller type scale (15px card titles) rather
  than inheriting the blunt global `h1`/`h2` sizing (18–24px) that read
  as "too big and ugly." Operator-scoped: agent-level settings are
  explicitly deferred to a later pass.
- feat: Settings > System is now real, live, and editable — Hermes
  System URL, Hermes Deployment Folder, App Database Folder
  (`.second-brain`), Vault Location, and CORS Allowed Origins, each shown
  with a live status check (reachable/exists/writable) and an on-demand
  Test button, backed by a new `GET/PUT /settings/system`,
  `POST /settings/system/test/{field}` API (`system_settings.py`). Saving
  writes to `.env` and shows "Restart to apply"; a paired
  `POST /settings/system/shutdown` gracefully stops the backend process
  (Windows-safe via `signal.raise_signal`, not `os.kill`, which silently
  bypasses Python signal handlers on Windows) so the operator can restart
  it themselves.
- refactor: `second_brain_data_path` is now a real, independent
  `config.py` setting (defaults to the historical `<vault>/.second-brain`)
  instead of being hard-derived from `vault_path` at ~30 call sites across
  5 files (`vault_writer.py`, `vault_migration.py`, `upload_storage.py`,
  `email_staging.py`, `registry/loader.py`, plus `vault_manager.py`'s own
  Templates lookup). Changing it from the System settings page performs a
  real folder move (verified against temp dirs: nested content preserved,
  refuses a non-empty destination, refuses self-nesting, no-ops on an
  unchanged path) rather than silently leaving existing registry/chat/
  upload data behind at the old location. `main.py`'s CORS origin list is
  now sourced from `settings.cors_allowed_origins` instead of hardcoded.
  Known, disclosed limitation: Hermes Skills (their own separate,
  physically-copied `vault_manager.py`) have no knowledge of this backend
  setting and will keep reading/writing Templates at
  `<vault>/.second-brain/` regardless — only this backend's own data
  follows a relocated App Database Folder.
- feat: Settings > Vault now has a real two-panel layout (persistent left
  nav — Overview / Entities / Templates / Index Builder — plus content,
  `VaultSettingsNav.tsx`) with three working sections:
  - **Entities**: a real CRUD UI over the Customer/Partner discovery
    registry (`vault_entities.py`, `GET/POST/PATCH/DELETE /vault/entities`)
    — approve (mark reviewed), edit Aliases/Affiliate of/Domain, move
    between Company/Partner, delete, add new. Parses/renders the exact
    same format the company-review Hermes Skills already use (ported
    byte-for-byte from `find_new_entities.py`'s own
    `parse_entities`/`render_entities`), verified live: 35 real entities
    (24 Companies/11 Partners) load correctly, a real edit round-trips to
    disk and back. Redesigned after live feedback (operator: "too long...
    hard to find newly added entities", "When you add the text I don't
    have a title for the textbox", "make Each Company Collapsed by
    default, Separate customers and partners, have a Separate Section
    called need review on top"): every field now has a persistent label
    instead of a placeholder that vanishes once filled in; rows collapse
    to just name + status by default, expanding to the editable fields
    only on click; a new **Needs Review** group (all `Ignore: Yes`
    entries — where a freshly-discovered entity always lands) sits above
    Companies/Partners, which now only list already-reviewed entries —
    no entry appears twice; each group shows newest-appended-first (entries
    are only ever appended, never reordered, so this is real file order,
    not fabricated); added a live search-by-name-or-domain filter.
- fix: Delete on an Entities.md row is now a soft delete (new `Deleted:
  Yes` field), not a real removal. Found live (operator: "sharepoint and
  Teams should be delete but they will keep surfacing and I know they
  will never be a company") — a hard delete removes the row's own Domain
  from `find_new_entities.py`'s `_already_tracked_domains` check, so a
  noise domain gets rediscovered on the very next scan. `delete_entity()`
  now sets `Deleted: Yes` + `Ignore: Yes` and leaves the row in place;
  `list_entities()` filters `Deleted: Yes` out, so it's invisible in the
  UI despite staying on disk. Added the same field to both canonical
  Hermes parse/render copies (`find_new_entities.py`,
  `create_companies_partners.py` — these are independent, non-shared
  copies of the same logic, both needed the fix) plus
  `build_entities_report.py` for schema consistency, then redeployed to
  all 11 real profiles (verified byte-identical after). No change needed
  to hub-creation logic — `Ignore: Yes` alone already skips a
  Deleted/Ignored entry there. Verified live: deleted Sharepointonline
  and Teams through the UI, confirmed both vanish from the app while
  their real rows (with `Deleted: Yes`) and Domain fields remain on disk.
  - **Overview**: total notes indexed, last rebuild time, and a per-Work-
    folder note-count breakdown (`vault_indexing.get_overview()`), plus a
    Rebuild index button reusing the existing `POST /vault-index/rebuild`.
  - **Templates**: read-only listing of every `Template.json` under
    `.second-brain/data/Templates/` (`vault_templates.py`,
    `GET /vault/templates`) — note-shape policy, per-section write
    access, frontmatter defaults.
  - **Index Builder**: an honest stub — still being designed (per-vault
    and per-Section `index.md` generation), not built yet.
- refactor: `Work/Entities.md` relocated to
  `.second-brain/Settings/Entities.md` (operator: "it should be in the
  Settings folder... lots of Agents are Accessing this file in Hermes so
  you need to check"). Real file move, verified byte-identical before the
  original was removed. Updated all 4 Hermes scripts that hardcode this
  path (`find_new_entities.py`, `apply_entity_decision.py`,
  `create_companies_partners.py`, `build_entities_report.py`) plus every
  SKILL.md prompt referencing "Work/Entities.md", then redeployed to all
  11 real Hermes profiles that actually have the company-review
  subskills installed (confirmed via each profile's own
  `skills/company-review/<subskill>/` — not every profile with a
  `company-review` folder has them, some only have the unrelated
  `track-opportunities` skill there). Verified byte-identical against
  source across all 11 after redeploy.

- feat: `vault_manager.py` — the vault-writer standardization design
  (`Implementation/Plans/2026-08-25-vault-writer-standardization.md`)
  built and verified. New `Hermes-Provisioning/shared/vault_manager.py`:
  a standalone (stdlib-only), template-driven vault read/write engine —
  `find(by=id|filename|folder)`, `create`, `update`, `get_section`,
  `modify_section` — replacing the near-byte-for-byte-duplicated
  primitives (slugify, frontmatter format/parse, named-section find/
  replace/append, unique-path collision avoidance) independently
  reimplemented across `create_opportunity.py`, `apply_thread_review.py`,
  `capture_file.py`, and `vault_lib.py`. Reads `Template.json` files from
  the same `data/Templates/<id>/` location the RegistryLoader already
  established (REQ-SB-80) — a template controls `note_name`/filename
  shape, `on_existing_title` (`update_section` vs `always_new`),
  `on_missing` (`create` vs `error`), and per-section write access
  (`machine_write` vs `user_edit`, enforced centrally by `modify_section`
  rather than trusted per-script). Deployment model: the file gets
  physically copied into a Skill's own `scripts/` folder (self-
  containment preserved — no dependency on Second Brain's backend being
  up), same "prepare here, apply there" workflow the rest of
  `Hermes-Provisioning/` already uses; not yet copied into any real Skill.
  13 new pytest cases (`Hermes-Provisioning/shared/tests/
  test_vault_manager.py`) lock in every scenario also verified live via
  the real CLI against a scratch vault: hierarchical `note_name`
  placement, overwrite-on-same-title with no duplicate, never-overwrite
  with disambiguated filenames, `modify_section`'s combined create-or-
  update, `on_missing="error"` refusing to auto-create, the `user_edit`
  section guard refusing a machine write, and a title rename via
  `update()` while `find(by="id")` keeps resolving the same file
  (the concrete fix for the real Meeting-rename mess named during design).

- feat: full real Meeting rebuild on `vault_manager.py` (`REQ-SB-80`'s
  first real production skill), operator-driven end to end, 2026-08-25/26.
  `Hermes-Provisioning/skills/vault-rebuild/meeting-capture/scripts/
  ingest_meeting.py` rewritten to use `vault_manager.py`'s real `id`-based
  find/create/modify_section instead of the old name-is-identity scheme
  (`vault_lib.py`'s own documented, never-fixed bug: a series stuck on a
  raw Outlook id forever once misnamed). New `meeting`/`meeting-series`
  Templates (`note_own_folder`, `note_filename_plain`, `folder_date` +
  `bump_folder_date` — a series folder now sorts by its real latest
  occurrence date while its own filename never carries a date). Deployed
  to all 11 real Hermes profiles carrying the skill; the real recurring
  cron job recreated at 30-minute cadence (down from 3 hours). Full real
  historical pull: 157/157 Outlook events, 0 errors, 787 attendees
  linked, 26 Threads linked, confirmed idempotent on a second full pass.
  `Work/Meetings/` is now the single, clean source of truth (the
  operator's own real, multi-scheme mess — raw-hex-id folders,
  `<date> <Subject>` folders, flat hash-suffixed files, bare-name
  recurring folders — fully superseded). `app/data_access/system/
  pipelines/meeting-builder.json` (the real Pipeline the Agents Map's
  Data Gatherer section renders) updated to match: correct 30-minute
  cadence, and the "Resolve Meeting Folder" step's own description
  rewritten to describe the real new id-based mechanism instead of the
  retired name-is-identity one. Four more real bugs found and fixed
  during the full-history run specifically (path-length truncation
  leaving a trailing space a second way, a hardcoded "Notes"
  root string in the Skill script, and a `modify_section` call missing
  its own `note_name` scope that fell back to scanning the entire
  `Work/` tree) — see `MEMORY.md` for the full account of each.

- feat: `REQ-SB-82-US-04` — Meeting/Inbox Cockpit Chat now routes each
  live question to the ONE brought-in Expert it belongs to (never a
  broadcast), falls back to the Research Agent in the background when
  none matches, and lands that fallback's reply as a threaded reply on
  the question that triggered it. New `app/business/cockpit/chat_turn.py`
  (routing/dispatch orchestration) and `app/business/cockpit/moderator.py
  ::route_question` (deterministic tokenized-overlap routing, reusing
  `US-03`'s own scoring, scoped to the brought-in roster; a genuine tie
  falls back to the Research Agent same as a zero-match). `app/business/
  hermes/chat_sessions.py::send_and_await_reply` factors the lock/
  session/timeout/discard-on-failure Hermes turn out of `agents_router.py
  ::send_chat_message` (now a thin wrapper) so both the single-agent Chat
  tab and Cockpit Chat's routed calls share one implementation.
  `chat_store.py::append_message` gives every message a real `id` and
  optional `reply_to_message_id`. New `POST /cockpit/{subject_kind}/
  {subject_note_stem}/message` endpoint. Frontend: `Cockpit.tsx`'s chat
  input is wired for the first time (previously a disabled "Chat isn't
  wired up yet…" placeholder); a threaded reply stays in its natural
  chronological position and carries a "↳ replying to: {quoted question}"
  strip rather than being repositioned; a light poll (3s × 20) picks up
  a Research Agent fallback's reply once it lands, since Cockpit Chat has
  no push/SSE mechanism. A message sent with no Experts brought in gets
  an honest system notice, never a fabricated reply. Verified live against
  the real vault/Hermes gateway (see `MEMORY.md` for the full scenario
  coverage).
- refactor: deleted `app/business/cockpit/research.py` — confirmed dead
  (zero live callers anywhere; only ever reachable from the archived
  pre-Hermes-pivot router). `threads.py`/`person_note_proposals.py` were
  investigated for the same cleanup but turned out to still be live (a
  registered skill tool writes through them) — left untouched; see
  `MEMORY.md`'s `US-04` entry and `BUG-040`.
- fix: logged `BUG-040` — `propose_person_note_update`'s Manual/
  Autonomous-dispatch proposal write has no live way to ever be seen,
  confirmed, or discarded (only wired in the archived cockpit router).
  Found while tracing the dead-code cleanup above; not fixed as part of
  `US-04` — unrelated scope.
- fix: `REQ-SB-82-US-04` live-testing fixes (operator: message stuck on
  "Sending...", no feedback on who's answering, no way to correct a wrong
  routing decision). `chat_turn.send_user_message` now dispatches EVERY
  reply — a routed Expert's, not just the Research Agent fallback's — as
  a background task via one shared `_dispatch_reply`, and returns almost
  immediately with `{"thread", "answering": {agent_id, agent_name} |
  None}` instead of blocking on the real Hermes turn. `Cockpit.tsx`
  optimistically appends the user's own message before the network round
  trip resolves, and renders an animated "X is typing…" bubble per
  in-flight reply (tracked as an array keyed by message id, so two
  messages routed to different agents each get their own indicator).
  New explicit `@mention` override (`chat_turn._resolve_mention`,
  matched against every real registered agent's id/name, not just the
  brought-in roster) always wins over the deterministic routing score —
  mentioning an agent not yet in the room brings them in first. Verified
  live: the reply-routed Expert path and the @mention override both
  render the optimistic message + typing indicator immediately and
  resolve correctly once the real Hermes turn completes.
- fix: `research-kb-writer` (`write_research_doc.py`) — research notes
  were landing as loose flat files directly under `Work/Research/`
  (operator: "if I want to do more research about a t[opic] it's gonna
  be a mess"). `note_name` is now computed per-call from the real topic
  (`Research/<topic>`), reusing `vault_manager`'s own existing
  hierarchical note_name mechanism (no engine change) — every call on the
  SAME topic string now lands in the SAME folder as a new dated file
  (never overwriting an earlier pass), while a different topic gets its
  own folder. Also added an optional `keywords` list, written into
  frontmatter when given. Deployed (script + `SKILL.md`) to the real
  `research-agent` Hermes profile. Verified live via two direct script
  calls on the same topic: both files landed in the same folder, correct
  distinct filenames, `keywords` present in each note's frontmatter.
- fix: Cockpit page layout — the Chat and Experts-roster columns now
  share a bounded, viewport-relative height and each scroll
  independently, instead of the whole page growing/shrinking as either
  column's content changed (operator: "When I start Typing in the
  Cockpit It Shrinks the window... Chat Window should be full Height and
  Same as the Agent... Scroll in the Agents Alone without the Chat").
  `.cockpit-layout` gets an explicit `height: calc(100vh - 100px)`
  (measured live) and default `align-items: stretch`; every grid child
  gets `min-height: 0`; `.cockpit-panel` (the real scroll unit) gets
  `flex:1; overflow-y:auto`. Also fixes the Chat tab specifically: the
  message thread now scrolls on its own while the title/hint/input row
  stay pinned (removed a stale `max-height: 380px` cap that no longer
  serves any purpose once the outer column is properly bounded).
  Verified live via direct DOM measurement, including confirming the
  layout's own height is unchanged before/after typing into the input.
- fix: `REQ-SB-82-US-04`'s Research Agent fallback was too eager — a
  question matching no brought-in Expert went straight to a live web
  search even when a real, not-yet-brought-in registered Expert (e.g.
  Masdar) would plausibly know more (operator: "The Research Agent
  Jumped in and Start Searching the web this is a wrong Behaviour...
  we can invite Masdar Expert... or I can go do a quick Search"). New
  `moderator.suggest_expert_for_question` checks every registered
  Expert (not just the brought-in roster) before falling back to
  research on a genuine zero-match; when a real candidate exists,
  dispatches nothing and surfaces an honest system suggestion naming
  them by name and `@mention`-able id (reusing the @mention override
  built earlier, including the explicit "search the web anyway"
  escape hatch). Along the way, found and fixed a real false-positive
  bug in the shared routing/suggestion scorer: `_OVERLAP_STOPWORDS`
  only covered domain-specific noise words, so an ordinary English
  word ("what") surviving in an Expert's own prose description spuriously
  matched the same word in a user's question — merged in a standard
  English stopword set (~90 words) to fix it for both `route_question`
  and the new suggestion check. Verified correct via direct code
  execution (with the Registry properly booted) after a genuinely
  confusing debugging detour caused by multiple orphaned backend
  processes from earlier terminal sessions still answering port 8001 —
  see `MEMORY.md` for the full account; flagged to the operator to
  clear those processes for a final live re-verification.
- feat: Cockpit Documents — upload a file or screenshot during a live
  meeting, stored attached to it (operator: "I will need to upload a
  file or a Screenshot while I am in the meeting... I don't have upload
  button in the screen"). New `app/data_access/vault_manager.py` — the
  first time Second Brain's own backend (not just a Hermes Skill) uses
  the canonical vault-write engine directly, after an initial bespoke
  writer was correctly rejected (operator: "we built a full Architecture
  to avoid creating a new file everytime"). New `app/business/cockpit/
  documents.py` uses the same real `file` Template `capture-files`
  already uses (folder-per-file + a companion Summary/Details note),
  nested under the subject's own real folder as a `Files/` subfolder
  (operator: "Do Files Folder... in the meetings") rather than a
  separate top-level tree. New `POST /cockpit/{subject_kind}/
  {subject_note_stem}/documents` endpoint (multipart upload); a system
  confirmation is appended to the live chat on success. `overview.
  related_documents` is now real data (was a hardcoded `[]`), powering
  both the Overview tab's own section and a real Documents tab
  (previously a permanent stub). Verified correct via direct Python
  execution against the real vault (bypassing the port-8001 zombie
  processes documented above): correct folder placement, correct
  frontmatter/sections matching the `file` Template.
- fix: two more Cockpit Chat UI bugs, both resolved by adopting
  `AgentChatPanel.tsx`'s already-established input pattern instead of
  Cockpit's own ad-hoc one. The Send button centering itself in an empty
  chat (operator: "when the Chat is empty, the Send Button is in the
  middle of the screen") — `.chat-thread` now always renders (empty
  state lives inside it, matching `AgentChatPanel.tsx`), instead of being
  swapped for a separately-laid-out block. No multiline support in the
  chat input (operator: "I don't have the Alt+Enter to add line we fixed
  this before") — replaced the single-line `<input>` with the same
  auto-growing `<textarea>` (Enter sends, Shift/Alt+Enter newline)
  `AgentChatPanel.tsx` already has, plus its same attach-button
  affordance, now wired to the new persistent Documents upload. Verified
  live via DOM measurement: the input row sits flush at the panel's
  bottom regardless of message count.
- fix: three real meeting-capture bugs found chasing one operator
  report ("Now all Meetings folder Showing the 2026-08-26"). (1)
  `ingest_meeting.py`'s one-time-meeting branch never passed
  `folder_date` to `vm.create()`, so a historical backfill mis-dated
  92 of 95 folders checked to the single day the backfill happened to
  run, not each meeting's own real date. (2) `vault_writer.
  list_all_note_paths()` never excluded `_archive/`-prefixed folders,
  so an archived duplicate note kept surfacing in live views (My Day
  Calendar, search) right alongside its current replacement — fixed by
  excluding any `_`-prefixed path component under `Work/`. (3) Outlook's
  own `EntryID` confirmed NOT reliable as a per-occurrence identifier
  for at least some recurring series (a live event today and an
  already-captured 2026-07-16 occurrence of the same series came back
  with the identical EntryID) — `ingest_meeting.py` used it directly as
  the occurrence's identity key, silently skipping every occurrence
  after the first-ever-captured one of any recurring series forever.
  Fixed with a synthetic `{series_id}-{start}` identity key instead
  (`event["id"]` still recorded in frontmatter, just never trusted as
  identity). Also fixed along the way: `run_full_meeting_capture.py`'s
  child processes crashed on a non-cp1252 character in real meeting
  data (Windows console codepage) — forced UTF-8 I/O on every spawned
  child. `Work/Meetings/` hard-deleted and fully recaptured twice
  (operator's own call, same approach as the original meeting-naming
  cleanup) — 191/191 events, 0 errors both passes; every folder date
  verified against its own real `start` frontmatter, zero mismatches;
  the reported duplicate/missing pair for 2026-08-27 confirmed fixed.
  All fixes plus a corrected `SKILL.md` (still described the pre-
  `vault_manager.py` folder shape) deployed to all 11 real profiles.
- fix: recreated the `meeting-capture-recurring` cron job (had vanished
  entirely — not visible under any profile's `cron list`) and started
  `meeting-prep-agent`'s own gateway, which was also not running.
  Real operational finding: cron jobs and gateways are scoped PER
  PROFILE in this Hermes install — the default profile's gateway being
  alive says nothing about another profile's own gateway state; always
  check `hermes -p <profile> cron status` for that specific profile.

- feat: `vault_manager.py`'s second and third real deployments —
  `capture-notes` (`notes-manager`) and `capture-files` (`files-manager`),
  operator: "handle the Notes files uploads." Both rewritten onto
  `vault_manager.py`'s `create()`/`modify_section()` (new `note`/`file`
  Templates); the real Customer/Partner auto-wikilinking logic is
  unchanged, reused as-is (not part of the write-mechanics problem).
  Shape change matches the meeting-capture precedent: date folded into
  the filename/folder name (`Work/Notes/<date>-<title>.md`, `Work/Files/
  <date>-<stem>/`) instead of a separate date-parent folder — old
  captures untouched, only new ones use the new shape. Verified live
  against the real vault (create + the file skill's own append-details
  mode), then cleaned up; deployed to both real profiles. Threads/email-
  thread-capture and the Threads-dependent summarize-and-tag-* skills
  explicitly deferred (operator: "Threads is Dangerous for now... lets
  leave it for later").

- feat: `REQ-SB-80` — RegistryLoader + boot sequence, built directly per
  operator direction (no `/spec`/`/plan-tasks` — a structural fix, not a
  Gherkin story). New `app/data_access/registry/` package
  (`schemas.py`/`errors.py`/`loader.py`): walks a real `data/` tree
  (`<vault>/.second-brain/data/Sections/*/Agents/*/{Agent-config.json,
  Agent-visual.json, soul.md}`, `Background/Agents/*/...`,
  `Tools/*/{Tool.json, Skills/*/{Skill.json, Skill-visual.json}}`,
  `Providers/*/Provider.json`) into an in-memory `Registry`, staged
  (`checking_hermes → loading_sections → loading_agents → loading_skills →
  loading_providers`) and fail-loud (the first invalid file halts that
  boot attempt with its exact path + reason). `checking_hermes` reuses
  `system_health.mcp_mount_reachable()` rather than a second HTTP-ping
  implementation. Hot-reload (`watch_and_reload`, 2s poll of the tree's
  own mtime fingerprint) calls the identical `boot()` coroutine used for
  cold start — one validation path, not two. New `GET /boot-status` /
  `POST /boot-status/retry` (`app/api/boot_router.py`), wired into
  `main.py`'s lifespan as a fire-and-forget task (same pattern as
  `vault_indexing.rebuild_index`) so it's pollable from the instant the
  app accepts connections. New one-off `scripts/migrate_to_data_layer.py`
  seeded the real tree from every existing source (`agents_map_adapter.py`
  hardcoded dicts, `hermes_definitions.py`, `agent_visual_registry.py`,
  `section_registry.py`, `provider_registry.py`, the real, product-
  relevant Hermes `SKILL.md` files) — 6 Sections, 21 Agents, 4 Tools / 13
  Skills, 2 Providers, confirmed live. Frontend: new `features/boot/`
  (`bootApiClient.ts`, `BootGate.tsx`) wraps `<App />` in `main.tsx` —
  full-screen blocking stage list on cold boot (or on a cold-boot
  failure), a small non-blocking corner banner for a hot-reload
  (in-progress or failed, with a Retry button), reusing the same
  `GET /boot-status` shape for both. Verified live end-to-end: normal
  boot, a deliberately corrupted `Agent-config.json` triggering the
  fail-loud banner with the exact file + reason, and auto-recovery once
  the file was fixed (no restart needed). Not yet done, deliberately:
  nothing else in the app reads from the new `Registry` yet — the
  migration script only seeds files, it doesn't rewire consumers; see
  `MEMORY.md`.

- refactor: `REQ-SB-80` follow-up — `app/business/hermes/
  agents_map_adapter.py`'s Type/Section/depends_on/is_background_agent/
  display_name now read the RegistryLoader's `Registry` instead of 5
  hardcoded per-agent dicts (`_AGENT_TYPE`/`_AGENT_SECTION`/
  `_AGENT_DEPENDS_ON`/`_BACKGROUND_AGENTS`/`_AGENT_DISPLAY_NAME`, all
  deleted); an agent not yet migrated falls through to the exact same
  defaults those dicts always used. `agent_visual_registry`/provider
  sourcing untouched (still separately CRUD-editable / a live Hermes
  mirror). Fixed a real bug this surfaced in `scripts/
  migrate_to_data_layer.py`: it now boots its own in-process Registry
  before calling any adapter helper (see `MEMORY.md` for why) and aborts
  if that boot fails, rather than silently overwriting real data with
  defaults on a re-run. Verified live: re-migration is byte-identical
  (idempotent), and the Agents Map (6 sections, 32 agents) renders
  unchanged through the new path.

- fix: `AgentsMapPage` showed a silently-empty canvas (0 sections, 0
  agents) for the full duration of its own `refreshAgents()` fetch
  (`/agents` + `/sections` + every Pipeline's `/agents/{id}/jobs`) on
  every page load/refresh — `loading` state already existed but nothing
  rendered for it. New shared `components/PageLoading.tsx` (reuses
  `BootGate`'s exact spinner/label visuals, `styles/boot.css`, so a
  refresh reads as one continuous loading experience — operator: "when I
  refresh it normally takes time for the data to load, We need to have
  the bootGate to tell me data is loading") now fills the map's own
  content area while `loading` is true. Verified live: reload shows
  "Loading your Agents Map…" with a spinner, then resolves cleanly into
  the normal 6-section/32-agent map.

- feat: `BootGate` now surfaces the backend going unreachable mid-session
  (process killed/crashed after the app already loaded), not just during
  initial boot — operator: "I need it to tell me if the backend is
  down." Previously the poll loop's own `catch` silently swallowed a
  failed `/boot-status` fetch once `everReadyRef` had already flipped
  true, so a backend crash left the last-known "ready" status on screen
  forever with zero indication anything was wrong. New `backendUnreachable`
  state (2 consecutive missed polls, ~2s, before declaring it down --
  avoids a false-positive flicker on one dropped request) drives a
  persistent red top banner ("Backend is unreachable — retrying…"),
  independent of the existing hot-reload-failure banner; the initial
  full-screen boot state also now distinguishes "still connecting" from
  "confirmed not responding." Clears itself the instant a poll succeeds
  again — no manual retry needed. Verified live: killed the backend
  process while the app was already showing, banner appeared within
  ~3s; restarted it, banner cleared automatically ~4s later with no
  interaction.

- feat: `BootGate`'s "backend unreachable" state now also renders a
  dimmed, full-viewport overlay (`.backend-down-overlay`, no click
  handler needed — an unstyled fixed div still intercepts pointer events
  from whatever's stacked below it) between the app and the top banner,
  so the operator can't click into a UI that can't actually do anything
  with the backend down (operator: "add a dimmed layer on top of the
  system when the backend is down so I can't touch it"). Verified live:
  killed the backend, confirmed a nav click through the dim layer did
  nothing (still on Agents Map, no navigation), restarted the backend,
  overlay + banner both cleared automatically with the app fully
  interactive again.

- fix: `REQ-SB-80` follow-up — found and fixed a real, live bug while
  extending Registry-backing to Skills: `SkillsTree.tsx`'s Capabilities
  panel never rendered ANY skill, for ANY agent. Its own
  `SKILLS_TREE_TOOL_ORDER` filters on an exact `Outlook`/`Vault`/`Web`/
  `Compass` string match, but `agents_map_adapter.py` was feeding it the
  raw Hermes skill-category folder name (`"knowledge-base"`,
  `"librarian"`, etc — confirmed live, never equal to any of the 4), on
  top of the ~80 generic bundled skills every cloned Hermes profile
  carries by default (irrelevant catalog noise). `/skills` and
  `/agents/{id}/skills` (`agents_map_adapter.list_all_skill_summaries`/
  `list_agent_skill_summaries`) now source from the RegistryLoader's own
  curated Tools/Skills catalog (new `_registry_skill_catalog()`) — `tool`
  is the owning Tool's real display name (exact match by construction),
  and the catalog is the 13 real, product-built skills, not Hermes'
  entire bundled set. Added a real `mutates: bool` to `SkillConfig`
  (`schemas.py`, `loader.py`, default `True`) since
  `AgentDetailPanel.tsx`'s `getSchedulableCapabilities()` genuinely reads
  it — `web-search` is the one real read-only skill, set explicitly in
  the migration script. Verified live: `/skills`/`/agents/azure-expert/
  skills` return correctly-tooled data, and the Settings tab's
  Capabilities tree now visibly groups under real Outlook/Vault/Web/
  Compass headers instead of rendering empty.

- fix: `REQ-SB-80` follow-up — closed a real data-drift/data-loss risk
  the Registry migration itself created. `section_registry.py`'s
  `create_section`/`update_section`/`_seed_state` now dual-write into
  `data/Sections/<id>/Section.json` (new `_write_registry_section_json`)
  so a rename/recolor through Settings doesn't go stale in the Registry
  (and therefore the Agents Map, which resolves a migrated agent's
  section name from there now) until someone re-runs the migration
  script by hand — RegistryLoader's existing hot-reload poll (~2s) picks
  it up automatically. `delete_section`'s own blocking check previously
  only consulted its `assignments` dict, which was never populated for
  real Hermes agents (only the retired pre-Hermes model) — deleting a
  Section with real migrated agents in it would have silently
  "succeeded" while orphaning their folders; now also checks the
  Registry's real agent placements. That fix surfaced a second live bug:
  `sections_router.py`'s `_blocked_delete_message` resolved blocker
  names via the same dead pre-Hermes `agent_registry` (`None["name"]`
  would have crashed the 409 response) — switched to
  `agents_map_adapter.get_agent_detail()`. Verified live: `DELETE
  /sections/technology` now correctly returns HTTP 409 listing all 10
  real agent names with no crash; a rename+revert on `/sections/industry`
  updated its `Section.json` immediately; did not test an actual
  real-section deletion (operator's live taxonomy, not scratch data).

- feat: `REQ-SB-80` follow-up — `agent_visual_registry.set_agent_visual`
  now also dual-writes the Registry's own `Agent-visual.json` (new
  `_write_registry_agent_visual`, same additive/one-way shape as
  `section_registry.py`'s `_write_registry_section_json`), closing the
  same kind of drift gap proactively before anything actually reads
  icon/color FROM the Registry (nothing does yet — `_visual()` still
  reads live from this store, unchanged). New shared
  `registry_loader.agent_data_dir(agent_id)` centralizes the Section-vs-
  Background real-folder resolution so future dual-writers (e.g. a future
  provider-assignment sync) don't have to re-derive it. Verified live:
  PATCH'd `azure-expert`'s icon/color, confirmed
  `data/Sections/technology/Agents/azure-expert/Agent-visual.json`
  updated immediately, reverted to the original values.

- test: `REQ-SB-80` follow-up — new `tests/test_registry_loader.py`, the
  first automated regression coverage for the RegistryLoader (previously
  verified only by hand, curl/browser, all session). 9 tests: valid-tree
  boot, empty-tree boot, fail-loud on a missing required field / an
  invalid agent `type` / a missing `soul.md` (asserting the exact file +
  message), a failed hot-reload leaving the previous good `Registry`
  object untouched (not blanked), `agent_data_dir`'s Section/Background/
  unmigrated resolution, and the hot-reload fingerprint changing on a
  real file edit. Isolated via `monkeypatch` on `settings.vault_path`
  (a temp dir, never the real vault) and a stubbed
  `system_health.mcp_mount_reachable` (never a real network call to a
  live backend). All 9 pass; confirmed the live backend's own real
  `/boot-status` was unaffected by the test run.

- feat: `REQ-SB-82-US-03-T01` (`ADR-009`) — new
  `app/business/cockpit/moderator.py`: two independent, purely
  deterministic Meeting Moderator matching tracks, no LLM call, no Hermes
  profile involvement. `match_customer_expert(subject_note_stem)` reads
  the subject note's own real customer signal (`customer:` frontmatter OR
  a `customer/<slug>` tag — both real, live signals depending on which
  capture pipeline produced the note, see `MEMORY.md`) and maps it to a
  real, already-registered `<slug>-expert` agent in the real "Customer"
  Section (`REQ-SB-83`'s Masdar/Adnoc/TAQA today) via
  `agents_map_adapter.list_agent_summaries()` — `None`, never fabricated,
  if no such agent is actually registered. `match_domain_experts
  (subject_note_stem)` is a stopword-filtered tokenized keyword overlap
  between the subject's own tags/subject text and every real `type:
  "expert"` agent's `name`/`description` — `[]` if nothing overlaps.
  Verified live against the real vault and the real Hermes-mirrored agent
  roster (no mocks): a real ADNOC-tagged Thread note and a real
  Masdar-tagged RawMessage note each correctly resolved to
  `adnoc-expert`/`masdar-expert`; a real Azure-subject Meeting note's
  domain-match list included `azure-expert`; a real Aldar-tagged Thread
  note (a customer with no registered Expert) correctly returned `None`;
  a real, topic-unrelated Thread note returned `None`/`[]` on both tracks;
  a full-vault scan of all 492 real notes carrying any customer signal
  confirmed `match_customer_expert` never resolves to an agent id outside
  the real, live Customer-Section roster. Does not close
  `REQ-SB-82-US-03` — `T02` (compute-on-first-read caching onto
  `chat_store`) and `T03` (frontend "Recommended" grouping) remain.
- feat: `REQ-SB-82-US-03-T02` (`ADR-009`) — `app/business/cockpit/
  chat_store.py::get_thread` additively computes and caches
  `recommended_agent_ids` onto `ADR-007`'s same per-subject persisted
  entry (`.second-brain/cockpit_chat.json`) — no new store. The first
  real read for a subject whose entry has no `recommended_agent_ids` key
  yet calls `moderator.match_customer_expert`/`match_domain_experts`
  (both tracks, combined, deduplicated, order-preserving), persists the
  result (including the honest empty-list case), and every later read
  serves the cached value with zero recomputation; `bring_in_agent`/
  `remove_agent` are untouched and never read/write this field. No
  router-code change needed — `cockpit_router.py`'s existing `GET`
  pass-through already surfaces the new field. Verified live against the
  real vault and the real, persisted `.second-brain/cockpit_chat.json`
  (production entry backed up before, byte-identical after): a scratch
  Masdar+Azure-subject Meeting note's first read returned
  `recommended_agent_ids` containing both `masdar-expert` and
  `azure-expert` (plus every other real Azure-domain expert the
  keyword-overlap track matched); a second read, with a call-count
  monkeypatch on both `moderator` functions, served the identical cached
  list with zero re-invocations; a scratch subject matching neither track
  persisted an honest `[]` on first read, also served from cache
  (zero re-invocations) on a second read; `bring_in_agent`/`remove_agent`
  round-tripped `brought_in_agent_ids` on the same entry with
  `recommended_agent_ids` unchanged throughout; independently reconfirmed
  through the real, unmodified `GET /cockpit/{subject_kind}/
  {subject_note_stem}` HTTP endpoint on a freshly-restarted backend
  (fresh vault-index rebuild), which surfaced the identical persisted
  `recommended_agent_ids` with no router edit. Scratch notes/script
  deleted and the real `cockpit_chat.json` restored to its exact
  pre-verification content afterward. Does not close `REQ-SB-82-US-03` —
  `T03` (frontend "Recommended" grouping) remains.
- feat: `REQ-SB-82-US-03-T03` — new "Recommended" grouping in
  `Cockpit.tsx`'s Chat tab right rail, above "In this chat"/"Bring in
  another Expert", per the same-day operator-approved visual shape (no
  fresh `/design` pass). `CockpitThread` (`cockpitApiClient.ts`) gains
  `recommended_agent_ids: string[]`; each recommended agent renders via
  the existing `ExpertRow` component (zero new bespoke row component),
  wrapped in the already-staged `cockpit-expert-recommended` CSS class for
  an accent-bordered visual distinction, with an "Add to chat" action
  calling the SAME `bringIn` function already wired to the real `POST
  .../roster` endpoint. An id present in both `recommended_agent_ids` and
  `brought_in_agent_ids` renders ONLY under "In this chat" (the plain
  "Experts"/"Bring in another Expert" list also excludes any
  still-recommended id, logged as a scope-internal judgement call).
  Closes `REQ-SB-82-US-03` — all 7 locked ACs (`AC-01`..`AC-07`) now
  verified across `T01`/`T02`/`T03`. Verified live (real headless-Edge CDP
  session, real running backend/frontend, real vault data, no mocks)
  against the real Masdar meeting note `Claire-Moussa - Catch-up Masdar
  Data Platform-2026-08-18-d2c74ddc.md`: the "Recommended" section
  rendered its real 6 matched agents (`AC-05`); bringing in a different,
  non-recommended Expert from the plain list worked unrestricted (`AC-06`,
  screenshot `t03-04-ac06-different-expert.png`); bringing in a
  recommended agent via its own Add action moved it to "In this chat"
  only, confirmed to persist across a real page reload (screenshots
  `t03-01`..`t03-03`). Test mutations reverted afterward
  (`brought_in_agent_ids` back to `[]` for the real subject). Also fixed,
  as an environment precondition for this verification: the persistent
  dev backend on port 8001 was found zombied (a dead reloader parent, a
  live `--multiprocessing-fork` child still serving pre-`T02` code with no
  `recommended_agent_ids` at all) — killed the confirmed-real stale PID
  and restarted one fresh instance with the project's own documented
  launch command; left running on port 8001 afterward per standing
  instruction.
- feat: `REQ-SB-82-US-05-T01` (`ADR-010`) — new `person-lookup` Skill
  (`Hermes-Provisioning/skills/librarian/person-lookup/{SKILL.md,
  scripts/check_person_note_empty.py, scripts/append_person_findings.py}`)
  for the Meeting Preparation Agent's one-time attendee web lookup.
  `check_person_note_empty.py` (`--note-path`) reads an existing Person
  note's own body (everything after the closing `---` frontmatter fence,
  same split convention as `vault_writer.py::read_note`) and reports
  `{"empty": true|false}` — whitespace-only counts as empty.
  `append_person_findings.py` (`--note-path`/`--input-file`,
  `{"findings": str}`) appends real findings text into an ALREADY-EXISTING
  note's own body, mirroring `app/business/cockpit/notes.py::add_person_
  note`'s append-only-to-an-existing-note shape — never creates a new
  note (errors honestly if the path doesn't exist), never overwrites or
  removes existing content. Neither script performs the web lookup itself
  — that stays the calling agent's own real `web_search` tool call, per
  `ADR-010`. The one-time gate IS the plain body-emptiness check; no
  separate "already looked up" tracking field or file exists. Verified
  live against real scratch Person notes under the real vault's
  `Work/People/` (cleaned up after verification, none left behind):
  frontmatter-only note reports `empty: true`; a whitespace-only body also
  reports `empty: true`; appending real findings makes a re-check on the
  SAME note report `empty: false`; a note with content added independently
  of this agent (not via `append_person_findings.py`) reports the same
  honest `empty: false`, confirming no distinction is made by who added
  the content; appending against a nonexistent note path errors honestly
  and creates nothing. This task does not close `REQ-SB-82-US-05` —
  `T02` (the cron/profile) remains.
- feat: `REQ-SB-82-US-02-T02` (`ADR-008`) — new `research-kb-writer` Skill
  (`Hermes-Provisioning/skills/librarian/research-kb-writer/{SKILL.md,
  scripts/write_research_doc.py}`) mirroring `azure-kb-writer`'s own
  `write_azure_doc.py` CLI/frontmatter contract (`--vault-path`/
  `--input-file`, scratch JSON, `type: "ResearchDoc"` frontmatter +
  `## Summary`/`## Details`), writing into a new `Work/Research/`
  top-level vault area. ONE deliberate divergence from `azure-kb-writer`:
  NEVER updates an existing note in place — a same-title call always
  creates a brand-new, distinctly-suffixed file (reuses
  `capture_note.py`'s own `_unique_note_path` time-then-counter
  disambiguation technique verbatim). No approval/confirmation step, no
  caller-identifying CLI argument. Provisioned the real, live
  `research-agent` Hermes profile (`hermes profile create research-agent
  --clone`; new SOUL.md — Librarian-Section research capability, not
  meeting-scoped, uses Hermes' own bundled `web_search`/`terminal` tools
  directly, no new lookup capability; real description set via `hermes
  profile describe --text`) with the Skill installed
  (`skills/librarian/research-kb-writer/`, confirmed `enabled` via
  `hermes -p research-agent skills list`). Verified live end-to-end: a
  real direct chat request produced a real, cited new note in
  `Work/Research/`; a real cross-profile relay (from `notes-manager`)
  produced an equivalent second note, proving caller-agnostic behavior; a
  deliberately-unanswerable request produced an honest "no verifiable
  record found; no note written" reply with zero new file created. The
  real, running Agents Map (`GET /agents`) now shows `research-agent`
  (`type: expert`, `section_id: librarian`), confirming `T01`'s
  previously-inert registration activates correctly. **`REQ-SB-82-US-02`
  (Research Agent) is now `Done`** — both tasks complete, all 5 locked ACs
  (`AC-01`-`AC-05`) verified live with real positive results. **Both
  `SPRINT-076` stories are now `Done` — `SPRINT-076` itself is `Done`**;
  see its own `## Retrospective`.
- feat: `REQ-SB-82-US-01-T02` — `cockpit_router.py`'s `GET
  /cockpit/{subject_kind}/{subject_note_stem}` now returns the real,
  persisted `thread` from `T01`'s `chat_store.get_thread(...)` in place of
  the hardcoded empty stub (pass-through, unchanged for
  `REQ-SB-82-US-03-T02`'s later `recommended_agent_ids` addition). New
  endpoints `POST /cockpit/{subject_kind}/{subject_note_stem}/roster`
  (body `{"agent_id": str}`) and `DELETE .../roster/{agent_id}`, both
  404-ing on an unknown `subject_note_stem` via the same
  `vault_indexing.get_index()` check the existing `GET` already used.
- feat: `REQ-SB-82-US-01-T03` — `Cockpit.tsx`'s Chat tab roster now reads
  and writes through the real backend instead of local-only `useState`.
  Removed the `broughtInIds` `useState` entirely; the roster is derived
  every render from the real fetched `data.thread.brought_in_agent_ids`,
  so it can no longer drift from the real persisted value. New
  `cockpitApiClient.ts` functions `bringInAgent`/`removeAgent` call
  `T02`'s real `POST .../roster`/`DELETE .../roster/{agentId}` endpoints;
  `bringIn`/`remove` merge the returned real thread back into component
  state. No new visual region — the existing "In this chat"/"Bring in
  another Expert" grouping and `chat-message`/`chat-message-author`
  rendering are reused unchanged; the composer stays disabled
  (`REQ-SB-82-US-04`'s concern). Verified live end-to-end (real browser,
  real backend, real vault meeting note): brought an Expert into chat,
  hard-reloaded, confirmed it survived; removed it, hard-reloaded,
  confirmed it was gone; brought it in again, navigated away and back via
  real in-app SPA navigation (not a hard reload), confirmed the roster
  was unchanged. **`REQ-SB-82-US-01` (Persisted Cockpit Chat) is now
  `Done`** — all 3 tasks complete, all 7 locked ACs verified live.
  Verified live end-to-end over real HTTP against the real running
  backend and real vault: bring-in/remove roundtrip (`AC-01`/`AC-02`),
  per-subject-scoped 404s on unknown subjects for both new endpoints, a
  never-touched real subject reading back the honest empty default
  (`AC-06`), and two directly-seeded attributed messages (via
  `chat_store`'s own functions, no new message-write endpoint added)
  read back byte-identical, same order, over the real `GET`
  (`AC-03`/`AC-07`). All scratch roster/message state removed from the
  real vault's `.second-brain/cockpit_chat.json` after verification.

- feat: `REQ-SB-82-US-01-T01` — new Cockpit Chat persistence module
  (`app/business/cockpit/chat_store.py`: `get_thread`/`bring_in_agent`/
  `remove_agent`) backed by a brand-new sibling JSON store,
  `.second-brain/cockpit_chat.json`, keyed per `"{subject_kind}:
  {subject_note_stem}"` (`ADR-007`). New sibling load/save functions
  (`load_cockpit_chat_state`/`save_cockpit_chat_state`) added to
  `vault_writer.py`, mirroring `load_agent_visuals_state`/
  `save_agent_visuals_state`'s established read-whole-file/
  default-if-missing/write-whole-file shape. Deliberately does NOT reuse
  the stale, pre-Hermes-pivot `business/cockpit/threads.py`/
  `cockpit_threads.json` (left untouched). Verified live against the
  real vault: bring-in/remove roundtrip via a fresh disk re-read,
  per-subject scoping (no cross-subject leakage), and an honest empty
  default for a never-touched subject key.

- feat: rebuilt `hermes_client.py`/`hermes_status.py`/`hermes_router.py`
  against Hermes' real, live-verified local API (`hermes serve`,
  `127.0.0.1:9119`, `x-hermes-session-token` auth) — replaces the
  original version, which was built from documentation that didn't match
  the actually-installed Hermes version. Verified end-to-end three layers
  deep against a real running Hermes instance (client → business wrapper
  → a real booted FastAPI app's own `/hermes/status`/`/hermes/sessions`
  routes), all returning real data. See `MEMORY.md` "Constraints" and
  `Implementation/Plans/2026-08-20-backend-architecture-redesign.md`.
- feat: wired the Tools registry into `main.py` and shipped the first
  real Action, `outlook -> email -> gather_emails` (thin wrapper over
  the existing, unmodified `pull_and_stage_emails`). Found and fixed two
  real bugs along the way: a mounted Tool's MCP server never initialized
  without its `session_manager.run()` lifespan entered explicitly
  (mirrors a gap `api/mcp_server.py`'s own mount already worked around);
  and `/mcp/outlook` silently 404'd because it sat inside the pre-existing
  `/mcp` mount's own path space (Starlette registration-order matching)
  -- fixed by moving Tool mounts to their own `/tools/<id>` prefix.
  Verified live: `/tools/outlook/` now answers with the same real MCP
  protocol response as the long-working `/mcp/` mount.
- feat: created the Backend Architecture Redesign skeleton (Data Access
  layer: `vault/`, `system/` incl. `provider/` and `tools/`; Business
  layer: `logic/`, `vault/`, `core/`, `hermes/`, `langgraph/`) alongside a
  real, tested `business/langgraph/proof.py` proving LangGraph works
  end-to-end against real vault data. See the same plan doc for the full
  block-by-block log, schema decisions, and open questions.
- feat: built the full vault-rebuild capture pipeline — 5 Actions
  (`ingest_email`, `rename_thread`, `link_person_to_thread`,
  `capture_attachments`, `capture_file_link`) plus a fetch-only
  `list_recent_emails`, initially exposed via a new `vault` MCP Tool
  alongside the existing `outlook` one, orchestrated by a new
  `email-thread-capture` Hermes Skill + cron job. Found and fixed 4 real
  bugs along the way, the most serious being a duplicate-Thread spawn
  when re-ingesting a message on an already-renamed Thread (wrong,
  rename-blind existence check — fixed by using `resolve_thread_
  directory` consistently everywhere). See the architecture redesign
  plan doc for the full block-by-block log.
- refactor: rewrote the email-thread-capture pipeline as fully
  Hermes-native — 8 standalone scripts (`vault_lib.py`, `outlook_lib.py`,
  one CLI entry point per Action) live directly in the Skill's own
  `scripts/` folder, invoked through Hermes' own `terminal` tool. No MCP
  server, no Second Brain backend dependency at all. Removed the 6 ported
  source files, the `vault` Tool's registry entry, and `list_recent_
  emails` from the `outlook` Tool — single source of truth moved to the
  Skill. Person-note creation in the new scripts is deliberately trimmed
  to bare name+email (no company/Customer/Partner matching or
  hub-linking — Capture-phase scope only; that enrichment stays Second
  Brain's own `retrofit_people_from_emails()` job, run later as a
  separate pass). Smoke-tested end-to-end against a scratch vault before
  the old code was deleted. See `ADR-002` for the full decision and
  alternatives considered.
- fix: message-note readable filenames (`<date> <sender>`) still
  collapsed into indistinguishable names whenever the same sender posted
  more than once in a thread on the same day — the hash-suffix collision
  fallback produced a second filename that still just reads "Name" in
  Obsidian's file view. Found live during the first real vault-rebuild
  pull. Fixed by including time-of-day (`<date> <HH:MM> <sender>`) in
  both `vault_lib.py` (deployed to the live Hermes install, took effect
  mid-run) and `app/data_access/vault_writer.py`'s `raw_message_note_path`
  for consistency. Already-written files from before the fix keep their
  old names for now — a one-time backfill/rename pass is planned once the
  current full-history pull completes, to avoid touching cross-references
  mid-run. See `MEMORY.md` "Patterns."
- feat: view-only backend mirror of Hermes' real Agent/Skill definitions
  — `GET /hermes/agents`, `GET /hermes/agents/{id}`. Reads Hermes' own
  files live on every call (`profile.yaml`, `config.yaml`, `SOUL.md`,
  every `SKILL.md`'s frontmatter) rather than a synced copy, so it can't
  drift from what Hermes actually has configured. New
  `app/data_access/hermes_definitions.py`, first real content in the
  `app/business/hermes/` skeleton folder (`definitions.py`), and
  `app/api/hermes_agents_router.py`. `HermesAgent`/`HermesSkill` naming
  (not bare `Agent`/`Skill`) avoids colliding with two other existing
  concepts in this codebase; every record carries `source: "hermes"`.
  Verified end-to-end against the real local Hermes install (all 4 real
  profiles — `default`/Primary plus `opp-manager`/`notes-manager`/
  `files-manager` — correctly discovered with accurate skill counts and
  config values) and against a real booted FastAPI app (`GET
  /hermes/agents/opp-manager` → 200 with real data; unknown id → 404).
  A scoped exception to ADR-001's "not ours to own" principle — see
  `ADR-003` for the full reasoning, alternatives, and the one open
  discrepancy (78 vs. 82 skills reported for Primary, not yet
  root-caused).
- feat/fix: retired the old Second-Brain-native orchestration agents for
  real (operator: "we're fully on Hermes now") — `agent_registry.py`'s
  10 hardcoded/persisted agents cleared, `main.py`'s lifespan no longer
  recreates the Librarian bootstrap on every app start. Restored Sections
  as Second Brain's own real, Hermes-independent concept — `app/api/
  sections_router.py` (verbatim from archive), real 6-Section taxonomy
  (Customer, Librarian, Industry, Technology, Data Gatherer, Sales),
  schema extended with `icon`/`color`/`subtitle`. Retrofitted
  `features/agents-map/` over the Hermes mirror via a new presentation
  adapter (`app/business/hermes/agents_map_adapter.py`) and fresh,
  view-only `app/api/agents_router.py`/`skills_router.py` at the same URL
  surface the frontend already calls — no frontend changes needed for
  list/detail rendering. Found and fixed a real stale-state bug along the
  way: `.second-brain/agent_sections.json` had already been seeded with
  the old 5-section list by an earlier app run, which the new seed-list
  code couldn't retroactively fix (seeding only fires when the file
  doesn't exist yet) — regenerated by hand. See `ADR-004` for the full
  reasoning, the archived-router alternative considered and rejected, and
  the one known follow-up (`/skills` is accurate but noisy — ~78 generic
  bundled skills on Primary alone — likely needs curation in a later UI
  pass).
- feat: ported the other 2 real Hermes cron jobs as Pipeline definitions —
  `meeting-builder.json` (Fetch Meetings → Resolve Meeting Folder → Build
  Attendees → Link to Thread) and `company-discovery.json` (Scan Threads
  + Scan Meetings for Domains → Filter Known Domains → Add to
  Entities.md — a real fork/merge shape, two parallel scans feeding one
  filter step). Generalized the map's splice mechanism from one
  hardcoded pipeline id to every real Pipeline (`GET /pipelines`,
  `fetchAllPipelineJobTrees`/`spliceAllPipelineJobTrees`) — adding a
  future pipeline is now just a new JSON file, no code change. Verified
  live: "6 sections · 13 agents mapped" (Primary + all 3 pipelines' real
  Step trees, fork/merge shape rendering correctly). See `ADR-005`.
- feat: built the "Hermes Operations" page (`/hermes`) — a read-only
  surface for Hermes' real cron job definitions/schedules (direct
  `cron/jobs.json` read, `hermes_cron.py`), server/gateway status (reused
  the existing `/hermes/status`), per-job run history
  (`cron/executions.db` via sqlite3), and each run's own linked detail: a
  clean per-run markdown report (`cron/output/<job_id>/<timestamp>.md`,
  matched by the run's real `finished_at`) plus the matching raw
  `agent.log` lines (matched by the run's real `started_at`, reconstructed
  into the same `[cron_<job_id>_<YYYYMMDD_HHMMSS>]` session tag Hermes
  itself writes). Also built a full, live two-way chat bridge to any real
  Hermes agent (`hermes_ws_client.py` + a new `/hermes/chat/{agent_id}`
  WebSocket proxy) — Hermes' embedded chat turned out to be a
  newline-delimited JSON-RPC-over-WebSocket protocol (`/api/ws`,
  `session.create` + `prompt.submit` + streaming `message.delta`/
  `message.complete` events, plus `approval.request`/`approval.respond`),
  not a REST call; the exact wire shape was confirmed by hand-driving a
  real session against the live gateway and getting a real model reply
  back before writing the FastAPI integration. Verified live end-to-end
  through the browser UI: cron job list/run history/report+log drill-down
  all render real data, and a chat message sent through the real page
  input got a real streamed reply back from Primary.
- fix: implemented the missing `POST /agents/{agent_id}/chat` endpoint —
  `AgentDetailPanel.tsx`'s own pre-existing per-agent "Chat" tab was
  calling it already, but it had never been built for Hermes-sourced
  agents, so every real agent's Chat tab silently failed ("Chat with Agent
  is not working"). Wired to the same `HermesChatSession` bridge as the
  new `/hermes` page (ADR-006) — no frontend changes needed. Verified live
  through the actual panel.
- refactor: dissolved the standalone `/hermes` page per operator direction
  ("build a top Page Tab to Navigate Different Sections of Health...one
  for App Status, one for Hermes Status" + "The Log of Corn Runs...should
  be instead of Crawlers"). System Health (`/system-health`) now has two
  top-level tabs (`.page-tabs`, a new generic page-tab style in
  `settings.css`) — "App Status" (the original content, unchanged) and
  "Hermes Status" (gateway/server status only). The cron job list + run
  history + linked report/log drill-down moved onto `CrawlersPage.tsx`
  (route `/crawlers` kept, since Crawlers' own original concept —
  Second-Brain-native background agents — has had zero real members since
  ADR-004 set every real Hermes agent `is_background_agent: false`;
  operator: "Just Call the Corn Jobs Crawlers and Bring the stuff here").
  Removed the standalone Chat widget from the old Hermes Operations page
  (operator: "Remove the chat with Agent at the bottom" — real per-agent
  chat already lives in each Agent Panel, fixed the same session) along
  with `hermes_router.py`'s now-unused `WEBSOCKET /hermes/chat/{agent_id}`
  proxy and the frontend's now-unused WS chat client functions.
- feat: Section Hubs are now clickable and have their own detail panel
  (`SectionDetailPanel.tsx`, Overview + Settings tabs — Name, Description,
  Icon, Color) — operator: "the Hub can be clicked and has its own
  Settings, Overview tab... Section Color and Icon, Description and
  Name." Wired into the ONE previously-dead click target this needed:
  `SectionDrilldown.tsx`'s own Hub render never passed `onActivate` (it
  stayed a plain non-interactive `<div>`, "matching today's behavior" per
  its own pre-existing comment) — now it does, opening the new panel,
  while the OVERVIEW Hub keeps its existing "zoom into this Section's
  drill-down" click meaning unchanged. `PATCH /sections/{id}` extended
  from name-only rename into a general update (icon/color/subtitle/
  description, same omitted-vs-empty-string convention as the agent
  Visual tab); `description` is a REAL backend field now — layoutAgents.ts
  had been typing it since 2026-08-15 ("will be used later") with nothing
  backing it. Reused `VisualPicker.tsx` verbatim for icon/color — its own
  comment had anticipated this exact call site ("once Hubs get their own
  settings surface"). Verified live: opened Data Gatherer's real panel,
  saved a real description, picked a real icon, watched the actual map
  Hub icon update in place with no reload, confirmed via a fresh
  `GET /sections`, then reset icon/color back to default via the same
  panel.
- fix: Agent Activity (`/agent-activity`) now shows Hermes' real session
  log — operator: "the Agents Activities Tab should get the Agents Log
  from Hermes." Its old Second-Brain-native "run_event/run_error" activity
  log was already silently dead: `agent_activity_router.py` had been
  removed from `app/api/` with nothing left importing it (the page's own
  `fetchAgentActivity()` call was 404ing), and its data source
  (`agent_registry.list_agents()`) has returned `[]` since agent
  orchestration moved to Hermes this session anyway — deleted the orphaned
  `app/business/agent_activity.py` and `features/agent-activity/client.ts`
  rather than repair a route with nothing real left behind it. Replaced
  with the already-live `/hermes/sessions` (now taking real `limit`/
  `offset` query params) — every genuine Hermes session, cron and
  interactive alike, agent name resolved via the existing agent list,
  source/status badges, title, message count, duration. Verified live: 50
  real sessions rendered correctly, including real WhatsApp conversations,
  cron runs, and CLI sessions.
- feat: each Agent's own Overview tab now shows its own recent real
  Hermes sessions — operator: "the Overview tab should show these Hermes
  sessions per agent too." `hermes_client.list_sessions()` gained a real
  `profile` filter param (confirmed live: an unfiltered call's own `total`
  dropped from 72 to 6 when scoped to `profile=opp-manager`, every
  returned row's own `profile` field matching) — threaded through
  `hermes_status.get_sessions()` and `GET /hermes/sessions?profile=`.
  `AgentDetailPanel.tsx`'s Overview tab passes `agentId` straight through
  as the profile (a real Agent's own id IS its real Hermes profile id) —
  no id-mapping needed. Verified live: Primary and opp-manager's panels
  each show their own distinct, correctly-scoped session list.
- fix: Agents Map/Section Hub connector lines had a real, confirmed bug —
  the Hub's own spoke line was drawn to each pipeline's ENTRY point (the
  root, e.g. "Fetch Emails") instead of its TERMINAL/producer stage (the
  one that actually writes to the vault) — operator: "Link to the Hub
  Should be The Nodes that Actually write to the Vault, I can See The
  nodes that Write to the Hub are the Farest from the Section Hub, Which
  is not Correct." The code had inverted the operator's own original
  2026-08-16 framing ("it should be the last one in the Tree") — fixed in
  both `AgentsMapCanvas.tsx` (overview) and `SectionDrilldown.tsx`
  (Section view) by filtering to agents with no outgoing dependency edge
  (nothing depends on them further) instead of no incoming one. This also
  fixed the reported "zigzag isn't clear, too many intersecting lines"
  complaint as a side effect — verified by writing a real geometric
  segment-intersection check (not eyeballing) against the live rendered
  SVG: the Data Gatherer section's own connector lines went from 5 real
  crossings (overview) / 6 (Section drilldown) to 0/0, since a spoke to
  the terminal stage is short (near the Hub) instead of spanning the
  entire depth range across other chains' territory.
- fix: a genuinely standalone agent (no `depends_on`, and nothing else
  depends on it — Primary, files-manager, notes-manager, opp-manager,
  none of which belong to any real pipeline) was landing at
  `AGENT_RADIUS_MAX`, the single farthest ring on the map — the exact
  same depth-0 branch a pipeline's own entry point uses, when a whole
  Section also contains real pipelines (their non-zero `maxDepth` pulls
  every depth-0 agent in the SAME section out to the outer edge) —
  operator: "the Agents that are solo, They are Far away from the Section
  Hub They need to be Closer." Fixed in `layoutAgents.ts`: a solo agent's
  radius is now a deterministic-per-id (same jitter-hash convention
  already used elsewhere, not `Math.random()`) random point 25%-50% of
  the way from the Hub out to where it would otherwise have landed.
  Verified live: Primary/opp-manager/etc. moved from radius ~56 to the
  computed [29.75, 38.5] band, each landing at a different point within
  it, connector-line crossing count unaffected (still 0).
- fix: closed two more real 404s on `AgentDetailPanel.tsx`, both cases of
  a frontend caller pointing at a backend route archived and never
  rebuilt against the Hermes mirror (same pattern as Chat/Agent Activity
  earlier this session). Settings tab's Provider row was an editable
  `<select>` populated by `GET /providers` (no providers router wired in
  `main.py`) whose own `onChange` (`PATCH /agents/{id}` with
  `provider_id`) would have silently no-opped anyway, since
  `AgentVisualUpdateBody` only ever reads `icon`/`color` — replaced with
  plain read-only text showing `agent.provider_name` (already real data,
  a Hermes agent's own `config.yaml` provider, ADR-004 point 3). History
  tab's `GET /agents/{agent_id}/history` never existed on the current
  router — added, returning `[]` always, matching `/jobs`'s own existing
  "never a 404, never fabricated" contract; the tab's pre-existing
  "Nothing recorded yet" empty state and the Overview tab's
  pending-approval scan (which depended on the same `history` fetch) both
  already degrade cleanly on an empty list, so no further UI changes were
  needed. Found two more, genuinely separate 404s of the same shape while
  investigating (`/agents/{id}/schedules` — the whole Schedule tab; the
  Settings page's own `/providers` CRUD, `ProvidersCard.tsx`) — flagged as
  a follow-up rather than fixed here, out of this fix's own scope.
- refactor: moved the per-agent real Hermes session log from the Overview
  tab to the History tab — operator: "The Hermes Sessions in Agent Should
  be in the History not in Overview." History's own pre-existing
  "Communication history" section (now honestly always-empty, see above)
  stays in place above it, in case a future fix restores real proposal
  data into it; limit raised 10 → 30 sessions now that this is the
  dedicated tab rather than an Overview preview.
- fix: the Vault Browser page (`/browse`) went blank ("Nothing indexed
  yet") after every backend restart — operator: "The Vault Browser page
  shows the wrong notes then when I refresh it is showing no notes."
  Root cause: `vault_indexing.py`'s own index is a plain module-level
  Python dict with zero disk persistence (ADR-024's own explicit,
  accepted tradeoff), silently wiped on every restart (a frequent event
  in dev — `--reload` included) with nothing left to rebuild it
  automatically once Hermes' own capture pipelines moved outside this
  backend process (2026-08-21 self-hosting rewrite removed the last
  in-process trigger). Fixed in `main.py`'s own lifespan: rebuilds
  eagerly on every start now, as a non-blocking background task
  (`asyncio.to_thread`, same "don't block application-startup-complete"
  pattern already used for the default-schedule dispatch). Verified
  live: restarted the backend with zero manual intervention, `GET
  /vault-search/status` came back `indexed: true` within 3s, `/browse`
  showed all 1,126 real notes immediately.
- bug: logged `BUG-036` — while verifying the fix above, found real,
  concrete evidence of a SEPARATE, genuine content bug this same page's
  default (unfiltered, stem-sorted) view surfaces first: several real
  Meeting-series and Person notes are filed under a raw Outlook internal
  identifier (`calendar_series_id` / LegacyExchangeDN) as their own
  filename, even though a real human-readable name (a meeting subject, a
  person's name) is already known and stored right in the same note's
  own frontmatter — this is almost certainly the "wrong notes" half of
  the operator's own report. Root cause lives in Hermes' own self-hosted
  capture skill scripts (outside this repo since the 2026-08-21
  rewrite), not in Second Brain's own read-only `vault_search.py`/
  `vault_indexing.py` (which are correctly reflecting real vault
  content) — logged rather than fixed here, per the operator's own
  separate "log them as bugs" direction this same session.
- fix: The Vault graph screen (`/vault`) only ever showed a small
  fraction of the real vault as nodes — operator: "the View Shows only
  like 20 Node while we have more than 1000 Nodes Something is wrong."
  Root cause, confirmed live by hooking `CanvasRenderingContext2D.arc()`
  (the per-node draw call) and inspecting real coordinates: the
  force-directed simulation (`forceLayout.ts`) is numerically unstable at
  the vault's real current scale (1,126 nodes / 6,032 edges — well past
  its original ~680-node design point, per its own docstring). A node
  caught in a dense, edge-less cluster (many same-kind notes with no
  wikilinks between them) can accumulate repulsion from hundreds of
  simultaneously-close neighbors in one tick; `VELOCITY_DAMPING` alone
  (a flat 15% shrink per tick) doesn't stop that compounding tick over
  tick, and positions diverge exponentially within a few dozen frames —
  measured directly at up to `1e+31`, thousands of orders of magnitude
  off-canvas. Of 1,126 real nodes, only 63 were still at sane coordinates
  by the time a viewer would actually look at the screen; the other
  1,063 were already permanently invisible, with no error and no
  automatic recovery. Fixed with a standard, targeted technique real
  force-layout libraries use for exactly this (e.g. d3-force's own
  velocity-decay + implicit speed clamp): cap each node's per-tick
  velocity magnitude (`MAX_VELOCITY`, `forceLayout.ts`), breaking the
  runaway feedback loop at its source without touching the tuned
  repulsion/spring constants. Verified live: same real 1,126-node graph,
  hooked the same way after the fix, ran the simulation for 8 real
  seconds — 1,126 of 1,126 nodes stayed at sane on-canvas coordinates,
  zero exploded.
- feat: three further Vault graph improvements, same session, operator-
  directed — "The Circle Size Should be Linked to the the Amount of
  links or Mentions for the file, The Lines are very Dense need to think
  about a solution, the more Dense Objects Move towards the Center."
  1. Circle radius now scales with each node's own real degree
     (incoming + outgoing wikilink count, computed client-side from the
     already-fetched edge list — no backend change) via
     `radiusForDegree()`, sqrt-scaled (`NODE_RADIUS_MIN`/`MAX`/
     `_DEGREE_SCALE`) so one extreme hub note doesn't dwarf the screen.
     Click hit-testing (`findNodeNear`) uses each node's own real drawn
     radius now too, not a flat constant.
  2. Density: edges render at a very low base opacity by default
     (`EDGE_ALPHA_BASE`, mirroring Obsidian's own graph view — the
     direct visual precedent for this screen), so dense areas read as a
     soft haze instead of solid clutter; hovering a node now brightens
     ONLY that node's own real edges (`EDGE_ALPHA_HIGHLIGHT`, thicker
     line) while dimming every other edge further
     (`EDGE_ALPHA_DIMMED`) — lets a viewer trace one note's real
     connections out of 6,032 edges on demand. `--graph-edge-color`
     (tokens.css) changed from a baked-in `rgba(..., 0.25)` to fully
     opaque — opacity is now controlled entirely by canvas
     `globalAlpha` in JS, not double-applied.
  3. Centering force (`forceLayout.ts`) is now degree-weighted
     (`DEGREE_CENTERING_FACTOR`, sqrt-scaled same as radius) — a
     heavily-linked hub note gets pulled toward the graph's center
     noticeably harder than a lightly-linked one, while a genuinely
     isolated (degree 0) note keeps the original, unmodified pull and
     drifts naturally outward under repulsion — hubs settle centrally,
     the periphery is real leaf/isolated notes.
  TypeScript typecheck (`tsc --noEmit`) passes clean; left live-browser
  verification to the operator this pass, per their own "let me verify,
  don't do validation yourself" direction.
- feat: four more Vault graph refinements after the operator's own live
  verification of the pass above — "The Nodes Hover Effect should Bring
  the node up front and have the name of the node visible, Nodes with
  more connections should be closer to the center, Nodes are Overlapping
  Massively, Lines on hover are very thick need to be more visually
  Appealing."
  1. Hovering a node now draws it LAST (strictly on top of any
     overlapping neighbor, regardless of paint order), with a thin ring
     around it and its real title drawn as a screen-space-constant-size
     label beside it (`HOVER_LABEL_FONT_PX`/`_OFFSET_PX`, divided by the
     current zoom scale at draw time, same convention as edge width).
  2. `DEGREE_CENTERING_FACTOR` raised 0.35 → 1.1 (`forceLayout.ts`) — the
     first pass was too weak; a hub's own local repulsion from its many
     close neighbors was competing with, not losing to, the centering
     pull.
  3. Added a real collision-resolution pass (`forceLayout.ts`) — a
     direct position correction (not another force) that runs
     unconditionally every tick and guarantees any two circles clear
     `COLLISION_PADDING` apart, using each node's own real drawn
     `radius` (now copied onto `SimulationNode` alongside `degree`).
     Plain inverse-square repulsion never guaranteed non-overlap,
     especially once circle size started varying per node (a large hub
     circle and a small leaf circle need more real separation than two
     equal small ones, which repulsion alone has no way to know).
  4. Highlighted edges softened `0.9`/`2px` → `0.55`/`1.25px`
     (`EDGE_ALPHA_HIGHLIGHT`/`EDGE_WIDTH_HIGHLIGHT`) — a true hub note
     can highlight hundreds of edges fanning from one point; near-opaque
     + double-width read as one solid wedge, not individually legible
     lines.
  TypeScript typecheck passes clean; left live-browser verification to
  the operator again, per their own standing direction this same
  session.
- feat: two more Vault graph refinements — operator: "The Nodes it self
  is very big leaving no Space for the lines to be Visible We need to
  have some room by Shrinking the nodes by 50% while Maintaining there
  Positions... Highlight the connected node with something like hover
  effect but different, think about it."
  1. `NODE_DRAW_SCALE = 0.5` applied only at the two circle-draw call
     sites — deliberately NOT a change to `simNode.radius` itself, which
     still governs collision spacing (`forceLayout.ts`) and click
     hit-testing (`findNodeNear`) unscaled. Shrinking the physics radius
     too would let collision resolution pack circles into the newly
     freed room, moving every node's real position — the opposite of
     "maintaining positions." Each circle now sits smaller inside the
     same personal-space bubble it already had, opening real visible
     gaps for edges.
  2. A hovered node's real neighbors (an edge actually connects them) now
     get their own third visual tier, distinct from both the resting
     state and the hovered node's own treatment: full opacity, a thin
     `--color-accent`-colored ring (deliberately not the same color as
     the hovered node's own text-colored ring, so the two tiers are never
     confusable), and their own title label — but only when the neighbor
     count is small enough to stay legible (`NEIGHBOR_LABEL_MAX_COUNT =
     25`; a true hub can have hundreds of real connections, and
     unconditionally labeling all of them would recreate the exact
     clutter this feature exists to cut through). Every OTHER node dims
     to `NORMAL_NODE_ALPHA_WHEN_HOVERING` while a hover is active, so the
     connected set reads as a lit island against a quiet background —
     the actual "who is this connected to" answer at a glance.
  TypeScript typecheck passes clean; live-browser verification left to
  the operator, per their own standing direction this session.
- fix: background edges weren't dimming at a comparable rate to
  background nodes while hovering — operator: "the not Hover [nodes] and
  the lines that are not connected are mixing... if you gonna Dim the
  nodes we need to dim the lines." `EDGE_ALPHA_DIMMED` dropped
  `0.02 → 0.006` — with most of the graph's 6,032 real edges not
  touching whichever node is hovered, thousands of still-somewhat-visible
  lines kept crossing behind the dimmed nodes, reading as one blended
  mass rather than a clearly quiet background. TypeScript typecheck
  passes clean; live-browser verification left to the operator.
- feat: clicking a Vault graph node (or a Browse & Search result) now
  shows the note's real markdown body, rendered as formatted HTML with
  working links — operator: "when I click on a node The Next View should
  be the MD file it self displayed in a nice HTML formatting with links
  to the Files and Tags etc." `GET /vault-search/notes/{stem}`
  (`vault_search.py::get_note_detail`) now includes real `body` text,
  read fresh from disk (same established pattern `search()` already
  used, ADR-026 — `vault_indexing.py`'s own index entries never cache
  body text). New `NoteBody.tsx`: real `[[wikilink]]`/`[[target|alias]]`
  syntax isn't standard CommonMark, so it's pre-processed into plain
  markdown link syntax before handing off to `react-markdown`
  (`ChatMessageText.tsx`'s own established zero-plugin, safe-by-omission
  convention — no `rehype-raw`, no `dangerouslySetInnerHTML`), resolved
  against the note's own already-backend-resolved `forward_links`
  (matched by STEM case-insensitively, the same key `vault_indexing.py`'s
  real wikilink resolution uses — never by title, which can legitimately
  differ). A target with no match is a real, honest dangling link,
  rendered as plain text, never fabricated. Internal links render via
  `react-router`'s `Link` (no full page reload); external links open in
  a new tab. Tag badges on the note detail page are now clickable too,
  navigating to `/browse?tag=X` (`VaultBrowserPage.tsx` now reads a
  `?tag=` query param on mount to pre-select the filter). New
  `.note-body` CSS block (`vault-browser.css`) reins heading sizes into
  the app's own existing type scale and styles links/code/blockquotes
  consistently with the rest of the UI. TypeScript typecheck and a
  Python compile check both pass clean; live-browser verification left
  to the operator, per their own standing direction this session.
- feat: created a new standalone Hermes agent, `azure-calculator` —
  operator: "I want to Create an Agent to be my Azure Calculator Helper
  ... it need to be simple and very smart, Ask the right Questions to
  get based on the Solution." Provisioned via `hermes profile create
  azure-calculator --clone` (own SOUL.md, config.yaml, `.env`), trimmed
  to a single real Skill (every cloned bundled skill moved aside into
  `_disabled-skills/`, matching the same narrow-mandate pattern already
  used for `opp-manager`/`notes-manager`/`files-manager`). New
  `pricing/azure-cost-calculator` Skill: `lookup_azure_price.py` queries
  Microsoft's own public Azure Retail Prices API
  (`prices.azure.com/api/retail/prices`, no API key needed) for real,
  current prices, with a convenience `estimated_monthly_cost` projection
  for hourly-billed rows. SOUL.md is written to hold a genuine
  back-and-forth conversation (ask what's missing — resource type,
  region, scale — before calculating; don't re-ask what's already been
  given) rather than the one-shot-relay shape `opp-manager` uses, since
  this agent needs real live dialogue to nail down what's actually being
  priced. Found and fixed a real bug while verifying against the live
  API: Azure's own `armSkuName` field is reliably populated for Virtual
  Machines but genuinely blank for Storage (whose real distinguishing
  name lives in `skuName`/`productName` instead) — a single-field
  `contains()` filter silently returned zero matches for every real
  Storage SKU; fixed by OR-ing the search across all three fields.
  Verified live end-to-end: real VM/Storage/PostgreSQL price lookups all
  return correct data with correct monthly-cost math, and the new agent
  is confirmed discoverable via Second Brain's own `GET /hermes/agents`
  (shows up on the Agents Map automatically, no Second Brain code
  changes needed — the map is a live mirror of every real Hermes
  profile).
- fix: `POST /agents/{agent_id}/chat` (`agents_router.py`) now surfaces a
  `clarify.request`/`approval.request` event as the turn's own reply
  instead of silently blocking for the full 180s and 504ing — found
  while verifying the new `azure-calculator` agent's real conversational
  behavior (it correctly tried to ask a clarifying question, but Second
  Brain's own chat endpoint had no handling for that event type at all).
  Confirmed the real wire shape directly against hermes-agent's own
  installed source (`tui_gateway/server.py::_block`/`_clarify_block`/
  `_emit_approval_request`): both event types carry a human-readable
  `question` (or batch `questions`)/`command` field plus the request's
  own `request_id`. This REST endpoint opens a fresh, single-turn
  `HermesChatSession` per call with nowhere to hold that `request_id`
  open across a follow-up HTTP request, so it surfaces the question/
  approval text verbatim as the reply rather than attempting
  `clarify.respond`/`approval.respond` — Hermes' own gateway already
  tolerates an unanswered clarify/approval past its own configured
  timeout (confirmed live: falls back to locked/default answers and the
  agent continues on its own, the same "(clarify timed out after 120s —
  locked answers returned)" behavior already observed in this session's
  one-shot CLI test).
- feat: real per-agent Agents Map Section placement — operator: "more the
  Azure Calculator to Technology Section, Bring the rest of the Corn Jobs
  even if they are competed to the Data Gathering, Move the Customer
  Extraction pipeline to Liberian Section" then "Opp Manager to Sales,
  and Notes and file Manager to Liberian." Previously every individual
  Hermes-mirrored agent (`agents_map_adapter.py`) landed in ONE hardcoded
  Section ("Data Gatherer") regardless of what it actually does — only
  Pipelines had their own real per-pipeline `section` field. Added
  `_AGENT_SECTION`, a real per-agent-id override (same shape as the
  existing `_AGENT_TYPE` map): `azure-calculator` → Technology,
  `opp-manager` → Sales, `notes-manager`/`files-manager` → Librarian. An
  agent id absent from the map (Primary/`default`) falls through to Data
  Gatherer by construction — the operator's own "bring the rest... to
  the Data Gathering" is true automatically, no separate entry needed.
  `list_agent_summaries`/`get_agent_detail` now resolve each agent's
  Section individually instead of computing one shared section_id for
  all of them. Confirmed "Customer Extraction pipeline" wasn't an exact
  registered name (only Company Discovery/Meeting Builder/Threads
  Builder exist) — asked the operator directly rather than guessing;
  confirmed as Company Discovery (scans Threads/Meetings for new company
  domains, files them to Entities.md for review), moved via its own
  `company-discovery.json`'s `section` field from Data Gatherer to
  Librarian. Meeting Builder/Threads Builder stay Data Gatherer,
  unchanged.
- fix: Section Hub icons not rendering in the Agents Map overview or the
  Section drill-down view (`SectionHub.tsx`) — reported live: "The Icons
  in the Section Hub is not Visible in both the Agent Map and Section
  view." Root cause: `SectionHub.tsx` rendered `section.icon` directly as
  the Material Symbols ligature name, but a Section's `icon` can be a
  VisualPicker `id` (e.g. `"compass"`) whose real ligature differs
  (`"explore"`) — the `liga` OpenType feature only substitutes a glyph
  for a real ligature name, so an id/ligature mismatch renders as the
  literal, barely-legible word instead of an icon. `AgentNode.tsx` had
  already hit and fixed this exact bug for Agent icons (2026-08-16,
  "icons still not visible on agents") via `getVisualIconName()`
  (`visualOptions.ts`) — `SectionHub.tsx` never got the same fix applied.
  Now resolves through the same helper. `SectionDrilldown.tsx` reuses
  `SectionHub` directly, so this one fix covers both reported locations.
  Verified live: the Industry Hub's icon text changed from the literal
  `"compass"` to the correct `"explore"` ligature in both the overview
  and its own drill-down, confirmed via direct DOM inspection (computed
  `textContent`) since Material Symbols glyphs aren't distinguishable
  from their name in a raw screenshot. TypeScript typecheck clean.
- fix: Section Hub icons visually clipped at the edges (`agents-map.css`,
  `.hub-node-icon`) — reported live, immediately after the ligature fix
  above: "the Icon Size is Clipped not visible fully." Root cause found
  by rasterizing the actual glyph to a canvas and reading back non-
  transparent pixel bounds (a screenshot can't distinguish "wrong glyph"
  from "right glyph, sliced" — both just look like a small illegible
  mark): Material Symbols Outlined's real ink for these glyphs is ~16x16
  px at the hub's 14px (0.875rem) font-size (its own font metrics —
  ascent 15 + descent 1 — sum to 16px), wider and taller than the plain
  14x14px box a bare `line-height: 1` box provides at that font-size.
  `.hub-node-icon`'s own `overflow: hidden` (added 2026-08-15 for a
  DIFFERENT, unrelated reason — stopping the icon from forcing
  `.hub-node`'s flex container into an oval) was silently slicing ~1-2px
  off every edge of that ink as a side effect. Fixed by giving the icon
  span an explicit `width`/`height: 1.3em` (~18.2px, comfortably bigger
  than the measured ~16x16 ink) with flex-centering — `overflow: hidden`
  on an element with an explicit size still resolves that element's own
  automatic minimum size to 0 (the same CSS mechanism the original
  circularity fix already relies on), so this couldn't reintroduce the
  oval bug; verified live both Hub geometries stayed exactly square
  (30.79x30.79 overview, 30.24x30.24 drill-down) before and after.
  Verified live in both the Agents Map overview and the Section
  drill-down (same shared `SectionHub` component): icon box grew from
  14x14 to a non-clipping 18.2x18.2 in both, hub circularity unaffected.
  TypeScript typecheck clean (CSS-only change).
- fix: Agent node icons on the main Agents Map overview still clipped
  after the Hub fix above — reported live: "The Map Main still have the
  icons clipped." `.agent-node-icon` (individual Agent circles, e.g.
  Primary/azure-calculator/opp-manager) had the exact same font-metrics-
  exceeds-box issue as the Hub icons — confirmed live via the same
  canvas ink-bounds technique: at this element's 6px font-size, most
  glyphs' ink fits a bare 6x6 box, but "hub" (Primary's own icon) paints
  ~8x6px, wider than the box. Applying the SAME `width`/`height: 1.3em` +
  flex-centering fix used for the Hub grew the box's WIDTH correctly
  (6→7.79px, live-measured) but its HEIGHT stayed stuck at 4.36px — a
  second, different cause found live: `.agent-node` is a COLUMN flex
  container with the icon plus TWO sibling text spans
  (`.agent-node-label`/`.agent-node-type`) sharing one ~7.7px-tall
  overview node; default `flex-shrink: 1` let the icon get squeezed on
  the shared vertical axis to make room for those siblings, even though
  live measurement showed both siblings already render at an unreadable
  ~1x1px at this same overview scale (nothing visible lost by
  shrinking them further). Added `flex-shrink: 0` to the icon so it
  keeps its full requested 7.79x7.79 box instead. Verified live: icon
  box now 7.79x7.79 (was 6x4.36) for every real glyph in use
  (hub/conveyor_belt/smart_toy/mail), `.agent-node` itself stayed
  exactly square (7.7x7.7) in the overview and (26.24x26.24) in the
  Technology section's own drill-down — the historical "Agents...
  Oval" regression this container's own `overflow: hidden` exists to
  prevent did not reappear in either view. TypeScript typecheck clean.
- fix: My Day's Emails/Calendar were silently reading a stale, abandoned
  data model — operator: "Now we go to my day, The API is Missing I
  know lets bring it back smarter." Confirmed live: `/my-day/emails`/
  `/my-day/calendar` returned real 200s (not 404s — the actual "missing"
  piece was Approvals, `/pending-approvals`, archived same as
  `BUG-034`/`BUG-035`'s sibling routers) but always empty, because
  `my_day.py` still pointed at `vault_writer.list_notes_in_kind_folder`:
  (1) a flat, non-recursive `glob("*.md")`, so it saw zero of the real
  dated Meeting occurrences (`Work/Meetings/<series>/occurrences/*.md`
  — only the undated series-container note, ADR-048 already fixed this
  exact "nested note kind" blind spot for `list_all_note_paths()`, just
  never propagated here); (2) pointed at `Work/Emails/`, a folder that
  no longer exists — email capture moved to the Threads Builder
  pipeline (2026-08-21) and this projection was never updated to
  follow. Rewired both functions onto `vault_indexing.get_index()`
  (the same already-correct, already-recursive index `vault_search.py`/
  the Vault Graph use), filtering `type == "Thread"`/`type == "Meeting"
  AND start present`. Added real resolution logic, not just a data-
  source swap: `_customer_name_by_tag()` resolves a `customer/<slug>`
  tag back to the real Customer/Partner hub note's own `name` field
  (never guessed by reversing the slug); `_latest_sender_by_conversation
  ()` gives a Thread (which has no single sender of its own) a
  best-effort "most recent real sender" for the UI's existing "from
  {sender}" display; `_meeting_series_lookup()`/`_series_folder_name_
  for()` inherit `customer` onto a dated occurrence from its own parent
  series note, since a real occurrence's own frontmatter carries no
  customer tag at all (confirmed live). Verified live end-to-end:
  17 real emails / 15 real meetings now surface for the current window,
  correctly classified (Core42/Adnoc/Masdar/DGE/Ewec) wherever the
  underlying capture data supports it, honestly `null` where it
  genuinely doesn't (e.g. a real internal meeting with no customer tag
  at all) — clicked through the actual UI (`/my-day/emails?day=
  2026-08-20`), confirmed real subjects/senders/timestamps render
  correctly. Found and logged, but did NOT attempt, a separate blocking
  gap while verifying the click-through: `BUG-037` (Cockpit 404s
  entirely, its own archived router needing a Hermes-chat rewiring on
  the scale of this session's `POST /agents/{id}/chat` rebuild — too
  large/risky to attempt unsupervised overnight).
- feat: created a new standalone Hermes agent, `daily-briefing` —
  operator: "let's bring it back smarter instead of just listing emails
  and meetings... Emails need to be more classified and if I missed
  something during the week bring it up," then, going to sleep: "Yeah
  agent, let's go with that I will go to sleep run this part
  autonomous." Built on top of the same-night `my_day.py` data-model fix
  above (this agent would have had nothing real to reason over
  otherwise). Provisioned via `hermes profile create daily-briefing
  --clone` (own SOUL.md, config.yaml, `.env`), same narrow-mandate
  pattern as `opp-manager`/`notes-manager`/`files-manager`/
  `azure-calculator` (every cloned bundled skill moved aside into
  `_disabled-skills/`). New `day-planning/daily-briefing` Skill, two
  scripts: `my_day_lookup.py` (calls Second Brain's own live `/my-day/*`
  API — summary/emails/calendar/todo, `--day` optional) and
  `note_detail.py` (calls the existing `/vault-search/notes/{stem}` for
  one note's full body, so the agent can check a specific Thread's own
  `## Actions` section for the "did I miss something" ask) — same "call
  the real API, never reimplement its logic" pattern `azure-cost-
  calculator` established. SOUL.md is explicitly, deliberately
  READ-ONLY: never writes to the vault, never fills in `## Actions`
  (a human-owned section, `section_ownership.py`), never takes an action
  — sidesteps the still-undecided Approval question entirely by design
  (operator: "The Approval is something we need to discuss I don't know
  how to handle this part yet"), rather than guessing at a flow the
  operator explicitly hasn't decided on. Verified live: both scripts
  return real, correct data against the actual running backend (17
  emails/15 meetings/82 todos for the current window; a real Thread's
  own empty `## Actions` section correctly surfaced via `note_detail.py`
  as a genuine "might need a look" signal); confirmed discoverable via
  `GET /hermes/agents` with exactly one skill, no Second Brain code
  changes needed (the map is a live mirror of every real Hermes
  profile). Left in the default "Data Gatherer" Section (no explicit
  placement instruction was given for this one, unlike the four agents
  moved earlier the same night) — same fallback every other unassigned
  individual Hermes agent gets.

  **Full live end-to-end verification** (real chat turn, `hermes -p
  daily-briefing chat -q "What's on my plate for August 20th, 2026?
  Give me a prioritized rundown."`, 2m26s / 44 tool calls): the agent
  correctly discovered its own Skill and scripts, called `summary`/
  `emails`/`calendar`/`todo` scoped to the real day, then went one level
  deeper via `note_detail.py` on the 4 threads it judged highest-impact
  (an urgent ADNOC RFP, a Compass ops alert, a GPU-demand COB deadline,
  a Masdar onboarding thread) — all 4 genuinely had an empty `## Actions`
  section, which the agent correctly cited as its own real "unresolved"
  signal rather than a vague guess. Produced a genuinely prioritized
  briefing (critical/time-sensitive/customer-impacting tiers, a meeting-
  prep note, emails triaged high→FYI, tasks pulled forward from the real
  82 open, suggested focus blocks) and explicitly flagged its own
  inference where the data was incomplete ("Customer: not set in the
  note (inference: likely external with Invest Bank based on the
  title)") rather than presenting a guess as fact. Took no write action
  of any kind — exactly the read-only/surfacing-only design this build
  was scoped to.
- feat: new top-level Chat page for talking to Primary directly —
  operator: "move the Primary Chat to be Background Agent, Create a new
  Tab we call Chat where we can Chat with this Agent Since it Talks to
  everything." Primary (`default`) is now excluded from the Agents Map
  ring entirely (`agents_map_adapter.py`'s new `_BACKGROUND_AGENTS`
  override, same `is_background_agent: true` mechanism already
  established for the other specialists — deliberately this time, not
  the earlier accidental exclusion), since the new Chat page is now its
  real, primary way to be reached. Extracted the chat UI out of
  `AgentDetailPanel.tsx`'s own inline Chat tab into a new, genuinely
  reusable `AgentChatPanel.tsx` (`features/chat/`) — same exact
  behavior, just no longer duplicated: the side panel's own Chat tab and
  the new standalone `/chat` route both render this one component now,
  parameterized by `agentId`/`agentName`. New `ChatPage.tsx` route +
  Sidebar nav entry. Verified live end-to-end: sent a real message to
  Primary through the new page and got a real reply; reopened
  azure-calculator's own Chat tab in the side panel afterward to confirm
  the extraction didn't regress the embedded case (panel renders, thread
  fills the panel's own height correctly).
- fix: chat's file-attach control was a raw, plain `<input type="file">`
  — operator: "We need the Upload file Button in Chat to be an Icon to
  look better." The real file input stays in the DOM (real picker
  behavior, its own accessible label) but is now visually hidden; a new
  `.chat-attach-btn` icon button (Material Symbols `attach_file`, same
  icon system already used across the Agents Map) proxies a click onto
  it. Verified live: button renders 36x36px with an 18x18px icon glyph
  (comfortably inside the box, no repeat of the earlier Section Hub
  icon-clipping bug), and a real click correctly triggers the hidden
  input's own click event. Applies everywhere `AgentChatPanel` is used
  (the new Chat page and every agent's own side-panel Chat tab), since
  it's the same one component now.
- feat: chat images/links, real ADR-050 follow-through — operator
  (after asking Primary to generate a picture): "it generated it but It
  showed a link, [1] The Link is not clickable [2] The Image should be
  displayed in the chat clicking on it open it in a pop [3] This goes to
  all chats." Root cause: `ChatMessageText.tsx` used zero remark/rehype
  plugins (ADR-050's own deliberate original choice), and CommonMark's
  base spec does NOT autolink a bare URL — a bare-URL reply (the shape
  a generated-image link actually comes back as, not markdown link
  syntax) rendered as inert plain text. ADR-050 itself named this exact
  gap up front as "a cheap, additive follow-on if a future story needs
  it" — added `remark-gfm` (GFM's autolink-literals) now that one does,
  with ADR-050's own safe-by-omission posture fully intact (still zero
  raw-HTML plugins, no `rehype-raw`, no `dangerouslySetInnerHTML`; GFM
  only changes markdown parsing, never HTML handling). New: any link OR
  markdown image whose URL matches a real image extension
  (png/jpg/jpeg/gif/webp/svg/avif, optional query string for a real
  SAS-token/cache-busting URL) renders INLINE as an actual clickable
  thumbnail instead of link text — covers the real case (a bare/plain
  image URL) as well as proper `![alt](url)` markdown image syntax.
  Clicking a thumbnail opens a real full-viewport lightbox (backdrop
  click or Escape to close, Escape wired at `document` level so it
  works regardless of what currently has focus). Since `ChatMessageText`
  is the one shared component every real chat surface already renders
  through (ADR-050 Decision 3, and this session's own new
  `AgentChatPanel` extraction), this one fix covers the Chat page, every
  agent's own side-panel Chat tab, and both Cockpits at once — directly
  satisfying "this goes to all chats." Verified live end-to-end: asked
  Primary to echo back a real bare image URL, confirmed it rendered as
  an actual loaded thumbnail (not text, not a bare link) in both the
  user's own echoed bubble and Primary's reply, clicked it into the
  lightbox (confirmed via `getBoundingClientRect` — full 1400x900,
  top:0/left:0 — the screenshot tool's own capture scale made it look
  cropped, not a real bug), and confirmed both close paths (backdrop
  click, Escape) work. TypeScript typecheck clean.
- feat/fix: Vault note detail page — operator: "The md file viewer looks
  bad very bad Structure and looks like it was Dumped inside the Page
  uncleaned, Images are not shown (EGA file if the only file with Decent
  Content use it as a Sample to Fix) I need this Page to be Beautiful
  and readable with Jumps to section." Used the real
  `EGA_Updated_HLD_17Mar23_MASTER_DECK` File note (112-slide HLD summary
  with real `## Summary`/`## Details` sections, a long nested bullet
  breakdown, and three `![[slide-N.png]]` Obsidian image embeds) as the
  actual reference case throughout, per the operator's own instruction.
  - **Images now render.** Root cause: this codebase had NO backend
    route to serve a raw vault asset at all — `![[slide-14.png]]` isn't
    standard CommonMark, and even resolved, there was nowhere to fetch
    the bytes from. New `GET /vault-search/notes/{stem}/assets/{filename}`
    (`vault_search.py::resolve_asset_path`) serves a note's own real,
    co-located sibling file (confirmed live: capture writes an image
    into the SAME folder as its own `.md`), with real path-containment
    validation (never serves outside that one folder). `NoteBody.tsx`
    now resolves `![[filename]]` embeds to real `![alt](url)` markdown
    image syntax BEFORE handing text to `react-markdown`, processed
    strictly before plain `[[wikilink]]` resolution (the embed syntax
    contains the wikilink syntax as a literal substring). Verified live:
    all 3 real slide images (1280px each) load and render.
  - **Jump-to-section.** New `tableOfContents.ts` (shared by `NoteBody`
    and `NoteDetailPage`) + `rehype-slug` assign every heading a real
    id and render a sticky ToC rail alongside the note's own body
    (`.note-detail-layout`, collapses to one column under 960px). First
    attempt hand-rolled the id/counter logic and shipped a real bug,
    caught by live testing: a plain counter mutated during React's own
    render desynced under StrictMode's double-invoked renders (Summary
    got `id="details"`, Details got no id at all) — switched to
    `rehype-slug`/`github-slugger` (a pure AST transform, not a
    render-time side effect) for the actual id assignment, with
    `tableOfContents.ts` using the same underlying library so the two
    independently-computed id sets can never disagree. Verified live
    post-fix: correct ids, correct jump (`.main`/`html` both get
    `scroll-behavior: smooth` — confirmed live which element actually
    scrolls varies by page).
  - **Visual structure.** h2 now gets a bottom rule + real top spacing
    (chapters read as chapters, not a wall of text); nested lists get
    real vertical rhythm; images are capped/centered/bordered so a
    1500px+ slide screenshot doesn't dominate the page, with the
    following caption paragraph styled distinctly via `:has()`.
  - **Real bug found and fixed while styling this:** `--space-5` does
    not exist anywhere in `tokens.css` (the scale jumps `--space-4` →
    `--space-6`) — every `var(--space-5)` in the new CSS silently
    resolved to nothing (an undefined custom property makes the whole
    declaration invalid, falling back to the property's own initial
    value), so list `padding-left` computed to a real `0px` despite the
    rule being present and matched — reported live: "The Bullet Points
    appear before the title should have been pushed inside a bit."
    Fixed to `--space-6` (24px) everywhere in the new CSS, and swept
    the WHOLE frontend for the same already-broken pattern: found two
    more real, pre-existing instances in `agents-map.css`
    (`.map-search-input`/`.map-search-empty`, both silently losing
    their entire `padding` shorthand the same way, unrelated to this
    task but the same class of bug, fixed in the same pass rather than
    left known-broken). Verified live: list items now sit a real 24px
    right of their own heading.
  - Also fixed while in this same code: a real Thread/Meeting note that
    genuinely wikilinks the same target twice (e.g. `[[Microsoft]]`
    mentioned in both `## Summary` and `## Details`) listed it TWICE
    under "Forward links" — `_resolve_forward_links` now dedupes by
    resolved stem. TypeScript typecheck + backend compile-check clean.
- fix: three real chat problems in one pass -- operator: "The Context
  disappear every Message no Memory... it didn't know how to show it as
  a picture... The Bullets Structure is missed up... in the Chat and in
  what's app."
  - **Real session continuity.** Root cause confirmed by reading the
    code directly: `POST /agents/{id}/chat` opened a BRAND NEW
    `HermesChatSession` (a genuinely fresh `session.create`, no prior
    `session_id`) on every single call and closed it in `finally` -- so
    Hermes' own gateway, which DOES carry real multi-turn history
    forward keyed by `session_id` (the same mechanism an interactive CLI
    session already relies on), had no way to know two consecutive
    messages were even the same conversation. New
    `app/business/hermes/chat_sessions.py` keeps one live session open
    PER AGENT across requests (a per-agent `asyncio.Lock` serializes
    concurrent turns against it), only replaced when confirmed dead.
    New `POST /agents/{id}/chat/reset` (+ a "New chat" button,
    `AgentChatPanel.tsx`) explicitly ends a conversation on request --
    the only way to make an agent pick up a changed SOUL.md
    mid-conversation too (MEMORY.md's own "session prompt injected once,
    never re-read" constraint). Verified live end-to-end at the network
    level across two genuinely separate HTTP requests: told Primary "my
    favorite number is 42" in one call, asked "what is my favorite
    number" in a completely separate call minutes later -- got back
    "42.". Confirmed the reset endpoint itself works correctly too (a
    real, different session_id before vs. after, verified via a direct
    Python script) -- a *separate*, expected finding along the way:
    Primary still recalled "42" even after a genuine session reset,
    because it had used its own long-term memory tool (it was
    explicitly told "just remember it"), a real feature independent of
    Hermes' own session-scoped conversation continuity -- not a bug in
    the reset.
  - **Real images in chat.** Root cause: Primary reads the vault
    directly (real filesystem tools) and could describe an image's
    existence, but had no way to actually SHOW one -- it didn't know
    Second Brain's own new asset-serving convention (added earlier this
    session) at all. SOUL.md now teaches it both real mechanisms: a
    markdown image link built from the note's own real stem + the
    image's own real filename, pointed at
    `http://127.0.0.1:8001/vault-search/notes/{stem}/assets/{filename}`,
    for this chat's own UI (renders as a real inline image,
    ChatMessageText.tsx's own earlier fix); the real
    `send_message(..., message="... MEDIA:<real local path>")`
    attachment convention for WhatsApp specifically, since a
    `127.0.0.1` URL is meaningless off this machine -- confirmed the
    real mechanism by reading send_message_tool.py's own source
    directly rather than guessing. Verified live end-to-end (reset the
    session first so the SOUL.md change actually took effect -- session
    prompts are injected once, per the constraint above): asked Primary
    "tell me what we know about EGA Architecture, and show me the
    target architecture picture" -- it replied with a real, correctly
    structured summary AND a genuinely loaded 1280px inline image
    (confirmed via naturalWidth/complete), clickable into the same
    lightbox built earlier this session.
  - **Well-structured replies.** Root cause in agent-panel.css:
    `.chat-message` still had `white-space: pre-wrap` -- a leftover from
    BEFORE ADR-050 added real markdown rendering, preserving every
    literal newline in the raw source text on TOP of react-markdown's
    own block-level `<p>`/`<li>` spacing, doubling it; `.chat-message`
    also never styled its own `p`/`ul`/`ol`/`li`/`code`/`pre` output at
    all (bare browser defaults). Removed the stale rule, added the same
    real spacing/list treatment `.note-body` got earlier this session
    (tuned tighter for a narrow bubble). Also added WhatsApp-aware
    guidance to SOUL.md itself (flat lists, one level of nesting at
    most, no markdown headers/tables -- WhatsApp's own renderer doesn't
    support them, `##` just shows as literal characters) since that
    surface can't be fixed with CSS at all. TypeScript typecheck +
    backend compile-check clean; WhatsApp's own rendering not
    independently verified (no live WhatsApp access in this session) --
    the guidance is real and correct per Hermes' own documented
    formatting limits, but flagged here as unverified on that one
    specific surface.
- feat: built the Compass Expert agent family -- operator: "I need to
  build Compass Expert (Since I am Selling it)... He Can talk to
  Multiple Agents Compass Pricing Expert... Compass Solutions... Compass
  Models Expert... How can we build that in Vault, Hermes and Agentic
  Map." A real design discussion preceded the build (relay pattern,
  KB source/refresh cadence, whether the dependency-tree view was
  already free) -- see MEMORY.md for the resolved decisions.
  - **Vault:** `Work/Technology/Compass/` -- a new top-level Technology
    domain (not a flat `Work/Compass/`, corrected live: "technology
    should be a full section... that has Compass under it," leaving
    room for a future technology beyond Compass without restructuring),
    with `Pricing/`/`General/`/`Solutions/`/`Models/` sub-areas, each
    holding real per-topic notes (corrected live: "we might have
    multiple files... it will be massive," not one file per area) plus
    a real `Compass.md` hub note. Models is deliberately ONE list note,
    not a folder of deep files (operator: "its not compass Technology
    its External Models Compass Exposes"), structured so a specific
    model can be promoted to its own note later without restructuring.
    Every doc carries both a real tag (`technology/compass`,
    `compass/<area>`) AND a `[[Compass]]` wikilink back to the hub --
    the same dual pattern already used everywhere else in this vault
    (operator: "We need to be able to support tagging").
  - **Hermes:** 4 new profiles (`compass-expert`,
    `compass-pricing-expert`, `compass-solutions`,
    `compass-models-expert`), same narrow-mandate clone pattern as
    every other specialist this session. `compass-expert` is Primary's
    new relay target (added to `SOUL.md`'s own specialist list) AND
    itself relays to its own 3 specialists the same way Primary relays
    to opp-manager -- a genuine two-level chain, confirmed live end-to-
    end (`hermes -p compass-expert chat -q "..."` correctly relayed to
    `compass-pricing-expert` and reported its reply back). The 3 subs
    never write to the vault or reach WhatsApp directly (operator: "We
    will not Expose all to Whats app") -- `compass-expert` is the SOLE
    real KB writer, via a new `compass-kb-writer` Skill
    (`write_compass_doc.py`, modeled directly on `notes-manager`'s own
    `capture_note.py`) -- verified live with a real write + read-back,
    correct frontmatter/tags/wikilink, then removed (scratch
    verification only). A real recurring cron job
    (`compass-kb-refresh`, `hermes -p compass-expert cron create
    "every 20160m" ...` -- 2 weeks, operator's own real cadence)
    researches Pricing/General/Models via Hermes' own native
    `web_search`/`web_extract` (no new engineering needed there) and
    writes updates through the same script; `compass-expert`'s own
    SOUL.md also covers the manual path (Mahmoud handing it a document/
    tidbit any time, same write mechanism). Gateway isn't running in
    this dev environment, so the cron job won't fire on its own here --
    flagged, not a bug in the registration (confirmed correct: "every
    20160m", not the mis-typed "once in 20160m" a bare `"20160m"`
    schedule string produces without the `every` prefix).
  - **Agents Map:** real discovery while investigating -- the
    depends_on TREE-RENDERING mechanism already existed and was fully
    generic (`layoutAgents.ts`'s own `computeAgentDepth`/
    `assignTreeAngles`/`buildDependencyEdges`, reading `agent.
    depends_on` directly, never Pipeline-specific despite the earlier
    MEMORY.md note suggesting otherwise) -- the ONLY gap was
    `agents_map_adapter.py` hardcoding `depends_on: []` for every real
    Hermes agent. New `_AGENT_DEPENDS_ON` override (same shape as the
    existing `_AGENT_TYPE`/`_AGENT_SECTION` maps) wires the 3
    specialists' own real `depends_on: ["compass-expert"]`. All 4 land
    in Technology (`_AGENT_SECTION`). Verified live: a real, visually
    connected tree renders on the map -- Technology Hub -> azure-
    calculator (separate) and Technology Hub -> compass-expert ->
    its 3 real sub-agents, confirmed via a live screenshot showing the
    actual connecting lines, not just the data being correct.

  **Full relay chain verified live end-to-end** (real `hermes -p
  compass-expert chat -q "What's Compass pricing like?..."`, 3m40s):
  compass-expert correctly relayed to `compass-pricing-expert` via the
  real one-shot mechanism (`hermes -p compass-pricing-expert chat -q
  "..." -Q --create-if-missing -c "compass-pricing-qa"`), which honestly
  checked the (currently empty) Pricing folder and reported that
  plainly rather than fabricating pricing data -- compass-expert then
  synthesized the reply back in its own words and proactively offered
  two real next steps (get official docs added, or research from the
  official Compass/Core42 source). Confirms the two-level relay chain,
  the "never fabricate" discipline, and the "subs report findings back
  rather than acting on them" design all work exactly as specified.
- feat: made the Compass KB refresh actually smart, not just a vague
  "go research and write" instruction -- operator: "we need it to be
  Smart what info to bring what info to skip and how to classify it,"
  then handed the real source: https://www.core42.ai/compass/
  documentation. Fetched it live rather than guessing -- confirmed its
  own real section taxonomy (Get Started, Model Pricing, Model
  Capabilities, How-To's, API Reference, Agents, Chat Enterprise, FAQs,
  Changelog). Added a real "Keeping the KB current" section to
  `compass-expert`'s own SOUL.md: a concrete docs-section -> KB-area
  mapping table (Model Pricing -> Pricing/, Get Started/How-To's/FAQs
  -> General/ as SEPARATE topic notes, API Reference skipped by default
  as pure developer-integration detail, Changelog used to decide what
  to re-check rather than written as its own note, and an explicit
  confirmation that no real "Solutions" section exists in the official
  docs at all -- that area stays empty from automated research by
  design, only a real hand-described pattern from Mahmoud goes there);
  real keep/skip criteria (concrete facts vs. marketing language/
  duplicate content/page furniture/pure API-reference minutiae); and an
  explicit "check for an existing same-topic note before writing" rule
  so a refresh updates in place rather than fragmenting into near-
  duplicate notes. Re-registered the cron job with a tightened prompt
  pointing at the real URL and this new SOUL.md section by name, rather
  than the original generic instruction. Verified live with a scoped
  real test (research just Model Pricing, write one real note) before
  trusting the full recurring job to it.

### 2026-08-24

- fix: Outlook capture never pulled Sent Mail into Threads (operator:
  "We didn't pull the outbox to the threads (I guess its a must)") --
  `email-thread-capture/scripts/outlook_lib.py`'s own `list_recent_mail`
  only ever queried the Inbox folder, so a Thread's own history only
  ever showed the received half of a real conversation, never Mahmoud's
  own replies/forwards. Extracted the existing restrict/iterate/filter
  logic into a new `_list_folder_mail(folder, ...)`, called once for
  Inbox and once for the newly added Sent Mail folder (`_OL_FOLDER_
  SENT_MAIL = 5`), merged and re-sorted by `received`, then trimmed to
  the real `limit` -- confirmed live that `ReceivedTime` is populated on
  a real Sent Item too (no conditional SentOn/ReceivedTime branching
  needed) and that a Sent Item's own `SenderEmailAddress` resolves via
  the same existing EX-type `GetExchangeUser()` path, reused unchanged.
  Verifying this surfaced a separate, real, pre-existing crash --
  `UnicodeEncodeError` on a genuine U+202F character in a real email --
  fixed with `sys.stdout.reconfigure(encoding="utf-8")` in
  `list_recent_emails.py`, plus explicit `encoding="utf-8"` on both
  orchestrators' own `subprocess.run()` calls (`run_delta_capture.py`,
  `run_full_capture.py`) so the parent side decodes the child's own
  UTF-8 output correctly too.
- fix: `BUG-036`/`BUG-038` -- Meeting-series/Person notes filed under a
  raw Outlook internal identifier instead of their real name, which
  turned out to also mean 7 recurring series and 17 one-time meetings
  each existed as a full DUPLICATE note (operator, same message: "I can
  See some meetings are pulled but their titles hasn't been updated").
  Root causes fixed in `meeting-capture/scripts/vault_lib.py` (and the
  identical, hand-kept-in-sync copy in `email-thread-capture/scripts/
  vault_lib.py`): (1) a LegacyExchangeDN returned by a failed
  `GetExchangeUser()` GAL lookup was trusted at face value as a real
  email address -- new `_looks_like_real_email()` guard falls back to a
  name-based dedup key/filename instead, and never writes the raw DN
  into a Person note's own `email` frontmatter field; (2) no self-
  healing rename existed for a Meeting series once its own concept
  folder was created under a raw id, so the dedup scan kept topping up
  the same badly-named folder forever -- new `rename_meeting_series_
  if_needed()` mirrors `rename_thread.py`'s already-proven pattern
  (collision-safe hash-suffix fallback included), called on every
  `ingest_meeting.py` run. Live-testing the rename fix against the real
  vault surfaced the duplicate-note issue itself (`BUG-038`): the old
  pre-`2026-08-21` flat one-time-meeting file shape is structurally
  invisible to the current dedup scan (`list_meeting_concept_notes`
  only globs folder-shaped notes), so a post-rewrite capture pass
  always created a second, correctly-shaped note alongside the old one
  rather than finding and topping it up. Operator chose to archive
  (never delete) the raw-ID/stray-file side of each pair rather than a
  full content merge -- all 24 real instances (7 series folders, 17 flat
  files, 1 broken-DN Person note) moved intact to `_Archived Duplicates
  (2026-08-24)/` subfolders under `Work/Meetings/` and `Work/People/`,
  leaving the correctly-named/foldered copy as the sole live note.
  Also applied the same `encoding="utf-8"` fix found in the email
  scripts to `meeting-capture/scripts/list_recent_meetings.py` and
  `run_full_meeting_capture.py`'s own `run_script()` -- same latent
  crash risk, not yet triggered live, fixed proactively for
  consistency.
- fix (follow-up, same day): reverted the `rename_meeting_series_if_
  needed()` auto-call from `ingest_meeting.py` after live verification
  repeatedly recreated hash-suffixed duplicate folders (e.g. "Weekly
  Forecast l Strategic Clients-6e2f3e06") on runs that should have been
  clean no-ops -- root cause not conclusively pinned down (this vault
  path isn't under OneDrive and isn't itself a git repo, ruling out the
  two most obvious external-restore explanations; something is still
  re-materializing an old raw-id folder between runs). The function
  itself tested correct in isolation and is collision-safe (never
  overwrites), so it's left defined in `vault_lib.py` for manual/on-
  demand use, just not wired into the automatic capture path until the
  real cause is confirmed. `ingest_meeting.py`'s recurring branch is
  back to its original plain resolve-or-create. Every duplicate this
  produced during testing was archived (never deleted) alongside
  `BUG-038`'s own cleanup. `BUG-036` reopened to `Open` (Person-note
  half stays fixed; Meeting-series self-heal is not live) to reflect
  this honestly rather than leave it marked Closed.
- fix: `BUG-039` -- Agents Map's Technology drilldown never drew a line
  from `compass-expert` down to `compass-solutions`, even though its
  real `depends_on` was already correct (confirmed live via `GET
  /agents`). Root cause: `layoutAgents.ts`'s own `MAX_OUTGOING_
  CONNECTIONS = 2` cap, a real 2026-08-15 decision scoped to pipeline
  Job fan-out, silently also capped an individual AGENT's own outgoing
  edges -- `compass-expert` is the first agent with 3 real dependents.
  Raised the cap to 3 (real pipeline Jobs never exceed 2 by the cap's
  own documented data-model constraint, so their rendering is
  unaffected). Verified live: re-read the drilldown's own SVG line/node
  coordinates before and after, confirmed the third edge now renders,
  screenshot taken.
- feat: built the Azure Expert agent family (operator: "We will build now
  Azure Expert Agent, He will have many Agents under it") -- the second
  real "one domain, one Hermes profile" specialist family, one level
  DEEPER than Compass Expert's own two-level chain: `azure-expert` (new
  profile, Primary's own new relay target, sole real owner of
  `Work/Technology/Azure/` writes) relays to `azure-services-expert` (new
  -- Azure's real service catalog, categorized `Services/<Category>/`
  short notes with a live Microsoft Learn link, `web_search`/
  `web_extract` for anything not covered locally) and
  `azure-enterprise-architect` (new -- Landing Zone/Enterprise-Scale
  reference architecture, and itself relays further to `azure-data-
  architect`/`azure-infra-architect`, both new -- data platform and
  infra/compute/network reference architectures respectively). `azure-
  calculator` moved from independently, directly reachable to a plain
  relay-only specialist under `azure-expert`, the same reachability shape
  `compass-pricing-expert` already has under `compass-expert` (SOUL.md
  rewritten accordingly; no longer directly reachable by Mahmoud/Primary).
  New `azure-kb-writer` Skill (`write_azure_doc.py`, adapted from
  `compass-kb-writer`) handles the two real structural differences from
  Compass's own writer: a required `category` for Services, and
  Architecture split into 3 separate real areas rather than one. New hub
  note `Work/Technology/Azure/Azure.md` carries real substantive content
  directly in 3 named sections (What is Azure / Sovereignty in Azure / How
  to start an Enterprise company in Azure) -- a deliberate difference from
  Compass.md's own structure-only hub, per the operator's own explicit
  ask; placeholder text until azure-expert's own first live research pass
  fills them in (never fabricated by hand). Wired
  `agents_map_adapter.py`'s `_AGENT_SECTION`/`_AGENT_DEPENDS_ON` for all 6
  new/moved agents (all Technology, matching the real 3-level relay
  chain), and swapped Primary's own SOUL.md relay-list entry from a
  nonexistent direct `azure-calculator` route to a new `azure-expert`
  entry mirroring `compass-expert`'s own. Verified live: fetched `GET
  /agents` directly and re-derived the drilldown's own SVG line endpoints
  against each node's real on-screen position, confirming all 8 real
  dependency edges render (including hitting `MAX_OUTGOING_CONNECTIONS`
  right at its newly-raised limit of 3 for `azure-expert` itself, without
  tripping `BUG-039` again), screenshot taken.
- feat: `type: "expert"` -- operator: "We need to change the type of
  Agents that Are Experts to be Experts instead of Workers as well".
  `AgentType`'s own `'expert'` value, and a real amount of dedicated
  frontend UI for it (`AgentDetailPanel`'s own "Knowledge gaps" tab,
  `CreateAgentWizardModal`'s own Expert-creation flow), had been built
  ahead of any real data ever using it (module docstring's own "no
  Experts Yet" note, 2026-08-22). Flipped `_AGENT_TYPE` for every real
  domain-knowledge specialist in both families -- `compass-expert` and
  its 3 specialists, `azure-expert` and its 5 (including `azure-
  calculator`) -- from the default `worker` to `expert`; `opp-manager`/
  `notes-manager`/`files-manager` deliberately untouched (pipeline-style
  capture/action agents, a different real category). Verified live: the
  Agents Map now shows a real `expert` badge and a working "Knowledge
  gaps" tab on `azure-expert`'s own detail panel.
- **Found + worked around, not a code fix**: the backend's own `uvicorn
  --reload` did not reliably pick up 3 consecutive edits to
  `agents_map_adapter.py` in this same session -- `GET /agents` kept
  returning pre-edit data for several minutes across multiple confirmed
  "WatchFiles detected changes... Reloading..." log lines, verified both
  through the browser AND a direct `curl` (ruling out a browser-side
  cache). A full `preview_stop`/`preview_start` cycle (a genuinely fresh
  process, not a reload) picked up every accumulated edit correctly on
  the first try. See MEMORY.md's own new entry -- worth a clean restart
  before spending more time debugging "my Python change isn't showing up"
  against this dev setup specifically.
- feat: Meeting/Inbox Cockpit UI makeover (`BUG-037` fix) -- operator
  whiteboarded the new layout live: left secondary nav
  (Overview/Chat/People/Documents/Articles) replacing the old fixed
  left Agents/research panel, and a right rail that swaps between
  Meeting/Email info (every prep tab) and a real Experts-only list
  (Chat tab, `type === 'expert'`, recommended slot reserved for a
  future Research Expert). `Cockpit.tsx` rewritten around this layout;
  `cockpitApiClient.ts`'s `CockpitData` contract simplified to
  `subject`/`people`/`overview`/`thread` (drops the old
  bring-in/message/research/proposal/attachment client calls --
  deliberately not rebuilt this pass). New, minimal
  `app/api/cockpit_router.py` replaces the archived one: reuses only
  `business/cockpit/people.py` (self-contained, vault-only, still
  correct) for real subject/people data; `overview`
  (`summary`/`related_documents`/`articles`) and `thread` come back as
  honest empty stubs, never fabricated, since the Research Expert prep
  pass and Hermes-backed chat are real "service" work the operator
  deferred to a separate discussion. Removed `AttachmentsPanel.tsx`
  (orphaned by the contract change; attachment hand-off is out of
  scope this pass). Verified live: both `/meeting-cockpit/:stem` and
  `/inbox-cockpit/:stem` load with zero console errors, real attendee
  chips resolve to real Person notes (31 on a real Core42 meeting),
  real meeting time/location/Teams-link/organizer render in the right
  rail, and the Chat tab correctly swaps to a real 11-agent Experts
  list with an honest "Chat isn't wired up yet" state instead of a
  fake-looking composer.
- fix/feat: Cockpit polish round, 3 operator-reported issues in one
  pass. (1) "not a fan of the Cards look" -- first pass only dropped
  `.card`'s border but kept the same raised-background-per-section
  repetition, which still read as cards; Overview's 4 sections now
  share ONE `.cockpit-panel`, divided by a `.cockpit-section` hairline
  border, not 4 separate boxes. (2) Experts panel restyled to icon +
  name rows (real Material Symbols icon via `getVisualIconName`,
  reusing `AgentNode.tsx`'s own convention) with the existing
  `a.item-row`/`button.item-row` hover highlight instead of a separate
  "+ Bring in" button; roster split into "In this chat"/"Bring in
  another Expert" groups in ONE panel rather than two sub-tabs
  (reasoning: avoids a third layer of tabs nested inside the Cockpit's
  own nav, for something glanced at constantly during a live meeting);
  clicking an in-chat Expert removes them (not an @mention insert --
  typing `@` in the composer already covers addressing a message,
  clicking a roster row is a "manage this participant" action, the
  same split Slack/Teams already use). Bring-in/remove is real,
  clickable, local component state -- not yet persisted, since there's
  still no Chat backend to persist it to (disclosed to the operator,
  not silently faked). (3) "I lost track of the meeting" -- clicking a
  Person chip used to navigate to `/browse/:stem`, a separate page;
  new `PersonNotePanel.tsx` renders the SAME `fetchNoteDetail`+
  `NoteBody` content inside the Cockpit's own side panel instead
  (reuses `AgentDetailPanel.tsx`'s existing `.side-panel-overlay`/
  `.side-panel` convention), so the meeting is never unmounted.
  Follow-up in the same pass: the panel wasn't showing frontmatter at
  all (where most of a Person note's real info lives -- email/phone/
  linkedin) -- added an explicit Person-field KV list plus a generic
  fallback loop for any other frontmatter key, so nothing is silently
  dropped. Also added real "add a note" capability -- operator: "Notes
  about the person during the meeting, saved to their note is needed
  we still can't edit notes anywhere" -- new
  `business/cockpit/notes.py`'s `add_person_note` calls
  `vault_writer.append_body_section_line` (an existing, already-tested
  primitive, REQ-SB-55-US-01-T01) against a real `## Personal Notes`
  section, timestamped, mirroring the same section convention Meeting/
  Thread notes already use. New `POST /cockpit/person/{stem}/notes`.
  Scoped deliberately narrow -- Person notes only, not general note
  editing (a real, separate, bigger gap the operator flagged but
  hasn't asked to build yet). Verified live end-to-end: typed a real
  note, confirmed `200 OK`, confirmed the exact new `## Personal
  Notes` section + timestamped line landed on disk in the real vault
  file, then removed that test entry afterward (verification-only,
  not something the operator actually said about the real person).
- feat: built the 3 Customer Experts (REQ-SB-83) -- `masdar-expert`,
  `adnoc-expert`, `taqa-expert`, same clone/SOUL.md/verify pattern as
  the original Azure Expert build. Sales Section, `type: "expert"`, no
  `depends_on` (one Expert per customer, per the operator's own "for now
  its one Expert per Customer today"). Each reads that ONE customer's
  real vault folder (`Work/Customers/<Name>/`) plus anything tagged
  `customer/<slug>` fresh on every question, never writes (points to
  `opp-manager` for any create/update ask). Wired into
  `agents_map_adapter.py` and Primary's own SOUL.md relay list.
  Verified live, all 3, real grounded answers against real vault data:
  Masdar's real "Data Platform" Opportunity (correctly found via tag
  search despite being filed as a Mubadala Affiliate, not its own
  top-level Customer folder), Adnoc's real "Azure Data Manager for
  Energy" Opportunity (~$50k/month), TAQA's real Affiliate breakdown
  (Ewec/Taqa Water Solutions/Taqadistribution, named contacts, recent
  log entries) with an honest "no dedicated Opportunities folder" where
  that's genuinely true. Real bug found and fixed along the way:
  `OBSIDIAN_VAULT_PATH` is unset system-wide, so the bundled `obsidian`
  Skill silently resolves to a nonexistent path unless the vault's
  absolute path is stated explicitly in the profile's own SOUL.md --
  see MEMORY.md.
- feat: registered `research-agent` (`REQ-SB-82-US-02-T01`, `ADR-008`) in
  `agents_map_adapter.py`'s `_AGENT_TYPE`/`_AGENT_SECTION` dicts --
  `type: "expert"`, `section: "Librarian"` -- so Second Brain's own Agents
  Map UI places and types it correctly the moment the real `research-agent`
  Hermes profile is provisioned (`T02`). Second Brain's own
  presentation-layer concern only; inert until the real profile exists.
  Verified live both in-process (monkeypatched `hermes_definitions.
  list_agents()`) and against a real running server's `GET /agents`
  response (`research-agent` correctly absent today; zero regression to
  any of the other 22 real agents/pipelines' own `type`/`section_id`).
- feat: `REQ-SB-82-US-05-T02` (`ADR-010`) — new
  `Hermes-Provisioning/cron/meeting-prep-agent.md` cron declaration
  (`schedule: {"kind": "interval", "minutes": 720}`, `deliver:
  "whatsapp"`, the real prompt text), plus the real, live
  `meeting-prep-agent` Hermes profile + cron job provisioned on the
  operator's actual Hermes install: `hermes profile create
  meeting-prep-agent --clone`, a new real `SOUL.md` (twice-daily
  scan/delegate/notify/suppress procedure), `T01`'s `person-lookup`
  Skill installed, real cron job `7b8f10e528ab` created
  (`hermes -p meeting-prep-agent cron create "every 720m" ...
  --deliver whatsapp --skill person-lookup`), gateway installed as a
  Windows login item. Closes `REQ-SB-82-US-05` — both tasks now `Done`.
  Verified live: an independent direct `hermes -p research-agent chat
  -q ...` relay call (real `web_search`-backed note written to
  `Work/Research/`); a real delegation triggered FROM
  `meeting-prep-agent` itself against a real, disposable scratch Meeting
  note (genuinely-unfamiliar topic → real Research Agent finding
  written); a real "nothing to find" control case against a second
  scratch meeting, correctly staying silent; a real plain-language
  suppression instruction, confirmed persisted to the profile's own
  native memory and re-confirmed HONORED in a brand-new session with
  zero prior conversation turns (a genuine cross-session persistence
  proof) against the same meeting that would otherwise have real
  findable data; the cron job's own `every 720m`/`deliver: whatsapp`
  registration confirmed live via `cron list`/`cron status`. All scratch
  vault/Person notes and the test memory entry cleaned up afterward (a
  real, unrelated-domain research note from the independent relay test
  left in place, matching `REQ-SB-82-US-02-T02`'s own precedent). Two
  real, disclosed findings, neither blocking a locked AC (see
  `MEMORY.md`): Hermes' own "remember" tool auto-routed the suppression
  fact into `memories/MEMORY.md` rather than the `memories/USER.md`
  `ADR-010` named (both are equally real, native, always-injected
  per-profile memory); a freshly-cloned profile's own gateway can't stay
  running unattended until its WhatsApp is separately, manually paired
  (`hermes -p meeting-prep-agent whatsapp`, a real operator follow-up
  action, not completed this session) — so AC-04/AC-05's literal
  WhatsApp-send half and AC-08's literal unattended-fire half are
  disclosed as configuration-confirmed/decision-logic-proven rather than
  fully live-observed end-to-end, per the task's own pre-authorized
  verification methodology for a 12h+ cadence. `SPRINT-077` (both its
  stories now `Done`) closed the same pass — see its own drafted
  Retrospective.

### 2026-08-27

- fix: Data-quality bug (operator: "Something Keeps Creating log capture
  and index in Mubadala and Core42 and DGE and few More this is
  destroying the data Quality") — orphaned, boilerplate `index.md`/
  `log.md`/`captures.md` files kept reappearing alongside the real,
  name-prefixed hub files (`<Customer>.md`, `<Customer>-log.md`,
  `<Customer>-captures.md`) in 10 of 15 real `Work/Customers/` folders.
  Root cause: `app/api/email_poc_router.py` — an unguarded, ~25-endpoint
  legacy debug/maintenance router (prefix `/poc`), mounted in `main.py`
  with zero live trigger (no scheduler, no MCP tool path, no frontend
  caller — confirmed by direct grep) but directly reachable by anyone
  who could POST to it, the only surviving path into
  `customer_hub_linking.ensure_customer_hub_note` and its siblings after
  the 2026-08-24 `capture_scheduler` lifespan retirement (see that
  entry's own comment in `main.py`). Fixed by deleting
  `email_poc_router.py` outright and removing its import/mount from
  `main.py` — the business modules it called into
  (`customer_hub_linking.py`, `email_classification.py`, etc.) are left
  in place, since other real, non-router code
  (`partner_hub_linking.py`, `vault_migration.py`) still imports them
  directly. Verified live: `/poc/*` now 404s; `/boot-status`,
  `/sections`, `/vault-search/status` all still 200. Cleaned up the 6
  still-affected customers' bare files after content-verifying every one
  as pure boilerplate (`# <Customer>\n\n- [[<Customer>]]` / empty body) —
  operator explicitly chose delete over archive for these specific,
  zero-content files (Azerbaijan/AzinTelecom/ILOE/Idda/Microsoft Azure,
  the other 5 originally-affected customers, were independently removed
  by the operator mid-investigation, unrelated to this bug). See
  `MEMORY.md` for the open question this didn't fully close (DGE's bare
  files were regenerated as recently as today, after the 2026-08-24
  scheduler fix was already in place — `/poc` closes the only KNOWN live
  path, but the exact trigger for that specific recreation was never
  conclusively identified).
- fix: Backend port 8001's zombie-socket issue (flagged as unresolved
  earlier this session, see the 2026-08-24 [Unreleased] entry above) —
  actually root-caused and fixed while restarting for the `/poc` removal
  above. The "phantom" LISTEN-owning PIDs `netstat`/`Get-NetTCPConnection`
  kept reporting were dead `uvicorn --reload` parent processes, but each
  had spawned a Windows `multiprocessing` reload child
  (`spawn_main(parent_pid=...)`) that inherited the listening socket
  handle and stayed alive after the parent died — confirmed by matching
  `Get-CimInstance Win32_Process`'s `parent_pid=` argument on the live
  child processes directly against the dead phantom PIDs. Killing those
  orphaned children (not the long-gone parents) released the socket for
  real; no reboot needed after all.

- refactor: Extracted `app/hermes/` — a reusable, Second-Brain-agnostic
  Hermes client library (operator: "Zero Software Engineering, Zero
  Architecture, and No OOB Basics... this Library knows nothing about
  our Second Brain its a Reusable Component of Hermes to do everything
  we used today any future need of hermes will go there as well"). Every
  prior direct-to-Hermes module (`data_access/hermes_client.py`,
  `hermes_ws_client.py`, `hermes_definitions.py`, `hermes_cron.py`,
  `api/mcp_auth.py`) is deleted and replaced by namespaced classes under
  `app/hermes/`: `HermesRestAPI` (status/sessions), `HermesChatSession`
  (live WS chat), `HermesProfiles`/`HermesSkills` (full CRUD — get_all/
  find_by_id/read/create/update/delete — over profile.yaml/config.yaml/
  SOUL.md/SKILL.md, direct file I/O since none of these have a real CLI
  equivalent), `HermesCron` (job/execution history), `HermesCLI`
  (subprocess wrapper for `hermes.exe` — profile create/delete/describe,
  gateway start/stop/restart/status/configure, dashboard start/stop/
  status, system status, cron run — used wherever a real CLI command
  exists, since e.g. `profile create --clone` does real work a plain
  mkdir can't replicate), and `RequireHermesSharedSecret` (inbound auth).
  `HermesClient.init(base_url, home_path, api_key,
  inbound_shared_secret)` composes all of them; nothing under
  `app/hermes` imports `app.config`. Exactly ONE file in the whole app,
  `app/business/hermes/client.py`, is allowed to import from
  `app/hermes` and construct the singleton `HermesClient` — every other
  consumer (routers, `main.py`, `vault_index_router.py`'s cron-rebuild
  trigger, `tools/registry.py`'s inbound-auth wrapping) goes through
  `get_client()` (operator: "All call that goes to something in hermes
  goes throw that library"). Also relocated the Pipeline/Tool JSON
  definitions (`company-discovery.json`, `meeting-builder.json`,
  `threads-builder.json`, `tools/registry.json`) out of the source tree
  into `<second_brain_data_path>/pipelines/` and `.../tools/` — real,
  live-edited Second Brain Data (operator: "these are not static we keep
  changing them... these are for sure Second Brain Data"), never static
  source-tree fixtures. Found and fixed a real bug along the way:
  `subprocess.run(..., text=True)` decodes Hermes' own CLI output with
  Windows' console codepage (cp1252) by default, which crashes on the
  real UTF-8 checkmarks Hermes prints — fixed with explicit
  `encoding="utf-8", errors="replace"`. Verified live end-to-end after a
  clean backend restart: `/hermes/status`, `/hermes/agents`, `/agents`,
  `/pipelines`, `/tools/outlook`, `/mcp` all correct; the new read-only
  CRUD additions (`profiles.read_soul`, `skills.get_all`/`read`,
  `cli.get_system_status`, `cli.gateway_status`) all confirmed against
  the real install. `create_profile`/`delete_profile`/`describe_profile`
  are NOT live-tested (would mutate a real Hermes profile) — verified
  only against the real `hermes profile --help`/`hermes gateway --help`
  output and code review.

- refactor: Second Data Access Layer architecture pass — split the
  Obsidian-vault side of `data_access/` into three real layers
  (operator: "vault is our Obsidian Mapping... Then we have Second
  Brain Vault, this one Understand Templates, Structure... Then Core
  can Talk to Second Brain Vault ask for Section it returns Section as
  a JSON"). New `app/obsidian/` — pure Obsidian-format primitives
  (frontmatter, tags, `## ` section read/write + write-permission
  rules, whole-vault/folder listing, the generic 4-file OKF directory
  pattern, attachments). Zero `app.config` import, matching
  `app/hermes/`'s own "config injected, never imported" convention —
  every function takes an explicit `path` or `vault_path`. New
  `app/vault/` — `vault_manager.py` relocated unchanged (still stdlib-
  only, still physically copy-deployed into 8 Hermes skill folders) plus
  a new `VaultClient`: constructed with a Template (fetched by the
  Template Manager) and the vault root, exposes `create_structure`/
  `write_file`/`write_section`/`update_property`/`find`/
  `get_last_modified_files`, then disposed — short-lived and scoped to
  one job, unlike `app/business/hermes/client.py`'s persistent
  singleton, since a different Template is a genuinely different job.
  New `app/data_access/templates/` — the real Template Manager
  (`get_template`/`list_templates`), fixing a real ADR-003 layering
  violation where `business/vault_templates.py` was reading
  `Template.json` files directly instead of going through data_access.
  `data_access/vault_writer.py` now holds only the ~150 Customer/
  Project/Person/Meeting/Thread/Partner/Task functions that have no
  real Template.json yet (operator: Threads specifically, "we kept it
  because it's used in the Threads pipeline as we didn't create a
  template for it yet") — every extracted primitive it used internally
  is now imported from `app.obsidian` instead of duplicated, and every
  external caller across `app/business/` keeps working unchanged via
  re-exports under the original names. Found and fixed a real bug along
  the way, the hard way (would have been invisible until the first
  actual call): `_slugify` had no replacement definition after
  extraction — 24 call sites across the file would have crashed with a
  `NameError` on first use, caught only by writing a script to cross-
  check every real `vault_writer.<name>` usage across the whole
  codebase (AST-parsed module symbols vs. every real attribute access)
  rather than trusting `import app.main` succeeding, which only proves
  module-level code is valid, not that every function body's names
  still resolve. Verified live after a clean backend restart:
  `/vault-index/rebuild` (1,545 real notes, exercises
  `list_all_note_paths`), `/vault-search/status`, `/vault/overview`,
  `/sections`, and `/vault/templates` (the new Template Manager, real
  templates like `azure-kb-doc`/`compass-kb-doc`) all correct. Left
  deliberately deferred, not silently dropped: the ~600-line JSON-
  state-store tail of `vault_writer.py` (agent history, cockpit chat,
  schedules, etc. — its own per-concern-folder split) and migrating the
  ~150 legacy note-kind functions onto real Templates + `VaultClient`
  (needs a Template authored per kind first).
