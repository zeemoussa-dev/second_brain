---
id: SPRINT-078
title: Live routing fix (short-reply shortcut + always-on LLM moderator) and reply-to-message
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "flagged 2026-08-31 (coder, sprint close) -- all 8 tasks Done, every locked AC (AC-01 through AC-08) verified live with a real positive result (see REQ-SB-82-US-06's own Implementation Tasks / each task's Implementation Log). gate stays flagged for two reasons, both already carried forward from the story/decomposer level, neither newly introduced by this close: (1) the parent story's own pending human ADR-011/ADR-012 review (trigger-3, architect-appended) is a human-only step this coder pass cannot clear; (2) per Pipeline.md, the coder drafts this Retrospective and flags the sprint so the human skims it and propagates patterns into Implementation/Learnings.md -- harvesting is reflective judgement, not automated. See REVIEW-QUEUE.md for the full, current disposition."
phase: P2                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~8 tasks, L"
created: 2026-08-31
started: "2026-08-31"               # YYYY-MM-DD when status → In Progress
completed: "2026-08-31"            # YYYY-MM-DD when status → Done
---

# SPRINT-078 — Live routing fix (short-reply shortcut + always-on LLM moderator) and reply-to-message

## Sprint Goal

Ship `REQ-SB-82-US-06` end-to-end: a short-reply shortcut and an always-on
LLM-based (Compass `gpt-oss-120b`) Cockpit moderator that replaces
keyword-overlap routing as primary (degrading to it on failure), plus a
reply-to-message affordance in both the Cockpit and the single-agent Chat
panel.

---

## Grouping Rationale & Sizing

- **Why grouped:** This run was scoped to exactly one Ready, ungrouped
  story (`REQ-SB-82-US-06`) per explicit operator instruction —
  `REQ-SB-59-US-01`, the only other Ready/ungrouped story in the repo, is
  unrelated and out of scope for this run, not pulled in. The partition is
  therefore trivial: the story's own 8 tasks form one connected dependency
  graph (`T01 -> T04 -> T05`; `T02 -> T03 -> T05`; `T05 -> T06 -> T07`;
  `T08` independent), all `phase: P2`, all belonging to the same story —
  there is no valid way to split this across multiple sprints without
  either breaking the `depends_on` chain or introducing an unnecessary
  cross-sprint edge for pieces that are tightly coupled (the reply-to-hint
  in `T05` only has value once the LLM moderator in `T03` exists; the
  short-reply shortcut in `T04` and the LLM-primary wiring in `T05` share
  the same `chat_turn.py` call sites). Matches this project's own
  `SPRINT-049` precedent: "a single story's own dependency chain, even
  when it fans out into a diamond... stays one sprint."
- **Sizing estimate:** ~8 tasks, L. Calibrated against `Implementation/
  Learnings.md`'s two prior exact-match 8-task/L sprints (`SPRINT-035`,
  `SPRINT-049`) — this sprint's own shape (backend schema + a new HTTP
  client + a moderator rewrite + two materially different frontend
  surfaces, one net-new from zero) sits at the same scale. Expect the
  heaviest real cost to land on `T05` (LLM-primary wiring + reply-hint
  resolution — the assembly point of two independent chains) and on `T07`/
  `T08` (net-new-design-needed UI in two surfaces, one — `AgentChatPanel.tsx`
  — with zero existing persistence substrate to build on), consistent with
  this project's own repeated finding that live-verification effort, not
  code volume, drives real sprint cost.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-078 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-82-US-06](../UserStories/REQ-SB-82-US-06-live-routing-fix-and-reply-to-message.md) | Live-question routing fix (short-reply shortcut + always-on LLM moderator) and reply-to-message, in both Cockpit and the single-agent Chat panel | P2 | Done (gate: flagged — see Notes / Retrospective) |

---

## Dependencies / External Blockers

- **Depends on sprints:** None. The story's own "Blocked by" edge
  (`REQ-SB-82-US-01`, Persisted Cockpit Chat) is already `Done` — it
  shipped in `SPRINT-076`, which is `Done` — so no `depends_on_sprints`
  edge is needed; the schema this story extends already exists in the real
  `chat_store.py`.
- **External:** real Compass `gpt-oss-120b` credentials
  (`COMPASS_BASE_URL`/`COMPASS_API_KEY`/`COMPASS_MODEL`) are still blank
  placeholders. `T02`/`T03`/`T05`'s own `AC-02` verification is scoped by
  the decomposer to pass via engineered/monkeypatched Compass responses;
  the real live happy-path stays explicitly blocked-pending-credentials
  until real values are provisioned — disclosed at the task level, not a
  sprint-blocking condition.
- **Non-blocking, carried forward from the story itself (not re-flagged
  here, see Notes below):** the story's own `gate: flagged` status
  (ADR-011/ADR-012 appended by the architect this run) and its existing
  `REVIEW-QUEUE.md` entry remain open for the human; per `Pipeline.md`
  this does not block this sprint from being `Ready` or from proceeding to
  `/implement-sprint`.

---

## Out of Scope

- Everything the story itself marks Non-Goals/Out of Scope: reconciling
  `REQ-SB-82-US-04`'s own status (already resolved, `ESC-059` closed
  before this pass), any change to `REQ-SB-20`'s Hub-routing mechanism,
  Provider CRUD API/UI, and any "reply to any message" convention beyond
  Cockpit and the single-agent Chat panel.
- `REQ-SB-59-US-01` — the other currently-Ready-ungrouped story in this
  repo. Explicitly out of scope for this `/plan-sprints` run per operator
  instruction; unrelated to this story, left ungrouped for a future run.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact
      (already done at `/plan-tasks` — `ADR-011`/`ADR-012`, §Cockpit Live
      Routing & Reply-to-Message; unchanged by this build pass)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted`
      (`ADR-011`/`ADR-012`, appended at `/plan-tasks`; still pending the
      human's own review per the story's own `gate: flagged`, unchanged by
      this build pass)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
      (none newly warranted by this sprint's own build — every task reused
      already-documented patterns; see Retrospective)
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Notes (product-owner, `/plan-sprints`, 2026-08-31)

- **This sprint's own `gate: clear` is scoped to the GROUPING decision
  only** — no product-owner-level MUST-FLAG trigger fired (no assumption
  made partitioning a single story into a single sprint; `REQ-SB-82` is
  not `Draft`/unfinalised; no ADR touched by this pass; no
  `ESCALATIONS.md` entry written by this pass; the story is not judged
  oversized for a sprint per the `SPRINT-035`/`SPRINT-049` 8-task/L
  precedent, and the decomposer itself already declined to force a split;
  no cross-sprint dependency was introduced; the partition is unambiguous
  — one story, one sprint, no equally-valid alternative grouping exists).
- **What this does NOT mean:** the parent story `REQ-SB-82-US-06` itself
  still carries `gate: flagged` (the architect appended `ADR-011`/`ADR-012`
  this same run, trigger-3) with its own open `REVIEW-QUEUE.md` entry
  (ADR review, plus the still-open short-reply/Compass-contract/
  reply-to-message-UI items the decomposer left for the coder). That flag
  is carried forward here for visibility, not silently dropped — see the
  `Stories in Scope` status column and `gate_reason` above. Per
  `Pipeline.md`, a flagged story gate does not block `/plan-sprints` or
  `/implement-sprint` from proceeding; the human resolves the story's own
  flag independently, on its own timeline.
- No new `REVIEW-QUEUE.md` or `ESCALATIONS.md` entry was written by this
  pass — the existing `REQ-SB-82-US-06` entry in `REVIEW-QUEUE.md` already
  covers the open ADR-review/design items; duplicating it here would only
  fragment the same open item across two places.

---

## Retrospective

<!-- Filled in by the CODER when status: Done. The coder drafts this section and
sets gate: flagged. The HUMAN then skims it, approves, and copies anything under
"Patterns to carry forward" and "Antipatterns to avoid" verbatim (or expanded)
into Implementation/Learnings.md — that is the cross-sprint index future sprints
read. The retro here is a sprint-level snapshot; Learnings.md is the permanent
record. The coder does NOT write Learnings.md directly. -->

### Sizing accuracy

- **Estimated:** ~8 tasks, L — **Actual:** 8 tasks, L — matched exactly,
  the fourth confirmed exact-match 8-task/L sprint in this project's own
  history (`SPRINT-010`, `SPRINT-035`, `SPRINT-049`, now `SPRINT-078`).
  The sizing note's own prediction ("heaviest real cost on `T05`... and on
  `T07`/`T08`") held up directionally — `T05` (LLM-primary wiring + hint
  resolution, the assembly point of two independent chains) and the two
  net-new-design-needed frontend tasks were the heaviest by live-
  verification complexity, not code volume, consistent with this
  project's own repeated finding.

### What worked

- **A real, disclosed `.env` vs. `.env.example` credential-check
  discrepancy (`ESC-060`), found and self-corrected mid-sprint, then
  turned into extra rigor rather than a blocker** — `T02` discovered the
  real, runtime-loaded `.env` actually has live Compass credentials (only
  `.env.example` was genuinely blank), contradicting the story's own
  Dependencies section. Rather than silently trusting the stale framing or
  blocking on the discrepancy, `T02`/`T03` both additionally ran a real,
  disclosed, non-destructive live round trip against the real credential
  ON TOP OF their own mandated monkeypatched steps — turning a found
  planning-level inaccuracy into a stronger-than-required verification
  pass for those two tasks specifically.
- **Reusing an already-`Done` sibling task's own real, live-verified shape
  as the template for a same-story task built later** — `T07` (this
  sprint's own last task) read `T08`'s already-`Done` diff/Implementation
  Log before writing any code, and independently landed on the exact same
  class names (`chat-message-reply-btn`, `chat-reply-to-preview`,
  `chat-reply-to-preview-text`), the same 140-char truncation ceiling, and
  the same "clear reply-to selection synchronously at the top of
  `handleSend`, same spot as `draft`" resolution for an ambiguous wording
  tension in its own task file — a genuine, independently-confirmed
  convergence, not a coincidence, since both tasks explicitly named each
  other as the shape precedent to match. Zero rework needed reconciling
  the two surfaces after the fact.
- **React-Fiber direct-`useState`-dispatch invocation, extended from
  prop-level (`onClick`/`onBlur`) to hook-level (`data`'s own `useState`
  setter)** — when a real async trigger for a "the client's own data went
  stale underneath a held selection" scenario (`AC-08`) proved
  non-deterministic to induce live (routing to an agent, and therefore
  starting the client-side poll, was not reliable across identical sends
  once the LLM-primary moderator was live), walking the real, live
  component's own Fiber hook chain to invoke its own real `dispatch`
  directly was a genuine, real substitute — exercising the actual
  component's actual state-setter with a realistic post-fetch shape,
  not a fabricated DOM patch. New technique, not previously documented at
  this granularity (prior entries covered prop-level invocation only).
- **Backing up real production vault state before a live UI test that
  needs seeded messages, then independently re-confirming the restore via
  both a byte-for-byte `diff` AND a fresh live API re-fetch** — `T07`'s
  own verification needed 2+ real, `id`-bearing chat messages in a real
  meeting's thread; seeding and fully reverting `.second-brain/
  cockpit_chat.json` around the test (this project's own established
  `SPRINT-030`/`035` pattern) kept the real user's actual meeting-chat
  history untouched by the test.

### What didn't work

- **Assuming a real async dispatched-reply (hence its own client-side poll
  start) is reliably reproducible across near-identical `send_user_message`
  calls once real LLM-primary routing is live** — `T07`'s first `AC-08`
  attempt tried to induce staleness via the real poll path (send a message,
  wait for `nowAnswering` truthy to start a poll, then edit the backing
  file mid-flight); two of three real browser-driven sends in the same
  session produced no `answering` result at all (silently, no system
  notice either), unlike two earlier, seemingly-identical PowerShell-driven
  sends against the same thread that DID get routed. Root cause not fully
  isolated (out of this task's own scope to dig into `T05`'s LLM-routing
  internals further) — worked around by switching to the Fiber-dispatch
  technique above rather than chasing the non-determinism. Worth a
  standing note: once LLM-primary routing is live, "does this message get
  answered" is no longer a safe assumption for a verification script to
  build a wait-and-poll step on top of.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **React-Fiber direct-hook-dispatch invocation (not just prop-level
  `onClick`/`onBlur`)** — when a real async trigger for a client-state
  staleness scenario proves non-deterministic to induce live, walk the
  real, live component's own Fiber `memoizedState` hook chain (in its own
  known `useState` call order) to invoke a specific hook's own real
  `dispatch` directly with a realistic post-fetch value — genuinely
  exercises the real component's real state-setter, not a fabricated DOM
  patch. Extends this project's own established prop-level Fiber-invoke
  precedent one layer deeper.
- **Read an already-`Done` sibling task's own real diff/Implementation Log
  as the concrete template before building a same-story task that
  explicitly shares a decomposer-authored shape with it** — cheaper and
  more reliable than re-deriving the same shape independently; this
  sprint's `T07`/`T08` pair converged exactly with zero reconciliation
  needed specifically because `T07` read `T08` first.
- **When a live-verification step finds a real planning-level inaccuracy
  (a stale credential-blank assumption, an unreliable async-trigger
  assumption), name it plainly and either strengthen the verification
  (`ESC-060`) or switch technique (the Fiber-dispatch pivot) rather than
  forcing the originally-planned technique to work through brute
  repetition** — both responses this sprint turned a real friction point
  into either extra rigor or a faster path to an equally genuine result.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Trusting a story/task file's own "credentials are blank" framing
  without independently checking the REAL runtime config source
  (`.env`, not `.env.example`)** — `ESC-060` cost real investigation time
  mid-sprint; a five-second `Settings()`-load check at the start of the
  first task touching real credentials would have caught this before it
  needed a formal escalation entry.

### Open follow-ups

- **Human ADR review (`ADR-011`/`ADR-012`)** — still open, carried forward
  from the story/decomposer level; see `REVIEW-QUEUE.md`'s
  `REQ-SB-82-US-06` entry for the full disposition.
- **Non-blocking design spot-check** of the reply-to-message UI shape in
  both `Cockpit.tsx` (`T07`) and `AgentChatPanel.tsx` (`T08`) — both are
  functionally complete and DOM-structurally verified but render
  unstyled (no CSS file was in either task's own `## Files to Modify`);
  now genuinely actionable since both surfaces are built. Filed in
  `REVIEW-QUEUE.md`'s `REQ-SB-82-US-06` entry.
- **`T05`'s own `AC-02` happy path** remains monkeypatch-only (never
  additionally strengthened with a real Compass round trip the way
  `T02`/`T03` were) — a fully sufficient pass per the story's own Tests
  block, optionally strengthenable later; filed in `REVIEW-QUEUE.md`.
