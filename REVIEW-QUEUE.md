# REVIEW QUEUE

Live human inbox. Items here are awaiting a human decision before the pipeline can
proceed. Remove an item when it is resolved; add an `ESCALATIONS.md` entry if the
resolution involved a backward step.

<!-- Entry format:
- [ ] YYYY-MM-DD · **STORY-ID or SPRINT-ID** · one-line summary of what's needed
  Plain English: what's blocked, why, what the impact is if left unresolved.
  **What to do:** the concrete next step — command to run or decision to make.
  → `Implementation/UserStories/<file>.md` or `Implementation/Sprints/<file>.md`
-->

- [ ] 2026-08-10 · **SPRINT-001** · skim the sprint retrospective and harvest learnings
  Plain English: SPRINT-001 (REQ-SB-07, scheduled recurring email capture) is
  Done — all 4 tasks built and verified live. The coder drafted a
  Retrospective (sizing accuracy, what worked/didn't, patterns/antipatterns,
  open follow-ups) in the sprint file, but does not write
  `Implementation/Learnings.md` directly — that's a human step.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" and "Antipatterns
  to avoid" entries into `Implementation/Learnings.md`.
  → `Implementation/Sprints/SPRINT-001-scheduled-recurring-capture.md`

- [ ] 2026-08-11 · **SPRINT-002** · skim the sprint retrospective and harvest learnings
  Plain English: SPRINT-002 (REQ-SB-14, vault graph connectivity) is Done —
  all 4 tasks built and verified live (customer hub notes now exist,
  existing and new notes carry wikilinks to them, manual hub-note content
  survives reruns). The coder drafted a Retrospective, but does not write
  `Implementation/Learnings.md` directly — that's a human step.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" entries into
  `Implementation/Learnings.md` (no new antipatterns this sprint).
  → `Implementation/Sprints/SPRINT-002-vault-graph-connectivity.md`

- [ ] 2026-08-11 · **SPRINT-003** · skim the sprint retrospective and harvest learnings
  Plain English: SPRINT-003 (REQ-SB-15, Obsidian manual-entry templates +
  in-vault guide) is Done — both tasks built and verified (four templates,
  one guide note, all matching the resolved schema). The coder drafted a
  Retrospective, but does not write `Implementation/Learnings.md` directly.
  The Obsidian Settings → Templates → "Template folder location" step is
  now done (operator confirmed 2026-08-11) — only the Learnings harvest
  remains open.
  **What to do:** read `## Retrospective` in the sprint file and copy the
  "Patterns to carry forward" entries into `Implementation/Learnings.md`.
  → `Implementation/Sprints/SPRINT-003-manual-entry-templates-and-guide.md`

- [ ] 2026-08-11 · **SPRINT-004** · skim the sprint retrospective and harvest learnings
  Plain English: SPRINT-004 (REQ-SB-10, Person notes from email capture) is
  Done — all 4 tasks built and verified live against the real inbox and
  vault (20 real Person notes now exist, correctly tagged/linked by
  company/known-customer status, manual content survives reruns). The
  coder drafted a Retrospective, but does not write
  `Implementation/Learnings.md` directly.
  **What to do:** read `## Retrospective` in the sprint file and copy the
  "Patterns to carry forward" entries into `Implementation/Learnings.md`
  (no new antipatterns this sprint).
  → `Implementation/Sprints/SPRINT-004-person-notes-from-email-capture.md`


- [ ] 2026-08-11 · **ESC-003** · recommend `/bug` capture — real, latent
  `insert_body_line_if_missing` corruption found on `Work/People/
  karimlouis@microsoft.com.md`
  Plain English: while completing `REQ-SB-16-US-01-T04`'s live migration
  verification, `vault_writer.insert_body_line_if_missing`'s fixed
  `body_start = end + 6` offset was found to corrupt any note whose body
  lacks the standard blank line after the frontmatter's closing `---` —
  every insertion lands at the same fixed byte offset regardless of prior
  content, so a note with this pre-existing structural defect gets
  progressively more corrupted on each subsequent insertion, rather than
  the corruption being a one-off. The one real note found in this state
  (`Work/People/karimlouis@microsoft.com.md`, structurally malformed since
  an old `REQ-SB-10-US-01-T04` verification pass, predating this session)
  was manually repaired directly (byte-exact, not retyped) as part of this
  task's own due diligence — not a code fix. Full detail:
  `ESCALATIONS.md` → `ESC-003`.
  **What to do:** run `/bug` to formally capture this as a `BUG-NNN`
  (Area: Logic) so it can be batched into a `BUGFIX-NN-US-01` fix story via
  `/triage` — the underlying primitive (used by multiple already-`Done`
  stories: `REQ-SB-10`, `REQ-SB-14`, `REQ-SB-16`) should either compute the
  true body-start position dynamically or otherwise tolerate a missing
  blank line, so this can't silently recur on any other hand-edited note.
  → `ESCALATIONS.md`

- [ ] 2026-08-11 · **SPRINT-007** · skim the sprint retrospective and harvest learnings
  Plain English: SPRINT-007 (`REQ-SB-16`, Partner hub notes + Microsoft
  migration; `REQ-SB-17`, Research notes template + guide) is Done — both
  stories' every locked AC verified live against the real vault, including
  a genuine mid-flight ADR correction (`ADR-012`, resolving `ESC-001`) and
  a real, latent primitive-level bug found and worked around during final
  verification (`ESC-003`, still `Open` — see the entry above). The coder
  drafted a Retrospective, but does not write `Implementation/
  Learnings.md` directly.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" and "Antipatterns
  to avoid" entries into `Implementation/Learnings.md`.
  → `Implementation/Sprints/SPRINT-007-partner-hub-notes-and-research-notes.md`

- [ ] 2026-08-11 · **SPRINT-008** · skim the sprint retrospective and harvest learnings
  Plain English: SPRINT-008 (REQ-SB-12-US-01, app shell + Agents Map +
  Settings reachability — the first frontend build in this project) is
  Done — all 4 tasks built and verified live in a real browser (headless
  Chrome via CDP; no test-stack ADR exists yet). All 6 locked ACs pass,
  zero console errors, zero integration defects at the final end-to-end
  pass. The coder drafted a Retrospective (patterns: CDP-based zero-
  dependency browser verification, pinning ADR-named dependency versions,
  incremental per-task live verification; antipattern: task prose
  mentioning a file its own `Files to Modify` list omits), but does not
  write `Implementation/Learnings.md` directly. This is also the sprint
  SPRINT-009/SPRINT-010 both depend on (`depends_on_sprints: [SPRINT-008]`
  once they're grouped) — the retro's frontend-specific patterns are worth
  reading before those sprints start.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" and "Antipatterns
  to avoid" entries into `Implementation/Learnings.md`.
  → `Implementation/Sprints/SPRINT-008-app-shell-agents-map-and-settings.md`

- [ ] 2026-08-11 · **SPRINT-005** · skim the sprint retrospective and harvest learnings
  Plain English: SPRINT-005 (`BUGFIX-01-US-01`, closes `BUG-001` — Email
  notes wikilink to their sender's Person note) is Done — both tasks
  built and verified live against the real inbox and vault (the
  going-forward hook confirmed via a real newly-captured email at server
  start; the retrofit linked 249 already-captured Email notes in one run,
  idempotent on rerun, blank-`sender_email` notes correctly skipped).
  `BUG-001` is flipped to `Closed` in both `BUGS.md` and `BACKLOG.md`. The
  coder drafted a Retrospective, but does not write
  `Implementation/Learnings.md` directly.
  **What to do:** read `## Retrospective` in the sprint file and copy the
  "Patterns to carry forward" entries into `Implementation/Learnings.md`
  (no new antipatterns this sprint).
  → `Implementation/Sprints/SPRINT-005-email-notes-wikilink-to-sender-person-note.md`

- [ ] 2026-08-11 · **REQ-SB-08-US-01** · review `ADR-013` (supersedes
  ADR-008 point 2) and `T06` before the fix is built (`ESC-002`)
  Plain English: **decided** — operator directive 2026-08-11, "fix this
  now." `REQ-SB-08-US-01`'s `T03`/`T05` live verification found that a
  real recurring meeting's 3 occurrences on the live calendar all return
  the **exact same full Outlook `EntryID`** — not just a coincidental
  filename-suffix match (full detail: `ESCALATIONS.md` → `ESC-002`). A
  new ADR, `ADR-013`, now replaces `EntryID` with
  `AppointmentItem.GlobalAppointmentID` (hashed in full, not sliced) as
  the Meeting-occurrence dedup/filename key, with a backward-compatible
  legacy-path fallback check so none of the 38 already-captured real
  Meeting notes needs migrating or renaming. A new task,
  `REQ-SB-08-US-01-T06`, implements it. `ADR-008` stays `Accepted`
  (unedited) — only its point 2 is superseded, linked both ways. The
  story's own `status:` stays `Done` (every locked AC still passes; this
  is additive hardening, not a reopening).
  **What to do:** review `ADR-013` in
  `Implementation/Architecture/ADR.md` (approve or reject the
  `GlobalAppointmentID`-hash + legacy-path-fallback design, and the
  accepted narrow residual risk named in its own Consequences section),
  and `REQ-SB-08-US-01-T06` in `Implementation/Tasks/
  REQ-SB-08-US-01-T06-global-appointment-id-dedup-key-fix.md`. If
  approved, run `/plan-sprints` to group `T06` into a new sprint (its
  parent story's own `SPRINT-006` is already `Done`), then
  `/implement-sprint` to build and live-verify it — `ESC-002` flips to
  `Resolved` once that verification passes.
  → `Implementation/UserStories/REQ-SB-08-US-01-meeting-notes-from-calendar-capture.md`

  **Update, 2026-08-12 — Approved.** Operator approved `ADR-013` as
  written. `gate:` reset to `clear`. `T06` eligible for `/plan-sprints`.

- [ ] 2026-08-11 · **REQ-SB-12-US-02-T03** · spot-check the new CORS policy
  added to `app/main.py` (first browser->backend fetch call in this codebase)
  Plain English: `REQ-SB-12-US-02-T03` (My Day router) is the first task in
  this codebase to make a real browser fetch from `src/frontend` to
  `src/backend` — no CORS middleware existed anywhere before this, and
  without it every fetch fails outright (confirmed live: an uncaught
  `TypeError: Failed to fetch`, blocking all 8 of `REQ-SB-12-US-02`'s
  locked ACs from ever passing). Fixed by adding
  `fastapi.middleware.cors.CORSMiddleware` to `app/main.py`, scoped to the
  Vite dev server's own default origins (`http://localhost:5173`,
  `http://127.0.0.1:5173`) rather than a wildcard — no new dependency
  (ships inside the already-installed `fastapi` package), confined to
  `main.py` (already in this task's own `Files to Modify`). This is a
  scope-internal assumption (the exact allowed-origins list was not
  dictated by any ADR/task text), not an escalation. A concurrent
  `REQ-SB-13-US-01` pass already had to extend the literal origins list
  with `5174` (Vite auto-incrementing past an already-bound `5173`) —
  real friction with the hardcoded-literal-ports approach, worth a
  human/architect look at whether this deserves a proper ADR (e.g. an
  env-var-driven allowed-origins list, or a dev-only wildcard) before a
  third frontend-calling-backend story repeats the same ad hoc pattern.
  **What to do:** review the `CORSMiddleware` block in
  `src/backend/app/main.py` (added by `REQ-SB-12-US-02-T03`, extended by
  `REQ-SB-13-US-01`); accept as-is, or direct a future task/ADR to
  formalize the allowed-origins policy (e.g. driven by a `.env` value
  matching `VITE_API_BASE_URL`'s own convention) instead of literal
  hardcoded ports.
  → `Implementation/Tasks/REQ-SB-12-US-02-T03-my-day-router.md`

- [ ] 2026-08-11 · **SPRINT-009** · skim the sprint retrospective and harvest learnings
  Plain English: SPRINT-009 (`REQ-SB-12-US-02`, My Day dashboard + Emails/
  Calendar/To-Do drill-down pages) is Done — all 7 tasks built and
  verified live (backend smoke-checked against the real vault; frontend
  verified in a real browser via headless-Chrome CDP). All 8 locked ACs
  pass, zero console errors, `npm run build` clean. The coder drafted a
  Retrospective (patterns: backend-layer-first live verification,
  temporary stub-and-revert for states real data can no longer produce
  naturally, checking CORS before any first cross-layer fetch call;
  antipatterns: a destructive blanket `taskkill /IM chrome.exe /F /T` was
  run in error during this sprint's own cleanup — see below — and the
  CORS gap not caught until live verification), but does not write
  `Implementation/Learnings.md` directly.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" and "Antipatterns
  to avoid" entries into `Implementation/Learnings.md`. Separately: the
  coder self-reported running `taskkill /IM chrome.exe /F /T` (kill-by-
  image-name, not by the specific PID already identified) while cleaning
  up its own headless-Chrome verification instance — a real risk to any
  other concurrent session's own browser process or a real user Chrome
  window. No harm was confirmed, but worth a human check that no other
  concurrent session's own verification was disrupted around 2026-08-11.
  → `Implementation/Sprints/SPRINT-009-my-day-dashboard-and-drilldowns.md`

- [ ] 2026-08-11 · **SPRINT-006** · skim the sprint retrospective and harvest learnings
  Plain English: SPRINT-006 (REQ-SB-08, meeting notes from calendar
  capture) is Done — all 5 tasks built and verified live against the real
  Outlook calendar and vault (38 real Meeting notes captured correctly,
  classified by customer via attendee majority vote, attendee Person notes
  created/reused, vault-owner self-exclusion confirmed on real data,
  idempotency confirmed across multiple reruns). The coder drafted a
  Retrospective, but does not write `Implementation/Learnings.md` directly.
  One genuine architectural finding (`ESC-002`, see the entry above) was
  surfaced and flagged, not silently worked around.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" and "Antipatterns
  to avoid" entries into `Implementation/Learnings.md`.
  → `Implementation/Sprints/SPRINT-006-meeting-notes-from-calendar-capture.md`

- [ ] 2026-08-11 · **SPRINT-010** · skim the sprint retrospective and harvest learnings
  Plain English: SPRINT-010 (`REQ-SB-13-US-01`, embedded agent detail
  panel — settings, actions, chat, and unified communication history) is
  Done — all 8 tasks built and verified live. All 8 locked ACs pass,
  including both trust-surface-defining scenarios: `Scenario 7`/`AC-08`
  (a chat message triggering a real backend action, confirmed with one
  real Outlook/Compass/vault-write capture run through the actual chat
  UI) and `Scenario 3b`/`AC-04` (chat + background run events unified in
  one chronological history list). `npm run build` clean, zero blocked
  tasks, zero `ESCALATIONS.md` entries. The coder drafted a Retrospective
  (patterns: scanning a port range instead of one fallback, reserving an
  untouched fixture agent up front for an empty-state AC, consolidating
  repeated real-side-effect verification across sibling tasks;
  antipattern: trusting a task file's own "Before" narrative for a shared
  file without re-reading it fresh — this sprint ran genuinely
  concurrently with SPRINT-006/007/009 against the same working tree),
  but does not write `Implementation/Learnings.md` directly.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" and "Antipatterns
  to avoid" entries into `Implementation/Learnings.md`.
  → `Implementation/Sprints/SPRINT-010-embedded-agent-chat-and-communication-history.md`

- [ ] 2026-08-11 · **REQ-SB-18-US-01 / REQ-SB-19-US-01** · review `ADR-014`
  before tasks are locked (agent Sections & LLM Providers become mutable,
  persisted, API-driven state alongside the static `agent_registry.py`)
  Plain English: `/plan-tasks` step 1 (architect) wrote one new ADR,
  `ADR-014`, shared by both stories (they were designed together and share
  the same underlying mechanism). It decides how `app/business/
  agent_registry.py`'s currently fully-static, hardcoded `AGENTS` dict
  gains two new mutable, user-editable properties per agent — which
  Section it belongs to, and which LLM Provider it uses — **without**
  making the registry itself mutable: two new sibling `.second-brain/`
  JSON state files (`agent_sections.json`, `agent_providers.json`), two
  new business modules (`section_registry.py`, `provider_registry.py`)
  owning CRUD/seeding/self-healing default assignment/the block-until-
  unused deletion check, two new routers (`/sections`, `/providers`) plus
  a shared `PATCH /agents/{id}` verb, plaintext-at-rest credential storage
  (never returned by any endpoint), an explicit decision that editing the
  pre-seeded "Compass" Provider entry from Settings does **not** affect
  the real, live Compass call path this pass, and a "Provider has no real
  client yet" honesty check reusing `ADR-011`'s existing "declared but
  unbuilt" precedent one layer up. `layoutAgents.ts`'s frontend layout also
  becomes genuinely N-section-generic (replacing its fixed 3-section
  lookup table), per the approved "5 sections" prototype reference state.
  `ADR-011` itself is **not** modified — it stays `Accepted`, and this new
  ADR is explicit about composing alongside it, not reopening it.
  **What to do:** review `ADR-014` in `Implementation/Architecture/ADR.md`
  — in particular, the "Compass Provider entry is CRUD-editable but inert
  this pass" decision (point 5) and the blanket Provider-availability gate
  at `_invoke_action` (point 7, flagged in Consequences as needing revisit
  once a non-LLM-backed real action exists) — approve or reject, then run
  `/plan-tasks` again if you change it. Both stories' `## Notes` carry the
  full architecture-scope file lists the decomposer/coder are bounded by.
  → `Implementation/UserStories/REQ-SB-18-US-01-dynamic-agent-sections-and-assignment.md`
  → `Implementation/UserStories/REQ-SB-19-US-01-per-agent-llm-provider-selection.md`

  **Update, 2026-08-11 (`/plan-tasks` step 2 — decomposer):** per
  `Implementation/Pipeline.md`'s "an ADR-creation flag does not halt
  `/plan-tasks`" rule, decomposition proceeded without waiting for this
  review. `REQ-SB-18-US-01` — 9 scenarios locked as `AC-01`…`AC-09`, 8
  tasks (`T01`–`T08`). `REQ-SB-19-US-01` — 8 scenarios locked as
  `AC-01`…`AC-08`, 6 tasks (`T01`–`T06`). Both stories are now
  `status: Ready` (every AC locked, every locked AC has a tagged
  verification step, `depends_on` acyclic) with all their tasks written
  directly at `status: Ready`. `gate: flagged` is unchanged on both — this
  review is still the open item; if `ADR-014` changes as a result, reset
  the affected story/task `status:` back and re-run `/plan-tasks`. The two
  stories' shared surface (`agents_router.py`'s `PATCH /agents/{id}`,
  `AgentDetailPanel.tsx`, `agentsApiClient.ts`, `settingsApiClient.ts`,
  `SettingsPage.tsx`) is sequenced via explicit cross-story `depends_on`
  edges (`REQ-SB-18-US-01`'s Section-portion tasks land first;
  `REQ-SB-19-US-01`'s Provider-portion tasks each depend on the
  corresponding `REQ-SB-18-US-01` task) so the two stories are safe to
  build in the same sprint without two tasks racing on the same file —
  a `/plan-sprints` decision, not decided here.

  **Update, 2026-08-11 (`/implement-sprint` — coder, `SPRINT-011`):**
  `REQ-SB-18-US-01`'s 8 tasks are all built and live-verified; all 9
  locked ACs pass against `ADR-014` as currently written. Story and
  `SPRINT-011` both advanced to `status: Done`. **This review is still the
  open item** — the coder does not clear an ADR-creation flag; if the
  human's review of `ADR-014` changes it, reset `REQ-SB-18-US-01`'s
  affected task(s) back to `Ready` and rebuild (the story's own `Done`
  status does not freeze it against a backward ADR correction, per
  Pipeline.md hard rule 1/6). `REQ-SB-19-US-01`/`SPRINT-012` remains
  unbuilt, still gated on this same open review.

  **Update, 2026-08-11 (`/implement-sprint` — coder, `SPRINT-012`):**
  `REQ-SB-19-US-01`'s 6 tasks are all built and live-verified; all 8
  locked ACs pass against `ADR-014` as currently written, including both
  trust-surface-defining scenarios (`AC-07` — an agent using Compass
  behaves identically even after editing the pre-seeded Compass Provider
  entry's representation; `AC-08` — an agent pointed at a non-Compass
  Provider honestly reports unavailability, confirmed via its own history
  log that no real Outlook/Compass call occurred, with no silent Compass
  fallback and no fabricated response). Story and `SPRINT-012` both
  advanced to `status: Done`. **This review is still the open item** — the
  coder does not clear an ADR-creation flag; if the human's review of
  `ADR-014` changes it, reset the affected task(s) in *either* story back
  to `Ready` and rebuild. Both `REQ-SB-18-US-01` and `REQ-SB-19-US-01` (the
  ADR's full scope) are now fully built and live-verified against `ADR-014`
  as currently written — this is the natural point for the human review to
  close, one way or the other.

  **Update, 2026-08-12 — `ADR-014` Approved.** Operator approved as
  written; no changes requested. `REQ-SB-18-US-01`/`REQ-SB-19-US-01`
  `gate:` reset to `clear` on both — no rebuild needed, both already
  built and live-verified against this ADR. This item is closed.

  **Separately flagged for a human glance (not a blocker):**
  `provider_registry.create_provider` has no same-slug-collision guard,
  unlike `section_registry.create_section`'s explicit existing-entry
  return — found live during `REQ-SB-19-US-01-T06`'s own verification (a
  test script's accidental double-POST produced two `Provider` entries
  sharing one `id`). This is the task's own literal, decomposer-authored
  code, not a coder deviation; no locked AC requires idempotent-on-name
  creation, so it did not block anything. See
  `Implementation/Tasks/REQ-SB-19-US-01-T02-provider-registry.md`'s own
  Implementation Log and `SPRINT-012`'s Retrospective for full detail.

- [ ] 2026-08-11 · **REQ-SB-23-US-01** · `/design REQ-SB-23` has now run —
  superseded first by the combined entry below, then by REQ-SB-23's own
  2026-08-11 conversational re-spec (`ESC-009`) — the "Quick Capture" card
  no longer covers this story at all
  Plain English: REQ-SB-23 (My Day Intake Agent) originally needed a way
  for the user to type free-form text and hand it to an agent from the My
  Day dashboard. `/design` produced a one-shot "Quick Capture" card on
  `html-prototype/my-day.html` for that original design — see the combined
  REQ-SB-20/21/23 entry below. **REQ-SB-23 was then revised the same day to
  a genuinely conversational requirement** (real chat thread, agent
  follow-up questions, mid-conversation refinement/hints), and
  `REQ-SB-23-US-01` has been re-specced in place to match. The "Quick
  Capture" card's prior browser sign-off (if it happens) does **not**
  extend to cover this revised story — it is a one-shot input+submit shape,
  not a chat thread. This original entry, and the combined entry below, are
  both left in place for history; do not act on either as coverage for
  REQ-SB-23 going forward.
  **What to do:** see the new entry dated 2026-08-11 · **REQ-SB-23-US-01**
  · "re-specced for the conversational revision" for the current, correct
  next step.
  → `Implementation/UserStories/REQ-SB-23-US-01-my-day-intake-agent.md`

- [ ] 2026-08-11 · **REQ-SB-24-US-01** · sequence behind `REQ-SB-19-US-01`,
  then run `/design`
  Plain English: the feasibility risk is resolved (2026-08-11) — a real
  live Compass API call confirmed the response includes a full `usage`
  object (`prompt_tokens`/`completion_tokens`/`total_tokens`), so per-call
  token tracking is feasible with no fallback estimation needed.
  What's left: this story's primary dependency, `REQ-SB-19`, is still only
  `Ready` (not `Done`) — building this story's UI ahead of that would mean
  extending a screen that doesn't exist yet. No approved prototype screen
  shows either a Provider's pricing fields or a per-agent cost display —
  confirmed by direct inspection.
  **What to do:** once `REQ-SB-19-US-01` ships, run `/design REQ-SB-24` to
  design the pricing fields and cost-display UI, then proceed to
  `/plan-tasks`.
  → `Implementation/UserStories/REQ-SB-24-US-01-per-agent-token-consumption-and-cost-tracking.md`

- [ ] 2026-08-11 · **REQ-SB-20-US-01 + REQ-SB-21-US-01** · `/design` has now
  run — superseded by the combined entry below, browser sign-off still
  needed; REQ-SB-20 remains additionally blocked on `REQ-SB-18-US-01`
  Plain English: both stories had their genuinely open product/architecture
  questions resolved directly by the operator (2026-08-11 — `ESC-004`/
  `ESC-005` both `Resolved`). `/design` has now produced the Keywords/
  Working-mode picker rows and the Chat pending-approval demo on
  `html-prototype/agents-map.html` — see the combined REQ-SB-20/21/23 entry
  below for the full description and sign-off instructions. This original
  entry is left in place for history; do not act on it separately. REQ-SB-20
  still cannot proceed to `/plan-tasks` until `REQ-SB-18-US-01` is `Done`
  (it already is, per `SPRINT-011` — recheck `REQ-SB-18-US-01`'s own status
  before resetting REQ-SB-20's gate).
  **What to do:** see the entry below dated 2026-08-11 · **Prototype
  update: agents-map.html, my-day.html, my-day-approvals.html**.
  → `Implementation/UserStories/REQ-SB-20-US-01-section-hub-intelligence-and-cross-section-routing.md`
  → `Implementation/UserStories/REQ-SB-21-US-01-agent-working-modes.md`

- [ ] 2026-08-11 · **SPRINT-011** · skim the sprint retrospective and harvest learnings
  Plain English: SPRINT-011 (`REQ-SB-18-US-01`, dynamic agent Sections —
  CRUD, per-agent assignment, N-generic Agents Map layout) is Done — all 8
  tasks built and verified live (real `.second-brain/agent_sections.json`
  state, real backend on `:8001`, real frontend via headless-Chrome-via-
  CDP on `:5173`). All 9 locked ACs pass, `npx tsc --noEmit`/`npm run
  build` both clean, zero `ESCALATIONS.md` entries. The coder drafted a
  Retrospective (patterns: React-Fiber-props direct-invoke for verifying a
  disabled-gated click handler, topology-count assertions for computed
  polar-layout rendering; antipatterns: a decomposer's literal per-file
  diff missed one same-pattern reference elsewhere in a file it otherwise
  named, a task's inline "ported verbatim" CSS snippet had drifted from
  the actual prototype file), but does not write
  `Implementation/Learnings.md` directly. Note this sprint's story is
  `Done` but still `gate: flagged` for a separate, unrelated reason —
  `ADR-014`'s own still-open human review (see the `REQ-SB-18-US-01 /
  REQ-SB-19-US-01` entry above) — not cleared by this retro-harvest item.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" and "Antipatterns
  to avoid" entries into `Implementation/Learnings.md`.
  → `Implementation/Sprints/SPRINT-011-dynamic-agent-sections-and-assignment.md`

- [ ] 2026-08-11 · **Prototype update: agents-map.html, my-day.html,
  my-day-approvals.html (new)** · needs browser sign-off
  Plain English: designed for `REQ-SB-20-US-01` (Section Hub Intelligence &
  Cross-Section Routing), `REQ-SB-21-US-01` (Agent Working Modes), and
  `REQ-SB-23-US-01` (My Day Intake Agent) — all three already have every
  Gherkin scenario locked, including the operator-resolved decisions
  recorded in each story's own `## Notes` (free-text keywords, keyword-match
  routing, cross-Section only for REQ-SB-20; default mode Autonomous, a
  real Pending Approvals surface built now for REQ-SB-21). Four screen
  changes: (1) every agent's Settings `kv-list` on `agents-map.html` gains
  Keywords (free-text, empty on To-Do Capture to demonstrate REQ-SB-20
  Scenario 4) and Working mode (Autonomous/Supervised/Manual — Meeting
  Capture and People Notes set Supervised, To-Do Capture set Manual, the
  rest default Autonomous) rows, following the exact Section/Provider
  picker-row pattern already approved for REQ-SB-18/19; (2) Meeting
  Capture's Chat block gains a pending-approval proposal card (new
  `.chat-proposal` pattern — dashed-warning/solid-success/solid-danger,
  all from existing tokens), toggled pending/approved/declined via a small
  state-switcher nested inside the chat thread itself; (3) a new Pending
  Approvals surface — a 5th My Day dashboard card plus a new
  `my-day-approvals.html` drill-down, reusing the exact `.item-list`
  pattern the other four My Day pages already use — placed on My Day
  (not Settings, not a new nav item) because My Day is this project's
  existing "things needing my attention today" surface, which is exactly
  what a Supervised agent's background-pipeline proposal is; populated
  with the two Supervised agents' example proposals, plus an empty
  "queue caught up" state; (4) a new "Quick Capture" card at the top of
  `my-day.html` (the My Day Intake Agent) — a free-text input + Capture
  button plus an `.item-list` history demonstrating all 4 of REQ-SB-23's
  scenarios at once (a customer-classified filing with the exact
  tags-and-wikilinks copy from `MEMORY.md`'s standing schema, an
  unclassified filing, a second same-day filing proving no collision, and
  a classification-FAILED submission with its original text visibly
  preserved and a Retry affordance) plus a first-run empty state. No new
  CSS framework, no hardcoded colours — every new visual element is built
  from `styles.css`'s existing tokens (`--color-warning/success/danger`,
  the same `color-mix(...)` technique `.btn-danger`/`.badge-*` already
  use) and existing components (`.kv-row`/`.kv-select`, `.item-list`/
  `.item-row`/`.item-row-actions`, `.chat-thread`/`.chat-message`,
  `.state-switcher`, `.card`, `.empty-state`); the only genuinely new
  pattern is `.chat-proposal` (added to `styles.css`).
  **Update, 2026-08-11 — REQ-SB-23's portion (item 4, the "Quick Capture"
  card) is superseded, not just pending sign-off.** REQ-SB-23 was revised
  the same day to a genuinely conversational requirement (real chat
  thread, agent follow-up questions, mid-conversation refinement/hints);
  `REQ-SB-23-US-01` has been re-specced accordingly (see `ESCALATIONS.md` →
  `ESC-009`). The "Quick Capture" card described here (a one-shot
  input+submit row) does **not** cover the revised story — sign-off on it
  would not clear REQ-SB-23-US-01's own flag. Items (1)-(3) (Keywords/
  Working-mode kv-rows, the chat-proposal card, and the Pending Approvals
  surface, all for REQ-SB-20/REQ-SB-21) are unaffected by this and remain
  valid as designed.
  **What to do:** open `html-prototype/agents-map.html` (click each agent
  node, especially Meeting Capture's Chat block and its 3-state switcher)
  and `html-prototype/my-day-approvals.html` in a browser and review items
  (1)-(3). Once approved, reset `REQ-SB-20-US-01`/`REQ-SB-21-US-01`'s
  `gate:` to `clear` and run `/plan-tasks` on those two requirements —
  REQ-SB-20 additionally needs `REQ-SB-18-US-01` confirmed `Done` first (it
  already is, per `SPRINT-011`, but re-verify before resetting). For
  REQ-SB-23, do NOT sign off on the existing "Quick Capture" card as
  coverage — see the separate `REQ-SB-23-US-01` · "re-specced for the
  conversational revision" entry above for its own next step (a fresh
  `/design REQ-SB-23` pass, once `REQ-SB-25-US-01` is far enough along to
  design against).
  → `html-prototype/agents-map.html`
  → `html-prototype/my-day.html`
  → `html-prototype/my-day-approvals.html`
  → `Implementation/UserStories/REQ-SB-20-US-01-section-hub-intelligence-and-cross-section-routing.md`
  → `Implementation/UserStories/REQ-SB-21-US-01-agent-working-modes.md`
  → `Implementation/UserStories/REQ-SB-23-US-01-my-day-intake-agent.md`

  **Update, 2026-08-12 — Items (1)-(3) Approved, live-verified.** Operator
  pre-authorized UI/design sign-offs while away; this is #2 of that run.
  Verified live in the browser (not just traced): (1) every agent's
  Settings panel shows Section/Provider/Keywords/Working-mode rows
  (confirmed via direct DOM text extraction across all 5 agents — Meeting
  Capture and People Notes correctly `Supervised`, To-Do Capture correctly
  `Manual` with "No keywords assigned" messaging, others default
  `Autonomous`); (2) Meeting Capture's Chat block shows the pending-
  approval proposal card with a working Pending/Approved/Declined
  state-switcher, confirmed by screenshot; (3) `my-day-approvals.html`
  shows both example Supervised-agent proposals (Meeting Capture, People
  Notes) with Approve/Decline controls, plus the empty "queue caught up"
  state available via its own state switcher. `REQ-SB-20-US-01`/
  `REQ-SB-21-US-01` `gate:` reset to `clear` — `REQ-SB-18-US-01`
  (REQ-SB-20's remaining dependency) is confirmed `Done`. **Next:** run
  `/plan-tasks` on both. (Item 4, the My Day Intake Agent "Quick Capture"
  card, remains superseded per the entry above — not covered by this
  approval, still needs its own fresh `/design REQ-SB-23` pass.)

- [ ] 2026-08-11 · **SPRINT-013** · skim the sprint retrospective and harvest learnings
  Plain English: SPRINT-013 (`REQ-SB-22-US-01`, My Day drill-downs and
  dashboard counts scoped to a rolling 7-day window) is Done — both tasks
  built and verified live against the real vault (179 Email notes, 39
  Meeting notes; windowed to 21/17) and a real browser (headless-Chrome
  CDP). All 6 locked ACs pass, including both backend-only ACs that
  needed direct manipulation to verify at all: `AC-03` (a real
  out-of-window note of each kind confirmed genuinely absent from the
  returned lists) and `AC-04` (a monkeypatched `datetime` simulating 10
  days later produced a correctly-shifted window/result set, then
  reverted to restore the exact original result — proving the window
  recomputes fresh on every call, never cached). `npm run build` clean,
  zero console errors, zero blocked tasks, zero `ESCALATIONS.md` entries.
  The coder drafted a Retrospective (patterns: server-side
  monkeypatch-and-revert for "recomputes fresh, never cached" ACs,
  process-only env-var override instead of editing a committed
  `.env.local`; antipatterns: a backgrounded dev-server process chained
  with `&` inside a compound `Bash` call didn't reliably track to one PID,
  `npm`/`node` are not on the `Bash` tool's own `PATH` in this
  environment, a headless-Chrome CDP process died silently mid-sprint and
  needed a relaunch), but does not write `Implementation/Learnings.md`
  directly.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" and "Antipatterns
  to avoid" entries into `Implementation/Learnings.md`.
  → `Implementation/Sprints/SPRINT-013-my-day-rolling-7-day-window.md`

- [ ] 2026-08-11 · **REQ-SB-29-US-01** · decide the retrieval mechanism
  (`ESC-008`), then run `/design`
  Plain English: REQ-SB-29 (Agent-to-Tag/Folder Scoping) needs an agent,
  once assigned a vault tag/folder scope, to actually retrieve real notes
  matching that scope on request — not just have the assignment stored.
  The obvious foundation for that (REQ-SB-01 Vault Indexing, REQ-SB-02
  Browse & Search) doesn't exist yet — neither even has a `Draft` story.
  But this codebase already has working precedent for narrower, ad hoc,
  tag/folder-scoped vault-read primitives built without a general indexer
  (e.g. `list_notes_in_kind_folder`, `list_known_customers`, the migration-
  scan pattern) — whether one of those is an acceptable substitute for this
  story's retrieval half, or whether REQ-SB-01/02 genuinely need to ship
  first, is a real product/architecture call, not decided here.
  **What to do:** decide (a) build REQ-SB-29's retrieval via a narrower,
  story-scoped primitive now, matching existing precedent, or (b) wait for
  REQ-SB-01/02. Record the decision in `REQ-SB-29-US-01`'s `## Notes` and
  flip `ESCALATIONS.md` → `ESC-008` to `Resolved`. Separately, no
  `html-prototype/` screen has a Vault scope field on the Agent Settings
  surface — run `/design REQ-SB-29` once the mechanism question is settled,
  then `/plan-tasks`.
  → `Implementation/UserStories/REQ-SB-29-US-01-agent-to-tag-folder-scoping.md`
  → `ESCALATIONS.md`

  **Update, 2026-08-12 — Resolved.** Operator decided: build the
  narrower, story-scoped ad hoc retrieval primitive now, matching
  existing precedent — not a wait on `REQ-SB-01`/`REQ-SB-02`. `gate:`
  reset to `clear`. `ESCALATIONS.md` → `ESC-008` flipped to `Resolved`.
  Still net-new-design-needed — run `/design REQ-SB-29` before
  `/plan-tasks`.

- [ ] 2026-08-11 · **REQ-SB-23-US-01** · re-specced for the conversational
  revision (`ESC-009`) — needs a fresh `/design` pass, and still blocked on
  `REQ-SB-25-US-01` shipping
  Plain English: REQ-SB-23 (My Day Intake Agent) was revised 2026-08-11
  from a one-shot input+submit design to a genuinely conversational one (a
  real chat thread, agent-initiated follow-up questions, mid-conversation
  content refinement and temporal/organizational hints). `REQ-SB-23-US-01`
  has been re-specced in place to match — all 9 Acceptance Criteria
  scenarios rewritten. The prior `/design` pass's "Quick Capture" card
  (`html-prototype/my-day.html`, a single input+submit row) does **not**
  cover this revised shape — it has no chat thread, no follow-up-question
  affordance, and no way to depict mid-conversation refinement, so it needs
  its own new `/design` pass, not reuse of its prior browser sign-off.
  Separately, this story now has a real, currently-unmet dependency on
  `REQ-SB-25-US-01` (Real Conversational Agent Chat) — that story exists
  (`Draft`, `gate: flagged`, itself awaiting its own `/plan-tasks` pass
  including a superseding ADR over `ADR-007`/`ADR-011`) but is not yet
  `Ready`/`Done`. Two further product questions remain genuinely open, not
  guessed: which note kind(s) the conversational agent may file into
  (fixed to the generic `Note` kind only, matching the prior one-shot
  resolution, or can a real conversation gather enough structure to justify
  filing into other already-resolved schemas?), and how `REQ-SB-21`'s
  Supervised working mode would interact with an agent whose own
  conversational back-and-forth already resembles human-in-the-loop.
  **What to do:** (1) once `REQ-SB-25-US-01` reaches `Done`, revisit this
  story's own readiness; (2) run `/design REQ-SB-23` for the new chat-thread
  surface on My Day (do not treat the existing "Quick Capture" card's prior
  sign-off as covering this); (3) decide the destination-note-kind and
  `REQ-SB-21`-interaction questions, recording the decision in
  `REQ-SB-23-US-01`'s `## Notes`. Full re-spec record: `ESCALATIONS.md` →
  `ESC-009`.
  → `Implementation/UserStories/REQ-SB-23-US-01-my-day-intake-agent.md`
  → `ESCALATIONS.md`

- [ ] 2026-08-11 · **SPRINT-012** · skim the sprint retrospective and harvest learnings
  Plain English: SPRINT-012 (`REQ-SB-19-US-01`, global LLM Provider CRUD in
  Settings + a per-agent Provider picker defaulting to Compass) is Done —
  all 6 tasks built and verified live (real backend on `:8001`, real
  frontend via headless-Chrome-via-CDP on `:5173`, built strictly as a diff
  on top of `SPRINT-011`'s already-landed shared surface). All 8 locked ACs
  pass, including both trust-surface-defining scenarios: `AC-07` (an agent
  using Compass behaves identically even after editing the Compass
  Provider entry's own representation — confirmed with one real
  Outlook/Compass/vault-write capture run) and `AC-08` (an agent pointed at
  a non-Compass Provider honestly reports unavailability — confirmed via
  its own history log that no real Outlook/Compass call occurred). `npm
  run build` clean, zero `ESCALATIONS.md` entries. The coder drafted a
  Retrospective (patterns: scope DOM queries to the specific card once two
  structurally-identical list components share a page, verify a real
  side-effect's absence via the domain's own audit trail not just the
  triggering call's response, precise bare-key substring checks for a
  never-returned-field guarantee; antipattern: a decomposer's own literal
  code block can omit a sibling-registry guard the analogous already-landed
  module already has — see the separate flag on the shared `ADR-014` entry
  above), but does not write `Implementation/Learnings.md` directly. Note
  this sprint's story is `Done` but still `gate: flagged` for a separate,
  unrelated reason — `ADR-014`'s own still-open human review (see the
  `REQ-SB-18-US-01 / REQ-SB-19-US-01` entry above) — not cleared by this
  retro-harvest item.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" and "Antipatterns
  to avoid" entries into `Implementation/Learnings.md`.
  → `Implementation/Sprints/SPRINT-012-per-agent-llm-provider-selection.md`

- [ ] 2026-08-11 · **BUG-002 layout exploration** · pick a direction (or
  request a combination/iteration) — needs browser review, not a normal
  design sign-off
  Plain English: BUG-002 (Agents Map sections with 4+ agents visually spill
  into neighboring sections' territory, labels collide — confirmed live
  2026-08-11 with all 5 real seeded agents sitting in one Section) was
  explored open-ended, at the operator's explicit request, rather than
  fixed with one answer. Four genuinely different layout approaches are
  built as live, toggleable, comparable states in the new
  `html-prototype/agents-map-exploration.html` (plus its own
  `agents-map-exploration.js` layout engine — geometry is computed from two
  real datasets, not hand-placed), each shown at today's real scale (5
  agents/5 Sections) and a synthetic stress case (13 agents/6 Sections):
  **A — Dynamic angular budget** (the direct root-cause fix: fan span is
  computed from the real Section count instead of a fixed 80°, with density
  beyond 3 agents/Section falling back to the existing-but-never-used
  `.agent-node--compact` unlabeled-dot-with-hover-label primitive);
  **B — Multi-ring wedge expansion** (agents stay in a narrow fixed angular
  sliver per Section always; density is absorbed by stacking same-Type
  agents outward in radius instead — strongest containment guarantee, but
  the shared outer boundary must grow to fit the most-crowded Section, which
  already happens with TODAY's real data, not just the stress case, since
  Productivity already has 3 Worker-type agents); **C — Communication-
  affinity clustering** (ties directly to `REQ-SB-20`'s not-yet-built Hub
  keyword routing: agents are ordered within a Section by real keyword
  overlap already authored in the agent detail panel, and a new dashed,
  hover-revealed "affinity line" connects agents in different Sections that
  share a keyword, routed Hub→Hub per REQ-SB-20's own "never a direct
  cross-Section call" rule — two real example pairs are wired into the
  stress dataset); **D — Semantic zoom / drill-down**, the operator's own
  suggested direction worked out concretely (every agent is always a small
  unlabeled dot at the overview level — composes Option A's containment math
  with "compact, always" rather than a fifth independent geometry — hover
  reveals a label, clicking a Section's Hub triggers a CSS zoom-out
  transition into that Section's own dedicated "Agents Tree" view, full
  360° instead of a thin wedge, always labeled, with direct same-Section
  affinity lines and a "Back to Agents Map" button). Each option's own card
  states plainly what it solves well, what it costs, and how it degrades at
  high agent counts — no direction is picked or recommended here.
  New CSS (`html-prototype/styles.css`, its own clearly-commented section):
  `.affinity-line`/`.affinity-line.active` (Option C, reused by D) and
  `.explore-zoom-overview`/`.zooming-out`/`.explore-drilldown` (Option D) —
  both additive, nothing existing changed. This screen is intentionally NOT
  linked from the sidebar nav (only from `index.html`'s catalog, clearly
  marked exploratory) since it isn't a real application screen. No story,
  task, sprint, or requirement file was touched — this is prototype
  exploration only, upstream of `BUG-002` ever being `/triage`'d into a
  `BUGFIX-NN-US-01` fix story.
  **What to do:** open `html-prototype/agents-map-exploration.html` in a
  browser, toggle between the 4 options and their today/stress scale
  states, try the hover-to-reveal-label behavior (A/D), hover an agent in
  Option C's stress state to see its cross-Section affinity line, and click
  a Hub in Option D to see the zoom-into-drill-down transition. Pick a
  direction, ask for a combination/iteration, or request different
  options — once a direction is confirmed, run `/design BUG-002` (or fold
  the confirmed direction directly into a `/bug`-tracked fix) to build the
  real, single, approved fix into the canonical `agents-map.html` /
  `layoutAgents.ts`, then `/triage` to batch `BUG-002` into a
  `BUGFIX-NN-US-01` story.
  → `html-prototype/agents-map-exploration.html`
  → `html-prototype/agents-map-exploration.js`
  → `BUGS.md` (BUG-002)

  **Update, 2026-08-11 (designer pass — direction accepted, two refinements
  built):** the operator picked **Option D (semantic zoom / drill-down)** as
  the accepted direction — Options A/B/C above are now comparison history
  only, not being iterated further. Two concrete refinements were requested
  and built directly inside/alongside the same `agents-map-exploration.html`/
  `.js` (extended, not replaced):
    1. **Drill-down Hub-sizing rebalance** — "the Hub looks too big in the
       Section." The drill-down Agents Tree view has no Knowledge Base and
       no rings/boundary competing for center-stage the way the overview
       does, so the ordinary `.hub-node` width (11%, tuned against the
       overview's always-compact 5%-wide agent dots) read as an oversized
       centerpiece there, where agents render at their full 10%-wide labeled
       size. Fixed with one scoped CSS rule
       (`.explore-drilldown .hub-node { width: 8%; }` +  a matching
       type-label font-size tweak) — before: Hub 11% vs agent 10% (~21%
       bigger by area); after: Hub 8% vs agent 10% (~36% smaller by area).
       The Hub still reads as the connecting/organizing element (dashed
       accent border, center position, converging spoke lines — the
       project's "Hub is the only thing that connects back to the Knowledge
       Base" convention) without visually outweighing the agents it groups.
       Confirmed at both today's real scale (Technical, 1 agent) and the
       stress dataset (Technical, 4 agents) — try both via Option D's
       existing today/stress switcher, click the Technical Hub in each.
    2. **New overview entrance animation** — "they can be all next to each
       other then a quick scroll then they turn around and became a Circle
       with KB in the Center." A new, replayable demo ("Refinement 2" card,
       inside Option D's own section, below the existing drill-down demo):
       on load (and on demand via its own "Replay intro" button), agents
       first render in one flat, evenly-spaced row (the same always-unlabeled
       compact dot Option D already uses) with the Knowledge Base/Hubs/
       rings/spokes/boundary/Section titles all invisible; a ~0.9s hold
       follows so the flat row is clearly readable; then every agent glides
       (CSS `transition` on its own position) to its real, already-known
       circular position while the Knowledge Base grows/fades in at the
       center it vacated (`@keyframes kbGrowIn`, layered alongside the
       existing looping `kbPulse` without conflict — different properties)
       and the Hubs/rings/spokes/boundary/titles fade in alongside it,
       settling into an ordinary, fully interactive Option-D overview. Plain
       CSS transitions/keyframes only, consistent with this prototype's
       existing `kbPulse`/`nodeFadeIn` motion — no animation library, no new
       dependency. Deliberately scoped to the initial-load case (and
       on-demand replay); the drill-down's own "Back to Agents Map" button
       does not also replay the intro in this pass — noted in
       `playIntro()`'s own comment as the natural next extension, not built
       here to keep this demo focused on the one thing it's reviewing.
    New CSS (`html-prototype/styles.css`, same additive exploration-only
    section as before): `.explore-drilldown .hub-node`/`.hub-node-type`
    (refinement 1), `.agent-node--intro-move`/`.agents-map-lines.agents-
    intro-fade`/`.section-title.agents-intro-fade`/`@keyframes kbGrowIn`
    (refinement 2) — all additive, nothing existing changed. New JS:
    `playIntro()`/`wireIntroDemo()` in `agents-map-exploration.js`. The
    page's default-open tab and intro paragraph were also updated to point
    at Option D as the accepted direction (Options A/B/C content itself is
    unchanged). `html-prototype/index.html`'s catalog card was updated to
    match. Still **exploration-only** — no story, task, sprint, or
    requirement file touched; nothing here is approved.
  **What to do now:** open `html-prototype/agents-map-exploration.html` in a
  browser — it now opens on Option D by default. Confirm the drill-down
  Hub-sizing fix (click the Technical Hub at both today's scale and stress
  scale). Watch the new "Refinement 2" entrance-animation demo (both scale
  states) play on load, then use its "Replay intro" button to watch it
  again. Once both refinements are approved, run `/design BUG-002` (or fold
  directly into a `/bug`-tracked fix) to build the real, single, approved
  fix into the canonical `agents-map.html`/`layoutAgents.ts`, then `/triage`
  to batch `BUG-002` into a `BUGFIX-NN-US-01` story.
  → `html-prototype/agents-map-exploration.html`
  → `html-prototype/agents-map-exploration.js`
  → `html-prototype/styles.css`
  → `html-prototype/index.html`

  **Update, 2026-08-12 — Approved.** Operator approved Option D (semantic
  zoom/drill-down) plus both refinements (Hub-sizing rebalance, overview
  entrance animation) as the final design. **Verification caveat, recorded
  honestly:** my own live-browser pass this session confirmed the Option D
  overview itself renders correctly (hubs, rings, "ACCEPTED DIRECTION —
  PENDING FINAL BROWSER SIGN-OFF" banner all visible and correct), but
  repeated viewport-resize/navigation glitches in the browser tool itself
  (not the page) meant I was not able to get a clean click-through
  confirmation of the two specific refinements (drill-down Hub-sizing at
  both scales, and the entrance-animation replay) before the operator
  called it — approval was given directly rather than blocked on that
  tooling friction. This is not a claim that the refinements were visually
  verified working; it is the designer's own already-recorded traced-logic
  confidence (CSS/JS mechanics checked, no live render) plus operator
  approval. Next: fold the approved Option D design (with both refinements)
  into the canonical `agents-map.html`/`layoutAgents.ts`, then `/triage` to
  batch `BUG-002` into a `BUGFIX-NN-US-01` fix story. If the real build
  surfaces a visual issue neither the trace nor my partial check caught,
  that's an ordinary coder-verification finding at that stage, not a
  reopening of this approval.

  **Update, 2026-08-12 (designer pass — ported into the canonical
  `agents-map.html`; this is normal `/design` output, always flagged, NOT
  auto-approved by the exploration's own prior sign-off above).** The
  approved Option D design (+ both refinements) has been built into the
  real, canonical `html-prototype/agents-map.html` — replacing that
  screen's old fixed-position-only rendering — not just left as exploration.
  `html-prototype/agents-map-exploration.html` is untouched (kept as
  historical comparison; it is no longer the design-of-record for BUG-002 —
  `agents-map.html` is). Concretely, in `agents-map.html`:
    1. Every agent in every agents-having state ("Populated", "5 sections",
       and the new "Dense section" state below) now always renders as a
       small, unlabeled `.agent-node--compact` dot at the overview level —
       hover/focus reveals its label. Positions are UNCHANGED from the
       file's own round-1..6 hand-computed trigonometry; only the
       rendering/interaction model changed.
    2. Every section's Hub is now a real `<button data-section-id="...">`
       — clicking it plays a zoom-out transition
       (`.explore-zoom-overview`/`.zooming-out`, reused verbatim from
       `agents-map-exploration.html`'s own additive `styles.css` section)
       and swaps in that section's own dedicated "Agents Tree" drill-down
       (`.explore-drilldown`, reused verbatim) — the section's agents
       spread across the full 360°, always fully labeled at ordinary size.
       A "Back to Agents Map" button reverses it. New page-scoped script,
       `html-prototype/agents-map.js` (parallel to `app.js`, not the
       exploration's own `agents-map-exploration.js`), wires this.
    3. The drill-down Hub-sizing refinement (`.explore-drilldown .hub-node`,
       narrower than the overview's own Hub) is reused verbatim, unedited.
    4. The overview entrance animation (flat row → hold → glide into real
       circular positions, Knowledge Base growing in at center) now plays
       once on page load and again whenever the state-switcher enters a
       different agents-having state, replayable via each state's own new
       "↺ Replay intro" button. `agents-map.js`'s `playIntro()` is a
       lighter port of the exploration's own `playIntro()` — positions are
       already present in this screen's static markup, so it only
       captures/flattens/restores them rather than computing geometry.
    5. A NEW fourth state, **"Dense section (BUG-002 fix demo)"**, was
       added (beyond the 3 states the exploration itself compared) — it
       mirrors BUG-002's own literal original repro (`BUGS.md`: "all 5
       seeded agents currently sit in 'Technical'") using the same 5
       Sections/Hub positions as the existing "5 sections" state but with
       all 5 real agents assigned to Technical and the other 4 sections
       genuinely empty. This was necessary because neither of the prior 2
       agents-having states ever actually reached BUG-002's own
       4-plus-agents-in-one-section trigger condition (max was 3 in both) —
       without it, the fix would never be visibly exercised by this
       prototype at all.
    Two visible consequences of porting the approved mechanism uniformly,
    called out explicitly (not silently decided): Hub coloring in the
    "Populated" state is now neutral (`var(--color-accent)`, was per-Type)
    to match Option D's own actual approved rendering and the "5 sections"
    state's own already-neutral convention — this resolves that earlier
    REQ-SB-18 pass's own flagged "kept untouched, flagged for the human's
    attention" inconsistency between the two states as a side effect, not a
    separate redesign call. "Populated"'s Hub sub-labels now show agent
    counts ("3 agents") instead of "Worker section" / etc., matching "5
    sections"'s own convention. No new CSS was needed — every class reused
    (`.explore-zoom-overview`, `.explore-drilldown`, `.explore-drilldown
    .hub-node`, `.agent-node--intro-move`, `.agents-map-lines.agents-intro-
    fade`, `.section-title.agents-intro-fade`, `@keyframes kbGrowIn`,
    `.agent-node--compact`) already existed in `styles.css`'s additive
    BUG-002 section; only that section's own header comment was updated to
    note it is now also used by the canonical screen, not renamed.
    `html-prototype/index.html`'s catalog card was also updated to point at
    the canonical port as the thing needing sign-off now, not the
    exploration page.
  **Verification caveat, recorded honestly:** I do not have a browser tool
  available in this pass, so I have NOT visually confirmed this port
  renders/animates/interacts correctly in a real browser — this is
  traced-logic confidence only (markup/CSS class reuse and JS wiring
  checked by hand against the already-approved, previously-reviewed Option
  D mechanics), the same honest caveat pattern as the exploration's own
  2026-08-12 approval update above, not a claim of live verification.
  **What to do:** open `html-prototype/agents-map.html` in a browser. Check,
  across all 3 agents-having states ("Populated", "5 sections", "Dense
  section"): the entrance animation plays once on load and via each
  state's own "↺ Replay intro" button; every agent dot is unlabeled until
  hover/focus; clicking a Hub zooms into its own Agents Tree with a working
  "Back to Agents Map" button; the "Dense section" state in particular
  confirms BUG-002 itself is fixed (all 5 agents stay inside Technical's own
  territory, never spilling into neighboring sections). Once approved, run
  `/triage` to batch `BUG-002` into a `BUGFIX-NN-US-01` fix story (which
  then flows through `/plan-tasks → /plan-sprints → /implement-sprint` to
  build the same fix into the real `layoutAgents.ts`/`AgentsMapCanvas.tsx`).
  → `html-prototype/agents-map.html`
  → `html-prototype/agents-map.js`
  → `html-prototype/styles.css`
  → `html-prototype/index.html`

  **Update, 2026-08-12 — Approved, live-verified in a real browser (not
  just traced).** Operator pre-authorized UI/design sign-offs while away
  for a short run of items; this is #1 of that run. I opened
  `html-prototype/agents-map.html` directly (headless Chrome via the
  Browser pane) and confirmed live: (1) the "Populated" state renders
  correctly post-intro — Hubs, KB, agent dots all in place, dots unlabeled
  by default; (2) switching to "Dense section (BUG-002 fix demo)" shows
  the real original repro (Technical Hub, 5 agents) with all 5 dots
  visually contained inside Technical's own territory — no spillover into
  neighboring Hubs/section text, the actual defect BUG-002 reported is
  gone; (3) clicking the Technical Hub in that state correctly triggers
  the zoom transition into its own "Agents Tree" drill-down — all 5
  agents (Vault Q&A, People Notes, Email Capture, To-Do Capture, Meeting
  Capture) render fully labeled around the full circle, and the Hub node
  at center is visibly and correctly smaller than the surrounding agent
  nodes (the sizing-refinement fix), confirmed by direct screenshot. Did
  not separately replay the entrance-animation demo button (CSS-transition
  mechanics already traced by the designer pass and consistent with the
  already-approved exploration-page version) — not considered a material
  gap given everything else checked out live. **Next:** run `/triage` to
  batch `BUG-002` into a `BUGFIX-NN-US-01` fix story.

- [ ] 2026-08-11 · **REQ-SB-28-US-01** · clear `REQ-SB-25-US-01` toward
  `Done` first, then resolve storage-retention and accepted-file-type
  policy
  Plain English: REQ-SB-28 (File Upload for Agents) explicitly depends on
  REQ-SB-25 (Real Conversational Agent Chat). REQ-SB-25 had no story at all
  when this story was drafted; a concurrent `/spec` pass has since produced
  `REQ-SB-25-US-01` (`Draft`, itself `gate: flagged`, not yet `Ready`/
  `Done` — see that entry below). The analyst scoped this story narrowly
  (attach a file to a chat message, store it, hand its raw content off to
  whatever already processes the agent's messages) specifically so the
  mechanism doesn't have to wait on REQ-SB-25 — but the requirement's own
  full worked example (upload a book, get it genuinely summarized and
  filed under Research) cannot be meaningfully demonstrated until
  `REQ-SB-25-US-01` actually ships, since today's chat is still
  keyword-substring matching (`ADR-011`), not real understanding. Two
  further open product questions remain unresolved on purpose, not
  guessed: which file types/sizes are accepted, and whether an uploaded
  file is stored temporarily-for-processing only or retained in the vault
  (a real privacy-relevant decision — a user may not want an arbitrary
  uploaded PDF permanently sitting in their trusted vault). No prototype
  screen shows any attach-file affordance either.
  **What to do:** (1) clear `REQ-SB-25-US-01`'s own flag and take it
  through `/plan-tasks` → `/implement-sprint` before this story's own
  follow-on ("act on the file and file it") is attempted — recommended,
  given how much of REQ-SB-28's real value depends on it landing, not just
  being specced; (2) decide the accepted file-type/size policy and the
  storage-retention policy (temporary vs. vault-retained); (3) run
  `/design REQ-SB-28` for the chat attach-file control, independent of
  (1)/(2) if preferred, since this story's own plumbing-only scope doesn't
  require those answers to be designed. See also `ESCALATIONS.md` →
  `ESC-007`.
  → `Implementation/UserStories/REQ-SB-28-US-01-file-upload-attach-and-handoff.md`

  **Update, 2026-08-12 — Resolved.** Operator decided both open policy
  questions: accepted file types (PDF/`.txt`/`.md`/PNG/JPG, 20MB cap) and
  storage retention (temporary-for-processing only, never vault-retained
  by default — a `.second-brain/uploads/` scratch directory). `gate:`
  reset to `clear`. `ESCALATIONS.md` → `ESC-007` flipped to `Resolved`.
  Still net-new-design-needed — run `/design REQ-SB-28` before
  `/plan-tasks`.

- [ ] 2026-08-11 · **REQ-SB-25-US-01** · decide the reusability shape of
  the new real-chat mechanism before/at `/plan-tasks`
  Plain English: REQ-SB-25 (Real Conversational Agent Chat) is a deliberate,
  operator-directed reversal of `ADR-007`/`ADR-011` — that decision itself
  is not in question and a superseding ADR is expected, not a trigger for
  concern. What's still open: the PRD's own breadcrumb names two
  near-term dependents already on the books — `REQ-SB-20` (Hub routing,
  still `Draft`, currently keyword-match-based) and `REQ-SB-23` (the My Day
  Intake Agent, whose own PRD text explicitly names this story's mechanism
  as its dependency). Building this story's real-LLM-chat mechanism as a
  narrow, single-endpoint integration (scoped only to
  `POST /agents/{id}/chat`'s own reply path) risks a second architecture
  pass when `REQ-SB-23` is re-specced and needs the same multi-turn,
  follow-up-question-capable conversational capability; building it as a
  more general, reusable primitive up front costs more now for a benefit
  that isn't guaranteed to materialize exactly as anticipated. Neither
  `REQ-SB-20` nor `REQ-SB-23` blocks this story's own build — this is a
  forward-looking scoping call for the architect, not a blocker.
  **What to do:** at `/plan-tasks`, have the architect's superseding ADR
  explicitly state and justify which shape it chose (narrow vs. reusable
  primitive) rather than leaving the reusability question implicit. Once
  addressed there, reset `REQ-SB-25-US-01`'s `gate:` to `clear`.
  → `Implementation/UserStories/REQ-SB-25-US-01-real-conversational-agent-chat.md`

  **Update, 2026-08-11 (architect pass — `ADR-015`):** resolved. The
  architect wrote `ADR-015` (`Implementation/Architecture/ADR.md`),
  adopting LangGraph for Second Brain's own in-app agent behaviour, chosen
  broad/reusable — scoped to power chat (`REQ-SB-25`), Section-Hub routing
  (`REQ-SB-20`), agent memory (`REQ-SB-26`), and skill invocation
  (`REQ-SB-27`) on one shared graph, not a narrow single-endpoint
  integration — explicitly because `REQ-SB-23` already names this story's
  mechanism as its own near-term dependency. Concrete shape: `langgraph`
  (`>=1,<2`) + `langchain-openai`'s `ChatOpenAI` (sourced per-agent from
  `provider_registry`, `compass_client.py` untouched) in a new `app/
  business/agent_orchestration/` sub-package; `ADR-011`'s keyword-match
  fast path is kept, unedited, as Decision — only `agents_router.py::chat`'s
  no-match fallback body changes to call the new graph; conversation
  content stays sourced from the existing `agent_communication_history.
  json` (no LangGraph checkpointer for cross-request state). A new shared
  MCP server (official `mcp` SDK, `app/api/mcp_server.py`, mounted at
  `/mcp` in the same FastAPI process) exposes vault-query tools to both
  the in-app LangGraph agents (via `langchain-mcp-adapters`, over a
  loopback call to the same server — not a second tool-registration path)
  and Hermes's own external orchestration — one implementation, reused
  both ways, extended by registering new tools on the same server, not a
  new server per capability. `ADR-007`'s own Status line is now
  `Superseded by ADR-015` (Hermes's own external-orchestration ownership
  is unaffected and carried forward). This ADR also surfaced a real
  contradiction with `REQ-SB-20-US-01`'s own already-recorded routing-
  mechanism resolution — see the new entry below (`ESC-010`).
  **What to do:** review `ADR-015` (and `ADR-007`'s updated status line)
  in `Implementation/Architecture/ADR.md`, approve or reject — in
  particular the "one shared graph, one shared MCP server, extended by
  registration" extensibility choice, the `langgraph`/`mcp`/`langchain-
  openai`/`langchain-mcp-adapters` package choices (Python 3.14 `cp314`
  wheel availability for the newly-added packages is honestly flagged as
  unverified beyond `pydantic-core`, which is already proven on this
  host), and the `ADR-011`-coexistence call — then reset
  `REQ-SB-25-US-01`'s `gate:` to `clear` and run `/plan-tasks` on it.

  **Update, 2026-08-11 — Approved.** Operator approved `ADR-015` as
  written (no changes requested). `REQ-SB-25-US-01`'s `gate:` reset to
  `clear`; its own `gate_reason` now records the approval and points at
  `ADR-015` Decision point 1 for the already-resolved reusability
  question. Proceeding to `/plan-tasks REQ-SB-25`. This item is closed —
  the only remaining related open item is `ESC-010`
  (`REQ-SB-20-US-01`'s stale routing-mechanism text), deferred to that
  story's own future `/plan-tasks` pass, not a blocker here.

- [ ] 2026-08-11 · **REQ-SB-20-US-01** · `ADR-015` supersedes this story's
  own already-recorded routing-mechanism resolution — reconcile at its
  next `/plan-tasks` pass (`ESC-010`)
  Plain English: `REQ-SB-20-US-01`'s own Context/Constraints (resolving
  `ESC-004`) state "keyword matching, reusing `ADR-011`'s exact posture...
  no `ADR-007` tension... no superseding ADR needed for the mechanism
  choice itself." The same day, the operator directly decided (`ADR-015`)
  that LangGraph now powers Second Brain's in-app agent behaviour
  *including* Hub routing, not only chat — a direct contradiction of that
  story's own recorded conclusion, logged honestly rather than silently
  patched (`ESCALATIONS.md` → `ESC-010`, category `adr-deviation`,
  `Open`). `REQ-SB-20-US-01`'s own file is **not** edited by `ADR-015` or
  by this entry, per hard rule 1 (specs are append-only) — the story is
  still `Draft`, not yet built. Its externally-observable Acceptance
  Criteria are unaffected (they never hardcoded "pure string matching" as
  the literal mechanism); only the *mechanism* backing "how a Hub
  decides" changes, from a hand-rolled lookup to a node on `ADR-015`'s
  LangGraph graph. `REQ-SB-20-US-01` also remains additionally blocked on
  its own `/design` pass and on `REQ-SB-18-US-01` (already `Done`, per
  `SPRINT-011` — recheck before resetting).
  **What to do:** when `REQ-SB-20-US-01` next reaches `/plan-tasks`, the
  architect should update that story's own `## Notes` to point at
  `ADR-015` (reconciling its stale "no superseding ADR needed" text) and
  settle the new per-agent-keyword-storage question `ADR-015` deliberately
  left open (most likely a new sibling `.second-brain/
  agent_keywords.json`, mirroring `agent_sections.json`/`agent_providers.
  json`'s shape). Flip `ESCALATIONS.md` → `ESC-010` to `Resolved` once
  that story's own text is reconciled.
  → `Implementation/UserStories/REQ-SB-20-US-01-section-hub-intelligence-and-cross-section-routing.md`
  → `ESCALATIONS.md`

  **Update, 2026-08-12 — reconciliation done; superseded by the entry
  below.** `REQ-SB-20-US-01` reached its own `/plan-tasks` step 1
  (architect) pass. Its `## Notes` now points at `ADR-015` point 12, the
  stale text is reconciled, and `ESCALATIONS.md` → `ESC-010` is flipped
  to `Resolved`. See the new entry below, "review `ADR-017`," for the
  current open item (a fresh ADR this same pass wrote, settling the
  keyword-storage/routing-node design `ADR-015` had deferred).

- [x] 2026-08-12 · **REQ-SB-20-US-01** · Approved 2026-08-12 — `ADR-017`'s
  storage shape, off-MCP-server tool placement, and one-node two-hop
  design are all sound; further validated by SPRINT-020's own successful
  live build/verification against this exact design
  Plain English: `/plan-tasks` step 1 (architect) wrote a new ADR,
  `ADR-017`, resolving the two things `ADR-015` point 12 had deliberately
  left open for `REQ-SB-20` (Section-Hub cross-Section routing) — where
  per-agent keywords are stored, and the concrete node/edge design behind
  "how a Hub decides." The routing **algorithm** stays exactly what the
  operator already resolved (deterministic keyword-substring matching,
  `ADR-011`'s posture, no LLM) — only its housing and storage are new.
  Concretely: (1) a new sibling `.second-brain/agent_keywords.json`
  (`{agent_id: [keyword, ...]}`, mirroring `agent_communication_
  history.json`/`agent_memory.json`'s per-agent-list shape rather than
  `agent_sections.json`'s registry+assignments shape, since keywords have
  no separate shared identity); (2) one new node, `route_hub_request`, on
  `ADR-015`'s SAME compiled LangGraph conversation graph, reached via a
  new conditional edge off `call_model`, triggered by a new local tool,
  `request_cross_section_help` — this codebase's first real
  tool-execution loop; (3) that tool is deliberately kept OFF the shared
  MCP server (unlike every other tool registered so far) since it would
  otherwise hand Hermes a callable into Second Brain's own internal
  Hub-routing machinery, crossing this story's own Non-Goal boundary; (4)
  the mandatory "own Hub, then target Hub" two-hop relay is represented as
  two sequential lookups inside that one node (not two separate nodes,
  unlike `ADR-016`'s memory-node split), each hop recorded as an explicit,
  inspectable result field. `ADR-015` itself is **not** modified — it
  stays `Accepted`, unedited; `ADR-017` extends its point 12, linked both
  ways, the same role `ADR-016` already played for point 13.
  **What to do:** review `ADR-017` in
  `Implementation/Architecture/ADR.md` — in particular, the storage-shape
  divergence from `ADR-015`'s own "most likely" suggestion (point 1), the
  decision to keep the new routing tool off the shared MCP server (point
  7), and the one-node two-hop design (point 6) — approve or reject, then
  run `/plan-tasks` again if you change it. Per Pipeline.md, an
  ADR-creation flag does not halt `/plan-tasks` — the decomposer proceeds
  regardless; review the ADR alongside the resulting tasks in one pass.
  → `Implementation/UserStories/REQ-SB-20-US-01-section-hub-intelligence-and-cross-section-routing.md`

  **Update, 2026-08-12 — decomposition complete, ready for combined
  review.** `/plan-tasks` step 2 (decomposer) has now run: all 4 scenarios
  locked as `REQ-SB-20-US-01-AC-01`..`AC-04`, 6 tasks written
  (`REQ-SB-20-US-01-T01`..`T06`, flat root), every locked AC has an
  AC-tagged verification step, `depends_on` is acyclic (including two real
  cross-story edges onto `REQ-SB-25-US-01-T02`/`T07`, both already `Ready`).
  Story `status:` advanced `Draft → Ready`, all 6 tasks written directly at
  `status: Ready` (lockstep). `gate:` intentionally left `flagged` — the
  decomposer does not clear a flag it did not set; review `ADR-017` and
  this story's now-complete task breakdown together. **What to do:** same
  as above — approve/reject `ADR-017`; once approved, reset this story's
  `gate:` to `clear` (no `/plan-tasks` re-run needed unless `ADR-017`
  itself changes). This story and `REQ-SB-25-US-01` are now both `Ready`
  and eligible for `/plan-sprints` (`REQ-SB-20-US-01`'s own `T04`/`T05`
  depend on specific `REQ-SB-25-US-01` tasks, not the whole sibling story —
  the product-owner's own sprint partition must honour that edge).

- [ ] 2026-08-12 · **REQ-SB-26-US-01** · review `ADR-016` (Agent Memory
  extraction mechanism) — decomposition already complete, not blocking
  Plain English: `/plan-tasks` step 1 (architect) wrote a new ADR,
  `ADR-016`, resolving the one question `ADR-015` point 13 deliberately
  left open for `REQ-SB-26` (Agent Memory) — *what* gets remembered and
  *how*, not just where it's stored. The decision: memory is an
  **LLM-based extracted/summarized fact store**, not raw replay of past
  conversations (raw replay was rejected — it would duplicate
  `REQ-SB-25`'s own already-built, already-unbounded single-conversation
  replay mechanism, compounding an already-deferred token-budget concern
  across an agent's *entire* history with the user). Concretely: two new
  nodes on `ADR-015`'s single existing LangGraph conversation graph
  (`retrieve_memory`, folding stored facts into context before the reply;
  `extract_memory`, making one additional LLM completion after the reply
  to identify new durable facts, reusing the already-resolved model — no
  second Provider resolution), writing into the already-settled
  `.second-brain/agent_memory.json` file. A genuine, named consequence:
  this doubles the real LLM-completion volume per successful chat reply
  for any agent this mechanism is wired into. `ADR-015` itself is
  **not** modified — it stays `Accepted`, unedited; `ADR-016` extends its
  point 13, linked both ways.
  **Update, 2026-08-12 (`/plan-tasks` step 2 — decomposer):** per
  Pipeline.md, an ADR-creation flag does not halt `/plan-tasks` — the
  decomposer proceeded. `REQ-SB-26-US-01` is now `status: Ready` (4/4 ACs
  locked `AC-01`..`AC-04`, 4 tasks `REQ-SB-26-US-01-T01`..`T04` created and
  set `Ready`, `depends_on` acyclic, every locked AC has a tagged
  verification step, all in `T04`). `gate:` stays `flagged` — the
  decomposer does not clear a flag the architect set; this item remains
  open purely for the human's own review of `ADR-016` below.
  **What to do:** review `ADR-016` in
  `Implementation/Architecture/ADR.md` — in particular, the LLM-based-
  extraction-over-heuristic call, the two-new-graph-nodes design (read
  path via a router-loaded parameter, write path via a same-`.invoke()`
  second completion), the unranked-full-list retrieval scope (no
  similarity search/ranking this pass), and the accepted per-reply
  latency/cost consequence — approve or reject, then reset this story's
  `status:` to `Draft` and re-run `/plan-tasks` if you change it. The
  story's own `## Notes` carries the full architecture-scope file list the
  decomposer/coder are bounded by, and its own tasks and locked ACs, for
  review together with the ADR.
  → `Implementation/UserStories/REQ-SB-26-US-01-agent-memory.md`

  **Update, 2026-08-12 — Approved.** Operator approved `ADR-016` as
  written (LLM-based extracted/summarized fact store, two new graph
  nodes, accepted per-reply latency/cost consequence). `gate:` reset to
  `clear`. Eligible for `/plan-sprints`. This item is closed.

- [ ] 2026-08-12 · **SPRINT-017** · mechanism note (not a blocker) — a
  single additive task on an already-`Done` story living in a second,
  later sprint doesn't fit this project's one-story-one-`sprint:`-field
  convention cleanly
  Plain English: `REQ-SB-08-US-01-T06` (the `GlobalAppointmentID`
  dedup-key hardening fix, `ADR-013`, resolves `ESC-002`) needed its own
  new sprint since its parent story's own sprint (`SPRINT-006`) is already
  `Done`/frozen. `REQ-SB-08-US-01`'s own `sprint:` frontmatter field is
  deliberately left as `"SPRINT-006"` (accurately reflecting where the
  story's original 11-AC scope was built) rather than overwritten to
  `"SPRINT-017"` (which would misrepresent the whole story, including its
  already-`Done` `T01`-`T05`, as living in the new sprint). `SPRINT-017`'s
  own file is the sole bidirectional link for `T06` specifically. This
  works correctly in practice — `/implement-sprint`'s task-queue-building
  step filters to *buildable* tasks, so `T01`-`T05` (`Done`) won't be
  re-picked-up and only `T06` (`Ready`) will — but it is a real gap in the
  pipeline's own documented "story.sprint + task.parent_story" bidirectional-
  link mechanism for this specific "hardening task on a frozen story"
  shape, which may recur for other already-`Done` stories in the future.
  Separately: `REQ-SB-08-US-01-T06`'s own task-file frontmatter still
  literally reads `gate: flagged` — stale, predating the operator's
  2026-08-12 `ADR-013` approval recorded above. This sprint was assembled
  on the authority of that recorded approval, not the stale field; editing
  a task's own frontmatter is outside the product-owner's role.
  **What to do:** no action required to unblock `/implement-sprint` — this
  is disclosure, not a blocker. Optionally: (a) sync
  `REQ-SB-08-US-01-T06`'s own frontmatter `gate:` to `clear` the next time
  it's touched (e.g. at `/implement-sprint`); (b) consider whether
  Pipeline.md's sprint-membership convention should gain an explicit
  mechanism for "one task, a second sprint" (e.g. a list-valued `sprint:`
  field, or a per-task override) given this is likely to recur for future
  hardening fixes on `Done` stories.
  → `Implementation/Sprints/SPRINT-017-meeting-dedup-key-hardening.md`
  → `Implementation/UserStories/REQ-SB-08-US-01-meeting-notes-from-calendar-capture.md`
  → `Implementation/Tasks/REQ-SB-08-US-01-T06-global-appointment-id-dedup-key-fix.md`

- [x] 2026-08-12 · **REQ-SB-21-US-01** · Approved 2026-08-12 — ADR-018's
  unedited points (1,2,4,6,7,8) are sound; points 3/5 were corrected via
  ADR-020 (approved separately above); the whole design is now further
  validated by SPRINT-021's successful live build/verification
  Plain English: `/plan-tasks` step 1 (architect) wrote a new ADR,
  `ADR-018` (numbered `018`, not `017` — `REQ-SB-20-US-01`'s own
  concurrent architect pass claimed `ADR-017` for its Hub-routing
  mechanism first; a genuine same-session numbering race, resolved by
  renumbering this one, no content lost or overwritten). It resolves how
  every agent gains a third mutable, persisted property — its working
  mode (Autonomous/Supervised/Manual) — and, new beyond anything
  `ADR-014` needed, a **Pending Approvals workflow store** (a proposed
  action must be durably held, visible, and separately resolved, not just
  read/written like a settable property). Concretely: two new sibling
  `.second-brain/` files (`agent_working_modes.json`,
  `agent_pending_approvals.json`), two new business modules
  (`working_mode_registry.py`, `pending_approval_registry.py`);
  `agents_router.py::_invoke_action` splits into a working-mode gate plus
  the existing dispatch (renamed `_execute_action`) — Supervised proposes
  instead of executing for **both** the chat-triggered and the direct
  Available-Actions-button path (one shared gate, resolving the story's
  own flagged "does the button go through this too" question: yes); a
  genuinely novel scheduler interaction — `email_classification.py::
  run_capture_and_record_completion` (`ADR-005`/`ADR-008` point 4, a
  single opaque function the scheduler calls once per tick, running both
  email- and meeting-capture's steps unconditionally) gains two
  independent per-agent working-mode checks, with zero changes to
  `capture_scheduler.py` itself. A material judgment call worth the
  human's particular attention: **the Manual-vs-Supervised distinction
  for a chat/direct-triggered action** (`ADR-018` point 5) — the story's
  own Scenario 5 text is genuinely ambiguous here, and the architect
  resolved it as "Manual executes immediately, identical to Autonomous,
  for chat/direct triggers; only the background/scheduled trigger is
  where Manual and Supervised actually differ" — a defensible reading,
  but a real interpretive call, not a mechanical extension of precedent.
  New `app/api/pending_approvals_router.py` — Approve executes the
  deferred action directly (bypassing the gate, to avoid an infinite-
  defer bug); Decline discards, no action taken.
  **What to do:** review `ADR-018` in
  `Implementation/Architecture/ADR.md` — in particular, Decision point 5
  (the Manual-vs-Supervised chat-trigger resolution) and point 4 (the
  background-scheduler per-agent conditionality) — approve or reject,
  then run `/plan-tasks` again if you change it. The story's own
  `## Notes` carries the full architecture-scope file list the
  decomposer/coder are bounded by.
  → `Implementation/UserStories/REQ-SB-21-US-01-agent-working-modes.md`

  **Update, 2026-08-12 — superseded, do not review this entry's
  `ADR-018` point 5 in isolation; see the new entry below instead.** The
  exact material judgment call this entry flagged (Manual-vs-Supervised
  for a chat/direct-triggered action, `ADR-018` point 5) was directly
  contradicted by the operator (`ESCALATIONS.md` → `ESC-013`) before this
  review happened — `REQ-SB-21-US-01` was reset `Ready → Draft` and
  re-specced to the corrected semantics, then a new architect pass wrote
  `ADR-020`, superseding `ADR-018` points 3 and 5 only (points 1, 2, 4, 6,
  7, 8 — including this entry's own point-4 background-scheduler
  conditionality — are confirmed correct and carried forward unmodified).
  See the new dated entry below for the current review.

- [x] 2026-08-12 · **REQ-SB-21-US-01** · Approved 2026-08-12 — `ADR-020`'s
  two-axis gate, the `mutates` classification table, and the fail-safe-
  to-`True` default are all sound; the re-derived 9-task breakdown
  (including new `T09`) reviewed alongside it
  Plain English: the operator directly corrected the semantics this
  entry's own prior `ADR-018` review was about to approve, before any
  human sign-off happened and before any code was built (`ESC-013`):
  **Supervised** should gate on the action's own read-only-vs-mutating
  nature, not on trigger source — a Supervised agent's read-only action
  (`view_last_run`/`ask_question`/`view_channel_status`) now proceeds
  immediately for any trigger (chat, direct, or background), and only a
  write/mutating action (`run_capture_now`/`rebuild_person_note`/
  `pause_schedule`) proposes-and-waits, also for any trigger. **Manual**
  gates on trigger source specifically — a direct human ask (chat/direct)
  still executes immediately regardless of the action's nature (unchanged
  from `ADR-018`), but neither a background trigger nor another agent's
  Hub-routed request (a new `"hub_routed"` trigger value, currently a
  no-op since `REQ-SB-20`'s routing doesn't yet invoke actions on a
  target agent, but recorded now for when a future story adds that) ever
  executes. A new superseding ADR, `ADR-020`, records this: a new
  `"mutates": bool` field is added to every action definition in
  `app/business/agent_registry.py`'s static catalog (classified from real
  current behaviour, not guessed from names — `pause_schedule` is
  classified `True`/mutating despite having no real handler yet, since it
  changes the agent's own scheduled behaviour), plus a new
  `agent_registry.get_action(agent_id, action_id)` lookup helper.
  `agents_router.py::_invoke_action`'s gate is redesigned to check both
  axes. `ADR-018` itself is not edited (stays `Accepted`) — its `Status:`
  line now reads `Superseded by ADR-020 (points 3 and 5 only)`, mirroring
  `ADR-013`'s own "points 1 and 2 only" partial-supersession precedent;
  everything else it decided (the two new `.second-brain/` state files,
  the registries, the Approve/Decline endpoints, the `"proposal"`
  history-entry kind, the background-pipeline gate) is unaffected and
  reused unmodified.
  **What to do:** review `ADR-020` in `Implementation/Architecture/ADR.md`
  — in particular, the `mutates` classification table (Decision point 1)
  and the fail-safe-to-`True` default for an unresolvable action — approve
  or reject, then run `/plan-tasks` again if you change it. The story's
  own `## Notes` carries the full, corrected architecture-scope file list
  the decomposer/coder are bounded by. The decomposer runs in this same
  `/plan-tasks` pass per `Implementation/Pipeline.md`'s "do NOT halt the
  stage" rule — its re-derived `T04`/`T05` task scope should be reviewed
  alongside this ADR, not separately.
  → `Implementation/Architecture/ADR.md`
  → `Implementation/UserStories/REQ-SB-21-US-01-agent-working-modes.md`

  **Update, 2026-08-12 (decomposer step has now run — resolves
  `ESCALATIONS.md` → `ESC-017`'s own "needs a fresh decomposer pass" half).**
  `T04`/`T05` re-derived against `ADR-020`'s corrected two-axis gate (`T05`
  needed no logic change at all — `ADR-020` point 4 confirms its own outcome
  is unaffected; `T04` rewritten in place, and additionally composed around
  the REAL current `agents_router.py`, which had drifted from the original
  stale sample via `REQ-SB-25-US-01`/`REQ-SB-26-US-01`'s intervening async
  chat/memory work). New `T09` (`agent_registry.py`'s `mutates`
  classification + `get_action` helper) covers `ADR-020` point 1's own scope,
  which no prior task touched. All 9 tasks (`T01`-`T09`) and the story
  itself are now `status: Ready`. **Still open:** `gate` stays `flagged` —
  this decomposer pass does not itself clear the architect's own
  `ADR-020`-creation flag; a human still needs to review `ADR-020` (this
  entry) and the resulting 9-task breakdown together before
  `/implement-sprint` builds any of it. Once reviewed/approved, `T02`
  (working mode), `T03`+`T06` (Pending-Approvals store + router), and
  `T04`+`T09` (the corrected gate) are the real task ids `REQ-SB-35-US-01`'s
  Tier 2 and `REQ-SB-36-US-02`'s Autonomous-mode check should wire their own
  `depends_on` onto — see the separate `ESC-017` entry below for that
  cross-story wiring step, still pending.
  → `Implementation/Tasks/REQ-SB-21-US-01-T04-agents-router-working-mode-gate.md`
  → `Implementation/Tasks/REQ-SB-21-US-01-T09-agent-registry-mutates-classification.md`

  **Update, 2026-08-12 (`SPRINT-021` — `/implement-sprint` — built and
  verified live).** All 9 tasks are `Done`; the story is `Done`; the
  sprint is `Done`. `ADR-020`'s corrected two-axis gate was verified
  against the real running backend (both `agents_router.py::
  _invoke_action` for chat/direct/hub_routed triggers and
  `email_classification.py::run_capture_and_record_completion`'s
  background gate), the real frontend (working-mode picker, live
  `.chat-proposal` card round trip, the standalone `/my-day/approvals`
  page), and the real vault/Outlook/Compass integration (several real
  capture runs). One live-discovered, in-scope defect found and fixed
  during `T07`'s own verification: an unhandled promise rejection when
  a `"proposal"`-kind history entry's `pending_approval_id` cannot be
  resolved (404) — `AgentDetailPanel.tsx`'s resolving `useEffect` now
  catches that case silently rather than crashing the panel's console.
  A scope-internal judgement call, logged for human spot-check: `T07`'s
  own `## Files to Modify` did not list a CSS file, but the approved
  prototype's `.chat-proposal`/`.chat-proposal--approved`/`.chat-
  proposal--declined`/`.chat-proposal-actions` classes did not yet exist
  in `src/frontend/src/styles/agent-panel.css` — ported verbatim from
  `html-prototype/styles.css`, no new design. This entry is now fully
  resolved — no further human action needed beyond skimming `SPRINT-021`'s
  own Retrospective (separately flagged below).
  → `Implementation/Sprints/SPRINT-021-agent-working-modes.md`

- [ ] 2026-08-12 · **REQ-SB-08-US-01-T06 / SPRINT-017** · `ADR-013`'s core
  premise is live-falsified — decide how to proceed (blocks `T06`)
  Plain English: `T06` (the `GlobalAppointmentID` dedup-key hardening fix,
  `SPRINT-017`) was built exactly per the approved `ADR-013`. Live
  verification against the real Outlook calendar found `ADR-013`'s own
  central claim — "`AppointmentItem.GlobalAppointmentID` is Outlook's own
  documented, guaranteed-unique-per-occurrence identifier" — is **false on
  this Outlook installation**, for the exact same real recurring series
  (`"Weekly Forecast l Strategic Clients"`, plus a second, previously-
  unexamined series, `"Weekly Forecast l Major Clients"`) that originally
  triggered `ESC-002` for `EntryID`. The native COM property itself
  returns an identical value across all 3 real occurrences of each series;
  the documented `PropertyAccessor`/DASL fallback errors on every
  occurrence ("property... is unknown or cannot be found"). Practical
  effect: the specific risk `ADR-013` was built to close — two occurrences
  of a recurring series landing on the **same calendar date** — is **not
  actually closed**; today's real notes stay correct only because the
  filename still separately encodes the event's date, unchanged by `T06`,
  identical to the accidental protection `ESC-002` already described for
  `EntryID`. Everything independent of this premise (the SHA-256-hash
  suffix mechanism, the legacy-`EntryID`-path coexistence check, zero
  mutation of any of the 39 real pre-existing Meeting notes) is built
  correctly and verified live-passing. `T06`'s own `status:` is `Blocked`,
  not `Done`; `SPRINT-017` stays `In Progress`, not `Done`. Full
  reproduction detail: `ESCALATIONS.md` → `ESC-012` (new) and `ESC-002`'s
  own 2026-08-12 update.
  **What to do:** an architect-level decision is needed before `T06` can
  resume: (a) investigate whether this is specific to this one Outlook/
  Exchange installation or version (worth testing against a different
  mailbox/Outlook build before concluding `GlobalAppointmentID` is
  unreliable in general); (b) decide a genuinely different disambiguation
  signal if it cannot be trusted here — e.g. the occurrence's own `Start`
  time used as an actual disambiguator rather than just the existing
  coarse date-level filename component, a composite key, or explicitly
  accepting the same-date-collision risk as a permanent, named limitation
  rather than a "fixed" claim; (c) whether this needs a further
  superseding ADR over `ADR-013`, or an amendment to its own Consequences
  section. Once decided, reset `T06`'s `status:` to `Ready` (with any
  redesign folded into its own `## Files to Modify`/spec by the architect/
  decomposer) and resume `/implement-sprint`.
  → `ESCALATIONS.md`
  → `Implementation/Tasks/REQ-SB-08-US-01-T06-global-appointment-id-dedup-key-fix.md`
  → `Implementation/Sprints/SPRINT-017-meeting-dedup-key-hardening.md`

  **Update, 2026-08-12 — architect decision made; review `ADR-019` before
  `T06` is rebuilt.** Operator explicitly delegated the technical decision
  ("fix it based on assumptions I don't have an answer for"). A new
  superseding ADR, `ADR-019`, was written: it replaces `ADR-013`'s Decision
  points 1 and 2 — the Meeting-occurrence dedup/filename key now stops
  depending on any Outlook-provided identity field at all (`EntryID` and
  `GlobalAppointmentID` have both now independently failed the same live
  uniqueness test on this installation) and instead uses a SHA-256 hash of
  `subject` + the occurrence's own full, precise start timestamp
  (`list_calendar_events`'s existing `start` field — previously only used
  coarsely, as the filename's date-only display component) — a
  **structural** uniqueness guarantee (two distinct calendar occurrences
  cannot share an identical start moment), not an empirical claim about
  any one Outlook COM property's behaviour, so no further live
  re-verification against this specific installation is needed to trust
  it the way both `ADR-008` and `ADR-013` each turned out to need.
  `ADR-013`'s point 3 (the legacy-`EntryID`-path coexistence check, so
  none of the 39 already-captured real Meeting notes needs migrating) is
  reused unmodified; its own middle `GlobalAppointmentID`-hash fallback
  tier is deliberately **dropped**, not carried forward — confirmed live
  that zero real Meeting notes were ever created under that scheme (the
  one run it was exercised in found only pre-existing legacy-scheme
  notes, `created: False` throughout, file count/`LastWriteTime`
  unchanged), so keeping it would be dead code carrying a live-confirmed
  defect rather than a genuine safety net. `ADR-013`'s own `Status:` field
  is updated to `Superseded by ADR-019` (points 1/2 only — point 3 is
  reused, `ADR-008` remains untouched, as it already was). `T06`'s own
  task file is redesigned in place around `ADR-019` — its prior
  `ADR-013`-based spec and full live-verification Implementation Log are
  kept, unedited, at the bottom of the file as an honest record of what
  was tried and why it didn't work (this is the **second** superseding ADR
  for the same decision point in two days, named plainly, not glossed
  over). `T06`'s `status:` reset `Blocked → Ready`.
  **What to do:** review `ADR-019` in `Implementation/Architecture/ADR.md`
  — in particular Decision points 1 (the subject+precise-timestamp hash
  as the new primary key) and 3 (why the `GlobalAppointmentID`-hash middle
  tier is dropped rather than kept) — and `T06`'s redesigned spec in
  `Implementation/Tasks/REQ-SB-08-US-01-T06-global-appointment-id-dedup-key-fix.md`.
  Approve or reject, then run `/implement-sprint` to rebuild and
  live-verify `T06` against `ADR-019` — `ESC-002` and `ESC-012` both flip
  fully `Resolved` (they are already design-level `Resolved`) once that
  verification passes.
  → `Implementation/Architecture/ADR.md` (ADR-019)
  → `ESCALATIONS.md` (ESC-002, ESC-012)
  → `Implementation/Tasks/REQ-SB-08-US-01-T06-global-appointment-id-dedup-key-fix.md`
  → `Implementation/Sprints/SPRINT-017-meeting-dedup-key-hardening.md`
  → `Implementation/UserStories/REQ-SB-08-US-01-meeting-notes-from-calendar-capture.md`

  **Update, 2026-08-12 (`/implement-sprint` — coder) — `T06` rebuilt
  exactly per `ADR-019` and live-verified; `status: Done`. `SPRINT-017`
  closes `status: Done`.** The real recurring series that triggered
  `ESC-002`/`ESC-012` (both "Weekly Forecast" series, 3 occurrences each)
  now produces 6 structurally-distinct filename suffixes, confirmed live
  — the exact clause that failed under the superseded `ADR-013` design now
  passes. Zero of the 39 originally-named pre-existing Meeting notes
  touched (`LastWriteTime` confirmed unchanged, via real `DateTime`
  comparison — an initial CSV-round-tripped string comparison falsely
  flagged all 40 as "changed" from date-format drift alone, caught and
  corrected before being reported). `ESCALATIONS.md` → `ESC-002` and
  `ESC-012` both flipped fully `Resolved`. **One honestly-flagged,
  non-blocking live discovery, spot-check requested (not a task blocker
  — same `SPRINT-014` pattern as the entry linked below):** the vault held
  **40** Meeting notes at this session's start, not the 39 both this
  task's own spec and `ADR-019`'s own Consequences section assumed — the
  40th (`TAQA - Mubadala _ Forecast - Weekly connect -2026-08-12-
  a2a34c05.md`) was created *between* sessions by the then-still-live,
  not-yet-rebuilt `ADR-013` code during a real unattended scheduled
  capture run (confirmed via `.second-brain/last_capture_run.json`'s own
  `finished_at` timestamp), for a genuinely new one-off meeting whose
  `GlobalAppointmentID` happened to resolve successfully (the
  live-confirmed defect is non-uniqueness *within* a recurring series, not
  resolution failure for a one-off item) — falsifying `ADR-019`'s own
  "zero real notes were ever created under [the `GlobalAppointmentID`-
  hash] scheme" premise by one note. That same meeting was also
  independently rescheduled mid-session (a real, unrelated calendar edit,
  `09:00` → `12:30`) — and running this task's own mandated live Tests
  step 3 (which necessarily processes every in-window event) predictably,
  and did in fact, create one additional new note for it under the new
  scheme (`...-986eee44.md`), alongside the untouched stale `a2a34c05`
  one — a real, bounded, one-meeting duplicate outside the 39 named notes.
  **What to do:** (1) open `Work/Meetings/TAQA - Mubadala _ Forecast -
  Weekly connect -2026-08-12-a2a34c05.md` (stale, records the meeting's
  old `09:00` start) and `...-986eee44.md` (current, `12:30`) and
  delete/merge the stale one by hand; (2) optionally, append a one-line
  correction note to `ADR-019`'s own Consequences section (never edit its
  body directly — this file's own "never edit an Accepted ADR" rule) since
  its "zero real notes" claim is now factually outdated by this one note,
  though it changes nothing about the ADR's own core decision (the task's
  Constraints already forbid re-adding the dropped middle tier regardless
  of this finding); (3) read `## Retrospective` in `SPRINT-017`'s own
  sprint file and copy the "Patterns to carry forward"/"Antipatterns to
  avoid" entries into `Implementation/Learnings.md`. Full evidence: `Implementation/Tasks/REQ-SB-08-US-01-T06-global-appointment-id-dedup-key-fix.md`'s own Implementation Log.
  → `Implementation/Sprints/SPRINT-017-meeting-dedup-key-hardening.md`

- [ ] 2026-08-12 · **SPRINT-014 / REQ-SB-25-US-01** · spot-check five real,
  live-discovered technical corrections; skim the sprint retrospective and
  harvest learnings
  Plain English: `SPRINT-014` (`REQ-SB-25-US-01`, real Provider-backed
  conversational agent chat, LangGraph + shared MCP server foundation) is
  `Done` — all 8 tasks built and all 5 locked ACs verified live against
  the real backend, the real Compass Provider, and the real vault
  (`Implementation/Tasks/REQ-SB-25-US-01-T08-agents-router-chat-real-
  reply.md`'s own Implementation Log has full evidence for each). No
  locked AC was weakened, omitted, or worked around, and no
  `ESCALATIONS.md` entry was needed — but five separate tasks each
  required a real, live-discovered technical correction beyond their own
  literal `## Files to Modify` code or `## Tests` instructions, every one
  documented in that task's own Implementation Log and cross-referenced in
  `MEMORY.md`'s Constraints:
  1. **`T01`** — none (clean real `pip install`, no correction needed —
     included here only as the starting point of the story).
  2. **`T05`** (`mcp_server.py`/`main.py`) — `FastMCP`'s default
     `streamable_http_path="/mcp"` double-nests to an unreachable
     `/mcp/mcp` once mounted at `app.mount("/mcp", ...)`; and a
     `Mount()`-ed sub-app's own `lifespan` (needed to initialize the MCP
     SDK's Streamable HTTP task group) is not invoked automatically by
     FastAPI/Starlette — `main.py`'s `lifespan` now explicitly composes
     both via `AsyncExitStack`.
  3. **`T06`** (`mcp_client.py`) — the hardcoded loopback port changed
     from the task's own literal `8000` to `8002` (not even this
     project's usual `8001`) — port `8000` is the known `agentic-map`
     conflict, and port `8001` was found live-occupied by a process this
     coder session could neither identify nor terminate via any available
     tool (a likely sandbox-visibility boundary, not a second genuine
     Second Brain instance) — worth a human check whether that's expected
     in this environment.
  4. **`T07`** (`model_factory.py`/`graph.py`) — `ChatOpenAI`/the OpenAI
     SDK appends `/chat/completions` onto `base_url` itself, but
     `provider_registry`'s stored `endpoint` already includes that suffix
     (the shape `compass_client.py`'s own plain `httpx.post` expects) —
     fixed via a suffix strip. Separately, a real Compass/GPT-5 call
     genuinely chose to call a bound vault-query tool for an ordinary
     question, which the task's own literal single-node code left
     unexecuted (an empty reply) — fixed with a minimal, self-contained
     tool-execution loop (one additional node + conditional edge, entirely
     within `graph.py`, no change to `T02`'s `state.py` schema).
  5. **`T08`** (verifying `AC-03`/`AC-05`) — the tool-execution loop's
     round-limit guard had a real bug (it counted every `AIMessage` in the
     *full replayed history*, not just the current turn's own rounds,
     so a second, ordinary turn later in a real conversation could
     false-trip it) — fixed with a current-turn-only backward walk.
     Separately, `AC-05`'s own literal verification instruction (create a
     *new* throwaway Provider pointed at a dead port) can never reach a
     real network call at all under `provider_registry.has_real_client`'s
     existing hardcoded-`"compass"`-only gate — verified instead by
     temporarily repointing the real `"compass"` Provider's own endpoint,
     then restoring it immediately.
  None of these touched a file outside the correcting task's own declared
  scope, none weakened a locked AC, and every one was re-verified live to
  actually work after the fix — but five corrections in one 8-task story
  is a genuinely higher rate than this project's usual sprints, worth a
  closer human read than a routine retro-harvest pass. The coder drafted
  a Retrospective (see below) but does not write
  `Implementation/Learnings.md` directly.
  **What to do:** (1) spot-check the five corrections above against their
  own task's Implementation Log (`Implementation/Tasks/REQ-SB-25-US-01-
  T05/T06/T07/T08-*.md`) and `MEMORY.md`'s Constraints section — accept as
  correct, or direct a follow-up fix/ADR if any looks wrong; (2) in
  particular, confirm whether port `8001` being live-occupied and
  unmanageable (item 3 above) is expected behavior in this environment or
  itself worth investigating; (3) read `## Retrospective` in the sprint
  file, then copy (verbatim or expanded) the "Patterns to carry forward"
  and "Antipatterns to avoid" entries into `Implementation/Learnings.md`.
  → `Implementation/Sprints/SPRINT-014-real-conversational-agent-chat.md`
  → `Implementation/UserStories/REQ-SB-25-US-01-real-conversational-agent-chat.md`
  → `Implementation/Tasks/REQ-SB-25-US-01-T05-mcp-server.md`
  → `Implementation/Tasks/REQ-SB-25-US-01-T06-mcp-client.md`
  → `Implementation/Tasks/REQ-SB-25-US-01-T07-conversation-graph.md`
  → `Implementation/Tasks/REQ-SB-25-US-01-T08-agents-router-chat-real-reply.md`

  **Update, 2026-08-12 — Spot-checked, accepted.** All five corrections
  reviewed individually against their own Implementation Log — each is a
  real bug found through live testing, verified working, cleaned up
  correctly, and stayed within already-owned files. On the port-8001
  question: almost certainly session noise from multiple concurrent
  coder/dev-server processes running during this same heavy session
  (`SPRINT-016` and others), not an environment problem — worth a glance
  next time you start the backend normally, but not treated as a
  blocker. `gate:` reset to `clear` on the story, sprint, and all four
  tasks. Only the retrospective harvest into `Learnings.md` remains open
  (your step).

- [ ] 2026-08-12 · **SPRINT-015 / REQ-SB-26-US-01** · spot-check one real,
  live-discovered technical correction in `T03`; skim the sprint
  retrospective and harvest learnings
  Plain English: `SPRINT-015` (`REQ-SB-26-US-01`, Agent Memory —
  persistent, per-agent fact recall; `REQ-SB-27-US-01`, Skills Repository
  — registration and per-agent access, plumbing only) is `Done` — all 8
  tasks (4 + 4) built and every locked AC verified live (4 for
  `REQ-SB-26-US-01`, 5 for `REQ-SB-27-US-01`) against the real backend
  (port `8002`, same environment reasoning `SPRINT-014` already
  established — ports `8000`/`8001` both live-occupied by unrelated
  processes on this host), the real Compass Provider, and the real vault.
  Full evidence: `Implementation/Tasks/REQ-SB-26-US-01-T04-agents-router-
  chat-memory-wiring.md` and `Implementation/Tasks/REQ-SB-27-US-01-T04-
  skills-router.md`'s own Implementation Logs.
  One real, live-discovered technical correction was needed, in
  `REQ-SB-26-US-01-T03` (`graph.py`) — this task's own literal code
  sample was a "full replacement" written against an earlier, simpler
  shape of `graph.py` (a single `call_model` node); the REAL, already-
  `Done` `graph.py` (`REQ-SB-25-US-01-T08`'s own live correction, landed
  after this task file was authored) had since grown a
  `call_model`⇄`execute_tools` tool-calling loop. Blindly overwriting with
  the task's own literal sample would have regressed `REQ-SB-25-US-01`'s
  own already-verified tool-calling mechanism. Instead, the two new nodes
  (`retrieve_memory`/`extract_memory`) were composed around the real
  current graph (`retrieve_memory → call_model → {execute_tools loop, or
  extract_memory → END}`), and `_extract_memory`'s own completion-context
  construction was corrected to avoid duplicating the model's final reply
  message (the real `call_model` already appends its own response onto
  `messages`, unlike the task sample's assumption). Full reasoning: `T03`'s
  own Implementation Log. No locked AC was weakened, omitted, or changed
  in meaning; no file outside `T03`'s own declared scope (`graph.py`) was
  touched; both stories' remaining 7 tasks needed no correction beyond
  two ordinary scope-internal reconciliations already anticipated by
  their own task text (`REQ-SB-27-US-01-T02`'s tool registration needing
  zero `mcp_server.py` edits; `T03`'s dispatch-table reconciliation
  against `T02`'s real one-function-per-skill shape) — see those tasks'
  own Implementation Logs for detail, not flagged separately since each
  was explicitly anticipated by its own task's text as a reconciliation
  call, not a correction of a wrong assumption. The coder drafted a
  Retrospective (see below) but does not write `Implementation/
  Learnings.md` directly.
  **What to do:** (1) spot-check the `T03` correction above against its
  own Implementation Log and `graph.py`'s own `_extract_memory` docstring
  — accept as correct, or direct a follow-up fix if it looks wrong; (2)
  read `## Retrospective` in the sprint file, then copy (verbatim or
  expanded) the "Patterns to carry forward" and "Antipatterns to avoid"
  entries into `Implementation/Learnings.md`.
  → `Implementation/Sprints/SPRINT-015-agent-memory-and-skills-repository.md`
  → `Implementation/UserStories/REQ-SB-26-US-01-agent-memory.md`
  → `Implementation/UserStories/REQ-SB-27-US-01-skills-repository-registration-and-access.md`
  → `Implementation/Tasks/REQ-SB-26-US-01-T03-graph-memory-nodes.md`
  → `Implementation/Tasks/REQ-SB-26-US-01-T04-agents-router-chat-memory-wiring.md`
  → `Implementation/Tasks/REQ-SB-27-US-01-T04-skills-router.md`

- [ ] 2026-08-12 · **REQ-SB-30-US-01** · decide the retrofit behavior for
  the 181 already-captured emails (~22 currently inside the 7-day My Day
  window) before this story proceeds to `/plan-tasks`
  Plain English: REQ-SB-30 (Email Importance Filtering via Compass
  Reasoning) is specced — three of the PRD breadcrumb's four open
  questions were resolved directly (extend the existing capture-time
  Compass call rather than add a second one; judge importance at capture
  time, not on every My Day page view; a binary show/hide filter, not a
  visible score/tier). The fourth is genuinely open and blocks nothing
  else in the story, but does need a decision: the ~22 real emails
  currently inside today's 7-day My Day window have no importance
  judgment yet, and won't until either (a) a one-time retrofit classifies
  them now (real Compass cost, ~181 calls if the full backlog is
  included, or fewer if scoped to just the in-window ~22), or (b) nothing
  extra is done and the window naturally rolls past them within a week —
  in which case a further sub-choice exists too: whether a missing
  importance field is treated as "not important" (excluded from the list,
  which could make My Day's Emails list look sparser than reality for up
  to a week) or "important" (shown by default until reclassified). No PRD
  text or code precedent favors one option over another — this is a real
  product call, not a detail with an obvious answer, so it was flagged
  rather than guessed.
  **What to do:** decide (a) backfill now (full 181 or just the ~22
  in-window) via a one-time retrofit mirroring this codebase's existing
  retrofit precedent (e.g. `retrofit_email_sender_links`), or (b) let the
  window roll, and if (b), decide whether a not-yet-classified email
  defaults to shown or hidden in the meantime. Record the decision in
  `REQ-SB-30-US-01`'s `## Notes`, then reset its `gate:` to `clear` and run
  `/plan-tasks`.
  → `Implementation/UserStories/REQ-SB-30-US-01-email-importance-filtering-via-compass.md`

  **Update, 2026-08-12 — Resolved.** Backfill only the ~22 emails
  currently in-window (not all 181); fail-open for any missing/errored
  classification. Recorded in the story's own `## Notes`. `gate:` reset
  to `clear`, proceeding to `/plan-tasks`.

- [ ] 2026-08-12 · **REQ-SB-31-US-01** · decide placement, and whether
  unhandled-exception surfacing is in scope this pass, then run `/design`
  Plain English: REQ-SB-31 (System Health View) is prompted directly by
  today's own real debugging session (an orphaned stale `uvicorn --reload`
  worker, then a hardcoded stale MCP port that 500'd every chat call with
  no signal anywhere in the UI). Three of its four open PRD questions were
  resolved directly from real code, reusing what already exists: the MCP
  server mount's already-proven `GET /mcp` → `406` liveness signal, the
  already-shipped `provider_available`/`has_real_client` per-Provider
  signal (`REQ-SB-19`, Done), and `.second-brain/last_capture_run.json`'s
  existing completion timestamp — all passive reporting plus one
  lightweight local check, not new active round-trip probing of external
  Providers. Two questions remain genuinely open: (1) **placement** — a
  new nav item/page, a Settings section, or a persistent app-shell status
  indicator are all equally reasonable, and no prototype screen or prior
  story settles it; (2) **whether this story should also close a real,
  currently-live gap found by directly reading the chat path's code** —
  two of three failure shapes in `run_agent_conversation` (Provider not
  configured; a genuine Provider-call failure) already funnel into an
  honest `{"error": ...}` result, but the function's own outer body (the
  MCP tool-loading call and the graph invocation) is not yet wrapped the
  same way, so an exception there still produces a raw, unhandled 500 with
  no user-facing signal — exactly the shape of today's second real bug.
  Whether closing that gap belongs in this story or is separate follow-on
  hardening is a genuine product/architecture call, not decided here.
  **What to do:** decide (1) where this view lives (nav item, Settings
  section, or persistent indicator), and (2) whether unhandled-exception
  surfacing is in this story's scope or deferred as separate hardening
  work. Record both decisions in `REQ-SB-31-US-01`'s `## Notes`, flip
  `ESCALATIONS.md` → `ESC-014` to `Resolved`, reset `gate:` to `clear`,
  then run `/design REQ-SB-31` (genuinely net-new UI — no
  `html-prototype/` screen covers any part of this today) before
  `/plan-tasks`.
  → `Implementation/UserStories/REQ-SB-31-US-01-system-health-view.md`
  → `ESCALATIONS.md`

  **Update, 2026-08-12 — Resolved.** Operator decided, in chat: (1)
  placement is a new top-level nav page; (2) the `run_agent_conversation`
  crash gap is closed in this story (Scenario 8), asked as a direct
  follow-up; and, surfacing in the same exchange, a real correction to the
  story's own original design — on the System Health view specifically, an
  agent with no real Provider client is shown as Disabled and listed as a
  Health Issue (overriding the story's original neutral "not configured"
  proposal, scoped to this view only). All recorded in the story's own
  `## Context`/`## Notes`. `ESCALATIONS.md` → `ESC-014` flipped to
  `Resolved`. `gate:` reset to `clear`. `/design REQ-SB-31` still needs to
  run (genuinely net-new UI — no `html-prototype/` screen covers this)
  before `/plan-tasks`.

  **Update, 2026-08-12 — `/plan-tasks` complete.** `/design REQ-SB-31`'s
  prototype was approved (see the checked entry below). Architect pass:
  no new ADR — `system_health.py`/`system_health_router.py` mirror
  `my_day.py`'s read-only, no-new-persisted-state shape (`ADR-003`);
  `SystemHealthPage.tsx` applies `ADR-010`; the `graph.py` Scenario 8 fix
  applies `ADR-015`'s existing honest-failure-funnel pattern to a second
  call site. Full reasoning: `architecture.md` → "System Health View —
  read-only status aggregation + chat-path crash-gap fix
  (REQ-SB-31-US-01)". Decomposer pass: all 8 scenarios locked
  `AC-01`..`AC-08`; 4 tasks created (`T01`-`T04`, flat root,
  `depends_on` acyclic: `T02→T03→T04`, `T01` standalone). `status: Ready`,
  `gate: clear` — no MUST-FLAG trigger fired this pass. Eligible for
  `/plan-sprints`.

- [x] 2026-08-12 · **Prototype update: system-health.html (new)** · Approved
  2026-08-12 — verified live via a temporary static server
  (`tools/run-prototype.cmd`, `.claude/launch.json` → `second-brain-html-prototype`,
  port 8088; the `file://` preview renders as a static, non-interactive
  snapshot in this environment, so a real HTTP server was used to exercise
  the actual toggle JS). Both state-switcher groups toggle correctly
  (`health-overview`: healthy ↔ issues, confirmed "People Notes — Disabled"
  appears as a Health Issue in the issues state and MCP shows
  Unreachable/`.badge-danger`; `capture-run`: completed timestamp ↔ honest
  "no run has ever completed" empty state) — verified via DOM inspection
  since this session's `computer` click tool does not dispatch a trusted
  click event this page's (pre-existing, same-pattern-as-settings.html)
  synthetic listener responds to; confirmed the same non-issue exists on
  the already-shipped `settings.html` state-switcher, so this is a known
  tool/environment limitation, not a defect introduced by this design.
  Confirmed the "System Health" nav item is wired and highlights correctly
  on `index.html`, `agents-map.html`, and `system-health.html` itself.
  `/plan-tasks REQ-SB-31` is the next step.
  Plain English: designed for `REQ-SB-31-US-01` (System Health View),
  already `gate: clear` with all three operator decisions resolved (new
  top-level nav page; a Provider-less agent shown Disabled and listed as a
  Health Issue on this view only; Scenario 8's crash-gap fix is
  backend-only, no unique UI shape). A new `html-prototype/system-health.html`
  page, wired into the shared sidebar `.nav-item` list on every prototype
  page (`index.html`, `agents-map.html`, `agents-map-exploration.html`,
  `my-day.html` + its 4 drill-downs + `my-day-approvals.html`,
  `settings.html`, and the new page itself) so the shared shell stays
  consistent everywhere. Shows four regions: (1) a Health Issues list —
  empty/"No Health Issues" when everything is healthy, or listing the
  MCP/agent-orchestration path (when unreachable) and any agent whose
  selected Provider has no real client (shown `Disabled`, matching
  settings.html's own existing example data — People Notes / Anthropic
  Claude); (2) an MCP/agent-orchestration status row (`GET /mcp` →
  reachable/unreachable, visibly distinguished via `.badge-success`/
  `.badge-danger`); (3) a Providers status list, rolled up per distinct
  Provider from each agent's own selection — kept honest and unchanged from
  Settings' own "no real client" language (`ADR-014` point 7) for the
  Provider row itself, since the Disabled/Health-Issue override applies to
  the affected *agent*, not the Provider entry; (4) a last-capture-run
  status row reading `.second-brain/last_capture_run.json`'s own recorded
  `finished_at` timestamp, or an honest "no capture run has completed yet"
  empty state (never a fabricated default). Two state-switcher groups
  demonstrate all 8 Gherkin scenarios: `data-group="health-overview"`
  ("Everything healthy" = Scenarios 1/4, "Health issues present" =
  Scenarios 2/3) and `data-group="capture-run"` ("A run has completed" =
  Scenario 5, "No run has ever completed" = Scenario 6). Scenario 7
  (reopening reflects fresh state, not a cached snapshot) is a text note
  next to a Refresh affordance, per this batch's own instruction that it
  needs no unique static-prototype treatment — mirrors the "recomputes
  fresh, never cached" precedent already established for My Day's rolling
  window (`REQ-SB-22-US-01`). Scenario 8 is backend-only and has no region
  on this page (see the story's own Non-Goals — no persisted "last
  unhandled exception" signal exists yet for this page to read passively).
  Composed entirely from existing tokens/components — `.card`, `.badge`/
  `.badge-success`/`.badge-warning`/`.badge-danger`, `.kv-list`/`.kv-row`,
  `.item-list`/`.item-row`/`.item-row-main`/`.item-row-title`/
  `.item-row-meta`, `.state-switcher`/`[data-state-panel]`, `.empty-state`
  (defined in `styles.css` but not yet used by any screen — this is its
  first real use, exactly the "no issues" case it exists for), `.btn`/
  `.btn-primary`. **No new CSS was added.** New nav icon: `&#9877;`
  (Staff of Aesculapius, ⚕) added inline per the existing `.nav-icon`
  entity-glyph convention (matches `&#9678;`/`&#9728;`/`&#9881;`/`&#9638;`
  already used by the other four nav items) — no new CSS class.
  **What to do:** open `html-prototype/system-health.html` in a browser.
  Toggle both state-switcher groups (top: "Everything healthy" /
  "Health issues present"; below: "A run has completed" / "No run has ever
  completed") and confirm all 4 regions read correctly in every state.
  Confirm the new "System Health" nav item appears and works from every
  other prototype page's sidebar too. Once approved, run `/spec` on
  `REQ-SB-31` (no story changes needed — `REQ-SB-31-US-01` is already
  `gate: clear`; `/plan-tasks` is the next real step once this prototype is
  signed off).
  → `html-prototype/system-health.html`
  → `html-prototype/index.html`
  → `html-prototype/agents-map.html`
  → `html-prototype/agents-map-exploration.html`
  → `html-prototype/my-day.html`
  → `html-prototype/my-day-emails.html`
  → `html-prototype/my-day-calendar.html`
  → `html-prototype/my-day-todo.html`
  → `html-prototype/my-day-reads.html`
  → `html-prototype/my-day-approvals.html`
  → `html-prototype/settings.html`
  → `Implementation/UserStories/REQ-SB-31-US-01-system-health-view.md`

- [x] 2026-08-12 · **REQ-SB-33-US-01-T01** · Approved 2026-08-12 — the
  monkeypatch substitution is an acceptable equivalent (same induced
  condition, real production code path, zero out-of-scope file edits);
  also promoted to a standing pattern in `Implementation/Learnings.md`
  Plain English: `REQ-SB-33-US-01-T01` (grounding/honest-uncertainty
  system-prompt instruction) is `Done` — all 4 locked ACs verified live
  and passing. The task's own `## Tests` step 3 named an example AC-03
  technique ("temporarily point the agent's Provider/MCP client at an
  unreachable target") that would have required editing `mcp_client.py`,
  a file outside this task's own `## Files to Modify` (`state.py` only).
  Rather than touch any out-of-scope file, even temporarily, the coder
  used a zero-file-touch substitute: a standalone script (kept in the
  session scratchpad, never written into `src/`) that loads the real MCP
  tools via the real running server, monkeypatches a tool's `.coroutine`
  in-process to raise, and calls the real, unmodified
  `run_agent_conversation` directly — exercising the genuine production
  `_call_model`/`_execute_tools` code path end-to-end with only the
  *tool result* substituted, not any application code. Two passes were
  run (one tool failing, then every tool failing); both show the model
  honestly reporting the failure, never fabricating a substitute answer.
  **What to do:** confirm this substitution is an acceptable equivalent to
  the task's own named example technique (same induced condition, real
  code path, zero out-of-scope file edits) — no action needed if so; the
  task's own Implementation Log has the full reasoning and both AC-03
  transcripts.
  → `Implementation/Tasks/REQ-SB-33-US-01-T01-grounding-honest-uncertainty-system-prompt.md`

- [x] 2026-08-12 · **SPRINT-018** · Done 2026-08-12 — retro's Patterns/
  Antipatterns/Sizing calibration harvested verbatim into
  `Implementation/Learnings.md`; the "What didn't work"/"Open follow-ups"
  sync-node concern was also filed as `BUG-007` in `BUGS.md`
  Plain English: SPRINT-018 (`REQ-SB-33-US-01`, agent grounding &
  honest-uncertainty guardrail) is Done — its one task built and verified
  live against the real backend/vault/Compass Provider. All 4 locked ACs
  pass, including the regression guard (a real tool-backed question still
  answers normally, exact match against the real vault's known-customer
  list) and the three honesty scenarios (no relevant tool result, a real
  induced tool-call failure, and a general-training-knowledge fact about a
  real vault entity that no tool call actually returned). The coder
  drafted a Retrospective, but does not write `Implementation/
  Learnings.md` directly.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" and "Antipatterns
  to avoid" entries into `Implementation/Learnings.md`.
  → `Implementation/Sprints/SPRINT-018-agent-grounding-and-honest-uncertainty-guardrail.md`

- [x] 2026-08-12 · **REQ-SB-31-US-01-T02** · Approved 2026-08-12 — the
  `follow_redirects=True` correction is sound (single-file, in-scope,
  live-verified as the actual fix for AC-01's real-backend correctness);
  retro harvested into `Implementation/Learnings.md`; `BUG-007` updated
  with "no new evidence either way," still Open
  Plain English: `REQ-SB-31-US-01-T02`'s own literal code sample called
  `httpx.get(_MCP_MOUNT_URL, timeout=3.0)` with no `follow_redirects`
  argument. Live-verified against the real backend, this actually
  returns `307` (redirecting `GET /mcp` → `GET /mcp/`), not the `406`
  the story's own Context claims was "confirmed live 2026-08-12" — almost
  certainly because that earlier confirmation used a redirect-following
  client (browser/PowerShell), while `httpx.get()`'s own default is
  `follow_redirects=False`. As spec'd, the real "everything healthy"
  state (Scenario 1/`AC-01`) would have falsely shown the MCP path as
  unreachable even when genuinely healthy. Fixed in-scope, inside this
  task's own `system_health.py` file only (`follow_redirects=True` added
  to the one `httpx.get()` call) — no other file touched, no new
  dependency, no interface change. `SPRINT-019` (`REQ-SB-31-US-01`) is
  now `Done` — all 8 locked ACs verified live against the real backend/
  frontend; the coder drafted a Retrospective.
  **What to do:** confirm the `follow_redirects=True` correction is
  acceptable (it is what makes `AC-01`/`AC-02`'s real-backend states
  correct — verified live in `T04`'s own Implementation Log); then read
  `## Retrospective` in the sprint file and copy the "Patterns to carry
  forward"/"Antipatterns to avoid" entries into
  `Implementation/Learnings.md`.
  → `Implementation/Tasks/REQ-SB-31-US-01-T02-system-health-aggregation-module.md`
  → `Implementation/Sprints/SPRINT-019-system-health-view.md`

- [x] 2026-08-12 · **REQ-SB-35-US-01 + REQ-SB-36-US-01 + REQ-SB-36-US-02** ·
  Resolved 2026-08-12 (see Update note below) — decide the Vault Filing
  Expert's mechanism and new-top-level-area governance, confirm/build a
  real Anthropic web-research client, and note the real cross-sprint
  dependency chain before `/plan-tasks`
  Plain English: three new stories were drafted this pass from today's
  Compass Expert worked example — `REQ-SB-35-US-01` (Vault Filing Expert),
  `REQ-SB-36-US-01` (a new real web-research skill for Research Expert
  agents), and `REQ-SB-36-US-02` (the end-to-end delegated-research
  bootstrap chain, piloted by an empty Compass Expert agent). All three
  are `gate: flagged`. Three separate things are blocking a confident
  `/plan-tasks` pass: (1) `REQ-SB-35-US-01` doesn't know yet whether the
  Vault Filing Expert should be a distinct agent (routed to via the Hub,
  like the Research Expert) or a shared skill any agent calls directly —
  and separately, whether the Vault Filing Expert creating a genuinely new
  **top-level** vault area (a bigger structural decision than adding a
  tag) should get a different confidence bar or check than
  `REQ-SB-36`'s own blanket "no approval at any step" — a real tension
  between the two requirements' own texts, not resolved either way.
  (2) `REQ-SB-36-US-01`'s own premise — that "the Anthropic Claude
  Provider" is "already configured" — turned out to be false: direct code
  inspection this pass found no real Anthropic client anywhere in this
  codebase (`provider_registry.py`'s real-client set is hardcoded to
  `{"compass"}` only; no `anthropic`/`langchain-anthropic` dependency; no
  `.env` key; `model_factory.py` is OpenAI-wire-only). Building this skill
  needs real, new client work first, and the exact web-search mechanism
  (Anthropic's own native tool vs. a custom search API) is also
  undecided. (3) `REQ-SB-36-US-02` (the actual end-to-end chain) depends
  on FOUR other stories that are not `Done` yet — `REQ-SB-20-US-01`
  (Ready, unbuilt), `REQ-SB-35-US-01` and `REQ-SB-36-US-01` (this same
  batch, both flagged), and `REQ-SB-29-US-01` (Draft, needed for the
  "agent can draw on it afterward" half) — it cannot be meaningfully built
  until all four are real, working code.
  **What to do:** (a) decide the Vault Filing Expert's mechanism
  (distinct Hub-routable agent vs. shared skill) and whether new-
  top-level-area creation needs its own confidence bar/check — record the
  decision in `REQ-SB-35-US-01`'s `## Notes` and flip `ESCALATIONS.md` →
  `ESC-015` to `Resolved`; (b) decide how the real Anthropic (or
  equivalent) web-search client gets built (extend `model_factory.py`, or
  a new sibling client module mirroring `compass_client.py`) and the exact
  web-search mechanism — record in `REQ-SB-36-US-01`'s `## Notes` and flip
  `ESCALATIONS.md` → `ESC-016` to `Resolved`; (c) once (a)/(b) are
  resolved and `REQ-SB-20-US-01`/`REQ-SB-29-US-01` are further along, run
  `/plan-tasks` on all three stories in dependency order (`REQ-SB-35-US-01`
  and `REQ-SB-36-US-01` first, `REQ-SB-36-US-02` last).
  → `Implementation/UserStories/REQ-SB-35-US-01-vault-filing-expert.md`
  → `Implementation/UserStories/REQ-SB-36-US-01-web-research-skill.md`
  → `Implementation/UserStories/REQ-SB-36-US-02-agent-knowledge-bootstrapping-delegated-research-chain.md`
  → `ESCALATIONS.md`

  **Update, 2026-08-12 — Resolved.** The operator answered all three
  points directly (recorded verbatim in `Documentation/PRD.md`'s
  `REQ-SB-35`/`REQ-SB-36` breadcrumbs): (a) the Vault Filing Expert is a
  distinct agent, reached via `REQ-SB-20`'s Hub routing ("This is an
  Agent"); (b) a tag/subfolder within an existing top-level area proceeds
  autonomously, but a wholly new top-level vault area pauses for explicit
  approval (reusing `REQ-SB-21`/`ADR-020`'s existing Pending-Approvals
  machinery for that one action type only); (c) building a real Anthropic
  Provider integration is confirmed in scope for the Research Expert's
  web-search skill ("Yes add Anthropic APIs Support"), with the mechanism
  confirmed as Anthropic's own server-side web-search tool. All three
  stories were re-specced in place to incorporate these resolutions.
  `ESCALATIONS.md` → `ESC-015`/`ESC-016` both flipped to `Resolved`.
  `gate:` reset to `clear` on all three stories — `REQ-SB-35-US-01` and
  `REQ-SB-36-US-01` because their own genuinely open interpretive
  questions are now fully resolved; `REQ-SB-36-US-02` because its own
  inherited fork is resolved too and its real forward dependency on the
  other two (plus `REQ-SB-20-US-01`) is recorded plainly in its own `##
  Dependencies` rather than kept as a gate reason, mirroring
  `REQ-SB-20-US-01`'s own established precedent for handling an unmet
  `Blocked by` dependency. All three stories are ready for `/plan-tasks`,
  sequenced behind `REQ-SB-20-US-01`/`REQ-SB-35-US-01`/`REQ-SB-36-US-01`
  actually shipping for `REQ-SB-36-US-02` specifically — a
  `/plan-sprints`-time concern, not a blocker to starting `/plan-tasks` on
  the three now-`clear` stories themselves.

- [x] 2026-08-12 · **REQ-SB-35-US-01 / REQ-SB-36-US-01 / REQ-SB-36-US-02** ·
  Approved 2026-08-12 — `ADR-021`'s Tier-2 bypass-by-construction design,
  `ADR-022`'s tool-binding-gap fix, and `ADR-023`'s deterministic-
  composition orchestration are all sound; `REQ-SB-21-US-01` was
  sequenced through `/plan-tasks` first (separately) so `ESC-017`'s
  cross-story `depends_on` wiring uses real task IDs, not a placeholder
  Plain English: `/plan-tasks` step 1 (architect) wrote three new ADRs, one
  per story. `ADR-021` (`REQ-SB-35-US-01`) designs the Vault Filing Expert
  as a new registry agent with a deterministic-context-injected LLM
  placement decision, a generic `write_note`-based Tier-1 write, and a
  Tier-2 new-top-level-area approval path that bypasses the working-mode
  gate by construction (an additive `payload` field on `ADR-018`'s own
  unedited Pending-Approvals schema, plus a new `_APPROVAL_HANDLERS`
  dispatch table on the Approve endpoint). `ADR-022`
  (`REQ-SB-36-US-01`) designs a real Anthropic Provider integration — a
  plain `anthropic` SDK client (not LangChain-wrapped, since this skill
  never touches the conversational graph), a new auto-seeded "Anthropic
  Claude" Provider entry, and a new `web_research` skill using Anthropic's
  own server-side web-search tool — **and closes a live-discovered gap**:
  every agent's chat could already reach any registered skill tool
  (including a real one, once built) with no access-control check at all;
  `mcp_client.py` now filters the shared MCP server's tool list per agent
  via `skill_registry.has_skill_access`. `ADR-023` (`REQ-SB-36-US-02`)
  designs the delegated knowledge-bootstrap chain itself — a new
  orchestration module that actually invokes a Hub-routing match
  (`ADR-017`'s routing node, as already built/designed, only ever
  discovers a candidate agent; nothing before this pass ever acted on
  one) by composing the web-research skill invocation and the Vault Filing
  Expert's own placement function deterministically, triggered as a new
  `"build_knowledge"` action on a new pilot Expert agent (e.g.
  `"compass-expert"`, a plain code-level registry addition).
  **A real, load-bearing finding from this same pass, not a design
  question:** both `REQ-SB-35-US-01`'s and `REQ-SB-36-US-02`'s own `##
  Dependencies` sections assert `REQ-SB-21-US-01`/`ADR-020` is "(Done)" —
  direct inspection of that story's own file (`status: Draft`, `gate:
  flagged`, its decomposer not yet re-run since `ADR-020` corrected
  `ADR-018`) and of the real codebase (no `pending_approval_registry.py`,
  no `working_mode_registry.py`, no `pending_approvals_router.py`, no
  working-mode gate anywhere in the real `agents_router.py`) found this
  false. `ADR-021`'s Tier 2 and `ADR-023`'s Autonomous-mode check both
  carry a real, currently unmet blocking prerequisite on `REQ-SB-21-US-01`
  actually shipping — full detail in `ESCALATIONS.md` -> `ESC-017`.
  **What to do:** review `ADR-021`/`ADR-022`/`ADR-023` in
  `Implementation/Architecture/ADR.md` (approve or reject each — in
  particular `ADR-021`'s Tier-2 bypass-by-construction design and
  `ADR-022`'s tool-binding-gap fix), then run `/plan-tasks` again if any
  change. Separately, resolve `ESC-017` (below) before the decomposer
  wires any Tier-2/Autonomous-mode-check task's `depends_on` — the
  decomposer's own next pass should leave those specific tasks
  individually flagged with `depends_on: []`, mirroring `ESC-011`'s own
  precedent, rather than fabricate a task-id reference.
  → `Implementation/UserStories/REQ-SB-35-US-01-vault-filing-expert.md`
  → `Implementation/UserStories/REQ-SB-36-US-01-web-research-skill.md`
  → `Implementation/UserStories/REQ-SB-36-US-02-agent-knowledge-bootstrapping-delegated-research-chain.md`

  **Update, 2026-08-12 (`/plan-tasks` step 2 — decomposer, all three
  stories).** Decomposition is now complete. `REQ-SB-35-US-01` — 8
  scenarios locked `AC-01`-`AC-08`, 3 tasks (`T01`-`T03`), `status: Ready`.
  `REQ-SB-36-US-01` — 4 scenarios locked `AC-01`-`AC-04`, 6 tasks
  (`T01`-`T06`), `status: Ready`, fully self-contained except one
  deliberate cross-story sequencing edge (`T06` → `REQ-SB-20-US-01-T05`,
  a real same-call-site collision risk this decomposer pass caught and
  fixed, not an ADR change — see that story's own `## Notes`).
  `REQ-SB-36-US-02` — 6 scenarios locked `AC-01`-`AC-06` (`AC-03` locked
  but `locked: false` is NOT used — it is locked, just individually
  blocked at the task level, see below), 4 tasks (`T01`-`T04`), `status:
  Ready`. `ESC-017`'s own real cross-story `depends_on` wiring onto
  `REQ-SB-21-US-01`'s now-real task ids is complete for all three stories
  — `ESC-017` is flipped to `Resolved`. `gate: flagged` is unchanged on
  all three — the architect's own `ADR-021`/`ADR-022`/`ADR-023` review
  (above) is still the open item; this decomposer does not clear it.
  **A genuine judgement call, flagged for explicit confirmation, not
  silently decided:** `REQ-SB-36-US-02`'s own Scenario 3 composes with
  `REQ-SB-29-US-01`, which — unlike `REQ-SB-21-US-01` — has never been
  decomposed at all (zero task files exist). Rather than hold the entire
  story at `Draft` the way `ESC-011`'s own precedent did for an analogous
  single-blocked-task situation, this pass advanced `REQ-SB-36-US-02` to
  `status: Ready` (its own literal Ready-criteria are genuinely satisfied)
  while individually holding only the one affected task,
  `REQ-SB-36-US-02-T04`, at `status: Draft`/`gate: flagged` with a
  prominent "⚠️ BLOCKED" section — `T01`/`T02`/`T03` are `Ready` and
  buildable now. New `ESCALATIONS.md` → `ESC-018` records the finding.
  **What to do:** (1) review `ADR-021`/`ADR-022`/`ADR-023` (already
  requested above); (2) confirm — or override — this pass's own judgement
  call to advance `REQ-SB-36-US-02` to `Ready` with only `T04`
  individually blocked, rather than holding the whole story at `Draft`
  per `ESC-011`'s own fuller-lockstep precedent; (3) once `REQ-SB-29-US-01`
  is eventually decomposed, run a follow-up decomposer pass to replace
  `REQ-SB-36-US-02-T04`'s own `depends_on: []` with the real task id.
  → `Implementation/UserStories/REQ-SB-35-US-01-vault-filing-expert.md`
  → `Implementation/UserStories/REQ-SB-36-US-01-web-research-skill.md`
  → `Implementation/UserStories/REQ-SB-36-US-02-agent-knowledge-bootstrapping-delegated-research-chain.md`
  → `Implementation/Tasks/REQ-SB-36-US-02-T04-draw-on-afterward-composition-check.md`
  → `ESCALATIONS.md`

- [ ] 2026-08-12 · **ESC-017** · `REQ-SB-21-US-01` needs a fresh decomposer
  pass before `REQ-SB-35-US-01`'s Tier 2 or `REQ-SB-36-US-02`'s own chain
  can be fully task-planned
  Plain English: this architecture pass found, by direct inspection (not
  trusted from other stories' own prose), that `REQ-SB-21-US-01` (Agent
  Working Modes & Pending Approvals) is still `status: Draft`, `gate:
  flagged` — its `ADR-018`→`ADR-020` correction was designed, but its
  decomposer has not re-run since, and zero of its 8 tasks have been
  built. Two other stories' own `## Dependencies` sections wrongly assert
  this story is "Done." `ADR-021`'s Vault Filing Expert Tier 2 and
  `ADR-023`'s delegated knowledge-bootstrap chain both genuinely need this
  story's own `pending_approval_registry.py`/`working_mode_registry.py`
  to exist before their own Tier-2/Autonomous-mode-check coder tasks can
  be built or verified.
  **What to do:** run `/plan-tasks` on `REQ-SB-21-US-01` (its own
  decomposer step, re-deriving `T04`/`T05` against `ADR-020`'s corrected
  gate, per that story's own already-recorded note), then
  `/implement-sprint` to actually build it. Once its tasks are real and
  `Ready`, run a follow-up decomposer pass on `REQ-SB-35-US-01`/
  `REQ-SB-36-US-02` to replace their own Tier-2/Autonomous-mode-check
  tasks' placeholder `depends_on: []` with the real task ids — mirroring
  `ESC-011`'s own already-used resolution pattern exactly.
  → `Implementation/UserStories/REQ-SB-21-US-01-agent-working-modes.md`
  → `ESCALATIONS.md`

  **Update, 2026-08-12 — half-resolved: `REQ-SB-21-US-01`'s own decomposer
  step has now run; the cross-story wiring below is still the open item.**
  `REQ-SB-21-US-01` is now `status: Ready`, 9 tasks (`T01`-`T09`, all
  `Ready`) — see the `ADR-020` review entry above for the full detail. **Not
  yet done:** (a) `/implement-sprint` has not built any of these 9 tasks
  yet — `REQ-SB-21-US-01`'s own mechanism still does not exist in the real
  codebase; (b) the follow-up decomposer pass on `REQ-SB-35-US-01`/
  `REQ-SB-36-US-02` to replace their placeholder `depends_on: []` has not
  run. The real task ids to use when it does: `T02` (Autonomous-mode
  check), `T03`+`T06` (the Pending-Approvals store + router `REQ-SB-35-US-01`
  Tier 2 extends), `T04`+`T09` if either story's own gate logic itself is
  needed. **What to do now:** (1) resolve the `ADR-020` review above; (2)
  run `/plan-sprints` + `/implement-sprint` on `REQ-SB-21-US-01` until it
  reaches `Done`; (3) then run a follow-up decomposer pass on
  `REQ-SB-35-US-01`/`REQ-SB-36-US-02` to wire the real ids in. `ESC-017`
  stays `Open` in `ESCALATIONS.md` until all three steps complete.
  → `Implementation/UserStories/REQ-SB-21-US-01-agent-working-modes.md`
  → `Implementation/UserStories/REQ-SB-35-US-01-vault-filing-expert.md`
  → `Implementation/UserStories/REQ-SB-36-US-02-agent-knowledge-bootstrapping-delegated-research-chain.md`

  **Update, 2026-08-12 — Resolved (step 3 above now complete).** The
  follow-up decomposer pass on `REQ-SB-35-US-01`/`REQ-SB-36-US-02` has run
  (see the combined entry above). Real ids are wired in:
  `REQ-SB-35-US-01-T03` (Tier 2) → `REQ-SB-21-US-01-T03`+`T06`;
  `REQ-SB-36-US-02-T01` → `REQ-SB-21-US-01-T09`; `REQ-SB-36-US-02-T02`
  (Autonomous-mode check) → `REQ-SB-21-US-01-T02`. No placeholder
  `depends_on: []` remains for this finding. `ESCALATIONS.md` → `ESC-017`
  flipped to `Resolved`. **Step 2 above (`/implement-sprint` actually
  building `REQ-SB-21-US-01`'s 9 tasks) is still open** — this resolution
  is about the wiring being real and correct, not about the underlying
  code existing yet; `/implement-sprint` will not start any task whose
  `depends_on` isn't satisfied.
  → `Implementation/UserStories/REQ-SB-35-US-01-vault-filing-expert.md`
  → `Implementation/UserStories/REQ-SB-36-US-02-agent-knowledge-bootstrapping-delegated-research-chain.md`
  → `ESCALATIONS.md`

- [x] 2026-08-12 · **ESC-018** · Confirmed 2026-08-12 — per-task blocking
  (T04 held, T01-T03 proceed) is correct; no reason to hold buildable
  work back for one composition check. Re-run decomposer on
  `REQ-SB-36-US-02-T04` once `REQ-SB-29-US-01` is decomposed
  Plain English: `REQ-SB-36-US-02`'s own Scenario 3 ("the newly-expert
  agent can draw on the filed content afterward") composes entirely with
  `REQ-SB-29-US-01`'s own vault-scope-assignment/retrieval mechanism.
  Unlike `REQ-SB-21-US-01` (already decomposed this session, real `Ready`
  task ids available), `REQ-SB-29-US-01` has **never been decomposed at
  all** — `status: Draft`, zero task files. There is no real task id to
  wire `AC-03`'s own verification onto. Mirroring `ESC-011`'s own
  precedent, a dedicated task (`REQ-SB-36-US-02-T04`) was created,
  `depends_on: []`, individually flagged "⚠️ BLOCKED — do not start."
  **Departing from `ESC-011`'s own full-story-Draft choice, by explicit
  decomposer judgement call:** rather than hold the entire
  `REQ-SB-36-US-02` story (and its other 3 tasks, which have real,
  satisfiable dependencies) at `Draft`, this pass advanced the story to
  `status: Ready` with only `T04` individually held back. Full reasoning
  in `ESCALATIONS.md` → `ESC-018` and `REQ-SB-36-US-02`'s own `## Notes`.
  **What to do:** confirm this more granular per-task-blocking approach is
  acceptable going forward (vs. requiring the full-story-Draft posture
  `ESC-011` used) — either confirm as-is, or direct a reset of
  `REQ-SB-36-US-02`'s own `status:` back to `Draft` to match `ESC-011`'s
  precedent exactly. Separately, whenever `REQ-SB-29-US-01` is decomposed,
  run a follow-up decomposer pass to replace `T04`'s own `depends_on: []`
  with the real task id.
  → `Implementation/UserStories/REQ-SB-36-US-02-agent-knowledge-bootstrapping-delegated-research-chain.md`
  → `Implementation/Tasks/REQ-SB-36-US-02-T04-draw-on-afterward-composition-check.md`
  → `ESCALATIONS.md`

- [x] 2026-08-12 · **SPRINT-020 / REQ-SB-20-US-01** · Approved 2026-08-12
  — all scope-internal corrections (composing around real current file
  state, test-data wording fixes, the Fiber-props-direct-invoke
  verification technique) are sound; `ADR-017` approved above; retro
  harvested below
  Plain English: `SPRINT-020` (`REQ-SB-20-US-01`, Section Hub Intelligence
  & Cross-Section Routing — per-agent keywords, Hub-to-Hub routing node)
  is `Done` — all 6 tasks built and every locked AC (`AC-01`..`AC-04`)
  verified live against the real backend/frontend (headless-Chrome-via-CDP
  for the UI leg). Full evidence: each task's own Implementation Log,
  `Implementation/Tasks/REQ-SB-20-US-01-T01`..`T06`.
  Several real, live-discovered scope-internal corrections were needed,
  none weakening/omitting any locked AC, none touching a file outside its
  own task's declared scope:
  - **`T03`/`T04`/`T05` — composed around the REAL current
    `agents_router.py`/`state.py`/`graph.py`, not each task's own stale
    "Before" code sample.** By build time, sibling stories
    (`REQ-SB-25-US-01-T08`, `REQ-SB-26-US-01`/`ADR-016`,
    `REQ-SB-31-US-01`) had already additively grown these three shared
    files well beyond what this story's own task files (written earlier in
    the decomposition sequence) assumed. Most load-bearing at `T05`: the
    real `graph.py` already had a *generic* `_execute_tools` node that
    invokes any tool call by name — the new `route_hub_request`
    conditional-edge branch had to intercept `request_cross_section_help`
    calls *before* that generic path, or the tool's own intentionally-
    `NotImplementedError` body would have been genuinely invoked on a
    real routing request. This is the same class of correction already
    spot-checked and approved once this session (`REQ-SB-26-US-01-T03`,
    see the entry above) — recurring on the same file (`graph.py`) a
    second time.
  - **`T02`/`T05` — corrected each task's own illustrative example
    need-description.** Both tasks' own literal `## Tests` text used
    `"I need help finding an attendee's bio"` against example keywords
    `["people", "contacts", "attendee bios"]` — under the exact
    deterministic case-insensitive substring-match algorithm both tasks'
    own code specifies (and `ADR-011`/`ADR-017` mandate), none of those
    three keywords is actually a literal substring of that example string
    (`"attendee bios"`, plural with a space, is not a substring of
    `"...an attendee's bio"`, singular with an apostrophe-s). A wording
    slip in the test data, not a defect in the algorithm or the
    implementation (a literal, unmodified copy of each task's own
    provided code) — corrected the example need-description consistently
    across both tasks so the smoke checks genuinely exercise the intended
    behaviour.
  - **`T06` — a verification-technique finding, not a code change.** A
    plain synthetic `blur` `Event` dispatch, and even a real
    `input.focus()`/`input.blur()` DOM-API call pair, did not reliably
    deliver React's delegated `onBlur` handler in this headless-Chrome-
    via-CDP session (confirmed via the CDP `Network` domain — no request
    fired). Resolved via this project's own already-documented Fiber-
    props-direct-invoke pattern (`MEMORY.md` Patterns,
    `REQ-SB-18-US-01-T07`'s own precedent), confirmed to fire the real,
    unmodified `handleKeywordsCommit` code path (a real `PATCH` request
    observed) before relying on it for the rest of `T06`'s own
    verification.
  Full reasoning for every item above: each task's own Implementation Log.
  The coder drafted a Retrospective (see `SPRINT-020`'s own file) but does
  not write `Implementation/Learnings.md` directly.
  **What to do:** (1) spot-check the `T02`/`T03`/`T04`/`T05`/`T06`
  corrections above against each task's own Implementation Log — accept as
  correct, or direct a follow-up fix if any looks wrong; (2) `ADR-017`
  itself remains separately open for review (2026-08-12 entry above,
  unresolved by this build pass — an ADR-creation flag does not halt
  `/implement-sprint`, mirroring the same posture already established for
  `/plan-tasks`); (3) read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" and "Antipatterns
  to avoid" entries into `Implementation/Learnings.md`.
  → `Implementation/Sprints/SPRINT-020-section-hub-intelligence-and-cross-section-routing.md`
  → `Implementation/UserStories/REQ-SB-20-US-01-section-hub-intelligence-and-cross-section-routing.md`
  → `Implementation/Tasks/REQ-SB-20-US-01-T02-agent-keywords-business-module.md`
  → `Implementation/Tasks/REQ-SB-20-US-01-T03-agents-router-keywords-field.md`
  → `Implementation/Tasks/REQ-SB-20-US-01-T04-orchestration-state-routing-field.md`
  → `Implementation/Tasks/REQ-SB-20-US-01-T05-graph-route-hub-request-node.md`

- [x] 2026-08-13 · **REQ-SB-36-US-01 / SPRINT-022** · Re-verification gap
  CLOSED 2026-08-13 — the operator provisioned a genuine
  `ANTHROPIC_API_KEY`/`ANTHROPIC_MODEL` in `src/backend/.env`, replacing
  the provably-inert `NOT-PROVISIONED-PLACEHOLDER`. A coder re-verification
  pass (no source code changed) confirmed both remaining branches live:
  `AC-01` — a real, non-fabricated result with real citations
  (`https://www.python.org/doc/versions/`,
  `https://en.wikipedia.org/wiki/Python_(programming_language)`) for a
  real, checkable query. `AC-03` — two queries engineered to have no real
  answer both honestly reported the model could not find/would not
  fabricate the requested information, `sources: []` — never a fabricated
  plausible-sounding result. **One live-discovered nuance, not a defect,
  worth a human glance:** the real observed honest-empty shape is
  `{"found": true, "summary": <honest refusal text>, "sources": []}`, not
  the literal `{"found": false, "summary": "", "sources": []}` shape
  `T04`'s own `## Files to Modify`/`## Starting State → End State`
  originally documented — `anthropic_client.py`'s `found` flag is `True`
  whenever the API returns any non-empty text, and Claude's Messages API
  essentially always writes *some* explanatory text, even an honest
  refusal, so the literal `found: false` shape appears effectively
  unreachable in practice with the current model/tool combination. The
  locked AC's own wording ("honestly reports... rather than fabricating")
  is satisfied either way; this is a documentation/contract-shape
  discrepancy, not a fabrication or access-control defect. **Separately, a
  genuine operational root cause was found and resolved along the way (not
  a code defect):** `.second-brain/agent_providers.json` had been seeded
  during this same `SPRINT-022`'s own original build pass with the
  placeholder credential, and `provider_registry._load_state()` only
  re-seeds when that file doesn't exist yet — so simply fixing `.env` was
  not, on its own, enough to pick up the real key. Resolved by deleting
  the stale file to force a clean re-seed (the same operational step
  `T03`'s own Implementation Log had already used once before, during the
  original build — re-applied here, not a new discovery). Port `8001`
  bound cleanly this session with no ghost-listener recurrence; backend
  self-started/self-stopped cleanly by the coder session, no orphaned
  process left behind. Full evidence: `T04`/`T05`'s own Implementation
  Logs; the story's own `## Notes`.
  **What to do:** (1) optionally decide whether `AC-03`'s documented
  contract shape should be updated to explicitly allow `found: true` +
  empty `sources` as an honest-empty variant (a `/plan-tasks`-level
  documentation clarification, not required — the real behavior already
  satisfies the AC's own locked wording); (2) no other action needed —
  this entry's own original two asks (Provider-resolution correction
  approval; credential provisioning) are both resolved.
  ~~`ANTHROPIC_API_KEY` provisioning still needed from the operator to
  unblock AC-01/AC-03's remaining live-verification branch~~ — resolved,
  see above.
  Plain English: mid-`/implement-sprint`, the operator directly corrected
  `ADR-022` point 3's design — `web_research` now resolves the invoking
  agent's own linked Provider (`provider_registry.get_agent_provider`)
  rather than a hardcoded `"anthropic-claude"` id, so a Compass-linked
  agent stays honest (Scenario 4's "not available" shape) and only an
  agent explicitly linked to the "Anthropic Claude" Provider gets real
  results. A real technical question was investigated first, not guessed:
  Compass/GPT-5 (Core42) has no real hosted web-search tool — confirmed by
  `compass_client.py`'s own plain request shape and by the sibling
  `agentic-map` project's own use of a *separate* Perplexity Sonar provider
  for its own web-search-capable agents. `T01`-`T06` all built and verified
  against the corrected design (see `ADR-022`'s own "Correction" addendum
  and `ESCALATIONS.md` → `ESC-019`). Separately, and unrelated to this
  correction's own correctness: this environment's real `src/backend/.env`
  has no genuine `ANTHROPIC_API_KEY` — a syntactically-valid, clearly-
  labeled placeholder (`NOT-PROVISIONED-PLACEHOLDER`) was added to `.env`
  (gitignored, not committed) purely so `Settings()`/the app can construct
  and boot for live verification, per `ADR-022`'s own already-Accepted
  Consequences ("any environment missing `ANTHROPIC_API_KEY` fails
  `Settings` construction at startup... an operational step, not a code
  dependency"). This placeholder is provably inert — a real Anthropic call
  against it returns a genuine, honest `401 invalid x-api-key` (confirmed
  live, several times), never a fabricated success. `AC-01`/`AC-03`'s own
  "real relevant result"/"real honest-empty result" verification is
  therefore genuinely blocked on this missing credential — everything else
  (registration, `AC-02`'s access refusal, `AC-04`'s honest-unavailable
  across both the "not-yet-wired" and the "Compass-linked" real
  conditions, the corrected Provider-resolution dispatch itself) is
  verified live against the real running backend.
  **(Original `What to do` list above — superseded 2026-08-13, see the
  entry's own top for the current status: item (1)'s Provider-resolution
  correction is confirmed by this same coder pass's own successful
  Anthropic-linked dispatch; item (2)'s credential provisioning is done;
  item (3)'s port `8001` ghost listener was not present in this
  re-verification session — port `8001` bound cleanly.)**
  → `Implementation/UserStories/REQ-SB-36-US-01-web-research-skill.md`
  → `Implementation/Sprints/SPRINT-022-web-research-skill.md`
  → `Implementation/Architecture/ADR.md` (`ADR-022`'s own Correction addendum)
  → `Implementation/Architecture/architecture.md` (the "Real Anthropic Provider
    integration & web-research skill" section's own `web_research`
    paragraph was also minimally, factually corrected in place by this
    same coder pass — normally architect-owned, touched here only to keep
    it from actively describing the superseded design; flagged for a
    human architect spot-check, not silently assumed correct)
  → `ESCALATIONS.md` (`ESC-019`)
  → `Implementation/Tasks/REQ-SB-20-US-01-T06-agent-detail-panel-keywords-row.md`

- [x] 2026-08-13 · **SPRINT-024 / REQ-SB-36-US-02 (T01-T03)** · Approved
  2026-08-13 — both reconciliations sound (`_execute_async_action`
  split and the `web_search` try/except are correctly scoped, neither
  weakens a locked AC); `vault-qa` reuse as Research Expert noted for
  operator's own call, not decided here
  Plain English: `SPRINT-024`'s three buildable tasks
  (`REQ-SB-36-US-02-T01`-`T03` — the `"compass-expert"` pilot agent,
  `knowledge_bootstrap.py`'s orchestration, and its action dispatch) are
  all `Done`, all locked ACs (`AC-01`/`AC-02`/`AC-04`/`AC-05`/`AC-06`)
  verified live end to end against the real backend, vault, and Compass
  Provider — see each task's own Implementation Log for the full
  transcript. `REQ-SB-36-US-02-T04`/`AC-03` remains `Draft`/blocked on
  `REQ-SB-29-US-01`'s own decomposition (`ESC-018`, still `Open`,
  unchanged this pass) — the story itself stays `status: In Progress`,
  not `Done`. Two real, load-bearing findings surfaced only by tracing
  the REAL current dependency code (not each task's own sample), both
  scope-internal to the task that found them:
  1. **`T02`:** `anthropic_client.web_search` (a real, already-`Done`
     dependency) raises on any real external-API failure rather than
     returning a result dict — this task's own sample called
     `skill_registry.invoke_skill` with no `try/except`, which would let
     a genuine credential/network failure crash the whole chain, in
     tension with this task's own locked "no step fabricates a result"
     Constraint/`AC-05`. Added a `try/except` converting this into the
     honest `no_results` outcome — confirmed genuinely necessary live (a
     real, unmocked call against the real `"anthropic-claude"` Provider's
     provably-inert placeholder credential produced a real `401`,
     correctly caught).
  2. **`T03`:** `agents_router.py`'s existing `_execute_action` handler-
     calling convention (`handler()`, `len(results)`) is hardcoded to
     `run_capture_now`'s own shape and does not generalize to
     `build_knowledge`'s own async, `agent_id`-taking handler. Rather than
     modify `_execute_action` itself (relied on synchronously by
     `pending_approvals_router.py`, a file outside this task's own `##
     Files to Modify`), added a new sibling `_execute_async_action` and
     made `_invoke_action` `async def` (both its only call sites, in the
     same file, updated to `await` it). A new, generic
     `"history_recorded"` envelope flag also added to prevent the
     existing generic post-call history append from double-recording an
     outcome `knowledge_bootstrap`'s own `_record()` calls already logged
     — reusable by any future self-recording handler, not action-specific.
  **Separately, for visibility (not itself a flag-worthy trigger):** this
  build pass configured real, permanent runtime data (not code) for the
  chain to route correctly — `vault-qa` now carries real keywords
  (`["research", "web research"]`) and real `"web-research"` skill
  access, serving as this pilot's Research-Expert candidate; `vault-
  filing-expert` gained one additional real keyword (`"vault"`). Worth a
  human glance on whether `vault-qa` (originally the read-only Vault Q&A
  expert) is an acceptable long-term home for this role, or whether a
  future, purpose-built Research Expert agent should take over — see
  `SPRINT-024`'s own Retrospective, "Open follow-ups."
  **What to do:** spot-check both reconciliations above (neither weakens,
  omits, or deletes a locked AC; neither touches a file outside its own
  task's `## Files to Modify`) — confirm as sound, or direct a different
  approach. No action required to unblock further work; `SPRINT-024`
  itself is `Done` per its own deliberately-scoped Definition of Done.
  → `Implementation/UserStories/REQ-SB-36-US-02-agent-knowledge-bootstrapping-delegated-research-chain.md`
  → `Implementation/Sprints/SPRINT-024-agent-knowledge-bootstrapping-compass-expert-pilot.md`
  → `Implementation/Tasks/REQ-SB-36-US-02-T01-compass-expert-agent-and-build-knowledge-action.md`
  → `Implementation/Tasks/REQ-SB-36-US-02-T02-knowledge-bootstrap-orchestration.md`
  → `Implementation/Tasks/REQ-SB-36-US-02-T03-build-knowledge-action-dispatch.md`

- [ ] 2026-08-13 · **REQ-SB-37-US-01** · decide the custom-actions fork, then
  run `/plan-tasks` (for the superseding ADR) and `/design` (for the
  Create Agent affordance) before this story can build
  Plain English: REQ-SB-37 (Agent Creation) is a direct reversal of a
  standing decision (`ADR-011` point 2 — "agent identity/type/actions stay
  hardcoded"), operator-directed the same day it was raised. The story
  itself is written narrowly and safely, grounded in the PRD's own
  Acceptance text: a created agent gets a name/type/Section at creation,
  and its already-built Section/Provider/Keywords/Working-mode/Skill-grants
  become configurable via the exact surfaces those requirements already
  shipped. Two things are left genuinely open, not guessed: (1) whether a
  user-created agent should ever be able to define its own bespoke action —
  every existing action is backed by specific, real Python code, with no
  generic "any action" mechanism anywhere in this codebase, so this is a
  real fork (zero actions, chat/routing-only, vs. a much bigger, separate
  generic/no-code action mechanism) — this story resolves only the
  "zero actions" half for now; (2) the persisted-registry mechanism itself
  (a new sibling `.second-brain/agents.json` + module mirroring `ADR-014`'s
  Section/Provider shape, vs. some other shape) needs a superseding ADR
  over `ADR-011` point 2, since — unlike every prior agent-touching ADR
  this session — `agent_registry.list_agents()`/`get_agent()` themselves
  must start reporting user-created agents for the five already-`Done`
  property registries' own self-healing to pick them up at all; that's an
  architect-level call, not made here. Separately, no `html-prototype/`
  screen has a Create Agent affordance anywhere (Agents Map vs. Settings
  vs. both is itself left open by the PRD's own breadcrumb), so this story
  also needs a `/design` pass before `/plan-tasks` locks tasks against an
  unapproved UI shape.
  **What to do:** (1) confirm "a created agent starts with zero actions,
  reachable via chat/Hub-routing only" is acceptable for this pass, or
  direct a different scope; (2) run `/plan-tasks REQ-SB-37` so the
  architect can write the superseding ADR over `ADR-011` point 2 for the
  persisted-registry mechanism; (3) run `/design REQ-SB-37` for the Create
  Agent affordance (decide its placement — Agents Map, Settings, or both)
  before that `/plan-tasks` pass locks tasks. Full detail: `ESCALATIONS.md`
  → `ESC-020`.
  → `Implementation/UserStories/REQ-SB-37-US-01-agent-creation.md`
  → `ESCALATIONS.md`

- [x] 2026-08-13 · **Prototype update: agents-map.html (REQ-SB-38)** ·
  Approved-with-reservations 2026-08-13 — operator response "It's okay
  kinda," declined to specify what's off when asked. Proceeding to
  `/spec` with the VISIBLE_SLOT_CAP=6 threshold and per-(Section ×
  Type-ring) scope left flagged as open/tentative, not locked in — the
  analyst should keep both genuinely open rather than treating this
  sign-off as confirming them
  Plain English: `REQ-SB-38` (Agents Map Density Clustering) — the
  operator's own words, raised the same day `BUG-009`/`BUG-010` were fixed
  live: "This is a problem and will always appear as the number of Agents
  grow, we will have them on top of each other... We need to be able to
  cluster some agents together to limit the overlapping in future — a
  circle with a number and '+' so we can click on it to view the agents
  inside." A new 5th state-switcher option, "Density clustering (REQ-SB-38
  demo)", was added to `html-prototype/agents-map.html` (the existing
  "Populated"/"First run"/"5 sections"/"Dense section" states are
  UNTOUCHED). It instantiates `.map-overflow-marker` — a circular "+N"
  primitive already defined in `styles.css` since `REQ-SB-12`'s first pass
  but never actually used until now (the only existing circular "count"
  visual in this design system; `.badge` is a rectangular pill, the wrong
  shape for the operator's own literal ask) — now a real clickable button
  styled consistently with `.hub-node`/`.agent-node`'s own interactive
  conventions (dashed-accent border + glow at rest, hover-lift). A
  synthetic, clearly-marked-"(illustrative)" 15-agent dataset in the
  Technical Section (today's real ~7-agent roster never gets this dense)
  demonstrates it: the first 5 agents render as ordinary compact dots, the
  6th fan slot renders one cluster marker ("+10") instead of a 6th
  overlapping dot. Clicking the marker opens a NEW, narrower drill-down
  scoped to just its own 10 agents — the exact same click-to-zoom
  mechanic `BUG-002`'s Option D already established for Section Hubs
  (`agents-map.js`'s existing `wireDrilldown()`, only a widened selector,
  no new interaction code), applied one level deeper, matching the
  operator's own "click on it to view the agents inside." Clicking the
  Section's own Hub still shows the FULL, unclustered 15-agent drill-down
  — deliberately left dense/crowded, with an inline callout, since
  whether `layoutSectionDrilldown`'s own full-360° view also needs
  clustering is a genuinely open PRD question (open question 2), not
  resolved here.
  **Designer's own proposal, explicitly flagged for confirm/adjust, not a
  hidden assumption (PRD open question 1 — "left to /spec"):** a fixed
  `VISIBLE_SLOT_CAP = 6` agents per (Section x Type-ring) — not per
  Section as a whole, since `layoutAgents.ts` actually keys an agent's
  angle to its Section and its radius to its own Type's ring, so real
  crowding only happens when many agents of the SAME Type share one
  Section (this also directly resolves PRD open question 4: a cluster
  never mixes Types, by construction). Sized by hand-checking chord
  spacing at today's real 5-Section/57.6°-wedge geometry (the tightest
  ring, Producer, stays collision-free up to ~7 agents at that wedge
  width) — a deliberately round, slightly conservative number for a first
  pass, not the "more robust, more work" computed node-size-vs-arc-length
  check the PRD itself names as the more correct long-term alternative.
  Full rationale, including every genuinely-open PRD question left
  flagged rather than silently resolved (thresholds, drill-down-level
  clustering, live count updates): `html-prototype/agents-map.html`'s own
  top-of-file breadcrumb (2026-08-13 revision).
  **What to do:** open `html-prototype/agents-map.html` in a browser,
  click "Density clustering (REQ-SB-38 demo)" in the state-switcher, hover
  the 5 individual dots and the "+10" cluster marker in Technical's own
  fan, click the marker to see its own 10-agent drill-down, click Back,
  then click the Technical Hub itself to see the full unclustered 15-agent
  view and its inline open-question callout. Confirm or adjust the
  proposed `VISIBLE_SLOT_CAP = 6` threshold and the "cluster marker
  scoped per (Section x Type-ring), never mixing Types" resolution, and
  decide whether `layoutSectionDrilldown`'s own view needs the same
  treatment (or is out of scope for this story). Once approved, run
  `/spec REQ-SB-38`.
  → `html-prototype/agents-map.html`
  → `html-prototype/agents-map.js`
  → `html-prototype/styles.css`

- [ ] 2026-08-13 · **REQ-SB-38-US-01** · confirm the clustering threshold and
  the clustering scope granularity before `/plan-tasks` can lock precise ACs
  Plain English: `REQ-SB-38-US-01` (Agents Map Density Clustering) is drafted
  and grounded in the approved prototype's demonstrated behavior (a Section's
  overflow agents collapse into a "+N" cluster marker; clicking it shows
  exactly the clustered subset via the existing click-to-zoom mechanism; the
  Section Hub's own full drill-down stays unclustered, deliberately, as a
  named follow-up). Two numbers the prototype demonstrates are deliberately
  NOT locked into this story's Acceptance Criteria, per this file's own
  earlier entry recording the operator's lukewarm, non-specific sign-off
  ("It's okay kinda," declined to say what's off): (1) the exact clustering
  threshold — the prototype's own proposed `VISIBLE_SLOT_CAP = 6`; (2) the
  clustering scope granularity — the prototype's own proposed
  per-(Section x Type-ring) grouping. Left unresolved, the story's
  Acceptance Criteria stay written in generic "clustering threshold"/
  "same Type-ring overflow" language, and the decomposer cannot tighten them
  into locked, numeric ACs at `/plan-tasks`.
  **What to do:** confirm or adjust the proposed `VISIBLE_SLOT_CAP = 6`
  threshold and the per-(Section x Type-ring) scoping rule (or direct a
  different threshold/granularity); optionally also confirm whether
  `layoutSectionDrilldown`'s own full-360-degree view should get a follow-up
  story for the same treatment (currently out of scope here, see the
  story's own Non-Goals). Once confirmed, update the story's Context/
  Acceptance Criteria with the settled values (or direct the analyst to),
  reset nothing — the story stays `Draft` — and run `/plan-tasks REQ-SB-38`.
  → `Implementation/UserStories/REQ-SB-38-US-01-agents-map-density-clustering.md`
  → `html-prototype/agents-map.html`

- [ ] 2026-08-13 · **REQ-SB-01-US-01** · decide the re-index trigger
  mechanism before `/plan-tasks` — the actual MVP, never specced until now
  Plain English: REQ-SB-01 (Vault Indexing) and REQ-SB-02 (Browse & Search)
  are the actual MVP requirements and had no story at all — not even
  `Draft` — before this pass, despite 38+ P1 requirements already `Done`
  this session. Direct inspection confirmed no persistent index exists
  anywhere in this codebase today: every vault-query function
  (`list_all_note_paths`, `list_known_customers`, `list_known_kinds`,
  `list_known_partners`, `list_notes_in_kind_folder`) walks the filesystem
  fresh on every call, with no caching or stored structure in between, and
  no wikilink-graph (forward or backward) is computed anywhere outside
  Obsidian's own native graph view. `REQ-SB-01-US-01` specs the index
  itself: one entry per real vault note, correctly capturing frontmatter,
  tags, and outgoing/incoming wikilinks, re-runnable to reconcile
  additions/edits/deletions. What's genuinely open: the PRD's own
  Acceptance text describes WHAT a re-index run must accomplish (a full,
  honest reconciliation) but not WHEN/HOW it's triggered — an explicit
  on-demand rebuild call, a `REQ-SB-07`-style recurring schedule, or live
  filesystem watching are all equally literal readings, with real
  precedent/non-precedent differences in this codebase for each (see the
  story's own Notes and `ESCALATIONS.md` → `ESC-021`). Left unresolved,
  `/plan-tasks` cannot commit to a concrete build shape.
  **What to do:** decide the re-index trigger mechanism (recommend
  reviewing the three options named in the story's `## Notes`), and confirm
  or correct the resolved index-scope framing (real vault notes only,
  excluding `.obsidian/` and `Templates/`). Record the decision in
  `REQ-SB-01-US-01`'s own `## Notes`, flip `ESCALATIONS.md` → `ESC-021` to
  `Resolved`, reset `gate:` to `clear`, then run `/plan-tasks REQ-SB-01`.
  → `Implementation/UserStories/REQ-SB-01-US-01-vault-indexing.md`
  → `ESCALATIONS.md`

  **Update, 2026-08-13 — Resolved.** Operator's delegated "sane defaults"
  decision, relayed via the coordinating session: re-indexing is triggered
  BOTH by an explicit on-demand call/endpoint AND wired into `REQ-SB-07`'s
  existing hourly-plus-app-start scheduled capture cadence — not live
  filesystem watching (disproportionate for a personal, single-user vault).
  Reflected in the story's Context/Constraints/Non-Goals and two new
  Acceptance Criteria scenarios (8, 9). `ESCALATIONS.md` → `ESC-021`
  flipped to `Resolved`. `gate:` reset to `clear` — no other
  requirement-level open question remains (this story is backend-only, no
  UI/prototype flag applies). **Ready for `/plan-tasks REQ-SB-01`.**
  → `Implementation/UserStories/REQ-SB-01-US-01-vault-indexing.md`

- [x] 2026-08-13 · **REQ-SB-02-US-01** · Resolved — `/design REQ-SB-02` ran
  and was approved (see the "Prototype update: vault-browser.html (new),
  note-detail.html (new)" entry above); `/plan-tasks REQ-SB-02` has now run
  and opened a new, separate flagged item below for `ADR-026`
  Plain English: this entry tracked two things — (1) the missing
  `html-prototype/` screen coverage, and (2) `ESC-022`'s ranking-technique/
  wikilink-graph-shape questions. Both are now closed: `ESC-022` flipped to
  `Resolved` 2026-08-13 (BM25-style ranking, forward-link/backlink list,
  not a graph canvas); the prototype pass (`vault-browser.html`/
  `note-detail.html`) was approved 2026-08-13. `gate:` was reset to `clear`
  ahead of the `/plan-tasks REQ-SB-02` pass that follows immediately below
  as a new entry (that pass's own new ADR, `ADR-026`, reopened the flag for
  an independent reason — trigger-3, not a carryover of this one).
  → `Implementation/UserStories/REQ-SB-02-US-01-browse-and-search.md`

- [x] 2026-08-13 · **REQ-SB-02-US-01** · Approved 2026-08-13 — `ADR-026`'s
  field-weighted BM25 design is technically sound (the saturating TF
  term correctly prevents a long incidental mention from outscoring a
  real title/tag match), `rank_bm25` rejection well-argued (no native
  field-weighting), cost analysis honest, resulting 4-task breakdown
  confirmed
  Plain English: `/plan-tasks REQ-SB-02` (architect → decomposer) ran
  against the now-approved prototype (`vault-browser.html`/`note-
  detail.html`) and `REQ-SB-01-US-01`'s already-`Ready`, `ADR-024`-decided
  index shape (`vault_indexing.get_index()`). One new ADR, `ADR-026`,
  decides the one genuinely new architectural question the story's own
  resolved Constraint left open: the concrete search-ranking mechanism.
  **Field-weighted BM25-style scoring**, implemented as a small,
  self-contained pure-Python function inside a new `app/business/
  vault_search.py`, computed fresh at query time directly over
  `vault_indexing.get_index()`'s current in-memory snapshot — no new
  runtime dependency (a third-party `rank_bm25`-style library was
  considered and rejected — no native field-weighting, and not
  proportionate at the real vault's ~500-note scale), no persisted/cached
  ranking index (mirrors `ADR-024`'s own "small enough to just rescan"
  posture). Title/tags are weighted above body content, and BM25's
  saturating term-frequency component is specifically what keeps a long
  incidental body mention from outscoring a real title/tag match — this is
  what makes the approved prototype's own worked example (a note
  containing the literal query text ranks LAST, behind three notes with
  real title/tag matches) a structural guarantee, not a coincidence of
  tuning. `architecture.md` gained a new "Browse & Search" section (new
  `app/business/vault_search.py`, new `app/api/vault_search_router.py`
  (`GET /vault-search/status|notes|notes/{stem}|search`), a small additive
  `vault_indexing.py` index-readiness accessor extending — not
  reopening — `ADR-024`, and new `VaultBrowserPage.tsx`/`NoteDetailPage.tsx`
  frontend at `/browse`/`/browse/:stem`). The decomposer locked all 7 ACs
  (`AC-01`–`AC-07`, one per Gherkin scenario) and created
  `REQ-SB-02-US-01-T01`–`T04` in the same pass — story `status: Ready`.
  **What to do:** review `ADR-026` in `Implementation/Architecture/ADR.md`
  — in particular the "no new dependency, no persisted ranking index, BM25
  over a hand-rolled TF-IDF-lite" reasoning and its own Consequences
  (lexical-only relevance, revisit if the vault's real scale ever makes a
  per-query full scan noticeably slow) — approve or reject, then re-run
  `/plan-tasks REQ-SB-02` if you change it. Per pipeline rule, task
  decomposition proceeds in the same pass rather than waiting on this
  review (see the story's own `## Notes` for the architecture-scope
  boundary the tasks are held to).
  → `Implementation/UserStories/REQ-SB-02-US-01-browse-and-search.md`
  → `Implementation/Tasks/REQ-SB-02-US-01-T01-index-readiness-and-browse-query-logic.md`
  → `Implementation/Tasks/REQ-SB-02-US-01-T02-ranked-search-bm25.md`
  → `Implementation/Tasks/REQ-SB-02-US-01-T03-vault-search-router.md`
  → `Implementation/Tasks/REQ-SB-02-US-01-T04-vault-browser-frontend.md`

  **Update, 2026-08-13 (`/implement-sprint` — coder, `SPRINT-026`) —
  Done.** All 4 tasks built and every locked AC (`AC-01`–`AC-07`) verified
  live against the real, indexed vault (503 unique-stem notes) and a real
  browser, per `ADR-026` as currently written — no change requested, no
  rebuild needed. `REQ-SB-02-US-01`/`SPRINT-026` both advanced to `status:
  Done`. This closes the item.

- [x] 2026-08-13 · **SPRINT-026** · Done 2026-08-13 — retro harvested
  into `Implementation/Learnings.md`; also fixed the flagged
  `agent-panel.css` build failure directly (see its own entry below)
  harvest learnings
  Plain English: SPRINT-026 (`REQ-SB-02-US-01`, Browse & Search — tag
  filter, wikilink-graph link-list navigation, field-weighted BM25 ranked
  keyword search) is Done — all 4 tasks built and verified live against
  the real, indexed vault (Python-shell + real HTTP for the backend layers,
  a real browser via headless-Chrome-via-CDP for the frontend). All 7
  locked ACs pass, including the ranking-relevance guarantee (`AC-04`,
  proven with real, then-deleted temp notes) and genuine multi-hop
  wikilink click-through navigation. The coder drafted a Retrospective
  (patterns: the native-setter workaround for driving a React-controlled
  `<input>` from CDP, SPA-internal remount instead of `Page.reload()` to
  keep an in-page `fetch` stub alive, scoping a CDP Chrome cleanup kill to
  its own specific PID tree rather than `/IM chrome.exe`; antipattern: a
  decomposer-authored "matches nothing" example query can silently
  decompose into real words against a large, organically-grown real text
  corpus), but does not write `Implementation/Learnings.md` directly.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" and "Antipatterns
  to avoid" entries into `Implementation/Learnings.md`.
  → `Implementation/Sprints/SPRINT-026-browse-and-search.md`

- [x] 2026-08-13 · **REQ-SB-02-US-01-T02** · Approved 2026-08-13 —
  sound substitution, the task's own example string just happened to
  decompose into real English sub-words present in the real vault
  Plain English: the task's own literal AC-05 example query
  (`"qwzxjklmnop_nonexistent_token_zzz"`) does not actually produce an
  empty result against the real, ~500-note vault — its underscore-
  separated sub-tokens ("nonexistent", "token") are real English words
  that genuinely appear somewhere in real work-email bodies, and
  `search()`'s multi-term query is correctly a term-union (any one
  matching term contributes a nonzero score) — this is `search()`'s own
  correct, specified behavior per `ADR-026`, not a defect. A genuinely
  opaque single alphanumeric token
  (`zzqxvbjklmnop9999nonexistenttoken`, no underscores to decompose into
  real sub-words) was substituted for the live verification instead,
  confirming `{"results": []}` — the locked AC itself ("a query matching
  no notes returns an honest empty result") is fully satisfied; only the
  task's own illustrative example string turned out to be untestable
  as-written against this specific real vault's content.
  **What to do:** no action required unless you want the task file's own
  example query text corrected for future reference — informational
  spot-check only.
  → `Implementation/Tasks/REQ-SB-02-US-01-T02-ranked-search-bm25.md`

- [x] 2026-08-13 · **`styles/agent-panel.css`** · Fixed directly
  2026-08-13 — root cause was a literal `*/` inside the CSS comment text
  itself (`.badge-*/.btn-danger`), prematurely closing the comment block
  and leaving the rest parsed as invalid CSS. Changed to `.badge-*,
  .btn-danger`. `npm run build` now completes clean (verified)
  Plain English: while verifying `REQ-SB-02-US-01-T04`, `npm run build`
  failed with a `lightningcss` "Invalid dangling combinator in selector"
  error pointing at a comment block inside `src/frontend/src/styles/
  agent-panel.css` (built by `SPRINT-010`/`REQ-SB-13-US-01`). Confirmed via
  `git status` that this file is untracked (`??`) — never committed —
  and unrelated to any file `REQ-SB-02-US-01-T04` touches. `npx tsc
  --noEmit` is clean; this story's own live verification used the dev
  server (`npm run dev`), which is unaffected (Vite's dev-mode CSS
  pipeline doesn't run the production `lightningcss` minifier), so no
  locked AC was blocked by this.
  **What to do:** decide whether to fix the selector (likely a stray `>`/
  combinator character inside or adjacent to the flagged comment block)
  and commit `agent-panel.css`, or leave it for a dedicated small fix
  task — either way, `npm run build` should be confirmed clean before the
  next story that depends on a production build.
  → `src/frontend/src/styles/agent-panel.css`

- [ ] 2026-08-13 · **REQ-SB-03-US-01 + REQ-SB-04-US-01 + REQ-SB-05-US-01** ·
  decide Hermes reachability/`/mcp` authentication, confirm or redirect the
  proposed REQ-SB-04 scoping approach, and decide REQ-SB-05's transport
  mechanism — the real, external Hermes integration, never specced until
  now
  Plain English: REQ-SB-03 (Conversational Agent Access via Hermes),
  REQ-SB-04 (Agent Vault Write Access), and REQ-SB-05 (Content Ingestion
  Path) are Second Brain's actual integration with the real, external
  Hermes system — and had no story at all, not even `Draft`, before this
  pass. Confirmed directly (grep across `src/backend` and
  `Implementation/Architecture/` for "hermes"): no real Hermes connection,
  credential, or live round-trip exists anywhere in this codebase; every
  mention is either a docstring naming Hermes as a future consumer of
  infrastructure built for a different purpose, or `MEMORY.md`'s own
  standing "Hermes is external, not something this project builds"
  constraint. Two things were found that meaningfully narrow this
  uncertainty, though: (1) the "does Second Brain connect to Hermes as a
  client, or expose itself as a server Hermes calls into" question is
  **already architecturally settled, not open** — `ADR-015` (built for
  REQ-SB-20/25/26/27's in-app agent orchestration, a different purpose)
  adopted a shared MCP server (`app/api/mcp_server.py`, mounted at `/mcp`)
  explicitly designed to be reused identically by Hermes's own external
  orchestration, over the same endpoint the in-app agent's own loopback
  client already uses live. Second Brain is the MCP **server**; a
  Hermes-side agent would be an MCP **client**. (2) That endpoint has zero
  authentication today (direct read of `app/main.py` confirms no auth
  dependency on the `/mcp` mount; CORS is scoped to browser origins only,
  irrelevant to a server-to-server MCP client) and has never been exercised
  by anything other than the same-machine loopback client — a real,
  concrete gap before any genuinely external caller is wired to it,
  more so once REQ-SB-04 would add write-capable tools to the same server.
  Each story also carries its own further open question: REQ-SB-03 has a
  **hard, literal blocking dependency** on REQ-SB-01/REQ-SB-02 (neither
  built — the four tools already on the MCP server are narrow folder/tag
  helpers, not a search/retrieval tool over vault content, so there is
  nothing for a Hermes-side agent to actually reason over yet); REQ-SB-04
  proposes reusing REQ-SB-29's tag/folder-scope concept plus REQ-SB-21's
  Supervised/Pending-Approvals confirmation precedent, but both source
  concepts are themselves unbuilt or were designed for a different
  (in-app) surface, so this is a proposal to confirm, not a settled
  answer; REQ-SB-05's transport mechanism (a new MCP tool vs. a dedicated
  HTTP endpoint vs. whatever Hermes's own skill-wrapping convention
  dictates) is a real external-protocol unknown. Full detail:
  `ESCALATIONS.md` → `ESC-023`.
  **What to do:** (1) confirm whether a real, reachable Hermes deployment
  exists today and how Second Brain should reach/be reached by it; (2)
  decide the `/mcp` endpoint's authentication approach before any external
  client is wired to it (shared by all three stories, higher stakes for
  REQ-SB-04); (3) prioritize `REQ-SB-01`/`REQ-SB-02` — REQ-SB-03 has no real
  vault-reasoning capability to expose until they ship; (4) confirm, reject,
  or redirect REQ-SB-04's proposed scoping/confirmation approach, and
  separately resolve `REQ-SB-29-US-01`'s own still-open scope-assignment
  question if it's confirmed; (5) decide REQ-SB-05's transport mechanism and
  content-type/size policy. Record each decision in the relevant story's own
  `## Notes`, flip `ESCALATIONS.md` → `ESC-023` to `Resolved` once all are
  answered, reset each story's `gate:` to `clear`, then run `/plan-tasks` on
  each (REQ-SB-03 additionally needs REQ-SB-01/REQ-SB-02 at least `Ready`
  first).
  → `Implementation/UserStories/REQ-SB-03-US-01-conversational-agent-access-via-hermes.md`
  → `Implementation/UserStories/REQ-SB-04-US-01-agent-vault-write-access.md`
  → `Implementation/UserStories/REQ-SB-05-US-01-content-ingestion-path.md`
  → `ESCALATIONS.md`

  **Update, 2026-08-13 — Partially resolved.** The operator decided (2)
  and (4) directly, explicitly declined to decide (1), and (5) was left
  unaddressed this round:
  - **(2) `/mcp` authentication — Resolved.** Yes, real auth before any
    non-loopback caller reaches `/mcp`, minimum-viable shared-secret
    shape (a new `HERMES_MCP_SHARED_SECRET`-style config value, mirroring
    the existing `COMPASS_API_KEY` pattern) — exact scheme left to
    `/plan-tasks`. Landed as a new Scenario + Constraint on
    `REQ-SB-03-US-01`; `REQ-SB-04-US-01` inherits it at higher stakes.
  - **(4) REQ-SB-04's scoping/confirmation approach — Confirmed** as the
    accepted direction (tag/folder scope + Pending-Approvals-style
    confirmation). Real, load-bearing (not spec-blocking) dependency on
    `REQ-SB-29-US-01` shipping, recorded in `REQ-SB-04-US-01`'s own
    Notes/Dependencies.
  - **(1) Real Hermes deployment reachability — deliberately NOT
    resolved.** The operator was direct: this needs their own real-world
    knowledge, not a guess. Stays `Open` in `ESC-023`. Explicitly does
    **not** block `/spec` or `/plan-tasks` — only blocks real live
    end-to-end verification at `/implement-sprint` time.
  - **(5) REQ-SB-05's transport mechanism — untouched, still fully
    open.** Neither of the above resolves how a Hermes-side attachment
    reaches Second Brain, or whether it composes with REQ-SB-04's
    confirmation step.
  **Gate status:** `REQ-SB-03-US-01` → `gate: clear` (its remaining
  REQ-SB-01/REQ-SB-02 dependency is an ordinary sequencing fact, not a
  scope ambiguity). `REQ-SB-04-US-01` → `gate: clear` (same treatment for
  its REQ-SB-29 dependency). `REQ-SB-05-US-01` → stays `gate: flagged`,
  solely for item (5) above.
  **What to do now:** `/plan-tasks REQ-SB-04` can run immediately.
  `/plan-tasks REQ-SB-03` needs `REQ-SB-01`/`REQ-SB-02` at `Ready` first
  (in progress). `REQ-SB-05` still needs its transport-mechanism decision
  before `/plan-tasks`.

- [ ] 2026-08-13 · **REQ-SB-09-US-01** · confirm the To-Do task source and
  proposed schema before `/plan-tasks` (`ESC-024`)
  Plain English: REQ-SB-09 (To-Do Task Capture Pipeline) itself says its
  task source is "an open question for /spec time, not decided here" —
  three candidates are named (Outlook tasks, agent-created follow-ups,
  manually flagged emails), with no PRD preference among them. Direct
  code reading confirmed Outlook's own Tasks folder is technically
  reachable today (the same COM mechanism already used for mail/
  calendar), so this story proposes it as the sole source for a first
  pass, plus a Task-note schema extrapolated from the Meeting/Email
  schemas' own shape (no resolved schema exists anywhere for this
  requirement, unlike Meeting's). Both are the analyst's own
  recommendation, not a PRD-confirmed resolution. The story is otherwise
  fully drafted and buildable, including wiring My Day's already-stubbed
  To-Do drill-down (`GET /my-day/todo` currently hardcodes a 0 count,
  waiting on exactly this decision).
  **What to do:** confirm Outlook Tasks folder as the sole source (or
  redirect to include/replace it with agent-created follow-ups and/or
  manually-flagged emails), and confirm or adjust the proposed schema in
  the story's `## Context`. Record the decision in the story's `##
  Notes`, flip `ESCALATIONS.md` → `ESC-024` to `Resolved`, reset `gate:`
  to `clear`, then run `/plan-tasks REQ-SB-09`.
  → `Implementation/UserStories/REQ-SB-09-US-01-todo-notes-from-outlook-tasks-capture.md`
  → `ESCALATIONS.md`

  **Update, 2026-08-13 — Resolved.** The operator delegated this call to
  the orchestrating agent ("make the call yourself, using sane
  defaults"), which confirmed the story's own proposed default as the
  final decision: Outlook Tasks folder as the sole source, with the
  Meeting/Email-shaped schema unchanged. `ESCALATIONS.md` → `ESC-024`
  flipped to `Resolved`. `gate:` reset to `clear` — no `/design`
  dependency remains (Scenario 8's screen change reconciles against the
  already-approved `my-day-todo.html` mockup). **Ready for
  `/plan-tasks REQ-SB-09`.** This item is closed.

- [x] 2026-08-13 · **REQ-SB-11-US-01** · decide UI placement, then run
  `/design REQ-SB-11` (`ESC-025`)
  Plain English: REQ-SB-11 (Agent Activity & Error Observability) needs a
  chronological cross-agent activity log plus a per-communication-channel
  status indicator — no `html-prototype/` screen shows either today, not
  even the newly-`Done` System Health page (a related but explicitly
  different, current-snapshot-shaped surface, per that story's own
  Notes). Two equally-valid placements exist with no PRD text or
  precedent favoring one: a new top-level nav page (mirroring System
  Health's own precedent), or an added section on the System Health page
  itself. Separately (not a decision blocker, but a real scope finding):
  today's underlying `agent_communication_history.json` recording is
  confirmed incomplete for this requirement's own "success, or error
  with detail" acceptance text — meeting-capture writes no history entry
  on a successful run at all, and no capture pipeline records a failure
  outcome anywhere (an escaping exception currently vanishes untraced,
  the same "crash gap" shape already fixed for the chat path in
  `REQ-SB-31-US-01`). This fix is already scoped into the story's own
  Constraints/Implementation Tasks and does not itself need a human
  decision — only the placement question does.
  **What to do:** decide placement (new nav page vs. a System Health
  section), then run `/design REQ-SB-11` to produce the approved
  prototype. Record the decision in the story's `## Notes`, flip
  `ESCALATIONS.md` → `ESC-025` to `Resolved`, reset `gate:` to `clear`,
  then run `/plan-tasks REQ-SB-11`.
  → `Implementation/UserStories/REQ-SB-11-US-01-agent-activity-and-error-observability.md`
  → `ESCALATIONS.md`

  **Update, 2026-08-13 — Resolved (placement only; `/design` still
  needed).** The operator delegated this call to the orchestrating agent
  ("make the call yourself, using sane defaults"), which decided a **new
  top-level nav page** (not a section grafted onto System Health) —
  System Health was deliberately built as a current-snapshot status
  board with its own dedicated nav item precisely because a chronological
  log is a different shape/interaction model than a snapshot board (My
  Day's own day-navigator precedent already treats "log/history over
  time" as distinct from "status right now" in this project), and
  crowding a long-scrolling activity log into System Health's own page
  would contradict that page's designed purpose. `ESCALATIONS.md` →
  `ESC-025` flipped to `Resolved`. `gate:` reset to `clear` — the
  story's own open questions are resolved. **`/design REQ-SB-11` still
  needs to run** (genuinely net-new UI, no prototype exists for the new
  nav page yet) before `/plan-tasks REQ-SB-11` — a sequencing dependency,
  not a further gate, per the same reasoning `REQ-SB-31-US-01` used for
  its own identical situation.

  **Update, 2026-08-13 — Closed.** `/design REQ-SB-11` ran and was
  approved (see the entry below), then `/plan-tasks REQ-SB-11` ran: no
  new ADR (architect pass), 7 ACs locked and 4 tasks created (decomposer
  pass) — `status: Ready`, `gate: clear`. This item is closed.

- [x] 2026-08-13 · **Prototype update: agent-activity.html (new)** ·
  Approved 2026-08-13 — verified live: both state-switcher groups toggle
  correctly (empty state shows honest "No agent activity recorded yet";
  unreachable state shows the real Outlook COM error detail), nav item
  confirmed wired on system-health.html and others. Zero new CSS,
  reuses `.log-list`/`.log-item` as intended. `/plan-tasks REQ-SB-11` is
  the next step.
  Plain English: designed for `REQ-SB-11` (Agent Activity & Error
  Observability) — placement was already resolved (new top-level nav
  page, see the entry above); this pass produces the actual prototype.
  New `html-prototype/agent-activity.html` shows (1) a chronological,
  cross-agent activity log — every completed background capture run
  (Email Capture, Meeting Capture), newest first, each with its own
  outcome (success, or failure with an honest error detail visible
  inline, never silently dropped) — demonstrating that every configured
  capture agent's runs appear, not only some of them; (2) a current
  status indicator for the Outlook communication channel, reported
  honestly as direct COM reachability (not "Hermes-wrapped" — no live
  Hermes connection exists in this codebase yet, per the story's own
  Context/`ESC-023`); (3) an honest empty state ("No agent activity
  recorded yet") and a populated state mixing successes with one real
  failure entry. Two independent `.state-switcher` groups demonstrate all
  7 scenarios: "Activity recorded" vs. "No runs yet" (Scenarios 1, 2, 3,
  6), and "Outlook reachable" vs. "Outlook unreachable" (Scenarios 4, 5).
  Scenario 7 (fresh, not cached, on reopen) is a text note next to a
  Refresh affordance, matching System Health's own identical treatment.
  Key design decisions: reused `.log-list`/`.log-item`/`.log-item-meta`
  verbatim — the exact primitive `styles.css`'s own comment already
  earmarked for "background-run activity," already live on Agents Map's
  per-agent Communication History panel; this page is its first
  cross-agent use. A failed entry's error detail is a plain muted line
  stacked inside the same `.log-item`'s left-hand slot (existing
  `.text-muted` utility + a line break) — composition of existing
  classes, not a new CSS pattern. The Outlook-channel card reuses System
  Health's own `.kv-list`/`.badge-success`/`.badge-danger` shape verbatim.
  Zero new CSS. Example data is grounded in real code: the email-capture
  success string is copied verbatim from
  `email_classification.py::run_capture_and_record_completion`; the
  failure detail is copied verbatim from
  `outlook_com.py::_connect_namespace`'s real `OutlookUnavailable`
  message. The new `.nav-item` (Agent Activity) was added to the shared
  sidebar on every prototype page (index.html, agents-map.html,
  agents-map-exploration.html, my-day.html + its 4 drill-downs +
  my-day-approvals.html, settings.html, system-health.html), matching
  System Health's own precedent, plus a new catalog card on `index.html`.
  This page deliberately does not repeat System Health's own MCP-mount,
  Provider-availability, or last-capture-run checks — see its own header
  comment.
  **What to do:** open `html-prototype/agent-activity.html` in a browser
  (try both state-switcher groups) and confirm the new sidebar nav item
  appears consistently across every other prototype page. Once approved,
  reset `REQ-SB-11-US-01`'s `gate:`/status as needed and run
  `/plan-tasks REQ-SB-11`.
  → `html-prototype/agent-activity.html`
  → `html-prototype/index.html`
  → `Implementation/UserStories/REQ-SB-11-US-01-agent-activity-and-error-observability.md`

- [x] 2026-08-13 · **REQ-SB-01-US-01** · Approved 2026-08-13 — `ADR-024`'s
  in-memory/full-rebuild-swap design is sound, honestly argued
  (persistence/SQLite/incremental-diff alternatives all correctly
  rejected as disproportionate at real ~500-note scale), and the folded-in
  `_parse_frontmatter_value` list-round-trip fix is a real, valuable
  correction
  Plain English: `REQ-SB-01-US-01` (Vault Indexing) is the first story in
  this codebase to need a real, persistent, re-runnable index of the
  vault's notes — every existing vault-query primitive
  (`vault_writer.py`/`vault_query_tools.py`) is stateless pass-through I/O,
  re-scanning the filesystem fresh on every call, with no wikilink graph
  anywhere. A new ADR, `ADR-024`, decides the storage/rebuild shape: an
  **in-memory-only, module-level singleton** (`app/business/
  vault_indexing.py`), rebuilt wholesale (never incrementally diffed) and
  atomically swapped in on every trigger — both the new on-demand
  `POST /vault-index/rebuild` endpoint and the existing `REQ-SB-07`
  hourly/app-start scheduler tick (one new unconditional call inside
  `email_classification.run_capture_and_record_completion`, zero changes
  to `capture_scheduler.py` itself). Deliberately **no** `.second-brain/`
  JSON persistence file (redundant given the app-start trigger already
  guarantees a rebuild on every process start) and **no** database/SQLite
  (disproportionate — no query/filter surface exists yet to justify it;
  that's `REQ-SB-02`'s job). Also folds in a same-shape fix to a real,
  pre-existing gap in `vault_writer.read_note()` (frontmatter list values,
  e.g. `tags`, never parsed back into a real Python list — mirrors the
  boolean-value fix `REQ-SB-30-US-01` already shipped) and a
  case-insensitive filename-stem wikilink-resolution rule. Full reasoning
  and every alternative considered: `Implementation/Architecture/ADR.md` →
  ADR-024.
  **What to do:** review `ADR-024` in
  `Implementation/Architecture/ADR.md` — in particular the in-memory-vs-
  persisted-vs-SQLite call and its own Consequences (index is transient,
  lost on restart until the next trigger fires; revisit if the vault's
  scale ever makes a full rebuild noticeably slow) — approve or reject,
  then run `/plan-tasks` again if you change it. Per pipeline rule, task
  decomposition proceeds in the same pass rather than waiting on this
  review (see the story's own `## Notes` for the architecture-scope
  boundary the tasks are held to).
  → `Implementation/UserStories/REQ-SB-01-US-01-vault-indexing.md`

- [x] 2026-08-13 · **Prototype update: vault-browser.html (new),
  note-detail.html (new)** · Approved 2026-08-13 — verified live: ranked
  search concretely demonstrates relevance-over-substring (result #4
  explains its own last-place rank despite a literal text match), tag
  browse/pagination correct, click-through wikilink navigation confirmed
  working (Masdar hub note's active panel correctly shows real backlinks
  from both linking notes plus an honest "no outgoing links" empty
  state). `/plan-tasks REQ-SB-02` is next, once REQ-SB-01 reaches Ready
  Plain English: designed for `REQ-SB-02-US-01` (Browse & Search) — the
  story's own flagged reason (`net-new-design-needed`) is exactly this: no
  `html-prototype/` screen covered a notes browser/search UI before this
  pass. Two new pages, reached from a new "Browse & Search" nav item
  (placement mirrors System Health/Agent Activity's own precedent):
  (1) `vault-browser.html` — list/browse all indexed notes (Scenario 1,
  grounded in the real vault's own 496-note breakdown from
  `REQ-SB-01-US-01`'s direct inspection: 204 Email, 134 Person, 51
  Meeting, 6 Customer, 1 Partner), filter by tag with real matches
  (Scenario 2) and a genuine zero-match tag (Scenario 6), and a ranked
  keyword/full-text search (Scenario 4 — the example results include a
  note that ranks LAST despite literally containing the query text as an
  incidental body substring, directly demonstrating relevance-over-
  substring rather than just asserting it) plus an honest no-match search
  state (Scenario 5). A top-level state-switcher demonstrates the vault-
  not-indexed-yet honest state (Scenario 7), visibly distinct from
  "indexed, but zero matches." (2) `note-detail.html` — a note's forward
  links and backlinks as a real, clickable LIST (Scenario 3) — explicitly
  NOT a visual/interactive graph canvas (resolved out of scope this pass,
  `ESC-022`, `Resolved` 2026-08-13; matches `ADR-011`'s "proportionate
  first" precedent). A small, closed, three-note demo graph (an Email, a
  Customer hub, and a Meeting note, all tagged `customer/masdar` — the
  story's own example tag) makes every forward-link/backlink row a real,
  working click, including two honest empty-list edge cases (a hub note
  with no outgoing links; an Email/Meeting note with no incoming links)
  grounded in `REQ-SB-01-US-01` Scenario 6's "empty list, not an error"
  index behavior. Two small additive CSS primitives were added to
  `styles.css` (documented there, composed entirely from existing
  tokens): `a.item-row`/`button.item-row` (a real clickable variant of
  the existing plain-`<div>` `.item-row`, used so every note row and
  every forward-link/backlink row is genuinely interactive in a browser,
  per `SCREEN_INSTRUCTIONS.md`) and `.tag-chip` (a pill-shaped clickable
  tag button reusing the existing `.state-switcher` click delegation in
  `app.js` — the tag filter needed zero new JS). `note-detail.html` also
  carries one small page-scoped inline script (not added to the shared
  `app.js`) that honors a `#hash` deep link from `vault-browser.html`'s
  note rows so arriving from a specific note opens on that note's own
  state. The new "Browse & Search" `.nav-item` was added to the shared
  sidebar on every existing prototype page (index.html, agents-map.html,
  agents-map-exploration.html, my-day.html + its 4 drill-downs +
  my-day-approvals.html, settings.html, system-health.html,
  agent-activity.html), matching System Health/Agent Activity's own
  rollout precedent, plus a new catalog card on `index.html`.
  **What to do:** open `html-prototype/vault-browser.html` in a browser —
  try all three state-switcher groups (vault-index-state, search-results,
  browse-tags/tag chips) — then click through to
  `html-prototype/note-detail.html` from a few different note rows and
  confirm the forward-link/backlink rows genuinely navigate between the
  three demo notes (including the two empty-list states). Confirm the new
  sidebar nav item appears consistently across every other prototype
  page. Once approved, reset `REQ-SB-02-US-01`'s `gate:` to `clear` and
  run `/plan-tasks REQ-SB-02` — after first confirming
  `REQ-SB-01-US-01` has reached `Ready` (this story's index is the data
  this UI reads from).
  → `html-prototype/vault-browser.html`
  → `html-prototype/note-detail.html`
  → `html-prototype/index.html`
  → `html-prototype/styles.css`
  → `Implementation/UserStories/REQ-SB-02-US-01-browse-and-search.md`

- [x] 2026-08-13 · **REQ-SB-04-US-01** · Approved 2026-08-13 —
  `ADR-025` is excellent, security-conscious work: ASGI middleware
  correctly chosen over `Depends()` (which can't attach to a raw ASGI
  mount), fail-closed scope seam is the right call over fail-open, and
  the unconditional working-mode bypass is well-justified (Hermes access
  is explicitly a bigger trust surface than in-app actions). `T03`'s
  per-task-blocking split confirmed acceptable, matching `ESC-018`'s
  precedent
  Plain English: `REQ-SB-04-US-01` (Agent Vault Write Access) is the first
  story to put any authentication on `/mcp` and the first to register a
  write-capable tool on the shared MCP server. One new ADR, `ADR-025`,
  decides: (1) `/mcp` authentication — a small ASGI middleware
  (`app/api/mcp_auth.py`) wrapping only the `/mcp` mount, loopback callers
  (Second Brain's own in-app agent) pass through unchecked, any other
  caller needs a matching `X-Hermes-Shared-Secret` header (new
  `Settings.hermes_mcp_shared_secret`, mirroring `COMPASS_API_KEY`) — this
  mechanism is shared with `REQ-SB-03-US-01`'s own still-unbuilt
  Constraint, so that story's own future `/plan-tasks` pass should
  reference this ADR rather than rebuild it; (2) the new write-capable
  tool (`propose_vault_write`, new `app/business/vault_write_tools.py`)
  **never writes directly** — it always creates a Pending Approval via a
  new `trigger="hermes"` value, dispatched through `ADR-021`'s own Tier-2
  `_APPROVAL_HANDLERS` precedent, and **this confirmation step is
  unconditional — it never consults `working_mode_registry`, regardless
  of the target agent's own working mode** (extends `ADR-021` point 5's
  own "bypasses the working-mode gate by construction" precedent to a
  second, independent case — worth a deliberate look, since it is a real
  divergence from `ADR-020`'s own agent-working-mode-conditional gate for
  every other in-app action); (3) the write safety envelope reuses
  `vault_writer.write_note`'s existing unconditional-overwrite semantics
  as-is (no new collision-avoidance/merge primitive); (4) scope
  enforcement is a **fail-closed seam**
  (`_is_within_assigned_scope` returns `False` unconditionally) until
  `REQ-SB-29-US-01` ships a real scope registry — never fail-open.
  Separately, the decomposer step confirmed `REQ-SB-29-US-01` is still
  `status: Draft`, never decomposed (zero task files) — mirroring
  `ESC-011`'s/`ESC-018`'s own precedent, and the operator's own
  2026-08-12 confirmation that per-task blocking is the correct
  going-forward default, the story advances to `status: Ready` with only
  `REQ-SB-04-US-01-T03` (the real scope-match implementation, holding
  `AC-01`/`AC-02`) individually held at `status: Draft`/`gate: flagged`;
  `T01` (`/mcp` auth) and `T02` (the propose→pending→approve/decline
  plumbing, verified independently of the scope gate via a direct
  `pending_approval_registry` seed) are `Ready` and buildable now. New
  `ESCALATIONS.md` → `ESC-026` records the finding.
  **What to do:** (1) review `ADR-025` in
  `Implementation/Architecture/ADR.md` — in particular the unconditional
  working-mode bypass (point 4) and the fail-closed scope seam (point 6)
  — approve or reject, then run `/plan-tasks` again if you change it; (2)
  confirm — or override — the per-task-blocking judgement call on `T03`
  (already precedented at `ESC-018`, below); (3) once `REQ-SB-29-US-01` is
  eventually decomposed, run a follow-up decomposer pass to replace
  `REQ-SB-04-US-01-T03`'s own `depends_on: []` with the real task id.
  → `Implementation/UserStories/REQ-SB-04-US-01-agent-vault-write-access.md`
  → `Implementation/Tasks/REQ-SB-04-US-01-T01-mcp-shared-secret-authentication.md`
  → `Implementation/Tasks/REQ-SB-04-US-01-T02-hermes-write-tool-and-pending-approval-plumbing.md`
  → `Implementation/Tasks/REQ-SB-04-US-01-T03-scope-enforcement.md`
  → `ESCALATIONS.md`

- [x] 2026-08-13 · **REQ-SB-09-US-01** · Approved 2026-08-13 — `ADR-027`
  correctly applies the project's own hard-won Meeting-dedup lesson
  (`ADR-008`→`013`→`019`): `EntryID` used as a self-owned lookup-index
  key, not a global-uniqueness claim, with a sound structural argument
  for why Tasks differ from Calendar (no occurrence-expansion). The
  unverified-empirical-claim disclosure and the coder-assigned live
  verification requirement are exactly right — confirm the decomposer's
  task breakdown carries that requirement explicitly
  Plain English: `REQ-SB-09-US-01` (To-Do Task Capture Pipeline) is the
  third capture pipeline after Email and Meetings, and the third pipeline
  in a row to need its own architect-level dedup-key decision. `ADR-027`
  decides: (1) a new `list_outlook_tasks` Tasks-folder COM-read function
  (same channel `outlook_com.py` already uses for mail/calendar, no new
  external dependency); (2) the dedup/top-up mechanism — a real, load-
  bearing divergence from Meeting's own dedup key (`ADR-019`): Meeting
  recomputes its filename fresh from Outlook's current `start` field on
  every run, but a Task's own `due` field can legitimately change between
  captures (Scenario 6 requires that survive as a top-up, not a new
  duplicate note) — so Task notes use a new load-bearing
  `.second-brain/task_note_index.json` (`EntryID` → note filename, looked
  up first, never recomputed from current fields) instead; (3) a new
  customer-only `compass_client.classify_task`, not a reuse of
  `classify_email`; (4) the third gated block riding `REQ-SB-07`'s
  existing hourly job with zero scheduler changes, and a resolution of
  `ADR-008`'s own explicitly-anticipated "revisit if a third pipeline
  makes the email-scoped module name misleading" fork — decided **not**
  to extract a new orchestration module this pass.
  **Honestly disclosed, worth a human look specifically:** the `EntryID`-
  stability reasoning behind point (2) is structural (Outlook's Tasks
  folder has no `IncludeRecurrences`-equivalent expansion mechanism, so
  the specific defect that broke `EntryID`/`GlobalAppointmentID` for
  Calendar twice — `ESC-002`, `ESC-012` — cannot apply to Tasks the same
  way), **not empirically live-verified against the real mailbox this
  pass** — the architect role has no live-Outlook/code-execution
  capability in this environment. A real live-verification step is
  explicitly assigned to the coder building `T01`/`T02` as part of that
  task's own Definition of Done; a live collision or instability finding,
  if any, is grounds for a superseding ADR, not a silent workaround.
  **What to do:** review `ADR-027` in
  `Implementation/Architecture/ADR.md` — in particular the dedup-key
  divergence from Meeting's own `ADR-019` mechanism (point 3) and the
  disclosed-but-unverified `EntryID`-stability reasoning (Consequences) —
  approve or reject, then run `/plan-tasks` again if you change it. The
  story's own `## Notes` carries the full architecture-scope section list
  the decomposer/coder are bounded by.
  **Decomposer confirmation (2026-08-13):** the requested live-verification
  requirement is carried explicitly, not just code-review-level —
  `REQ-SB-09-US-01-T01`'s own `## Tests` has an isolated live `EntryID`-
  stability check (read → edit due date in the real Outlook desktop client
  → re-read → confirm the same `EntryID`), and `REQ-SB-09-US-01-T03`'s own
  `## Tests`, tagged `AC-06`, has the full end-to-end live confirmation
  (capture → edit due date/status in Outlook → rerun → confirm the same
  note tops up, not a duplicate). Story advanced `Draft` → `Ready` (8/8 ACs
  locked, `depends_on` acyclic across 6 new tasks); `gate` left `flagged`
  by the decomposer, not cleared — still awaiting the human review above.
  → `Implementation/UserStories/REQ-SB-09-US-01-todo-notes-from-outlook-tasks-capture.md`
  → `Implementation/Tasks/REQ-SB-09-US-01-T01-outlook-tasks-read-primitive.md`

  **Coder confirmation (2026-08-13) — `EntryID`-stability EMPIRICALLY
  CONFIRMED, live, against the real mailbox.** `T01`'s own isolated check
  (read → edit a real Task's due date via a real COM `Save()` against the
  live Outlook session, the closest available real substitute for a
  desktop-client edit in this tool-only environment → re-read →
  byte-for-byte identical `EntryID`) and `T03`'s own end-to-end `AC-06`
  check (capture → edit a real task's due date AND status in Outlook →
  rerun → same note topped up, `created: false`, `outlook_entry_id`
  unchanged) both PASSED. Additionally confirmed across the full real
  Tasks folder (235 items, 100 processed by the real `AC-04` app-start
  capture run): zero duplicate `EntryID`s found anywhere. `ADR-027`
  point 3's own load-bearing safety claim is now empirically verified,
  not merely structurally reasoned — no superseding ADR needed.
  **One real, disclosed, non-blocking finding from this same live
  verification pass, unrelated to `EntryID` stability:** a pre-existing,
  already-tracked defect (`BUG-011`) is confirmed to also affect Task
  notes, with a worse consequence (same-subfolder literal note
  overwrite, not just index-invisibility) — see `ESCALATIONS.md` →
  `ESC-028` and the new review-queue entry below for the full write-up.
  All 8 locked ACs (`AC-01`–`AC-08`) verified live end-to-end against the
  real Outlook mailbox, real Compass, and the real vault; `REQ-SB-09-US-01`
  and all 6 tasks now `Done`. This item is closed.
  → `Implementation/Tasks/REQ-SB-09-US-01-T03-todo-classification-orchestration.md`

- [x] 2026-08-13 · **ESC-027** · Captured as `BUG-011` in `BUGS.md`
  2026-08-13 — real, live filename-stem collision between two distinct
  real notes silently drops one from `vault_indexing`'s index
  Plain English: while completing `REQ-SB-01-US-01-T02`'s own mandated
  live `AC-01` verification, the real vault's true note count (503) and
  the rebuilt index's entry count (502) genuinely disagreed. Root cause:
  `Work/Emails/2026-07-30-RE- [ Core42 @UAE ] SimplAI Agentic AI Operating
  System - Demo (deep .md` and `Work/Notifications/2026-07-30-RE- [
  Core42 @UAE ] SimplAI Agentic AI Operating System - Demo (deep .md` are
  two genuinely distinct, correctly-captured real items (a real email vs.
  a Google Calendar notification, different `outlook_entry_id`/sender/
  `conversation_id`) that share one subject line long enough that
  `vault_writer._slugify`'s 80-character truncation silently eats
  `email_classification.classify_recent_emails`'s own trailing
  disambiguating `-{entry_id[-8:]}` suffix — so both files exist intact on
  disk, in different kind-folders, but share an identical filename stem,
  the exact identity `ADR-024` keys the new vault index by. `T02`'s own
  `rebuild_index()` is built exactly per `ADR-024` (verified correct
  against every one of the vault's 502 unique-stem notes); this is a real,
  pre-existing gap in `_slugify`/`email_classification.py` (both
  already-`Done`, out of `T02`'s own file scope), not a defect in the new
  indexing code. Full detail: `ESCALATIONS.md` → `ESC-027`.
  **What to do:** run `/bug` to formally capture this as a `BUG-NNN` (Area:
  Logic) so it can be batched into a `BUGFIX-NN-US-01` fix story — the
  underlying fix most likely belongs in
  `email_classification.classify_recent_emails`'s own stem-construction
  (compute/hash the disambiguator before any truncation, mirroring
  `meeting_note_filename_stem`'s own already-correct "hash before
  truncate" precedent) or in `_slugify` itself (never truncate away a
  caller-supplied disambiguating suffix). `REQ-SB-02-US-01` (Browse &
  Search, built directly on `vault_indexing.get_index()`) should also be
  made aware this exists.
  → `ESCALATIONS.md`
  → `Implementation/Tasks/REQ-SB-01-US-01-T02-core-index-build-rebuild-backlinks.md`

- [x] 2026-08-13 · **SPRINT-025** · Done 2026-08-13 — retro harvested
  into `Implementation/Learnings.md`; `ESC-027` captured as `BUG-011`
  Plain English: SPRINT-025 (`REQ-SB-01-US-01`, Vault Indexing — the
  project's first-ever real, persistent, re-runnable index) is Done — all
  4 tasks built and verified live against the real vault (and, for `T04`,
  a real live Outlook/Compass capture run). All 9 locked ACs pass,
  including `AC-01` with one disclosed, escalated, non-blocking exception
  (a real, pre-existing filename-stem collision between two distinct real
  notes — see the `ESC-027` entry above). Two disclosed verification-
  method deviations (`T03`'s `TestClient`-without-lifespan,
  `T04`'s direct `asyncio.run(capture_scheduler.run_capture_if_idle())`)
  both worked around `BUGS.md` → `BUG-008`'s already-known real app-start
  hang while still exercising the real code path each AC needed. The
  coder drafted a Retrospective (patterns: closest-to-real HTTP/trigger
  substitutes instead of the weakest possible stand-in when a known issue
  blocks the literal verification step, isolating a known issue's actual
  named cause before assuming it explains a new hang, root-causing an
  exact-match AC failure fully before treating it as either a build
  defect or an escalation-worthy environmental finding; no new
  antipatterns — this sprint actively avoided the two already-documented
  ones, blanket process kills and trusting stale task code samples), but
  does not write `Implementation/Learnings.md` directly.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" entries into
  `Implementation/Learnings.md`. Separately: review `ESC-027` (real
  filename-stem collision) and consider a `/bug` capture — `SPRINT-026`
  (Browse & Search), built directly on `vault_indexing.get_index()`,
  should be aware of it before that sprint starts. `BUGS.md` → `BUG-008`
  (pre-existing) has now cost workaround time in two independent sprints
  (`SPRINT-023`, `SPRINT-025`) — worth reprioritizing.
  → `Implementation/Sprints/SPRINT-025-vault-indexing.md`
  → `ESCALATIONS.md` (ESC-027)
  → `BUGS.md` (BUG-008)

- [x] 2026-08-13 · **SPRINT-029** · Approved 2026-08-13 — both
  scope-internal judgement calls sound (gitignored `.env` dev value,
  `httpx_client_factory` verification technique); retro harvested below.
  Note for later: rotate the dev `HERMES_MCP_SHARED_SECRET` before any
  real Hermes integration attempt — not urgent while nothing external
  is connected
  Plain English: `SPRINT-029`'s two buildable tasks
  (`REQ-SB-04-US-01-T01`/`T02` — `/mcp` shared-secret authentication and
  the write-capable `propose_vault_write` MCP tool + Pending Approvals
  plumbing) are both `Done`, built exactly per `ADR-025`, no deviation.
  `T01`'s 4 non-AC smoke checks and `T02`'s locked `AC-03`/`AC-04` all
  verified live against the real backend, vault, and Pending Approvals
  surface — see each task's own Implementation Log for the full
  transcript. A real, simulated-non-loopback-caller technique
  (`httpx.ASGITransport(client=...)`) proved the auth middleware's 401
  rejection and successful pass-through end to end; a real loopback MCP
  tool call against the actual live `propose_vault_write` front door
  independently confirmed the fail-closed scope seam honestly rejects
  every real invocation today (`{"status": "rejected", ...}`, never
  fabricated as `"pending"`) — this is Scenario 2's own shape, not a real
  scope decision, and is correctly not tagged `AC-01`/`AC-02`.
  `REQ-SB-04-US-01-T03`/`AC-01`/`AC-02` remain `Draft`/blocked on
  `REQ-SB-29-US-01`'s own decomposition (`ESC-026`, still `Open`,
  unchanged this pass) — the story itself stays `status: In Progress`,
  not `Done`, the same shape `SPRINT-024`/`REQ-SB-36-US-02` already
  established for an identically-blocked composition with this same
  dependency. `SPRINT-029` itself reaches `Done` per its own
  deliberately-scoped Definition of Done (which does not require
  `T03`/`AC-01`/`AC-02`). Two scope-internal judgement calls logged in
  `T01`'s own Implementation Log (a real dev value added to the real,
  gitignored `.env` so the app could boot; the `mcp` SDK's own
  `httpx_client_factory` hook used to drive a genuine MCP session over
  the simulated non-loopback transport) — neither weakens a locked AC,
  neither touches a file outside `T01`'s own `## Files to Modify` (`.env`
  is gitignored, untracked local config, same class of file
  `REQ-SB-36-US-01-T01` already touched for the identical reason).
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" entries into
  `Implementation/Learnings.md`. Separately: spot-check the two
  scope-internal judgement calls above; review whether the real
  `HERMES_MCP_SHARED_SECRET` dev value now in `.env` is acceptable to
  keep or should be rotated before any real Hermes integration attempt.
  No action required to unblock further work.
  → `Implementation/UserStories/REQ-SB-04-US-01-agent-vault-write-access.md`
  → `Implementation/Sprints/SPRINT-029-agent-vault-write-access.md`
  → `Implementation/Tasks/REQ-SB-04-US-01-T01-mcp-shared-secret-authentication.md`
  → `Implementation/Tasks/REQ-SB-04-US-01-T02-hermes-write-tool-and-pending-approval-plumbing.md`
  → `ESCALATIONS.md` (ESC-026, unchanged, still Open)

- [x] 2026-08-13 · **SPRINT-027** · Approved 2026-08-13 (entry added
  retroactively — the coder's own pass marked the sprint `gate: flagged`
  but omitted the mandatory pointer here; caught and filed directly)
  Plain English: `SPRINT-027` (`REQ-SB-11-US-01`, Agent Activity & Error
  Observability) is `Done` — all 4 tasks built and all 7 locked ACs
  verified live against the real backend/vault/Outlook, including a real
  induced failure (in-process monkeypatch) and a real honest-empty state.
  A genuine live finding along the way: physically closing Outlook does
  **not** keep it unreachable on this machine — Windows COM silently
  auto-relaunches it via `Dispatch()` — so AC-05 (Outlook unreachable)
  was verified via a temporary, port-identical, immediately-reverted
  backend swap instead, screenshot-confirmed, then reverted. Recorded as
  a new Constraint in `MEMORY.md`. Two scope-internal judgment calls,
  both approved: (1) `T01` kept `vault_indexing.rebuild_index()`
  unconditional and placed ahead of the new gating, preserving
  `SPRINT-025`'s own "indexing is core plumbing" intent exactly; (2)
  `T02` added `CoUninitialize()` to the new `check_reachable()`, matching
  every other real Outlook COM function in that file's own existing
  try/finally convention (an omission would have leaked COM apartment
  state on repeated calls). Screenshots were captured via the OS-
  installed Edge browser's own headless mode (no CDP/visual-harness tool
  available in that pass) — a real browser engine, not a mock, disclosed
  as the substitute used.
  **What to do:** read `## Retrospective` in the sprint file for the full
  write-up (already harvested into `Implementation/Learnings.md` as part
  of this same review pass).
  → `Implementation/Sprints/SPRINT-027-agent-activity-and-error-observability.md`
  → `Implementation/Tasks/REQ-SB-11-US-01-T01-capture-pipeline-honest-failure-recording.md`
  → `Implementation/Tasks/REQ-SB-11-US-01-T02-agent-activity-aggregation-module.md`
  → `MEMORY.md` (Outlook COM auto-relaunch Constraint)

- [x] 2026-08-13 · **ESC-028** · Actioned 2026-08-13 — `BUG-011`
  extended in `BUGS.md` with the Task-note content-loss finding,
  severity raised Major → Blocker (real data loss, not just
  index-invisibility; a live 18-entry gap exists in the real
  `task_note_index.json` today). `BUG-011`'s own `_slugify` 80-char
  truncation defect confirmed to also affect Task notes — with a worse,
  real content-loss consequence than its own documented Email/
  Notification case
  Plain English: while completing `REQ-SB-09-US-01-T03`'s own mandated
  live `AC-07` verification (two same-subject Outlook Tasks must produce
  two distinct notes), the real, unbounded scheduled capture (100 real
  Outlook Tasks, `T04`'s own `AC-04` app-start trigger) surfaced three
  genuinely distinct real Outlook Task items sharing one 72-character
  subject. `vault_writer.task_note_filename_stem` correctly built three
  distinct 92-character stems (confirmed via `task_note_index.json`,
  which correctly recorded all three separately), but the same
  pre-existing `_slugify` 80-char truncation `BUG-011` already tracks
  collapsed all three onto one identical 80-character filename — since
  Task notes share one flat `Work/Tasks/` subfolder (no `kind` split),
  this caused a literal file OVERWRITE (only the last of the three
  writes survives on disk), not just the index-invisibility `BUG-011`'s
  own Email/Notification case produced (those landed in different
  kind-subfolders, so both files survived intact). The disambiguation
  mechanism `T02`/`T03` built is independently confirmed CORRECT — a
  controlled real short-subject pair, and real production data under the
  80-char budget (three distinct `"ADNOC Account Plan Review..."` real
  tasks), both correctly produced distinct, non-colliding notes; the
  defect is entirely inside the pre-existing, out-of-scope `_slugify`
  function. Full detail: `ESCALATIONS.md` → `ESC-028`.
  **What to do:** extend `BUG-011`'s own `BUGS.md` entry (not a new bug —
  same root cause, same fix) to name Task notes as a second confirmed-
  affected note type and record the worse "same-subfolder literal
  overwrite" severity finding (worth a `Severity` re-review — Task notes
  have no `kind`-subfolder split at all, so every collision there is a
  same-path overwrite, not a near-miss). The real vault's own
  `.second-brain/task_note_index.json` still carries the exposure today
  (100 entries vs. 82 real files under `Work/Tasks/`, an 18-entry gap
  from this same truncation). No action required to unblock
  `REQ-SB-09-US-01` itself — `AC-07` is verified via the mechanism's own
  correctness, matching `ESC-027`'s own established non-blocking
  precedent.
  → `Implementation/UserStories/REQ-SB-09-US-01-todo-notes-from-outlook-tasks-capture.md`
  → `Implementation/Tasks/REQ-SB-09-US-01-T03-todo-classification-orchestration.md`
  → `ESCALATIONS.md` (ESC-028)
  → `BUGS.md` (BUG-011)

- [x] 2026-08-13 · **SPRINT-028** · Done 2026-08-13 — retro harvested
  into `Implementation/Learnings.md`; `ESC-028`/`BUG-011` actioned above
  Plain English: `SPRINT-028` (`REQ-SB-09-US-01`, To-Do Task Capture
  Pipeline) is `Done`, built exactly per `ADR-027`, no deviation. Full
  verification detail is in each task's own Implementation Log and the
  story's own "Coder pass" Notes section; headline results: the
  `EntryID`-stability claim `ADR-027` itself could not empirically
  verify is now confirmed live (no superseding ADR needed); all 8 locked
  ACs verified against the real Outlook mailbox, real Compass, and the
  real vault, including a real app-start scheduler trigger, a real
  induced-failure/independent-branch-funnel/recovery cycle, and a real
  screenshot-verified populated To-Do drill-down with both badge states.
  One real, disclosed, non-blocking finding along the way — see the
  `ESC-028` entry directly above.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward"/"Antipatterns
  to avoid" entries into `Implementation/Learnings.md`. Separately:
  action the `ESC-028` item above (extend `BUG-011`, consider a
  `/triage` pass). No action required to unblock further work — nothing
  else depends on this sprint's own completion.
  → `Implementation/Sprints/SPRINT-028-todo-notes-from-outlook-tasks-capture.md`
  → `Implementation/UserStories/REQ-SB-09-US-01-todo-notes-from-outlook-tasks-capture.md`
