---
id: SPRINT-081
title: Vault Data Sharing — Export Data folder-tree picker + attachment-aware .sbd archive writer
status: Done                        # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Sprint Done — every story Done, every locked AC verified live. Flagged per Pipeline.md's own sprint-close convention (human skims the drafted retro + harvests Learnings.md) AND because REQ-SB-86-US-02's own standing ADR-016 human-review flag, plus two further disclosed findings from T02/T03's own live verification, are all still open in REVIEW-QUEUE.md — carried forward, not cleared by this pass."
phase: P2                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~5 tasks, M"     # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-09-01
started: "2026-09-01"              # YYYY-MM-DD when status → In Progress
completed: "2026-09-01"            # YYYY-MM-DD when status → Done
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

# SPRINT-081 — Vault Export Data (folder-tree picker + `.sbd` archive writer)

## Sprint Goal

Ship `REQ-SB-86` end-to-end: a real Settings → Vault → Export Data folder-tree
picker (`REQ-SB-86-US-01`) feeding a real export flow that auto-resolves
embedded attachments and writes one real, collision-safe `.sbd` archive in
flat or hierarchy-preserving shape (`REQ-SB-86-US-02`).

---

## Grouping Rationale & Sizing

- **Why grouped as one sprint:** Both stories are `REQ-SB-86`'s own two-way
  split of a single requirement (picker / export), share the same
  `SettingsVaultExportDataPage.tsx` frontend surface, and their combined
  5-task graph is a single connected chain with no cross-sprint reach-back
  — confirmed directly from each task file's own `depends_on:` frontmatter,
  not re-derived from story prose:
  - `REQ-SB-86-US-01-T01` `depends_on: []` — new read-only tree-listing
    endpoint.
  - `REQ-SB-86-US-01-T02` `depends_on: [REQ-SB-86-US-01-T01]` — picker page.
  - `REQ-SB-86-US-02-T01` `depends_on: []` — attachment resolver, operates
    on a plain `selection: list[str]` input contract; deliberately given NO
    edge onto `US-01-T01`, per the decomposer's own disclosed reasoning (the
    resolver and archive writer are independently buildable/testable against
    a hand-constructed selection, without needing `US-01`'s own endpoint to
    exist or run).
  - `REQ-SB-86-US-02-T02` `depends_on: [REQ-SB-86-US-02-T01]` — `.sbd`
    archive writer + `POST /vault/export-data/export`.
  - `REQ-SB-86-US-02-T03` `depends_on: [REQ-SB-86-US-02-T02,
    REQ-SB-86-US-01-T02]` — the one genuine cross-story edge, since the
    export-options screen wires its Export trigger directly onto
    `SettingsVaultExportDataPage.tsx`.
  Per hard rule 7, this graph is honoured entirely by ordinary intra-sprint
  task sequencing (`T01`s first, `US-02-T03` last) — no `depends_on_sprints`
  edge is needed, since nothing reaches back into a different sprint.
- **No split considered:** unlike `REQ-SB-85`'s own 3-story/13-task split
  across `SPRINT-079`/`SPRINT-080` (forced by a real graph fault line
  reaching back across sprints) or `SPRINT-049`→`050`'s own upstream/
  downstream split (forced by a downstream task needing the REAL running
  output of an upstream pipeline), `REQ-SB-86`'s 5-task graph has no such
  fault line — `US-02-T01`/`T02` are explicitly NOT coupled to `US-01`'s own
  endpoint at build time, and the one real cross-story edge (`US-02-T03`)
  only needs `US-01-T02`'s own frontend page to exist, which the same
  sprint already delivers earlier in the same build pass. Splitting into two
  sprints here would introduce an unnecessary `depends_on_sprints` edge with
  no corresponding real benefit — an artificial split this project's own
  `REQ-SB-85` precedent does not actually call for.
- **Sizing estimate:** ~5 tasks, M. Sits comfortably under this project's
  own most-reliable sizing band (6-9 tasks/sprint, confirmed an exact match
  multiple times — `SPRINT-020`/`022`/`028`/`048`/`080`). Sized M rather
  than S because two of the five tasks are `net-new-design-needed` frontend
  screens (the folder-tree picker, the export-options screen) — this
  project's own repeated finding is that `net-new-design-needed` frontend
  work drives real live-verification cost regardless of task count,
  matching `SPRINT-076`'s own 5-task/M precedent (also a "two independent
  foundations feeding a shared surface" shape) over the smaller `SPRINT-032`/
  `038` 5-task/S precedents (which carried no net-new screens).

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-081 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-86-US-01](../UserStories/REQ-SB-86-US-01-vault-export-data-folder-picker.md) | Settings → Vault → Export Data — real folder-tree browser, multi-select, `.md` quick filter | P2 | Done (gate: clear) — T01/T02 both Done |
| [REQ-SB-86-US-02](../UserStories/REQ-SB-86-US-02-vault-export-data-archive-writer.md) | Export — automatic embedded-attachment inclusion, flat/hierarchy extraction, single `.sbd` archive | P2 | Done (gate: flagged — ADR-016 human review pending, plus 2 further disclosed findings, see REVIEW-QUEUE.md) — T01/T02/T03 all Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** None — self-contained, no reach-back into any
  other sprint's output.
- Internal task order (per the decomposer's own `depends_on`, read directly
  from each task file): `US-01-T01` → `US-01-T02`; `US-02-T01` → `US-02-T02`
  (independent of the `US-01` pair, buildable/verifiable in either order or
  in parallel); `US-02-T03` last (needs both `US-02-T02` and `US-01-T02`).

---

## Out of Scope

- **Import of a `.sbd` file** — explicitly deferred by the operator; out of
  scope for `REQ-SB-86` entirely (both stories' own Non-Goals).
- **`REQ-SB-85`'s `.sbf` capability-bundle mechanism** (browser/export/
  import, `SPRINT-079`/`SPRINT-080`) — a deliberately separate, already-Done
  sibling capability; no shared code expected beyond the general "Settings
  sub-area with a real listing + multi-select" shape.
- **Secret-scanning selected content** — this is real, already-trusted
  vault data the operator is deliberately choosing to share; `ADR-016`
  explicitly excludes `REQ-SB-85`/`ADR-013`'s dependency-closure/secret-scan
  machinery from this story's scope.
- **A `/design REQ-SB-86` visual-polish pass** — both stories build
  functional-first per the operator's own same-day override extended from
  `REQ-SB-85`; a design pass remains a deliberately separate, later step.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact (done at `/plan-tasks`, this sprint made no further change)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` (`ADR-016`
  remains pending human review — see `REVIEW-QUEUE.md`, carried forward)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Notes (product-owner, `/plan-sprints`, 2026-09-01)

- **This sprint's own `gate: clear` is scoped to the GROUPING decision
  only** — no product-owner-level MUST-FLAG trigger fired: no assumption
  was made partitioning both `REQ-SB-86` substories into one sprint (the
  real `depends_on` edges were read directly from each task file's own
  frontmatter, not re-derived or guessed); neither story is
  `Draft`/unfinalised in the PRD; no ADR was created or changed by this
  pass (`ADR-016` was appended at `/plan-tasks`, not here); no
  `ESCALATIONS.md` entry was written by this pass; the sprint is not judged
  oversized (5 tasks sits well under this project's own confirmed 6-9
  task/sprint most-reliable band); no cross-sprint dependency had to be
  introduced (the graph is fully self-contained); the partition is
  unambiguous — there is no equally-valid alternative grouping once the
  real task graph is read (splitting into two sprints would introduce an
  artificial `depends_on_sprints` edge the real graph does not call for,
  since `US-02-T01`/`T02` are explicitly decoupled from `US-01`'s own
  endpoint).
- **What this does NOT mean:** `REQ-SB-86-US-02` itself still carries
  `gate: flagged` at the story level (the architect created `ADR-016` at
  `/plan-tasks`, trigger-3) with its own open `REVIEW-QUEUE.md` entry. That
  flag is carried forward here for visibility, not silently dropped — see
  the `Stories in Scope` status column above. Per `Pipeline.md`, a flagged
  story gate does not block `/plan-sprints` or `/implement-sprint` from
  proceeding; the human resolves the story's own flag independently, on its
  own timeline — the same carry-forward shape `SPRINT-080` already
  established for `REQ-SB-85-US-03`'s `ADR-015`/`ADR-014` review.
- No new `REVIEW-QUEUE.md` or `ESCALATIONS.md` entry was written by this
  pass — the existing `REQ-SB-86-US-02` entry in `REVIEW-QUEUE.md` already
  covers the open `ADR-016` review; duplicating it here would only fragment
  the same open item across two places.

---

## Retrospective

<!-- Filled in by the CODER when status: Done. The coder drafts this section and
sets gate: flagged. The HUMAN then skims it, approves, and copies anything under
"Patterns to carry forward" and "Antipatterns to avoid" verbatim (or expanded)
into Implementation/Learnings.md — that is the cross-sprint index future sprints
read. The retro here is a sprint-level snapshot; Learnings.md is the permanent
record. The coder does NOT write Learnings.md directly. -->

### Sizing accuracy

- **Estimated:** ~5 tasks, M — **Actual:** 5 tasks, M — matched exactly.
  Both `net-new-design-needed` frontend tasks (`US-01-T02`'s folder-tree
  picker, `US-02-T03`'s export-options screen) were, as predicted, the real
  cost center by live-verification effort, not code volume — each needed a
  genuinely non-trivial CDP session (folder-tree multi-select interaction;
  request-shape + response-byte-integrity + browser-download-mechanism
  proof) well beyond what either task's own diff size would suggest.

### What worked

- Reading the REAL current file (`REQ-SB-86-US-01-T02`'s own already-`Done`
  `SettingsVaultExportDataPage.tsx`, and its `MEMORY.md` Pattern entry)
  before building `US-02-T03` against it caught, up front, that the task's
  own "expand a folder selection client-side on confirm" step was already
  satisfied by construction — `selectedFilePaths` only ever holds file
  paths, expanded at select-time by the upstream task. Zero redundant
  expansion code written; the finding was logged as a scope-internal
  judgement call instead of silently duplicating already-correct behavior.
- A live backend-first smoke check (`curl.exe` directly against
  `POST /vault/export-data/export`, inspecting the real returned zip)
  before any browser-level check, same as `SPRINT-019`'s own established
  "backend-layer-first" precedent — caught early that the backend was
  genuinely fresh (not stale `--reload` output) and confirmed the real
  request/response contract before writing a single line of frontend
  fetch code against it.
- A minimal native `fetch`+`WebSocket` CDP driver against real headless
  Edge (no `puppeteer`/`playwright`), combined with a `window.fetch` spy
  that still calls through to the real backend, proved BOTH the exact
  outgoing request shape per extraction mode AND the real response bytes'
  own zip-signature/byte-length integrity in one pass — genuinely
  end-to-end, not a mock.
- **Independently reproducing a suspicious finding against an already-
  shipped sibling flow, in the SAME session, before concluding it's a new
  defect** — the exact "download completes fully then reports canceled"
  symptom was reproduced byte-for-byte against `REQ-SB-85-US-02-T05`'s own
  already-`Done`, unmodified Export flow using the identical
  `<a download>`/`URL.createObjectURL` technique, which is what correctly
  identified it as a CDP-headless/`blob:`-URL-download-interception
  environment quirk rather than a regression in this task's own new code.
  A speculative fix (delaying the `URL.revokeObjectURL` call) was tried,
  found to make no difference, and reverted rather than left in as
  unrequested, unproven "defensive" code.

### What didn't work

- **Trusting `Browser.downloadWillBegin`/`downloadProgress`'s own terminal
  `state` field at face value** — both events showed `receivedBytes`
  reaching `totalBytes` exactly (proof the full, real blob content
  transferred), immediately followed by a `canceled` state with
  `receivedBytes` reset to `0` in that same terminal event. Read casually,
  "canceled" looks like the download never worked; only cross-referencing
  the PRIOR event's own byte counts (already at 100%) plus a same-session
  control check against known-working sibling code revealed this is a
  reporting/interception-layer artifact specific to headless CDP's
  handling of `blob:`-URL downloads, not a real data-loss event.
- `Page.setDownloadBehavior` (the older CDP domain) silently produced ZERO
  download events at all in this Edge build (`Edg/151.0.4129.107`) —
  `Browser.setDownloadBehavior` (the current domain) was required to get
  any interception signal whatsoever. Worth checking directly rather than
  assuming either domain name still works given the CDP protocol version.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Cross-check a suspicious CDP-headless download/interaction finding
  against an already-shipped sibling flow using the IDENTICAL technique,
  in the same live session, before concluding the new code is at fault** —
  turned what looked like a possible download-trigger defect in new code
  into a correctly-isolated, disclosed, non-blocking environment/tooling
  quirk (reproduced identically on `REQ-SB-85-US-02-T05`'s own already-
  `Done` flow). Generalizes this project's own existing "independently
  confirm a new mechanism is correct via a controlled case before
  attributing a real-data failure to it" pattern (`SPRINT-028`) to the
  CDP-headless-download domain specifically.
- **When a CDP download-interception event shows `receivedBytes ===
  totalBytes` before a terminal `canceled` state, treat the byte-count
  match as the real signal of client-side transfer success** — pair it
  with an independent read of the response's own raw bytes (e.g. a
  zip-magic-number check) client-side, via a `fetch` spy that still calls
  through to the real network, rather than relying on the download
  manager's own terminal state label alone.
- **`Browser.setDownloadBehavior` (not `Page.setDownloadBehavior`) is the
  CDP domain that actually produces download-interception events on this
  project's current Edge build** — check this directly rather than
  assuming either domain still applies, especially after a browser-version
  bump.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Applying a speculative "defensive" code change (e.g. delaying
  `URL.revokeObjectURL`) to try to silence an unexplained CDP-only
  symptom, without first isolating root cause via a control check** — the
  delay was tried, made zero observable difference, and had to be
  reverted; the control-check-first approach (reproduce against an
  already-shipped sibling using identical code) would have ruled this out
  immediately without touching production code at all.

### Open follow-ups

- **`ADR-016` human review** — still open, carried forward from
  `/plan-tasks` (architect trigger-3); see `REVIEW-QUEUE.md`.
- **CDP-headless/`blob:`-URL download-interception terminal-state quirk**
  — disclosed, non-blocking, environment/tooling-specific (this Edge
  build + `Browser.setDownloadBehavior`); reproduced against both this
  sprint's own new export-options flow AND the already-`Done`
  `REQ-SB-85-US-02-T05` flow. No code action indicated; filed for
  awareness only, in case a future automated-test harness needs to account
  for it.
- **Backend CORS-header gap on an unhandled-exception response path**
  (`app/api/vault_router.py`/backend CORS config) — a genuinely
  actionable, real, disclosed finding, entirely out of this sprint's own
  `## Files to Modify` scope: a raw Python exception during request
  handling (e.g. a genuinely non-existent selected file path) returns a
  real `500` with a real body when hit directly, but the SAME response is
  opaque-`CORS`-blocked (`TypeError: Failed to fetch`, no readable status)
  when the request originates from the browser, because
  `CORSMiddleware`'s response headers are not attached to a response built
  from an unhandled exception. This task's own honest-error rendering
  still holds regardless (a generic-but-real "Request failed." message is
  shown, never a silent failure or fabricated success), but a future task
  addressing this backend gap (e.g. wrapping the route handler, or adding
  a global exception handler that preserves CORS headers) would improve
  error-message fidelity for every route in this backend, not just this
  one. Filed for a human decision on priority/scope.
