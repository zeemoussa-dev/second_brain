---
id: REQ-SB-100-US-01
title: Read a Hermes session's transcript — the prompt it was really given, every turn, every tool call
requirement_ids: [REQ-SB-100]
requirement_section: "REQ-SB-100: Read a Hermes Session's Transcript, to See Why an Ask Went Wrong"
phase: P2
status: Draft
gate: flagged
gate_reason: "trigger-8 (the PRD names an open decision this story cannot take for the operator: session dumps contain real mail and real names, and 'putting them on a screen makes them easier to export and share by accident, which is worth a deliberate decision rather than a default' — how far that goes, from read-only-no-export to redaction to an access gate, changes what gets built)"
sprint: ""
created: 2026-10-17
updated: 2026-10-17
---

# REQ-SB-100-US-01 — Read a Hermes session's transcript — the prompt it was really given, every turn, every tool call

## Story

**As a** Second Brain operator whose ask went wrong
**I want** to open a session from Agent Activity and read what the agent was
actually given and actually did — the system prompt, the skill text injected into
it, every turn, and every tool call with its arguments and its real output
**So that** I can see where a wrong instruction came from and which step misread
it, instead of opening a JSON file on the machine

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-100* — raised 2026-10-17 by the operator:
  "We need to Ability to Debug The Hermes CHats So I can Fix When an Ask Gets
  Confused". Finding 1 (Hermes already writes every run to
  `<HERMES_HOME>/sessions/request_dump_*.json` — the system prompt, the model, the
  injected skill text and every turn), Finding 2 (the app lists sessions and shows
  none of their content), Finding 3 (a scheduled job's prompt lives in Hermes' own
  job record and can disagree with the Skill it names — on 2026-10-16 it still
  instructed the old one-script flow after the Skill had been replaced).
- **Grounded against the real code.** The gap is exactly as described:
  - `GET /hermes/sessions` → `business/hermes/status.py::get_sessions` →
    `rest.list_sessions` returns **metadata only**: profile, title, message count,
    start/end, `end_reason`, `is_active`.
  - `AgentActivityPage.tsx` renders those as `.log-item` rows under "Hermes session
    log". **The rows are not clickable** — there is no session detail route, no
    detail component and no reader of `request_dump_*.json` anywhere in the
    repository.
  - Run detail *is* exposed for a cron job's runs
    (`GET /hermes/cron/jobs/{id}/runs/{id}/detail` →
    `HermesCron.get_execution_detail`, which returns the run's own report plus a
    matching `agent.log` excerpt) — but not for an interactive session, and
    neither path shows the prompt the agent was given.
- **The open decision this story cannot take.** The PRD's own *Worth knowing
  before choosing*: these dumps hold whatever the agent read — real mail, real
  names. They are already on disk; a screen makes them easy to export and share by
  accident. The defensible answers range from "render it, never offer an export"
  through "redact recognised addresses by default" to "put it behind an explicit
  reveal". They produce materially different builds, and it is the operator's
  call. Scenario 6 below encodes the **narrowest** of them so the story is
  buildable either way; the decomposer is asked in Notes to consider leaving it
  non-locked until the operator answers, exactly as `REQ-SB-95-US-01`'s own
  export-privacy AC was handled.
- **Independent of everything else raised on 2026-10-17.** It needs nothing from
  `REQ-SB-96`, `REQ-SB-97`, `REQ-SB-98` or `REQ-SB-95`, and is one of the two
  cheapest of the five.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: A session in Agent Activity opens into its own transcript

```gherkin
Given Agent Activity lists a completed Hermes session
When the operator opens that session
Then the transcript for that session is shown: the system prompt the agent was
    given, the skill text injected into it, each turn in order, and the final
    answer
  And each tool call is shown with the arguments it was called with and the real
    output it returned, not a summary of either
  And the session's own identity — which agent, when, which model — is shown with
    it, so the transcript cannot be read against the wrong run
```

### Scenario 2: The 2026-10-16 failure is diagnosable from the screen

```gherkin
Given the session in which summarize-and-tag-threads failed because the agent was
    told to call a scripts\apply_thread_review.py path that does not exist in the
    deployed Skill
When the operator opens that session's transcript
Then the instruction naming that path is visible, and it is visible which part of
    the input it came from — the system prompt, the injected skill text, or the
    job's own stored prompt
  And the failing tool call and its real error output are both shown
  And no file on the machine has to be opened to reach either
```

### Scenario 3: A scheduled run's stored prompt is shown beside the Skill it names

```gherkin
Given a cron job whose stored prompt disagrees with the current content of the
    Skill it names
When the operator opens that run
Then the prompt the job actually sent and the skill text actually injected are
    both shown
  And the disagreement is apparent from the screen rather than requiring the two
    to be compared by hand elsewhere
  And a run that recorded ok while its transcript shows a failed tool call is not
    presented as successful without that contradiction being visible
```

### Scenario 4: A session with no transcript on disk says so

```gherkin
Given a session listed in Agent Activity whose dump has been rotated away, was
    never written, or cannot be parsed
When the operator opens it
Then the view says the transcript is unavailable and why
  And the session's existing metadata is still shown
  And nothing is reconstructed, inferred or fabricated to stand in for it
```

### Scenario 5: A long transcript is readable rather than dumped

```gherkin
Given a session with a very large number of turns, or a tool call returning a very
    large output
When the operator opens it
Then the transcript renders without the screen hanging or silently dropping
    content
  And any content not shown in full is explicitly marked as truncated, with a way
    to see the rest
```

### Scenario 6: A transcript is read in place, not handed around

```gherkin
Given a transcript containing real mail content and real names
When the operator views it
Then it is reachable only by explicitly opening one named session, never as a
    bulk listing of transcript contents
  And the screen offers no download, export or copy-all affordance for it
  And nothing about viewing it copies the dump anywhere outside <HERMES_HOME>
```

### Scenario 7: An unreadable sessions store is reported honestly

```gherkin
Given the Hermes install is unreachable, or its sessions directory cannot be read
When the operator opens a session
Then the view says so, and why
  And no empty transcript is presented as a session that had nothing in it
```

## Affected Screens

- `src/frontend/src/pages/AgentActivityPage.tsx` — the existing "Hermes session
  log" `.log-item` rows become openable (they are inert today), and gain the
  unavailable-transcript state. The Outlook "Communication channels" region is
  untouched.
- **New** session transcript view (a route or a panel — the architect's call).
  Reuses the live approved `.card`, `.log-list`/`.log-item`, `badge` and
  `.empty-state` families, plus the existing `mono` convention for raw text.
- `html-prototype/agent-activity.html` — see Notes → Prototype parity.

## Dependencies

- **Blocked by:** none.
- **Related to:** `REQ-SB-99-US-01` (the other half of debugging — what the agent
  *is*, where this is what it *did*); `REQ-SB-96-US-01` (the 2026-10-16 failure in
  Scenario 2 is a drift failure seen from the transcript side).
- **External:** a real Hermes install whose `sessions/` directory holds real
  `request_dump_*.json` files.

## Constraints

- **Read-only.** Nothing here writes to, moves, prunes or rotates a dump.
- **Never leaves `<HERMES_HOME>`.** The transcript is read and rendered; it is not
  copied into the data path, into the vault, or into a log.
- **Honest absence over reconstruction.** A missing or unparsable dump is reported,
  never approximated from metadata.
- **No new Hermes→app direction.** This reads Hermes' own files and existing
  endpoints; it does not open a new inbound surface (`ADR-033` owns the one
  deliberate loopback direction).
- **The privacy posture is the operator's to widen, not the build's.** Until the
  decision in Notes is taken, Scenario 6's narrow posture is the floor; nothing in
  the build may quietly exceed it.
- **One Manager is the sole gateway**; raw I/O stays in `data_access/` and
  `app/hermes/`.
- **Windows host.** Dumps live under a long install path and can be large; use the
  established long-path helper, and stream rather than load-and-hold.

## Implementation Tasks

<!-- Owned by the decomposer at /plan-tasks. -->

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Editing a prompt, a job's stored prompt, or a Skill from this screen.** The
  screen shows the disagreement; fixing it happens where those are edited.
- **Searching across transcripts**, or any bulk view of their contents — expressly
  against Scenario 6's posture.
- **Exporting, downloading or sharing a transcript** — the open decision; if the
  operator wants it, it is a new story.
- **Redaction** — a defensible answer to the same open decision, deliberately not
  assumed here.
- **Retention, rotation or pruning of dumps.** Hermes owns their lifecycle.
- **Replaying or re-running a session.**
- **Changing the session list itself** beyond making a row openable.

## Notes

**The open decision, stated plainly for the human:** the PRD asks for a deliberate
choice about transcripts containing real mail and real names. Scenario 6 encodes
the narrowest posture (read in place; no export, no bulk listing of contents) so
the story is buildable while the question is open. **Recommendation to the
decomposer:** lock Scenarios 1–5 and 7, and consider leaving Scenario 6's AC
non-locked (`<!-- AC-ID: … | locked: false -->`) with the reason recorded, exactly
as `REQ-SB-95-US-01`'s own export-privacy AC was handled on 2026-10-16 — so the
debugger can ship without pre-empting a decision the operator has not made.

**Prototype parity (`html-prototype/agent-activity.html`):**

- *Activity log* region — **Specced** (Scenarios 1, 4): the approved `.log-list`/
  `.log-item` rows are what the real page already renders; this story makes a row
  openable and adds the unavailable state. No new list pattern.
- *Empty state* ("No agent activity recorded yet") — **Specced** as-is; the real
  page already carries its equivalent and Scenarios 4 and 7 extend the same
  honest-failure convention.
- *Refresh / never-a-cached-snapshot* region — **Specced** as-is, unchanged.
- *Communication channels* (Outlook reachability) — **Deferred (different
  concern)**: untouched by this story.
- The transcript view itself — **Specced functional-first** (Scenarios 1, 2, 3, 5).
  No approved prototype screen covers a transcript; it is a composition of the
  already-approved `.card`, `.log-item` and `mono` families rather than a new
  visual system, following the operator's own 2026-08-31 precedent (recorded in
  `REQ-SB-85-US-01`'s `gate_reason`, applied again on `REQ-SB-95-US-02`/`US-04`).
  If the human disagrees, `/design REQ-SB-100` before `/plan-tasks` is the cheap
  correction.

**Architect pointers for `/plan-tasks` (context, not decisions):**

- Two possible sources for a transcript, and the choice matters: Hermes' own REST
  surface (`app/hermes/rest.py` already does `GET /api/sessions/stats` and
  `list_sessions`, so a detail endpoint may exist there) versus reading
  `<HERMES_HOME>/sessions/request_dump_*.json` off disk. The dumps are what the
  PRD's Finding 1 is based on; whether Hermes exposes the same content over REST
  was not confirmed in this pass and should be before the split is written.
- `HermesCron.get_execution_detail()` is the nearest existing precedent for "open
  one run and show its real content", including its discipline of keying the log
  excerpt off the *same* real execution row rather than approximating — Scenario 3
  is that idea extended to the prompt.
- Scenario 5's size handling is a real concern, not a hypothetical: a dump holds
  every turn plus full tool outputs, including mail bodies.

**Audit breadcrumb:**

gate: flagged 2026-10-17 — trigger 8 (the PRD names an open decision — how far the
privacy posture goes for transcripts containing real mail and real names — and the
answers produce materially different builds). `REQ-SB-100` is finalised in the PRD
with a complete Acceptance paragraph and carries no `<!-- Draft -->` marker; no ADR
created or changed by this pass; no `ESCALATIONS.md` entry; not oversized (one
read-only view over an existing list page); no contradictory inputs — every finding
was checked against the real code and matched.
