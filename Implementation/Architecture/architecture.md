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

**Last reviewed:** 2026-08-25 (architect pass, `REQ-SB-82-US-01/02/03/05`,
`ADR-007` through `ADR-010`).
