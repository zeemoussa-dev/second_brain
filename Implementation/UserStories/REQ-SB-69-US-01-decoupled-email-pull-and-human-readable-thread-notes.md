---
id: REQ-SB-69-US-01
title: Decouple the Outlook pull out of Classify/Thread-Match-Merge/Route-to-Project into a durable vault-local staging step, and make Thread notes read like a human wrote them (filename, dates, wikilinks)
requirement_ids: [REQ-SB-69]
requirement_section: "REQ-SB-69: Decoupled Email Pull + Human-Readable, Graph-Connected Thread Notes"
phase: P1
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-046 created) — standing human-review breadcrumb, unresolved; all 8/8 tasks Done, all 11 locked ACs verified live"
sprint: "SPRINT-056"
created: 2026-08-17
updated: 2026-08-17
---

# REQ-SB-69-US-01 — Decoupled Email Pull + Human-Readable, Graph-Connected Thread Notes

## Story

**As a** Second Brain operator
**I want** the Outlook email pull to run as its own independent step —
fetching raw email content and writing it to a durable vault-local staging
area, then being completely done with Outlook — so a stall anywhere inside
that one Outlook call can never again wedge the whole Classify/
Thread-Match-Merge/Route-to-Project pipeline or the shared Outlook-COM
dispatch lock every other job also needs, and **I want the Thread notes
that pipeline produces to read like a human wrote them** — a real
filename instead of a GUID, human-readable dates instead of raw machine
timestamps, and real Obsidian `[[wikilinks]]` into the Customer/Person/
Project notes a Thread is actually about
**So that** a repeat of tonight's two separate 20+-minute live hangs can
never happen again, and opening a Thread note — or looking at Obsidian's
own graph view — tells me at a glance what it's about and what it
connects to, without reading a raw GUID or a machine timestamp

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-69: Decoupled Email Pull +
  Human-Readable, Graph-Connected Thread Notes*. Raised 2026-08-17,
  operator-directed, immediately following a **second, separate** real
  Outlook-COM hang the same night — after `REQ-SB-68-US-01`'s own
  non-blocking-dispatch fix had already shipped (`Done`, `SPRINT-055`),
  proving that fix necessary but not sufficient: the real stall lives one
  layer deeper, inside `Fetch`'s own single monolithic Outlook call, not
  in how that call gets dispatched onto the event loop. The operator's own
  words, quoted directly in the PRD: *"Here is my Approach, Have one Agent
  to Hand the pull of All Emails Separately And then we will have a
  pipeline to Summarize the Files and Emails from the Vault instead of
  outlook."* The operator explicitly granted full autonomy end-to-end for
  this requirement ("You are in full control... You will not be able to
  know what is blocking us") — open implementation questions this pass
  cannot get a live answer to tonight are resolved directly, with the
  reasoning disclosed here and in `## Notes`, rather than left flagged.
- **Real code read directly to ground this story, not assumed:**
  - `app/business/pipelines/email_capture_pipeline.py::run_email_capture_pipeline`
    (lines ~256-316) — its very first line is
    `emails = outlook_com.list_recent_mail(limit=limit)`, a single
    synchronous call, BEFORE the per-tick loop that invokes the compiled
    `Classify → Thread-Match/Merge → Route-to-Project` graph once per new
    email. This module's own docstring documents the current design
    explicitly: *"`Fetch` stays a pre-graph, per-tick batch step
    (`ADR-043` point 2)... invokes the compiled graph ONCE per new
    email."* None of `classify`, `summarize_attachment`,
    `thread_match_merge`, `route_to_project`, `detect_recurring_pattern`,
    or `consult_librarian` import or call `outlook_com` — confirmed by
    direct reading of `email_classification.py`'s own imports. **This
    story's job is to move `list_recent_mail`'s own call out from ahead
    of that loop entirely**, so a stall inside it can no longer block the
    loop, and the loop can no longer block the next pull either.
  - `app/data_access/outlook_com.py::list_recent_mail` (lines 216-249) —
    what that one call actually does: `pythoncom.CoInitialize()` →
    connects to Outlook COM (`_connect_namespace`) → gets the Inbox →
    `items.Sort("[ReceivedTime]", True)` → iterates every candidate item,
    resolving sender (`_resolve_sender`, an Exchange-user lookup per
    email), extracting attachments (`_extract_attachments`, a
    save-to-temp-file-then-read-then-delete round trip per attachment),
    and resolving recipients (`resolve_mail_recipients`, another
    per-recipient Exchange-user lookup) — all inside the one call,
    entirely synchronous, entirely inside the shared Outlook-COM dispatch
    lock's hold window (`REQ-SB-45`/`REQ-SB-47-US-01`, `ADR-037`). This is
    the concrete call whose 2026-08-17 stalls (one 20+ minute hang, and a
    second, separate one later the same night even after a
    supposedly-unlimited Outlook access grant) wedged the whole tick.
  - `ADR-043` (`Implementation/Architecture/ADR.md`) point 2 — the
    Accepted decision this requirement asks the architect to reconsider:
    *"`Fetch` is a pre-graph, per-tick batch step... no persisted
    queue/staging between `Fetch` and the rest of the graph, and no
    cross-email graph state."* This story's whole first half is exactly
    that reconsideration — introducing the persisted, durable staging
    boundary `ADR-043` point 2 explicitly did not have. Not decided here
    (that's the architect's call at `/plan-tasks` step 1) — named here so
    the Gherkin below is grounded in what's actually true today.
  - `ADR-042` point 5 — Thread's current path resolution: *"path resolved
    deterministically from `conversation_id` alone... mirroring
    `hub_note_path`/`meeting_note_path`'s existing 'deterministic path
    from a stable key, no separate lookup index' precedent."* Concretely,
    `vault_writer.thread_note_path(conversation_id)` returns
    `Work/Threads/<slug-of-conversation_id>.md` with **no** lookup step —
    `thread_match_merge` calls `thread_note_exists(conversation_id)` then
    writes straight to that computed path. **This requirement's filename
    ask (last-message-date + conversation name, not the raw GUID) breaks
    that "deterministic from a stable key alone" invariant** — the
    filename can no longer be computed from `conversation_id` alone
    without either a lookup step or a hash-based disambiguator (see
    below). This is a real, disclosed architectural consequence for the
    architect to resolve at `/plan-tasks` — not something this pass
    decides (see `## Notes`).
  - `vault_writer.meeting_note_filename_stem(subject, start)` (lines
    844-868) — **the exact, already-shipped precedent for "human-readable
    filename, collision-safe" this story's Thread-filename ask should
    mirror**: `<subject>-<date>-<hash-suffix>`, where the suffix is an
    8-hex-char SHA-256 prefix of the full `f"{subject}|{start}"` string —
    not a raw counter, not silently overwriting. `EntryID`/
    `GlobalAppointmentID` were tried first and live-confirmed non-unique
    across a real recurring series (`ESC-002`, `ESC-012`) before this
    hash scheme was adopted. The email-note path
    (`email_classification.py` line 651) uses a related but distinct
    scheme: `f"{received[:10]}-{subject}-{id[-8:]}"`, suffixed by a slice
    of Outlook's own `EntryID`. Thread's own stable identity key is
    `conversation_id` (not a per-message id like `EntryID`/`start`) —
    whichever exact disambiguator the architect picks, hashing/slicing
    `conversation_id` itself (not the mutable `last_message_at`) keeps the
    disambiguator itself stable across the renames point below implies,
    even though the filename's own date component moves. Left to
    `/plan-tasks`, not decided here.
  - `app/business/meeting_classification.py::_date_proximity_gap_days`
    (lines 86-103) and `_link_to_thread_by_fallback_heuristic` (lines
    125-191) — **the one real, already-shipped, currently-live piece of
    code that programmatically parses a Thread's `last_message_at`
    frontmatter value**: `datetime.strptime(thread_last_message_at[:10],
    "%Y-%m-%d")`, used by `REQ-SB-56-US-01`'s own Thread↔Meeting
    fallback-linking date-proximity bar. Confirmed by direct repo-wide
    search: no other module parses `last_message_at` programmatically
    (`my_day.py` has no reference to it at all). This is the concrete
    fact grounding the PRD's own "any date field other, already-shipped
    code actually parses... may keep a machine-parseable form alongside"
    clause — see `## Constraints` and `## Notes` for how this pass treats
    it (a locked product-level Constraint: this one real consumer must
    keep working; the exact field-split mechanism is left open, per the
    PRD's own text, to `/plan-tasks`).
  - `customer_hub_linking.link_note_to_customer_hub` (lines 49-57) and
    `people_extraction.link_email_to_person` (lines ~231-253) — the
    already-shipped `**Label:** [[NoteStem]]` inline-wikilink primitives
    this codebase already uses for Email notes (`**Customer:**
    [[Hub]]`, `**Sender:** [[PersonStem]]`). **`ADR-043` point 7's own
    Consequences explicitly declined to call `link_note_to_customer_hub`
    from `Thread-Match/Merge`** ("the inline `**Customer:** [[Hub]]`
    wikilink was Email's own per-note linking convention, superseded by
    the OKF concept file's own `sources:` provenance field... Thread-
    Match/Merge does not itself write `sources:`" — only
    `ensure_customer_hub_note` is called today, never the inline-link
    half). **This requirement's wikilink ask directly reopens that
    specific `ADR-043` point 7 decision, for Thread notes specifically**
    — a real, disclosed architectural reopening, not a fresh invention;
    flagged for the architect's attention in `## Notes`, not resolved by
    this pass.
  - `route_to_project` (lines 374-476) — a Thread's `project` frontmatter
    key is written only once `route_to_project`'s own Pending Approval is
    approved (`finalize_thread_project_routing`); it is **absent by
    design** on every newly created Thread (`ADR-042` point 7). This is a
    real, structural timing fact, not a guess: a wikilink to a Project
    note can only exist on a Thread AFTER that approval resolves, never
    on a brand-new, not-yet-routed Thread.
- **Why one story, not two** (mirroring this project's own established
  `REQ-SB-53`/`REQ-SB-43`/`REQ-SB-44` split precedents, and directly
  analogous to `REQ-SB-68-US-01`'s own "two tightly-coupled fixes, one
  story" shape): the PRD's own `<!-- Raised -->` comment states the
  content-quality asks are folded in explicitly *"since they touch the
  same Thread-writing code path this restructuring already has to
  touch"* — both halves land in the same real files
  (`email_capture_pipeline.py`, `email_classification.py::
  thread_match_merge`, `vault_writer.py`'s Thread primitives), and the
  content-quality half is only worth doing once the pull-decoupling half
  stops the pipeline from randomly wedging mid-work (the PRD's own
  sequencing framing, verbatim). Splitting into two stories would force
  an artificial ordering dependency between two stories touching
  overlapping code, for no isolation benefit — the same reasoning
  `REQ-SB-68-US-01` used to keep its own two coupled fixes (non-blocking
  dispatch + Scheduling monitor) as one story. See `## Notes` for the
  full disclosed reasoning (mirroring `REQ-SB-53-US-01`'s own documented
  split-decision precedent, applied here to a keep-together decision
  instead).

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: A real, live-triggered pull stages raw email content without the downstream pipeline ever calling Outlook directly

```gherkin
Given a real, live-triggered Outlook pull (email_pull.pull_and_stage_emails)
    runs
When it completes
Then the raw content of every newly fetched email is written to a
    durable, vault-local staging area (.second-brain/email_staging/)
  And none of app/business/pipelines/email_capture_pipeline.py's
    Classify/Thread-Match-Merge/Route-to-Project code paths (nor
    Summarize-Attachment, Detect-Recurring-Pattern, or Consult-Librarian)
    import or call outlook_com.* directly — verified by confirming none
    of those modules import outlook_com at all
```
<!-- AC-ID: REQ-SB-69-US-01-AC-01 -->

### Scenario 2: A deliberately-slow or stalled pull no longer blocks already-staged mail from being processed

```gherkin
Given the Outlook pull step (pull_email) is deliberately slow or
    genuinely stalled (mirroring the real, live-confirmed 20+ minute
    hang of 2026-08-17)
When a separate, independently-dispatched run (process_staged_email)
    processes mail that was already staged before the pull stalled
Then that already-staged mail is still classified, threaded, and filed
    normally, in the same or a later run — it does not wait for the
    stalled pull to finish, because pull_email and process_staged_email
    never share a lock
```
<!-- AC-ID: REQ-SB-69-US-01-AC-02 -->

### Scenario 3: A stall in Compass/vault processing no longer blocks the next pull from running

```gherkin
Given the Classify/Thread-Match-Merge/Route-to-Project processing of
    previously staged mail (process_staged_email) is itself slow or
    genuinely stalled
When the next scheduled or manually-triggered Outlook pull (pull_email)
    fires
Then it runs and stages newly fetched mail successfully, without waiting
    for the stalled processing to finish
```
<!-- AC-ID: REQ-SB-69-US-01-AC-03 -->

### Scenario 4: A single staged email's own processing failure doesn't lose or block the rest of that run

```gherkin
Given one staged email's own Classify/Thread-Match-Merge/Route-to-Project
    processing fails partway through (e.g. a real CompassError)
When the run that raised that failure ends
Then that email is left staged (not removed from
    .second-brain/email_staging/) and unmarked in
    processed_email_ids.json, so a later run retries it — mirroring this
    pipeline's own already-shipped per-email failure posture, now
    preserved across the new staging boundary
  And every other staged email in the same run is still processed
    normally (removed from staging and marked processed), not lost or
    skipped because of the one failure
```
<!-- AC-ID: REQ-SB-69-US-01-AC-04 -->

### Scenario 5: A newly created Thread note's filename is human-readable, never a raw GUID

```gherkin
Given a brand-new conversation's first message is captured and staged
When its Thread note is created
Then the Thread note's filename is derived from its last-message date,
    human-readable, plus the conversation's own subject/name (its new
    thread_name frontmatter field)
  And the filename is never the raw conversation_id GUID (e.g. never
    "01D26A7530444A23803A002210620160.md")
```
<!-- AC-ID: REQ-SB-69-US-01-AC-05 -->

### Scenario 6: Two Threads that would otherwise collide on date+name are safely disambiguated

```gherkin
Given two distinct real conversations whose last-message date and
    derived thread_name would otherwise produce the identical Thread
    filename
When both Thread notes are created
Then both are written as two distinct files, disambiguated from one
    another by the conversation_id-derived hash suffix
  And neither Thread note's content is ever silently overwritten by the
    other's
```
<!-- AC-ID: REQ-SB-69-US-01-AC-06 -->

### Scenario 7: An existing Thread's filename tracks its new last-message date on a later message, without losing content

```gherkin
Given an existing Thread note whose filename reflects an earlier
    last-message date
When a later message in the same conversation is captured and merged
Then the Thread note's filename updates to reflect the new last-message
    date (still human-readable, still collision-safe)
  And the Thread's existing frontmatter, ## Summary, ## Transcript, and
    ## Attachments content is preserved intact across that change — no
    content is lost or reset
```
<!-- AC-ID: REQ-SB-69-US-01-AC-07 -->

### Scenario 8: Every human-visible date on a Thread note renders human-readable

```gherkin
Given a real captured message is merged into a Thread note
When the operator opens that Thread note in Obsidian
Then the note's new last_message_at_display frontmatter field renders in
    a human-readable form (e.g. "Aug 16, 2026, 1:02 PM"), not a raw
    machine timestamp (e.g. "2026-08-16 13:02:57.246000+00:00") —
    while last_message_at itself stays machine-parseable, unchanged
  And each ## Transcript entry's own per-message timestamp renders the
    same human-readable way
```
<!-- AC-ID: REQ-SB-69-US-01-AC-08 -->

### Scenario 9: The existing Thread↔Meeting date-proximity fallback linking keeps working, unregressed

```gherkin
Given REQ-SB-56-US-01's already-shipped Thread-Meeting fallback linking
    (meeting_classification.py::_link_to_thread_by_fallback_heuristic)
    depends on parsing a real Thread's own last_message_at field to
    compute a date-proximity gap
When this story's human-readable date rendering ships
Then that existing date-proximity matching continues to correctly link
    real Meetings to real Threads exactly as it did before this story —
    verified live against real captured Threads and Meetings
```
<!-- AC-ID: REQ-SB-69-US-01-AC-09 -->

### Scenario 10: A Thread note carries at least one real wikilink to an entity it actually relates to

```gherkin
Given a Thread note is created or updated for a real, matched Customer
When the operator opens that Thread note
Then its body's ## Related section carries at least one real
    [[wikilink]] to a Customer, Person, or Project note it actually
    relates to
  And opening Obsidian's own graph view shows a real edge connecting the
    Thread note to that entity note
```
<!-- AC-ID: REQ-SB-69-US-01-AC-10 -->

### Scenario 11: No fabricated or placeholder wikilink is ever written for a relationship that doesn't actually exist

```gherkin
Given a Thread's matched customer is "Unsorted" (no real customer was
    determined), or a participant/Project cannot be resolved to a real
    note
When that Thread note is created or updated
Then no fabricated or placeholder [[wikilink]] is written into its
    ## Related section for that unresolved relationship — an honest
    absence (an empty but present ## Related section), never a guessed
    link
```
<!-- AC-ID: REQ-SB-69-US-01-AC-11 -->

## Affected Screens

None — backend and vault-content only. No PRD text for `REQ-SB-69` names
a UI surface. `html-prototype/system-health.html`'s Scheduling section
(`REQ-SB-68-US-01`, `Done`) currently shows the whole
`email-capture-pipeline` job as one row; whether the new, decoupled Pull
step warrants its own separate row there is a real, disclosed open
question left to the architect at `/plan-tasks` (see `## Notes`) — not
assumed or built here, since the PRD's own Acceptance text for this
requirement names no such UI change.

## Dependencies

- **Blocked by:** none. This is a **new** story extending already-`Done`
  work (`REQ-SB-55-US-01`, `REQ-SB-56-US-01`, `REQ-SB-63-US-01`,
  `REQ-SB-67-US-01`, `REQ-SB-68-US-01` are all `Done`) — specs are
  append-only (`Implementation/Pipeline.md` hard rule 1); this story never
  edits those `Done` stories' own files.
- **Related to:** `REQ-SB-55-US-01` (`Done`, `SPRINT-049`) — the
  `Fetch → Classify → Thread-Match/Merge → Route-to-Project` pipeline
  this story restructures the `Fetch` half of; every other Job's own
  topology, approval gating, and tag-accumulation behavior (`ADR-043`
  points 3-6) is unchanged by this story.
- **Related to:** `REQ-SB-56-US-01` (`Done`, `SPRINT-053`) — the
  Thread↔Meeting fallback linker whose real `last_message_at` parsing
  (Scenario 9, above) must keep working unregressed.
- **Related to:** `REQ-SB-63-US-01` (`Done`, `SPRINT-050`) — the
  `Consult-Librarian` fork point; unaffected in topology, but its own
  input (the Thread note's path/content) is touched by this story's
  filename/date/wikilink changes.
- **Related to:** `REQ-SB-67-US-01` (`Done`, `SPRINT-054`) — real
  per-Thread summary synthesis, whose `replace_body_section`/
  `read_body_section` calls against a Thread's own path must keep
  resolving correctly across this story's filename-rename mechanism
  (Scenario 7).
- **Related to:** `REQ-SB-45` / `REQ-SB-47-US-01` (`Done`, `ADR-037`) —
  the shared Outlook-COM dispatch lock this decoupling reduces the real
  hold-duration of (the lock itself is unchanged; only how long Fetch
  holds it changes).
- **Related to:** `REQ-SB-68-US-01` (`Done`, `SPRINT-055`) — the
  non-blocking-dispatch fix this requirement's own raised-comment
  explicitly names as "necessary but not sufficient," since the real
  stall lives one layer deeper, inside `Fetch`'s own monolithic call.
- **Related to, not revived:** `REQ-SB-53-US-01` (`Parked`) — an earlier
  Pull/Tag/Link/Store split proposal that gave Pull its own Agent-tier
  identity; superseded by `ADR-043` point 6's single-Agent-identity
  Pipeline shape (`REQ-SB-55-US-01`'s own Context: "stays `Parked`, not
  reworked"). This story does not revive that model — decoupling Pull's
  own *timing* from the rest of the graph is a different question from
  giving it its own addressable Agent identity; whether the latter is
  also warranted here is a real open question left to the architect (see
  `## Notes`), not assumed.
- **External:** none new.

## Constraints

- **No downstream Job may import or call `outlook_com` after this story
  ships** — `Classify`, `Summarize-Attachment`, `Thread-Match/Merge`,
  `Route-to-Project`, `Detect-Recurring-Pattern`, `Consult-Librarian` all
  read exclusively from the new staging area from now on. Mirrors
  `REQ-SB-55`'s own "no second, independent classification call chain"
  Constraint precedent, extended here to Outlook access specifically.
- **The staging area must be durable and vault-local, not memory-only** —
  a process restart between Pull and processing must not silently lose
  staged content (the PRD's own "writes it to a durable vault-local
  staging area" text is a hard requirement, not a suggestion).
- **`meeting_classification.py::_date_proximity_gap_days`'s real,
  already-shipped parsing of a Thread's `last_message_at` must keep
  working** — a machine-parseable form of the date it reads must survive
  this story unchanged in meaning (`%Y-%m-%d`-prefix-parseable). The
  PRD's own text explicitly leaves the exact field-split mechanism
  (rename the existing key and add a new human-readable one; keep the
  existing key machine-form and add a new human-readable sibling; or
  something else) as "an implementation decision, not a product one" —
  this Constraint locks the OUTCOME (that real consumer must not break),
  not the mechanism.
- **Every already-shipped Thread behavior this story doesn't name is
  unchanged**: graph topology (`ADR-043` points 3, 5), tag
  accumulation/union semantics, `participants` accumulation, approval
  gating (`route_to_project`/`detect_recurring_pattern` always creating a
  Pending Approval), and `## Summary` regenerate-from-scratch synthesis
  (`REQ-SB-67-US-01`) are all untouched — this story changes WHEN staged
  content reaches those Jobs and HOW the Thread note's filename/dates/
  links render, never their own internal logic.
- **Filename collisions must never silently overwrite an existing
  Thread's content** (Scenario 6) — mirrors `meeting_note_filename_stem`'s
  own already-shipped hash-suffix disambiguation precedent
  (`vault_writer.py` lines 844-868); the exact disambiguator is an
  implementation decision left to `/plan-tasks` (see `## Notes`), not
  decided here.
- **No fabricated wikilinks** (Scenario 11) — mirrors this codebase's
  existing `ensure_hub_note_and_link`'s own "skip Unsorted/blank
  customer" honesty precedent, extended to Person/Project resolution.
- **No new push/WebSocket/polling mechanism is invented** for the
  staging boundary itself beyond what the decoupling genuinely needs —
  mirrors this project's own "reuse first, invent last" convention
  (`REQ-SB-68-US-01`'s own identical Constraint).
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).

## Implementation Tasks

<!-- Decomposer's own table (/plan-tasks step 2, 2026-08-17) — supersedes
the analyst's starting-point table above. Task-scoped against ADR-046 and
the real current code, not the analyst's own provisional shape. Full
reasoning: ## Decomposer Pass, below. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-69-US-01-T01 | backend | `app/data_access/email_staging.py` (new) — durable, vault-local, per-email staging store: `stage_email`/`list_staged_emails`/`remove_staged_email`, one directory per email under `.second-brain/email_staging/<entry_id>/` | `app/data_access/email_staging.py` (new) | `../Tasks/REQ-SB-69-US-01-T01-durable-email-staging-primitives.md` |
| REQ-SB-69-US-01-T02 | backend | `outlook_com.list_recent_mail` gains an additive `on_item_fetched` callback; new `app/business/pipelines/email_pull.py::pull_and_stage_emails` — the sole remaining `outlook_com` importer in the email path | `app/data_access/outlook_com.py`, `app/business/pipelines/email_pull.py` (new) | `../Tasks/REQ-SB-69-US-01-T02-decoupled-pull-step.md` |
| REQ-SB-69-US-01-T03 | backend | Restructure `email_capture_pipeline.py` to read from `email_staging.list_staged_emails()` instead of calling `outlook_com` directly; drop the `outlook_com` import; `remove_staged_email`+`mark_email_processed` only on per-item success | `app/business/pipelines/email_capture_pipeline.py` | `../Tasks/REQ-SB-69-US-01-T03-pipeline-reads-from-staging.md` |
| REQ-SB-69-US-01-T04 | backend | `pull_email`/`process_staged_email` become two independently-dispatched capabilities of `email-capture-pipeline` (new `skill_tools.SKILLS` entries, new dedicated Outlook-lock-free processing lock, `capture_scheduler.py`'s composite trigger restructured into two steps, run-state tracking extended) — the mechanism making Scenarios 2/3 true by construction | `app/business/skill_tools.py`, `app/business/skill_registry.py`, `app/business/agent_schedule_registry.py`, `app/scheduling/capture_scheduler.py`, `app/business/email_classification.py` | `../Tasks/REQ-SB-69-US-01-T04-independent-pull-and-process-dispatch.md` |
| REQ-SB-69-US-01-T05 | backend | Thread filename/lookup/rename primitives in `vault_writer.py` — `thread_name` baseline frontmatter key, `<slug(thread_name)>-<date>-<hash8(conversation_id)>` filename derivation, `resolve_thread_note_path` (frontmatter-scan lookup, no persisted index), `rename_thread_note` | `app/data_access/vault_writer.py` | `../Tasks/REQ-SB-69-US-01-T05-thread-filename-lookup-rename-primitives.md` |
| REQ-SB-69-US-01-T06 | backend | Wire `thread_match_merge` to the new filename/lookup/rename mechanism (create-vs-update via `resolve_thread_note_path`, rename after every other write); fix the stale Pending-Approval-payload bug (`route_to_project`/`finalize_thread_project_routing`) | `app/business/email_classification.py` | `../Tasks/REQ-SB-69-US-01-T06-wire-thread-rename-and-fix-stale-payload.md` |
| REQ-SB-69-US-01-T07 | backend | Human-readable dates — additive `last_message_at_display` frontmatter field, human-readable `## Transcript` entry timestamps at write time; `last_message_at` stays byte-for-byte unchanged | `app/data_access/vault_writer.py`, `app/business/email_classification.py` | `../Tasks/REQ-SB-69-US-01-T07-human-readable-thread-dates.md` |
| REQ-SB-69-US-01-T08 | backend | New, deterministically-regenerated `## Related` body section — real Customer/Person/Project `[[wikilink]]`s via `replace_body_section`, honest absence for Unsorted/unresolved entities | `app/data_access/vault_writer.py`, `app/business/email_classification.py` | `../Tasks/REQ-SB-69-US-01-T08-thread-related-wikilinks.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass — all 11 locked ACs (`AC-01`
      through `AC-11`) verified live, per each owning task's own
      `## Implementation Log` (`AC-01`/`02`/`03` → `T04`; `AC-04` → `T03`;
      `AC-05`/`06`/`07` → `T06`; `AC-08`/`09` → `T07`; `AC-10`/`11` → `T08`)
- [x] Every Implementation Task above is complete — `T01`-`T08`, all 8, `status: Done`
- [x] All Constraints respected — confirmed per-task; the one disclosed,
      out-of-scope residual gap (`agent_schedules_router.py::run_now`
      hardcoding the shared Outlook lock for every capability id,
      including `process_staged_email`) does not violate the story's own
      locked Constraint text (which binds the hourly/app-start scheduled
      tick specifically) — see `T04`'s own `## Implementation Log`
- [x] Automated tests added/updated and passing (once test tooling exists — manual/live-data-trace verification mode until then, per this project's own standing convention)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Giving `Pull` its own addressable Agent-tier identity** (own Working
  Mode, own Agents Map node, own chat surface) — a real, disclosed open
  question (see `## Notes`), but this story's own minimum acceptance bar
  is about decoupling Pull's *timing* from the rest of the graph, not
  necessarily its *addressability*. Left to the architect to decide
  whether the staging boundary alone satisfies the requirement or a new
  Agent identity is also warranted.
- **`REQ-SB-53`'s original Puller/Tagger/Linker/Storer 4-agent split** —
  explicitly not revived (see `## Dependencies`); `REQ-SB-53-US-01` stays
  `Parked`.
- **Reconciling multiple `ConversationID`s into one real Conversation** —
  `REQ-SB-60`'s own separate, deferred future scope, untouched here.
- **A Scheduling-view row for the new, decoupled Pull step** — a real,
  disclosed open question (see `## Notes`/`## Affected Screens`), not
  designed or built here; the existing `email-capture-pipeline` row
  (`REQ-SB-68-US-01`, `Done`) is left as-is unless the architect decides
  otherwise.
- **Backfilling already-captured Thread notes onto the new
  filename/date/wikilink shape** — this story covers real, live-captured
  Threads going forward, mirroring `REQ-SB-67-US-01`'s own explicit
  precedent for treating "going-forward capture" and "backfill of
  already-existing notes" as separable concerns; a backfill pass (if
  wanted) is a follow-up, not assumed built here.
- **Real-time push/WebSocket-based live staging-queue depth display** —
  no new observability UI is designed here beyond what `## Affected
  Screens` already scopes as open.
- **Any change to `Classify`/`Thread-Match/Merge`/`Route-to-Project`'s own
  internal decision logic** (customer/kind classification, tag
  accumulation, project-routing guess, recurring-pattern detection) —
  only Pull's timing and the Thread note's filename/dates/links change;
  every other already-verified behavior is preserved unmodified.

## Notes

**Why one story, not two (Scoping decision — full reasoning):** the
PRD's own `<!-- Raised -->` comment states the content-quality asks are
folded in *"since they touch the same Thread-writing code path this
restructuring already has to touch,"* and frames the two halves as
sequentially motivated — content quality "is only worth doing once the
first stops the pipeline from randomly wedging mid-work." Both halves
touch the same real files (`email_capture_pipeline.py`,
`email_classification.py::thread_match_merge`, `vault_writer.py`'s
Thread primitives) and the same real ADRs (`ADR-042`, `ADR-043`). This
mirrors `REQ-SB-68-US-01`'s own directly analogous precedent — "Two
tightly-coupled fixes to the same underlying gap," kept as one story, not
split by facet — rather than `REQ-SB-53`'s own precedent (which split by
CAPTURE TYPE — Email/Meeting/To-Do each getting a materially different
code path — not applicable here, since REQ-SB-69 has only one capture
type and one code path). Splitting into two stories here would force an
artificial `depends_on` edge between two stories touching overlapping
code/files, for no real isolation benefit — a worse partition than one
story with an internal task order (`T01/T02` pull-decoupling, then
`T03`-`T05` content-quality, since the PRD's own text says the latter is
only worth doing once the former lands). Sizing: 5 starting tasks,
comparable to `REQ-SB-55-US-01`'s own original 8-task pipeline build and
`REQ-SB-68-US-01`'s own 4-task coupled-fix shape — not judged oversized
(trigger 5 does not fire).

**Real, disclosed architectural consequences flagged for the architect at
`/plan-tasks` (not resolved by this pass — mechanism-level decisions are
the architect's role, not the analyst's, per `Implementation/
Pipeline.md`'s own role boundaries):**

1. **`ADR-043` point 2 ("Fetch is a pre-graph, per-tick batch step... no
   persisted queue/staging") is the Accepted decision this requirement
   asks to reconsider.** This story's own Scenarios 1-4 specify the
   OUTCOME (no downstream `outlook_com` calls; a stall on either side
   doesn't block the other side) without dictating the staging store's
   own format/location/mechanism — genuinely left open per the
   operator's own "open implementation questions... resolved directly by
   the pipeline" framing, since a human confirmation is not available
   tonight. Whether this reopening needs a new/amended ADR is the
   architect's call.
2. **`ADR-042` point 5 ("path resolved deterministically from
   `conversation_id` alone... no separate lookup index") is broken by
   this requirement's own filename ask.** A Thread's filename can no
   longer be computed from `conversation_id` alone once it depends on the
   mutable `last_message_at` + subject — `thread_match_merge`'s existing
   `thread_note_exists(conversation_id)`/`thread_note_path(conversation_id)`
   calls need a real replacement mechanism (a lookup index, a
   frontmatter-scan mirroring `list_thread_notes()`'s own already-shipped
   pattern used by `REQ-SB-56`'s fallback linker, or something else).
   Scenario 7 specifies the OUTCOME (filename tracks the new last-message
   date on update, content preserved) without dictating this mechanism.
3. **`ADR-043` point 7's own explicit decision NOT to call
   `link_note_to_customer_hub` from `Thread-Match/Merge`** ("superseded
   by the OKF concept file's own `sources:` provenance field... Thread-
   Match/Merge does not itself write `sources:`") **is directly reopened
   by this requirement's wikilink ask, for Thread notes specifically.**
   Scenarios 10-11 specify the OUTCOME (at least one real, honest
   wikilink; never a fabricated one) without dictating whether this
   reuses `link_note_to_customer_hub`/`link_email_to_person` as-is, a new
   Thread-specific sibling primitive, or a body-section (`## Related`)
   shape instead of an inline line — a real design-latitude question
   mirroring `REQ-SB-64-US-01`'s own identical "mechanical shape left to
   `/plan-tasks`" precedent.
4. **Whether `Pull` should also get its own Agent-tier identity** (as
   `REQ-SB-53-US-01`'s now-`Parked` model proposed, before `ADR-043`
   superseded it with a single-Agent-identity Pipeline) is a real,
   disclosed open question this story does not resolve — see
   `## Non-Goals`. The operator's own words ("Have one Agent to Hand the
   pull of All Emails Separately") could read either way (a genuinely new
   addressable Agent, or simply "the pull logic, handled as one
   coherent, separate step" without necessarily a new Agents-Map-visible
   identity) — left to the architect, who is better positioned to weigh
   it against `ADR-043` point 6's already-settled "Jobs stay
   non-addressable" default.

**Why none of the above triggers MUST-FLAG for this analyst pass (why
`gate: clear`, not `flagged`):** every genuinely open question above is
explicitly a MECHANISM question the Pipeline's own role boundaries assign
to the architect at `/plan-tasks` step 1, not a scoping/interpretation
ambiguity that changes what Gherkin to write here — this pass wrote every
Scenario at the OBSERVABLE-OUTCOME level (mirroring `REQ-SB-68-US-01`'s
own identical "specify the outcome, leave the dispatch mechanism to the
architect" precedent), so no guess among equally-valid readings was
needed to produce correct, buildable Acceptance Criteria (trigger 8 does
not fire). The `last_message_at` machine-parseable-consumer question was
resolved directly, not guessed: `meeting_classification.py::
_date_proximity_gap_days` was located and read directly (line-cited
above), confirming exactly one real, live consumer exists and locking a
Constraint around it, rather than leaving "which dates stay
machine-parseable" as an open flag — the PRD's own text explicitly says
this SPLIT (not the outcome) is "an implementation decision, not a
product one," so delegating the split mechanism to `/plan-tasks` is
following the PRD's own instruction, not deferring a genuinely unclear
product question. No material assumption was made to fill a scoping gap
(trigger 1); `REQ-SB-69` carries no `<!-- Draft -->` marker in the PRD —
it is finalized text (trigger 2 n/a); no ADR was created or changed by
this analyst pass — that is explicitly the architect's own role at
`/plan-tasks` (trigger 3 n/a for this role); no `ESCALATIONS.md` entry
was written — this is ordinary forward `/spec` work, not a backward/
out-of-scope event (trigger 4 n/a); this story is not judged oversized,
per the sizing comparison above (trigger 5 n/a — `/plan-tasks` may still
find task-level splitting is warranted, that is its own call); no
contradictory PRD inputs exist — the PRD's own text is internally
consistent, it simply delegates several mechanism-level decisions
downstream on purpose (trigger 7 n/a).

**Prototype parity:** N/A — no `html-prototype/` screen is touched by
this story (backend + vault-content only). See `## Affected Screens` for
the one real, disclosed open question (a possible Scheduling-view row for
the new decoupled Pull step) left to the architect, not designed here.

**Resolved directly, not left for a human tonight (per the operator's own
full-autonomy grant):** the single-vs-two-story split decision above, and
the choice to write every Scenario at the observable-outcome level so
none of the four disclosed mechanism-level questions blocks a `gate:
clear` advance — both decided with grounded, code/precedent-cited
reasoning (this section and `## Context`), not by guessing among
equally-plausible alternatives, mirroring `REQ-SB-53-US-01`'s own
"Resolved directly, not re-asked" precedent for Linker's agent Type.

gate: clear 2026-08-17 — no MUST-FLAG trigger fired (see the itemized
trigger-by-trigger reasoning above); every genuinely open mechanism-level
question is disclosed and routed to the architect at `/plan-tasks`, per
this project's own established role boundaries, not silently guessed or
left unaddressed.

---

## Architect Pass (`/plan-tasks` step 1) — 2026-08-17

**Architecture scope:** §Decoupled Email Pull + Human-Readable,
Graph-Connected Thread Notes (`architecture.md`), §Email Capture &
Threading Pipeline — First Concrete Pipeline (`architecture.md`,
unchanged parts still bound the compiled-graph shape) — the coder is
bounded to these two `architecture.md` sections plus `ADR-046` in full.

**ADR created:** `ADR-046` (new), superseding `ADR-043` points 2 and 7
and `ADR-042` point 5 only — every other point of `ADR-041`, `ADR-042`,
`ADR-043`, `ADR-045` stays exactly as already `Accepted`, unedited (specs
are append-only; nothing in `ADR.md` was rewritten, only appended to).
This trips **MUST-FLAG trigger 3** (ADR created) — `gate: flagged`,
`gate_reason: "trigger-3 (ADR-046 created)"`, a `REVIEW-QUEUE.md` pointer
is filed below. Per `Implementation/Pipeline.md`, this does **not** halt
the pipeline — the decomposer runs next regardless, so the human reviews
`ADR-046` and the resulting locked ACs/tasks together in one pass.

**The four mechanism-level questions this story's own `## Notes`
flagged, resolved concretely in `ADR-046` (full reasoning, Alternatives
Considered, and Consequences in the ADR itself — summarized here):**

1. **Staging store format/location (`ADR-043` point 2 reopened):** a new
   `app/data_access/email_staging.py` module, one directory per staged
   email under `.second-brain/email_staging/<entry_id>/` (metadata JSON,
   attachment bytes on disk — mirrors `ADR-034`'s blob-storage
   precedent, not a JSON-encoded-string workaround, which is for small
   structured values, not multi-megabyte binaries). `outlook_com.
   list_recent_mail` gains an additive `on_item_fetched` callback so
   staging is genuinely live-updating/incremental/resumable, per the
   operator's own concrete steer — a stall mid-loop still leaves every
   already-fetched item durably staged, never buffered-then-lost. Pull
   and downstream processing become two independently-dispatched
   capabilities of the SAME `email-capture-pipeline` Agent (`pull_email`,
   still under the shared Outlook-COM lock; `process_staged_email`,
   deliberately never under that lock) — this is what makes "a stalled
   Pull can't block already-staged mail" and "stalled processing can't
   block the next Pull" true by construction, not convention.
2. **Thread filename → path lookup (`ADR-042` point 5 reopened):**
   filename becomes `<slug(thread_name)>-<date>-<hash8(conversation_id)>.md`
   (mirrors `meeting_note_filename_stem`'s already-shipped shape exactly,
   per this story's own Context grounding). `thread_note_path`'s
   "deterministic from `conversation_id` alone" lookup is retired and
   replaced by a frontmatter-scan lookup (`resolve_thread_note_path`,
   built on the already-shipped `list_thread_notes()`) — no new
   persisted index file, deliberately (would be a new class of drift
   risk `ADR-042` already rejected once for an adjacent need). A real,
   previously-latent bug was found and fixed alongside this: `route_to_
   project`'s Pending-Approval payload captured a `thread_path` STRING
   that can now go stale between proposal and approval — the payload
   gains `conversation_id`, and `finalize_thread_project_routing`
   re-resolves the CURRENT path at Approve time.
3. **Wikilink mechanism (`ADR-043` point 7 reopened):** a NEW,
   deterministically-regenerated `## Related` body section (via the
   already-shipped `replace_body_section`) — NOT Email's own existing
   `insert_body_line_if_missing`-based inline primitives. Direct reading
   found those primitives would silently conflict with `replace_body_
   opening_line`'s own full-region ownership of the same pre-first-header
   position (a genuine, previously-undisclosed bug risk, not a style
   preference) — this is why the ADR decides definitively rather than
   leaving the shape open. Regenerated every call from real,
   currently-resolvable data only (Customer hub stem, existing Person
   notes for participants, Project stem once routed) — an honest
   absence, never a fabricated link, for Unsorted/unresolved entities.
4. **Pull's own tier/addressability:** resolved as NO new Agent-tier
   identity. The operator's own words are satisfied literally by Pull
   becoming a second, independently-triggerable CAPABILITY of the
   existing `email-capture-pipeline` Agent (no new Map node, chat
   surface, or Working Mode) — extends `ADR-037`/`ADR-045`'s own
   "multiple independently-dispatched capabilities per Agent-tier
   identity" shape one capability further, rather than reopening `ADR-041`
   point 1's Job-tier default or reviving `REQ-SB-53-US-01`'s now-`Parked`
   4-Agent model.

A fifth, real correctness consequence was found and resolved by direct
reading, not anticipated by the story's own `## Context`: `route_to_
project`'s payload's stale-path risk (point 2 above) — disclosed as a
Consequence in `ADR-046`, including the migration-window caveat for any
already-pending approval created before this ships.

**Human-readable dates (Constraints — locked outcome, mechanism
resolved):** a new, additive `last_message_at_display` frontmatter
sibling field; `last_message_at` itself stays byte-for-byte unchanged
(still ISO-8601), so `meeting_classification.py::_date_proximity_gap_days`'s
real, already-shipped parsing keeps working exactly as today (Scenario
9). `## Transcript` entries format their own timestamp human-readably at
write time — confirmed by direct repo-wide search that nothing
programmatically parses an individual Transcript line.

**Escalations:** none. No decision here contradicts an `Accepted` ADR,
the PRD, or a `MEMORY.md` constraint — every reopened ADR point is
superseded via `ADR-046`, never rewritten in place (specs stay
append-only), and no `out-of-scope`/`adr-deviation` finding was made.

**Handoff:** the decomposer runs next, bounded to the architecture scope
named above; it locks ACs/AC-IDs and writes tasks against `ADR-046` and
the two named `architecture.md` sections.

---

## Decomposer Pass (`/plan-tasks` step 2) — 2026-08-17

**ACs locked:** all 11 Scenarios tightened and assigned `AC-01`–`AC-11`,
each locked by default (no non-locked exception used — every ACS
outcome is verifiable, see AC → task/test mapping below). Tightening was
light-touch: the analyst's own Gherkin was already grounded and precise;
edits mostly named the now-concrete architecture terms `ADR-046` settled
(`pull_email`/`process_staged_email`, `thread_name`,
`last_message_at_display`, `## Related`) so each Scenario's Then-clause
maps onto a real, buildable, checkable artefact rather than a
description.

**Task breakdown (8 tasks, two independent roots converging into two
mostly-independent chains — mirrors `REQ-SB-55-US-01`'s own 8-task
diamond-shaped precedent, not judged oversized against that comparison):**

- **Pull/staging half (`T01`→`T04`, mechanism 1 — `ADR-046` Decisions
  1-5):** `T01` (staging primitives) is the root; `T02` (Pull step) and
  `T03` (pipeline reads from staging) both depend only on `T01` and are
  mutually independent (a real diamond — neither composes the other);
  `T04` (independent-dispatch capabilities + lock separation + scheduler
  restructuring) converges both, since it is the mechanism that makes
  Scenarios 2/3 true by construction and needs both `pull_and_stage_emails`
  and the staging-reading pipeline to dispatch to.
- **Thread content-quality half (`T05`→`T08`, mechanisms 2/3 — `ADR-046`
  Decisions 6-10):** `T05` (filename/lookup/rename primitives) is a
  second, independent root — it does not depend on the pull/staging half
  at all, per the operator's own explicit steer that filename/lookup work
  can proceed in parallel with staging when it doesn't depend on it.
  `T06` (wires `thread_match_merge` to the new mechanism, plus the
  stale-payload fix) depends on `T05`. `T07` (dates) and `T08`
  (wikilinks) both touch `thread_match_merge` again and are sequenced
  behind `T06` (and, for `T08`, behind `T07` too) purely to avoid
  same-function conflicting edits across tasks — not because either
  scenario semantically requires the others' output.
- **Why not fewer tasks:** each of the three real mechanism changes named
  in the operator's own sizing note (Fetch/staging decoupling, filename/
  lookup rename, wikilinks) genuinely spans more than one independently-
  verifiable unit of work — e.g. mechanism 1 alone has three separately
  checkable properties (staging happens at all — `T01`/`T02`; downstream
  never touches Outlook — `T03`; a stalled step never blocks its sibling
  — `T04`, `ADR-046`'s own most architecturally load-bearing decision).
  Splitting these keeps each task's own `## Tests` block honestly
  scoped to what that task's own diff actually proves, rather than one
  task claiming to prove a property (lock separation) its own diff
  doesn't yet build.
- **Why not more tasks:** the stale Pending-Approval-payload fix (a real,
  disclosed `ADR-046` Consequence, Decision 8) is folded into `T06`
  rather than split out — it is causally inseparable from `T06`'s own
  rename mechanism (the bug is only reachable once renaming is real) and
  is small (two call sites); splitting it would be a busywork split, not
  a genuinely separately-verifiable unit. It carries no AC-tagged step of
  its own (no Scenario names it explicitly) but is verified as a plain
  regression step inside `T06`'s own `## Tests`.

**AC → task mapping (every locked AC has at least one tagged step; no
locked AC is unverifiable):**

| AC | Task | Verified via |
|---|---|---|
| AC-01 | T04 | Full Scenario-1 integration check (real pull stages content; grep-confirmed no downstream `outlook_com` import) — placed in `T04` rather than `T02`/`T03` individually since `T04` is the first task that `depends_on` both, guaranteeing both halves are real by the time this is checked |
| AC-02 | T04 | Induced-stall concurrency check: `pull_email` stalled, `process_staged_email` still completes against pre-staged content |
| AC-03 | T04 | Induced-stall concurrency check: `process_staged_email` stalled, `pull_email` still completes |
| AC-04 | T03 | Induced per-item failure against `run_email_capture_pipeline()`'s new staging-reading loop; failed item stays staged+unmarked, others succeed |
| AC-05 | T06 | Real Thread creation; filename shape check |
| AC-06 | T06 | Two same-date/name conversations; distinct files, no overwrite |
| AC-07 | T06 | Rename on a later message; content-preservation diff |
| AC-08 | T07 | `last_message_at_display` human-readable; `## Transcript` entries human-readable |
| AC-09 | T07 | `_date_proximity_gap_days` regression check against real Threads/Meetings |
| AC-10 | T08 | Real wikilink in `## Related`; Obsidian graph-view edge |
| AC-11 | T08 | Unsorted/unresolved case; honest empty `## Related`, no fabricated link |

**Why `gate` stays `flagged`, `gate_reason` unchanged:** no NEW MUST-FLAG
trigger fired during this decomposer pass itself (every AC is locked and
verifiable, every locked AC has a tagged step, `depends_on` is acyclic —
confirmed by direct construction above, a diamond plus two short chains,
no cycle). The existing `trigger-3 (ADR-046 created)` flag from the
architect's own pass this run is left exactly as set, per
`Implementation/Pipeline.md`'s own instruction ("If the architect flagged
the story this run for an ADR change, leave it `gate: flagged` — the
human reviews the ADR and your tasks together") — `REVIEW-QUEUE.md`
already carries the one pointer this run needs (filed by the architect),
which already anticipates this decomposer pass's own task breakdown
("either let the decomposer's already-run task breakdown stand..."); no
second, duplicate `REVIEW-QUEUE.md` entry is added.

**Status:** `Draft → Ready`. All three gate conditions for advancing
status are met: (a) every AC is locked (11/11); (b) every locked AC has
at least one tagged verification step (table above); (c) `depends_on` is
acyclic (`T01`/`T05` roots; `T02`/`T03` ← `T01`; `T04` ← `T02`,`T03`;
`T06` ← `T05`; `T07` ← `T06`; `T08` ← `T06`,`T07` — a DAG, confirmed by
inspection, no back-edges). All 8 tasks are written at `status: Ready`
in lockstep with the story, per `Implementation/Pipeline.md`'s own "task
status moves in lockstep with the story" rule.

**Handoff:** eligible for `/plan-sprints` once the human clears the
`ADR-046` review-queue flag above (the flag does not block
`/plan-sprints` from being able to read this story as `Ready` and
ungrouped — the pipeline is exception-based and gates are for human
attention, not a hard block on downstream commands per
`Implementation/Pipeline.md`'s own "gates are exception-based" hard
rule 10 — but the human should still review `ADR-046` before this
ships).
