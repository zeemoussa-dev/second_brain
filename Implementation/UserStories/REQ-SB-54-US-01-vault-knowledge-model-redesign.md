---
id: REQ-SB-54-US-01
title: Vault knowledge model redesign — Threads/Meetings/Manual Captures evidence layer, Project/Customer synthesis layer (Background/History/Glimpse/Captures)
requirement_ids: [REQ-SB-54]
requirement_section: "REQ-SB-54: Vault Knowledge Model Redesign — Threads, Linked Meetings, Living Project & Customer Documents"
phase: P1
status: Done
gate: clear
gate_reason: "ADR-042 reviewed and approved by the operator, 2026-08-16 (no changes requested). All ACs locked, tasks T01-T06 wired, status Ready. Eligible for /plan-sprints. All 6 tasks (T01-T06) shipped Done, all 5 locked ACs verified live — see MEMORY.md and each task's own Implementation Log. T04/T05 each carry one open, non-blocking REVIEW-QUEUE.md spot-check item (scope-internal judgement calls); story status: Done regardless per Pipeline.md (gate flags are independent of status)."
sprint: "SPRINT-048"
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-54-US-01 — Vault knowledge model redesign — Threads/Meetings/Manual Captures evidence layer, Project/Customer synthesis layer (Background/History/Glimpse/Captures)

## Story

**As a** Second Brain user
**I want** the vault to separate raw, append-only evidence (Threads, Meetings,
manual Captures) from living, regenerated synthesis documents (Project and
Customer notes, each with structured frontmatter plus a Background/History/
Glimpse narrative), instead of one email producing one disconnected note
**So that** I can always find the current status of anything in one place —
the root pain this whole batch traces back to, in the operator's own words:
"The pain is I can't find the current status of anything."

## Context

- **UPDATED 2026-08-16 (same day this story was drafted): Customer/Project
  are now a small OKF-conformant DIRECTORY** (`index.md`/`<slug>.md`/
  `log.md`/`captures.md` — Google Cloud's Open Knowledge Format v0.2),
  **not sections inside one file**, per direct operator decision — see
  PRD `REQ-SB-54` points 4/5/7/8/11 for the authoritative current shape;
  anywhere below this note still describes Background/History/Glimpse/
  Captures as "sections in one note," read it as "the concept file's own
  body / `log.md` / `captures.md`" per that mapping. Scenario 3 has been
  updated to match; the Implementation Tasks table below has not — it's
  explicitly non-authoritative pending the decomposer's own pass at
  `/plan-tasks` anyway.
- PRD: `Documentation/PRD.md` → *REQ-SB-54: Vault Knowledge Model Redesign —
  Threads, Linked Meetings, Living Project & Customer Documents*. This is the
  foundational data-model requirement every other requirement in this batch
  (`REQ-SB-55` through `REQ-SB-59`) builds on — it defines the shape; it does
  NOT itself build the capture pipelines, synthesizer agents, Glimpse-first
  Expert behavior, or the historical backfill that populate/consume that
  shape (all separate, dependent stories — see Non-Goals/Dependencies).
- **Raised 2026-08-16, over an extended discussion, not a single instruction**
  — the PRD's own comment block reconstructs the converged design rather than
  a single ask; the operator was explicitly treated as a thinking partner.
  Every decision below traces back to the root pain quoted in `## Story`.
- **Evidence layer — resolved, not open:**
  1. **Threads replace Emails.** Today (`app/business/email_classification.py`)
     every email becomes its own note; Outlook's real `ConversationID` is
     already captured (`app/data_access/outlook_com.py::list_recent_mail`,
     confirmed directly by reading the real code — `"conversation_id":
     getattr(item, "ConversationID", None) or ""`) but is only used for a
     loose `vault_writer.find_related_note_stems()` lookup, never to merge
     notes. Under this requirement, the FIRST email in a conversation
     creates one Thread note; every later email in that SAME conversation
     updates that same note (running transcript, dated entries) instead of
     creating a new file. Operator, confirming this replaces rather than
     adds to Emails: "Okay thread and Meetings" (in response to being asked
     whether Emails stays a separate parallel section — it does not).
  2. **Meetings stay their own note kind**, not folded into Threads — a
     meeting has its own shape (attendees, agenda, action items) — but gains
     a link back to whichever Thread it relates to. **This story only
     establishes that a Meeting note carries room for that relationship in
     its schema** — actually populating the link (matching a real meeting to
     a real Thread) is `REQ-SB-56`'s own, separate scope.
  3. **Manual Captures — a third evidence source, not a protected
     human-only zone.** Operator: "This is not only Agent input, sometimes I
     need to add stuff in Obsidian... The Source of info we have now is
     Emails, WebSearch, Files and Meetings, but sometimes I get info that is
     not in any of those — a word or a mouth, a quick update in an elevator,
     a quick guide from a manager." Resolved: the operator writes these
     directly into the relevant Project/Customer note, in the moment, into
     an append-only "Captures" section — same tier as a Thread or Meeting,
     feeding the exact same synthesis, not a personal-commentary carve-out.
     Routing is free for this source (no guess-and-approve needed) since the
     operator already knows what it's about when they write it.
- **Synthesis layer — resolved, except point 6 below:**
  4. **Project (new note kind) and Customer (restructured, not new)** each
     carry structured frontmatter (stage, open items, key facts,
     last-updated) PLUS a narrative body — operator: "The KB is for me and
     my Agents to put data and pull data" — frontmatter is what an agent
     pulls cheaply mid-conversation without re-parsing prose; the narrative
     is what the operator skims to answer "what happened." **Confirmed
     against the real current Customer note shape** — `app/business/
     customer_hub_linking.py`'s `ensure_customer_hub_note`/
     `create_customer_hub_note_baseline` produce a minimal baseline
     (`Type`, `Affiliate of`) with NO narrative body mechanism today —
     this requirement genuinely restructures it, matching the operator's
     own complaint (quoted directly in `REQ-SB-57`): "no one update this
     file."
  5. **Customer's narrative splits into three sections, each with its own
     update rule:**
     - **Glimpse** — fully regenerated on every relevant change. One line
       per active Project. Never appended to, never hand-edited by an agent
       partially — thrown away and rebuilt from current state.
     - **History** — append-only, grows forever. A line is added only when
       something genuinely concludes (a Project closes, a renewal lands) —
       NOT on every routine update, or it becomes a second activity feed.
       **The exact bar for "worth a History line" is left to the architect/
       decomposer to propose and the operator to confirm — this story does
       not lock a specific bar; see `REQ-SB-57-US-01`, the story that
       actually writes History lines, for where this gets resolved.**
     - **Background** — the slowest-moving section; changes only when a new
       DURABLE fact is detected (e.g. "they're now a Core42 customer"), not
       on routine activity. Mirrors `agent_memory.json`'s existing shape
       (discrete, timestamped facts per agent), scoped to the customer,
       folded into prose. A new-fact detection routes through Pending
       Approvals (see `REQ-SB-57`), same reasoning as a new-Project
       proposal.
     - **Captures** — append-only, operator-written (point 3 above), read by
       the synthesizer as input to Glimpse/History regeneration but NEVER
       itself rewritten by an agent.
  7. **Exactly one owner writes Glimpse/History per note; nothing else ever
     touches those sections directly** — prevents two agents racing to
     rewrite the same file. **This story only establishes that this rule
     exists at the data-model level** — the actual enforcement mechanism
     (a Thread/Meeting/Capture update TRIGGERS resynthesis rather than
     writing the section itself) is `REQ-SB-57`'s own scope.
  8. **Regenerate, don't patch**, for anything meant to reflect current
     state (a Thread's own top summary, any Glimpse) — read the full current
     evidence set and rewrite fresh, rather than incrementally editing old
     text, which drifts and duplicates. This also sidesteps an
     already-documented fragility: `vault_writer.insert_body_line_if_missing`
     computes a fixed byte offset from the frontmatter's closing `---`,
     unsafe for a note touched many times over its life (`MEMORY.md`,
     `BUG-003`/`ESC-003`, `Open`) — a note meant to be rewritten repeatedly
     should read-reconstruct-overwrite in full, never lean on that
     incremental primitive at all.
- **RESOLVED 2026-08-16 — operator, direct confirmation:** "Yes, Project
  gets the same directory shape as Customer."
  6. Project gets the identical OKF-conformant directory shape as
     Customer — `index.md`/`<project-slug>.md`/`log.md`/`captures.md` —
     no longer a working default, a confirmed decision. See `## Notes`
     and `ESCALATIONS.md` → `ESC-037`, `Resolved`.
- **Prerequisite risk — VERIFIED live 2026-08-16, RESOLVED, no longer
  blocking:**
  9. Outlook's `ConversationID` is the proposed Thread key. Verified
     read-only against the real, configured Outlook installation: scanned
     300 real inbox items → 155 distinct `ConversationID`s, 41 with 2+
     messages (real threads). Every multi-message thread sampled held
     together correctly (e.g. a real 3-message "G42/Data Lake RFP
     Discussion" thread, spanning 2026-08-07 to 2026-08-14, all 3 messages
     under one `ConversationID`). Two cases initially looked like
     collisions (same `ConversationID`, differing `ConversationTopic`) but
     on inspection were the SAME conversation with its subject line edited
     partway through ("Ewec Discussion (Compass - AI) online" →
     "...Compass - Cloud - AI) online"; "Data/Integration Workshop -
     [Core42]" → "Placeholder: Data/Integration Workshop - [Core42]") —
     `ConversationID` correctly kept these threaded together where a
     subject-string join would have split them. **No genuine collision
     found** — unlike `EntryID`/`GlobalAppointmentID` before it
     (`ESC-002`/`ESC-012`), this identifier held up under direct testing
     for FALSE MERGING (one ID wrongly spanning unrelated messages).
  10. **`ConversationID` under-merges — RESOLVED 2026-08-16 by scope
      split, not by inventing a merge heuristic.** Operator flagged the
      opposite failure mode directly: "The ConversationID is not the only
      link, sometimes different emails with different ConversationID are
      linked to the same thread." A real conversation CAN legitimately
      span multiple `ConversationID`s that Outlook itself never merges.
      Resolved: "I guess we keep threads as is and then we will need to
      have an entity called Conversation where thread is the raw data,
      then we will handle the data in the KB later." **Thread stays
      EXACTLY as originally specced** — one note per `ConversationID`,
      no cross-ID merge logic in this story. The merge problem moves
      entirely to `REQ-SB-60` (`Conversation`, a new note kind above
      Thread), a placeholder requirement NOT yet spec'd — deliberately
      deferred until `REQ-SB-55` has real capture history to design the
      merge logic against, rather than guessed abstractly now. This story
      and `REQ-SB-55`'s `Thread-Match/Merge` Job are fully un-blocked by
      this resolution.
- **No `html-prototype/` screen renders note body/narrative content at
  all.** Confirmed by direct inspection of `note-detail.html` — it shows
  frontmatter as a `kv-list`, tags as badges, and forward-link/backlink
  rows only; it never renders a note's markdown body. This is consistent
  with the project's own "Obsidian remains the authoring/reading surface
  for note content" convention (`note-detail.html`'s own header comment).
  A Customer/Project note's new Background/History/Glimpse/Captures
  narrative sections are therefore **not a screen-design concern** — no
  `net-new-design-needed` trigger fires here; see `## Notes`.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: A multi-message Outlook conversation collapses into exactly one Thread note

<!-- TIGHTENED 2026-08-16 (decomposer, /plan-tasks step 2): reworded to be
buildable/verifiable against THIS story's own data-model primitives alone
(vault_writer.thread_note_path/create_thread_note_baseline/
replace_body_section/append_person_note_update_line) — the actual
"a message is captured" trigger is REQ-SB-55's still-unbuilt pipeline
(this story's own Non-Goals), so the locked scenario below is framed
around the deterministic-path + regenerate-vs-append primitives that
pipeline will call, not around a live capture run that doesn't exist yet. -->

```gherkin
Given the Thread note primitives (vault_writer.thread_note_path,
    create_thread_note_baseline) resolve a single, deterministic path
    from an Outlook conversation_id alone
When a Thread note is created for a conversation_id for the first time
    (the first message in that conversation)
Then exactly one Thread note is created at that deterministic path, with
    an empty ## Summary section and an empty ## Transcript section
When the SAME conversation_id is processed again (a later message in the
    same conversation)
Then no new note is created — thread_note_path(conversation_id) still
    resolves to the SAME single file — and instead: ## Transcript gains a
    new appended dated entry (growing, never replaced), and ## Summary is
    regenerated in full via replace_body_section (never incrementally
    patched), leaving ## Transcript and the frontmatter block untouched
```
<!-- AC-ID: REQ-SB-54-US-01-AC-01 -->

### Scenario 2: Manual Captures are appended directly, never rewritten by an agent

<!-- TIGHTENED 2026-08-16 (decomposer): re-worded from "note's Captures
section" to "directory's own captures.md file" to match the 2026-08-16
directory-shape update (see story ## Context) — Captures is now a
physically separate file, not a section inside one note. -->

```gherkin
Given a Customer or Project directory's own captures.md file already has
    existing content
When a new entry is appended directly to captures.md (simulating the
    operator writing directly in Obsidian, outside any agent-triggered
    write)
Then the entry is preserved verbatim, appended after the existing
    content
When an agent-triggered regeneration subsequently runs against that same
    directory's <slug>.md concept file (its ## Glimpse and/or
    ## Background section, via replace_body_section)
Then captures.md's content, including the newly appended entry, is left
    completely untouched — no code path used for <slug>.md regeneration
    ever opens or writes to captures.md
```
<!-- AC-ID: REQ-SB-54-US-01-AC-02 -->

### Scenario 3: A Customer directory carries the full OKF-conformant shape, with the update-ownership boundary structurally enforced

<!-- UPDATED 2026-08-16: Customer/Project are now a small OKF-conformant
DIRECTORY (index.md/<slug>.md/log.md/captures.md), not sections inside
one file — operator chose to adopt OKF's own reserved-filename convention
literally. See PRD REQ-SB-54 point 4. -->

```gherkin
Given a real Customer directory has been created under this data model
When its contents are inspected
Then it contains index.md (OKF directory listing, auto-generated),
    <customer-slug>.md (the OKF concept file — frontmatter with at
    minimum type: customer, plus title/description/tags/status/
    stale_after/generated/verified/sources, and a body of exactly two
    ##-headed sections, ## Glimpse and ## Background), log.md (OKF
    History, date-headed, append-only), and captures.md (append-only,
    operator-written)
When a manual edit is placed directly into captures.md
  And an agent-triggered Glimpse regeneration (via replace_body_section
    against <customer-slug>.md's ## Glimpse section) subsequently runs
Then the manual captures.md edit survives completely untouched — the
    regeneration call only ever opens/rewrites <customer-slug>.md, and
    has no code path capable of writing to captures.md or any other file
    in the directory
```
<!-- AC-ID: REQ-SB-54-US-01-AC-03 -->

### Scenario 4: Glimpse-type sections are regenerated in full, never incrementally patched

```gherkin
Given a note's ## Glimpse section (or any other ##-headed section)
    already has content from a prior replace_body_section call
When replace_body_section(path, "## Glimpse", new_content) is called
    again with different content
Then the entire region strictly between the ## Glimpse header and the
    next ##-level header (or end of file) is replaced wholesale with
    new_content
  And every byte outside that bounded region (frontmatter, other
    sections, the header lines themselves) is left byte-for-byte
    unchanged
  And no part of the new content is produced by inserting or appending at
    a computed byte offset — the function locates headers by their
    literal text, not a cached position, so it behaves identically no
    matter how many times the file has already been regenerated
```
<!-- AC-ID: REQ-SB-54-US-01-AC-04 -->

### Scenario 5: A Project directory carries the same OKF-conformant shape as Customer, confirmed

```gherkin
Given a real Project has been created under this data model, nested at
    Work/Customers/<customer-slug>/projects/<project-slug>/
When its directory is inspected
Then it contains index.md, <project-slug>.md, log.md, and captures.md —
    identical in shape and update-ownership rules to a Customer directory
    (operator-confirmed 2026-08-16, not a working default — see Notes)
```
<!-- AC-ID: REQ-SB-54-US-01-AC-05 -->

## Affected Screens

None — backend/data-model only. `html-prototype/note-detail.html` (the only
screen that renders note content in this app) shows frontmatter/tags/links
generically and never renders a note's markdown body — new frontmatter keys
(`stage`, `open_items`, `key_facts`, `last_updated`) and new body sections
(Background/History/Glimpse/Captures) are read/authored in Obsidian directly,
per this project's own established "Obsidian is the authoring surface"
convention. No `net-new-design-needed` trigger fires. See `## Notes` for the
prototype-parity breakdown.

## Dependencies

- **Blocks:** `REQ-SB-55-US-01` (Email Capture & Threading Pipeline — builds
  the Thread-populating pipeline on top of this data model), `REQ-SB-56-US-01`
  (Meeting Capture & Thread Linking — populates the Meeting→Thread link field
  this story only reserves), `REQ-SB-57-US-01` (Project & Customer Status
  Synthesizer Agents — the actual mechanism enforcing point 7's ownership
  rule and resolving point 5's History-line bar). ConversationID verification
  (point 9) is complete; cross-ID merging (point 10) is resolved by scope
  split, deferred to `REQ-SB-60` — neither blocks these three anymore.
- **Related to:** `REQ-SB-14` (Customer Hub Notes & Graph Connectivity,
  `Done`) — the existing baseline Customer note shape this requirement
  restructures, not replaces from scratch.
- **Related to:** `REQ-SB-08` (Meeting notes captured from calendar sync,
  `Done`) — the existing Meeting note shape this requirement extends with a
  Thread-link field.
- **Related to:** `REQ-SB-07` (Scheduled Recurring Agent Capture, `Done`) —
  the existing per-email capture shape Threads replace.
- **External:** live, read-only verification of `ConversationID` stability
  against the real, configured Outlook installation — a genuine technical
  prerequisite, not a code change; see Constraints and Notes.

## Constraints

- **Hard precondition — SATISFIED (2026-08-16).** `ConversationID`
  stability was verified live (read-only, no vault writes) against the
  real Outlook installation for false merging — no genuine collision
  found across 41 real multi-message threads (`T00`, done). The opposite
  failure mode (under-merging, point 10) is resolved by scope split, not
  by inventing a merge heuristic: `REQ-SB-60` (a new, deferred
  requirement) owns reconciling multiple `ConversationID`s into one real
  Conversation. This story's own Thread notes stay exactly one per
  `ConversationID` — `REQ-SB-55`'s `Thread-Match/Merge` Job may be built
  as originally specced.
- **Regenerate, don't patch, for anything meant to reflect current state**
  (Thread top summaries, any Glimpse) — never use
  `vault_writer.insert_body_line_if_missing`'s fixed-byte-offset incremental
  insertion for these sections (`MEMORY.md`, `BUG-003`/`ESC-003`).
- **Exactly one owner writes Glimpse/History per note.** This story
  establishes the rule at the data-model level only; it does not itself
  build the enforcement mechanism (`REQ-SB-57`'s scope) — do not have this
  story's own tasks write ad hoc Glimpse/History content from more than one
  code path.
- **Project's directory shape is CONFIRMED, not an assumption** — operator,
  2026-08-16: "Yes, Project gets the same directory shape as Customer."
  Scenario 5 is final.
- **Manual Captures content is never rewritten by any agent, under any
  circumstance** (Scenario 2) — this is a hard invariant, not a
  best-effort behavior.
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).

## Implementation Tasks

<!-- Decomposer's own table (2026-08-16, /plan-tasks step 2) — supersedes
the analyst's non-authoritative draft table above this note (the draft's
T00-T05 numbering is retired; see ## Notes for the full renumbering
rationale, including why T00 has no task file). -->

| ID | Type | Task | Files / Area | Task File | depends_on |
|---|---|---|---|---|---|
| REQ-SB-54-US-01-T01 | backend | `replace_body_section(path, header, new_content)` — new header-scoped full-region regeneration primitive (ADR-042 point 2) | `app/data_access/vault_writer.py` | `../Tasks/REQ-SB-54-US-01-T01-replace-body-section-primitive.md` | — |
| REQ-SB-54-US-01-T02 | backend | Thread note kind — deterministic path, baseline create/top-up, `## Summary` (regenerated) + `## Transcript` (append-only) | `app/data_access/vault_writer.py` | `../Tasks/REQ-SB-54-US-01-T02-thread-note-kind.md` | T01 |
| REQ-SB-54-US-01-T03 | backend | Meeting note schema extension — additive, empty `thread` field reserved for `REQ-SB-56` | `app/data_access/vault_writer.py` | `../Tasks/REQ-SB-54-US-01-T03-meeting-thread-link-field.md` | — |
| REQ-SB-54-US-01-T04 | backend | Directory-shaped OKF note-kind primitive family (generic, shared) + Customer application, `customer_hub_linking.py` restructure preserving all 5 real live call sites | `app/data_access/vault_writer.py`, `app/business/customer_hub_linking.py` | `../Tasks/REQ-SB-54-US-01-T04-okf-directory-family-and-customer.md` | T01 |
| REQ-SB-54-US-01-T05 | backend | Project directory-shaped note kind — reuses T04's generic family, nested under its own Customer directory | `app/data_access/vault_writer.py` | `../Tasks/REQ-SB-54-US-01-T05-project-directory-note-kind.md` | T04 |
| REQ-SB-54-US-01-T06 | backend | `list_all_note_paths()` two-levels-deep recursion extension (the flagged ADR-042 Consequence) | `app/data_access/vault_writer.py` | `../Tasks/REQ-SB-54-US-01-T06-list-all-note-paths-recursion.md` | T04, T05 |

No cycles. `T00` (ConversationID stability, point 9) is NOT a task file — see
`## Notes` for why; its result is already recorded above in this story's own
`## Notes`/Definition of Done, done 2026-08-16.

## Definition of Done

- [x] ConversationID stability verification (point 9) is complete and its
      result is recorded in this story's `## Notes`, before any other task
      begins — done 2026-08-16, no genuine collision found. (Referred to
      as `T00` in the analyst's own draft table; the decomposer's own
      `/plan-tasks` pass did not create a `T00` task file for this
      already-completed, no-code verification — see `## Notes`.)
- [x] All acceptance-criteria scenarios pass — all 5 (`AC-01`..`AC-05`) verified live, manual mode (see each owning task's own Implementation Log: `AC-01`→`T02`, `AC-02`→`T04`+`T05`, `AC-03`→`T04`, `AC-04`→`T01`, `AC-05`→`T05`).
- [x] Every Implementation Task above is complete (or explicitly dropped with reason) — `T01`-`T06` all `Done`.
- [x] All Constraints respected — confirmed per-task; no `insert_body_line_if_missing` reuse for a regenerated section, exactly one owner writes Glimpse/History content (data-model level only, per this story's own scope), Project's directory shape matches Customer's exactly, Manual Captures never rewritten by any code path (structurally confirmed in `T04`/`T05`'s own live tests).
- [ ] Automated tests added/updated and passing (once test tooling exists) — still `n/a`, test tooling pending across the whole project; every task verified manual-mode instead, per this project's own default verification mode.
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints — one consolidated story-level entry added on `T06`'s completion (`[2026-08-16] REQ-SB-54-US-01`), plus `T01`'s own already-recorded `replace_body_section` pattern entry.
- [x] `CHANGELOG.md` entry appended.

## Non-Goals / Out of Scope

- **Building the Email or Meeting capture pipelines themselves** — this
  story defines the target data shape only; `REQ-SB-55`/`REQ-SB-56` build
  the pipelines that populate it.
- **Actually linking a Meeting to a Thread** — `REQ-SB-54` only reserves the
  schema field; `REQ-SB-56` performs the real matching/linking.
- **Building the Glimpse/History/Background synthesis mechanism itself**
  (the actual regeneration triggers, the ownership-enforcement code, the
  exact History-line bar) — `REQ-SB-57`'s own scope.
- **Glimpse-first chat answering** — `REQ-SB-58`'s own scope.
- **Backfilling any existing vault content into the new shape** —
  `REQ-SB-59`'s own scope, and explicitly depends on this story plus
  `REQ-SB-55` through `REQ-SB-58` all being `Done` first.
- ~~Resolving whether Project gets the three-way split~~ — RESOLVED,
  operator-confirmed 2026-08-16 (see `## Notes`); no longer a Non-Goal.

## Notes

**Prototype parity (note-detail.html):**

- Frontmatter kv-list / tags / forward-links / backlinks — **N/A, not
  touched.** This story adds new frontmatter keys and new note kinds
  (Project) to an already-generic rendering mechanism; no new screen
  region is introduced.
- Note body/narrative content (Background/History/Glimpse/Captures) —
  **N/A, out of scope for any Second Brain screen.** No `html-prototype/`
  screen renders note body content today (confirmed by direct inspection);
  this content is authored/read in Obsidian directly, per this project's
  own established convention. No `/design` pass is needed for this story.

**Why `gate: clear` (all three MUST-FLAG triggers this story raised are
now resolved):**

1. **Trigger 1 (material assumption), point 6 — RESOLVED 2026-08-16.**
   Operator, direct confirmation: "Yes, Project gets the same directory
   shape as Customer." No longer a default — a confirmed decision. See
   `ESCALATIONS.md` → `ESC-037`, `Resolved`.
2. `REQ-SB-54` carries no `<!-- Draft -->`/unfinalised marker in the PRD —
   trigger 2 does not fire.
3. N/A (architect/ADR trigger).
4. `ESCALATIONS.md` → `ESC-037` was written for point 6 and is now
   `Resolved`, resolving artefact = the operator's own direct
   confirmation above.
5. Not oversized — the requirement's own PRD Acceptance text already scopes
   evidence-layer and synthesis-layer as one testable unit (a real capture
   run producing one Thread note, and one Customer note carrying all four
   sections with ownership respected); kept as one story to match.
6. N/A (coder trigger).
7. No contradictory PRD inputs found.
8. **RESOLVED 2026-08-16, twice, on two different axes.** Point 9
   (`ConversationID` FALSE-MERGE risk) verified, see T00 result below.
   The operator then corrected the resulting "safe to build on" verdict —
   point 10, the opposite failure mode (UNDER-merging) — but this was
   ALSO resolved same-day, by scope split rather than a build-blocking
   open question: merging related Threads is `REQ-SB-60`'s job (a new,
   deferred placeholder requirement), not this story's. Trigger-8 no
   longer fires on either axis.

**T00 result (2026-08-16, live, read-only, real Outlook installation) —
FALSE-MERGE check:** Scanned 300 inbox items → 155 distinct
`ConversationID`s, 41 with 2+ messages. All sampled multi-message threads
held together correctly under one `ConversationID` (verified example: a
real 3-message "G42/Data Lake RFP Discussion" thread spanning
2026-08-07–2026-08-14). Two apparent "collisions" (same ID, different
`ConversationTopic`) turned out to be the same conversation with an
edited subject line, not a real collision. **No false merge found** —
unlike `EntryID`/`GlobalAppointmentID` (`ESC-002`/`ESC-012`), this
identifier doesn't wrongly span unrelated messages.

**False-split (point 10), resolved by scope split, not a build blocker:**
operator: "I guess we keep threads as is and then we will need to have an
entity called Conversation where thread is the raw data, then we will
handle the data in the KB later." Thread stays exactly as originally
specced; `REQ-SB-60` owns the future merge logic once real Thread data
exists to design it against.

**What's still open (at analyst stage):** nothing. Point 6 resolved
2026-08-16 (operator, direct confirmation, see above) — the last of this
story's three analyst-stage MUST-FLAG triggers.

gate: flagged 2026-08-16, narrowed 2026-08-16, narrowed again 2026-08-16,
reset to `gate: clear` 2026-08-16 — every analyst-stage trigger this story
raised (point 6 material assumption; point 9/10 ConversationID
false-merge and false-split) was resolved before the architect pass
below. Its `REVIEW-QUEUE.md` item was removed; `ESCALATIONS.md` →
`ESC-037` is `Resolved`.

**Architect pass (2026-08-16) — `/plan-tasks` step 1:**

- **Architecture scope: §"Vault Knowledge Model Redesign — Threads,
  Manual Captures, OKF-Conformant Customer & Project Directories"
  (`Implementation/Architecture/architecture.md`, under `## Data Model`,
  appended after "Partner Hub Notes & Mutually-Exclusive Company
  Taxonomy"), §ADR-042 (`Implementation/Architecture/ADR.md`). The coder
  is bounded by these two sections for every task under this story —
  they define: the Thread note kind (`Work/Threads/<slug-of-conversation-
  id>.md`, deterministic path, `## Summary` regenerated + `## Transcript`
  appended); the Customer/Project 4-file OKF directory shape
  (`index.md`/`<slug>.md`/`log.md`/`captures.md`, Project nested one
  level inside Customer's own directory); the new `vault_writer.py`
  primitive family (directory baseline/top-up, the new
  `replace_body_section` header-scoped regeneration primitive, the
  JSON-encoded-string convention for `generated`/`verified`); and the
  flagged, not-yet-resolved `list_all_note_paths()` two-levels-deep
  recursion gap the decomposer must turn into an explicit task. Related,
  unmodified context also in scope for reference (not restructured by
  this story): §"Customer Hub Notes & Graph Linking" and §"Meeting Notes
  & Calendar-Attendee Extraction" (both under `## Data Model`) — the
  existing shapes this story restructures/extends respectively.
- **New ADR: `ADR-042`.** Genuinely required, not written reflexively —
  three real, disclosed gaps against the current codebase drove it (no
  existing primitive can regenerate a bounded body region without the
  already-documented fixed-byte-offset fragility, `BUG-003`/`ESC-003`; no
  existing note kind is a directory of multiple files; the existing
  frontmatter writer cannot round-trip OKF's nested `generated`/`verified`
  actor fields). Full reasoning, Alternatives Considered, and
  Consequences: `Implementation/Architecture/ADR.md` → `ADR-042`.
  **Extends, does not reopen, `ADR-004`** ("Customer is a tag, never a
  folder level") — the new directory shape governs the hub/synthesis
  entities themselves (already an established carve-out since `REQ-SB-14`),
  never real content-note classification, which stays flat/tag-only
  exactly as `ADR-004` already established.
- **No `adr-deviation`/`out-of-scope` escalation.** The directory shape,
  the Project-nested-inside-Customer physical location, and the
  Threads/Meetings-stay-flat rule are all direct, operator-confirmed PRD
  text (`Documentation/PRD.md` → `REQ-SB-54` points 4–7), not architect
  invention or assumption — no `ESCALATIONS.md` entry was needed for this
  pass.
- **Gate: `flagged`, trigger-3 only.** Per Pipeline.md, touching an ADR
  is a MUST-FLAG trigger regardless of how well-resolved the underlying
  design is — this does not halt the stage; the decomposer runs next so
  a human reviews `ADR-042` and the resulting locked tasks together in
  one pass. See `REVIEW-QUEUE.md` for the pointer.

**Decomposer pass (2026-08-16) — `/plan-tasks` step 2:**

- **All 5 Gherkin scenarios locked** as `REQ-SB-54-US-01-AC-01`..`AC-05`,
  wording tightened for buildability (Scenario 1 in particular no longer
  requires `REQ-SB-55`'s still-unbuilt capture pipeline to be verifiable —
  it is reframed around this story's own primitives, which is what
  `REQ-SB-55` will call). None marked `locked: false` — every scenario has
  a real, observable outcome a direct primitive call or filesystem
  inspection can verify.
- **Six tasks written, `T01`-`T06`**, flat root, `depends_on` acyclic:
  `T01` (no deps) -> `T02`/`T04` -> `T05` -> `T06`; `T03` independent. See
  the `## Implementation Tasks` table above for the full breakdown. Every
  locked AC has at least one tagged verification step: `AC-01`->`T02`,
  `AC-02`->`T04`+`T05`, `AC-03`->`T04`, `AC-04`->`T01`, `AC-05`->`T05`.
- **No `T00` task file.** The analyst's own draft table listed a `T00`
  "ConversationID stability verification" task, but that verification is
  pre-story, read-only Outlook-installation work with no code to build —
  it already ran and its result is recorded above in this story's own
  `## Notes`/Definition of Done (done 2026-08-16, no genuine collision
  found). A task file exists for a buildable unit of code; there is
  nothing left to build for T00, so no phantom task file was created for
  already-completed verification.
- **Status: `Draft` -> `Ready`.** All three of the decomposer's own gating
  criteria are met (every AC locked; every locked AC has >=1 tagged step;
  `depends_on` is acyclic) — Pipeline.md's status/gate independence means
  this status transition proceeds even though `gate` stays `flagged` (the
  architect's trigger-3 human-review flag is not cleared by this pass;
  `/plan-sprints`'s own batch logic parks a flagged `Ready` story until a
  human resolves it in `REVIEW-QUEUE.md`).
- **A THIRD real, load-bearing consequence found live, beyond the two
  ADR-042 already named** (the `list_all_note_paths()` glob gap;
  `customer_hub_linking.py` needing restructuring) — found by reading the
  real current codebase, not assumed: `vault_writer.hub_note_path` /
  `hub_note_exists` / `create_customer_hub_note_baseline` /
  `ensure_hub_note_baseline_frontmatter` (the OLD flat-file Customer
  hub-note primitives) are directly, currently depended on by
  `app/business/partner_hub_linking.py::migrate_customer_to_partner`
  (`REQ-SB-16`, `ADR-009`, `Done`, a real shipped feature, reachable via
  a real endpoint) to locate and MOVE a customer's flat hub note into
  `Work/Partners/` during a real Customer->Partner reclassification. That
  function has no concept of the new 4-file directory shape and was never
  in this story's scope to teach it one (`ADR-042`'s own Alternatives
  explicitly reject generalizing the directory shape beyond Customer/
  Project). **Resolution (T04): the OLD flat-file primitives and
  `partner_hub_linking.py` are left completely untouched** — they keep
  serving any customer whose hub note predates this story. Only
  `customer_hub_linking.ensure_customer_hub_note`'s own internal body is
  restructured to build/top-up the NEW directory shape instead, via new,
  separately-named `vault_writer.py` functions — its external return
  shape (`{"hub_note_path": str, "created": bool}`) is unchanged, so all
  5 real call sites (`email_classification.py`, `meeting_classification.
  py`, `people_extraction.py`, `todo_classification.py`,
  `vault_filing_expert.py`) keep working unmodified. `link_note_to_
  customer_hub`/`ensure_hub_note_and_link`/`retrofit_customer_hub_links`
  also need zero changes — confirmed live-by-reasoning: the new concept
  file's own filename stem (`_slugify(customer)`) is byte-identical to
  the old flat file's stem, so the existing inline `**Customer:**
  [[<stem>]]` wikilink resolves correctly either way; and the new concept
  file's OKF frontmatter schema has no plain `customer:` key, so
  `retrofit_customer_hub_links`'s existing `customer`-field filter
  naturally skips it (no self-link bug). **A genuine, disclosed,
  deferred gap remains and is NOT fixed by this story:** a customer
  onboarded AFTER this story ships gets the NEW directory shape only, and
  `migrate_customer_to_partner`'s own hub-note-move step (keyed off the
  OLD `hub_note_path`) will silently no-op for that customer — a real
  future defect once REQ-SB-54 ships, worth a follow-up bug/story once
  observed, but out of this story's own declared scope (Partner does not
  get the OKF directory shape, per `ADR-042`). Flagged here and in
  `REVIEW-QUEUE.md`, not silently absorbed or silently fixed.
- **Design judgement call, not an escalation:** `list_all_note_paths()`'s
  fix (`T06`) hardcodes the literal `Customers/*/*.md` and
  `Customers/*/projects/*/*.md` glob shapes rather than a fully dynamic
  "detect any directory-shaped kind" scan — deliberate, matching
  `ADR-042`'s own explicit, non-generalized 2-kind scope (its Alternatives
  Considered reject generalizing the directory shape to every kind as
  scope creep). A low-probability, disclosed edge case: a customer/
  project whose own slug literally equals `index`/`log`/`captures` would
  have its concept file wrongly filtered out by `T06`'s reserved-filename
  exclusion — an OKF-convention-inherent ambiguity, not something this
  story's own primitives can resolve without deviating from OKF's own
  reserved-filename standard; not defended against, per this project's
  "minimal changes" convention.

gate: flagged 2026-08-16 (decomposer pass) — trigger-3 carried forward
unresolved from the architect pass (ADR-042 still awaits human review);
this pass's own additional finding (the `partner_hub_linking.py`
blast-radius consequence, and the resulting `hub_note_path`-preservation
decision) is folded into the same open flag, not a second separate one —
see `REVIEW-QUEUE.md`.

gate: clear 2026-08-16 — operator reviewed `ADR-042` in full and approved
it with no changes requested. `REVIEW-QUEUE.md` entry removed. Ready for
`/plan-sprints`.

**Product-owner pass (2026-08-16) — `/plan-sprints`:** grouped into
`SPRINT-048` (single sprint, all 6 tasks — this is the only `Ready`,
ungrouped story right now, so the only real decision was whether to split
its own 6-task chain across ordered sprints; not warranted, see
`SPRINT-048`'s own Grouping Rationale). `depends_on_sprints: []`. No
MUST-FLAG trigger fired (not oversized against the `~6 tasks, M` precedent
in `Implementation/Learnings.md`; not blocked; no cross-sprint dependency
introduced; exactly one valid partition). `sprint: SPRINT-048` written to
this story's frontmatter (bidirectional link); `SPRINT-048` advanced
`Draft` → `Ready`.

gate: clear 2026-08-16 (product-owner) — no triggers fired.

**Coder pass (2026-08-16) — `/implement-sprint`, `T06` (last task):**
`list_all_note_paths()` extended to also discover the Customer/Project OKF
concept files (`ADR-042`'s own flagged Consequence), verified live against
a real 2-level-deep Customer + Project pair created via `T04`/`T05`'s own
primitives, with a full regression check confirming every previously-
discoverable flat note kind is unaffected. **Status: `In Progress` →
`Done`** — all 6 tasks (`T01`-`T06`) are `Done`, all 5 locked ACs verified
live. Two non-blocking `REVIEW-QUEUE.md` spot-check items remain open from
`T04`/`T05` (slug casing; a small private path-resolution helper) — neither
blocks story completion, both scope-internal judgement calls awaiting
human spot-check, not defects. The disclosed, deferred
`migrate_customer_to_partner`/new-customer-after-this-ships gap (recorded
above, decomposer pass) remains a genuine, out-of-this-story's-scope future
follow-up, not fixed here — see `SPRINT-048`'s own Retrospective → Open
follow-ups.

gate: clear 2026-08-16 (coder) — no new MUST-FLAG trigger fired on `T06`
itself; the two open `REVIEW-QUEUE.md` items are carried forward from
`T04`/`T05`, already disclosed, non-blocking.
