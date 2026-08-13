---
id: REQ-SB-05-US-01
title: Content Ingestion Path — content arriving via a Hermes-connected channel lands as a new vault note
requirement_ids: [REQ-SB-05]
requirement_section: "REQ-SB-05: Content Ingestion Path"
phase: P1
status: Draft
gate: flagged
gate_reason: "unclear-requirement (ESC-023, partially resolved 2026-08-13 — see Notes) — the shared foundational Hermes-connectivity/mcp-authentication question REQ-SB-03-US-01 originally flagged is now resolved (real /mcp auth: yes, minimum-viable shared-secret shape; operator decision). What remains genuinely open, and is this story's own: (1) the transport mechanism by which a Hermes channel would actually deliver content to Second Brain (a new MCP tool call, a webhook/HTTP endpoint Hermes posts to, or something Hermes's own skill-wrapping convention dictates) — a real external-protocol unknown; (2) whether this story's own trust rule should compose with REQ-SB-04-US-01's confirmed scope/confirmation rule, or stand alone, since ingestion is itself a vault write. Neither was addressed by the operator's two resolutions and both need a human decision."
sprint: ""
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-05-US-01 — Content Ingestion Path — content arriving via a Hermes-connected channel lands as a new vault note

## Story

**As a** Second Brain user
**I want** content I send through a Hermes-connected channel (e.g. an
attachment) to land as a new note in my vault
**So that** I have a way to get content into my knowledge base other than
directly authoring it in Obsidian, from wherever Hermes already reaches me

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-05: Content Ingestion Path* —
  "Content can enter the vault through a path other than directly editing
  files in Obsidian — e.g. an attachment or piece of content arriving via a
  Hermes-connected channel lands as a new vault note." Acceptance: "Content
  submitted through a defined ingestion path (channel attachment, or another
  surface decided at `/spec` time) results in a new note in the vault,
  indexed the same way any Obsidian-authored note would be."
- **Ported from `agentic-map` REQ-035 (Upload data directly to an agent)** —
  tool swap only; scope resolved 2026-08-10 alongside `REQ-SB-04`, see
  `Implementation/Plans/2026-08-10-agentic-map-requirement-port.md`.
- **This story shares `REQ-SB-03-US-01`'s foundational finding**: no real
  Hermes connection exists anywhere in this codebase. Full detail:
  `REQ-SB-03-US-01`'s own `## Context`/`## Notes` and `ESCALATIONS.md` →
  `ESC-023`. **Update, 2026-08-13:** the `/mcp`-authentication half of that
  shared finding is now resolved (operator decision: yes, real
  authentication, minimum-viable shared-secret shape — see
  `REQ-SB-03-US-01`'s own Constraints). The real-Hermes-deployment-
  reachability half remains genuinely open but is explicitly scoped by the
  operator as an `/implement-sprint`-time live-verification concern, not a
  `/spec`/`/plan-tasks` blocker (see `## Notes`).
- **This requirement is itself a form of vault write** — content "results in
  a new note in the vault," per the PRD's own literal Acceptance text, not a
  temporary staging area. This composes directly with `REQ-SB-04-US-01`'s
  trust-surface concerns (an external channel causing a vault write). The
  operator has since confirmed REQ-SB-04's own scope/confirmation rule
  (tag/folder scope + Pending-Approvals confirmation), but **has not**
  addressed whether REQ-SB-05's own ingestion path should compose with that
  rule, or stand alone (REQ-SB-05's own PRD text does not name a tag/folder
  scope or confirmation rule the way REQ-SB-04's does) — this remains a
  real, unresolved interaction between the two requirements' own trust
  postures (see `## Notes`).
- **Closest existing precedent — but a different channel, and itself
  unbuilt:** `REQ-SB-28` (File Upload for Agents, `REQ-SB-28-US-01`, `Draft`/
  `gate: flagged`) already resolved two closely related policy questions for
  a *different* ingestion surface — file attachments on Second Brain's own
  **in-app** chat (`REQ-SB-13`/`REQ-SB-25`), not an external Hermes channel:
  accepted file types (PDF, `.txt`/`.md`, PNG/JPG, 20MB cap) and storage
  retention (temporary-for-processing only, **never vault-retained by
  default**). That retention default is the opposite of what REQ-SB-05's own
  PRD text describes ("lands as a new vault note") — REQ-SB-05 reads, on its
  own literal Acceptance text, as directly filing into the vault by design,
  consistent with this project's standing "no staging/promotion gate,
  trusted personal data" posture (`MEMORY.md`), not as a temporary scratch
  upload awaiting further action. This story takes that literal reading
  rather than assuming REQ-SB-28's retention default should carry over
  unchanged — a defensible grounding in REQ-SB-05's own Acceptance text
  (the same kind of resolved-by-literal-reading judgment REQ-SB-28-US-01
  itself made for "which agents accept uploads"), not a guess at open
  intent, so it is not itself counted as a flag-worthy ambiguity below.
  Whether the file-type/size limits should also carry over from `REQ-SB-28`
  is a smaller, more plausibly-reusable question, but still not decided
  here (see Constraints).
- **The transport mechanism is genuinely unknown, and is not this analyst's
  call to invent.** How would a Hermes-side attachment actually reach
  Second Brain? Candidates with no clear existing precedent to choose
  between: (a) a new MCP tool (e.g. an `ingest_content` tool registered
  alongside `REQ-SB-03`'s read tools and `REQ-SB-04`'s write tools on the
  same shared `app/api/mcp_server.py`, carrying file content inline or by
  reference); (b) a dedicated HTTP endpoint Hermes itself posts an
  attachment to, outside the MCP tool-invocation model entirely; (c)
  whatever shape `MEMORY.md`'s own "Hermes integration-sourcing precedence"
  constraint implies — "prefer a native Hermes skill or MCP server if one
  already exists; otherwise wrap an existing working implementation as a
  Hermes skill" — which presumes visibility into Hermes's own real
  capabilities that this repo does not have.

## Acceptance Criteria

<!-- Untagged Gherkin — the decomposer authors final wording and assigns
AC-IDs at /plan-tasks. Written against the PRD's own literal Acceptance
text; Constraints/Notes are explicit that the transport mechanism and
file-type/size policy are not decided here. -->

### Scenario 1: Content submitted through a Hermes-connected channel results in a new, indexed vault note

```gherkin
Given the user has a Hermes-connected channel available
When the user submits content through that channel (e.g. an attachment)
Then a new note is created in the vault containing that content
  And the new note is indexed the same way any Obsidian-authored note would
    be
```

### Scenario 2: Content of an unsupported type or exceeding the configured size limit is rejected clearly

```gherkin
Given the user attempts to submit content through a Hermes-connected
    channel that fails whatever type/size constraints are configured (exact
    constraints left to /plan-tasks — see Constraints)
When the submission is processed
Then the user receives a clear rejection explaining the content was not
    accepted
  And no partial, corrupt, or empty note is created in the vault as a
    result
```

### Scenario 3: Submitting the same content twice does not create a duplicate or corrupt an existing note

```gherkin
Given content was already submitted through a Hermes-connected channel and
    landed as a vault note
When the same content is submitted again
Then no duplicate note silently overwrites or corrupts the existing one
  And the outcome (a new distinct note, an update, or a clear rejection) is
    handled the same deliberate way this project's other capture pipelines
    already guarantee no-data-loss on rerun (e.g. REQ-SB-07/REQ-SB-08's
    idempotency guarantees)
```

## Affected Screens

None — backend/integration only. Per `MEMORY.md`'s standing "Hermes is an
integration point, not something this project builds" constraint, the
submission surface itself is external to Second Brain; nothing in
`html-prototype/` covers or should cover this requirement's own submission
UI. Whether Second Brain needs its own UI acknowledgement (e.g. an
observability entry, per `REQ-SB-11`) once content lands is not decided
here.

## Dependencies

- **Blocked by:** `REQ-SB-03` (Conversational Agent Access via Hermes) —
  `REQ-SB-03-US-01`, `Draft`/`gate: clear` (2026-08-13). The shared
  `/mcp`-authentication requirement is resolved; the real-Hermes-deployment-
  reachability question is unaffected (see `## Notes`).
- **Related to:** `REQ-SB-04` (Agent Vault Write Access) — `REQ-SB-04-US-01`,
  `Draft`/`gate: clear` (2026-08-13). Its own scope/confirmation rule is now
  confirmed; whether THIS story should compose with it, or stand on its own
  separate trust rule, remains a real, unresolved question specific to
  REQ-SB-05 — see `## Notes`.
- **Related to:** `REQ-SB-28` (File Upload for Agents) — `REQ-SB-28-US-01`,
  `Draft`/`gate: flagged`. Closest existing precedent for an
  attachment-to-note-content pipeline, but a different channel (in-app chat,
  not external Hermes) with an opposite retention default (temporary, never
  vault-retained by default) than this story's own literal reading of
  REQ-SB-05's PRD text (direct vault filing). Not assumed to share a
  mechanism; a future implementation pass may still choose to share
  underlying file-handling code once both exist, but that is not decided
  here.
- **External:** the transport mechanism unknown named above
  (external-protocol design this repo cannot answer from its own contents)
  remains fully open. The real-Hermes-deployment-reachability unknown named
  in `REQ-SB-03-US-01`'s `## Notes` applies here too — does not block
  `/spec`/`/plan-tasks`, only `/implement-sprint`'s live end-to-end
  verification.

## Constraints

- **Ingested content must result in a real vault note, indexed the same way
  any Obsidian-authored note would be** — the PRD's own literal Acceptance
  text; matches this project's standing "no staging/promotion gate" posture
  (`MEMORY.md`).
- **No silent data loss or corruption on a duplicate/rerun submission** —
  matches this project's standing idempotency posture (`REQ-SB-07`/
  `REQ-SB-08`'s existing no-duplicate-on-rerun guarantees), and
  `MEMORY.md`'s standing "never build a note filename from date+subject
  alone" constraint (a real, previously-found defect class).
- **The transport mechanism (new MCP tool vs. dedicated HTTP endpoint vs.
  something Hermes's own skill convention dictates) is NOT decided here** —
  a real external-protocol/architecture decision, left to `/plan-tasks`, not
  guessed.
- **The accepted content-type/size policy is NOT decided here** — `REQ-SB-28`
  is a plausible starting point (PDF/`.txt`/`.md`/PNG/JPG, 20MB cap) given
  its recency and this project's general preference for consistency, but
  reusing it verbatim vs. defining REQ-SB-05's own policy is left to
  `/plan-tasks`/a human decision, not assumed.
- **Do not build a second, parallel tool-registration mechanism** if the
  chosen transport is an MCP tool — per `ADR-015`'s "grow by registering,
  not a new server per capability" rule, it registers on the existing
  `app/api/mcp_server.py` instance, not a new one.
- **`/mcp` must require real authentication for any non-loopback caller**
  before this story's ingestion path is reachable, IF the chosen transport
  is an MCP tool (operator decision, 2026-08-13, shared with
  `REQ-SB-03-US-01`/`REQ-SB-04-US-01`) — minimum-viable shared-secret shape.
  If a dedicated HTTP endpoint is chosen instead, it needs an equivalent
  authentication decision of its own, left to `/plan-tasks`.
- **Whether this story's writes must additionally satisfy `REQ-SB-04`'s
  scope/confirmation rule is NOT decided here** — a real, unresolved
  interaction between the two requirements, left to a human decision (see
  `## Notes`).

## Implementation Tasks

<!-- Left for the architect/decomposer at /plan-tasks — genuinely blocked on
the human decisions named in ## Notes (transport mechanism, content-type/
size policy, and the REQ-SB-04 trust-rule composition question). /mcp
authentication itself is resolved (see ## Constraints), no longer a
blocker. -->

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Read access** — `REQ-SB-03`, a separate requirement.
- **Arbitrary agent-directed writes not tied to a specific submitted piece
  of content** — `REQ-SB-04`, a separate requirement and trust rule (though
  related, see Dependencies).
- **Summarization, classification, or "acting on" the ingested content's
  meaning** — the PRD's own Acceptance text asks only that the content
  "results in a new note in the vault," not that it be understood/
  transformed; any such behavior is a separate, future capability (parallel
  to how `REQ-SB-28-US-01` deliberately excluded "act on the file's
  contents" from its own scope).
- **Reusing `REQ-SB-28`'s implementation verbatim** — related but not
  assumed identical (different channel, different retention default); not
  built here without an explicit decision.

## Notes

**Prototype parity:** N/A — no `html-prototype/` screen covers or should
cover an external Hermes channel's own submission UI.

**Why `gate: flagged` (`ESCALATIONS.md` → `ESC-023`) — updated 2026-08-13,
partially resolved, still flagged:**

1. **Material assumption, disclosed, not hidden:** this story reads
   REQ-SB-05's "lands as a new vault note" literally as direct-to-vault
   filing (not REQ-SB-28's temporary-scratch default) — a defensible literal
   reading, not itself flagged as an ambiguity, but the *transport
   mechanism* by which that filing actually happens is a genuine, disclosed
   assumption gap (see point 8, unresolved).
2. `REQ-SB-05` itself carries no `<!-- Draft -->` marker — trigger 2 is not
   about the requirement's finalization state; it's about the dependency
   chain (`REQ-SB-03`), which is now `gate: clear`, no longer itself a
   reason to stay flagged.
3. N/A directly (architect/ADR trigger) — but `/plan-tasks` should expect a
   real architecture decision on the transport mechanism.
4. `ESCALATIONS.md` → `ESC-023` written (category `unclear-requirement`,
   shared with `REQ-SB-03-US-01`/`REQ-SB-04-US-01`) — stays `Open`
   (partially resolved, see its own 2026-08-13 update); this story's own
   sub-questions (below) are the reason it stays open.
5. Not oversized as scoped — deliberately split from `REQ-SB-03`/`REQ-SB-04`
   into its own story given its own distinct mechanism (content transport/
   filing, not query or agent-directed writes).
6. N/A (coder trigger).
7. No contradictory PRD inputs.
8. **Genuinely unclear, not guessable from this repo — still open after the
   operator's 2026-08-13 decisions, which addressed REQ-SB-03/REQ-SB-04's
   own questions but not these:** the transport mechanism (new MCP tool vs.
   dedicated HTTP endpoint vs. Hermes-skill convention), and whether this
   story's trust rule should compose with `REQ-SB-04`'s now-confirmed
   scope/confirmation rule or stand alone — textbook trigger 8, flagged
   rather than invented.

**Resolved 2026-08-13 (operator decision, shared with `REQ-SB-03-US-01`/
`REQ-SB-04-US-01`):** `/mcp` authentication, IF an MCP tool ends up being the
chosen transport — yes, real authentication, minimum-viable shared-secret
shape, in scope (see `## Constraints`). This does not resolve the transport-
mechanism choice itself (point 8 above) — only what happens once/if that
choice lands on an MCP tool.

**Still NOT resolved, genuinely open, not this analyst's call:** (a) the
transport mechanism itself; (b) whether this story's writes must compose
with `REQ-SB-04`'s scope/confirmation rule; (c) whether the accepted
content-type/size policy reuses `REQ-SB-28`'s (PDF/`.txt`/`.md`/PNG/JPG,
20MB cap) or defines its own; (d) whether a real, reachable Hermes
deployment exists to test the eventual transport against — per the
operator's own 2026-08-13 framing (see `REQ-SB-03-US-01`'s Notes), this
last item specifically does **not** block `/spec`/`/plan-tasks`, only
`/implement-sprint`'s live end-to-end verification, and is tracked
separately from (a)-(c) above.

**What to do:** (1) decide the transport mechanism by which a Hermes channel
delivers content to Second Brain (a new MCP tool, a dedicated HTTP endpoint,
or Hermes's own preferred skill-wrapping shape — likely needs input from
whoever administers the real Hermes deployment, not just this repo); (2)
decide whether ingested content should compose with `REQ-SB-04`'s
confirmed scope/confirmation trust rule, or use its own; (3) confirm or
replace the proposed content-type/size policy (reuse `REQ-SB-28`'s, or
define new). Record decisions directly in this story's `## Notes`, flip
`ESCALATIONS.md` → `ESC-023` to `Resolved` once (1)-(3) are answered (it may
stay `Open` afterward only for the still-separate real-Hermes-reachability
tracking item, per that file's own convention), reset `gate:` to `clear`,
then run `/plan-tasks REQ-SB-05` — after `REQ-SB-03` (already `Ready`-
eligible) is actually `Ready`.

gate: flagged 2026-08-13 (unchanged — partially resolved, not fully).
`ESCALATIONS.md` → `ESC-023` stays `Open`, updated 2026-08-13 to record
that the shared Hermes-connectivity/`/mcp`-auth questions are resolved but
this story's own transport-mechanism and trust-rule-composition questions
are not. `REVIEW-QUEUE.md` updated accordingly.
