# Architecture

Living description of Second Brain's system as it is today. Update this file as
the architecture evolves — it describes what IS, not what MIGHT BE.

**2026-08-20:** The pre-redesign description of this system is archived,
not deleted — see `Documentation-Archive-2026-08-20/Implementation/
Architecture/architecture.md`. This file is being rewritten from scratch
alongside the backend architecture redesign ([ADR-001](ADR.md), executing
the Hermes/LangGraph pivot).

**Current status: mid-redesign, skeleton only.** The block-by-block design
work is happening collaboratively (operator + assistant as Architect/
Business Analyst) and is tracked live in `Implementation/Plans/2026-08-20-
backend-architecture-redesign.md` — that document is the actual source of
truth for the emerging shape right now, not this file. This file will be
filled in once the design stabilizes past the "empty skeleton folders"
stage; until then, treat anything written here as provisional.

## What exists today (confirmed, not aspirational)

- **Data taxonomy** (operator-defined): System Data (Second Brain's own
  operational state), Hermes/LangGraph Data (their own execution data, not
  ours to own), Vault Data (the real Obsidian vault — OKF directories/
  notes with frontmatter).
- **Data Access layer:** `app/data_access/vault/`, `app/data_access/
  system/` (with `app/data_access/system/provider/` inside it) — empty
  skeleton folders, nothing migrated in yet.
- **Business layer:** `app/business/logic/`, `app/business/vault/`,
  `app/business/core/`, `app/business/hermes/`, `app/business/langgraph/`
  — empty skeleton folders, nothing migrated in yet.
- **API layer:** confirmed to need no restructuring — stays a flat folder
  of single-purpose router files, same as before this redesign.
- The pre-redesign backend is still fully running in production
  (unaffected by the skeleton above) and is fully preserved at
  `Backend-Backup/backend-2026-08-20/` as the migration source.

See the Plans doc for open questions (the approval/safety gate, the
capture trigger's home, `core`'s exact definition, the MCP boundary's
placement) and the Provider schema still being settled.

---

## Cockpit Mechanics (REQ-SB-82)

The Meeting/Inbox Cockpit (`src/frontend/src/features/cockpit/Cockpit.tsx`,
`src/backend/app/api/cockpit_router.py`) is real, shipped UI (REQ-SB-43/44)
whose Chat tab, Research surface, and Moderator roster-assembly were
deliberately left as honest empty stubs post-Hermes-pivot (`business/
cockpit/{threads,research,person_note_proposals,attachments}.py` are
confirmed stale — see `MEMORY.md`, 2026-08-25). `REQ-SB-82` fills these in
as four separable mechanisms, each documented below. `people.py`/`notes.py`
under `app/business/cockpit/` are the only pre-existing modules reused
as-is; everything below is new.

### §Cockpit Persisted Chat (`REQ-SB-82-US-01`, `ADR-007`)

- **New store:** `.second-brain/cockpit_chat.json` — ONE file, top-level
  dict keyed by `"{subject_kind}:{subject_note_stem}"`, mirroring the
  pre-pivot `cockpit_threads.json` naming convention but a genuinely new
  module (never re-imports the stale `business/cockpit/threads.py`/its
  `ADR-036` design, which composed the now-nonexistent
  `run_agent_conversation`). Same load/save-whole-file pattern as every
  other single-key JSON state store in this app (`vault_writer.
  load_agent_visuals_state`/`save_agent_visuals_state` is the direct
  precedent to mirror, new sibling functions in the same file).
- **Per-subject entry shape:** `{"brought_in_agent_ids": [str, ...],
  "messages": [{"speaker": "user"|"agent", "agent_id": str|null,
  "agent_name": str|null, "text": str}, ...]}` — exactly
  `cockpitApiClient.ts`'s existing `CockpitThread` TS contract, no
  redesign. `US-03` (below) additively extends this same entry with a
  `recommended_agent_ids` field — do not fork a second store.
- **New business module:** `app/business/cockpit/chat_store.py` —
  `get_thread(subject_kind, subject_note_stem)`, `bring_in_agent(...)`,
  `remove_agent(...)`. Never composes a Hermes call itself — pure
  roster/message storage, no send/receive (that's `REQ-SB-82-US-04`).
- **Router:** `cockpit_router.py`'s existing `GET
  /cockpit/{subject_kind}/{subject_note_stem}` returns the real, persisted
  `thread` instead of the hardcoded empty stub; new `POST .../roster` and
  `DELETE .../roster/{agent_id}` mutate it.
- **Frontend:** `Cockpit.tsx`'s `broughtInIds` moves from local `useState`
  to state loaded from/written to the endpoints above — the existing "In
  this chat"/"Bring in another Expert" markup and `ChatMessageText`
  rendering are reused unchanged.
- Scoping is always per `(subject_kind, subject_note_stem)` — never merged
  across subjects.

### §Research Agent & Librarian Vault-Write Skill (`REQ-SB-82-US-02`, `ADR-008`)

- **New Hermes profile:** `research-agent`, under the existing Librarian
  Section (`app/business/hermes/agents_map_adapter.py`'s `_AGENT_TYPE`/
  `_AGENT_SECTION` dicts, same registration pattern as `notes-manager`/
  `files-manager`). No MCP server, no Second Brain backend process
  involvement at runtime (`ADR-002`'s precedent).
- **Research mechanism:** Hermes' own bundled `web_search`/`terminal`
  tools — the same real capability already powering `azure-expert`/
  `compass-expert`. No new lookup Skill.
- **Write mechanism:** new `research-kb-writer` Skill, script
  `write_research_doc.py`, mirroring `azure-kb-writer`'s own
  `write_azure_doc.py` CLI contract (`--vault-path`/`--input-file`,
  frontmatter + `## Summary`/`## Details`, optional images) with ONE
  deliberate divergence: every call creates a NEW note (title collision
  gets a suffix, never an overwrite) — `azure-kb-writer`'s own
  update-in-place default is explicitly NOT mirrored here, since
  `REQ-SB-82-US-02`'s own Constraints rule out merge/dedup logic for v1.
- **Destination:** `Work/Research/<slug>.md` — flat (no category split,
  unlike Azure's `Services/<Category>/`), a brand-new top-level vault
  area, this agent's ONLY write target.
- **No approval gate** — the write proceeds immediately once research is
  done; safe by construction because the write is structurally confined
  to `Work/Research/` and can never touch existing content.
- **Does NOT route through `REQ-SB-63`'s Vault Filing Expert** —
  `vault_filing_expert.py`'s only real callers are themselves
  pre-Hermes-pivot orchestration code `main.py` no longer wires in; there
  is no live mechanism to route through today, so this is a structural
  non-routing, not an active deviation from a working alternative.
- Callable identically from a scheduled job or a live Cockpit Chat request
  (Scenario 4) — the agent itself carries no caller-specific behavior.

### §Meeting Moderator Roster Recommendation (`REQ-SB-82-US-03`, `ADR-009`)

- **New business module:** `app/business/cockpit/moderator.py` —
  `match_customer_expert(subject_note_stem)` (meeting's own `customer`
  tag/folder → a real, already-registered `<customer>-expert` agent id,
  per `REQ-SB-83`'s real Masdar/Adnoc/TAQA agents; `None` if no match —
  never fabricated) and `match_domain_experts(subject_note_stem)`
  (lightweight keyword overlap between the meeting's own tags/subject and
  every real `type: "expert"` agent's already-exposed `GET /agents`
  `name`/`description` fields — no new per-agent schema field).
- **Trigger point: compute-on-read, then cache.** The FIRST real `GET
  /cockpit/{subject_kind}/{subject_note_stem}` call for a subject with no
  `recommended_agent_ids` entry yet computes both tracks and persists the
  result into that subject's own entry in `.second-brain/cockpit_chat.json`
  (§Cockpit Persisted Chat, above) — every subsequent read serves the
  cached value. No new Hermes profile, cron job, or scheduled backend task
  is needed: both match tracks are purely deterministic/mechanical
  (frontmatter lookup + keyword overlap), not an LLM judgment call, so
  they run entirely inside Second Brain's own backend, synchronously.
- **Persisted schema (additive):** the SAME per-subject entry `US-01`
  built gains one new field, `recommended_agent_ids: list[str]` — a
  non-authoritative hint list, separate from `brought_in_agent_ids`.
  Bringing a recommended agent into the chat uses the SAME `bring_in_agent`
  mechanism as any manual bring-in (Scenario 6 — recommendation never
  restricts manual choice).
- **Frontend:** a NEW "Recommended" grouping in `Cockpit.tsx`'s Chat tab
  right rail, above "In this chat"/"Bring in another Expert" — the
  already-approved (same-day live-whiteboarded, operator-confirmed)
  visual shape: a "Recommended" section header, the matched agent(s) with
  an Add action, plain Experts list below. An agent already brought in
  renders in "In this chat" only, never duplicated into "Recommended."

### §Meeting Preparation Agent (`REQ-SB-82-US-05`, `ADR-010`)

- **New Hermes profile:** `meeting-prep-agent`, with its OWN new cron job
  — `schedule: {"kind": "interval", "minutes": 720}` (twice daily),
  `deliver: "whatsapp"`, mirroring the real, live `new-company-discovery`
  cron's own shape (`cron/jobs.json`, confirmed directly) and its "silent
  unless real findings — never a no-op notification" prompt convention.
- **KB-lookup delegation:** relays to `research-agent` (§Research Agent,
  above) via the same one-shot cross-profile relay every multi-profile
  chain in this codebase already uses (`hermes -p research-agent chat -q
  "..."`) — no live back-channel, so the Prep Agent must fully specify its
  research ask in one shot (`MEMORY.md`'s documented relay constraint).
- **Person-note web lookup:** a new Skill (own script, mirrors `notes.
  add_person_note`'s established append-only-to-an-existing-note shape) —
  runs a real web lookup ONLY when an attendee's Person note body (past
  frontmatter) is empty, appends real findings once found, and never
  re-runs once the note has any real body content (from this agent OR the
  user) — the one-time-per-person gate is a plain body-emptiness check,
  not a separate tracking field.
- **Suppression persistence: Hermes' own native per-profile `memories/
  USER.md` file** — real, general, already populated on every existing
  profile (confirmed on `azure-expert`'s own file) — NOT `vault_writer.
  append_agent_memory_entries` (confirmed zero live callers, PRD citation
  is stale). The agent writes/reads its own learned suppression
  preference in plain language via its own memory tool, keyed by the
  meeting's own `calendar_series_id` (falling back to its `customer` tag)
  — no new Second-Brain-side schema or store.
- Second Brain's backend has no visibility into or query access over
  what's currently suppressed — it lives entirely inside Hermes' own
  per-profile memory file, outside this repo.

### §Cockpit Live Routing & Reply-to-Message (`REQ-SB-82-US-06`, `ADR-011`, `ADR-012`)

- **New data-access module:** `app/data_access/compass_client.py` — raw
  HTTP client for Compass `gpt-oss-120b`, sourced from `app.config.
  settings` (`compass_base_url`/`compass_api_key`/`compass_model`), using
  `httpx` (same proven pattern as `app/hermes/rest.py`). This is the
  first direct-to-LLM client in the post-2026-08-20 architecture. Raises
  a dedicated error type on any failure (network error, timeout,
  non-success response) — never a silent `None`. **`ADR-022`**, cited as
  "Accepted" by several pre-existing code comments/task files
  (`provider_manager.py`, `REQ-SB-36-US-01-T01`/`T02`), is confirmed
  **orphaned** — no such entry exists anywhere in this ledger (the real
  highest entry was `ADR-010` before this pass); it belongs to the
  archived pre-2026-08-20 ADR sequence and governed code
  (`compass_client.py`/`anthropic_client.py`) since deleted in the
  2026-08-27 "fully agentic" purge. Treat any reference to it as
  pre-redesign history, not a live decision — cite `ADR-011` going
  forward.
- **LLM-based moderator:** a new function in the existing `app/business/
  cockpit/moderator.py` (sibling to `route_question`/
  `match_domain_experts`), composing `compass_client` to reason over the
  brought-in roster's own `name`/`description`, recent conversation
  history, and the new message's own text. Runs on EVERY message not
  caught by the short-reply shortcut below (operator's "always on"
  choice) — the PRIMARY routing decision. The existing deterministic
  `route_question` is retained unmodified and demoted to the explicit
  degrade path on any Compass client failure, mirroring
  `_reply_via_agent`'s already-proven Hermes-failure degrade shape.
- **Short-reply shortcut:** a pre-routing check in
  `chat_turn.py::send_user_message`, checked before any moderator call
  (deterministic or LLM) — no full routing decision needed to reach it.
  Depends on a new additive field on `ADR-007`'s own per-subject
  `chat_store.py` entry — `last_answering_agent_id`/
  `last_answering_agent_name` (same honest-empty-until-set convention as
  `ADR-009`'s `recommended_agent_ids`) — set by `_dispatch_reply`
  whenever any real agent reply is dispatched. No prior answer recorded
  → the shortcut cannot fire, the message falls through to normal
  routing. The exact detection rule (length threshold vs. fixed
  vocabulary vs. both) is left to the decomposer/coder.
- **Reply-to-message, Cockpit:** the outgoing `POST /cockpit/
  {subject_kind}/{subject_note_stem}/message` endpoint gains an optional
  caller-supplied `reply_to_message_id` (additive to the field
  `chat_store.append_message` already accepts internally for
  auto-threaded replies). When present, `chat_turn.py` resolves the
  referenced message's own text and feeds it into the LLM moderator's
  reasoning as one more context input — never a hard override; the
  moderator can still route elsewhere when the new message's content
  clearly belongs to a different Expert. A stale/unresolvable reference
  is treated as absent — the message still sends and routes normally,
  no error rendered.
- **Reply-to-message, single-agent Chat panel:** architecturally separate
  from the above — `AgentChatPanel.tsx` has zero message-id/persistence
  concept today (a stateless streaming call, no `chat_store` backing). A
  lighter-weight, purely client-side context-anchoring mechanism (attach
  the referenced message's own text to the outgoing request) is the
  intended shape — no backend schema change, no LLM-moderator
  involvement, since only one agent ever answers there.
- **Visual/UI treatment in both surfaces is `net-new-design-needed`** (no
  `html-prototype/` coverage) — deferred to a `/design` pass before
  frontend tasks are cut; this architecture note covers only the
  backend/API-contract shape.

## Artifact Export/Import — Portable Capability Bundles (`REQ-SB-85`)

Second Brain's own Data Layer (`REQ-SB-80`, built directly per `BACKLOG.md`'s
own row, real and `Done`) already exposes four entity Managers, each the sole
real gateway onto its own store (the same "one real gateway per entity" rule
`SectionManager`/`AgentManager` already established): `SkillManager`
(`business/core/skills/skill_manager.py`, content in
`Hermes-Provisioning/skills/<category>/<slug>/`, metadata in the Registry's
`Tools/<tool>/Skills/<slug>/Skill.json`), `TemplateManager`
(`business/core/templates/template_manager.py`, `.second-brain/data/
Templates/<id>/Template.json`, vault-only), `AgentManager`
(`business/core/agents/agent_manager.py`, composes a real Hermes profile +
the Registry's own `Agent.json`/`soul.md` mirror — two genuinely separate
stores), and `PipelineManager` (`business/core/pipelines/pipeline_manager.py`,
`<second_brain_data_path>/pipelines/<id>.json`, cron-linked). `REQ-SB-85`
builds a new, portable-bundle export/import surface entirely on TOP of these
four — it never becomes a 5th "Manager" (it owns no entity/store of its own),
and it does not change any of the four Managers' own read-side contracts
except the two narrow write-path additions `ADR-015` records below.

### §Artifact Inventory Composition (`REQ-SB-85-US-01`)

- **New:** `app/business/logic/artifacts_inventory.py` — a single
  `list_all_artifacts()` composing `SkillManager().get_all()`/
  `TemplateManager().get_all()`/`AgentManager().get_all()`/
  `PipelineManager().get_all()` into one tagged (`kind`, `id`, `name`,
  `description`) list. Pure read composition — matches the existing
  `business/logic/` pattern already used for cross-entity, no-owned-store
  work (`section_agents.py`, `cockpit_view.py`, `system_health.py`), not a
  new structural layer.
- **New:** `app/api/artifacts_router.py` — `GET /artifacts`, the same flat
  single-purpose-router convention every other entity uses (`skills_router.py`,
  `pipelines_router.py`, `sections_router.py`).
- **Frontend:** `SettingsArtifactsPage.tsx` (new) reuses the already-approved
  `.item-list`/`.item-row` family (`SettingsVaultTemplatesPage.tsx`/
  `SettingsSectionsPage.tsx`) for per-artifact rows and the existing
  `.card.settings-card` grid for its own Settings-landing-page entry point.
  The cross-type multi-select is client-side-only ephemeral React state —
  never persisted, never round-tripped to the backend until an Export/Import
  action is actually taken.
- No new ADR — this section composes only already-Accepted Manager
  gateways, adds no store, and follows an already-established composition
  pattern.

### §Dependency Closure, Secret Scan & `.sbf` Archive Format (`REQ-SB-85-US-02`, `ADR-013`)

- **New:** `app/business/logic/artifact_dependency_resolver.py` — given an
  initial `(kind, id)` selection, resolves and returns the full closure with
  a human-readable reason per included artifact:
  - **Skill → its own shared-file copies:** already physically present in
    that Skill's own `scripts/` folder (`data_access/skills.py::
    list_scripts()`) — the resolver's job here is disclosure ("this file is
    a copy of the shared `vault_manager.py`"), not traversal to a separate
    artifact, since the bytes already travel with the Skill's own payload.
  - **Agent → Registry `skill_ids`/`depends_on`:** recurses transitively
    into every Agent id named in either real field on the `Agent` dataclass.
  - **Skill → implicit Template.json coupling:** a static text scan of the
    Skill's own script content for any real `TemplateManager().get_all()`
    id appearing as a literal string — a disclosed heuristic (no structured
    field exists anywhere today, confirmed by direct reading of the `Skill`
    dataclass), not a guaranteed-complete detector; see Consequences.
  - **Pipeline → step Agents:** each real Agent id named in `steps[]`,
    recursed the same way as a direct Agent selection.
  Every resolved artifact is shown to the operator (the dependency-preview
  screen) BEFORE any archive byte is written — never a silent auto-include.
- **New:** `app/business/logic/artifact_secret_scan.py` — scans ONLY
  Second-Brain-owned new bytes in the resolved closure (Skill SKILL.md/
  scripts content, Template.json content, seed/blank data file content).
  **Never re-scans or touches the nested Hermes profile sub-archive** — that
  piece arrives already silently redacted by Hermes' own `export_profile`
  (`ADR-014`); this system's own explicit, per-finding promise governs only
  the surface it owns. Sits as a hard gate between "closure resolved" and
  "archive written" — the archive writer never runs while any finding is
  undecided. Three finding-level actions (Redact / Keep as-is / Cancel
  export — the story's own disclosed, non-locked judgement call) are applied
  in-memory before the affected file is written into the archive.
- **New:** `app/business/logic/sbf_archive.py` — writer (`US-02`) and
  reader (`US-03`) share this one module/shape. `.sbf` is a real **zip**
  file:
  - `manifest.json` — `format_version`, `generated_at`, `artifacts: [{kind,
    id, included_reason: "selected"|"dependency", depends_via}]`,
    `secret_scan: {findings_decided, redacted_count}`.
  - `skills/<slug>/SKILL.md`, `skills/<slug>/scripts/**` — mirrors
    `Hermes-Provisioning/skills/<category>/<slug>/` (category lives in the
    manifest entry, not the payload path).
  - `templates/<id>/Template.json` — mirrors `data/Templates/<id>/
    Template.json` exactly.
  - `pipelines/<id>.json` — mirrors `pipelines/<id>.json` exactly.
  - `agents/<agent_id>/profile.tar.gz` — the RAW, unmodified output of
    `HermesCLI.export_profile` (`ADR-014`) — never unpacked/repacked.
  - `agents/<agent_id>/Agent.json`, `agents/<agent_id>/soul.md` — the
    Registry-side mirror, same shape `registry_writer.write_agent_files`
    already produces.
  - `seed_data/<real-target-relative-path>` — e.g. `seed_data/Settings/
    Entities.md`, content genuinely empty (the hard capability/data
    boundary — Scenarios 4/5), path mirrors the real target location so
    import writes it back verbatim.
- **API:** `POST /artifacts/export` (writer), `POST /artifacts/import`
  (reader, `US-03`) on the same `artifacts_router.py` `US-01` added.
- **Frontend:** dependency-preview + secret-scan confirmation screens
  (`net-new-design-needed`, functional-first per the operator's own
  same-day override — see story frontmatter), wired from the Export action
  on `SettingsArtifactsPage.tsx`.

### §Hermes Profile Export/Import Reuse (`REQ-SB-85-US-02`/`US-03`, `ADR-014`)

- `app/hermes/cli.py::HermesCLI` gains `export_profile(name, output_path)` /
  `import_profile(archive_path, name=None)` — the exact same `_run()`
  subprocess-capture pattern as the class's existing `create_profile`/
  `delete_profile`/`describe_profile`, wrapping Hermes' own real, already-
  shipped, non-interactive `hermes profile export <name> [output]` /
  `hermes profile import <archive> [--name <name>]` CLI subcommands
  (confirmed live against the installed source, `hermes_cli/profiles.py`).
- This is the ONLY mechanism by which an Agent artifact's Hermes-profile
  piece is produced/consumed — the resulting bytes are opaque to Second
  Brain (never parsed, never re-scanned; Hermes' own `export_profile`
  already force-redacts every text-ish staged file before writing its own
  `tar.gz`).
- `import_profile`'s own real `--name` override (lands the imported profile
  under an alternate id) and its own real `FileExistsError`-on-collision are
  the exact primitives `US-03`'s "keep both" and per-artifact conflict
  detection are built on for the Agent kind — no separate conflict-detection
  logic is invented for this piece.
- Resolves, for this one surface only, `ADR-003`'s own explicitly-deferred
  "backend needs real write access into Hermes... its own future decision"
  question — does NOT reopen `ADR-003`'s broader still-deferred "backend
  creates Agents/Pipelines/Cron Jobs in Hermes from scratch" direction.

### §Template/Pipeline Write-Path Additions & Import Orchestration (`REQ-SB-85-US-03`, `ADR-015`)

- `data_access/templates.py` gains `write_template_json(template_id, data)`
  (same-shape sibling to the existing `read_template_json`, raw I/O only);
  `TemplateManager` gains a real create/import method that calls it — still
  the sole gateway onto Template data.
- `data_access/pipelines.py` gains `write_pipeline_json(pipeline_id, data)`;
  `PipelineManager` gains the matching create/import method. Same shape,
  same narrow scope.
- Both new writers exist ONLY to support import provisioning — no general
  Templates/Pipelines authoring UI is built here (see `ADR-015`).
- **New:** `app/business/logic/artifact_import.py` — reads a `.sbf` via
  `sbf_archive.py` (`ADR-013`), runs per-artifact conflict detection against
  the target machine's own real current state (across all 4 kinds), then
  deploys each per its resolved decision:
  - **Skill:** `SkillManager.deploy(skill_id, profile_id)` — already real;
    this story's own new work is target-profile selection + conflict
    wiring, not the deploy mechanism itself.
  - **Agent:** `HermesCLI.import_profile` (`ADR-014`) for the profile piece,
    `registry_writer.write_agent_files` for the Registry piece; "overwrite"
    = `AgentManager.delete()` then a fresh import (mirrors `AgentManager.
    update()`'s own delete-then-recreate shape for a relocated agent).
  - **Template/Pipeline:** the new writers above.
  - **Seed/blank data files:** written verbatim from the archive's own
    `seed_data/` payload (already guaranteed empty at export time).
  Every artifact's own deployment outcome (succeeded/failed) is reported
  independently — a mid-import failure on one artifact never silently
  drops or falsely-reports another (Scenario 9).
- **API:** `POST /artifacts/import` (see `US-02`'s section above).
- **Frontend:** upload/contents-preview + per-artifact conflict-resolution
  screens (`net-new-design-needed`, functional-first — see story
  frontmatter), wired from the Import action on `SettingsArtifactsPage.tsx`.

## Vault Data Export — Real Slice of the Vault (`REQ-SB-86`)

Deliberately separate from `REQ-SB-85`'s Artifact Export/Import subsystem
above (see that section's own §Artifact Inventory Composition intro for
the capability/data split) — `REQ-SB-86` moves real, already-trusted
operator vault DATA (a Customer's own notes, an Industry KB), never a
capability. `VaultManager` (`app/business/core/vault/vault_manager.py`)
stays the sole gateway for every real vault-data read this subsystem
needs; neither substory adds a second door onto vault content.

### §Export Data Folder-Tree Picker (`REQ-SB-86-US-01`)

- **New:** one real, unfiltered directory-tree-listing method on
  `VaultManager` (folders + files, includes OKF-reserved files and
  `_`-prefixed folders that `app/obsidian/notes.py::list_all_note_paths()`
  deliberately excludes from the ordinary note index) — a genuine
  filesystem walk of `settings.vault_path`, never the note-index
  primitives. Read-only; no new store, no new Manager.
- **API:** a new `GET` route on the existing `app/api/vault_router.py`,
  same flat single-purpose-router convention every other Vault Settings
  page already uses.
- **Frontend:** `SettingsVaultExportDataPage.tsx` (new) — folder-tree
  browse, multi-select (folder selection includes every nested file), `.md`
  quick filter; a new `VAULT_NAV_ITEMS` entry on the existing
  `VaultSettingsNav.tsx`. Selection state is ephemeral, client-side only —
  never persisted, handed directly to the Export flow below.
- **No new ADR** — this is a pure read-only listing addition to the
  already-Accepted `VaultManager` gateway, following that Manager's own
  already-established shape (`get_index_config()`/`list_templates()`/
  `list_entities()` are the direct precedent for "one more dict/list-
  returning read method"). Confirmed directly against `vault_manager.py`'s
  own real code before deciding, not assumed.

### §Embedded-Attachment Resolution & `.sbd` Archive Writer (`REQ-SB-86-US-02`, `ADR-016`)

- **New `business/logic/` modules** (no new Manager — mirrors `ADR-013`'s
  own placement convention): `vault_attachment_resolver.py` (scans a
  selected `.md` file's real body, via `app/obsidian/frontmatter.py::
  read_note()`, for a genuinely-embedded, on-disk attachment — wikilink-
  embed `![[...]]` and markdown-image-link `![...](...)` syntax, both
  scanned) and `sbd_archive.py` (writer only — no reader, no import round-
  trip exists to design for).
- **`.sbd` format** — a real zip, **no `manifest.json`** (unlike `.sbf`):
  every selected file plus every resolved attachment lands at its real
  archive-member path, computed per the operator's flat/hierarchy choice.
  A flat-extraction filename collision is disambiguated by prefixing the
  archive member name with its own original parent-folder name (e.g.
  `masdar_index.md`, `acme_index.md`) — never a silent overwrite.
- **Deliberately no dependency-closure resolution and no secret-scan gate**
  — the exact mirror-image posture to `ADR-013`'s `.sbf` pipeline: real,
  already-trusted vault data the operator is explicitly, purposefully
  choosing to share has neither a dependency-closure concept nor a
  credential-scan need the way a capability bundle does.
- **API:** `POST /vault/export-data/export` on the existing
  `app/api/vault_router.py`.
- **Frontend:** a new export-options screen (flat/hierarchy choice,
  confirm, download), wired from the Export action on
  `SettingsVaultExportDataPage.tsx`.
- **ADR-016** records this section's own module placement, the no-manifest
  decision, the attachment-detection heuristic, the flat-collision naming
  rule, and the explicit divergence from `ADR-013`'s machinery — see
  `ADR.md` for the full Context/Decision/Alternatives/Consequences.

## Email Thread Capture — a New, LLM-Driven Pipeline (`REQ-SB-87`)

Consolidates the one remaining real capture pipeline still writing by hand
(`email-thread-capture`) onto the shared `vault_manager.py` template engine
`meeting-capture`/`create-companies-partners` already proved (2026-08-25→27),
and layers genuinely new capability on top: Capture-time noise-skip +
Internal/Partner/Customer classification, and Enrich-stage pending-action
extraction. Five stories: `US-01` (engine resync + templates, this section's
own primary scope), `US-02` (`email-thread-capture` mechanics migration),
`US-03` (Capture-time classification/skip), `US-04`
(`summarize-and-tag-threads` mechanics migration), `US-05` (pending-action
extraction).

### §Canonical `vault_manager.py` Source & Deployment (`REQ-SB-87-US-01`)

- **The canonical source already exists and was already the right place to
  edit — confirmed, not invented this pass:** `Hermes-Provisioning/shared/
  vault_manager.py` (module docstring, 2026-08-25: "Editing the engine
  happens in exactly ONE place (this file, then re-copy)"). Direct diff
  confirms it already carries every function `create-companies-partners`'s
  own deployed copy has; the real drift is `meeting-capture`'s own deployed
  copy alone, which lags behind it. Real, full deployment inventory: nine
  copies today (`azure-kb-writer`, `compass-kb-writer`, `research-kb-writer`,
  `capture-files`, `capture-notes`, `vault-index`, `track-opportunities`,
  `create-companies-partners`, `meeting-capture`), all re-synced to
  byte-match the canonical source by this story; two brand-new copies
  deployed for the first time by the sibling stories
  (`email-thread-capture`, `US-02`; `summarize-and-tag-threads`, `US-04`).
- No new ADR governs the resync itself — it enforces an already-Accepted
  convention. `ADR-017` (below) governs the real engine CAPABILITY changes
  this story also needs.

### §`vault_manager.py` Engine Extensions — Dynamic Children & Per-Caller Access (`REQ-SB-87-US-01`, `ADR-017`)

- **Dynamic (unbounded) children:** `Template.json`'s existing `root.
  children` array gains a per-entry `"growth": "fixed" | "dynamic"` field
  (default `"fixed"`, every existing template unchanged). A `"dynamic"`
  entry declares its own subfolder, its own `frontmatter_defaults`/
  `sections`, and its own natural-key identity for idempotent lookup — the
  real shape Thread's `messages/` folder needs (one new RawMessage note per
  captured email, unbounded, over the Thread's whole lifetime), genuinely
  distinct from the existing FIXED-sibling `children` shape (Customer/
  Partner's `log`/`captures`, created once, atomically, at root-creation
  time). The engine's own module docstring already named this exact case
  as a planned, not-yet-built extension before this requirement existed.
- **Per-caller section-write access:** a section's `access` declaration
  gains an optional `allowed_callers: [str, ...]` list; `create`/
  `modify-section` require a caller-identity argument on every call and
  refuse a write not on that list — the same guarantee `vault_lib.py`'s own
  `_CALLER_ALLOW_LISTS` already provided, now Template.json data instead
  of hardcoded Python. No `allowed_callers` key = open to any
  `machine_write` caller (zero behavior change for every already-`Done`
  template). Every mutating caller in every already-migrated Skill
  (`meeting-capture`, `create-companies-partners`), not just the new ones,
  must pass this new caller-identity argument going forward.
- **Thread template's own section-access shape:** `## Related` →
  `link_person_to_thread` only; `## Files` → `capture_attachments`/
  `capture_file_link` only; `## Summary` and `## Actions` → both
  `apply_thread_review` only (one caller, two sections); `## Personal
  Notes` → `human_only`, no exception.
- **`## Actions` write mode is `replace`, mirroring `## Summary` exactly**
  (resolves `US-05`'s own flagged Constraint) — not append, not a
  coexist-with-human-content design; `## Actions` carries no real content
  of either kind today, and a resolved pending action must actually
  disappear on re-summarization, which append-only could never represent.
- The exact `## Actions` entry PROSE shape (plain bullet vs. an agent
  voluntarily wikilinking a Person) is left open, deliberately — no new
  engine capability is needed either way; a dedicated `Work/Tasks/`
  integration is already ruled out by `US-05`'s own Non-Goals. Decomposer/
  coder-level prompt design.
- See `ADR-017` for full Context/Alternatives/Consequences.

### §Capture-Time Classification & Noise-Skip (`REQ-SB-87-US-03`, `ADR-018`)

- **Capture's own recurring loop (`run_delta_capture.py`/
  `run_full_capture.py`) stays the existing deterministic, single-process,
  subprocess-orchestrated design** — confirmed directly, zero LLM/agent
  call anywhere in today's real per-email loop, deliberately engineered
  this way (O(1), not O(N), LLM round trips per tick). It is NOT
  restructured into a `job4-summarize-tag-threads`-style live, multi-turn,
  resumable agent session — that shape solves a different problem (a
  one-time, 209-Thread backlog too large for one session's context), not a
  short, unattended, ~30-minute-cadence recurring tick.
  - **The classify-or-skip judgment is ONE bounded, one-shot `hermes -p
    <profile> chat -q "..."` relay subprocess call per newly-first-seen
    `conversation_id` only** (never per message), inserted into
    `ingest_email.py`'s own `if existing_directory is None:` branch,
    BEFORE any Thread/RawMessage note is written — the same already-proven
    cross-profile relay mechanism this codebase uses everywhere else, and
    the same `subprocess.run()`-style dispatch `run_delta_capture.py`
    already uses for every other per-email step.
  - **A new, dedicated, lightweight Hermes profile** is the relay's
    anticipated target (exact identity/prompt design decomposer/
    coder-level), returning one structured JSON verdict (`is_noise`,
    `classification`, reasoning) — the agent decides, the script only
    applies, same division of labor as `apply_thread_review.py`.
  - **The noise-definition artifact is a real, structured, persisted file
    under the vault's own `.second-brain/data/` tree** (a new sibling to
    `Templates/`), never a Skill-`scripts/`-folder file, never baked into
    the profile's own static prompt — every script already receives
    `--vault-path`, so it reads with zero deploy step, mirroring
    `Template.json`'s own already-established convention.
  - **Derivation of the noise definition is a separate, out-of-band act**
    (on-demand, e.g. during the 100-email scratch-sample proving phase),
    decoupled from the recurring tick — the per-tick path always reads an
    already-persisted artifact, never invents one fresh.
- See `ADR-018` for full Context/Alternatives/Consequences, including the
  disclosed reliability trade-off (added per-tick live-dependency surface,
  given this same pipeline's own real, same-day gateway-down incident).

### §Enrich-Stage Mechanics Migration & Pending-Action Extraction (`REQ-SB-87-US-04`/`US-05`)

- `apply_thread_review.py` migrates its own hand-rolled `read_note`/
  `merge_tags`/`upsert_frontmatter_key`/`replace_body_section`/
  `_HUMAN_OWNED_HEADERS` primitives onto the resynced `vault_manager.py`
  (a brand-new copy deployed to `summarize-and-tag-threads/scripts/`,
  `US-04`) — no change to its own real judgment (company resolution,
  the never-tag-Person-notes rule, log-entry re-sort).
- Pending-action extraction (`US-05`) is agent-prompt judgment over a
  Thread's own already-read messages, applied through the SAME migrated
  `apply_thread_review.py` → `vault_manager.py` call path `US-04` builds —
  no second, bespoke writer. Depends on `US-04` (the migrated call path)
  and `US-01` (the widened `## Actions` access + replace-mode decision,
  `ADR-017`) — both real, confirmed dependencies, not assumed.

**Last reviewed:** 2026-09-01 (architect pass, `REQ-SB-87-US-01`/`US-03`/
`US-05` — `ADR-017`/`ADR-018`, the Email Thread Capture pipeline
consolidation + new Capture/Enrich capability; `REQ-SB-86-US-01`/`US-02` —
`ADR-016`, the Vault Data Export subsystem; `REQ-SB-85-US-01`/`US-02`/
`US-03` — `ADR-013`/`ADR-014`/`ADR-015`, the Artifact Export/Import
subsystem, reviewed 2026-08-31).
