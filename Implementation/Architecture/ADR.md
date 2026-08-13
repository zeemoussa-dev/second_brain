# Architecture Decision Records

Append-only log of architectural decisions. One ADR per decision, numbered
sequentially from ADR-001.

**Never edit an accepted ADR.** A change of mind is a new superseding ADR (linked
both ways). Status enum: `Proposed | Accepted | Rejected | Deprecated | Superseded by ADR-XXX`.

**Alternatives Considered is mandatory** on every ADR.

<!-- ADR format:
## ADR-001: [Short title]
**Status:** Accepted
**Date:** YYYY-MM-DD
**Context:** Why this decision was needed — the forces at play.
**Decision:** What was decided and why.
**Alternatives Considered:** Other options evaluated (mandatory field).
**Consequences:** Trade-offs, implications, and future considerations.
---
-->

## ADR-001: Backend runtime pinned to Python 3.14

**Status:** Accepted
**Date:** 2026-08-10
**Context:** `architecture.md` originally targeted Python 3.12, but the only
Python actually available on the development host is 3.14.6 (via the `py`
launcher — the bare `python` command is a non-functional Windows Store alias
stub). No admin rights are available on this host to install a different
version.
**Decision:** Target Python 3.14 for `src/backend`. The `.venv` at
`src/backend/.venv` is created with `py -3.14 -m venv .venv`.
**Alternatives Considered:** Installing Python 3.12 alongside 3.14 — rejected;
it would require an installer/admin rights or a portable-Python workaround
with no corresponding benefit, since nothing in this project yet depends on
a 3.12-specific feature or library ceiling.
**Consequences:** Dependency versions must stay compatible with 3.14. If a
future dependency requires an older interpreter, this ADR will need a
superseding decision.

---

## ADR-002: Portable Node.js toolchain (no system install)

**Status:** Accepted
**Date:** 2026-08-10
**Context:** The development host has no admin rights available to run the
Node.js Windows installer, and no Node.js was present on the host by any
means (PATH, common install directories) at project start.
**Decision:** Use the official Node.js LTS Windows binary archive
(`node-v24.19.0-win-x64.zip` from `nodejs.org`, LTS "Krypton"), extracted
to `tools/node/` at the repo root (git-ignored, machine-specific). `npm`
ships inside the same archive. `tools/use-node.ps1` dot-sources onto `PATH`
for a shell session; commands can otherwise be invoked directly via
`tools\node\npm.cmd` / `tools\node\npx.cmd`.
**Alternatives Considered:**
- System install via the official installer — rejected, requires admin
  rights not available on this host.
- `winget install OpenJS.NodeJS` — not attempted after the user confirmed
  installers aren't viable here; winget-installed Node still typically
  requires elevation for the machine-wide install path.
- A Node version manager (nvm-windows, Volta) — rejected for now as
  unnecessary indirection; a single pinned portable version is sufficient
  until multi-version needs arise.
**Consequences:** `tools/node/` must be re-provisioned on any new
development machine (it is not committed to git). `npm run dev` documented
in `CLAUDE.md`'s Commands table assumes `tools/node` is on `PATH` for the
session (via `tools/use-node.ps1`) or invoked with its full path.

---

## ADR-003: Layered backend architecture (data_access / business / api)

**Status:** Accepted
**Date:** 2026-08-10
**Context:** The backend needs a structural boundary between reading/writing
the Obsidian vault, the domain logic that operates on parsed notes, and the
HTTP surface that exposes it — established up front so future stories land
in a consistent place rather than accreting ad hoc structure.
**Decision:** `src/backend/app` is split into three layers:
- `app/data_access/` — reads/writes the vault folder and any other storage;
  no business rules, no HTTP concerns.
- `app/business/` — domain logic and orchestration over data read via
  `data_access`; no HTTP concerns, no direct filesystem access.
- `app/api/` — FastAPI routers; translates HTTP requests into calls against
  `business/`, never talks to `data_access/` directly.

`app/main.py` wires the FastAPI app and includes routers from `app/api/`.
**Alternatives Considered:** A conventional `repositories/services/routers`
naming — rejected in favour of `data_access/business/api`, matching the
user's own terminology for the three layers exactly, to keep the
architecture legible against how the user thinks about the system.
**Consequences:** Coder tasks that add a vault-reading capability must land
code in `data_access`, not `business` or `api`; a task that needs to reach
across layers out of this order is a scope violation per the coder's
layer boundary and should escalate rather than reach around it.

---

## ADR-004: Customer is a tag, never a folder level

**Status:** Accepted
**Date:** 2026-08-10
**Context:** The email-classification POC originally wrote notes to
`Work/Customers/<Customer>/<Kind>/`. The operator supplied *Beyond the
Second Brain* (Mo Elkholy) as a standing architecture reference
(`Documentation/References/beyond-the-second-brain-methodology.md`), whose
Chapter 6 argues folders should not be the primary organizing structure for
a thinking vault — an idea (or a note) is multidimensional and a folder
hierarchy forces one physical home, making it invisible from every other
angle it's relevant to. The book explicitly reserves folders for things with
a genuinely single, stable home.
**Decision:** `Work/<Kind>/` only (e.g. `Work/Emails/`, `Work/Files/`,
`Work/Notifications/`) — `Kind` stays a folder level since it's a stable,
single-home property of a note (an email is always an email). `Customer` is
never a folder; it lives only as frontmatter (`customer:`) and a
`customer/<slug>` tag (`app/data_access/vault_writer.py`'s `build_tags`).
`list_known_customers` reads the frontmatter field across all notes rather
than scanning folder names; `list_known_kinds` still scans folder names
under `Work/`.
**Alternatives Considered:**
- Keep the two-level `Customer/Kind` hierarchy — rejected per the book's
  argument above, and it also blocked a clean answer to the earlier
  Unsorted→Affiliate reclassification problem (would have needed a
  dedicated file-move/merge operation).
- Drop `Kind` to a tag too, fully flat `Work/` — rejected; unlike customer,
  kind is not multidimensional (a note is never simultaneously an Email and
  a Notification), so the book's own carve-out for single-home folders
  applies to it.
**Consequences:** All 35 existing notes were migrated live via `POST /poc/
flatten-customer-folders` (`app/business/vault_restructure.py`), zero
collisions, `Work/Customers/` removed once empty. Reclassifying which
customer a note belongs to (e.g. resolving an `Unsorted` note once its real
customer/affiliate is known) is now a tag/frontmatter edit, not a file
move. Two of the book's other structural principles — atomic notes
(one-idea-per-note vs. today's full raw email dumps) and output-oriented
structure (organizing around what's produced, not around input entities)
— remain unaddressed; see `Documentation/References/beyond-the-second-
brain-methodology.md`'s "Tensions" section.

---

## ADR-005: In-process recurring scheduler via APScheduler, plus a new `app/scheduling/` layer

**Status:** Accepted
**Date:** 2026-08-10
**Context:** REQ-SB-07 (`Implementation/UserStories/REQ-SB-07-US-01-
scheduled-recurring-capture.md`) requires the email-capture pipeline
(`app/business/email_classification.py::classify_recent_emails`, exposed
manually today via `POST /poc/classify-emails`) to also run automatically:
every hour, once on app start, and — because Second Brain runs as a
single-process dev server on the user's own laptop rather than a persistent
always-on server — catching up exactly once for any hourly run missed while
the laptop was off or asleep, without ever running two captures
concurrently. There is currently no background scheduler, no persistent
process beyond `uvicorn app.main:app --reload`, and no "when did this last
run" state beyond the unrelated dedup files already living in
`.second-brain/` (`processed_email_ids.json`, `conversation_index.json`).
ADR-003 defines a strict `api → business → data_access` layering, but a
scheduler is a timer/lifecycle-driven trigger source, not a match for any
of those three boxes — it needs its own place, defined once so REQ-SB-08
and REQ-SB-09 (which explicitly plan to reuse "the recurring schedule from
REQ-SB-07" per their own PRD text) inherit a settled home rather than each
improvising one.

**Decision:**
1. **Library: APScheduler** (`AsyncIOScheduler`), wired into FastAPI's
   `lifespan`, over a hand-rolled `asyncio.sleep`-loop. One job is
   registered with `IntervalTrigger(hours=1)`, `coalesce=True`,
   `misfire_grace_time=None`, `max_instances=1`. `coalesce=True` +
   `misfire_grace_time=None` together are exactly agentic-map REQ-069's
   "a missed job fires once on the next opportunity, however late, not
   once per missed slot" semantics — APScheduler's own well-tested misfire
   engine, not hand-written code this project has to debug itself.
   `max_instances=1` gives "skip rather than overlap" (Scenario 4) at the
   library level. Windows suspend pauses this process rather than killing
   it, so this in-memory scheduler correctly resumes and fires a coalesced
   catch-up run the moment the OS wakes it — no persistent job store is
   needed for that case.
2. **The app-start trigger is unconditional application code, not an
   APScheduler job.** On FastAPI startup (`lifespan`), the app fires one
   capture run immediately, every time, regardless of how recently the
   last run completed (Scenario 2, confirmed unconditional by Scenario 5).
   This same code path also *is* the catch-up mechanism for "the process
   was fully closed, not just suspended" (Scenario 3's full-restart case):
   because the app-start run always fires, there is no separate
   conditional "was a run missed?" check to get wrong on this path. The
   APScheduler in-memory misfire/coalesce handling in point 1 covers the
   complementary case — the process stayed alive and the laptop merely
   slept underneath it.
3. **One concurrency guard spans both trigger sources.** A single shared
   guard (e.g. a non-blocking `asyncio.Lock`) lives in the new scheduling
   layer and is checked by both the startup trigger and the APScheduler
   job, so an app-start run and an hourly-boundary run can never overlap
   each other either, not just overlap themselves.
4. **Last-run persistence.** Scenario 1 requires "the last-successful-run
   record is updated once the run completes." This is a small JSON file
   under the existing `.second-brain/` state directory that
   `app/data_access/vault_writer.py` already owns for
   `processed_email_ids.json` / `conversation_index.json` — written by
   `data_access`, updated by `business` after each completed run, the same
   call shape `email_classification.py` already uses for
   `mark_email_processed`. It exists for audit and for REQ-SB-11 (future
   observability) to read later. Per point 2, none of this story's five
   ACs require the scheduling *decision logic itself* to read this record
   back — the decomposer/coder should not build a conditional
   "read-last-run-time-to-decide-whether-to-fire" path the ACs don't
   actually call for.
5. **New layer: `app/scheduling/`** — a fourth top-level package alongside
   `api/`, `business/`, `data_access/`. It owns the APScheduler instance,
   its FastAPI `lifespan` wiring, the interval/misfire/coalesce
   configuration, and the concurrency guard. It is a **trigger source**,
   structurally parallel to `api/`: both translate an external event (an
   HTTP request; a timer/lifecycle event) into a call against `business/`,
   and neither reaches into `data_access/` directly — this extends, but
   does not edit, ADR-003's boundary (ADR-003 remains Accepted and
   unmodified).
**Alternatives Considered:**
- **Hand-rolled `asyncio.sleep`-based interval loop** (compute remaining
  time to the next hourly boundary, `asyncio.sleep` it, loop; track
  elapsed-since-last-run manually for catch-up) — rejected. This project's
  own precedent (ADR-001, ADR-002) favours the already-solved option over a
  bespoke one built for its own sake; misfire/coalesce/overlap-guard
  semantics are easy to get subtly wrong by hand (e.g. correctly detecting
  "the OS suspended us mid-sleep" is exactly the kind of edge case a
  mature scheduling library has already hardened against). There is no
  durability gain from hand-rolling here to offset the risk of a first-cut
  bug in stop/skip/catch-up logic that's awkward to test on a real
  laptop-sleep cycle.
- **APScheduler with a persistent job store** (`SQLAlchemyJobStore` backed
  by a small SQLite file, so `next_run_time` itself survives a full
  process restart) — rejected for this story. It would add a new
  dependency (SQLAlchemy) and a new state-storage mechanism inconsistent
  with the existing `.second-brain/` JSON convention, to solve a problem
  the unconditional app-start trigger (point 2) already solves for free:
  since app-start always fires a run regardless of recency, there is no
  case where the scheduler needs to remember an exact overdue
  `next_run_time` across a full restart. Revisit if a future story needs
  the scheduler itself (not just the last-run record) to survive process
  restarts with sub-hour precision.
- **OS-level scheduling** (Windows Task Scheduler invoking the endpoint on
  a timer) — rejected. It would run outside the FastAPI process (an extra
  moving part, extra Windows-specific setup with no admin-rights guarantee
  — see ADR-001/ADR-002's no-admin-rights constraint), duplicate the
  concurrency-guard problem across process boundaries, and doesn't
  naturally give an in-process app-start hook the way FastAPI's own
  `lifespan` does.
- **Cron-expression libraries** (e.g. `croniter` plus a manual loop) —
  rejected as strictly more machinery than this story needs; hourly
  cadence has no cron-expression complexity to justify it, and
  APScheduler already ships an `IntervalTrigger` for exactly this shape.
**Consequences:**
- New dependency: `apscheduler` (added to `src/backend/requirements.txt`
  by the coder task that implements this ADR).
- `app/main.py` gains `lifespan` wiring to start/stop the scheduler; the
  scheduler and the concurrency lock become long-lived objects for the
  life of the process, not request-scoped.
- `app/scheduling/` calls into `business/` only — it must not import from
  `data_access/` directly, mirroring the constraint already binding
  `api/`.
- The `.second-brain/` state directory gains a new JSON file (the last-run
  record) alongside the two that already exist there; exact naming/schema
  is left to the decomposer/coder, but it must not collide with
  `processed_email_ids.json` / `conversation_index.json`.
- REQ-SB-08 and REQ-SB-09 inherit `app/scheduling/` as the settled home
  for "the recurring schedule from REQ-SB-07" — their own `/plan-tasks`
  passes decide how they plug an additional pipeline into the same
  scheduler (a second job, or generalizing the one job to run multiple
  pipelines), rather than re-deciding where scheduling code lives.
- Because misfire handling here is in-memory only, a true crash (not just
  laptop sleep) that kills the process still relies entirely on the
  app-start trigger (point 2) for catch-up — sufficient for this story's
  ACs, but worth knowing if a future story ever needs sub-restart catch-up
  granularity.

---

## ADR-006: New top-level vault root `Templates/`; guide note lives outside it, under `Work/Guides/`

**Status:** Accepted
**Date:** 2026-08-11
**Context:** REQ-SB-15 (`Implementation/UserStories/REQ-SB-15-US-01-manual-
entry-templates-and-guide.md`) needs Obsidian's core Templates plugin
configured with a single "template folder location" holding one template
file per resolved note type (Customer, Opportunity, Agreement,
Consumption-Snapshot — schema already resolved in
`Implementation/Plans/2026-08-10-vault-taxonomy-draft.md`), plus an in-vault
guide note explaining what each type is for and how to use its template.
`architecture.md` currently documents exactly two top-level vault roots,
`Personal/` (untouched by Second Brain) and `Work/` (everything Second
Brain's *backend* writes lands here, per `MEMORY.md`) — that `Work/`-only
constraint was written to bound backend code, not human-authored vault
tooling, so it does not by itself answer where template files or the guide
note belong. Obsidian's Templates feature also has a real functional
constraint worth designing around: every file inside the configured
template folder is listed as insertable in the "Insert Template" picker —
there is no way to exclude a specific file from that list by naming
convention or otherwise.
**Decision:**
1. Add a third top-level vault root, `Templates/` (sibling to `Personal/`
   and `Work/`), containing exactly the four template files
   (`Templates/Customer.md`, `Templates/Opportunity.md`,
   `Templates/Agreement.md`, `Templates/Consumption-Snapshot.md`) and
   nothing else. Obsidian's Settings → Templates → "Template folder
   location" is pointed at `Templates/` — a one-time manual step performed
   by the user in their own Obsidian install; not something `src/backend`
   automates, scripts, or tracks, and out of this story's/any coder task's
   scope.
2. The in-vault guide note lives at `Work/Guides/Manual-Entry-Guide.md` —
   under the existing `Work/<Kind>/` kind-folder convention (`Guides`
   becomes a new dynamically-discoverable kind, consistent with
   `list_known_kinds` scanning folder names under `Work/`, no code change
   required) — deliberately outside `Templates/`, so it can never be listed
   or accidentally inserted by Obsidian's "Insert Template" command.
3. `Personal/` remains untouched and out of scope, as before. `Templates/`
   is not backend-write territory — `MEMORY.md`'s "everything Second Brain
   writes goes under `Work/`" constraint continues to bind `src/backend`
   code specifically; it never governed human/Obsidian-native content
   authored directly in the vault, which is what this story's templates and
   guide note are.
**Alternatives Considered:**
- Nest templates under `Work/Templates/` (a `kind` folder, like
  `Work/Emails/`) — rejected: templates are not captured content classified
  by kind the way Compass-classified notes are; nesting them under `Work/`
  would present them to a future indexer/search feature (REQ-SB-01/
  REQ-SB-02) as ordinary indexable note content sitting alongside real
  notes, when structurally they're closer to vault tooling/configuration
  than to a note.
- Guide note inside `Templates/` (e.g. `Templates/_Guide.md` or
  `Templates/README.md`) — rejected: Obsidian's Templates feature lists
  every file in the configured template folder as insertable regardless of
  filename; a non-template guide note there would be selectable by "Insert
  Template" and inserted verbatim into a target note, which is not its
  purpose and would confuse the user. There is no folder-exclusion
  mechanism to work around this, so no naming convention fixes it.
- `Templates/` nested inside `Personal/` — rejected: `Personal/` is
  documented as untouched-by-Second-Brain content; these templates exist
  specifically for the Second Brain-relevant schemas (Customer/Opportunity/
  Agreement/Consumption-Snapshot), so placing them there would misrepresent
  ownership and be a surprising place to find them.
- Guide note kept only in the project repo (`Documentation/`), not the vault
  — rejected outright by the story's own Scenario 5 and the PRD's own
  acceptance text: the user works primarily in Obsidian and must not need to
  leave it or consult the repo to use the templates.
**Consequences:**
- `architecture.md`'s "two top-level roots" statement is updated to three:
  `Personal/`, `Work/`, `Templates/`.
- A future vault indexer (REQ-SB-01/REQ-SB-02, not yet built) will need to
  decide whether `Templates/` is indexed/searched at all — templates hold
  placeholder frontmatter, not real note content, so it likely should be
  excluded; left as an open flag for whichever story builds indexing, not
  resolved here.
- `Work/Guides/` becomes a new dynamically-discovered kind folder with no
  code change required for `list_known_kinds` to surface it; the guide
  note's own frontmatter (if any) is authored once by hand, not produced or
  classified by the Compass capture pipeline.
- This is a vault-content-only decision — it does not touch `src/backend`
  or `src/frontend`; REQ-SB-15's task scope is authoring files directly in
  the vault at `VAULT_PATH` plus this ADR/architecture.md update, and
  explicitly excludes automating Obsidian's own local application settings
  (the "Template folder location" setting remains a one-time manual step
  for the user).

---

## ADR-007: No agent-orchestration framework (e.g. LangGraph) in Second Brain — Hermes owns orchestration

**Status:** Superseded by ADR-015
**Superseded note (2026-08-11, append-only — the body below is otherwise
unchanged, per this file's own "never edit an Accepted ADR" rule):**
`ADR-015` reverses this ADR's core "Second Brain's own stack stays free
of an orchestration framework" decision, but only for a bounded surface —
Second Brain's own in-app Agents Map agent behavior (chat, Hub routing,
memory, skill invocation — `REQ-SB-20`/`25`/`26`/`27`). This ADR's other
claim, "Hermes owns orchestration on its own side of the integration
boundary," remains entirely true and is carried forward unchanged by
`ADR-015` — Hermes's own future integration (`REQ-SB-03`, not yet built)
is untouched. Read `ADR-015` for the current, correct decision on
Second Brain's own in-app agent orchestration.
**Date:** 2026-08-11
**Context:** The operator asked directly whether an agent-orchestration
framework (LangGraph named specifically) needs to be introduced into this
architecture, or whether Hermes already covers that ground. `MEMORY.md`
already records that Second Brain's PRD requirements were seeded by walking
agentic-map's 76-entry requirements list and classifying each Port/Adapt/
Drop — multi-agent orchestration and the agent-routing console were
explicitly dropped as out of scope (2026-08-10). Separately, `MEMORY.md`
also records Hermes's own internal architecture as context: Hermes already
categorizes agents by Type (`Expert`, `Worker`, `Hub`, more to come) and by
Section/Department, with multi-provider LLM access — i.e. Hermes already
owns agent typing and orchestration on its own side of the integration
boundary. Nothing in any Accepted PRD requirement (`REQ-SB-01`..`REQ-SB-17`)
asks Second Brain itself to route between agents, plan multi-step agent
work, or manage agent state machines.
**Decision:** Second Brain does not add LangGraph (or any other
agent-orchestration framework) to its own stack. Second Brain's role stays
"a good knowledge base for Hermes-connected agents to query" (`REQ-SB-03`,
future P2 integration surface) — not an orchestrator of agents itself.
Orchestration, if and when it's needed, is Hermes's responsibility, per the
integration-sourcing precedence constraint already established in
`MEMORY.md` (prefer/extend the existing external system over building a
parallel mechanism inside this project).
**Alternatives Considered:**
- Add LangGraph now, ahead of any concrete orchestration need — rejected:
  no Accepted requirement calls for Second Brain to orchestrate multi-step
  agent work; adding it speculatively would duplicate a concern Hermes
  already owns and introduce a framework dependency with no requirement
  driving it, contradicting this project's own "don't design for
  hypothetical future requirements" discipline.
- Add LangGraph scoped narrowly to Second Brain's own internal pipelines
  (e.g. the email-capture business logic) — rejected: those pipelines are
  simple, linear, already-working Python functions (`classify_recent_emails`
  and its equivalents); a graph-orchestration framework would be
  disproportionate machinery for straight-line fetch → classify → write
  logic with no branching agent behavior to coordinate.
**Consequences:**
- If a future requirement genuinely needs Second Brain itself to coordinate
  multi-step or multi-agent work (not just serve KB queries to agents
  Hermes already orchestrates), that is new scope requiring its own
  requirement and a superseding ADR — not assumed or pre-built here.
- `src/backend`'s dependency set stays free of an orchestration framework;
  nothing in this ADR blocks Hermes or agentic-map from using LangGraph (or
  anything else) on their own side of the integration boundary — this ADR
  governs Second Brain's own stack only.

---

## ADR-009: Partner — a second, mutually-exclusive tag-and-hub-note namespace parallel to Customer, in a new sibling module

**Status:** Accepted
**Date:** 2026-08-11
**Context:** `REQ-SB-16-US-01` (`Implementation/UserStories/REQ-SB-16-US-01-
partner-hub-notes-and-migration.md`) needs a second entity taxonomy,
Partner, that is structurally identical to Customer's hub-note/tag/wikilink
mechanism (`ADR-004`, `REQ-SB-14`) but deliberately scoped down (no
Pipeline/Agreements/Consumption-equivalent sub-entities) and kept strictly
**mutually exclusive** with Customer at the tag/frontmatter level — a
company is a Customer, a Partner, or neither, never both (operator's
explicit choice, `MEMORY.md` 2026-08-11). This is the first time the vault
taxonomy needs two parallel, mutually-exclusive "which top-level company
relationship is this" tag namespaces sharing the exact same underlying
mechanism (hub-note existence + inline wikilink), and the first time a real,
already-captured company (Microsoft) needs migrating from one namespace to
the other. The story's own Constraints explicitly deferred the exact
module/function layering and the migration's exact shape to this
`/plan-tasks` pass. Two structural questions needed settling before the
decomposer could break this into tasks: (1) does the Partner mechanism
extend the existing `customer_hub_linking.py` module or live in a new
parallel module, and (2) is the one-time Customer→Partner migration a
generic, vault-scanning operation or limited to the specific notes the
story's own Context names. On (2): live vault inspection during this
architecture pass (`C:\myWorx\Moussa MD\Moussa Brain\Work\`) found the
actual set of already-mistagged notes is **larger** than the story's
narrative count of "5 Person notes and 2 Email notes" — 1 Newsletter note
and 4 Notification notes also already carry `customer: Microsoft` /
`customer/microsoft`, beyond the 7 the story names. This does not
contradict any Accepted ADR, the PRD, or a `MEMORY.md` constraint (the
story's own Scenario 6 already only claims coverage of "the 5 Person notes
and 2 Email notes" as an illustrative, not exhaustive, description of what
was found), but it is exactly the kind of layering question this ADR
resolves: a generic, vault-scanning migration design (below) picks up every
mistagged note regardless of exactly how many exist or which `kind` folder
they live in, so this finding changes nothing about correctness — it is
recorded here as the reason a hardcoded-file-list design was rejected.
**Decision:**
1. Partner reuses `ADR-004`'s tag-not-folder pattern exactly — `partner:`
   frontmatter, a `partner/<slug>` tag, `Work/Partners/` is a `kind` folder
   holding hub notes only (same shape as `Work/Customers/`). No new
   folder-vs-tag tradeoff; this is a direct extension, not a fresh question.
2. A new, dedicated module, `app/business/partner_hub_linking.py`,
   structurally mirrors `customer_hub_linking.py`'s two granular primitives
   (`ensure_partner_hub_note`, `link_note_to_partner_hub`) rather than
   adding Partner-branch parameters/functions into `customer_hub_linking.py`
   itself. This keeps the `Done`, `Accepted`-mechanism REQ-SB-14 module and
   its existing `email_classification.py` call site untouched (this
   project's "minimal changes" rule), and keeps each module's name matching
   exactly what it does — a future reader looking for "how are Partners
   linked" finds `partner_hub_linking.py` directly, the same
   one-module-per-entity/operation shape already established by
   `tag_backfill.py`, `vault_restructure.py`, `customer_hub_linking.py`, and
   `people_extraction.py`.
3. New `app/data_access/vault_writer.py` primitives mirror the Customer
   hub-note baseline primitives (`partner_hub_note_path`,
   `partner_hub_note_exists`, `create_partner_hub_note_baseline`,
   `ensure_partner_hub_note_baseline_frontmatter`, `build_partner_tags`,
   `list_known_partners` — the last mirroring `list_known_customers()`'s
   vault-derived, never-hardcoded pattern exactly) but with Partner's own,
   shorter baseline-key set — `type`, `partner`, `tags` only, no
   `affiliate_of`-equivalent (Partner deliberately has no Affiliate concept,
   the story's own explicit scoping).
4. The one-time Customer→Partner migration
   (`partner_hub_linking.migrate_customer_to_partner(customer_name: str)`)
   is a **generic, vault-scanning retrofit**, not a hardcoded list of
   specific note paths: it moves the named customer's hub note
   (`Work/Customers/<name>.md` → `Work/Partners/<name>.md`, reusing the
   existing `vault_writer.move_note_and_attachments` primitive
   `vault_restructure.py` already established) and then iterates every
   vault note via the existing `list_all_note_paths()`/`read_note()` scan —
   the same pattern `retrofit_customer_hub_links`/`retrofit_people_from_emails`
   already use — retagging every note whose `customer` frontmatter equals
   the given name. This is what correctly picks up the additional
   Newsletter/Notification notes found live during this pass (see Context),
   consistent with `MEMORY.md`'s standing pattern ("never hardcode a
   customer or kind list in business logic — read what's already there").
5. Three new **generic** `vault_writer.py` primitives are needed beyond the
   existing insert-if-missing family, because a migration renames/replaces
   an *existing* value rather than filling in an absent one: a
   frontmatter-key rename (rename a key and set its new value, no-op once
   the old key is already absent — the idempotency mechanism for reruns), a
   tags-list swap (replace one tag with another within the `tags` list,
   same no-op-if-absent contract), and a body-line-label replace (swap
   `**Customer:** [[X]]` for `**Partner:** [[X]]` in place, no-op if the
   old line is already absent). Each returns a boolean/count so the
   migration and its endpoint can report what changed — mirroring every
   existing insert-if-missing primitive's own "return whether it did
   anything" contract. These are written generically (not Partner-specific)
   so a future migration of this same rename/replace shape can reuse them.
**Alternatives Considered:**
- Generalize `customer_hub_linking.py` into a `company_hub_linking.py`-style
  module parameterized by entity type (Customer vs. Partner), rather than a
  parallel sibling module — rejected: would require touching and
  re-testing the already-`Done`, mechanism-`Accepted` REQ-SB-14 module and
  its existing `email_classification.py` call site, for a story that
  explicitly does not want a Partner-equivalent capture-pipeline hook (see
  the story's own Non-Goals). A parallel sibling module is a strictly
  additive, lower-risk change that matches this project's existing
  one-module-per-entity/operation precedent; none of `tag_backfill.py`,
  `vault_restructure.py`, `customer_hub_linking.py`, `people_extraction.py`
  is a shared generic module today, so unifying now would be the odd one
  out, not a continuation of an existing pattern.
- Hardcode the migration to the exact 5 Person + 2 Email note paths the
  story's Context names — rejected once live vault inspection (this
  architecture pass) found the actual mistagged set is larger (Context,
  above); a hardcoded list would also silently go stale the moment vault
  content changes again, unlike a generic scan, and contradicts the
  project's standing vault-derived-not-hardcoded pattern.
- Give Partner the same `affiliate_of`-style sub-entity as Customer for
  schema symmetry — rejected per the story's own explicit, operator-
  confirmed scoping: a partner relationship isn't a sales/consumption
  relationship, so Pipeline/Agreements/Consumption/Affiliate-equivalents are
  deliberately not built for Partner.
**Consequences:**
- `architecture.md`'s Data Model gains a "Partner Hub Notes &
  Mutually-Exclusive Company Taxonomy (REQ-SB-16)" subsection (this same
  pass) naming every new function/module.
- `vault_writer.py` grows three new generic replace/rename primitives
  (point 5) usable by any future migration that needs to rename an existing
  frontmatter key/tag/body-line-label, not just this one — a reusable
  addition, not single-purpose plumbing.
- `people_extraction.ensure_person_note` gains a second, mutually-exclusive
  branch (Partner, checked only after Customer finds no match) — its
  return dict grows a new `partner_matched` key alongside the existing
  `customer_matched`/`linked` keys; existing callers reading only
  `customer_matched`/`linked` are unaffected (additive field).
- A third company-relationship type beyond Customer/Partner (should one
  ever be proposed) would need its own architecture pass to decide whether
  it reuses `partner_hub_linking.py`'s shape or needs a new generalization
  — not pre-designed here.

---

## ADR-008: Meetings capture — Outlook Calendar COM-read function, occurrence dedup key, vault-owner self-email source, and hourly-scheduler reuse

**Status:** Accepted
**Date:** 2026-08-11
**Context:** REQ-SB-08 (`Implementation/UserStories/REQ-SB-08-US-01-meeting-
notes-from-calendar-capture.md`) requires calendar meetings to become
Meeting-type vault notes the same way email already does, on the same
recurring schedule (ADR-005). `app/data_access/outlook_com.py` currently
only reads mail (`list_recent_mail`) and explicitly excludes meeting-invite
items — no calendar-read function exists yet. Four concrete mechanism
questions were left open by the story for this pass: (1) what shape/window
the new calendar-read function uses and which fields it returns; (2) what
uniquely identifies one calendar *occurrence* for dedup/filenames; (3) how
"the vault owner's own email" is identified so it can be excluded from
attendee processing (Scenario 11, operator-confirmed behaviour); (4)
whether meetings capture rides REQ-SB-07's existing hourly job or needs its
own. Per `MEMORY.md`'s Hermes integration-sourcing precedence, the
calendar-read function should port/wrap agentic-map's own working
`services/gateway/outlook_com.py` precedent
(`list_upcoming_events`/`list_calendar_since`, both read in full for this
decision) rather than being designed fresh.
**Decision:**
1. **New sync function `list_calendar_events(days_back, days_ahead, limit)`
   in `app/data_access/outlook_com.py`**, mirroring `list_recent_mail`'s
   exact conventions in *this* codebase (plain synchronous function — not
   agentic-map's `asyncio.to_thread`-wrapped async shape, since Second
   Brain already wraps the whole business-layer capture call in
   `asyncio.to_thread` one layer up, in `capture_scheduler.py`; same
   `pythoncom.CoInitialize()/CoUninitialize()` bracketing; same
   best-effort per-item `try/except: continue` skip). Internally it ports
   agentic-map's `_list_upcoming_events_sync`/`_list_calendar_since_sync`
   mechanics: `ns.GetDefaultFolder(9)` (`_OL_FOLDER_CALENDAR`, new
   constant, ported), `items.IncludeRecurrences = True` (this is what
   expands a recurring series into individual occurrence items — ported
   as-is, no reinterpretation), `items.Sort("[Start]")`. **The sync window
   is a single bounded date range centred on "now"** — `[now - days_back,
   now + days_ahead]` — rather than either of agentic-map's two narrower
   semantics alone: `list_upcoming_events` (future-only, so an
   already-happened meeting a user wants to add minutes to would never be
   captured) or `list_calendar_since` (a persisted `LastModificationTime`
   watermark — a new state-file/cursor mechanism this project's email
   pipeline has no equivalent of; email capture instead uses a simple
   bounded `list_recent_mail(limit=N)` fetch plus a processed-IDs set for
   idempotency, and this mirrors that simpler shape for calendar rather
   than importing agentic-map's more elaborate delta-sync cursor). Exact
   default values for `days_back`/`days_ahead` are a task-level parameter
   default, not fixed by this ADR — same latitude ADR-005 left for the
   last-run-record's exact filename/schema. Per-event fields returned:
   `id` (EntryID), `subject`, `start`/`end` (ISO datetime strings),
   `location`, `organizer` (display string, via `getattr(item, "Organizer",
   "")`, ported as-is), and `attendees: list[{"name": str, "email": str}]`
   — a new `_resolve_attendees(item)` helper ports agentic-map's
   `_resolve_recipients_sync` EX-address-resolution logic
   (`GetExchangeUser().PrimarySmtpAddress` for internal Exchange
   recipients) but returns structured name/email pairs instead of a
   formatted display string, and **merges required (`To`) and optional
   (`Cc`) recipients into one flat list** — the resolved Meetings schema's
   `**Attendees:** [[Person1]], [[Person2]], ...` body line makes no
   required/optional distinction, so there is no reason to carry that
   split forward into this project's schema.
2. **Dedup key: Outlook `EntryID` (`item.EntryID`), not
   `GlobalAppointmentID`.** Every expanded occurrence returned by
   `items.IncludeRecurrences = True` is treated as a plain item with its
   own `EntryID`, exactly as agentic-map's own precedent already does with
   no additional series/occurrence identifier — porting that behaviour
   as-is rather than introducing new mechanism. This also matches the
   story's own Scenario 9 text verbatim ("distinguished by its own date
   and entry-id-suffix"), which already names EntryID as the disambiguator.
   A new `.second-brain/processed_meeting_ids.json` file mirrors
   `processed_email_ids.json`'s exact flat-set-of-IDs shape
   (`load_processed_meeting_ids()`/`mark_meeting_processed(entry_id)` in
   `vault_writer.py`) — one dedup mechanism, applied to a second entity
   type, not a second concept. Filenames use the same 8-character
   EntryID-suffix slice email already uses:
   `Work/Meetings/<subject>-<date>-<entry-id[-8:]>.md`.
3. **Vault-owner self-email source: a new required `self_email: str` field
   on `app/config.py`'s `Settings`, read from `.env`** (added to
   `src/backend/.env.example` alongside `VAULT_PATH`/`COMPASS_*`) — not a
   dynamic Outlook COM current-user lookup. The vault owner's own address
   is a fixed fact about *this* single-user deployment, the same category
   as `VAULT_PATH` and the Compass credentials (already `Settings`-
   configured, not derived), not vault-content that genuinely grows over
   time the way `list_known_customers`/`list_known_kinds` do — so
   `MEMORY.md`'s "don't hardcode, derive from the vault" pattern does not
   apply here; that pattern protects against hardcoding open-ended
   *content* enumerations, not a single static identity fact. The new
   `meeting_classification.py` module filters `self_email` (case-
   insensitive) out of the attendee list returned by
   `list_calendar_events` before any attendee reaches
   `people_extraction.ensure_person_note` or customer derivation
   (Scenario 11).
4. **Meetings capture rides REQ-SB-07's existing hourly job — no second
   scheduled job, no second concurrency guard.**
   `email_classification.run_capture_and_record_completion` (already
   self-documented as "Scheduling-layer entry point (ADR-005)" and already
   the sole function `app/scheduling/capture_scheduler.py` calls) gains one
   additional call, `meeting_classification.classify_recent_meetings()`,
   alongside its existing `classify_recent_emails()` call, before the one
   shared `vault_writer.record_capture_run_completed()` call.
   `capture_scheduler.py` itself requires **zero code changes** — it
   already treats `run_capture_and_record_completion` as an opaque unit, so
   email and meeting capture now both ride the same hourly
   `IntervalTrigger`, the same `coalesce=True`/`misfire_grace_time=None`
   catch-up semantics, the same unconditional app-start trigger, and the
   same shared `_capture_run_lock` (ADR-005 points 1–3) with no changes to
   any of them. This extends, but does not rewrite or contradict, ADR-005
   — ADR-005's own Consequences section already named this exact path
   ("generalizing the one job to run multiple pipelines") as the intended
   way a second pipeline like this one would plug in, as an alternative to
   "a second job." ADR-005 remains Accepted and unmodified.
**Alternatives Considered:**
- **Use `list_upcoming_events`'s forward-only window as-is** (future
  meetings only) — rejected: a meeting that already happened but hasn't
  yet been captured (e.g. the app was off when it occurred) would never
  produce a note, undermining the note's own purpose as a place to add
  minutes after the fact.
- **Port `list_calendar_since`'s `LastModificationTime`-watermark delta
  sync verbatim** — rejected for this story: it requires a new persisted
  cursor/state-file concept this project's own capture pipelines don't
  otherwise use (email capture dedups via a processed-IDs set over a
  simple bounded fetch, not a watermark), and agentic-map's own docstring
  on that function records a real, previously-live bug in watermarking on
  the wrong timestamp for recurring series — importing that entire
  mechanism (and its documented failure mode) is more risk than this
  story's ACs call for. Revisit if a future story needs true incremental
  delta-sync semantics.
- **`GlobalAppointmentID` as the occurrence dedup key** — rejected: neither
  agentic-map's own precedent nor this story's Scenario 9 text calls for
  it (Scenario 9 explicitly names "entry-id-suffix"); introducing
  `GlobalAppointmentID` parsing would be new mechanism, which the story's
  own Constraints discourage ("port/wrap... rather than designing fresh").
  Noted as a real risk in Consequences below, not dismissed.
- **Outlook COM current-user lookup for the vault owner's own email**
  (e.g. `ns.CurrentUser`, resolved via the same
  `GetExchangeUser().PrimarySmtpAddress` pattern already used for
  sender/attendee resolution) — rejected in favour of a config value: it
  would add a new COM failure surface (delegate mailboxes, shared
  accounts, multiple Outlook profiles are all real edge cases for
  `CurrentUser`) for a value that is static and already known with
  certainty by the single user running this personal tool, and it would be
  untestable without a live Outlook session, unlike a plain config read.
  Revisit only if this project ever becomes genuinely multi-user.
- **A second scheduled job for meetings** (its own `IntervalTrigger`, its
  own concurrency guard) — rejected: one hourly cadence already correctly
  serves both pipelines, a second job would duplicate the concurrency-guard
  problem ADR-005 point 3 already solved once, and ADR-005's own
  Consequences section explicitly anticipated and preferred "generalizing
  the one job" over adding a second one.
- **Moving `run_capture_and_record_completion` out of
  `email_classification.py` into a new dedicated orchestration module**
  (e.g. `app/business/capture_orchestration.py`) — considered, since the
  function's own docstring already self-identifies as scheduling-layer
  scoped rather than email-specific. Rejected for this pass as scope
  creep beyond what this story needs (CLAUDE.md's minimal-changes
  discipline): the function can gain one more call in place without any
  behavioural or layering change, and `capture_scheduler.py` needs zero
  edits either way. Revisit if a third capture pipeline (e.g. REQ-SB-09)
  makes the email-scoped module name genuinely misleading.
**Consequences:**
- New dependency-free capability: `list_calendar_events` in
  `outlook_com.py`, following `list_recent_mail`'s exact conventions
  (no new library).
- New `Settings.self_email` field — required, no default, added to
  `.env.example`; any environment missing it fails Settings construction
  the same way a missing `VAULT_PATH`/`COMPASS_*` value already does.
- New `.second-brain/processed_meeting_ids.json` state file, alongside the
  two/three that already exist there — must not collide with
  `processed_email_ids.json` / `conversation_index.json` /
  `last_capture_run.json`.
- New `app/business/meeting_classification.py`, mirroring
  `email_classification.py`'s shape (fetch → derive customer via attendees
  → write note → link customer hub + attendee Person notes → dedup) and
  reusing `people_extraction.ensure_person_note` and
  `customer_hub_linking`'s granular primitives as-is, per the story's
  Constraints — no changes to either of those two modules' existing public
  functions.
- `vault_writer.py` gains meeting-note file-I/O primitives following the
  established baseline-preservation contract (Person/Customer-hub
  precedent), plus a genuinely new primitive for the `**Attendees:**
  [[P1]], [[P2]], ...]` body line: unlike the single-target
  `insert_body_line_if_missing` reused as-is for the `**Customer:**
  [[Hub]]`/`**Sender:** [[Person]]` lines (a line is either present or
  not), the Attendees line can legitimately grow across reruns as new
  attendees are confirmed — the actual per-attendee-wikilink upsert
  mechanics are left to the decomposer/coder, generalizing the existing
  "insert this line if this key/value is absent" philosophy rather than
  introducing a new one.
- Known risk, honestly flagged rather than silently assumed: Outlook's
  documented behaviour for `EntryID` stability across
  `IncludeRecurrences = True` occurrence expansion is not something either
  this codebase or agentic-map's has had to stress-test against a
  real recurring series yet. If a future live run shows two distinct
  occurrences sharing an `EntryID` (an EntryID collision, not just a
  same-subject/same-date collision the filename suffix already guards
  against), that is grounds for a superseding ADR introducing
  `GlobalAppointmentID`-based disambiguation — not a silent workaround.
- REQ-SB-09 (To-Do Task Capture Pipeline, not yet specced) inherits the
  same "add a call inside `run_capture_and_record_completion`" pattern
  this ADR establishes as the second precedent (after email) for plugging
  a new capture pipeline into the shared hourly job, unless a third
  pipeline makes extracting a dedicated orchestration module (see
  Alternatives Considered) the better call by then.

---

## ADR-010: Frontend application architecture — routing, styling, data-fetching, and Agents Map component structure

**Status:** Accepted
**Date:** 2026-08-11
**Context:** `REQ-SB-12-US-01` (`Implementation/UserStories/REQ-SB-12-US-01-
app-shell-agents-map-and-settings.md`) is the first real page built on
`src/frontend`'s `create-vite` scaffold (React 19.2 + Vite 8.2 + TypeScript;
`package.json` currently lists only `react`/`react-dom` — no router, no
styling system, no data-fetching library). It needs a persistent
collapsible-sidebar shell navigating between an Agents Map (default/home),
My Day, and Settings, and a real React reproduction of the approved
`html-prototype/agents-map.html`'s polar-grid visualization (a radar
background, 3 concentric agent-type rings — Worker outermost, Expert
middle, Producer innermost — 3 section Hubs on an inner band, ring-placed
agent nodes, and a central Knowledge Base "brain" element), plus a reachable
placeholder Settings page (`html-prototype/settings.html`). The story's own
Constraints/Context explicitly defer two things: real backend wiring (no
"list configured agents" endpoint exists in `src/backend` yet — this story
renders the prototype's own 5-agent example as static/mocked data) and the
agent-detail chat panel (`REQ-SB-13-US-01`, which will attach a click
handler to the agent nodes rendered here). Four structural questions had to
be settled before the decomposer could write coder tasks, none previously
decided since this is the first frontend code beyond the bare scaffold: how
page navigation works, how styling is authored/scoped, how the frontend will
eventually call FastAPI endpoints, and how the Agents Map's bespoke visual
decomposes into components.
**Decision:**
1. **Routing: `react-router`** (v7.x, the current unified package —
   supersedes the now-legacy `react-router-dom` split), added via
   `npm install react-router`, used in its declarative mode
   (`<BrowserRouter>`, `<Routes>`, `<Route>`, `<NavLink>`) — not the
   data-router/loader API, since no task in this story needs route-level
   data loading yet. `src/frontend/src/App.tsx` wraps the app in
   `<BrowserRouter>` with three routes: `/` (Agents Map, the default/home
   page — Scenario 1), `/my-day`, `/settings`. The sidebar's nav items are
   `<NavLink>`s; `<NavLink>`'s built-in `isActive` state drives the active
   nav-item styling (Scenario 6) instead of hand-rolled path comparison.
2. **Data-fetching: no library, native `fetch` behind a thin client,
   reserved for a future story.** This story ships a local, typed mock
   data module, `src/frontend/src/features/agents-map/mockAgents.ts`,
   mirroring the prototype's exact 5-agent populated state and its
   first-run/empty state — no HTTP call is made by this story at all, per
   its own Non-Goals/Context framing ("UI shell + static/mocked agent
   data... not real backend wiring"). The convention this ADR settles for
   whenever a later story does wire a real endpoint: a thin
   `src/frontend/src/api/client.ts` wrapping native `fetch` (a Vite env var
   for the base URL, JSON in/out, one shared error-handling shape) — no
   data-fetching library. That future story still owns designing the
   actual REST route/payload shape itself; this ADR settles only the
   calling convention, not the endpoint contract.
3. **Styling: reuse the prototype's plain global CSS, not a component
   styling system.** `html-prototype/styles.css` is ported near-verbatim
   into `src/frontend/src/styles/`, split by concern for readability
   (`tokens.css` — the `:root` custom-property tokens; `shell.css` —
   `.app-shell`/`.sidebar`/nav/burger-menu; `agents-map.css` — KB/hub/
   agent-node/ring/radar classes; `settings.css` plus shared `.card`/
   `.badge`/`.btn`/`.input`/`.kv-list` primitives), imported once
   application-wide. Class names are kept identical to the prototype's
   (`.agent-node--worker`, `.hub-node`, `.kb-node`, ...) so components
   reference exactly the classes the approved design already validated,
   with no renaming/translation step.
4. **Component structure for the Agents Map, grounded in the prototype's
   actual markup, not invented:**
   - `AgentsMapCanvas` owns the one connected SVG background layer (radar
     spokes, ring circles, boundary circle, section-boundary guide lines,
     Hub→KB spoke-lines, Hub→agent cluster-lines, ring-label text) plus
     positions its `KnowledgeBaseNode`, `SectionHub`, and `AgentNode`
     children — mirroring the prototype's single `<svg class="agents-map-
     lines">` that already draws all of these together, since they are one
     interdependent coordinate system (a cluster-line's endpoints depend on
     both its Hub's and its agent's computed position).
   - `KnowledgeBaseNode` (the central KB + its brain SVG), `SectionHub`
     (one per section — Capture/People/Q&A this pass, non-clickable), and
     `AgentNode` (one per configured agent; rendering only — the
     click-to-open-detail-panel behaviour is `REQ-SB-13-US-01`'s scope, not
     built here) are separate components, matching the prototype's own
     `.kb-node` / `.hub-node` / `.agent-node` class families.
   - A pure geometry function, `polarLayout.ts` (ring radius + section
     angular midpoint → `{x, y}` on the shared 0–100 viewBox, grounded in
     the prototype's own round-6 values — Producer r=30, Expert r=45,
     Worker r=50, Hub band r=32, boundary r=58, KB edge ~r=17), replaces
     the prototype's hand-derived per-node percentage coordinates (its own
     revision comments document ~6 rounds of manually re-deriving every
     node/line coordinate by hand) with one shared, reusable computation.
**Alternatives Considered:**
- *Routing:* no router, conditional rendering keyed off local component
  state — rejected: Scenario 5 requires real page-to-page navigation with
  the sidebar persisting across pages, which a shareable/back-button-aware
  URL per page (the ordinary expectation for a multi-page shell) serves
  better than hand-rolled state, and loses `<NavLink>`'s free active-item
  detection. TanStack Router — rejected: newer, smaller ecosystem, and a
  steeper type-generation learning curve for a single-developer project
  with no requirement yet for its type-safe-params selling point;
  react-router is the established Vite+React default with zero setup
  friction. Migrating off Vite to Next.js/Remix for file-based routing —
  rejected outright: `src/frontend` is an already-scaffolded Vite SPA
  (ADR-002); replacing the framework is a disproportionate, unrequested
  change with no requirement driving it.
- *Data-fetching:* adding React Query/SWR now, ahead of any real endpoint —
  rejected: no concrete caching/mutation/polling need exists yet (this
  story's data is a static mock); adding either now would be exactly the
  speculative-dependency pattern this project's own precedent avoids
  (ADR-002, ADR-007). Axios instead of native `fetch` — rejected: `fetch`
  is available in every target browser and Vite's toolchain with no
  additional dependency; nothing in this story or its foreseeable
  follow-ons (simple JSON calls against this project's own FastAPI
  backend) needs Axios's interceptor/cancellation surface. Building the
  real "list configured agents" endpoint and wiring it live in this pass —
  rejected per the story's own Non-Goals/Context framing and its
  Constraints (the route/payload shape is explicitly left open, not this
  pass's job to build) — doing so now would be scope creep past this
  story's own boundary.
- *Styling:* CSS Modules (Vite-native, no new dependency) — rejected for
  this pass specifically: it would require translating every prototype
  class reference into per-component scoped imports
  (`styles['agent-node--worker']`) with no scoping benefit at this app's
  actual size (3–4 screens, already-collision-safe BEM-ish prototype class
  names) — pure translation risk against a pixel-approved, bespoke visual
  (the polar grid/KB brain SVG) with no offsetting gain. Revisit once the
  app has enough independent component authors/screens that global-
  namespace collisions become a real, not hypothetical, risk. Tailwind CSS
  — rejected: adds a utility-class dependency/build step and a full
  re-authoring of every prototype style (absolute-percentage positioning,
  bespoke radial/SVG visuals, custom animation keyframes) into utility
  classes, none of which Tailwind meaningfully simplifies here; the
  prototype is already a complete, approved design system in plain CSS.
  styled-components/Emotion (CSS-in-JS) — rejected: a runtime dependency
  and a new authoring syntax for zero net benefit over reusing the
  already-approved CSS as-is.
- *Component structure:* one monolithic page component with all markup
  inline — rejected: the prototype's own markup already separates KB/Hub/
  Agent-node concerns visually and by CSS class family; a single giant
  component would diverge from the prototype's own conceptual seams and
  get harder to reason about as agent count grows. One component per
  agent-type ring (`WorkerRing`/`ExpertRing`/`ProducerRing`) — rejected: a
  ring is a purely radial/visual grouping derived from an agent's `type`
  field, not an independent data or behaviour boundary the prototype's
  markup actually has (agents are placed individually by section+type, not
  iterated per ring). Hardcoding each node's `top`/`left` as literal
  percentages copied straight from the prototype — rejected: the
  prototype's own revision history shows every visual rebalance required
  manually re-deriving every node/line coordinate by hand across multiple
  rounds; a shared pure layout function turns that into one tested
  computation instead of hand-maintained magic numbers scattered across
  JSX — a direct, low-risk improvement grounded in the actual pain the
  prototype's own comments document, not a speculative refactor.
**Consequences:**
- New dependency: `react-router` (added to `src/frontend/package.json`).
  No other new frontend dependency results from this ADR.
- `src/frontend/src` gains: `pages/` (`AgentsMapPage.tsx`,
  `MyDayPage.tsx`, `SettingsPage.tsx`), `components/shell/`
  (`AppShell.tsx`, `Sidebar.tsx`), `features/agents-map/`
  (`AgentsMapCanvas.tsx`, `KnowledgeBaseNode.tsx`, `SectionHub.tsx`,
  `AgentNode.tsx`, `polarLayout.ts`, `mockAgents.ts`), `api/client.ts`,
  and `styles/` (`tokens.css`, `shell.css`, `agents-map.css`,
  `settings.css`) — see `architecture.md`'s new "Frontend Application
  Architecture" section for the full tree.
- `REQ-SB-12-US-02` (My Day) inherits `pages/`/`components/shell/` rather
  than re-deciding shell structure — its pages live in the same `pages/`
  folder, reusing `AppShell`/`Sidebar` as-is. `REQ-SB-13-US-01` (agent chat
  panel) is expected to extend `AgentNode.tsx`'s click handling and, if it
  needs a real backend call, use `api/client.ts`'s convention.
- No `src/backend` change results from this ADR — it governs `src/frontend`
  only. A future story that builds the real "list configured agents"
  endpoint still owns choosing its exact REST route/payload shape and
  replacing `mockAgents.ts` with a real `api/client.ts` call; neither is
  decided here.

---

## ADR-011: Agent chat action-triggering — static keyword-matched action registry, not an NLU/LLM pipeline; unified history via a new `.second-brain/` JSON file

**Status:** Accepted
**Date:** 2026-08-11
**Context:** `REQ-SB-13-US-01` (`Implementation/UserStories/REQ-SB-13-US-01-
embedded-agent-chat-and-communication-history.md`) resolved, operator-
confirmed, that the embedded agent chat can trigger backend actions via
natural language, and that "communication history" is one unified
chronological timeline merging chat messages and background run events.
Neither mechanism exists anywhere in this project yet: no LLM-based
intent-routing/NLU has been built anywhere in Second Brain's own stack
(`ADR-007` explicitly keeps multi-step/agent-orchestration capability out
of this project's own stack, delegated to Hermes), and no per-agent
structured settings/actions/chat/history endpoint exists (`ADR-010`'s
`mockAgents.ts` is agent node/visualization data only — id/type/label for
drawing the polar-grid map — not settings/actions/chat/history data).
Three concrete mechanism questions needed settling before the decomposer
could write tasks: (1) how does "chat message → triggered backend action"
actually work, given no NLU exists anywhere in this project; (2) is the
known-agent-and-its-actions set vault-derived, per this project's standing
"derive from the vault, don't hardcode" pattern (`MEMORY.md`), or a static
configuration; (3) where does the merged chat+run-event history persist,
given this project has no database anywhere in its stack.
**Decision:**
1. **Action-triggering: exact-phrase/keyword substring matching against a
   small, per-agent-declared set of trigger phrases — not an NLU/LLM
   pipeline.** `app/business/agent_registry.py` declares each action's
   `trigger_phrases` (e.g. `run_capture_now:
   ["run capture", "run capture now", "capture now"]`);
   `app/business/agent_chat.py::handle_chat_message` lowercases the
   incoming message and checks it for a substring match against any
   declared phrase, in registry-declared order, first match wins.
   Proportionate to what actually exists in this project today — no
   LLM-backed intent classifier has been built anywhere in Second Brain's
   own stack (`ADR-007` keeps that class of capability out of scope, on
   Hermes's side of the integration boundary), and the entire initial
   action surface is exactly one real, callable action (`email-capture`'s
   `run_capture_now`) — building real NLU for a one-action universe would
   be pure speculative machinery this project's own discipline discourages.
2. **The known-agent-and-actions registry is a small, static, hardcoded
   Python dict (`app/business/agent_registry.py`), not vault-derived.**
   This deliberately does not extend `MEMORY.md`'s "derive from the
   vault, never hardcode" pattern (`list_known_customers`/
   `list_known_kinds`): that pattern protects against hardcoding
   genuinely open-ended vault *content* enumerations that grow as real
   captured data arrives. Which agents/pipelines Second Brain has is
   app/deployment configuration — a small, currently-fixed set matching
   this project's own PRD requirements (REQ-SB-07/08/09/10/03), the same
   category of static deployment fact as `ADR-008`'s
   `Settings.self_email` (not vault content) — not something a future
   capture run could organically add a new value to the way a new
   customer or kind can.
3. **Only actions backed by an already-`Done`, real pipeline get a real
   handler.** `email-capture`'s `run_capture_now` maps to
   `email_classification.run_capture_and_record_completion` (already
   exists, already scheduler-wired per `ADR-005`/`ADR-008`). Every other
   declared action (Meeting/To-Do Capture's "Run capture now", People
   Notes' "Rebuild a person note", Vault Q&A's actions) has no handler
   this pass — invoking one, by button or chat, returns an honest "not
   yet available" response rather than a fabricated success. This story
   does not invent functionality for REQ-SB-08/09/03's own not-yet-built
   pipelines.
4. **Communication history: one new `.second-brain/
   agent_communication_history.json`**, extending the existing flat-
   JSON-file state convention (`processed_email_ids.json`,
   `conversation_index.json`, `last_capture_run.json`) to a fourth
   concern, keyed by `agent_id` → chronological list of `{"kind":
   "chat_user" | "chat_agent" | "run_event", "text", "timestamp"}`
   entries. `email_classification.run_capture_and_record_completion`
   gains one additional call appending a `run_event` entry, alongside its
   existing `record_capture_run_completed()` call, so every trigger
   source (scheduler, app-start, `/poc/classify-emails`, this story's new
   action/chat triggers) produces the same history entry through the one
   shared entry point.
**Alternatives Considered:**
- A real LLM-backed intent-routing call (e.g. asking Compass to classify
  "which action, if any, does this message request") — rejected for this
  pass: disproportionate to a one-real-action universe, adds a new
  Compass call pattern and a new failure mode (misclassification,
  latency, cost) this story's own resolution never asked for ("can
  trigger actions," not "must understand arbitrary phrasing"), and edges
  toward the general orchestration/NLU capability `ADR-007` already
  scoped out of this project's own stack. Revisit once the real action
  set is large/varied enough that keyword matching starts producing wrong
  or missed matches in practice — that is a concrete trigger for a
  superseding ADR, not a hypothetical one.
- Vault-deriving the agent/action registry (e.g. scanning some new
  `Work/Agents/` note-per-agent convention) — rejected: agents are not
  user-authored vault content the way Customers/Kinds/Partners are;
  inventing a vault-note-per-agent scheme to satisfy a pattern meant for
  open-ended vault content would be solving a problem that doesn't exist
  here, and would need its own schema/ADR of its own with no requirement
  calling for it.
- A new SQLite/database table for communication history — rejected: this
  project has no database anywhere in its stack yet (`ADR-005`'s own
  rejection of a persistent job store for the same "no new storage tech
  without a concrete need" reasoning); a flat JSON file matches every
  other piece of `.second-brain/` state exactly, keeps the
  single-user/local-first shape this project has used throughout, and the
  data volume (one user's own chat/run history) has no scale
  characteristic that would justify a database.
- Per-agent history files (`.second-brain/agent_history/<agent_id>.json`)
  instead of one combined file — considered, since it mirrors
  `processed_meeting_ids.json` being a sibling file to
  `processed_email_ids.json` rather than one shared file; rejected in
  favour of one combined file keyed by `agent_id`, since the existing
  convention is "one file per *concern*" (all processed-email IDs
  together, all conversations together) and "communication history" is
  one concern spanning every agent, not a concern that's naturally
  partitioned by agent the way dedup-ID sets are.
- Wiring the "run capture now" action to call `email_classification.
  classify_recent_emails` directly instead of
  `run_capture_and_record_completion` — rejected: would skip the
  existing `record_capture_run_completed()` last-run-record update that
  every other trigger source already performs, producing an inconsistent
  last-run record depending on which surface triggered the run.
**Consequences:**
- `app/business/agent_registry.py`'s hardcoded action set becomes stale
  the moment REQ-SB-08/09/03 actually ship real, callable pipelines —
  each of those stories' own `/plan-tasks` pass should add a real handler
  entry here (per point 3, this is expected, additive work, not a
  rewrite).
- `app/data_access/vault_writer.py` gains a fourth `.second-brain/` state
  file; must not collide with the existing three
  (`processed_email_ids.json`, `conversation_index.json`,
  `last_capture_run.json`, and REQ-SB-08's planned
  `processed_meeting_ids.json`).
- `email_classification.run_capture_and_record_completion`'s one new call
  is the only change to already-`Done` REQ-SB-07/REQ-SB-14/REQ-SB-10 code
  this story makes — everything else in this ADR is new files.
- If a future story needs genuinely free-form agent conversation (not
  just action-triggering) — e.g. "what emails came in today" answered
  from real vault content — that is new scope requiring its own
  requirement and very likely a superseding ADR (a real read/query
  surface over vault content is a different, larger decision than this
  ADR's simple keyword-matched action-triggering); not assumed or
  pre-built here.

---

## ADR-012: Customer→Partner migration scan gains a second match signal — inline `**Customer:** [[name]]` body wikilink, unioned with the existing frontmatter-equality signal (extends ADR-009 point 4)

**Status:** Accepted
**Date:** 2026-08-11
**Context:** `ADR-009` point 4 designed `partner_hub_linking.
migrate_customer_to_partner`'s retag pass as a generic vault-wide scan
matching every note whose `customer` frontmatter equals the given
`customer_name`. `REQ-SB-16-US-01-T04`'s coder ran the required
pre-migration sanity check against the real vault (before calling the
mutating endpoint, as instructed) and found this match predicate is
factually incomplete: the 5 real Microsoft Person notes the story's own
Context and locked `AC-06` explicitly name (`Work/People/{amraze,
karimlouis, lumazohlof, m365copilotupdates, maccount}@microsoft.com.md`)
carry **no** `customer` frontmatter field and **no** `customer/microsoft`
tag at all — `REQ-SB-10`'s Person-note schema
(`people_extraction.build_person_tags`) never gave Person notes a
`customer:` field; they only ever get a `company/<slug>` tag plus an
inline `**Customer:** [[CompanyName]]` body wikilink, written separately
by `customer_hub_linking.link_note_to_customer_hub` when the company was
classified as a Customer. Because `ADR-009`'s scan gates strictly on
`frontmatter.get("customer") == customer_name`, it structurally can never
reach these 5 notes — running the migration as originally specified would
correctly retag the 8 notes that do carry `customer` frontmatter (1 hub +
2 Email + 1 Newsletter + 4 Notification) but permanently leave these 5
Person notes' inline wikilink reading `**Customer:** [[Microsoft]]` for a
company no longer classified as a Customer — stale, internally
inconsistent data, exactly the "stranded data" outcome the migration
exists to prevent (locked `AC-06`). This is a data-*shape* gap (an entire
referencing pattern the match predicate can't see), not the quantity-only
Newsletter/Notification undercount `ADR-009`'s own Context already
resolved. The mutating endpoint was **not** called against the real vault
pending this decision (`ESCALATIONS.md` → `ESC-001`; real
`Work/Customers/Microsoft.md` and every `customer/microsoft`-tagged note
were left untouched). Operator decision, 2026-08-11: extend the scan to
also catch these notes, via a second signal matching the inline wikilink
itself, rather than accepting `AC-06` as satisfied only for
frontmatter-bearing notes.
**Decision:**
1. `migrate_customer_to_partner`'s per-note match condition becomes a
   **union of two signals, evaluated inside the same existing single
   vault-wide scan** (`list_all_note_paths()`/`read_note()` — unchanged
   from `ADR-009` point 4), not a second, separate full-vault iteration:
   - **Signal A (unchanged, `ADR-009` point 4):**
     `frontmatter.get("customer") == customer_name`.
   - **Signal B (new):** the note's body contains the exact line
     `**Customer:** [[<hub note filename stem>]]` (the same
     `old_body_line` value the scan already computes once, up front, for
     its existing `replace_body_line` call), regardless of whether
     `customer` frontmatter is present at all.
   A note is processed if Signal A **or** Signal B is true. Concretely,
   the existing loop's guard clause:
   ```python
   frontmatter, _ = vault_writer.read_note(path)
   if frontmatter.get("customer") != customer_name:
       continue
   ```
   becomes:
   ```python
   frontmatter, body = vault_writer.read_note(path)
   matches_frontmatter = frontmatter.get("customer") == customer_name
   matches_body_wikilink = old_body_line in body
   if not (matches_frontmatter or matches_body_wikilink):
       continue
   ```
   Both signals are read from the **same** `read_note(path)` call the loop
   already makes once per note — zero additional vault I/O over the
   current implementation; this is purely a broadened `if` condition, not
   a new scan mechanism.
2. **No double-processing.** Each note path from `list_all_note_paths()`
   is still visited exactly once per scan iteration (unchanged from
   `ADR-009`); a note matching both signals (e.g. an Email note that
   happens to carry both the frontmatter field and the inline wikilink)
   is still only ever appended once to `notes_retagged`, since the union
   check gates entry into the per-note body of the loop, not a per-signal
   branch. There is no scenario in which a single note is processed
   twice.
3. **No new `vault_writer.py` primitives.** Every retag primitive the
   loop body already calls (`rename_frontmatter_key`,
   `remove_frontmatter_key_if_present`, `swap_tag` ×2,
   `replace_body_line`) is already no-op-if-absent (`ADR-009` point 5),
   so for a note matched only by Signal B (e.g. a Person note with no
   `customer` frontmatter or tag at all) the frontmatter-only primitives
   simply no-op (return `False`, no write) and only `replace_body_line`
   fires — changing exactly the inline label, nothing else. This is a
   pure match-predicate broadening over the existing, already-idempotent
   primitive set; idempotency on rerun is preserved by construction for
   the same reason `ADR-009` point 5 already established it (a note fully
   migrated no longer matches Signal A *or* Signal B, so the very first
   `if` already excludes it).
4. **`REQ-SB-16-US-01-AC-06`'s locked wording is unchanged.** The AC
   already asked for "every note the generic scan finds" to have its
   frontmatter key, tag, and — where present — body-line label retagged;
   this ADR only corrects the scan's *matching* logic so it actually
   finds the 5 Person notes AC-06 already named. No AC re-wording, no new
   AC.
**Alternatives Considered:**
- A genuinely separate second `for path in list_all_note_paths(): ...`
  loop dedicated to Signal B only, run after the existing loop —
  rejected: doubles vault I/O (every note's file read twice) for no
  benefit, since Signal A and Signal B are both derivable from the exact
  same `read_note()` return value the existing loop already captures per
  iteration; a genuinely separate second loop would also reintroduce the
  double-processing risk this ADR's point 2 explicitly avoids (a
  both-signals note would need explicit cross-loop dedup bookkeeping,
  whereas a single unioned condition inside one loop makes
  double-processing structurally impossible).
- Match Signal B on `company/<slug>` tag presence (alone, or ANDed with
  the inline wikilink) instead of the inline wikilink alone — as the
  `REVIEW-QUEUE.md` entry's own first-draft phrasing suggested — rejected:
  `company/<slug>` is every Person note's own always-present company tag,
  unrelated to Customer/Partner status (every Person note has one,
  Customer-linked or not), so requiring it would arbitrarily exclude any
  *other* note kind that might, in some future capture path, carry the
  inline `**Customer:**` wikilink without ever having a `company` tag at
  all (e.g. a hand-authored note). The inline wikilink itself is the
  actually-stale artefact `AC-06` cares about relabeling, so matching on
  its literal presence is the precise, minimal, note-kind-agnostic
  signal — consistent with `ADR-009`'s own "generic, vault-wide, not
  hardcoded to a note kind" reasoning, just applied to the new signal too.
- Hardcode the 5 known Person-note paths as a targeted, one-off patch —
  rejected for the exact reason `ADR-009` already rejected a hardcoded
  list for the original migration design: it would go stale the moment
  vault content changes again (e.g. a 6th Microsoft Person note captured
  tomorrow) and contradicts this project's standing vault-derived-not-
  hardcoded pattern (`MEMORY.md`).
- Accept `AC-06` as satisfied only for frontmatter-bearing notes and file
  the 5 Person notes' relabeling as separate follow-up scope (the
  `REVIEW-QUEUE.md` entry's other named option) — rejected by explicit
  operator decision, 2026-08-11: the story's own Context frames a stale
  post-migration label as exactly the failure mode this migration exists
  to prevent, and the actual fix is small and mechanical (broadening one
  `if` condition against data already available in the loop), not
  disproportionate follow-up-worthy scope.
**Consequences:**
- `partner_hub_linking.migrate_customer_to_partner`'s per-note match
  condition changes from a single frontmatter-equality check to the
  two-signal union in Decision point 1 above — no new function
  signatures, no change to the function's own docstring-documented return
  shape (`{"hub_note_moved", "hub_note_path", "notes_retagged"}`), no new
  `vault_writer.py` primitives.
- `architecture.md`'s "Partner Hub Notes & Mutually-Exclusive Company
  Taxonomy (REQ-SB-16)" → "Generic retag pass" bullet is updated (this
  same pass) to describe the unioned two-signal match condition,
  referencing this ADR alongside `ADR-009`.
- `REQ-SB-16-US-01-T04`'s task spec is corrected to reflect the new match
  predicate; its `## Acceptance Criteria` checklist and the story's locked
  `AC-06` wording are unchanged — only the implementation's matching
  logic changes, per Decision point 4.
- **`ADR-009` itself remains `Accepted` and is not edited.** Its points 1
  (tag-not-folder pattern), 2 (parallel sibling module), 3 (new
  `vault_writer.py` baseline primitives), and 5 (the three generic
  rename/swap/replace primitives) are entirely unaffected by this change;
  only point 4's specific match *predicate* is extended by this ADR.
  Future readers should read `ADR-009` point 4 together with this ADR,
  not point 4 alone, for the migration's current, correct matching
  behaviour.
- A third match signal (e.g. a `company/<slug>` tag alone, with no inline
  wikilink present) is explicitly **not** added here — if a future note
  shape needs Partner-migration coverage without ever having carried the
  inline `**Customer:**` wikilink, that is new scope requiring its own
  review, not assumed to already be covered by this ADR.
- Resolves `ESCALATIONS.md` → `ESC-001` and clears the corresponding
  `REVIEW-QUEUE.md` entry for `REQ-SB-16-US-01-T04`; `T04`'s `status:`
  resets from `Blocked` to `Ready` for `/implement-sprint` to resume
  against the real, still-untouched Microsoft vault data.

## ADR-013: Meetings occurrence dedup key — `GlobalAppointmentID` (full-string hash) replaces `EntryID` for filename/dedup disambiguation, with a legacy-`EntryID`-path backward-compatibility check (supersedes ADR-008 point 2)

**Status:** Superseded by ADR-019
**Superseded note (2026-08-12, append-only — the body below is otherwise
unchanged, per this file's own "never edit an Accepted ADR" rule):**
`ADR-019` replaces this ADR's Decision points 1 and 2 — live verification of
the fix this ADR itself specified (`REQ-SB-08-US-01-T06`, `SPRINT-017`)
found `AppointmentItem.GlobalAppointmentID` has the **exact same
non-uniqueness defect** on this Outlook installation that this ADR was
written to fix for `EntryID` (`ESCALATIONS.md` → `ESC-012`) — identical
values across all real occurrences of two separate recurring series, and
the documented `PropertyAccessor`/DASL fallback error on every occurrence.
`ADR-019` stops depending on any Outlook-provided identity field entirely,
using the occurrence's own precise start timestamp (combined with subject)
instead — a structural uniqueness guarantee, not an empirical one. This
ADR's Decision point 3 (the legacy-`EntryID`-path coexistence check, so none
of the 38/39 already-captured real Meeting notes needs migrating) **remains
valid and is reused unmodified by `ADR-019`** — only the *new*-scheme half
of the design (points 1 and 2) is replaced.
**Date:** 2026-08-11
**Context:** `ADR-008` point 2 chose Outlook `EntryID` as the per-occurrence
dedup key for calendar events expanded by `items.IncludeRecurrences = True`,
explicitly on the assumption that "every expanded occurrence returned by
`IncludeRecurrences = True` is treated as a plain item with its own
`EntryID`" — while its own Consequences section honestly flagged this as
*unverified* against a real recurring series, and pre-authorized "a
superseding ADR, not a silent workaround" as the required response if a
live collision were ever observed (`ADR-008`'s Alternatives Considered
already discussed and rejected `GlobalAppointmentID` for that first pass,
for the same reason). `REQ-SB-08-US-01-T03`/`T05`'s live verification
(Scenario 9 / `AC-09`) found exactly that: a real recurring meeting
("Weekly Forecast l Strategic Clients," 3 occurrences on 2026-08-10/17/24)
returns the **exact same full `EntryID` string** for all 3 distinct
occurrences — not a coincidental suffix match, the entire ID is identical.
Full detail: `ESCALATIONS.md` → `ESC-002`. Today's 38 real Meeting notes
are all still correct only because `meeting_note_filename_stem` also
incorporates the event's date and these 3 real occurrences happen to fall
on different dates — a future recurring meeting with two occurrences on
the **same** date (a twice-daily recurring meeting, or a rescheduled
occurrence landing on another occurrence's date) would produce an
identical filename for both, and `meeting_note_exists()`'s
create-vs-top-up branch would silently merge two distinct meetings into
one note. **Operator decision, 2026-08-11: fix this now**, per `ADR-008`'s
own pre-authorized path (a superseding ADR adopting `GlobalAppointmentID`)
rather than leave it as an accepted known limitation. `REQ-SB-08-US-01`
itself stays `Done` and is not reopened — every one of its 11 locked ACs
passed against real, live data available at the time, and none of that
verified behavior is invalidated by this ADR; this is a forward-looking
hardening fix for a not-yet-triggered edge case, tracked as a new,
additive task (`REQ-SB-08-US-01-T06`) under the same story, per hard rule
1's "completed... stories are frozen" (no story ACs are reworded here).
**Decision:**
1. **`AppointmentItem.GlobalAppointmentID` (Outlook's own documented,
   guaranteed-unique-per-occurrence identifier) becomes the occurrence
   dedup/filename key, replacing `EntryID` for that purpose.**
   `GlobalAppointmentID` is a native COM property on `AppointmentItem`
   (`item.GlobalAppointmentID`), read the same direct way `item.EntryID`
   already is — no new library, no new mechanism class. As a defense-in-
   depth fallback (mirroring a technique already present in this exact
   file — `_is_inline_attachment`'s `PropertyAccessor.GetProperty` call
   against a MAPI proptag), a new `_resolve_global_appointment_id(item)`
   helper in `app/data_access/outlook_com.py` tries the native property
   first, then falls back to `item.PropertyAccessor.GetProperty(
   "http://schemas.microsoft.com/mapi/id/{6ED8DA90-450B-101B-98DA-
   00AA003F1305}/00030102")` — the documented Extended MAPI DASL tag for
   this exact property (`PidLidGlobalObjectId`) — if the native property
   read raises. If **both** fail, the event is skipped entirely (the
   existing best-effort per-item `try/except: continue` category
   `list_calendar_events` already uses for any malformed/unreadable item)
   — **no fallback to `EntryID` as a substitute dedup key.** Silently
   degrading back to a known-non-unique identifier for the rare
   resolution-failure case would reintroduce exactly the bug this ADR
   exists to close; skipping is the safe choice, and it is self-healing —
   an in-window event that fails resolution on one hourly run remains in
   the rolling sync window and is retried on the next.
2. **Filename/dedup suffix: an 8-hex-character prefix of
   `hashlib.sha256(global_appointment_id.encode("utf-8")).hexdigest()`,
   not a raw substring slice.** `GlobalAppointmentID`'s internal structure
   (Extended MAPI `PidLidGlobalObjectId` / `MS-OXOCAL`'s `GlobalObjectId`
   format) encodes the specific occurrence's original date near the
   **front** of the byte sequence, with a long, series-constant trailing
   component inherited from the master series — meaning naively porting
   this codebase's existing "slice the last 8 characters" convention
   (safe for `EntryID` in this project's own prior usage, but never
   actually guaranteed by Outlook's documentation for *any* identifier)
   risks slicing exactly the part of the value that does **not** vary
   per-occurrence, silently reproducing the identical class of defect
   `ESC-002` just found — just moved to a new field. Hashing the
   **complete** string sidesteps this: any difference anywhere in the
   full `GlobalAppointmentID` (including the date-encoding bytes nearer
   the front) changes the hash, so the resulting 8-hex-char suffix is a
   true per-occurrence disambiguator, not a location-dependent gamble.
   8 hex characters (32 bits, ~4.3 billion values) is ample margin for any
   single-user personal calendar's realistic occurrence volume — matches
   the existing filename convention's visual shape (`<subject>-<date>-
   <8-char-suffix>.md`), so already-familiar notes in Obsidian look the
   same going forward.
3. **No migration/rename of the 38 already-captured Meeting notes or their
   `processed_meeting_ids.json` entries — the new scheme applies only to
   newly-captured occurrences going forward, made safe by a
   backward-compatibility existence check (not a data migration).** The
   38 existing notes carry no stored calendar-identifier of any kind in
   their frontmatter (`type`, `customer`, `subject`, `start`, `end`,
   `location`, `organizer`, `tags` only — no `id`/`entry_id`/
   `global_appointment_id` field), so migrating them would require
   re-deriving each one's `GlobalAppointmentID` via a fresh, wide-window
   live COM query and fuzzy-matching it back to an existing file by
   subject+date — real risk of mismatch, and a live-vault-mutating batch
   rename of real, possibly hand-edited notes for **zero present
   benefit** (none of the 38 collide today; `ESC-002` is a prospective
   risk, not an active failure). Instead, `vault_writer.py` gains a
   single resolution function (replacing the orchestrator's current
   two-call `meeting_note_path()` / `meeting_note_exists()` pattern) that
   checks the **new** `GlobalAppointmentID`-hash path first, and — only if
   not found there — a **legacy** `EntryID`-suffix path (the exact
   pre-this-ADR filename scheme) as a fallback; whichever path is actually
   found on disk is what gets topped up, and only if neither is found is a
   new note created (always under the new scheme). This is what prevents
   the regression a naive "just switch the filename scheme forward" fix
   would otherwise cause: without this check, the next capture run after
   this fix ships would recompute a **different** filename (new suffix)
   for every still-in-window event that already has an old-style note,
   find no file at that new path, and create a **duplicate** note — the
   exact no-duplicate guarantee (`AC-02`/`AC-07`/`AC-09`) this fix exists
   to protect. `mark_meeting_processed` writes `GlobalAppointmentID`
   values going forward; the file's existing `EntryID` entries are left
   untouched (append-only, heterogeneous, but the file is already
   documented — `mark_meeting_processed`'s own docstring — as an audit
   trail for future observability (`REQ-SB-11`), not a schema-enforced
   lookup structure any code path depends on for uniqueness).
**Alternatives Considered:**
- **Migrate/rename the 38 existing notes and rewrite
  `processed_meeting_ids.json` to the new scheme** — rejected for this
  pass: requires re-deriving each note's `GlobalAppointmentID` via a live,
  wide-window COM query and fuzzy subject+date matching back to a file (no
  identifier is stored in the notes' own frontmatter today), a real risk
  of mismatch against real user data, for zero present benefit (no
  existing collision). The legacy-path fallback check (Decision point 3)
  achieves the same forward-safety without touching any existing file.
  Revisit if a future need (e.g. a full observability/audit rebuild,
  REQ-SB-11) already requires a wide-window recomputation pass for other
  reasons — migrating filenames could then ride along cheaply.
- **Combine `EntryID` and `GlobalAppointmentID` into one composite dedup
  key** (e.g. `f"{entry_id}:{global_appointment_id}"`) — rejected:
  `EntryID` is confirmed non-unique per occurrence for at least one real
  recurring series, so it contributes zero disambiguating value in a
  composite key; combining a reliable identifier with an unreliable one
  adds complexity without adding safety. `EntryID` is kept in
  `list_calendar_events`'s return shape (the `"id"` field) for
  informational/debugging value only, no longer load-bearing.
- **Raw substring slice of `GlobalAppointmentID`** (mirroring the
  existing `EntryID`-slice convention exactly, just swapping the source
  field) — rejected: per Decision point 2's reasoning, `GlobalObjectId`'s
  per-occurrence-varying bytes are not guaranteed to fall within any
  fixed trailing slice; this would risk silently reproducing the exact
  class of bug this ADR exists to fix, just relocated to a new field.
  Full-string hashing is the robust choice.
- **Silently fall back to `EntryID` as the dedup key when
  `GlobalAppointmentID` resolution fails** (native property raises *and*
  the `PropertyAccessor`/DASL fallback also raises) — rejected: this is
  precisely the non-unique identifier `ESC-002` found broken; falling
  back to it for the failure case would silently reintroduce the bug for
  exactly the events most likely to need protection (anything unusual
  enough about the item to make property resolution fail in the first
  place). Skipping the event (existing best-effort per-item category) is
  safer and self-healing across the rolling sync window.
- **Accept the current date-disambiguation-only behavior as a known,
  accepted limitation for a single-user personal tool** (the
  `REVIEW-QUEUE.md` entry's third named option) — rejected by explicit
  operator decision, 2026-08-11: "fix this now," per `ADR-008`'s own
  pre-authorized path.
**Consequences:**
- `app/data_access/outlook_com.py::list_calendar_events` gains a new
  `_resolve_global_appointment_id(item)` helper and a new
  `"global_appointment_id"` field on every returned event dict; the
  existing `"id"` (`EntryID`) field is retained, unchanged, now
  informational/debugging only — no longer load-bearing for dedup or
  filenames.
- `app/data_access/vault_writer.py`'s `meeting_note_filename_stem`,
  `meeting_note_path`, and `create_meeting_note_baseline` are re-parametrized
  to take `global_appointment_id` in place of `entry_id`; a new legacy-path
  helper and a single new resolve-or-create function replace the
  orchestrator's current `meeting_note_path()` + `meeting_note_exists()`
  two-call pattern (exact function shape left to the coder, per this
  project's existing convention of leaving mechanical shape choices to
  implementation). `mark_meeting_processed` is re-parametrized the same
  way.
- `app/business/meeting_classification.py::classify_recent_meetings` reads
  both `event["global_appointment_id"]` and `event["id"]` per event
  (the latter only for the legacy-path fallback check) and threads
  `global_appointment_id` through to note creation and the audit-record
  call.
- **Known, accepted, narrow residual risk — not eliminated by this ADR:**
  the legacy-path fallback check (Decision point 3) protects against
  *duplicating* an already-captured occurrence, but does not fully
  eliminate `ESC-002`'s original merge risk for the specific historical
  intersection of "one of the 38 pre-fix notes' own exact date" **and** "a
  genuinely new, distinct occurrence of that same series lands on that
  exact same date" — in that narrow case, the legacy-path check would
  still find the old note (same subject, same date, same stale `EntryID`
  suffix) and top it up as if it were the same occurrence, since the
  legacy path is computed the same non-unique way `ESC-002` found broken.
  This is a materially smaller, bounded, shrinking-over-time risk (limited
  to the 38 already-known dates, not the general future) compared to
  leaving the pre-fix behavior in place unconditionally — accepted for a
  single-user personal tool, consistent with `ADR-008`'s own precedent of
  naming a real residual risk honestly rather than either silently
  ignoring it or over-engineering a full migration for zero present
  benefit. A future full migration (first Alternative above) would close
  this residual gap entirely, if ever warranted.
- **Locked `AC-07`/`AC-09` wording ("entry-id-suffix") is now a stale
  implementation-detail phrase, not a functional inaccuracy — left
  unedited.** Both ACs' black-box guarantee (each occurrence gets its own,
  non-colliding note) is what this ADR fulfills more robustly; the literal
  phrase "entry-id-suffix" in the already-locked, already-verified Gherkin
  text no longer describes the new-scheme mechanism precisely, but per
  this role's own constraints (architect may not edit ACs) and hard rule 1
  (locked/verified ACs are not rewritten), the wording is left as-is.
  Flagged here for visibility, not acted on.
- Resolves `ESCALATIONS.md` → `ESC-002` at the design level (fix decided,
  not yet built) and the corresponding `REQ-SB-08-US-01` `REVIEW-QUEUE.md`
  entry; `architecture.md`'s "Meeting Notes & Calendar-Attendee
  Extraction (REQ-SB-08)" section is updated (this same pass) to describe
  the new dedup key. `ADR-008` itself remains `Accepted` and is not
  edited — only its point 2 is superseded by this ADR; points 1, 3, and 4
  are entirely unaffected.
- New task `REQ-SB-08-US-01-T06` implements this ADR; `REQ-SB-08-US-01`'s
  own `status:` stays `Done` (unchanged) — this is additive, forward work
  against a frozen story per hard rule 1, not a reopening.

---

## ADR-014: Mutable, user-editable agent Sections & LLM Providers — parallel persisted `.second-brain/` stores, composed at the API layer without modifying `agent_registry.py`, block-until-unused deletion, plaintext local credential storage, and N-section-generic frontend layout

**Status:** Accepted
**Date:** 2026-08-11
**Context:** `REQ-SB-18-US-01` (user-editable agent Sections, decoupled from
agent Type, with per-agent section reassignment) and `REQ-SB-19-US-01`
(global LLM Provider CRUD, with a per-agent Provider picker defaulting to
Compass) were designed together (one `/design` pass) and both land on the
exact same architectural fault line: `app/business/agent_registry.py`'s
`AGENTS` dict is a small, static, hardcoded Python literal — `ADR-011` point
2 chose this deliberately, reasoning that "which agents exist is
app/deployment configuration, not vault content... not something a future
process could organically add to." Both stories now need a *new*, narrower
kind of mutability layered on top of that same registry: not "which agents
exist" (still hardcoded, `ADR-011` unchanged) but "which Section an agent
belongs to" and "which Provider an agent uses" — user-driven, explicit CRUD
via a Settings UI, persisted across restarts. Neither concept exists
anywhere in this codebase today. Six concrete questions needed settling
before the decomposer could write tasks for either story: (1) the
persistence mechanism, and whether `agent_registry.py`'s own shape needs to
change; (2) the API surface for Section CRUD, Provider CRUD, and per-agent
reassignment; (3) where the "block deletion/removal while in use" check
(both stories' own operator-resolved Scenario 4b) lives, and its error
shape; (4) how a Provider's credential is stored and how the API avoids ever
echoing it back in plaintext; (5) how `layoutAgents.ts`'s currently
fixed-3-section, 1:1-with-Type layout becomes genuinely N-section-generic,
per the approved "5 sections" prototype reference state; (6) where the
"selecting a not-yet-built Provider must honestly fail" check (`REQ-SB-19`'s
own Scenario 7, explicitly modelled on `ADR-011` point 3's "declared but
unbuilt action" precedent) actually lives in the request path.
**Decision:**
1. **Two new parallel `.second-brain/` JSON state files, one per concern,
   extending the existing flat-JSON-file convention (`processed_email_ids.
   json`, `conversation_index.json`, `last_capture_run.json`,
   `processed_meeting_ids.json`, `agent_communication_history.json`) to a
   fifth and sixth file — not a database, not a new storage mechanism.**
   - `.second-brain/agent_sections.json`:
     `{"sections": [{"id": str, "name": str}, ...], "assignments":
     {<agent_id>: <section_id>, ...}}`. `id` is a slug
     (`vault_writer.tag_slug(name)`) generated **once, at creation, and
     never regenerated on rename** — renaming a section only ever updates
     its `name` field in place, so every existing `assignments` entry
     pointing at that `id` stays correct automatically (this is what makes
     `REQ-SB-18`'s Scenario 3, "the rename does not change assignment,"
     true by construction, with no extra propagation code needed).
   - `.second-brain/agent_providers.json`:
     `{"providers": [{"id": str, "name": str, "endpoint": str,
     "credential": str, "model": str}, ...], "assignments": {<agent_id>:
     <provider_id>, ...}}`. Same slug-id-stable-across-rename shape.
   - **Seeding is a business-layer decision, not a data-access default.**
     Mirroring `load_processed_email_ids()`'s existing "return an empty
     default when the file doesn't exist" contract, the two new
     `vault_writer.py` primitives (`load_sections_state()` /
     `load_providers_state()`) return `None`/absent-file as-is — pure I/O,
     no business rules, per `ADR-003`. The **non-trivial** default content
     (the starting 5 sections named in the PRD breadcrumb; the pre-seeded
     Compass Provider entry, whose `endpoint`/`credential`/`model` are read
     once from `app.config.settings.compass_base_url` /
     `compass_api_key` / `compass_model` at first read) is a domain
     decision, so it lives in two new business modules,
     `app/business/section_registry.py` and
     `app/business/provider_registry.py`, each seeding-then-persisting on
     first read (calling `vault_writer.save_sections_state()` /
     `save_providers_state()` immediately after computing the default, so
     the seed is written once and every subsequent read is a plain load).
   - **Self-healing default assignment for any agent with no explicit
     entry.** Both business modules resolve `agent_registry.list_agents()`
     for the full known-agent-id set on every read; any agent id present
     there but absent from `assignments` (true for every agent on first
     seed, and for any agent a future story adds to `agent_registry.py`
     without a corresponding migration) is assigned to a fixed default —
     the first section in creation order (`"technical"`, per the PRD
     breadcrumb's starting set) for sections, `"compass"` for providers —
     and the assignment is persisted immediately. This is what keeps
     `GET /agents/{id}` always returning a real section/provider for every
     known agent with zero manual migration step, and is exactly the
     "Compass remains the default Provider for every agent unless the user
     explicitly picks a different one" constraint (`REQ-SB-19`) applied at
     the data layer, not just the UI layer.
2. **`agent_registry.py` itself is not modified — `ADR-011` point 2's
   "identity/type/actions stay hardcoded" reasoning is preserved exactly,
   not reworked.** `AGENTS` gains no `section_id`/`provider_id` field of its
   own. Composition happens one layer up, at the API layer:
   `app/api/agents_router.py`'s `GET /agents` and `GET /agents/{agent_id}`
   handlers call `agent_registry.list_agents()`/`get_agent()` (unchanged)
   *plus* `section_registry.get_agent_section(agent_id)` and
   `provider_registry.get_agent_provider(agent_id)`, merging the results
   into the response dict. This is the same "one business module composing
   another" shape `architecture.md` already documents as an established,
   intentional pattern (`people_extraction.py` → `customer_hub_linking.py`;
   `meeting_classification.py` → `people_extraction.py`), applied once more
   at the router's own composition point — not a new layering precedent.
3. **API surface: two new resource routers, plus one new verb on the
   existing agent resource.**
   - `app/api/sections_router.py`, `APIRouter(prefix="/sections")`:
     `GET /sections` → `[{"id", "name", "agent_ids": [str]}]`;
     `POST /sections` (body `{"name"}`) → creates, returns the created
     section; `PATCH /sections/{section_id}` (body `{"name"}`) → renames in
     place (same `id`, per point 1); `DELETE /sections/{section_id}` →
     deletes, or `409` if `agent_ids` is non-empty (point 4, below).
   - `app/api/providers_router.py`, `APIRouter(prefix="/providers")`:
     `GET /providers` → `[{"id", "name", "endpoint", "model",
     "credential_set": bool, "is_default": bool, "has_real_client": bool,
     "agent_ids": [str]}]` — **never a `credential` field, in any list or
     detail response** (point 5, below); `POST /providers` (body `{"name",
     "endpoint", "credential", "model"}`) → creates; `PATCH /providers/
     {provider_id}` (body: any subset of `{"name", "endpoint",
     "credential", "model"}`) → updates only the supplied fields, an
     omitted/absent `credential` leaves the stored value untouched (point
     5); `DELETE /providers/{provider_id}` → deletes, or `409` if
     `agent_ids` is non-empty.
   - `app/api/agents_router.py` gains `PATCH /agents/{agent_id}` (body: any
     subset of `{"section_id", "provider_id"}`) → validates each supplied
     id actually exists (`404` if not), updates the corresponding
     assignment(s), returns the same merged detail shape `GET /agents/
     {agent_id}` returns. One endpoint handles both `REQ-SB-18`'s
     section-reassignment (Scenario 5) and `REQ-SB-19`'s provider-picker
     (Scenario 5) — the Agent Settings surface's one detail panel is the
     single place both reassignments happen from, per both stories' own
     Context naming the same panel, so one flexible PATCH avoids two
     near-identical endpoints for what is, from the panel's perspective,
     one "update this agent's settings" action.
   - All three new routers registered in `app/main.py` alongside the
     existing four, matching the established `app.include_router(...)`
     pattern exactly.
4. **Block-until-empty/unused enforcement lives in the business layer,
   returning a structured result; the router translates a block into
   `HTTP 409`.** `section_registry.delete_section(section_id)` and
   `provider_registry.remove_provider(provider_id)` each return
   `{"deleted": bool, "blocked_by_agent_ids": [str]}` (mirroring the
   existing `_invoke_action`/`trigger_action` result-dict convention already
   used in `agents_router.py`, rather than raising a Python exception for
   ordinary control flow). When `blocked_by_agent_ids` is non-empty, the
   router raises `HTTPException(status_code=409, detail=<message>)`, where
   `<message>` is composed by resolving each blocking id's display name via
   `agent_registry.get_agent(id)["name"]` — e.g. "Can't delete
   'Productivity' — 3 agents (Email Capture, Meeting Capture, To-Do
   Capture) are still assigned to this section. Move them to a different
   section first, then try again." — matching the approved
   `settings.html` prototype's blocked-state copy verbatim in shape. This
   is the exact same policy, worded identically by the operator, for both
   stories (`REQ-SB-18` Scenario 4b, `REQ-SB-19` Scenario 4b) — one shared
   error-shape convention (`409` + a name-resolved message), not two
   independent implementations.
5. **Credential handling: plaintext at rest (matching this project's
   existing `.env`-sourced `compass_api_key` trust model), never returned
   by any endpoint, in whole or in part.** This is a single-user,
   local-first personal tool — the same trust boundary `compass_api_key`
   already lives inside (an unencrypted value on the user's own disk,
   readable by anything with filesystem access to `.env` or, now,
   `.second-brain/agent_providers.json`). No new encryption-at-rest
   mechanism is introduced; over-engineering one here would protect against
   a threat model (a second party reading this user's own laptop's
   filesystem) no Accepted requirement asks this project to defend against.
   `GET /providers` (list or, once one exists, detail) never includes a
   `credential` field at all — not even a masked/partial value — the
   safest option, and consistent with how Compass's own credential is
   *never* returned by any existing endpoint today either. The approved
   `settings.html` prototype's masked `sk-live-••••••••••••` display value
   is frontend-only decoration (a fixed placeholder shown once a Provider's
   `credential_set` is `true`), not a value the backend ever sends.
   `PATCH /providers/{id}` accepting an omitted `credential` field (rather
   than requiring it on every edit) is what lets a user edit a Provider's
   endpoint/model without being forced to re-paste its credential each
   time, matching the prototype's Edit form pre-filling the masked value
   rather than leaving the credential field blank.
   - **The pre-seeded "Compass" Provider entry is a CRUD-editable
     *representation* only — editing it via Settings does not change the
     actual, live Compass call path this pass.** `REQ-SB-19`'s own
     Non-Goals explicitly forbid "removing or replacing Compass's existing
     `.env`-sourced configuration mechanism," and Scenario 6 requires "an
     agent using Compass continues to work exactly as today — no change in
     behaviour, endpoint, or credential used." Read together, these two
     constraints already answer the question: `app/data_access/
     compass_client.py`'s real HTTP calls continue reading
     `app.config.settings.compass_base_url` / `compass_api_key` /
     `compass_model` directly, entirely unaffected by whatever the
     `agent_providers.json` "Compass" entry's fields currently hold. This
     is a known, explicit, honestly-named limitation for this pass (not a
     silent gap): a user who edits the Compass Provider entry's endpoint or
     credential from Settings will see the edit reflected in the Providers
     list, but the real capture pipeline keeps using `.env`'s values until
     a future story deliberately reconciles the two (out of scope here,
     since building that reconciliation would mean touching the
     `.env`-sourced mechanism this story is explicitly told not to touch).
6. **Frontend: `layoutAgents.ts` becomes genuinely N-section-generic,
   replacing its fixed 3-section `SECTION_META`/`TYPE_TO_SECTION` lookup
   tables.** `layoutAgents(agents, sections)` takes the real `GET /sections`
   list alongside `GET /agents` (previously agents only); section
   membership comes from each agent's own `section_id` (previously derived
   from `type`). Hub angles are computed, not hand-placed: N sections
   (sorted, e.g., by `id`, for a stable render order) are spaced evenly
   around the full circle (`hubAngleDeg(i) = i * (360 / N) + offset`, exact
   `offset` left to the coder as a purely cosmetic starting-rotation choice
   with no functional consequence) — the same "computed, not hardcoded"
   philosophy `ADR-010`'s `polarLayout.ts` already established for
   ring/hub radii, extended to hub *count*. `AgentsMapCanvas.tsx`'s
   `section-boundary` divider lines (currently three hardcoded lines at
   fixed `-90/30/150` degree positions) are replaced by N lines, one at the
   angular midpoint between each pair of adjacent hub angles — the general
   form of the same fixed geometry, not a new visual concept. Per the
   approved prototype's own explanatory note (`agents-map.html`, "5
   sections" reference state), **Hub coloring moves from per-agent-Type
   tinting to one neutral color** (`var(--color-accent)`, already
   `.hub-node`'s CSS fallback) — now that one Section can hold agents of
   any Type (`REQ-SB-18` Scenario 6), a Section no longer has a single Type
   to tint by. `AgentSection`'s `type: AgentType` field (`mockAgents.ts`) is
   dropped as no longer meaningful; `sectionId`/`SectionId` (a 3-value
   union type today) becomes a plain `string` (an arbitrary, user-created
   id). **Ring radius/placement itself is untouched** — an agent's `type`
   still drives which ring (Producer/Expert/Worker) it renders on; this ADR
   only changes which *hub* an agent's cluster-lines connect to and where
   that hub sits, per both stories' explicit Non-Goal against redesigning
   the Type/ring mechanism.
7. **"Not yet available" enforcement for a non-Compass Provider lives at
   the one existing shared funnel point both the direct-action-trigger and
   chat-triggered paths already go through:
   `app/api/agents_router.py::_invoke_action`.** Before its existing
   `_ACTION_HANDLERS.get((agent_id, action_id))` lookup, `_invoke_action`
   resolves the agent's Provider via `provider_registry.get_agent_provider
   (agent_id)` and checks `provider_registry.has_real_client(provider_id)`
   — a small, hardcoded set, `{"compass"}`, mirroring `ADR-011` point 3's
   own "declared but not yet backed by a real handler" pattern one layer up
   (Provider, not action). If the resolved Provider has no real client,
   `_invoke_action` short-circuits with `{"status": "error", "message":
   f"{provider_name} is not available yet — no client has been built for
   it."}`, **without calling the underlying handler at all** — no silent
   fallback to Compass, no fabricated response, satisfying `REQ-SB-19`
   Scenario 7 literally. This is safe and correct for this pass because
   every currently-real handler (there is exactly one,
   `email-capture`'s `run_capture_now`) already is itself LLM-backed (it
   calls Compass via `email_classification.py` → `compass_client.py`), so
   gating the entire `_invoke_action` funnel on Provider availability does
   not block any handler that doesn't actually need one. A future story
   that adds a real action with no LLM dependency at all would need to
   revisit this blanket gate (see Consequences).
**Alternatives Considered:**
- **A single combined `.second-brain/agent_settings.json`** holding both
  Section and Provider assignment (and any future per-agent mutable
  property) in one file — rejected: `ADR-011`'s own precedent for the
  existing `.second-brain/` files is "one file per *concern*," and Section
  and Provider are two independently-CRUD'd, independently-blocked,
  independently-shaped concerns (one has no credential; the other does) —
  combining them would couple their read/write paths for no benefit, and
  would make a future third mutable-property concern (should one arise)
  need to either grow this same file further or break the "one file per
  concern" convention inconsistently either way. Two sibling files matches
  `processed_email_ids.json`/`processed_meeting_ids.json` already being
  two sibling files for a structurally similar reason (same shape, two
  independent entity types).
- **Vault-deriving Sections/Providers** (e.g. a `Work/Sections/` or
  `Work/Providers/` note-per-entity convention, mirroring
  `list_known_customers`) — rejected for the same reason `ADR-011` already
  rejected vault-deriving the agent registry itself: Sections and Providers
  are user-configured application settings, explicitly created/edited via
  a Settings UI form, not content the user authors as vault notes or that
  a capture pipeline organically discovers — inventing a vault-note schema
  to satisfy a pattern meant for open-ended vault *content* would solve a
  problem that doesn't exist here.
- **Extending `agent_registry.py`'s own `AGENTS` dict with mutable
  `section_id`/`provider_id` keys, read/written in place** — rejected: it
  would turn a currently-static, hardcoded Python module-level dict into a
  runtime-mutated one, which is a much larger and riskier change to an
  already-`Accepted`, already-`Done`-story-dependent module (`REQ-SB-13`'s
  chat/action/history mechanism reads `AGENTS` directly) than composing two
  new sibling stores at the API layer. It would also directly contradict
  `ADR-011` point 2's own reasoning, which this ADR is explicit about
  *not* reopening — only about adding new, independent, per-agent
  properties alongside it.
- **A relational/SQLite store for Sections and Providers**, since both are
  genuinely relational (agents reference sections/providers by id, with a
  referential-integrity-like "can't delete while referenced" constraint) —
  rejected for the same reason `ADR-005`/`ADR-011` already rejected a
  database for scheduler state and communication history: this project has
  no database anywhere in its stack, the data volume (a handful of
  sections/providers, five agents) has no scale characteristic that would
  justify one, and the referential-integrity check this data model wants
  is small enough to implement directly in the business layer (point 4)
  without needing a database engine to enforce it.
- **Encrypting the Provider credential at rest** (e.g. via a
  machine-derived key, or requiring a user-supplied passphrase) —
  rejected: no Accepted requirement or `MEMORY.md` constraint asks for
  this, it would be new cryptographic surface with its own key-management
  problem (where does the encryption key itself live, safely, on a
  single-user personal laptop with no admin rights — `ADR-001`/`ADR-002`'s
  standing constraint) for a threat model this project has never been
  asked to defend against; `compass_api_key` is already plaintext in
  `.env` today with no prior objection, so introducing encryption only for
  *new* Providers would be an inconsistent, partial protection anyway.
- **Requiring the credential on every `PATCH /providers/{id}` call**
  (forcing re-entry to edit any field) — rejected: directly contradicts the
  approved prototype's own Edit form (pre-filled masked value, editable
  endpoint/model fields without re-pasting the key) and adds needless
  friction for zero security benefit (the credential a user would have to
  re-paste is the exact same one already stored).
- **A single flat list of Providers with a boolean `is_default` field
  stored per-provider** (rather than deriving "is this the default" from
  `id == "compass"`) — considered, since it would let a user rename which
  Provider is "the default" in the abstract; rejected as unrequested scope
  — no scenario in `REQ-SB-19` asks for a *different* provider to become
  "the default for new agents," only that Compass is and remains the
  default unless a specific agent's own selection is explicitly changed.
  `is_default` in the `GET /providers` response is purely a
  frontend-badge-rendering convenience, derived, not a new stored concept.
- **Keeping `layoutAgents.ts`'s existing per-Type-keyed `SECTION_META`
  lookup and merely widening it to more hand-picked entries** (adding
  Sales/Customers/Products as literal additional lookup rows) — rejected
  outright: the entire point of `REQ-SB-18` is that Sections are
  user-created and arbitrary-N at runtime (Scenario 2's "create a new
  section... appears... without a code change"), so any hardcoded lookup
  table, however large, would fail the very next time a user creates a
  section from Settings — this is precisely the kind of "N-section-generic"
  computed layout the story's own Notes flag as not covered by the
  originally-approved 3-section prototype.
- **Checking Provider availability inside each individual action handler**
  (e.g. inside `email_classification.run_capture_and_record_completion`
  itself) instead of once at the shared `_invoke_action` funnel — rejected:
  would need to duplicate the same check into every future real handler as
  it's added, whereas the funnel point already exists specifically because
  both the direct-trigger and chat-trigger paths already share it
  (`architecture.md`'s own documented reason `_invoke_action` exists at
  all) — checking once there is strictly less code and cannot be
  forgotten by a future handler author the way a per-handler check could.
**Consequences:**
- `app/data_access/vault_writer.py` gains a fifth and sixth
  `.second-brain/` state file (`agent_sections.json`, `agent_providers.
  json`) and their paired `load_*_state()`/`save_*_state()` primitives —
  pure JSON I/O, no business rules, matching every existing state-file
  primitive's shape.
- Two new business modules, `app/business/section_registry.py` and
  `app/business/provider_registry.py`, own seeding, self-healing default
  assignment, CRUD, and the block-until-unused check for their respective
  concern. Neither imports the other; both import `agent_registry` (to
  enumerate known agent ids) — a second and third instance of the
  already-established "one business module composing another" pattern.
- `agent_registry.py` and `agent_chat.py` (`ADR-011`) are **not modified**
  by this ADR — `ADR-011` remains `Accepted`, unedited, and fully in force
  for the concerns it actually governs (chat trigger-phrase matching,
  agent identity/type/actions staying hardcoded, per-action "not yet
  available" honesty). This ADR is additive alongside it, composed at the
  router layer, not a supersession.
- `app/api/agents_router.py` gains `PATCH /agents/{agent_id}` and a Provider
  -availability check inside `_invoke_action`; `GET /agents` and
  `GET /agents/{agent_id}`'s response shapes grow additive fields
  (`section_id` on the list; `section_id`/`section_name`/`provider_id`/
  `provider_name`/`provider_available` on the detail) — existing callers
  reading only the previously-existing fields are unaffected.
- Two new routers (`sections_router.py`, `providers_router.py`) registered
  in `app/main.py`.
- `src/frontend/src/features/agents-map/layoutAgents.ts`,
  `mockAgents.ts`, and `AgentsMapCanvas.tsx` change as described in point 6;
  `AgentDetailPanel.tsx` gains two new `<select>` `kv-row`s (Section,
  Provider), wired to new fetch/update calls. A new
  `src/frontend/src/features/settings/` folder (mirroring the existing
  `features/agents-map/`, `features/my-day/` one-folder-per-feature
  convention) holds `SectionsCard.tsx`, `ProvidersCard.tsx`, and
  `settingsApiClient.ts` (owning the `/sections` and `/providers` HTTP
  calls); `agentsApiClient.ts` gains the new `PATCH /agents/{id}` call
  only. `SettingsPage.tsx` composes the two new cards alongside its
  existing placeholder Vault/Connections content.
- The pre-seeded "Compass" Provider entry's CRUD-editability-without-
  effect (point 5) is a real, user-facing surprise if not clearly labelled
  in the UI ("editing this does not change your live Compass connection
  this pass" or similar) — left as a UI-copy decision for the decomposer/
  coder, not mandated by this ADR, but flagged here so it isn't
  overlooked.
- The blanket Provider-availability gate at `_invoke_action` (point 7)
  is correct only because every currently-real handler happens to be
  LLM-backed; the first future story that adds a real, non-LLM-backed
  action handler must revisit whether that gate should become
  conditional per-action rather than blanket — not assumed or pre-solved
  here.
- If a future requirement needs a Provider's edited fields to actually
  drive a live call (Compass or otherwise), that is new scope requiring
  its own story and very likely a superseding or additional ADR — this
  ADR deliberately keeps the "Compass" Provider entry inert with respect
  to the real Compass client, per `REQ-SB-19`'s own explicit Non-Goals.

---

## ADR-015: LangGraph adopted for Second Brain's own in-app agent orchestration (chat, Hub routing, memory, skill invocation), bounded to `src/backend`; a shared MCP server exposes vault-query tools to both the in-app agents and Hermes's external orchestration — supersedes ADR-007's blanket "no framework" stance, composes alongside ADR-011

**Status:** Accepted
**Date:** 2026-08-11
**Context:** Four PRD requirements landed the same day this ADR was
written, all on the same architectural fault line `ADR-007` drew:
`REQ-SB-20` (Section Hub Intelligence & Cross-Section Routing — an agent
needing help outside its own knowledge is relayed via its own Section
Hub, then the target Section's Hub, never agent-to-agent directly),
`REQ-SB-25` (Real Conversational Agent Chat — a chat message that isn't a
recognized trigger phrase must get a real, Provider-backed conversational
reply, not the static canned fallback `ADR-011` built), `REQ-SB-26`
(Agent Memory — an agent must correctly draw on information from an
earlier, separate conversation, not just replay the flat chronological
log), and `REQ-SB-27` (Skills Repository — a registered, invocable
specialized capability an agent can call on, e.g. understanding an
uploaded diagram image). `REQ-SB-25`'s own PRD breadcrumb names itself
directly as "the trigger `ADR-007`'s own Consequences section
anticipated" ("If a future requirement genuinely needs Second Brain
itself to coordinate multi-step... work... that is new scope requiring
its own requirement and a superseding ADR — not assumed or pre-built
here") and states plainly that "a superseding ADR is expected at
`/plan-tasks`, not avoided." `REQ-SB-25-US-01` (`Implementation/
UserStories/REQ-SB-25-US-01-real-conversational-agent-chat.md`, `Draft`,
already resolves the fast-path-vs-replace question from its own
acceptance text — `ADR-011`'s keyword-match fast path stays, unchanged,
for the one already-real action; only the previously-canned fallback
changes — but leaves one sub-question explicitly flagged for this pass:
"should the new mechanism be built as a reusable primitive (given
`REQ-SB-23`'s explicit near-term dependency on it) or a narrow one-off?"
`REQ-SB-20-US-01` (`Draft`, already exists) separately resolved its own
routing mechanism, *before* this decision, as "keyword matching, reusing
`ADR-011`'s exact posture... no `ADR-007` tension... no superseding ADR
needed for the mechanism choice itself" — a resolution this ADR now
factually supersedes for the reasons below (recorded honestly as a
contradiction, not silently patched over — see `ESCALATIONS.md` →
`ESC-010`). `REQ-SB-26-US-01`/`REQ-SB-27-US-01` do not exist as stories
yet (`REQ-SB-27`'s own PRD breadcrumb self-assesses as "the
least-precedented requirement captured this session," `ESCALATIONS.md` →
`ESC-006`, still `Open`). **Operator decision, 2026-08-11, made directly
after discussion — resolved, not an open question this ADR re-litigates:**
(1) LangGraph is adopted, scoped specifically to powering Second Brain's
own in-app Agents Map agent behavior (chat, Hub routing, memory, skill
invocation — the four requirements above) — the broad/reusable shape
`REQ-SB-25-US-01`'s own flagged sub-question named as one of two options,
not the narrow single-endpoint alternative; (2) Hermes's own
orchestration for external-channel access (`REQ-SB-03`, not yet built)
is explicitly untouched — `ADR-007`'s "Hermes owns orchestration on its
side of the integration boundary" claim stays entirely true; only its
blanket "Second Brain adds zero orchestration framework to its own
stack" claim is reversed, and only for this bounded in-app surface; (3)
Second Brain exposes one shared MCP server (vault-query tools now, and
`REQ-SB-27`'s skills once that story resolves its own "what is a skill"
question, `ESC-006`) as the tool surface both Second Brain's own in-app
LangGraph agents and Hermes's own externally-orchestrated agents can
call — one implementation, reused both ways, per this project's own
standing integration-sourcing precedent (`MEMORY.md`: prefer/reuse a
single mechanism over building the same capability twice); (4) built now,
alongside the LangGraph adoption, not deferred to some later requirement.
This ADR works out the concrete technical shape those four points leave
open: which `langgraph` package/version, where the graph/state lives in
the `api → business → data_access` layering (`ADR-003`), how it composes
with what already exists (`agent_chat.py`/`ADR-011`, `provider_registry.py`/
`compass_client.py`/`REQ-SB-19`, `agent_communication_history.json`/
`REQ-SB-26`'s likely extension point), which MCP server library, where it
lives, its first tools, and its relationship to the existing REST API
(`agents_router.py`), and whether `ADR-011` needs superseding or coexists.
**No live network/package-index access was available to this architecture
pass** — package/version facts below are grounded in this project's own
already-installed, already-working dependency stack (`requirements.txt`,
`ADR-001`) plus documented package metadata, not a live `pip install`;
every genuinely unverified fact is named as such, not silently assumed,
per this project's own "COM-assisted, one-time determination of a
no-safe-default value" honesty precedent (`MEMORY.md` Patterns).
**Decision:**
1. **Scope of the reversal.** `ADR-007`'s Decision — "Second Brain does
   not add LangGraph... to its own stack" — is reversed, but only for
   Second Brain's own in-app Agents Map agent surface (the chat/Hub-
   routing/memory/skill-invocation behaviour `REQ-SB-20`/`25`/`26`/`27`
   describe). `ADR-007`'s own carve-out for "simple, linear,
   already-working Python functions... with no branching agent behavior
   to coordinate" (`classify_recent_emails`,
   `classify_recent_meetings`/`run_capture_and_record_completion`) is
   **unaffected and unreconsidered** — those pipelines stay exactly as
   they are, outside LangGraph, called directly by the scheduler/`api`
   layer as today (`ADR-005`/`ADR-008`). `REQ-SB-03` (Hermes integration,
   not yet built) is likewise unaffected — Hermes continues to own
   whatever orchestration mechanism it uses for its own multi-channel/
   cross-agent behaviour on its own side of the integration boundary,
   per `MEMORY.md`'s standing "Hermes is external, not something this
   project builds or tracks" constraint; Second Brain's new MCP server
   (point 7, below) is simply one tool/data source Hermes's own
   orchestration can call into, the same relationship any other external
   system integration has to it.
2. **Package: `langgraph` (PyPI), pinned to the major line, exact minor
   resolved at real install time.** `langgraph`'s current stable major is
   `1.x` (GA'd alongside LangChain's own 1.0 release, per the LangChain/
   LangGraph ecosystem's own aligned October 2025 versioning milestone) —
   `requirements.txt` should read `langgraph>=1,<2`, per this project's
   own already-established "pin the ADR's stated major; let the real
   `pip install` resolve, and confirm, the concrete minor/patch" pattern
   (`MEMORY.md` Patterns, first established for `react-router`/`ADR-010`
   after `npm install <pkg>` silently resolved past the analyzed major).
   **Python floor:** `langgraph`/`langchain-core`'s `1.x` line requires
   Python `>=3.10` — comfortably inside this project's Python 3.14
   (`ADR-001`); no conflict there. **The one genuinely open, honestly-
   flagged risk this pass could not verify directly:** whether every
   transitive compiled dependency `langgraph`/`langchain-core` pulls in
   (chiefly `pydantic-core`, the Rust extension pydantic v2 depends on)
   already ships a prebuilt Windows `cp314` wheel — this project's
   no-admin-rights constraint (`ADR-001`/`ADR-002`) means there is no
   C/Rust build toolchain available on this host to compile a missing
   wheel from source. **Partial, real, already-verified evidence in this
   project's own favour:** `pydantic-core` already has a working `cp314`
   wheel on this exact host today — `requirements.txt`'s existing
   `pydantic-settings>=2.5` (itself pydantic-v2-backed, hence
   `pydantic-core`-backed) already installs and runs successfully against
   Python 3.14.6 in the real `.venv` (`ADR-001`), so the single most
   load-bearing compiled dependency across this whole new surface is
   already proven, not merely hoped for. The remaining, still-unverified
   surface is `langgraph`/`mcp`/`langchain-openai`/`langchain-mcp-
   adapters`'s own additional transitive dependencies, if any beyond
   `pydantic-core` — must be confirmed by the coder task's own real
   `pip install` against the real `.venv`, exactly the same verification
   step already established for `react-router`'s pinned-major install,
   not assumed here. If a required wheel is genuinely missing for
   `cp314`, that is grounds for a follow-up decision (pin an older
   transitive dependency version, or escalate) — not a silent
   workaround.
3. **Layering: a new `app/business/agent_orchestration/` sub-package**
   (the first sub-package under `business/` — every existing module there
   is a flat file; this is the first concern with enough internal
   structure — graph definition, state schema, model resolution, MCP
   client — to warrant one, per the task's own explicit "a new module or
   sub-package" framing). Contents:
   - `state.py` — the graph's state schema (agent id, the replayed
     message history, the resolved model/tool bindings for that call).
   - `model_factory.py` — resolves a per-agent `langchain_openai.
     ChatOpenAI` instance from `provider_registry.get_agent_provider(
     agent_id)` (point 4, below); returns an explicit "unavailable"
     signal rather than a model object when `provider_registry.
     has_real_client(provider_id)` is `False`, **before** any model is
     constructed or called — mirrors `agents_router.py::_invoke_action`'s
     existing "declared but not yet backed by a real handler → honest
     unavailability, no silent fallback, no fabricated response" funnel-
     gate shape (`ADR-011` point 3 / `ADR-014` point 7), applied one
     layer over for conversational replies (`REQ-SB-25` Scenario 4).
   - `mcp_client.py` — a `langchain_mcp_adapters.client.
     MultiServerMCPClient` wrapper, pointed at Second Brain's own MCP
     server's loopback URL (point 8, below), used to load that server's
     registered tools as LangChain `Tool` objects the graph binds to its
     model.
   - `graph.py` — builds and compiles **one** `langgraph.graph.
     StateGraph`, exposing `run_agent_conversation(agent_id: str,
     message: str, history: list[dict]) -> dict` (`{"reply": str} |
     {"error": str}`) as the module's one public entry point. This pass
     (`REQ-SB-25`) needs only a single model-call node (reply, bound to
     whatever tools `mcp_client.py` currently loads); `REQ-SB-20`/`26`/
     `27` are each expected to extend this **same** graph with additional
     nodes/conditional edges (a Hub-routing decision node; a memory-
     retrieval node; skill-invocation tool nodes) as their own
     `/plan-tasks` passes design them — mirroring, one layer over, the
     MCP server's own "grow by registering, not by spinning up a new
     instance" extensibility story (point 9, below). Exact node/edge
     shapes for `REQ-SB-20`/`26`/`27` are **not** decided by this ADR —
     each inherits this graph as its settled home, the same way
     `ADR-005` gave `REQ-SB-08`/`09` a settled scheduling home without
     pre-designing their own pipelines.
   - `app/business/vault_query_tools.py` (new, **sibling** to
     `agent_orchestration/`, not nested inside it — a general capability
     consumed by both the MCP server registration layer and, indirectly
     via the MCP client, the graph, not something orchestration-specific)
     — the actual tool *implementations*, thin business-layer functions
     over already-existing read-only `vault_writer` primitives
     (`list_known_customers`, `list_known_kinds`, `list_known_partners`,
     `list_notes_in_kind_folder`) — no new `data_access` reads, no
     business rules beyond simple projection, per `ADR-003`.
4. **Model integration: `langchain_openai.ChatOpenAI`, not an extension of
   `compass_client.py`'s existing `classify_email`.** `app/data_access/
   compass_client.py` is **untouched** by this ADR — it keeps its one
   existing, fixed-shape, single-purpose function, called only by the
   linear email-classification pipeline (point 1's carve-out). The new
   LangGraph-orchestrated surface needs a genuine multi-turn, tool-
   calling-capable chat-model abstraction — exactly what `ChatOpenAI`
   (a `langchain_core.language_models.BaseChatModel`) provides and a raw
   single-shot `httpx.post` function does not — instantiated per-call
   with `base_url`/`api_key`/`model` read from the agent's resolved
   Provider record (`provider_registry.get_agent_provider`), reusing
   `REQ-SB-19`'s existing Provider-selection mechanism as the single
   source of LLM connection configuration for this new surface too, not
   a second, parallel config path. Confirmed compatible with Compass
   specifically by `compass_client.py`'s own existing docstring — "Second
   Brain talks to it directly over httpx; no SDK needed since Compass
   speaks the same wire format as OpenAI's `/chat/completions`" — the
   exact same reason `ChatOpenAI`'s `base_url` override works against
   Compass, not only `api.openai.com`.
5. **Composition with `ADR-011`: coexistence, not supersession.**
   `ADR-011` stays `Accepted`, **unedited**, and fully governs the exact-
   phrase/keyword-substring fast path for the one currently-real action
   (`email-capture`'s `run_capture_now`) — resolved directly from
   `REQ-SB-25-US-01`'s own acceptance text ("a chat message **that isn't
   a recognized trigger phrase**" presupposes trigger-phrase recognition
   still exists). `app/business/agent_chat.py` is **not modified** by
   this ADR. Only `app/api/agents_router.py::chat` changes: it still
   calls `agent_chat.handle_chat_message` first, unchanged; on a match,
   behaviour is identical to today (direct handler invocation, no LLM
   call — `REQ-SB-25` Scenario 2); on no match, instead of returning
   `matched["fallback_reply"]`'s static canned string directly, it now
   calls `agent_orchestration.run_agent_conversation(agent_id, message,
   history)` and returns its real reply (or honest unavailability/failure
   message, `REQ-SB-25` Scenarios 4/5) in place of the old fallback. This
   is the same "compose alongside, don't reopen" shape `ADR-014` already
   used for `agent_registry.py` — a second, independent decision layered
   on top of an `Accepted` mechanism, not a rewrite of it.
6. **Conversation-state source of truth stays `.second-brain/
   agent_communication_history.json` — no LangGraph persistent
   checkpointer for cross-request state.** `REQ-SB-25` Scenario 3's
   multi-turn continuity is satisfied by `agents_router.py::chat`
   reading that agent's existing history (`vault_writer.
   load_agent_history(agent_id)`, already called for `GET /agents/{id}/
   history`) and passing the relevant recent turns into `run_agent_
   conversation`'s `history` argument as the graph's initial state on
   **every call** — the graph itself runs statelessly per HTTP request
   (`.invoke()`, not a thread-ID-keyed `.stream()`/persistent-checkpoint
   invocation). This deliberately avoids introducing a second,
   potentially-divergent conversation-history store: `langgraph` ships
   built-in checkpointers (`MemorySaver`, or `SqliteSaver` via
   `langgraph-checkpoint-sqlite` for cross-restart persistence), but this
   project has repeatedly and explicitly rejected adding SQLite/a
   database for local state (`ADR-005`'s job-store rejection, `ADR-011`'s
   communication-history rejection, `ADR-014`'s Sections/Providers
   rejection) in favour of the existing flat-JSON `.second-brain/`
   convention — no reason to make a different call here. No entry-`kind`
   schema change to `agent_communication_history.json` results — a
   real-conversational-reply's failure (Scenario 5) is still just a
   `"chat_agent"`-kind entry containing the honest failure text, the same
   shape every existing reply already uses.
7. **MCP server library: the official Model Context Protocol Python SDK,
   package `mcp` (PyPI), specifically its high-level `mcp.server.
   fastmcp.FastMCP` server class** (decorator-based tool registration,
   `@mcp.tool()`) — the standard, spec-maintained implementation, over a
   hand-rolled JSON-RPC-over-HTTP protocol implementation this project
   has no reason to build itself (mirrors this project's own repeated
   "prefer an already-solved library over hand-rolled protocol/mechanism
   code" precedent — `ADR-005`'s APScheduler choice, `ADR-008`'s
   port-don't-reinvent stance for Outlook COM). **Transport: Streamable
   HTTP** (the MCP protocol's current recommended HTTP-based transport,
   superseding the original separate HTTP+SSE transport), **mounted as
   an ASGI sub-application inside the existing single FastAPI process** —
   `app/api/mcp_server.py` (new; api-adjacent, per the task's own
   framing — a protocol/transport-translation layer analogous to
   `agents_router.py`'s own REST-translation role, but mounted via
   `app.mount("/mcp", mcp_server_app.streamable_http_app())` rather than
   `app.include_router(...)`, since MCP's own protocol isn't ordinary
   REST) registers `vault_query_tools.py`'s functions as `@mcp.tool()`s
   and is wired into `app/main.py` alongside the six existing
   `app.include_router(...)` calls. No new port, no new process — the
   same single-process precedent `ADR-005` already established
   ("Second Brain runs as a single-process dev server"); Hermes reaches
   this MCP server exactly the way it would reach any other Second Brain
   HTTP surface, over the same host:port. `mcp`'s own Python floor is
   `>=3.10`, same headroom as point 2.
8. **How the in-app LangGraph agents consume the *same* MCP server —
   "one implementation, reused both ways," concretely.** The in-app
   graph does **not** import `vault_query_tools.py`'s functions directly
   and wrap them a second time with LangChain's own `@tool` decorator —
   that would be a second, manually-kept-in-sync tool-registration
   surface (name/description/argument-schema declared twice, free to
   silently drift between the two declarations) — exactly the "two
   implementations of the same capability" duplication the operator's
   own decision (point 3, Context) rejects. Instead, `agent_orchestration
   /mcp_client.py`'s `MultiServerMCPClient` connects to the exact same
   mounted `/mcp` endpoint over a loopback HTTP call (the in-app agent is
   simply another MCP client, indistinguishable in principle from
   Hermes), auto-generating LangChain `Tool` objects from whatever the
   server currently has registered. A tool's name/description/schema is
   therefore declared **exactly once** — in the MCP server's own
   `@mcp.tool()` registration — and every consumer, in-app or external,
   sees the identical contract. The small loopback-HTTP round-trip cost
   (same process, same machine, single user) is a deliberate, worthwhile
   trade against that drift risk.
9. **Extensibility pattern, explicit for both the MCP server and the
   graph.** The MCP server grows by **registering new tools on the same
   server** as new capabilities are built (e.g. `REQ-SB-27`'s skills
   become new `@mcp.tool()` entries over time, once that story resolves
   its own "what is a skill" question, `ESC-006`) — **not** by spinning
   up a new server per capability; a second server is the exception (a
   genuinely separate concern, e.g. a future non-vault external
   integration with its own trust boundary), not the default extension
   path. The LangGraph graph (point 3) follows the identical philosophy
   one layer over: new capability (`REQ-SB-20` Hub-routing, `REQ-SB-26`
   memory, `REQ-SB-27` skill-invocation) is added as new nodes/edges on
   the **same** compiled graph, not a new graph per requirement.
10. **Relation to the existing REST API — a parallel surface, not a
    replacement.** `agents_router.py`'s existing `GET`/`POST /agents/...`
    endpoints are unchanged in shape (only the chat handler's fallback
    body, point 5) and continue to serve the in-app frontend's own
    settings/actions/chat/history UI — ordinary human-facing HTTP+JSON.
    The MCP server exposes read/query-style vault tools using MCP's own
    tool-invocation semantics, structured for LLM/agent tool-calling, not
    human REST browsing — the two surfaces serve structurally different
    consumers (a human's browser vs. an LLM-orchestrated agent, whether
    Second Brain's own LangGraph or Hermes) and deliberately do not
    merge, mounted at a distinct path prefix (`/mcp`) in the same
    process.
11. **First tools — illustrative, not mandated by this pass.** Since
    `REQ-SB-01`/`REQ-SB-02` (Vault Indexing & Browse/Search) don't exist
    yet, the first genuinely useful tools are necessarily thin wrappers
    over already-existing read primitives: `list_known_customers`,
    `list_known_kinds`, `list_known_partners`, `list_notes_in_kind_folder`
    (point 3). Building the MCP server skeleton plus at least one real
    tool is expected to land as part of whichever story's own
    `/plan-tasks` pass first needs a working, exercised (not just
    theoretical) tool-calling graph — most plausibly `REQ-SB-25-US-01`,
    the earliest-ready of the four (per the operator's "build now, not
    deferred" directive, Context point 3/4) — but the exact task-level
    sequencing and scope is the decomposer's call at that story's own
    `/plan-tasks` pass, not decided here (this ADR's own job is the
    architecture decision, not implementation tasks).
12. **`REQ-SB-20`'s Hub-routing mechanism moves from pure keyword-
    substring matching to a LangGraph-orchestrated routing node** — a
    real, acknowledged change from what `REQ-SB-20-US-01`'s own Context/
    Constraints currently record ("keyword matching, reusing `ADR-011`'s
    exact posture... no `ADR-007` tension... no superseding ADR needed").
    That story's own locked-shape Acceptance Criteria (a keyword field
    per agent; a cross-Section request relayed via both Hubs, never
    agent-to-agent directly; an honest no-match report; an agent with no
    keywords never selected) are **unaffected** — they describe
    externally observable routing behaviour, not a specific mechanism,
    so they remain satisfiable under either a pure string-match or a
    LangGraph-orchestrated decision node that uses each agent's declared
    keywords as its own routing input. Only the *mechanism* backing "how
    a Hub decides" changes, from a hand-rolled lookup to a node on this
    ADR's graph (point 3/9). Per hard rule 1 (specs are append-only),
    `REQ-SB-20-US-01`'s existing Context/Constraints text is **not**
    edited by this ADR — the contradiction is recorded honestly in
    `ESCALATIONS.md` → `ESC-010` instead, to be reconciled in that
    story's own `## Notes` when it actually reaches its own `/plan-tasks`
    pass (not this one — no story file is edited by this ADR). Per-agent
    keyword storage itself (a new persisted concern, "keywords assigned
    per agent alongside its Section") is **not** decided here — most
    likely a new sibling `.second-brain/agent_keywords.json` extending
    the established flat-JSON convention, mirroring `agent_sections.
    json`/`agent_providers.json`'s shape, but that is `REQ-SB-20-US-01`'s
    own architecture-pass decision to make, not pre-empted by this ADR.
13. **`REQ-SB-26` (Agent Memory) inherits a settled *storage-location*
    pattern, not a settled *mechanism*.** Whatever extraction/
    summarization logic `REQ-SB-26`'s own `/spec`/`/plan-tasks` passes
    design (raw replay vs. a summarized store — explicitly still open per
    its own PRD breadcrumb), the *storage location* is architecturally
    resolved now: a new sibling `.second-brain/agent_memory.json`,
    extending the established flat-JSON-file convention to a new
    concern (mirroring every other new concern's own sibling-file
    pattern — `processed_meeting_ids.json`, `agent_sections.json`,
    `agent_providers.json`), consumed by a new memory-retrieval node on
    this ADR's graph (point 3/9) — not LangGraph's own built-in
    checkpointer/store mechanism (point 6's reasoning applies equally
    here), and not a database. This bounds *where* `REQ-SB-26` plugs in
    without pre-deciding *what* it extracts or *how*.
**Alternatives Considered:**
- **Leave `ADR-007` as-is, keep rejecting an orchestration framework
  entirely** — rejected: the operator has directly, explicitly decided
  otherwise (Context), and `ADR-007`'s own Consequences section already
  pre-authorized exactly this class of reversal once a real requirement
  needed it; `REQ-SB-20`/`25`/`26`/`27` collectively are that requirement.
  This story does not re-litigate whether to adopt LangGraph — only how.
- **A hand-rolled Python state machine / plain function composition**
  instead of LangGraph — rejected: `ADR-007`'s original judgment that
  real orchestration machinery was "disproportionate" held only while
  the entire agent surface was a single keyword-matched action; four
  separate, genuinely branching, stateful capabilities (routing, memory,
  skill-invocation, multi-turn chat) built independently would each
  re-implement LangGraph's own graph/state/tool-calling abstractions
  from scratch, worse than adopting the one established framework once —
  the same "prefer the already-solved library once complexity crosses a
  real threshold" reasoning this project has applied repeatedly
  (`ADR-005` APScheduler, `ADR-008` porting proven COM code).
- **A different orchestration framework (CrewAI, AutoGen, or similar)**
  instead of LangGraph — rejected: LangGraph is the framework `ADR-007`'s
  own original Context named specifically (the operator asked about it
  by name at project inception), it composes natively with the MCP
  tool-calling ecosystem via the official `langchain-mcp-adapters`
  package (point 8), and it is the operator's own explicit, named choice
  in this session's discussion (Context) — not a default this pass
  needed to independently re-litigate among alternatives.
- **Narrow, single-endpoint scope** (LangGraph wired only into
  `REQ-SB-25`'s own `POST /agents/{id}/chat` reply path, with `REQ-SB-20`/
  `26`/`27` each left to decide their own mechanism independently later)
  — the other option `REQ-SB-25-US-01`'s own flagged sub-question named
  — rejected in favour of the broad/reusable shape (Decision point 1):
  the operator's own direct instruction explicitly names all four
  requirements as this adoption's intended scope, and `REQ-SB-23`'s own
  PRD breadcrumb already names `REQ-SB-25`'s mechanism as its own
  near-term dependency — building narrow now would all but guarantee a
  second architecture pass the moment `REQ-SB-23`/`REQ-SB-20` are
  actually driven through `/plan-tasks`, the exact risk that flagged
  sub-question named.
- **The full `langchain` package** instead of the targeted `langgraph` +
  `langchain-openai` combination — rejected: `langchain` is a much
  larger, integration-bundling monolith; `langgraph` and `langchain-
  openai` each depend only on the shared, lighter `langchain-core`
  abstractions package, not the full `langchain` surface — no
  requirement here needs `langchain`'s own higher-level chains/agents
  abstractions, only `langgraph`'s graph engine and `langchain-openai`'s
  chat-model adapter.
- **Extending `compass_client.py`'s existing `classify_email`-shaped
  `httpx` call into a general-purpose conversational function**, instead
  of adding `langchain-openai` — rejected (Decision point 4): would force
  hand-rolling a multi-turn/tool-calling loop LangGraph exists
  specifically to provide, and that hand-rolled loop would need
  redesigning three more times as `REQ-SB-20`/`26`/`27` each add their
  own graph nodes — one genuine framework-native model integration,
  built once, is strictly less total work and risk than a bespoke
  extension repeated per requirement.
- **A hand-rolled MCP/JSON-RPC server implementation** instead of the
  official `mcp` Python SDK — rejected for the same "prefer an
  already-solved library" reasoning as the framework choice itself
  (Decision point 7) — the protocol has real edge cases (session
  handling, streaming, capability negotiation) a spec-maintained SDK has
  already solved.
- **Direct in-process dual tool-registration** (import `vault_query_
  tools.py` functions directly, wrap each a second time with LangChain's
  own `@tool` decorator for the graph, entirely bypassing the MCP client
  for the in-app path) instead of routing the in-app agent through the
  same MCP server via `langchain-mcp-adapters` — rejected as the default
  (Decision point 8): faster (no loopback round-trip) but reintroduces
  exactly the "two declarations of the same tool contract, free to
  drift" duplication the operator's own decision (Context point 3)
  explicitly rejects. Revisit only if the loopback round-trip's latency
  proves genuinely disqualifying for a real scenario — not assumed here.
- **A second, separate MCP server per new capability** (e.g. one server
  for vault-query tools, a different one for `REQ-SB-27`'s skills) —
  rejected outright per the operator's own explicit extensibility
  directive (Context point 4, Decision point 9): one server, grown by
  registration, is the default; a second server is reserved for a
  genuinely separate concern, not a convenience default.
- **LangGraph's own built-in persistent checkpointer**
  (`SqliteSaver`/`langgraph-checkpoint-sqlite`) for cross-request/cross-
  restart conversation state, instead of continuing to source it from
  `agent_communication_history.json` — rejected (Decision point 6): a
  new storage technology (SQLite) this project has repeatedly and
  explicitly rejected for local state (`ADR-005`, `ADR-011`, `ADR-014`),
  and a second, divergence-risking representation of "what was said"
  alongside the file that's already the established source of truth for
  exactly that.
- **Superseding `ADR-011` entirely** (replacing keyword-match action-
  triggering outright, instead of keeping it as a fast path alongside the
  new conversational surface) — rejected: already resolved directly from
  `REQ-SB-25-US-01`'s own acceptance-text wording ("a chat message **that
  isn't a recognized trigger phrase**" presupposes the fast path still
  exists), not a fresh architectural call this ADR needed to re-open.
**Consequences:**
- **New dependencies** (`src/backend/requirements.txt`): `langgraph`
  (`>=1,<2`), `langchain-openai`, `mcp`, `langchain-mcp-adapters` — each
  pinned to its current major per this project's own established
  pin-then-verify-at-install pattern; exact resolved minors recorded by
  the coder task that runs the real `pip install`, per Decision point 2's
  own honestly-flagged wheel-availability risk (not assumed clean here).
- **New files:** `app/business/agent_orchestration/` (`state.py`,
  `model_factory.py`, `mcp_client.py`, `graph.py`, `__init__.py`
  exposing `run_agent_conversation`), `app/business/
  vault_query_tools.py`, `app/api/mcp_server.py`. `app/main.py` gains one
  new `app.mount("/mcp", ...)` call alongside its six existing
  `app.include_router(...)` calls. `app/api/agents_router.py::chat`'s
  no-trigger-phrase-match branch changes (Decision point 5) — its
  trigger-phrase-match branch, every other endpoint, and every other
  module named in this ADR's Context are otherwise unchanged.
- **`ADR-007`'s own Status line is updated to `Superseded by ADR-015`**,
  with a short linking note appended directly below it (its Context/
  Decision/Alternatives/Consequences body is **not** rewritten, per this
  file's own "never edit an Accepted ADR" rule) — its "Hermes owns
  orchestration on its own side of the integration boundary" claim
  remains entirely true and is carried forward unchanged by this ADR
  (Decision point 1); only its blanket "Second Brain's own stack stays
  free of an orchestration framework" claim is reversed, for the bounded
  surface this ADR names.
- **`ADR-011` remains `Accepted`, unedited, and fully in force** for the
  concern it actually governs (keyword-substring fast-path matching for
  the one currently-real action) — this ADR composes alongside it,
  exactly the "second, independent decision layered on top, not a
  rewrite" shape `ADR-014` already established as this project's own
  precedent for extending a settled mechanism without reopening it.
- **`REQ-SB-25-US-01`'s own flagged reusability sub-question is resolved**
  by Decision point 1/Alternatives ("broad, reusable" chosen over
  "narrow, single-endpoint") — see `REVIEW-QUEUE.md`'s updated entry for
  that story.
- **`REQ-SB-20-US-01`'s existing Context/Constraints text (keyword-match
  mechanism, "no `ADR-007` tension," "no superseding ADR needed") is now
  factually superseded by this ADR** — recorded as a genuine contradiction
  in `ESCALATIONS.md` → `ESC-010` (category `adr-deviation`), **left
  `Open`** since `REQ-SB-20-US-01` itself is not edited by this pass (per
  the task that produced this ADR, story-level reconciliation is deferred
  to that story's own `/plan-tasks` pass, not done here) — its own
  Acceptance Criteria are unaffected (Decision point 12).
- **`REQ-SB-26`/`REQ-SB-27` inherit a settled home** (a graph node plus,
  for `REQ-SB-26`, a new sibling `.second-brain/agent_memory.json` file)
  without either requirement's own open questions (memory's exact
  extraction mechanism; `REQ-SB-27`'s own "what is a skill," `ESC-006`,
  still `Open`) being pre-decided by this ADR.
- **`REQ-SB-21` (Agent Working Modes, `Draft`) interaction not resolved
  here.** A Supervised agent's "propose an action and wait for approval"
  behaviour may eventually want LangGraph's own `interrupt()`/human-in-
  the-loop primitive for a chat-triggered flow — genuinely relevant to a
  graph-based conversational surface, but out of this ADR's scope
  (`REQ-SB-21-US-01` is its own story); if used, an in-memory
  `MemorySaver` scoped to a single active request/thread is expected to
  be sufficient (no cross-restart persistence need, since Decision point
  6 already keeps conversation content itself out of any LangGraph
  checkpointer) — not decided further here.
- **`app/data_access/compass_client.py`, `app/business/agent_chat.py`,
  and `app/business/agent_registry.py` are all untouched** by this ADR —
  every existing, already-`Done` capability built on them continues to
  work exactly as it does today.
- A `MEMORY.md` decision entry recording this ADR's real-world outcome
  (once actually built and live-verified) is expected at the Definition-
  of-Done step of whichever story implements it first, per this
  project's own standing coder-updates-`MEMORY.md` convention — not
  written by this architecture pass, which does not itself build or
  verify anything.

---

## ADR-016: Agent Memory (`REQ-SB-26`) extraction mechanism — LLM-based extracted/summarized fact store, not raw cross-conversation replay; two new nodes on `ADR-015`'s existing conversation graph — extends `ADR-015` point 13, does not reopen it

**Status:** Accepted
**Date:** 2026-08-12
**Context:** `ADR-015` point 13 already settled `REQ-SB-26`'s *storage
location* (a new sibling `.second-brain/agent_memory.json`, not an
extension of `agent_communication_history.json`, not LangGraph's own
checkpointer, not a database) and *architectural home* (a new node on the
same compiled `app/business/agent_orchestration/graph.py` `ADR-015`
already built for `REQ-SB-25`) — but explicitly left the *extraction
mechanism* open: "whatever extraction/summarization logic `REQ-SB-26`'s
own `/spec`/`/plan-tasks` passes design (raw replay vs. a summarized
store — explicitly still open per its own PRD breadcrumb)... this bounds
*where* `REQ-SB-26` plugs in without pre-deciding *what* it extracts or
*how*." `REQ-SB-26-US-01`'s own Constraints reaffirm this is still open
at this pass. This ADR makes that call. **Raw replay is rejected up
front, before evaluating what a "summarized/extracted" mechanism should
look like:** `REQ-SB-25-US-01-T02`'s own `history_entries_to_messages`
already replays a *single, still-open* conversation's full history into
every model call with **no truncation/window this pass** (its own
docstring: "a token-budget concern is `REQ-SB-24`'s own separate
scope"). `REQ-SB-26`'s own Non-Goals explicitly distinguish itself from
that mechanism — memory is for information from a conversation that has
*already ended*, spanning potentially many separate past conversations,
not the one still-open thread. Replaying the *raw* transcript of every
past separate conversation, unbounded, into every future call would (a)
compound an already-deliberately-punted token-budget concern across the
user's entire conversation history with an agent, forever, rather than a
small bounded store, and (b) directly risk Scenario 3's "honest, not
fabricated" bar by drowning whatever fact is actually relevant to a new
question in a large volume of unrelated past chat noise, rather than
surfacing it cleanly. A small, purpose-extracted fact store is the
mechanism this ADR designs instead.
**Decision:**
1. **Extraction is LLM-based (a real Provider-backed completion), not a
   hand-rolled heuristic** (regex/keyword-triggered pattern matching for
   phrases like "my name is"/"I prefer"). The acceptance text places no
   constraint on what shape of information the user might share
   (Scenario 1's "information the user gave it" is deliberately open-
   ended), so a fixed-pattern extractor cannot be trusted to reliably
   separate a durable, worth-remembering fact from incidental chat noise
   — the same "prefer the real Provider-backed mechanism over a hand-
   rolled heuristic for genuinely open-ended natural-language content"
   reasoning `REQ-SB-25`/`ADR-015` already applied one layer over
   (rejecting a keyword/NLU-free canned fallback for conversational
   replies themselves).
2. **Two new nodes on `ADR-015`'s existing single compiled graph**
   (`app/business/agent_orchestration/graph.py`) — not a second graph,
   per `ADR-015` points 3/9's already-settled "grow by node" pattern:
   - **Read path — `retrieve_memory`, running before the existing
     `call_model` node.** The node itself performs no file I/O (graph
     modules stay free of `data_access` access, mirroring `ADR-015` point
     6's "history passed in fresh from the router" shape for conversation
     state). Instead, `agents_router.py::chat` loads the agent's stored
     memory via a new `vault_writer.load_agent_memory(agent_id) ->
     list[dict]` primitive (mirroring `load_agent_history`'s exact shape)
     and passes it into `run_agent_conversation` as a new `memory:
     list[dict]` parameter, alongside the existing `history` parameter.
     `retrieve_memory` folds those stored facts into the graph's initial
     message list (a dedicated `SystemMessage` enumerating each stored
     fact, appended after the existing agent-identity `SystemMessage`
     `REQ-SB-25-US-01-T02` already builds) before `call_model` runs, so
     the reply node's own context includes prior-conversation facts with
     zero additional file I/O inside `agent_orchestration/` itself.
   - **Write path — `extract_memory`, running after `call_model`, on the
     SAME graph, inside the SAME `.invoke()` call — not a second,
     separate HTTP round trip or a second Provider resolution.** It
     reuses the exact model instance `call_model` already resolved/bound
     (no second `model_factory.resolve_agent_model` call, no second
     Provider-availability check) and issues one additional, narrowly-
     scoped completion asking the model to identify any new durable
     fact(s) the user shared in the latest exchange worth remembering for
     a future, separate conversation — explicitly instructed to return
     none rather than inventing one, mirroring Scenario 3's "honest, not
     fabricated" posture one layer over — producing a small list of short
     fact strings on the graph's own state (`extracted_facts:
     list[str]`), not written to disk by the graph itself.
     `run_agent_conversation`'s return shape gains this field —
     `{"reply": str, "extracted_facts": list[str]} | {"error": str}` —
     with extraction skipped entirely (`extracted_facts` never produced)
     whenever `call_model` itself failed/returned an error, matching the
     existing short-circuit-on-unavailable-Provider shape `ADR-015`
     already established. `agents_router.py::chat` persists any returned
     facts via a new `vault_writer.append_agent_memory_entries(agent_id,
     facts: list[str]) -> None` primitive, called immediately alongside
     its existing `append_agent_history_entry` calls — the same "router
     persists post-graph side effects" shape already established for
     conversation history, extended one concern over to memory.
3. **Storage shape:** `.second-brain/agent_memory.json`, `{agent_id:
   [{"fact": str, "recorded_at": iso8601}, ...]}` — a flat, append-only
   list of short extracted-fact strings per agent, not raw message
   objects, mirroring `agent_communication_history.json`'s existing
   one-file-keyed-by-agent-id shape (`ADR-011`) applied to a new concern.
   No dedup/merge/consolidation logic this pass (a growing list of short
   facts, not a maintained "profile") — `REQ-SB-26-US-01`'s own
   Acceptance Criteria require correct recall, not a bounded/pruned
   store; consolidation is left for a future pass once real growth is
   observed, not pre-designed here.
4. **Retrieval scope: the full stored fact list for that `agent_id` is
   folded into every call, unfiltered/unranked** — no similarity search,
   no relevance-ranking, no vector index. The simplest mechanism that
   satisfies the locked ACs, mirroring the "no truncation/window this
   pass" precedent `REQ-SB-25-US-01-T02` already established for
   conversation-history replay; real memory volume for a personal,
   single-user assistant is expected to be small. Revisit only once real
   growth is observed to actually strain a real Provider's context
   window — not assumed a problem here.
**Alternatives Considered:**
- **Raw full-conversation-history replay spanning conversation
  boundaries** (extend `history` itself to include prior, already-ended
  conversations, sourced straight from `agent_communication_history.json`,
  with no separate `agent_memory.json` at all) — rejected: this is
  exactly what `ADR-015` point 13 and `REQ-SB-26-US-01`'s own Constraints/
  Non-Goals already rule out (a **new**, separate file is explicitly
  required, not an extension of `agent_communication_history.json`), and
  it would duplicate `REQ-SB-25`'s own existing single-conversation
  continuity mechanism while unboundedly compounding an already-punted
  token-budget concern (`REQ-SB-24`) across an agent's *entire*
  conversation history with the user, forever, rather than a small
  bounded fact store.
- **A hand-rolled heuristic extractor** (regex/keyword-triggered pattern
  matching) instead of an LLM-based extraction call — rejected (Decision
  point 1): the acceptance text places no constraint on what shape of
  information the user might share, so a fixed-pattern extractor would
  silently miss most real user statements — a correctness/completeness
  risk this project has no basis to accept when a real Provider-backed
  model is already the established mechanism for open-ended natural-
  language understanding elsewhere on this exact surface
  (`REQ-SB-25`/`ADR-015`).
- **A second, separate LLM call outside the graph** (a standalone
  extraction function in a new module, invoked by the router after
  `run_agent_conversation` returns, resolving its own model instance
  independently) instead of a node on the same graph inside the same
  `.invoke()` — rejected: would re-resolve the agent's Provider/model a
  second time (a second `model_factory.resolve_agent_model` call,
  redundant work, and a second place the "Provider unavailable" short-
  circuit would need duplicating) and forces the router to hand-
  orchestrate two dependent LLM calls itself instead of composing them
  declaratively as sequential graph nodes — exactly the shape LangGraph
  exists to provide (`ADR-015`'s own "prefer the framework over hand-
  rolled composition" reasoning, applied one layer over).
- **Fold retrieval/extraction into a single node/single LLM call** (e.g.
  `call_model` itself asked to also emit a structured "facts to
  remember" field via one structured-output/tool-calling response,
  alongside its ordinary reply) — rejected for this pass: `call_model`
  already binds vault-query tools (`bind_tools`); layering a second,
  independent structured-output schema onto the same call that is also
  reasoning about tool calls risks one concern degrading the other
  (reply quality vs. extraction correctness). Two separate, narrowly-
  scoped nodes/prompts is more likely to produce a correct reply *and* a
  correct extraction than one overloaded call, at the cost of one
  additional — but same-`.invoke()`, no extra network round trip beyond
  the model call itself — completion. Revisit if a real single-call
  structured-output approach later proves reliably cheaper — not assumed
  here.
- **Similarity-search/embedding-ranked retrieval** (fold in only the
  "most relevant" subset of stored facts per query, via a vector store or
  embedding-similarity step) instead of always replaying the full stored
  list — rejected as premature: introduces a new storage technology (a
  vector index) this project has no precedent for and no demonstrated
  need for yet (expected memory volume per agent is small — a personal,
  single-user assistant, not a high-volume corpus); full-list replay
  already satisfies every locked AC and mirrors the "no truncation this
  pass" precedent already accepted for conversation-history replay.
  Revisit only once real growth demonstrates this is insufficient.
- **No extraction at all** — treat "memory" as simply re-surfacing the
  raw text of the most recent N chat turns from
  `agent_communication_history.json`, verbatim, regardless of relevance —
  rejected: does not scale (the same unbounded-growth rejection as the
  first alternative above) and does not actually satisfy Scenario 1's
  "correctly reference or use" bar for information from a conversation
  that may have happened long ago among many unrelated turns; an
  extracted, purpose-built fact is a materially stronger signal for a
  later, unrelated conversation's context than an arbitrary raw excerpt.
**Consequences:**
- **Additive-only changes to `ADR-015`'s already-built shape.**
  `app/business/agent_orchestration/graph.py` gains two new nodes
  (`retrieve_memory`, `extract_memory`); `state.py`'s
  `AgentConversationState` gains `memory: list[dict]` (input) and
  `extracted_facts: list[str]` (output) fields. No existing field is
  removed or renamed. `run_agent_conversation`'s public signature gains
  one new parameter (`memory`) and its return shape gains one new key
  (`extracted_facts`) — both additive and backward-compatible with
  `REQ-SB-25`'s existing call site once this story's own equivalent of
  `T08` updates it.
- **New files:** `.second-brain/agent_memory.json` (`ADR-015` point 13's
  already-settled location) plus two new `vault_writer.py` primitives,
  `load_agent_memory`/`append_agent_memory_entries`, mirroring
  `load_agent_history`/`append_agent_history_entry`'s exact shape.
- **A second real LLM completion now happens on every successful
  conversational reply** (extraction, in addition to the reply itself) —
  a genuine cost/latency consequence (roughly double the per-message
  Provider call volume for any agent this mechanism is wired into),
  named explicitly, not hidden. Acceptable for a personal, single-user
  assistant at today's expected message volume; worth revisiting (e.g.
  batching extraction, or running it async/best-effort rather than
  inline) if real usage ever makes chat reply latency noticeably worse —
  not a problem solved here.
- **`REQ-SB-20`/`REQ-SB-27` are unaffected by this ADR.** This decision
  is scoped to `REQ-SB-26`'s own two new nodes; neither other
  requirement's own future `/plan-tasks` pass inherits an extraction-
  mechanism precedent from this ADR beyond the already-general "grow the
  graph by node" pattern `ADR-015` itself established.
- **Does not modify or reopen `ADR-015`** — extends it (point 13)
  exactly the way `ADR-015` point 9 already anticipated ("each inherits
  this graph as its settled home... exact node/edge shapes... not
  decided by this ADR").

---

## ADR-018: Per-agent working mode (Autonomous/Supervised/Manual) — a new mutable agent property gating both the chat/direct-action funnel and the background-capture scheduler tick, backed by a new Pending Approvals workflow store

**Status:** Superseded by ADR-020 (points 3 and 5 only)
**Superseded note (2026-08-12, append-only — the body below is otherwise
unchanged, per this file's own "never edit an Accepted ADR" rule):**
`ADR-020` replaces this ADR's Decision points 3 (the chat/direct-action
gate) and 5 (the Manual-vs-Supervised reasoning) — the operator directly
contradicted both (`ESCALATIONS.md` → `ESC-013`): Supervised gates on the
action's own read-only-vs-mutating nature, not on trigger source (a
Supervised agent's read-only action now proceeds immediately for any
trigger; only a write/mutating action proposes-and-waits, for any
trigger); Manual gates on trigger source specifically — a direct human ask
(chat/direct) always executes immediately regardless of the action's
nature, but neither a background/scheduled trigger nor another agent's
Hub-routed request (a new trigger value, `"hub_routed"`, this ADR never
considered) ever executes. This ADR's Decision points 1, 2, 4, 6, 7, and 8
— the two new `.second-brain/` state files and their registry modules
(`working_mode_registry.py`, `pending_approval_registry.py`), the
background-pipeline gate inside `email_classification.py::
run_capture_and_record_completion`, the Approve/Decline endpoints calling
`_execute_action`/`run_capture_for_agent` directly, the `"proposal"`
history-entry kind, and the merged `working_mode` field on `GET
/agents`/`PATCH /agents/{agent_id}` — **remain valid and are reused
unmodified by `ADR-020`.** Read `ADR-020` for the current, correct
chat/direct-action gate and Manual-vs-Supervised design.
**Date:** 2026-08-12
**Context:** `REQ-SB-21-US-01` (`Implementation/UserStories/REQ-SB-21-US-01-
agent-working-modes.md`) requires every agent to carry one of three
working modes — Autonomous (acts immediately), Supervised (proposes and
waits for explicit approval), Manual (dormant until explicitly asked) —
enforced for **both** chat-triggered actions (`ADR-011`'s
`agents_router.py::_invoke_action` funnel) and background/scheduled
pipeline triggers (`ADR-005`'s scheduler, `ADR-008` point 4's shared
hourly tick). Two product questions were operator-resolved before this
pass (`ESC-005`): default mode is Autonomous (behavior-preserving), and
the Supervised background-pipeline approval gets a real, dedicated
Pending Approvals surface built now (approved prototype:
`html-prototype/agents-map.html`'s working-mode picker row and chat
`.chat-proposal` card, `html-prototype/my-day-approvals.html`'s 5th My
Day card + drill-down list). Left genuinely open for this architecture
pass, per the story's own Context: (1) the persistence shape for the new
mutable per-agent mode property; (2) how the existing chat/direct-action
funnel and the existing background-scheduler tick each check mode before
acting; (3) where a "proposed, awaiting approval" record lives and how
Approve/Decline actually execute or discard the deferred action; (4) the
precise mechanical distinction between Manual and Supervised for a
chat/direct-triggered action, since the story's own Scenario 5 text is
ambiguous on this point and the task brief explicitly asked the architect
to resolve it, not guess it. A genuinely new structural question,
distinct from `ADR-014`'s simple mutable-property-plus-CRUD shape:
`email_classification.py::run_capture_and_record_completion` (`ADR-008`
point 4) is a single opaque function the scheduler calls once per tick,
internally composing **both** email-capture's and meeting-capture's
capture steps unconditionally, back to back — introducing a per-agent
gate here means making each of those two calls independently
conditional, without touching `capture_scheduler.py` itself (preserving
`ADR-008` point 4's "capture_scheduler.py requires zero changes, treats
this function as an opaque unit" invariant) and without changing that
function's documented return shape (`ADR-008`/`REQ-SB-08-US-01-T04`'s own
"still exactly the email-results list" constraint).
**Decision:**
1. **New sibling `.second-brain/agent_working_modes.json`, the eighth
   `.second-brain/` state file** (`{"assignments": {<agent_id>:
   "autonomous" | "supervised" | "manual"}}`), extending the existing
   flat-JSON-file convention exactly (`ADR-011`/`ADR-014`'s own files).
   Unlike Sections/Providers, working mode is a **fixed 3-value enum, not
   a user-created catalog** — there is no "list of entities" half to this
   file, only the assignment map, and no non-trivial seed content to
   compute (no starting-5-sections-style default catalog) — so the new
   `app/business/working_mode_registry.py` folds seeding directly into
   its one `_load_state()` helper rather than carrying a separate
   `_seed_state()` function the way `section_registry.py`/
   `provider_registry.py` do; a deliberate, minor simplification, not an
   oversight. Self-healing default assignment is unchanged from `ADR-014`'s
   own pattern: any known agent (`agent_registry.list_agents()`) absent
   from `assignments` is assigned `"autonomous"` (the operator-resolved
   default) and persisted immediately. Exposes `get_agent_working_mode
   (agent_id) -> str` (never `None` — always resolvable, by construction)
   and `set_agent_working_mode(agent_id, mode) -> bool` (`False` if `mode`
   is not one of the three valid values). `app/data_access/vault_writer.py`
   gains the paired `load_working_modes_state()`/`save_working_modes_state()`
   primitives, mirroring `load_sections_state()`/`save_sections_state()`'s
   exact pure-I/O shape (`ADR-003`).
2. **New sibling `.second-brain/agent_pending_approvals.json`, the ninth
   `.second-brain/` state file** — a genuinely different concern from
   working mode itself (a workflow record with a lifecycle, not a
   settable property), so it gets its own sibling module,
   `app/business/pending_approval_registry.py`, rather than being folded
   into `working_mode_registry.py` — the same "one module per concern"
   discipline `ADR-014` already applied to Sections vs. Providers despite
   both living on the same panel. Shape: `{"pending": [{"id": str,
   "agent_id": str, "trigger": "chat" | "direct" | "background",
   "action_id": str | null, "description": str, "status": "pending" |
   "approved" | "declined", "created_at": iso8601, "resolved_at": iso8601
   | null}, ...]}`. `id` is generated via `uuid.uuid4().hex[:12]` — this
   project's first use of the stdlib `uuid` module (no new dependency;
   noted for the record since nothing else in this codebase has needed a
   synthetic id before now — every other entity's id is either a vault
   fact, e.g. Outlook `EntryID`, or a name-derived slug). `action_id` is
   `null` for a `"background"`-trigger proposal (there is no discrete
   action id for "run the scheduled tick" — see point 4). Exposes
   `list_pending_approvals(status=None, agent_id=None)`,
   `get_pending_approval(approval_id)`, `create_pending_approval(agent_id,
   trigger, action_id, description)`, and `resolve_pending_approval
   (approval_id, status)` (sets `status` + `resolved_at`). **Idempotency
   guard for `trigger="background"` only:** `create_pending_approval`
   first checks for an existing unresolved (`status == "pending"`) record
   for the same `agent_id` + `trigger="background"` and returns that
   instead of creating a duplicate — without this, every hourly tick for
   a still-unapproved Supervised background agent would pile up a new
   record on top of the last, unbounded. `trigger in ("chat", "direct")`
   proposals are never deduplicated — each is a distinct, deliberate user
   request, and a user asking twice on purpose is expected, ordinary
   behaviour, not pileup. A **declined** background proposal is not
   suppressed going forward: the next scheduled tick's own idempotency
   check finds no unresolved `"pending"` record (the declined one is
   `"declined"`, not `"pending"`) and proposes again — intentional,
   matching Autonomous's own tick-by-tick semantics (each tick's findings
   are a distinct proposal opportunity), and avoids inventing a
   snooze/suppression mechanism the story's own Non-Goals ("no automatic
   expiry, retry, or reminder behaviour") never asked for.
3. **Chat/direct-action gate: `agents_router.py::_invoke_action` is split
   into a thin gate and the existing unconditional dispatch, renamed
   `_execute_action`.** `_invoke_action(agent_id, action_id, trigger)` —
   `trigger` is a new parameter, `"direct"` from `trigger_action` (the
   Available Actions button) or `"chat"` from `chat`'s matched-phrase
   path — first resolves `working_mode_registry.get_agent_working_mode
   (agent_id)`. **Supervised:** short-circuits — creates a pending-
   approval record (`pending_approval_registry.create_pending_approval`,
   `action_id` set to the real matched action id, `description` composed
   from the agent/action's own display names) and returns `{"status":
   "pending", "message": "Proposed — <action label>. Awaiting your
   approval.", "pending_approval_id": <id>}` — the handler is **never**
   invoked, the same "short-circuit before dispatch, no silent
   fallback" shape `ADR-014` point 7 already established for Provider
   unavailability, applied to a second, independent gating axis ahead of
   it (mode is checked before the Provider-availability check, since a
   Supervised proposal should not reveal an execute-time Provider error
   before the human has even approved it). **Autonomous and Manual: fall
   straight through to `_execute_action`, unchanged from today's
   behaviour** — see point 5 for why Manual does not gate this path.
   `trigger_action` (the direct-button endpoint) and `chat`'s
   matched-action branch both call the gate, not `_execute_action`
   directly — this deliberately extends the Supervised gate to the direct
   Available Actions button too, per the story's own Notes flagging this
   as "not explicitly named in the PRD's acceptance text... but not
   itself blocking, since already funnels through `_invoke_action`" — one
   shared funnel, one shared gate, no second code path to keep in sync.
4. **Background-pipeline gate: two explicit, independent per-agent checks
   inside `email_classification.py::run_capture_and_record_completion`,
   not a generic dispatch loop.** Before each of its two existing internal
   calls (`classify_recent_emails(...)` for `"email-capture"`,
   `meeting_classification.classify_recent_meetings()` for
   `"meeting-capture"`), the function now checks that agent's own working
   mode: **Autonomous** — runs the step exactly as today (via a new small
   shared helper, `run_capture_for_agent(agent_id, limit) -> list`, so the
   scheduled path and the Pending-Approvals-approval path, point 6, below,
   never duplicate the "which function does this agent_id's capture step
   call" mapping); **Supervised** — creates a `trigger="background"`
   pending-approval record (idempotent per point 2) plus a `"proposal"`-
   kind history entry (point 7) instead of running the step; **Manual** —
   skips silently, no record, no history entry at all (this *is* "stays
   dormant," the literal PRD language, for the one trigger context where
   Manual and Supervised are meant to differ — see point 5).
   `capture_scheduler.py` itself requires **zero changes** — this
   conditionality lives entirely inside the one function it already treats
   as opaque, extending (not reopening) `ADR-008` point 4 and `ADR-005`
   exactly the way `ADR-008` point 4 itself already extended `ADR-005`.
   `run_capture_and_record_completion`'s return shape is unchanged (still
   the email-capture results list — empty when email-capture's own mode is
   non-Autonomous, which is new, user-opted-into behaviour, not a
   default-path regression, since Autonomous stays the default per this
   story's own behavior-preservation Constraint). Two explicit sequential
   blocks (email-capture's, then meeting-capture's), not a generic
   per-agent dispatch loop over a dict of handlers, matching this
   codebase's established preference for explicit, repetition-tolerant
   code over cleverness (`section_registry.py`/`provider_registry.py` are
   themselves near-identical siblings, not a shared generic engine).
   `"todo-capture"` is not part of this gate — no real background pipeline
   exists for it yet (`REQ-SB-09` unbuilt); its own future `/plan-tasks`
   pass adds a third block following this exact pattern, the same
   "becomes stale, additive work expected" posture `ADR-011`'s own
   Consequences already named for a newly-real action.
5. **Manual vs. Supervised for a chat/direct-triggered action: Manual
   executes immediately (identical to Autonomous); only Supervised
   proposes-and-waits for this trigger context.** This resolves the
   story's own Scenario 5 ambiguity (its "a trigger... that would
   otherwise cause the agent to act" framing loosely groups a matched
   chat message together with a background trigger, then separately says
   an "explicit ask" is performed — the same event described two ways).
   Second Brain's chat mechanism has exactly one way to "ask" an agent to
   do something — trigger-phrase substring matching against the incoming
   message (`ADR-011`) — there is no second, more "deliberate" request
   channel, and inventing one (e.g. a modal confirming genuine intent)
   would require exactly the NLU/intent-classification capability
   `ADR-007`/`ADR-011` already keep out of this project's own stack.
   A matched chat message or an Available-Actions button press **is**,
   mechanically, "the user explicitly asking the agent to perform a
   specific task" — the PRD's own literal Manual-mode carve-out — so
   there is no remaining context in which Manual should gate that path.
   The one place Manual and Supervised genuinely differ is the background/
   scheduled trigger (point 4): a trigger the user did not, in that
   moment, ask for at all — Supervised surfaces it for a decision, Manual
   silently declines to act on it, both consistent with "stays dormant
   and only acts when the user explicitly asks it to do something."
6. **Approving a pending record executes the deferred action; declining
   discards it — via `_execute_action`/`run_capture_for_agent` directly,
   bypassing the working-mode gate entirely (the approval itself is the
   authorization).** New `app/api/pending_approvals_router.py`,
   `APIRouter(prefix="/pending-approvals")`: `GET /pending-approvals`
   (optional `status`/`agent_id` query filters) and `GET
   /pending-approvals/{id}` — read the store, resolving each record's
   agent display name; `POST /pending-approvals/{id}/approve` — `404` if
   unknown, `409` if already resolved; otherwise, for a chat/direct
   record (`action_id` set), calls `_execute_action(agent_id, action_id)`
   directly (**not** `_invoke_action` — re-entering the gate would find
   the agent still Supervised and create a second pending record instead
   of ever actually running, an infinite-defer bug this design
   deliberately avoids); for a background record (`action_id` is `null`),
   calls the same `run_capture_for_agent(agent_id)` helper point 4
   introduced; either way, marks the record `"approved"` and appends a
   `run_event`-kind history entry with the real outcome. `POST
   /pending-approvals/{id}/decline` — same `404`/`409` checks, marks the
   record `"declined"`, appends a `run_event`-kind entry ("Declined — no
   action taken"), takes no other action (Scenario 3b). Both endpoints
   are agent-agnostic and shared by every UI surface that can trigger
   them — the approved prototype's own inline chat `.chat-proposal`
   state-switcher and the standalone Pending Approvals page both call the
   identical two endpoints, no surface-specific approval mechanism.
7. **Communication history gains one new entry kind, `"proposal"` —
   additive, extends `ADR-011`'s existing `"chat_user" | "chat_agent" |
   "run_event"` enum, does not reopen it.** Created (with the pending
   record's own `id` carried as a new, optional `pending_approval_id`
   field on the history entry — other kinds omit/leave it `null`) at the
   moment a Supervised proposal is created, from either gate (point 3's
   chat/direct path or point 4's background path) — so the unified
   per-agent history timeline shows a proposal the same way regardless of
   what triggered it. The frontend renders a `"proposal"`-kind entry as
   the distinct pending-styled card the approved prototype already shows
   (`.chat-proposal`), and resolves its **live** current status
   (Pending/Approved/Declined) by fetching `GET /pending-approvals/{id}`
   with the entry's own `pending_approval_id` — the history entry's own
   text/kind never change after creation (history is append-only,
   `ADR-011`), only the pending-approval record's own `status` does, so
   the card's state-switcher is driven by that live lookup, not by a
   second history entry per resolution.
8. **`GET /agents`/`GET /agents/{agent_id}` gain a merged `working_mode`
   field; `PATCH /agents/{agent_id}` gains an optional `working_mode`
   body field.** Composition happens at the router, exactly like
   `section_id`/`provider_id` (`ADR-014` point 2) —
   `working_mode_registry.py` is composed *alongside*
   `agent_registry.py`, which stays fully unmodified (`ADR-011` point 2's
   reasoning untouched a second time over). An invalid `working_mode`
   value on `PATCH` returns `400` (a fixed-enum validation failure),
   deliberately distinct from the existing `404 Unknown section/provider`
   pattern (a lookup-against-a-user-created-catalog failure) — the two
   are different failure classes and should read differently to a client.
**Alternatives Considered:**
- **A generic per-agent background-trigger dispatch loop** (a dict
  mapping `agent_id -> capture_function`, iterated generically) instead
  of two explicit sequential blocks — rejected: this codebase's own
  established style favours explicit, repetition-tolerant sibling code
  over a shared generic engine for a small, fixed N (`section_registry.py`/
  `provider_registry.py` themselves are near-identical siblings, not a
  shared engine); with only two real background pipelines today, the
  abstraction buys nothing and costs a layer of indirection future
  readers have to unwind.
- **Manual also gates chat/direct-triggered actions, distinguished from
  Supervised only by not persisting a Pending Approvals record** (e.g. a
  same-turn inline confirmation instead of a durable proposal) —
  rejected: this would make Manual and Supervised behaviourally
  indistinguishable for exactly the trigger context (explicit chat/
  button ask) where the PRD draws its clearest line ("Manual... only
  acts when the user explicitly asks"), and requires inventing a second,
  more "deliberate" request channel this project has no mechanism for
  (`ADR-007`/`ADR-011` explicitly keep intent-classification out of
  scope) — solving an imagined problem with infrastructure this project
  doesn't have.
- **Re-checking working mode on Approve** (so an approval still routes
  through `_invoke_action`) — rejected: since approving a Supervised
  agent's own proposal would immediately re-observe that same agent as
  still Supervised, this produces an infinite-defer bug (approve → propose
  again, never execute) rather than ever actually running the action;
  approval is itself the authorization, so it must call the unconditional
  `_execute_action`/`run_capture_for_agent` directly.
- **Folding `agent_pending_approvals.json` into
  `agent_working_modes.json`, one file, two concerns** — rejected: a
  fixed-enum property and a growing workflow-record list have genuinely
  different shapes and lifecycles (the former never grows past one entry
  per agent; the latter grows and is pruned/queried by status) —
  `ADR-014`'s own "one file per concern" precedent (Sections vs.
  Providers) applies identically here.
- **A snooze/suppression window after a declined background proposal**
  (so the very next tick doesn't immediately re-propose) — rejected as
  exactly the "automatic expiry, retry, or reminder behaviour" the
  story's own Non-Goals explicitly excluded; each tick's own findings are
  treated as a fresh, independent proposal opportunity instead.
- **Rolling the "5th My Day card" Pending Approvals count into `GET
  /my-day/summary`** (extending `app/business/my_day.py`/
  `my_day_router.py`, `REQ-SB-12-US-02`'s own modules) — rejected:
  Pending Approvals is an unrelated, cross-agent workflow concept, not a
  read-only projection over Email/Meeting notes the way My Day's existing
  three sections are; the new dashboard card fetches `GET
  /pending-approvals` directly instead, keeping `my_day.py`/
  `my_day_router.py` (an already-`Done` story's own files) untouched by
  this story entirely.
**Consequences:**
- **Two new `.second-brain/` state files (8th, 9th)** and two new
  business modules (`working_mode_registry.py`, `pending_approval_registry.py`)
  — no new storage technology, extending the existing flat-JSON-file
  convention exactly.
- **`agents_router.py::_invoke_action` is renamed/split**
  (`_execute_action` = today's unconditional dispatch;
  `_invoke_action` = the new gate wrapping it) — every existing internal
  caller (`trigger_action`, `chat`) is updated to call the gate with an
  explicit `trigger` argument; external response shape gains one new
  possible `status: "pending"` value plus a `pending_approval_id` field,
  additive to the existing `{"status": "ok" | "error", "message"}` shape
  `ADR-011`/`ADR-014` already established.
- **`email_classification.py::run_capture_and_record_completion` (already
  governed by `ADR-005`/`ADR-008`) gains per-agent conditionality** — the
  first behavioural change to this function since `REQ-SB-08-US-01-T04`.
  Fully behavior-preserving for the default (Autonomous) case; any
  observable change is opt-in, following a user's own explicit mode
  change away from the default.
- **New API surface:** `app/api/pending_approvals_router.py`
  (`GET`/`POST` as in point 6), registered in `app/main.py`.
- **This project's first use of `uuid`** — a small, stdlib-only, easily
  auditable addition; no new third-party dependency.
- **Composes cleanly with `ADR-015`'s still-unbuilt LangGraph chat path**
  (`REQ-SB-25-US-01`, `status: Ready`, not yet built): `ADR-015` itself
  states `ADR-011`'s keyword-match fast path is "kept, unedited" and only
  `chat`'s no-match fallback body changes — this ADR's gate sits entirely
  on that unedited fast (matched-action) path, so no conflict or rework
  is anticipated when `REQ-SB-25-US-01` ships.
- **A future non-background, non-chat/direct trigger source** (none
  exists today) would need its own explicit `trigger` value and its own
  gate call site — this ADR does not attempt to generalize beyond the two
  trigger sources that actually exist in this codebase today.

## ADR-017: Hub-routing (`REQ-SB-20`) keyword storage & routing-node mechanism — deterministic keyword-substring matching via a new tool-triggered conditional-edge node on `ADR-015`'s existing conversation graph, a new sibling `.second-brain/agent_keywords.json`, kept off the shared MCP server — extends `ADR-015` point 12, does not reopen it

**Status:** Accepted
**Date:** 2026-08-12
**Context:** `ADR-015` point 12 already settled that `REQ-SB-20`'s
Hub-routing *mechanism* moves from a hand-rolled, stand-alone keyword-
substring lookup to "a node on this ADR's graph... using each agent's
declared keywords as that node's own routing input," and recorded that
change as a genuine, factual contradiction of `REQ-SB-20-US-01`'s own
earlier-recorded resolution ("keyword matching, reusing `ADR-011`'s exact
posture... no `ADR-007` tension... no superseding ADR needed") —
`ESCALATIONS.md` → `ESC-010`. Point 12 explicitly left two things open,
in near-identical language to how point 13 left `REQ-SB-26`'s extraction
mechanism open (which `ADR-016` then settled): "Per-agent keyword storage
itself... is not decided here... that is `REQ-SB-20-US-01`'s own
architecture-pass decision to make," and the concrete node/edge shape
implementing the routing decision itself is likewise unspecified beyond
"a node." This ADR is that decision, reached at `REQ-SB-20-US-01`'s own
`/plan-tasks` pass, mirroring `ADR-016`'s own role for `REQ-SB-26` —
extending `ADR-015` point 12, not reopening it. `REQ-SB-20-US-01`'s own
Acceptance Criteria (a keyword field per agent; a cross-Section request
relayed via both Hubs, never agent-to-agent directly; an honest no-match
report; an agent with no keywords never selected) and Constraints
(cross-Section routing only this pass; within-Section routing deferred;
no change to Hermes's own internal Section/Department/Hub concept,
`MEMORY.md`) are the fixed bar this decision must satisfy; the routing
*algorithm* itself (keyword-substring matching, `ADR-011`'s exact
posture) was already operator-resolved before `ADR-015` existed and is
**unaffected** by `ADR-015`'s mechanism-housing change — only the
algorithm's housing and storage are decided here.
**Decision:**
1. **Keyword storage: a new sibling `.second-brain/agent_keywords.json`,
   shaped `{agent_id: [keyword: str, ...]}`** — a flat, per-agent-id-keyed
   list, mirroring `agent_communication_history.json`/`agent_memory.json`'s
   existing "one file keyed by agent_id" shape (`ADR-011`/`ADR-016`), not
   `agent_sections.json`/`agent_providers.json`'s "registry +
   assignments" shape (`ADR-014`), despite `ADR-015` point 12's own
   "most likely... mirroring `agent_sections.json`/`agent_providers.json`'s
   shape" phrasing being merely a suggestion, explicitly deferred to this
   pass. A Section or Provider is a separately identified, renameable
   entity shared by many agents, which is what the registry+assignments
   split is *for* (a rename must not disturb every assignment). A
   keyword list carries no such shared, separately-renameable identity —
   it is free text wholly owned by one agent (the operator's own
   resolution, `REQ-SB-20-US-01`'s Context: "free-text keywords per
   agent, user-assigned... no fixed vocabulary"), so the simpler,
   already-established per-agent-list shape is the closer semantic fit
   and avoids inventing an unnecessary id/slug for something that is
   never itself renamed, listed, or CRUD'd independently of its owning
   agent.
2. **New `vault_writer.py` primitives:** `load_agent_keywords(agent_id:
   str) -> list[str]`, `save_agent_keywords(agent_id: str, keywords:
   list[str]) -> None` (mirrors `load_agent_history`/
   `append_agent_history_entry`'s pure-JSON-I/O shape), and
   `load_all_agent_keywords() -> dict[str, list[str]]` (a new "read the
   whole file" primitive — needed because the routing node, below, must
   scan every *other* agent's keywords, not one agent's own; no existing
   `vault_writer` primitive does a whole-file read for a per-agent-keyed
   store, so this is a new, small, same-shape addition, not a repurposing
   of an existing one).
3. **New business module, `app/business/agent_keywords.py`** (sibling to
   `section_registry.py`/`provider_registry.py`, composed *alongside*
   `agent_registry.py`, which stays unmodified — `ADR-011` point 2's
   "agent identity/type/actions stay hardcoded" reasoning untouched):
   `get_agent_keywords(agent_id) -> list[str]`,
   `set_agent_keywords(agent_id, keywords: list[str]) -> list[str]`
   (whole-list replace semantics, matching the free-text kv-list editing
   UX the Settings panel already uses for other per-agent fields — no
   incremental add/remove-one-keyword endpoint is implied or required),
   and `list_candidate_agents_for_keyword_match(requesting_agent_id: str,
   need_description: str) -> list[dict]` — the actual cross-Section
   keyword-substring matching function the routing node (point 5, below)
   calls; composes `section_registry.get_agent_section`/`list_sections`
   (to exclude the requester's own Section) and `agent_registry.
   list_agents` (to enumerate every known agent), the same "one business
   module composing another" shape already established across this
   codebase (`people_extraction.py` → `customer_hub_linking.py`;
   `meeting_classification.py` → `people_extraction.py`).
4. **Routing algorithm stays exactly `ADR-011`'s posture — deterministic,
   case-insensitive keyword-substring matching, first-match-wins; no LLM
   involved in the match itself.** This is unchanged from
   `REQ-SB-20-US-01`'s own original operator-resolved Constraints — only
   the *housing* of this algorithm changes (point 5), not the algorithm.
   An agent with an empty keyword list is structurally never a match
   candidate (Scenario 4 — an empty list has no substring to test against
   `need_description`), satisfied by construction, not by an explicit
   exclusion check.
5. **Housing: ONE new node, `route_hub_request`, added to `ADR-015`'s
   SAME compiled `app/business/agent_orchestration/graph.py`
   `StateGraph`** (not a second graph — `ADR-015` points 3/9/12's
   "grow by node, not by new graph" convention) — reached via a new
   conditional edge from the existing `call_model` node, triggered when
   the model's own response includes a tool call to a new,
   **orchestration-internal** LangChain tool, `request_cross_section_help
   (need_description: str)`, bound to the model alongside the existing
   vault-query tools (`T07`'s `bound_model = model.bind_tools(tools)`).
   This is this codebase's **first real tool-execution loop** on the
   graph (today's `call_model` binds tools but has no conditional
   edge/loop-back — `bind_tools` without an execution path is, in
   practice, inert for any tool the model actually decides to call): on
   a `request_cross_section_help` tool call, the graph routes to
   `route_hub_request` (point 6, below) instead of `END`, then loops
   back to `call_model` with the routing outcome appended as a
   `ToolMessage`, so the requesting agent's own model composes its final
   natural-language reply incorporating that outcome (an honest no-match
   report, or an acknowledgement a matching agent was found) — Scenario
   3's "honestly reports... rather than fabricating a response" is
   satisfied at the reply-composition layer, on top of the routing
   decision itself already being deterministic (point 4). The module
   also exposes `route_cross_section_request(requesting_agent_id: str,
   need_description: str) -> dict` as a second, directly callable public
   function (alongside `run_agent_conversation`) wrapping the same node
   logic — the same "public entry point, directly testable" convention
   `T07` already established for `run_agent_conversation`'s own non-AC
   smoke-check verification path, so this story's own future tasks can
   verify the routing decision directly without first wiring a live,
   model-driven tool-call trigger end-to-end.
6. **`route_hub_request`'s own body represents the mandatory "own Hub,
   then target Hub" two-hop relay as two sequential lookups inside the
   ONE node** (not two separate LangGraph nodes — see Alternatives for
   why this diverges from `ADR-016`'s two-node read/write split): (a)
   resolves the requesting agent's own Section via `section_registry.
   get_agent_section(requesting_agent_id)` — the first hop, "the
   requesting agent's own Section Hub"; (b) calls `agent_keywords.
   list_candidate_agents_for_keyword_match(requesting_agent_id,
   need_description)` — the second hop, "the target Section's Hub" —
   which scans every other agent whose Section differs from (a)'s result
   (cross-Section only, per this story's own Constraint deferring
   within-Section routing) for a keyword-substring match. Returns
   `{"matched": True, "agent_id": ..., "section_id": ...}` on the first
   match (first-match-wins, `ADR-011`'s existing tie-break convention) or
   `{"matched": False}` on an exhaustive no-match (Scenario 3). Both hops
   are recorded as explicit fields on the routing result (`from_section_
   id`, and either `matched_section_id` or nothing) so "went through both
   Hubs, never agent-to-agent directly" is a real, inspectable property
   of the result, not just a narrative description of the code path — an
   audit-trail entry into `.second-brain/agent_communication_history.json`
   (a new `"hub_routing"` `kind`, mirroring `run_event`'s existing
   audit-log role) recording this outcome is left as ordinary
   `/plan-tasks` implementation latitude for this story's own task
   breakdown, not mandated further here.
7. **The new `request_cross_section_help` tool is NOT registered on the
   shared MCP server (`app/api/mcp_server.py`).** It is defined locally
   inside `agent_orchestration/` (e.g. alongside `graph.py`, as a plain
   `langchain_core.tools` `@tool`-decorated function) and bound directly
   via `model.bind_tools([...vault_query_tools, request_cross_section_
   help])` — never loaded through `mcp_client.py`'s loopback
   `MultiServerMCPClient`, and never one of `vault_query_tools.py`'s or
   `skill_tools.py`'s `@mcp.tool()` registrations. See Alternatives for
   why this diverges from `ADR-015` point 8's "declared exactly once, on
   the shared server, consumed identically by every caller" convention
   for every other tool this codebase has registered so far.
**Alternatives Considered:**
- **Mirror `agent_sections.json`/`agent_providers.json`'s registry +
  assignments shape literally**, as `ADR-015` point 12's own "most
  likely" phrasing suggested — rejected (Decision point 1): that shape
  exists specifically to let a shared, separately-identified entity
  (a Section name, a Provider's connection details) be renamed/edited
  once without walking every assignment; a free-text, per-agent-owned
  keyword list has no such shared identity to protect, so the simpler,
  already-established per-agent-list shape (`agent_communication_
  history.json`/`agent_memory.json`) is the better mirror, not a
  deviation invented without cause.
- **Register `request_cross_section_help` as a new `@mcp.tool()` on the
  shared MCP server**, mirroring `vault_query_tools.py`/`skill_tools.py`'s
  existing registration pattern — rejected (Decision point 7): the
  shared server's entire purpose (`ADR-015` points 7-9) is one tool
  surface reused **identically** by Hermes and the in-app agents; Hermes
  has its own, separate, external Section/Department/Hub concept
  (`MEMORY.md`'s Constraints), and `REQ-SB-20-US-01`'s own Non-Goals are
  explicit that "Second Brain's Hub-routing concept here is its own
  business-logic concept, not a sync with Hermes's." Registering this
  tool on the shared server would hand Hermes a live callable into
  Second Brain's own internal agent-to-agent routing machinery — a
  boundary violation this story's own Non-Goals already rule out, not a
  fresh call this ADR is making independently.
- **An LLM-based (semantic) routing-decision node**, instead of
  deterministic keyword-substring matching, for the match itself —
  rejected (Decision point 4): `REQ-SB-20-US-01`'s own operator-resolved
  Constraints already settled the algorithm as keyword matching reusing
  `ADR-011`'s exact posture, unaffected by `ADR-015`'s housing change
  (`ADR-015` point 12's own text: "they remain satisfiable under either a
  pure string-match or a LangGraph-orchestrated decision node... using
  each agent's declared keywords"); Scenarios 3/4 need a hard
  determinism guarantee (an honest no-match; a no-keyword agent
  structurally never selected) a probabilistic LLM call cannot cleanly
  provide without extra guardrail machinery this story has no basis to
  build, the same reasoning `ADR-011` originally gave for chat
  action-triggering.
- **A standalone hand-rolled Python function outside the graph** (the
  original, now-superseded posture `REQ-SB-20-US-01`'s own Context
  recorded before `ADR-015`) — rejected outright by `ADR-015` point 12
  itself; not re-litigated here.
- **Two separate nodes for the two relay hops** (an "own-Hub" node and a
  "target-Hub" node), mirroring `ADR-016`'s `retrieve_memory`/
  `extract_memory` split — rejected (Decision point 6): `ADR-016`'s split
  was justified because each of its two nodes was a materially separate,
  independently-failable real LLM completion (a genuine decision/failure
  boundary worth its own node). The "own Hub" hop here is a plain,
  never-failing lookup of the requester's own already-known Section — no
  real branch or failure mode of its own — so splitting it into a
  second node would add LangGraph structure with no corresponding
  decision boundary; recording both hops as explicit fields on one
  node's result is proportionate and still makes each hop independently
  inspectable.
- **No tool-call/conditional-edge trigger at all** — expose
  `route_cross_section_request` purely as a standalone public function,
  never wired into the live conversational graph's own tool-calling —
  rejected as the *only* mechanism (though kept as an additional, directly-
  callable entry point, Decision point 5): Scenario 2's "an agent needs
  help... When the request is routed" describes a live, model-observable
  behaviour reachable from within a real agent's own conversation turn,
  not just an internally-testable function; LangGraph's own tool-calling
  is this graph's established mechanism for a model to invoke branching
  behaviour, the whole reason `ADR-015` adopted LangGraph in the first
  place (its own Alternatives: "four separate, genuinely branching,
  stateful capabilities... built independently would each re-implement
  LangGraph's own graph/state/tool-calling abstractions from scratch").
  Exposing the directly-callable function *in addition* costs nothing and
  gives this story's own future tasks the same incremental,
  test-before-wiring-live path `T07` already used for
  `run_agent_conversation`.
**Consequences:**
- **`REQ-SB-20-US-01`'s own Context/Constraints text (recorded before
  `ADR-015` existed) is now reconciled, not left stale** — that story's
  own `## Notes` (updated at this same `/plan-tasks` pass) points at this
  ADR and `ADR-015` point 12 as the now-governing mechanism decision,
  closing `ESCALATIONS.md` → `ESC-010`. Its own Acceptance Criteria are
  unaffected by either `ADR-015` or this ADR (both ADRs' own text already
  confirms this).
- **New files:** `.second-brain/agent_keywords.json` (new state file,
  seeded empty — no starting-keyword seed list, unlike Sections/
  Providers, since free-text keywords have no sensible universal
  default); `app/business/agent_keywords.py` (new). `app/business/
  agent_orchestration/graph.py` gains one new node (`route_hub_request`),
  one new conditional edge (from `call_model`), and one new local tool
  definition (`request_cross_section_help`) — additive to `ADR-015`'s/
  `ADR-016`'s already-built shape; no existing node, edge, or field is
  removed or renamed. `AgentConversationState` (`state.py`) is expected
  to gain whatever routing-outcome field(s) the eventual task-level
  design needs to pass the tool result back into `call_model`'s replayed
  messages — exact field name(s) are ordinary `/plan-tasks`/task-level
  latitude, not decided further here (the same latitude `ADR-016` left
  for its own two nodes' exact prompt wording).
- **This codebase's first LangGraph tool-execution loop** (a real
  conditional edge plus a loop-back to `call_model`, not just an inert
  `bind_tools` call) — a genuine structural precedent future graph
  extensions (`REQ-SB-27`'s skill-invocation nodes, most plausibly) are
  expected to reuse rather than each inventing their own loop shape.
- **`app/api/mcp_server.py`/`vault_query_tools.py`/`skill_tools.py` are
  untouched** by this ADR — the new tool is deliberately kept off the
  shared server (Decision point 7); Hermes's own reachable tool surface
  gains nothing from this story.
- **Does not modify or reopen `ADR-015`** — extends it (point 12) exactly
  the way `ADR-015` point 9 already anticipated, mirroring `ADR-016`'s
  identical role for point 13.
- A `MEMORY.md` decision entry recording this ADR's real-world outcome
  (once actually built and live-verified) is expected at the
  Definition-of-Done step of whichever task first implements
  `route_hub_request` live, per this project's own standing
  coder-updates-`MEMORY.md` convention — not written by this
  architecture pass.

---

## ADR-019: Meetings occurrence dedup key — precise start timestamp + subject (full-string hash), no Outlook-provided identity field at all — supersedes ADR-013 points 1 and 2 (both `EntryID` and `GlobalAppointmentID` are live-falsified as unique-per-occurrence on this Outlook installation)

**Status:** Accepted
**Date:** 2026-08-12
**Context:** This is the **second** superseding ADR for the same Meetings-
occurrence dedup-key decision point in two days, and it says so plainly:
`ADR-008` point 2 chose Outlook `EntryID`; live verification
(`REQ-SB-08-US-01-T03`/`T05`) found a real recurring series' occurrences all
share the exact same `EntryID` (`ESCALATIONS.md` → `ESC-002`). `ADR-013`
then replaced `EntryID` with `AppointmentItem.GlobalAppointmentID` — Outlook's
own documented, guaranteed-unique-per-occurrence identifier, per its own
Object Model documentation — on the reasoning that it was the *other*
Outlook-native identity field with exactly the disambiguating property the
first field lacked. Building and live-verifying that fix
(`REQ-SB-08-US-01-T06`, `SPRINT-017`) found `GlobalAppointmentID` has the
**exact same defect** on this Outlook installation: `item.
GlobalAppointmentID` (the native COM property itself, read the identical
direct-attribute way as `item.EntryID`) returned the same, full, identical
value across all 3 real occurrences of **two** separate real recurring
series ("Weekly Forecast l Strategic Clients" and "Weekly Forecast l Major
Clients") — not a partial/coincidental match, the entire value. The
documented `PropertyAccessor`/DASL fallback for this exact property
(`PidLidGlobalObjectId`'s Extended MAPI tag,
`ADR-013`'s own defense-in-depth mechanism) also **errors on every
occurrence** ("property... is unknown or cannot be found") — not usable as
a fallback disambiguator either. Full reproduction: `ESCALATIONS.md` →
`ESC-012`. **Practical conclusion driving this ADR: two of the two
Outlook-native per-occurrence identity fields this codebase has now tried
have independently failed the same live uniqueness test, on the one real
Outlook installation this project actually runs against.** Continuing to
search for a third Outlook-provided identity field to trust would be
repeating the same category of mistake a third time — an *empirical*
uniqueness claim (Outlook's own documentation says X is unique; live
verification on this installation says otherwise) rather than a
*structural* one. This ADR deliberately stops depending on any
Outlook-provided identity field for occurrence disambiguation at all.
**Operator decision, 2026-08-12:** the technical path was explicitly
delegated ("fix it based on assumptions I don't have an answer for") — this
ADR is that technical decision, reasoned through directly rather than
guessed: the occurrence's own **precise start date+time** (the full
timestamp string `list_calendar_events` already returns as `event["start"]`
— `str(item.Start)`, not the coarse `start[:10]` date-only slice this
codebase's filename scheme has used since `ADR-008`) is not an Outlook
identity-field claim at all — it is a structural fact about what makes two
occurrences *distinct occurrences* in the first place. Two real, separate
occurrences of the same recurring series cannot share an identical exact
start moment; if they ever did, they would not be two occurrences, they
would be the same occurrence. This requires no live re-verification of
Outlook's own behaviour on this installation the way both prior attempts
did, because the guarantee does not come from Outlook's documentation or
COM property implementation at all.
**Decision:**
1. **Primary occurrence dedup/filename key: an 8-hex-char SHA-256 hash
   prefix of `f"{subject}|{start}"`, where `start` is the full, precise
   timestamp string `list_calendar_events` already returns — not any
   Outlook-provided identity field, and not the coarse `start[:10]`
   date-only slice the filename's own display component still uses.**
   Two ingredients, two different jobs: (a) the precise timestamp is what
   disambiguates two distinct occurrences of the *same* recurring series
   (structurally, as argued above); (b) the subject is combined in because
   two *different*, unrelated meetings can genuinely start at the exact
   same instant (a common real calendar case — two separate meetings both
   scheduled for 9:00am), and a timestamp-only key would silently merge
   those two into one note, a new, different collision class neither
   `ADR-008` nor `ADR-013` needed to consider (they always had a
   nominally-per-item Outlook identifier as the key's core, however
   unreliable it turned out to be). Hashing the full combined string,
   not any raw slice, keeps `ADR-013` point 2's already-correct reasoning
   intact (verified working in `REQ-SB-08-US-01-T06`'s own Tests step 2,
   independent of the finding that defeated the rest of that ADR): any
   difference anywhere in the input changes the hash, so no positional
   assumption about where the "varying part" of a date/subject string
   lives is ever load-bearing. `meeting_note_filename_stem(subject, start)`
   drops the trailing identifier parameter entirely — no id of any kind is
   threaded into filename computation any more; `meeting_note_path`,
   `meeting_note_exists`, `create_meeting_note_baseline`, and
   `ensure_meeting_note_baseline_frontmatter`'s call sites are
   re-parametrized to match (`app/data_access/vault_writer.py`).
2. **`app/data_access/outlook_com.py::list_calendar_events` reverts to not
   resolving or depending on any per-occurrence identity field for dedup
   purposes.** `_resolve_global_appointment_id` and
   `_PR_GLOBAL_APPOINTMENT_ID_DASL` (both added by `T06`'s `ADR-013` build)
   are removed — dead code once nothing calls them for a load-bearing
   purpose. The skip-the-event-on-empty-resolution branch `ADR-013`
   required (to guarantee never silently falling back to a known-non-unique
   identifier) is removed along with it — there is no longer any identifier
   resolution step to fail. `list_calendar_events` keeps returning `id`
   (`EntryID`) in its per-event dict, same as before `ADR-013` — informational
   for most purposes, but load-bearing again for one narrow use: Decision
   point 3's legacy-path lookup, below. No `global_appointment_id` field is
   returned any more.
3. **Note-existence resolution: two tiers, not three.** `resolve_meeting_
   note_path(subject, start, entry_id)` checks the new precise-timestamp
   scheme's path first; if not found, falls back to the pre-`ADR-013`
   legacy `EntryID`-suffix path (`ADR-008`'s original scheme, unchanged) —
   whichever is found on disk gets topped up, and only if neither is found
   is a new note created (always under the new scheme). This is
   `ADR-013` point 3's own coexistence mechanism, reused **unmodified** —
   still what protects the 39 already-captured real Meeting notes from
   being duplicated by a forward-only filename-scheme switch, still no
   migration of any of them (they carry no stored calendar identifier in
   frontmatter, same reasoning `ADR-013` already gave). **`ADR-013`'s own
   middle tier — checking a `GlobalAppointmentID`-hash path between the new
   scheme and the legacy `EntryID` scheme — is deliberately dropped, not
   carried forward as a third tier.** This was an explicit design choice,
   not an oversight: `T06`'s own live verification confirmed **zero** real
   Meeting notes were ever created under that scheme (`created: False` for
   every one of the 37 in-window events processed; the vault's Meeting-note
   count and every file's `LastWriteTime` were both confirmed unchanged
   before/after that run) — there is nothing on disk that tier could ever
   match. Keeping it would not be a genuine safety net for real data; it
   would be dead code carrying a live-confirmed defect (`ESC-012`) — if it
   were ever somehow reached, it would reproduce the exact same-date
   collision this whole line of ADRs exists to close, one field removed.
   Dropping it is a pure simplification with zero regression risk against
   real data.
4. **`mark_meeting_processed`'s parameter is renamed to a generic `marker`,
   and its caller now passes the resolved note's own filename stem
   (`note_path.stem`), not a separately-computed identifier value.** Once
   there is no single "the" per-occurrence Outlook identifier the way
   `ADR-008`/`ADR-013` each assumed, computing one specially just for this
   audit-trail call is unnecessary busywork — the note's own filename stem
   is already the exact per-occurrence disambiguator under whichever tier
   `resolve_meeting_note_path` actually resolved (new-scheme hash or legacy
   `EntryID`-suffix), and is always in sync with the path actually used,
   by construction. `app/business/meeting_classification.py::
   classify_recent_meetings` is updated to match: it no longer reads or
   threads a `global_appointment_id` field at all, calls `resolve_meeting_
   note_path(event["subject"], event["start"], event["id"])`, and calls
   `mark_meeting_processed(note_path.stem)`. The file's existing
   heterogeneous entries (`EntryID`-era and `GlobalAppointmentID`-era
   values both, written by earlier code) are left untouched — still an
   append-only audit trail (`REQ-SB-11`), never a schema-enforced lookup
   structure any code path depends on for uniqueness, exactly as `ADR-008`
   and `ADR-013` already established.
**Alternatives Considered:**
- **Keep `GlobalAppointmentID` as a middle fallback tier "in case it's
  occasionally reliable"** (the task brief's own explicitly-offered option)
  — rejected, per Decision point 3's reasoning: zero real notes exist under
  that scheme to ever fall back to, confirmed live, and the field is
  confirmed non-unique-per-occurrence on this installation (`ESC-012`) — if
  the tier were ever reached, it would silently reproduce the exact merge
  defect this line of ADRs exists to close. This is not a safety net with
  low expected value; it is dead code with a live-confirmed landmine inside
  it. Removing it is strictly safer and simpler than keeping it.
- **A composite key combining the precise timestamp with `EntryID` or
  `GlobalAppointmentID`** (e.g. `f"{start}:{entry_id}"`) — rejected, same
  reasoning `ADR-013` already gave for rejecting an `EntryID`+
  `GlobalAppointmentID` composite: both Outlook fields are now confirmed
  non-unique per occurrence on this installation, so either contributes
  zero disambiguating value to a composite key while adding complexity.
  `EntryID` is kept in the legacy-path *lookup*, never mixed into the new
  scheme's own hash input.
- **A raw substring slice of the precise timestamp, mirroring this
  codebase's original `EntryID[-8:]` convention** — rejected: an ISO-shaped
  datetime string's most-varying characters (seconds, then minutes) sit at
  the *end*, so a trailing slice would likely work in practice for this
  specific case, but relying on "likely, in practice" positional luck is
  exactly the reasoning `ADR-013` point 2 already rejected for
  `GlobalAppointmentID`, for good reason — this ADR does not reintroduce
  that same category of fragile assumption just because the specific field
  changed. Hashing the complete `subject`+`start` string removes any
  positional assumption entirely.
- **Investigate whether `GlobalAppointmentID`'s non-uniqueness is specific
  to this one Outlook/Exchange installation or version before abandoning
  it** (one of the open questions `ESC-012` itself named) — deferred, not
  pursued as this pass's fix: this project has exactly one real Outlook
  installation to run against; there is no second mailbox/Outlook build
  available to test on, and delaying a working, low-cost fix to investigate
  root cause on an environment with no accessible alternative to compare
  against is not a good trade for a single-user personal tool. More
  fundamentally, the timestamp-based key needs no such investigation to
  trust, because its uniqueness guarantee is structural (two distinct
  calendar occurrences cannot literally begin at the same instant), not an
  empirical claim about one specific COM property's behaviour on one
  specific installation — which is precisely the category of claim that has
  now failed twice.
- **Accept the current date-only (coarse) disambiguation as a permanent,
  named limitation instead of shipping a further fix** — rejected, same
  reasoning `ADR-013` already gave for rejecting this option: a real,
  low-cost fix is available (this ADR's own design is, if anything, simpler
  than both prior attempts — no COM property resolution, no DASL fallback,
  no per-item skip branch — since it only reads a field `list_calendar_
  events` already returns), and should ship rather than being left as an
  accepted gap for a risk this project has now twice confirmed is real, not
  theoretical.
**Consequences:**
- `app/data_access/outlook_com.py`: `_resolve_global_appointment_id` and
  `_PR_GLOBAL_APPOINTMENT_ID_DASL` removed; `list_calendar_events`'s
  per-item loop no longer resolves or skips on any identity field, keeps
  `id` (`EntryID`), drops `global_appointment_id` from the returned dict;
  docstring updated to describe this (third) dedup-key mechanism honestly,
  naming both prior attempts that were tried and found broken.
- `app/data_access/vault_writer.py`: `meeting_note_filename_stem`/
  `meeting_note_path`/`meeting_note_exists`/`create_meeting_note_baseline`
  drop the trailing identifier parameter entirely (no `entry_id`, no
  `global_appointment_id`); `_legacy_meeting_note_path_by_entry_id` is kept
  unmodified (`ADR-013` point 3, reused); `resolve_meeting_note_path` drops
  to two tiers; `mark_meeting_processed`'s parameter is renamed to the
  generic `marker`.
- `app/business/meeting_classification.py::classify_recent_meetings` no
  longer reads or threads `event["global_appointment_id"]`; calls the
  two-tier `resolve_meeting_note_path` and `mark_meeting_processed
  (note_path.stem)`.
- **None of the 39 real Meeting notes needs migrating** — the legacy-path
  tier is `ADR-013` point 3, byte-for-byte unmodified.
- **Zero regression risk from dropping the `GlobalAppointmentID`-hash
  tier** — confirmed live (`T06`'s own verification): no real note was ever
  created under that scheme, so there is nothing on disk that tier's
  removal could stop matching.
- **`ADR-013`'s own honestly-named residual risk is unchanged by this
  ADR, not newly introduced or newly closed** — a genuinely new occurrence
  landing on the exact same date as one of the pre-`ADR-013` notes, sharing
  that series' stale `EntryID`, would still be misrecognized by the
  legacy-path lookup as the same occurrence (`ADR-013`'s Consequences
  already named this, bounded to the 38/39 already-known dates, shrinking
  over time, closeable only by a full migration this ADR does not
  undertake either). This ADR closes the *forward* risk (every occurrence
  captured from here on gets a structurally-guaranteed-unique key,
  regardless of which Outlook identity field does or does not behave as
  documented) — it does not retroactively close the legacy tier's own
  narrow gap.
- `REQ-SB-08-US-01-T06`'s own task file is redesigned in place around this
  ADR (superseding its own prior `GlobalAppointmentID`-based `## Files to
  Modify` spec) — `status:` reset `Blocked → Ready`.
- `architecture.md`'s "Meeting Notes & Calendar-Attendee Extraction
  (REQ-SB-08)" → "Occurrence dedup key" bullet is rewritten a third time
  (this same pass) to describe this mechanism.

**Correction note, 2026-08-12 (post-build, `T06`'s own live verification):**
this ADR's Decision point 3 and the "Alternatives Considered" entry above
both stated "zero real notes exist under the `GlobalAppointmentID`-hash
scheme" as the justification for dropping that tier outright. `T06`'s
rebuild found this was true only at the time this ADR was written — a
real note (`TAQA - Mubadala _ Forecast - Weekly connect
-2026-08-12-a2a34c05.md`) was created under that scheme by an unattended
scheduled capture run that happened *between* this ADR being written and
`T06`'s rebuild session (the old code was still live in that window).
This does **not** change the decision itself — the tier's removal is
still correct (the field remains confirmed non-unique-per-occurrence,
`ESC-012`; keeping a tier with a live-confirmed defect for one
retroactive note is not a reasonable trade) — it only corrects the
factual claim of zero instances to "zero as of this ADR's own
authoring; one real, bounded, human-recoverable instance surfaced during
the gap before rebuild." No code change results; the one affected note
needs a manual human glance (delete/merge against its own successor,
`...-986eee44.md`) — not automated here.

## ADR-020: Working-mode gating corrected — Supervised gates on the action's own read-only-vs-mutating nature, Manual gates on trigger source; new `mutates` classification on `agent_registry.py`'s action definitions — supersedes ADR-018 points 3 and 5 only

**Status:** Accepted
**Date:** 2026-08-12
**Context:** `ADR-018` (`REQ-SB-21-US-01`, Working Modes) was built on two
unconfirmed architect judgement calls, later directly contradicted by the
operator (`ESCALATIONS.md` → `ESC-013`): Decision point 3 gated Supervised
uniformly by **trigger source** (chat/direct **and** background alike,
regardless of whether the action reads or writes), and Decision point 5
resolved Manual-vs-Supervised for a chat/direct trigger by treating any
matched chat message or Available-Actions button press as "the user
explicitly asking," identically to Autonomous, with no consideration of a
future Hub-routed (agent-to-agent) trigger at all. Asked to confirm this
reading before any code was built (`REQ-SB-21-US-01` was still `Draft`,
never shipped), the operator gave materially different, authoritative
semantics directly, quoted in full in `REQ-SB-21-US-01`'s own `## Context`
and `ESC-013`:
- **Supervised:** "It is running — but some writing or modifying needs my
  approval" — the agent operates and responds normally/immediately for
  read-only/query actions; only actions that write or modify something
  require approval first, **regardless of what triggered them** (chat,
  direct button, or background).
- **Manual:** "Can't Pull unless I asked him to... No Agent can Trigger an
  Action" — only a *direct human* ask counts as "asked" — a
  scheduled/background trigger does not run it (already correctly resolved
  in `ADR-018` point 4, not reopened here), and **neither does another
  agent's Hub-routed request** (`ADR-017`, `REQ-SB-20`) — a trigger source
  `ADR-018` never considered as a gate input at all. `ADR-017`'s own
  routing-node design, as built, only ever returns a matched-candidate
  description to the requester; it never itself invokes an action on the
  target agent (confirmed directly by the operator: "It can be Offered but
  it doesn't execute — We will get to this Part when we reach this level of
  the product," `ESC-013`'s own mid-pass update) — so gating this trigger
  source today is provably a no-op, not dead code: it is forward-looking
  correctness for the day a future story lets a routed request actually
  invoke the target's action, recorded now rather than re-discovered later.
This is a genuinely different gating **axis** for Supervised (the action's
own nature, not what triggered it) — `app/business/agent_registry.py`'s
action definitions carry no read/write classification at all today, so
this requires a real, new, small piece of structure, not a parameter
tweak. Live inspection of `app/business/agent_registry.py`'s actual
declared actions (5 agents, 12 action entries, 4 distinct action ids)
confirms the classification is not guessable from the id/label alone in
every case — see Decision point 1.
**Decision:**
1. **New `"mutates": bool` field on every action definition dict in
   `app/business/agent_registry.py`'s static `AGENTS` catalog** — the
   simplest possible shape for a small, fixed, hardcoded action list
   (mirrors `ADR-011` point 2's "agent/action identity is app
   configuration, not vault content, and stays hardcoded" reasoning
   exactly one field further; **not** a persisted/mutable concern the way
   Sections/Providers/Working-mode are, since which actions exist and
   whether they write are structural facts about the codebase, not user
   preference). Classified from each action's real current behaviour
   (`app/api/agents_router.py`'s `_ACTION_HANDLERS` mapping and each
   agent's own PRD-sourced settings/description — not guessed from the id
   string alone):
   - `run_capture_now` (email-capture, meeting-capture, todo-capture) →
     `"mutates": True` — files new notes into the vault
     (`email_classification.run_capture_and_record_completion`/
     `meeting_classification.classify_recent_meetings`); the one action
     with a real handler today (`ADR-011`).
   - `pause_schedule` (email-capture, meeting-capture, todo-capture) →
     `"mutates": True` — changes the agent's own future scheduled
     behaviour (a control-plane state change), even though it has no real
     handler yet (`ADR-011` point 3's "declared but not yet backed"
     pattern) and does not itself touch vault content — classified
     conservatively as a write because it is not read-only by any
     reasonable reading, and the corrected Supervised semantics' own
     illustrative parenthetical ("the vault, an external system") is
     descriptive of the common case, not an exhaustive allow-list; a
     control-plane mutation is still a mutation.
   - `view_last_run` (email-capture, meeting-capture, todo-capture,
     people-producer) → `"mutates": False` — reads and reports the last
     recorded run outcome, writes nothing.
   - `rebuild_person_note` (people-producer) → `"mutates": True` — writes
     (overwrites/regenerates) a Person note in the vault
     (`people_extraction`'s own build path).
   - `ask_question` (vault-qa) → `"mutates": False` — a read-only query;
     the agent's own declared `settings` say so explicitly ("Write access:
     Read-only here (see REQ-SB-04 for write scope)").
   - `view_channel_status` (vault-qa) → `"mutates": False` — a read-only
     status check.
   A new `agent_registry.get_action(agent_id, action_id) -> dict | None`
   helper is added (a plain dict lookup over the existing static `AGENTS`
   structure — no new state, no new file) so the gate (point 2) has one
   place to resolve an action's `mutates` flag without duplicating the
   nested-list search inline. **Fail-safe default:** if `get_action`
   returns `None` (an action id not found in the static catalog — should
   not happen for any id reachable through the existing chat/direct
   funnel, but defensive against a future mismatch) or an action dict ever
   omits the field, the gate treats it as `mutates: True` — an unknown
   action is gated as if it writes, never silently allowed through,
   matching this project's existing "honest refusal over silent
   fabrication" posture (`ADR-011` point 3, `ADR-014` point 7).
2. **`agents_router.py::_invoke_action`'s gate is corrected to check BOTH
   axes — the action's own `mutates` classification (for Supervised) and
   the trigger source (for Manual) — replacing `ADR-018` point 3's
   single trigger-source check.** `_invoke_action(agent_id, action_id,
   trigger)` — `trigger` is now `"chat" | "direct" | "hub_routed"` inside
   this funnel (background never reaches `_invoke_action`; it has its own
   separate gate, `ADR-018` point 4, kept unmodified — see Consequences).
   Corrected order:
   1. Resolve `mode = working_mode_registry.get_agent_working_mode
      (agent_id)` and `action = agent_registry.get_action(agent_id,
      action_id)` (point 1's fail-safe default applies if `None`).
   2. **Manual, trigger `"hub_routed"`:** refuse — no pending-approval
      record, no execution — mirroring `ADR-018` point 4's existing
      "Manual skips silently" background behaviour, now also covering the
      Hub-routed trigger source (`REQ-SB-21-US-01` Scenario 5b). Today this
      branch is unreachable in practice (`ADR-017`'s routing node never
      calls `_invoke_action` with `trigger="hub_routed"` — see Context) —
      kept, not dropped, as the named future-proofing point above.
   3. **Supervised, `action["mutates"] is True`:** short-circuits exactly
      as `ADR-018` point 3 already did — creates a pending-approval record
      (`pending_approval_registry.create_pending_approval`, unchanged
      shape) and returns the same `{"status": "pending", ...}` response —
      **now regardless of `trigger`** (`"chat"`, `"direct"`, or
      `"hub_routed"`), not only for a specific trigger value.
   4. **Supervised, `action["mutates"] is False`:** falls straight through
      to `_execute_action`, identical to Autonomous — the corrected
      behaviour `ADR-018` point 3 did not have at all (it gated every
      chat/direct action uniformly, read-only or not).
   5. **Autonomous (any trigger), Manual (`"chat"`/`"direct"` trigger):**
      fall straight through to `_execute_action`, unchanged from `ADR-018`
      point 5's own conclusion — a matched chat message or an
      Available-Actions button press remains the one mechanism this
      codebase has for "the user explicitly asking" (`ADR-007`/`ADR-011`,
      no NLU), so Manual still executes immediately on either, regardless
      of whether the action reads or writes (`REQ-SB-21-US-01` Scenario 5's
      corrected "whether the action is read-only or write/mutating" text).
3. **New trigger value, `"hub_routed"`, added alongside the existing
   `"chat"`/`"direct"`/`"background"` on the shared trigger enum used by
   both `_invoke_action` and `pending_approval_registry`'s pending-record
   `trigger` field** — `ADR-018` point 2's `agent_pending_approvals.json`
   schema (`"trigger": "chat" | "direct" | "background"`) is extended to a
   fourth value, not restructured; no existing record's shape changes.
   This is the concrete future-proofing named in Context: the day a future
   story lets a Hub-routed request actually invoke an action on its
   target agent, it calls `_invoke_action(agent_id, action_id,
   "hub_routed")` and both gates (Manual's refusal, Supervised's
   mutates-check) apply automatically, with no further gate-logic change
   needed — only the new call site.
4. **`ADR-018` point 4 (the background-pipeline gate inside
   `email_classification.py::run_capture_and_record_completion`) is
   extended, not reopened, and needs no structural change.** Both
   background-triggered steps it gates (`classify_recent_emails` for
   `"email-capture"`, `meeting_classification.classify_recent_meetings()`
   for `"meeting-capture"`) are, today, always `"mutates": True` actions
   (they file notes) — so Supervised's corrected mutates-based rule and
   `ADR-018`'s original trigger-based rule produce the **identical**
   outcome for the background trigger by construction (Supervised
   proposes-and-waits; Manual skips silently) — the behavioural change
   introduced by this ADR is real but entirely confined to the chat/direct
   funnel (point 2), where a Supervised agent's *read-only* actions now
   proceed immediately instead of always proposing. Should a future
   read-only background pipeline ever exist, this gate would need its own
   `mutates`-aware update at that time — not a gap in this ADR, since no
   such pipeline exists today (`"todo-capture"` remains outside this gate
   entirely, unbuilt, per `ADR-018` point 4's own note).
**Alternatives Considered:**
- **Derive `mutates` from the action id/label via a naming convention**
  (e.g. any id starting with `run_`/`rebuild_` mutates, anything starting
  with `view_`/`ask_` does not) instead of an explicit field — rejected:
  `pause_schedule` is the counter-example that breaks this rule (it
  neither runs nor rebuilds anything, yet is a real control-plane
  mutation) — an explicit, reviewable field per action is more honest than
  a naming convention this catalog has already shown does not hold
  universally, and costs nothing extra to maintain on a small, fixed,
  hardcoded list.
- **A separate `mutating_action_ids: set[str]` sibling structure in
  `agent_registry.py`, parallel to `AGENTS`** (mirroring
  `provider_registry.py`'s `has_real_client`'s small hardcoded-set
  pattern) instead of a per-action field — rejected: the classification is
  a property of the *action*, already nested inside `AGENTS`; a parallel
  keyed-by-what structure (agent id? action id? both, since the same
  action id like `run_capture_now`/`view_last_run` repeats across three
  agents with identical semantics each time) invites drift between the two
  structures with no compensating benefit — a field on the action dict
  itself cannot drift out of sync with the action it describes.
- **Fail-open (`mutates: False`) instead of fail-safe (`mutates: True`)
  for an unresolvable action** — rejected: the entire point of this ADR is
  that a write/mutating action must never execute without approval under
  Supervised; defaulting an unknown action to "safe to auto-run" is
  exactly backwards from the risk this correction exists to close, even
  though the specific failure mode (an action id reachable through the
  funnel but absent from the static catalog) should not occur in practice
  given today's code.
- **Making `mutates` a persisted, user-editable per-agent-action property**
  (a tenth `.second-brain/` state file, mirroring `ADR-014`'s Sections/
  Providers shape) instead of a static field on `agent_registry.py` —
  rejected: whether an action writes or reads is a structural fact about
  what the action's own code does, not a user preference or configuration
  choice the way Section/Provider/working-mode assignment are — no PRD
  acceptance text or operator direction asks for a user to reclassify an
  action's own read/write nature, and doing so would let a user
  misconfigure a genuinely write/mutating action as `False` and silently
  defeat Supervised's entire safety purpose.
- **Gate the background pipeline by the same explicit `mutates`-lookup
  call the chat/direct funnel now uses, rather than leaving `ADR-018`
  point 4's own logic as-is** — considered, not adopted: since both
  real background-triggered steps are unconditionally mutating today, the
  observable behaviour is identical either way; leaving `ADR-018` point
  4's already-`Accepted`, already-correct logic untouched avoids
  re-touching frozen, working code for a change with zero present
  behavioural effect (kept as a named follow-up if a read-only background
  pipeline is ever added, per Decision point 4).
**Consequences:**
- **`app/business/agent_registry.py`** gains a `"mutates": bool` field on
  every action dict (6 distinct action definitions, 12 total entries
  across 5 agents) and a new `get_action(agent_id, action_id) -> dict |
  None` lookup helper — still a fully static, hardcoded module; `ADR-011`
  point 2's "agent identity/actions are app configuration, not vault
  content, and stay hardcoded" claim is unaffected, only extended by one
  descriptive field.
- **`agents_router.py::_invoke_action`'s gate logic changes shape** from a
  single trigger-source switch (`ADR-018` point 3) to a two-axis check
  (mutates-for-Supervised, trigger-for-Manual) — the only externally
  observable behavioural change is that a Supervised agent's read-only
  chat/direct action (`view_last_run`, `ask_question`,
  `view_channel_status`) now executes immediately instead of always
  proposing; every other combination's observable outcome is unchanged
  from `ADR-018`'s original design.
- **`agent_pending_approvals.json`'s `trigger` enum gains a fourth value,
  `"hub_routed"`** — additive, no migration of existing records; no code
  path produces it yet (see Decision point 3).
- **`ADR-018` points 1, 2, 4, 6, 7, 8 are unaffected and remain in full
  effect, unedited** — the two new `.second-brain/` state files and their
  registry modules, the background-pipeline gate, the Approve/Decline
  endpoints calling `_execute_action`/`run_capture_for_agent` directly
  (bypassing the gate, avoiding the infinite-defer bug), the `"proposal"`
  history-entry kind, and the merged `working_mode` field on `GET
  /agents`/`PATCH /agents/{agent_id}` all stand exactly as `ADR-018`
  specified them. `ADR-018` itself is not edited (append-only, per this
  file's own rule) — its `Status:` line is updated to record this partial
  supersession, naming points 3 and 5 specifically, mirroring `ADR-013`'s
  own "points 1 and 2 only" precedent.
- **Resolves `ESCALATIONS.md` → `ESC-013`** — the operator's directly-
  quoted corrected semantics are now the governing design, recorded
  architecturally rather than only in the story's own re-specced
  Acceptance Criteria.
- **The decomposer's next pass over `REQ-SB-21-US-01` re-derives `T04`/
  `T05`'s task scope against this corrected gate** — the story's own
  Implementation Tasks table already flags the prior `T01`-`T08` set as
  stale pending this ADR; that re-derivation is the decomposer's job, not
  this architect pass's.
- Closes `ESCALATIONS.md` → `ESC-002` and `ESC-012` at the design level —
  both still require `T06`'s own live rebuild and re-verification to close
  operationally, per this project's existing "design vs. built-and-verified"
  distinction.
- **Named plainly, not glossed over:** this is the second superseding ADR
  for the same decision point in two days. `ADR-013` was a reasonable,
  honestly-argued fix for a real, confirmed defect (`ESC-002`) that turned
  out to share its own root cause with the thing it replaced — trusting an
  Outlook-documented identity-field uniqueness guarantee that this specific
  installation does not honor. This ADR's own design does not repeat that
  category of risk: its uniqueness guarantee does not depend on Outlook's
  behaviour, documented or otherwise, being trustworthy on this or any
  other installation.

---

## ADR-021: Vault Filing Expert — a new registry agent with an LLM-reasoned, methodology-grounded placement decision, a deterministic Tier-1 write path, and a Tier-2 new-top-level-area approval override that bypasses the working-mode gate entirely — extends `ADR-004`, `ADR-011` point 2, `ADR-015`, and `ADR-018` (unedited points), does not reopen any of them

**Status:** Accepted
**Date:** 2026-08-12
**Context:** `REQ-SB-35-US-01` (`Implementation/UserStories/REQ-SB-35-US-01-
vault-filing-expert.md`) needs a distinct registry agent, reached via
`REQ-SB-20`'s Hub routing (operator-confirmed, "This is an Agent"), that
decides where new content belongs in the vault — an existing category if
one genuinely fits, a new tag/subfolder within an existing top-level area
if it doesn't (Tier 1, autonomous), or a genuinely new top-level vault area
(Tier 2, pauses for the operator's explicit approval regardless of the
agent's own configured working mode). This is genuinely new ground: no
agent in this codebase currently makes a write *decision* — every existing
mutating action (`run_capture_now`, `rebuild_person_note`) has a fixed,
predetermined target shape; this is the first agent whose whole job is to
*decide* a target shape from open-ended content, grounded in
`Documentation/References/beyond-the-second-brain-methodology.md` and the
vault's own live structure, then write to it. It is also the first agent
action whose approval requirement is **independent of the agent's own
working mode** — every existing Supervised/Manual gate design (`ADR-018`,
`ADR-020`) keys off either the action's own `mutates` flag or the trigger
source, both scoped by a per-agent mode setting; Tier 2 must pause
*regardless* of that setting, per the operator's own explicit words ("not a
change to the agent's own general working-mode assignment").

**A real, load-bearing gap was found live during this pass, not assumed
away:** `REQ-SB-35-US-01`'s own `## Dependencies` states "`REQ-SB-21-US-01`/
`ADR-020` (Done) — ... Already `Done`, so this dependency is satisfied."
Direct inspection of `Implementation/UserStories/REQ-SB-21-US-01-agent-
working-modes.md`'s own frontmatter (`status: Draft`, `gate: flagged`) and
of the real `src/backend` source tree (no `app/business/
pending_approval_registry.py`, no `app/business/working_mode_registry.py`,
no `app/api/pending_approvals_router.py`, no `working_mode`/`mutates`
handling anywhere in the real `app/api/agents_router.py`) confirms this
claim is **factually wrong** — `REQ-SB-21-US-01` was reset `Ready → Draft`
after `ADR-020` corrected `ADR-018`, and its decomposer has not yet
re-run; none of its 8 tasks have been built. `ADR-018`'s Pending-Approvals
*design* (points 1, 2, 4, 6, 7, 8 — the state files, the registry modules,
the `uuid`-based id, the Approve/Decline endpoints, the `"proposal"`
history-entry kind) remains `Accepted` and unedited by `ADR-020`, so this
ADR designs Tier 2 against that shape with confidence — but the
**implementing code does not exist yet**. This is recorded honestly as a
real, blocking prerequisite for Tier 2's own coder task (mirroring
`ESCALATIONS.md` → `ESC-011`'s precedent — a real dependency that cannot
yet be wired to a real, `Ready` task) in `ESCALATIONS.md` → `ESC-017`, not
silently patched or asserted satisfied.

**Decision:**

1. **New registry agent, `"vault-filing-expert"`** (type `expert`), added
   as a plain new entry to `app/business/agent_registry.py`'s already-
   static `AGENTS` dict — no change to `agent_registry.py`'s own shape or
   to `ADR-011` point 2's "agent identity/type/actions stay hardcoded"
   reasoning. Reached by other agents exclusively via `REQ-SB-20`/`ADR-017`'s
   already-real, directly-callable `graph.route_cross_section_request(...)`
   — assigned a Section and a keyword set (e.g. `"filing"`, `"tags"`,
   `"vault placement"`, `"categorize"`) like any other agent, exact values
   left to the decomposer/coder (ordinary configuration, not an
   architectural fork).
2. **New business module, `app/business/vault_filing_expert.py`**
   (sibling to `people_extraction.py`/`partner_hub_linking.py` — a
   one-module-per-concern shape, `ADR-003`), exposing one public entry
   point: `determine_placement_and_file(content: str, source_description:
   str, requesting_agent_id: str) -> dict`. Internally:
   - **Grounding is deterministic context injection, not a bound-tool
     reasoning loop.** The function pre-fetches `vault_query_tools.
     list_known_kinds()`/`list_known_customers()`/`list_known_partners()`
     directly (plain Python calls, not an LLM tool-call round-trip) and
     embeds the result plus a condensed excerpt of `beyond-the-second-
     brain-methodology.md`'s own principles (atomic notes, output-
     orientation, tags-for-multidimensional-attributes,
     extensibility-over-enumeration, `ADR-004`'s tag/folder split) into one
     prompt, then issues **one** completion via `model_factory.
     resolve_agent_model("vault-filing-expert")` (the exact same
     Provider-honesty funnel-gate `_call_model`/`_extract_memory` already
     use — an unavailable Provider returns Scenario `N/A`'s honest
     unavailability, never a fabricated placement) asking for a
     structured decision: `{"kind": str, "is_new_top_level_area": bool,
     "tags": list[str], "filename_stem": str, "body": str, "confidence":
     "high" | "low", "uncertainty_note": str | null}`. Chosen over binding
     `list_known_kinds`/etc. as tools the model decides whether to call —
     the three lists are always needed for a correct decision, so
     pre-fetching them removes any risk of the model skipping the lookup
     and guessing instead (this project's own "prefer a real deterministic
     call over hoping the model chooses to tool-call" precedent, `ADR-016`'s
     `extract_memory` reasoning applied one layer over).
   - **`is_new_top_level_area` is computed by set membership, not asked as
     an open question the model could get wrong about the codebase's own
     rules:** the prompt instructs the model to set it `True` only when
     `kind` is not already present in the pre-fetched `list_known_kinds()`
     result — the model still *chooses* `kind`, but the Tier boundary
     itself (`kind in list_known_kinds()`) is re-checked in Python after
     the completion returns, never trusted from the model's own boolean
     alone (an honest belt-and-braces check, not a distrust of the model's
     placement judgment itself).
   - **Tier 1** (`kind` already known, or `is_new_top_level_area is
     False`): writes immediately via `vault_writer.write_note(f"Work/
     {kind}", filename_stem, frontmatter, body)` — the same fully generic
     primitive already used by every specialized note type; no new
     `data_access` primitive is required, since `write_note`'s own
     `target_dir.mkdir(parents=True, exist_ok=True)` already creates a
     brand-new `Work/<kind>/` folder transparently the first time a
     genuinely new tag/subfolder-level category is used within Tier 1's
     own bound (a new *tag value* inside an existing area, or a follow-on
     note under a kind that already exists — Tier 1 never needs a
     structurally new top-level root). Every wikilink/tag obligation
     (`MEMORY.md`'s standing tags-and-wikilinks rule) is satisfied by the
     model's own returned `tags`/`body` content plus, where the content
     references an existing vault entity (e.g. a customer/partner hub),
     reusing `customer_hub_linking`/`partner_hub_linking`'s existing
     granular primitives — left to the decomposer/coder as ordinary
     composition, not a new mechanism.
   - **Scenario 6 (honest uncertainty):** when the model's own
     `confidence` is `"low"`, the written note's body is prefixed with a
     visible marker (exact copy left to the coder) sourced verbatim from
     `uncertainty_note` — never silently dropped, never presented as a
     settled decision. This never affects the Tier decision itself
     (independent axis, per the story's own Constraints).
3. **Tier 2 bypasses the working-mode gate by construction, not by an
   override flag on it.** `determine_placement_and_file`'s Tier-2 branch
   is reached by a code path that never goes through `agents_router.py::
   _invoke_action`'s chat/direct/hub_routed funnel at all (this function is
   called directly by whatever orchestration invoked the Vault Filing
   Expert — see `ADR-023`) — so there is no working-mode check to bypass;
   the branch **unconditionally** calls `pending_approval_registry.
   create_pending_approval(agent_id="vault-filing-expert", trigger=
   "direct", action_id="propose_new_top_level_area", description=...)`
   regardless of `working_mode_registry.get_agent_working_mode(
   "vault-filing-expert")`'s own value. This is the concrete mechanism
   satisfying the operator's own "not a change to the agent's own
   general working-mode assignment" framing: the exception lives in *which
   code path this action takes*, not in a per-mode override rule layered
   onto `ADR-020`'s existing gate.
4. **`ADR-018`'s Pending-Approvals record schema
   (`agent_pending_approvals.json`) gains one additive field, `"payload":
   dict | null`** — carrying whatever structured data the deferred action
   needs to actually execute once approved (here: `content`,
   `source_description`, the model's own proposed `kind`/`tags`/
   `filename_stem`/`body`). This is a genuine, necessary extension beyond
   `ADR-018`'s original scope (which only ever re-dispatched an
   `agent_registry`-declared action with no payload of its own, via
   `_execute_action`/`run_capture_for_agent`) — `propose_new_top_level_area`
   is not an `agent_registry` action and carries real content that must
   survive from proposal to resolution. Additive (`null` for every
   existing record shape `ADR-018` already defined), so no migration of
   any hypothetical already-existing record is needed.
5. **`app/api/pending_approvals_router.py`'s `POST /pending-approvals/{id}/
   approve` gains a second dispatch path, parallel to its existing
   `_execute_action`/`run_capture_for_agent` re-dispatch** — a small,
   explicit `_APPROVAL_HANDLERS: dict[str, Callable]` keyed by `action_id`
   (mirrors `agents_router.py`'s own `_ACTION_HANDLERS`/`skill_registry.py`'s
   own `_SKILL_HANDLERS` dispatch-table convention exactly), with
   `"propose_new_top_level_area": vault_filing_expert.
   finalize_new_top_level_area` — a second public function on the same
   module, taking the pending record's own stored `payload` and performing
   the actual `write_note` call only once approved. **Decline** (Scenario
   4) takes no further action beyond `ADR-018`'s existing
   `resolve_pending_approval(approval_id, "declined")` — the content is
   never filed under the declined area, and is not silently retried
   elsewhere (the story's own explicit Scenario 4 text); the calling
   orchestration (`ADR-023`) surfaces the decline honestly rather than
   inventing an alternative location.

**Alternatives Considered:**

- **Bind `list_known_kinds`/`list_known_customers`/`list_known_partners` as
  tools the model decides whether to call** (reusing `call_model`/
  `_execute_tools`'s existing tool-loop mechanics as-is) — rejected: those
  three lookups are unconditionally required for *any* correct placement
  decision, so leaving the model free to skip them risks exactly the
  "stretch-fit guess" the story's own Acceptance text warns against; a
  deterministic pre-fetch removes that risk entirely for a decision this
  consequential (it gates a real vault write).
  - **A shared skill (`REQ-SB-27`), not a distinct registry agent** — the
  originally-open question at `/spec` time, since resolved directly by the
  operator ("This is an Agent") before this pass began; not re-litigated
  here.
- **A blanket per-agent working-mode-independent flag on `agent_registry.py`
  actions** (a new `"always_requires_approval": bool` field, checked inside
  `_invoke_action`'s gate alongside `mutates`) — considered, then rejected:
  `propose_new_top_level_area` is never reached through `_invoke_action`'s
  funnel at all (it's a business-function call, not a chat/direct/hub-
  routed agent action), so adding a field `_invoke_action` would need to
  check, for a code path that never calls `_invoke_action`, would be dead
  configuration — the "bypass by construction" design (point 3) achieves
  the identical observable behaviour with strictly less surface.
- **A brand-new, parallel approval-workflow store, separate from
  `ADR-018`'s `agent_pending_approvals.json`** (since Tier 2's payload need
  is structurally different from every existing use) — rejected: the
  *lifecycle* (pending → approved/declined, one durable record, one
  Approve/Decline pair of endpoints) is identical to `ADR-018`'s already-
  designed mechanism; only the record's own payload richness differs, which
  an additive field solves without duplicating the entire workflow concept
  a second time.
- **Skip Tier 2's approval-payload persistence; re-run the whole placement
  decision fresh at Approve time instead of storing the model's own prior
  output** — rejected: re-running the LLM completion a second time (a)
  costs a second real Provider call for no benefit, and (b) risks a
  different decision the second time (the model is not guaranteed
  deterministic across calls), which would silently disconnect what the
  operator actually reviewed/approved from what gets written — the stored
  `payload` is exactly what was proposed and exactly what the operator is
  approving.

**Consequences:**

- `app/business/agent_registry.py` gains one new agent entry (data only,
  no shape change) and, for the Tier-2 resolution path, `pending_approval_
  registry.py`'s schema gains one additive field — neither reopens
  `ADR-011` point 2 or `ADR-018`'s own `Accepted` design.
- **Tier 2's coder task has a real, currently-unmet blocking prerequisite:**
  `REQ-SB-21-US-01` must actually ship (`pending_approval_registry.py`,
  `agent_pending_approvals.json`, `pending_approvals_router.py`) before
  `finalize_new_top_level_area`/the `_APPROVAL_HANDLERS` dispatch can be
  built or verified. Tier 1 (Scenarios 1, 2, 5, 6, 7, 8) has no such
  dependency and can be built and verified independently — see
  `ESCALATIONS.md` → `ESC-017` for the decomposer-facing detail on how to
  sequence this without a fabricated task-ID reference.
- A future second Tier-2-shaped action (any other "always pauses regardless
  of mode" decision) reuses the same `payload` field and
  `_APPROVAL_HANDLERS` dispatch-table pattern rather than inventing a third
  approval mechanism.
- The Vault Filing Expert's own real Provider call (for the placement
  completion) is a second per-invocation LLM cost/latency, the same
  accepted trade-off `ADR-016`'s memory-extraction completion already
  named for a personal, single-user assistant at today's expected volume.

---

## ADR-022: Real Anthropic Provider integration for the web-research skill — a plain `anthropic` SDK client in `data_access` (not `model_factory.py`/LangChain), extends `ADR-014` point 7's honesty gate and `REQ-SB-27-US-01`'s skill plumbing; closes a live-discovered skill-access tool-binding gap in `ADR-015`'s conversational graph

**Status:** Accepted
**Date:** 2026-08-12
**Context:** `REQ-SB-36-US-01` (`Implementation/UserStories/REQ-SB-36-US-01-
web-research-skill.md`) needs a real, invocable web-research skill backed
by a genuinely working Anthropic Provider — confirmed by direct inspection
of `app/business/provider_registry.py` (`_REAL_CLIENT_PROVIDER_IDS =
{"compass"}`), `requirements.txt` (no `anthropic`/`langchain-anthropic`),
and `.env.example` (no Anthropic key) that no such integration exists
anywhere in the real codebase today — the "Anthropic Claude" Provider other
stories' prose refers to is a UI-only placeholder, never backed by a real
client. `app/business/agent_orchestration/model_factory.py` is
`langchain_openai.ChatOpenAI`-only, an OpenAI-wire-format abstraction;
Anthropic's own native Messages API (needed specifically to reach
Anthropic's *server-side* web-search tool, the operator-confirmed
mechanism) is not that wire format, so `model_factory.py` cannot simply
gain a second `base_url` the way Compass's OpenAI-compatible endpoint does.

**A second, real, live-discovered gap surfaced during this pass, load-
bearing for `REQ-SB-36-US-01`'s own Scenario 2:** `app/business/
agent_orchestration/mcp_client.py::load_vault_query_tools()` calls
`MultiServerMCPClient.get_tools()` with no filtering — this returns
**every** tool registered on the shared MCP server, including
`skill_tools.py`'s catalog (confirmed by direct reading of both files).
Since `graph.py::_call_model` binds whatever `run_agent_conversation`
passes as `tools` to **every** agent's model unconditionally, `skill_tools.
diagram_understanding` (and, once built, `web_research`) is already
reachable through *any* agent's ordinary chat turn today, regardless of
`skill_registry.has_skill_access` — a real, currently harmless gap
(`diagram_understanding` is a stub that always honestly refuses), but one
that would silently falsify `REQ-SB-36-US-01` Scenario 2 ("An agent without
granted access cannot invoke the skill") the moment `web_research` becomes
a real, working tool. `app/business/skill_registry.py`'s own docstring
already anticipated exactly this fix point ("a future `agent_orchestration/`
tool-binding step is 'most plausibly' where enforcement additionally
lives... designed now so future integration reuses this exact check") —
this is that future point.

**Decision:**

1. **New dependency: the official `anthropic` Python SDK** (`anthropic`,
   PyPI), added to `requirements.txt` — not `langchain-anthropic`. The web-
   research skill is a standalone business-logic call (invoked via
   `skill_registry.invoke_skill`, never routed through `run_agent_
   conversation`'s LangGraph loop — see point 5, and `REQ-SB-36-US-01`'s
   own Non-Goals excluding general-purpose Anthropic-backed chat), so there
   is no LangChain graph node needing a `BaseChatModel`-shaped wrapper;
   a plain SDK client mirrors `compass_client.py`'s own existing "plain
   client, no framework wrapper" shape (`ADR-003`) for a fixed-purpose
   external call, rather than adding LangChain's own Anthropic integration
   for a surface that never touches LangChain.
2. **New `app/data_access/anthropic_client.py`** (sibling to
   `compass_client.py`, `ADR-003` layering) — `web_search(api_key: str,
   model: str, query: str) -> dict`, calling Anthropic's Messages API with
   its own server-side web-search tool included in the request's `tools`
   list (the operator-confirmed mechanism) — the exact current tool-type
   identifier/API version is a coder-task-level detail, confirmed against
   Anthropic's own current documentation at real build time (this
   project's established "pin-then-verify-at-real-install" precedent,
   `ADR-015` point 6). Returns a normalized `{"found": bool, "summary": str,
   "sources": list[str]}` — `"found": False` (Scenario 3) when the search
   genuinely returns nothing relevant, never a fabricated summary.
3. **`app/business/provider_registry.py` extended, not reworked:**
   `_REAL_CLIENT_PROVIDER_IDS` gains `"anthropic-claude"`; `_seed_state()`
   additionally seeds an `"Anthropic Claude"` Provider entry (mirrors the
   existing `"Compass"` self-seed exactly), sourced from two new `Settings`
   fields, `anthropic_api_key: str`/`anthropic_model: str` (mirrors
   `compass_api_key`/`compass_model`'s required-field shape — `app/
   config.py`, `.env.example` gains `ANTHROPIC_API_KEY=`/`ANTHROPIC_MODEL=`).
   Auto-seeding (over leaving the operator to create it manually via the
   already-built Provider CRUD form) was chosen because every other
   Provider this codebase's own stories already refer to by a fixed,
   known name (`"Compass"`) is auto-seeded — leaving "Anthropic Claude" as
   a manual-creation-only entry would be the only inconsistent case, and
   every other agent's Settings picker already expects a stable, always-
   present option list. A new `provider_registry.get_provider(provider_id)
   -> dict | None` helper (direct by-id lookup, mirroring
   `get_agent_provider`'s shape one level down) is added — the web-research
   skill resolves credentials by this fixed Provider id, not by whichever
   agent happens to invoke it (point 5), so no existing per-agent lookup
   fits.
4. **`app/business/skill_tools.py` gains `web_research(query: str) -> dict`**
   (`@mcp_server.tool()`, same catalog/registration shape `REQ-SB-27-US-01`
   already established) — resolves the `"anthropic-claude"` Provider via
   `provider_registry.get_provider`/`has_real_client` (the identical
   "declared but not yet backed → honest unavailability" funnel-gate shape
   `model_factory.resolve_agent_model`/`_invoke_action` already use one
   layer over, `ADR-011` point 3/`ADR-014` point 7) before ever calling
   `anthropic_client.web_search` — Scenario 4 (not yet available) and
   Scenario 3 (no results) are therefore always distinguishable from each
   other and from a real result, per the story's own Constraints.
5. **`skill_registry.invoke_skill(agent_id, skill_id, args: dict | None =
   None) -> dict`** — an additive optional third parameter (every existing
   zero-arg caller, i.e. `diagram_understanding`, is unaffected — `args`
   defaults to `None`/`{}` and is only threaded through when the resolved
   handler accepts it), and `app/api/skills_router.py`'s `POST /agents/
   {agent_id}/skills/{skill_id}/invoke` gains an optional JSON body (e.g.
   `{"query": str}`) passed through as `args` — the concrete mechanism
   Scenario 1's "invokes the skill with a research subject/query" needs,
   which `REQ-SB-27-US-01`'s original zero-argument stub never required.
   **The web-research skill is invoked exclusively through this existing
   REST/`invoke_skill` plumbing** (directly, by `ADR-023`'s orchestration,
   or via the router) — **not** bound as a tool inside `run_agent_
   conversation`'s LangGraph tool loop this pass; general conversational
   "ask your agent to go search the web" chat wiring is out of scope
   (`REQ-SB-36-US-01`'s own Non-Goals).
6. **The live-discovered tool-binding gap (Context, above) is closed now,
   not deferred a second time.** `app/business/agent_orchestration/
   mcp_client.py` gains `load_agent_tools(agent_id: str) -> list` —
   fetches the full server tool list via the existing `_MCP_CLIENT.
   get_tools()` call, then filters: a tool is always kept if its name is
   not a `skill_tools.SKILLS` key (the four core vault-query tools, never
   access-gated); a tool whose name *is* a skill id is kept only if
   `skill_registry.has_skill_access(agent_id, skill_id)` is `True`.
   `graph.py::run_agent_conversation` calls `mcp_client.load_agent_tools(
   agent_id)` in place of the old `load_vault_query_tools()` (removed —
   no remaining caller). This closes the gap for both `web_research`
   (satisfying `REQ-SB-36-US-01` Scenario 2 for the conversational path
   too, not just the direct REST path) and `diagram_understanding`
   (incidentally, a previously-harmless gap now correctly closed as a
   side effect of doing this correctly for the first real skill) — reusing
   `has_skill_access` exactly as `skill_registry.py`'s own docstring
   already anticipated, not a new enforcement concept.

**Alternatives Considered:**

- **`langchain-anthropic` + extending `model_factory.py` with a second,
  Anthropic-flavoured branch** — rejected: `model_factory.py`'s one job is
  resolving a `BaseChatModel` for `run_agent_conversation`'s own graph;
  this skill is deliberately *not* wired into that graph (point 5), so
  adding a LangChain wrapper and a second code path inside `model_factory.py`
  for a capability that never reaches it would be unused complexity — a
  plain SDK client in `data_access`, matching `compass_client.py`'s own
  precedent, is the closer fit.
- **General-purpose Anthropic-backed chat now, alongside the skill** (since
  a real client, once built, trivially supports it) — rejected per the
  operator's own explicit scoping ("specifically to give the Research
  Expert real web-search capability") and the story's own Non-Goals; adding
  it would be unrequested surface this pass.
- **Leave the "Anthropic Claude" Provider entry manually-created-only** (no
  auto-seed) — rejected, see point 3's own reasoning (consistency with the
  existing `"Compass"` self-seed precedent every other story already
  assumes).
- **Defer the tool-binding access-control gap** (leave `load_vault_query_
  tools()` as-is, accept that any agent's chat can reach `web_research`
  once real) — rejected: this would make `REQ-SB-36-US-01` Scenario 2
  provably false the moment the skill is real, for a fix `skill_registry.py`
  already anticipated and designed toward; fixing it now, while building
  the first real skill, is cheaper and more honest than leaving a known,
  now-consequential gap open a second time.
- **Enforce skill access inside each skill function's own body** (e.g.
  `web_research` takes `agent_id` and self-checks `has_skill_access`) —
  rejected: this would leak an `agent_id` parameter into an MCP tool's own
  public schema (awkward for any external MCP caller, including Hermes,
  which has no reason to know or supply Second Brain's own internal agent
  identity), and would require every future skill to remember to
  self-check rather than getting the guarantee structurally from the one
  shared loader.

**Consequences:**

- `requirements.txt` gains `anthropic`; `app/config.py`/`.env.example` gain
  two new required fields — any environment missing
  `ANTHROPIC_API_KEY`/`ANTHROPIC_MODEL` fails `Settings` construction at
  startup, the same behaviour a missing `COMPASS_*`/`SELF_EMAIL` value
  already has (`ADR-008`). A real Anthropic API key must be provisioned
  before the app will start at all once this ships — an operational
  step, not a code dependency (the story's own `## Dependencies`).
- `mcp_client.py`'s public surface changes from `load_vault_query_tools()`
  to `load_agent_tools(agent_id)` — a real, necessary edit to
  `graph.py::run_agent_conversation`'s own call site, confined to these two
  already-`Done`-story-owned files; no other caller of the old function
  name exists (confirmed by direct inspection).
- Every future real skill automatically inherits correct per-agent
  access-gating in the conversational tool loop for free, without its own
  enforcement code, by registering through the same `skill_tools.SKILLS`
  catalog `skill_registry.py` already reads.
- A second real, billed external API call now exists in this codebase
  (Anthropic, alongside Compass) — cost/latency is per-invocation, not
  per-conversation-turn, since it's only reached via explicit skill
  invocation, not bound into every chat turn.

**Correction (operator-directed, 2026-08-12, mid-`/implement-sprint` on
`SPRINT-022`) — supersedes point 3's "fixed `anthropic-claude`
Provider id" design; point 5's rejected-alternative reasoning is
narrowed, not overturned:**

The operator corrected point 3's design directly, quoted verbatim: "The
Anthropic_API_KEY Should be a Provider added to the Providers List — if
I linked the Research Agent to Compass, use Compass." `web_research`
now resolves its real backend from the **invoking agent's own linked
Provider** (`provider_registry.get_agent_provider(agent_id)`), not a
single hardcoded `"anthropic-claude"` id lookup — an agent must be
explicitly linked (via `REQ-SB-19-US-01`'s already-shipped Provider
picker) to the "Anthropic Claude" Provider entry to get real web
research; the "Anthropic Claude" Provider entry itself (point 3's own
auto-seed) is unchanged and still required.

**A real technical question was investigated before implementing this
correction, per the operator's own explicit instruction, not guessed:
does Compass/GPT-5 (Core42's gateway) have a real, hosted server-side
web-search tool structurally equivalent to Anthropic's own?** Confirmed
live, **no**: (a) this codebase's own `compass_client.py` sends only
`{"model", "messages"}` — no `tools`/search parameter of any kind; (b)
the sibling `agentic-map` project's own `services/gateway/compass.py`
does support generic OpenAI-style client-side function-calling
(`tools`/`tool_choice` passthrough) — but that requires the *caller* to
implement and execute any declared tool itself, structurally different
from a hosted server-side tool; (c) most tellingly, that same sibling
project's own `services/gateway/providers.py` routes its own
`web_search`-capable agents (`masdar_expert` et al.) through a
**separate, dedicated Perplexity Sonar provider**, with an explicit
code comment naming it as "the declared web_search provider" — real,
independent evidence that a team who already solved this exact
provider-selection problem concluded Compass/GPT-5 alone cannot do real
web search. Fabricating a "researched" result from a plain Compass
completion would violate `REQ-SB-33`'s own already-shipped
grounding/no-hallucination guardrail — not an acceptable substitute.

**Corrected decision:** `skill_tools.web_research(query: str, agent_id:
str) -> dict` resolves `provider_registry.get_agent_provider(agent_id)`;
if that Provider's id is `"anthropic-claude"` and
`has_real_client("anthropic-claude")`, dispatches to the real
`anthropic_client.web_search` call (point 2, unchanged); for any other
linked Provider (Compass, or none) it returns the exact same honest
"not yet available" shape point 4/Scenario 4 already defines — never a
fabricated result, regardless of which Provider is linked.
`skill_registry.invoke_skill(agent_id, skill_id, args)` injects
`agent_id` into the handler call whenever the resolved handler's own
signature declares an `agent_id` parameter (via `inspect.signature`),
so `skills_router.py`'s own request-body contract (`{"query": ...}`)
and `diagram-understanding`'s zero-arg call are both unaffected —
`agent_id` comes from `invoke_skill`'s own already-authenticated
parameter, never from the request body, so a caller cannot spoof a
different agent's Provider.

**This narrows, but does not overturn, point 5's own rejected
alternative** ("enforce skill access inside each skill function's own
body... would leak an `agent_id` parameter into an MCP tool's own
public schema") — that objection was about *access-control*
duplication; this correction's `agent_id` parameter is for *Provider
resolution*, a different concern the operator has now confirmed is
required. The tradeoff is accepted, not silently ignored: `web_research`'s
own MCP-declared schema now does include `agent_id: str`, a real
surface a future model-driven tool-caller could in principle try to
supply an arbitrary value for — currently inert, since `T05`'s own
Constraint keeps this skill reachable exclusively through
`invoke_skill`'s REST plumbing, never bound into
`run_agent_conversation`'s own LangGraph tool loop as an actually-
invocable capability this pass (`T06` only closes the *access-control
gap* for tools that end up bound; it does not add `web_research` as a
model-callable chat capability). Revisit this specific tradeoff if a
future story ever does bind `web_research` into the conversational tool
loop as a genuine chat capability.

Full escalation record: `ESCALATIONS.md` (this same date, `adr-deviation`,
resolved by this correction).

---

## ADR-023: Delegated knowledge-bootstrap orchestration — a new module composing `ADR-017`'s directly-callable Hub-routing lookup with real invocation of the matched candidate's own capability (skill invocation, or the Vault Filing Expert's placement function), the first code path in this project that actually acts on a Hub-routing match rather than only reporting it — extends `ADR-017`, does not reopen it

**Status:** Accepted
**Date:** 2026-08-12
**Context:** `REQ-SB-36-US-02` (`Implementation/UserStories/REQ-SB-36-US-02-
agent-knowledge-bootstrapping-delegated-research-chain.md`) needs a newly-
created, empty Expert agent to bootstrap its own knowledge end-to-end: its
own Section's Hub routes a help request to a Research Expert, which
performs real web research (`REQ-SB-36-US-01`) and hands the result to the
Vault Filing Expert (`REQ-SB-35-US-01`), which files it — the whole chain
completing without approval except `REQ-SB-35`'s own Tier-2 exception.

**A real, load-bearing gap, confirmed by direct reading of `REQ-SB-20-US-01`'s
own file, not assumed:** that story's own `## Notes` states plainly
(2026-08-12, resolving `ESC-013`'s working-mode-gating question): "`ADR-017`'s
already-approved routing-node design only ever *returns a matched-
candidate description to the requester* — it does not itself invoke any
action on the target agent... no story yet lets a routed request actually
execute anything on its target." This is the exact, and only, missing piece
`REQ-SB-36-US-02`'s entire premise depends on — Hub routing alone
*discovers who*, it does not *do anything with them*. This pass is the
first to actually need that, and is squarely "when we reach this level of
the product" the operator's own `ESC-013` resolution deferred to.

**A second real, load-bearing gap, inherited from `ADR-021`:** the
Constraint that "every agent in the delegation chain... must be in
Autonomous working mode for this specific flow" needs `app/business/
working_mode_registry.get_agent_working_mode(...)`, which — like `ADR-021`'s
own Tier-2 mechanism — does not exist in code yet (`REQ-SB-21-US-01` is
`status: Draft`, unbuilt; see `ADR-021`'s own Context and `ESCALATIONS.md`
→ `ESC-017`). Recorded here, not silently assumed satisfied, since this
story's own `## Dependencies` also lists `REQ-SB-21-US-01`/`ADR-020` as
"(Done)... satisfied already," which this pass's direct code inspection
found to be false.

**Decision:**

1. **New module, `app/business/agent_orchestration/knowledge_bootstrap.py`**
   (sibling to `graph.py` inside `agent_orchestration/` — a general
   in-app-agent-orchestration concern, not vendor/protocol-specific,
   `ADR-015` point 3's own placement rule), exposing one public entry
   point: `async def bootstrap_agent_knowledge(agent_id: str, subject:
   str) -> dict` — mirroring `run_agent_conversation`'s own "one public
   entry point, directly testable" convention.
2. **The chain is a deterministic composition of already-real (or, per
   `ADR-021`/`ADR-022`, already-designed) entry points — not a second,
   recursive `run_agent_conversation` call per hop.** Concretely:
   - Hop 1: `graph.route_cross_section_request(agent_id, need_description=
     f"real web research about {subject}")` (`ADR-017`, already directly
     callable) → a matched Research Expert `agent_id`, or an honest
     `{"matched": False}` (Scenario 4 — chain stops, no fabricated match).
   - Working-mode check: the matched agent's own `working_mode_registry.
     get_agent_working_mode(...)` must be `"autonomous"` for this flow to
     proceed unattended (the story's own Constraint) — **a real, currently
     unmet code dependency on `REQ-SB-21-US-01`**, see Context/Consequences.
   - Research: `skill_registry.invoke_skill(research_expert_agent_id,
     "web-research", {"query": subject})` (`ADR-022`) → real gathered
     content, or Scenario 5's honest no-results (chain records the
     honest failure and stops, per the story's own "no step fabricates a
     confident result to keep the chain moving" Constraint).
   - Hop 2: `graph.route_cross_section_request(research_expert_agent_id,
     need_description="file this content into the vault")` → a matched
     Vault Filing Expert `agent_id`, same honest-no-match handling as Hop 1.
   - Filing: `vault_filing_expert.determine_placement_and_file(content=
     gathered_content, source_description=f"Web research about {subject}",
     requesting_agent_id=agent_id)` (`ADR-021`) → Tier 1 (written
     immediately, chain completes) or Tier 2 (a pending-approval record is
     created — **a real, currently unmet code dependency on
     `REQ-SB-21-US-01`**; the chain's own return value honestly reports
     `"status": "pending_approval"`, satisfying Scenario 2's "only that
     one step pauses... every other step in the chain has already
     completed").
   - **The Hub-routing match is used to identify *who*; the specific
     capability invoked at each hop is composed by this orchestration
     directly (`invoke_skill(..., "web-research", ...)`,
     `determine_placement_and_file(...)`), not dynamically dispatched by
     role name.** This is a deliberate scope bound (see Alternatives) —
     `REQ-SB-36-US-02`'s own Constraints already name exactly these three
     mechanisms as what this story composes, not reimplements.
3. **Triggered through the existing action-trigger funnel, not a new
   endpoint.** A newly-created Expert agent (e.g. `"compass-expert"`, a
   plain new `agent_registry.AGENTS` entry — `ADR-011` point 2/`REQ-SB-
   36-US-02`'s own "code-level addition" resolution, no new mechanism)
   declares one new action, `"build_knowledge"`, dispatched through the
   existing `_ACTION_HANDLERS`/`_invoke_action` mechanism (`ADR-011`) —
   `("compass-expert", "build_knowledge"): knowledge_bootstrap.
   bootstrap_agent_knowledge` — reachable by chat trigger phrase or a
   direct Available-Actions button, identically to every existing action.
   Any future pilot Expert agent adds the identical one-line registry
   entry, satisfying Scenario 6 (general capability, not Compass-specific)
   structurally — the handler itself never references "Compass."
4. **The whole chain's outcome is recorded as one `run_event` history
   entry on the originating Expert agent** (`vault_writer.
   append_agent_history_entry`, the same mechanism every existing action
   already uses) — a human reviewing that agent's own Communication
   History sees exactly what was researched, where it was filed (or that
   it is pending Tier-2 approval, or that it honestly failed/found
   nothing), in one place.

**Alternatives Considered:**

- **Recursively invoke `run_agent_conversation` for each matched candidate**
  (treat the Research Expert/Vault Filing Expert hops as real, independent
  LLM conversations the orchestration "talks to") — rejected for this
  pass: it would require the Research Expert's own conversational turn to
  itself decide, via tool-calling, to invoke the web-research skill and
  then decide, via a second tool call, to hand off to the Vault Filing
  Expert — introducing a second layer of "will the model reliably choose
  to call the right tool in the right order" risk on top of `ADR-021`
  point 2's own already-made "prefer deterministic composition over
  hoping the model tool-calls correctly" decision, for no behavioural gain
  this story's own Acceptance text asks for (it describes *that the chain
  runs*, not that each hop must itself be a free-form LLM conversation).
  A future story that genuinely needs open-ended, model-driven multi-agent
  dialogue (not this one, which has an entirely fixed three-hop shape) can
  revisit this.
- **A fully generic, role-name-keyed dynamic dispatch table** (Hub routing
  returns a matched agent id, and a registry maps agent id → its own
  capability function, so a *third* future delegation chain needs zero new
  orchestration code) — rejected as speculative generality this story's
  own scope doesn't call for; `REQ-SB-36-US-02`'s own Constraints
  explicitly name the three mechanisms this chain composes. A future
  second delegation chain with a genuinely different shape is a new
  architecture question for whichever story builds it, not pre-solved
  here.
- **Skip the working-mode check entirely this pass** (since
  `working_mode_registry.py` doesn't exist yet, treat every agent as
  implicitly Autonomous, matching today's real, only-existing behaviour) —
  rejected: this would silently contradict the story's own explicit
  Constraint and `ADR-020`'s already-`Accepted` per-agent mode concept the
  moment `REQ-SB-21-US-01` does ship (a Supervised/Manual-mode Research
  Expert would then incorrectly still run unattended through this chain,
  unless the check is designed in now). The check is designed and named
  here; **building** it is blocked on `REQ-SB-21-US-01`, recorded honestly
  in Consequences, not silently dropped from the design.

**Consequences:**

- **This story's own coder task for `knowledge_bootstrap.py` has two real,
  currently-unmet blocking prerequisites, both inherited from `ADR-021`'s
  own finding, not new to this ADR:** `REQ-SB-21-US-01` must ship
  `working_mode_registry.py` (for the Autonomous-mode check) and
  `pending_approval_registry.py`/`pending_approvals_router.py` (for Tier
  2's own resolution, via `ADR-021`). Neither can be given a real,
  `Ready` cross-story `depends_on` task id today — see `ESCALATIONS.md` →
  `ESC-017` for the decomposer-facing detail, mirroring `ESC-011`'s own
  precedent (a real dependency recorded plainly rather than a fabricated
  task-id reference).
- `route_cross_section_request` (`ADR-017`) is used exactly as already
  designed — this ADR adds no change to that function's own signature or
  behaviour, only a new caller.
- A future second delegation chain with a genuinely different shape (see
  Alternatives) is free to compose `route_cross_section_request` the same
  way, or to propose its own mechanism — this ADR does not generalize
  itself pre-emptively.
- `agent_registry.py` gains one new action definition per pilot Expert
  agent (`"build_knowledge"`) — no change to `agent_registry.py`'s own
  shape, `ADR-011` point 2 untouched.

## ADR-024: Vault index storage & rebuild shape — in-memory, module-level, full-rebuild-and-swap on every trigger; no `.second-brain/` persistence, no new database

**Status:** Accepted
**Date:** 2026-08-13
**Context:** `REQ-SB-01-US-01` (`Implementation/UserStories/REQ-SB-01-US-01-
vault-indexing.md`) is the first story to need a **real, persistent, re-
runnable index** of the vault's notes (frontmatter, tags, outgoing/incoming
wikilinks). Direct inspection of the current codebase (2026-08-13) confirms
none exists: every vault-query primitive in `app/data_access/vault_writer.py`
(`list_all_note_paths`, `list_known_customers`, `list_known_kinds`,
`list_known_partners`) and their thin pass-throughs in `app/business/
vault_query_tools.py` (built for `REQ-SB-25`'s agent tool-calling) re-scan
the filesystem fresh on every call — stateless request-scoped I/O, not a
cached or persisted structure. No wikilink-graph (forward or backward) is
computed or stored anywhere; Obsidian's own graph view is the only place
backlinks currently render. This ADR decides the storage/rebuild shape for
the new index the story's own Constraints deliberately left open as
"ordinary architecture-level latitude." Forces: (1) the story's own
Constraint that re-running the index must fully reconcile additions, edits,
**and deletions** without a manually-fed diff; (2) the story's resolved
(`ESC-021`) trigger design — **both** an explicit on-demand call and the
already-`Done` `REQ-SB-07` hourly-plus-app-start scheduler tick (`ADR-005`)
refresh the index, with live filesystem watching explicitly out of scope
this pass; (3) a real, grounded scale: 496 notes today under `Work/` in the
real vault (`VAULT_PATH`), single-user, growing gradually, not by orders of
magnitude; (4) this story explicitly builds **no** browse/search/query
surface over the index (`REQ-SB-02`'s job, per this story's own Non-Goals)
— so nothing yet needs the index to serve filtered/ranked queries fast, only
to exist correctly and be rebuildable.

**Decision:**

1. **In-memory only — a module-level singleton dict, no disk persistence.**
   New `app/business/vault_indexing.py` holds `_vault_index: dict[str, dict]`
   (module-level), keyed by each note's filename stem (the same identity
   `write_note()`/`meeting_note_filename_stem()`/wikilinks this project
   already writes use throughout — see point 3). No `.second-brain/*.json`
   file is added for this store, unlike every other persisted concern in
   this codebase (`processed_email_ids.json`, `conversation_index.json`,
   `agent_sections.json`, etc.).
2. **Every rebuild is a full rebuild, never an incremental diff.** One
   function, `rebuild_index() -> dict` (business-layer, synchronous),
   is the single code path both trigger sources call: the new on-demand
   `POST /vault-index/rebuild` endpoint (`app/api/vault_index_router.py`,
   new) calls it directly; the existing `REQ-SB-07` scheduler tick
   (`app/business/email_classification.py::run_capture_and_record_completion`)
   gains one additional, **unconditional** call to it (not gated by
   `email-capture`'s or `meeting-capture`'s own working mode — vault
   indexing is core plumbing, not an Agents Map agent action, so
   `ADR-018`/`ADR-020`'s per-agent working-mode gate does not apply to
   it). `app/scheduling/capture_scheduler.py` itself needs **zero**
   changes — it already treats `run_capture_and_record_completion` as an
   opaque unit, the same "no scheduler-layer change needed" precedent
   `REQ-SB-08`'s meeting capture already established for adding a second
   concern to the same tick.
   `rebuild_index()` walks `vault_writer.list_all_note_paths()` (unchanged
   — already scoped to `Work/*/*.md`, which already excludes the vault
   root's `.obsidian/` and `Templates/` since neither lives under `Work/`;
   Scenario 7 is satisfied by this existing primitive with zero new
   filtering code), reads each note via `vault_writer.read_note()`,
   extracts `tags` and outgoing wikilink targets, assembles a **brand-new**
   dict end to end, then atomically reassigns the module-level reference
   in one step (a single-reference rebind is safe under CPython's GIL —
   no explicit lock is needed for the swap itself, unlike
   `capture_scheduler.py`'s `_capture_run_lock`, which guards a different
   concern — overlapping *capture* runs writing vault state — that the
   read-only, side-effect-free index rebuild does not share). **Discarding
   the old dict wholesale, rather than patching it, is what gives
   deletions their honest reconciliation for free (Scenario 5):** a note
   removed from the vault simply cannot appear in the freshly-built dict
   or contribute a backlink on this rebuild — no separate deletion-
   tracking code is needed.
3. **Backlinks (incoming wikilinks) are derived, not stored per-note at
   write time.** A second pass over the freshly-built per-note map inverts
   every note's outgoing-wikilink list into the target notes' incoming-
   wikilink lists (Scenario 2). Wikilink target text is matched against
   each indexed note's own filename stem, case-insensitively — the same
   identity this project's own capture pipelines already use when writing
   wikilinks (`upsert_attendee_links`, `record_conversation_note`/
   `find_related_note_stems` both render/track `[[<stem>]]` using the
   exact slugified filename stem). A target that matches no indexed note's
   stem (a genuinely dangling link, or a manually-authored note's
   free-text wikilink that doesn't resolve under this rule) is recorded
   as an outgoing link only, with no crash and no fabricated target entry
   — honest handling, not a hard link-resolution guarantee equivalent to
   Obsidian's own (aliases, headings, and non-unique-title resolution are
   out of scope; the PRD's own Acceptance text asks for "outgoing/incoming
   wikilinks," not Obsidian's full resolution algorithm).
4. **A real, pre-existing gap in `vault_writer.read_note()` must be fixed
   for tags to round-trip correctly, in `data_access`, not worked around
   in the new indexing module.** `read_note()`'s `_parse_frontmatter_value`
   only handles a quoted-string branch and a raw-passthrough fallback — a
   `tags: ["customer/x", "kind/y"]` line currently reads back as the
   literal unparsed string `'["customer/x", "kind/y"]'`, not a Python
   list, which would silently fail Scenario 1's "correctly captures that
   note's tags." This is the same class of round-trip gap `REQ-SB-30-
   US-01` already found and fixed for boolean frontmatter values
   (`important`) — the fix here is the same shape: `_parse_frontmatter_
   value` gains one more branch recognizing a bracketed-list value and
   returning a real `list[str]`, mirroring the existing boolean-branch
   precedent, not a new parsing format or a general YAML parser (still
   explicitly out of scope, per `read_note()`'s own docstring). No new ADR
   for this fix specifically — it is an ordinary, same-shape extension of
   an already-`Accepted` primitive, exactly as `REQ-SB-30-US-01`'s own
   equivalent fix required no new ADR.

**Alternatives Considered:**

- **Persist to a new `.second-brain/vault_index.json` file**, mirroring
  the existing flat-JSON-file `.second-brain/` convention every other
  cross-request store in this codebase uses. Rejected: the durability this
  buys (index survives a process restart before the first rebuild
  completes) is redundant here specifically, because this story's own
  resolved trigger design (`ESC-021`) already guarantees an unconditional
  rebuild fires on every app start (`ADR-005`'s existing unconditional
  app-start trigger, which this story wires into) — the population gap on
  a bare restart is bounded by that already-fast, already-existing tick,
  not an open window. Meanwhile a JSON file would cost real serialization
  complexity this store's shape doesn't have elsewhere: every existing
  `.second-brain/*.json` file is flat (an id-keyed list or dict of
  primitives); this index is a two-level graph (per-note maps plus a
  *derived* backlink index), and persisting it correctly would mean either
  serializing the derived backlinks too (redundant with the source of
  truth, a staleness risk if the file and the vault ever disagree) or
  re-deriving them on load anyway (in which case the persisted file buys
  nothing the in-memory rebuild doesn't already give for free). No
  consumer reads this file between rebuilds this story anyway — `REQ-SB-02`
  (browse/search) is explicitly out of this story's scope.
- **A real database (SQLite).** Rejected as disproportionate: this
  codebase has never used a database — every existing persisted concern is
  a flat JSON file or the vault's own markdown — and SQLite's real
  advantage (fast filtered/indexed queries at scale) has no consumer this
  story builds; this story's own Non-Goals explicitly exclude any browse/
  search/query layer (`REQ-SB-02`'s job). Introducing a new persistence
  technology to serve a query surface that doesn't exist yet is exactly
  the kind of speculative-generality this project has repeatedly declined
  in favor of "proportionate first, escalate only if proven insufficient"
  (`ADR-011`'s own precedent, directly cited in this story's Context).
  Revisit **this ADR** (supersede, don't silently swap) if/when `REQ-SB-02`
  demonstrates the full-vault-scan-and-in-memory-dict approach cannot serve
  its real browse/search/filter requirements fast enough at the vault's
  actual scale.
- **Incremental/diff-based reconciliation** (track each note's mtime or a
  content hash; re-read only changed files; explicitly track deletions via
  a seen-this-run-vs-seen-last-run set difference). Rejected: the story's
  own Constraint requires a full, honest reconciliation of add/edit/
  delete with no manually-fed diff, and re-reading ~500 small markdown
  files (a frontmatter parse plus one body regex scan each) is cheap
  enough on a single-user machine that the added bookkeeping (mtime
  tracking, explicit deletion-set bookkeeping) buys speed at a real
  correctness risk — a missed or wrong mtime update silently serves stale
  data — for a performance problem that does not exist yet at this scale.
  A full rebuild is also the only mechanism that gives Scenario 5's
  dangling-link honesty for free (point 2, above), which an incremental
  approach would have to reimplement by hand as an explicit deletion path.

**Consequences:**

- The index is **transient** — lost on process restart, repopulated by the
  next rebuild trigger (bounded, in practice, by `ADR-005`'s existing
  unconditional app-start trigger, which this story's own scheduler-tick
  wiring reuses rather than duplicates). No cross-process sharing; this
  matches this project's existing single-user/single-host posture
  elsewhere (e.g. My Day's "today" computed from the app/server host's
  local clock, no timezone/multi-instance handling).
- Every rebuild is `O(all notes)` — proportionate at today's real ~500-note
  scale; if the vault grows enough that a full rebuild's latency becomes
  noticeable against the hourly/on-demand cadence, that is a concrete,
  measured reason to revisit this ADR (supersede it), not a reason to
  pre-optimize now.
- `rebuild_index()`'s call inside `run_capture_and_record_completion()` is
  **unconditional**, independent of `email-capture`'s/`meeting-capture`'s
  own working mode (`ADR-018`/`ADR-020`) — a future story that wants the
  index rebuild itself to be gateable must make that an explicit new
  decision, not assume today's wiring already supports it.
- `vault_indexing.get_index()` (a plain whole-dict accessor, no filter/
  query parameters) is the only read surface this ADR adds — it exists for
  internal/test use and as the substrate `REQ-SB-02` builds its actual
  browse/search endpoints on top of; it is deliberately **not** a browse/
  search API itself, preserving this story's own Non-Goals boundary.
- The `_parse_frontmatter_value` list-value fix (point 4) is a permanent,
  reusable correction to `vault_writer.py` — every future frontmatter list
  field (not just `tags`) now round-trips correctly through `read_note()`,
  not just the one this story happened to need.

## ADR-025: `/mcp` shared-secret authentication for non-loopback callers, plus a write-capable MCP tool that never writes directly — it always creates a Pending Approval (new `trigger="hermes"`, dispatched like `ADR-021`'s Tier-2 `action_id`), scope-gated by a fail-closed seam pending `REQ-SB-29-US-01`

**Status:** Accepted
**Date:** 2026-08-13
**Context:** `REQ-SB-04-US-01` (`Implementation/UserStories/REQ-SB-04-US-01-
agent-vault-write-access.md`) needs a Hermes-connected agent to create or
modify a vault note, under an explicitly bounded scope and an explicit
confirmation step — the PRD's own Acceptance text, with two operator-
confirmed decisions grounding the build shape: (1) real authentication on
`/mcp` for any non-loopback caller (shared with `REQ-SB-03-US-01`, higher
stakes here since a write-capable tool is a materially bigger exposure than
the four read-only tools `REQ-SB-03` depends on); (2) scope reuses
`REQ-SB-29`'s tag/folder-scope concept, confirmation reuses `REQ-SB-21`'s
Supervised/Pending-Approvals precedent. Direct inspection of the real
codebase (2026-08-13) confirms the starting state precisely: `app/api/
mcp_server.py` registers four read-only `@mcp.tool()`s and is mounted at
`app.mount("/mcp", mcp_server.streamable_http_app())` in `app/main.py` with
**zero** authentication of any kind — no header check, no dependency, no
API key (`CORSMiddleware` is scoped only to the Vite dev-server's browser
origins and does not apply to a server-to-server MCP client at all). No
write-capable tool exists anywhere on the server. `app/business/
pending_approval_registry.py`/`app/api/pending_approvals_router.py`
(`ADR-018`/`ADR-020`, `REQ-SB-21-US-01`, `Done`, `SPRINT-021`) already
implement a real, working propose→pending→approve/decline lifecycle with an
explicit `trigger` enum (`"chat" | "direct" | "background"`, `"hub_routed"`
added by `ADR-020` as a documented-but-still-inert future value) and an
additive `payload: dict | None` field (`ADR-021` point 4) that a
non-`agent_registry`-declared `action_id` can carry deferred-execution data
through, dispatched via `pending_approvals_router.py`'s own
`_APPROVAL_HANDLERS` table (`ADR-021` point 5's Tier-2 precedent —
`vault_filing_expert.finalize_new_top_level_area` is the one existing
entry). `app/data_access/vault_writer.write_note(subfolder, filename_stem,
frontmatter, body)` is the generic, already-shared write primitive every
capture pipeline in this codebase uses — it unconditionally overwrites
whatever file already exists at the computed path (`path.write_text(...)`,
no existence check, no collision guard) and creates parent directories as
needed. **The one piece with no existing mechanism at all:**
`REQ-SB-29-US-01` (Agent-to-Tag/Folder Scoping) — the story this one's own
scope-enforcement is confirmed to reuse — is itself `status: Draft`,
`gate: clear`, has never been decomposed (zero `REQ-SB-29-US-01-T*.md`
files exist, confirmed by direct glob), and still needs its own `/design`
pass before its own `/plan-tasks`. This is a real, load-bearing dependency
this ADR must design around, not guess past — mirrored, not re-litigated
here (`REQ-SB-29`'s own retrieval-mechanism question is already resolved on
its own terms, `ESC-008`, `Resolved`).

**Decision:**

1. **`/mcp` authentication: a small ASGI middleware wrapping only the
   mounted `/mcp` sub-app, not a blanket app-wide auth layer.**
   `app.mount(path, app)` takes a raw ASGI application and has no
   `dependencies=` parameter the way `APIRouter.include_router`/a FastAPI
   route does — so a `Depends(...)`-based check cannot be attached to the
   mount directly. New `app/api/mcp_auth.py` exports
   `require_hermes_shared_secret(app: ASGIApp) -> ASGIApp`, a thin ASGI
   middleware class: for any `scope["type"] != "http"` request, pass
   through unchanged (Streamable HTTP's own SSE/streaming framing must not
   be disturbed); for an HTTP request, if `scope["client"][0]` (the real
   TCP peer address FastAPI/Starlette populate regardless of what hostname
   string the caller's own client used to connect — confirmed against
   `agent_orchestration/mcp_client.py`'s own already-live loopback call,
   `"http://127.0.0.1:8001/mcp"`) is in `{"127.0.0.1", "::1"}`, pass
   through unchanged (Second Brain's own in-app LangGraph agent, already
   live since `REQ-SB-25-US-01`, must be unaffected — the story's own
   Scenario 4/Constraint, shared with `REQ-SB-03-US-01`); otherwise, require
   header `X-Hermes-Shared-Secret` to exactly match
   `settings.hermes_mcp_shared_secret`, rejecting with a plain `401` (no
   tool call reaches the underlying FastMCP app) on any mismatch or absent
   header. `app/main.py` wraps the mount:
   `app.mount("/mcp", require_hermes_shared_secret(mcp_server.
   streamable_http_app()))` — `mcp_server.py` itself is untouched by this
   point; the auth concern lives in its own sibling module, not folded into
   the tool-registration file (separation of concerns, same "one module,
   one concern" discipline `ADR-014`/`ADR-018` already established
   repeatedly in this codebase).
2. **New `Settings.hermes_mcp_shared_secret: str` field, `.env`-sourced,
   mirroring `compass_api_key`/`anthropic_api_key`'s existing shape exactly**
   — the operator's own named minimum-viable pattern. A single shared
   secret for every non-loopback caller (not a per-agent credential) —
   authenticates "this is a legitimate Hermes-side caller," nothing more;
   *which* agent is acting is a separate, explicit parameter every tool call
   supplies (point 4, below), never inferred from the secret itself.
3. **Built once, reused by both stories — not duplicated.** This mechanism
   satisfies `REQ-SB-04-US-01`'s own Constraint verbatim and is the
   identical mechanism `REQ-SB-03-US-01`'s own already-recorded Scenario
   4/Constraint (`ESC-023`) independently names. `REQ-SB-03-US-01` has not
   yet reached `/plan-tasks` (still `status: Draft`, zero tasks); when it
   does, its own architect pass should point at this ADR and this story's
   own auth task (`REQ-SB-04-US-01-T01`) rather than re-design or re-build
   the mechanism a second time — recorded here so that future pass does not
   have to rediscover it.
4. **The write-capable MCP tool never writes directly — it always creates a
   Pending Approval, unconditionally, regardless of the target agent's own
   working mode.** New `app/business/vault_write_tools.py` (sibling to
   `vault_query_tools.py`, same "thin business-layer wrapper the MCP server
   registers" shape `ADR-015` point 3 already established) exposes
   `propose_vault_write(agent_id: str, subfolder: str, filename_stem: str,
   frontmatter: dict, body: str) -> dict`, registered as
   `@mcp_server.tool()` in `mcp_server.py` (growing the *same* shared server
   — `ADR-015` point 9's "register, never a new server per capability" rule
   — not a second instance). `agent_id` is an explicit, required parameter
   the calling agent supplies — Second Brain does not derive "which agent"
   from the shared secret (point 2) or from any session/connection state;
   an `agent_id` that does not resolve via `agent_registry.get_agent(...)`
   is rejected outright (`{"status": "rejected", ...}`), never silently
   treated as "no restriction." For a **known** agent, the proposed
   write's target is checked against that agent's `REQ-SB-29`-assigned
   scope (point 5, below); if in scope, `pending_approval_registry.
   create_pending_approval(agent_id, trigger="hermes", action_id=
   "hermes_vault_write", description=..., payload={"subfolder":
   subfolder, "filename_stem": filename_stem, "frontmatter": frontmatter,
   "body": body})` is called — a new `trigger` enum value, added the exact
   same way `ADR-020` added `"hub_routed"` (a plain string field on an
   already-general record shape; `create_pending_approval`'s own
   `trigger == "background"`-only idempotency guard needs no code change to
   accept it, since every other trigger value is already never deduplicated
   by construction) — and the tool returns `{"status": "pending", ...,
   "pending_approval_id": ...}`. **This is unconditional — it does not
   consult `working_mode_registry` at all, for any agent, ever**, extending
   `ADR-021` point 5's own "`working_mode_registry` is never referenced
   anywhere in `vault_filing_expert.py`... bypassing the working-mode gate
   by construction, not a conditional check on it" precedent to a second,
   independent case: this story's own Context names Hermes access as "a
   materially bigger trust surface" than in-app actions specifically
   *because* it originates outside Second Brain's own UI, and its own
   Constraints require confirmation on **every** write with no
   Autonomous-mode carve-out — a deliberate, permanent divergence from
   `ADR-020`'s own agent-working-mode-conditional gate for in-app
   chat/direct/hub_routed actions, not an oversight.
   `pending_approvals_router.py`'s existing `_APPROVAL_HANDLERS` table
   gains one entry, `"hermes_vault_write":
   vault_write_tools.finalize_hermes_write` — `finalize_hermes_write
   (payload) -> dict` calls `vault_writer.write_note(payload["subfolder"],
   payload["filename_stem"], payload["frontmatter"], payload["body"])` and
   returns `{"path": ...}`, matching `finalize_new_top_level_area`'s own
   return shape exactly (consumed by the router's existing `f"Approved —
   filed at {result['path']}."` message, unchanged). **Decline needs no new
   code** — the existing `decline_pending_approval` endpoint already
   resolves any `"pending"` record regardless of `action_id`/`trigger`,
   discarding the proposal and recording an honest "Declined — no action
   taken" history entry (`ADR-018` point 2/6, unmodified).
5. **Write safety envelope: reuse `vault_writer.write_note`'s existing
   unconditional-overwrite semantics as-is — no new collision-avoidance or
   merge/append primitive.** The story's own Scenario 1 text — "a new **or
   modified** note appears in the vault" — explicitly covers both create and
   overwrite-in-place, matching how every other capture pipeline in this
   codebase already treats a deterministically-targeted filename (email/
   meeting/people captures all call `write_note`-family primitives that
   overwrite a stable, computed path, never append/merge). This is a
   different case from `ADR-021` Tier 2's own numeric-suffix collision
   guard, which exists specifically to protect an *ambiguous, LLM-proposed*
   new-top-level-area name from an accidental clash — here, the target
   `subfolder`/`filename_stem` is an explicit parameter the calling agent
   itself names, not an LLM-inferred guess, so "modify" (overwrite the
   named target) is the intended, literal behaviour Scenario 1 asks for,
   not a hazard to guard against with a second mechanism.
6. **Scope enforcement: a real, load-bearing dependency on
   `REQ-SB-29-US-01`, resolved with a fail-CLOSED seam, never fail-open.**
   `REQ-SB-29-US-01` has no scope-assignment/lookup mechanism built at all
   (Context, above) — there is nothing real to query yet. Rather than block
   this entire ADR/story on that story shipping (contradicting Pipeline.md's
   "forward is autonomous by exception" rule and this story's own
   already-recorded "architecture/task creation may proceed now" framing),
   `vault_write_tools.py` isolates the scope decision behind one seam
   function, `_is_within_assigned_scope(agent_id, subfolder, frontmatter) ->
   bool`, whose body is, for now, a **permanent-until-replaced `return
   False`** with a comment naming exactly why and what replaces it: "no
   `REQ-SB-29` scope registry exists yet — every write is rejected as
   out-of-scope until one does; this is the fail-closed default, never
   fail-open, matching `REQ-SB-29-US-01` Scenario 6's own 'no assigned scope
   = no bounded access' rule extended to writes." This makes
   `propose_vault_write` **structurally incapable of ever landing a write**
   until `REQ-SB-29-US-01` ships a real per-agent scope lookup this seam can
   call — an honest, safe, buildable-now state, not a half-built trust hole.
   The decomposer's own task split (see the parent story's `## Notes`)
   separates this seam's real implementation (blocked on `REQ-SB-29-US-01`,
   no real task id exists to depend on yet — `ESCALATIONS.md` → `ESC-026`)
   from the surrounding propose→pending→approve/decline plumbing (buildable
   and live-verifiable now, using a direct `pending_approval_registry`
   seed to exercise the confirm/decline mechanics independently of the
   scope gate).

**Alternatives Considered:**

- **FastAPI `Depends()`-based auth on individual MCP tool functions**,
  instead of ASGI middleware around the mount. Rejected: `@mcp_server.
  tool()`-decorated functions are FastMCP's own registration mechanism, not
  FastAPI route handlers — they carry no FastAPI dependency-injection
  machinery at all, and threading a manual header check into every tool
  function (four existing, plus this story's new one, plus whatever
  `REQ-SB-03`/future stories add) duplicates the same check at every call
  site instead of once at the transport boundary, and — worse — a tool
  function's own internal check cannot reject the underlying MCP
  session/handshake itself, only a specific tool invocation after a
  connection is already established.
- **A per-agent API key/credential** (each Hermes-side agent presents its
  own distinct secret, from which Second Brain derives `agent_id` directly),
  instead of one shared secret plus an explicit `agent_id` parameter.
  Rejected as disproportionate for the operator's own named "minimum-viable
  shared-secret shape" — issuing/rotating/storing N per-agent credentials is
  real, unrequested surface (a credential-management concern this project
  has never needed before) for a single-user, single-Hermes-deployment
  integration; the explicit `agent_id` parameter already gives Second Brain
  everything the scope/registry lookups need, and a compromised shared
  secret is no worse a exposure than today's *zero* authentication, not a
  regression.
- **Scope check enforced at Approve-time (inside `finalize_hermes_write`)
  rather than at proposal-time (inside `propose_vault_write`).** Rejected:
  the story's own Scenario 2 text is explicit that an out-of-scope attempt
  is "rejected" with "no note created or modified as a result of the
  attempt," described as happening at attempt time, distinct from
  Scenario 3/4's "held pending"/"declined" language for an **in-scope**
  proposal awaiting the user's own decision — conflating the two would mean
  an out-of-scope write silently becomes a Pending Approval the user has to
  notice and manually decline, rather than being refused immediately and
  honestly, matching this project's standing "honest refusal over silent
  pileup" posture (`ADR-011` point 3, `ADR-014` point 7, `ADR-020` point 1).
- **Fail-open scope default** (treat an unassigned/unresolvable scope as
  "no restriction, allow the write") while `REQ-SB-29-US-01` remains
  unbuilt, so `REQ-SB-04-US-01` could be fully live-verified today.
  Rejected outright — this is exactly the "materially bigger trust surface"
  the story's own Context warns against, and directly contradicts both this
  story's own Constraint ("writes outside an agent's assigned scope must be
  rejected, never silently allowed") and `REQ-SB-29-US-01`'s own explicit
  Scenario 6 rule ("an agent with no assigned scope has no bounded vault
  query access... does not silently search the whole vault"). A
  structurally-safe, honestly-incomplete state (fail-closed, verified via
  the propose→pending plumbing alone) is preferred over a functionally-complete
  but unsafe one.
- **Wait for `REQ-SB-29-US-01` to ship before writing this ADR/running
  `/plan-tasks` on `REQ-SB-04-US-01` at all.** Rejected per the story's own
  already-recorded framing ("architecture/task creation may proceed now")
  and Pipeline.md's "forward is autonomous by exception" rule — nothing
  about the missing scope registry prevents designing and building the
  auth mechanism, the tool-registration surface, or the confirm/decline
  plumbing today; only the scope-match seam's own real body is genuinely
  blocked.

**Consequences:**

- `/mcp` is genuinely unreachable end-to-end by any real external Hermes
  client until a real `HERMES_MCP_SHARED_SECRET` is provisioned in `.env`
  and a real Hermes deployment is confirmed reachable (`ESC-023`, still
  `Open`) — this ADR makes the mechanism real and testable (loopback-vs-
  non-loopback, correct-vs-incorrect secret), not a live Hermes round trip,
  matching this project's own established "design/build vs. live-verified"
  distinction for external-system-dependent work.
- `propose_vault_write` cannot land a single real write until
  `REQ-SB-29-US-01` ships a real scope registry `_is_within_assigned_scope`
  can call — this is a deliberate, honest, temporary limitation, not a
  defect; `REQ-SB-04-US-01`'s own Scenarios 1 and 2 (the scope-dependent
  ones) cannot be genuinely live-verified until then, matching the story's
  own already-recorded expectation exactly. Scenarios 3 and 4 (the
  confirm/decline plumbing) do not depend on scope and are buildable and
  verifiable now.
- A future `REQ-SB-29-US-01` architecture pass must confirm its own scope
  representation (tag string vs. folder path vs. something else) is
  directly comparable against this tool's `subfolder`/`frontmatter`
  parameters — if it lands in a shape this seam cannot match against
  directly (e.g. only tag-based, no folder-based equivalent), that is a
  concrete, real finding for `_is_within_assigned_scope`'s own eventual
  implementation to reconcile, not assumed compatible here.
- The `"hermes"` trigger value, like `ADR-020`'s `"hub_routed"`, is now a
  permanent addition to the Pending Approvals record shape's documented
  `trigger` enum — any future code that pattern-matches on `trigger` by an
  exhaustive literal list (none does today; `pending_approval_registry.py`
  treats it as an opaque string throughout) must account for it.
- `REQ-SB-03-US-01`'s own future `/plan-tasks` pass inherits this ADR's
  points 1-3 (the `/mcp` auth mechanism) as already-decided, reused
  infrastructure — it should reference this ADR and `REQ-SB-04-US-01-T01`
  directly rather than design or build the mechanism a second time.

## ADR-026: Search ranking mechanism — field-weighted BM25-style scoring, implemented as a small pure-Python function over `vault_indexing.get_index()`, computed at query time; no new dependency, no persisted search index

**Status:** Accepted
**Date:** 2026-08-13
**Context:** `REQ-SB-02-US-01` (`Implementation/UserStories/REQ-SB-02-US-01-
browse-and-search.md`) resolves (`ESC-022`, Resolved) that search must be "a
real ranked keyword/full-text relevance mechanism (e.g. BM25-style
term-frequency scoring across frontmatter/tags/body, boosted by field) —
not a bare substring match, not embeddings" (`REQ-SB-06`/P2 stays out of
scope), with the exact library/implementation choice left as "ordinary
implementation latitude... left to `/plan-tasks`" (the story's own
Constraints). This ADR is that `/plan-tasks` decision: it is a genuine,
alternatives-bearing mechanism choice — not merely restating already-
settled requirement scope — the same class of decision this project has
repeatedly written a dedicated ADR for (`ADR-011`'s keyword-match-vs-NLU
chat-action-triggering choice; `ADR-017`'s deterministic keyword-substring
Hub-routing choice). Forces: (1) Scenario 4's own falsifiable bar — a note
with only an incidental body substring match must rank *below* a note whose
title/tags genuinely match, which a bare term-frequency-only score does not
guarantee on its own (a long incidental mention can out-count a short exact
title match without field weighting and without discounting very common
terms); BM25's saturating term-frequency component (diminishing returns per
repeated occurrence of the same term) plus inverse-document-frequency
weighting (rare/specific terms score higher than common ones) directly
implements "relevance over raw substring count," and field-weighting
(title/tags boosted over body) directly implements the story's own worked
example; (2) real, grounded scale — 496 notes today (`ADR-024`'s own cited
figure), growing gradually, not by orders of magnitude; (3)
`vault_indexing.get_index()` is already a full, in-memory `dict[str, dict]`
rebuilt wholesale on every trigger (`ADR-024`) — no persisted/incremental
index exists to build a ranking structure on top of, and none is warranted
at this scale; (4) this project's own repeated "proportionate first, no new
dependency unless the built-in/hand-rolled path is proven insufficient"
precedent (`ADR-011`, `ADR-022`, `ADR-024`'s own SQLite rejection).

**Decision:**

1. **Field-weighted BM25 scoring, computed at query time — no
   persisted/precomputed ranking structure.** A search request tokenizes
   the query and each candidate note's three fields (title/subject, tags,
   body) into lowercase word tokens (simple regex word-splitting, no
   stemming/stopword removal — proportionate for a personal single-user
   vault at this scale, not a general-purpose search engine), computes
   standard BM25 term-frequency/inverse-document-frequency statistics fresh
   on every call (document frequency counted across every currently-indexed
   note), and sums a per-field BM25 score weighted title > tags > body
   (concrete weights, e.g. title=3x/tags=2x/body=1x, are implementation-
   internal tuning constants, adjustable without a superseding ADR since
   the decision here is the mechanism, not the tuning values), returning
   notes ordered descending by combined score, ties broken by stem for
   determinism. **Title/tags come directly from `vault_indexing.
   get_index()`'s already-in-memory entries (`frontmatter`/`tags`); body
   text does not** — `ADR-024`'s own index entry shape (`REQ-SB-01-US-01-
   T02`) deliberately never stores a note's raw body text (only
   `outgoing_wikilinks`, already extracted from it), so `search()` reads
   each candidate note's body fresh via `vault_writer.read_note(entry
   ["path"])` at query time — the same "re-read every note under a scope on
   every request, no caching" precedent `my_day.py::list_email_items`/
   `list_calendar_items` already establish, applied here to the whole
   index's candidate set instead of one kind-folder. This is a read-time
   cost (bounded, ~500 small markdown files at today's real scale), not a
   change to `ADR-024`'s own stored index shape — `vault_search.py` composes
   `vault_writer.read_note` directly for this one field, the same way
   `my_day.py` already composes `vault_writer` directly elsewhere in this
   codebase.
2. **A small, self-contained, pure-Python BM25 implementation**, new code
   inside `app/business/vault_search.py` (no new module) — no third-party
   ranking library.
3. **No new persisted or cached ranking index of any kind** — every search
   recomputes IDF/term-frequency statistics from `vault_indexing.
   get_index()`'s live snapshot on every call, mirroring `ADR-024`'s own
   "small enough to just rebuild/rescan wholesale" posture rather than
   introducing a second, separately-maintained data structure that could
   drift from the vault index itself.

**Alternatives Considered:**

- **A third-party ranking library (`rank_bm25` or similar).** Rejected:
  adds a new runtime dependency for what is, in practice, a small (~30-40
  line), well-understood formula; `rank_bm25`'s own API has no native
  field-weighting (the story's own "title and tags should outweigh an
  incidental body mention" bar), so using it would still require
  hand-writing a field-weighting wrapper around it — at which point the
  library buys little over writing the (smaller) core formula directly. Not
  proportionate at 496 notes, and not this project's established pattern
  (`ADR-022` chose a plain SDK client over pulling in more of LangChain for
  a narrower need; `ADR-024` rejected a real database for a query surface
  with no proven need).
- **Hand-rolled TF-IDF-lite scoring** (raw term-frequency × inverse-
  document-frequency, no BM25 saturation term). Rejected: BM25's saturating
  term-frequency component is specifically what keeps a long, repetitive
  incidental body mention from mathematically outscoring a short, exact
  title/tag match purely by repeating the term many times — a plain TF-IDF
  score doesn't bound a single field's contribution the same way, making
  Scenario 4's own worked example (a note with one incidental body mention
  must rank last, even against notes with real title/tag matches) a harder
  guarantee to hold structurally rather than by tuned coincidence. The
  story's own resolved Constraint names "BM25-style" as the settled
  technique bar specifically, not TF-IDF generically.
- **A bare substring/keyword match, unranked or ranked only by match
  count.** Rejected outright — this is exactly what the story's own
  Scenario 4 and its own PRD breadcrumb ("Search should be relevant to real
  queries, not a bare substring match") explicitly rule out; already
  settled at `/spec` time, restated here only as the rejected floor this
  ADR must clear.
- **Semantic/embedding-based search.** Rejected — explicitly out of scope
  for this story and deferred to `REQ-SB-06` (P2); building it now would be
  exactly the speculative-generality this project has repeatedly declined
  (`ADR-024`'s own precedent, itself citing `ADR-011`).
- **A precomputed/persisted inverted index or cached IDF table**, rebuilt
  alongside `vault_indexing.rebuild_index()`. Rejected as premature: at 496
  notes, computing IDF/term-frequency statistics fresh from the in-memory
  dict on every query is cheap (a linear scan of already-in-memory, small
  documents), and a second, separately-maintained ranking structure
  introduces a real staleness risk between it and `vault_indexing`'s own
  already-established full-rebuild-and-swap model, for a performance
  problem that does not exist yet. Revisit (supersede this ADR, don't
  silently swap) if/when real usage shows per-query scan latency is a
  genuine problem at the vault's actual scale — the same conditional-
  revisit posture `ADR-024` already established for its own storage shape.

**Consequences:**

- Search quality is bounded by BM25's own known characteristics (a
  lexical/keyword relevance model, not semantic understanding) — a query
  using different words than a note's own vocabulary will not match, by
  design; this is explicitly acceptable this pass (`REQ-SB-06`, P2, is the
  deferred semantic-search refinement).
- Every search request is `O(notes × query terms)` in scoring cost, plus
  one `vault_writer.read_note()` file read per candidate note (for body
  text, since it is not stored in the index) — proportionate at today's
  ~500-note scale, recomputed fresh (no caching), so a note added/edited
  via the next `vault_indexing.rebuild_index()` is immediately reflected in
  the very next search with zero invalidation logic needed. If this
  per-search file-read cost ever becomes the dominant latency factor at a
  larger real scale, storing body text on the index entry itself (a
  `REQ-SB-01-US-01`/`ADR-024`-side change, not this ADR's) is the concrete
  fix to revisit — not something this ADR pre-empts speculatively now.
- The three field weights (title/tags/body) and the standard BM25 constants
  (`k1`, `b`) are implementation-internal tuning values, not locked by this
  ADR or by any AC — free to adjust later without a superseding ADR, since
  the mechanism (field-weighted BM25 over the live index) is this
  decision's actual scope, not its specific constants.
- If the vault grows enough that per-query full-scan latency becomes a
  real, measured problem, or if BM25's lexical-only model proves
  insufficient for real queries, that is a concrete reason to revisit this
  ADR (supersede it) — not a reason to pre-optimize or pre-empt with
  embeddings now.

## ADR-027: To-Do (Outlook Tasks) capture — Tasks-folder COM-read function, an EntryID-keyed lookup index as the dedup/top-up mechanism (not a recomputed-path check), Task-specific Compass customer classification, and scheduler/working-mode reuse

**Status:** Accepted
**Date:** 2026-08-13
**Context:** `REQ-SB-09-US-01`
(`Implementation/UserStories/REQ-SB-09-US-01-todo-notes-from-outlook-tasks-
capture.md`) requires Outlook Tasks-folder items to become Task-type vault
notes on the same recurring schedule email/meeting capture already run
(`ADR-005`), the third capture pipeline after Email (`ADR-005`) and Meetings
(`ADR-008`, dedup key later corrected twice — `ADR-013`, `ADR-019`). The
story itself resolved the source (Outlook's own Tasks folder,
`ESCALATIONS.md` → `ESC-024`, Resolved) and a proposed schema, but
explicitly left several mechanism questions to this pass: (1) the
Tasks-folder COM-read function's shape/fields; (2) the dedup/top-up key —
the story's own Constraints explicitly call out this project's own
twice-repeated lesson (`ADR-008`→`ADR-013`→`ADR-019`) that an
Outlook-documented "unique" identity field cannot be trusted at face value,
and ask the architect to verify empirically before choosing one; (3) the
customer-classification call shape (reuse `classify_email` as-is, or a
Task-specific variant); (4) whether a third capture pipeline changes
`ADR-008` point 4's own explicitly-anticipated fork ("revisit if a third
pipeline makes the email-scoped module name genuinely misleading").
**Honest scoping note on point (2):** the architect role in this pipeline
has Read/Glob/Grep/Edit/Write tooling only — no shell/code-execution access
to run a live check against the real Outlook mailbox the way
`REQ-SB-08-US-01-T06`'s own live verification did. This ADR reasons through
the dedup-key decision structurally instead (below) and explicitly assigns
a live-verification step to the coder who builds `T01`, matching this
project's standing practice of never trusting an Outlook identity-field
uniqueness claim without live confirmation — it defers, rather than skips,
that confirmation.

**Decision:**

1. **New sync function `list_outlook_tasks(limit: int = 100)` in
   `app/data_access/outlook_com.py`**, mirroring `list_recent_mail`'s
   conventions exactly (plain synchronous function, `pythoncom.
   CoInitialize()`/`CoUninitialize()` bracketing, best-effort per-item
   `try/except: continue`). `ns.GetDefaultFolder(13)` (`_OL_FOLDER_TASKS`,
   new constant — `OlDefaultFolders.olFolderTasks`). **No date-window
   parameters (`days_back`/`days_ahead`), unlike `list_calendar_events`** —
   a task has no "did/will this occur near now" framing the way a meeting
   does; an undated or far-future-due task is still relevant until
   completed. A flat `limit`, mirroring `list_recent_mail`'s simpler
   unbounded-by-date shape, is the closer precedent. Per-item fields
   returned: `id` (`EntryID`), `subject`, `due` (`DueDate`, ISO date string
   — **normalized to `None` when Outlook's own "no date set" sentinel is
   detected**, since `TaskItem.DueDate` is never a true null in COM; a
   defensive guard here is what makes the resolved schema's "`due` (if
   set); omitted if none is set" possible at all, not optional polish),
   `status` (`TaskItem.Status`/`Complete`, mapped per point 2 below),
   `body` (`TaskItem.Body`, capped the same way `list_recent_mail` caps
   email bodies — reuses `_MAX_BODY_CHARS`, no new constant). **No
   `IncludeRecurrences`-equivalent property exists on the Tasks folder's
   `Items` collection at all** — this is a structural fact about the
   Outlook Object Model (`Items.IncludeRecurrences` is documented and
   implemented specifically for the Calendar folder), not an empirical
   claim about this mailbox's data, and it is the key reason point 3's
   dedup reasoning differs from Calendar's: Tasks are never expanded into
   multiple simultaneously-returned occurrence-items sharing one
   underlying identity property, the exact mechanism that broke `EntryID`
   and `GlobalAppointmentID` for Calendar (`ESC-002`, `ESC-012`). A
   recurring Outlook Task instead shows as a single live item at a time.
2. **Status mapping, a three-value business rule, not a raw pass-through of
   Outlook's own five-value `OlTaskStatus` enum** (matches the resolved
   schema's `Not Started | In Progress | Completed`, exactly): `Complete ==
   True` → `"Completed"` (the `Complete` boolean is authoritative,
   independent of `Status`, per Scenario 5's own "status field honestly
   reflects that it is complete"); else `Status == olTaskInProgress (1)` →
   `"In Progress"`; else (`olTaskNotStarted`, `olTaskWaiting`,
   `olTaskDeferred`) → `"Not Started"`. Recorded here, not as a separate
   ADR line, the same way `meeting_classification.py`'s attendee-majority
   tie-break was recorded in `architecture.md` rather than ADR'd
   separately — a business-rule mapping within already-established
   primitives, not a new tool/framework/structural-boundary choice.
3. **Dedup/top-up key: `EntryID`, looked up through a new load-bearing
   `.second-brain/task_note_index.json` (`{entry_id: note_filename_stem}`)
   consulted BEFORE any path is computed from current Outlook fields — not
   Meeting's own "recompute the deterministic path fresh from current
   fields, then `exists()`-check it" mechanism.** This is a genuine,
   reasoned divergence from `ADR-019`'s Meeting mechanism, forced by a real
   difference between the two stories' own ACs: Meeting's dedup only ever
   needed to survive reruns of an *unchanged* `start` timestamp — no
   Meeting AC requires a rescheduled meeting to still resolve to its
   original note. **Scenario 6 explicitly requires the opposite for Tasks**
   — "the scheduled capture run processes that same Outlook Task item again
   (e.g. because its due date or status changed in Outlook)... only missing
   or changed baseline fields are topped up." If the Task-note filename
   were recomputed from the *current* `due` value on every run (Meeting's
   own pattern, substituting `due` for `start`), a due-date edit between
   runs would produce a different filename and silently create a
   **duplicate** note instead of topping up the original — directly
   violating Scenario 6. A dedup key built from any mutable field (`due`,
   `status`, or a hash combining either) cannot satisfy this AC; the key
   must be something Outlook does not change when the same item's other
   properties are edited. `EntryID` is exactly that (standard COM/MAPI
   behaviour: an item's `EntryID` does not change when its own properties
   are edited in place, only if it moves store/folder) — used here for a
   different reason than Calendar tried it for: not as a claimed-unique
   filename disambiguator recomputed fresh each time (`ADR-008`'s original,
   later-falsified approach), but as a **stable lookup key into an index
   this pipeline itself owns and controls**, so it never needs to be
   Outlook-globally-unique across everything, only stable and distinct
   across *this mailbox's own Tasks folder contents* — a materially weaker,
   more defensible claim. **Filename construction happens once, at first
   capture, and is then frozen**: `<subject>-<capture-date>-<entry-id
   [-8:]>.md` under `Work/Tasks/`, where `capture-date` is the date the
   note was first written (not `due`, which is exactly the field Scenario 6
   requires the filename to be stable against). The index maps
   `entry_id → note_filename_stem` at that same moment; every later run
   looks up the stem by `entry_id` first — if found, tops up that exact
   note regardless of what `due`/`status`/`subject` now read as in Outlook;
   if not found, this is genuinely a new item, so a new note (and a new
   index entry) is created. `Work/Tasks/` follows `Work/Meetings/`'s own
   precedent exactly — a fixed folder (own note type, not a
   Compass-classified `kind`), auto-discovered by `list_known_kinds()`'s
   existing directory scan with no code change needed there. Exact new
   `vault_writer.py` primitive names (e.g. `load_task_note_index`/
   `lookup_task_note_stem`/`record_task_note`) are left to the
   decomposer/coder — this generalizes the project's existing "a small
   `.second-brain/*.json` sibling, paired load/save primitives" shape
   (`processed_meeting_ids.json`, `conversation_index.json`) to a genuinely
   load-bearing (not merely audit) lookup, the same shape
   `conversation_index.json`'s `find_related_note_stems`/
   `record_conversation_note` already established (a real
   key → value(s) index, not a flat set) — reused, not invented fresh.
   **Honestly disclosed, not silently assumed:** `EntryID` stability
   *across edits to the same live Task item* was not live-verified against
   the real mailbox this pass (see Context) — the structural argument in
   point 1 (no occurrence-expansion mechanism exists for Tasks, unlike
   Calendar) is why this is judged safe enough to proceed rather than
   block, but it is a reasoned, not an empirically-confirmed, safety claim.
   The coder building `T01`/`T02` must live-verify EntryID stability/
   uniqueness across a real capture-then-rerun cycle against the real
   Outlook Tasks folder as part of that task's own verification (this
   project's standing practice for every Outlook-identity-field claim,
   `ADR-008`'s own Consequences precedent) — a live collision or
   instability finding, if any, is grounds for a superseding ADR, not a
   silent workaround.
4. **Customer classification: a new, Task-specific Compass function,
   `compass_client.classify_task(subject, body, known_customers) -> {
   "customer": str, "confidence": float}`, not a reuse of `classify_email`
   as-is.** `classify_email`'s existing prompt jointly derives two axes
   (`customer` AND `kind`) and is worded around an "inbox item"/`From:`
   framing; Tasks need only the customer axis (folder placement is fixed —
   point 3 — not Compass-classified) and have no sender at all. Reusing
   `classify_email` as-is would force a discarded `kind` guess into every
   call and misrepresent an absent sender in the prompt. `classify_task`
   is a customer-only sibling prompt (`subject` + `body`, `known_customers`
   list, same "Unsorted rather than guessing" fallback posture), living
   alongside `classify_email` in `compass_client.py` — one more
   classification function in an already-established one-function-per-
   classification-shape module, not a new client/protocol/module.
5. **Scheduler and working-mode reuse — rides `REQ-SB-07`'s existing hourly
   job, extends `ADR-005`/`ADR-008` point 4/`ADR-018`, reopens none of
   them.** `"todo-capture"` is already a registered agent in
   `agent_registry.py` (pre-seeded ahead of this story, `REQ-SB-13-US-01`)
   with a placeholder "Task source" setting value — `working_mode_registry`
   's existing self-healing default (`"autonomous"`) already covers it with
   zero code change to that module. `email_classification.
   run_capture_and_record_completion` gains a **third** explicit per-agent
   gated block, structurally identical to the existing `"meeting-capture"`
   one (Autonomous → `run_capture_for_agent("todo-capture")` → a new
   `run_event` history entry; Supervised → a `trigger="background"`
   pending-approval + `"proposal"` history entry; Manual → skip silently,
   no record). `run_capture_for_agent` gains a `"todo-capture"` branch
   calling a new `app/business/todo_classification.py::
   classify_recent_todos()`, mirroring `meeting_classification.py`'s own
   shape (fetch → classify by customer → write/top-up Task note → link
   customer hub after a confirmed match only, same granular-primitives-
   only carve-out `people_extraction.py`/`meeting_classification.py`
   already established → dedup via point 3). `capture_scheduler.py`
   requires **zero code changes** — the third pipeline in a row to prove
   `ADR-005`'s own Consequences section right that "generalizing the one
   job" scales past two pipelines with no scheduler-layer change.
   `agent_registry.py`'s `"todo-capture"` entry's placeholder "Task source"
   setting value should be updated to name the resolved source ("Outlook
   Tasks folder") — an ordinary data-only registry edit, decomposer/coder
   task-level detail, not an architectural decision.
6. **`run_capture_and_record_completion` stays inside
   `email_classification.py` — not extracted into a new dedicated
   orchestration module.** `ADR-008`'s own Alternatives Considered
   explicitly named this exact fork point for future revisit ("Revisit if
   a third capture pipeline (e.g. REQ-SB-09) makes the email-scoped module
   name genuinely misleading"). This ADR is that revisit, and resolves it:
   **no extraction, this pass**, per `CLAUDE.md`'s minimal-changes
   discipline — the function is already self-documented as "Scheduling-
   layer entry point," decoupled in doc-comment intent from the file it
   physically lives in; a third explicit `if mode == ...` block reads no
   more confusingly than the second one `ADR-008` already added without
   extracting. Extraction (e.g. a new `app/business/
   capture_orchestration.py`) remains available as a later call if a
   *fourth* pipeline makes the email-scoped module name clearly
   unworkable — not pre-built speculatively now.

**Alternatives Considered:**

- **`GlobalAppointmentID` as the Task dedup key** — not applicable at all:
  `GlobalAppointmentID` is an `AppointmentItem`-only COM property; Outlook's
  `TaskItem` does not expose it.
- **Recompute the deterministic filename fresh from current Outlook fields
  every run, then `exists()`-check it (Meeting's exact `ADR-019`
  mechanism, substituting `due` for `start`)** — rejected: Scenario 6
  explicitly requires a due-date/status change to still resolve to the
  *same* existing note; a recomputed-from-`due` filename would silently
  duplicate on exactly that rerun. This is the central reasoned divergence
  this ADR makes from its own closest precedent, not an oversight.
- **A structural hash of `subject` + `due` (`ADR-019`-style, no Outlook
  identity field at all)** — rejected for the same reason: `due` is
  precisely the field Scenario 6 requires stability against, so it cannot
  be part of the dedup key's own input, structurally hashed or not.
- **Reuse `classify_email` as-is for Task customer classification** —
  rejected: forces a discarded `kind` guess into every call and
  misrepresents a Task's absent sender inside a prompt worded around
  "inbox item"/`From:` framing designed for email. A small, customer-only
  sibling function is more honest and no more code than adapting the
  existing one to ignore half its own output.
- **A time-windowed Tasks fetch (`days_back`/`days_ahead`, mirroring
  `list_calendar_events`)** — rejected: no AC calls for it, and a task has
  no natural "occurs near now" framing the way a meeting does — an
  undated or far-future task remains relevant indefinitely until
  completed, unlike a calendar occurrence that has a genuine temporal
  window of relevance.
- **Extract a new `app/business/capture_orchestration.py` module now,
  moving `run_capture_and_record_completion` out of
  `email_classification.py`** — considered, since `ADR-008` itself flagged
  this as the natural revisit point for a third pipeline. Rejected for
  this pass per `CLAUDE.md`'s minimal-changes discipline: the change is
  purely organizational (no behavioural difference), and three sibling
  gated blocks in one already-self-documented "scheduling-layer entry
  point" function is not yet confusing enough to justify a file move that
  touches every existing call site's import. Left as a concrete, named
  option for a future fourth pipeline, not silently dropped.

**Consequences:**

- New dependency-free capability: `list_outlook_tasks` in
  `outlook_com.py`, following `list_recent_mail`'s conventions (no new
  library).
- New load-bearing state file, `.second-brain/task_note_index.json` (the
  tenth `.second-brain/` state file) — unlike most of this project's prior
  state files (flat audit-only sets, e.g. `processed_meeting_ids.json`),
  this one is directly consulted for top-up-vs-create control flow, not
  merely descriptive. Worth naming explicitly for future maintainers as a
  different shape from the audit-trail convention most other state files
  follow.
- New `app/business/todo_classification.py`, mirroring
  `meeting_classification.py`'s shape (fetch → classify by customer →
  write/top-up → dedup via the index above → link customer hub after a
  confirmed match only).
- New Task-note `vault_writer.py` primitives following the established
  insert-only-if-missing baseline-preservation contract (Person/Customer-
  hub/Meeting precedent); the single-target `insert_body_line_if_missing`
  is reused as-is for the `**Customer:** [[Hub]]` line — **no new
  growable-line primitive is needed** (unlike Meeting's `upsert_
  attendee_links`), since a Task note links no Person/attendee list at
  all, per the story's own Constraints.
- New `compass_client.classify_task`, a second classification prompt
  function alongside `classify_email` — both live in the same module, no
  new client/protocol.
- `agent_registry.py`'s `"todo-capture"` entry's "Task source" setting
  value needs a small data-only text update (its current placeholder
  reads "Open question — resolved at /spec (REQ-SB-09)").
- Known, honestly-flagged risk carried forward, not silently assumed: this
  ADR's `EntryID`-stability reasoning (point 3) is structural, not
  empirically confirmed against this mailbox's real Tasks data — the
  architect pass that authored this ADR had no live-Outlook execution
  capability available in this environment. If a future live capture-then-
  rerun cycle shows two distinct Task items sharing an `EntryID`, or an
  `EntryID` changing across an in-place edit to the same item, that is
  grounds for a superseding ADR — the same honest-disclosure posture
  `ADR-008` took for Calendar before its own claim was twice falsified
  live (`ESC-002`, `ESC-012`).
- `ADR-008` point 4's own explicitly-anticipated "revisit if a third
  pipeline..." fork is now resolved (point 6, above): no orchestration-
  module extraction this pass. `ADR-005` and `ADR-008` both remain
  `Accepted`, unmodified — this ADR extends both, reopens neither.
