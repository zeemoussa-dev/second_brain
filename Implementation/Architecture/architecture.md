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

> **Structure changed on 2026-09-06 (`ADR-019`).** Skills, the shared
> `vault_manager`, and the Entity ("Master") Templates are now backend-owned and
> ship with the product; `Hermes-Provisioning/` no longer exists;
> `allowed_callers` has moved off Template.json onto the Skills, via a derived
> `section_access.json`. The per-requirement sections below are **historical
> records of what each requirement established at the time** and are deliberately
> not rewritten — read `ADR-019` and `Documentation/Framework/Artifacts.md` for
> the current shape.

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
capture trigger's home, `core`'s exact definition) and the Provider schema
still being settled. The MCP boundary is no longer an open question: Second
Brain exposes nothing over MCP, and that layer was deleted on 2026-09-04.

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
`business/core/skills/catalog/<tool>/<slug>/`, metadata in the Registry's
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
    `business/core/skills/catalog/<tool>/<slug>/` (the grouping folder lives
    in the manifest entry, not the payload path).
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

## Close the Remaining `vault_manager.py` Migration Gaps (`REQ-SB-88`)

The last two real Skill scripts still writing by hand after `REQ-SB-87`'s own
pass: `summarize-and-tag-files/scripts/apply_file_review.py` (never had a
`vault_manager.py` copy at all) and `track-opportunities/scripts/
link_opportunity.py` (a real, deployed, byte-current copy sits unused right
next to it). Both confirmed, directly, purely additive/consumptive of
capability `ADR-017` already built (per-caller `allowed_callers` allow-list on
`modify_section`/`create`) — neither needs a new engine capability, so
**neither substory gets a new ADR.**

### §Files-Skill `vault_manager.py` Migration + Cron Provisioning (`REQ-SB-88-US-01`)

- **Tenth deployed copy, sourced from the canonical file.** `summarize-and-
  tag-files/scripts/` has never had a `vault_manager.py` copy (confirmed via
  `Glob` — only `apply_file_review.py`/`render_pptx_slide_win32.py` exist
  there today). Deploy fresh from `Hermes-Provisioning/shared/vault_manager.py`
  (`REQ-SB-87-US-01`'s own canonical source), joining the nine-copy inventory
  that section already tracks.
- **`apply_file_review()`'s `## Summary` write and `merge_tags` call migrate
  onto `vm.modify_section`/`vm.merge_tags`, exactly mirroring
  `REQ-SB-87-US-04`'s own already-proven shape** — `vm.load_template(vault_path,
  "file")`, read/mint the File's own `id` via `vm.update` (the File template's
  `identity.strategy` is `"id"`, same as Thread; a real pre-migration File
  note carries no `id` yet, same already-solved case), then `vm.modify_section
  (..., section="Summary", mode="replace", note_id=..., caller="apply_file_
  review")`. **Confirmed directly against the real, deployed `file` Template.json:**
  both `## Summary` and `## Details` are already `"access": "machine_write"`
  with **no `allowed_callers` key** — open to any machine-write caller today,
  zero Template.json edit needed for either.
- **`add_file_detail()`'s `## Details` append migrates the same way**
  (`vm.modify_section(..., section="Details", mode="append", ...)` — the
  engine's own `mode="append"` already does the existing-content-plus-new-
  content merge `add_file_detail()` currently hand-rolls). Image copy/embed
  (`_attach_images`/`_unique_sibling_path`) is plain filesystem work, unrelated
  to any note-write primitive — stays hand-written, unchanged.
- **`update_files_log_line()`'s Thread `## Files` write needs ONE
  Template.json data edit, not a new engine capability:** the real, deployed
  `thread` Template.json's `## Files` section currently declares
  `"allowed_callers": ["capture_attachments", "capture_file_link"]`
  (`ADR-017`) — `apply_file_review` is a new, third caller and must be ADDED
  to that same array for its migrated write to be accepted by `vm.
  modify_section`'s own `_require_machine_write` check. This is the exact,
  already-anticipated extension mechanism `ADR-017` built (`allowed_callers`
  is Template.json data, editing it is not an engine change) — ordinary
  Template.json maintenance, not an architecture decision, so no ADR.
  Company resolution (`build_company_index`/`resolve_companies`) stays
  hand-written, unchanged, per `REQ-SB-87-US-04`'s own identical precedent.
- **The new cron job is a Hermes `cron/jobs.json` entry under the
  `files-manager` profile, mirroring `job4-summarize-tag-threads`'s own real,
  confirmed shape** — read directly off the live `cron/jobs.json`:
  `schedule: {"kind": "interval", "minutes": 20}`, a **bounded** `repeat.times`
  budget (job4's own was `8`, against a 209-Thread backlog; this Skill's real
  backlog is ~80 Files, per SKILL.md's own documented scale), `enabled: false`/
  `state: "completed"` once the budget is exhausted — never an unbounded,
  indefinitely-recurring job. Confirmed live: `files-manager`'s own profile
  directory carries no `cron/` folder at all today, so this is a first-time
  provisioning, not an edit. This is Hermes-side operational configuration
  (a JSON job entry, same class as every other real job already in
  `cron/jobs.json`), not a Second-Brain architecture change — no ADR. The
  exact `repeat.times`/batch-size numbers are decomposer/coder-level, sized
  against the real ~80-file backlog.

### §`track-opportunities` Link-Write Migration (`REQ-SB-88-US-02`)

- **No new copy — the already-deployed `track-opportunities/scripts/
  vault_manager.py` is confirmed byte-current** (its own function/line
  layout matches the canonical `Hermes-Provisioning/shared/vault_manager.py`
  exactly, confirmed directly by reading both). `link_opportunity.py` simply
  never imports it yet.
- **Resolves the story's own disclosed open implementation-shape question:
  the already-public, template-driven `vm.modify_section` entry point is
  sufficient — no reach into underscore-private helpers (`_set_section_
  content`), and no new public primitive needs promoting.** The only reason
  this looked different from `REQ-SB-87-US-04`'s own precedent is that
  `link_opportunity.py` receives a bare `note_path` rather than a `title` to
  resolve — but `modify_section`'s `note_id`-based path (the SAME path
  `apply_thread_review.py` already uses) only ever needs the target's own
  `id`, which the script mints/reads via `vm.update` exactly like the
  Thread-migration precedent, plus which TEMPLATE to load (`"thread"` vs.
  `"meeting"`, trivially derivable from `note_path`'s own `Work/Threads/` vs.
  `Work/Meetings/` prefix — decomposer/coder-level). No engine change.
- **The frontmatter `opportunities` list write migrates onto `vm.read_note`
  (read existing list) + `vm.update(..., frontmatter={"opportunities":
  merged_list})`** — the same shape `apply_thread_review.py`'s own frontmatter
  stamping already uses.
- **The `## Related` write needs ONE Template.json data edit for the Thread
  case, not a new capability — and confirms the Constraint's own "never a
  silent widening" concern was real and must be resolved, not skipped:**
  confirmed directly against both real, deployed Template.json files —
  Thread's `## Related` already declares `"allowed_callers":
  ["link_person_to_thread"]` (`ADR-017`), so a migrated call with
  `caller="link_opportunity"` would be REFUSED outright unless
  `link_opportunity` is added to that same array (a real correctness
  requirement, not optional hardening — Scenario 2's own AC would fail
  against a Thread target without it). Meeting's `## Related` has **no**
  `allowed_callers` key at all (open to any machine-write caller today) —
  confirmed directly, zero edit needed for the Meeting case. Same ordinary
  Template.json maintenance as `US-01` above — no ADR.
- `resolve_opportunity()`/`_iter_opportunity_notes()` (title/customer
  matching, ambiguity handling) stay hand-written, unchanged — real,
  Opportunity-specific business logic, not mechanics, per the story's own
  Constraints.

## An Agent Acts From a Published Catalogue (`REQ-SB-95`)

`ADR-032` settles the shape: `Action` is the sixth artifact kind, `Workflow` the
seventh, both instance data in the App Database Folder, `Pipeline` untouched,
one implementation per Action resolved at save time, enforcement at the call.
`ADR-033` and `ADR-034` settle the three things it left open — which surface
"the call" lands on, how "who may run it" and "needs confirmation" are
represented end to end, and what actually happens when a Workflow matches.
`ADR-035` records the operator's two corrections (the resolver is framework and
generic; `self_email` lives in the Profile *and* Hermes' `.env`), and `ADR-036`
/`ADR-037` settle what those corrections left open — how the Profile reaches
agent context, and where the tag-keyed index lives and how a namespace is
registered. `ADR-038` (operator decision, 2026-10-16) then **supersedes the
`SELF_EMAIL` retirement in `ADR-036`**: the setting stays exactly as it is and
the Profile *mirrors* it. `ADR-036`'s marker-block decision stands untouched.

### §Operator Profile — the Singleton Record, and the Address It Mirrors (`REQ-SB-95-US-01`, `ADR-032`/`ADR-035`/`ADR-036`/`ADR-038`)

- **New:** `app/business/core/operator/operator_profile.py` (the `OperatorProfile`
  entity: the operator's name, their own mail addresses, and the team as
  `email` + `role` entries and nothing more) and `operator_profile_manager.py`
  — the sole gateway onto it, same Manager shape as `IndexManager`, but a
  **singleton**: `get()`/`save()`, no list, no create, no delete, no id
  namespace.
- **New:** `app/data_access/operator_profile.py` — raw I/O only over
  `settings.second_brain_data_path / "data" / "Operator" / "Profile.json"`.
- **Membership, not copies** (`ADR-032`). A team entry is an email and a role.
  The vault's Person notes are filenamed by email, so the email IS the join key
  and the Profile never holds a second description of a colleague (`US-01`
  Scenario 3 is satisfied by *not* storing anything, not by copying).
- **The operator's own address is MIRRORED, not owned** (`ADR-038`, superseding
  `ADR-036`'s retirement). `SELF_EMAIL` stays exactly as it is: a startup-required
  env setting, present in `system_settings._FIELDS` ("Your Email Address",
  `env_key: SELF_EMAIL`, `_check_email` validation), editable on Settings → System,
  with its setup-wizard step unchanged. The Profile **reads** that setting for the
  operator's own address and publishes it into agent context with the rest of the
  profile — it never writes it and never offers a second editor for it.
- **The fresh-install boot path is out of this story's blast radius entirely**
  (`ADR-038`). `config.REQUIRED_FOR_STARTUP` is **not** touched, no startup gate
  moves, `missing_required_settings` keeps naming `self_email`, and
  `setup_wizard.sync_settings_to_hermes(vault_path, data_path, self_email)` keeps
  its **current** source — a Profile save does not call it. `REQ-SB-89`'s
  fresh-install path is untouched by `REQ-SB-95`.
- **The Profile solely owns everything the setting does not**: the operator's
  name, their *other* mail addresses, the team roster as `email` + `role` entries,
  and timezone. Exactly one editable place per fact still holds — it is just two
  surfaces for two different sets of facts, not two writers of one fact.
- **Nothing redeploys, and nothing changes for the deployed scripts.**
  `ingest_email.py`, `ingest_meeting.py`, `retrofit_conversation_index.py` and the
  Graph libs keep reading `SECOND_BRAIN_SELF_EMAIL` from Hermes' `.env`, which
  keeps being written by the same wizard call as today. A running gateway not
  re-reading `.env` is `ADR-035`'s accepted limitation, not a problem to engineer
  around.
- **Excluded from artifact export by default** (`ADR-032`) — the same exclusion
  that already covers `ActionCalls/` and `WorkflowRuns/`.
- **Frontend:** a new Operator Profile Settings page on the live
  `.item-list`/`.item-row`/`.input`/`Save changes` families plus one more card in
  `SettingsPage.tsx`'s `SETTINGS_SECTIONS` grid. `SettingsSystemPage.tsx` is
  **unchanged** — it keeps "Your Email Address" and remains the one editor of it;
  the Profile page shows that address read-only, as a mirror, pointing at
  Settings → System for editing.

### §Operator Facts in Agent Context — the Fourth Marker Block (`REQ-SB-95-US-01`, `ADR-036`)

`ADR-038` leaves this whole sub-section standing: it narrowed only where the
operator's own address lives, not how operator facts reach an agent.

- **The Profile rides the same mechanism as the Action catalogue**: a fourth
  auto-generated, marker-delimited block in the agent's own SOUL.md, beside
  `_SPECIALISTS_*`, `_INDEX_GUIDANCE_*` and `ADR-033`'s catalogue block. The
  reason is structural, not cosmetic: **SOUL.md is the store.** `_to_agent()`
  reads it back through `_split_soul_sections()`, and that is where
  `Agent.prompt` comes from — so anything composed at write time without an
  inverse at read time is absorbed into the prompt and becomes hand-editable.
- **Three deliberate differences from the two precedents:**
  - *Fan-out, not recompute* — the Profile is a singleton, so one save
    republishes every agent with identical text.
  - *The block is never removed when empty.* An unconfigured Profile emits a
    short block saying so and naming where to configure it; that block is what
    makes `US-01` Scenario 5 answerable at all.
  - *Its heading is `## Who you work for`* — never `## Guardrails` or
    `## Scope`, which `_split_soul_sections()` matches exactly and would cut the
    body out into the wrong field.
- **One republish pass, shared with `US-03`.** A dedicated `AgentManager`
  republish walks every agent once, writes each soul, and reloads the Registry
  ONCE — not `update()` per agent, whose `_reload_registry()` is
  `asyncio.run(registry_loader.boot())`, i.e. a full Registry boot per agent (41
  on the reporting install). `US-01` builds this seam; `US-03`'s catalogue
  publication reuses it unchanged, because an Action with
  `allowed_callers: ["*"]` is the same fan-out.
- **Triggered by the save**, the way `SkillManager` calls
  `publish_section_access_map()` on every deploy/undeploy. Editing the Profile is
  enough; no prompt is hand-edited (`US-01`'s "derived, not hand-copied").
- **The operator's own address in the block is read from the `SELF_EMAIL`
  setting** (`ADR-038`), published alongside the Profile-owned facts so agent
  context carries one coherent "who you work for" whichever surface holds which
  fact. Publication *reads* that setting; it never writes it, and changing it on
  Settings → System is what makes the block restate it.
- Publication writes colleague names and addresses into every Hermes profile's
  SOUL.md on this machine. That is local instance data; the export exclusion is
  about bundles and still holds.

Two facts bound everything below, both confirmed by direct reading:

- **The agent runtime is Hermes, out of process.** `business/logic/
  agent_chat_stream.py` is an SSE relay over a live Hermes session; its
  `tool.start`/`tool.complete` handling is display text, not interception.
  Nothing on that path can refuse a tool call.
- **A Hermes-side script already calls this app over loopback.**
  `skills/catalog/vault/vault-search/scripts/search_vault.py` calls
  `GET /vault-search/...` at `SECOND_BRAIN_API_URL` (default
  `http://127.0.0.1:8001`); `vault-index/scripts/build_vault_index.py` POSTs
  `/vault-index/refresh`. The removed inbound MCP direction (`app/config.py`'s
  own comment, and "Second Brain exposes nothing over MCP" above) is not what
  this reuses.

### §Action Catalogue — the Sixth Artifact Kind (`REQ-SB-95-US-02`, `ADR-032`)

- **New:** `app/business/core/actions/action.py` (the `Action` entity: `id`,
  `description`, `inputs` as typed entries with a required flag,
  `allowed_callers`, `needs_confirmation`, exactly one `implementation` of
  `skill` | `http` | `ui`) and `action_manager.py` — the sole gateway onto
  Action data, same shape as `IndexManager`.
- **New:** `app/data_access/actions.py` — raw I/O only, over
  `settings.second_brain_data_path / "data" / "Actions" / <id> / "Action.json"`,
  mirroring `data_access/indexes.py` function for function
  (`list_action_ids`/`read_action_json`/`write_action_json`/`delete_action_definition`).
- **Save-time resolution, not call-time** (`ADR-032`). `skill` resolves against
  `SkillManager` (deployed, not merely catalogued); `http` resolves against the
  running app's own route table, which includes a plugin's routes already
  mounted under `/plugins/<plugin_id>/`; `ui` resolves against the registered
  front-end feature key. A save that cannot resolve is refused naming what did
  not resolve; zero or two implementations is the same refusal. The precedent
  for the refuse-rather-than-ship stance is `SkillManager.deploy()`, which
  refuses on `validate_declared_writes` problems rather than shipping something
  that fails only when it runs.
- **Re-resolution report** (`US-02` Scenario 7): a read-side status per Action
  (`resolves` | `broken`, with what no longer resolves), exactly the shape
  `SkillManager`'s deployment report already returns
  (`current`/`stale`/`missing`/`modified` per skill+profile). Computed on read,
  never cached — the catalogue is small and `business/logic/`'s own no-caching
  convention applies.
- **API:** `app/api/actions_router.py` — flat, single-purpose, same convention
  as `skills_router.py`/`index_router.py`. CRUD plus the call route below.
- **Frontend:** a new Settings page for the catalogue and the one-Action editor,
  on the already-approved `.item-list`/`.item-row` + `.input`/`Save changes`
  families, plus one more card in `SettingsPage.tsx`'s live `SETTINGS_SECTIONS`
  grid.

### §Adding a Kind — the Measured Touch Points (`REQ-SB-95-US-02`/`US-04`)

The `Index` precedent (`ADR-019`, 2026-09-06) is the template, and these are the
exact places a sixth/seventh kind lands (read directly, not estimated):

- `business/logic/artifacts_inventory.py` — compose one more Manager and
  **correct the module header**, which today states `kind` is always one of five
  and "no 6th value is ever produced". The comment is part of the change, not
  collateral.
- `business/logic/artifact_dependency_resolver.py` — a new `elif kind ==`
  branch, and the genuinely new edges: Action → its implementation Skill,
  Workflow → every Action its steps name (recursing into those Actions' own
  Skills).
- `business/logic/artifact_export.py` — a `_PAYLOAD_FOLDER` entry per kind
  (`"action": "actions"`, `"workflow": "workflows"` — naive pluralisation is
  what the existing `"index": "indexes"` entry exists to prevent) and the
  payload-writing branch.
- `business/logic/artifact_import.py` — the `_deploy_<kind>` dispatch
  (`raise ValueError(f"unrecognized artifact kind {kind!r}")` is the current
  fall-through), conflict detection, and the `_next_alternate_id` keep-both path.
- `business/logic/artifact_secret_scan.py` — the new JSON bytes are
  Second-Brain-owned, so they are in the scan's surface.
- No new ADR for any of this: it is `ADR-013`/`ADR-015`'s machinery extended the
  way `Index` already extended it.

### §Plugin-Contributed Actions (`REQ-SB-95-US-02`, `ADR-022`)

- `app/plugin_api.py` gains `register_action(...)` alongside
  `register_router`/`register_subject_enricher`/`register_seed_data_file` — the
  same per-plugin-instance collection shape, so every contributed Action is
  attributable to its `plugin_id` without core naming any plugin.
- A plugin's Actions are **composed at read time**, never written into
  `<DATA_PATH>/data/Actions/`: `ActionManager.get_all()` returns stored Actions
  plus whatever the loaded plugins registered. Uninstalling a plugin therefore
  removes its Actions by construction (they only ever existed while it was
  loaded) and cannot touch the install's own — which is exactly `US-02`
  Scenario 6.
- A plugin Action's `http` implementation names its own mounted
  `/plugins/<plugin_id>/...` route.

### §Catalogue Publication Into Agent Context (`REQ-SB-95-US-03`, `ADR-033`)

- `AgentManager` gains a third auto-generated, marker-delimited block beside
  `_SPECIALISTS_BEGIN/END` and `_INDEX_GUIDANCE_BEGIN/END` — same idempotent
  replace-own-block shape, same "do not hand-edit" marker, removed entirely when
  the agent may call nothing. It lists only the Actions that agent is permitted
  to call, and the one way to call them.
- Regeneration is triggered by the catalogue, not by a human: `ActionManager`
  calls it on every create/update/delete, the way `SkillManager` calls
  `publish_section_access_map()` on every deploy/undeploy. That is `US-03`
  Scenario 8 — editing the catalogue is enough, no prompt is hand-edited.
- **`ADR-033` reads `ADR-032`'s "same mechanism that already publishes the
  section-access map" as the derived-republish *pattern*, not as a second JSON
  file.** Nothing in agent context reads `section_access.json`; the shared
  `vault_manager` does, at write time. The gate below reads the live catalogue,
  never the published text, so a stale block can mislead an agent but can never
  let a call through.

### §The Action Call Gate (`REQ-SB-95-US-03`, `ADR-033`)

- **New:** `app/business/logic/action_invocation.py` — the one validating door.
  Refuses an unknown id, an unknown or missing required input (naming it, never
  defaulting it), a caller not in `allowed_callers`, an implementation that no
  longer resolves, and a confirmation-required call with no consumed grant.
  Nothing is half-performed: validation completes before dispatch begins.
- **New route:** `POST /actions/{action_id}/call` on `actions_router.py`.
- **The agent's only door is one shipped runner Skill** that posts to it over
  loopback, exactly as `search_vault.py` already reaches `/vault-search`. The
  same route backs the in-app UI, so the screen and the agent cannot disagree
  about what exists.
- **Dispatch by kind:** `http` performed by the app; `ui` never performed —
  the response names where the operator does it; `skill` **authorised, not
  performed** — the response carries a single-use grant naming the deployed
  Skill and the validated inputs, and the runner performs it in the profile
  where Skills already run. The app does not execute `skills/catalog/` payload
  (`ADR-019`).
- **Caller identity is the agent id**, which is the Hermes profile id throughout
  this codebase (`SkillManager.deploy(skill_id, profile_id)`,
  `cli.enable_tools(..., profile_id=agent_id)`). `allowed_callers: ["*"]` means
  every agent. Not Sections (`Agent.section_id` is legitimately `None` for an
  unplaced agent) and not agent type.
- **Trust boundary, stated plainly:** the runner names its own profile id and the
  app believes it, as `/vault-search` believes any local caller today. An agent
  with a terminal can still run a deployed Skill directly. This makes the Action
  surface honest; it does not sandbox Hermes.
- `REQ-SB-33-US-01`'s global honest-uncertainty instruction stays where it is —
  this gate is the enforced version of it, not a second instruction beside it.

### §Confirmation and the Action-Call Ledger (`REQ-SB-95-US-03`, `ADR-033`)

- **New store:** `<DATA_PATH>/data/ActionCalls/<call_id>.json` — one record per
  call: who called, which Action, the validated inputs, the outcome
  (`performed` | `refused:<reason>` | `awaiting_confirmation` | `declined`), and
  the unmet-request text when an agent reports that nothing covers a request.
  This is `US-03` Scenario 5's "recorded so a missing capability can be
  discovered"; the reviewable surface over it is explicitly later work.
- **Confirmation flow:** first call of a confirmation-required Action performs
  nothing and returns `awaiting_confirmation` plus the `call_id`; the operator
  confirms or declines on an app surface; a confirmed record is a **single-use
  grant** the re-call consumes exactly once; declining refuses with `declined`.
- **Why not the existing approvals machinery:** `pending_approvals_router.py` is
  archived — not present in the repo — and `GET /agents/{id}/history` returns
  `[]` with a comment naming it as the reason; only
  `load_pending_approvals_state`/`save_pending_approvals_state` survive in
  `data_access/vault_writer.py`. `Agent.working_mode`'s own comment records that
  `human_in_loop`'s Hermes `approval.request`/`respond` path is "not yet wired",
  and `chat_sessions.format_approval_request` currently ENDS the turn. An
  Action's confirmation flag is a per-operation operator decision and is
  orthogonal to `working_mode`, which stays what it is.
- The framework may ship a starter `report-unmet-request` Action (`ADR-032`
  allows shipped starters) so "I cannot do that" leaves a record rather than only
  a sentence.

### §Workflow — the Seventh Artifact Kind (`REQ-SB-95-US-04`, `ADR-032`)

- **New:** `app/business/core/workflows/workflow.py` + `workflow_manager.py` and
  `app/data_access/workflows.py` over
  `<DATA_PATH>/data/Workflows/<id>/Workflow.json` — same Manager/data-access
  split and the same file-per-id shape as Actions and Indexes.
- **Referential integrity, one direction only** (`ADR-034`): a step names an
  Action id; an Action knows nothing about Workflows. Save-time validation
  rejects a step naming an unknown Action; Action deletion asks the Workflow side
  for referencing Workflows and reports them before anything is removed
  (`US-04` Scenario 6). The editor offers only catalogued Actions, so the invalid
  state is hard to reach in the first place.
- `PipelineManager` is the nearest step-based shape to read for reference and is
  **not** shared, extended or migrated (`ADR-032`; `US-04` Scenario 7).

### §Workflow Runs — Ordered by the Framework (`REQ-SB-95-US-04`, `ADR-034`)

- **New store:** `<DATA_PATH>/data/WorkflowRuns/<run_id>.json` — the workflow id,
  the ordered steps, each step's status and outcome, and the Action-call ids it
  produced.
- **New routes:** start a run, fetch the one next step, report that step's
  outcome. The framework hands back exactly ONE step at a time and will not
  advance until the current step's outcome is recorded — that is what makes
  "in order", "no skipped step" and "no invented step" properties of the run
  record rather than promises by the model.
- Every step is dispatched through §The Action Call Gate; a confirmation-marked
  step opens the same `awaiting_confirmation` record and the run pauses there,
  visibly. The report back is composed from recorded step outcomes, so a failed
  step cannot be reported as done.
- `ActionCalls/` and `WorkflowRuns/` are instance data and are excluded from
  artifact export, alongside the Operator Profile (`ADR-032`) — a run is not a
  capability.

### §Entity Resolution — a Generic Tag Resolver, No Plugin Named (`REQ-SB-95-US-05`, `ADR-035`/`ADR-037`)

- **New:** `app/business/logic/tag_resolution.py` (name indicative) — the
  resolver. It is generic over any `<namespace>/<slug>` tag and answers two
  questions only: *which notes carry this tag*, and *which tag does this name
  mean*. It knows nothing of Customers, Partners or Entities and **names no
  plugin** (`ADR-035`, `ADR-022`, `ADR-023`).
- **A name, an alias or a domain** resolves to `(kind, tag, hub)`. Matching is
  case-insensitive, against registered entries only — never a fuzzy search over
  note titles (`US-05` Scenario 1). Two entries matching one name is reported
  **ambiguous**, never silently resolved to one of them (Scenario 3).
- `kind` is an **opaque string** supplied by whoever registered the namespace.
  Core never enumerates kinds — that is `ADR-022`'s CFO test expressed in code.

### §The One Tag-Keyed Index — a Projection, Not an Artifact (`REQ-SB-95-US-05`, `ADR-037`)

- The index is **computed inside `VaultManager.rebuild_index()` and rebound
  alongside `_vault_entries`**, from the `tags` each entry already carries. It
  therefore cannot be newer or older than the notes it groups.
- **No new `Index` artifact, no new cron job, no second refresh trigger.** It
  refreshes exactly when the vault index does — which, since `BUG-082`, is every
  `POST /vault-index/refresh` the `vault-index-rebuild` job makes once it has
  written the disk index, plus every explicit rebuild. `BUG-082` is the whole
  reason this is a projection rather than a stored artifact: the backend's own
  index rebuilt only at boot, and 250 notes were invisible for three days.
- **Keys are every `<namespace>/<slug>` tag present in the vault**, grouped
  regardless of registration — so Scenario 7 holds on an install with no plugins
  at all. Registration turns a *name* into a tag; it does not populate the index.
  A tag key with no registered entry is **reported unknown**, not dropped.
- `ADR-032`'s "a single artifact" is honoured in what it decided — one index, a
  dict lookup, no per-entity provisioning — and is deliberately not read as "an
  `Index` kind instance". The three hand-made per-customer Indexes and their
  hourly jobs are untouched (`US-05` Scenario 4).
- **The scoped read** — hub synthesis first, then tagged evidence newest first —
  is framework business logic over the projection, and the agent reaches it
  through §The Action Call Gate as the `http` implementation of a shipped
  Action (`US-05` Scenario 6). Nothing is published as a file for agents to read.

### §Registering a Tag Namespace (`REQ-SB-95-US-05`, `ADR-035`/`ADR-037`)

- `app/plugin_api.py` gains `register_tag_namespace(namespace, entries)`, where
  `entries() -> list[dict]` yields `slug`, `name`, `aliases`, `domains`, `hub`
  and `kind`. It is a **callable, called at resolution time** — never a list
  captured at register time, because the plugin's own registry
  (`Settings/Entities.md`, already plugin seed data via
  `register_seed_data_file`) is edited while the app runs.
- Same shape as `register_subject_enricher`/`register_agent_matcher`, same
  facade rule: plain dicts out, never a framework entity class.
- **One namespace, one owner** — a second registration of the same prefix is
  refused naming both plugins (the `provide_service` precedent). A callable that
  raises is skipped and logged, and the resolver answers "did not resolve"
  rather than a wrong answer (the `register_agent_matcher` precedent).
- Zero registered namespaces means nothing resolves — `ADR-035`'s "degrades to
  nothing rather than to a wrong answer". The entities plugin registering
  `customer/` and `partner/` is its own work in `sb-plugins-entities`.

### §One Contract Bump for All of `REQ-SB-95` (`REQ-SB-95-US-02`/`US-05`, `ADR-037`)

- `register_action` (`US-02`) and `register_tag_namespace` (`US-05`) are the
  **only two** additions `REQ-SB-95` makes to `plugin_api.py`; `US-03` and
  `US-04` add none.
- Both land **additively while `FRAMEWORK_API` stays 7**. The constant moves to
  **8 exactly once**, in whichever of the two stories lands last, and no plugin
  may depend on either capability until it does. One republish of every
  installed plugin, not two — the operator has taken seven bumps this autumn.
- This is a **planning constraint, not just a coding one**: `US-02` and `US-05`
  carry a cross-story edge on `plugin_api.py`, and the decomposer/product-owner
  must place the single bump in the later of the two rather than discover it.

**Last reviewed:** 2026-10-16 (architect re-pass, `REQ-SB-95-US-01` only, on the
operator's `ADR-038` decision: `SELF_EMAIL` stays exactly as it is — a
startup-required setting, in `system_settings._FIELDS`, editable on
Settings → System, wizard step unchanged — and the Operator Profile **mirrors**
it rather than retiring it, so the fresh-install boot path leaves this story's
blast radius entirely. The §Operator Profile sub-section is rewritten around the
mirror; `ADR-036`'s fourth-marker-block decision, and every other section, are
untouched. No new ADR — `ADR-038` already records the decision.)

Earlier: 2026-10-16 (architect pass, `REQ-SB-95-US-01`/`US-05`, both
cleared by operator decisions recorded in `ADR-035` — `ADR-036`/`ADR-037`
appended: the Operator Profile reaches agent context as a fourth SOUL.md marker
block through one shared republish pass and is the single writer of the
operator's own address, the tag-keyed index is a projection rebound inside
`VaultManager.rebuild_index()` rather than a new Index artifact with a second
refresh trigger, a plugin registers a tag namespace as a callable, and the
`FRAMEWORK_API` bump is taken once for all of `REQ-SB-95`); 2026-10-16
(architect pass, `REQ-SB-95-US-02`/`US-03`/`US-04`
— `ADR-033`/`ADR-034` appended on top of the already-Accepted `ADR-032`: the
Action call surface is one loopback route on this app's own API, the caller is an
agent/profile id, confirmation is a single-use grant in a new Action-call ledger,
and a Workflow is run step-by-step by the framework rather than recited to the
model); 2026-09-02 (architect pass, `REQ-SB-88-US-01`/`US-02` —
no new ADR, both stories confirmed purely additive/consumptive of `ADR-017`'s
already-built per-caller `allowed_callers` mechanism plus ordinary
Template.json data edits; 2026-09-01 architect pass, `REQ-SB-87-US-01`/`US-03`/
`US-05` — `ADR-017`/`ADR-018`, the Email Thread Capture pipeline
consolidation + new Capture/Enrich capability; `REQ-SB-86-US-01`/`US-02` —
`ADR-016`, the Vault Data Export subsystem; `REQ-SB-85-US-01`/`US-02`/
`US-03` — `ADR-013`/`ADR-014`/`ADR-015`, the Artifact Export/Import
subsystem, reviewed 2026-08-31).
