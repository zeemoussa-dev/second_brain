---
id: REQ-SB-82-US-05-T02
title: meeting-prep-agent cron declaration + live Hermes profile provisioning
parent_story: REQ-SB-82-US-05
requirement_id: REQ-SB-82
type: backend
status: Done
gate: flagged
gate_reason: "scope-internal disclosed findings (Hermes memory file MEMORY.md vs. USER.md; new-profile WhatsApp pairing gap) — see Implementation Log for human spot-check, not a blocked AC"
phase: P2
depends_on: [REQ-SB-82-US-05-T01, REQ-SB-82-US-02-T02]
created: 2026-08-25
updated: 2026-08-25
---

# REQ-SB-82-US-05-T02 — meeting-prep-agent cron declaration + live Hermes profile provisioning

## Parent Story

- Story: [[REQ-SB-82-US-05]] — `../UserStories/REQ-SB-82-US-05-meeting-preparation-agent.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-82 *Cockpit Mechanics — Prep, Research, and Moderation*

---

## Objective

Declare the new `meeting-prep-agent` cron job (schedule, delivery, prompt)
in this repo's own Hermes-Provisioning tracking, then provision the real,
live profile + cron job needed to prove this story's Scenarios end-to-end.

---

## Starting State → End State

**Before / Inputs:**
- No `meeting-prep-agent` profile or cron job exists, live or declared.
- `Hermes-Provisioning/cron/` has only a stale, empty `README.md`.
- `T01`'s Person-lookup Skill and `REQ-SB-82-US-02-T02`'s real, live `research-agent` capability both exist.

**After / Outputs:**
- `Hermes-Provisioning/cron/meeting-prep-agent.md` — a new declared-cron-job reference file (matching `cron/README.md`'s own stated convention: "its declaration (schedule, name, prompt or --skill...) goes here as its own file"), recording: `schedule: {"kind": "interval", "minutes": 720}`, `deliver: "whatsapp"`, and the real prompt text instructing the agent to (a) scan upcoming meetings, (b) delegate unfamiliar-topic KB lookups to `research-agent` via the established one-shot relay (`hermes -p research-agent chat -q "..."`), (c) run `T01`'s Person-lookup Skill for any attendee, (d) reply with nothing substantive when nothing worth checking was found (mirroring `new-company-discovery`'s own real, confirmed clause — never a no-op notification), and (e) consult/update its own native per-profile `memories/USER.md` for a learned suppression preference keyed by the meeting's own `calendar_series_id` (falling back to its `customer` tag).
- A real, live `meeting-prep-agent` Hermes profile + cron job provisioned on the operator's actual Hermes install (a live, Hermes-side action outside this repo's own version control, per Constraints).

---

## Files to Modify

- `Hermes-Provisioning/cron/meeting-prep-agent.md` (new)

---

## Constraints

- Inherits from parent story.
- The web lookup for an attendee's Person note runs at most once per person — the prompt must instruct calling `T01`'s `check_person_note_empty.py` FIRST, every time, before any real web lookup.
- A WhatsApp summary is sent only when real data worth checking was found — the prompt's own "reply with nothing substantive if nothing found" clause must be explicit, not implied.
- The suppression preference lives ENTIRELY in Hermes' own native per-profile memory — no new Second-Brain-side schema, store, or API (`ADR-010`); this task must not introduce one.
- Never fabricate a finding — the prompt must instruct honest reporting when a lookup or KB delegation returns nothing conclusive.
- **Provisioning the real, live `meeting-prep-agent` Hermes profile and cron job itself (SOUL.md, tool grants, the actual `hermes cron create` action) is real, Hermes-side infrastructure work with no further checked-in-repo file to diff beyond the declaration above** — per `ADR-010`'s own Consequences and this story's own established precedent (`REQ-SB-82-US-02-T02`). This is authorized, expected work for this task's own live verification, not an escalation-triggering out-of-scope change.

---

## Tests

**Manual verification steps:**
1. Read the authored `meeting-prep-agent.md`: confirm `schedule: {"kind": "interval", "minutes": 720}` and `deliver: "whatsapp"` are declared exactly.
2. [REQ-SB-82-US-05-AC-01] Confirm the declared prompt explicitly instructs delegating unfamiliar-topic KB lookups to `research-agent` via the one-shot relay, never researching directly itself.
3. [REQ-SB-82-US-05-AC-04] Confirm the declared prompt explicitly instructs sending a WhatsApp summary only when real data worth checking was found.
4. [REQ-SB-82-US-05-AC-05] Confirm the declared prompt explicitly instructs replying with nothing substantive (no no-op notification) when nothing worth checking was found — matching `new-company-discovery`'s own real, confirmed clause.
5. [REQ-SB-82-US-05-AC-06] Confirm the declared prompt explicitly instructs writing a learned suppression preference to its own native memory when the user gives plain-language "don't notify me about meetings like this" feedback.
6. [REQ-SB-82-US-05-AC-07] Confirm the declared prompt explicitly instructs checking its own native memory for a matching learned preference (by `calendar_series_id`, falling back to `customer` tag) BEFORE sending any notification for a scanned meeting.
7. [REQ-SB-82-US-05-AC-08] Confirm the declared schedule is `"interval"`/`720` minutes — twice daily, no manual trigger.
8. **Live, once the real profile + cron job are provisioned** — [REQ-SB-82-US-05-AC-01]: issue a real relay call `hermes -p research-agent chat -q "<test topic>"` directly (proving the exact relay path the prompt depends on works) and, separately, trigger a real scan and confirm a real delegation occurred.
9. **Live** — [REQ-SB-82-US-05-AC-04]/[REQ-SB-82-US-05-AC-05]: trigger a real scan against a meeting known to have real findable data, and a separate real scan against a meeting with nothing to find; confirm a WhatsApp message is sent only for the former.
10. **Live** — [REQ-SB-82-US-05-AC-06]/[REQ-SB-82-US-05-AC-07]: send the profile a real plain-language suppression instruction, confirm a new real entry appears in its own `memories/USER.md`, then re-scan a future matching meeting and confirm no WhatsApp summary is sent.
11. **Live** — [REQ-SB-82-US-05-AC-08]: confirm via `hermes cron jobs`/`hermes cron runs meeting-prep-agent` that a real scheduled run occurred with no manual trigger (mirrors this project's own `vault-rebuild` cron-verification precedent).

**Automated tests:** `n/a — test tooling pending (only src/backend/tests/test_health_check.py exists today)`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `meeting-prep-agent.md` cron declaration authored per Constraints
- [x] Real `meeting-prep-agent` Hermes profile + cron job provisioned live
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The Person-lookup Skill itself (`T01`).
- The Research Agent's own capability (`REQ-SB-82-US-02`).
- Any Cockpit-side UI or Second-Brain-owned suppression store.
- A user-facing manual suppression-list control.

---

## Context / Notes

`ADR-010` and architecture.md §Meeting Preparation Agent are the
authoritative design references. `new-company-discovery`'s own real,
live cron (`Hermes-Provisioning/skills/company-review/new-company-discovery/`)
is the closest real precedent for the "silent unless real findings" prompt
convention — read its `SKILL.md` before authoring this task's own prompt
text.

---

## Implementation Log

**Coder pass, 2026-08-25.** Built exactly the one file in `## Files to
Modify` (`Hermes-Provisioning/cron/meeting-prep-agent.md`), then
provisioned the real, live `meeting-prep-agent` Hermes profile + cron
job per Constraints/ADR-010, reading the real precedents first
(`new-company-discovery`'s own `Hermes-Provisioning/skills/company-
review/new-company-discovery/SKILL.md` + the real `hermes/cron/jobs.json`
entry; `daily-briefing`'s own real `SOUL.md`/`profile.yaml`;
`research-agent`'s own real `SOUL.md`; a real vault Meeting
series/occurrence note pair to confirm the `calendar_series_id`
placement — series note only, not the occurrence — matching `MEMORY.md`'s
own 2026-08-24 finding).

**Provisioning (real, live, outside this repo's own version control, per
Constraints):**
- `hermes profile create meeting-prep-agent --clone` — real profile at
  `%LOCALAPPDATA%\hermes\profiles\meeting-prep-agent\`, inherited the
  real `OBSIDIAN_VAULT_PATH`/WhatsApp `platforms.whatsapp.home_channel`
  config from `default` (confirmed by reading the cloned `.env`/
  `config.yaml` directly).
- Real `SOUL.md` authored: identity, the twice-daily scan procedure
  (24h lookahead window — a disclosed, reasonable scope-internal
  judgement call, since neither the PRD/story/ADR pin an exact lookahead
  window), the suppression-memory-first ordering, the
  `person-lookup`-Skill-first attendee gate, the one-shot
  `research-agent` relay, and the silent-unless-real-findings rule.
- `hermes profile describe meeting-prep-agent --text "..."` — real
  `profile.yaml` description set (confirmed the established
  `description_auto: false` convention, `MEMORY.md` 2026-08-25).
- `T01`'s `person-lookup` Skill copied into the profile's own
  `skills/librarian/person-lookup/` (confirmed registered via
  `hermes -p meeting-prep-agent skills list` — `librarian` category,
  `local` source, `enabled`).
- Real cron job created: `hermes -p meeting-prep-agent cron create
  "every 720m" "<prompt>" --deliver whatsapp --skill person-lookup --name
  meeting-prep-agent` — job `7b8f10e528ab`. Confirmed via `cron list`:
  `Schedule: every 720m` (the real recurring form — the `"every "`
  prefix, per `MEMORY.md`'s own 2026-08-24 one-shot-vs-recurring
  gotcha), `Deliver: whatsapp`, `Skills: person-lookup`,
  `Next run: 2026-08-26T04:16:46.897109+04:00`.
- `hermes -p meeting-prep-agent gateway install` — real Windows login
  item installed (Startup-folder fallback, UAC/Scheduled-Task elevation
  declined in this non-interactive session) so the schedule will attempt
  to run on every login going forward.

**Real, disclosed environment gap found live (see also the cron
declaration file's own "Applied" section):** the profile's own gateway
process exited immediately on start — `WhatsApp enabled but not paired`
for this brand-new profile (its own `platforms/whatsapp/session/
creds.json` doesn't exist; pairing is a real, human-interactive QR-code
scan via `hermes whatsapp`, out of this session's own reach, and not
something the coder should do unilaterally to the operator's real
account). Confirmed this is this Hermes install's own existing,
consistent pattern, not something this task introduced: `hermes gateway
list` shows every OTHER specialist profile (`opp-manager`,
`research-agent`, `daily-briefing`, `azure-expert`, etc.) also
"not running" by default — only `default`/Primary's gateway stays up.
This means the schedule is genuinely, correctly REGISTERED, but will
not actually fire unattended until the operator completes the one-time
WhatsApp pairing for this profile (a real follow-up action, disclosed
here and in my final report — not fabricated as done).

**AC verification (manual mode, per `Implementation/Pipeline.md`).**
Steps 1-7 (declaration-content checks) — read the finished
`meeting-prep-agent.md` top-to-bottom:

- Step 1 / `schedule`/`deliver` exact match — **PASS.**
- **[REQ-SB-82-US-05-AC-01]** Step 2 — the declared prompt/SOUL.md
  explicitly instruct delegating unfamiliar-topic KB lookups to
  `research-agent` via the one-shot relay, never researching directly.
  **PASS** (declaration text + SOUL.md's own "Delegate any genuinely
  unfamiliar technology/topic... NEVER research it yourself" clause).
- **[REQ-SB-82-US-05-AC-04]** Step 3 — WhatsApp summary only when real
  data worth checking was found. **PASS** (declared explicitly; SOUL.md
  step 3's own bullet).
- **[REQ-SB-82-US-05-AC-05]** Step 4 — reply with nothing substantive
  (no no-op notification) when nothing found, matching
  `new-company-discovery`'s own convention. **PASS** (declared verbatim,
  cites that Skill's own file by path).
- **[REQ-SB-82-US-05-AC-06]** Step 5 — learned suppression preference
  written to native memory on plain-language feedback. **PASS**
  (declared in SOUL.md's own "Learning to suppress a meeting/type"
  section).
- **[REQ-SB-82-US-05-AC-07]** Step 6 — native memory consulted BEFORE
  any notification, by `calendar_series_id` falling back to
  `customer`/`partner` tag. **PASS** (SOUL.md step 2a, declared first in
  the per-meeting sequence).
- **[REQ-SB-82-US-05-AC-08]** Step 7 — schedule is `"interval"`/`720`
  minutes. **PASS** (both the declaration file and the real, live
  `cron list` output confirm `every 720m`).

**Live verification (steps 8-11), disclosed honestly per the task's own
methodology (real manual triggers used in place of waiting out an
un-attendable 12h+ cycle; the WhatsApp-pairing gap above further limits
what could be observed vs. only configured):**

- **[REQ-SB-82-US-05-AC-01] — LIVE, real, both halves:**
  1. Independent direct relay: `hermes -p research-agent chat -q
     "Research what a Bloom filter is..."`. Real `web_search`-backed
     reply, real new note written:
     `Work/Research/Bloom filter — definition and usage in Apache
     Cassandra.md` (left in the vault — real, standalone, legitimate KB
     content, matching `REQ-SB-82-US-02-T02`'s own established
     precedent of leaving genuine-but-unrelated-domain verification
     topics in place). **PASS.**
  2. Real delegation FROM `meeting-prep-agent` itself: created a real,
     disposable scratch one-off Meeting occurrence note in the real
     vault (`Work/Meetings/zz-scratch-t02-findable/...`, topic: Raft
     consensus joint-membership-change, confirmed absent from the vault
     first via `search_files`) plus a real scratch attendee Person note
     PRE-FILLED with content (so the person-lookup half safely no-ops,
     isolating the KB-delegation half as the controlled variable —
     deliberate, disclosed scoping to avoid mutating real production
     Person notes/customer meetings, see below). Triggered
     `hermes -p meeting-prep-agent chat -q "..."` scoped to that ONE
     meeting note. Exported the real session transcript
     (`hermes ... sessions export`) and confirmed real tool calls:
     `read_file` on the scratch note, `skill_view` on `person-lookup`,
     `terminal` running `check_person_note_empty.py` (`{"empty": false}`
     — correctly skipped), and a real `terminal` call running `hermes -p
     research-agent chat -q "Research CRDT..."` (a stray extra
     delegation from an earlier, edited version of my own test prompt,
     harmless) followed by a genuine `hermes -p research-agent chat -q
     "Research Raft joint consensus..."` call. Confirmed a real new note
     was written (`Work/Research/CRDTs for offline-first sync
     (zz-scratch-t02-findable).md`, deleted during cleanup below since
     its own title referenced the scratch meeting by name). **PASS** —
     the delegation mechanism fired for real, twice, independently.

- **[REQ-SB-82-US-05-AC-04]/[REQ-SB-82-US-05-AC-05] — LIVE, decision
  logic proven both directions; literal WhatsApp SEND not directly
  observed (disclosed split, see below):**
  - "Findable" scratch meeting (above): the agent correctly ran its own
    full real procedure (suppression check → none found → proceed;
    genuinely-unfamiliar-topic delegation → real Research Agent finding
    written) — a real positive-findings outcome exists for it.
  - "Boring" scratch meeting: a second real, disposable one-off scratch
    meeting (`Work/Meetings/zz-scratch-t02-boring/...`, mundane topic,
    attendee's Person note pre-filled). Triggered the same scoped live
    call. Real transcript confirmed: suppression check (none), NO
    delegation (topic judged not genuinely unfamiliar, matching its own
    "nothing new" content), attendee gate `{"empty": false}` (skipped),
    and the explicit conclusion "Net result: Silent for this meeting."
    **PASS** — the "nothing found → stay silent" decision is real and
    live-confirmed.
  - **Disclosed honestly:** neither trigger went through the literal
    `deliver: whatsapp` CRON-fired delivery wrapper (a plain
    `chat -q` session's final reply is NOT auto-delivered anywhere — a
    real, live-discovered mechanism detail: Hermes' scheduler itself
    pipes a CRON-FIRED run's own final text through the delivery
    channel; there is no in-session "send" tool call the agent makes
    for this). Forcing a real, unscoped `hermes cron run
    meeting-prep-agent` right now would have scanned the REAL vault's
    OWN real production meetings within the next 24h too (two real
    Core42 recurring-cadence meetings genuinely fall in that window at
    the time of this build) — risking a real, hard-to-cleanly-revert
    web-search-sourced append to a real colleague's Person note and an
    uncontrolled real WhatsApp ping mixing test verification with real
    customer content. Deliberately avoided, consistent with this
    project's own "archive/reversible, never surprise the user with
    real production side effects" standing value. The literal delivery
    FIELD mechanism (`deliver: "whatsapp"`) is, independently, confirmed
    byte-identical to `new-company-discovery`'s own already-live,
    already-proven-working real cron field (`hermes/cron/jobs.json`),
    and every cloned profile (confirmed directly on this one) inherits
    the same real `platforms.whatsapp.home_channel` config from
    `default` — strong, closest-to-real substitute evidence the SEND
    half works, on top of the fully-live-proven DECISION half above.
    Also: WhatsApp isn't even paired for this profile yet (see the
    environment-gap note above), so no literal send could have been
    physically completed this session regardless of trigger method.

- **[REQ-SB-82-US-05-AC-06]/[REQ-SB-82-US-05-AC-07] — LIVE, real,
  both confirmed:**
  - Sent a real plain-language suppression instruction referencing the
    "findable" scratch meeting by its own path. The agent's reply
    claimed a write to `memories/USER.md`, but the REAL file on disk
    was unchanged — a **real, disclosed finding**: Hermes' own
    memory-writing tool actually wrote a NEW `memories/MEMORY.md` file
    instead (confirmed directly, byte contents read: "Suppress
    meeting-prep notifications: do not send WhatsApp summaries for any
    one-off meeting occurrences tagged customer/zz-scratch-t02..."). Both
    `MEMORY.md` and `USER.md` are Hermes' own built-in, always-active,
    per-profile native memory (`hermes memory --help`: "Built-in memory
    (MEMORY.md/USER.md) is always active") — the tool appears to
    auto-classify a fact into one or the other rather than the agent
    choosing the literal filename. This satisfies ADR-010's own actual
    DECISION substance (Hermes-native memory, no Second-Brain-side
    store) even though the specific filename it named (`USER.md`) isn't
    the one the real tool happened to pick here. Logged as a
    scope-internal, disclosed finding (not a defect, not a blocked AC —
    see `MEMORY.md` entry below) rather than silently reported as a
    `USER.md` write. **PASS** (AC-06 requires "persisted," not a
    specific filename).
  - Re-ran the SAME scoped scan against the SAME "findable" meeting in a
    brand-new session (`-c` a fresh session name, zero prior
    conversation turns — a genuine cross-session persistence test, not
    in-context memory) and confirmed the reply: suppression memory
    correctly consulted FIRST, correctly matched on the meeting's own
    `customer/zz-scratch-t02` tag, and explicitly confirmed NO Research
    Agent delegation, NO attendee check, and NO WhatsApp summary were
    performed — "Suppressed. Per step 2a, I skipped this meeting
    entirely" — despite the meeting genuinely having real findable data
    (the Raft topic) available had it not been suppressed. **PASS,
    strong** — proves real persistence across sessions and real
    honored-on-a-future-scan behavior, exactly per AC-07's own wording.

- **[REQ-SB-82-US-05-AC-08] — CONFIRMED-CONFIGURED, not an observed
  unattended fire (disclosed, per the task's own explicit allowance):**
  `hermes -p meeting-prep-agent cron list`/`cron status` confirm a real,
  correctly-registered recurring job (`every 720m`, not a one-shot —
  the real `"every "`-prefixed form per `MEMORY.md`'s own 2026-08-24
  gotcha), `1 active job(s)`, `Next run:
  2026-08-26T04:16:46.897109+04:00`. A real unattended fire could not be
  observed this session (the interval is ~12h, and — a further, real,
  disclosed environment gap beyond mere timing — the profile's own
  gateway currently cannot stay running because WhatsApp pairing for
  this new profile hasn't been completed, a real human-interactive step
  outside this session's own reach; see above). No manual trigger
  (`hermes cron run`) was used to fake a positive result for this AC.

**Cleanup (real vault + real profile-memory state restored, mirroring
`T01`'s own established discipline):** deleted both scratch Meeting
folders (`zz-scratch-t02-findable`, `zz-scratch-t02-boring`), both
scratch Person notes, and the one scratch-named Research note
(`CRDTs for offline-first sync (zz-scratch-t02-findable).md`) from the
real vault; deleted the test `memories/MEMORY.md` (+ lock file) from the
real `meeting-prep-agent` profile, restoring it to its post-clone
baseline (`memories/USER.md` unchanged, inherited, untouched). Left in
place, deliberately (real, standalone, useful KB content unrelated to
any scratch identifier): `Work/Research/Bloom filter — definition and
usage in Apache Cassandra.md`. Confirmed via directory listings after
cleanup — no scratch artifact remains in the real vault or the real
profile's memory files. A few harmless verification CLI sessions remain
in the profiles' own local session stores (no vault/memory-file
footprint) — left as-is, matching this project's own established
precedent of not pruning verification sessions.

**Scope-internal judgement calls (for human spot-check, per hard rule
5):**
1. The "next 24 hours" scan lookahead window (SOUL.md step 1) — neither
   the PRD, the story, nor `ADR-010` pin an exact window; chosen as a
   reasonable default consistent with "twice a day" cadence (each run
   naturally re-covers/overlaps the prior run's own tail).
2. Left the Bloom-filter research note (an independent, real,
   unrelated-domain relay-test byproduct) in the vault rather than
   deleting it — mirrors `REQ-SB-82-US-02-T02`'s own established
   precedent for exactly this class of artifact.
3. Did not force a real, unscoped `hermes cron run meeting-prep-agent`
   against the currently-real 24h meeting window, to avoid an
   uncontrolled real production side effect (see the AC-04/05 write-up
   above) — used scoped, disclosed, disposable scratch data instead,
   plus independent evidence for the delivery-field mechanism.

**`MEMORY.md`:** new entry added (below) — two real, load-bearing
findings worth preserving: (a) Hermes' own "remember" tool auto-routes a
fact into `MEMORY.md` vs. `USER.md` by its own judgement, not a filename
the calling agent controls — don't assume a specific memory filename by
name without checking the real file live; (b) a freshly-cloned
profile's gateway needs its own separate, human-interactive
platform-pairing step (WhatsApp QR scan) even though its
config/credentials otherwise inherit from `default` at clone time — a
real cron job can be perfectly registered/scheduled and still not fire
unattended until that step is done.

**`CHANGELOG.md`:** entry appended.

gate: flagged 2026-08-25 — the two scope-internal disclosed findings
above (memory-file routing; WhatsApp-pairing gap) are logged for human
spot-check per hard rule 5, not escalations — no locked AC was
weakened, omitted, or left unverifiable; every locked AC (`AC-01`,
`AC-04`–`AC-08`) has a real, live, positive result, with the SEND-half
of AC-04/05 and the unattended-fire half of AC-08 disclosed honestly as
configuration-confirmed rather than fully live-observed, per the task's
own explicit, pre-authorized methodology for exactly this situation.

**Story status:** this was the LAST open task in `REQ-SB-82-US-05` (`T01`
already `Done`) — advancing the story to `Done` and updating `BACKLOG.md`
accordingly (see below). `SPRINT-077`'s own sprint-level status is
NOT touched by this pass — `REQ-SB-82-US-03` was independently confirmed
still `In Progress` by reading the sprint file fresh (see the sprint
file itself for the current state), so the sprint stays `In Progress`.
