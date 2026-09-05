---
id: REQ-SB-55-US-01-T08
title: Retire email-capture; register email-capture-pipeline Agent-tier identity across every real referencing file; full live end-to-end verification
parent_story: REQ-SB-55-US-01
requirement_id: REQ-SB-55
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-043 created) — carried from the parent story; the human reviews ADR-043 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: [REQ-SB-55-US-01-T07]
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-55-US-01-T08 — Retire `email-capture`; register `email-capture-pipeline`

## Parent Story

- Story: [[REQ-SB-55-US-01]] — `../UserStories/REQ-SB-55-US-01-email-capture-and-threading-pipeline.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-55 *Email Capture & Threading Pipeline*

---

## Objective

Replace the `email-capture` Agent-tier identity with ONE new identity, `email-capture-pipeline` (`type: "worker"`, matching the retired entry's own type per `ADR-043` point 6), across every real file that references the literal `"email-capture"` id — confirmed by direct search this pass: `agent_registry.py`, `background_agent_registry.py`, `skill_tools.py`, `skill_registry.py`, `agents_router.py`, `email_classification.py` itself. Rewire `run_capture_for_agent`/`run_capture_and_record_completion` to dispatch the new agent_id to `T07`'s `email_capture_pipeline.run_email_capture_pipeline` instead of the old `classify_recent_emails`. Then run this story's own mandatory real, live Outlook-backed end-to-end verification (`AC-09`).

---

## Starting State → End State

**Before / Inputs:**
- `agent_registry.py`'s `_SEED_AGENTS["email-capture"]` — the old Worker entry (Schedule/Vault target/Classifier settings, `run_capture_now`/`view_last_run`/`pause_schedule` actions).
- `background_agent_registry.py`'s `_DEFAULT_BACKGROUND_AGENT_IDS = {"email-capture", "meeting-capture", "todo-capture"}`.
- `skill_tools.py`'s `run_capture_now` MCP-tool handler: `if agent_id == "email-capture": ...`.
- `skill_registry.py`'s three grant lists (`view_last_run`/`run_capture_now`/`pause_schedule`) each including `"email-capture"`.
- `agents_router.py`'s `_ACTION_HANDLERS = {("email-capture", "run_capture_now"): run_capture_and_record_completion, ...}`.
- `email_classification.py`'s `run_capture_for_agent`'s `if agent_id == "email-capture": return classify_recent_emails(limit=limit)` branch, and `run_capture_and_record_completion`'s own multiple `"email-capture"` string uses (working-mode gate, history entries, pending-approval creation).
- `demo_taxonomy.py`'s `_DEMO_PIPELINES[0]["id"] == "pipeline-email-capture"` — an in-memory, disconnected demo fixture for the (not-yet-built) Pipeline Builder UI, unrelated to `agent_registry`'s own real registry.

**After / Outputs:**
- `agent_registry.py`'s `_SEED_AGENTS` has NO `"email-capture"` key — instead, `"email-capture-pipeline"` (`type: "worker"`), with settings/actions text updated to describe the real Pipeline shape (e.g. `run_capture_now` still the one real handler; settings reflecting the Fetch→Classify→Thread-Match/Merge→Route-to-Project chain plus the two branch Jobs, rather than the old single-stage description).
- `background_agent_registry.py`'s default set includes `"email-capture-pipeline"` in place of `"email-capture"`.
- `skill_tools.py`'s `run_capture_now` handler checks `agent_id == "email-capture-pipeline"`, calling `email_classification.run_capture_and_record_completion()` (unchanged call site — that function's OWN internals are what changed, per below).
- `skill_registry.py`'s three grant lists reference `"email-capture-pipeline"` in place of `"email-capture"`.
- `agents_router.py`'s `_ACTION_HANDLERS` key becomes `("email-capture-pipeline", "run_capture_now")`.
- `email_classification.py`'s `run_capture_for_agent` dispatches `"email-capture-pipeline"` to `pipelines.email_capture_pipeline.run_email_capture_pipeline(limit=limit)` (not the old `classify_recent_emails`); `run_capture_and_record_completion`'s own working-mode gate, history entries, and pending-approval creation all reference `"email-capture-pipeline"`.
- `GET /agents` (and every other real agent-listing surface — Agents Map, Cockpit bring-in list, Schedule tab, background-agent rail) shows `email-capture-pipeline`, never `email-capture` (`AC-08`).
- A real, live scheduled or manually-triggered capture run correctly produces real Thread notes/attachment sub-entries/Pending Approvals (`AC-09`).

---

## Files to Modify

- `src/backend/app/business/agent_registry.py`
- `src/backend/app/business/background_agent_registry.py`
- `src/backend/app/business/skill_tools.py`
- `src/backend/app/business/skill_registry.py`
- `src/backend/app/api/agents_router.py`
- `src/backend/app/business/email_classification.py`
- `src/backend/app/business/demo_taxonomy.py` — reconcile (rename the coincidentally-matching `"pipeline-email-capture"` id/description to avoid reader confusion) OR leave as an explicitly-disconnected demo fixture — coder's own judgement call (this file has zero real behavioral coupling to `agent_registry.py`), log the choice taken in the Implementation Log; not locked-AC-bearing either way.

---

## Constraints

- Inherits from parent story: **`email-capture` must no longer appear as its own agent anywhere** once this task is complete (`AC-08`, Scenario 8's own literal wording) — this means the STRING `"email-capture"` must stop resolving as a real `agent_id` in `agent_registry.get_agent`/`list_agents`, not merely have its settings text rewritten in place under the same id.
- `email-capture-pipeline`'s own `type` must be `"worker"` — matching the retired entry's own type so every existing type-keyed piece of code (ring placement, Section coloring, `background_agent_registry.py`'s own literal exception set) needs zero further changes beyond the literal id-string swap (`ADR-043` point 6).
- None of the six Jobs (`Fetch`/`Classify`/`Thread-Match/Merge`/`Route-to-Project`/`Summarize-Attachment`/`Detect-Recurring-Pattern`) get their own `agent_registry` entry, Map node, chat surface, or Working Mode — only ONE new identity is added, replacing the old one 1:1.
- `run_capture_and_record_completion`'s own overall CONTRACT must be preserved: still returns the capture-results list (empty when the agent's own mode is non-Autonomous or on a caught failure), still writes exactly one `run_event`/`run_error`/`proposal` history entry per tick per this Constraint's own existing shape — only the agent_id string and the underlying function called change, not the surrounding gating/history/error-handling logic (`meeting-capture`/`todo-capture`'s own branches in the SAME function are untouched).
- `classify_recent_emails`, `record_conversation_note`/`conversation_index.json`/`find_related_note_stems`/`## Related Emails` become dead code for the email path once this task lands (a `conversation_id`-scoped Thread already IS "the related emails, merged") — `ADR-043` deliberately does NOT mandate deleting them; deleting cleanly (confirming no other real caller remains) vs. leaving them as clearly-marked dead code is this task's own coder judgement call — log the choice, not a locked-AC requirement either way.
- Any already-persisted `.second-brain/` state keyed by the literal string `"email-capture"` (schedules, working-mode overrides, background-agent flags, agent history) is NOT migrated by this task — a fresh/reset dev vault picks up the new id's own self-healing defaults; a real production vault carrying old `"email-capture"`-keyed state is a disclosed, out-of-scope migration concern (log if encountered, not a locked-AC gap — no Scenario in this story tests state migration).
- Do not touch `meeting-capture`/`todo-capture`'s own branches/settings anywhere in any of the files above.

---

## Tests

**Manual verification steps:**
1. **[REQ-SB-55-US-01-AC-08]** Query `GET /agents` (or `agent_registry.list_agents()` directly) — confirm `email-capture` does NOT appear anywhere in the result, and `email-capture-pipeline` DOES, with `type: "worker"`. Confirm `agent_registry.get_agent("email-capture")` returns `None`.
2. Confirm `BACKLOG.md`'s own `REQ-SB-53` row already marks `REQ-SB-53-US-01` superseded (per the parent story's own Context — this was set at `/spec` time, not this task's own job to add; if for any reason it is missing, add the one-line marker here and log it as a scope-internal judgement call, not a new material assumption).
3. Confirm `email-capture-pipeline` correctly renders on every real existing surface with ZERO new code beyond the id-string swap: the Agents Map (main ring, Worker-type coloring), the Schedule tab (`REQ-SB-47`), the background-agent rail (`REQ-SB-51`, since it inherits the default background-agent set), Cockpit's bring-in list exclusion (still background-excluded, same as the old id was).
4. **[REQ-SB-55-US-01-AC-09]** Against the real, live Outlook desktop and the real, configured `VAULT_PATH` (never a mocked/simulated pipeline): trigger a real capture run — either the real scheduled tick or `POST /agents/email-capture-pipeline/actions/run_capture_now` (or the equivalent real dispatch path) — over real, genuinely new email in the real mailbox. Confirm the resulting Thread note(s) reflect real captured content correctly (real `## Summary`/`## Transcript`, real `customer`/`tags`/`participants`/`last_message_at`), any real attachment produces a real dated `## Attachments` sub-entry, and any real Pending Approval(s) created (`route_thread_to_project` and/or `propose_recurring_pipeline`, if a real email happens to trigger either) carry real, correctly-derived payloads — not fabricated or simulated data at any point.
5. Regression check: confirm `meeting-capture`/`todo-capture`'s own real scheduled/on-demand behavior is completely unaffected (byte-for-byte unchanged code paths) by this task's edits to the SHARED `run_capture_and_record_completion` function.
6. Regression check: confirm no other real file in `src/backend/app` still references the literal string `"email-capture"` after this task (a full-tree search comes back empty, excluding historical/comment-only mentions in already-`Done` task files' own Implementation Logs, which are append-only and never edited).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-08** (Scenario 8) — `email-capture` no longer appears as its own agent anywhere; `email-capture-pipeline` fully replaces it.
- [x] **AC-09** (Scenario 9) — a real, live Outlook-backed capture run produces correct, real (never mocked/simulated) Thread notes, attachment sub-entries, and Pending Approvals.
- [x] Every real file referencing the literal `"email-capture"` string has been updated; a full-tree search confirms none remain (see Implementation Log for the one, comment-only, out-of-scope exception found in `agent_schedule_registry.py`).
- [x] `meeting-capture`/`todo-capture`'s own behavior is unaffected.
- [x] `MEMORY.md` updated with this story's own new decision/pattern (the new Pipeline module shape, the two new Pending-Approval kinds, the new Agent-tier identity)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Migrating any already-persisted `.second-brain/` state keyed by the old `"email-capture"` id (schedules, working-mode overrides, background-agent flags, history) — disclosed, out-of-scope (see Constraints).
- Building the Pipeline Builder itself (`ADR-041` point 6) — stays deferred, per `ADR-043`'s own Consequences.
- `REQ-SB-56`/`REQ-SB-57`/`REQ-SB-63`'s own future work (Meeting→Thread linking, Glimpse synthesis, the Librarian's consult call) — this task only leaves `Thread-Match/Merge`/`Route-to-Project` cleanly consultable, per the parent story's own Notes; it does not build any of that integration itself.

---

## Context / Notes

Full reasoning: `Implementation/Architecture/ADR.md` → `ADR-043` point 6 and its own Consequences ("every real `email-capture`-referencing file this retirement touches, confirmed by direct search this pass"); `Implementation/Architecture/architecture.md` → "Email Capture & Threading Pipeline — First Concrete Pipeline". This is expected to be the heaviest task in this story by real verification effort, not code volume — most of the file edits are small, mechanical id-string swaps; `AC-09`'s own real, live, unbounded-latency Outlook-backed capture run is the genuine cost center, per this project's own repeated Learnings precedent for "unbounded real-pipeline invocation" sizing risk (`SPRINT-031`).

**On `MEMORY.md`:** this is the story's own FINAL task — the coder should write the story-level `MEMORY.md` entry here (once every task above is `Done` and every locked AC verified live), following this codebase's own established per-story entry convention (see e.g. the `REQ-SB-54-US-01` entry), not a task-scoped entry alone.

---

## Implementation Log

**2026-08-16, coder pass.**

Seven files edited, exactly as scoped under `## Files to Modify`:

- `src/backend/app/business/agent_registry.py` — `_SEED_AGENTS["email-capture"]`
  removed; `_SEED_AGENTS["email-capture-pipeline"]` added in its place
  (same dict position), `type: "worker"` unchanged, same three real
  Action ids (`run_capture_now`/`view_last_run`/`pause_schedule`,
  identical `trigger_phrases`/`mutates` values — `ADR-043` point 6's own
  "matching the retired entry's own type" plus this task's own
  Constraint that zero type-keyed code needs further changes). Settings
  text rewritten to describe the real Pipeline shape (`Job chain`,
  `Branch Jobs` rows added; `Vault target` corrected to `Work/Threads/`;
  `Purpose` rewritten) rather than the old single-stage "classify + file"
  description. Module docstring and `create_agent`'s own illustrative-id
  comment updated for consistency (prose only, no behavior change).
- `src/backend/app/business/background_agent_registry.py` —
  `_DEFAULT_BACKGROUND_AGENT_IDS` swapped `"email-capture"` →
  `"email-capture-pipeline"`. Live-verified (see below) that the
  self-healing default correctly assigns the new id `True`.
- `src/backend/app/business/skill_tools.py` — `run_capture_now`'s
  `if agent_id == "email-capture":` branch condition changed to
  `"email-capture-pipeline"`; the docstring's own real/honest-unavailable
  explanation updated to match. The call site inside the branch
  (`email_classification.run_capture_and_record_completion()`) is
  unchanged — that function's own internals are what changed, per the
  task's own End-State contract.
- `src/backend/app/business/skill_registry.py` — `_MIGRATION_GRANT_SEED`'s
  three lists (`view_last_run`/`run_capture_now`/`pause_schedule`) each
  had `"email-capture"` swapped for `"email-capture-pipeline"`; a comment
  line added noting this is the same historical seed, retargeted onto
  the same real agent's new identity, not a new migration concern.
- `src/backend/app/api/agents_router.py` — `_ACTION_HANDLERS` key changed
  from `("email-capture", "run_capture_now")` to
  `("email-capture-pipeline", "run_capture_now")`; the preceding comment
  updated to match.
- `src/backend/app/business/email_classification.py` —
  `run_capture_for_agent`'s dispatch branch changed from
  `if agent_id == "email-capture": return classify_recent_emails(limit=limit)`
  to `if agent_id == "email-capture-pipeline":` dispatching to
  `pipelines.email_capture_pipeline.run_email_capture_pipeline(limit=limit)`.
  The import is deliberately INSIDE this branch, not at module top level —
  `app/business/pipelines/email_capture_pipeline.py` imports five plain
  Job functions FROM this module at ITS OWN top level (`T07`), so a
  module-level import here would complete a real circular import
  (`email_classification` → `pipelines.email_capture_pipeline` →
  `email_classification`); mirrors `skill_tools.py`'s own already-
  established `build_knowledge`/`propose_person_note_update` deferred-
  import precedent for the identical reason. Confirmed live (below) this
  resolves cleanly with zero import error. `run_capture_and_record_
  completion`'s own `"email-capture"` agent_id string uses (the working-
  mode read, the `run_capture_for_agent` call, both history-entry agent_id
  arguments in the Autonomous branch, the pending-approval `agent_id` and
  history-entry agent_id in the Supervised branch) all swapped to
  `"email-capture-pipeline"` — the surrounding gating/history/error-
  handling control flow is byte-for-byte unchanged, only the id string
  and (via `run_capture_for_agent`) the underlying dispatched function
  changed, per this task's own Constraint. The Supervised-branch pending-
  approval `description` text was reworded from "the scheduled
  email-capture step" to "the scheduled email capture pipeline" (no
  hyphen) — purely to avoid a stray literal-string match on the retired
  `"email-capture"` id in a user-facing description sentence; the
  `meeting-capture`/`todo-capture` sibling branches in the SAME function
  were not touched (their own description text keeps the exact same
  hyphenated wording as before, per this task's own Constraint forbidding
  any change to those two branches). Docstrings updated to match
  throughout (prose only).

  `classify_recent_emails` is now dead code for the email-capture-
  pipeline path (`run_capture_for_agent` no longer calls it) — per this
  task's own Constraint, NOT deleted: `app/api/email_poc_router.py`
  (outside this task's own `## Files to Modify`) still calls it directly
  as its own standalone `/poc/classify-emails` manual endpoint, a real
  remaining caller. Left in place with a new comment marking it dead for
  the scheduled/on-demand email-capture-pipeline path specifically and
  explaining why (the Thread-Match/Merge Job already IS "the related
  emails, merged"), rather than silently orphaned. `record_conversation_
  note`/`find_related_note_stems`/`conversation_index.json`/the
  `## Related Emails` body region are untouched for the same reason
  (still exercised by `classify_recent_emails`' own real remaining
  caller) — not deleted, not marked, since they are `vault_writer.py`
  primitives outside this task's own Files to Modify.

- `src/backend/app/business/demo_taxonomy.py` — reconciled (chosen over
  leaving as-is): renamed the coincidentally-matching demo-fixture id
  `"pipeline-email-capture"` → `"pipeline-inbound-email-demo"`
  (`name` also reworded to "Inbound Email Pipeline (Demo)"), with a new
  comment explaining the rename and confirming this fixture never had
  any real coupling to `agent_registry.py`'s own retired id. Chosen
  because it was a small, low-risk edit already explicitly sanctioned by
  this task's own `## Files to Modify` entry, and it lets the full-tree
  "no literal `email-capture` string remains outside comments" regression
  check (Test step 6) come back clean rather than needing a documented
  exception for this file too. No other line in this file touched — the
  bulk-generated 150-entity sample set and every other hand-authored
  entry are unaffected.

**One real, out-of-scope finding, logged for human spot-check (not an
escalation — a documentation-only leftover, not a functional identity
leak):** `src/backend/app/business/agent_schedule_registry.py` (NOT in
this task's own `## Files to Modify` — confirmed by direct reading it is
absent from that list) contains two comment-only, historical-reasoning
mentions of the literal string `"email-capture"` inside `_record_outcome`'s
own docstring (explaining a past live-discovered self-recording-history
quirk, using the old id as its illustrative example). This file's own
real dispatch logic is fully generic over `agent_id`/`capability_id` (no
hardcoded `"email-capture"` anywhere in actual code, only in prose) — the
rename does not break anything there. Left untouched per this task's own
scope boundary (Forbidden: "Touching any file not in the task's Files to
Modify"); the decomposer's own "confirmed by direct search this pass"
enumeration of `## Files to Modify` did not include this file, and this
task's own regression-check wording (Test step 6, `## Acceptance
Criteria`'s third bullet) is satisfied for every file this task IS scoped
to touch — this one comment-only exception is disclosed here rather than
silently left unmentioned.

**Verification — manual mode, mix of scratch-vault checks and the
mandatory REAL live run:**

1. **[`REQ-SB-55-US-01-AC-08`]** Ran `agent_registry.get_agent("email-capture")`
   directly — returned `None`. Ran `agent_registry.get_agent(
   "email-capture-pipeline")` — returned the real entry, `type ==
   "worker"`. Ran `agent_registry.list_agents()` — confirmed
   `"email-capture"` is NOT present in the id set and `"email-capture-
   pipeline"` IS (`['compass-expert', 'email-capture-pipeline',
   'meeting-capture', 'people-producer', 'todo-capture',
   'vault-filing-expert', 'vault-qa']` — still exactly 7 shipped agents).
   Ran `app.api.agents_router.list_agents()` (the real `GET /agents`
   handler function, called directly) against a scratch vault — same id
   set, plus confirmed `is_background_agent` reads `True` for
   `"email-capture-pipeline"` (the self-healing default correctly picked
   up the new id). Confirmed `agents_router._ACTION_HANDLERS` keys are
   `[("email-capture-pipeline", "run_capture_now"), ("compass-expert",
   "build_knowledge")]`. Confirmed `skill_registry.list_agent_skills(
   "email-capture-pipeline")` returns the 3 migrated ids
   (`pause_schedule`/`run_capture_now`/`view_last_run`) via the
   retargeted migration seed, and `skill_registry.list_agent_skills(
   "email-capture")` returns `[]` (unknown agent, no skills). Confirmed
   the Agents Map/Schedule tab/Cockpit bring-in list/background-agent
   rail need zero new code — direct `grep` of `src/frontend` for the
   literal string `"email-capture"` returned zero matches (already
   agent-count-agnostic, per the parent story's own established
   `REQ-SB-53-US-01` precedent, reconfirmed here). **PASS.**
2. Confirmed `BACKLOG.md`'s `REQ-SB-53` row already marks
   `REQ-SB-53-US-01` superseded ("Parked — Email (US-01) ... superseded
   by `REQ-SB-55`/`REQ-SB-56` below") — set at `/spec` time, nothing to
   add here. **PASS (pre-existing).**
3. Full-tree `grep` of `src/backend/app` for the exact quoted string
   `"email-capture"` (not `"email-capture-pipeline"`) after every edit
   above returned exactly 5 matches, ALL inside comments/docstrings this
   task itself wrote to explain the rename (`agent_registry.py`,
   `email_classification.py`, `agents_router.py`, `demo_taxonomy.py`,
   `skill_registry.py`) — zero remaining in any functional
   dict-key/string-comparison/function-argument position. The one
   real exception outside this task's own scope
   (`agent_schedule_registry.py`, comment-only) is disclosed above.
   **PASS.**
4. Regression: `email_classification.run_capture_for_agent("meeting-capture")`
   and `("todo-capture")` (both classification functions monkeypatched to
   return `[]` for speed) still dispatch correctly; `run_capture_for_agent(
   "email-capture")` (the retired id) now raises `ValueError` — the exact
   same "no background capture step for this agent_id" behavior any other
   unrecognized string already produced, not a new/different failure mode.
   **PASS.**
5. **[`REQ-SB-55-US-01-AC-09`, the mandatory real, live run]** Confirmed
   real Outlook COM reachable (`outlook_com.list_recent_mail(limit=3)`
   returned real, current inbox items). Confirmed the real, configured
   `VAULT_PATH` (`<OPERATOR_VAULT_OLD>`) exists and was used
   UNMODIFIED (no scratch-vault override for this one step, per this
   story's own Constraint that `AC-09` is not satisfiable via a
   mocked/simulated pipeline). Confirmed exactly 1 genuinely new
   (not-already-processed) email existed in the real inbox before the
   run (`"Re: Presight Agent Academy Demo"`, from
   `aleksandr.sofronov@presight.ai`, 0 attachments) — a small, bounded,
   real live-verification run. Ran `email_classification.
   run_capture_and_record_completion(limit=15)` for real (no
   monkeypatching anywhere in this call) — completed in ~110s. Real
   result: `{'subject': 'Re: Presight Agent Academy Demo', 'customer':
   'Presight', 'thread_path': '...\\Work\\Threads\\
   01D26A7530444A23803A002210620160.md', 'created': True, 'attachments':
   0}`. Read the real, written Thread note directly off disk — real
   frontmatter (`type: "Thread"`, `conversation_id`, `tags:
   ["customer/presight", "kind/emails"]`, `customer: "Presight"`,
   `participants: ["aleksandr.sofronov@presight.ai"]`, `last_message_at`
   matching the real message timestamp), real `## Summary` (the real
   latest message's own body, not fabricated), real `## Transcript` (one
   real dated entry). No `## Attachments` region — correct, this email
   genuinely had none (mirrors `T03`'s own documented "never created
   empty" contract). Read `pending_approval_registry.
   list_pending_approvals(status="pending")` directly — confirmed exactly
   ONE new record created by this run (`action_id ==
   "route_thread_to_project"`, `agent_id == "email-capture-pipeline"`,
   `trigger == "direct"`, real payload: `customer: "Presight"`,
   `guessed_project: "Presight Agent Academy Demo"`, `is_new_project:
   True` — genuinely derived, since Presight had zero currently-open
   Projects; the other 2 pending records present in the real store are
   pre-existing, unrelated `meeting-capture` records dated `2026-08-14`,
   confirmed by their own `created_at` to predate this task entirely).
   Confirmed `email-capture-pipeline`'s own real agent history recorded
   a new `run_event` (`"Capture run completed — 1 email(s) filed"`) at
   the real run's own timestamp; confirmed the retired `"email-capture"`
   id's own history file is untouched (still its old length — this run
   never wrote to it). Confirmed, in the SAME real run,
   `meeting-capture`/`todo-capture` both completed their own real,
   Autonomous-mode captures normally (`meeting-capture`: 37 meetings
   filed; `todo-capture`: 100 tasks filed) and recorded their own real
   `run_event` history entries — their own branches are unaffected by
   this task's edits. **PASS — a real, live, non-mocked, non-simulated
   Outlook-backed capture run produced a correct, real Thread note and a
   correct, real, genuinely-derived Pending Approval, exactly as
   `AC-09`/Scenario 9 requires.**

**Acceptance criteria verified:**

- **AC-08** (Scenario 8) — **Verified**, step 1.
- **AC-09** (Scenario 9) — **Verified**, step 5 (the mandatory real,
  live Outlook-backed run, against the real configured mailbox and
  vault, no mocking).
- Every real file referencing the literal `"email-capture"` string has
  been updated — **Verified**, step 3 (one disclosed, out-of-scope,
  comment-only exception noted above).
- `meeting-capture`/`todo-capture` unaffected — **Verified**, steps 4
  and 5.

No `ESCALATIONS.md` entry — nothing in this pass contradicts an
`Accepted` ADR, the PRD, or a `MEMORY.md` constraint; the `demo_taxonomy.py`
reconciliation choice and the `agent_schedule_registry.py` comment-only
finding are both scope-internal judgement calls / disclosures the task
file itself anticipated, logged inline for human spot-check per this
task's own already-standing `gate: flagged` (trigger-3, `ADR-043`). No
new `REVIEW-QUEUE.md` entry either — this task's already-flagged gate,
inherited from the parent story's `ADR-043` review, already carries this
pass into the existing human-review flag; this is also the story's own
FINAL task, so the story-level `MEMORY.md` entry is written below per
this task's own Context/Notes instruction.
