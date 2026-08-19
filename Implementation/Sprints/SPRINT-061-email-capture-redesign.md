---
id: SPRINT-061
title: Email Capture Redesign — Thread Raw/Distilled Split, Two-Stage Pipeline, Files/OKF Companions
status: Done                      # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Human confirmed directly, 2026-08-18: operator's own 'finish the sprint' directive covers this routine cross-sprint sequencing trigger — depends_on_sprints: [SPRINT-060] is now satisfied (SPRINT-060 status: Done). This is a procedural sequencing flag, not a fresh architectural risk (every ADR-048 design decision was already co-designed with the operator turn-by-turn in the originating conversation). Flag cleared; eligible for /implement-sprint. Prior flagged history (trigger-5, cross-sprint dependency) preserved in git history of this file. [Coder, 2026-08-18: all 7 tasks Done, all 7 locked ACs verified live. Re-flagged for retro-harvest (standard end-of-sprint gate) plus one new, separately-recorded out-of-scope finding — ESC-048 — found live during this build. See REVIEW-QUEUE.md."
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: ["SPRINT-060"] # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~7 tasks, L"     # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-18
started: "2026-08-18"                        # YYYY-MM-DD when status → In Progress
completed: "2026-08-18"                        # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-061 — Email Capture Redesign — Thread Raw/Distilled Split, Two-Stage Pipeline, Files/OKF Companions

## Sprint Goal

Replace the single-file Thread with a directory of immutable raw message
notes plus a distilled `## Summary`/`## Related` concept file, regenerated
via two decoupled, operator-triggered stages (zero-Compass raw capture,
Compass-backed synthesis), and give every real email attachment its own
`files/<slug>/` OKF-companion note.

---

## Grouping Rationale & Sizing

- **Why a single-story sprint.** All 7 tasks belong to one story
  (`REQ-SB-71-US-02`) with one Definition of Done and one architecture
  scope (`architecture.md` → "Email Capture Redesign — Thread Raw/Distilled
  Split, Stage 1/Stage 2" + "Files/OKF Companion Convention"). Graph read
  directly from each task file's own `depends_on:` frontmatter, not
  re-derived from the story's own summary table:
  - `T01` (Thread directory + raw message primitives) — `depends_on: []`.
  - `T02` (note-discovery generalization) — `depends_on: [T01]`.
  - `T03` (Stage 1 pipeline) — `depends_on: [T01]`.
  - `T04` (Stage 1 endpoint) — `depends_on: [T03]`.
  - `T05` (Stage 2 — `synthesize_thread`) — `depends_on: [T01, T02,
    REQ-SB-71-US-01-T01]` — the one real cross-story edge, into this
    batch's sibling foundation story.
  - `T06` (Stage 2 endpoint) — `depends_on: [T04, T05]`.
  - `T07` (Files/OKF companion) — `depends_on: [T05, REQ-SB-71-US-01-T01]`
    — the second real cross-story edge, same reason as `T05`.
  - Acyclic, all `phase: P1`. Splitting `T02`/`T07` out into separate
    sprints (the only structurally-possible finer split, since they're
    each their own decomposer-called-out separable pieces of work) would
    introduce needless additional cross-sprint edges for a single story
    with one DoD — the same "don't split a tightly-scoped single story"
    reasoning `SPRINT-057`/`SPRINT-058`/`SPRINT-059` already established
    as this project's norm.
- **Why sequenced strictly BEHIND `SPRINT-060`, not merged into one giant
  sprint with it (or with `REQ-SB-71-US-03`):** `T05` and `T07` both
  `depends_on: REQ-SB-71-US-01-T01` — this story's own new Thread/Files
  callers cannot correctly register against `section_ownership.py`'s
  registry, nor call the guarded `replace_body_section`, until that guard
  actually exists. This directly extends this project's own repeatedly
  confirmed `Implementation/Learnings.md` pattern (`SPRINT-011`→`012`,
  `SPRINT-025`→`026`, `SPRINT-049`→`050`): *"Sequence a downstream story
  strictly behind its upstream one via `depends_on_sprints`, rather than
  combining into one oversized sprint, when the downstream story's own
  Tests block requires the REAL, running output of the upstream story."*
  Here the "real, running output" is the guard module and its
  `SectionWriteNotAllowed` contract, not a stub the coder would otherwise
  have to improvise against.
- **Why NOT one giant 13-task sprint across all three `REQ-SB-71` stories
  (the single-sprint alternative considered and rejected):** the combined
  batch (`REQ-SB-71-US-01` 2 tasks + `REQ-SB-71-US-02` 7 tasks +
  `REQ-SB-71-US-03` 3 tasks = 12, or 13 with `REQ-SB-70-US-01`) would sit
  well above every sprint this project has shipped and confirmed accurate
  to date — the largest confirmed-accurate precedent is 9 tasks, L
  (`SPRINT-021`, `SPRINT-030`); the next-largest recurring bucket is 8
  tasks, L (`SPRINT-010`, `SPRINT-035`, `SPRINT-039`, `SPRINT-049`,
  `SPRINT-056`). A 12-13-task sprint would be a genuine, disclosed
  "oversized sprint" risk (MUST-FLAG trigger 5) with no offsetting
  benefit — the real task dependency graph is a strict, mostly-linear
  chain across the three stories (not a tangled web needing one shared
  working context), so ordered sprints with recorded
  `depends_on_sprints` edges honour that same graph exactly as
  faithfully as one giant sprint would, without the size risk.
- **Sizing estimate:** ~7 tasks, L — between this project's own confirmed
  6-task M bucket and 8-9-task L bucket; sized L because the story's own
  text names three real, substantial pieces of work bundled together (raw/
  distilled split, two-stage pipeline, Files/OKF-companion convention),
  comparable in shape to `SPRINT-049`'s own 8-task L sprint (also a single,
  dependency-chained story with a diamond-shaped task graph).

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-061 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-71-US-02](../UserStories/REQ-SB-71-US-02-email-capture-raw-distilled-and-two-stage-pipeline.md) | Email Capture Redesign — Thread raw/distilled split, two-stage operator-triggered capture, Files/OKF companions | P1 | Done |

**Tasks in scope** (dependency order): `T01` → `T02`/`T03` (both depend
only on `T01`) → `T04` (depends on `T03`) → `T05` (depends on `T01`, `T02`,
and `REQ-SB-71-US-01-T01` from `SPRINT-060`) → `T06` (depends on `T04`,
`T05`) → `T07` (depends on `T05` and `REQ-SB-71-US-01-T01`).

---

## Dependencies / External Blockers

- **Depends on sprints:** `SPRINT-060` — must be `Done` before this sprint
  starts (`T05`/`T07` both hard-`depends_on` `REQ-SB-71-US-01-T01`, per
  `Implementation/Pipeline.md` hard rule 9: `/implement-sprint` refuses a
  sprint whose `depends_on_sprints` are not all `Done`).
- **External:** the real, live Outlook mailbox this pipeline captures from
  (Stage 1); the real Compass Provider (Stage 2, Files companion summary).

---

## Out of Scope

- Meeting capture, section-ownership enforcement itself, and vault base
  provisioning — each their own sibling sprint (`SPRINT-060`,
  `SPRINT-062`).
- Scheduler wiring for either stage (explicitly excluded per the story's
  own `## Non-Goals`).
- Backfilling already-captured Thread notes onto the new shape.
- Fixing Inbox Cockpit's own pre-existing hardcoded `Work/Emails/
  attachments` attachment root — disclosed, deliberately left as a
  separate follow-up (story's own `## Non-Goals`).

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — already appended at `/plan-tasks` (`ADR-048`), unchanged this pass
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — none created this pass (`ADR-048` already exists from `/plan-tasks`, still awaiting the human review recorded in `REVIEW-QUEUE.md`)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. The coder drafts this section and
sets gate: flagged. The HUMAN then skims it, approves, and copies anything under
"Patterns to carry forward" and "Antipatterns to avoid" verbatim (or expanded)
into Implementation/Learnings.md — that is the cross-sprint index future sprints
read. The retro here is a sprint-level snapshot; Learnings.md is the permanent
record. The coder does NOT write Learnings.md directly. -->

### Sizing accuracy

- **Estimated:** ~7 tasks, L — **Actual:** 7 tasks, L — matched exactly.
  Real build/verification time skewed heavier than the task count alone
  suggests, driven almost entirely by genuine Compass latency (repeated
  60-90s real synthesis calls) during live AC verification, not by code
  volume — mirrors `SPRINT-018`'s own already-recorded sizing-calibration
  lesson ("sizing estimate accurate for build effort, doesn't capture
  real-Provider-call latency variance during live verification").

### What worked

- Reading the FULL real code (`vault_writer.py`, `email_classification.py`,
  `email_pull.py`/`email_staging.py`, `agent_schedule_registry.py`) before
  writing a single line surfaced a real, load-bearing architectural
  tension (`ESC-048`) that no amount of re-reading the task/ADR text alone
  would have found — the task files' own docstrings describe an idealized
  "joins the shared dispatch lock" framing for `pull_and_stage_emails`
  that the real code does not actually implement (the lock lives in the
  scheduler's own dispatch wrapper, never in the pipeline function
  itself) — direct reading over trusting the spec's own narrative caught
  this before it became a live risk.
- Taking a real, immediate protective action (pausing `email-capture-
  pipeline` to `supervised` via the real, existing working-mode endpoint)
  BEFORE writing any code, the moment the `resolve_thread_note_path`
  retargeting risk was identified — not after the fact — meant the live
  hourly scheduler never had a window to exercise the broken path during
  this build.
- Real, live testing surfaced two genuine implementation bugs
  (`classify_captured_email` vs. `_with_fallback`; the `_slugify` 80-char
  truncation collapsing a real file_slug) that a synthetic/mocked test
  would very plausibly have missed — both required a real Compass call
  and a real, long filename respectively to manifest.
- Reusing the operator's own real, live inbox (rather than synthetic
  fixtures) for every AC gave unusually strong, concrete evidence: 252
  real raw message notes, 127 real Thread directories, real multi-
  message full-reconstruction synthesis, real PDF/XLSX attachments with
  genuine Compass summaries — all directly inspectable, not asserted.

### What didn't work

- Real Compass latency (60-90+ seconds per `synthesize_thread` call
  against this mailbox's real, often-long forwarded-chain content) made
  a straightforward single `curl -m <timeout>` unreliable for capturing
  the full response — had to fall back to firing the call with a short
  client-side timeout (the server continues processing in its own worker
  thread regardless of client disconnection) and polling the vault
  directly for completion. Worth a named pattern for future sprints that
  call real, slow synthesis endpoints.
- A large, uninspected pre-existing backlog in `.second-brain/
  email_staging/` (leftover from earlier `SPRINT-060` migration work)
  meant the very first real `AC-01` verification call produced a much
  larger real batch (252 messages) than a "one real newly-arrived email"
  Scenario literally describes — correct, honest behavior per `T03`'s own
  spec ("drains every currently-staged... email"), but worth flagging
  early in a task's own Tests section next time a story's own Stage 1
  might inherit an unknown-sized backlog from a prior migration.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Before retargeting a shared lookup primitive (`resolve_X_path`-shaped
  functions) that a NEW story's own task explicitly mandates changing,
  grep every real caller of that primitive across the WHOLE codebase, not
  just the callers the story's own text names — a still-`Done`, still-
  scheduled sibling capability from an earlier story can depend on the
  SAME primitive's OLD behavior in a way neither the analyst nor the
  architect's own text surfaces, because from that story's own vantage
  point it looks like a pure internal-mechanism change with an unchanged
  public contract.** Found live, `REQ-SB-71-US-02-T02` (`ESC-048`).
- **When a real, live regression risk to an already-`Done`, currently-
  scheduled capability is found mid-build, take a real, immediate,
  reversible protective action using an EXISTING, already-shipped control
  surface (here: the working-mode toggle) rather than either (a) silently
  proceeding and hoping the scheduler doesn't fire during the build
  window, or (b) improvising a fix in a file outside the task's own
  declared scope.** Found live, `REQ-SB-71-US-02-T01`/`T02` (`ESC-048`).
- **For a real, slow (60-90s+) synthesis-style endpoint under live
  verification, fire the call with a short client-side timeout and poll
  the vault directly for the durable write, rather than blocking a long
  `curl -m <large>` on the full HTTP response** — the server's own
  worker-thread execution continues regardless of client disconnection,
  so the real write still completes and is directly verifiable without
  tying up the verification session on one open connection. Found live,
  `REQ-SB-71-US-02-T05`/`T06`.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Trusting a task/ADR docstring's own narrative description of an
  existing function's behavior (e.g. "already joins the shared dispatch
  lock") without directly re-reading that function's real, current
  source** — the docstring's framing was aspirational/simplified, not
  literally how the code works; direct reading is what caught it before
  it mattered (in this case, harmlessly — the real behavior was actually
  MORE decoupled than the docstring implied, but the same blind trust
  could just as easily have hidden a real regression the other
  direction). Found live, `REQ-SB-71-US-02-T03`.

### Open follow-ups

- `ESC-048` (`REVIEW-QUEUE.md`): decide whether to file a `/bug` →
  `BUGFIX-NN-US-01` rewiring `process_staged_email` onto the new
  Stage 1/Stage 2 pipeline and retiring `thread_match_merge`'s live call
  site, or to leave `email-capture-pipeline` in `supervised` mode until
  `REQ-SB-71-US-03`/`SPRINT-062` or a dedicated follow-up addresses it.
- `T03`'s own disclosed, non-blocking finding: `capture_raw_thread_
  messages` never calls `mark_email_processed`, so the same near-term
  Outlook items can be harmlessly re-staged and re-skipped on repeated
  calls — a real efficiency (not correctness) follow-up, if ever worth
  addressing.
- The 12 pre-existing, `email.json`-less corrupted staging directories
  found in `.second-brain/email_staging/` (unrelated to this story, safely
  ignored by the existing `list_staged_emails()` guard) — a real, minor,
  pre-existing data-hygiene artifact, not filed as a bug since it causes
  no observable defect.

---

## Notes

**Grouping decision (product-owner, 2026-08-18):** Single-story sprint,
sequenced strictly behind `SPRINT-060` via a recorded `depends_on_sprints`
edge, per two real, hard task-level dependencies (`T05`, `T07` →
`REQ-SB-71-US-01-T01`) confirmed by direct reading of the task files, not
inferred. This extends this project's own repeatedly-confirmed Learnings
pattern (`SPRINT-011`→`012`, `SPRINT-025`→`026`, `SPRINT-049`→`050`:
sequence via `depends_on_sprints` rather than merge into one oversized
sprint when a downstream story's own Tests genuinely need the upstream
story's real, running output). See `SPRINT-060`'s own `## Notes` and this
sprint's `## Grouping Rationale & Sizing` above for the full single-vs-
multi-sprint reasoning across the whole 4-story `ADR-048` batch.

**Why `gate: flagged` (MUST-FLAG trigger 5 — cross-sprint dependency
introduced):** this sprint's own `depends_on_sprints: ["SPRINT-060"]` is a
cross-sprint dependency this pass had to introduce to honour the real task
graph without merging into one oversized (12-13-task) sprint. Per this
role's own MUST-FLAG list, introducing a cross-sprint dependency is always
flagged for human visibility, even when — as here — the sequencing is the
demonstrably correct, well-precedented call, not a genuinely ambiguous one.
No other MUST-FLAG trigger fired: not oversized on its own (7 tasks, L,
within this project's own confirmed range); no blocked story; the
partition itself is unambiguous (one story, one sprint, no alternative
grouping was seriously in play once `SPRINT-060`'s own foundational-vs-
Email/Meeting split was decided). The story's own `gate: flagged`
(architect's `ADR-048` flag) stays on the STORY, unchanged — tracked in
`REVIEW-QUEUE.md`'s existing 4-story `ADR-048` entry, not duplicated here.

gate: flagged 2026-08-18 (product-owner) — trigger 5 (cross-sprint
dependency introduced). See `REVIEW-QUEUE.md` for the human-facing entry.
Sprint stays `status: Draft` until the human reviews the sequencing (and,
separately, `ADR-048` itself).

---

**Coder note (2026-08-18, `/implement-sprint SPRINT-061`):** `SPRINT-060`
confirmed `Done`, `depends_on_sprints` satisfied. Human "finish the
sprint" directive (recorded in this sprint's own `gate_reason` above)
covers the routine cross-sprint sequencing flag. All 7 tasks built and
verified `Done` with real, live evidence — see the story's own coder
addendum and each task's own `## Implementation Log`. Sprint status →
`Done`. `gate` re-flagged for the standard end-of-sprint retro-harvest
plus one new, separately-recorded finding this build itself produced
(`ESC-048` — see `REVIEW-QUEUE.md`); the story's own standing `ADR-048`
human-review flag is unchanged, not cleared by this pass.
