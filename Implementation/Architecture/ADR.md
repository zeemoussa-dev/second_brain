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
