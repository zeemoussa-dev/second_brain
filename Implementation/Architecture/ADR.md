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

**Status:** Accepted, point 3 partially superseded by ADR-057 (Partner gains affiliate_of) — points 1, 2, 4, 5 unaffected
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

**Status:** Superseded by ADR-030 (point 2 only)
**Superseded note (2026-08-13, append-only — the body below is otherwise
unchanged, per this file's own "never edit an Accepted ADR" rule):**
`ADR-030` (`REQ-SB-37-US-01`, Agent Creation Wizard) replaces this ADR's
Decision point 2 only — "the known-agent-and-actions registry is a small,
static, hardcoded Python dict... not a persisted/mutable concern" no longer
holds: `agent_registry.py` now merges the still-static, still-code-held
`_SEED_AGENTS` (the 7 agents this point originally described, unchanged)
with a new persisted `.second-brain/agents_registry.json` overlay, so an
agent can be created at runtime with no source-code change. Decision points
1 (keyword/substring trigger-phrase matching, not NLU), 3 (only an
already-real pipeline gets a real action handler), and 4 (the unified
communication-history JSON file shape) are untouched and remain `Accepted`
— see `ADR-030` for the full reasoning and the load-bearing fact (every
already-`Done` self-healing per-agent registry composes `agent_registry.
list_agents()`/`get_agent()` fresh, uncached, on every call) that made this
a safe, zero-downstream-code-change reversal rather than a breaking one.
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
real meeting note (a real recurring-meeting subject, redacted here) was
created under that scheme by an unattended scheduled capture run that
happened *between* this ADR being written and `T06`'s rebuild session
(the old code was still live in that window). This does **not** change
the decision itself — the tier's removal is still correct (the field
remains confirmed non-unique-per-occurrence, `ESC-012`; keeping a tier
with a live-confirmed defect for one retroactive note is not a
reasonable trade) — it only corrects the factual claim of zero instances
to "zero as of this ADR's own authoring; one real, bounded, human-
recoverable instance surfaced during the gap before rebuild." No code
change results; the one affected note needs a manual human glance
(delete/merge against its own successor note) — not automated here.

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
`web_search`-capable agents through a
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

---

## ADR-028: Unified agent capability model, phase 1 — read-only Actions migrated to Skills via a per-Skill `mutates` field and an explicit `invoke_skill` `trigger` parameter; `ADR-011`'s chat funnel dispatch changes, the funnel itself is not rebuilt — extends `ADR-011`, `ADR-014`, `ADR-015`, `ADR-020`, `ADR-022`, reopens none of them

**Status:** Accepted
**Date:** 2026-08-13
**Context:** `REQ-SB-39-US-01` (`Implementation/UserStories/REQ-SB-39-US-01-
unify-capabilities-model-and-read-only-migration.md`) is an operator-
confirmed, PRD-breadcrumb-named "genuine architecture reversal" of
`ADR-011` point 2's "agent identity/actions stay hardcoded" framing:
every capability any agent has — including every capability that exists
today as a hardcoded `agent_registry.py` Action — must become a Skill,
granted/revoked through the one mechanism `REQ-SB-27-US-01` already built,
"including existing shipped agents," not just future wizard-created ones
(`ESCALATIONS.md` → `ESC-029`). The analyst split the full reversal into
two sequential stories (`ESC-029`) so a mutating capability is never
observably ungated even transiently; this ADR covers **only** `US-01`'s
own scope — the capability model itself plus the 3 currently `"mutates":
False` action ids (`view_last_run`, `ask_question`, `view_channel_status`,
across the 4 already-shipped agents that carry them: `email-capture`,
`meeting-capture`, `todo-capture`, `people-producer`, `vault-qa`).
`REQ-SB-39-US-02` (the mutating-Action migration + working-mode gate
extension) is explicitly out of this ADR's scope and composes on top of
it. Live inspection of the real code (not PRD-text assumption) confirms
three concrete facts this ADR must design around:
- `app/business/agent_registry.py`'s static `AGENTS` catalog is the sole
  source `app/business/agent_chat.py::handle_chat_message`'s keyword-match
  funnel (`ADR-011`) reads for trigger phrases, and the sole source
  `app/api/agents_router.py::_invoke_action`'s working-mode gate
  (`ADR-020`) reads for an action's `mutates` classification. Removing an
  entry from it, or restructuring `agent_chat.py`'s own matching loop,
  would touch both mechanisms at once — a materially larger blast radius
  than this story's own operator-directed "minimal blast radius" framing
  for Scenario 4 calls for.
- `app/business/skill_registry.py::invoke_skill(agent_id, skill_id, args)`
  and `app/api/skills_router.py`'s `POST /agents/{agent_id}/skills/
  {skill_id}/invoke` check only `has_skill_access` today — no `trigger`
  parameter exists anywhere on this path, and no working-mode check reaches
  it. Exactly right for `REQ-SB-27`'s own narrow, read-only skills to date
  — this ADR must add the `trigger` *shape* `REQ-SB-39-US-02` will need to
  gate on, without adding gating behaviour itself (out of this story's own
  Non-Goals: "Extending the working-mode gate to Skills at all").
- `app/business/skill_tools.py`'s `SKILLS` catalog (`diagram-understanding`,
  `web-research`) carries no `mutates` field at all today — this is a
  genuinely new, structural addition to the catalog's own shape, not a
  parameter tweak, mirroring exactly how `ADR-020` added the same field one
  layer down to `agent_registry.py`'s action definitions.
- `app/business/agent_orchestration/mcp_client.py::load_agent_tools`
  (`ADR-022` point 6) already filters every registered Skill-catalog tool
  by `skill_registry.has_skill_access` for the general LangGraph
  conversational loop — this is a separate, already-correct access-grant
  filter (not a working-mode gate); nothing here needs to change it.

**The three mechanism-level decisions below are operator-directed, relayed
for architecture record, not re-derived by this pass** (the operator made
them directly, having reviewed the real code and this story's own
mechanism-level open questions). The remaining decisions (the migration
catalog/grant seeding shape, the capability-list unification shape, the
result-shape translation, and which existing call sites gain the new
`trigger` parameter) are this pass's own architectural resolution of the
"how" underneath those three directives.

**Decision:**

1. **`mutates` becomes a static `bool` field on every `skill_tools.SKILLS`
   catalog entry — mirrors `ADR-020` point 1's `agent_registry.py` action
   shape exactly** (a structural fact about the catalog entry itself, not
   computed per-invocation from `args`). Applied to **every** entry, not
   only the 3 newly-migrated ones — `diagram-understanding` and
   `web-research` both gain `"mutates": False` (both are read-only:
   `diagram-understanding` is an honest-unavailable stub, `web-research`
   only ever reads the web and returns a summary, writing nothing) as a
   same-shape consequence of adding a field to a shared catalog, not new
   functional scope. **Fail-safe default, mirroring `ADR-020` point 1
   exactly:** a catalog entry that ever omits the field is treated as
   `mutates: True` by any future gate that reads it — an unknown skill is
   gated as if it writes, never silently allowed through. This field is
   deliberately **not consulted by any gate in this story** — `invoke_skill`
   (point 2) threads `trigger` through but does not yet branch on `mutates`
   or `trigger` together; `REQ-SB-39-US-02` is the pass that adds the real
   two-axis check, reusing `_invoke_action`'s own corrected logic
   (`ADR-020` point 2) against this exact field.
2. **`invoke_skill(agent_id, skill_id, args, trigger)` gains a required,
   no-default `trigger: Literal["chat", "direct", "hub_routed"]`
   parameter — mirrors `_invoke_action(agent_id, action_id, trigger)`'s
   existing shape exactly**, including the same three values and the same
   "no default, every call site must be explicit" discipline (`_invoke_
   action` has never had a default for `trigger` either). Every real call
   site is updated to pass a concrete value, reasoned per site, not
   guessed uniformly:
   - `app/api/skills_router.py`'s `POST /agents/{agent_id}/skills/
     {skill_id}/invoke` — **hardcodes `trigger="direct"` server-side,
     never accepts a client-supplied value.** Mirrors `POST /agents/
     {agent_id}/actions/{action_id}`'s own hardcoded `trigger="direct"`
     (`agents_router.py::trigger_action`) and this codebase's standing
     "never trust a caller-supplied trust-level/identity value" posture
     (`skill_registry.invoke_skill`'s own existing `agent_id`-injection
     docstring reasoning, `ADR-022` point 5's Correction addendum) — a
     caller cannot claim `trigger="chat"` to reach a future looser gate
     path by simply setting a JSON field.
   - `app/api/agents_router.py`'s dispatch paths (point 4, below) — pass
     `trigger="direct"` (from `trigger_action`) or `trigger="chat"` (from
     `chat()`), the exact values `_invoke_action` already receives from
     the same two call sites today.
   - `app/business/agent_orchestration/knowledge_bootstrap.py`'s existing
     `skill_registry.invoke_skill(research_expert_id, "web-research",
     {"query": subject})` call — gains `trigger="hub_routed"`: this call
     is itself the product of `ADR-017`'s Hub-routing match (`hop1`), the
     same semantic `ADR-020` point 3 already reserved the `"hub_routed"`
     value for on the Actions side. This is the **first real call site**
     to ever pass `trigger="hub_routed"` on either the Actions or Skills
     path — `ADR-020`'s own "kept as named forward-looking correctness,
     not dead code" framing is realized here, one release early and on
     the Skills side rather than Actions.
3. **`ADR-011`'s chat keyword-match funnel is extended at its dispatch
   step only — `agent_registry.py` and `agent_chat.py` are both left
   completely unmodified by this story.** `agent_chat.handle_chat_message`
   keeps reading `agent["actions"]` and matching trigger phrases exactly
   as today, including for the 3 migrated ids — their existing action
   entries in `agent_registry.py`'s static `AGENTS` catalog (id, label,
   `trigger_phrases`, `"mutates": False`) are **not removed and not
   edited**. What changes is `app/api/agents_router.py`'s own dispatch,
   in both `trigger_action` and `chat()`: **wherever a matched/requested
   id is a member of `skill_tools.SKILLS`, the call routes to
   `skill_registry.invoke_skill(agent_id, id, args=None, trigger=...)`
   instead of `_invoke_action(agent_id, id, trigger=...)`; every other id
   (the still-real Actions: `run_capture_now`, `pause_schedule`,
   `rebuild_person_note`, `build_knowledge`) keeps calling `_invoke_action`
   exactly as today.** This membership check (`id in skill_tools.SKILLS`)
   is the **only** new "is this migrated" logic anywhere in the system —
   no separate migration-id list/constant is introduced, because the
   migrated Skill catalog entries deliberately **reuse their exact former
   Action id string** (`view_last_run`, `ask_question`,
   `view_channel_status` — not new kebab-case ids like `web-research`'s).
   This identity continuity is what makes both the untouched chat-matching
   input (`agent["actions"]`) and the new dispatch-time membership check
   correct with zero duplicated bookkeeping. **A small result-shape
   translation is required** (architecturally load-bearing, exact helper
   name left to the decomposer/coder): `skill_registry.invoke_skill`'s
   varying return shapes (`{"status": "unknown_skill"}`,
   `{"status": "refused", "reason": ...}`, or a skill handler's own
   `{"available": bool, "message": str}` honest-unavailable envelope) must
   normalize into the `{"status", "message"}` envelope
   `agents_router.py`'s existing post-dispatch code already expects
   (`result["status"] not in ("pending", "refused")` gates the run_event
   append; `result["message"]` becomes the chat reply) — `"refused"`'s
   `reason` maps to `message` so Scenario 6's honest refusal still reaches
   the user as a chat reply with no new history entry, mirroring Manual's
   existing silent-skip-but-reply posture exactly one layer over.
4. **Migrated Skill handlers (`view_last_run`, `ask_question`,
   `view_channel_status`) are new zero-arg `@mcp_server.tool()` functions
   in `skill_tools.py`, each unconditionally honest-unavailable** —
   identical posture to `diagram_understanding`'s own existing stub (no
   real handler exists for any of the three today; `_ACTION_HANDLERS` in
   `agents_router.py` never carried an entry for them either, confirmed by
   direct reading). This satisfies Scenario 3 ("no change in behaviour is
   observable") at the only level that is actually true today — there was
   never real behaviour to preserve, only an honest "not yet available"
   reply, which the migrated Skill continues to give. Registering them as
   ordinary `@mcp_server.tool()` entries (not excluded from the LangGraph
   conversational loop the way `web-research` was, `ADR-022` point 5) is a
   deliberate, harmless consequence, not a new decision: `mcp_client.
   load_agent_tools`'s existing per-agent `has_skill_access` filter
   (`ADR-022` point 6) already governs every registered skill tool
   generically — a granted agent's free-form chat can now also reach these
   three via the general conversational path, in addition to the exact
   keyword-phrase funnel, with zero code change to that filter.
5. **Retrofit of existing agents: a one-time, explicitly-scoped migration
   seed inside `skill_registry.py`, not a general self-healing default.**
   Per the operator's own directive ("Everything, including existing
   shipped agents" — not just new wizard-created ones), the 4 real,
   already-shipped agents that carried these 3 Action ids today must gain
   the equivalent Skill **grant**, not just have the mechanism exist for a
   hypothetical future agent. A new, small, literal mapping —
   `{"view_last_run": ["email-capture", "meeting-capture", "todo-capture",
   "people-producer"], "ask_question": ["vault-qa"], "view_channel_status":
   ["vault-qa"]}` — is folded into `skill_registry._load_state()`,
   idempotently granting each pair exactly once (reusing `grant_skill_
   access`'s own already-idempotent "only append if not already granted"
   behaviour), the same "seed once, on first load" shape `provider_
   registry._seed_state()` already established for the pre-seeded
   "Compass" Provider entry. **This is deliberately framed as a one-time
   historical migration backfill of a known, fixed, named set — not a
   reopening of `REQ-SB-27-US-01`'s own stated "deliberately no
   self-healing default-assignment... an agent gets skill access only via
   an explicit grant" principle**, which stays true going forward for any
   genuinely new Skill: this seed only ever re-grants exactly the 3
   already-migrated ids to exactly the 4 agents that already had the
   equivalent Action, once, and never grows to cover a future Skill
   without its own explicit new mapping entry and its own new architecture
   decision.
6. **New capability-list aggregator, `skill_registry.
   list_agent_capabilities(agent_id) -> list[dict]`**, composing
   `agent_registry.get_agent(agent_id)["actions"]` (filtered to exclude any
   id that is also a `skill_tools.SKILLS` member — i.e., the still-real
   Actions only: `run_capture_now`, `pause_schedule`, `rebuild_person_note`,
   `build_knowledge`, agent-dependent) with `list_agent_skills(agent_id)`
   (the agent's granted Skills, including the 3 migrated ones), returned as
   one combined list. Placed in `skill_registry.py` (which already imports
   `agent_registry`, an established one-directional dependency — putting
   this the other way around, inside `agent_registry.py`, would need it to
   import `skill_registry`, a layering direction this project has never
   used and should not introduce here). `app/api/agents_router.py::
   get_agent`'s response is changed from a bare `"actions": [...]` (sourced
   directly from `agent_registry.py`'s array) to `"capabilities": [...]`
   (sourced from this new aggregator) — the `"actions"` key is **removed**,
   not kept alongside a new `"skills"`/`"capabilities"` key, so the
   frontend has no way to reconstruct two separate lists even
   accidentally, directly satisfying Scenario 7's "no separate 'Actions'
   section shown alongside a separate 'Skills' section." The exact
   per-item field shape (reconciling Actions' `{"id","label"}` with
   Skills' `{"id","name","description"}` into one uniform item shape) is
   ordinary decomposer/coder-level latitude, not a further architectural
   fork.

**Alternatives Considered:**

- **Remove the 3 migrated ids from `agent_registry.py`'s per-agent
  `actions` arrays entirely, moving their `trigger_phrases` onto the new
  `skill_tools.SKILLS` catalog entries, and extending `agent_chat.
  handle_chat_message` to also scan the agent's granted skills** —
  rejected: this is a real rebuild of the funnel's own matching input and
  logic (two data sources instead of one, a new merge step), directly
  contradicting the operator's explicit "`ADR-011`'s chat keyword-match
  funnel is NOT rebuilt... only its dispatch step changes... minimal blast
  radius" directive. It would also touch `agent_chat.py`, a file with zero
  functional need to change for this story's own scope.
- **Compute a migrated-id set from a new explicit constant (e.g.
  `skill_tools.MIGRATED_ACTION_IDS = {"view_last_run", "ask_question",
  "view_channel_status"}`) instead of the `id in skill_tools.SKILLS`
  membership check** — rejected as redundant bookkeeping: since the
  migrated Skill ids deliberately reuse their former Action id string,
  `skill_tools.SKILLS` membership already is exactly that set: a second,
  separately-maintained constant could drift from the catalog itself with
  no compiler/test to catch it.
- **A general self-healing default-assignment for Skills (mirroring
  `section_registry.py`/`provider_registry.py`/`working_mode_registry.py`'s
  "any known agent absent from `assignments` gets the default" shape)** —
  rejected: `REQ-SB-27-US-01`'s own Non-Goals explicitly left "should some
  skills default to all agents" unresolved, and a blanket self-heal would
  silently grant every future Skill to every agent with no explicit
  decision — the wrong default for a cross-cutting, deliberately
  explicit-grant capability model. The scoped, one-time, named-mapping
  migration seed (point 5) achieves the operator's actual directive
  (retrofit these specific 4 agents onto these specific 3 already-had
  capabilities) without reopening that unresolved general question.
- **A dedicated `POST /poc/retrofit-agent-skills` endpoint (mirroring the
  vault-note retrofit family — `retrofit_customer_hub_links`,
  `retrofit_people_from_emails`, `retrofit_email_importance`)** —
  rejected: those retrofits exist because they process potentially
  hundreds of already-captured *vault notes*, a genuinely different scale/
  class of operation needing an explicit, re-runnable, observable trigger.
  This retrofit is four small, fixed, known `.second-brain/
  agent_skills.json` grants — the auto-seed-on-first-load shape
  `provider_registry._seed_state()` already established for the "Compass"
  Provider is the closer, lighter-weight precedent.
- **Preserve the exact literal Action-era unavailable message ("This
  action is not yet available.") for the 3 migrated Skill stubs, instead
  of the existing Skill-stub convention ("This skill is not yet available
  — no real handler has been built for it.")** — considered, for the
  most literal reading of Scenario 3's "no change in behaviour is
  observable"; not mandated here, since Scenario 3's own substance is "the
  capability still honestly refuses, never fabricates," not "the exact
  placeholder string is byte-identical," and consistency with every other
  Skill's own honest-unavailable wording better serves the unified model
  this story exists to build. Left as decomposer/coder-level copy latitude
  either way — not a functional regression in either reading.
- **Bind the 3 migrated skills into `run_agent_conversation`'s LangGraph
  tool loop, but exclude them from `mcp_client.load_agent_tools`'s general
  filter the way `web-research` was excluded (`ADR-022` point 5)** —
  rejected: `web-research`'s exclusion was scoped specifically to keep a
  *new, first-of-its-kind* skill's blast radius narrow while its own
  invocation contract was still being proven out; these 3 are honest
  no-op stubs with zero real side effects to worry about, so there is no
  proportional reason to special-case them out of the general filter
  `ADR-022` point 6 already built for exactly this purpose.

**Consequences:**

- `app/business/skill_tools.py`'s `SKILLS` catalog grows from 2 to 5
  entries; every entry now carries `"mutates": bool` — a structural field
  `REQ-SB-39-US-02` will read directly for its own gate extension, with no
  further catalog-shape change expected at that point.
- `app/business/skill_registry.py::invoke_skill`'s signature is a breaking
  change for any caller that does not pass `trigger` — both of today's two
  real callers (`skills_router.py`, `knowledge_bootstrap.py`) are updated
  by this same pass; a future caller that forgets it fails loudly at
  Python's own call-site, by design (no default value to silently paper
  over a missed update).
- `app/api/agents_router.py::get_agent`'s response shape changes
  (`"actions"` removed, `"capabilities"` added) — a real, but internal,
  interface change: `AgentDetailPanel.tsx` (frontend) is the only real
  consumer (confirmed by this story's own `## Affected Screens`; no
  external caller, including Hermes, reaches this endpoint), so this is
  safe to change in the same pass rather than needing an additive/
  deprecation period.
- `agent_registry.py`'s per-agent `actions` arrays now carry entries whose
  real invocation no longer routes through them at all for the 3 migrated
  ids (`_invoke_action`/`_execute_action` are never reached for
  `view_last_run`/`ask_question`/`view_channel_status` post-migration) —
  their continued presence there is deliberately vestigial, serving only
  `agent_chat.py`'s unmodified trigger-phrase matching. A future story that
  removes them from `agent_registry.py` (once, for example, the chat
  funnel itself is eventually redesigned to read trigger phrases from the
  Skill catalog directly) would need its own superseding ADR — not silently
  assumed as a natural next step by this one.
- `.second-brain/agent_skills.json`'s `"assignments"` map gains 4 agents'
  worth of new entries the first time `skill_registry._load_state()` runs
  after this ADR ships — a one-time, observable state change, not a
  recurring seed (idempotent thereafter).
- `REQ-SB-39-US-02` inherits a real, load-bearing foundation from this
  ADR: `mutates` already exists on every Skill catalog entry (point 1),
  `trigger` already threads through every real `invoke_skill` call site
  (point 2) — its own gate-extension work is adding the actual branching
  logic inside `invoke_skill` (mirroring `_invoke_action`'s corrected
  two-axis check, `ADR-020` point 2), not inventing either piece of shape
  from scratch.

---

## ADR-029: Working-mode gate extended to Skills, keyed inside `invoke_skill` itself (not mirrored into `agents_router.py`) — the 4 mutating Actions migrate to Skills in the same pass; a new ungated `_dispatch_skill` primitive backs both the gate's own fallthrough and the Pending-Approvals Approve endpoint — extends `ADR-020`, `ADR-028`, `ADR-021` point 5's `action_id` reuse precedent, reopens none of them

**Status:** Accepted
**Date:** 2026-08-13
**Context:** `REQ-SB-39-US-02` (`Implementation/UserStories/REQ-SB-39-US-02-
unify-capabilities-working-mode-gate-and-mutating-migration.md`) is the
safety-critical second half of the same operator-directed reversal
`ADR-028` began: every mutating capability — including the 4 that exist
today as hardcoded `agent_registry.py` Actions (`run_capture_now`,
`pause_schedule`, `rebuild_person_note`, `build_knowledge`) — must honor
the agent's own working mode after becoming a Skill, exactly as it does
today as an Action, with **zero transient window** where a mutating
capability is invocable ungated (`ESCALATIONS.md` → `ESC-029`). `ADR-028`
explicitly scoped this out of its own decision ("`REQ-SB-39-US-02`...is
explicitly out of this ADR's scope and composes on top of it") — this ADR
is that composition, not a reopening.

Live inspection of the real code (not PRD-text assumption) confirms four
concrete facts this ADR must design around:

- `app/api/agents_router.py::_invoke_action` (`ADR-020` point 2) is the
  gate for Actions — but it lives in the **api** layer and today has
  exactly two real call sites, both inside the same file
  (`trigger_action`, `chat()`). `skill_registry.invoke_skill` (`ADR-028`
  point 2), by contrast, has **three** real call sites spanning two
  layers: `app/api/skills_router.py`'s own direct invoke endpoint (the
  REQ-SB-27 surface this story's Scenario 8 names explicitly as a
  possible bypass), `app/api/agents_router.py`'s dispatch fork (`ADR-028`
  point 3, for the 3 already-migrated read-only ids and, after this ADR,
  the 4 newly-migrated mutating ones), and `app/business/
  agent_orchestration/knowledge_bootstrap.py`'s own Hub-routed call
  (`trigger="hub_routed"`). The third call site is a **business** module —
  `ADR-003`'s one-directional `api → business → data_access` layering
  forbids it from importing anything out of the `api` layer, so a gate
  living in `agents_router.py` (mirroring `_invoke_action`'s own location
  literally) is not just stylistically inconsistent, it is
  **structurally unreachable** from `knowledge_bootstrap.py` without
  violating `ADR-003`.
- `agent_registry.py`'s `_ACTION_HANDLERS` dispatch table (confirmed by
  direct reading, not the story's own Context paraphrase) wires a **real**
  handler to only 2 of the 4 mutating action ids' agent pairs today:
  `("email-capture", "run_capture_now")` →
  `run_capture_and_record_completion`, and `("compass-expert",
  "build_knowledge")` → `_run_build_knowledge` (→
  `knowledge_bootstrap.bootstrap_agent_knowledge`). The other 5 real
  (agent, action) pairs that carry these 4 ids — `meeting-capture`'s and
  `todo-capture`'s own `run_capture_now`, all 3 agents' `pause_schedule`,
  and `people-producer`'s `rebuild_person_note` — have **no wired handler
  in `_ACTION_HANDLERS` today**; `_execute_action`'s existing `handler is
  None` branch already returns the honest "This action is not yet
  available." for every one of them via the direct/chat funnel (their real
  underlying business logic — `meeting_classification.
  classify_recent_meetings`, `people_extraction.ensure_person_note` — is
  real and used by the **background** scheduler pipeline, `ADR-018` point
  4, but was never wired to the on-demand Action). Migrating faithfully
  means the Skill equivalents preserve this exact honest/dishonest split,
  not silently make the unwired 5 newly real (this story's own Constraint:
  "a gating/declaration refactor, not a rewrite of what any capability
  actually does").
- `app/business/pending_approval_registry.py::create_pending_approval`'s
  `action_id: str | None` parameter is **already** used generically for a
  non-`agent_registry`-declared id — `ADR-021` point 5's Tier-2
  `propose_new_top_level_area` id is stored in this exact field today, and
  `app/api/pending_approvals_router.py`'s Approve endpoint already
  dispatches on `record["action_id"]` via its own `_APPROVAL_HANDLERS`
  table before falling through to the `agent_registry`-Action-only
  `_execute_action` path. Reusing this same field for a skill_id is a
  same-shape extension of an already-proven pattern, not a new one.
- `app/api/pending_approvals_router.py` already imports a **private**
  function across module boundaries — `from app.api.agents_router import
  _execute_action` — to bypass `_invoke_action`'s gate on Approve ("the
  approval itself is the authorization; re-entering the gate would find
  the agent still Supervised and defer forever," `ADR-018` point 6). This
  is direct, live precedent for this ADR's own equivalent need on the
  Skills side.

**Decision:**

1. **The gate lives inside `skill_registry.invoke_skill` itself — not
   mirrored into `agents_router.py`.** This is the one function all three
   real call sites already pass through unconditionally (`ADR-028` point
   2's own "no default, every call site explicit" `trigger` threading), so
   putting the two-axis check here is what makes Scenario 8 ("never a
   route around the gate") true **by construction** — no caller can reach
   a Skill's real dispatch without passing through this one gate, and no
   caller-side discipline is required to keep it that way. This also
   avoids the `ADR-003` layering violation `knowledge_bootstrap.py` would
   otherwise force (Context, above).
2. **Gate logic is inserted between the existing `has_skill_access` check
   and the existing handler-dispatch step — the pre-existing
   `unknown_skill`/access-`refused` order is unchanged.** Access-grant
   (`has_skill_access`) is a genuinely different, prior axis ("can this
   agent reach this skill at all") than working mode ("does invoking it
   right now need approval") — checking access first avoids ever creating
   a pending-approval record for a skill the agent was never granted.
   Mirrors `ADR-020` point 2's exact two-axis shape, keyed off
   `skill_tools.SKILLS[skill_id]["mutates"]` (`ADR-028` point 1) instead of
   `agent_registry.get_action(...)["mutates"]`:
   - **Manual + `trigger == "hub_routed"`:** refuse — `{"status":
     "refused", "reason": "This agent is in Manual mode — it does not act
     on another agent's request."}` — the same field name (`"reason"`,
     not `_invoke_action`'s `"message"`) `invoke_skill`'s own existing
     access-`refused` shape already uses, so `skills_router.py`'s existing
     `result.get("reason", ...)` 403-mapping needs no change. Today
     unreachable via any real call site with a **mutating** skill (only
     `knowledge_bootstrap.py` passes `trigger="hub_routed"`, and only for
     `web-research`, `mutates: False`) — kept as the same named
     forward-looking correctness `ADR-020` point 3 already established for
     Actions, realized here on the Skills side.
   - **Supervised + `mutates is True` (or unresolvable — fail-safe `True`,
     `ADR-028` point 1):** short-circuits into a pending-approval record —
     `pending_approval_registry.create_pending_approval(agent_id, trigger,
     action_id=skill_id, description=f"{skill_name} ({agent_name})",
     payload=args)`, reusing the `action_id` field for `skill_id` (Context,
     above — `ADR-021`'s own precedent) and the existing `payload` field to
     carry the invocation's own `args` so Approve (point 3, below) can
     replay them. Appends the same `"proposal"` history-entry kind
     `_invoke_action` already appends (`ADR-018`). Returns `{"status":
     "pending", "message": f"Proposed — {skill_name}. Awaiting your
     approval.", "pending_approval_id": approval["id"]}` — identical shape
     to `_invoke_action`'s own pending response.
   - **Supervised + `mutates is False`, Autonomous (any trigger), Manual
     (`"chat"`/`"direct"` trigger):** fall straight through to dispatch
     (point 3, below) — identical decision table to `ADR-020` point 2's
     points 3–5, one field-source over.
3. **New raw, ungated dispatch primitive, `skill_registry._dispatch_skill
   (agent_id, skill_id, args) -> dict`** — the exact pre-this-ADR body of
   `invoke_skill` (the `_SKILL_HANDLERS` lookup + the existing `agent_id`-
   injection-if-the-handler-declares-it logic), extracted unchanged, called
   both by `invoke_skill`'s own post-gate fallthrough and by
   `pending_approvals_router.py`'s Approve endpoint (point 4, below) —
   mirrors `_execute_action`'s own "thin gate wraps unconditional dispatch"
   split (`ADR-018` point 3) one layer over, for the identical reason:
   re-entering `invoke_skill`'s own gate on Approve would find the agent
   still Supervised and defer forever (`ADR-018` point 6).
4. **`pending_approvals_router.py`'s Approve endpoint gains one new branch,
   checked before its existing `_APPROVAL_HANDLERS` / generic
   `_execute_action` chain:** `elif record["action_id"] in
   skill_tools.SKILLS: result = skill_registry._dispatch_skill(
   record["agent_id"], record["action_id"], record["payload"])` — mirrors
   the file's own already-existing cross-module private-function import
   (`from app.api.agents_router import _execute_action`, Context, above) by
   adding an equivalent import from `skill_registry`. Without this branch,
   a pending mutating-Skill approval would silently fall into the existing
   `elif record["action_id"] is not None: _execute_action(...)` branch,
   which resolves `_ACTION_HANDLERS.get((agent_id, skill_id))` — never a
   match for a skill_id — and would incorrectly report "This action is not
   yet available." on Approve instead of actually running it. This is the
   concrete mechanism Scenario 2 ("Approving a pending mutating Skill
   invocation executes it") requires.
5. **Migration: the 4 mutating action ids become `skill_tools.SKILLS`
   entries with `"mutates": True`, added to `_SKILL_HANDLERS`, preserving
   exactly today's real/honest-unavailable split (Context, above) — no
   new real behavior is built by this pass.** `run_capture_now` and
   `build_knowledge` gain real Skill handlers that call through to the
   same real functions their Action counterparts already call
   (`run_capture_and_record_completion`, `_run_build_knowledge`'s own
   `knowledge_bootstrap.bootstrap_agent_knowledge` translation) — for
   `run_capture_now` specifically, since the Skill catalog is agent-
   agnostic (one entry, not one per agent), the handler resolves which
   agent's own capture pipeline to run from the injected `agent_id`
   (mirrors `web_research`'s own existing `agent_id`-resolves-real-backend
   pattern, `ADR-022`'s Correction addendum — not a new shape).
   `pause_schedule` and `rebuild_person_note` gain honest,
   unconditionally-unavailable Skill handlers — identical posture to
   `ADR-028` point 4's 3 read-only stubs — since neither has a real
   wired handler to preserve today.
6. **`agent_registry.py`'s per-agent action arrays for these 4 ids stay in
   place, unedited — vestigial, chat-funnel-matching only — mirroring
   `ADR-028` point 3's identical "leave in place" precedent.** No new
   dispatch-fork code is needed in `agents_router.py`'s `trigger_action`/
   `chat()`: `ADR-028` point 3's existing `id in skill_tools.SKILLS`
   membership check already routes any id present in the catalog to
   `invoke_skill(...)` instead of `_invoke_action(...)` — once these 4 ids
   are added to `skill_tools.SKILLS` (point 5, above), that same,
   already-built membership check picks them up automatically. The 2 now-
   unreachable `_ACTION_HANDLERS` entries (`("email-capture",
   "run_capture_now")`, `("compass-expert", "build_knowledge")`) become
   dead code post-migration (never reached — the membership check
   intercepts before `_invoke_action`/`_execute_action` are ever called for
   these ids again); left in place rather than deleted, since removing
   them is unrelated cleanup outside this story's own scope, not a
   functional requirement of any Scenario.
7. **Retrofit: the existing one-time migration-grant seed
   (`skill_registry._load_state()`, `ADR-028` point 5) gains 4 new
   id→agent-list entries, same idempotent shape as the 3 already there:**
   `"run_capture_now": ["email-capture", "meeting-capture",
   "todo-capture"]`, `"pause_schedule": ["email-capture", "meeting-
   capture", "todo-capture"]`, `"rebuild_person_note":
   ["people-producer"]`, `"build_knowledge": ["compass-expert"]` — 5
   distinct real agents in total across the 4 ids (`email-capture`,
   `meeting-capture`, `todo-capture`, `people-producer`, `compass-expert`),
   confirmed by direct reading of `agent_registry.py`'s own `AGENTS`
   catalog, not guessed. Same "seed once, on first load, idempotent
   thereafter" discipline, not a reopening of `skill_registry.py`'s "no
   self-healing default-assignment" principle for any future Skill.
8. **Atomicity, concretely defined for a single-process dev app with no
   staged rollout:** "the gate extension and the migration land together,
   in the same release" (this story's own Constraint) means the two halves
   must never exist in the running app in a state where the 4 catalog
   entries/grants (point 5, 7) are present **without** the gate branch
   (point 2) already live in the same code — there is no real deploy
   boundary to enforce this technically (one FastAPI process, restarted as
   a whole, `ADR-005`'s own "in-process" framing), so this is a
   **task-sequencing** discipline for the decomposer, not a code
   mechanism: the gate-logic task, the Approve-endpoint task, and the
   4-id-migration-plus-retrofit task must be `depends_on`-chained with **no
   intermediate task marked `Done` that a real app restart between tasks
   could ever run** with the catalog change but not the gate change (or
   vice versa) — concretely, the migration/retrofit task must `depends_on`
   the gate-logic task, never the reverse or a parallel-independent
   ordering, since a running app with the migration alone but not the
   gate would have `invoke_skill` dispatch a mutating capability
   completely ungated, which is exactly the outcome `ESC-029`'s two-story
   split exists to prevent.

**Alternatives Considered:**

- **Mirror `_invoke_action`'s own location literally — put the gate in
  `agents_router.py`, wrapping `skill_registry.invoke_skill`** — rejected:
  structurally unreachable from `knowledge_bootstrap.py` (a business
  module) without violating `ADR-003`'s one-directional layering
  (Context, above); even setting layering aside, it would require **three**
  separate call sites (`skills_router.py`, `agents_router.py`'s own
  dispatch, `knowledge_bootstrap.py`) to each remember to call the gate
  wrapper instead of `invoke_skill` directly — exactly the kind of
  caller-discipline-dependent bypass risk Scenario 8 exists to close, where
  centralizing inside `invoke_skill` itself closes it by construction.
- **A gate implemented as a decorator applied to `invoke_skill`, instead
  of inline logic** — considered, for aesthetic symmetry with a future
  second gated business function; not adopted: this codebase has no
  existing decorator-based gate precedent (`_invoke_action`'s own gate is
  plain inline logic), and introducing one for a single call site is
  process/tooling novelty this story does not need to justify.
- **A new `.second-brain/agent_pending_approvals.json` `skill_id` field,
  parallel to `action_id`, instead of reusing `action_id` for both** —
  rejected: `action_id` is already proven generic (`ADR-021` point 5's
  Tier-2 ids), and `pending_approvals_router.py`'s Approve dispatch already
  switches on one field (`record["action_id"]`); a second, parallel
  optional field would need every existing dispatch branch to check both,
  for no behavioural gain over reusing the field that already means "the
  id of the thing being approved."
- **Build real handler behavior for the 5 currently-unwired mutating
  (agent, action) pairs (meeting/todo-capture's `run_capture_now`, all 3
  `pause_schedule`, `rebuild_person_note`) as part of this same
  migration** — rejected: out of this story's own Constraint ("a
  gating/declaration refactor, not a rewrite of what any capability
  actually does"); mirrors `ADR-028` point 4's identical precedent for the
  3 read-only stubs — an honest "not yet available" Skill is not a
  regression from an equally honest "not yet available" Action.
- **Treat the gate-extension and migration as two independently-shippable
  tasks with no ordering constraint, trusting `/implement-sprint`'s own
  task-at-a-time discipline to land them close together** — rejected: "close
  together" is not "atomic" for the exact failure mode this story's own
  split exists to prevent (a mutating capability observably ungated even
  transiently); an explicit `depends_on` edge from the migration task onto
  the gate-logic task is a real, cheap guarantee the decomposer can encode
  directly, not a hope about ordering.

**Consequences:**

- `app/business/skill_registry.py::invoke_skill` gains the two-axis gate
  (point 2) and a new `_dispatch_skill` primitive (point 3) — its
  signature is unchanged from `ADR-028` point 2 (`agent_id, skill_id, args,
  trigger`); every existing caller continues to compile unchanged, only its
  observable behavior for a granted **mutating** skill under Supervised/
  Manual+hub_routed now differs from before this ADR (previously
  unconditional, now gated) — the load-bearing, intended change.
- `app/api/pending_approvals_router.py` gains one new import
  (`skill_registry`) and one new Approve-dispatch branch (point 4) — its
  existing `_APPROVAL_HANDLERS`/`_execute_action` branches are unedited.
- `app/business/skill_tools.py`'s `SKILLS` catalog grows from 5 to 9
  entries (the 3 `ADR-028` already added, plus these 4); `_SKILL_HANDLERS`
  in `skill_registry.py` grows to match. 2 of the 4 new handlers
  (`run_capture_now`, `build_knowledge`) call through to real, already-
  shipped business logic; 2 (`pause_schedule`, `rebuild_person_note`) are
  honest stubs, matching today's real/unavailable split exactly.
- `.second-brain/agent_skills.json`'s `"assignments"` map gains 5 real
  agents' worth of further entries (`email-capture`, `meeting-capture`,
  `todo-capture`, `people-producer`, `compass-expert`) the first time
  `skill_registry._load_state()` runs after this ADR ships.
- `agent_registry.py`'s `_ACTION_HANDLERS` table's 2 real entries become
  dead code (point 6) — a named, deliberate consequence, not a silently
  discovered one; a future cleanup pass removing them needs no new ADR
  (removing already-unreachable code is not a structural decision), but is
  not this story's own job.
- **Resolves the safety-critical half of `ESCALATIONS.md` → `ESC-029`** —
  once this ADR's tasks are `Done` (per point 8's sequencing discipline),
  no mutating capability on any of the 5 real retrofitted agents is ever
  invocable through any real call site (chat, direct trigger, Hub-routed
  request, or the direct skill-invocation endpoint) without the
  working-mode gate applying to it — the same guarantee `ADR-020`
  established for Actions, now extended to Skills without a transient gap.

## ADR-030: Agent registry becomes a static-seed-plus-persisted-JSON-overlay store — `agent_registry.py` gains a `.second-brain/agents_registry.json` layer so agents can be created at runtime — supersedes ADR-011 point 2 only

**Status:** Accepted
**Date:** 2026-08-13
**Context:** `REQ-SB-37-US-01` (`Implementation/UserStories/REQ-SB-37-US-01-
agent-creation.md`) needs a real "create a new Expert agent from the app,
no source-code change" mechanism (Scenarios 1/3). `ADR-011` point 2
established, deliberately, that `app/business/agent_registry.py`'s `AGENTS`
dict is "a small, static, hardcoded Python dict... not a persisted/mutable
concern" — this is a direct reversal of that specific point, flagged in
advance as an open ADR-level question (`ESCALATIONS.md` → `ESC-020`), not a
silent workaround. The operator's own mechanism direction (relayed via the
decomposer/orchestrator, not re-derived here): a JSON-file-backed persisted
registry mirroring this codebase's own established no-database pattern —
the static dict becomes seed/default data merged with a new
`.second-brain/agents_registry.json` at load time; agent creation appends a
new entry to that JSON file; existing shipped agents remain addressable
exactly as they are today.

Live code inspection (not PRD-text assumption) confirms the load-bearing
fact `ESC-020` already named: every already-`Done` per-agent property
registry — `section_registry.py`, `provider_registry.py`,
`agent_keywords.py` (via `vault_writer.load_all_agent_keywords`/
per-agent reads), `working_mode_registry.py`, `skill_registry.py` — reads
`agent_registry.list_agents()` **fresh, uncached, on every call** (no
module-level caching anywhere in this codebase's registries) to self-heal
its own default per-agent assignment. None of those five modules needs to
change for a created agent to be picked up automatically — they already
compose `agent_registry.list_agents()`/`get_agent()` exactly as `ADR-014`
point 1 and `ADR-017`/`ADR-018`/`ADR-028` intended; the only real change
needed is inside `agent_registry.py` itself, so that those two functions
start reporting a created agent at all.

`app/business/skill_registry.py`'s `_load_state`/`_save_state`
(`grant_skill_access`/`revoke_skill_access`) is the closest, most direct
precedent for "a persisted JSON overlay composed alongside a related static
concern" already in this codebase, and is mirrored here, not reinvented.

**Decision:**

1. **New `vault_writer.py` primitives, `load_agents_registry_state()` /
   `save_agents_registry_state()`**, byte-for-byte mirroring
   `load_skills_state()`/`save_skills_state()`'s existing shape (`ADR-014`
   point 1's "pure I/O, returns `None` if the file doesn't exist, no
   default content computed in `data_access`" contract): reads/writes
   `.second-brain/agents_registry.json`, a new eleventh `.second-brain/`
   state file alongside `agent_sections.json`/`agent_providers.json`/
   `agent_skills.json`/etc.
2. **`agent_registry.py`'s existing module-level `AGENTS` dict is renamed
   `_SEED_AGENTS` and is otherwise byte-identical** — all 7 entries, same
   keys, same nested `settings`/`actions` shape, unchanged. It stays a
   plain Python dict, in code, not migrated into the JSON file — shipped
   agents remain, per `ADR-011` point 2's still-valid half, app/deployment
   configuration (the same category of static fact `ADR-011` compared to
   `Settings.self_email`), not something a user-facing create/edit flow
   ever touches. This story's own Non-Goals explicitly do not require
   migrating the 7 seed entries into the persisted store, and this
   decision deliberately does not do so — see Alternatives, below.
3. **A new `_load_state()` (mirrors `section_registry.py`'s own
   `_load_state` shape exactly) owns only the *created* side:** reads
   `vault_writer.load_agents_registry_state()`; if `None`, seeds
   `{"created_agents": {}}` and persists it immediately (empty, not
   copying `_SEED_AGENTS` into the file — the JSON file's only job is to
   hold agents that did not ship with the codebase). No self-healing loop
   is needed here (unlike Sections/Providers) — there is nothing to
   default-assign; a created agent's own record already carries every
   field it needs at creation time (point 5, below).
4. **`get_agent(agent_id)` and `list_agents()` become seed-plus-persisted
   merges, in that order** (seed agents first, preserving today's existing
   7-agent ordering and every existing test/UI expectation of "email-
   capture, meeting-capture, todo-capture, people-producer, vault-qa,
   vault-filing-expert, compass-expert" appearing first): `get_agent`
   checks `_SEED_AGENTS` first, falls through to
   `_load_state()["created_agents"]` only on a miss; `list_agents` returns
   `[..._SEED_AGENTS entries..., ...created_agents entries...]`, same
   `{"id", "name", "type"}` projection as today, unchanged shape.
   `get_action(agent_id, action_id)` is unchanged in body (it already
   calls the now-merged `get_agent`, via `AGENTS.get` → `get_agent`
   internally) — a created agent's `actions: []` (point 5) means
   `get_action` always returns `None` for one, correctly falling into
   `agents_router.py`'s existing "not yet available" honest-unavailable
   path with zero code change there either.
5. **New `create_agent(name: str, type: str, settings: list[dict] | None =
   None) -> dict`.** `agent_id` is generated via
   `vault_writer.tag_slug(name)` — the same id-derivation function
   `section_registry.create_section`/`provider_registry.create_provider`
   already use, keeping every agent-identifying id in this codebase
   human-readable and consistent (`email-capture`, `compass-expert`,
   `widgets-expert`), not a UUID/integer. **Unlike `create_section`'s
   "slug collision returns the existing entry" idempotent semantic**,
   `create_agent` disambiguates on collision (`-2`, `-3`, ... appended)
   against the union of `_SEED_AGENTS` keys and `created_agents` keys —
   idempotent-on-collapse is wrong for agents, since two distinct
   agent-creation requests must never silently collide into one shared
   identity, and a created agent's slug must never be allowed to shadow a
   shipped agent's id. The new record — `{"name": name, "type": type,
   "settings": settings or [], "actions": []}` — is appended to
   `created_agents[agent_id]` and persisted immediately. `actions: []`
   mirrors the already-`Done` `vault-filing-expert`/`compass-expert`
   "starts with zero pre-seeded actions" precedent (`ESC-020`'s own
   resolution) — no bespoke-action mechanism is introduced by this ADR;
   `REQ-SB-39`'s Skills unification is the only path to a created agent
   ever gaining a capability, via the already-`Done`
   `skill_registry.grant_skill_access`, unchanged.
6. **A new `POST /agents` endpoint in `app/api/agents_router.py`** calls
   `agent_registry.create_agent(...)` and returns the same shape
   `GET /agents/{agent_id}` already returns (composing
   `section_registry`/`provider_registry`/`working_mode_registry`/
   `agent_keywords` exactly as that existing handler does) — the wizard's
   own Section assignment (Scenario 3) is a second, immediate
   `PATCH /agents/{agent_id}` call against the already-`Done`
   `update_agent_assignment` endpoint, not new logic in `create_agent`
   itself, keeping `agent_registry.py` ignorant of Sections/Providers
   exactly as `ADR-014` already established ("composed alongside, not
   inside").

**Alternatives Considered:**
- **Migrate all 7 shipped agents into `agents_registry.json` at first load
  (full-migration overlay, no code-held seed set at all)** — rejected:
  not required by this story's own Non-Goals ("migrating the seven
  existing static `AGENTS` entries... the architect's `/plan-tasks` call,
  not required here"); would introduce a first-run migration step and a
  live risk of the code and the JSON file drifting for agents this project
  still treats as deployment configuration (`ADR-011` point 2's "which
  agents exist is app/deployment configuration" reasoning is only reversed
  for *newly creatable* agents by this ADR, not for the 7 that ship with
  the codebase).
- **Mutate the module-level `AGENTS` dict in place at import/first-write
  time (`AGENTS[new_id] = {...}`) instead of a file-backed read-merge**
  — rejected: every other persisted registry in this codebase
  (`section_registry`/`provider_registry`/`skill_registry`/
  `working_mode_registry`) reads its state fresh from disk on every call,
  with no in-process cache, specifically so a restart or a second worker
  process never sees a stale or missing copy; an in-memory-only mutation
  would not survive a restart without the JSON file backing it regardless,
  so the file must be the source of truth either way — making the module
  dict a second, redundant cache duplicates state for no benefit and
  reintroduces the staleness class this codebase has consistently avoided
  elsewhere.
- **A new SQLite/other database table for agents** — rejected: no database
  exists anywhere in this stack (`ADR-005`, `ADR-011` point 4), no scale
  characteristic of a single user's own agent set justifies introducing
  one now.
- **A vault-note-per-agent scheme** (deriving the registry from a new
  `Work/Agents/` note convention) — rejected, unchanged from `ADR-011`
  point 2's own already-Accepted rejection: agents are not open-ended,
  user-authored vault content the way Customers/Kinds/Partners are;
  inventing a vault-note schema to satisfy the "derive from the vault"
  pattern would solve a problem that doesn't exist here.
- **Random UUID or incrementing integer agent_id instead of a
  name-derived slug** — rejected: breaks the existing human-readable id
  convention every other identity-bearing id in this codebase already
  uses (`email-capture`, `compass-expert`, and `tag_slug`-derived Section/
  Provider ids), which several real call sites rely on for readability
  (`_ACTION_HANDLERS` keys, communication-history file entries, chat
  trigger-phrase matching by agent name).
- **Collision handling that returns the existing agent on a slug match**
  (mirroring `create_section`'s own idempotent-collapse behavior) —
  rejected specifically for agents: two independently-submitted
  "create an agent" requests must never silently collapse into one shared
  identity the way two "ensure this Section exists" calls should — a
  numeric-suffix disambiguation (point 5) is used instead.

**Consequences:**
- `ADR-011` point 2 ("the known-agent-and-actions registry is a small,
  static, hardcoded Python dict... not a persisted/mutable concern") is
  **superseded, that point only** — points 1 (keyword-match action
  triggering), 3 (only a real pipeline gets a real handler), and 4
  (communication-history JSON shape) remain `Accepted` and untouched;
  `ADR-011`'s own Status line is updated with a superseded note pointing
  here, per this file's "linked both ways, never rewritten" rule.
- `agent_registry.py` gains its **first-ever** dependency on
  `app/data_access/vault_writer` and its first file I/O — previously the
  one registry every other agent-property module composed *alongside*
  without it depending on anything; every existing caller of `get_agent`/
  `list_agents`/`get_action` keeps its exact same call signature and
  return shape, so no call site outside `agent_registry.py` itself needs
  to change.
- Every already-`Done` self-healing per-agent registry
  (`section_registry.py`, `provider_registry.py`, `working_mode_registry.py`,
  `skill_registry.py`, `agent_keywords.py`) gains automatic support for a
  created agent with **zero code changes to any of those five files** —
  the concrete mechanism `ESC-020` flagged as needing an ADR-level
  decision, now resolved: their own `agent_registry.list_agents()` calls
  simply start returning one more entry.
- `agents_router.py::list_agents`/`get_agent` (the HTTP handlers) also
  need no change beyond composing the new `POST /agents` endpoint — they
  already treat `agent_registry.get_agent`/`list_agents` as their sole
  source of agent identity, uncached, on every request.
- A created agent's `actions: []` means Scenario 8 (chat/history work "the
  same way they already do for an existing agent") is satisfied by the
  conversational path (`agent_orchestration.run_agent_conversation`,
  `ADR-015`/`ADR-016`), not the keyword-matched action-trigger path —
  `agent_chat.handle_chat_message` already falls through to the
  conversational graph whenever no trigger phrase matches any declared
  action (unchanged), which is every message for a freshly created,
  zero-action agent.
- Future `REQ-SB-37-US-02`/`US-03` (Worker/Producer flows) will call this
  same `create_agent`, populating `settings` with Skills/Vault-Scope/
  Purpose data those stories define — this ADR's `create_agent` signature
  is deliberately permissive (`settings: list[dict] | None`) so those
  stories extend the call, they do not need to re-open this decision.

---

## ADR-031: Producer output-action fork resolved — a Producer's output action is a granted output Skill (single-select at creation), not a destination/write-mode field; Purpose is stored via `create_agent`'s existing `settings` kv-list (mirrors Expert's Domain), not a new field; one minimal placeholder output Skill (`write-to-vault-draft`) is seeded so the mechanism is exercisable — extends `ADR-030`, `ADR-028`, `ADR-029`, reopens none of them

**Status:** Accepted
**Date:** 2026-08-13
**Context:** `REQ-SB-37-US-03` (`Implementation/UserStories/REQ-SB-37-US-03-
agent-creation-producer-flow.md`) was flagged `gate: flagged` at `/spec`
specifically because the PRD's own text leaves the Producer "output action"
mechanism genuinely open (the operator's own breadcrumb trails off mid-
sentence: "Producers Need to have a Purpose and then do something with
[it]"). The story's own Context named two internally-consistent, equally-
valid readings and declined to guess (Pipeline.md MUST-FLAG trigger 8):
Reading A — the output action is itself a Skill, unifying with the same
mechanism `REQ-SB-39` establishes for a Worker's tools; Reading B — the
output action is a materially different concept, a destination/write-mode
configuration (a target Section + a write mode), not a grantable capability
at all.

**The operator has since directly resolved this fork (relayed for
architecture record, not re-derived here):** Reading A. A Producer's output
action is the exact same mechanism a Worker uses for its tools — a granted
Skill from the same Skills registry `REQ-SB-39`/`REQ-SB-37-US-02` already
wired up. Everything an agent "does" — reading (Worker tools, Expert domain
knowledge) or acting on its own purpose-driven output (Producer) — is a
Skill it holds. No parallel destination/write-mode field is introduced.

Direct inspection of the real, current `skill_tools.SKILLS` catalog (both
today's file and the catalog shape `ADR-028`/`ADR-029` add on top of it, per
this story's own hard dependency on both `REQ-SB-39-US-01`/`-US-02` landing
first) confirms a concrete fact this ADR must design around: **no existing
or already-planned Skill is a plausible output/destination Skill.** Every
catalog entry is either genuinely read-only (`diagram-understanding`,
`web-research`, and the 3 migrated `view_last_run`/`ask_question`/
`view_channel_status`) or a wrapper around an already-existing, narrowly-
scoped capture/build pipeline invoked by name (`run_capture_now`,
`pause_schedule`, `rebuild_person_note`, `build_knowledge` — none of which
accepts arbitrary Producer-authored content to write anywhere). A Producer
created under this story's own scope, as specced, would have **zero**
selectable output Skills — an honest empty state by the letter of the
catalog, but one that makes the operator's own newly-directed "the wizard's
second step lets the user grant it an output Skill" mechanism impossible to
exercise or verify at all, not merely sparse.

Separately, `REQ-SB-41-US-01`'s own Context (`Implementation/UserStories/
REQ-SB-41-US-01-agent-overview-surface.md`) found, by direct inspection, that
**no dedicated purpose/description field exists anywhere in the data model
or UI today** (`agent_registry.py`'s catalog carries only `name`, `type`,
`settings`, `actions`), and left "the exact data source for the Purpose
region" as its own still-open `/plan-tasks`-level question — that story is
still `Draft`, unbuilt, and does not resolve this. This story (`US-03`) is
the first to actually need a real, persisted Purpose value, and this ADR
decides where it lives.

**Decision:**

1. **Output action = a granted Skill, single-select at creation.** The
   Producer wizard's second step lets the user select exactly **one**
   output Skill (not a multi-select checkbox list) and, on submit, issues
   exactly one `POST /agents/{agent_id}/skills/{skill_id}` call — the
   identical, unmodified endpoint `REQ-SB-37-US-02`'s Worker step already
   calls per selected Skill (`skill_registry.grant_skill_access`,
   `ADR-028`/`ADR-029`), called here at most once. **Cardinality reasoning:**
   the PRD's own phrasing is consistently singular — "an output action,"
   "the exact Producer 'output action' shape" — and a Producer's identity is
   one Purpose paired with one way of acting on what it produces, structurally
   unlike a Worker's open toolbox of many Skills for varied read/query tasks.
   This is a **wizard-UI-level** choice only, not a data-model cap: the
   underlying grant mechanism (`agent_skills.json`) is untouched and already
   supports multiple grants per agent (proven by Worker's own multi-select);
   a human can still grant a second output Skill to a Producer later via
   `AgentDetailPanel.tsx`'s existing, agent-type-agnostic Skills grant/revoke
   control, unrestricted, exactly as for any other agent — restricting that
   already-`Accepted`, shared control per-agent-type would be a disproportionate
   new structural change this decision does not make.
2. **One minimal placeholder output Skill is seeded: `write-to-vault-draft`.**
   Added to `app/business/skill_tools.py`'s `SKILLS` catalog with
   `"mutates": True` (a real write-shaped capability, gated by the working-
   mode two-axis check `ADR-029` already built — no new gating code needed),
   a new `@mcp_server.tool()` stub function mirroring `diagram_understanding`'s
   exact honest-unavailable shape (`{"available": False, "message": "This
   skill is not yet available — no real handler has been built for it."}`),
   registered in `skill_registry.py`'s `_SKILL_HANDLERS`. **Reasoning:**
   without at least one real, selectable output Skill, the operator's own
   directed mechanism (a Skills-grant step in the Producer wizard) has
   nothing to render or verify against — the same "one illustrative stub to
   prove the plumbing, no real handler yet" precedent `REQ-SB-27-US-01`
   already established for `diagram-understanding`, applied here to the
   first Skill of a genuinely new *kind* in this catalog (a write-shaped,
   Producer-facing output capability, as opposed to every existing entry
   being either read-only or a wrapper around an already-existing named
   pipeline). This is **not** a violation of this codebase's honest-empty-
   over-fabrication standing pattern — the stub never fabricates a result,
   it honestly refuses every real invocation, exactly like every other
   stub Skill in this catalog; seeding it is scaffolding a real, honestly-
   labeled mechanism, not fabricating a working capability.
3. **Purpose is stored via `create_agent`'s existing `settings` kv-list —
   `[{"key": "Purpose", "value": purpose}]` — mirroring Expert's Domain
   exactly (`ADR-030` point 5/6), not a new field on the agent record and
   not Worker's empty-`settings` pattern.** This story is what actually
   introduces the first real Purpose value into the data model — it does
   **not** depend on `REQ-SB-41-US-01` landing first. `ADR-030`'s own
   Consequences section already anticipated this exact composition
   ("Future `REQ-SB-37-US-02`/`US-03` (Worker/Producer flows) will call this
   same `create_agent`, populating `settings` with Skills/Vault-Scope/
   Purpose data those stories define... they do not need to re-open this
   decision"). **Reasoning for reusing `settings`, not a new field:** Purpose
   is a single descriptive string, structurally identical to Expert's Domain
   (both are "the one thing that defines what this agent is about," entered
   once at creation, shown read-only thereafter) — not an operational,
   multi-concern config the way Worker's Skills/Scope/Section are, each of
   which needed its own separate persisted concern/endpoint. `REQ-SB-41-US-01`
   remains free to later decide, at its own `/plan-tasks` pass, whether to
   read Purpose from this same `settings` slot for every agent type or add a
   dedicated field — this ADR does not presume or block that future decision,
   it only settles where **this story's own** Producer Purpose value lives.
4. **Section assignment reuses Expert's sequential shape, not Worker's
   combined shape.** A Producer has no Scope-equivalent field to combine
   with Section in one `PATCH` the way Worker's Vault Scope does — so the
   wizard issues `POST /agents` (type `"producer"`, `settings` carrying
   Purpose) → grant the selected output Skill (point 1) →
   `PATCH /agents/{agent_id}` carrying `section_id` alone, mirroring
   `ADR-030` point 6's original Expert-only two-call shape, not `REQ-SB-37-
   US-02`'s combined-`PATCH` amendment.
5. **This story's own current Acceptance Criteria (Scenarios 1–5) cover only
   Purpose + Section — they do not yet include a Scenario for granting the
   output Skill.** This is a real, named gap between this now-resolved
   architecture and the story's own specced ACs, not silently papered over.
   The story's own Notes already anticipated exactly this path ("this
   story's own output-action half likely needs... an amendment here, since
   it has not yet reached `Done`, once a human/architect decision resolves
   the fork") — since the story has not reached `Done` (specs are append-only
   per completed work, not per artefact), the decomposer is directed to
   amend Scenario 2 (creating a Producer also grants the selected output
   Skill) and add a Scenario 4-equivalent (submitting without an output
   Skill selected) as part of locking this story's ACs, rather than this
   being re-routed through a fresh `/spec` pass — recorded here so the
   decomposer has the architectural basis to do so without re-deriving it.

**Alternatives Considered:**

- **Reading B — a destination/write-mode configuration (target Section +
  write mode), not a grantable capability** — rejected per the operator's
  direct resolution of the fork; also, independently, composes worse: every
  currently-mutating write path in this codebase (`rebuild_person_note`,
  `run_capture_now`) was already mid-migration to Skills under `REQ-SB-39-
  US-02` at the time this fork was named, so a parallel, non-Skill write-mode
  concept would have introduced a second, competing mutation mechanism
  alongside the one this project was actively unifying everything else onto.
- **Multi-select output Skills (mirroring Worker's step verbatim, no
  cardinality distinction between agent types)** — considered, for
  implementation symmetry with Worker; rejected because the PRD's own
  wording is consistently singular ("an output action") and because
  collapsing Producer and Worker into the identically-shaped step would
  erase the one conceptual distinction that actually exists between the two
  types (a Worker holds a toolbox of many capabilities; a Producer pairs one
  Purpose with one way of acting on its output) for no requirement that
  asked for it.
- **Leave the output-Skill catalog empty this pass, ship Purpose + Section
  only, defer the Skills-grant step entirely to a follow-on story** — this
  was the story's own original Non-Goals framing before the operator's
  resolution; superseded by the operator's direct instruction that the
  wizard's second step should grant an output Skill now. Rejected as the
  ongoing plan once that instruction was given, since an empty catalog would
  make the newly-directed step unbuildable/unverifiable, not merely deferred.
- **A brand-new, Producer-specific field on the agent record (e.g.
  `purpose: str` as a first-class column) instead of reusing `settings`** —
  rejected: `create_agent`'s `settings: list[dict] | None` kv-list already
  exists precisely for "the one descriptive/config fact this agent type
  needs," proven by Expert's Domain; adding a second, parallel single-value
  field for an structurally identical need would fork the agent record's own
  shape for no behavioral gain, and would pre-empt `REQ-SB-41-US-01`'s own
  still-open "is Purpose a `settings` entry or a dedicated field, for every
  agent type" question rather than leaving it open as intended.
- **A dedicated new endpoint (`POST /agents/{agent_id}/skills:grant-output`
  or similar) instead of reusing `POST /agents/{agent_id}/skills/{skill_id}`**
  — rejected: no behavioral or semantic difference exists between a Worker
  granting a tool Skill and a Producer granting an output Skill — both are
  "this agent may now invoke this Skill" — so a second endpoint would
  duplicate `grant_skill_access`'s own already-generic contract for no gain.

**Consequences:**

- `app/business/skill_tools.py`'s `SKILLS` catalog gains a tenth entry
  (`write-to-vault-draft`, `"mutates": True`) — the first catalog entry
  whose whole purpose is to exist as an *output* capability rather than a
  read or an existing-pipeline wrapper; `skill_registry.py`'s
  `_SKILL_HANDLERS` grows to match.
- `app/api/agents_router.py`'s `POST /agents` gains a third `type` branch
  (`"producer"`, alongside `"expert"`/`"worker"`), requiring `purpose` (a new
  request-body field) and building `settings=[{"key": "Purpose", "value":
  purpose}]` — the third and final agent-type branch anticipated by `ADR-030`
  point 6's original two-type design.
- A created Producer's `actions: []` (unchanged from Expert/Worker,
  `ADR-030` point 5) — its only real capability is whichever single output
  Skill was granted at creation (or none, if the decomposer's amended ACs
  ultimately treat it as optional — left to that pass), consistent with
  every other created agent's "starts with zero pre-seeded actions"
  precedent.
- The decomposer must amend this story's Scenario 2 and add a missing-
  output-Skill rejection Scenario before locking ACs (point 5, above) — a
  real, named follow-up this ADR creates, not an open-ended one: the
  mechanism (single grant call, one catalog entry to select from) is fully
  specified here.
- `REQ-SB-41-US-01`'s own still-open "Purpose data source" question is
  narrowed, not closed: it now has one real precedent (`settings` kv-list,
  used identically by Expert/Producer) to evaluate against when it reaches
  its own `/plan-tasks` pass, but this ADR does not decide that story's
  outcome for it.

## ADR-032: Agent Knowledge-Gap Tracking (`REQ-SB-40`) — a structured, intercepted-tool-call decline signal extending `ADR-015`'s conversation graph (mirrors `ADR-017`'s `request_cross_section_help` precedent); a new, dedicated `.second-brain/agent_knowledge_gaps.json` store, not `agent_activity.py`; a new Knowledge Gaps tab on the Agent Detail Panel, gated to Expert-type agents

**Status:** Accepted
**Date:** 2026-08-13
**Context:** `REQ-SB-40-US-01` (`Implementation/UserStories/REQ-SB-40-US-01-
agent-knowledge-gap-tracking-and-expert-readiness.md`) requires every
honest "I don't know" reply an Expert agent gives (`REQ-SB-33-US-01`'s
grounding/honest-uncertainty guardrail, `Done`) to be recorded as a
trackable, closeable knowledge gap, with the open-gap count as the
observable "how close to Expert" readiness signal. The story's own
Constraints left two mechanism questions open, resolved by the operator
and relayed to this pass rather than re-derived: (1) detection — a
structured signal the model itself emits, not a text pattern-match over
its reply; (2) storage — a new, dedicated per-agent log, not a reuse of
`REQ-SB-11-US-01`'s existing `agent_activity.py`. This ADR also resolves
the one question genuinely left to the architect: **where** the display
surface lives, since `/design` was explicitly skipped for this batch
(operator-directed) and `REQ-SB-41` (Agent Overview, the PRD breadcrumb's
own named "likely fit") remains unspecced with no prototype coverage.

Direct code inspection, not assumption, grounds every point below:
- `app/business/agent_orchestration/state.py::history_entries_to_messages`
  confirms `REQ-SB-33`'s honest-uncertainty behavior is one appended
  instruction on a single prepended `SystemMessage` — there is no
  structured field anywhere distinguishing an honest decline from an
  ordinary answered reply; the model's raw `response.content` is returned
  as `reply` either way.
- `app/business/agent_orchestration/graph.py::_call_model` confirms this
  graph has exactly one structured channel between the model and this
  codebase today: **bound tools** (`model.bind_tools(tools).invoke(...)`).
  There is no `with_structured_output`/JSON-response-format mechanism
  anywhere in this graph. Critically, this project already has a real,
  working precedent for using a bound tool purely as a structured signal
  rather than a real capability call: `request_cross_section_help`
  (`ADR-017`) is bound to the model, but its own function body is never
  actually invoked — `_route_after_model`'s conditional edge intercepts
  any call to it *before* the generic `_execute_tools` node and routes to
  a dedicated node (`_route_hub_request`) that performs the real work
  deterministically in Python, then loops back to `call_model` so the
  model produces its actual final reply afterward. This is exactly the
  "tool-call mechanism appropriate to how this graph already gets
  structured signals from the model" the story's own Constraints named as
  the preferred option, already proven out, not hypothetical.
- `app/business/agent_activity.py` confirms its own `_ACTIVITY_KINDS =
  {"run_event", "run_error"}` scope is deliberately narrow to
  background-run outcomes (its own story's Constraints) — a knowledge gap
  originates from a conversational turn, not a background run, so folding
  it in would widen a scope that story deliberately narrowed.
- `app/business/skill_registry.py` and `app/data_access/vault_writer.py`
  (its `load_skills_state()`/`save_skills_state()` pair, and the sibling
  `load_working_modes_state()`/`load_pending_approvals_state()`/
  `load_task_note_index()` families) confirm this project's own
  established "one dedicated business module + one dedicated
  `.second-brain/<concern>.json` file, pure I/O in `vault_writer`,
  business rules in the composing module" pattern — the concrete shape
  this ADR's storage decision reuses, not invents.
- `src/frontend/src/features/agents-map/AgentDetailPanel.tsx` confirms the
  Agent Detail Panel carries exactly **3** tabs today (`TABS = ['chat',
  'history', 'settings']`), not 4 — "Available actions" is a subsection
  rendered inside the `settings` tab's own body (`<h3>Available
  actions</h3>`), not a fourth tab. Correcting this inaccuracy in the
  task brief that prompted this pass, for the record, since it was
  confirmed by direct read rather than assumed.

**Decision:**

1. **Detection — a new bound tool, `record_knowledge_gap(topic: str)`,
   intercepted exactly like `request_cross_section_help` (`ADR-017`), not
   a text pattern-match.** `graph.py` gains this second interceptable
   tool, bound alongside the existing MCP-loaded tools and
   `request_cross_section_help` in `run_agent_conversation`.
   `history_entries_to_messages`'s existing single `SystemMessage`
   (`state.py`) gains one more appended instruction (mirrors
   `REQ-SB-33-US-01`'s own precedent of appending to that same message,
   not writing a second one, and does not edit that story's existing
   locked instruction text): when the model determines an honest "I don't
   know" is the right reply, it must first call `record_knowledge_gap`
   with a short topic label, then produce its honest decline as normal
   text. `_route_after_model` gains one more branch (checked after the
   existing `request_cross_section_help` check, before falling through to
   generic `execute_tools`): a call to `record_knowledge_gap` routes to a
   new node, `_record_knowledge_gap`, mirroring `_route_hub_request`'s
   shape exactly — it does **not** trust the model's own `topic` argument
   for the durable question text (models can paraphrase); instead it
   deterministically reads the turn's real originating `HumanMessage`
   (the last `HumanMessage` in `current_state["messages"]`, reliable
   because this graph replays the full, untruncated history on every
   call, per `state.py`'s own documented no-truncation-this-pass
   design) and calls `knowledge_gap_tracking.record_gap(agent_id,
   question=<that message>, topic=<model's short label>)`. It appends a
   confirming `ToolMessage` and edges back to `call_model` (identical to
   `route_hub_request -> call_model`), so the model's own final reply
   text — the actual honest "I don't know" the user sees — is produced
   normally afterward, never fabricated by this new node.
   `AgentConversationState` (`state.py`) gains one additive optional
   field, `gap_recorded: dict | None`, mirroring `hub_routing_result`'s
   own addition shape (`ADR-017`) — extends, does not reopen, `ADR-016`
   point 2's existing field-growth pattern.
2. **Storage — a new, dedicated `app/business/knowledge_gap_tracking.py`,
   composed the same way `skill_registry.py` composes `skill_tools.py`,
   never folded into `agent_activity.py`.** New tenth `.second-brain/`
   state file, `agent_knowledge_gaps.json`:
   `{"gaps": [{"id": str, "agent_id": str, "question": str, "topic": str,
   "status": "open" | "closed", "created_at": iso8601, "closed_at":
   iso8601 | null, "resolution": "human_provided" | "research" | null}]}`.
   `id` is `uuid.uuid4().hex[:12]`, the same synthetic-id precedent
   `ADR-018` point 2 already established for a workflow record with no
   natural vault-derived identity (a gap is born from a conversation
   turn, not a vault fact). New `vault_writer.py` primitives
   `load_knowledge_gaps_state()`/`save_knowledge_gaps_state()`, mirroring
   `load_skills_state()`/`save_skills_state()`'s exact pure-I/O shape —
   no default content computed in `data_access` (`ADR-003`).
   `knowledge_gap_tracking.py` exposes `list_agent_gaps(agent_id,
   status=None)`, `record_gap(agent_id, question, topic) -> dict`,
   `close_gap(gap_id, resolution) -> bool`, and `count_open_gaps(agent_id)
   -> int` (the readiness signal, Scenario 5 — a simple current count,
   per the story's own Constraints, no rate/window/threshold).
3. **Closing path (Scenario 3, human-provided answer) composes the
   already-`Done`, already-trusted Vault Filing Expert
   (`REQ-SB-35-US-01`/`ADR-021`), never a new correctness-verification
   step layered on top** (per the story's own Constraints, mirroring
   `MEMORY.md`'s standing no-staging-gate posture): a human's direct
   answer is routed through
   `vault_filing_expert.determine_placement_and_file(...)` unchanged;
   `knowledge_gap_tracking.close_gap(gap_id, resolution="human_provided")`
   is called once filing actually completes — immediately for a Tier-1
   write, or at Tier-2 approval-finalization time (the existing
   `_APPROVAL_HANDLERS` dispatch table on `pending_approvals_router.py`,
   `ADR-021`) for a Tier-2 new-top-level-area case — never before content
   is actually filed. The exact endpoint shape (a new per-agent
   sub-resource on `agents_router.py`, e.g. `POST /agents/{agent_id}/
   knowledge-gaps/{gap_id}/resolve`) is decomposer/task-level, not fixed
   here.
4. **Closing path (Scenario 4/7, directed research) composes the
   already-`Done` delegated knowledge-bootstrap chain
   (`REQ-SB-36-US-02`/`ADR-023`) as-is, never reimplemented.** A new
   composing function (e.g. `knowledge_gap_tracking.resolve_gap_via_
   research(gap_id)`) calls `knowledge_bootstrap.bootstrap_agent_
   knowledge(agent_id, subject=<gap's question>)` unchanged; a real
   `"written"`/`"pending_approval"` outcome closes the gap
   (`resolution="research"`); an honest `"no_results"` outcome (the same
   honest-empty behavior `REQ-SB-36-US-01` Scenario 3 already
   established) leaves the gap open — this is Scenario 7's regression
   guard, produced by composition, not new logic.
5. **Display surface — a fourth tab on the existing Agent Detail Panel
   (`AgentDetailPanel.tsx`), gated to Expert-type agents, not a new
   top-level nav page and not `REQ-SB-41`.** `TABS` gains `'gaps'`
   (`TAB_LABELS: {..., gaps: 'Knowledge gaps'}`), rendered conditionally —
   omitted from the array entirely for a non-Expert `agent.type`, the
   same "known, structural agent-type marker" `agent_registry.py`'s
   static `AGENTS` catalog already carries (confirmed real, not a role
   description, per the story's own Context). A new `GET /agents/
   {agent_id}/knowledge-gaps` endpoint on `agents_router.py` (mirrors the
   existing `/history`/`/skills` per-agent sub-resource convention)
   returns `{"gaps": [...], "open_count": int}`; the tab's own
   gap-closing form posts to point 3's resolve endpoint. This does not
   depend on `REQ-SB-41` (Agent Overview) landing first, and does not
   modify it — that story's own eventual surface may later choose to
   *also* project this same open-gap count, composing
   `count_open_gaps()`, but that is that story's own future decision, not
   this one's.

**Alternatives Considered:**

- **Text pattern-matching over the model's reply content** (regex/keyword
  scan for "I don't know"/"couldn't find") — rejected: fragile against
  phrasing drift (the exact wording is model-chosen, only guided by the
  system prompt, not templated), and the operator explicitly directed a
  structured signal over pattern-matching; this codebase also already has
  a real, working precedent for exactly the structured-signal shape
  needed (`ADR-017`'s intercepted tool call), so extending it costs less
  and is strictly more reliable than inventing a parallel text-matching
  mechanism the story's own Constraints named only as a fallback.
- **LLM structured output / `with_structured_output` / a JSON
  response-format mode** — rejected: confirmed by direct read of
  `_call_model` that this graph uses exactly one structured channel
  today, bound tools, and nothing else; introducing a first-of-its-kind
  structured-output wrapper for one narrow yes/no signal would be a
  larger structural change than reusing the tool-call channel the model
  is already bound to, for information a tool call already conveys
  cleanly.
- **Folding gap storage into `agent_activity.py`** — rejected: confirmed
  by direct code read that its own `_ACTIVITY_KINDS` scope is
  deliberately narrow to background-run outcomes, per that story's own
  Constraints; forcing a conversational-origin record in would widen a
  scope that `Done` story deliberately narrowed, not an additive
  extension of it.
- **Folding gap storage into `agent_communication_history.json`** (the
  existing per-agent chat/run-event transcript) — rejected: that file is
  a linear, append-only transcript (`ADR-011`) with no closeable-record
  concept (`status`/`resolved_at`); modeling "closed" would require
  either mutating a past entry (violates the append-only invariant) or
  scanning the whole transcript to compute an open-gap count on every
  request. A dedicated file with a real `status` field mirrors
  `agent_pending_approvals.json`'s own already-established "workflow
  record with a lifecycle gets its own file" precedent (`ADR-018` point
  2) instead.
- **A new, generic top-level nav page** (mirrors `SystemHealthPage.tsx`/
  `AgentActivityPage.tsx`) instead of an Agent Detail Panel tab —
  rejected: a knowledge gap is fundamentally a per-agent concept (one
  Expert agent's own domain completeness), not a cross-agent aggregation
  the way System Health/Agent Activity are; the Agent Detail Panel is
  where every other per-agent concept already lives (Settings/Chat/
  History), so a new tab is the same-shape extension, not a new
  page-level architectural decision.
- **A tab visible for every agent type**, with an empty/N-A state for
  non-Expert agents — rejected: mirrors the operator's own "for an Expert
  agent" framing and the PRD's Expert-specific readiness signal; a
  Worker/Producer agent has no "becoming expert in a domain" concept at
  all (confirmed: `REQ-SB-37-US-02`/`-US-03`'s own Worker/Producer flows
  never mention gap-closing), so omitting the tab entirely for non-Expert
  types is more honest than an always-empty section with no path to ever
  populate it.
- **Waiting for `REQ-SB-41` (Agent Overview) to exist before building any
  display surface at all** — rejected: `REQ-SB-41` is itself unspecced,
  PRD-only, with no prototype coverage (confirmed by direct inspection);
  blocking this story's own Scenario 2/5 on an unscheduled dependency
  would leave Scenario 1's honest-decline recording mechanism built with
  no way for the user to ever see it, and the operator directed real code
  now, not another open question — a minimal, additive Agent Detail Panel
  tab is buildable today and does not foreclose `REQ-SB-41` later
  choosing to *also* project the same `count_open_gaps()` signal.

**Consequences:**

- Tenth `.second-brain/` state file (`agent_knowledge_gaps.json`), new
  `app/business/knowledge_gap_tracking.py`, two new `vault_writer.py`
  primitives — no new storage technology, extends the existing flat-
  JSON-file convention exactly.
- `AgentConversationState` (`state.py`) gains one more additive optional
  field (`gap_recorded`) — extends `ADR-016`/`ADR-017`'s existing
  "grow by adding a field" pattern, reopens neither.
- `graph.py` gains one new bound tool (`record_knowledge_gap`), one new
  intercepted node (`_record_knowledge_gap`, mirrors `_route_hub_request`),
  and one more branch in `_route_after_model` — extends `ADR-015`'s "grow
  the same graph by adding nodes" convention (already used by `ADR-016`,
  `ADR-017`), reopens none of its existing nodes/edges/routing.
- `history_entries_to_messages`'s system prompt gains one more appended
  instruction — `REQ-SB-33-US-01`'s own locked ACs and existing
  instruction text are extended, not modified or reopened.
- Composes with, but does not modify, `REQ-SB-35-US-01`'s Vault Filing
  Expert (Scenario 3) and `REQ-SB-36-US-02`'s delegated
  knowledge-bootstrap chain (Scenario 4/7) — both reused as already-`Done`
  black boxes, per this project's own established composition-over-
  reimplementation precedent.
- `AgentDetailPanel.tsx` gains a fourth, conditionally-rendered tab and a
  new `agentsApiClient.ts` function; `agents_router.py` gains 1–2 new
  per-agent sub-resource endpoints (exact count/shape is decomposer/
  task-level, not fixed here).
- **A known, real edge case this ADR does not fully resolve, left for the
  decomposer/coder to handle the same way `_route_after_model`'s existing
  single-interception-at-a-time design already does:** if the model's own
  tool_calls list contained both `request_cross_section_help` and
  `record_knowledge_gap` in the same turn (a model both asking for
  cross-Section help and declining in the same breath), only one branch
  fires, per `_route_after_model`'s existing `if`/`elif`-shaped checks —
  the same limitation `ADR-017` already lives with for its own single
  interceptable tool; not a new gap this ADR introduces, and not expected
  to occur in practice given the system prompt guides each behavior
  toward a distinct situation.
- Does not depend on, and does not modify, `REQ-SB-41` (Agent Overview,
  still unspecced) — narrows a future option for it (a real
  `count_open_gaps()` it could later choose to project), the same
  "narrows, does not close" relationship `ADR-031` already established
  for that story's own still-open Purpose-data-source question.

---

## ADR-033: Agent Overview surface (`REQ-SB-41`) — Overview becomes the panel's new default-landing tab (Chat no longer auto-selected); Purpose reads the existing `settings` kv-list (`"Purpose"`, falling back to `"Domain"`), never a display-time-derived summary; all 7 shipped agents backfilled with a real, authored Purpose entry; open-knowledge-gap count composed into the Overview for Expert-type agents — extends `ADR-030`, `ADR-031`, `ADR-032`, reopens none of them

**Status:** Accepted
**Date:** 2026-08-13
**Context:** `REQ-SB-41-US-01` (`Implementation/UserStories/REQ-SB-41-US-01-
agent-overview-surface.md`) was flagged at `/spec` for two genuinely open
questions: the navigation shape (the PRD's own "before or instead of"
phrasing does not commit to one shape) and the Purpose region's data
source (no dedicated purpose/description field existed anywhere in the
data model at spec time). The operator's own breadcrumb is unambiguous
about intent, even though it does not fix the mechanism: "I need to have
an Overview... before [I] Can Chat with it" — a real complaint about
today's `AgentDetailPanel.tsx` always opening on Chat (`TABS = ['chat',
'history', 'settings']`, `activeTab` initialised and reset to `'chat'` on
every agent switch, confirmed by direct read).

Since this story was specced, two things this pass composes with, rather
than re-deriving, now exist:
- `ADR-030`/`ADR-031` (`REQ-SB-37`, Agent Creation Wizard, all three
  sub-stories now `Ready`) introduce the first real, persisted Purpose-
  shaped data: Expert agents get `{"key": "Domain", "value": ...}`,
  Producer agents get `{"key": "Purpose", "value": ...}`, both via
  `create_agent`'s existing `settings` kv-list — `ADR-031`'s own
  Consequences explicitly anticipated this story reading that precedent
  ("narrows... this story's own still-open Purpose-data-source question").
  Direct inspection of `REQ-SB-37-US-02-T01` (Worker flow, `Ready`,
  locked) confirms a Worker's `create_agent` call is constrained to
  `settings=[]` — "never fabricate a Domain-equivalent setting for a
  Worker" — a locked constraint on an already-`Ready` task this ADR must
  not contradict.
- `ADR-032` (`REQ-SB-40-US-01`, Knowledge-Gap Tracking, now `Ready`) built
  a real `count_open_gaps(agent_id) -> int` function and a `GET
  /agents/{agent_id}/knowledge-gaps` endpoint (`{"gaps": [...],
  "open_count": int}`) that did not exist when this story was specced and
  its own gap-count display was punted as "speculative UI for data that
  doesn't exist yet." `ADR-032`'s own Consequences already named this
  story as free to "later choose to also project the same
  `count_open_gaps()` signal."

Direct inspection of `app/business/agent_registry.py`'s current 7-entry
`AGENTS` dict confirms none of the 7 shipped agents (`email-capture`,
`meeting-capture`, `todo-capture`, `people-producer`, `vault-qa`,
`vault-filing-expert`, `compass-expert`) carries a Purpose/Domain-shaped
settings entry — they predate this convention entirely, by construction.

**Decision:**

1. **Navigation shape — Overview becomes the panel's new default-landing
   tab; Chat is no longer auto-selected.** `AgentDetailPanel.tsx`'s `TABS`
   gains a new `'overview'` entry, placed **first** in the array (ahead of
   `'chat'`/`'history'`/`'settings'`, and ahead of `ADR-032`'s
   conditionally-rendered `'gaps'` — final order:
   `['overview', 'chat', 'history', 'settings', 'gaps']`, `gaps` still
   omitted entirely for `agent.type !== 'expert'`, unchanged from
   `ADR-032`). `activeTab`'s initial state and its reset-on-agent-switch
   value both change from `'chat'` to `'overview'`. Chat remains fully
   reachable, one click away, with every existing behavior unmodified —
   this is a tab-order and default-selection change only, not a removal or
   restructuring of any existing tab's own content (Scenario 7's
   regression guard). This resolves the operator's own "before... Can Chat
   with it" framing directly, in the sense the PRD's Acceptance text names
   as acceptable ("before or instead of").
2. **Purpose data source — reads the existing `settings` kv-list, no new
   field, no new endpoint.** The Overview's Purpose region reads
   `GET /agents/{agent_id}`'s existing `settings: [{"key", "value"}]`
   array: look for a `"Purpose"` entry first, then a `"Domain"` entry: the
   first one found is shown as the agent's stated purpose. If neither key
   is present, the region shows an honest `"No stated purpose recorded for
   this agent."` string — never a fabricated or inferred summary. This
   settles the story's own previously-open "exact data source" question by
   directly reusing `ADR-030` point 5 / `ADR-031` point 3's existing
   mechanism, rather than adding a parallel field.
3. **Worker purpose — backfill, not display-time inference.** Two parts:
   a. **All 7 shipped agents are backfilled** with one real, authored
      `{"key": "Purpose", "value": "<one line>"}` entry, **appended** to
      each entry's existing static `settings` list in
      `agent_registry.py`'s seed dict (append-only per entry — no existing
      settings row edited, reordered, or removed). Draft text (final
      wording is the decomposer/coder's own copy-editing latitude):
      - `email-capture`: "Automatically captures incoming Outlook emails
        into the vault on an hourly schedule, classified by customer."
      - `meeting-capture`: "Automatically captures Outlook Calendar
        meetings into the vault on an hourly schedule, classified by
        customer and deduplicated across reruns."
      - `todo-capture`: "Automatically captures Outlook Tasks into the
        vault on an hourly schedule."
      - `people-producer`: "Builds and maintains a person note for every
        new email sender or meeting attendee, preserving any user-added
        content."
      - `vault-qa`: "Answers questions about the vault's contents,
        grounded in the indexed vault; reachable from this panel and
        Hermes channels."
      - `vault-filing-expert`: "Decides where new vault content belongs
        using the Second Brain filing methodology, pausing for approval
        when a new top-level area is needed."
      - `compass-expert`: "A subject-matter expert on Compass, built from
        delegated research rather than pre-loaded knowledge."
   b. **This is a static-seed-data edit only — it does not touch
      `create_agent`, `POST /agents`, or any of `REQ-SB-37-US-02-T01`'s
      already-`Ready`, already-locked constraints.** That task's "a
      Worker's `create_agent` call MUST pass `settings=[]`" governs the
      runtime wizard-creation call path only; it says nothing about this
      story's own one-time backfill of the 7 static seed entries (which
      never go through `create_agent` at all), so no ADR deviation is
      introduced and no already-`Ready` task is reopened. A Worker (or any
      agent) created **after** this pass via the wizard, with no
      Purpose/Domain entry — Worker's own wizard flow intentionally passes
      `settings=[]`, per `ADR-030`/`REQ-SB-37-US-02`, unchanged by this
      ADR — is shown decision point 2's honest "No stated purpose
      recorded" state, never a generated/derived summary computed from its
      Skills/Scope at display time (see Alternatives).
4. **Open-knowledge-gap count — composed into the Overview for Expert-type
   agents, reusing `ADR-032`'s existing endpoint, no new endpoint or
   business-layer function.** The Overview renders a one-line "Open
   knowledge gaps: N" summary (reading `GET /agents/{agent_id}/
   knowledge-gaps`'s existing `open_count` field) with a link that
   switches the panel's `activeTab` to the existing `'gaps'` tab — gated
   identically to that tab (`agent.type === 'expert'` only), never
   rendered for a Worker/Producer. This narrows `ADR-032`'s own
   explicitly-left-open "where does readiness surface" question, per its
   own Consequences' anticipation of exactly this composition. This
   region has a real, sequencing-only build dependency on
   `REQ-SB-40-US-01`'s `GET /agents/{agent_id}/knowledge-gaps` endpoint
   landing first; the rest of the Overview (Purpose, Scope, Guardrails,
   Working mode) has no such dependency.

**Alternatives Considered:**

- **Overview as a new 5th/6th tab, Chat staying the default landing
  tab** — rejected: does not resolve the operator's own explicit
  complaint ("before... Can Chat with it"); would still require an extra
  click for exactly the "context before chat" flow this story exists to
  deliver.
- **Overview as a one-time interstitial** (shown once per agent, then
  auto-advancing into Chat) — rejected: no existing precedent anywhere in
  this panel or codebase for transient/one-shot UI state (a "seen"/
  dismissal flag would be a genuinely new structural concern); harder to
  intentionally re-reach than a persistent tab; a materially bigger
  structural change than reusing the existing tab-array mechanism for no
  requirement that asked for it.
- **A brand-new, dedicated `purpose` field on the agent record** (distinct
  from `settings`) — rejected, mirrors `ADR-031`'s own already-considered-
  and-rejected alternative for the identical reason: `settings`'s kv-list
  already exists precisely for "the one descriptive fact this agent is
  about," proven by Domain/Purpose; a second, parallel field would fork
  the agent record's shape for no behavioral gain.
- **Deriving a Worker's Purpose display from its granted Skills/Scope at
  read time** (a computed "Has access to: X, scoped to: Y" sentence) —
  rejected: this project's own honesty-over-fabrication standing pattern
  (`REQ-SB-33`'s grounding guardrail; this codebase's repeated "honest
  empty state, never a fabricated one" precedent) is better served by a
  real, authored sentence (this pass's backfill, or a future edit) or an
  honest "no stated purpose" gap than by a display-time inference
  presented as if the agent stated it — a derived sentence is not
  something the agent (or its creator) actually said about itself.
- **Leaving all 7 shipped agents at an honest "no stated purpose" state
  instead of backfilling** — rejected: these are 7 real, already-
  understood, already-`Done` agents (not speculative future agents); a
  real one-line description is both cheap (7 static-dict edits, no new
  mechanism) and more honest/useful than a placeholder empty state for
  agents whose purpose is already well understood, mirroring the
  "retrofit already-shipped agents onto a new convention" pattern
  `REQ-SB-39`'s own (unbuilt, but already-decided-in-principle) Skills
  migration establishes for this codebase generally.
- **Deferring the knowledge-gap count wiring again** — rejected: the
  objection that motivated the original punt (`REQ-SB-40-US-01`'s own
  Notes: "speculative UI for data that doesn't exist yet") no longer
  applies now that `REQ-SB-40-US-01` is `Ready` with `count_open_gaps()`/
  the endpoint fully specified by `ADR-032`; composing an already-decided,
  low-cost read is materially different from building ahead of an
  unresolved foundation, which is the concern that justified the original
  punt.

**Consequences:**

- `AgentDetailPanel.tsx`'s `TABS` gains a new `'overview'` entry, first in
  the array; `activeTab`'s initial/reset value changes from `'chat'` to
  `'overview'` — every agent's panel now opens on Overview, Chat one click
  away, every other tab's own content and behavior unchanged (Scenario 7).
- `agent_registry.py`'s 7 seed entries each gain one additive
  `{"key": "Purpose", "value": ...}` settings entry — no existing entry
  touched, no call-signature change, no new dependency, no change to
  `create_agent`/`POST /agents`.
- No new endpoint, no new business module, no new `.second-brain/` state
  file — the Overview composes `GET /agents/{agent_id}`'s existing
  `settings`/`scope`/`working_mode` fields and, for Expert-type agents
  only, `GET /agents/{agent_id}/knowledge-gaps`'s existing `open_count`
  field.
- `REQ-SB-41-US-01`'s build now has one real, sequencing-only dependency
  it did not have at spec time: the gap-count region needs
  `REQ-SB-40-US-01`'s endpoint landed first. The rest of the Overview
  (Purpose, Scope, Guardrails, Working mode) has no such dependency and
  can build/ship independently — the decomposer should sequence
  tasks/ACs accordingly, mirroring this story's own existing
  Scenario-5-vs-Scenario-6 (blocked-vs-buildable-today) Scope precedent.
- The Guardrails region remains a static, non-configurable informational
  statement per the story's own Constraints, unchanged by this ADR —
  `REQ-SB-33`'s own guardrail mechanism is not touched.
- Narrows `ADR-032`'s own "does not depend on, and does not modify,
  `REQ-SB-41`" Consequences note to: composes with it, does not modify
  it — `ADR-032`'s own `'gaps'` tab, endpoint, and Expert-type gating stay
  exactly as `ADR-032` decided them.
- A future agent-type ever needing a Purpose-equivalent of its own (beyond
  Expert/Producer/backfilled-Worker) has a settled precedent to extend
  (add a `"Purpose"` settings entry) rather than an open question.

## ADR-034: File upload & summarization pipeline (`REQ-SB-28`) — new temporary non-vault blob storage under `.second-brain/uploads/`, `pypdf` for PDF text extraction, a `summarize-file` Skill wired through the already-Accepted Skills extensibility path — and image (PNG/JPG) support explicitly deferred, not built, since neither Compass nor `diagram-understanding` produces a usable text output today

**Status:** Accepted
**Date:** 2026-08-13
**Context:** `REQ-SB-28-US-01` (`Implementation/UserStories/REQ-SB-28-US-01-
file-upload-attach-and-handoff.md`) needs the user to attach a file to an
agent chat message; the agent summarizes it via Compass and hands the
summary to the Vault Filing Expert (`REQ-SB-35-US-01`, `ADR-021`, `Done`),
which files it with tags. Direct code inspection this pass confirmed
several load-bearing facts the story's own re-spec left open:

1. **No attachment/upload handling exists anywhere in the backend.**
   `app/api/email_poc_router.py` (the only prior POC-era candidate) has no
   `attach`/`upload` handling at all; no `app/api/` router accepts a file
   today.
2. **`app/data_access/compass_client.py` is confirmed text-only.** Both its
   existing functions (`classify_email`, `classify_task`) build a plain
   OpenAI-chat-completions-shaped JSON payload (`{"model", "messages":
   [{"role": "user", "content": <string prompt>}]}`); no vision/image
   parameter exists anywhere in this module, and no generic
   `summarize_*` function exists yet either.
3. **No PDF-parsing library exists in `requirements.txt`.** Extracting
   text from an uploaded `.pdf` before it can be handed to Compass as a
   plain string requires a new dependency.
4. **`diagram-understanding` (`REQ-SB-27-US-01`) is a stub, not a real
   capability.** Direct reading of `app/business/skill_tools.py` confirms
   its `@mcp_server.tool() def diagram_understanding()` unconditionally
   returns `{"available": False, "message": "This skill is not yet
   available — no real handler has been built for it."}` — its own
   docstring names the reason: "no multimodal-capable Provider exists
   yet." It does not, today, produce any text description of an image.

The story's own re-spec explicitly named this fork ("a real Compass vision
call... or routing through `REQ-SB-27`'s `diagram-understanding` Skill")
and deferred it to `/plan-tasks` rather than guessing. Both named options
were checked against the real, current implementation, not assumed:
neither produces a usable text output for an image today.

**Decision:**

1. **New temporary, non-vault blob-storage boundary, `.second-brain/
   uploads/`.** Extends the project's established flat-file `.second-brain/`
   state convention (`processed_email_ids.json`,
   `agent_communication_history.json`, `agent_skills.json`, etc.) to raw
   file bytes for the first time — one file per upload, named with a
   generated id to avoid collisions, deleted once its Compass summary has
   been produced and handed off to the Vault Filing Expert (Scenario 5) or
   on validation rejection (Scenario 7). A new `app/data_access` module
   owns this (exact name — e.g. `upload_storage.py` — left to
   `/plan-tasks`), following the existing `data_access` layering boundary
   (`ADR-003`).
2. **`pypdf` (new `requirements.txt` dependency) extracts PDF text**
   before it is handed to Compass as plain text — Compass itself never
   receives a PDF binary.
3. **A new Compass function, `summarize_content(content: str,
   source_description: str) -> dict`, added to `compass_client.py`**,
   follows the exact `classify_email`/`classify_task` shape (same payload
   construction, same `CompassError` handling) — confirmed no generic
   summarize function exists there yet.
4. **The summarization capability is registered as a new Skill
   (`summarize-file`) through the already-`Accepted` `ADR-015` Skills
   extensibility path** — a new `skill_tools.py` catalog entry + handler,
   dispatched through `skill_registry.py`'s existing
   `_SKILL_HANDLERS`/`invoke_skill`/grant mechanism, unchanged in kind.
   This is precisely the extension point `ADR-015` point 9 and the
   "Skills Repository" architecture section already anticipated — no new
   architecture for this part. This is this project's **first real
   (non-stub) Skill implementation**, composed into the chat-attachment
   flow the same way `knowledge_bootstrap.bootstrap_agent_knowledge`
   already composes `invoke_skill(..., "web-research", ...)` with
   `vault_filing_expert.determine_placement_and_file(...)` (`ADR-023`) —
   the identical "compose already-real primitives deterministically"
   shape, one concept over.
5. **Image (PNG/JPG) support is explicitly deferred, not built, by this
   story.** Neither `diagram-understanding` (a stub) nor
   `compass_client.py` (text-only) produces a usable text output for an
   image today; wiring either would either silently produce an
   empty/fabricated summary (violating Scenario 2/8's honesty constraint —
   "never a fabricated summary and never a silent no-op") or add real code
   for zero real capability. This story's real implementation is scoped to
   **text-bearing files only: `.pdf` (via `pypdf` extraction), `.txt`,
   `.md`.** The story's own Constraints text explicitly permits the
   decomposer to tune the accepted-file-types default "for a concrete
   implementation reason" — this is that reason. A follow-up story should
   build a real image-summarization capability (a confirmed Compass vision
   call, or a real `diagram-understanding` handler once a
   multimodal-capable Provider exists) before PNG/JPG can be genuinely
   honored end-to-end; at that point, this same `summarize-file`
   Skill-composition pattern (point 4) extends to route image uploads
   through that real capability with no further change to the Vault
   Filing Expert handoff (Scenario 3) needed.
6. **The new upload-bearing endpoint is additive — it does not modify
   the existing `POST /agents/{agent_id}/chat` JSON contract
   (`REQ-SB-25-US-01`, `Done`).** A new sub-resource route on the existing
   `agents_router.py` (exact path left to `/plan-tasks`, e.g. `POST
   /agents/{agent_id}/chat/attachment`, accepting `multipart/form-data`:
   `message` + `file`) mirrors the already-established
   `/history`/`/skills`/`/knowledge-gaps` per-agent sub-resource
   convention, rather than a new top-level router — keeping the plain-text
   chat path (Scenario 6) byte-for-byte unchanged.

**Alternatives Considered:**

- **Route images through `diagram-understanding` anyway, feeding its
  output into Compass** — rejected as a real capability for this pass:
  direct inspection confirms it is a stub that always returns `available:
  False`, never a text description; composing it would not satisfy
  Scenario 2's "reflects the file's actual content, not a fabricated or
  generic placeholder." Deferred to a follow-up story once a real handler
  exists (see Decision point 5).
- **A real Compass vision call** — rejected: unconfirmed anywhere in this
  codebase or `compass_client.py`'s own docstring/shape (OpenAI-chat-
  completions-shaped, text-only); building and validating a genuinely new
  multimodal capability against a live Provider is out of scope for a
  file-upload/handoff story.
- **`pdfplumber` for PDF extraction** — rejected: pulls in
  `pdfminer.six` plus table/layout-extraction machinery this story does
  not need (only plain extracted text, per the story's own framing).
- **`PyMuPDF`/`fitz`** — rejected: AGPL-licensed, and a compiled
  C-extension dependency; `pypdf` is pure-Python and MIT-licensed, a
  better fit for this project's Windows host environment (no native build
  tooling assumed, per `CLAUDE.md`'s host-environment note).
- **`unstructured`** — rejected: a large, kitchen-sink document-parsing
  package (OCR, many format handlers) far beyond this story's plain-text-
  extraction need.
- **Storing uploaded file bytes inside an existing JSON `.second-brain/`
  state file** (e.g. base64-encoded inside a JSON blob) — rejected: would
  bloat and slow every read/write of an otherwise small JSON file for an
  unrelated concern, and complicates the "delete after processing" cleanup
  (Scenario 5) versus a plain file-per-upload directory.
- **Extending the existing `POST /agents/{agent_id}/chat` endpoint's
  request body to optionally carry a file** — rejected: a shared-interface
  change to an already-`Done`, already-relied-upon JSON contract
  (`REQ-SB-25-US-01`), directly contradicting Scenario 6's "nothing about
  the existing conversational chat mechanism changes for a plain message."
  A new, additive sub-resource route is used instead.
- **A bespoke, non-Skill business function called directly from the
  attachment endpoint** (bypassing `skill_registry.py` entirely) —
  rejected: the PRD's own operator resolution states this should be
  "built as a Skill from the start"; `ADR-015`'s extensibility path
  already exists precisely for this, at zero additional architectural
  cost.

**Consequences:**

- `requirements.txt` gains `pypdf`; no other new runtime dependency.
- `.second-brain/uploads/` is a new kind of state under that root — raw
  bytes, not JSON — future work touching `.second-brain/` cleanup/backup
  tooling should account for a directory of transient binary files, not
  just flat JSON files.
- Image (PNG/JPG) upload support is a known, named gap, not a silent
  omission — a follow-up story should build a real image-summarization
  capability before that accepted-file-type default can be genuinely
  honored end-to-end. The decomposer's ACs/Constraints for
  `REQ-SB-28-US-01` should reflect the text-file-only real scope of this
  pass.
- `summarize-file` is this project's first real (non-stub) Skill
  implementation — sets the precedent that new agent capabilities land
  through the Skills registry rather than as bespoke per-agent code,
  matching the operator's own "built as a Skill from the start" intent,
  and gives `diagram-understanding` a concrete sibling to model its own
  eventual real implementation on.
- `POST /agents/{agent_id}/chat` (`REQ-SB-25-US-01`) is untouched — its
  contract, behavior, and tests remain valid with zero changes.

---

## ADR-035: Real-Time Agent Activity Pulses (`REQ-SB-42`) — Server-Sent Events push transport, plus a new, ephemeral, in-memory "agent presence" registry distinct from `REQ-SB-11`'s persisted history

**Status:** Accepted
**Date:** 2026-08-14
**Context:** `REQ-SB-42-US-01` (approved `/design` pass, `html-prototype/
agents-map.html`'s "Agent activity pulses" state-switcher option) needs the
Agents Map's static connections replaced with a live view of what is
happening right now, on both the overview and a Section drill-down: a
per-agent glow while it runs a capture/Skill or generates a chat reply, a
traveling pulse between two specific agents for a Hub-routed cross-Section
request, and a distinct steady (non-animated) highlight for an agent with
an open pending-approval record. Two genuine gaps confirmed directly, not
assumed: (1) **no real-time push transport exists anywhere in this
codebase** — every existing surface (`GET /agents`, My Day, System Health,
Vault Search, etc.) is REST/poll-shaped; direct inspection of
`src/backend/app/api/` confirms no WebSocket or SSE route exists today. The
operator explicitly chose push over a 2–5s poll interval — this is a
genuine new architectural capability, and the PRD's own context names the
transport choice specifically as an architect-level call. (2) **No
"is this agent doing something right now" concept exists.** `REQ-SB-11`'s
Agent Activity & Error Observability (`Done`) — see "Agent Activity & Error
Observability" in `architecture.md` — records completed history entries
only, written after the fact (`vault_writer.append_agent_history_entry`,
called from `run_capture_and_record_completion`'s per-step branches); there
is no in-progress marker set at the start of a real dispatch path and
cleared at completion anywhere in this codebase. The PRD's own context
frames this state as ephemeral/transient by nature, explicitly distinct
from a durable vault-writer concern.

**Decision:**

1. **Transport: Server-Sent Events (SSE), not WebSocket.** This channel is
   one-directional (server → client) only — the client never sends
   anything over it. SSE runs over plain HTTP/1.1 (`text/event-stream`),
   needs no upgrade handshake, and the browser's native `EventSource` API
   auto-reconnects on drop with zero client-side reconnect code — no new
   frontend dependency, no new backend package (hand-rolled via FastAPI's
   `StreamingResponse`), matching this project's repeated "prefer the
   simpler, already-sufficient built-in mechanism" precedent.
2. **New module, `app/business/agent_presence.py`** (business layer, no
   `data_access` — nothing here touches the vault or an external system) —
   **in-memory, module-level, no `.second-brain/` persistence**, mirroring
   `ADR-024`'s `vault_indexing.py` "in-memory, full-rebuild-and-swap, no
   disk persistence" shape one layer over:
   - `_active: dict[agent_id, {"kind": "capture" | "chat", "since": iso8601}]`
     — the two single-agent "working" triggers.
   - `_hub_routes: dict[token, {"from_agent_id", "to_agent_id", "since"}]`
     — the Hub-routed traveling-pulse case, a pair of agents, not one.
   - `_subscribers: set[asyncio.Queue]` — one queue per connected SSE
     client, in-process pub/sub (single-process app, `ADR-005`'s existing
     precedent, unchanged).
   - `start_activity(agent_id, kind) -> token`, `end_activity(agent_id,
     token)`, `start_hub_routing(from_agent_id, to_agent_id) -> token`,
     `end_hub_routing(token)` — each mutates the in-memory state, then
     calls `broadcast_snapshot()`.
   - `get_snapshot() -> dict` composes `_active`, `_hub_routes`, **and a
     fresh, live read of `pending_approval_registry`'s own already-
     persisted "list open approvals" data** (grouped by `agent_id`) into
     one payload. The pending-approval half is deliberately **not**
     duplicated into new ephemeral state — it is recomposed from the
     single existing source of truth on every snapshot, so there is never
     a second, potentially-divergent copy of "is this agent waiting on
     approval."
   - `broadcast_snapshot()` pushes `get_snapshot()` onto every subscriber
     queue.
   - **Restart-safety is intentional, not a gap:** an empty registry after
     a process restart is the exactly-correct value (nothing really is
     running the instant the process comes back up) — this is precisely
     why the PRD frames this state as ephemeral, not vault-writer-owned.
3. **Real dispatch call-site instrumentation — five named triggers:**
   a. **Capture/Skill run:** wrap `email_classification.
      run_capture_for_agent(agent_id, ...)`'s body — the one function every
      real capture-EXECUTION path already funnels through (a scheduled
      Autonomous tick via `run_capture_and_record_completion`, and a
      Supervised approval's own Approve dispatch) — in
      `start_activity(agent_id, "capture")` / `end_activity(...)` (in a
      `finally` block, so a raised exception still clears the marker).
   b. **Skill run (explicit, non-conversational):** wrap
      `skill_registry._dispatch_skill(agent_id, skill_id, args)` — the one
      ungated dispatch primitive every real skill-EXECUTION path already
      funnels through, per that function's own docstring — the same way,
      reusing the `"capture"` kind (Scenario 1 groups capture and Skill
      runs under one glow treatment). A skill invoked mid-conversation via
      the model's own tool-calling is already covered by (c), not
      double-marked here.
   c. **Chat generation:** wrap `agents_router.py::chat`'s call to
      `agent_orchestration.run_agent_conversation(...)` in
      `start_activity(agent_id, "chat")` / `end_activity(...)` — the one
      call site.
   d. **Hub-routed cross-section request:** wrap each REAL caller of
      `graph.route_cross_section_request(...)` that goes on to actually
      invoke the matched agent (today: `knowledge_bootstrap.
      bootstrap_agent_knowledge`'s two hops) with
      `start_hub_routing(from_agent_id, to_agent_id)` /
      `end_hub_routing(token)`, spanning from the match to completion of
      the downstream call — **not** inside `route_cross_section_request`
      itself, since that function only computes the match and has no
      visibility into how long the downstream call takes.
   e. **Pending-approval creation/resolution:** no new ephemeral marker
      (point 2); instead `pending_approval_registry.create_pending_approval(
      ...)` and its Approve/Decline resolution function each gain one
      additional call to `agent_presence.broadcast_snapshot()`, so a
      change is pushed immediately rather than waiting for an unrelated
      broadcast.
4. **New router `app/api/agent_presence_router.py`, `GET
   /agent-presence/stream`** — subscribes a new `asyncio.Queue`, yields an
   initial `get_snapshot()` immediately on connect (so a client opening the
   Agents Map after activity has already started sees correct state without
   waiting for the next change), then yields every subsequent broadcast as
   an SSE `data: <json>\n\n` event; unsubscribes on client disconnect.
   Registered in `app/main.py` alongside the existing routers.
5. **Frontend:** a new `src/frontend/src/features/agent-presence/client.ts`
   wrapping the browser's native `EventSource` (no new npm dependency)
   against `GET /agent-presence/stream`, feeding parsed snapshots into the
   Agents Map's existing per-agent-id node lookup so already-rendered nodes
   apply the approved prototype's own new CSS classes —
   `.agent-node--activity-glow` (Scenarios 1/2), `.agent-node--pending-
   approval` (Scenario 4), `.route-pulse-dot` plus `.affinity-line.active`
   (overview) / the drill-down's own captioned `.cluster-line` treatment
   (Scenario 3) — exactly as `html-prototype/agents-map.html`'s own
   approved `REQ-SB-42` design-pass revision already defines them. The
   existing decorative `kb-pulse-dot` is untouched (Scenario 8) by
   construction — this pass only ever adds new elements/classes alongside
   it, never edits it.

**Alternatives Considered:**

- **WebSocket** — rejected: needs a bidirectional upgrade handshake and
  hand-rolled client reconnect logic for a channel that only ever pushes
  server → client; no capability this story needs is unavailable to SSE.
- **Polling (2–5s interval)** — rejected outright by explicit operator
  direction ("real time means push, not polling").
- **An SSE helper package (e.g. `sse-starlette`)** — rejected in favor of a
  hand-rolled `StreamingResponse` generator; the actual mechanics needed (a
  `data: ...\n\n`-formatted chunk, an async generator reading a per-client
  queue) are a few lines, not enough surface to justify a new dependency —
  contrast `ADR-008`'s adoption of the `mcp` SDK's `FastMCP`, where the
  protocol itself is genuinely complex enough to warrant one.
- **Persisting "in progress" state to a new `.second-brain/
  agent_presence.json` file**, matching this codebase's usual
  per-concern-JSON-file convention — rejected: the PRD explicitly frames
  this state as ephemeral/transient, not a durable vault-writer concern;
  persisting sub-second-lived state to disk on every start/end would be
  wasted I/O for a value that is correctly "everything idle" the moment the
  process restarts anyway.
- **Deriving "capture in progress" from `REQ-SB-11`'s existing
  `agent_communication_history.json`** (e.g. "no `run_event`/`run_error`
  since the last known start") — rejected: that store only ever gains an
  entry AFTER a run completes or fails; there is no "started" marker in it
  at all today, so answering "is this running right now" would still need
  a new in-memory started-at marker plus a new history-entry kind, which is
  strictly more indirect than a purpose-built registry.

**Consequences:**

- This is the codebase's first real-time push surface — any future story
  needing server-push has a working precedent (in-process `asyncio.Queue`
  pub/sub, SSE endpoint shape) to extend rather than reinvent, though
  `agent_presence.py` itself stays scoped to activity/presence only this
  pass, not generalized into a pub/sub framework (per the story's own
  Non-Goals).
- Single-process only, consistent with `ADR-005`'s existing single-process
  precedent — if Second Brain is ever run with multiple worker processes,
  the in-memory registry and subscriber set would need to move to a shared
  mechanism (e.g. Redis pub/sub); not needed today, flagged for whoever
  revisits deployment topology.
- `end_activity`/`end_hub_routing` must be called from a `finally` block at
  each wrapped call site so a raised exception still clears the marker — a
  real correctness requirement the decomposer/coder must honor, not just
  the happy path.

---

## ADR-036: Meeting & Inbox Cockpits (`REQ-SB-43`, `REQ-SB-44`) — multi-agent shared-thread chat mechanism composed from `ADR-015`'s existing per-agent conversation graph, one shared backend/frontend module shape, a confirmed working-mode-gate bypass by construction, a `REQ-SB-28-US-01` cross-story dependency, and a new Email `recipients` capture field

**Status:** Accepted
**Date:** 2026-08-14
**Context:** `REQ-SB-43-US-01` (Meeting Cockpit) and `REQ-SB-44-US-01`
(Inbox Cockpit), both approved `/design` passes (`html-prototype/
meeting-cockpit.html`, `html-prototype/inbox-cockpit.html`), each need a
unified thread in which more than one brought-in Expert agent can respond,
each reply attributed to the Expert that produced it. This codebase's
existing chat (`REQ-SB-13`/`REQ-SB-25`, `ADR-015`'s LangGraph conversation
graph, `app/business/agent_orchestration/`) is single-agent-per-panel
today — `AgentConversationState`'s own `agent_id` field and
`run_agent_conversation(agent_id, message, history, memory)`'s signature
are both scoped to exactly one agent per call. `REQ-SB-43-US-01`'s own
operator-resolved decision (already recorded in that story's own `##
Notes`, not re-decided here) needs a concrete mechanical shape: "explicit
user-invitation into the cockpit's chat bypasses `REQ-SB-21` working-mode
gating for that Expert's actions in-session." `REQ-SB-44-US-01` shares the
identical 3-panel pattern plus two real differences (attachment review, a
draft-reply area) and has a real, currently-unmet dependency on
`REQ-SB-28-US-01` (confirmed `status: Ready`, `gate: flagged`, not `Done`
— its own tasks already exist at `Implementation/Tasks/
REQ-SB-28-US-01-T01`…`T05`) for its attachments half, plus a confirmed gap:
no existing Email note frontmatter field captures CC'd-recipient or
thread-participant data (`app/business/email_classification.py`'s own real
`write_note(...)` call carries only `subject`/`sender`/`sender_email`/
`received`/`outlook_entry_id`/`conversation_id`, confirmed by direct
reading).

**Decision:**

1. **Multi-agent shared thread — COMPOSE `ADR-015`'s existing per-agent
   `run_agent_conversation`, do not build a new orchestration layer or a
   second graph.** New sibling `.second-brain/cockpit_threads.json` (a
   genuinely new structural concept — a shared, multi-party thread,
   distinct from `agent_communication_history.json`'s per-agent,
   single-party shape), keyed by `"{subject_kind}:{subject_note_stem}"`
   (`subject_kind` = `"meeting"` or `"email"`), each holding
   `{"messages": [{"speaker": "user" | "agent", "agent_id": str | None,
   "agent_name": str | None, "text": str, "timestamp": iso8601}],
   "brought_in_agent_ids": [str, ...]}`. When the user sends a message, for
   EACH currently brought-in Expert, the composing function builds that
   Expert's own `history: list[dict]` view of the shared thread — the
   user's own turns map to `{"kind": "chat_user", ...}` unchanged; every
   OTHER Expert's own turn maps to `{"kind": "chat_user", "text":
   f"[{other_agent_name} said]: {text}", ...}` (framed as relayed context
   the user is providing, never as if this Expert once said it itself) —
   then calls the real, **unmodified** `agent_orchestration.
   run_agent_conversation(agent_id, message, history, memory)` per Expert,
   appending each real reply to the shared thread tagged with that
   Expert's own `agent_id`/`agent_name` for attribution (Scenario 6). This
   reuses `ADR-015`'s "no LangGraph checkpointer, conversation state lives
   outside the graph" precedent one layer over, at the new shared-thread
   granularity instead of per-agent history.
2. **New sub-package `app/business/cockpit/`** — mirrors
   `agent_orchestration/`'s own "first concern with enough internal
   structure to warrant one" precedent: e.g. `threads.py` (point 1's
   composition), `people.py` (point 7's chip resolution), `research.py`
   (save/discard). Generic over `subject_kind`/`subject_note_stem`, not two
   parallel modules.
3. **Shared backend/frontend module shape — SHARE, do not fork.** The
   3-panel shell, unified-thread mechanism, per-Expert attribution, scoped
   research list, and save/discard flow are behaviorally identical between
   the two stories (confirmed by direct comparison of both stories' own
   Scenario text) — one capability with a thin per-`subject_kind` adapter,
   not two independent features that happen to look similar.
   `REQ-SB-44-US-01`'s two real differences (attachment review; a
   draft-reply area) are additive layers on top of the shared shape, not a
   fork: frontend, one shared `Cockpit`-panel component (3-column grid,
   chat thread, agents-to-bring-in list, research list) accepting an
   optional attachments slot and an optional draft-reply affordance,
   mirroring `BUGFIX-02-US-01`'s already-established "one component,
   optional props, two call sites" precedent (`AgentNode.tsx`'s
   `compact`/`radiusOverride` props) rather than
   `MeetingCockpitPage.tsx`/`InboxCockpitPage.tsx` forking their own
   separate layout markup. **A draft reply needs no new backend concept at
   all** — per the operator's own resolution (ephemeral, no persistence),
   it is simply an ordinary Expert chat reply the FRONTEND chooses to
   render with a distinct "draft" affordance (e.g. a Copy action); point
   1's shared-thread mechanism needs no draft-specific field or endpoint.
4. **Working-mode-gate mechanical shape for a brought-in Expert —
   CONFIRMED, by direct code investigation, to be "naturally already true
   because the Cockpit is a new, separate invocation surface that never
   reaches the gated dispatch path at all," not a new bypass flag:**
   - An Expert's own chat reply, including any skill it tool-calls
     mid-conversation (e.g. on-the-spot research): `run_agent_conversation`
     → `_execute_tools` invokes a bound MCP tool directly via
     `tool.ainvoke(...)` — confirmed by direct reading, this **never**
     calls `skill_registry.invoke_skill` at all; only `mcp_client.
     load_agent_tools`'s access-grant filter (`has_skill_access`) applies,
     never the working-mode/`mutates`/pending-approval gate inside
     `invoke_skill`. **This is a pre-existing characteristic of `ADR-015`'s
     conversational graph, not something newly introduced for the
     Cockpit** — `architecture.md`'s own "What this pass does not decide"
     note under `ADR-015` already named this exact gap ("`REQ-SB-21`'s
     Supervised working-mode/approval interaction with a graph-based
     conversational surface... genuinely relevant, not resolved here").
     This story's operator decision closes that open item **for the
     Cockpit's own surface**, and by extension documents that it already
     describes today's ordinary single-agent chat's real behavior too —
     not a new decision invented here.
   - Saving a research result: a direct `vault_writer.write_note(...)` call
     from `app/business/cockpit/research.py`, never through
     `skill_registry`/`_invoke_action` at all — the user's own explicit
     Save click is the only trigger, mirroring `ADR-021`'s Tier-1 "writes
     immediately" path one layer over.
   - No explicit Action/Skill-trigger button exists anywhere in either
     Cockpit's own approved design — the only ways a brought-in Expert does
     anything are chat (including its own tool-calling) and the user's own
     explicit save/discard, both already covered above.
   **Consequence: no new `"cockpit"` trigger value, context flag, or gate
   modification is needed anywhere** — `skill_registry.invoke_skill`'s
   `Literal["chat", "direct", "hub_routed"]` trigger enum is unchanged.
5. **`REQ-SB-44`'s attachments half — a cross-story dependency, sequenced
   via `depends_on`, not built around.** Mirroring `REQ-SB-39-US-02`'s own
   precedent for a `Ready`-not-`Done` cross-story dependency (that story's
   own `## Notes`: "the gate-logic task... must be `depends_on`-chained...
   a decomposer-level task-sequencing discipline, not a code mechanism,
   since no real deploy boundary exists to enforce it technically"), the
   decomposer must give whichever `REQ-SB-44-US-01` task(s) implement
   attachment review a `depends_on` edge onto `REQ-SB-28-US-01`'s own
   relevant task id(s) (`T03`/`T04` — the `summarize-file` Skill and the
   chat-attachment endpoint the Cockpit's own attachment review calls,
   per point 6). The rest of `REQ-SB-44-US-01` (people chips, unified chat,
   research) carries no such dependency and may be sequenced independent of
   `REQ-SB-28-US-01`'s own remaining `ADR-034` human review.
6. **Attachment surfacing reuses `REQ-SB-28`'s own mechanism directly**
   (operator-resolved): the Inbox Cockpit's attachment-review panel calls
   the SAME `summarize-file` Skill / chat-attachment endpoint
   `REQ-SB-28-US-01` builds (`ADR-034`) against the email's own
   already-vault-saved attachment file(s) (`email_classification.py`'s
   existing `vault_writer.write_attachments` output) — not a second,
   separate read-only preview mechanism. The exact call shape (which of
   `REQ-SB-28`'s own endpoints the Cockpit calls, and how a brought-in
   Expert's summarized-attachment content threads into the shared
   conversation) is `REQ-SB-28-US-01`'s own already-decided contract
   (`ADR-034`) plus ordinary decomposer/coder wiring — no new
   architectural surface beyond "the Cockpit is one more caller of an
   already-designed mechanism."
7. **New Email-note frontmatter field, `recipients: list[{"name": str,
   "email": str}]`** — mirrors the Meeting note's own already-established
   `attendees: list[{"name","email"}]` field shape exactly (see
   `architecture.md` → "Meeting Notes & Calendar-Attendee Extraction"),
   merging To + CC recipients into one flat list (the same "no
   required/optional distinction" precedent `ADR-008` already established
   for meetings). Captured via `app/data_access/outlook_com.py`'s existing
   `_resolve_attendees(item)` mechanism, confirmed directly to be
   mechanically generic over any Outlook item exposing a `.Recipients`
   collection (a `MailItem`'s own `Recipients` collection uses the same
   numeric recipient-type values, `olTo=1`/`olCC=2`, that happen to
   coincide with the meeting-recipient-type values `_resolve_attendees`
   already filters on) — generalized into a new public function (e.g.
   `resolve_mail_recipients`, decomposer/coder-named) rather than reusing
   the private, meeting-specific name, and called from
   `email_classification.classify_recent_emails` alongside the existing
   frontmatter fields, additive only (no existing field renamed or
   removed). **Deliberately does NOT extend `people_extraction.
   ensure_person_note` to CC'd/thread participants** — only the sender
   still gets a Person note ensured at capture time, matching both
   stories' own Non-Goal ("no create-Person-note flow" from a chip)
   exactly: a CC'd/thread participant's chip is expected, honestly, to
   often render as the plain non-clickable fallback (Scenario 3) until
   some other mechanism creates their Person note. The Cockpit's own
   people-chip resolution (`app/business/cockpit/people.py`) reads a
   subject note's `attendees`/`recipients` frontmatter list directly and
   independently looks up an existing Person note by email address via a
   new **read-only** `people_extraction.find_existing_person_note(email)
   -> dict | None` (a new function — every existing `people_extraction.py`
   entry point either creates-or-finds (`ensure_person_note`) or writes a
   link; this is the first pure lookup, added because the Cockpit must
   never create a Person note as a side effect of merely opening) — never
   depending on whether the subject note's own body carries an inline
   `**Attendees:**`/`**Recipients:**` wikilink line.

**Alternatives Considered:**

- **A second, parallel LangGraph orchestrating all brought-in Experts
  inside one compiled graph** (e.g. a supervisor/router node dispatching to
  per-Expert sub-graphs) — rejected: `ADR-015`'s own graph is deliberately
  single-agent-scoped (one `agent_id` on `AgentConversationState`);
  building a second, structurally different graph purely for the Cockpit
  would duplicate `ADR-015`'s tool-loading/memory/model-resolution
  machinery for no behavior this composition-based approach doesn't
  already achieve.
- **Reusing `agent_communication_history.json` itself for the Cockpit's
  shared thread** (e.g. a synthetic multi-agent "meta-agent" id) —
  rejected: that store's own schema and every existing consumer (`GET
  /agents/{id}/history`, `AgentDetailPanel.tsx`'s Communication History
  tab, `history_entries_to_messages`) are single-agent-per-entry by
  construction; forcing a shared, multi-party thread through it would
  either corrupt an individual Expert's own real conversation history or
  require a parallel disambiguation scheme uglier than a dedicated new
  store.
- **Two independent stories, two independent modules/screens for Meeting
  vs. Inbox Cockpit** — rejected (point 3): the two stories' own Scenario
  text is near-verbatim outside the two named email-specific differences;
  forking would duplicate the unified-thread/attribution/research-list/
  save-discard mechanism for zero behavioral benefit.
- **Adding a new `"cockpit"` value to `skill_registry.invoke_skill`'s
  `trigger` `Literal`, plus a conditional bypass keyed on it** — rejected
  (point 4): investigation showed the Cockpit never reaches this function
  at all through any of its own real mechanisms, so there is nothing to
  bypass; adding an unused trigger value/branch would be speculative,
  ungrounded code.
- **A separate, Cockpit-only read-only attachment preview** (bypassing
  `REQ-SB-28` entirely) — rejected per the operator's own explicit
  resolution: keeps exactly one attachment-handling mechanism in the
  codebase, not two.
- **Extending `people_extraction.ensure_person_note` to every CC'd/thread
  participant at capture time** (matching Meeting's own attendee-
  Person-note-creation precedent) — considered, not adopted this pass:
  would make more chips resolve to real links, but silently expands
  `REQ-SB-08`'s "every real attendee" precedent to a structurally
  different, much higher-volume real-world case (a busy inbox's CC lists
  are typically far larger and noisier than a meeting's attendee list)
  with no requirement asking for it; left as a genuinely separate, future
  product decision, matching the stories' own already-flagged Non-Goal.

**Consequences:**

- `cockpit_threads.json` is this codebase's first multi-party (not
  per-agent) conversation store — any future multi-agent surface has a
  working precedent to extend or deliberately diverge from, rather than
  reusing `agent_communication_history.json`'s per-agent shape by default.
- The working-mode-gate finding (point 4) is a genuine, pre-existing gap in
  `ADR-015`'s own conversational tool-calling path (not Cockpit-specific)
  that this pass deliberately does not close for ordinary single-agent
  chat — only the Cockpit's own use of it is now an explicitly-confirmed,
  intentional design (per the operator's own resolution), not an
  oversight; closing or further restricting it for ordinary chat, if ever
  desired, is separate future work, not implied here.
- `REQ-SB-44-US-01`'s attachments-half `depends_on` edge (point 5) means
  the decomposer may need to split that story into more than one task
  group (attachments-blocked vs. not) to let the unblocked majority of the
  story proceed in parallel — an ordinary decomposer-level sequencing
  decision, not a further architectural fork.
- The new `recipients` field (point 7) has no retrofit story of its own
  this pass — existing Email notes captured before this change simply have
  no `recipients` field; the Cockpit's own people-chip resolution must
  treat a missing field as an empty list, not an error.

---

## ADR-037: Per-Agent Scheduler + shared Outlook-COM dispatch lock (`REQ-SB-47`, `REQ-SB-45`) — the shared lock's canonical home relocates to a new `app/business/agent_schedule_registry.py` (not `app/scheduling/`), scoped explicitly in-process-only; a new `"scheduled"` trigger literal composes with `ADR-029`'s gate; `capture_scheduler.py`'s hardcoded hourly blob tick coexists unchanged, sharing only the dispatch lock — extends `ADR-005`, `ADR-029`, reopens neither

**Status:** Accepted
**Date:** 2026-08-14
**Context:** `REQ-SB-47-US-01` (`Implementation/UserStories/REQ-SB-47-US-01-
per-agent-scheduler-and-shared-serialization.md`) merges two requirements
the operator confirmed building together: a per-agent Schedule tab
(configure/edit/remove/run-now/run-history, generalized across every
agent's own granted, mutating capabilities) and `REQ-SB-45`'s shared
serialization guarantee (no two Outlook-COM-touching runs ever execute
concurrently, regardless of trigger source). The story's own analyst pass
(gate: flagged) named two real, unresolved architecture forks rather than
guessing:

1. **Where the shared lock lives.** `app/scheduling/capture_scheduler.py`
   owns today's ONLY real concurrency guard (`_capture_run_lock`,
   `ADR-005` point 3) — but "run now" is a `business`-layer dispatch
   (`skill_registry.invoke_skill` → `_dispatch_skill`), and any live
   add/edit/remove of a per-agent-capability schedule (Scenario 4/5, "no
   restart required") must also mutate the live, already-running
   `AsyncIOScheduler`'s own job registry from that same `business`-layer
   CRUD call. Both needs point at a `business → scheduling` dependency
   this codebase has never had — `ADR-005` point 5 established
   `scheduling → business` as strictly one-directional, mirroring the
   constraint already binding `api/`.
2. **The shared lock's cross-process scope.** `REQ-SB-45`'s own motivating
   evidence — a real `SPRINT-030` live-verification session that
   "accidentally ran two full capture passes concurrently... after a coder
   mistakenly started two server instances" — was two independent OS
   processes racing, each with its own independent Python interpreter and
   therefore its own independent `asyncio.Lock` object. A generalized
   **in-process** lock, however completely it covers every job type within
   one process, structurally cannot prevent that specific collision; only
   a cross-process-safe mechanism (e.g. an on-disk lock file) would.

A third, operator-relayed decision (not re-derived here) narrows point 2:
**the shared lock is scoped in-process only.** It protects the real,
normal single-user operating case — multiple scheduled
agents/capabilities running within ONE live server process. "Two separate
backend processes racing against the same vault" is treated as a known,
separate, already-partially-documented operational-hygiene risk
(`MEMORY.md`/`Implementation/Learnings.md` already carry repeated "check
for/confirm what a stray already-running dev-server process is actually
serving before live verification" guidance from `SPRINT-019`/`021`/`022`/
`029`/`031`) — not something this requirement's application code must
solve via a cross-process mechanism. This mirrors `REQ-SB-45`'s own PRD
text explicitly rejecting a full queue/broker as disproportionate
infrastructure for a single-user local app ("a queue would be
disproportionate new infrastructure") — a cross-process file-lock, with
its own stale-lock/crash-recovery problem to solve, would be a step in
that same disproportionate direction for a collision class this project
already mitigates operationally (never run two dev servers against the
same vault). A second operator-relayed decision resolves the story's own
Context point 2 scope fork: **`meeting-capture`'s/`todo-capture`'s
`run_capture_now` stays the existing honest "not available" on-demand
stub** (mirroring `REQ-SB-39-US-02`'s already-established real/honest-
unavailable split) — this ADR generalizes the SCHEDULING MECHANISM only;
wiring real on-demand handlers for those two capabilities is legitimate
future work, not required by this story's own Acceptance text.

**Decision:**

1. **The shared dispatch lock's canonical home relocates to a new
   business-layer module, `app/business/agent_schedule_registry.py`, not
   `app/scheduling/`.** This directly mirrors `ADR-029` point 1's own
   resolution to an identical class of problem (the working-mode gate
   needed to live where every real caller across layers could reach it
   without violating `ADR-003`) — applied here to a concurrency primitive
   instead of a gating decision. A single module-level `asyncio.Lock()`
   (the direct generalization of `capture_scheduler._capture_run_lock`,
   renamed, relocated) is exposed via `get_shared_dispatch_lock()`, and one
   new coroutine, `dispatch_with_shared_lock(agent_id, capability_id,
   trigger: Literal["scheduled", "direct"]) -> dict`, is the ONE function
   every real trigger source for a scheduled/on-demand capability now
   passes through: a new per-agent-capability APScheduler job's own
   callback (below), and the new "Run now" endpoint. Mirrors `ADR-005`
   point 3's own "one concurrency guard spans both trigger sources" shape
   generalized one further step — not a new design, a proven one extended.
   `dispatch_with_shared_lock` skips (does not queue) if the lock is
   already held — `{"status": "skipped", "message": "skipped — another
   run is already in progress"}`, recorded to that agent's run history via
   the existing `vault_writer.append_agent_history_entry` (Scenario 7's
   own "recorded honestly" text) — else acquires the lock and calls
   `await asyncio.to_thread(skill_registry.invoke_skill, agent_id,
   capability_id, None, trigger)`, mirroring `run_capture_if_idle`'s own
   exact blocking-call-off-the-event-loop shape. `capture_scheduler.
   run_capture_if_idle` (the existing hourly blob tick) is edited
   surgically — not rewritten — to acquire `agent_schedule_registry.
   get_shared_dispatch_lock()` instead of its own private, now-removed
   `_capture_run_lock`, which is what makes the blob tick and any newly-
   configured per-agent schedule targeting one of the same three capture
   agents correctly serialize against each other (the story's own named
   coexistence Constraint) with neither mechanism's own internal logic
   rewritten.
2. **Live job-registry mutation without a new cross-layer import edge —
   `app/scheduling/capture_scheduler.py` publishes its live `AsyncIOScheduler`
   instance into `agent_schedule_registry` once, at startup; it does not
   import `agent_schedule_registry` back the other way for job mutation.**
   `agent_schedule_registry.set_live_scheduler(scheduler)` is called from
   `capture_scheduler.lifespan()` immediately after `build_scheduler()`
   (before `scheduler.start()`) — an ordinary `scheduling → business` call,
   already an allowed edge (`ADR-005` point 5). `agent_schedule_registry`'s
   own CRUD functions (`create_or_update_schedule`/`remove_schedule`) then
   call `.add_job(..., replace_existing=True)` / `.remove_job(...)`
   directly on that stored reference whenever a schedule changes — this
   works without `app/business/` ever importing `app.scheduling` at all,
   because the object being manipulated is a plain third-party
   `apscheduler.schedulers.asyncio.AsyncIOScheduler` instance (already a
   project dependency since `ADR-005`), not `app.scheduling`-owned
   application code. `capture_scheduler.build_scheduler()` itself is
   extended (not replaced) to also read `agent_schedule_registry.
   list_schedules()` at boot and register one job per persisted schedule,
   alongside the existing unchanged hardcoded `hourly_capture` job — the
   same `coalesce=True, misfire_grace_time=None, max_instances=1`
   configuration, `IntervalTrigger(minutes=...)`/`IntervalTrigger(hours=...)`
   per the schedule's own persisted unit, `id=f"schedule:{agent_id}:
   {capability_id}"`. This makes Scenario 4/5's "no restart required" true
   by construction: `POST`/`PATCH`/`DELETE` on the new schedules router
   call straight into `agent_schedule_registry`, which persists JSON AND
   mutates the one live scheduler object in the same call.
3. **New sibling `.second-brain/agent_schedules.json`** —
   `{"schedules": {"<agent_id>::<capability_id>": {"agent_id", "capability_id",
   "interval_value": int, "interval_unit": "minutes" | "hours",
   "created_at", "updated_at"}}}`, a composite `"{agent_id}::{capability_id}"`
   string key, not a uuid-keyed list. `app/data_access/vault_writer.py`
   gains the paired `load_agent_schedules_state()`/
   `save_agent_schedules_state()` primitives, pure I/O, mirroring
   `load_working_modes_state()`/`save_working_modes_state()`'s exact shape
   (no default content computed in `data_access`, per `ADR-003`).
4. **New business module, `app/business/agent_schedule_registry.py`**
   (owns all of points 1–3's mechanism in one place, deliberately — the
   lock, the live-scheduler reference, and the persisted schedule CRUD are
   one cohesive concern, not three modules): `list_schedules(agent_id=None)`,
   `create_or_update_schedule(agent_id, capability_id, interval_value,
   interval_unit) -> dict` (refuses — Scenario 9 — unless `capability_id`
   is in `skill_registry.list_agent_skills(agent_id)` AND
   `skill_tools.SKILLS[capability_id]["mutates"] is True`), `remove_schedule
   (agent_id, capability_id) -> bool`, `set_live_scheduler(scheduler)`,
   `get_shared_dispatch_lock()`, `dispatch_with_shared_lock(...)` (point 1).
5. **New `"scheduled"` trigger literal on `skill_registry.invoke_skill`**
   — `Literal["chat", "direct", "hub_routed", "scheduled"]` — for a fully-
   automatic tick with no user presently in the loop, generalizing the
   semantic the blob tick's own bespoke `trigger="background"` pending-
   approval calls already use (a real, already-shipped concept in
   `email_classification.py`, just not one `invoke_skill` itself accepted)
   into the ONE real gated dispatch path every Skill invocation already
   passes through (`ADR-029` point 1). **Manual mode gains one new branch,
   inserted alongside the existing `mode == "manual" and trigger ==
   "hub_routed"` refusal:** `mode == "manual" and trigger == "scheduled"`
   → `{"status": "skipped_manual", "reason": "This agent is in Manual mode
   — its scheduled runs stay dormant."}`, written with **zero** history
   entry — mirroring the identical, already-established
   `email_classification.py` background-gate precedent ("Manual skips
   silently — no record, no history entry at all") one layer over, now
   generalized to any scheduled capability instead of re-implemented per
   capture type (Scenario 8). `agent_schedule_registry.
   dispatch_with_shared_lock` checks for this exact `"skipped_manual"`
   status and does not call `append_agent_history_entry` for it — every
   other result status IS recorded (Scenario 6/7's "recorded honestly").
   **On-demand "run now" reuses the existing `"direct"` literal, unchanged
   — no new branch, no new literal needed for it**, per the story's own
   already-resolved reasoning: a user is presently, explicitly clicking a
   button, and Manual mode already lets `"direct"` calls through today
   (Manual blocks *automatic*/hub-routed action, not an explicit user
   request). **Supervised + `mutates is True` + `trigger == "scheduled"`**
   is not special-cased — it falls into the existing pending-approval
   branch unchanged, identical decision table, one more `trigger` value
   over (`ADR-029` point 2's own "identical decision table... one
   field-source over" precedent).
6. **The existing hourly blob tick is NOT rebuilt to route through this
   mechanism, and is not retired.** `capture_scheduler.py`'s hardcoded
   `hourly_capture` job keeps calling `run_capture_if_idle` →
   `email_classification.run_capture_and_record_completion` exactly as
   today (its own bespoke, already-`Accepted` per-capture-type
   Autonomous/Supervised/Manual gate, `ADR-018`/`ADR-020`, untouched,
   `trigger="background"` unchanged) — the ONLY edit is which lock object
   it acquires (point 1). A user MAY additionally configure a new
   per-agent-capability schedule targeting `email-capture`'s (or
   `meeting-capture`'s/`todo-capture`'s) `run_capture_now`; both mechanisms
   then run independently on their own cadence but correctly serialize
   against each other via the one shared lock — this is the concrete
   resolution to the story's own named "must not silently stop running,
   or silently double-run" Constraint.
7. **New API surface, `app/api/agent_schedules_router.py`**,
   `APIRouter(prefix="/agents/{agent_id}/schedules")`: `GET` (list),
   `POST` (create — `400` on Scenario 9's refusal), `PATCH /{capability_id}`
   (edit), `DELETE /{capability_id}` (remove), `POST
   /{capability_id}/run-now` (`await agent_schedule_registry.
   dispatch_with_shared_lock(agent_id, capability_id, trigger="direct")`).
   Registered in `app/main.py`, mirroring `pending_approvals_router.py`'s
   own "new dedicated router for a new dedicated concern" precedent. **Run
   history needs no new endpoint** — the Schedule tab reuses the existing
   `GET /agents/{agent_id}/history` (`REQ-SB-11`, unchanged), per the
   story's own already-resolved Context point 3.
8. **`skill_tools.SKILLS`/the 4 migrated mutating handlers are unchanged.**
   `meeting-capture`'s/`todo-capture`'s `run_capture_now` remains the
   honest "not yet available" stub (operator-relayed scoping decision,
   Context, above) — schedulable through the new picker (Scenario 2, any
   granted `"mutates": True` capability), but a tick or run-now against it
   always produces the same honest "not available" outcome the direct/chat
   path already produces today, recorded to run history like any other
   outcome — a disclosed, known limitation, never a fabricated success.

**Alternatives Considered:**

- **Accept the new `business → scheduling` dependency edge** (import
  `app.scheduling.capture_scheduler` directly from `skill_registry.py`/a
  new business module) — rejected: reverses `ADR-005` point 5's
  established one-directional edge for no benefit the "publish a live
  scheduler reference into business" mechanism (point 2) doesn't already
  achieve without ever inverting the import direction.
- **A new `api → scheduling` edge** (a router imports `capture_scheduler`
  directly to mutate live jobs) — rejected: introduces a novel dependency
  between two structurally-parallel trigger-source layers `ADR-005`
  explicitly modeled as siblings, neither reaching into the other;
  `app/main.py`'s existing `capture_scheduler` import is composition-root
  lifespan wiring, not a router-level precedent, and extending it to
  routers would blur that distinction for every future router.
- **A cross-process lock file under `.second-brain/`** (e.g.
  `.second-brain/capture.lock`, exclusive-create-checked before any
  COM-touching dispatch) — the only mechanism that would ALSO cover the
  literal `SPRINT-030` two-process collision; rejected for this story's
  scope per the operator's own explicit scoping decision (Context, above):
  treated as a known, separate, already-partially-documented operational-
  hygiene risk, not an application-code requirement. It would also need
  its own stale-lock/crash-recovery design (a killed process leaving an
  orphaned lock file) — real added complexity in the same disproportionate
  direction `REQ-SB-45`'s own PRD text already rejects for a full
  queue/broker. Revisit if a future requirement specifically targets
  multi-process deployment.
- **A lock keyed per-capability by "touches Outlook COM" vs. not** (two
  distinct locks) — considered, rejected in favor of one single shared
  lock spanning every scheduled/run-now dispatch, mirroring `ADR-005`
  point 3's own proven "one concurrency guard spans both trigger sources"
  shape exactly, and avoiding a new, currently-unneeded classification
  that could silently drift out of sync as future Skills are added (a
  future non-COM Skill misclassified into the "doesn't need locking"
  bucket would be a silent regression risk a single shared lock cannot
  have, at the cost of at most one unnecessary skip between two genuinely
  unrelated capabilities colliding at the same instant — an acceptable,
  honest trade-off for a single-user local app).
- **A uuid-keyed schedule list** (mirroring `pending_approval_registry`'s
  record shape) instead of a composite `"{agent_id}::{capability_id}"`
  dict key — rejected: the story's own Scenario 1/4/5 model schedule
  identity as exactly one active schedule per (agent, capability) pair; a
  uuid-list shape would need its own extra uniqueness-enforcement code to
  prevent two schedules silently targeting the same pair, which the
  composite-key dict shape prevents structurally, for free.
- **Rebuild the blob tick to route through this new generalized mechanism,
  retiring the hardcoded `hourly_capture` job** — rejected as out of this
  story's own scope; its own Constraint explicitly forbids silently
  changing the existing blob tick's behavior as a side effect of this
  generalization. The two mechanisms coexist (point 6), sharing only the
  dispatch lock.
- **Building real, non-stub `run_capture_now` handlers for
  `meeting-capture`/`todo-capture` as part of this same pass** — rejected
  per the operator-relayed scoping decision (Context, above); would mean
  splitting or duplicating logic out of the blob tick, materially larger
  scope than generalizing the scheduling mechanism, and is legitimate,
  separately-scoped future work.

**Consequences:**

- `app/scheduling/capture_scheduler.py` loses its own private
  `_capture_run_lock`; the shared lock's canonical home is now
  `app/business/agent_schedule_registry.py` — a deliberate, narrowly-scoped
  exception to `ADR-005` point 5's "scheduling owns the concurrency guard"
  framing, not a general erosion of the `scheduling`/`business` boundary.
  `ADR-005` remains Accepted; this ADR records the one point it amends.
- `app/business/` gains its first-ever dependency on a live
  `AsyncIOScheduler` INSTANCE (not the `app.scheduling` package) — a
  third-party-library-typed reference published once at startup. A
  deliberate, narrow seam, not a general precedent for `business` reaching
  into arbitrary runtime state owned by another layer.
- The existing hourly blob tick and any newly-configured per-agent
  schedule targeting one of the same three capture agents now correctly
  serialize against each other — closes the story's own named coexistence
  gap — without either mechanism's own internal logic being rewritten.
- The cross-process collision `REQ-SB-45`'s own motivating evidence
  (`SPRINT-030`) demonstrated remains **not** solved by this mechanism, by
  deliberate, disclosed scope decision, recorded here and in
  `architecture.md` so it is not silently forgotten — a future requirement
  must explicitly ask for cross-process safety before this is revisited.
- `meeting-capture`'s/`todo-capture`'s `run_capture_now` stays an honest,
  on-demand "not available" stub even when scheduled through the new
  generalized mechanism — a known, disclosed limitation, not a regression,
  never silently masked by the new Schedule tab (its run history shows the
  same honest outcome any other honest failure/unavailability produces).
- A future Skill added with `"mutates": True` automatically becomes
  schedulable through the same grant+mutates picker validation
  (`create_or_update_schedule`), with zero new registry code — mirrors
  this codebase's established "generic over the catalog, not per-id"
  precedent (`ADR-028`/`ADR-029`).
- Net-new frontend surface: `AgentDetailPanel.tsx` gains a 5th tab,
  "Schedule" (alongside `overview`/`chat`/`history`/`settings`/`gaps`),
  with no approved prototype coverage today (the story's own Notes) — the
  decomposer/coder should treat its concrete layout as still needing a
  `/design` pass or explicit operator sign-off to skip one, independent of
  this ADR's own backend-mechanism scope.

---

## ADR-038: Cockpit Person-Directed Instruction (`REQ-SB-49-US-02`) — a gate-preserving bound-tool interception (`propose_person_note_update`, mirrors `ADR-032`'s `record_knowledge_gap` shape) reaches `skill_registry.invoke_skill`'s real gate through a NEW `"cockpit_mention"` trigger literal, deliberately carved out of `ADR-036`'s own Cockpit-bypasses-gate precedent; "propose" is read as a genuine, mode-independent explicit-confirm deviation for Manual/Autonomous dispatch only — extends `ADR-029`, `ADR-032`, `ADR-036`, `ADR-037`, reopens none of them

**Status:** Accepted
**Date:** 2026-08-14
**Context:** `REQ-SB-49-US-02` (`Implementation/UserStories/REQ-SB-49-US-02-
cockpit-person-mention-proposed-note-edit.md`) needs a Cockpit-brought-in
Expert's own `@PersonName`-directed instruction to propose a real,
never-silently-applied edit to an existing Person note, "subject to that
agent's own working-mode gate" (the PRD's own Acceptance text). The
analyst's own pass (`gate: flagged`) resolved the mutation itself to a new
`mutates: True` Skill, `propose_person_note_update`, but explicitly left
open the one real architectural fork: `ADR-036` (Meeting & Inbox Cockpits,
`Accepted`, `Done`) already found, by direct code inspection, that every
real Cockpit mechanism today — an Expert's own chat/tool-calling reply,
included — **never reaches `skill_registry.invoke_skill`'s gated dispatch
path at all**; "bringing an Expert in on purpose is itself the approval"
was that story's own operator-resolved reading. Extending that precedent to
this new capability would mean an LLM's own interpretation of a person's
name and an editing instruction could mutate a real, existing Person note
with zero working-mode gate involvement — directly contradicting this
story's own PRD Acceptance text and its own unqualified Constraint ("no
code path writes to a Person note as a direct, unconfirmed side effect of a
chat instruction"). The operator's own relayed resolution for this pass is
explicit: build a NEW, gate-preserving call path for this one capability
specifically, mirroring `ADR-032`'s `record_knowledge_gap` bound-tool-
interception shape — do not extend `ADR-036`'s bypass to it.

Direct code inspection, not assumption, grounds every point below:
- `app/business/agent_orchestration/graph.py` already has a real, twice-
  proven precedent for exactly this shape: `request_cross_section_help`
  (`ADR-017`) and `record_knowledge_gap` (`ADR-032`) are both bound
  directly to the model (never registered on the shared MCP server), their
  own function bodies are never actually invoked, and `_route_after_model`
  intercepts any call to either one **before** the generic `execute_tools`
  node, routing to a dedicated node that performs the real work
  deterministically in Python before looping back to `call_model`.
- `app/business/cockpit/research.py::trigger_research` is a real, live,
  already-shipped Cockpit code path that **does** call
  `skill_registry.invoke_skill(research_expert_id, "web-research", ...,
  trigger="direct")` directly — confirmed by direct reading. This refines,
  not contradicts, `ADR-036` point 4's own finding: what never reaches
  `invoke_skill` is specifically the **model's own bound-tool-calling loop**
  (`_execute_tools`, for tools loaded via `mcp_client.load_agent_tools`) —
  a Cockpit-side function that explicitly chooses to call `invoke_skill` on
  an agent's behalf already does reach it today, trivially satisfying the
  gate only because `web-research` is `mutates: False`. This story is the
  first time a Cockpit-originated call reaches the gate for a **mutating**
  Skill, which is what actually makes the gate consequential rather than a
  structural no-op.
- `app/business/skill_registry.py::invoke_skill`'s two-axis gate
  (`ADR-029` point 2) refuses only on `mode == "manual" and trigger ==
  "hub_routed"`; every other `(mode, trigger)` combination either falls
  through to dispatch or (Supervised + `mutates`) creates a Pending
  Approval, **regardless of the specific `trigger` value** — confirmed by
  direct reading of the gate's own two `if` branches. Adding a new
  `trigger` literal therefore requires zero new branches in the gate
  itself, only a `Literal[...]` type extension — the exact same "new
  literal, zero new gate branches" shape `ADR-037` point 8's own
  `"scheduled"` trigger already established as this codebase's own
  precedent for a genuinely new dispatch SOURCE that composes with, rather
  than special-cases, the existing gate.
- `app/api/pending_approvals_router.py`'s Approve endpoint already calls
  `skill_registry._dispatch_skill(record["agent_id"], record["action_id"],
  record["payload"])` directly (never `invoke_skill`, `ADR-029` point 4) —
  the approval itself is the authorization. `_dispatch_skill`'s own
  existing signature-introspection auto-injection (`if "agent_id" in
  inspect.signature(handler).parameters: call_args["agent_id"] = agent_id`)
  is a real, already-proven seam for a handler to opt into caller-supplied
  context with zero effect on any other handler's call — the exact
  mechanism this ADR reuses (point 4, below) to let one Skill's own handler
  distinguish "dispatched via a just-approved Pending Approval" from
  "dispatched directly," without adding gate-shape-specific logic to the
  generic dispatch primitive itself.
- `people_extraction.find_existing_person_note(email)` (`ADR-036` point 7)
  is this codebase's first pure, read-only, never-create Person-note
  lookup — keyed by email, not name. Resolving `@AhmedMoussa` needs a
  name-keyed sibling of the same read-only shape (exact function naming
  left to the decomposer/coder, per this story's own explicit non-
  assertion of NLU-level parsing detail).

**Decision:**

1. **New bound tool, `propose_person_note_update(person_name: str,
   instruction: str)`, intercepted exactly like `record_knowledge_gap`
   (`ADR-032` point 1) — never registered on the shared MCP server, never
   reachable via the generic `execute_tools` node.** `graph.py` gains this
   third interceptable tool. `_route_after_model` gains one more branch,
   checked alongside the existing two, before the generic
   `execute_tools` fallthrough: a call to `propose_person_note_update`
   routes to a new node, `_propose_person_note_update`.
2. **Conditional binding — the ONE deliberate structural difference from
   `request_cross_section_help`/`record_knowledge_gap`'s own "bind to
   every agent unconditionally" shape.** Those two are generic, ungated
   graph-level capabilities with no per-agent grant concept at all;
   `propose_person_note_update` is a real, declared `skill_tools.SKILLS`
   entry (point 3, below) with a real per-agent access-grant concept
   (`skill_registry.has_skill_access`) — binding it to every agent's model
   regardless of grant would expose a tool schema most agents can never
   meaningfully use and that the gate would just refuse. `run_agent_
   conversation` binds it only when `skill_registry.has_skill_access(
   agent_id, "propose_person_note_update")` is true — mirrors `mcp_client.
   load_agent_tools`'s own existing access-grant filtering for MCP-loaded
   tools, applied here to a graph-bound tool for the first time. The
   system-prompt instruction telling a granted agent when to call this
   tool (mirrors `record_knowledge_gap`'s own appended-instruction
   precedent) is threaded through the same conditional — exact signature
   plumbing (how `history_entries_to_messages`/`run_agent_conversation`
   learn the per-agent grant) is decomposer/coder latitude, not fixed here.
3. **New `skill_tools.SKILLS` entry, `propose_person_note_update`,
   `"mutates": True`, granted to `people-producer` via one new
   `_MIGRATION_GRANT_SEED` entry (`skill_registry.py`) — mirrors `ADR-029`
   point 7's exact per-id, per-agent-list seeding shape, one more row, not
   a new mechanism.** Registered in `skill_registry._SKILL_HANDLERS`
   alongside the existing 11 entries.
4. **The node resolves the real Person note READ-ONLY first, never through
   the gate — only a genuine match proceeds to a gated Skill call.**
   `_propose_person_note_update` calls a new, read-only, name-keyed sibling
   of `people_extraction.find_existing_person_note` (point 5 of the
   Context, above) directly — no gate involvement, mirrors `_record_
   knowledge_gap`'s own direct `knowledge_gap_tracking.record_gap` call
   (a read/write that is not itself a vault mutation subject to the
   working-mode gate). **No match:** appends an honest "no matching Person
   note found" `ToolMessage`, loops back to `call_model` — no
   `invoke_skill` call at all (Scenario 4; never fabricates a match, never
   creates a note, never proposes an edit for an unresolved mention). **A
   match:** calls `skill_registry.invoke_skill(agent_id, "propose_person_
   note_update", args={"note_path": ..., "person_name": ..., "instruction":
   ...}, trigger="cockpit_mention")` — the FULL existing two-axis gate
   applies exactly as it would for any other mutating Skill (Scenario 3),
   by construction, since `invoke_skill` is the one function this ADR
   routes through, never bypassed. Whether a bare `@mention` with no real
   editing instruction ever reaches this tool call at all (Scenario 5) is
   a system-prompt-instruction concern ("only call this tool once you have
   identified a real, specific change to propose") — the node itself does
   not need its own no-instruction detection.
5. **New trigger literal, `"cockpit_mention"` — NOT a reuse of `"chat"`,
   `"direct"`, `"hub_routed"`, or `ADR-037`'s `"scheduled"`.** Reasoned
   explicitly, not defaulted: `"direct"` already covers every existing
   explicit, deterministic, non-conversational dispatch (an explicit UI
   button/endpoint call with server-fixed `skill_id`/`args` — `skills_
   router.py`'s direct-invoke endpoint, `agents_router.py`'s `trigger_
   action`, `vault_filing_expert.py`'s Tier-2 flow, `research.py`'s own
   `trigger_research`). This call site is categorically different: it is
   the FIRST dispatch in this codebase whose `skill_id`'s own `args`
   (which person, what edit) are determined by an **LLM's own
   interpretation of free natural-language text**, not a deterministic
   caller. `"chat"` is reserved for `agents_router.py`'s existing single-
   agent keyword-matched action-word funnel (`chat()`'s own `matched_
   capability_id` resolution) — a different, already-real mechanism this
   story's call site does not reuse or extend. `"hub_routed"` would
   incorrectly refuse this capability in Manual mode (`invoke_skill`'s own
   `mode == "manual" and trigger == "hub_routed"` refusal), directly
   contradicting Scenario 3's own requirement that Manual mode dispatch
   this exactly like any other mutating action for that mode — this
   capability is never one agent acting on ANOTHER agent's request, it is
   always the user's own direct instruction. A new, honestly-named literal
   gives this codebase's own audit trail (Pending Approval descriptions,
   agent history entries, any future reporting) a real, distinguishable
   record of "an LLM's own interpretation of an `@mention` triggered this
   mutating dispatch," mirroring `ADR-037` point 8's own precedent of
   minting `"scheduled"` for a new dispatch SOURCE rather than folding it
   into an existing literal whose audit meaning it would dilute. Requires
   zero new gate branches (Context, above) — `invoke_skill`'s `Literal[
   "chat", "direct", "hub_routed", "scheduled"]` gains a fifth value,
   `"cockpit_mention"`; the refusal branch's `trigger == "hub_routed"`
   check and the Supervised+`mutates` branch's trigger-agnostic check both
   already compose correctly with it, unmodified.
6. **"Propose" is read as a genuine, deliberate DEVIATION from this Skill's
   own standard post-gate dispatch behavior — but ONLY for Manual/
   Autonomous, never for Supervised.** This story's own Constraints section
   is unqualified by working mode: "no code path writes to a Person note
   as a direct, UNCONFIRMED side effect of a chat instruction." Examined
   per mode:
   - **Supervised (Scenario 2):** the gate's own existing Pending-Approval
     detour (`ADR-029` point 2) already IS an explicit, human-in-the-loop
     confirm step — the user's own "Approve" click is the confirmation.
     No further step is needed or introduced; approving directly performs
     the write, matching Scenario 2's own literal wording exactly.
   - **Manual/Autonomous (Scenario 3):** `invoke_skill`'s gate, unmodified,
     falls straight through to `_dispatch_skill` with **zero human click
     of any kind** — this is precisely what Manual/Autonomous mode means
     everywhere else in this codebase (e.g. `build_knowledge` writes
     immediately in Autonomous mode). For every OTHER existing mutating
     Skill, that is correct and desired. For THIS Skill specifically, an
     immediate, unconfirmed write here would be exactly the "direct,
     unconfirmed side effect" this story's own Constraint forbids
     unconditionally — this is what makes this capability, per the PRD's
     own word choice ("proposing... never silently applying"), genuinely
     different from every other mutating Skill this codebase has, and why
     a carve-out inside the Skill's OWN handler (never inside the shared
     gate) is warranted.
   - **Reconciling with Scenario 3's own "exactly as any other mutating
     action already is for that mode, never a special-cased, ungated
     bypass" wording:** that wording is about the GATE's own axis decision
     (Supervised → pending, Manual/Autonomous → dispatch) — unmodified,
     zero special-casing, by this ADR. What a Skill's own handler does
     with its own dispatch is already normal per-Skill variation in this
     codebase (`build_knowledge`'s own multi-branch outcome logic,
     `web_research`'s own Provider-dependent honest-unavailable branch) —
     this ADR's deviation lives entirely inside `propose_person_note_
     update`'s own handler body, never inside the shared gate axis logic
     Scenario 3 is actually describing.
7. **Mechanism: `_dispatch_skill` gains one new, opt-in keyword,
   `already_approved: bool = False`, auto-injected via the SAME signature-
   introspection seam that already injects `agent_id` (Context, above) —
   a no-op for every one of the other 11 existing handlers, none of which
   declare this parameter.** `pending_approvals_router.py`'s Approve
   branch for a migrated Skill (`ADR-029` point 4) passes `already_
   approved=True` explicitly on this ONE call site; every other dispatch
   path (the gate's own Manual/Autonomous fallthrough) leaves it at its
   default `False`. `propose_person_note_update`'s own handler:
   - `already_approved=True` (reached only via a just-approved Supervised
     Pending Approval): composes the edit and writes it directly via
     `vault_writer` (exact write shape — a new body line vs. a structured
     frontmatter change — is this story's own already-disclosed non-
     assertion, decomposer/coder latitude), returns `{"status": "written",
     ...}`.
   - `already_approved=False` (Manual/Autonomous direct dispatch, or any
     future non-approval-derived call): does NOT write. Composes the
     proposed edit and records it as an explicitly confirmable/discardable
     in-thread proposal — a new, small `app/business/cockpit/person_note_
     proposals.py` (mirrors `cockpit/research.py`'s own scoped-list-plus-
     direct-`vault_writer`-on-explicit-action shape, `ADR-036` point 4
     bullet 2's precedent, reused one layer over for a new proposal kind;
     stored as part of the owning thread's own `cockpit_threads.json`
     record rather than a new top-level `.second-brain/` file, since a
     pending, not-yet-confirmed proposal is ephemeral, thread-scoped state
     with no standing audit requirement once discarded) — returns
     `{"status": "proposed", "proposal_id": ..., ...}`. A new, small
     confirm/discard pair of endpoints (mirrors the existing research
     save/discard shape) is the ONLY place `vault_writer` is called for
     this path — the user's own explicit click, never a side effect of the
     chat reply itself, exactly `ADR-036` point 4's own "the user's own
     explicit Save click is the only trigger" precedent, reused for this
     new proposal kind. Exact endpoint routes/payload field names are
     decomposer/coder latitude, not fixed here.
   The graph node translates `invoke_skill`'s own returned `status`
   ("refused" / "pending" / "proposed" / "written") into the `ToolMessage`
   content the model's own final reply is composed from afterward — never
   a fabricated description of an outcome that did not actually occur.

**Alternatives Considered:**

- **Extend `ADR-036`'s own "bringing an Expert in is itself the approval"
  precedent to this capability too** (i.e., no new call path — an ordinary
  MCP-registered tool the model calls through the existing `_execute_
  tools` loop) — rejected, per the operator's own explicit resolution: this
  is the Cockpit's first real, autonomous, LLM-initiated vault-MUTATION
  candidate, categorically different from every other real Cockpit action
  today (either read-only, or already carrying its own explicit-consent
  flow — the research save/discard pattern). Every other mutating action
  in this codebase already gets the working-mode gate; carving this one out
  would be a genuine regression in protection for exactly the riskiest new
  capability this pass adds, directly contradicting the PRD's own
  Acceptance text.
- **Reuse `trigger="direct"` for this call site** (mirrors `research.py`'s
  own `trigger_research` call) — considered, not adopted: `"direct"`'s
  existing real call sites are all deterministic, explicit-UI-triggered
  dispatches with server-fixed `args`; this is the first LLM-interpreted
  dispatch, a genuinely distinct SOURCE worth its own honestly-named
  literal for future audit/reporting, mirroring `ADR-037`'s own reasoning
  for minting `"scheduled"` rather than folding a new dispatch source into
  an existing bucket.
- **Reuse `trigger="hub_routed"`** — rejected: would incorrectly refuse in
  Manual mode (`invoke_skill`'s own `mode == "manual" and trigger ==
  "hub_routed"` branch), contradicting Scenario 3's own explicit
  requirement that Manual mode dispatch this exactly like any other
  mutating action; this capability is never one agent acting on another
  agent's behalf.
- **Extending `vault_write_tools.propose_vault_write`'s existing MCP-tool
  shape** (`REQ-SB-04-US-01`, already named and set aside by the story's
  own Context) — rejected, re-confirmed: that tool always creates a
  Pending Approval unconditionally, bypassing `working_mode_registry`
  entirely regardless of mode, which does not match the PRD's own mode-
  DEPENDENT "subject to that agent's own working-mode gate" acceptance
  text.
- **Always require the explicit in-thread confirm step, even for
  Supervised** (i.e., approving a Pending Approval would only ever produce
  a further-confirmable proposal, never a direct write) — considered,
  rejected: contradicts Scenario 2's own literal wording ("approves it →
  the real Person note is updated... and not before"); the Supervised
  Pending-Approval detour is already, structurally, the one human-
  confirmation click this capability needs for that mode — stacking a
  second confirm step on top would be redundant friction the story's own
  Scenario text does not ask for.
- **Never require an explicit in-thread confirm step for Manual/
  Autonomous** (dispatch always writes immediately, matching every other
  mutating Skill's own default behavior) — considered, rejected: directly
  contradicts this story's own unqualified Constraint ("no code path
  writes... as a direct, unconfirmed side effect of a chat instruction")
  for the two modes whose gate has no human click at all in its own
  dispatch path; also the most defensible reading of the PRD's own word
  choice "proposing (never silently applying)," which the story's
  Constraints section does not scope to Supervised mode only.
- **A wholly new, second gate mechanism outside `skill_registry`/
  `working_mode_registry` entirely** (a bespoke approval flow invented
  only for this capability) — rejected per Scenario 3's own explicit
  "never a special-cased, ungated bypass invented only for this
  capability" wording, and per this project's own standing precedent of
  composing with `REQ-SB-39-US-02`'s already-Done, already-generalized gate
  rather than building a parallel one.

**Consequences:**

- `skill_registry.invoke_skill`'s `trigger` `Literal` grows a fifth value,
  `"cockpit_mention"` — every existing real call site (`skills_router.py`,
  `agents_router.py`, `knowledge_bootstrap.py`, `research.py`) is
  unaffected; the gate's own two `if` branches compose correctly with it
  with zero new code, mirroring `ADR-037`'s own identical "new literal,
  zero new gate branches" consequence.
- `_dispatch_skill` gains one new opt-in, signature-introspected keyword
  (`already_approved`) — a real, reusable seam for any FUTURE Skill that
  similarly needs to distinguish a just-approved dispatch from a fresh one,
  not a one-off hack; every one of the 11 existing handlers is unaffected,
  confirmed by direct reading (none declare this parameter).
- `graph.py`'s conditional-tool-binding for `propose_person_note_update`
  is this codebase's first graph-bound (non-MCP) tool that is NOT
  unconditionally available to every agent — a real, deliberate precedent
  for any future capability that needs both graph-level interception AND a
  genuine per-agent access-grant concept; `request_cross_section_help`/
  `record_knowledge_gap` remain unconditionally bound, unchanged.
- `app/business/cockpit/person_note_proposals.py` is a new, small sibling
  concern inside `cockpit/`, alongside `threads.py`/`people.py`/
  `research.py` — extends `ADR-036` point 2's own "generic sub-package,
  grows by adding files" pattern, does not reopen it.
- `ADR-036`'s own "the Cockpit never reaches `invoke_skill`'s gated
  dispatch path" finding is now correctly scoped to "the model's own
  bound-tool-calling loop via `_execute_tools`, for MCP-loaded tools" — it
  was already imprecise (`research.py`'s own `trigger_research` already
  reached `invoke_skill` for a non-mutating Skill); this ADR is the first
  Cockpit-originated call to reach it for a MUTATING Skill, which is the
  first time that finding's own scope actually matters. `ADR-036` is not
  rewritten (Forbidden — a change of mind is a new ADR, never a rewrite of
  an Accepted one) — this point is recorded here as the refining
  consequence, not as an edit to `ADR-036`'s own text.
- Any FUTURE Cockpit capability that proposes a real vault mutation from an
  LLM's own interpretation of chat text now has a proven, reusable shape to
  follow (bound-tool interception → read-only resolution → gated
  `invoke_skill` call with a source-honest trigger literal → per-handler
  propose-vs-write branching keyed on `already_approved`) rather than
  needing its own from-scratch architecture pass.

---

## ADR-039: Agent Creation Wizard Redesign (`REQ-SB-46`) — popup modal + step-bar container (new tokens-based CSS, not `.side-panel-*` reuse), a shared `SkillsTree.tsx` component extracted from `REQ-SB-48-US-01-T02` and consumed by both the wizard and the Agent Detail Panel, Trigger metadata composition reconfirmed unchanged, Background-Agent toggle fold-in declined — extends `ADR-030`/`ADR-031` (Agent Creation), composes with `REQ-SB-48-US-01`'s own in-flight design, reopens neither

**Status:** Accepted
**Date:** 2026-08-14
**Context:** `REQ-SB-46-US-01` (`Implementation/UserStories/REQ-SB-46-US-01-
agent-creation-wizard-popup-modal-redesign.md`) redesigns the already-real,
already-shipped Agent Creation Wizard mechanism (`ADR-030`/`ADR-031`,
`CreateAgentWizard.tsx`, `Done`) into a popup modal reached from a new
bottom-right FAB on the Agents Map, with a visual 4-step progress bar and a
regrouped field-to-step mapping — a pure frontend composition/relocation
exercise plus one small additive `Trigger` metadata field. The story's own
analyst pass flagged `net-new-design-needed` (no popup-modal/step-bar/FAB
pattern anywhere in `html-prototype/`) and a disclosed field-to-step mapping
assumption. The operator resolved both directly, relayed to this pass, not
re-derived here: (1) skip a formal `/design` pass, matching this session's
`REQ-SB-47`/`REQ-SB-48` precedent, and direct the coder to build a
genuinely polished step-bar by drawing on this codebase's own existing
visual language (the side panel's slide-in overlay styling, `agents-map.css`'s
color/spacing tokens) rather than inventing a new design system; (2) confirm
the analyst's field-to-step mapping as final, not re-litigated here.

This story lands last in its batch, after three siblings that are now all
`Ready` with real, decomposed designs — `REQ-SB-47-US-01` (Scheduler,
`ADR-037`), `REQ-SB-48-US-01` (Skills-grouped-by-Tool collapsible tree, no
new ADR, tasks `T01`/`T02` `Ready`), `REQ-SB-51-US-01` (Background Agents,
no new ADR, tasks `T01`-`T06` `Ready`). This creates a real composition
opportunity this architecture pass must resolve concretely, not leave to
the coder's own judgement:

1. **Step 3 (Tools/Skills) and `REQ-SB-48`'s own Capabilities tree.**
   `REQ-SB-48-US-01-T02` is about to replace `AgentDetailPanel.tsx`'s flat
   Skills `kv-list` with a collapsible, icon-bearing, Tool-grouped tree
   (reading a new `"tool"` field `T01` adds to `skill_tools.SKILLS`/
   `SkillSummary`). `REQ-SB-46`'s own Step 3 needs the SAME grouped-tree
   presentation for a genuinely different interaction (multi-select
   pre-creation, no immediate grant/revoke call — today's Worker step's
   own flat checkbox list, `CreateAgentWizard.tsx` lines 252-265) rather
   than a separate, divergent tree implementation.
2. **Step 4's Trigger choice and `REQ-SB-47`'s now-real Schedule tab.**
   Confirming whether the story's own already-resolved "records intent
   only, does not build `REQ-SB-47`'s own configuration UI inline" scoping
   still holds now that `REQ-SB-47`'s real schedule-CRUD mechanism exists
   (`agent_schedule_registry.py`, `agent_schedules_router.py`, both
   `Ready`, not yet `Done`/built).
3. **`REQ-SB-51`'s new `is_background_agent` flag and wizard-time
   creation.** `REQ-SB-51-US-01`'s own Non-Goals explicitly deferred a
   wizard-time toggle to "whichever wizard shape is current once
   `REQ-SB-46` lands" — that condition is now true, so this pass must
   decide concretely whether to fold it in.

**Decision:**

1. **New popup-modal container, `CreateAgentWizardModal.tsx`** (renamed/
   restructured from `CreateAgentWizard.tsx`, mounted from
   `AgentsMapPage.tsx` behind a new bottom-right `.map-fab` button,
   replacing the Settings-page entry point per Scenario 1) — centered
   overlay + panel + a new `.wizard-step-bar` (1-2-3-4, current-step
   highlighted). New CSS classes (`.wizard-modal-overlay`, `.wizard-modal`,
   `.wizard-step-bar`, `.wizard-step`, `.map-fab`), added to
   `agents-map.css`, built entirely from this codebase's own existing
   design tokens (`--color-surface`, `--color-accent`, `--color-border`,
   `--space-*`, `--radius-*`, the same `color-mix(...)` glow/tint idiom
   `.hub-node`/`.map-overflow-marker` already use) — **NOT** a literal
   reuse of `.side-panel-overlay`/`.side-panel`'s own class names or
   edge-anchored slide-in behavior, since Scenario 2 explicitly requires
   the new modal be "distinct from the existing agent-detail side panel's
   slide-in overlay." The FAB reuses `.map-overflow-marker`'s own circular
   dashed-border/tinted-glow badge treatment (bottom-right `position: fixed`
   instead of map-relative absolute placement) rather than inventing a new
   button visual language. The four steps' own per-type field regrouping
   (Description→Expert's Domain; Instructions/Guardrails→Working mode, all
   types; output-fields→Producer's Purpose+outputSkill; Tools/Skills→Step
   3) follows the story's own already-confirmed `## Context` mapping
   verbatim — the existing per-type submit sequences (`handleSubmit`/
   `handleWorkerSubmit`/`handleProducerSubmit`, their exact `createAgent` →
   optional `grantAgentSkill` call(s) → `updateAgentAssignment` PATCH
   ordering) are preserved unchanged, only regrouped into the new 4-step
   structure and gated behind per-step "Next" validation instead of one
   single-step form, per the story's own Constraint that backend call
   sequences stay identical.
2. **New shared `SkillsTree.tsx`** (`src/frontend/src/features/agents-map/
   SkillsTree.tsx`) — a presentational, mode-parameterized, collapsible,
   icon-bearing, Tool-grouped tree, reading the `"tool"` field
   `REQ-SB-48-US-01-T01` adds to `skill_tools.SKILLS`/`SkillSummary`/
   `AgentCapability`. Two modes via props: `mode="manage"` (per-row
   Grant/Revoke buttons firing the parent's own callback immediately —
   `AgentDetailPanel.tsx`'s real Capabilities-section usage, `REQ-SB-48`'s
   own scope) and `mode="select"` (checkbox multi-select, no immediate API
   call, parent owns the selected-id array — `CreateAgentWizardModal.tsx`'s
   new Step 3, replacing today's flat Worker-only checkbox list AND
   extending multi-select Skills selection to Expert/Producer for the
   first time, per the story's own Scenario 5). Grouping/collapse-state
   logic (`REQ-SB-48`'s own resolved 4-Tool taxonomy: Outlook/Vault/Web/
   Compass, 4 fixed Tool-level Unicode-glyph icons) lives exactly once, in
   this shared component — never duplicated into a second, wizard-local
   tree implementation. `REQ-SB-48-US-01-T02` is the task that actually
   originates `SkillsTree.tsx` (it lands first — `REQ-SB-48` is already
   `Ready` with locked ACs/tasks targeting this exact component before
   `REQ-SB-46` reaches `/plan-tasks`); `REQ-SB-46-US-01`'s own Step-3 task
   consumes it, carrying a real cross-story `depends_on: REQ-SB-48-US-01-T02`
   edge — the decomposer wires the exact edge, this pass records the
   requirement. This is the first genuinely cross-story frontend
   `depends_on` edge in this codebase's task graph (every prior
   `depends_on` edge has been intra-story); Pipeline.md hard rule 7
   explicitly anticipates dependency-linked stories landing in the same or
   ordered sprints, so this is a real but permitted graph shape, not a
   violation.
3. **Trigger/Schedule composition — reconfirmed unchanged, no new
   mechanism.** Step 4's "Schedule" Trigger choice stays a metadata-only
   placeholder (`{"key": "Trigger", "value": "schedule"}`, via
   `create_agent`'s existing generic `settings` kv-list, mirroring
   Domain/Purpose — `CreateAgentBody` gains one additive optional
   `trigger?: str` field on `agents_router.py`'s `POST /agents`, applied
   uniformly across all three types after their own per-type `settings`
   list is built, defaulting to `"user"`), with the same honest
   placeholder message pointing at `REQ-SB-47`'s own Schedule tab. Actually
   composing a real schedule at creation time was considered (Alternatives)
   and rejected — `REQ-SB-47`'s own schedule-CRUD contract requires two
   additional required inputs this story's own Step 4 does not collect
   (which capability, what interval), and building that collection UI
   inline would directly re-open the story's own already-written
   Non-Goals ("`REQ-SB-47`'s own Schedule tab / schedule-configuration UI
   — not built here") and its locked Scenario 8 wording ("no
   schedule-configuration UI of any kind opens inline"). No architecture
   change needed here beyond the additive `trigger` field already named in
   the story's own Constraints.
4. **Background-Agent toggle — fold-in declined, deferral stands.** This
   story's own locked Acceptance Criteria (Scenarios 1-11) name no
   Background-Agent toggle anywhere; adding one now would be undisclosed
   scope creep beyond what any scenario requires, and this role may not
   expand a story's scope beyond its own Context/Constraints (Pipeline.md:
   architect must not modify ACs). It would also create a hard dependency
   on `REQ-SB-51-US-01`'s own `is_background_agent` registry/`PATCH` field,
   which is `Ready` but not yet `Done`/built — a real, avoidable coupling
   for a toggle no locked scenario needs. `REQ-SB-51-US-01`'s own Non-Goals
   reasoning ("fully available post-creation via Settings... a future story
   may add this to whichever wizard shape is current once `REQ-SB-46`
   lands") already anticipates exactly this outcome and remains correct —
   a FUTURE story, not this one, is the right place to fold it in, once
   both mechanisms are independently `Done` and a locked AC actually asks
   for it.

**Alternatives Considered:**

- **Duplicate a second, wizard-local Skills-tree implementation instead of
  extracting `SkillsTree.tsx`** — rejected: directly contradicts the
  operator's own explicit "avoid duplicating the tree UI in two places"
  preference; would leave two divergent tree implementations (taxonomy,
  icons, collapse behavior) to keep in sync by hand as the Skill catalog
  grows.
- **Originate `SkillsTree.tsx` from `REQ-SB-46` instead, with `REQ-SB-48`
  refactored to consume it afterward** — rejected: `REQ-SB-48-US-01` is
  already `Ready` with locked ACs and a task (`T02`) whose own `## Files to
  Modify` and verification steps are already scoped and written against
  `AgentDetailPanel.tsx` directly originating the tree; re-sequencing to
  have a later-arriving sibling story originate it would mean reopening
  `REQ-SB-48-US-01-T02`'s already-locked task file, which the decomposer
  may not do once written. Letting the earlier-shipping sibling originate
  the shared component, and this one consume it via a `depends_on` edge,
  needs no rework of already-locked work.
- **Reuse `.side-panel-overlay`/`.side-panel`'s exact class names/behavior
  for the new popup modal** — rejected: Scenario 2 explicitly requires the
  new modal be "distinct from the existing agent-detail side panel's
  slide-in overlay"; the two are structurally different shapes
  (edge-anchored slide-in vs. centered popup with a step bar) — reusing
  the exact selectors/behavior would not satisfy that scenario's own
  distinctness requirement, even though the underlying design tokens
  (colors, spacing, surface treatment) are intentionally shared for visual
  consistency.
- **Compose `REQ-SB-47`'s real schedule-creation call directly into Step
  4, now that its endpoints exist** — rejected: needs two additional
  required inputs (capability, interval) this story's own locked Step 4
  does not collect, and would silently expand this story's own AC surface
  beyond what the analyst/decomposer wrote and locked; the honest
  placeholder-message pattern (`REQ-SB-37-US-03`'s own `write-to-vault-draft`
  precedent) is unchanged and sufficient.
- **Fold the Background-Agent toggle into Step 1 or Step 4 now** —
  considered (the operator explicitly asked this pass to decide, not
  default): rejected because no locked AC requires it and it would
  introduce a real, avoidable dependency on `REQ-SB-51-US-01`'s own
  not-yet-`Done` backend field; revisit as a small, cheap follow-on once
  both this story and `REQ-SB-51-US-01` are `Done`.

**Consequences:**

- `CreateAgentWizard.tsx` is renamed/restructured to
  `CreateAgentWizardModal.tsx` — its existing per-type submit handlers and
  call sequences are preserved byte-for-byte in logic, only regrouped into
  4 steps and wrapped in the new modal/step-bar container; no backend
  contract changes beyond the additive `trigger` field.
- `SkillsTree.tsx` becomes this codebase's first shared frontend component
  intentionally consumed by two different real workflows (management vs.
  pre-creation selection) — a reusable pattern future Skill-selection UIs
  can extend, rather than each screen growing its own bespoke list/tree.
- First genuinely cross-story frontend `depends_on` edge
  (`REQ-SB-46-US-01`'s Step-3 task → `REQ-SB-48-US-01-T02`) — the
  product-owner must sequence `REQ-SB-48-US-01` no later than the same
  sprint as (and ordered before) `REQ-SB-46-US-01`'s own Step-3 task, per
  Pipeline.md hard rule 7.
- Settings' `+ Create agent` `<details>` disclosure
  (`CreateAgentCard.tsx`) is retired; `SettingsPage.tsx` loses that
  affordance entirely, per Scenario 1 — no duplicate entry point remains.
- `agents_router.py`'s `CreateAgentBody` gains one additive `trigger?: str`
  field; `create_agent`'s per-type `settings` construction gains one
  uniform trailing append (`{"key": "Trigger", "value": trigger or
  "user"}`) applied identically across all three type branches — no
  per-type special-casing needed, since the append happens after each
  branch's own `settings` list is already built.
- The Background-Agent toggle question is revisited as a small, separate,
  future story once `REQ-SB-51-US-01` ships — not blocked or foreclosed by
  this decision, only deferred with a named, disclosed reason.

---

## ADR-040: Capture pipelines split into Pull/Tag/Link/Store agent stages (`REQ-SB-53`) — a new shared, capture-type-agnostic `app/business/capture_pipeline.py` orchestration engine; per-stage working-mode gate reuses `ADR-018` point 4's per-agent tick-level Autonomous/Supervised/Manual pattern generalized to 4 stages (never routed through `skill_registry.invoke_skill`); buffered/deferred per-item history commit (a new additive `"reverted"` history kind) implements the partial-failure rollback; Supervised-stage suspension resumes via a new `pending_approvals_router.py` branch reusing the existing `trigger="background"` idempotency guard — extends `ADR-005`, `ADR-011`, `ADR-018`, `ADR-020`, `ADR-029`, `ADR-030`, `ADR-036`'s shared-module precedent; reopens none of them

**Status:** Accepted
**Date:** 2026-08-15
**Reconsidered note (2026-08-15, append-only — the body below is otherwise
unchanged, per this file's own "never edit an Accepted ADR" rule):** the
operator directly raised, mid-flow, before `/plan-tasks` step 2
(decomposer) ran — "shouldn't LangGraph handle this agent-to-agent retry
and stuff?" — asking whether this ADR's own hand-rolled buffered-commit-
plus-rollback and Supervised-stage-suspend-then-resume mechanism should
instead be built on LangGraph's own checkpointer + `interrupt()`/
human-in-the-loop primitives, given `langgraph` is already a real,
installed dependency (`ADR-015`), not a hypothetical new one. Reconsidered
directly against that specific comparison (see the new Alternatives
Considered entry below) — **the Decision is unchanged; this pipeline
stays fully hand-rolled.** Logged: `ESCALATIONS.md` → `ESC-036`.
**Superseded note (2026-08-15, append-only — the body below is otherwise
unchanged):** immediately after the reconsideration above, the operator
stopped forward work entirely and drove a from-scratch taxonomy
discussion ("this is getting messy... let's discuss all types of
Agents"), which produced a genuinely different domain model — see
[ADR-041](ADR.md). Under that model, a Pipeline is a user-extensible DAG
of lightweight **Jobs** (own prompt + Skills, NOT a full Agent identity),
not a fixed 4-stage chain of 4 separately-visible, separately-gated full
Agents. This ADR's own core shape — Puller/Tagger/Linker/Storer as 4
individually-addressable `_SEED_AGENTS` entries per capture type, gated
individually via `working_mode_registry` — **is superseded by ADR-041**
and should not be built as designed here. `REQ-SB-53` and its 3 stories
(`US-01`/`US-02`/`US-03`) need to be re-scoped against the new Job/
Pipeline/Hub model before any `/plan-tasks` decomposer step runs on them
— they are parked, not cancelled (see `BACKLOG.md`). This ADR's own
Alternatives Considered reasoning about LangGraph (below) is NOT
invalidated by this note — if anything ADR-041 leans further toward
LangGraph, for the DAG/builder capability specifically, not for this
ADR's own now-superseded fixed-chain shape.
**Context:** `REQ-SB-53-US-01`/`US-02`/`US-03` (Email/Meetings/To-Do) each
split one monolithic capture Worker (`email-capture`/`meeting-capture`/
`todo-capture`) into 4 separate, individually-visible, individually-gated
agent identities — Puller → Tagger → Linker (`type: "producer"`, resolved
in `REQ-SB-53-US-01`'s own `## Notes`, 2026-08-15) → Storer — running
in-process, in one atomic pipeline pass per item, on the SAME existing
`capture_scheduler.py` trigger (no new schedule, no persisted queue —
locked by the PRD's own resolved clarifying-question block). Two real
design questions are explicitly left to this architecture pass by all 3
stories' own Context/Constraints sections, verified directly against the
real current code before deciding either:

1. **Mechanism for the locked partial-failure OUTCOME** (Scenario 4, all
   3 stories): if Link fails after Tag already succeeded for one item,
   Tag's own history entry for that item must show failed/reverted, Store
   never runs for it, and the whole item retries from Pull next tick — the
   PRD's own text explicitly asks whether Tag's history write happens
   immediately then gets amended/superseded, or is deferred until the
   whole pipeline settles.
2. **Composition with the existing single-call, two-axis working-mode gate**
   (`skill_registry.invoke_skill`/`_dispatch_skill`, `ADR-020`/`ADR-029`):
   today that gate checks ONE agent, ONE Skill/action invocation, at a
   time. This story's Scenario 6 needs a single logical capture attempt to
   genuinely SUSPEND mid-pipeline (Pull/Tag/Link Autonomous, Store
   Supervised → a real Pending Approval, resumed on Approve) — a shape the
   existing gate has never composed with, since it was built for exactly
   one dispatch per call.

**Real, code-grounded precedent this pass builds on, confirmed by direct
reading, not assumed:**

- `ADR-018` point 4 (still Accepted, unedited by `ADR-020`) already gates
  a SCHEDULED, TICK-LEVEL, per-agent background step — two explicit
  sequential blocks inside `email_classification.py::
  run_capture_and_record_completion`, each checking
  `working_mode_registry.get_agent_working_mode(agent_id)` directly
  (Autonomous runs the step; Supervised creates ONE `trigger="background"`
  Pending Approval, idempotent per tick via `create_pending_approval`'s own
  existing dedup guard; Manual skips silently, no history entry) — **never
  routed through `skill_registry.invoke_skill` at all.** This is the
  correct, already-Accepted precedent for gating an internal pipeline
  step, not `invoke_skill`'s catalog-Skill gate (see Alternatives).
- `ADR-011`'s `append_agent_history_entry`/`load_agent_history` are
  explicitly **append-only** — `ADR-018` point 7: "the history entry's own
  text/kind never change after creation." No code path anywhere in this
  codebase mutates a previously-written history entry in place.
- `ADR-036` (Cockpit) established this codebase's own precedent for "one
  architectural mechanism, applied per-type via a shared, generic module,
  not N independently-invented parallel copies" (`app/business/cockpit/`,
  generic over `subject_kind`) — the exact shape `REQ-SB-53-US-02`/`US-03`
  themselves already declare they will reuse, not re-derive, from this
  story.
- `pending_approval_registry.create_pending_approval`'s `payload: dict |
  None` field is already additive/generic (`ADR-021` point 4) — already
  used to carry arbitrary deferred-action state (the Vault Filing Expert's
  proposed kind/tags/body).
- Each of `email_classification.py`/`meeting_classification.py`/
  `todo_classification.py`'s real, current Pull/Tag/Link/Store logic
  (fetch shape, Compass-vs-majority-vote Tag, EntryID-vs-recomputed-path
  dedup, Person-linking-vs-customer-only-Link) was read directly — see
  each story's own Context table — and diverges meaningfully enough
  between the 3 types that the shared mechanism below must never contain
  any capture-type-specific business logic itself.

**Decision:**

1. **New shared, capture-type-agnostic module, `app/business/
   capture_pipeline.py`** — mirrors `ADR-036` point 2's own "one shared
   module, generic over a per-application parameter, not two/three
   parallel copies" precedent, one layer over: generic over `capture_type`
   (`"email"` | `"meeting"` | `"todo"`) and a `stage_agent_ids` mapping
   (`{"pull": "email-puller", "tag": "email-tagger", "link":
   "email-linker", "store": "email-storer"}`), never over any
   Outlook/Compass/vault-write call itself. Owns exactly four concerns:
   the per-stage working-mode gate check, the per-item buffered/deferred
   history commit (point 3), Supervised-stage Pending-Approval creation
   and resumption (point 4), and the top-level tick entry point,
   `run_capture_pipeline(capture_type, stage_agent_ids, pull_fn, tag_fn,
   link_fn, store_fn) -> list[dict]` (same return shape every capture
   type's own current entry function already has). It never imports
   `outlook_com`/`compass_client`/`customer_hub_linking`/
   `people_extraction` directly — those stay exactly where they are today,
   inside each capture type's own business module.
2. **Each capture type's own existing monolithic function is split into 4
   real stage functions, kept inside that type's OWN existing file**
   (`email_classification.py`'s `classify_recent_emails` →
   `pull_recent_emails() -> list[dict]`, `tag_emails(items) ->
   StageResult`, `link_emails(items) -> StageResult`, `store_emails(items)
   -> StageResult`; exact literal names are decomposer/coder latitude,
   this shape is not). **Never moved into `capture_pipeline.py` itself** —
   the shared module is the ENGINE; each type's own real business logic
   (Compass calls, majority-vote customer derivation, EntryID-keyed dedup,
   the `recipients`/`attendees` JSON-string frontmatter workaround, the
   narrower Link-with-no-Person-linking shape for To-Do) stays exactly
   where it already lives, confirming the shared-module boundary is drawn
   at the right seam — none of these real, already-established divergences
   between the 3 types ever needs to leak into the generic engine.
   Contract: `pull_fn() -> list[dict]` (raw fetched items); `tag_fn`/
   `link_fn`/`store_fn(items: list[dict]) -> StageResult`, where
   `StageResult = {"succeeded": list[dict], "failed": list[tuple[dict,
   Exception]]}` — each stage function loops its own real per-item work
   (generalizing `classify_recent_emails`'s own already-existing per-item
   `try/except CompassError: ...; continue` shape, from one known
   exception type to any `Exception`, mirroring `ADR-011`'s established
   honest-failure-funnel pattern) and partitions items itself; the engine
   never inspects an item's own business fields, only which partition it
   landed in.
3. **Partial-failure rollback — buffered/deferred per-item history commit,
   never immediate-write-then-mutate.** As `run_capture_pipeline` walks
   Pull → Tag → Link → Store for one tick's batch, it holds each item's own
   list of TENTATIVE per-stage outcomes in memory — no
   `append_agent_history_entry` call happens until an item's fate for this
   tick is fully known. Once known:
   - **Full success (the item reached Store):** one real `"run_event"`
     history entry per stage is committed, each attributed to that stage's
     own `agent_id` (Scenario 1 — 4 separate, attributed entries).
   - **Failure at some stage:** a `"run_error"` entry (already an
     established, if informally-enumerated, kind — used today by
     `run_capture_and_record_completion`'s own except blocks) is committed
     for the FAILING stage's own agent; **every earlier stage this item had
     already tentatively passed through this tick gets one new, additive
     history-entry kind, `"reverted"`** (extends `ADR-011`/`ADR-018` point
     7's `"chat_user" | "chat_agent" | "run_event" | "proposal"` enum by
     one value) — never a mutation of an entry that was never written,
     since the tentative outcome was held in memory, not persisted, until
     this point. This is what makes Scenario 4's "a human reviewing this
     email's Agent Activity sees ONE clear failure for it, not a split
     trail" literally true: Tag's own persisted history for that item is
     `"reverted"`, never a bare `"run_event"` success a human would have to
     mentally discount.
   - **Store never runs for a failed item** — it is simply excluded from
     the batch handed to `store_fn`; no explicit "retry state" is needed,
     since the item was never marked processed (each type's own existing
     dedup mechanism — EntryID lookup, filename-exists check — naturally
     re-surfaces it next tick, unchanged).
   - Other items in the SAME tick's batch that did not fail continue and
     commit independently — rollback is genuinely per-item, isolated from
     sibling items, a real new capability this buffered design supports by
     construction (each item carries its own tentative-outcome list).
4. **Working-mode gate — per-stage, per-TICK (batch-level), generalizing
   `ADR-018` point 4's own two-explicit-block precedent to four blocks,
   never routed through `skill_registry.invoke_skill`.** Before each
   stage runs the current batch of live items, `capture_pipeline.py`
   checks that stage's own `working_mode_registry.get_agent_working_mode
   (stage_agent_id)` directly:
   - **Autonomous** — runs the stage function against the whole batch,
     exactly as today's whole-pipeline Autonomous path does.
   - **Manual** — skips silently for the whole batch, dormant this tick,
     zero history entries (Scenario 7) — and, since the next stage's own
     input never arrives, every downstream stage is a no-op for this batch
     this tick too, with no special-case code needed (the batch handed
     downstream is simply empty).
   - **Supervised** — creates exactly ONE Pending Approval covering the
     WHOLE batch of items that reached this stage this tick (not one per
     item — see Alternatives), via the **existing, unmodified**
     `create_pending_approval(agent_id=stage_agent_id, trigger="background",
     action_id=f"pipeline:{capture_type}:{stage_name}", description=...,
     payload={"pipeline_resume": {"capture_type": capture_type,
     "stage_agent_ids": stage_agent_ids, "resume_stage": stage_name,
     "items": items}})`. Reusing `trigger="background"` (not a new trigger
     value) inherits `create_pending_approval`'s own existing per-agent
     per-tick idempotency-dedup guard with **zero new code** — a Supervised
     pipeline stage's own "don't pile up a fresh approval every tick while
     one is still outstanding" need is identical to the existing
     background-tick guard's own semantics. `action_id` is a new, synthetic,
     colon-bearing string (`"pipeline:email:store"`) — confirmed by direct
     reading to never collide with any real `skill_tools.SKILLS` key
     (none contain `:`) and never `None`, so it can never be
     misrouted into the legacy `action_id is None` branch (point 5).
     Downstream stages never run this tick for this batch (identical
     "nothing to consume" reasoning as Manual, above) — matches Scenario 6
     exactly (Pull/Tag/Link complete, Store alone suspends).
5. **`pending_approvals_router.py`'s Approve endpoint gains ONE new
   branch, checked before the existing `elif record["action_id"] is not
   None` / `else` (legacy background) branches:** if
   `record["payload"]` is a dict containing a `"pipeline_resume"` key,
   call `capture_pipeline.resume_pipeline_from_stage(**record["payload"]
   ["pipeline_resume"])` directly — bypasses the gate entirely, mirroring
   `ADR-018` point 6's already-Accepted "the approval itself is the
   authorization; re-entering the gate would find the agent still
   Supervised and defer forever" reasoning, applied one layer over.
   `resume_pipeline_from_stage` re-enters `capture_pipeline.py`'s own
   internal walk starting at the stage AFTER the one just approved,
   continuing forward through any REMAINING stages — each of which is
   still independently gated against ITS OWN mode (a downstream stage MAY
   itself be Supervised too, producing a second, cascaded Pending
   Approval; this is the intended, literal consequence of Scenario 5's
   "each of the 4 stages has its own independent Working Mode setting,"
   not a bug). History commit for the resumed run follows point 3
   unchanged — a fully-resumed item that reaches Store still gets all 4
   stages' own `"run_event"` entries committed together at that point
   (the ALREADY-approved stage's own tentative outcome, held in the
   approval's own `payload`, is committed alongside the newly-completed
   stages', not before). The 3 pre-existing Approve branches (a migrated
   Skill; an `_APPROVAL_HANDLERS` entry; a chat/direct `_execute_action`
   call) are **untouched**.
6. **`skill_registry.invoke_skill`/`_dispatch_skill` are untouched — no
   new `trigger` literal, no new branch, no new call site.** These 4
   pipeline stages are never `skill_tools.SKILLS` catalog entries (they
   are not independently invocable via chat/direct/hub_routed the way a
   real Skill is) — exactly like today's whole-pipeline gate, they are
   gated by a direct `working_mode_registry` check inside business-layer
   pipeline code, a call path that has never gone through `invoke_skill`
   (see Alternatives for why folding them in was considered and rejected).
7. **Agent registry & Background Agent inheritance** — `_SEED_AGENTS`
   gains 4 new entries per capture type (Puller/Tagger:
   `type: "worker"`; Linker/Storer: `type: "producer"`, per each story's
   own already-resolved Notes), replacing that type's one retired
   monolithic entry. `background_agent_registry.py`'s
   `_DEFAULT_BACKGROUND_AGENT_IDS` literal set is extended to the 12 new
   ids (mirrors its own already-documented "a bounded, literal exception
   set, not a general self-heal rule" shape — the same set is extended,
   not a new mechanism invented).

**Alternatives Considered:**

- **Immediate-write-then-mutate-in-place for Tag's history entry on
  downstream failure** (write a `"run_event"` success entry the moment Tag
  completes, then edit that same entry's `kind` to `"reverted"` if Link
  later fails) — rejected: breaks `ADR-018` point 7's own explicit,
  already-Accepted "a history entry's own text/kind never change after
  creation" invariant; every current consumer (`load_agent_history`,
  `AgentDetailPanel.tsx`'s History tab) assumes append-only semantics. The
  buffered/deferred-commit design (point 3) achieves the identical
  observable outcome — one clear failure per item — by only ever
  APPENDING, never editing, a previously-persisted entry.
- **Per-item Supervised Pending Approvals** (one approval per fetched
  email/meeting/task reaching a Supervised stage, each independently
  approvable) instead of one per stage per tick covering the whole batch —
  rejected: no locked Scenario asks for that granularity; a busy inbox
  could produce dozens of near-duplicate approval cards for a single tick,
  and `create_pending_approval`'s own existing `trigger="background"`
  idempotency guard is specifically a per-agent-per-tick (not per-item)
  dedup — batch-level resumption reuses that guard verbatim with zero new
  code, exactly extending `ADR-018`'s own already-Accepted, twice-reused
  (`ADR-018`, `ADR-037`) coarse-grained shape rather than inventing finer
  granularity nothing in this story's own text requires.
- **Routing the 4 stages through `skill_registry.invoke_skill` as real
  catalog Skills, reusing its existing two-axis gate directly** —
  considered, rejected: `invoke_skill`'s gate is built for exactly ONE
  dispatch per call, with a Pending Approval whose `payload` is "the
  arguments to one Skill invocation." A Supervised pipeline stage's own
  payload here is an entire in-flight BATCH of partially-processed items
  plus a resume point — a fundamentally different, pipeline-shaped
  payload the Skills catalog was never designed to carry. Folding it in
  would force `skill_tools.SKILLS` to grow 12 catalog entries for internal
  stages that are never independently triggerable via chat/direct/
  hub_routed the way a real Skill is — a structural mismatch, not a
  genuine reuse. `ADR-018` point 4's own already-Accepted, direct
  `working_mode_registry` check (never through `invoke_skill`) is the
  correct, already-precedented shape for gating an internal pipeline step,
  generalized one layer further (4 stages, not 2 capture-agents) rather
  than reused directly.
- **Each of the 3 sibling stories independently re-deriving its own
  orchestration/rollback/gate-composition logic inside its own file** (no
  shared module) — rejected in favor of one shared engine, per this
  codebase's own `ADR-036` Cockpit precedent for an almost identical
  shape (one mechanism, applied per-type, 2-3 real applications);
  `REQ-SB-53-US-02`/`US-03` themselves already declare (their own
  Context/Dependencies) that they reuse this story's own mechanism rather
  than re-derive it — confirming the intent was always "design once,
  build three times," not independent invention risking 3 subtly
  divergent rollback/gate implementations.
- **A real, persisted, per-item queue/staging architecture** (each stage
  genuinely decoupled, independently triggerable) instead of an in-process
  buffered-batch engine — out of scope, explicitly declined by the
  operator per all 3 stories' own Constraints/Non-Goals; not reconsidered
  here.
- **LangGraph's own `StateGraph` + built-in checkpointer + `interrupt()`/
  human-in-the-loop primitive**, in place of the hand-rolled buffered-
  commit-plus-rollback engine and the hand-rolled Supervised-stage-
  suspend-then-resume mechanism above — raised directly by the operator
  mid-flow (`ESCALATIONS.md` → `ESC-036`) and seriously reconsidered, not
  dismissed by reflex citation of the superseded 2026-08-11 "no
  orchestration framework" MEMORY entry (that entry is itself already
  narrowed/superseded by `ADR-015`, which adopted LangGraph for this
  project's own in-app conversational orchestration — `langgraph>=1,<2`
  is confirmed already present in `src/backend/requirements.txt`, so this
  is genuinely NOT a new-dependency question). **Rejected, for concrete,
  code-grounded reasons specific to this pipeline, not general aversion:**
  1. **This project already directly confronted and declined this exact
     idea, twice, on the record.** `ADR-015` point 6's own Alternatives
     Considered already rejected LangGraph's built-in persistent
     checkpointer (`SqliteSaver`/`langgraph-checkpoint-sqlite`) for
     cross-request conversation state, "a new storage technology (SQLite)
     this project has repeatedly and explicitly rejected for local state
     (`ADR-005`, `ADR-011`, `ADR-014`) ... no reason to make a different
     call here" — and `ADR-015`'s own Consequences went further, naming
     the EXACT scenario this ADR now faces ("a Supervised agent's
     'propose an action and wait for approval' behaviour may eventually
     want LangGraph's own `interrupt()`/human-in-the-loop primitive"),
     leaving it explicitly open for `REQ-SB-21`'s own future architecture
     pass. That pass happened (`ADR-018`) and did **not** adopt
     `interrupt()` — it built the hand-rolled `pending_approval_registry.py`
     / `agent_pending_approvals.json` mechanism this ADR is the THIRD
     extension of (`ADR-029`'s Skills gate, `ADR-037`'s Scheduler, now
     this). Adopting LangGraph's checkpointer here would reverse that
     already-lived-with, twice-reused, working precedent for one more
     bounded case, not extend it.
  2. **Cross-restart durability is a hard requirement here that `ADR-015`'s
     own "in-memory `MemorySaver` is expected to be sufficient" reasoning
     explicitly does not cover.** `ADR-015`'s Consequences reasoned an
     in-memory checkpointer would suffice for a chat-triggered approval
     because "no cross-restart persistence need" — true for a single
     synchronous HTTP request/response. This ADR's own Pending Approvals
     are background/scheduled proposals routinely left unresolved for
     hours or days (per `pending_approval_registry.py`'s own real
     `create_pending_approval`/`resolve_pending_approval` shape, already
     built for exactly that), across however many `uvicorn --reload`
     restarts land in between — a routine, already-documented occurrence
     in this project's own `Learnings.md` (`SPRINT-021`/`022`/`027`/`028`
     entries on stale/reloaded dev-server processes). An in-memory
     `MemorySaver` would silently lose every paused pipeline on the next
     restart; genuine durability would require `SqliteSaver`
     (`langgraph-checkpoint-sqlite`, not currently installed) — a real
     new persistence technology, exactly what point 1's precedent already
     rejects, for the same reasons.
  3. **No dynamic, LLM-driven branching exists anywhere in this pipeline
     for a graph engine to actually earn its keep on.** `ADR-015`'s graph
     manages a genuinely dynamic `call_model` ⇄ `execute_tools` loop whose
     next step depends on the model's own output. Pull/Link/Store make no
     LLM call at all; Tag makes exactly one deterministic classification
     call per item (Compass for Email/To-Do, a majority vote for
     Meetings) — not a loop, not model-driven routing. The ONLY
     conditional branching anywhere in this pipeline is the working-mode
     gate, a plain 3-value enum lookup — precisely the class of logic
     `ADR-018` point 4 already solved in a few lines of direct
     `working_mode_registry` calls, reused unchanged by `ADR-029` and
     `ADR-037`. A graph-execution engine buys nothing over that already-
     working shape when there is no dynamic branching for it to manage.
  4. **A checkpointer would not even remove the hand-rolled bridging code
     this ADR needs — it would sit alongside it, duplicating state.**
     This app's Pending-Approvals surface (a flat, filterable list; `GET`/
     `POST .../approve|decline`; an idempotent-per-tick dedup guard; a
     `payload` dict; every existing UI card) has no native equivalent in
     LangGraph's own thread-id/checkpoint model — translating an
     `interrupt()` pause into a real Pending Approval record, and an
     Approve click back into a `graph.invoke(Command(resume=...))` call,
     would still require essentially all of points 4/5's own bridging
     code above, now WITH a second, parallel state representation (the
     checkpoint DB's own paused-graph-state) alongside the Pending
     Approval record already carrying the identical information via
     `payload.pipeline_resume` — the exact "a second, divergence-risking
     representation of the same fact" shape `ADR-015` point 6 already
     named and rejected for chat history, recurring here for pipeline
     state. Net effect: a new dependency surface, a new persistence
     technology, and MORE code, not less — the literal "worst of both
     worlds" the operator's own question anticipated.
  **Conclusion: partial adoption (using LangGraph's checkpoint/interrupt
  primitives directly, without adopting it as this pipeline's general
  orchestrator) is not a sensible middle ground for this specific
  mechanism — it is strictly worse than the hand-rolled design on every
  axis raised (dependency footprint, persistence-technology consistency,
  restart durability, and code volume), for a pipeline with no dynamic
  LLM-driven branching to justify a graph engine in the first place.**
  `ADR-015`'s own conversational graph is untouched by this ADR either
  way — this reconsideration does not reopen or narrow it.

**Consequences:**

- **Zero new `.second-brain/` state files.** This ADR reuses
  `agent_working_modes.json`, `agent_pending_approvals.json`, and
  `agent_communication_history.json` exactly as they exist today — the
  only additive changes are one new history `kind` value (`"reverted"`)
  and one new, additive `payload` shape convention
  (`{"pipeline_resume": {...}}`) on existing Pending Approval records.
- `agent_communication_history.json` entries gain a 6th real `kind` value
  (`"run_error"` was already de facto in use, just not formally
  enumerated in `ADR-011`/`ADR-018`'s own docstrings; `"reverted"` is
  genuinely new) — any future frontend rendering of the History tab must
  handle it explicitly (a plain, non-error-styled but visually distinct
  treatment is a reasonable default; exact styling is decomposer/coder
  latitude, not resolved here).
- `email_classification.py`'s current `classify_recent_emails` and its
  `run_capture_for_agent`'s `if agent_id == "email-capture": ...` mapping
  become dead once `REQ-SB-53-US-01`'s own `T02` lands (the `email-capture`
  agent id no longer exists) — the equivalent `meeting-capture`/
  `todo-capture` mappings stay exactly as-is until each sibling story
  ships, confirming zero cross-story regression in the interim (both
  sibling stories are explicitly `depends_on`-blocked on this story's own
  architecture, per their own Dependencies sections, not on simultaneous
  delivery).
- `pending_approvals_router.py` gains one new Approve branch and
  `capture_pipeline.py` gains one new module — the 3 pre-existing Approve
  branches (Skill, `_APPROVAL_HANDLERS`, chat/direct) are unmodified.
- Each capture type's own real, already-established divergences
  (deterministic majority-vote Tag vs. Compass-LLM Tag; EntryID-keyed vs.
  recompute-and-`exists()` dedup; a narrower Link stage with no
  Person-note linking for To-Do) are preserved untouched inside each
  type's own 4 stage functions — the shared engine's own `StageResult`
  contract never needs to know or care about any of these differences,
  confirming the module boundary (point 1/2) is drawn at the correct seam.
- The Agents Map's 4x-denser capture cluster (12 new agents replacing 3)
  is architecturally unaffected (every downstream surface is already
  agent-count-agnostic, confirmed directly by each story's own Context) —
  a disclosed, non-blocking future `/design` concern, not resolved here.
- **Future extensibility:** a real persisted queue/staging architecture
  (explicitly declined this pass) would most likely replace
  `capture_pipeline.py`'s in-process batch-buffer with a persisted
  per-item state machine — this ADR's own module boundary (stage
  functions are plain, engine-agnostic list-in/`StageResult`-out
  callables) is deliberately chosen so that would be a swap of the ENGINE
  only, never a rewrite of any of the 3 capture types' own real Pull/Tag/
  Link/Store business logic, should that ever become a future story.

---

## ADR-041: Agent/Pipeline/Job/Hub domain-model taxonomy adopted; Pipelines become user-authored DAGs executed on LangGraph, with a native React Flow visual builder — supersedes ADR-040's fixed-chain shape; narrows ADR-007/ADR-015's "simple linear pipelines stay outside orchestration" carve-out for the Pipeline domain specifically

**Status:** Accepted (directional/foundational — implementation specifics
deferred to `/plan-tasks` on whatever requirement formally re-specs
`REQ-SB-53`; see Consequences)
**Date:** 2026-08-15

**Context:** Immediately after ADR-040 was reconsidered against LangGraph
and kept unchanged (see that ADR's own Reconsidered note, `ESC-036`), the
operator stopped all forward implementation and drove a from-scratch
taxonomy discussion: "I guess we need to stop working and We start
discussing All types of Agents and Build a Taxonomy to be our guide from
now on as this is getting messy." The proximate trigger: ADR-040 forced
4 pipeline stages into the existing Worker/Producer/Expert Type model,
and the 4th stage (Linker) was genuinely, structurally ambiguous across
all 3 types — not a values-open-question the way Marcellus's placement
was for `REQ-SB-52`, but a sign the TAXONOMY ITSELF had no correct slot
for what a pipeline stage actually is. The discussion (worked example: an
email with an attachment forks into a body-classify Job and an
attachment-classify Job, merges back, optionally branches to consult an
"Opps Expert" mid-flow, always terminates in Store) confirmed this
directly — real pipelines fork, merge, and conditionally consult Experts;
they are not the linear 4-box chain ADR-040 assumed.

**Decision — the domain model, going forward:**

1. **Two independent axes, not one flat list of types.**
   - **Kind of work:** *Expert* (answers questions over the KB), *Producer*
     (composes/generates a deliverable — a file, an email reply, a to-do
     action), and the mechanical pipeline verbs (fetch, classify/tag,
     link, store, and any future verb a Pipeline author adds).
   - **Structural tier:** *Agent* (a full, independently-addressable
     identity — own chat, own communication history, own Working Mode,
     own Agents Map node; today's Worker/Producer/Expert `_SEED_AGENTS`
     entries are all this tier) vs. *Job* (a lightweight unit that lives
     INSIDE a Pipeline's own DAG — its own editable prompt and its own
     Skill(s), but not a full Agent identity by default: no guaranteed
     own chat thread, own Map node, or own Working Mode setting, unless a
     future pass decides a specific Job-level surface is worth exposing).
   - A "Producer" can be either tier: a standalone Producer AGENT (you
     ask it directly, e.g. "build me a sheet") or a Producer-flavored JOB
     embedded in someone else's Pipeline (the email-reply gets composed
     mid-pipeline, then handed downstream to be stored). "Expert" is
     always the Agent tier — by definition something the user and other
     agents/pipelines address directly. The mechanical pipeline verbs
     (fetch/classify/link/store) are always the Job tier.
2. **Hub** — the root of a Section's own tree. Both a MANAGER (knows/
   routes to its own Pipelines and Experts) and a DATABASE (holds the
   Section's own registry: which files/vault scope it works with, which
   agents and pipelines belong to it). Not a new structural tier of its
   own — an organizing node, matching this app's own existing Section
   concept, now given an explicit manager+database job description.
3. **Pipeline** — a user-extensible DAG of Jobs, not a fixed N-stage
   chain. Real, confirmed capabilities a Pipeline must support: forking
   (parallel Jobs over different parts of the same input), merging
   (parallel branches recombine into one stream), and branching to
   consult a standalone Expert mid-flow (the Expert's answer feeds back
   into the Pipeline; consulting an Expert is additive, not a replacement
   for the Pipeline's own terminal step — e.g. Store still runs either
   way). The user adds/removes/rewires Jobs themselves, via the builder
   (point 5) — this is not something engineers hardcode per pipeline
   type going forward, which is the specific way ADR-040's fixed
   Puller→Tagger→Linker→Storer chain no longer fits.
4. **Prompt customization is universal** — every Agent (Expert, Producer)
   and every Job gets the same "edit this thing's own instructions"
   mechanism, one UI pattern wherever it appears. Not designed in detail
   here; a real, locked requirement for whatever story implements it.
5. **Execution engine: LangGraph, for the Pipeline domain specifically —
   narrows `ADR-007`'s original "simple linear pipelines stay outside any
   orchestration framework" carve-out further than `ADR-015` already did.**
   `ADR-015` bounded LangGraph to Second Brain's own in-app AGENT
   behavior (chat, Hub routing, memory, skill invocation) and explicitly
   left `compass_client.py`'s linear classification pipelines outside
   that boundary, unreconsidered. This ADR reconsiders that carve-out for
   the Pipeline domain ONLY, because Pipelines now have genuine dynamic
   structure (fork/merge/conditional-Expert-branch) and need real
   mid-pipeline suspension for human approval — exactly what `ADR-015`'s
   own Consequences already flagged as a plausible future use for
   LangGraph's checkpointer/`interrupt()` primitives, and exactly the
   capability ADR-040's own hand-rolled Pending-Approval-resume mechanism
   was a narrower, bespoke stand-in for. `langgraph` is already a real,
   installed dependency (`ADR-015`) — this is a scope widening of an
   existing tool, not a new one. A Pipeline's own DAG (author-defined via
   the builder) is compiled into a `langgraph.graph.StateGraph` at
   runtime, distinct from `ADR-015`'s own single, code-fixed chat graph.
6. **Builder: a native canvas inside the existing React frontend (e.g.
   React Flow), not an external visual-builder application (LangFlow/
   Flowise-style tools were considered and explicitly declined).** Reason:
   this app has consistently stayed one cohesive product — the builder
   needs to share the Hub/Section/Agent/Skill data model and the Agents
   Map's own visual language directly, not fight an external tool's own
   data model or require running/self-hosting a second service.
7. **`ADR-040` is superseded, not deleted** — see the Superseded note
   appended directly to that ADR's own entry, above. `REQ-SB-53` and its
   3 sibling stories are parked (not cancelled) pending a re-spec against
   this model.

**Consequences:**

- **This is directional, not implementation-complete.** Real, open
  questions deliberately NOT resolved by this ADR, left to whatever
  requirement/story formally re-specs the Pipeline Builder: the DAG's own
  persisted data model (how a user-authored Pipeline definition is
  stored — likely `.second-brain/`-flat-JSON per this project's own
  standing convention, but not decided here); the checkpointer's own
  persistence backend for genuine cross-restart durability of a
  suspended, Supervised-stage-pending pipeline (`ADR-015`'s own
  in-memory `MemorySaver` was judged sufficient for a single chat
  turn — a Pipeline can sit suspended for hours/days awaiting approval,
  the same durability problem ADR-040's own Reconsidered note flagged;
  whether that pushes toward a real `SqliteSaver` — this project's first
  departure from flat-JSON persistence — or a hand-rolled durable
  checkpoint reusing the existing Pending Approval registry, is
  unresolved here); whether/how a Job earns its own Agents Map presence,
  chat surface, or Working Mode in specific cases; the exact canvas UI/
  UX (node palette, wiring interaction, validation).
- **Sequencing, decided 2026-08-15 (operator, immediately after this ADR
  was written): the Builder (Decision point 6) is explicitly deferred
  until at least ONE real Pipeline is hand-built under this model
  first** — "We will build the pipeline Builder once we build actual
  Pipeline and know what we need to do." The builder is a generalization
  of real, learned requirements, not something to design from this
  ADR's own taxonomy alone. Concretely: the next real work is a single,
  concrete Pipeline (author-defined DAG expressed directly, e.g. in
  code or config — not yet through a visual canvas) built on the
  LangGraph engine (Decision point 5), most likely the Email capture
  flow given it's the fully worked example this ADR's own Context
  section already traced (fork body/attachment, merge, branch to an
  Opps Expert, terminate in Store). Only once that concrete pipeline is
  real and its actual needs are known does Decision point 6 (the native
  React Flow builder) get scoped and built. Do not start the Builder
  before a concrete Pipeline exists.
- **`REQ-SB-53` and its 3 stories stay parked in `Draft`/flagged status**
  (`BACKLOG.md`) until a new requirement (Pipeline Builder, or a rewritten
  `REQ-SB-53`) formally re-specs the Email/Meetings/To-Do capture flows
  as Pipelines under this model — this ADR does not itself re-write them.
- **Scope is large enough to likely need its own multi-story epic**,
  spanning: the Job/Pipeline/Hub backend data model, the LangGraph
  execution engine, the React Flow canvas UI, universal prompt
  customization, and migrating the 3 existing capture flows onto it —
  not a single story the way `REQ-SB-52`'s theme swap was.
- **`compass_client.py`'s own linear `classify_email`/`classify_task`
  functions are untouched by this ADR** — they keep running exactly as
  they do today until whatever story migrates Email/To-Do capture onto
  the new Pipeline engine actually lands; this ADR does not implicitly
  break or bypass today's real, working capture flows.

**Alternatives considered:**

- **Keep `ADR-040`'s fixed 4-stage chain, just resolve the Linker-Type
  question differently.** Rejected — the taxonomy discussion itself
  demonstrated the problem was never which Type Linker should be, it was
  that pipeline stages don't belong in the Agent-Type model at all. Any
  Type assignment would have been papering over the real structural
  mismatch.
- **External visual builder (LangFlow, Flowise, or similar).** Rejected
  — see Decision point 6. Faster to a working canvas, but fragments the
  product into two applications with two data models.
- **A fully generic, engine-agnostic DAG executor (no LangGraph
  dependency at all), mirroring `ADR-040`'s own hand-rolled approach one
  layer up.** Considered, not chosen — `ADR-040`'s Reconsidered note
  already established that hand-rolling was the right call for a FIXED,
  non-branching, no-visual-authoring pipeline; once real forking/merging/
  conditional-Expert-branching and a visual builder are genuine
  requirements, hand-rolling a second, bespoke graph-execution-plus-
  checkpointing engine duplicates what `langgraph` (already a real
  dependency) is specifically built for, with none of its tooling.

---

## ADR-042: Vault knowledge model redesign (`REQ-SB-54`) — directory-based OKF v0.2-conformant note kind for Customer/Project, a new header-scoped full-section regeneration primitive, and Thread notes keyed by Outlook `ConversationID` — extends `ADR-004`'s folder-vs-tag boundary, does not reopen it

**Status:** Accepted
**Date:** 2026-08-16

**Context:** `REQ-SB-54` (root pain, operator's own words: "The pain is I
can't find the current status of anything") replaces the vault's
note-per-email capture shape with a layered model: an **evidence layer**
(Thread, Meeting, manual Captures — raw, append-only, never silently
rewritten) feeding a **synthesis layer** (Customer and Project — living
documents, regenerated from current evidence). The design is fully
resolved (see `REQ-SB-54-US-01`'s own `## Context`/`## Notes` and PRD
`REQ-SB-54`) and adopts Google Cloud's Open Knowledge Format (OKF v0.2,
June 2026) literally, not as inspiration only — Customer and Project each
become a small directory (`index.md`/`<slug>.md`/`log.md`/`captures.md`),
not sections inside one file. Three concrete gaps against the current
codebase, found by direct inspection rather than assumed, make this
genuinely architectural rather than an ordinary same-shape extension:

1. **No existing `vault_writer.py` primitive can regenerate a bounded
   region of an already-written note's body.** Every note kind to date
   (Email, Meeting, Person, Customer hub, Partner hub, Task) follows one
   of two contracts: `write_note` (unconditional full overwrite, used
   only at first creation) or the baseline-then-surgical-insert-if-missing
   family (`insert_frontmatter_key_if_missing`,
   `insert_body_line_if_missing`) — both explicitly designed to
   **preserve** anything added after creation, never to regenerate it.
   `REQ-SB-54` point 8 requires the opposite for anything meant to reflect
   current state (a Thread's own summary, a concept file's own Glimpse
   section): full read-reconstruct-overwrite on every relevant change.
   `insert_body_line_if_missing`'s fixed-byte-offset-from-the-closing-`---`
   mechanism is already a documented, disclosed fragility for a note
   touched many times over its life (`MEMORY.md`, `BUG-003`/`ESC-003`,
   `Open`) — repeatedly regenerating a Glimpse section is exactly the
   repeated-touch case that bug report warns about, so leaning on that
   primitive for this new, much-higher-churn write pattern would be
   building directly on top of a known defect rather than around it.
2. **No existing note kind is a directory of multiple files.** Every kind
   to date is exactly one `.md` file, addressed by a deterministic
   path-resolution function (`hub_note_path`, `meeting_note_path`,
   `person_note_path`, `partner_hub_note_path`) sharing one
   create-baseline-then-top-up contract. OKF's own reserved-filename
   directory convention (`index.md`/`log.md` plus a `<slug>.md` concept
   file) is a structurally new shape this project has never written.
3. **`_format_frontmatter_value`/`_parse_frontmatter_value` round-trip a
   string or a list-of-strings only — a nested dict silently corrupts on
   read.** OKF's `generated: {by: <agent-id>, at: <timestamp>}` /
   `verified: {by: human:<operator>, at: <timestamp>}` actor-provenance
   fields are exactly this shape. This is the same class of gap already
   found and worked around twice in this codebase for a **list**-of-dicts
   (Meeting `attendees`, `ADR-036` point 7; Email `recipients`,
   `MEMORY.md` 2026-08-14) — both via a JSON-encoded STRING value under
   the field's own real name, never a native Python-dict-repr write (which
   reads back as `[]`/garbage). `generated`/`verified` are a single dict,
   not a list of dicts, but the same underlying `_format_frontmatter_value`
   limitation applies.

**Decision:**

1. **New directory-shaped note-kind primitive family in
   `app/data_access/vault_writer.py`, applied to both Customer and
   Project — one shared mechanism, not two parallel implementations.**
   Mirrors the existing hub-note-baseline family's shape
   (path-resolution / exists-check / create-baseline / top-up-if-partial)
   but produces four files instead of one:
   - `index.md` — OKF reserved; a pure auto-generated directory listing
     (bullet links + descriptions of what's inside). Zero user- or
     agent-owned prose ever lives here, so it is always a **whole-file
     swap** on every directory-membership change (the same unconditional
     `write_note`-style overwrite the baseline-creation functions already
     use at first-creation time) — never header-scoped, since there is no
     content to preserve.
   - `<slug>.md` — the OKF concept file: frontmatter (`type` at minimum,
     plus `title`/`description`/`tags`/`status`/`stale_after`/
     `generated`/`verified`/`sources`) and a body of exactly two
     `##`-headed sections, `## Glimpse` and `## Background`, each
     independently regenerated on its own cadence (Glimpse: every
     relevant evidence change; Background: only on a new durable fact —
     `REQ-SB-54` point 5). Two sections, not one whole-body regeneration,
     because collapsing them would force every routine Glimpse refresh to
     also recompute Background, contradicting Background's own
     slow-moving cadence rule and making the two impossible to trigger or
     test independently.
   - `log.md` — OKF reserved; append-only History, date-headed prose
     entries.
   - `captures.md` — not an OKF-reserved name, but the same
     isolate-anything-append-only-into-its-own-file principle, extended:
     physically separating Captures into its own file means a full-file
     open-and-rewrite of `<slug>.md` (Glimpse/Background regeneration)
     **cannot** touch it, by construction, not by convention — this is
     what upgrades `REQ-SB-54` point 7's single-owner rule from a
     discipline to a structural guarantee for the Captures axis
     specifically (the Glimpse/History "exactly one synthesizer" half of
     that rule is still convention-only, enforced by caller discipline —
     `REQ-SB-57`'s own scope, per this story's Constraints).
   `log.md`/`captures.md` are both appended to via the existing generic
   unconditional-append primitive (`vault_writer.
   append_person_note_update_line` — already fully generic over
   `path`/`line` despite its Person-era name; the decomposer/coder may
   rename it to reflect its now-multi-purpose role, but no new append
   primitive is needed).
2. **New primitive: `replace_body_section(path, header, new_content)`.**
   Locates the line matching `header` (e.g. `"## Glimpse"`) and the next
   `##`-level header (or end of file) that follows it, and replaces
   everything strictly between them — leaving every byte outside that
   bounded region (frontmatter, other sections, the header lines
   themselves) untouched, regardless of how many times the file has
   already been edited. This directly resolves the fixed-byte-offset
   fragility named in Context point 1, and is the canonical mechanism for
   **every** full-regeneration write this requirement introduces — not
   Customer/Project-only: a Thread note's own summary section (point 7,
   below) reuses it unchanged.
3. **`generated`/`verified` are written as JSON-encoded strings under
   their own literal OKF field names** — extending, not duplicating, the
   already-`Accepted` `recipients`/`attendees` list-of-dicts convention to
   a single-dict value. No second, inconsistent workaround is introduced
   for the same underlying `_format_frontmatter_value` gap.
4. **Customer's directory lives at `Work/Customers/<customer-slug>/`;
   Project nests one level inside its own Customer's directory, at
   `Work/Customers/<customer-slug>/projects/<project-slug>/`** — operator,
   direct confirmation, 2026-08-16: "Yes, Project gets the same directory
   shape as Customer" (`ESCALATIONS.md` → `ESC-037`, `Resolved`).
   `Work/Customers/` remains the existing `kind` folder (`list_known_kinds`
   already discovers it); this changes what lives **inside** an
   already-established kind folder (directories instead of flat files),
   it does not introduce a new kind-folder concept.
5. **Thread note kind: `Work/Threads/<slug-of-conversation-id>.md`, one
   per Outlook `ConversationID`, path resolved deterministically from
   `conversation_id` alone** — mirroring `hub_note_path`/
   `meeting_note_path`'s existing "deterministic path from a stable key,
   no separate lookup index" precedent, **not** a repurposing of
   `conversation_index.json`/`record_conversation_note` (see Alternatives).
   Body = `## Summary` (full regeneration via `replace_body_section`,
   point 2) + `## Transcript` (append-only, growing — one dated entry per
   later message in the same conversation, via the same generic append
   primitive point 1 reuses). `Work/Threads/` is a new, dynamically
   discovered `kind` folder — no code change needed for `list_known_kinds`
   to find it.
6. **Meeting note frontmatter gains one additive, currently-empty
   `thread` field** — reserved for `REQ-SB-56`'s own future
   Meeting→Thread linking, not populated by this story. Ordinary additive
   field, no new primitive.
7. **Threads and Meetings stay flat — never physically nested under a
   Customer/Project directory** — cross-linked only via `customer:`/
   `project:` frontmatter, tags, and an OKF `sources:` entry on the
   concept file. This directly extends `ADR-004`'s already-`Accepted`
   "Customer is a tag, never a folder level" rule (for real, multidimensional
   content notes) rather than reopening it — see Consequences.

**Alternatives Considered:**

- **Keep Customer/Project as a single flat file with in-file
  `## Glimpse`/`## History`/`## Background`/`## Captures` sections** (the
  story's own earlier working draft, superseded same-day by direct
  operator decision) — rejected. This relies on a section-boundary
  convention holding forever; a bug in a future Glimpse-regeneration pass
  could still corrupt History/Captures text within the same file. The
  operator's own stated reasoning (`REQ-SB-54` point 4/7): "physically
  separating Captures means an agent's full-file Glimpse regeneration can
  never touch it, by construction — not just by convention."
- **Repurpose `conversation_index.json`/`record_conversation_note` as the
  Thread-note lookup mechanism** instead of a deterministic path function
  — rejected. That file's shape (`conversation_id -> [note_stem, ...]`) is
  designed for MULTIPLE per-email notes sharing one conversation (today's
  "Related Emails" linking); forcing it to mean "conversation_id -> [the
  one Thread stem]" either leaves permanently-confusing single-element-list
  semantics or needs a schema migration, for zero benefit over computing
  the path directly the same way every other note kind already does.
  `conversation_index.json` itself is untouched by this ADR — it stays
  owned by today's still-live `email_classification.py` until `REQ-SB-55`
  replaces that module.
- **Flatten `generated`/`verified` into scalar keys**
  (`generated_by`/`generated_at`, `verified_by`/`verified_at`) instead of
  a JSON-encoded string under the literal `generated`/`verified` names —
  considered, rejected. `REQ-SB-54-US-01`'s own locked Scenario 3 names
  `generated`/`verified` as literal required frontmatter fields;
  flattening preserves the information but not the literal field name,
  and introduces a second, inconsistent workaround for the same
  `_format_frontmatter_value` limitation the `recipients`/`attendees`
  precedent already solved once.
- **Swap `_format_frontmatter_value`/`_parse_frontmatter_value`/
  `read_note` for a real YAML library (e.g. PyYAML)**, so nested
  dicts/lists-of-dicts round-trip natively — rejected for this pass.
  `read_note`'s docstring has explicitly disclaimed "not a general YAML
  parser" since `REQ-SB-01`, and every note this project has ever written
  was produced by this same writer, so there is no legacy-shape risk to
  hedge against; a full parser swap is materially larger and riskier than
  this story's own data-model scope, and the JSON-string workaround has
  already shipped safely twice. Revisit only if OKF frontmatter someday
  needs deeper nesting this workaround can't express.
- **Generalize the directory-note-kind shape to every note kind**
  (Meeting/Person/Partner too), not just Customer/Project — rejected as
  scope creep. Only Customer and Project are directory-shaped, per this
  story's own Scenario 3/Scenario 5 and the operator's explicit
  confirmation; Thread/Meeting/Person/Partner remain flat single files,
  unchanged.

**Consequences:**

- `app/data_access/vault_writer.py` gains: the directory-note-kind
  primitive family (point 1), `replace_body_section` (point 2, general
  purpose — also used by Thread, not Customer/Project-only), the
  deterministic `thread_note_path(conversation_id)` resolver (point 5),
  and reuse (possibly a rename) of the existing generic append primitive
  for `log.md`/`captures.md`/Thread-transcript growth.
- `app/business/customer_hub_linking.py` is **substantially restructured,
  not merely extended** — its single-file `ensure_customer_hub_note`/
  `create_customer_hub_note_baseline` contract no longer matches the new
  directory shape. `email_classification.py`'s existing live call site
  (`ensure_hub_note_and_link`) is a real, currently-running caller this
  story's own tasks must not silently break; the decomposer's `/plan-tasks`
  pass must either preserve that call's existing signature/behavior for
  the transition period or make the cutover an explicit `depends_on`
  ordering — this ADR does not itself decide which, only flags it as a
  real, load-bearing consequence.
- **`Work/Customers/` and the new `Work/Customers/<slug>/projects/`
  nesting are the first vault locations where a `kind` folder's own
  contents are not flat `.md` files.** `list_all_note_paths()`'s current
  one-level `Work/*/*.md` glob will not discover anything nested two
  directories deep — a Customer/Project's own `<slug>.md`/`log.md`/
  `captures.md` would be structurally invisible to `list_known_customers()`,
  `vault_indexing`, and search unless a task explicitly extends that scan
  (or an equivalent) to recurse into this new shape. This is a real,
  load-bearing consequence the decomposer must turn into an explicit task
  under `T04`/`T05`, not an incidental side effect.
- **`REQ-SB-55`/`REQ-SB-56`/`REQ-SB-57` inherit this data model as
  settled** — they should call the primitives this ADR establishes, not
  re-derive path-resolution or write-primitive shape themselves.
- **Does not reopen `ADR-004`.** `ADR-004`'s rule (`customer` is
  frontmatter/tag only for real, multidimensional content notes — Emails/
  Files/Notifications, now Threads/Meetings) is unchanged and unedited;
  this ADR only extends the already-established, separate carve-out
  (first used for the single-file Customer hub note, `REQ-SB-14`) that a
  `kind` folder MAY hold the hub/synthesis entities of that kind
  themselves — now one level deeper for Project nested inside its own
  Customer directory, by explicit operator confirmation, not by silent
  default.

---

## ADR-043: Email Capture & Threading Pipeline (`REQ-SB-55`) — the first concrete Pipeline built under `ADR-041`'s model; Fetch stays a pre-graph batch step, the compiled DAG runs once per email; mid-pipeline human approval is a flat-JSON Pending-Approval-payload deferred write, never a LangGraph checkpointer suspension; one Agent-tier identity represents the whole Pipeline, its Jobs stay tier-less — extends `ADR-041`, `ADR-021`'s independent-of-working-mode approval precedent, and `ADR-042`'s Thread/OKF primitives; does not reopen any of them

**Status:** Superseded by ADR-051 (points 1 and 3's live-execution/topology
halves only — `process_staged_email` no longer executes this Decision's own
compiled `StateGraph`; the module's physical location, every Job's own
function signature/business logic, the flat-JSON Pending-Approval deferred-
write shape (point 4), approval gating (point 5), and the single Agent-tier
identity (point 6) all remain Accepted, unreopened)
**Date:** 2026-08-16

**Context:** `ADR-041` adopted the Agent/Pipeline/Job/Hub taxonomy
directionally, explicitly deferring: (a) the DAG's own persisted data
model, (b) the checkpointer's own durability backend for a suspended
Supervised-stage-pending pipeline, (c) whether/how a Job ever earns its
own Agent-like surface — and explicitly sequenced the next real work:
"the next real work is a single, concrete Pipeline... most likely the
Email capture flow... Only once that concrete pipeline is real and its
actual needs are known does [the Builder] get scoped and built." `REQ-SB-55`
is exactly that concrete Pipeline — replacing the monolithic
`classify_recent_emails` Worker with a real `Fetch`→`Classify`→
`Thread-Match/Merge`→`Route-to-Project` chain plus two branch Jobs
(`Summarize-Attachment`, `Detect-Recurring-Pattern`), built on `ADR-041`
point 5's confirmed LangGraph execution engine.

Two of this story's own confirmed approval-gating requirements (Scenario
3/4: `Route-to-Project` always creates a Pending Approval, but a later
message in an already-routed conversation never re-triggers one; Scenario
5: `Detect-Recurring-Pattern` always creates its own Pending Approval,
proposing — never building — a new Pipeline) are genuinely mid-DAG
human-approval points — exactly the shape `ADR-041`'s own Context named
("real mid-pipeline suspension for human approval") as a plausible reason
to widen LangGraph's scope in the first place. Whether that suspension
needs LangGraph's own checkpointer (`MemorySaver`/`SqliteSaver`) or can
reuse this codebase's already-`Accepted`, already-shipped flat-JSON
Pending Approval mechanism (`ADR-018`; `ADR-021` point 3's Tier-2 override;
the now-superseded but design-precedent-worthy `capture_pipeline.py`'s own
`pipeline_resume` payload convention from `ADR-040`) is exactly the open
question this ADR resolves, concretely, for this one Pipeline.

`REQ-SB-55`'s own Constraint ("No second, independent Compass/
classification call chain — this is an extension of the existing
`Fetch`→`Classify` shape... not a parallel pipeline") and the operator's
own reusability framing for `Detect-Recurring-Pattern` ("I am trying to
build a reusable system here, not just a one-time code") both push toward
keeping each Job's real business logic as plain, LangGraph-ignorant
functions, never logic tangled into graph-node closures — this also keeps
`Thread-Match/Merge`/`Route-to-Project` cleanly consultable by `REQ-SB-63`'s
own future generalized Vault Filing Expert consult call (raised directly
this pass, not built here), without this story needing to anticipate that
integration's shape.

**Decision:**

1. **Module layout — a new `app/business/pipelines/` subpackage is this
   codebase's first home for a Pipeline's own DAG assembly, kept separate
   from each capture type's own business-logic module.**
   `app/business/pipelines/email_capture_pipeline.py` owns exactly: the
   `StateGraph` construction/compile, a typed pipeline state (the data
   threaded between nodes), and the public entry point
   `run_email_capture_pipeline(limit: int = 10) -> list[dict]` — the
   function `run_capture_for_agent`/`run_capture_and_record_completion`
   call for the new Agent-tier identity (point 6) that replaces
   `email-capture`. It never imports `outlook_com`/`compass_client`
   directly — every node is a thin callable wrapping a PLAIN function
   living in `email_classification.py` (`Fetch` reuses
   `outlook_com.list_recent_mail` unchanged; `Classify` extends the
   existing `compass_client.classify_email` call with two new outcomes;
   `Thread-Match/Merge`, `Route-to-Project`, `Summarize-Attachment`, and
   `Detect-Recurring-Pattern` are new plain functions, each independently
   callable/testable outside any LangGraph context, taking/returning
   ordinary Python data — never a graph-state dict). This is the concrete
   resolution of `ADR-041`'s own left-open "DAG's own persisted data
   model" question, scoped to what this one Pipeline actually needs: the
   DAG topology itself is CODE (a `StateGraph` built directly in
   `email_capture_pipeline.py`), not yet a persisted, user-editable
   definition — matching `ADR-041`'s own sequencing note that the Builder
   (and whatever data model it needs) comes only after a real, hand-built
   Pipeline exists. Future Pipelines (Meeting-capture's own eventual
   migration, `REQ-SB-56`; To-Do) get their own sibling module in this
   same subpackage, not a forced-generic shared engine invented ahead of a
   second real example.
2. **`Fetch` is a pre-graph, per-tick batch step — the compiled
   `StateGraph` represents `Classify`→`Thread-Match/Merge`→
   `Route-to-Project` (plus the two branch Jobs), run ONCE PER FETCHED
   EMAIL.** Mirrors `classify_recent_emails`'s existing per-email loop
   shape and this story's own Non-Goals ("this pipeline runs in-process,
   in one atomic pass per email... mirroring `REQ-SB-53-US-01`'s own
   equivalent, now-superseded constraint") — no persisted queue/staging
   between `Fetch` and the rest of the graph, and no cross-email graph
   state. `list_recent_mail`'s own already-processed-id dedup
   (`already_processed`/`mark_email_processed`) stays exactly where it is
   today, in the per-tick loop, outside the graph.
3. **Forking/merging, concretely:** `Classify` is the fork point. Its
   output conditionally routes to (a) `thread_match_merge`
   unconditionally (every classified email either starts or updates
   exactly one Thread), (b) `summarize_attachment` in parallel, once per
   real attachment, when the email has any — its output (the dated
   sub-entries) is threaded back into `thread_match_merge`'s own input (a
   LangGraph fan-in: `thread_match_merge` runs only once
   `summarize_attachment`'s branch, if triggered, has completed, so the
   Attachments section and the regenerated Summary land in the same
   pass), and (c) `detect_recurring_pattern` in parallel, independently,
   when `Classify`'s new recurring-candidate outcome fires — this branch
   never feeds back into `thread_match_merge`; it terminates on its own
   once it creates its own Pending Approval. `thread_match_merge`
   conditionally routes to `route_to_project` only when this pass created
   a brand-new Thread (first message in the conversation); an update to
   an already-existing Thread routes straight to the graph's end for this
   item — the concrete mechanism satisfying Scenario 4 (no re-routing/
   re-approval on a later message).
4. **Mid-pipeline human approval is a flat-JSON Pending-Approval-payload
   deferred write, never a LangGraph checkpointer suspension — resolving
   `ADR-041`'s own open "checkpointer durability" question for this
   Pipeline: it is not needed.** `route_to_project` and
   `detect_recurring_pattern` each run their own graph branch to a clean,
   ordinary completion on every single invocation — never `interrupt()`,
   never a suspended/checkpointed graph state. Each creates a Pending
   Approval (`pending_approval_registry.create_pending_approval`) whose
   `payload` carries everything needed to finish the deferred write (the
   Thread's own path plus the guessed/candidate Project or new-Project
   proposal; the seed content for the Agent Creation Wizard pre-fill),
   then the graph run for that item ends. The actual "finish the
   routing" / "hand off to the wizard" side effect on Approve is
   dispatched the same way `ADR-021` point 5's Vault Filing Expert
   Tier-2 proposal and the now-superseded `capture_pipeline.py`'s own
   `pipeline_resume` convention already do: two new entries in
   `pending_approvals_router.py`'s existing `_APPROVAL_HANDLERS`
   dispatch table (e.g. `finalize_thread_project_routing`,
   `finalize_recurring_pipeline_proposal`), each a plain function living
   alongside the rest of this Pipeline's own business logic, never a
   graph resume. This sidesteps `MemorySaver`/`SqliteSaver` and any
   cross-restart durability question entirely — the SAME already-
   `Accepted`, already-shipped flat-JSON mechanism this codebase already
   trusts for exactly this "propose now, commit later, survive a restart
   in between" shape.
5. **Approval gating composes with, rather than replaces, the Pipeline's
   own top-level working-mode gate — applying `ADR-021`'s "independent of
   the agent's own working mode" precedent a second time.** Exactly one
   working-mode check gates the whole per-tick Pipeline run (Autonomous/
   Manual/Supervised), evaluated once against the single new Agent-tier
   identity (point 6) — mirroring today's existing single
   `working_mode_registry.get_agent_working_mode("email-capture")` check
   in `run_capture_and_record_completion`, **not** the now-superseded
   `capture_pipeline.py`'s own rejected per-stage 4-gate shape (that
   design belonged to `ADR-040`'s fixed 4-Agent-per-type shape, itself
   superseded by `ADR-041`). Independently, and regardless of that
   top-level gate's own resolution (even when Autonomous), `route_to_project`
   and `detect_recurring_pattern` ALWAYS create their own Pending
   Approval — the same unconditional-regardless-of-working-mode shape
   `ADR-021`'s Tier-2 override already established, for a structurally
   analogous reason (a decision big enough to always warrant a human
   look).
6. **One new Agent-tier identity replaces `email-capture` 1:1 in
   `agent_registry.py`'s `_SEED_AGENTS`** (`type: "worker"`, matching the
   retired entry's own type so every existing type-keyed piece of code —
   ring placement, Section coloring, `background_agent_registry.py`'s
   literal exception set — needs zero changes, per this story's own Notes'
   "agent-count-agnostic" precedent) — this is the single addressable
   surface (chat/history/Working Mode/Map node/Pending-Approval
   `agent_id`) representing the whole Pipeline. None of the six Jobs
   (`Fetch`/`Classify`/`Thread-Match/Merge`/`Route-to-Project`/
   `Summarize-Attachment`/`Detect-Recurring-Pattern`) get their own
   `agent_registry` entry, Map node, chat surface, or Working Mode — the
   Job-tier default `ADR-041` already defines, resolving `ADR-041`'s own
   open "whether/how a Job earns its own Agent-like surface" question for
   this Pipeline concretely: it doesn't, none of its Jobs do. Satisfies
   Scenario 8 (`email-capture` no longer appears as its own agent) by
   direct construction.
7. **Thread's own baseline frontmatter family (`ADR-042` point 5) gains
   additive keys, extended rather than reopened** — `ADR-042`'s own
   baseline key set was explicitly left non-exhaustive: `customer`
   (written by `Thread-Match/Merge`, mirroring Email's old per-note
   `customer` field) and `project` (absent on a newly created Thread;
   written only once `Route-to-Project`'s Pending Approval resolves).
   This pass also explicitly claims ownership — flagged open by the
   already-recorded `REQ-SB-56` architecture section — of the two Thread
   fields that story's own fallback-linking heuristic needs
   (`participants`, `last_message_at`): `Thread-Match/Merge` is their
   natural writer, since it is the only code path that touches every
   Thread's frontmatter on every message; both are ordinary additive
   scalar/list-of-string values, no new round-trip workaround needed.

**Consequences:**

- New `vault_writer.py` primitive: a header-SCOPED body append (not just
  `replace_body_section`'s full-region replace) — `## Transcript` and the
  new `## Attachments` section are both independently growing, and only
  one of a note's sections can be "physically last" for the existing
  EOF-blind `append_person_note_update_line` to correctly target; a
  natural generalization reusing `replace_body_section`'s own header/
  next-header location logic (insert just before the region's own end,
  rather than replacing it) resolves this without inventing a new
  mechanism family.
- New `vault_writer.py` primitive: an enumeration of a Customer's own
  `projects/*/` subdirectories and each one's `status`, for
  `Route-to-Project`'s "currently open Projects" guess — a mechanical
  extension of `list_known_customers()`'s own frontmatter-scan shape,
  bounded to one customer's own projects subtree.
- `customer_hub_linking.ensure_hub_note_and_link`'s inline-body-wikilink
  half is NOT reused by `Thread-Match/Merge` — only
  `ensure_customer_hub_note` (ensures the Customer's OKF directory
  skeleton exists) is called; the inline `**Customer:** [[Hub]]`
  wikilink was Email's own per-note linking convention, superseded by the
  OKF concept file's own `sources:` provenance field, populated at
  synthesis time (`REQ-SB-57`, out of this story's scope) —
  `Thread-Match/Merge` does not itself write `sources:`.
- `email_classification.py`'s old `record_conversation_note`/
  `conversation_index.json` and `find_related_note_stems`/
  `## Related Emails` mechanism become dead code for the email path once
  this Pipeline ships (a `conversation_id`-scoped Thread already IS "the
  related emails, merged") — explicitly NOT deleted by this ADR (other
  capture types may still reference the shared file; confirming and
  retiring dead code is a coder-level task-scoping decision, not decided
  here).
- Every real `email-capture`-referencing file this retirement touches
  (`agent_registry.py`, `background_agent_registry.py`, `skill_tools.py`,
  `skill_registry.py`, `agent_schedule_registry.py`, `agents_router.py`,
  `demo_taxonomy.py`, `email_classification.py` itself — confirmed by
  direct search this pass) is a real, multi-file surface; the
  decomposer's own retirement task must enumerate all of them explicitly,
  not assume `agent_registry.py` alone.
- This ADR does not decide the Builder (`ADR-041` point 6) — it stays
  deferred, now genuinely closer (one real Pipeline exists), per
  `ADR-041`'s own sequencing note.

**Alternatives Considered:**

- **Keep `classify_recent_emails` as one monolithic function, add the new
  Thread/Route/branch logic as more inline steps inside it (no LangGraph,
  no new subpackage).** Rejected — directly contradicts `ADR-041`'s own
  explicit decision (Pipeline = LangGraph-compiled DAG) and its
  sequencing note naming Email capture as the intended first concrete
  build; would also make the genuine fork/merge shape (attachment
  summarization merging back before Thread regeneration; the independent
  recurring-pattern branch) far harder to reason about and re-test in
  isolation than named graph nodes.
- **Use LangGraph's own checkpointer (`SqliteSaver`) for genuine mid-graph
  `interrupt()`-based suspension at `Route-to-Project`/
  `Detect-Recurring-Pattern`, resuming the exact graph state on
  Approve.** Considered — this is the literal mechanism `ADR-041`'s own
  Context flagged as LangGraph's plausible payoff for human-approval
  gating. Rejected for this Pipeline specifically: it would be this
  project's first departure from flat-JSON `.second-brain/` persistence
  (`ADR-041`'s own Consequences already named this as a real, unresolved
  cost) for zero functional gain over the already-shipped, already-trusted
  Pending-Approval-payload mechanism this exact "propose now, commit
  later" shape already solves correctly (proven live across the Vault
  Filing Expert Tier-2 flow and the Skill-approval dispatch table).
  Revisit only if a future Pipeline's own approval step genuinely needs
  to resume mid-DAG state too large/complex to fit in a Pending
  Approval's own JSON payload.
- **Per-stage working-mode gating (4+ separate gates, one per Job),
  mirroring the now-superseded `capture_pipeline.py` design.** Rejected —
  that design belonged to `ADR-040`'s fixed 4-visible-Agent-per-type
  shape, which `ADR-041` itself superseded specifically because pipeline
  stages don't deserve independent Agent-level identity; one top-level
  gate plus two independent, always-fire Pending-Approval points
  (mirroring `ADR-021`'s own precedent) is simpler and matches the Job
  tier's own "no independent Working Mode" default.
- **A new `agent_registry` `type: "pipeline"` value, distinct from
  worker/producer/expert.** Considered, not chosen — no locked AC or
  existing Map/Section-coloring code needs a new type value to render
  correctly; introducing one adds a genuinely new taxonomy axis value
  with zero behavioral payoff this story needs, contradicting the
  story's own "zero bespoke code" Map-parity Note.

---

## ADR-044: A Job gains exactly one narrow, addressable surface — its own Settings view (Prompt + Guardrails), reachable by clicking its own Agents Map node — via a new, dedicated `/agents/{agent_id}/jobs/{job_id}/settings` endpoint pair and a genuinely separate, minimal frontend shell; never by widening `agents_router.py`'s Agent-detail resolution or `AgentDetailPanel.tsx`'s shared tab machinery. Resolves `ADR-041`'s own deferred "whether/how a Job earns its own surface" Consequence, for Settings specifically; narrows `ADR-043` point 6 to one explicit, bounded exception — does not reopen it otherwise

**Status:** Accepted
**Date:** 2026-08-16

**Context:** `REQ-SB-66` asks that every real Job (the Email Capture
Pipeline's own six — `classify`, `summarize_attachment`,
`detect_recurring_pattern`, `thread_match_merge`, `route_to_project`,
`consult_librarian`, per `email_capture_pipeline.get_job_tree()`) become
individually clickable on the Agents Map, opening a real, populated
Settings-only detail view showing an editable Prompt (where a real LLM
call site exists) and a structure-only Guardrails field — the operator's
own words: "Jobs we don't need to chat with, I need to have the prompt
that runs the agent to be in the Settings so I can manage it later." This
is a genuine, material narrowing of two already-`Accepted` decisions, not
a routine feature addition:

- `ADR-041` point 1 defines the Job tier as explicitly NOT a full Agent
  identity by default ("no guaranteed own chat thread, own Map node, or
  own Working Mode setting, unless a future pass decides a specific
  Job-level surface is worth exposing") and its own Consequences list,
  as an explicitly deferred open question, "whether/how a Job earns its
  own Agents Map presence, chat surface, or Working Mode in specific
  cases." `REQ-SB-65-US-01` already answered the Map-PRESENCE half of
  that question (a Job becomes visible, still fully non-clickable). This
  story is the first to answer the SURFACE half — this ADR is that
  answer.
- `ADR-043` point 6 ("Jobs stay non-addressable in every respect") and
  the frontend's own current, real click-handling code
  (`AgentsMapCanvas.tsx`'s uniform `onSelect={onSelectAgent}` →
  `AgentDetailPanel` → `GET /agents/{agent_id}` → `agent_registry.
  get_agent(agent_id)` → `None` for any Job id → 404 → an empty,
  unpopulated panel shell, confirmed by direct reading this pass) is the
  concrete mechanism this story asks to change for exactly one facet
  (Settings), while leaving chat/history/independent Working Mode/
  Schedule/Pending-Approval `agent_id`/Skills grant untouched.

Structurally, this mirrors `REQ-SB-65-US-01`'s own Option A/B
data-source choice for the Job Tree Visualization (`architecture.md` →
"Pipeline Job Tree Visualization") almost exactly — same two shapes were
offered again in this story's own `## Notes` — but is NOT a mechanical
repeat of that decision for two confirmed, material reasons found by
direct reading this pass, not assumed:

1. That prior decision was pure READ, pure visibility — a Job never
   became clickable, addressable, or editable. This decision makes a Job
   clickable AND its Settings editable AND persisted (`agent_prompts.
   json`, keyed by `job_id`, uniformly with real Agent ids) — a strictly
   bigger boundary crossing than Job Tree Visualization's own "shape
   becomes visible, addressability doesn't change at all."
2. `AgentDetailPanel.tsx`'s real, current `TABS` constant
   (`['overview', 'chat', 'history', 'settings', 'schedule', 'visual']`)
   is FIXED for every real Agent type today — the only existing per-Type
   variance is ADDITIVE (`'gaps'` appended only for `type === 'expert'`).
   There is no existing tab-REMOVAL mechanism anywhere in this component
   to reuse for a Job's own "Settings only, no Chat/History/Schedule/
   Visual" bar (Scenario 6/7) — confirmed by direct reading, not assumed.
   The story's own Option B framing ("the same way it already varies
   tabs... today") does not hold up against the real, current file; this
   is a correction, disclosed here rather than silently carried forward.

**Decision:**

1. **A Job gains exactly one narrow, addressable surface: a Settings-only
   view (Prompt + Guardrails only), reachable by clicking its own Map
   node.** This resolves `ADR-041`'s own deferred "whether/how a Job
   earns its own surface" Consequence, for Settings specifically — and
   narrows, does not reopen, `ADR-043` point 6: every OTHER facet (Chat,
   History, independent Working Mode, Schedule, Pending-Approval
   `agent_id`, Skills grant) stays exactly as `ADR-043` point 6 already
   established, fully intact, unchanged by this story.
2. **New, dedicated backend resource — `GET`/`PATCH
   /agents/{agent_id}/jobs/{job_id}/settings`, added to the existing
   `agents_router.py`** — never a bare top-level `/jobs/{job_id}`
   resource, and never a widening of `GET /agents/{agent_id}` or
   `agent_registry.get_agent()` itself. Nesting under the owning
   Pipeline's own already-real Agent-tier id mirrors
   `REQ-SB-65-US-01`'s own `/agents/{agent_id}/jobs` sub-resource
   convention and its own "no bare top-level `/pipelines` resource until
   a second real Pipeline exists" reasoning, applied a second time for
   the identical reason: a bare `job_id` (e.g. `"classify"`) is not
   guaranteed globally unique once a second real Pipeline exists: scoping
   under the owning Pipeline's own id is the disambiguation this
   codebase already established, at zero extra cost. `agent_id` in the
   path is used only to confirm the Job genuinely belongs to that
   Pipeline (via `email_capture_pipeline.get_job_tree()`, the same
   already-real function `GET /agents/{agent_id}/jobs` already calls) —
   never as `agent_prompts.json`'s own storage key.
   - `GET` response: `{"id", "name", "prompt": str | None, "guardrails":
     str}`. `prompt` is the key omitted for a Job with no real runtime
     call site of its own (`thread_match_merge`, `detect_recurring_
     pattern` — Scenario 10, `ESC-039` Resolved) — a small, explicitly
     disclosed, hand-maintained 2-item exclusion set, checked at this
     endpoint (see Alternatives — this is NOT the same class of
     "never hardcode" violation `REQ-SB-65-US-01` itself already
     rejected for the Job TREE structure; "does this Job's own function
     call Compass" is a fact about `email_classification.py`'s own real
     code, not a property `_GRAPH.get_graph()`'s introspection can ever
     expose). `guardrails` is always present (`""` default, per
     `agent_prompts.json`'s own additive-layering shape, Decision 3 in
     the parent story).
   - `PATCH` body: `{"prompt"?: str, "guardrails"?: str}` — writes
     directly into `agent_prompts.json` under the `job_id`'s own key,
     via the same `agent_prompts.py` module/functions Agent ids use
     (Scenario 8/9's own "no special-casing between the two" bar).
3. **Frontend: a new, small, standalone Settings-only component — NOT a
   widening of `AgentDetailPanel.tsx`'s own tab machinery.** Rejected for
   the two reasons named in Context above (tier-boundary blurring across
   every `AgentDetail`-typed consumer; the newly-found absence of any
   tab-removal mechanism). `AgentsMapPage.tsx` already fetches the real
   Job-id list on every load (`fetchAgentJobs(EMAIL_CAPTURE_PIPELINE_
   AGENT_ID)`, `REQ-SB-65-US-01-T02`) for `pipelineJobTreeAdapter.ts`'s
   own splice — this story reuses that SAME already-fetched list (no new
   fetch) to know, client-side, whether `selectedAgentId` is a real Job
   id or a real Agent id, and branches which panel component to mount in
   its own already-established `{selectedAgentId && <.../>}` conditional-
   mount slot: `AgentDetailPanel` for a real Agent id (unchanged), a new
   `JobSettingsPanel`-equivalent component for a known Job id.
   `AgentDetailPanel.tsx` itself is untouched by this story.
4. **`agent_registry.py` stays untouched** (the parent story's own
   Constraint, reconfirmed here as architecturally correct, not merely
   assumed) — consistent with every prior Job-tier decision
   (`ADR-043` point 6, `REQ-SB-65-US-01`'s own Option A).

**Alternatives Considered:**

- **Option B — widen `agents_router.py::get_agent`/`AgentDetail.type` to
  recognize a Job id (via `email_capture_pipeline.get_job_tree()`) and
  return an `AgentDetail`-compatible shape, reusing `AgentDetailPanel.
  tsx`'s existing tab-filtering.** Rejected. Would require every
  downstream `AgentDetail`-typed consumer (chat handlers, schedule/
  skills-tree fetchers, the Pending-Approval history poller, the Visual
  Picker, the Working-Mode PATCH path) to defensively distinguish "a real
  Agent" from "a Job wearing an Agent's registry shape" — the exact
  structural blurring `ADR-041`/`ADR-043` built the two-tier split to
  avoid, and the identical reasoning `architecture.md`'s own "Pipeline
  Job Tree Visualization" section already recorded rejecting this same
  shape for the (much narrower, read-only) Job Tree question. This
  decision's own lift is heavier still: that prior story never needed
  `AgentDetailPanel` to structurally HIDE any of its own existing tabs;
  this one does, and no such removal mechanism exists to reuse (Context,
  point 2, above) — Option B here would mean building new tab-suppression
  machinery inside an already-large, general-purpose shared component,
  not reusing an established pattern.
- **A bare top-level `/jobs/{job_id}/settings` resource (no owning-Agent
  scoping in the path).** Rejected — mirrors `REQ-SB-65-US-01`'s own
  already-recorded rejection of a bare top-level `/pipelines` resource
  ("no second real Pipeline exists yet to generalize a shared resource
  shape toward"); nesting under the owning Pipeline's own already-real
  `agent_id` costs nothing today and removes a real future id-collision
  risk (two different Pipelines each naming a Job `"classify"`) entirely.
- **Resolving the "has a real call site" Prompt-omission question
  generically/structurally** (e.g. probing `email_classification.py` at
  runtime for whether a given Job function calls `compass_client`).
  Rejected — no such introspection exists or is warranted for a fixed,
  small, already-fully-enumerated 6-Job set; a disclosed, hand-maintained
  2-item exclusion set is the honest, proportionate mechanism, matching
  this project's own repeated "don't build generic machinery for a still-
  small, fully-known set" discipline (`ADR-011` point 1's identical
  reasoning for keyword-matching over NLU, applied a further time).
- **Returning the resolved EFFECTIVE prompt text (falling back to each
  call site's own hardcoded default string) from the new `GET` endpoint,
  rather than the stored override only.** Considered, deliberately left
  as decomposer/coder-level UX latitude, not decided here — the
  endpoint's own contract (store-and-return `agent_prompts.json`'s own
  already-locked shape, the parent story's own Decision 2) does not
  require it either way, and resolving it here would give this endpoint
  direct string-literal knowledge of every scattered hardcoded default
  across `compass_client.py`/`vault_filing_methodology.py`/`state.py` — a
  coupling no Scenario actually asks for.

**Consequences:**

- A second real Pipeline (`REQ-SB-56`/`REQ-SB-57`) will need the
  identical `/agents/{agent_id}/jobs/{job_id}/settings` treatment once it
  exists — the route shape already generalizes (any Pipeline's own
  Agent-tier id + any of its own real Job ids); no redesign anticipated,
  mirrors `get_jobs`'s own already-generic-but-single-populated-caller
  shape (`REQ-SB-65-US-01`).
- The 2-item Prompt-omission set (`thread_match_merge`, `detect_
  recurring_pattern`) is a disclosed, hand-maintained fact, deliberately
  not self-healing — if a future story gives either Job a real LLM call
  site, this endpoint's own small exclusion check must be updated by
  hand.
- The new Settings-only frontend component's own visual design
  deliberately reuses the existing Settings `kv-list` idiom directly, per
  the parent story's own operator-directed "no `/design` pass" resolution
  — this ADR decides architecture/data-shape/addressability only, not
  visual layout.
- Any FUTURE story proposing a Job gain a SECOND kind of narrow surface
  (e.g. its own Run History) should reopen this exact question again, not
  assume this ADR's Settings-only precedent silently extends to it — this
  ADR is scoped to Settings (Prompt + Guardrails) alone, per Decision 1.
- The additive Prompt-override storage mechanism itself
  (`app/business/agent_prompts.py` + `.second-brain/agent_prompts.json`,
  composed alongside `agent_registry.py`, never inside it) needs no new
  ADR of its own — it is a further, mechanical application of `ADR-011`
  point 2/`ADR-030`'s already-`Accepted` "identity stays hardcoded,
  mutable state lives separately" pattern, the same shape
  `agent_keywords.json`/`agent_scopes.json`/`agent_working_modes.json`
  already established repeatedly. Only the Job-Settings-ADDRESSABILITY
  question (Decision 1, above) crossed a boundary `ADR-041`/`ADR-043`
  had not already settled.

---

## ADR-045: Non-blocking manual capture dispatch closes ADR-037's own unachieved "every real trigger source" goal — `agents_router.py`'s manual `run_capture_now` dispatch (button + chat) is rerouted through `agent_schedule_registry.dispatch_with_shared_lock` instead of calling `skill_registry.invoke_skill` directly, joining the shared Outlook-COM lock and gaining `asyncio.to_thread` for free; a new sibling `.second-brain/job_run_state.json` store, read fresh via the existing `GET /system-health`, gives the three covered capture jobs a real running/duration/outcome record — extends `ADR-037`, `ADR-011` point 2/`ADR-030`'s sibling-store pattern, and `REQ-SB-31-US-01`'s recompute-fresh-on-refresh convention; reopens none of them

**Status:** Accepted
**Date:** 2026-08-17

**Context:** `REQ-SB-68-US-01` was raised directly off a real 2026-08-17
incident: a manually-triggered "Run Capture Now" click froze the entire
backend (confirmed live — a concurrent `GET /agents` returned nothing
until the capture run finished) for the full duration of a real, slow
Outlook-COM-plus-Compass capture pass, with zero visibility into
whether it was running, stuck, or erroring.

The story's own analyst pass (`## Context`) grounded the bug in
`agents_router.py::_execute_action`'s `_ACTION_HANDLERS` dispatch table,
citing its direct, un-awaited `handler()` call as the blocking call site,
and contrasted it with `capture_scheduler.py::run_capture_if_idle`'s
already-`asyncio.to_thread`-wrapped, non-blocking shape. **Direct
re-reading of the REAL current `agents_router.py`, `skill_tools.py`, and
`skill_registry.py` this pass found this grounding is materially wrong
about WHICH function is actually reached** (the underlying diagnosis —
"the manual trigger blocks the event loop" — is correct; the specific
function is not), mirroring this project's own repeated Learnings
pattern ("when a task's own sample disagrees with the REAL current file,
treat the real file as ground truth and correct the plan, not the
other way"):

1. Both of `_ACTION_HANDLERS`'s only two entries
   (`("email-capture-pipeline", "run_capture_now")` and
   `("compass-expert", "build_knowledge")`) are ids that ALSO exist as
   full members of `skill_tools.SKILLS` (added by `REQ-SB-39-US-02`/
   `ADR-029` point 5, migrating these exact 4 formerly-hardcoded mutating
   Action ids into Skills — `run_capture_now`/`pause_schedule`/
   `rebuild_person_note`/`build_knowledge`). Every real call site that
   could reach `_execute_action`/`_ACTION_HANDLERS`
   (`agents_router.py::trigger_action`, `agents_router.py::chat`,
   `pending_approvals_router.py::approve_pending_approval`) checks
   `action_id in skill_tools.SKILLS` FIRST and branches away to the
   Skills path whenever true — which is always true for both of
   `_ACTION_HANDLERS`'s own two entries. Confirmed by direct reading of
   all three call sites: **`_execute_action`'s `_ACTION_HANDLERS` lookup
   for these two ids is unreachable dead code today** — a real,
   previously-undisclosed finding, not merely a naming/comment
   inconsistency. `skill_tools.py::build_knowledge` is a separate, real,
   already-working implementation, confirming the old
   `agents_router.py::_run_build_knowledge`/`_execute_async_action` pair
   is equally dead.
2. The REAL manual-trigger dispatch path for
   `POST /agents/{agent_id}/actions/run_capture_now` (and the identical
   chat-keyword-matched trigger) is:
   `agents_router.py::trigger_action`/`chat` → `_invoke_capability`
   (plain `def`, called with no `await`/`asyncio.to_thread`) →
   `skill_registry.invoke_skill` (plain `def`) → `_dispatch_skill`
   (plain `def`) → `skill_tools.run_capture_now(agent_id)` →
   `email_classification.run_capture_and_record_completion()` (real,
   slow, blocking Outlook COM + Compass calls). This chain is fully
   synchronous end-to-end with no thread offload anywhere in it — this
   is the REAL bug, confirmed against the REAL current files, not the
   `_execute_action` path the story's own Context named.
3. `agent_schedule_registry.py::dispatch_with_shared_lock` (`ADR-037`
   point 1) already exists, is already `Accepted`, and already does
   exactly what this bug needs: `await asyncio.to_thread(skill_registry.
   invoke_skill, ...)` under the shared lock, skip-not-queue-not-overlap
   on contention. `ADR-037`'s own point 1 text says this is meant to be
   "the ONE function every real trigger source for a scheduled/on-demand
   capability now passes through" — but the actual `REQ-SB-47-US-01`
   build only wired it into the NEW scheduled-tick callback and the NEW
   `agent_schedules_router.py`'s own `run-now` endpoint, never into
   `agents_router.py`'s own pre-existing manual action/chat dispatch
   surface, leaving this exact gap open. This ADR closes it.
4. `agent_schedule_registry.py` is also `ADR-037`'s own canonical home
   for the shared dispatch lock and is a `business`-layer module
   `agents_router.py` (api layer) may call directly (`ADR-003`'s
   `api → business` edge, already used throughout `agents_router.py`) —
   no new cross-layer edge is introduced.

**Decision:**

1. **`agents_router.py::_invoke_capability` becomes `async def`, and gains
   one new, narrow branch: when `capability_id == "run_capture_now"`, it
   calls `await agent_schedule_registry.dispatch_with_shared_lock(
   agent_id, capability_id, trigger=trigger)` instead of calling
   `skill_registry.invoke_skill(...)` directly.** Every other
   `capability_id` keeps calling `skill_registry.invoke_skill` exactly as
   today, unchanged — this is a single-id routing branch, not a general
   rewrite of `_invoke_capability`. `run_capture_now` is the correct,
   sufficient gate: it is the one and only capability id shared by
   exactly the three covered agents
   (`email-capture-pipeline`/`meeting-capture`/`todo-capture`, per
   `skill_registry._MIGRATION_GRANT_SEED["run_capture_now"]`) and no
   other agent/capability pair — no additional agent_id check is needed.
   `_invoke_capability`'s existing result-shape translation (the
   `"unknown_skill"`/`"refused"`/`"available"` branches) is extended with
   one more case: `result.get("status") == "skipped"` (the shape
   `dispatch_with_shared_lock` returns when the lock is already held) now
   maps to `{"status": "skipped", "message": result["message"]}`,
   preserved verbatim rather than being folded into the generic
   `"available" → "ok"` fallback, which would otherwise mislabel a
   genuine skip as a success. The translated result additionally carries
   `"history_recorded": True` whenever the call was routed through
   `dispatch_with_shared_lock` (i.e., whenever `capability_id ==
   "run_capture_now"`) — `dispatch_with_shared_lock` already records its
   own outcome to history internally (`_record_outcome`, `ADR-037` point
   1); without this flag, `trigger_action`'s/`chat`'s own generic
   post-call `vault_writer.append_agent_history_entry` would write a
   second, duplicate entry for the same run, mirrors the exact
   `"history_recorded"` convention `_run_build_knowledge`/`skill_tools.
   build_knowledge` already established for the identical
   self-recording-handler shape.
2. **Both of `_invoke_capability`'s only two real call sites
   (`trigger_action`, `chat`) — both already `async def` — add `await`
   at their existing, unchanged call-site lines.** No other ripple:
   `_execute_action`/`_ACTION_HANDLERS`/`_invoke_action`/
   `_execute_async_action` are left **fully unchanged, still dead code
   for their only two entries** (Context, point 1) — this ADR does not
   fix, remove, or repurpose them; doing so is out of this story's own
   scope (minimal changes) and is recorded as a disclosed housekeeping
   finding for a future cleanup story, not actioned here.
   `dispatch_with_shared_lock`'s own `trigger` parameter type widens from
   `Literal["scheduled", "direct"]` to `Literal["scheduled", "direct",
   "chat"]` — a trivial, backward-compatible widening (the function
   already just forwards `trigger` to `skill_registry.invoke_skill`,
   whose own `Literal` already includes `"chat"`) needed because
   `agents_router.py::chat`'s own keyword-matched "run capture now"
   trigger is the second, equally-real manual-trigger surface this
   story's own goal ("manually triggering a capture job to never
   freeze... the way it did") covers — not just the literal REST button
   Scenario 1 quotes.
3. **The manual dispatch path now acquires `agent_schedule_registry`'s
   shared dispatch lock — the race-condition risk the story's own
   `## Non-Goals` left open for this ADR to decide is resolved as: yes,
   close it, via the exact mechanism already being adopted for the
   blocking fix, not a new one.** A manual "Run Capture Now" click and a
   concurrent scheduled tick targeting one of the same three covered
   agents now correctly serialize (skip-not-queue-not-overlap, mirroring
   `run_capture_if_idle`'s own Scenario-4 convention) instead of racing
   two real Outlook COM sessions. This was the cheaper, not the harder,
   choice — `dispatch_with_shared_lock` already does both jobs
   (non-blocking dispatch AND locking) in one already-`Accepted`,
   already-proven function; routing through it for the blocking fix and
   then declining to also take the lock would have required deliberately
   re-implementing a parallel non-locked `asyncio.to_thread` wrapper next
   to it for no benefit.
4. **New run-state persistence: a new sibling store,
   `.second-brain/job_run_state.json`, composed via two new pure-I/O
   primitives on `app/data_access/vault_writer.py`
   (`load_job_run_state()`/`save_job_run_state()`), mirroring
   `load_agent_schedules_state()`/`save_agent_schedules_state()`'s exact
   shape (returns `None` if absent; no default content computed in
   `data_access`, `ADR-003`).** Keyed by the same composite
   `"{agent_id}::{capability_id}"` string `agent_schedules.json` already
   uses (`ADR-037` point 3) — reusing an established key shape, not
   inventing a new one. Record shape per key: `{"agent_id",
   "capability_id", "running": bool, "started_at": iso8601 | None,
   "finished_at": iso8601 | None, "last_outcome": "success" | "error" |
   "skipped" | None, "last_error_message": str | None,
   "last_duration_seconds": float | None}`. Two new functions on
   `app/business/agent_schedule_registry.py` (the module `ADR-037`
   already made the canonical home for this exact class of concern —
   composed alongside its existing lock/CRUD/dispatch code, not a new
   module): a start-marker and a finish-marker, called from INSIDE
   `dispatch_with_shared_lock`'s own `async with lock:` block (immediately
   before and after its existing `await asyncio.to_thread(...)` call),
   gated to `capability_id == "run_capture_now"` only — the same
   structural gate Decision 1 uses, keeping run-state tracking scoped to
   exactly the three covered jobs (the story's own Constraint) without a
   hardcoded agent-id list. Duration for an in-flight run is NEVER
   persisted incrementally — a new read accessor,
   `get_job_run_states() -> list[dict]`, computes `now − started_at`
   fresh on every call for any record with `running: True` (`now −
   started_at` at read time, never stored), mirroring `REQ-SB-31-US-01`'s
   own established "recompute fresh on every call, never cached"
   convention for this exact page. A covered job with no record yet
   returns nothing for that key — the accessor (or its `system_health.py`
   caller) omits it rather than fabricating a running/idle/duration/
   outcome value (Scenario 5), and the frontend renders an explicit "no
   runs yet" state for any covered job absent from the response — never
   a blank/broken row (Scenario 7's own "not left broken or empty-looking
   because of the uncovered action" bar, applied one facet over).
5. **New API surface: none — extends the EXISTING `GET /system-health`
   only.** `app/business/system_health.py::get_system_health()` gains a
   new `"scheduling"` key (`agent_schedule_registry.get_job_run_states()`
   composed in, list of the covered jobs' current records), and
   `app/api/system_health_router.py` needs no change (it already returns
   `get_system_health()`'s full dict unmodified). This directly satisfies
   the story's own "run-state should be readable via a real endpoint, not
   just a raw file" directive without adding a second, narrower endpoint
   — `GET /system-health` is already the one real aggregation surface
   for exactly this class of read-only operational signal
   (`REQ-SB-31-US-01`), and only three jobs' worth of data needs exposing.
6. **`.second-brain/last_capture_run.json` (`record_capture_run_completed`/
   `load_last_capture_run`, `ADR-008`-era) is superseded for DISPLAY
   purposes only — left alone for STORAGE purposes.** The new
   `job_run_state.json` record for `email-capture-pipeline`'s own
   `run_capture_now` key is a strict superset of what `last_capture_run.
   json` ever tracked (a single `finished_at` timestamp, aggregate across
   trigger sources, no running/duration/error field). `system_health.
   py::get_system_health()`'s existing `"last_capture_run"` key is
   REMOVED from its response (replaced by the richer `"scheduling"` key);
   `SystemHealthPage.tsx`'s existing `<h2>Last capture run</h2>` + card
   region (lines 148-169 today) is REPLACED outright by the new
   "Scheduling" region at the same position (immediately after the
   "Providers" card) — not left to coexist alongside it, since a smaller,
   strictly-subsumed sliver of the same signal sitting next to the fuller
   one is more confusing, not less. `record_capture_run_completed()`'s
   own call site inside `email_classification.run_capture_and_record_
   completion` (`ADR-008`) and the underlying `.second-brain/
   last_capture_run.json` file itself are left byte-for-byte unchanged —
   removing that write path is not required by any Scenario here, and
   deleting already-`Done`, still-functioning code with no story
   requirement asking for its removal contradicts this project's own
   minimal-changes discipline. A harmless, disclosed redundancy, not a
   defect.
7. **Frontend: `SystemHealthPage.tsx`'s new "Scheduling" section reuses
   the page's own already-established `item-list`/`item-row` visual
   idiom** (the same pattern the "Providers" card immediately above it
   already uses on this exact page) rather than inventing a new layout —
   one row per covered job, each showing running-state, elapsed/most-
   recent duration, and last outcome (success, or the real error message
   on failure), per the story's own operator-directed "no `/design` pass"
   resolution (mirrors `ADR-044`'s own identical "this ADR decides
   architecture/data-shape only, not visual layout" framing).

**Alternatives Considered:**

- **Fix the blocking bug at `_execute_action`/`_ACTION_HANDLERS` instead,
  as the story's own Context originally proposed** (wrap `handler()` in
  `asyncio.to_thread`, make `_execute_action` `async def`, ripple through
  `_invoke_action` and `pending_approvals_router.py`'s Approve dispatch).
  Rejected — this would fix a code path that is never actually reached by
  any real caller for either of `_ACTION_HANDLERS`'s two entries (Context,
  point 1); the real, live-incident-producing call path runs entirely
  through `skill_registry.invoke_skill`/`_dispatch_skill`, untouched by
  that fix. Shipping it would look like a fix, pass no live reproduction
  of the actual bug, and leave the real incident fully reproducible.
- **A brand-new, dedicated `asyncio.to_thread` wrapper inside
  `_invoke_capability` itself, calling `skill_registry.invoke_skill`
  directly, without also routing through `agent_schedule_registry`.**
  Would fix the blocking half only, leaving the race-condition risk
  (Decision 3) unresolved and requiring either a second, separate locking
  mechanism later or accepting the race indefinitely. Rejected in favor
  of the one function that already does both, `ADR-037`'s own
  `dispatch_with_shared_lock` — reuse over reinvention, and it closes
  `ADR-037`'s own stated-but-unachieved "every real trigger source" goal
  in the same stroke.
- **Generalize the non-blocking fix to EVERY `skill_tools.SKILLS` handler**
  (wrap `_dispatch_skill`'s own generic `handler(**call_args)` call in
  `asyncio.to_thread` unconditionally, fixing `build_knowledge`'s own
  identical, currently-live blocking gap for free). Rejected for this
  story's own scope — the story's Constraints explicitly bound run-state
  tracking (and, by the same reasoning, this pass's own blocking fix) to
  the three capture-style jobs already covered by the shared dispatch
  lock, not "every dispatched agent action generally." `build_knowledge`/
  `compass-expert` genuinely shares the same structural gap (confirmed by
  direct reading, `skill_tools.py::build_knowledge`'s own
  `ThreadPoolExecutor(...).submit(asyncio.run, coro).result()` blocks its
  own calling thread exactly the same way, still fully synchronous
  end-to-end through `_dispatch_skill`) — disclosed here as a real,
  known, NOT-fixed-by-this-ADR limitation for a future story to pick up,
  not silently masked or assumed away.
- **Delete/repurpose the now-confirmed-dead `_execute_action`/
  `_ACTION_HANDLERS`/`_run_build_knowledge`/`_execute_async_action` code
  as part of this same pass**, since it was found dead while grounding
  this ADR. Rejected — out of this story's own scope (its own Constraint
  is "only how `run_capture_now` is dispatched changes"); removing dead
  code is a legitimate, separate, low-risk cleanup a human should
  explicitly schedule, not an incidental side effect of a live-incident
  bugfix story. Recorded in Consequences below and flagged to
  `REVIEW-QUEUE.md` so it is not silently lost.
- **A brand-new, dedicated `.second-brain/scheduling_status.json`-style
  store keyed differently from `agent_schedules.json`'s own composite-key
  shape** (e.g. a flat list, or nested per-agent objects). Rejected —
  reusing the exact `"{agent_id}::{capability_id}"` composite-string-key
  convention `agent_schedules.json` already established costs nothing and
  keeps this project's own sibling-`.second-brain/`-store shape uniform,
  mirroring `ADR-011` point 2/`ADR-030`'s already-`Accepted` "identity
  stays hardcoded, mutable state lives separately" pattern one further
  concern over.
- **A dedicated new `GET /agents/{agent_id}/schedules/{capability_id}/
  run-state` endpoint** instead of extending `GET /system-health`.
  Rejected — only three jobs' worth of data ever needs exposing, and the
  Scheduling VIEW this data feeds already lives on the System Health
  page (the story's own Affected Screens); `GET /system-health` is
  already the established single real aggregation surface for exactly
  this class of signal. A narrower per-schedule endpoint remains
  legitimate future work if a consumer other than this page ever needs
  just one job's own state, not assumed or pre-built here.
- **Coexist: keep the existing "Last capture run" region alongside the
  new "Scheduling" region, rather than replacing it.** Considered — the
  story's own Notes explicitly left this open. Rejected: the old
  region's own single data point (`email-capture-pipeline`'s last
  `finished_at`) is now strictly, losslessly contained within the new
  region's own richer per-job data for the same agent; showing both
  would present the same underlying fact twice, at two different levels
  of completeness, on the same page — more confusing than clarifying,
  not a genuinely additional signal.

**Consequences:**

- `agents_router.py::_execute_action`, `_ACTION_HANDLERS`,
  `_invoke_action`'s `_execute_action`-fallthrough branch,
  `_execute_async_action`, and `_run_build_knowledge` remain confirmed
  dead code for their only two real entries after this ADR — a disclosed,
  real housekeeping finding, not actioned here, flagged to
  `REVIEW-QUEUE.md` for a future, separately-scoped cleanup story. Any
  FUTURE story adding a new `_ACTION_HANDLERS` entry must first confirm
  its own action id is NOT also a `skill_tools.SKILLS` member, or it will
  silently inherit this exact same unreachability.
- `build_knowledge`/`compass-expert` keeps its own, already-live,
  structurally identical blocking-dispatch gap (`skill_tools.
  build_knowledge`'s own `ThreadPoolExecutor(...).result()` call) — not
  fixed by this ADR, disclosed as known, scoped explicitly out per this
  story's own three-covered-jobs boundary. A future story extending
  run-state tracking or the non-blocking fix to `build_knowledge` (or any
  other mutating Skill) should read this ADR's own Decision 1/`ADR-037`
  precedent first, rather than re-deriving the mechanism.
- `agent_schedule_registry.py` gains its second `.second-brain/` sibling
  store (`job_run_state.json`, alongside `agent_schedules.json`) and two
  new write call sites inside `dispatch_with_shared_lock`'s own
  lock-held block — a deliberate, narrow extension of `ADR-037`'s already-
  established module boundary, not a new one.
- `GET /system-health`'s response shape changes (drops `"last_capture_
  run"`, gains `"scheduling"`) — any external consumer of that exact key
  (none exist outside `SystemHealthPage.tsx` today, confirmed by direct
  reading) would need to update; disclosed here since this is a
  behavioral change to an already-`Done` story's own response contract,
  not purely additive.
- The manual dispatch fix and the run-state tracking share one single
  choke point (`dispatch_with_shared_lock`) with the scheduled tick —
  this is what makes Scenario 6's "the Scheduling view correctly reflects
  that scheduled run's own running/duration/outcome state, using the
  same mechanism a manually-triggered run's state is shown through" true
  by construction, not by parallel, independently-maintained code paths.

---

## ADR-046: Decoupled Email Pull + Human-Readable, Graph-Connected Thread Notes (`REQ-SB-69`) — `Fetch` is retired from the pre-graph batch step and becomes its own independently-dispatched, incrementally-staged `pull_email` capability, writing to a new vault-local `.second-brain/email_staging/` store; Thread processing becomes a second, Outlook-lock-free `process_staged_email` capability — both under the existing single `email-capture-pipeline` Agent-tier identity, no new Agent/Job surface; Thread filenames become human-readable and collision-safe via a frontmatter-scan lookup (no persisted index); dates split into a machine-parseable/human-readable sibling pair; a new, deterministically-regenerated `## Related` body section carries honest Customer/Person/Project wikilinks — supersedes `ADR-043` points 2 and 7 and `ADR-042` point 5 only; extends `ADR-041`, `ADR-037`, `ADR-045`, and `ADR-042`'s own `replace_body_section`/OKF primitives; reopens nothing else

**Status:** Accepted
**Date:** 2026-08-17

**Context:** `REQ-SB-69-US-01` was raised directly off a real, repeated
2026-08-17 production incident — the shared Outlook-COM dispatch lock
wedged TWICE the same night, even after `REQ-SB-68-US-01`'s own
non-blocking-dispatch fix (`ADR-045`, shipped earlier the same night)
proved the stall lives one layer deeper than dispatch: inside
`run_email_capture_pipeline`'s own single, synchronous, per-tick `Fetch`
call (`outlook_com.list_recent_mail`), which runs BEFORE
`Classify`/`Thread-Match/Merge`/`Route-to-Project` and holds the shared
lock for its entire duration (`ADR-043` point 2's own explicit "no
persisted queue/staging between `Fetch` and the rest of the graph"
design). Direct reading of `list_recent_mail` (`outlook_com.py` lines
216-249) confirms it does real, synchronous, per-item COM work in a loop
— sender resolution via `GetExchangeUser()`, attachment
save-then-read-then-delete, recipient resolution — any one of which can
stall, and did, twice, the second time even with a supposedly-unlimited
Outlook access grant. The operator directed, with full autonomy and no
availability for review tonight: decouple Pull into its own step,
writing to a durable vault-local staging area, so downstream processing
never touches Outlook COM directly and a Pull stall can't block
already-staged work — and explicitly warned that Pull itself may still
be slow or stall mid-loop, so the mechanism must be live-updating,
resumable, and incremental (stage each item as it's fetched, never
buffer until the whole COM loop returns), not merely "make Pull fast."

The story's own analyst pass (`REQ-SB-69-US-01`'s `## Notes`) identified
four concrete mechanism-level questions this ADR resolves, each reopening
a specific point of an already-`Accepted` ADR:

1. **`ADR-043` point 2** ("no persisted queue/staging between `Fetch` and
   the rest of the graph") — this requirement's whole first half asks for
   exactly that staging boundary, for the Email path only (not
   `REQ-SB-53`'s earlier, broader, declined 4-agent Puller/Tagger/
   Linker/Storer redesign, which stays `Parked`).
2. **`ADR-042` point 5** ("Thread path resolved deterministically from
   `conversation_id` alone... no separate lookup index") — broken the
   moment the filename depends on the mutable `last_message_at` + a
   subject-derived name, per this requirement's own human-readable-
   filename ask.
3. **`ADR-043` point 7** (`Thread-Match/Merge` never calls
   `link_note_to_customer_hub`'s inline-wikilink half — only
   `ensure_customer_hub_note`) — reopened by this requirement's real
   `[[wikilink]]` ask for Thread notes specifically.
4. **Whether `Pull` earns its own Agent-tier identity** (`ADR-041` point
   1's Job-tier default vs. `REQ-SB-53-US-01`'s now-`Parked`,
   `ADR-041`-superseded 4-Agent model) — left open by the story.

Direct re-reading of the REAL current code this pass, beyond what the
story's own `## Context` already grounded, found two further
architecturally load-bearing facts:

5. `email_classification.py::route_to_project` captures
   `thread_result["thread_path"]` — a plain path STRING — into its
   Pending Approval's own `payload` at proposal time
   (`create_pending_approval`), and `finalize_thread_project_routing`
   (run later, on Approve, per `ADR-043` point 4's deferred-write shape)
   trusts that captured string directly (`Path(payload["thread_path"])`).
   Once a Thread's filename can change between proposal and approval
   (this requirement's own Scenario 7), that captured string can go
   stale — a real, previously-latent correctness gap this ADR's own
   filename change makes newly reachable, not something `REQ-SB-69`'s own
   Scenarios named explicitly, but a direct, necessary consequence of
   Decision 4 below that this ADR must also resolve.
6. `vault_writer.replace_body_opening_line` (`REQ-SB-67-US-01-T01`)
   already, unconditionally, WHOLESALE-regenerates the Thread note's own
   "opening region" (from the end of frontmatter to the first `## `
   header) on every `thread_match_merge` call. `customer_hub_linking.
   link_note_to_customer_hub`/`people_extraction.link_email_to_person`
   (Email's own existing inline-wikilink primitives, `REQ-SB-14`/
   `BUGFIX-01`) both insert their `**Label:** [[Stem]]` line via
   `insert_body_line_if_missing`, which inserts AT THE SAME position
   `replace_body_opening_line` fully owns and overwrites whole-region on
   every call — reusing those primitives as-is for Threads would mean
   `replace_body_opening_line`'s own next call silently erases whatever
   wikilink line `insert_body_line_if_missing` had just written. This is
   a genuine, previously-undisclosed primitive conflict, found by direct
   reading, not assumed — it rules out the most literal reading of
   reusing Email's own wikilink mechanism unchanged, and is why Decision
   6 below is a new, dedicated, regenerated body section instead.

**Decision:**

1. **New durable, vault-local, incremental staging store — a new,
   dedicated `app/data_access/email_staging.py` module (a data_access
   sibling to `vault_writer.py`, mirroring `upload_storage.py`'s own
   precedent of a dedicated blob-storage module kept separate from
   `vault_writer.py` for a structurally different storage concern), never
   folded into `vault_writer.py` itself.** One directory per staged
   email, `.second-brain/email_staging/<entry_id>/` (`.second-brain/` is
   already vault-local — every existing sibling JSON store,
   `job_run_state.json`/`agent_schedules.json`/etc., already lives under
   `settings.vault_path`, so this satisfies the story's own "durable and
   vault-local, not memory-only" Constraint by construction, reusing the
   established location rather than inventing a new one):
   - `email.json` — the full email dict `outlook_com.list_recent_mail`
     already produces (`id`, `subject`, `sender_name`, `sender_email`,
     `received`, `body`, `conversation_id`, `recipients`), MINUS raw
     attachment bytes, PLUS attachment metadata only (`filename`, `size`,
     a relative path into this same directory's own `attachments/`
     subfolder) — preserving the EXACT shape every downstream Job
     (`classify_captured_email`, `thread_match_merge`,
     `summarize_attachment`, etc.) already consumes, so none of their own
     function bodies need to change (the story's own "every other
     already-verified behavior is preserved unmodified" Constraint).
   - `attachments/<filename>` — raw attachment bytes written to disk
     once, at staging time, never base64-inflated into the JSON record —
     mirrors `ADR-034`'s own `.second-brain/uploads/` blob-on-disk
     precedent for exactly this class of "structured metadata plus a
     real binary payload" data, rather than reusing the `recipients`/
     `attendees`/`generated`/`verified` JSON-encoded-STRING workaround
     (`ADR-042` point 3), which is for small structured VALUES, not
     multi-megabyte binary content.
   - **Not a staging/promotion gate on ingested vault data — a
     pre-note, transient RAW-CONTENT buffer only, mirroring
     `_extract_attachments`'s own existing save-then-delete temp-file
     shape one layer up.** `MEMORY.md`'s own standing constraint (this
     project deliberately does not replicate `agentic-map`'s
     staging→canonical two-tier trust model) is about whether a Thread
     note, once written, requires a SEPARATE human-approval step before
     it counts as real/usable vault content — it does not, and this ADR
     does not add one. A staged email is not yet a note at all; the
     moment it is processed it becomes a real Thread note through the
     SAME already-`Accepted` graph and the SAME already-`Accepted`
     approval gates (`route_to_project`/`detect_recurring_pattern`'s own
     Pending Approvals, unchanged) — no new review/promotion step is
     interposed between "processed" and "usable." This store exists
     solely so a real Outlook-COM stall cannot lose already-fetched
     content, a pipeline-resilience concern, not a content-trust one.
   - Three primitives: `stage_email(email: dict) -> None` (writes one
     email's own directory; called once per successfully-resolved item),
     `list_staged_emails() -> list[dict]` (enumerates every staged
     directory, reconstructing each into the exact `list_recent_mail`
     dict shape, re-reading attachment bytes from their own files),
     `remove_staged_email(entry_id: str) -> None` (deletes a staged
     entry's own directory once its graph run completes successfully —
     mirrors `_extract_attachments`'s own save-read-delete temp-file
     discipline, applied one layer up, so staging never grows
     unboundedly).
2. **`outlook_com.list_recent_mail` gains one new, optional, additive
   parameter: `on_item_fetched: Callable[[dict], None] | None = None`,
   invoked with each item's own dict immediately after it is fully
   resolved (sender/attachments/recipients), inside the existing
   per-item loop, before continuing to the next item — never buffered
   into the function's own returned list first.** This is the concrete
   mechanism satisfying the operator's own "live-updating, resumable,
   incremental... write items to the vault as they're actually fetched"
   steer: even if the SAME call later stalls or raises on a LATER item,
   every item already handed to the callback is already durably staged.
   Every existing caller (the now-legacy `classify_recent_emails`,
   `app/api/email_poc_router.py`'s standalone POC endpoint) passes
   nothing and keeps today's exact buffer-then-return behavior,
   unaffected — this is a strictly additive signature change, never a
   behavior change for an existing caller.
3. **A new business-layer module, `app/business/pipelines/email_pull.py`
   (a new sibling inside `ADR-043` point 1's own `app/business/
   pipelines/` subpackage, not a new top-level module)** — owns
   `pull_and_stage_emails(limit: int = 10) -> dict`, the ONLY function in
   the email path that still imports `outlook_com` (satisfying Scenario
   1's structural check that NONE of `Classify`/`Thread-Match-Merge`/
   `Route-to-Project`/`Summarize-Attachment`/`Detect-Recurring-Pattern`/
   `Consult-Librarian` do). It calls `outlook_com.list_recent_mail(limit=
   limit, on_item_fetched=email_staging.stage_email)`, filtering out any
   id already in `vault_writer.load_processed_email_ids()` OR already
   sitting in staging (a light pre-check, so a Pull re-run against the
   same recent-N window doesn't re-stage a duplicate copy of mail already
   staged-but-not-yet-processed) — `already_processed`/`mark_email_
   processed` itself is UNCHANGED, still consulted a second time, at
   processing time, exactly as `ADR-043` point 2 already established.
   `app/business/pipelines/email_capture_pipeline.py` drops its own
   `outlook_com` import entirely — its own `Fetch`-era docstring
   references are retired; its public entry point (still compiled-graph-
   driven, `Classify`→`Thread-Match/Merge`→`Route-to-Project` plus branch
   Jobs, structurally UNCHANGED from `ADR-043` points 1/3/4) is
   restructured to read its per-item input from `email_staging.
   list_staged_emails()` instead of a `Fetch` call, and to call
   `email_staging.remove_staged_email(entry_id)` alongside its own
   existing `vault_writer.mark_email_processed(entry_id)` call on success
   — on a per-item failure (Scenario 4), NEITHER is called, so the item
   stays staged AND unmarked for a later run to retry, mirroring the
   per-email try/except+continue posture `ADR-043` point 1 already
   established, now spanning the staging boundary too.
4. **Pull and Processing become two independently-dispatchable
   capabilities of the SAME existing `email-capture-pipeline` Agent-tier
   identity — `pull_email` (Outlook-touching, joins the shared
   Outlook-COM dispatch lock exactly like every other real Outlook
   caller, via `agent_schedule_registry.dispatch_with_shared_lock`,
   `ADR-037`/`ADR-045`) and `process_staged_email` (Outlook-free, and
   critically, NEVER acquires the shared Outlook-COM lock — a new,
   separate, lightweight "skip if already running" guard, mirroring
   `dispatch_with_shared_lock`'s own shape but over a NEW, dedicated
   `asyncio.Lock` scoped to email processing alone, not the Outlook
   one).** This is the mechanism that makes Scenario 2 (a stalled Pull
   doesn't block already-staged mail) and Scenario 3 (stalled processing
   doesn't block the next Pull) true BY CONSTRUCTION, not by convention:
   the two capabilities share no lock, so one being stuck structurally
   cannot block the other's own dispatch, regardless of which one is
   slow. `capture_scheduler.py::run_capture_if_idle`'s own hourly/
   app-start composite trigger is restructured to invoke these as two
   separate steps — Pull (bundled with Meeting-capture's and
   Todo-capture's own still-unchanged, still-Outlook-touching legs,
   under ONE shared-lock hold, exactly as today — this ADR does not
   touch Meeting/Todo capture's own triggering at all, out of this
   story's Email-only scope) THEN, as a separate, subsequent,
   lock-independent call, Processing. Both `pull_email` and
   `process_staged_email` also become new `skill_tools.SKILLS` entries
   (`mutates: True`, mirroring `run_capture_now`'s own shape) so they are
   independently schedulable via `agent_schedule_registry`'s already-
   generic per-`(agent_id, capability_id)` schedule mechanism — no new
   Scheduling-view UI row is built for either (the story's own Non-Goal,
   left to a future pass); `run_capture_now` itself is UNCHANGED,
   still the composite email+meeting+todo dispatch it is today, for
   backward-compatible manual/chat-triggered behavior. Run-state
   tracking (`ADR-045`'s `job_run_state.json`/`get_job_run_states()`) is
   extended to cover both new capability ids alongside the existing
   three, for internal observability parity, without any new frontend
   surface.
5. **This directly resolves the story's own fourth open question: `Pull`
   does NOT earn its own Agent-tier identity.** The operator's own words
   ("Have one Agent to Hand the pull of All Emails Separately") are
   satisfied literally — the SAME one `email-capture-pipeline` Agent-tier
   identity now has Pull handled as its own genuinely separate,
   independently-triggerable capability, never a new Agents Map node,
   chat surface, or Working Mode. This does not reopen `ADR-041` point
   1's Job-tier default or `ADR-043` point 6 ("Jobs stay non-addressable
   in every respect") — it extends the ALREADY-established "one
   Agent-tier identity can expose more than one independently-dispatched
   capability" shape `ADR-037`/`ADR-045` already built (multiple
   Skills/capability_ids per agent_id), one capability further; it does
   not give either new capability its own Map node, chat thread, or
   Working Mode.
6. **Thread filename: `<slug(thread_name)>-<date>-<hash8>.md`, mirroring
   `meeting_note_filename_stem`'s own already-shipped `<subject>-<date>-
   <hash-suffix>` scheme exactly, adapted per the story's own Context
   grounding.** `thread_name` is a NEW, additive baseline frontmatter key
   — the FIRST message's own subject, captured ONCE at Thread-creation
   time and never recomputed on a later message (a Thread's own
   descriptive name must stay stable across its life; recomputing it from
   whatever the LATEST message's subject happens to be — "Re: X" vs.
   "Fwd: X — updated" — would make the filename's own name component
   drift unpredictably on every later message, which no Scenario asks
   for and which would make Decision 8's own re-resolution problem
   worse, not better). `date` = `last_message_at[:10]` (the mutable,
   already-existing field). `hash8` = the first 8 hex characters of
   `sha256(conversation_id)` — deliberately hashing `conversation_id`
   ALONE, not `f"{name}|{date}"` the way Meeting does — per the story's
   own Context: this keeps the disambiguator itself stable across
   renames even though the filename's own date component moves on every
   later message (Scenario 7), which hashing the mutable date into the
   suffix would break. `Work/Threads/` stays a flat, dynamically
   discovered `kind` folder — no directory nesting introduced.
7. **`vault_writer.thread_note_path(conversation_id)`'s own "deterministic
   from `conversation_id` alone" contract (`ADR-042` point 5) is retired
   for an ALREADY-EXISTING Thread and replaced by a frontmatter-scan
   lookup, `resolve_thread_note_path(conversation_id) -> Path | None`,
   built directly on the ALREADY-SHIPPED `list_thread_notes()`
   (`REQ-SB-56-US-01`'s own fallback-linker enumeration primitive) —
   scans every real `Work/Threads/*.md` note's own `conversation_id`
   frontmatter field for a match, returns `None` if genuinely new (the
   create-vs-update signal `thread_match_merge` already needs).** This is
   a deliberate choice over a new persisted `conversation_id -> stem`
   index file (see Alternatives) — zero new state that can drift from
   the vault's own real content, and `Work/Threads/` is exactly the same
   bounded folder size `REQ-SB-56`'s own fallback linker already scans on
   every real Meeting, so the added cost is not a new class of expense
   for this codebase. A NEW primitive, `rename_thread_note(old_path,
   new_path)`, physically renames the file in place (mirrors `Path.
   rename`'s own atomicity, the same primitive `move_note_and_
   attachments` already uses internally) whenever `thread_match_merge`
   computes a new filename (the date component changed) for an
   already-existing Thread — called AFTER every other frontmatter/body
   write for that call completes, so a rename never races an in-flight
   write to the OLD path. `thread_match_merge`'s own create-vs-update
   branch now resolves the Thread's current path via
   `resolve_thread_note_path` first (not `thread_note_exists`/
   `thread_note_path`, both retired for this call site), then computes
   the freshly-derived path from the now-current `last_message_at`, and
   renames if the two differ.
8. **`route_to_project`'s Pending-Approval payload gains `conversation_id`
   (already available on `thread_result`), and `finalize_thread_project_
   routing` re-resolves the Thread's CURRENT real path via `resolve_
   thread_note_path(conversation_id)` at finalize (Approve) time, instead
   of trusting the `thread_path` string captured at proposal time.**
   This closes the real, previously-latent correctness gap found in
   Context point 5 — a Thread renamed between a routing proposal's
   creation and its later approval (now a real possibility once
   filenames are no longer permanently stable) must still resolve to the
   right file. `thread_path` stays in the payload too, for the Pending
   Approvals UI's own human-readable display — only the WRITE path
   (`upsert_frontmatter_key` target) changes to the freshly-resolved one.
9. **A new, deterministically-regenerated `## Related` body section**
   (via the already-shipped `replace_body_section`, `ADR-042` point 2 —
   general-purpose, not Customer/Project-only, exactly as that primitive
   was designed) **carries Thread's real `[[wikilink]]`s — never Email's
   existing `insert_body_line_if_missing`-based inline primitives**,
   which Context point 6 found would silently conflict with `replace_
   body_opening_line`'s own full ownership of the same pre-first-header
   region. Added to Thread's own baseline body (alongside `## Summary`/
   `## Transcript`) and regenerated, from scratch, on every
   `thread_match_merge` call, from real, currently-resolvable data only:
   - `[[CustomerHubStem]]` when `customer` is real (not `"Unsorted"`/
     blank) — `vault_writer.hub_note_path(customer).stem`, the SAME
     stem-resolution `customer_hub_linking.link_note_to_customer_hub`
     already uses and which `ensure_customer_hub_note`'s own docstring
     already confirms resolves correctly under the OKF directory shape
     (`ADR-042`).
   - `[[PersonStem]]` for each of the Thread's own accumulated
     `participants` that has a REAL, already-existing Person note
     (`people_extraction.find_existing_person_note(email)` — never a
     guessed/fabricated one; a participant with no matching Person note
     is honestly omitted).
   - `[[ProjectStem]]` once the Thread's own `project` frontmatter key is
     populated (only after `route_to_project`'s approval resolves,
     `ADR-042` point 7 — absent on every newly created and every
     not-yet-routed Thread, per that already-`Accepted` timing fact).
   A Thread with none of the three currently resolvable produces an
   empty (but present) `## Related` section — an honest absence, never a
   fabricated placeholder link (Scenario 11). This is a genuine, narrow
   reopening of `ADR-043` point 7's specific "no inline wikilink" clause
   for Thread notes — `ensure_customer_hub_note`'s own call (unchanged)
   is not affected.
10. **Human-readable dates, without breaking `meeting_classification.py::
    _date_proximity_gap_days`'s real, already-shipped `last_message_at[:10]`
    parsing.** A new, additive frontmatter sibling field,
    `last_message_at_display` (e.g. `"Aug 16, 2026, 1:02 PM"`), is written
    alongside the existing `last_message_at` (left byte-for-byte in its
    current ISO-8601 machine-parseable form — the Constraint's own locked
    outcome). `## Transcript` entries format `email["received"]`'s own
    raw COM-stringified timestamp human-readably at write time (nothing
    in this codebase programmatically parses an individual `##
    Transcript` line — confirmed by direct repo-wide search — so this is
    a pure display-time formatting change with zero downstream parsing
    consequence).

**Alternatives Considered:**

- **A single, growing JSON array file for staging** (e.g.
  `.second-brain/email_staging.json`, one record per email) instead of
  one directory per email. Rejected — every new staged item would require
  reading, appending to, and rewriting the WHOLE file, which is exactly
  the kind of single-growing-blob contention this story's own "incremental,
  resumable" bar warns against (a rewrite mid-stall risks a torn/partial
  write corrupting every OTHER already-staged item in the same file, not
  just the newest one); one file per email makes each stage-write fully
  independent and atomic at the filesystem level.
- **Base64-encode attachment bytes directly into each staged email's own
  JSON record**, reusing the `recipients`/`attendees`/`generated`/
  `verified` JSON-encoded-string workaround (`ADR-042` point 3).
  Rejected — that workaround targets small, structured, textual values;
  attachments are already permitted up to `_MAX_ATTACHMENT_BYTES` (20MB),
  and base64 inflates that further for zero benefit over writing the
  bytes to their own sibling file (`ADR-034`'s own precedent), while
  making the metadata JSON itself needlessly large and slow to
  read/write on every enumeration.
- **A new, persisted `conversation_id -> current filename stem` index
  file** (e.g. `.second-brain/thread_index.json`), instead of a
  frontmatter-scan lookup. Considered — O(1) instead of O(n) — but
  rejected for the same reason `ADR-042` already rejected repurposing
  `conversation_index.json` for an adjacent Thread-lookup need: a second,
  independently-persisted index is a new class of drift risk (it can
  silently disagree with the vault's own real, current content if ever
  edited, moved, or restored out of band), for a bounded-cost operation
  `REQ-SB-56`'s own fallback linker already performs, live, on every real
  Meeting, with `list_thread_notes()` already built for exactly this
  scan shape.
- **Reuse Email's existing `insert_body_line_if_missing`-based inline
  wikilink primitives verbatim for Thread notes**, as the story's own
  Notes first suggested as one option. Rejected — Context point 6's own
  direct-reading finding: `replace_body_opening_line`'s already-shipped
  full-region-regenerate contract owns the exact same pre-first-header
  position `insert_body_line_if_missing` would insert at, so reusing it
  as-is would have one primitive silently erase the other's own most
  recent write on every single `thread_match_merge` call — a real,
  latent bug, not a stylistic preference. A dedicated, deterministically
  regenerated `## Related` section sidesteps the conflict entirely and
  is also the semantically correct shape: a Thread's own related-entity
  set can genuinely grow over its life (e.g. gaining a Project link only
  once routing resolves), which a regenerate-every-call section
  expresses naturally and an idempotent-insert-once primitive does not.
- **Keep `Pull` and `Processing` bundled in one call for every trigger
  source, relying solely on the new staging boundary's own durability**
  (i.e., decline Decision 4's lock-separation, and accept that a
  composite trigger's own single lock hold still serializes Processing
  behind Pull). Rejected — this would satisfy Scenario 1 and the
  "resumable, incremental" bar, but would NOT satisfy Scenario 2/3 for
  the SAME trigger surface that produced tonight's real incident (the
  scheduled/manual composite dispatch): a genuinely separate, lock-free
  Processing path is required for those Scenarios to be true in general,
  not just for a hypothetical, never-actually-triggered new schedule
  entry.
- **Restructure Meeting-capture's and Todo-capture's own triggering to
  match** (give them the same Pull/Process lock-separation). Rejected as
  out of this story's own Email-only scope (`## Non-Goals`) — their own
  capture functions do not yet have an equivalent "downstream processing
  Job that doesn't need Outlook at all" split to decouple toward; a
  future story extending this exact pattern to either should read this
  ADR's Decision 4 first rather than re-deriving the mechanism.
- **A generic, cross-capture-type staging/queue engine**, built once and
  reused by Meeting/Todo capture immediately. Rejected — mirrors `ADR-043`
  point 1's own "no forced-generic shared engine invented ahead of a
  second real example" reasoning; `email_staging.py` is scoped to Email
  alone until a second real, concrete need for the same shape exists.
- **Give `Pull` its own Agent-tier identity** (own Map node, Working
  Mode, chat surface), reviving `REQ-SB-53-US-01`'s now-`Parked` model.
  Rejected — `REQ-SB-53-US-01` stays `Parked`, not revived; `ADR-041`
  point 1's Job-tier default already covers "a separately-triggerable
  step of an existing Pipeline" without a new addressable surface, and no
  Scenario in this story asks for Pull to be independently chattable,
  independently Working-Mode-gated, or independently visible on the Map.

**Consequences:**

- `app/business/pipelines/email_capture_pipeline.py` drops its
  `outlook_com` import entirely (Scenario 1's structural check); its own
  module docstring's `Fetch`-era text needs updating to describe reading
  from staging instead — a documentation-only follow-on, not a behavior
  change.
- `app/api/email_poc_router.py`'s standalone `/poc/classify-emails`
  endpoint (still calling the legacy `classify_recent_emails` directly,
  confirmed a real, unrelated remaining caller of `outlook_com.
  list_recent_mail`) is UNAFFECTED by this ADR — it never routes through
  `email_staging.py`, `pull_email`, or `process_staged_email`; the new
  `on_item_fetched` parameter is optional and this caller simply never
  passes it.
- Meeting-capture's and Todo-capture's own real Outlook-COM calls remain
  bundled with `pull_email` under one shared-lock hold inside
  `capture_scheduler.py`'s hourly/app-start composite trigger, UNCHANGED
  — a disclosed, deliberate scope boundary (see Alternatives), not an
  oversight: their own worst-case Outlook-hold duration is not reduced by
  this ADR.
- `route_to_project`'s Pending-Approval payload shape gains
  `conversation_id` (additive) — any already-pending, not-yet-approved
  `route_thread_to_project` record created BEFORE this ADR ships lacks
  it; `finalize_thread_project_routing` must fall back to the legacy
  `payload["thread_path"]` string for such a pre-existing record (a real,
  disclosed migration-window consequence the decomposer/coder must handle
  explicitly, not silently ignore) — a genuinely NEW record, created
  after this ships, always carries it.
- `Work/Threads/*.md`'s own filename is no longer a pure, permanent
  function of `conversation_id` — any external reference to a Thread's
  OLD filename (a manual Obsidian bookmark, a manually-typed wikilink
  elsewhere in the vault) breaks silently on rename, with no forwarding/
  redirect mechanism built here — a real, disclosed limitation, not
  assumed away; Obsidian's own "unlinked mentions" surface is the
  operator's own recovery path if this is ever hit in practice, not a
  new mechanism this story builds.
- `thread_note_path`/`thread_note_exists` (the deterministic-path
  functions `ADR-042` point 5 established) become dead code for the
  Thread-note-creation-and-lookup path once this ships — deliberately
  NOT deleted by this ADR (any other real caller must be confirmed first,
  a decomposer/coder-level task, mirroring this project's own repeated
  "confirming and retiring dead code is a task-scoping decision, not
  decided at the ADR level" precedent, `ADR-043`'s own Consequences).
- Backfilling already-captured Thread notes onto the new filename/date/
  wikilink shape is explicitly out of this story's own scope (`##
  Non-Goals`) — every Thread captured before this ships keeps its old
  `<slug-of-conversation-id>.md` filename and its old bare `last_
  message_at` until it next receives a real new message (which triggers
  the rename/dual-date-field/`## Related` regeneration as a side effect
  of the normal update path) — a real, disclosed, intentionally deferred
  migration gap, not a defect.

---

## ADR-047: One-Time Full Vault Migration (`REQ-SB-59`) — archive-not-delete via a new `.second-brain/migration_backup/` soft-delete pattern; existing history-window parameters reused (no new Outlook-COM primitives); legacy flat Customer hub notes resolve `ESC-046`'s collision as an in-scope T03 consequence, feeding pre-migration content through the already-`Accepted` `detect_customer_durable_fact`/Pending-Approval gate, never a migration-only auto-write bypass — new `app/business/vault_migration.py` retrofit module, mirrors `tag_backfill.py`/`vault_restructure.py`/`partner_hub_linking.py`'s existing one-off-migration-module shape; extends `ADR-042`, `ADR-043`, `ADR-046`, and `REQ-SB-57`'s own durable-fact detection contract, reopens none of them

**Status:** Accepted
**Date:** 2026-08-18

**Context:** `REQ-SB-59-US-01` — now unblocked, all five dependency
stories (`REQ-SB-54` through `REQ-SB-58`) confirmed `Done` — is a one-time,
operator-authorized ("I am okay with rewriting the data") wipe of the
legacy per-email `Work/Emails/` notes, a full re-run of capture over
Outlook history through the already-`Done` Thread/Meeting-linking
pipelines, and regeneration of every Customer note onto the new OKF
Background/History/Glimpse/Captures shape (`ADR-042`), preserving durable
pre-migration content rather than discarding it. Direct reading of the
real, current code this pass, beyond what the story's own `## Context`
already grounded, found three further architecturally load-bearing facts
none of the story's own three stub tasks had already resolved:

1. **The email dedup gate is exact-`EntryID`-keyed and would silently
   defeat T02 if left untouched.** `run_email_capture_pipeline`'s own
   `email["id"] in already_processed` check
   (`vault_writer.load_processed_email_ids()`, unchanged since `ADR-043`
   point 2) is populated from `.second-brain/processed_email_ids.json`.
   Outlook `EntryID`s are stable across a same-mailbox rerun, so every
   real historical email this migration means to recapture is already
   marked processed in that file — a "recapture" that never resets it
   would silently process zero emails.
2. **Meeting-capture's own dedup marker is already non-gating.**
   `mark_meeting_processed`'s own docstring confirms
   `meeting_classification.py` does not gate reprocessing on
   `processed_meeting_ids.json` the way email does — it is a pure,
   idempotent audit trail, and the Meeting note write path is a top-up,
   not a create-once. Re-running `classify_recent_meetings` over a wide
   historical window is therefore sufficient on its own for Scenario 5 —
   no Meeting-note wipe is needed or wanted.
3. **The exact filename-stem collision `ESC-046` recorded (2026-08-18,
   `REQ-SB-58-US-01-T01`, still `Open`) is the same artifact this story's
   own T03 must already read and act on.** `vault_writer.
   list_all_note_paths()`'s own docstring already confirms it returns
   BOTH the old-shape flat `Work/Customers/<Name>.md` hub notes AND the
   new OKF concept files in the same flat list — the 14-of-17 collision
   `ESC-046` found live is not a separate discovery this ADR needed to
   re-derive, it is the direct, mechanical shape of the data T03's own
   Scenario 2 ("every Customer note is regenerated... preserving durable
   content") already has to enumerate and process.

Neither of these three facts was assumed — each is grounded in direct
reading of `vault_writer.py`, `meeting_classification.py`, and `ESC-046`'s
own already-recorded text, cited above.

**Decision:**

1. **New retrofit module, `app/business/vault_migration.py`, the fifth
   instance of this codebase's already-`Accepted` one-off-migration-module
   shape** (`tag_backfill.py`/`vault_restructure.py`/`partner_hub_linking.
   migrate_customer_to_partner`) — never a new mechanism family. Three
   public functions mirror the story's own T01/T02/T03 split
   (`wipe_legacy_email_notes`, `recapture_outlook_history`,
   `regenerate_customer_notes`), each exposed as its own new flat
   `POST /poc/<verb>` endpoint in `email_poc_router.py`, matching that
   router's own existing naming convention — operator-triggered, no
   scheduler wiring, no UI, no new gate mechanism.
2. **Archive, never delete — a new `.second-brain/migration_backup/
   <UTC-run-timestamp>/` root, this project's first soft-delete
   location.** Every Note this migration removes from `Work/` moves there
   via the EXISTING, unmodified `vault_writer.move_note_and_attachments`
   primitive (already fully generic over `target_dir`, no code change);
   the two now-stale `.second-brain/` JSON stores
   (`processed_email_ids.json`, `conversation_index.json`) move there via
   a plain `Path.rename` inside `vault_migration.py` itself, mirroring
   `vault_restructure.py`'s own existing precedent of touching
   `settings.vault_path` directly for mechanical, non-Note filesystem
   bookkeeping rather than inventing a new `vault_writer` primitive for a
   one-time move of already-owned files. Moving
   `processed_email_ids.json` out of its canonical path is what makes
   `load_processed_email_ids()`'s own existing `if not path.exists():
   return set()` branch reset the dedup gate — zero new `vault_writer`
   code needed for the reset itself.
3. **`Work/Meetings/` is never wiped.** Per Context point 2 above,
   `recapture_outlook_history`'s own wide-window
   `meeting_classification.classify_recent_meetings(days_back=
   meeting_days_back, days_ahead=14, limit=...)` call is sufficient, on
   its own, to satisfy Scenario 5 — it tops up every pre-migration Meeting
   note in place and, since `REQ-SB-56`'s `Link-to-Thread` Job already
   runs unconditionally inside that same call, also re-links every
   historical Meeting to its now-recaptured Thread, with zero code
   change.
4. **"Full Outlook history" reuses existing, already-parametrized read
   functions with an operator-supplied large window/limit value — no new
   Outlook-COM primitive.** `recapture_outlook_history(email_limit:
   int, meeting_days_back: int)` takes both as required, caller-supplied
   parameters (never a hardcoded magic number in this function's own
   body, this project's standing "config, not constants" convention):
   `email_pull.pull_and_stage_emails(limit=email_limit)` once (`list_
   recent_mail` iterates its own `Items` collection until `limit` is hit
   OR the collection is exhausted — an `email_limit` at/above the real
   Inbox item count fetches full history in one call), then
   `email_capture_pipeline.run_email_capture_pipeline()` once (its own
   current body already drains every currently-staged, not-yet-processed
   email in a single call, per its own docstring), then `classify_recent_
   meetings(days_back=meeting_days_back, ...)` once (`list_calendar_
   events` applies a real COM `Restrict()` date filter, so this genuinely
   reaches full calendar history). Both underlying reads stay scoped to
   the default Inbox/Calendar folders only — unchanged, pre-existing
   behavior, not a new limitation this ADR introduces or is asked to
   fix.
5. **`regenerate_customer_notes` resolves `ESC-046` directly, as an
   in-scope consequence of Scenario 2 — not a separately deferred
   bugfix.** Enumerates every note `list_all_note_paths()` returns whose
   `frontmatter["type"] == "Customer"` AND whose `path.parent.name ==
   "Customers"` (the old flat shape; an OKF concept file's own parent
   directory is instead the slug) — a generic, vault-wide scan mirroring
   `migrate_customer_to_partner`'s own "never a hardcoded name list"
   precedent. For each: `ensure_customer_hub_note(customer)` guarantees
   its OKF directory exists (no-op if already migrated); reads the flat
   note's full body; calls the SAME, unmodified, already-`Accepted`
   `project_customer_synthesizer.synthesize_customer(customer,
   evidence_text=<flat note body>)` the ongoing `REQ-SB-57` Synthesizer
   itself uses — regenerating `## Glimpse` (harmless, idempotent) and,
   via that function's own internal `detect_customer_durable_fact` call,
   proposing a normal `propose_background_amendment` Pending Approval for
   any durable fact — the exact same human-reviewed gate every other
   Background amendment goes through, **deliberately never a
   migration-only auto-write bypass.** Finally archives the flat file via
   `move_note_and_attachments` into `.second-brain/migration_backup/
   <run-timestamp>/Customers/`, which is what removes the filename-stem
   collision from `vault_indexing.rebuild_index()`'s index (`ADR-024`) —
   `ESC-046`'s own recorded option (a) ("a one-time cleanup pass
   deleting/archiving each stale legacy flat Customer hub note once its
   OKF directory concept file exists"), executed here.
6. **Pending Approvals `regenerate_customer_notes` produces are NOT part
   of this story's own Definition of Done.** Resolving them is ordinary,
   ongoing operator review through the existing, unmodified Pending
   Approvals surface — decoupled from "migration complete." The
   migration's job is to surface every real durable fact for review, not
   to force approval before the story can close.
7. **No new "already ran" state marker, no dry-run flag.** Every function
   above is naturally idempotent through the same "nothing left to act
   on" mechanism its sibling migration modules already rely on (see
   Alternative 5, below).

**Alternatives Considered:**

1. **Hard-delete (`Path.unlink()`) instead of archive-move.** Rejected —
   no existing precedent for destructive delete anywhere in this
   codebase's data-mutation surface, and an archive-move is equally cheap
   at this vault's scale while adding a free, real safety net for
   genuinely irreplaceable pre-migration prose.
2. **A new dedicated Outlook-COM "full history" primitive** (e.g. an
   unbounded `list_all_mail`/`list_calendar_since`). Rejected —
   `list_recent_mail(limit=...)`/`list_calendar_events(days_back=...)`
   already parametrize to cover full history with a sufficiently large
   operator-supplied value; a new COM query family would duplicate
   already-`Accepted`, already-proven mechanics for no new capability.
3. **Auto-writing legacy Customer content directly into `## Background`
   during migration, bypassing Pending Approval.** Rejected — this would
   special-case migration with a bulk-auto-accept path the ongoing
   Synthesizer itself never gets, undermining the one already-`Accepted`
   human-reviewed gate (`REQ-SB-57`) for exactly the highest-risk content
   this story touches: rewriting real production narrative history. The
   operator's "I am okay with rewriting the data" authorization covers
   wipe-then-recapture of EVIDENCE (Threads/Meetings, re-derivable from
   Outlook, the real source of truth); it does not extend to silently
   bypassing the durable-fact human gate for irreplaceable pre-migration
   prose that exists ONLY in the vault, with no Outlook source to
   re-derive it from if a bulk auto-write got it wrong.
4. **Leaving `ESC-046` as a fully separate, independently-scheduled
   bugfix story.** Rejected — `regenerate_customer_notes` already reads
   and must archive the exact same stale legacy flat Customer files
   `ESC-046` named; resolving it there is strictly less total work, and
   it closes a real, currently-live data-correctness bug (the wrong file
   silently answering `vault-qa`/search for 14 of 17 real Customers) at
   the same moment the Customer note shape work happens anyway, rather
   than leaving both a duplicate mechanism and the bug open for a second
   future pass.
5. **A persisted migration "already-ran" state marker, or an explicit
   dry-run flag.** Rejected as a dedicated new mechanism — archive-move
   already makes every function naturally idempotent (nothing left to
   move/act on, on a rerun) without inventing new state, exactly
   matching `vault_restructure.py`'s own existing idempotency framing
   ("once `Work/Customers/` is gone, a rerun finds nothing to move"). No
   precedent module in this codebase (`tag_backfill.py`,
   `vault_restructure.py`, `partner_hub_linking.py`) implements a
   dry-run mode either — inventing one here for the first time would be
   a deviation from established convention, not an extension of it.

**Consequences:**

- `.second-brain/migration_backup/<run-timestamp>/` becomes this
  project's first soft-delete convention; any future destructive one-off
  migration should reuse this same location/shape rather than inventing a
  second archive convention.
- `processed_email_ids.json`/`conversation_index.json` become one-time
  archived, not deleted — recoverable if a real regression is later found
  in recaptured Thread data, at the cost of leaving two now-empty-by-move
  canonical paths behind (both already handle a missing file gracefully,
  so no other caller is affected).
- `regenerate_customer_notes` will leave one Pending Approval per legacy
  Customer note whose body contains a genuine durable fact — a real,
  expected operational load on the Pending Approvals surface immediately
  after this migration runs, not a defect; the operator should expect to
  review a batch of Background-amendment proposals, not zero.
- `vault_migration.py` becomes a fifth precedent instance of the one-off-
  migration-module shape; a future similar bulk vault change should look
  here first, not reinvent.
- This migration does not touch the Partner namespace's own flat files
  (never migrated to an OKF directory, `ADR-009`) or any legacy flat
  Project-kind note (no evidence either currently exists) — if the coder
  discovers either during implementation, it is a scope-internal finding
  to log against this story, not something this ADR pre-decided.
- `email_limit`/`meeting_days_back` being required, caller-supplied
  parameters (not defaulted silently) means the operator must know
  (or estimate generously) their own real Inbox item count / mailbox
  history length before triggering T02 — an explicit, disclosed
  operational step, not hidden inside the code.

---

## ADR-048: Vault Base Provisioning + Redesigned Email/Meeting Capture (`REQ-SB-70`, `REQ-SB-71`) — raw/distilled Thread directory shape, a code-enforced section-ownership allow-list on `replace_body_section`, a generalized Files/OKF-companion primitive, Person notes nested under their primary Customer, and a generalized recursive `list_all_note_paths()` — supersedes `ADR-042` point 5 and `ADR-046` Decisions 6/7/9/10 (Thread shape only); extends `ADR-042` point 2, `ADR-041`'s Job-tier-default precedent, `ADR-046` Decision 3's Pull/Process decoupling, and `ADR-004`'s folder-vs-tag boundary (a second, narrow, disclosed carve-out); reopens neither `ADR-042` point 1's Customer/Project-only directory-shape scope-lock nor any other ADR's core decision

**Status:** Accepted
**Date:** 2026-08-18

**Context:** `REQ-SB-70`/`REQ-SB-71` were raised in one dedicated
vault-structure conversation, immediately following the `REQ-SB-59`
migration being paused mid-run over a live reliability concern (operator's
own words: *"This is Very Un Reliable and We lose soo many info if we lost
the emails"*). Both requirements were worked out turn-by-turn with the
operator, note kind by note kind, across that same conversation and are
architecturally one coherent redesign, not four independent asks — this
ADR covers all four `/plan-tasks` stories in the batch
(`REQ-SB-70-US-01`, `REQ-SB-71-US-01/-02/-03`) together, per the operator's
own framing: *"Five parts, one cohesive redesign... the vision below is one
coherent whole and should not be built piecemeal without the others."*

Four real architectural gaps, found by direct reading of the current code
(not assumed), make this genuinely ADR-worthy rather than an ordinary
same-shape extension:

1. **`vault_writer.replace_body_section` has zero caller-awareness today.**
   Confirmed by direct repo-wide search: exactly 4 real call sites
   (`email_classification.py` x2, `thread_summary_backfill.py`,
   `project_customer_synthesizer.py` x2 physically — see Decision 2) each
   regenerate a specific, agent-owned section, but nothing in the
   primitive itself stops any one of them from being passed a DIFFERENT
   header string by a future bug or careless edit. The operator's own
   words: *"What Challenges me is the Personal Info on the Item Being Re
   Written... It Applies everywhere not just on the Threads."*
2. **Thread's current shape (`ADR-042` point 5, `ADR-046` Decisions 6/7/9/10)
   is a single file that IS the transcript** — `## Transcript` accumulates
   terse one-line entries only, never a message's own full body (`REQ-SB-67`'s
   own Constraint). There is no primitive anywhere in this codebase for an
   immutable, per-message, verbatim raw note — the operator's own root
   pain (losing real email content across a stalled/imperfect re-synthesis)
   is structurally unresolved by the current shape, not merely imperfectly
   handled.
3. **`vault_writer.person_note_path(email)` is deterministic from email
   alone, flat, with no Customer-nesting concept at all** — and
   `meeting_classification.py`'s own real, already-shipped attendee loop
   (`classify_recent_meetings`, lines 271-279) contains a literal
   `if not email: continue` that silently drops every attendee with no
   resolvable email address. This is the exact, concrete code location of
   the operator's own named gap: *"people I meet that I don't have emails
   for."*
4. **`vault_writer.list_all_note_paths()` already carries one hardcoded,
   narrowly-scoped fix for exactly this class of problem** (`ADR-042`'s own
   flagged Consequence, resolved for Customer/Project only, `REQ-SB-54-US-01-T06`)
   — a 1-level flat glob plus two hardcoded `Customers/*/*.md` /
   `Customers/*/projects/*/*.md` globs. This redesign introduces a THIRD
   (Thread) and, for a recurring series, a FOURTH (Meeting) real
   directory-shaped note kind, each nesting a real, normally-frontmattered
   note at a depth the current hardcoded globs cannot see — stacking a
   third and fourth special case would repeat the same smell `ADR-042`
   already flagged once, not fix it.

**Decision:**

1. **Vault Base Provisioning (`REQ-SB-70`) — new `app/business/
   vault_provisioning.py`, mirroring `vault_migration.py`'s own module
   shape but NOT a migration (no archiving, no wipe, idempotent creation
   only).** One public function:
   ```python
   def provision_vault_base() -> dict:
       """Idempotent mkdir(parents=True, exist_ok=True) for exactly:
       Work/Customers/, Work/Threads/, Work/Meetings/, Work/Resources/,
       Work/Archive/{Opportunities,Customers,Resources}/ -- mirroring
       _write_frontmatter_note's/write_attachments' own already-proven
       idempotent-mkdir convention. Creates nothing else -- no individual
       Customer OKF directory, no Work/Opportunities/, Work/Websites/,
       Work/Notes/."""
   ```
   Exposed as `POST /poc/provision-vault-base` in the existing
   `app/api/email_poc_router.py` — that router is already this
   codebase's general home for flat, operator-triggered one-off `/poc/*`
   operations regardless of subject area (`backfill-tags`,
   `flatten-customer-folders`, `migrate-customer-to-partner` already share
   it despite none being "email" specifically); a new sibling router would
   fragment an already-established convention for no real gain.
2. **Section-ownership enforcement (`REQ-SB-71` point 6, `REQ-SB-71-US-01`)
   — a new, composed-alongside `app/data_access/section_ownership.py`
   (data_access layer, never business — `ADR-003`'s layer boundary means
   `replace_body_section` itself, which performs this check, cannot depend
   on anything in `app/business`), mirroring `ADR-014`'s own "compose
   alongside, don't reopen" precedent rather than growing `vault_writer.py`
   itself further.** Two independent, structural rules, per the operator's
   own explicit scope choice (*"1 and 2 is enough"* — no snapshot-before-write
   safety net, no extra approval gate beyond `REQ-SB-57`'s existing
   `Background`-amendment flow):
   ```python
   class SectionWriteNotAllowed(PermissionError):
       """Raised by replace_body_section when `caller` may not write
       `header` -- a real, observable, honest failure (Scenario 2), never
       a silent no-op indistinguishable from replace_body_section's own
       separate, unchanged 'header not found in THIS file' contract."""

   # Rule 1 -- ownership-typing. Header text ALONE is the key (not
   # file/note-kind-scoped) -- "## Personal Notes"/"## Actions" carry the
   # identical human-owned meaning on a Thread, a Meeting, a File
   # companion, or any future note kind that reuses either name, per the
   # PRD's own vault-wide framing. Checked FIRST and UNCONDITIONALLY --
   # never overridable by any caller's own registered allow-list, by
   # construction (Scenario 3's "applies uniformly... not only the ones
   # this story happens to test explicitly").
   _HUMAN_OWNED_HEADERS: frozenset[str] = frozenset({
       "## Personal Notes", "## Actions",
   })

   # Rule 2 -- per-caller allow-list of agent-owned headers, deny-by-
   # default: a caller id absent from this dict may write nothing.
   # Caller granularity is the calling FUNCTION (module.function), not
   # the calling MODULE -- least-privilege: project_customer_
   # synthesizer.py's own three real call sites are three DISTINCT
   # caller ids even though they share one module and one "sole
   # synthesizer owner" convention, because synthesize_project has no
   # legitimate reason to ever write ## Background.
   _CALLER_ALLOW_LISTS: dict[str, frozenset[str]] = {
       "email_classification.thread_match_merge": frozenset({"## Summary", "## Related"}),
       "thread_summary_backfill.backfill_thread_summaries": frozenset({"## Summary"}),
       "project_customer_synthesizer.synthesize_project": frozenset({"## Glimpse"}),
       "project_customer_synthesizer.synthesize_customer": frozenset({"## Glimpse"}),
       "project_customer_synthesizer.finalize_background_amendment_proposal": frozenset({"## Background"}),
   }

   def is_header_allowed(caller: str, header: str) -> bool:
       if header in _HUMAN_OWNED_HEADERS:
           return False
       return header in _CALLER_ALLOW_LISTS.get(caller, frozenset())
   ```
   `vault_writer.replace_body_section` gains a REQUIRED keyword-only
   `caller: str` parameter (a deliberate breaking-signature change — every
   call site, present and future, must explicitly declare identity; no
   default, so a forgotten declaration is a loud `TypeError`, not a silent
   gap):
   ```python
   def replace_body_section(path, header: str, new_content: str, *, caller: str) -> bool:
       if not section_ownership.is_header_allowed(caller, header):
           raise section_ownership.SectionWriteNotAllowed(caller, header)
       ...  # unchanged region-location/replace mechanism (ADR-042 point 2)
   ```
   `read_body_section`/`append_body_section_line`/
   `replace_body_opening_line`/`insert_body_line_if_missing` are
   UNCHANGED — scope is exactly `replace_body_section`, per the PRD's own
   text (`REQ-SB-71-US-01`'s own Non-Goals). All 4 real, already-shipped
   call sites (6 physical `replace_body_section` invocations across them —
   `thread_match_merge` calls it twice, `project_customer_synthesizer.py`
   calls it three times across its own three functions, `thread_summary_
   backfill.py` once) are retrofitted with the `caller` id shown above in
   the SAME task that
   ships the guard — never left calling the old signature. `REQ-SB-71-US-02`/
   `-US-03` each register their OWN new caller id(s) against this SAME
   registry as part of their own scope (Decision 3/6, below) — never
   silently inheriting an existing entry.
3. **Email Capture Redesign (`REQ-SB-71` points 1/2, `REQ-SB-71-US-02`) —
   Thread becomes a directory, permanently keyed by `conversation_id`
   alone; raw messages are immutable, write-once; Stage 1/Stage 2 are two
   new, decoupled, no-shared-lock capabilities of the EXISTING
   `email-capture-pipeline` Agent-tier identity.**
   - **Thread directory shape — `Work/Threads/<slug-of-conversation_id>/`
     — reverts to `ADR-042` point 5's ORIGINAL deterministic-from-
     conversation_id-alone scheme, permanently (not merely provisionally),
     superseding `ADR-046` Decisions 6/7/9's own human-readable/renamable
     FILENAME mechanism.** This is a deliberate simplification, not an
     oversight: `ADR-046`'s rename-in-place/frontmatter-scan-lookup
     machinery existed solely because the OLD single-FILE shape wanted the
     FILE's own name to carry an evolving human-readable identity for
     Obsidian browsability. A DIRECTORY's own name carries far less of that
     UX weight — the distilled concept file's `thread_name` frontmatter
     field (unchanged, captured once from the first message) already
     supplies the human-readable identity Obsidian's own note title/search
     surfaces, and the concept file underneath can simply be named
     identically to its own directory (`<slug>/<slug>.md`), matching
     `okf_directory_paths`' own `<slug>/<slug>.md` convention already
     established for Customer/Project — WITHOUT adopting that family's
     `index.md`/`log.md`/`captures.md` reserved files (Thread is a
     genuinely different, simpler 2-part convention; `ADR-042` point 1's
     own explicit "Customer and Project are the ONLY two 4-file-OKF-shaped
     kinds" scope-lock is NOT reopened by this addition — Thread never
     gets that 4-file shape).
     ```python
     def thread_directory_paths(conversation_id: str) -> dict:
         concept_slug = _slugify(conversation_id)
         base = settings.vault_path / _THREADS_SUBFOLDER / concept_slug
         return {"directory": base, "concept": base / f"{concept_slug}.md",
                 "messages": base / "messages"}
     ```
   - **Distilled concept file body** (`<slug>.md`): `## Summary`
     (agent-owned, regenerated) + `## Personal Notes` (human-owned) +
     `## Actions` (human-owned, a literal checklist — resolved directly:
     `## Actions` is never backed by `todo_classification` in either
     direction, since that would require an agent write path into a
     human-owned section, directly contradicting Decision 2's own Rule 1)
     + `## Related` (agent-owned, regenerated, unchanged mechanism from
     `ADR-046` Decision 9). `## Transcript` is RETIRED — superseded by the
     `messages/` directory itself, which now carries the full verbatim
     content `## Transcript`'s own terse one-liners never did.
   - **Raw message note — write-once, `messages/<received[:10]>-<hash8
     (message_id)>.md`**, mirroring `meeting_note_filename_stem`'s own
     hash-suffix disambiguation shape (`message_id` = the email's own
     `id`/EntryID field, already unique per message). A new `vault_writer`
     primitive family (`raw_message_note_path`, `raw_message_note_exists`,
     `create_raw_message_note`) — the caller (Stage 1) MUST check
     `raw_message_note_exists()` first and never call `create_raw_message_
     note` a second time for the same `message_id` (mirrors every other
     `create_*_baseline`'s own "always writes unconditionally, caller
     checks existence first" contract already established in this module).
   - **Stage 1 — zero Compass calls, reuses `email_pull.pull_and_stage_
     emails`/`email_staging` VERBATIM as its raw-fetch substrate** (the
     PRD's own explicit "matching this project's own decoupled-pull
     lesson... extended one level deeper" instruction, taken literally,
     not just in shape). New `app/business/pipelines/raw_message_capture.py`
     (sibling to `email_capture_pipeline.py`/`email_pull.py`), owning:
     ```python
     def capture_raw_thread_messages(limit: int = 10) -> dict:
         """Calls email_pull.pull_and_stage_emails(limit=limit) (real
         Outlook COM -- joins agent_schedule_registry.get_shared_
         dispatch_lock(), the SAME shared lock pull_email already joins;
         this is concurrency-safety reuse, never a new agent_schedule_
         registry ENTRY), then drains every currently-staged email
         (email_staging.list_staged_emails()) not yet written as a raw
         message note: writes create_raw_message_note (write-once),
         ensures the Thread's own distilled note exists (create_thread_
         note_baseline if thread_directory_paths(conversation_id)
         ['concept'] doesn't exist yet -- a real, deterministic existence
         check, no lookup needed, per Decision 3's own directory-naming
         reversion), then email_staging.remove_staged_email(entry_id).
         Zero compass_client import anywhere in this module."""
     ```
     Exposed as `POST /poc/capture-raw-thread-messages` — a NEW,
     independent capability id (e.g. `capture_raw_thread_messages`) of the
     SAME existing `"email-capture-pipeline"` Agent-tier identity
     (extends `ADR-041`'s Job/capability-tier-default precedent, mirrors
     `ADR-046` Decision 3's own "Pull does NOT earn its own Agent-tier
     identity" reasoning exactly) — never a new Agent, no new Map node.
   - **Stage 2 — the real Compass-backed judgment, fully decoupled, no
     shared lock with Stage 1.** `email_classification.py` gains
     `synthesize_thread(conversation_id: str) -> dict`, replacing
     `thread_match_merge`'s own prior role: reads EVERY raw message
     currently under that Thread's own `messages/` directory (full
     reconstruction, never a rolling/incremental delta — a deliberate
     reversal of `REQ-SB-67`'s own rolling-synthesis design, justified
     below in Alternatives Considered, now that full raw content is
     durably available to re-read cheaply), calls `classify_email`
     ONCE against the FIRST raw message's own body (customer/kind
     determination — preserves the existing "customer decided once, on
     the first message, never contradicted by a later one" Constraint
     rather than inventing new mid-conversation-reclassification
     behavior), does the real merge-vs-new-Thread judgment, and
     regenerates `## Summary` via `replace_body_section(path, "##
     Summary", ..., caller="email_classification.synthesize_thread")`
     and `## Related` via `replace_body_section(path, "## Related", ...,
     caller="email_classification.synthesize_thread")` — ONE caller id,
     covering both headers, mirroring the OLD `thread_match_merge`'s own
     registered allow-list shape from Decision 2 (this NEW caller id
     supersedes that OLD one for new capture; the old entry becomes dead
     registry data the moment `thread_match_merge` itself is retired —
     see Consequences). `route_to_project`'s own existing Pending-Approval
     shape (`ADR-043` point 4) is preserved, now triggered from
     `synthesize_thread`'s own end instead of `thread_match_merge`'s.
     Exposed as `POST /poc/synthesize-thread?conversation_id=<id>` — a
     second new, independent capability id (`synthesize_thread`) of the
     SAME `"email-capture-pipeline"` Agent-tier identity, sharing NO lock
     with `capture_raw_thread_messages` (Scenario 5's own proof
     obligation, mirroring `pull_email`/`process_staged_email`'s own
     "share no lock" precedent, `ADR-046` Decision 3, exactly).
   - **The EXISTING scheduled `pull_email`/`process_staged_email`
     capability ids stay wired exactly as-is (no new `agent_schedule_
     registry` entry) — their own underlying implementation is what
     composes the two new functions above in sequence,** so the hourly
     tick keeps fully capturing mail automatically with zero new
     registration, while each stage ALSO becomes independently,
     directly operator-triggerable via its own new endpoint. This is the
     literal embodiment of `REQ-SB-71`'s own repeated "supersedes the
     shape, never the trigger mechanism" framing, applied identically to
     both Email and Meeting (Decision 5, below).
4. **Files/OKF-companion convention (`REQ-SB-71` point 5) — a new, generic
   `vault_writer` primitive, parameterized by (subfolder, note_stem)
   exactly like `write_attachments` already is, renamed `attachments/` →
   `files/`.**
   ```python
   def write_file_companion(
       subfolder: str, note_stem: str, file_slug: str,
       original_filename: str, content: bytes, summary: str,
   ) -> dict:
       """files/<slug-of-file_slug>/<original_filename> (raw bytes,
       untouched) beside files/<slug-of-file_slug>/<slug-of-file_slug>.md
       (OKF-lite companion: frontmatter + ## Summary + ## Personal Notes).
       Built once, against the one real concrete need (Email/Thread
       attachments) -- REQ-SB-71-US-02's own Files task -- generically
       enough that Meeting/Customer/Person/a future Opportunity reuse it
       UNCHANGED the moment a second real files-capturing need exists,
       mirroring okf_directory_* being built once for Customer then reused
       unchanged for Project."""
   ```
   The companion note's own `## Summary` write goes through the SAME
   section-ownership guard (Decision 2) — its caller (e.g.
   `"email_classification.write_file_companion"` or wherever the coder
   composes it) is a NEW registry entry `REQ-SB-71-US-02`'s own task
   registers, allow-list `{"## Summary"}`; `## Personal Notes` is human-
   owned, per Decision 2's Rule 1, uniformly. Reuses `compass_client.
   summarize_content` + `upload_storage.save_upload/extract_text_content/
   delete_upload` VERBATIM (the identical technique `summarize_attachment`
   already established) — no new summarization/extraction mechanism.
5. **Meeting Capture Redesign (`REQ-SB-71` point 3) — reuses the EXISTING
   `/poc/classify-meetings` endpoint and `"meeting-capture"` capability id
   unchanged; `meeting_classification.classify_recent_meetings` is
   rewritten IN PLACE to produce the new shape.** No new endpoint is
   needed or built — the existing endpoint already satisfies "reachable
   via a real HTTP endpoint, operator-triggered" for free, and the
   existing scheduled trigger keeps running exactly as wired, now
   producing the new shape on its next tick (the identical "supersedes
   shape, never trigger" pattern as Decision 3's Email design).
   - **One-time meeting — unchanged filename scheme,
     `Work/Meetings/<meeting-slug>.md`** (`meeting_note_filename_stem`,
     `hash8("{subject}|{start}")`, `ADR-019`, untouched).
   - **Recurring meeting — a new directory shape,
     `Work/Meetings/<series-slug>/<series-slug>.md`, `series-slug` keyed
     by `item.GlobalAppointmentID` (Outlook's own per-series-stable
     property).** A direct, deliberate reuse of a fact `ADR-013`/`ESC-012`
     already live-confirmed and then REJECTED as a per-OCCURRENCE dedup
     key (it was found IDENTICAL across every occurrence of a series) —
     the exact property that made it wrong for that purpose (constant
     across occurrences) is exactly right for THIS one (series identity).
     `outlook_com.list_calendar_events` gains `is_recurring: bool` and
     `series_id: str` (`getattr(item, "GlobalAppointmentID", None) or
     ""`) fields.
   - **Frontmatter-only logistics, raw invite dropped entirely, never
     archived (a deliberate, operator-authorized, named exception to this
     project's own archive-not-delete discipline).** `teams_link`/
     `dial_in` are extracted via regex from `item.Body` TRANSIENTLY,
     inside `list_calendar_events` (or a small helper it calls) — the raw
     body string itself is NEVER included in the function's own returned
     dict and never reaches any caller, business layer, or disk. Surviving
     frontmatter: `teams_link`, `dial_in`, `organizer`, `attendees`
     (wikilinks), `recurrence`, `calendar_event_id` (`id`/EntryID, one-time)
     or `calendar_series_id` (`series_id`, recurring).
   - **Body — identical shape for one-time and recurring** (one shared
     code path, never two divergent ones, mirroring this project's own
     repeated "one shared mechanism" precedent): `## Summary` (agent-owned,
     regenerated, new caller id `"meeting_classification.classify_recent_
     meetings"` → allow-list `{"## Summary"}`) + `## History` (agent-owned,
     GROWING via the existing, unguarded `append_body_section_line` — one
     dated entry per occurrence; a one-time meeting simply ends up with
     exactly one entry, ever) + `## Personal Notes`/`## Actions`
     (human-owned). Each `## History` entry is synthesized (a new Compass
     call, mirroring `_synthesize_thread_summary`'s own verbatim reuse of
     `compass_client.summarize_content`) from the occurrence's own calendar
     logistics AND, when linked, its Thread's current `## Summary` (reads
     `synthesize_thread`'s own just-written output via `read_body_section`
     — never a second, divergent Thread-summarization call).
   - **People — no-email attendee no longer skipped; Person storage
     retargeted (Decision 6).**
6. **People nested under primary Customer (`REQ-SB-71` point 4,
   `REQ-SB-71-US-03`) — extends `ADR-004`'s folder-vs-tag boundary a
   SECOND time (after `ADR-042`'s own Customer/Project hub-entity
   carve-out), deliberately and narrowly, for Person only.**
   ```python
   def person_note_dedup_key(name: str, email: str | None) -> str:
       """Lowercased email when one exists (REQ-SB-10's own original,
       unchanged convention) -- or a slug of the display name when it
       does not (closes meeting_classification.py's own silent
       no-email-attendee `continue`). A name-based key cannot
       structurally distinguish two different real no-email people who
       share an exact display name -- a real, disclosed, narrow residual
       limitation, not resolved further by this story."""
       return email.lower() if email else _slugify(name.lower())

   def person_note_path(dedup_key: str, customer: str | None) -> Path:
       """Work/Customers/<slug>/People/<slug-of-dedup_key>.md when
       customer is a real, matched Customer name; the existing flat
       Work/People/<slug-of-dedup_key>.md otherwise -- operator-
       confirmed 2026-08-18 fallback for the PRD's own silent third case
       (a Person with no derivable/matched Customer at all, including
       every no-email attendee, since there is no email domain to derive
       a company from)."""

   def find_person_note_path(dedup_key: str) -> Path | None:
       """Vault-wide lookup by dedup_key alone, regardless of which
       Customer (if any) the note is nested under -- mirrors resolve_
       thread_note_path's own 'no persisted index, a live bounded scan'
       precedent (ADR-046 Decision 7) for the identical class of
       problem: a Person's home is no longer deterministic from dedup_
       key alone once nesting depends on a per-caller Customer match
       that can legitimately differ across callers/time. Scans
       Work/Customers/*/People/<stem>.md and Work/People/<stem>.md."""
   ```
   `people_extraction.ensure_person_note(name, email)` (signature
   otherwise unchanged; `email` may now be `None`/`""`) is retargeted:
   `find_person_note_path` is checked FIRST — if a note already exists
   ANYWHERE, it is topped up in place, NEVER moved or duplicated, even
   when this call's own newly-derived Customer differs from where the
   note already lives (Scenario 5: the existing note under Customer A is
   simply wikilinked from Customer B's own relevant note via the SAME
   `upsert_attendee_links`/`_build_thread_related_wikilinks`-style
   forward-link mechanism already in use everywhere else in this
   codebase, plus Obsidian's own automatic backlinks — no new linking
   mechanism is invented). Only when no note exists anywhere yet is a NEW
   one created, nested under the matched Customer or, absent one (Scenario
   6, including every no-email attendee), at the flat fallback location.
   `customer_hub_linking.ensure_customer_hub_note`/`link_note_to_customer_
   hub` are called EXACTLY as they already are today, layered on top,
   unmodified — this decision retargets WHERE the note physically lives,
   never the existing company-tag/hub-linking behavior.

   **This extension is deliberately NOT generalized to any other
   multidimensional content note kind** — Thread, Meeting, and Files all
   stay flat/tag-linked exactly as `ADR-004`/`ADR-042` already established;
   only Person gets this second carve-out, per the PRD's own explicit,
   narrow framing ("a Person's primary home... a physical filing choice,
   not a hard constraint").

   **Person's own PRD-named `## Glimpse` (agent-owned, rolled up from every
   Thread/Meeting mention) + `## Personal Notes` body redesign is
   explicitly OUT OF SCOPE for this batch.** None of `REQ-SB-71-US-03`'s
   own AC Scenarios test Person note body content — only existence, dedup,
   and nesting location. Building a Person-level Synthesizer here would be
   real, unrequested scope creep; a future story is where that lands, not
   invented here. Person's own body stays exactly as it is today (empty,
   or the pre-existing inline `**Customer:**`/`**Partner:**` wikilink
   line(s)) for this batch.
7. **`vault_writer.list_all_note_paths()` generalized to a single bounded
   recursive scan, replacing the 1-level flat glob plus two hardcoded
   Customer/Project-specific 2-level globs.**
   ```python
   def list_all_note_paths() -> list:
       work_root = settings.vault_path / _WORK_ROOT
       if not work_root.exists():
           return []
       return sorted(
           path for path in work_root.rglob("*.md")
           if path.name not in _OKF_RESERVED_FILENAMES
       )
   ```
   Strictly behavior-preserving for every existing caller (a superset of
   the old flat + two-hardcoded-glob result — nothing previously
   discoverable stops being discoverable); newly, correctly discovers
   Thread's own distilled concept file, a recurring Meeting series' own
   concept file, every raw message note, and every File OKF companion note
   — all real, normally-frontmattered notes this redesign nests at varying
   depths, none of them OKF-reserved. `list_thread_notes()` (composed by
   `list_threads_for_project`, Meeting's own fallback linker, and
   `_link_to_thread_by_conversation_id`'s existence check) is similarly
   rewritten for the new 2-level shape (`Work/Threads/*/*.md`, filtered to
   `path.parent.name == path.stem` — excludes `messages/*.md`); a
   directory-shaped recurring Meeting series needs no equivalent
   enumeration primitive of its own (no caller composes over "every
   Meeting series" the way Thread's own linkers do).

**Alternatives Considered:**

1. **Per-caller allow-list passed ad-hoc by each call site, instead of a
   central registry.** Rejected — weaker guarantee: a bug/careless edit at
   any one call site could pass a wider inline list with nothing else to
   catch it. A single, composed-alongside registry (Decision 2) is the
   ONE place a human (or a future architect pass) audits every caller's
   own real permissions at a glance.
2. **Per-MODULE caller granularity** (e.g. one `"project_customer_
   synthesizer"` id covering all three of that module's own real call
   sites). Considered, since the module's own docstring already frames
   itself as the sole owner of both sections — rejected as strictly less
   safe than per-FUNCTION granularity for no real cost: `synthesize_
   project` has no legitimate reason to ever write `## Background`, so it
   should not be able to.
3. **A decorator-based guard** (e.g. `@allowed_sections(...)` wrapping each
   caller function). Rejected — this codebase's own established style is
   plain functions with explicit, inline parameters (mirrors every other
   primitive in `vault_writer.py`); a decorator would be new ceremony for
   a check that a single required kwarg + one registry lookup already
   expresses completely.
4. **Keep Thread's single-file shape; add a separate side-channel "raw
   archive" of full message bodies alongside it.** Rejected — directly
   contradicts the PRD's own explicit "every individual email becomes its
   own immutable, verbatim raw note" framing, and would leave TWO
   partially-overlapping representations of the same evidence (the old
   file's own accumulated state, plus a new side-archive) rather than one
   coherent raw/distilled split.
5. **Give Stage 1/Stage 2 their own new Agent-tier identities**, rather
   than two more capabilities of the existing `"email-capture-pipeline"`
   identity. Rejected — mirrors `ADR-046` Decision 3's own already-`Accepted`
   reasoning exactly (no new Map node, no new chat surface, no new Working
   Mode needed for a capability-level split within one already-established
   Pipeline).
6. **Keep `synthesize_thread`'s own grounding rolling/incremental**
   (`REQ-SB-67`'s own design), reading only the prior `## Summary` + a new
   message's own delta, rather than reconstructing from every raw message
   on every Stage 2 call. Rejected for the NEW shape specifically: `REQ-SB-67`'s
   rolling design existed because full message bodies were NEVER durably
   available to re-read (`## Transcript` only ever kept a terse one-liner)
   — now that raw messages ARE durably, verbatim, cheaply re-readable, full
   reconstruction is strictly higher-fidelity (avoids compounding
   summarization drift across many prior syntheses) at an accepted, real
   cost of a larger prompt per Stage 2 call.
7. **Keep Thread's directory name human-readable/renamable** (porting
   `ADR-046` Decisions 6/7/9 forward unchanged onto the new directory
   shape). Rejected — the entire rename-in-place/frontmatter-scan-lookup
   mechanism existed to solve a problem (an evolving human-readable
   FILENAME) a directory name doesn't have the same UX weight for; reverting
   to `ADR-042`'s original deterministic-from-`conversation_id`-alone
   scheme removes a whole class of complexity (rename races, no-persisted-
   index lookup cost) that the new shape does not need to re-pay.
8. **A dedicated `Work/Meetings/<series-slug>/` directory ALSO for
   one-time meetings, for shape symmetry with recurring.** Rejected — no
   real need; mirrors `ADR-042`'s own "don't generalize until a second
   real need exists" precedent — a one-time meeting's own flat file
   already fully satisfies every AC Scenario, and Files' own
   `subfolder`/`note_stem`-parameterized convention (Decision 4) already
   works identically for a flat OR directory-shaped owner, so nothing is
   gained by forcing symmetry here.
9. **A brand-new, separate meeting-capture endpoint, distinct from the
   existing `/poc/classify-meetings`.** Rejected — would duplicate, not
   extend, the existing scheduled capability's own real logic, directly
   risking the standing "existing scheduled capabilities are not touched,
   removed, or DUPLICATED" constraint; reusing the existing endpoint
   satisfies "reachable via a real HTTP endpoint" for free.
10. **An "Unsorted"-style catch-all Customer directory for a Person with
    no derivable/matched Customer**, instead of the existing flat
    `Work/People/` fallback. Rejected — operator-confirmed 2026-08-18,
    choosing between exactly this option and the flat fallback; the flat
    fallback reuses an already-proven, already-correct existing behavior
    rather than inventing a new bucket the PRD never named, and mirrors
    this project's own "honest absence over a fabricated placement"
    precedent (`REQ-SB-69-US-01` Scenario 11).
11. **Moving a Person's note to a NEW Customer directory once a stronger
    match is later found**, instead of wikilink-only. Rejected — the PRD's
    own explicit text: a Person spanning multiple Customers is "simply
    wikilinked from the others, never physically duplicated or moved."
12. **Stack a third/fourth hardcoded glob onto `list_all_note_paths()`**
    (one more per new directory-shaped kind), rather than generalizing to
    a bounded recursive scan. Rejected — this is the SAME fix pattern
    `ADR-042` already applied once, narrowly; a third and fourth real
    instance (Thread, recurring Meeting) crosses this codebase's own
    repeated "generalize after two-to-three real instances" threshold —
    continuing to special-case would be a repeat of an already-flagged
    smell, not a fix for it.
13. **Fold `REQ-SB-70`'s provisioning module into `vault_migration.py`**,
    since both are one-off `app/business/` operator-triggered modules.
    Rejected — provisioning is explicitly NOT a migration (no archive, no
    wipe, no re-run over Outlook history); folding it in would blur
    `vault_migration.py`'s own real, `ADR-047`-established "archive-not-
    delete, wipe/recapture/regenerate" identity for no shared logic gained.

**Consequences:**

- **`email_classification.thread_match_merge` is retired** the moment
  `synthesize_thread` (Decision 3) ships — its own `"email_classification.
  thread_match_merge"` section-ownership registry entry becomes dead data,
  and `## Transcript`'s own append-only role is fully superseded.
  Confirming and retiring the function itself (and any now-dead helper,
  e.g. `_build_thread_related_wikilinks` if fully absorbed into
  `synthesize_thread`) is a coder-level task-scoping decision, mirroring
  this project's own established precedent (`record_conversation_note`/
  `conversation_index.json`'s own retirement, "Email Capture & Threading
  Pipeline" section above) — every real caller must be enumerated
  explicitly by whoever picks up that task, the same discipline `ADR-043`'s
  own `email-capture` retirement already required.
- **`resolve_thread_note_path`/`rename_thread_note`/`thread_note_
  filename_stem`/`thread_note_path_for`/`last_message_at_display`
  (`ADR-046` Decisions 6/7) become dead code for new capture** — the same
  coder-level retirement discipline applies. `thread_note_path`
  (`ADR-042`'s ORIGINAL function) is REVIVED, unchanged in shape, as the
  concept-file half of `thread_directory_paths`.
- **`vault_writer.person_note_path`'s signature change
  (`(email)` → `(dedup_key, customer)`) is a breaking change** across
  every real caller: `people_extraction.py` (`ensure_person_note`, `find_
  existing_person_note`, `ensure_person_note_for_captured_email`, `link_
  email_to_person`), `email_classification.py`'s own per-write hook, and
  any Cockpit-surface caller. The decomposer must enumerate every real
  caller explicitly, mirroring the same discipline required above.
- **`replace_body_section`'s new required `caller` kwarg is ALSO a
  breaking signature change** — every one of its 6 physical existing call
  sites must be touched in the SAME task that ships the guard (`REQ-SB-71-
  US-01-T02`), never left calling the old signature even transiently.
- **`inbox-cockpit.html`'s backend** (`app/business/cockpit/
  attachments.py`, hardcoded `Work/Emails/attachments`) **and `meeting-
  cockpit.html`'s own backend both have a real, disclosed regression risk**
  against these new shapes (raw `files/` layout; recurring Meeting's own
  `## History`-per-occurrence shape) — named here, not silently left
  broken. Whether each is fixed inside these same stories' own tasks or
  filed as a separate, disclosed follow-up is a decomposer-level scoping
  call, not pre-decided by this ADR.
- **Backfilling already-captured Thread/Meeting/Person notes onto any of
  these new shapes is explicitly NOT part of this ADR's own scope**
  (mirrors `REQ-SB-67`/`REQ-SB-69`'s own "capture vs. backfill are
  separable concerns" precedent) — going-forward capture only; a future
  `REQ-SB-59`-style follow-up, if wanted.
- `Work/Threads/`, and `Work/Meetings/<series-slug>/` for a recurring
  series, become directory-shaped kinds for the FIRST time outside the
  Customer/Project OKF family — Decision 7's generalized `list_all_note_
  paths()` is what keeps both (and every File OKF companion, at whatever
  depth) genuinely discoverable by search/indexing/`list_known_customers`
  rather than silently invisible, closing the SAME class of gap `ADR-042`'s
  own flagged Consequence already named once for Customer/Project.
- `.second-brain/email_staging/` (`ADR-046` Decision 1) is fully reused,
  unmodified, as Stage 1's own substrate — no new staging/promotion gate
  is introduced anywhere in this redesign (`MEMORY.md`'s standing
  constraint, reconfirmed, not reopened).
- Every new capability this ADR introduces (`provision_vault_base`,
  `capture_raw_thread_messages`, `synthesize_thread`, the rewritten
  `classify_recent_meetings`) is reachable ONLY via a real `/poc/*` HTTP
  endpoint, operator-triggered — none is wired into `REQ-SB-47`'s
  scheduler or given a new `agent_schedule_registry` entry, per the PRD's
  own explicit, standing out-of-scope block for this whole requirement.

---

## ADR-049: The Librarian Section — First Housekeeping Pipeline (`REQ-SB-72`) — a new autonomous, scheduled Agent-tier identity; Thread lookup reverts to a frontmatter scan (partially supersedes `ADR-048` Decision 3's own "permanent deterministic-path" sub-decision only); a new whole-directory Thread-rename primitive; `## Related` ownership transfers wholesale to a new Librarian Job; a new company-mention-detection Compass call re-checked against live known-entity lists before ever auto-creating or proposing — extends `ADR-048` Decisions 1/2/4/7 (Section/Agent creation, section-ownership guard, Files/OKF convention, `list_all_note_paths`), `ADR-021` point 2 (never a second, divergent placement/proposal mechanism), and `ADR-037` (`agent_schedule_registry`); reopens neither `ADR-048`'s Thread-directory-shape decision itself nor any other ADR's core decision

**Status:** Accepted — Decision 1's own "purely read-only" framing narrowed
by [ADR-052](ADR.md) (adds a one-time, self-healing migration WRITE for a
legacy, pre-redesign flat-shape `Work/Threads/<name>.md` Thread note only;
the frontmatter-scan-over-deterministic-path choice itself, and every other
Decision below, remain unchanged, not reopened)
**Date:** 2026-08-18

**Context:** `REQ-SB-72` was raised in the same vault-structure conversation
as `REQ-SB-70`/`REQ-SB-71`, opened once those stories' own capture pipelines
shipped and real housekeeping gaps (`ESC-046`, `ESC-048`) surfaced as live
evidence for why a self-running Section is needed. Every scope-level decision
in the PRD text (the four concrete tasks, the two explicit deferrals, that
this pipeline runs scheduled/autonomous unlike `REQ-SB-70`/`REQ-SB-71`) was
worked out turn-by-turn with the operator and is not re-litigated here — this
ADR covers the MECHANISM-level decisions the PRD/story text explicitly left
to the architect.

Three real things, found by direct reading of the current live code (not
assumed), make this genuinely ADR-worthy rather than an ordinary same-shape
extension:

1. **A real filename/directory rename requires reopening `ADR-048` Decision
   3's own Thread-lookup choice.** `resolve_thread_note_path` is today a pure,
   deterministic existence check against `thread_directory_paths(conversation_
   id)["concept"]` — correct only as long as a Thread's own directory name
   never diverges from its `conversation_id` slug. The PRD's own text
   explicitly names this reopening as required, not optional: *"This requires
   switching Thread existence-lookup from `ADR-048`'s deterministic path-based
   check back to a frontmatter-based match on `conversation_id`."* (NOTE, for
   the record: the ADR-048 document's own numbered Decision list places this
   specific choice under Decision 3, "Email Capture Redesign" — several
   already-shipped code docstrings and this story's own text instead cite it
   as "Decision 7," which the ADR-048 document itself assigns to `list_all_
   note_paths()`'s generalization. This is a pre-existing citation-numbering
   drift in already-`Done` work, not a live defect and not this ADR's own
   scope to correct — flagged here only for precision, not re-litigated.)
2. **Direct reading of every real composer of `thread_directory_paths(
   conversation_id)` finds THREE call sites — not the two the story's own
   Context names — that silently resolve to the WRONG (stale, since-renamed)
   path the moment a Thread's directory diverges from its `conversation_id`
   slug:** `raw_message_capture.capture_raw_thread_messages`'s own Stage 1
   existence check (line 97), `synthesize_thread`'s own `messages/` directory
   read (line 479, Stage 2 — distinct from its own already-correctly-cited
   create-vs-update check at line 503), and `meeting_classification._
   synthesize_history_entry`'s own linked-Thread `## Summary` read (line 324).
   Only fixing `resolve_thread_note_path` itself (the story's own narrower
   framing) would leave all three of these silently broken the first time any
   Thread is renamed — a real, material gap this ADR closes.
3. **A real, materially worse, ALREADY-LIVE consequence against the still-
   `supervised`, still-scheduled `thread_match_merge` pipeline, beyond what
   `ESC-048` currently describes.** `ESC-048` (2026-08-18, `SPRINT-061`)
   disclosed that `thread_match_merge` silently creates a DUPLICATE Thread
   for a pre-redesign, flat-shape conversation, because the retargeted
   `resolve_thread_note_path` no longer finds it. Direct reading of `thread_
   match_merge`'s own full body (`email_classification.py` lines 191-418),
   done for THIS pass, finds a second, more severe failure mode `ESC-048`
   did not name: for a conversation with an ALREADY-EXISTING, NEW-shape
   (`ADR-048`) Thread, `resolve_thread_note_path` DOES find it — and then
   `thread_match_merge`'s own still-live legacy `thread_note_path_for`/
   `rename_thread_note` calls (`ADR-046`, lines 382-386) compute a FLAT,
   hash-suffixed legacy path and physically move the concept file onto it,
   ORPHANING that Thread's own `messages/`/`files/` subdirectories — a
   directory-orphaning data-integrity defect, not merely a duplicate note.
   This is confirmed to already fire TODAY, independent of this ADR/story —
   see Consequences and `ESCALATIONS.md` → `ESC-050`.

**Decision:**

1. **Thread lookup reverts to a frontmatter-based scan — a new, shared
   `resolve_thread_directory(conversation_id) -> Path | None` primitive,
   composing the existing `list_thread_notes()` (never a second,
   independent Thread-enumeration mechanism), matching `frontmatter.get(
   "conversation_id") == conversation_id`.** This is the THIRD swing of
   this project's own Thread-matching mechanism (`ADR-046` frontmatter-scan
   → `ADR-048` deterministic-path → back to frontmatter-scan), justified by
   real operational data: steady-state capture is ~10 emails/hour, cheap
   enough to scan; `ADR-048`'s own 400-email bulk-retrofit volume concern is
   a SEPARATE, disclosed carve-out (below), not reopened wholesale.
   - `resolve_thread_note_path(conversation_id) -> Path | None` — PUBLIC
     SIGNATURE UNCHANGED, retargeted to a thin wrapper (`directory /
     f"{directory.name}.md"` or `None`) — every existing real caller
     (`_link_to_thread_by_conversation_id`, `_trigger_project_resynthesis`,
     `synthesize_thread`'s own create-vs-update check) keeps working with
     ZERO call-site change, mirroring `ADR-048` Decision 7's own exact
     "signature-preserving retarget" shape.
   - `raw_message_note_path(conversation_id, message_id, received)` —
     retargeted to resolve-first, deterministic-fallback: composes `resolve_
     thread_directory` first; writes under that directory's own `messages/`
     if found; falls back to the deterministic `thread_directory_paths(
     conversation_id)["messages"]` only for a genuinely brand-new Thread
     (no existing directory yet) — mirrors `resolve_meeting_note_path`'s own
     established two-tier "resolve, else deterministic-create-path" shape.
   - **Three real callers migrated off directly composing `thread_directory_
     paths(conversation_id)`** (Context point 2, above) — `raw_message_
     capture.capture_raw_thread_messages`'s existence check swapped for
     `resolve_thread_note_path`; `synthesize_thread`'s own `messages/` read
     reordered to derive from its ALREADY-resolved `existing_path`'s parent
     (falling back to the deterministic path only on the create branch);
     `meeting_classification._synthesize_history_entry`'s linked-Thread
     Summary read swapped for `resolve_thread_note_path`.
   - **`thread_directory_paths(conversation_id)` itself is UNCHANGED** —
     still the deterministic path a brand-new Thread is always FIRST created
     at, and still available for bulk/retrofit internal use (the PRD's own
     explicit carve-out: *"Bulk/retrofit operations may still use path-based
     lookup internally if needed"*). Thread's own directory-vs-single-file
     shape, its permanent `conversation_id` grouping key, the Stage 1/Stage 2
     split, and the write-once raw-message contract are all UNCHANGED —
     `ADR-048` Decision 3 is reopened for exactly ONE sub-decision (whether
     an already-existing Thread's CURRENT location is looked up by path or
     by scan), nothing else.
2. **A new, atomic whole-directory rename primitive**, one level up from
   `rename_thread_note`'s own existing single-file discipline:
   ```python
   def rename_thread_directory(old_directory: Path, new_directory: Path) -> Path:
       """No-op if old == new. Raises FileExistsError if new_directory
       already exists (a genuine <date> <subject> collision -- surfaced,
       never silently overwritten, mirroring rename_thread_note's own
       refuse-to-overwrite discipline one level up). Otherwise old_
       directory.rename(new_directory) moves the WHOLE tree -- concept
       file, messages/, any files/ -- in one atomic filesystem op, then
       the concept file inside is itself renamed from <old-slug>.md to
       <new-slug>.md, preserving the <slug>/<slug>.md invariant list_
       thread_notes() depends on. Returns the new concept file path."""
   ```
   The Rename Job computes each Thread's new slug as `<date> <subject-
   without-Re->` (e.g. `2026-08-16 Ewec Discussion`) from the Thread's own
   already-captured `thread_name`/`last_message_at` frontmatter — no hash
   suffix (unlike Meeting's/legacy Thread's own schemes, since a directory
   name's own collision surface is far smaller and a genuine collision is
   meant to surface, not be silently disambiguated away). The OLD `rename_
   thread_note`/`thread_note_path_for`/`thread_note_filename_stem`
   primitives (`ADR-046`) are left COMPLETELY UNTOUCHED by this ADR — still
   `thread_match_merge`'s own internal mechanism; see Consequences for why
   this pass does not touch them.
3. **Files/OKF backfill reuses `write_file_companion` (`REQ-SB-71-US-02`)
   UNCHANGED** — scans `staged_attachment_files(conversation_id, message_id)`
   for every raw message under a Thread's own (resolved, current)
   `messages/`, generating a companion for any attachment with none yet
   (idempotent — an already-companioned attachment is skipped). A new,
   structured `## Files` body section (filename/date/summary-blurb/link per
   companioned attachment) is a NEW `section_ownership.py` allow-list entry,
   distinct from `## Summary`'s own prose region.
4. **`## Related` ownership transfers wholesale.** `email_classification.
   synthesize_thread`'s own `section_ownership.py` allow-list entry narrows
   from `{"## Summary", "## Related"}` to `{"## Summary"}` alone, in the
   EXACT SAME change that registers the Librarian's own new `## Related`-
   writing caller id — never a window where both are simultaneously
   permitted (the exact race `REQ-SB-71-US-01`'s "one owner per section"
   guard exists to prevent, applied here to a header transferring ownership
   rather than a brand-new one). The Librarian's own `populate_thread_
   related_links` Job reuses `_build_thread_related_wikilinks`'s existing
   honest-omission contract (an unmatched participant is omitted, never
   guessed) and extends it with Decision 5's company-mention detection.
5. **Company-mention detection is a NEW, dedicated Compass call — technique-
   only reuse of `compass_client.summarize_content`, never `vault_filing_
   expert.determine_placement_and_file` itself.** That function decides
   WHERE ONE piece of brand-new content is filed (a single-item placement
   decision); this is a different-shaped problem — extracting WHICH already-
   known/plausible companies an already-filed Thread's own content mentions.
   Re-checked in Python against the live `known_customers`/`known_partners`
   lists before ever acting — never trusted from the model's own naming
   alone, mirroring `_maybe_create_cross_cutting_proposal`'s own exact
   discipline (`ADR-021` point 2):
   - **Genuinely new, unambiguous name** (no fuzzy/partial match against
     either known list) → auto-creates via `ensure_customer_hub_note`
     (`REQ-SB-63`, UNCHANGED) directly — Tier-1-shaped, no approval
     (Scenario 9).
   - **A name plausibly matching an existing entry under a different
     spelling, or model-flagged low-confidence** → a new Pending Approval,
     `action_id="propose_librarian_company_link"`, payload mirroring
     `_create_cross_cutting_proposal`'s own shape (`entity_type`,
     `entity_name`, `reason`, `thread_path`, `requesting_agent_id=
     "librarian-housekeeping"`), finalized by a new `finalize_librarian_
     company_link` handler performing the deferred create-or-link action on
     approval, nothing on decline (Scenario 10) — never a second, divergent
     placement/proposal mechanism (`ADR-021` point 2's own precedent, reused
     by analogy, exactly as `REQ-SB-63`'s own cross-cutting-proposal shape
     already reused it once).
6. **A new "Librarian" Section + `librarian-housekeeping` Agent, via the
   EXISTING, UNMODIFIED `section_registry.create_section`/`set_agent_
   section` mechanism (`REQ-SB-18`/`ADR-014`) — no new Section-creation
   machinery.** `create_section("Librarian")` → `"librarian"`;
   `agent_registry.create_agent("Librarian Housekeeping", type="worker",
   settings=[...])` → `"librarian-housekeeping"` (mirrors `email-capture-
   pipeline`'s own "worker" type + Pipeline-shaped settings-block
   convention); `set_agent_section("librarian-housekeeping", "librarian")`.
   `REQ-SB-61`'s own separately-deferred Location/Tags generalization is not
   built here, per this story's own explicit, cited-precedent scoping call.
7. **Five new capabilities, all on the NEW `"librarian-housekeeping"` Agent
   identity, reusing the EXISTING `app/api/email_poc_router.py`** (already
   this codebase's general home for flat, operator-triggered `/poc/*`
   operations regardless of subject area, `ADR-048` Decision 1's own
   precedent — no new sibling router): `POST /poc/librarian-rename-threads`,
   `/poc/librarian-backfill-files`, `/poc/librarian-populate-related`,
   `/poc/librarian-backfill-company-folders` (each independently, directly
   operator-triggerable), plus `POST /poc/librarian-run-housekeeping-pass`
   — the ORCHESTRATING capability (rename first, so downstream Jobs operate
   on each Thread's own final directory; the other three have no ordering
   dependency among themselves) — the ONE capability id Decision 8 targets.
8. **A REAL, deliberate `agent_schedule_registry` entry — the disclosed
   opposite of `REQ-SB-70`/`REQ-SB-71`'s own standing no-scheduler
   constraint, per the PRD's own explicit mandate that ongoing housekeeping
   should run itself, unlike operator-controlled capture:**
   ```python
   agent_schedule_registry.create_schedule(
       agent_id="librarian-housekeeping",
       capability_id="run_housekeeping_pass",
       interval_value=6, interval_unit="hours",
   )
   ```
   `interval_value=6` is a reasonable, operator-adjustable DEFAULT — never a
   locked-AC value (mirrors this codebase's own established "no locked AC
   tests a specific field value" pattern, e.g. `build_customer_concept_
   frontmatter`'s own `status`/`stale_after` defaults) — editable/pausable
   via the existing Schedule tab like every other `agent_schedule_registry`
   entry, and directly, manually triggerable too via Decision 7's endpoints.

**Alternatives Considered:**

1. **Fix only `resolve_thread_note_path` itself**, leaving `raw_message_
   note_path`, `raw_message_capture.py`'s existence check, `synthesize_
   thread`'s own `messages/` read, and `meeting_classification.py`'s linked-
   Summary read all directly composing `thread_directory_paths(conversation_
   id)`. Rejected — Context point 2's own direct-reading finding: all four
   would silently break (write to / read from a stale, since-renamed
   location) the FIRST time any Thread is renamed, defeating the whole point
   of Scenario 1/2's own "nothing orphaned, no duplicate" guarantee.
2. **Keep the deterministic path as the primary lookup, with a frontmatter-
   scan FALLBACK only when the deterministic path misses** (a hybrid, mirrors
   `resolve_meeting_note_path`'s own two-tier shape). Rejected for THIS
   specific case — a hybrid still requires the SAME scan cost on every
   post-rename lookup (the deterministic tier would miss every renamed
   Thread, every time, forever, not just once during a transition window
   the way `resolve_meeting_note_path`'s own legacy-EntryID fallback tier
   is a one-time historical artifact) — a plain, single-tier frontmatter
   scan is simpler and equally cheap at real steady-state volume, with no
   permanently-dead fast-path tier to carry forward.
3. **A new, parallel lookup primitive, migrating every real caller off
   `resolve_thread_note_path` entirely**, rather than retargeting `resolve_
   thread_note_path` itself in place. Rejected — `resolve_thread_note_path`'s
   own PUBLIC signature (`Path | None`, concept-file) is already exactly
   right for every existing caller; a signature-preserving retarget (mirrors
   `ADR-048` Decision 7's own established precedent for this SAME function)
   changes zero call sites, versus a parallel primitive that would need every
   caller migrated for no behavioral gain.
4. **Do NOT touch `thread_match_merge`/`email_capture_pipeline.py` at all,
   silently leaving Context point 3's own newly-discovered directory-
   orphaning risk undisclosed.** Rejected outright — this is exactly the
   class of finding this project's own established `ESC-022`/`ESC-025`/
   `ESC-046`/`ESC-048` precedent requires surfacing (*"a real, out-of-scope,
   root-caused defect discovered via due-diligence live verification does
   not block the task that found it"* — but it does require disclosure).
   `email_capture_pipeline.py` stays outside this story's own `## Files to
   Modify` (its own Non-Goals already name this), but the finding itself is
   escalated, not buried — see Consequences/`ESC-050`.
5. **Proactively retire `thread_match_merge`/rewire `process_staged_email`
   onto `capture_raw_thread_messages`/`synthesize_thread` as PART of this
   ADR**, closing `ESC-048` (and Context point 3's own sharper finding) by
   construction. Rejected for THIS story specifically — `ESC-048` already
   named this exact fix and left it as an explicit, open, human operational-
   priority call ("file a `/bug` now, or wait for a dedicated follow-up") not
   yet resolved; unilaterally deciding it here, inside a story whose own
   `## Files to Modify`/Non-Goals never named `email_capture_pipeline.py`,
   would be scope creep this project's own "coder is scope-bounded... any
   out-of-scope event escalates, no improvisation" rule (`Pipeline.md` hard
   rule 5) exists to prevent — even at the architect layer. The right move is
   sharpening the disclosure (Context point 3, Consequences, `ESC-050`), not
   silently absorbing someone else's already-recorded, still-open decision.
6. **Reuse `vault_filing_expert.determine_placement_and_file` directly for
   company-mention detection**, rather than a new, dedicated Compass call.
   Rejected — that function's own real contract is a SINGLE placement
   decision for ONE piece of brand-new content being filed right now; this
   Job needs to extract POTENTIALLY MULTIPLE company mentions from content
   that is already filed and stays exactly where it is — a genuinely
   different shape of question. Reusing the CALL TECHNIQUE (`compass_client.
   summarize_content` + Python-side re-check against live known-entity lists)
   while NOT reusing the function itself keeps `ADR-021` point 2's own "never
   a second, divergent PLACEMENT mechanism" promise intact — the placement/
   proposal shape (`ensure_customer_hub_note` direct-create vs. propose/
   finalize) is reused verbatim; only the upstream detection call is new.
7. **A new, dedicated Librarian router** (`app/api/librarian_router.py`),
   rather than reusing `email_poc_router.py`. Rejected — mirrors `ADR-048`
   Decision 1's own already-`Accepted` reasoning exactly: that router is
   already this codebase's general, subject-agnostic home for flat,
   operator-triggered `/poc/*` operations (`provision-vault-base`,
   `backfill-tags`, `flatten-customer-folders`, `migrate-customer-to-
   partner` already share it despite none being "email"-specific); a new
   sibling router would fragment an already-established convention for no
   real gain.
8. **Give each of the four Jobs (rename/files/related/company-folder) its
   own separate `agent_schedule_registry` entry**, rather than one
   orchestrating `run_housekeeping_pass` capability. Rejected — the PRD's
   own text frames this as ONE pipeline's ONE housekeeping pass, and the
   Rename Job's own output (each Thread's current directory) is what the
   other three Jobs need to operate against — a single scheduled entry
   running all four in a fixed, sensible order (rename first) is simpler and
   avoids four independent schedules racing each other over the same Thread.
   Direct per-Job triggering stays available via Decision 7's own separate
   endpoints for exactly this reason (operator wants to run just one Job).
9. **No hash suffix vs. a hash-suffixed rename slug** (mirroring Meeting's/
   legacy Thread's own `hash8(...)` disambiguation). Considered a hash
   suffix for parity — rejected: the PRD's own worked example
   (`2026-08-16 Ewec Discussion`) is explicitly hash-free, and a directory
   name's own collision surface (one Thread's own `<date> <subject>` vs.
   another's) is small enough that `rename_thread_directory`'s own
   raise-on-overwrite discipline is a sufficient, honest safety net —
   collisions surface for a human to notice and resolve, never silently
   hidden behind an opaque hash suffix.

**Consequences:**

- **`ADR-048` Decision 3 is PARTIALLY superseded** — its own "`resolve_
  thread_note_path` stays a deterministic existence check, permanently" sub-
  decision no longer holds; every other part of Decision 3 (Thread stays
  directory-shaped, permanently keyed by `conversation_id`, Stage 1/Stage 2
  split, write-once raw messages, the attachments-durable-persistence root
  staying keyed by `conversation_id` alone) is UNCHANGED and remains
  `Accepted`. `ADR-048`'s own text is left untouched (an Accepted ADR is
  never rewritten) — this ADR's own title records the partial supersession,
  mirroring `ADR-048`'s own identical practice when it partially superseded
  `ADR-042`/`ADR-046`.
- **A materially worse, ALREADY-LIVE risk against `thread_match_merge` is
  now on record, beyond `ESC-048`'s own original description** — directory-
  orphaning data corruption for any already-existing new-shape Thread the
  first time `thread_match_merge` runs against it, confirmed to already fire
  TODAY, independent of this ADR shipping. A new escalation (`ESC-050`) is
  appended (never editing the still-open `ESC-048`) reinforcing that `email-
  capture-pipeline` must stay `supervised` (or `thread_match_merge`'s own
  live call site must be retired, `ESC-048`'s own already-named fix) until a
  dedicated follow-up ships — a human operational-priority call, not decided
  by this ADR.
- **Bulk/retrofit Thread operations that compose `thread_directory_paths(
  conversation_id)` directly are UNCHANGED and remain valid** — this ADR
  narrows only the "does an already-existing Thread's CURRENT location need
  to be looked up" question; a genuinely bulk operation building brand-new
  Threads at their own deterministic path never needed the scan in the first
  place.
- **`resolve_thread_directory`/`resolve_thread_note_path`'s own cost is now
  O(number of Threads) per call, not O(1)** — an accepted, disclosed
  trade-off at real steady-state volume (~10 emails/hour, ~127 real Thread
  directories at the time of this ADR); a future material increase in Thread
  count (e.g. `REQ-SB-59`-style backfill onto pre-redesign flat-shape
  Threads) is a separate, disclosed concern (`ESC-048`) that may need this
  question revisited, not pre-solved here.
- **Every new capability this ADR introduces is reachable via a real `/poc/*`
  HTTP endpoint, operator-triggered, AND — unlike `REQ-SB-70`/`REQ-SB-71` —
  the orchestrating capability is ALSO wired to a real, configured recurring
  schedule** (`agent_schedule_registry`), the deliberate, disclosed exception
  to that prior batch's own standing no-scheduler constraint, per this
  requirement's own explicit PRD mandate.

---

## ADR-050: Chat rich-text rendering — `react-markdown`, a shared `ChatMessageText` component, and a default-safe (no raw-HTML) sanitization posture — first real delivery of `REQ-SB-32` (`BUGFIX-04-US-01`, `BUG-025`)

**Status:** Accepted
**Date:** 2026-08-19

**Context:** `BUG-025` (logged 2026-08-19, triaged into `BUGFIX-04-US-01`)
found all real chat surfaces in this codebase — Meeting Cockpit, Inbox
Cockpit (`Cockpit.tsx`, both mount points), and the Agents Map's embedded
agent chat panel (`AgentDetailPanel.tsx`) — render chat message text as a
raw literal string (`{message.text}`), so any markdown-formatted content
(`**bold**`, `- ` bullets, etc.) shows its literal syntax characters
instead of rendering as formatted text. Direct code + `package.json`
inspection (the triage analyst's own confirmed root cause, re-confirmed by
this architecture pass) established this is genuinely NET-NEW capability,
not a regression: `REQ-SB-32` ("Rich Text Rendering in Agent Chat"), the
PRD requirement this symptom maps to, was never actually spec'd or built
(`BACKLOG.md` row 53 unlinked, no story, no status; `Documentation/
PRD.md`'s own comment marks it an open discussion topic, explicitly
naming three open questions: which markdown subset, which rendering
approach/library, whether user messages also render). `package.json`
today lists no markdown/rich-text dependency at all (`react`, `react-dom`,
`react-router` only). `ESC-053` records this finding permanently.

The three open questions the PRD comment named were resolved directly by
the operator ahead of this architecture pass (recorded in
`BUGFIX-04-US-01`'s own `## Notes`, `gate: clear`, reasoning disclosed):
markdown subset = the common baseline a Compass-generated reply would
naturally produce (bold/italic, bulleted/numbered lists, links,
inline/block code, headings — not full CommonMark/GFM); library =
`react-markdown`; scope = both user- and agent-authored messages render
rich, symmetrically ("All Text Should be Rich Text in Chat," the
operator's own words, drawing no agent/user distinction). This ADR settles
the remaining architectural questions those resolutions did not cover:
exactly how the library is wired (plugin surface, sanitization posture —
the story's own Constraint explicitly names raw/unsanitized
`dangerouslySetInnerHTML` as a real, if latent, XSS surface the instant
ANY markdown-to-HTML rendering is introduced) and the component-structure
decision needed to avoid triplicating the same wiring across two real
files.

**Decision:**
1. **Library: `react-markdown`** (current stable v9.x, added as a real
   `src/frontend/package.json` dependency) — no additional remark/rehype
   plugin package (no `remark-gfm`, no `rehype-raw`, no `rehype-sanitize`).
   CommonMark's own default feature set, which `react-markdown` implements
   out of the box with zero plugins, already covers the operator-resolved
   subset (bold/italic/lists/links/code/headings) in full.
2. **Sanitization posture: default-safe by omission, not by an added
   sanitizer dependency.** `react-markdown` parses markdown to React
   elements directly and never invokes `dangerouslySetInnerHTML`, and it
   never parses/renders raw HTML embedded in message text unless the
   `rehype-raw` plugin is explicitly added to its plugin pipeline — this
   decision adds no such plugin, so the story's own Constraint is satisfied
   structurally, by the chosen wiring itself, not by layering a second
   sanitizer (e.g. DOMPurify) on top. Link/image URLs render through
   `react-markdown`'s own built-in `defaultUrlTransform`, unmodified — it
   already strips non-`http`/`https`/`mailto`/`tel` schemes from generated
   URLs by default, closing the `javascript:`-link-injection variant of the
   same risk, with no custom `urlTransform` override needed.
3. **One new shared presentational component,
   `src/frontend/src/components/ChatMessageText.tsx`**
   (`<ChatMessageText text={string} />`), consumed by exactly the two real
   chat-thread renderers that exist — `Cockpit.tsx`'s chat-thread map (both
   `chat-message--user`/`chat-message--agent` rows, symmetric — Meeting and
   Inbox Cockpit share this one component per `ADR-036`) and
   `AgentDetailPanel.tsx`'s chat-thread map (both `role === 'user'`/
   `role === 'agent'` rows, symmetric) — replacing each literal
   `{message.text}` in place. Confirmed by direct inspection that the
   Agents Map has no third, separate embedded-chat-panel component;
   `AgentDetailPanel.tsx` IS that surface — two call sites, not three,
   fully cover the story's own "all 3 chat surfaces" framing.
4. **Both user- and agent-authored messages render through the identical
   `ChatMessageText` component — no speaker/role-conditional branch** —
   directly implementing the operator's own symmetric resolution.

**Alternatives Considered:**
- `markdown-it` / `marked` (string→HTML markdown parsers) rendered via
  `dangerouslySetInnerHTML` — rejected: this is the exact pattern the
  story's own Constraint explicitly warns against; closing the resulting
  XSS gap would additionally require a real sanitizer (DOMPurify) as a
  SECOND new dependency, where `react-markdown`'s AST-to-React-element
  pipeline closes it with zero extra dependency.
- `remark`/`rehype` used directly (the same underlying engine
  `react-markdown` wraps, hand-assembled) — rejected: `react-markdown`
  already is exactly this pipeline, pre-wired for React with sane
  defaults; hand-assembling the same processor chain is pure reinvention
  for zero behavior difference at this project's actual scale (one
  chat-message-text rendering concern, not a general-purpose MDX/CMS
  pipeline).
- A hand-rolled regex-based bold/italic/list transformer (zero new
  dependency) — rejected: real, if narrow, correctness risk (nested or
  overlapping markdown constructs, escaping edge cases) for an
  already-solved problem; this project's own repeated "prefer an
  already-solved library over hand-rolled parsing" precedent (`ADR-005`,
  `ADR-008`, the MCP-SDK choice under "In-App Agent Orchestration") argues
  against it here too.
- `remark-gfm` added alongside `react-markdown` for tables/strikethrough/
  task lists — rejected for THIS pass: outside the operator-resolved
  "common baseline" subset; a cheap, additive follow-on if a future story
  needs it, not a blocker here.
- `rehype-sanitize` (or DOMPurify) layered on top of `react-markdown` as
  defense-in-depth — considered, not added this pass: `react-markdown`'s
  own no-raw-HTML-by-default posture already closes the concrete risk the
  story's Constraint names; adding a second sanitizer layer with no
  `rehype-raw`/raw-HTML path already in use would be speculative
  hardening against a risk that does not exist in this wiring today —
  revisit if a future story adds `rehype-raw` or any other raw-HTML
  rendering path.
- A separate, independently-configured `<ReactMarkdown>` call inline
  inside both `Cockpit.tsx` and `AgentDetailPanel.tsx` (no shared
  component) — rejected: identical wiring (same library, same
  zero-plugin configuration, same future sanitization surface) duplicated
  across two files is exactly the pattern this project's own established
  "one shared implementation, multiple call sites" precedent
  (`isBackgroundAgent`, the `SkillsTree.tsx` extraction under `ADR-039`)
  argues against; a single shared component means a future
  sanitization/plugin change happens exactly once.

**Consequences:**
- New frontend dependency: `react-markdown` (`src/frontend/package.json`)
  — the first markdown/rich-text dependency in this codebase. Verify the
  pinned version installs cleanly against this project's real Node/Vite
  toolchain (`ADR-002`) at real `npm install` time, not assumed.
- New shared component: `src/frontend/src/components/ChatMessageText.tsx`
  — the first component shared across features from a top-level
  `components/` location (`Cockpit.tsx` lives under `features/cockpit/`,
  `AgentDetailPanel.tsx` under `features/agents-map/`); exact folder
  precedent for future cross-feature components is decomposer/coder
  latitude, consistent with `ADR-010`'s "component structure grounded in
  real markup" convention, not a new architectural layer.
- `Cockpit.tsx` and `AgentDetailPanel.tsx` each gain one import plus one
  call-site substitution; no other file changes result structurally from
  this ADR.
- Formally begins satisfying `REQ-SB-32`'s own PRD Acceptance text for the
  first time. Per `BUGFIX-04-US-01`'s own `## Notes`, a human should
  decide whether to update `REQ-SB-32`'s PRD entry/`BACKLOG.md` row once
  this story ships — not decided by this ADR.
- Future GFM-feature requests (tables, strikethrough, task lists,
  footnotes) are a cheap, additive `remark-gfm` install landing in exactly
  one place (`ChatMessageText.tsx`), not a re-architecture.
- If a future story needs to render trusted, pre-sanitized raw HTML in
  chat (not requested by this story), that requires deliberately
  reopening Decision 2's "no `rehype-raw`" choice via a new/superseding
  ADR, not a silent plugin add.

---

## ADR-051: `process_staged_email` retargeted onto direct Stage 1/Stage 2 composition (`capture_raw_thread_messages` + `synthesize_thread`), with `detect_recurring_pattern`/`consult_librarian`/project-Glimpse-resync explicitly re-composed as direct calls, never re-implemented — closes `BUG-026`/`ESC-048`/`ESC-050` (`BUGFIX-05-US-01`) — supersedes `ADR-043` points 1 and 3 (live-execution/topology halves only — module location, Job function signatures, the Pending-Approval-payload deferred-write shape, and the Agent-tier identity model are unchanged, not reopened); reopens neither `ADR-046`, `ADR-048`, nor `ADR-049`

**Status:** Accepted
**Date:** 2026-08-19

**Context:** `BUG-026` (found live, triaged into `BUGFIX-05-US-01`) confirmed
by direct code reading — not restated from `ESC-048`/`ESC-050`'s own text
alone — that `process_staged_email` (the only capability the real, scheduled
`email-capture-pipeline` Agent invokes to process staged mail) still calls
`email_capture_pipeline.run_email_capture_pipeline()`, which still invokes
the module's compiled `StateGraph` and, through it, `email_classification.
thread_match_merge` — the exact legacy function `ADR-048`/`ADR-049` and
`architecture.md`'s own already-stated intent all named as due for
retirement, but which no story had actually rewired until now.
`thread_match_merge`'s own still-live create-vs-update check
(`resolve_thread_note_path`, now a frontmatter scan per `ADR-049`) either
silently creates a DUPLICATE Thread for a pre-redesign, flat-shape
conversation (`ESC-048`), or, on the update branch, computes a rename
target via its own still-live legacy `thread_note_path_for`/
`rename_thread_note` and moves only the concept file, ORPHANING an
already-migrated Thread's own `messages/`/`files/` subdirectories
(`ESC-050`, materially worse). `email-capture-pipeline`'s working mode has
been kept `supervised` since `ESC-048` specifically to contain this risk.

The replacement functions — `raw_message_capture.capture_raw_thread_
messages` (Stage 1, zero-Compass raw capture) and `email_classification.
synthesize_thread` (Stage 2, the real Compass-backed judgment) — already
exist, already work correctly (proven live via the `/poc` router), and
`synthesize_thread` already internally re-implements `thread_match_merge`'s
create-vs-update/customer-tags-participants/`## Summary` responsibilities
plus `route_to_project`'s own trigger (confirmed by direct reading of
`email_classification.py` lines 461-671 this pass) and the Files/OKF
companion write (`write_file_companion`, called from `synthesize_thread`'s
own end). But three of the old compiled graph's other real, unconditional
branch effects have NO equivalent anywhere in the new Stage 1/Stage 2
functions or in the `REQ-SB-72` Librarian housekeeping pipeline, confirmed
by direct reading of both:
- **`detect_recurring_pattern`** — fires once per newly arrived email
  (independent of Thread create/update), proposing a new standing Pipeline
  via Pending Approval. Nothing in `capture_raw_thread_messages`/
  `synthesize_thread`/`librarian_housekeeping.py` reads or acts on a
  message's own `recurring_candidate` classification signal.
- **`consult_librarian`** — fires on every Thread update, consulting the
  GENERALIZED Vault Filing Expert (`vault_filing_expert.determine_
  placement_and_file`, `ADR-021`/`REQ-SB-63`) against the Thread's own
  regenerated `## Summary`. This is NOT the same "Librarian" as `REQ-SB-72`'s
  new `librarian-housekeeping` Agent (confusingly similar name, unrelated
  mechanism/purpose — Thread rename/Files-backfill/`## Related`/company-
  folder-backfill vs. a generalized cross-cutting placement consult) —
  `REQ-SB-72` supplies no equivalent for this branch at all.
- **`trigger_project_synthesis`** (`project_customer_synthesizer.
  resync_project_from_thread`) — fires on every Thread update (created AND
  updated alike, per `REQ-SB-57` Scenario 1/AC-01), resynchronizing an
  already-routed Project's own `## Glimpse` from the Thread's current
  `## Summary`. `synthesize_thread` triggers `route_to_project` (the
  ROUTING proposal, created-only) but never this ongoing resync call.

Conversely, two of the old graph's branches ARE already, deliberately
superseded by the shipped `REQ-SB-71`/`REQ-SB-72` redesign and need no
equivalent on the new path: `summarize_attachment`'s inline, dated
`## Attachments` entries are superseded by the Files/OKF companion
mechanism (`write_file_companion`, called from `synthesize_thread`'s own
end, producing a first-class `files/<slug>/` companion note) plus the
Librarian's own structured `## Files` backfill (`REQ-SB-72-US-01-T04`) —
`## Attachments` itself does not exist in the new distilled concept-file
body shape at all (`architecture.md`'s own "Distilled concept file body"
list). `route_to_project`'s created-only Pending-Approval shape is already
preserved verbatim inside `synthesize_thread` itself, confirmed above.

**Decision:**

1. **`process_staged_email`'s own capability/Skill registration does NOT
   change.** `skill_registry.py`'s `"process_staged_email": skill_tools.
   process_staged_email` mapping, `skill_tools.process_staged_email`'s own
   signature (`agent_id: str`), and its deferred-import call site
   (`from app.business.pipelines.email_capture_pipeline import
   run_email_capture_pipeline`) all stay byte-for-byte unchanged — the fix
   is entirely inside `run_email_capture_pipeline`'s own function BODY, in
   the same module, under the same name and zero-argument call shape. Only
   its RETURN SHAPE changes (Decision 5) — a real, disclosed behavior
   change, not a signature change.
2. **`run_email_capture_pipeline()`'s body no longer builds or invokes
   `email_capture_pipeline.py`'s `StateGraph`.** It becomes a plain,
   sequential composing function: (a) calls `capture_raw_thread_messages
   (limit=...)` once (Stage 1); (b) derives the DISTINCT set of
   `conversation_id`s that received at least one genuinely NEW raw message
   this run (from Stage 1's own per-item processing — Stage 1's return dict
   gains one new, additive, backward-compatible key, `conversation_ids_
   touched: list[str]`, computed from its own already-in-scope per-item
   loop; its existing `processed`/`skipped_already_noted`/`pulled` keys are
   unchanged, so the `/poc/capture-raw-thread-messages` endpoint's existing
   response shape for any existing consumer is a pure superset, never
   broken); (c) for each such `conversation_id`, calls `synthesize_thread
   (conversation_id)` (Stage 2) — which, internally, already performs
   create-vs-update, customer/tags/participants, `## Summary`, the Files/OKF
   companion writes, and `route_to_project`'s created-only trigger.
3. **The three side effects with no equivalent elsewhere (Context above)
   are explicitly, directly re-composed in this SAME new function — never
   re-implemented, always calling through to the existing plain functions —
   mirroring `librarian_housekeeping.run_housekeeping_pass`'s own
   established "one orchestrator, direct sequential calls to existing plain
   Jobs" shape (`ADR-049` Decision 7), the closest existing precedent for
   composing several independent side effects around one pass over a
   corpus:**
   - **`detect_recurring_pattern`** — for each NEWLY captured raw message
     this run (Stage 1's `processed` list, not `skipped_already_noted`),
     the composing function reads back that message's own just-written raw
     note (frontmatter + body), reconstructs an `email`-shaped dict, and
     calls `classify_captured_email_with_fallback` once against it — a
     genuine, additional Compass classify call per new message, separate
     from `synthesize_thread`'s own internal, Thread-lifetime-scoped
     classify (which is always re-derived from the Thread's FIRST message,
     the wrong signal for a later message's own recurring-pattern check).
     When the resulting classification's `recurring_candidate` is true,
     calls `detect_recurring_pattern(email, classification)` exactly as
     before. This step is wrapped in its own try/except — its failure must
     never mark the enclosing Thread's own already-successful capture/
     synthesis as an error (mirrors the old graph's own "each branch
     terminates on its own, never gates another" invariant).
   - **`consult_librarian`** — called once per `synthesize_thread` call
     whose own result has `synthesized: True`, passing that result dict
     directly (the SAME shape `thread_match_merge`'s own result used to
     supply) — unconditional, fires for both a brand-new and an updated
     Thread alike, exactly as before. `consult_librarian` already has its
     own internal broad try/except (unchanged), so no additional wrapping
     is needed here.
   - **`project_customer_synthesizer.resync_project_from_thread`** —
     called once per synthesized Thread, passing `thread_result[
     "thread_path"]` directly (its own existing signature and internal
     "no-op for a not-yet-routed Thread" contract are both unchanged) —
     unconditional, mirroring `trigger_project_synthesis`'s own
     old graph-branch shape exactly. Wrapped in its own try/except for the
     same non-gating reason as the recurring-pattern step above.
4. **The whole per-`conversation_id` unit of work (Stage 2 plus its three
   composed side effects) is wrapped in ONE outer try/except at the loop
   level, mirroring `run_email_capture_pipeline`'s own existing per-email
   try/except+continue+honest-error-result posture** (now per-`conversation_
   id` instead of per-email) — a genuinely unexpected exception anywhere in
   that unit is caught, reported as `{"conversation_id": ..., "error": str}`,
   and the loop continues to the next `conversation_id`; it never aborts the
   whole tick's remaining Threads.
5. **Return shape changes from one row per fetched email to one row per
   synthesized Thread this run** — a real, disclosed behavior change.
   `skill_tools.process_staged_email`'s own consumption of this return value
   (`filed = [r for r in results if "error" not in r]`) is compatible
   as-is (same `"error"`-key-presence convention), but its own success
   message wording ("N email(s) filed") should be adjusted to reflect
   per-Thread granularity ("N thread(s) updated") — a task-level wording
   detail for the coder, not re-specified here. This granularity change is
   a net EFFICIENCY IMPROVEMENT for a burst of several new messages landing
   in the SAME conversation within one run: the old graph ran a full
   `thread_match_merge` (with its own Compass synthesis call) once per
   message; the new composition runs `synthesize_thread`'s own full
   reconstruction once per Thread, regardless of how many new messages
   landed in it this run.
6. **`email_capture_pipeline.py`'s `_build_graph()`/`_GRAPH`/`get_job_tree()`
   and `email_classification.thread_match_merge`'s own function body are
   DEPRECATED, not deleted.** `thread_match_merge` keeps its already-live
   `section_ownership.py` allow-list entry (`## Summary`, `## Related`) —
   nothing here changes `section_ownership.py`. Rationale: `get_job_tree()`
   (`REQ-SB-65-US-01`, the Agents Map's Pipeline Job Tree visualization) is
   a real, separate, currently-shipped read-only capability that reads the
   SAME compiled `_GRAPH` singleton via `langgraph`'s own `Pregel.
   get_graph()` introspection — deleting `_GRAPH` outright would break that
   surface as an uncontrolled side effect of a bugfix whose own `## Files
   to Modify`/Acceptance Criteria never mention it. Per `BUGFIX-05-US-01`'s
   own Non-Goals ("retiring `thread_match_merge`'s function body/definition
   itself... is a `/plan-tasks`-level judgement call"), this pass's own
   judgement is: keep it, but disclose (Consequences, below) that
   `get_job_tree()`'s own visualization now shows a topology that is no
   longer literally what executes — a known, disclosed staleness, not a
   silently-broken feature, consistent with this project's own "disclosed,
   not silently left broken" precedent (`ESC-048`/`ESC-050`,
   `architecture.md`'s "Disclosed, unresolved-by-this-pass regression
   risks" sections).

**Alternatives Considered:**

- **Retarget the compiled `StateGraph` itself** (rewire its nodes to call
  `capture_raw_thread_messages`/`synthesize_thread` instead of
  `thread_match_merge`, keeping `_GRAPH.invoke()` as the live mechanism).
  Rejected — Stage 1 (`capture_raw_thread_messages`) is its own,
  independently-triggerable, zero-Compass, no-shared-lock capability with
  its OWN internal `pull_and_stage_emails` call and its own dispatch-lock
  join (`ADR-048` Decision 3); forcing it inside a single per-email graph
  node would either duplicate that call per email (wrong — Stage 1 is
  meant to run ONCE per tick, batch-draining all currently-staged mail, not
  once per already-fetched item) or require a fundamentally different graph
  shape (a single Stage-1 pre-step feeding a per-Thread, not per-email,
  loop over `synthesize_thread`) that no longer resembles a per-email
  `StateGraph` at all — at which point LangGraph is providing no real
  structuring value over plain sequential composition, mirroring
  `librarian_housekeeping.run_housekeeping_pass`'s own already-`Accepted`
  precedent for exactly this shape (`ADR-049` Decision 7).
- **Delete `email_capture_pipeline.py`'s `StateGraph`/`get_job_tree()`
  and `thread_match_merge` outright in this same pass, rebuilding Pipeline
  Job Tree visualization against the new composed shape.** Rejected for
  THIS pass — out of `BUGFIX-05-US-01`'s own scope (no AC, no `## Files to
  Modify` entry names `agents_router.py`'s Job Tree endpoints or
  `AgentsMap`'s tree-visualization frontend); would turn a scoped bugfix
  into an unbounded second redesign. Named as a disclosed, recommended
  follow-up instead (Consequences).
- **Rename `run_email_capture_pipeline` to something that no longer implies
  "runs a LangGraph pipeline"** (e.g. `process_staged_threads`). Considered
  — the name is arguably misleading post-fix. Declined for minimal blast
  radius: the ONE real call site (`skill_tools.py`'s deferred import) would
  need a matching one-line change for zero functional gain: the name still
  accurately describes the function's OWN role/outcome ("runs the email
  capture pipeline," now Stage-1/Stage-2-composed instead of
  LangGraph-executed), not literally "invokes a `StateGraph` object."
- **Drop `detect_recurring_pattern`/`consult_librarian`/`resync_project_
  from_thread` from the new composed path entirely, treating them as
  consciously scoped out** (an option the story's own Constraints
  explicitly permitted, with a reason). Rejected — direct reading confirms
  none of the three has ANY equivalent anywhere in the shipped `REQ-SB-71`/
  `REQ-SB-72` redesign (unlike `summarize_attachment`, which genuinely IS
  superseded); silently dropping them would be a real, undisclosed
  capability loss the story's own Constraints explicitly warned against,
  not a deliberate redesign choice.
- **Have the composing function independently re-scan `email_staging` for
  `conversation_id`s instead of extending `capture_raw_thread_messages`'s
  own return shape.** Rejected — `capture_raw_thread_messages` calls
  `pull_and_stage_emails` INTERNALLY, at its own start, and removes every
  staged item (via `email_staging.remove_staged_email`) as it drains them;
  by the time it returns, nothing newly staged this tick remains in
  `email_staging` for an external caller to independently re-derive
  `conversation_id`s from — a pre-read (before calling Stage 1) would also
  miss anything `pull_and_stage_emails` itself newly staged THIS tick. The
  additive return-key extension is the only workable, non-duplicating
  option.

**Consequences:**

- `email_capture_pipeline.py`'s module-level docstring and
  `run_email_capture_pipeline`'s own docstring need a real rewrite to
  describe the new composed shape accurately — a task-level documentation
  correction for the coder, not spelled out here.
- **Disclosed, not fixed by this pass:** `get_job_tree()`'s Pipeline Job
  Tree visualization (`REQ-SB-65-US-01`, Agents Map) now reflects a
  topology (`Classify`→`Thread-Match/Merge`→...) that is no longer what
  `process_staged_email` actually executes — a real, known staleness,
  named here rather than silently left broken. Rebuilding it against the
  new Stage-1/Stage-2-plus-three-composed-side-effects shape is recommended
  as its own future, separately-scoped follow-up story; it does not block
  `BUGFIX-05-US-01`.
- `raw_message_capture.capture_raw_thread_messages`'s own return dict gains
  one additive key (`conversation_ids_touched`) — the `/poc/capture-raw-
  thread-messages` endpoint's response shape widens (a pure superset); no
  existing behavior/key is removed or renamed.
- Steady-state Compass call volume per newly captured message changes
  shape, not clearly up or down overall: the recurring-pattern classify
  step above adds one Compass call per NEW message (previously: one
  `Classify` call per email plus one `thread_match_merge` synthesis call
  per email = two per email, always); the new composition amortizes
  `synthesize_thread`'s own classify+synthesis calls once PER THREAD per
  run rather than once per message, a net improvement for any Thread
  receiving more than one new message in the same run. At this project's
  own real steady-state capture volume (~10 emails/hour, `ADR-049`'s own
  cited figure), this is not a material cost concern.
- Once this fix is verified live (`BUGFIX-05-US-01-T02`), `email-capture-
  pipeline`'s working mode is flipped back `supervised → autonomous`,
  resolving `ESC-048`/`ESC-050`'s own still-open severity note.
- `thread_match_merge`, `_build_graph()`, `_GRAPH`, and `get_job_tree()`'s
  current implementation all remain in the codebase, fully functional but
  no longer on any live execution path for real capture — confirming or
  retiring this dead-but-not-deleted surface entirely is a future,
  separately-scoped decision (mirrors `ADR-043`'s own already-`Accepted`
  precedent for `record_conversation_note`/`conversation_index.json`
  becoming dead code without being deleted in the same pass that retired
  its last live call site).

---

## ADR-052: `resolve_thread_directory()` recognizes a legacy, pre-redesign flat `Work/Threads/<name>.md` Thread note via a second scan tier, migrating it to the standard directory shape on first touch (self-healing, one-time, idempotent) — closes `ESC-055`'s own `AC-01` gap (`BUGFIX-05-US-01`) — extends `ADR-049` Decision 1 only (narrows its "purely read-only" framing for this one legacy-shape case; the frontmatter-scan-over-deterministic-path choice itself is unchanged, not reopened); reopens neither `ADR-048`, `ADR-051`, nor any other Decision

**Status:** Accepted
**Date:** 2026-08-19

**Context:** `BUGFIX-05-US-01`'s own decomposer pass (`/plan-tasks` step 2,
2026-08-19) found, by direct code reading corroborated by a real, live-vault
finding — not restated from `ADR-051`'s own text alone — that `ADR-051`'s
composed-function rewire does NOT actually close `BUG-026`'s duplication
facet (`AC-01`), because the gap lives one layer deeper than `ADR-051`
touches: `vault_writer.list_thread_notes()` globs `Work/Threads/*/*.md`
only, filtered to `path.parent.name == path.stem` — a flat, top-level
`Work/Threads/<name>.md` note (zero intermediate directory segments) can
never match this pattern. `resolve_thread_directory()`/`resolve_thread_
note_path()` (`ADR-049` Decision 1's own shared primitive, composing `list_
thread_notes()` alone, never a second enumeration mechanism) inherit this
SAME blindness, independent of which composing function calls them —
`thread_match_merge` OR the new `synthesize_thread`/`capture_raw_thread_
messages`. Confirmed already firing for real, not merely reasoned: the live
vault (`VAULT_PATH`) has 8 real, genuinely flat, pre-redesign `Work/
Threads/<name>.md` notes; one of them (`conversation_id
ED0954959F6F4A4C88F9E2ACA3D7113A`, "Azure-Net New Revenue Forecast for H2")
already has a SECOND, directory-shaped duplicate (`2026-08-17 Azure-Net New
Revenue Forecast for H2 for AM Updates/`) holding 4 of its own later
messages — `BUG-026`'s own duplication failure mode, already live. Full
finding: `ESCALATIONS.md` → `ESC-055`.

Before deciding HOW to close this, this pass re-verified (direct reading of
`email_classification.synthesize_thread`, `vault_writer.raw_message_note_
path`, and `vault_writer.write_file_companion`'s own call site) whether the
decomposer's own "leave a found flat note in place, just return its real
path" framing (`ESC-055`'s option (a)) is actually viable given the
EXISTING update-branch code, or only looks viable in the abstract. It is
NOT viable as-is: `synthesize_thread`'s own update branch derives `messages_
dir = existing_path.parent / "messages"`, and `write_file_companion` is
called with `thread_directory=path.parent` — for a flat note, `existing_
path.parent` is `Work/Threads/` ITSELF (the shared root all flat notes
live directly under), not a private per-Thread directory. Naively widening
`list_thread_notes()`/`resolve_thread_directory()` to return a flat note's
own parent as "its directory" would silently point EVERY currently-
unmigrated flat Thread's own new raw messages and Files/OKF companions at
ONE SHARED `Work/Threads/messages/`/`Work/Threads/files/` folder — a WORSE
data-integrity defect than the one being fixed here, one layer deeper into
exactly this bug's own "duplication vs. orphaning" failure family. The
"return its path unmigrated" option is therefore not the minimal-necessary
fix it first appears to be; a real (small, safe, self-healing) migration is
required for the existing downstream code to behave correctly at all.

**Decision:**

1. **A new primitive, `migrate_flat_thread_to_directory(flat_path: Path) ->
   Path`, in `vault_writer.py`.** Given an existing flat Thread note's own
   path (its `conversation_id` read from its own frontmatter), migrates it
   in place to the STANDARD directory shape at `thread_directory_paths(
   conversation_id)` — the SAME deterministic location a brand-new Thread
   is always first created at (reused unchanged, never a second naming
   derivation): creates the directory, moves/renames the flat file to
   `<slug>/<slug>.md`, creates an empty `messages/` subdirectory alongside
   it. Mirrors `rename_thread_directory`'s own already-`Accepted`
   refuse-to-overwrite discipline (`ADR-049` Decision 2) — raises
   `FileExistsError`, never silently overwrites, on the structurally
   near-impossible collision where the deterministic slug directory already
   exists. Returns the new concept-file path.
2. **`resolve_thread_directory(conversation_id)` gains a second scan tier,
   tried ONLY when the first (existing, `list_thread_notes()`-based,
   directory-shaped) scan finds no match.** The second tier globs `Work/
   Threads/*.md` directly (a new, small, dedicated glob for flat notes only
   — deliberately NOT folded into `list_thread_notes()` itself, Decision 4
   below) for a `frontmatter.get("conversation_id") == conversation_id`
   match, mirroring the first tier's own matching logic exactly. On a
   match, it immediately calls `migrate_flat_thread_to_directory` and
   returns the NEW directory — it never returns a flat file's own path or
   parent directly. This is a one-time, idempotent, self-healing write: the
   moment ANY caller resolves that `conversation_id` (via `resolve_thread_
   directory` or `resolve_thread_note_path`, both signature-unchanged, zero
   call-site edits anywhere — the SAME "signature-preserving retarget"
   shape `ADR-048` Decision 7 and `ADR-049` Decision 1 already each
   established once for this SAME function), the flat note permanently
   becomes a normal directory-shaped Thread for every future caller AND
   every future `list_thread_notes()`-based bulk Job (the Librarian's own
   Rename/Files-backfill/Related-backfill/company-folder-backfill Jobs) —
   no other caller anywhere in the codebase needs to change.
3. **Ordering is load-bearing.** The directory-shaped scan runs FIRST, the
   flat-note scan SECOND, only on a miss. This is what makes the mechanism
   correctly, silently no-op for a `conversation_id` that ALREADY has BOTH
   shapes (the already-manifested Azure Forecast duplicate, `ESC-055`) —
   the directory-shaped scan finds the existing duplicate and returns it,
   never attempting a redundant (and likely colliding) migration of the
   already-orphaned flat note. That already-diverged case is a deliberate,
   disclosed non-goal of this migration mechanism — a separate data-
   remediation decision, not folded in here (Consequences, and `ESC-055`'s
   own resolution note).
4. **`list_thread_notes()` itself is UNCHANGED.** Its own `Work/Threads/*/
   *.md`, `path.parent.name == path.stem` contract, and every one of its
   OWN direct callers (`list_threads_for_project`, the Librarian's own
   `rename_threads`/Files-backfill/`## Related`-backfill/company-folder-
   backfill Jobs) stay exactly as they are today — still correctly,
   deliberately directory-shape-only. Each sees a migrated former-flat-note
   automatically, for free, on its own next pass, the moment ANY `resolve_
   thread_directory` call has touched it — no special-casing needed
   anywhere else.
5. **`resolve_thread_directory`'s own docstring/contract is corrected, not
   silently left inaccurate.** It is no longer purely read-only; disclosed
   explicitly as "read-only for an already-directory-shaped Thread; a
   one-time, idempotent, self-healing migration WRITE for a legacy
   flat-shape Thread note, the one deliberate exception." This narrows
   `ADR-049` Decision 1's own "purely read-only... never creates, writes,
   or renames anything" framing for this ONE legacy-shape case only — the
   frontmatter-scan-over-deterministic-path choice itself, and every other
   real behavior of that Decision, are unchanged, not reopened.

**Alternatives Considered:**

- **Widen `list_thread_notes()` itself to glob both shapes, leaving a found
  flat note in place, unmigrated** (`ESC-055`'s own option (a), the
  decomposer's tentative "probably right" framing). Rejected — confirmed
  above, by direct reading, that a flat note's own parent directory (`Work/
  Threads/` itself) is not a private per-Thread directory; naively
  returning it as "the Thread's directory" would silently share ONE
  `messages/`/`files/` folder across every currently-unmigrated flat
  Thread — a WORSE data-integrity defect than `BUG-026` itself. It would
  also force every OTHER `list_thread_notes()` caller (the Librarian's four
  Jobs, `list_threads_for_project`) to grow its OWN flat-shape special-case
  handling, multiplying the blast radius rather than containing it at one
  primitive.
- **Proactive, eager migration of every existing flat note in one dedicated
  bulk pass, as part of THIS bugfix story** (`ESC-055`'s own option (b),
  taken literally as an upfront bulk operation rather than lazy/on-touch).
  Rejected for THIS story specifically — mirrors this project's own
  already-established "capture vs. backfill are separable concerns"
  precedent (`architecture.md`'s "Disclosed, unresolved-by-this-pass
  regression risks" section, `REQ-SB-67`/`REQ-SB-69`); a proactive bulk
  pass over the whole vault is squarely the Librarian's own scheduled
  housekeeping scope (`REQ-SB-72`), not a scoped primitive-lookup bugfix.
  Lazy, on-first-touch migration reaches the exact same end state
  incrementally and correctly, at zero extra code cost, the moment each
  flat Thread is next actually touched by a real new message.
- **Keep `resolve_thread_directory` strictly read-only; add a SEPARATE,
  second lookup-and-migrate function used only by `synthesize_thread`'s own
  call site.** Rejected — this codebase's own ADRs (`ADR-048` Decision 7,
  `ADR-049` Decision 1, each restated explicitly) repeatedly and
  deliberately reject "a second, independent Thread-enumeration/resolution
  mechanism"; a parallel primitive used by only one caller would
  immediately diverge from what `meeting_classification.py`'s linked-Thread
  lookup and `list_threads_for_project` see, recreating exactly the kind of
  blindness this ADR exists to close, one layer down.
- **A two-step, explicit API — callers detect a flat note via `resolve_
  thread_directory`, then separately, explicitly call `migrate_flat_thread_
  to_directory` themselves (e.g. gated to a Librarian-only capability).**
  Rejected — reintroduces the first Alternative's own "every caller must
  special-case this" blast radius for no real benefit; the migration itself
  is small, safe (mirrors `rename_thread_directory`'s own already-Accepted
  atomic-move-plus-refuse-to-overwrite discipline), and idempotent by
  construction — a Thread already migrated is simply a normal
  directory-shaped Thread on the very next call, indistinguishable from one
  that was always directory-shaped.
- **Give the migrated directory a human-readable stem directly** (`<date>
  <subject>`, matching the Librarian Rename Job's own eventual target)
  **instead of the deterministic `conversation_id` slug.** Rejected —
  reuses `thread_directory_paths(conversation_id)` completely unchanged
  rather than inventing a second naming derivation inside a migration
  helper; the Librarian's already-`Accepted`, already-scheduled `rename_
  threads()` Job (`ADR-049` Decision 2) renames it to the human-readable
  stem on its own very next scheduled pass anyway, exactly as it already
  does for every other freshly-created Thread — no duplicate logic, no
  special-casing.

**Consequences:**

- `resolve_thread_directory` (and therefore `resolve_thread_note_path`) is
  no longer literally side-effect-free for the legacy flat-shape case — a
  real, deliberate, disclosed one-time exception. Every one of its real
  callers (`meeting_classification.py`'s linked-Thread `## Summary` read,
  `_link_to_thread_by_conversation_id`, `_trigger_project_resynthesis`,
  not only `synthesize_thread`/`capture_raw_thread_messages`) may now
  trigger this migration as a side effect of what looks like a read — a
  deliberate choice (self-healing benefits every real caller, not only
  capture), disclosed here rather than silently narrowed to one call site.
- A genuine (structurally near-impossible) `conversation_id`-slug collision
  between an about-to-be-migrated flat note and an already-existing,
  differently-`conversation_id`'d directory at the SAME deterministic slug
  path raises `FileExistsError`, surfaced up through `resolve_thread_
  directory` to whichever caller triggered it. For `synthesize_thread`'s
  own real call path (`run_email_capture_pipeline`), `ADR-051` Decision 4's
  own already-existing per-`conversation_id` try/except already catches and
  reports this as `{"conversation_id", "error"}` without aborting the rest
  of the tick — zero new error-handling code needed at that layer.
- **The ALREADY-manifested, already-diverged duplicate
  (`ED0954959F6F4A4C88F9E2ACA3D7113A`, the Azure Forecast conversation) is
  NOT retroactively fixed by this migration mechanism — by design**
  (Decision 3's own ordering rule): the directory-shaped scan finds the
  EXISTING 08-17 duplicate first and returns it, permanently leaving the
  07-27 flat note's own single message un-migrated and un-merged. This is a
  deliberate, disclosed non-goal of this ADR, not an oversight — see
  `ESC-055`'s own resolution note for the separate data-remediation
  decision (deferred to the Librarian's future housekeeping scope, not this
  story).
- Of the 8 real flat Thread notes confirmed live in the vault at this pass,
  7 have no known directory-shaped counterpart yet and will each be
  correctly, automatically, losslessly normalized in place the next time a
  new message arrives for their own `conversation_id` — no human action
  needed. Only the 1 already-diverged case needs separate handling.
- Migration touches only filesystem SHAPE (directory creation, one file
  move/rename, one empty subdirectory creation) — never note body or
  frontmatter content — so no new `section_ownership.py` allow-list entry
  is implicated.

---

## ADR-053: Freshly-migrated flat Thread's pre-migration `## Summary` is preserved via a one-time, self-consuming `pre_migration_summary.md` sidecar — `migrate_flat_thread_to_directory` writes it, `synthesize_thread` folds it into its SAME existing Compass call and then archives it in place — closes `ESC-056`'s own gap (`BUGFIX-05-US-01`); narrows `ADR-052` Decision 1's "touches only filesystem SHAPE... never note body... content" framing for this one case; extends (does not reopen) `ADR-048`'s "full reconstruction, never a rolling/incremental delta" Stage 2 design; reopens neither `ADR-049`, `ADR-051`, nor any other Decision

**Status:** Accepted
**Date:** 2026-08-19

**Context:** `BUGFIX-05-US-01-T04`'s own live verification of `AC-01`
(`ESCALATIONS.md` → `ESC-056`) found, against a real Thread in the live
vault, that `ADR-052`'s migration mechanism does not actually satisfy
`AC-01`'s own locked "preserving its own prior content" clause once the
composed flow is run end-to-end. `migrate_flat_thread_to_directory`
performs exactly as `ADR-052` designed it — a pure filesystem-shape
move, the new `messages/` directory correctly empty, no content touched
— but that emptiness is exactly what breaks the very next step in the
SAME pipeline tick (`ADR-051`'s composition): `synthesize_thread` always
regenerates `## Summary` by FULL RECONSTRUCTION from every raw message
note currently under `messages/` (`ADR-048`'s own deliberate "never a
rolling/incremental delta" design, Alternatives Considered 6). For a
just-migrated flat Thread, `messages/` holds at most the ONE new message
that triggered the migration — so the first post-migration synthesis
regenerates `## Summary` from that one message alone, silently replacing
the flat note's own real, substantive, pre-migration Summary (written
over real history by the OLD `thread_match_merge` pipeline) with a
synopsis of a single new message. Confirmed live and fully repaired
before this decision (`Compass Alert- Failed API Calls`, byte-identical
restore, `ESC-056`).

This pass independently re-read `migrate_flat_thread_to_directory`,
`synthesize_thread`, `read_body_section`/`replace_body_section`, and
`section_ownership.py`'s `_CALLER_ALLOW_LISTS` before deciding, rather
than trusting `ESC-056`'s own three candidate options at face value —
each of the coder's own three options was evaluated directly against
this real code (see Alternatives Considered) and a fourth, narrower
design is adopted instead. Two structural facts, confirmed by direct
reading, shaped the decision:

1. **`synthesize_thread`'s `## Summary` regeneration is the ONLY
   at-risk section.** `## Related` ownership already transferred wholly
   to the Librarian's own Job (`ADR-049` Decision 4); `## Personal
   Notes`/`## Actions` are human-owned and never written by any agent
   path; the legacy `## Transcript` section is dead and untouched by
   `synthesize_thread` either way (confirmed directly, `ESC-056`). The
   fix therefore only needs to protect `## Summary` — not a general
   "preserve everything" mechanism.
2. **Frontmatter is the wrong storage for this content.**
   `read_note`/`_format_frontmatter_value` (`vault_writer.py`) parse and
   serialize frontmatter one `key: "value"` line at a time — a
   multi-paragraph Compass-generated Summary written as a frontmatter
   string value is not guaranteed to be a single line, and
   `_format_frontmatter_value` does not escape embedded newlines. Storing
   the preserved Summary text in frontmatter risks silently truncating
   it at the first embedded newline on the very next parse — the exact
   kind of silent content loss this decision exists to prevent, just
   moved one layer over. The preserved content must live in a body-shaped
   file instead, where multi-line text is safe by construction.

**Decision:**

1. **`migrate_flat_thread_to_directory` (`vault_writer.py`) gains one
   additional, narrow content-preservation step, run BEFORE the file
   move.** It reads the flat note's own pre-migration `## Summary` via
   the existing `read_body_section(flat_path, "## Summary")` primitive
   (no new reader). If non-empty, it writes that text VERBATIM to a new
   sidecar file, `<new-thread-directory>/pre_migration_summary.md` —
   created AFTER the target directory (`paths["directory"].mkdir(...)`)
   but BEFORE `flat_path.rename(paths["concept"])` — plain text, no
   frontmatter block, the same "reserved, non-frontmatter sidecar file"
   shape this codebase already established for `index.md`/`log.md`/
   `captures.md` (`ADR-042` point 1), just outside the OKF family. If the
   flat note's own `## Summary` is empty, no sidecar file is written —
   a true no-op, mirroring `read_body_section`'s own "absent is a valid,
   expected outcome" contract. This sidecar lives OUTSIDE `messages/`,
   never inside it — deliberately, so it is structurally invisible to
   `list_thread_notes()`'s own `path.parent.name == path.stem` filter and
   to `synthesize_thread`'s own `messages_dir.glob("*.md")` loop that
   builds its `messages` list (confirmed by direct reading: no code
   change needed in either place for exclusion by construction).
2. **`synthesize_thread` (`email_classification.py`) gains one small,
   additive, backward-compatible read, immediately before composing
   `full_content` for its existing Compass call.** It checks for
   `path.parent / "pre_migration_summary.md"`. If present, that file's
   text is prepended to `full_content` as an explicitly-labeled
   prior-history block, ahead of the real per-message content — the SAME
   existing `compass_client.summarize_content` call synthesizes `##
   Summary` grounded in BOTH the genuine pre-migration history and every
   real raw message, never a second Compass call, never a new function.
   Critically, this sidecar's content is READ directly by path — it is
   **never** added to the `messages` list itself, so it has zero effect
   on `first_message`/`classify_captured_email_with_fallback` (which
   still classifies against the real first raw message, unchanged),
   `existing_participants`, or `message_count` — confirmed by
   construction, closing a further, deeper risk this pass found (but
   `ESC-056` had not yet raised) in the coder's own option (a): folding
   a synthetic entry INTO `messages/` itself would have silently
   corrupted exactly those three things instead. On a **successful**
   synthesis only (the function's own existing `summary_error is None`
   boundary, unchanged), the sidecar is renamed in place to
   `pre_migration_summary.consumed.md` — never deleted, archive-not-
   delete, mirroring `ADR-047` Decision 2's own soft-delete convention at
   the smallest possible scope (a rename, not a move to
   `.second-brain/`, since this is genuinely Thread-scoped, human-
   relevant provenance worth keeping visibly alongside the Thread
   itself). This is what makes the fold-in happen EXACTLY ONCE — every
   later `synthesize_thread` call for the same Thread finds no
   `pre_migration_summary.md` (only the renamed, no-longer-matching
   `.consumed.md`) and reverts to `ADR-048`'s normal, unmodified full-
   reconstruction-from-`messages/`-only behavior. On a **failed**
   synthesis (`summary_error` set, existing `## Summary` left untouched,
   unchanged), the sidecar is deliberately NOT renamed — it stays
   pending, exactly as the Thread's own existing Summary also stays
   pending, so a transient Compass failure can never silently drop the
   preserved history either; the next successful run picks it up.
3. **`list_all_note_paths()` (`vault_writer.py`) is extended to exclude
   both `pre_migration_summary.md` and `pre_migration_summary.consumed.md`
   by filename**, the same mechanism (and, if the implementer chooses, the
   same set — or a clearly-named sibling set — `list_all_note_paths`
   already checks for `index.md`/`log.md`/`captures.md`) — so this
   plain, non-frontmatter sidecar is never surfaced to callers that
   iterate "every real note" (search/browse indexing, Librarian Jobs)
   expecting `read_note()`'s ordinary `type:`-bearing shape. `read_note()`
   itself does not crash on it either way (its own `if not text.
   startswith("---\n"): return {}, text` fallback already handles a
   frontmatter-less file gracefully) — this exclusion is about correct
   "is this a real note" semantics for vault-wide listings, not crash
   safety.
4. **No `section_ownership.py` change.** The sidecar file is not written
   via `replace_body_section` and carries no `## `-level header of its
   own — `synthesize_thread`'s existing `## Summary`-only allow-list
   entry (`email_classification.synthesize_thread`) is unchanged and
   remains the only writer of the concept file's own `## Summary`
   region; the sidecar mechanism sits entirely outside the header-
   ownership system by design, never a second writer of a governed
   header.
5. **`ADR-052` Decision 1's "touches only filesystem SHAPE... never note
   body or frontmatter content" framing is narrowed, not rewritten** —
   mirroring `ADR-052` Decision 5's own already-established pattern of
   disclosing a narrow, one-time exception to a prior Decision's
   framing rather than reopening it: `migrate_flat_thread_to_directory`
   now also writes ONE piece of real body content (the pre-migration
   `## Summary`, verbatim, to its own new sidecar file) — but never
   touches the migrated concept file's own body or frontmatter, and
   never touches anything for a flat Thread whose own `## Summary` was
   already empty. Every other real behavior of `ADR-052` Decision 1
   (target-directory resolution, refuse-to-overwrite discipline, the
   deterministic `thread_directory_paths` reuse) is unchanged.

**Alternatives Considered:**

- **`ESC-056`'s own option (a) — back-fill ONE synthetic raw message note
  under the new `messages/` directory, reconstructed from the flat
  note's pre-migration content.** Rejected, on two independent grounds
  found by this pass's own direct reading (beyond the coder's own
  disclosed "stretches `create_raw_message_note`'s verbatim-real-email
  contract" concern): first, it would still need `type: RawMessage`-
  shaped frontmatter with fabricated `sender`/`sender_email`/
  `message_id` fields to be readable by `synthesize_thread`'s existing
  loop, misrepresenting reconstructed content as a genuine captured
  email — a real, disclosed integrity concern, not just a stylistic one;
  second, and more load-bearing, it would sort into the SAME `messages`
  list `synthesize_thread` uses for `first_message`/classification and
  `existing_participants` accumulation — silently changing which message
  classification runs against (a real, adjacent risk this pass found
  independently of `ESC-056`'s own write-up) and inflating `message_count`
  permanently. This ADR's own sidecar-file design achieves the SAME
  grounding benefit (real prior history fed into the SAME Compass call)
  with none of these side effects, by construction, since the sidecar
  never enters `messages_dir` at all.
- **`ESC-056`'s own option (b) — `synthesize_thread` detects a Thread
  with pre-existing `## Summary` and no raw messages, and MERGES via an
  additional Compass call or prose concatenation.** Rejected as a
  DISTINCT mechanism from this ADR's own Decision 2 in one important
  way: a second Compass call doubles synthesis cost for every real
  migration event (small, but avoidable) and a plain prose concatenation
  (no Compass call at all) would produce a disjointed, un-synthesized
  `## Summary` rather than one coherent picture — this ADR's Decision 2
  achieves the same "merge old and new" outcome through the EXISTING
  single Compass call instead, by extending its input grounding, not
  its call count or its output shape.
- **`ESC-056`'s own option (c) — copy the pre-migration `## Summary`
  directly into the new concept file's own `## Summary` region as part
  of migration, and change `synthesize_thread` to APPEND/update-in-place
  rather than wholesale-replace when a Thread has no raw messages yet
  but a non-empty `## Summary`.** Rejected — writing directly into the
  concept file's own `## Summary` region from `migrate_flat_thread_to_
  directory` would make `vault_writer.py` a SECOND, uncoordinated writer
  of a header `section_ownership.py`'s allow-list already scopes to a
  specific, registered caller id (`email_classification.synthesize_
  thread`) — exactly the pattern `ADR-042` point 2 / `ADR-048` Decision 2
  exist to prevent (a header's writers must be enumerable via the
  allow-list, not discoverable only by reading every call site). The
  sidecar-file design keeps `## Summary` written by exactly one caller,
  through exactly one primitive (`replace_body_section`), unchanged.
- **A general "`synthesize_thread` always grounds on the Thread's own
  current `## Summary`, not only after a migration" mechanism** (a
  broader version of option (c), reopening `ADR-048`'s own "full
  reconstruction, never a rolling/incremental delta" Alternatives
  Considered 6 decision). Rejected outright — `ADR-048`'s own reasoning
  for reversing away from rolling/incremental synthesis (`REQ-SB-67`'s
  prior design) is not reopened by this ADR; this fix is a one-time,
  self-consuming exception scoped EXCLUSIVELY to a freshly-migrated flat
  Thread's own pre-migration history (real content with no other
  representation anywhere under `messages/`), never a standing "read
  your own prior AI output as rolling context" mechanism for ordinary,
  steady-state Thread updates.
- **A stateful frontmatter marker (e.g. `migrated_summary_pending:
  true`) instead of a sidecar file's own existence as the "has this been
  folded in yet" signal.** Rejected — the marker and the preserved text
  would be two separately-written pieces of state (`upsert_frontmatter_
  key` plus a body/file write), not atomically related; a crash between
  the two writes could leave a marker with no content, or content with
  no marker, either of which is a worse, subtler failure mode than the
  sidecar file's own existence doubling as both the content AND the
  state signal in one write.
- **Copy the ENTIRE pre-migration note (not just `## Summary`) to a
  separate `.second-brain/migration_backup/` archive, mirroring `ADR-047`
  Decision 2's own full-note soft-delete precedent exactly.** Considered
  and rejected as unnecessary redundancy, not principle: this pass
  confirmed by direct reading (Context, above) that `## Summary` is the
  ONLY section any live code path overwrites — `migrate_flat_thread_to_
  directory` itself already preserves every other section losslessly
  (a pure rename, `ADR-052`'s own already-accepted, already-correct
  design), so a second, whole-note backup mechanism would duplicate a
  guarantee that already holds for everything except the one section
  this ADR's own sidecar already protects. Revisit if a future finding
  identifies a SECOND at-risk section.

**Consequences:**

- A freshly-migrated flat Thread's directory carries one extra file,
  `pre_migration_summary.md` (later renamed `pre_migration_summary.
  consumed.md`), for exactly one synthesis cycle's worth of time in the
  common case — a small, disclosed, permanent addition to the Thread
  directory's own file inventory, visible to the operator directly in
  Obsidian (a deliberate, human-legible provenance trail, not hidden
  state).
- `synthesize_thread`'s own Compass prompt grows by the length of the
  preserved prior-history text on exactly the ONE call where the sidecar
  is present — a real, disclosed, one-time cost, not a standing one
  (`ADR-048`'s own steady-state full-reconstruction cost profile is
  otherwise unchanged).
- If `migrate_flat_thread_to_directory` fails or crashes strictly between
  writing the sidecar file and renaming the flat note into place, the
  target directory is left holding only the sidecar file while the
  original flat note remains fully intact, untouched, at its original
  location (no data loss) — but a retry immediately raises
  `FileExistsError` per the existing refuse-to-overwrite guard
  (`paths["directory"].exists()`), the SAME already-accepted,
  already-disclosed non-atomic-multi-step risk profile `ADR-052`'s own
  migration and `rename_thread_directory` both already carry; this ADR
  does not add new transactional/rollback machinery, consistent with
  that already-accepted risk posture.
- The decomposer must re-lock `BUGFIX-05-US-01-AC-01` against this
  concrete design and create/amend a task touching BOTH `app/data_access/
  vault_writer.py` (the sidecar write in `migrate_flat_thread_to_
  directory`, plus the `list_all_note_paths()` exclusion) AND `app/
  business/email_classification.py` (`synthesize_thread`'s own new
  sidecar read/consume step) — a deliberate, disclosed departure from
  `BUGFIX-05-US-01-T01`'s own task-level Constraint ("must NOT modify
  `email_classification.py`"), which was scoped to `T01`'s own narrower
  rewire concern, not a standing architectural prohibition; this ADR is
  the architecture-level decision that supersedes that task-level
  boundary for this one, narrow, additive change only. `ADR-051`'s own
  Decision (the composed-function rewire itself) is not reopened.
- Recommended live-verification target for the replacement/amended `T04`:
  the SAME `Compass Alert- Failed API Calls` conversation `ESC-056` found
  and already fully repaired (byte-identical), or any other of the 6
  remaining real flat Threads confirmed live with no known
  directory-shaped duplicate — verifying that the migrated Thread's `##
  Summary` afterward reflects BOTH the real pre-migration history AND
  the new message's own content, not one or the other, and that the
  sidecar file is correctly renamed to `.consumed.md` afterward, never
  deleted.

---

## ADR-054: Bidirectional Thread ↔ Message Linking (`REQ-SB-73`) — a new `link_thread_messages()` Librarian Job (`## Messages` + `thread:` backlink, retrofit + self-heal), a bounded `rename_threads()` fan-out extension for a zero-staleness-window guarantee, and a `vault_indexing.py` outgoing-wikilink extension to also scan frontmatter string values — extends `ADR-049` Decisions 2/3/4/7 and `ADR-024`; reopens none of them

**Status:** Accepted
**Date:** 2026-08-19

**Context:** `REQ-SB-73-US-01`'s own text settles every SCOPE-level question
directly with the operator (retrofit-first priority, the fan-out rename-
safety design) and explicitly leaves four MECHANISM-level questions to
`/plan-tasks` (see the story's own `## Notes`). Direct reading of the real,
current code — `librarian_housekeeping.py`, `vault_writer.py`,
`section_ownership.py`, and (found independently, not named by the story)
`vault_indexing.py` — resolves three of those four by REUSE of an
already-established primitive, with zero new `vault_writer.py` code:

1. **Header insertion** — `insert_body_section_if_missing` (`REQ-SB-72-
   US-01-T04`) already IS the generic "idempotent top-up-only-if-absent for
   a whole `## `-level header" primitive this story's own `## Messages`
   needs; `backfill_files`'s own two-call sequence (`insert_body_section_
   if_missing` then `replace_body_section`) is reused verbatim, not
   reinvented.
2. **The `thread:` backlink write (new AND stale-correct, Scenarios 3/5)
   AND the rename fan-out (Scenario 4)** — `vault_writer.upsert_
   frontmatter_key(path, "thread", value) -> bool` (already shipped,
   `REQ-SB-09`/used live by `meeting_classification.py`'s own `thread:`
   field) already provides EXACTLY the semantics both scenarios need in
   one primitive: inserts if absent, overwrites in place if present with a
   DIFFERENT value (self-heals a stale slug), and is a true no-op —
   returns `False`, writes nothing — if the value already matches
   (Scenario 6's idempotency). `insert_frontmatter_key_if_missing` (the
   OTHER existing top-up primitive, used by every baseline-field top-up in
   this codebase) was considered and rejected for this one field
   specifically, because it never touches an already-present key — it
   cannot self-heal a stale post-rename value at all, which Scenario 5
   requires.
3. **A genuinely new architectural gap, found independently by this pass,
   not named by the story:** the story's own `## Affected Screens` asserts
   the already-shipped backlinks panel/graph view (`REQ-SB-14`) will
   surface the new `thread:` wikilink "automatically, with no prototype
   change needed." Direct reading of `vault_indexing.py::_build_entry`
   (`ADR-024`'s own indexing mechanism, the ONE substrate both the
   backlinks panel and the graph view read, via `vault_search.py`) finds
   this claim is NOT currently true: `outgoing_wikilinks` is computed as
   `vault_writer.extract_wikilink_targets(body)` — BODY ONLY. Every
   existing wikilink convention in this codebase (`**Customer:** [[Hub]]`,
   `**Attendees:** [[P1]], [[P2]]`, `index.md`'s own listing) lives in a
   note's BODY; there is no precedent anywhere in this codebase for a
   wikilink embedded as a FRONTMATTER field's own string value — which is
   exactly what the story's own Gherkin requires `thread:` to be (every
   Scenario says "frontmatter `thread:` field," never a body line). Left
   unaddressed, a Thread's own real, correctly-written `thread:` value
   would be silently invisible to both the backlinks panel and the graph
   view — breaking the story's own foundational premise, not a cosmetic
   gap.

**Decision:**

1. **`link_thread_messages()`** (new, `librarian_housekeeping.py`) — for
   every real Thread (`list_thread_notes()`), regenerates `## Messages`
   wholesale from the Thread's own CURRENT `messages/*.md` glob (sorted,
   mirroring every sibling Job's own chronological-by-filename ordering) as
   `"- [[<message-stem>]]"` bullets, via `insert_body_section_if_missing`
   + `replace_body_section(..., caller="librarian_housekeeping.link_
   thread_messages")` — never incrementally patched (Scenario 2), mirroring
   `## Files`'s own "regenerated each pass" contract exactly. For every
   message under that same glob, calls `vault_writer.upsert_frontmatter_
   key(message_path, "thread", f"[[{concept_path.stem}]]")` — the Thread's
   own CURRENT stem (already-final if this Job runs after the Rename Job in
   the same pass), satisfying the write-new (Scenario 3), self-heal
   (Scenario 5), and true-no-op-on-rerun (Scenario 6) requirements from one
   existing primitive, zero new `vault_writer.py` code.
2. **`rename_threads()` fan-out extension** (`librarian_housekeeping.py`,
   bounded addition to the ALREADY-Accepted `ADR-049` Decision 2 Job) — the
   ONE deliberate exception to Decision 1 above's "read the Thread's
   already-final directory" assumption: on a successful `rename_thread_
   directory` call, in the SAME loop iteration (never a separate pass, never
   `link_thread_messages()`'s own next scheduled run), globs the renamed
   Thread's own (now-current) `messages/*.md` and calls `upsert_frontmatter_
   key(message_path, "thread", f"[[{new_concept_path.stem}]]")` for each —
   a genuinely NEW invariant `ADR-049` Decision 2 did not provide (its own
   shipped docstring is explicit: "touches nothing INSIDE `messages/`",
   confirmed live) — a zero-staleness-window guarantee, not merely
   "eventually consistent via the next scheduled `link_thread_messages()`
   pass." `rename_threads()`'s own external contract (return shape,
   collision handling, idempotent-skip-if-already-renamed) is otherwise
   unchanged.
3. **`section_ownership.py` gains one new `_CALLER_ALLOW_LISTS` entry:**
   `"librarian_housekeeping.link_thread_messages": frozenset({"## Messages"})`
   — mirrors `backfill_files`/`populate_thread_related_links`'s own exact
   precedent (one new caller id, registered in the SAME change that
   introduces the new header), least-privilege, deny-by-default.
4. **Job-chain placement:** `link_thread_messages()` runs SECOND in `run_
   housekeeping_pass()`, immediately after `rename_threads()` and before
   `backfill_files()`/`populate_thread_related_links()`/`backfill_company_
   folders()` — grouping the two Jobs that together own the Thread↔Message
   relationship (the rename fan-out handles the write-path staleness
   guarantee; this Job is the retrofit + ongoing self-healing vehicle for
   every OTHER path a message's `thread:` field can go missing or stale)
   adjacent in the chain, for readability — not load-bearing for
   correctness, since Scenario 4's own fan-out already keeps `thread:`
   correct independent of ordering, and this Job's own `## Messages`
   regeneration has no dependency on Files/Related/Company-folder state
   either. New endpoint: `POST /poc/librarian-link-thread-messages`,
   mirroring the existing `/poc/librarian-*` convention exactly (`ADR-049`
   Decision 7).
5. **`vault_indexing.py::_build_entry` is extended to also scan frontmatter
   STRING (and list-of-string) values for `[[...]]` targets**, composed
   additively onto the existing body scan:
   `outgoing_wikilinks = extract_wikilink_targets(body) + <targets found in
   any frontmatter string value or string-list element>` — reusing `vault_
   writer.extract_wikilink_targets` unchanged (it is already a pure regex
   match over any string, agnostic to body vs. frontmatter origin), never a
   second, divergent wikilink-detection mechanism. Strictly additive/
   behavior-preserving for every existing note (a note with no wikilink-
   shaped frontmatter value contributes zero extra targets, byte-identical
   to today), mirroring `list_all_note_paths()`'s own "generalize without
   reopening the underlying invariant" precedent (`Implementation/
   Learnings.md`, `SPRINT-048`) — this is why it does NOT need its own ADR
   as a standalone decision; it is folded into this ADR only because
   `REQ-SB-73`'s own Scenario 3/4/5 correctness genuinely depends on it,
   named here so the decomposer adds `vault_indexing.py` to this story's
   own file scope rather than discovering the gap mid-build.

**Alternatives Considered:**

- **A new, dedicated `vault_writer.py` primitive for the `## Messages`
  write, distinct from `insert_body_section_if_missing`/`replace_body_
  section`.** Rejected — those two primitives are already fully generic
  over ANY header string; writing a second, `## Messages`-specific pair
  would duplicate `## Files`'s own already-proven mechanism for zero
  benefit, violating this codebase's own repeated "generic primitive
  first, kind-specific wrapper second" pattern (`Implementation/
  Learnings.md`, `SPRINT-048`).
- **A dedicated `set_thread_backlink()`-style wrapper around `upsert_
  frontmatter_key` for the `thread:` write**, instead of calling the
  generic primitive directly from both `link_thread_messages()` and the
  `rename_threads()` fan-out. Rejected as premature — both call sites
  compute the SAME `f"[[{stem}]]"` value shape inline from an
  already-in-scope `concept_path`/`new_concept_path`, a one-line
  expression; a wrapper function would add an indirection layer with no
  real shared logic beyond string formatting.
- **Writing `thread:` as a body line (`**Thread:** [[...]]`), mirroring
  `**Customer:** [[Hub]]`, instead of a frontmatter field** — would have
  sidestepped the `vault_indexing.py` gap entirely (body wikilinks are
  already indexed). Rejected — the story's own Gherkin explicitly and
  repeatedly locks this to a FRONTMATTER field (every Scenario says
  "frontmatter `thread:` field"), and a note's raw `RawMessage` body is the
  immutable, verbatim email content (`ADR-048` Decision 3's own "preserved
  byte-for-byte, forever" contract for `create_raw_message_note`) — a body
  line would be the one thing on that note ever agent-written, a real,
  disclosed tension with that Decision this ADR avoids entirely by keeping
  the link in frontmatter, at the cost of the `vault_indexing.py` fix
  above.
- **Fixing the `vault_indexing.py` gap by teaching `_build_entry` about the
  `thread:` key BY NAME specifically**, instead of generically scanning
  every frontmatter value. Rejected — a named-key special case would need
  to be revisited every time a future note kind introduces its own new
  frontmatter-wikilink field (already a realistic near-term shape: Meeting's
  own `thread:` field currently stores a bare `conversation_id`, not a
  wikilink, but could plausibly be redesigned the same way later); the
  generic scan handles any future frontmatter-wikilink field for free, with
  the same "superset of the old result, byte-identical for every note
  without one" safety property `list_all_note_paths()`'s own generalization
  already established.
- **A separate, one-time backfill Job/endpoint distinct from the ongoing
  self-healing Job**, mirroring `REQ-SB-72-US-01-T09`'s pattern of a
  standalone retrofit script. Rejected — the story's own Constraints are
  explicit ("the single vehicle for both the one-time retrofit... AND
  ongoing self-healing," `MEMORY.md`'s own "no script workarounds, API-
  first" constraint) and `backfill_files`'s own precedent already proves
  one idempotent Job serves both purposes with zero special-casing.

**Consequences:**

- Zero new `vault_writer.py` primitives — `link_thread_messages()` and the
  `rename_threads()` fan-out extension are pure composition of
  already-shipped primitives (`insert_body_section_if_missing`, `replace_
  body_section`, `upsert_frontmatter_key`, `list_thread_notes`).
  `vault_indexing.py::_build_entry` gains one small, additive helper.
- The `vault_indexing.py` extension is retroactive: any note ANYWHERE in
  this vault that already happens to carry a `[[...]]`-shaped frontmatter
  string value (none currently do, confirmed by this codebase's own
  established conventions above) becomes newly indexed the next time
  `rebuild_index()` runs — a disclosed, intended, behavior-preserving
  widening, not a narrow one scoped to `thread:` alone.
- `rename_threads()`'s own per-Thread try/except-and-continue collision
  handling is unaffected by the fan-out addition — a message's own `thread:`
  fan-out write happens only AFTER `rename_thread_directory` itself has
  already succeeded for that Thread, so a genuine `<date> <subject>`
  collision (caught, skip-and-report) never leaves any message mid-way
  through a fan-out.
- Future work: `Meeting`'s own `thread:` frontmatter field (currently a bare
  `conversation_id`, not a wikilink — confirmed live, `meeting_
  classification.py`) is a natural, NOT-in-scope-here candidate to migrate
  onto the same real-wikilink convention this ADR establishes, now that
  `vault_indexing.py` can index it generically; named for a future story,
  not built here.

---

## ADR-055: Customer Backfill (`REQ-SB-74`) — a batched, multi-target Pending Approval payload convention (reuses the existing generic registry/dispatch mechanism unmodified, no schema change), a new whole-OKF-directory cross-parent archival-move primitive, a new `list_customer_folders()` enumeration, and a new narrower-sibling Compass Customer-match call — extends `ADR-021` point 4, `ADR-027` point 4, `ADR-042` point 1, and `ADR-049` Decision 5; reopens none of them

**Status:** Accepted
**Date:** 2026-08-19

**Context:** `REQ-SB-74-US-01`'s own text settles every SCOPE-level
question directly with the operator (archive-then-backfill order,
propose-then-approve posture, Customer-tag-only scope) and names five
MECHANISM-level questions for `/plan-tasks` (story `## Notes`). Direct
reading of the real, current code — `pending_approval_registry.py`,
`pending_approvals_router.py`, `customer_hub_linking.py`, `project_
customer_synthesizer.py`, `compass_client.py`, and `vault_writer.py` —
resolves all five, three by confirming an already-generic mechanism needs
NO change and two by a new, narrowly-scoped primitive:

1. **The batched-per-Customer payload shape needs NO registry/schema
   change at all — confirmed by direct reading, not assumed.**
   `pending_approval_registry.create_pending_approval(agent_id, trigger,
   action_id, description, payload: dict | None = None)` already stores
   `payload` as an opaque, additive dict (`ADR-021` point 4's own framing);
   `pending_approvals_router.py`'s Approve/Decline endpoints and its
   `_APPROVAL_HANDLERS` dispatch table are already fully target-shape-
   agnostic — `_APPROVAL_HANDLERS[action_id](record["payload"])` passes
   the WHOLE payload dict straight to the registered handler, which decides
   for itself what to do with it. Every existing proposal kind happens to
   use a payload naming ONE target note purely by convention, never by any
   structural constraint in the registry or the router. This is a genuinely
   new, precedent-setting CONVENTION worth recording (this is the first
   multi-target proposal kind in this codebase, and it sets the shape every
   future one should follow), even though it required zero code change to
   the mechanism itself.
2. **The exact Customer-match detection call** — `classify_task(subject,
   body, known_customers, prompt_override)` (`ADR-027` point 4) is the
   closest sibling shape, NOT `detect_mentioned_companies_for_thread`
   (`ADR-049` Decision 5) — that function answers a different question
   ("what OTHER companies does this Thread's content mention, besides its
   own already-known primary Customer"), while this story needs "what IS
   this Thread's own primary Customer." `classify_task`'s own prompt
   technique (reuse an exact known name when it clearly matches; propose a
   new proper-noun name when it clearly doesn't; answer `"Unsorted"` rather
   than guess) is EXACTLY this story's own required three-way outcome
   (existing match / new-Customer proposal / leave Unsorted, Scenarios
   1/3/8) with zero extra Python-side confidence-threshold logic needed —
   the honest-`"Unsorted"` behavior is the model's own prompted output, the
   same contract `classify_email`/`classify_task` already established.
3. **A genuinely new enumeration gap, found independently, not named by
   the story:** `vault_writer.list_known_customers()` (the only existing
   "known Customers" primitive) scans `customer:` FRONTMATTER usage across
   every note, not Customer FOLDER existence — and this story's own
   confirmed corpus state (zero of 137 Threads ever routed, all still
   `customer: "Unsorted"`) means it currently returns few or none of the
   real 26 existing Customer folders at all. The Customer-match call above,
   and the archival-candidate Job, both need the real folder list directly.
4. **The archival-move target, `Work/Archive/Customers/`, already exists**
   — confirmed live: `vault_provisioning.provision_vault_base`
   (`REQ-SB-70-US-01`) already idempotently creates `Work/Archive/
   {Opportunities,Customers,Resources}/` unconditionally. No new archive
   root needs provisioning, only the move primitive itself.
5. **No existing primitive moves a whole OKF-conformant directory to a
   DIFFERENT parent** — `rename_thread_directory` (`ADR-049` Decision 2)
   only handles a same-parent slug rename, and additionally renames the
   concept file INSIDE (old-slug.md → new-slug.md); `move_note_and_
   attachments` only moves a single flat note plus its sibling
   `attachments/<slug>/` folder, not a 4-file OKF directory (`index.md`/
   `<slug>.md`/`log.md`/`captures.md`, `ADR-042` point 1).

**Decision:**

1. **Batched-per-Customer payload convention, adopted as this codebase's
   canonical shape for any future multi-target Pending Approval, with ZERO
   change to `pending_approval_registry.py` or `pending_approvals_router.py`:**
   `payload = {"customer": <name>, "is_new_customer": <bool>, "thread_
   paths": [<str>, ...]}` for a routing-batch proposal, `action_id=
   "propose_customer_backfill_routing"`; `payload = {"customer": <name>,
   "source_directory": <str>}` for an archival-candidate proposal,
   `action_id="propose_customer_archival_candidate"`. Both use `trigger=
   "direct"` (never `"background"`), mirroring `_create_librarian_company_
   link_proposal`'s own exact reasoning — one backfill pass legitimately
   produces multiple distinct per-Customer batches, which `"background"`'s
   own idempotency guard would silently collapse. `finalize_customer_
   backfill_routing(payload)`/`finalize_customer_archival(payload)`
   (`librarian_housekeeping.py`) register in `_APPROVAL_HANDLERS`
   (`pending_approvals_router.py`) exactly like every other handler —
   `_resolved()`, the list/get endpoints, and `close_gap_by_pending_
   approval` all already operate on the record as a whole, with zero
   knowledge of or dependency on how many targets its own payload names —
   confirmed by direct reading, not assumed.
2. **`compass_client.detect_customer_for_thread(thread_content: str,
   known_customers: list[str], prompt_override: str | None = None) -> dict`**
   (new) → `{"customer": str, "confidence": float}` — a narrower sibling of
   `classify_task` (`ADR-027` point 4's "narrower sibling" precedent
   applied a fourth time: `classify_email` → `classify_task` → `guess_
   project_for_thread`/`detect_customer_durable_fact` → this), same prompt
   TECHNIQUE, own prompt TEXT framed around a Thread's full concatenated
   content (reusing `librarian_housekeeping._thread_full_content`,
   UNCHANGED) instead of a Task's subject+body. No retry loop (mirrors
   `classify_task`'s own precedent, not `classify_email`'s separate,
   unrelated retry bugfix).
3. **`vault_writer.list_customer_folders() -> list[dict]`** (new) —
   `{"customer": <title>, "slug": <dir name>, "directory": Path}` for every
   real Customer OKF directory under `Work/Customers/`, mirroring `list_
   customer_projects`'s own exact "enumerate this directory level, read
   title from concept file" shape one level up (a Customer's own sibling
   directly under `Work/Customers/`, rather than a Customer's own
   `projects/` subdirectory). Returns `[]` if `Work/Customers/` does not
   exist yet, same not-yet-created-folder contract every sibling
   enumeration primitive already has.
4. **`vault_writer.move_okf_directory(source_directory: Path, target_
   parent_directory: Path) -> Path`** (new, generic — not Customer-specific,
   named/placed alongside `okf_directory_paths` for the same reason
   `okf_directory_paths` itself is shared across Customer/Project) — mirrors
   `rename_thread_directory`'s own atomic-move-plus-refuse-to-overwrite
   discipline (raises `FileExistsError` on a genuine collision, never
   silently overwrites), narrowed one way and widened another: WIDENED to a
   different parent directory (not just a new slug under the same parent);
   NARROWED by NOT renaming the concept file inside — the directory's own
   name/slug is unchanged, only its LOCATION moves, so every file inside
   (`index.md`/`<slug>.md`/`log.md`/`captures.md`, plus any nested `People/`
   subdirectory) is moved byte-for-byte, untouched, in one atomic `Path.
   rename()` — satisfying Scenario 5's own "content byte-for-byte unchanged"
   requirement by construction, not by a defensive check. `finalize_
   customer_archival` calls it with `target_parent_directory = settings.
   vault_path / "Work/Archive/Customers"` (already provisioned, point 4
   above) — no new directory-provisioning code needed.
5. **Endpoints** (new, `email_poc_router.py`, mirroring the existing
   `/poc/librarian-*` convention): `POST /poc/librarian-propose-customer-
   backfill` (runs `propose_customer_backfill()` then `propose_customer_
   archival_candidates()` in one orchestrating call, passing the first's own
   `matched_existing_customer_names` result directly into the second — one
   evidence pass, never two independently-run Compass sweeps that could
   disagree with each other). Deliberately NOT added to `run_housekeeping_
   pass()`'s own scheduled chain — manually-triggered only, per the story's
   own explicit Constraint.

**Alternatives Considered:**

- **A new, dedicated multi-target Pending Approval schema/table** (e.g. a
  `targets: list[str]` first-class field on the registry record itself,
  rather than an opaque `payload` convention). Rejected — the existing
  `payload: dict` is ALREADY fully generic and already the documented
  extension point (`ADR-021` point 4); adding a first-class `targets` field
  would special-case ONE payload shape at the registry level while every
  other proposal kind's own payload shape stays free-form, an inconsistent,
  unnecessary schema change for a need the existing mechanism already
  satisfies without modification.
- **One Pending Approval per Thread (N separate single-target approvals per
  Customer) instead of one batched approval per Customer.** Rejected — the
  PRD's own text explicitly frames this as impractical at the real scale
  this backfill needs (up to 137 individual approvals to review one at a
  time); the batched shape is the story's own already-decided SCOPE
  choice, restated here only for why the MECHANISM (payload, not registry)
  is where the batching lives.
- **Extending `detect_mentioned_companies_for_thread`/`compass_client.
  detect_mentioned_companies` with a `primary_customer_mode` flag**, instead
  of a new sibling `compass_client` function. Rejected — that function's
  own parse contract returns a LIST of classified mentions
  (`known`/`new_unambiguous`/`ambiguous`), a genuinely different shape from
  this story's own single best-fit-or-Unsorted answer; branching one
  function's parse contract on a mode flag would make BOTH call shapes
  harder to reason about, violating `ADR-027` point 4's own established
  "narrower sibling, not a branching parameter" precedent.
- **Reusing `_fuzzy_match_known_entity` (the near-spelling heuristic
  `backfill_company_folders` uses for OTHER-companies-mentioned) to
  additionally dedupe the primary-Customer match itself before batching.**
  Rejected — `classify_email`'s own already-established, simpler contract
  ("reuse an exact existing name when it clearly matches one") is what this
  story's Compass call mirrors; the PRD's own text deliberately keeps
  near-spelling/ambiguous-name reconciliation OUT of this pass's scope
  (Columbus/Sindan/AZCON/HR Avatar are explicitly NOT hand-classified here)
  — adding a fuzzy layer to the PRIMARY match would reach into that
  explicitly-deferred territory uninvited.
- **A general "move any note or directory to an arbitrary target" primitive**
  in `vault_writer.py`, instead of the narrower `move_okf_directory`.
  Rejected — this codebase's own established pattern is a family of
  narrow, purpose-built move/rename primitives, each with its own explicit
  discipline (`move_note_and_attachments` for a flat note plus its
  attachments sibling; `rename_thread_note`/`rename_thread_directory` for
  Thread's own two shapes) — a maximally-general mover would need to
  handle every one of those shapes' own edge cases (sibling `attachments/`
  folders, concept-file-internal renaming) inside one function, when the
  archival need here is narrower and cleaner: an OKF directory, keeping its
  own name, moving to a new parent, nothing else.

**Consequences:**

- The batched-approval convention this ADR establishes is now the
  reference shape for any future multi-target Pending Approval — named
  explicitly so a future story does not have to re-derive "does this need a
  registry change" from first principles (answer: no, as long as the
  targets fit inside one `payload` dict the finalize handler alone
  interprets).
- **Disclosed, not fixed by this pass:** a second manual trigger of `POST
  /poc/librarian-propose-customer-backfill` before an already-created batch
  is approved or declined will re-propose the SAME still-`"Unsorted"`
  Threads into a NEW, separate pending batch (`trigger="direct"`'s own
  idempotency guard does not apply, only `"background"`'s does) — a real,
  disclosed operational risk, not a defect this story's own locked ACs
  (Scenario 9 only covers ALREADY-APPROVED Threads) require fixing. Left
  to normal operator discipline for a "manually-triggered, one-time
  backfill" (the story's own Constraint) — review and resolve pending
  batches before re-triggering. Named here so a future retrofit-repeat
  incident is not mistaken for a new bug.
- `list_customer_folders()` and `vault_writer.list_known_customers()`
  remain two DELIBERATELY DIFFERENT enumerations, answering two different
  questions (real folder existence vs. current frontmatter usage) — not
  merged into one, since collapsing them would silently change `classify_
  email`/`classify_task`'s own existing "known customers" prompt input
  (frontmatter-usage-based) to folder-based, an unrelated, out-of-scope
  behavior change to already-`Done` stories this ADR does not intend.
- `move_okf_directory`'s own "keep the same name, change only the parent"
  contract means an archived Customer's own directory name never changes —
  a future "un-archive" (restore) operation, if ever built, is a
  structurally simple reverse call to the same primitive; not built here,
  named only as a natural future extension point.

---

## ADR-056: Target-aware `dedupe_key` on `create_pending_approval` — closes the same-target/racing-trigger duplication gap left open by `ADR-018` point 2 and disclosed-but-not-fixed by `ADR-055` — extends `ADR-018` point 2 and `ADR-021` point 4's opaque-payload precedent, reopens neither

**Status:** Accepted
**Date:** 2026-08-19

**Context:** `BUGFIX-08-US-01` batches `BUG-029` (`meeting-capture`'s
`run_capture_now` produced two live Pending Approvals, one `trigger:
"scheduled"` and one `trigger: "direct"`, 5.76ms apart, neither ever
resolved) and `BUG-030` (staged-email routing/classification-failure
proposals, plus `librarian-housekeeping`'s Customer-backfill/archival
proposals, re-proposed as fresh duplicates on later capture/Job ticks —
301+50+15 real `email-capture-pipeline` duplicates, 13 real
`librarian-housekeeping` groups, one repeated 17×). Both root-cause to the
exact same gap: `create_pending_approval`'s existing idempotency guard
(`ADR-018` point 2) is scoped to `trigger == "background"` + `agent_id`
ONLY — correctly, so that `"chat"`/`"direct"` triggers (each a distinct,
deliberate request) and one tick's several genuinely-different-target
proposals are never wrongly collapsed. That correctness leaves a real,
narrower blind spot: two DIFFERENT non-`"background"` triggers (or the
SAME trigger repeated across ticks) both targeting the exact SAME real
thing. `ADR-055` itself already disclosed this precise risk in its own
Consequences ("a second manual trigger... will re-propose the SAME still-
`Unsorted` Threads into a NEW, separate pending batch... a real, disclosed
operational risk") without closing it — this ADR is that fix, generalized
to every real call site both bugs name.

Direct reading of the current, real code this pass (not assumed from
either bug's own note alone):

- `skill_registry.py::invoke_skill`'s own Supervised+mutates gate (the
  Pending-Approval-creating call at its line ~229) is the SINGLE central
  call site for every Skill-based approval — already the ONE function
  every real dispatch path (`skills_router.py`, `agents_router.py`'s
  dispatch fork, `knowledge_bootstrap.py`'s Hub-routed call, and —
  load-bearing for `BUG-029` — `agent_schedule_registry.dispatch_with_
  shared_lock`) passes through by construction (the function's own
  docstring already states this).
- `dispatch_with_shared_lock`'s own module-level `asyncio.Lock` already
  wraps the ENTIRE `skill_registry.invoke_skill` call (via `asyncio.
  to_thread`) inside its critical section, for both `"scheduled"` and
  `"direct"` dispatch of the SAME `(agent_id, capability_id)` pair — a
  single-threaded `asyncio.Lock`'s own check-then-acquire
  (`if lock.locked(): skip else: async with lock:`) has no yield point
  between the check and the acquire when uncontended, so the LITERAL race
  `BUG-029`'s live evidence measured is not structurally reproducible
  against this exact, already-consolidated lock path as currently
  written. Two real, plausible explanations for the live evidence, neither
  requiring a lock rewrite to close going forward: (a) it predates `ADR-
  037`'s shared-lock consolidation (`capture_scheduler.py`'s own docstring
  confirms a FORMER separate, private `_capture_run_lock` existed before
  that consolidation), or (b) it crossed the ALSO-real gap between the
  bundled-hourly `run_capture_if_idle` path and a standalone per-agent-
  schedule `dispatch_with_shared_lock` path — two different call chains
  that both reach `create_pending_approval` for the same agent without
  being the literal same function call. Either way, a target-aware dedup
  check at the point of persistence is the correct, deterministic,
  caller-independent guarantee — not a re-derivation of, or reliance on,
  precise asyncio lock-timing behaviour, which is real today but fragile
  to depend on alone and not independently unit-testable.
- `email_classification.py::route_to_project`/`_create_classification_
  failure_pending_approval`, and `librarian_housekeeping.py::propose_
  customer_backfill`/`propose_customer_archival_candidates`, all
  deliberately use `trigger="direct"` for the documented, still-correct
  reason that one tick can legitimately produce several distinct-target
  proposals. None of them has ever had ANY same-target check across ticks.
- `propose_customer_backfill`'s own docstring claim ("this filtering alone
  gives Scenario 9's own idempotency for free") is genuinely correct, but
  only for the narrower case of an ALREADY-APPROVED-AND-WRITTEN Thread
  (whose `customer` frontmatter is no longer `"Unsorted"` once `finalize_
  customer_backfill_routing` has actually run) — not for a Thread with an
  UNRESOLVED, still-`"pending"` proposal, whose frontmatter is
  deliberately left `"Unsorted"` until approval (the function's own
  "proposal only, never a silent write" contract). The docstring's own
  wording does not distinguish these two cases; the second is exactly the
  case `ADR-055`'s Consequences already named and `BUG-030`'s live
  evidence (13 real duplicate groups, one repeated 17×) actually hit. Not
  a wrong claim — an incomplete one, resolved here rather than left
  ambiguous for the decomposer.

**Decision:**

1. **`create_pending_approval` gains one new optional parameter,
   `dedupe_key: str | None = None`** — additive, mirrors `ADR-021` point
   4's own `payload` precedent (every existing zero-argument caller is
   unaffected by construction). When supplied, a SECOND, independent
   idempotency check runs — alongside, never replacing, `ADR-018` point
   2's existing `trigger == "background"` guard, which stays exactly as
   documented and unmodified: matches an existing `status == "pending"`
   record sharing the SAME `agent_id` AND the SAME `dedupe_key`,
   REGARDLESS of `trigger` value, and returns that existing record instead
   of creating a new one. The stored record gains one new additive field,
   `"dedupe_key": str | None`, defaulting to `None` on every pre-existing
   record (never matched by the new check, since the check itself is
   skipped entirely whenever the CALLER's own `dedupe_key` argument is
   `None` — every caller this ADR does not touch is behaviourally
   unaffected).
2. **`dedupe_key`'s VALUE is entirely the calling module's own
   convention** — the registry performs no parsing/derivation of it,
   mirroring `payload`'s own already-established "opaque to the registry,
   meaningful to the caller" shape (`ADR-021` point 4, `ADR-055` point 1).
   Adopted convention for every real call site named by both bugs,
   namespaced `"{action_id}:{stable_target_identifier}"` so two DIFFERENT
   action kinds sharing one `agent_id` can never accidentally collapse an
   overlapping raw identifier into each other (e.g. `librarian-
   housekeeping`'s backfill-routing and archival-candidate proposals could
   otherwise both legitimately name the same Customer string):
   - **`skill_registry.py::invoke_skill`'s own Supervised+mutates gate** —
     `dedupe_key = f"{agent_id}:{skill_id}"`, computed INSIDE
     `invoke_skill` itself, requiring ZERO change to any of its own
     callers (`dispatch_with_shared_lock`, `skills_router.py`,
     `agents_router.py`'s dispatch fork, `knowledge_bootstrap.py`). This
     is the generalized, permanent close for `BUG-029`'s own class of
     problem — every current and future Supervised, mutating Skill's
     scheduled-vs-direct (or any-trigger-vs-any-trigger) race for the same
     decision point, not `meeting-capture`/`run_capture_now` alone.
   - **`email_classification.py::route_to_project`** — `dedupe_key =
     f"route_thread_to_project:{thread_result['conversation_id']}"` (the
     Thread's own stable identifier — `ADR-046` Decision 8 already
     established `conversation_id`, not `thread_path`, as the one that
     survives a rename; already read into this call's own `payload`
     today, no new data needed).
   - **`email_classification.py::_create_classification_failure_pending_
     approval`** — `dedupe_key =
     f"acknowledge_classification_failure:{email['conversation_id']}"`.
   - **`librarian_housekeeping.py::propose_customer_backfill`** —
     `dedupe_key = f"propose_customer_backfill_routing:{customer}"`,
     computed per batch inside the function's own existing per-customer
     loop.
   - **`librarian_housekeeping.py::propose_customer_archival_
     candidates`** — `dedupe_key =
     f"propose_customer_archival_candidate:{customer}"`, computed per
     candidate.
3. **No change to `agent_schedule_registry.py`'s shared-lock mechanism**
   (`dispatch_with_shared_lock`/`dispatch_with_dedicated_processing_lock`/
   `capture_scheduler.run_capture_if_idle`) — its own concurrency-guard
   purpose (serializing real Outlook-COM/dispatch execution) stays valid
   and fully unmodified; this fix is deliberately independent of, and does
   not rely on, that lock's own timing guarantees, for the reasons in
   Context above.

**Alternatives Considered:**

- **Restructure `dispatch_with_shared_lock` so the lock itself is made to
  explicitly, documentedly span approval-creation**, instead of a
  registry-level dedupe check. Rejected — even a provably airtight lock
  would not close the OTHER gap found this pass (the bundled-hourly
  `run_capture_if_idle` path and a standalone per-agent `dispatch_with_
  shared_lock` call reaching `create_pending_approval` for the same agent
  via two DIFFERENT code paths), would not touch `BUG-030` at all (no lock
  exists, or should exist, around `route_to_project`/`propose_customer_
  backfill` — these are legitimately concurrent, independent proposals
  across different targets), and is not independently unit-testable the
  way a deterministic two-calls-same-`dedupe_key` registry check is.
- **A per-`(agent_id, action_id)` dedup scope hardcoded inside
  `create_pending_approval` itself, no caller-supplied key at all** — e.g.
  always dedupe on `(agent_id, action_id)` regardless of target. Rejected
  — this is exactly the shape `ADR-018` point 2 already correctly avoided
  for non-`"background"` triggers: it would incorrectly collapse `route_
  to_project`'s or `propose_customer_backfill`'s genuinely-different-
  target proposals (two different Threads, two different Customers)
  sharing one `agent_id`/`action_id` into one record, violating this
  story's own Constraint against collapsing different real targets.
- **Extend the EXISTING `trigger == "background"` guard's own matching
  logic to also compare a target field**, instead of a new, separate
  `dedupe_key` check. Rejected — would force every `"background"`-trigger
  caller (today, exactly three: email/meeting/todo-capture's own
  background gate) to start supplying a target identifier none of them
  has one for (a background tick has no single discrete target — `ADR-
  018` point 2's own original reasoning, `action_id` is `null` for these)
  — an unnecessary, unrelated change to an already-correct, already-
  `Accepted` path this story's own Constraints explicitly protect from
  weakening.
- **A storage-level change** (a dedicated dedup index/table, or
  auto-hashing `payload` instead of a caller-supplied key). Rejected —
  mirrors `ADR-055` point 1's own reasoning almost exactly: the registry's
  job is to stay a generic, caller-agnostic store; deriving a dedup key
  automatically from `payload` would assume every caller's payload shape
  carries a comparable, stable identity field (several don't — e.g. a
  `"background"`-trigger's `payload=None`), an unnecessary structural
  coupling the existing opaque-`payload` convention was deliberately built
  to avoid.

**Consequences:**

- `pending_approval_registry.py`'s stored record schema gains one new
  additive field (`dedupe_key`) — no migration needed; an absent/`None`
  key on every pre-existing record behaves identically to "no `dedupe_key`
  supplied," matching this codebase's own established additive-field
  precedent (`payload`, `ADR-021` point 4).
- **A `dedupe_key` match returns the EXISTING record's own stale payload/
  description, never refreshed** with whatever new information the later,
  suppressed call would have carried (e.g. a `propose_customer_backfill`
  re-run that would have added a newly-`"Unsorted"` Thread to an
  already-pending "Acme Corp" batch does not retroactively grow that
  batch's own `thread_paths`) — an accepted trade-off, matching this
  story's own "one live decision point per real target" goal exactly; the
  newly-found Thread is picked up on the NEXT run once the current pending
  batch is actually resolved (approved or declined), never silently lost.
- **Every future new Pending-Approval-creating call site must explicitly
  decide whether it needs a `dedupe_key`** (and if so, whether it must be
  namespaced by its own `action_id` to avoid colliding with a DIFFERENT
  action kind sharing the same `agent_id`) — this ADR is now the canonical
  reference for that decision, the same role `ADR-055` point 1 already
  plays for the batched-payload convention.
- `agent_schedule_registry.py`'s shared-lock mechanism is unmodified and
  its own documented guarantee (real Outlook-COM/dispatch serialization)
  is unaffected — this ADR deliberately does not re-open `ADR-037`.
- **The live, already-existing duplicate records are NOT retroactively
  deduplicated by this change** (2 real `meeting-capture`, 301+50+15 real
  `email-capture-pipeline`, 13 real `librarian-housekeeping` records) —
  matches the story's own explicit Non-Goal; this fix only closes the
  creation path going forward.

---

## ADR-057: Company Review (`REQ-SB-76`) — a boilerplate-aware extraction call (new sibling, not an edit to the frozen `detect_customer_for_thread`), one 5-outcome batched Pending Approval resolved via a new additive decision body on the existing Approve endpoint, `affiliate_of` restored onto Customer's OKF shape and added to Partner's shape (narrowly revises `ADR-009` point 3, additive only — points 1/2/4/5 unchanged), and a generalized, parameterized retag-scan primitive shared by the `migrate_customer_to_partner` OKF-shape fix and the new Merge outcome — extends `ADR-004`, `ADR-009`, `ADR-012`, `ADR-021` point 4, `ADR-042` point 1, `ADR-049` Decision 5, `ADR-055`, `ADR-056`; reopens none of them

**Status:** Accepted
**Date:** 2026-08-19

**Context:** `REQ-SB-76-US-01`'s own text settles every SCOPE-level question
directly (five real outcomes including Merge, batched-per-company review,
`migrate_customer_to_partner` must genuinely work against the current OKF
directory shape, a second confirmed company on an already-routed Thread is
additive-only) and names seven MECHANISM-level questions for `/plan-tasks`
(story `## Notes`). Direct reading of the real, current code —
`compass_client.py`, `librarian_housekeeping.py`, `pending_approvals_
router.py`, `pending_approval_registry.py`, `vault_writer.py`,
`partner_hub_linking.py`, `customer_hub_linking.py`, `MyDayApprovalsPage.tsx`,
`pendingApprovalsApiClient.ts` — resolves all seven:

1. **`detect_customer_for_thread` (`REQ-SB-74-US-01`, `Done`, `ADR-055`
   Decision 2) is confirmed, by direct reading of its real prompt text, to
   carry NO boilerplate-exclusion instruction at all** — only "If you can't
   confidently tell, use 'Unsorted' rather than guessing." Its own known-
   customers list is grounded in `vault_writer.list_customer_folders()`
   (folder names), which already contains prior boilerplate-derived noise
   (Apple/Google/Instagram/Twitter/LinkedIn), making the existing call
   self-reinforcing exactly as the story's own root-cause finding describes.
   `REQ-SB-74-US-01` is `Done` — per `Implementation/Pipeline.md` hard rule 1
   (specs are append-only), this function is frozen; it is superseded by a
   NEW sibling, never edited in place.
2. **A single Compass call answering "primary customer, yes/no" (`detect_
   customer_for_thread`'s own shape) cannot satisfy Scenario 9** (a SECOND,
   independently-confirmable company on a Thread that already has a primary
   customer) — this needs a MULTI-mention shape, the same TECHNIQUE `detect_
   mentioned_companies`/`detect_mentioned_companies_for_thread` (`ADR-049`
   Decision 5) already established (`{"mentions": [...]}`), but that
   function's own prompt is deliberately scoped to "companies OTHER than
   this content's own already-known primary Customer" (excludes the primary
   by design) — a genuinely different question from this story's own "every
   real company this Thread's content mentions, full stop, including
   whichever one should become primary." Extending `detect_mentioned_
   companies` with a mode flag was rejected for the same reason `ADR-055`'s
   own Alternatives Considered already rejected it for `detect_customer_for_
   thread`'s narrower need: branching one function's parse contract on a
   mode flag makes both call shapes harder to reason about, against `ADR-
   027` point 4's own established "narrower sibling, not a branching
   parameter" precedent.
3. **`POST /pending-approvals/{id}/approve` takes no body today** (direct
   reading confirms `def approve_pending_approval(approval_id: str) -> dict`
   has no request-body parameter at all) — a 5-way choice, plus the
   Affiliate branch's own parent+kind pick and the Merge branch's own
   parent-only pick, needs a real decision payload the router does not
   accept today. `_APPROVAL_HANDLERS[action_id](record["payload"])` (8
   existing registered handlers, `ADR-021` point 5/`ADR-055` Decision 1) is
   confirmed, by direct reading, to be a strict one-argument contract every
   one of those 8 handlers already relies on.
4. **`build_customer_concept_frontmatter` (the CURRENT OKF Customer concept-
   file shape, `ADR-042` point 1) carries no `affiliate_of` key at all**
   (confirmed by direct reading — `type`/`title`/`description`/`tags`/
   `status`/`stale_after`/`generated`/`verified`/`sources` only); the LEGACY
   flat hub-note shape (`create_customer_hub_note_baseline`/`_HUB_NOTE_
   BASELINE_KEYS`, `REQ-SB-14`) still carries it. `create_partner_hub_note_
   baseline`/`_PARTNER_HUB_NOTE_BASELINE_KEYS` (`ADR-009` point 3) carries no
   such key at all, by original design ("Partner has no Affiliate concept").
   The PRD's own text explicitly asks for `affiliate_of` on BOTH shapes.
5. **`migrate_customer_to_partner`'s real gap is narrower than "the scan
   can't see the OKF shape at all"** — confirmed by direct reading and by
   tracing `list_all_note_paths()`'s own current implementation (already a
   recursive `work_root.rglob("*.md")` scan, extended cross-cuttingly during
   `REQ-SB-54-US-01`): the function's Step 2 (the generic vault-wide retag
   scan) ALREADY discovers a Customer's OKF concept file today, and its
   existing Signal-A/B primitives (`rename_frontmatter_key`, `swap_tag`,
   `replace_body_line`) already no-op gracefully on every field the OKF
   concept file doesn't carry (its own `"type": "customer"` value, an OKF
   entity-KIND axis distinct from the legacy hub note's `"type": "Customer"`
   business-relationship value, never equals the Step-2 type-swap check's
   literal `"Customer"` string; it carries no top-level `customer` key to
   rename at all). The REAL gap is narrower and entirely in **Step 1**: `old_
   hub_path = vault_writer.hub_note_path(customer_name)` only ever resolves
   the LEGACY flat path (`Work/Customers/<name>.md`); for a Customer created
   under the current OKF directory shape, that path never exists, so `hub_
   note_moved` stays `False` and NOTHING moves — confirmed live by direct
   reading, not assumed, exactly matching the disclosed `MEMORY.md`
   (`REQ-SB-54-US-01-T04`, 2026-08-16) finding.
6. **The Merge outcome's own real target/content-move shape needs settling**
   — the PRD's own amended text mandates reuse of `migrate_customer_to_
   partner`'s own retag scan and `REQ-SB-74`'s own archival-candidate
   mechanism, "never a new, third move/retag primitive," but `migrate_
   customer_to_partner`'s own Step 2 is hardcoded to a Customer→Partner KIND
   swap (frontmatter key rename `customer`→`partner`, tag prefix swap,
   `type: Customer`→`Partner`) — unsuitable as-is for a same-kind merge
   (Customer duplicate → Customer canonical, the PRD's own real Mudala/
   Mubadala example) or a cross-kind merge in the OTHER direction (a
   duplicate Partner merging into a canonical Customer). The PRD's own
   Scenario 10 wording ("reusing the exact same generic, vault-wide retag
   MECHANISM migrate_customer_to_partner already uses") — not "calling
   `migrate_customer_to_partner` directly" — is read literally: the
   mechanism (the scan TECHNIQUE and its four per-note rewrite primitives)
   generalizes; the function's own external contract does not need to.
7. **No REST endpoint exposes the live known-Customer/known-Partner name
   list to the browser frontend today** — `mcp_server.py`'s `list_known_
   customers`/`list_known_partners` MCP tools are for agents/Hermes, not the
   React app; the Affiliate parent-picker and the Merge canonical-picker
   both need this list, freshly, at render time (never baked into the
   proposal's own payload snapshot, which would go stale the moment ANY
   other Company Review batch resolves first).

**Decision:**

1. **New, narrower-sibling Compass call — `compass_client.extract_thread_
   companies_for_review(thread_content: str, known_companies: list[str],
   prompt_override: str | None = None) -> {"companies": [{"name": str,
   "confidence": float}, ...]}`** (new function, `detect_customer_for_
   thread` is left byte-for-byte untouched — frozen, `Done`, superseded in
   practice, never edited). Mirrors `detect_mentioned_companies`'s own
   multi-mention TECHNIQUE (JSON `{"mentions"/"companies": [...]}` parse
   contract) with its OWN prompt TEXT: explicitly instructs Compass to
   IGNORE any company/product/device name that appears ONLY inside an
   email-client or device signature line (e.g. "Sent from my iPhone," "Get
   Outlook for Android"), a mailing-list footer, or a legal disclaimer —
   these are NOT genuine mentions — and to identify every REAL company the
   Thread's own substantive content genuinely relates to, reusing an exact
   known name (from the UNION of `list_customer_folders()` + `list_known_
   partners()`, never hardcoded) when it clearly matches one. Malformed/
   missing `"companies"` raises `CompassError`, mirroring every sibling
   primitive's own honest-failure contract.
2. **New Job pair, `librarian_housekeeping.propose_company_review()` /
   `finalize_company_review(payload)`, added alongside (never replacing)
   `propose_customer_backfill`/`finalize_customer_backfill_routing`.**
   `propose_company_review()` iterates every real Thread (via `list_thread_
   notes()` — NOT filtered to `"Unsorted"` only, since Scenario 9 needs
   already-routed Threads considered too), calls decision 1's extraction
   function once per Thread, and for each returned company mention SKIPS it
   if that Thread's OWN current `tags` already carries `customer/<slug>` or
   `partner/<slug>` for that exact company (the per-mention idempotency
   floor — mirrors `propose_customer_backfill`'s own "already routed" skip,
   generalized from per-Thread to per-mention granularity). Every remaining
   mention groups into ONE batched Pending Approval per distinct company
   name (`action_id="propose_company_review"`, `trigger="direct"`, `payload
   = {"company": <name>, "thread_paths": [<str>, ...]}`, `dedupe_key=
   f"propose_company_review:{company}"` — `ADR-056`'s own target-aware
   convention, applied to this new call site from day one rather than left
   for a future bugfix). A single transient `CompassError` for one Thread is
   recorded in a `"failed"` list and skipped, mirroring `propose_customer_
   backfill`'s own `T06`-found honest-failure handling — never crashes the
   whole pass. `propose_customer_backfill`/`detect_customer_for_thread`/
   `POST /poc/librarian-propose-customer-backfill` are left physically
   unedited (frozen, `Done`) but superseded in PRACTICE — the operator uses
   the new endpoint (below) going forward; the old one is simply unused, not
   deleted, not hidden.
3. **The Approve endpoint gains one new, additive, optional Pydantic-model
   request body**, mirroring this codebase's own established `BaseModel`-
   request-body convention (`agents_router.py`/`skills_router.py`/etc.), NOT
   a raw dict: `class CompanyReviewDecisionBody(BaseModel): outcome: str;
   parent_name: str | None = None; parent_kind: str | None = None`. `def
   approve_pending_approval(approval_id: str, decision:
   CompanyReviewDecisionBody | None = None) -> dict`. Inside the existing
   `elif record["action_id"] in _APPROVAL_HANDLERS:` branch ONLY, the router
   merges the decision into the stored payload BEFORE dispatch —
   `effective_payload = {**record["payload"], **(decision.model_dump() if
   decision else {})}`; `result = _APPROVAL_HANDLERS[record["action_id"]]
   (effective_payload)` — every one of the other 8 registered handlers keeps
   its EXACT existing one-argument `(payload: dict) -> dict` signature,
   completely unaffected (their own stored payloads never contain
   `outcome`/`parent_name`/`parent_kind` keys, so `effective_payload ==
   payload` for them whenever the frontend sends no body, exactly as it does
   today). `Decline` is NOT touched at all — `POST /pending-approvals/{id}/
   decline` has and needs zero body for this or any proposal kind, since it
   never invokes a handler (Scenario 7's "completely unchanged" requirement
   is satisfied by construction, reusing the existing endpoint verbatim).
   `finalize_company_review(payload)` is registered once:
   `_APPROVAL_HANDLERS["propose_company_review"] = finalize_company_review`
   — ONE handler, branching internally on `payload["outcome"]` (`"customer"
   | "partner" | "affiliate" | "merge"`), not four separately-registered
   handlers, since exactly one Pending Approval record is ever created per
   company (Scenario 1's own "exactly ONE Pending Approval offering five
   real outcomes"). A `parent_name` the server cannot independently confirm
   is a real, existing Customer/Partner of the claimed `parent_kind`
   (`customer_concept_file_exists`/`hub_note_exists` for Customer,
   `partner_hub_note_exists` for Partner) raises before any write happens —
   the existing call order (`_APPROVAL_HANDLERS[...]` runs BEFORE
   `resolve_pending_approval`) already means a raised exception leaves the
   record `"pending"`, never silently half-applied — no new error-handling
   mechanism needed, an already-correct consequence of the existing code
   shape.
4. **`build_customer_concept_frontmatter` gains `"affiliate_of": ""`** (one
   additive dict key — flows through both `create_customer_directory_
   baseline` and `ensure_customer_directory_baseline`/`ensure_okf_directory_
   baseline`'s existing top-up-if-missing loop with ZERO further code
   change, since both already iterate whatever `build_customer_concept_
   frontmatter` returns). **`_PARTNER_HUB_NOTE_BASELINE_KEYS` gains
   `"affiliate_of"`** (`("type", "partner", "tags", "affiliate_of")`,
   mirroring the legacy Customer hub note's own 4-key shape exactly);
   `create_partner_hub_note_baseline`/`ensure_partner_hub_note_baseline_
   frontmatter` both gain the same `"affiliate_of": ""` default. Setting a
   REAL `affiliate_of` value (the Affiliate outcome, decision 3 above) reuses
   the ALREADY-EXISTING generic `vault_writer.upsert_frontmatter_key(path,
   "affiliate_of", parent_name)` — zero new write primitive. **This
   narrowly, additively revises `ADR-009` point 3's "Partner deliberately
   has no Affiliate concept" sub-clause only** — `ADR-009`'s own real point
   (Customer/Partner mutual exclusivity, point 1; the parallel-sibling-
   module structure, point 2; the generic vault-scanning migration, point 4;
   the three generic rename/swap/replace primitives, point 5) is completely
   untouched, mirroring the EXACT precedent `ADR-012` already set (extending
   `ADR-009` point 4's match predicate via a NEW ADR, never rewriting `ADR-
   009`'s own text). `ADR-009`'s own `**Status:**` line is updated to
   `Accepted, point 3 partially superseded by ADR-057 (Partner gains
   affiliate_of)` — the same cross-reference convention already used
   elsewhere in this file (`ADR-018`, `ADR-011`, `ADR-013`'s own "Superseded
   by ADR-XXX (points N only)" Status-line pattern) — never a rewrite of
   `ADR-009`'s own Context/Decision/Alternatives/Consequences prose.
5. **`migrate_customer_to_partner`'s Step 1 gains an OKF-directory-first
   branch, tried BEFORE the existing legacy-flat-path check** (mirrors
   `resolve_thread_directory`'s own "directory-shaped scan first, flat-note
   scan second, only on a miss" ordering discipline, `ADR-052`): if `vault_
   writer.customer_concept_file_exists(customer_name)`, the WHOLE OKF
   directory is moved via `vault_writer.move_okf_directory(vault_writer.
   customer_directory_paths(customer_name)["directory"], vault_writer.
   partner_hub_note_path(customer_name).parent)` — the exact same generic,
   already-`Accepted` primitive `REQ-SB-74-US-01-T04` built (`ADR-055`
   Decision 4), reused verbatim, zero new move code; `hub_note_moved =
   True`. Only when the OKF concept file does NOT exist does the existing
   legacy-flat branch run, completely unchanged. **Step 2 (the generic
   retag scan) needs exactly ONE correction, not an extension:** the `if
   vault_writer.remove_frontmatter_key_if_present(path, "affiliate_of"):`
   line is DELETED — decision 4 above means Partner legitimately carries
   `affiliate_of` now, so a migrated entity's own real (or empty)
   `affiliate_of` value must carry forward untouched, exactly like every
   other field Step 2 doesn't explicitly rewrite. Everything else in Step 2
   — the two match signals, the `type`/`customer→partner`/tag/body-line
   rewrites — already correctly discovers and retags the OKF concept file
   (confirmed by direct reading, Context point 5) with ZERO further change.
6. **Step 2's per-note rewrite logic is extracted into a new, generalized,
   parameterized internal helper, `partner_hub_linking._retag_company_
   references(old_name: str, old_kind: str, new_name: str, new_kind: str) ->
   list[dict]`** (`old_kind`/`new_kind` ∈ `{"customer", "partner"}`), so the
   SAME scan technique drives both a kind-changing migration (old_kind !=
   new_kind) and a name-changing, kind-preserving-or-changing merge (any
   combination) — computing the type-swap/field-rename/tag-swap/body-line
   values FROM the four parameters instead of hardcoding "Customer"/
   "Partner." `migrate_customer_to_partner(customer_name)` becomes a THIN
   wrapper — `_retag_company_references(customer_name, "customer",
   customer_name, "partner")` plus its own unchanged Step 1 — behaviourally
   IDENTICAL to today by construction (same name in, same name out, kind
   flips), its own external contract/return shape unchanged, zero call-site
   changes anywhere. A new, thin, PUBLIC sibling, `partner_hub_linking.
   retarget_company_references(old_name, old_kind, new_name, new_kind) ->
   list[dict]`, is added purely as a one-line pass-through to the SAME
   private helper — this is the function the new Merge outcome (decision 7)
   calls. **No third move/retag primitive is introduced** — one scan
   technique, one shared helper, two thin callers.
7. **Merge outcome (`finalize_company_review`'s `"merge"` branch):**
   validates `parent_name`/`parent_kind` (decision 3), then (a) batch-
   applies the canonical entity's own frontmatter+tag to every Thread in
   `payload["thread_paths"]` via the SAME shared per-outcome apply helper
   the Customer/Partner/Affiliate branches already use (`_apply_company_to_
   threads(thread_paths, target_name, target_kind)`, itself the one place
   Scenario 9's already-set-vs-unset primary-`customer`/`partner` check
   lives — see decision 8); then (b) ONLY if the duplicate name already has
   a real prior entity of its own (`customer_concept_file_exists(company)`,
   `hub_note_exists(company)`, or `partner_hub_note_exists(company)`) —
   calls `retarget_company_references(company, <duplicate's own real kind>,
   parent_name, parent_kind)` (decision 6) to redirect every OTHER real
   vault note's own reference away from the duplicate, THEN archives the
   now-unreferenced duplicate note by reusing an ALREADY-EXISTING move
   primitive matched to its OWN shape — `vault_writer.move_okf_directory`
   (OKF-directory-shaped duplicate) or `vault_writer.move_note_and_
   attachments` (legacy-flat-Customer-shaped duplicate), both times to
   `Work/Archive/Customers/`, literally reusing `librarian_housekeeping.
   finalize_customer_archival`'s own call shape as a plain same-module
   function call (`REQ-SB-74-US-01`'s own archival-candidate mechanism,
   `ADR-055` Decision 4) — never a new archival primitive. **Disclosed, not
   fixed by this pass:** a duplicate whose own prior entity is Partner-
   shaped (flat `Work/Partners/<name>.md`) is correctly retargeted (step b's
   reference-redirect half) but its own now-unreferenced flat file is left
   in place, untouched, NOT archived — no `Work/Archive/Partners/` root is
   provisioned yet (`vault_provisioning.provision_vault_base` only
   provisions `Work/Archive/{Opportunities,Customers,Resources}/`,
   confirmed live during `ADR-055`), and provisioning a new archive root is
   real, additive scope this story's own PRD text never asked for — named
   here, not silently left broken, mirroring this codebase's own repeated
   "disclosed, not fixed by this pass" convention (`ADR-055`/`ADR-049`
   Consequences).
8. **`_apply_company_to_threads(thread_paths, target_name, target_kind) ->
   list[str]`** (new, shared by all four Customer/Partner/Affiliate/Merge
   branches) — for each Thread, freshly reads its CURRENT `customer`/
   `partner` frontmatter AT FINALIZE TIME (never snapshotted into the
   proposal payload, since a different Company Review batch could resolve
   first and change that state in between propose and approve — mirrors
   `finalize_customer_backfill_routing`'s own established "read fresh, write
   deferred" discipline): if the Thread's own primary `customer`/`partner`
   is still unset/`"Unsorted"`, writes `target_name` to the primary field
   plus the `target_kind/<slug>` tag (Scenarios 3-6/10's own "primary write"
   path); if it is ALREADY set to a DIFFERENT real company, leaves the
   primary field byte-for-byte untouched and instead adds an ADDITIVE
   `target_kind/<slug>` tag PLUS regenerates that Thread's own `## Related`
   section (Scenario 9) — reusing `email_classification.build_thread_
   related_wikilinks` DIRECTLY (the same composition primitive `populate_
   thread_related_links` itself calls), never `populate_thread_related_
   links()` itself (a whole-vault batch Job with no per-Thread entry point —
   extracting one would be an unrelated refactor of an already-`Done`
   Job outside this story's own scope), written via `vault_writer.replace_
   body_section(concept_path, "## Related", ..., caller="librarian_
   housekeeping.populate_thread_related_links")` — the SAME already-
   registered `section_ownership.py` caller id (`ADR-049` Decision 4), since
   this is conceptually the Librarian's own `## Related` mechanism firing
   on-demand for one Thread, not a second, competing owner.
9. **New `GET /pending-approvals/known-companies -> {"customers": [<name>,
   ...], "partners": [<name>, ...]}`** (new, `pending_approvals_router.py` —
   colocated with what consumes it, rather than `email_poc_router.py`'s
   one-off-migration-endpoint convention, since this is an ordinary,
   repeatedly-polled read composed directly from `vault_writer.list_
   customer_folders()` + `vault_writer.list_known_partners()` — both
   already-existing, vault-derived, never-hardcoded enumerations, zero new
   `vault_writer.py` code). Frontend calls this fresh on every Approvals
   page load, never bakes the list into a proposal's own stored payload.
10. **Scheduling — manually-triggered only, mirroring `ADR-055`'s own
    explicit precedent exactly:** `POST /poc/librarian-propose-company-
    review` (new, `email_poc_router.py`, matching the existing `/poc/
    librarian-*` naming convention) runs `propose_company_review()`.
    Deliberately NOT added to `run_housekeeping_pass()`'s own scheduled
    chain — the PRD's own text does not repeat `REQ-SB-70`/`71`'s standing
    manual-posture constraint for this successor mechanism, but nothing
    argues for a different posture either, and an unreviewed, autonomous
    re-run of a NOISE-REDUCING mechanism the operator explicitly wants to
    review company-by-company would work against the story's own stated
    purpose.

**Alternatives Considered:**

- **Edit `detect_customer_for_thread`'s own prompt text in place** to add
  the boilerplate-exclusion instruction, rather than adding a new sibling
  function. Rejected — `REQ-SB-74-US-01` is `Done`; per `Implementation/
  Pipeline.md` hard rule 1, its own artefacts are frozen, and this story's
  own Context explicitly frames itself as SUPERSEDING that Job's mechanism,
  not patching it — a live-caller-preserving new sibling, not an in-place
  edit, is this codebase's own repeatedly-applied precedent (`SPRINT-036`'s
  own "verify the existing function's own real handler-calling convention
  ... add a NEW sibling function ... whenever the existing function is also
  relied on synchronously by a caller outside the current task's own file
  scope," `Implementation/Learnings.md`).
- **A dedicated multi-target Pending Approval schema/table**, or a per-
  outcome `action_id` (`propose_company_review_customer`/`_partner`/
  `_affiliate`/`_merge`), instead of one `action_id` with a decision body.
  Rejected for the schema table for the exact reason `ADR-055`'s own
  Alternatives Considered already rejects it (the opaque `payload: dict` is
  already the documented extension point). Rejected for per-outcome
  `action_id`s because the classification is NOT known at propose time —
  Scenario 1 requires exactly ONE Pending Approval per company offering all
  five outcomes, so the `action_id` cannot encode an outcome that does not
  exist yet; a decision payload supplied at approve time is the only shape
  that fits.
- **Change every one of the 8 existing `_APPROVAL_HANDLERS` entries' own
  signature to `(payload, decision=None)`**, instead of merging `decision`
  into `payload` at the router before dispatch. Rejected — touches 8
  already-`Done` handler functions across 4 different modules for a
  capability only ONE of them needs; the merge-before-dispatch shape keeps
  every existing handler's own one-argument contract completely untouched,
  a strictly additive, lower-risk change.
- **Give Partner its own OKF directory shape as part of this fix**
  (`ensure_partner_hub_note`'s own native creation path becomes directory-
  based, matching Customer). Rejected — this story's own explicit Constraint
  is "`ensure_partner_hub_note`/`link_note_to_partner_hub` are reused
  UNMODIFIED"; a migrated-from-OKF-Customer Partner entry legitimately ends
  up directory-shaped (decision 5) while a natively-created Partner stays
  flat-file-shaped — an accepted, disclosed asymmetry (Consequences, below),
  not resolved by inventing OKF vocabulary (a `type: "partner"` value) no
  other code path would ever produce or consume, for a capability nothing
  else in this story's own scope needs.
- **Rewrite the OKF concept file's own `type` field** (`"customer"` →
  `"partner"`) during a Customer→Partner migration, for schema symmetry with
  the legacy hub note's own `type: Customer` → `type: Partner` rewrite.
  Rejected — confirmed by direct reading (`build_project_concept_
  frontmatter`) that OKF's own `type` field is an ENTITY-KIND axis
  (`"customer"`/`"project"`), a genuinely different axis from the vault's
  own Customer-vs-Partner business-relationship classification (which lives
  entirely in `tags`) — rewriting it would invent a new, unprecedented OKF
  type value nothing else produces or reads, for zero functional benefit
  (nothing today branches on OKF `type` to distinguish Customer from
  Partner).
- **Provision a new `Work/Archive/Partners/` root as part of this pass**, so
  EVERY Merge-duplicate shape (including Partner) gets archived. Rejected —
  real, additive vault-structure scope the PRD's own text never asked for;
  disclosed as a named, narrower gap (decision 7) instead, consistent with
  this codebase's own "disclosed, not fixed by this pass" convention rather
  than silently expanding scope to close it uninvited.
- **Extract a per-Thread callable out of `populate_thread_related_links()`**
  so the Multi-Customer additive path (decision 8) could call it directly
  instead of composing `build_thread_related_wikilinks` itself. Rejected —
  an unrelated refactor of an already-`Done`, already-scheduled Librarian
  Job outside this story's own `## Files to Modify`, for a benefit `build_
  thread_related_wikilinks` (the actual composition primitive `populate_
  thread_related_links` itself calls) already delivers directly with zero
  refactor.

**Consequences:**

- `ADR-009`'s own `**Status:**` line is updated to `Accepted, point 3
  partially superseded by ADR-057 (Partner gains affiliate_of)` — points 1,
  2, 4, and 5 stay `Accepted`, unedited, in full force; this is the SAME
  narrow-supersession convention already used for `ADR-011`/`ADR-013`/
  `ADR-018`.
- **A real, disclosed, permanent shape asymmetry:** a Partner entry created
  NATIVELY (`ensure_partner_hub_note`, never touched by this ADR) stays
  flat-file-shaped (`Work/Partners/<name>.md`); a Partner entry that arrives
  via a Customer→Partner migration or a Merge-into-Partner (decisions 5/7)
  is directory-shaped (`Work/Partners/<slug>/<slug>.md` + siblings) — both
  are fully valid, `list_known_partners()`/`partner_hub_note_exists()`-
  discoverable Partner entries; no code path today needs them to share one
  physical shape. A future story giving Partner its own native OKF shape
  (should one ever be proposed) would need its own architecture pass, not
  pre-designed here — the same "third company-relationship type" future-
  extension carve-out `ADR-009`'s own Consequences already named.
- **`propose_customer_backfill`/`finalize_customer_backfill_routing`/
  `detect_customer_for_thread`/`POST /poc/librarian-propose-customer-
  backfill` remain live, callable, byte-for-byte unedited code** — not
  deleted, not hidden, simply superseded in practice. A future cleanup pass
  removing genuinely dead code is a separate, later decision, not silently
  folded into this one (`Implementation/Pipeline.md` hard rule 1).
- **The per-mention idempotency floor (decision 2) is coarser than exact-
  content tracking** — a Thread whose OWN tags already carry `customer/
  <slug>` for a company is skipped for THAT company on every future
  `propose_company_review()` run, but a genuinely NEW company mention
  appearing in a later message on the SAME Thread is still correctly
  re-considered (the skip is keyed on the specific company/tag pair, not
  the whole Thread) — same trade-off precedent as `ADR-056`'s own disclosed
  "a dedupe_key match returns the existing record's own stale payload,
  never refreshed" Consequence, accepted for the identical reason.
- `_apply_company_to_threads`'s own additive-tag branch (decision 8) means
  a Thread can accumulate an unbounded number of `customer/<slug>`/
  `partner/<slug>` tags over its lifetime (one primary + N additive) — an
  intentional, PRD-mandated data-model consequence (`customer:` stays
  single-value; multi-company support is tag-only), not a defect.

---

## ADR-058: The Librarian splits into two real sub-agents (`REQ-SB-79`) — a new "retire without delete" `agent_registry.py` primitive, `run_housekeeping_pass()` splits into two independently-scheduled orchestrators, and all five real Pending-Approval-creating call sites re-home onto "Company and Partner Building"; extends `ADR-049`, `ADR-055`, `ADR-057`, composes with `REQ-SB-77-US-01`'s own new self-heal wiring; reopens none of them

**Status:** Accepted
**Date:** 2026-08-19

**Context:** `REQ-SB-79-US-01`'s own text settles the SCOPE question directly
and concretely — the operator explored an open-ended "one sub-agent per
Job" shape, then explicitly concretized it: "Just be Concrete / 2
Pipelines... one for Threads Cleaning and one for Company and Partner
Building" — no new Section, no 5-agent shape, this ADR does not re-open
that question. What the story's own text leaves to `/plan-tasks` is
MECHANISM: exactly which real files/call sites need to change, how the
already-existing single `librarian-housekeeping` identity's own real
historical data (Pending Approvals, Agent History) survives the split
without being orphaned or silently rewritten, and how the two new
identities become independently schedulable given `agent_schedule_
registry.create_or_update_schedule`'s own hard requirement that a
`capability_id` be both a real, granted Skill AND classified `"mutates":
True`.

Direct reading of the real, current code (confirmed, not assumed):

1. **`librarian_housekeeping.py`'s own 5-Job chain splits cleanly along the
   PRD's own named boundary, with ZERO ambiguity.** `rename_threads`,
   `link_thread_messages`, `backfill_files`, `populate_thread_related_
   links` (Threads Cleaning) create ZERO Pending Approvals between them —
   grepping the whole module for `pending_approval_registry.create_
   pending_approval` finds exactly FOUR call sites, and every one of them
   belongs to a Company-and-Partner-Building-side Job: `_create_librarian_
   company_link_proposal` (called only from `backfill_company_folders`),
   `propose_customer_backfill`, `propose_company_review`, `propose_
   customer_archival_candidates`. The FIVE literal `agent_id=
   "librarian-housekeeping"`-shaped references across the module (the
   proposal-creation function's own default `requesting_agent_id`
   parameter, plus the four call sites above) are therefore ALL on the
   Company-and-Partner-Building side — Threads Cleaning's own four Jobs
   need no per-call-site identity edit at all.
2. **`agent_registry.py` has no rename or delete primitive for any agent
   identity today** — only `create_agent`/`get_agent`/`list_agents`/`get_
   action`. Renaming the EXISTING `librarian-housekeeping` record in place
   to become one of the two new identities is therefore not a small edit;
   it would require building a brand-new capability this story's own
   Constraints ("zero new Job logic") do not ask for.
3. **`section_registry.py` has no "unassign" primitive** — `set_agent_
   section` requires a real, existing `section_id`; there is no way to
   remove an agent from a Section's own visible membership without
   reassigning it to some OTHER real Section (a confusing, arbitrary
   re-categorization of a defunct identity).
4. **`agent_schedule_registry.create_or_update_schedule` refuses any
   `capability_id` that is not both a granted Skill AND `"mutates": True`**
   — confirmed by direct reading of `_is_schedulable`. `run_housekeeping_
   pass` is the ONE Skill/MCP-tool/schedule entry this bundle has today,
   granted to `librarian-housekeeping` alone (`skill_tools.SKILLS`,
   `skill_registry._SKILL_HANDLERS`/`_MIGRATION_GRANT_SEED`, `main.py`'s
   own `create_or_update_schedule` call). Two independently-schedulable
   sub-agents structurally need two independent `(agent_id, capability_id)`
   Skill/grant/schedule entries, not one shared one.
5. **`section_ownership.py`'s `_CALLER_ALLOW_LISTS` keys off dotted
   FUNCTION names** (`"librarian_housekeeping.backfill_files"` etc.),
   never agent identity — confirmed by direct reading; genuinely zero
   change needed there.
6. **`pending_approvals_router.py`'s `_APPROVAL_HANDLERS` dispatches by
   `action_id`, never `agent_id`** — confirmed by direct reading; every
   registered Librarian-family handler (`finalize_librarian_company_link`,
   `finalize_customer_backfill_routing`, `finalize_customer_archival`,
   `finalize_company_review`) is unaffected by which agent identity
   created the record it resolves.
7. **8 real production files reference the `librarian-housekeeping`
   identity or the `librarian_housekeeping` module** (confirmed by direct
   grep, excluding a `.scratch/` throwaway script): `librarian_
   housekeeping.py`, `pending_approvals_router.py`, `email_poc_router.py`,
   `email_classification.py` (comment only, zero functional coupling),
   `section_ownership.py` (zero change, point 5), `main.py`, `skill_
   tools.py`, `skill_registry.py` — matching the PRD's own disclosed count.
8. **`REQ-SB-77-US-01`'s own Scenario 6b** (People-note re-linking's
   scheduled, self-healing catch-all) is explicitly designed, this same
   architect pass, to live INSIDE this story's new Company-and-Partner-
   Building scheduled orchestrator — a real, load-bearing composition
   point this ADR's own Decision 3 below must leave room for.

**Decision:**

1. **Two new Agent-tier identities under the SAME already-existing
   "Librarian" Section — no new Section:** `agent_registry.create_agent
   ("Threads Cleaning", type="worker", settings=[...])` → `threads-
   cleaning`; `agent_registry.create_agent("Company and Partner Building",
   type="worker", settings=[...])` → `company-and-partner-building`. Both
   `section_registry.set_agent_section(<id>, "librarian")`.
2. **`agent_registry.py` gains its first "retire without delete"
   primitive.** A CREATED agent's own record (never a `_SEED_AGENTS`
   entry — a shipped, static agent can never be retired) gains an
   additive `retired: bool` key, default `False`. `retire_agent(agent_id:
   str) -> bool` sets it (idempotent no-op if already retired; `False` for
   an unknown or `_SEED_AGENTS` id). `list_agents(include_retired: bool =
   False)` gains the optional filter, default excludes retired agents —
   the exact shape `GET /agents`/the Agents Map already calls, so a
   retired agent structurally stops appearing under any Section with ZERO
   frontend change. `get_agent(agent_id)` is left COMPLETELY UNCHANGED —
   always resolves ANY agent regardless of `retired`, so `_resolved()`
   (`pending_approvals_router.py`) and every agent-history-name lookup
   keep returning a real, honest `agent_name` for every already-existing
   record attributed to `librarian-housekeeping`, forever (Scenario 6).
   `librarian-housekeeping` itself is retired via this new primitive,
   idempotently, on every app start (`main.py`'s lifespan) — a real,
   self-healing startup step, mirroring this codebase's own dominant
   idempotent-bootstrap convention (`ensure_librarian_agent_and_section`'s
   own existing shape, `_MIGRATION_GRANT_SEED`'s own self-healing grant),
   never a one-off migration script.
3. **`run_housekeeping_pass()` splits into two orchestrators, one per new
   agent:**

   ```python
   def run_threads_cleaning_pass() -> dict:
       return {
           "rename_threads": rename_threads(),
           "link_thread_messages": link_thread_messages(),
           "backfill_files": backfill_files(),
           "populate_thread_related_links": populate_thread_related_links(),
       }


   def run_company_partner_building_pass() -> dict:
       return {
           "backfill_company_folders": backfill_company_folders(),
           "retrofit_people_from_emails": people_extraction.retrofit_people_from_emails(),
       }
   ```

   The first is a straight rename of the existing orchestrator, minus
   `backfill_company_folders` — same fixed job order, same ordering
   guarantee (Scenario 2/7). The second is new, and — composing directly
   with `REQ-SB-77-US-01`'s own Scenario 6b, decided this same architect
   pass — additionally drives the ALREADY-EXISTING, already-`Done`
   `people_extraction.retrofit_people_from_emails()` on its own schedule,
   the whole-vault self-healing half of that story's own two-trigger-point
   design. `librarian_housekeeping.py` gains one new import,
   `people_extraction` — a business-to-business composition, reusing that
   module's own already-established "intentional, permitted horizontal
   call within the business layer" precedent a second time.
   `propose_customer_backfill`/`propose_customer_archival_candidates`/
   `propose_company_review` stay individually, manually triggered via
   their own already-existing `/poc/*` endpoints — never folded into this
   scheduled wrapper, mirroring `ADR-055`/`ADR-057`'s own explicit
   "manually-triggered only" precedent, untouched.
4. **All five literal `agent_id="librarian-housekeeping"`-shaped
   references in `librarian_housekeeping.py` become
   `"company-and-partner-building"`** (`_create_librarian_company_link_
   proposal`'s own default `requesting_agent_id` parameter, plus the four
   real `create_pending_approval` call sites named in Context point 1) —
   the complete, exhaustive set; Threads Cleaning's own four Jobs need no
   equivalent edit, since they create no Pending Approvals at all.
5. **Skill/grant/schedule split:** `skill_tools.SKILLS["run_housekeeping_
   pass"]` is REPLACED by two catalog entries (`"run_threads_cleaning_
   pass"`, `"run_company_partner_building_pass"`, same `"mutates": True`,
   `"tool": "Vault"` shape), each with its own thin `@mcp_server.tool()`
   wrapper. `skill_registry._SKILL_HANDLERS`/`_MIGRATION_GRANT_SEED` gain
   the matching two entries, granted to `threads-cleaning`/`company-and-
   partner-building` respectively, REPLACING the single `"run_
   housekeeping_pass": ["librarian-housekeeping"]` line. `main.py`'s
   lifespan renames/generalizes `ensure_librarian_agent_and_section()` to
   `ensure_librarian_agents_and_section()` (idempotent-checks and creates
   BOTH new agents, mirrors the existing per-agent shape applied twice),
   idempotently retires `librarian-housekeeping` (decision 2) and removes
   its own now-stale schedule entry (`agent_schedule_registry.remove_
   schedule("librarian-housekeeping", "run_housekeeping_pass")`, already
   idempotent/safe if absent), then calls `create_or_update_schedule`
   TWICE, once per new `(agent_id, capability_id)` pair, both defaulting
   to the SAME 6-hour interval `REQ-SB-72-US-01` originally chose —
   genuinely independent schedule records from the first tick onward
   (Scenario 3), each separately operator-adjustable thereafter.
6. **`email_poc_router.py`:** `/poc/librarian-run-housekeeping-pass` is
   REPLACED by `/poc/librarian-run-threads-cleaning-pass`/`/poc/librarian-
   run-company-partner-building-pass`. Every per-Job endpoint (rename,
   link-thread-messages, backfill-files, populate-related, backfill-
   company-folders, propose-customer-backfill, propose-company-review) is
   UNCHANGED — same function, same route, mirroring the existing `/poc/
   librarian-*` naming convention exactly.
7. **`section_ownership.py`/`pending_approvals_router.py`'s
   `_APPROVAL_HANDLERS` need ZERO change** (Context points 5/6) —
   confirmed, not merely assumed.

**Alternatives Considered:**

- **Leave `librarian-housekeeping` visible forever alongside the two new
  agents (three cards under one Section).** Rejected — contradicts
  Scenario 1's own "two real, independently-listed Agents" framing and
  would present a dead, capability-less identity indistinguishable from a
  real one to an operator browsing the Agents Map.
- **Rename the EXISTING `librarian-housekeeping` record in place to become
  one of the two new identities** (e.g. "Threads Cleaning"), creating only
  ONE new sibling agent. Rejected — `agent_registry.py` has no rename
  primitive today (Context point 2), and building one is a real,
  out-of-scope new capability; it would also make old Company-Review-
  shaped historical records display under a now-misleading "Threads
  Cleaning" name, less honest than a clean retirement.
- **Retroactively rewrite every existing Pending Approval/Agent History
  record's own stored `agent_id` string** to whichever of the two new
  identities it "should" have belonged to. Rejected — a real, risky,
  one-off data-migration script (`MEMORY.md`'s own "API-first, no script
  workarounds" constraint) needing per-record reclassification logic with
  no clean, certain rule for already-resolved historical records that
  predate this split even existing as a concept; this project's own
  standing "archive/retire, never destructively rewrite" default
  (`MEMORY.md`) makes a non-destructive retirement strictly safer.
- **A brand-new, THIRD scheduled capability dedicated solely to
  `retrofit_people_from_emails()`'s own self-heal**, instead of composing
  it into `run_company_partner_building_pass()`. Rejected — `REQ-SB-77-
  US-01`'s own Scenario 6 explicitly frames the self-heal as living
  INSIDE the Company and Partner Building sub-pipeline, not as an
  independent third schedule; composing it into the existing orchestrator
  is the minimal, story-text-faithful shape and avoids a third
  `(agent_id, capability_id)` schedule entry for a single one-line call.
- **One Agent per Job (5 agents)** instead of two grouped ones. Rejected
  outright by the operator's own explicit "Just be Concrete / 2
  Pipelines" direction (story's own Non-Goals).

**Consequences:**

- The `run_housekeeping_pass` MCP tool (`@mcp_server.tool()`) is removed/
  renamed — a disclosed shared-interface change. Harmless today since no
  real external Hermes caller exists yet (`P1`, not yet built), but worth
  naming explicitly for whenever Hermes integration lands and might
  otherwise expect the old tool name.
- `librarian-housekeeping` stays a permanent, inert, historical-only
  identity inside `.second-brain/agents_registry.json`'s `created_agents`
  — a small, permanent bit of dead weight in that JSON file, accepted as
  the cost of never rewriting history.
- `list_agents(include_retired=False)`'s new optional parameter is the
  FIRST real "hide but don't delete" primitive in `agent_registry.py`; a
  future story retiring any OTHER agent identity should reuse this exact
  primitive rather than re-deriving a second one.
- `run_company_partner_building_pass()` now also drives a real,
  vault-wide `retrofit_people_from_emails()` sweep every 6 hours by
  default — a real, disclosed new steady-state cost (proportional to
  total Email/raw-message-note count), accepted because it is `REQ-SB-77-
  US-01` Scenario 6b's own explicit, chosen design (both stories decided
  together in this same architect pass), and the function itself is
  already proven idempotent/safe to call repeatedly.
- `REQ-SB-77-US-01`'s own scheduled-self-heal task has a real `depends_on`
  edge onto whichever `REQ-SB-79-US-01` task creates `run_company_
  partner_building_pass()` — a genuine cross-story task dependency the
  decomposer/product-owner must honour (same sprint, or `REQ-SB-79` first
  with a recorded `depends_on_sprints` edge); the instant-hook half of
  `REQ-SB-77-US-01` (Scenario 6a, into the already-`Done` `finalize_
  company_review`) carries no such dependency.

---
