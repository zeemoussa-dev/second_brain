---
id: REQ-SB-57-US-01-T01
title: Project Synthesizer core (Glimpse regeneration + History-line conclusion trigger) + Thread-pipeline trigger wiring + new Agent identity
parent_story: REQ-SB-57-US-01
requirement_id: REQ-SB-57
type: backend
status: Done
gate: flagged
gate_reason: "scope-internal judgement calls logged for human spot-check — see Implementation Log"
phase: P1
depends_on: []
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-57-US-01-T01 — Project Synthesizer core + Thread-pipeline trigger wiring

## Parent Story

- Story: [[REQ-SB-57-US-01]] — `../UserStories/REQ-SB-57-US-01-project-and-customer-status-synthesizer-agents.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-57 *Project & Customer Status Synthesizer Agents*

---

## Objective

Build the Project Synthesizer's own core mechanism — a real, callable
`synthesize_project(customer, project, evidence_text="")` that fully
regenerates a Project's `## Glimpse` and appends a `log.md` line only on
a genuine `status` conclusion — and wire the ONE real trigger point this
task owns: a real Thread update (`thread_match_merge`, inside the Email
Capture Pipeline's own compiled graph) automatically calling it, in the
SAME pipeline run, for the Thread's own already-linked Project.

---

## Starting State → End State

**Before / Inputs:**
- `app/business/email_classification.py::thread_match_merge` never
  writes anywhere near a Project's Glimpse — confirmed by direct
  reading. It DOES leave the Thread's own current, fresh `customer`/
  `project` frontmatter and a freshly-regenerated `## Summary` on the
  final, post-rename path by the time it returns.
- `app/business/pipelines/email_capture_pipeline.py::_build_graph` forks
  after `thread_match_merge` into `consult_librarian` (ALWAYS an
  additional destination, fires on every Thread update) and
  `route_to_project` (only when `created`) — `_route_after_thread_
  match_merge` is the real routing function; `EmailCapturePipelineState`
  is the real typed state dict.
- `app/data_access/vault_writer.py::create_okf_directory_baseline`
  already writes a Project's own `<slug>.md` concept file with body
  `"## Glimpse\n\n## Background\n"` (`REQ-SB-54`, `Done`).
  `build_project_concept_frontmatter` supplies the concept file's
  baseline frontmatter (`type`, `title`, `tags`, `status: "active"`,
  `stale_after`, `generated`, `verified`, `sources`) — no `status`
  history-tracking field exists yet.
  `replace_body_section`/`read_body_section` are the real header-scoped
  regenerate/read primitives; `list_thread_notes`/`resolve_thread_note_
  path` are the real Thread-enumeration primitives; `append_person_note_
  update_line` is the real generic unconditional-append primitive
  (already used for both `log.md`-shaped and body-line-shaped growth
  elsewhere in this codebase, despite its Person-era name).
- `app/business/agent_registry.py::_SEED_AGENTS` has no entry for any
  Synthesizer identity yet — `"email-capture-pipeline"`/`"meeting-
  capture"` are the real precedent shape to mirror (`name`, `type:
  "worker"`, `settings`, `actions`).

**After / Outputs:**
- New module `app/business/project_customer_synthesizer.py` with:
  - `resync_project_from_thread(thread_path) -> dict | None` — reads
    the Thread's OWN current frontmatter fresh (`vault_writer.
    read_note`); returns `None` (a genuine no-op) when `project` is
    absent/blank (a not-yet-routed Thread); otherwise calls and returns
    `synthesize_project(customer, project, evidence_text=<the Thread's
    own current `## Summary`, via `read_body_section`>)`. This is the
    ONE shared helper every real trigger call site (this task's own
    pipeline node, and `T03`'s Meeting-link wiring) calls — neither
    trigger call site ever reads/writes Glimpse content itself.
  - `synthesize_project(customer, project, evidence_text="") -> dict` —
    the actual Job that performs the write (the ONLY function in this
    codebase, after this task, allowed to touch a Project's own `##
    Glimpse` or `log.md`):
    1. Enumerates the Project's own currently-linked Threads via a new
       `vault_writer.list_threads_for_project(customer, project)`
       primitive (below).
    2. Builds `## Glimpse` content as a mechanical rollup — one bullet
       per linked Thread, each carrying that Thread's own already-
       synthesized opening line/`## Summary` excerpt (read via
       `read_body_section`/the Thread's own opening-region text) plus a
       `[[wikilink]]` to it — reusing already-synthesized content,
       never a second, divergent Compass call (mirrors `consult_
       librarian`'s own documented "never a second Compass call"
       precedent).
    3. Writes it via `vault_writer.replace_body_section(concept_path,
       "## Glimpse", <rollup content>)` — never `insert_body_line_if_
       missing`.
    4. History-line conclusion trigger (`architecture.md` → "Project &
       Customer Synthesizer"): reads the Project's own CURRENT `status`
       and its own `last_synthesized_status` frontmatter field
       (defaulting `"active"` if the key is absent — an old Project
       predating this task, or its own first-ever synthesis pass).
       Appends one dated line to the Project's own `log.md` (via
       `append_person_note_update_line`) **iff** `status` differs from
       `last_synthesized_status` AND `status` is one of `won`/`lost`/
       `renewed` — never on `active`/`on_hold`. Then, REGARDLESS of
       whether a line was appended, unconditionally writes
       `last_synthesized_status = status` via `upsert_frontmatter_key`
       — this is what makes a later, unchanged re-observation of an
       already-terminal `status` a true no-op (idempotent).
    5. Returns `{"customer": customer, "project": project, "concluded":
       <bool — True only when THIS call appended a log.md line>,
       "latest_evidence_text": evidence_text}` — `latest_evidence_text`
       is plumbed through untouched for `T02`/`T04`'s own later use;
       this task's own code does nothing else with it.
    6. Does **NOT** call any Customer-level function — that cascade
       call is `T02`'s own scope. Leave a clear one-line comment at the
       end of the function marking where `T02` adds it (e.g. `# T02
       adds: project_customer_synthesizer.synthesize_customer(...)
       here`).
- `app/data_access/vault_writer.py` gains:
  - `list_threads_for_project(customer, project) -> list[Path]` —
    composes `list_thread_notes()` (never a new, second `Work/Threads/`
    glob), filters by reading each Thread's own `customer`/`project`
    frontmatter for an exact match. Returns `[]` if none match — never
    raises for a Project with no linked Threads yet.
  - `build_project_concept_frontmatter` gains one additive key:
    `"last_synthesized_status": "active"` — the SAME default `status`
    itself already uses, so a brand-new Project's first-ever synthesis
    pass naturally compares `status` against `"active"` with zero
    special-casing.
- `app/business/agent_registry.py::_SEED_AGENTS` gains one new entry,
  `"project-customer-synthesizer"` (`type: "worker"`), `settings`
  describing the real trigger mechanism (explicitly NOT a schedule —
  "Trigger" setting value naming the real Thread-update/Meeting-link-in/
  Project-change-cascade call sites), and NO `actions` requiring a real
  handler this task builds (no `run_capture_now`-style action — nothing
  in this story's own scope manually triggers a run; see `## Out of
  Scope`). This is what makes the new identity render on the Agents
  Map's already agent-count-agnostic canvas (story's own `## Affected
  Screens`).
- `app/business/pipelines/email_capture_pipeline.py`:
  - `EmailCapturePipelineState` gains `project_synthesis_result: dict |
    None`.
  - New node `_trigger_project_synthesis_node`, calling
    `project_customer_synthesizer.resync_project_from_thread(state[
    "thread_result"]["thread_path"])`.
  - `_route_after_thread_match_merge` gains `"trigger_project_
    synthesis"` as an ALWAYS-fired additional destination (mirrors
    `consult_librarian`'s own unconditional-branch shape exactly —
    fires on every Thread update, `created=True` and `created=False`
    alike; never gates `route_to_project` or vice versa).
  - `_build_graph` registers the new node and its own fixed edge to
    `END`, and adds `"trigger_project_synthesis"` to the destinations
    list passed to `add_conditional_edges`.

---

## Files to Modify

- `src/backend/app/business/project_customer_synthesizer.py` (new file)
- `src/backend/app/data_access/vault_writer.py` — add
  `list_threads_for_project`; add the one additive
  `last_synthesized_status` key to `build_project_concept_frontmatter`.
- `src/backend/app/business/agent_registry.py` — add the
  `"project-customer-synthesizer"` `_SEED_AGENTS` entry.
- `src/backend/app/business/pipelines/email_capture_pipeline.py` — add
  the new node/state key/routing-destination/edge described above.

---

## Constraints

- Inherits from parent story — in particular: **exactly one owner
  writes `## Glimpse`/`log.md` per Project note** (`REQ-SB-54` point 7)
  — no code this task adds anywhere OUTSIDE `project_customer_
  synthesizer.py` ever calls `replace_body_section`/`append_person_
  note_update_line` against a Project's own concept file or `log.md`.
  The new pipeline node/helper only ever CALLS into the Synthesizer —
  it never assembles or writes Glimpse content itself.
- **`## Glimpse` is always fully regenerated via `replace_body_section`,
  never incrementally patched** (`REQ-SB-54` point 8) — never `insert_
  body_line_if_missing`.
- **History-line trigger is exactly the architect-proposed, operator-
  confirmed rule** (`architecture.md` → "Project & Customer Synthesizer
  — the 'genuinely concludes' History-line bar") — do not invent a
  different bar. `on_hold` is an explicit pause, never a conclusion.
- **Never a second, divergent Compass/LLM call for Glimpse content** —
  the rollup reuses each linked Thread's own already-synthesized
  content; this task's own code makes zero new Compass calls.
- **`resync_project_from_thread` reads the Thread's own frontmatter
  FRESH on every call** (`vault_writer.read_note`) — never trusts a
  caller-passed `customer`/`project`, and returns `None` cleanly (no
  exception) for a Thread with no `project` set yet.
- **Never calls `synthesize_customer`** — that cascade call is `T02`'s
  own addition to `synthesize_project`'s own body; this task leaves the
  clearly-marked seam only.
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`) — the new pipeline node stays inside `app/business/`.

---

## Tests

**Manual verification steps:**

1. `[REQ-SB-57-US-01-AC-01]` Using real vault fixtures (a real, existing
   Customer; a disposable Project directory created via `vault_writer.
   create_project_directory_baseline`; a disposable Thread with its
   `project` frontmatter set to that Project's own title, mirroring
   what `finalize_thread_project_routing` would do at a real Approve),
   call `thread_match_merge` for a new message on that same
   `conversation_id` directly (mirrors this codebase's own established
   "call the real Job function directly" verification precedent, e.g.
   `REQ-SB-69-US-01-T08`), then run the compiled graph's own real
   invocation path (or call `_trigger_project_synthesis_node`/
   `resync_project_from_thread` directly against the same `thread_
   result`) — confirm the Project's own `<slug>.md` `## Glimpse` section
   now contains a real bullet referencing the updated Thread's own
   current content, written within the SAME call chain as the Thread
   update. Confirm (by direct code inspection, not just output) that no
   function outside `project_customer_synthesizer.py` performed the
   `replace_body_section` call against `## Glimpse`.
2. `[REQ-SB-57-US-01-AC-04]` With the same fixtures, leave `status` at
   `"active"` throughout, and run `synthesize_project` twice in a row
   (two separate "evidence updates"). Confirm `## Glimpse` is rewritten
   both times (content reflects whatever Threads are linked at call
   time) and `log.md` stays empty across both calls — no line added for
   routine, non-concluding activity.
3. Non-AC regression / idempotency check: set the fixture Project's
   `status` to `"won"`, call `synthesize_project` three times in a row
   with no further status change. Confirm exactly ONE `log.md` line was
   appended (on the first call, the transition `active`→`won`) and
   `last_synthesized_status` reads `"won"` after every call — the
   second and third calls are true no-ops for `log.md`.
4. Non-AC regression check: call `resync_project_from_thread` against a
   real, disposable Thread with NO `project` frontmatter key set at
   all. Confirm it returns `None` and touches no file.
5. Clean up every disposable fixture (Project directory, Thread note)
   created during verification; confirm pre-existing real vault content
   is byte-for-byte/mtime-unchanged afterward.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `REQ-SB-57-US-01-AC-01` — a real Thread update triggers a full
      `## Glimpse` rewrite on its linked Project, in the same call
      chain, with no other function writing to `## Glimpse` directly
- [x] `REQ-SB-57-US-01-AC-04` — routine, non-concluding evidence updates
      rewrite `## Glimpse` but never append a `log.md` line
- [x] `synthesize_project`'s History-line comparison is idempotent
      across repeated calls with an unchanged, already-terminal `status`
- [x] `resync_project_from_thread` is a safe no-op for a not-yet-routed
      Thread
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Calling `synthesize_customer` or any Customer-level write — `T02`.
- The Route-to-Project-approval trigger call site
  (`finalize_thread_project_routing`) — `T02`.
- The Meeting-link-in trigger call site (`meeting_classification.py`) —
  `T03`.
- Background-amendment detection/proposal — `T04`.
- A `run_capture_now`-style manual-trigger action or any scheduled tick
  for the new `project-customer-synthesizer` identity — this mechanism
  is evidence-triggered only, per the story's own Non-Goals/Context
  ("NOT on a fixed schedule"); no such action exists anywhere in this
  story's own scope.
- Any change to `thread_match_merge`'s own existing body beyond what the
  new pipeline node composes around it — `thread_match_merge` itself is
  untouched by this task.

---

## Context / Notes

`Implementation/Architecture/architecture.md` → "Project & Customer
Synthesizer — the 'genuinely concludes' History-line bar" (under `##
Data Model`) is the full architectural reasoning for the History-line
rule, operator-confirmed 2026-08-18 (see the parent story's own `##
Notes`). `ADR-042` (unchanged, referenced) is the OKF data-model ADR
this task's new primitives extend — no new ADR.

**One new Agent identity, not two** (decomposer's own implementation
choice, documented in the parent story's own `## Notes` — the story's
Constraints explicitly leave this open and require every AC to hold
under either choice).

`app/business/vault_filing_expert.py::_create_cross_cutting_proposal`/
`finalize_cross_cutting_update` and `email_classification.py::route_to_
project`/`finalize_thread_project_routing` are the two closest real
precedents for a "propose in the owning module, perform the deferred
write in the same module, trigger from elsewhere" shape — this task's
`synthesize_project`/`resync_project_from_thread` split mirrors that
same discipline (the trigger call site never performs the write).

---

## Implementation Log

**Built (2026-08-18):**

- New module `app/business/project_customer_synthesizer.py`:
  `resync_project_from_thread(thread_path)` (fresh-read no-op helper) and
  `synthesize_project(customer, project, evidence_text="")` (the real
  Glimpse-regenerate + History-line Job), exactly per the task's own End
  State — the ONLY module allowed to call `replace_body_section` against
  a Project's own concept file or `append_person_note_update_line`
  against its own `log.md` (confirmed by direct grep of the whole
  `app/` tree: `email_classification.py`/`thread_summary_backfill.py`
  are the only other `replace_body_section` callers, both against a
  Thread's own `## Summary`/`## Related`, never `## Glimpse`;
  `cockpit/person_note_proposals.py`/`skill_tools.py` are the only other
  `append_person_note_update_line` callers, both against a Person note,
  never a Project's `log.md`). Leaves the `# T02 adds:
  synthesize_customer(...)` seam comment at the end of
  `synthesize_project`, never calls it.
- `app/data_access/vault_writer.py`: added `list_threads_for_project`
  (composes `list_thread_notes()`, filters by exact
  `customer`/`project` frontmatter match, `[]` on no match) placed
  directly after `list_thread_notes()`; added the additive
  `"last_synthesized_status": "active"` key to
  `build_project_concept_frontmatter`.
- `app/business/agent_registry.py`: added the `"project-customer-
  synthesizer"` `_SEED_AGENTS` entry (`type: "worker"`, `actions: []`,
  mirroring `vault-filing-expert`'s own no-real-handler-yet precedent —
  no `run_capture_now`-style action, per this task's own Out of Scope).
- `app/business/pipelines/email_capture_pipeline.py`: added
  `project_synthesis_result: dict | None` to
  `EmailCapturePipelineState`; added `_trigger_project_synthesis_node`
  (calls `project_customer_synthesizer.resync_project_from_thread`
  only — never touches Glimpse content itself); `_route_after_thread_
  match_merge` now always returns `["consult_librarian", "trigger_
  project_synthesis"]` plus `"route_to_project"` when `created`; graph
  registers the new node with its own fixed edge to `END` and adds it to
  the `add_conditional_edges` destinations list. Updated the module's
  own top docstring and `_route_after_thread_match_merge`'s docstring
  for accuracy (both now describe the third, always-fired branch)
  — a documentation-only change, no behavior beyond what's listed above.

**Scope-internal judgement calls (logged for human spot-check, gate:
flagged per this session's own protocol):**

1. **Glimpse bullet format** — the task's own End State names the
   content ("a bullet per linked Thread, each carrying that Thread's own
   already-synthesized opening line/`## Summary` excerpt... plus a
   `[[wikilink]]`") but not an exact string template. Implemented as
   `- [[<thread-filename-stem>]] <thread_name> — <## Summary content>`
   per Thread, `_No linked Threads yet._` when none are linked yet (a
   real, honest empty state rather than a blank section).
2. **`## Summary` used as the "opening line" excerpt** — no
   `read_body_opening_line`/equivalent reader primitive exists anywhere
   in `vault_writer.py` (confirmed by direct grep); only `## Summary` is
   actually readable via `read_body_section`, so the rollup uses that
   region alone, exactly as the task's own alternative phrasing allows
   ("the Thread's own opening-region text" was offered as one option,
   `## Summary` as the other — the only one with a real reader).
3. **`log.md` line wording/date format** — the task specifies WHEN a
   line is appended (the History-line bar) but not its exact text.
   Wrote `"{YYYY-MM-DD UTC} — Project \"{project}\" status changed to
   {status}."`, mirroring this codebase's own `{date} — {description}`
   dated-line convention already used elsewhere (e.g.
   `summarize_attachment`'s own `dated_entry` shape,
   `_fallback_attachment_entry`).

**Manual verification (real vault, `VAULT_PATH` =
`<OPERATOR_VAULT_OLD>`; real, pre-existing Customer
`Core42`; disposable Project `"REQ-SB-57-T01 Verification Project"` and
two disposable Threads, both fully removed afterward — confirmed the
real, pre-existing `Core42` OKF files and all 6 real pre-existing
`Work/Threads/*.md` notes were byte-identical/untouched afterward, and
the empty leftover `projects/` directory was removed):**

- `[REQ-SB-57-US-01-AC-01]` **PASS.** Created the Project directory
  baseline, created a disposable Thread via a real `thread_match_merge`
  call (message 1), set the Thread's own `project` frontmatter key to
  the Project's title (mirroring `finalize_thread_project_routing`'s
  own real write), then called `thread_match_merge` again for a genuinely
  NEW message on the same `conversation_id` (message 2, `created=False`)
  — mirroring this codebase's own "call the real Job function directly"
  precedent. Called `resync_project_from_thread` directly against that
  same `thread_result` (same call chain). Observed: the Project's own
  `<slug>.md` `## Glimpse` was rewritten in full, containing a real
  bullet `[[<thread-stem>]]` plus the Thread's own real, Compass-
  synthesized `## Summary` content reflecting BOTH messages (confirmed
  the returned summary text explicitly referenced "the staging
  environment is fully configured and the customer has asked for a demo
  next week" — message 2's own content, not stale). Confirmed by direct
  code inspection (grep across `app/`) that no function outside
  `project_customer_synthesizer.py` calls `replace_body_section` against
  `"## Glimpse"` anywhere in this codebase.
- `[REQ-SB-57-US-01-AC-04]` **PASS.** With `status` left at `"active"`
  throughout, called `synthesize_project` twice more in direct
  succession (two separate "evidence updates"). Observed: `## Glimpse`
  was rewritten on both calls (verified via re-read after each);
  `log.md` stayed byte-empty (`''`) across both calls — no line added
  for routine, non-concluding activity.
- **Non-AC idempotency regression:** set the fixture Project's `status`
  to `"won"` via `upsert_frontmatter_key`, called `synthesize_project`
  three times in a row with no further status change. Observed: call 1
  returned `concluded: true` and appended exactly one `log.md` line
  (`"2026-08-17 — Project \"REQ-SB-57-T01 Verification Project\" status
  changed to won."`); calls 2 and 3 both returned `concluded: false` and
  appended nothing further — `log.md` held exactly one line after all
  three calls. `last_synthesized_status` read `"won"` after every call.
  PASS.
- **Non-AC regression — no-op for un-routed Thread:** created a second
  disposable Thread (no `project` frontmatter key at all) via a real
  `thread_match_merge` call, then called `resync_project_from_thread`
  against it directly. Observed: returned `None`; the Thread's own
  on-disk mtime was byte-identical before/after (confirmed via
  `os.path.getmtime`) — a genuine no-op, no file touched. PASS.
- **Cleanup:** every disposable fixture (Project directory + both
  disposable Threads) was removed at the end of the same verification
  run; independently re-confirmed afterward that `Core42`'s own 4 real
  OKF files and all 6 real, pre-existing `Work/Threads/*.md` notes were
  present and untouched, and removed the one empty leftover `projects/`
  directory the test left behind under `Core42` (the fixture Project
  itself was already removed; only the now-empty parent directory
  needed a separate cleanup pass).

**Verification technique note:** ran the two real trigger call sites
(`thread_match_merge` directly, `resync_project_from_thread` directly)
rather than invoking the full compiled LangGraph via
`run_email_capture_pipeline` — the Tests block names both as equally
valid ("or call `_trigger_project_synthesis_node`/
`resync_project_from_thread` directly against the same `thread_
result`"), and calling the real functions directly avoids needing a
real staged-email fixture (`email_staging`) purely to exercise this
task's own node, while still exercising the exact same real code path
`_trigger_project_synthesis_node` calls. The graph wiring itself
(`trigger_project_synthesis` registered as an always-fired additional
destination) was independently confirmed via `get_job_tree()`, which
listed `trigger_project_synthesis` with `depends_on: ["thread_match_
merge"]` alongside `consult_librarian`/`route_to_project`.

gate: flagged 2026-08-18 (coder) — trigger 8-class scope-internal
judgement calls only (Glimpse bullet format, `## Summary`-as-excerpt,
`log.md` line wording), all logged above for human spot-check; no
MUST-FLAG escalation trigger fired (no new dependency, no shared-
interface change, no ADR deviation, no unanticipated file, every locked
AC verified live). `REQ-SB-57-US-01-T01` → `status: Done`.
