---
id: REQ-SB-71-US-02
title: Email Capture Redesign — Thread raw/distilled split, two-stage operator-triggered capture, Files/OKF companions
requirement_ids: [REQ-SB-71]
requirement_section: "REQ-SB-71: Redesigned Email & Meeting Capture — Raw/Distilled Split, Section-Ownership Enforcement, People Auto-Extraction, File Companion Notes (points 1, 2, 5)"
phase: P1
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-048 created) — architect pass, 2026-08-18. Analyst's own gate: clear reasoning below is unaffected/preserved; the flag is the architect's own, added on top, per Implementation/Pipeline.md's ADR trigger. See ## Notes. [Coder, 2026-08-18: all 7 tasks Done, all 7 locked ACs verified live against the real operator mailbox/vault — see each task's own Implementation Log. This flag stays open for the human's own pending ADR-048 review; not this role's to clear. A second, separate finding (ESC-048, out-of-scope, non-blocking) is also open — see REVIEW-QUEUE.md.]"
sprint: "SPRINT-061"
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-71-US-02 — Email Capture Redesign — Thread raw/distilled split, two-stage operator-triggered capture, Files/OKF companions

## Story

**As a** Second Brain operator
**I want** every individual captured email to become its own immutable,
verbatim raw message note, the Thread note itself to become a distilled
`## Summary`/`## Personal Notes`/`## Actions` layer regenerated on demand
from those raw messages via two decoupled stages, and every real email
attachment to become a first-class `files/<slug>/` entry with its own
OKF companion note — every step reachable only by MY OWN direct, real HTTP
call (mine, or Claude Code's acting on my behalf), never a background
schedule
**So that** raw email content is preserved verbatim forever regardless of
what any future re-synthesis does, the Thread's own distilled view can be
safely regenerated without ever risking my own Personal Notes/Actions, an
attachment becomes a real, backlink-discoverable thing in its own right
instead of a buried sub-entry, and I stay in full control of exactly when
capture happens

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-71*, points 1 (Thread raw/distilled
  split), 2 (two-stage pipeline), 5 (Files/OKF companions), plus the
  requirement's own standing "reachable via a real HTTP endpoint" constraint
  and its explicit "Out of scope — scheduling/autonomous triggering" block.
  Raised 2026-08-18. **Supersedes `REQ-SB-55-US-01`'s current Thread shape
  going forward** — that story stays `Done`, untouched (specs are
  append-only, `Implementation/Pipeline.md` hard rule 1); this is new
  forward work, mirroring `REQ-SB-53`'s own SUPERSEDED precedent, not a
  retroactive edit.
- **Explicitly, this requirement builds NO scheduling/autonomous
  triggering.** The PRD's own dedicated block: *"Every call into these APIs
  is operator-initiated, with the operator's own AI assistant (Claude Code)
  acting on their behalf as the caller — 'you will be acting as me.'
  `/plan-tasks`/`/implement-sprint` must not add scheduler wiring,
  background-agent registration, or any `agent_schedule_registry` entry for
  either pipeline as part of this requirement."* `REQ-SB-55-US-01`'s own
  existing scheduled `email-capture-pipeline` capability (`capture_
  scheduler.py`, `agent_schedule_registry`) stays wired exactly as it is
  today, completely untouched by this story — this story supersedes its
  Thread *shape*, never its *trigger mechanism*. Every Scenario below is
  written as a direct, real API call the operator (or Claude Code) makes,
  never as a description of a recurring tick.
- **Real code read directly to ground this story, not assumed:**
  - `app/business/email_classification.py::thread_match_merge` (`REQ-SB-55-
    US-01-T03`, extended by `REQ-SB-69-US-01`) — today's single-file Thread
    shape: one Thread note IS the transcript, `## Summary` regenerated from
    only the LATEST message, `## Transcript` grows by append, `## Related`
    regenerated wikilinks. This story replaces the "one file IS the
    transcript" model; `## Transcript`'s own append-by-accumulation role is
    superseded by the new raw `messages/` folder.
  - `app/data_access/email_staging.py` + `app/business/pipelines/email_pull.
    py::pull_and_stage_emails` + `app/business/pipelines/email_capture_
    pipeline.py::run_email_capture_pipeline` (`REQ-SB-69-US-01`, `Done`,
    `ADR-046`) — **this is the DIRECT precedent the PRD's own point 2 names
    explicitly** ("matching this project's own decoupled-pull lesson"):
    `pull_and_stage_emails` already does exactly what this story's new
    Stage 1 wants for the OUTLOOK-fetch half — a fast, cheap, durable,
    vault-local staging write with zero Compass dependency, already proven
    resumable and stall-isolated. `process_staged_email` already does what
    this story's new Stage 2 wants for the COMPASS-backed half — the real
    Classify/Thread-Match-Merge judgment. The PRD's own text says this
    story's split is that SAME lesson "extended one level deeper": today's
    `process_staged_email` step (fetch already done, staged content already
    durable) is itself being split further — a first sub-step that writes
    the raw, immutable per-message note and a provisional `ConversationID`-
    only grouping with zero Compass calls, and a second sub-step that does
    the real Compass-backed Customer/merge judgment and regenerates the
    distilled `## Summary`. Whether this story's own two stages are built
    as genuinely new functions/endpoints layered on top of the EXISTING
    `email_staging`/`email_pull` primitives, or as a parallel mechanism, is
    left open below (mechanism-level, not scope-level).
  - `vault_writer.write_attachments`/`app/business/email_classification.py::
    summarize_attachment` (`REQ-SB-55-US-01-T05`) — today's attachment
    handling: saved under `<subfolder>/attachments/<note-slug>/<message-
    slug>/<filename>`, its own summary buried as a dated sub-entry string
    fed into `## Attachments`, never its own note. This story replaces that
    shape with `files/<file-slug>/<original-filename>` beside `files/
    <file-slug>/<file-slug>.md` (an OKF-shaped companion, reusing the
    already-shipped `compass_client.summarize_content` primitive
    `summarize_attachment` already calls).
  - `vault_writer.replace_body_section`/`REQ-SB-71-US-01` (this batch's own
    sibling story) — the code-enforced allow-list guard this story's own
    Thread `## Summary` regeneration must be assigned a correct allow-list
    against from day one.
- **"## Actions" open question, explicitly named by the PRD for `/spec` to
  resolve — resolved directly here, not guessed, and not flagged:** the
  PRD's own point 1 asks whether `## Actions` should be "a literal
  checklist section, or backed by this codebase's existing `todo_
  classification`/todo-capture mechanism so an Action surfaces wherever
  else todos are tracked." **Resolved: a literal, human-typed checklist
  section, identical in kind to `## Personal Notes` — never backed by an
  agent-driven sync to/from `todo_classification`.** Reasoning: this same
  requirement's own point 6 defines "human-owned" as "an agent may read it
  for context, but no agent code path may ever write to it" — a `todo_
  classification`-backed sync, in EITHER direction (an agent writing a
  captured to-do INTO `## Actions`, or an agent writing an `## Actions`
  entry OUT to the to-do system), would require an agent code path to write
  into `## Actions`, directly contradicting the requirement's own hard rule
  for human-owned sections. This is not a coin-flip between two equally
  valid readings — one of the two readings the PRD itself poses is
  structurally incompatible with the SAME requirement's own point 6, so the
  literal-checklist reading is the only one that keeps this requirement
  internally consistent. (`REQ-SB-09`'s own existing `todo_classification`
  pipeline is untouched by this resolution — it keeps working exactly as it
  does today, independently of a Thread's own `## Actions` section.)
- **Why Files (point 5) lands here, not as its own story or inside the
  Meeting story:** the PRD's own text frames it as a generic convention
  ("applies uniformly to every concept family that can carry files... one
  convention, not a special case per kind"), but the only concept family
  with a REAL, currently-flowing attachment pipeline in this batch is
  Email/Thread (`summarize_attachment`, above) — Meeting attachments are
  not a currently-captured concept in this codebase (`list_calendar_events`
  reads no attachment field at all, confirmed by direct reading). Building
  the new `files/<slug>/` + OKF-companion primitive generically here
  (parameterized exactly like today's `write_attachments(subfolder,
  note_stem, ...)` already is), against the one real, concrete need, mirrors
  this project's own repeatedly-applied "build one real thing, generalize
  only once a second real need exists" precedent (`ADR-041`'s own Builder-
  after-two-real-instances sequencing; `REQ-SB-54-US-01`'s own `okf_
  directory_*` family built once for Customer then reused UNCHANGED for
  Project, "zero duplicated logic," per this project's own `MEMORY.md`
  entry) — a future Meeting/People/Opportunity attachment need reuses this
  same primitive without rebuilding it, exactly like Project reused
  Customer's own OKF-directory primitives.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: A real email produces its own immutable, verbatim raw message note

```gherkin
Given the operator (or Claude Code, acting on the operator's behalf)
    directly calls the real Stage 1 capture endpoint for a real, newly
    arrived email
When that call completes
Then a new, verbatim raw message note exists at Work/Threads/<thread-
    slug>/messages/<date>-<message-id>.md, never edited by any later step
  And that Thread's own distilled note, Work/Threads/<thread-slug>/
    <thread-slug>.md, exists (created if new) with an empty or
    not-yet-synthesized ## Summary — Stage 1 itself never generates ##
    Summary content
```
<!-- AC-ID: REQ-SB-71-US-02-AC-01 -->

### Scenario 2: A second message in the same conversation never modifies an earlier raw message note

```gherkin
Given a Thread already has one real raw message note under its own
    messages/ folder, from Scenario 1
When a second, later real email in the SAME conversation is captured via
    a further direct Stage 1 call
Then a NEW, second raw message note is written under the same messages/
    folder
  And the first raw message note's own content is byte-for-byte
    unchanged — no raw message note is ever edited once written
```
<!-- AC-ID: REQ-SB-71-US-02-AC-02 -->

### Scenario 3: Stage 1 groups purely by ConversationID, with zero Compass calls, and never fails when Compass is unavailable

```gherkin
Given Compass (the LLM Provider this pipeline's real judgment depends on)
    is deliberately unavailable or slow
When the operator directly calls the Stage 1 capture endpoint for a real
    email
Then Stage 1 still completes successfully — the raw message note is
    written and the email is provisionally grouped into a Thread using
    Outlook's own ConversationID alone, with no LLM call made and no
    dependency on Compass being reachable
```
<!-- AC-ID: REQ-SB-71-US-02-AC-03 -->

### Scenario 4: Stage 2, called directly by the operator, does the real Compass-backed judgment and regenerates the Thread's distilled Summary

```gherkin
Given one or more raw message notes exist under a real Thread's own
    messages/ folder, staged by Stage 1
When the operator directly calls the real Stage 2 endpoint for that
    Thread
Then Stage 2 determines the real Customer this Thread belongs to, decides
    merge-vs-new-Thread using its own real judgment (not the provisional
    ConversationID-only grouping alone), and regenerates the Thread note's
    ## Summary from the real content of every raw message note under
    messages/ — via REQ-SB-71-US-01's own allow-list-checked replace_body_
    section, declared with this caller's own correct allow-list
```
<!-- AC-ID: REQ-SB-71-US-02-AC-04 -->

### Scenario 5: A stall in Stage 2 never blocks Stage 1 from continuing to capture further raw mail

```gherkin
Given a real or deliberately-induced stall inside a Stage 2 call for one
    Thread
When the operator directly calls the Stage 1 endpoint again, for a
    different, unrelated real email, while that Stage 2 call is still
    stalled
Then the new Stage 1 call completes normally and writes its own new raw
    message note — it does not wait for the stalled Stage 2 call to finish,
    because the two never share a lock (the same proof obligation REQ-SB-69
    already established for the pull/process split, extended one level
    deeper, per the PRD's own text)
```
<!-- AC-ID: REQ-SB-71-US-02-AC-05 -->

### Scenario 6: A manually-added Personal Notes/Actions entry survives byte-for-byte across a Stage 2 re-synthesis

```gherkin
Given a real Thread note whose ## Personal Notes and ## Actions sections
    each carry a real, manually-typed entry the operator wrote directly in
    Obsidian
When the operator directly calls the Stage 2 endpoint again for that same
    Thread (e.g. because a further raw message arrived)
Then the Thread's ## Summary is regenerated from the current full set of
    raw messages
  And the ## Personal Notes and ## Actions sections' own manually-typed
    content survive byte-for-byte, untouched — neither section is ever
    targeted by Stage 2's own regeneration call
```
<!-- AC-ID: REQ-SB-71-US-02-AC-06 -->

### Scenario 7: A real email attachment produces a files/ entry with its own OKF companion note

```gherkin
Given a real captured email carries a real attachment
When that email's raw message note is written (Stage 1) and, once
    Stage 2 has run, its Thread has a real, determined identity
Then a files/<file-slug>/ directory exists containing both the original
    attachment file, byte-identical and untouched, and a generated OKF
    companion note (files/<file-slug>/<file-slug>.md) whose ## Summary
    carries a real, genuine Compass-generated summary of that file's own
    content — never a buried, unlinked sub-entry inside the Thread note
    itself
```
<!-- AC-ID: REQ-SB-71-US-02-AC-07 -->

## Affected Screens

None — backend and vault-content only. No PRD text for `REQ-SB-71` names a
UI surface. `html-prototype/vault-browser.html`/`note-detail.html`
(`REQ-SB-14-US-01`, already built) render whatever real note/folder
structure exists in the vault generically — they need no change to
display the new raw/distilled Thread shape or the new `files/` layout.
`html-prototype/inbox-cockpit.html` (`REQ-SB-44-US-01`, `Done`) is a real,
disclosed area of risk, not confirmed safe here: its own backend
(`app/business/cockpit/attachments.py`) hardcodes `Work/Emails/attachments`
as its attachment root — a path that predates even `REQ-SB-54`'s own
Thread redesign and does not match this story's new `files/` shape either.
Whether Inbox Cockpit's attachment listing needs updating to read the new
`files/` shape is a real, disclosed open question left to the architect,
not assumed fixed or left broken silently — see `## Notes`.

## Dependencies

- **Blocked by (hard):** `REQ-SB-71-US-01` (Section-Ownership Enforcement)
  — this story's own Thread `## Summary` regeneration (Scenario 4/6) must
  call the allow-list-checked `replace_body_section` from day one, never
  landing ungated even briefly.
- **Related to:** `REQ-SB-55-US-01` (`Done`, `SPRINT-049`) — the pipeline
  this story supersedes going forward (Thread shape only); that story's
  own file stays `Done`, unedited.
- **Related to:** `REQ-SB-69-US-01` (`Done`, `SPRINT-056`, `ADR-046`) — the
  direct precedent for this story's own Stage 1/Stage 2 split
  ("extended one level deeper," per the PRD's own text); `email_staging.py`/
  `email_pull.py`/`email_capture_pipeline.py` are the concrete modules this
  story's own mechanism question (below) is grounded against. That story's
  own scheduled `pull_email`/`process_staged_email` capabilities stay wired
  to the scheduler exactly as-is, untouched by this story.
- **Related to:** `REQ-SB-54-US-01` (`Done`, `ADR-042`) — the OKF-directory/
  `replace_body_section` primitives this story's Files convention and
  Thread regeneration both build on.
- **Related to:** `REQ-SB-57-US-01` (`Done`) — Project/Customer Glimpse
  synthesis, which reads Thread evidence; must keep resolving correctly
  once the Thread note's own path/shape changes (a regression risk named,
  not newly introduced — the same class of risk `REQ-SB-69-US-01` already
  disclosed and resolved for its own filename-rename mechanism).
- **Related to:** `REQ-SB-56-US-01` (`Done`) — Meeting↔Thread linking;
  `REQ-SB-71-US-03` (Meeting story) reads this story's own new Thread shape
  for its recurring-occurrence History synthesis (see that story's own
  `## Dependencies`).
- **Related to, soft only:** `REQ-SB-70-US-01` — the empty `Work/Threads/`
  scaffold this pipeline writes into; not a hard code dependency (see that
  story's own `## Context`).
- **External:** none new.

## Constraints

- **No scheduler wiring, no `agent_schedule_registry` entry, no cron-style
  recurring tick for either stage** — every call is operator-initiated
  (Claude Code acting on the operator's behalf as the caller), per the
  PRD's own explicit out-of-scope block. `REQ-SB-55-US-01`/`REQ-SB-69-US-01`'s
  existing scheduled capabilities are not touched, removed, or duplicated.
- **Every raw message note is write-once** — never edited once written
  (Scenario 2).
- **Stage 1 has zero dependency on Compass being up, fast, or reachable**
  (Scenario 3) — zero LLM calls inside Stage 1.
- **Thread `## Summary` regeneration must go through `REQ-SB-71-US-01`'s
  own allow-list-checked `replace_body_section`** — this story does not
  build a second, parallel, unguarded write path to that section.
- **`## Personal Notes` and `## Actions` are both literal, human-owned,
  freeform/checklist sections** — never targeted by any agent write path in
  this story, including Stage 2's own regeneration (Scenario 6).
- **The Files/OKF-companion mechanism is built generically** (parameterized
  by subfolder/note-stem, mirroring `write_attachments`'s own existing
  shape) — not hardcoded to Thread specifically, so a future concept family
  can reuse it unchanged.
- **Every capability is reachable only via a real HTTP endpoint** — every
  build-time and later verification call goes through that endpoint, never
  a raw script.
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).

## Implementation Tasks

<!-- Analyst-authored starting point, non-authoritative — the decomposer's
own table at /plan-tasks supersedes this. Exact task count/shape is left to
the architect's own mechanism decisions (see ## Notes). -->

<!-- Decomposer table, /plan-tasks, 2026-08-18 — supersedes the analyst's
starting-point table above; the exact task shape below reflects the
architect's own resolved mechanism (## Notes addendum below). -->

| ID | Type | Task | Files / Area | Depends On | Task File |
|---|---|---|---|---|---|
| REQ-SB-71-US-02-T01 | backend | Thread directory shape (`thread_directory_paths`) + raw message note primitives (`raw_message_note_path`/`_exists`/`create_raw_message_note`) + `create_thread_note_baseline` revived for the new 2-part concept-file shape | `app/data_access/vault_writer.py` | — | `../Tasks/REQ-SB-71-US-02-T01-thread-directory-and-raw-message-primitives.md` |
| REQ-SB-71-US-02-T02 | backend | `list_all_note_paths()` generalized to a bounded recursive scan; `list_thread_notes()`/`resolve_thread_note_path()` retargeted to the new 2-level directory shape (signature-preserving) | `app/data_access/vault_writer.py` | T01 | `../Tasks/REQ-SB-71-US-02-T02-note-discovery-generalization.md` |
| REQ-SB-71-US-02-T03 | backend | Stage 1 pipeline — `capture_raw_thread_messages()`, reusing `email_pull.pull_and_stage_emails`/`email_staging` verbatim, zero Compass calls | `app/business/pipelines/raw_message_capture.py` (new) | T01 | `../Tasks/REQ-SB-71-US-02-T03-stage-1-raw-capture-pipeline.md` |
| REQ-SB-71-US-02-T04 | backend | `POST /poc/capture-raw-thread-messages` — new capability id of the existing `email-capture-pipeline` Agent, operator-triggered, no scheduler wiring | `app/api/email_poc_router.py` | T03 | `../Tasks/REQ-SB-71-US-02-T04-stage-1-endpoint.md` |
| REQ-SB-71-US-02-T05 | backend | Stage 2 — `email_classification.synthesize_thread()`: real Compass-backed Customer/merge judgment reading `messages/`, regenerates `## Summary`+`## Related` via the allow-list-checked `replace_body_section`; registers its own new caller in `section_ownership.py` | `app/business/email_classification.py`, `app/data_access/section_ownership.py` | T01, T02, REQ-SB-71-US-01-T01 | `../Tasks/REQ-SB-71-US-02-T05-stage-2-synthesize-thread.md` |
| REQ-SB-71-US-02-T06 | backend | `POST /poc/synthesize-thread?conversation_id=` — new capability id, sharing no lock with Stage 1 | `app/api/email_poc_router.py` | T04, T05 | `../Tasks/REQ-SB-71-US-02-T06-stage-2-endpoint.md` |
| REQ-SB-71-US-02-T07 | backend | `write_file_companion()` (generic `files/<slug>/` + OKF-lite companion note primitive) + wiring into email attachment capture once a Thread's identity is determined; registers its own new caller in `section_ownership.py` | `app/data_access/vault_writer.py`, `app/business/email_classification.py`, `app/data_access/section_ownership.py` | T05, REQ-SB-71-US-01-T01 | `../Tasks/REQ-SB-71-US-02-T07-files-okf-companion-convention.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists) — manual mode still in effect, per `Implementation/Pipeline.md`
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Any scheduler wiring, `agent_schedule_registry` entry, or cron-style
  recurring tick** — explicitly excluded per the PRD's own out-of-scope
  block; `REQ-SB-55`/`REQ-SB-69`'s existing scheduled capabilities stay
  wired exactly as-is.
- **Meeting capture** — `REQ-SB-71-US-03`'s own scope entirely.
- **People auto-extraction from meeting attendees, or the new nested-under-
  Customer People directory shape** — `REQ-SB-71-US-03`'s own scope; this
  story does not modify `people_extraction.py`'s existing email-participant
  extraction beyond what's needed to keep it working against the new
  Thread shape.
- **Backfilling already-captured Thread notes onto the new raw/distilled
  shape** — going-forward capture only, mirroring `REQ-SB-67-US-01`'s and
  `REQ-SB-69-US-01`'s own explicit "capture vs. backfill are separable
  concerns" precedent; a backfill (if wanted) is a `REQ-SB-59`-style
  follow-up, not built here.
- **Any change to Project/Customer synthesis logic itself** (`REQ-SB-57`) —
  only the shape of the Thread evidence it reads changes, never its own
  synthesis logic.
- **Conversation-merging across multiple `ConversationID`s** — `REQ-SB-60`'s
  own separately deferred future scope.
- **Fixing Inbox Cockpit's own pre-existing, hardcoded `Work/Emails/
  attachments` attachment root** — a real, disclosed pre-existing
  staleness (see `## Affected Screens`), not caused by this story and not
  fixed here; left to the architect to decide whether it's in this story's
  own scope or a separate, disclosed follow-up.

## Notes

**Prototype parity:** N/A — no `html-prototype/` screen change for the
capture pipeline itself. `vault-browser.html`/`note-detail.html` already
render vault content generically. `inbox-cockpit.html`'s own real,
disclosed attachment-path staleness is named above, not silently ignored.

**Mechanism-level questions left to `/plan-tasks`, not resolved by this
pass (Gherkin above specifies the OUTCOME, not the mechanism — mirrors
`REQ-SB-69-US-01`'s own identical precedent):**

1. **Whether Stage 1/Stage 2 reuse `REQ-SB-69-US-01`'s own existing
   `email_staging.py`/`email_pull.pull_and_stage_emails` as their raw-fetch
   substrate**, since that mechanism already does exactly what "Stage 1's
   raw capture, zero Compass calls" wants for the Outlook-fetch half — or
   whether a parallel, new mechanism is warranted specifically to avoid any
   entanglement with `REQ-SB-69`'s own scheduler-bound `pull_email`
   capability id. The PRD's own text explicitly frames this story's split
   as extending that SAME lesson "one level deeper," which is a strong hint
   toward reuse, but the exact code-level shape is a real architect
   decision, not asserted here.
2. **Whether the two stages are exposed as two genuinely separate
   endpoints** (mirroring `pull_email`/`process_staged_email`'s own
   two-capability precedent, just without either being scheduler-wired) **or
   as one endpoint whose own internal execution is merely structured in two
   decoupled sub-steps** — the PRD's own text explicitly allows either
   reading ("both synchronous to that call or at least both triggered by
   it"). Scenario 5 (a Stage 2 stall never blocks a further Stage 1 call)
   is written generically enough to hold under either shape.
3. **The raw message note's exact filename/message-id disambiguator** —
   left to the architect, mirroring `meeting_note_filename_stem`'s own
   already-shipped hash-suffix precedent.
4. **Exact new endpoint route names** — follow the existing `/poc/*`
   convention; left to the architect/decomposer.
5. **Whether Inbox Cockpit's own pre-existing attachment-path staleness
   (`## Non-Goals`) is folded into this story's own `T05` or filed as its
   own separate, disclosed follow-up** — a real, pre-existing gap this
   story's own reading surfaced, not caused by it.

**Why the "## Actions" resolution above does not trip trigger 1/trigger
8:** the PRD's own text explicitly delegates this exact decision to
`/spec` ("open question for `/spec` to resolve"), and the resolution
reached is not a guess among equally-plausible options — one of the two
readings the PRD itself poses is directly, structurally incompatible with
the SAME requirement's own point 6 (human-owned = no agent write path,
ever), so only one reading keeps the requirement internally consistent.
This mirrors `REQ-SB-69-US-01`'s own precedent of resolving a PRD-delegated
"implementation decision, not a product one" directly via grounded
reasoning, rather than flagging it.

**Why `gate: clear`:** every genuinely open question above is a MECHANISM
question this project's own role boundaries assign to the architect at
`/plan-tasks`, not a scoping/interpretation ambiguity that changes what
Gherkin to write here — every Scenario is written at the observable-outcome
level (mirroring `REQ-SB-69-US-01`'s own identical precedent). No material
assumption was made to fill a scoping gap (trigger 1 — the one PRD-
delegated question, `## Actions`, was resolved via direct internal-
consistency grounding, not assumed); `REQ-SB-71` carries no `<!-- Draft
-->` marker — finalized text (trigger 2 n/a); no ADR created/changed by
this analyst pass (trigger 3 n/a for this role); no `ESCALATIONS.md` entry
written (trigger 4 n/a); sizing — 5 starting tasks, comparable to
`REQ-SB-55-US-01`'s own original pipeline-build shape and smaller than
`REQ-SB-69-US-01`'s own 8-task shape (trigger 5 n/a); no contradictory PRD
inputs — the requirement's own "Five parts" phrasing vs. its own six
enumerated points (1-6) is a minor textual inconsistency, noted here for
completeness, but every one of the six points is unambiguously detailed
and covered by this batch's stories (this story covers 1/2/5; `REQ-SB-71-
US-01` covers 6; `REQ-SB-71-US-03` covers 3/4) — it does not create any
real scope ambiguity, so it is disclosed rather than treated as a
contradictory-input trigger; the Files-convention scoping decision (built
against the one real concrete need, Email/Thread, not built as its own
story) is grounded in a directly-cited codebase precedent (`REQ-SB-54-
US-01`'s own OKF-directory reuse), not an arbitrary pick (trigger 8 n/a).

gate: clear 2026-08-18 — no MUST-FLAG trigger fired (see the itemized
trigger-by-trigger reasoning above). [Analyst pass — see the architect
addendum immediately below for the trigger-3 flag added at `/plan-tasks`,
and for every mechanism-level question this story's own `## Notes` left
open, now resolved.]

---

**Architect addendum (2026-08-18, `/plan-tasks` step 1):**

**Mechanisms resolved (all five questions this story's own `## Notes`
explicitly left to `/plan-tasks`):**

1. **Stage 1 REUSES `email_pull.pull_and_stage_emails`/`email_staging`
   verbatim as its raw-fetch substrate** — new `app/business/pipelines/
   raw_message_capture.py` (sibling to `email_capture_pipeline.py`/
   `email_pull.py`) owns `capture_raw_thread_messages(limit: int = 10)
   -> dict`, which calls `pull_and_stage_emails` (joining `agent_schedule_
   registry.get_shared_dispatch_lock()`, the SAME lock `pull_email`
   already joins — concurrency-safety reuse, never a new `agent_schedule_
   registry` entry), then drains staged-but-not-yet-raw-noted mail. Zero
   `compass_client` import in this module.
2. **Two genuinely separate endpoints, each its own new, independent
   capability id of the EXISTING `"email-capture-pipeline"` Agent-tier
   identity** — `POST /poc/capture-raw-thread-messages`
   (`capture_raw_thread_messages`) and `POST /poc/synthesize-
   thread?conversation_id=<id>` (`synthesize_thread`), sharing no lock
   (Scenario 5's own proof obligation, mirroring `pull_email`/`process_
   staged_email`'s own precedent, `ADR-046` Decision 3).
3. **Raw message note filename:** `messages/<received[:10]>-<hash8
   (message_id)>.md` — `message_id` is the email's own `id`/EntryID field
   (already unique per message), hashed the same way `meeting_note_
   filename_stem` already hashes its own disambiguator.
4. **Endpoint routes:** as above — `/poc/*` convention, in the existing
   `app/api/email_poc_router.py`.
5. **Inbox Cockpit's own pre-existing hardcoded `Work/Emails/attachments`
   attachment-root staleness is NOT folded into this story's own `T05`** —
   disclosed as a separate, real regression risk against the new `files/`
   shape in architecture.md's own "Disclosed, unresolved-by-this-pass
   regression risks" (below); left to the decomposer to scope as a
   follow-up task or a separate story.

**Also resolved, beyond the five questions this story's own `## Notes`
named:** Thread becomes a DIRECTORY (`Work/Threads/<slug-of-
conversation_id>/`), permanently deterministic from `conversation_id`
alone — superseding `ADR-046`'s own human-readable/renamable Thread
FILENAME mechanism (no longer needed: the human-readable identity now
lives in the concept file's `thread_name` frontmatter, not the directory
name). `thread_match_merge` is replaced by `email_classification.
synthesize_thread(conversation_id) -> dict` (Stage 2's own real function),
which reconstructs `## Summary`/`## Related` from the FULL current set of
raw messages on every call (a deliberate reversal of `REQ-SB-67`'s own
rolling/incremental design — see `ADR-048` Alternatives Considered 6 for
why) and calls `classify_email` once against the FIRST raw message only,
preserving the existing "customer decided once, never contradicted later"
Constraint.

**Architecture scope:** `Implementation/Architecture/architecture.md` →
"Vault Base Provisioning + Redesigned Email/Meeting Capture..." §"Email
Capture Redesign — Thread Raw/Distilled Split, Stage 1/Stage 2
(`REQ-SB-71-US-02`)" and §"Files/OKF Companion Convention
(`REQ-SB-71-US-02`)" — the coder is bounded to those two subsections
(plus the shared §"Section-Ownership Enforcement" table for this story's
own two NEW caller registrations, `email_classification.synthesize_thread`
and `email_classification.write_file_companion`, and the cross-cutting
§"`list_all_note_paths()` generalization").

**ADR:** [ADR-048](../Architecture/ADR.md), Decisions 3-4 and Alternatives
Considered 4-7.

**Why `gate: flagged` now, despite the analyst's own `gate: clear` above:**
trigger-3 fired — this architect pass created `ADR-048`, which this story
depends on (`REQ-SB-71-US-01`) and is itself covered by; every genuinely
open mechanism question this story's own `## Notes` deferred to
`/plan-tasks` is resolved above, with reasoning, not guessed. Per
`Implementation/Pipeline.md`, this does NOT halt the pipeline — the
decomposer still runs next on all four stories. A `REVIEW-QUEUE.md` entry
has been added.

---

**Decomposer addendum (2026-08-18, `/plan-tasks` step 2):**

All 7 Scenarios locked as `REQ-SB-71-US-02-AC-01`..`AC-07`, wording
unchanged from the analyst's own text. 7 tasks — larger than the analyst's
own 5-task starting point, deliberately: the architect's own resolved
mechanism surfaced two real, separately-verifiable pieces of work the
analyst's table hadn't yet split out:

- **`T02` (`list_all_note_paths()`/`list_thread_notes()`/
  `resolve_thread_note_path()` generalization) is its own explicit task,
  not folded into `T01`.** This directly applies this project's own
  `Implementation/Learnings.md` `SPRINT-048` entry — *"A one-level
  discovery glob is a real, structural blind spot the moment ANY note kind
  gains a directory shape — make the fix its own explicit task, not an
  assumed side effect of the kind-adding task."* Thread's new directory
  shape is exactly that trigger a second time; `T02` also retargets
  `resolve_thread_note_path`'s own INTERNAL lookup (scan → deterministic
  path check) while preserving its PUBLIC signature
  (`conversation_id -> Path | None`) unchanged — this is what keeps
  `REQ-SB-71-US-03`'s own unmodified `_link_to_thread_by_conversation_id`
  (which calls `resolve_thread_note_path` directly) working against the
  new Thread shape with ZERO change to `meeting_classification.py`'s own
  linking code, satisfying that story's own Dependencies text ("linking
  mechanism is reused, not rebuilt").
- **`T07` (Files/OKF companion) is split from Stage 2 (`T05`) but kept
  dependent on it**, since Scenario 7's own Given/When makes the
  companion's own write a genuine second step gated on Stage 2 having
  determined the Thread's real identity first — not concurrent, sequenced.

`T04`/`T06` (the two endpoints) are kept as their own tasks, separate from
the business-logic tasks they expose (`T03`/`T05`) — mirrors this
project's own repeated business-logic/endpoint task-pairing precedent
(e.g. `REQ-SB-69-US-01-T02`/`-T04`), and keeps `AC-05`'s own "no shared
lock between the two stages" proof cleanly attachable to `T06` (the last
task in the chain that can call BOTH real endpoints).

**`AC-01`/`AC-02`/`AC-03` are tagged in `T04`** (the Stage 1 endpoint,
where the parent story's own Constraint — "every capability is reachable
only via a real HTTP endpoint... never a raw script" — is actually
satisfiable end-to-end), not in the lower-level `T01`/`T03`. **`AC-04`/
`AC-05`/`AC-06` are tagged in `T06`** (the Stage 2 endpoint, same
reasoning — `AC-05` specifically needs both endpoints reachable, hence
`T06 depends_on: [T04, T05]`). **`AC-07` is tagged in `T07`.**

**Disclosed, decomposer-level scoping calls (not new MUST-FLAG triggers —
both were explicitly left open by the architect for this pass to decide,
`## Affected Screens`/`ADR-048` Consequences):**

1. `inbox-cockpit.html`'s backend (`app/business/cockpit/attachments.py`,
   hardcoded `Work/Emails/attachments`) is **NOT** folded into any task in
   this story — the architect's own addendum above already resolved this
   ("NOT folded into this story's own `T05`"; renumbered `T07` here). It
   stays a disclosed, real regression risk against the new `files/` shape,
   left as a follow-up for a future story/task, not silently fixed or
   silently left broken.
2. No task in this story touches `thread_match_merge`'s own retirement
   (`ADR-048` Consequences: *"Confirming and retiring the function itself
   ... is a coder-level task-scoping decision"*) — `T05`'s own coder may
   retire it as a scope-internal judgement call once `synthesize_thread`
   fully replaces its role, logged in that task's own Implementation Log,
   mirroring this project's own established retirement-discipline
   precedent; not pre-decided here as a separate task.

**Status → `Ready`; `gate` left `flagged`** (architect's own `ADR-048`
flag, not cleared by this pass). No new MUST-FLAG trigger fired: no
material assumption beyond the architect's own already-resolved mechanism
questions (trigger 1 n/a); nothing `<!-- Draft -->` (trigger 2 n/a); this
pass did not itself touch `ADR-048` (trigger 3 n/a for this role); no
`ESCALATIONS.md` entry (trigger 4 n/a); not oversized — 7 tasks, between
`REQ-SB-55-US-01`'s original 8-task shape and the analyst's own 5-task
starting estimate, growing only for the two genuinely separable pieces of
work named above, not scope creep (trigger 5 n/a); every locked AC got a
tagged verification step (trigger 6 n/a); no contradictory inputs
(trigger 7 n/a); the task split above is grounded directly in a cited
Learnings entry and a cited cross-story dependency requirement, not a
coin-flip (trigger 8 n/a).

**AC → verification mapping:** `AC-01`-`AC-03` tagged in `T04`; `AC-04`-
`AC-06` tagged in `T06`; `AC-07` tagged in `T07`. No locked AC is left
unverified.

gate: flagged (unchanged, architect's own `ADR-048` trigger-3) — decomposer
pass added nothing new to flag. See `REVIEW-QUEUE.md`'s existing
`REQ-SB-70-US-01 + REQ-SB-71-US-01 + REQ-SB-71-US-02 + REQ-SB-71-US-03`
entry (already covers all four stories in this batch; not duplicated
here).

---

**Coder addendum (2026-08-18, `/implement-sprint SPRINT-061`):**

All 7 tasks built and marked `Done`, all 7 locked ACs (`AC-01`-`AC-07`)
verified with real, live evidence against the real operator Outlook
mailbox and the real vault (`C:\myWorx\Moussa MD\Moussa Brain`) — every
verification call went through a real `POST /poc/*` HTTP endpoint, never
a raw script call, per this story's own standing Constraint. Full
evidence in each task's own `## Implementation Log`; summarized:

- **`AC-01`/`AC-02`/`AC-03`** (`T04`): one real Stage 1 call drained a
  large real backlog into 252 real, verbatim raw message notes across 127
  real Thread directories, each Thread's own concept file left with an
  empty `## Summary`; two distinct real raw notes confirmed coexisting
  under one real multi-message Thread, neither ever overwritten; Stage 1
  confirmed to complete successfully (`200 OK`, 1.3s) with Compass
  pointed at a deliberately unreachable address, zero LLM dependency.
- **`AC-04`/`AC-05`/`AC-06`** (`T06`): real Stage 2 calls against two real
  multi-message Threads regenerated `## Summary` from the FULL real
  content of every raw message (confirmed textually, not just the
  latest); a real, naturally-occurring 60-90s Compass latency served as a
  genuine Stage 2 "stall," during which a real Stage 1 call for unrelated
  mail completed independently in 0.83s — real, live, direct proof the
  two endpoints share no lock; a manually-added, real `## Personal
  Notes`/`## Actions` entry survived a real re-synthesis byte-for-byte,
  confirmed via matching SHA-256 hashes before/after.
- **`AC-07`** (`T07`): three real attachments (one PDF, two repeats of a
  PDF+XLSX pair across different messages) each produced their own real
  `files/<slug>/` directory with the byte-identical original file beside
  a genuine, Compass-generated OKF companion note — never a buried
  sub-entry.

**Two real bugs found live during verification, both fixed in-scope
(within the finding task's own `## Files to Modify`), both logged in
detail in the relevant task's own Implementation Log:** (1)
`synthesize_thread`'s initial call to the raw `classify_captured_email`
let a real, pre-existing Compass classification-parse failure crash the
whole Stage 2 call with an unhandled `500` — fixed by switching to the
already-established `classify_captured_email_with_fallback`
(`BUG-015`'s own precedent) (`T05`). (2) The Files/OKF companion's
initial `file_slug` silently exceeded `_slugify`'s own 80-char cap,
dropping the real filename and risking a same-message multi-attachment
collision — fixed to a short `hash8(message_id)-<filename>` disambiguator,
re-verified live for a real 2-attachment message (`T07`).

**One real, disclosed, non-blocking out-of-scope finding, recorded as
`ESC-048`:** `T02`'s own mandated retargeting of `resolve_thread_note_
path` (required for the new Thread shape) breaks the still-live,
scheduled `thread_match_merge` pipeline's own create-vs-update check for
every pre-redesign, flat-shape Thread note — confirmed live (zero of this
vault's real pre-existing flat Thread notes are found by the retargeted
lookup). Retiring `thread_match_merge`'s live call site would require
editing `email_capture_pipeline.py`, a file no task in this story
declares — an unanticipated-file trigger, not improvised past. As a real
protective measure, `email-capture-pipeline`'s working mode was flipped
`autonomous` → `supervised` via the real `PATCH /agents/email-capture-
pipeline` endpoint before any code was written this session, and
deliberately left `supervised` at completion. This finding blocks nothing
in this story (none of the 7 locked ACs exercise the old path) — full
detail, resolution options, and the human decision needed are in
`ESC-048`/`REVIEW-QUEUE.md`.

Story status → `Done`. `gate` left `flagged` — the architect's own
`ADR-048` human-review flag is not this role's to clear.
