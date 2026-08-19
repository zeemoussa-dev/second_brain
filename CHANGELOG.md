# CHANGELOG

All notable changes to Second Brain.

<!-- Format:
## YYYY-MM-DD — Sprint NNN / task description
- feat: what was added
- fix: what was fixed
- refactor: what was restructured
- docs: documentation changes
-->

## [Unreleased]

- feat: `SPRINT-072` / `REQ-SB-76-US-01` — Company Review: boilerplate-aware
  company extraction replaces direct Thread→Customer routing; one batched
  Pending Approval per company with a real 5-way outcome (Customer / Partner
  / Affiliate-of-an-existing-Customer-or-Partner / Merge-into-an-existing-
  entity / Decline), approving batch-applies to every real Thread in one
  pass; `affiliate_of` restored on the current OKF Customer shape and added
  to Partner's shape for the first time (`ADR-057`, narrowly revising
  `ADR-009`); `migrate_customer_to_partner` fixed to work against the real
  OKF directory shape, closing `REQ-SB-62`. Live-verified against the real
  vault: 9 real classification decisions made (Core42→Partner, Masdar/
  Mubadala→Customer, Sindan→Affiliate-of-Mubadala, G42→Affiliate-of-Core42,
  ADFEC and Mubadala Investment Company→Merge, LinkedIn→Decline), 39 real
  proposals left pending for the operator's own review. Two real, non-
  blocking nuances found live and logged in `MEMORY.md` (Merge-source names
  can be re-proposed on a later pass; `## Related` doesn't accumulate across
  3+ separate resolutions on the same Thread).
- fix: `SPRINT-071` / `BUGFIX-08-US-01` (`BUG-029`, `BUG-030`) — Pending Approvals gain a
  target-aware `dedupe_key` idempotency check (`ADR-056`), closing the concurrent-trigger
  race (`meeting-capture`'s `run_capture_now` firing near-simultaneously via a scheduled
  tick and a direct dispatch) and the same-target reprocessing duplication (staged
  emails/Threads and Librarian Customer-backfill/archival proposals re-created on every
  later capture/Job tick). `pending_approval_registry.create_pending_approval`
  (`src/backend/app/business/pending_approval_registry.py`) gains an additive, optional
  `dedupe_key: str | None = None` — a second, independent idempotency check, alongside
  (never replacing) `ADR-018` point 2's existing `trigger == "background"` guard, matching
  an existing `status == "pending"` record on the same `agent_id` + `dedupe_key` regardless
  of `trigger`. Wired into `skill_registry.py::invoke_skill`'s central Supervised+mutates
  gate (`dedupe_key = f"{agent_id}:{skill_id}"`, computed internally — zero change to any
  caller, closing `BUG-029` for every Supervised mutating Skill, not just
  `meeting-capture`), and into the four real `BUG-030` call sites:
  `email_classification.py::route_to_project`/`_create_classification_failure_pending_
  approval`, `librarian_housekeeping.py::propose_customer_backfill`/`propose_customer_
  archival_candidates`. Both locked ACs verified live against the real backend/vault/store.
  `BUG-029`/`BUG-030` closed.
- fix: `SPRINT-070` / `BUGFIX-07-US-01` (`BUG-028`) — Customer/Project
  `log.md`/`captures.md` now open with an identifying `# {name}\n\n`
  header instead of anonymous empty content, mirroring `index.md`'s own
  already-`Accepted` header convention. `create_okf_directory_baseline`/
  `ensure_okf_directory_baseline` (`src/backend/app/data_access/
  vault_writer.py`) gained a required `identifying_name: str` parameter
  and a new shared `_write_or_backfill_identifying_header` helper — writes
  the header on fresh creation, backfills it onto an already-existing
  headerless file (empty or already carrying real appended content, e.g.
  from `append_person_note_update_line`) without disturbing a single
  byte, and leaves an already-headered file completely untouched
  (idempotent). All four Customer/Project wrapper functions
  (`create_customer_directory_baseline`/`ensure_customer_directory_
  baseline`/`create_project_directory_baseline`/`ensure_project_
  directory_baseline`) updated to pass their own real display name.
  Both locked ACs verified live against the real `vault_writer` functions
  and the real, configured vault (throwaway Customer/Project directory,
  cleaned up after). `BUG-028` closed.
- feat: `SPRINT-069` / `REQ-SB-75-US-01` (The Vault — Real-Data Knowledge
  Graph Screen) — new interactive force-directed graph screen at `/vault`
  reshaping the existing `vault_indexing.get_index()` snapshot (686 real
  notes, 1467 real resolved-wikilink edges) into `{nodes, edges}`, with
  kind filters (live counts, fully hide/show, never dim), name search, and
  click-through to the existing, unmodified `/browse/:stem` route. All 3
  tasks `Done`, all 6 locked ACs live-verified against the real backend
  and a real, running headless-browser session.
  New `vault_search.get_graph()` (reuses `_summary()`/`_kind_for()`
  verbatim; edges via a new `_resolve_forward_link_stems()` sibling of
  the existing `_resolve_forward_links`, same case-insensitive
  stem-matching rule, dangling/self targets silently omitted) plus
  `GET /vault-search/graph`, additive on the existing `/vault-search/*`
  router — zero new indexing/caching, zero new router/module.
  New `src/frontend/src/features/vault-graph/` — `forceLayout.ts` (pure
  repulsion+spring+centering physics tick, no DOM/canvas access),
  `client.ts` (`fetchVaultGraph()`, same thin-wrapper convention as
  `vault-browser/client.ts`), `VaultGraphCanvas.tsx` (hand-rolled
  `<canvas>` + `requestAnimationFrame` force-directed renderer with
  drag/zoom/pan and click-to-navigate via `useNavigate()` — zero new npm
  dependency, a new sibling to `AgentsMapCanvas.tsx`, not a reuse of it).
  New `tokens.css` node-kind-color rotating palette
  (`--graph-kind-color-1`..`-8`, drawn from this app's own already-curated
  hues) + `--graph-edge-color`, so an open-ended, real `frontmatter.type`
  set (`RawMessage`, `Thread`, `File`, `Person`, `Meeting`, `customer`,
  `Partner`, `Unknown`, `project` observed live) colors deterministically
  with zero hardcoded literals and zero fixed kind-name enum.
  New `src/frontend/src/pages/VaultGraphPage.tsx` (fetch-once,
  client-side kind-filter/search state), `/vault` route in `App.tsx`,
  "The Vault" nav entry in `Sidebar.tsx` (after "Browse & Search"), new
  `vault-graph.css`. One scope-internal judgement call disclosed
  (`main.tsx` touched to wire the new stylesheet's global import,
  outside `T03`'s own `## Files to Modify` list) — flagged in
  `REVIEW-QUEUE.md` for human spot-check; not a blocker.
- feat: `SPRINT-068` / `REQ-SB-74-US-01` (Customer Backfill — Propose/
  Approve Thread Routing + Noise Reconciliation, `ADR-055`) — the
  Librarian's new batched propose/approve Customer-routing Job, all 6
  tasks `Done`, live-verified against the real, 133-Thread/28-folder
  vault. New `compass_client.detect_customer_for_thread` (narrower
  sibling of `classify_task`); new `vault_writer.list_customer_folders()`
  and `vault_writer.move_okf_directory()`; new `librarian_housekeeping.
  propose_customer_backfill()`/`finalize_customer_backfill_routing()`/
  `propose_customer_archival_candidates()`/`finalize_customer_archival()`;
  both finalize handlers registered in `pending_approvals_router.py`'s
  `_APPROVAL_HANDLERS`; new `POST /poc/librarian-propose-customer-
  backfill` (`email_poc_router.py`, deliberately NOT wired into `run_
  housekeeping_pass()`'s recurring schedule — manually-triggered only).
  First multi-target Pending Approval in this codebase — one batched
  approval per proposed Customer, naming every matched Thread together,
  reusing the existing `pending_approval_registry`/`_APPROVAL_HANDLERS`
  mechanism completely unmodified. Real backfill run: 10 real Threads
  routed (`Aldar` × 3, `TAQA` × 7 — a brand-new real Customer folder
  created via unmodified `ensure_customer_hub_note`), 2 real noise
  folders archived to `Work/Archive/Customers/` (`Twitter`, `Google`,
  content byte-for-byte preserved), idempotency after approval confirmed
  for real (`AC-09`). A genuine live defect (a transient Compass
  connection drop crashing the whole ~120-Thread pass) found and fixed
  in scope — `propose_customer_backfill()` now isolates a single Thread's
  `CompassError` into an additive `"failed"` key instead of discarding
  every other Thread's already-good classification, mirroring `backfill_
  files`'s own established honest-degradation pattern; no change to
  `ADR-055`'s own "no retry loop" decision. 64 pending routing + 31
  pending archival-candidate real records left for operator review (real
  duplication from 3 real full-corpus verification passes this session —
  see `REVIEW-QUEUE.md`); a real archival false-positive nuance (a
  Customer already routed by an earlier pass gets wrongly re-proposed for
  archival by a later pass) also flagged there, out of this story's own
  locked scope to fix.
- docs: `SPRINT-067`/`REQ-SB-73-US-01` marked `Done` — Bidirectional Thread
  ↔ Message Linking (Retrofit + Rename-Safe) fully built and live-verified
  (all 6 locked ACs `PASS`). `BACKLOG.md` `REQ-SB-73` row updated. Sprint
  retrospective drafted, `gate: flagged` for the human to skim and
  propagate patterns/antipatterns into `Implementation/Learnings.md`;
  `ADR-054`'s own standing human-review item in `REVIEW-QUEUE.md` remains
  open (updated with a build-completion note, per the `SPRINT-060`
  precedent — a standing architect-level ADR flag does not block the
  build).
- feat: `REQ-SB-73-US-01-T04` — real, full-corpus retrofit run of `link_
  thread_messages()` via the real `POST /poc/librarian-link-thread-
  messages` endpoint against the real vault (132 Thread directories, 258
  raw message notes, 129 message-bearing Threads), plus a real, byte-for-
  byte idempotency proof (SHA-256 hash of all 390 real files, unchanged
  across two consecutive real endpoint calls). Full-corpus consistency
  re-check: 0 `thread:` mismatches across every real message. `REQ-SB-73-
  US-01` (all 4 tasks `Done`) and `SPRINT-067` marked `Done`. No code
  change required — see the task's own Implementation Log for the real
  verification evidence.
- feat: `REQ-SB-73-US-01-T02`/`T03` — `rename_threads()` extended
  (`app/business/pipelines/librarian_housekeeping.py`) with a bounded
  fan-out: on every successful `rename_thread_directory` call, in the SAME
  loop iteration, every one of that Thread's own current messages gets its
  `thread:` field rewritten to the new slug via `upsert_frontmatter_key` —
  a zero-staleness-window guarantee (`ADR-054` Decision 2). `link_thread_
  messages()` wired into `run_housekeeping_pass()`'s own Job chain, SECOND
  (immediately after `rename_threads()`). New endpoint `POST /poc/
  librarian-link-thread-messages` on `email_poc_router.py`, mirroring the
  existing `/poc/librarian-*` convention. Live-verified against the real
  vault (`REQ-SB-73-US-01-AC-04`, pass, including 5 genuine real stem
  collisions correctly caught with zero fan-out attempted) and the real
  running endpoint — see both tasks' own Implementation Logs.
- feat: `REQ-SB-73-US-01-T01` — new Librarian Job `link_thread_messages()`
  (`app/business/pipelines/librarian_housekeeping.py`), per `ADR-054`:
  regenerates every real Thread's own `## Messages` section wholesale from
  its current `messages/*.md` glob (`insert_body_section_if_missing` +
  `replace_body_section`), and writes/self-heals every one of those
  messages' own `thread:` frontmatter backlink via `upsert_frontmatter_key`
  — write-new, self-heal-stale, and true-no-op-on-rerun from one existing
  primitive, zero new `vault_writer.py` code. New `section_ownership.py`
  entry `librarian_housekeeping.link_thread_messages -> {"## Messages"}`.
  `app/business/vault_indexing.py::_build_entry` gains
  `_frontmatter_wikilink_targets()` — `outgoing_wikilinks` now additionally
  scans every frontmatter string/string-list value for `[[...]]` targets
  (generic, not `thread:`-named), so the new `thread:` backlink is visible
  to the already-shipped backlinks panel/graph view. Live-verified against
  the real vault (`REQ-SB-73-US-01-AC-01/02/03/05`, all pass) — see the
  task's own Implementation Log.
- fix: `BUGFIX-06-US-01-T01` (`BUG-027`) — Meeting/Inbox Cockpit no longer
  500s on a real subject note whose `attendees`/`recipients` frontmatter
  is a plain wikilink-string list (the shape `meeting_classification.py`'s
  real attendee-write path actually writes today, not the originally
  designed `list[dict]`). `app/data_access/vault_writer.py`'s
  `_WIKILINK_PATTERN` promoted to public `WIKILINK_PATTERN` (pure rename;
  its own 2 internal call sites, `extract_wikilink_targets` and
  `upsert_attendee_links`, updated to the new name). `app/business/
  cockpit/people.py` gains `_normalize_person_item`, wired into
  `_coerce_people_list`, which strips `[[...]]` via `WIKILINK_PATTERN` and
  resolves the stem via `vault_indexing.get_index()` — a resolved stem
  yields a real `{"name", "email"}` from that Person note's own
  frontmatter; an unresolvable stem falls back to the existing "no note
  yet" chip (`{}`), never creating a Person note (`ADR-036` point 7,
  unchanged). `resolve_people_chips` itself is byte-for-byte unchanged.
  Live-verified against both of `BUG-027`'s own confirmed real repro
  meetings ("Alignment Mubadala-2026-08-17-a4737bc4", "PSS Team Weekly
  Meeting-2026-08-18-47a72b70") — both now return `200` with real,
  cross-checked attendee name/email chips (`AC-01`); a temporarily added,
  fully reverted orphaned wikilink stem confirmed the "no note yet"
  fallback with no crash, and a temporarily added, fully reverted
  JSON-encoded-string `recipients` field plus a real Thread note with no
  `recipients` field at all confirmed both pre-existing shapes are
  unregressed (`AC-02`). `BUG-027` flipped `In Sprint → Closed` in
  `BUGS.md`/`BACKLOG.md`. `SPRINT-066`/`BUGFIX-06-US-01` marked `Done`.
- docs: architect pass (`/plan-tasks` step 1, re-opened) for
  `BUGFIX-05-US-01` — `ADR-053` created, closing `ESC-056`'s own
  content-loss gap: `migrate_flat_thread_to_directory` gains a one-time,
  content-preservation step (reads the flat note's own pre-migration
  `## Summary` via the existing `read_body_section`, writes it verbatim to
  a new `pre_migration_summary.md` sidecar before the rename);
  `synthesize_thread` gains one small, additive read/fold/archive step
  (folds the sidecar into its SAME existing Compass call as prior-history
  grounding, archives it to `pre_migration_summary.consumed.md` on
  success, leaves it untouched on failure). `architecture.md` gains
  "Migration content-preservation — the `pre_migration_summary.md`
  sidecar". `ESC-056` marked `Resolved`, naming `ADR-053` as the resolving
  artefact.
- docs: decomposer re-lock #2 (`/plan-tasks` step 2) for `BUGFIX-05-US-01`
  — `AC-01` re-locked against `ADR-053`'s concrete sidecar design; new task
  `BUGFIX-05-US-01-T05` created (one combined task spanning
  `vault_writer.py` + `email_classification.py`, since the sidecar's write
  and read/fold/archive halves are verification-coupled in the SAME
  pipeline tick); `T04` amended in place (`depends_on` gains `T05`,
  `Blocked → Ready`, `## Objective`/`## Tests` updated to also verify the
  sidecar fold-in/archive). A real, additional finding this pass:
  `T03`'s own smoke test had already permanently migrated one real flat
  Thread (`RITM0108464`) before the sidecar mechanism existed, leaving it
  sidecar-less and at the same latent content-loss risk — `T05` gains a
  bounded, one-time manual backfill step for this one Thread.
- fix: `BUGFIX-05-US-01-T05` — implements `ADR-053`'s sidecar mechanism.
  `app/data_access/vault_writer.py`'s `migrate_flat_thread_to_directory`
  now writes `pre_migration_summary.md` (plain text, no frontmatter,
  verbatim via `read_body_section`, OUTSIDE `messages/`) before the
  rename, only when the flat note's own pre-migration `## Summary` is
  non-empty; `list_all_note_paths()` gains a `_THREAD_SIDECAR_RESERVED_
  FILENAMES` exclusion for both `pre_migration_summary.md` and `pre_
  migration_summary.consumed.md`. `app/business/email_classification.py`'s
  `synthesize_thread` now reads the sidecar (if present) immediately
  before composing `full_content`, prepends it as an explicitly-labeled
  prior-history block feeding the SAME existing Compass call, and — only
  after `replace_body_section` succeeds — renames it to `pre_migration_
  summary.consumed.md` (left completely untouched on `CompassError`). No
  `section_ownership.py` change. Live-verified against a real flat Thread
  (`Masdar Data`, `conversation_id 45597B7A26F545B3882C53D78B52C628`): the
  sidecar was written byte-identical, folded into a real Compass
  synthesis whose regenerated `## Summary` genuinely reflected both the
  pre-migration content and a new message, archived to `.consumed.md`,
  and confirmed fed exactly once across a second synthesis run. Performed
  the one-time `RITM0108464` sidecar backfill after re-confirming its own
  preconditions still held live.
- fix: `BUGFIX-05-US-01-T04` (second attempt, against the now-`Done`
  `T05`) — `[BUGFIX-05-US-01-AC-01]` and `[BUGFIX-05-US-01-AC-02]`'s own
  working-mode-flip clause both verified PASS live against the real
  `process_staged_email` capability endpoint. A real, clean flat Thread
  (`Compass Alert- Failed API Calls`, `conversation_id
  041969487D51E942B77F5CD4A13A6CC2`) was migrated to the standard
  directory shape; its regenerated `## Summary` genuinely reflected both
  the original Jul 27 alert content and a new synthetic verification
  message; its sidecar was archived to `pre_migration_summary.consumed.md`;
  no duplicate Thread note exists anywhere for that `conversation_id`.
  `email-capture-pipeline`'s working mode flipped `supervised →
  autonomous` via the real `PATCH /agents/email-capture-pipeline`
  endpoint, confirmed permanent via a fresh `GET` — the final undo of
  `ESC-048`'s protective measure. This attempt self-caught and fully
  repaired two real-vault incidents before the tracked run (a diagnostic
  call that side-effect-triggered a migration outside the real endpoint;
  a stale, pre-`T05`-edit backend process reproducing the pre-`ADR-053`
  content-loss bug) — zero permanent data loss, full incident record in
  `T04`'s own Implementation Log; `REVIEW-QUEUE.md` carries a new,
  non-blocking FYI entry for human awareness. `BUGFIX-05-US-01` (`BUG-026`
  fix), all 5 tasks now `Done`, both locked ACs verified — story advances
  to `Done`; `BUG-026` flips `In Sprint → Closed`; `SPRINT-065` advances to
  `Done` (retrospective drafted, `gate: flagged` for human harvest into
  `Implementation/Learnings.md`).
- fix: `BUGFIX-05-US-01-T01` — `process_staged_email`'s underlying
  implementation (`app/business/pipelines/email_capture_pipeline.py::
  run_email_capture_pipeline`) retargeted off the old, still-buggy
  `StateGraph`/`thread_match_merge` path onto a plain, sequential
  composition of `capture_raw_thread_messages` (Stage 1) +
  `synthesize_thread` (Stage 2), closing `AC-02` (the directory-shape
  orphaning facet) by construction (`ADR-051`). `detect_recurring_
  pattern`/`consult_librarian`/`project_customer_synthesizer.resync_
  project_from_thread` explicitly re-composed as plain calls, each with
  its own try/except, so none of the old graph's three real side effects
  with no equivalent elsewhere are silently dropped.
  `raw_message_capture.capture_raw_thread_messages` gains an additive
  `conversation_ids_touched` return key (pure superset, existing keys
  unchanged). `skill_tools.process_staged_email`'s success-message
  wording updated to per-Thread granularity ("N thread(s) updated.").
  `email_capture_pipeline.py`'s `StateGraph`/`_GRAPH`/`get_job_tree()`
  and every graph node function left byte-for-byte unchanged — deprecated,
  not deleted, per `ADR-051` Decision 6 (`get_job_tree()`,
  `REQ-SB-65-US-01`'s Pipeline Job Tree, still reads the same compiled
  graph). Live-verified via direct real-vault Python calls and the real
  `process_staged_email` capability — see `T01`'s own Implementation Log.
- fix: `BUGFIX-05-US-01-T03` — `app/data_access/vault_writer.py`'s
  `resolve_thread_directory()` gains a second scan tier, tried only on a
  miss from the existing directory-shaped scan, that recognizes a legacy,
  pre-redesign FLAT `Work/Threads/<name>.md` Thread note by its own
  `conversation_id` frontmatter and lazily, idempotently migrates it (new
  `migrate_flat_thread_to_directory` primitive) to the standard `<slug>/
  <slug>.md` + empty `messages/` directory shape on first touch (`ADR-052`).
  `list_thread_notes()` and `resolve_thread_note_path()` bodies unchanged.
  Live-verified against 2 real flat Threads (one migrated as part of this
  task's own smoke test; the already-diverged Azure conversation confirmed
  correctly, silently no-op'd per the migration's own load-bearing
  ordering rule).
- test: `BUGFIX-05-US-01-T02` — live-verified `AC-02` (a real,
  directory-shaped Thread's own `messages/`/`files/` content is never
  orphaned when a new message arrives) against the real, live vault and
  the real `process_staged_email` capability endpoint — genuine PASS. The
  first attempt hit a self-detected, self-repaired incident (an
  already-running backend process predating `T01`'s fix briefly
  reproduced `BUG-026`'s own orphaning failure live) — full incident
  timeline, repair evidence, and the clean second-attempt PASS are in
  `T02`'s own Implementation Log; `REVIEW-QUEUE.md` carries an FYI
  (non-blocking) entry for human awareness.
- **BLOCKED** — `BUGFIX-05-US-01-T04` — live verification of `AC-01`
  (a real, clean flat Thread migrates and threads in place, never
  duplicating) found a genuine, real failure: the migrated Thread's own
  real, pre-migration `## Summary` content is silently overwritten and
  lost the moment the SAME composed pipeline tick's own `synthesize_thread`
  call next regenerates `## Summary` purely from the Thread's own
  now-migrated-but-empty `messages/` directory — a previously-undiscovered
  interaction gap between `ADR-051` and `ADR-052`, not a `T01`/`T03` coding
  defect. Real vault fully repaired (byte-identical restore, confirmed).
  `email-capture-pipeline`'s working mode NOT flipped — stays `supervised`.
  Full write-up: `ESCALATIONS.md` → `ESC-056`; `REVIEW-QUEUE.md` (blocking,
  needs an architect decision). `BUGFIX-05-US-01` stays `In Progress`;
  `BUG-026` stays `In Sprint`, not `Closed`; `SPRINT-065` stays
  `In Progress`, not `Done`.
- docs: `/plan-tasks` step 2 (decomposer, re-lock pass) complete for
  `BUGFIX-05-US-01` (`BUG-026` fix) — re-locked `AC-01` (the flat-shape
  duplication facet) against `ADR-052`'s own concrete design (`resolve_
  thread_directory()`'s new second scan tier + `migrate_flat_thread_to_
  directory` primitive), unblocking it after the prior pass's `ESC-055`
  finding. Two new flat-root task files:
  `Implementation/Tasks/BUGFIX-05-US-01-T03-migrate-flat-thread-on-first-touch.md`
  (the `vault_writer.py`-only primitive fix — deliberately NOT folded into
  `T01`, since `ADR-052`'s fix lives one layer below `T01`'s own composing-
  function rewire, in a shared primitive several other real callers also
  use) and
  `Implementation/Tasks/BUGFIX-05-US-01-T04-live-verification-flat-thread-migration-and-mode-flip.md`
  (live verification of `AC-01` — against a real, clean flat Thread note,
  explicitly excluding the already-diverged `ED0954959F6F4A4C88F9E2ACA3D7113A`
  Azure conversation, deferred to a future Librarian-housekeeping backlog
  item per the architect's own Decision 2 — plus the `email-capture-
  pipeline` working-mode flip `supervised → autonomous`, moved here from
  being permanently out of `T02`'s own scope, now that both `AC-01`
  (`T04`) and `AC-02` (`T02`) have a real place to land). `depends_on`:
  `T01: []`, `T02: [T01]`, `T03: []`, `T04: [T01, T02, T03]` — acyclic.
  `T01`/`T02`'s own stale "`AC-01` not locked" text corrected in place
  (substantive scope unchanged). Every locked AC (`AC-01`, `AC-02`) now
  has at least one tagged verification step; the story advances
  `Draft → Ready`; all four tasks set `status: Ready`. `REVIEW-QUEUE.md`'s
  `ADR-052`-review entry checked off (resolved directly by the operator,
  per the story's own frontmatter `gate_reason`); the separate, still-open
  entry on the already-diverged Azure duplicate's own future backlog
  disposition is untouched — not blocking this story. No new MUST-FLAG
  trigger fired this pass; full reasoning in the story's own new
  "Decomposer pass (re-lock)" `## Notes` section.
  → `Implementation/UserStories/BUGFIX-05-US-01-email-thread-processing-retires-legacy-thread-match-merge.md`

- feat: `SPRINT-063` (`REQ-SB-72-US-01`, The Librarian Section — First
  Housekeeping Pipeline) — `T06`-`T09` built/verified live this session
  (`T01`-`T05` completed in prior sessions). All 9 tasks `Done`, all 11
  locked ACs verified against real, live evidence.
  - `T06` (`## Related` ownership transfer): `email_classification.
    build_thread_related_wikilinks` promoted from private
    `_build_thread_related_wikilinks` to a public, cross-module function,
    extended with a new `mentioned_companies` parameter (one `[[wikilink]]`
    per real company mention, honest-omission preserved for all link
    kinds). `synthesize_thread` no longer writes `## Related` —
    `section_ownership.py`'s allow-list narrowed to `{"## Summary"}` for
    that caller in the SAME change that registers `librarian_housekeeping.
    populate_thread_related_links` as the new sole `## Related` owner.
  - `T07` (company folder backfill + ambiguous-finding approval): new
    `librarian_housekeeping.backfill_company_folders()` auto-creates a
    Customer OKF folder (via the existing, unmodified `ensure_customer_
    hub_note`) for every confident/`new_unambiguous` company mention; an
    ambiguous mention creates a real Pending Approval
    (`action_id="propose_librarian_company_link"`, new
    `_create_librarian_company_link_proposal`/`finalize_librarian_
    company_link`, registered on `pending_approvals_router.py`'s
    `_APPROVAL_HANDLERS`) instead of acting autonomously.
  - `T08` (Agent/Section identity + orchestration + endpoints): new
    `librarian_housekeeping.ensure_librarian_agent_and_section()` —
    idempotent bootstrap creating the "Librarian" Section + `librarian-
    housekeeping` Agent (type `worker`), called once from `app/main.py`'s
    `lifespan`. New orchestrating `run_housekeeping_pass()` (Rename Job
    first, then Files/`## Related`/Company-folder backfill). 5 new `POST
    /poc/librarian-*` endpoints on the existing `email_poc_router.py`
    (`librarian-rename-threads`, `librarian-backfill-files`, `librarian-
    populate-related`, `librarian-backfill-company-folders`, `librarian-
    run-housekeeping-pass`).
  - `T09` (scheduled wiring): `run_housekeeping_pass` promoted to a real,
    granted, mutating `skill_tools.SKILLS`/`skill_registry._SKILL_
    HANDLERS` entry (a new `_MIGRATION_GRANT_SEED` entry for
    `librarian-housekeeping`, mirroring `pull_email`/`process_staged_
    email`'s own precedent). `app/main.py`'s `lifespan` now seeds a real,
    persisted `agent_schedule_registry` entry (6-hour default interval)
    once, after the agent/skill grant exist.
  - Real vault-hygiene progress this session (via the real endpoints,
    never a raw script): `## Related` population went from 20/126 to
    87/126 real Threads; 10 real ambiguous company-mention Pending
    Approvals created (1 approved live, 1 declined live, 5 left for real
    operator review); several new real Customer folders created for
    confident mentions. The remainder completes autonomously via the new
    6-hour schedule once the app runs normally.
  - Disclosed finding: a reproducible coding-session infrastructure
    limitation (long-running bulk Jobs colliding with this session's own
    background-process reclaim policy) left `T09`'s own `AC-11`
    verification with a disclosed, itemized partial-evidence gap (2 of 5
    endpoints have a captured live `200`; 3 have strong real execution
    evidence but no captured `200` within this session) — see `ESC-054`,
    `REVIEW-QUEUE.md`, and the sprint's own retrospective.

- fix: `SPRINT-064` (`BUGFIX-04-US-01`, Cockpit chat correctly addresses
  agents, sends on Enter, updates live, and renders rich text —
  `BUG-022`/`023`/`024`/`025`) — `T01`-`T04` built and verified live.
  - `T01`: `app/business/cockpit/threads.py::send_user_message` gains an
    optional `addressed_agent_ids: list[str] | None = None` parameter —
    its dispatch loop iterates `addressed_agent_ids or
    thread["brought_in_agent_ids"]`, scoping replies to only the
    addressed agent(s) when present, falling back to today's broadcast-
    to-every-brought-in-agent behavior byte-for-byte when absent/empty.
    `app/api/cockpit_router.py`'s `POST .../message` endpoint reads the
    matching optional `addressed_agent_ids` request-body field and passes
    it straight through, no new validation. Verified live against a real
    scratch Cockpit thread: an addressed send produced exactly one agent
    reply; an unaddressed follow-up produced replies from every brought-in
    agent (regression-safe).
  - `T02`: `src/frontend/src/features/cockpit/Cockpit.tsx`'s
    `chat-input-row` becomes a real `<form onSubmit={handleSendMessage}>`
    (Enter now sends, mirroring `AgentDetailPanel.tsx`'s own precedent);
    a new `sending` state disables the input/Send button and shows a
    typing-dot pending indicator while a send is in flight;
    `handleSendMessage` applies `sendCockpitMessage`'s own returned
    `CockpitThread` directly via `setData(...)` instead of firing a
    redundant `reload()` GET; `mentionedAgents.map((agent) => agent.id)`
    is now passed through as `sendCockpitMessage`'s new optional
    `addressedAgentIds` argument
    (`src/frontend/src/features/cockpit/cockpitApiClient.ts`). Verified
    live in a real Meeting Cockpit: Enter sent a message and cleared the
    input; the pending indicator and disabled state showed correctly
    in-flight; the sent message and reply appeared without a manual page
    refresh; an `@mention`-addressed send through the real UI reproduced
    `BUG-022`'s exact original repro, fixed.
  - `T03`: new shared `src/frontend/src/components/ChatMessageText.tsx`
    component wrapping `react-markdown` v9.x (added to
    `src/frontend/package.json`), zero remark/rehype plugins, default-safe
    by omission (`ADR-050`) — first real delivery of `REQ-SB-32`.
  - `T04`: `Cockpit.tsx` and
    `src/frontend/src/features/agents-map/AgentDetailPanel.tsx` both
    replace their literal `{message.text}` chat-thread render with
    `<ChatMessageText text={message.text} />`, symmetric for user- and
    agent-authored messages. Verified live via real DOM structural checks
    (`<strong>`/`<li>` elements, no literal `**`/`- ` syntax visible)
    across Meeting Cockpit, Inbox Cockpit (same shared component), and the
    Agents Map's own embedded agent chat panel.

- feat: `SPRINT-063` (`REQ-SB-72-US-01`, The Librarian Section — First
  Housekeeping Pipeline) — `T01`-`T05` built and verified live against
  the real vault.
  - `T01`: `app/data_access/vault_writer.py` gains `resolve_thread_
    directory(conversation_id)` (new frontmatter-scan primitive,
    composing `list_thread_notes()`), `resolve_thread_note_path`
    retargeted (public signature unchanged) to a thin wrapper over it,
    `raw_message_note_path` retargeted to resolve-first/deterministic-
    fallback, and a new `rename_thread_directory(old, new)` atomic
    whole-directory-move primitive (refuse-to-overwrite, no-op on
    `old==new`) — `ADR-049` Decision 1/2.
  - `T03`: new `app/business/pipelines/librarian_housekeeping.py` module,
    `rename_threads()` Job — renames every real Thread directory still
    named after its raw `conversation_id` slug to `<date> <subject-
    without-Re->`. Live-run against the full real 126-Thread corpus:
    **121 renamed, 5 genuine stem collisions caught and reported
    per-Thread (run did not abort)**, idempotent on rerun (0
    re-renamed, 121 skipped).
  - `T02`: migrated the 3 real callers `ADR-049` found directly composing
    `thread_directory_paths` — `raw_message_capture.py`'s Stage 1
    existence check, `email_classification.synthesize_thread`'s
    `messages/` read (reordered after create-vs-update resolution), and
    `meeting_classification._synthesize_history_entry`'s linked-Thread
    Summary read — all now resolve via `resolve_thread_note_path`, so an
    already-renamed Thread is found correctly, never duplicated.
  - `T04`: `insert_body_section_if_missing` (new, `vault_writer.py`),
    `backfill_files()` Job (`librarian_housekeeping.py`) — backfills
    `files/<slug>/` OKF companions for every un-companioned real
    attachment (reuses `email_classification.write_file_companion`
    unchanged) and writes a structured `## Files` section per Thread. New
    `section_ownership.py` entry (`librarian_housekeeping.backfill_
    files` → `## Files`). Live-run against the full real corpus: **58
    new companions created, 2 honest failures (non-extractable scanned
    PDFs), 26 Threads' `## Files` sections written**; idempotent on
    rerun (0 new, byte-identical companions).
  - `T05`: `compass_client.detect_mentioned_companies` (new prompt/parse
    contract) + `librarian_housekeeping.detect_mentioned_companies_for_
    thread` (Python re-check against `list_known_customers`/`list_known_
    partners`, classifying each mention `known`/`new_unambiguous`/
    `ambiguous`) — the shared building block `T06`/`T07` consume.
  - Two real, out-of-scope defects found live and escalated (disclosed,
    not silently fixed): `ESC-051` (`write_attachments`'s own `_slugify`
    80-char truncation collapses near-identical long Outlook
    `message_id`s onto the same attachment directory) and `ESC-052`
    (`write_file_companion`'s own `file_slug` breaks when an attachment's
    own filename already ends in `.md`, crashing the live scheduled index
    rebuild — mitigated in-scope with a defensive, zero-behavior-change
    `path.is_file()` guard on `list_all_note_paths()`; root cause left
    disclosed). Full evidence in each task's own `## Implementation Log`
    under `Implementation/Tasks/REQ-SB-72-US-01-T0{1,2,3,4,5}-*.md`.

- feat: `SPRINT-062` (Meeting Capture Redesign — one-time/recurring split,
  frontmatter-only logistics, People auto-extraction from attendees
  nested under Customer) built and verified `Done` — all 3 tasks, one
  story (`REQ-SB-71-US-03`), the last story in the `ADR-048` 4-story
  redesign batch.
  - `app/data_access/outlook_com.py`: `list_calendar_events` gains
    `is_recurring`/`series_id` (`GlobalAppointmentID`, used ONLY as a
    series key) and TRANSIENT `teams_link`/`dial_in` regex extraction
    from `item.Body` (`_extract_teams_link`/`_extract_dial_in`) — the raw
    invite body is read into a local variable only, never persisted
    anywhere.
  - `app/data_access/vault_writer.py`: new `meeting_series_directory_
    paths(series_id) -> dict` (`Work/Meetings/<slug>/<slug>.md`, mirrors
    `thread_directory_paths`). `create_meeting_note_baseline`/`ensure_
    meeting_note_baseline_frontmatter` rewritten to accept an
    already-resolved `note_path` and write the new logistics-only
    frontmatter shape (`type`/`customer`/`tags`/`thread`/`teams_link`/
    `dial_in`/`organizer`/`recurrence`/`attendees`/`calendar_event_id`-or-
    `calendar_series_id`) + the new shared `## Summary`/`## History`/
    `## Personal Notes`/`## Actions` body skeleton — `subject`/`start`/
    `end`/`location` no longer persisted. People: new `person_note_dedup_
    key(name, email)` (email when present, else a name-slug — closes the
    real, previously-shipped `if not email: continue` silent-skip gap);
    `person_note_path`/`person_note_exists` retargeted from `(email)` to
    `(dedup_key, customer)` — nests at `Work/Customers/<slug>/People/
    <slug>.md` when `customer` is a real, matched Customer name, else the
    existing flat `Work/People/<slug>.md`; new `find_person_note_path
    (dedup_key) -> Path | None`, a vault-wide scan mirroring `resolve_
    thread_note_path`'s own precedent. `create_person_note_baseline`/
    `ensure_person_note_baseline_frontmatter` retargeted to accept an
    already-resolved `note_path` (`email` may be `None`).
  - `app/data_access/section_ownership.py`: new `"meeting_classification.
    classify_recent_meetings": frozenset({"## Summary"})` allow-list
    entry.
  - `app/business/meeting_classification.py`: `classify_recent_meetings`
    rewritten in place — branches one-time vs. recurring; regenerates
    `## Summary` via a new Compass call (`_synthesize_meeting_summary`,
    mirroring `_synthesize_thread_summary`'s own verbatim reuse of
    `compass_client.summarize_content`) through the allow-list-checked
    `replace_body_section`; appends a new, dated `## History` entry per
    real occurrence (`_synthesize_history_entry` + `_append_history_
    entry_if_new_occurrence`, content-based idempotency, synthesized from
    calendar logistics plus, when linked, the Thread's own current `##
    Summary`) via the unguarded `append_body_section_line`; the attendee
    loop's `if not email: continue` skip REMOVED — every attendee now
    reaches the retargeted `people_extraction.ensure_person_note(name,
    email, customer=...)`.
  - `app/business/people_extraction.py`: `ensure_person_note(name, email,
    customer=None)` retargeted — `find_person_note_path` checked FIRST
    (tops up an already-existing note in place, never moves/duplicates
    it); creates new, nested under the matched Customer (or the meeting's
    own derived Customer, for the no-email case only) or the flat
    fallback, only when genuinely absent. `find_existing_person_note`
    retargeted the same way. `email_classification.py`'s own 3 existing
    call sites need zero change (backward-compatible `customer=None`
    default).
  - All 7 locked ACs (`AC-01`..`AC-07`) verified live against the real
    operator Outlook calendar/vault: a real one-time meeting produced a
    clean, boilerplate-free note; a real recurring series ("Weekly
    Forecast l Strategic Clients") accumulated 4 real dated `## History`
    entries on the SAME note across multiple real calls, one genuinely
    drawing on a real linked Thread's own content; a real manually-added
    Personal Notes/Actions entry survived byte-for-byte across a further
    real History append; the People scenarios verified via a scoped,
    disclosed, real-endpoint monkeypatch of only the external Outlook-COM
    boundary (the live calendar has zero real no-email-attendee instances
    and the vault currently carries zero notes with a real `customer`
    frontmatter value — a same-day migration reset). All fixture/
    engineered artifacts fully removed and confirmed clean afterward.
  - Disclosed, non-blocking finding: `ESC-049` — `app/business/
    my_day.py::list_calendar_items` reads Meeting `subject`/`start`
    frontmatter this redesign deliberately drops, silently excluding
    every new-shape Meeting note from My Day's own 7-day window;
    `my_day.py` is not in this story's own `## Files to Modify`, left as
    a disclosed follow-up (see `ESCALATIONS.md`).
- docs: `REQ-SB-72` (The Librarian Section — First Housekeeping Pipeline)
  added to `Documentation/PRD.md`, following a dedicated design
  conversation with the operator on 2026-08-18, opened once `REQ-SB-71`'s
  own capture pipelines were built and real housekeeping gaps (`ESC-046`,
  `ESC-048`) surfaced as live evidence. Four tasks: human-readable Thread
  renaming (requires a disclosed, deliberate partial reversal of `ADR-048`
  Decision 7's deterministic-path lookup, back to frontmatter matching, now
  justified by real ~10-email/hour steady-state volume data), Files/OKF
  companion backfill + a new `## Files` section, `## Related` ownership
  transfer from Stage 2 to the Librarian, and Customer-folder backfill via
  the existing Filing Expert. Meaningful/topic tags and cross-Thread
  recurring-artifact linking explicitly deferred. Not yet specced —
  `BACKLOG.md` row added at `Draft`.
- feat: `SPRINT-061` (Email Capture Redesign — Thread raw/distilled split,
  two-stage operator-triggered pipeline, Files/OKF companions) built and
  verified `Done` — all 7 tasks, one story (`REQ-SB-71-US-02`).
  - `app/data_access/vault_writer.py`: `thread_directory_paths
    (conversation_id) -> dict` (new) — `Work/Threads/<slug>/{<slug>.md,
    messages/}`, permanently deterministic from `conversation_id` alone,
    superseding `ADR-046`'s own human-readable/renamable-filename scheme.
    `create_thread_note_baseline` rewritten (drops `date`; new 4-section
    body, `## Transcript` retired). `raw_message_note_path`/`_exists`/
    `create_raw_message_note` (new) — write-once, immutable raw message
    notes. `list_all_note_paths()` rewritten to a single bounded recursive
    scan (`rglob("*.md")`, `_OKF_RESERVED_FILENAMES` excluded), replacing
    the old 1-level-flat + 2-hardcoded-glob shape. `list_thread_notes()`
    retargeted to the new 2-level shape; `resolve_thread_note_path()`'s
    internals retargeted to a deterministic existence check (public
    signature/contract unchanged). `write_file_companion`/`staged_
    attachment_files` (new) — the generic Files/OKF companion primitive
    and its durable-attachment-lookup sibling.
  - `app/business/pipelines/raw_message_capture.py` (new): Stage 1 —
    `capture_raw_thread_messages(limit=10) -> dict`, reuses `email_pull.
    pull_and_stage_emails`/`email_staging` verbatim, zero `compass_client`
    import. Exposed as `POST /poc/capture-raw-thread-messages`.
  - `app/business/email_classification.py`: Stage 2 — `synthesize_thread
    (conversation_id) -> dict` (new), full-reconstruction Compass-backed
    judgment (classifies once against the first raw message via
    `classify_captured_email_with_fallback`, regenerates `## Summary`/`##
    Related` via the allow-list-checked `replace_body_section`). `write_
    file_companion(attachment_path, message_id, thread_directory)` (new)
    — the Files/OKF composing Job, wired into `synthesize_thread`'s own
    end. Exposed as `POST /poc/synthesize-thread?conversation_id=`.
  - `app/data_access/section_ownership.py`: two new `_CALLER_ALLOW_LISTS`
    entries — `email_classification.synthesize_thread` (`## Summary`, `##
    Related`), `email_classification.write_file_companion` (`## Summary`).
  - All 7 locked ACs (`REQ-SB-71-US-02-AC-01..07`) verified with real,
    live evidence against the real operator Outlook mailbox/vault — 252
    real raw message notes across 127 real Thread directories from one
    real Stage 1 call; real full-reconstruction Stage 2 synthesis across
    two real multi-message Threads; a real, live proof Stage 1/Stage 2
    share no lock; a real manually-added `## Personal Notes`/`## Actions`
    entry confirmed byte-for-byte unchanged (SHA-256) across a
    re-synthesis; real PDF/XLSX attachments producing real `files/<slug>/`
    OKF companions with genuine Compass summaries. Two real bugs found and
    fixed live, in-scope (a Compass classification failure crashing Stage
    2 — fixed via the existing `BUG-015` fallback wrapper; a `_slugify`
    80-char truncation dropping a real filename — fixed to a
    `hash8(message_id)`-based disambiguator). Full evidence in each task's
    own `## Implementation Log`.
  - Story → `Done`; sprint → `Done`, retrospective drafted. `gate` left
    `flagged` — the standing `ADR-048` human-review flag is unchanged, plus
    one new, disclosed out-of-scope finding (`ESC-048`): the new Thread
    shape's own `resolve_thread_note_path` retargeting breaks the still-
    live, scheduled `thread_match_merge` pipeline's create-vs-update check
    for pre-redesign Threads — `email-capture-pipeline`'s working mode was
    deliberately left `supervised` (not reverted to `autonomous`) as the
    interim protective measure. See `REVIEW-QUEUE.md`.

- feat: `SPRINT-060` (Vault Base Provisioning + Section-Ownership
  Enforcement) built and verified `Done` — all 3 tasks, both stories
  (`REQ-SB-70-US-01`, `REQ-SB-71-US-01`).
  - `app/business/vault_provisioning.py` (new): `provision_vault_base()`,
    idempotent `mkdir(parents=True, exist_ok=True)` for exactly
    `Work/Customers/`, `Work/Threads/`, `Work/Meetings/`, `Work/
    Resources/`, `Work/Archive/{Opportunities,Customers,Resources}/`.
    Exposed as `POST /poc/provision-vault-base` in `app/api/
    email_poc_router.py`.
  - `app/data_access/section_ownership.py` (new): `_HUMAN_OWNED_HEADERS`
    (`## Personal Notes`, `## Actions` — checked first, unconditionally),
    `_CALLER_ALLOW_LISTS` (per-function, deny-by-default),
    `is_header_allowed`, `SectionWriteNotAllowed`.
  - `app/data_access/vault_writer.py`: `replace_body_section` gains a
    REQUIRED keyword-only `caller: str` parameter (a deliberate breaking-
    signature change), checked against `section_ownership.
    is_header_allowed` before any file I/O.
  - Retrofitted all 6 physical, already-shipped `replace_body_section`
    call sites (4 real callers) with their own `caller=` id:
    `app/business/email_classification.py::thread_match_merge` (x2),
    `app/business/thread_summary_backfill.py::backfill_thread_summaries`,
    `app/business/project_customer_synthesizer.py`'s
    `synthesize_project`/`synthesize_customer`/
    `finalize_background_amendment_proposal` (x1 each) — zero change to
    any of their own internal write logic.
  - All 8 locked ACs (`REQ-SB-70-US-01-AC-01..04`,
    `REQ-SB-71-US-01-AC-01..04`) verified with real, live evidence against
    the real operator vault — real HTTP endpoint calls, a real on-demand
    email capture run, a real backfill run, and a real Pending-Approval
    approval (never a raw internal-function script bypass), per this
    project's own standing "call the real APIs" constraint. Full evidence
    in each task's own `## Implementation Log`.
  - Both stories → `Done`; sprint → `Done`, retrospective drafted. `gate`
    left `flagged` on the sprint and both stories — the standing `ADR-048`
    human-review flag is unchanged (not this role's to clear); two new,
    disclosed scope-internal judgment calls also flagged for human
    spot-check (see `REVIEW-QUEUE.md`).

- feat: `/plan-tasks` step 2 (decomposer) complete for the `REQ-SB-70`/
  `REQ-SB-71` batch — `REQ-SB-70-US-01`, `REQ-SB-71-US-01/-02/-03` (one
  coherent redesign built by the architect as `ADR-048`). Locked 22 ACs
  total (4/4/7/7) and wrote 13 flat-root task files
  (`Implementation/Tasks/REQ-SB-70-US-01-T01`,
  `REQ-SB-71-US-01-T01/T02`, `REQ-SB-71-US-02-T01`-`T07`,
  `REQ-SB-71-US-03-T01`-`T03`), with real cross-story `depends_on` edges
  (`REQ-SB-71-US-02`'s Stage 2/Files tasks depend on `REQ-SB-71-US-01-T01`'s
  section-ownership guard; `REQ-SB-71-US-03`'s tasks depend on both
  `REQ-SB-71-US-01-T01` and `REQ-SB-71-US-02-T02`/`-T05`). `REQ-SB-71-US-01-T02`
  is the explicit, dedicated retrofit of all 6 physical `replace_body_
  section` call sites (4 real callers) with the new required `caller`
  kwarg, so the breaking-signature change cannot be silently missed.
  `REQ-SB-71-US-02-T02` generalizes `list_all_note_paths()`/
  `list_thread_notes()`/`resolve_thread_note_path()` as its own explicit
  task (applying this project's own `SPRINT-048` Learnings entry), keeping
  `REQ-SB-71-US-03`'s existing Meeting↔Thread linking working with zero
  code change. `REQ-SB-71-US-03`'s own analyst-drafted `T03` (a new
  meeting-capture endpoint) is dropped — the architect's own resolved
  mechanism reuses the existing `/poc/classify-meetings` endpoint
  unchanged. All four stories advanced `Draft → Ready`; `gate` left
  `flagged` on all four (the architect's own `ADR-048` trigger-3 flag, not
  cleared by this pass, per `Implementation/Pipeline.md`). No new
  MUST-FLAG trigger fired; no new `REVIEW-QUEUE.md`/`ESCALATIONS.md`
  entry needed — the architect's own existing batched `ADR-048` review
  entry already covers all four stories. Two real, disclosed follow-ups
  named but explicitly NOT folded into any task: `inbox-cockpit.html`'s
  hardcoded `Work/Emails/attachments` root, and `meeting-cockpit.html`'s
  own regression risk against the new recurring-series/`## History`
  shape. Eligible for `/plan-sprints`.
- docs: `REQ-SB-70` (Vault Base Provisioning API — Fresh PARA/OKF Skeleton)
  and `REQ-SB-71` (Redesigned Email & Meeting Capture — Raw/Distilled Split,
  Section-Ownership Enforcement, People Auto-Extraction, File Companion
  Notes) added to `Documentation/PRD.md`, following a dedicated
  vault-structure design conversation with the operator on 2026-08-18,
  triggered by pausing the `REQ-SB-59` migration mid-run over a reliability
  concern. Grounded in *Building a Second Brain*'s PARA/CODE framework.
  `REQ-SB-71` supersedes `REQ-SB-55`/`REQ-SB-56`/`REQ-SB-69`'s Thread/
  Meeting shape going forward (those stories stay `Done`, untouched, per
  this project's append-only-spec rule). Not yet specced — `BACKLOG.md`
  rows added at `Draft`.
- feat: `REQ-SB-58-US-01-T02` — new `_glimpse_first_context` node in
  `app/business/agent_orchestration/graph.py`, wired `retrieve_memory ->
  glimpse_first_context -> call_model`, gated to `agent_id == "vault-qa"`
  only (the first literal agent-identity gate in this graph). Reads the
  turn's real question from the last `HumanMessage`, calls `glimpse_
  first_qa.resolve_glimpse_first_context`, and on a real match inserts
  one `SystemMessage` naming the resolved Customer/Project's Glimpse and
  Background as the preferred answer source, falling back to `vault-qa`'s
  existing tools on request or no match. No new `AgentConversationState`
  field, no new MCP tool. `app/business/agent_orchestration/state.py`'s
  `default_identity_and_grounding_text` gains one additive clause naming
  Glimpse/Background as a legitimate grounded source — every other
  sentence unchanged; `REQ-SB-33`'s `record_knowledge_gap` mechanism
  untouched. This is the LAST task in `REQ-SB-58-US-01` — story
  `status: Done`, sprint `SPRINT-058` `status: Done`, unblocking
  `REQ-SB-59` (Full Vault Migration) to be specced. All 6 locked ACs
  (`AC-01`-`AC-06`) verified live against the real configured vault, real
  Compass Provider, and disposable Customer/Project/Thread fixtures.
  Two real, disclosed, out-of-scope findings surfaced during live
  verification, neither blocking this task: `ESC-047` (`retrieve_notes_
  in_agent_scope`'s own MCP tool requires the calling model to self-report
  its own literal internal `agent_id`, which it is never told anywhere in
  its own context, so it reliably guesses wrong) and a reconfirmation of
  `T01`'s own `ESC-046` (real Customer filename-stem collision) informing
  this task's disposable-fixture test-data choice.

- feat: `REQ-SB-58-US-01-T01` — new `app/business/glimpse_first_qa.py`,
  first task of `REQ-SB-58-US-01` (Customer/Project-Aware Expert,
  `SPRINT-058`). One public function, `resolve_glimpse_first_context(
  question: str) -> dict | None`: resolves `question` to a Customer/
  Project via `vault_search.search()`'s own rank-1 result only (no new
  matching logic), reads BOTH `## Glimpse` and `## Background` from the
  matched entity's OKF concept file via `vault_writer.read_body_section`
  (deliberately not a durable-vs-current classifier — `ADR-042` already
  structurally separates the two), and returns `{"entity_type": "customer"
  | "project", "entity_name": str, "glimpse": str, "background": str}` or
  `None`. Read-only — never calls a write primitive; not bound as an MCP
  tool. Verified live via 6 non-AC module-level smoke checks against the
  real configured vault (disposable Customer/Project fixtures, cleaned up
  afterward) — this task carries none of the story's own locked ACs
  itself (all 6 are carried by `T02`'s live graph-wiring verification,
  next). Found and disclosed a real, out-of-scope vault-state finding
  while verifying (`ESCALATIONS.md` `ESC-046`): 14 of 17 real Customers
  already migrated to the `ADR-042` OKF directory shape still carry a
  stale, un-retired legacy flat hub note that shadows the real OKF
  concept file in `vault_indexing`'s stem-keyed index — directly informs
  `T02`'s own real-Customer test-data choice.

- feat: `REQ-SB-57-US-01-T04` — Background-amendment durable-fact detection
  + Pending Approval proposal/finalize, the LAST task in `REQ-SB-57-US-01`'s
  own dependency chain — story `status: Done`, sprint `SPRINT-057` `status:
  Done`. `app/data_access/compass_client.py` gains `detect_customer_
  durable_fact(evidence_text, customer, existing_background,
  prompt_override=None)` — a narrower sibling of `guess_project_for_thread`,
  grounded in BOTH the new evidence and the Customer's own current `##
  Background` prose, so an already-recorded fact honestly yields
  `has_durable_fact: false` (the real dedup mechanism, no separate
  idempotency check built). `app/business/project_customer_synthesizer.py`:
  `synthesize_customer` now runs this detection only when `evidence_text`
  is non-empty, catching any exception so a Compass failure never aborts
  the Glimpse/History work already completed; on a genuine new fact, calls
  new `_propose_background_amendment(customer, fact, source_description)`
  (mirrors `vault_filing_expert._create_cross_cutting_proposal`'s exact
  "propose in the owning module" shape, `trigger="direct"`, `action_id
  "propose_background_amendment"`, `agent_id "project-customer-
  synthesizer"`) — `## Background` is NEVER rewritten by the detection
  call itself. New `finalize_background_amendment_proposal(payload)` —
  called only on operator approval, mechanically appends the approved
  fact as one bullet to the Customer's own existing `## Background` prose
  (no second Compass call). `app/api/pending_approvals_router.py`'s
  `_APPROVAL_HANDLERS` gains one new entry (`"propose_background_
  amendment"`), mirroring `"propose_cross_cutting_update"` exactly.
  `REQ-SB-57-US-01-AC-03` and both non-AC regression checks (no duplicate
  proposal on a repeat observation of an already-recorded fact; no Compass
  call/no proposal on empty `evidence_text`) all verified live against the
  real configured vault, via a disposable `ZZZ-T04-Verify-Co` Customer
  fixture, fully cleaned up and independently reconfirmed clean afterward
  — see the task's own `## Implementation Log` for the full verification
  record.
- feat: `REQ-SB-57-US-01-T03` — Meeting-link-in trigger wiring, the THIRD
  and last real evidence-change trigger point for the Project Synthesizer.
  `app/business/meeting_classification.py::classify_recent_meetings`
  gains a new private helper `_trigger_project_resynthesis(conversation_id)`
  (resolves the linked Thread's own current path via `vault_writer.
  resolve_thread_note_path` and calls the SAME shared `project_customer_
  synthesizer.resync_project_from_thread` helper `T01` built — never
  assembles or writes `## Glimpse`/`log.md` content itself, wrapped in a
  broad, honest non-crashing `try/except` so one Synthesizer failure
  never aborts the rest of a `classify_recent_meetings` run), called
  immediately after `thread_linked` is finalized (covers both the
  primary `conversation_id`-match path and the fallback-heuristic path) —
  a Meeting that fails to link to any Thread triggers no Synthesizer call
  at all. `classify_recent_meetings`'s own existing return shape is
  unchanged. Verified live against the real configured vault (`Core42`,
  a disposable Project + two disposable Threads + two disposable Meeting
  notes, all fully cleaned up afterward, plus a real self-heal
  `synthesize_customer("Core42")` call to correct the real Customer's
  `## Glimpse` after disposable-Project cleanup) — `AC-06` and the
  no-link non-AC regression check both pass; see the task's own
  `## Implementation Log` for the full verification record.
- feat: `REQ-SB-57-US-01-T02` — Customer Synthesizer core + Route-to-Project-
  approval trigger wiring. `app/business/project_customer_synthesizer.py`
  gains `synthesize_customer(customer, concluded_project=None,
  evidence_text="")` — the sole owner of a Customer's own `## Glimpse`/
  `log.md` (`REQ-SB-54` point 7): fully regenerates `## Glimpse` as a
  mechanical rollup of every Project under `customer` whose `status` ∈
  `{active, on_hold}` (`- **{title}** — {status}`, one line per Project,
  always rebuilt fresh via `replace_body_section`, never patched), and
  appends one dated `log.md` line naming the concluded Project only when
  `concluded_project` is passed non-`None` — cascaded from `synthesize_
  project`'s own end, never independently re-deriving a conclusion from
  its own `status` comparison (Ownership rule). `synthesize_project` now
  ends by calling `synthesize_customer(customer, concluded_project=project
  if concluded else None, evidence_text=evidence_text)`. `app/business/
  email_classification.py::finalize_thread_project_routing` (the
  Route-to-Project approval's own deferred write) now calls `synthesize_
  project(customer, project)` immediately after setting the Thread's own
  `project` frontmatter — the real, first moment a Thread's evidence
  attaches to a Project, so the Customer's rollup Glimpse now includes a
  brand-new Project on first attachment, not only on its next Thread
  update. Verified live against the real configured vault (`Core42`,
  disposable Project/Thread fixtures, fully cleaned up afterward) — `AC-02`/
  `AC-05` both pass, plus the two non-AC regression checks (`finalize_
  thread_project_routing` end-to-end, `T01`'s own `AC-01`/`AC-04`); see the
  task's own `## Implementation Log` for the full verification record.
- feat: `REQ-SB-57-US-01-T01` — Project Synthesizer core + Thread-pipeline
  trigger wiring. New `app/business/project_customer_synthesizer.py` module
  (`resync_project_from_thread`, `synthesize_project`) is now the sole owner
  of a Project's own `## Glimpse`/`log.md` (`REQ-SB-54` point 7's ownership
  rule, actually enforced starting here): every real Thread update
  (`thread_match_merge`, via the new `trigger_project_synthesis` graph node,
  always-fired alongside `consult_librarian`) fully regenerates the linked
  Project's `## Glimpse` as a rollup of its currently-linked Threads, and
  appends a dated `log.md` line only when the Project's `status` frontmatter
  transitions into `won`/`lost`/`renewed` (never on `active`/`on_hold`,
  never re-appended on repeat observation — the architect-proposed,
  operator-confirmed History-line bar, `architecture.md` → "Project &
  Customer Synthesizer"). Adds `vault_writer.list_threads_for_project` and
  a `last_synthesized_status` baseline frontmatter key on new Projects, and
  a new `"project-customer-synthesizer"` Agent-tier identity (`agent_
  registry.py`, evidence-triggered only, no schedule/manual-run action).
  Verified live against the real configured vault (`Core42`, disposable
  Project/Thread fixtures, fully cleaned up afterward) — `AC-01`/`AC-04`
  both pass; see the task's own `## Implementation Log` for the full
  verification record.
- feat: On-request-directed follow-up (2026-08-17/18 night) — when Compass
  classification fails for a staged email (`BUG-015`'s pattern), the
  pipeline no longer retries silently forever. `classify_captured_email_
  with_fallback` catches the `CompassError`, falls back to an honest
  "Unsorted" classification so the email's real content still lands in a
  real, visible Thread note this pass, and raises a real Pending Approval
  (`acknowledge_classification_failure`) so the failure is visible and
  actionable — the real fix is editing the filed Thread's own
  `customer`/`tags` frontmatter directly in Obsidian (a tag edit, this
  module's own established convention), then approving to clear the alert.
- fix: `BUG-021` — `thread_match_merge`'s update path read
  `frontmatter.get("thread_name")` for its end-of-call rename check, which
  is `None` for any Thread created before `ADR-046`/`T06` shipped (no
  `thread_name` key existed yet) — produced a real, literal
  `"None-2026-08-17-<hash>.md"` filename, found live processing a real
  update to the pre-existing "Weekly Forecast l Strategic Clients" Thread.
  Now backfills the missing key from the current message's own subject
  (top-up-only-if-missing, mirroring `T05`'s own baseline-key convention)
  instead of letting `None` propagate. The one already-broken file was
  corrected directly via the real `vault_writer` rename functions.
- fix: `BUG-020` — `skill_tools.process_staged_email` counted `len(results)`
  as "filed" without filtering out per-item `{"error": ...}` entries,
  silently reporting real Compass classification failures as successes.
  Found live re-verifying `SPRINT-056` post-restart: 4 real staged emails
  (3 of them `BUG-015`'s own known failures) were reported "4 filed" across
  5 real runs while the vault stayed completely unchanged. Fixed by
  splitting `results` into `filed`/`failed` before building the message,
  mirroring `email_classification.run_capture_and_record_completion`'s own
  already-fixed pattern. Verified live: honestly reports "0 filed, 4 failed
  (will retry next run)" against the same 4 real staged emails.
- feat: `REQ-SB-69-US-01-T04` (`SPRINT-056`, "Decoupled Email Pull +
  Human-Readable, Graph-Connected Thread Notes", `ADR-046` Decision 4) —
  `pull_email`/`process_staged_email` become two independently-dispatched
  capabilities of the existing `email-capture-pipeline` Agent-tier
  identity, deliberately sharing NO lock. `src/backend/app/business/
  skill_tools.py` gains both `SKILLS` entries (`mutates: True`) and
  `@mcp_server.tool()` handlers — `pull_email` calls `email_pull.
  pull_and_stage_emails()`; `process_staged_email` calls `email_capture_
  pipeline.run_email_capture_pipeline()` (a deferred import — see the
  circular-import finding below). `src/backend/app/business/skill_
  registry.py` gains matching `_SKILL_HANDLERS`/`_MIGRATION_GRANT_SEED`
  entries (both granted to `email-capture-pipeline` alone).
  `src/backend/app/business/agent_schedule_registry.py` gains a SECOND,
  dedicated `asyncio.Lock` (`_processing_lock`) and a sibling dispatch
  function, `dispatch_with_dedicated_processing_lock`, mirroring `dispatch_
  with_shared_lock`'s own exact shape (skip-not-queue on contention,
  `asyncio.to_thread`, run-state marking, outcome recording) but never
  touching the shared Outlook-COM lock; `_RUN_STATE_TRACKED_CAPABILITY_ID`
  (a single string) widens to `_RUN_STATE_TRACKED_CAPABILITY_IDS` (a
  3-tuple), and `get_job_run_states()` now iterates all three tracked ids.
  `src/backend/app/scheduling/capture_scheduler.py::run_capture_if_idle`
  restructured into two steps — Pull (bundled with Meeting/Todo capture's
  own still-unchanged Outlook legs, under the shared lock, exactly as
  today) THEN, after that lock releases, Processing dispatched separately
  through the new dedicated lock; both `_make_scheduled_tick_callback`
  (`agent_schedule_registry.py`) and `_build_scheduled_tick` (`capture_
  scheduler.py`) now route a persisted `process_staged_email` schedule
  through the dedicated lock too (live-mutation and cold-start paths
  both fixed). `src/backend/app/business/email_classification.py::
  run_capture_for_agent`'s email branch now composes `email_pull.
  pull_and_stage_emails()` + `run_email_capture_pipeline()` in one call
  (necessary so `run_capture_now`'s own "fully captured end-to-end"
  contract survives `T03` retiring Fetch from `run_email_capture_
  pipeline`); `run_capture_and_record_completion` gains a `trigger:
  Literal["scheduled", "direct"] = "direct"` parameter — only the
  scheduled tick's own Autonomous branch does Pull-only, under the shared
  lock, leaving every other caller (`run_capture_now`, a Supervised
  background-approval Approve) byte-for-byte unchanged.
  Verified live against the real, configured Outlook inbox/Compass/vault:
  `AC-01` (a real Pull staged 1 genuinely new email; grep-confirmed no
  downstream Job imports `outlook_com`), `AC-02` (a controlled,
  deterministic induced stall — `pull_email` stalled 15s, `process_
  staged_email` completed in `0.53s`, fully inside the stall window) and
  `AC-03` (reversed — `process_staged_email` stalled ~58.5s across 4
  items, `pull_email` completed in `0.01s`) all PASS — direct,
  unambiguous proof the two capabilities share no lock. `run_capture_
  now`'s own backward-compatible contract confirmed via call-count
  instrumentation (`pull_and_stage_emails` called exactly once inside one
  synchronous `run_capture_now` call); the 4 real staged test emails
  could not be observed filing successfully this session due to a
  genuine, external, unrelated Compass API flakiness (`CompassError:
  couldn't parse Compass response`, reproduced twice via an isolated,
  dispatch-independent re-invocation) — not a regression, the pre-
  existing per-item failure posture (`AC-04`/`T03`) correctly held
  throughout. `GET /system-health`'s response shape confirmed unchanged
  (same 4 top-level keys); `scheduling` now correctly carries 5 real
  entries (was 3). A genuine transitive circular import was found and
  fixed within scope (`skill_tools -> email_classification -> ... ->
  skill_registry -> skill_tools -> email_capture_pipeline`, confirmed via
  direct testing under multiple real import orders) via a deferred import
  mirroring `build_knowledge`'s own established precedent. A disclosed,
  out-of-scope residual gap logged (not fixed, `ESC-045`, `Status: Open`):
  `agent_schedules_router.py::run_now` still hardcodes the shared lock for
  every `capability_id`, including `process_staged_email` — outside this
  task's own `## Files to Modify`; the hard Constraint (lock separation
  for the hourly/app-start scheduled tick) is unaffected since both real
  locations that matter for that trigger path were fixed. `gate: flagged`,
  a `REVIEW-QUEUE.md` pointer filed, non-blocking.
  **`REQ-SB-69-US-01` story `status: Done`** — all 8 tasks (`T01`-`T08`)
  complete, all 11 locked ACs (`AC-01`-`AC-11`) verified live; `gate:`
  stays `flagged` (the standing `ADR-046`/trigger-3 human-review flag,
  unresolved, independent of build completion). **`SPRINT-056`
  `status: Done`** — its one story is now `Done`; sizing estimate (~8
  tasks, L) matched exactly; `gate:` set to `flagged` (retro-harvest, plus
  the standing `ADR-046` review). Full evidence:
  `Implementation/Tasks/REQ-SB-69-US-01-T04-independent-pull-and-process-dispatch.md`
  → `## Implementation Log`.
- fix: `ESC-045` follow-up (`REQ-SB-69-US-01-T04`/`ADR-046` Decision 4) —
  `src/backend/app/api/agent_schedules_router.py::run_now` no longer
  hardcodes the shared Outlook-COM dispatch lock for every
  `capability_id`; it now selects `agent_schedule_registry.dispatch_with_
  dedicated_processing_lock` for `capability_id == "process_staged_email"`
  and keeps `dispatch_with_shared_lock` for every other id (`pull_email`
  included), mirroring `_make_scheduled_tick_callback`'s/`_build_
  scheduled_tick`'s own already-shipped dispatch-selection shape. While
  checking this endpoint's sibling manual-dispatch surface, also found and
  fixed a related, previously-undisclosed gap in `src/backend/app/api/
  agents_router.py::_invoke_capability`: `pull_email`/`process_staged_
  email` (both real `skill_tools.SKILLS` members reachable via `POST
  /agents/{agent_id}/actions/{action_id}`) fell through to the generic,
  UN-locked `skill_registry.invoke_skill` branch entirely — not merely the
  wrong lock, no lock at all. Fixed identically (`pull_email` → shared
  lock, `process_staged_email` → dedicated processing lock); `history_
  recorded` widened to cover both ids so no duplicate history entry is
  written. Verified live: real backend process, `email_pull.pull_and_
  stage_emails` monkeypatched to a real 15s sleep and `email_capture_
  pipeline.classify_captured_email` monkeypatched to fail fast per item
  (mirrors `T04`'s own AC-02 induced-stall technique), against the 4 real
  items already staged in the configured vault — a separately-dispatched
  `process_staged_email` completed in 0.55s (via `run_now`) and 0.64s (via
  `_invoke_capability`) while the shared lock was confirmed held and
  `pull_email` was still genuinely mid-sleep (completing at 15.01s both
  times), through both fixed entry points; all 4 staged items remained
  staged afterward (no data loss). `ESC-045` (`ESCALATIONS.md`) updated to
  `Status: Resolved`; its `REVIEW-QUEUE.md` pointer updated (the
  reconciliation-judgement-call spot-check item stays open independently).
- feat: `REQ-SB-69-US-01-T08` (`SPRINT-056`, "Decoupled Email Pull +
  Human-Readable, Graph-Connected Thread Notes", `ADR-046` Decision 9) —
  Thread notes gain a new, deterministically-regenerated `## Related`
  body section. `src/backend/app/data_access/vault_writer.py::
  create_thread_note_baseline`'s body literal gains a third, initially
  empty section (`"## Summary\n\n## Transcript\n\n## Related\n"`). New
  `src/backend/app/business/email_classification.py::
  _build_thread_related_wikilinks(customer, participants, project) ->
  str` composes three already-shipped, read-only stem-resolution
  primitives — `vault_writer.hub_note_path(customer).stem` (the same
  source `customer_hub_linking.link_note_to_customer_hub` already uses),
  `people_extraction.find_existing_person_note(email)` per participant (a
  participant with no real Person note honestly omitted), and
  `vault_writer.project_directory_paths(customer, project)["concept"]
  .stem` (the same convention `route_to_project`/`finalize_thread_
  project_routing` already use) — into a Markdown bullet list of real
  `[[wikilink]]`s, or `""` when none are currently resolvable.
  `thread_match_merge` gains one new call, placed after its own rename
  block (targeting the FINAL, post-rename path) and before its `result`
  dict is built: `vault_writer.replace_body_section(path, "## Related",
  _build_thread_related_wikilinks(...))` — a full, deterministic
  regeneration via `replace_body_section` on EVERY call, deliberately
  never Email's own `insert_body_line_if_missing`-based inline
  primitives, per `ADR-046` Context point 6's own found primitive
  conflict with `replace_body_opening_line`'s full ownership of the same
  pre-first-header region. Verified live against the real, configured
  vault (`VAULT_PATH`) — `AC-10` (a real Customer-hub `[[wikilink]]` and a
  real Person `[[wikilink]]` both written into `## Related`; a real
  bidirectional graph edge confirmed via this codebase's own already-
  shipped `vault_indexing.rebuild_index()` backlink index, standing in
  for Obsidian's own graph view — no browser/GUI tool available this
  session) and `AC-11` (an `"Unsorted"`-customer, no-real-Person-note
  message produces a present but genuinely empty `## Related` section —
  no fabricated/placeholder link) both passed, plus the "regenerates from
  CURRENT state on every call" check (a later message, after a real
  Project OKF directory was created and the Thread's `project`
  frontmatter set, grew `## Related` to include the Project's own
  `[[wikilink]]` without disturbing the Customer/Person links already
  there) and an idempotency check (a third identical-input call produced
  no duplication/corruption). Every disposable Thread note/Project OKF
  directory this verification created was cleaned up afterward; the
  vault's 2 pre-existing real Thread notes and `Work/Customers/Core42/`'s
  own pre-existing files were confirmed unchanged. One scope-internal
  assumption logged (`_build_thread_related_wikilinks`'s own exact
  parameter list omits the task text's sketched `path` parameter, per
  `ADR-046` Decision 9's own literal composition) — `gate: flagged`, a
  spot-check-only `REVIEW-QUEUE.md` pointer filed, non-blocking.
  **`REQ-SB-69-US-01` story status: `In Progress`, `T04` still `Ready`**
  — `T08` is the last task in its own chain (`T05`→`T08`) and is now
  `Done`, but the story's other independent chain (`T01`→`T04`,
  pull/staging decoupling) has `T04` still outstanding (a sibling coder
  session, per this task's own dispatch note) — the story cannot advance
  to `Done` until `T04` also completes and every locked AC across all 8
  tasks is verified.
- feat: `REQ-SB-69-US-01-T07` (`SPRINT-056`, "Decoupled Email Pull +
  Human-Readable, Graph-Connected Thread Notes", `ADR-046` Decision 10) —
  new `src/backend/app/data_access/vault_writer.py::
  format_human_readable_datetime(raw: str) -> str`, parses `email
  ["received"]`'s own raw COM-stringified shape (`datetime.fromisoformat`,
  with a date-only `strptime` fallback) and renders it human-readably
  (e.g. `"Aug 16, 2026, 1:02 PM"`) — never raises, returns the input
  unchanged on a genuine parse failure. `src/backend/app/business/
  email_classification.py::thread_match_merge` gains one additive
  `upsert_frontmatter_key(path, "last_message_at_display", ...)` call,
  written alongside (never instead of) the existing, byte-for-byte-
  unchanged `last_message_at` write; the `## Transcript` entry's own
  timestamp interpolation now renders human-readably via the same helper.
  Verified live against the real, configured vault (`VAULT_PATH`) — `AC-08`
  (4/4 assertions: `last_message_at_display` human-readable,
  `last_message_at` unchanged, `## Transcript` entry human-readable) and
  `AC-09` (3/3 assertions: `meeting_classification.py::
  _date_proximity_gap_days`/`_link_to_thread_by_fallback_heuristic` still
  correctly parse `last_message_at` and link a real Meeting to the right
  Thread, unregressed) both passed, plus the malformed-input regression
  check (`format_human_readable_datetime("not a real date")` returns it
  unchanged). Every disposable Thread note this verification created was
  cleaned up afterward; the vault's 2 pre-existing real Thread notes were
  left untouched.
- feat: `REQ-SB-69-US-01-T02` (`SPRINT-056`, "Decoupled Email Pull +
  Human-Readable, Graph-Connected Thread Notes", `ADR-046` Decisions 2/3)
  — `src/backend/app/data_access/outlook_com.py::list_recent_mail` gains
  an additive, optional `on_item_fetched: Callable[[dict], None] | None =
  None` parameter, invoked once per item, inside the existing per-item
  loop, immediately after that item's own dict is fully resolved, never
  buffered until the whole COM loop returns; every existing caller
  (`classify_recent_emails`, `email_poc_router.py`'s POC endpoint) passes
  nothing and is unaffected. New
  `src/backend/app/business/pipelines/email_pull.py` —
  `pull_and_stage_emails(limit: int = 10) -> dict`, the sole remaining
  `outlook_com` importer in the email path: wires the new callback to a
  filtering closure over `email_staging.stage_email` so
  already-processed/already-staged ids are pre-filtered and never
  re-staged on an overlapping re-run; returns an honest `{"fetched",
  "newly_staged", "already_staged_or_processed"}` summary. Verified live
  against the real, configured Outlook desktop and vault (`VAULT_PATH`)
  — all 4 manual Test steps passed, including a real Pull staging 3
  genuinely new emails and a second, immediate re-run staging zero
  duplicates.
- refactor: `REQ-SB-69-US-01-T03` (`SPRINT-056`, "Decoupled Email Pull +
  Human-Readable, Graph-Connected Thread Notes", `ADR-046` Decision 3) —
  `src/backend/app/business/pipelines/email_capture_pipeline.py::
  run_email_capture_pipeline` now reads its per-item input from
  `email_staging.list_staged_emails()` instead of calling `outlook_com.
  list_recent_mail` directly; the module drops its `outlook_com` import
  entirely (`from app.data_access import email_staging, vault_writer`).
  On per-item success, `email_staging.remove_staged_email(email["id"])`
  is now called alongside the existing `vault_writer.mark_email_processed(
  email["id"])`; on the existing per-item failure branch neither is
  called, so a failed item stays staged AND unmarked for a later run to
  retry — the per-email try/except+continue posture now spans the new
  staging boundary too (`AC-04`). `vault_writer.load_processed_email_ids()`
  stays a deliberate second, independent check at processing time. The
  `limit` parameter is kept on the function's own signature (unused by
  the body now) for call-site backward compatibility. The compiled graph
  (`_build_graph`/`_GRAPH`/`get_job_tree()`) is completely unchanged.
  Verified live against the real, configured vault and venv — `AC-04`
  passed (16/16 checks: a per-item failure leaves that item staged and
  unmarked while the other two staged items in the same run are removed
  from staging and marked processed normally; a retry run then completes
  the previously-failed item successfully), plus both non-AC regression
  checks (no `outlook_com` import; `get_job_tree()`'s 6 Job ids/edges
  byte-identical to before). Every synthetic test artefact this
  verification created was cleaned up afterward.
- feat: `REQ-SB-69-US-01-T05` (`SPRINT-056`, "Decoupled Email Pull +
  Human-Readable, Graph-Connected Thread Notes", `ADR-046` Decisions 6/7)
  — new Thread filename/lookup/rename primitives in
  `src/backend/app/data_access/vault_writer.py`, standalone, not yet
  wired into `thread_match_merge` (`T06`'s scope): `thread_note_filename_
  stem(thread_name, date, conversation_id)` (mirrors `meeting_note_
  filename_stem`'s `<name>-<date>-<hash8>` shape, but hashes
  `conversation_id` ALONE — deliberately never combined with `thread_name`/
  `date` — so the disambiguator stays stable across a Thread's later
  filename renames even though its `date` component moves on every new
  message); `thread_note_path_for(thread_name, date, conversation_id)`
  (resolves without checking existence, mirrors `meeting_note_path`);
  `resolve_thread_note_path(conversation_id) -> Path | None` (a pure,
  read-only frontmatter-scan lookup over the already-shipped
  `list_thread_notes()`, replacing `thread_note_path`'s now-retired
  "deterministic from `conversation_id` alone" contract — no new persisted
  index file, per `ADR-046`'s own rejected alternative); `rename_thread_
  note(old_path, new_path)` (physical rename, refuses to silently
  overwrite a genuine collision — mirrors `move_note_and_attachments`'s
  own refuse-to-overwrite discipline — and is a safe no-op when
  `old_path == new_path`). `_THREAD_NOTE_BASELINE_KEYS` gains a 4th key,
  `thread_name`; `create_thread_note_baseline`/`ensure_thread_note_
  baseline_frontmatter` both gain a `thread_name` parameter, following
  the same baseline-preservation/top-up-only-if-missing contract as the
  existing three keys. `thread_note_path`/`thread_note_exists` (the old
  deterministic-from-`conversation_id`-alone functions) are left
  unmodified and undeleted, per `ADR-046`'s own Consequences (retirement
  is a separately-scoped future task). Verified live against the real,
  configured vault (`VAULT_PATH`) — all 19 assertions across the task's 5
  manual Test steps passed; the vault's 2 pre-existing real Thread notes
  were left untouched and every disposable test note this verification
  created was cleaned up afterward.
- feat: `REQ-SB-69-US-01-T06` (`SPRINT-056`, "Decoupled Email Pull +
  Human-Readable, Graph-Connected Thread Notes", `ADR-046` Decisions 6-8)
  — `src/backend/app/business/email_classification.py::thread_match_merge`
  wired onto `T05`'s new filename/lookup/rename primitives: create-vs-
  update now resolved via `resolve_thread_note_path(conversation_id)`
  (replacing the retired `thread_note_exists`/`thread_note_path` pair for
  this call site); on create, `thread_name` is captured once from the
  first message's own subject and the Thread is written directly at its
  correct human-readable filename via `thread_note_path_for`
  (`create_thread_note_baseline` correspondingly gained a required `date`
  parameter so its own internal `write_note` call uses the new
  `thread_note_filename_stem`-derived stem, never the old
  `conversation_id`-only one); on update, every existing read/write is
  unchanged, and a rename (via `rename_thread_note`) is computed and
  applied strictly AFTER every other frontmatter/body write for that
  call has completed, using the Thread's own already-resolved
  `thread_name` (never recomputed from a later message's own subject).
  Also fixes the real, previously-latent stale-Pending-Approval-payload
  bug (`ADR-046` Decision 8): `route_to_project`'s payload gains
  `conversation_id`; `finalize_thread_project_routing` re-resolves the
  Thread's CURRENT real path via `resolve_thread_note_path` at Approve
  time instead of trusting the `thread_path` string captured at proposal
  time, with a working legacy-string fallback for any pre-`T06` Pending
  Approval (no `conversation_id` key) or a genuinely unresolvable Thread.
  Verified live against the real, configured vault (`VAULT_PATH`) — all
  21 assertions across `AC-05`/`AC-06`/`AC-07` and both non-AC regression
  checks (stale-payload rename-before-approve; legacy-payload fallback)
  passed, including real Compass-synthesized `## Summary`/opening-line
  regeneration and a real `guess_project_for_thread` call; every
  disposable Thread note/Customer-Project directory/Pending-Approval
  record this verification created was cleaned up afterward.
- fix: `BUG-019` (`Closed`, direct fix, same pass as `T06`'s own
  verification) — `src/backend/app/business/meeting_classification.py::
  _link_to_thread_by_conversation_id` (`REQ-SB-56-US-01`'s Link-to-Thread
  PRIMARY strategy) still checked `vault_writer.thread_note_exists(
  conversation_id)`, which silently returns `False` for every
  genuinely-existing Thread created after `T06`'s human-readable-filename
  change ships — permanently starving the primary exact-match strategy in
  favor of the weaker date-proximity fallback, no exception, no log.
  Found live via a repo-wide grep for the OLD helper's own real callers
  (`ADR-046`'s own Consequences section mischaracterized it as "becomes
  dead code" — a real, live second caller existed). Fixed by swapping the
  existence check to `resolve_thread_note_path(conversation_id) is not
  None` — the same real, current-path lookup `T05`/`T06` already built.
  Verified live: a disposable post-fix Thread + Meeting note confirmed
  the primary strategy now links correctly. See `ESC-044`
  (`ESCALATIONS.md`).
- feat: `REQ-SB-69-US-01-T01` (`SPRINT-056`, "Decoupled Email Pull +
  Human-Readable, Graph-Connected Thread Notes", `ADR-046` Decision 1) —
  new `src/backend/app/data_access/email_staging.py`, a durable,
  vault-local, per-email staging store: `stage_email`/
  `list_staged_emails`/`remove_staged_email`, one directory per email
  under `.second-brain/email_staging/<entry_id>/` (`email.json` metadata
  plus real attachment bytes under `attachments/`, never base64-inflated
  into JSON — mirrors `upload_storage.py`'s `ADR-034` blob-on-disk
  precedent). Idempotent re-stage (overwrite, not duplicate) and
  idempotent remove; `list_staged_emails()` reconstructs the exact
  `outlook_com.list_recent_mail`-shaped dict so no downstream Job's own
  function body needs to change once wired in (`T02`/`T03`). Never
  imports `outlook_com` or `vault_writer`. Verified live against the
  real, configured vault — all 5 manual Test steps passed.
- fix: `BUG-018` (direct fix, 2026-08-17, `ESC-043`, found while
  verifying `BUGFIX-03-US-01-T02`) — `app/business/cockpit/
  attachments.py`'s `list_attachments`/`hand_off_attachment_to_chat`
  silently broke for any email captured after `T02`'s own per-message
  attachment nesting (they assumed a flat `.../attachments/<stem>/
  <filename>` layout `write_attachments` no longer produces). New
  `_iter_attachment_files` generator supports both the real, already-
  saved historical flat shape (untouched, never migrated) and the new
  nested shape, so both old and new attachments are found correctly.
  Verified live against the real vault both directions.
- fix: `BUG-017` (direct fix, 2026-08-17, found while investigating
  `BUGFIX-03-US-01-T01`) — `outlook_com.py::_is_inline_attachment` no
  longer treats a mere non-empty MIME `PR_ATTACH_CONTENT_ID` as proof
  an attachment is inline. Some sending mail systems stamp a genuine
  Content-ID on real, standalone attachments too — this silently
  dropped them from capture entirely (confirmed live: a real 4.96MB
  PDF, "260816 Agentic academy v06_shared.pdf", the root cause of the
  historical "Presight Agent Academy Demo" Thread never capturing its
  own real attachment). Now requires the Content-ID to be genuinely
  referenced inline via a `cid:` URL in the message's own `HTMLBody`,
  falling through to the existing filename heuristics otherwise.
  Verified live both directions against the real mailbox: the
  previously-dropped PDF now resolves `is_inline=False`; a sample of
  genuinely-inline images (`image001.png`/`.jpg`, `image002.png`,
  `image003.png`, multiple `thumbnail_emailsignature_*`/`logo_*`
  files) all still correctly resolve `is_inline=True` — no regression.
- fix: `BUGFIX-03-US-01-T01` (`SPRINT-055`, `BUG-014` gap 1) —
  `email_capture_pipeline.py::_summarize_attachment_node` no longer
  silently discards an attachment that fails to save or summarize.
  `summarize_attachment` already returned an honest `summary_error` on
  every non-success outcome (oversized/unsaved, saved-but-
  unsummarizable), but the node only appended to `attachment_entries`
  when a real `dated_entry` was present — every other outcome vanished
  with no trace, so `thread_match_merge` never wrote a `## Attachments`
  line for it and `write_attachments`' own `attachments/` directory
  never even got created for the oversized case. New module-level
  `_fallback_attachment_entry` synthesizes a visibly-distinct fallback
  line (`"(not saved — ...)"` / `"(saved but could not be summarized —
  ...)"`) whenever `dated_entry` is absent, mirroring
  `classify_recent_emails`' own already-established honest-fallback
  wording. `summarize_attachment`'s own signature/return contract/body
  unchanged. Verified via a throwaway in-process monkeypatch (real
  `.venv`, no permanent code change): both fallback cases produce the
  exact expected wording, and a genuine `dated_entry` still passes
  through unwrapped (no regression). Live-diagnostic sub-step also ran
  against the real Outlook mailbox for the historical "Presight Agent
  Academy Demo" Thread — the real cause was none of `architecture.md`'s
  four candidates; `outlook_com.py::_is_inline_attachment` false-
  positives on that message's one genuine PDF attachment (see `MEMORY.md`
  Constraints), a separate, not-yet-filed defect, recorded but not fixed
  here. `AC-01`/`AC-02` (locked) remain unverified — both need `T02`'s
  gap-2 fix and are verified together in `T02`'s own live end-to-end
  session.
- fix: `BUG-015` (direct fix, live investigation session, not through a
  BUGFIX story — urgent, applied 2026-08-17) —
  `email_classification.py::run_capture_and_record_completion` no
  longer mislabels a failed email as "filed" in its own history text.
  `run_email_capture_pipeline`'s per-email try/except catches a failure
  (e.g. a Compass timeout) and appends `{"subject", "error"}` into the
  SAME results list a real success populates — previously counted 1:1
  toward "N email(s) filed" regardless. Now splits `results` into
  `filed`/`failed` before building the history text:
  `"N email(s) filed, M failed (will retry next run)"` when any failed,
  unchanged `"N email(s) filed"` otherwise. Root cause discovered live:
  3 real emails ("RE: Azure-Net New Revenue Forecast...", "RE: Weekly
  Forecast l Major/Strategic Clients") were consistently failing
  `classify_email` (Compass timeout / empty response) and being
  silently reported as successes — no data loss (a failed email is
  never marked processed, so it retries every tick), but the history
  log was actively misleading about it.
- fix: `compass_client.py::classify_email` gains a 3-attempt retry with
  backoff (1.5s × attempt) around its Compass HTTP call, covering both
  `httpx.HTTPError` and the response-parse failure path (an empty/
  malformed response body is itself an observed real failure mode, not
  just a transport-level error). Confirmed live NOT to fix `BUG-015`'s
  3 specific emails (same failures reproduced identically after
  retries — ruled out as transient) but a reasonable general resilience
  improvement for genuinely transient Compass blips going forward.
  Verified the retry path doesn't regress the normal success case.
- feat: `REQ-SB-56-US-01-T02` (`SPRINT-053`) — `Link-to-Thread` Job,
  attendee-overlap + date-proximity fallback strategy, tried only when
  `T01`'s primary `conversation_id` strategy left a meeting unlinked.
  Thresholds are real, config-backed values, never Python constants: new
  `app/business/meeting_thread_link_config.py` (`get_attendee_overlap_floor`
  / `set_attendee_overlap_floor`, `get_one_on_one_carve_out_enabled` /
  `set_one_on_one_carve_out_enabled`, `get_date_proximity_days` /
  `set_date_proximity_days`; self-healing per-key defaults `2` / `true` /
  `7`), backed by a new sibling `.second-brain/meeting_thread_link_config.json`
  store, mirroring `agent_prompts.py`/`working_mode_registry.py`'s own
  established sibling-JSON-store convention. New `vault_writer.py`
  primitives: `load_meeting_thread_link_config()` /
  `save_meeting_thread_link_config(config)` (pure I/O, mirrors
  `load_working_modes_state`/`save_working_modes_state`), and
  `list_thread_notes()` (a scoped Threads-folder enumeration, composing
  the already-existing `list_notes_in_kind_folder("Threads")`). New
  `app/business/meeting_classification.py::
  _link_to_thread_by_fallback_heuristic(event, self_excluded_attendees)`:
  self-excludes `settings.self_email` from both the meeting's own
  attendees and every candidate Thread's own `participants`; a Thread
  missing either `participants` or `last_message_at` is skipped outright;
  requires BOTH the attendee-overlap bar (>= the configured floor shared
  attendees, OR exactly 1 shared attendee that is the entirety of the
  smaller of the two sets, when the 1:1 carve-out is enabled) AND the
  date-proximity bar (within the configured day window of the Thread's
  own `last_message_at`, either direction) to clear; multiple qualifying
  Threads tie-break by higher overlap count then smaller date gap; a tie
  surviving both leaves the meeting explicitly unlinked, never a forced
  weak match. Wired into `classify_recent_meetings` right after `T01`'s
  primary-strategy call, only when it did not link, via the same
  `vault_writer.upsert_frontmatter_key` write path. Verified against a
  `VAULT_PATH`-scratch vault: overlap+proximity link (`AC-02`), the 1:1
  carve-out firing specifically rather than just the raw `>=2` floor
  (`AC-02`), an overlap-clears-but-proximity-fails case and its inverse
  both leaving the meeting unlinked (`AC-03`), a genuine tie on both axes
  leaving it unlinked (`AC-03`), a full regression pass confirming
  `classify_recent_meetings`'s existing customer/attendee/hub-linking/
  note-create-or-top-up outputs are unaffected (`AC-04`, finalizing `T01`'s
  own partial pass), and `BACKLOG.md`'s `REQ-SB-53` row re-confirmed
  already reading superseded/Parked (`AC-05`, no edit needed). The
  config-not-hardcoded requirement was proven, not just asserted: raising
  `attendee_overlap_floor` to `3` via `set_attendee_overlap_floor` made an
  otherwise-identical 2-overlap case newly fail to link, then reset to
  the default; `.second-brain/meeting_thread_link_config.json` confirmed
  on disk holding all 3 keys after first read/write. This closes out
  `REQ-SB-56-US-01`'s last task — the story, `SPRINT-053`, and
  `BACKLOG.md`'s `REQ-SB-56` row are marked `Done`. Full detail: task's
  own `## Implementation Log`, `Implementation/Tasks/
  REQ-SB-56-US-01-T02-link-to-thread-fallback-strategy.md`.

- feat: `REQ-SB-56-US-01-T01` (`SPRINT-053`) — `Link-to-Thread` Job,
  primary `conversation_id`-match strategy, built under the operator's
  provisional Option (a) resolution of `ESC-040` (`T00`'s negative live
  finding). `list_calendar_events` (`app/data_access/outlook_com.py`)
  gains a new safe `_resolve_conversation_id(item)` helper and a
  `"conversation_id"` field on its returned dict — resolves to `""` for
  BOTH an absent property and a present-but-COM-inaccessible/non-string
  one (narrow `try/except` + `isinstance(value, str)` guard), deliberately
  NOT `list_recent_mail`'s own `getattr(item, "ConversationID", None) or
  ""` pattern, which would silently pass a broken bound-method object
  through as a truthy fake id. `app/business/meeting_classification.py`
  gains `_link_to_thread_by_conversation_id(event, note_path) -> bool`,
  called additively from `classify_recent_meetings` after the existing
  customer/attendee linking logic: writes a matching `conversation_id`
  into the Meeting note's own `thread` frontmatter field ONLY when it is
  non-empty AND an already-existing Thread note carries it (never creates
  a Thread note itself); every other case leaves `thread` at its reserved
  empty string. Adds a new `"thread_linked": bool` key to
  `classify_recent_meetings`'s own per-event result dict. `AC-01` plus
  the new untagged ConversationID-safety check verified against a
  `VAULT_PATH`-scratch vault: a matching `conversation_id` links (thread
  field populated, function returns `True`); a non-matching non-empty one
  and an empty/absent one both leave `thread` empty with no exception and
  no false Thread creation; a real, live spot-check against 16 real
  recurring-occurrence calendar items on this same Outlook installation
  (matching `T00`'s own recorded broken subjects, e.g. "Weekly Forecast l
  Strategic Clients") confirmed `conversation_id` resolves safely to `""`
  with zero exceptions, plus a synthetic double pinning the exact ESC-040
  failure shape (attribute access returns a callable, raises only if
  invoked). No existing line of `list_calendar_events` or
  `classify_recent_meetings` was changed. Full detail: task's own
  `## Implementation Log`, `Implementation/Tasks/
  REQ-SB-56-US-01-T01-link-to-thread-primary-strategy.md`.

- verify: `REQ-SB-56-US-01-T00` (`SPRINT-053`) — live, read-only,
  independently-executed COM probe of real Outlook calendar items
  (mirroring `list_calendar_events`'s own `GetDefaultFolder(9)` /
  `IncludeRecurrences = True` / `[Start]`-window mechanics) to determine
  whether meeting/appointment items expose a usable `ConversationID` on
  this installation, before `T01` builds the primary Meeting-to-Thread
  linking strategy on top of it. Result: **NEGATIVE**, contradicting the
  previously-referenced "100/100 non-empty" figure — 22/37 (59.5%) real
  sampled items carried a genuine, usable `ConversationID`; 15/37 (40.5%,
  a material fraction) — every one an `IncludeRecurrences`-expanded
  recurring-occurrence item — returned a broken, non-string value via
  both the `.ConversationID` convenience property and the raw MAPI
  `PropertyAccessor` fallback. No `src/` code was changed (read-only
  task). `REQ-SB-56-US-01-T00` marked `Done` (its own job — probe and
  record — was performed correctly); `REQ-SB-56-US-01-T01` marked
  `Blocked` pending a human/architect decision on how the primary
  strategy should treat recurring-occurrence meetings. Full finding:
  `Implementation/UserStories/
  REQ-SB-56-US-01-meeting-capture-and-thread-linking.md` → `## Notes`;
  `REVIEW-QUEUE.md`; `ESCALATIONS.md` → `ESC-040`.

- feat: `REQ-SB-66-US-01-T01` (`SPRINT-052`) — new
  `.second-brain/agent_prompts.json` sibling store, composed alongside
  `app/business/agent_registry.py` (never inside it, `ADR-011` point 2,
  `ADR-044`). New `app/business/agent_prompts.py`: `get_prompt(id)`/
  `set_prompt(id, prompt)` (`None` when unset — no sensible universal
  default text of its own), `get_guardrails(id)`/`set_guardrails(id,
  guardrails)` (`""` when unset — always present, structure-only), each
  whole-value-replace, zero cross-id bleed. New `vault_writer.py`
  primitives: `_agent_prompts_path()`, `_load_agent_prompts_index()`,
  `load_agent_prompt_record(id)`/`save_agent_prompt_record(id, record)`
  — mirrors `agent_keywords.py`/`working_mode_registry.py`'s own
  established sibling-store shape one-for-one. One flat id-keyed
  namespace covers both a real Agent id (e.g. `"vault-filing-expert"`)
  and a real Job id (e.g. `"classify"`) uniformly, no special-casing.
  This task only builds the store's own get/set surface — wiring the
  override into any real prompt-building call site is `T02`/`T03`'s own
  scope; any HTTP-reachable endpoint is `T04`/`T06`'s own scope.

- feat: `REQ-SB-66-US-01-T02` (`SPRINT-052`) — wired the new Prompt
  override into `compass_client.py`'s 4 hardcoded-prompt-building
  functions (`classify_email`, `classify_task`, `guess_project_for_thread`,
  `summarize_content`), each gaining a new, optional
  `prompt_override: str | None = None` parameter. Unset (`None`, the
  default) reproduces today's exact hardcoded prompt text byte-for-byte
  (additive layering, `ADR-044`); when set, the override text replaces
  only the function's own static instructional text, with the same real
  per-call dynamic data (subject/sender/body, known-customer/kind/project
  lists, thread summary, source content) still appended verbatim.
  `email_classification.classify_captured_email`/`route_to_project`/
  `summarize_attachment` and `todo_classification.classify_recent_todos`
  — each the ONE real, confirmed owning call site for its own
  `compass_client` function — now resolve their own owning id's stored
  override via `agent_prompts.get_prompt("classify"/"route_to_project"/
  "summarize_attachment"/"todo-capture")` and pass it through.
  `classify_recent_emails`'s own separate call (the still-live, manual
  `/poc/classify-emails` path) and `skill_tools.summarize_file`'s own
  separate call (a shared, cross-agent MCP skill with no single owning
  identity) are both deliberately left unwired — disclosed dual-ownership/
  second-caller scoping calls, per the parent story's own `## Non-Goals`.
  `compass_client.py` (data_access) never imports `agent_prompts.py`
  (business) — the override lookup happens only in the business-layer
  callers, which pass the already-resolved string down as a plain
  parameter (`ADR-003` layering).

- feat: `REQ-SB-66-US-01-T03` (`SPRINT-052`) — wired the new Prompt
  override into the 2 remaining real call sites this story covers.
  `agent_orchestration/state.py`'s `history_entries_to_messages` gained
  an optional `agent_id: str | None = None` parameter — when given, it
  resolves `agent_prompts.get_prompt(agent_id)` and, when a stored
  override exists, uses it as the per-turn Chat `SystemMessage`'s own
  content in place of the hardcoded identity/grounding sentence
  (`REQ-SB-33-US-01`); unset reproduces today's exact hardcoded text
  byte-for-byte. `graph.py`'s `run_agent_conversation` now passes its
  own already-in-scope `agent_id` through to this call — the
  `record_knowledge_gap` tool-call mechanism itself (bound onto every
  turn's tools list, and every other node in the conversation graph) is
  untouched; only the SystemMessage's own default text becomes
  overridable. `vault_filing_methodology.build_placement_prompt` gained
  an optional `prompt_override: str | None = None` parameter, replacing
  `_METHODOLOGY_EXCERPT` as the returned `SystemMessage`'s own content
  when set; the `HumanMessage` (known-lists/schema/content) is never
  overridable, built identically either way.
  `vault_filing_expert.determine_placement_and_file` resolves
  `agent_prompts.get_prompt("vault-filing-expert")` — the ONE owning
  identity, regardless of `requesting_agent_id` (bookkeeping-only) or
  caller (`REQ-SB-20` Hub routing or `email_classification.
  consult_librarian`'s own internal call alike) — and passes it through
  as `prompt_override`. `agent_chat.py` was not modified — confirmed by
  direct reading to carry no LLM prompt of any kind, out of this task's
  scope entirely despite the PRD's own naming of it.

- feat: `REQ-SB-66-US-01-T04` (`SPRINT-052`) — extended the existing
  `GET`/`PATCH /agents/{agent_id}` verb pair with `prompt`/`guardrails`
  fields, for every real Agent (Worker/Producer/Expert), composed at the
  router layer via `T01`'s `agent_prompts.py` (`agent_registry.py` itself
  not modified). `GET /agents/{agent_id}` now returns `"prompt": str |
  None` (the STORED override only, `None` when unset — never a
  resolved-effective-default) and `"guardrails": str` (`""` when unset)
  alongside every pre-existing field, unchanged. `AgentAssignmentUpdateBody`
  gained optional `prompt`/`guardrails` fields; `PATCH
  /agents/{agent_id}` whole-value-replaces either when supplied, mirroring
  `keywords`/`scope`'s own omitted-means-unchanged convention. `GET /agents`
  (list) is untouched — `prompt`/`guardrails` stay detail-only fields,
  matching `keywords`/`scope`'s own precedent. Scenario 5/6
  (`AC-05`/`AC-06`) verify fully once `T05` wires `AgentDetailPanel.tsx`'s
  actual kv-rows against this endpoint; this task's own verification is 4
  non-AC smoke checks confirming the endpoint's shape/behavior in
  isolation.

- feat: `REQ-SB-66-US-01-T05` (`SPRINT-052`) — `AgentDetailPanel.tsx`'s
  Settings tab gains two new editable `kv-list` rows, Prompt (a
  `<textarea>`) and Guardrails (a text `<input>`), shown unconditionally
  for every real Agent Type (Worker/Producer/Expert), alongside the
  existing Section/Provider/Working mode/Background Agent/Keywords/Vault
  scope rows — never a new tab, never a new screen. Mirrors the
  Keywords/Vault-scope rows' own exact commit-on-blur UX one-for-one: new
  `promptDraft`/`guardrailsDraft` local state, reset on agent switch and
  synced from `fetchAgent(agentId)`'s response, committed via new
  `handlePromptCommit`/`handleGuardrailsCommit` (`updateAgentAssignment(
  agentId, { prompt: promptDraft })` / `{ guardrails: guardrailsDraft }`,
  `setAgent(updated)`, re-sync the draft from the response). New rows
  carry their own `data-testid="settings-prompt-input"` /
  `data-testid="settings-guardrails-input"`, distinct from the Overview
  tab's pre-existing, unrelated, hardcoded `data-testid="overview-
  guardrails"` row (`REQ-SB-33-US-01`), left byte-for-byte unchanged.
  `agentsApiClient.ts`'s `AgentDetail` interface gained `prompt: string |
  null` / `guardrails: string`; `updateAgentAssignment`'s body type gained
  optional `prompt?: string` / `guardrails?: string`. No `/design` pass
  (operator-directed, story-level decision) — built directly against the
  existing `kv-list` visual language. Live-verified against the real
  running backend (`http://127.0.0.1:8001`): `GET /agents/{id}` shows
  `prompt: null`/`guardrails: ""` by default for a Worker
  (`todo-capture`), a Producer (`people-producer`), and an Expert
  (`vault-qa`); a `PATCH` for each field persists across a re-`GET`
  (simulating a reload); editing one agent's own value leaves a sibling
  agent's own stored value completely unchanged (no cross-id bleed).

- feat: `REQ-SB-66-US-01-T06` (`SPRINT-052`) — new, dedicated `GET`/`PATCH
  /agents/{agent_id}/jobs/{job_id}/settings` resource pair in
  `agents_router.py` (`ADR-044` Decision 2) — never a bare top-level
  `/jobs/{job_id}` resource, never a widening of `GET /agents/{agent_id}`
  or `agent_registry.get_agent()`. `agent_id` validates/scopes `job_id`
  against `email_capture_pipeline.get_job_tree()` (the same function `GET
  /agents/{agent_id}/jobs` already calls, itself untouched); the store
  itself is keyed by `job_id` alone via `T01`'s `agent_prompts.py`, no
  special-casing vs. real Agent ids. `GET` returns `{"id", "name",
  "prompt"?, "guardrails"}` — the `"prompt"` key is genuinely OMITTED (not
  `null`) for the 2 Jobs with no real LLM call site of their own
  (`thread_match_merge`, `detect_recurring_pattern`, the disclosed
  `_JOBS_WITHOUT_REAL_PROMPT_CALL_SITE` exclusion set); `"guardrails"` is
  always present. New `JobSettingsUpdateBody` (`prompt`/`guardrails`, both
  optional, omission-means-unchanged); `PATCH`ing `"prompt"` for one of the
  2 excluded Jobs returns `400` rather than being silently stored — the
  disclosed, symmetric edge-case decision this task's own `## Constraints`
  made explicit. This task carries no AC tags of its own; Scenario
  5/6/7/10 (`AC-05`/`AC-06`/`AC-07`/`AC-10`) verify fully once `T07` wires
  the real Job-Settings-only frontend shell against this endpoint — this
  task's own verification is 5 non-AC smoke checks (200/persist,
  omission-not-null, 400-on-excluded-prompt, 404s on unknown agent/job,
  same flat `agent_prompts.json` object real-Agent writes use) confirming
  the endpoint's shape/behavior in isolation, run against the real backend
  and vault.

- feat: `REQ-SB-66-US-01-T07` (`SPRINT-052`) — new, standalone
  `JobSettingsPanel.tsx` component (`ADR-044` Decision 3) and
  `AgentsMapPage.tsx` conditional-mount wiring, so clicking one of the
  Email Capture Pipeline's real Job nodes on the Agents Map now opens a
  real, populated Settings-only view instead of `AgentDetailPanel`'s
  empty, unpopulated 404 shell. `agentsApiClient.ts`: new `JobSettings`
  interface (`prompt` genuinely optional/absent-capable, mirroring `T06`'s
  own omitted-key contract) and `fetchJobSettings`/`updateJobSettings`,
  mirroring `fetchAgent`/`updateAgentAssignment`'s own shape.
  `JobSettingsPanel.tsx`: fetches `GET .../settings` on mount/id-change,
  renders the Job's own real `name` as title, a Settings-only `kv-list`
  with a Prompt row gated on `'prompt' in settings` (key-presence, never
  an empty-string check — genuinely absent, not shown-but-inert, for
  `thread_match_merge`/`detect_recurring_pattern`) and an always-present
  Guardrails row, both committed on blur via `PATCH .../settings`,
  mirroring `T05`'s own `handlePromptCommit`/`handleGuardrailsCommit`
  pattern. No Chat/History/Working-Mode/Schedule/Visual tab or control
  anywhere in the component — no tab bar at all. `AgentsMapPage.tsx`:
  stores the SAME already-fetched `fetchAgentJobs(EMAIL_CAPTURE_PIPELINE_
  AGENT_ID)` list in a new `jobs` state slot (no new fetch), resolves
  `selectedAgentId` against it, and branches the existing
  `{selectedAgentId && <AgentDetailPanel .../>}` conditional mount into
  two: `JobSettingsPanel` for a known Job id, `AgentDetailPanel` unchanged
  for a real Agent id or no match. `AgentDetailPanel.tsx` and
  `AgentsMapCanvas.tsx` received zero edits from this task — the click
  handling stays uniform, only what mounts after a click changes. Verifies
  this story's `AC-05`/`AC-06`/`AC-07`/`AC-10` in the real rendered UI, per
  the parent story's own AC→task mapping. All 7 tasks of `REQ-SB-66-US-01`
  now `Done` — story and `SPRINT-052` both closed `Done`.

- fix: `AgentsMapCanvas.tsx` — a Hub-to-agent connector line was drawn for
  EVERY agent in a Section unconditionally, on top of the real
  dependency-tree edges — meaning every Job in a multi-stage pipeline got
  a redundant direct line back to the Hub in addition to its real line to
  its own predecessor, producing a "starburst" look instead of a clean
  tree. Found live validating `REQ-SB-65`'s real 6-Job tree; operator:
  "All Agents Are Connected to the hub while it should be the last one in
  the Tree," confirmed as root-only. Fixed: an agent now gets a Hub line
  only if it has no incoming dependency edge within its own Section (the
  tree's own root, or — unchanged — a standalone agent with no tree at
  all, which is trivially its own root). Verified live: Data Gathering's
  6 Jobs now show exactly 1 Hub line (`classify`, the real entry point)
  plus the 5 real tree edges; every other Section's standalone agents
  (Productivity, Technology) are unaffected. Total rendered line count
  matches the computed layout exactly (10 = 5 dependency edges + 5 root
  agents across all Sections).

- fix: `layoutAgents.ts::assignTreeAngles`'s `place()` function — a branch
  point's own children were partitioned across the ORIGINAL, un-offset
  `[lo, hi]` angular range instead of a range re-centered on the node's
  own actual (zigzag-offset) drawn position. Any branch reached via an
  odd `zigzagIndex` (a straight-run node pulled off-center before itself
  forking) handed its children a territory centered on a point it was
  never drawn at — visually tearing a fork away from its own parent.
  Found live while visually validating `REQ-SB-65`'s real 6-Job tree
  (`thread_match_merge` forking into `route_to_project`/
  `consult_librarian` looked "all over the place," not a clean fan).
  Fixed by re-centering a same-width window on the node's own placed
  angle before partitioning branch children; single-child straight runs
  are untouched (they deliberately keep a fixed band across the whole
  run, per the function's own existing design). Verified live: the two
  real siblings now fan symmetrically around their real parent's actual
  angle (confirmed via direct computation, not just visual inspection).
  Affects `layoutAgents.ts` generally, not `REQ-SB-65`-specific — any
  future multi-branch Pipeline benefits.

- feat: `REQ-SB-65-US-01-T01` (`SPRINT-051`) — real, read-only Job-tree
  data source for the Email Capture Pipeline. New
  `app/business/pipelines/email_capture_pipeline.py::get_job_tree()`
  reads `_GRAPH.get_graph()` (LangGraph's `Pregel.get_graph()`
  introspection API, `langgraph==1.2.11`) fresh on every call, filters the
  graph's own `START`/`END` sentinel nodes, and returns one
  `{"id", "name", "depends_on"}` entry per real, currently-compiled Job
  node — never a hardcoded Job-name list. New
  `GET /agents/{agent_id}/jobs` in `app/api/agents_router.py` mirrors the
  existing `/history`/`/knowledge-gaps` per-agent sub-resource shape:
  404s for a genuinely unknown agent id, returns the real Job tree (each
  entry carrying a freshly-resolved `section_id`) for
  `email-capture-pipeline`, and `[]` — never fabricated, never a 404 —
  for every other real agent. All 4 locked ACs tagged to this task
  (`AC-02`-`AC-05`) verified live against the real installed `langgraph`
  package and a FastAPI `TestClient`; recorded in the task's own
  Implementation Log. `T02` (frontend splice into the Agents Map) is
  still pending.

- feat (blocked): `REQ-SB-65-US-01-T02` (`SPRINT-051`) — frontend splice
  of `T01`'s real Job tree into the Agents Map. New
  `agentsApiClient.ts::fetchAgentJobs(agentId)` +
  `JobTreeEntry` interface; new pure adapter
  `features/agents-map/pipelineJobTreeAdapter.ts::
  spliceEmailCapturePipelineJobTree(agents, jobs)`; `AgentsMapPage.tsx`'s
  `refreshAgents()` now fetches `/jobs` for `email-capture-pipeline`
  alongside the existing calls and runs the adapter before
  `layoutAgents()` (itself unchanged). Live verification against real
  backend data (isolated Node harness running the actual adapter +
  `layoutAgents()` functions) found `AC-05` passes but `AC-01`/`AC-02`
  fail: the real `email-capture-pipeline` agent is `is_background_agent:
  true`, and `layoutAgents.ts`'s own already-shipped filter
  (`REQ-SB-51-US-01`) excludes every Background Agent from the Agents Map
  ring — inheriting that field verbatim onto the spliced Job entries (this
  task's own locked Constraint) makes every Job invisible too. Task marked
  `Blocked`, not `Done`; parent story `REQ-SB-65-US-01` downgraded
  `Ready → Blocked`; `SPRINT-051` downgraded `In Progress → Blocked`. Full
  writeup: `ESCALATIONS.md` → `ESC-038`; open review item:
  `REVIEW-QUEUE.md` → `REQ-SB-65-US-01-T02`.

- fix: `REQ-SB-65-US-01-T02` (`SPRINT-051`) — ESC-038 resolved,
  `is_background_agent` hardcoded `false` on every spliced Job
  `AgentSummary` entry in `features/agents-map/pipelineJobTreeAdapter.ts`
  (was inherited verbatim from `email-capture-pipeline`, per the
  architect/decomposer's original design). Operator decision, 2026-08-16:
  "Jobs always render, regardless of parent's flag." Every other
  inherited field (`type`/`working_mode`/`icon`/`color`/`description`)
  stays verbatim, unchanged; `email-capture-pipeline`'s own real registry
  flag (still `true`, still shown on `CrawlersPage.tsx`) is untouched —
  scoped to the synthetic Job entries only. Re-verified against real
  backend data (Vite SSR-loaded, unmodified `spliceEmailCapturePipelineJobTree()`
  + `layoutAgents()`): `AC-01` (Data Gathering Section's `mapAgents` now
  holds 6 distinct Job nodes, each inheriting `email-capture-pipeline`'s
  own `type`/`icon`/`color`/`working_mode`), `AC-02` (5 real dependency
  edges present; `classify`/`thread_match_merge` each show 2 outgoing
  edges), `AC-05` (every other Section unaffected), and the empty-`/jobs`
  regression case all pass. `npx tsc -b` shows zero new errors. Task,
  story `REQ-SB-65-US-01`, and `SPRINT-051` all marked `Done`. Full
  writeup: `ESCALATIONS.md` → `ESC-038` (Resolved).

- docs: `/plan-tasks REQ-SB-65-US-01` complete ("Pipeline Job
  Visualization"). Architect resolved the story's own genuinely-open
  data-source question as Option A (a new, read-only endpoint over the
  real, compiled `email_capture_pipeline.py` `StateGraph`, via
  `langgraph`'s already-installed `Pregel.get_graph()` introspection
  API, verified against the installed `langgraph==1.2.11` — no new ADR,
  extends `ADR-043` point 1's own module boundary) and designed the
  concrete `GET /agents/{agent_id}/jobs` route/response shape + frontend
  merge strategy, recorded in `architecture.md` →
  "Pipeline Job Tree Visualization". Decomposer locked all 5 ACs
  (`AC-01`-`AC-05`) and wrote 2 tasks (`T01` backend data source,
  `T02` frontend adapter, acyclic `depends_on: [T01] → [T02]`),
  resolving the architect's one disclosed frontend sub-choice (fetch
  `/jobs` only for the known `email-capture-pipeline` id, not every
  agent) — advancing the story `Draft → Ready`. `gate: flagged`
  (trigger-1) stays set as a standing breadcrumb — the architect's
  concrete endpoint/response-shape/frontend-merge design still awaits
  human confirmation (`REVIEW-QUEUE.md`), per this project's own
  established `REQ-SB-54-US-01`/`REQ-SB-55-US-01`/`REQ-SB-63-US-01`
  precedent that a standing trigger-1 flag does not block `status` from
  advancing. Ready for `/plan-sprints`.

- fix: `GET /agents` (`agents_router.py::list_agents`) — added
  `depends_on: []` and `branch_target_agent_id: null` to every real agent
  in the response. The frontend's `layoutAgents.ts` treats both fields as
  required and calls `.length`/`.map()` on `depends_on` unconditionally;
  the real backend never populated them (only the separate demo-backend's
  synthetic `demo_taxonomy.py` data did), so every real, non-demo agent
  list threw inside the Agents Map's fetch chain, silently caught by its
  own `.catch()`, collapsing the whole map to "0 sections · 0 agents
  mapped" with no console error. Found live while validating `SPRINT-049`/
  `SPRINT-050` against the real backend for the first time this session
  (previously verified mostly against the demo-backend, port 8090).
  Honest empty defaults, not fabricated pipeline-dependency data — no
  real `depends_on` source exists yet in `agent_registry.py`.

- feat: `REQ-SB-63-US-01-T02` (`SPRINT-050`, "The Librarian") — this
  story's/sprint's final task. Added `vault_writer.read_body_section(path,
  header) -> str`, the read counterpart to `replace_body_section` (reuses
  its exact header/next-header location regex, `""` if `header` absent,
  never writes). Added `email_classification.consult_librarian(
  thread_result: dict) -> dict` — the `Consult-Librarian` Job: reads the
  Thread's own `## Summary` via `read_body_section`, calls `T01`'s
  generalized `vault_filing_expert.determine_placement_and_file(...,
  already_filed_path=thread_result["thread_path"])` inside a `try/except`
  that returns an honest `{"status": "unavailable", ...}` on any raised
  exception — never crashes the pipeline. Wired a new `consult_librarian`
  node into `email_capture_pipeline.py`'s compiled `StateGraph`:
  `_route_after_thread_match_merge` now returns a list of destinations
  (`consult_librarian` ALWAYS, `route_to_project` ADDITIONALLY only when
  `created` is `True`, mirroring `_route_after_classify`'s own "always
  this, additionally that" shape) — each destination has its own
  independent fixed edge to `END`, so Consult-Librarian structurally never
  gates Route-to-Project. Verified live end-to-end against a `tempfile.
  mkdtemp()` scratch vault (`VAULT_PATH` env-overridden), a scoped
  `model_factory` stub for the Librarian's own model call: a grounded
  Tier-1 "linked" decision (`AC-01`), a real `[[wikilink]]` hub-link
  landing on the already-filed Thread note (`AC-02`), Provider-unavailable
  honesty flowing through both a direct call and the graph's own node
  wrapper with `Route-to-Project` still firing independently (`AC-05`),
  and a grep-confirmed regression that `classify_recent_emails`/`REQ-SB-08`
  /`09`/`10`'s modules are untouched (`AC-06`). **This closes
  `REQ-SB-63-US-01` and `SPRINT-050`** — all 3 tasks (`T01`-`T03`) `Done`,
  all 6 locked ACs verified; `BACKLOG.md`'s `REQ-SB-63` row and the
  `SPRINT-050` Sprint Status row both set to `Done`; the sprint's own
  Retrospective drafted, `gate: flagged` for the human retro-harvest,
  carrying forward the still-open architect-designed-write-shape review
  item too. See `MEMORY.md` `[2026-08-16] REQ-SB-63-US-01-T02` for full
  detail.

- feat: `REQ-SB-63-US-01-T03` (`SPRINT-050`, "The Librarian") — added
  `vault_filing_expert.finalize_cross_cutting_update(payload) -> dict`,
  the deferred-write half of `T01`'s `propose_cross_cutting_update`
  Pending Approval: unions an additive `customer/<slug>`/`partner/<slug>`
  tag into the already-filed note's own existing `tags` (idempotent, no
  tag lost or duplicated), via `vault_writer.upsert_frontmatter_key`
  (`REQ-SB-55-US-01-T01`) — never touches `captures.md` (`ADR-042`).
  Registered `"propose_cross_cutting_update": vault_filing_expert.
  finalize_cross_cutting_update` in `pending_approvals_router.py`'s
  `_APPROVAL_HANDLERS` (additive entry, 4 pre-existing entries
  unaffected). Verified live against a temp scratch vault. See
  `MEMORY.md` `[2026-08-16] REQ-SB-63-US-01-T03` for full detail.

- feat: `REQ-SB-63-US-01-T01` (`SPRINT-050`, "The Librarian") —
  generalized `vault_filing_expert.determine_placement_and_file` with an
  additive, keyword-only `already_filed_path: str | None = None` param
  (skips `vault_writer.write_note` for a Tier-1 decision, links the
  already-filed note instead, returns `"status": "linked"`) and an
  additive `cross_cutting_implication` field on the model's own JSON
  placement decision (`vault_filing_methodology.py`), re-checked in
  Python against the same pre-fetched `known_customers`/`known_partners`
  lists via a new `_maybe_create_cross_cutting_proposal` helper. A new
  `_create_cross_cutting_proposal` (mirroring `_create_tier_2_proposal`'s
  shape) creates a `propose_cross_cutting_update` Pending Approval
  whenever a valid, different-entity cross-cutting implication is
  detected; the return dict gains an additive `"cross_cutting_approval_
  id"` key when one was created. All 3 pre-existing callers unaffected.
  Verified live against the real vault with a monkeypatched, engineered
  model reply. See `MEMORY.md` `[2026-08-16] REQ-SB-63-US-01-T01` for
  full detail.

- feat: `REQ-SB-55-US-01-T08` (`SPRINT-049`, `ADR-043`) — retired
  `email-capture`; registered `email-capture-pipeline`. Replaced the
  former single-stage `email-capture` Agent-tier identity 1:1 with a
  genuinely new id, `email-capture-pipeline` (`type: "worker"`, same
  type, same three real Actions), across every real referencing file:
  `agent_registry.py` (`_SEED_AGENTS`, settings rewritten to describe the
  real Job chain), `background_agent_registry.py`
  (`_DEFAULT_BACKGROUND_AGENT_IDS`), `skill_tools.py` (`run_capture_now`'s
  handler), `skill_registry.py` (the 3 migrated-grant lists),
  `agents_router.py` (`_ACTION_HANDLERS`), and `email_classification.py`
  (`run_capture_for_agent` now dispatches
  `"email-capture-pipeline"` to `pipelines.email_capture_pipeline.
  run_email_capture_pipeline` — via a deferred, in-branch import to avoid
  a circular import with `T07`'s own pipeline module — instead of the
  retired `classify_recent_emails`; `run_capture_and_record_completion`'s
  own gating/history/error-handling shape is unchanged, only the id
  string and underlying dispatched function changed). Also renamed
  `demo_taxonomy.py`'s coincidentally-matching, disconnected demo-fixture
  id `"pipeline-email-capture"` → `"pipeline-inbound-email-demo"` to
  avoid reader confusion with the new real identity. `classify_recent_
  emails`/`record_conversation_note`/`find_related_note_stems` are now
  dead code for this path but deliberately left in place — still called
  directly by `app/api/email_poc_router.py`'s own standalone
  `/poc/classify-emails` manual endpoint. Verified live: `agent_registry.
  get_agent("email-capture")` now returns `None`; `GET /agents` shows
  `email-capture-pipeline` (`type: "worker"`), never the retired id
  (`AC-08`). A real, live, non-mocked Outlook-backed capture run against
  the real configured mailbox/vault produced a correct real Thread note
  (real frontmatter/`## Summary`/`## Transcript`) and a correct, real,
  genuinely-derived `route_thread_to_project` Pending Approval (`AC-09`);
  `meeting-capture`/`todo-capture` ran unaffected in the same real tick.
  This is the story's own final task — `REQ-SB-55-US-01` and
  `SPRINT-049` both close `Done` on this task's completion.

- feat: `REQ-SB-55-US-01-T07` (`SPRINT-049`, `ADR-043`) — Pipeline
  assembly. New `app/business/pipelines/` subpackage (this codebase's
  first Pipeline-DAG-assembly module): `app/business/pipelines/
  email_capture_pipeline.py` wires `T02`-`T06`'s 5 plain, LangGraph-
  ignorant Job functions into a compiled `langgraph.graph.StateGraph`
  (`classify` fork point → mandatory `summarize_attachment` pass-through
  node, looping 0-or-more times over real attachments, with one fixed
  edge straight into `thread_match_merge` — the structural fan-in
  guarantee — → conditionally `route_to_project` only when `thread_
  match_merge`'s own `created` is `True`; `detect_recurring_pattern`
  branches off `classify` in parallel, independently, when `recurring_
  candidate` is set, and terminates on its own, never feeding back into
  `thread_match_merge`). No `MemorySaver`/`SqliteSaver`/`interrupt()`
  anywhere — both approval-creating Jobs run to a clean, ordinary
  completion on every invocation, per `ADR-043` point 4. New public entry
  point `run_email_capture_pipeline(limit=10) -> list[dict]`: a pre-graph,
  per-tick `Fetch` batch loop (`outlook_com.list_recent_mail`, unchanged)
  invokes the compiled graph once per new (not-already-processed) email;
  a per-email failure is caught at this loop level (never inside the
  graph), leaving the failed email unmarked (retry-eligible) while every
  other fetched email in the same tick is still processed normally.
  Verified live end-to-end (scratch vault, real Compass Provider, only
  `outlook_com.list_recent_mail` monkeypatched): `AC-01` (two real
  messages in one conversation collapse into exactly one Thread note,
  `## Transcript` grows, `## Summary` regenerates with zero residue of
  the first message); `AC-04` (a real call-count spy around the real
  `route_to_project` confirms it fires exactly once across both messages
  — never on the second, already-routed one); fan-in ordering (a real
  attachment's `summarize_attachment` result is confirmed present and
  correctly populated on `thread_match_merge`'s own call); per-email
  failure isolation (a real, scoped, reverted `CompassError` induction on
  one of two fetched emails leaves 1 honest error result + 1 real
  successful result, never aborting the tick); dedup rerun (zero new
  Thread notes/approvals on a rerun of already-processed ids).

- feat: `REQ-SB-55-US-01-T06` (`SPRINT-049`, `ADR-043`) —
  `Detect-Recurring-Pattern` branch Job. New
  `email_classification.detect_recurring_pattern(email, classification) ->
  dict | None`: no-ops (`None`) when `classification["recurring_candidate"]`
  is falsy; otherwise creates exactly one Pending Approval
  (`agent_id="email-capture-pipeline"`, `trigger="direct"`,
  `action_id="propose_recurring_pipeline"`) proposing a NEW standing
  Pipeline, with a payload shaped to match `agents_router.py`'s real
  `CreateAgentBody` contract (`name`, `type: "worker"`, `purpose`) —
  genuinely derived from the triggering email's own subject/customer/kind,
  plus a `seed_source` sub-dict carrying the raw email fields. New
  `pending_approvals_router.finalize_recurring_pipeline_proposal(payload)
  -> dict`, wired into `_APPROVAL_HANDLERS["propose_recurring_pipeline"]`
  — a deliberately minimal acknowledgment on Approve
  (`{"message": "Approved — seed data ready. Open the Agent Creation
  Wizard to complete the new Pipeline."}`) that never calls
  `agent_registry.create_agent` or any other agent-creation code path on
  any branch; actually creating the new Pipeline stays the operator's own
  separate, manual completion of the existing Agent Creation Wizard
  (`REQ-SB-37`, `Done`). Verified live (manual mode, scratch vault, real
  Compass Provider, reusing `T02`'s own two structurally-different real
  test fixtures): both a Weekly-Usage-Report-shaped email and an
  Invoice-shaped email from an unrelated customer independently produce
  one correctly-seeded Pending Approval each via the same code path
  (`AC-05`/`AC-06`); an ordinary conversational email produces no
  approval; both records use `trigger="direct"`; a real Approve call
  confirms the minimal outcome message and confirms
  `agent_registry.list_agents()`'s own count is unchanged before/after.

- feat: `REQ-SB-55-US-01-T05` (`SPRINT-049`, `ADR-043`) — `Summarize-Attachment`
  branch Job. New `email_classification.summarize_attachment(attachment,
  conversation_id, received) -> dict`: saves the ONE attachment via
  `vault_writer.write_attachments(subfolder="Work/Threads",
  note_stem=conversation_id, ...)` (`Work/Threads/attachments/
  <slug-of-conversation_id>/`); if saved, extracts text by composing
  `REQ-SB-28-US-01`'s own `upload_storage.save_upload`/
  `extract_text_content`/`delete_upload` directly against the attachment's
  own in-memory bytes (the same temporary-save-then-extract-then-delete
  technique `REQ-SB-44-US-01`'s `cockpit/attachments.py` already
  established), then summarizes via `compass_client.summarize_content`
  directly. Returns `{"filename", "saved", "relative_link" (if saved),
  "dated_entry" (if summarized), "summary_error" (if unsaved/
  non-text-bearing/a real `CompassError`)}` — never fabricates, never
  raises; the resulting `dated_entry` is a dated sub-entry string kept
  structurally separate from the Thread's regenerated `## Summary` (never
  calls `replace_body_section`), fed into `thread_match_merge`'s own
  `attachment_entries` parameter by `T07`'s future pipeline wiring, not by
  this function itself. Verified live (manual mode, scratch vault, real
  Compass Provider): a real `.txt` attachment produces a genuine, dated
  sub-entry accurately reflecting its own content (`AC-02`); a deliberately
  oversized attachment (content already `None` per Outlook's own upstream
  size cap) reports `saved: False` with an honest `summary_error`, no
  fabricated `dated_entry`; a real, scoped, reverted-after
  `compass_client.summarize_content` monkeypatch confirms a real
  `CompassError` is caught and honestly reported (`summary_error`), never
  raised uncaught; direct reading confirms the function never calls
  `replace_body_section`/`thread_match_merge`.

- feat: `REQ-SB-55-US-01-T04` (`SPRINT-049`, `ADR-043`) — `Route-to-Project`
  Job. New `email_classification.route_to_project(thread_result,
  classification, email) -> dict | None`: no-ops when
  `thread_result["created"]` is `False` (Scenario 4/`AC-04`'s own defensive
  half); for a brand-new Thread, filters `vault_writer.list_customer_projects`
  to currently-open (`status == "active"`) Projects, asks the new
  `compass_client.guess_project_for_thread(thread_summary, open_projects) ->
  {"project", "confidence"}` to pick the best-fitting name or propose a new
  one, and ALWAYS creates a Pending Approval (`trigger="direct"`, never
  `"background"` — a single pipeline tick can produce multiple distinct
  routing proposals) with `action_id="route_thread_to_project"` and a payload
  naming the Thread's own path, the guessed Project, and whether it's new —
  never auto-commits the Thread's own `project` frontmatter key (Scenario 3/
  `AC-03`). New `finalize_thread_project_routing(payload) -> dict`
  (`email_classification.py`, mirroring `vault_filing_expert.
  finalize_new_top_level_area`'s own payload-driven deferred-write shape):
  creates the new Project directory first when proposed, then sets the
  Thread's `project` key via `upsert_frontmatter_key`, returning
  `{"path", "message"}`. Registered as `pending_approvals_router.py`'s third
  `_APPROVAL_HANDLERS` entry (`"route_thread_to_project"`); the Approve
  endpoint's own `outcome_message` construction is now additive
  (`result.get("message") or f"Approved — filed at {result['path']}."`) so a
  handler may supply its own outcome text — confirmed live that both
  pre-existing handlers (which return no `"message"` key) are unaffected.
  Verified live (manual mode, scratch vault, real Compass Provider): a
  Customer with a real open Project produces exactly one Pending Approval
  naming it, the Thread's `project` key stays absent until Approve, then
  reads back correctly; a Customer with zero open Projects produces a
  new-Project proposal, and Approve both creates the real Project directory
  and sets the Thread's `project` key; a `created=False` call is a confirmed
  true no-op (no new Pending Approval); both records confirmed
  `trigger="direct"`; the pre-existing `propose_new_top_level_area` handler's
  outcome text reconfirmed byte-for-byte unchanged. No `ESCALATIONS.md`
  entries; one scope-internal judgement call (handler's business-layer home)
  logged in the task's own Implementation Log.
- feat: `REQ-SB-55-US-01-T03` (`SPRINT-049`, `ADR-043`) — `Thread-Match/Merge`
  Job. New `email_classification.thread_match_merge(email, classification,
  attachment_entries=None) -> dict`: on the FIRST message of a
  `conversation_id`, creates the Thread note
  (`vault_writer.create_thread_note_baseline`) and writes its `customer`
  frontmatter key once (never again on a later message); on EVERY call,
  unions this message's own `build_tags(customer, kind)`-derived tags onto
  the Thread's current tags (read-union-write, never pruning), accumulates
  the sender into `participants`, unconditionally overwrites
  `last_message_at`, grows `## Transcript` by one dated entry
  (`T01`'s `append_body_section_line`), folds any `attachment_entries` into
  `## Attachments` (left untouched when none), and fully regenerates `##
  Summary` (`replace_body_section`, REQ-SB-54's "regenerate, don't patch"
  invariant) from a deterministic, non-LLM rendering of the latest message
  only. Calls `customer_hub_linking.ensure_customer_hub_note(customer)`
  only — never the inline `**Customer:** [[Hub]]` wikilink convention.
  Returns `{"thread_path", "created", "conversation_id", "customer"}` —
  `created` is the signal `T07`'s pipeline wiring uses to decide whether
  `Route-to-Project` fires. Verified live (manual mode, scratch vault): a
  brand-new conversation produces exactly one Thread note with correct
  baseline frontmatter and a real `## Summary`; a second message in the
  SAME conversation resolves to the identical path, regenerates `##
  Summary` with zero residue of the first message's own wording, and
  grows `## Transcript` in call order (`AC-01`); an attachment sub-entry
  lands in its own `## Attachments` region, kept separate from `##
  Summary` (`AC-02`); tags union across a kind change with one genuinely
  new tag and one overlapping tag, nothing previously present removed
  (`AC-07`); `participants` accumulates all 3 distinct senders and
  `last_message_at` reflects the most recent message. No
  `ESCALATIONS.md`/`REVIEW-QUEUE.md` entries — two scope-internal
  judgement calls logged inline in the task's own Implementation Log.
- feat: `REQ-SB-55-US-01-T02` (`SPRINT-049`, `ADR-043`) — `Classify` Job
  extended with a general, structural recurring-pattern-candidate signal.
  `compass_client.classify_email`'s prompt gained a third JSON axis,
  `recurring_candidate: <true/false>`, worded to reason about structure/
  repetition (consistent layout, labeled fields, tabular/itemized data)
  rather than any specific customer or format — response-parsing gained the
  matching additive `"recurring_candidate": bool(parsed.get(...))` key,
  `customer`/`kind`/`confidence` unchanged. New
  `email_classification.classify_captured_email(email, known_customers,
  known_kinds) -> dict` — a thin, LangGraph-ignorant wrapper (this
  Pipeline's own `Classify` Job, `ADR-043` point 1), exactly one Compass
  call, no vault write, no Pending Approval. Verified live against the real
  Compass Provider: a synthetic weekly-usage-report email and a
  structurally different invoice-shaped email from an unrelated fictitious
  customer both correctly flagged `recurring_candidate: True` via the SAME
  mechanism (`AC-06`), an ordinary conversational email flagged `False`,
  the wrapper confirmed to make exactly 1 Compass call via a call-count spy,
  and `customer`/`kind`/`confidence` regression-checked unaffected. No
  `ESCALATIONS.md`/`REVIEW-QUEUE.md` entries.
- feat: `REQ-SB-55-US-01-T01` (`SPRINT-049`, first task of the Email Capture &
  Threading Pipeline, `ADR-043`) — two new `vault_writer.py` primitives:
  `append_body_section_line(path, header, line)` (header-scoped, growing
  body-section append — reuses `replace_body_section`'s own header/next-
  header location logic, generalized to insert-before-region-end instead of
  full-region replace; creates a missing header at end-of-file on first use,
  unlike `replace_body_section`'s own no-op-if-absent contract) and
  `list_customer_projects(customer) -> list[dict]` (enumerates one
  Customer's own `projects/*/` subdirectories, returning `{"project",
  "slug", "status"}` read directly from each Project's own concept-file
  frontmatter, `[]` if none exist yet). The task's third named primitive
  (an unconditional frontmatter-key setter) turned out to already exist as
  `vault_writer.upsert_frontmatter_key` (`REQ-SB-09-US-01-T01`) — reused
  as-is rather than duplicated; see `MEMORY.md`/the task's own
  Implementation Log for the full judgement-call reasoning. Verified live
  (manual mode, scratch vault): growing-append call-order and header-
  creation behavior, unconditional-setter insert/overwrite behavior, and
  `list_customer_projects`' `[]`-then-2-real-entries behavior all confirmed;
  `ast.parse()` clean, no pre-existing function altered.
- feat: `REQ-SB-54-US-01-T06` (`SPRINT-048`, last task) — `vault_writer.
  list_all_note_paths()` extended to discover the new two-levels-deep
  Customer/Project OKF concept files (the flagged `architecture.md`
  Consequence). New module-level `_OKF_RESERVED_FILENAMES = {"index.md",
  "log.md", "captures.md"}` constant; the function now unions the existing
  one-level `Work/*/*.md` glob (unchanged) with two additional, deliberately
  hardcoded globs — `Work/Customers/*/*.md` and `Work/Customers/*/projects/
  */*.md` — filtered to exclude the OKF-reserved filenames, then returns the
  sorted union. Deliberately NOT generalized to detect any directory-shaped
  kind dynamically, per `ADR-042`'s own explicit 2-kind (Customer/Project)
  scope. No other discovery function touched (`list_known_kinds`,
  `list_notes_in_kind_folder` unchanged). Verified live (manual mode,
  scratch vault): every previously-discoverable flat note kind unaffected
  (same set/count, zero drops/duplicates), both a real Customer and a real
  nested Project concept file discovered, their own `index.md`/`log.md`/
  `captures.md` correctly excluded, and `list_known_customers()` confirmed
  unaffected by the new concept files (they carry no plain `customer:`
  frontmatter key). **This completes `REQ-SB-54-US-01` — all 6 tasks
  (`T01`-`T06`) `Done`, all 5 locked ACs verified; story and `SPRINT-048`
  both closed `Done`.** See `MEMORY.md` for the consolidated story-level
  entry and `Implementation/Sprints/SPRINT-048-vault-knowledge-model-
  redesign.md`'s own Retrospective.
- feat: `REQ-SB-54-US-01-T05` (`SPRINT-048`) — Project directory-shaped note
  kind added to `vault_writer.py` (`ADR-042` point 4), nested one level
  inside its own Customer's directory. New thin wrappers
  `project_directory_paths(customer, project)`,
  `project_concept_file_exists(customer, project)`,
  `build_project_concept_frontmatter(customer, project)`,
  `create_project_directory_baseline(customer, project)`,
  `ensure_project_directory_baseline(customer, project)`, all delegating to
  `T04`'s generic `okf_directory_paths`/`okf_concept_file_exists`/
  `create_okf_directory_baseline`/`ensure_okf_directory_baseline`/
  `format_okf_provenance` family — zero duplicated 4-file-creation logic. A
  Project's own directory root is always
  `customer_directory_paths(customer)["directory"] / "projects"`, computed
  via a small private `_project_directory_root(customer)` helper (never a
  separately-hardcoded path string), so a Project sits at
  `Work/Customers/<customer>/projects/<project>/`, containing the identical
  `index.md`/`<project-slug>.md`/`log.md`/`captures.md` shape as a Customer
  directory. Frontmatter mirrors Customer's own field set exactly, only
  `tags` differs (`["customer/<tag-slug>", "kind/project"]`, so a Project
  stays findable both by its own kind and by its parent Customer). Verified
  live (manual mode, scratch vault): directory/concept-file creation,
  `captures.md` structurally unreachable from `## Glimpse`-section
  regeneration, and idempotent top-up via `ensure_project_directory_
  baseline` all confirmed. No new business-layer orchestration module —
  this task builds the data_access-layer primitives only (no real caller
  classifies content into Projects yet).
- feat: `REQ-SB-54-US-01-T04` (`SPRINT-048`) — generic directory-shaped OKF
  note-kind primitive family added to `vault_writer.py` (`ADR-042` point 1),
  applied to Customer. New generic primitives: `okf_directory_paths
  (directory_root, slug)` (deterministic `index.md`/`<slug>.md`/`log.md`/
  `captures.md` path set, mirroring `hub_note_path`/`meeting_note_path`'s
  own precedent), `okf_concept_file_exists`, `create_okf_directory_baseline`
  (whole-file `index.md`, `<slug>.md` via the new `_write_frontmatter_note`
  helper with a body of exactly empty `## Glimpse`/`## Background`
  sections, `log.md`/`captures.md` created empty only if missing), and
  `ensure_okf_directory_baseline` (surgical top-up of concept frontmatter
  via the existing `insert_frontmatter_key_if_missing`, never touches an
  already-present key or the body; `log.md`/`captures.md` never truncated
  if present). New `format_okf_provenance(by, at)` JSON-encodes the OKF
  `generated`/`verified` actor-provenance dict under its own literal field
  name (`ADR-042` point 3), extending the existing Meeting `attendees`/
  Email `recipients` workaround. `write_note`'s own inline frontmatter
  logic was extracted into a private `_write_frontmatter_note(path,
  frontmatter, body)` helper, shared by `write_note` and the new directory
  family — behavior-preserving, verified byte-identical output. Customer
  application: `customer_directory_paths`/`customer_concept_file_exists`/
  `build_customer_concept_frontmatter`/`create_customer_directory_
  baseline`/`ensure_customer_directory_baseline` thin wrappers around the
  generic family, at `Work/Customers/<slug>/`. `customer_hub_linking.
  ensure_customer_hub_note` restructured to build/top-up the new directory
  shape internally — its own external contract (`{"hub_note_path": str,
  "created": bool}`) is byte-identical, so all 5 real call sites
  (`email_classification.py`, `meeting_classification.py`,
  `people_extraction.py`, `todo_classification.py`,
  `vault_filing_expert.py`) needed zero changes. `link_note_to_customer_
  hub`/`ensure_hub_note_and_link`/`retrofit_customer_hub_links` are
  unmodified (diff-confirmed). `vault_writer.hub_note_path`/
  `hub_note_exists`/`create_customer_hub_note_baseline`/`ensure_hub_note_
  baseline_frontmatter`/`_HUB_NOTE_BASELINE_KEYS` and
  `app/business/partner_hub_linking.py` are byte-for-byte unmodified
  (diff-confirmed) — `partner_hub_linking.migrate_customer_to_partner`'s
  own dependency on the old flat-file primitives is untouched, per
  `ADR-042`'s own out-of-scope Alternatives. Verified live (manual mode,
  real backend venv, scratch vault dir): fresh directory creation produces
  all 4 files with the required concept-file frontmatter keys and exactly
  the two `## Glimpse`/`## Background` sections; a manual append to
  `captures.md` survives byte-for-byte across a subsequent `replace_body_
  section` regeneration of `## Glimpse` (captures.md is structurally
  unreachable from that code path); a business-layer `ensure_customer_hub_
  note` rerun on the same customer is a true no-op top-up (`created:
  False`, no frontmatter/body change); the old flat `hub_note_path`
  resolves to a path that was never created by this task and
  `partner_hub_linking.py` shows zero diff; `ensure_hub_note_and_link`
  against a Person note links on the first call and is idempotent on the
  second, with the inline wikilink correctly resolving to the new concept
  file's identical filename stem; `create_meeting_note_baseline`'s raw
  file output is unchanged after the `_write_frontmatter_note` extraction.
  All 6 manual Test steps `PASS`. Task marked `Done`.
- feat: `REQ-SB-54-US-01-T02` (`SPRINT-048`) — Thread note kind added to
  `vault_writer.py` (`ADR-042` point 5): `thread_note_path(conversation_id)`
  (pure, deterministic — `Work/Threads/<slug-of-conversation_id>.md`, no
  separate lookup index, mirrors `hub_note_path`/`meeting_note_path`),
  `thread_note_exists`, `create_thread_note_baseline(conversation_id,
  tags=None)` (baseline frontmatter `type`/`conversation_id`/`tags` plus a
  body of exactly an empty `## Summary` followed by an empty
  `## Transcript`), and `ensure_thread_note_baseline_frontmatter` (surgical
  top-up of the same three keys via the existing
  `insert_frontmatter_key_if_missing`, same no-op-when-already-present
  contract as every other note kind). Callers regenerate `## Summary` via
  `T01`'s `replace_body_section` and grow `## Transcript` via the existing
  `append_person_note_update_line` directly — no new wrapper primitive
  added, per `ADR-042`'s "one shared mechanism" principle.
  `conversation_index.json`/`find_related_note_stems`/
  `record_conversation_note`/`email_classification.py` were not touched —
  still owned by `REQ-SB-55`. `list_known_kinds()` needed zero code
  change — `Work/Threads/` is discovered dynamically, confirmed live.
  Verified live (manual mode, real backend venv, scratch vault dir): first
  creation for a `conversation_id` produces exactly one note at the
  deterministic path with the empty two-section body; a second resolution
  of the same `conversation_id` returns the identical path (no new file);
  `replace_body_section` + `append_person_note_update_line` against that
  path regenerate `## Summary` in full and grow `## Transcript` while the
  frontmatter block stays byte-for-byte unchanged; `ensure_thread_note_
  baseline_frontmatter` on the same already-complete note is a true
  no-op (`inserted == []`, file byte-for-byte unchanged); `Threads` shows
  up in `list_known_kinds()`. All 4 manual Test steps `PASS`. Task marked
  `Done`.
- feat: `REQ-SB-54-US-01-T03` (`SPRINT-048`) — Meeting note baseline
  frontmatter schema gains one additive, currently-empty `thread` field
  (`ADR-042` point 6), reserved for `REQ-SB-56`'s own future
  Meeting→Thread linking — not populated by this task. `_MEETING_NOTE_
  BASELINE_KEYS` extended from 8 to 9 keys; `create_meeting_note_baseline`
  now writes `thread: ""` unconditionally on every new Meeting note;
  `ensure_meeting_note_baseline_frontmatter` tops up `thread: ""` on any
  already-existing Meeting note missing it, via the existing surgical
  `insert_frontmatter_key_if_missing` (never touches an already-present
  key). Both function signatures are unchanged, so `meeting_classification.
  py`'s two real call sites need zero edits. Verified live (manual mode):
  a freshly created Meeting note carries `thread: ""` alongside the other
  8 baseline keys; a simulated pre-task Meeting note (no `thread` key) is
  topped up with `inserted == ["thread"]`, every other frontmatter line
  and the body byte-for-byte unchanged. Task marked `Done`.
- feat: `REQ-SB-54-US-01-T01` (`SPRINT-048`) — new
  `vault_writer.replace_body_section(path, header, new_content)`
  primitive, the foundation `T02`/`T04`/`T05` build on (`ADR-042` point
  2). Locates a `##`-level header by an exact, literal line match on
  every call (never a cached/computed byte offset — the fixed-frontmatter-
  offset fragility `insert_body_line_if_missing` already carries,
  `MEMORY.md`, `BUG-003`/`ESC-003`) and replaces everything strictly
  between it and the next `##`-level header (or end of file) wholesale —
  a nested `###`+ subheader inside the same section is not a boundary.
  Returns `False`/no-op if `header` isn't found; never raises, never
  creates the section. Purely additive — every other `vault_writer.py`
  primitive is untouched. Verified live (manual mode) against all 3
  Test steps for `REQ-SB-54-US-01-AC-04`: first-call replace, second-call
  regeneration on the same already-touched file (no positional drift),
  last-section-extends-to-EOF, and the not-found no-op contract — all
  `PASS`. Task marked `Done`; `T02`/`T04`/`T05` are now unblocked.
- feat: `/plan-tasks REQ-SB-54-US-01` complete — architect wrote `ADR-042`
  (directory-based OKF v0.2 note-kind family for Customer/Project, a new
  `replace_body_section` header-scoped regeneration primitive, Thread
  notes keyed by `conversation_id`); decomposer locked 5 ACs and wrote 6
  tasks (`T01`-`T06`, acyclic `depends_on`), advancing the story to
  `Ready`. Operator reviewed and approved `ADR-042` with no changes —
  `gate:` reset to `clear`, `REVIEW-QUEUE.md` entry (and its orphaned
  decomposer addendum, now fully preserved in the story's own `## Notes`)
  removed. Ready for `/plan-sprints`.
- docs: `REQ-SB-54-US-01`'s last open flag resolved — operator, direct
  confirmation: "Yes, Project gets the same directory shape as Customer."
  Project gets the identical OKF-conformant four-file shape as Customer.
  This was the final one of three MUST-FLAG triggers this story raised;
  all three are now resolved and its `gate:` flips from `flagged` to
  `clear` — ready for `/plan-tasks`. `ESCALATIONS.md` → `ESC-037` closed
  (`Resolved`), its `REVIEW-QUEUE.md` entry removed, `BACKLOG.md` updated.
- docs: Adopted Google Cloud's Open Knowledge Format (OKF v0.2, published
  June 2026) as the concrete frontmatter/file-structure standard for
  `REQ-SB-54`'s Project/Customer synthesis layer — operator: "Files now
  in the KB will contain a OKF Standard Front matter and a quick Summary
  in the beginning as a start of the file to know what's inside."
  Researched the real spec (not guessed from the name) via
  `github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md`.
  Customer and Project are now each a small OKF-conformant DIRECTORY, not
  a single file — `index.md` (OKF-reserved directory listing), `<slug>.md`
  (the OKF concept file: `type`/`title`/`description`/`tags`/`status`/
  `stale_after`/`generated`/`verified`/`sources` frontmatter, Glimpse +
  Background body), `log.md` (OKF-reserved, History — append-only by
  being a separate file, not just convention), `captures.md` (same
  principle, not OKF-reserved but structurally isolated the same way).
  OKF's `generated`/`verified` actor fields turn out to formalize the
  exact agent-proposes/operator-approves pattern already designed
  throughout this batch; `stale_after` gives a real mechanism for the
  root pain ("I can't find the current status of anything") to surface
  staleness explicitly. Threads/Meetings stay flat (not nested under
  Customer/Project directories), extending this vault's own
  already-established "Customer is never a folder level" rule
  (`REQ-SB-14`, `MEMORY.md`) to Project too — cross-linked via
  frontmatter instead of physical placement, so a routing correction
  never requires a file move. Also added a working-default (flagged, not
  operator-confirmed) convention: every KB file's body opens with a
  one-line current-state summary, separate from OKF's own `description`
  frontmatter field, since frontmatter is often collapsed at a glance in
  Obsidian. Updated `Documentation/PRD.md` (`REQ-SB-54` points 4/5/7/8/11,
  `REQ-SB-57`'s synthesizer description), `REQ-SB-54-US-01`'s story
  (Context pointer note + Scenario 3), and `BACKLOG.md`.
- docs: Resolved `REQ-SB-54` point 10 (`ConversationID` under-merging) by
  scope split rather than by designing a merge heuristic under time
  pressure — operator: "I guess we keep threads as is and then we will
  need to have an entity called Conversation where thread is the raw
  data, then we will handle the data in the KB later." Added
  `REQ-SB-60: Conversation — Merging Related Threads into One Real
  Exchange` (`Documentation/PRD.md`, P2) as a deliberate placeholder — not
  spec'd, explicitly deferred until `REQ-SB-55` has real capture history
  to design the merge logic against. Thread (`REQ-SB-54`) and
  Thread-Match/Merge (`REQ-SB-55`) both revert to their original,
  fully-specced shape (one note per `ConversationID`, no merge logic) —
  fully un-blocked. `REQ-SB-54-US-01`'s `gate: flagged` narrows to a
  single remaining item (Project's own Background/History/Glimpse split,
  still awaiting operator confirmation). `BACKLOG.md`/`REVIEW-QUEUE.md`
  updated to match.
- docs: Live-verified two of `/spec`'s open technical questions for the
  KB redesign batch (read-only Outlook COM checks, no vault writes): (1)
  mail `ConversationID` false-merge risk — clear, no genuine collision
  across 41 real multi-message threads; (2) meeting-item `ConversationID`
  exposure — confirmed present and non-empty on 100/100 sampled calendar
  items (existing code just never reads it). Recorded in
  `REQ-SB-54-US-01`/`REQ-SB-56-US-01`'s own `## Notes`, `REVIEW-QUEUE.md`,
  and `BACKLOG.md`. **Then corrected same-day** — operator: "The
  ConversationID is not the only link, sometimes different emails with
  different ConversationID are linked to the same thread." The false-merge
  check only tested one failure direction; a real conversation can span
  MULTIPLE `ConversationID`s that Outlook itself never merges (edited
  subject lines, forwards into new recipient sets, a fresh email restarting
  an old topic). Added this as `REQ-SB-54` point 10 (PRD, story, and
  `REQ-SB-55`'s own `Thread-Match/Merge` Job description) — a secondary
  merge signal is required and not yet designed; `conversation_id`-only
  Thread matching is explicitly documented as a known-incomplete v0
  behavior until it lands. Re-opened `REQ-SB-54-US-01`'s trigger-8 flag on
  this new axis (the false-merge half stays resolved).
- docs: Drafted 6 new PRD requirements (`REQ-SB-54` through `REQ-SB-59`,
  `Documentation/PRD.md`) covering the KB knowledge-model redesign
  worked out over an extended design discussion: a Threads/Meetings/
  Manual-Captures evidence layer feeding always-current Project/Customer
  status documents (Background/History/Glimpse/Captures), a rebuilt
  Email Capture & Threading pipeline (supersedes `REQ-SB-53-US-01`) with
  approval-gated Project routing and a general "this looks like it wants
  its own Pipeline" detector, Meeting-to-Thread linking (supersedes
  `REQ-SB-53-US-02`), the Project/Customer synthesizer agents that keep
  those status documents honest, a Glimpse-first extension to `vault-qa`,
  and a full wipe-and-recapture migration. `BACKLOG.md` updated with all
  6 rows plus `REQ-SB-53`'s own row corrected to point at what supersedes
  it (To-Do/`US-03` stays parked, out of this batch).
- fix: The click-to-focus center+zoom (above) centered the Agent on the
  canvas's own literal 50%, landing it BEHIND the AgentDetailPanel —
  operator: "now the Agent is in the Center Behind the Panel not
  between the panel and Side Bar." `.side-panel` (agent-panel.css) is a
  `position: fixed; right: 0; width: min(560px, 100vw);` overlay that
  opens as PART OF the exact same click that focuses the Agent, so it's
  always covering the canvas's own right edge whenever this treatment
  is active — the canvas's own center is no longer the visual center of
  the space actually left over. Added a `useEffect` (SectionDrilldown.tsx)
  that measures the free gap between the canvas's own left edge and the
  panel's left edge (`window.innerWidth - panelWidth`), converts it to
  a canvas-relative X percentage, and targets THAT instead of a literal
  50 (Y stays 50 — a right-side panel doesn't affect vertical
  centering). Caught a real measurement bug along the way: the first
  attempt read `canvasEl.getBoundingClientRect()`, which reports the
  already-transformed (post 3x-zoom) box once focused, not the natural
  one the percentage math needs — switched to `.agents-map-stage`'s own
  rect (never gets the focus transform) combined with the canvas's
  `offsetLeft`/`offsetWidth` (also transform-immune), which stays
  correct regardless of whatever transform is currently live. Verified
  live: expected center (measured) vs. the focused node's actual
  on-screen center matched to within 0.03px.
- fix: Hovering any Agent in the Section View crashed the whole page to
  blank — operator: "Hover on Agents Makes everything Disapppear now."
  Root cause: `SectionDrilldown.tsx`'s `activeAgentPoint` (added for the
  click-to-focus feature below) referenced `hoveredAgentPoint`, but that
  variable's own declaration was accidentally dropped in the same edit
  — a `ReferenceError` on every hover, which React has no error boundary
  around, so it unmounted the whole component tree
  (`console`: "An error occurred in the <SectionDrilldown> component").
  Restored the missing `const hoveredAgentPoint = hoveredAgent ?
  pointById.get(hoveredAgent.id) ?? null : null;` line. Also discovered
  in the process: this repo's root `tsconfig.json` has `"files": []`
  with only project references, so plain `tsc --noEmit -p .` (used to
  "verify" every change so far this session) silently checks NOTHING —
  it needs `tsc -b` (build/reference mode) to actually type-check
  source files, which WOULD have caught this as a compile error
  (`TS2304: Cannot find name 'hoveredAgentPoint'`) before it ever
  reached the browser. Verified live this time (dispatched a real hover
  event, confirmed no crash and the hover card renders correctly) —
  use `tsc -b` for all future verification in this repo.
- feat: Section View — clicking an Agent (opening its AgentDetailPanel,
  already existing behavior) now also centers and zooms the whole
  canvas in on that Agent, 3x, with a double-ring focus indicator —
  operator: "when the Panel Open The Agent will be Zoomed in to 3x with
  now 2 Borders will be added one the closer one is 2x the Original
  Border and 1 outer 1x the Size and 0,8 the Alpha." Scoped to the
  Section View only (confirmed with the operator — the overview's own
  150+ tiny dots were deliberately kept effect-free earlier for
  crowding reasons). Implementation:
  - `selectedAgentId` (AgentsMapPage.tsx) threaded down through
    AgentsMapCanvas.tsx into SectionDrilldown.tsx, which resolves it
    against its OWN section's agents only — a different Section's
    selected agent correctly leaves this Section's canvas untouched.
  - The "centering" is a real camera move on the whole
    `.agents-map-canvas` (translate + scale), not a per-node CSS
    transform — scaling just one node would visually detach it from
    its own connector lines/Hub, which live in the node's normal
    coordinate space. `.explore-drilldown.active .agents-map-stage`
    gained `overflow: hidden` to contain the 3x-bigger rendering
    (transforms don't affect layout, so without this the zoomed canvas
    would paint past the stage into the page/Sidebar).
  - INNER ring = the focused node's own border, thickened to 2px via a
    new `.agent-node--focused` class/`focused` AgentNode prop. OUTER
    ring = a new `.agent-focus-ring` element (1px border, 0.8 opacity,
    sized bigger than the node for a halo gap) — rendered as a SIBLING
    in SectionDrilldown.tsx, not a child of the node, since
    `.agent-node`'s own `overflow: hidden` would clip anything bigger
    than the node trying to render inside it.
  - "Name is Visible": reused the existing hover info card
    (`.agent-hover-card`, name/type/description) instead of building a
    separate mechanism — it now shows for `hoveredAgent ??
    focusedAgent`, so it stays up for as long as the panel is open, not
    just while actively hovering.
- feat: Section View Agent hover-zoom scale raised from 1.1x to 1.2x —
  operator: "I guess the Zoom need to be 1.2 for Agents"
  (`.agent-node--large:hover`, agents-map.css).
- feat: Hovering an Agent in the Section View now shows a floating info
  card with its name, type, and description (if it has one) — operator:
  "we can show the Agent name we zoomed on and a Description of that
  Agent if Exist below the name and the type of that agent think of a
  nice layout for that." Threaded a new `description` field end to end:
  demo-backend's `_agent_summary()` (main.py) now exposes each agent's
  first `settings` entry value (the same "Purpose"/"Domain" text
  AgentDetailPanel's own Settings tab already shows) on the LIST
  endpoint, not just the per-agent detail fetch — avoids an extra fetch
  per hover. Piped through `AgentSummary`/`MockAgent`
  (agentsApiClient.ts/mockAgents.ts/layoutAgents.ts). New
  `.agent-hover-card` (agents-map.css) renders as a SIBLING of the
  Agent nodes in `SectionDrilldown.tsx`, not a child of one —
  `.agent-node` itself needs `overflow: hidden` for its own oval-shape
  fix, which would clip a child trying to render past its tiny circle
  — positioned at the hovered node's own point, offset below it: bold
  serif name, a small type-colored uppercase caption (reusing the
  `.agent-node--<type>`-style `--node-color` convention), and a muted
  description paragraph shown only when present.
- fix: Section View's previous/next-Section chevron nav
  (`.section-edge-nav`) rendered over the app's own persistent Sidebar
  instead of staying within the page's content column — operator: "The
  previous Section Appear on top of the Side bar It should be in the
  same view not on top of the Side Bar." Root cause: `position: fixed`
  positions against the whole browser viewport, so `left:
  var(--space-4)` landed 16px from the window's own edge, under the
  Sidebar. Changed to `position: absolute` (agents-map.css), resolving
  against `.agents-map-page`'s own `position: relative` — the same
  content-column boundary every other Map element already respects.
  Also removed the visible border (operator: "It has a Border remove
  the Border") via `border: 1px solid transparent` rather than `border:
  none`, keeping the exact same box-model dimensions so the clickable
  area doesn't shrink.
- fix: Section View's "&larr; Back to Agents Map" button rendered
  dead-center of the screen with a background matching the
  previous/next-Section chevrons — operator: "the Back to main view is
  now in th center of the view with background Same as the Pervious
  and Next Section." Root cause: it's `.explore-drilldown.active`'s
  first flex-column child with no explicit width, so the default
  `align-items: stretch` forced it to fill the full row width, and a
  plain `<button>` centers its own text by default — stretching a
  `.btn`-styled (`--color-surface-raised` fill) button to full width
  made its label land in the middle of the screen and its background
  read as one continuous bar with `.section-edge-nav`'s own
  `--color-surface` fill. Fixed via `align-items: flex-start` on
  `.explore-drilldown.active` (`.agents-map-stage` is unaffected — it
  already sets its own explicit `width: 100%`).
- feat: Section View's edge-nav chevrons gained the idle "nudge"
  animation — operator: "Find the Animation for the Pervious and Next
  Section in the Prototype." The component was ported from
  html-prototype's `.skillmap-edge-nav`/`.skillmap-chev`
  (agents-map-skilltree-exploration.html's own rebuild pass), which
  never had an animation; the ACTUAL chevnudge animation lives in a
  different, earlier prototype pass (`.map-edge-nav-btn`,
  html-prototype/styles.css ~line 1864) that was never ported. Added
  the same `chevnudge` keyframe (1.8s ease-in-out infinite
  `translateX(0)` &harr; `translateX(3px)`) to `.section-edge-chev`,
  reversed on the left/prev side so both chevrons nudge outward.
- feat: Section View Agent nodes now scale to 1.1x on hover — operator:
  "the hover over an Agent should Zoom the Agent to 1.1x." Scoped to
  `.agent-node--large` only (the Section View drill-down's own bigger,
  far-less-crowded variant — one Section's Agents at a time, not the
  overview's 150+ packed dots), not the base `.agent-node` — the
  overview's own hover scale-up/glow was deliberately removed earlier
  (operator, 2026-08-15: "Remove the Hover Effect on the Agent as Its
  Really hard to see anything in this view") because one node scaling
  up threw a glow that swallowed its tightly-packed neighbors; this
  adds only the scale (no glow/shadow bump) and only where that
  crowding complaint doesn't apply.
- fix: Agent Map icons never rendered for almost any Agent, regardless
  of the previous two fixes — operator: "icons still not visible on
  agents." Root cause: `AgentNode.tsx` resolves `agent.icon` through
  `getVisualIconName()` (`visualOptions.ts`), which looked it up as a
  curated PICKER `id` (the 14-entry `VISUAL_ICONS` whitelist —
  `brain`/`mail`/`chat`/.../`link` — set by `VisualPicker.tsx`'s own
  `onSelectIcon(icon.id)`), returning `null` on no match. But
  `sample_data.py`'s `icon` values (and `SectionHub.tsx`'s own
  `section.icon`, rendered with NO lookup at all — the two were already
  inconsistent) are raw Material Symbols LIGATURE names
  (`handshake`/`download`/`category`/...) — only `mail` and `search`
  ever coincidentally matched both a valid id and its own ligature,
  which is the entire reason any icon ever appeared to work. Fixed
  `getVisualIconName()` to fall back to the raw value when it isn't a
  known picker id, so it now supports both conventions: a picker-set id
  still resolves through the curated list, anything else (API/demo
  data) is treated as an already-valid ligature name, matching
  `SectionHub.tsx`'s own existing convention. Spot-verified live
  (`.agent-node-icon` glyphs now render with the correct
  `Material Symbols Outlined` font and the expected
  `--color-on-accent` contrast on filled nodes, well beyond the
  `mail`/`search` coincidences that were the only ones ever working
  before) — operator took over full verification from there.
- fix: Filled (`--autonomous`) Agent nodes could render an invisible
  icon — `--agent-color-worker` is literally `var(--color-text)`
  (near-white), and `.agent-node--autonomous` fills the node's own
  background solid with that same `--node-color`, while the icon glyph
  inherited `color: var(--color-text)` from the base `.agent-node`
  rule — a near-white icon on a near-white fill for any filled Worker
  node — operator: "I guess the text of the icon is white on top of a
  while [white] Background change that." Added
  `.agent-node--autonomous .agent-node-icon { color:
  var(--color-on-accent); }` (agents-map.css) — reuses the codebase's
  own existing "text on a filled accent color" token (already used by
  agent-panel.css/settings.css), scoped to just the icon since the
  label/type text repositions OUTSIDE the filled circle on hover/focus
  reveal and would lose contrast against the dark canvas if it also
  went dark.
- feat: Demo data — `_STAGE_ICONS` (`sample_data.py`) only set an icon
  for the Fetch/Store pipeline stages; every other stage (Classify,
  Merge, Consult Expert, Summarize, Enrich — the bulk of the 142
  generated stage-Agents) rendered as a plain empty circle, hiding any
  icon-related rendering bug from view — operator: "Add Some Icons to
  the Agents and Jobs So I can See the Bugs." Gave every stage its own
  icon (`category`/`call_merge`/`forum`/`summarize`/`auto_awesome`).
- fix: Section View overview — clicking a Section only navigated in when
  the click landed exactly on its Hub node, even though hovering
  anywhere across the wider wedge (or the title label) already triggered
  that Section's own zoom — operator: "The Clicking Area of the Section
  is only the hub not the whole Section as Hover." Both the invisible
  hover wedge (`describeAnnularSector`, `HUB_RADIUS` to
  `SECTION_TITLE_RADIUS`) and the Section title `<div>` already carried
  `onMouseEnter`/`onMouseLeave` for `hoveredSectionId` but never an
  `onClick` — added `onClick={() => handleActivateSection(section.id)}`
  to both in `AgentsMapCanvas.tsx`, plus `cursor: pointer` on
  `.section-title` (agents-map.css) to match the wedge's own inline
  cursor style.
- fix: Section View (drill-down) connector lines reached the Hub's own
  edge (a prior fix) but still terminated at the AGENT end on that
  Agent's exact CENTER point, not its edge — barely visible in the
  overview's tiny dots but obvious here since drill-down Agents render
  at the much bigger `--large` size — operator: "the Lines move to the
  center of the Agent not the edge." Added `DRILLDOWN_AGENT_VISUAL_RADIUS
  = 1.875` (half of `.agent-node--large`'s own 3.75% width, same
  derivation as the existing `DRILLDOWN_HUB_VISUAL_RADIUS`) in
  `SectionDrilldown.tsx`, and applied `pointTowards()` trimming to the
  Agent-side endpoint of the Hub→root-agent lines and to BOTH endpoints
  of the predecessor→agent dependency lines (previously untrimmed on
  either end).
- fix: Section View Agents crowded/overlapped into a narrow central
  wedge while most of the canvas sat empty, and some Agents rendered
  cropped label text inside their own circle instead of a clean icon or
  empty dot — operator: "the Map is Condinced the the middle Alot of
  empty space about which makes agents and jobs over lap while not
  needed" and "Some Agents display a text inside the circle this is not
  a behavior needed if no icon just display the empty circle if there
  is an Icon Display the icone." Two fixes:
  1. `layoutAgents.ts`'s own `DRILLDOWN_ANGULAR_HALF_WIDTH_DEG` widened
     from `70` to `85` — the original value was a conservative first
     pass that only used a 140deg-total cone above the Hub, leaving most
     of the square canvas empty on both sides while packing every Agent
     into that thin wedge (`DRILLDOWN_TREE_RADIUS_MAX` stays `50`; even
     at 85deg the boundary math — `radius * sin(HALF_WIDTH) <= 50` —
     still holds with a small safety margin, `50 * sin(85deg) ≈ 49.8`).
  2. `SectionDrilldown.tsx`'s own `<AgentNode>` usage gained the `compact`
     prop (the SAME convention the overview already uses) — without it,
     label/type rendered as normal always-visible flex children, so an
     Agent with little else competing for its own tiny circle could show
     cropped label text instead of a clean dot; `compact` keeps them
     invisible until hover/focus/click, matching "icon or empty circle"
     exactly.
  Verified via `tsc --noEmit`.

- fix: Section View connector lines drew a straight line from EVERY
  Agent to the Hub's own CENTER, regardless of real pipeline structure
  — operator: "All Agents including Jobs are connected to the Hub no
  More Pipeline with Zigzag view is Visiable, the Connection Goes to
  the Center of the HUb not to the Edge." This view's own line-drawing
  was never updated when the Agents' own POSITIONS were redesigned to
  follow the real branch/tree shape (an earlier entry) — the Agents sat
  in the correct tree-shaped spots, but every line still just pointed
  straight at the Hub, visually flattening that shape into a plain
  spoke fan and hiding which stage actually depends on which. Fixed by
  threading `dependencyEdges` (already computed once at the top level
  by `layoutAgents.ts`'s own `buildDependencyEdges`) down through
  `AgentsMapCanvas.tsx` into `SectionDrilldown.tsx`: an Agent that's the
  target of a real `depends_on` edge within this Section now gets its
  line from that actual predecessor Agent instead of the Hub; only
  Agents with no predecessor (a pipeline's own entry point, or a
  standalone Agent) still connect straight to the Hub. That Hub
  connection now also reaches the Hub's own EDGE via `pointTowards()`
  (a new `DRILLDOWN_HUB_VISUAL_RADIUS = 2.5` constant, matching
  `AgentsMapCanvas.tsx`'s own `HUB_VISUAL_RADIUS` since the Hub is the
  same visual size in both views) instead of its center — the exact fix
  the overview's own Hub<->Agent lines already got, that this view never
  inherited. Verified via `tsc --noEmit`.

- fix: Icons inside Agent nodes were visibly clipped — operator: "The
  Icon are too big inside the agents it Clips," a direct side effect of
  the previous entry's own `overflow: hidden` fix (correct for the
  node's SHAPE, but the icon glyph's own font-size — 13px/20px in the
  overview/Section View — was still bigger than the node's own tiny box,
  now cropped at the edge instead of stretching it). Shrunk
  `.agent-node-icon` from `0.8125rem` to `0.375rem`,
  `.agent-node--large .agent-node-icon` from `1.25rem` to `0.625rem`,
  and `.agent-node`'s own padding from `var(--space-1)` (4px, eating
  most of a node that's often under 10px) to `1px` (`2px` for the
  `--large` Section View variant, which can afford a little more).

- fix: Individual Hub/Agent dots (not the overall canvas — a different
  bug than the two entries below) rendered as ovals, and in the Section
  View drill-down visibly overlapped each other — operator: "the Hubs in
  the main Screen is not Circluar any more" and "the Agents in the
  Section views Still Oval," then after the Hub fix landed: "Hubs now
  Circular... the Section View All Agents appear in Oval and on top of
  each other with a lot of Empty Space." Root cause, isolated live: an
  icon-less `.agent-node` measured perfectly square
  (`getBoundingClientRect()`), while an otherwise-identical one WITH an
  icon measured 9.33x22.33 — a Material Symbols icon glyph's own
  intrinsic line-height (its font-size, ~13-20px depending on context)
  exceeded the tiny dot's `aspect-ratio: 1/1`-derived height, and since
  `.hub-node`/`.agent-node` are `display: flex` CONTAINERS (for their own
  icon/label/type children), that content pushed the container taller
  than its aspect-ratio square — width stayed correct, height didn't,
  producing an oval. A first attempt put `overflow: hidden` on the ICON
  SPAN itself and did not work (verified live — still 9.33x22.33 with the
  icon's own overflow already hidden); the actual fix needed it on the
  CONTAINER (`.hub-node`/`.agent-node` themselves) — clipping overflow at
  the container's own boundary is what stops a descendant's natural
  content size from inflating the container that aspect-ratio is
  supposed to govern. The Section View's own "Agents on top of each
  other" symptom was very likely just these oversized oval hitboxes
  visually colliding even though their actual center points
  (`layoutSectionDrilldown`'s own angle/radius math) were correctly
  spaced apart — expected to resolve once the shape itself is fixed, not
  a separate layout bug. Verified live for `.hub-node` before applying
  the identical fix to `.agent-node`. Not yet re-verified for the Agent
  side — operator taking over verification from here.

- fix: Agents Map overview rendered as an oval instead of a circle, and
  separately sat as a small fixed 504px map surrounded by a large empty
  margin — operator: "First the map is Consunrated in the Center with
  alot of Empty space , The Cicles Appear Oval not circlur" (the oval
  half reconfirmed as "The Oval bug not fixed" mid-fix, after the first
  attempt only removed part of the cause). Two related fixes:
  1. **Oval**: the previous entry's own `max-height: 100%` addition to
     the SHARED base `.agents-map-canvas` rule was meant only for the
     Section View drill-down, but this rule also backs the overview,
     which pins `width` to an explicit 504px via `.explore-zoom-
     overview`'s own override. `aspect-ratio` only shrinks BOTH
     dimensions together when the non-explicit one is `auto` — since
     width here was never `auto`, `max-height` just clamped height
     alone whenever the stage's available height dropped below 504px
     (which the recent flex-height fixes made a real case, not
     theoretical), squishing the circle into an oval. Removed
     `max-height` from the shared base rule entirely — the drill-down's
     own scoped `.explore-drilldown .agents-map-canvas` override doesn't
     need it either, since it already solves its own sizing by driving
     off `height` directly.
  2. **Empty space**: `.explore-zoom-overview` (the resting/"zoomed out"
     overview state) was flat `width: min(100%, 504px)` — a fixed size
     chosen when the surrounding layout still had OTHER bugs; now that
     `.agents-map-stage` correctly reserves exactly the real available
     space (recent entries above), a flat 504px inside that correctly-
     sized-but-much-bigger stage just reads as a small map floating in a
     large empty margin. Reworked to the same height-driven pattern the
     drill-down already uses: `height: min(calc(100% - 140px), 700px);
     width: auto; max-width: 100%;` — fills however much room the stage
     actually has (up to a genuine 700px "not zoomed out at all"
     ceiling) instead of sitting fixed regardless of surrounding space.
     The `140px` reservation (tuned live, starting from 80px and
     increasing after measuring residual overflow) leaves room for
     Section titles — positioned at `SECTION_TITLE_RADIUS` inside the
     canvas's own nominal circle, but rendering a real text box (label +
     subtitle) that pokes a bit further out than that single anchor
     point — which the OLD flat-504px layout absorbed for free via its
     own large incidental slack, and a canvas now filling 100% of
     available space no longer has any slack left for. A flat
     canvas-size-independent px reservation is correct here since title
     text doesn't grow with the canvas.
  Verified live end-to-end at 1280x800 (fresh tabs, real `.hub-node`
  click-throughs): overview canvas 516x516 (square, `mainOverflowAmount
  === 0`), drill-down still 621x621 with zero overflow, "Back to Agents
  Map" restores the overview cleanly, zero console errors throughout.
  `tsc --noEmit` passes clean.

- fix: Section View (drill-down) required scrolling to see at all, and
  once visible had a big empty gap before it and a cut-off Section
  title — operator: "No Still All the Items Back to Map and the
  Section view is Appearing When I Scroll only," then "Came up but wtill
  there is a big Gap between Back to Map and the Section view The
  Section Name you need to scroll to see it." Three compounding bugs,
  found and fixed in sequence, all live-verified via
  `main.scrollHeight - main.clientHeight === 0` plus real `.hub-node`
  click-throughs on fresh tabs (not just static measurement):
  1. The overview's own canvas was only hidden via `opacity: 0`
     (`.zooming-out`, from the existing zoom transition) when a
     drill-down opened — never removed from FLEX LAYOUT, so it kept
     reserving a full `flex: 1` share of `.agents-map-page`'s height at
     the same time as the drill-down's own `.explore-drilldown` block,
     pushing the now-visible drill-down below the fold. Fixed:
     `AgentsMapCanvas.tsx` applies a new `is-inactive` class once
     `activeTarget` is set (i.e. once the zoom-in transition has
     already finished).
  2. `.explore-drilldown.active` (`display: block`) and its own nested
     `.agents-map-stage`, as flex children with no explicit width,
     sized to shrink-fit instead of stretch — the same collapse class
     the overview's own stage hit two entries back, one level deeper.
     Fixed: `.explore-drilldown.active` is now `display: flex;
     flex-direction: column; width: 100%; flex: 1; min-height: 0`.
  3. The drill-down's own canvas (700px, uncapped — unlike the
     overview's own smaller `.explore-zoom-overview` override) still
     overflowed vertically even once its parents sized correctly,
     because `aspect-ratio` only shrinks BOTH dimensions together when
     the non-explicit one is `auto` — `max-height: 100%` alone clamped
     height but left `width: min(100%, 700px)` (an explicit value)
     unchanged, producing a non-square, still-overflowing box. Fixed
     with a drill-down-scoped override,
     `.explore-drilldown .agents-map-canvas { width: auto; max-width:
     100%; height: min(100%, 700px); }` — driving off height (reliably
     the tighter constraint on this app's real fixed-viewport layout)
     instead of width, leaving the overview's own separately-overridden
     sizing untouched.
  Along the way, `is-inactive`'s FIRST attempt (`position: absolute`)
  turned out to be only a half-fix in its own right: it stopped the
  overview competing for LAYOUT space, but its `.zooming-out` transform
  (`scale(2.1)`, which stays applied for as long as a drill-down is
  showing, not just during the brief transition) kept contributing to
  `.main`'s own SCROLLABLE OVERFLOW region regardless — a box scaled to
  ~1058px still counts toward scrollable content even once
  `position: absolute` has removed it from its parent's own size
  calculation, two genuinely different mechanisms. Replaced with
  `display: none` (safe specifically because the animation has already
  finished by the time `is-inactive` applies, and "Back" clears it
  instantly with no reverse animation to interrupt either). Verified via
  `tsc --noEmit` throughout.

- fix: Agents Map canvas required scrolling a large amount to see —
  operator: "Not fixed I need to Scoll a full Page to See the Map"
  (following the previous entry's centering fix, which had itself
  replaced an even earlier `transform: scale()` fix). Root cause: the
  previous fix's `.agents-map-stage { min-height: calc(100vh - 96px); }`
  guessed the sticky topbar's + `main`'s own padding footprint from ONE
  measured viewport (1280x800) — that guess only holds by coincidence at
  that exact size; at the operator's real window size it overshot the
  truly available space, and because it was a flex `min-height` driving
  vertical CENTERING, the overshoot pushed the centered canvas roughly
  twice as far down the page as the raw overshoot itself. Also caught
  mid-diagnosis: `document.body.scrollHeight` (what both prior fixes were
  verified against) is the WRONG element to check here — `.main`
  (`shell.css`) has its own `overflow-y: auto`, making IT the real scroll
  container, not `document.body`; `main.scrollHeight` vs
  `main.clientHeight` is what actually needed checking, and hadn't been
  after the centering change. Replaced the guessed constant with a
  self-adapting flex layout: `AgentsMapPage.tsx`'s own root wraps in a
  new `.agents-map-page` (`display: flex; flex-direction: column;
  min-height: 100%`) — percentage height resolves reliably here because
  `.main` is a CSS Grid item (`shell.css`'s `.app-shell { display: grid;
  min-height: 100vh; }`), which the Grid spec guarantees a definite size
  for, unlike normal block flow — and `.agents-map-stage` is `flex: 1;
  min-height: 0; width: 100%` (the explicit `width: 100%` fixes a second
  bug this surfaced: without it, `.agents-map-stage` — itself a flex
  container for centering its own canvas — sized to shrink-fit instead of
  stretching, starving `.agents-map-canvas`'s own `width: min(100%,
  504px)` of a real basis to resolve "100%" against and collapsing the
  whole canvas to 0x0). No magic numbers left on either axis — the layout
  now fills exactly whatever space is really available, self-correcting
  to any viewport. Verified on a FRESH tab (a reused tab's console showed
  a stale mid-edit HMR error that a fresh load didn't reproduce) at
  1280x800: `main.scrollHeight - main.clientHeight === 0`, canvas
  504x504 and centered. Also stress-tested at a deliberately short
  1024x560 viewport: a small, proportional 55px overflow appears (the
  504px canvas genuinely doesn't fit in the ~464px truly available at
  that size) — expected, self-correcting behavior, not another
  full-page-sized guess gone wrong.

- fix: Agents Map canvas sat pinned to the very top of the page with a
  big empty void below it, instead of centered in the space available —
  operator: "No its not fixed lots of Empty Space at the top" (following
  the previous entry's scroll fix). Root cause: shrinking
  `.explore-zoom-overview`'s own box (previous entry) correctly matched
  the RESERVED layout space to what's actually painted, removing the
  scrollbar — but `.agents-map-stage` had no way to use the leftover
  704px - 552px ~= 152px of now-genuinely-spare vertical space, so it
  all just sat below the canvas as dead page background instead of
  splitting evenly around it. Fixed by making `.agents-map-stage` a flex
  container (`align-items: center; justify-content: center;`) with
  `min-height: calc(100vh - 96px)` (96px approximates the sticky
  topbar's real footprint + `main`'s own bottom padding, measured live
  via `getBoundingClientRect()` before picking the value so it stays
  safely inside the real available space rather than overshooting it
  and reintroducing a scrollbar). Verified live at a 1280x800 viewport:
  `document.body.scrollHeight` still exactly matches `window.innerHeight`
  (no scroll reintroduced), and the canvas now sits with a symmetric
  100px gap above and below instead of 0px above / 152px below.

- fix: Agents Map overview required scrolling down to see, even though
  the map itself fully fits a normal viewport — operator: "The Map is
  Displayed After scrolling down." Root cause: the overview canvas's
  resting "zoomed out" state used `transform: scale(0.72)`
  (`.explore-zoom-overview` in `agents-map.css`) to shrink it visually —
  but a CSS `transform` only changes what's PAINTED, not the LAYOUT
  SPACE the element reserves in its own parent. `.agents-map-stage` kept
  reserving room for the full unscaled 700px box even though only
  ~504px of it was ever visually used, silently padding the page with
  ~200px of dead space below the visible map and pushing the bottom of
  that reserved region past the fold on anything shorter than a tall
  desktop viewport. Fixed by shrinking the actual box (`width: min(100%,
  504px)`, i.e. 0.72 * the base rule's own 700px) instead of scaling it
  — percentage-positioned children (Hub/Agent nodes, SVG viewBox
  coordinates) don't care whether they're 0-100% of a big box or a small
  one, so nothing else needed to change. Verified live: at a 1280x800
  viewport, `document.body.scrollHeight` now matches `window.innerHeight`
  exactly (was overflowing by 44px before); screenshotted the full map
  rendering fully within the viewport with zero scroll.

- fix: Section View rendered with the Hub/title visible but every Agent
  collapsed onto one point off the bottom of the canvas, reading as
  empty — operator: "View is empty" (after "The Who is empty," a typo
  for the same report). Root cause: `AgentsMapPage.tsx`'s `fullAgents`
  state — what `SectionDrilldown.tsx` actually receives — was a
  manually-built placeholder array with `angleDeg: 0, radius: 0` on
  EVERY agent, justified by an old comment: "recomputed by
  layoutSectionDrilldown() inside every drill-down consumer, never
  rendered." That stopped being true the moment `layoutSectionDrilldown()`
  was rewritten (previous entry below) to STRETCH the input's own
  already-computed `angleDeg`/`radius` instead of discarding them for a
  fresh spread — fed all-zero placeholders instead, every agent's
  `radiusFraction` came out identically negative (`(0 - 29) / 27`), and
  the resulting negative radius placed every single Agent at the exact
  same off-screen point below the Hub. Fixed at the actual source:
  `fullAgents` now reuses `layout.mapAgents` directly (already
  real-geometry, and already the full eligible set — clustering, the
  original reason a SEPARATE "full" array existed, is itself dead code
  right now, `layout.clusters` always `[]`) instead of rebuilding a
  parallel placeholder array. Verified via `tsc --noEmit`.

- feat: Section View (the drill-down opened by clicking a Section)
  redesigned — Hub moves to the bottom of the canvas with its title and
  subtitle rendered just below it, Agents now fan out ABOVE the Hub
  using the same branch/tree shape the overview computed (just stretched
  into more space), Agents render 0.75x the Hub's own size, and an Agent
  with no icon of its own now falls back to its Section's icon —
  operator: "Now Clicking on a Section Takes us to the Section view I
  want to Have the title and the Subtitle Rendered at the Bottom on the
  Section View with the Hub then All Agents Appear on top there, Same
  Branch View but now we have More Space So Spread then, and Now Agents
  will be Bigger 0.75 of the Hub Section Icons will be displayed."
  Several pieces:
  - `polarToCartesian()`/`describeAnnularSector()` (`polarLayout.ts`)
    now take a full `{x,y}` Point for `center` instead of a single
    scalar (every existing call site only ever used the symmetric
    default, so this is a widening, not a breaking change) — needed so
    Agents/lines can fan out from the Hub's own OFF-CENTER bottom point
    instead of literal canvas center. New shared
    `DRILLDOWN_HUB_ANGLE_DEG = 90` (straight down) constant.
  - `AgentNode.tsx` gained `center` (the origin its own polar math
    measures from) and `large` (`.agent-node--large`, new CSS: width
    `3.75%` = 0.75 * the Hub's own `5%`, with proportionally bigger
    icon/type font sizes) props.
  - `layoutAgents.ts`'s `layoutSectionDrilldown()` rewritten: instead of
    discarding the overview's own tree shape for a fresh even 360deg
    spread, it now STRETCHES the already-computed `angleDeg` (which
    already encodes `assignTreeAngles`' zigzag/depth-ordering) and
    `radius` (already encodes `computeAgentDepth`'s pipeline depth) from
    the overview's own narrow per-Section band into a much bigger one
    (`DRILLDOWN_TREE_RADIUS_MIN/MAX = 14/50`, angular half-width `70deg`
    around straight-up from the Hub) — "Same Branch View... more space
    so spread them," not a different layout algorithm. `AGENT_RADIUS_MIN`
    /`AGENT_RADIUS_MAX` (the overview's own band) exported so this remap
    has real bounds to stretch FROM. Radius cap (50, not a rounder 62) is
    deliberately conservative — `radius * sin(70deg)` must stay under 50
    (the Hub's own horizontal room to the canvas edge) even for an Agent
    at both max radius AND the widest angular swing simultaneously, or
    it would clip off the left/right edge.
  - `SectionDrilldown.tsx`: Hub placement uses `radiusOverride={32}` +
    an `angleOffsetDeg` that cancels the Section's own overview
    `hubAngleDeg` so it always lands at `DRILLDOWN_HUB_ANGLE_DEG`
    (straight down) regardless of where it sat on the overview map;
    connector lines and every `AgentNode` share that identical
    `hubPoint` as their own `center`; a new title block (reusing the
    overview's own `.section-title`/`.section-title-subtitle`/
    `.section-title-accent` treatment) renders 11 units below the Hub;
    each `AgentNode`'s own `agent` prop falls back to `section.icon`
    when `agent.icon` is null.
  - `sample_data.py`/`main.py` needed no changes — `subtitle`/`icon`
    were already exposed by `GET /sections` from the previous entry.
  Verified via `tsc --noEmit`.

- feat: Sections now carry a `subtitle` (displayed) and `description`
  (data-only, for later) — operator: "Now I need to have a Section
  Subtitle and Description The Subtitle will be Displayed in the Agent
  Map The Description will be used later Generate Some Dummy Info for
  now and update the API to get those in Section Call." `subtitle` is
  the existing `slogan` field (`sample_data.py`'s own SECTIONS dict),
  renamed now that it has a real consumer — values unchanged, still the
  "word · word · word" style. `description` is genuinely new one-
  sentence dummy copy per Section (plausible business-domain text, not
  rendered anywhere yet, per the operator's own "will be used later"
  framing). `GET /sections` (`main.py`) needed no code change — it
  already returns the raw `SECTIONS` dict values unshaped, so both
  fields flow through automatically; restarted the demo backend
  (`preview_stop`/`preview_start` — `--reload` is documented unreliable
  here) and verified live via `curl http://127.0.0.1:8090/sections`.
  Frontend: `SectionSummary` (`layoutAgents.ts`) gained both fields;
  `AgentSection` (`mockAgents.ts`) gained `subtitle` only (threaded
  through `layoutAgents()`'s own Section-building map and
  `ClusterDrilldown.tsx`'s literal `clusterHubSection` — `description`
  deliberately stops at `SectionSummary`, not threaded further, since
  nothing reads it yet); `AgentsMapCanvas.tsx` renders it as a new
  `.section-title-subtitle` line under the Section title (plain
  `--font-sans`, muted, normal-case — a caption under the title's own
  bold `--font-serif` heading, not a second competing headline),
  rendering nothing when a Section has none set. Verified via
  `tsc --noEmit`.

- fix: Agent nodes no longer drop the Section-level hover (zoom/glow/
  title) when the cursor passes over them, and their own hover-triggered
  label reveal is removed — operator: "Remove the Agents Hover as it
  affects the Section Hover." An Agent node has to keep real
  pointer-events to stay clickable (unlike the lines/section-node-group
  wrapper, which could just go `pointer-events: none`), so it
  unavoidably sits on top of its own Section's hover-wedge — the cursor
  passing over an agent made the wedge (and `hoveredSectionId`) drop out
  from under it, the same class of interference already chased down for
  lines and the section-node-group wrapper, stuttering the Section's own
  zoom/glow/title every time the mouse crossed an agent dot. Fixed at
  the root: `AgentNode.tsx` gained an `onHoverChange` prop (mirrors
  `SectionHub.tsx`'s own), wired in `AgentsMapCanvas.tsx` to the SAME
  `setHoveredSectionId(agent.sectionId)` call the Hub/hit-region/wedge
  already use — hovering an agent now COUNTS as hovering its own
  Section, keeping the zoom alive instead of dropping it. Also removed,
  per the literal "Remove the Agents Hover": `agents-map.css`'s
  `.agent-node--compact:hover` trigger for the label/type tooltip reveal
  (kept `:focus-visible`, a different interaction mode that never
  touches `hoveredSectionId`, for keyboard Tab-navigation
  accessibility). Verified via `tsc --noEmit`.

- fix: Section hover now actually triggers from anywhere in the
  Section (agents, empty wedge space), not just a literal hover on the
  Hub icon — operator: "The Hover is on the Hub only I need it to be on
  the Everything in that Section." Root cause: the new
  `.section-node-group` wrapper (previous entry below) is `inset: 0` —
  FULL-CANVAS-SIZE, one per Section, all stacked directly on top of each
  other AND on top of `.agents-map-lines`' own per-Section hover-wedge
  `<path>`. Unlike an SVG shape, a plain HTML `<div>` is hit-testable
  across its entire box by default even with nothing painted in it, so
  the LAST-rendered Section's wrapper silently captured every pointer
  event across the whole canvas except where an actual Hub/Agent button
  sat on top of it — leaving only a literal hover directly on a button
  working, and even that not reliably attributed to the right Section.
  Fixed the same way `.agents-map-lines` was fixed for the identical
  class of bug one pass ago: `pointer-events: none` added to
  `.section-node-group` itself, with `.hub-node`/`.hub-hit-region`/
  `.agent-node` each explicitly opting back into `pointer-events: auto`
  (an inherited property, a descendant can freely override it) so those
  real interactive targets keep working exactly as before. Verified via
  `tsc --noEmit`.

- feat: Section hover-zoom now scales the whole visual cluster (Hub, its
  own Agents, and its own connector/dependency lines) together as one
  unit anchored on the Hub, not just the Hub icon alone — operator:
  "Now Only the Hub is Zooming not the Whole Section," clarified as "Hub
  + its Agents + its lines together." `AgentsMapCanvas.tsx` restructured
  the flat `{sections.map(SectionHub)}` + `{agents.map(AgentNode)}`
  two-pass render into ONE pass per Section: a new
  `<div className="section-node-group">` wrapper (`position: absolute;
  inset: 0` unconditionally — required so it stays the containing block
  for its `position: absolute` Hub/Agent children whether or not a
  `transform` is currently applied to it, avoiding a jump when hover
  toggles) containing that Section's own `<SectionHub>` and its own
  filtered `<AgentNode>`s, with `transform-origin` set inline to the
  Hub's own `%, %` position and a `.is-hovered` class (from the same
  shared `hoveredSectionId` state) triggering `transform: scale(1.1)`
  (`agents-map.css`'s new `.section-node-group`/`.section-node-group.
  is-hovered` rules, `z-index: 4` on the hovered state so the zoomed
  cluster paints above a dimmed neighbor). The matching `<g>` for that
  Section's own Hub<->Agent + dependency lines (inside `.agents-map-
  lines`) gets the identical `scale(1.1)` + Hub-anchored
  `transform-origin` (in SVG user units) so both layers zoom in lockstep
  — the KB<->Hub spoke line's own separate `<g>` is deliberately excluded
  since one of its endpoints (the KB) isn't part of this Section's own
  zooming subtree. The Hub's own PREVIOUS individual `scale(1.1)` on
  `:hover`/`.is-hovered` (added two passes ago) is now removed from
  `.hub-node` itself — it would have compounded with the new wrapper's
  own scale (1.1 * 1.1 = 1.21x); `.hub-node`'s hover rule now only carries
  the glow-pulse animation. Verified via `tsc --noEmit`.

- fix: Section Hub now actually zooms on hover from anywhere in the
  Section's own hover-wedge, not just a literal cursor-over-hub — operator:
  "Titles Zooming in but the Sections are not." Root cause: the Hub's
  zoom/glow was driven purely by CSS `:hover`/`:focus-visible` (plus a
  `.hub-hit-region:hover ~ .hub-node` sibling trick), which can only ever
  fire when the cursor is literally over `.hub-node` or its hit-region —
  but the Section-wide hover-wedge (`AgentsMapCanvas.tsx`, "the Section
  Hover is the whole Area between the Hub and the Title") is a
  structurally unrelated SVG element elsewhere in the DOM that sets the
  SAME shared `hoveredSectionId` React state from anywhere in the wedge.
  The title already read that shared state directly (`.is-hovered` class)
  so it zoomed correctly from anywhere in the wedge; the Hub's CSS-only
  trigger could not. Added an `isHovered` prop to `SectionHub.tsx`
  (`hoveredSectionId === section.id`, passed from `AgentsMapCanvas.tsx`)
  applied as a `.is-hovered` class on `.hub-node`, and added
  `.hub-node.is-hovered` as a trigger alongside the existing
  `:hover`/`:focus-visible`/sibling rules in `agents-map.css` (kept for
  direct mouse/keyboard interaction). Verified via `tsc --noEmit`.

- feat: Section hover zoom increased — operator: "Increase the Zoom a
  bit 1.1 for Sections and 1.07 for title." `agents-map.css`:
  `.hub-node:hover`/`:focus-visible` (and its `.hub-hit-region:hover ~
  .hub-node` sibling) scale from 1.03x to 1.1x; `.section-title.
  is-hovered` scale from 1.06x to 1.07x.

- fix: Section hover no longer flickers/drops when the cursor crosses a
  connector line — operator: "Still the lines overcome the Section
  Hover." Root cause: the per-Section invisible hover-wedge `<path>`
  paints first/underneath inside `.agents-map-lines`' own SVG, with
  every spoke-line/cluster-line/dependency edge painted after it, on
  top, in DOM order — and an SVG `<line>` with a stroke is hit-testable
  by default even with no handlers of its own, so the instant the
  cursor crossed a rendered line's stroke, that line (not the wedge
  underneath it) became the topmost element under the pointer, firing
  the wedge's own `onMouseLeave` and dropping `hoveredSectionId`, then
  re-entering the wedge past the line fired `onMouseEnter` again — a
  flicker every time the mouse crossed a line while hovering a Section,
  worse in busier Sections. Fixed by setting `pointer-events: none` on
  `.agents-map-lines` itself (agents-map.css) and relying on the wedge
  `<path>`'s own existing inline `style={{ pointerEvents: 'all' }}`
  (AgentsMapCanvas.tsx, unchanged) to re-enable itself specifically — an
  inline style on an element always wins over an inherited property
  from its own parent, so every other decorative SVG element in that
  file (lines, pulse dots, the currently-unused radar/ring/boundary
  guides) is now inert to the pointer, and the wedge is the only thing
  that can ever receive a hover there.

- feat: Section hover now zooms the Hub in by 1.03x and its title by
  1.06x, and dependency/Hub<->Agent connector lines are slimmer —
  operator: "Hovering on a Section Should Zoom the Section in by 1.03x
  and the Title by 1.06x The Lines and Agents Should not be Hovered for
  now mak the lines Slimer a even 0.7 the current weight."
  `agents-map.css`: `.hub-node:hover`/`:focus-visible` (and its
  `.hub-hit-region:hover ~ .hub-node` wide-hit-target sibling) now also
  sets `transform: translate(-50%, -50%) scale(1.03)` alongside the
  existing glow-pulse animation, with `transform` added to `.hub-node`'s
  own transition list so it animates smoothly instead of snapping;
  `.section-title.is-hovered`'s own scale changed from 1.07x to the
  requested 1.06x. Deliberately did NOT add any hover-driven scale to
  `.agent-node` (already removed entirely in an earlier pass — see that
  rule's own comment) or to `.cluster-line` (never had one) — both stay
  exactly as they render today, just dimmed via the existing
  `.is-dimmed` opacity rule when a DIFFERENT Section is hovered.
  `.cluster-line`'s own `stroke-width` reduced from 0.25 to 0.175 (0.7x).

- feat: Agent depth-to-radius mapping now applies a small deterministic
  +/- jitter instead of an exact value — operator: "the Agents Appear
  like they are in Circles equal Distance around the KB Which doen't fit
  my Tree Concept they need to have a + - Number to be more Tree
  Looking." Every agent at the same pipeline depth previously landed on
  the literal same radius, so a Section's whole set of depth-1 (or
  depth-2, etc.) agents formed a visible perfect concentric ring around
  the KB — read as "rings," not "tree." Added `hashToUnitOffset()` to
  `layoutAgents.ts` (a deterministic hash of the agent's own id into
  [-1, 1] — stable across re-renders/re-fetches, not `Math.random()`) and
  applied it as `baseRadius + jitterAmplitude * hashToUnitOffset(id)`,
  clamped back into `[AGENT_RADIUS_MIN, AGENT_RADIUS_MAX]`. Amplitude is
  capped at `RADIUS_JITTER_FRACTION = 0.35` of the gap between two
  adjacent depth rings (`radiusStep`, itself capped at
  `RADIUS_JITTER_MAX = 3`) so a jittered agent can never visually drift
  into a neighboring depth's own band and read as the wrong pipeline
  stage. Verified via `tsc --noEmit`.

- feat: Agent node colors are now keyed by Type instead of the old
  arbitrary blue/purple/pink trio — operator: "I need the Workers/Jobs
  to be White, Experts to have a Color That Matches ourdesign, Producers
  a different color that matchs the design as well." `tokens.css`'s
  `--agent-color-worker`/`--agent-color-producer`/`--agent-color-expert`
  (the existing REQ-SB-12 mechanism `.agent-node--<type>` rules already
  read `--node-color` from, and a per-agent `agent.color` Visual-tab
  override already takes precedence over via inline style) now resolve
  to: worker = `var(--color-text)` (the same "white" the Agent<->Hub
  connector lines already use, not a literal `#fff`), expert =
  `var(--color-accent)` (the app's own real signature copper — the most
  literal "matches our design"), producer = `#65a30d`, a distinct hue
  already present in `visualOptions.ts`'s own curated `VISUAL_COLORS`
  palette (not a new invented value), picked to avoid colliding with any
  Section's own color. `VISUAL_COLORS`'s inline comments updated to match
  the new token mapping. Verified via `tsc --noEmit`.

- investigated, no fix needed in sample_data.py: operator flagged "Some
  pipeline Reuse the Same Jobs Accross pipeline this is not going to
  happen." Checked programmatically (`sample_data.py`'s own generator,
  run standalone): every generated stage-Agent id is
  `{domain_slug}-{stage_slug}`, all 28 domain slugs are unique, and a
  scripted check of every `depends_on` edge across all 155 Agents found
  zero cases where an Agent's own predecessor belongs to a different
  domain (0 problems out of every edge checked) — the generator does not
  currently share a Job Agent across two different pipelines. Reported
  this finding back to the operator rather than changing sample data
  that already looks correct; still open — if the operator points to a
  concrete example, the more likely explanation is a stale demo-backend
  process (MEMORY.md's own documented `uvicorn --reload` unreliability
  constraint) or a frontend line-crossing rendering artifact between two
  DIFFERENT pipelines that happen to share a Section, not an actual
  data-level id reuse.

- feat: Agents Map pipeline chains now zigzag instead of sweeping in a
  straight monotonic line, and a chain's own angular territory no longer
  grows with its stage count — operator: "Now The Pipeline looks like a
  Straight Line Make it a bit of ZigZag It will be move visually
  Appealing, and at the same time if we have a 10 Stages Pipeline they
  can fit between the same spaces." The prior weighted-subtree-size
  partition (next entry below) DID spread a chain's stages apart —
  fixing the earlier collapse-to-one-spoke bug — but it did so by
  sweeping monotonically across an ever-wider territory (proportional to
  total stage count), which reads as a smooth diagonal line/spiral
  rather than a deliberate zigzag, and meant a 10-stage pipeline would
  claim roughly double a 5-stage one's angular width. Reworked
  `assignTreeAngles()` in `layoutAgents.ts`: branch/fan points (more
  than one child — e.g. Fetch fanning into two Classify stages) still
  subdivide their own territory among children, but now by each child's
  own LEAF count (`computeLeafCount()`, replacing `computeSubtreeWeight`)
  rather than total descendant count — a straight chain of any length
  has exactly one terminal stage, so it claims the same territory as a
  single standalone Expert, same as before the weighted-partition
  attempt. Inside a straight (single-child) run, though, a stage no
  longer shrinks or advances that territory at all — every stage keeps
  the SAME `[lo, hi]` range handed down from its nearest branch ancestor
  and just alternates a flat `ZIGZAG_AMPLITUDE_DEG = 6` swing to either
  side of that fixed range's center as depth increases. Because the
  swing is a constant, not a fraction of chain length, a 4-stage and a
  10-stage run both fan out inside the exact same fixed territory,
  alternating sides more times rather than claiming more width — depth
  (radius) does the rest of the work of keeping every stage visually
  distinct. Verified via `tsc --noEmit`.

- fix: Agents Map tree-angle algorithm reworked from a leaf-count
  dendrogram to a weighted subtree partition ("icicle" layout applied to
  point placement) — operator: "In the sample Data I see Lots of Experts
  in the pipeline and Less Jobs That Makes the visual Look Weird Fix
  that in the sample data." Investigated first: the actual sample-data
  counts already favor Jobs heavily (145 pipeline-stage Jobs vs. 10
  standalone Experts; e.g. the `capture` Section alone has 30 Jobs vs. 3
  Experts) — the real cause was the PRIOR tree-angle algorithm
  (`assignTreeAngles`, from the previous entry below) counting only
  LEAVES for slot width and averaging a chain node's angle down to its
  single child's own angle: a standalone Expert (1 leaf, no
  `depends_on`, no connecting line) and an entire straight 4-/5-stage
  pipeline chain (also 1 leaf, since only the terminal Store stage has
  no dependents under it) got an EQUAL angular slot, and every stage in
  that chain then collapsed onto the exact same angle as the one after
  it — a 5-agent pipeline visually read as one thin radial spoke, while
  a lone Expert stood out at its own clean angle despite there being far
  fewer Experts overall. Confirmed with the operator (`AskUserQuestion`)
  that this belonged in the frontend layout math, not a sample-data
  rebalance. Fix: added `computeSubtreeWeight()` (self + every
  descendant, not just leaves) and rewrote `assignTreeAngles()` as a
  weighted preorder partition — each node reserves a `1/weight` slice of
  its own allotted angular range for its own point, then divides the
  REMAINING range among its children proportional to their own weight,
  recursively. Run on a straight chain this degenerates to exactly
  "evenly spaced across the full range" (verified by hand: a 5-node
  chain's weights 5/4/3/2/1 produce angles at 1/10, 3/10, 1/2, 7/10,
  9/10 of its own allotted width — evenly spaced), which is what makes a
  multi-stage pipeline visibly fan out instead of collapsing to a
  needle; a 6-stage fork/merge pipeline still splits its own remaining
  range across multiple children the same way. Verified via
  `tsc --noEmit`.

- fix: Dependency-edge connection cap corrected from an arbitrary
  combined total of 5 to the real, direction-aware data-model
  constraint — operator: "Jobs will have only 2 Dependencies in and out
  This is clean the visual alot." `layoutAgents.ts`'s
  `buildDependencyEdges()` now tracks incoming (`depends_on` count) and
  outgoing (fan-out to dependents) separately, each capped at 2
  (`MAX_INCOMING_CONNECTIONS`/`MAX_OUTGOING_CONNECTIONS`), replacing the
  prior single `MAX_AGENT_CONNECTIONS = 5` combined-total guess.

- feat: Agents Map overview's Hub-Agent connector lines now follow real
  `depends_on` pipeline edges instead of connecting every agent in a
  Section to every other agent — operator: "there is too many
  Dependencies which will not be true limit Max Agent Connection to 5."
  The old all-pairs mesh (`for i, for j` over every agent pair sharing a
  Section) drew a line between agents with no actual relationship,
  which is what made the view unreadable once a Section held more than
  a handful of agents. Added `buildDependencyEdges()` to
  `layoutAgents.ts`: walks each agent's real `depends_on` list, keeping
  an edge only when both endpoints exist in the rendered agent set, and
  caps every agent at `MAX_AGENT_CONNECTIONS = 5` combined
  incoming+outgoing edges (a ceiling against a future unusually-wide
  fan-out/fan-in stage — today's sample data tops out at 2 parents/2
  children, so the cap is never actually hit yet). New exported
  `DependencyEdge` type/`dependencyEdges` field on `AgentMapLayout`,
  threaded through `AgentsMapPage.tsx` state and a new
  `AgentsMapCanvas.tsx` prop; the Canvas resolves each edge's two agent
  ids to that render's own rotated points and draws real depends_on
  lines in place of the removed mesh loop.

- feat: Agents Map overview's per-Section angular spread now uses a real
  radial-tree layout instead of an evenly-spaced index fan — operator:
  "the Spread of Agents is Programatic I need some Math Envolved of how
  to make it look like a tree branches not just Spread into everywhere"
  + "Agents that communicate with each others should be near by to
  avoid the mess." Added `assignTreeAngles()` to `layoutAgents.ts`: a
  radial-dendrogram algorithm — every agent nothing else depends on (a
  "leaf") gets an evenly-spaced slot across the Section's own arc span,
  walked via deterministic depth-first traversal so one pipeline's
  leaves always land in one contiguous block (siblings never
  interleave, which is what keeps agents that actually talk to each
  other angularly adjacent); every non-leaf agent then settles at the
  angular midpoint of its own direct children, resolved bottom-up, so a
  multi-stage pipeline visually converges toward its own entry point
  instead of scattering independently. A Merge-style stage (more than
  one `depends_on` entry) only contributes its own arc width under its
  FIRST resolvable parent (the "primary" edge) so a converging merge
  doesn't double-book width under two different parents — every real
  parent still gets its own dependency line (see above), this only
  decides angle ownership. Replaces the old
  `(index / (count - 1) - 0.5) * sectionArcSpanDeg` linear fan. Verified
  via `tsc --noEmit`.

- feat: Agents Map overview now spreads each Agent radially by its own
  pipeline depth instead of a flat per-Type ring — operator: "The Tree
  lets Start by Spreading the Agents between the title and the Hub."
  Added `computeAgentDepth()` to `layoutAgents.ts` (LangGraph-style
  longest-path over each Agent's own `depends_on` edges, memoized, with
  a cycle guard), then linearly maps each Section's own agents' depths
  onto a radial band between the Hub and the Section title (new
  `AGENT_RADIUS_MIN`/`AGENT_RADIUS_MAX` constants, inset from
  `HUB_RADIUS`/`SECTION_TITLE_RADIUS` so depth-0 agents clear the Hub
  and the deepest agents stay clear of the title text); a Section with
  no multi-stage pipeline (every agent its own entry point) places its
  agents at the band's own midpoint rather than collapsing them all onto
  the inner edge. `MockAgent` gained a `radius: number` field
  (`mockAgents.ts`), computed per-agent in `layoutAgents()` and consumed
  by `AgentNode.tsx` (`radiusOverride ?? agent.radius`, replacing the old
  `RING_RADIUS[agent.type]` lookup) and by `AgentsMapCanvas.tsx`'s own
  Hub↔Agent connector-line endpoint math (`agent.radius`, replacing the
  same old lookup) — the Section/Cluster drill-down views are unaffected
  since they already always pass an explicit `radiusOverride`.
  `SECTION_TITLE_RADIUS` was moved from a local const in
  `AgentsMapCanvas.tsx` into an exported const in `polarLayout.ts` so
  `layoutAgents.ts` could import it too. `RING_RADIUS` itself is left in
  place (still used by the — currently always-empty — cluster-marker
  rendering path) per this session's own "collapse the values, keep the
  structure" convention. Verified via `tsc --noEmit`; this pass adds
  radial POSITIONING only — the connector lines still draw Hub-to-every-
  agent-in-Section plus an all-pairs Agent mesh, not yet redrawn to
  actually follow `depends_on`, per the operator's own scoped ask.

- feat: Agent data now carries `depends_on`/`branch_target_agent_id` —
  operator: "Some Agents are connected in a Pipeline some Are Experts
  some Experts are connected to a pipeline, The Data About the Agent
  should have who is connected to who in order to have a tree, Check
  Langraph Data." Same shape LangGraph's own graph model uses (edges
  between nodes; a distinct branch/conditional edge), and the same
  shape this project's own taxonomy-modeled sample data already had
  (`demo_taxonomy.py`'s Job `depends_on`/`branch_target_agent_id`)
  before being flattened out of the demo backend's own data for the
  "150 Agents" pass — brought back here directly on the flat Agent
  shape. `depends_on` = ids of Agents this one structurally receives
  from (a pipeline predecessor; empty for a pipeline's own entry point
  or a standalone Agent); `branch_target_agent_id` = the one Expert
  Agent a "Consult Expert" stage additively branches out to (Store
  still depends only on Merge, not on this — the taxonomy's own
  original "additive, doesn't gate the terminal step" rule, preserved).
  Exposed on both `GET /agents` and `GET /agents/{id}`
  (`src/demo-backend/`), and typed on the frontend's own `AgentSummary`
  (`agentsApiClient.ts`) — not yet READ/rendered anywhere; this pass is
  scoped to the data itself, per the operator's own "so we can START
  having a tree view" framing. Verified live: no dangling references
  (every `depends_on`/`branch_target_agent_id` value across all 155
  Agents resolves to a real Agent id), 6-stage fork/merge and 5-/4-stage
  linear chains both computed correctly.

- fix: Agent node border slimmed down and given a bit of alpha
  (`agents-map.css`) — operator: "The Agents Border should be much
  Slimmer and a bit of Alpha." Was a full 2px opaque ring; now 1px at
  70% opacity. Shared by both fill treatments (autonomous/assisted),
  neither overrides border.

- fix: Agent nodes are now 25% of the Hub's own width (1.25%, was 10%/
  5% compact — `agents-map.css`) — operator: "The Agents Should be 25%
  the size of the Hub." Hub is 5% everywhere now (an earlier pass), so
  25% of that is 1.25%; `.agent-node--compact`'s own width override is
  gone too since it would just re-declare that same number.
- feat: Agent nodes render Filled when `working_mode` is `autonomous`,
  or border-only with a 10%-alpha background otherwise ("Human
  Assistant" — `supervised`/`manual` together) — operator: "The
  Autonmous Agents will be Filled and Human Assistant will be a border
  with a background 10% alpha." `working_mode` is new on the Map's own
  data path: added to `AgentSummary`/`MockAgent`
  (`agentsApiClient.ts`/`mockAgents.ts`), threaded through
  `layoutAgents.ts`, and now included in the demo backend's `/agents`
  summary response too (`sample_data.py`'s own `working_mode` field
  existed already, just wasn't exposed outside the full per-agent
  detail fetch — the real backend's own `list_agents()` already
  included it). Demo data given real variety across all 3 modes (114
  autonomous / 39 supervised / 2 manual across 155 agents) so the new
  split is actually visible, not just theoretical — mutating/consulting
  pipeline stages (Store, Consult Expert) default to supervised, and
  Security/Compliance Experts to manual.

- feat: Section hover now covers the WHOLE wedge between the Hub and
  its title (`AgentsMapCanvas.tsx`, new `describeAnnularSector()`
  helper in `polarLayout.ts`) — operator: "the Section Hover is the
  whole Area between the Hub and the Title." Previously only the Hub's
  own small hit-region and the title text were independently hoverable,
  with a dead gap between them; a new invisible SVG annular-sector path
  per Section (from `HUB_RADIUS` out to `SECTION_TITLE_RADIUS`, spanning
  the angular midpoint to each neighboring Section) now fills that gap.
  Sits beneath every HTML node (Hub/Agent/title all carry their own
  explicit `z-index`, this SVG doesn't), so hovering directly on one of
  those still resolves to its own handler first — the wedge only ever
  catches the previously-dead space around them.

- fix: Agent↔Hub connector lines now terminate at the Hub's actual EDGE,
  not its center (`AgentsMapCanvas.tsx`) — operator, correcting the
  previous pass's own read of this: "The Lines should Reach the Edge of
  the Hub not the Center of the hub." Since each Agent sits at a
  different angle from the Hub, this needed real per-line direction
  math (new `pointTowards()` helper, `polarLayout.ts`) rather than the
  KB↔Hub spoke-line's own trick of subtracting a fixed radius along one
  shared polar ray — that only works because the spoke line always
  travels along that exact ray; an Agent↔Hub line doesn't.

- fix: removed the Type-grouped crowding cap / cluster-marker overflow
  (`layoutAgents.ts`) — operator: "remove the Agents Grouping the Old
  Logic." Every Section's own agents now fan out individually,
  uncapped, instead of collapsing an over-6-per-(Section,Type) group
  into a "+N" cluster marker. That cap was keyed to
  `RING_RADIUS[agent.type]` making visual sense of "too many dots
  overlapping on the same ring"; now that `RING_RADIUS` collapsed to
  one shared radius for every Type (previous pass), a per-Type cap no
  longer maps to anything visible. `ClusterMarker`/`ClusterDrilldown.tsx`
  stay in place, unreachable (`clusters` is now always `[]`) rather
  than torn out — same reversible "collapse the values, keep the
  structure" pattern as the `RING_RADIUS` change itself. Confirmed (via
  code review, not live browser — verification is the operator's own
  from here) that Agent↔Hub connector lines were already targeting the
  Hub's true center point (`HUB_RADIUS`, unmodified) both before and
  after this change — documented explicitly in `AgentsMapCanvas.tsx`
  per the operator's own "Lines... Goes to the Hubs Center" note, no
  functional change needed there.

- feat: every Section now carries its own `color`/`icon` (operator,
  2026-08-15: "every section Should have its own Color and Icon, The
  Hub should Match the Color of the Section the Hover effect of the
  Section Change the Section title to that Same Color") — reuses the
  same curated color palette/Material Symbols icon language already
  established for Agents (`VisualPicker.tsx`), not a second system.
  Demo backend's 8 Sections all populated (`sample_data.py`). Threaded
  through `SectionSummary`/`AgentSection` (`layoutAgents.ts`/
  `mockAgents.ts`) into: `SectionHub.tsx` — the Hub's border/glow/icon
  color (`--hub-color`) and its rendered icon (was always a fixed
  "hub" glyph, now falls back to it only when a Section has none set);
  `AgentsMapCanvas.tsx`'s Section title — the underline accent bar
  always uses the Section's color, and hovering now tints the title
  text/glow to that same color (`--section-color`) instead of the
  fixed `--color-accent` every Section shared before.

- feat: Section Hub hover glow (`agents-map.css`) — ported from
  html-prototype/agents-map-skilltree-exploration.html's own
  `.skillmap-tree-hub:hover`/`smGlow` pulsing box-shadow, operator:
  "Bring the Hover Effect of the Section from the Prototype." Also
  triggers from `.hub-hit-region`'s own hover (the oversized invisible
  click target around the Hub), not just a precise hover on the small
  visible icon.
- fix: Agent connector lines (`.cluster-line`, Hub↔Agent and
  Agent↔Agent) are now white (`var(--color-text)`, was
  `var(--color-accent)`) and slimmer (`stroke-width` 0.5→0.25) —
  operator: "Lines that Connects Agents should be White Slimmer."
- fix: removed the Worker/Producer/Expert position-split — every Agent
  Type now shares one `RING_RADIUS` (32, was 30/45/50 per Type),
  noticeably closer to the Hub (radius 21) than the old spread —
  operator: "we have a logic to split Workers, Producers and Experts in
  Differnt Location Remove that login for now" + "Bring Agents that
  Connects to the hub Directly Closer." The visual ring guides
  (`ring-circle`/`ring-label`) were already removed in an earlier pass,
  which is exactly why this per-Type split had started looking
  arbitrary with nothing left marking what it meant. Still keyed by
  `AgentType` (`polarLayout.ts`) so re-introducing real separation
  later is a one-line change, not a call-site rewrite.

- fix: KB↔Hub connector-line endpoints (`KB_EDGE_RADIUS`/
  `HUB_VISUAL_RADIUS`, `AgentsMapCanvas.tsx`) updated to match the KB's
  and Hub's own real current sizes — operator: "the Connections to the
  Hub need to reach the Vault That is now Broken when we did the
  Modification." Both constants were still keyed to the OLD, larger
  node sizes (34%/6% width) from before earlier passes shrank them
  (25.5%/5%), so the lines undershot the nodes' real edges, leaving a
  visible gap. Recomputed: `KB_EDGE_RADIUS` 17→12.75, `HUB_VISUAL_RADIUS`
  3→2.5 (the Hub-side value was already stale too, same class of bug,
  fixed alongside).
- feat: Section Hub renders a "hub" Material Symbols icon instead of
  its text label (`SectionHub.tsx`) — operator: "Replace the Hub Text
  with an Icon." Every Hub uses the same fixed glyph for now (no
  per-Hub icon field exists yet, unlike Agents); the real label moves
  to `aria-label`/`title` so it's still available on hover and to
  assistive tech.
- feat: demo backend Agent data enriched with icons and richer
  descriptions (`src/demo-backend/sample_data.py`) — operator: "Some
  Agents will have Icons some will not update the Agents Data to have
  Icons and Description... as the new UI still Looks for Worker
  Capture and Expert" (i.e. within the existing flat `type`/`section_id`
  contract, not the taxonomy's own Agent/Pipeline/Job shape). All 8
  generated Experts + the Fetch/Store stage of every generated Pipeline
  + 4 of the 5 hand-authored Agents now carry a real Material Symbols
  icon (68 of 155 total); the rest (`Deal Tracker`, every Classify/
  Merge/Consult-Expert/Summarize/Enrich stage) stay icon-less on
  purpose, exercising both the icon-glyph and plain-dot render paths.
  Every stage's `settings` "Purpose" text is now a real per-stage-kind
  description instead of one generic placeholder string.

- fix: Agents Map default overview now renders visually smaller/zoomed
  out (`transform: scale(0.72)` on `.explore-zoom-overview`,
  `agents-map.css`) — operator, 2026-08-15: "The Map is big it was
  zoomed out in the Protype do the same," matching the skilltree
  prototype's own resting `--tree-scale: 0.55`. Purely visual — node
  positions are percentage/viewBox-based, unaffected by an ancestor
  `transform`. Scoped to the true overview only: the Section/cluster
  drill-down's own canvas never carries the `explore-zoom-overview`
  class, so it stays full-size once focused (verified live: overview
  504px vs. its own 700px base = 0.72x; drill-down still exactly 700px,
  `transform: none`).

- feat: Agents Map top bar (`AgentsMapPage.tsx`/`agents-map.css`) —
  ported from html-prototype/agents-map-skilltree-exploration.html's
  own `.skillmap-topbar`, fitted to this app's actual chrome (sticky
  within `.main`'s own scroll container, not viewport-`fixed`, since
  there's no other fixed chrome here; center slot shows the page title
  "Agents Map" instead of a second "Second Brain" wordmark — the
  Sidebar already owns that; the prototype's dead fullscreen-toggle
  button is dropped). Left: existing search + doctrine ("?") triggers,
  now inside a proper bar instead of a plain `<h1>`+toolbar stack.
  Right: live counts ("N sections · M agents mapped"). Verified live:
  155 agents · 8 sections rendered correctly, search still lists all
  155.
- fix: dashed section-boundary divider lines and the WORKER/EXPERT/
  PRODUCER `ring-label` text removed from the Agents Map background too
  (`AgentsMapCanvas.tsx`) — operator, second pass: "The map still Have
  Dashed Separator and a Text for Worker, Producer and Expert in the
  background Shouldn't be there." The prior pass removed the radar-
  spoke/ring-circle/boundary-circle grid but kept these two, reasoning
  they were "functional dividers/labels, not decorative" — operator
  says otherwise; both are gone now too, confirmed via DOM query
  (`0` remaining `.section-boundary`/`.ring-label` elements).

- fix: dashed radar-spoke/ring-circle/boundary-circle background grid
  removed from the Agents Map (`AgentsMapCanvas.tsx`) — operator,
  2026-08-15: "the Map still have a Dashed Background that should not
  be there." The skilltree prototype this app's other recent visual
  ports (hover-dim, ghost-name, rotor, chevron nav) all come from has
  no such radial wheel-grid at all. `section-boundary` (the real
  per-Section divider lines) is unrelated and stays.
- feat: demo backend now serves 155 agents (5 hand-authored + 150
  generated) across 8 Sections (`src/demo-backend/sample_data.py`) —
  the same 150-entity spread originally built for the real backend's
  taxonomy-shaped `/demo/agents`/`/demo/pipelines`
  (`src/backend/app/business/demo_taxonomy.py`), reshaped flat to match
  this backend's own today's-contract Agent shape (no Pipeline/Job/DAG
  concept exists in the flat model, so each generated "stage" just
  becomes its own ordinary Agent). 5 new Sections added (Support, HR,
  Finance, Legal, Marketing) alongside the existing Capture/Sales/
  Productivity; `Section.agent_ids`/`Provider.agent_ids` are now
  derived from `AGENTS` at import time instead of hand-maintained.
  Verified live: 155 agents, 8 Sections, density clustering (REQ-SB-38)
  correctly collapsing the overflow into cluster markers at this scale.
- fix: every user-visible `name` in the demo backend's sample data no
  longer contains the word "Demo" (operator, 2026-08-15: "Remove the
  word Demo as It might affect the UI") — e.g. "Email Capture (Demo)"
  → "Email Capture", "Compass (Demo)" → "Compass". `id` values (e.g.
  `demo-email-capture`) are untouched — never rendered as text anywhere
  in the UI, only `name` is.

- feat: frontend now points at the standalone demo backend by default
  (`src/frontend/.env.local` → `http://127.0.0.1:8090`, was the real
  backend on 8001) — per the operator's own working agreement this
  session: UI work happens against the demo backend's replica API +
  demo data; the real backend only grows the endpoints the UI actually
  needs, once the UI itself is settled.
- feat: "Background Agents" rail removed from the Agents Map
  (`AgentsMapCanvas.tsx`) and moved to its own page, `/crawlers`
  (`src/frontend/src/pages/CrawlersPage.tsx`), reached via a new
  Sidebar nav item — independent fetch/filter (`is_background_agent`),
  not derived from the Map's own `layoutAgents()` call, since a
  Crawler was never placed on the ring layout to begin with. Demo
  backend's `demo-email-capture` sample agent flagged
  `is_background_agent: true` so the new page has something to show.

- feat: Visual tab icon picker switched from plain emoji glyphs to the
  self-hosted Material Symbols Outlined icon font (Google Fonts —
  operator, 2026-08-15: "This will Beautify the UI Alot"). Font
  downloaded once from `fonts.gstatic.com` to
  `src/frontend/public/fonts/MaterialSymbolsOutlined.woff2` and served
  locally via a new `@font-face`/`.material-symbols-outlined` rule in
  `tokens.css`, matching the existing Plus Jakarta Sans/Marcellus
  no-runtime-CDN-fetch convention exactly — no live Google Fonts link.
  `visualOptions.ts`'s `VISUAL_ICONS` now carry a Material Symbols
  ligature name (e.g. `"psychology"`) instead of a raw emoji character;
  `VisualPicker.tsx` and `AgentNode.tsx` render it inside a
  `.material-symbols-outlined` span. Verified live: the font loads on
  first real use (browsers load `@font-face` lazily) and renders
  correctly both in the picker grid and on the Agents Map node itself.

- feat: demo taxonomy backend (`GET /demo/agents`/`GET /demo/pipelines`)
  bulk sample data — 150 procedurally generated entities on top of the
  original hand-authored worked example: 10 six-stage + 10 five-stage +
  8 four-stage Pipelines (142 Jobs total) + 8 standalone Experts, spread
  across 7 generated Hubs (`src/backend/app/business/demo_taxonomy.py`).
  6-stage Pipelines reuse the worked example's own fork/merge/branch-to-
  Expert DAG shape; 5- and 4-stage are linear. Built for real UI density
  checks against the taxonomy model, per the operator's own request.
- feat: standalone demo backend Sections now carry a `slogan` field
  (`src/demo-backend/sample_data.py`), reusing the html-prototype's own
  real per-section slogans verbatim where the Section name matches.
  Tagged `PORT-TO-REAL-API` in-code — the real `section_registry.py`/
  `sections_router.py`/`SectionSummary` don't carry this field yet;
  port it there once Section subtitles go live for real.

- fix: Agents Map canvas (`.agents-map-canvas`, `src/frontend/src/styles/agents-map.css`)
  no longer has a filled disc background/shadow — matches
  `html-prototype/styles.css`'s own `.theme-skilltree .agents-map-canvas`
  pass ("nodes now float directly over the starfield/page background").
  The ring/boundary/radar-spoke lines and WORKER/EXPERT/PRODUCER ring
  labels now sit directly over the page background instead of an opaque
  plate.
- fix: Section titles (`.section-title`) now render in the serif
  `--font-serif` (Marcellus) instead of the default `--font-sans`,
  matching the distinctive-heading treatment the prototype already uses
  for its sidebar wordmark/About-panel heading/ghost-name watermark.

- feat: standalone demo backend (`src/demo-backend/`) — a separate
  FastAPI process (own `.venv`, own `requirements.txt`, port 8090,
  `tools/run-demo-backend.cmd`, `.claude/launch.json` entry
  `second-brain-demo-backend`) mirroring today's real endpoint contract
  (`/agents`, `/agents/{id}`, `PATCH /agents/{id}`, `/agents/{id}/skills`,
  `/agents/{id}/history`, `/agents/{id}/chat`, `/agents/{id}/schedules`,
  `/sections`, `/providers`, `/skills`, `/vault-search/scope-suggestions`)
  with plain in-memory sample data (`sample_data.py`) — no Outlook,
  Compass, vault I/O, or Skill/Tool execution, no persistence across
  restarts. Point the frontend at it by swapping in the new
  `src/frontend/.env.demo` (`VITE_API_BASE_URL=http://127.0.0.1:8090`)
  in place of `.env.local`. Purpose: let UI work continue against a
  fully-populated, zero-dependency backend so gaps surface early,
  without touching or depending on the real `src/backend` app at all —
  the real app gets the actual missing APIs built later, once the UI
  itself is settled.

- feat: Agent Visual tab — icon + color customization, applied live on
  the Agents Map. Backend: `icon`/`color` fields added to
  `GET /agents`, `GET /agents/{id}`, and `PATCH /agents/{id}`
  (`src/backend/app/api/agents_router.py`), backed by a new
  `agent_visual_registry.py` business module + `agent_visuals.json`
  persisted store (`vault_writer.py`), mirroring `working_mode_registry.py`'s
  exact shape. Omitting `icon`/`color` in a PATCH leaves them unchanged;
  an explicit empty string clears the override back to default (the
  panel's "Reset to default" button). Frontend: a shared
  `VisualPicker.tsx` component (14-glyph icon grid + 10-swatch color
  row, `visualOptions.ts`) reused by a new "Visual" tab in
  `AgentDetailPanel.tsx`; `AgentNode.tsx`/`layoutAgents.ts`/
  `mockAgents.ts` thread `icon`/`color` through to the map so a chosen
  icon renders on the node and the chosen color overrides `--node-color`.
  Built as an informal spike directly in `src/frontend`/`src/backend`
  (not the static `html-prototype/`) — one reusable component instead of
  the 6 hand-duplicated prototype copies, per the operator's own
  redirect this pass.

- feat: demo taxonomy backend — `GET /demo/agents` and `GET /demo/pipelines`
  (`src/backend/app/api/demo_taxonomy_router.py`,
  `src/backend/app/business/demo_taxonomy.py`), an in-memory sample-data
  fixture shaped to `ADR-041`'s Agent/Pipeline/Job/Hub taxonomy — not a
  persisted registry. Returns 3 demo Agents (2 Experts, 1 standalone
  Producer) and one demo Pipeline, the "Email Capture Pipeline", modeled
  directly on the operator's own worked example: pull → fork into
  body-summary + attachment-summary Jobs → merge → additively branch to
  the Ops Expert → store (Store is not gated on the Expert branch,
  matching `ADR-041`'s "additive, not a replacement for the terminal
  step" rule). Built to let the frontend start proving out the new
  taxonomy's real shape with live sample data, per the operator's own
  sequencing rule (one concrete Pipeline before the generic Builder).

- fix: Agents Map Section Hub now renders at the identical visual size in
  both the default Map view and the focused Section drill-down
  (`src/frontend/src/styles/agents-map.css`) — removed the
  `.explore-drilldown .hub-node { width: 8% }` override that used to
  scale the Hub up on focus, and reduced the base `.hub-node` width from
  6% to 5% ("a bit smaller" per the operator). Only the surrounding
  layout (agent ring radius) changes on zoom-in now, not the Hub itself.
  Ported from the same fix already applied to the design prototype
  (`html-prototype/styles.css`'s new `.skillmap-hub-group` counter-scale
  wrapper) — done directly in the real app this time, since the operator
  redirected this pass ("we are doing it 6 times to maintain the visuals
  ... in App we need to do it once for all the elements") away from
  further static-prototype duplication.

- docs: **`ADR-041`** — Agent/Pipeline/Job/Hub domain-model taxonomy
  adopted (operator-driven discussion, "this is getting messy... let's
  discuss all types of Agents"), superseding `ADR-040`'s fixed Pull/Tag/
  Link/Store agent-chain shape. A Pipeline is now a user-extensible DAG
  of lightweight Jobs (own prompt + Skill(s), not a full Agent identity),
  supporting fork/merge/branch-to-Expert-consultation, executed on
  LangGraph (already a real dependency, `ADR-015`) via a native React
  Flow builder in the existing frontend — external visual-builder tools
  (LangFlow/Flowise) explicitly considered and declined. `REQ-SB-53` and
  its 3 sibling stories (Email/Meetings/To-Do capture split) are parked,
  not cancelled, pending a re-spec against this model. Directional/
  foundational only — no code changed by this pass. Full reasoning:
  `Implementation/Architecture/ADR.md` → `ADR-041`;
  `Implementation/Architecture/architecture.md` → "Agent / Pipeline /
  Job / Hub Domain Model — Taxonomy"; `MEMORY.md`'s own matching Decision
  entry.

- feat: **`REQ-SB-52-US-01`** — App-wide dark palette + real Plus Jakarta
  Sans / Marcellus typefaces, `tokens.css`-only swap
  (`src/frontend/src/styles/tokens.css`). All 9 `--color-*` tokens
  swapped to the dark SkillTree palette (`--color-bg: #0e1118`,
  `--color-surface: #171a22`, `--color-surface-raised: #1f2430`,
  `--color-border: rgba(233, 228, 214, 0.1)`, `--color-text: #e9e4d6`,
  `--color-text-muted: #b9b4a6`, `--color-accent: #c58b5f`,
  `--color-accent-muted: rgba(197, 139, 95, 0.16)`, `--color-on-accent:
  #0e1118`); `--agent-color-worker/-producer/-expert` and
  `--color-success/-warning/-danger` left byte-identical (regression
  guard). `--font-sans` repointed to lead with `"Plus Jakarta Sans"`; new
  `--font-serif` token added, leading with `"Marcellus"`. Both fonts load
  from real local WOFF2 files (`src/frontend/public/fonts/
  PlusJakartaSans-Variable.woff2`, `Marcellus-Regular.woff2`, copied
  verbatim from `html-prototype/fonts/`) via two new `@font-face` rules —
  no CDN/network font request. Marcellus applied to the sidebar "Second
  Brain" wordmark (`.sidebar-header h2` in `src/frontend/src/styles/
  shell.css`). Cascades to all 6 real screens (My Day, Settings, System
  Health, Agent Activity, Browse & Search, Agents Map) with zero
  per-screen CSS edits, since every screen already consumed color
  exclusively via `var(--color-*)`. All 6 locked ACs verified live
  against the real running dev server across all 6 routes (screenshots,
  computed-style, and network evidence).
- feat: **`REQ-SB-52`** — Real Agents Map (`src/frontend/src/features/
  agents-map/`) ported 3 pieces from the exploration prototype directly
  into the canonical app (operator, 2026-08-15: "Port the CSS, the KB new
  Design and KB new Lines we Built Leave the Rest till We finish the
  prototype" — a deliberately narrow port; the prototype's Sections
  View/Agent-in-Focus work stays prototype-only for now). Colors adapted
  to this app's own real light-theme tokens (`--color-accent`/
  `--agent-color-*`), never the prototype's own dark-theme values —
  the two apps use different themes entirely.
  1. **`KnowledgeBaseNode.tsx`** — the hand-authored 23-neuron/42-synapse
     mesh is replaced with a seeded-random 220-dot constellation (same
     deterministic LCG recipe as the prototype), fully transparent at
     rest (no border/background/glow/label), with the same hover-rotate-
     and-freeze-in-place behavior (not reset) translated from the
     prototype's vanilla-JS `mouseenter`/`mouseleave` handlers into a
     React ref + `useState`.
  2. **`.hub-node`** (`agents-map.css`) — replaced the dashed-border/
     tinted-fill treatment with the prototype's real `.rootb` recipe: a
     thin 1.5px mostly-transparent ring plus a soft wide low-opacity
     box-shadow halo, both keyed off the existing `--hub-color` custom
     property (zero change to the Worker/Producer/Expert color-keying
     mechanism already in place).
  3. **KB<->Hub `.spoke-line`s** (`AgentsMapCanvas.tsx`) — endpoints moved
     from literal canvas-center/hub-center to each circle's own real EDGE
     (`KB_EDGE_RADIUS=17`, `HUB_RADIUS(21) - HUB_VISUAL_RADIUS(3)`), and
     each line gained two traveling `<circle>` dots via `<animateMotion>`
     (one Hub->KB, one KB->Hub), with desynced per-Section timing derived
     from each section's own index — since the real app's Section count
     is dynamic (unlike the prototype's fixed 6), timing is computed, not
     hardcoded per line.
  Verified live: TypeScript build clean (`tsc -b --noEmit`), zero console
  errors, the dot constellation renders (220 circles confirmed via direct
  DOM query), hub border/shadow computed styles match the target values
  exactly, spoke-line endpoints land at the real edge coordinates (not
  center), hover-spin-and-freeze confirmed by measuring actual rotation
  advance over a real 300ms hover then a frozen value after mouseleave,
  and Hub click -> Section drill-down still opens correctly (pre-existing
  behavior, unaffected). `src/frontend/src/features/agents-map/
  KnowledgeBaseNode.tsx`, `src/frontend/src/features/agents-map/
  AgentsMapCanvas.tsx`, `src/frontend/src/styles/agents-map.css`.

- design: **`REQ-SB-52`** — Agents Map exploration prototype, connector
  lines now genuinely touch the agent dots (operator, 2026-08-15: "No
  Lines are not connected to the Agents Circle" — the edge-to-edge
  coordinates from the previous pass were geometrically correct against
  each node's OWN `--nx/--ny` anchor point, confirmed via direct
  `getScreenCTM()` measurement, but the dot ITSELF wasn't rendered at
  that point: `.skillmap-node` was a `flex-direction:column` button
  stacking the dot ABOVE the label with a 4px gap, and its own
  `translate(-50%,-50%)` centered that WHOLE dot+label stack on
  `--nx/--ny` — pushing the dot's actual visual center up and off the
  line's real endpoint by roughly half the label's reserved height, ~17-
  27px depending on section). Fixed at the source, not by re-tuning
  coordinates again: `.skillmap-node` is now sized to exactly the dot's
  own 17x17 box (flex layout removed) so the button's own centering
  transform lands the DOT ITSELF on `--nx/--ny`; `.skillmap-node-label`
  moved to its own `position:absolute; top:100%` below the dot instead of
  sharing the centering flexbox. Re-verified live via the same
  `getScreenCTM()` technique: every one of the 14 connector lines now
  ends within 0.1px of its own node dot's real 17px screen radius (was
  ~40-46px off). Also applied the operator's separate styling request for
  this pass while investigating (thinner, alpha ~0.7, ivory/white instead
  of the debugging-pass copper). Only `.skillmap-node`/`-dot`/`-label`
  CSS changed — the 14 `<line>` coordinate values from the prior edge-to-
  edge pass are untouched, since they were already correct.
  `html-prototype/styles.css`.

- design: **`REQ-SB-52`** — Agents Map exploration prototype, all 6
  Sections given real fixture agents (operator, 2026-08-14: "Add some
  Agents with Connectors to Some Sections Agents should be the 3 types
  Expert, Producer and Worker" — Sales/Products/Technical went from
  genuinely empty to 3 agents each, one of each type, richer test
  coverage for the Sections View visuals). New card-detail panels/search
  entries for all 9 new agents (`deal-capture`/`pipeline-expert`/
  `proposal-drafts`, `feedback-capture`/`roadmap-expert`/
  `changelog-drafts`, `incident-capture`/`systems-expert`/
  `runbook-drafts`) — total fixture now 14 agents (was 5), every counts
  display updated. **Real, live-discovered rendering bug found and fixed
  in the same pass** (operator: "Still missing the lines (links between
  Agents and then Hubs To make it a Tree)"): the hub-to-agent
  `.skillmap-connector` lines were never actually painting AT ALL — their
  parent `.skillmap-tree-lines` SVG is a `width:0;height:0` box (this
  file's own established zero-size-anchor pattern, which reliably lets
  plain HTML children overflow and paint in every browser) but this
  rendering engine clips an SVG's OWN content to that literal 0x0
  viewport regardless of `overflow:visible` — confirmed directly live
  (even a blunt `stroke:red;stroke-width:10px;opacity:1` override was
  still fully invisible, despite a real, correctly-positioned
  `getBoundingClientRect`). Fixed by giving each `.skillmap-tree-lines`
  real 400x400px dimensions (`left/top:-200px`) paired with a matching
  `viewBox="-200 -200 400 400"` so the internal coordinate system's
  (0,0) still means "hub center" exactly as before — zero changes needed
  to any of the 14 real `<line>` coordinate values already authored. Two
  smaller, real secondary issues fixed in the same investigation (kept,
  not reverted, even though they weren't the root cause): connector
  stroke switched from `var(--sm-text)` (same near-white as the Sections
  View's own ghost-name text it visually crosses) to the accent copper;
  and a `stroke-dashoffset` entrance `animation` on focus was removed
  outright after confirming it gets stuck at its invisible starting frame
  forever in this environment — the same frozen-animation-timeline
  artifact already documented for the KB hover-spin, now also confirmed
  to affect a plain one-shot `@keyframes` entrance effect, not just
  `infinite` ones. `html-prototype/agents-map-skilltree-exploration.html`,
  `html-prototype/agents-map-skilltree-exploration.js`,
  `html-prototype/styles.css`.

- design: **`REQ-SB-52`** — Agents Map exploration prototype
  (`html-prototype/agents-map-skilltree-exploration.html`), Sections View
  pass: clicking a Section now opens a genuinely separate full-screen view
  instead of the previous in-place dim/recenter-and-scale treatment
  (operator, 2026-08-14: "The Map will be Hidden, and now this is a new
  view with a new layout we call it Sections Views"). The Default map (KB,
  all 6 hubs, the rotor, hub-to-KB connector lines, the rotation arrows)
  is hidden outright while a Section is focused — not dimmed — and the
  focused Section's own hub+tree jumps to one fixed stage anchor
  (bottom-half center) at a bigger scale, alongside a new large serif
  "ghost-name" watermark (real value checked live on the reference's own
  focused-department screen: full-color text sitting behind the tree, not
  literally faded) and real vertical-writing-mode edge-department labels
  (`writing-mode:vertical-rl`, 13px, 2.86px letter-spacing, uppercase —
  also checked live) replacing the previous plain horizontal ones. The
  "ALL SECTIONS" back link and edge-nav arrows are unchanged/reused; the
  arrows still cycle between Sections without returning to the map first.
  Collapsed 12 hardcoded per-Section CSS position overrides (6 world
  recenter + 6 title position rules) down to 2 generic ones now that only
  one Section is ever visible at a time. Also fixed two bugs found during
  this pass: a duplicate `transition` declaration on `.skillmap-title`
  that silently dropped its own `left`/`top` transition, and hover-driven
  `.dimmed`/`.is-hovered` classes getting stuck across a focus/back cycle
  (the DOM hide/show breaks the `mouseout` `relatedTarget` check that
  normally clears them — both `focusSection`/`unfocus` now clear that
  state explicitly). `html-prototype/agents-map-skilltree-exploration.html`,
  `html-prototype/agents-map-skilltree-exploration.js`,
  `html-prototype/styles.css`.

- design: **`REQ-SB-52`** — Agents Map Visual Redesign (SkillTree-Inspired
  Theme), designer REDO pass (supersedes the entry immediately below —
  operator rejected pass 1 as too conservative: "No No I want to Copy
  everything The Layout the Animation the Looks and Colors Forget what we
  have"), flagged for human browser sign-off (never auto-advanced). A real
  rebuild of the visual/animation system against a deeper, second
  extraction of the reference site's own real CSS source — still zero
  interaction/data/markup-structure change (Section-Hub drill-down, cluster
  markers, agent detail side panel/tabs/chat/history, entrance animation,
  all 6 state-switcher states, agents-map.js all UNTOUCHED). Structural:
  `.agents-map-stage` is now `position:fixed; inset:0` (true full-viewport
  canvas, was the bounded box pass 1 kept), achieved via stacking-context
  math with zero HTML restructuring. Full real palette
  (`--bg:#0E1118`/`--ivory:#E9E4D6`/`--ivory-2`/`--ink-2`/`--ink-3`/
  `--copper:#C58B5F` accent/`--line`/`--glass`) replaces pass 1's 2-token
  minimal swap. Real named keyframes: `nodepop` (staggered bounce pop-in,
  reusing each node's own existing inline animation-delay), `livepulse`
  (renamed from `agentActivityGlow`, REQ-SB-42, same recipe — now also
  drives a hover/selected-node glow), `drawline` (connector lines
  self-draw via `stroke-dashoffset`), `hspin` (KB inner mesh slow
  spin+drift, folded into one keyframe), `chevnudge` (new edge-nav
  chevrons), `bpulse` (warning badges). Glass blur bumped to the real
  extracted amounts: side panel/card 14px → 16px, zoom toolbar 14px → 12px
  (repositioned fixed/right/bottom, matching the reference exactly). New
  net-new `.map-edge-nav` component (fixed, vertically centered,
  hover/focus-revealed chevron pair) added once per state's drill-down
  group (5 insertion points). Typography: h1 now real
  27px/.12em-letter-spacing/400-weight Plus Jakarta Sans; Marcellus (the
  reference's second loaded font) adopted for the sidebar's own "Second
  Brain" wordmark. Several items explicitly flagged as designer judgment
  calls, not silent assumptions — see `REVIEW-QUEUE.md` and both files'
  own top-of-file breadcrumbs for the full list.
  `html-prototype/agents-map.html`, `html-prototype/styles.css`.

- design: **`REQ-SB-52`** — Agents Map Visual Redesign (SkillTree-Inspired
  Theme), designer pass (SUPERSEDED by the redo entry above), flagged for
  human browser sign-off (never auto-advanced). Pure re-skin of the
  already-approved `agents-map.html`
  prototype — no interaction/data/markup-structure change. New
  page-scoped `body.theme-skilltree` dark charcoal-navy (`#20242D`) / warm
  cream (`#E9E4D6`) palette (CSS custom-property override only, zero other
  screens touched); a 60-dot CSS-only animated `.starfield` background
  layer; the agent detail `.side-panel` and this page's `.card` blocks
  re-skinned as translucent near-black glass cards
  (`rgba(14,17,24,.85)`, 10px corners, flat/no-shadow); a new net-new
  `.map-zoom-toolbar` component (−/level/+/Fit/help, visual chrome only,
  no zoom logic) added to all 6 state-switcher demo states' map
  viewports. Typeface: `"Plus Jakarta Sans"` named first in the font
  stack with the existing system-font fallbacks kept after it (no
  CDN/network font request — documented judgment call, this prototype has
  no build step). Values extracted live from the reference site
  (`skilltree.altari.ai`) per the PRD's own breadcrumb; derived shades
  (surface/border/muted/accent brightness/warning/success/danger) are the
  designer's own proposal, explicitly flagged, not extracted. See
  `REVIEW-QUEUE.md` and `agents-map.html`'s/`styles.css`'s own
  top-of-file breadcrumbs for full rationale.
  `html-prototype/agents-map.html`, `html-prototype/styles.css`.

- feat: **`REQ-SB-49-US-01`** (`SPRINT-046`, `T01`) — Cockpit Inline
  `@agent_id` Mention: typing `@agent_id` (or `@Agent Name`, case/
  whitespace-insensitive) in a Meeting/Inbox Cockpit chat message and
  sending it brings that agent into the shared thread via the exact same
  `bringInAgent` call the left panel's "+ Bring in" button already uses —
  no second bring-in code path. A live, prefix-filtered `@`-mention
  suggestion dropdown renders real, registry-derived candidates while
  typing. The chat `<input>`'s own `disabled={!hasExperts}` is removed
  (the concrete fix for a real gating conflict the architect flagged); the
  Send button's own gate is relaxed so a resolvable in-message mention can
  itself satisfy the "has an expert" precondition. An unmatched `@token`
  is left as plain literal text, never a fabricated match. Wired against
  `REQ-SB-51-US-01`'s already-landed Background-Agent-filtered
  `bringInCandidates` list. `src/frontend/src/features/cockpit/Cockpit.tsx`
  only, zero backend changes. Verified live end-to-end against all 5
  locked ACs via a real running frontend/backend and a from-scratch CDP
  browser session. Full reasoning: `MEMORY.md`;
  `Implementation/Tasks/REQ-SB-49-US-01-T01`'s own Implementation Log.

- feat: **`REQ-SB-49-US-02`** (`SPRINT-046`, `T01`-`T06`) — Cockpit
  Person-Directed Instruction (`@PersonName`): a Cockpit-brought-in
  Expert's own free-text instruction naming a real person (e.g.
  "`@AhmedMoussa` is leaving the company, update his note") now proposes
  a real, never-silently-applied edit to that person's real Person note,
  subject to the invoking agent's own working-mode gate, per `ADR-038`. A
  new bound tool `propose_person_note_update` is intercepted in
  `graph.py`'s `_route_after_model` before the generic `execute_tools`
  node (mirrors `record_knowledge_gap`), this graph's first
  CONDITIONALLY-bound tool (gated on `skill_registry.has_skill_access`).
  A real match resolves via a new read-only
  `people_extraction.find_person_note_by_name`, then dispatches through
  `skill_registry.invoke_skill(..., trigger="cockpit_mention")` — a new
  trigger literal, zero new gate branches. A new `mutates: True` Skill,
  `propose_person_note_update` (`skill_tools.py`), granted to
  `people-producer`, branches on a new `_dispatch_skill(...,
  already_approved: bool = False)` seam (forwarded via the same
  signature-introspection pattern as `agent_id`): Supervised mode's
  existing Pending-Approval "Approve" click is already the human
  confirmation (unchanged); Manual/Autonomous dispatch (zero human click
  in its own path) now records an explicitly confirmable/discardable
  in-thread proposal instead of writing immediately — a new
  `app/business/cockpit/person_note_proposals.py` module (create/list/
  confirm/discard, stored in the owning thread's own
  `cockpit_threads.json` record), two new confirm/discard endpoints on
  `cockpit_router.py`, and a new `.chat-proposal`-shaped pending-proposal
  region in `Cockpit.tsx` (reuses the existing quick-research proposal
  pattern verbatim — no new CSS). A mentioned name with no matching
  Person note is honestly reported, never fabricated, never creates a
  note. Two real, live-discovered integration bugs were found and fixed
  in-scope: a new `SKILLS` entry missing the `"tool"` field a sibling,
  already-`Done` sprint had made mandatory (`skill_tools.py`); a save
  race in `threads.send_user_message` that silently clobbered a
  mid-loop-created pending proposal (`threads.py`). Verified live
  end-to-end against all 6 locked ACs — real Python-shell/HTTP calls for
  the deterministic Supervised gate path, real live model calls
  (Compass) for the Manual/Autonomous "propose" path, and a real CDP
  browser session driving the actual confirm/discard UI, including a
  real write to a real Person note on Confirm and a confirmed no-op on
  Discard. `ADR-038` held up exactly as designed under live verification.
  Full reasoning: `MEMORY.md`; each task's own Implementation Log under
  `Implementation/Tasks/REQ-SB-49-US-02-T01`..`T06`.

- feat: **`REQ-SB-47-US-01`** (`SPRINT-045`, `T01`-`T06`, also covers
  `REQ-SB-45`) — Per-Agent Scheduler + Shared Outlook-COM Dispatch Lock: a
  new Schedule tab on `AgentDetailPanel.tsx` (configure/edit/remove/
  run-now/run history), generalized across every agent's own granted
  mutating capabilities, built with the shared serialization guarantee
  that no two Outlook-COM-touching runs ever execute concurrently.
  Backend: new `app/business/agent_schedule_registry.py` (persisted
  composite-key `.second-brain/agent_schedules.json` schedule CRUD, the
  live `AsyncIOScheduler` seam, the shared in-process dispatch lock —
  `dispatch_with_shared_lock`), new paired `vault_writer.py` I/O
  primitives, `app/scheduling/capture_scheduler.py` surgically edited
  (removed its own private lock, now shares `agent_schedule_registry`'s;
  registers one job per persisted schedule alongside the unchanged
  `hourly_capture` job; publishes the live scheduler at startup), a new
  `"scheduled"` trigger literal + Manual-mode silent-skip branch on
  `skill_registry.invoke_skill`, and a new `app/api/
  agent_schedules_router.py` (`GET`/`POST`/`PATCH`/`DELETE` +
  `POST .../run-now`, registered in `app/main.py`). Frontend: new
  `agentSchedulesApiClient.ts`, `skillsApiClient.ts`'s `SkillSummary`
  gains `mutates: boolean`. A real, live-discovered duplicate-history-entry
  defect in the shared dispatch function's own generic outcome-recording
  was found and fixed in-scope (a generic before/after history-length
  comparison, replacing a hardcoded/flag-based exclusion list). Verified
  live end-to-end against all 9 locked ACs, including the shared-lock
  property confirmed via two independent techniques (an in-process
  `asyncio.gather` timing-marker proof, and a real, unplanned HTTP-layer
  race against a genuine multi-minute Outlook-COM backlog run) and a real
  CDP-driven browser session for the frontend. No `/design` pass was run
  for the net-new Schedule tab (disclosed, non-blocking, per the story's
  own Notes) — flagged for human retroactive sign-off. Full reasoning:
  `MEMORY.md`; each task's own Implementation Log under
  `Implementation/Tasks/REQ-SB-47-US-01-T01`..`T06`.

- feat: **`REQ-SB-51-US-01`** (`SPRINT-044`, `T01`-`T06`) — Background
  Agents: a new, explicit, user-settable `is_background_agent` flag
  excludes an agent from every other agent's Hub-routing candidacy and
  the Cockpit's Available Agents bring-in list, while leaving its own
  detail panel/direct chat/direct actions/scheduled runs fully
  unrestricted. Backend: new `app/business/background_agent_registry.py`
  (self-healing default, mirroring `working_mode_registry.py`), a new
  `.second-brain/agent_background_flags.json` sibling store owned by new
  `vault_writer.py` I/O primitives, and a literal 3-agent backfill
  (`email-capture`/`meeting-capture`/`todo-capture` self-heal to `True`
  with zero manual step). `GET`/`PATCH /agents` merge/accept the new
  field. `agent_keywords.list_candidate_agents_for_keyword_match` skips
  any Background Agent inside its existing loop. Frontend: a new shared
  `isBackgroundAgent(agent)` predicate (`agentsApiClient.ts`) filters
  `Cockpit.tsx`'s Available Agents list and partitions `layoutAgents.ts`'s
  ring/clustering input into a new `backgroundAgents` field; a new
  "Background Agents" `.card`/`.item-list` rail on the Agents Map
  (`AgentsMapCanvas.tsx`) renders that set, clicking a row opens the
  normal `AgentDetailPanel`; the Settings tab gained one new "Background
  Agent" checkbox row. Verified live end-to-end against all 9 locked
  ACs, including a real CDP-driven headless-Edge session (checkbox
  persistence across panel close/reopen, a real direct chat reply from a
  Background Agent, and a full un-mark restoration check confirming
  Hub-routing/Cockpit/Map addressability all recover live with no
  restart). No new ADR — an ordinary extension of already-Accepted
  `ADR-014`/`ADR-018` patterns. Full reasoning: `MEMORY.md`; each task's
  own Implementation Log under `Implementation/Tasks/
  REQ-SB-51-US-01-T01`..`T06`.

- feat: **`REQ-SB-46-US-01-T02`..`T05`** (`SPRINT-043`) — completes the
  Agent Creation Wizard Redesign end to end. `CreateAgentWizardModal.tsx`'s
  4 steps now hold ONE shared set of fields (not three parallel per-type
  copies): Step 1 (Name/Type/conditional Description-Expert-only or
  Scope-Worker-only/Section, in-place show/hide, values preserved across
  Type changes), Step 2 (Working-mode selector for every Type, plus
  Producer-only Purpose + single-select output Skill), Step 3 (the REAL
  shared `SkillsTree.tsx` in `mode="select"`, required ≥1 for Worker,
  optional for Expert/Producer — reconciled against its actual shipped
  prop shape, not the task's own illustrative guess), Step 4 (read-only
  summary + a Trigger choice — User/Agent/Schedule, defaulting to User —
  + "Create agent"). Backend: `POST /agents`'s `CreateAgentBody` gains an
  additive `trigger: str | None = None`, recorded via the existing generic
  `settings` kv-list uniformly across all 3 types (`{"key": "Trigger",
  "value": ...}`, defaulting `"user"`) — no new endpoint, no schema
  change. Every per-type submit call sequence (count/order/shape) is
  unchanged from today's shipped wizard, extended only with `trigger` and
  a now-sent `working_mode` (additive param on the existing
  `updateAgentAssignment` PATCH). Verified live end-to-end against all 11
  locked ACs via a real CDP-driven headless-Edge session plus direct
  backend HTTP cross-checks: all 3 agent types (Expert/Worker/Producer)
  created successfully through the full new wizard flow, each
  byte-for-byte cross-checked against a parallel direct-API-call agent of
  the same type (Expert) or independently confirmed correct
  capabilities/scope (Worker/Producer); Schedule/Agent Trigger choices
  confirmed metadata-only with an honest placeholder and no behavior
  change; full-chain validation-blocking and mid-wizard-close-discards-draft
  scenarios both confirmed. Story `REQ-SB-46-US-01` and `SPRINT-043` both
  `Done`.
- feat: **`REQ-SB-46-US-01-T01`** (`SPRINT-043`) — Agent Creation Wizard
  Redesign: new bottom-right `.map-fab` on the Agents Map opens a new
  centered popup modal (`CreateAgentWizard.tsx` renamed to
  `CreateAgentWizardModal.tsx`) with a visual 4-step progress bar
  (`.wizard-step-bar`, step 1 current by default) — structurally distinct
  from the existing agent-detail side panel's slide-in overlay (zero
  shared class names, confirmed live). The Settings-page `+ Create agent`
  entry point (`CreateAgentCard.tsx`) is retired; the Map FAB is now the
  sole entry point. Existing per-type form logic preserved unchanged
  inside the new shell — `T02`-`T05` regroup it into the real 4 steps.
  Verified live via a real CDP-driven headless-Edge session (FAB → modal →
  step bar → close/unmount).
- feat: **`REQ-SB-48-US-01`** (`SPRINT-042`, `T01`-`T02`) — Skills
  Capabilities Tree, collapsible/icon-bearing/multi-select, grouped by
  Tool. `skill_tools.SKILLS` gains a `"tool"` field on every one of its 11
  entries (`Outlook`/`Vault`/`Web`/`Compass`, `T01`), passed through by
  `skill_registry.list_agent_capabilities`'s skill-kind branch unchanged
  (action-kind rows carry no `"tool"` key). New standalone, mode-
  parameterized `src/frontend/src/features/agents-map/SkillsTree.tsx`
  (`mode="manage" | "select"` — `"manage"` is this story's own scope;
  `"select"` is a real, already-wired seam for `REQ-SB-46-US-01-T04`,
  `SPRINT-043`) replaces `AgentDetailPanel.tsx`'s flat Capabilities
  `kv-list` with 4 collapsible Tool groups (fixed Unicode icon per Tool,
  expanded by default), a same-grant-state-only multi-select composing N
  sequential existing single-Skill `grantAgentSkill`/`revokeAgentSkill`
  calls (never a new batch endpoint), alongside the unchanged per-row
  Grant/Revoke buttons; Built-in (action-kind) capabilities stay outside
  the tree, ungrouped, exactly as before (`T02`). Verified live against
  all 9 locked ACs via a real CDP-driven headless-Edge session. Found and
  disclosed `BUG-013` (pre-existing, out-of-scope `skill_registry.
  _load_state` migration-seed self-heal bug) along the way — see
  `BUGS.md`/`ESCALATIONS.md` → `ESC-035`.
- feat: **`REQ-SB-50-US-01`** (`SPRINT-042`, `T01`-`T02`) — Tags/Locations
  Autocomplete on the Agent Settings Vault Scope field. New
  `vault_search.list_scope_suggestions()` composes the already-real
  `list_tags()` + `vault_writer.list_known_kinds()` into one
  `{"tags", "folders"}` payload, exposed at a new `GET /vault-search/
  scope-suggestions` (no `q=` filter — full snapshot, client filters,
  `T01`). New `fetchScopeSuggestions()` (`features/vault-browser/
  client.ts`), fetched once per agent-switch in `AgentDetailPanel.tsx`;
  a suggestion dropdown renders under the existing Vault scope `<input>`,
  client-filtered against the in-progress comma-separated token
  (substring match), selected via `onMouseDown` + `preventDefault()` (not
  `onClick`, which would fire after the field's own `onBlur` commit and
  lose the pick) — a second commit path alongside the existing typed+blur
  one, neither disturbing already-committed scope values (`T02`).
  Verified live against all 4 locked ACs via real vault-derived tag/
  folder data and a real CDP-driven browser session.
- feat: **`REQ-SB-44-US-01`** (`SPRINT-041`, `T01`-`T06`) — Inbox Cockpit:
  the Meeting Cockpit's shared 3-panel pattern extended for email, per
  `ADR-036`. New Email-note frontmatter field `recipients:
  list[{"name","email"}]` (merges To + CC, no required/optional
  distinction) — captured via a new `outlook_com.resolve_mail_recipients`
  (public generalization of `_resolve_attendees`, itself unmodified) and
  written by `email_classification.classify_recent_emails` as a
  JSON-encoded STRING (not a raw list literal), reusing `SPRINT-040`'s own
  already-established workaround for `vault_writer.py`'s confirmed
  list-of-dicts round-trip limitation — `cockpit/people.py`'s existing
  JSON-string acceptance already consumes it with zero changes (`T01`).
  `my_day.list_email_items` gains an additive `"stem"` field, mirroring
  `list_calendar_items`'s own (`T02`). New `app/business/cockpit/
  attachments.py` (`list_attachments`/`hand_off_attachment_to_chat`) —
  lists an email's already-vault-saved attachment files and hands one off
  by composing `REQ-SB-28-US-01`'s own `upload_storage`
  (save/extract/delete) and `summarize_file` Skill DIRECTLY against the
  real vault-saved bytes, posting an honest result to the shared Cockpit
  thread via `threads.append_system_message` — never `REQ-SB-28`'s own
  chat-upload endpoint (which auto-files via the Vault Filing Expert, not
  wanted here), never `skill_registry`/`_invoke_action` (`T03`). Two new
  additive, email-only routes on the SHARED `cockpit_router.py` (`GET
  /cockpit/email/{stem}/attachments`, `POST .../attachments/{filename}/
  hand-off`, `T04`) and two new functions on the SHARED
  `cockpitApiClient.ts` (`fetchCockpitAttachments`/`handOffAttachment`,
  `T05`) — the Meeting Cockpit's own five/six existing routes/exports
  unmodified throughout. New `features/cockpit/AttachmentsPanel.tsx` (renders
  nothing for an attachment-free email — Scenario 4b) and
  `pages/InboxCockpitPage.tsx`, supplying `subjectKind="email"` plus two
  additive props (`attachmentsSlot`, `enableDraftCopyAffordance`) to the
  SHARED `Cockpit` component `REQ-SB-43-US-01` built — no fork. New
  `/inbox-cockpit/:stem` route; `MyDayEmailsPage.tsx`'s rows are now real
  `<Link>`s keyed by the real email stem (`T06`). A drafted reply is
  ephemeral (frontend-only Copy affordance on every Expert reply, no
  backend persistence, no send capability anywhere in the codebase —
  Scenario 7's "never sent automatically" holds by construction). Verified
  live end-to-end in a real browser (headless-Edge CDP session): a real
  clickable Emails row opens the exact right cockpit; sender/CC people
  chips honestly distinguish an existing Person note (clickable) from one
  that doesn't exist yet (`.tag-chip--static` fallback); a real PDF
  attachment on a real captured email was listed and handed off to a real
  Compass summarization call, the summary posted into the shared thread;
  two real brought-in Experts replied in one shared thread with distinct
  attribution; a real Anthropic-backed on-the-spot research call (reusing
  `SPRINT-040`'s own `research.py` UNCHANGED) produced a genuine result
  with an explicit Save/Discard choice, scoped per-email (a second email's
  cockpit never showed the first email's saved result); Save created a
  real standalone note wikilinked to the Email note, Discard created
  nothing. Full reasoning: `Implementation/Architecture/ADR.md` →
  `ADR-036`; each task's own Implementation Log under
  `Implementation/Tasks/REQ-SB-44-US-01-T01`..`T06`.

- feat: **`REQ-SB-43-US-01`** (`SPRINT-040`, `T01`-`T09`) — Meeting Cockpit:
  a clickable My Day Calendar row opens a 3-panel prep-and-live workspace
  (right: meeting info + attendee chips; middle: a unified multi-agent
  Expert chat; left: available Agents + this meeting's own scoped
  quick-research results), per `ADR-036`. New shared `.second-brain/
  cockpit_threads.json` state (`vault_writer.load_cockpit_threads_state`/
  `save_cockpit_threads_state`, `T01`), this codebase's first multi-party
  (not per-agent) conversation store. New shared `app/business/cockpit/`
  sub-package, generic over `subject_kind`/`subject_note_stem`: `threads.py`
  (`get_thread`/`bring_in_agent`/`send_user_message`/`append_system_message`
  — composes `ADR-015`'s existing, unmodified `run_agent_conversation` once
  per currently brought-in Expert per user message, each reply appended to
  the SAME shared thread tagged with its own `agent_id`/`agent_name`, `T02`);
  `people.py` (`resolve_people_chips`, plus a new read-only
  `people_extraction.find_existing_person_note(email)` — the first pure
  "find, never create" lookup in that module, `T03`); `research.py`
  (`trigger_research` Hub-routes to a real Research Expert and invokes the
  already-`Done` `web-research` Skill; `save_research_result` writes a real,
  standalone, wikilinked note via a direct `vault_writer.write_note` call,
  never through `skill_registry`; `list_research_results` reads via the
  subject note's own indexed backlinks, `T04`). New `app/api/
  cockpit_router.py` (`GET`/`POST /cockpit/{subject_kind}/{subject_note_stem}
  [...]`), registered in `main.py` (`T05`). `my_day.list_calendar_items`
  gains an additive `"stem"` field (`T06`). New frontend
  `features/cockpit/cockpitApiClient.ts` (`T07`) and shared `Cockpit.tsx`
  3-panel component (`T08`, new `styles/cockpit.css` — `.cockpit-layout`/
  `.tag-chip--static`/`.chat-message-author`, ported from the approved
  `html-prototype/meeting-cockpit.html`), reused by `REQ-SB-44-US-01`'s own
  future Inbox Cockpit via two optional props (`attachmentsSlot`/
  `enableDraftCopyAffordance`), mirroring `BUGFIX-02-US-01`'s "one
  component, optional props, two call sites" precedent. New
  `pages/MeetingCockpitPage.tsx` + `/meeting-cockpit/:stem` route;
  `MyDayCalendarPage.tsx`'s rows are now real `<Link>`s keyed by the real
  meeting stem (`T09`). Verified live end-to-end: two real Expert agents
  (Vault Q&A, People Notes) brought into one shared chat produced
  distinctly-attributed real replies in a single thread; a real
  Anthropic-backed on-the-spot research call produced a genuine result with
  an explicit Save/Discard choice (Save created a real wikilinked note,
  Discard created nothing); attendee chips correctly distinguished a real
  existing Person note from an honest "no note yet" fallback; `REQ-SB-20`'s
  own Hub-routing behavior for a brought-in Expert was independently
  reconfirmed unaffected. **Disclosed finding, not fixed in this pass:**
  `vault_writer.py`'s frontmatter parser cannot round-trip a list-of-dicts
  value, and no real captured Meeting note carries an `attendees` field yet
  (`REQ-SB-08`'s own capture pipeline is unmodified by this story) — worked
  around within `cockpit/people.py`'s own scope (accepts a JSON-encoded
  string), see `MEMORY.md` and `REVIEW-QUEUE.md`. Full reasoning:
  `Implementation/Architecture/ADR.md` → `ADR-036`; each task's own
  Implementation Log under `Implementation/Tasks/REQ-SB-43-US-01-T01`..`T09`.

- feat: **`REQ-SB-28-US-01`** (`SPRINT-038`, `T01`-`T05`) — File upload
  on agent chat: Compass summarization + Vault Filing Expert handoff,
  per `ADR-034`. New `app/data_access/upload_storage.py` — the
  `.second-brain/` convention's first extension to raw bytes
  (`.second-brain/uploads/`), owning `validate_upload`/`save_upload`/
  `extract_text_content` (`.txt`/`.md` direct decode, `.pdf` via a new
  `pypdf` dependency)/`delete_upload`; a real 20 MB size cap and
  `.pdf`/`.txt`/`.md`-only accepted-extension list, each rejection
  distinctly worded (`T01`). `requirements.txt` also gains
  `python-multipart` (a routine implementation necessity of the new
  multipart endpoint, not a new architectural decision). New
  `compass_client.summarize_content(content, source_description)` —
  same payload/`CompassError`-handling shape as `classify_email`/
  `classify_task` (`T02`). New `summarize-file` Skill — this project's
  **first real (non-stub) Skill implementation** — one additive
  `skill_tools.SKILLS` entry + `@mcp_server.tool()` handler
  (`"mutates": False`, calls `compass_client.summarize_content`, never
  raises — an honest `{"status": "error", ...}` on `CompassError`) +
  one additive `skill_registry._SKILL_HANDLERS` row (`T03`). New
  additive `POST /agents/{agent_id}/chat/attachment`
  (`app/api/agents_router.py`, multipart `message` + `file`) composes
  validate → save → extract → `summarize-file` (auto-granted,
  unconditional/idempotent — this mechanism's own mandatory default
  capability, not an opt-in Skill) → the already-`Done` Vault Filing
  Expert's `determine_placement_and_file`, deleting the temporary
  upload once summarized on every reachable path regardless of
  downstream filing outcome; a Compass/filing failure is surfaced
  honestly, never fabricated, and a filing failure after a successful
  summary preserves and shows the real summary text rather than
  discarding it. The existing `POST /agents/{agent_id}/chat` JSON
  contract is untouched (`T04`). Frontend: `AgentDetailPanel.tsx`'s
  Chat tab gains a `[data-role="chat-attach-input"]` file control
  (`.pdf`/`.txt`/`.md`), an attached-file preview with a remove
  control, and an inline honest-rejection error for an unsupported
  client-side extension; `agentsApiClient.ts` gains
  `sendChatMessageWithAttachment` (a raw `fetch`, bypassing
  `client.ts`'s hardcoded JSON `Content-Type`, since a multipart
  request needs its own boundary header). Verified live end-to-end
  against all 10 locked ACs, with real files: a real `.txt`/`.pdf`
  attachment through the full chain to a filed, tagged, wikilinked
  vault note about a genuinely new customer; the temporary upload
  confirmed deleted on every reachable path; the existing plain chat
  endpoint confirmed byte-for-byte unmodified; both honest-rejection
  paths (unsupported type, oversized file) confirmed with zero
  storage/API calls; a real induced Compass failure and a real induced
  Vault-Filing-Expert-unavailable outcome both confirmed honest and
  non-fabricating, the latter's summary confirmed preserved and shown.
  Frontend verified via a from-scratch Python `websockets`-based CDP
  driver against a real headless Edge browser (no Playwright/Puppeteer
  in this repo) — real `DOM.setFileInputFiles` for file-input
  interaction. Two scope-internal judgement calls (`T05` — attach-state
  reset on agent switch; a file-only send guard loosening), logged for
  human spot-check, see `REVIEW-QUEUE.md`.

- feat: **`REQ-SB-38-US-01`** (`SPRINT-037`, `T01`-`T04`) — Agents Map
  Density Clustering. `layoutAgents.ts` gains a new `VISIBLE_SLOT_CAP = 6`
  constant (sibling to `SECTION_ARC_SPAN_DEG_CAP`/`SECTION_ARC_SPAN_FRACTION`)
  and groups a Section's agents by `(sectionId, agentType)` — not
  `sectionId` alone — ahead of the existing fan-out math: a group over the
  cap keeps only its first 5 agents in `mapAgents` and emits one new
  `ClusterMarker` descriptor (`id`, `sectionId`, `type`, `angleDeg`,
  `count`, `agentIds`) for the rest, at the group's own last fan slot; a
  group at/under the cap is unaffected (`T01`). `agents-map.css`'s
  `.map-overflow-marker` is replaced with the prototype's now-clickable
  version (accent dashed border/glow, hover/focus-visible lift, new
  `.map-overflow-marker-count`/`-label` inner spans), ported verbatim
  (`T02`). New `ClusterDrilldown.tsx` — a sibling to `SectionDrilldown.tsx`
  — renders a drill-down scoped to exactly one cluster's own represented
  agent ids, reusing `layoutSectionDrilldown()`/`SectionHub`/`AgentNode`
  unmodified (`T03`). `AgentsMapCanvas.tsx` renders one
  `.map-overflow-marker` button per cluster, widens its local click-to-zoom
  state (`BUG-002` Option D) from a bare `sectionId` to a
  `{ kind: 'section' | 'cluster'; id }` pair so a cluster's own click
  target can never collide with a Section Hub's, and mounts
  `ClusterDrilldown` on a marker click while the Section Hub's own click
  path continues to open the full, unclustered `SectionDrilldown`
  unaffected (`T04`). `T04` also required a minimal, mechanical extension
  of `AgentsMapPage.tsx` (new `clusters`/`fullAgents` state, passed through
  as two new props) — outside every task's own declared Files to Modify,
  logged as a scope-internal judgement call, `gate: flagged` — since
  `AgentsMapCanvas` cannot compute clusters itself, and `T01`'s own locked
  `mapAgents` reduction would otherwise silently drop clustered agents from
  the Section Hub's own full drill-down. All 6 locked ACs verified live:
  `layoutAgents()` exercised directly (Node's own TS type-stripping, no
  transpile step); `ClusterDrilldown` rendered by the real dev server +
  React runtime in a real CDP-driven headless browser; the fully-wired
  canvas against 8 real `worker`-type agents created via the live `POST
  /agents` endpoint (bringing a real `technical/worker` group to 8, over
  the cap) — observed 5 dots + 1 "+3" marker, a cluster-scoped drill-down
  showing exactly its own 3 agents, an unchanged overview on Back, and the
  Section Hub's own full 9-agent unclustered drill-down; test agents fully
  removed afterward. Sprint `SPRINT-037` complete; retrospective drafted,
  `gate: flagged` for human retro-harvest + the `AgentsMapPage.tsx`
  judgement-call spot-check.

- feat: **`REQ-SB-41-US-01`** (`SPRINT-036`, `T01`-`T02`) — Agent Overview
  surface, per `ADR-033`. `agent_registry.py`'s 7 shipped `_SEED_AGENTS`
  entries each gain one appended `{"key": "Purpose", "value": "..."}`
  settings row (`email-capture`/`meeting-capture`/`todo-capture`/
  `people-producer`/`vault-qa`/`vault-filing-expert`/`compass-expert`),
  additive-only, no existing row edited/reordered/removed (`T01`).
  `AgentDetailPanel.tsx`'s `TABS` gains a new `'overview'` entry, placed
  first, ahead of `'chat'`/`'history'`/`'settings'`/`ADR-032`'s
  conditionally-rendered `'gaps'`; `activeTab`'s initial state and its
  per-agent-switch reset value both change from `'chat'` to `'overview'`
  — opening any agent now lands on a new Overview tab, not Chat, with
  Chat one click away and fully unmodified. The Overview renders 4
  regions (Purpose — reads `settings` `"Purpose"`, falling back to
  `"Domain"`, or an honest "No stated purpose recorded for this agent."`
  string; Working mode; a static, non-configurable Guardrails statement
  identical for every agent; Vault Scope — the real assigned value or an
  honest "No vault scope assigned yet" state) plus, for `agent.type ===
  'expert'` only, a one-line "Open knowledge gaps: N" summary composing
  `REQ-SB-40-US-01`'s existing `GET /agents/{agent_id}/knowledge-gaps`
  `open_count` field, linking into the existing Gaps tab (`T02`). All 7
  locked ACs verified live via a CDP-driven headless Edge session against
  the real running app, spot-checked across `vault-qa` (Expert),
  `todo-capture` (Worker), and `people-producer` (Producer). Sprint
  `SPRINT-036` complete; retrospective drafted, `gate: flagged` for
  human retro-harvest + `ADR-033` review.

- feat: **`REQ-SB-40-US-01`** (`SPRINT-035`, `T01`-`T08`) — Agent
  Knowledge-Gap Tracking & Expert Readiness, per `ADR-032`. `graph.py`
  gains a second interceptable bound tool, `record_knowledge_gap(topic:
  str)`, mirroring `ADR-017`'s `request_cross_section_help` pattern
  exactly: intercepted by a new `_record_knowledge_gap` node BEFORE
  generic tool execution, which reads the turn's real originating
  `HumanMessage` (never the model's own paraphrased `topic` argument) and
  loops back to `call_model`. `state.py`'s `AgentConversationState` gains
  an additive `gap_recorded: dict | None` field; its system prompt gains
  one appended sentence instructing the model to call
  `record_knowledge_gap` before an honest "I don't know" (extends, does
  not modify, `REQ-SB-33-US-01`'s existing instruction text). New `app/
  business/knowledge_gap_tracking.py` (`record_gap`/`close_gap`/
  `list_agent_gaps`/`count_open_gaps`/`get_gap`/
  `resolve_gap_with_human_answer`/`resolve_gap_via_research`/
  `close_gap_by_pending_approval`) + new tenth `.second-brain/
  agent_knowledge_gaps.json`, owned by new `vault_writer.py` primitives
  `load_knowledge_gaps_state`/`save_knowledge_gaps_state`. Two closing
  paths, both composing already-`Done` chains unchanged: `POST
  /agents/{id}/knowledge-gaps/{gap_id}/resolve` routes a human-provided
  answer through the unmodified Vault Filing Expert
  (`vault_filing_expert.determine_placement_and_file`); `POST
  /agents/{id}/knowledge-gaps/{gap_id}/research` routes through the
  unmodified delegated knowledge-bootstrap chain
  (`knowledge_bootstrap.bootstrap_agent_knowledge`) — a real
  `"written"`/`"pending_approval"` outcome closes the gap, an honest
  `"no_results"`/other status leaves it open. `pending_approvals_router.
  py::approve_pending_approval` gains one additive, resolution-agnostic
  call (`close_gap_by_pending_approval`) so a Tier-2 gap-closing proposal
  only closes its gap once filing actually finalizes. New `GET
  /agents/{id}/knowledge-gaps` (`{"gaps": [...], "open_count": int}`).
  Frontend: `AgentDetailPanel.tsx` gains a fourth, conditionally-rendered
  "Knowledge gaps" tab, gated to `agent.type === 'expert'` (genuinely
  omitted from the tab-bar array for Worker/Producer agents, not
  hidden); `agentsApiClient.ts` gains `fetchAgentKnowledgeGaps`/
  `resolveKnowledgeGap`/`researchKnowledgeGap`. Verified live end-to-end
  against all 7 locked ACs (`AC-01`..`AC-07`) — real Compass/Anthropic
  Provider calls, a real filed vault note for the human-answer path, a
  real web-research-then-file round trip for the research path, a real
  honest no-results induction, and a real CDP-driven browser pass
  confirming the tab's own open-gap count visibly declines with no page
  reload once a gap is closed through the screen itself. Confirmed
  ordinary chat (an agent answering something it genuinely knows) still
  works unaffected on 2 separate existing agents (`vault-qa`,
  `compass-expert`) after the shared `graph.py` change. Full reasoning:
  `Implementation/Architecture/ADR.md` → `ADR-032`; each task's own
  Implementation Log under `Implementation/Tasks/REQ-SB-40-US-01-T01`..
  `T08`.
- feat: **`REQ-SB-37-US-03`** (`SPRINT-034`, `T03`) —
  `CreateAgentWizard.tsx` gains a Producer step: Purpose field (`textarea`)
  + a genuinely single-select output-Skill control (radio inputs, one
  `name` group, never checkboxes) + the Section `<select>` reused
  verbatim from Expert/Worker. Submit validates name + Purpose + a
  selected output Skill + a Section client-side before any call fires,
  then issues, in order: `createAgent({name, type: 'producer', purpose})`
  → exactly one `grantAgentSkill(agentId, selectedOutputSkillId)` →
  `updateAgentAssignment(agentId, {section_id})` — `section_id` carried
  **alone**, never combined with another field (the one deliberate
  structural difference from Worker's own combined `PATCH`). The Producer
  type button is now genuinely selectable. `agentsApiClient.ts`'s
  `CreateAgentBody` gains `purpose?: string`. Verified live via CDP: the
  mounted step's exact 4-field set (no Domain/Skills-label/Vault-Scope
  text anywhere), the honest all-fields-missing rejection, a dedicated
  honest rejection naming only "an output Skill" when every other field
  is present, and a real end-to-end creation (`vault-scribe`) confirmed
  against `GET /agents/vault-scribe` + `GET /agents/vault-scribe/skills`.
- feat: **`REQ-SB-37-US-03`** (`SPRINT-034`, `T02`) — `POST /agents`'s
  `type` dispatch on `app/api/agents_router.py` gains a third,
  `"producer"` branch: `purpose` (new, optional at the Pydantic level,
  required non-blank for a Producer) stored via `create_agent(name,
  "producer", settings=[{"key": "Purpose", "value": purpose}])` — the
  same generic `settings` kv-list mechanism Expert's Domain already uses
  (`ADR-031` point 3). Any `type` other than
  `"expert"`/`"worker"`/`"producer"` is still refused with an honest `400`
  naming all three. Verified live end-to-end: Purpose validation, the
  output-Skill grant + Section assignment combination, a freshly created
  Producer rendering on the Agents Map's Producer ring with zero new
  frontend code, and Chat/History behaving identically to an existing
  agent's.
- feat: **`REQ-SB-37-US-03`** (`SPRINT-034`, `T01`) — a new placeholder
  output Skill, `write-to-vault-draft` (`mutates: True`), seeded into
  `app/business/skill_tools.py`'s `SKILLS` catalog with a matching
  zero-arg `@mcp_server.tool()` stub (honest-unavailable, mirrors
  `diagram_understanding`'s exact body) and the matching
  `skill_registry._SKILL_HANDLERS` entry — per `ADR-031` point 2. Verified
  live that it is gated by the already-real two-axis working-mode gate
  with zero new gating code (a Supervised-mode invocation defers to a
  real Pending Approval, exactly like any other granted mutating Skill).
- feat: **`REQ-SB-37-US-02`** (`SPRINT-034`, `T02`) —
  `CreateAgentWizard.tsx` gains a Worker step: a Skills multi-select
  (checkboxes sourced from `GET /skills`, the full unified `REQ-SB-39`
  catalog) + a Vault Scope free-text/comma-separated field + the Section
  `<select>` reused verbatim from the Expert step. Submit validates name +
  ≥1 Skill + non-empty Scope + a Section client-side before any call
  fires, then issues, in order: `createAgent({name, type: 'worker'})` →
  one `grantAgentSkill(agentId, skillId)` per selected Skill → one
  combined `updateAgentAssignment(agentId, {section_id, scope})` carrying
  both fields together in a single call. The Worker type button is now
  genuinely selectable. `agentsApiClient.ts`'s `CreateAgentBody.domain`
  becomes optional. Verified live via CDP (native-setter input technique +
  a `window.fetch` spy): the exact 4-field set, the honest all-fields-
  missing rejection with zero API calls, and a real end-to-end creation
  (`ops-helper`, with a read-only Skill and a migrated mutating Skill both
  granted) confirmed against `GET /agents/ops-helper` +
  `GET /agents/ops-helper/skills`.
- feat: **`REQ-SB-37-US-02`** (`SPRINT-034`, `T01`) — `POST /agents`'s
  `type` check on `app/api/agents_router.py` extended to accept
  `"worker"` alongside `"expert"`; `domain` becomes optional at the
  Pydantic level (required only for Expert). A Worker is created via
  `agent_registry.create_agent(name, "worker", settings=[])` — no
  Domain-equivalent setting; its real configuration (Skills, Vault Scope,
  Section) lives entirely in the wizard's own three follow-up calls.
  Verified live end-to-end: a freshly created Worker's granted mutating
  Skill honors Supervised-mode gating identically to an existing,
  already-shipped agent's own granted Skill (cross-checked against
  `email-capture`); the created Worker renders on the Agents Map's Worker
  ring with zero new frontend code; Chat/History behave identically to an
  existing agent's.
- feat: **`REQ-SB-37-US-01`** (`SPRINT-033`, `T04`) — new
  `src/frontend/src/features/agents-map/CreateAgentWizard.tsx` (type
  selector — Expert enabled, Worker/Producer visibly-present-but-disabled
  — plus the Expert step: name/knowledge-domain/Section) and new
  `src/frontend/src/features/settings/CreateAgentCard.tsx` (the "+ Create
  agent" Settings entry affordance, `<details>`-based, mirroring
  `SectionsCard.tsx`/`ProvidersCard.tsx`'s own pattern); `SettingsPage.tsx`
  additionally composes `<CreateAgentCard />`; `agentsApiClient.ts` gains
  `createAgent({name, type, domain}) -> Promise<AgentDetail>`. This is the
  first real, no-source-code-change agent-creation entry point in the app.
  Verified live via a real CDP-driven browser session: the wizard reaches
  from Settings with zero code change, Expert's field set is exactly
  name/domain/Section (no Worker/Producer fields anywhere), submitting
  with any field missing fires zero API calls and names every missing
  field, and a real submission fires exactly `POST /agents` then
  `PATCH /agents/{id}` in sequence and shows a real success confirmation.
- feat: **`REQ-SB-37-US-01`** (`SPRINT-033`, `T03`) — new `POST /agents`
  endpoint on `app/api/agents_router.py` (`CreateAgentBody`: `name`,
  `type`, `domain`) — creates a new agent via `agent_registry.create_agent`
  and returns the exact `GET /agents/{agent_id}` shape. Rejects a missing
  `name`/`domain` with `400` before calling `create_agent` at all; rejects
  any `type != "expert"` with an honest `400` (Worker/Producer are
  `REQ-SB-37-US-02`/`US-03`'s own scope). Never accepts a `section_id` —
  Section assignment stays the existing, separate `PATCH /agents/{id}`
  call. Verified live end-to-end against every already-`Done` downstream
  surface with zero code change to any of them: the created agent renders
  immediately on the Agents Map (Expert ring, assigned Section, no
  restart); honestly declines a question within its own stated domain
  (`REQ-SB-33`'s guardrail, zero new code); Provider/Working-mode/Skill
  grants settable via the exact same endpoints an existing agent uses;
  Chat and Communication History behave identically to an existing agent's
  (byte-identical response shape).
- feat: **`REQ-SB-37-US-01`** (`SPRINT-033`, `T02`) — `app/business/
  agent_registry.py` becomes a static-seed-plus-persisted-JSON-overlay
  store, per `ADR-030`: the module-level `AGENTS` dict is renamed
  `_SEED_AGENTS` (byte-identical, unchanged — the 7 shipped agents stay
  in-code, deployment configuration); `get_agent`/`list_agents` become
  seed-then-persisted merges (seed agents always first); new
  `create_agent(name, type, settings=None)` derives `agent_id` via
  `vault_writer.tag_slug(name)`, disambiguating on collision with a
  numeric suffix (`-2`, `-3`, ...) against the union of seed and created
  ids — never collapses two distinct creations into one identity, never
  lets a created agent's slug shadow a shipped agent's id. Every
  already-`Done` self-healing per-agent registry (Sections/Providers/
  Working-mode/Skills/Keywords) now picks up a created agent automatically
  — confirmed live, zero code changes needed in any of those five files.
- feat: **`REQ-SB-37-US-01`** (`SPRINT-033`, `T01`) — new
  `app/data_access/vault_writer.py` primitives,
  `load_agents_registry_state()` / `save_agents_registry_state()`, the
  eleventh `.second-brain/` state-file pair (`agents_registry.json`),
  byte-for-byte mirroring `load_skills_state()`/`save_skills_state()`'s
  pure-I/O shape — the persisted overlay `T02`'s `agent_registry.py`
  composes for runtime-created agents.
- fix: **`BUG-008`** — `app/scheduling/capture_scheduler.py::lifespan` awaited
  `run_capture_if_idle()` directly, so FastAPI's own "application startup
  complete" — and therefore ALL HTTP traffic — was gated on the entire
  app-start capture catch-up run finishing first. With a real backlog this
  meant 100+ sequential live Compass calls before the server would answer
  any request. Changed to `asyncio.create_task(run_capture_if_idle())`:
  capture still fires unconditionally on every start per `REQ-SB-07`'s
  spec, it just no longer blocks the API. Verified live: server now
  answers within ~2s of start. Direct fix (urgency precedent, see
  `BUGS.md`), not routed through `/triage`.
- feat: **`REQ-SB-39-US-01`** (`SPRINT-030`, `T01`) — `app/business/
  skill_tools.py`'s `SKILLS` catalog gains a `"mutates": bool` field on
  every entry (`diagram-understanding`/`web-research` both `False`) and 3
  new zero-arg, unconditionally honest-unavailable `@mcp_server.tool()`
  Skill handlers (`view_last_run`, `ask_question`, `view_channel_status`)
  reusing their exact former `agent_registry.py` Action id strings —
  `ADR-028` point 1/4, the first step of migrating every read-only
  hardcoded Action onto the Skills mechanism.
- feat: **`REQ-SB-39-US-01`** (`SPRINT-030`, `T02`) — `app/business/
  skill_registry.py::invoke_skill` gains a required, no-default `trigger:
  Literal["chat","direct","hub_routed"]` parameter (mirrors
  `agents_router.py::_invoke_action`'s own shape, `ADR-028` point 2);
  `_SKILL_HANDLERS` gains the 3 new entries from `T01`. Not yet branched
  on anywhere — `REQ-SB-39-US-02`'s own job.
- feat: **`REQ-SB-39-US-01`** (`SPRINT-030`, `T03`) — `app/api/
  skills_router.py`'s `POST /agents/{agent_id}/skills/{skill_id}/invoke`
  now passes `trigger="direct"` (server-hardcoded literal, never
  client-suppliable) to `skill_registry.invoke_skill`, satisfying `T02`'s
  new required parameter (`ADR-028` point 2).
- feat: **`REQ-SB-39-US-01`** (`SPRINT-030`, `T04`) — `app/business/
  agent_orchestration/knowledge_bootstrap.py`'s existing
  `skill_registry.invoke_skill` call gains `trigger="hub_routed"` — the
  first real call site on either the Actions or Skills path to ever pass
  this value (`ADR-028` point 2, `ADR-020` point 3's own reserved
  semantic, realized here one release early).
- feat: **`REQ-SB-39-US-01`** (`SPRINT-030`, `T05`) — `app/business/
  skill_registry.py` gains a one-time, explicitly-scoped migration-grant
  retrofit seed (`_MIGRATION_GRANT_SEED`, folded into `_load_state()`) —
  the 4 real, already-shipped agents that carried `view_last_run`/
  `ask_question`/`view_channel_status` as a hardcoded Action before this
  migration now genuinely hold the equivalent Skill grant, confirmed live
  against the real `.second-brain/agent_skills.json` (`ADR-028` point 5).
  `grant_skill_access` gained an internal-only `_preloaded_state` seam to
  avoid a real infinite-recursion bug the naive implementation would have
  hit (see `MEMORY.md`).
- feat: **`REQ-SB-39-US-01`** (`SPRINT-030`, `T06`) — `app/business/
  skill_registry.py` gains `list_agent_capabilities(agent_id)`, combining
  an agent's still-real Actions (filtered to exclude any migrated id) with
  its granted Skills into one uniformly-shaped list (`{"id", "label",
  "kind": "action" | "skill"}`) — `ADR-028` point 6.
- feat: **`REQ-SB-39-US-01`** (`SPRINT-030`, `T07`) — `app/api/
  agents_router.py`'s `trigger_action`/`chat()` now route any capability
  id that is a `skill_tools.SKILLS` member through
  `skill_registry.invoke_skill` (new `_invoke_capability` helper,
  translating its result shapes into the existing `{"status", "message"}`
  envelope); every still-real Action id keeps calling `_invoke_action`
  unchanged (`ADR-028` point 3). Verified live: the "view last run" chat
  trigger for `email-capture` still matches the same capability id and
  routes correctly — the reply wording changed from the Action-era generic
  message to the Skill-stub convention message, an already-Accepted,
  disclosed `ADR-028` design choice, not a functional regression (see
  `T07`'s own Implementation Log for the full live comparison).
- feat: **`REQ-SB-39-US-01`** (`SPRINT-030`, `T08`) — `app/api/
  agents_router.py::get_agent()`'s response shape changes `"actions"` →
  `"capabilities"` (sourced from `list_agent_capabilities`) — `"actions"`
  fully removed, not kept alongside. `update_agent_assignment` (`PATCH`)
  needed no edit, already delegates.
- feat: **`REQ-SB-39-US-01`** (`SPRINT-030`, `T09`) — `AgentDetailPanel.tsx`'s
  Settings tab's static "Available actions" block is replaced with a
  unified "Capabilities" `kv-list`: action-shaped items stay plain/
  non-interactive, skill-shaped items get a real, working `Grant`/`Revoke`
  control (new `skillsApiClient.ts`, reuses the existing `GET /skills`/
  `GET,POST,DELETE /agents/{agent_id}/skills[/{id}]` endpoints — no new
  backend endpoint). `agentsApiClient.ts`'s `AgentDetail.actions` →
  `capabilities: AgentCapability[]`. **Disclosed environment gap:** no
  Node.js install exists on this host at all, so `npm run build`/real
  browser verification could not be run — both locked ACs this task
  touches were already independently verified live at the API layer by
  `T03`/`T08`; see `T09`'s own Implementation Log and `MEMORY.md`.
- feat: **`REQ-SB-39-US-02`** (`SPRINT-031`, `T01`) — `app/business/
  skill_registry.py::invoke_skill` gains `ADR-020`'s own two-axis
  working-mode gate (`ADR-029` point 2), inserted after the existing
  access check and before dispatch: Manual + `trigger="hub_routed"`
  refuses outright; Supervised + the resolved Skill's own `"mutates"` flag
  creates a real `pending_approval_registry` record (storing `skill_id` in
  the existing `action_id` field, `args` in `payload`) plus a `"proposal"`
  history entry; everything else falls through. `_dispatch_skill(agent_id,
  skill_id, args)` extracted as the raw, ungated primitive (byte-identical
  pre-gate dispatch body) — the one function every real call site
  (`skills_router.py`, `agents_router.py`'s dispatch fork,
  `knowledge_bootstrap.py`'s Hub-routed call) now passes through, making
  "never a route around the gate" true by construction.
- feat: **`REQ-SB-39-US-02`** (`SPRINT-031`, `T02`) — `app/api/
  pending_approvals_router.py`'s Approve endpoint gains a new
  `skill_tools.SKILLS`-aware branch, checked before `_APPROVAL_HANDLERS`,
  calling `skill_registry._dispatch_skill` directly (never `invoke_skill`
  — re-entering the gate on Approve would defer forever). New
  `skip_history` guard (defaults `False`) lets a self-recording handler
  (e.g. `build_knowledge`) suppress the generic post-approve history
  append via its own `"history_recorded"` result key.
- feat: **`REQ-SB-39-US-02`** (`SPRINT-031`, `T03`) — `app/business/
  skill_tools.py`'s `SKILLS` catalog grows from 5 to 9 entries: the 4
  formerly-hardcoded mutating Action ids (`run_capture_now`,
  `pause_schedule`, `rebuild_person_note`, `build_knowledge`), all
  `"mutates": True`, migrated with zero loss of protection and preserving
  today's exact real/honest-unavailable split (`run_capture_now` real only
  for `email-capture`; `pause_schedule`/`rebuild_person_note`
  unconditional honest-unavailable stubs; `build_knowledge` a real handler
  calling through to `knowledge_bootstrap.bootstrap_agent_knowledge` via a
  deferred import — avoids a real circular import — and a dedicated
  single-use thread bridge — avoids a "cannot be called from a running
  event loop" crash under a real async caller). `skill_registry.
  _SKILL_HANDLERS` gains the matching 4 entries.
- feat: **`REQ-SB-39-US-02`** (`SPRINT-031`, `T04`) — `app/business/
  skill_registry.py`'s `_MIGRATION_GRANT_SEED` extended with the 4 new
  id→agent-list entries, retrofitting the 5 real, already-shipped agents
  (`email-capture`/`meeting-capture`/`todo-capture`: `run_capture_now` +
  `pause_schedule`; `people-producer`: `rebuild_person_note`;
  `compass-expert`: `build_knowledge`) with the equivalent Skill access
  they carried as a hardcoded Action before this migration — same
  idempotent, one-time-backfill mechanism `REQ-SB-39-US-01-T05` already
  established.
- docs: **`Documentation/PRD.md`** — new requirement **REQ-SB-42: Real-Time
  Agent Activity Pulses (Agents Map)** — replaces the Agents Map's static
  agent connections with a live, push-driven visualization of per-agent
  activity (running a capture/Skill, generating a chat reply, an in-flight
  Hub-routed cross-section request, or an open pending-approval record),
  including a traveling pulse between the two specific agents during a real
  Hub-routed request. Captured via a requirements-gathering session;
  `BACKLOG.md` gains its index row (no story yet — next step is `/spec`).
- docs: **`Documentation/PRD.md`** — new requirement **REQ-SB-43: Meeting
  Cockpit — Expert-Assisted Meeting Workspace** — clicking a meeting opens a
  3-panel workspace (meeting info + clickable attendee chips linking to
  Person notes; a unified multi-agent chat where brought-in Experts all
  respond in one thread; a panel listing available Agents and this
  meeting's own quick-research results), with on-the-spot research
  optionally saved as a new note wikilinked to the Meeting note. Captured
  via a requirements-gathering session; `BACKLOG.md` gains its index row
  (no story yet — next step is `/spec` + `/design`, no prototype exists).
- docs: **`Documentation/PRD.md`** — new requirement **REQ-SB-44: Inbox
  Cockpit — Expert-Assisted Email Workspace** — same 3-panel pattern as
  REQ-SB-43 applied to email: sender + CC'd/thread-participant chips,
  attachments surfaced (hard dependency on REQ-SB-28, `Draft`), a unified
  multi-agent chat that can draft (never send) a reply, and this email's
  own quick-research results, optionally saved as a note wikilinked to the
  Email note. Captured via a requirements-gathering session; `BACKLOG.md`
  gains its index row (no story yet — next step is `/spec` + `/design`).
- feat: **`REQ-SB-29-US-01`** (`SPRINT-032`, `T01`) — `app/data_access/
  vault_writer.py` gains `load_agent_scope`/`save_agent_scope`/
  `load_all_agent_scopes` (new sibling `.second-brain/agent_scopes.json`,
  mirroring `agent_keywords.json`'s exact shape) and a new, independent
  `list_notes_matching_scope(scope: list[str]) -> list` retrieval
  primitive (frontmatter-tag / kind-folder-name match, mirroring
  `list_known_customers()`/`list_notes_in_kind_folder()`'s exact shape —
  deliberately does NOT compose `vault_indexing.get_index()`/
  `vault_search.py`, per the story's own Constraints).
- feat: **`REQ-SB-29-US-01`** (`SPRINT-032`, `T02`) — new `app/business/
  scope_registry.py` (`get_agent_scope`/`set_agent_scope`), a thin
  composition over `T01`'s new `vault_writer` primitives, mirroring
  `agent_keywords.py`'s exact shape; composed alongside
  `agent_registry.py`, which stays unmodified.
- feat: **`REQ-SB-29-US-01`** (`SPRINT-032`, `T03`) — `app/api/
  agents_router.py`'s `GET`/`PATCH /agents/{agent_id}` gain an additive
  `scope: list[str]` field (whole-list-replace on `PATCH`, explicit `[]`
  clears, omitted is a no-op) — `GET /agents` (list) unchanged.
- feat: **`REQ-SB-29-US-01`** (`SPRINT-032`, `T04`) — new `app/business/
  scope_query_tools.py::retrieve_notes_in_agent_scope(agent_id)`,
  registered as a sixth `@mcp_server.tool()` on the existing shared MCP
  server (`app/api/mcp_server.py`) — resolves and enforces the calling
  agent's own assigned vault scope server-side (never a freeform
  `tags`/`folders` model-supplied argument), returning real note content
  (`"status": "ok"`), an honest `"no_scope"` result for an unassigned
  agent, or an honest `"empty"` result for a non-empty scope with no
  matches — never a fabricated response. Not added to
  `skill_tools.SKILLS` — unconditionally available to every agent.
- feat: **`REQ-SB-29-US-01`** (`SPRINT-032`, `T05`) — `AgentDetailPanel.tsx`
  gains a "Vault scope" kv-row (free-text, comma-separated, `onBlur`
  commit — matching the Keywords row's exact established pattern, no new
  `/design` pass); `agentsApiClient.ts`'s `AgentDetail`/
  `updateAgentAssignment` gain an additive `scope: string[]` field. This
  completes `REQ-SB-29-US-01` end-to-end (`SPRINT-032`, `Done`) —
  activating the Customer/Pipeline/Agreements/Consumption vault schema's
  real retrieval path for the first time since it was resolved
  structure-only on 2026-08-10.

## 2026-08-13 — Repo onboarding docs + one-click launcher

- docs: **`README.md` (new)** — public-facing repo overview: what Second
  Brain is, stack, quick start, project layout, and a pointer to the
  delivery pipeline for contributors.
- docs: **`Documentation/DeploymentGuide.md` (new)** — prerequisites
  (Outlook desktop required for COM capture), the full `.env` variable
  reference, how to start/build, port list, and troubleshooting (orphaned
  `uvicorn --reload` worker holding a port; missing `.env` values failing
  loudly at startup by design).
- feat: **`start.bat` (new, repo root)** — one-click launcher: checks
  `src/backend/.env` exists, then opens the backend and frontend each in
  their own `cmd /k` window via `tools/run-backend.cmd`/
  `tools/run-frontend.cmd`. Found and fixed a real quoting bug during
  testing (doubled quotes around the repo's space-containing path
  silently broke it — see `MEMORY.md`); full live verification of the
  fix is left to the user's own desktop session, since this sandboxed
  shell cannot spawn a real interactive console window to test against.

## 2026-08-13 — SPRINT-028 — REQ-SB-09-US-01 (To-Do Task Capture Pipeline)

- feat: **`src/backend/app/data_access/outlook_com.py` (additive)** —
  `list_outlook_tasks(limit=100)`, this codebase's first Outlook
  Tasks-folder read (`GetDefaultFolder(13)`, no date-window params),
  plus `_map_task_status`/`_normalize_task_due_date` helpers. Live-COM
  correction: the real "no due date" sentinel on this installation reads
  as `"4501-01-01 00:00:00+00:00"`, not the originally-guessed
  `"1/1/4501"` — corrected before verification.
- feat: **`src/backend/app/data_access/vault_writer.py` (additive)** —
  `upsert_frontmatter_key` (the codebase's first genuine upsert-not-
  insert-only-if-missing baseline primitive), the Task-note
  create/top-up primitives (`create_task_note_baseline`,
  `ensure_task_note_baseline_frontmatter`, `build_task_tags`,
  `task_note_filename_stem`, `task_note_path_for_stem`,
  `task_note_exists_for_stem`), and the load-bearing
  `.second-brain/task_note_index.json` dedup/top-up lookup index
  (`load_task_note_index`/`lookup_task_note_stem`/`record_task_note`).
- feat: **`src/backend/app/data_access/compass_client.py` (additive)** —
  `classify_task`, a customer-only sibling to `classify_email` (no
  `kind` axis, no sender).
- feat: **`src/backend/app/business/todo_classification.py` (new)** —
  `classify_recent_todos`: fetch Outlook Tasks → classify by customer
  (Compass) → write/top-up via the EntryID-keyed dedup index → link the
  matched customer hub after a confirmed match only.
- feat: **`src/backend/app/business/email_classification.py`** — third
  gated `todo_mode` block in `run_capture_and_record_completion`
  (Autonomous/Supervised/Manual, its own independent `try/except` and
  `todo_capture_failed` boolean extending the trailing completion gate),
  a new `"todo-capture"` branch in `run_capture_for_agent`. Zero changes
  to `app/scheduling/capture_scheduler.py`.
- feat: **`src/backend/app/business/agent_registry.py`** —
  `"todo-capture"`'s "Task source" setting resolved to `"Outlook Tasks
  folder"` (was a placeholder pending this story).
- feat: **`src/backend/app/business/my_day.py` +
  `app/api/my_day_router.py`** — `list_todo_items()` (real, unwindowed
  read over `Work/Tasks/`, still-open tasks only) replaces the
  hardcoded-0 `todo` stub in `summary()`; `GET /my-day/todo` now returns
  real data.
- feat: **`src/frontend/src/pages/MyDayTodoPage.tsx` +
  `features/my-day/client.ts`** — populated To-Do drill-down
  (`.item-list`/`.item-row`, subject/customer-or-"No customer"/
  due-or-"No due date", `.badge`/`.badge-warning` for "Due today"/
  "Upcoming"), matching the approved `my-day-todo.html` prototype. No
  new CSS. `MyDayPage.tsx`'s dashboard card needed zero code change.
- verified: all 8 locked ACs (`AC-01`–`AC-08`) live against the real
  Outlook mailbox (235-item Tasks folder), real Compass, and the real
  vault (100 real items processed by a real app-start scheduler trigger,
  82 real notes on disk) — including a real induced-failure/independent-
  branch-funnel/recovery cycle, a real Supervised-mode gate check, and a
  real screenshot-verified populated drill-down with both badge states.
  `ADR-027`'s own disclosed-but-unverified `EntryID`-stability claim is
  now empirically confirmed (no superseding ADR needed).
- disclosed: one real, non-blocking finding — `BUG-011`'s pre-existing
  `_slugify` 80-char-truncation defect also affects Task notes, with a
  worse (same-subfolder literal overwrite) consequence than its own
  documented case, since Task notes share one flat `Work/Tasks/`
  subfolder. `ESCALATIONS.md` → `ESC-028`; recommend extending `BUG-011`'s
  own `BUGS.md` entry, not a new bug.
- docs: `MEMORY.md`, `REVIEW-QUEUE.md`, `BACKLOG.md` updated; sprint
  retrospective drafted (`Implementation/Sprints/SPRINT-028-todo-notes-
  from-outlook-tasks-capture.md`).

## 2026-08-13 — SPRINT-026 — REQ-SB-02-US-01 (Browse & Search)

- feat: **`src/backend/app/business/vault_indexing.py` (additive)** —
  `get_last_rebuilt_at() -> str | None` (`REQ-SB-02-US-01-T01`), a second,
  independent accessor alongside `get_index()`; a new module-level
  `_last_rebuilt_at` timestamp is set (ISO-8601 UTC) at the end of every
  `rebuild_index()` call. `rebuild_index()`'s own rebuild/backlink logic
  is otherwise untouched.
- feat: **`src/backend/app/business/vault_search.py` (new)** — read-only
  browse/tag-filter/note-detail/ranked-search query logic over
  `vault_indexing.get_index()` (`REQ-SB-02-US-01-T01`/`T02`): `list_notes`
  (paginated, optional exact-tag filter), `list_tags` (real tag list with
  counts, feeds the frontend's tag-filter chip row), `get_note_detail`
  (a note's resolved forward-links/backlinks), and `search` — a
  field-weighted BM25-style ranked keyword search (title=3x/tags=2x/
  body=1x, per `ADR-026`), computed fresh at query time with no persisted
  ranking index; body text is read fresh via `vault_writer.read_note()`
  per candidate note since `vault_indexing`'s own index entries never
  store it.
- feat: **`src/backend/app/api/vault_search_router.py` (new)** —
  `GET /vault-search/status|notes|notes/{stem}|search|tags`
  (`REQ-SB-02-US-01-T03`), registered in `app/main.py`. `/status` surfaces
  index readiness for the frontend's honest "nothing indexed yet" state;
  `/notes/{stem}` returns `404` for an unknown stem.
- feat: **`src/frontend/src/pages/VaultBrowserPage.tsx` +
  `NoteDetailPage.tsx` (new)** — the Browse & Search UI
  (`REQ-SB-02-US-01-T04`): a search box + ranked results, a tag-filter
  chip row + paginated browse list, a note-detail view with clickable
  forward-link/backlink navigation, and the honest "nothing indexed yet"
  state gating the whole page. New `features/vault-browser/client.ts` API
  client, new `styles/vault-browser.css` (`a.item-row`/`button.item-row`,
  `.tag-chip`, ported verbatim from the approved prototype). New
  `/browse`/`/browse/:stem` routes in `App.tsx`, new `Browse & Search` nav
  item in `Sidebar.tsx`.
- Verified live end-to-end against the real vault (503 unique-stem notes;
  `BUG-011`'s already-disclosed filename-stem collision, unaffected) and a
  real browser: all 7 locked ACs pass, including the ranking-relevance
  guarantee (`AC-04` — a note with only an incidental repeated body
  mention ranks strictly below a note with a real title/tag match) and
  genuine multi-hop wikilink click-through navigation. Full detail: each
  task's own Implementation Log under `Implementation/Tasks/
  REQ-SB-02-US-01-T01`..`T04`; `Implementation/Architecture/ADR.md` →
  `ADR-026`.

## 2026-08-13 — SPRINT-027 — REQ-SB-11-US-01 (Agent Activity & Error Observability)

- fix: **`src/backend/app/business/email_classification.py::
  run_capture_and_record_completion`** — honest-failure-recording fix
  (`REQ-SB-11-US-01-T01`). Meeting-capture's Autonomous branch now
  appends its own `"run_event"` success entry ("Capture run completed —
  N meeting(s) filed") — parity with email-capture, closing the gap
  where meeting-capture's successful runs were never recorded at all.
  Both capture steps' `run_capture_for_agent(...)` calls are now
  independently wrapped in their own `try/except`; an exception escaping
  either step's own per-item handling is caught and recorded as a new
  `"run_error"`-kind history entry ("Capture run failed — {exc}") instead
  of propagating uncaught — one step's failure never suppresses the
  other's own independent success/failure recording.
  `record_capture_run_completed()` now fires only when neither step
  failed this tick, preserving `last_capture_run.json`'s existing "only
  reached when nothing raised" semantics. Composed around the real
  current file (SPRINT-025's own `vault_indexing.rebuild_index()` call,
  landed after this task was authored, is preserved unconditionally).
- feat: **`src/backend/app/data_access/outlook_com.py::check_reachable()`
  (new)** — a lightweight, real, in-process Outlook COM reachability
  check (`REQ-SB-11-US-01-T02`), reusing `_connect_namespace()`'s already-
  proven connection mechanism; never raises past its own body, returns
  `{"reachable": bool, "detail": str | None}`.
- feat: **`src/backend/app/business/agent_activity.py` (new)** — read-only
  cross-agent activity-log aggregation (`REQ-SB-11-US-01-T02`).
  `list_activity_log()` composes every known agent's
  `"run_event"`/`"run_error"` history entries (via
  `agent_registry.list_agents()` + `vault_writer.load_agent_history()`),
  newest-first, excluding `"chat_user"`/`"chat_agent"`/`"proposal"`
  entries. `get_agent_activity()` returns `{"activity_log",
  "outlook_channel"}`, recomputed fresh on every call — no caching, no
  new persisted state.
- feat: **`src/backend/app/api/agent_activity_router.py` (new)** — `GET
  /agent-activity` (`REQ-SB-11-US-01-T03`), a thin passthrough to
  `agent_activity.get_agent_activity()`. Registered in
  **`src/backend/app/main.py`**.
- feat: **`src/frontend/src/pages/AgentActivityPage.tsx` (new)** — the
  Agent Activity page (`REQ-SB-11-US-01-T04`), per the approved prototype
  (`html-prototype/agent-activity.html`): a chronological Activity log
  card (per-entry Success/Failed badge, a failed entry's error detail
  shown inline, an honest empty state when nothing has run yet) and a
  Communication channels card (Outlook COM reachable/unreachable, with
  the real detail message on failure), plus a manual Refresh button.
  **`src/frontend/src/features/agent-activity/client.ts` (new)** —
  `fetchAgentActivity()`. New route (`/agent-activity`) in **`App.tsx`**
  and new nav item in **`Sidebar.tsx`**, positioned after System Health.
  Zero new CSS — composed entirely from already-ported `.card`/
  `.badge*`/`.log-list`/`.kv-list`/`.empty-state`/`.btn` classes.
- Verified live end-to-end against the real backend/vault/Outlook, no
  mocks: the real app-start scheduler tick alone produced the first-ever
  `meeting-capture` success entry; a real in-process-monkeypatched
  email-capture failure proved the `"run_error"` path, Scenario 3's
  cross-agent independence, and the `record_capture_run_completed()`
  gating (`finished_at` unchanged on the failed tick, advancing again on
  a genuine successful one). All 7 locked ACs (`AC-01`..`AC-07`) plus the
  nav-item structural check confirmed with real, live browser
  screenshots (OS-installed Edge headless mode) against real data,
  including a real, screenshot-confirmed Outlook-unreachable state
  (achieved via a temporary, port-identical, immediately-reverted backend
  swap, since physically closing Outlook silently auto-relaunches it on
  this machine via Windows COM). Full verification detail: each task's
  own Implementation Log under `Implementation/Tasks/REQ-SB-11-US-01-T01`
  ..`T04`.

## 2026-08-13 — SPRINT-029 — REQ-SB-04-US-01-T01/T02 (Agent Vault Write Access — buildable scope)

- feat: **`src/backend/app/api/mcp_auth.py` (new)** — per `ADR-025` point
  1: `require_hermes_shared_secret(app: ASGIApp) -> ASGIApp`, an ASGI
  middleware wrapping only the `/mcp` mount. Non-`"http"` ASGI scopes pass
  through unchanged (preserves Streamable HTTP's own SSE/streaming
  framing); an HTTP request whose real TCP peer (`scope["client"][0]`) is
  `127.0.0.1`/`::1` passes through unchanged (Second Brain's own in-app
  loopback MCP client stays unaffected); any other HTTP request must
  present a matching `X-Hermes-Shared-Secret` header or receives a plain
  `401`, with the underlying FastMCP app never invoked.
- feat: **`src/backend/app/config.py`** — new
  `Settings.hermes_mcp_shared_secret: str` field, `.env`-sourced,
  mirroring `compass_api_key`/`anthropic_api_key`'s existing shape.
  **`src/backend/.env.example`** gained a matching `HERMES_MCP_SHARED_SECRET=`
  line.
- feat: **`src/backend/app/main.py`** — the `/mcp` mount now wraps
  `mcp_server.streamable_http_app()` with `require_hermes_shared_secret(...)`;
  `mcp_server.py` itself untouched by this change.
- feat: **`src/backend/app/business/vault_write_tools.py` (new)** — per
  `ADR-025` points 4-6: `propose_vault_write(agent_id, subfolder,
  filename_stem, frontmatter, body)` rejects an unknown `agent_id`
  outright; for a known agent, checks `_is_within_assigned_scope` (a
  deliberate fail-closed stub, **always returns `False`** — no
  `REQ-SB-29-US-01` scope registry exists yet, so every write is honestly
  rejected as out of scope today, never silently allowed); if in scope
  (structurally unreachable until `REQ-SB-04-US-01-T03`), creates a new
  `trigger="hermes"` Pending Approval via
  `pending_approval_registry.create_pending_approval` and returns
  `{"status": "pending", ...}` — never writes directly. New
  `finalize_hermes_write(payload)` — the only function in this module
  that calls `vault_writer.write_note`, invoked exclusively via the
  Approve endpoint's dispatch table.
- feat: **`src/backend/app/api/mcp_server.py`** — registers
  `propose_vault_write` as a fifth `@mcp_server.tool()` (growing the same
  shared server, per `ADR-015` point 9 — no second server instance).
- feat: **`src/backend/app/api/pending_approvals_router.py`** —
  `_APPROVAL_HANDLERS` gains `"hermes_vault_write":
  vault_write_tools.finalize_hermes_write`; Decline needed no new code
  (the existing endpoint already resolves any `"pending"` record
  regardless of `action_id`/`trigger`).
- Verified live against the real backend/vault: `T01`'s 4 non-AC smoke
  checks (real loopback chat-triggered tool call unaffected; a simulated
  non-loopback caller — `httpx.ASGITransport(client=...)` — rejected `401`
  with no header, rejected `401` with a wrong secret, reached the real
  FastMCP app and completed a real tool call with the correct secret);
  `T02`'s locked `AC-03`/`AC-04` (a seeded `"hermes"` pending record's
  real Approve landed a real note with the exact supplied
  frontmatter/body and a real `run_event` history entry; a second seeded
  record's real Decline created no file and appended a real "Declined —
  no action taken" history entry); plus one additional real end-to-end
  MCP tool call against the live `propose_vault_write` front door,
  confirming the fail-closed scope seam honestly rejects every real
  invocation today with a clear message, never fabricated as `"pending"`.
  Full transcripts: each task's own Implementation Log.
- `REQ-SB-04-US-01-T03` (real scope enforcement, `AC-01`/`AC-02`) remains
  `Draft`/blocked on `REQ-SB-29-US-01`'s own decomposition (`ESC-026`,
  `Open`, unchanged) — the story stays `status: In Progress`, not `Done`;
  `SPRINT-029` itself reaches `Done` per its own deliberately-scoped
  Definition of Done.

## 2026-08-13 — SPRINT-025 — REQ-SB-01-US-01 (Vault Indexing)

- feat: **`src/backend/app/data_access/vault_writer.py`** —
  `_parse_frontmatter_value` gained a bracketed-list-value parsing branch
  (`tags: ["a", "b"]` now round-trips into a real `list[str]`, not the
  raw unparsed string); new public `extract_wikilink_targets(body) ->
  list[str]`, reusing the existing `_WIKILINK_PATTERN` constant.
- feat: **`src/backend/app/business/vault_indexing.py` (new)** — the
  project's first real, persistent, re-runnable vault index, per
  `ADR-024`: an in-memory, module-level singleton (`rebuild_index()`,
  `get_index()`), full-rebuild-and-atomic-swap on every trigger, deriving
  incoming-wikilink backlinks from every note's outgoing wikilinks.
- feat: **`src/backend/app/api/vault_index_router.py` (new)** —
  `POST /vault-index/rebuild`, an explicit on-demand re-index trigger
  (`ESC-021` resolved trigger path (a)), registered in `main.py`.
- feat: **`src/backend/app/business/email_classification.py`** — one new,
  unconditional `vault_indexing.rebuild_index()` call inside
  `run_capture_and_record_completion` (`ESC-021` resolved trigger path
  (b)) — the vault index now refreshes on every existing hourly-plus-
  app-start capture tick, with zero changes to
  `app/scheduling/capture_scheduler.py`.
- fix (finding, not this sprint's own scope): a real, pre-existing
  filename-stem collision was found live during `AC-01` verification —
  two distinct real notes (`Work/Emails/...SimplAI...md`,
  `Work/Notifications/...SimplAI...md`) share an identical 80-character-
  truncated filename stem, because `vault_writer._slugify`'s truncation
  silently discards `email_classification.py`'s trailing disambiguating
  id-suffix when the subject alone fills the 80-char budget. Not fixed
  here (out of this sprint's own file scope) — escalated as
  `ESCALATIONS.md` → `ESC-027` (Open), recommended for `/bug` capture.
- docs: `REQ-SB-01-US-01`, `SPRINT-025`, all 4 tasks (`T01`-`T04`) marked
  `Done`; `BACKLOG.md` REQ-SB-01/SPRINT-025 rows updated; `ESCALATIONS.md`
  → `ESC-027` (new); `REVIEW-QUEUE.md` pointers added (`ESC-027`,
  `SPRINT-025` retro harvest).

## 2026-08-13 — REQ-SB-02 (Browse & Search) — /design pass

- design: **`html-prototype/vault-browser.html` (new)** — a new top-level
  nav page: lists/browses all indexed notes (grounded in the real vault's
  own 496-note breakdown from `REQ-SB-01-US-01`'s direct inspection — 204
  Email, 134 Person, 51 Meeting, 6 Customer, 1 Partner), filters by tag
  (a real match and a genuine zero-match example), and runs a ranked
  keyword/full-text search — NOT a bare substring match, NOT
  embeddings/semantic search (`REQ-SB-06`, P2, stays deferred) — with an
  example result set where a note ranks last despite literally containing
  the query text as an incidental body substring, demonstrating
  relevance-over-substring directly. A top-level state-switcher
  demonstrates the honest "vault not indexed yet" state, visibly distinct
  from "indexed, but zero matches."
- design: **`html-prototype/note-detail.html` (new)** — a note's forward
  (outgoing) wikilinks and backlinks (incoming wikilinks) as a real,
  clickable LIST — explicitly NOT a visual/interactive graph canvas
  (resolved out of scope this pass, `ESC-022` `Resolved` 2026-08-13,
  matching `ADR-011`'s "proportionate first" precedent). A small, closed,
  three-note demo graph (an Email, a Customer hub, and a Meeting note, all
  tagged `customer/masdar` — the story's own example tag) makes every
  forward-link/backlink row a genuinely working click in a browser,
  including two honest empty-list edge cases grounded in
  `REQ-SB-01-US-01` Scenario 6's "empty list, not an error" index
  behavior.
- design: added two small additive CSS primitives to `styles.css`,
  composed entirely from existing tokens (no new hex, no framework):
  `a.item-row`/`button.item-row` (a real clickable variant of the
  existing plain-`<div>` `.item-row`) and `.tag-chip` (a pill-shaped
  clickable tag button reusing the existing `.state-switcher` click
  delegation in `app.js` — the tag filter and note-graph navigation both
  needed zero new shared JS). `note-detail.html` carries one small
  page-scoped inline script, not added to the shared `app.js`, that
  honors a `#hash` deep link from `vault-browser.html`'s note rows.
- design: added the new "Browse & Search" `.nav-item` to the shared
  sidebar on every existing prototype page (`index.html`,
  `agents-map.html`, `agents-map-exploration.html`, `my-day.html` + its 4
  drill-downs + `my-day-approvals.html`, `settings.html`,
  `system-health.html`, `agent-activity.html`), matching System
  Health/Agent Activity's own rollout precedent; added a new catalog card
  to `index.html`.
- docs: flagged for human browser sign-off — see `REVIEW-QUEUE.md`. Not
  yet approved; do not run `/plan-tasks REQ-SB-02` until it is (and until
  `REQ-SB-01-US-01` has reached `Ready`).

## 2026-08-13 — REQ-SB-11 (Agent Activity & Error Observability) — /design pass

- design: **`html-prototype/agent-activity.html` (new)** — a new
  top-level nav page (placement previously resolved, `ESC-025`
  `Resolved`) showing a chronological, cross-agent activity log (every
  completed background capture run, newest first, with its own
  success/failure outcome and — for a failure — its error detail visible
  inline, never dropped) plus a current status indicator for the Outlook
  communication channel, reported honestly as direct COM reachability
  (not "Hermes-wrapped" — no live Hermes connection exists in this
  codebase yet). Two independent `.state-switcher` groups demonstrate all
  7 Gherkin scenarios: "Activity recorded" (a mix of successes across
  both configured capture agents plus one real failure with detail) vs.
  "No runs yet" (the honest empty state), and "Outlook reachable" vs.
  "Outlook unreachable". Deliberately does not duplicate System Health's
  own MCP-mount, Provider-availability, or last-capture-run checks.
- design: reused `styles.css`'s existing `.log-list`/`.log-item`/
  `.log-item-meta` chronological-log primitive verbatim (already live on
  Agents Map's per-agent Communication History panel; this is its first
  cross-agent use) and System Health's `.kv-list`/`.badge-success`/
  `.badge-danger` shape for the channel-status card. Zero new CSS — a
  failed run's error detail is composed from existing `.text-muted` +
  a line break inside the same `.log-item`, not a new class.
- design: added the new "Agent Activity" `.nav-item` to the shared
  sidebar on every prototype page (`index.html`, `agents-map.html`,
  `agents-map-exploration.html`, `my-day.html` + its 4 drill-downs +
  `my-day-approvals.html`, `settings.html`, `system-health.html`),
  matching System Health's own rollout precedent; added a new catalog
  card to `index.html`.
- docs: flagged for human browser sign-off — see `REVIEW-QUEUE.md`. Not
  yet approved; do not run `/plan-tasks REQ-SB-11` until it is.

## 2026-08-13 — REQ-SB-42 / REQ-SB-43 / REQ-SB-44 — /design pass

- design: **`html-prototype/agents-map.html`** gains a new 6th
  state-switcher option, "Agent activity pulses (REQ-SB-42 demo)",
  demonstrated on both the overview and a Section drill-down: an animated
  per-agent glow (`.agent-node--activity-glow`, Email Capture — running a
  capture/Skill or generating a chat reply); a traveling pulse along a
  connecting line between two specific agents (Meeting Capture &harr;
  Vault Q&A — a Hub-routed cross-Section request, reusing the previously-
  unused `.affinity-line` primitive plus a new `.route-pulse-dot`, same
  SVG `animateMotion` technique as the KB's own synapse pulses); and a
  steady, non-animated highlight (`.agent-node--pending-approval`, People
  Notes — an open pending-approval record, reusing `--color-warning`, the
  same token `.chat-proposal`'s own pending card already uses). To-Do
  Capture is left idle for direct comparison. The existing decorative
  `kb-pulse-dot` KB&harr;Hub spoke animation is unaffected. The Section
  drill-down's own connecting-line geometry (routing the pulse along each
  Section's own Hub&rarr;agent line, captioned rather than drawn
  cross-Section) is the designer's own proposal, flagged for confirmation,
  not a locked decision.
- design: **`html-prototype/styles.css`** — new "Agent activity pulses
  (REQ-SB-42)" section: `.agent-node--activity-glow` (+ `agentActivityGlow`
  keyframes, reusing `kbPulse`'s own box-shadow-pulse recipe, recolored
  per-agent), `.agent-node--pending-approval`, `.route-pulse-dot`. New
  "3-panel Cockpit workspace (REQ-SB-43/REQ-SB-44)" section:
  `.cockpit-layout` (3-column grid), `.tag-chip--static` (plain,
  non-clickable no-Person-note chip fallback), `.chat-message-author`
  (per-Expert colored name label, reusing the existing
  `.hub-node-type`/`.agent-node-type` "small uppercase type-colored label"
  micro-pattern), `.draft-reply`/`.draft-reply-actions` (Inbox Cockpit's
  reviewable-only drafted-reply card, same recipe as `.chat-proposal`
  recolored to `--color-accent`).
- design: **`html-prototype/meeting-cockpit.html` (new)** — REQ-SB-43's
  3-panel Meeting Cockpit: available Agents to bring in + this meeting's
  own scoped quick-research list (left), one unified multi-agent chat with
  every brought-in Expert's reply visibly attributed to it (middle),
  meeting info + attendee chips including the plain non-clickable
  no-Person-note fallback (right, constant across states). 3 states:
  empty/first-open, in-progress (2 attributed Experts), quick-research
  pending a save/discard decision (nested `.chat-proposal`-style
  pending/saved/discarded switcher, mirroring `agents-map.html`'s own
  Meeting Capture approval-card convention).
- design: **`html-prototype/inbox-cockpit.html` (new)** — REQ-SB-44's
  3-panel Inbox Cockpit, the same pattern adapted for email: sender +
  CC'd/thread-participant chips (same fallback rule), an attachment-review
  section with its own has-attachment/no-attachments demo toggle, the same
  unified multi-agent chat, and a distinct draft-reply area showing
  reviewable text only — no send action anywhere on the page. 4 states:
  empty/first-open, in-progress, draft reply visible, quick-research
  pending.
- design: **`html-prototype/my-day-calendar.html`** — the two meeting
  `.item-row`s are now `a.item-row` (styles.css's existing clickable-row
  primitive), opening `meeting-cockpit.html`.
- design: **`html-prototype/my-day-emails.html`** — the three email
  `.item-row`s are now `a.item-row`, opening `inbox-cockpit.html`.
- design: **`html-prototype/index.html`** — added a catalog card pointing
  at the new "Agent activity pulses" demo state and the two new Cockpit
  screens.
- docs: flagged for human browser sign-off — see `REVIEW-QUEUE.md`. Not
  yet approved; do not run `/spec` on `REQ-SB-42-US-01`/`REQ-SB-43-US-01`/
  `REQ-SB-44-US-01` until it is (REQ-SB-42-US-01 also separately still
  needs the architect's own WebSocket-vs-SSE transport choice at
  `/plan-tasks`, and REQ-SB-44-US-01's attachments half is still blocked
  on `REQ-SB-28-US-01` reaching `Done`).

## 2026-08-13 — REQ-SB-38 (Agents Map Density Clustering) — /design pass

- design: **`html-prototype/agents-map.html`** gains a new 5th
  state-switcher option, "Density clustering (REQ-SB-38 demo)" —
  demonstrates a new clickable cluster marker ("+N" circle, per the
  operator's own literal request) that collapses a Section's own overflow
  agents once a proposed `VISIBLE_SLOT_CAP = 6` (per Section x Type-ring,
  designer's own proposal, flagged for sign-off) is exceeded, instead of
  rendering every agent at a fixed position regardless of count. A
  synthetic 15-agent "Illustrative Worker" dataset in the Technical
  Section (marked illustrative throughout, not real/planned agents)
  stress-tests the pattern since today's real ~7-agent roster never
  reaches it. Clicking the marker opens a NEW narrower drill-down scoped
  to just the clustered subset (10 agents), reusing the existing
  `.explore-drilldown`/`.hub-node`/`.agent-node`/`.cluster-line` "Agents
  Tree" pattern BUG-002's Option D already established — the same
  click-to-zoom mechanic applied one level deeper, wired through
  `agents-map.js`'s existing generic `wireDrilldown()` with only a
  widened element selector, no new interaction code. Clicking the
  Section's own Hub still shows the full, unclustered 15-agent drill-down
  (an intentional, explicitly-flagged open question — whether
  `layoutSectionDrilldown`'s own full-360° view also needs clustering is
  left undecided, per the PRD's own open question 2).
- design: **`html-prototype/styles.css`** — `.map-overflow-marker`
  (defined since REQ-SB-12's first pass, never instantiated until now)
  is now a real, clickable `<button>` — dashed-accent border + tinted
  glow at rest (matching `.hub-node`), hover-lift (matching
  `.agent-node`) — with two new inner spans,
  `.map-overflow-marker-count`/`-label`, mirroring `.hub-node`'s own
  bold-text + muted-subtext structure. No new hex, no new component
  family — the marker itself already existed as an unused primitive.
- design: **`html-prototype/agents-map.js`** — `wireDrilldown()`'s Hub
  click selector and `playIntro()`'s Hub-treatment selector each widened
  by one clause to also match `.map-overflow-marker[data-section-id]` —
  no new functions.
- docs: **new shared side-panel stand-in**
  (`[data-agent-detail="illustrative-worker"]` in `agents-map.html`'s
  `#agentPanel`) — every synthetic "Illustrative Worker" node shares one
  explanatory panel instead of 15 near-duplicate real ones; REQ-SB-13's
  real per-agent panel contract is unaffected for every real agent.
  Flagged for human browser sign-off — see `REVIEW-QUEUE.md`. Not yet
  approved; do not run `/spec REQ-SB-38` until it is.

## 2026-08-13 — Agents Map overview: BUG-009/BUG-010 fixes

- fix: **BUG-009** — agents could fan out past their own Section's wedge
  boundary into a neighboring Section on the Agents Map overview.
  `layoutAgents.ts`'s `SECTION_ARC_SPAN_DEG` was a fixed 80° fan-out
  applied regardless of section count; with 5 sections evenly spaced
  (72° wedges), a section with enough agents overflowed by 4°+ per side.
  Replaced with a span computed as `min(80deg, (360/n) * 0.8)`, capping
  the fan-out at 80% of the section's own wedge width. Verified live:
  `Email Capture` moved from -58° (inside Customers' wedge) to -47°
  (inside Productivity's own wedge); `Vault Filing Expert` moved from
  22° to 11°.
- fix: **BUG-010** — on hover, an agent's Type and Name labels rendered
  at the identical position on the Agents Map overview, directly
  overlapping and illegible. `.agent-node--compact:hover`'s label and
  type rules shared the same `top: 100%` anchor with no vertical offset
  between them. Type's rule now offsets to `top: calc(100% + 1.9em)`,
  clearing the label's own reveal box. Verified live with real rendered
  text — label and type now render with a clean 3px gap, zero overlap.

## 2026-08-13 — REQ-SB-36-US-01 (T04/T05) re-verification — SPRINT-022 follow-up

- docs: **Live re-verification of `REQ-SB-36-US-01`'s `AC-01`/`AC-03`
  (web-research skill), closing the real-credential gap flagged in
  `REVIEW-QUEUE.md` since `SPRINT-022`.** No source code changed. The
  operator provisioned a genuine `ANTHROPIC_API_KEY`/`ANTHROPIC_MODEL` in
  `src/backend/.env`. `AC-01` confirmed: a real, non-fabricated web-search
  result with real citations (`python.org`, Wikipedia) for a real,
  checkable query. `AC-03` confirmed: two queries engineered to have no
  real answer both honestly refused to fabricate a result (`sources: []`)
  — though the real observed shape (`found: true` + honest refusal text)
  differs from the `found: false` shape originally documented in `T04`, a
  live-discovered nuance recorded for human review, not a defect.
- fix (operational, not code): found and resolved a genuine root cause
  blocking re-verification — `.second-brain/agent_providers.json` had
  been seeded during `SPRINT-022`'s own original build with the inert
  placeholder credential, and `provider_registry` never auto-resyncs an
  already-persisted Provider's credential from `.env`. Resolved by
  deleting the stale state file to force the already-documented clean
  re-seed. See `MEMORY.md` → `## Constraints` for the standing rule this
  produced.
- docs: updated `Implementation/Tasks/REQ-SB-36-US-01-T04-web-research-
  skill-tool.md`, `...-T05-invoke-skill-args-and-router-body.md`,
  `Implementation/UserStories/REQ-SB-36-US-01-web-research-skill.md`, and
  `REVIEW-QUEUE.md`'s `SPRINT-022` entry with the re-verification results.

## 2026-08-13 — SPRINT-024 / REQ-SB-36-US-02 (T01-T03)

- feat: **Agent knowledge bootstrapping — delegated-research chain,
  Compass Expert pilot** (`REQ-SB-36`, `ADR-023`). New pilot Expert
  agent, `"compass-expert"` (`src/backend/app/business/agent_registry.py`
  — data only, no shape change), with one new declared action,
  `"build_knowledge"` (`"mutates": True`, trigger phrases "build my
  knowledge" / "build knowledge" / "research my subject").
- feat: **New `src/backend/app/business/agent_orchestration/
  knowledge_bootstrap.py`** — `async def bootstrap_agent_knowledge(
  agent_id, subject) -> dict`, a deterministic (never recursive/model-
  driven) three-hop composition of four already-real functions: Hop 1
  `graph.route_cross_section_request` (Hub routing to a Research
  Expert) → an Autonomous-mode check
  (`working_mode_registry.get_agent_working_mode`) → research
  (`skill_registry.invoke_skill(..., "web-research", {"query": ...})`)
  → Hop 2 `route_cross_section_request` (Hub routing to the Vault Filing
  Expert) → filing (`vault_filing_expert.determine_placement_and_file`,
  Tier 1 writes / Tier 2 defers to a real pending-approval record).
  Every branch (`written`/`pending_approval`/`no_match`/`no_results`/
  `not_autonomous`/`unavailable`) records one real `run_event` history
  entry; a `try/except` around the research call converts a genuine
  external-API failure (a bad/absent Provider credential) into the
  honest `no_results` outcome instead of crashing the chain — a real,
  live-verified finding (a genuine `401` from a real, unmocked Anthropic
  call was caught correctly), not a theoretical safeguard. Fully
  generic over `agent_id`/`subject` — never references `"compass"`
  anywhere in its own body, confirmed live with a second, throwaway
  pilot agent.
- feat: **`src/backend/app/api/agents_router.py`** — `"build_knowledge"`
  wired into the existing `_ACTION_HANDLERS`/`_invoke_action` funnel (no
  new endpoint): a new `_run_build_knowledge(agent_id)` handler resolves
  `subject` from the matched agent's own `"Subject"` setting and
  translates `bootstrap_agent_knowledge`'s own richer status shape into
  the shared `{"status", "message"}` envelope. Since the existing
  `_execute_action`'s own handler-calling convention (`handler()`,
  `len(results)`) is hardcoded to `run_capture_now`'s own shape and does
  not generalize to an async, `agent_id`-taking handler, added a NEW
  sibling `_execute_async_action` (mirrors `_execute_action`'s own
  Provider-availability gate) rather than modifying `_execute_action`
  itself, which `app/api/pending_approvals_router.py`'s own synchronous
  Approve dispatch still relies on unchanged. `_invoke_action` is now
  `async def` (its only two call sites, `trigger_action`/`chat`, both
  already `async def`, updated to `await` it); a new, generic
  `"history_recorded"` envelope flag prevents the existing generic
  post-call history append from double-recording an outcome the handler
  already recorded itself.
- Verified live end-to-end against the real backend, real vault, and
  real Compass Provider: `AC-01` (Scenario 1) via both the real chat
  trigger and the direct Available-Actions endpoint; `AC-02` (Scenario
  2, Tier-2 pause) — a real pending-approval record created for a
  genuinely new top-level area, both Hub hops and research already
  completed by the pause, per the real `vault_filing_expert` mechanism;
  `AC-04` (Scenario 4, no-match); `AC-05` (Scenario 5, honest failure) —
  two independent real paths, including a genuine live `401` from the
  real (provably-inert-credentialed) `"anthropic-claude"` Provider;
  `AC-06` (Scenario 6, generic capability) via a second, throwaway pilot
  agent and subject. `vault-qa` configured (real runtime data, not code)
  as this pilot's Research-Expert candidate (keywords, `web-research`
  skill access); `vault-filing-expert` gained one additional real
  keyword (`"vault"`) so Hop 2's routing genuinely matches it. **Honest,
  disclosed verification gap:** no real `ANTHROPIC_API_KEY` exists in
  this environment (provably-inert placeholder, per `SPRINT-022`'s own
  finding); the Tier-1 "written" and Tier-2 "pending_approval" full
  chain-composition outcomes (real Vault Filing Expert invocation, real
  Compass LLM placement call, real vault write / real pending-approval
  record) were proven live via the established, disclosed, reverted
  in-process-monkeypatch technique substituting only the externally-
  credential-gated research step. `REQ-SB-36-US-02-T04` (Scenario 3,
  "draw on afterward") remains `Draft`/blocked on `REQ-SB-29-US-01`'s
  own decomposition (`ESC-018`, still `Open`) — out of this sprint's own
  scope by design. Full reasoning: `Implementation/Architecture/ADR.md`
  → `ADR-023`; each task's own Implementation Log under
  `Implementation/Tasks/REQ-SB-36-US-02-T01`..`T03`.

## 2026-08-12 — SPRINT-022 / REQ-SB-36-US-01 (T01-T06)

- feat: **Real Anthropic Provider integration + `web-research` skill**
  (`REQ-SB-36`, `ADR-022`, corrected mid-build — see below). New
  `anthropic` dependency (`requirements.txt`, resolved `0.121.0`); new
  required `Settings.anthropic_api_key`/`anthropic_model`
  (`src/backend/app/config.py`, `.env.example`). New
  `src/backend/app/data_access/anthropic_client.py` — plain `anthropic`
  SDK client (not LangChain-wrapped), `web_search(api_key, model, query)
  -> {"found": bool, "summary": str, "sources": list[str]}`, calling
  Anthropic's own server-side web-search tool
  (`web_search_20250305`/`web_search`, confirmed current against the
  real, installed SDK). `src/backend/app/business/provider_registry.py`
  extended (not reworked): `_REAL_CLIENT_PROVIDER_IDS` gains
  `"anthropic-claude"`, `_seed_state()` additionally auto-seeds an
  `"Anthropic Claude"` Provider entry, new `get_provider(provider_id) ->
  dict | None` by-id lookup added.
- feat: **`src/backend/app/business/skill_tools.py`** gains a third real
  skill, `web-research` — `web_research(query: str, agent_id: str) ->
  dict`. Resolves the **invoking agent's own linked Provider**
  (`provider_registry.get_agent_provider(agent_id)`) and dispatches to
  the real Anthropic call only when that Provider is `"anthropic-claude"`
  with a real client; any other linked Provider (Compass, or none)
  returns the same honest "not yet available" shape `diagram-
  understanding` already established — never a fabricated result.
  `src/backend/app/business/skill_registry.py::invoke_skill` gains an
  additive `args` parameter, plus automatic `agent_id` injection for any
  handler whose own signature declares it (`diagram-understanding`'s
  zero-arg call is unaffected). `src/backend/app/api/skills_router.py`'s
  invoke endpoint gains an optional JSON body (`{"query": ...}`).
- fix: **Live-discovered skill-access tool-binding gap closed**
  (`ADR-022` point 6) — `src/backend/app/business/agent_orchestration/
  mcp_client.py::load_vault_query_tools()` returned every tool on the
  shared MCP server with no per-agent filtering, meaning any agent's
  ordinary chat turn could already reach `skill_tools.py`'s catalog
  regardless of `skill_registry.has_skill_access`. Replaced with
  `load_agent_tools(agent_id)`, which gates every `skill_tools.SKILLS`
  entry by `has_skill_access` while always keeping the four core
  vault-query tools; `graph.py::run_agent_conversation`'s call site
  updated accordingly (composed around the real, current file — matched
  `REQ-SB-20-US-01-T05`'s own already-landed shape exactly, no
  reconciliation needed).
- **Mid-build operator correction (`ESCALATIONS.md` → `ESC-019`,
  `ADR-022`'s own "Correction" addendum):** `ADR-022` point 3's original
  fixed-`"anthropic-claude"`-Provider-id design was reversed at the
  operator's own direct instruction — confirmed live first (not assumed)
  that Compass/GPT-5 has no real hosted web-search capability, so a
  Compass-linked agent must honestly report unavailable rather than
  fabricate a result from a plain completion.
- **Verified live** against the real running backend (real HTTP + direct
  calls): dependency install, `Settings` fail-fast, `provider_registry`
  seeding/credential-edit-takes-effect, the corrected Provider-resolution
  dispatch (Compass-linked → honest unavailable; Anthropic-linked → real
  dispatch attempt, confirmed via a real, honest `401` since no genuine
  API key is provisioned in this environment), `AC-02`'s `403` access
  refusal distinct from both the `200` honest-unavailable and the
  real-dispatch-attempt responses, and `load_agent_tools`'s own filtering
  logic (in-process monkeypatch, since this project's documented
  MCP-loopback port `8001` was held by an unkillable stale listener this
  session's tooling could not clear). **Open gap, honestly flagged, not
  hidden:** `AC-01`/`AC-03`'s own "produces a real relevant result" /
  "produces a real honest-empty result" branches could not be exercised —
  no genuine `ANTHROPIC_API_KEY` was available; a clearly-labeled,
  provably-inert placeholder was added to the real, gitignored `.env`
  purely so the app could boot for all other verification. See
  `REVIEW-QUEUE.md` for the follow-up.

## 2026-08-12 — SPRINT-023 / REQ-SB-35-US-01 (T01-T03)

- feat: **Vault Filing Expert — new registry agent, methodology-grounded
  placement/write, two-tier approval** (`REQ-SB-35`, `ADR-021`). New
  `"vault-filing-expert"` entry (`type: "expert"`, `actions: []`) in
  `src/backend/app/business/agent_registry.py`, reachable only via
  `REQ-SB-20`'s Hub-to-Hub cross-Section routing — real, persisted
  keywords assigned (`filing`, `tags`, `vault placement`, `categorize`,
  `new category`).
- feat: **`src/backend/app/business/vault_filing_methodology.py`** (new)
  — `build_placement_prompt(...)`, grounding a placement decision in a
  condensed excerpt of `Documentation/References/beyond-the-second-brain-
  methodology.md` plus `ADR-004`'s tag/folder split, alongside the three
  deterministically pre-fetched `list_known_kinds`/`list_known_customers`/
  `list_known_partners` lists (never left to the model to tool-call).
- feat: **`src/backend/app/business/vault_filing_expert.py`** (new) —
  `determine_placement_and_file(content, source_description,
  requesting_agent_id)`: one `model_factory.resolve_agent_model(
  "vault-filing-expert")` completion for a structured placement decision;
  `is_new_top_level_area` is always re-checked in Python
  (`kind not in known_kinds`), never trusted from the model's own
  boolean. **Tier 1** (existing category, or a new tag/subfolder within
  an existing top-level area) writes immediately via `vault_writer.
  write_note`, with a numeric-suffix collision guard
  (`_unique_filename_stem`) and a visible uncertainty marker on
  low-confidence placements (never silently dropped, placement never
  pauses). **Tier 2** (a genuinely new top-level area) unconditionally
  calls `pending_approval_registry.create_pending_approval(...)` —
  `working_mode_registry` is never referenced anywhere in this module,
  bypassing the working-mode gate by construction, not a conditional
  check — and returns `{"status": "pending_approval", ...}`; content is
  written only once `finalize_new_top_level_area(payload)` runs on
  Approve. A written note's `customer`/`partner` frontmatter field plus a
  real `[[wikilink]]` to the referenced entity's hub note (via
  `customer_hub_linking`/`partner_hub_linking`, reused as-is) are added
  mechanically whenever the model names one — required for the new
  entity to be discoverable via `list_known_customers()`/
  `list_known_partners()`, not just tagged.
- feat: **Tier-2 approval resolution** — `pending_approval_registry.
  create_pending_approval` gained an additive `payload: dict | None =
  None` parameter, stored verbatim on the record (every existing
  zero-payload caller unaffected). `src/backend/app/api/
  pending_approvals_router.py`'s Approve endpoint gained a new
  `_APPROVAL_HANDLERS` dispatch table (`{"propose_new_top_level_area":
  vault_filing_expert.finalize_new_top_level_area}`), consulted before
  the existing `_execute_action`/`run_capture_for_agent` re-dispatch.
  Decline needed no new code — `resolve_pending_approval(id, "declined")`
  alone is sufficient; `finalize_new_top_level_area` is never called for
  a declined record.
- Verified live end-to-end against the real backend `.venv`, real vault,
  and a real Compass Provider call, against all 8 locked ACs: an
  existing-category placement (`AC-01`); a genuinely new customer tag
  within an existing kind folder, discoverable via
  `list_known_customers()` (`AC-02`); real methodology + live-vault
  grounding, with real tags/wikilinks (`AC-05`); an honest, visible
  low-confidence marker that never pauses placement (`AC-06`); real
  Hub-routing discoverability with no separate write path elsewhere
  (`AC-07`); a numeric-suffix filename-collision guard that never
  overwrites (`AC-08`); a genuinely-new-top-level-area proposal that
  creates an identical pending-approval outcome regardless of the
  agent's own working mode — `autonomous` and `supervised` both tested —
  and writes only on Approve (`AC-03`); and an honestly-recorded decline
  that never files the content and is never silently retried elsewhere
  (`AC-04`).

## 2026-08-12 — SPRINT-021 / REQ-SB-21-US-01 (T01-T09)

- feat: **Agent Working Modes — Autonomous / Supervised / Manual**
  (`REQ-SB-21`, `ADR-018`/`ADR-020`). New sibling `.second-brain/
  agent_working_modes.json` (self-healing default `"autonomous"`),
  owned by new `src/backend/app/business/working_mode_registry.py`
  (`get_agent_working_mode`/`set_agent_working_mode`/
  `VALID_WORKING_MODES`), composed alongside `agent_registry.py`
  (unmodified).
- feat: **Pending Approvals workflow store** — new sibling
  `.second-brain/agent_pending_approvals.json` (this project's first
  use of `uuid`), owned by new `src/backend/app/business/
  pending_approval_registry.py` (`list_pending_approvals`/
  `get_pending_approval`/`create_pending_approval`/
  `resolve_pending_approval`; idempotent per `agent_id`+
  `trigger="background"` only).
- feat: **Corrected two-axis working-mode gate** — `src/backend/app/
  business/agent_registry.py` gained a static `"mutates": bool` field
  on every action definition plus a new `get_action(agent_id,
  action_id)` lookup helper (`ADR-020` point 1, fail-safe to `True` for
  an unresolvable action). `src/backend/app/api/agents_router.py`'s
  `_invoke_action` was split into the gate + the existing unconditional
  dispatch (renamed `_execute_action`): **Supervised** gates on the
  action's own `mutates` classification, regardless of trigger; a
  read-only action proceeds immediately even while Supervised, only a
  mutating one proposes-and-waits. **Manual** gates on trigger source —
  a direct chat/button ask always executes immediately; a new
  `"hub_routed"` trigger value is refused outright (currently a no-op,
  forward-looking correctness for a future cross-agent action-invoke
  story). `GET`/`PATCH /agents/{agent_id}` gained an additive
  `working_mode` field. `src/backend/app/business/
  email_classification.py::run_capture_and_record_completion` gained
  the paired background-pipeline gate (new shared
  `run_capture_for_agent(agent_id, limit)` helper) — Autonomous runs
  unchanged, Supervised creates a `trigger="background"` pending
  approval instead of running, Manual skips silently, no record.
- feat: **`Pending Approvals` HTTP surface** — new `src/backend/app/api/
  pending_approvals_router.py` (`GET /pending-approvals[?status&
  agent_id]`, `GET /pending-approvals/{id}`, `POST /pending-approvals/
  {id}/approve|decline`); Approve calls `_execute_action`/
  `run_capture_for_agent` directly, bypassing the gate (the approval
  itself is the authorization — re-entering the gate would infinite-
  defer). Registered in `src/backend/app/main.py`.
- feat: **Agent Settings working-mode picker + live `.chat-proposal`
  card** — `src/frontend/src/features/agents-map/agentsApiClient.ts`
  (`AgentDetail`/`updateAgentAssignment`/`AgentHistoryEntry` gained
  `working_mode`/`"proposal"` kind/`pending_approval_id`, additive);
  new `pendingApprovalsApiClient.ts`; `AgentDetailPanel.tsx` gained a
  Working-mode `<select>` kv-row and renders a `"proposal"`-kind
  Communication History entry as a `.chat-proposal` card with live-
  resolved Pending/Approved/Declined status and working Approve/
  Decline. `src/frontend/src/styles/agent-panel.css` gained the
  `.chat-proposal*` rules, ported verbatim from the approved
  `html-prototype/styles.css`.
- feat: **Standalone Pending Approvals page** — new
  `src/frontend/src/pages/MyDayApprovalsPage.tsx` (route
  `/my-day/approvals`), a new `App.tsx` route, and a new "Pending
  Approvals" card on `MyDayPage.tsx` with its own live pending count
  (fetches `GET /pending-approvals` directly — `my_day.py`/
  `my_day_router.py` untouched).
- fix: an unresolvable `pending_approval_id` on a `"proposal"`-kind
  history entry (live-discovered, leftover smoke-check debris) produced
  an unhandled promise rejection in `AgentDetailPanel.tsx`'s new
  card-resolving effect — fixed with `.catch(() => {})`.
  Verified live end-to-end against all 8 locked ACs (`AC-01`..`AC-08`)
  via the real backend, real frontend (headless-Chrome-via-CDP), the
  real vault, and real Outlook/Compass integration — including several
  genuine capture runs and a live Approve click driving a real
  39-meeting sweep. Full reasoning and transcripts:
  `Implementation/Tasks/REQ-SB-21-US-01-T01`..`T09`'s own Implementation
  Logs; `Implementation/UserStories/REQ-SB-21-US-01-agent-working-
  modes.md`; `Implementation/Architecture/ADR.md` → `ADR-018`/`ADR-020`.

## 2026-08-12 — SPRINT-020 / REQ-SB-20-US-01 (T01-T06)

- feat: **Section Hub Intelligence & Cross-Section Routing** — per-agent
  free-text keywords and Hub-mediated cross-Section request routing
  (`REQ-SB-20`, `ADR-017`). `src/backend/app/data_access/vault_writer.py`
  gained `load_agent_keywords`/`save_agent_keywords`/
  `load_all_agent_keywords` (new sibling `.second-brain/
  agent_keywords.json`, `{agent_id: [keyword, ...]}`); new
  `src/backend/app/business/agent_keywords.py` (`get_agent_keywords`/
  `set_agent_keywords`/`list_candidate_agents_for_keyword_match` —
  deterministic, case-insensitive, cross-Section-only keyword-substring
  matching, `ADR-011`'s posture one layer up); `src/backend/app/api/
  agents_router.py`'s `GET`/`PATCH /agents/{agent_id}` gained an additive
  `keywords` field (explicit `[]` clears, omitted is a no-op).
- feat: **`route_hub_request` LangGraph node + `request_cross_section_help`
  tool** — `src/backend/app/business/agent_orchestration/graph.py` gained
  one new node on the same compiled graph, a new local (never-MCP-
  registered) tool intercepted before the graph's own generic
  `_execute_tools` path, and a directly-callable
  `route_cross_section_request(requesting_agent_id, need_description)`
  public entry point representing the mandatory "own Hub, then target Hub"
  two-hop relay as two sequential lookups, both hops recorded as explicit
  result fields (`from_section_id`/`matched_section_id`). `src/backend/app/
  business/agent_orchestration/state.py`'s `AgentConversationState` gained
  `hub_routing_result: dict | None`.
- feat: **Agent Settings Keywords row** —
  `src/frontend/src/features/agents-map/agentsApiClient.ts` (`AgentDetail`/
  `updateAgentAssignment` gained `keywords`, additive) and
  `AgentDetailPanel.tsx` (new commit-on-blur free-text Keywords kv-row,
  comma-separated, whitespace/empty entries dropped on commit).
  Verified live end-to-end against all 4 locked ACs: a real cross-Section
  match with both relay hops explicit and inspectable; an honest,
  byte-identical-across-4-repeats no-match; an empty-keyword agent
  structurally never selected across 5 varied need-descriptions (including
  one textually overlapping its own name); the Keywords field's full
  round-trip (empty state with placeholder → commit → persisted across a
  real panel close/reopen → independent backend `GET`), via headless-
  Chrome-via-CDP. Full reasoning and transcripts:
  `Implementation/Tasks/REQ-SB-20-US-01-T01`..`T06`'s own Implementation
  Logs; `Implementation/UserStories/REQ-SB-20-US-01-section-hub-
  intelligence-and-cross-section-routing.md`.

## 2026-08-12 — SPRINT-019 / REQ-SB-31-US-01 (T01-T04)

- fix: **`run_agent_conversation` crash-gap fix (T01, Scenario 8)** —
  `src/backend/app/business/agent_orchestration/graph.py`'s outer body
  (`await mcp_client.load_vault_query_tools()` through `await
  _GRAPH.ainvoke(initial_state)`) is now wrapped in the same
  honest-failure-funnel `try/except Exception as exc: return {"error":
  ...}` pattern `_call_model` already used — an unexpected exception in
  MCP tool loading or graph invocation itself now returns an honest
  `{"error": ...}` instead of propagating as a raw, unhandled 500.
  Verified live via an in-process monkeypatch inducing a real exception
  for an agent whose Provider is otherwise available, then a reverted
  normal call confirmed to still succeed.
- feat: **System Health View (T02-T04)** — new read-only status
  aggregation surface (`REQ-SB-31`). `src/backend/app/business/
  system_health.py` (new — `get_system_health()`, `mcp_mount_reachable()`,
  `list_disabled_agents()`, composing `provider_registry`/
  `agent_registry`/`vault_writer` as-is, plus one local `GET /mcp`
  loopback reachability check); `src/backend/app/api/
  system_health_router.py` (new — `GET /system-health`), registered in
  `app/main.py`; `src/frontend/src/features/system-health/client.ts` +
  `src/frontend/src/pages/SystemHealthPage.tsx` (new — Health Issues / MCP
  path / Providers / Last capture run cards, zero new CSS), wired into
  `App.tsx` (`/system-health` route) and `Sidebar.tsx` (new nav item),
  per the approved prototype `html-prototype/system-health.html`.
  Verified live end-to-end: the real "everything healthy" state (MCP
  reachable, all 5 agents on Compass, a real completed capture run); a
  real induced "issues present" state (MCP mount pointed at an
  unreachable port + a throwaway no-real-client Provider assigned to one
  agent) showing both as Health Issues simultaneously, then reverted; the
  real vault's `last_capture_run.json` temporarily moved aside and
  restored to prove the honest "no run has completed yet" empty state
  (never a fabricated timestamp); every state change confirmed to reflect
  on the very next call/reload with no caching. One real, live-discovered
  bug found and fixed in-scope: `mcp_mount_reachable()`'s `httpx.get()`
  call needed `follow_redirects=True` — the real `/mcp` mount 307-redirects
  `GET /mcp` → `GET /mcp/` before answering its documented 406 "alive"
  signal, and `httpx.get()`'s own default (`follow_redirects=False`)
  stopped at the redirect, which would have falsely shown MCP as
  unreachable even when healthy. Full reasoning and transcripts:
  `Implementation/Tasks/REQ-SB-31-US-01-T01`..`T04`'s own Implementation
  Logs; `Implementation/UserStories/REQ-SB-31-US-01-system-health-view.md`.

## 2026-08-12 — SPRINT-018 / REQ-SB-33-US-01-T01

- feat: **Agent grounding & honest-uncertainty guardrail** —
  `history_entries_to_messages`'s single prepended `SystemMessage`
  (`src/backend/app/business/agent_orchestration/state.py`) now carries a
  grounding/honest-uncertainty instruction alongside the existing identity
  sentence: answer only from real tool results/history/memory, honestly
  report a failed tool call rather than inventing a substitute, and say
  "I don't know" rather than answering from the model's own general
  training knowledge as if it were a vault fact. Still exactly one
  `SystemMessage`, applied globally to every agent's real conversational
  reply path (`REQ-SB-25`), unconditional, no per-agent config. Verified
  live against all 4 locked ACs: a real tool-backed question still answers
  normally (exact match against the real vault's known-customer list); a
  real vault-scoped question with no matching data gets an honest "I don't
  see it"; two real induced tool-call-failure passes (one tool failing
  with a real fallback recovery, then every tool failing with no
  fallback) both produce an honest failure report, never a fabricated
  substitute; a question inviting a general-knowledge fact about a real
  vault entity (ADNOC) is honestly declined rather than answered from
  training knowledge. Full reasoning and transcripts:
  `Implementation/Tasks/REQ-SB-33-US-01-T01-grounding-honest-uncertainty-system-prompt.md`.

- design: **System Health View prototype (`REQ-SB-31`)** — new
  `html-prototype/system-health.html` top-level nav page (operator-directed
  placement, 2026-08-12), wired into the shared sidebar `.nav-item` list on
  every prototype page. Shows a Health Issues list (empty "No Health
  Issues" state, or the MCP/agent-orchestration path plus any agent whose
  Provider has no real client — shown `Disabled`, listed as a Health Issue,
  per the operator's scoped 2026-08-12 override), an MCP/agent-orchestration
  status row (`GET /mcp` reachable/unreachable), a Providers status list
  rolled up per distinct Provider (unchanged, neutral "no real client"
  honesty language — the override applies to the affected agent, not the
  Provider row), and a last-capture-run status row reading
  `.second-brain/last_capture_run.json`'s recorded completion time or its
  honest absence. Two state-switcher groups demonstrate all 8 Gherkin
  scenarios from `REQ-SB-31-US-01`; Scenario 8 (backend-only crash-gap fix)
  has no UI region, per the story's own Non-Goals. Composed entirely from
  existing tokens/components — `.card`, `.badge-*`, `.kv-list`/`.kv-row`,
  `.item-list`/`.item-row`, `.state-switcher`, `.empty-state` (its first
  real use). No new CSS. Always flagged for human browser sign-off — see
  `REVIEW-QUEUE.md`. **Approved 2026-08-12** after live verification via a
  new temporary static-file preview server (`tools/run-prototype.cmd`,
  registered in `.claude/launch.json` as `second-brain-html-prototype`,
  port 8088) — needed because this environment's `file://` preview renders
  `html-prototype/` as a static, non-interactive snapshot, so the
  state-switcher toggle JS couldn't be exercised without a real HTTP
  server.

- feat: Agent detail panel (`AgentDetailPanel.tsx`) — restructured into
  Chat/History/Settings tabs, per direct operator feedback ("the Chat
  Window is very small... My Recommendations is to have a Tab System").
  Previously all three sections stacked in one scrolling column, with
  the chat thread capped at a fixed `220px` (`.chat-thread`'s old
  `max-height`) squeezed between Settings/Actions above and
  Communication history below. Now: panel widened `440px` → `560px`
  (`.side-panel`), Chat is the default tab and its thread fills the
  panel's full remaining height (`.side-panel-section--chat`, `flex: 1`
  chain from `.side-panel-body` down). Also added, addressing "I don't
  have any indication that something is happening in the background":
  a `sending` state disables the input/Send button and shows an
  animated three-dot typing indicator (`.chat-message--pending`,
  `.chat-typing-dot`) in the thread itself while waiting for a real
  Compass reply (now several seconds, per the async chat fix above);
  auto-scrolls to the newest message/indicator. Also added real error
  handling — `handleSend` previously had no `try`/`catch` at all, so a
  failed request silently did nothing; now shows an honest inline error
  message (`.chat-message--error`) and always re-enables the input,
  never leaving the panel stuck. Live-verified end-to-end: sent a real
  question, watched the typing indicator for its full ~14s duration,
  received and rendered a genuinely useful, vault-grounded reply.

- fix: **Real conversational agent chat was completely broken in the real
  running app** (every message either silently hung or 500'd) — found
  live while investigating the operator's "chat is still not working"
  report, 2026-08-12. Root cause: `agents_router.py::chat` was a sync
  `def`, so FastAPI scheduled it via `run_in_threadpool` (a worker
  thread); inside that thread, `run_agent_conversation` called
  `asyncio.run(...)` to bridge into the MCP client's async loopback
  call — a **second event loop, in a worker thread, trying to connect
  back into the same single-process server**. That self-connection
  reliably failed with `httpcore.ConnectError: All connection attempts
  failed`, even though the identical MCP client call succeeded instantly
  when run as a standalone script (confirmed via a direct isolated
  test — proved the MCP server itself was fine, the bug was specifically
  in the nested-event-loop self-connection). Separately, and compounding
  it: `agent_orchestration/mcp_client.py`'s loopback URL was hardcoded to
  port `8002` — a workaround an earlier build session left in place for
  a *different*, session-local problem (port 8001 stuck due to an
  orphaned `uvicorn --reload` worker) — restored to this project's real
  documented port, `8001`. **Fix:** made the whole chain genuinely
  async — `agents_router.py::chat` is now `async def` and `await`s
  `run_agent_conversation` directly (no thread pool); `graph.py`'s
  `run_agent_conversation` is now `async def`, using `await
  mcp_client.load_vault_query_tools()` and `await _GRAPH.ainvoke(...)`
  instead of `asyncio.run()`/`.invoke()`; `_execute_tools` (the graph's
  tool-execution node) is now an async node using `await
  tool.ainvoke(...)` instead of its own nested `asyncio.run()`. One
  event loop for the whole request, start to finish — no self-connection
  possible. Live-verified: a real question ("What kinds of notes exist
  in my vault right now?") now returns a real Compass-backed reply in
  ~7 seconds, confirmed both via direct API call and through the actual
  chat UI.

- feat: My Day — added a day-navigator (← Wed, Aug 12 → / "Jump to
  today") to the dashboard, per direct operator request ("I meant to
  have a My Day view but I can have a Calendar or a Slider or something
  on the top where I can move between different days"). Backend:
  `app/business/my_day.py`'s `summary()`/`list_email_items()`/
  `list_calendar_items()` gain an optional `day` parameter — narrows
  results to that single date instead of the full 7-day window when
  provided; `window` in the summary response always reflects the full
  navigable range regardless of `day`, so the frontend can render both
  "which day is selected" and "what range can I navigate within"
  simultaneously. `app/api/my_day_router.py`'s three endpoints accept an
  optional `?day=YYYY-MM-DD` query param, validated (`400`) against the
  current window bounds — a day outside the real navigable range is
  rejected, not silently clamped or ignored. Frontend: `MyDayPage.tsx`
  defaults to today, steps by whole days, disables Previous/Next at the
  window edges, and passes the selected day through to each section's
  drill-down link (`?day=...`). `MyDayEmailsPage.tsx`/
  `MyDayCalendarPage.tsx` now read that `day` search param
  (`useSearchParams`) and pass it through to their own fetch calls,
  re-fetching when it changes — clicking through from a selected day
  shows that day's items, not the whole week's, closing the loop between
  the dashboard and its drill-downs. Live-verified end-to-end: stepping a
  day changes the dashboard counts (Aug 12: 1 email/6 meetings; Aug 11: 6
  emails/2 meetings), the boundary correctly clamps at `Aug 9` with
  Previous disabled, and `/my-day/calendar?day=2026-08-12` shows exactly
  that day's 6 meetings, chronologically sorted.

- fix: My Day — `app/business/my_day.py`'s `list_email_items()`/
  `list_calendar_items()` now sort their results chronologically
  (`items.sort(key=...)` on `received`/`start`) — previously returned in
  vault-scan order, which read as arbitrary/unrelated to time on both the
  Emails and Calendar drill-down pages. `summary()` now also returns a
  `window: {start, end}` field (the same `_compute_window()` value
  already computed on every call, just never surfaced) — the frontend
  (`MyDayPage.tsx`) now displays "Showing Aug 9 – Aug 15" so the active
  rolling-7-day range is actually visible, not just correctly applied
  invisibly. `MyDaySummary` (`features/my-day/client.ts`) widened to
  match. Live-verified: calendar items now return in strict chronological
  order; the date range renders correctly on the real page.

- fix: Agents Map — Section Hub node resized and repositioned
  (`src/frontend/src/features/agents-map/polarLayout.ts`'s `HUB_RADIUS`
  32 → 21; `.hub-node`'s CSS width 11% → 6%, `src/frontend/src/styles/
  agents-map.css`), per direct operator request: the Hub was sitting
  almost exactly on top of the Producer ring (radius 30 vs. the Hub's own
  32), so its own visual disk physically overlapped the entire Producer
  ring band — freeing that space lets Ring 3 (Producer, innermost) be
  used exclusively for agent nodes going forward, and incidentally fixes
  `BUG-004` (a Producer-type agent rendering on top of a neighboring
  Section's Hub) as a direct consequence. Live-verified: Hub visual size
  now 42px (was 77px) at the real canvas scale, placement now 147px from
  center (was 224px), zero DOM-rect overlaps between any agent node and
  any Hub across all 5 real seeded agents. `RING_RADIUS` itself
  (Worker/Expert/Producer) is unchanged — this is a Hub-only adjustment.

- fix: `REQ-SB-08-US-01-T06` (`SPRINT-017`) rebuilt exactly per `ADR-019`
  and live-verified — the **second** Meetings-occurrence dedup/filename-key
  fix for the same finding class, and the one that actually holds up under
  live testing. `src/backend/app/data_access/outlook_com.py`:
  `_resolve_global_appointment_id`/`_PR_GLOBAL_APPOINTMENT_ID_DASL` removed
  (dead code); `list_calendar_events` no longer resolves, returns, or skips
  on any per-occurrence Outlook identity field, reverted to appending every
  successfully-read item; docstring rewritten. `src/backend/app/
  data_access/vault_writer.py`: `meeting_note_filename_stem`/
  `meeting_note_path`/`meeting_note_exists`/`create_meeting_note_baseline`
  drop the trailing identifier parameter entirely — the filename/dedup
  suffix is now an 8-hex-char SHA-256 prefix of `f"{subject}|{start}"`
  (full precise `start` timestamp, not any Outlook identity field, not a
  raw slice); `resolve_meeting_note_path` drops to two tiers (new scheme,
  then the legacy `EntryID`-suffix scheme, `ADR-013` point 3 reused
  unmodified) — the `GlobalAppointmentID`-hash middle tier is not carried
  forward; `mark_meeting_processed`'s parameter renamed `global_
  appointment_id` → generic `marker`, now fed the resolved note's own
  filename stem. `src/backend/app/business/meeting_classification.py`:
  `classify_recent_meetings` updated to match — no longer reads or threads
  `event["global_appointment_id"]` anywhere. Live-verified against the
  real Outlook calendar and vault: the real recurring series that
  originally triggered `ESCALATIONS.md` → `ESC-002`/`ESC-012` ("Weekly
  Forecast l Strategic/Major Clients") now produces 6 distinct filename
  suffixes for its 6 real occurrences; zero of the 39 originally-named
  pre-existing Meeting notes touched (confirmed via real `LastWriteTime`
  comparison across all 40 pre-existing files). `ESC-002`/`ESC-012` both
  flipped to `Resolved`. One honestly-flagged, non-blocking live discovery
  — a 40th pre-existing Meeting note (created between sessions by the
  then-still-live old code) plus a genuine mid-session calendar reschedule
  produced one real, bounded, recoverable duplicate note outside the 39
  named notes — recorded in full in `Implementation/Tasks/
  REQ-SB-08-US-01-T06-global-appointment-id-dedup-key-fix.md`'s own
  Implementation Log and flagged in `REVIEW-QUEUE.md` for human spot-check.
  `SPRINT-017` closes `Done`.

- docs: `ADR-019` written (`Implementation/Architecture/ADR.md`) — the
  **second** superseding ADR for the Meetings-occurrence dedup/filename key
  in two days. Live verification of `ADR-013`'s own fix
  (`REQ-SB-08-US-01-T06`, `SPRINT-017`) found `AppointmentItem.
  GlobalAppointmentID` has the exact same non-uniqueness defect on this
  Outlook installation that `EntryID` had (`ESCALATIONS.md` → `ESC-012`).
  `ADR-019` supersedes `ADR-013`'s Decision points 1 and 2 (`ADR-013`'s own
  `Status:` updated to `Superseded by ADR-019`, point 3 unmodified and
  reused): the new dedup/filename key is an 8-hex-char SHA-256 hash of
  `subject` + the occurrence's own full, precise start timestamp
  (`list_calendar_events`'s existing `start` field, previously only used
  coarsely as the filename's date component) — a structural uniqueness
  guarantee (two distinct calendar occurrences cannot share an identical
  start moment), not an empirical claim about any Outlook COM property's
  behaviour. `ADR-013`'s own middle `GlobalAppointmentID`-hash fallback
  tier is deliberately dropped (confirmed live that zero real Meeting
  notes were ever created under it); `ADR-013`'s legacy-`EntryID`-path
  coexistence check is reused unmodified — none of the 39 already-captured
  real Meeting notes needs migrating. `architecture.md`'s "Meeting Notes &
  Calendar-Attendee Extraction (REQ-SB-08)" → "Occurrence dedup key" bullet
  rewritten a third time to match. `REQ-SB-08-US-01-T06`'s own task file is
  redesigned in place around `ADR-019` (its prior `ADR-013`-based spec and
  live-verification Implementation Log kept, unedited, as history) —
  `status:` reset `Blocked → Ready`. `ESCALATIONS.md` → `ESC-012` flipped to
  `Resolved` (design-level; `T06` still needs rebuild + live re-verification
  to close operationally), `ESC-002` updated with a pointer to the same
  resolution. `REVIEW-QUEUE.md`'s `REQ-SB-08-US-01-T06`/`SPRINT-017` entry
  updated in place to carry the new review pointer. No code changed yet in
  this pass — this is the architect-stage design correction;
  `REQ-SB-08-US-01-T06` still needs to be rebuilt against this new design.

- feat: `REQ-SB-26-US-01` (Agent Memory, `SPRINT-015`) shipped end-to-end
  and verified live, per `ADR-016`. `src/backend/app/data_access/
  vault_writer.py` gained `load_agent_memory(agent_id)`/
  `append_agent_memory_entries(agent_id, facts)` (new
  `.second-brain/agent_memory.json`, `{agent_id: [{"fact": str,
  "recorded_at": iso8601}, ...]}`, mirroring `load_agent_history`/
  `append_agent_history_entry`'s exact shape). `app/business/
  agent_orchestration/state.py`'s `AgentConversationState` gained
  additive `memory: list[dict]`/`extracted_facts: list[str]` fields.
  `app/business/agent_orchestration/graph.py`'s compiled graph gained two
  new nodes on `REQ-SB-25-US-01`'s same graph — `retrieve_memory` (read
  path, folds stored facts into the message list as a second
  `SystemMessage` before `call_model`) and `extract_memory` (write path,
  reuses the already-resolved model for one additional, narrowly-scoped
  completion after a final reply, honestly returning no facts rather than
  inventing one) — composed around the real `call_model`⇄`execute_tools`
  tool-calling loop, not a blind replacement of it (a live-discovered
  correction vs. `T03`'s own literal code sample — see `T03`'s own
  Implementation Log and `REVIEW-QUEUE.md`). `run_agent_conversation`
  gained an additive `memory` parameter and an `"extracted_facts"` key on
  its success-path return (never present on the `{"error": ...}` path).
  `app/api/agents_router.py::chat`'s no-trigger-phrase-match branch now
  loads memory once before calling `run_agent_conversation` and persists
  any `extracted_facts` afterward. Verified live end-to-end against the
  real backend/vault/Compass Provider, all 4 locked ACs: a fact stated in
  one conversation ("My favourite customer is Acme Corp") correctly
  recalled in a later, separate conversation (isolated from
  `REQ-SB-25`'s own history-replay mechanism by clearing that agent's
  history entry beforehand); a second, unrelated agent showed no
  awareness of it (`agent_memory.json` confirmed no cross-agent entry);
  an agent asked to recall something never actually shared honestly said
  it didn't know, with no fabricated entry written; and the fact
  survived a full backend process restart. Full reasoning:
  `Implementation/Architecture/ADR.md` → `ADR-016`.
- feat: `REQ-SB-27-US-01` (Skills Repository — registration and
  per-agent access, plumbing only, `SPRINT-015`) shipped end-to-end and
  verified live, per `ADR-015`. New `app/business/skill_tools.py` (a
  sibling to `vault_query_tools.py`) holds a small, literal `SKILLS`
  catalog (`id`/`name`/`description`) and one illustrative,
  `@mcp.tool()`-decorated stub skill (`diagram_understanding`) registered
  on the same shared `FastMCP` instance `app/api/mcp_server.py` exposes
  for `vault_query_tools.py` — its body unconditionally returns an honest
  "not yet available" response, never a fabricated result. New `app/
  data_access/vault_writer.py` primitives `load_skills_state()`/
  `save_skills_state(state)` (new `.second-brain/agent_skills.json`,
  `{"assignments": {<agent_id>: [<skill_id>, ...]}}`, mirroring
  `load_sections_state`/`save_sections_state`). New `app/business/
  skill_registry.py` (mirrors `section_registry.py`/`provider_registry.py`'s
  `ADR-014` shape one concept over): `list_skills`, `list_agent_skills`,
  `grant_skill_access`, `revoke_skill_access`, `has_skill_access`,
  `invoke_skill` — deliberately **no self-healing default assignment**,
  an agent gets skill access only via an explicit grant. New `app/api/
  skills_router.py` (`GET /skills`, `GET /agents/{id}/skills`, `POST`/
  `DELETE /agents/{id}/skills/{skill_id}`, `POST .../invoke`), registered
  in `app/main.py` additively. Verified live end-to-end against the real
  backend, all 5 locked ACs: `GET /skills` returns the registered
  catalog; granting an agent access is reflected in its own skills list;
  invoking for an ungranted agent returns a `403` refusal; invoking for a
  granted agent with no real handler yet returns an honest `200`
  "not yet available" body, distinct in both status and shape from the
  refusal; revoking access removes it and the refusal shape re-applies.
  This story is plumbing only — the first real skill's implementation and
  any UI are explicit follow-on work, per its own Non-Goals. Full
  reasoning: `Implementation/Architecture/ADR.md` → `ADR-015`.
- fix: `BUG-002` closed (`BUGFIX-02-US-01`, `SPRINT-016`) — "Agents Map:
  sections with 4+ agents visually spill into neighboring sections."
  Ported the already-approved, already-live-browser-verified Option D
  (semantic zoom / drill-down) design from `html-prototype/agents-map.html`/
  `agents-map.js` into the real React app. `src/frontend/src/features/
  agents-map/polarLayout.ts` gained `DRILLDOWN_AGENT_RADIUS = 40`;
  `layoutAgents.ts` gained a new sibling `layoutSectionDrilldown()`
  (full-360° evenly-spaced angle per agent), deliberately not a branch
  inside the existing `layoutAgents()`/`SECTION_ARC_SPAN_DEG` overview fan-
  out — both left unchanged. `AgentNode.tsx` gained optional `compact`
  (applies the already-shipped-but-unused `.agent-node--compact` CSS
  modifier — every overview agent now always renders as a small, unlabeled
  dot, hover/focus reveals its label, never a density threshold) and
  `radiusOverride` props. `SectionHub.tsx` gained optional `onActivate`
  (renders a real `<button>` at the overview call site; omitted at the
  drill-down's own call site, which stays the original non-interactive
  `<div>`) and `radiusOverride` (lets the drill-down's own Hub render at
  the canvas's literal center via `radius=0`) props. New
  `SectionDrilldown.tsx` renders one Section's own full-360°, fully-labeled
  "Agents Tree" — centered Hub, that Section's agents, Hub→agent cluster-
  lines only, the established `.empty-state` pattern for a 0-agent Section,
  and a "Back to Agents Map" control. `agents-map.css` gained the
  prototype's own `.explore-zoom-overview`/`.zooming-out`/
  `.explore-drilldown`/`.explore-drilldown .hub-node` rules plus
  `@keyframes fadeIn`, ported verbatim (class names unchanged).
  `AgentsMapCanvas.tsx` wires it all together: local `activeSectionId`/
  `zoomTargetSectionId` `useState` (not lifted), every overview `AgentNode`
  now renders `compact`, every `SectionHub` is a clickable button that
  plays the zoom-out CSS transition then mounts that Section's
  `SectionDrilldown` on `transitionend`; a `<>...</>` fragment return keeps
  `AgentsMapPage.tsx`'s existing call site source-compatible, zero edit
  needed there. Verified live end-to-end via headless-Chrome-over-CDP
  against the real running app (real seed data: "Productivity" Section, 4
  agents — the real assignment drifted from `BUG-002`'s original
  "Technical, 5 agents" filing, still today's real 4+-agents-in-one-Section
  repro condition): compact dots render with zero real visual (bounding-
  box) overlap against any neighboring Hub/agent/section-title; hover/
  focus reveals a label without moving the dot; Hub-click zooms into a
  fully-labeled drill-down with a correctly-smaller (8% vs 10% width) Hub
  node; Back restores the overview unchanged; the empty-Section drill-down
  and the overview agent-dot's existing click-to-detail-panel behavior are
  both unregressed. Full evidence: `Implementation/Tasks/BUGFIX-02-US-01-
  T06-agents-map-canvas-drilldown-wiring.md`'s Implementation Log.
- feat: `REQ-SB-25-US-01-T01` (`SPRINT-014`) — `src/backend/requirements.txt`
  gains `langgraph>=1,<2`, `langchain-openai`, `mcp`,
  `langchain-mcp-adapters` (`ADR-015`). Real `pip install` against the real
  `.venv` confirmed clean on this Windows/`cp314` host — resolved versions
  `langgraph==1.2.11`, `langchain-openai==1.4.3`, `mcp==1.29.0`,
  `langchain-mcp-adapters==0.3.2`; every transitive compiled dependency
  (`pydantic-core`, `cryptography`, `cffi`, `rpds-py`, `orjson`, `tiktoken`,
  and others) resolved a prebuilt wheel — `ADR-015`'s own honestly-flagged
  wheel-availability risk is now confirmed clear, not just hoped for.

- feat: `REQ-SB-25-US-01-T02` (`SPRINT-014`) — new `app/business/
  agent_orchestration/` package (first sub-package under `business/`,
  `ADR-015`), `state.py`: `AgentConversationState` TypedDict (the
  LangGraph conversation graph's state) and `history_entries_to_messages`
  (maps `agent_communication_history.json`'s existing entry shape into the
  graph's replayed LangChain message list — `"chat_user"`→`HumanMessage`,
  `"chat_agent"`→`AIMessage`, `"run_event"` excluded, one `SystemMessage`
  prepended from the agent's own name, per `architecture.md`'s 2026-08-12
  Addendum).

- feat: `REQ-SB-25-US-01-T03` (`SPRINT-014`) — new `agent_orchestration/
  model_factory.py`: `resolve_agent_model(agent_id)` resolves a per-agent
  `langchain_openai.ChatOpenAI` from `provider_registry`, returning an
  explicit `None` — never a constructed-then-broken model — before any
  model is built when the agent's Provider has no real client, mirroring
  `agents_router.py::_invoke_action`'s existing honest-unavailability
  funnel-gate one layer over for conversational replies (`ADR-015` point
  3, Scenario 4).

- feat: `REQ-SB-25-US-01-T04` (`SPRINT-014`) — new `app/business/
  vault_query_tools.py`: thin pass-through business-layer wrappers over
  already-existing read-only `vault_writer` primitives
  (`list_known_customers`/`list_known_kinds`/`list_known_partners`/
  `list_notes_in_kind_folder`, the last projecting `Path`→`str` for JSON
  serializability) — the tool *implementations* the new shared MCP server
  (`T05`) registers.

- feat: `REQ-SB-25-US-01-T05` (`SPRINT-014`) — new `app/api/mcp_server.py`:
  Second Brain's own shared MCP server (`ADR-015` points 7-11), an `mcp`
  SDK `FastMCP` instance registering `vault_query_tools.py`'s four
  functions as `@mcp.tool()`s, mounted at `/mcp` in `main.py`
  (`streamable_http_app()`, Streamable HTTP transport) alongside the six
  existing `include_router` calls. Two real, live-discovered corrections
  beyond a naive mount (see the task's own Implementation Log for full
  detail): `FastMCP(..., streamable_http_path="/")` avoids an unreachable
  `/mcp/mcp` double-mount nesting; `main.py`'s `lifespan` now explicitly
  composes `mcp_server.session_manager.run()` alongside the existing
  `capture_scheduler.lifespan` via `AsyncExitStack`, since a `Mount()`-ed
  sub-app's own lifespan is not invoked automatically by FastAPI/Starlette
  — without it, every real MCP request 500'd with "Task group is not
  initialized." Live-verified: `GET /mcp` now returns a correct `406 Not
  Acceptable` (protocol-level content-negotiation rejection of a bare GET,
  not a 404/500), and all six pre-existing REST endpoints are unaffected.

- feat: `REQ-SB-25-US-01-T06` (`SPRINT-014`) — new `agent_orchestration/
  mcp_client.py`: an async `load_vault_query_tools()` wrapping
  `langchain_mcp_adapters.client.MultiServerMCPClient`, pointed at Second
  Brain's own mounted `/mcp` endpoint over a real loopback HTTP call — the
  in-app agent is simply another MCP client, indistinguishable in
  principle from Hermes (`ADR-015` point 8); never re-wraps
  `vault_query_tools.py`'s functions directly. Live-verified: a real
  loopback round-trip returned all 4 of `T05`'s registered tools.

- feat: `REQ-SB-25-US-01-T07` (`SPRINT-014`) — new `agent_orchestration/
  graph.py`: a compiled `langgraph.graph.StateGraph` exposing
  `run_agent_conversation(agent_id, message, history) -> {"reply": str} |
  {"error": str}`, re-exported as `agent_orchestration`'s one public
  symbol (`__init__.py`). Two model-call/tool-execution nodes with one
  conditional edge (`call_model` ↔ `execute_tools`) — not literally the
  originally-sketched single node — since a real Compass/GPT-5 call
  genuinely chose to call a bound tool for an ordinary vault-query
  question, and the tool result has to actually be executed and fed back
  for a real, non-empty reply (found + fixed live, see the task's own
  Implementation Log); no LangGraph checkpointer, stateless per call
  (`ADR-015` point 6). Also fixed live in `agent_orchestration/
  model_factory.py` (`T03`): `ChatOpenAI`'s `base_url` needs
  `provider["endpoint"]` with its `/chat/completions` suffix stripped
  (the OpenAI SDK appends it itself) — `provider_registry`'s own stored
  shape is unchanged. Live-verified: a real vault-query question now
  returns a real, tool-backed Compass reply; a Provider with no real
  client short-circuits before the graph is ever invoked, returning the
  exact `_invoke_action`-matching unavailability message.

- feat: `REQ-SB-25-US-01-T08` (`SPRINT-014`, story `REQ-SB-25-US-01`
  complete) — `agents_router.py::chat`'s no-trigger-phrase-match branch
  now calls `agent_orchestration.run_agent_conversation(agent_id,
  body.message, history_before_this_message)` in place of the old static
  canned `fallback_reply`; the trigger-phrase-match branch and every
  other endpoint are byte-for-byte unchanged (`ADR-015` point 5). Agent
  chat is now genuinely conversational, Provider-backed, and
  vault-tool-aware for any message that isn't a recognized trigger
  phrase, with the existing keyword-match action fast path fully
  preserved. **All 5 locked ACs verified live** against the real backend/
  real Compass/real vault: a real, relevant, tool-backed reply for an
  ordinary question (`AC-01`); the fast path unchanged, no LLM call
  (`AC-02`); a second turn correctly recalling the first turn's own
  content (`AC-03`, after fixing a real round-count bug in `graph.py` —
  see `T08`'s own Implementation Log); honest unavailability for a
  no-real-client Provider, no silent fallback (`AC-04`); and an honest,
  real connection-failure message, recorded as a normal `chat_agent`
  history entry (`AC-05`, verified by temporarily repointing the real
  `"compass"` Provider's own endpoint at a dead port, then restoring it —
  a newly created Provider can never reach a real call at all under
  `provider_registry`'s own existing `"compass"`-only availability gate,
  see `MEMORY.md`). `REQ-SB-25-US-01` and `SPRINT-014` are `Done`.

- fix (partial, blocked): `REQ-SB-08-US-01-T06` (`SPRINT-017`) — replaces
  Outlook `EntryID` with a SHA-256 hash of `AppointmentItem.
  GlobalAppointmentID` as the Meeting-occurrence dedup/filename key, per
  `ADR-013`, with a legacy-`EntryID`-path coexistence fallback so none of
  the 39 already-captured real Meeting notes needed migrating or renaming.
  `app/data_access/outlook_com.py` gained `_resolve_global_appointment_id`
  (native COM property + `PropertyAccessor`/DASL fallback, never falls
  back to `EntryID`) and a `global_appointment_id` field on
  `list_calendar_events`'s per-event results; `app/data_access/
  vault_writer.py`'s meeting-note filename/dedup functions re-parametrized
  from `entry_id` to `global_appointment_id` (hashed, not sliced), plus a
  new `resolve_meeting_note_path` (new-scheme-then-legacy-path lookup,
  replacing the orchestrator's old two-call `meeting_note_path()`/
  `meeting_note_exists()` pattern); `app/business/meeting_classification.py`
  threads `global_appointment_id` through accordingly. **Live verification
  against the real Outlook calendar/vault found `ADR-013`'s own core
  premise — `GlobalAppointmentID` is unique per occurrence — is itself
  false on this Outlook installation**, for the exact real recurring
  series that originally motivated this fix (`ESC-002`): the native COM
  property returns an identical value across all 3 real occurrences of two
  separate recurring series, and its documented DASL fallback errors on
  every occurrence. The coexistence/no-duplicate mechanism and the hash-
  suffix logic are independently verified correct and non-regressive (39
  real notes, zero renamed/altered/duplicated), but the task's own
  regression check re-verifying distinct dedup keys for the trigger series
  fails. `REQ-SB-08-US-01-T06` is left `status: Blocked`, not `Done`;
  `SPRINT-017` stays `In Progress`. See `ESCALATIONS.md` → `ESC-012` (new)
  and `ESC-002`'s 2026-08-12 update; `REVIEW-QUEUE.md` carries the human
  decision point needed to resume.
- design: `BUG-002` fix ported into the canonical `html-prototype/
  agents-map.html` (Option D, semantic zoom / drill-down, plus both
  operator-approved refinements — operator approved the design 2026-08-12;
  see `REVIEW-QUEUE.md`'s "BUG-002 layout exploration" entry, updated in
  place, for the full history). Replaces the screen's old fixed-position-
  only rendering with the approved fix: every agent now always renders as a
  small, unlabeled `.agent-node--compact` dot at the overview level (hover/
  focus reveals its label); each Section's Hub is now a clickable button
  that zooms into that Section's own dedicated "Agents Tree" drill-down view
  (agents there spread across the full 360°, always fully labeled, with a
  "Back to Agents Map" button) — reusing `.explore-zoom-overview`/
  `.zooming-out`/`.explore-drilldown`/`.explore-drilldown .hub-node` verbatim
  from `agents-map-exploration.html`'s own additive `styles.css` section, no
  new CSS needed. A replayable overview entrance animation (flat row → hold
  → glide into real circular positions, Knowledge Base growing in at center)
  plays once on load and again on state-switch, via each state's own new
  "Replay intro" button. New page-scoped script `html-prototype/
  agents-map.js` (parallel to `app.js`) wires both. A new fourth state,
  "Dense section (BUG-002 fix demo)", was added to `agents-map.html`
  mirroring BUG-002's own literal original repro (all 5 real agents in one
  Section) — neither of the prior two agents-having states ever actually
  reached the bug's own 4-plus-agents-in-one-Section trigger condition, so
  this is the first state in the prototype to visibly exercise the fix.
  Hub coloring in the "Populated" state is now neutral (was per-Type), a
  called-out consequence of porting Option D's own approved rendering
  uniformly, resolving an earlier REQ-SB-18-pass debt item as a side effect.
  `html-prototype/agents-map-exploration.html` is untouched (kept as
  historical comparison, no longer the design-of-record for BUG-002 —
  `agents-map.html` is); `html-prototype/index.html`'s catalog card and
  `styles.css`'s BUG-002 CSS-section header comment updated to match. Always
  flagged (designer never auto-advances) — fresh `REVIEW-QUEUE.md` sign-off
  needed on this canonical port before `/triage` runs.
- design: Agents Map layout exploration (`BUG-002`) sign-off pass — the
  operator picked **Option D (semantic zoom / drill-down)** as the accepted
  direction (Options A/B/C stay as comparison history only); two refinements
  built directly inside the existing `html-prototype/agents-map-
  exploration.html`/`.js`: (1) rebalanced the drill-down "Agents Tree"
  Hub's size against the agent nodes it groups (`.explore-drilldown
  .hub-node` now 8% width vs the agent nodes' 10%, down from 11% before —
  confirmed at both today's scale and the stress dataset), scoped CSS only,
  no JS change; (2) a new, replayable overview entrance animation
  (`playIntro()`/`wireIntroDemo()`) — agents render first in a flat row,
  hold ~0.9s, then transition into their real circular positions while the
  Knowledge Base grows/fades in at center (new `@keyframes kbGrowIn`,
  `.agent-node--intro-move`, `.agents-intro-fade`), plain CSS
  transitions/keyframes only, no animation library. Page default tab and
  intro copy updated to reflect Option D as accepted; `html-prototype/
  index.html`'s catalog card updated to match. Still exploration-only — no
  story/task/sprint/requirement file touched, both refinements flagged for
  human browser sign-off before this becomes a real `BUGFIX-NN-US-01` fix
  story (`REVIEW-QUEUE.md`'s existing BUG-002 entry updated in place, not
  duplicated).
- design: Agents Map layout exploration for `BUG-002` (sections with 4+
  agents visually spill into neighboring sections, labels collide) — new
  `html-prototype/agents-map-exploration.html` + `agents-map-exploration.js`
  compare 4 genuinely different candidate fixes (dynamic angular budget;
  multi-ring wedge expansion; communication-affinity clustering grounded in
  REQ-SB-20's real keyword data; semantic zoom/drill-down, the operator's
  own suggested direction), each at today's real scale and a synthetic
  13-agent/6-section stress case, computed client-side from real
  `polarLayout.ts`-matching constants rather than hand-placed. Exploratory
  only — no direction picked, no story/task/sprint/requirement file touched.
  New additive CSS in `html-prototype/styles.css`: `.affinity-line`/
  `.affinity-line.active`, `.explore-zoom-overview`/`.zooming-out`/
  `.explore-drilldown`. `html-prototype/index.html` gained a clearly-marked
  catalog pointer to the new file (not added to the main sidebar nav, since
  it isn't a real application screen). Flagged to `REVIEW-QUEUE.md` for
  human sign-off on a direction before this becomes a real `BUGFIX-NN-US-01`
  fix story via `/triage`.
- docs: initial scaffold created
- feat: backend layered structure (`app/api`, `app/business`, `app/data_access`)
  with a `/health` endpoint, `.venv` on Python 3.14, and a passing pytest suite
- feat: frontend scaffolded via `create-vite` (React + TypeScript) under
  `src/frontend`
- chore: portable Node.js v24.19.0 LTS toolchain added at `tools/node/`
  (git-ignored) with a `tools/use-node.ps1` PATH helper, since no admin rights
  are available to install Node system-wide
- docs: `architecture.md` and `ADR.md` updated — Python 3.14 target
  (ADR-001), portable Node.js toolchain (ADR-002), layered backend
  architecture (ADR-003)
- docs: `Documentation/PRD.md` populated with real MVP/P1/P2 requirements
  (REQ-SB-01..06), replacing the placeholder — seeded by classifying all 76
  entries in agentic-map's `REQUIREMENTS.md` against Second Brain's actual
  scope; full reasoning in
  `Implementation/Plans/2026-08-10-agentic-map-requirement-port.md`;
  `BACKLOG.md` indexed accordingly
- feat: email-classification POC (`POST /poc/classify-emails`) — fetches
  recent mail via a ported `outlook_com` COM-automation data access
  (`app/data_access/outlook_com.py`, from agentic-map's ADR-0018 precedent),
  classifies each by customer via a Compass API client
  (`app/data_access/compass_client.py`), and files the result as a note under
  `Customers/<Customer>/Emails/` in the vault (`app/data_access/
  vault_writer.py`), orchestrated by `app/business/email_classification.py`.
  Verified live against a real inbox (3 emails, correctly split across two
  known customers and one low-confidence `Unsorted` bucket)
- chore: `src/backend/.env`/`.env.example` added (Compass credentials, vault
  path) — `.env` git-ignored, never committed
- feat: extensible item-kind classification — Compass now returns a `kind`
  (e.g. `Emails`, `Files`, `Notifications`) alongside `customer`, read
  dynamically from existing vault subfolders (`vault_writer.list_known_kinds`)
  the same way customers are; new kinds need no code change. Real meeting
  invites are excluded before ever reaching Compass, via Outlook's
  `MessageClass` (`IPM.Schedule.Meeting.*`)
- feat: attachment extraction — email/file-share attachments are saved into
  `attachments/<note>/` next to their note and linked from the note body
  (ported from agentic-map's save-to-temp/read/delete technique, 20MB cap,
  oversized files recorded but not written)
- fix: filenames now include a slice of the Outlook EntryID — two same-
  subject, same-day items (e.g. a duplicate share notification) were
  colliding on `date-subject.md` and the second silently overwrote the
  first; found live (`ADNOC_Azure_MACC_Review` shared twice 2026-08-07),
  fixed, and the lost note was recovered by re-fetching both EntryIDs
  directly from Outlook and reprocessing
- feat: thread linking — notes from the same Outlook conversation
  (`ConversationID`) now get a `## Related Emails` section with wikilinks to
  prior notes in the same thread (`vault_writer.find_related_note_stems` /
  `record_conversation_note`, backed by `.second-brain/conversation_index.json`);
  Obsidian computes the reverse links automatically
- fix: inline signature/body images (e.g. a logo pasted into a signature)
  were being extracted as real attachments — Outlook has no reliable COM
  flag for this (agentic-map's own outlook_com.py docstring notes the same
  limitation and deliberately keeps them for its signature-mining use case);
  Second Brain's use case doesn't need that noise, so `_is_inline_attachment`
  filters on `PR_ATTACH_CONTENT_ID` plus an `imageNNN.ext` filename fallback
- feat: hierarchical Obsidian tags (`customer/<slug>`, `kind/<slug>`) added
  to every note's frontmatter (`vault_writer.build_tags`), so notes stay
  findable by customer/kind independent of which folder they physically sit
  in — surfaces in Obsidian's tag pane/search even before a note is
  physically moved
- chore: `POST /poc/backfill-tags` — one-off, idempotent migration that
  added `tags` to all 35 pre-existing notes via a surgical line-insert
  (`vault_writer.insert_tags_line`), not a full frontmatter rewrite, so
  every other field's exact formatting (e.g. unquoted numbers) was left
  untouched
- docs: `Documentation/References/beyond-the-second-brain-methodology.md`
  added — condensed reference summary of *Beyond the Second Brain* (Mo
  Elkholy), supplied by the operator as a standing architecture reference.
  Flags real tensions with the email-classification POC (folder-heavy
  structure vs. link-based structure, no AI-output review gate vs. the
  book's AI Staging principle, non-atomic notes) for operator decision
- refactor: flattened `Work/Customers/<Customer>/<Kind>/` to `Work/<Kind>/`
  — customer is no longer a folder level, only frontmatter + a
  `customer/<slug>` tag, per the book's "folders are the enemy of
  thinking" principle (`vault_writer.list_known_customers` now reads
  frontmatter instead of scanning folder names; `POST /poc/
  flatten-customer-folders` migrated all 35 existing notes + their
  attachments with zero collisions). This also resolves the earlier
  Unsorted→Affiliate reorg question — reclassifying a note's customer is
  now a tag edit, not a file move
- fix: inline signature/logo images that didn't match the `imageNNN.ext`
  pattern (a recurring `thumbnail_emailsignature_new-02_*.jpg`) were still
  being saved as real attachments — `_is_inline_attachment` now also
  matches filenames containing signature/thumbnail/logo keywords.
  Retroactively swept 13 signature-file instances and 52 pre-fix
  `imageNNN.ext` files (captured before the original inline-image filter
  existed) from already-written notes, including their link lines and any
  now-empty attachment folders
- docs: formalized the book's principles across the three-way knowledge
  split — `ADR-004` (customer-as-tag decision, in `Implementation/
  Architecture/ADR.md`), `architecture.md`'s `## Data Model` (the vault's
  actual current structure + explicitly what's not yet adopted), and a
  provisional (non-sprint-retro) entry in `Implementation/Learnings.md`,
  clearly marked as deviating from that file's normal retro-only protocol
  at the operator's explicit request
- docs: `Documentation/PRD.md`/`BACKLOG.md` — five new P1 requirements
  (REQ-SB-07..11): Scheduled Recurring Agent Capture, Meetings Capture
  Pipeline, To-Do Task Capture Pipeline, People Living Documents, Agent
  Activity & Error Observability. Hermes's own agent-type/section taxonomy
  and multi-LLM-provider plan recorded as context in `MEMORY.md`, not new
  Second Brain requirements — Hermes stays a dependency this project
  doesn't build, per the existing constraint
- feat: last-successful-capture-run persistence
  (`REQ-SB-07-US-01-T01`) — `vault_writer.record_capture_run_completed`/
  `load_last_capture_run` add a `.second-brain/last_capture_run.json`
  convention (`{"finished_at": "<ISO-8601 UTC>"}`), mirroring the existing
  `processed_email_ids.json`/`conversation_index.json` state-file pattern;
  `load_last_capture_run` returns `None` until the first run completes.
  Not yet called from anywhere — this is the persistence primitive T02–T04
  build the scheduler on top of
- feat: `run_capture_and_record_completion` (`REQ-SB-07-US-01-T02`) —
  thin orchestration entry point in `app/business/email_classification.py`
  that calls the existing `classify_recent_emails` unchanged, then records
  completion via `vault_writer.record_capture_run_completed()`
  unconditionally, even when no new emails were found; the single call the
  future `app/scheduling/` layer (T03/T04) makes per capture run. The
  manual `POST /poc/classify-emails` endpoint keeps calling
  `classify_recent_emails` directly and is untouched. Verified live against
  a real Outlook/Compass/vault session
- docs: `Documentation/PRD.md`/`BACKLOG.md` — two new P1 requirements
  (REQ-SB-12, REQ-SB-13) capturing the operator's UI vision: a burger-menu
  app shell with an "Agents Map" default page (Knowledge Base at the center,
  agents arranged around it, color-coded by type) and a "My Day" dashboard
  (REQ-SB-12), plus an embedded in-app agent chat and communication-history
  panel (REQ-SB-13) — written so `/design` has requirement IDs to scope
  against, per `.claude/agents/designer.md`'s "bare invocation not
  supported" rule
- feat: new `app/scheduling/` package (`REQ-SB-07-US-01-T03`, ADR-005 point
  5) — `capture_scheduler.run_capture_if_idle()` wraps
  `email_classification.run_capture_and_record_completion` in a module-level
  `asyncio.Lock` non-blocking concurrency guard, so a trigger arriving while
  a capture run is already in progress skips immediately (logged) rather
  than queuing or overlapping. `app/scheduling/` imports only from
  `app/business/`, never `app/data_access/` directly. Not yet wired to any
  trigger source (app-start / hourly interval — T04's scope). Verified live:
  a second, overlapping call returned in under 1ms while the first call's
  real Outlook/Compass/vault run (~20s) completed uninterrupted, and
  `.second-brain/last_capture_run.json` recorded exactly one completion, not
  two
- design: first `html-prototype/` screens (`/design` against REQ-SB-12,
  REQ-SB-13) — `agents-map.html` (default/home page: Knowledge Base node at
  the center, agent nodes arranged and color-coded by type
  Worker/Producer/Expert via new `--agent-color-<type>` tokens, so a future
  type is a new color, never a layout change), `my-day.html` plus its four
  drill-down pages (`my-day-emails.html`, `my-day-calendar.html`,
  `my-day-todo.html`, `my-day-reads.html`), and `settings.html`. Clicking an
  agent node opens a right-side `.side-panel` overlay (REQ-SB-13, not a page
  nav) with that agent's settings, available actions, an embedded
  `.chat-thread` demo chat, and a `.log-list` communication history — one
  panel per agent, grounded in existing requirements (REQ-SB-03/07/08/09/10).
  New reusable `styles.css` patterns: the collapsible burger sidebar
  (`.sidebar-header`/`.burger-btn`/`.app-shell.sidebar-collapsed`), the
  `.state-switcher` buildable-state demo control (used on every new screen to
  show empty/populated/error states in one file), `.item-list`/`.item-row`
  (shared by all four My Day drill-downs), and CSS-only motion (KB pulse
  glow, staggered agent-node fade-in, node hover-scale, sidebar collapse
  transition, sliding side panel). New shared `html-prototype/app.js` for the
  sidebar toggle, state switcher, and agent-panel/chat-demo interactions
  (no framework, no backend calls). `index.html` updated from the "no
  screens yet" placeholder to a catalog of the new screens. Flagged to
  `REVIEW-QUEUE.md` for mandatory human browser sign-off before `/spec`
  reconciles stories against it — never marked "clear," per
  `.claude/agents/designer.md`
- feat: APScheduler wired into FastAPI's `lifespan`
  (`REQ-SB-07-US-01-T04`, ADR-005 points 1–2) — completes REQ-SB-07 end to
  end. `capture_scheduler.build_scheduler()` registers one `AsyncIOScheduler`
  job (`IntervalTrigger(hours=1)`, `coalesce=True`, `misfire_grace_time=None`,
  `max_instances=1`) against `run_capture_if_idle`; `capture_scheduler.
  lifespan(app)` starts the scheduler, fires one unconditional
  `run_capture_if_idle()` call on every app start/restart regardless of how
  recently the previous run finished, then shuts the scheduler down cleanly
  on exit. `app/main.py` passes `lifespan=lifespan` into the `FastAPI(...)`
  constructor. `requirements.txt` gains `apscheduler>=3.10`. Verified live:
  job registration matched ADR-005 verbatim; two consecutive server
  starts/restarts each fired an immediate capture run
  (`.second-brain/last_capture_run.json`'s `finished_at` updated both times,
  the second within ~90s of the first, proving the app-start trigger is
  unconditional). This closes `REQ-SB-07-US-01` — all five ACs now
  exercised end-to-end by a running process
- chore: **SPRINT-001 Done** (2026-08-10) — first sprint completed in this
  project, first `/spec → /plan-tasks → /plan-sprints → /implement-sprint`
  pipeline run end to end. REQ-SB-07 closed. Sizing estimate (~4 tasks, S)
  matched actual exactly. Retrospective drafted in the sprint file, flagged
  for human harvest into `Implementation/Learnings.md` (see `REVIEW-QUEUE.md`)
- design: `html-prototype/` revision pass (round 2, still pre-approval) on the
  REQ-SB-12/REQ-SB-13 screens, after operator browser review of round 1.
  Two changes: (1) **light theme, green accent** — `styles.css` `:root` color
  tokens swapped from dark/blue-accent to white/near-white surfaces with a
  green `--color-accent` (`#15803d`); `--color-success/-warning/-danger`
  darkened for legibility on white (the dark-theme pastel values would fail
  contrast against it); new `--color-on-accent` token replaces the two
  places that hardcoded `#0f1115` as text-on-accent-background
  (`.btn-primary`, `.chat-message--user`); `.nav-item.active` now uses the
  accent explicitly (green text/wash) instead of a neutral highlight; added
  a generic `:focus-visible` outline. Cascades to every screen from this one
  token-level edit — no screen had a hardcoded color, so no per-screen
  markup changed. Agent-type colors (`--agent-color-worker/producer/expert`)
  were deliberately moved off the green family (now blue/violet/pink) so
  they stay visually distinct from the new brand accent. (2) **Agents Map
  rebuilt as a wheel** — replaced the single ring of individually
  KB-spoked agent nodes with a pie-wedge wheel: 3 sections grouped from the
  same 5 agents established in round 1 (Capture/Worker: Email+Meeting+To-Do
  Capture; People/Producer: People Notes; Q&A/Expert: Vault Q&A), each with
  a new dashed, non-clickable `.hub-node` at the wheel's rim that is the
  only thing connecting inward to the KB (topology: KB → Hub →
  agents-in-section; agents within a section connect to each other, not
  each individually back to the KB). The Knowledge Base itself is now a
  small neuron-mesh "brain" (`.kb-brain-svg`/`.kb-neuron` — SVG circles +
  connecting lines with a staggered pulse) instead of a plain labeled
  circle. `.agents-map-canvas` is now forced square via `aspect-ratio` so
  the wheel renders as a true circle instead of the ellipse the earlier
  non-square box stretched it into. REQ-SB-13's per-agent click → side-panel
  behavior (settings/actions/embedded chat/communication history) is
  unchanged — only the map's visual structure and the color theme moved
  this round. Every changed screen's breadcrumb comment updated to record
  this revision; `REVIEW-QUEUE.md`'s existing (still-open) entry amended in
  place to describe what's now on disk, rather than left stale. Still
  flagged for mandatory human browser sign-off before `/spec` — never
  marked "clear"
- docs: Customer structured-data schema resolved
  (`Implementation/Plans/2026-08-10-vault-taxonomy-draft.md`) — Customer hub
  notes, atomic Pipeline/Agreement notes, and one-note-per-snapshot Azure
  Consumption tracking, all following `ADR-004`'s kind-folder/customer-tag
  pattern. Reverses the earlier port-classification "Drop" on agentic-map's
  REQ-079/080/081 now that real captured data confirms the same Azure
  MACC/consumption domain (see `MEMORY.md`). Structure only — no
  ingestion/agent code yet
- design: `html-prototype/agents-map.html` revision pass (round 3, still
  pre-approval), after operator browser review of round 2 found the
  wedge/hub structure wrong (read as one Hub per section near the KB —
  backwards). Rebuilt as a true polar/radial grid, implemented close to the
  operator's exact spec: **angular axis = sections** (same 3 as round 2:
  Capture/People/Q&A) — now purely a virtual boundary, a faint dashed
  `.section-boundary` guide line at each edge, round 2's filled
  `.wedge-fill` removed entirely; **radial axis = 3 concentric rings,
  global across every section, one per agent type** (`.ring-circle` at a
  fixed radius each) — Worker outermost, Expert middle, Producer innermost
  (closest to the KB) — every section's angular span is cut through by all
  3 rings, rings are not per-section. Each `.hub-node` now sits at the
  wheel's outer rim (the `.boundary-circle`'s radius), not near the KB —
  exactly one `.spoke-line` per Hub runs inward to the KB (the section's
  single KB-facing connector); agents (placed at their type's ring, within
  their section's angular span) connect to each other and to their Hub via
  `.cluster-line`, never individually to the KB. Added a 12-line faint
  `.radar-spoke` background grid (renders even in the first-run/empty
  state — ambient chrome, not a configured entity) plus `.ring-label`s
  (Producer/Expert/Worker) and `.section-title`s (Capture/People/Knowledge
  Q&A — HTML labels outside the outer boundary at each section's angular
  midpoint, larger/letter-spaced typography with a type-colored accent
  bar). Knowledge Base rebuilt denser: 14 neurons (was 8, varied
  size/opacity for depth), ~26 crossing synapse lines (was a simple
  ring+spokes), two traveling pulse dots via SVG `animateMotion` along
  synapse paths, plus a static soft outer glow (CSS `drop-shadow`) layered
  under the existing pulsing halo. General visual-polish pass: bigger
  canvas via a new padded `.agents-map-stage` wrapper (reserves room for
  the outside labels so nothing clips), soft ambient shadow under the whole
  wheel, per-node glow/shadow keyed to agent-type color, hover now lifts
  (translateY, not just scale). Documented — not instantiated, still only
  ~5 real agents — a scale-to-~100-agents pattern in both the file's
  breadcrumb and `styles.css`: `.agent-node--compact` (unlabeled dot,
  label/type revealed on hover/focus only) and `.map-overflow-marker`
  ("+N") for an overcrowded ring/section arc segment, both defined and
  ready to apply. REQ-SB-13's per-agent click → side-panel behavior
  (settings/actions/embedded chat/communication history) is byte-for-byte
  unchanged — only the map's own structure/visuals were in scope this
  round; the round-2 light/green theme is unchanged. `REVIEW-QUEUE.md`'s
  existing (still-open) entry amended in place again to describe what's
  now on disk. Still flagged for mandatory human browser sign-off before
  `/spec` — never marked "clear"
- fix: `html-prototype/agents-map.html` container-sizing bug (round 4, still
  pre-approval) — a targeted bug fix, not a redesign; round 3's polar-grid
  math (ring-by-type radial axis, virtual section boundaries, hub-at-rim
  trigonometry, the brain, the radar background, section titles) was
  untouched and confirmed correct. Root cause, confirmed by the operator via
  `getBoundingClientRect()` measurement rather than visual inspection:
  `.agents-map-stage`'s `padding: 130px 110px` (`box-sizing: border-box`)
  consumed a fixed 220px of horizontal width regardless of the container's
  actual size — on a realistic (non-ultrawide) window this collapsed
  `.agents-map-canvas`'s content-box width to double digits (a measured
  274px stage produced a 54px canvas), so the entire wheel — KB, all 3
  hubs, all 5 agents — rendered inside a ~54x54px circle. That crowding,
  not a positioning-math error, is what read as "hubs next to the KB."
  Fixed in `styles.css` by decoupling canvas size from stage padding:
  `.agents-map-stage` now reserves only a small fixed `24px` margin;
  `.agents-map-canvas` caps its own width explicitly (`width: min(100%,
  700px)`, centered) instead of inheriting 100% of a padding-starved stage.
  The outside section-title/hub labels don't need reserved padding to stay
  visible — they already position via percentages beyond the 0-100% range
  against `.agents-map-canvas`, which already has `overflow: visible`; they
  just need nothing clipping them, which the small margin provides.
  Hand-verified (no browser available) for stage widths ~500px/~700px/
  ~1000px: canvas content-box comes out to ~452px/~652px/~700px(capped) —
  comfortably several-hundred-px at every width checked, never collapsing.
  Breadcrumb in `agents-map.html` updated to record this as a sizing fix;
  `REVIEW-QUEUE.md`'s existing (still-open) entry amended in place again.
  Still flagged for mandatory human browser sign-off before `/spec` —
  never marked "clear"
- design: `html-prototype/agents-map.html` Hub reposition (round 5, still
  pre-approval) — a genuine direction change, not another sizing fix; the
  round-4 canvas-sizing fix was independently re-verified by the operator
  (226px measured in a narrow test viewport, up from the broken 54px) and
  is untouched. Moved every `.hub-node` from round 3's outer-rim placement
  (r=54, the wheel's edge) to the inner band (r=19 — just outside the
  Producer ring, r=18, leaving clearance from the KB's own ~r=11 edge),
  computed with the same angle×radius trigonometry round 3 used: Capture
  Hub stays at its section's true midpoint (-30°) — its own Worker-ring
  agent sits 23 units further out, no collision; Q&A Hub stays at its
  section's true midpoint (210°) — 11-unit clearance to its own
  Expert-ring agent at r=30; People Hub is deliberately offset to 45°
  (off its section's 90° midpoint) because People Notes, a real
  Producer-type agent, already occupies that exact ring/angle — offsetting
  the Hub's angle (not overlapping it) was explicit in the requested fix.
  All three re-checked for KB clearance (~2.5-3.5 units) and hub-to-hub
  separation (>20 units, no risk). Recomputed every `.spoke-line` (Hub ->
  KB, now short, matching the near-center Hub positions) and every
  `.cluster-line` (Hub -> its section's agents, from the new Hub
  coordinates — the Capture section's now reach *outward* to the Worker
  ring at r=42 instead of round 3's short outward reach).
  `.section-boundary` guide lines and `.section-title` labels are
  untouched (never tied to Hub radius). Legend/intro copy updated from "at
  the rim" to "on the inner ring, close to the KB." REQ-SB-13's per-agent
  click -> side-panel behavior is unchanged; the round 2 light/green theme
  and the round 4 canvas-sizing fix are both unchanged. Breadcrumbs in
  both `agents-map.html` and `styles.css` updated to record this as a Hub
  reposition, explicitly distinct from the round 4 sizing bug fix;
  `REVIEW-QUEUE.md`'s existing (still-open) entry amended in place again.
  Still flagged for mandatory human browser sign-off before `/spec` —
  never marked "clear"
- design: `html-prototype/agents-map.html` KB growth + full radial-scale
  rebalance (round 6, still pre-approval) — a scale/spacing rebalance, not
  another direction change; round 5's inner-ring Hub placement is
  preserved, it now just has real breathing room, and the round-4
  canvas-sizing fix is untouched (independently re-verified by the
  operator, 226px measured, before this round started). Root cause
  confirmed by the operator via direct `getBoundingClientRect()`
  measurement: the KB was correctly centered and exactly 22% wide as
  coded (no centering bug) — the real problem was that round 5's Hubs at
  r=19 sat only ~2.5%-of-canvas-radius from the KB's edge (~5.6px measured
  on a 226px canvas), three 11%-wide Hub nodes crowding a KB too small
  (22%) to read as dominant. Fixed as one coordinated rebalance: (1) grew
  `.kb-node` from 22% to 34% of canvas width (`styles.css`) and rebuilt the
  brain substantially denser in `agents-map.html` — 23 neurons (16 outer +
  6 mid + 1 center), up from 14, ~42 crossing synapse lines (up from ~26),
  varied neuron size/opacity across 3 depth layers, a stronger glow
  (`.kb-node`'s `drop-shadow` blur 16px→26px, `kbPulse`'s peak spread
  28px→42px); (2) recomputed the entire radial scale outward — by the same
  angle×radius trigonometry every prior round used, not eyeballed — so
  nothing collides now the KB is bigger: Hub band r=19→32 (edge-to-edge
  KB-Hub gap is now ~9.5 units, ~19% of the canvas radius, the explicit
  "comfortable double-digit percentage" target), Producer ring r=18→30,
  Expert ring r=30→45, Worker ring r=42→50, boundary r=54→58; every
  dependent coordinate recomputed from the new radii — all 3 `.hub-node`
  positions, all 5 `.agent-node` positions, every `.spoke-line`, every
  `.cluster-line`, the `.ring-label`/`.section-title` positions — none left
  pointing at stale round-5 coordinates. Hand-verified (no browser
  available): KB-edge-to-Hub-edge ~9.5 units (19%); KB-edge-to-
  Producer-ring-agent-edge ~8 units (16%); both same-angle Hub-vs-its-
  section's-own-agent pairs (Capture, Q&A) re-checked with positive
  clearance beyond the 10.5-unit combined-radii minimum (7.5 and 2.5 units
  respectively). `.section-boundary` guide lines and `.section-title`
  labels moved only incidentally with the slightly larger boundary —
  never tied to Hub or KB radius directly. REQ-SB-13's per-agent click ->
  side-panel behavior is unchanged; the round 2 light/green theme is
  unchanged. Breadcrumbs in both `agents-map.html` and `styles.css`
  updated to record this as a scale/spacing rebalance;
  `REVIEW-QUEUE.md`'s existing (still-open) entry amended in place again.
  Still flagged for mandatory human browser sign-off before `/spec` —
  never marked "clear"
- feat: hub-note file-I/O primitives added to `vault_writer.py`
  (`REQ-SB-14-US-01-T01`) — `hub_note_path`/`hub_note_exists` resolve/check
  `Work/Customers/<Customer>.md` (same `_slugify()` `write_note()` uses
  internally, so the two always agree on the file); `create_customer_hub_note_baseline`
  writes a new hub note's baseline frontmatter (`type`, `customer`, `tags`,
  `affiliate_of`) plus a short auto-generated body stub, via the existing
  `write_note`; `insert_frontmatter_key_if_missing` generalizes
  `insert_tags_line`'s surgical-insert precedent from a single hardcoded
  `tags` key to any key/value pair; `ensure_hub_note_baseline_frontmatter`
  tops up only the baseline keys an existing hub note is missing (never
  resets a real `affiliate_of`, never touches the body); `insert_body_line_if_missing`
  generalizes the same surgical-insert idea to the note body, idempotently
  inserting a line (e.g. the inline `**Customer:** [[Hub]]` wikilink) only
  if not already present. Purely additive — no existing function's behavior
  changed. Verified live against the real `.venv` and real configured vault:
  AC-01 (baseline creation + path/exists resolution) passed, plus two non-AC
  smoke checks (baseline top-up preserving existing keys/body, idempotent
  body-line insert); all throwaway test notes deleted afterward. This is the
  file-I/O layer `app/business/customer_hub_linking.py` (T02) will
  orchestrate on top of — no business logic (which customer, which note)
  lives here
- feat: new `app/business/customer_hub_linking.py` orchestration module
  (`REQ-SB-14-US-01-T02`) — `ensure_customer_hub_note` creates a
  customer's hub note baseline if missing or tops up only missing
  baseline frontmatter keys if it already exists; `link_note_to_customer_hub`
  idempotently inserts the inline `**Customer:** [[Hub]]` wikilink into a
  note's body; `ensure_hub_note_and_link` is the single shared operation
  (skips the `Unsorted` placeholder pseudo-customer and blank customers)
  that both the one-time retrofit and the future per-write capture hook
  call; `retrofit_customer_hub_links` iterates every vault note, skips
  notes with no real `customer:` frontmatter, and never links a hub note
  to itself. Built entirely on T01's `vault_writer` primitives — no direct
  filesystem I/O in this module (ADR-003 layering), mirroring
  `tag_backfill.py`/`vault_restructure.py`'s one-module-per-maintenance-
  operation shape. Non-AC smoke check run live against the real `.venv`
  and real configured vault (this story's locked ACs are exercised by
  T03/T04, which build on this module): created a throwaway note under
  `Work/Emails/` with `customer: 'Verify-T02-Customer'`, called
  `ensure_hub_note_and_link` — first call returned
  `hub_created: True, linked: True` and created
  `Work/Customers/Verify-T02-Customer.md`; second call with identical
  arguments returned `hub_created: False, linked: False` (idempotent);
  a call with `customer="Unsorted"` returned `skipped: True`. Throwaway
  note and hub note deleted afterward, leaving the real vault unchanged
- feat: wired the per-write customer hub-linking hook into
  `app/business/email_classification.py` (`REQ-SB-14-US-01-T03`) — after a
  captured note is written and marked processed,
  `classify_recent_emails` now calls
  `customer_hub_linking.ensure_hub_note_and_link(note_path, customer)`
  before returning, so every newly captured note is written with its
  customer's `[[wikilink]]` already in place and the customer's hub note
  is created automatically if missing — no separate manual linking step.
  Two-line addition only (one import, one call); `run_capture_and_record_completion`,
  the manual endpoint, and the function's return shape are all unchanged.
  Verified live (AC-03) against the real Outlook desktop client and the
  real configured vault: `Work/Customers/` did not exist beforehand
  (confirming no hub note pre-existed for any customer); probed
  increasing `limit` values on `classify_recent_emails` until reaching a
  genuinely unprocessed email (`limit=10` reached one: "Re: Workshop
  slides"); the real call classified it as customer `Masdar`, created
  `Work/Customers/Masdar.md` matching the Scenario-1 schema, and the
  written note's body already began with `**Customer:** [[Masdar]]`
  immediately after the call returned, with no separate edit
- feat: new `POST /poc/retrofit-customer-hub-links` endpoint
  (`REQ-SB-14-US-01-T04`) — thin wrapper around T02's
  `retrofit_customer_hub_links`, matching the existing `/poc/backfill-tags`/
  `/poc/flatten-customer-folders` one-off-migration-endpoint shape exactly;
  tallies `linked`/`hub_notes_created` counts from the results list. This
  closes `REQ-SB-14-US-01` — all five ACs now verified (AC-03 live in T03;
  AC-01/AC-02/AC-04/AC-05 verified live here). Verified live against the
  real configured vault: first call against customer `TAQA` (multiple
  existing customer-tagged notes, no hub note yet) created
  `Work/Customers/TAQA.md` matching the Scenario-1 schema and added
  `**Customer:** [[TAQA]]` to a pre-existing, previously-unlinked TAQA note
  (AC-01, AC-02); a manually-added `## My Notes` line was then appended to
  the hub note simulating user content, and a second call left it and the
  hub note's baseline frontmatter unchanged (AC-04), created no duplicate
  hub note (AC-01 idempotency half), and left the previously-linked note
  byte-for-byte unchanged, confirmed via matching SHA-256 hashes before/
  after (AC-05)
- chore: **SPRINT-002 Done** (2026-08-11) — REQ-SB-14 closed. Sizing
  estimate (~4 tasks, S) matched actual exactly, second sprint in a row.
  Retrospective drafted, flagged for human harvest into
  `Implementation/Learnings.md` (see `REVIEW-QUEUE.md`)
- docs: authored the four Obsidian core-Templates note-type templates
  (`REQ-SB-15-US-01-T01`) — `Templates/Customer.md`,
  `Templates/Opportunity.md`, `Templates/Agreement.md`,
  `Templates/Consumption-Snapshot.md`, written vault-relative at
  `VAULT_PATH` (per ADR-006's new third top-level vault root, sibling to
  `Personal/`/`Work/`) as pure vault-content authoring — no
  `src/backend`/`src/frontend` change. Each matches
  `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md`'s resolved
  schema field-for-field; Customer is structurally parallel to
  `REQ-SB-14-US-01-T01`'s `create_customer_hub_note_baseline` output; the
  other three carry the inline `**Customer:** [[REPLACE_WITH_CUSTOMER_NAME]]`
  wikilink line established by `REQ-SB-14-US-01`. Verified by reading all
  four files back from the real vault and YAML-parsing each frontmatter
  block in isolation (all 5 tagged ACs — AC-01 through AC-04, AC-06 —
  passed)
- docs: authored the in-vault Manual Entry Guide note
  (`REQ-SB-15-US-01-T02`) — `Work/Guides/Manual-Entry-Guide.md`, written
  vault-relative at `VAULT_PATH` (deliberately outside `Templates/` per
  ADR-006, so it never appears in Obsidian's "Insert Template" picker).
  Explains all four manual-entry note types (Customer, Opportunity,
  Agreement, Consumption-Snapshot) — what each is for, its target folder,
  and its matching template — plus a shared "How to insert a template"
  walkthrough; folder/template names cross-checked against T01's actual
  written files, no drift. This closes `REQ-SB-15-US-01` — all six ACs now
  verified (AC-01 through AC-04, AC-06 in T01; AC-05 here). Verified by
  reading the file back from the real vault
- chore: **SPRINT-003 Done** (2026-08-11) — REQ-SB-15 closed. Sizing
  estimate (~2 tasks, XS) matched actual exactly, third sprint in a row.
  Retrospective drafted, flagged for human harvest into
  `Implementation/Learnings.md` (see `REVIEW-QUEUE.md`)
- refactor: `vault_writer._tag_slug` promoted to public `tag_slug`
  (`REQ-SB-10-US-01-T01`) — pure rename, no behavior change; `build_tags`'s
  two internal call sites updated. Frees the normalization function for
  reuse by `app/business/people_extraction.py` (T02) without duplicating
  slug logic outside `data_access`
- feat: five new Person-note file-I/O primitives added to `vault_writer.py`
  (`REQ-SB-10-US-01-T01`) — `person_note_path`/`person_note_exists` (dedup
  key: sender email, lowercased before slugifying), `build_person_tags`
  (separate `company/<slug>` tag namespace, `kind/person` always present),
  `create_person_note_baseline` (first-write baseline: type/name/email/
  phone/linkedin/tags + empty body), `ensure_person_note_baseline_frontmatter`
  (surgical top-up of missing baseline keys only, never resets a
  user-filled value, never touches the body) — mirrors the
  `REQ-SB-14-US-01` hub-note primitives for the People schema. Additive
  only; no other existing function's behavior changed. Verified via three
  non-AC smoke checks against the real backend `.venv` and real configured
  vault (this task's own locked-AC verification runs later, live, in
  T02/T03/T04): `tag_slug`/`build_tags` behavior-preserved after rename;
  `create_person_note_baseline` created a throwaway Person note with
  correct frontmatter/dedup-by-lowercased-email behavior;
  `ensure_person_note_baseline_frontmatter` topped up a removed `linkedin`
  key exactly once and was a true no-op on a second run. Throwaway test
  note and the `Work/People/` directory it created were deleted afterward,
  restoring the vault to its exact pre-task state
- feat: new `app/business/people_extraction.py` orchestration module
  (`REQ-SB-10-US-01-T02`) — `derive_company_from_email` (email-domain ->
  display-name company, `None` for a fixed set of personal/free email
  providers or a blank/malformed address), `find_matching_customer`
  (company vs. `list_known_customers()` by `tag_slug` equality, not exact
  string match), `ensure_person_note` (the shared create-or-top-up
  operation: baseline note on first sight, surgical baseline top-up on
  repeat, company tag always when derivable, hub-note link only after a
  confirmed customer match — calling `customer_hub_linking`'s two
  granular primitives directly, never `ensure_hub_note_and_link`),
  `ensure_person_note_for_captured_email` (per-write hook wrapper, skips
  cleanly on a blank `sender_email`), and `retrofit_people_from_emails`
  (one-time batch over every captured Email note, deduped by lowercased
  `sender_email`, skips notes with none). First business module that
  composes another business module (`customer_hub_linking.py`) rather
  than only `data_access` — an intentional, ADR-003-permitted shape
  recorded in `architecture.md`. This task's own functions carry no
  locked story AC directly (this story's 9 locked ACs are exercised
  live by T03/T04); verified via three non-AC smoke checks against the
  real backend `.venv` and real configured vault:
  `derive_company_from_email` correctly resolved `"core42.ai"` ->
  `"Core42"`, a personal Gmail domain -> `None`, and a blank address ->
  `None`; `find_matching_customer("Adnoc")` matched the real vault's
  `"ADNOC"` known customer despite mixed casing, and a made-up company
  name matched nothing; `ensure_person_note` created a throwaway Person
  note (`created: True`, correct company/no-match/no-link outcome) and a
  second identical call was a true no-op (`created: False`, no duplicate).
  Throwaway test note deleted afterward, restoring the vault to its
  exact pre-task state
- feat: going-forward per-write Person-note hook wired into
  `email_classification.py` (`REQ-SB-10-US-01-T03`) — immediately after the
  existing `customer_hub_linking.ensure_hub_note_and_link(note_path,
  customer)` call in `classify_recent_emails`, one additional call,
  `people_extraction.ensure_person_note_for_captured_email(email
  ["sender_name"], email["sender_email"])`, ensures every newly captured
  email's sender gets a Person note created or topped up as part of the
  same write — no separate manual step, going forward (Scenario 7). Only
  the import line and this one call site changed; `classify_recent_emails`'s
  return shape, `run_capture_and_record_completion`, and the manual
  `POST /poc/classify-emails` endpoint are untouched. Verified live
  (`REQ-SB-10-US-01-AC-07`, both creation and update halves) against the
  real Outlook desktop client and the real configured vault: called
  `classify_recent_emails(limit=10)` against two genuinely unprocessed
  emails, confirming `Work/People/ahmad.hamzeh@core42.ai.md` and
  `Work/People/shadi.shaat@core42.ai.md` were created in the same call
  with no prior manual step (creation half: PASS); immediately calling
  `ensure_person_note_for_captured_email` again for the same sender
  returned `created: False` with no duplicate note (update half: PASS)
- feat: new `POST /poc/retrofit-people-from-emails` endpoint
  (`REQ-SB-10-US-01-T04`) — thin wrapper around T02's
  `retrofit_people_from_emails`, matching the existing `/poc/backfill-tags`/
  `/poc/flatten-customer-folders`/`/poc/retrofit-customer-hub-links`
  one-off-migration-endpoint shape exactly; tallies `created`/`linked`
  counts from the results list. This closes `REQ-SB-10-US-01` — all nine
  ACs now verified (AC-07 live in T03; AC-01 through AC-06, AC-08, AC-09
  verified live here). Verified live against the real configured vault
  using real, naturally-occurring senders wherever the vault already had
  one, falling back to a single throwaway Email note only for AC-09's
  blank-`sender_email` case: `mohamed.eltanany@core42.ai` (7 Email notes,
  no Person note yet) produced exactly one Person note with `kind/person`
  and, since Core42 is an existing known customer, both the `company/core42`
  tag and a `[[Core42]]` wikilink, no duplicate hub note (AC-01, AC-03);
  `karimlouis@microsoft.com` (Microsoft, a derivable but not-a-known-
  customer company) got the `company/microsoft` tag only, no wikilink, no
  new hub note (AC-04); `mahmoud.m.moussa@live.com` (a personal email
  domain already in `people_extraction.py`'s known-provider set) got
  neither tag nor wikilink (AC-05); a throwaway blank-`sender_email` Email
  note was skipped without erroring the run (AC-09); a manually-added
  `## Notes` line on the Microsoft-company Person note survived an
  idempotent second call byte-for-byte (matching SHA-256 hashes,
  confirming AC-02's no-duplicate-Person-note guarantee too) (AC-02,
  AC-06); creating a `Work/Customers/Microsoft.md` hub note (via
  `customer_hub_linking.ensure_customer_hub_note`, then deleted afterward
  as test-only) and re-running retroactively added the `[[Microsoft]]`
  wikilink to that same Person note without disturbing the manual content
  (AC-08). Real production Person notes created by this real retrofit run
  against the real vault (18 distinct senders) were deliberately kept, not
  cleaned up — only the throwaway Email note, the throwaway
  `Microsoft.md` hub note, and the wikilink line it caused were removed
  afterward
- chore: **SPRINT-004 Done** (2026-08-11) — REQ-SB-10 closed. Sizing
  estimate (~4 tasks, S) matched actual exactly, third sprint in a row for
  this task shape. Retrospective drafted, flagged for human harvest into
  `Implementation/Learnings.md` (see `REVIEW-QUEUE.md`)
- fix: `BUG-001` — Email notes now wikilink to their sender's Person note
  (`BUGFIX-01-US-01-T01`) — new `people_extraction.link_email_to_person
  (email_note_path, person_note_path) -> bool`, mirroring
  `customer_hub_linking.link_note_to_customer_hub`'s exact shape: inserts
  an inline `**Sender:** [[PersonStem]]` wikilink into the Email note's
  body via the existing `vault_writer.insert_body_line_if_missing`
  primitive, only if not already present. Wired into
  `email_classification.classify_recent_emails`'s existing
  `ensure_person_note_for_captured_email` call site — its previously-
  discarded return value is now captured, and `link_email_to_person` is
  called whenever it isn't `None`. Closes the inbound (Email→Person)
  direction of `MEMORY.md`'s 2026-08-11 standing constraint (a
  referencing note must link out, not just cause the referenced note to
  be created), which the original `REQ-SB-10` pass only checked outbound
  (Person→Company). Verified live: a genuine newly-captured email
  (`Rudra.Potturu@tadweer.ae`, captured by the real app-start capture
  trigger) had `**Sender:** [[rudra.potturu@tadweer.ae]]` in its body
  immediately after capture, with no separate manual step
  (`BUGFIX-01-US-01-AC-01`, going-forward half)
- feat: one-time `retrofit_email_sender_links()` batch + new
  `POST /poc/retrofit-email-sender-links` endpoint (`BUGFIX-01-US-01-T02`)
  — backfills the same `**Sender:** [[PersonStem]]` wikilink onto every
  already-captured Email note with a real `sender_email`, mirroring
  `retrofit_customer_hub_links`'s/`retrofit_people_from_emails`'s exact
  batch shape and the existing `/poc/retrofit-*` endpoint pattern. Unlike
  `retrofit_people_from_emails`, deliberately does not dedup by sender —
  every Email note from a given sender needs its own body link. Verified
  live against the real configured vault (`VAULT_PATH`): one run linked
  249 already-captured Email notes (`BUGFIX-01-US-01-AC-01`, retrofit
  half), 84 notes correctly skipped for having no `sender_email` (Person/
  Customer-hub notes plus one Guide note), and a real newly-captured email
  already linked by the forward hook read `already_linked`; a second,
  identical run produced zero new links and no duplicate wikilink lines
  (`BUGFIX-01-US-01-AC-02`); a naturally-occurring blank-`sender_email`
  note (`Work/Guides/Manual-Entry-Guide.md`) was skipped, left
  byte-for-byte unchanged, with no error on either run
  (`BUGFIX-01-US-01-AC-03`)
- chore: **SPRINT-005 Done** (2026-08-11) — `BUGFIX-01-US-01` closed,
  `BUG-001` flipped `In Sprint → Closed` in both `BUGS.md` and
  `BACKLOG.md`. Sizing estimate (~2 tasks, XS) matched actual exactly.
  Retrospective drafted, flagged for human harvest into
  `Implementation/Learnings.md` (see `REVIEW-QUEUE.md`)
- feat: Partner hub-note baseline primitives + four generic rename/remove/
  swap/replace primitives (`REQ-SB-16-US-01-T01`) — ten new functions
  appended to `app/data_access/vault_writer.py`: `partner_hub_note_path`/
  `_exists`, `build_partner_tags`, `create_partner_hub_note_baseline`,
  `ensure_partner_hub_note_baseline_frontmatter`, `list_known_partners`
  (mirroring the Customer hub-note family exactly, `ADR-009`'s shorter
  Partner baseline-key set, no `affiliate_of`), plus `rename_frontmatter_key`,
  `remove_frontmatter_key_if_present`, `swap_tag`, `replace_body_line` —
  four generic, idempotent-by-construction primitives (no-op once the old
  key/tag/line is already absent) any future rename/retag migration can
  reuse. No existing function's behavior changed. Verified live against the
  real vault (AC-01 plus five non-AC smoke checks, all throwaway data
  deleted afterward)
- feat: new `app/business/partner_hub_linking.py` module
  (`REQ-SB-16-US-01-T02`) — `ensure_partner_hub_note`,
  `link_note_to_partner_hub` (mirroring `customer_hub_linking.py`'s two
  granular primitives exactly), and `migrate_customer_to_partner(
  customer_name)` — the one-time Customer→Partner migration: moves
  `Work/Customers/<name>.md` to `Work/Partners/<name>.md`
  (`vault_writer.move_note_and_attachments`), then a single generic
  vault-wide scan retags every note whose `customer` frontmatter equals
  `customer_name` (frontmatter key, `type` value, tags, and — where
  present — the inline `**Customer:**` body line), idempotent by
  construction. A parallel sibling to `customer_hub_linking.py`, per
  `ADR-009` — the `Done` REQ-SB-14 module and its
  `email_classification.py` call site are untouched. Verified live against
  a small faithfully-reproduced Microsoft-shaped fixture (throwaway data
  only — see `REQ-SB-16-US-01-T04` below for why this was **not** run
  against the real Microsoft data yet)
- feat: `people_extraction.py` gains a Partner-matching branch
  (`REQ-SB-16-US-01-T03`) — new `find_matching_partner` (mirrors
  `find_matching_customer` exactly, against a new vault-derived
  `list_known_partners()`); `ensure_person_note` now checks Customer first
  (unchanged) and Partner second, only when no Customer match was found
  (`ADR-009`'s mutual-exclusivity rule); return dict gains `partner_matched`
  (additive). Verified live end-to-end against throwaway partner/customer
  names (`REQ-SB-16-US-01-AC-01/02/03/04/08` Person-note half, all PASS) —
  real Microsoft/ADNOC data untouched by this task
- fix: `MEMORY.md` gains a new standing constraint — a "generic scan"
  migration keyed on frontmatter-field equality silently misses notes that
  reference the same entity by tag plus inline wikilink alone (found live
  verifying `REQ-SB-16-US-01-T04`, below)
- fix: `partner_hub_linking.migrate_customer_to_partner`'s retag-scan match
  predicate (`REQ-SB-16-US-01-T04`, corrected scope per `ADR-012`) —
  broadened from frontmatter-equality alone to a union of that signal and
  a new inline-body-wikilink-presence signal, both read from the loop's
  existing single `read_note()` call (no second scan, no new
  `vault_writer.py` primitive). Resolves `ESCALATIONS.md` → `ESC-001`: the
  original predicate structurally could never reach Person notes, which
  never carry a `customer` frontmatter field, only a `company/<slug>` tag
  plus a separately-written inline `**Customer:** [[Hub]]` wikilink
- feat: new `POST /poc/migrate-customer-to-partner` endpoint
  (`REQ-SB-16-US-01-T04`) — thin wrapper over the corrected
  `migrate_customer_to_partner`, matching the existing `/poc/retrofit-*`
  one-off-migration-endpoint shape. Ran live against the real vault: moved
  `Work/Customers/Microsoft.md` → `Work/Partners/Microsoft.md` (correct
  schema, no `affiliate_of`, existing `[[Microsoft]]` wikilinks still
  resolve — exactly one `Microsoft.md` file exists anywhere in the vault);
  a full vault-wide sweep confirmed all 15 real Microsoft-related notes the
  generic scan found (1 hub note, 2 Email, 1 Meeting, 1 Newsletter, 4
  Notification, 6 Person — one more Person note than the story's original
  count of 5, correctly picked up by the generic, not-hardcoded design)
  are fully retagged with zero stale Customer references remaining
  anywhere; a rerun is a true no-op; manually-added hub-note content
  survives reruns. This closes `REQ-SB-16-US-01` — all 8 locked ACs now
  verified live
- fix: two real vault notes manually repaired as due diligence during this
  live verification, both documented in `ESCALATIONS.md`: a harmless
  duplicate wikilink line on `nabeehquaroout@microsoft.com.md` (a real,
  newly-found 6th Microsoft Person note), and a genuine structural
  corruption on `karimlouis@microsoft.com.md` (pre-existing since an old
  `REQ-SB-10-US-01-T04` verification pass — `insert_body_line_if_missing`'s
  fixed body-start byte offset assumption, `ESC-003`, new finding, `Open`,
  primitive itself not yet fixed — see `MEMORY.md`)
- feat: `Templates/Research.md` (`REQ-SB-17-US-01-T01`) — the fifth
  Obsidian core-Templates file, authored directly into the real vault
  (`VAULT_PATH`), matching the resolved Research schema field-for-field
  (`type: Research`, `title`/`author` `REPLACE_WITH_...` placeholders,
  `tags: [kind/research]`), free-form body, deliberately no customer/
  company link anywhere. Verified live: real YAML parse confirms valid
  frontmatter with both placeholders unfilled; raw-text scan confirms no
  `customer`/`company` substring anywhere in the file
- docs: `Work/Guides/Manual-Entry-Guide.md` gains a fifth `## Research`
  section (`REQ-SB-17-US-01-T02`) — additive only: the opening paragraph
  now names five note types (Research added), and a new section matches
  the existing four sections' exact `**Folder:** ... · **Template:** ...`
  shape, citing `Work/Researches/`/`Templates/Research.md` by exact name.
  The four pre-existing sections and the "How to insert a template" steps
  are byte-for-byte unchanged. This closes `REQ-SB-17-US-01` — all 4 ACs
  verified live
- chore: **SPRINT-007 Done** (2026-08-11) — both `REQ-SB-16-US-01` and
  `REQ-SB-17-US-01` closed, every locked AC verified live against the real
  vault. Sizing estimate (~6 tasks, M) matched actual task count exactly,
  though `REQ-SB-16-US-01-T04`'s own live-migration verification needed a
  mid-flight architecture correction (`ADR-012`) and surfaced one
  unrelated, real primitive-level bug (`ESC-003`, still `Open`).
  Retrospective drafted, flagged for human harvest into
  `Implementation/Learnings.md` (see `REVIEW-QUEUE.md`)
- feat: **first real frontend page** (`REQ-SB-12-US-01-T01`, app shell +
  routing scaffold) — `react-router` (pinned `^7.18.2` per ADR-010's `v7.x`
  decision) wires `App.tsx`'s `<BrowserRouter>` to three routes (`/`,
  `/my-day`, `/settings`) behind a persistent `AppShell`/`Sidebar` layout;
  the collapsible burger-menu sidebar reproduces `html-prototype`'s
  `.app-shell`/`.sidebar-collapsed` behavior exactly (`aria-expanded`
  flips on toggle), `NavLink`'s `isActive` drives the `.active` nav-item
  class. `styles/tokens.css`/`shell.css`/`settings.css` ported near-
  verbatim from `html-prototype/styles.css`; the old Vite-template
  `App.css`/`index.css` counter-demo content removed. `api/client.ts`
  (thin `fetch` wrapper convention, unused this pass) established per
  ADR-010. Verified live in a real browser: burger toggle (`AC-04`) and
  nav round-trip across all 3 placeholder pages (`AC-05`) both PASS, zero
  console errors
- feat: **Agents Map polar-grid visualization** (`REQ-SB-12-US-01-T02`) —
  `features/agents-map/` (`mockAgents.ts` — the prototype's exact 5-agent/
  3-section populated dataset plus an empty first-run dataset;
  `polarLayout.ts` — a pure `polarToCartesian(radius, angleDeg)` geometry
  function, replacing the prototype's hand-derived per-node coordinates;
  `KnowledgeBaseNode`/`SectionHub`/`AgentNode`/`AgentsMapCanvas`) renders
  a central Knowledge Base "brain" SVG with 3 Section Hubs and 5 type-
  classed agent nodes (`.agent-node--worker/--producer/--expert`) on a
  3-ring polar grid, plus the ambient radar/ring/section-boundary/spoke-
  line/cluster-line SVG chrome. `styles/agents-map.css` ported near-
  verbatim. Verified live: populated state (1 KB element + 5 correctly-
  typed agent nodes, `AC-02`) and first-run empty state (KB element +
  "No agents connected yet" message, zero agent/hub nodes, `AC-03`) both
  PASS; every node's computed position matches the approved prototype's
  literal coordinates to within rounding
- feat: **Settings page reachability** (`REQ-SB-12-US-01-T03`) — minimal
  placeholder (`<h1>Settings</h1>` + an explanatory paragraph) replacing
  `T01`'s bare placeholder; no Vault/Connections card content (explicitly
  deferred per story scope). Verified live: URL reaches `/settings`, no
  thrown error, Settings `NavLink` carries `aria-current="page"` +
  `.active` while the other two nav items do not (`AC-06` PASS)
- chore: **`REQ-SB-12-US-01` (`SPRINT-008`) Done** (2026-08-11) — `T04`
  end-to-end verification found zero integration defects across `T01`–
  `T03`; all 6 locked ACs (`AC-01`–`AC-06`) re-verified together in one
  continuous, fresh-browser-session pass (headless Chrome via the Chrome
  DevTools Protocol — no test-stack ADR exists yet, so this is this
  sprint's "browser preview tool"), zero console errors/warnings
  throughout. This is the first-ever frontend build in this project and
  the foundation `REQ-SB-12-US-02` (My Day) and `REQ-SB-13-US-01` (agent
  chat panel) both build on next. Sprint `status: Done`, `gate: flagged`
  (retro drafted, awaiting human `Learnings.md` harvest — see
  `REVIEW-QUEUE.md`)
  (deferred until the blocked task resolves)
- feat: **new Outlook Calendar read primitive** (`REQ-SB-08-US-01-T01`) —
  `app/data_access/outlook_com.py::list_calendar_events(days_back,
  days_ahead, limit)`, this codebase's first calendar-read capability
  (ported from agentic-map's `list_upcoming_events`/`list_calendar_since`
  COM mechanics per ADR-008), plus `_resolve_attendees` (merges required/
  optional recipients into one flat `{"name", "email"}` list, excluding
  organizer/resource recipients). Verified live: 38 real events returned,
  correct schema, real Outlook calendar-view data matched
- feat: **Meeting-note vault-writer primitives** (`REQ-SB-08-US-01-T02`) —
  `meeting_note_path`/`meeting_note_exists`/`create_meeting_note_baseline`/
  `ensure_meeting_note_baseline_frontmatter` (mirroring the Person/Customer-
  hub baseline-preservation contract), `load_processed_meeting_ids`/
  `mark_meeting_processed` (mirroring the email dedup-state-file shape),
  and a genuinely new `upsert_attendee_links` primitive — a per-attendee-
  wikilink upsert for the growable `**Attendees:** [[P1]], [[P2]], ...]`
  body line (distinct from the single-target `insert_body_line_if_missing`
  reused as-is for `**Customer:** [[Hub]]`). Verified live via a throwaway
  note, then cleaned up
- feat: **`app/business/meeting_classification.py`** (`REQ-SB-08-US-01-T03`,
  new) — the Meetings-capture orchestration: fetch calendar events →
  exclude the vault owner's own email (new required `Settings.self_email`
  config field, `.env`-sourced) → derive a customer via majority vote among
  attendee companies (tie-broken by first-encountered order) → write/top-up
  the Meeting note → link the matched customer hub and every attendee's
  Person note (reusing `people_extraction.ensure_person_note`/
  `customer_hub_linking`'s granular primitives as-is, per REQ-SB-10/14's
  established carve-out). Verified live: correct customer derivation
  (majority vote confirmed against real Core42-domain attendees), and the
  vault owner's own email confirmed excluded from both Person-note creation
  and customer derivation on a real self-organized meeting
- feat: **Meetings capture rides the existing hourly scheduler**
  (`REQ-SB-08-US-01-T04`) — `email_classification.
  run_capture_and_record_completion` gains one additional call,
  `meeting_classification.classify_recent_meetings()`, alongside its
  existing email-capture call; zero changes to `app/scheduling/
  capture_scheduler.py` (confirmed by diff — extends ADR-005 without
  rewriting it, per ADR-008). Verified live: a fresh dev-server app-start
  produced 38 real Meeting notes with no separate manual trigger
- feat: **`POST /poc/classify-meetings`** (`REQ-SB-08-US-01-T05`) — manual
  on-demand trigger mirroring `/poc/classify-emails`'s thin-wrapper shape.
  All 10 of this task's tagged ACs (`AC-01`–`AC-09`, `AC-11`) verified live
  against the real Outlook calendar/vault: idempotent reruns (no
  duplicates, manually-added Meeting-note and Person-note content
  preserved), no-customer-match handling, same-subject/same-date
  disambiguation, no-attendee events handled without error, recurring-
  occurrence handling, and — the story's most important AC — the vault
  owner's own email confirmed excluded from both Person-note creation and
  customer derivation on real production data, not just a throwaway
  construction
- chore: **`REQ-SB-08-US-01` (`SPRINT-006`) Done** (2026-08-11) — all 5
  tasks built and verified live; all 11 locked ACs pass against the real
  Outlook calendar and vault (38 real Meeting notes correctly captured,
  classified, and linked). One genuine architectural finding surfaced
  during Scenario 9 verification and escalated per ADR-008's own
  pre-authorized path, not silently patched: 3 real occurrences of a
  recurring meeting were found to share one identical, full Outlook
  `EntryID` (not just a coincidental filename-suffix match), falsifying
  ADR-008's stated per-occurrence-EntryID-uniqueness assumption — today's
  notes are all correct only because the filename also incorporates the
  event's date, and a future same-date recurring collision could silently
  merge two distinct meetings into one note. Does not block this sprint's
  `Done` status (every locked AC passed against real data available
  today). Full detail: `ESCALATIONS.md` → `ESC-002`; `REVIEW-QUEUE.md`
  pointer added for a human decision (superseding ADR vs. accepted known
  limitation). Sprint `status: Done`, `gate: flagged` (retro drafted,
  awaiting human `Learnings.md` harvest, plus the `ESC-002` decision — see
  `REVIEW-QUEUE.md`)
- feat: **`vault_writer.list_notes_in_kind_folder(kind)`**
  (`REQ-SB-12-US-02-T01`) — same-shape sibling of `list_all_note_paths()`
  scoped to one `Work/<kind>/` folder, returning `[]` if that kind folder
  doesn't exist yet. Verified live against the real vault (178 sorted
  paths under `Work/Emails/`; `[]` for a nonexistent kind)
- feat: **`app/business/my_day.py`** (`REQ-SB-12-US-02-T02`, new) —
  read-only My Day aggregation: `list_email_items()`/`list_calendar_items()`
  project `subject`/`sender`(or `start`)/`customer` from captured Email/
  Meeting notes (`customer` normalized to `null` for `"Unsorted"`/absent,
  reusing `list_known_customers()`'s existing convention); `summary()`
  returns per-section counts (`todo` hardcoded `0` — REQ-SB-09 has no
  resolved task source yet). Verified live against the real vault
- feat: **`GET /my-day/summary|emails|calendar|todo`**
  (`REQ-SB-12-US-02-T03`, new `app/api/my_day_router.py`) — the first
  router outside the `/poc` migration-endpoint family, registered in
  `app/main.py` alongside the existing routers. Also added
  `fastapi.middleware.cors.CORSMiddleware` to `app/main.py` — the first
  real browser-to-backend fetch call in this codebase, which fails
  outright without it; scoped to the Vite dev server's own default
  origins. Verified live against the real vault (178 emails, 39 meetings,
  0 to-do items)
- feat: **My Day dashboard page** (`REQ-SB-12-US-02-T04`) — three
  clickable `.day-section-card`s (Emails/Calendar/To-Do) with live counts
  from `/my-day/summary`, or "Nothing captured yet" per section; drill-down
  routes (`/my-day/emails|calendar|todo`) registered in `App.tsx`;
  `features/my-day/client.ts` and `styles/my-day.css` (ported from
  `html-prototype/styles.css`) added. Verified live in a real browser via
  headless-Chrome CDP: exactly 3 cards render, correct counts/empty-state
  per section, all-zero first-run state (temporary stub), and all 3
  card-click navigations land on the right drill-down route
- feat: **Emails drill-down page** (`REQ-SB-12-US-02-T05`,
  `MyDayEmailsPage.tsx`) — populated `.item-list` (subject/sender/customer,
  `null` renders "Unclassified") sourced from `/my-day/emails`, or an
  `.empty-state`. Verified live: 178 real captured emails rendered
  correctly (5 "Unclassified"); empty state confirmed via a temporary
  client-side stub, then reverted
- feat: **Calendar drill-down page** (`REQ-SB-12-US-02-T06`,
  `MyDayCalendarPage.tsx`) — populated `.item-list`
  (subject/start/customer, `null` renders "No customer") sourced from
  `/my-day/calendar`, or an `.empty-state`. Verified live: 39 real
  captured meetings rendered correctly (3 "No customer") — SPRINT-006
  landed concurrently mid-sprint, so this is real production data, not the
  synthetic test note the task originally planned; empty state confirmed
  via a temporary client-side stub instead (the real vault can no longer
  produce it naturally), then reverted
- feat: **To-Do drill-down page** (`REQ-SB-12-US-02-T07`,
  `MyDayTodoPage.tsx`) — always renders `.empty-state` ("To-Do Capture
  (REQ-SB-09) has not been built yet"), deliberately no populated-state
  code path pending REQ-SB-09's own future task-source resolution.
  Verified live
- chore: **`REQ-SB-12-US-02` (`SPRINT-009`) Done** (2026-08-11) — all 7
  tasks built and verified live; all 8 locked ACs pass (backend
  smoke-checked against the real vault; frontend verified in a real
  browser via headless-Chrome CDP, `npm run build` clean). Zero blocked
  tasks, zero `ESCALATIONS.md` entries. One genuine architectural gap
  (missing CORS middleware — see the `T03` entry above) was found and
  fixed within scope, flagged for human spot-check of the allowed-origins
  policy. Sprint `status: Done`, `gate: flagged` (retro drafted, awaiting
  human `Learnings.md` harvest, plus the CORS spot-check — see
  `REVIEW-QUEUE.md`)
- feat: **agent-history vault_writer primitives** (`REQ-SB-13-US-01-T01`,
  `ADR-011`) — new `.second-brain/agent_communication_history.json`,
  `append_agent_history_entry(agent_id, kind, text)` /
  `load_agent_history(agent_id)`, mirroring the existing
  `record_capture_run_completed`/`load_last_capture_run` shape. Additive
  only — no existing `vault_writer.py` function changed
- feat: **static agent/settings/actions/trigger-phrases registry**
  (`REQ-SB-13-US-01-T02`, new `app/business/agent_registry.py`) — five
  known agents (`email-capture`/`meeting-capture`/`todo-capture`/
  `people-producer`/`vault-qa`), each with `settings`/`actions`/
  `trigger_phrases`, deliberately hardcoded per `ADR-011` (not
  vault-derived — which agents exist is deployment configuration, not
  open-ended vault content)
- feat: **agent chat trigger-phrase matching** (`REQ-SB-13-US-01-T03`, new
  `app/business/agent_chat.py`) — `handle_chat_message(agent_id, message)`,
  lowercase substring match against the agent's declared trigger phrases,
  registry order, first match wins; deliberately not an NLU/LLM pipeline
  (`ADR-007`/`ADR-011`)
- feat: **`run_capture_and_record_completion` history hook**
  (`REQ-SB-13-US-01-T04`) — one additional
  `vault_writer.append_agent_history_entry("email-capture", "run_event",
  ...)` call, alongside the existing `record_capture_run_completed()`
  call, so every trigger source (scheduler, app-start,
  `/poc/classify-emails`, the new agent-panel action/chat triggers)
  produces the same Communication History entry through one shared entry
  point. The only change to already-`Done` code this story makes
- feat: **`GET /agents/{id}`, `POST /agents/{id}/actions/{action_id}`,
  `POST /agents/{id}/chat`, `GET /agents/{id}/history`**
  (`REQ-SB-13-US-01-T05`, new `app/api/agents_router.py`, registered in
  `app/main.py`) — the shared `_invoke_action`/`_ACTION_HANDLERS` call
  site used by both the direct action-trigger endpoint and the chat
  endpoint, so a button click and a matching chat message invoke the
  identical handler. Only `email-capture`'s `run_capture_now` has a real
  handler this pass; every other action returns an honest "not yet
  available" result. Verified live: `GET /agents/email-capture` returns
  settings/actions with no `trigger_phrases` leaked, `404` for an unknown
  agent, chat matching and fallback confirmed, the real action-trigger
  path confirmed via `T07`'s UI-driven check (see below)
- feat: **agent detail panel — settings, available actions, open/close**
  (`REQ-SB-13-US-01-T06`, new `AgentDetailPanel.tsx`/
  `agentsApiClient.ts`/`styles/agent-panel.css`; `AgentNode.tsx`/
  `AgentsMapCanvas.tsx` gained `onSelect`/`onSelectAgent` click wiring;
  `AgentsMapPage.tsx` gained selection state) — clicking an `.agent-node`
  opens a `.side-panel` overlay showing that agent's real settings/
  actions; closes via its close control or an outside click. Verified
  live in a real browser via headless-Chrome CDP
- feat: **embedded chat thread** (`REQ-SB-13-US-01-T07`) — send/receive
  against the real `POST /agents/{id}/chat` endpoint, no canned/demo
  reply. Verified live: a non-matching message gets a real fallback
  reply; "please run capture now" triggered one real Outlook/Compass/
  vault-write capture run through the actual UI, with a reply confirming
  what was done — no external navigation at any point
- feat: **communication history + full agent-switching refresh**
  (`REQ-SB-13-US-01-T08`) — unified chronological `.log-list` (chat +
  run events together, not two separate lists) or an `.empty-state`,
  re-fetched on agent switch and after every chat send. Verified live:
  populated history renders correctly ordered, an untouched agent
  (`meeting-capture`) shows the empty state, and switching agents mid-panel
  fully replaces every section's content with no leftover from the
  previously selected agent
- chore: **`REQ-SB-13-US-01` (`SPRINT-010`) Done** (2026-08-11) — all 8
  tasks built and verified live; all 8 locked ACs pass, including both
  trust-surface-defining scenarios (a chat message triggering a real
  backend action; chat + run events unified in one chronological
  history), confirmed with a single real capture run triggered through
  the actual chat UI. `npm run build` clean. Zero blocked tasks, zero
  `ESCALATIONS.md` entries; small additive CORS-origin extension in the
  shared `app/main.py` (Vite landed on port 5174, already flagged by a
  concurrent session's own `REVIEW-QUEUE.md` entry, not duplicated).
  Sprint `status: Done`, `gate: flagged` (retro drafted, awaiting human
  `Learnings.md` harvest — see `REVIEW-QUEUE.md`)
- feat: **Agents Map wired to real backend data, replacing `mockAgents.ts`'s
  static example** (operator-directed, 2026-08-11, outside the formal
  pipeline — small, well-bounded wiring task, not new product scope). New
  `agent_registry.list_agents()` + `GET /agents` (`app/api/agents_router.py`)
  return the real 5-agent registry (id/name/type) already built by
  `REQ-SB-13-US-01`/ADR-011. New frontend `fetchAgentList()`
  (`agentsApiClient.ts`) + `layoutAgents()` (`features/agents-map/
  layoutAgents.ts`) derive section membership and evenly-spaced ring angles
  from the real list instead of hardcoded per-agent coordinates —
  `AgentsMapPage` now fetches on mount instead of importing static
  `POPULATED_SECTIONS`/`POPULATED_AGENTS`, which were removed from
  `mockAgents.ts` (shared type definitions kept). Verified live: `GET
  /agents` returns the real registry, the rendered map matches it exactly
  (5 agents, correct sections/rings), zero console errors on a fresh load.
- design: `/design` run retroactively against REQ-SB-18 (Dynamic Agent
  Sections & Agent-to-Section Assignment) and REQ-SB-19 (Per-Agent LLM
  Provider Selection), still pre-approval — both stories already went
  through `/spec` and had their Gherkin locked (including the operator-
  resolved block-until-empty/unused deletion policy, Scenario 4b in both),
  and their analyst flagged the missing prototype coverage for `/design`
  to supply before `/plan-tasks`. `html-prototype/settings.html` gains two
  new cards: **Sections** (list/create/rename/delete, REQ-SB-18) and
  **Providers** (list/add/edit/remove, Compass pre-seeded and marked
  "Default", REQ-SB-19); the existing Vault/Connections cards (REQ-SB-12)
  are untouched. Both new cards demonstrate the block-until-empty/unused
  policy two ways at once — a disabled Delete/Remove button with a `title`
  tooltip, plus an always-visible danger-colored explanation naming which
  agent(s) block it — and an isolated "blocked deletion/removal attempt"
  state-switcher panel. Credential fields are always `type="password"`
  (masked). `html-prototype/agents-map.html`'s side panel `kv-list` gains
  its first genuinely *editable* rows — a Section picker and a Provider
  picker (native `<select>`, zero JS) — on all 5 existing agents; People
  Notes is deliberately set to a non-Compass Provider with no real client
  yet, surfaced with a `badge-warning` "Not yet available" + explanatory
  text, directly demonstrating REQ-SB-19 Scenario 7's honesty requirement
  at the exact surface where the user picks a Provider. A new third Agents
  Map state, "5 sections (REQ-SB-18 N-section reference)", proves the
  existing polar-grid Hub mechanism (ring=Type, angle=Section, Hub on the
  inner band, radar/ring background, KB brain — all otherwise UNCHANGED)
  generalizes past the approved design's hardcoded 3 hubs to an arbitrary
  N: 5 evenly-spaced Sections (72° apart, same angle x radius trigonometry
  every prior agents-map.html round used, re-derived from round 6's own
  committed coordinates rather than eyeballed), 2 of them genuinely
  zero-agent Hubs (Scenario 7) rendering with no cluster lines — a visual
  reference for `/plan-tasks`'s real `layoutAgents.ts`/`polarLayout.ts`
  computation, not the final production geometry (explicitly out of this
  batch's scope). Reused: My Day's `.item-list`/`.item-row` family for
  both new Settings lists; native `<details>/<summary>` for every create/
  rename/edit/add affordance instead of new JS wiring. New (added to
  `styles.css`): `.item-row-actions`, `.btn-danger` (symmetric with
  `.btn-primary`, built from the existing `--color-danger` token, no new
  hex), `.kv-select` (compact inline `<select>` for the side panel), and a
  `summary.btn` marker reset. Hub color in the new 5-section state is
  neutral (`--color-accent`) instead of the old per-Type modifier classes
  — a Section can now hold agents of any Type (Scenario 6), so a single
  Type color on its Hub would misrepresent it; the existing 3-hub
  "Populated" state's Type-colored hubs are left exactly as approved
  (minimal-change scope), flagged in `REVIEW-QUEUE.md` for a human call on
  whether that older state should eventually be relabeled to the new
  Section names. As always, flagged for mandatory human browser sign-off
  before `/plan-tasks` proceeds — never marked "clear"
- feat: `REQ-SB-18-US-01` (User-editable agent Sections, decoupled from
  agent Type, with per-agent section reassignment, `SPRINT-011`) shipped
  end-to-end and verified live, per `ADR-014`. Backend: `app/data_access/
  vault_writer.py` gained `load_sections_state`/`save_sections_state`
  (new `.second-brain/agent_sections.json`); new `app/business/
  section_registry.py` (seeds the starting 5 sections — Technical, Sales,
  Productivity, Customers, Products — on first read, self-heals any known
  agent absent from `assignments` to the first section, and owns
  create/rename/delete with a block-until-empty result dict); new `app/
  api/sections_router.py` (`GET/POST /sections`, `PATCH/DELETE
  /sections/{id}`, `409` with a name-resolved message when a delete is
  blocked), registered in `app/main.py`; `app/api/agents_router.py`
  gained `PATCH /agents/{agent_id}` (`section_id`) and merged
  `section_id`/`section_name` fields onto `GET /agents`/`GET
  /agents/{agent_id}`, composed at the router layer without modifying
  `agent_registry.py` (`ADR-011` point 2 untouched). Frontend:
  `layoutAgents.ts` rewritten to a genuinely N-section-generic computation
  (hub angles evenly spaced around the full circle from the real `GET
  /sections` list; section membership from each agent's own `section_id`,
  no longer from `type`); `mockAgents.ts`'s `AgentSection` dropped `type`,
  `SectionId` widened to `string`; `AgentsMapCanvas.tsx`'s
  `section-boundary` dividers generalized from 3 fixed lines to N
  adjacent-hub-angle-midpoint lines, and Hub/spoke-line/cluster-line
  coloring moved to one neutral `var(--color-accent)` (a Section can now
  hold agents of any Type); `SectionHub.tsx` dropped its per-Type modifier
  class; new `src/frontend/src/features/settings/SectionsCard.tsx` +
  `settingsApiClient.ts` (Settings' new Sections area — list/create/
  rename/delete, a disabled+tooltipped Delete button when blocked, and a
  blocked-message region rendering the server's exact `409` text);
  `AgentDetailPanel.tsx` gained a Section `<select>` kv-row wired to the
  new `updateAgentAssignment` (`agentsApiClient.ts`). Verified live (real
  `.second-brain/agent_sections.json`, real backend on `:8001`, real
  frontend via headless-Chrome-via-CDP on `:5173`): all 9 locked ACs pass,
  including both trust-defining scenarios — `AC-05` (blocked deletion:
  confirmed the exact `409` message renders in the UI, section/assignments
  unchanged) and `AC-09` (the Agents Map reflects a just-changed
  assignment with no code change/restart, confirmed via cluster-line
  topology counts matching the reassignment exactly). `npx tsc --noEmit`
  and `npm run build` both clean. Full verification detail: each task's
  own `## Implementation Log`,
  `Implementation/Tasks/REQ-SB-18-US-01-T01`…`T08`.
- design: `/design` run against `REQ-SB-20-US-01` (Section Hub Intelligence
  & Cross-Section Routing), `REQ-SB-21-US-01` (Agent Working Modes), and
  `REQ-SB-23-US-01` (My Day Intake Agent), still pre-approval — all three
  already had their Gherkin locked (including the operator-resolved
  decisions in each story's own `## Notes`: free-text keywords/keyword-
  match routing/cross-Section-only for REQ-SB-20; default mode Autonomous/
  a real Pending Approvals surface built now for REQ-SB-21) and were
  flagged for missing prototype coverage. Four changes: (1)
  `html-prototype/agents-map.html`'s side panel Settings `kv-list` gains
  Keywords (free-text, following the Section/Provider picker-row pattern —
  empty on To-Do Capture to demonstrate REQ-SB-20 Scenario 4's "no
  keywords, never a routing target") and Working mode
  (Autonomous/Supervised/Manual, defaulting Autonomous; Meeting Capture and
  People Notes set Supervised, To-Do Capture set Manual) rows on all 5
  agents; (2) Meeting Capture's Chat block gains a pending-approval
  proposal card (new `.chat-proposal` pattern in `styles.css` — dashed-
  warning while pending, solid-success/solid-danger once resolved, all via
  the existing `color-mix(...)`-over-token technique, no new hex), its
  pending/approved/declined outcomes demonstrated via a small
  `.state-switcher` nested inside the chat thread itself; (3) a new
  Pending Approvals surface — a 5th card on `html-prototype/my-day.html`'s
  dashboard grid plus a new drill-down page,
  `html-prototype/my-day-approvals.html` (reusing the same `.item-list`
  pattern the other four My Day drill-downs already use), listing each
  Supervised agent's background-pipeline proposal with Approve/Decline
  actions, plus an empty "queue caught up" state — placed on My Day (not
  Settings, not a new nav item) since My Day is this project's existing
  "things needing my attention today" surface; (4) a new "Quick Capture"
  card at the top of `my-day.html` (the My Day Intake Agent, REQ-SB-23) — a
  free-text input + Capture button plus an `.item-list` submission history
  demonstrating all 4 of that story's locked scenarios (a
  customer-classified filing using the exact tags-and-wikilinks copy from
  `MEMORY.md`'s standing schema, an unclassified filing, a second same-day
  filing proving no filename collision, and a classification-FAILED
  submission with its original text visibly preserved plus a Retry
  affordance) and a first-run empty state. `html-prototype/index.html`'s
  catalog updated to list the new drill-down and the three additions. As
  always, flagged for mandatory human browser sign-off before `/plan-tasks`
  proceeds — never marked "clear". Full breadcrumb: the top-of-file
  comments in `agents-map.html`/`my-day.html`/`my-day-approvals.html`;
  review entry: `REVIEW-QUEUE.md`.
- feat: `REQ-SB-22-US-01` (My Day drill-downs and dashboard counts scoped
  to a rolling 7-day window, `SPRINT-013`) shipped end-to-end and verified
  live. `app/business/my_day.py` gained the first date-range filtering
  ever added to My Day's read path — new `_compute_window()` (3 days
  before through 3 days after `datetime.now()`, recomputed on every call,
  never cached) and `_within_window()` (ISO-date-string-prefix compare,
  no `datetime.fromisoformat()`/timezone logic) helpers; both
  `list_email_items()` and `list_calendar_items()` now narrow to the
  window, and `list_email_items()` gains a `received` field it previously
  omitted entirely. `app/api/my_day_router.py` is unchanged — endpoint
  contracts are unaffected (additive field + narrower result set only).
  Frontend: `features/my-day/client.ts`'s `MyDayEmailItem` gains
  `received: string`; `MyDayEmailsPage.tsx`'s existing `.item-row-meta`
  line renders it. `MyDayCalendarPage.tsx`/`MyDayPage.tsx` needed no code
  change — verified live as already-correct consumers of the now-narrower
  backend response. Verified against the real vault (179 Email notes, 39
  Meeting notes): windowed counts 21 emails / 17 meetings; a real
  out-of-window email and a real out-of-window meeting were each confirmed
  genuinely absent from the returned lists (not flagged, not
  de-emphasized); a monkeypatched `datetime` simulating 10 days later
  produced a correctly-shifted window and result set, then reverted to
  restore the exact original result — confirming the window advances
  automatically with zero caching. Both drill-downs' empty states verified
  via a temporary client-stub-and-revert (`Promise.resolve([])`), real
  populated states restored exactly afterward. `npm run build` clean, zero
  console errors. Full verification detail: `Implementation/Tasks/
  REQ-SB-22-US-01-T01-backend-rolling-window-filtering.md`,
  `Implementation/Tasks/REQ-SB-22-US-01-T02-drilldowns-consume-windowed-
  response.md`.
- feat: `REQ-SB-19-US-01` (Global LLM Provider CRUD in Settings, with a
  per-agent Provider picker defaulting to Compass, `SPRINT-012`) shipped
  end-to-end and verified live, per `ADR-014`, built as a diff on top of
  `REQ-SB-18-US-01`/`SPRINT-011`'s already-landed shared surface. Backend:
  `app/data_access/vault_writer.py` gained `load_providers_state`/
  `save_providers_state` (new `.second-brain/agent_providers.json`); new
  `app/business/provider_registry.py` (seeds a "Compass" Provider entry
  from `app.config.settings.compass_*` on first read, self-heals any known
  agent absent from `assignments` to `"compass"`, owns create/update/
  remove with a block-until-unused result dict, and `has_real_client()` —
  a small hardcoded real-client set, mirroring `ADR-011` point 3's
  "declared but unbuilt" pattern one layer up); new `app/api/
  providers_router.py` (`GET/POST /providers`, `PATCH/DELETE
  /providers/{id}`, `409` with a name-resolved message when a removal is
  blocked, never a `credential` field in any response), registered in
  `app/main.py`; `app/api/agents_router.py` gained the `provider_id`
  portion of `PATCH /agents/{agent_id}`, merged `provider_id`/
  `provider_name`/`provider_available` fields onto `GET /agents`/`GET
  /agents/{agent_id}`, and a Provider-availability gate inside
  `_invoke_action` (returns an honest "not available yet" result before
  ever calling a real handler, when the agent's selected Provider has no
  real client — no silent fallback to Compass, no fabricated response).
  `agent_registry.py`, `app/data_access/compass_client.py`, and
  `app/config.py` were not modified — the pre-seeded "Compass" Provider
  entry is a CRUD-editable *representation* only; the real Compass call
  path keeps reading `.env`/`Settings.compass_*` directly, unaffected by
  any edit made to it from Settings. Frontend: new
  `src/frontend/src/features/settings/ProvidersCard.tsx` +
  `settingsApiClient.ts`'s `/providers` calls (Settings' new Providers
  area — list/add/edit/remove, a masked credential field, a disabled+
  tooltipped Remove button when blocked, and a blocked-message region
  rendering the server's exact `409` text), composed into
  `SettingsPage.tsx` alongside `REQ-SB-18-US-01`'s `<SectionsCard>`;
  `AgentDetailPanel.tsx` gained a Provider `<select>` kv-row (wired to the
  existing `updateAgentAssignment`, `agentsApiClient.ts`'s `AgentDetail`
  widened with `provider_id`/`provider_name`/`provider_available`) plus a
  conditional honesty note when the selected Provider has no real client.
  Verified live (real `.second-brain/agent_providers.json`, real backend
  on `:8001`, real frontend via headless-Chrome-via-CDP on `:5173`): all 8
  locked ACs pass, including both trust-surface-defining scenarios —
  `AC-07` (an agent using Compass behaves identically even after editing
  the Compass Provider entry's own representation, confirmed with one real
  Outlook/Compass/vault-write capture run) and `AC-08` (an agent pointed
  at a non-Compass Provider honestly reports unavailability, confirmed via
  its own history log that no real Outlook/Compass call occurred). `npm
  run build` (`tsc -b && vite build`) clean. Full verification detail:
  each task's own `## Implementation Log`,
  `Implementation/Tasks/REQ-SB-19-US-01-T01`…`T06`.
- feat: `REQ-SB-67-US-01-T01` (`SPRINT-054`) — new `vault_writer.
  replace_body_opening_line(path, new_line) -> bool` primitive, a
  mechanical generalization of `replace_body_section` (`ADR-042` point 2):
  regenerates a note's own "opening region" (between the frontmatter's
  closing `---` — located via the same `"\n---\n"` boundary
  `insert_body_line_if_missing`/`insert_tags_line` already use — and the
  first `## `-level header, reusing the same shared
  `_BODY_SECTION_HEADER_PATTERN`) wholesale on every call, the same
  "regenerate, don't patch" contract every other `replace_body_section`
  call site already follows (`REQ-SB-54` point 8). Placed directly after
  `read_body_section`, same primitive family. Purely additive — no
  existing function's behavior changed. `REQ-SB-54` point 11's first real
  implementation ("current state at a glance" opening body sentence),
  scoped to Threads by the parent story; the primitive itself is general
  (any note kind with well-formed frontmatter). Returns `False` (no write)
  only when the file has no parseable frontmatter-closing boundary at all.
  Verified live against a throwaway `VAULT_PATH`-overridden scratch vault
  (never the real vault): insert into an empty opening region, wholesale
  replace on a second call (prior text fully gone, no residue), real
  `## Summary`/`## Transcript` content and frontmatter left byte-for-byte
  untouched across all calls, malformed-note guard returns `False` with
  zero write, `ast.parse()` confirms no syntax error and the diff is
  purely additive. No AC tag of its own — pure infrastructure; `AC-02`
  (Scenario 2, the opening line) is verified once `T02` wires this
  primitive into `thread_match_merge` (`depends_on: [T01]`). Full
  reasoning: `Implementation/Architecture/architecture.md` → "Real Thread
  Summary Synthesis + Opening-Line + One-Shot Backfill"; verification
  evidence: `Implementation/Tasks/REQ-SB-67-US-01-T01-thread-opening-line-
  primitive.md`.
- feat: `REQ-SB-67-US-01-T02` (`SPRINT-054`) — `thread_match_merge`
  (`app/business/email_classification.py`) gains exactly ONE new real
  `compass_client.summarize_content` call per invocation, replacing the
  old deterministic, non-LLM `_build_thread_summary_content` raw-dump
  (now deleted — zero remaining callers), and reversing
  `REQ-SB-55-US-01`'s own "no second Compass call" story-level Constraint
  via this new story (`REQ-SB-55-US-01` itself untouched, per
  `Implementation/Pipeline.md` hard rule 1). New `_synthesize_thread_
  summary(existing_summary, transcript, new_message_body, prompt_override)`
  helper, grounded ROLLING/INCREMENTALLY — the Thread's own prior `##
  Summary` (read via `vault_writer.read_body_section` BEFORE this call
  overwrites it; `""` on the first message) + its full current `##
  Transcript` (read AFTER this message's own dated entry is appended) +
  the new message's own real body as the delta (`None` on backfill — a
  future `T03` concern, not this task's) — never a full-history
  reconstruction, since `## Transcript` never carries a message's own body
  text. New `_split_thread_synthesis_response(raw_summary)` splits the
  ONE returned `"summary"` string on the first blank line into
  `{"opening_line": str, "summary": str}` (a graceful single-string
  fallback — first line becomes `opening_line`, whole string becomes
  `summary` — when no blank line is found, never an error); this split
  lives entirely in `email_classification.py`, so `compass_client.
  summarize_content`'s own shared parsing (and every other real caller —
  `summarize_attachment`, `skill_tools.summarize_file`,
  `vault_filing_expert`) is untouched. On success: `opening_line` is
  written via `T01`'s new `vault_writer.replace_body_opening_line`;
  `summary` via the pre-existing `replace_body_section` (unchanged). On
  `compass_client.CompassError`: neither the opening line nor `##
  Summary` is written (existing content left completely untouched), and
  `thread_match_merge`'s own return dict gains a `"summary_error"` key —
  mirrors `summarize_attachment`'s own honest, non-fabricating failure
  posture exactly; the function itself never raises. New hardcoded
  `_THREAD_SUMMARY_SYNTHESIS_DEFAULT_INSTRUCTIONS` default-instructions
  literal, used whenever `agent_prompts.get_prompt("thread_match_merge")`
  has no saved override yet — the call site ALWAYS passes a non-`None`
  `prompt_override` into `summarize_content` (never a bare `None`, unlike
  `summarize_attachment`'s own wiring, since `summarize_content`'s own
  generic built-in default does not know about the two-part
  opening-line+Summary split this call site requires). `route_to_project`
  now grounds `guess_project_for_thread`'s own prompt by reading the
  just-written, real synthesized Summary
  (`vault_writer.read_body_section(path, "## Summary")`) instead of
  recomputing a second, divergent summary of the same message —
  `guess_project_for_thread`'s own call shape stays completely unchanged
  (still exactly one call); its `email` parameter is now unused
  internally but its signature is left unchanged (out-of-scope call site
  in `email_capture_pipeline.py`). `app/api/agents_router.py`'s
  `_JOBS_WITHOUT_REAL_PROMPT_CALL_SITE` shrinks from
  `{"thread_match_merge", "detect_recurring_pattern"}` to
  `{"detect_recurring_pattern"}` — `thread_match_merge` now has a real
  Compass call site, so its Job-Settings `GET`/`PATCH` Prompt field is
  genuinely readable/writable end-to-end; `detect_recurring_pattern`'s
  own exclusion is unaffected. No change to `compass_client.py`,
  `agent_prompts.py`, or `email_capture_pipeline.py`'s `StateGraph`
  topology — all composed as-is. Verified live against a throwaway
  `VAULT_PATH`-overridden scratch vault and the real, configured Compass
  Provider (6 real round trips, no mocked Compass response anywhere
  except the one deliberate `AC-05` failure-induction monkeypatch): a
  brand-new, single-message Thread produces a real, non-empty,
  non-raw-body-verbatim synthesized `## Summary` plus a real opening line
  (`AC-01`/`AC-04`); a second message on the same Thread regenerates the
  opening line wholesale (prior exact wording confirmed absent) and folds
  both messages into one coherent Summary (`AC-02`); an induced
  `compass_client.CompassError` (scoped, `finally`-reverted monkeypatch)
  leaves the existing opening line and `## Summary` byte-for-byte
  unchanged, returns an honest `"summary_error"` key, never raises, and a
  DIFFERENT Thread's own subsequent real call succeeds normally,
  confirming the pipeline run continues (`AC-05`); `route_to_project`'s
  own `guess_project_for_thread` spy confirms its prompt text is
  byte-identical to the just-written on-disk `## Summary` and that it is
  still called exactly once; a real, distinctive `agent_prompts.
  set_prompt("thread_match_merge", ...)` override is confirmed reaching
  `summarize_content`'s own `prompt_override` argument, and clearing it
  confirms the hardcoded default literal is used instead of a bare
  `None`; `_JOBS_WITHOUT_REAL_PROMPT_CALL_SITE`'s `GET`/`PATCH` follow-on
  confirmed both halves (`thread_match_merge` now works end-to-end,
  `detect_recurring_pattern`'s own 400-rejection and key-omission stay
  unaffected); regression: `compass_client.summarize_content`'s own
  signature unchanged, `get_job_tree()` still returns the same six Jobs.
  Full reasoning: `Implementation/Architecture/architecture.md` → "Real
  Thread Summary Synthesis + Opening-Line + One-Shot Backfill";
  verification evidence:
  `Implementation/Tasks/REQ-SB-67-US-01-T02-real-thread-summary-synthesis.md`.

- feat: `REQ-SB-67-US-01-T03` (`SPRINT-054`) — one-shot backfill for
  already-captured Thread notes. New `app/business/thread_summary_backfill.py::
  backfill_thread_summaries() -> list[dict]`: iterates
  `vault_writer.list_all_note_paths()` filtered to
  `frontmatter.get("type") == "Thread"` (mirrors `tag_backfill.py`'s own
  iterate-and-filter shape — no new enumeration primitive added), and for
  each Thread reads its own current `## Summary`/`## Transcript` via
  `read_body_section` and calls `T02`'s shared
  `email_classification._synthesize_thread_summary` helper IDENTICALLY,
  with `new_message_body=None` (a pure resynthesis of what's already
  persisted — no delta to fabricate) and
  `prompt_override=agent_prompts.get_prompt("thread_match_merge") or
  T02's own default-instructions literal`. On success: writes the new
  opening line (`T01`'s `replace_body_opening_line`) and the new `##
  Summary` (`replace_body_section`), appends `{"note": str, "status":
  "regenerated"}`. On `compass_client.CompassError`: writes nothing (that
  Thread's existing Summary/opening line left completely untouched),
  appends `{"note": str, "status": "summary_error", "summary_error": str}`,
  and the loop continues to the next Thread rather than aborting the whole
  run — mirrors `tag_backfill.py`'s own per-item honest-failure posture.
  Frontmatter, `## Transcript`, `## Attachments`, and tags are never
  touched on any code path. New `POST /poc/backfill-thread-summaries`
  (`app/api/email_poc_router.py`) — a thin wrapper matching the file's own
  established six-endpoint `/poc/...` shape exactly, returning
  `{"notes_checked": int, "regenerated": int, "results": [...]}`.
  Sequential, one real Compass call per Thread note found in the vault at
  run time — no hardcoded count, no batching/rate-limit infrastructure
  (architect's own resolved posture, matching
  `classify_recent_emails`'/`summarize_attachment`'s own established
  no-rate-limit precedent at this data volume). Verified against a
  throwaway `VAULT_PATH`-overridden scratch vault (real Compass Provider):
  a multi-message Thread and a single-message Thread both regenerated with
  a real synthesized opening line + `## Summary`, frontmatter/`##
  Transcript`/`## Attachments`/tags confirmed byte-for-byte unchanged
  (`AC-03`); the single-message Thread's synthesis was real and sensible,
  not an error/empty/raw-dump fallback (`AC-04`); a scoped, `finally`-
  reverted monkeypatch induced a real `CompassError` for exactly one
  Thread among three — that Thread's own Summary/opening line stayed
  byte-for-byte unchanged with an honest `"summary_error"` result entry,
  while the other two Threads in the same run were genuinely regenerated
  and the endpoint returned its full `results` list without aborting
  (`AC-06`); a non-Thread note (a Meeting note, a Customer OKF concept
  file) was confirmed byte-for-byte unaffected by the same run. Then run
  for real, once, against the operator's actual live `VAULT_PATH` vault's
  2 real pre-existing Thread notes (`Work/Threads/*.md`, excluding the
  non-Thread `test-librarian-t01-scratch-thread.md` scratch file) via the
  already-running real backend — both notes now carry a real,
  Compass-synthesized `## Summary` and opening line, with their
  frontmatter/`## Transcript`/tags confirmed byte-for-byte identical to
  their pre-backfill state (neither had an `## Attachments` section before
  or after). Story `REQ-SB-67-US-01` and `SPRINT-054` complete. Full
  reasoning: `Implementation/Architecture/architecture.md` → "Real Thread
  Summary Synthesis + Opening-Line + One-Shot Backfill"; verification
  evidence:
  `Implementation/Tasks/REQ-SB-67-US-01-T03-thread-summary-backfill.md`.

- fix: `REQ-SB-68-US-01-T01` (`SPRINT-055`) — non-blocking manual
  capture dispatch (`ADR-045` point 1-3), closing the real 2026-08-17
  incident where a manually-triggered "Run Capture Now" froze the ENTIRE
  backend for the full duration of a real capture pass. Grounding
  correction (architect pass): the real blocking call site was
  `agents_router.py::_invoke_capability` (via `trigger_action`/`chat` →
  `skill_registry.invoke_skill` → `_dispatch_skill` →
  `skill_tools.run_capture_now` →
  `email_classification.run_capture_and_record_completion`), fully
  synchronous end-to-end — not `_execute_action`/`_ACTION_HANDLERS`,
  confirmed dead code today for both its entries (left untouched, a
  disclosed housekeeping finding for a future cleanup story). Fix:
  `_invoke_capability` is now `async def`; when `capability_id ==
  "run_capture_now"` it routes through `await
  agent_schedule_registry.dispatch_with_shared_lock(agent_id,
  capability_id, trigger=trigger)` — already `asyncio.to_thread`-wrapped
  (`ADR-037`), the same proven shape `capture_scheduler.py::
  run_capture_if_idle` already uses — instead of calling
  `skill_registry.invoke_skill` directly; every other `capability_id` is
  unaffected (single-id routing branch, not a rewrite). Both real call
  sites (`trigger_action`, `chat`) now `await` it.
  `dispatch_with_shared_lock`'s own `trigger` `Literal` widened to
  include `"chat"` (the chat-triggered manual surface, alongside the
  REST button). The manual path now also joins the shared Outlook-COM
  dispatch lock — closing a real race-condition risk between a manual
  trigger and a concurrent scheduled tick. A new `"skipped"` result
  translation and a `"history_recorded": true` flag were added, closing
  a pre-existing duplicate-history-entry gap for `run_capture_now`
  specifically (one real history entry per run now, not two).
  Live-verified against the real running backend, real Outlook/Compass:
  a genuinely in-flight manual `run_capture_now` no longer blocks a
  concurrent `GET /agents` — over 250 concurrent probes taken across two
  separate real, multi-minute in-flight capture windows, zero failures/
  slow responses; a real dispatch through the same shared mechanism was
  observed completing normally and recording its usual outcome; the
  chat surface and an unrelated capability (`view_last_run`) were
  confirmed unaffected/non-blocking. `MEMORY.md`'s 2026-08-17
  `run_capture_now`-blocking Constraint entry closed out. Full
  reasoning: `Implementation/Architecture/ADR.md` → `ADR-045`;
  verification evidence:
  `Implementation/Tasks/REQ-SB-68-US-01-T01-non-blocking-manual-capture-dispatch.md`.

- feat: `REQ-SB-68-US-01-T02` (`SPRINT-055`) — persisted per-job run-state
  tracking (`ADR-045` point 4): a new sibling store
  `.second-brain/job_run_state.json` via new pure-I/O primitives
  `vault_writer.load_job_run_state()`/`save_job_run_state()`, mirroring
  `load_agent_schedules_state`/`save_agent_schedules_state`'s exact
  shape. Two new `agent_schedule_registry.py` functions,
  `_mark_run_started`/`_mark_run_finished`, wired inside
  `dispatch_with_shared_lock`'s own `async with lock:` block
  (immediately before/after its existing `asyncio.to_thread(...)` call),
  gated structurally to `capability_id == "run_capture_now"` — no
  hardcoded agent-id list at the write side. A genuine failure is
  classified honestly (`"error"` with the real message) vs. the two
  non-failure non-dispatch outcomes (`"pending"`/`"skipped_manual"`,
  mapped to `"skipped"`), never fabricated. New public
  `get_job_run_states() -> list[dict]` read accessor, composed by `T03`,
  enumerates covered agent ids directly from
  `skill_registry._MIGRATION_GRANT_SEED["run_capture_now"]` (the same
  real source `ADR-045` names) — a disclosed, in-scope refinement of
  `ADR-045` point 4's own literal read-side wording (locked by the
  decomposer, not a re-litigation of the write-side mechanism): returns
  exactly one record per covered agent always, with an honest
  `"has_run": false` placeholder (every other field `None`) for a
  covered agent with no persisted run yet, rather than omitting it —
  this is what lets `T04`'s frontend render every covered row with zero
  independent knowledge of which agent ids are covered, never
  re-hardcoding the same 3-agent-id list a second time. `elapsed_seconds`
  for an in-flight run is computed fresh at read time (`now -
  started_at`), never persisted incrementally. Verified: 5 non-AC smoke
  checks (fresh/absent state -> 3 honest `has_run: false` placeholders;
  `_mark_run_started` -> `has_run`/`running: true`/growing
  `elapsed_seconds`, other 2 covered jobs unaffected; `_mark_run_finished`
  success shape -> `running: false`/`last_outcome: "success"`/positive
  `last_duration_seconds`/`elapsed_seconds: None`; a genuine failure
  shape -> `last_outcome: "error"` with the real message verbatim; an
  uncovered agent/capability pair never appears) against a
  `VAULT_PATH`-scratch double vault, confirming no persisted file other
  than `job_run_state.json` was created. Live end-to-end verification
  against the real running backend, real Outlook/Compass, real vault: a
  real `POST /agents/email-capture-pipeline/actions/run_capture_now`
  dispatch was observed transitioning `job_run_state.json` from
  `running: true` (with `elapsed_seconds` growing continuously from
  ~0.17s to ~474s across live polling) to `running: false` with a real
  `last_duration_seconds` (473.95s) and `last_outcome: "success"` once
  it genuinely completed — while the backend stayed fully responsive
  throughout (dozens of concurrent `GET /agents` probes, all fast).
  Full reasoning: `Implementation/Architecture/ADR.md` -> `ADR-045`;
  verification evidence:
  `Implementation/Tasks/REQ-SB-68-US-01-T02-per-job-run-state-tracking.md`.

- feat: `REQ-SB-68-US-01-T03` (`SPRINT-055`) — `GET /system-health`'s
  `system_health.py::get_system_health()` composes `T02`'s new
  `agent_schedule_registry.get_job_run_states()` into a new
  `"scheduling"` key, replacing the retired `"last_capture_run"` key
  (`ADR-045` point 5); no new endpoint, `system_health_router.py`
  unchanged. Dropped the now-unused `vault_writer` import (its only call
  site, `load_last_capture_run()`, is gone). Verified correct in
  isolation (direct calls to `agent_schedule_registry.get_job_run_states()`
  and `mcp_mount_reachable()` both succeed and return the expected
  shape) — **left `status: Blocked`, not `Done`**, because a real,
  pre-existing, unrelated `HTTP 500` on the live `GET /system-health`
  endpoint (confirmed via a real traceback BEFORE any of this task's own
  changes, and unchanged after) blocks end-to-end live verification.
- fix: `BUG` finding (not yet triaged, `status: Open` via `ESCALATIONS.md`
  → `ESC-042` — NOT fixed in this pass, escalated) — `GET /system-health`
  crashes with `HTTP 500` because `.second-brain/agent_providers.json`'s
  `"assignments"` map carries a stale, orphaned `"email-capture"` key
  (the agent was renamed to `"email-capture-pipeline"` by the already-
  `Done` `REQ-SB-55-US-01-T08`/`ADR-043`); `provider_registry.py::
  _load_state()` never prunes stale assignment keys on an agent-id
  rename, so `system_health.py::_providers_with_agent_names()`
  (`REQ-SB-31-US-01`) crashes dereferencing it with no `None`-guard.
  Root-caused via a real traceback, not guessed; left unfixed —
  outside `REQ-SB-68-US-01-T03`'s own declared scope (`Files to Modify`
  and explicit `Out of Scope`), escalated for a human/architect fix-shape
  decision. Full write-up: `ESCALATIONS.md` → `ESC-042`.
- fix: `ESC-042` resolved, 2026-08-17 — direct operator decision (Option
  (a)). `provider_registry.py::_load_state()` gains a symmetric prune
  step: after its existing add-missing-assignment loop, any
  `"assignments"` key whose agent id is no longer in
  `agent_registry.list_agents()` is removed and the state persisted back
  — self-healing reconciliation for any current or future agent-id
  rename, mirroring `working_mode_registry.py`/`background_agent_registry.py`'s
  own established self-healing-default convention. Live-verified against
  the real running backend/vault: the stale `"email-capture": "compass"`
  key was confirmed present in `.second-brain/agent_providers.json`, then
  confirmed pruned automatically the next time `_load_state()` ran
  (triggered by a real `GET /system-health` call) — no manual JSON edit.
  `GET /system-health` now returns a real, live `200` with the exact
  `{"mcp", "providers", "disabled_agents", "scheduling"}` shape;
  `system_health_router.py` confirmed byte-for-byte unchanged. This
  unblocks `REQ-SB-68-US-01-T03` (`SPRINT-055`), whose own 3 non-AC
  smoke checks all passed live once unblocked, including a real
  `"running": true` (growing `"elapsed_seconds"`, sampled repeatedly) →
  `"running": false` (`"last_outcome": "success"`,
  `"last_duration_seconds": 597.1`) transition observed through the
  actual endpoint. `T03` `status: Done`, `gate: clear`. Full evidence:
  `Implementation/Tasks/REQ-SB-68-US-01-T03-scheduling-system-health-extension.md`
  → `## Implementation Log`; `ESCALATIONS.md` → `ESC-042` (`Status:
  Resolved`).

- feat: `REQ-SB-68-US-01-T04` (`SPRINT-055`) — new "Scheduling" section
  on the System Health page (`SystemHealthPage.tsx`,
  `system-health/client.ts`), replacing the former "Last capture run"
  region outright, same position (immediately after the "Providers"
  card) — one `.item-row` per `GET /system-health`'s new `"scheduling"`
  entry (`T03`), showing per covered job whether it's currently running
  (with a freshly-computed elapsed duration), how long its current/most
  recent run took, and its last real outcome (success, a real error
  message, or an honest "no runs yet" placeholder). Reuses
  `.card`/`.badge`/`.badge-success`/`.badge-warning`/`.badge-danger`/
  `.item-list`/`.item-row`/`.mono` verbatim — no new CSS file, no new
  class. Zero client-side hardcoded agent-id list — renders exactly
  `health.scheduling`'s own rows, in the order the API returns them.
  Live-verified against the real running backend/vault/Outlook/Compass:
  a real in-flight `email-capture-pipeline` run showed genuinely growing
  `elapsed_seconds` (`7.97s` → `24.79s`) with concurrent `GET /agents`
  staying responsive (`49-65ms`) and a concurrent second dispatch
  correctly skipped, then completed with a real `580.55s` success
  duration; `meeting-capture`'s real, honest "not yet available"
  on-demand result surfaced as a real failure with its real message
  verbatim, not stale/blank; `todo-capture` showed the honest "no runs
  yet" placeholder, then — via a real, temporary per-agent schedule
  (deleted afterward) firing a genuine `trigger="scheduled"` tick against
  the live `AsyncIOScheduler`, no manual HTTP call — transitioned through
  the identical, trigger-agnostic `dispatch_with_shared_lock` mechanism a
  manual run already uses; `compass-expert`/`build_knowledge` never
  appeared among the 3 covered-job rows. Every rendering branch traced
  against this real live data. **Disclosed: no browser/screenshot tool
  was available this session** (same limitation `REQ-SB-66-US-01-T05`/
  `T07` already disclosed) — verified instead via `tsc -b`/`oxlint` clean
  plus exact-code-match plus live-data-trace; the operator's own stated
  plan is to perform the live-browser confirmation pass personally. `T04`
  `status: Done`, `gate: clear`. **`REQ-SB-68-US-01` story `status:
  Done`** — all 4 tasks (`T01`-`T04`) complete, all 7 locked ACs
  verified; `gate:` stays `flagged` (standing `ADR-045`/trigger-3
  human-review item, unresolved by build completion).
  `SPRINT-055` stays `In Progress` (`BUGFIX-03-US-01`'s own `T01`/`T02`
  remain outstanding in the same sprint). Full evidence:
  `Implementation/Tasks/REQ-SB-68-US-01-T04-scheduling-view-frontend.md`
  → `## Implementation Log`.

- fix: `BUGFIX-03-US-01-T02` (`SPRINT-055`, `BUG-014` gap 2) —
  `vault_writer.py::write_attachments` now requires a `message_segment: str`
  parameter and nests its save path/`relative_link` one level deeper via
  `_slugify(message_segment)` —
  `Work/Threads/attachments/<thread-slug>/<slug-of-received>/<filename>`
  instead of the old flat `attachments/<thread-slug>/<filename>` — so two
  different messages in the same Thread carrying a same-named attachment
  (e.g. recurring `image001.png` signature images) can never silently
  overwrite each other. Both live call sites updated:
  `email_classification.summarize_attachment` passes
  `message_segment=received`; `classify_recent_emails` passes
  `message_segment=email["id"]` (mechanical — already collision-safe by
  construction via its own EntryID-suffixed `note_stem`). The existing
  oversized-attachment `"saved": False` precedent is unchanged.
  Live-verified end-to-end against the real configured vault, one
  continuous session, both locked ACs: no natural same-filename-collision
  email arrived within the window, so used the task's own disclosed Tests
  step 3 substitute — called the real, unmodified `summarize_attachment`
  directly, twice, against a real, already-existing Thread's
  `conversation_id`, with two `image001.png` attachment dicts (identical
  filename, genuinely different content) and two different `received`
  timestamps. Both files saved under distinct nested paths; read back and
  confirmed byte-identical to source and NOT identical to each other (no
  overwrite); the Thread note's `## Attachments` section gained two
  separate dated sub-entries (exercised via the same real
  `append_body_section_line` primitive `thread_match_merge` itself uses).
  A third, distinct-filename attachment confirmed no regression to the
  single-attachment case. The real vault was fully restored to its
  pre-task state afterward. `[BUGFIX-03-US-01-AC-01]` and
  `[BUGFIX-03-US-01-AC-02]`: both PASS. `T02` `status: Done`, `gate:
  flagged` (`ESC-043`, non-blocking — see below).
  **`BUGFIX-03-US-01` story `status: Done`** — both tasks (`T01`, `T02`)
  complete, both locked ACs verified live. `BUG-014` flipped
  `In Sprint → Closed` in both `BUGS.md` and `BACKLOG.md`'s `## Bugs`
  mirror. **`SPRINT-055` `status: Done`** — both of its stories
  (`REQ-SB-68-US-01`, `BUGFIX-03-US-01`) are now `Done`; `gate:` stays
  `flagged` (retro-harvest, the standing `REQ-SB-68-US-01` `ADR-045`
  review, and `ESC-043` below). Full evidence:
  `Implementation/Tasks/BUGFIX-03-US-01-T02-per-message-attachment-nesting.md`
  → `## Implementation Log`.
- discovered (not fixed, `ESC-043`, shared-interface-change,
  non-blocking): verifying `BUGFIX-03-US-01-T02` surfaced a real,
  previously-unconsidered THIRD consumer of `write_attachments`'s old
  flat save-path convention — `app/business/cockpit/attachments.py`
  (Inbox Cockpit, live via `cockpit_router.py`'s attachment endpoints)
  hardcodes the OLD flat `Work/Emails/attachments/<note_stem>/<filename>`
  path when reading back `classify_recent_emails`-sourced email
  attachments. `classify_recent_emails` is still live
  (`/poc/classify-emails`), so any FUTURE capture through that path will
  leave its attachments silently invisible to Cockpit's
  `list_attachments`/`hand_off_attachment_to_chat` (empty/not-found, no
  error). Already-saved historical attachments are unaffected. Left
  unfixed (outside `T02`'s own `## Files to Modify`), per
  `Implementation/Pipeline.md` hard rule 5 — recorded in `ESCALATIONS.md`
  → `ESC-043` and `REVIEW-QUEUE.md`, a `/bug` capture recommended.
