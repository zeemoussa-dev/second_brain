---
id: REQ-SB-72-US-01
title: The Librarian Section — First Housekeeping Pipeline (Thread Rename, Files Backfill, ## Related Ownership Transfer, Company Folder Backfill)
requirement_ids: [REQ-SB-72]
requirement_section: "REQ-SB-72: The Librarian Section — First Housekeeping Pipeline (Thread Rename, Files Backfill, ## Related Ownership, Company Folder Backfill)"
phase: P1
status: Done
gate: flagged
gate_reason: "Coder pass, 2026-08-19: all 9 tasks Done, all 11 locked ACs verified against real, live evidence. Re-flagged (was cleared by the human at /plan-sprints, see prior gate_reason preserved below) solely for T09/AC-11's disclosed partial-evidence gap — 2 of 5 /poc/librarian-* endpoints have a captured live 200 in this session, the other 3 have strong real execution evidence but no captured 200, due to a reproducible coding-session background-process reclaim (ESC-054, REVIEW-QUEUE.md) — not believed to indicate a real defect. Prior gate_reason (human's own ADR-049/ESC-050 sign-off, 2026-08-18): 'Human confirmed directly, 2026-08-18: every real decision in ADR-049 (frontmatter-based Thread matching restored, atomic directory-move rename to <date> <subject>, real agent_schedule_registry wiring at 6h default, the Librarian Section/Agent itself, the ## Related/## Files ownership transfer) was already co-designed turn-by-turn with the operator in the originating conversation before the architect formalized it — same basis ADR-048 was cleared on. ESC-050 (thread_match_merge orphaning risk) was separately discussed directly with the operator and confirmed non-blocking (dormant while email-capture-pipeline stays supervised; real fix scoped as a priority follow-up, not this story's scope). Flag cleared; eligible for /plan-sprints. Prior flagged history (trigger-3, ADR-049 created) preserved in git history of this file.'"
sprint: "SPRINT-063"
created: 2026-08-18
updated: 2026-08-19
---

# REQ-SB-72-US-01 — The Librarian Section — First Housekeeping Pipeline (Thread Rename, Files Backfill, ## Related Ownership Transfer, Company Folder Backfill)

## Story

**As a** Second Brain operator
**I want** a new "Librarian" Section on the Agents Map housing a first,
scheduled/autonomous housekeeping pipeline that renames Thread files to
human-readable names, backfills missing Files/OKF companions and a
structured `## Files` list across the real Thread corpus, takes over sole
ownership of `## Related` from Stage 2's capture pipeline (populating it
with real Person/Company wikilinks instead of raw addresses), and creates
a Customer folder for any mentioned company that doesn't have one yet
**So that** the vault keeps organizing and correcting itself over time
without me having to trigger every housekeeping pass by hand — the way
ongoing vault hygiene should work, unlike capture, which I keep under full
manual control — while anything the pipeline can't resolve on its own
still stops for my own approval, never silently guessed or silently
dropped

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-72: The Librarian Section — First
  Housekeeping Pipeline (Thread Rename, Files Backfill, `## Related`
  Ownership, Company Folder Backfill)*. Raised 2026-08-18, same
  vault-structure conversation as `REQ-SB-70`/`REQ-SB-71`, opened once
  `REQ-SB-71`'s own capture pipelines shipped and real housekeeping gaps
  (`ESC-046`, `ESC-048`) surfaced as live evidence for why this Section is
  needed. Every decision in the PRD text was individually proposed,
  challenged, and confirmed turn-by-turn with the operator in a dedicated
  conversation — not analyst-assumed defaults, including two real
  operator course-corrections during that pass (physical files always
  in-vault, never external references only; the "Section for files in the
  Thread" framing that resolves the `## Related` race-condition risk by
  giving it its own, already-existing, exclusively-owned section, the same
  "one owner per section" rule `REQ-SB-71-US-01` already built).
- **Four concrete, PRD-named tasks, all against the real Thread corpus
  `REQ-SB-71` just captured** (confirmed live: `REQ-SB-71-US-02`'s own
  coder pass drained a real backlog into 252 raw message notes across 127
  real Thread directories):
  1. Rename Thread files/directories to human-readable `<date>
     <subject-without-Re->` names (e.g. `2026-08-16 Ewec Discussion`).
  2. Backfill `files/<slug>/` OKF companions for every real attachment
     already durably staged with none yet, and add a new, structured
     `## Files` section to each Thread's own concept file.
  3. Take over `## Related` ownership from `email_classification.
     synthesize_thread` entirely — `synthesize_thread` stops writing it;
     the Librarian becomes its sole owner, populating real Person/Company
     wikilinks (not raw participant email addresses).
  4. Create a Customer folder for a mentioned company with none yet,
     reusing `REQ-SB-63`'s existing Filing-Expert mechanism unchanged.
  **Explicitly deferred, not this story's scope** (named and consciously
  punted in the same PRD conversation, not oversights): meaningful/topic
  tags (needs its own taxonomy discussion first — the operator's own
  reasoning: this pipeline's 4 tasks are all mechanical, tagging needs a
  vocabulary decision); cross-Thread linking of recurring file artifacts
  (deferred to future Opportunity/Pipeline work).
- **Real code read directly to ground this story, not assumed:**
  - `app/business/pipelines/raw_message_capture.py` (Stage 1, `Done`,
    `REQ-SB-71-US-02-T03`) — confirms real attachment bytes are already
    durably persisted at `Work/Threads/attachments/<slug-of-
    conversation_id>/<slug-of-message_id>/<filename>` via the unmodified
    `vault_writer.write_attachments` (reused verbatim, per that module's
    own docstring) — nothing lost, just not yet promoted to a `files/`
    OKF companion for every attachment. This location is keyed by
    `conversation_id` alone and does **not** move when a Thread's own
    directory is renamed (see `## Constraints`).
  - `app/business/email_classification.py::synthesize_thread` (Stage 2,
    `Done`, `REQ-SB-71-US-02-T05`) — confirmed by direct reading: it
    currently regenerates `## Related` on every call via
    `_build_thread_related_wikilinks`/`replace_body_section(...,
    caller="email_classification.synthesize_thread")`, registered in
    `app/data_access/section_ownership.py` with allow-list
    `{"## Summary", "## Related"}`. This story's own task 3 requires
    dropping `"## Related"` from that same caller's own allow-list the
    moment this story's new caller takes over — never both writing it
    simultaneously (the exact race the PRD's own text names and the
    "one owner per section" resolution sidesteps).
  - `app/data_access/vault_writer.py` — `thread_directory_paths`
    (`Work/Threads/<slug-of-conversation_id>/`, permanently deterministic
    from `conversation_id` alone, `ADR-048` Decision 3/7) and
    `resolve_thread_note_path` (a pure existence check against that SAME
    deterministic path, confirmed by direct reading — no scan) are the
    two primitives task 1's rename requires reworking: once a Thread's
    own directory is renamed to `<date> <subject>`, its path is no longer
    derivable from `conversation_id` alone, so `resolve_thread_note_path`
    (or an equivalent lookup every real caller of it composes —
    `synthesize_thread`, `meeting_classification.py`'s Thread-linking
    fallback) must go back to a frontmatter-scan match on
    `conversation_id`, mirroring `ADR-046`'s own prior scan-based
    contract before `ADR-048` reverted it to deterministic-path. `list_
    thread_notes()`'s own `parent.name == stem` filter keeps working
    unchanged after a rename, since the concept file is renamed alongside
    its own directory, preserving the `<slug>/<slug>.md` invariant.
    `write_file_companion`, `staged_attachment_files` (`REQ-SB-71-US-02-
    T07`) are the Files/OKF backfill's own reused primitives; `rename_
    thread_note`'s own refuse-to-overwrite discipline is the direct
    precedent for a new whole-directory rename primitive this story needs
    (see `## Constraints`).
  - `app/business/vault_filing_expert.py` /
    `app/business/customer_hub_linking.py::ensure_customer_hub_note`
    (`REQ-SB-63`, `Done`) — confirmed: `ensure_customer_hub_note` already
    creates a Customer's OKF directory baseline unconditionally for any
    customer name passed to it (Tier 1, no approval gate) — task 4 reuses
    this exact function unchanged, no new placement-decision logic. The
    SAME module's `_create_cross_cutting_proposal`/
    `finalize_cross_cutting_update` pair (Tier-2-shaped, re-checks the
    model's own naming in Python against the live `known_customers`/
    `known_partners` lists before ever proposing) is the direct, already-
    shipped precedent this story's own "ambiguous finding → Pending
    Approval" safety net (PRD's own standing constraint) is grounded
    against — never a second, divergent proposal/finalize mechanism
    (`ADR-021` point 2's own "never a second, divergent placement
    implementation" rule, reused here by analogy).
  - `app/business/people_extraction.py::find_existing_person_note` —
    already resolves a participant's REAL Person note if one exists and
    honestly omits it otherwise (never fabricates); `_build_thread_
    related_wikilinks` already calls it this way. This story's own
    `## Related` regeneration keeps that exact honest-omission contract —
    coverage of Person links depends on whichever mechanism creates
    Person notes for a given participant (out of this story's own scope,
    see `## Non-Goals`), never guessed.
  - `app/business/section_registry.py` (`REQ-SB-18`/`ADR-014`, `Done`) —
    `create_section(name)`/`set_agent_section(agent_id, section_id)`
    already exist, already proven (Sections are a persisted, user-mutable
    concern independent of Worker/Producer/Expert type). `app/business/
    agent_registry.py` — the 8 existing seed Agents (including
    `vault-filing-expert`, type `expert`) each self-heal into the first
    Section in creation order unless explicitly reassigned; none is
    currently assigned to any Section named "Librarian" (no such Section
    exists yet in code or in this pass's own reading of the runtime
    state).
  - `app/business/agent_schedule_registry.py` (`REQ-SB-47`, `Done`) — the
    single canonical, already-proven home for persisted, composite-key
    (`"<agent_id>::<capability_id>"`) schedule CRUD, the mechanism this
    story's own scheduled/autonomous operation (see below) wires into —
    never a bespoke, parallel scheduling mechanism.
- **Section-creation-machinery scoping — a real judgment call this pass
  makes, not silently assumed, per the launching agent's own explicit
  callout:** this story does **not** build or extend any Section-creation
  machinery. `section_registry.create_section`/`set_agent_section`
  (`REQ-SB-18`, `ADR-014`, already `Done`) are sufficient and already
  proven — this story simply calls them once to create a new "Librarian"
  Section and assign this story's own new Agent identity to it, exactly
  the same way any Settings-driven Section creation already works today.
  `REQ-SB-61`'s own separately-deferred generalization (giving a Section
  its own vault Location/Tags/OKF-conformant directory shape in one
  first-class flow) is **not** needed here and is **not** built by this
  story — the "Librarian" Section is a pure agent-routing/Hub grouping,
  identical in kind to the 5 starting Sections, with no new vault-location
  concept of its own (the Section's own housekeeping WORK targets
  `Work/Threads/`, an already-provisioned location, not a new one the
  Section itself would need to own). This grounds the scoping call in
  already-shipped, proven machinery and the PRD's own explicit framing
  ("mirroring how every other Section already works") rather than a
  coin-flip — see `## Notes` for the full trigger-8 reasoning.
- **Whether the already-shipped `vault-filing-expert` Agent (`REQ-SB-63`)
  is ALSO reassigned into the new "Librarian" Section is a real,
  disclosed, NOT-in-scope question, not silently ignored** — see
  `## Non-Goals`.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: A real Thread's directory and concept file are renamed to a human-readable date+subject name

```gherkin
Given a real Thread directory currently named after its own conversation_id
    slug (Work/Threads/<slug-of-conversation_id>/), with a real concept
    file, real raw messages under messages/, and any already-created
    files/ companions inside it
When the Librarian's housekeeping pipeline processes that Thread
Then the Thread's own directory AND its concept file are renamed to a
    human-readable <date> <subject-without-Re-> stem (e.g. "2026-08-16
    Ewec Discussion"), derived from the Thread's own real frontmatter
  And every raw message note under messages/ and every already-created
    files/ companion moves with the renamed directory, byte-for-byte
    unchanged — nothing is orphaned or duplicated by the rename
```
<!-- AC-ID: REQ-SB-72-US-01-AC-01 -->

### Scenario 2: A new message in the SAME conversation still correctly matches the renamed Thread — no duplicate created

```gherkin
Given a real Thread has already been renamed to its own human-readable
    name (Scenario 1), so its directory no longer matches its own
    conversation_id slug
When a further real message in that SAME conversation is captured and
    Stage 2 (synthesize_thread) is run for it
Then the existing, renamed Thread is found and updated in place — via a
    frontmatter-based match on conversation_id, not a deterministic
    path-based check — and no second, duplicate Thread directory is ever
    created for the same conversation_id
```
<!-- AC-ID: REQ-SB-72-US-01-AC-02 -->

### Scenario 3: A real attachment already durably staged gets a real Files/OKF companion when none exists yet

```gherkin
Given a real attachment already durably persisted under Work/Threads/
    attachments/<slug-of-conversation_id>/<slug-of-message_id>/<filename>
    (Stage 1's own existing, unmodified persistence) has no files/<slug>/
    OKF companion yet under its owning Thread
When the Librarian's housekeeping pipeline processes that Thread
Then a real files/<slug>/ directory is created containing both the
    original attachment file, byte-identical and untouched, and a
    generated OKF companion note carrying a real, genuine summary of that
    file's own content — reusing REQ-SB-71-US-02-T07's own write_file_
    companion mechanism unchanged, never a second, divergent companion
    primitive
```
<!-- AC-ID: REQ-SB-72-US-01-AC-03 -->

### Scenario 4: Re-running the Files backfill never creates a duplicate companion for an attachment that already has one

```gherkin
Given a real attachment already has a real files/<slug>/ OKF companion
    (from Scenario 3, or from Stage 2's own going-forward companioning)
When the Librarian's housekeeping pipeline runs again, including over
    that same attachment
Then no second, duplicate companion is created, and the existing
    companion's own content is left byte-for-byte unchanged
```
<!-- AC-ID: REQ-SB-72-US-01-AC-04 -->

### Scenario 5: The Thread's own ## Files section lists every companioned attachment with a real summary and a working link

```gherkin
Given a real Thread has one or more real files/<slug>/ OKF companions,
    across more than the 2 Threads already companioned before this story
    shipped
When the Librarian's housekeeping pipeline processes that Thread
Then the Thread's own concept file carries a structured ## Files section
    — distinct from ## Summary's own prose — listing each attached file's
    filename, date, a small summary drawn from the companion note's own
    ## Summary, and a real, working link to the companion note itself
```
<!-- AC-ID: REQ-SB-72-US-01-AC-05 -->

### Scenario 6: synthesize_thread stops writing ## Related — the Librarian becomes its sole owner

```gherkin
Given email_classification.synthesize_thread (Stage 2) currently
    regenerates ## Related as a byproduct of every call, per its own
    section_ownership.py allow-list entry
When this story ships
Then synthesize_thread's own registered allow-list no longer includes
    "## Related" — it writes exactly ## Summary, nothing else in the
    body — and any attempt by that caller to write ## Related is rejected
    outright by the SAME code-enforced guard REQ-SB-71-US-01 already
    built, never merely discouraged by convention
```
<!-- AC-ID: REQ-SB-72-US-01-AC-06 -->

### Scenario 7: The Librarian populates ## Related with real Person/Company wikilinks, never raw addresses

```gherkin
Given a real Thread whose content names one or more real, already-known
    companies (beyond its own primary Customer) and whose participants
    include senders with a real, already-existing Person note
When the Librarian's housekeeping pipeline processes that Thread
Then its ## Related section is fully regenerated to contain a real
    [[wikilink]] to the Thread's own Customer hub, a real [[wikilink]]
    for each participant with an existing Person note (any participant
    with none is honestly omitted, never guessed, mirroring the existing
    honest-omission contract), and a real [[wikilink]] for each other
    real company genuinely mentioned in the Thread's own content — never
    a raw, unlinked email address
```
<!-- AC-ID: REQ-SB-72-US-01-AC-07 -->

### Scenario 8: A subsequent Stage 2 re-synthesis of the same Thread leaves ## Related byte-for-byte unchanged

```gherkin
Given a real Thread's ## Related section has already been populated by
    the Librarian (Scenario 7)
When Stage 2 (synthesize_thread) later re-synthesizes that SAME Thread
    again (e.g. because a further raw message arrived)
Then ## Summary is regenerated as normal, and ## Related is left
    byte-for-byte unchanged — proving the Librarian's sole ownership by
    construction, not merely by the two callers happening to agree
```
<!-- AC-ID: REQ-SB-72-US-01-AC-08 -->

### Scenario 9: A company mentioned in a Thread with no existing Customer folder gets one created automatically

```gherkin
Given a real Thread's content confidently names a real company that is
    not yet a known customer (no existing Work/Customers/<slug>/
    directory)
When the Librarian's housekeeping pipeline processes that Thread
Then a new Customer OKF directory is created for that company via the
    existing, unmodified ensure_customer_hub_note mechanism
    (REQ-SB-63) — no new placement-decision logic is invented for this
    story, and no operator approval is required for this confident,
    genuinely-new-entity case
```
<!-- AC-ID: REQ-SB-72-US-01-AC-09 -->

### Scenario 10: A finding the pipeline can't resolve deterministically routes through a real Pending Approval, never silently applied

```gherkin
Given a real Thread's content names a company whose match against the
    live known_customers/known_partners lists is genuinely ambiguous or
    low-confidence (e.g. it could plausibly be an existing Customer under
    a different name, or could be genuinely new) — a real judgment call,
    not a mechanical one
When the Librarian's housekeeping pipeline processes that Thread
Then neither an autonomous link nor an autonomous folder creation
    happens for that ambiguous case — a new, real Pending Approval is
    created instead, the same gate REQ-SB-57's Background amendments
    already use, mirroring REQ-SB-63's own already-shipped propose/
    finalize shape
  And approving it performs the deferred link/create action; declining it
    performs nothing — the finding is never silently dropped and never
    silently applied with no trace
```
<!-- AC-ID: REQ-SB-72-US-01-AC-10 -->

### Scenario 11: The pipeline is reachable via a real HTTP endpoint, runs on its own configured schedule, and its own Agent is housed under a new "Librarian" Section

```gherkin
Given the Librarian's housekeeping pipeline exists as this story's own
    new Agent-tier identity
When the Agents Map / Settings are queried for the current Section and
    Agent set
Then a new "Librarian" Section exists (created via the existing,
    unmodified section_registry.create_section mechanism, REQ-SB-18),
    and this pipeline's own Agent is assigned to it (via the existing,
    unmodified set_agent_section mechanism) — rendered by the Agents Map
    with no prototype change required
  And every one of this pipeline's own capabilities is reachable via a
    real HTTP endpoint, matching this project's standing convention
  And, unlike REQ-SB-70/REQ-SB-71's explicitly manual/API-only pipelines,
    this pipeline is ALSO wired to a real, configured recurring schedule
    (agent_schedule_registry) — it runs on its own, without requiring a
    per-run operator call, while remaining directly, manually triggerable
    too
```
<!-- AC-ID: REQ-SB-72-US-01-AC-11 -->

## Affected Screens

None new — backend and vault-content only. `html-prototype/agents-map.html`
already renders any current Section/Agent set generically (`REQ-SB-18`/
`ADR-014`, already `Done`) — the new "Librarian" Section and its own new
Agent appear automatically once created, with no prototype change needed.
`html-prototype/vault-browser.html`/`note-detail.html` already render
whatever real note/folder structure exists in the vault generically
(`REQ-SB-14-US-01`) — no change needed to display a renamed Thread
directory or a new `## Files` section.

## Dependencies

- **Blocked by (hard):** `REQ-SB-71-US-02` (Email Capture Redesign, `Done`,
  `SPRINT-061`) — the Thread directory shape, raw messages, `synthesize_
  thread`, and `write_file_companion` this story retrofits/extends;
  nothing in this story is buildable before that shape exists.
- **Blocked by (hard):** `REQ-SB-71-US-01` (Section-Ownership Enforcement,
  `Done`, `SPRINT-060`) — this story's new callers (`## Files`, `##
  Related`) must register their own correct allow-list entries against
  that same `section_ownership.py` registry from day one, and `synthesize_
  thread`'s own allow-list must be narrowed in the SAME guarded mechanism
  that story built.
- **Related to:** `REQ-SB-63-US-01` (The Librarian — Vault Filing Expert
  central authority, `Done`, `SPRINT-050`) — `ensure_customer_hub_note`
  (task 4, unchanged reuse) and the `_create_cross_cutting_proposal`/
  `finalize_cross_cutting_update` propose/finalize shape this story's own
  ambiguous-finding Pending-Approval safety net is grounded against;
  never a second, divergent placement/proposal mechanism.
- **Related to:** `REQ-SB-18-US-01`/`REQ-SB-20-US-01` (Dynamic Agent
  Sections & Assignment; Section Hub Intelligence, both `Done`) — the
  Section CRUD/agent-to-Section assignment machinery this story reuses
  unchanged to create the new "Librarian" Section; no new Section-creation
  machinery is built here (see `## Context`).
- **Related to:** `REQ-SB-71-US-03` (Meeting Capture Redesign, `Ready`,
  not yet `Done`) — People-from-attendees auto-extraction; NOT a hard
  dependency, since this story's own `## Related` regeneration honestly
  omits any participant with no existing Person note regardless of which
  mechanism eventually creates one (mirrors `_build_thread_related_
  wikilinks`'s own already-established honest-omission contract).
- **Related to:** `REQ-SB-47-US-01` (Per-Agent Scheduler, `Done`) —
  `agent_schedule_registry.py`, the mechanism this story's own scheduled/
  autonomous operation wires into.
- **External:** none new.

## Constraints

- **Never a second, divergent placement/proposal mechanism** — any
  finding this pipeline can't resolve deterministically reuses `vault_
  filing_expert.py`/`pending_approval_registry`'s existing create-then-
  finalize shape (`ADR-021` point 2's own precedent, reused here by
  analogy); task 4's Customer-folder creation reuses `ensure_customer_hub_
  note` unchanged, no new placement-decision logic invented.
- **A Thread rename is a whole-directory move** — raw messages under
  `messages/` and any already-created `files/` companions move with it,
  byte-for-byte unchanged, never orphaned or duplicated (Scenario 1).
- **The attachments-durable-persistence root stays keyed by
  `conversation_id` alone**
  (`Work/Threads/attachments/<slug-of-conversation_id>/...`), independent
  of any Thread directory rename — this story's Files backfill re-derives
  that same deterministic location; the rename mechanism (task 1) does
  not touch it.
- **Scope is exactly steady-state capture's own existence check**
  (`resolve_thread_note_path`, or whichever primitive real callers
  compose) — the PRD's own explicit carve-out: bulk/retrofit operations
  may still use a path-based lookup internally where useful; this does
  not require every internal code path to change.
- **`## Related` is written by exactly one caller going forward** —
  `email_classification.synthesize_thread` must stop declaring `"##
  Related"` in its own `section_ownership.py` allow-list the moment this
  story's new caller takes over, never both simultaneously (Scenario 6),
  preventing the exact race the PRD's own text names.
- **Every real capability this pipeline exposes is reachable via a real
  HTTP endpoint** (standing project convention) **AND, unlike `REQ-SB-70`/
  `REQ-SB-71`, is ALSO wired to run on its own configured schedule**
  (`agent_schedule_registry`) — the deliberate opposite of those stories'
  explicit no-scheduler constraint, per the operator's own explicit call
  that ongoing housekeeping should run itself.
- **No new Section-creation machinery is built** — reuses `section_
  registry.create_section`/`set_agent_section` (`REQ-SB-18`/`ADR-014`)
  unchanged; `REQ-SB-61`'s own separately-deferred Location/Tags
  generalization is not built here.
- **Meaningful/topic tags and cross-Thread recurring-artifact linking are
  out of scope** — the PRD's own explicit deferrals (see `## Non-Goals`).
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).

## Implementation Tasks

<!-- Decomposer's own table (/plan-tasks step 2, 2026-08-18) — SUPERSEDES the
analyst's own 7-task starting-point table this pass replaced (per this
pipeline's own non-authoritative-analyst-draft rule). 9 tasks: the
Thread-lookup migration warranted real, separate task-level attention
(T01 primitives + T03 Rename Job + T02 caller migration, not folded into
one), and company-mention detection is its own shared building block (T05)
consumed by both T06 (## Related) and T07 (company folders), rather than
duplicated inline in each. See ## Notes for full dependency-graph reasoning. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-72-US-01-T01 | backend | Thread lookup reverts to a frontmatter scan (`resolve_thread_directory`, new) + signature-preserving retarget of `resolve_thread_note_path`/`raw_message_note_path` + new `rename_thread_directory` whole-directory-move primitive | `app/data_access/vault_writer.py` | `../Tasks/REQ-SB-72-US-01-T01-thread-lookup-primitives-and-rename-primitive.md` |
| REQ-SB-72-US-01-T03 | backend | The Rename Job — new `app/business/pipelines/librarian_housekeeping.py`, computing each Thread's `<date> <subject-without-Re->` stem from real frontmatter and renaming via `T01`'s primitive; per-Thread skip-and-report on collision | `app/business/pipelines/librarian_housekeeping.py` (new) | `../Tasks/REQ-SB-72-US-01-T03-rename-job.md` |
| REQ-SB-72-US-01-T02 | backend | Migrates the 3 real callers `ADR-049`'s own direct-reading pass found (beyond `resolve_thread_note_path`'s own zero-call-site retarget) off directly composing `thread_directory_paths(conversation_id)` — `raw_message_capture.py`'s Stage 1 existence check, `synthesize_thread`'s `messages/` read, `meeting_classification._synthesize_history_entry`'s linked-Summary read | `app/business/pipelines/raw_message_capture.py`, `app/business/email_classification.py`, `app/business/meeting_classification.py` | `../Tasks/REQ-SB-72-US-01-T02-migrate-real-callers-off-thread-directory-paths.md` |
| REQ-SB-72-US-01-T04 | backend | Files/OKF backfill Job — reuses `write_file_companion` unchanged for every un-companioned real attachment; new idempotent `## Files` header top-up primitive + structured section writer + new caller registration | `app/business/pipelines/librarian_housekeeping.py`, `app/data_access/vault_writer.py`, `app/data_access/section_ownership.py` | `../Tasks/REQ-SB-72-US-01-T04-files-backfill-job.md` |
| REQ-SB-72-US-01-T05 | backend | Company-mention detection — new dedicated Compass call (`compass_client.py`) + Python re-check against live `known_customers`/`known_partners`, the shared building block `T06`/`T07` both consume | `app/data_access/compass_client.py`, `app/business/pipelines/librarian_housekeeping.py` | `../Tasks/REQ-SB-72-US-01-T05-company-mention-detection.md` |
| REQ-SB-72-US-01-T06 | backend | `## Related` ownership transfer — drops `"## Related"` from `synthesize_thread`'s own allow-list in the SAME change that registers the Librarian's new `populate_thread_related_links` caller; extends the existing honest-omission wikilink builder with `T05`'s company mentions | `app/business/email_classification.py`, `app/business/pipelines/librarian_housekeeping.py`, `app/data_access/section_ownership.py` | `../Tasks/REQ-SB-72-US-01-T06-related-ownership-transfer.md` |
| REQ-SB-72-US-01-T07 | backend | Company folder backfill Job — `ensure_customer_hub_note` reused unchanged for a confident, genuinely-new mention; a new `propose_librarian_company_link` Pending Approval (mirroring `_create_cross_cutting_proposal`/`finalize_cross_cutting_update`'s shape) for an ambiguous one | `app/business/pipelines/librarian_housekeeping.py`, `app/api/pending_approvals_router.py` | `../Tasks/REQ-SB-72-US-01-T07-company-folder-backfill-and-ambiguous-finding-approval.md` |
| REQ-SB-72-US-01-T08 | backend | New "Librarian" Section + `librarian-housekeeping` Agent (idempotent bootstrap, existing unmodified mechanism) + orchestrating `run_housekeeping_pass` (rename first) + 5 new `/poc/*` endpoints on the existing `email_poc_router.py` | `app/business/pipelines/librarian_housekeeping.py`, `app/main.py`, `app/api/email_poc_router.py` | `../Tasks/REQ-SB-72-US-01-T08-agent-section-and-endpoints.md` |
| REQ-SB-72-US-01-T09 | backend | Scheduled/autonomous wiring — `run_housekeeping_pass` becomes a real, granted, mutating Skill (required by the REAL `agent_schedule_registry.create_or_update_schedule` gate, a grounding correction beyond `ADR-049`'s own illustrative snippet) + a real, persisted 6-hour default schedule entry | `app/business/skill_tools.py`, `app/business/skill_registry.py`, `app/main.py` | `../Tasks/REQ-SB-72-US-01-T09-scheduled-wiring.md` |

**Dependency graph:** `T01 → T03 → T02 → T06` (`T06` also needs `T05`); `T01 → T04`; `T05` independent, feeds `T06` and `T07`; `T03`+`T04`+`T06`+`T07` → `T08` → `T09`. No cycles.

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — manual mode still in effect, per `Implementation/Pipeline.md`
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Meaningful/topic tags** (e.g. `#stage/proposal`, `#renewal-risk`) —
  explicitly deferred by the PRD to a future taxonomy-design pass; this
  pipeline's own 4 tasks are all mechanical, per the operator's own
  reasoning.
- **Cross-Thread linking of recurring file artifacts** (e.g. the same
  report resent repeatedly) — explicitly deferred to future Opportunity/
  Pipeline work; each attachment instance is captured independently here.
- **Retrofitting `REQ-SB-08`/`09`/`10`'s still-live, untouched
  classification modules** — unaffected by this story, mirrors
  `REQ-SB-63-US-01`'s own established non-retrofit precedent.
- **Reassigning the already-shipped `vault-filing-expert` Agent
  (`REQ-SB-63`) into the new "Librarian" Section** — a real, disclosed
  scoping call, not silently ignored: the PRD frames this story as
  building the Section's FIRST housekeeping pipeline, not reorganizing an
  already-`Done` story's own Agent-to-Section assignment. Left as a
  possible future follow-up, not this story's own scope.
- **Building `REQ-SB-61`'s generalized Location+Tags Section-creation
  flow** — this story reuses the EXISTING `create_section`/
  `set_agent_section` mechanism (`REQ-SB-18`/`ADR-014`) unchanged; no new
  Section-creation machinery is built here (see `## Context`).
- **Designing a comprehensive, closed, final housekeeping-pipeline
  platform** — this is the FIRST of a growing family the Librarian
  Section will eventually house, mirroring `REQ-SB-63-US-01`'s own
  "growing set of Agents, not a one-go" framing; no speculative
  extensibility hooks are built here for future pipelines nothing yet
  needs.
- **Backfilling any pre-`REQ-SB-71-US-02` flat-shape Thread notes** (if
  any remain in the vault, outside the 127 real directory-shaped Threads
  Stage 1 already drained the real backlog into) — a separate, disclosed
  concern (`ESC-048`), not this story's own scope; left to the human
  decision already recorded there.

## Notes

**Prototype parity:** N/A — no new `html-prototype/` screen region.
`agents-map.html` already renders any current Section/Agent set
generically (`REQ-SB-18`); `vault-browser.html`/`note-detail.html` already
render vault content generically. See `## Affected Screens`.

**Section-creation-machinery scoping — full trigger-8 reasoning (why this
does NOT need to be flagged):** the launching agent explicitly asked this
pass to make this call rather than assume it. `section_registry.
create_section`/`set_agent_section` are already `Done`, already proven
(`REQ-SB-18-US-01`, `SPRINT-011`), and structurally sufficient for
exactly what this story needs — one new Section, one new Agent assigned to
it. The PRD's own text explicitly frames the Librarian Section as
"mirroring how every other Section already works," not as needing a new
kind of Section. `REQ-SB-61` (giving a Section its own vault Location/
Tags in one first-class flow) is a SEPARATE, already-deferred requirement
whose own deferral condition (a second, independent real request for a
new KB area) is not satisfied by this story — the Librarian Section's own
housekeeping work targets `Work/Threads/`, an already-provisioned
location it does not need to own. This is a grounded, cited-precedent
call, not a coin-flip among equally-valid readings — trigger 8 does not
fire.

**Mechanism-level questions left to `/plan-tasks`, not resolved by this
pass (Gherkin above specifies the OUTCOME, not the mechanism — mirrors
`REQ-SB-69-US-01`/`REQ-SB-71-US-02`'s own identical precedent):**

1. **The exact shape of the frontmatter-based lookup reversal (T01)** —
   whether `resolve_thread_note_path` itself is retargeted in place
   (signature-preserving, mirroring `ADR-048` Decision 7's own reversal
   shape) or a new, parallel lookup is introduced and callers are
   migrated — left to the architect, who must also decide whether this
   needs its own ADR amendment or a new ADR (trigger 3 is architect-only,
   not this role's to resolve or flag).
2. **The concrete company-mention detection technique (T04/T05)** —
   whether the Librarian's housekeeping pipeline reuses `vault_filing_
   expert.determine_placement_and_file`'s own existing grounded-decision
   call shape (already proven for the structurally similar `cross_
   cutting_implication` re-check), or a new, dedicated LLM call scoped to
   "which known/plausible companies does this Thread's content mention" —
   left to the architect. Either way, the re-check-in-Python-against-the-
   live-vault-structure discipline (`ADR-021` point 2) must not be
   diluted.
3. **The exact ambiguous-finding Pending-Approval payload shape and its
   own `action_id`** — mirrors `_create_cross_cutting_proposal`'s own
   shape structurally, but the concrete confidence threshold and payload
   fields are a real architect design, not asserted here (same "architect
   proposes a concrete answer, decomposer locks ACs against it" precedent
   `REQ-SB-63-US-01`/`REQ-SB-56-US-01`/`REQ-SB-57-US-01` already
   established).
4. **The exact new Agent id, Section id, endpoint route(s), and schedule
   interval** — left to the architect/decomposer, following the existing
   `/poc/*`-or-dedicated-router and `Schedule tab`/`agent_schedule_
   registry` conventions already established elsewhere in this codebase;
   no specific interval is asserted here (Scenario 11 only requires that
   a real, configured schedule exists, never naming one).
5. **Whether the rename Job (T01/T02) must run before or independently of
   the Files/Related/Company Jobs (T03-T05) within one pipeline pass** —
   the Gherkin above is written so it holds either way (each Scenario's
   own Given/When is self-contained); sequencing is a Job-chain ordering
   decision left to the architect, mirroring `ADR-041`'s own established
   fork/merge/branch-shape latitude.

**Why this does NOT trip trigger 1 (material assumption) despite the
above:** every genuinely open item above is a MECHANISM question this
project's own role boundaries assign to the architect at `/plan-tasks` —
the PRD's own text was worked out turn-by-turn with the operator and
resolves every SCOPE-level question (what the 4 tasks are, what's
deferred, that this runs scheduled/autonomous, that ambiguous findings
route through Pending Approval) directly; this pass adds no scope the PRD
did not already state. The one real, disclosed pass-level judgment call
(Section-creation-machinery scoping) is grounded in cited, already-shipped
precedent, not a gap-filling guess (see above).

**Why this does NOT trip trigger 2:** `REQ-SB-72` carries no `<!--
Draft -->` marker in the PRD — its own footnote confirms every decision
was individually proposed, challenged, and confirmed turn-by-turn with
the operator, finalized text.

**Why this does NOT trip trigger 3:** ADR creation/change is the
architect's own trigger, not this role's; this pass discloses the
partial-`ADR-048`-Decision-7-reversal clearly (see `## Context`/task T01)
but does not itself create or edit `Implementation/Architecture/ADR.md`.

**Why this does NOT trip trigger 4:** no `ESCALATIONS.md` entry was
written — nothing in this pass is a backward pipeline step or an
out-of-scope event; every open question above is a forward, PRD-
acknowledged mechanism question.

**Why this does NOT trip trigger 5 (oversized):** 7 starting tasks,
directly comparable to `REQ-SB-71-US-02`'s own 7-task shape and smaller
than `REQ-SB-69-US-01`'s own 8-task shape — both already proven buildable
in one working context; not oversized.

**Why this does NOT trip trigger 7:** no contradictory PRD inputs found —
the PRD's own text is internally consistent throughout, including its own
explicit disclosure of the two real operator course-corrections that
shaped it.

**Why this does NOT trip trigger 8, beyond the Section-machinery call
already reasoned above:** the one story-shape decision this pass makes
(ONE story covering all 4 tasks, rather than splitting per-task) is
grounded directly in the operator's own PRD-quoted framing ("Five parts,
one cohesive redesign" — precedent's own wording pattern — here: "this
pipeline's 4 tasks are all mechanical," i.e. facets of one Section's one
housekeeping pass, not four independently-scoped features) and mirrors
`REQ-SB-63-US-01`'s own identical "kept as one story since they are all
facets of the same... mechanism, not independently designed things"
precedent — not a coin-flip among equally-valid splits.

gate: clear 2026-08-18 — no MUST-FLAG trigger fired (see the itemized
trigger-by-trigger reasoning above).

**What to do next:** eligible for `/plan-tasks REQ-SB-72-US-01` — the
architect resolves the mechanism-level questions above (including
whether the partial `ADR-048` Decision 7 reversal needs a new ADR or an
amendment to the existing one, which will set `gate: flagged` per this
project's own standing ADR-review trigger, same as every other story in
this batch), then the decomposer locks ACs and writes tasks.

---

## Architect pass (`/plan-tasks` step 1, 2026-08-18)

**Architecture scope: §"The Librarian Section — First Housekeeping
Pipeline" (`REQ-SB-72-US-01`, `ADR-049`)** in `architecture.md` — the
coder is bounded to this section (Thread lookup/rename, Files/OKF
backfill + `## Files`, `## Related` ownership transfer, company-mention
detection + Pending Approval, Section/Agent/endpoints/scheduling) plus
its directly-cited unchanged primitives from §"Vault Base Provisioning +
Redesigned Email/Meeting Capture" (`ADR-048`) — `section_ownership.py`'s
guard mechanism, `write_file_companion`, `staged_attachment_files`,
`thread_directory_paths`, `list_thread_notes` — and §"Vault Filing Expert"
(`ADR-021`)/"The Librarian — Vault Filing Expert generalized..."
(`REQ-SB-63`) for `ensure_customer_hub_note`/the propose-finalize shape.

**All 5 mechanism-level questions this story's own `## Notes` left open
are resolved, with a real ADR (`ADR-049`) — see
`Implementation/Architecture/ADR.md`:**

1. **Thread lookup reversal shape:** `resolve_thread_note_path` itself is
   retargeted IN PLACE (signature-preserving — zero call-site changes for
   its existing callers), now composing a new, shared `resolve_thread_
   directory(conversation_id) -> Path | None` frontmatter-scan primitive.
   Direct reading during this pass found the story's own Context
   undercounted the blast radius: TWO more real callers beyond the two it
   named (`raw_message_capture.py`'s Stage 1 existence check;
   `synthesize_thread`'s own `messages/` directory read, distinct from its
   already-correctly-named create-vs-update check) also directly compose
   `thread_directory_paths(conversation_id)` and would silently break
   (read from/write to a stale path) the first time any Thread is renamed
   — all three are now in scope alongside the two originally named. This
   needs its own new ADR (not an amendment to `ADR-048` — an Accepted ADR
   is never rewritten): `ADR-049`, partially superseding `ADR-048`
   Decision 3's own "permanent deterministic-path" sub-decision only.
2. **Company-mention detection technique:** a NEW, dedicated Compass call
   (technique-only reuse of `compass_client.summarize_content`, re-checked
   in Python against live `known_customers`/`known_partners` before ever
   acting) — never `vault_filing_expert.determine_placement_and_file`
   itself, which is scoped to single-item NEW-content placement, a
   different-shaped problem from extracting mentions from already-filed
   content. See `ADR-049` Decision 5/Alternative 6.
3. **Ambiguous-finding Pending-Approval shape:** new `action_id=
   "propose_librarian_company_link"`, payload mirroring `_create_cross_
   cutting_proposal`'s own shape, finalized by a new `finalize_librarian_
   company_link` handler — see `ADR-049` Decision 5.
4. **Agent/Section/endpoint/schedule identity:** Section `"librarian"`,
   Agent `"librarian-housekeeping"` (type `worker`), five new endpoints on
   the EXISTING `email_poc_router.py` (no new router), one orchestrating
   `run_housekeeping_pass` capability wired to a new `agent_schedule_
   registry` entry (default 6-hour interval, operator-adjustable, never a
   locked-AC value) — see `ADR-049` Decisions 6-8.
5. **Job sequencing:** the Rename Job runs FIRST in the orchestrated pass
   (so Files/Related/Company-folder Jobs operate on each Thread's own
   final, current directory); those three have no ordering dependency
   among themselves — see `ADR-049` Decision 7/Alternative 8.

**A real, newly-escalated finding, disclosed not fixed (`ESC-050`):**
direct, full-body reading of the still-live `thread_match_merge`
(`email_capture_pipeline.py`, `supervised`-only per `ESC-048`) found a
SECOND, more severe failure mode beyond `ESC-048`'s own original
"duplicate Thread for a flat-shape conversation" description: for an
ALREADY-EXISTING new-shape Thread, `thread_match_merge`'s own still-live
legacy rename logic (`ADR-046`) moves the concept file OUT of its own
directory, ORPHANING `messages/`/`files/` — confirmed to already fire
TODAY, independent of this story shipping. `email_capture_pipeline.py`
stays outside this story's own `## Files to Modify`/`## Non-Goals` — not
touched by this pass, per this project's own "coder is scope-bounded, any
out-of-scope event escalates" rule applied here at the architect layer
too. See `ESCALATIONS.md` → `ESC-050` and `REVIEW-QUEUE.md`.

**Gate:** `flagged` — `gate_reason: trigger-3 (ADR-049 created)`. Per
`Implementation/Pipeline.md`, an ADR trigger does NOT halt the stage — the
decomposer runs next regardless, so the human reviews `ADR-049` and the
resulting tasks together in one pass. `REVIEW-QUEUE.md` carries two new
pointers: one for `ADR-049` itself, one for `ESC-050`.

---

## Decomposer pass (`/plan-tasks` step 2, 2026-08-18)

**All 11 Gherkin scenarios above are locked as `REQ-SB-72-US-01-AC-01`
through `AC-11`**, one-to-one against the analyst's own untagged scenarios
(tightened only for buildability, no scope change) — every AC-ID tag is
appended immediately after its own scenario's closing Gherkin fence, all
locked by default (none marked `locked: false`; every locked AC has a real,
observable outcome — no unverifiable AC found).

**Task table above supersedes the analyst's own 7-task starting point** —
9 tasks, grounded directly in `ADR-049`'s own real mechanism text (not the
analyst's own pre-architecture guess): `T01` (Thread-lookup primitives) →
`T03` (Rename Job) → `T02` (the 3 real callers `ADR-049`'s own direct-
reading pass found still directly composing `thread_directory_paths`,
migrated off it) → `T06` (`## Related` transfer, also needs `T05`); `T01` →
`T04` (Files/OKF backfill); `T05` (company-mention detection, standalone)
feeds both `T06` and `T07` (company folder backfill); `T03`+`T04`+`T06`+
`T07` → `T08` (Agent/Section/orchestration/endpoints) → `T09` (scheduled
wiring). No cycles. `T02` is sequenced AFTER `T03` (not merely both
depending on `T01`) because `T02`'s own AC-02 verification needs a real,
already-renamed Thread as its test fixture — a genuine verification-order
dependency the analyst's/architect's own task-shape text did not surface.

**AC → task mapping:** AC-01 → `T03`; AC-02 → `T02`; AC-03/AC-04/AC-05 →
`T04`; AC-06/AC-07/AC-08 → `T06`; AC-09/AC-10 → `T07`; AC-11 → `T09`
(verified comprehensively there, once the Section/Agent/endpoints from
`T08` and the schedule from `T09` all exist together). `T01` and `T05` are
building-block tasks with no directly-locked AC of their own — mirrors this
codebase's own established precedent (`REQ-SB-63-US-01-T01`/`T02`) —
consumed and AC-verified downstream. Every locked AC has at least one
AC-tagged manual verification step in exactly the task(s) named above; no
locked AC is left without a tagged step (confirmed by direct cross-check
against all 9 task files' own `## Tests` blocks before finalizing this
pass).

**Verification technique, reconciling this pipeline's own real-HTTP-
endpoint standing constraint with this story's own real build-order:** the
5 new `/poc/librarian-*` endpoints do not exist until `T08` — `T01`-`T07`'s
own AC-tagged steps are real, direct Python-shell function calls against
the real, configured vault (this codebase's own long-established, repeatedly
-used verification technique, not a weaker substitute), and AC-11 (the one
scenario actually ABOUT HTTP reachability) is verified via the real,
genuinely-new `/poc/*` endpoints once `T08`/`T09` land — never conflating
"the business logic is correct" (function-level) with "the capability is
reachable via HTTP" (endpoint-level), each proven at the layer that actually
demonstrates it.

**A real, disclosed grounding correction found during this pass, not itself
a new architectural decision (`T09`'s own Context/Notes):** `ADR-049`
Decision 8's own illustrative `agent_schedule_registry.create_schedule(...)`
snippet does not match the real function name/contract — direct reading of
`agent_schedule_registry.py`/`skill_registry.py` found `create_or_update_
schedule` (the real name) hard-refuses any capability that is not already a
granted, mutating `skill_tools.SKILLS` member, dispatched via `skill_
registry.invoke_skill`. `T09` grounds the schedule in this REAL mechanism
(a new Skill entry + a `_MIGRATION_GRANT_SEED` grant, mirroring `REQ-SB-69-
US-01-T04`'s own established "genuinely new grant reusing that same seed
dict" precedent) rather than the ADR's own simplified pseudocode. This does
not change `ADR-049`'s own decision or consequence — it is the same
mechanism-shaped, cited-precedent, no-new-ambiguity kind of task-shaping
call this story's own `## Notes` already reasoned through once (Section-
creation-machinery scoping) — not a MUST-FLAG trigger.

**Why this pass does NOT fire a NEW trigger, beyond the architect's own
already-standing `ADR-049` flag (which this role does not clear, per
`Implementation/Pipeline.md`):**
- **Trigger 1 (material assumption):** every task-shaping choice this pass
  made (the `insert_body_section_if_missing`/`detect_mentioned_companies`
  new primitives, `ensure_librarian_agent_and_section`'s app-lifespan
  placement, `T09`'s grounding correction above) is a mechanical, cited-
  precedent composition choice within decomposer's normal task-authoring
  latitude, not a scope/requirement gap filled by guessing.
- **Trigger 5 (oversized):** 9 tasks sits at this project's own established,
  repeatedly-proven single-session ceiling (`SPRINT-021`/`SPRINT-030`, 9
  tasks/L; `SPRINT-049`, 8 tasks/L) — not oversized for this story's real
  complexity (a 3-real-caller lookup migration, 2 backfill Jobs, a shared
  detection building block, an ownership transfer, a Pending Approval, and
  a new Agent/Section/schedule identity).
- **Trigger 6 (unverifiable AC):** every locked AC has a concrete, real,
  observable verification path (a real function return value, a real file
  on disk, a real HTTP response, a real Pending Approval record) — none
  found unverifiable.
- **Trigger 7 (contradictory inputs):** the launching pass's own "5 call
  sites (2 named + 3 found)" framing and `ADR-049`'s own precise Decision 1
  text ("THREE call sites... not the two the story's own Context names")
  are reconciled by following `ADR-049`'s own more precise, authoritative
  count (3 real callers migrated in `T02`, plus `resolve_thread_note_path`
  itself retargeted with zero call-site change in `T01`) — logged here as a
  scope-internal reconciliation, mirroring `REQ-SB-55-US-01-T07`'s own
  established "reconcile by following the more authoritative text" Learnings
  precedent, not treated as a blocking contradiction.
- **Trigger 8 (multiple equally-valid / unclear):** the 9-task split (vs.
  the analyst's own non-authoritative 7) is grounded directly in `ADR-049`'s
  own real mechanism text, not a coin-flip among equally-valid shapes.

**Status:** `Draft → Ready` — every AC is locked, every locked AC has a
tagged verification step in at least one task, and `depends_on` is acyclic
(confirmed above). `gate` stays `flagged` (`gate_reason` unchanged —
`trigger-3`, `ADR-049`) — the decomposer does not clear an architect's own
ADR flag; the human reviews `ADR-049`/`ESC-050` and this pass's own 9 tasks
together, per the architect's own Notes above. All 9 new task files are
written at `status: Ready` in lockstep with this story's own transition, per
`Implementation/Pipeline.md`'s "task status moves in lockstep with the
story" rule.

**What to do next:** this story is now `status: Ready` with a complete,
locked task graph, but `gate: flagged` — per `Implementation/Pipeline.md`'s
"Promotion of a flagged item" human gate, the human resolves the flag (reads
`ADR-049`/`ESC-050` at `REVIEW-QUEUE.md`, reviews this pass's own 9 tasks
alongside them) before `/plan-sprints` picks this story up.

---

## Product-owner pass (`/plan-sprints`, 2026-08-18)

Assigned to `SPRINT-063` (single sprint, all 9 tasks — no split; full
grouping/sizing/split-vs-single reasoning recorded in
`Implementation/Sprints/SPRINT-063-librarian-section-first-housekeeping-pipeline.md`
`## Grouping Rationale & Sizing` and `## Notes`). No `depends_on_sprints`
edge needed — `SPRINT-060`/`SPRINT-061` (this story's own hard
prerequisites) are already `Done`; every task-level `depends_on` edge
resolves entirely within this story's own 9 tasks. Sprint `gate: clear`,
advanced `Draft → Ready`, eligible for `/implement-sprint SPRINT-063`. This
story's own `gate: flagged` (`ADR-049`, `trigger-3`) had already been
cleared directly by the operator earlier the same day (see frontmatter
`gate_reason`) — unaffected by, and unrelated to, this sprint-grouping pass.

---

## Coder pass (`/implement-sprint SPRINT-063`, 2026-08-18/19, resumed across sessions)

**All 9 tasks `Done`; all 11 locked ACs verified against real, live evidence** —
`T01`-`T05` in prior sessions (per their own task-file frontmatter/Implementation
Logs, not redone here); `T06`-`T09` in this resumed session, after two prior
attempts at `T06` were themselves interrupted by infrastructure issues (per this
session's own launch context) — this pass confirmed the code those attempts had
already produced for `T06`/`T07` was correct by direct reading before building
further, rather than redoing it.

**AC-06/AC-07/AC-08 (`T06`):** real Thread `D05C9002AFC20B4DB222A45E202B1862`
before/after byte-comparisons via the real `POST /poc/synthesize-thread`
endpoint, plus a direct guard-check confirming `section_ownership.
SectionWriteNotAllowed` is raised (not merely undeclared) for `synthesize_
thread`'s own now-narrowed allow-list. **AC-09/AC-10 (`T07`):** real Customer
folders created for confident mentions with zero Pending Approvals among them;
5 (later 10) real ambiguous mentions routed to real Pending Approvals; one
approved live (folder created), one declined live (nothing created). **AC-11
(`T08`/`T09`):** "Librarian" Section + `librarian-housekeeping` Agent
confirmed idempotently bootstrapped across 3 real app restarts (no
duplicate); its own real, persisted 6-hour `agent_schedule_registry` entry
confirmed idempotent across 2 restarts; 2 of 5 `/poc/librarian-*` endpoints
have a captured live `200`, the other 3 have strong real execution evidence
(live Compass call logs, real on-disk `## Related` mutations across 87/126
Threads, the real Pending Approval lifecycle above) but no captured `200`
within this session, due to a reproducible coding-session-specific
background-process reclaim — disclosed in full in `T09`'s own Implementation
Log and `ESC-054`, `gate: flagged` on `T09` for human spot-check (not
believed to indicate a real defect; the underlying capability is
independently proven correct via the strongest available real evidence
channel each time). No orphaned processes and no concurrent calls to the
same mutating function occurred at any point — verified via live process/log
checks before every retry, per this session's own standing constraint.

**Real vault-hygiene progress this session (operational, not itself a
locked-AC requirement):** `## Related` population 20→87/126 real Threads;
10 real ambiguous company-mention Pending Approvals created; several real new
Customer folders created for confident mentions. The remainder will complete
via `T09`'s own real, persisted, now-live 6-hour schedule, running on the
operator's normally-launched backend — the story's own intended self-healing
design.

**Story status:** `Ready → Done`. `gate: flagged` (was already `clear` per
the human's own earlier `ADR-049` sign-off; re-flagged here solely for the
`T09`/`AC-11` partial-evidence disclosure above — see `REVIEW-QUEUE.md`).
`SPRINT-063` itself is `Done` — see its own `## Retrospective`.
