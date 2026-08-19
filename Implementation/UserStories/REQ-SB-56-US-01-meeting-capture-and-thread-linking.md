---
id: REQ-SB-56-US-01
title: Meeting Capture & Thread Linking — Link-to-Thread Job (ConversationID match, attendee-overlap/date-proximity fallback)
requirement_ids: [REQ-SB-56]
requirement_section: "REQ-SB-56: Meeting Capture & Thread Linking"
phase: P1
status: Done
gate: flagged
gate_reason: "All 5 locked ACs verified across T00→T01→T02 (all now Done). Shipped under the operator's provisional overnight Option (a) resolution of ESC-040 (T00's negative live ConversationID finding) — that resolution's own spot-check (whether Option (a) was the right call vs. investigating Option (b) later) remains independently open in REVIEW-QUEUE.md, not blocking this story's own completion but not yet human-confirmed either. See ## Notes."
sprint: SPRINT-053
created: 2026-08-16
updated: 2026-08-17
---

# REQ-SB-56-US-01 — Meeting Capture & Thread Linking — Link-to-Thread Job (ConversationID match, attendee-overlap/date-proximity fallback)

## Story

**As a** Second Brain user
**I want** a meeting that's genuinely part of an email conversation to show
up connected to that conversation's Thread, and a meeting with no email
origin to still get a best-effort link when the evidence genuinely supports
one
**So that** meeting evidence and email evidence about the same topic read
together under the same Project, instead of the meeting reading as an
unrelated island

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-56: Meeting Capture & Thread
  Linking*. Extends the existing `meeting-capture` Worker with a
  `Link-to-Thread` Job, so a meeting that's genuinely part of an email
  conversation shows up connected to it. **Supersedes `REQ-SB-53-US-02`**
  (Meeting Pull/Tag/Link/Store split), same reasoning as `REQ-SB-55`'s
  relationship to `REQ-SB-53-US-01`. `REQ-SB-53-US-03` (To-Do) is NOT
  covered by this batch — it was not part of this discussion and stays
  parked.
- Raised 2026-08-16, same discussion as `REQ-SB-54`/`REQ-SB-55`.
- **This is an additive extension, not a rebuild.** Unlike `REQ-SB-55`
  (which replaces `email-capture` with a full Pipeline of Jobs), `REQ-SB-56`
  keeps `meeting-capture`'s existing Worker and fetch behavior completely
  unchanged (`app/business/meeting_classification.py::
  classify_recent_meetings`, confirmed by direct reading) and adds exactly
  one new Job on top. No new agent identity is retired or introduced by
  this story.
- **Linking strategy, in priority order — both parts flagged, not
  silently resolved:**
  1. **`conversation_id` match, if available.** A meeting invite sent
     inside an email thread may itself carry that thread's
     `ConversationID` as an Outlook item. If so, linking is free — same
     join as everything else in `REQ-SB-54`/`REQ-SB-55`, no separate
     matching logic. **Unconfirmed by the PRD itself, and confirmed
     FALSE by direct code inspection for this story:**
     `app/data_access/outlook_com.py::list_calendar_events` (this
     codebase's meeting-capture COM read, distinct from the email read)
     does NOT read `ConversationID` on the `AppointmentItem` today — only
     `id`/`subject`/`start`/`end`/`location`/`organizer`/`attendees` are
     read. Whether the live COM property actually exposes a usable,
     stable `ConversationID` on a real meeting/appointment item on this
     Outlook installation has not yet been checked live — this must be
     verified before this Job's primary strategy can be built, not
     assumed either way.
  2. **Attendee-overlap + date-range-proximity heuristic, as fallback** —
     for meetings created directly (not as a reply within a conversation),
     which structurally can't share a `conversation_id` with anything.
     **Exact overlap/proximity thresholds left to the architect/decomposer
     to propose** — this is a genuine judgement call the operator did not
     pin down numerically during discussion.
- **Once linked, the meeting feeds the same Project Glimpse the linked
  Thread feeds (`REQ-SB-57`)** — this requirement only covers the linking
  itself, not the synthesis that reads it.
- **False-positive links are worse than no link** — a mis-linked meeting
  would corrupt a Project's own Glimpse. The fallback heuristic must be
  conservative: a meeting that doesn't clear a real confidence bar is left
  explicitly unlinked, never guessed into a wrong Thread.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: A meeting invite sent as a reply within an existing Thread links via the primary strategy

```gherkin
Given a real meeting invite was sent as a reply within an already-captured
    email Thread, and T00's live COM check has confirmed the meeting
    item's ConversationID is usable on this Outlook installation
When that meeting is captured by the existing meeting-capture Worker
Then the resulting Meeting note's `thread` frontmatter field is populated
    with that Thread's own conversation_id, linking the Meeting note to
    the Thread's note via the primary ConversationID-match strategy
```
<!-- AC-ID: REQ-SB-56-US-01-AC-01 -->

### Scenario 2: A meeting with no email-thread origin gets a best-effort fallback link

```gherkin
Given a real meeting was created directly (not as a reply within any
    captured email conversation), and its post-self-exclusion attendee set
    clears the fallback heuristic's attendee-overlap bar (>=2 shared
    attendees with an existing Thread's own accumulated participants, OR
    exactly 1 shared attendee that is the entirety of the smaller of the
    two sets) AND its start timestamp falls within the fallback's
    date-proximity window (7 calendar days, either direction) of that
    Thread's own last_message_at
When that meeting is captured
Then the resulting Meeting note's `thread` frontmatter field is populated
    with that Thread's own conversation_id, linking the Meeting note to
    the Thread via the fallback heuristic
```
<!-- AC-ID: REQ-SB-56-US-01-AC-02 -->

### Scenario 3: A meeting that doesn't clear the fallback's confidence bar is left explicitly unlinked

```gherkin
Given a real meeting was created directly, with no email-thread origin,
    and for every existing Thread its attendee-overlap and/or
    date-proximity falls short of the fallback heuristic's own bars (or a
    genuine tie survives both tie-break rules)
When that meeting is captured
Then the resulting Meeting note's `thread` frontmatter field is left at
    its reserved empty string — explicitly unlinked, never populated with
    the closest-but-still-weak-matching Thread's own conversation_id
  And no false-positive link is created
```
<!-- AC-ID: REQ-SB-56-US-01-AC-03 -->

### Scenario 4: meeting-capture's existing fetch behavior is unchanged

```gherkin
Given the existing meeting-capture Worker's fetch/classify/write behavior
    (calendar-event fetch, self-exclusion, customer derivation via
    majority vote, attendee Person-note linking, customer hub linking,
    Meeting note create/top-up)
When this story's new Link-to-Thread Job is added on top
Then every one of those existing behaviors continues to produce the same
    outputs it did before this story, for a meeting that matches no
    Thread by either strategy — this is a purely additive Job, not a
    replacement of any existing stage
```
<!-- AC-ID: REQ-SB-56-US-01-AC-04 -->

### Scenario 5: REQ-SB-53-US-02 is marked superseded, not reworked

```gherkin
Given this story has shipped
When BACKLOG.md's REQ-SB-53 row is inspected
Then REQ-SB-53-US-02 (Meeting Pull/Tag/Link/Store split) is marked
    superseded/Parked by REQ-SB-55/REQ-SB-56, not reworked into this
    story's own Link-to-Thread Job
```
<!-- AC-ID: REQ-SB-56-US-01-AC-05 -->

## Affected Screens

None — backend only. No `html-prototype/` screen renders a Meeting note's
link to a Thread today; this story only extends the vault-level Meeting note
schema, consistent with `REQ-SB-54-US-01`'s own "note content is authored/
read in Obsidian" convention.

## Dependencies

- **Blocked by:** `REQ-SB-54-US-01` (Vault Knowledge Model Redesign) —
  Thread notes must exist (and their own `ConversationID` join must be
  verified stable) before anything can link to them. **Correction,
  decomposer pass 2026-08-17:** this line was written when
  `REQ-SB-54-US-01` was still `Draft`/`gate: flagged`, describing its
  status AS OF WHEN THIS STORY WAS WRITTEN (2026-08-16). Confirmed via
  `BACKLOG.md` this pass: `REQ-SB-54-US-01` is now `Done` (`SPRINT-048`,
  gate: clear) — this dependency is fully satisfied, no longer blocking.
- **Blocked by:** `REQ-SB-55-US-01` (Email Capture & Threading Pipeline) —
  the actual pipeline that creates Thread notes this story's primary
  linking strategy joins against, and (per the architect's 2026-08-16
  pass) the sole writer of the `participants`/`last_message_at` Thread
  fields the fallback strategy reads. **Correction, decomposer pass
  2026-08-17:** this line was written when `REQ-SB-55-US-01` was still
  `Draft`, describing its status AS OF WHEN THIS STORY WAS WRITTEN.
  Confirmed via `BACKLOG.md` this pass: `REQ-SB-55-US-01` is now `Done`
  (`SPRINT-049`, gate: flagged — ADR-043 human review, unrelated to this
  story) — this dependency is fully satisfied, no longer blocking.
- **Related to:** `REQ-SB-08` (Meeting notes captured from calendar sync,
  `Done`) — the existing `meeting-capture` Worker this story extends,
  unmodified in its own fetch/classify/write behavior.
- **Related to:** `REQ-SB-57-US-01` (Project & Customer Status Synthesizer
  Agents) — consumes this story's link as Project evidence; this story only
  produces the link, it does not read it back into any synthesis.
- **Supersedes:** `REQ-SB-53-US-02` (Meeting Pull/Tag/Link/Store split,
  `Parked`) — not reworked; `BACKLOG.md`'s `REQ-SB-53` row already notes
  this. `REQ-SB-53-US-03` (To-Do) stays parked, untouched by this story.
- **External:** live verification of whether meeting/appointment COM items
  on this Outlook installation actually expose a usable `ConversationID` —
  a genuine technical prerequisite for the primary linking strategy, not a
  code change.

## Constraints

- **`meeting-capture`'s existing fetch/classify/write behavior must not
  regress** (Scenario 4) — this is a purely additive Job.
- **False-positive links are worse than no link** — the fallback heuristic
  must be conservative; a meeting that doesn't clear its confidence bar is
  left unlinked, never force-linked to the closest weak match (Scenario 3).
- **The primary (ConversationID) strategy's own real-world feasibility on
  this Outlook installation is unverified** — do not build the fallback
  heuristic as though the primary strategy is guaranteed usable; verify
  live first (see Notes/REVIEW-QUEUE.md).
- **Exact attendee-overlap/date-proximity thresholds.** ~~Not locked by
  this story — do not silently pick specific numbers at `/plan-tasks`; the
  human decision must be resolved first.~~ **Resolved, decomposer pass
  2026-08-17:** the architect's proposal (≥2 shared attendees / 1:1
  carve-out / 7-day window) was operator-confirmed 2026-08-17 as the
  working default (see `## Notes`) and is now locked into `T02`, as real
  config values, never hardcoded Python constants (see `T02`'s own task
  file).
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).

## Implementation Tasks

<!-- Decomposer's own table (/plan-tasks step 2, 2026-08-17) — supersedes
the analyst-authored starting point above. -->

| ID | Type | Task | Files / Area | Task File | depends_on |
|---|---|---|---|---|---|
| REQ-SB-56-US-01-T00 | verification | Live, read-only COM check: does a real Outlook meeting/appointment item expose a usable ConversationID on this installation? Result recorded in this story's own `## Notes`. | `app/data_access/outlook_com.py` (read-only); this story's `## Notes` | `../Tasks/REQ-SB-56-US-01-T00-meeting-conversationid-verification.md` | — |
| REQ-SB-56-US-01-T01 | backend | `Link-to-Thread` Job — primary ConversationID-match strategy (`list_calendar_events` code-gap fix + Meeting `thread` field write) | `app/data_access/outlook_com.py`, `app/business/meeting_classification.py` | `../Tasks/REQ-SB-56-US-01-T01-link-to-thread-primary-strategy.md` | T00 |
| REQ-SB-56-US-01-T02 | backend | `Link-to-Thread` Job — attendee-overlap + date-proximity fallback strategy, config-backed thresholds (new sibling store, not hardcoded); BACKLOG.md REQ-SB-53 supersession re-check | `app/business/meeting_classification.py`, new `app/business/meeting_thread_link_config.py`, `app/data_access/vault_writer.py`, `BACKLOG.md` | `../Tasks/REQ-SB-56-US-01-T02-link-to-thread-fallback-strategy.md` | T01 |

AC coverage: `AC-01` → `T01`. `AC-02`/`AC-03` → `T02`. `AC-04` (regression)
verified at `T01` (partial) and finalized at `T02` (full, both strategies
landed). `AC-05` (BACKLOG supersession) → `T02`. Dependency graph is a
single linear chain `T00 → T01 → T02`, acyclic.

## Definition of Done

- [x] `T00` (meeting ConversationID live verification) is complete and its
      result is recorded in this story's `## Notes`, before `T01` is built
- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists) — n/a, test tooling still pending across this whole project; every locked AC verified manually per `Pipeline.md`'s manual-mode default
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Rebuilding `meeting-capture` into a full 4-stage Pipeline** (unlike
  `REQ-SB-55`'s treatment of email-capture) — this story is a narrower,
  additive Job extension only.
- **The synthesis that reads a linked meeting into a Project's Glimpse** —
  `REQ-SB-57`'s own scope.
- **To-Do capture** — `REQ-SB-53-US-03` stays parked, untouched.
- **Locking the exact attendee-overlap/date-proximity thresholds** —
  genuinely open, flagged for a human/architect decision (see Notes).

## Notes

**Prototype parity:** N/A — no `html-prototype/` screen is touched; see
Affected Screens.

**Why `gate: flagged` (MUST-FLAG trigger 8, fired twice):**

1. **Meeting-item `ConversationID` exposure is unconfirmed, and the PRD
   itself says so verbatim:** "Unconfirmed, flag for the architect: does
   this codebase's meeting-capture COM read... actually expose
   `ConversationID` on meeting/appointment items? Not yet checked — verify
   live before relying on it, same spirit as `REQ-SB-54` point 9's
   verification requirement." Confirmed directly by this analyst pass, by
   reading the real `list_calendar_events` code: it currently does NOT
   read `ConversationID` at all. Whether the live COM property would
   actually return a usable value if added has not been tested. This is a
   real, unresolved technical premise the primary linking strategy depends
   on entirely.
2. **The fallback heuristic's exact thresholds are a genuine, unpinned
   judgement call**, and the PRD itself says so verbatim: "Exact
   overlap/proximity thresholds left to the architect/decomposer to
   propose; this is a genuine judgement call the operator did not pin down
   numerically during discussion — flag rather than guess a specific
   threshold silently." No PRD text, code precedent, or resolved
   clarifying answer favors one specific threshold over another.

No other trigger fired: no material assumption was made beyond the two
explicitly-PRD-flagged items above; `REQ-SB-56` carries no `<!--
Draft -->` marker; no ADR was created by this pass (trigger 3 n/a); no
`ESCALATIONS.md` entry was written — both open items are PRD-acknowledged,
forward technical-verification/design questions, not backward pipeline
steps or unclear PRODUCT requirements (trigger 4 n/a); not oversized — one
additive Job over one already-`Done` Worker (trigger 5 n/a); no
contradictory PRD inputs (trigger 7 n/a).

**What to do next:** run the live meeting-item `ConversationID` check
(`T00`) against the real Outlook installation and record the result here;
separately, get the architect/decomposer to propose specific
overlap/proximity thresholds at `/plan-tasks`, with the operator confirming
before `T02` is built. See `REVIEW-QUEUE.md` for both action items.

gate: flagged 2026-08-16 — trigger-8 fired twice (meeting-item
`ConversationID` exposure unconfirmed on this installation; fallback
thresholds genuinely unpinned). A `REVIEW-QUEUE.md` entry has been added.

---

**Architect pass (2026-08-16) — `/plan-tasks` step 1:**

- **Architecture scope: §"Meeting → Thread Linking — ConversationID
  Primary Strategy, Attendee-Overlap/Date-Proximity Fallback"**
  (`Implementation/Architecture/architecture.md`, under `## Data Model`,
  appended directly after "Vault Knowledge Model Redesign — Threads,
  Manual Captures, OKF-Conformant Customer & Project Directories"),
  §`ADR-042` (unchanged, referenced — no new ADR, see below). The coder
  is bounded by that section for both `T01` (primary strategy) and `T02`
  (fallback strategy).
- **No new ADR.** Both the primary-strategy code gap (add
  `conversation_id` to `list_calendar_events`'s returned dict) and the
  fallback heuristic's thresholds are parameter/business-rule choices
  made WITHIN `ADR-042`'s already-`Accepted` data model — neither
  introduces a new tool, framework, or structural boundary. The two new
  Thread frontmatter fields the fallback needs (`participants`,
  `last_message_at`) are ordinary additive scalar/list-of-string values
  the existing frontmatter writer already round-trips natively — no new
  primitive, no reopening of `ADR-042` or `REQ-SB-54-US-01`/T02's own
  locked ACs. Trigger-3 does not fire from this pass.
- **PROPOSAL — awaiting operator confirmation, NOT yet final.** Concrete
  fallback-strategy definition (full reasoning and grounding in
  `architecture.md`'s new "Meeting → Thread Linking..." section):
  - **Attendee sets:** meeting attendees (`outlook_com._resolve_attendees`)
    vs. the candidate Thread's own accumulated `participants` (a NEW
    Thread frontmatter field this story or `REQ-SB-55` must add — see
    below), both with the vault owner's own `settings.self_email`
    excluded first (mirrors `meeting_classification._exclude_self`).
  - **Overlap bar:** clears if **≥2 shared attendees**, OR **exactly 1
    shared attendee that is the ENTIRE smaller of the two attendee
    sets** (covers a genuine 1:1-meeting-matches-1:1-thread case without
    weakening the ≥2 bar for any larger meeting/thread). A single shared
    contact out of a larger list is NOT sufficient — one recurring
    point-of-contact legitimately appears across many unrelated
    meetings/threads for the same account.
  - **Date-range-proximity bar:** meeting `start` within **7 calendar
    days (either direction)** of the candidate Thread's own
    most-recently-captured-message timestamp (a second NEW Thread
    frontmatter field, `last_message_at`). Grounded in a real data point,
    not a round number: `REQ-SB-54-US-01`'s own live `ConversationID`
    verification found a real 3-message thread ("G42/Data Lake RFP
    Discussion") spanning exactly 7 days end-to-end — the fallback reuses
    that same order of magnitude as this vault's own observed
    "still-the-same-live-topic" cadence.
  - **Both bars required (AND).** Either failing → explicitly unlinked
    (Scenario 3), never a forced weak match.
  - **Tie-break** across multiple qualifying Threads: higher overlap
    count wins; if still tied, smaller date gap wins; if still tied on
    both, leave unlinked rather than guess.
  - **Prerequisite, flagged for the decomposer:** `participants`/
    `last_message_at` don't exist on Thread notes yet
    (`REQ-SB-54-US-01`/T02's baseline is `type`/`conversation_id`/
    `tags` only). Natural owner is `REQ-SB-55`'s own `Thread-Match/Merge`
    Job (it already writes Thread frontmatter on every message); if this
    story's own `/plan-tasks` pass lands before that Job is built, `T02`
    must add both fields to `vault_writer.py`'s Thread primitives
    directly instead. The decomposer must pick one explicitly, not leave
    it implicit.
- **Grounding, not arbitrary round numbers:** the ≥2-shared-attendee floor
  is chosen specifically to reject the single-recurring-contact false
  positive (this vault is a small, account-based B2B context — the same
  1-2 people recur across many unrelated meetings/threads for one
  customer, so 1 shared attendee alone is a customer-level signal, not a
  thread-level one); the 1:1 carve-out exists because a bare ≥2 floor
  would structurally exclude every real 1-external-attendee sales call,
  which this vault's own Meeting capture code (`_derive_meeting_customer`,
  majority-vote-among-attendees) already treats as a normal case, not an
  edge case. The 7-day proximity window reuses this vault's own real,
  live-verified thread cadence (the G42 RFP thread) rather than an
  unrelated industry rule of thumb.
- **Gate stays `flagged` — this pass does NOT resolve trigger-8.** The
  numbers above are the architect's proposal only; the operator must
  confirm or correct them before `T02` (fallback strategy) is built. See
  `REVIEW-QUEUE.md` for the updated pointer.

---

**Operator confirmation, 2026-08-17:** the architect's fallback-threshold
proposal above (≥2 shared attendees, OR exactly 1 when that's the whole
smaller attendee set; 7-day date-range proximity; both required; tie-break
by overlap then date-gap then unlinked) is accepted as the working
default — it is grounded in this vault's own real observed data (the
G42 RFP thread), not an arbitrary guess, and the operator authorized
proceeding on well-grounded architect proposals rather than blocking on
each one individually overnight (2026-08-17, standing instruction: find
genuinely urgent questions now, best-guess everything else). `/plan-tasks`
step 2 (decomposer) may now proceed and lock `T02` against these numbers.

**Additional standing constraint for `/plan-tasks`/`/implement-sprint`
on this story (operator, 2026-08-17):** the attendee-overlap floor (2),
the 1:1 carve-out, and the 7-day date-proximity window must be real,
accessible config values (not Python constants) — same config/settings
surface convention already established elsewhere in this codebase
(`agent_prompts.json`, `working_mode_registry.py`), so they can be tuned
later without a code change.

`gate` reset to `clear` — see `REVIEW-QUEUE.md` for the corresponding
update.

---

**Decomposer pass (2026-08-17) — `/plan-tasks` step 2:**

- **5 ACs locked**, tightened for buildability and tagged
  `REQ-SB-56-US-01-AC-01` through `-AC-05` (see `## Acceptance Criteria`
  above) — none marked `locked: false`; no gap-filling assumption was
  needed beyond what the architect's already-confirmed pass already
  settled.
- **3 tasks created** (flat root, `Implementation/Tasks/`): `T00`
  (live verification, no code), `T01` (primary strategy), `T02` (fallback
  strategy). `depends_on` is a single linear chain `T00 → T01 → T02` —
  acyclic. Every locked AC has at least one AC-tagged manual verification
  step across `T01`/`T02`'s own `## Tests` (`AC-01`→`T01`; `AC-02`/`AC-03`
  →`T02`; `AC-04` partially at `T01`, finalized at `T02`; `AC-05`→`T02`).
- **`T00` is deliberately NOT treated as already answered**, even though
  `architecture.md`/`REVIEW-QUEUE.md`/`BACKLOG.md` all already reference
  an apparent prior finding ("100/100 sampled real calendar items carried
  a non-empty ConversationID", attributed to the architect's own
  2026-08-16 pass) — that figure has never been formally recorded inside
  THIS story's own `## Notes`, which the Definition of Done explicitly
  requires before `T01` is built. `T00` stays the real first task in
  dependency order; its own task file requires an independently-executed,
  read-only COM probe and a recorded result here, not a copy-paste of the
  referenced figure. If `T00`'s own result contradicts the referenced
  100/100 figure, `T00`'s own Constraints require a `REVIEW-QUEUE.md` +
  `ESCALATIONS.md` entry and `T01` stays blocked — not a silently
  reinterpreted scope.
- **Dependencies corrected** (see `## Dependencies` above): both
  `REQ-SB-54-US-01` and `REQ-SB-55-US-01` are confirmed `Done` in
  `BACKLOG.md` as of this pass (`SPRINT-048`/`SPRINT-049`) — the story's
  own original Dependencies text was accurate as of 2026-08-16 (both were
  still `Draft`/in-flight when this story was authored) but is now stale;
  corrected in place rather than silently left misleading. Neither story
  being `Done` reopens anything already shipped — `T02` only READS the
  `participants`/`last_message_at` fields `REQ-SB-55-US-01-T03` already
  writes; no cross-story `depends_on` edge is added onto an already-`Done`
  task (nothing here is still pending on that side).
- **`T02`'s own config surface, per explicit operator instruction
  (2026-08-17):** the attendee-overlap floor (2), the 1:1 carve-out, and
  the 7-day date-proximity window are scoped as a NEW sibling-store config
  module (`app/business/meeting_thread_link_config.py` +
  `.second-brain/meeting_thread_link_config.json`), mirroring
  `agent_prompts.py`/`working_mode_registry.py`'s own established
  convention — never Python constants inside `meeting_classification.py`.
  `T02`'s own task file states this explicitly in both its Objective and
  Constraints, with a dedicated Test step proving the comparison logic
  actually reads the configured value (not a baked-in literal). **No new
  HTTP endpoint or Settings UI surface is scoped for editing these
  values** — no locked AC in this story tests threshold-editing (see
  `## Non-Goals`), so wiring a settable-via-API surface beyond the
  in-process `get_*`/`set_*` functions would be scope beyond what this
  story's own 5 Scenarios need. Flagged explicitly in `T02`'s own `## Out
  of Scope` so a human isn't surprised the values aren't yet editable from
  the UI — a natural follow-up story, mirroring `REQ-SB-66`'s own
  `agent_prompts` endpoint precedent, can wire this in once there's a real
  need to tune without hand-editing the JSON file directly.
- **Status: `Draft → Ready`.** All three gate criteria hold: (a) every AC
  is locked; (b) every locked AC has ≥1 tagged verification step; (c)
  `depends_on` is acyclic. **`gate: clear`** — no MUST-FLAG trigger fired
  on this pass: no new material assumption (the two open judgement calls
  were already resolved upstream by the architect/operator); no `<!--
  Draft -->` requirement relied on; no ADR created/changed by this pass;
  no `ESCALATIONS.md` entry written; no oversized task (each of `T00`/
  `T01`/`T02` is a single-session unit); every locked AC is verifiable
  (`T01`/`T02`'s own Tests sections give each a concrete, observable
  frontmatter/return-value check); no contradictory inputs; no genuinely
  unclear/multiple-equally-valid breakdown (the architecture section
  already specifies one concrete shape).
- `REVIEW-QUEUE.md`: the existing `REQ-SB-56-US-01` entry is closed out
  (superseded by this pass — thresholds are now locked, not merely
  proposed) with a pointer to this update; no NEW `REVIEW-QUEUE.md` entry
  is opened by this pass. No `ESCALATIONS.md` entry written.
- All three task files are written at `status: Ready` (in lockstep with
  this story's own `Draft → Ready` transition), per the standing
  status-lockstep rule — not left at `Draft`, which would stall
  `/implement-sprint`'s pickup.

gate: clear 2026-08-17 — no decomposer-owned trigger fired (see full
reasoning above); this story and its 3 tasks are eligible for
`/plan-sprints`.

---

**Product-owner pass (2026-08-17) — `/plan-sprints`.** Assigned to a new
single-story sprint, `SPRINT-053` — no other `Ready`, ungrouped story existed
to group alongside it (the only other `Ready` story, `REQ-SB-42-US-01`, already
carries `sprint: SPRINT-039`, assigned at `/plan-tasks` time). No
`depends_on_sprints` edge needed — both of this story's real upstream
dependencies (`REQ-SB-54-US-01`, `REQ-SB-55-US-01`) are already `Done`. `gate:
clear` — no MUST-FLAG trigger fired; full reasoning in `SPRINT-053`'s own
Notes. `BACKLOG.md`'s `REQ-SB-56` row updated (Sprint → `SPRINT-053`, Sprint
Status → `Ready`).

---

**`T00` live verification, 2026-08-17 — NEGATIVE, contradicts the referenced
100/100 figure.** An independent, real, read-only COM probe was run this
session (not a copy of the architect's own 2026-08-16 figure) against the
real Outlook desktop session, mirroring `list_calendar_events`'s own exact
`GetDefaultFolder(9)` / `IncludeRecurrences = True` / `[Start]` window
mechanics (`days_back=7, days_ahead=14`, the function's own defaults):

- **Sample size: 37** real calendar items in the live window
  (2026-08-10 .. 2026-08-31).
- **22/37 (59.5%) carried a genuine, usable, distinct `ConversationID`
  string.** Example: subject "Summary preparation for Masdar workshop",
  start `2026-08-10 10:00:00+00:00`, `conversation_id =
  'E20C7692EED748E082340F21ED08451A'`. All 22 non-empty values observed
  were mutually distinct (no collision across different meetings) — looks
  stable/plausible as a join key **for this subset**.
- **15/37 (40.5%) — a material fraction, not a rounding-error edge case —
  returned a broken, unusable value.** `getattr(item, "ConversationID",
  None)` resolves to a bound-method object, not a string, for these items
  (`bool()` of that object is truthy, so the naive `getattr(item,
  "ConversationID", None) or ""` pattern `list_recent_mail` already uses
  for mail would silently pass a non-string garbage value through as if
  it were a real conversation id). Explicitly invoking it raises a COM
  error (`-2147352573, 'Member not found.'`). A follow-up raw-MAPI
  `PropertyAccessor.GetProperty("http://schemas.microsoft.com/mapi/
  proptag/0x3013001F")` (`PR_CONVERSATION_ID`) read was also attempted
  directly against the same 15 items as a possible workaround — it also
  fails on every one of them (`-2147352571, 'Type mismatch.'`). **Every
  one of these 15 broken items has `IsRecurring = True` and
  `RecurrenceState` 2 (`olApptOccurrence`) or 3 (`olApptException`) — i.e.
  every one is an individual occurrence of a recurring series, expanded
  by `IncludeRecurrences = True`, the exact mechanism
  `list_calendar_events`'s own docstring says is required to turn a
  recurring series into individual occurrence items.** 5 distinct real
  recurring series are represented in the broken set ("Weekly Forecast l
  Strategic Clients", "Weekly Forecast l Major Clients", "Discuss with
  Mousa", "Kimi 3 - Foundry PoC - Integration CORE42-Weekly Checkpoints",
  "Standup - AZDL Readiness", "PSS Team Get together").
- **This is the third independent, live-confirmed instance on this same
  Outlook installation of a per-item COM identity/relationship property
  being unreliable specifically on `IncludeRecurrences`-expanded
  occurrence items** — `EntryID` (`ESC-002`) and `GlobalAppointmentID`
  (`ESC-012`) both independently failed the same class of live test
  before this one; `ConversationID` is now a third, and behaves
  differently again (not merely non-unique like the first two, but
  outright non-string/inaccessible).
- **Verdict: `ConversationID` is NOT usable as this task's Constraints
  define "usable"** (empty/absent/unstable on a material fraction of real
  sampled items — 40.5% clears that bar) — this **contradicts** the
  100/100-non-empty figure the architect's 2026-08-16 pass referenced
  (that earlier pass evidently did not include a real recurring-occurrence
  item in its own sample, or did not detect the non-string return value
  the same way this probe's explicit `callable()`/invocation check did).
  Per this task's own Constraints, `T01` is **not** silently narrowed or
  re-scoped by this task — see `REVIEW-QUEUE.md` and `ESCALATIONS.md` →
  `ESC-040` for the full finding and the open question for a human/
  architect decision. `T01` is left `status: Blocked`.

gate: flagged 2026-08-17 (T00) — trigger-7 fired (contradictory inputs:
this story's own architecture section and gate history are grounded in a
100/100-non-empty premise this task's own live, independent check
disproved for a material 40.5% of the real sample). See
`REVIEW-QUEUE.md` / `ESCALATIONS.md` → `ESC-040`.

---

**Operator resolution of `ESC-040`, 2026-08-17 (overnight, best-guess
authorization — no urgent human decision was available, per the
operator's own standing instruction).** Took `ESC-040`'s own listed
**Option (a):** a non-string/COM-inaccessible `ConversationID` (the
40.5% recurring-occurrence fraction `T00` found) is treated identically
to an absent one — never fabricated into a link, the meeting simply
falls through to `T02`'s own fallback strategy untouched. The primary
strategy still fully covers the 59.5% single-occurrence majority.
**Option (b)** (investigating whether the recurring series' own master
item recovers a usable id for the other 40.5%) was deliberately NOT
attempted — a genuine scope/investigation question, left open for the
operator's own morning review rather than guessed into either direction.
`REQ-SB-56-US-01-T01` reset `Blocked → Ready` with one concrete scope
addition (a safe `""`-on-failure guard around the `ConversationID` read,
replacing `list_recent_mail`'s naive pattern which would otherwise pass
the broken value through as truthy) — see the task file's own updated
Constraints/Tests/AC sections. `gate` stays `flagged` (provisional,
non-blocking) pending morning spot-check; `ESC-040` stays `Open` in
`ESCALATIONS.md` (not marked Resolved — this is a provisional overnight
call, not a genuine operator confirmation) with an `Update` note pointing
here. See `REVIEW-QUEUE.md` for the corresponding update.

---

**Coder pass (2026-08-17) — `T02` built, `Done`; story complete.** The
fallback attendee-overlap + date-proximity strategy landed:
`meeting_thread_link_config.py` (new, `.second-brain/
meeting_thread_link_config.json`-backed) holds the attendee-overlap floor
/ 1:1 carve-out toggle / date-proximity window as real, `get_*`/`set_*`
config values — never hardcoded, proven live by reconfiguring the floor
and observing the outcome change. `meeting_classification.py` gained
`_link_to_thread_by_fallback_heuristic`, called only when `T01`'s primary
strategy left a meeting unlinked; both bars (AND), tie-break by overlap
then date-gap, unresolved tie leaves the meeting unlinked. All 5 locked
ACs now verified: `AC-01` (`T01`), `AC-02`/`AC-03` (`T02`, both bar
clauses, both failure directions, and the genuine-tie case all directly
exercised), `AC-04` (finalized — full regression pass with both
strategies active produces the same `created`/`customer`/`linked`/
`attendees` outputs as before this story), `AC-05` (`BACKLOG.md`'s
`REQ-SB-53` row re-confirmed already superseded/Parked, no edit needed).
Full verification detail in `T02`'s own `## Implementation Log`.

**Status: `Done`.** All 3 tasks (`T00`→`T01`→`T02`) are `Done`; every
locked AC is verified; no Constraint was violated. **`gate: flagged`** —
carried forward, not newly introduced by this pass: the operator's own
overnight provisional `ESC-040` Option (a) resolution (treating a
non-string/COM-inaccessible `ConversationID` identically to an absent
one) still awaits its own human spot-check in `REVIEW-QUEUE.md`. This
does not block the story's own completion — `T01` built the safe
fallthrough Option (a) implies, and `T02`'s own fallback strategy is
exactly what a primary-strategy miss (whether from a genuinely absent
`conversation_id` or from ESC-040's broken-recurring-occurrence case)
falls through to. `BACKLOG.md`'s `REQ-SB-56` row and `SPRINT-053` are
both updated to `Done` by this same pass.

gate: flagged 2026-08-17 — carried forward from `T01`'s own still-open
`ESC-040` spot-check (`REVIEW-QUEUE.md`); no NEW MUST-FLAG trigger fired
on this `T02` coder pass itself (see `T02`'s own `gate_reason`).
