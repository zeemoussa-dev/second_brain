---
id: SPRINT-029
title: Agent Vault Write Access — /mcp shared-secret auth, write-capable MCP tool, Pending Approvals plumbing
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Sprint wrap — human should skim the retro below and propagate patterns to Implementation/Learnings.md. Also carries the still-Open ESC-026 (T03/AC-01/AC-02 remain outside every sprint until REQ-SB-29-US-01 is decomposed)."
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~2 tasks, S (buildable — T03 excluded, see Notes)"      # effort estimate; checked vs actual in retro
created: 2026-08-13
started: "2026-08-13"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-13"            # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — who drives each transition:
     Draft       → product-owner assembles the sprint. Bidirectional link is written
                   at creation: every story listed here already has sprint: SPRINT-NNN.
     Ready       → product-owner advances Draft→Ready when grouping is CLEAR (gate: clear).
                   Ambiguous, oversized, or blocked grouping stays Draft + gate: flagged.
                   Adding a story to a Ready sprint AUTO-REVERTS it to Draft.
     In Progress → /implement-sprint has started. Coder sets this + records started:.
     Blocked     → external dependency is unmet. Record it under Dependencies.
     Done        → every story is Done and every DoD box is checked. Coder sets this,
                   records completed:, DRAFTS the retrospective, and sets gate: flagged
                   for the human to skim and harvest Learnings.md.
-->

# SPRINT-029 — Agent Vault Write Access

## Sprint Goal

Build `REQ-SB-04-US-01`'s buildable scope: real `/mcp` shared-secret
authentication for non-loopback callers, and a write-capable
`propose_vault_write` MCP tool that always routes through a
`trigger="hermes"` Pending Approval — never a direct, unconfirmed write.

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — `REQ-SB-04-US-01` is the only
  story assigned here. The 2 buildable tasks (`T01`–`T02`) share one
  architecture scope (`ADR-025`, "`/mcp` shared-secret authentication + a
  write-capable MCP tool") and one straight dependency chain (`T01 → T02`).
- **Why NOT combined with `REQ-SB-09-US-01`/`REQ-SB-11-US-01` (this same
  pass's other P1-phase sprints), despite same phase and no dependency
  edge:** confirmed independent of all four other stories in this batch —
  no shared architecture scope, no shared file surface, and this story's
  own Context/Dependencies explicitly names it as unrelated to the To-Do
  capture pipeline or the activity-observability view. Combining unrelated
  stories only for task-count padding is not a grouping this project's own
  sprint history uses; each story here has a real, distinct architecture
  scope of its own.
- **`REQ-SB-04-US-01-T03` is deliberately EXCLUDED from this sprint's own
  scope — not scheduled as buildable work.** The decomposer's own pass
  individually held `T03` at `status: Draft`, `gate: flagged`,
  `depends_on: []`, with an explicit "⚠️ BLOCKED — DO NOT START" section
  (`ESCALATIONS.md` → `ESC-026`, `Open`): `T03` covers `AC-01`/`AC-02`
  (real scope enforcement, `_is_within_assigned_scope`), which composes
  entirely with `REQ-SB-29-US-01`'s own vault-scope-assignment mechanism —
  and `REQ-SB-29-US-01` has not been decomposed at all (zero task files
  exist anywhere in `Implementation/Tasks/`), so there is no real task id
  to sequence `T03` against. This mirrors `SPRINT-024`'s own identical
  handling of `REQ-SB-36-US-02-T04` (`ESC-018`) exactly: a confirmed,
  operator-acceptable per-task-blocking judgement call, not this
  product-owner pass's own decision to make or unmake. No attempt was made
  to unblock it, fabricate a `depends_on` edge for it, or silently schedule
  it. **This sprint schedules only `T01`–`T02`.** `T03` remains outside
  every sprint until `REQ-SB-29-US-01` is itself decomposed and a real task
  id exists to sequence it against — at that point a future
  `/plan-sprints` pass gives it its own sprint (most likely depending on
  this one plus whichever sprint eventually carries `REQ-SB-29-US-01`'s own
  tasks), not this one.
- **Sizing estimate:** ~2 tasks, S (buildable scope only). `T01` (`/mcp`
  shared-secret authentication for non-loopback callers, an ASGI
  middleware wrapping only the `/mcp` mount) → `T02` (the write-capable
  `propose_vault_write` MCP tool + Pending Approvals plumbing —
  `trigger="hermes"`, verifies `AC-03`/`AC-04` via a direct
  `pending_approval_registry` seed since the tool's own front door is
  deliberately fail-closed until `T03`). `T03` excluded, see above — matches
  `SPRINT-024`'s own identical "~3 tasks, S (buildable — T04 excluded)"
  shape for the same class of situation.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-029 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-04-US-01](../UserStories/REQ-SB-04-US-01-agent-vault-write-access.md) | Agent Vault Write Access — scoped, confirmed writes from a Hermes-connected agent | P1 | In Progress (T01–T02 Done; T03 blocked, ESC-026) |

**Tasks in scope** (dependency order, buildable only): [[REQ-SB-04-US-01-T01]]
(`/mcp` shared-secret authentication for non-loopback callers,
`depends_on: []`), [[REQ-SB-04-US-01-T02]] (write-capable MCP tool
`propose_vault_write` + Pending Approvals plumbing, `depends_on: [T01]`,
verifies `AC-03`/`AC-04`).

**Excluded from this sprint (not scheduled, not buildable):**
[[REQ-SB-04-US-01-T03]] — `status: Draft`, `gate: flagged`,
`depends_on: []`, individually blocked pending `REQ-SB-29-US-01`'s own
decomposition (`ESC-026`, `Open`). Holds `AC-01`/`AC-02`'s own real
verification. See Grouping Rationale.

---

## Dependencies / External Blockers

- **Depends on sprints:** None.
- **Not a blocker for this sprint, but recorded for the human:**
  `REQ-SB-04-US-01-T03` stays outside every sprint until
  `REQ-SB-29-US-01` is decomposed (`ESC-026`, `Open` — see
  `REVIEW-QUEUE.md`). This sprint's own Definition of Done does not
  require `T03` or `AC-01`/`AC-02` to be verified — the story's own `Done`
  status, once all locked ACs this sprint's tasks cover are verified,
  still leaves `AC-01`/`AC-02` open pending that future task; the same
  shape `ESC-011`/`ESC-018` already established for an individually-
  blocked task inside an otherwise-`Ready`/buildable story.
- `ADR-025` (already `Accepted`, reviewed and approved 2026-08-13 per
  `REVIEW-QUEUE.md`) is not itself a blocker for this sprint.
- Separately, a real reachable Hermes deployment remains an unconfirmed
  external unknown (`ESC-023`, `Open`) — blocks only this sprint's own
  live end-to-end verification against a real Hermes caller, not
  `/implement-sprint`'s ability to build and locally verify `T01`/`T02`.

---

## Out of Scope

- `REQ-SB-04-US-01-T03` — individually blocked, excluded from this
  sprint's own scope; see Grouping Rationale and Dependencies above.
- `REQ-SB-29-US-01` (Agent-to-Tag/Folder Scoping) — not yet decomposed,
  not eligible for `/plan-sprints`; not built here.
- Read access (`REQ-SB-03`), content ingestion via a Hermes channel
  (`REQ-SB-05`), and a new Hermes-channel-native confirmation UI — all
  explicitly out of this story's own scope.

---

## Definition of Done

- [x] `REQ-SB-04-US-01-T01`/`T02` are both `Done` and their covered ACs
      (`AC-03`, `AC-04`) verified live; `T01` carries no locked AC of its
      own (see its own Notes) — its 4 non-AC smoke checks all verified
      live instead
- [x] All story-level Definition-of-Done items satisfied for the
      buildable scope; `AC-01`/`AC-02`/`T03` remain explicitly open,
      tracked via `ESC-026`, not silently marked complete
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural
      fact — no change needed; `ADR-025`/architecture.md's own Addendum
      section already correctly described what was built, unmodified by
      this build pass
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — none new
      this pass (`ADR-025` already `Accepted` at `/plan-tasks`)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. -->

### Sizing accuracy

- **Estimated:** ~2 tasks, S (buildable) — **Actual:** 2 tasks, S, matched
  exactly. `T01` (auth middleware) was genuinely small in code volume but
  needed a real, non-trivial verification technique (simulating a
  non-loopback caller against a locally-run server); `T02` (the tool +
  plumbing) was correctly sized as the slightly heavier of the two (two
  locked ACs, a fail-closed seam that had to be proven honest both via the
  seeded-record technique and a real end-to-end MCP call), but total
  effort stayed within the "S" estimate.

### What worked

- **Simulating a genuinely non-loopback caller against a server that can
  only actually be reached via loopback in this environment**, via
  `httpx.ASGITransport(app=app, client=(fake_ip, fake_port))` driving the
  real, unmodified `app`/`mcp_server` objects in-process — exactly the
  technique `T01`'s own Tests block named as an example, and it produced
  a fully genuine exercise of the real middleware (a real `401`, a real
  pass-through to a real MCP tool call), not a mock or a stand-in.
  Extends this project's own established in-process-verification-
  technique family (monkeypatch, ASGITransport-with-custom-`client`) to a
  new concrete case.
- **Splitting a locked task's own real front-door decision from its own
  plumbing verification, honestly** — `T02`'s own Tests block already
  named the seeded-`pending_approval_registry` technique for `AC-03`/
  `AC-04` specifically because `propose_vault_write`'s own scope decision
  is deliberately unreachable this pass; building the whole task around
  that honest split (rather than trying to force a fail-open shortcut
  just to get a "cleaner" green checkmark) kept the fail-closed seam
  genuinely trustworthy. A real, additional end-to-end MCP tool call
  against the actual front door confirmed the honest-rejection shape
  live, on top of the named plumbing verification — worth doing whenever
  a task's own Tests block deliberately routes around a front door for a
  documented reason, to independently confirm that front door still
  behaves exactly as designed for the one behaviour it CAN exhibit today.
- **The specific-PID-kill-and-restart protocol, reconfirmed a further
  time** (now four sprints running: `SPRINT-019`/`021`/`022`/`029`) — a
  stray `--reload` uvicorn process (plus its own separately-alive
  multiprocessing-fork child) was found holding port 8001 at the start of
  this sprint; killing both and starting a single, explicitly-controlled
  instance kept the rest of the sprint's live verification unambiguous.

### What didn't work

- **A throwaway ASGITransport-based verification script's first attempt
  used an arbitrary placeholder Host (`"http://testserver"`), which
  produced a genuine but unrelated `421 Misdirected Request` from
  FastMCP's own internal Host-header validation** — cost one extra
  debug/retry cycle before realizing the failure wasn't from this task's
  own middleware at all. Worth naming explicitly: when driving a FastMCP
  (or any MCP `streamable_http`) mount via `ASGITransport`, use a
  plausible real host (matching what a genuine client, e.g.
  `mcp_client.py`, would actually send) rather than an arbitrary
  placeholder, since the MCP transport layer does its own Host validation
  independent of any application-level auth being tested.
- **An app-start capture pass genuinely crashed once, mid-sprint, on a
  transient real-vault race** (a concurrent session's own throwaway test
  file was read by a glob-then-read sequence after having already been
  deleted) — entirely outside this sprint's own file scope, and resolved
  by a plain retry once the vault state stabilized. Not a defect in this
  sprint's own code, but a reminder that this shared dev vault can carry
  real concurrent-session drift beyond just shared source files (already
  known for `main.py`, now also confirmed for live vault content).

### Patterns to carry forward

- **`httpx.ASGITransport(app=app, client=(fake_ip, fake_port))`, with a
  plausible (not arbitrary) Host in `base_url`, is the correct default
  technique for verifying an ASGI-middleware-level auth/network-origin
  check that cannot be exercised via a real non-loopback network path in
  this environment** — genuinely drives the real, unmodified application
  object, not a mock.
- **When a task's own Tests block deliberately verifies plumbing via a
  seeded/bypassed front door for an honestly-documented reason (a
  fail-closed seam not yet real), add one extra, clearly-labeled real
  end-to-end check against the actual front door** to independently
  confirm it behaves exactly as designed for whichever behaviour it CAN
  exhibit today (here: honest rejection, never fabricated success) — cheap
  additional confidence beyond what the task's own named steps strictly
  require.

### Antipatterns to avoid

- **Assuming an arbitrary placeholder hostname is inert for any ASGI-
  transport-based test against a real third-party ASGI sub-application**
  — some sub-applications (here, FastMCP's own transport) validate the
  Host header themselves, independent of whatever is being tested.

### Open follow-ups

- `REQ-SB-04-US-01-T03`/`AC-01`/`AC-02` remain `Draft`/blocked on
  `REQ-SB-29-US-01`'s own decomposition (`ESC-026`, still `Open`) — no
  change this pass; tracked in `REVIEW-QUEUE.md` as before.
- The real Hermes-deployment-reachability question (`ESC-023`, still
  `Open`) remains unresolved — this sprint made `/mcp` genuinely
  authenticatable and testable (loopback-vs-non-loopback,
  correct-vs-incorrect secret), but a real Hermes round trip against a
  real external deployment was not and could not be exercised this pass.
- A real, usable `HERMES_MCP_SHARED_SECRET` dev value now lives in the
  real, gitignored `.env` (not a placeholder) — worth a human glance to
  confirm this is an acceptable value to keep using for local
  development, or whether it should be rotated before any real Hermes
  integration attempt.

---

## Notes

**Sprint assembled 2026-08-13 (`/plan-sprints`).** `REQ-SB-04-US-01-T03`
explicitly confirmed excluded/blocked, not scheduled into this or any
other sprint as buildable work — per the decomposer's own already-recorded,
confirmed-acceptable judgement call (`ESC-026`), mirroring `SPRINT-024`'s
own identical handling of `REQ-SB-36-US-02-T04`/`ESC-018`. No attempt was
made to unblock it, fabricate a `depends_on` edge for it, or silently
schedule it.

**Gate: `gate: clear` 2026-08-13.** No MUST-FLAG trigger fires for this
product-owner pass: (1) no material assumption — the `T03` exclusion is
read directly off the decomposer's own recorded `depends_on: []` and its
own already-flagged, human-facing judgement call, not guessed or
re-decided; (2) `REQ-SB-04` is finalized PRD text (its scoping/`/mcp`-auth
open questions were resolved before this pass); (3) product-owner does not
write ADRs — `ADR-025` was already reviewed and approved
(`REVIEW-QUEUE.md`, 2026-08-13) before this pass; (4) no new
`ESCALATIONS.md` entry written by this pass — `ESC-026` was already opened
by the decomposer, this pass does not duplicate it; (5) re-checked
explicitly against both the "oversized" and "blocked story" MUST-FLAG
sub-triggers, not skipped: not oversized (2 buildable tasks, S); this is
not a "blocked story" in the MUST-FLAG sense requiring a fresh flag — the
*story* is `status: Ready` with 2 of 3 tasks genuinely buildable and zero
blocking issue of their own, and the one blocked task (`T03`) was already
individually flagged, with its own resolution path named, by the
decomposer's prior pass; this pass's own contribution is scheduling the
confirmed-buildable subset, not making a fresh blocked-story judgement
call; (6) N/A (coder-only trigger); (7) no contradictory inputs; (8) not
genuinely ambiguous for this pass — the decomposer's own prior pass already
made the granular per-task-scheduling choice (mirroring `ESC-018`'s own
established precedent), itself flagged for human confirmation
(`REVIEW-QUEUE.md`); this pass applies that already-made choice rather than
re-opening it; separately confirmed this story shares no dependency or
architecture-scope overlap with any other story in this same
`/plan-sprints` batch (`REQ-SB-01`/`02`/`09`/`11`), so no combined-sprint
option was genuinely equally valid either. Advances `Draft → Ready`.
