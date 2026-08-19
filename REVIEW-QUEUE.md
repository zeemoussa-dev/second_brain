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

- [ ] 2026-08-17 · **REQ-SB-69-US-01** · review `ADR-046` (decoupled Email
  Pull + human-readable Thread notes) before tasks are locked
  Plain English: following tonight's second real Outlook-COM hang, the
  architect pass wrote `ADR-046`, which retires `Fetch` from the email
  capture graph's pre-graph batch step and replaces it with two
  independently-dispatched capabilities of the existing
  `email-capture-pipeline` Agent — `pull_email` (still Outlook-COM,
  still under the shared dispatch lock, now writing incrementally to a
  new `.second-brain/email_staging/` store) and `process_staged_email`
  (Outlook-free, deliberately never sharing that lock, so a stalled Pull
  can no longer block already-staged mail and vice versa). It also makes
  Thread note filenames human-readable/collision-safe (a frontmatter-scan
  lookup replaces the old deterministic-from-`conversation_id`-alone
  path resolution), fixes a real, previously-latent stale-path bug this
  found in `route_to_project`'s Pending-Approval payload, splits Thread
  dates into a machine-parseable/human-readable sibling pair, and adds a
  new, deterministically-regenerated `## Related` body section carrying
  honest Customer/Person/Project wikilinks. `ADR-046` supersedes `ADR-043`
  points 2 and 7 and `ADR-042` point 5 only — every other already-Accepted
  ADR point is unchanged. The operator granted full autonomy for this
  requirement and was unavailable to review tonight, so every mechanism
  question was resolved directly, with reasoning and Alternatives
  Considered recorded in the ADR itself, per this project's own
  "resolve directly, don't guess" precedent — not silently guessed.
  **What to do:** review `ADR-046` in
  `Implementation/Architecture/ADR.md`, approve or reject the four
  resolved mechanism decisions (staging shape, filename/lookup mechanism,
  wikilink placement, Pull's non-addressable-capability resolution), then
  either let the decomposer's already-run task breakdown stand or reset
  the story's `status:` to redo `/plan-tasks` if you change the ADR.
  → `Implementation/UserStories/REQ-SB-69-US-01-decoupled-email-pull-and-human-readable-thread-notes.md`

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

- [x] 2026-08-11 · **REQ-SB-29-US-01** · decide the retrieval mechanism
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

  **Update, 2026-08-13 — Resolved.** Operator explicitly decided to skip
  the `/design` pass for this entire batch of work (REQ-SB-28/29/37/38/
  39/40/41) and build directly; the coder matches the established
  Section/Provider/Keywords/Working-mode kv-list row pattern instead.
  `/plan-tasks REQ-SB-29` proceeded without a prototype.

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

  **Update, 2026-08-13 — Re-specced in place after an operator PRD
  rewrite; re-checked, not re-guessed.** REQ-SB-28's PRD text now names
  the concrete mechanism directly (operator, verbatim): pass the upload
  to Compass for a summary, hand that summary to the Vault Filing Expert
  (REQ-SB-35) to place, tag, and write. Both real product dependencies
  this story needs are now `Done` and verified (`REQ-SB-25-US-01`,
  `REQ-SB-35-US-01`) — REQ-SB-35's own real interface
  (`determine_placement_and_file(content, source_description,
  requesting_agent_id)`) needs zero changes to accept this handoff. The
  PRD's own stated `REQ-SB-39` dependency was checked against the real
  code and judged NOT a real blocker — `REQ-SB-27-US-01`'s already-Done
  Skills mechanism (register/grant/invoke) already supports registering
  a brand-new Skill; `REQ-SB-39` is scoped to migrating *existing*
  hardcoded Actions, a separate concern (full reasoning in the story's
  own Context/Dependencies). One new, genuinely open technical finding
  surfaced this pass: Compass is text-only (no vision evidence anywhere
  in this codebase) so a plain Compass completion cannot summarize an
  image file the way the PRD's own text implies — left open to
  `/plan-tasks` (Compass vision vs. routing through REQ-SB-27's
  `diagram-understanding` Skill instead), but this does not block the
  text-file (PDF/txt/md) path.
  **What to do:** run `/design REQ-SB-28` for the chat attach-file
  control and the summarization/filing-progress acknowledgement in the
  thread — the only remaining hard gate. No other human decision is
  required first; this story is otherwise closer to buildable than it
  was at the prior pass.
  → `Implementation/UserStories/REQ-SB-28-US-01-file-upload-attach-and-handoff.md`

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

- [ ] 2026-08-13 · **REQ-SB-37-US-01 / US-02 / US-03** · REQ-SB-37 was
  rewritten (now "Agent Creation Wizard") and re-specced into three
  per-type stories — decide the persisted-registry ADR, the Producer
  output-action fork, then sequence `/design` + `/plan-tasks` per story
  Plain English: the PRD's operator rewrote REQ-SB-37 the same day this
  queue entry was first opened, replacing the old flat "Agent Creation"
  shape with a wizard whose steps differ by Type (Worker: Skills + Vault
  Scope + Section; Expert: a domain, starting empty and honestly uncertain;
  Producer: a Purpose + an output action). The analyst re-specced the
  existing `REQ-SB-37-US-01` in place and split it into three stories
  because the three types have genuinely different build-readiness today:
  - **`REQ-SB-37-US-01`** (entry point + Expert flow) is the *most* ready —
    it is NOT blocked by `REQ-SB-39` (only Worker/Producer are, per the
    PRD's own breadcrumb) and does not need `REQ-SB-40` either (an Expert
    can start empty and honestly say "I don't know" using the already-`Done`
    `REQ-SB-33` guardrail; `REQ-SB-40`'s gap-tracking is an add-on, not a
    precondition — see that story's own Context for the judgment call).
    It still carries the original ADR-level question forward: the
    persisted-registry mechanism (`AGENTS` becoming mutable, or
    `list_agents()`/`get_agent()` merging a static + persisted source)
    directly reverses `ADR-011` point 2 and needs a superseding ADR at
    `/plan-tasks`. The original custom-bespoke-actions fork is now resolved
    by `REQ-SB-39`'s own existence (everything becomes a Skill) and is no
    longer an open question.
  - **`REQ-SB-37-US-02`** (Worker flow) and **`REQ-SB-37-US-03`** (Producer
    flow) are both hard-blocked on `REQ-SB-39-US-01` **and**
    `REQ-SB-39-US-02` (both halves, not either) — a Worker's "Skills"
    step cannot honestly be written against today's still-dual Actions/
    Skills system without either misrepresenting what a Worker can do or
    building a second parallel mechanism, exactly what `REQ-SB-39` exists
    to prevent. `REQ-SB-37-US-02` additionally needs `REQ-SB-29-US-01`
    (Vault Scope) to land its own assignment surface first.
    `REQ-SB-37-US-03` additionally carries its own unresolved fork: the
    PRD's own text leaves the Producer "output action" mechanism genuinely
    open (a Skill vs. a destination/write-mode configuration) — not
    guessed, flagged for a human/architect decision.
  - None of the three has any `html-prototype/` coverage — a Create Agent
    affordance does not exist anywhere in the approved prototype.
  **What to do:** (1) confirm whether `REQ-SB-37-US-01`'s "no REQ-SB-40
  dependency" judgment call is acceptable, or direct otherwise; (2)
  ~~run `/plan-tasks REQ-SB-37-US-01` so the architect can write the
  superseding ADR~~ **done — see the 2026-08-13 architect-pass update,
  below**; (3) for `REQ-SB-37-US-02`/`US-03`, first advance
  `REQ-SB-39-US-01`, `REQ-SB-39-US-02`, and (for US-02) `REQ-SB-29-US-01`
  — they cannot be planned before those land; (4) for `REQ-SB-37-US-03`
  specifically, make a product/architect decision on the output-action
  fork (Skill vs. destination/write-mode) before its own wizard step can be
  specced at all.
  Full detail: `ESCALATIONS.md` → `ESC-020` (follow-up note, 2026-08-13).

  **Architect-pass update, 2026-08-13 (`/plan-tasks REQ-SB-37-US-01` step
  1) — new item requiring human review before the decomposer's tasks are
  locked in:** `ADR-030` was written (`Implementation/Architecture/ADR.md`)
  — it supersedes `ADR-011` point 2 only (points 1/3/4 untouched):
  `agent_registry.py`'s static `AGENTS` dict becomes `_SEED_AGENTS`
  (byte-identical, unchanged, stays in code) merged at read time with a new
  persisted `.second-brain/agents_registry.json` overlay for runtime-
  created agents, mirroring `skill_registry.py`'s own `_load_state`/
  `_save_state` JSON-file pattern exactly (the operator's own relayed
  mechanism decision, not architect-derived). Please review `ADR-030`
  before this story's tasks are built — in particular the id-collision
  disambiguation rule (numeric-suffix, not `create_section`'s "collapse to
  existing" semantic) and the decision to leave the 7 shipped agents in
  code (`_SEED_AGENTS`), not migrated into the JSON file. `/design` was
  explicitly skipped for this batch (operator direction) — the Create
  Agent entry-point placement (Settings, not the Agents Map canvas) and the
  type-selector's Worker/Producer-disabled-not-hidden sequencing were
  decided as ordinary architect calls, recorded in the story's own `##
  Notes`, not flagged separately. **What to do:** approve or reject
  `ADR-030`, then either let `/plan-tasks` continue to the decomposer as-is
  or reset `REQ-SB-37-US-01`'s `status:` to redo this pass with a different
  mechanism.

  **Decomposer-pass update, 2026-08-13 (`/plan-tasks REQ-SB-37-US-01` step
  2) — tasks now built on top of `ADR-030`, awaiting the same human
  review named above; nothing new to decide beyond it:** 8 scenarios
  locked as `AC-01`..`AC-08`; 4 tasks created (`T01` `vault_writer.py`
  primitives, `T02` `agent_registry.py` overlay + `create_agent`, `T03`
  `POST /agents`, `T04` `CreateAgentWizard.tsx` + Settings entry
  affordance), straight-line `depends_on` chain, all `status: Ready` in
  lockstep with the story. Story `status: Draft → Ready`; `gate` stays
  `flagged` (unchanged) — this pass introduced no new open question, it
  only decomposed `ADR-030`'s already-flagged mechanism into buildable
  tasks. **What to do:** unchanged from above — approve or reject
  `ADR-030`; once approved, `/plan-sprints` can group this story (its
  `gate: flagged` does not block sprint grouping, only signals the human
  should have looked at `ADR-030`/this task breakdown first).
  → `Implementation/UserStories/REQ-SB-37-US-01-agent-creation.md`
  → `Implementation/UserStories/REQ-SB-37-US-02-agent-creation-worker-flow.md`
  → `Implementation/UserStories/REQ-SB-37-US-03-agent-creation-producer-flow.md`
  → `Implementation/Architecture/ADR.md` (ADR-030, and the ADR-011
  superseded-note)

  **Coder-pass update, 2026-08-14 (`/implement-sprint SPRINT-033`) —
  `REQ-SB-37-US-01`'s own portion of this item is now resolved; `ADR-030`
  self-confirmed by a successful live build, not just a paper review:**
  all 4 tasks built and verified live end-to-end, all 8 locked ACs
  passing, story `status: Ready → Done`, `gate: flagged → clear`
  (mirroring `REQ-SB-20-US-01`/`REQ-SB-21-US-01`/`REQ-SB-35-US-01`'s own
  "successful build resolves the ADR-review flag" precedent). The id-
  collision disambiguation rule and the "7 shipped agents stay in code"
  decision both held up exactly as `ADR-030` specified, live. A
  sprint-level end-to-end pass beyond any single task's own ACs also
  confirmed the 7 pre-existing static agents are byte-identically
  unaffected. **This item stays open** — `REQ-SB-37-US-02`/`US-03` are
  unchanged, still blocked on `REQ-SB-39`/`REQ-SB-29-US-01`/the Producer
  output-action fork, exactly as recorded above (now further clarified
  and resolved by `ADR-031`, not reopened here).
  → `Implementation/Sprints/SPRINT-033-agent-creation-wizard-entry-and-expert-flow.md`
  → `Implementation/Architecture/architecture.md`
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

- [x] 2026-08-13 · **REQ-SB-38-US-01** · confirm the clustering threshold and
  the clustering scope granularity before `/plan-tasks` can lock precise ACs
  — Resolved 2026-08-13 (architect pass, `/plan-tasks` step 1): operator
  confirmed and locked both of the prototype's own proposed values as
  final — `VISIBLE_SLOT_CAP = 6`, scoped per-(Section × Type-ring), exactly
  as originally proposed, not re-derived. See the story's own `## Notes`
  ("Architect pass, 2026-08-13") and `architecture.md` → "Agents Map —
  Density Clustering (REQ-SB-38-US-01)" for the full reasoning. No ADR was
  needed. Story `gate` reset to `clear`; the decomposer tightens the
  Acceptance Criteria wording with these real values in the next
  `/plan-tasks` step.
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

- [ ] 2026-08-13 · **REQ-SB-39-US-01 + REQ-SB-39-US-02** · decide the
  mutates-classification mechanism for Skills, the chat-funnel question, and
  the build order — this is the largest, most consequential architecture
  reversal scoped this session
  Plain English: `REQ-SB-39` (Unify Agent Capabilities Under Skills) is a
  genuine, operator-confirmed reversal of `ADR-011` point 2's own "agent
  identity/actions stay hardcoded" design and `ADR-020`'s entire two-axis
  working-mode approval gate — every existing hardcoded Action
  (`run_capture_now`, `rebuild_person_note`, `ask_question`,
  `view_last_run`, `view_channel_status`, `pause_schedule`,
  `build_knowledge`) becomes a Skill, granted/revoked the same way
  `web-research`/`diagram-understanding` already are. The operator confirmed
  this covers "Everything, including existing shipped agents," not just
  future wizard-created ones. Split into two sequential stories (not one
  monolithic story, and not guessed as independently-orderable) so a
  mutating capability is never observably ungated even transiently:
  `REQ-SB-39-US-01` (the capability model + migrating every currently
  read-only Action — `view_last_run`/`ask_question`/`view_channel_status` —
  needs no gate change at all) must land before `REQ-SB-39-US-02`
  (extending the working-mode gate to Skills + migrating every currently
  mutating Action — `run_capture_now`/`pause_schedule`/`rebuild_person_note`/
  `build_knowledge` — both halves together, in the same release). Direct
  code inspection (not PRD-text assumption) confirms today's real shape:
  `agents_router.py::_invoke_action`'s two-axis gate is real and working;
  `skill_registry.py::invoke_skill`/its own invoke endpoint is confirmed
  **completely ungated** by working mode today (only the grant/revoke check
  applies) — exactly right for `REQ-SB-27`'s narrow read-only skills, and
  exactly what `REQ-SB-39-US-02` must close for mutating ones. A genuine,
  previously-uncaught gap was also found: `REQ-SB-27-US-01` shipped **zero
  UI** for Skills — no `html-prototype/` screen and no `src/frontend`
  component anywhere calls the Skills grant/revoke/invoke endpoints; today's
  only capability UI is `agents-map.html`'s static "Available actions"
  button list, which has no grant/revoke affordance and no Skills awareness
  at all. Neither story resolves the mechanism-level questions the PRD's own
  breadcrumb explicitly leaves open (the `mutates`-classification shape for
  Skills; whether `invoke_skill`/its endpoint needs a `trigger` concept and
  how it threads through every call site; whether `ADR-011`'s chat
  keyword-match funnel itself needs restructuring) — both are architect-
  level calls, correctly left to `/plan-tasks`, not guessed here. Full
  detail, including the live code findings behind every claim above:
  `ESCALATIONS.md` → `ESC-029`.
  **What to do:** before `/plan-tasks` can meaningfully begin architecting
  this, decide (a) the `mutates`-classification mechanism for Skills — a
  static per-Skill field mirroring `agent_registry.py`'s own precedent, or a
  materially different model (the PRD breadcrumb raises the possibility that
  a single Skill's read/write nature could vary by its own invocation args,
  unlike a fixed-shape Action); (b) whether `invoke_skill`/its endpoint
  gains a `trigger` parameter (`"chat" | "direct" | "hub_routed"`, mirroring
  `_invoke_action`'s own shape) and how every real call site is updated to
  supply it; (c) whether `ADR-011`'s chat keyword-match funnel stays
  Action-shaped and calls into the Skills mechanism internally, or is itself
  restructured to dispatch to Skills directly; (d) confirm the two-story,
  read-only-then-mutating build order is acceptable (recommended, for the
  safety reason named above) or direct a different sequencing. Separately,
  run `/design REQ-SB-39` for the Skills grant/revoke/unified-capability-list
  UI — no such surface exists in any approved prototype today, and
  `REQ-SB-39-US-02`'s own affected-screens question cannot be answered until
  it does.
  → `Implementation/UserStories/REQ-SB-39-US-01-unify-capabilities-model-and-read-only-migration.md`
  → `Implementation/UserStories/REQ-SB-39-US-02-unify-capabilities-working-mode-gate-and-mutating-migration.md`
  → `ESCALATIONS.md` (ESC-029)

  **Update, 2026-08-13 (`/plan-tasks REQ-SB-39-US-01` step 1 — architect).**
  The operator made both mechanism decisions (a)/(b) directly and relayed
  them: (a) `mutates` is a static per-Skill boolean on the Skill's own
  catalog entry, mirroring `ADR-020`'s Action shape exactly (not
  computed per-invocation from args); (b) `invoke_skill` gains a required
  `trigger: Literal["chat","direct","hub_routed"]` parameter, threaded
  through every real call site, mirroring `_invoke_action`'s shape.
  (c) `ADR-011`'s chat funnel is **not** rebuilt/restructured — only its
  dispatch step changes: a matched phrase for a migrated capability now
  calls `invoke_skill(..., trigger="chat")` instead of `_invoke_action(
  ..., trigger="chat")`, preserving every existing trigger phrase with
  minimal blast radius (`agent_registry.py`/`agent_chat.py` are both left
  completely unmodified). (d) The two-story, read-only-then-mutating
  order is confirmed and already in effect (this is `US-01`). The
  operator separately decided to skip `/design REQ-SB-39` and build
  directly (part of a batch decision covering `REQ-SB-28/29/37/38/39/
  40/41` — see `REQ-SB-29-US-01`'s own entry above), so the Skills grant/
  revoke/unified-capability-list UI is now built without a prototype,
  matching the established Section/Provider/Keywords/Working-mode
  kv-list row pattern. A new ADR, `ADR-028`, records the full mechanism
  for `US-01`'s own scope (the capability model + the 3 read-only ids):
  the `mutates`/`trigger` shapes above, the funnel dispatch fork, a
  one-time migration seed retrofitting the 4 real already-shipped agents
  onto real Skill grants, and a new `list_agent_capabilities` aggregator
  unifying `GET /agents/{agent_id}`'s response. `US-01`'s own `gate:`
  stays `flagged` (MUST-FLAG trigger 3 — `ADR-028` created), but per
  `Implementation/Pipeline.md` this does not halt `/plan-tasks` — the
  decomposer proceeds; review `ADR-028` and `US-01`'s resulting tasks
  together in one pass.
  **What to do now:** review `ADR-028` in
  `Implementation/Architecture/ADR.md`, approve or reject (in particular
  the "minimal blast radius" chat-funnel decision — `agent_registry.py`'s
  3 migrated-id entries stay physically present, unused by real
  invocation, purely as trigger-phrase-matching input — and the one-time
  migration-seed framing), then let the decomposer's `US-01` tasks
  proceed or reset `US-01`'s `status:` to redo if you change it.
  `US-02` (the mutating-Action migration + working-mode gate extension)
  is unaffected by this update — still needs its own `/plan-tasks` pass,
  composing on top of `ADR-028` once `US-01` ships.
  → `Implementation/Architecture/ADR.md` (ADR-028)

  **Update, 2026-08-13 (`/plan-tasks REQ-SB-39-US-01` step 2 —
  decomposer).** All 7 scenarios locked as `AC-01`…`AC-07`; 9 tasks
  written (`T01`–`T09`), `depends_on` acyclic; `status: Draft → Ready`,
  `gate: flagged` unchanged (same open `ADR-028` review, not a new
  trigger). **One additional call worth the same review pass:** `T09` is
  a real frontend task (`AgentDetailPanel.tsx` + a new
  `skillsApiClient.ts`, unifying the "Available actions" block into one
  capability list with a real grant/revoke control) — included because
  the architect's own Architecture-scope list names these files and this
  entry's own operator decision to skip `/design REQ-SB-39` and "build
  directly" already resolved the net-new-design-needed blocker. This
  reads as in tension with `US-01`'s own `## Non-Goals` ("Designing or
  building the concrete Skills grant/revoke UI"), written by the analyst
  before that same-day operator decision — the decomposer resolved it in
  the architect's favour (build it now) but flags the call explicitly, in
  case the operator intended the UI to wait for `US-02` or a later story.
  Both locked ACs touching this surface (`AC-02`, `AC-07`) are
  independently verifiable at the API/mechanism level regardless
  (`T03`/`T08`), so nothing is blocked either way. Full reasoning:
  `Implementation/UserStories/REQ-SB-39-US-01-unify-capabilities-model-
  and-read-only-migration.md` → `## Notes`.
  **What to do now:** as above (review `ADR-028`), plus confirm `T09`'s
  own inclusion in this pass is correct, or direct it deferred to a later
  story.

  **Update, 2026-08-13 (`/plan-tasks REQ-SB-39-US-02` step 1 —
  architect).** `US-01` landed `Ready` with `ADR-028`. This pass resolves
  `US-02`'s own remaining open architecture questions — where the
  working-mode gate for Skills lives, how a Supervised mutating Skill
  invocation creates a Pending Approval, and what "atomic" concretely
  means for landing the gate extension and the 4-mutating-Action migration
  together in a single-process app with no staged rollout — and records
  them in a new ADR, `ADR-029` (extends `ADR-020`/`ADR-028`, reopens
  neither). Three findings worth a human look specifically:
  1. **The gate moves inside `skill_registry.invoke_skill` itself, not
     mirrored into `agents_router.py` the way `_invoke_action` is.**
     `invoke_skill` has three real call sites across two layers
     (`skills_router.py`'s direct endpoint, `agents_router.py`'s dispatch,
     `knowledge_bootstrap.py`'s Hub-routed call — the last a business
     module `ADR-003`'s layering forbids from reaching into `agents_router.py`)
     — centralizing the gate in the one function every caller already
     passes through is what makes Scenario 8 ("never a route around the
     gate") true by construction, not by caller discipline.
  2. **A real, previously-undiscussed gap, confirmed by direct code
     reading:** of the 4 mutating action ids, only 2 (agent, action) pairs
     have a real wired handler in `_ACTION_HANDLERS` today
     (`email-capture`'s `run_capture_now`, `compass-expert`'s
     `build_knowledge`) — the other 5 real pairs (`meeting-capture`'s and
     `todo-capture`'s own `run_capture_now`, all 3 agents' `pause_schedule`,
     `people-producer`'s `rebuild_person_note`) already return an honest
     "not yet available" via the direct/chat funnel today, with no real
     handler to preserve. The migrated Skill handlers preserve this exact
     split — no new real behavior is built by this pass, matching this
     story's own Constraint ("a gating/declaration refactor, not a
     rewrite"). Worth confirming this reading matches the operator's own
     expectation before tasks are built against it.
  3. **The "4 real agents" framing in this story's own retrofit directive
     actually names 4 *action ids* across 5 distinct real agents** (3
     share `run_capture_now`+`pause_schedule`, 2 each carry one distinct
     id) — confirmed by direct reading of `agent_registry.py`: `email-
     capture`, `meeting-capture`, `todo-capture`, `people-producer`,
     `compass-expert`. Recorded explicitly since the story's own prose
     could be read as 4 agents.
  `US-02`'s own `gate:` stays `flagged` (MUST-FLAG trigger 3 — `ADR-029`
  created), does not halt the decomposer per `Implementation/Pipeline.md`.
  **What to do now:** review `ADR-029` in
  `Implementation/Architecture/ADR.md` — in particular point 8's
  atomicity framing (a `depends_on` task-sequencing discipline, not a code
  mechanism, since no real deploy gate exists in this app) — approve or
  reject, then let the decomposer's `US-02` tasks proceed or reset `US-02`'s
  `status:` to redo if you change it. Once both `ADR-028` and `ADR-029`
  are reviewed together with the resulting tasks, this entire combined
  entry can close.
  → `Implementation/Architecture/ADR.md` (ADR-029)
  → `Implementation/UserStories/REQ-SB-39-US-02-unify-capabilities-working-mode-gate-and-mutating-migration.md`

  **Update, 2026-08-13 (`/plan-tasks REQ-SB-39-US-02` step 2 —
  decomposer).** All 8 scenarios locked `AC-01`…`AC-08`; 4 tasks written
  (`T01`–`T04`), `depends_on` acyclic and structurally enforcing `ADR-029`
  point 8's atomicity (`T03`, the catalog/handler migration, `depends_on`
  `T01`, the gate, directly — never independently; `T04`, the retrofit,
  `depends_on` `T03`). Cross-story edges into `REQ-SB-39-US-01`'s real
  task IDs: `T01`/`T03` depend on `US-01-T01`/`T02` (the `mutates` field +
  `trigger` param this gate/migration build on); `T04` depends on
  `US-01-T05` (the exact `_MIGRATION_GRANT_SEED` dict it extends).
  `US-02`'s own `status: Draft → Ready`; `gate:` stays `flagged` — the
  same `ADR-029`-creation breadcrumb above, not a new trigger.
  **Two real wiring gaps found live while building `T03`
  (`build_knowledge`'s real handler), both resolved in-scope, worth the
  same review pass as `ADR-029` itself:**
  1. `bootstrap_agent_knowledge` (`knowledge_bootstrap.py`) is `async
     def`; `invoke_skill`/`_dispatch_skill`'s own dispatch contract is
     synchronous end-to-end, and a real caller may already be inside
     FastAPI's own active event loop when this handler runs — a plain
     `asyncio.run()` would crash there. Resolved with a dedicated
     single-use thread bridge, entirely inside `skill_tools.py` (in
     scope) — no edit needed to `knowledge_bootstrap.py`/
     `agents_router.py`/`skills_router.py`.
  2. A genuine circular import (`skill_tools → knowledge_bootstrap →
     skill_registry → skill_tools`) — resolved with a deferred,
     function-body import inside the new handler, not a module-level one.
  3. **Disclosed, NOT fixed (genuinely out of this story's own named file
     scope):** `build_knowledge` invoked via the chat/direct dispatch
     fork (`agents_router.py`'s own `_invoke_capability`,
     `REQ-SB-39-US-01-T07`) will append a second, generic history entry
     on top of `bootstrap_agent_knowledge`'s own internal one — low
     real-world severity (`compass-expert` stays Autonomous by standing
     convention, `REQ-SB-36-US-02`), a cosmetic duplicate history line,
     never a security/approval-bypass issue. Suggested fast-follow: a
     one-line `"history_recorded"` forward inside `_invoke_capability`'s
     own translated dict.
  **What to do now:** review `ADR-029`, `ADR-028`, and `T01`–`T04` (both
  stories) together in one pass; approve, or reset either story's
  `status:` to `Draft` to redo — in particular, decide whether the
  `_invoke_capability` fast-follow above should be pulled into `US-02`'s
  own scope now rather than deferred. Once reviewed, this entire combined
  `REQ-SB-39-US-01 + REQ-SB-39-US-02` entry can close.
  → `Implementation/Tasks/REQ-SB-39-US-02-T01-skill-registry-gate-and-dispatch-primitive.md`
  → `Implementation/Tasks/REQ-SB-39-US-02-T02-pending-approvals-router-skill-branch.md`
  → `Implementation/Tasks/REQ-SB-39-US-02-T03-migrate-four-mutating-actions-to-skills.md`
  → `Implementation/Tasks/REQ-SB-39-US-02-T04-migration-grant-retrofit-seed-mutating.md`

- [x] 2026-08-13 · **REQ-SB-40-US-01** · decide the "I don't know" detection
  mechanism and the human-input-closing UI shape, then run `/design` for the
  knowledge-gaps view
  Plain English: `REQ-SB-40` (Agent Knowledge-Gap Tracking & Expert
  Readiness) needs every honest "I don't know" reply (`REQ-SB-33`, `Done`)
  recorded as a trackable, viewable, closeable knowledge gap, with an
  agent's open-gap count visible and declining as gaps close — the operator's
  own named signal of Expert readiness. Direct code inspection confirms
  `REQ-SB-33`'s honest-uncertainty behavior is prompt-level only today (no
  structured signal distinguishes an "I don't know" reply from any other
  reply), "Expert" is already a real `"type": "expert"` marker in
  `agent_registry.py`, and `REQ-SB-11`'s existing Agent Activity log
  deliberately excludes conversational entries (a gap needs a new record
  kind, not reuse of that log). No `html-prototype/` screen shows a
  knowledge-gaps view anywhere, and `REQ-SB-41` (Agent Overview) — the PRD
  breadcrumb's own named "likely fit, not confirmed" display surface — is
  itself unspecced with no prototype coverage of its own. The story's own
  Acceptance Criteria are written at the observable-behavior level only
  (an honest "I don't know" produces a recorded, viewable, closeable gap;
  the two named closing paths — direct human input, or directing the agent
  to research it via `REQ-SB-36` — both work; the open count visibly
  declines) and do not presume the detection mechanism, the human-input UI
  shape, or the display surface. Two other questions the PRD breadcrumb left
  open were resolved directly, not guessed: whether "declining rate" needs a
  threshold/window (resolved as a simple current count, per the
  requirement's own Acceptance text) and whether a closed gap needs
  additional correctness verification (resolved as unnecessary, directly
  from this project's own standing `MEMORY.md` "no staging/promotion gate"
  constraint). Full detail: `ESCALATIONS.md` → `ESC-030`.
  **What to do:** before `/plan-tasks` can meaningfully begin architecting
  this, decide (a) the "I don't know" detection mechanism — a structured
  signal the model itself emits alongside its reply (extends `REQ-SB-33`'s
  own system-prompt design), or a cheaper, less-reliable pattern-match over
  the reply text; (b) the concrete shape of "the user directly provides the
  missing information" — a chat reply routed through the existing Vault
  Filing Expert (`REQ-SB-35-US-01`), mirroring how `REQ-SB-23`'s My Day
  Intake Agent already files conversational input, or a dedicated
  gap-resolution UI. Separately, run `/design REQ-SB-40` for the
  knowledge-gaps view itself — no such surface exists in any approved
  prototype today; ideally coordinate this with whenever `REQ-SB-41` (Agent
  Overview) is itself specced, since the PRD breadcrumb names that as the
  likely eventual display surface.
  → `Implementation/UserStories/REQ-SB-40-US-01-agent-knowledge-gap-tracking-and-expert-readiness.md`
  → `ESCALATIONS.md` (ESC-030)

  **Update, 2026-08-13 — Resolved at `/plan-tasks`.** The architect relayed
  the operator's own detection/storage decisions and made the one placement
  call left open (the Knowledge Gaps tab lives on `AgentDetailPanel.tsx`,
  gated to Expert-type agents), writing `ADR-032` — the `/design` step named
  above was explicitly skipped for this batch (operator-directed). See the
  still-open item below for the resulting `ADR-032` human review, and
  `ESCALATIONS.md` → `ESC-030` (flipped to `Resolved`).

  **Update, 2026-08-14 — Built and verified live.** All 8 tasks under
  `REQ-SB-40-US-01` (`SPRINT-035`) shipped and all 7 locked ACs verified
  against the real running app — see `MEMORY.md`'s `[2026-08-14]
  REQ-SB-40-US-01` entry and each task's own Implementation Log. The
  `ADR-032` review item directly below is still open and now doubles as the
  review point for the completed build.

- [ ] 2026-08-13 · **REQ-SB-41-US-01** · decide the Overview's navigation
  shape and Purpose data source (`ESC-031`), then run `/design REQ-SB-41`
  Plain English: REQ-SB-41 (Agent Overview Surface) specs a new overview —
  purpose, Vault Scope, Guardrails, working mode — shown before an agent's
  Chat, replacing today's "opens straight to Chat" behavior
  (`AgentDetailPanel.tsx`, confirmed live: `activeTab` defaults to `'chat'`
  on every agent switch). Three things are buildable today independent of
  any other unbuilt story: Purpose, Guardrails (a static statement of
  `REQ-SB-33`'s already-shipped behavior), and Working mode (reads
  `REQ-SB-21`'s already-shipped data). Vault Scope is only partially
  blocked — showing a real assigned scope needs `REQ-SB-29-US-01` (Draft,
  unbuilt) to ship first, but showing today's honest "no scope assigned
  yet" state does not and is specced directly. Two things are genuinely
  open, not guessed: (1) the exact navigation shape — the PRD's own
  "before or instead of landing directly on the Chat tab" phrasing does not
  commit to a new 4th tab, a new default landing tab, or a one-time
  interstitial; (2) no dedicated purpose/description data field exists
  anywhere in the real code today (only `name`, `type`, and `settings`/
  `actions` kv-rows) despite the PRD breadcrumb's own implication that one
  already does — a real discrepancy, confirmed by direct code inspection,
  not a guess. `REQ-SB-40-US-01`'s own explicit cross-reference ("is
  REQ-SB-41 the right display surface for the knowledge-gap count?") is
  resolved as a deliberate punt, not silently dropped: `REQ-SB-40` is
  itself unbuilt with its own detection mechanism and data model still
  undecided, so no knowledge-gaps region is built on this Overview this
  pass — see the story's own Notes and `REQ-SB-40-US-01`'s Notes for the
  full reasoning. No `html-prototype/` screen shows an Overview region,
  Guardrails statement, or Vault Scope display anywhere — net-new-design
  needed regardless of the two decisions above. Full detail:
  `ESCALATIONS.md` → `ESC-031`.
  **What to do:** decide (a) the Overview's navigation shape (new tab vs.
  new default landing vs. interstitial), and (b) the Purpose region's data
  source (reuse `name`/`type`/`settings` as-is, or add a new dedicated
  description field per agent in `agent_registry.py`). Then run
  `/design REQ-SB-41` — no prototype coverage exists for any part of this
  requirement today. Separately, no action needed on the
  `REQ-SB-40`/`REQ-SB-41` cross-reference — it is resolved (punted, not a
  hard dependency); revisit only once `REQ-SB-40-US-01`'s own mechanism
  questions are decided.
  → `Implementation/UserStories/REQ-SB-41-US-01-agent-overview-surface.md`
  → `ESCALATIONS.md` (ESC-031)

  **Update, 2026-08-13 (`/plan-tasks` step 1 — architect) — superseded by
  `ADR-033`; review that instead.** `/design` stays skipped for this batch
  (operator-directed, unchanged). Both genuinely open questions above are
  now resolved: (a) navigation shape — Overview becomes
  `AgentDetailPanel.tsx`'s new **default-landing tab** (`TABS` gains
  `'overview'`, first; `activeTab` no longer defaults to `'chat'`),
  directly answering the operator's own "before... Can Chat with it"
  framing; (b) Purpose data source — reads the existing `settings`
  kv-list (`"Purpose"`, falling back to `"Domain"`), composing
  `ADR-030`/`ADR-031`'s already-established Expert-Domain/Producer-Purpose
  mechanism, never a new field. Two further real judgment calls, made and
  recorded, not left open: all 7 shipped agents are backfilled with a real,
  authored one-line Purpose (see `ADR-033` point 3a for the 7 draft
  lines) rather than shown an empty state, since they're real,
  already-understood agents; and the Overview now composes `ADR-032`'s
  already-built `GET /agents/{agent_id}/knowledge-gaps` `open_count` field
  for Expert-type agents (the punt's original objection — "speculative UI
  for data that doesn't exist yet" — no longer applies now that
  `REQ-SB-40-US-01` is `Ready` with a real endpoint). `ESC-031` stays
  `Open` until this ADR is reviewed (it is the resolving artefact once
  approved, not yet marked `Resolved`).
  **What to do:** review `ADR-033` in `Implementation/Architecture/ADR.md`
  — in particular the navigation-default change (Chat no longer
  auto-selected) and the 7 draft backfill Purpose lines (point 3a) — approve
  or reject, then run `/plan-tasks` again if you change it. The decomposer
  proceeds to lock ACs/tasks in the same pass, per Pipeline.md's "do NOT
  halt the stage" rule — review the ADR and the resulting tasks together.
  → `Implementation/Architecture/ADR.md` (ADR-033)
  → `Implementation/UserStories/REQ-SB-41-US-01-agent-overview-surface.md`

- [ ] 2026-08-13 · **REQ-SB-37-US-03** · review `ADR-031` — resolves the
  Producer "output action" fork before the decomposer amends and locks ACs
  Plain English: `/plan-tasks` step 1 (architect) resolved this story's own
  previously-flagged, PRD-acknowledged open fork — whether a Producer's
  "output action" is a granted Skill or a separate destination/write-mode
  concept — per the operator's own direct instruction (relayed, not
  re-derived): it's a granted Skill, the same mechanism a Worker uses for
  its tools. New `ADR-031` records this plus three consequential decisions:
  (1) the wizard's output-Skill step is single-select, not Worker's
  multi-select — the PRD's own consistently singular "an output action"
  phrasing, and a Producer's identity being one Purpose paired with one way
  of acting on its output, not an open toolbox; (2) one minimal placeholder
  output Skill, `write-to-vault-draft`, is seeded into `skill_tools.SKILLS`
  (honest-unavailable stub, mirrors `diagram-understanding`'s own precedent)
  because direct inspection confirmed zero existing or already-planned
  Skill is a plausible output/destination Skill — without seeding one, the
  newly-directed Skills-grant step would have nothing to render or verify;
  (3) Purpose is stored via `create_agent`'s existing `settings` kv-list
  (mirrors Expert's Domain), and this story is what actually introduces the
  first real Purpose value in the data model — it does not wait on
  `REQ-SB-41-US-01` (still `Draft`, unbuilt) to land first. **A real,
  named gap:** this story's own current Acceptance Criteria (Scenarios 1-5)
  cover only Purpose + Section — they predate this fork's resolution and do
  not yet include a Scenario for granting the output Skill; the ADR directs
  the decomposer to amend Scenario 2 and add a missing-output-Skill
  rejection Scenario as part of locking ACs, rather than re-routing through
  `/spec`, since the story itself anticipated exactly this "amendment, since
  it has not yet reached Done" path. The decomposer proceeds without
  waiting for this review (an ADR-creation flag does not halt `/plan-tasks`,
  per `Implementation/Pipeline.md`) — review the ADR and the resulting/
  amended tasks together in one pass.
  **What to do:** review `ADR-031` in `Implementation/Architecture/ADR.md`
  — in particular the output-Skill cardinality decision (single-select) and
  the placeholder-Skill-seeding decision (`write-to-vault-draft`) — approve
  or reject, then run `/plan-tasks` again if you change it. This story's
  own `## Notes` carries the full architecture-scope section list the
  decomposer/coder are bounded by. Separately, this story remains
  net-new-design-needed (no `html-prototype/` screen has a Producer wizard
  step anywhere) — a `/design` pass is still needed before the frontend
  task can build against an approved screen.
  → `Implementation/UserStories/REQ-SB-37-US-03-agent-creation-producer-flow.md`

- [ ] 2026-08-13 · **REQ-SB-40-US-01** · review `ADR-032` — the detection/
  storage mechanism and the display-surface placement, before the
  decomposer locks tasks
  Plain English: `/plan-tasks` step 1 (architect) resolved this story's own
  previously-flagged mechanism questions (`ESC-030`), per the operator's
  own relayed decisions plus one placement call left to the architect
  (`/design` explicitly skipped for this batch): (1) **Detection** — a new
  bound tool, `record_knowledge_gap(topic)`, intercepted before generic
  tool execution exactly like `ADR-017`'s already-real
  `request_cross_section_help` — direct code read confirmed this graph's
  only structured model-signal channel today is bound tools, so this
  reuses a real, already-working precedent rather than a text
  pattern-match or a new structured-output mechanism. (2) **Storage** — a
  new, dedicated `app/business/knowledge_gap_tracking.py` +
  `.second-brain/agent_knowledge_gaps.json` (tenth state file), confirmed
  NOT folded into `agent_activity.py` (its `_ACTIVITY_KINDS` scope stays
  background-run-only, per that `Done` story's own Constraints). (3)
  **Closing paths** compose the already-`Done` Vault Filing Expert
  (`REQ-SB-35-US-01`, human-provided answers) and delegated
  knowledge-bootstrap chain (`REQ-SB-36-US-02`, directed research)
  unchanged — no new correctness-verification step, mirroring
  `MEMORY.md`'s standing no-staging-gate constraint. (4) **Display** — a
  new, conditionally-rendered "Knowledge gaps" tab on the existing
  `AgentDetailPanel.tsx`, gated to Expert-type agents only, since
  `REQ-SB-41` (Agent Overview, the PRD breadcrumb's own "likely fit")
  remains unspecced with no prototype coverage — this is the architect's
  own placement decision, not a prototype port. The decomposer proceeds
  without waiting for this review (an ADR-creation flag does not halt
  `/plan-tasks`, per `Implementation/Pipeline.md`) — review `ADR-032` and
  the resulting tasks together in one pass.
  **What to do:** review `ADR-032` in `Implementation/Architecture/ADR.md`
  — in particular the tool-call-interception detection mechanism and the
  Agent-Detail-Panel-tab display decision (both Alternatives Considered
  sections explain why a text pattern-match, a new structured-output
  wrapper, folding into `agent_activity.py`, and a new top-level nav page
  were each rejected) — approve or reject, then run `/plan-tasks` again if
  you change it. This story's own `## Notes` carries the full
  architecture-scope section list the decomposer/coder are bounded by.
  → `Implementation/UserStories/REQ-SB-40-US-01-agent-knowledge-gap-tracking-and-expert-readiness.md`

- [ ] 2026-08-13 · **REQ-SB-28-US-01** · review `ADR-034` — new upload
  storage, the `pypdf` dependency choice, and image support being
  explicitly deferred — before the decomposer locks tasks
  Plain English: `/plan-tasks` step 1 (architect) wrote `ADR-034` for this
  story's file-upload/Compass-summarization/Vault-Filing-Expert-handoff
  mechanism (`/design` explicitly skipped for this batch, operator
  direction). Direct code inspection confirmed two load-bearing facts the
  story's own re-spec had left open: `compass_client.py` is text-only (no
  vision), and `REQ-SB-27`'s `diagram-understanding` Skill is an
  unconditional stub that always returns `available: False` — it does not
  produce a text description of an image today. Neither of the story's own
  two named image-summarization options is real, so **this story's
  buildable scope is text-bearing files only (`.pdf` via a new `pypdf`
  dependency, `.txt`, `.md`); PNG/JPG image support is explicitly deferred
  to a follow-up story**, not silently built or guessed at. The ADR also
  decides: a new temporary, non-vault blob-storage boundary
  (`.second-brain/uploads/`, the first extension of the flat-file
  `.second-brain/` convention to raw bytes); the summarization capability
  is registered as a new `summarize-file` Skill through the already-
  `Accepted` Skills extensibility path (`ADR-015`) — this project's first
  real, non-stub Skill; and the new upload endpoint is additive, never
  modifying the existing `POST /agents/{agent_id}/chat` JSON contract
  (`REQ-SB-25-US-01`, `Done`). The decomposer proceeds without waiting for
  this review (an ADR-creation flag does not halt `/plan-tasks`, per
  `Implementation/Pipeline.md`) — review `ADR-034` and the resulting tasks
  together in one pass.
  **What to do:** review `ADR-034` in `Implementation/Architecture/ADR.md`
  — in particular the `pypdf` dependency choice (vs. `pdfplumber`/
  `PyMuPDF`/`unstructured`, all rejected in Alternatives Considered), the
  new `.second-brain/uploads/` blob-storage boundary, and the decision to
  explicitly defer PNG/JPG image support rather than wire it through the
  non-functional `diagram-understanding` stub — approve or reject, then
  run `/plan-tasks` again if you change it. This story's own `## Notes`
  carries the full architecture-scope file list the decomposer/coder are
  bounded by.
  → `Implementation/UserStories/REQ-SB-28-US-01-file-upload-attach-and-handoff.md`

  **Update, 2026-08-13 — Decomposer pass complete, `status: Ready`, gate
  stays `flagged` (carried forward, not re-triggered).** 10 ACs locked
  (`AC-01`..`AC-10`) — Scenario 1 tightened to the narrowed accepted-type
  list plus an attach-control structural requirement; Scenario 7 (image
  upload) is a new, split-out honest-rejection scenario, distinct from
  Scenario 8 (was Scenario 7 — exceeds the 20 MB cap). 5 tasks created at
  the flat root (`REQ-SB-28-US-01-T01`..`T05`, acyclic `depends_on`
  chain, all `status: Ready`): upload-storage module + `pypdf`/
  `python-multipart` (`T01`), `compass_client.summarize_content` (`T02`),
  the `summarize-file` Skill registration (`T03`, `depends_on: [T02]`),
  the new additive `POST /agents/{agent_id}/chat/attachment` endpoint
  (`T04`, `depends_on: [T01, T03]`), and the frontend attach affordance +
  honest-rejection UI (`T05`, `depends_on: [T04]`). One correction beyond
  `ADR-034`'s own text: `python-multipart` is also required (FastAPI's
  multipart `File`/`Form` parsing) and was missing from `ADR-034`'s
  dependency list — added to `T01` as a routine implementation necessity
  of the already-decided multipart endpoint, not a new architectural
  decision. Review `ADR-034` and this pass's 5 tasks together — same
  action as above, nothing further blocks review.
  → `Implementation/UserStories/REQ-SB-28-US-01-file-upload-attach-and-handoff.md`

- [x] 2026-08-13 · **REQ-SB-42-US-01** · needs `/design` for live per-agent
  activity pulses, plus an architect-level real-time-transport choice
  Plain English: REQ-SB-42 (Real-Time Agent Activity Pulses) asks for the
  Agents Map's static connections to be replaced with a live visualization
  of what's happening right now — a per-agent glow while it runs a
  capture/Skill or generates a chat reply, a traveling pulse between two
  specific agents for a Hub-routed cross-Section request, and a distinct
  steady (non-animated) highlight for an agent with an open pending-approval
  record — on both the Agents Map overview and a Section's drill-down. No
  `html-prototype/` screen shows any of these three visual elements today,
  only the existing, unaffected decorative `kb-pulse-dot` spoke animation.
  Separately, the operator explicitly chose real-time push over polling, but
  no push transport (WebSocket or SSE) exists in this codebase yet — the PRD
  itself names the specific choice as an architect-level call, not decided
  in this spec. The story also needs a brand-new "is this agent doing
  something right now" concept (REQ-SB-11's own observability only records
  completed history after the fact).
  **What to do:** run `/design REQ-SB-42` for the per-agent glow, the
  traveling pulse, and the steady pending-approval highlight on both
  surfaces; then `/plan-tasks` (architect) resolves the WebSocket-vs-SSE
  transport choice and the new in-progress-activity state design.
  → `Implementation/UserStories/REQ-SB-42-US-01-real-time-agent-activity-pulses.md`

  **Update, 2026-08-13 (designer pass complete — needs browser sign-off).**
  `agents-map.html` now has a 6th state-switcher option, "Agent activity
  pulses (REQ-SB-42 demo)", on both the overview and a Section drill-down:
  an animated per-agent glow (Email Capture, running), a traveling pulse
  along a connecting line between two specific agents (Meeting Capture
  &harr; Vault Q&A, Hub-routed), and a steady non-animated highlight
  (People Notes, pending approval) — plus To-Do Capture left idle for
  direct comparison. The existing decorative `kb-pulse-dot` is unaffected.
  The drill-down's own connecting-line geometry (routing the pulse along
  each Section's own Hub&rarr;agent line, captioned rather than drawn
  cross-Section) is the designer's own proposal, flagged for confirmation,
  not a locked decision — see that file's own top-of-file breadcrumb.
  **What to do:** open `html-prototype/agents-map.html` in a browser,
  select the new state-switcher option on both the overview and a
  drill-down, and approve (or adjust) before running `/spec` /
  `/plan-tasks` on REQ-SB-42-US-01 (which still separately needs the
  architect's own WebSocket-vs-SSE transport choice).

  **Approved 2026-08-13.** Operator reviewed and approved the prototype
  as-is. Story frontmatter updated to `status: Ready`, `gate: clear`.
  Moving to `/plan-tasks` (architect resolves the WebSocket-vs-SSE
  transport choice there, as anticipated above).

- [x] 2026-08-13 · **REQ-SB-43-US-01** · needs `/design` for the Meeting
  Cockpit, plus a decision on whether REQ-SB-21 working-mode gating applies
  to a brought-in Expert
  Plain English: REQ-SB-43 (Meeting Cockpit) asks for clicking a meeting (My
  Day's Calendar) to open a dedicated 3-panel workspace — attendee chips
  linking to Person notes on the right, a single shared multi-agent chat
  where the user brings in Expert agents as needed in the middle, and the
  user's available Agents plus this meeting's own scoped quick-research
  results (explicit save-or-discard, wikilinked to the Meeting note) on the
  left. `my-day-calendar.html`'s meeting rows are currently a flat,
  non-clickable list, and no part of this 3-panel workspace exists in any
  approved prototype screen. One product question the PRD's own
  clarifying session left genuinely open, not guessed at: whether
  REQ-SB-21's Autonomous/Supervised/Manual working-mode gating still
  applies to an Expert's actions once the user has explicitly brought it
  into this cockpit's chat, or whether being user-invited changes that —
  REQ-SB-21's own Manual-mode resolution never contemplated "brought into a
  shared chat" as a trigger category. A safer, narrower default was already
  resolved without guessing: an attendee chip with no existing Person note
  renders as a plain, non-clickable indicator (never a fabricated link),
  and every Expert's reply in the shared thread is visibly attributed to
  that Expert (exact visual mechanism left to `/design`).
  **What to do:** run `/design REQ-SB-43` for the 3-panel layout (clickable
  meeting rows, attendee chips including the no-Person-note fallback, the
  unified multi-agent chat with per-Expert attribution, and the scoped
  quick-research list); separately, decide whether REQ-SB-21 working-mode
  gating applies to a brought-in Expert's actions inside this cockpit
  before `/plan-tasks` locks the chat's action-dispatch design.
  → `Implementation/UserStories/REQ-SB-43-US-01-meeting-cockpit-expert-assisted-workspace.md`

  **Update, 2026-08-13.** Operator decision: explicit invitation into
  this cockpit's chat bypasses REQ-SB-21 working-mode gating for that
  Expert's actions inside the session — resolved, see the story's own
  Notes. `net-new-design-needed` still stands; `/design REQ-SB-43` is
  still required before this item clears.

  **Update, 2026-08-13 (designer pass complete — needs browser sign-off).**
  New screen `html-prototype/meeting-cockpit.html`: a 3-panel workspace
  (available Agents + this meeting's own scoped quick-research on the
  left, one unified multi-agent chat with per-Expert attribution in the
  middle, meeting info + attendee chips — including the plain non-
  clickable no-Person-note fallback — on the right), with 3 states
  (empty/first-open, in-progress with 2 attributed Experts, quick-research
  pending a save/discard decision). `my-day-calendar.html`'s meeting rows
  are now clickable, opening this screen. `net-new-design-needed` is now
  resolved by this pass.
  **What to do:** open `html-prototype/meeting-cockpit.html` in a browser
  (via a meeting row on `my-day-calendar.html`), click through all 3
  states, and approve (or adjust) before running `/spec` on
  REQ-SB-43-US-01.

  **Approved 2026-08-13.** Operator reviewed and approved the prototype
  as-is. Story frontmatter updated to `status: Ready`, `gate: clear`.
  Moving to `/plan-tasks`.

- [x] 2026-08-13 · **REQ-SB-44-US-01** · needs `/design` for the Inbox
  Cockpit, plus decisions on draft-reply persistence, the attachment
  mechanism, and tracking its REQ-SB-28-US-01 dependency
  Plain English: REQ-SB-44 (Inbox Cockpit) adapts REQ-SB-43's own 3-panel
  Meeting Cockpit pattern for email — clicking an email (My Day's Emails
  list) opens a workspace with sender/CC'd/thread-participant chips plus
  attachment review on the right, a shared multi-agent chat that can draft
  a reply as reviewable text (never auto-sent, and confirmed not to need
  working-mode/approval gating since drafting has no vault or external
  side effect) in the middle, and the user's Agents plus this email's own
  scoped quick-research results on the left. `my-day-emails.html`'s rows
  are currently flat and non-clickable, and no part of this workspace
  exists in any approved prototype. Three things are genuinely open, not
  guessed at: whether a drafted reply persists anywhere (a returnable
  draft object, or purely ephemeral in the chat session); how a surfaced
  attachment relates to REQ-SB-28's own Compass-summarize/handoff
  mechanism (reused directly, or a separate read-only preview); and — a
  real, currently-unmet dependency — REQ-SB-28-US-01 (File Upload for
  Agents) is `Ready`, not yet `Done` (this session's own direct check
  supersedes the PRD's own stale "Draft" characterization), so this
  story's attachments half specifically cannot build yet. A confirmed,
  real gap was also recorded, not assumed: no existing Email note field
  captures CC'd-recipient or thread-participant data today, so surfacing
  those chips needs new capture-side work, not just a cockpit-side read.
  **What to do:** run `/design REQ-SB-44` (ideally alongside
  `/design REQ-SB-43` for layout consistency); decide draft-reply
  persistence and the attachment-mechanism relationship to REQ-SB-28
  before `/plan-tasks` locks the design; and track REQ-SB-28-US-01's own
  remaining `ADR-034` human review — this story's attachments half is
  blocked until that story reaches `Done`.
  → `Implementation/UserStories/REQ-SB-44-US-01-inbox-cockpit-expert-assisted-workspace.md`

  **Update, 2026-08-13.** Operator decisions: a drafted reply is
  ephemeral (chat-session-only, no returnable-draft storage); a
  surfaced attachment reuses REQ-SB-28's own Compass-summarize/handoff
  mechanism directly (not a separate preview) — resolved, see the
  story's own Notes. The REQ-SB-28-US-01 dependency (Ready, not Done)
  is unchanged and still blocks the attachments half; `net-new-design-
  needed` still stands; `/design REQ-SB-44` is still required before
  this item clears.

- [ ] 2026-08-13 · **REQ-SB-39-US-01-T05** · scope-internal judgement
  call — a new internal-only seam on `grant_skill_access`
  Plain English: the migration-grant retrofit seed needed to call
  `grant_skill_access` during `_load_state()` itself, which would
  otherwise recurse infinitely (the function both reads and triggers a
  reload of the same state). Fixed with a backward-compatible internal
  seam: `grant_skill_access` gained one new keyword-only
  `_preloaded_state: dict | None = None` parameter, used only by the
  seed loop — every real external caller (`skills_router.py`'s grant
  endpoint, etc.) is unaffected, byte-identical behavior confirmed
  live. Not an `ESCALATIONS.md`-level event (no new dependency, no
  shared-interface change visible outside this file, no ADR deviation)
  — flagged per the coder's own "scope-internal judgement call" rule
  for a human spot-check, not a blocker.
  **What to do:** read `T05`'s own Implementation Log and the new
  `_preloaded_state` parameter in `skill_registry.py::grant_skill_access`
  — confirm the seam is acceptable, or direct a different fix if not.
  → `Implementation/Tasks/REQ-SB-39-US-01-T05-migration-grant-retrofit-seed.md`

- [ ] 2026-08-13 · **REQ-SB-39-US-01-T07** · two spot-check items — a
  result-shape bug fix, and an honest wording-changed finding on the
  operator's own highest-risk regression check
  Plain English: (1) the task's own illustrative `_invoke_capability`
  sample used `result["status"]`, which would `KeyError` on every real
  successful/honest-unavailable dispatch (those results carry no
  `"status"` key at all) — fixed with `result.get("status")`, same file,
  no new dependency/interface/ADR. (2) The coder's own explicit
  instructions for this sprint named "verify an existing chat trigger
  phrase (e.g. 'view last run') still produces the identical reply it did
  before this sprint" as the single highest-risk check. Verified live: the
  trigger phrase still matches the same capability id and the dispatch
  genuinely reroutes through `skill_registry.invoke_skill` — but the reply
  TEXT changed from `_execute_action`'s generic "This action is not yet
  available." to the Skill-stub convention "This skill is not yet
  available — no real handler has been built for it." Not a build defect —
  `ADR-028`'s own "Alternatives Considered" already explicitly declined
  mandating byte-identical wording, framing it as coder-level copy
  latitude and "not a functional regression in either reading" — but
  flagged here explicitly since the instruction asked for "identical
  reply" and the honest, disclosed answer is: mechanism identical, wording
  intentionally different, by already-Accepted-ADR design.
  **What to do:** read `T07`'s own Implementation Log for the full live
  before/after comparison; confirm the wording change is acceptable as
  `ADR-028` already decided, or direct a follow-up if the exact legacy
  string should be preserved after all.
  → `Implementation/Tasks/REQ-SB-39-US-01-T07-agents-router-dispatch-fork.md`

- [x] 2026-08-13 · **REQ-SB-39-US-01-T09** · built in an isolated
  worktree that lacked Node.js — real browser/build verification owed,
  now resolvable from the main checkout
  Plain English: this task was built by a coder running in an isolated
  git worktree (`.claude/worktrees/agent-a0ff2ea4ae24d5621`) for
  `SPRINT-030`. That worktree had no Node.js reachable anywhere inside
  it — `tools/node/` (the portable toolchain) is gitignored (`ADR-002`)
  and, like `.env`/`.venv`, was never copied in — so `npm run build`/
  `npx tsc --noEmit` could not run there, and `AgentDetailPanel.tsx`'s
  new unified Capabilities list (`T09`) was built and manually
  type/consumer-reviewed but never actually compiled or clicked in a
  real browser during that run. **Confirmed same-day: the main
  checkout DOES have a real, working `tools/node/`** — this was a
  worktree-isolation gap, not a true host-wide absence (see `MEMORY.md`
  for the correction). Both locked ACs this task touches (`AC-02`,
  `AC-07`) were already independently verified live at the API layer
  (`T03`/`T08`) — this gap does not block either AC, but the screen
  itself needs the real build/browser check this note describes.
  **What to do:** from the main checkout (`src/frontend`), run
  `..\..\tools\node\npm.cmd run build`, then open the Agents Map in a
  real browser — click an agent with mixed migrated-Skill capabilities
  (e.g. `vault-qa`), confirm the single unified Capabilities list
  renders correctly, and exercise a real Grant/Revoke click per `T09`'s
  own Test steps 1–3.

  **Update, 2026-08-14 — Resolved.** `npm run build` passed cleanly
  (real `tsc -b && vite build`, no errors). Live browser check against
  `vault-qa`: the Settings tab's unified "Capabilities" list rendered
  correctly — migrated read-only Skills (`View Channel Status`, `Ask a
  Question`) showed as genuinely granted per `T05`'s retrofit seed,
  alongside pre-existing Skills (`Web Research` granted, `Diagram
  Understanding`/`View Last Run` not) — no separate Actions/Skills
  sections, matching Scenario 7 exactly. Exercised a real Grant click on
  `Diagram Understanding`: flipped to `Revoke` and persisted; reverted
  with a real Revoke click, confirmed round-trip correct. `AC-02`/`AC-07`
  now independently confirmed at the UI layer too, not just the API
  layer. **Also found and fixed along the way (`BUG-008`, see
  `BUGS.md`):** the backend's own app-start capture pass was blocking
  FastAPI's startup completion — and therefore all HTTP traffic — on the
  full catch-up run finishing (100+ real Compass calls observed
  pre-fix). Fixed directly (`asyncio.create_task` instead of `await` in
  `capture_scheduler.py`'s `lifespan`), verified live: server now
  answers within ~2s of start, with or without `--reload`.
  → `Implementation/Tasks/REQ-SB-39-US-01-T09-agent-detail-panel-unified-capability-list.md`

- [x] 2026-08-13 · **SPRINT-030** · skim the sprint retrospective and
  harvest learnings
  Plain English: SPRINT-030 (REQ-SB-39-US-01, unify agent capabilities
  under Skills — capability model + read-only migration) is Done — all 9
  tasks built and verified live, including the operator's own two named
  watch-items (T05's real migration-grant seed confirmed against real
  `.second-brain/agent_skills.json` state; T07's chat-trigger-phrase
  regression check confirmed live via three independent layers). The
  coder drafted a Retrospective (sizing accuracy, what worked/didn't,
  patterns/antipatterns, open follow-ups) in the sprint file, but does
  not write `Implementation/Learnings.md` directly — that's a human step.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" and
  "Antipatterns to avoid" entries into `Implementation/Learnings.md`.
  Also review the 3 coder-level spot-check items and the inherited
  `ADR-028` review flagged separately above before considering this
  sprint's own review fully closed.
  → `Implementation/Sprints/SPRINT-030-unify-capabilities-model-and-read-only-migration.md`

  **Update, 2026-08-13 (designer pass complete — needs browser sign-off).**
  New screen `html-prototype/inbox-cockpit.html`: the same 3-panel
  pattern as meeting-cockpit.html, adapted for email — sender +
  CC'd/thread-participant chips (same clickable-vs-plain fallback rule),
  an attachment-review section with its own has-attachment/no-attachments
  demo toggle, the same unified multi-agent chat, and a distinct
  draft-reply area showing reviewable text only — there is no send action
  anywhere on the page. 4 states: empty/first-open, in-progress with 2
  attributed Experts, draft reply visible, quick-research pending a
  save/discard decision. `my-day-emails.html`'s rows are now clickable,
  opening this screen. `net-new-design-needed` is now resolved by this
  pass; the REQ-SB-28-US-01 dependency block on the attachments half is
  unchanged and still real (that story is `Ready`, not `Done`).
  **What to do:** open `html-prototype/inbox-cockpit.html` in a browser
  (via an email row on `my-day-emails.html`), click through all 4 states
  plus the attachment-presence toggle, and approve (or adjust) before
  running `/spec` on REQ-SB-44-US-01.

  **Approved 2026-08-13 (see REQ-SB-44-US-01's own entry above for the
  full item — this designer-pass note landed here, after the unrelated
  SPRINT-030 entry, due to a stray edit anchor; not relocated to avoid
  colliding with concurrent edits elsewhere in this file).** Operator
  reviewed and approved `html-prototype/inbox-cockpit.html` as-is. Story
  frontmatter updated to `status: Ready`, `gate: clear`. The
  REQ-SB-28-US-01 dependency block on the attachments half remains real
  and unresolved — `/plan-tasks` must sequence around it. Moving to
  `/plan-tasks`.

- [x] 2026-08-14 · **REQ-SB-42-US-01** · `ADR-035` created — review the
  real-time transport choice and new ephemeral agent-presence design
  before tasks are locked
  Plain English: `/plan-tasks` (architect step) wrote `ADR-035`, which
  chooses Server-Sent Events (not WebSocket) as the real-time push
  transport for the Agents Map's new activity pulses, and designs a new,
  in-memory-only `app/business/agent_presence.py` registry (never written
  to `.second-brain/`) tracking which agent is doing what right now,
  instrumented at five real dispatch call sites (capture/Skill run, chat
  generation, Hub-routed cross-Section requests, plus a live read of
  existing pending-approval state). This is the codebase's first
  real-time push surface — worth a human look before the decomposer's
  resulting tasks are built.
  **What to do:** review `ADR-035` in
  `Implementation/Architecture/ADR.md`, approve or reject the SSE choice
  and the `agent_presence.py` design, then let `/plan-tasks` continue (the
  decomposer runs automatically in the same pass — this flag does not
  block it, only marks the ADR for review alongside the resulting tasks).
  → `Implementation/UserStories/REQ-SB-42-US-01-real-time-agent-activity-pulses.md`

  **Approved 2026-08-14.** Operator reviewed ADR-035 and approved the SSE
  transport + `agent_presence.py` design as-is. Story frontmatter updated
  to `gate: clear`. Moving to `/plan-sprints`.

- [x] 2026-08-14 · **REQ-SB-43-US-01** · `ADR-036` created — review the
  multi-agent shared-thread chat mechanism and the working-mode-gate
  finding before tasks are locked
  Plain English: `/plan-tasks` (architect step) wrote `ADR-036`, which
  designs how the Meeting Cockpit's unified chat lets more than one
  brought-in Expert reply in one thread — by calling each Expert's own
  existing conversation function once per message and merging the results,
  not building a new orchestration layer — plus a genuine finding from
  reading the real code: a brought-in Expert's chat replies (including any
  research it triggers) never pass through this codebase's working-mode
  approval gate at all today, for a structural reason unrelated to this
  story, so the operator's own "bringing an Expert in is itself the
  approval" decision requires no new code — it already holds. Worth a
  human look, since this also documents a real, pre-existing gap in
  ordinary agent chat's own approval gating, not just Cockpit-specific
  behavior.
  **What to do:** review `ADR-036` in
  `Implementation/Architecture/ADR.md`, approve or reject the shared-thread
  mechanism and the working-mode-gate finding, then let `/plan-tasks`
  continue (the decomposer runs automatically in the same pass).
  → `Implementation/UserStories/REQ-SB-43-US-01-meeting-cockpit-expert-assisted-workspace.md`

  **Approved 2026-08-14.** Operator reviewed ADR-036 and approved the
  shared-thread mechanism and the working-mode-gate finding as-is. The
  pre-existing chat-tool-calling gate gap was logged as `BUG-012`
  (`BUGS.md`), deliberately not fixed in this batch. Story frontmatter
  updated to `gate: clear`. Moving to `/plan-sprints`.

- [x] 2026-08-14 · **REQ-SB-44-US-01** · `ADR-036` created — review the
  shared Cockpit module shape, the `REQ-SB-28-US-01` `depends_on`
  sequencing, and the new Email `recipients` field before tasks are locked
  Plain English: `/plan-tasks` (architect step) wrote `ADR-036` (shared
  with `REQ-SB-43-US-01`), which also decides that the Inbox Cockpit
  should share one backend/frontend module with the Meeting Cockpit rather
  than being built as a separate implementation, confirms the attachments
  half of this story genuinely cannot be built until `REQ-SB-28-US-01`
  ships (`Ready`, not `Done` — the decomposer must sequence around it with
  a `depends_on` edge, the rest of the story is not blocked), and designs
  a new Email-note field, `recipients`, to capture CC'd/thread-participant
  data that today's capture pipeline does not record at all.
  **What to do:** review `ADR-036` in
  `Implementation/Architecture/ADR.md`, approve or reject the shared
  module shape and the new `recipients` field, confirm the
  `REQ-SB-28-US-01` sequencing plan, then let `/plan-tasks` continue (the
  decomposer runs automatically in the same pass).
  → `Implementation/UserStories/REQ-SB-44-US-01-inbox-cockpit-expert-assisted-workspace.md`

  **Approved 2026-08-14.** Operator reviewed ADR-036 and approved the
  shared module shape, the `recipients` field, and the REQ-SB-28-US-01
  sequencing plan as-is. Story frontmatter updated to `gate: clear`.
  Moving to `/plan-sprints`.

- [ ] 2026-08-14 · **REQ-SB-39-US-02-T03** · live-discovered finding — a
  real, unrelated stray dev-server process is still running against the
  real vault, and its own background-scheduler tick created a real
  pending-approval record during this task's own live test window
  Plain English: while verifying `run_capture_now`'s real Supervised-mode
  behavior for `email-capture`, a SECOND, unrelated pending-approval
  record appeared (`action_id: None`, `trigger: "background"`, text "Run
  the scheduled email-capture step..."). This is the pre-existing
  `email_classification.py`/`ADR-018` background gate, not this sprint's
  own Skill gate, and no file this task touched. Root cause, confirmed by
  direct inspection: a real FastAPI dev-server process (`Get-NetTCPConnection
  -LocalPort 8000`) has been running unattended since before this session
  started (already at high accumulated CPU time at session start) — its
  own real hourly capture tick fired against the same real vault while
  `email-capture` happened to be briefly Supervised during this task's own
  test window, a genuine timing coincidence. **Not resolved (approved/
  declined) by the coder** — it is a real, correctly-gated, legitimate
  proposal (exactly what Supervised mode is supposed to produce), left
  `pending` for a human to review and act on directly rather than silently
  discarded or approved on the operator's behalf. Separately, this
  explains why the live capture verification for this task took
  unusually long in wall-clock time (contention with a second real,
  concurrent capture-scheduler process against the same Outlook/Compass
  backends) — not a defect in this sprint's own code.
  **What to do:** (1) decide the real, still-pending `background`-triggered
  `email-capture` proposal (approve/decline via the Pending Approvals UI or
  API) — it is real and safe either way, unrelated to this sprint's own
  correctness; (2) decide whether the stray dev-server process on port
  8000 should be stopped (it is real, unattended, already-running
  production-identical code, not a bug, but worth a deliberate decision
  rather than leaving it unnoticed).

- [x] 2026-08-14 · **SPRINT-032** · skim the sprint retrospective and
  harvest learnings
  Plain English: SPRINT-032 (`REQ-SB-29-US-01`, Agent-to-Tag/Folder Vault
  Scoping) is Done — all 5 tasks built and verified live, all 6 locked ACs
  confirmed (assignment via a real headless-browser/CDP round trip;
  retrieval via direct calls to the real, unmocked scope-aware MCP tool
  plus one live chat round-trip). The coder drafted a Retrospective
  (sizing accuracy, what worked/didn't, patterns/antipatterns, open
  follow-ups) in the sprint file, but does not write
  `Implementation/Learnings.md` directly — that's a human step. Also
  worth a skim: an honest, disclosed finding that the real vault has zero
  notes yet under `Work/Pipeline`/`Agreements`/`Consumption` specifically
  (structure only, no ingestion — unchanged since 2026-08-10), so the
  PRD's own literal "get me the pipeline for Masdar" example was verified
  against the closest real substitute (the `customer/<slug>` tag
  dimension) rather than that exact sub-schema, which has no real content
  yet to test a positive case against.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" and "Antipatterns
  to avoid" entries into `Implementation/Learnings.md`.
  → `Implementation/Sprints/SPRINT-032-agent-to-tag-folder-scoping.md`
  → `Implementation/Tasks/REQ-SB-39-US-02-T03-migrate-four-mutating-actions-to-skills.md`

- [x] 2026-08-14 · **SPRINT-033** · skim the sprint retrospective and
  harvest learnings
  Plain English: SPRINT-033 (`REQ-SB-37-US-01`, Agent Creation Wizard —
  entry point + Expert-type flow) is Done — all 4 tasks built and verified
  live, all 8 locked ACs confirmed (AC-01/02/03/07 via a real CDP-driven
  headless-browser session against the real wizard UI; AC-04/05/06/08 via
  real HTTP calls against every already-`Done` downstream surface). This
  is the first-ever runtime agent creation in the codebase — `ADR-030`'s
  own predicted mechanism (zero code changes needed in any of the five
  self-healing per-agent registries) was independently confirmed live, not
  just trusted. An additional sprint-level end-to-end pass (beyond any
  single task's own ACs) confirmed a freshly created Expert agent's real
  detail panel (Settings/Chat/History tabs) is fully functional, its Chat
  tab honestly declines an out-of-domain question rather than fabricating
  one, and the 7 pre-existing static agents are byte-identically
  unaffected before/after this build. The coder drafted a Retrospective
  (sizing accuracy, what worked/didn't, patterns/antipatterns, open
  follow-ups) in the sprint file, but does not write
  `Implementation/Learnings.md` directly — that's a human step. One
  scope-internal, non-blocking correction also worth a skim: the task's
  own informal `/agents-map` verification-step reference does not exist as
  a real route — the Agents Map is actually mounted at `/` (root).
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" and "Antipatterns
  to avoid" entries into `Implementation/Learnings.md`.
  → `Implementation/Sprints/SPRINT-033-agent-creation-wizard-entry-and-expert-flow.md`
  → `Implementation/UserStories/REQ-SB-37-US-01-agent-creation.md`

- [ ] 2026-08-14 · **REQ-SB-38-US-01-T04** · scope-internal judgement call — `AgentsMapPage.tsx` edited outside this task's own declared Files to Modify
  Plain English: `T04`'s own Objective (render `T01`'s cluster markers,
  widen the click-to-zoom state, wire the cluster drill-down) turned out to
  be structurally impossible from `AgentsMapCanvas.tsx` alone —
  `AgentsMapPage.tsx` (not listed in any of this story's four tasks' own
  `## Files to Modify`) is the sole caller of `layoutAgents()`, so
  `clusters` could only reach `AgentsMapCanvas` by threading it through
  that page. Separately, `T01`'s own locked `mapAgents` reduction (visible-
  on-overview agents only) meant the same reduced list, if reused unmodified
  for `SectionDrilldown`/`ClusterDrilldown`, silently dropped exactly the
  agents a cluster marker represents — a live-confirmed violation of `T04`'s
  own "must not narrow the existing full drill-down" Constraint (Scenario
  6/`AC-06`). The coder resolved both by adding one new `clusters` state and
  one new derived `fullAgents` state to `AgentsMapPage.tsx`, passed to
  `AgentsMapCanvas` as two new props — a minimal, mechanical extension of
  that file's own already-established state-then-pass-through pattern
  (mirrors `sections`/`agents`), verified live to be both necessary (AC-06
  genuinely fails without it) and sufficient (AC-06 passes with it, screenshot
  evidence in the task's own Implementation Log).
  **What to do:** read `REQ-SB-38-US-01-T04`'s own Implementation Log (the
  "Scope-internal judgement call" section) and confirm the
  `clusters`/`fullAgents` prop addition to `AgentsMapPage.tsx` is an
  acceptable resolution, or direct a different shape if not. No code action
  needed if accepted — this is a spot-check, not a blocker (the story is
  already `Done`, all 6 locked ACs verified live).
  → `Implementation/Tasks/REQ-SB-38-US-01-T04-agents-map-canvas-cluster-wiring.md`
  → `Implementation/UserStories/REQ-SB-38-US-01-agents-map-density-clustering.md`

- [x] 2026-08-14 · **SPRINT-037** · skim the sprint retrospective and harvest learnings
  Plain English: SPRINT-037 (`REQ-SB-38-US-01`, Agents Map Density
  Clustering) is Done — all 4 tasks built and verified live: `layoutAgents()`
  exercised directly via Node's own TS type-stripping (`T01`); the real
  `ClusterDrilldown` component rendered by the real dev server + React
  runtime in a real CDP-driven headless browser (`T03`); the fully-wired
  `AgentsMapCanvas` against 8 real `worker`-type agents created live via
  `POST /agents` (bringing a real `technical/worker` group to 8, over
  `VISIBLE_SLOT_CAP`) — genuinely observed 5 dots + 1 "+3" cluster marker, a
  cluster-scoped drill-down showing exactly its own 3 agents, an unchanged
  overview on Back, and the Section Hub's own full 9-agent unclustered
  drill-down (`T04`). Test agents were fully removed from the persisted
  registry immediately after (confirmed via a fresh `GET /agents`). The
  coder drafted a Retrospective (sizing accuracy, what worked/didn't,
  patterns/antipatterns, open follow-ups) in the sprint file, but does not
  write `Implementation/Learnings.md` directly — that's a human step. See
  also the separate `REQ-SB-38-US-01-T04` entry above for the one
  scope-internal judgement call this sprint made.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" and "Antipatterns
  to avoid" entries into `Implementation/Learnings.md`.
  → `Implementation/Sprints/SPRINT-037-agents-map-density-clustering.md`

- [ ] 2026-08-14 · **REQ-SB-28-US-01-T05** · two scope-internal
  judgement calls — reset attachment state on agent switch; allow a
  file-only send with no typed message
  Plain English: (1) the task's own reset block didn't explicitly say
  to clear `attachedFile`/`attachError` when the user switches agents,
  but leaving a staged attachment across a switch would silently attach
  the wrong agent's file on the next send — added to the existing
  agent-switch reset alongside `draft`/`messages`. (2) The task's own
  `handleSend` code sample composes `sendChatMessageWithAttachment(
  agentId, draft.trim(), attachedFile)` but doesn't redefine the
  original `!text || sending` guard; kept verbatim, attaching a file
  with no typed message would be silently blocked from ever sending,
  which contradicts ordinary chat-attachment UX and Scenario 1's own
  framing — loosened to `(!text && !attachedFile) || sending`, mirrored
  in the submit button's `disabled` condition. Neither changes any
  locked AC's own wording; both are additive, non-blocking, single-
  reading judgement calls, not ambiguous guesses.
  **What to do:** read `T05`'s own Implementation Log and the two
  changed conditions in `AgentDetailPanel.tsx` (`handleSend`'s guard,
  the agent-switch `useEffect`'s reset block) — confirm both are
  acceptable, or direct a different behavior if not.
  → `Implementation/Tasks/REQ-SB-28-US-01-T05-frontend-attach-affordance.md`

- [x] 2026-08-14 · **SPRINT-038** · skim the sprint retrospective and harvest learnings
  Plain English: SPRINT-038 (`REQ-SB-28-US-01`, File upload on agent
  chat — Compass summarization + Vault Filing Expert handoff) is Done —
  all 5 tasks built and verified live end-to-end with real files: a
  real `.txt` attachment through `upload_storage` → a real Compass
  summary genuinely reflecting the file's own content → a real Vault
  Filing Expert handoff → a real vault note filed with real tags/
  wikilinks, the temporary upload deleted every time, the original never
  vault-retained; the honest-rejection paths (unsupported `.png` type,
  oversized file) verified with zero storage/API calls made; the
  existing plain `POST /agents/{agent_id}/chat` JSON endpoint confirmed
  byte-for-byte unmodified, both by direct re-read and a real live call.
  The coder drafted a Retrospective (sizing accuracy, what worked/
  didn't, patterns/antipatterns, open follow-ups) in the sprint file,
  but does not write `Implementation/Learnings.md` directly — that's a
  human step. See also the separate `REQ-SB-28-US-01-T05` entry above
  for the two scope-internal judgement calls this sprint made.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" and
  "Antipatterns to avoid" entries into `Implementation/Learnings.md`.
  → `Implementation/Sprints/SPRINT-038-file-upload-attach-and-handoff.md`

- [ ] 2026-08-14 · **REQ-SB-43-US-01-T03** · scope-internal finding —
  `ADR-036`'s "already-established" Meeting `attendees` frontmatter field
  does not actually exist, and `vault_writer.py`'s own frontmatter parser
  cannot round-trip a list-of-dicts value at all
  Plain English: `ADR-036` point 7 states Meeting notes already carry an
  `attendees: list[{"name","email"}]` frontmatter field. Direct
  investigation found this false — no captured Meeting note has this
  field (attendee data lives only as body wikilinks); worse, a live test
  proved `vault_writer.py`'s own real `_format_frontmatter_value`/
  `_parse_frontmatter_value` pair silently loses a list-of-dicts value on
  any write+read round trip (renders as an unparseable Python-repr
  string, reads back as `[]`) — a structural gap in a shared primitive,
  not a "no data yet" situation. Worked around entirely within
  `cockpit/people.py`'s own file (accepts a JSON-encoded string as well
  as a native list) — no `vault_writer.py`/shared-interface change, so
  not escalated — but every real captured Meeting note today honestly
  shows zero attendee chips until either (a) some future story adds real
  `attendees` capture using the JSON-string convention documented in this
  task's own Implementation Log, or (b) `vault_writer.py`'s frontmatter
  parser itself gains native list-of-dicts support.
  **What to do:** confirm the JSON-string-encoding workaround is
  acceptable as the interim convention, or direct a `vault_writer.py`
  frontmatter-parser fix (own ADR/task) instead. Either way, `REQ-SB-08`'s
  own Meeting-capture pipeline still needs a follow-on story to actually
  WRITE the `attendees` field before this story's own attendee-chip
  mechanism produces real chips against real, non-test-constructed data.
  → `Implementation/Tasks/REQ-SB-43-US-01-T03-cockpit-people-chips.md`

- [ ] 2026-08-14 · **REQ-SB-43-US-01-T08** · scope-internal reconciliation
  against the real approved prototype
  Plain English: `T08`'s own illustrative code sample used a
  `.cockpit-grid` class that doesn't exist anywhere and had no per-Expert
  attribution color mechanism at all. Reconciled against the REAL
  approved `html-prototype/meeting-cockpit.html` instead, per this task's
  own Context/Notes directive: real `.cockpit-layout`/`.chat-proposal`/
  `.empty-state` classes, and a real `--agent-color-{type}` attribution
  color wired via `fetchAgentList()`'s own `type` field. No locked AC
  weakened; the deviations all make the built screen match the approved
  design MORE closely, not less.
  **What to do:** view the real running Cockpit (or the captured
  screenshot referenced in `T08`'s own Implementation Log) and confirm it
  reads as intended — no action needed if so.
  → `Implementation/Tasks/REQ-SB-43-US-01-T08-cockpit-shared-component.md`

- [ ] 2026-08-14 · **SPRINT-040** · skim the sprint retrospective and harvest learnings
  Plain English: SPRINT-040 (`REQ-SB-43-US-01`, Meeting Cockpit — shared
  `app/business/cockpit/` module + shared `Cockpit.tsx` 3-panel component)
  is Done — all 9 tasks built and verified live end-to-end: a real click
  from My Day's Calendar opens the 3-panel Cockpit for that exact
  meeting; attendee chips (via a hand-constructed test note, see the
  `T03` entry above) correctly link to real Person notes or honestly show
  "no note yet"; two real Expert agents brought into the same chat
  produced one genuinely shared thread with distinct, colored
  attribution; on-the-spot research produced a real Anthropic web-search
  result with an explicit Save/Discard choice (Save created a real
  wikilinked note; Discard created nothing); `REQ-SB-20`'s own
  Hub-routing behavior for a brought-in Expert was independently
  reconfirmed byte-identical before/after. Two scope-internal judgment
  calls (see the `T03`/`T08` entries above) logged for spot-check. The
  coder drafted a Retrospective, but does not write
  `Implementation/Learnings.md` directly — that's a human step.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" and
  "Antipatterns to avoid" entries into `Implementation/Learnings.md`.
  → `Implementation/Sprints/SPRINT-040-meeting-cockpit-expert-assisted-workspace.md`

- [ ] 2026-08-14 · **REQ-SB-44-US-01-T01** · scope-internal deviation —
  `recipients` written as a JSON-encoded string, not the task's own raw-list
  code sample
  Plain English: the task's own illustrative code sample wrote `"recipients":
  email.get("recipients", [])` — a raw `list[dict]` literal. Direct reading
  of `vault_writer.py::_format_frontmatter_value`/`_parse_frontmatter_value`
  (before writing any code) confirmed this exact real limitation
  `REQ-SB-43-US-01-T03` already found for the `attendees` field applies
  identically here: a raw list-of-dicts literal round-trips to `[]` silently.
  Implemented as `json.dumps(email.get("recipients", []))` instead — the same
  JSON-string convention `cockpit/people.py` (built by `REQ-SB-43-US-01-T03`)
  already accepts, requiring zero consuming-side changes. Verified live: a
  real, monkeypatched-Outlook `classify_recent_emails()` run produced a real
  Email note whose `recipients` field round-trips correctly through
  `read_note()`/`json.loads()`, and real chip rendering (existing vs.
  non-existent Person note) was independently confirmed live in a real
  browser against this exact data.
  **What to do:** spot-check that the JSON-string convention (rather than a
  `vault_writer.py`-level fix to `_format_frontmatter_value`/
  `_parse_frontmatter_value` themselves) remains the right call for now — a
  dedicated fix to those two functions was already named as a candidate
  future follow-up in `SPRINT-040`'s own Open follow-ups, not scoped to
  either cockpit story.
  → `Implementation/Tasks/REQ-SB-44-US-01-T01-email-recipients-capture.md`

- [ ] 2026-08-14 · **REQ-SB-44-US-01-T03** · scope-internal deviation —
  `_attachments_dir` skips slugification entirely, not the task's own
  private-`_slugify`-reach-through sample
  Plain English: the task's own code sample fell back to reaching into
  `vault_writer.py`'s private `_slugify` if needed. Direct reading of
  `vault_writer.py::write_attachments`/`write_note` confirmed both compute
  the attachments-directory name and the note's own filename stem via the
  IDENTICAL `_slugify(filename_stem)` call on the IDENTICAL raw input — so a
  real Email note's own `path.stem` (what the Cockpit route is keyed on) is
  already byte-identical to the attachments-directory name. Implemented
  `_attachments_dir` with NO slugification at all, confirmed live against
  two real vault fixtures (an email with a real PDF attachment, one
  without).
  **What to do:** spot-check this reasoning holds for any future
  attachments-directory naming change to `write_attachments`/`write_note` —
  if either ever diverges in how it derives its own slug, this
  no-slugification shortcut would need revisiting.
  → `Implementation/Tasks/REQ-SB-44-US-01-T03-cockpit-attachments-module.md`

- [ ] 2026-08-14 · **SPRINT-041** · skim the sprint retrospective and harvest learnings
  Plain English: SPRINT-041 (`REQ-SB-44-US-01`, Inbox Cockpit — Meeting
  Cockpit pattern adapted for email, attachment review, reviewable draft
  replies) is Done — all 6 tasks built and verified live end-to-end,
  directly on top of `SPRINT-040`'s own shared `app/business/cockpit/`/
  `cockpit_router.py`/`cockpitApiClient.ts`/`Cockpit.tsx`, zero duplication:
  a real click from My Day's Emails opens the 3-panel Inbox Cockpit for
  that exact email; sender/CC people chips (via a real captured test email)
  correctly distinguish an existing Person note (clickable) from one that
  doesn't exist yet; a real PDF attachment on a real captured email was
  listed and handed off to a real Compass summarization call, posted into
  the shared thread; two real brought-in Experts replied in one shared
  thread with distinct attribution; a drafted reply rendered as reviewable
  text with a real, working Copy-to-clipboard affordance, with no
  send/outbound-email code path anywhere in the codebase (confirmed by
  direct whole-codebase reading); a real Anthropic-backed on-the-spot
  research call (reusing `SPRINT-040`'s own `research.py` UNCHANGED)
  produced a genuine result with an explicit Save/Discard choice, scoped
  per-email. Two scope-internal judgment calls (see the `T01`/`T03` entries
  above) logged for spot-check. The coder drafted a Retrospective, but does
  not write `Implementation/Learnings.md` directly — that's a human step.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" and
  "Antipatterns to avoid" entries into `Implementation/Learnings.md`. In
  particular, the `brought_in_agent_ids[0]`-as-requester research-routing
  UX rough edge has now recurred across two sprints (`SPRINT-040`,
  `SPRINT-041`) and may warrant a dedicated future product decision.
  → `Implementation/Sprints/SPRINT-041-inbox-cockpit-expert-assisted-workspace.md`

- [ ] 2026-08-14 · **REQ-SB-46-US-01** · review new `ADR-039` (Agent
  Creation Wizard Redesign — popup modal + step bar, shared `SkillsTree.tsx`
  extraction), and the new cross-story `depends_on` edge onto
  `REQ-SB-48-US-01-T02`
  Plain English: the analyst's original two flags (net-new-design-needed;
  the field-to-step mapping assumption) are both resolved — the operator
  directed a `/design` skip (matching `REQ-SB-47`/`REQ-SB-48`'s own
  precedent) and confirmed the field-to-step mapping as final. The
  architect pass instead wrote `ADR-039`, resolving three real composition
  questions against this story's now-`Ready` siblings: (1) Step 3's
  Tools/Skills picker will use a NEW shared `SkillsTree.tsx` component —
  originated by `REQ-SB-48-US-01-T02` (a `mode="manage"` grant/revoke
  tree for `AgentDetailPanel.tsx`) and consumed here in a new
  `mode="select"` multi-select mode, rather than duplicating the tree UI —
  this is this codebase's FIRST cross-story frontend task dependency
  (`REQ-SB-46-US-01`'s Step-3 task will carry `depends_on:
  REQ-SB-48-US-01-T02`); (2) Step 4's Trigger/Schedule composition stays
  metadata-only, reconfirmed unchanged now that `REQ-SB-47`'s real
  Schedule tab exists; (3) folding `REQ-SB-51`'s Background-Agent toggle
  into the wizard was considered and declined (no locked AC needs it, and
  it would add an avoidable dependency on that story's own not-yet-built
  backend field) — left for a future story. The new popup modal/step-bar
  CSS is built from this codebase's own existing design tokens, explicitly
  NOT a reuse of the side panel's own slide-in overlay classes/behavior
  (the story's own Scenario 2 requires visual distinctness from it).
  **What to do:** review `ADR-039` in
  `Implementation/Architecture/ADR.md` (approve, or redirect and re-run
  `/plan-tasks`); when the decomposer runs, confirm the new
  `REQ-SB-48-US-01-T02` cross-story `depends_on` edge is sequenced
  correctly by the product-owner at `/plan-sprints` (same sprint, or
  `REQ-SB-48-US-01` in an earlier ordered sprint).
  → `Implementation/UserStories/REQ-SB-46-US-01-agent-creation-wizard-popup-modal-redesign.md`

- [x] 2026-08-14 · **REQ-SB-46-US-01** · decomposer pass: `REQ-SB-48-US-01-T02`'s
  own locked scope does not guarantee the standalone, mode-parameterized
  `SkillsTree.tsx` component `ADR-039` and this story's new `T04` assume
  Plain English: `ADR-039` (and this story's own Step-3 task,
  `REQ-SB-46-US-01-T04`) assume `REQ-SB-48-US-01-T02` will originate a
  shared component at `src/frontend/src/features/agents-map/
  SkillsTree.tsx` with a `mode="manage"`/`mode="select"` prop. Read
  directly, `REQ-SB-48-US-01-T02`'s own locked `## Files to Modify` gives
  its coder real latitude — "a new sibling component file... e.g.
  `SkillsCapabilityTree.tsx`... vs. an inline implementation is your own
  latitude" — it never mandates the filename `SkillsTree.tsx`, never
  mentions a `mode` prop, and its own locked ACs/Tests describe only the
  `mode="manage"` grant/revoke tree behavior. If `T02`'s coder builds it
  inline, or under a different name/shape, `REQ-SB-46-US-01-T04`
  (`depends_on: REQ-SB-48-US-01-T02`) will have nothing importable to
  extend into a `mode="select"` variant — its own task text names this
  explicitly and directs its coder to escalate rather than duplicate the
  tree if that happens, but the root gap (two locked task files disagreeing
  on a shared artefact's own guaranteed shape) is a real, disclosed
  inconsistency this pass could not resolve on its own authority (editing
  `REQ-SB-48-US-01-T02`'s own locked task file is out of this role's scope
  — a sibling story's locked task, not this pass's own artefact).
  **What to do:** before `/plan-sprints` sequences these two stories, either
  (1) amend `REQ-SB-48-US-01-T02`'s own `## Files to Modify`/Constraints to
  mandate the exact `SkillsTree.tsx` path + `mode` prop shape `ADR-039`
  assumes (a locked-task edit — human, or re-run the decomposer against
  that still-`Ready`, not-yet-`Done` task specifically), or (2) accept the
  risk and let `REQ-SB-46-US-01-T04`'s coder resolve the shape mismatch
  live when it starts, per that task's own documented escalation path.

  **Update, 2026-08-14 — Resolved.** Took option (1): `REQ-SB-48-US-01-T02`'s
  own `## Files to Modify` amended directly (still `Ready`, not yet `Done`,
  in scope for this fix) to mandate the exact standalone, mode-parameterized
  `SkillsTree.tsx` shape `ADR-039`/`REQ-SB-46-US-01-T04` assume — filename,
  `mode="manage"`/`mode="select"` prop, and an explicit instruction not to
  ship a fully-inlined, non-extractable implementation. The coordination
  risk is removed at the source; `REQ-SB-46-US-01-T04`'s own documented
  escalation path remains as a defensive fallback only, not the expected
  path.
  → `Implementation/UserStories/REQ-SB-46-US-01-agent-creation-wizard-popup-modal-redesign.md`
  → `Implementation/Tasks/REQ-SB-48-US-01-T02-capabilities-tool-tree.md`
  → `Implementation/Tasks/REQ-SB-46-US-01-T04-step3-skills-tree.md`

- [ ] 2026-08-14 · **REQ-SB-47-US-01** · review new ADR-037 (Per-Agent
  Scheduler + shared Outlook-COM dispatch lock), then run `/design
  REQ-SB-47` before the coder builds the Schedule tab
  Plain English: the architect pass wrote `ADR-037`, resolving the shared
  lock's real mechanism (relocated to a new `app/business/
  agent_schedule_registry.py`, mirroring ADR-029's own precedent — no new
  `business → scheduling` import edge), its explicit **in-process-only**
  scope (per the operator's own already-relayed decision: the literal
  SPRINT-030 two-process collision stays a disclosed, out-of-scope
  operational-hygiene risk, not solved by this mechanism), and the new
  `invoke_skill` `"scheduled"` trigger's composition with ADR-029's
  working-mode gate (Manual mode's scheduled ticks skip silently; run-now
  reuses the existing `"direct"` literal unchanged). `meeting-capture`'s/
  `todo-capture`'s `run_capture_now` stays the existing honest
  not-available stub, per the operator's own already-relayed scoping
  decision. One item remains genuinely open, unresolved by this
  architecture pass: no Schedule tab, or any tab-bar pattern, exists
  anywhere in `html-prototype/agents-map.html`'s agent detail panel today
  — confirmed by direct inspection.
  **What to do:** review `ADR-037` in
  `Implementation/Architecture/ADR.md` (approve, or redirect and re-run
  `/plan-tasks`); run `/design REQ-SB-47` to produce an approved
  Schedule-tab prototype screen before the coder builds the frontend half
  of this story's scope (or explicitly direct a build-without-`/design`
  skip, matching this project's own established precedent for a story at
  this stage).
  **Update, 2026-08-14 (`/implement-sprint SPRINT-045`):** the coder built
  the full story anyway, per this project's own precedent that a flagged
  item does not halt the build — all 6 tasks are `Done`, all 9 locked ACs
  verified live (including the shared-lock property, confirmed twice
  independently: an in-process `asyncio.gather` timing-marker proof, and a
  real cross-agent HTTP-layer race). The Schedule tab shipped WITHOUT a
  `/design` pass (the one item this entry itself flagged as still open) —
  its concrete layout is real, working, and visually spot-checked
  (screenshot in `T06`'s own Implementation Log) but never received a
  human/prototype sign-off. **Remaining ask, narrowed:** review `ADR-037`
  (as originally requested) AND retroactively review the shipped Schedule
  tab's own layout/visual language (a `/design`-after-the-fact spot-check,
  or explicit sign-off that the shipped layout is acceptable as-is). Also
  see `T02`'s own Implementation Log for one real, live-discovered
  duplicate-history-entry defect found and fixed in-scope during this
  build (flagged there for spot-check, not a new architecture question).
  → `Implementation/UserStories/REQ-SB-47-US-01-per-agent-scheduler-and-shared-serialization.md`
  → `Implementation/Tasks/REQ-SB-47-US-01-T02-agent-schedule-registry.md`
  → `Implementation/Tasks/REQ-SB-47-US-01-T06-frontend-schedule-tab.md`

- [ ] 2026-08-14 · **REQ-SB-49-US-02** · review `ADR-038` — the new
  gate-preserving call path for the `@PersonName` proposed Person-note
  edit, and its "propose" deviation for Manual/Autonomous mode
  Plain English: the architect has resolved the tension this story's own
  analyst pass named (`ADR-036`'s "Cockpit bypasses `invoke_skill`'s gate
  by construction" vs. this requirement's own PRD text wanting the
  `@PersonName` edit gated) with a new `ADR-038`: a bound tool
  (`propose_person_note_update`), intercepted in `graph.py` exactly like
  `ADR-032`'s `record_knowledge_gap`, reaches the real working-mode gate
  through a new `"cockpit_mention"` trigger literal — a deliberate,
  narrow carve-out that does NOT extend `ADR-036`'s bypass to this one
  capability, per the operator's own relayed resolution. `ADR-038` also
  makes a second, real judgement call worth a human look: "propose" is
  read as requiring an explicit in-thread confirm/discard step for
  Manual/Autonomous dispatch specifically (Supervised needs none — its
  own Pending-Approval "Approve" click already is the confirmation) — a
  genuine deviation from how every other mutating Skill in this codebase
  behaves once dispatched in those two modes.
  **What to do:** review `ADR-038` in
  `Implementation/Architecture/ADR.md` (approve, or redirect and re-run
  `/plan-tasks`), paying particular attention to the "propose" deviation
  (Decision point 6/7 and its own "Alternatives Considered" entries) —
  then let the decomposer's own already-produced tasks proceed, or reset
  `status:`/`gate:` on this story first if a different scope is chosen.
  → `Implementation/UserStories/REQ-SB-49-US-02-cockpit-person-mention-proposed-note-edit.md`

  **Coder update (2026-08-14, `SPRINT-046`, `/implement-sprint`):** all 6
  tasks built and verified live, end-to-end, real vault/real model calls
  — `ADR-038` held up EXACTLY as designed: Supervised mode's existing
  Pending-Approval Approve/Decline confirmed gated and un-auto-applying
  (`T04`); Manual/Autonomous's new "propose" in-thread confirm/discard UI
  confirmed real, never a silent write (`T02`/`T05`/`T06`, driven through
  the actual running Cockpit chat via a real CDP browser session). No
  adr-deviation trigger fired; this is new evidence for the still-pending
  human review, not a substitute for it — this item stays open. Two real,
  live-discovered integration bugs were found and fixed in-scope (a
  missing `SKILLS["tool"]` field; a `threads.send_user_message` save race
  clobbering a mid-loop-created proposal) — full writeups in `T01`'s/
  `T02`'s own Implementation Logs.

- [ ] 2026-08-14 · **REQ-SB-48-US-01-T01** · AC-09 verified via a scoped monkeypatch, not a real still-real-Action agent (none currently exists)
  Plain English: this task's own Tests block for AC-09 asks to call `list_agent_capabilities` on a real agent that has at least one still-real (non-migrated) Built-in Action. Live-checking all 7 real agents found none qualify any more — `SPRINT-031`/`REQ-SB-39-US-02` (already `Done`, prior work) migrated every formerly-hardcoded mutating Action id into `skill_tools.SKILLS` itself, so the action-kind branch now empties to `[]` for every real agent. Verified the AC honestly instead via a scoped, in-process, fully-reverted monkeypatch of `agent_registry.get_agent` (adds one fabricated action-kind entry to a real agent's real dict), confirming the real, unmodified `list_agent_capabilities` never attaches a `"tool"` key to an action-kind row while every skill-kind row carries the correct one. AC itself passed; only the verification precondition/technique differs from the task's own prose.
  **What to do:** spot-check this verification-technique substitution is acceptable (no code change needed — the underlying AC-09 guarantee is structurally true by the code's own shape, confirmed live). No action required unless a real still-real-Action agent is wanted for a stronger future check.
  → `Implementation/Tasks/REQ-SB-48-US-01-T01-skills-tool-field.md`

- [ ] 2026-08-14 · **BUG-013** · recommend `/triage` batching — a real, pre-existing, self-healing revoke bug on 7 migration-seeded Skill/agent pairs
  Plain English: found live during `REQ-SB-48-US-01-T02`'s own AC-06 verification (out of that task's scope to fix, confirmed via a UI-free Python-shell repro too). `skill_registry._load_state()` re-applies `_MIGRATION_GRANT_SEED` on every state read, so revoking `view_last_run`/`ask_question`/`view_channel_status`/`run_capture_now`/`pause_schedule`/`rebuild_person_note`/`build_knowledge` from one of the specific agents that seed named at migration time never actually sticks — it silently reappears granted the moment anything else reads state next.
  **What to do:** run `/triage BUG-013` to batch it into a `BUGFIX-NN-US-01` fix story (recommended direction: make the seed apply once, e.g. a persisted `"migration_seed_applied"` flag, rather than unconditionally on every `_load_state()` call).
  → `BUGS.md` → BUG-013

- [ ] 2026-08-14 · **REQ-SB-48-US-01-T02** · spot-check 2 scope-internal judgement calls (mode="select" minimal implementation; BUG-013 finding)
  Plain English: all 9 locked ACs passed live verification (see the task's own Implementation Log). Two things flagged for a human look, neither blocking: (1) `SkillsTree.tsx`'s `mode="select"` branch was given a small, real, working implementation (checkboxes + `selectedIds`/`onChange`, no API call) rather than a no-op stub, on the reasoning this is a stronger "extractable" seam for `REQ-SB-46-US-01-T04` (SPRINT-043) to build on — that story remains free to change its own selection semantics. (2) Live AC-06 verification found `BUG-013` (see its own REVIEW-QUEUE entry above), a real, pre-existing, out-of-scope bug — verified AC-06 honestly using a non-affected Skill/agent pair instead.
  **What to do:** confirm the `mode="select"` seam shape is acceptable for `SPRINT-043` to build on (or redirect before that sprint starts); no other action needed — `BUG-013` already has its own queue entry.
  → `Implementation/Tasks/REQ-SB-48-US-01-T02-capabilities-tool-tree.md`

- [ ] 2026-08-14 · **SPRINT-043** · skim the sprint retrospective and harvest learnings
  Plain English: SPRINT-043 (REQ-SB-46-US-01, Agent Creation Wizard
  Redesign) is Done — all 5 tasks built and all 11 locked ACs verified
  live. The coder drafted a Retrospective (sizing accuracy, what
  worked/didn't, patterns/antipatterns, open follow-ups) in the sprint
  file, but does not write `Implementation/Learnings.md` directly.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" and "Antipatterns
  to avoid" entries into `Implementation/Learnings.md`. Note the CDP
  `Runtime.evaluate` IIFE-wrapping finding — likely a durable, reusable
  fix for this project's own established CDP-driver technique going
  forward, not story-specific.
  → `Implementation/Sprints/SPRINT-043-agent-creation-wizard-redesign.md`

- [ ] 2026-08-14 · **REQ-SB-46-US-01** · spot-check 2 scope-internal judgement calls (all-4-steps-built-together sequencing; Expert's own optional Step-3 Skills grants)
  Plain English: all 11 locked ACs passed live verification across
  `T01`-`T05` (see each task's own Implementation Log), including a real
  regression check against today's shipped wizard for all 3 agent types
  (Expert cross-checked byte-for-byte against a parallel direct-API-call
  agent). Two things flagged for a human look, neither blocking: (1) the
  coder built all 4 steps of `CreateAgentWizardModal.tsx` in one coherent
  pass rather than as 5 separate non-compiling intermediate checkpoints
  (disclosed reasoning in `T02`'s own Implementation Log — this project's
  own `noUnusedLocals`/`noUnusedParameters` `tsconfig` options would
  otherwise trip on temporarily-unused imports for no real benefit, since
  Vite's dev-time transform doesn't type-check); every task is still
  verified and marked `Done` independently, strictly against its own
  locked ACs. (2) `T05`'s coder extended Expert's own submit handler to
  also grant any Step-3-selected Skills (mirroring Worker's/Producer's own
  shape) since Step 3 makes Skills selection genuinely available to Expert
  too (Scenario 5) — no locked AC's own literal wording states this for
  Expert specifically, but leaving a real Expert Skill selection silently
  discarded at submit time would be a genuine UX gap; the change is a
  structural no-op (zero calls) for AC-07's own literal 0-selected-Skills
  Expert test case, so it does not affect that AC's own literal pass/fail.
  **What to do:** confirm both are acceptable (or redirect); no other
  action needed.
  → `Implementation/UserStories/REQ-SB-46-US-01-agent-creation-wizard-popup-modal-redesign.md`
  → `Implementation/Tasks/REQ-SB-46-US-01-T02-step1-identity-type.md`
  → `Implementation/Tasks/REQ-SB-46-US-01-T05-step4-summary-trigger-submit.md`

- [ ] 2026-08-14 · **Prototype update (REDO): agents-map.html** · needs browser sign-off
  Plain English: this REPLACES the entry above's own prior pass — the
  operator reviewed pass 1 (a light reskin: 2 colors + a starfield layer +
  glass panels, keeping the existing bounded canvas) and rejected it as too
  conservative: "No No I want to Copy everything The Layout the Animation
  the Looks and Colors Forget what we have." This redo is a real rebuild of
  the visual/animation system against a second, deeper extraction of the
  reference site's own real CSS source (4 `<style>` tags read directly from
  its DOM — see PRD `REQ-SB-52`'s own "Update, 2026-08-14 — operator
  escalation" breadcrumb for the full verbatim value list), not another
  accent layer on top of pass 1. Every existing interaction/data structure
  (Section-Hub drill-down, cluster markers, the agent detail side panel and
  its tabs/chat/history, the entrance animation, all 6 state-switcher demo
  states, every data-agent-id/data-section-id wiring, agents-map.js) is
  STILL UNTOUCHED — this pass is CSS-only plus one small, generic, additive
  markup block (new edge-navigation chevrons).
  What actually changed structurally this time (not just recolored):
  (1) **True full-viewport canvas** — `.agents-map-stage` is now
  `position:fixed; inset:0`, filling the screen edge-to-edge (was the
  bounded/padded box pass 1 kept), achieved via stacking-context math alone
  (negative z-index within the app-shell's own context) so the page's
  static chrome — h1/description/state-switcher/legend/sidebar — floats
  over it for free, with zero HTML restructuring; (2) **full real palette**
  (`--bg:#0E1118`, `--ivory:#E9E4D6`, `--ivory-2:#B9B4A6`, `--ink-2:#8A8DA0`,
  `--ink-3:#565A6E`, `--copper:#C58B5F` accent, `--line`, `--glass`) —
  accent is now the reference's own real copper, replacing pass 1's
  invented emerald green entirely; (3) **real node entrance/interaction**:
  `nodepop` staggered bounce pop-in (exact `cubic-bezier(.2,.9,.3,1.4)`,
  reusing each node's own pre-existing inline `animation-delay` — no HTML
  edit needed there), a hover/selected glow reusing the renamed `livepulse`
  keyframe (was `agentActivityGlow`, same color-mix() recipe, REQ-SB-42 —
  pure rename for traceability, zero behavior change), a self-drawing
  `drawline` for connector lines (SVG `stroke-dashoffset` animates to 0),
  and a slow spin+drift (`hspin`, applied to the KB's own inner mesh so it
  can't be clobbered by agents-map.js's existing inline transform control);
  (4) **real glass blur**: side panel/card bumped 14px → 16px; zoom toolbar
  14px → 12px, repositioned from absolute/left/bottom to fixed/right/bottom
  (the reference's own real toolbar position); (5) **new**:
  `.map-edge-nav` — fixed, vertically centered, hover/focus-revealed,
  `chevnudge`-animated chevron pair, added once per state's own
  `[data-agents-drilldown]` group (5 insertion points), disabled/inert,
  same convention as the zoom toolbar's own buttons — the one genuinely NEW
  element this pass adds; (6) **typography**: h1 now real
  27px/.12em-letter-spacing/400-weight Plus Jakarta Sans (was unstyled
  default); Marcellus (the reference's own second loaded font) adopted for
  the sidebar's "Second Brain" wordmark only.
  GENUINELY OPEN, flagged, not silently decided (in addition to the
  still-open items from pass 1's own note, which stand unchanged — derived
  surface/warning/success/danger shades): (a) the connector-line `drawline`
  uses one shared dasharray (not per-line computed length) and isn't
  tightly synced to agents-map.js's own `playIntro()` timing — for the
  intro-animated states it will typically already read as fully drawn by
  the time the line reveal fires; (b) `hspin`/`hdrift` are folded into one
  combined keyframe (CSS can't cleanly run two animations on the same
  `transform` property); (c) the circular canvas is sized against
  `min(92vw, 92vh, 820px)` rather than literally matching the reference's
  own unbounded/pannable plane — chosen to preserve every existing
  hand-computed polar-grid position exactly (real pan/zoom stays out of
  scope); (d) the Marcellus wordmark placement is this designer's own
  proposal, not extracted/confirmed from the reference. Full rationale for
  every value: `agents-map.html`'s own top-of-file breadcrumb (2026-08-14
  REDO revision) and `styles.css`'s own rewritten "Agents Map
  SkillTree-inspired dark theme (REQ-SB-52)" section.
  **What to do:** open `html-prototype/agents-map.html` in a browser (a
  real HTTP server, not `file://` — `tools/run-prototype.cmd`) and confirm:
  the canvas now fills the full viewport edge-to-edge behind the floating
  h1/description/state-switcher/legend/sidebar chrome (no clipping/
  overlap); the copper accent, exact starfield twinkle, node pop-in stagger,
  connector-line draw-in, KB spin/drift, and hover glow all read correctly;
  every existing interaction still works exactly as before (Hub click →
  drill-down zoom, cluster-marker click → scoped drill-down, agent click →
  side panel with working tabs/chat/history, "Replay intro"); the new
  hover-revealed edge-nav chevrons appear inside each drill-down group; the
  zoom toolbar now sits bottom-right with a visibly heavier blur. Confirm
  or redirect the open proposals above (this pass's own (a)-(d), plus
  pass 1's still-open derived-shade note). Once approved, run
  `/spec REQ-SB-52`.
  → `html-prototype/agents-map.html`
  → `html-prototype/styles.css`
  → `Documentation/PRD.md` (REQ-SB-52)

- [ ] 2026-08-14 · **Prototype rebuild (NEW comparison artifact): agents-map-skilltree-exploration.html** · needs browser sign-off
  Plain English: this does NOT replace either entry above — the redo pass
  (immediately above) was live-verified by the orchestrator (not the
  designer role, which has no browser tools) directly in a running preview
  and found genuinely broken: the page's own intro paragraph/demo-state
  badges/legend (still in normal document flow, untouched by that pass) now
  render underneath the enlarged full-viewport canvas, producing unreadable
  overlapping text ("Q&A Hub / 3 AGENTS" tangled with "Worker ring
  (outermost)…") AND blocking clicks — confirmed via `elementFromPoint` that
  clicking the visually-rendered Capture Hub node actually hit `<main>`, not
  the node. Root cause: the stacking-context trick that makes the canvas
  full-viewport was never paired with repositioning the legacy intro-copy
  block, so the two now occupy the same screen region.
  Reported to the operator with this finding; independently, the operator
  escalated further and rejected the reskin approach itself as too shallow:
  "The Design is still Far off from the site I Showed you, Build the same
  exact layout understand the Intro outro and then we will see how can we
  move what we have there in a Sprint." Confirmed with the operator before
  building: since the reference (skilltree.altari.ai/explore) is a live paid
  commercial product with its own copyrighted markup/CSS/copy, this file
  matches its STRUCTURE/LAYOUT MECHANICS/ANIMATION LANGUAGE only — every
  class, CSS value, and word of copy is an ORIGINAL implementation, not
  copied from the reference's own source or text (the operator confirmed
  this scope explicitly: "Yes, original code + our content"). The
  reference's commercial-only elements (email-gated intro, a "Founding
  Cohort $49/mo" pricing dialog, an agency-upsell dialog, analytics hooks)
  are dropped entirely.
  What this file is (a genuinely different container/layout model, not
  another layer on the same one): no `.app-shell`/`.sidebar` — a full-
  viewport takeover (structural fix for the overlap bug: a fixed canvas and
  in-flow page chrome sharing one screen collide by construction, so here
  there is no separate in-flow chrome to collide with); a small topbar
  (fullscreen toggle, a functional Ctrl/Cmd+K agent search palette, a
  wordmark linking back to the app, live counts); one overview showing all 3
  real Sections (Capture/People/Knowledge Q&A, same 5-agent fixture the
  canonical screen already uses) as small "mini" trees around the central
  Knowledge Base — clicking a Section's Hub focuses it full-size with
  labeled agent nodes while the other two shrink to dim satellites, and
  edge-navigation chevrons page directly between Sections without returning
  to the overview first; a floating, closable detail card (bottom-right,
  matching the reference's own floating-card mechanic, not this app's
  existing full-height edge drawer) with the same real per-agent Settings/
  Actions/Chat content the canonical screen already established
  (REQ-SB-18/19/20/21); a real intro splash (own copy, no email field) and a
  doctrine/outro panel (own content — this app's actual Producer/Worker/
  Expert/Knowledge-Base rules, opened via the controls' `?` button); zoom/Fit
  controls stay disabled/visual-only, same established convention as the
  canonical screen.
  Verification note: the Browser pane's screenshot tool proved unreliable
  for this file (a previously-documented limitation this session, not a
  page bug) — a screenshot showed content clustered near the top-left at a
  fraction of its real size, while `getBoundingClientRect()`/computed-style
  inspection independently confirmed every element (the Knowledge Base, all
  3 Section trees, all 5 agent nodes) rendering at its correct real-pixel
  position and size. The automation tool's own synthetic mouse clicks also
  did not reliably land (confirmed via `elementsFromPoint` that the target
  button WAS correctly topmost at the exact click coordinate, yet the
  click's effect never fired) — worked around by dispatching real `.click()`
  calls directly (which exercise the identical event-listener code path a
  genuine click would) and confirming each resulting DOM/CSS state via
  `getComputedStyle`. Verified this way: intro dismiss; Section focus
  (`data-focused` attribute, `.is-focused` class, world recentering
  transform, edge-nav labels) for all 3 Sections; back-button unfocus;
  chevron cycling in both directions; detail-card open/close with the
  correct per-agent content; search open, live filtering (query "meeting"
  correctly narrows to only Meeting Capture), and select-to-open-card; about
  panel open/close. Zero console errors throughout. **Not independently
  confirmed with a real mouse in this session** — flagged, not silently
  assumed equivalent to a human click.
  GENUINELY OPEN, flagged, not silently decided:
  (a) whether this full-viewport takeover model should replace
  `agents-map.html` in place, or stay a separate "focused workspace" mode
  reachable from it — this file is the comparison artifact for that
  decision, same role `agents-map-exploration.html` played for BUG-002;
  (b) wiring this screen to the real agent/Section data model is explicitly
  deferred to a future Sprint, per the operator's own framing ("then we will
  see how can we move what we have there in a Sprint") — today it is static
  HTML matching the same 5-agent fixture every other state on the canonical
  screen already uses;
  (c) ~~the exact palette/animation-timing values... are this
  orchestrator's own original choices... not extracted/copied values~~ —
  SUPERSEDED by the update below; no longer accurate for palette/fonts/KB
  ring/card panel.
  **What to do:** open
  `html-prototype/agents-map-skilltree-exploration.html` in a browser (a
  real HTTP server, not `file://`) and confirm the layout/interaction model
  reads as intended, then decide (a) above. Once approved, decide whether to
  fold this into `/spec REQ-SB-52` as its locked design, and scope the
  future data-wiring Sprint per (b).

  **Update, 2026-08-14 (same day, operator follow-up):** "One note I like
  the Style of the KB they have in the Tree Site Use it Better than that one
  we have Same for the Agents and how he structure the Agents in the map
  (not all the same size or in the same line). and DO the Design with 6
  Sections and Copy the the Fonts and The Agents Style (There is no Copy
  Rights here) same as for the Panels that Open for the Agent." Three
  changes made in response, all live-verified:
  (1) the operator's own correction on fonts is right — a font-family NAME
  (Plus Jakarta Sans, Marcellus, both open-license) isn't the reference's
  exclusive IP the way source code or marketing copy is — so palette/fonts/
  card panel/KB ring now re-point to the SAME real values already verified
  live from the reference's own `:root` custom properties and `#card`/
  `.leaf` computed styles (identical to what the canonical screen's own
  `.theme-skilltree` section already uses); the CSS rules/selectors
  themselves are still this file's own independent implementation, no
  copy-pasted source text, no reused copy/marketing text — that boundary
  still stands;
  (2) investigated the reference's real node positioning directly: `.jdot`/
  `.leaf` are FIXED-size circles (15px/20px, confirmed via computed style on
  live elements) — size does not vary per node; what varies is POSITION
  (real per-node coordinates are JS-computed tree-layout offsets, confirmed
  irregular via several elements' own inline `left/top` px values, not a
  hand-symmetric fan). Applied that: Capture's 3 agent nodes now sit at
  deliberately uneven radius (~74-84px)/angle from their Hub instead of an
  exact symmetric 3-way fan — flagged as an honest match (organic scatter),
  not an invented size-variance embellishment the reference doesn't actually
  have either;
  (3) expanded from 3 to 6 Sections — Capture/People/Knowledge Q&A
  unchanged (still the real 5-agent fixture) plus Sales/Products/Technical,
  genuinely empty (Scenario 7, same convention the canonical screen's own
  "5 sections" state already established for these same names), hexagonal
  layout (angle = idx/6*360-90, radius 32) — the 3 real Sections land at the
  exact same angles the 3-Section layout already used, so only the 3 new
  empty Hubs and their focus-recenter rules are additions.
  Live-verified (same DOM/computed-style method as before — screenshots
  still unreliable in this environment): all 6 trees render at correct
  hexagonal positions (confirmed via `getBoundingClientRect`); empty
  Sections correctly flagged (`.skillmap-tree-hub--empty`, 0 agent nodes);
  focus + edge-nav chevron cycling correctly loops through all 6 in order
  (sales → people → products → qa → technical → capture → sales); zero
  console errors. **What to do:** re-review with this update in mind — the
  KB ring/card panel/font values are no longer this orchestrator's own
  invention, they're the same real extracted values as the canonical
  screen's redo pass.
  → `html-prototype/agents-map-skilltree-exploration.html`
  → `html-prototype/agents-map-skilltree-exploration.js`
  → `html-prototype/styles.css`

- [ ] 2026-08-15 · **SPRINT-047** · skim the sprint retrospective and harvest learnings
  Plain English: SPRINT-047 (REQ-SB-52-US-01, app-wide dark palette + real
  Plus Jakarta Sans / Marcellus typefaces via a `tokens.css`-only swap) is
  Done — its one task built and verified live against all 6 real app
  routes (screenshots, computed-style, and network evidence for every
  locked AC). The coder drafted a Retrospective (sizing accuracy, what
  worked/didn't, patterns/antipatterns, open follow-ups), but does not
  write `Implementation/Learnings.md` directly — that's a human step. One
  unrelated, pre-existing backend finding also surfaced during live
  verification (`GET /system-health` → real `500`, no backend file
  touched by this task) — filed as an Open follow-up in the retro, not a
  blocker on this sprint.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" and
  "Antipatterns to avoid" entries into `Implementation/Learnings.md`.
  Separately, consider a `/bug` capture for the `/system-health` `500`.
  → `Implementation/Sprints/SPRINT-047-app-wide-dark-palette-and-typeface-swap.md`

- [ ] 2026-08-15 · **REQ-SB-53-US-01 + US-02 + US-03** · review new `ADR-040` (Capture Pipeline Split — Pull/Tag/Link/Store agent stages) before the decomposer's tasks are built
  Plain English: the architect pass wrote `ADR-040`, resolving the two real
  design questions the PRD and all 3 `REQ-SB-53` stories left open: how a
  4-stage, 4-agent-identity capture pipeline (Puller/Tagger/Linker/Storer,
  per capture type) shares one atomic in-process run, and how the existing
  single-call `skill_registry.invoke_skill` gate composes with a pipeline
  that must now genuinely SUSPEND mid-run when one stage is Supervised
  while others are Autonomous. The decision: a new shared, capture-type-
  agnostic `app/business/capture_pipeline.py` orchestration engine
  (mirroring the Cockpit's own `app/business/cockpit/` shared-module
  precedent, `ADR-036`) that (1) gates each stage independently at
  per-tick/batch granularity, generalizing `ADR-018` point 4's already-
  Accepted 2-block background-tick gate to 4 blocks — deliberately NEVER
  routed through `invoke_skill`, which stays completely untouched; (2)
  implements the locked partial-failure rollback outcome via a buffered/
  deferred per-item history commit (a new additive `"reverted"` history
  kind), never an immediate-write-then-mutate, since history is
  append-only (`ADR-018` point 7); (3) resumes a Supervised-suspended
  pipeline via one new `pending_approvals_router.py` Approve branch,
  reusing the existing `trigger="background"` per-tick idempotency-dedup
  guard verbatim rather than inventing per-item approval granularity.
  Each of the 3 sibling stories' own real capture-type-specific logic
  (Compass-vs-majority-vote Tag, EntryID-vs-recompute dedup, a narrower
  no-Person-linking Link stage for To-Do) stays untouched inside each
  type's own existing file, plugged into the shared engine as plain stage
  functions — the engine itself carries zero capture-type-specific logic.
  All 3 stories are `gate: flagged` (trigger-3) as a result, but per the
  pipeline contract this does not halt the pipeline — the decomposer runs
  next so the human reviews `ADR-040` and the resulting tasks together in
  one pass.
  **What to do:** review `ADR-040` in
  `Implementation/Architecture/ADR.md` (approve, or redirect and re-run
  `/plan-tasks`) — in particular the two design calls it makes with no
  operator-resolved precedent to lean on: batch-level (not per-item)
  Supervised-stage Pending Approvals, and the new `"reverted"` history
  entry kind. If approved as-is, no further action needed before the
  decomposer's tasks proceed to `/plan-sprints`/`/implement-sprint`.
  **Update, 2026-08-15 (mid-flow reconsideration, `ESCALATIONS.md` →
  `ESC-036`):** before the decomposer ran, the operator directly asked
  whether this ADR's own hand-rolled mechanism should instead be built on
  LangGraph's checkpointer + `interrupt()`/human-in-the-loop primitive
  (`langgraph` is already a real, installed dependency, `ADR-015` — this
  was never a new-dependency question). Reconsidered directly and
  concretely (not by reflex citation of the old, already-superseded
  "no orchestration framework" MEMORY entry) — **`ADR-040` is unchanged;
  the mechanism stays fully hand-rolled.** Full reasoning (this project
  already declined a LangGraph checkpointer twice on the record via
  `ADR-015` point 6/Consequences; genuine cross-restart durability here
  would need a new SQLite-backed checkpointer this project has repeatedly
  rejected; zero dynamic/LLM-driven branching exists for a graph engine to
  manage; a checkpointer would duplicate, not replace, the hand-rolled
  Pending-Approval bridging code) is now recorded directly in `ADR-040`'s
  own Alternatives Considered section. Reviewing `ADR-040` now also means
  reviewing this specific reconsideration, not just the original Decision.
  → `Implementation/UserStories/REQ-SB-53-US-01-email-capture-pull-tag-link-store-split.md`
  → `Implementation/UserStories/REQ-SB-53-US-02-meeting-capture-pull-tag-link-store-split.md`
  → `Implementation/UserStories/REQ-SB-53-US-03-todo-capture-pull-tag-link-store-split.md`
  → `Implementation/Architecture/ADR.md` → ADR-040
  → `ESCALATIONS.md` → ESC-036


- [x] 2026-08-16 · **REQ-SB-56-US-01** · architect has proposed concrete
  fallback-link thresholds — operator needs to confirm or correct them
  before `T02` is built — RESOLVED
  Plain English: this story adds a Link-to-Thread Job to the existing
  meeting-capture Worker so a meeting genuinely part of an email thread
  shows up connected to it. The primary-strategy feasibility question was
  already RESOLVED — verified live 2026-08-16: 100/100 sampled real
  calendar items carried a non-empty `ConversationID` (the existing code
  just never reads it today — a code gap, not a data gap). **New, this
  pass:** the architect has now proposed concrete fallback-heuristic
  thresholds (`/plan-tasks` step 1, 2026-08-16) — attendee overlap clears
  at ≥2 shared attendees, OR exactly 1 shared attendee when that's the
  entirety of the smaller attendee list; date-range proximity clears when
  the meeting's start falls within 7 calendar days of the candidate
  Thread's own most recent message; BOTH bars required together; ties
  broken by higher overlap then smaller date gap then left unlinked.
  Grounded in this vault's own real observed thread cadence (a real
  7-day-spanning thread found during `REQ-SB-54-US-01`'s own
  ConversationID verification), not arbitrary round numbers. Full
  reasoning: `Implementation/Architecture/architecture.md` →
  "Meeting → Thread Linking — ConversationID Primary Strategy,
  Attendee-Overlap/Date-Proximity Fallback"; the story's own `## Notes`.
  No new ADR was needed (a parameter choice within the already-Accepted
  `ADR-042` data model, not a new architectural boundary).
  **What to do:** review the proposed thresholds in the story's own
  `## Notes` (and the architecture.md section above), confirm or correct
  them, then `/plan-tasks` can lock `T02`'s tasks against the confirmed
  numbers. Once confirmed, reset `gate:` to `clear`.
  → `Implementation/UserStories/REQ-SB-56-US-01-meeting-capture-and-thread-linking.md`
  → `Implementation/Architecture/architecture.md` → "Meeting → Thread Linking..."

  **Update, 2026-08-17 — Confirmed, gate reset to clear.** Operator
  accepted the architect's proposal as the working default (well-grounded
  in real vault data, not arbitrary) and authorized proceeding overnight
  on well-grounded proposals rather than blocking on each one. Added one
  standing constraint: the thresholds must be real config, not hardcoded
  constants. `/plan-tasks` step 2 (decomposer) now unblocked for `T02`.

  **Update, 2026-08-17 — Decomposer pass complete, RESOLVED.** 5 ACs
  locked (`AC-01`..`AC-05`); 3 tasks created (`T00 → T01 → T02`, acyclic):
  `T00` (live ConversationID re-verification, no code), `T01` (primary
  strategy), `T02` (fallback strategy, config-backed thresholds per the
  standing constraint above — new `meeting_thread_link_config.py` sibling
  store, mirrors `agent_prompts.py`/`working_mode_registry.py`). Story
  `status: Draft → Ready`, `gate: clear`. Story's stale Dependencies text
  (`REQ-SB-54-US-01`/`REQ-SB-55-US-01` shown `Draft`) corrected in place —
  both are `Done` in `BACKLOG.md`. **Not a new flag, but worth noting for
  the build loop:** `T00` is kept first in dependency order and is NOT
  treated as already answered by the 100/100 figure referenced above —
  its own task file requires an independently-executed, recorded live
  probe before `T01` proceeds; see the story's own "Decomposer pass"
  `## Notes` and `T00`'s own task file for the full reasoning.
  → `Implementation/UserStories/REQ-SB-56-US-01-meeting-capture-and-thread-linking.md`
  → `Implementation/Tasks/REQ-SB-56-US-01-T00-meeting-conversationid-verification.md`

- [x] 2026-08-16 · **REQ-SB-57-US-01** · architect has proposed a concrete
  "worth a History line" bar — operator needs to confirm or correct it
  before `T03` is built — **RESOLVED 2026-08-18: operator confirmed the
  proposal as-is directly, no correction. Story `gate: clear`.**
  Plain English: this story builds the Project/Customer Synthesizer
  mechanism that keeps Glimpse current and appends a History line only when
  something genuinely concludes (e.g. a Project closes). The PRD itself
  says directly (`REQ-SB-54` point 5) that the exact bar for "worth a
  History line" is left to the architect/decomposer to propose and the
  operator to confirm. **New, this pass:** the architect has now proposed
  a concrete Project `status` enum (`active|on_hold|won|lost|renewed`) and
  a transition-based trigger — a History line is appended only when
  `status` transitions INTO `won`, `lost`, or `renewed` (never on
  `active`/`on_hold`, never re-appended on repeat observation of an
  already-terminal value). `won`/`lost` together map onto the operator's
  own "a Project closes" example (a loss is as much a genuine conclusion
  as a win); `renewed` is the operator's own second named example
  verbatim. Most of this story (Glimpse regeneration, the
  ownership-enforcement rule, Background-amendment approvals) does not
  depend on this open question and can be built as specced; only the
  History-line trigger task (`T03`) is blocked on it. Full reasoning:
  `Implementation/Architecture/architecture.md` → "Project & Customer
  Synthesizer — the 'genuinely concludes' History-line bar"; the story's
  own `## Notes`. No new ADR was needed (a parameter choice within the
  already-Accepted `ADR-042` data model, not a new architectural
  boundary).
  **What to do:** review the proposed `status` enum and trigger rule in
  the story's own `## Notes` (and the architecture.md section above),
  confirm or correct them, then `/plan-tasks` can lock `T03` against the
  confirmed rule. Once confirmed, reset `gate:` to `clear`.
  → `Implementation/UserStories/REQ-SB-57-US-01-project-and-customer-status-synthesizer-agents.md`
  → `Implementation/Architecture/architecture.md` → "Project & Customer Synthesizer..."

- [ ] 2026-08-16 · **REQ-SB-54-US-01-T04** · spot-check one scope-internal
  assumption — Customer OKF directory/concept-file slug casing
  Plain English: `REQ-SB-54-US-01-T04` (`SPRINT-048`) is `Done` — the
  generic OKF directory-note-kind family and its Customer application were
  built and all 6 Test steps verified live. The task's own manual-test
  prose (Tests step 1) illustrates the resulting folder as
  `Work/Customers/acme-test-co/` (lowercase, hyphenated) for a customer
  named "Acme Test Co", but the actual implementation follows the
  codebase's already-established `_slugify()` precedent (used identically
  by `hub_note_path`/`meeting_note_path`/`person_note_path`/
  `thread_note_path`), which only strips filesystem-invalid characters —
  it does not lowercase or hyphenate spaces (that transform, `tag_slug()`,
  is reserved for Obsidian tag values only). Live-verified: for
  `"Acme Test Co"` the concept directory/file is literally
  `Work/Customers/Acme Test Co/Acme Test Co.md`, not `Work/Customers/
  acme-test-co/acme-test-co.md`. This choice was necessary for Constraints
  step 5's own required property (`hub_note_path(customer).stem ==` the
  new concept file's stem, so the existing inline wikilink resolves
  correctly regardless of which shape produced it) and matches the task's
  own illustrative implementation code, which reuses `_slugify()`
  verbatim — only the Tests section's own prose example used a
  lowercase-hyphenated string. No locked AC names an exact slug casing.
  **What to do:** confirm plain `_slugify()` (current codebase precedent,
  case/space-preserving) is the intended Customer/Project directory
  naming, or direct a switch to a lowercase-hyphenated slug (would need a
  small follow-up task, since `T05`/Project reuses the same generic
  family and would inherit whichever choice is confirmed here). No action
  required to unblock further work — `T05`/`T06` are unaffected either
  way.
  → `Implementation/Tasks/REQ-SB-54-US-01-T04-okf-directory-family-and-customer.md`

- [ ] 2026-08-16 · **REQ-SB-54-US-01-T05** · spot-check one scope-internal
  assumption — small private path-resolution helper, not in the task's own
  illustrative code
  Plain English: `REQ-SB-54-US-01-T05` (`SPRINT-048`) is `Done` — the
  Project directory-shaped note kind was built as five thin wrappers
  around `T04`'s generic OKF directory family and all 3 Test steps
  verified live. The task's own illustrative implementation code repeats
  `customer_directory_paths(customer)["directory"] / "projects"` inline in
  each of the four customer/project-taking functions; I instead factored
  that one-line computation into a private `_project_directory_root
  (customer)` helper called by all four, to avoid the same three-line
  duplication existing four times in one file. Not a behavior change — it
  still computes the identical value via `T04`'s own `customer_directory_
  paths` function on every call (never a separately-hardcoded path
  string, matching the task's own Constraints), and every one of the five
  public function names/signatures listed in the task's own `## Files to
  Modify` is unchanged from the illustrative shape. No locked AC is
  affected either way.
  **What to do:** confirm the private-helper factoring is acceptable (no
  action needed if so), or direct inlining the computation to match the
  illustrative code verbatim (a trivial follow-up edit if requested — no
  behavior change either way).
  → `Implementation/Tasks/REQ-SB-54-US-01-T05-project-directory-note-kind.md`

- [ ] 2026-08-16 · **REQ-SB-54-US-01** (`T04`, re-surfaced) · disclosed,
  deferred defect: `migrate_customer_to_partner` will silently no-op for
  any Customer onboarded after this story ships
  Plain English: `T04` (`SPRINT-048`) found, live, that `app/business/
  partner_hub_linking.py::migrate_customer_to_partner` (`REQ-SB-16`,
  `ADR-009`, already `Done`, a real shipped feature) locates a Customer's
  hub note to MOVE into `Work/Partners/` via the OLD flat-file
  `vault_writer.hub_note_path`/`hub_note_exists` primitives — which `T04`
  deliberately left untouched (per `ADR-042`'s own Alternatives, which
  reject generalizing the new OKF directory shape to Partner). Any
  Customer created AFTER `REQ-SB-54-US-01` ships gets ONLY the new
  4-file OKF directory shape, which `migrate_customer_to_partner` has no
  concept of — a real future reclassification of such a Customer will
  silently no-op its hub-note-move step instead of erroring or moving the
  right file. This was originally noted in the story's own decomposer
  pass (`## Notes`) as "flagged here and in `REVIEW-QUEUE.md`," but no
  standalone item was ever written for it — it was folded into the
  broader `ADR-042` human-review entry, which was then removed once the
  operator approved the ADR, taking this more specific disclosure down
  with it (see `SPRINT-048`'s own Retrospective → "What didn't work" for
  the retrospective note on this). Re-filed here as its own item, now
  that the story is fully `Done`, so it isn't lost.
  **What to do:** no action required to unblock any further work — this
  is a genuine, disclosed, low-probability-until-triggered future defect,
  not a current blocker. When convenient, either (a) file a `/bug` for it
  now so it's tracked ahead of the first real post-`REQ-SB-54` Customer→
  Partner reclassification, or (b) accept the risk and wait for it to
  surface organically, then `/bug` it at that point.
  → `Implementation/UserStories/REQ-SB-54-US-01-vault-knowledge-model-redesign.md`
  → `Implementation/Tasks/REQ-SB-54-US-01-T04-okf-directory-family-and-customer.md`
  → `src/backend/app/business/partner_hub_linking.py`

- [x] 2026-08-16 · **SPRINT-048** · skim the sprint retrospective and harvest learnings
  Resolved 2026-08-16 — operator reviewed the retrospective, one factual
  correction applied (the `migrate_customer_to_partner` REVIEW-QUEUE
  re-file, above), and the 3 Patterns + 1 Antipattern harvested into
  `Implementation/Learnings.md` under `## 2026-08-16 — SPRINT-048`.
  `SPRINT-048`'s own `gate` reset to `clear`. The two T04/T05 spot-check
  items and the `migrate_customer_to_partner` disclosure above remain
  separately open — not cleared by this item.
  → `Implementation/Sprints/SPRINT-048-vault-knowledge-model-redesign.md`
  → `Implementation/Learnings.md`

- [x] 2026-08-16 · **REQ-SB-63-US-01** · confirm the cross-cutting-update
  trigger mechanism before `T03` is built
  Resolved 2026-08-16 — operator confirmed Option B (Pending Approval,
  mirroring `ADR-021` point 5's already-proven create-then-finalize shape)
  after reviewing both candidates. Retrofit scope was already resolved
  during the `/spec` pass ("There is no Retrofit we Will Redo everything
  any way and replace it with pipeline"). Story `gate:` reset to `clear`;
  `T03` unblocked. Ready for `/plan-tasks`.
  → `Implementation/UserStories/REQ-SB-63-US-01-the-librarian-vault-expert-central-authority.md`

- [ ] 2026-08-16 · **REQ-SB-55-US-01** · review new `ADR-043` (Email
  Capture & Threading Pipeline) — the decomposer's 8 tasks (`T01`-`T08`)
  are now locked against this shape, story `status: Ready`
  Plain English: this is the first concrete Pipeline built under
  `ADR-041`'s directional Agent/Pipeline/Job/Hub taxonomy — it replaces
  the monolithic `email-capture` Worker with a real
  `Fetch`→`Classify`→`Thread-Match/Merge`→`Route-to-Project` chain (plus
  `Summarize-Attachment`/`Detect-Recurring-Pattern` branch Jobs) compiled
  to a `langgraph.graph.StateGraph`. `ADR-043` makes three concrete calls
  `ADR-041` itself deliberately left open: (1) the DAG lives as CODE in a
  new `app/business/pipelines/` subpackage, not yet a persisted/
  user-editable definition; (2) mid-pipeline human approval (the Thread→
  Project routing guess, the new-Pipeline proposal) is handled via the
  existing flat-JSON Pending Approval mechanism — deliberately NOT a real
  LangGraph checkpointer/`interrupt()` suspension, to avoid this
  project's first departure from flat-JSON `.second-brain/` persistence
  for a shape the existing mechanism already proves out; (3) one single
  new Agent-tier identity (`type: "worker"`) replaces `email-capture` 1:1
  — none of the six Jobs get their own Agents Map node, chat surface, or
  Working Mode. Worth a human look before the decomposer's tasks lock in
  around this shape, since it's the template every future Pipeline
  (Meeting-capture, To-Do) will likely follow.
  **What to do:** review `ADR-043` in
  `Implementation/Architecture/ADR.md`, approve or reject (a rejection
  is a new superseding ADR, not an edit), then run `/plan-tasks` again if
  you change it.
  → `Implementation/UserStories/REQ-SB-55-US-01-email-capture-and-threading-pipeline.md`

- [ ] 2026-08-16 · **REQ-SB-63-US-01** · review the architect's concrete
  design for "the deferred cross-reference write" (no new ADR — a
  material-assumption flag, not an ADR-review flag) — the decomposer's 3
  tasks (`T01`-`T03`) are now locked against this shape, story
  `status: Ready`
  Plain English: this pass confirmed, by direct inspection, that
  generalizing `vault_filing_expert.py`/`ADR-021` to a `REQ-SB-55` Pipeline
  Job caller needs no new ADR — it's the same plain-function composition
  three other real callers already use, and the new cross-cutting-update
  Pending Approval reuses `ADR-021` point 5's own dispatch pattern
  verbatim, already pre-authorized by that ADR's own Consequences. What
  the story itself did NOT specify is WHAT the approved write actually
  performs — this pass designed it: an additive, keyword-only
  `already_filed_path` parameter on `determine_placement_and_file` (so a
  Pipeline Job's already-placed content isn't redundantly re-filed), a new
  `cross_cutting_implication` field on the SAME model completion, and a
  new `finalize_cross_cutting_update` handler that writes an additive
  `customer/<slug>`/`partner/<slug>` TAG onto the already-filed note
  (never `captures.md`, which `ADR-042` reserves for operator-only writes).
  This tag is real, inspectable evidence today, but does not yet
  automatically feed a Glimpse regeneration — `REQ-SB-57` (still `Draft`)
  has not yet designed how its own Synthesizer discovers evidence, so
  whether it will read this specific tag convention is an honest, disclosed
  forward dependency, not something this pass could confirm.
  **What to do:** read "The Librarian — Vault Filing Expert generalized to
  a Pipeline-Job caller + cross-cutting-update detection" in
  `Implementation/Architecture/architecture.md`, confirm or correct the
  concrete write mechanism (the tag convention; the `already_filed_path`
  parameter shape) before the decomposer's tasks lock in around it — the
  decomposer runs next regardless (this flag does not halt the stage), so
  review alongside its own task breakdown in one pass.
  → `Implementation/UserStories/REQ-SB-63-US-01-the-librarian-vault-expert-central-authority.md`

- [x] 2026-08-16 · **SPRINT-049** · skim the sprint retrospective AND
  review `ADR-043` — TWO distinct items; only the retro-harvest half is
  resolved by this entry
  Retro-harvest half resolved 2026-08-16 — 4 Patterns + 1 Antipattern
  harvested into `Implementation/Learnings.md` under
  `## 2026-08-16 — SPRINT-049`. **The `ADR-043` human-review half remains
  open** (its own separate line item above, ~line 5375) — a rejection
  would be a new superseding ADR, not an edit; not resolved by this entry.
  → `Implementation/Sprints/SPRINT-049-email-capture-and-threading-pipeline.md`
  → `Implementation/Learnings.md`

- [x] 2026-08-16 · **SPRINT-050** · skim the sprint retrospective AND
  review the architect's designed cross-cutting-update write shape — TWO
  distinct items; only the retro-harvest half is resolved by this entry
  Retro-harvest half resolved 2026-08-16 — 4 Patterns + 1 Antipattern
  harvested into `Implementation/Learnings.md` under
  `## 2026-08-16 — SPRINT-050`. **The architect's designed write-shape
  review half remains open** (its own separate line item above, ~line
  5403 — `already_filed_path`/`cross_cutting_implication`/the
  `customer/<slug>`/`partner/<slug>` tag write) — not resolved by this
  entry.
  → `Implementation/Sprints/SPRINT-050-the-librarian-vault-expert-central-authority.md`
  → `Implementation/Learnings.md`

- [ ] 2026-08-16 · **REQ-SB-64-US-01** · confirm two open scope questions
  before `/plan-tasks` — retrofit scope, and the Hub-mediation mechanism's
  mechanical shape
  Plain English: this new story generalizes the already-shipped Section
  Hub concept (today: only cross-Section agent-to-agent HELP routing) into
  a real gateway that a Section's own pipelines/agents route their KB
  placement requests through before reaching REQ-SB-63's Librarian. The
  PRD itself left two things genuinely open: (1) whether this retrofits
  the ALREADY-shipped Email Capture Pipeline's existing Librarian-consult
  call site (an additive wrap around already-verified, currently-running
  code) or only applies to pipelines built after this story ships; (2)
  the concrete mechanism a Job would call through — this pass leans
  toward a new, plain, synchronous business-layer function (composed
  alongside `section_registry.py`, the same "compose alongside, don't
  reopen" shape this project already uses elsewhere) over a decorator/
  interceptor, but does not commit to it. Neither question was resolved
  in this drafting pass — no operator was available to confirm either
  one live, unlike the closely analogous `REQ-SB-63-US-01` retrofit
  question, which WAS resolved in-session. Left unresolved, `/plan-tasks`
  has no confirmed design to lock tasks against.
  **What to do:** read `## Notes` in the story file below — confirm or
  correct the retrofit-scope candidate (Option A: retrofit the shipped
  `consult_librarian` call site as an additive wrap; Option B: forward-
  only) and the mechanical-shape candidate (plain composed function vs.
  an alternative), then update the story's `## Notes` with the resolution
  and re-run `/plan-tasks REQ-SB-64-US-01`.
  → `Implementation/UserStories/REQ-SB-64-US-01-section-hub-kb-traffic-gateway.md`

- [x] 2026-08-16 · **REQ-SB-65-US-01** · pick the Job-tree data-source
  shape before `/plan-tasks` locks tasks against it
  Resolved 2026-08-16 (architect pass, `/plan-tasks` step 1) — Option A
  confirmed: a new, read-only endpoint inspecting the real, compiled
  `email_capture_pipeline.py` `StateGraph`, via `langgraph`'s own
  already-installed `Pregel.get_graph()` introspection API (verified
  directly against the installed `langgraph==1.2.11` package, not
  assumed). Jobs stay non-addressable; `ADR-043` point 6 stays intact,
  not reopened; no new ADR. See the new, separate line item directly
  below for the architect's own concrete-design review flag (a distinct
  item — this entry only resolves the option pick).
  → `Implementation/UserStories/REQ-SB-65-US-01-email-capture-pipeline-job-tree-visualization.md`

- [ ] 2026-08-16 · **REQ-SB-65-US-01** · review the architect's concrete
  endpoint/response-shape/frontend-merge design (no new ADR — a
  material-assumption flag, not an ADR-review flag)
  Plain English: this pass confirmed, by direct inspection of the
  installed `langgraph` package, that a read-only Job-tree endpoint needs
  no new ADR — `Pregel.get_graph()` already returns the real compiled
  graph's own nodes/edges, `ADR-043` point 6's "Jobs stay tier-less"
  decision is extended, not reopened. What the story/PRD did NOT specify,
  and this pass designed: a new `email_capture_pipeline.get_job_tree()`
  function; a new `GET /agents/{agent_id}/jobs` route (mirroring the
  existing `/agents/{agent_id}/history` shape) returning
  `{id, name, depends_on, section_id}` for `email-capture-pipeline`, `[]`
  for any other agent; a frontend adapter that reshapes each Job into an
  `AgentSummary`-compatible object and splices it into `layoutAgents()`'s
  own input list in place of the single pipeline agent entry, with zero
  changes to `layoutAgents.ts` itself. One sub-choice (fetch `/jobs` only
  for the known pipeline id, vs. for every agent and merge non-empty
  responses) was deliberately left open for the decomposer/coder, not
  decided here.
  **What to do:** read "Pipeline Job Tree Visualization — read-only
  `StateGraph` introspection" in
  `Implementation/Architecture/architecture.md` (and the mirrored
  resolution in the story's own `## Notes`), confirm or correct the
  concrete endpoint/response shape before the decomposer's tasks lock in
  around it — the decomposer runs next regardless (this flag does not
  halt the stage), so review alongside its own task breakdown in one
  pass.
  → `Implementation/UserStories/REQ-SB-65-US-01-email-capture-pipeline-job-tree-visualization.md`

- [x] 2026-08-16 · **REQ-SB-65-US-01-T02** · was `BLOCKED` — RESOLVED
  Resolved 2026-08-16 — operator decision: "Jobs always render, regardless
  of parent's flag." The spliced Job `AgentSummary` entries get
  `is_background_agent: false` hardcoded (not inherited); every other
  field stays inherited verbatim as originally designed.
  `email-capture-pipeline`'s own real registry flag is unchanged (still on
  `CrawlersPage.tsx`). Task's Constraints/Objective updated; task reset
  `Blocked → Ready`; story/sprint reset accordingly. See `ESCALATIONS.md` →
  `ESC-038` (Resolved).
  → `Implementation/Tasks/REQ-SB-65-US-01-T02-agents-map-job-tree-rendering.md`

- [ ] 2026-08-16 · **SPRINT-051** · skim the sprint retrospective AND
  review the architect's concrete endpoint/response-shape/frontend-merge
  design — TWO distinct items; the design-review item is the SAME open
  line item as `REQ-SB-65-US-01`'s own entry above (not a duplicate), only
  the retro-harvest half is new
  Plain English: `T02` rebuilt and re-verified `Done` after ESC-038's
  resolution — every task/story/sprint in this sprint is now `Done`. The
  coder drafted a Retrospective in
  `Implementation/Sprints/SPRINT-051-pipeline-job-tree-visualization.md`
  (`## Retrospective`), including the real ESC-038 detour as a genuine
  "what didn't work" finding — a stale AC premise ("the single opaque node
  it renders today") carried forward unchecked through `/spec`/
  `/plan-tasks` despite already being invalidated by an earlier,
  unrelated-sounding shipped change (`REQ-SB-51-US-01`'s Background Agent
  ring filter). 2 Patterns + 1 Antipattern drafted, awaiting harvest.
  **What to do:** skim the drafted Retrospective, harvest the
  Patterns/Antipatterns worth carrying forward into
  `Implementation/Learnings.md` (human-only step, per this project's own
  established convention); separately, the architect's own concrete
  endpoint/response-shape/frontend-merge design (`REQ-SB-65-US-01`'s own
  standing trigger-1 flag, unresolved, unchanged by this pass — see that
  story's own line item above) still awaits its own review, independent of
  this retro-harvest.
  → `Implementation/Sprints/SPRINT-051-pipeline-job-tree-visualization.md`
  → `Implementation/Learnings.md`

- [x] 2026-08-16 · **REQ-SB-66-US-01** · `/design` explicitly skipped
  (operator-directed); ESC-039 Resolved; one item remains, non-blocking
  Both prior blockers resolved same-day: `ESC-039` (Thread-Match/Merge/
  Detect-Recurring-Pattern omit the Prompt field entirely, rather than
  showing it inert) and the `/design` pass ("no more designer we will do
  it later build the needed ui we will fix it later" — the coder builds
  directly against the existing Settings `kv-list` visual language,
  revisited later if needed). **Still open, non-blocking:** the exact
  backend shape for resolving a Job click into a real, populated
  Settings-only detail view (Option A/B, story's own `## Notes`) — left
  for `/plan-tasks`'s own architect step, mirroring `REQ-SB-65-US-01`'s
  identical precedent. Story is otherwise ready for `/plan-tasks`.
  → `Implementation/UserStories/REQ-SB-66-US-01-real-editable-prompt-and-guardrails-placeholder.md`
  → `ESCALATIONS.md` (ESC-039)

- [ ] 2026-08-16 · **REQ-SB-66-US-01** · review new `ADR-044` (Job
  Settings addressability) — the decomposer's 7 tasks (`T01`-`T07`) are
  now locked against this shape, story `status: Ready`
  Plain English: the architect resolved the story's own open
  Job-Settings-detail-view question as Option A — a new, dedicated
  `GET`/`PATCH /agents/{agent_id}/jobs/{job_id}/settings` endpoint pair,
  paired with a genuinely separate, minimal frontend shell that
  `AgentsMapPage.tsx` mounts in place of `AgentDetailPanel` whenever the
  clicked Map node is a known Job id — never a widening of `agents_
  router.py`'s Agent-detail resolution or `AgentDetailPanel.tsx`'s shared
  tab machinery (Option B). Unlike `REQ-SB-65-US-01`'s own structurally
  similar Option A/B choice (which needed no new ADR — pure read, zero
  addressability change), this decision genuinely narrows two already-
  `Accepted` decisions: `ADR-041`'s own deferred "whether/how a Job earns
  its own surface" Consequence, and `ADR-043` point 6 ("Jobs stay
  non-addressable in every respect") — a Job becomes clickable AND its
  own Settings become editable/persisted for the first time. A new ADR,
  `ADR-044`, records this: a Job gains exactly ONE narrow, addressable
  surface (Settings — Prompt where a real call site exists, Guardrails
  always); every other facet (Chat, History, independent Working Mode,
  Schedule, Pending-Approval `agent_id`, Skills grant) stays exactly as
  `ADR-043` point 6 already established. A real, newly-found correction
  is also disclosed in `ADR-044`'s own Context: `AgentDetailPanel.tsx`'s
  real, current tab set has NO existing tab-REMOVAL mechanism (only an
  additive one, for Expert's own `'gaps'` tab) — the story's own Option B
  framing ("the same way it already varies tabs for `type === 'expert'`
  today") did not hold up against the real file.
  Decomposer pass, `/plan-tasks` step 2, 2026-08-16: all 10 scenarios
  locked (`AC-01`..`AC-10`), 7 tasks written — `T06` (backend endpoint)
  and `T07` (frontend shell) directly implement `ADR-044`'s Decisions 2/3
  and both carry `gate: flagged`/trigger-3 forward as their own
  breadcrumb. Every locked AC has ≥1 tagged verification step,
  `depends_on` is acyclic (including 2 real cross-story edges onto
  `REQ-SB-65-US-01-T01`/`T02`, both `Done`) — story `status` advanced
  `Draft → Ready`.
  **What to do:** review `ADR-044` in
  `Implementation/Architecture/ADR.md`, approve or reject, then reset the
  story's own `status`/re-run `/plan-tasks` if you change it — this flag
  does not block `/plan-sprints`/`/implement-sprint` from proceeding.
  → `Implementation/UserStories/REQ-SB-66-US-01-real-editable-prompt-and-guardrails-placeholder.md`
  → `Implementation/Architecture/ADR.md` (ADR-044)
  → `Implementation/Architecture/architecture.md` ("Universal Prompt
  Override + Guardrails Placeholder — Agents and Pipeline Jobs")
  → `Implementation/Tasks/REQ-SB-66-US-01-T06-job-settings-endpoint.md`
  → `Implementation/Tasks/REQ-SB-66-US-01-T07-job-settings-frontend-shell.md`

- [ ] 2026-08-16 · **REQ-SB-66-US-01** · still-standing trigger-1 —
  `compass_client.py`'s "various classify_* functions" scoped expansively
  to all 4 hardcoded-prompt functions, plus 2 disclosed dual-ownership
  calls deliberately left unwired — locked into `T02`, non-blocking
  Plain English: the PRD/story's own text names "compass_client.py's
  various classify_* functions" — read literally, that's only
  `classify_email`/`classify_task`. This pass (originally the analyst's
  own `/spec` finding, carried unresolved into `gate_reason` and now
  implemented by the decomposer's own `T02`) reads it expansively as all
  4 of that file's hardcoded-prompt-building functions
  (`classify_email`/`classify_task`/`guess_project_for_thread`/
  `summarize_content`) — narrowly matching only the two literally-named
  ones would arbitrarily leave the other two hardcoded despite being the
  exact same kind of gap the requirement's own motivating text names.
  Two further, disclosed scoping calls stay deliberately UNWIRED:
  `classify_recent_emails`'s own separate call to `classify_email` (a
  still-live, separate `/poc/classify-emails` manual path, not the real
  production `classify` Job); `skill_tools.summarize_file`'s own shared,
  cross-agent call to `summarize_content` (no single owning `agent_id`
  reaches that call site at all).
  **What to do:** confirm the "all 4 functions, 2 calls left unwired"
  scoping is the intended reading before/alongside `T02`'s own build;
  correcting it would mean re-scoping `T02`'s own Files to Modify, not a
  simple text edit.
  → `Implementation/UserStories/REQ-SB-66-US-01-real-editable-prompt-and-guardrails-placeholder.md`
  → `Implementation/Tasks/REQ-SB-66-US-01-T02-compass-client-prompt-override-wiring.md`

- [ ] 2026-08-17 · **SPRINT-052** · skim the sprint retrospective AND
  live-browser-confirm `T07`'s new Job-Settings shell — TWO distinct items,
  neither clears the two still-open `REQ-SB-66-US-01` entries above
  Plain English: `T07` (the sprint's final task) is built and `Done` — all 7
  tasks, the story, and the sprint are now `Done`. The coder drafted a
  Retrospective in
  `Implementation/Sprints/SPRINT-052-real-editable-prompt-and-guardrails-placeholder.md`
  (`## Retrospective`), naming the continued absence of a coder-side
  browser/screenshot tool as a real, standing gap (2 Patterns + 1
  Antipattern drafted, awaiting harvest). Separately: no browser tool was
  available to verify `T07`'s `JobSettingsPanel.tsx` by actually clicking a
  Job dot on the real Agents Map — every AC was instead proven via
  TypeScript/lint clean-checks, direct JSX reading, and real HTTP
  round-trips against both an in-process `TestClient` and the live dev
  backend (both returning identical, contract-matching results). The
  operator's own stated plan is to perform the live-browser click-through
  personally, exactly as already done for `T05`.
  **What to do:** skim the drafted Retrospective, harvest the
  Patterns/Antipatterns worth carrying forward into
  `Implementation/Learnings.md` (human-only step); separately, click a real
  Job dot (e.g. `classify`) and a real Agent dot (e.g. `vault-filing-expert`)
  on the live Agents Map to confirm `JobSettingsPanel`/`AgentDetailPanel`
  each render as `T07`'s own `## Implementation Log` describes. This item is
  independent of, and does not clear, the two still-open `REQ-SB-66-US-01`
  entries above (`ADR-044` review; the still-standing trigger-1
  `compass_client.py` scoping confirmation).
  → `Implementation/Sprints/SPRINT-052-real-editable-prompt-and-guardrails-placeholder.md`
  → `Implementation/Tasks/REQ-SB-66-US-01-T07-job-settings-frontend-shell.md`
  → `Implementation/Learnings.md`

  **Update, 2026-08-17 — Live-browser-confirm half done.** Clicked a real
  Job dot (`classify`) and confirmed `JobSettingsPanel` renders: no tab
  bar, heading "classify job", Settings-only body, Prompt/Guardrails rows
  both present and pre-populated with their real persisted values, edits
  commit via a real `PATCH /agents/email-capture-pipeline/jobs/classify/
  settings` round-trip. Also clicked `thread_match_merge` and confirmed
  the Prompt row is entirely absent (key-presence gated, matches AC-10/
  ESC-039) while Guardrails still renders and persists. Clicked a real
  Agent dot (`Vault Q&A`) afterward and confirmed the full 7-tab
  `AgentDetailPanel` still opens unchanged — the two panels branch
  correctly. All test values written during this check were reverted in
  `.second-brain/agent_prompts.json` afterward. The retro-skim/Learnings-
  harvest half of this item remains open (human-only step per CLAUDE.md).

- [ ] 2026-08-17 · **REQ-SB-56-US-01-T01** · `T00`'s own independent live
  ConversationID re-verification came back NEGATIVE — contradicts the
  100/100 figure the earlier (now-resolved) queue item above referenced;
  `T01` is blocked
  Plain English: `T00`'s task brief explicitly required an independently-
  executed, live, read-only COM probe this session — not a reuse of the
  architect's 2026-08-16 "100/100 non-empty" figure. That independent
  probe (37 real calendar items, the same window `list_calendar_events`
  already uses) found `ConversationID` genuinely usable on only 22/37
  (59.5%). The other 15/37 (40.5%) — every single one an
  `IncludeRecurrences`-expanded recurring-occurrence item
  (`IsRecurring=True`, `RecurrenceState` 2/3), the exact mechanism
  `list_calendar_events` already relies on to expand a recurring series
  into individual occurrences — return a broken, non-string value via
  both the `.ConversationID` convenience property (a bound-method object,
  raises `Member not found.` if invoked) and the raw MAPI
  `PropertyAccessor` fallback (`Type mismatch.`). This is a material
  fraction, not noise, and it's concentrated exactly on the recurring
  meetings this real calendar has several of (5 distinct recurring series
  in-window). It's also the THIRD independent live-confirmed instance on
  this Outlook installation of a per-item COM property breaking
  specifically on `IncludeRecurrences`-expanded occurrences (`EntryID` —
  `ESC-002`; `GlobalAppointmentID` — `ESC-012`; now `ConversationID`).
  Per `T00`'s own Constraints, this is NOT silently narrowed into a
  smaller scope — `T00` recorded the finding, filed `ESCALATIONS.md` →
  `ESC-040`, and set `REQ-SB-56-US-01-T01`'s own `status:` to `Blocked`.
  `T00` itself is `Done` — it performed its own job (probe + record)
  correctly regardless of the outcome.
  **What to do:** decide how the primary ConversationID-match strategy
  should treat recurring-occurrence meetings, since roughly 2 in 5 real
  meetings in this calendar are recurring occurrences that cannot use it
  as currently understood. Concrete options worth weighing (none decided
  here): (a) treat a non-string/non-empty-but-invalid `ConversationID` as
  absent and let those meetings fall through to `T02`'s fallback strategy
  only (the primary strategy still works for the 59.5% single-occurrence
  majority); (b) investigate whether reading the recurring series'
  master item's own `ConversationID` (rather than each expanded
  occurrence proxy) resolves it, before concluding the property is
  unusable for these meetings at all; (c) some other resolution. Once
  decided, resume `REQ-SB-56-US-01-T01` (reset `status:` from `Blocked`,
  update its own scope/Starting-State accordingly) via the normal
  `/plan-tasks`/`/implement-sprint` machinery.
  → `Implementation/UserStories/REQ-SB-56-US-01-meeting-capture-and-thread-linking.md`
  → `Implementation/Tasks/REQ-SB-56-US-01-T00-meeting-conversationid-verification.md`
  → `Implementation/Tasks/REQ-SB-56-US-01-T01-link-to-thread-primary-strategy.md`
  → `ESCALATIONS.md` → ESC-040

  **Update, 2026-08-17 — provisionally resolved overnight, spot-check
  requested.** No urgent human decision was available (operator asleep,
  own standing instruction: best-guess rather than block). Took Option
  (a) above: non-string/inaccessible `ConversationID` treated identically
  to absent, never fabricated into a link, falls through to `T02`'s
  fallback untouched — the safer, more conservative of the two concrete
  options, and zero new investigation scope. Option (b) deliberately NOT
  attempted (a real investigation question, not a safe default to guess).
  `T01` reset `Blocked → Ready` with a concrete scope addition (safe
  `""`-on-failure guard around the `ConversationID` read — see the task
  file's own updated Constraints/Tests/AC). `T01`/`T02` are proceeding to
  build under this resolution now. **What to do:** spot-check that Option
  (a) was the right call (vs. investigating Option (b) for better primary-
  strategy coverage later, as a fast-follow) once you're back — this is
  provisional, not a demand for immediate action.

  **Update, 2026-08-17 — `T01` built and `Done`.** `list_calendar_events`
  now returns a safe `conversation_id` (guarded via `try/except` +
  `isinstance(str)`, never the naive `list_recent_mail`-style `or ""`
  pattern); `_link_to_thread_by_conversation_id` added to
  `meeting_classification.py`. `AC-01` plus the new untagged
  ConversationID-safety check both verified — including a live spot-check
  against real, currently-broken recurring-occurrence items on this same
  installation (`Weekly Forecast l Strategic Clients` and 4 other recurring
  series `T00` originally found broken), which all safely resolved to `""`
  with zero exceptions. Full detail: `T01`'s own `## Implementation Log`.
  This does not resolve the still-open item above — the question of
  whether Option (a) itself (vs. investigating Option (b) later) was the
  right call remains a genuine open spot-check for you, unaffected by
  `T01`'s own completion. Also surfaced, incidentally, a separate
  pre-existing and unrelated bug worth a `/bug` capture: a real attendee
  resolves to an EX-style legacyExchangeDN address that
  `vault_writer.create_person_note_baseline`'s own filename slugify turns
  into an invalid Windows path, raising inside
  `people_extraction.ensure_person_note` on a real live
  `classify_recent_meetings` run — not caused by, and out of scope for,
  `T01`'s own change (worked around for `T01`'s own verification via a
  mocked calendar-event source instead).

  **Update, 2026-08-17 — `T02` built and `Done`; `REQ-SB-56-US-01` and
  `SPRINT-053` both now `Done`.** The fallback attendee-overlap +
  date-proximity strategy landed, config-backed (new
  `app/business/meeting_thread_link_config.py` +
  `.second-brain/meeting_thread_link_config.json`). All 5 of the story's
  own locked ACs are now verified. This item's own open question — whether
  the operator's overnight Option (a) resolution of `ESC-040` was the
  right call, vs. investigating Option (b) later — remains open and
  unaffected by the story/sprint reaching `Done`; `T01`/`T02` were both
  built correctly against Option (a) as given, which is a separate
  question from whether Option (a) itself should stand. `SPRINT-053`'s
  own drafted `## Retrospective` also awaits human propagation into
  `Implementation/Learnings.md` — it explicitly names this open spot-check
  as a follow-up. **What to do:** unchanged from above — spot-check
  Option (a) when convenient; also skim `SPRINT-053`'s own Retrospective
  and harvest anything worth carrying into `Implementation/Learnings.md`.

- [ ] 2026-08-17 · **SPRINT-054** · skim the sprint retrospective and harvest learnings
  Plain English: SPRINT-054 (REQ-SB-67, real per-Thread Summary synthesis
  for live capture + a one-shot backfill for already-captured Thread
  notes) is Done -- all 3 tasks built and verified live, all 6 locked ACs
  confirmed, including a real one-time backfill run against the
  operator's actual vault. The coder drafted a Retrospective (sizing
  accuracy, what worked/didn't, patterns/antipatterns, open follow-ups)
  in the sprint file, but does not write Implementation/Learnings.md
  directly -- that's a human step. Two items worth a closer look: (1)
  this story deliberately reversed a documented Constraint from the
  already-Done REQ-SB-55-US-01 story ("no second Compass call") via a
  new story rather than editing the Done one -- the architect pass
  confirmed no ADR was needed, and this worked cleanly in practice; (2)
  a real operational finding -- starting a second `uvicorn app.main:app`
  instance against a scratch VAULT_PATH unexpectedly triggers the real
  capture_scheduler against the REAL Outlook mailbox regardless of
  VAULT_PATH -- now recorded as a MEMORY.md Constraint, worth carrying
  into Learnings.md as a general "verification harness hygiene" pattern.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" and
  "Antipatterns to avoid" entries into `Implementation/Learnings.md`.
  → `Implementation/Sprints/SPRINT-054-real-thread-summary-synthesis-and-backfill.md`

- [ ] 2026-08-17 · **Performance/architecture finding** ·
  `run_capture_now` blocks the ENTIRE backend, not just its own request
  Plain English: manually triggered `POST /agents/email-capture-pipeline/
  actions/run_capture_now` tonight to double-check why the vault only had
  2 real Threads (it turned out the scheduler was already fully caught
  up — see the corresponding `MEMORY.md` entry, this is not a bug in the
  capture itself). While that request was running, the WHOLE app stopped
  responding — `GET /agents` and every other endpoint went unreachable
  for several minutes, confirmed via direct `curl`. Root cause:
  `_execute_action` (the sync dispatch path this action uses) calls its
  handler directly on the asyncio event loop with no thread-pool offload,
  so any slow real work inside it blocks every other request. The
  scheduled hourly runs hit the same code path but are usually fast
  (nothing new → early exit) so this hasn't been visibly disruptive
  before. Not fixed tonight — deliberately out of scope for an overnight
  investigation, and no story currently owns it.
  **What to do:** decide whether this is worth a real fix (move the
  handler onto a thread-pool executor, or make the underlying pipeline
  genuinely async) — likely worth it now that per-message Compass calls
  (`REQ-SB-67`) make manual/backlog runs meaningfully slower than before.
  → `Implementation/Architecture/architecture.md`
  → `MEMORY.md` → Constraints (same finding, full detail)
  **Update 2026-08-17:** now formally specced as `REQ-SB-68-US-01` — see
  the next entry below.

  **Update 2026-08-17 (architect pass, `/plan-tasks` step 1) — the root
  cause named above is corrected.** Direct re-reading of the REAL current
  `agents_router.py`/`skill_tools.py`/`skill_registry.py` found
  `_execute_action` is NOT actually the live call site — both of its own
  `_ACTION_HANDLERS` entries (`run_capture_now`, `build_knowledge`) are
  ALSO `skill_tools.SKILLS` members, so every real caller branches away
  from `_execute_action` before it is ever reached; it is confirmed dead
  code today. The REAL blocking path is `_invoke_capability` →
  `skill_registry.invoke_skill` → `_dispatch_skill` →
  `skill_tools.run_capture_now` — fully synchronous, no thread offload.
  The diagnosis ("the manual trigger blocks the event loop") was correct;
  the named function was not. Full correction and the fix's real shape:
  `ADR-045` in `Implementation/Architecture/ADR.md`, and the next entry
  below. See also the new, separate housekeeping entry below for the
  confirmed-dead-code finding itself.

- [ ] 2026-08-17 · **REQ-SB-68-US-01** · approve a prototype for the new
  Scheduling region before `/plan-tasks`
  Plain English: this story fixes the `run_capture_now` blocking bug
  above AND adds a new "Scheduling" section to the System Health page
  (per-job running/duration/outcome/error, for email-capture-pipeline,
  meeting-capture, and todo-capture). The Scheduling region has no
  covering `html-prototype/` screen today — confirmed by direct
  inspection of `system-health.html` and a repo-wide search for any
  scheduling-monitor UI region; none exists. The story itself is a clear
  `Draft` otherwise — both PRD-deliberate open scope questions (which
  jobs are covered; static vs. live-updating duration) are already
  resolved in the story's own `## Context`/`## Notes` with code-grounded
  reasoning, not left open.
  **What to do:** run `/design REQ-SB-68` to produce an approved
  prototype for the new Scheduling region (and decide there whether it
  replaces or coexists with the page's existing "Last capture run"
  section), then reset this story's `gate:` to `clear` (or otherwise
  resolve) so `/plan-tasks` can proceed.
  → `Implementation/UserStories/REQ-SB-68-US-01-non-blocking-capture-dispatch-and-scheduling-monitor.md`

  **Update, 2026-08-17 — `/design` skipped by direct operator decision,
  `gate` reset to `clear`.** Same standing precedent already set the
  same night for `REQ-SB-66`'s Job-Settings UI — a small, additive
  region on an already-existing page, not a net-new screen. `/plan-tasks`
  proceeding directly; the coder decides replaces-vs-coexists for the
  existing "Last capture run" section against this story's own ACs.
  Spot-check the resulting UI whenever convenient — not urgent.

  **Update, 2026-08-17 (architect pass, `/plan-tasks` step 1) — new
  `ADR-045`, `gate` set back to `flagged` (trigger-3, ADR created/
  changed).** Not a reopening of the design question above (still
  resolved, still clear) — a separate, later flag. Plain English: the
  architect found and corrected a real error in this story's own
  `## Context` (the named blocking function, `_execute_action`, is
  confirmed dead code — the REAL blocking path runs through
  `skill_registry.invoke_skill`/`_dispatch_skill` instead), decided the
  manual dispatch should join `agent_schedule_registry`'s shared lock
  (closing the race-condition risk the story left open), and designed the
  new `job_run_state.json` persistence + `GET /system-health` extension.
  This does NOT halt the pipeline — the decomposer still runs so a human
  reviews `ADR-045` and the resulting tasks together in one pass.
  **What to do:** review `ADR-045` in
  `Implementation/Architecture/ADR.md`, approve or reject, then run
  `/plan-tasks` again if you change it.
  → `Implementation/UserStories/REQ-SB-68-US-01-non-blocking-capture-dispatch-and-scheduling-monitor.md`

  **Update, 2026-08-17 (decomposer pass, `/plan-tasks` step 2) — all 7
  ACs locked (`AC-01`-`AC-07`), 4 tasks created (`T01`→`T02`→`T03`→`T04`,
  one linear `depends_on` chain), story advanced `status: Ready`, `gate`
  left `flagged`.** Still awaiting the same human review named above —
  now review `ADR-045` and `T01`-`T04` together in one pass, per
  `Implementation/Pipeline.md`. One disclosed, in-scope refinement of
  `ADR-045` point 4's own read-side wording: `get_job_run_states()`
  enumerates the 3 covered agent ids from `skill_registry.
  _MIGRATION_GRANT_SEED["run_capture_now"]` (the same real source
  `ADR-045` itself already names) and returns an honest `"has_run":
  False` placeholder for one with no run yet, rather than omitting it —
  avoids forcing the frontend to hold its own independently-hardcoded
  copy of the same 3-agent-id list, per tonight's own standing
  config-not-hardcoded directive. Same store, same write-side gate, same
  record shape — not a reopening of `ADR-045`'s own storage/mechanism
  decisions, see `T02`'s own task file for the full reasoning.

- [ ] 2026-08-17 · **Housekeeping finding (not story-blocking)** ·
  `agents_router.py::_execute_action`/`_ACTION_HANDLERS`/
  `_run_build_knowledge`/`_execute_async_action` are confirmed dead code
  Plain English: while grounding `REQ-SB-68-US-01`'s fix, the architect
  found that `_ACTION_HANDLERS`'s only two entries (`run_capture_now`,
  `build_knowledge`) are both also `skill_tools.SKILLS` members, and
  every real caller (`trigger_action`, `chat`,
  `pending_approvals_router.py`'s Approve endpoint) branches away to the
  Skills path before `_execute_action` is ever reached for either id.
  `agents_router.py::_run_build_knowledge`/`_execute_async_action` (its
  own async-handler counterpart) are equally unreachable — a real,
  already-working `skill_tools.build_knowledge` handler is what actually
  runs today. Left unfixed by `REQ-SB-68-US-01` (out of that story's own
  scope, minimal changes) — recorded here so it isn't silently lost.
  **What to do:** decide whether this is worth a small, standalone
  cleanup story (delete the four confirmed-dead functions/table entries
  from `agents_router.py`) — no functional risk either way, since nothing
  real calls them today.
  → `src/backend/app/api/agents_router.py`
  → `Implementation/Architecture/ADR.md` → `ADR-045` (Context, point 1 —
  full finding)

- [x] 2026-08-17 · **BUGFIX-03-US-01** · Resolved 2026-08-17 (architect,
  `/plan-tasks` step 1) — real gap-1 root cause found by direct code
  investigation
  Plain English: `BUG-014` said Thread email attachments are never
  captured because `outlook_com.py`'s email fetch "never reads a
  MailItem's Attachments COM collection at all." That was already
  confirmed wrong at `/triage` — `outlook_com.py` already extracts
  attachments fine. The architect pass has now found the REAL mechanism:
  `email_capture_pipeline.py`'s attachment node only writes a
  `## Attachments` line when an attachment is BOTH saved AND
  successfully summarized; an oversized attachment (over the 20MB cap) or
  one that can't be summarized vanishes with zero trace — no note line,
  no saved file, no log — which explains the real Thread's own missing
  section AND its missing `attachments/` folder from one confirmed cause.
  Corroborated by the still-live legacy email-capture path, which already
  has the "record it anyway, even unsaved" line the new pipeline lost.
  **What to do:** review the fix design in `architecture.md` → "Thread
  Attachment Capture — Silent-Loss Fix + Per-Message Collision Safety"
  and `BUGFIX-03-US-01`'s own `## Notes` before/alongside the decomposer's
  task-level review; one small residual item (confirming live which exact
  real-world variant — oversized cap vs. a OneDrive/SharePoint cloud
  link vs. a stale dev-testing timing artifact — applied to the specific
  historical Thread) is folded into `T01`'s own scope for the coder, not
  blocking.
  → `Implementation/UserStories/BUGFIX-03-US-01-thread-attachment-capture-and-collision-safety.md`
  → `Implementation/Architecture/architecture.md` → "Thread Attachment
  Capture — Silent-Loss Fix + Per-Message Collision Safety"
  → `ESCALATIONS.md` → `ESC-041` (`Resolved`, full write-up)

- [x] 2026-08-17 · **REQ-SB-68-US-01-T03** · Resolved 2026-08-17 —
  operator chose Option (a) (prune orphaned assignments inside
  `provider_registry.py::_load_state()`); fix built and live-verified,
  `T03` now `Done`
  Plain English: `T03`'s own code (compose `agent_schedule_registry.
  get_job_run_states()` into a new `"scheduling"` key) is built exactly
  per spec and verified correct in isolation, but `GET /system-health`
  itself was already crashing with a real `HTTP 500` before this task
  touched anything, and still does after. Root cause (confirmed via a
  real traceback, not guessed): `.second-brain/agent_providers.json`'s
  `"assignments"` map carries a stale key, `"email-capture"`, orphaned
  since `REQ-SB-55-US-01-T08`/`ADR-043` renamed that agent to
  `"email-capture-pipeline"` (already `Done`, unrelated prior story).
  `provider_registry.py::_load_state()` only ever adds new assignments,
  never prunes stale ones, so `system_health.py::_providers_with_agent_names()`
  (built by the already-`Done` `REQ-SB-31-US-01`) crashes on
  `agent_registry.get_agent("email-capture")["name"]` (`None["name"]`).
  Both real fix locations (`provider_registry.py`'s own reconciliation
  logic, or a defensive guard in `_providers_with_agent_names()`) are
  outside `T03`'s own `## Files to Modify` and explicitly outside its own
  `## Out of Scope` carve-out — not this task's fix to make. Left
  unfixed and undisturbed (not even the stale JSON data key was edited)
  per `Implementation/Pipeline.md` hard rule 5 (no improvisation outside
  declared scope).
  **What to do:** decide the fix shape — prune stale assignment keys
  inside `provider_registry.py::_load_state()`'s own reconciliation loop,
  or add a defensive None-guard inside `_providers_with_agent_names()` —
  then re-run `T03`'s own live verification (and unblock `T04`, which
  depends on it).
  → `Implementation/Tasks/REQ-SB-68-US-01-T03-scheduling-system-health-extension.md`
  → `ESCALATIONS.md` → `ESC-042` (full root-cause write-up)

  **Update, 2026-08-17 — Resolved.** Operator decision: Option (a) —
  `provider_registry.py::_load_state()`'s own reconciliation loop now
  prunes any `"assignments"` key whose agent id is no longer in
  `agent_registry.list_agents()`, symmetric with that same function's
  existing add-missing-assignment loop. Live-verified against the real
  running backend/vault: `.second-brain/agent_providers.json`'s stale
  `"email-capture": "compass"` key was confirmed present, then confirmed
  pruned automatically the next time `_load_state()` ran (triggered via a
  real `GET /system-health` call) — no manual edit of the JSON file. `GET
  /system-health` now returns a real `200` with the exact
  `{"mcp", "providers", "disabled_agents", "scheduling"}` shape, no
  `"last_capture_run"` key. `REQ-SB-68-US-01-T03`'s own 3 non-AC smoke
  checks (fresh/real-state placeholder shape, a real `running: true` →
  `finished` transition observed live through the endpoint with growing
  `elapsed_seconds`, and uncovered-action isolation) all passed. `T03`
  `status: Done`, `gate: clear`. Full evidence:
  `Implementation/Tasks/REQ-SB-68-US-01-T03-scheduling-system-health-extension.md`
  → `## Implementation Log`; `ESCALATIONS.md` → `ESC-042` (`Status:
  Resolved`). The story's own separate, standing `ADR-045` review flag
  (above) is untouched by this resolution.

- [ ] 2026-08-17 · **BUGFIX-03-US-01-T02** · recommend a `/bug` capture — `cockpit/attachments.py` now silently can't find attachments captured via `classify_recent_emails` after T02's own required per-message nesting fix
  Plain English: `T02`'s own fix (`write_attachments` now nests one level
  deeper per message) is correctly built and both locked ACs
  (`AC-01`/`AC-02`) are verified live and passing — this does not block
  `T02` or the story. But verifying it surfaced a real, previously
  unconsidered THIRD consumer of the old flat save-path convention:
  `app/business/cockpit/attachments.py` (Inbox Cockpit, live via
  `cockpit_router.py`'s attachment endpoints) hardcodes the OLD flat
  `Work/Emails/attachments/<note_stem>/<filename>` path when reading back
  attachments for `classify_recent_emails`-sourced email notes.
  `classify_recent_emails` is still live (`/poc/classify-emails`) and its
  own call site now (correctly) passes `message_segment=email["id"]`, so
  any future capture through that path leaves its attachments silently
  invisible to Cockpit (`list_attachments` returns `[]`, no error;
  `hand_off_attachment_to_chat` returns `not_found`, no error).
  Already-saved historical attachments are unaffected.
  **What to do:** run `/bug` to capture this as a new bug, then `/triage`
  it into a fix story once ready. Most plausible fix shape: thread
  `message_segment`/the email's own id into
  `cockpit/attachments.py::_attachments_dir`'s own path resolution
  (mirroring `write_attachments`'s new contract), or have Cockpit
  enumerate one level deeper instead of assuming a flat directory —
  genuinely open, not decided here.
  → `Implementation/Tasks/BUGFIX-03-US-01-T02-per-message-attachment-nesting.md`
  → `ESCALATIONS.md` → `ESC-043`

  **Update, 2026-08-17 — Resolved directly, same day.** Logged as
  `BUG-018` (`Closed`) and fixed immediately: `cockpit/attachments.py`
  gained `_iter_attachment_files`, supporting both the real historical
  flat shape and the new nested shape, chosen over threading
  `message_segment` through (Option (b), no new coupling needed since
  `classify_recent_emails` only ever writes one segment per note).
  Verified live against the real vault both directions. `ESC-043` is
  now `Resolved` in `ESCALATIONS.md`.

- [ ] 2026-08-17 · **SPRINT-055** · skim the sprint retrospective and harvest learnings
  Plain English: SPRINT-055 (REQ-SB-68, non-blocking manual capture
  dispatch + a real Scheduling monitor, bundled with BUGFIX-03-US-01/
  BUG-014's Thread-attachment fix) is Done — both stories, all 6 tasks
  built and verified live, matching the "~6 tasks, M" estimate exactly
  (the fifth consecutive sprint to land on-estimate). The coder drafted a
  Retrospective (sizing accuracy, what worked/didn't, patterns/
  antipatterns, open follow-ups) in the sprint file, but does not write
  `Implementation/Learnings.md` directly — that's a human step. Two
  patterns worth a closer look for `Learnings.md`: (1) grepping for calls
  to a shared save-path/data-shape PRODUCER function undercounts real
  consumers of its own CONVENTION — this sprint independently rediscovered
  that exact shape twice (`ESC-042`'s `provider_registry.py`/
  `system_health.py` JSON-key coupling; `ESC-043`'s `write_attachments`/
  `cockpit/attachments.py` path-shape coupling); (2) a bug ledger's own
  stated root cause should be re-verified by direct code reading at
  `/plan-tasks`, not trusted — `BUG-014`'s own gap-1 mechanism claim was
  confirmed false the very next stage (`ESC-041`). This sprint leaves one
  standing, non-blocking flag open: `REQ-SB-68-US-01`'s own
  `ADR-045`/trigger-3 human-review item. (`ESC-043`, the other flag this
  sprint opened, is now also Resolved — `BUG-018`, fixed same day, see
  the update on the entry above.)
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" and
  "Antipatterns to avoid" entries into `Implementation/Learnings.md`;
  separately, review `ADR-045` (independent of the retro harvest itself).
  → `Implementation/Sprints/SPRINT-055-non-blocking-capture-dispatch-and-thread-attachment-fix.md`

- [ ] 2026-08-17 · **REQ-SB-69-US-01-T06** · `ADR-046`'s own "becomes dead
  code" claim about `thread_note_exists`/`thread_note_path` was wrong —
  found and fixed same pass, worth a skim
  Plain English: `T06`'s own fix (wiring `thread_match_merge` to the new
  human-readable filename/lookup/rename mechanism, plus the stale
  Pending-Approval-payload fix) is correctly built and all 3 locked ACs
  (`AC-05`/`AC-06`/`AC-07`) plus the stale-payload regression checks are
  verified live and passing — this does not block `T06` or the story.
  But a repo-wide grep (before trusting `ADR-046`'s own claim that
  `thread_note_exists`/`thread_note_path` "become dead code") found a
  real, live second caller: `meeting_classification.py::
  _link_to_thread_by_conversation_id` (`REQ-SB-56-US-01`'s own Link-to-
  Thread PRIMARY strategy) — its `thread_note_exists(conversation_id)`
  check silently returned `False` for every genuinely-existing Thread
  created after `T06` ships, permanently starving the primary strategy in
  favor of the weaker date-proximity fallback, no exception, no log.
  Fixed directly, same pass (`BUG-019`, `Closed`) — a one-line swap to
  `resolve_thread_note_path(...) is not None`, verified live.
  **What to do:** no action required — resolved. Worth a skim only
  because it's the SECOND time this exact shape has bitten this project
  (mirrors `ESC-043`/`BUG-018`'s identical "grepping for a shared
  helper's own CALLERS, not trusting an ADR's/story's own named call
  site, found a second real one" pattern) — a candidate for
  `Implementation/Learnings.md` if a human agrees it's worth calling out
  explicitly as a recurring antipattern (an ADR's own Consequences
  section asserting "X becomes dead code" should be grep-verified, not
  trusted, before any coder relies on it).
  → `Implementation/Tasks/REQ-SB-69-US-01-T06-wire-thread-rename-and-fix-stale-payload.md`

- [ ] 2026-08-17 · **REQ-SB-69-US-01-T08** · minor helper-signature
  deviation from the task text's own sketch — spot-check only, not
  blocking
  Plain English: `T08` (`## Related` wikilinks) is correctly built and
  both locked ACs (`AC-10`/`AC-11`) plus the "regenerates from current
  state on every call" behavior are verified live and passing — this
  does not block `T08` or the story. The task file's own text sketched
  `_build_thread_related_wikilinks(path, customer, participants,
  project) -> str` (with a `path` parameter); it was implemented as
  `_build_thread_related_wikilinks(customer, participants, project) ->
  str` instead (no `path`), with the caller (`thread_match_merge`)
  performing the `vault_writer.replace_body_section(path, "## Related",
  <result>)` call itself. This matches `ADR-046` Decision 9's own literal
  text (the assembly step and the `replace_body_section` write are
  described as two separate things there) and keeps the helper pure
  (no I/O) — the task file's own Objective text explicitly frames the
  helper shape as "a new helper ... or composed inline," i.e. disclosed
  implementation latitude, not a locked signature.
  **What to do:** no action required — a spot-check only, logged per this
  project's own "scope-internal judgement calls flag the task for human
  review" convention.
  → `Implementation/Tasks/REQ-SB-69-US-01-T08-thread-related-wikilinks.md`
  → `ESCALATIONS.md` → `ESC-044`, `BUGS.md` → `BUG-019`

- [ ] 2026-08-17 · **REQ-SB-69-US-01-T04** · reconciliation judgement call
  — spot-check only, not blocking
  Plain English: `T04` (pull_email/process_staged_email independent
  dispatch + dedicated processing lock) is correctly built and all 3
  locked ACs it owns (`AC-01`/`AC-02`/`AC-03`) plus the `run_capture_now`
  backward-compatibility regression are verified live and passing — this
  does not block `T04` or the story. One item logged for spot-check:
  `run_capture_for_agent`'s email branch now composes `email_pull.
  pull_and_stage_emails()` + `run_email_capture_pipeline()` in one call
  (necessary — after `T03` retired Fetch from `run_email_capture_
  pipeline`, leaving this unchanged would have silently broken
  `run_capture_now`'s own contract); `run_capture_and_record_completion`
  gained a `trigger` parameter so only the scheduled tick's own Autonomous
  branch does Pull-only. Also found and fixed within scope: a genuine
  transitive circular import (`skill_tools -> email_classification -> ...
  -> skill_registry -> skill_tools -> email_capture_pipeline`), confirmed
  by direct testing under multiple real import orders, fixed via a
  deferred import mirroring `build_knowledge`'s own established
  precedent. (A second, disclosed, out-of-scope residual lock-sharing gap
  — `agent_schedules_router.py::run_now` hardcoding the shared Outlook-COM
  lock for every `capability_id` — was logged here as `ESC-045`; that gap
  is now fixed, `agents_router.py::_invoke_capability`'s own analogous
  no-lock-at-all gap for the same two capability ids was found and fixed
  alongside it, both verified live. See `ESCALATIONS.md` → `ESC-045`,
  `Status: Resolved`, for the resolving artefact — no further action
  needed for that item.)
  **What to do:** spot-check the `run_capture_for_agent`/`run_capture_
  and_record_completion` reconciliation judgement call described above;
  then remove this item.
  → `Implementation/Tasks/REQ-SB-69-US-01-T04-independent-pull-and-process-dispatch.md`

- [ ] 2026-08-17 · **SPRINT-056** · skim the sprint retrospective and
  harvest learnings
  Plain English: `SPRINT-056` (`REQ-SB-69-US-01`, decoupled Email Pull +
  human-readable Thread notes) is `Done` — all 8 tasks (`T01`-`T08`)
  built and verified live against the real, configured Outlook inbox,
  Compass, and vault; all 11 locked ACs (`AC-01`-`AC-11`) pass. The coder
  drafted a Retrospective (sizing accuracy — exact match, 8 tasks/L;
  what worked/didn't; patterns/antipatterns — including a real, recurring
  transitive-circular-import hazard hit independently by two different
  tasks this sprint; open follow-ups), but does not write
  `Implementation/Learnings.md` directly — that's a human step. The
  story's own standing `ADR-046`/trigger-3 human-review flag (see the
  separate `REQ-SB-69-US-01` entry above) remains open independently of
  this retro-harvest item.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  the "Patterns to carry forward" and "Antipatterns to avoid" entries into
  `Implementation/Learnings.md`.

- [ ] 2026-08-18 · **REQ-SB-57-US-01-T01** · spot-check three scope-internal
  judgement calls (Glimpse bullet format, `## Summary`-as-excerpt, `log.md`
  line wording) — not a blocker, `T01` is `Done` and both its locked ACs
  (`AC-01`/`AC-04`) verified live
  Plain English: the task's own End State named WHAT the Project Synthesizer's
  `## Glimpse` rollup should contain (one bullet per linked Thread, a
  `[[wikilink]]` plus that Thread's own already-synthesized opening-line/
  `## Summary` excerpt) and WHEN a `log.md` line is appended (the
  operator-confirmed History-line bar), but not the exact bullet string
  template, which region to read (no `read_body_opening_line`-equivalent
  primitive exists anywhere in `vault_writer.py`, confirmed by direct grep
  — only `## Summary` is actually readable, so that's what the rollup
  uses), or the exact `log.md` line wording/date format. Implemented as
  `- [[<thread-stem>]] <thread_name> — <## Summary content>` per Thread
  (`_No linked Threads yet._` when none are linked), and
  `"{YYYY-MM-DD UTC} — Project \"{project}\" status changed to {status}."`
  for the `log.md` line, mirroring this codebase's own `{date} —
  {description}` dated-line convention. Both verified live against the real
  configured vault (`Core42`, disposable fixtures, fully cleaned up
  afterward) — full detail in the task's own `## Implementation Log`.
  **What to do:** read `T01`'s own `## Implementation Log`; confirm the
  Glimpse bullet format and `log.md` line wording are acceptable, or direct
  a different format — either can be changed later without any locked-AC
  impact, since no AC names an exact string template.
  → `Implementation/Tasks/REQ-SB-57-US-01-T01-project-synthesizer-core-and-thread-trigger.md`
  → `Implementation/Sprints/SPRINT-056-decoupled-email-pull-and-human-readable-thread-notes.md`

- [ ] 2026-08-18 · **REQ-SB-57-US-01-T03** · spot-check two minor
  scope-internal judgement calls, plus a disclosed real concurrent-session
  finding — not a blocker, `T03` is `Done` and its locked `AC-06` (plus the
  non-AC "no Thread match" regression check) verified live
  Plain English: (1) the trigger call site captures the winning
  `conversation_id` directly at each of the two Link-to-Thread strategies
  rather than re-reading the Meeting note's own `thread` frontmatter
  afterward — the task's own End State offered both as equally valid; (2)
  the new logic lives in its own small private helper
  (`_trigger_project_resynthesis`) rather than inline in
  `classify_recent_meetings`, matching this module's own existing style.
  Separately: live verification used a disposable Project nested under the
  REAL, pre-existing Customer `Core42` (the same real Customer `T01`/`T02`
  also verified against) — `synthesize_project`'s own already-`Done`
  Customer cascade (`T02`) correctly rewrote the real `Core42.md`'s own
  `## Glimpse` to include the disposable Project while it existed, which
  went stale once the disposable Project directory was deleted at cleanup.
  Self-healed live by calling the real, already-`Done`
  `synthesize_customer("Core42")` once more after cleanup, confirmed
  `Core42`'s own `## Glimpse` now correctly reads `_No active Projects
  yet._`. Also observed, independently traced to a concurrent sibling
  coder session's own live `REQ-SB-57` verification against the SAME real
  `Core42` customer (not self-caused): real content/mtime drift on
  `Core42`'s own `log.md`/`index.md`, and one real pre-existing Thread note
  present at this task's own start-of-run snapshot gone by its end.
  **What to do:** read `T03`'s own `## Implementation Log` for full detail;
  confirm the two minor format choices are acceptable (no locked-AC impact
  either way); no action needed on the concurrent-session finding itself
  (already self-healed live) — recorded for awareness only, plus a new
  `MEMORY.md` Constraint so future `REQ-SB-57`-family verification against
  real, shared Customer fixtures accounts for the same cascade pattern.
  → `Implementation/Tasks/REQ-SB-57-US-01-T03-meeting-link-trigger.md`
  → `Implementation/UserStories/REQ-SB-57-US-01-project-and-customer-status-synthesizer-agents.md`

- [ ] 2026-08-18 · **REQ-SB-57-US-01-T04** · spot-check three scope-internal
  judgement calls — not a blocker, `T04` is `Done` and its locked `AC-03`
  (plus both non-AC regression checks) verified live
  Plain English: (1) `_propose_background_amendment`'s own
  `source_description` argument had no real, threaded-through provenance
  string available from `synthesize_customer`'s own actual inputs (only the
  raw `evidence_text` reaches it, not which Thread/Meeting it came from) —
  used a generic, honest `"evidence observed while resynthesizing
  \"<customer>\""` rather than fabricating a more specific claim; (2)
  `compass_client` is imported at MODULE level in `project_customer_
  synthesizer.py` (mirrors `email_classification.py`'s own precedent, no
  circular-import risk with this pair of modules), while `pending_
  approval_registry` stays a LOCAL import inside `_propose_background_
  amendment` specifically to mirror `vault_filing_expert._create_cross_
  cutting_proposal`'s own literal precedent, which the task's own
  Objective names directly; (3) approval-time dispatch was verified by
  calling the real `pending_approvals_router.approve_pending_approval`
  function directly in-process (no HTTP layer) — an equivalent real code
  path, since that function takes no `Request`/`Depends`.
  **What to do:** read `T04`'s own `## Implementation Log`; confirm the
  `source_description` wording and the import-placement split are
  acceptable (no locked-AC impact either way — a future task can thread a
  more specific provenance string through if wanted).
  → `Implementation/Tasks/REQ-SB-57-US-01-T04-background-amendment-proposal.md`

- [ ] 2026-08-18 · **REQ-SB-57-US-01** · story complete — `T01`-`T04` all
  `Done`, all six locked ACs (`AC-01` through `AC-06`) verified live; story
  `status: In Progress → Done`
  Plain English: every task in this story's own dependency chain is now
  built and verified against the real, configured vault, each with its own
  disposable fixture, fully cleaned up. `gate: flagged` carried forward
  purely from the scope-internal judgement-call spot-check items above
  (`T01`/`T03`/`T04`) — none rose to a MUST-FLAG trigger.
  **What to do:** spot-check the three linked task-level items above at
  your convenience; no action blocks anything downstream. This also
  unblocks `REQ-SB-58-US-01` (Customer/Project-Aware Expert) to proceed
  through `/plan-tasks`.
  → `Implementation/UserStories/REQ-SB-57-US-01-project-and-customer-status-synthesizer-agents.md`

- [ ] 2026-08-18 · **SPRINT-057** · sprint complete — drafted retrospective
  awaiting human skim/harvest into `Implementation/Learnings.md`
  Plain English: `REQ-SB-57-US-01` (this sprint's only story) is `Done`;
  sprint `status: In Progress → Done`, `completed: 2026-08-18`. The coder
  drafted `## Retrospective` per the Pipeline's own "coder drafts, human
  harvests" contract.
  **What to do:** read `## Retrospective` in the sprint file, then copy the
  "Patterns to carry forward" and "Antipatterns to avoid" entries into
  `Implementation/Learnings.md`.

- [ ] 2026-08-18 · **REQ-SB-58-US-01-T01** · `ESC-046` — real,
  pre-existing legacy-flat-vs-OKF-directory filename-stem collision
  shadows 14 of 17 already-migrated real Customers in `vault_indexing`'s
  stem-keyed index
  Plain English: while building/verifying the new `glimpse_first_qa.py`
  module, found that most real Customers with both an old flat `Work/
  Customers/<Name>.md` hub note (never retired) AND a migrated OKF
  directory concept file collide on filename stem — the STALE legacy flat
  file wins in `vault_indexing.get_index()`, not the real, current OKF
  concept file `REQ-SB-57`'s Synthesizer keeps up to date. Confirmed live
  for `Core42` (`type` reads back `"Customer"`, the legacy shape, not
  `"customer"`). Only `Microsoft Azure`/`Azerbaijan Ministry of Digital
  Development and Transport`/`Unsorted` are collision-free among migrated
  Customers. `T01` itself is unaffected (verified via a disposable
  Customer/Project fixture instead, per its own Tests block's sanctioned
  alternative) and is `Done`, but this **directly affects `REQ-SB-58-US-
  01-T02`**'s own real-Customer test-data choice, next in `SPRINT-058`.
  **What to do:** read `ESC-046` in full; decide the fix shape (delete/
  archive stale legacy flat Customer hub notes once migrated, and/or a
  `vault_indexing` collision-precedence rule) and consider a `/bug`
  capture so it is tracked to a `BUGFIX-NN-US-01` fix story. No action
  required before `T02` proceeds — `T02` is already informed to use a
  collision-free real Customer or a disposable one.
  → `Implementation/Tasks/REQ-SB-58-US-01-T01-glimpse-first-entity-resolution-module.md`
  → `Implementation/Sprints/SPRINT-057-project-and-customer-status-synthesizer-agents.md`

- [ ] 2026-08-18 · **REQ-SB-58-US-01-T02** · `ESC-047` — `retrieve_notes_
  in_agent_scope`'s own MCP tool requires the calling model to self-report
  its own literal internal `agent_id`, which is never stated anywhere in
  its own context, and it reliably guesses wrong
  Plain English: while live-verifying `AC-02`/`AC-03`, found that
  `vault-qa` is never told its own literal internal id (`"vault-qa"`)
  anywhere in its system prompt — only its human-readable display name
  (`"Vault Q&A"`). When the model tries to call `retrieve_notes_in_agent_
  scope(agent_id)` (a required, model-supplied argument), it reliably
  guesses wrong (captured live: `"vault_qa_agent"`), and the server
  honestly rejects the call. Confirmed, via 8 real live chat attempts
  (including 3 instrumented diagnostic ones) plus a direct, independent
  call with the correct argument, that this is a real, pre-existing
  `REQ-SB-29-US-01` tool-contract fragility, reproduced identically with
  this task's own new `glimpse_first_context` node disabled (a
  byte-identical no-op) — unrelated to and unaffected by `REQ-SB-58`'s
  own new code. `AC-02`/`AC-03` are recorded verified via the closest
  available disclosed substitute (real tool-call-attempt evidence +
  independent direct-call confirmation of the underlying mechanism);
  `T02` is not blocked.
  **What to do:** read `ESC-047` in full; decide the fix shape (drop the
  model-supplied `agent_id` argument in favor of server-side caller
  resolution, and/or state each agent's own literal internal id in its
  identity system message) and consider a `/bug` capture so it is tracked
  to a `BUGFIX-NN-US-01` fix story.
  → `Implementation/Tasks/REQ-SB-58-US-01-T02-graph-node-wiring-and-live-verification.md`
  → `Implementation/Sprints/SPRINT-058-customer-project-aware-expert.md`

- [ ] 2026-08-18 · **REQ-SB-59-US-01** · review `ADR-047` (one-time full
  vault migration) before tasks are locked
  Plain English: all 5 hard-dependency sibling stories (`REQ-SB-54`
  through `REQ-SB-58`) are now confirmed `Done`, so the architect pass
  unblocked and planned this story. It wrote `ADR-047`, which introduces
  this project's first archive-not-delete pattern
  (`.second-brain/migration_backup/<run-timestamp>/`, built entirely from
  the existing `vault_writer.move_note_and_attachments` primitive — never
  a hard `Path.unlink()` delete) for the new `app/business/
  vault_migration.py` module (T01 wipe / T02 recapture / T03 Customer
  regeneration). Two load-bearing findings drove the design: (1)
  `.second-brain/processed_email_ids.json` MUST be archived out as part of
  T01, or T02's recapture silently processes zero emails (Outlook
  `EntryID`s are stable across a rerun, so the existing dedup gate would
  skip every real historical email); (2) Meeting notes need NO wipe at
  all — their own dedup marker is already non-gating/top-up-only, so T02's
  wide-window meeting re-run satisfies Scenario 5 on its own. **`ADR-047`
  also decides `ESCALATIONS.md` → `ESC-046`'s own open "what still needs a
  human/architect decision" question**: the 14-of-17 legacy-flat-vs-OKF-
  directory Customer filename-stem collision is resolved as a direct,
  in-scope consequence of T03 (Customer note regeneration already reads
  and must archive the exact same stale flat files `ESC-046` named) —
  NOT deferred to a separate `BUGFIX-NN-US-01` story. T03 also
  deliberately reuses the existing, unmodified `project_customer_
  synthesizer.synthesize_customer`/`detect_customer_durable_fact`
  Pending-Approval gate for preserving durable pre-migration content —
  never a migration-only auto-write bypass, so expect a real batch of new
  Background-amendment Pending Approvals once T03 ships, not zero.
  **What to do:** review `ADR-047` in
  `Implementation/Architecture/ADR.md` — confirm the archive-not-delete
  design, the `ESC-046` resolution-via-T03 call, and the deliberate
  choice to route preserved content through Pending Approval rather than
  auto-writing it — then either let the decomposer's task breakdown stand
  or reset the story's `status:` to redo `/plan-tasks` if you change the
  ADR.
  → `Implementation/UserStories/REQ-SB-59-US-01-full-vault-migration-to-new-knowledge-model.md`

  **Decomposer addendum (2026-08-18):** all 5 scenarios locked as `AC-01`
  through `AC-05`; 3 tasks written, `status: Draft -> Ready` (all 5 locked
  ACs have a matching tagged verification step, `depends_on` acyclic).
  `gate` stays `flagged` per Pipeline.md's own rule (leave flagged when the
  architect flagged for an ADR change this same run) — review `ADR-047`
  and these 3 tasks together, then clear the flag or reset `status:` to
  redo. Dependency graph: `T01 -> T02` (hard — `T01` archiving
  `processed_email_ids.json` is what resets the email dedup gate `T02`'s
  recapture needs, per `ADR-047` Context point 1); `T03` carries
  `depends_on: []`, a directly-verified finding (not the "likely straight
  chain" the launch instructions floated) — `regenerate_customer_notes()`'s
  own evidence is each legacy flat Customer note's OWN pre-migration body,
  and its Glimpse rollup reads existing Project frontmatter, both fully
  disjoint from what `T01` archives and `T02` recaptures. Worth an explicit
  human glance since it deviates from the initially-assumed shape.
  → `Implementation/Tasks/REQ-SB-59-US-01-T01-wipe-legacy-email-notes.md`
  → `Implementation/Tasks/REQ-SB-59-US-01-T02-recapture-outlook-history.md`
  → `Implementation/Tasks/REQ-SB-59-US-01-T03-customer-note-regeneration.md`

- [ ] 2026-08-18 · **REQ-SB-71-US-03** · confirm where a Person with no
  derivable/matched Customer nests under the new People shape
  Plain English: `REQ-SB-71`'s People redesign (part 4) says a Person nests
  at `Work/Customers/<customer-slug>/People/<person-slug>.md` when a real
  Customer match exists, and says a Person spanning multiple Customers gets
  wikilinked from the others rather than duplicated — but it never says
  where a Person goes when NO Customer can be derived at all (an internal
  colleague, an unmatched email domain, or a no-email meeting attendee with
  no other signal). Today's existing flat model already handles this case
  gracefully (`kind/person` tag only, no company wikilink); the new nested
  model structurally needs a Customer parent, which this case doesn't have.
  This `/spec` pass resolved it by falling back to the existing flat
  `Work/People/<person-slug>.md` location for this one case — a real,
  disclosed judgment call, not confirmed by the operator, and a genuinely
  different, equally defensible answer exists (e.g. a dedicated `Work/
  People/` bucket reserved specifically for the unmatched case under the
  NEW model). Left unresolved, `/plan-tasks` would lock this guess into a
  task (`T04`) without a human ever having weighed in.
  **What to do:** confirm the flat-fallback resolution (or specify a
  different one) directly in the story's `## Notes`, then run
  `/plan-tasks REQ-SB-71-US-03`.
  → `Implementation/UserStories/REQ-SB-71-US-03-meeting-capture-recurring-split-and-people-from-attendees.md`

  **RESOLVED 2026-08-18** — the operator confirmed directly: falls back to
  the existing flat `Work/People/<slug>.md` location, exactly as this
  entry's own provisional resolution proposed. See the story's own
  frontmatter `gate_reason` history. Superseded by the new, SEPARATE
  trigger-3 (`ADR-048`) entry below, dated 2026-08-18.

- [ ] 2026-08-18 · **REQ-SB-70-US-01 + REQ-SB-71-US-01 + REQ-SB-71-US-02 +
  REQ-SB-71-US-03** · review `ADR-048` (Vault Base Provisioning +
  Redesigned Email/Meeting Capture) before tasks are locked
  Plain English: these four stories are one coherent redesign, worked out
  turn-by-turn with the operator in a dedicated vault-structure
  conversation right after tonight's `REQ-SB-59` migration was paused
  mid-run over a live reliability concern. The architect pass wrote ONE
  ADR (`ADR-048`) covering all four together, per the operator's own "one
  cohesive redesign... should not be built piecemeal" framing. It decides:
  a new idempotent `vault_provisioning.py` (`REQ-SB-70-US-01`, no
  archiving, not a migration); a real, code-enforced `caller` parameter on
  `vault_writer.replace_body_section` checked against a new per-function
  allow-list registry, with `## Personal Notes`/`## Actions` unconditionally
  unwritable by any agent code path regardless of that registry
  (`REQ-SB-71-US-01`); Thread becomes a directory holding immutable,
  write-once raw message notes plus a distilled `## Summary`/`##
  Related` concept file, split into two new, independently-triggerable,
  no-shared-lock capabilities of the existing email-capture Agent (Stage 1
  zero-Compass, Stage 2 Compass-backed) — and, notably, this REVERSES
  `ADR-046`'s own human-readable/renamable Thread-filename mechanism
  (Thread's directory name goes back to being purely deterministic from
  `conversation_id`, since a directory doesn't carry the same browsability
  need a filename did) — plus a new, generic `files/`-companion primitive
  (`REQ-SB-71-US-02`); Meeting's one-time/recurring split reuses the
  EXISTING `/poc/classify-meetings` endpoint unchanged (no new endpoint),
  keyed by `GlobalAppointmentID` for a recurring series, with raw
  calendar-invite boilerplate parsed transiently for `teams_link`/
  `dial_in` then discarded, never persisted; and Person notes move to
  nest under their primary Customer — a second, narrow, deliberate
  extension of `ADR-004`'s own "Customer is a tag, never a folder"
  boundary, for Person only (`REQ-SB-71-US-03`). The operator's own
  already-confirmed People-fallback resolution (see the entry immediately
  above, now resolved) is preserved unchanged by this ADR, just built out
  mechanically.
  **What to do:** review `ADR-048` in
  `Implementation/Architecture/ADR.md`, approve or reject (particular
  attention warranted on: the Thread-directory-naming reversal away from
  `ADR-046`'s own renamable-filename mechanism; the per-function vs.
  per-module section-ownership granularity choice; and the second
  `ADR-004` carve-out for Person nesting), then either let the
  decomposer's already-run task breakdown for all four stories stand or
  reset each story's `status:` to redo `/plan-tasks` if you change the ADR.
  → `Implementation/UserStories/REQ-SB-70-US-01-vault-base-provisioning-api.md`
  → `Implementation/UserStories/REQ-SB-71-US-01-section-ownership-enforcement.md`
  → `Implementation/UserStories/REQ-SB-71-US-02-email-capture-raw-distilled-and-two-stage-pipeline.md`
  → `Implementation/UserStories/REQ-SB-71-US-03-meeting-capture-recurring-split-and-people-from-attendees.md`

- [ ] 2026-08-18 · **SPRINT-061 + SPRINT-062** · ordered-sprint sequencing
  for the `ADR-048` redesign batch (cross-sprint dependencies introduced)
  Plain English: `/plan-sprints` partitioned the 4 `Ready`, ungrouped
  `ADR-048` stories into THREE ordered sprints instead of one — `SPRINT-060`
  (`REQ-SB-70-US-01` + `REQ-SB-71-US-01`, the two independent, foundational
  roots, `~3 tasks, S`, `gate: clear`, already `Ready`), `SPRINT-061`
  (`REQ-SB-71-US-02`, `~7 tasks, L`, `depends_on_sprints: [SPRINT-060]`),
  and `SPRINT-062` (`REQ-SB-71-US-03`, `~3 tasks, S`,
  `depends_on_sprints: [SPRINT-060, SPRINT-061]`). This follows the real
  task-level `depends_on` graph read directly from each task file (not
  inferred): `REQ-SB-71-US-02-T05`/`-T07` and `REQ-SB-71-US-03-T01` all
  hard-depend on `REQ-SB-71-US-01-T01`; `REQ-SB-71-US-03-T01`/`-T02`
  additionally hard-depend on `REQ-SB-71-US-02-T02`/`-T05`. The
  alternative — one 12-13-task sprint spanning all four stories — was
  considered and rejected as a disclosed, real oversized-sprint risk (the
  largest sprint this project has shipped and confirmed accurate to date
  is 9 tasks, L, per `Implementation/Learnings.md`); this batch's own real
  dependency graph is a strict, mostly-linear chain, so ordered sprints
  honour it exactly as faithfully as one giant sprint would, without that
  size risk. This mirrors this project's own repeatedly-confirmed Learnings
  pattern for exactly this situation (`SPRINT-011`→`012`,
  `SPRINT-025`→`026`, `SPRINT-049`→`050`). `SPRINT-061`/`SPRINT-062` are
  each flagged solely because introducing a `depends_on_sprints` edge is
  an unconditional MUST-FLAG trigger for this role, not because the
  sequencing itself is genuinely in question.
  **What to do:** review the sequencing in `SPRINT-060`/`SPRINT-061`/
  `SPRINT-062`'s own `## Grouping Rationale & Sizing` / `## Notes`
  sections. If you agree, no action is needed — `SPRINT-061`/`SPRINT-062`
  build in order once each upstream sprint reaches `Done`
  (`/implement-sprint` already refuses to start a sprint whose
  `depends_on_sprints` aren't all `Done`, per `Implementation/Pipeline.md`
  hard rule 9). If you'd prefer a different partition (e.g. merging
  `SPRINT-061`/`SPRINT-062`, or folding `REQ-SB-70-US-01` into its own
  sprint instead of `SPRINT-060`), say so and re-run `/plan-sprints` with
  that guidance.
  → `Implementation/Sprints/SPRINT-060-vault-base-provisioning-and-section-ownership-enforcement.md`
  → `Implementation/Sprints/SPRINT-061-email-capture-redesign.md`
  → `Implementation/Sprints/SPRINT-062-meeting-capture-redesign.md`

- [ ] 2026-08-18 · **SPRINT-060** · skim the sprint retrospective, harvest
  learnings, and spot-check two disclosed coder judgment calls
  Plain English: SPRINT-060 (REQ-SB-70-US-01, REQ-SB-71-US-01) is Done —
  all 3 tasks built and verified live against the REAL operator vault (real
  `POST /poc/provision-vault-base` calls; real on-demand email capture via
  `POST /agents/email-capture-pipeline/schedules/{pull_email,
  process_staged_email}/run-now`; real `POST /poc/backfill-thread-
  summaries`; a real, freshly-created `route_thread_to_project` Pending
  Approval approved via `POST /pending-approvals/{id}/approve`). The coder
  drafted a Retrospective (sizing accuracy, what worked/didn't, patterns/
  antipatterns, open follow-ups) in the sprint file. Two scope-internal
  judgment calls were disclosed, not hidden, in the task-level
  Implementation Logs, worth a human skim:
  1. Starting the real app to reach the provisioning endpoint also
     triggers its own pre-existing, unrelated app-start capture job
     (`ADR-005`), which wrote real Meeting/People/Thread/Customer content
     into the real vault concurrently with `REQ-SB-70-US-01-T01`'s own
     verification — the endpoint's own machine-readable return dict was
     used as the authoritative evidence of what it itself created (exact
     on every call); the broader directory-listing noise is disclosed, not
     hidden.
  2. `REQ-SB-71-US-01-T02`'s `finalize_background_amendment_proposal`
     caller could not be exercised fully live, end-to-end, this session —
     no real `propose_background_amendment` Pending Approval currently
     exists in this vault, and its only real trigger path
     (`synthesize_customer`'s `evidence_text` parameter) has no
     currently-reachable real caller now that the legacy-flat-Customer-note
     migration already ran. Verified instead via strong compensating
     evidence: an unchanged-code-diff (single mechanical `caller=` kwarg
     addition) plus a live-proven guard check confirming the exact
     caller+header pair this call site uses is allowed and functional.
  This standing `ADR-048` human-review flag (shared with `REQ-SB-71-US-02`/
  `-US-03`, see the existing entry above) remains open regardless — not
  cleared by this pass.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward"/"Antipatterns to
  avoid" entries into `Implementation/Learnings.md`. Separately, spot-check
  the two disclosed judgment calls above (in `REQ-SB-70-US-01-T01`'s and
  `REQ-SB-71-US-01-T02`'s own `## Implementation Log`) and decide whether
  either warrants further action (e.g. opportunistically re-verifying
  `finalize_background_amendment_proposal` once a real Background-
  amendment approval naturally occurs).
  → `Implementation/Sprints/SPRINT-060-vault-base-provisioning-and-section-ownership-enforcement.md`
  → `Implementation/Tasks/REQ-SB-70-US-01-T01-vault-base-provisioning.md`
  → `Implementation/Tasks/REQ-SB-71-US-01-T02-retrofit-existing-callers.md`

- [ ] 2026-08-18 · **ESC-048** · `thread_match_merge`'s still-live,
  scheduled create-vs-update check now silently duplicates Threads for
  pre-redesign conversations — `email-capture-pipeline` left `supervised`
  as an interim protective measure
  Plain English: building `REQ-SB-71-US-02` (`SPRINT-061`) required
  retargeting `resolve_thread_note_path` to the new Thread directory
  shape (`T02`, per `ADR-048`) — correct for new capture, but it breaks
  the SAME primitive `thread_match_merge` (the still-`Done`, still-
  scheduled `process_staged_email` capability) uses for its own create-
  vs-update decision. Confirmed live: none of this vault's real,
  pre-existing OLD-shape flat Thread notes are found by the retargeted
  lookup anymore — the next time `thread_match_merge` runs against a new
  message in one of those existing conversations, it will silently
  create a duplicate Thread note instead of updating the real one. No
  task in this story's own `## Files to Modify` touches `email_capture_
  pipeline.py` (the module that still calls `thread_match_merge`), so
  this could not be fixed in-scope — retiring `thread_match_merge`
  itself was explicitly left an optional, not-mandated, coder-level call
  by the decomposer, and doing so here would have meant editing an
  unanticipated file. As a real, live protective measure (not just a
  proposal), `email-capture-pipeline`'s working mode was flipped to
  `supervised` via the real `PATCH /agents/email-capture-pipeline`
  endpoint before any code was written this session, and deliberately
  left `supervised` — reverting to `autonomous` before the underlying
  conflict is resolved would re-expose the duplication risk on the very
  next scheduled tick. `REQ-SB-71-US-02`'s own 7 tasks/7 locked ACs are
  fully `Done` and unaffected (none exercise the old path).
  **What to do:** read the full finding in `ESC-048` (`ESCALATIONS.md`),
  then decide: (a) `/bug` capture (Area: Logic) → a `BUGFIX-NN-US-01` fix
  story that rewires `process_staged_email`'s own underlying
  implementation onto `capture_raw_thread_messages`/`synthesize_thread`
  and formally retires `thread_match_merge`'s live call site, restoring
  `email-capture-pipeline` to `autonomous` once that ships; or (b) leave
  `email-capture-pipeline` in `supervised` mode until `REQ-SB-71-US-03`
  (`SPRINT-062`) or a dedicated follow-up naturally addresses it.
  → `ESCALATIONS.md` (ESC-048)
  → `Implementation/Tasks/REQ-SB-71-US-02-T02-note-discovery-generalization.md`
  → `Implementation/Sprints/SPRINT-061-email-capture-redesign.md`

- [ ] 2026-08-18 · **SPRINT-061** · skim the sprint retrospective and
  harvest learnings
  Plain English: SPRINT-061 (`REQ-SB-71-US-02`, Email Capture Redesign —
  Thread raw/distilled split, two-stage pipeline, Files/OKF companions)
  is `Done` — all 7 tasks built and verified live against the REAL
  operator mailbox/vault (a real `POST /poc/capture-raw-thread-messages`
  call that wrote 252 real raw message notes across 127 real Thread
  directories in one batch; real `POST /poc/synthesize-thread` calls that
  regenerated `## Summary`/`## Related` from full raw-message
  reconstruction, including one genuine Compass classification failure
  handled honestly via the existing `BUG-015` fallback; a real, live
  concurrency proof that Stage 1 and Stage 2 share no lock; a real
  manually-added `## Personal Notes`/`## Actions` entry confirmed
  byte-for-byte unchanged, by SHA-256 hash, across a re-synthesis; real
  PDF/XLSX attachments producing real, byte-identical `files/<slug>/` OKF
  companions with genuine Compass-generated summaries). The coder drafted
  a Retrospective in the sprint file. This standing `ADR-048` human-
  review flag (shared with `REQ-SB-70-US-01`/`REQ-SB-71-US-01`/
  `REQ-SB-71-US-03`, see the existing entry above) remains open
  regardless — not cleared by this pass. The `ESC-048` finding above is
  this sprint's own one genuine, disclosed out-of-scope discovery — not
  nested inside this entry (`Implementation/Learnings.md`'s own
  `SPRINT-048` antipattern: give a real, separate risk its own line item).
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward"/"Antipatterns to
  avoid" entries into `Implementation/Learnings.md`. Separately, decide
  `ESC-048` above.
  → `Implementation/Sprints/SPRINT-061-email-capture-redesign.md`
  → `Implementation/UserStories/REQ-SB-71-US-02-email-capture-raw-distilled-and-two-stage-pipeline.md`

- [ ] 2026-08-18 · **ESC-049** · `my_day.py::list_calendar_items` silently
  excludes every new-shape Meeting note from its own 7-day window —
  `REQ-SB-71-US-03`'s own dropped `subject`/`start` frontmatter fields
  Plain English: `REQ-SB-71-US-03`'s own deliberate, three-times-repeated
  design (analyst Scenario 1, architect End-State text, `ADR-048`
  Decision 5) drops `subject`/`start`/`end`/`location` from a Meeting
  note's own frontmatter — correct for Meeting Capture's own new shape,
  but `app/business/my_day.py::list_calendar_items` reads exactly
  `subject`/`start` directly (`start` doubles as its own 7-day rolling-
  window filter input). Confirmed live by direct code reading: every
  NEW-shape Meeting note captured from now on will render with a blank
  subject and, more seriously, be silently, permanently EXCLUDED from My
  Day's own Calendar tab and its own summary count (`_within_window("",
  ...)` always returns `False`). `my_day.py` is not named in any of this
  story's own 3 tasks' `## Files to Modify` — fixing it would mean
  editing an unanticipated file, so it was disclosed, not fixed. Mirrors
  this same 4-story batch's own `ESC-048` precedent exactly (a real,
  disclosed, out-of-scope regression found via due-diligence direct
  reading, not blocking the task that found it).
  **What to do:** read the full finding in `ESC-049` (`ESCALATIONS.md`),
  then decide: (a) `/bug` capture (Area: Logic) → a `BUGFIX-NN-US-01` fix
  story that gives `list_calendar_items` a fallback display/window-filter
  path for the new Meeting shape, or (b) leave it as a disclosed,
  accepted gap until a dedicated My-Day-refresh story naturally addresses
  it.
  → `ESCALATIONS.md` (ESC-049)
  → `Implementation/Tasks/REQ-SB-71-US-03-T01-one-time-vs-recurring-meeting-shape.md`
  → `Implementation/Sprints/SPRINT-062-meeting-capture-redesign.md`

- [ ] 2026-08-18 · **SPRINT-062** · skim the sprint retrospective, harvest
  learnings, and spot-check the disclosed coder scope-internal judgement
  calls
  Plain English: SPRINT-062 (`REQ-SB-71-US-03`, Meeting Capture Redesign
  — one-time/recurring split, `## History` synthesis, People nested under
  Customer) is `Done` — the last story in the `ADR-048` 4-story batch.
  All 3 tasks built and all 7 locked ACs (`AC-01`..`AC-07`) verified live
  against the REAL operator Outlook calendar/vault: a real one-time
  meeting produced a clean, boilerplate-free note; a real recurring
  series ("Weekly Forecast l Strategic Clients") accumulated 4 real dated
  `## History` entries on the SAME note across multiple real calls (file
  count never grew), one genuinely drawing on a real linked Thread's own
  content; a real manually-added Personal Notes/Actions entry survived
  byte-for-byte across a further real History append. The People
  scenarios (`AC-03`-`AC-06`) were verified via a scoped, disclosed,
  real-endpoint monkeypatch of ONLY the external Outlook-COM boundary —
  the real live calendar has zero real no-email-attendee instances across
  a 240-day scan, and the real vault currently carries zero notes with a
  real `customer` frontmatter value (a same-day migration reset) — full
  design/disclosure/cleanup-confirmation in `T02`'s/`T03`'s own
  Implementation Logs; all fixture/engineered artifacts were fully
  removed and confirmed clean afterward (a vault-wide `*fixture*` scan
  returned zero matches). The coder drafted a Retrospective in the sprint
  file. Several scope-internal judgement calls were disclosed, not
  hidden, in the task-level Implementation Logs (all 3 tasks are `gate:
  flagged` for this reason, not because anything is blocked):
  1. `T01` — reconciled the story's own broader Scenario 1 text vs. this
     task's own more precise End-State text on which frontmatter fields
     survive (followed the End-State text — `type`/`customer`/`tags`/
     `thread` persist, only raw calendar-logistics fields drop); and
     implemented `attendees` as a genuine new frontmatter field (both
     texts list it), alongside the pre-existing body wikilink line.
  2. `T02`/`T03` — the disclosed monkeypatch verification technique
     itself (see above).
  3. `T03` — the exact `ensure_person_note(customer=)` fallback
     semantics (meeting-derived customer used ONLY for the no-email case,
     never overriding an email-resolvable person's own matched Customer).
  This standing `ADR-048` human-review flag (shared with `REQ-SB-70-US-01`/
  `REQ-SB-71-US-01`/`-US-02`, see the existing entry above) remains open
  regardless — not cleared by this pass. `ESC-049` above is this sprint's
  own one genuine, disclosed out-of-scope discovery — not nested inside
  this entry (`Implementation/Learnings.md`'s own `SPRINT-048`
  antipattern: give a real, separate risk its own line item).
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward"/"Antipatterns to
  avoid" entries into `Implementation/Learnings.md`. Spot-check the 3
  disclosed judgement-call groups above (in each task's own `##
  Implementation Log`). Separately, decide `ESC-049` above.
  → `Implementation/Sprints/SPRINT-062-meeting-capture-redesign.md`
  → `Implementation/UserStories/REQ-SB-71-US-03-meeting-capture-recurring-split-and-people-from-attendees.md`
  → `Implementation/Tasks/REQ-SB-71-US-03-T01-one-time-vs-recurring-meeting-shape.md`
  → `Implementation/Tasks/REQ-SB-71-US-03-T02-history-entry-synthesis.md`
  → `Implementation/Tasks/REQ-SB-71-US-03-T03-people-nested-under-customer.md`

- [ ] 2026-08-18 · **REQ-SB-72-US-01** · `ADR-049` created — review the
  Librarian's Thread-lookup mechanism (a third swing back to frontmatter
  scan) and its new autonomous scheduling before tasks are locked
  Plain English: the architect wrote `ADR-049` for "The Librarian Section —
  First Housekeeping Pipeline." It partially reopens `ADR-048` Decision 3:
  `resolve_thread_note_path` reverts from a deterministic path check back
  to a frontmatter-based scan (the THIRD swing of this project's own
  Thread-matching mechanism — `ADR-046` scan → `ADR-048` path → back to
  scan), justified by real steady-state capture volume (~10 emails/hour).
  Direct reading during this pass found TWO more real call sites beyond
  what the story itself named (`raw_message_capture.py`'s Stage 1
  existence check, `synthesize_thread`'s own `messages/` read) that also
  needed migrating off the deterministic path, plus a new whole-directory
  `rename_thread_directory` primitive for the actual rename. The ADR also
  decides: the new "Librarian" Section/`librarian-housekeeping` Agent
  identity (via the existing, unmodified `section_registry`/`agent_
  registry` mechanisms — no new Section-creation machinery); five new
  `/poc/*` endpoints on the existing `email_poc_router.py`; and — a real
  point of difference from every other story in this batch — a genuine new
  `agent_schedule_registry` entry (`run_housekeeping_pass`, every 6 hours,
  operator-adjustable), the deliberate opposite of `REQ-SB-70`/`REQ-SB-71`'s
  own standing no-scheduler constraint. Separately, this same pass found and
  escalated a real, already-live defect (not caused by this story) in the
  still-`supervised` `thread_match_merge` pipeline — see `ESC-050` below,
  its own separate review-queue entry.
  **What to do:** review `ADR-049` in
  `Implementation/Architecture/ADR.md` — confirm the frontmatter-scan
  reversal, the three-call-site migration, the Librarian Agent/Section/
  endpoint/scheduling shape, and the company-mention-detection design
  (a new, dedicated Compass call, never reusing `determine_placement_and_
  file` itself) — then either let the decomposer's task breakdown stand or
  reset the story's `status:` to redo `/plan-tasks` if you change the ADR.
  → `Implementation/UserStories/REQ-SB-72-US-01-librarian-section-first-housekeeping-pipeline.md`

- [ ] 2026-08-18 · **ESC-050** · `thread_match_merge`'s still-live,
  `supervised`-only pipeline already ORPHANS a Thread's `messages/`/
  `files/` subdirectories for any new-shape Thread — worse than `ESC-048`
  disclosed
  Plain English: while architecting `REQ-SB-72-US-01`, direct reading of
  `thread_match_merge`'s own full body found that for a conversation with
  an ALREADY-EXISTING, new-shape (directory-based) Thread, it finds the
  Thread fine, but then computes a rename target via its own still-live
  LEGACY (`ADR-046`) flat-filename logic and physically moves the concept
  file out of its own directory — orphaning that Thread's real `messages/`
  raw-evidence and any `files/` companions. This already fires TODAY,
  independent of `REQ-SB-72-US-01` shipping, and is materially worse than
  `ESC-048`'s own original "duplicate Thread" description (real data-
  integrity corruption, not just a duplicate note). Reinforces, does not
  replace, `ESC-048`'s own still-open finding and recommended fix.
  **What to do:** read the full finding in `ESC-050` (`ESCALATIONS.md`),
  then decide, together with `ESC-048`: (a) `/bug` capture (Area: Logic) →
  a `BUGFIX-NN-US-01` fix story that rewires `process_staged_email` onto
  `capture_raw_thread_messages`/`synthesize_thread` and formally retires
  `thread_match_merge`'s live call site; or (b) leave `email-capture-
  pipeline` in `supervised` mode until a dedicated follow-up naturally
  addresses it. Given this entry's own sharper severity, recommend
  prioritizing this over its original `ESC-048` framing.
  → `ESCALATIONS.md` (ESC-050, and its sibling `ESC-048`)
  → `Implementation/Architecture/ADR.md` (ADR-049 Consequences)
  → `Implementation/UserStories/REQ-SB-72-US-01-librarian-section-first-housekeeping-pipeline.md`

- [ ] 2026-08-18 · **ESC-051** · `write_attachments`'s own `_slugify(...,
  max_len=80)` truncation collapses near-identical, long Outlook
  `message_id`s onto the SAME attachment directory
  Plain English: found live while coding/verifying `REQ-SB-72-US-01-T04`'s
  Files Backfill Job against the real vault — the Job's own real attachment
  count came back 121 vs. 56 real files on disk. Root cause, confirmed by
  direct reading: `write_attachments`'s own attachment-directory naming
  truncates the message-segment slug at 80 characters; real Outlook
  `message_id` values run past 80 characters and, for multiple real
  copies/recipients of the same email, differ only past that point — so
  they silently collapse onto the SAME attachment directory (16 real
  collision groups confirmed in this vault). No real attachment content
  loss observed, but `T04`'s own Job produces redundant (not duplicate-per-
  its-own-key, but redundant across colliding keys) companions, and the
  SAME mechanism could in principle silently overwrite two different real
  attachments that share both a colliding `message_id` prefix AND an
  identical filename (not observed live, but a real latent risk given the
  mechanism).
  **What to do:** read the full finding in `ESC-051` (`ESCALATIONS.md`),
  then decide: (a) `/bug` capture (Area: Logic) → a `BUGFIX-NN-US-01` fix
  story that widens/hashes the message-segment slug in `write_attachments`/
  `staged_attachment_files` (mirroring `raw_message_note_path`'s own hash-
  suffix precedent), plus a one-time backfill to de-duplicate any
  redundant companions already produced; or (b) leave as-is, since no real
  content loss has been observed and the consequence so far is cosmetic
  redundancy, not corruption.
  → `ESCALATIONS.md` (ESC-051)
  → `Implementation/Tasks/REQ-SB-72-US-01-T04-files-backfill-job.md`

- [ ] 2026-08-19 · **REQ-SB-72-US-01-T09** · spot-check `AC-11` — 3 of 5
  real `/poc/librarian-*` endpoints have strong real execution evidence
  but no captured live `200` within this coding session
  Plain English: `T06`-`T09` are all `Done`, all locked ACs verified
  against real, live evidence. One genuine, disclosed gap: `AC-11`'s own
  test literally asks to "POST each of the 5 real endpoints and confirm
  each returns a real 200." `/poc/librarian-rename-threads` and `/poc/
  librarian-backfill-files` did — clean, captured `200 OK` each. `/poc/
  librarian-populate-related`, `/poc/librarian-backfill-company-folders`,
  and `/poc/librarian-run-housekeeping-pass` did NOT — not because
  anything failed, but because these Jobs each genuinely take 30-90+
  minutes against the real 126-Thread corpus (one real Compass call per
  Thread, no per-call limit), and this coding session's own background-
  process tooling reclaimed the backend process partway through 3 separate
  real attempts (confirmed via live log tailing every time: the Job was
  still actively succeeding — real Compass 200s, real on-disk `##
  Related` changes, real Pending Approvals created — right up to each
  kill; never a server crash, never two concurrent calls to the same
  mutating function). See `ESC-054` for the full, itemized finding. Real,
  substantial forward progress WAS made and is real, live vault state, not
  a simulation: `## Related` population went 20→87/126 real Threads; 10
  real `propose_librarian_company_link` Pending Approvals exist (1
  approved live → real Customer folder created; 1 declined live → nothing
  created, confirming the mechanism both ways; 5 genuinely pending for
  real operator review); multiple new real Customer folders were created
  for confident mentions.
  **What to do:** either (a) trust the itemized real evidence in `T06`/
  `T07`/`T09`'s own Implementation Logs as sufficient (the underlying
  mechanism is proven correct 5 different ways; only the literal "captured
  a 200 in THIS session" formality is incomplete for 3 routes) and clear
  this flag, or (b) independently close the gap in under 2 minutes by
  running the backend normally (NOT inside a coding session) and calling
  `POST /poc/librarian-run-housekeeping-pass` once yourself — it will run
  to completion without the coding-session-specific background-process
  ceiling this entry describes, finishing the remaining `## Related`/
  company-folder backfill for real in the same call. Either way, `T09`'s
  own real, persisted 6-hour schedule will also complete this
  autonomously going forward once the app is running normally.
  → `ESCALATIONS.md` (ESC-054)
  → `Implementation/Tasks/REQ-SB-72-US-01-T06-related-ownership-transfer.md`
  → `Implementation/Tasks/REQ-SB-72-US-01-T07-company-folder-backfill-and-ambiguous-finding-approval.md`
  → `Implementation/Tasks/REQ-SB-72-US-01-T09-scheduled-wiring.md`

- [ ] 2026-08-18 · **ESC-052** · `write_file_companion`'s own `file_slug`
  convention breaks when an attachment's own filename already ends in
  `.md` — crashed the live scheduled index rebuild, now mitigated (not
  root-cause-fixed)
  Plain English: found live coding/verifying `REQ-SB-72-US-01-T04` — a
  real attachment named `project-scaffold.md` produced a companion
  DIRECTORY literally named `....md`, which `vault_indexing.rebuild_
  index()`'s own `*.md` scan then tried to read as a note file and
  crashed on (`PermissionError`, confirmed live on the freshly-restarted
  real backend). Mitigated in-scope with a defensive `path.is_file()`
  guard on `list_all_note_paths()` (zero behavior change for any
  well-formed note) — the live crash is stopped — but the ROOT CAUSE
  (`email_classification.write_file_companion`'s own `file_slug`
  convention) is outside this story's own `## Files to Modify` and left
  disclosed, not fixed.
  **What to do:** read the full finding in `ESC-052` (`ESCALATIONS.md`),
  then decide whether to `/bug` capture (Area: Logic) a fix to `write_
  file_companion`'s own `file_slug` construction — batch with `ESC-051`
  (same module, same class of slug-construction gap) into one
  `BUGFIX-NN-US-01` fix story.
  → `ESCALATIONS.md` (ESC-052, sibling `ESC-051`)
  → `Implementation/Tasks/REQ-SB-72-US-01-T04-files-backfill-job.md`

- [x] 2026-08-19 · **BUGFIX-04-US-01** · Resolved 2026-08-19 (operator, in
  full autopilot) — confirm `BUG-025`'s scope before `/plan-tasks`
  proceeds — it is net-new work against a still-Draft PRD requirement, not
  a regression
  Plain English: this triage batch's own brief characterized `BUG-025`
  (chat renders plain text, not rich text, in Meeting Cockpit, Inbox
  Cockpit, and the Agents Map chat panel) as "a regression against
  already-shipped `REQ-SB-32`." Direct checking found `REQ-SB-32` was
  never actually specced or built — `BACKLOG.md` shows no story link and
  no status for it, `Documentation/PRD.md`'s own comment says it was
  explicitly left as an open discussion topic, and no markdown/rich-text
  rendering code or dependency exists anywhere in `src/frontend` today.
  `BUG-025`'s own symptom (raw `**`/`-` syntax renders literally) is real
  and unaffected by this — only the "already shipped, now regressed"
  framing is wrong. Left unresolved, `/plan-tasks` could build Scenario
  4's fix without realizing it needs real design decisions (which
  markdown subset, which rendering library, whether user messages also
  render), not just a small patch, and `REQ-SB-32`'s own PRD/BACKLOG entry
  will stay looking unbuilt even after this story ships it.
  **What to do:** read `BUGFIX-04-US-01`'s own `## Notes` and
  `ESCALATIONS.md` → `ESC-053`, then either (a) let `/plan-tasks` proceed
  on all 4 scenarios with this context in hand, or (b) decide `BUG-025`
  should instead route through a fresh `/spec REQ-SB-32` pass (formally
  resolving the PRD's own open discussion) and pull it out of this bugfix
  story — `BUG-022`/`BUG-023`/`BUG-024` are unaffected either way and may
  proceed to `/plan-tasks` now.
  **Resolved:** the operator chose (a) directly, in the story's own
  `gate_reason`/`## Notes` (2026-08-19) — markdown subset = common
  chat-reply baseline, library = `react-markdown`, scope = both user and
  agent messages render rich. `ESC-053` stays `Open`, permanent record of
  the original finding; `REQ-SB-32`'s own PRD/`BACKLOG.md` reconciliation
  is still an open human follow-up, not resolved by this pointer.
  → `Implementation/UserStories/BUGFIX-04-US-01-cockpit-chat-addressing-input-and-rendering-fixes.md`
  → `ESCALATIONS.md` (ESC-053)

- [x] 2026-08-19 · **BUGFIX-04-US-01** · `ADR-050` created (`react-markdown`
  chat rich-text rendering) — review before `/plan-tasks`'s decomposer
  step locks tasks against it
  Plain English: the architect pass resolved `BUGFIX-04-US-01` Scenario 4
  (`BUG-025`)'s remaining open design questions — beyond the markdown-
  subset/library/scope choices the operator already settled directly —
  into a real architectural decision, `ADR-050`: `react-markdown` v9.x
  with zero remark/rehype plugins, a default-safe sanitization posture
  (no `rehype-raw`, so no raw-HTML/`dangerouslySetInnerHTML` path exists;
  link URLs pass through `react-markdown`'s own built-in scheme-stripping
  `defaultUrlTransform`), and one new shared `src/frontend/src/
  components/ChatMessageText.tsx` component consumed by both `Cockpit.tsx`
  and `AgentDetailPanel.tsx` (confirmed the only two real chat-thread
  render sites — no third, separate Agents-Map-chat-panel component
  exists), applied symmetrically to user and agent messages. This is a
  genuine new npm dependency and a real, if narrow, security-relevant
  wiring choice (how markdown-to-React rendering avoids the XSS surface
  the story's own Constraint names) — squarely the kind of decision this
  project's own ADR practice gates for human review, even though the
  higher-level "which library, which subset, does it apply to user
  messages too" questions were already operator-resolved before this pass.
  **What to do:** review `ADR-050` in `Implementation/Architecture/
  ADR.md` (Decision, Alternatives Considered, Consequences), approve or
  reject/redirect (e.g. object to `react-markdown` itself, or to the
  "no `rehype-raw`" sanitization posture), then either let `/plan-tasks`'s
  decomposer proceed to lock Scenario 4's AC and tasks against it, or reset
  `BUGFIX-04-US-01`'s `status:` to `Draft` (already `Draft`) with a Notes
  correction and re-run `/plan-tasks` once resolved.
  **Resolved:** the operator approved `ADR-050` directly (recorded in
  `BUGFIX-04-US-01`'s own `gate_reason`, 2026-08-19); the decomposer pass
  the same day locked Scenario 4 as `AC-04`, created `T03`/`T04` against
  `ADR-050`'s module shape unchanged, and advanced the story `Draft →
  Ready`. `ADR-050` itself stays `Accepted` in `ADR.md`, unedited.
  → `Implementation/Architecture/ADR.md` (ADR-050)
  → `Implementation/UserStories/BUGFIX-04-US-01-cockpit-chat-addressing-input-and-rendering-fixes.md`

- [ ] 2026-08-19 · **SPRINT-064** · skim the sprint retrospective and harvest learnings
  Plain English: SPRINT-064 (`BUGFIX-04-US-01`, Cockpit chat addressing/
  Enter/pending-state/rich-text fix) is Done — all 4 tasks built and all 4
  locked ACs verified live (real backend dispatch, a real Meeting Cockpit
  in a real browser, real Enter/pending-state/live-update behavior, real
  DOM structural checks for markdown rendering across all 3 named chat
  surfaces). The coder drafted a Retrospective in the sprint file,
  including two verification-harness techniques (headless-Edge PNA
  preflight workaround, `requestSubmit()`-paired-with-real-CDP-Enter) and
  one disclosed live-Provider-outage workaround, all worth carrying
  forward for future frontend-heavy sprints.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward"/"Antipatterns to
  avoid" entries into `Implementation/Learnings.md`.
  → `Implementation/Sprints/SPRINT-064-cockpit-chat-addressing-input-and-rendering-fixes.md`

- [ ] 2026-08-19 · **BUG (uncaptured)** · `app/business/cockpit/
  people.py::resolve_people_chips` 500s on a real Meeting note whose
  `attendees` frontmatter is a list of plain wikilink strings, not dicts
  Plain English: found incidentally while selecting a live Meeting Cockpit
  for `SPRINT-064`'s own verification — `GET /cockpit/meeting/Alignment
  Mubadala-2026-08-17-a4737bc4` (and at least one other real meeting,
  `PSS Team Weekly Meeting-2026-08-18-47a72b70`) return `500 Internal
  Server Error`. Root cause confirmed by direct code reading:
  `_coerce_people_list` only JSON-decodes a STRING `attendees` value or
  passes a real list through as-is; when the real, live `attendees`
  frontmatter value is a plain list of wikilink strings (e.g.
  `["[[sandeep.penumadu@core42.ai]]", ...]` — the actual, real shape
  Meeting Capture currently writes for at least some meetings) rather than
  the `list[dict]` shape `ADR-036` point 7 designed, `resolve_people_
  chips`'s own `for person in people: person.get("email", "")` crashes
  with `AttributeError: 'str' object has no attribute 'get'`, surfaced as
  a bare `500`. Worked around for `SPRINT-064`'s own verification by
  simply choosing a different, unaffected real meeting (`Weekly Forecast l
  Strategic Clients-2026-08-17-733126dd`, zero attendees) — not fixed, out
  of `SPRINT-064`'s own `## Files to Modify` (`people.py` is not named in
  any of `BUGFIX-04-US-01`'s 4 tasks) and unrelated to any of its 4 locked
  ACs. Real, live, reproducible impact: EVERY Meeting Cockpit whose
  attendees frontmatter is still in this older/raw shape currently 500s
  its own `GET /cockpit/meeting/{stem}` entirely — not just the people-
  chips panel, the WHOLE Cockpit fails to load for that meeting.
  **What to do:** run `/bug` to formally capture this as a new `BUG-NNN`
  (Area: Logic, Severity: Major — the whole Cockpit fails to load, not
  just a display glitch) so it can be triaged into a fix story; likely fix
  shape is either making `_coerce_people_list` also accept a plain list of
  wikilink strings (extracting a display name/email via the same pattern
  `people_extraction.py` already uses elsewhere) or a defensive per-item
  type check inside `resolve_people_chips`'s own loop.
  → `src/backend/app/business/cockpit/people.py`

- [x] 2026-08-19 · **BUGFIX-05-US-01** · `ADR-051` created (retargets
  `process_staged_email` off the old `thread_match_merge` pipeline) —
  review before `/plan-tasks`'s decomposer step locks tasks against it —
  Resolved directly by the operator, 2026-08-19 (see the story's own
  frontmatter `gate_reason` and `## Notes`): `ADR-051`'s own direction
  (compose the already-shipped Stage 1/Stage 2 functions, explicitly
  re-compose the three side-effects with no equivalent, deprecate-not-
  delete the old graph for `REQ-SB-65`'s Job Tree) approved as-is. **This
  approval does NOT cover a separate, new finding the decomposer pass
  made while locking tasks against it — see the new entry below
  (`ESC-055`) — `AC-01` stays unlocked pending that separate decision.**
  Plain English: the architect pass resolved this story's own open
  `## Constraints` question (does `thread_match_merge`'s other real
  side-effects — attachments, recurring-pattern, route-to-project,
  consult-librarian, project-synthesis — survive being replaced by
  `capture_raw_thread_messages`/`synthesize_thread`) into a real
  architectural decision, `ADR-051`: `process_staged_email`'s underlying
  implementation (`email_capture_pipeline.run_email_capture_pipeline`,
  same name/module/call shape) is retargeted from invoking the module's
  compiled `StateGraph` onto a plain, sequential composition of Stage 1
  (`capture_raw_thread_messages`) + Stage 2 (`synthesize_thread`), with
  three side-effects that have NO equivalent in the shipped `REQ-SB-71`/
  `REQ-SB-72` redesign (`detect_recurring_pattern`, `consult_librarian`,
  the ongoing Project-`## Glimpse` resync) explicitly, directly
  re-composed as plain calls in that same function. `email_capture_
  pipeline.py`'s `StateGraph`/`get_job_tree()`/`thread_match_merge` are
  DEPRECATED, not deleted — kept only because `get_job_tree()`
  (`REQ-SB-65-US-01`'s Pipeline Job Tree visualization) still reads the
  same compiled graph; that visualization becomes a disclosed, known-stale
  surface until a future story rebuilds it. `ADR-043`'s own `Status` line
  was updated to `Superseded by ADR-051` (points 1/3, live-execution
  halves only — its Decision/Context/Consequences text is untouched).
  **What to do:** review `ADR-051` in `Implementation/Architecture/
  ADR.md` (Decision, Alternatives Considered, Consequences) — in
  particular the "deprecate, don't delete" call on `email_capture_
  pipeline.py`'s `StateGraph`/`get_job_tree()` and the additive
  `conversation_ids_touched` return-key extension to `capture_raw_thread_
  messages` — approve or redirect, then either let `/plan-tasks`'s
  decomposer proceed to lock ACs/tasks against it, or reset
  `BUGFIX-05-US-01`'s `status:` (already `Draft`) with a Notes correction
  and re-run `/plan-tasks` once resolved.
  → `Implementation/Architecture/ADR.md` (ADR-051; ADR-043 Status line)
  → `Implementation/Architecture/architecture.md` ("`process_staged_email`
    Retargeted onto Stage 1/Stage 2 Composition")
  → `Implementation/UserStories/BUGFIX-05-US-01-email-thread-processing-retires-legacy-thread-match-merge.md`

- [x] 2026-08-19 · **BUGFIX-05-US-01** · `ADR-051`'s own rewire does NOT
  actually close `AC-01` (the flat-shape duplication facet) — a real
  duplicate already exists live in the vault, proving the true root cause
  is `vault_writer.list_thread_notes()`'s own blindness to flat,
  pre-redesign Thread notes, not which composing function calls it
  Plain English: the decomposer pass (`/plan-tasks` step 2) found, by
  direct code + real live vault reading, that `resolve_thread_directory`/
  `list_thread_notes()` (`Work/Threads/*/*.md` only) can never match a
  flat, top-level `Work/Threads/<name>.md` note — so `synthesize_thread`
  (the function `ADR-051` retargets `process_staged_email` onto) would
  ALSO fail to find a real, pre-redesign flat Thread and would create
  ANOTHER duplicate, just directory-shaped instead of flat. This is
  already confirmed happening for real: `ED0954959F6F4A4C88F9E2ACA3D7113A`
  has BOTH a real flat note (`RE- Azure-Net New Revenue Forecast...`,
  2026-07-27) AND a real directory-shaped duplicate with 4 of that same
  conversation's later messages (`2026-08-17 Azure-Net New Revenue
  Forecast...`). `AC-02` (the orphaning facet) is unaffected — genuinely
  closed by `ADR-051`'s rewire.
  **Resolved by the architect pass, 2026-08-19 (`ESC-055` re-opened,
  same day):** a new `ADR-052` decides the concrete design — see the NEW
  entry directly below for the human's own required review of `ADR-052`
  itself (trigger-3 fires again; this is a genuine second, separate
  architectural decision, not a rubber-stamp of the first). `ESC-055` is
  marked `Resolved` in `ESCALATIONS.md`, naming `ADR-052` as the resolving
  artefact. This checkbox closes the "what still needs a human/architect
  decision" question this entry originally raised — it does NOT mean
  `AC-01` is locked yet; that is the decomposer's own next step, gated on
  the human's review of `ADR-052` below.
  → `ESCALATIONS.md` (`ESC-055`, now `Resolved`)
  → `Implementation/Architecture/ADR.md` (`ADR-052`)

- [x] 2026-08-19 · **BUGFIX-05-US-01** · `ADR-052` created — legacy
  flat-shape Thread notes are now recognized by `resolve_thread_
  directory()` via a one-time, self-healing migration to the standard
  directory shape — review before the decomposer re-locks `AC-01` against it
  — **Resolved directly by the operator, 2026-08-19** (see the story's own
  frontmatter `gate_reason`: "operator in full autopilot for the
  remainder of the session... `ADR-052` is a narrow, well-grounded fix...
  Flag cleared on the same basis `ADR-047`/`048`/`049`/`050`/`051` were").
  `AC-01` re-locked against `ADR-052` this same decomposer pass — see
  `Implementation/Tasks/BUGFIX-05-US-01-T03-migrate-flat-thread-on-first-touch.md`
  and `...-T04-live-verification-flat-thread-migration-and-mode-flip.md`;
  the story advances `Draft → Ready`.
  Plain English: this closes `ESC-055`'s own gap — `resolve_thread_
  directory()` now ALSO scans genuinely flat, pre-redesign `Work/Threads/
  <name>.md` notes (which `list_thread_notes()` structurally can't see) and,
  on a match, migrates the note in place to the standard `<slug>/<slug>.md`
  + `messages/` directory shape before returning it — a real, disclosed
  WRITE side effect added to a primitive `ADR-049` previously called
  "purely read-only." This was confirmed NECESSARY, not just one option
  among several: direct reading of `synthesize_thread`'s own update-branch
  code shows that simply widening the glob and returning a flat note's own
  path UNMIGRATED would silently share one `messages/`/`files/` folder
  across every unmigrated flat Thread (a worse defect than the one being
  fixed) — see `ADR-052`'s own Context for the full reasoning. Ordering is
  load-bearing: the existing directory-shaped scan still runs first, so
  this does NOT retroactively fix the one already-diverged, already-live
  duplicate (`ED0954959F6F4A4C88F9E2ACA3D7113A`) — that stays a deliberate
  non-goal here, recommended instead for the Librarian's own future
  housekeeping scope (see the separate entry below for that decision).
  **What to do:** review `ADR-052` in `Implementation/Architecture/ADR.md`
  (Decision, Alternatives Considered, Consequences) — in particular the
  self-healing-migration-as-a-side-effect-of-a-lookup design and the
  deliberate "does not fix the already-diverged case" scope boundary —
  approve or redirect, then let `/plan-tasks`'s decomposer proceed to lock
  `AC-01` against it (recommended live-verification target: one of the
  7 flat notes WITHOUT an already-existing directory-shaped duplicate, not
  `ED0954959F6F4A4C88F9E2ACA3D7113A`, since that one would just re-confirm
  the existing duplicate rather than exercise the new migration path).
  → `Implementation/Architecture/ADR.md` (`ADR-052`; `ADR-049` Status line)
  → `Implementation/Architecture/architecture.md` ("Legacy flat-shape
    Thread recognition — self-healing migration on first touch")
  → `Implementation/UserStories/BUGFIX-05-US-01-email-thread-processing-retires-legacy-thread-match-merge.md`
  → `src/backend/app/data_access/vault_writer.py` (`list_thread_notes`,
    `resolve_thread_directory`, new `migrate_flat_thread_to_directory`)

- [ ] 2026-08-19 · **BUGFIX-05-US-01 / ESC-055** · the already-live,
  already-diverged Thread duplicate (`ED0954959F6F4A4C88F9E2ACA3D7113A`,
  "Azure-Net New Revenue Forecast for H2") is a real, current data-
  fragmentation issue in the operator's own vault, NOT fixed by `ADR-052`'s
  code fix and NOT addressed by this bugfix story — recommend a new,
  separately-scoped backlog item, not a silent drop
  Plain English: the flat note (2026-07-27, 1 message) and the
  directory-shaped duplicate (2026-08-17, 4 later messages of the SAME
  conversation) are real, already-split content today. Merging them
  requires combining `## Summary`/`## Personal Notes`/`## Actions`/
  `messages/`/`files/` content across two notes — a genuinely new
  capability this codebase does not have yet (not just a shape migration,
  which `ADR-052` already handles for every OTHER still-clean flat note).
  The architect's judgement: defer this to the Librarian's own future
  housekeeping scope (`REQ-SB-72`) as a new, systematic "detect and merge
  duplicate/split Threads sharing a `conversation_id`" Job, rather than a
  manual one-off fix inside `BUGFIX-05-US-01` — the story's own existing
  Non-Goals already scope this class of repair out ("Backfilling/repairing
  any already-orphaned Thread from a PAST live `thread_match_merge`
  run... out of scope unless a human explicitly asks for a retrofit/repair
  pass"), a systematic detector is more complete than hand-fixing the one
  known instance (there may be others not yet surfaced), and a hasty manual
  merge risks real data loss without a designed archive-not-delete path.
  **What to do:** decide whether to (a) accept the deferral — file a new
  PRD-level backlog item extending `REQ-SB-72` for a future "duplicate
  Thread detection & merge" Job, naming `ED0954959F6F4A4C88F9E2ACA3D7113A`
  as its first concrete real case, or (b) explicitly ask for a one-off
  manual reconciliation now instead. Either way, `BUGFIX-05-US-01` itself
  does not block on this decision — `AC-01`/`AC-02` are both fully
  verifiable without touching this specific already-diverged conversation.
  → `ESCALATIONS.md` (`ESC-055`)
  → `BACKLOG.md` (candidate new item, pending the human's choice above)

- [ ] 2026-08-19 · **BUGFIX-05-US-01-T02** · FYI (not blocking): a real,
  live orphaning incident (`BUG-026`'s own failure mode) briefly fired for
  real during this task's own live verification, self-detected and fully
  repaired by the coder — human spot-check recommended, not required
  Plain English: `T02`'s first live-verification attempt called the real
  `process_staged_email` capability against a backend server process that
  had been started BEFORE `T01`'s code fix landed (no `--reload`, so it
  never picked up the fix). That stale process ran the OLD, still-buggy
  `thread_match_merge` path for real, which orphaned the real
  `Work/Threads/2026-08-16 FW- Presight Agent Academy Demo/` Thread's own
  `messages/`/`files/` subfolders — `BUG-026` Scenario 2 firing live,
  exactly as this whole story exists to fix. The coder caught this
  immediately (the OLD "N email(s) filed" wording in the result, not
  `T01`'s new wording), confirmed via direct filesystem inspection that
  this was the ONLY real Thread affected (two other real Threads
  independently reprocessed by the same stale dispatch were confirmed
  unaffected), restored the Presight Thread's concept file byte-identical
  from a pre-test backup back into its correct directory location, deleted
  the resulting flat duplicate, restarted the backend server, confirmed
  the fresh process runs the corrected code, then re-ran the live
  verification cleanly to a genuine `AC-02` PASS. No code defect — this
  was a coder-side process-hygiene gap (verify the server has actually
  restarted before trusting HTTP-endpoint-based verification), not an
  architecture or requirements issue. `T02`/the story are NOT blocked —
  `AC-02` is genuinely verified passing and the real vault is confirmed
  restored to its correct state.
  **What to do:** optional spot-check — read `T02`'s own Implementation
  Log (full incident timeline + repair evidence) and, if desired, directly
  confirm `Work/Threads/2026-08-16 FW- Presight Agent Academy Demo/`'s own
  concept file/`messages/`/`files/` look correct in Obsidian. No action
  required to unblock anything.
  → `Implementation/Tasks/BUGFIX-05-US-01-T02-live-verification-directory-shaped-thread.md`

- [x] 2026-08-19 · **BUGFIX-05-US-01-T04** · BLOCKING: `AC-01` genuinely
  fails live — a freshly-migrated flat Thread's real, pre-migration
  `## Summary` content is silently lost, not preserved, the first time
  `synthesize_thread` runs on it — architect decision needed before
  `AC-01` can be re-locked/re-verified
  — **Resolved by the architect, 2026-08-19** (`/plan-tasks` step 1,
  re-opened to resolve `ESC-056`): decided a concrete fix, `ADR-053` — a
  one-time, self-consuming `pre_migration_summary.md` sidecar file (see
  the new entry below for the full write-up and its own required
  review). `T04` is now unblocked for the decomposer to re-lock `AC-01`
  against and a replacement/amended task to live-verify.
  Plain English: `T04`'s own live verification (a real, clean flat Thread,
  `conversation_id 041969487D51E942B77F5CD4A13A6CC2`, "Compass Alert:
  Failed API Calls") confirmed `T03`'s migration primitive itself works
  correctly (shape migrated, content byte-identical immediately after
  migration) — but the SAME composed pipeline tick immediately calls
  `synthesize_thread` next, which regenerates `## Summary` PURELY from the
  Thread's own `messages/` directory. Since the migration leaves
  `messages/` empty (per `ADR-052`'s own deliberate "touches only
  filesystem SHAPE" design), the Thread's real, substantive ORIGINAL
  `## Summary` text (describing the actual Compass API-failure alert) gets
  silently OVERWRITTEN and lost — replaced by a summary describing only
  the new triggering message. This directly contradicts `AC-01`'s own
  locked wording ("preserving its own prior content"). Not a `T01`/`T03`
  coding defect — both did exactly what their own specs said; this is a
  genuine, previously-undiscovered interaction gap between two already-
  `Accepted` ADRs (`ADR-051`'s composition, `ADR-052`'s migration) when
  chained together, only surfaced by `T04`'s own live, end-to-end test
  (neither `T01`'s nor `T03`'s own task-level smoke tests happened to
  chain "migrate a flat note" directly into "immediately synthesize it").
  The coder immediately repaired the real vault (byte-identical restore
  from a pre-test backup, `diff`-confirmed, both migration and lossy
  synthesis fully reversed — zero permanent data loss) and did NOT flip
  `email-capture-pipeline`'s working mode (the story's own Constraint
  requires BOTH `AC-01` AND `AC-02` verified passing first — `AC-01` is
  not). This also means the 6 other real, still-flat Threads in the live
  vault (7 minus the one `T03`'s own smoke test already migrated, which is
  itself sitting in this same at-risk, not-yet-synthesized state right
  now) will each hit this SAME content-loss the first time a genuinely new
  message organically arrives for them, until this is fixed — not a
  test-only risk.
  **What to do:** the architect needs to decide how the migration+
  synthesis flow should preserve a freshly-migrated Thread's own real
  pre-migration `## Summary` content — `ESC-056` lays out three
  non-decided candidate approaches (backfill a reconstructed raw message
  note; merge old+new `## Summary` via a Thread-state-aware `synthesize_
  thread` variant; copy `## Summary` verbatim during migration itself and
  change `synthesize_thread` to append-not-replace when no raw messages
  exist yet). Once decided (likely a new or amended ADR), the decomposer
  re-locks `AC-01` against the new design and creates a replacement `T04`
  (or amends this one, since it is not `Done`). Until then: `T04` stays
  `Blocked`, the story stays `In Progress`/cannot reach `Done`, `email-
  capture-pipeline`'s working mode stays `supervised`, and `BUG-026` stays
  `In Sprint` (not `Closed`) in `BUGS.md`/`BACKLOG.md`.
  → `ESCALATIONS.md` (`ESC-056`)
  → `Implementation/Tasks/BUGFIX-05-US-01-T04-live-verification-flat-thread-migration-and-mode-flip.md`

- [x] 2026-08-19 · **BUGFIX-05-US-01** · `ADR-053` created — closes
  `ESC-056`'s own content-loss gap via a one-time, self-consuming
  `pre_migration_summary.md` sidecar file — review the integration
  approach before `AC-01` is re-verified and the working-mode flip is
  attempted
  — **Resolved by the operator directly, 2026-08-19** (full autopilot,
  same "resolve directly when the fix only adds safety, never removes it"
  judgment used all night — see the story's own frontmatter `gate_reason`).
  The decomposer then re-locked `AC-01` against `ADR-053`'s concrete
  design and created `BUGFIX-05-US-01-T05` (the sidecar write+read+archive
  mechanism, one combined task spanning `vault_writer.py` +
  `email_classification.py`), amending `T04` in place (`Blocked` →
  `Ready`, `depends_on` gains `T05`) to also verify the sidecar fold-in/
  archive. See the story's own "Decomposer pass (re-lock #2)" `## Notes`
  section for the full task-placement reasoning and re-verification-target
  confirmation.
  Plain English: `T04`'s own live verification found that `ADR-052`'s
  migration mechanism, though correct in isolation, loses a freshly-
  migrated flat Thread's real, pre-migration `## Summary` the first time
  `synthesize_thread` runs on it (it regenerates `## Summary` purely from
  `messages/`, which the migration correctly leaves empty). `ADR-053`
  decides the fix: `migrate_flat_thread_to_directory` now also writes the
  flat note's own pre-migration `## Summary` (verbatim) to a new sidecar
  file, `pre_migration_summary.md`, living OUTSIDE the Thread's
  `messages/` directory so it can never pollute message-count,
  participant-accumulation, or first-message classification. `synthesize_
  thread` gains one small, additive read: if that sidecar exists, its
  text is prepended to the SAME existing Compass call as prior-history
  grounding (never a second call), and on a successful synthesis the
  sidecar is renamed in place to `pre_migration_summary.consumed.md` —
  never deleted, fed exactly once. This is a deliberate, disclosed
  departure from `BUGFIX-05-US-01-T01`'s own task-level "must NOT modify
  `email_classification.py`" constraint (that constraint was scoped to
  `T01`'s own narrower rewire concern, not a standing prohibition); the
  decomposer must create/amend a task touching both `vault_writer.py` and
  `email_classification.py`. None of `ESC-056`'s own three candidate
  options were adopted as-is — each had a real, disclosed problem found
  by direct code reading (see `ADR-053`'s own Alternatives Considered);
  this sidecar design was chosen instead, specifically because it cannot
  corrupt classification/participants/message-count the way backfilling a
  synthetic raw message into `messages/` would have, and does not make
  `vault_writer.py` a second, uncoordinated writer of a `section_
  ownership.py`-governed header the way writing directly into the concept
  file's own `## Summary` region would have.
  **What to do:** review `ADR-053` in `Implementation/Architecture/ADR.md`
  and the new "Migration content-preservation — the
  `pre_migration_summary.md` sidecar" section in `architecture.md`;
  approve or reject, then run `/plan-tasks` again (the decomposer
  re-locks `AC-01` against this design and creates/amends the task that
  live-verifies it).
  → `Implementation/Architecture/ADR.md` (`ADR-053`)
  → `Implementation/Architecture/architecture.md`
  → `ESCALATIONS.md` (`ESC-056`, now `Resolved`)
  → `Implementation/UserStories/BUGFIX-05-US-01-email-thread-processing-retires-legacy-thread-match-merge.md`

- [x] 2026-08-19 · **BUGFIX-05-US-01-T05** · FYI (not blocking): one real,
  already-migrated Thread (`RITM0108464`) needs a one-time sidecar
  backfill before its next natural update, or it will hit the SAME
  content-loss bug `ESC-056` found
  — **Done, 2026-08-19:** the backfill was performed and verified. Its
  precondition was re-confirmed at execution time (`messages/` still
  empty, `## Summary` still intact, 537 chars) before writing `Work/
  Threads/CF7FD118DD45F740ACAD6B93AB83BEB5/pre_migration_summary.md`,
  byte-identical to that `## Summary`. See `T05`'s own Implementation Log.
  Plain English: `BUGFIX-05-US-01-T03`'s own smoke test already
  permanently migrated one real flat Thread (`conversation_id
  CF7FD118DD45F740ACAD6B93AB83BEB5`, "Requested Item RITM0108464 has been
  updated") to the standard directory shape BEFORE `ADR-053`'s
  `pre_migration_summary.md` sidecar mechanism existed. Its own real
  pre-migration `## Summary` is confirmed still intact right now (`T03`'s
  own Implementation Log, byte-identical, `synthesize_thread` has not run
  on it since) — but it has no sidecar, so it carries the exact same
  latent content-loss risk `ESC-056` found, live, for this one specific
  real Thread, the moment a genuinely new message next arrives for it
  naturally. This is not an open question — it is a direct, bounded
  application of `ADR-053`'s own already-decided sidecar shape to one
  already-known real case, so the decomposer resolved it directly (no ADR
  change, no ambiguity) rather than flagging it as blocking: `T05` (`Ready`)
  performs a one-time, explicitly-gated manual backfill for this ONE
  Thread only (re-confirming its `## Summary`/empty `messages/` state is
  still exactly as `T03` left it before writing the sidecar; escalates
  instead of fabricating if not).
  **What to do:** nothing required — informational only. If you want to
  confirm the backfill yourself once `T05` ships, check
  `Work/Threads/CF7FD118DD45F740ACAD6B93AB83BEB5/pre_migration_summary.md`
  exists in the real vault.
  → `Implementation/Tasks/BUGFIX-05-US-01-T05-preserve-pre-migration-summary-via-sidecar.md`
  → `Implementation/UserStories/BUGFIX-05-US-01-email-thread-processing-retires-legacy-thread-match-merge.md`

- [ ] 2026-08-19 · **BUGFIX-05-US-01-T04** · FYI (not blocking): two real,
  live incidents briefly fired during this task's own second live-
  verification attempt (a stale-server repeat of the T02 failure class,
  plus a diagnostic call that side-effect-triggered a migration outside
  the real endpoint), both self-detected and fully repaired — human
  spot-check recommended, not required
  Plain English: (1) a diagnostic call to `vault_writer.resolve_thread_
  note_path` — made while re-confirming the reserved verification
  candidate's own clean state — triggered `resolve_thread_directory`'s own
  documented side-effecting second-scan tier and silently migrated the
  real "Compass Alert- Failed API Calls" Thread outside the real
  capability endpoint this task's own Constraints require; no content was
  lost (`migrate_flat_thread_to_directory` is a pure rename plus the new
  sidecar, confirmed byte-identical), repaired immediately by renaming the
  concept file back to its flat path and removing the sidecar/directory.
  (2) Separately, the first tracked verification attempt (through the real
  capability endpoint) ran against a `uvicorn` process that had been
  started BEFORE this session's own `T05` code edits landed (no
  `--reload`) — reproducing `ESC-056`'s ORIGINAL pre-`ADR-053` bug exactly
  (no sidecar written, `## Summary` silently replaced by only the new
  message). Diagnosed (not assumed) via the process's own `CreationDate`
  predating the code edits. The real Thread was restored a second time,
  reconstructed byte-for-byte from this task's own two independent `Read`
  tool outputs of the file (no other backup existed — the vault itself is
  not under git). Stale processes killed cleanly (confirmed zero orphans),
  a fresh server started, confirmed responding with the correct code
  before the clean, passing re-attempt. No code defect in either case —
  both are coder-side process/script discipline gaps (the same failure
  class `T02`'s own incident already flagged once this story), not an
  architecture or requirements issue. `T04`/the story are NOT blocked —
  both `AC-01` and `AC-02`'s flip clause are genuinely verified passing
  and the real vault is confirmed in its correct, permanent, post-fix
  state.
  **What to do:** optional spot-check — read `T04`'s own second
  Implementation Log entry (full incident timeline + repair evidence) and,
  if desired, directly confirm `Work/Threads/041969487D51E942B77F5CD4A13A6CC2/`'s
  own concept file/`## Summary`/`pre_migration_summary.consumed.md` look
  correct in Obsidian. No action required to unblock anything.
  → `Implementation/Tasks/BUGFIX-05-US-01-T04-live-verification-flat-thread-migration-and-mode-flip.md`

- [ ] 2026-08-19 · **BUGFIX-06-US-01-T01** · FYI (not blocking): one
  scope-internal judgement call made to fill a real verification gap —
  the live vault currently has no note anywhere with a real `recipients`
  field, so `AC-02`'s own "already-JSON-encoded-string shape unregressed"
  facet was verified via a temporarily added, fully reverted field rather
  than a pre-existing real note
  Plain English: `AC-02`'s own `## Tests` step 4 asks to confirm the
  pre-existing JSON-encoded-string `recipients` shape is unregressed
  against a real subject note already carrying that shape. A full-vault
  grep (migration_backup excluded) found none — the pipeline that used to
  write `recipients` as a JSON-encoded string moved to the Thread-based
  model (`REQ-SB-71-US-02`) and no live note retains the old field. Reused
  the SAME "direct, reverted file edit" technique `AC-02`'s own step 3
  already sanctions for the orphan-wikilink-stem facet, applied here to a
  different field on the same real Meeting note (Alignment Mubadala):
  temporarily added `recipients: "[{\"name\": \"Maik Alexander Kurz\",
  \"email\": \"maik.kurz@core42.ai\"}]"`, rebuilt the index, called
  `GET /cockpit/email/Alignment%20Mubadala-2026-08-17-a4737bc4` → `200`
  with a correctly-resolved real chip, then reverted the field and
  rebuilt the index again, confirming the file is byte-for-byte identical
  to its pre-test state. This shape's own code path
  (`json.loads` → dict passthrough, short-circuiting `_normalize_
  person_item`'s `isinstance` check before it ever reaches the new
  wikilink-handling branch) is unaffected by this fix by construction, so
  the real-note substitution does not weaken the confidence of the
  result — both `AC-01` and `AC-02` are genuinely verified PASS.
  **What to do:** optional spot-check — read `BUGFIX-06-US-01-T01`'s own
  Implementation Log for the full verification record (all four
  `GET /cockpit/...` calls plus the two revert confirmations). No action
  required to unblock anything; `BUG-027` is already `Closed`.
  → `Implementation/Tasks/BUGFIX-06-US-01-T01-wikilink-string-attendee-resolution.md`

- [ ] 2026-08-19 · **REQ-SB-73-US-01** · review `ADR-054` (Bidirectional
  Thread ↔ Message Linking) before the build starts
  Plain English: the architect wrote one ADR covering three things — a new
  `link_thread_messages()` Librarian Job that regenerates a Thread's own
  `## Messages` section and self-heals every message's `thread:` backlink,
  a bounded extension to the already-shipped `rename_threads()` Job so a
  rename fans its new slug out to every one of that Thread's own messages
  in the SAME atomic operation (zero staleness window, not "eventually
  consistent"), and — found independently while grounding the story,
  not something the story itself named — a small `vault_indexing.py`
  extension so the vault's own outgoing-wikilink index also scans
  frontmatter string values, not just note bodies. Without that third
  piece, the new `thread:` field would have been silently invisible to
  the already-shipped backlinks panel and graph view, which is exactly
  the surface this story exists to light up — worth a human's eyes before
  the decomposer locks tasks against it, since it touches a shared,
  cross-cutting indexing primitive no other open story currently names.
  **What to do:** review `ADR-054` in
  `Implementation/Architecture/ADR.md`, approve or reject (especially the
  `vault_indexing.py` extension and the `rename_threads()` fan-out), then
  run `/plan-tasks` again if you change it.
  **Coder update (2026-08-19):** per the `SPRINT-060`/`ADR-048` precedent
  (built while that story's own standing ADR-review flag was still open),
  this standing flag did not block the build — `REQ-SB-73-US-01` is now
  `Done` (all 4 tasks built and live-verified against the real vault,
  `SPRINT-067` closed). This review item stays open for your own read of
  `ADR-054` itself; nothing further is blocked on it.
  → `Implementation/UserStories/REQ-SB-73-US-01-bidirectional-thread-message-linking.md`

- [ ] 2026-08-19 · **REQ-SB-74-US-01** · review `ADR-055` (Customer
  Backfill — batched approvals + archival-move primitive) before the
  build starts
  Plain English: the architect wrote one ADR covering four things — a
  decision to batch every Thread proposed for the SAME Customer into ONE
  Pending Approval (the first multi-target approval in this codebase;
  confirmed by direct reading that the existing approval registry and its
  Approve/Decline dispatch table need ZERO code change to support this,
  since they were already generic — the ADR records this as the
  codebase's new canonical shape for any future multi-target approval,
  worth a human's eyes since it sets precedent); a new Compass call that
  decides a Thread's own primary Customer (reuse an existing folder,
  propose a brand-new one like TAQA, or leave it Unsorted); a new
  enumeration of the real Customer folders on disk (deliberately
  different from the existing `list_known_customers()`, which reads
  frontmatter usage, not folder existence); and a new, generic
  "move a whole Customer folder to `Work/Archive/Customers/`, content
  byte-for-byte unchanged" primitive for the noise-reconciliation half of
  this story. Review before 137 real Threads start getting routed off of
  it.
  **What to do:** review `ADR-055` in
  `Implementation/Architecture/ADR.md`, approve or reject (especially the
  batched-approval payload convention and the archival-move primitive's
  target path), then run `/plan-tasks` again if you change it.
  **Coder update (2026-08-19):** per the `SPRINT-060`/`SPRINT-067`
  precedent (built while the story's own standing ADR-review flag was
  still open), this standing flag did not block the build —
  `REQ-SB-74-US-01` is now `Done` (all 6 tasks built and live-verified
  against the real vault: a real 133-Thread backfill run, 10 Threads
  genuinely routed, 1 new Customer folder created (`TAQA`), 2 folders
  archived (`Twitter`, `Google`), `SPRINT-068` closed). This review item
  stays open for your own read of `ADR-055` itself; nothing further is
  blocked on it. See the two new entries below for real findings from
  this build worth your attention: the pending-approvals queue state and
  a real archival false-positive nuance.
  → `Implementation/UserStories/REQ-SB-74-US-01-customer-backfill-thread-routing-and-noise-reconciliation.md`

- [ ] 2026-08-19 · **REQ-SB-74-US-01** · 64 pending Customer-routing +
  31 pending archival-candidate real Pending Approvals await your review
  (substantial duplication, never auto-approved)
  Plain English: this build's own live verification triggered the real
  full-corpus backfill 3 separate times (once per task needing its own
  real HTTP/function-level proof — `T01`, `T05`'s component check, `T06`'s
  own idempotency re-run), and `ADR-055`'s own accepted "no idempotency
  guard on `trigger="direct"`" design means each trigger re-proposes
  every STILL-`"Unsorted"` Thread into a fresh, separate batch rather
  than collapsing into the earlier one. Real result: 64 pending
  `propose_customer_backfill_routing` records and 31 pending `propose_
  customer_archival_candidate` records exist right now, with real
  duplication (the same Customer proposed 2-3 times across the 3 runs).
  Nothing was auto-approved or mass-processed — only a small, individually
  verified handful were resolved during testing (2 routing batches
  approved for real — `Aldar`, `LinkedIn`; 2 archival candidates approved
  for real — `Twitter`, `Google`; a handful of the most clearly-stale
  duplicates/false-positives declined, named in `T05`/`T06`'s own
  Implementation Logs).
  **What to do:** review `GET /pending-approvals` for the real, current
  list; for each Customer with multiple duplicate routing batches, approve
  the one naming the most Threads (or the latest) and decline the rest;
  for archival candidates, read the next queue item below BEFORE approving
  any — some are real false positives, not genuine noise.
  → `Implementation/Tasks/REQ-SB-74-US-01-T06-backfill-run-and-idempotency-verification.md`

- [ ] 2026-08-19 · **REQ-SB-74-US-01** · real archival false-positive
  nuance — a Customer already routed in an EARLIER pass gets wrongly
  re-proposed for archival in a LATER pass
  Plain English: `propose_customer_archival_candidates` only ever checks
  "did this Customer get a real Thread match THIS SAME pass" (`ADR-055`
  Decision 5, by design — never a cross-pass memory). Once a Customer's
  entire real Thread-match set has already been approved/routed in an
  earlier pass, none of its Threads are `"Unsorted"` anymore for a LATER
  pass to match — so the LATER pass honestly (per its own literal,
  locked-AC wording) finds "zero real Thread matches this pass" and
  proposes archiving an actively-used, real Customer folder. Observed for
  real twice this session (`Aldar`, `LinkedIn`) — both declined, never
  approved, to protect real data. Not a violation of any locked AC
  (Scenario 4's own wording is genuinely "this pass," not cumulative), but
  a real UX rough edge for a manually-re-triggerable Job.
  **What to do:** decide whether this needs a follow-up story adding a
  "has real, currently-linked Threads" cross-pass exclusion to `propose_
  customer_archival_candidates` (out of `REQ-SB-74-US-01`'s own locked
  scope) — and, in the meantime, always cross-check an archival candidate
  against its own folder's real content before approving.
  → `Implementation/Tasks/REQ-SB-74-US-01-T06-backfill-run-and-idempotency-verification.md`

- [ ] 2026-08-19 · **REQ-SB-75-US-01-T03** · scope-internal judgement
  call — `src/frontend/src/main.tsx` touched outside this task's own
  `## Files to Modify` list, to add `import './styles/vault-graph.css'`
  Plain English: the task's own End-State text requires `vault-graph.css`
  to be "imported globally alongside the other per-feature stylesheets,"
  and `main.tsx` is the one real place every existing per-feature
  stylesheet (`vault-browser.css`, `agent-panel.css`, `cockpit.css`, ...)
  is imported — there is no other mechanism to satisfy the task's own
  already-specified requirement. A mechanical, one-line, same-pattern
  addition (no new logic), not a scope expansion of intent. All 6 locked
  ACs (`REQ-SB-75-US-01-AC-01`..`AC-06`) were verified live and pass —
  nothing is blocked; this is a spot-check item, not a build blocker.
  **What to do:** confirm the `main.tsx` one-line addition is an
  acceptable "strong-default, not absolute-ceiling" extension of this
  task's own `## Files to Modify` list (this project's own established
  precedent, `SPRINT-021`/`SPRINT-037` Learnings) — no action needed
  unless the human disagrees with the judgement call itself.
  → `Implementation/Tasks/REQ-SB-75-US-01-T03-vault-graph-page-and-nav.md`

- [ ] 2026-08-19 · **SPRINT-070** · skim the sprint retrospective and harvest learnings
  Plain English: SPRINT-070 (`BUGFIX-07-US-01`, `BUG-028` fix — Customer/
  Project `log.md`/`captures.md` now carry an identifying header) is
  Done — its one task built and both locked ACs verified live against the
  real vault. The coder drafted a Retrospective (sizing accuracy, what
  worked/didn't, patterns/antipatterns, open follow-ups) in the sprint
  file, but does not write `Implementation/Learnings.md` directly — that's
  a human step.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" and "Antipatterns
  to avoid" entries into `Implementation/Learnings.md`.
  → `Implementation/Sprints/SPRINT-070-okf-directory-log-captures-identifying-header.md`

- [ ] 2026-08-19 · **BUGFIX-07-US-01-T01** · scope-internal judgement call
  — declined to mutate any real, already-existing Customer/Project
  directory during verification
  Plain English: the task's own `## Tests` step 4 invited (but did not
  require) exercising `ensure_customer_directory_baseline` against one
  real, already-existing, pre-fix headerless Customer folder if
  "convenient." A read-only scan of every real Customer folder (26+) and
  the one real Project directory in the live vault confirmed every single
  `log.md`/`captures.md` is genuinely empty — no real, content-bearing,
  pre-fix candidate exists to backfill against. The coder chose not to
  run the fix against a real, content-free folder anyway, since it would
  add no verification signal beyond the synthetic empty-file check already
  performed, and would otherwise mutate production data with no
  compensating benefit. Both locked ACs (`AC-01`, `AC-02`) still verified
  PASS via the synthetic throwaway directory; nothing is blocked.
  **What to do:** confirm this verification-approach choice is acceptable
  (no action needed unless the human disagrees) — `REQ-SB-74`'s own
  planned backfill pass will apply the header to real data naturally the
  next time each real directory's own `ensure_*` path runs.
  → `Implementation/Tasks/BUGFIX-07-US-01-T01-okf-log-captures-header.md`

- [ ] 2026-08-19 · **BUGFIX-08-US-01** · review `ADR-056` (target-aware
  `dedupe_key` on `create_pending_approval`) before tasks are locked
  Plain English: closing `BUG-029` (meeting-capture's `run_capture_now`
  fired twice near-simultaneously — a scheduled tick and a manual
  "Run Capture Now" both created their own live Pending Approval) and
  `BUG-030` (a staged email/Thread, or a Librarian Customer-backfill
  batch, gets re-proposed as a fresh duplicate on every later capture/Job
  tick while the first proposal still sits unresolved), the architect
  wrote `ADR-056`: `create_pending_approval` gains an additive, optional
  `dedupe_key` parameter — a second idempotency check, alongside (never
  replacing) the existing `trigger == "background"` guard, that matches on
  `agent_id` + `dedupe_key` regardless of `trigger`. Wired into
  `skill_registry.py::invoke_skill`'s own central Supervised-gate (closes
  BUG-029 for any Supervised mutating Skill, not just meeting-capture),
  `email_classification.py::route_to_project`/`_create_classification_
  failure_pending_approval`, and `librarian_housekeeping.py::propose_
  customer_backfill`/`propose_customer_archival_candidates`. The architect
  also concluded the existing shared dispatch lock does NOT need
  restructuring — BUG-029's literal race is not reproducible against the
  current, already lock-consolidated `dispatch_with_shared_lock` path, so
  the `dedupe_key` check (deterministic, unit-testable, caller-independent)
  is the sole mechanism, not a belt-and-suspenders addition to a lock fix.
  **What to do:** review `ADR-056` in
  `Implementation/Architecture/ADR.md`, approve or reject the mechanism
  (including the "no lock change needed" reasoning in its Context/
  Alternatives Considered), then run `/plan-tasks` again if you change it.
  **Update 2026-08-19 (`/implement-sprint SPRINT-071`):** both tasks are now `Done` and both
  locked ACs verified live against the real backend/vault exactly per `ADR-056`'s own decided
  mechanism (no deviation) — the story and `SPRINT-071` are `Done`, `BUG-029`/`BUG-030` are
  `Closed`. This entry stays open for the human's own `ADR-056` sign-off; nothing further is
  blocked on it, and no code change is pending behind it.
  → `Implementation/UserStories/BUGFIX-08-US-01-pending-approval-target-aware-dedup.md`

- [ ] 2026-08-19 · **REQ-SB-76-US-01** · review `ADR-057` (Company Review
  mechanism + a narrow, additive revision of `ADR-009` point 3) before
  tasks are locked
  Plain English: the architect wrote `ADR-057` to cover this story's own
  real mechanism decisions — a new, boilerplate-aware Compass extraction
  call that replaces (in practice, not by editing) the already-`Done`
  `detect_customer_for_thread`; one batched Pending Approval per company
  offering all five outcomes (Customer/Partner/Affiliate/Merge/Decline),
  resolved through a new, additive decision body on the existing Approve
  endpoint; a real fix to `migrate_customer_to_partner`'s silent no-op
  against today's OKF-shaped Customer directories; and a generalized
  retag-scan primitive the new Merge outcome reuses rather than inventing a
  third move/retag mechanism. The one genuinely architectural change worth
  a human's own look: `ADR-009`'s "Partner has no Affiliate concept"
  sub-clause (point 3) is narrowly, additively revised — Partner gains a
  real `affiliate_of` field, mirroring Customer's own restored field —
  while `ADR-009`'s real point (Customer/Partner mutual exclusivity, point
  1) and every other point stay untouched and `Accepted`. `ADR-009`'s own
  `**Status:**` line was updated to record this (never rewritten).
  **What to do:** review `ADR-057` in
  `Implementation/Architecture/ADR.md` (and `ADR-009`'s updated `**Status:**`
  line), approve or reject the mechanism — including the disclosed
  Consequences (a Partner-shaped Merge duplicate is retargeted but not yet
  archived; a natively-created Partner stays flat-file-shaped while a
  migrated/merged-in one becomes directory-shaped) — then run `/plan-tasks`
  again if you change it. This does not halt the pipeline — the decomposer
  still runs so you review `ADR-057` and the resulting tasks together in
  one pass.
  **Update 2026-08-19 (`/plan-tasks` step 2):** the decomposer has now locked all
  11 ACs (10 from the analyst's own scenarios, plus `AC-11` — a decomposer-added
  structural AC for the new decision control, per this role's own screen/frontend
  rule) and written 9 task files (`REQ-SB-76-US-01-T01` through `T09`), and the
  story has advanced `Draft → Ready`. `gate` deliberately stays `flagged` — this
  entry is NOT resolved by that pass; it still awaits your own `ADR-057` sign-off,
  reviewed together with the resulting 9 tasks per the note above.
  → `Implementation/UserStories/REQ-SB-76-US-01-company-review-extract-classify-and-batch-apply.md`

- [ ] 2026-08-19 · **REQ-SB-79-US-01** · review `ADR-058` (Librarian splits
  into Threads Cleaning / Company and Partner Building) before tasks are
  locked
  Plain English: the architect wrote `ADR-058` to cover this story's own
  real mechanism decisions — two new Agent identities ("Threads Cleaning",
  "Company and Partner Building") under the same existing Librarian
  Section; ALL FIVE real Pending-Approval-creating call sites in
  `librarian_housekeeping.py` re-home from the old shared
  `librarian-housekeeping` identity onto the new "Company and Partner
  Building" one (confirmed by direct reading — the four Threads Cleaning
  jobs create zero Pending Approvals and need no such edit); and
  `run_housekeeping_pass()` splits into two independently-scheduled
  orchestrators. The one genuinely new architectural primitive worth a
  human's own look: `agent_registry.py` gains its FIRST "retire without
  delete" mechanism (a `retired` flag + `retire_agent()` +
  `list_agents(include_retired=False)`) so the old `librarian-housekeeping`
  identity can be idempotently retired (never deleted, never renamed) at
  every app start, while every already-existing Pending Approval/Agent
  History record attributed to it keeps resolving a real, honest agent
  name forever via the unfiltered `get_agent()`. This composes with a
  real, disclosed cross-story dependency: `REQ-SB-77-US-01`'s own
  scheduled People-relinking self-heal task cannot be built before this
  story's new `run_company_partner_building_pass()` function exists —
  see `REQ-SB-77-US-01`'s own `## Notes` for the matching finding.
  **What to do:** review `ADR-058` in
  `Implementation/Architecture/ADR.md` — especially the "retire without
  delete" primitive and its rejected alternatives (renaming the existing
  identity in place; retroactively rewriting historical records) — approve
  or reject, then run `/plan-tasks` again if you change it. This does not
  halt the pipeline — the decomposer still runs so you review `ADR-058`
  and the resulting tasks together in one pass. Also confirm the
  decomposer/product-owner correctly wire the `REQ-SB-77-US-01` cross-story
  `depends_on` edge named above.
  → `Implementation/UserStories/REQ-SB-79-US-01-librarian-two-sub-pipelines.md`

