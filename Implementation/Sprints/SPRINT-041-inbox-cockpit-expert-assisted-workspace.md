---
id: SPRINT-041
title: Inbox Cockpit — Meeting Cockpit pattern adapted for email, attachment review, reviewable draft replies
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "retro drafted for human skim; 2 scope-internal judgment calls on T01/T03 logged for spot-check (see REVIEW-QUEUE.md); no blocked work."
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: [SPRINT-040, SPRINT-038]   # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~6 tasks, M"      # effort estimate; checked vs actual in retro
created: 2026-08-14
started: "2026-08-14"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-14"            # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-041 — Inbox Cockpit

## Sprint Goal

Build `REQ-SB-44-US-01` end to end per `ADR-036`: the `recipients`
Email-note frontmatter field and `my_day` stem field, then — once its two
real prerequisite sprints land — attachment review (composing
`REQ-SB-28-US-01`'s upload/summarize mechanism), extending the SHARED
`cockpit_router.py`/`cockpitApiClient.ts`/`Cockpit.tsx` `REQ-SB-43-US-01`
builds, and a clickable My Day Emails row that opens the real Inbox
Cockpit with reviewable (never auto-sent) draft replies.

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — `REQ-SB-44-US-01` is the only
  story here. All 6 of its tasks are real, buildable work with a real task
  id to sequence against (unlike `SPRINT-024`'s/`SPRINT-029`'s own
  precedent of a task individually excluded from every sprint because its
  blocker had zero decomposition) — so the whole story is kept together in
  one sprint, ordered after its two real prerequisites via
  `depends_on_sprints`, per `Implementation/Pipeline.md` hard rule 7's
  "ordered sprints with a recorded `depends_on_sprints` edge" clause.
- **Two real, pre-existing cross-story `depends_on` edges drive the
  ordering — neither introduced by this pass:**
  1. **Shared-module dependency (`ADR-036` point 3, "SHARE, do not
     fork"):** this story's `T04`/`T05`/`T06` each carry a `depends_on`
     edge onto a `REQ-SB-43-US-01` task (`T05`/`T07`/`T08` respectively) —
     this story extends the SAME `cockpit_router.py`/`cockpitApiClient.ts`/
     `Cockpit.tsx` files `REQ-SB-43-US-01` builds, never a duplicate
     module. Recorded as `depends_on_sprints: [SPRINT-040]` (the sprint
     carrying `REQ-SB-43-US-01`).
  2. **Cross-story `REQ-SB-28-US-01` dependency (`ADR-036` point 5,
     mirroring `REQ-SB-39-US-02`'s own precedent for a `Ready`-not-`Done`
     cross-story dependency):** this story's `T03`
     (`cockpit/attachments.py`) carries `depends_on: [REQ-SB-28-US-01-T01,
     REQ-SB-28-US-01-T03, REQ-SB-28-US-01-T04, REQ-SB-43-US-01-T02]`.
     `REQ-SB-28-US-01` already carries a real sprint assignment
     (`SPRINT-038`, `status: Ready`) as of this pass — recorded as
     `depends_on_sprints: [..., SPRINT-038]` rather than excluding `T03`
     from every sprint, since a real target sprint now exists to sequence
     against (unlike the `SPRINT-024`/`SPRINT-029` precedent, where the
     blocking story had zero decomposition and no real task id existed at
     all). `T04`/`T05`/`T06` transitively wait on `T03`.
- **Why NOT split into two sprints** (a "buildable now" sprint for `T01`/
  `T02` — which carry no such dependency and could build immediately — plus
  a separately-ordered sprint for `T03`-`T06`): a story carries exactly one
  `sprint:` field (the bidirectional link is per-story, not per-task), so
  splitting `T01`/`T02` out would require a second, distinct story-level
  sprint assignment this project's own artefact model does not support.
  `T01`/`T02` are also both infra-only, supporting-only tasks with no
  AC-tagged step of their own (mirrors `REQ-SB-40-US-01-T01`'s own
  precedent) — genuinely no independent value alone, so gating them behind
  the same two real prerequisites as the rest of this small (6-task) story
  is the correct, non-speculative reading of hard rule 7's "ordered
  sprints" clause, not an unforced blocking decision.
- **Why NOT combined with `REQ-SB-43-US-01` directly:** would produce a
  ~15-task sprint, past this project's own sizing ceiling — see
  `SPRINT-040`'s own Grouping Rationale for the full reasoning.
- **Sizing estimate:** ~6 tasks, M. `T01`/`T02` (recipients field; `my_day`
  stem field, both `depends_on: []`, buildable immediately once this
  sprint starts) → `T03` (attachments module, gated on `SPRINT-038` +
  `SPRINT-040`) → `T04` (extend `cockpit_router.py`) → `T05` (extend
  `cockpitApiClient.ts`) → `T06` (`InboxCockpitPage.tsx` + clickable Emails
  rows + `AttachmentsPanel.tsx` + draft-copy affordance, owning the
  page-level bulk of the locked ACs).

---

## Stories in Scope

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-44-US-01](../UserStories/REQ-SB-44-US-01-inbox-cockpit-expert-assisted-workspace.md) | Inbox Cockpit — the Meeting Cockpit's 3-panel pattern adapted for email, with sender/CC/thread people chips, attachment review, and reviewable (never auto-sent) draft replies | P1 | Done |

**Tasks in scope** (dependency order): `T01` (`outlook_com.
resolve_mail_recipients` + Email note `recipients` field, `depends_on:
[]`), `T02` (`my_day.list_email_items` gains `"stem"`, `depends_on: []`) —
both independent, buildable as soon as this sprint starts — then `T03`
(`cockpit/attachments.py`, `depends_on: [REQ-SB-28-US-01-T01,
REQ-SB-28-US-01-T03, REQ-SB-28-US-01-T04, REQ-SB-43-US-01-T02]`) → `T04`
(extend `cockpit_router.py`, `depends_on: [T03, REQ-SB-43-US-01-T05]`) →
`T05` (extend `cockpitApiClient.ts`, `depends_on: [T04,
REQ-SB-43-US-01-T07]`) → `T06` (`InboxCockpitPage.tsx` + route + clickable
Emails rows + `AttachmentsPanel.tsx` + draft-copy affordance, `depends_on:
[T05, REQ-SB-43-US-01-T08, T02]`).

---

## Dependencies / External Blockers

- **Depends on sprints:** `SPRINT-040` (`REQ-SB-43-US-01` — the shared
  `cockpit_router.py`/`cockpitApiClient.ts`/`Cockpit.tsx` module this
  story's `T04`/`T05`/`T06` extend) and `SPRINT-038`
  (`REQ-SB-28-US-01` — the upload-storage/summarize-file mechanism this
  story's `T03` composes directly). Both must be `Done` before
  `/implement-sprint` may start this sprint, per
  `Implementation/Pipeline.md` hard rule 9.
- Both edges mirror real, already-recorded `depends_on` task edges the
  decomposer wired (`ADR-036` points 3 and 5) — not introduced by this
  product-owner pass.

---

## Out of Scope

- `REQ-SB-43-US-01` — built in its own, earlier-ordered sprint
  (`SPRINT-040`); this sprint only extends it, never duplicates it.
- `REQ-SB-42-US-01` — no dependency relationship to this story (see
  `SPRINT-039`).
- Actually sending a drafted reply, a create-Person-note flow, draft-reply
  persistence, and new CC/thread-participant capture-side extraction
  beyond the `recipients` field itself — all explicitly out of this
  story's own scope (see the story's own Non-Goals).

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — N/A, this sprint built exactly the module/field shape `ADR-036` already recorded; no new architectural fact emerged
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — N/A, `ADR-036` already `Accepted` before this sprint started
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

### Sizing accuracy

- **Estimated:** ~6 tasks, M — **Actual:** 6 tasks, M — matched exactly.
  No task was split, dropped, or merged. Code volume was genuinely small
  across all 6 tasks (the new `attachments.py` module is ~60 lines; every
  other task was a few-line additive change) — the real cost was, once
  again, live-verification complexity: a real Outlook-capture-pipeline
  composition to prove the JSON-string frontmatter workaround round-trips
  (`T01`), a real PDF attachment + real Compass summarization call
  (`T03`/`T04`/`T05`), and a full real-browser, multi-agent,
  multi-real-Provider-call click-through covering all 13 locked ACs
  (`T06`) — including a temporary real skill-grant/Provider-swap
  reconfiguration for on-the-spot research, cleanly reverted and
  independently reconfirmed afterward.

### What worked

- **Reusing `SPRINT-040`'s own already-disclosed `vault_writer.py`
  list-of-dicts round-trip limitation immediately, without rediscovering
  it** — the parent agent's own briefing named the exact gap and the exact
  workaround (`MEMORY.md`'s 2026-08-14 entry) before this sprint's `T01`
  started; the JSON-string convention was applied directly and confirmed
  live to round-trip correctly through the real, unmodified
  `write_note`/`read_note` pair on the first attempt, with zero debugging
  cycles spent rediscovering the same defect a second time.
- **Composing `REQ-SB-28-US-01`'s own already-`Done`
  `upload_storage`/`summarize_file` DIRECTLY, never through its own
  chat-upload HTTP endpoint** — confirmed live end-to-end (a real PDF
  attachment on a real captured email, real extraction, real Compass
  summarization, real thread turn) with genuinely zero code duplication;
  the deliberate divergence from `T04`'s own endpoint (documented up front
  in `T03`'s own Context, not discovered mid-build) held up exactly as
  planned.
- **`SPRINT-040`'s own temporary-real-state-reconfigure-then-revert
  protocol reused a further time** for the identical real gap (no agent
  in this vault's real configuration is both Hub-routable for research AND
  already Provider/Skill-equipped for it) — `vault-qa`'s temporary
  `web-research` grant + Anthropic-Claude Provider swap was cleanly
  reverted and independently reconfirmed via a fresh
  `list_agent_skills`/`get_agent_provider` call, plus a final vault-index
  note-count check matching the exact pre-test value.
- **The `research.py` module needed genuinely zero changes** — the
  decomposer's own judgment call (reuse `REQ-SB-43-US-01-T04`'s module
  UNCHANGED, already generic over `subject_kind`) was independently
  confirmed twice: once by direct source reading (no `REQ-SB-44`-specific
  branch anywhere in the file) and once live (a real `"email"`
  `subject_kind` research trigger/save/discard/scoping round trip, all
  correct, with zero new backend code).

### What didn't work

- **The frontend's own hardcoded `brought_in_agent_ids[0]` requester
  convention silently produced an honest `no_match` on the first live
  research attempt**, reproducing `SPRINT-040`'s own already-documented
  Learnings entry a second time (a different story, the identical root
  cause) — the first-brought-in Expert happened to be the only real
  keyword-matching Hub-routing candidate for its own request, excluded as
  its own requester. Resolved immediately by constructing a second test
  cockpit with the bring-in order reversed; not a defect, but confirms
  this specific test-construction lesson is worth carrying forward a
  further time, since it recurred even with the prior Learnings entry
  already on file.
- **A dedicated real frontend dev server + backend port pair had to be
  stood up from scratch for this sprint's own live verification**, since
  the harness's own pre-existing "preview server" (port 5173) defaulted to
  an unrelated sibling project's backend (port 8000, `agentic-map`) with
  no `VITE_API_BASE_URL` override in place — cost one investigation cycle
  (a confusing `{"detail":"Not Found"}` from what looked like a real
  backend) before the mismatch was confirmed via a direct `curl /` probe.

### Patterns to carry forward

- **When a parent agent's own launch briefing already names a prior
  sprint's disclosed real-primitive limitation and its exact workaround,
  apply it directly on the first attempt rather than re-deriving it** —
  saved a full debugging cycle this sprint that `SPRINT-040` itself had to
  spend discovering the limitation from scratch.
- **Before trusting any pre-existing "preview" dev server for live
  verification, confirm what backend/app it is actually serving via a
  direct, unauthenticated probe** (e.g. `GET /` and inspect the real
  response) — extends this project's own already-documented "don't trust
  a stray dev-server process without confirming what it serves" antipattern
  one layer further, to a *frontend* dev server pointed at the *wrong*
  backend, not just a stale/orphaned process serving old code.
- **Constructing TWO independent real test fixtures (different bring-in
  orders) to get a genuinely positive research-routing result, rather than
  reusing one fixture and hoping the ordering doesn't matter** — cheap
  (one more synthetic capture + two more bring-in clicks) and turned a
  known failure mode into a directly-observed, confidently-positive
  confirmation instead of a caveat.

### Antipatterns to avoid

- **Assuming a harness-provided "preview server" is correctly wired to
  THIS sprint's own backend without an explicit content probe first** —
  cost one avoidable investigation cycle this sprint; check the served
  content's own identity (title, root response) before spending time
  debugging what looks like an app-level bug.

### Open follow-ups

- **The `brought_in_agent_ids[0]`-as-requester convention for on-the-spot
  research is a real, recurring UX rough edge** (now observed twice,
  `SPRINT-040` and `SPRINT-041`) — worth a future, explicit product
  decision (e.g. let the user pick which brought-in Expert originates a
  research request) rather than the current implicit "whoever was brought
  in first" rule silently producing an honest-but-confusing `no_match`.
  Not a defect of either shipped story — both built exactly to their own
  locked ACs — but worth naming for a future polish pass.
- **Same open item `SPRINT-040` already named, still open:** whether a
  people chip with no existing Person note should offer a
  create-Person-note flow — this sprint's own Inbox Cockpit reuses the
  identical honest-fallback-only design, still deliberately not built.

---

## Notes

**Sprint assembled 2026-08-14 (`/plan-sprints`).** `REQ-SB-44-US-01`'s own
`ADR-036` (shared with `REQ-SB-43-US-01`) was approved 2026-08-14; this
story enters `/plan-sprints` fully `Ready`, `gate: clear`, carrying two
real, pre-existing cross-story `depends_on` edges (onto `REQ-SB-43-US-01`'s
shared-module tasks and onto `REQ-SB-28-US-01`'s upload/summarize tasks) —
both mapped to `depends_on_sprints` edges here, since both blocking stories
already carry real sprint assignments (`SPRINT-040`, this same pass;
`SPRINT-038`, assembled by a concurrent `/plan-sprints` pass and
re-confirmed fresh immediately before this file was written).

**Gate: `gate: clear` 2026-08-14.** No MUST-FLAG trigger fires for this
product-owner pass: (1) no material assumption — both `depends_on_sprints`
edges mirror real, decomposer-recorded task-level `depends_on` edges
exactly, not guessed or re-decided; the choice to keep the whole story in
one sprint rather than split `T01`/`T02` out is a direct consequence of
this project's own one-story-one-sprint artefact model, not an assumption;
(2) `REQ-SB-44` is not `<!-- Draft -->`/unfinalised; (3) product-owner does
not write ADRs — `ADR-036` was already reviewed and approved before this
pass; (4) no new `ESCALATIONS.md` entry; (5) **re-checked explicitly
against all three MUST-FLAG sub-triggers named for this role, not
skipped:** not oversized (6 tasks, M); not a "blocked story" in the
MUST-FLAG sense — the story is `status: Ready` with a real, disclosed,
already-tracked cross-story dependency (the story's own `gate_reason`
already names it as "tracked at task level, not a story-level blocker"),
and both of this sprint's cross-sprint edges are pre-existing task-level
edges the decomposer already recorded, not new dependencies this pass
introduced (mirrors `SPRINT-024`'s and `SPRINT-029`'s own identical point-5
reasoning); (6) N/A (coder-only trigger); (7) no contradictory inputs; (8)
not genuinely ambiguous — the one-sprint-ordered-after-two-prerequisites
reading is the only one this project's own one-story-one-sprint model
supports; the alternative (splitting `T01`/`T02` into their own sprint) was
considered and rejected explicitly above, not silently discarded. Advances
`Draft → Ready`.
