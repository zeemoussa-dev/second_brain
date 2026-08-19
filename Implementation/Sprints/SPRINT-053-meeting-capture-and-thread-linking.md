---
id: SPRINT-053
title: Meeting Capture & Thread Linking — Link-to-Thread Job (ConversationID primary strategy, attendee-overlap/date-proximity fallback)
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "All 3 tasks (T00→T01→T02) Done, all 5 locked ACs verified. Non-blocking standing breadcrumb carried from T00/T01: the operator's own overnight provisional Option (a) resolution of ESC-040 (a non-string/COM-inaccessible ConversationID treated identically to absent) still awaits its own human spot-check — see REVIEW-QUEUE.md / ESCALATIONS.md ESC-040 (still Open, not Resolved). Plus retro-harvest — this sprint's drafted Retrospective below awaits human propagation into Implementation/Learnings.md."
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~3 tasks, S"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-17
started: "2026-08-17"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-17"            # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-053 — Meeting Capture & Thread Linking — Link-to-Thread Job

## Sprint Goal

Extend the existing, unmodified `meeting-capture` Worker with a `Link-to-Thread`
Job — primary `conversation_id`-match strategy plus a conservative, config-backed
attendee-overlap/date-proximity fallback — so a meeting genuinely part of an email
conversation shows up linked to that conversation's Thread.

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — `REQ-SB-56-US-01` is the only `Ready`,
  ungrouped story this pass (confirmed by reading every story's `status:`/
  `sprint:` frontmatter; the only other `Ready` story, `REQ-SB-42-US-01`, already
  carries `sprint: SPRINT-039` and is out of scope for this pass). Its 3 tasks
  (`T00`→`T01`→`T02`) form one strict linear chain, acyclic, all within one
  architecture section ("Meeting → Thread Linking..."); no reason to split a
  single story's own 3-task chain across sprints.
- **Dependency graph honoured, not contradicted:** `T00` (live, read-only
  `ConversationID` verification, `depends_on: []`) → `T01` (primary strategy,
  `depends_on: [T00]`) → `T02` (fallback strategy, `depends_on: [T01]`) — read
  directly off the decomposer's own recorded `depends_on` edges, not
  reinterpreted.
- **No cross-sprint dependency needed.** The story's own two blocking
  dependencies (`REQ-SB-54-US-01`, `REQ-SB-55-US-01` — the Thread notes and their
  `participants`/`last_message_at` fields this story's fallback strategy reads)
  are both already `Done` (`SPRINT-048`, `SPRINT-049`) — fully satisfied before
  this sprint starts, not merely ordered against an in-flight sprint. No
  `depends_on_sprints` edge is required.
- **Sizing estimate:** ~3 tasks, S — matches this project's now-repeated
  "~3 tasks, S" precedent for a single, bounded story extending one already-`Done`
  mechanism with one new Job (`SPRINT-023`, `SPRINT-024`, `SPRINT-050`, all
  matched exactly at retro). `T02` (the fallback strategy, config-backed
  thresholds, two independent heuristic bars, plus the `BACKLOG.md`
  supersession re-check) is expected to be the heaviest by live-verification
  effort — it owns the largest share of locked ACs (`AC-02`, `AC-03`, `AC-05`,
  plus finalizing `AC-04`).

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-053 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-56-US-01](../UserStories/REQ-SB-56-US-01-meeting-capture-and-thread-linking.md) | Meeting Capture & Thread Linking — Link-to-Thread Job (ConversationID match, attendee-overlap/date-proximity fallback) | P1 | Done |

**Tasks in scope** (dependency order): `T00` (live meeting-item `ConversationID`
verification, `depends_on: []`) → `T01` (primary ConversationID-match strategy,
`depends_on: [REQ-SB-56-US-01-T00]`) → `T02` (attendee-overlap + date-proximity
fallback strategy, config-backed thresholds, `depends_on: [REQ-SB-56-US-01-T01]`).

---

## Dependencies / External Blockers

- **Depends on sprints:** None — `REQ-SB-54-US-01` (`SPRINT-048`) and
  `REQ-SB-55-US-01` (`SPRINT-049`), the two stories this story's linking
  strategies join against, are both already `Done`.
- `T00`'s own live COM probe is a genuine external/environmental prerequisite
  for `T01` (the primary strategy) — not a cross-sprint dependency, but the
  first task in this sprint's own dependency order, per the story's own
  Definition of Done.

---

## Out of Scope

- Rebuilding `meeting-capture` into a full 4-stage Pipeline (unlike
  `REQ-SB-55`'s treatment of email-capture) — this story is a narrower,
  additive Job extension only.
- The synthesis that reads a linked meeting into a Project's Glimpse —
  `REQ-SB-57`'s own scope, not yet `Ready`.
- To-Do capture — `REQ-SB-53-US-03` stays parked, untouched.
- `REQ-SB-42-US-01` (Real-time Agent Activity Pulses) — already grouped into
  its own `SPRINT-039`, out of scope for this pass.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — n/a this sprint; the architect's prior pass (2026-08-16) already covers both strategies, no new architectural fact emerged during build
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — n/a, no new ADR (both strategies are parameter/business-rule choices within `ADR-042`'s already-`Accepted` data model, per the architect's own pass)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. -->

### Sizing accuracy

- **Estimated:** ~3 tasks, S — **Actual:** 3 tasks, S, but with one genuine
  mid-flight blocker (`T01` went `Ready → Blocked → Ready` when `T00`'s own
  live verification came back negative) — **Takeaway:** the task *count*
  estimate held exactly (matching the repeated "~3 tasks, S" precedent this
  project has now confirmed four times — `SPRINT-023`, `SPRINT-024`,
  `SPRINT-050`, now `SPRINT-053`), but the estimate implicitly assumed
  `T00`'s live check would simply confirm what an earlier, less rigorous
  sample had already suggested (100/100 non-empty). It didn't. `T00` being
  deliberately kept as a REAL, independently-executed verification task
  (not a copy-paste of a referenced figure — the decomposer's own explicit
  call, see `REQ-SB-56-US-01`'s own Notes) is exactly what caught this
  before it became a silent correctness bug in `T01`'s own primary
  strategy, at the cost of one blocked-then-resumed cycle rather than a
  clean single pass.

### What worked

- **Keeping the live-verification task (`T00`) structurally separate from,
  and strictly before, the task that builds against its result (`T01`)**
  paid off directly this sprint: a real, independently-run COM probe
  overturned a previously-referenced "100/100" figure for a material 40.5%
  of real sampled items, entirely because `T00` was never allowed to treat
  that earlier figure as already-answered. Building `T01` first and
  discovering the gap live in production would have been far more
  expensive to unwind.
- **The config-not-hardcoded requirement was verifiable, not just
  assertable** — `T02`'s own Test step 5 (reconfigure the floor, observe
  the outcome actually change, reset) gave a concrete, mechanical way to
  prove the operator's own explicit "must be real config, never a Python
  constant" instruction was honored, rather than trusting a docstring or a
  visual code read alone.
- **Composing an already-existing generic primitive
  (`list_notes_in_kind_folder("Threads")`) instead of duplicating its glob
  mechanism inside a new, differently-named one (`list_thread_notes()`)**
  kept `T02`'s own new `vault_writer.py` surface small and consistent with
  this codebase's own "don't re-implement an existing scoped-enumeration
  pattern" convention, at the small cost of a scope-internal judgement
  call worth flagging in the task's own Implementation Log for a human
  spot-check.

### What didn't work

- **The story's own two open judgement calls (`ConversationID` feasibility,
  fallback thresholds) were both flagged and resolved BEFORE this sprint
  even started** (architect proposal → operator confirmation, both
  2026-08-16/17) — which meant this sprint's own build phase ran cleanly
  end-to-end, but it also means this sprint's retro can't independently
  confirm whether the operator's overnight best-guess standing instruction
  (used for `ESC-040`'s own Option (a) resolution) is a pattern that scales
  well across MORE overnight decisions, or whether this was a
  favorably-simple case (one binary choice, one safe/conservative option
  clearly dominating the alternative). Worth watching the next time this
  standing instruction fires on a genuinely closer call.

### Patterns to carry forward

- **A live, independently-executed verification task, kept structurally
  separate from and strictly before the task that depends on its result,
  is worth the extra task-count even when a plausible-looking prior figure
  already exists** — this is the second time this exact shape has caught a
  real discrepancy this project (the first being `EntryID`/`GlobalAppointmentID`
  non-uniqueness, `ESC-002`/`ESC-012`; `ConversationID`/`ESC-040` is the
  third distinct COM property in the same failure class, now on the same
  installation). Treat "a live COM/environment property behaves as
  expected" as something to re-verify per-property, not something to infer
  by analogy from a previously-verified sibling property.
- **When an operator instruction says "these must be real config values,
  not code constants," design the task's own verification step to actually
  reconfigure the value and observe the outcome change — not just confirm
  the value is read from a config module.** A `get_*` function that reads
  from a config file but is only ever called with the seeded default value
  during verification would not actually prove the comparison logic reads
  it fresh each time.

### Antipatterns to avoid

- **Don't assume a task's own literal wording ("no existing primitive does
  X") forecloses composing an existing, more general primitive that
  already covers the same ground** — re-read the actual codebase before
  assuming a gap is real; `T02`'s own Starting State said no primitive
  enumerated Threads specifically, which was true of a *dedicated,
  discoverably-named* one, but a generic scoped-folder enumeration already
  existed and could be composed instead of duplicated.

### Open follow-ups

- **`ESC-040`'s own provisional overnight Option (a) resolution still
  needs its own human spot-check** — not "was `T01`/`T02` built correctly
  against Option (a)" (they were, and this is verified), but "was Option
  (a) itself the right call, vs. investigating Option (b) — reading a
  recurring series' own master item for a usable `ConversationID` on the
  40.5% broken fraction — before shipping." See `REVIEW-QUEUE.md`.
- **A future story wiring `meeting_thread_link_config.py`'s `set_*`
  functions to a real HTTP endpoint / Settings UI surface** — deliberately
  out of `T02`'s own scope, flagged there and here so these thresholds
  don't stay hand-edit-the-JSON-file-only forever, mirroring
  `REQ-SB-66`'s own `agent_prompts` endpoint precedent (`ADR-044`) once
  there's a real need to tune them.

---

## Notes

**Sprint assembled 2026-08-17 (`/plan-sprints`).** Full pass over every story
file's `status:`/`sprint:` frontmatter confirmed exactly two `Ready` stories
exist: `REQ-SB-56-US-01` (`sprint: ""`, ungrouped — this sprint) and
`REQ-SB-42-US-01` (`sprint: SPRINT-039` already set at `/plan-tasks` time — not
ungrouped, out of scope for this pass, left untouched). Every other story is
`Draft`, `In Progress`, or `Done`.

`REQ-SB-56-US-01` enters `/plan-sprints` at `status: Ready`, `gate: clear`
(decomposer pass, 2026-08-17 — 5 ACs locked, 3 tasks created, `depends_on`
acyclic). No standing story-level flag to carry forward (unlike `SPRINT-050`'s
`REQ-SB-63-US-01`) — the story's own two open judgement calls (ConversationID
feasibility, fallback thresholds) were both fully resolved upstream before this
story reached `Ready`.

**Gate: `gate: clear` 2026-08-17.** No MUST-FLAG trigger fires for this
product-owner pass: (1) no material assumption — the single-story grouping and
the "no `depends_on_sprints` needed" conclusion are both read directly off the
decomposer's own recorded `depends_on` edges and `BACKLOG.md`'s own confirmed
`Done` status for `REQ-SB-54-US-01`/`REQ-SB-55-US-01`, not guessed; (2)
`REQ-SB-56` is not `<!-- Draft -->`/unfinalised; (3) product-owner does not
write ADRs — none created or changed by this pass; (4) no new `ESCALATIONS.md`
entry; (5) not oversized (3 tasks, S, matching three prior confirmed-accurate
3-task/S precedents — `SPRINT-023`, `SPRINT-024`, `SPRINT-050`); not a blocked
story — every task is `status: Ready`; no cross-sprint dependency had to be
introduced (the only two real upstream dependencies are already `Done`, not
merely ordered); (6) N/A (coder-only trigger); (7) no contradictory inputs; (8)
not genuinely ambiguous — one story, one sprint, no equally-valid alternative
partition exists. Advances `Draft → Ready`.

**BACKLOG.md updated:** `REQ-SB-56` row's Sprint column set to `SPRINT-053`,
Sprint Status set to `Ready`; new `SPRINT-053` row appended to the Sprint Status
table.

---

**Coder pass (2026-08-17) — `T00` built, `T01` Blocked.** `T00` (live,
read-only `ConversationID` verification) ran an independent probe against
the real Outlook installation and came back **negative** — contradicts the
100/100-non-empty figure this sprint's own scope was built against. `T00`
itself is `Done` (it performed its own job correctly). `T01` is set
`status: Blocked`, pending a human/architect decision on how the primary
strategy should treat recurring-occurrence meetings (~40% of the real
sample). `T02` was not touched (depends on `T01`, never started). Sprint
`status: Ready → In Progress`, `gate: clear → flagged`. Full finding:
`REQ-SB-56-US-01`'s own `## Notes`; `REVIEW-QUEUE.md`;
`ESCALATIONS.md` → `ESC-040`. `BACKLOG.md`'s `REQ-SB-56` row and this
sprint's own Sprint Status row updated to `In Progress`.

---

**Coder pass (2026-08-17) — `T01` built, `Done`.** Under the operator's
provisional overnight Option (a) resolution of `ESC-040` (see
`REQ-SB-56-US-01`'s own `## Notes`), `T01` was reset `Blocked → Ready` and
built this pass: `list_calendar_events` now returns a safe `conversation_id`
per event (`""` for both absent and non-string/COM-inaccessible values, via
a narrow `try/except` + `isinstance(str)` guard — never the naive
`list_recent_mail`-style `or ""` pattern); `meeting_classification.py` gained
`_link_to_thread_by_conversation_id` and the new `"thread_linked"` result
field. `AC-01` plus the new untagged ConversationID-safety check both
verified — one check against a real, live recurring-occurrence item on this
same installation (16/37 real in-window items, matching `T00`'s own recorded
broken subjects, all safely resolved to `""`, zero exceptions) and one
against a synthetic double pinning the exact ESC-040 failure shape. Full
verification detail in `T01`'s own `## Implementation Log`. `T01` is now
`status: Done`, `gate: clear` (no new coder-owned trigger fired). `T02`
(fallback strategy) has not started — sprint stays `status: In Progress`.
Sprint `gate` stays `flagged` — the story-level provisional-resolution
spot-check on `ESC-040` (whether Option (a) was the right call) remains
open in `REVIEW-QUEUE.md`, independent of and not blocking `T01`'s own
completion. `BACKLOG.md`'s `REQ-SB-56` row updated to reflect `T00`/`T01`
`Done`, `T02` not started.

---

**Coder pass (2026-08-17) — `T02` built, `Done`; sprint complete.** The
fallback attendee-overlap + date-proximity strategy landed, config-backed
per the operator's own explicit instruction (new
`app/business/meeting_thread_link_config.py` + sibling
`.second-brain/meeting_thread_link_config.json`, mirroring
`agent_prompts.py`/`working_mode_registry.py`'s own established
convention a further time over). All 5 of `REQ-SB-56-US-01`'s own locked
ACs are now verified across `T01`/`T02`; `REQ-SB-56-US-01` is `status:
Done`; `BACKLOG.md`'s `REQ-SB-56` row and this sprint's own Sprint Status
row are both updated to `Done`. Full build/verification detail in `T02`'s
own `## Implementation Log`. Sprint `status: In Progress → Done`,
`completed: "2026-08-17"`. `gate` stays `flagged` — not a new trigger from
this pass, but two standing, non-blocking breadcrumbs: (1) the operator's
own overnight provisional `ESC-040` Option (a) resolution still awaits its
own human spot-check (`REVIEW-QUEUE.md`); (2) this sprint's own drafted
`## Retrospective` (above) awaits human propagation into
`Implementation/Learnings.md`, per the standing human-only-harvest rule.
