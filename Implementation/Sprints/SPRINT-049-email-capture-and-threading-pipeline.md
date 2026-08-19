---
id: SPRINT-049
title: Email Capture & Threading Pipeline — Fetch/Classify/Thread-Match-Merge/Route-to-Project, attachment summarization, recurring-pattern detection
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "retro-harvest (this closing pass drafted the Retrospective below, human skims and propagates into Implementation/Learnings.md) AND the still-open, pre-existing ADR-043 human-review item (architect pass, REVIEW-QUEUE.md) — this closure resolves neither on its own; both stay open as independent flags, see REVIEW-QUEUE.md's SPRINT-049 entry."
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~8 tasks, L"      # effort estimate; checked vs actual in retro
created: 2026-08-16
started: "2026-08-16"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-16"            # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-049 — Email Capture & Threading Pipeline

## Sprint Goal

Ship `REQ-SB-55-US-01`'s full Pipeline of Jobs under `ADR-043` — Fetch (unchanged)
→ Classify (extended with recurring-pattern-candidate detection) → Thread-Match/Merge
→ Route-to-Project, plus the Summarize-Attachment and Detect-Recurring-Pattern branch
Jobs — replacing the monolithic `email-capture` Worker end to end, verified against a
real, live Outlook-backed capture run.

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — `REQ-SB-55-US-01` is the only story here.
  All 8 tasks (`T01`-`T08`) belong to one story, one architecture scope (`ADR-043`),
  and one connected dependency chain: `T01`/`T02` are independent roots → `T03`
  depends on `T01` → `T04`/`T05` depend on `T01`+`T03` → `T06` depends on `T02`+`T04`
  → `T07` (pipeline assembly) depends on `T03`/`T04`/`T05`/`T06` → `T08` (retirement
  + live verification) depends on `T07`. No reason to split a single story's own
  internal, acyclic chain across sprints.
- **Why NOT combined with `REQ-SB-63-US-01`** (the sibling story this sprint's own
  work unblocks): confirmed by direct reading of both story's task files that the
  dependency runs strictly one-directional — `REQ-SB-63-US-01-T02` depends on THIS
  story's `T03` (Thread-Match/Merge, supplies `thread_result`), `T04` (Route-to-
  Project, the Consult-Librarian branch must never gate it), and `T07` (Pipeline
  assembly — `email_capture_pipeline.py` does not exist until `T07` lands, and `T02`
  adds its own 6th node into the graph `T07` compiles); `REQ-SB-63-US-01-T03`
  depends on this story's `T01` (the unconditional frontmatter-key setter it reuses
  for the cross-cutting tag write). None of this story's own 8 tasks depend back on
  anything in `REQ-SB-63-US-01` — confirmed by reading all 8 `depends_on` lists
  directly (`T01`/`T02`: `[]`; `T03`: `[T01]`; `T04`/`T05`: `[T01, T03]`; `T06`:
  `[T02, T04]`; `T07`: `[T03, T04, T05, T06]`; `T08`: `[T07]` — every edge stays
  inside `REQ-SB-55-US-01`). Two real, additional considerations tip this from "could
  combine" to "should not":
  1. **Sizing ceiling.** Combined, the two stories total 11 tasks — past this
     project's own largest-ever confirmed-accurate sprint (`SPRINT-021`/`SPRINT-030`,
     9 tasks/L, both matched their estimate exactly at retro per
     `Implementation/Learnings.md`). This story alone (8 tasks) already sits at this
     project's own well-calibrated L ceiling, matching two prior 8-task/L precedents
     that both matched their estimate exactly (`SPRINT-010` — `REQ-SB-13-US-01`,
     cited directly in `SPRINT-011`'s own Grouping Rationale — and `SPRINT-039`,
     `Learnings.md`'s own most recent 8-task/L match). Adding 3 more tasks on top
     would produce this project's first-ever 11-task sprint, with no sizing
     precedent to calibrate against — a real, avoidable risk to "fits in a single
     working context," not a hypothetical one.
  2. **A genuine, not artificial, live-verification boundary.** `REQ-SB-63-US-01-
     T02`'s own Tests block requires invoking the REAL, running
     `email_capture_pipeline.py` graph (or `consult_librarian` fed a real
     `thread_result` from a real `thread_match_merge` call) to verify `AC-01`/
     `AC-02`/`AC-05` — its own Context explicitly states "if the coder reaches this
     task before those land, treat it as genuinely blocked, not as license to
     improvise a divergent pipeline shape." That module is this sprint's own `T07`
     deliverable. Splitting on this exact boundary — this sprint ships and verifies
     the real pipeline first, the follow-on sprint consults it second — mirrors this
     project's own established `SPRINT-011`→`SPRINT-012` and `SPRINT-025`→`SPRINT-026`
     precedent: a real decomposer-authored cross-story `depends_on` edge is honoured
     via `depends_on_sprints` on the DOWNSTREAM sprint, not treated as "an artificial
     edge this role invented" (the exact phrase both those sprints' own Notes use to
     distinguish a real from a fabricated cross-sprint dependency) — so it does not
     trip the "cross-sprint dependency you had to introduce" MUST-FLAG trigger. See
     `SPRINT-050`'s own Grouping Rationale for the mirrored reasoning on that side.
  Kept as two ordered sprints, not two flagged-ambiguous options — the sizing
  ceiling plus the one-directional, live-verification-gated dependency shape make
  this a reasoned sizing + dependency-shape call, not a genuinely ambiguous
  partition (mirroring `SPRINT-011`'s own identical framing).
- **Sizing estimate:** ~8 tasks, L — directly matches two prior 8-task/L precedents
  that both matched their estimate exactly at retro (`SPRINT-010`, `SPRINT-039`),
  and sits just under this project's own largest confirmed-accurate ceiling
  (`SPRINT-021`/`SPRINT-030`, 9 tasks/L). `T07` (pipeline assembly, wiring all 6 Jobs
  into one compiled `StateGraph`) and `T08` (multi-file retirement plus the
  mandatory real, live Outlook-backed end-to-end run, `AC-09`) are expected to be
  the heaviest by live-verification effort, not code volume — consistent with this
  project's own repeated sizing-calibration finding (`Learnings.md`, most sprints)
  that the heaviest task is the one carrying the real live-integration proof, not
  the largest diff.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-049 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-55-US-01](../UserStories/REQ-SB-55-US-01-email-capture-and-threading-pipeline.md) | Email Capture & Threading Pipeline — Fetch/Classify/Thread-Match-Merge/Route-to-Project, attachment summarization, recurring-pattern detection | P1 | Done |

**Tasks in scope** (dependency order): `T01` (`vault_writer.py` new primitives,
`depends_on: []`), `T02` (Classify recurring-pattern-candidate extension,
`depends_on: []`) → `T03` (Thread-Match/Merge, `depends_on: [T01]`) → `T04`
(Route-to-Project, `depends_on: [T01, T03]`), `T05` (Summarize-Attachment,
`depends_on: [T01, T03]`) → `T06` (Detect-Recurring-Pattern, `depends_on: [T02, T04]`)
→ `T07` (Pipeline assembly, `depends_on: [T03, T04, T05, T06]`) → `T08` (Retire
`email-capture` + live end-to-end verification, `depends_on: [T07]`).

---

## Dependencies / External Blockers

- **Depends on sprints:** None. This story's real prerequisite,
  `REQ-SB-54-US-01` (the Thread data shape and `ConversationID` stability), is
  already `Done` (`SPRINT-048`, 2026-08-16) — no sprint-level edge is needed for
  already-completed work.
- **Unblocks:** `SPRINT-050` (`REQ-SB-63-US-01`) — recorded as that sprint's own
  `depends_on_sprints: [SPRINT-049]` edge, not duplicated here.
- Story-level `gate: flagged` (trigger-3, `ADR-043` human review) is a standing
  breadcrumb, not a build blocker — per this project's own established
  `REQ-SB-54-US-01`/`SPRINT-048` precedent (a `Ready`/`flagged` story is fully
  eligible for `/plan-sprints` and `/implement-sprint`; the flag awaits a human
  look at `ADR-043`, independent of delivery progress).

---

## Out of Scope

- `REQ-SB-63-US-01` — this same `/plan-sprints` batch's other story; depends ON
  this sprint's own output (`T01`/`T03`/`T04`/`T07`), sequenced into `SPRINT-050`.
- Building whatever new Pipeline `Detect-Recurring-Pattern` proposes — the story's
  own Non-Goals; a separate, runtime, operator-approved creation through the
  existing Agent Creation Wizard.
- Meeting capture / Thread linking (`REQ-SB-56`), the Glimpse/History synthesis
  mechanism (`REQ-SB-57`), Glimpse-first chat answering (`REQ-SB-58`), and
  backfilling existing Email notes into Threads (`REQ-SB-59`) — all separate,
  future stories per this story's own Non-Goals.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact (n/a — `ADR-043`/`architecture.md`'s own "Email Capture & Threading Pipeline" section were both written at the architect pass, before this sprint's own build began; this coder pass introduced no new architectural fact beyond what `ADR-043` already recorded)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` (n/a to this closing pass — `ADR-043` was already recorded at the architect pass; this task did not touch `ADR.md`/`architecture.md`, per its own scope boundary)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [x] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

### Sizing accuracy

- **Estimated:** ~8 tasks, L — **Actual:** 8 tasks, L — matched exactly.
  A third confirmed-accurate 8-task/L precedent alongside `SPRINT-010` and
  `SPRINT-039` (`Implementation/Learnings.md`), reinforcing that "8 tasks,
  a clean linear-with-one-fork dependency chain" is this project's own
  well-calibrated L ceiling. As predicted in this sprint's own Grouping
  Rationale, `T07` (pipeline assembly) and `T08` (retirement + the
  mandatory real live-verification run) were the heaviest by real
  verification effort, not code volume — `T08`'s own live run against the
  real, configured Outlook mailbox took ~110s wall-clock for a single
  genuinely-new email, well inside this project's own documented 90s-to-
  several-minutes real-capture-run range (`SPRINT-031` precedent, reused
  correctly here).

### What worked

- **Building the graph assembly (`T07`) LAST, only once every Job function
  (`T02`-`T06`) already existed and was independently verified**, avoided
  ever reconciling a half-built `StateGraph` against Job functions whose
  own return shapes were still in flux — by the time `T07` started, every
  contract (`thread_result["created"]`, `classification["recurring_
  candidate"]`, `summarize_attachment`'s `dated_entry`) was already real
  and stable.
- **Reusing an existing primitive instead of adding a near-duplicate one**
  — `T01` discovered live that its own planned "unconditional frontmatter-
  key setter" already existed as `upsert_frontmatter_key` (`REQ-SB-09-
  US-01-T01`, `SPRINT-028`) and reused it directly rather than adding a
  second, functionally-identical primitive under a new name. Caught early
  (at the first task in the chain) because the coder read the existing
  file before writing, per this project's own standing "read before
  writing" rule.
- **The decomposer's own `trigger="direct"` (never `"background"`) call**
  for both new Pending-Approval kinds (`T04`/`T06`) held up cleanly in
  live verification — a single real pipeline tick can and did produce
  multiple distinct proposals (this sprint's own live runs confirmed
  `route_thread_to_project` fires once per brand-new Thread, never
  collapsed by `"background"`'s idempotency guard, which was the exact
  risk this decomposer-level judgement call was written to avoid).
- **The mandatory real, live Outlook-backed `AC-09` verification (`T08`)
  found a genuinely new, unprocessed real email on the first attempt** —
  no need for a synthetic/injected test message, no multi-attempt retry
  to find "genuinely new" mail. The resulting real Thread note and real,
  genuinely-derived `route_thread_to_project` Pending Approval (a real
  new-Project proposal, since the matched customer had zero currently-
  open Projects) matched every AC-09 Then-clause on the first real run.

### What didn't work

- **A plain `str` return value handed directly to a `Path`-requiring
  primitive** tripped a live `AttributeError: 'str' object has no
  attribute 'read_text'` in `T03` (`create_thread_note_baseline` returns
  `write_note`'s own plain-`str` contract, while `replace_body_section`/
  `append_body_section_line`/`upsert_frontmatter_key`/`read_note` all
  require a real `Path`) — the SAME class of error recurred independently
  in `T04`'s own `finalize_thread_project_routing` (a Pending-Approval
  `payload` value is always a JSON-round-tripped `str`, never a `Path`,
  requiring an explicit `Path(...)` re-wrap before reuse). Neither
  recurrence was a design flaw in the primitives themselves — both were
  caught live, on the first real attempt, and fixed by resolving the
  correct `*_path()` helper up front — but the SAME gap recurring twice
  independently across two different tasks in the same story is worth a
  standing pattern note (below) rather than treating each as a one-off.

### Patterns to carry forward

- **Before composing a `vault_writer.py` body/frontmatter primitive
  (`replace_body_section`/`append_body_section_line`/
  `upsert_frontmatter_key`/`read_note`, all of which call `path.read_text`/
  `path.write_text` directly) against a value that came from a DIFFERENT
  function's own return contract or a JSON-round-tripped Pending-Approval
  `payload`, explicitly resolve/re-wrap it as a real `Path` first** (e.g.
  via the relevant `*_path()` helper, or `Path(payload["field"])`) —
  never assume a `str`-shaped return value is interchangeable with a
  `Path` just because it prints the same. This bit two independent tasks
  in this one sprint alone.
- **Build a multi-Job DAG's own assembly module (the `StateGraph` file)
  strictly LAST, after every composed Job function already has an
  independently-verified, stable return contract** — confirmed a second
  time this sprint (`T07`), matching the same "assembly last" ordering
  this project's own architect pass had already reasoned through when it
  split the 8 tasks this way.
- **When a decomposer-level Pending-Approval design choice (e.g.
  `trigger="direct"` vs `"background"`) hinges on a documented but
  easy-to-miss idempotency/dedup contract of an existing shared
  primitive, log the specific mechanism reasoning inline in the task file
  itself** (as `T04`/`T06` both did for `create_pending_approval`'s own
  `"background"`-only dedup guard) — this made the choice easy to verify
  live rather than needing to be re-derived from scratch during
  implementation.

### Antipatterns to avoid

- **Do not assume two different "returns effectively the same string"
  contracts are interchangeable** (a `write_note`-family plain `str`
  path vs. a real `pathlib.Path` object; a Pending-Approval JSON
  `payload` value vs. an in-process `Path` object) — both are real,
  live-discovered gaps this sprint, not hypothetical.
- **Do not defer the mandatory real, live external-integration
  verification (`AC-09`-shaped ACs) to "whenever it's convenient"** — this
  sprint's own final task ran it as a small, bounded, single-new-email
  live check rather than a large batch, keeping the real wall-clock cost
  and the blast radius against the real vault both small and legible.

### Open follow-ups

- `classify_recent_emails`/`record_conversation_note`/
  `find_related_note_stems`/`conversation_index.json`/the `## Related
  Emails` body region are now dead code for the scheduled/on-demand email
  path specifically, but were deliberately left in place (`T08`) since
  `app/api/email_poc_router.py`'s own standalone `/poc/classify-emails`
  manual endpoint still calls `classify_recent_emails` directly — a real
  remaining caller outside this story's own scope. Whether that endpoint
  itself should eventually be retired/migrated onto the new Pipeline is
  an open, undecided question for a future pass, not decided here.
- `ADR-043`'s own human review (flagged at the architect pass, `REVIEW-
  QUEUE.md`) is STILL OPEN — shipping and verifying this story does not
  resolve it; it is its own separate approve/reject decision on the ADR
  as written, independent of whether the resulting code works (which it
  does, verified live).
- Any already-persisted `.second-brain/` state on a DIFFERENT real vault
  (not this project's own dev/production vault, which this task itself
  ran against and which self-healed cleanly) still keyed under the
  literal `"email-capture"` id (schedules, working-mode overrides,
  background-agent flags, history) is not migrated by this story — a
  disclosed, out-of-scope migration concern per `T08`'s own Constraints,
  not tested by any Scenario here.

---

## Notes

**Sprint assembled 2026-08-16 (`/plan-sprints`).** `REQ-SB-55-US-01` enters
`/plan-sprints` `status: Ready`, `gate: flagged` (trigger-3, `ADR-043` — a
standing breadcrumb, not a blocker per the established `REQ-SB-54-US-01`/
`SPRINT-048` precedent explicitly reconfirmed for this pass).

**Gate: `gate: clear` 2026-08-16.** No MUST-FLAG trigger fires for this
product-owner pass: (1) no material assumption — the standalone, single-story
grouping is read directly off the decomposer's own recorded `depends_on` graph
(fully internal to this story) and off `REQ-SB-63-US-01`'s own recorded
cross-story edges (confirmed one-directional by direct reading, not guessed);
(2) `REQ-SB-55` is not `<!-- Draft -->`/unfinalised; (3) product-owner does not
write ADRs — `ADR-043` was already authored and reviewed before this pass;
(4) no new `ESCALATIONS.md` entry; (5) not oversized (8 tasks, L, matching two
prior confirmed-accurate 8-task/L precedents, `SPRINT-010`/`SPRINT-039`, and
under this project's own largest-ever 9-task/L ceiling); not a blocked story
(its one real prerequisite, `REQ-SB-54-US-01`, is already `Done`); the
`depends_on_sprints: [SPRINT-049]` edge this pass records lives on `SPRINT-050`,
not here — and even there it is a real edge mirroring the decomposer's own
recorded task-level `depends_on`, not an artificial one this role invented (see
`SPRINT-050`'s own Notes; the identical, already-established `SPRINT-011`→
`SPRINT-012` and `SPRINT-025`→`SPRINT-026` reasoning applies); (6) N/A
(coder-only trigger); (7) no contradictory inputs; (8) not genuinely
ambiguous — the sizing ceiling plus the one-directional, live-verification-
gated dependency shape (`REQ-SB-63-US-01-T02`'s own Tests block requires the
real, running pipeline this sprint's `T07` builds) make two ordered sprints
the reasoned call, not an equally-valid toss-up with one combined sprint.
Advances `Draft → Ready`.

**BACKLOG.md updated:** `REQ-SB-55` row's Sprint column set to `SPRINT-049`.

**Coder pass, 2026-08-16 — sprint closed `Done`.** All 8 tasks
(`T01`-`T08`) `Done`; the one story in scope, `REQ-SB-55-US-01`, closed
`status: Done` on `T08`'s own completion (all 9 locked ACs verified,
including the mandatory real, live, non-mocked Outlook-backed `AC-09`
run against this project's own real, configured mailbox and vault — see
`T08`'s own Implementation Log for the real Thread note and real Pending
Approval it produced). `status: In Progress` → `Done`, `completed:
"2026-08-16"`. `gate` set to `flagged` (was `clear`) — NOT because a new
MUST-FLAG trigger fired on this closing pass itself, but per this
project's own sprint-wrap contract: closing a sprint via a drafted
Retrospective always sets `gate: flagged` so a human skims it before its
Patterns/Antipatterns propagate into `Implementation/Learnings.md`. This
sprint's own `gate_reason` deliberately carries TWO independent reasons
forward, not one — the retro-harvest trigger (this pass, new) AND the
pre-existing `ADR-043` human-review item the architect pass originally
flagged on `REQ-SB-55-US-01` (still open, `REVIEW-QUEUE.md`, not
resolved by this closure) — per this task's own launch instructions, the
older item is disclosed rather than silently dropped when the newer one
is added. `BACKLOG.md`'s `SPRINT-049` Sprint Status row and `REQ-SB-55`
row both updated to `Done` in the same pass. See `## Retrospective`
above for the full sizing/what-worked/what-didn't/patterns/antipatterns/
follow-ups breakdown, and `REVIEW-QUEUE.md`'s own new `SPRINT-049` entry
for the human action items this closure leaves open.
