---
id: REQ-SB-67-US-01
title: Real Per-Thread Summary Synthesis (live capture) + One-Shot Backfill for Already-Captured Threads
requirement_ids: [REQ-SB-67]
requirement_section: "REQ-SB-67: Real Per-Thread Summary Synthesis + Existing-Thread Backfill"
phase: P1
status: Done
gate: clear
gate_reason: "Analyst pass: no MUST-FLAG trigger fired. Both scope questions the PRD explicitly leaves open for /spec are resolved below by direct, repeated, uncontested existing codebase precedent (see ## Notes) rather than by guessing between equally-valid options; the requirement itself is finalised (not <!-- Draft -->/unfinalised) in the PRD; no ADR is touched by an analyst; no ESCALATIONS.md entry was needed; the story is normally sized (3 tasks, matching the REQ-SB-65/REQ-SB-66 single-story precedent for a comparably-scoped extension of an already-Done pipeline); no contradictory PRD input was found. Architect pass (2026-08-17, /plan-tasks step 1): no new ADR — reversing REQ-SB-55-US-01's own story-level 'no second Compass call' Constraint via a new story narrows a story-level scoping decision, not any Accepted ADR's own Decision text (confirmed by direct re-reading of ADR-043's seven numbered points); extends ADR-044's own already-anticipated Consequence (thread_match_merge's Job-Settings Prompt-omission exclusion set shrinks by one, a mechanical update that ADR already named). Decomposer pass (2026-08-17, /plan-tasks step 2): no MUST-FLAG trigger fired — all 6 ACs locked and tagged, all 3 tasks carry an acyclic depends_on chain, every locked AC has at least one AC-tagged verification step. See ## Notes for the full decomposer pass."
sprint: "SPRINT-054"
created: 2026-08-17
updated: 2026-08-17
---

# REQ-SB-67-US-01 — Real Per-Thread Summary Synthesis (live capture) + One-Shot Backfill for Already-Captured Threads

## Story

**As a** Second Brain user
**I want** a Thread note's own `## Summary` region to be a real,
Compass-synthesized abstract of that Thread's current state (not the
latest message's raw body pasted in verbatim), plus a one-line "current
state at a glance" sentence at the top of its body — for both newly
captured Threads AND the small number already sitting in my vault today
**So that** I can actually tell what a Thread is about at a glance,
instead of re-reading a raw email dump every time — the same "can't find
the current status of anything" pain `REQ-SB-54` was raised to fix, which
this one remaining raw-Summary gap still leaves unsolved for Threads
specifically

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-67: Real Per-Thread Summary
  Synthesis + Existing-Thread Backfill*.
- **Extends `REQ-SB-55-US-01`'s `Thread-Match/Merge` Job (`Done`),
  deliberately reopening one of its own documented Constraints** — "this
  Job never makes a second Compass call" — via a NEW story, per this
  project's own append-only-specs rule (`Implementation/Pipeline.md` hard
  rule 1); `REQ-SB-55-US-01` itself is never edited. This mirrors the
  established precedent `REQ-SB-65`/`REQ-SB-66` both already set for
  reopening a different Done story's own Constraint (`REQ-SB-41`'s
  "Jobs are non-addressable") the same way.
- **Confirmed this is NOT `REQ-SB-57`'s job.** `REQ-SB-57` (Project &
  Customer Status Synthesizer, `Draft`) synthesizes Project/Customer
  Glimpse documents ONE LEVEL ABOVE Threads, reading Thread evidence as
  input — it never rewrites a Thread's own `## Summary` region. Verified
  directly against `REQ-SB-57-US-01`'s own story text: it describes
  Glimpse regeneration for Project/Customer concept files only.
- **Operator directly confirmed, two `AskUserQuestion` rounds (per the
  PRD's own comment block):** (1) fix a Thread's own Summary now, as a
  small Threads-only extension, rather than waiting on `REQ-SB-57`; (2)
  backfill the already-captured real Thread notes in place, not just new
  ones going forward.
- **The exact call-site pattern to reuse — read directly, not
  guessed:** `app/business/email_classification.py::summarize_attachment`
  already calls `compass_client.summarize_content(extracted_text,
  source_description, prompt_override=agent_prompts.get_prompt(...))`
  and returns an honest `"summary_error"` key (never raises, never
  fabricates) when saved-but-unsummarizable or when
  `compass_client.CompassError` is raised. This story's new Thread-level
  synthesis call reuses `compass_client.summarize_content` directly —
  the same primitive, same `prompt_override` parameter (already present
  from `REQ-SB-66-US-01`'s own `T02` work) — never a second, divergent
  summarization call shape.
- **Fits inside the existing pipeline shape, does not bypass it.**
  `thread_match_merge` is a plain, `LangGraph`-ignorant Job function
  composed into `app/business/pipelines/email_capture_pipeline.py`'s
  `StateGraph` (`ADR-043`). The new Compass call lives inside
  `thread_match_merge` (or a function it calls) exactly where
  `_build_thread_summary_content` runs today — it does not need a new
  Job, a new graph node, or any change to the graph's own edges.
- **`REQ-SB-54` point 8 ("Regenerate, don't patch")** already governs
  how `## Summary` gets rewritten — `vault_writer.replace_body_section`
  (a real whole-region replace, never a patch) is the existing primitive
  `thread_match_merge` already calls for `## Summary`; this story changes
  WHAT content is generated to fill that call, not the write mechanism
  itself.
- **`REQ-SB-54` point 11 (one-line "current state at a glance" opening
  body sentence)** is explicitly listed by the PRD as applying to Thread
  notes too, but was never actually built for any note kind —
  confirmed directly: `REQ-SB-54-US-01`'s own story file makes no mention
  of an opening-line mechanism anywhere, and
  `vault_writer.create_thread_note_baseline`'s current body is exactly
  `"## Summary\n\n## Transcript\n"` — no line precedes `## Summary`
  today. This story is the first real implementation of point 11, scoped
  to Threads only (point 11's broader rollout to Meeting/Project/Customer
  concept files is not this story's scope).

### Two PRD-flagged open scope questions — resolved below, not left open

The PRD (`REQ-SB-67`'s own comment block) explicitly names two design
questions and defers them to `/spec`. Both are resolved here by direct,
repeated, uncontested existing codebase precedent (see `## Notes` for the
full reasoning) rather than by guessing between equally-valid options:

1. **Backfill trigger mechanism — resolved: a one-shot admin endpoint,
   not a lazy background catch-up job.** `app/api/email_poc_router.py`
   already hosts six real endpoints of exactly this shape for exactly
   this class of operation (`POST /poc/backfill-tags`, `/poc/
   flatten-customer-folders`, `/poc/retrofit-customer-hub-links`, `/poc/
   retrofit-people-from-emails`, `/poc/retrofit-email-sender-links`,
   `/poc/migrate-customer-to-partner`) — every one of them a business
   function returning a `list[dict]` of per-item outcomes, wrapped by a
   thin router endpoint that does light aggregation. This story's backfill
   follows the identical, already-established shape: a new business
   function (e.g. `backfill_thread_summaries()`) plus a new `POST /poc/
   backfill-thread-summaries` endpoint. No lazy/background catch-up
   mechanism exists anywhere in this codebase for any comparable
   operation — introducing one here would be a genuinely new pattern for
   a one-time, operator-triggered maintenance operation, not the
   established one.
2. **Cost/rate-limiting posture — resolved: sequential, one Compass call
   per Thread note found in the vault at run time, honest per-item
   failure handling, no hardcoded count.** The backfill discovers however
   many Thread notes actually exist under `Work/Threads/` at the moment
   it runs (never a fixed/assumed count) and processes them one at a
   time, mirroring `classify_recent_emails`'/`summarize_attachment`'s own
   established per-item try/except+continue posture (see Scenario 6
   below) — this naturally scales as the Thread count grows (today: 2)
   without any code change, and never fires concurrent/batched Compass
   calls that would need dedicated rate-limiting infrastructure this
   codebase has never needed before at this data volume.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: A live-captured Thread produces a genuinely Compass-synthesized Summary

```gherkin
Given a real Outlook conversation is being captured through the Email
    Capture Pipeline's Thread-Match/Merge Job
When a message in that conversation is merged into its Thread note
    (whether this is the first message or a later one)
Then the Thread's "## Summary" region is regenerated via a real Compass
    call grounded in that Thread's own accumulated transcript
  And the resulting Summary reads as a genuine synthesized abstract of the
    Thread's current state — not the latest message's raw, unprocessed
    body pasted in verbatim
```
<!-- AC-ID: REQ-SB-67-US-01-AC-01 -->

### Scenario 2: The Thread's body opens with a one-line "current state at a glance" sentence

```gherkin
Given a Thread note's body is regenerated by the Thread-Match/Merge Job
    (on first creation or on any later update)
When that regeneration completes
Then the first line of the Thread note's body is a single, regenerated
    sentence stating the Thread's current state at a glance
  And the rest of the body's existing structure ("## Summary",
    "## Transcript", "## Attachments" where present) follows immediately
    after that opening line, unchanged in shape
```
<!-- AC-ID: REQ-SB-67-US-01-AC-02 -->

### Scenario 3: The backfill regenerates Summary + opening line for existing Thread notes, in place, leaving everything else untouched

```gherkin
Given the vault already contains one or more Thread notes captured before
    this requirement shipped, each still carrying the old raw-message-dump
    "## Summary" content and no opening-line sentence
When the operator runs the backfill (POST /poc/backfill-thread-summaries)
Then each existing Thread note's "## Summary" region is regenerated with a
    real Compass-synthesized summary grounded in that Thread's own full
    transcript
  And a one-line opening sentence is added at the top of that Thread
    note's body
  And that Thread note's frontmatter, "## Transcript" region,
    "## Attachments" region, and tags are left completely unchanged by the
    backfill
```
<!-- AC-ID: REQ-SB-67-US-01-AC-03 -->

### Scenario 4: A Thread with only one message still produces a sensible summary

```gherkin
Given a Thread note has exactly one message in its transcript (a brand-new
    conversation with no reply yet)
When its Summary is generated — whether through live capture or through
    the backfill
Then Compass still produces a real, sensible synthesized summary grounded
    in that one message's own content
  And this is not treated as an error, left as an empty section, or
    silently fallen back to the old raw-dump behavior
```
<!-- AC-ID: REQ-SB-67-US-01-AC-04 -->

### Scenario 5: A Compass failure during live capture does not corrupt the Thread or crash the pipeline run

```gherkin
Given a message is being merged into a Thread note through the
    Thread-Match/Merge Job
When the Compass call to synthesize the Summary fails (e.g. a network
    error or an unparseable response)
Then the Thread note's existing "## Summary" content is left untouched —
    not blanked, not overwritten with an error, not corrupted
  And an honest, non-fabricated failure outcome is recorded for that
    message, mirroring summarize_attachment's own "summary_error"
    pattern, rather than a fabricated or partial summary being written
  And the rest of that pipeline run continues for other emails/Jobs — one
    failed synthesis does not crash or abort the run
```
<!-- AC-ID: REQ-SB-67-US-01-AC-05 -->

### Scenario 6: A Compass failure for one Thread during the backfill does not abort the whole backfill run

```gherkin
Given the backfill is processing multiple existing Thread notes
When the Compass call fails for one specific Thread note
Then that Thread note's existing "## Summary" content and opening line are
    left untouched — not blanked, not corrupted
  And an honest, non-fabricated failure outcome is recorded for that one
    Thread note
  And the backfill continues processing the remaining Thread notes rather
    than aborting the entire run
```
<!-- AC-ID: REQ-SB-67-US-01-AC-06 -->

## Affected Screens

None — backend only. No screen in `html-prototype/` renders a note's full
body content (`note-detail.html` renders frontmatter/tags/wikilink
graph only, per its own documented scope — REQ-SB-02-US-01, Scenario 3;
full note-body content stays an Obsidian-viewed surface, per this
project's own established convention). No new screen or screen region is
introduced by this story.

## Dependencies

- **Related to:** `REQ-SB-55-US-01` (Email Capture & Threading Pipeline,
  `Done`) — this story extends `thread_match_merge`/
  `_build_thread_summary_content` and deliberately supersedes that story's
  own "no second Compass call" Constraint, via a new story rather than an
  edit to the Done one (Pipeline.md hard rule 1).
- **Related to:** `REQ-SB-54-US-01` (Vault Knowledge Model Redesign,
  `Done`) — point 8's "regenerate, don't patch" mechanism
  (`replace_body_section`) and point 11's opening-line convention, both
  already established for the Thread note shape this story writes into.
- **Related to, NOT satisfied by:** `REQ-SB-57` (Project & Customer Status
  Synthesizer, `Draft`) — confirmed to never touch a Thread's own
  `## Summary`; still separately needed for Project/Customer Glimpse.
  This story does not reduce `REQ-SB-57`'s own remaining scope.
  `REQ-SB-58`/`REQ-SB-59` also remain unaffected — `REQ-SB-59`'s own
  future full wipe-and-recapture stays a separate, later, much larger
  operation than this story's narrow Summary/opening-line-only backfill.
- **Related to:** `REQ-SB-66-US-01` (Real, Editable Per-Agent/Job Prompt,
  `Done`) — the `prompt_override` parameter on
  `compass_client.summarize_content` this story's new call reuses
  directly already exists from that story's own `T02` work; whether/how
  this new call site gets its own Settings-editable prompt id is left to
  `/plan-tasks` (not itself part of this story's own Acceptance Criteria).
- **External:** the already-configured, real Compass Provider this
  project's other Compass call sites already depend on; the user's real,
  live Obsidian vault (`VAULT_PATH`) — Scenario 3's backfill and every
  other scenario's live-capture verification are not satisfiable via a
  mocked/simulated vault or a mocked Compass response.

## Constraints

- **Reuse `compass_client.summarize_content` directly** — the same
  primitive `summarize_attachment` already calls, including its existing
  `prompt_override` parameter; no second, divergent summarization call
  shape is invented for this story.
- **Fits inside the existing `Thread-Match/Merge` Job, inside the already
  existing LangGraph `StateGraph`** (`ADR-043`) — no new Job, no new graph
  node/edge, no bypass of the pipeline's existing assembly.
- **Backfill touches ONLY the Summary region and the opening-line
  sentence** of each already-existing Thread note — frontmatter,
  `## Transcript`, `## Attachments`, and tags must be left byte-for-byte
  unchanged (Scenario 3).
- **Regenerate, don't patch** (`REQ-SB-54` point 8) — both the Summary and
  the opening line are wholly regenerated via whole-region-replace
  semantics on every call, live capture and backfill alike, never
  incrementally patched or appended to.
- **A Compass failure must never blank/corrupt an existing Summary**, and
  must never crash the whole pipeline run (live capture, Scenario 5) or
  the whole backfill run (Scenario 6) — an honest, non-fabricating failure
  posture, mirroring `summarize_attachment`'s own `"summary_error"`
  pattern, not a new error-handling shape.
- **Still no SECOND, independent classification/routing call chain** —
  this story adds exactly the one new synthesis call `REQ-SB-67`'s own
  PRD text approves paying for; it does not reopen or duplicate
  `Classify`/`Route-to-Project`'s own existing Compass calls.
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).
- This work runs against the user's real, live Obsidian vault
  (`VAULT_PATH`) and the real, configured Compass Provider — Scenario 3's
  backfill must be verified against the real, already-captured
  `Work/Threads/*.md` notes, not a mocked/simulated vault.

## Implementation Tasks

<!-- Analyst-authored starting point, non-authoritative — the decomposer's
own table at /plan-tasks supersedes this. -->

<!-- Decomposer's own table (supersedes the analyst's draft above) — the
dependency order is real, not just presentational: T02's own Compass call
site writes the opening line via T01's new primitive, and T03's backfill
reuses T02's own shared synthesis helper directly, so the analyst's
original T01/T02 content is deliberately SWAPPED here (T01 = the
standalone vault_writer primitive with no dependency; T02 = the
integration task that actually wires the new Compass call) rather than
kept in the analyst's original order. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-67-US-01-T01 | backend | New `vault_writer.py` opening-line primitive (`replace_body_opening_line`) — mechanical generalization of `replace_body_section`, regenerates the body's opening region (between the frontmatter close and the first `## ` header) wholesale on every call | `app/data_access/vault_writer.py` | `../Tasks/REQ-SB-67-US-01-T01-thread-opening-line-primitive.md` |
| REQ-SB-67-US-01-T02 | backend | Real Compass-synthesized Summary + opening line for live capture — extend `thread_match_merge` with exactly ONE new `compass_client.summarize_content` call (rolling/incremental grounding, split into opening-line + Summary), retire `_build_thread_summary_content`, repoint `route_to_project`'s grounding to `vault_writer.read_body_section`, wire `agent_prompts.get_prompt("thread_match_merge")`, shrink `agents_router.py`'s `_JOBS_WITHOUT_REAL_PROMPT_CALL_SITE` by one entry | `app/business/email_classification.py`, `app/api/agents_router.py` | `../Tasks/REQ-SB-67-US-01-T02-real-thread-summary-synthesis.md` |
| REQ-SB-67-US-01-T03 | backend | One-shot backfill — new `app/business/thread_summary_backfill.py` + `POST /poc/backfill-thread-summaries` endpoint, sequential per-Thread regeneration of Summary + opening line (no delta, pure resynthesis), honest per-item failure handling; live verification against the vault's real, already-captured Thread notes | `app/business/thread_summary_backfill.py` (new), `app/api/email_poc_router.py` | `../Tasks/REQ-SB-67-US-01-T03-thread-summary-backfill.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists — manual verification mode until then, per this project's own standing convention)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **`REQ-SB-57`'s Project/Customer Glimpse synthesis** — this story only
  fixes a Thread's own Summary; it does not build the mechanism that keeps
  Project/Customer concept files current.
- **`REQ-SB-59`'s full vault migration/wipe-and-recapture** — this story's
  backfill is deliberately narrow (Summary + opening line only, in place);
  it is not a substitute for that future, much larger operation, and does
  not depend on `REQ-SB-56`/`57`/`58`.
- **Point 11's rollout to Meeting/Project/Customer concept files** — this
  story implements the opening-line convention for Thread notes only.
- **A persisted/scheduled background catch-up mechanism for the
  backfill** — resolved above to a one-shot admin endpoint instead; a
  background mechanism is not built by this story.
- **Reconciling multiple `ConversationID`s into one real Conversation**
  (`REQ-SB-54` point 10) — unrelated to and unaffected by this story.

## Notes

**Analyst pass, 2026-08-17 — `gate: clear`, no triggers fired:**

- **Trigger 1 (material assumption) — did not fire.** Both open scope
  questions the PRD names are resolved by directly reading existing,
  repeated, uncontested codebase precedent (`app/api/email_poc_router.py`'s
  six existing `/poc/...` one-off endpoints; `summarize_attachment`'s own
  per-item honest-failure posture), not by picking arbitrarily between
  unexplored options. See `## Context`'s "Two PRD-flagged open scope
  questions" subsection above for the full resolution and citations.
- **Trigger 2 (unfinalised requirement) — did not fire.** `REQ-SB-67` is
  not marked `<!-- Draft -->`/unfinalised in the PRD; `BACKLOG.md`'s own
  row for it read "Not yet specced — ready for `/spec`" before this pass,
  not "Draft/unfinalised."
- **Trigger 3 (ADR) — not applicable to the analyst.**
- **Trigger 4 (ESCALATIONS.md entry) — did not fire.** Nothing here
  contradicts an Accepted ADR, a `MEMORY.md` constraint, or the PRD; this
  story is an explicit, PRD-directed, in-scope extension of `REQ-SB-55`,
  not a backward/out-of-scope event.
- **Trigger 5 (oversized) — did not fire.** Three tasks, one Job
  extended in place, one new backfill endpoint — comparable in size to
  the `REQ-SB-65`/`REQ-SB-66` single-story precedent for a similarly-scoped
  extension of an already-`Done` pipeline.
- **Trigger 7 (contradictory inputs) — did not fire.** `REQ-SB-57`'s own
  story text was read directly and confirmed to never touch a Thread's
  own Summary — no contradiction between `REQ-SB-67`'s premise and
  `REQ-SB-57`'s actual scope.
- **Trigger 8 (multiple equally-valid options / genuinely unclear) — did
  not fire.** Both PRD-named open questions have one dominant, repeatedly
  established answer in this codebase (see above) — not two live,
  equally-weighted options being guessed between.
- `gate: clear 2026-08-17 — no triggers fired (requirement finalised in
  the PRD, both PRD-flagged open scope questions resolved via direct,
  repeated existing-code precedent rather than assumption, no ADR touched
  by this pass, no ESCALATIONS.md entry, normally-sized story, no
  contradictory inputs).`

**Prototype parity:** Not applicable — this story touches no screen in
`html-prototype/` (see `## Affected Screens` above); the Prototype
reconciliation subsection is only mandatory for screen-touching stories.

---

**Architect pass (2026-08-17) — `/plan-tasks` step 1:**

- **Architecture scope:** `Implementation/Architecture/architecture.md` →
  §"Real Thread Summary Synthesis + Opening-Line + One-Shot Backfill"
  (new subsection, appended directly after "Pipeline Job Tree
  Visualization", under "Email Capture & Threading Pipeline — First
  Concrete Pipeline") — covers the Job/node placement, the one-new-call
  shape and its Summary/opening-line split, the rolling-synthesis
  grounding strategy, `route_to_project`'s repointed grounding and
  `_build_thread_summary_content`'s retirement, the new opening-line
  `vault_writer.py` primitive, the `agent_prompts.py` config wiring, and
  the backfill module/endpoint shape. Plus, for context only (read, not
  modified by this story): §"Email Capture & Threading Pipeline — First
  Concrete Pipeline" (`REQ-SB-55`, `ADR-043` — the Job this story extends
  in place) and §"Universal Prompt Override + Guardrails Placeholder"
  (`REQ-SB-66`, `ADR-044` — the config mechanism this story's new call
  site plugs into). The coder is bounded by these sections for all three
  tasks.
- **Job/node placement — extends `thread_match_merge` in place, no new
  Job, no new graph node/edge.** Read `ADR-043` and
  `app/business/pipelines/email_capture_pipeline.py` directly before
  deciding: none of `ADR-043`'s own seven numbered Decision points assert
  "`thread_match_merge` never calls Compass" as an architectural rule —
  that was `REQ-SB-55-US-01`'s own story-level Constraint text only. The
  new synthesis call is business-rule content within the SAME Job's own
  single responsibility (regenerating a Thread note's own regions on every
  merge); it does not need its own node, its own edge, or a new Job
  identity, and `email_capture_pipeline.py`'s compiled graph topology is
  unchanged (`get_job_tree()` keeps returning the same six Jobs).
- **No new ADR.** Reversing `REQ-SB-55-US-01`'s own "no second Compass
  call" Constraint via a new story (Pipeline.md hard rule 1) narrows a
  story-level scoping decision, not any `Accepted` ADR's own Decision —
  mirrors `REQ-SB-56-US-01`'s own architect-pass reasoning for an
  analogous "is this a new boundary or a parameter/business-rule choice
  within an already-Accepted model" judgement call. The config-surface
  piece (wiring the new call's prompt through `agent_prompts.py`, and
  shrinking `ADR-044`'s own hand-maintained Prompt-omission exclusion set
  by one entry) is a mechanical application of `ADR-044`'s own mechanism
  and its own explicitly-anticipated Consequence, not a reopening of it.
  Trigger-3 does not fire from this pass; `gate` stays `clear`.
- **Operator standing constraint 1 (config, not hardcoded) — applied:**
  the new synthesis call's `prompt_override` routes through
  `agent_prompts.get_prompt("thread_match_merge")`
  (`app/business/agent_prompts.py`, `ADR-044`'s already-`Accepted`
  sibling-store), mirroring `summarize_attachment`'s own exact wiring —
  never a bare Python literal with no override path. No other new
  tunable value is warranted: the existing shared `content[:8000]` cap
  inside `compass_client.summarize_content` (pre-existing, shared by
  every caller) already bounds the synthesis input, so this story
  introduces no second, narrower length/token cap; the backfill discovers
  Thread notes dynamically at run time (no hardcoded count) and runs
  sequentially with no artificial delay (mirrors
  `classify_recent_emails`'/`summarize_attachment`'s own established
  no-rate-limit precedent), so no batch-size/rate-limit config is
  warranted either — both are structural absences of a knob, not
  hardcoded knobs needing config-ification. The `## Summary` section
  heading name itself stays structural, per the operator's own guidance,
  not a tunable.
- **Operator standing constraint 2 (API-first, no script workarounds) —
  confirmed sound:** the analyst-scoped `POST /poc/backfill-thread-
  summaries` in `app/api/email_poc_router.py` matches this codebase's own
  established six-endpoint `/poc/...` pattern exactly (confirmed by direct
  reading of all six), and respects the `api → business → data_access`
  layer boundary (`ADR-003`) — a thin router endpoint calling a new
  `app/business/thread_summary_backfill.py::backfill_thread_summaries()`
  business function, mirroring `tag_backfill.py`'s own shape. No
  standalone script is used or needed anywhere in this design.
- **A real, load-bearing finding this pass made, not assumed:**
  `## Transcript` (`vault_writer.append_body_section_line`) only ever
  accumulates a terse one-line `date — sender: subject` entry per
  message — it never carries a message's own body text anywhere, and this
  story's own Constraints forbid changing that shape. Since no full,
  multi-message raw-body history persists anywhere in this data model, the
  new synthesis call is grounded as a ROLLING/INCREMENTAL synthesis (prior
  `## Summary` + full `## Transcript` + the new message's own body as the
  delta on live capture; no delta on backfill), not a full-history
  reconstruction — see the architecture section for the full reasoning.
  This also means `route_to_project`'s own `guess_project_for_thread`
  grounding is repointed to read the just-written real Summary
  (`vault_writer.read_body_section`) instead of recomputing a second,
  divergent summary of the same message, and `_build_thread_summary_
  content` (its only two callers, both replaced) becomes dead code to be
  retired — flagging this explicitly for the decomposer's own task
  scoping, since neither Scenario names this function by name.
- `gate: clear 2026-08-17 — no MUST-FLAG trigger fired (no ADR
  created/changed; both extended-mechanism decisions — thread_match_merge's
  new call, agent_prompts.py wiring — are parameter/business-rule choices
  within already-Accepted ADR-043/ADR-044; no ESCALATIONS.md entry; no
  contradiction with any Accepted ADR, PRD text, or MEMORY.md constraint).`
  No `REVIEW-QUEUE.md` entry written by this pass.

---

**Decomposer pass (2026-08-17) — `/plan-tasks` step 2:**

- **All 6 Scenarios locked as-is, tightened by nothing more than the
  trailing AC-ID tag.** Read every Scenario directly against
  `architecture.md`'s new subsection before locking: each already reads as
  a buildable, observable-outcome assertion (a real Compass call fired; a
  specific region's own content/shape; an honest non-fabricating failure
  record) with no ambiguous verb needing rewording. `REQ-SB-67-US-01-AC-01`
  through `REQ-SB-67-US-01-AC-06` assigned in Scenario order, all
  **locked** (no `locked: false` tag on any — every one has a real,
  verifiable observable outcome, see per-AC verification mapping below).
- **Task order deliberately SWAPPED from the analyst's own draft table.**
  The analyst's `T01` (the Compass-call task) and `T02` (the opening-line
  primitive) are reordered here: the real dependency runs the other way —
  `thread_match_merge`'s own new Compass call (analyst's `T01`) WRITES the
  opening line through the new `vault_writer.py` primitive (analyst's
  `T02`), so the primitive has to exist first. Renamed to
  `REQ-SB-67-US-01-T01` = the standalone primitive (zero dependencies) and
  `REQ-SB-67-US-01-T02` = the integration task that actually wires the new
  Compass call (`depends_on: [T01]`); `REQ-SB-67-US-01-T03` = the backfill,
  `depends_on: [T02]` since it reuses `T02`'s own shared synthesis helper
  directly (mirrors this codebase's own repeated "generic-primitive-first"
  precedent, `Implementation/Learnings.md` `SPRINT-048`). Acyclic,
  strictly linear chain — no diamond, no fan-in.
- **AC → task verification mapping (every locked AC has ≥1 AC-tagged
  step):**
  - `AC-01` (Scenario 1, live-capture real synthesis) — `T02`.
  - `AC-02` (Scenario 2, opening line) — `T02` (the integration task; the
    Scenario's own Given clause is "a Thread note's body is regenerated by
    the Thread-Match/Merge Job", an observable outcome that does not exist
    until `T02`'s own wiring lands — `T01`'s own Tests verify the raw
    primitive mechanically, un-tagged, since Scenario 2 is about the
    Job's own behaviour, not the primitive in isolation).
  - `AC-03` (Scenario 3, backfill in place) — `T03`.
  - `AC-04` (Scenario 4, single-message Thread) — tagged in BOTH `T02`
    (live-capture path) and `T03` (backfill path), since the Scenario's
    own wording explicitly covers "whether through live capture or
    through the backfill" as one Scenario covering two real call paths.
  - `AC-05` (Scenario 5, Compass failure during live capture) — `T02`.
  - `AC-06` (Scenario 6, Compass failure during backfill) — `T03`.
- **The `_JOBS_WITHOUT_REAL_PROMPT_CALL_SITE` mechanical follow-on
  (architect-flagged, not a locked AC of its own) is covered by `T02`** —
  the same task that wires `thread_match_merge`'s own new Compass call
  site also shrinks `app/api/agents_router.py`'s exclusion set from
  `{"thread_match_merge", "detect_recurring_pattern"}` to
  `{"detect_recurring_pattern"}`, with its own (non-AC-tagged, since no
  Gherkin Scenario in this story names the Job-Settings UI) verification
  step in `T02`'s own `## Tests`.
- **Trigger 1 (material assumption) — did not fire.** Every concrete
  naming/shape decision the architect left open ("naming left to the
  decomposer") is a mechanical, single-obvious-answer choice made directly
  from the architecture section's own explicit guidance (e.g. the shared
  synthesis helper's own parameter shape, the primitive's own boundary
  logic mirroring `replace_body_section`'s exact pattern) — not a gap
  filled by guessing.
- **Trigger 2 (unfinalised requirement) — did not fire.** Unchanged from
  the analyst/architect passes.
- **Trigger 3 (ADR) — did not fire.** No ADR touched by this pass; carries
  forward the architect's own "no new ADR" finding.
- **Trigger 4 (`ESCALATIONS.md` entry) — did not fire.** Nothing here
  contradicts an `Accepted` ADR, the PRD, or a `MEMORY.md` constraint.
- **Trigger 5 (oversized) — did not fire.** 3 tasks, one linear
  `depends_on` chain, matching the parent story's own architect-confirmed
  sizing.
- **Trigger 6 (a locked AC cannot be verified) — did not fire.** All 6
  ACs have a real, directly observable outcome (specific file-region
  content/shape; a specific field present/absent in a return dict; a
  specific vault region's byte-for-byte non-change) — none needed a
  `locked: false` tag.
- **Trigger 7 (contradictory inputs) — did not fire.**
- **Trigger 8 (multiple equally-valid options / genuinely unclear) — did
  not fire.** The one real design choice this pass made (the task-order
  swap above) has one dominant, mechanically-derived answer from the
  real dependency direction, not two live options being guessed between.
- `gate: clear 2026-08-17 — no MUST-FLAG trigger fired (no ADR
  created/changed by this pass; no material assumption — every open
  naming choice had one mechanical answer from the architecture section;
  no ESCALATIONS.md entry; all 6 locked ACs individually verifiable; no
  contradictory inputs; normally-sized, acyclic 3-task depends_on chain).`
  No `REVIEW-QUEUE.md` entry written by this pass. **Story advances
  `Draft` → `Ready`; all 3 tasks written at `status: Ready` in lockstep.**

---

**Coder pass (2026-08-17) — `T03` (the last remaining task) verified and
marked `Done`:** all 6 locked ACs (`AC-01` through `AC-06`) now verified —
`AC-01`/`AC-02`/`AC-04`(live-capture half)/`AC-05` by `T02`;
`AC-03`/`AC-04`(backfill half)/`AC-06` by `T03`. All 3 tasks `Done`.
Story `status` set to `Done`. See `T03`'s own `## Implementation Log`
(`Implementation/Tasks/REQ-SB-67-US-01-T03-thread-summary-backfill.md`)
for the full scratch-vault + real-vault verification evidence, including
the real, live one-time backfill run the operator explicitly asked for
against the actual `VAULT_PATH` vault's 2 real pre-existing Thread notes.
`BACKLOG.md`'s `REQ-SB-67` row updated to `Done`. `SPRINT-054` (this
story's only sprint) set to `status: Done` with a drafted `##
Retrospective`, `gate: flagged` for human harvest into
`Implementation/Learnings.md`.
