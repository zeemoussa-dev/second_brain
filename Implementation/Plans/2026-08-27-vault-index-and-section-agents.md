# Vault structural index + Section fallback agents — design and build log

**Date:** 2026-08-27
**Status:** All 5 phases built and verified live (operator: "let's write it
up as a plan and Start building"). Not yet a REQ/ADR; this document is the
real starting point for both. Scoped narrowly per the operator's own
decisions along the way: structural indexing only (no semantic/content
layer), fallback-only routing, Customer Section proven first (Technology/
Sales/Industry get the same mechanism once they have an equivalent
subject-tagging convention), Partners left unassigned for now.

## Motivation

Every vault lookup any agent makes today does a full filesystem walk, on
every call, with no caching:

- The MCP tools Hermes agents actually call (`list_notes_in_kind_folder`,
  `retrieve_notes_in_agent_scope`, etc., `app/business/hermes/scope_query_tools.py`,
  `vault_query_tools.py`) call `vault_writer.list_notes_matching_scope`
  (`app/data_access/vault_writer.py:3074-3084`), whose own docstring
  explicitly forbids reusing `vault_indexing.py`'s existing in-memory index
  — "a narrow, independent frontmatter/folder scan" — a full `rglob("*.md")`
  plus a per-file frontmatter parse, every call.
- Hermes Skills' own `vault_manager.py` (`Hermes-Provisioning/skills/
  vault-rebuild/meeting-capture/scripts/vault_manager.py:338-364`) —
  `find_by_id`/`find_by_filename`/`find_in_folder` — do the exact same thing:
  `root.rglob("*.md")`, parsing every note's frontmatter, just to check one
  field (`id` or filename).
- This already caused a real, confirmed production incident (2026-08-26,
  `ingest_meeting.py`): an unscoped `find_by_id` call "fell back to scanning
  the ENTIRE Work/ tree... slow, and it hit an inaccessible file under old,
  unrelated Work/_archive/ content."
- A real, maintained, fast in-memory index already exists
  (`app/business/vault_indexing.py`) — but it's wired up for the React
  frontend only (`vault_search_router.py`, "HTTP-only... no data_access/
  filesystem access of its own"). Nothing agent-facing touches it.

Separately: Sections are a real, live workforce-grouping concept
(`section_registry.py`) but have zero reasoning capability. Most Customers
have no dedicated Expert agent — only "a few that are important" (operator)
— so there's nobody to talk to about the rest.

## Goals (this pass)

1. One canonical, standalone indexing script (no backend dependency, same
   deployment model as `vault_manager.py` — edited once, physically copied
   into whichever Hermes profiles need it).
2. **Structural index only** — paths, `id`, tags, frontmatter. Explicitly
   NOT semantic/content indexing this pass (operator: "maybe in future we
   will need a special indexing system, not there yet").
3. Every Section gets (a) a roster-aware Agent identity that knows which
   Experts are under it, and (b) an array of zero-or-more folder-scoped
   content indexes (operator: "if a section need more than one folder we
   give both indexes to the Expert of Hub").
4. Section agents answer chat as a **fallback only** — tried after routing
   to a specific Expert doesn't match (operator: "Fallback-only").
5. The index is updated by a Hermes cron job (scheduled) **and** on demand,
   triggered by the app's existing Vault Overview "Rebuild index" button via
   `hermes cron run <job_id>` (confirmed real: `hermes cron run --help` —
   "Run a job on the next scheduler tick... job_id"). One script, two
   triggers, no drift between them.
6. Existing capture-pipeline dedup lookups (`find_by_id`/`find_by_filename`/
   `find_in_folder`, used by meeting-capture, threads-builder,
   company-review, the KB writers) switch from full-vault scans to index
   lookups — this has an already-confirmed production incident behind it,
   so it's real leverage, not speculative.

## Non-goals / explicitly deferred

- Semantic/content indexing (embeddings, summaries).
- First-contact routing through a Section agent — fallback-only for v1.

## Section → folder mapping (real gap, not fully settled)

Sections are 100% a workforce grouping today — the 6 real Sections
(`section_registry.py`'s `_STARTING_SECTION_NAMES`: Customer, Librarian,
Industry, Technology, Data Gatherer, Sales) don't map 1:1 onto `Work/`'s own
real top-level folders (from the live Vault Overview breakdown: `Threads`,
`Meetings`, `People`, `Partners`, `Customers`, `Tasks`, `Technology`,
`Industries`, `Initiatives`, `Notes`, `Files`, `Research`, `Sales`,
`Templates`).

Decision (operator): folder-based mapping, root-folder granularity, one
Section can own an array of folders (not forced 1:1).

| Section | Folder(s) | Confidence |
|---|---|---|
| Customer | `Work/Customers` | High — direct name match |
| Technology | `Work/Technology` | High — direct name match |
| Sales | `Work/Sales` | High — direct name match |
| Industry | `Work/Industries` | High — direct name match |
| Librarian | *(none yet)* | Role, not a content domain |
| Data Gatherer | *(none yet)* | Role, not a content domain |
| **unmapped** | `Threads`, `Meetings`, `People`, `Partners`, `Tasks`, `Initiatives`, `Notes`, `Files`, `Research`, `Templates` | Cross-cutting or ownerless today |

Every Section gets an agent regardless (operator: "Each Section Gets An
Agent... and an Array of Indexes") — Librarian/Data Gatherer just start with
an empty index array, same code path, no special-casing. Their fallback
chat has no content index to answer from yet, which is honest, not broken.

**Open, not decided here:** `Partners` (115 real notes) has no owning
Section at all today. Needs a real decision — new "Partner" Section
(mirrors Entities.md's own `## Companies`/`## Partners` split), or folded
into Customer's array — before or during Phase 4 below.

## Architecture

### Index format & storage

- One indexing pass over `Work/`, computing a whole-vault map
  (`id/stem -> {path, id, tags, frontmatter}`, mirroring `vault_indexing.py`'s
  own per-note entry shape so the two stay conceptually consistent) plus one
  JSON slice per real top-level folder actually indexed — a folder is
  computed once even if more than one Section's array ends up referencing
  it later.
- Location: `.second-brain/data/index/vault_index.json` (whole-vault) +
  `.second-brain/data/index/folders/<FolderName>.json` (per-folder) — under
  the App Database Folder (System settings), matching where
  Templates/Providers/etc. already live. JSON, matching every other
  `.second-brain/data/*.json` store in this codebase.

### Who writes it

- New standalone Hermes-Provisioning skill (own `scripts/`, stdlib-only, no
  backend import) — same "edit once, physically copy" model as
  `vault_manager.py`.
- Triggered two ways against the exact same script: a new Hermes cron job
  (cadence TBD, likely similar to `meeting-capture-recurring`'s `every
  30m`), and the app's Rebuild button via `hermes cron run <job_id>`.
  **Open: does "Rebuild index" become one action doing both rebuilds (the
  backend's own in-memory one for the React frontend, and this disk one for
  agents), or two separate actions?**

### Capture-pipeline consumers (existing, real leverage)

`vault_manager.py`'s `find_by_id`/`find_by_filename`/`find_in_folder`
switch from `root.rglob("*.md")` + per-file parse to reading the relevant
folder's index file. Every Skill using these gets faster for free — no
per-Skill changes beyond this one shared function.

### Section agents

- Roster awareness needs no new data — `section_registry.py` already
  tracks `agent_ids` per Section.
- Each Section gains a new field: an array of folder references (its
  content index scope).
- `chat_turn.py` gains a fallback path: when no specific Expert matches,
  route to the mentioned entity's owning Section's own agent, which answers
  using its own folder index(es) — still reads the actual note it finds
  (structural index only, no summarized content yet).
- **Open, not decided here:** does a Section agent need its own real Hermes
  profile (like `masdar-expert`/`taqa-expert`), or is it a lighter routing
  construct inside `chat_turn.py` with no dedicated profile? Changes
  deployment shape substantially — settle before Phase 5.

## Index Filtering (built, 2026-08-27)

Added mid-Phase-1, before Phase 2, per the operator: "Index Filtering a
new settings feature... instead of Hardcoding files." Which top-level
`Work/` folders the indexer walks is now real, editable config
(`.second-brain/index_config.json`, `GET/PATCH /vault/index-config`,
Settings > Vault > Index Filtering) instead of an unconditional
walk-every-folder default. A folder absent from the config still
defaults to included, so this doesn't change Phase 1's original
behavior until the operator actually excludes something. This is
deliberately scoped narrowly to "should this folder be indexed at all" —
it does NOT overlap with the Section → folder OWNERSHIP mapping (still
open, still Phase 4 below); a folder can be included in the index without
being claimed by any Section yet.

## Phase 2 (built, 2026-08-27)

- New Skill `vault-index` (`Hermes-Provisioning/skills/vault-rebuild/
  vault-index/`), deployed to the default/Primary profile (its gateway
  was confirmed running; `meeting-prep-agent`'s own gateway, hosting the
  existing `meeting-capture-recurring` job, was found DOWN during this
  work — a real, separate, pre-existing operational gap, not introduced
  here, not yet fixed).
- Cron job `vault-index-rebuild`, `every 30m`, `--deliver local`.
- `hermes cron run vault-index-rebuild` confirmed working (triggerable
  by job NAME, not just its hex id).
- `POST /vault-index/rebuild` (the app's own "Rebuild index" button) now
  also fires this same job via `subprocess.Popen` — fire-and-forget,
  confirmed necessary live (an agent-mediated run took ~60s, would have
  made the button hang if awaited synchronously).

## Phase 3 (built, 2026-08-27)

- `find_by_id`/`find_by_filename`/`find_in_folder` in
  `Hermes-Provisioning/shared/vault_manager.py` (+ 7 identical copies)
  now try the index first, always falling through to the original
  `rglob` scan on anything less than a verified hit — see the function-
  level docstrings for the exact safety invariant. Only `ingest_meeting.py`
  is a confirmed real external caller today (`find_by_id`, all 3 sites,
  folder-scoped) — `find_by_filename`/`find_in_folder` have no live
  caller yet but got the same treatment for consistency.
- Verified live against the real vault: real-id hit ~0.002s (was
  ~0.06s+), genuine miss still correctly falls through and returns
  `None`, both confirmed from the actual deployed `meeting-prep-agent`
  copy, not just the repo source.
- Redeployed to all 17 real active locations (verified byte-identical):
  11 meeting-capture profiles, azure-kb-writer, compass-kb-writer,
  capture-files, capture-notes, research-kb-writer, vault-index.
- Found, not fixed (follow-up task): an unscoped
  (`note_name=None`) call crashes on a real file under `Work/_archive/`
  — dormant today (no real caller passes `None`), pre-existing.

## Phase 4 (built, 2026-08-27)

- Decided: Partners stays unassigned for now (operator: "Don't include
  Partners for now") — neither a new Section nor folded into Customer.
  Revisit later.
- `folders: string[]` added to the Section model (`section_registry.py`,
  `PATCH /sections/{id}`, Registry's own `Section.json` mirror) — real,
  editable, no hardcoded table, matching the same "instead of
  Hardcoding files" principle Index Filtering already established.
  Settings > Sections surfaces it as a checkbox list of the same live
  folder set Vault Overview/Index Filtering already discover.
- Mapped live: Customer→`Customers`, Technology→`Technology`,
  Sales→`Sales`, Industry→`Industries`. Librarian/Data Gatherer left
  empty (workforce roles, not content domains).

## Phase 5 (built, 2026-08-27)

- Decided: needs a real Hermes profile (operator, resolving the plan's
  own last open question), Customer Section only for now.
- `fallback_agent_id` added to the Section model, editable from Settings
  > Sections. `moderator.match_customer_fallback_agent` generalizes
  `match_customer_expert`'s own subject-tag resolution: dedicated Expert
  always wins if one exists; Section fallback only engages for a
  genuinely uncovered Customer.
- Wired into `chat_turn.py` at BOTH real gap points — found live during
  verification that the first wiring (only the "roster has agents but
  none match" branch) missed the actual motivating case: a brand-new
  conversation with an empty roster never reached that branch at all,
  hitting the unrelated "bring in an Expert first" message instead.
  Fixed by checking the same fallback in the empty-roster branch too.
- New real profile `customer-hub` (`--no-skills`, deliberately
  read-only, no bundled write-capable Skills) with a SOUL.md pointing it
  at `Customers.json`'s structural index plus direct vault reads.
- Verified live end-to-end: a real question about Mubadala (no
  dedicated Expert) on a real Thread with an empty roster routed to
  `customer-hub` and got back a complete, accurate answer citing real
  vault content.
- Hit and worked around a real Hermes compatibility gap along the way:
  `hermes serve` (headless) no longer serves its web UI, which broke
  the backend's only session-token-fetch mechanism for ALL live chat,
  not just this feature. `hermes dashboard --no-open` unblocks it
  (same port/backend); a proper fix is a separate follow-up.
- Also found (unrelated, flagged separately): the Inbox Cockpit's own
  "Customer" info field can resolve to a Partner's name instead —
  root-caused live, not fixed here.

## Phase 5, replicated for Technology/Sales/Industry (built, 2026-08-27)

- Confirmed live before building (operator asked to "Continue to
  Technology, Sales, and Industry"): unlike Customer, these three have
  NO subject-tagging convention on real Meetings/Threads today —
  `technology/`/`sales/`/`industry/` tags exist only on each entity's
  own hub note, never on a conversation about it. Decided (operator):
  build the profiles + config now, leave live routing for later once a
  real tagging convention exists.
- Three new profiles (`technology-hub`, `sales-hub`, `industry-hub`),
  same recipe as `customer-hub` (`--no-skills`, cloned config from
  `research-agent`), each with its own SOUL.md describing its real
  folder structure (hierarchical KB-reference docs, not per-entity hub
  folders) and pointing at its own structural index file.
  `fallback_agent_id` set on all three Sections.
- `moderator.match_customer_fallback_agent`/`chat_turn.py`'s live
  routing NOT extended to these three yet — deliberately dormant until
  the tagging-convention question is answered. Verified
  `technology-hub` directly via `@mention` instead (proves the agent
  itself works; automatic fallback has nothing to trigger it yet).

## Phased build order

Verify live after each phase before moving to the next (this session's own
established discipline) — Phase 1 depends on none of the three open
questions above and can start immediately.

1. **Indexing script** (Hermes-Provisioning, standalone) — walk `Work/`,
   write whole-vault + per-folder JSON. Cross-check output against
   `vault_indexing.py`'s own in-memory index (same note count, same tags)
   as a sanity check.
2. **Cron wiring** — register the job, confirm `hermes cron run <job_id>`
   regenerates the files on demand; wire the app's Rebuild button to also
   trigger it.
3. **Capture-pipeline cutover** — switch `find_by_id`/`find_by_filename`/
   `find_in_folder` to read the index; redeploy to every real profile using
   them (same procedure as the Entities.md relocation); verify a real
   meeting/thread capture run still dedups correctly and is measurably
   faster.
4. **Section → folder mapping** — settle the Partners question, add the
   folder-array field to Sections (backend + Settings UI). This is the
   "affects Sections in Settings a lot" part.
5. **Section fallback agent + chat routing** — settle profile-vs-routing-
   layer, build, verify against a real "customer with no dedicated Expert"
   conversation.

## Open questions to settle before/while building

1. Where does `Partners` (115 notes, no owning Section today) go?
2. Does "Rebuild index" become one button doing both rebuilds, or two?
3. Does a Section agent need its own real Hermes profile, or is it a
   routing-layer construct inside `chat_turn.py`?
