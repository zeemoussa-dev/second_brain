---
id: SPRINT-022
title: Real Anthropic Provider integration & web-research skill for Research Expert agents
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Combined human review needed: ADR-022 (original + a same-date operator-directed Correction addendum reversing point 3's design) and an honest, operator-acknowledged verification gap (AC-01/AC-03's own real-result branches blocked on a missing genuine ANTHROPIC_API_KEY). See REVIEW-QUEUE.md."
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: [SPRINT-020]   # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~6 tasks, M"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-12
started: "2026-08-12"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-12"            # YYYY-MM-DD when status → Done
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

# SPRINT-022 — Real Anthropic Provider Integration & Web-Research Skill

## Sprint Goal

Build and verify `REQ-SB-36-US-01` end to end: a real Anthropic SDK client
(`anthropic_client.py`), a genuinely working `"anthropic-claude"` Provider
entry, and a new `web_research(query)` skill (reusing `REQ-SB-27-US-01`'s
existing catalog/access-grant plumbing) that reaches Anthropic's own
server-side web-search tool — plus the live-discovered tool-binding gap fix
so a skill-catalog tool is only ever bound to an agent that has been
granted access to it.

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — all 6 tasks belong to
  `REQ-SB-36-US-01`, the only story assigned here.
- **Why sequenced after `SPRINT-020` (Section Hub Intelligence), not
  combined with it:** `T06` carries a real, decomposer-confirmed
  cross-story `depends_on` edge onto `REQ-SB-20-US-01-T05` — both tasks
  edit the exact same `graph.py::run_agent_conversation` call site
  (`load_vault_query_tools()`/the routing node's own tool list), a genuine
  same-function collision risk the decomposer caught and resolved with a
  real ordering edge, not a fabricated one. `SPRINT-020` must land first
  so this task composes around the real, current state of that file
  rather than racing it. `depends_on_sprints: [SPRINT-020]` records this.
- **Why NOT bundled with `REQ-SB-21-US-01` (Agent Working Modes) or
  `REQ-SB-35-US-01` (Vault Filing Expert), despite all three eventually
  feeding the same "Compass Expert" chain:** this story's own `##
  Dependencies`/`## Notes` are explicit — "No dependency on
  `REQ-SB-21-US-01` anywhere in this story... this story's own
  architecture is fully self-contained and unblocked" beyond the one
  `SPRINT-020` edge. Bundling with `REQ-SB-21-US-01` would force this
  sprint to wait on a 9-task sprint it has no real dependency on, purely to
  reduce sprint count — an artificial coupling this project's own
  established practice (honour the dependency graph, never introduce a
  cross-sprint edge that isn't real) rejects. Bundling with
  `REQ-SB-35-US-01` (which itself needs `SPRINT-020` **and** `SPRINT-021`)
  would have the identical problem. Kept as its own sprint, gated only on
  the one real prerequisite it actually has.
- **Sizing estimate:** ~6 tasks, M — `T01` (dependency/config) →
  `T02`/`T03` (Anthropic client, Provider-registry extension) → `T04`
  (the skill function) → `T05` (invoke-args plumbing) → `T06` (the
  tool-binding gap fix, gated on `SPRINT-020`). Comparable to `SPRINT-007`/
  `SPRINT-012`/`SPRINT-020`'s own 6-task M precedent.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-022 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-36-US-01](../UserStories/REQ-SB-36-US-01-web-research-skill.md) | Real Anthropic Provider integration and a web-research skill for Research Expert agents | P1 | Done |

**Tasks in scope** (dependency order): [[REQ-SB-36-US-01-T01]] (Anthropic
dependency + Settings fields, `depends_on: []`), [[REQ-SB-36-US-01-T02]]
(`anthropic_client.py`, `depends_on: [T01]`), [[REQ-SB-36-US-01-T03]]
(`provider_registry.py` `"anthropic-claude"`, `depends_on: [T01]`),
[[REQ-SB-36-US-01-T04]] (`web_research` skill, `depends_on: [T02, T03]`),
[[REQ-SB-36-US-01-T05]] (`invoke_skill` `args` + router body, `depends_on:
[T04]`), [[REQ-SB-36-US-01-T06]] (`mcp_client.py` tool-binding gap fix,
`depends_on: [T04, REQ-SB-20-US-01-T05]` — cross-sprint, see Dependencies).

---

## Dependencies / External Blockers

- **Depends on sprints:** `SPRINT-020` (must be `Done`) — `T06`'s real,
  decomposer-confirmed edge onto `REQ-SB-20-US-01-T05` (a same-call-site
  collision fix in `graph.py::run_agent_conversation`).
- No new ADR expected beyond `ADR-022` (already `Accepted`, written at
  `/plan-tasks`); not reopened by this sprint's own grouping.

---

## Out of Scope

- `REQ-SB-21-US-01` (Agent Working Modes) — no real dependency edge from
  this story onto it; not bundled. Built in its own sprint, `SPRINT-021`.
- `REQ-SB-35-US-01` (Vault Filing Expert) — no dependency edge from this
  story onto it (the dependency runs the other way, downstream, at
  `SPRINT-024`); not bundled. Built in its own sprint, `SPRINT-023`.
- `REQ-SB-36-US-02` (Compass Expert pilot) — depends on this story's `T05`;
  built in its own sprint, `SPRINT-024`, sequenced after this one.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied (all Constraints respected; every Implementation Task complete; `MEMORY.md`/`CHANGELOG.md` updated; automated tests remain n/a — test tooling still pending project-wide)
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated (a small, factual in-place correction to the already-existing "Real Anthropic Provider integration & web-research skill" section, reflecting the mid-build Provider-resolution correction — flagged for human spot-check, see `REVIEW-QUEUE.md`)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` (`ADR-022` itself was already `Accepted` at `/plan-tasks`; this pass added a dated "Correction" addendum to the same entry, not a new ADR number — a scope-internal judgement call, logged for human spot-check, see `REVIEW-QUEUE.md`)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. -->

### Sizing accuracy

- **Estimated:** ~6 tasks, M — **Actual:** 6 tasks, M, but with a real,
  unplanned mid-build design reversal (`T04`/`T05` had to be built twice —
  once per `ADR-022`'s original point 3, once per the operator's direct
  correction) plus two genuine environmental blockers (a missing real
  credential; an unkillable port) that consumed real investigation time
  the estimate didn't and couldn't anticipate. Task *count* held exactly;
  effort within `T04`/`T05` roughly doubled.

### What worked

- **Investigating a real technical claim before implementing an operator
  correction, instead of assuming the correction's own premise** — the
  operator asked a direct, falsifiable question ("does Compass have real
  web search?") rather than just dictating an implementation; answering
  it live (via this codebase's own `compass_client.py` plus the sibling
  `agentic-map` project's own real, working precedent of using a
  *separate* Perplexity Sonar provider for exactly this need) turned a
  potentially-fabrication-risking correction into a confidently-honest
  one, and gave concrete, citable evidence for the story's own updated
  design rather than a guess.
- **In-process monkeypatch verification as a genuine substitute for a
  live round trip, when the live round trip's own peer is provably stale
  infrastructure** — `T06`'s own filtering logic was verified against the
  REAL, unmodified function body (not a rewritten test double), just fed
  a synthetic tool list in-process, once the actual port `8001` peer was
  confirmed (not assumed) to be serving pre-this-story code. This
  produced stronger, more honest evidence than either skipping the check
  or running it against known-stale infrastructure and reporting a
  misleading pass/fail.
- **Splitting a two-part locked AC's verification honestly** (the
  routing/honesty-funnel half vs. the "produces a real positive result"
  half) rather than either claiming full pass or blocking the whole task
  — every real, verifiable piece of `AC-01`/`AC-03` (the resolution logic
  correctly reaches Anthropic's real API for a linked agent; the system
  never fabricates when blocked) was verified live and reported
  precisely as such, with the one genuinely-external, genuinely-
  unverifiable piece (a real credential) named specifically, not folded
  into a vague "partially done."

### What didn't work

- **A hardcoded, undiscoverable "ghost" TCP listener on this project's
  own documented dev-server port (`8001`)** blocked a genuinely fresh,
  end-to-end MCP round trip against this story's own new tool
  registration — confirmed via five independent Windows process-
  enumeration mechanisms (`Get-NetTCPConnection`/`Get-Process`/`tasklist`/
  `wmic`/.NET `Process.GetProcessById`), all agreeing the owning PID does
  not exist, with no admin rights available on this host to investigate
  further (`netstat -anob` requires elevation). This is the same failure
  mode `mcp_client.py`'s own historical docstring note already describes
  once before this sprint — recurring a second time within the same
  project's lifetime.
- **A required-Settings-field addition (`ANTHROPIC_API_KEY`) silently
  breaks the whole app's dev-server reload the moment the real `.env`
  doesn't have it yet** — this is `ADR-022`'s own already-Accepted,
  already-anticipated Consequence, not a surprise, but it meant a
  managed/background dev-server process on this exact host went dark
  (serving pre-this-story stale code) the instant `T01` landed, until a
  placeholder value was added — worth naming explicitly as a real,
  observed operational cost of this class of design, not just a
  theoretical one.

### Patterns to carry forward

- **Investigate, don't assume, when an operator correction's own
  reasoning depends on a checkable technical fact** — reused from
  `SPRINT-018`'s own "frame a fabrication-risk test around a real entity"
  pattern, one level up: apply the same discipline to a correction's own
  premise, not just to the feature's own output.
- **A sibling project's own already-solved precedent for the identical
  problem is strong, citable evidence** — `agentic-map`'s own dedicated
  Perplexity Sonar provider (kept separate from Compass specifically for
  web search) was more convincing, load-bearing evidence than reasoning
  from this codebase's own request shape alone.
- **When a live network peer is provably stale (confirmed by literally
  diffing its own response against the newly-registered entity), don't
  run the "real" check against it and report a misleading result — name
  the staleness, and use the strongest available substitute (in-process
  monkeypatch of the real function) instead**, exactly as this project's
  own established `SPRINT-018` Pattern already generalizes.

### Antipatterns to avoid

- **Assuming a `--port 8001`-adjacent process found via `Get-NetTCPConnection`
  is killable via ordinary means just because a prior sprint's own
  identical-looking symptom was** — `SPRINT-021`'s own antipattern entry
  already warned not to trust a stray dev-server process's *code
  freshness* without checking; this sprint adds: don't assume its
  *killability* either. When five independent enumeration tools all
  agree a PID doesn't exist, stop trying to kill it and pivot to an
  alternate port immediately rather than repeating the same failed
  approach.

### Open follow-ups

- Provision a real `ANTHROPIC_API_KEY`/`ANTHROPIC_MODEL` in
  `src/backend/.env` (replacing the placeholder) and re-run `AC-01`/
  `AC-03`'s own positive-result verification.
- A human (or an operator with admin rights) needs to clear whatever is
  holding port `8001` — restart the machine, or identify the owning
  process through a privileged tool this session's tooling couldn't use.
- Consider wrapping `web_research`'s real Anthropic dispatch (and/or
  `invoke_skill`'s own call to it) in a try/except that translates a real
  `AnthropicResearchError` into a cleaner error shape over HTTP, instead
  of the current raw `500 Internal Server Error` — observed live during
  this sprint's own verification, not a defect introduced by it (no task
  ever specified a try/except here), but worth a deliberate follow-up
  decision rather than leaving it as an accidental gap.

---

## Notes

**Sprint assembled 2026-08-12 (`/plan-sprints`, operator-directed batch —
the "Compass Expert" business chain).** Part of a 5-sprint sequence
(`SPRINT-020`…`SPRINT-024`); see `SPRINT-020`'s own Notes for the full
chain-partitioning rationale. This sprint is deliberately kept independent
of `SPRINT-021` (no shared dependency), so it can start as soon as
`SPRINT-020` alone is `Done` — real parallelism, not forced serialization.

**Gate: `gate: clear` 2026-08-12.** No MUST-FLAG trigger fires: (1) no
material assumption — the one real cross-sprint edge (`T06` →
`REQ-SB-20-US-01-T05`) is read directly off the decomposer's own recorded
finding, not guessed; (2) `REQ-SB-36` is not `<!-- Draft -->`/unfinalised;
(3) product-owner does not write ADRs — none touched; (4) no new
`ESCALATIONS.md` entry written by this pass; (5) not oversized (6 tasks,
M); the one `depends_on_sprints` edge introduced (`[SPRINT-020]`) is not a
MUST-FLAG "cross-sprint dependency you had to introduce" in the
problematic sense — it mirrors a real, already-recorded task-level
`depends_on` edge exactly the way `SPRINT-012`'s own `depends_on_sprints:
[SPRINT-011]` did for an equivalent real edge, not an artificial coupling;
(6) N/A (coder-only trigger); (7) no contradictory inputs; (8) not
genuinely ambiguous — one story, one natural partition, the two considered
alternatives (bundling with `REQ-SB-21-US-01` or `REQ-SB-35-US-01`)
documented and rejected above. Advances `Draft → Ready`.
