---
id: SPRINT-079
title: Artifact Browser (Settings → Artifacts) + Export — dependency closure, secret scan, .sbf archive writer
status: Done                        # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Sprint retro drafted at close, per Pipeline.md — human to skim and harvest Learnings.md. Also carries forward REQ-SB-85-US-02's own standing ADR-013/ADR-014 human-review flag (see REVIEW-QUEUE.md), unresolved, not this pass's to clear."
phase: P2                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~7 tasks, L"     # effort estimate; checked vs actual in retro
created: 2026-08-31
started: "2026-08-31"               # YYYY-MM-DD when status → In Progress
completed: "2026-08-31"            # YYYY-MM-DD when status → Done
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

# SPRINT-079 — Artifact Browser + Export (dependency closure, secret scan, `.sbf` writer)

## Sprint Goal

Ship the Settings → Artifacts browser (`REQ-SB-85-US-01`) and the full Export
pipeline built on top of it (`REQ-SB-85-US-02`) — resolve a real dependency
closure, run a secret scan with explicit per-finding operator decisions, and
produce one real `.sbf` archive.

---

## Grouping Rationale & Sizing

- **Why grouped:** `REQ-SB-85-US-01` and `REQ-SB-85-US-02` form a real,
  connected dependency chain, confirmed directly from the decomposer's own
  task frontmatter, not re-derived:
  - `US-01-T01` (no deps) → `US-01-T02` (`depends_on: [US-01-T01]`).
  - `US-02-T01`/`T02`/`T03` are each independently buildable
    (`depends_on: []`) against the already-`Done` Manager/`HermesCLI` base.
  - `US-02-T04` `depends_on: [US-02-T01, US-02-T02, US-02-T03]` (composes
    all three into the archive writer).
  - `US-02-T05` (frontend) `depends_on: [US-02-T04, REQ-SB-85-US-01-T02]` —
    the Export flow UI wires directly onto `SettingsArtifactsPage.tsx`'s own
    selection state, so it cannot build before that page exists.
  This is a one-directional dependency (`US-02` needs `US-01`'s frontend
  output; `US-01` needs nothing from `US-02`) that resolves cleanly inside
  one sprint's own internal task order — no cross-sprint edge needed for
  this half of the graph.
- **Why `US-03` (Import) is NOT included here:** `US-03` depends on this
  sprint's own output at the BACKEND layer, not just the frontend layer —
  a materially different, heavier coupling than `US-01`→`US-02`'s single
  frontend edge above: `US-03-T01` `depends_on: [REQ-SB-85-US-02-T04]`
  (shares the `sbf_archive.py` module `ADR-013` designates — "writer and
  reader share this one module"); `US-03-T05` `depends_on: [..., 
  REQ-SB-85-US-02-T01]` (the shared `HermesCLI` edit that adds both
  `export_profile` AND `import_profile`); `US-03-T06` `depends_on: [...,
  REQ-SB-85-US-01-T02]` (the Import entry point on the same Artifacts
  page). Per hard rule 7, a dependency this real and multi-pronged is
  honoured with an ordered `depends_on_sprints` edge, not folded into one
  13-task/3-story sprint — see `SPRINT-080`.
- **Why NOT one 13-task/3-story sprint:** this project's own
  `Learnings.md` sizing-calibration history caps out at 9 tasks/L as the
  largest sprint that ever matched its own estimate exactly (`SPRINT-021`,
  `SPRINT-030`); 8 tasks/L is the next most-confirmed band, matched four
  separate times (`SPRINT-010`, `SPRINT-035`, `SPRINT-049`, `SPRINT-078`).
  13 tasks across 3 stories sits well past both — a genuinely oversized
  single sprint by this project's own real, repeated evidence. Splitting
  along the graph's own real fault line (the two frontend-linked-but-
  backend-independent stories first, the backend-and-frontend-dependent
  third story second) mirrors this project's own direct precedent for a
  large multi-story requirement: `REQ-SB-82`'s six substories split across
  `SPRINT-076`/`SPRINT-077` by dependency cohesion, not arbitrarily. This
  is a disclosed product-owner sizing judgement call (either a 2-sprint or
  a 3-sprint split — `US-01` alone, then `US-02`, then `US-03` — is
  dependency-graph-legal); the 2-sprint shape is chosen because `US-01`'s
  own 2 tasks are small enough to comfortably absorb into `US-02`'s sprint
  without pushing it past the proven envelope, and a 3rd, 2-task-only
  sprint would fragment the work more than the real graph requires.
- **Sizing estimate:** ~7 tasks, L (`US-01`: 2 tasks; `US-02`: 5 tasks).
  Sits just above this project's own reliable 6-task/M band (`SPRINT-020`/
  `022`/`028`/`048`, all exact matches) and just below the 8-task/L band —
  called L because of real, disclosed complexity beyond task count: two
  new ADRs (`ADR-013`/`ADR-014`) covering a brand-new archive format, a
  recursive multi-kind dependency resolver, and a first-ever Hermes-side
  CLI wrapper extension, plus two genuinely new frontend screens
  (`net-new-design-needed`, functional-first per the operator's own
  same-day override). Expect `US-02-T02` (recursive dependency-closure
  resolver) and `US-02-T05` (dependency-preview + secret-scan confirmation
  UI, the assembly point of the whole flow) to be the heaviest of the
  seven, consistent with this project's own repeated finding that
  live-verification effort, not code volume, drives real sprint cost.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-079 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-85-US-01](../UserStories/REQ-SB-85-US-01-artifact-browser.md) | Settings → Artifacts — cross-type browsable, multi-selectable inventory of Skills/Templates/Agents/Pipelines | P2 | Done (gate: clear — T01/T02 both Done) |
| [REQ-SB-85-US-02](../UserStories/REQ-SB-85-US-02-export-dependency-closure-and-secret-scan.md) | Export — real dependency-closure resolution, explicit secret-scan confirmation, single `.sbf` bundle | P2 | Done (gate: flagged — ADR-013/ADR-014 human review pending, see Notes; all 5 tasks Done, all 7 locked ACs verified live) |

---

## Dependencies / External Blockers

- **Depends on sprints:** None.
- Internal task order (within this sprint, per the decomposer's own
  `depends_on`): `REQ-SB-85-US-01-T01` → `T02`; `REQ-SB-85-US-02-T01`/`T02`/
  `T03` independent (buildable in any order, or in parallel) → `T04`
  (composes all three) → `T05` (needs `T04` AND `REQ-SB-85-US-01-T02`).
  Recommended build order: `US-01-T01` → `US-01-T02` → `US-02-T01`/`T02`/
  `T03` (any order) → `US-02-T04` → `US-02-T05`.
- `REQ-SB-85-US-03` (this sprint's downstream consumer) is deliberately NOT
  in this sprint — see `SPRINT-080`, which records
  `depends_on_sprints: [SPRINT-079]` for exactly this reason.

---

## Out of Scope

- `REQ-SB-85-US-03` (Import — per-artifact conflict resolution, real
  target-machine provisioning) — depends on this sprint's own output at
  the backend layer (`US-02-T04`'s shared archive module, `US-02-T01`'s
  `HermesCLI` wrapper) as well as the frontend layer (`US-01-T02`);
  sequenced into `SPRINT-080` instead.
- `REQ-SB-86` (Vault Data Sharing, `.sbd`) — a deliberately separate,
  later, real-data-sharing capability; neither story in this sprint
  touches it.
- Everything either story's own Non-Goals section already excludes
  (create/edit/delete of an artifact from the browser; changing Hermes'
  own `export_profile` secret-scrub behaviour; scheduling/automating an
  export; persisting a selection across sessions).

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — done at `/plan-tasks` (architect pass, `ADR-013`/`ADR-014` sections), unchanged by this coder pass
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — `ADR-013`/`ADR-014` recorded at `/plan-tasks`; their own human-review flag stays open, tracked separately (see gate_reason)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Notes (product-owner, `/plan-sprints`, 2026-08-31)

- **This sprint's own `gate: clear` is scoped to the GROUPING decision
  only** — no product-owner-level MUST-FLAG trigger fired: no assumption
  was made partitioning this connected 13-task/3-story graph (the real
  `depends_on` edges, both within and across the three stories, were read
  directly from each story's own decomposer notes, never re-derived or
  guessed); `REQ-SB-85` is not `Draft`/unfinalised in the PRD; no ADR was
  created or changed by this pass; no `ESCALATIONS.md` entry was written by
  this pass; neither story is judged oversized for its own sprint (7 tasks
  sits inside this project's own confirmed-accurate range, and the story
  files themselves already flagged/considered a further task-level split
  and declined it); the one real cross-sprint dependency this pass
  introduces (`SPRINT-080` → this sprint) is a **disclosed, honoured**
  edge, not a contradiction of the graph (see Grouping Rationale); the
  partition is unambiguous — the graph's own real fault line (frontend-
  only coupling vs. backend-and-frontend coupling) gives one clear,
  non-arbitrary split point, not several equally-valid alternatives.
- **What this does NOT mean:** `REQ-SB-85-US-02` itself still carries
  `gate: flagged` at the story level (the architect appended `ADR-013`/
  `ADR-014` at `/plan-tasks`, trigger-3) with its own open
  `REVIEW-QUEUE.md` entry. That flag is carried forward here for
  visibility, not silently dropped — see the `Stories in Scope` status
  column above. Per `Pipeline.md`, a flagged story gate does not block
  `/plan-sprints` or `/implement-sprint` from proceeding; the human
  resolves the story's own flag independently, on its own timeline —
  exactly the same carry-forward shape `SPRINT-078` already established
  for `REQ-SB-82-US-06`'s own `ADR-011`/`ADR-012` review.
- No new `REVIEW-QUEUE.md` or `ESCALATIONS.md` entry was written by this
  pass — the existing `REQ-SB-85-US-02` entry in `REVIEW-QUEUE.md` already
  covers the open `ADR-013`/`ADR-014` review; duplicating it here would
  only fragment the same open item across two places.

---

## Retrospective

<!-- Filled in by the CODER when status: Done. The coder drafts this section and
sets gate: flagged. The HUMAN then skims it, approves, and copies anything under
"Patterns to carry forward" and "Antipatterns to avoid" verbatim (or expanded)
into Implementation/Learnings.md — that is the cross-sprint index future sprints
read. The retro here is a sprint-level snapshot; Learnings.md is the permanent
record. The coder does NOT write Learnings.md directly. -->

### Sizing accuracy

- **Estimated:** ~7 tasks, L — **Actual:** 7 tasks, L — matched exactly
  (`US-01`: 2 tasks; `US-02`: 5 tasks). The sprint's own pre-build call
  that `US-02-T02` (recursive dependency-closure resolver) and `US-02-T05`
  (frontend assembly) would be the heaviest of the seven held up — `T05`
  in particular needed a genuine dev-server-staleness recovery plus a
  4-scenario, disclosed-technique-heavy live CDP pass to cover its 4
  tagged locked ACs, not just code volume.

### What worked

- **Combining two locked ACs into one live pass when one real selection's
  own real content genuinely satisfies both preconditions at once**
  (`T05`'s `AC-01`+`AC-02`: `create-companies-partners`'s real closure has
  both a genuine multi-entry dependency chain AND zero real secret
  findings) — one fewer full page-load/CDP round trip than testing them
  against two separate selections, with zero loss of rigor since each
  AC's own assertion (call-ordering for `AC-01`; confirm→download for
  `AC-02`) was still independently checked.
- **A disposable scratch Skill with an engineered secret-shaped literal,
  created directly under the real `Hermes-Provisioning/skills/` tree and
  deleted immediately after verification** — the task's own Tests block
  named this technique explicitly; confirming its real finding via a
  direct `curl` to `/preview` BEFORE ever touching the UI caught the
  real finding key's exact shape (`skills/verify-secret-scan-t05/SKILL.md
  :9`) up front, so the later CDP assertions on `data-testid="finding-
  redact-<key>"` could target the real key with no guessing.
- **Invoking a structurally-disabled button's own real React `onClick`
  handler via its Fiber props** (`__reactProps$...`) to reach a code path
  ordinary interaction cannot — the honest-inline-error AC (`400` from an
  incomplete secret-scan decision set) is only reachable this way BY
  DESIGN, since the UI correctly prevents ever submitting an incomplete
  decision through normal clicks; this is the correct way to prove the
  guarded path still behaves honestly, not a workaround.

### What didn't work

- **Trusting an already-running dev-server process without confirming
  what it was actually serving** — `T05` began against a backend PID that
  predated `T04`'s own commit (no `--reload` flag, so `T04`'s new
  `/artifacts/export/{preview,commit}` routes were never picked up); a
  direct `GET /openapi.json` check caught this before any browser time was
  spent, but the check should have been the FIRST action taken, not one
  reached only after a live `curl` returned a genuine `404`.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Check `GET /openapi.json` (or the equivalent route-listing surface)
  for a just-shipped endpoint's real presence BEFORE any browser-level
  verification time is spent, whenever picking up a dev server that may
  predate the dependency task's own commit** — cheaper and more precise
  than a generic health-check ping, since it directly answers "does this
  process actually have my new route" rather than just "is it alive."
- **When a task's own Tests block already names a disposable-scratch-data
  induction technique for a real, once-only condition (here: a real
  secret-shaped finding), confirm the induced condition's exact real
  shape via the lightest-weight layer (a direct `curl`) BEFORE building
  any browser-level automation against it** — turns "does the UI reflect
  reality" into the only remaining open question, rather than debugging
  both the induction and the UI assertion at once.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Assuming a long-lived dev-server process left running by an earlier
  task in the same sprint is automatically current** — reconfirms this
  project's own repeated finding (`SPRINT-021`/`028`/`029`) one further
  time, this time for a NO-`--reload` process specifically (a
  `--reload`-less `uvicorn` will never pick up ANY later commit no matter
  how long it stays up, a stronger and more silent failure mode than the
  already-documented `WatchFiles`-misses-a-rapid-edit case).

### Open follow-ups

- The disclosed, non-blocking `Skill→Template` over-inclusion (a shared
  script like `vault_manager.py` enumerating every Template id pulls in
  every Template on export, not just the ones a Skill genuinely writes)
  remains live and undisplayed-as-a-caveat beyond the preview panel's own
  honest `depends_via` labeling — acceptable v1 behavior per `ADR-013`,
  not a defect, but worth a follow-up UX pass once the deferred `/design
  REQ-SB-85` sign-off happens.
- `ADR-013`/`ADR-014`'s own human review is still the standing open item
  blocking neither this sprint's nor `REQ-SB-85-US-02`'s own `Done` status
  (see `REVIEW-QUEUE.md`) — unchanged by this sprint's completion.
- A real `/design REQ-SB-85` pass (dependency-preview + secret-scan
  confirmation screens, alongside `US-01`'s own browser and `US-03`'s
  upload/conflict screens) is still expected later, per the operator's own
  functional-first override recorded in `US-02`'s frontmatter.
