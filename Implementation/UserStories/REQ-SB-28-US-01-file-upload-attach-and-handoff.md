---
id: REQ-SB-28-US-01
title: File attachment on agent chat messages — upload, storage, and raw-content handoff (summarization/filing behavior deferred)
requirement_ids: [REQ-SB-28]
requirement_section: "REQ-SB-28: File Upload for Agents"
phase: P1
status: Draft
gate: clear
gate_reason: "Resolved 2026-08-12 — operator decided the storage-retention and accepted-file-type policy (see Notes). REQ-SB-25-US-01 is now Ready (no longer blocking planning). Still net-new-design-needed — run /design REQ-SB-28 before /plan-tasks."
sprint: ""
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-28-US-01 — File attachment on agent chat messages — upload, storage, and raw-content handoff (summarization/filing behavior deferred)

## Story

**As a** Second Brain user
**I want** to attach a file to a chat message I send an agent, with the
file's contents made available to whatever processes that message
**So that** I can eventually ask an agent to act on a file I give it (e.g.
summarize it), building on a real attachment mechanism rather than each
future skill needing its own upload plumbing

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-28: File Upload for Agents* — "The
  user can upload a file to an agent and ask it to act on the file's
  contents — for example, uploading a book and asking the agent to
  summarize it and file the summary under Research (REQ-SB-17)."
  Acceptance: "The user can attach a file to a chat message sent to an
  agent; the agent can act on the file's contents as asked (e.g. summarize
  it) and file the result into the vault under the requested area, matching
  existing schema conventions."
- **PRD breadcrumb (2026-08-11, operator-authored):** names four genuinely
  open questions, none decided in the PRD: (1) which agents accept
  uploads — the My Day Agent (`REQ-SB-23`) specifically, or any agent via
  its own chat; (2) accepted file types; (3) where uploaded files are
  stored — temporarily for processing only, vs. retained in the vault;
  (4) how "summarize and file under Research" maps onto an actual skill
  invocation (`REQ-SB-27`) versus a bespoke, one-off capability. It also
  states two explicit dependencies: **REQ-SB-25** (real chat, "to receive
  and discuss the upload") and **likely REQ-SB-27** (skills, "as the
  mechanism that actually processes the file").
- **REQ-SB-25 had no story at all when this scoping decision was made** —
  confirmed by direct `BACKLOG.md` inspection at the start of this pass.
  A concurrent `/spec` pass has since drafted `REQ-SB-25-US-01` (`Draft`,
  itself `gate: flagged`, not yet `Ready`/`Done`); this section's own
  reasoning is unchanged by that — the *mechanism* still doesn't exist as
  working code yet, only as a story. Today's real chat mechanism
  (`REQ-SB-13-US-01`, Done) is exact-phrase/keyword-substring matching
  against a small, per-agent `trigger_phrases` set (`ADR-011`) —
  deliberately not an LLM/NLU pipeline. Asking an agent to "summarize this
  file and file it under Research" in natural language would not match any
  declared trigger phrase today; genuine understanding of an arbitrary
  free-text instruction about an attached file's contents is, in
  substance, what REQ-SB-25 itself is for. **This story's own scenarios
  are therefore written to not assume REQ-SB-25 has shipped** (see
  Constraints) — they cover the upload/storage/handoff mechanism only, so
  this plumbing is buildable and independently verifiable regardless of
  REQ-SB-25's own timeline, but the requirement's own full worked example
  (genuine summarization) cannot be meaningfully demonstrated end-to-end
  until REQ-SB-25-US-01 is actually `Done`.
- **Scoping decision — which agents accept uploads:** the PRD's own
  Acceptance text says "attach a file to a chat message sent to an
  agent," without naming a specific agent, unlike the breadcrumb's tentative
  "My Day Agent specifically" phrasing. This story reads the Acceptance
  text literally: any agent reachable through `REQ-SB-13-US-01`'s existing
  embedded chat panel can accept an attachment on its chat messages — the
  same surface, extended, not a new one restricted to a single agent. This
  is a defensible grounding in the requirement's own literal acceptance
  text, not a guess at open product intent, so it is not itself a
  flag-worthy ambiguity (see `## Notes`'s enumerated MUST-FLAG reasoning —
  distinguishing this resolved point from the genuinely open ones).
- **Scoping decision — deferring "summarize and file under Research":**
  per this run's own instruction to scope narrowly ("upload mechanism +
  hand raw content to the agent's chat," without assuming a specific skill
  invocation model) so this story doesn't have to wait on REQ-SB-27's own
  still-unresolved architectural shape (`REQ-SB-27-US-01`, also drafted
  this session, scoped to registry/access plumbing only, first skill
  deferred). This story's scope ends at: the file is attached, stored, and
  its raw content (or a reference sufficient to retrieve it) is included
  in whatever the agent's existing message-processing path already
  receives — today, that's `ADR-011`'s keyword-trigger matcher; in future,
  whatever REQ-SB-25 lands as. **This story alone does not fully satisfy
  REQ-SB-28's PRD Acceptance text** — the "act on the file's contents as
  asked" and "file the result... matching existing schema conventions"
  halves of the Acceptance text are explicit follow-on work (see
  Non-Goals), not built here.
- Storage retention (temporary-for-processing vs. vault-retained) is a
  genuine product/privacy decision, not a pure implementation detail — a
  user may not want an arbitrary uploaded file (e.g. a personal book PDF)
  permanently retained inside their trusted vault alongside their own
  authored notes, or may specifically want it retained for future
  reference. This is not decided here (see `## Notes`).
- No `html-prototype/` screen shows any file-attachment affordance —
  confirmed by direct inspection of `agents-map.html`'s chat block (a
  `chat-thread` plus a plain text-input send form, no attach control). A
  `/design` pass is needed before this story can proceed past
  `/plan-tasks` — noted, not designed here.

## Acceptance Criteria

<!-- Untagged Gherkin — the decomposer authors final wording and assigns
AC-IDs at /plan-tasks. Happy path first, then the no-attachment regression
guard, then error states. Deliberately scoped to the upload/storage/
raw-content-handoff mechanism only — see Context's scoping decisions; no
scenario here asserts genuine summarization or vault-filing behavior. -->

### Scenario 1: Attaching a file to a chat message stores it and shows it in the chat thread

```gherkin
Given the user has an agent's chat panel open
When the user attaches a file to a chat message and sends it
Then the message, with an indication of its attached file (e.g. filename),
    appears in the chat thread
  And the file's content is stored so it can be retrieved for processing
```

### Scenario 2: The attached file's raw content is made available to whatever currently processes the agent's messages

```gherkin
Given the user has attached a file to a chat message directed at an agent
When the agent's existing message-processing path runs (today: keyword-
    trigger matching; in future: whatever backs real conversational chat)
Then the file's raw content, or a reference sufficient to retrieve it, is
    included alongside the message text in what that processing path
    receives
  And this story adds no new understanding, summarization, or vault-
    filing logic of its own — only the handoff
```

### Scenario 3: An uploaded file's presence is recorded in the agent's unified communication history

```gherkin
Given an attached file was sent to an agent in a chat message (per
    REQ-SB-13-US-01's existing unified chat + run-event history)
When the user views that agent's communication history
Then the corresponding chat entry indicates a file was attached (e.g. its
    filename), consistent with the existing chronological unified log
```

### Scenario 4: Sending a chat message with no attachment is unaffected

```gherkin
Given the user sends an ordinary chat message with no file attached
When the agent's existing message-processing path runs
Then its behavior is identical to before this story shipped — no
    attachment-handling code path is triggered, and nothing about the
    existing REQ-SB-13-US-01 chat mechanism changes for a plain message
```

### Scenario 5: Attempting to attach a file that fails validation is rejected clearly, not silently

```gherkin
Given the user attempts to attach a file that fails whatever type/size
    constraints are configured (exact constraints left to /plan-tasks — see
    Constraints)
When the user sends the message
Then the user receives a clear rejection message explaining the file was
    not accepted
  And no partial/corrupt attachment is stored, and no message is sent with
    a broken or missing attachment reference
```

## Affected Screens

- No `html-prototype/` screen currently covers this. `agents-map.html`'s
  agent detail panel's Chat block (`.chat-thread` + send form) is the
  natural surface this story extends with an attach-file control — but no
  such control exists in the approved prototype. Per the mandatory
  prototype-reconciliation rule, this triggers `net-new-design-needed`;
  recommend `/design REQ-SB-28` (the attach affordance itself can likely
  be designed independently of REQ-SB-25/REQ-SB-27's own open questions,
  since this story's scope is upload/storage/handoff only).

## Dependencies

- **Blocked by:** REQ-SB-25 (Real Conversational Agent Chat) —
  `REQ-SB-25-US-01` now exists (`Draft`, itself `gate: flagged`, not yet
  `Ready`/`Done`, drafted by a concurrent `/spec` pass during this same
  session). This story's own scenarios are written not to assume
  REQ-SB-25 has shipped (see Context/Constraints), so the upload/storage/
  handoff plumbing can be planned and built independently — but the
  requirement's own full worked example (genuine summarization from an
  uploaded book) has no meaningful way to be demonstrated end-to-end until
  `REQ-SB-25-US-01` is actually `Done`. Recommend clearing
  `REQ-SB-25-US-01`'s own flag and building it through `/plan-tasks` →
  `/implement-sprint` before this story's follow-on (the "act on contents
  and file it" story) is attempted.
- **Related to:** REQ-SB-27 (Skills Repository, `REQ-SB-27-US-01` also
  drafted this session) — the PRD's own suggested eventual mechanism for
  "acting on" a file's contents (e.g. an image/diagram-understanding
  skill). Not assumed or built here; this story's handoff scenario
  (Scenario 2) is deliberately agnostic to whatever eventually consumes
  the file's raw content.
- **Related to:** REQ-SB-13 (`REQ-SB-13-US-01`, Done) — this story extends
  its existing embedded chat panel and unified communication history with
  an attachment capability, rather than building a new chat surface.
- **Related to:** REQ-SB-17 (Research Notes, `REQ-SB-17-US-01`, Done) — the
  PRD's own worked example cites this schema as the eventual filing
  target for a summarized upload; not built here (see Non-Goals). A
  future follow-on story implementing "summarize and file" should target
  this exact schema, not a new one.
- **External:** the storage-retention decision (temporary-for-processing
  vs. vault-retained) has real product/privacy implications and needs a
  human decision, not a guess — see `## Notes`.

## Constraints

- **Does not require or assume REQ-SB-25 (real conversational chat)
  exists or has shipped.** Scenario 2 is deliberately written against
  "whatever currently processes the agent's messages" — today's
  keyword-trigger matcher (`ADR-011`), or a future real-chat mechanism —
  rather than asserting genuine natural-language understanding of the
  attached file's contents.
- **Adds no summarization, "act on contents," or vault-filing logic of its
  own** (Scenario 2's explicit final line) — that is the requirement's own
  Acceptance text's second half, deferred to a follow-on story once
  REQ-SB-25 and/or REQ-SB-27 have resolved their own open questions.
- **Never silently drop or corrupt an attachment** (Scenario 5) — mirrors
  this project's standing "honest, not fabricated/silent" posture already
  established for actions/Providers (`ADR-011`, `ADR-014`).
- **Accepted file types (decided 2026-08-12, see Notes):** PDF (`.pdf`),
  plain text/markdown (`.txt`, `.md`), and common image formats (`.png`,
  `.jpg`/`.jpeg`) — covers the PRD's own worked examples (a book PDF;
  REQ-SB-27's image/diagram-understanding skill example) without an
  open-ended allowlist. Max size **20 MB** per file. Both are defaults the
  decomposer may tune at `/plan-tasks` if a concrete implementation reason
  requires it, but are no longer an open product question.
- **Storage retention (decided 2026-08-12, see Notes): temporary-for-
  processing only, never vault-retained by default.** An uploaded file is
  stored outside the Obsidian vault (e.g. a new `.second-brain/uploads/`
  scratch directory, mirroring the existing `.second-brain/` state-file
  convention) for as long as needed to hand its content to the agent's
  message-processing path, then eligible for cleanup — exact TTL/cleanup
  mechanism left to `/plan-tasks`. Explicitly chosen over vault-retention
  as the *default* because the vault is this project's trusted,
  user-curated space (per `CLAUDE.md`'s own "no promotion gate — it's
  trusted personal data" framing) and an arbitrary uploaded file (e.g. a
  personal PDF) should not silently become part of that trusted space
  without the user asking for it. A future story may add an explicit
  "keep this file in the vault" action; not built here (Non-Goals,
  unchanged).
- No backend endpoint currently accepts a file alongside a chat message —
  a new/extended API surface is required; its shape is left to
  `/plan-tasks`.

## Implementation Tasks

<!-- Left for the architect/decomposer at /plan-tasks — genuinely blocked
on two open human decisions named in ## Notes (storage retention; accepted
file types/size limits) and on REQ-SB-25-US-01 not being Ready/Done yet;
the decomposer should confirm at least the storage-retention question has
been addressed (or explicitly deferred with a safe default, e.g.
temporary-only, per this project's no-staging-gate-but-still-cautious
posture) before task breakdown proceeds. -->

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **"Act on the file's contents as asked" (e.g. genuine summarization)** —
  the requirement's own Acceptance text's first behavioral half; deferred
  to a follow-on story once REQ-SB-25 (real chat) exists to genuinely
  understand a free-text instruction about the file.
- **"File the result into the vault... matching existing schema
  conventions" (e.g. filing a Research note per REQ-SB-17)** — the
  requirement's own Acceptance text's second behavioral half; deferred to
  the same follow-on story, once it's also clear whether this is a
  bespoke capability or a REQ-SB-27 skill invocation (also not decided
  here).
- **Any specific accepted file-type allowlist or size limit** — a genuine
  open product question (see `## Notes`), not guessed at here.
- **A storage-retention decision (temporary vs. vault-retained)** — a
  genuine open product/privacy question (see `## Notes`), not guessed at
  here.
- **Restricting uploads to a single named agent (e.g. only the My Day
  Agent)** — this story's own scoping decision (see Context) reads the
  requirement's literal Acceptance text as agent-agnostic, extending
  REQ-SB-13's existing per-agent chat panel generally, not one agent
  specifically.
- **Any UI** — no `/design` pass has occurred for an attach-file control on
  the chat surface; this story's scope is backend plumbing only until
  `/design` runs.

## Notes

**Prototype parity:** not applicable — no file-attachment region exists in
any `html-prototype/` screen today (`agents-map.html`'s Chat block was
checked directly: a `.chat-thread` plus a plain text send form, no attach
control anywhere). `net-new-design-needed` — recommend `/design REQ-SB-28`
for the attach-file affordance on the existing chat send form.

**Why `gate: flagged`:**

1. **Material assumption, minimized by narrow scoping, but two remain
   genuinely undecided and are named, not guessed:** accepted file types/
   size limits, and storage retention (temporary vs. vault-retained). The
   "which agents accept uploads" question was instead resolved by a
   defensible literal reading of the Acceptance text (see Context) — not a
   guess, so not counted as an unresolved assumption.
2. REQ-SB-28 is not marked `<!-- Draft -->` in the PRD (it carries a
   "Scope resolved" breadcrumb naming its own open sub-questions, not an
   unfinalised marker) — trigger 2 does not apply in the literal sense.
3. N/A directly (architect/ADR trigger) — but `/plan-tasks` should expect
   to face the storage-retention question directly; flagging it now is
   intended to save a wasted round-trip.
4. `ESCALATIONS.md` → `ESC-007` written (category `unclear-requirement`),
   per the Forbidden section's own instruction. Not resolved in this pass
   — no operator was available to resolve it live.
5. Not oversized as currently scoped (comparable in size to a single-
   concern extension of `REQ-SB-13-US-01`'s already-Done chat surface) —
   the *full* requirement (real summarization + vault filing) would very
   plausibly need its own separate story regardless, which is exactly why
   it's deferred rather than attempted here.
6. N/A (coder trigger).
7. No contradictory PRD inputs.
8. **Genuinely unclear / multiple equally-valid options** on accepted file
   types and storage retention — textbook trigger 8, not guessed past.
   This story's primary dependency, REQ-SB-25, had no story at all when
   this scoping decision was made; a concurrent `/spec` pass has since
   drafted `REQ-SB-25-US-01` (`Draft`, itself `gate: flagged`, not yet
   `Ready`/`Done`) — the dependency is now tracked but still unbuilt,
   which keeps this story's own real-world value gated regardless.

`gate: flagged` 2026-08-11, `gate_reason` above. `REVIEW-QUEUE.md` entry
added pointing here. `ESCALATIONS.md` → `ESC-007` added (`Status: Open`).
Recommend the human's first action be clearing `REQ-SB-25-US-01`'s own
flag and taking it through `/plan-tasks` → `/implement-sprint` before
continuing this story's own follow-on work, given how much of REQ-SB-28's
actual product value (genuine "act on this file" behavior) is gated on
REQ-SB-25 actually shipping, not just being specced.

**Update, 2026-08-12 — Resolved.** Operator decided both open policy
questions directly (recorded in Constraints above): accepted file types
(PDF/txt/md/PNG/JPG, 20MB cap) and storage retention (temporary-for-
processing only, never vault-retained by default — a `.second-brain/
uploads/` scratch directory, mirroring the project's existing state-file
convention, not the trusted vault itself). `REQ-SB-25-US-01` has also
since reached `status: Ready` (`gate: clear`), removing that blocker on
planning (though its full `Done` build is still recommended before this
story's own "act on the file" follow-on is attempted, per the
dependency's own unchanged reasoning above). `gate:` reset to `clear`.
`ESCALATIONS.md` → `ESC-007` flipped to `Resolved`, naming this update as
the resolving artefact. **Next step: this story is still net-new-design-
needed** (no attach-file affordance exists in any `html-prototype/`
screen) — run `/design REQ-SB-28` before `/plan-tasks`.
