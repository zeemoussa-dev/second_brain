# Architecture

Living description of Second Brain's system as it is today. Update this file as
the architecture evolves — it describes what IS, not what MIGHT BE.

**Last reviewed:** 2026-08-19 (architect pass, `/plan-tasks` step 1,
batched — `REQ-SB-77-US-01`/`REQ-SB-78-US-01`/`REQ-SB-79-US-01`): one new
ADR, [ADR-058](ADR.md), for `REQ-SB-79-US-01` only — the Librarian's single
shared `librarian-housekeeping` identity splits into two real,
independently-schedulable Agent identities, "Threads Cleaning" and
"Company and Partner Building," under the SAME already-existing Librarian
Section; `agent_registry.py` gains its first "retire without delete"
primitive (`retired` flag, `retire_agent`, `list_agents(include_retired=
False)`) so `librarian-housekeeping` can be idempotently retired at every
app start without ever rewriting or orphaning its own already-existing
Pending Approval/Agent History records; `run_housekeeping_pass()` splits
into `run_threads_cleaning_pass()` (the same 4-job fixed order, minus
`backfill_company_folders`) and `run_company_partner_building_pass()`
(wraps `backfill_company_folders()` plus, composing with `REQ-SB-77-US-01`
below, the already-existing `people_extraction.retrofit_people_from_
emails()` self-heal). `REQ-SB-77-US-01` (People Notes retroactively linked
to their real Company/Partner note) and `REQ-SB-78-US-01` (Pending
Approvals grouped/color-coded, with scoped bulk-approve) needed **no new
ADR** — both are pure composition of already-`Accepted` patterns; see
their own "Why no new ADR" notes below. A real, disclosed cross-story task
dependency was found: `REQ-SB-77-US-01`'s own scheduled-self-heal wiring
(Scenario 6b) cannot be built before `REQ-SB-79-US-01`'s new `run_company_
partner_building_pass()` exists — see "People Notes Retroactively Linked
to Company/Partner" below for the full finding. See "The Librarian — Two
Sub-Pipelines," "People Notes Retroactively Linked to Company/Partner,"
and "Pending Approvals — Grouped, Color-Coded Review" below for the full
additions.

**Previously:** 2026-08-19 (`REQ-SB-76-US-01` architect pass,
`/plan-tasks` step 1 — "Company Review — Extract, Classify (Customer/
Partner/Affiliate/Merge), and Batch-Apply"): one new ADR, [ADR-057](ADR.md),
narrowly, additively revising `ADR-009` point 3 only (Partner gains a real
`affiliate_of` field — points 1/2/4/5 unaffected). A new boilerplate-aware
extraction call (`compass_client.extract_thread_companies_for_review`, a
new sibling, never an edit to the frozen, `Done` `detect_customer_for_
thread`) feeds a new `propose_company_review()`/`finalize_company_review()`
Job pair added alongside (not replacing in place) `propose_customer_
backfill`'s own now-superseded-in-practice live usage; ONE `action_id=
"propose_company_review"` Pending Approval carries all five real outcomes
(Customer/Partner/Affiliate/Merge/Decline), resolved via a new additive,
optional decision body on the EXISTING `POST /pending-approvals/{id}/
approve` endpoint (merged into the stored payload before dispatch — zero
signature change to any of the other 8 registered handlers); `migrate_
customer_to_partner`'s real OKF-directory-shape gap is fixed by extending
its own Step 1 (reusing `move_okf_directory` verbatim) while its Step 2 scan
is generalized into a new, parameterized `_retag_company_references` helper
both it AND the new Merge outcome reuse — no third move/retag primitive.
See "The Librarian — Company Review" below for the full addition.

**Previously:** 2026-08-19 (`BUGFIX-08-US-01` architect pass,
`/plan-tasks` step 1, batched — `BUG-029`/`BUG-030`, "Pending Approvals
gain a target-aware dedup check"): one new ADR, [ADR-056](ADR.md).
`pending_approval_registry.create_pending_approval` gains an additive,
optional `dedupe_key: str | None` parameter — a second idempotency check,
alongside (never replacing) `ADR-018` point 2's existing
`trigger == "background"` guard, matching an existing `status ==
"pending"` record on the same `agent_id` + `dedupe_key` regardless of
`trigger`. Closes `BUG-029` (two trigger sources racing for the same
Supervised mutating Skill's decision point — fixed centrally inside
`skill_registry.py::invoke_skill`, zero caller changes needed) and
`BUG-030` (staged-email/Thread routing & classification-failure proposals,
plus `librarian-housekeeping`'s Customer-backfill/archival proposals,
re-proposed as duplicates across repeated ticks — the same gap `ADR-055`'s
own Consequences already disclosed without fixing). See "Agent Working
Modes & Pending Approvals" below for the full addition.

**Previously:** 2026-08-19 (`BUGFIX-07-US-01` architect pass,
`/plan-tasks` step 1 — "Customer/Project `log.md`/`captures.md` carry an
identifying header," `BUG-028`): **no new ADR.** `create_okf_directory_
baseline`/`ensure_okf_directory_baseline` (`ADR-042` point 1's shared
Customer/Project primitive) gain an `identifying_name` parameter and one
shared header-write-or-backfill helper — content-only additions to
`log.md`/`captures.md`'s own creation/top-up logic, reusing the
already-`Accepted` `# {name}` header convention verbatim, touching neither
the 4-file directory shape nor `<slug>.md`'s Glimpse/Background
regeneration isolation guarantee. See "Vault Knowledge Model Redesign"
below for the full addition.

**Previously:** 2026-08-19 (`REQ-SB-75-US-01` architect pass,
`/plan-tasks` step 1 — "The Vault — Real-Data Knowledge Graph Screen"):
**no new ADR.** A new additive `GET /vault-search/graph` endpoint
(`vault_search.get_graph()`, reshaping the SAME `vault_indexing.get_index()`
snapshot `Browse & Search` already reads into `{nodes, edges}`, reusing
`_summary()`/`_kind_for()` verbatim, zero kind-mapping table, zero
pagination/filter params — kind-filter counts/name-search are a
client-side-only concern over the one fetched snapshot); a new
`pages/VaultGraphPage.tsx` at route `/vault`, nav label "The Vault" (direct
reading of the real `Sidebar.tsx` confirms the existing `/browse` item's
own on-screen label is "Browse & Search," never "Vault Browser," so the
PRD's disclosed naming-overlap concern has no real on-screen collision
today; the new screen's own component/feature names are still chosen
distinct from `VaultBrowserPage`/`vault-browser` at the code level); and a
new, zero-new-dependency `<canvas>`+`requestAnimationFrame` hand-rolled
force-directed renderer (`VaultGraphCanvas.tsx`/`forceLayout.ts`),
confirmed against the real `package.json` that no graph/visualization
library exists today and none is added. Every decision is a pure
composition of already-`Accepted` `ADR-003` (layering) and `ADR-010`
(frontend routing/styling/data-fetching/no-speculative-dependency
conventions) — neither is reopened. See "The Vault — Knowledge Graph
Screen" below, appended directly after the "Tag/Folder Scope Suggestions"
subsection of "Browse & Search."

**Previously:** 2026-08-19 (`REQ-SB-73-US-01`/`REQ-SB-74-US-01` architect
pass, `/plan-tasks` step 1, batched — Bidirectional Thread ↔ Message Linking
and Customer Backfill): two new ADRs. `ADR-054` (`REQ-SB-73`) — a new
`link_thread_messages()` Librarian Job (`## Messages` + `thread:` backlink,
regenerated/self-healed via already-shipped `insert_body_section_if_missing`/
`replace_body_section`/`upsert_frontmatter_key`, zero new `vault_writer.py`
primitives), a bounded `rename_threads()` fan-out extension for a
zero-staleness-window guarantee (extends `ADR-049` Decision 2), and — found
independently, not named by the story — a `vault_indexing.py` extension so
`outgoing_wikilinks` also scans frontmatter string values, not body text
alone, closing a real gap that would otherwise have made the story's own
"already-shipped backlinks panel/graph view surfaces this automatically"
premise false. `ADR-055` (`REQ-SB-74`) — confirms, by direct reading, that
the batched-per-Customer multi-target Pending Approval shape needs ZERO
change to `pending_approval_registry.py`/`pending_approvals_router.py` (an
opaque `payload` dict was already fully generic); a new `compass_client.
detect_customer_for_thread` (narrower sibling of `classify_task`); a new
`vault_writer.list_customer_folders()` enumeration; and a new generic
`vault_writer.move_okf_directory()` cross-parent archival-move primitive
(`Work/Archive/Customers/` already provisioned, `REQ-SB-70-US-01`). See "The
Librarian — Bidirectional Thread ↔ Message Linking" and "The Librarian —
Customer Backfill" below, both appended directly after "`process_staged_
email` Retargeted onto Stage 1/Stage 2 Composition."

**Previously:** 2026-08-19 (`BUGFIX-06-US-01` architect pass, `/plan-tasks`
step 1 — "Meeting Cockpit resolves plain wikilink-string attendees to real
Person info instead of 500ing (`BUG-027` fix)": no new ADR — the fix
composes two already-`Accepted`, already-live primitives at a second call
site (`vault_writer.py`'s existing wikilink-stripping regex, promoted from
private `_WIKILINK_PATTERN` to public `WIKILINK_PATTERN` per this project's
own "promote a private `data_access` helper to public the moment a second
layer needs it" pattern, `MEMORY.md`; and `vault_indexing.get_index()`'s
existing stem-keyed lookup, the same one `resolve_people_chips` already
performs for the subject note itself) — no new tool, framework, or
layering boundary. Also corrects a stale architectural claim: Meeting
`attendees` was documented (REQ-SB-54 section, below) as sharing Email
`recipients`'s JSON-encoded `list[dict]` string shape; direct reading of
`meeting_classification.py`'s real, current write path confirms Meeting
`attendees` has always actually been written as a plain `list[str]` of
wikilinks — that claim never matched Meeting's real, shipped behaviour.
See "Meeting & Inbox Cockpits" → `people.py` extended bullet, and the
correction bullet appended after the REQ-SB-54 "OKF nested actor-
provenance" bullet, both below.

**Previously:** 2026-08-19 (`BUGFIX-05-US-01` architect pass, `/plan-tasks`
step 1, re-opened AGAIN to resolve `ESC-056` — `T04`'s own live
verification of `AC-01` found that `ADR-052`'s migration mechanism, though
a correct, lossless shape migration on its own, does not survive being
composed with `synthesize_thread` in the SAME pipeline tick: a
freshly-migrated flat Thread's `messages/` starts empty, so the very next
`synthesize_thread` call regenerates `## Summary` by full reconstruction
from just the one new message, silently overwriting the flat note's own
real, substantive pre-migration Summary. One new `ADR-053`: a one-time,
self-consuming `pre_migration_summary.md` sidecar file —
`migrate_flat_thread_to_directory` writes the flat note's pre-migration
`## Summary` to it (verbatim, outside `messages/`, so it never pollutes
classification/participants/message-count); `synthesize_thread` folds it
into its SAME existing Compass call as prior-history grounding, then
renames it in place to `pre_migration_summary.consumed.md` on success
(archive-not-delete, never fed twice). Confirmed by direct reading that
`## Summary` is the only at-risk section; does not reopen `ADR-048`'s own
"full reconstruction, never a rolling/incremental delta" design — this is
a narrow, one-time exception for genuine pre-migration history, not a
standing rolling-context mechanism. See "Migration content-preservation —
the `pre_migration_summary.md` sidecar" below, appended directly after
"Legacy flat-shape Thread recognition — self-healing migration on first
touch."

**Previously:** 2026-08-19 (`BUGFIX-05-US-01` architect pass, `/plan-tasks`
step 1, re-opened to resolve `ESC-055` — the decomposer's own same-day
finding that `ADR-051`'s composed-function rewire alone does NOT close
`AC-01`, `BUG-026`'s duplication facet: one new `ADR-052`, narrowing
`ADR-049` Decision 1's own "purely read-only" framing for one case only —
`resolve_thread_directory()` gains a second scan tier recognizing a
legacy, pre-redesign FLAT `Work/Threads/<name>.md` Thread note (which
`list_thread_notes()`'s own directory-shaped-only glob structurally cannot
see) and migrates it, self-healing and one-time, to the standard directory
shape via a new `migrate_flat_thread_to_directory` primitive before
returning it — confirmed necessary, not just sufficient, by direct reading
of `synthesize_thread`'s own update-branch code, which would otherwise
silently share ONE `messages/`/`files/` folder across every unmigrated flat
Thread. Does NOT retroactively fix the one already-diverged, already-live
duplicate found (`conversation_id ED0954959F6F4A4C88F9E2ACA3D7113A`) — by
design; that is a separate, deferred data-remediation decision, recommended
for the Librarian's own future housekeeping scope, not this story (see
`ESC-055`'s resolution note). See "Legacy flat-shape Thread recognition —
self-healing migration on first touch" below, appended directly after
"Thread lookup — frontmatter-based, again."

**Previously:** 2026-08-19 (`BUGFIX-05-US-01` architect pass, `/plan-tasks`
step 1 — "`process_staged_email` retires legacy `thread_match_merge` so
Threads no longer duplicate or orphan on new messages (`BUG-026` fix)": one
new `ADR-051`, partially superseding `ADR-043` points 1 and 3 (the
live-execution/topology halves only) — `process_staged_email`'s own
underlying implementation (`email_capture_pipeline.run_email_capture_
pipeline`, same name/module/zero-arg call shape, `skill_tools.py`
untouched) is retargeted from invoking the module's compiled `StateGraph`
(and, through it, the still-buggy `thread_match_merge`) onto a plain,
sequential composition of Stage 1 (`capture_raw_thread_messages`) + Stage 2
(`synthesize_thread`) — both already-shipped, already-correct (`REQ-SB-71-
US-02`) — with the old graph's three OTHER real branch effects that have no
equivalent anywhere in the `REQ-SB-71`/`REQ-SB-72` redesign
(`detect_recurring_pattern`, `consult_librarian`, `project_customer_
synthesizer.resync_project_from_thread`) explicitly re-composed as direct
calls in that same new function, never re-implemented; `summarize_
attachment`'s own old role needs no equivalent — it is already superseded
by the Files/OKF companion mechanism. `email_capture_pipeline.py`'s
`StateGraph`/`get_job_tree()`/`thread_match_merge` are DEPRECATED, not
deleted — kept only for `get_job_tree()`'s own read-only Pipeline Job Tree
introspection (`REQ-SB-65-US-01`), a real, disclosed, now-known-stale
visualization surface (out of this bugfix's own scope to rebuild). Closes
`ESC-048`/`ESC-050`/`BUG-026`; `email-capture-pipeline`'s working mode
flips `supervised → autonomous` once verified live (`T02`). See
"`process_staged_email` Retargeted onto Stage 1/Stage 2 Composition"
below, appended directly after "The Librarian Section — First Housekeeping
Pipeline."

**Previously:** 2026-08-19 (`BUGFIX-04-US-01` architect pass, `/plan-tasks`
step 1 — "Cockpit chat correctly addresses agents, sends on Enter, updates
live, and renders rich text (BUG-022/023/024/025 fix)": one new `ADR-050`
(`react-markdown`, a shared `ChatMessageText.tsx` component, and a
default-safe, no-raw-HTML sanitization posture — the first real delivery of
`REQ-SB-32`, never actually spec'd/built before this pass, per this same
story's own `ESC-053` finding); three further fixes composing already-
`Accepted` mechanisms with no new ADR — `threads.py::send_user_message`
gains an optional `addressed_agent_ids` parameter/request-body field so an
`@mention`ed message dispatches only to the mentioned agent(s) (reusing
`REQ-SB-49-US-01`'s existing frontend mention resolution as the addressing
signal, never a second parser), `Cockpit.tsx`'s chat input becomes a real
`<form onSubmit>` mirroring `AgentDetailPanel.tsx`'s own working precedent,
and a `sending`/typing-dot pending-state UI plus reuse of the send
response's own already-returned thread data replace the previous silent
post-send `reload()` (no SSE/polling/websocket introduced or needed — the
existing synchronous per-request Cockpit dispatch already returns full
post-turn state). See "Cockpit Chat — Addressed-Reply Dispatch,
Send-on-Enter, and Pending-State Live Update" and "Chat Rich-Text
Rendering — `react-markdown`" below, both appended directly after "Cockpit
Person-Directed Instruction."

**Previously:** 2026-08-18 (`REQ-SB-72-US-01` architect pass, `/plan-tasks`
step 1 — "The Librarian Section — First Housekeeping Pipeline": new `ADR-049`,
partially superseding `ADR-048` Decision 3's own "resolve_thread_note_path
stays a deterministic existence check, permanently" sub-decision only (every
other part of Decision 3 — Thread stays directory-shaped, permanently keyed by
`conversation_id`, Stage 1/Stage 2 split, write-once raw messages — is
unaffected) — a new "Librarian" Section/`librarian-housekeeping` Agent (via
the EXISTING, unmodified `section_registry.create_section`/`set_agent_section`
mechanism, `REQ-SB-18`/`ADR-014`) housing this project's first autonomous,
SCHEDULED housekeeping pipeline (a real, disclosed, deliberate reversal of
`REQ-SB-70`/`REQ-SB-71`'s own standing no-scheduler constraint), reusing the
EXISTING `app/api/email_poc_router.py` for five new operator-triggerable
endpoints; a new shared `resolve_thread_directory()` primitive retargets
`resolve_thread_note_path`/`raw_message_note_path` back to a frontmatter-based
scan over `list_thread_notes()` (the THIRD swing of this project's own Thread-
matching mechanism: `ADR-046` frontmatter-scan → `ADR-048` deterministic-path
→ now back to frontmatter-scan, justified by real steady-state capture volume,
~10 emails/hour, cheap enough to scan; bulk/retrofit operations may still
compose the deterministic path directly), letting a new whole-directory
`rename_thread_directory` primitive rename a Thread to a human-readable
`<date> <subject>` name with `messages/`/`files/` moving atomically, byte-for-
byte unchanged, and the `<slug>/<slug>.md` invariant preserved; a new Files/
OKF backfill Job (reusing `write_file_companion` unchanged) plus a new,
structured `## Files` body section; `## Related` ownership transfers wholesale
from `email_classification.synthesize_thread` (its own allow-list entry
narrowed to `## Summary` alone, in the SAME change that registers the
Librarian's own new entry — never both simultaneously) to a new Librarian Job
populating real Person/Company wikilinks; a new company-mention-detection
Compass call (technique-only reuse of `compass_client.summarize_content`,
never `determine_placement_and_file` itself — a different-shaped problem),
re-checked in Python against live `known_customers`/`known_partners` before
ever auto-creating (`ensure_customer_hub_note`, unchanged) or proposing a new
Pending Approval (`propose_librarian_company_link`, mirroring `REQ-SB-63`'s
own `_create_cross_cutting_proposal`/`finalize_cross_cutting_update` shape).
A real, newly-discovered, ESCALATED consequence against the still-live,
`supervised`-only `thread_match_merge` pipeline (`ESC-048`) is disclosed, not
fixed, by this pass — see `ADR-049` Consequences and `ESCALATIONS.md` →
`ESC-050`. See "The Librarian Section — First Housekeeping Pipeline" below,
appended directly after "Vault Base Provisioning + Redesigned Email/Meeting
Capture."

**Previously reviewed:** 2026-08-18 (`REQ-SB-70-US-01`/`REQ-SB-71-US-01/-02/-03`
architect pass, `/plan-tasks` step 1 — "Vault Base Provisioning +
Redesigned Email/Meeting Capture": new `ADR-048`, covering all four stories
in this batch as one coherent redesign — a new idempotent `app/business/
vault_provisioning.py` (mirrors `vault_migration.py`'s own module shape,
NOT a migration — no archive, no wipe); a new, composed-alongside `app/
data_access/section_ownership.py` giving `vault_writer.replace_body_
section` a real, code-enforced, required `caller` keyword parameter checked
against a hand-maintained per-caller allow-list, with human-owned headers
(`## Personal Notes`/`## Actions`) unconditionally, structurally
unwritable by any caller regardless of that caller's own registered
allow-list; Thread becomes a directory (`Work/Threads/<slug-of-
conversation_id>/`, permanently deterministic — reverting `ADR-046`
Decisions 6/7's human-readable/renamable filename mechanism, no longer
needed once the human-readable identity lives in frontmatter instead of
the directory name) holding an immutable, write-once raw message note per
email under `messages/` plus a distilled concept file (`## Summary`/
`## Personal Notes`/`## Actions`/`## Related`); two new, independently-
triggerable, no-shared-lock capabilities (`capture_raw_thread_messages`,
zero-Compass; `synthesize_thread`, Compass-backed) of the EXISTING
`email-capture-pipeline` Agent-tier identity, composed together by the
EXISTING scheduled `pull_email`/`process_staged_email` capability ids
(no new scheduler wiring); a new, generic `files/`-companion primitive
(renamed from `attachments/`) giving every captured file its own
OKF-lite note; Meeting's one-time/recurring split reuses the EXISTING
`/poc/classify-meetings` endpoint (no new endpoint), recurring series
keyed by `GlobalAppointmentID`, raw invite boilerplate parsed transiently
for `teams_link`/`dial_in` then discarded, never persisted; Person notes
retargeted to nest under their primary Customer
(`Work/Customers/<slug>/People/<slug>.md`), a second, narrow extension of
`ADR-004`'s folder-vs-tag boundary for Person only, with a vault-wide
`find_person_note_path` lookup so an already-existing note is reused
(never duplicated/moved) and a name-derived dedup key closing
`meeting_classification.py`'s own silent no-email-attendee skip,
falling back to the existing flat `Work/People/` location when no
Customer match exists (operator-confirmed 2026-08-18); and a generalized,
fully recursive `vault_writer.list_all_note_paths()` replacing three
hardcoded globs with one bounded scan. See "Vault Base Provisioning +
Redesigned Email/Meeting Capture" below, appended directly after "Vault
Migration."

**Previously reviewed:** 2026-08-18 (`REQ-SB-59-US-01` architect pass,
`/plan-tasks` step 1 — "Full Vault Migration to the New Knowledge Model":
new `ADR-047` — a new one-time-migration module,
`app/business/vault_migration.py` (fifth instance of the existing
`tag_backfill.py`/`vault_restructure.py`/`partner_hub_linking.py`
retrofit-module precedent), introduces this project's first
archive-not-delete pattern (`.second-brain/migration_backup/
<run-timestamp>/`) built entirely from the already-`Accepted`, unmodified
`vault_writer.move_note_and_attachments` primitive; resolves `ESC-046`
(the legacy-flat-vs-OKF-directory Customer filename-stem collision) as a
direct, in-scope consequence of Customer note regeneration rather than a
separately deferred bugfix; reuses `project_customer_synthesizer.
synthesize_customer`'s existing `detect_customer_durable_fact`/Pending-
Approval gate unmodified for pre-migration content, deliberately never a
migration-only auto-write bypass; reuses existing, already-parametrized
Outlook-COM read functions (`list_recent_mail`/`list_calendar_events`)
with operator-supplied large history-window values instead of inventing a
new "full history" primitive. See "Vault Migration — One-Time Full Vault
Migration to the New Knowledge Model" below, appended directly after
"Project & Customer Synthesizer."

**Previously reviewed:** 2026-08-18 (`REQ-SB-58-US-01` architect pass,
`/plan-tasks` step 1 — "Customer/Project-Aware Expert (Glimpse-First
Answers)": extends `vault-qa` with a new `app/business/
glimpse_first_qa.py` business module plus one new, `vault-qa`-gated
`graph.py` node (`retrieve_memory -> glimpse_first_context -> call_model`)
that reuses `vault_search.search()` (`ADR-026`) for entity resolution
(rank-1-result-only, zero new matching logic), resolves the matched
Customer/Project's own OKF concept-file path directly from the search
index (`ADR-024`), and injects both `## Glimpse` and `## Background`
(`vault_writer.read_body_section`, `ADR-042` point 2) as one `SystemMessage`
ahead of the model call — no durable-vs-current-status classifier
invented; `## Background` structurally carries every durable fact,
`## Glimpse` structurally carries only current status, by `ADR-042`'s
own already-decided split. Evidence drill-down (Scenario 3) needs no new
tool — `vault-qa`'s existing `retrieve_notes_in_agent_scope` (`REQ-SB-29`)
stays the sole raw-evidence path, correlated via the Glimpse's own
already-embedded `[[wikilink]]` stems; a new ungated "read any note"
tool was considered and rejected as a deviation from `REQ-SB-29`'s own
scope-enforcement boundary. `REQ-SB-33`'s grounding instruction
(`state.py::history_entries_to_messages`) gains one additive clause
naming this new context source, mirroring `REQ-SB-66`/`ADR-044`'s own
"additive extension, no ADR" precedent. **No new ADR** — every composed
primitive (`ADR-015`/`ADR-024`/`ADR-026`/`ADR-042`) is unmodified in its
own contract, and no new MCP tool is registered. See "Glimpse-First
`vault-qa` Answers" below, appended directly after "File upload, Compass
summarization & Vault Filing Expert handoff."

**Previously reviewed:** 2026-08-17 (`REQ-SB-69-US-01` architect pass,
`/plan-tasks` step 1 — "Decoupled Email Pull + Human-Readable,
Graph-Connected Thread Notes": new `ADR-046`, superseding `ADR-043`
points 2 and 7 and `ADR-042` point 5 only — `Fetch` retired from the
pre-graph batch step, replaced by an independently-dispatched,
incrementally-staged `pull_email` capability writing to a new
`.second-brain/email_staging/` store, plus a second, Outlook-lock-free
`process_staged_email` capability; Thread filenames become
human-readable/collision-safe via a frontmatter-scan lookup (no
persisted index); a real, previously-latent Pending-Approval
stale-path gap (found by direct reading, not assumed) is fixed
alongside it; dates split into a machine-parseable/human-readable
sibling pair; a new, deterministically-regenerated `## Related` body
section carries honest Customer/Person/Project wikilinks. See
"Decoupled Email Pull + Human-Readable, Graph-Connected Thread Notes"
below, appended directly after "Non-Blocking Manual Capture Dispatch +
Scheduling Monitor."

**Previously:** 2026-08-17 (`BUGFIX-03-US-01` architect pass, `/plan-tasks`
step 1 — "Thread attachment capture and collision safety (BUG-014 fix)":
resolves `ESCALATIONS.md` → `ESC-041`'s own open contradiction between
`BUG-014`'s stated gap-1 root cause ("`outlook_com.py` never reads a
`MailItem`'s `Attachments` COM collection at all") and the real, current
code — `_extract_attachments`/`list_recent_mail` already populate a real
`"attachments"` key on every email, confirmed false, not newly disputed
here. Direct re-reading of the LIVE `Summarize-Attachment` Job chain
(`email_capture_pipeline.py`'s `_summarize_attachment_node` →
`email_classification.summarize_attachment` →
`vault_writer.write_attachments`) finds the REAL, confirmed mechanism: an
attachment that isn't saved (oversized, over `outlook_com.py`'s 20MB
`_MAX_ATTACHMENT_BYTES` cap) or can't be summarized collapses to a
`summary_error` the pipeline node silently discards — no `## Attachments`
line is ever appended, and for the oversized case specifically,
`write_attachments`'s own `.mkdir()` call is never reached, so the
attachments folder itself never comes into existence — a single mechanism
that independently explains BOTH of `BUG-014`'s own live-observed
symptoms (missing `## Attachments` section AND missing `attachments/`
folder) with no unverifiable assumption about Outlook's own COM behavior.
Corroborated by direct comparison against the still-live sibling
`classify_recent_emails` path, which already carries an honest
"not saved — exceeds the size cap" fallback line the new Thread pipeline
never inherited. **No new ADR** — a bugfix within `ADR-043`'s
already-`Accepted` Job/Pipeline shape, restoring an already-established
honest-signal convention and mechanically extending `write_attachments`,
not a new tool/framework/structural boundary. `ESC-041` marked
`Resolved` (this pass's own finding is the resolving artefact); one
residual, non-blocking live-diagnostic item (which exact real-world cause
applied to the ONE already-captured historical Thread — oversized cap
vs. a OneDrive/SharePoint cloud-attachment link vs. a stale-dedup
timing artifact from `SPRINT-049`'s own build-out) is folded into `T01`'s
own scope for the coder to confirm live, mirroring
`REQ-SB-56-US-01-T00`'s own precedent — it does not change the fix's
design, only which of several already-covered honest-signal paths fires
for that one historical note. See "Thread Attachment Capture —
Silent-Loss Fix + Per-Message Collision Safety" below, appended directly
after "Real Thread Summary Synthesis + Opening-Line + One-Shot Backfill."

**Previously:** 2026-08-17 (`REQ-SB-68-US-01` architect pass,
`/plan-tasks` step 1 — "Non-blocking manual capture dispatch + a real
Job/Scheduling monitor on System Health": corrects a material grounding
error found by direct re-reading of the REAL current
`agents_router.py`/`skill_tools.py`/`skill_registry.py` (the story's own
Context named `_execute_action`/`_ACTION_HANDLERS` as the live blocking
call site; that path is actually confirmed-dead code today — both of its
only two entries are also `skill_tools.SKILLS` members, so every real
caller branches away from it before it is ever reached). The REAL manual
`run_capture_now` dispatch path (`_invoke_capability` →
`skill_registry.invoke_skill` → `_dispatch_skill`, fully synchronous, no
thread offload) is rerouted through `agent_schedule_registry.
dispatch_with_shared_lock` — an already-`Accepted` (`ADR-037`),
already-proven mechanism that gains the fix its own non-blocking dispatch
AND the shared Outlook-COM lock in one stroke, closing `ADR-037`'s own
stated-but-unachieved "every real trigger source" goal. A new sibling
`.second-brain/job_run_state.json` store (composed via `vault_writer.py`,
written from inside `dispatch_with_shared_lock`) backs a new
`"scheduling"` key on the existing `GET /system-health`, which replaces
`SystemHealthPage.tsx`'s existing "Last capture run" region outright (not
coexisting with it) with a richer per-job Scheduling section for the
three capture-style jobs `agent_schedule_registry`'s shared lock already
covers. **New ADR** — `ADR-045` — MUST-FLAG trigger 3 fired;
`gate: flagged`, `REVIEW-QUEUE.md` entry added. See "Non-Blocking Manual
Capture Dispatch + Scheduling Monitor" below, appended directly after
"Universal Prompt Override + Guardrails Placeholder."

**Previously:** 2026-08-17 (`REQ-SB-67-US-01` architect pass,
`/plan-tasks` step 1 — "Real Thread Summary Synthesis + Opening-Line +
One-Shot Backfill": adds exactly ONE new real Compass call inside the
already-existing `thread_match_merge` Job (no new Job, no new graph
node/edge — `email_capture_pipeline.py`'s compiled `StateGraph` topology
is completely unchanged), reversing a story-level (not ADR-level)
Constraint from the already-`Done` `REQ-SB-55-US-01`'s own text via a new
story, per `Implementation/Pipeline.md` hard rule 1. **No new ADR** —
confirmed by direct re-reading, `ADR-043`'s own seven numbered Decision
points never assert "this Job never calls Compass" as an architectural
rule themselves; that was purely `REQ-SB-55-US-01`'s own story-level
scoping text. This pass also extends `ADR-044`'s own already-`Accepted`,
self-anticipated Consequence — `thread_match_merge` gains a real Compass
call site for the first time, so its Job-Settings `GET` response's
hand-maintained Prompt-omission exclusion set shrinks from
`{"thread_match_merge", "detect_recurring_pattern"}` to
`{"detect_recurring_pattern"}`, a mechanical update that ADR's own
Consequences already named verbatim. `gate: clear` — no MUST-FLAG
trigger fired. See "Real Thread Summary Synthesis + Opening-Line +
One-Shot Backfill" below, appended directly after "Pipeline Job Tree
Visualization."

**Previously:** 2026-08-16 (`REQ-SB-66-US-01` architect pass,
`/plan-tasks` step 1 — "Universal Prompt Override + Guardrails
Placeholder — Agents and Pipeline Jobs": resolves the story's own
genuinely-open Job-Settings-detail-view data-source question as
**Option A — a new, dedicated `GET`/`PATCH
/agents/{agent_id}/jobs/{job_id}/settings` pair, paired with a
genuinely separate, minimal frontend shell — never a widening of
`agents_router.py`'s Agent-detail resolution or `AgentDetailPanel.tsx`'s
shared tab machinery.** **New ADR — `ADR-044`** (`gate: flagged`,
trigger-3): this is a genuine, material narrowing of `ADR-041`'s own
deferred "whether/how a Job earns its own surface" Consequence and
`ADR-043` point 6 ("Jobs stay non-addressable in every respect"), not
pure-read/zero-boundary-change the way `REQ-SB-65-US-01`'s own,
structurally similar Option A/B choice was — a Job becomes clickable AND
its Settings become editable/persisted for the first time, and
`AgentDetailPanel.tsx`'s real, current tab set has no existing
tab-REMOVAL mechanism to reuse (confirmed by direct reading, a
correction of the story's own Option B framing). A REVIEW-QUEUE pointer
was written; the decomposer still runs. See "Universal Prompt Override +
Guardrails Placeholder — Agents and Pipeline Jobs" below, appended
directly after "Pipeline Job Tree Visualization."

**Previously:** 2026-08-16 (`REQ-SB-65-US-01` architect pass,
`/plan-tasks` step 1 — "Pipeline Job Tree Visualization": resolves the
story's own genuinely-open, `/spec`-flagged (trigger-8) data-source
question as **Option A — a new, read-only endpoint that inspects the
real, compiled `email_capture_pipeline.py` `StateGraph`'s own structure,
via `langgraph`'s own already-installed, already-public `Pregel.get_graph()`
introspection API, confirmed by direct reading of the installed package
(`langgraph==1.2.11`), not assumed.** Jobs stay fully non-addressable —
`ADR-043` point 6 stays intact, not reopened. **No new ADR** — a new READ
path over an already-compiled object, inside `ADR-043` point 1's own
already-established module boundary, returning data through the
already-established `api → business` layering (`ADR-003`), reusing
`layoutAgents.ts`'s already-built, already-generic tree/dependency-edge
layout math with zero changes to it. See "Pipeline Job Tree Visualization
— read-only `StateGraph` introspection" below, appended directly after
"Email Capture & Threading Pipeline — First Concrete Pipeline." `gate:
flagged` (trigger-1, material assumption — the concrete endpoint route/
response shape and the frontend merge/adapter strategy were not specified
by the story/PRD, both explicitly left "for the architect to confirm";
this pass designed and verified them; a REVIEW-QUEUE pointer was written)
— the decomposer still runs.)

**Previously:** 2026-08-16 (`REQ-SB-63-US-01` architect pass,
`/plan-tasks` step 1 — "The Librarian": generalizes the already-`Done`
`vault_filing_expert.py`/`ADR-021` from one caller (chat-uploaded
attachments) into a plain function any business-layer module already
composes, confirmed by direct inspection of three real existing call sites,
plus one new caller (a `REQ-SB-55` Pipeline Job) and one new decision
outcome (cross-cutting-update detection). **No new ADR** — every piece is a
parameter-additive extension of `ADR-021` point 5's own already-`Accepted`,
already-self-anticipated Tier-2-shaped dispatch pattern, plus `ADR-004`'s
already-`Accepted` tag idiom for the deferred write itself (an additive
`customer/<slug>`/`partner/<slug>` tag, never `captures.md`, never a new
evidence file). See "The Librarian — Vault Filing Expert generalized to a
Pipeline-Job caller + cross-cutting-update detection" below, and the
amendment note appended to "Email Capture & Threading Pipeline — First
Concrete Pipeline"'s own Fork/merge-shape bullet (a new, seventh,
`consult_librarian` branch Job). `gate: flagged` (trigger-1, material
assumption — the concrete shape of "the deferred cross-reference write"
was not specified by the story/PRD; a REVIEW-QUEUE pointer was written) —
the decomposer still runs.)

**Previously:** 2026-08-16 (`REQ-SB-55-US-01` architect pass,
`/plan-tasks` step 1, `ADR-043` — the first concrete Pipeline built under
`ADR-041`'s directional taxonomy: a new `app/business/pipelines/` subpackage
(`email_capture_pipeline.py`) owns a `langgraph.graph.StateGraph` compiled
from `Classify`→`Thread-Match/Merge`→`Route-to-Project` plus two branch Jobs
(`Summarize-Attachment`, `Detect-Recurring-Pattern`), run once per fetched
email (`Fetch` itself stays a pre-graph, per-tick batch step); every Job's
real logic stays a plain, LangGraph-ignorant function in
`email_classification.py`, composed — not reimplemented — from the existing
`outlook_com`/`compass_client` calls. Mid-pipeline human approval (Scenario
3/5) is resolved as a flat-JSON Pending-Approval-payload deferred write via
`pending_approvals_router.py`'s existing `_APPROVAL_HANDLERS` table — never a
LangGraph checkpointer suspension — concretely closing `ADR-041`'s own
left-open "checkpointer durability" question for this Pipeline. One new
Agent-tier identity (`type: "worker"`) replaces `email-capture` 1:1 in
`agent_registry.py`; none of the six Jobs get their own registry entry, Map
node, or Working Mode, closing `ADR-041`'s own "does a Job earn its own
surface" question the same way: it doesn't, here. Thread's own baseline
frontmatter (`ADR-042` point 5) gains `customer`/`project`, plus
`participants`/`last_message_at` — claiming, on `REQ-SB-56`'s behalf, the
field-ownership decision that section's own Notes left flagged for
whichever story's decomposer reached it first. See "Email Capture &
Threading Pipeline — First Concrete Pipeline" below, and the amendment note
appended to "Meeting → Thread Linking", below. `gate: flagged` (trigger-3,
`ADR-043` human review) — the decomposer still runs.)

**Previously:** 2026-08-16 (`REQ-SB-56-US-01`/`REQ-SB-57-US-01` architect
pass, `/plan-tasks` step 1 — no new ADR for either, both extend
[ADR-042](ADR.md) as parameter choices within its already-Accepted data
model, not new architectural boundaries. Proposes concrete, buildable
answers to the two open trigger-8 judgement calls the analyst pass
explicitly left for the architect: (1) `REQ-SB-56`'s Meeting→Thread
fallback-link thresholds — attendee-overlap (≥2 shared attendees, or 1
shared attendee when it's the entirety of the smaller side's list) AND
date-range proximity (meeting start within 7 days of the Thread's own
most recent message), both self-excluded and both required together,
grounded in this vault's own real observed thread cadence; requires two
new, purely additive Thread frontmatter fields (`participants`,
`last_message_at`); (2) `REQ-SB-57`'s "genuinely concludes" History-line
bar — a concrete Project `status` enum (`active|on_hold|won|lost|renewed`)
and a transition-based trigger (`log.md` gains a line only on a
transition INTO `won`/`lost`/`renewed`, never on `active`/`on_hold`).
**Both proposals are recorded as PROPOSALS awaiting operator confirmation
in their own stories' `## Notes` — neither gate is cleared by this pass.**
See "Meeting → Thread Linking — ConversationID Primary Strategy,
Attendee-Overlap/Date-Proximity Fallback" and "Project & Customer
Synthesizer — the 'genuinely concludes' History-line bar", both below.)

**Previously:** 2026-08-16 (`REQ-SB-54-US-01` Vault Knowledge Model
Redesign architecture pass, ADR-042 — `Work/Threads/` (one note per
Outlook `ConversationID`, full-regeneration-on-every-update) replaces
per-email notes; Customer AND Project each become a small OKF v0.2-
conformant DIRECTORY (`index.md`/`<slug>.md`/`log.md`/`captures.md`),
Project nested one level inside its own Customer's directory (operator-
confirmed, `ESC-037` Resolved); a new header-scoped `replace_body_section`
primitive replaces the fixed-byte-offset `insert_body_line_if_missing`
for anything meant to regenerate (a concept file's own Glimpse/Background
sections, a Thread's own Summary section); OKF's nested `generated`/
`verified` actor fields reuse the already-`Accepted` JSON-encoded-string
frontmatter convention (`ADR-036` point 7's `recipients`/`attendees`
precedent), extended from list-of-dicts to a single dict; extends, does
not reopen, `ADR-004`'s "Customer is a tag, never a folder level" rule —
see "Vault Knowledge Model Redesign — Threads, Manual Captures, OKF-
Conformant Customer & Project Directories", below. **Flagged consequence
for whoever picks up `T04`/`T05`:** `list_all_note_paths()`'s current
one-level `Work/*/*.md` glob cannot discover the new two-levels-deep
directory shape — needs an explicit recursion extension, see that
section's own Consequences note.)

**Previously:** 2026-08-15 (ADR-041 — Agent/Pipeline/Job/Hub domain-model
taxonomy adopted, direct operator-driven discussion, not a single
requirement's own `/plan-tasks` pass: a Pipeline is now a user-extensible
DAG of lightweight Jobs, executed on LangGraph, authored via a native
React Flow builder — see "Agent / Pipeline / Job / Hub Domain Model —
Taxonomy" near the top of this file. Supersedes the REQ-SB-53 Capture
Pipeline Split pass immediately below this entry — that section is now
marked SUPERSEDED in place, kept for historical record only.)

**Previously:** 2026-08-15 (REQ-SB-53-US-01/US-02/US-03 Capture Pipeline
Split architecture pass, ADR-040 — Email/Meetings/To-Do capture split into
Pull/Tag/Link/Store agent stages behind a new shared, capture-type-agnostic
`app/business/capture_pipeline.py` orchestration engine; see "Capture
Pipeline Split — Pull/Tag/Link/Store Agent Stages" below, now marked
SUPERSEDED by the ADR-041 pass above. Superseded footer text from the
prior review retained beneath it — see that section for the ADR-039 pass.)

**Previously:** 2026-08-14 (REQ-SB-46-US-01 Agent Creation Wizard
Redesign architecture pass, ADR-039 — the wizard's entry point moves to a
new bottom-right Agents Map `.map-fab` opening a popup modal with a
`.wizard-step-bar` (4 steps), built from new CSS classes composed entirely
of this codebase's own existing design tokens, deliberately not a reuse of
`.side-panel-overlay`/`.side-panel`'s own edge-anchored slide-in selectors
(distinct-shape requirement); `CreateAgentWizard.tsx` renamed/restructured
to `CreateAgentWizardModal.tsx`, its existing per-type `create_agent`/
grant/assign call sequences preserved unchanged, only regrouped into 4
steps per the story's own confirmed field-to-step mapping; Settings' own
"+ Create agent" affordance retired (sole entry point becomes the Map
FAB); new shared `SkillsTree.tsx` (mode-parameterized: `manage` for
`AgentDetailPanel.tsx`'s existing grant/revoke UI, `select` for the
wizard's new Step 3 multi-select) is originated by `REQ-SB-48-US-01-T02`
and consumed here via this codebase's first cross-story frontend
`depends_on` edge, rather than duplicated; Step 4's Trigger choice stays
recorded-intent-only (new additive `trigger` field on `POST /agents`,
mirroring Domain/Purpose's `settings` kv-list mechanism), composing
`REQ-SB-47-US-01`'s now-real Schedule tab without building any of its
configuration UI inline; folding `REQ-SB-51-US-01`'s `is_background_agent`
toggle into the wizard was considered and declined (no locked AC needs it,
and it would add an avoidable dependency on that story's own not-yet-`Done`
backend field) — see "Amendment — Popup Modal Redesign, shared
`SkillsTree.tsx` extraction, Trigger/Background-Agent composition" under
"Agent Creation Wizard", below)

**Previously:** 2026-08-14 (REQ-SB-50-US-01 Tags and Locations
Autocomplete architecture pass, no new ADR — a purely additive composing
endpoint over two already-`Accepted`, already-shipped read-only
enumeration functions, the same "ordinary same-shape extension" posture
already established repeatedly in this file: new `GET /vault-search/
scope-suggestions` → new `vault_search.list_scope_suggestions()`, calling
its own existing `list_tags()` plus `vault_writer.list_known_kinds()`
directly (mirroring `search()`'s own existing direct-`vault_writer`-call
precedent), returned as two distinct, un-merged `tags`/`folders` lists,
not flattened; `AgentDetailPanel.tsx`'s already-shipped Vault Scope
`kv-row` (`REQ-SB-29-US-01-T05`) gains a client-side-filtered suggestion
dropdown sourced from it, fetched once per agent-switch alongside
`fetchSections()`/`fetchProviders()`, with an `onMouseDown`-before-
`onBlur` interaction-order note recorded for the coder — see "Tag/Folder
Scope Suggestions" under "Browse & Search" and the matching addendum
under "Agent-to-Tag/Folder Vault Scoping", below) + REQ-SB-49-US-02 Cockpit Person-Directed
Instruction `@PersonName` architecture pass, ADR-038 — a deliberate,
gate-preserving carve-out from `ADR-036`'s own "Cockpit bypasses
`invoke_skill`'s gate by construction" precedent: a new bound tool,
`propose_person_note_update`, intercepted before the generic
`execute_tools` node exactly like `ADR-032`'s `record_knowledge_gap`,
conditionally bound only to an agent with real access (unlike its two
graph-level siblings' "bind to everyone" shape); a new `mutates: True`
Skill of the same name, granted to `people-producer`; a new `"cockpit_
mention"` trigger literal (never a reuse of `"chat"`/`"direct"`/
`"hub_routed"`/`ADR-037`'s `"scheduled"`) so the FULL existing two-axis
working-mode gate (`ADR-029`) applies; "propose" is read as a genuine,
mode-scoped deviation — Supervised needs no extra step (its own Pending-
Approval "Approve" click already is the confirmation), Manual/Autonomous
gains a new opt-in `_dispatch_skill(..., already_approved=False)` seam
(mirrors the existing `agent_id` auto-injection precedent) so the Skill's
own handler never writes on an unconfirmed direct dispatch, instead
recording an explicitly confirmable/discardable in-thread proposal (new
`app/business/cockpit/person_note_proposals.py`, mirrors `cockpit/
research.py`'s own scoped-list/direct-`vault_writer`-on-Save shape) — see
"Cockpit Person-Directed Instruction (`@PersonName`)" section, below) +
REQ-SB-49-US-01 Cockpit Inline `@agent_id`
Mention architecture pass, no new ADR — purely additive frontend parsing
over `ADR-036`'s already-Accepted Cockpit mechanism, no new endpoint, no
new persisted concern: `Cockpit.tsx`'s `chat-input-row` gains send-time
`@token` extraction (`/@(\S+)/g`) resolved against the SAME candidate list
its own "Available Agents" panel already renders from (never a second,
independently-filtered list) by exact, case-insensitive `id`-or-normalized-
`name` match, each match triggering the existing, unmodified
`bringInAgent(...)` call before `sendCockpitMessage(...)`, mirroring the
"+ Bring in" button's own sequencing; a live, prefix-filtered `@`-suggestion
dropdown reads the same list as the user types; composes with
`REQ-SB-51-US-01`'s (Ready, not yet built) `isBackgroundAgent` predicate as
a soft, same-source dependency, not a hard `depends_on` — see "Cockpit
Inline `@agent_id` Mention" section, below) + REQ-SB-48-US-01 Skills Capabilities Tree —
Collapsible, Icon-Bearing, Multi-Select Groups by Tool architecture pass,
no new ADR — a purely additive/presentational upgrade over the
already-`Accepted` Skills mechanism, not a new mechanism: every
`skill_tools.SKILLS` entry gains a `"tool": "Outlook" | "Vault" | "Web" |
"Compass"` field (the analyst's already-resolved taxonomy, confirmed
accurate by direct re-read against the current, unchanged 11-entry
catalog — no Skill has been added or removed since `REQ-SB-39`); the field
is server-side, not a frontend static map, so it stays the single source
of truth as the catalog grows (`list_skills()`'s existing full-dict
passthrough and `skill_registry.list_agent_capabilities`'s skill-kind
branch both carry it through with no new endpoint); the 4 Tool-level icons
stay a small frontend-only static lookup keyed by `"tool"` (mirrors
`Sidebar.tsx`'s own existing plain-Unicode-glyph `.nav-icon` convention;
unlike the Skill catalog, the 4-Tool taxonomy is not expected to grow at
anywhere near the same rate, so no drift risk from keeping icon glyphs
frontend-owned); `AgentDetailPanel.tsx`'s flat Capabilities `kv-list` is
replaced by a new collapsible, multi-select tree grouped by Tool,
composing N sequential existing single-Skill grant/revoke calls — no new
bulk endpoint — see "Amendment — Skills grouped by Tool" under "Skills
Repository — registration & per-agent access", below) + REQ-SB-47-US-01 / REQ-SB-45 Per-Agent
Scheduler + Shared Outlook-COM Dispatch Lock architecture pass, ADR-037 —
the shared dispatch lock's canonical home relocates to a new
`app/business/agent_schedule_registry.py` (generalized from
`capture_scheduler._capture_run_lock`), not `app/scheduling/`, mirroring
ADR-029's own "gate lives where every caller can reach it" resolution
applied to a concurrency primitive instead of a gating decision;
`capture_scheduler.py` publishes its live `AsyncIOScheduler` INSTANCE into
that module once at startup rather than `business` importing
`app.scheduling`, so live schedule add/edit/remove needs no restart; new
sibling `.second-brain/agent_schedules.json`
(`"{agent_id}::{capability_id}"`-keyed); the shared lock is explicitly
scoped **in-process only** — the SPRINT-030 two-process collision that
motivated REQ-SB-45 stays a deliberate, disclosed, out-of-scope
operational-hygiene risk, not solved here; `invoke_skill` gains a
`"scheduled"` trigger literal composing with ADR-029's existing gate
(Manual + scheduled skips silently, mirroring the blob tick's own
precedent; Supervised + mutating falls into the existing pending-approval
branch unchanged); the existing hardcoded hourly blob tick is unmodified
except for which lock object it acquires, so it and any new per-agent
schedule targeting the same capture agent correctly serialize;
`meeting-capture`'s/`todo-capture`'s `run_capture_now` stays the existing
honest not-available stub, operator-relayed scoping decision, not rebuilt
— see "Per-Agent Scheduler & Shared Outlook-COM Dispatch Lock" section,
below + REQ-SB-51-US-01 Background Agents —
architecture pass, no new ADR — new `app/business/background_agent_registry.py`
mirroring `working_mode_registry.py`'s exact shape, backed by
`.second-brain/agent_background_flags.json`; the 3 real capture-pipeline
Workers backfilled True via a per-id exception set, all others default
False; a single backend exclusion check inside
`agent_keywords.list_candidate_agents_for_keyword_match`, and a single
shared frontend predicate `isBackgroundAgent` used by both `Cockpit.tsx`
and `layoutAgents.ts`; applies ADR-014/ADR-018's already-Accepted
"registry composed alongside `agent_registry.py`" shape, one boolean
concept over — see "Background Agents" section, below + REQ-SB-28-US-01 File upload, Compass
summarization & Vault Filing Expert handoff architecture pass, ADR-034 —
new temporary non-vault blob storage under `.second-brain/uploads/` (first
extension of the flat-file `.second-brain/` convention to raw bytes, not
JSON); `pypdf` (new dependency) extracts PDF text before Compass ever sees
it; a new `summarize_content` Compass function mirrors `classify_email`/
`classify_task`'s shape; the summarization capability is registered as a
new `summarize-file` Skill through the already-`Accepted` Skills
extensibility path (`ADR-015`) — this project's first real, non-stub Skill
implementation; the handoff to the Vault Filing Expert
(`determine_placement_and_file`) needs zero interface changes; image
(PNG/JPG) support is explicitly deferred, not built — direct inspection
confirmed `diagram-understanding` is an unconditional stub
(`available: False`) and Compass is text-only, so this pass's real scope
is text-bearing files only (`.pdf`/`.txt`/`.md`); the new upload endpoint
is an additive sub-resource on `agents_router.py`, never a modification of
the existing `POST /agents/{agent_id}/chat` JSON contract
(`REQ-SB-25-US-01`) — see "File upload, Compass summarization & Vault
Filing Expert handoff" under "In-App Agent Orchestration", below +
REQ-SB-38-US-01 Agents Map Density Clustering
architecture pass, no new ADR — confirms and locks the prototype's own two
previously-flagged-tentative values as final, by direct operator decision,
not re-derivation: `VISIBLE_SLOT_CAP = 6`, scoped per-(Section × Type-ring);
see "Agents Map — Density Clustering (REQ-SB-38-US-01)", below + REQ-SB-41-US-01 Agent Overview surface
architecture pass, ADR-033 — Overview becomes `AgentDetailPanel.tsx`'s new
default-landing tab (`TABS` gains `'overview'` first; `activeTab` no
longer defaults to `'chat'`), resolving the operator's own "before... Can
Chat with it" complaint directly; Purpose region reads the existing
`settings` kv-list (`"Purpose"`, falling back to `"Domain"`), composing
`ADR-030`/`ADR-031`'s already-established mechanism, never a display-time-
derived summary; all 7 shipped agents backfilled with a real, authored
Purpose settings entry (a static-seed-data edit only, does not touch
`REQ-SB-37-US-02-T01`'s already-locked Worker `settings=[]` constraint);
open-knowledge-gap count composed into the Overview for Expert-type agents
via `ADR-032`'s already-built endpoint, no new endpoint — extends
`ADR-030`, `ADR-031`, `ADR-032`, reopens none of them — see "Agent Overview
surface" under "My Day & Agent Panel APIs", below + REQ-SB-40-US-01 Agent Knowledge-Gap Tracking
& Expert Readiness architecture pass, ADR-032 — a structured, intercepted-
tool-call decline signal (`record_knowledge_gap`, mirrors `ADR-017`'s
`request_cross_section_help` precedent) extends `ADR-015`'s conversation
graph rather than a text pattern-match; a new, dedicated tenth
`.second-brain/agent_knowledge_gaps.json` store + `app/business/
knowledge_gap_tracking.py` (deliberately not `agent_activity.py`, whose
`_ACTIVITY_KINDS` scope stays background-run-only); closing paths compose
the already-`Done` Vault Filing Expert (`ADR-021`, human-provided answers)
and delegated knowledge-bootstrap chain (`ADR-023`, directed research)
unchanged; display is a new, conditionally-rendered "Knowledge gaps" tab on
`AgentDetailPanel.tsx` gated to Expert-type agents (`/design` skipped for
this batch, operator-directed) — does not depend on or modify `REQ-SB-41`
(Agent Overview, still unspecced) — see "Agent Knowledge-Gap Tracking &
Expert Readiness" under "In-App Agent Orchestration", below + REQ-SB-37-US-03 Agent Creation Wizard —
Producer-type flow architecture pass, ADR-031 — resolves the PRD's own
previously-unresolved output-action fork: a Producer's output action is a
granted output Skill (single-select at creation), not a destination/write-
mode field; Purpose is stored via `create_agent`'s existing `settings`
kv-list, mirroring Expert's Domain (`ADR-030`), not a new field, and does
not depend on REQ-SB-41-US-01 landing first; one minimal placeholder output
Skill, `write-to-vault-draft`, is seeded into `skill_tools.SKILLS` so the
mechanism is exercisable — extends `ADR-030`/`ADR-028`/`ADR-029`, reopens
none of them — see "Amendment — Producer-type flow" under "Agent Creation
Wizard — entry point, type selector, Expert-type flow", below + REQ-SB-37-US-02 Agent Creation Wizard —
Worker-type flow (Skills + Vault Scope + Section) architecture pass, no new
ADR — additive composition of `ADR-030` (`create_agent`/`POST /agents`,
its sequential-`PATCH`-after-`POST` precedent), `ADR-028`/`ADR-029`
(unified Skills grant via the already-existing `POST`/`DELETE
/agents/{agent_id}/skills/{skill_id}` endpoints, unchanged), and
`REQ-SB-29-US-01`'s additive `PATCH /agents/{agent_id}` `scope` field:
`POST /agents`'s `type` check is extended to also accept `"worker"`
(`domain` becomes optional, unused for Worker — `settings` stays `[]`,
matching the already-`Done` "starts with zero pre-seeded actions"
precedent); the wizard's Worker step performs the same
client-validate-before-any-call discipline `REQ-SB-37-US-01-T04`'s Expert
step already established (Scenario 4/AC-07 precedent), then issues a
sequential call chain against an already-live `agent_id` — never a
draft/staged agent record — `POST /agents` → one `POST
/agents/{agent_id}/skills/{skill_id}` per selected Skill → one combined
`PATCH /agents/{agent_id}` carrying both `section_id` and `scope` in the
same call (`AgentAssignmentUpdateBody` already accepts multiple optional
fields per request, so no second `PATCH` is needed). See "Amendment —
Worker-type flow" under "Agent Creation Wizard — entry point, type
selector, Expert-type flow", below + REQ-SB-37-US-01 Agent Creation
Wizard — entry point, type selector, and the Expert-type flow — architecture pass,
ADR-030 — `agent_registry.py`'s static `AGENTS` dict becomes `_SEED_AGENTS`
(byte-identical, unchanged) merged at read time with a new persisted
`.second-brain/agents_registry.json` overlay (`created_agents`), a new
`create_agent()` primitive slug-derives a unique `agent_id` via
`vault_writer.tag_slug`, a new `POST /agents` endpoint in
`agents_router.py`, and a new `features/agents-map/CreateAgentWizard.tsx`
+ Settings-page entry affordance — supersedes ADR-011 point 2 only, does
not reopen points 1/3/4 — see "Agent Creation Wizard — entry point, type
selector, Expert-type flow", below + REQ-SB-39-US-02 unified agent capability
model, phase 2 — working-mode gate extended to Skills, the 4 mutating
Actions migrated — architecture pass, ADR-029: the two-axis gate moves
inside `skill_registry.invoke_skill` itself (not mirrored into
`agents_router.py`, since `knowledge_bootstrap.py`'s own call site is a
business module `ADR-003` forbids from reaching into `api`), a new
ungated `skill_registry._dispatch_skill` primitive backs both the gate's
own fallthrough and a new Pending-Approvals Approve-endpoint branch,
`run_capture_now`/`pause_schedule`/`rebuild_person_note`/`build_knowledge`
join `skill_tools.SKILLS` with `"mutates": True` preserving today's exact
real/honest-unavailable split, and the migration-grant seed retrofits 5
real already-shipped agents (`email-capture`, `meeting-capture`,
`todo-capture`, `people-producer`, `compass-expert`) — see "Amendment —
unified capability model, phase 2" under "Skills Repository —
registration & per-agent access", below + REQ-SB-39-US-01 unified agent
capability model, phase 1 — read-only Actions migrated to Skills —
architecture pass, ADR-028: `skill_tools.SKILLS` gains a `mutates` field on
every entry, `skill_registry.invoke_skill` gains a required `trigger`
parameter threaded through every real call site, `ADR-011`'s chat funnel's
dispatch step (not the funnel itself) routes migrated ids to `invoke_skill`
instead of `_invoke_action`, a one-time migration seed retrofits the 4
real already-shipped agents onto real Skill grants, and a new
`skill_registry.list_agent_capabilities` aggregator unifies the
`GET /agents/{agent_id}` capability list — see "Amendment — unified
capability model, phase 1" under "Skills Repository — registration &
per-agent access", below + REQ-SB-09-US-01 To-Do Task Capture Pipeline
architecture pass, ADR-027 — see "Task Notes & Outlook-Tasks Capture" under
Data Model, the "To-Do real data" amendment under My Day APIs, and the
`todo-capture` working-mode-gate update, below + REQ-SB-11-US-01 Agent Activity & Error
Observability architecture pass, no new ADR — honest-failure-recording
fix inside `email_classification.py::run_capture_and_record_completion`
(meeting-capture success-entry parity, a per-capture-step honest-failure-
funnel extending `ADR-015` to a new call site, a new `"run_error"`
history-entry kind), new read-only `app/business/agent_activity.py`/
`app/api/agent_activity_router.py` mirroring `system_health.py`'s shape,
a new `outlook_com.py::check_reachable()` reachability check, and a new
`AgentActivityPage.tsx` top-level nav page + REQ-SB-04-US-01 Agent Vault Write Access —
`/mcp` shared-secret authentication for non-loopback callers plus a
write-capable MCP tool that never writes directly, always routing through
a new `trigger="hermes"` Pending Approval dispatched via `ADR-021`'s own
Tier-2 `action_id` mechanism, scope-gated by a fail-closed seam pending
`REQ-SB-29-US-01` (real, load-bearing, unresolved dependency —
`ESCALATIONS.md` → `ESC-026`), architecture pass, ADR-025 — shares its
`/mcp` auth mechanism with `REQ-SB-03-US-01`'s own still-unbuilt
Constraint + REQ-SB-01-US-01 Vault Indexing — the first
real, persistent, re-runnable vault index (frontmatter/tags/wikilink graph)
architecture pass, ADR-024 — new `app/business/vault_indexing.py`
module-level in-memory rebuild-and-swap cache, new `app/api/
vault_index_router.py` on-demand rebuild endpoint, unconditional
scheduler-tick wiring into `email_classification.
run_capture_and_record_completion` (zero changes to `capture_scheduler.py`
itself), and a same-shape `vault_writer.read_note()` frontmatter list-value
round-trip fix mirroring REQ-SB-30-US-01's own boolean-value fix precedent
+ REQ-SB-08 meeting-notes-from-calendar-capture architecture pass + REQ-SB-14 vault-graph-connectivity + REQ-SB-15 manual-entry-templates + REQ-SB-10 people-notes-from-email-capture + BUGFIX-01 email-to-person-wikilink pass + REQ-SB-16 partner-hub-notes-and-migration architecture pass + REQ-SB-17 research-notes-template-and-guide architecture pass + REQ-SB-12-US-01 app-shell/Agents Map frontend architecture pass + REQ-SB-12-US-02 My Day dashboard API architecture pass + REQ-SB-13-US-01 agent detail panel (settings/actions/chat/history) architecture pass, ADR-011 + REQ-SB-16-US-01-T04 migration-scan correction pass, ADR-012 + REQ-SB-08-US-01-T06 meeting-occurrence-dedup-key correction pass, ADR-013 — resolves ESC-002 + REQ-SB-18-US-01 dynamic agent Sections/agent-to-section-assignment + REQ-SB-19-US-01 global LLM Provider CRUD/per-agent provider picker architecture pass, ADR-014 + REQ-SB-22-US-01 My Day rolling 7-day window date-filtering architecture pass + LangGraph in-app agent orchestration & shared MCP server architecture pass (REQ-SB-20/25/26/27), ADR-015 — supersedes ADR-007 + REQ-SB-25-US-01 architecture-scoping confirmation pass (ADR-015 already covers this story in full; `run_agent_conversation` history-to-message-shape addendum, no ADR change) + REQ-SB-27-US-01 Skills Repository registration/per-agent-access plumbing architecture pass, no new ADR — applies ADR-015 + REQ-SB-26-US-01 Agent Memory extraction-mechanism architecture pass, ADR-016 — extends ADR-015 point 13, does not reopen it + BUGFIX-02-US-01 Agents Map semantic-zoom/drill-down containment fix architecture pass (BUG-002), no new ADR — applies ADR-010/ADR-014 + REQ-SB-20-US-01 Section-Hub cross-Section routing keyword-storage/routing-node architecture pass, ADR-017 — extends ADR-015 point 12, does not reopen it, resolves ESC-010 + REQ-SB-21-US-01 per-agent working modes (Autonomous/Supervised/Manual) + Pending Approvals workflow architecture pass, ADR-018 — extends ADR-005/ADR-008/ADR-011, does not reopen any of them + REQ-SB-08-US-01-T06 second meeting-occurrence-dedup-key correction pass, ADR-019 — supersedes ADR-013 points 1/2, resolves ESC-002 and ESC-012 + REQ-SB-21-US-01 working-mode gate correction pass, ADR-020 — supersedes ADR-018 points 3/5 only, resolves ESC-013 + REQ-SB-30-US-01 Compass-judged email importance filtering architecture pass, no new ADR — extends the existing `classify_email` capture-time call, fixes a `vault_writer.py` frontmatter boolean round-trip gap, extends `my_day.py`'s read-path filter, and scopes a new in-window-only retrofit, all as same-shape extensions of already-Accepted structure + REQ-SB-33-US-01 agent grounding & honest-uncertainty guardrail architecture pass, no new ADR — extends `history_entries_to_messages`'s existing single identity `SystemMessage` with an additional grounding/honest-uncertainty instruction appended to its own content, applies ADR-015 + REQ-SB-31-US-01 System Health View read-only status-aggregation + chat-path crash-gap fix architecture pass, no new ADR — new `system_health.py`/`system_health_router.py` mirror `my_day.py`'s "read-only, no new persisted state" shape (extends ADR-003), new `SystemHealthPage.tsx`/nav item apply ADR-010, `run_agent_conversation`'s Scenario 8 fix applies ADR-015's existing honest-failure-funnel pattern to a second call site) + REQ-SB-35-US-01 Vault Filing Expert (new registry agent, methodology-grounded placement/write decision, Tier-2 new-top-level-area approval override) architecture pass, ADR-021 + REQ-SB-36-US-01 real Anthropic Provider integration & web-research skill architecture pass, ADR-022 — closes a live-discovered skill-access tool-binding gap in ADR-015's conversational graph + REQ-SB-36-US-02 delegated knowledge-bootstrap orchestration (Hub-routing match → real invocation) architecture pass, ADR-023 — extends ADR-017, does not reopen it. **Live-discovered, not silently patched:** `REQ-SB-35-US-01`'s and `REQ-SB-36-US-02`'s own `## Dependencies` sections both wrongly assert `REQ-SB-21-US-01`/`ADR-020` is "(Done)" — direct code and story-file inspection during this pass found `REQ-SB-21-US-01` is actually `status: Draft`, unbuilt, with zero real code for its Pending-Approvals/working-mode mechanism; `ADR-021`'s Tier 2 and `ADR-023`'s Autonomous-mode check both carry a real, currently unmet blocking prerequisite on it shipping — see `ESCALATIONS.md` → `ESC-017` + REQ-SB-02-US-01 Browse & Search architecture pass, ADR-026 — new `app/business/vault_search.py` (read-only browse/tag-filter/note-detail/ranked-search, composes `vault_indexing.get_index()` only) + new `app/api/vault_search_router.py` + new `VaultBrowserPage.tsx`/`NoteDetailPage.tsx` frontend, plus a small additive `vault_indexing.py` index-readiness accessor (`get_last_rebuilt_at()`) — extends ADR-024, does not reopen it + REQ-SB-09-US-01 To-Do (Outlook Tasks) capture architecture pass, ADR-027 — new `outlook_com.py::list_outlook_tasks` (Tasks-folder COM read, no `IncludeRecurrences`-equivalent exists for Tasks, structurally unlike Calendar), a new load-bearing `.second-brain/task_note_index.json` EntryID-keyed lookup (not a recomputed-path check, diverging from Meeting's own `ADR-019` mechanism — Task's own Scenario 6 requires a due-date/status change to still resolve to the same note), new `compass_client.classify_task` (customer-only, not a reuse of `classify_email`), new `app/business/todo_classification.py` mirroring `meeting_classification.py`, a third gated block in `run_capture_and_record_completion` (extends ADR-005/ADR-008 point 4/ADR-018, reopens none — and resolves ADR-008's own explicitly-anticipated "revisit if a third pipeline..." fork with "no orchestration-module extraction this pass"), plus My Day's `GET /my-day/todo` real-data amendment (no new ADR needed for that piece — same-shape extension of already-Accepted `my_day.py` structure) + REQ-SB-29-US-01 Agent-to-Tag/Folder Vault Scoping architecture pass, no new ADR — see "Agent-to-Tag/Folder Vault Scoping — assignment & scope-bounded retrieval" — new `.second-brain/agent_scopes.json` + `app/business/scope_registry.py` mirroring `ADR-017`'s per-agent-list keyword shape, a new `vault_writer.list_notes_matching_scope` primitive deliberately independent of `ADR-024`/`ADR-026`'s vault-indexing layer, a new scope-aware `@mcp.tool()` mirroring `vault_write_tools.propose_vault_write`'s agent_id-explicit/server-resolved shape (`ADR-015` point 9), a `PATCH /agents/{agent_id}` additive `scope` field, and a new "Vault scope" `AgentDetailPanel.tsx` kv-row mirroring the Keywords row — exposes the real per-agent scope lookup `ADR-025` point 6's fail-closed seam (`ESC-026`) needs, but does not itself wire or close that seam (a separate, still-blocked `REQ-SB-04-US-01` task + REQ-SB-42-US-01 Real-Time
Agent Activity Pulses architecture pass, ADR-035 — Server-Sent Events push
transport (not WebSocket) plus a new, in-memory-only `app/business/
agent_presence.py` ephemeral "agent presence" registry, distinct from
`REQ-SB-11`'s persisted history; instruments five real dispatch call sites
(capture/Skill via `run_capture_for_agent`, explicit Skill via
`_dispatch_skill`, chat via `run_agent_conversation`, Hub-routing via each
real `route_cross_section_request` caller, pending-approval create/resolve
broadcast-only); new `GET /agent-presence/stream` SSE endpoint — see "Real-
Time Agent Activity Pulses", below + REQ-SB-43-US-01/REQ-SB-44-US-01
Meeting & Inbox Cockpits architecture pass, ADR-036 — a multi-agent
shared-thread chat mechanism composing `ADR-015`'s existing per-agent
`run_agent_conversation` unmodified (new sibling `.second-brain/
cockpit_threads.json`, this codebase's first multi-party conversation
store), one shared `app/business/cockpit/` module + frontend `Cockpit`
component for both stories (REQ-SB-44's attachment review/draft-reply are
additive props, not a fork), a confirmed-by-investigation working-mode-gate
bypass-by-construction (the Cockpit never reaches `skill_registry.
invoke_skill`/`_invoke_action`'s gated dispatch at all — no new trigger
value needed), a real `depends_on` cross-story sequencing requirement onto
`REQ-SB-28-US-01` (`Ready`, not `Done`) for the attachments half, and a new
Email-note `recipients` frontmatter field mirroring Meeting's `attendees`
shape — see "Meeting & Inbox Cockpits", below)

## Agent / Pipeline / Job / Hub Domain Model — Taxonomy (see [ADR-041](ADR.md))

**Purpose of the whole system, in the operator's own words (2026-08-15):**
Second Brain is a framework of agentic solutions on top of Obsidian, to
remove work from the operator's head and help them be smarter at work.
The vault is the operator's own human-readable KB, covering both work and
personal life (currently: work phase only). Everything below exists to
serve that purpose — read this section before adding any new
agent-shaped concept anywhere in this codebase; it is the durable
taxonomy referenced by name across every other section.

**Two independent axes — not one flat list of "agent types":**

- **Kind of work** (what it does): **Expert** (answers questions over the
  KB), **Producer** (composes/generates a deliverable — a file, an email
  reply, a to-do action), and the mechanical pipeline verbs (fetch,
  classify/tag, link, store, and any future verb a Pipeline author adds).
- **Structural tier** (how it's exposed): **Agent** — a full,
  independently-addressable identity: own chat, own communication
  history, own Working Mode, own Agents Map node. **Job** — a
  lightweight unit living INSIDE a Pipeline's own DAG: its own editable
  prompt and its own Skill(s), but no guaranteed own chat thread, Map
  node, or Working Mode, unless a future pass decides a specific Job
  deserves one.

A "Producer" can be either tier: a standalone Producer Agent (asked
directly — "build me a sheet") or a Producer-flavored Job embedded in
someone else's Pipeline (an email reply composed mid-pipeline, then
handed downstream to be stored). "Expert" is always the Agent tier — by
definition something the user and other agents/pipelines address
directly. The mechanical pipeline verbs are always the Job tier.

- **Hub** — the root of a Section's own tree. Both a MANAGER (routes to
  its own Pipelines and Experts) and a DATABASE (holds the Section's own
  registry — which files/vault scope, which agents and pipelines belong
  to it). Not a new structural tier — an organizing node, the same
  Section concept this app already has, now with an explicit job
  description.
- **Pipeline** — a user-extensible DAG of Jobs, not a fixed N-stage
  chain. Real, confirmed capabilities: forking (parallel Jobs over
  different parts of one input — e.g. an email's body vs. its
  attachment), merging (parallel branches recombine into one stream),
  and branching to consult a standalone Expert mid-flow (additive — the
  Pipeline's own terminal step, e.g. Store, still runs either way). The
  user adds/removes/rewires Jobs themselves via the builder, below — not
  something engineers hardcode per pipeline type.
- **Prompt customization is universal** — every Agent and every Job gets
  the same "edit this thing's own instructions" mechanism, one UI
  pattern wherever it appears.
- **Execution engine:** a Pipeline's own author-defined DAG compiles to a
  `langgraph.graph.StateGraph` at runtime (narrows `ADR-007`'s original
  "simple linear pipelines stay outside any orchestration framework"
  carve-out further than `ADR-015` already did, for the Pipeline domain
  specifically — `langgraph` is already a real, installed dependency).
- **Builder:** a native canvas inside this app's own React frontend
  (e.g. React Flow), not an external visual-builder application —
  shares the same Hub/Section/Agent/Skill data model and the Agents
  Map's own visual language, one cohesive product.

**Status:** directional/foundational, adopted 2026-08-15 (`ADR-041`).
Real implementation detail (the DAG's own persisted data model, the
checkpointer's own durability backend, the canvas UI/UX, exactly how/
whether a Job ever earns its own Agent-like surface) is explicitly left
open, to be resolved by whatever requirement formally specs the Pipeline
Builder. `REQ-SB-53` (Capture Pipeline Split into fixed Pull/Tag/Link/
Store Agent stages, `ADR-040`) is **superseded** by this model and
parked — see "Capture Pipeline Split", below, and `ADR-040`'s own
Superseded note. **The first real, concrete Pipeline now exists
(2026-08-16, `REQ-SB-55`, [ADR-043](ADR.md)) — see "Email Capture &
Threading Pipeline — First Concrete Pipeline", below.** It resolves the
DAG's own persisted-data-model question (code-defined `StateGraph`, not
yet a persisted/user-editable definition), the checkpointer-durability
question (not needed — mid-pipeline human approval reuses the existing
flat-JSON Pending Approval mechanism, never a LangGraph suspend/resume),
and the Job-Agent-surface question (a Job never earns one; one Agent-tier
identity represents the whole Pipeline) — all concretely, for this one
Pipeline. The Builder (point 6) stays deferred, per `ADR-041`'s own
sequencing note, now genuinely closer.

## System Overview

Second Brain indexes and serves the user's Obsidian vault (markdown notes with
frontmatter and wikilinks) directly — no staging/promotion gate, since it's the
user's own trusted personal data, not agent-written scratch data. Standalone
project; Hermes (an external MCP-based multi-channel communication tool) is a
planned integration point, not something this project builds. Future integration
with `agentic-map`'s agents is a deliberately separate, later decision.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.14 + FastAPI (see [ADR-001](ADR.md)) |
| Frontend | TypeScript + React + Vite, portable Node.js toolchain (see [ADR-002](ADR.md)); `react-router` for client-side navigation, plain global CSS, native `fetch` (no data-fetching library yet) — see [ADR-010](ADR.md) |
| Scheduling | APScheduler (`AsyncIOScheduler`), in-process, wired into FastAPI's `lifespan` (see [ADR-005](ADR.md)) |
| Agent orchestration | LangGraph (`langgraph`), bounded to Second Brain's own in-app Agents Map agent behavior (chat, Hub routing, memory, skill invocation) — not Hermes's own external orchestration, which stays untouched; see [ADR-015](ADR.md) (supersedes [ADR-007](ADR.md)) |
| Tool protocol | Model Context Protocol — official `mcp` Python SDK, one shared server exposing vault-query tools to both the in-app LangGraph agents and Hermes's external orchestration; see [ADR-015](ADR.md) |
| External LLM APIs | Compass (OpenAI-wire-compatible, `langchain_openai.ChatOpenAI` via `model_factory.py`) for conversational replies; Anthropic (official `anthropic` SDK, plain client in `data_access/anthropic_client.py`, not LangChain-wrapped) for the web-research skill's server-side web-search tool specifically — see [ADR-022](ADR.md) |
| Chat rich-text rendering | `react-markdown` (v9.x, CommonMark's default feature set, no `remark-gfm`/`rehype-raw`/`rehype-sanitize` plugins — no raw-HTML/`dangerouslySetInnerHTML` path exists), one shared `src/frontend/src/components/ChatMessageText.tsx` presentational component consumed by both `Cockpit.tsx` and `AgentDetailPanel.tsx` — see [ADR-050](ADR.md) |

## Source Layout

```
src/
  backend/
    .venv/            — Python 3.14 virtual environment (not committed)
    app/
      api/             — FastAPI routers; HTTP-only, delegates to business/
      business/        — domain logic and orchestration; no HTTP, no direct filesystem access
      data_access/     — reads/writes the Obsidian vault (and any other storage); no business rules
      scheduling/      — in-process recurring/catch-up scheduler (APScheduler); a trigger
                          source parallel to api/, calls into business/ only, never
                          data_access/ directly (see ADR-005)
      main.py          — FastAPI app instantiation, router wiring, scheduler lifespan wiring
    tests/
    requirements.txt
  frontend/            — TypeScript + React + Vite SPA (scaffolded via `create-vite`;
                          see "Frontend Application Architecture" below for the
                          `src/frontend/src` internal structure, ADR-010)
tools/
  node/                — portable Node.js runtime + npm (not committed; see ADR-002)
  use-node.ps1         — dot-source to put tools/node on PATH for a shell session
```

Layer boundary (see [ADR-003](ADR.md)): `api` → `business` → `data_access`, one
direction only. A router must not reach into `data_access` directly, and
`business` must not perform HTTP or filesystem I/O of its own. `scheduling/`
(see [ADR-005](ADR.md)) is a second trigger source structurally parallel to
`api/`: it translates timer/lifecycle events (app startup, hourly interval,
in-process missed-run catch-up) into calls against `business/`, under the same
"never reach `data_access/` directly" rule — it does not sit *below* `api/` in
the request path, it sits *beside* it as an alternative entry point into
`business/`.

`app/business/customer_hub_linking.py` (REQ-SB-14, new) is the shared "ensure
the customer's hub note exists, then link this note to it" orchestration, used
by both the one-time retrofit and the going-forward capture-pipeline hook —
the same one-module-per-maintenance-operation shape as the existing
`tag_backfill.py` / `vault_restructure.py` modules already in `app/business/`.
See Data Model → "Customer Hub Notes & Graph Linking", below, for the full
layering breakdown.

`app/business/people_extraction.py` (REQ-SB-10, new) is the parallel "ensure
this email sender's Person note exists and is up to date, linking it to their
company's Customer hub note when that company is a known customer"
orchestration — same one-module-per-maintenance-operation shape, and the
first business module that composes another business module
(`customer_hub_linking.py`'s granular hub-note primitives) rather than only
`data_access`. See Data Model → "Person Notes & Email-Sender Extraction",
below, for the full layering breakdown and the load-bearing carve-out on how
it reuses (not blindly calls) `customer_hub_linking`.

`app/business/meeting_classification.py` (REQ-SB-08, new — see
[ADR-008](ADR.md)) mirrors `email_classification.py`'s shape exactly (fetch
→ derive customer via attendees → write note → link customer hub +
attendee Person notes → dedup), composing `people_extraction.py` (attendee
Person notes, extended from "sender" to "attendee") and
`customer_hub_linking.py` (the same granular-primitives-only-after-a-
confirmed-match carve-out `people_extraction.py` already established) as-is
— no changes to either module's existing public functions. `app/
data_access/outlook_com.py` gains a new calendar-read function,
`list_calendar_events`, alongside the existing `list_recent_mail`. See
Data Model → "Meeting Notes & Calendar-Attendee Extraction", below.

`app/business/todo_classification.py` (REQ-SB-09, new — see
[ADR-027](ADR.md)) mirrors `meeting_classification.py`'s shape (fetch →
classify by customer → write/top-up Task note → link customer hub after a
confirmed match only → dedup), composing `people_extraction`/
`customer_hub_linking`'s same granular-primitives-only carve-out — no
Person/attendee linking, since a Task has no attendee list. `app/
data_access/outlook_com.py` gains a third read function,
`list_outlook_tasks`, alongside `list_recent_mail`/`list_calendar_events`.
`app/data_access/compass_client.py` gains a second classification prompt
function, `classify_task` (customer-only, not a reuse of `classify_email`).
See Data Model → "Task Notes & Outlook-Tasks Capture", below.

`app/business/partner_hub_linking.py` (REQ-SB-16, new — see
[ADR-009](ADR.md)) is a **parallel sibling** to `customer_hub_linking.py`,
not an extension of it: the same two-granular-primitives shape
(`ensure_partner_hub_note`, `link_note_to_partner_hub`) applied to the new,
mutually-exclusive `partner/<slug>` tag namespace, plus the one-time
`migrate_customer_to_partner` retrofit that moves Microsoft's hub note and
retags every already-mistagged note. `customer_hub_linking.py` itself is
untouched. See Data Model → "Partner Hub Notes & Mutually-Exclusive Company
Taxonomy", below, for the full layering breakdown and why a sibling module
was chosen over extending the existing one.

`src/frontend/src` (REQ-SB-12-US-01, new — see [ADR-010](ADR.md)) gains its
first real structure beyond the bare `create-vite` scaffold: `pages/`
(route-level screens), `components/shell/` (the persistent collapsible-
sidebar app shell, reused by every page), `features/agents-map/` (the
Agents Map's polar-grid canvas and its child nodes, plus a pure layout-
geometry function and this pass's mock agent data), `api/` (a thin `fetch`
client convention, unused by this story but established for whenever a
later story wires a real backend call), and `styles/` (the approved
prototype's CSS, ported near-verbatim). See "Frontend Application
Architecture", below, for the full tree and reasoning.

`app/business/my_day.py` (REQ-SB-12-US-02, new) is a read-only aggregation
module — composes only `vault_writer` (no other business module, no vault
writes) to build My Day's dashboard summary counts and drill-down lists
from already-captured Email/Meeting notes. `app/api/my_day_router.py`
(new) is the first router outside the `/poc` migration-endpoint family —
My Day is an ongoing feature surface, not a one-off maintenance operation.
See "My Day & Agent Panel APIs", below.

`app/business/agent_registry.py` and `app/business/agent_chat.py`
(REQ-SB-13-US-01, new — see [ADR-011](ADR.md)) hold, respectively, a
small static known-agent registry (settings/available-actions/trigger-
phrases per agent) and the keyword/phrase-matching chat-to-action
mechanism. `app/api/agents_router.py` (new) exposes per-agent settings/
actions/chat-send/history. See "My Day & Agent Panel APIs", below, and
[ADR-011](ADR.md) for the full mechanism reasoning.

`app/business/section_registry.py` and `app/business/provider_registry.py`
(REQ-SB-18-US-01/REQ-SB-19-US-01, new — see [ADR-014](ADR.md)) each own one
new persisted, user-mutable concern (agent Sections; LLM Providers) layered
*alongside* `agent_registry.py`, not inside it — `agent_registry.py` and
`agent_chat.py` are unmodified, and `ADR-011`'s "agent identity/type/actions
stay hardcoded" reasoning is untouched. New `app/api/sections_router.py`
and `app/api/providers_router.py` expose Section/Provider CRUD;
`agents_router.py` gains `PATCH /agents/{agent_id}` for per-agent
reassignment. See "My Day & Agent Panel APIs", below, and
[ADR-014](ADR.md) for the full mechanism reasoning.

`app/business/skill_registry.py` and `app/business/skill_tools.py`
(REQ-SB-27-US-01, new — applies [ADR-015](ADR.md), no new ADR) split the
same way `ADR-015` already resolved: `skill_tools.py` (sibling to
`vault_query_tools.py`) holds the code-registered `@mcp.tool()` skill
capability itself; `skill_registry.py` owns the new persisted,
per-agent skill-*access* concern, composed alongside `skill_tools.py`'s
catalog the same way `section_registry.py`/`provider_registry.py` compose
alongside `agent_registry.py`. New `app/api/skills_router.py` exposes the
skill catalog, per-agent grant/revoke, and a plumbing-only invocation
endpoint. See "Skills Repository — registration & per-agent access",
below.

`app/business/vault_indexing.py` (REQ-SB-01-US-01, new — see
[ADR-024](ADR.md)) is the first module in this codebase to hold a
module-level, in-memory, rebuild-and-swap cache rather than either doing
stateless pass-through I/O (`vault_writer`/`vault_query_tools`) or reading/
writing a `.second-brain/*.json` file (every other cross-request store so
far). New `app/api/vault_index_router.py` exposes the on-demand rebuild
trigger; `app/business/email_classification.py::
run_capture_and_record_completion` gains one unconditional call into it, so
the existing `REQ-SB-07` hourly/app-start scheduler tick refreshes the
index too, with zero changes to `app/scheduling/capture_scheduler.py`
itself. See "Vault Indexing Layer", below, and [ADR-024](ADR.md) for the
full storage/rebuild-shape reasoning.

`app/business/vault_filing_expert.py` (REQ-SB-35-US-01, new — see
[ADR-021](ADR.md)) is the Vault Filing Expert's own placement/write
mechanism, composed by a new `"vault-filing-expert"` `agent_registry.py`
entry (data only) — deterministic-context-injected LLM placement decision,
a generic `vault_writer.write_note`-based Tier-1 write, and a Tier-2
new-top-level-area approval path that bypasses the working-mode gate by
construction, extending (not editing) `ADR-018`'s unedited-by-`ADR-020`
Pending-Approvals schema with an additive `payload` field. `app/data_access/
anthropic_client.py` (REQ-SB-36-US-01, new — see [ADR-022](ADR.md)) is a
plain `anthropic` SDK client, sibling to `compass_client.py`, backing a new
`web_research` entry in `app/business/skill_tools.py`'s catalog; `app/
business/agent_orchestration/mcp_client.py` gains `load_agent_tools(
agent_id)`, closing a live-discovered skill-access tool-binding gap (every
agent's chat previously could reach any registered skill tool
unconditionally). `app/business/agent_orchestration/knowledge_bootstrap.py`
(REQ-SB-36-US-02, new — see [ADR-023](ADR.md)) is the delegated
knowledge-bootstrap chain's own orchestration, composing `ADR-017`'s
`route_cross_section_request`, `ADR-022`'s `skill_registry.invoke_skill`,
and `ADR-021`'s `vault_filing_expert.determine_placement_and_file`
deterministically — the first code path in this project that actually
acts on a Hub-routing match rather than only reporting it. See
"Vault Filing Expert", "Real Anthropic Provider integration & web-research
skill", and "Delegated knowledge-bootstrap orchestration", below (all
under "In-App Agent Orchestration").

## Frontend Application Architecture

`src/frontend` is a Vite + React + TypeScript SPA (ADR-002). This section
describes how its `src/` is structured as pages/features are built on top
of the bare scaffold — see [ADR-010](ADR.md) for the routing/styling/
data-fetching/component-structure decisions this codifies.

### Routing (REQ-SB-12)

`react-router` (v7, declarative mode) drives all page-to-page navigation.
`App.tsx` wraps the tree in `<BrowserRouter>` with three routes: `/` (Agents
Map — the default/home page), `/my-day`, `/settings`. The sidebar's nav
items are `<NavLink>`s; `<NavLink>`'s built-in `isActive` state drives which
nav item renders as active, rather than hand-rolled path comparison.

### Styling

Global plain CSS, ported near-verbatim from the approved
`html-prototype/styles.css`, split by concern under
`src/frontend/src/styles/` (`tokens.css` — the `:root` custom-property
tokens; `shell.css` — `.app-shell`/`.sidebar`/nav/burger-menu; `agents-
map.css` — KB/hub/agent-node/ring/radar classes; `settings.css` plus shared
`.card`/`.badge`/`.btn`/`.input`/`.kv-list` primitives — grown as further
screens are built), imported once, application-wide. Class names are kept
identical to the prototype's own (`.agent-node--worker`, `.hub-node`,
`.kb-node`, `.app-shell`, ...) so components reference exactly the classes
the approved design already validated, with no renaming/translation step.
No CSS Modules, Tailwind, or CSS-in-JS — see [ADR-010](ADR.md) for why.

### Data-fetching

No data-fetching library. A thin `src/frontend/src/api/client.ts` wraps
native `fetch` for whenever a page needs a real backend call. REQ-SB-12-
US-01 itself makes no HTTP call at all — its Agents Map renders local, typed
mock data (`features/agents-map/mockAgents.ts`) mirroring the approved
prototype's 5-agent populated state and its first-run/empty state, since no
"list configured agents" endpoint exists in `src/backend` yet. The exact
route/payload shape for that future endpoint is not decided here — left to
whichever story actually builds it.

### Source structure

```
src/frontend/src/
  main.tsx                     — entry point; mounts <App />
  App.tsx                      — <BrowserRouter> + <Routes>; wraps every
                                  page in <AppShell>
  pages/
    AgentsMapPage.tsx           — default/home route ("/"); composes
                                  <AgentsMapCanvas>
    MyDayPage.tsx                — "/my-day" (REQ-SB-12-US-02; content out
                                  of this story's scope)
    SettingsPage.tsx             — "/settings" (reachability only this
                                  pass; content deferred)
  components/
    shell/
      AppShell.tsx               — persistent layout: <Sidebar> + <main>
      Sidebar.tsx                 — collapsible burger-menu nav, reused by
                                  every page
  features/
    agents-map/
      AgentsMapCanvas.tsx         — the polar-grid SVG background (radar
                                  spokes, rings, boundary, section-
                                  boundaries, Hub->KB spoke-lines, Hub->agent
                                  cluster-lines, ring-label text) plus the
                                  KB/Hub/agent-node children it positions.
                                  section-boundary divider lines are
                                  computed at each pair of adjacent hub
                                  angles' midpoint (REQ-SB-18-US-01,
                                  ADR-014), not 3 fixed positions. Owns the
                                  overview<->drill-down zoom/containment
                                  state (BUGFIX-02-US-01, BUG-002 fix — see
                                  "Agents Map — semantic zoom / drill-down
                                  containment fix", below): a local
                                  `activeSectionId: string | null` plus a
                                  transient zoom-transition flag, driving a
                                  `zooming-out` CSS class + an
                                  `onTransitionEnd` handler (React's
                                  declarative equivalent of the approved
                                  prototype's own CSS-transition +
                                  `transitionend`-listener swap — no new
                                  animation mechanism). When set, renders
                                  `SectionDrilldown` in place of its own
                                  overview markup instead of the prototype's
                                  DOM-hide/CSS-`display:none` toggle.
      KnowledgeBaseNode.tsx        — the central KB element + its brain SVG
      SectionHub.tsx                — one per section, arbitrary N
                                  (REQ-SB-18-US-01: user-created, includes
                                  zero-agent sections), neutral-colored
                                  (ADR-014 — a Section can hold agents of
                                  any Type, so it no longer tints per-Type).
                                  Gains an optional `onActivate` prop
                                  (BUGFIX-02-US-01, BUG-002 fix): when
                                  supplied (the overview's own usage),
                                  renders as a real `<button>` that opens
                                  that section's drill-down; when omitted
                                  (reused as-is inside `SectionDrilldown`),
                                  stays the original non-interactive `<div>`
                                  — one component, two call sites, no
                                  branch-by-view-name prop
      AgentNode.tsx                  — one per configured agent; rendering
                                  only (click-to-open-detail-panel is
                                  REQ-SB-13-US-01's scope); ring placement
                                  still driven by the agent's Type only
                                  (ADR-014 does not touch ring geometry).
                                  Gains two optional props (BUGFIX-02-US-01,
                                  BUG-002 fix): `compact` (applies the
                                  already-present-but-previously-unused
                                  `.agent-node--compact` CSS modifier —
                                  ADR-010's own "scale-to-~100-agents
                                  primitive, defined and ready to apply, not
                                  instantiated" — unconditionally at the
                                  overview level, replacing the never-built
                                  density-threshold branch BUG-002's root
                                  cause made necessary) and `radiusOverride`
                                  (lets `SectionDrilldown` place an agent at
                                  its own fixed drill-down radius instead of
                                  `polarLayout.ts`'s Type-keyed
                                  `RING_RADIUS`, without duplicating
                                  `AgentNode`'s rendering/click-through
                                  logic for a second, drill-down-specific
                                  node component)
      SectionDrilldown.tsx           — NEW (BUGFIX-02-US-01, BUG-002 fix):
                                  one Section's own full-360°, fully-labeled
                                  "Agents Tree" — a Hub (via `SectionHub`,
                                  no `onActivate`, non-interactive; CSS-
                                  scoped narrower via the ported
                                  `.explore-drilldown .hub-node` rule, no
                                  new size prop needed) at the visual
                                  center, that Section's own agents (via
                                  `AgentNode`, `compact` omitted,
                                  `radiusOverride={DRILLDOWN_AGENT_RADIUS}`,
                                  same `onSelectAgent` passed straight
                                  through so click-to-detail keeps working
                                  identically to the overview), Hub->agent
                                  cluster-lines only (no KB, no rings, no
                                  radar — the drill-down's own reduced SVG,
                                  matching the approved prototype's markup),
                                  the already-established `.empty-state`
                                  pattern for a 0-agent Section (no
                                  regression of REQ-SB-18-US-01's Done
                                  empty-Section handling), and a "Back to
                                  Agents Map" control. A same-shape sibling
                                  of `AgentsMapCanvas.tsx`'s own existing
                                  "container composes KB/Hub/agent-node
                                  children" pattern (ADR-010 Decision 4),
                                  one view over — not a new component
                                  pattern.
      AgentDetailPanel.tsx           — settings/actions/chat/history side
                                  panel (REQ-SB-13-US-01); Settings block
                                  gains Section/Provider <select> kv-rows
                                  (REQ-SB-18-US-01/REQ-SB-19-US-01, ADR-014)
      polarLayout.ts                  — pure ring-radius + angle -> {x, y}
                                  geometry (Producer r=30, Expert r=45,
                                  Worker r=50, Hub band r=32, boundary r=58,
                                  KB edge ~r=17 on a 0-100 viewBox);
                                  unchanged by ADR-014 — hub *count*/angle
                                  computation lives in layoutAgents.ts, ring
                                  radii stay Type-driven. Gains
                                  `DRILLDOWN_AGENT_RADIUS = 40`
                                  (BUGFIX-02-US-01, BUG-002 fix) — the
                                  drill-down's own single, Type-independent
                                  ring, co-located with this file's other
                                  geometry constants rather than
                                  hand-derived in a component
      layoutAgents.ts                  — real `GET /agents` + `GET
                                  /sections` -> the {sections, mapAgents}
                                  shape AgentsMapCanvas renders. Section
                                  membership comes from each agent's own
                                  `section_id` (no longer derived from
                                  `type`); N sections' hub angles are spaced
                                  evenly around the full circle, replacing
                                  the fixed 3-entry `SECTION_META`/
                                  `TYPE_TO_SECTION` lookup (REQ-SB-18-US-01,
                                  ADR-014). Gains `layoutSectionDrilldown`
                                  (BUGFIX-02-US-01, BUG-002 fix): takes the
                                  overview's own already-filtered
                                  `MockAgent[]` for one Section and returns
                                  a fresh `MockAgent[]` with new `angleDeg`
                                  values evenly spread across the full 360°
                                  (`idx/n * 360 - 90`, matching the approved
                                  prototype's own `renderSectionTree()`
                                  trigonometry) — a sibling, drill-down-only
                                  geometry function next to `layoutAgents`
                                  itself, not a branch inside it, since the
                                  two views' angular models are genuinely
                                  different (per-Section wedge fan-out vs.
                                  full-circle spread) and conflating them
                                  into one function/one fixed `SECTION_ARC_
                                  SPAN_DEG` constant is BUG-002's own root
                                  cause
      mockAgents.ts                    — shared type definitions only
                                  (`AgentSection`/`MockAgent`); `SectionId`
                                  is a plain `string` and `AgentSection` has
                                  no `type` field as of ADR-014 (arbitrary
                                  user-created sections, no longer 1:1 with
                                  Type)
      agentsApiClient.ts               — `/agents` HTTP calls; gains
                                  `updateAgentAssignment(agentId, {
                                  section_id?, provider_id? })` (`PATCH
                                  /agents/{id}`, REQ-SB-18-US-01/
                                  REQ-SB-19-US-01, ADR-014)
    settings/
      SectionsCard.tsx                — Settings' Sections area
                                  (create/rename/delete), REQ-SB-18-US-01
      ProvidersCard.tsx                — Settings' Providers area
                                  (add/edit/remove, Compass pre-seeded),
                                  REQ-SB-19-US-01
      settingsApiClient.ts             — `/sections` and `/providers` HTTP
                                  calls (list/create/rename-or-edit/delete),
                                  shared by SectionsCard/ProvidersCard and
                                  by AgentDetailPanel (to populate its
                                  Section/Provider picker options) —
                                  REQ-SB-18-US-01/REQ-SB-19-US-01, ADR-014
  api/
    client.ts                    — thin fetch wrapper convention; unused by
                                  this story, established for the first
                                  story that calls a real backend endpoint
  styles/
    tokens.css, shell.css, agents-map.css, settings.css — ported from
    html-prototype/styles.css, imported globally. `agents-map.css` gains
    (BUGFIX-02-US-01, BUG-002 fix) the zoom-transition/drill-down-scoping
    rules already sitting, unused, in `html-prototype/styles.css`'s own
    additive Option-D section (`.explore-zoom-overview`/`.zooming-out`,
    `.explore-drilldown` + its narrower `.explore-drilldown .hub-node`
    scope) — ported now that they are actually instantiated. The
    `.agent-node--compact` rule this file already carries needs no
    porting — ADR-010 already shipped it, unused until this fix applies
    it. The same section's entrance-animation-only rules
    (`.agent-node--intro-move`, `.agents-intro-fade`, `@keyframes
    kbGrowIn`) are **not** ported by this story — see "Agents Map —
    semantic zoom / drill-down containment fix", below.
```

## Agents Map — semantic zoom / drill-down containment fix (BUGFIX-02-US-01, BUG-002)

**No new ADR** — this closes `BUG-002` by porting an already-approved,
already-live-browser-verified prototype design (`html-prototype/
agents-map.html`/`agents-map.js`, "Option D," accepted 2026-08-12 — see
`REVIEW-QUEUE.md`'s "BUG-002 layout exploration" entry for the full
approval history) into the real React components, entirely within
`ADR-010`'s already-`Accepted` component-decomposition shape (container
composes small presentational children, a pure geometry module computes
positions) and `ADR-014` point 6's already-`Accepted` N-section-generic
layout. Nothing here introduces a new tool, framework, state-management
library, or structural boundary — it is ordinary component/prop/function
decomposition, so no ADR is warranted; recorded here (architecture.md, not
ADR.md) purely because there is no other durable home for "why these
specific files/props/functions" once this bugfix story is `Done`.

- **Root cause (confirmed live, not guessed):** `layoutAgents.ts`'s
  `SECTION_ARC_SPAN_DEG = 80` is a fixed angular budget every Section's
  agents fan across, regardless of how many Sections exist (`ADR-014`
  point 6 already made hub angle spacing N-generic, `360/N` per Section)
  or how many agents share one Section — at today's real `N=5` a Section
  only owns 72°, already narrower than the fixed 80° span before any
  agent-count crowding is even considered.
- **The fix changes *rendering density and interaction*, not the
  overview's underlying per-agent polar position.** Every agent still
  renders at `layoutAgents()`'s existing computed `angleDeg`/ring
  position — this bugfix does not touch that fan-out math at all. It
  instead (a) makes every overview agent dot **always** compact/unlabeled
  (`AgentNode`'s existing-but-previously-unapplied `.agent-node--compact`
  modifier, per Option D — not a density threshold, since "always" is
  what makes crowding structurally unable to read as label collision at
  any count) and (b) gives each Section's own Hub a click-to-drill-down
  interaction into a dedicated, full-360°, fully-labeled view of just
  that Section's agents (`SectionDrilldown`, a new sibling component to
  `AgentsMapCanvas`'s existing KB/Hub/agent-node children, per `ADR-010`
  Decision 4's own "separate component per visual concern" shape).
- **State ownership: local to `AgentsMapCanvas.tsx`, not lifted to
  `AgentsMapPage.tsx`.** Unlike `selectedAgentId` (which the page needs,
  to conditionally mount `AgentDetailPanel`), which Section is currently
  drilled into is a concern entirely internal to the map widget — no
  sibling of `AgentsMapCanvas` needs to observe or react to it. Ordinary
  React local `useState`, the same mechanism `AgentsMapPage.tsx` already
  uses for its own state — not a new state-management pattern, and not
  a new architectural question.
- **The click-to-zoom CSS transition is ported (in scope); the flat-row
  entrance animation is not (out of scope, confirmed).** The approved
  prototype's Option D bundles two effects behind one `agents-map.js`:
  the Hub-click zoom-transition (`.explore-zoom-overview`/`.zooming-out`,
  a `transitionend`-driven swap to the drill-down) and a separate,
  independently-toggleable entrance animation (flat-row → circular glide
  on initial load/state-switch/manual replay). Only the former is load-
  bearing for `BUG-002`'s own containment/drill-down defect — the
  story's own Non-Goals already deferred the latter as a polish/motion
  affordance, not a design gap, and its own repro/expected text
  (`BUGS.md`) never mentions entrance motion. Confirmed here, not
  reopened: this story's scope stays exactly what its Non-Goals already
  said. `AgentsMapCanvas.tsx`'s `onTransitionEnd` handler is React's
  declarative equivalent of the prototype's imperative
  `transitionend`-listener + `style.display = 'none'` swap — conditional
  rendering replaces the DOM-hide step, consistent with how this
  codebase's frontend already prefers React's own idioms over a literal
  DOM-manipulation port (`ADR-010`).
- **Geometry: a second, drill-down-only layout function, not a branch in
  the existing one.** `layoutAgents()`'s per-Section wedge fan-out and
  the drill-down's own full-360°-spread-at-a-fixed-radius model are
  genuinely different angular systems — conflating them into one
  function (or one shared constant) is exactly `BUG-002`'s own root
  cause shape (a single fixed span serving two different needs). The new
  `layoutSectionDrilldown()` sits beside `layoutAgents()` in the same
  file, and a new `DRILLDOWN_AGENT_RADIUS` constant sits beside
  `polarLayout.ts`'s existing `RING_RADIUS`/`HUB_RADIUS`/
  `BOUNDARY_RADIUS` — extending the existing "one shared geometry
  module" convention (`ADR-010` Decision 4) rather than hand-deriving
  positions inside a component.
- **Reuse over duplication for `SectionHub`/`AgentNode`.** Both
  components gain small, optional props (`SectionHub`'s `onActivate`;
  `AgentNode`'s `compact`/`radiusOverride`) rather than the drill-down
  growing its own parallel Hub/agent-node components — one interactive-
  vs-non-interactive Hub, one compact-vs-labeled/type-ring-vs-fixed-
  radius agent node, each reused at both call sites. This keeps
  `AgentNode`'s existing `onSelect` click-through to `AgentDetailPanel`
  (`REQ-SB-13-US-01`) working identically in the drill-down with zero
  extra wiring, per the story's own Constraint that this behaviour must
  not regress.
- **No regression of `REQ-SB-18-US-01`'s empty-Section handling.** A
  0-agent Section's drill-down reuses the exact `.empty-state` pattern
  already established elsewhere in this codebase (e.g.
  `AgentsMapPage.tsx`'s own first-run empty state) — not a new empty-
  state component or convention.
- **CSS: port only the load-bearing subset of the prototype's additive
  Option-D styles.** `.explore-zoom-overview`/`.zooming-out`/
  `.explore-drilldown`/`.explore-drilldown .hub-node` are ported into
  `src/frontend/src/styles/agents-map.css` verbatim (class names
  unchanged, per `ADR-010` Decision 3's "no renaming/translation step"
  convention); `.agent-node--intro-move`/`.agents-intro-fade`/
  `@keyframes kbGrowIn` (entrance-animation-only) are not — see the
  Non-Goals point, above.

## Agents Map — Density Clustering (REQ-SB-38-US-01)

**No new ADR** — this locks two previously-flagged-tentative numbers as
final by direct operator decision (`REVIEW-QUEUE.md`'s
"REQ-SB-38-US-01" entry, resolved 2026-08-13: confirm and lock the
prototype's own proposed values, not re-derive them). Both values were
already the prototype's own proposed defaults
(`html-prototype/agents-map.html`'s top-of-file breadcrumb, 2026-08-13
revision), grounded in `layoutAgents.ts`'s existing ring-per-Type geometry
and `BUG-009`'s `SECTION_ARC_SPAN_DEG_CAP`/`SECTION_ARC_SPAN_FRACTION`
precedent — nothing here introduces a new tool, framework, or structural
boundary, so no ADR is warranted; recorded here purely as the durable home
for "why these specific numbers/files."

- **Locked: `VISIBLE_SLOT_CAP = 6`.** A new constant in `layoutAgents.ts`
  (sibling to `SECTION_ARC_SPAN_DEG_CAP`/`SECTION_ARC_SPAN_FRACTION`, same
  "hand-sized against today's real 5-Section/57.6° wedge geometry"
  reasoning, not a computed node-size-vs-arc-length check — that remains a
  deferred follow-up per the story's own Non-Goals). Same class of decision
  as those two existing sibling constants, which also never received an
  ADR — confirmed here, not re-litigated.
- **Locked: clustering scope is per-(Section × Type-ring), not per-Section
  as a whole.** Grounded directly in `layoutAgents.ts`'s own existing
  geometry: an agent's angle is keyed to its Section, its radius to its own
  Type's `RING_RADIUS` (`polarLayout.ts`) — real crowding only happens
  among agents sharing both. Group by `(sectionId, agentType)` before
  applying `VISIBLE_SLOT_CAP`, not by `sectionId` alone. This also
  structurally guarantees a cluster marker never mixes Types (Scenario
  4) — the grouping key makes it impossible by construction, not an added
  check.
- **Cluster overflow placement:** within one (Section × Type-ring) group,
  the first `VISIBLE_SLOT_CAP - 1` agents (existing sort/index order)
  render as ordinary `AgentNode` compact dots at their existing fanned
  positions; the group's LAST fan slot renders one new cluster-marker
  element instead of an `AgentNode` — mirrors the prototype's own "last
  slot becomes the overflow marker" shape exactly.
- **Cluster drill-down reuses `layoutSectionDrilldown()` as-is — no new
  layout function.** That function already accepts an arbitrary
  `MockAgent[]` and spreads it full-360°; it is not internally filtered by
  Section. Calling it with the clustered subset (instead of a whole
  Section's agents) is a direct, zero-modification reuse — the same "one
  shared geometry module" convention `BUGFIX-02-US-01`'s architecture pass
  already established (see above).
- **Click-to-zoom state widens, does not duplicate.**
  `AgentsMapCanvas.tsx`'s existing `zoomTargetSectionId`/`activeSectionId`
  pair (`BUGFIX-02-US-01`, above) currently only ever holds a Section id. A
  cluster marker's click needs a second, distinct identity — mirroring the
  prototype's own `data-section-id="technical-cluster-overflow"`
  convention (deliberately distinct from the Section's own real id, so the
  Section Hub's click target and the cluster marker's click target never
  collide, and Scenario 6 is unaffected). The decomposer/coder own the
  exact shape of that widened state (e.g. a discriminated union, or a
  second id/subset pair) — ordinary component-state design within the
  already-established local-`useState`-on-`AgentsMapCanvas` pattern, not a
  new architectural question.
- **New component, not a new mechanism.** The cluster-scoped drill-down is
  a small sibling to `SectionDrilldown.tsx` (or a generalization of it to
  accept an already-filtered agent list plus a heading), reusing
  `SectionHub`/`AgentNode`/`layoutSectionDrilldown` unchanged — the same
  reuse-over-duplication precedent `BUGFIX-02-US-01` already applied to
  `SectionHub`/`AgentNode`.
- **Cluster-marker visual:** reuses `.map-overflow-marker`, already defined
  in `styles.css`'s "Scale-to-~100-agents pattern" and demonstrated live in
  the prototype — port verbatim, same convention `BUGFIX-02-US-01`'s CSS
  port already followed (no renaming/translation step, `ADR-010` Decision
  3).

## Agent Creation Wizard — entry point, type selector, Expert-type flow (REQ-SB-37-US-01, ADR-030)

This is the first story to make `agent_registry.py` a **mutable, persisted**
concern — see `ADR-030` (supersedes `ADR-011` point 2 only) for the full
mechanism reasoning. This section records the resulting file-level shape.

- **`app/business/agent_registry.py`** — `AGENTS` is renamed `_SEED_AGENTS`
  and is otherwise byte-identical (all 7 shipped agents, same ids, same
  `settings`/`actions`); it stays in code, not migrated into the persisted
  store. A new `_load_state()` (mirrors `section_registry.py`'s shape)
  reads/seeds `.second-brain/agents_registry.json`'s `{"created_agents":
  {}}` shape via two new `vault_writer` primitives,
  `load_agents_registry_state()`/`save_agents_registry_state()` (mirror
  `load_skills_state()`/`save_skills_state()` exactly). `get_agent(agent_id)`
  and `list_agents()` become seed-then-persisted merges (seed agents always
  first, preserving today's existing ordering); `get_action` is unchanged
  in body. New `create_agent(name, type, settings=None) -> dict` derives
  `agent_id` via `vault_writer.tag_slug(name)`, disambiguating on collision
  (`-2`, `-3`, ...) against the union of `_SEED_AGENTS` and `created_agents`
  keys — unlike `create_section`'s idempotent-collapse-on-collision
  semantic, two agent-creation calls must never collapse into one shared
  identity. A created agent's `actions: []` (mirrors the already-`Done`
  `vault-filing-expert`/`compass-expert` "starts empty" precedent) — no
  bespoke-action mechanism is introduced; `REQ-SB-39`'s Skills unification
  remains the only path to a created agent gaining a capability, via the
  already-`Done` `skill_registry.grant_skill_access`, unchanged.
- **`app/api/agents_router.py`** gains `POST /agents` (name, type,
  domain — the Expert-type wizard's own two required fields beyond name),
  calling `agent_registry.create_agent(...)` then returning the same shape
  `GET /agents/{agent_id}` already returns. The wizard's Section selection
  (Scenario 3) is a second, immediate `PATCH /agents/{agent_id}` call
  against the already-`Done` `update_agent_assignment` endpoint — `POST
  /agents` itself does not accept a `section_id`, keeping `agent_registry.py`
  ignorant of Sections exactly as `ADR-014` already established. Every
  other existing `agents_router.py` handler (`GET /agents`,
  `GET /agents/{agent_id}`, `PATCH`, `/chat`, `/history`,
  `/actions/{action_id}`) is unchanged — each already treats
  `agent_registry.get_agent`/`list_agents` as its sole, uncached,
  per-request source of agent identity, so a created agent flows through
  every one of them with zero code change, including Scenario 8's chat/
  history parity (an `actions: []` agent's chat falls straight through
  `agent_chat.handle_chat_message`'s existing no-trigger-phrase-match
  branch into the ordinary `agent_orchestration.run_agent_conversation`
  path, `ADR-015`/`ADR-016`, applying `REQ-SB-33`'s grounding/honest-
  uncertainty `SystemMessage` — confirmed agent-agnostic by direct reading
  of `state.py::history_entries_to_messages`, which is parameterized
  purely by the calling agent's own `name`/`type`, with no per-agent-id
  branching anywhere in the graph).
- **Every already-`Done` self-healing per-agent registry** —
  `section_registry.py`, `provider_registry.py`, `working_mode_registry.py`,
  `skill_registry.py`, `agent_keywords.py` — needs **zero code change**:
  each already iterates `agent_registry.list_agents()` fresh, uncached, on
  every read, so a created agent is picked up (default Section, default
  Provider, default Autonomous working mode, zero granted Skills, empty
  keywords) the instant it exists — the concrete mechanism
  `ESCALATIONS.md` → `ESC-020` identified as needing this ADR at all.
- **Frontend — entry point placed in Settings, not the Agents Map
  canvas** (an architect sequencing call, `ESC-020`'s net-new-design-needed
  point 2, `/design` skipped for this batch per operator direction): a new
  `src/frontend/src/features/agents-map/CreateAgentWizard.tsx` (type
  selector + Expert-type step: name, domain, Section `<select>`) is
  reached via a new "+ Create agent" affordance on `SettingsPage.tsx`,
  mirroring `SectionsCard.tsx`/`ProvidersCard.tsx`'s existing "+ Create
  new …" `<details>` pattern (the closest existing precedent, per the
  story's own Notes) rather than adding a new interactive element to
  `AgentsMapCanvas.tsx`'s already-`Done` semantic-zoom/drill-down surface
  (`BUGFIX-02-US-01`) — keeps this story's frontend scope additive-only
  against Settings' existing card-based CRUD area instead of reopening the
  map canvas's own layout/interaction code. `AgentDetailPanel.tsx` (already
  `Done`, `REQ-SB-13/18/19/21/27`) needs no change — Scenario 6 reuses it
  unchanged for a created agent, since it already renders purely from
  `GET /agents/{agent_id}`'s response shape. `agentsApiClient.ts` gains
  `createAgent({name, type, domain}) -> Promise<Agent>` (`POST /agents`),
  and `settingsApiClient.ts` or the wizard component itself issues the
  follow-up `PATCH /agents/{agent_id}` for Section assignment, reusing the
  already-`Done` `updateAgentAssignment` call. The already-`Done`
  `layoutAgents.ts`/`AgentsMapCanvas.tsx` need no change to surface a
  created agent on the map (Scenario 5) — they already re-fetch
  `GET /agents`/`GET /sections` and lay out whatever `list_agents()`
  returns, with no hardcoded agent count or id list anywhere in that path.

### Amendment — Worker-type flow (REQ-SB-37-US-02, no new ADR)

Additive composition of three already-`Accepted`/already-established
mechanisms — `ADR-030` (this section, above), `ADR-028`/`ADR-029`'s
unified Skills grant surface, and `REQ-SB-29-US-01`'s additive Vault Scope
field. No new persisted state, no new structural boundary, no reversal of
any `Accepted` decision — reopens nothing, so no new ADR is written.

- **`app/api/agents_router.py`'s `POST /agents`** (`ADR-030` point 6,
  `REQ-SB-37-US-01-T03`) — its `type != "expert"` refusal is extended to
  also accept `"worker"`. `domain` becomes optional (`str | None`),
  required only when `type == "expert"`; for a Worker,
  `agent_registry.create_agent(name, "worker", settings=[])` is called
  with no Domain-equivalent setting — a Worker's real configuration
  (Skills, Vault Scope, Section) lives entirely in the three follow-up
  calls below, never in `settings`. Any `type` other than `"expert"`/
  `"worker"` is still refused honestly (`400`), unchanged.
- **Skills step** — calls the already-`Done`, unmodified `skills_router.py`
  endpoint once per selected Skill: `POST /agents/{agent_id}/skills/{skill_id}`
  (`grant_skill_access`, `ADR-028`/`ADR-029`). No new endpoint, no batch
  grant call — the wizard issues one request per selected Skill, mirroring
  how `AgentDetailPanel.tsx`'s own Skills grant/revoke control
  (`REQ-SB-39-US-01`) already calls this endpoint one Skill at a time.
- **Vault Scope + Section step** — a single, combined `PATCH
  /agents/{agent_id}` call carrying both `scope` (`REQ-SB-29-US-01`'s
  additive `AgentAssignmentUpdateBody` field) and `section_id` together —
  `AgentAssignmentUpdateBody` already accepts multiple optional fields per
  request (it does today, for `section_id`/`provider_id`/`keywords`/
  `working_mode`), so this is one `PATCH` call, not two sequential ones the
  way `ADR-030` point 6's original Expert-only flow needed (Expert has no
  Scope field to combine with).
- **Sequencing decision — sequential calls against an already-live
  `agent_id`, never a draft/staged agent record (an explicit alternative,
  considered and rejected):** `create_agent` returns a real, immediately
  `get_agent`-visible record, exactly as it does for Expert (`ADR-030`).
  A draft/pending-finalization agent state was considered and rejected —
  it would introduce a genuinely new structural concern (staged vs. live
  record) that no persisted registry in this codebase has today, and it
  sits against this project's own dominant no-staging-layer posture
  (`MEMORY.md`: no staging/promotion gate on ingested vault data — the
  same "written is usable" philosophy this reasoning extends to a second,
  unrelated concern, agent creation). Scenario 4's "no partial or broken
  agent appears anywhere" requirement is instead met entirely client-side:
  the Worker wizard step validates name + at least one selected Skill + a
  non-empty Vault Scope + a chosen Section are all present **before firing
  any backend call at all**, mirroring `REQ-SB-37-US-01-T04`'s own
  already-established "no call fires on a missing required field" pattern
  (that story's AC-07). No backend rollback/atomicity mechanism is built or
  needed — none exists anywhere else in this codebase's multi-call
  workflows either (e.g. Expert's own `POST` then `PATCH` for Section has
  never had one).
- **Section's own self-healing default does not weaken Scenario 4:**
  `section_registry._load_state()` (`ADR-014`) assigns every agent a
  default Section, including a freshly created one, the instant it exists
  — before the wizard's own `PATCH` call ever fires. Scenario 4's "without
  selecting a Section" is therefore a wizard-level (client-validation)
  requirement, exactly like Expert's own Section field already is (T04) —
  it does not change or reverse Section's existing self-healing
  architecture. Skills and Vault Scope carry no such default
  (`skill_registry.py`'s "deliberately no self-healing default
  assignment"; `scope_registry.py` mirrors `agent_keywords.py`'s own
  empty-by-default shape) — both stay empty until explicitly
  granted/assigned, so the wizard's own required-field validation is the
  only gate for those two fields as well.
- **Frontend** — a new Worker step inside the same `CreateAgentWizard.tsx`
  component `REQ-SB-37-US-01-T04` builds (its `step` state machine gains a
  `'worker'` value alongside `'type'`/`'expert'`), reusing the Expert
  step's Section `<select>` verbatim, a new Skills multi-select sourced
  from `GET /skills` (mirroring `AgentDetailPanel.tsx`'s already-`Done`
  Skills grant/revoke control, `REQ-SB-39-US-01`), and a new Vault Scope
  free-text/comma-separated field mirroring the Keywords row's own pattern
  (per `REQ-SB-29-US-01`'s own Notes). No existing `agentsApiClient.ts`
  function changes beyond `createAgent`'s `type` accepting `'worker'` —
  `updateAgentAssignment` and the Skills grant call are already-`Done`/
  already-additive.

### Amendment — Producer-type flow (REQ-SB-37-US-03, ADR-031)

Resolves the PRD's own previously-unresolved "output action" fork — see
`ADR-031` for the full context and reasoning. Structurally similar to the
Worker-type flow above (`POST /agents` + a Skills-grant step), minus
Worker's Vault Scope/multi-Skill specifics, since a Producer's PRD text
names only "Purpose and Section," plus the operator's own directed
Skills-grant step for the output action.

- **`app/api/agents_router.py`'s `POST /agents`** gains a third `type`
  branch, `"producer"`, alongside `"expert"`/`"worker"` (`ADR-030` point 6's
  original two-type design anticipated exactly one more). A new required
  request-body field, `purpose: str`, is validated non-blank (mirrors
  Expert's `domain` requiredness check) and stored via
  `agent_registry.create_agent(name, "producer", settings=[{"key":
  "Purpose", "value": purpose}])` — the same generic `settings` kv-list
  mechanism Expert's Domain already uses, not a new field on the agent
  record and not Worker's empty-`settings` pattern (`ADR-031` point 3).
  **This story is what actually introduces the first real, persisted
  Purpose value in this codebase** — it does not depend on
  `REQ-SB-41-US-01` (Agent Overview surface, still `Draft`, unbuilt) landing
  first; that story's own still-open "Purpose data source" question is
  narrowed, not closed, by this precedent (`ADR-031` Consequences).
- **Output-Skill step — single-select, reuses the exact Worker-step grant
  call.** The wizard's second step offers a single-select (not Worker's
  multi-select) of exactly one output Skill sourced from `GET /skills`,
  issuing at most one `POST /agents/{agent_id}/skills/{skill_id}` call —
  the identical, unmodified `grant_skill_access` endpoint
  (`ADR-028`/`ADR-029`) `REQ-SB-37-US-02`'s Worker step already calls,
  called here at most once instead of per-checked-item. See `ADR-031`
  point 1 for the cardinality reasoning (PRD's own singular "an output
  action" framing; not a data-model cap — `AgentDetailPanel.tsx`'s existing
  Skills grant/revoke control can still grant a Producer a second Skill
  later, unrestricted, exactly as for any other agent).
- **New placeholder catalog entry, `write-to-vault-draft`** —
  `app/business/skill_tools.py`'s `SKILLS` gains a tenth entry
  (`"mutates": True`), a new `@mcp_server.tool()` stub mirroring
  `diagram_understanding`'s exact honest-unavailable shape, registered in
  `skill_registry.py`'s `_SKILL_HANDLERS`. Seeded so the Producer wizard's
  output-Skill-grant step has at least one real, selectable, honestly-
  labeled entry — mirrors `REQ-SB-27-US-01`'s own "one illustrative stub to
  prove the plumbing" precedent (`ADR-031` point 2). No real write handler
  is built by this pass — invoking it always returns the same honest
  "not yet available" response every other stub Skill in this catalog
  returns.
- **Section step reuses Expert's sequential shape, not Worker's combined
  shape** — a Producer has no Scope-equivalent field to combine with
  Section in one `PATCH`, so the call sequence is `POST /agents` (Purpose in
  `settings`) → grant the selected output Skill → `PATCH
  /agents/{agent_id}` carrying `section_id` alone (`ADR-031` point 4).
- **This story's own current Acceptance Criteria (Scenarios 1–5) cover only
  Purpose + Section** — they predate the operator's resolution of the
  output-action fork and do not yet include a Scenario for granting the
  output Skill. Per the story's own Notes (anticipating exactly this path
  since it has not yet reached `Done`) and `ADR-031` point 5, the decomposer
  amends Scenario 2 (creating a Producer also grants the selected output
  Skill) and adds a missing-output-Skill rejection Scenario as part of
  locking this story's ACs — the mechanism is fully specified above and in
  `ADR-031`; the exact wording is the decomposer's own tightening latitude,
  including whether the output-Skill grant is required or optional at
  submit time.
- **Frontend** — a new Producer step inside `CreateAgentWizard.tsx` (`step`
  state gains a `'producer'` value alongside `'type'`/`'expert'`/`'worker'`),
  reusing the Expert/Worker steps' own Section `<select>` verbatim, a new
  Purpose `<textarea>`/`<input>` (plain controlled input, mirroring Expert's
  Name/Domain field shape — pre-submit draft state, not a live-editing
  panel row), and a new single-select output-Skill control (radio-button-
  equivalent over `GET /skills`, not Worker's checkbox multi-select).
  `agentsApiClient.ts`'s `createAgent`'s `CreateAgentBody.type` union
  already includes `'producer'`; gains a new optional `purpose?: string`
  field. No existing Worker/Expert step code changes.

### Amendment — Popup Modal Redesign, shared `SkillsTree.tsx` extraction, Trigger/Background-Agent composition (REQ-SB-46-US-01, [ADR-039](ADR.md))

Redesigns the wizard's entry point and presentation only — every per-type
`create_agent`/grant/assign call sequence established above is preserved
unchanged (`ADR-030`/`ADR-031` untouched, no reopening). See `ADR-039` for
the full context and reasoning on all four resolved composition questions;
this section records the resulting file-level shape.

- **`src/frontend/src/features/agents-map/CreateAgentWizardModal.tsx`**
  (renamed/restructured from `CreateAgentWizard.tsx`) — a centered popup
  modal (new `.wizard-modal-overlay`/`.wizard-modal` classes, built from
  this codebase's own existing design tokens, deliberately not a reuse of
  `.side-panel-overlay`/`.side-panel`'s own edge-anchored slide-in
  selectors/behavior — Scenario 2's own "distinct from the side panel"
  requirement) with a new `.wizard-step-bar` (steps 1-4, current step
  highlighted). Internal `step` state becomes a 4-step machine
  (`'step1' | 'step2' | 'step3' | 'step4'`), replacing the current
  type-branching 3-form structure; each step's own fields follow the
  story's own confirmed `## Context` field-to-step mapping exactly
  (Step 1: Name/Type/conditional Description(Expert)/conditional
  Scope(Worker)/Section; Step 2: Working-mode selector (all types) +
  conditional Purpose/output-Skill (Producer); Step 3: the new shared
  `SkillsTree.tsx` in `mode="select"`; Step 4: read-only summary + Trigger
  choice + "Create agent"). The existing `handleSubmit`/
  `handleWorkerSubmit`/`handleProducerSubmit` bodies and their exact
  `createAgent` → optional `grantAgentSkill` call(s) → `updateAgentAssignment`
  PATCH sequences are preserved, fired only from Step 4's own "Create
  agent" action.
- **`src/frontend/src/features/agents-map/SkillsTree.tsx`** (new, shared)
  — a presentational, mode-parameterized (`mode: 'manage' | 'select'`),
  collapsible, icon-bearing, Tool-grouped tree over `SkillSummary[]`/
  `AgentCapability[]` (both carrying `REQ-SB-48-US-01-T01`'s new `"tool"`
  field). `mode="manage"` renders `AgentDetailPanel.tsx`'s own
  Grant/Revoke buttons calling the parent's callback immediately
  (`REQ-SB-48-US-01-T02`'s own real usage, unchanged by this amendment).
  `mode="select"` renders checkboxes over an agent-controlled selected-id
  array with no immediate API call (this story's Step 3 usage). Grouping/
  Tool-taxonomy/icon logic (`REQ-SB-48-US-01`'s resolved Outlook/Vault/
  Web/Compass taxonomy, 4 fixed glyph icons) lives once, here.
  `REQ-SB-48-US-01-T02` is the task that originates this file;
  `REQ-SB-46-US-01`'s own Step-3 task carries a real `depends_on:
  REQ-SB-48-US-01-T02` edge (decomposer-assigned) — this codebase's first
  cross-story frontend task dependency (`ADR-039` point 2).
- **`src/frontend/src/pages/AgentsMapPage.tsx`** — gains a new bottom-right
  `.map-fab` button (reuses `.map-overflow-marker`'s own circular
  dashed-border/tinted-glow treatment, `position: fixed` instead of
  map-relative) that mounts `CreateAgentWizardModal.tsx`; on successful
  creation, behaves exactly as today's `onCreated` callback already does
  (refreshes the map).
- **`src/frontend/src/features/settings/CreateAgentCard.tsx`** retired;
  **`src/frontend/src/pages/SettingsPage.tsx`** loses its "+ Create agent"
  mount point entirely (Scenario 1 — sole entry point is now the Map FAB).
- **`src/backend/app/api/agents_router.py`** — `CreateAgentBody` gains one
  additive optional `trigger: str | None = None` field; `create_agent`
  appends `{"key": "Trigger", "value": trigger or "user"}` to each
  type branch's already-built `settings` list uniformly, immediately
  before calling `agent_registry.create_agent(...)` — no per-type
  special-casing, no new endpoint, no new persisted store (`ADR-039`
  point 3). `GET`/`PATCH /agents/{agent_id}` need no change — `Trigger`
  reads back through the existing `settings` passthrough exactly like
  `Domain`/`Purpose` already do.
- **`src/frontend/src/features/agents-map/agentsApiClient.ts`** —
  `CreateAgentBody` gains an additive optional `trigger?: string` field,
  mirroring `domain?`/`purpose?`.
- **Background-Agent toggle** — explicitly NOT added to this story's scope
  (`ADR-039` point 4); `REQ-SB-51-US-01`'s own deferred-to-a-future-story
  reasoning stands unchanged.

## My Day & Agent Panel APIs (REQ-SB-12-US-02, REQ-SB-13-US-01)

Both features follow the existing `api → business → data_access` layering
(ADR-003) exactly — no new layer, no new trigger source. Neither wires up a
frontend page itself; both settle the backend surface a later frontend
task calls, the same "backend surface now, frontend wiring next" split
already used across this codebase's earlier stories.

### My Day dashboard & drill-downs (REQ-SB-12-US-02)

- **New router `app/api/my_day_router.py`**, `APIRouter(prefix="/my-day")`,
  registered in `app/main.py` alongside `health_check_router`/
  `email_poc_router`. This is the first router outside the `/poc`
  migration-endpoint family — `/poc/...` names a one-off maintenance
  operation (backfills/retrofits/migrations); My Day is an ongoing feature
  surface a user visits repeatedly, not a migration, so it does not belong
  under `/poc`.
  - `GET /my-day/summary` → `{"emails": {"count": int}, "calendar":
    {"count": int}, "todo": {"count": 0}}` (Scenarios 1, 2). The frontend
    derives "show a count" vs. "nothing captured yet" purely from whether
    `count == 0` — there is no separate has-a-pipeline-ever-run flag. A
    section that ran and genuinely found zero items today is
    indistinguishable from one that has never run; nothing in this story's
    ACs requires telling those two apart, so adding a flag to distinguish
    them would be unrequested surface.
  - `GET /my-day/emails` → `[{"subject": str, "sender": str, "customer":
    str | null}]` (Scenarios 4, 5). `customer` is `null` when the note's
    `customer` frontmatter is `"Unsorted"` or absent — reusing
    `vault_writer.list_known_customers()`'s existing `!= "Unsorted"`
    convention for "not really classified" rather than inventing a second
    one; the frontend renders "unclassified" for `null`.
  - `GET /my-day/calendar` → `[{"subject": str, "start": str, "customer":
    str | null}]` (Scenarios 6, 7) — same `customer` convention as Emails.
    Backed by `Work/Meetings/` notes (REQ-SB-08's resolved schema); since
    REQ-SB-08 is not yet `Done`, `Work/Meetings/` does not exist in the
    real vault yet, so this list resolves to `[]` today with no
    special-casing needed — the same "kind folder doesn't exist yet"
    handling `list_all_note_paths()` already has.
  - `GET /my-day/todo` → always `[]`, hardcoded, no vault read at all
    (Scenario 8). REQ-SB-09's task source and kind-folder name are still
    unresolved (this story's own Non-Goals) — guessing a folder name to
    glob against would itself be exactly the kind of material assumption
    this story explicitly declined to make. Replace the hardcoded `[]`
    with a real read once REQ-SB-09 resolves its schema; not this story's
    or this pass's job.
- **New business module `app/business/my_day.py`** — read-only
  aggregation. `list_email_items()` / `list_calendar_items()` both call
  one shared helper that reads every note under a given kind folder and
  projects it down to the response's whitelisted fields; `todo` is not
  routed through this helper at all, per the point above.
- **New `vault_writer.py` primitive, `list_notes_in_kind_folder(kind:
  str) -> list`**, mirroring `list_all_note_paths()`'s exact existing
  shape (`work_root / kind`, glob `*.md`, sorted, `[]` if the kind folder
  doesn't exist) but scoped to one kind folder — avoids reading and
  discarding every Customer/Person/Partner/Notification/File note just to
  filter down to Emails/Meetings. A same-shape extension of an existing
  read-only primitive, not a new pattern.
- **No ADR.** A straight extension of already-`Accepted` structural
  decisions (ADR-003's layering; the one-module-per-feature `business/`
  shape already established by `tag_backfill.py`/`customer_hub_linking.py`/
  `people_extraction.py`; a `vault_writer` read primitive mirroring an
  existing one's shape exactly) — no new tool, framework, storage
  mechanism, or trust-surface decision, and nothing here contradicts any
  Accepted ADR, the PRD, or a `MEMORY.md` constraint.

#### Amendment — rolling 7-day window date-filtering (REQ-SB-22-US-01)

As shipped for REQ-SB-12-US-02, `list_email_items()`/`list_calendar_items()`
returned **every** note ever written under their kind folder, unfiltered by
date — there was no "only today," "only this window," or any other
date-scoping in the read path at all. REQ-SB-22-US-01 is the first story to
add date-range filtering to My Day's read path. Filtering is applied
**backend, at query time**, inside `app/business/my_day.py` — not
client-side over an already-fetched full list — because the unfiltered list
this endpoint already returns only grows over time (every note ever
captured), so pushing the full set to the browser on every request and
filtering there does not scale and duplicates the date-window logic on both
sides of the HTTP boundary for no benefit; the endpoints exist specifically
so the frontend never has to reason about vault-note shape itself.

- `GET /my-day/emails` response shape gains one field: `[{"subject": str,
  "sender": str, "customer": str | null, "received": str}]` — `received` is
  the note's existing `received` frontmatter field (written by
  `email_classification.py`), now surfaced for the first time; not a new
  data source, an existing captured field the response previously omitted
  (`architecture.md`'s own Constraints note, carried from the story). Both
  `/my-day/emails` and `/my-day/calendar` now return only items whose date
  field falls inside the current 7-day window (3 days before today through
  3 days after today) — items outside the window are excluded from the
  list entirely, not flagged or dimmed.
- `GET /my-day/summary` counts (`emails.count`, `calendar.count`) are
  derived from the same windowed lists (`len(list_email_items())`/
  `len(list_calendar_items())`, unchanged internally) — so the dashboard's
  counts and each drill-down's own item count are always consistent by
  construction, never two separately-computed numbers.
- **"Today" is computed backend-side, once per request, from the app/server
  host's local clock** (`datetime.now()` — naive local time, no timezone
  library, no per-user timezone preference; single-user, single-host app,
  per this story's own Non-Goals) — never a client-supplied or cached
  value. Both drill-down pages already re-fetch their list on every page
  visit (`useEffect` with an empty dependency array, `MyDayEmailsPage.tsx`/
  `MyDayCalendarPage.tsx`), which is what makes the window advance
  automatically as days pass (Scenario 4) with zero additional
  polling/refresh mechanism — a plain page reload already recomputes
  "today" on the backend.
- Each note's date field (`received` for Emails, `start` for Meetings) is
  an ISO-8601-prefixed string (`YYYY-MM-DD...`); the window comparison
  uses the first 10 characters (the calendar date) against the computed
  window's own `YYYY-MM-DD` bounds, string-compared — ISO date strings
  sort/compare correctly as plain strings, the same `received[:10]`/
  `start[:10]` slicing precedent `email_classification.py` and
  `vault_writer.meeting_note_filename_stem()` already use elsewhere in this
  codebase. No `datetime.fromisoformat()` parsing/timezone conversion is
  introduced by this pass.
- Frontend changes are additive only, within the already-`Done`
  `MyDayEmailsPage.tsx`/`MyDayCalendarPage.tsx`/`features/my-day/client.ts`:
  `MyDayEmailItem` gains a `received: string` field, rendered in the
  existing `.item-row-meta` line (Calendar already renders `start` there
  today, unchanged). No new component, region, or route — the same flat
  `.item-list`/`.item-row` pattern, narrowed by a smaller, already-filtered
  response instead of a client-side filter step.
- **Still no ADR.** Same reasoning as the original REQ-SB-12-US-02 pass
  above: a query-time filter added inside an existing `business/` module,
  behind an already-`Accepted` `api → business → data_access` layering
  (ADR-003), with no new tool, framework, storage mechanism, endpoint
  contract *shape* (only an additive field and a narrower result set), or
  trust-surface decision. Nothing here contradicts any `Accepted` ADR, the
  PRD, or a `MEMORY.md` constraint.

#### Amendment — Compass-judged email importance filtering (REQ-SB-30-US-01)

My Day's Emails list (drill-down + dashboard count) narrows further: from
"every captured Email note inside the window" to "every captured Email
note inside the window that Compass judged important." This threads
through three already-`Accepted` layers — the capture-time Compass call,
the vault frontmatter serialization primitive, and My Day's own read
path — as an ordinary same-shape extension of each; no new layer, tool,
or storage mechanism, so **no new ADR** (see "No ADR" note at the end of
this amendment).

- **Capture-time judgment: one more key on the existing `classify_email`
  JSON object, not a second Compass call.** `app/data_access/
  compass_client.py::classify_email`'s prompt already classifies one
  email along two axes (`customer`, `kind`) in a single JSON response;
  this amendment adds a third axis, `important` (boolean), to the same
  prompt and the same response object — one more paragraph in the same
  voice as the existing CUSTOMER/KIND instructions ("IMPORTANT — whether
  this specific email genuinely needs the recipient's attention: a direct
  ask, a real back-and-forth needing a response or decision,
  time-sensitive information, or something from a real customer/company
  relationship; not a notification, automated alert, FYI, newsletter, or
  routine share notification — reason about the actual content, not
  sender or keyword"), and one more key in the response JSON template
  (`"important": <true|false>`). `classify_email`'s return dict gains
  `"important": bool(parsed.get("important", True))` — defaulting to
  `True` even for a *parseable* response that happens to omit the key,
  the same fail-open posture applied one step earlier than the "field
  missing on read" case below. No new HTTP round-trip, no new Compass
  endpoint, no new parsing path beyond one more dict key — the same
  reasoning `email_classification.py`'s own docstring already gives for
  why `customer`+`kind` share one call.
  `app/business/email_classification.py::classify_recent_emails`'s
  written frontmatter dict gains one key, `"important":
  classification["important"]`, alongside the existing `customer`/`kind`/
  `classification_confidence` keys — same write, same call site, no new
  code path. **Failure mode unchanged:** `classify_email` raising
  `CompassError` is already caught per-email by `classify_recent_emails`
  before any note is written for that email (the whole note is skipped,
  an error result recorded) — a Compass failure can never produce a note
  with a fabricated `important` value, satisfying Scenario 6 with zero
  additional error-handling code.
- **Frontmatter boolean round-trip — a real gap this is the first story
  to hit, fixed in `app/data_access/vault_writer.py`, not worked around
  in `business/`.** `important` is the first-ever boolean frontmatter
  field in this codebase. `_format_frontmatter_value`'s existing fallback
  (`str(value)`) would serialize Python's `True`/`False` as the *literal
  strings* `"True"`/`"False"` (capitalized, not valid lowercase
  YAML/Obsidian boolean syntax), and `_parse_frontmatter_value` has no
  matching read-side conversion — reading the note back would return the
  *string* `"False"`, which is truthy in Python, silently defeating the
  entire filter (an email marked not-important would still evaluate as
  important on every subsequent read). Confirmed by direct reading of
  both functions, not assumed. **Fix, scoped to these two functions
  only:** `_format_frontmatter_value` gains an `isinstance(value, bool)`
  branch (checked before the generic fallback — `bool` is not `str`, so
  the existing `isinstance(value, str)` branch does not already catch
  it) writing lowercase `true`/`false`; `_parse_frontmatter_value` gains
  a matching `raw == "true"` / `raw == "false"` check (after the existing
  quoted-string check, before the generic passthrough) returning real
  `True`/`False`. A one-time-forward-compatible, surgical fix to an
  existing `data_access` primitive — not a new serialization format, not
  a migration (every other frontmatter value already written is a string
  or number and round-trips unchanged through the new branches, which
  only ever match the literal tokens `true`/`false`).
- **My Day read path: fail-open filter, plus a new `captured_count` for
  the two-empty-states distinction — additive only, no endpoint shape
  break.** `app/business/my_day.py::list_email_items(day)` gains one more
  condition after the existing window check:
  `frontmatter.get("important", True)` — a genuinely absent field (an
  email captured before this story, not yet backfilled) or an explicit
  `True` is shown; only an explicit `False` is excluded. This is the
  general-case fail-open behavior the story's own Notes record (not just
  the retrofill-window special case, below). `list_email_items`'s
  response shape is unchanged (`[{"subject", "sender", "customer",
  "received"}]`) — same "additive field or narrower result set, never a
  reshape" precedent as the REQ-SB-22-US-01 amendment above. To
  distinguish Scenario 4 ("captured but filtered out") from Scenario 5
  ("nothing captured at all") without reshaping `GET /my-day/emails`
  itself, `summary()`'s `emails` object gains one additive field:
  `{"count": int, "captured_count": int}` — `count` stays
  `len(list_email_items(day))` (post-importance-filter, unchanged
  meaning), `captured_count` is the same window-scoped count *before* the
  importance filter (every Email note inside the window regardless of
  `important`). The frontend empty-state decision
  (`MyDayEmailsPage.tsx`, T03's scope) is then a pure comparison of the
  two counts already available from `GET /my-day/summary` (which the
  page already needs to fetch, or now additionally fetches, alongside
  `GET /my-day/emails`) — `captured_count > 0 && count === 0` renders
  Scenario 4's "captured but filtered" copy, `captured_count === 0`
  renders Scenario 5's existing "nothing captured yet" copy. No new
  endpoint. `list_calendar_items`/the Calendar drill-down are untouched —
  REQ-SB-30 is Emails-only per the story's own Non-Goals.
- **Retrofit: scoped to the ~22 in-window emails only, reusing My Day's
  own window definition — not a full-181-note batch.** A new function,
  living in `app/business/email_classification.py` alongside
  `classify_recent_emails` (the module that already owns the Compass
  email-classification call and the frontmatter-write path this retrofit
  extends), iterates only `Work/Emails/` notes whose `received` falls
  inside `my_day._compute_window()`/`_within_window()` — reusing My Day's
  own window functions directly (the same cross-module reach
  `my_day_router.py::_validate_day` already established for
  `my_day._compute_window()`) so "in window" here can never drift from
  what My Day itself means by it. **Idempotent**, mirroring
  `retrofit_customer_hub_links`/`retrofit_people_from_emails`'s exact
  shape: a note that already carries an `important` key is skipped
  (`status: "already_classified"`), never re-classified. For each
  still-unclassified in-window note, it calls
  `compass_client.classify_email` with that note's own already-stored
  `subject`/`sender_email`/body (read via `vault_writer.read_note`,
  which already returns the note's own body text) and writes **only**
  the resulting `important` value back — the same-call `customer`/`kind`
  judgment is deliberately discarded; this is an importance backfill,
  not a re-classification, so a note's already-filed `customer`/`kind`
  can never drift from a retrofit rerun. Writing the single new key
  reuses `insert_tags_line`'s existing "surgical single-line insert just
  before the closing `---`" shape in `vault_writer.py` — either a small
  new sibling primitive (e.g. `insert_frontmatter_field(path, key,
  value)`, generalizing `insert_tags_line`'s body to one arbitrary key)
  or a narrow `important`-specific variant is implementation latitude
  left to the decomposer/coder, not an architectural fork; either way it
  is additive to `vault_writer.py`, not a rewrite of `insert_tags_line`
  itself. A note whose Compass call errors during the retrofit is left
  with no `important` field at all (`status: "skipped_compass_error"`),
  never a fabricated value — `list_email_items`'s own fail-open default
  then shows it, exactly the general-case behavior described above.
  Exposed the same way every existing retrofit is — a new
  `POST /poc/retrofit-email-importance` endpoint in
  `app/api/email_poc_router.py`, matching `retrofit_customer_hub_links_endpoint`'s
  existing response-shape convention (`{"notes_checked", "<verb>ed", "results"}`).
- **No ADR.** Every piece above is an ordinary, same-shape extension of
  already-`Accepted` structural decisions: the capture-time Compass call
  (one prompt, one response object, one more key — the mechanism ADR-015
  point "Model integration" explicitly left `compass_client.py`'s
  existing linear-pipeline shape untouched by *that* pass, and this
  amendment does not reopen or contradict that framing, since
  `classify_email` remains the one fixed-shape function called only by
  the linear email-classification pipeline, unedited in kind — only
  extended in the number of keys it returns); the `data_access`
  frontmatter-serialization primitive (a bugfix-shaped extension for the
  first boolean field, not a new storage format); the `my_day.py`
  query-time filter and additive `summary()` field (identical reasoning
  to the REQ-SB-22-US-01 amendment directly above — no new endpoint
  contract shape, only an additive field and a narrower result set); and
  the retrofit (the exact one-module-per-maintenance-operation,
  idempotent, `/poc`-exposed shape already established by
  `retrofit_customer_hub_links`/`retrofit_people_from_emails`/
  `retrofit_email_sender_links`). No new tool, framework, storage
  mechanism, or trust-surface decision; nothing here contradicts any
  `Accepted` ADR, the PRD, or a `MEMORY.md` constraint.

#### Amendment — To-Do real data replaces the hardcoded-0 stub (REQ-SB-09-US-01)

`GET /my-day/todo` moves from "always `[]`, hardcoded, no vault read at
all" (REQ-SB-12-US-02's own deliberate placeholder — see that section's
own bullet, above) to a real read over `Work/Tasks/` notes, now that
REQ-SB-09 has resolved the Task source/schema/kind-folder question the
original placeholder was explicitly waiting on. Same shape as the
REQ-SB-22-US-01/REQ-SB-30-US-01 amendments above — an ordinary extension
of already-`Accepted` `my_day.py` structure, not a new one.

- **New `app/business/my_day.py::list_todo_items()`**, mirroring
  `list_email_items()`/`list_calendar_items()`'s existing shape exactly:
  reads every note under `vault_writer.list_notes_in_kind_folder("Tasks")`,
  projects down to `[{"subject": str, "customer": str | null, "due": str |
  null}]`. `customer` follows the same `_customer_or_null` convention
  already shared by Emails/Calendar. **Filters to still-open tasks only**
  (`frontmatter.get("status") != "Completed"`) — Scenario 8's own text
  ("lists each still-open captured task"); a completed task is still a
  real, captured Task note (Scenario 5), it is simply excluded from this
  particular read projection, the same "captured but filtered" shape
  REQ-SB-30-US-01's `important` filter already established for Emails (no
  `captured_count`-style second field is needed here, since no AC asks
  this pass' empty state to distinguish "nothing captured" from "captured
  but all complete" the way REQ-SB-30 needed to for importance-filtering).
  **No date-window filtering** — unlike `list_email_items`/
  `list_calendar_items`'s rolling-7-day window (REQ-SB-22-US-01), a Task
  has no natural "occurred near now" framing (mirroring
  `list_outlook_tasks`'s own no-date-window design, [ADR-027](ADR.md)); a
  far-future or undated task stays listed until it is completed, not until
  it ages out of a window.
- **`summary()`'s `todo` object** moves from the hardcoded `{"count": 0}`
  to `{"count": len(list_todo_items())}` — internally unchanged shape,
  now naturally reflecting real data, mirroring how `emails`/`calendar`
  already compute their own counts from their own list functions.
- **`GET /my-day/todo` response shape** is unchanged from
  `REQ-SB-12-US-02`'s own originally-declared placeholder shape
  (`[{"subject", "customer", "due"}]`) — the endpoint contract itself was
  already correctly speculated even before this story resolved what would
  actually populate it; only the underlying data source changes, from a
  hardcoded empty list to a real read.
- **No ADR.** A straight extension of already-`Accepted` structural
  decisions — the same `api → business → data_access` layering (ADR-003),
  the same `list_notes_in_kind_folder` primitive Emails/Calendar already
  use, and no new endpoint contract shape (the response shape was already
  declared, just previously unpopulated). Nothing here contradicts any
  `Accepted` ADR, the PRD, or a `MEMORY.md` constraint — the capture-side
  half of this same story (the Tasks-folder read pipeline itself) is what
  needed [ADR-027](ADR.md); this read-path half does not.

### Agent detail panel — settings, actions, chat, unified history (REQ-SB-13-US-01, see [ADR-011](ADR.md))

- **New router `app/api/agents_router.py`**, `APIRouter(prefix="/agents")`,
  registered in `app/main.py`:
  - `GET /agents/{agent_id}` → `{"id", "name", "type", "settings":
    [{"key", "value"}], "actions": [{"id", "label"}]}` (Scenario 1).
  - `POST /agents/{agent_id}/actions/{action_id}` → triggers that action's
    registered handler synchronously (the Available Actions buttons —
    the direct-trigger surface, alongside chat, per the story's own
    Constraints), appends a `run_event` history entry, returns
    `{"status": "ok" | "error", "message": str}`.
  - `POST /agents/{agent_id}/chat` → body `{"message": str}` (Scenarios 2,
    7): matches the message against the agent's known action
    trigger-phrases (mechanism: [ADR-011](ADR.md)); on a match, invokes
    the same handler the direct-action endpoint would, appends both a
    `chat` and a `run_event` history entry, and replies confirming what
    was done; on no match, replies with a canned, honestly
    non-conversational fallback listing that agent's available actions.
    Returns `{"reply": str, "action_triggered": str | null}`.
  - `GET /agents/{agent_id}/history` → the unified chronological list
    (chat + run events merged) — Scenarios 3, 3b, 4.
- **New `app/business/agent_registry.py`** — a small, static, hardcoded
  dict of known agents (id/name/type/settings/actions + trigger-phrases),
  keyed by the same `data-agent-id` values the approved prototype and
  `REQ-SB-12-US-01`'s planned `mockAgents.ts` already use
  (`email-capture`, `meeting-capture`, `todo-capture`, `people-producer`,
  `vault-qa`). **Deliberately not vault-derived**, unlike
  `list_known_customers`/`list_known_kinds` — full reasoning: ADR-011.
  Only `email-capture`'s `run_capture_now` action has a real handler this
  pass, wired to the already-`Done` `email_classification.
  run_capture_and_record_completion` — the only capture pipeline that
  actually exists today. Every other declared action (Meeting/To-Do
  Capture's "Run capture now", People Notes' "Rebuild a person note",
  Vault Q&A's actions) has no handler this pass — invoking one (button or
  chat) returns an honest `status: "error"`/"not yet available" response,
  not a fabricated success. This story does not invent functionality for
  REQ-SB-08/09/03's own not-yet-built pipelines.
- **New `app/business/agent_chat.py::handle_chat_message(agent_id,
  message) -> dict`** — the keyword/phrase-matching mechanism itself.
  Full reasoning: ADR-011.
- **New `vault_writer.py` primitives, `append_agent_history_entry(agent_id:
  str, kind: str, text: str) -> None` / `load_agent_history(agent_id: str)
  -> list[dict]`**, backed by a new `.second-brain/
  agent_communication_history.json` (one file, `{agent_id: [{"kind":
  "chat_user" | "chat_agent" | "run_event", "text": str, "timestamp":
  iso8601}, ...]}`) — extends the existing `.second-brain/` flat-JSON-
  file state convention (`processed_email_ids.json`,
  `conversation_index.json`, `last_capture_run.json`) to a fourth concern,
  not a new storage mechanism. `email_classification.
  run_capture_and_record_completion` gains one additional call,
  `vault_writer.append_agent_history_entry("email-capture", "run_event",
  ...)`, alongside its existing `record_capture_run_completed()` call —
  so a capture run started by the hourly scheduler, the app-start
  trigger, `/poc/classify-emails`, or this story's new action/chat
  triggers all produce the exact same history entry, through the one
  shared entry point already established by ADR-005/ADR-008.

### Agent Overview surface — new default-landing tab, Purpose/Scope/Guardrails/Working-mode summary (`REQ-SB-41-US-01`, see [ADR-033](ADR.md))

Resolves the operator's own "opens straight to Chat... need an Overview...
before I can chat with it" complaint by making Overview the panel's new
default-landing tab, not a bolt-on region reached only after Chat.
`/design` was explicitly skipped for this batch (operator-directed); the
navigation-shape and Purpose-data-source decisions below are this pass's
own architectural call, not a prototype port — full reasoning: `ADR-033`.

- **Navigation — `AgentDetailPanel.tsx`'s `TABS` gains `'overview'`,
  first in the array.** Final tab order: `['overview', 'chat', 'history',
  'settings', 'gaps']` — `'gaps'` stays exactly as `ADR-032` decided it
  (conditionally present only for `agent.type === 'expert'`). `activeTab`'s
  initial state and its reset-on-agent-switch value both change from
  `'chat'` to `'overview'`. No other tab's own content, route, or behavior
  changes — Chat is one click away, functionally identical to today.
- **Purpose region — reads the existing `settings` kv-list, no new field,
  no new endpoint.** Looks for a `"Purpose"` entry first, then a
  `"Domain"` entry, in `GET /agents/{agent_id}`'s existing `settings`
  array; shows whichever is found first. If neither key exists, shows an
  honest `"No stated purpose recorded for this agent."` string — never a
  fabricated or Skills/Scope-derived summary. Composes `ADR-030` point 5 /
  `ADR-031` point 3's existing Expert-Domain/Producer-Purpose mechanism
  directly; no new field is added to the agent record.
- **Backfill — all 7 shipped agents (`email-capture`, `meeting-capture`,
  `todo-capture`, `people-producer`, `vault-qa`, `vault-filing-expert`,
  `compass-expert`) gain one additive `{"key": "Purpose", "value": "..."}`
  settings entry each**, appended to their existing static `settings` list
  in `agent_registry.py`'s seed dict (append-only per entry, nothing
  existing edited/reordered). Draft copy for all 7: `ADR-033` point 3a.
  This is a static-seed-data edit only — it does not touch `create_agent`
  or any of `REQ-SB-37-US-02-T01`'s already-`Ready`, already-locked
  "Worker's `create_agent` call MUST pass `settings=[]`" constraint, which
  governs the runtime wizard-creation path only. A Worker (or any agent)
  created after this pass via the wizard with no Purpose/Domain entry
  shows the same honest "No stated purpose recorded" state above — never a
  display-time-derived summary.
- **Scope region** reads `GET /agents/{agent_id}`'s existing `"scope":
  [...]` field (`REQ-SB-29-US-01`, already additive on this same
  endpoint) — a real assigned value once one exists (Scenario 5), or an
  honest "no scope assigned" state for an empty list (Scenario 6, real for
  every agent today since `REQ-SB-29-US-01` remains unbuilt). No new field.
- **Guardrails region** is a static, non-configurable informational
  sentence describing `REQ-SB-33-US-01`'s already-live grounding/honest-
  uncertainty guardrail — the same text for every agent, sourced from no
  API field at all (the guardrail itself has no per-agent toggle to read).
  Unchanged by this pass.
- **Working-mode region** reads `GET /agents/{agent_id}`'s existing
  `"working_mode"` field (`REQ-SB-21-US-01`, already-`Done`), the same
  value the Settings tab's own `kv-list` row already shows. No new field.
- **Open-knowledge-gap count (Expert-type agents only)** — composes
  `ADR-032`'s existing `GET /agents/{agent_id}/knowledge-gaps` endpoint's
  `open_count` field, no new endpoint or business-layer function. Rendered
  as a one-line summary with a link that switches `activeTab` to the
  existing `'gaps'` tab, gated identically to it. Has a real,
  sequencing-only build dependency on `REQ-SB-40-US-01`'s endpoint landing
  first; the rest of this section's regions do not.
- **Frontend** — a new `AgentOverviewTab.tsx` (or an inline
  `activeTab === 'overview'` branch inside `AgentDetailPanel.tsx`, exact
  file split is decomposer/coder latitude) renders the four required
  regions plus the conditional gap-count line, composing only fields
  `GET /agents/{agent_id}` (and, for the gap count,
  `GET /agents/{agent_id}/knowledge-gaps`) already returns — no new
  backend endpoint anywhere in this section.

Full reasoning, every alternative considered, and every consequence:
[ADR-033](ADR.md).

### Agent Sections & LLM Providers — mutable, persisted agent configuration (REQ-SB-18-US-01, REQ-SB-19-US-01, see [ADR-014](ADR.md))

Both stories give the user runtime, restart-surviving control over two new
per-agent properties — which Section an agent belongs to, and which LLM
Provider it uses — **without** making `app/business/agent_registry.py`
itself mutable. `ADR-011` point 2's reasoning ("which agents exist is
app/deployment configuration, not vault content") is preserved exactly:
`agent_registry.py` and `agent_chat.py` are untouched by this pass. Section
and Provider are two new, independent, persisted concerns composed
*alongside* the static registry, not inside it.

- **Two new sibling `.second-brain/` state files**, extending the existing
  flat-JSON-file convention to a fifth and sixth concern:
  - `.second-brain/agent_sections.json` — `{"sections": [{"id", "name"}],
    "assignments": {<agent_id>: <section_id>}}`. `id` is a slug
    (`vault_writer.tag_slug(name)`) fixed at creation and never
    regenerated on rename, so a rename only ever updates `name` in place —
    every existing `assignments` entry stays correct automatically
    (REQ-SB-18 Scenario 3's "the rename does not change assignment," true
    by construction).
  - `.second-brain/agent_providers.json` — `{"providers": [{"id", "name",
    "endpoint", "credential", "model"}], "assignments": {<agent_id>:
    <provider_id>}}`. Same slug-id-stable-across-edit shape.
  - `app/data_access/vault_writer.py` gains the paired
    `load_sections_state()`/`save_sections_state()` and
    `load_providers_state()`/`save_providers_state()` primitives — pure
    JSON I/O, no business rules, mirroring every existing state-file
    primitive's shape (`load_processed_email_ids()`/`mark_email_processed`,
    etc.).
- **Two new business modules own seeding, self-healing default assignment,
  CRUD, and the block-until-unused check:**
  - `app/business/section_registry.py` — seeds the starting 5 sections
    (Technical, Sales, Productivity, Customers, Products, per the PRD
    breadcrumb) on first read, persisting immediately; any known agent
    (`agent_registry.list_agents()`) absent from `assignments` is
    self-healingly assigned to the first section in creation order
    (`"technical"`) and persisted. Exposes `list_sections()`,
    `create_section(name)`, `rename_section(section_id, name)`,
    `delete_section(section_id) -> {"deleted": bool,
    "blocked_by_agent_ids": [str]}`, `get_agent_section(agent_id)`,
    `set_agent_section(agent_id, section_id)`.
  - `app/business/provider_registry.py` — seeds the pre-populated
    "Compass" Provider entry on first read, reading `app.config.settings.
    compass_base_url`/`compass_api_key`/`compass_model` once; any known
    agent absent from `assignments` is self-healingly assigned
    `"compass"`. Exposes the equivalent `list_providers()`,
    `create_provider(...)`, `update_provider(provider_id, ...)` (an
    omitted `credential` leaves the stored value untouched),
    `remove_provider(provider_id) -> {"deleted": bool,
    "blocked_by_agent_ids": [str]}`, `get_agent_provider(agent_id)`,
    `set_agent_provider(agent_id, provider_id)`, and
    `has_real_client(provider_id) -> bool` (a small hardcoded set,
    `{"compass"}`, mirroring `ADR-011` point 3's "declared but not yet
    backed by a real handler" pattern one layer up).
  - **The pre-seeded "Compass" Provider entry is a CRUD-editable
    representation only — editing it from Settings does not change the
    live Compass call path.** `app/data_access/compass_client.py`
    continues reading `app.config.settings.compass_*` directly and
    unconditionally, per REQ-SB-19's own Non-Goal against touching that
    `.env`-sourced mechanism, and per Scenario 6 ("no change in
    behaviour, endpoint, or credential used"). A known, explicit
    limitation for this pass, not a silent gap — see `ADR-014`.
  - Neither module imports the other; both import `agent_registry` only
    (to enumerate known agent ids) — the same "one business module
    composing another" shape already established
    (`people_extraction.py` → `customer_hub_linking.py`;
    `meeting_classification.py` → `people_extraction.py`).
- **Composition happens at the router, not inside `agent_registry.py`.**
  `app/api/agents_router.py`'s `GET /agents` and `GET /agents/{agent_id}`
  call `agent_registry.list_agents()`/`get_agent()` (unchanged) plus
  `section_registry.get_agent_section(agent_id)` and
  `provider_registry.get_agent_provider(agent_id)`, merging results:
  `GET /agents` → `[{"id", "name", "type", "section_id"}]`;
  `GET /agents/{agent_id}` → the existing `{"id", "name", "type",
  "settings", "actions"}` shape plus `"section_id"`, `"section_name"`,
  `"provider_id"`, `"provider_name"`, `"provider_available"`.
- **New API surface:**
  - `app/api/sections_router.py`, `APIRouter(prefix="/sections")`:
    `GET /sections` → `[{"id", "name", "agent_ids"}]`; `POST /sections`
    (`{"name"}`); `PATCH /sections/{section_id}` (`{"name"}`);
    `DELETE /sections/{section_id}` → `409` with a name-resolved message
    if `agent_ids` is non-empty (REQ-SB-18 Scenario 4b).
  - `app/api/providers_router.py`, `APIRouter(prefix="/providers")`:
    `GET /providers` → `[{"id", "name", "endpoint", "model",
    "credential_set", "is_default", "has_real_client", "agent_ids"}]` —
    **never a `credential` field**, in any response; `POST /providers`
    (`{"name", "endpoint", "credential", "model"}`); `PATCH /providers/
    {provider_id}` (any subset; an omitted `credential` preserves the
    stored value); `DELETE /providers/{provider_id}` → `409` with a
    name-resolved message if `agent_ids` is non-empty (REQ-SB-19
    Scenario 4b).
  - `app/api/agents_router.py` gains `PATCH /agents/{agent_id}` (body: any
    subset of `{"section_id", "provider_id"}`) → validates each supplied
    id exists (`404` otherwise), updates the assignment(s), returns the
    same merged detail shape as `GET /agents/{agent_id}`. One endpoint
    serves both REQ-SB-18's section-reassignment and REQ-SB-19's
    provider-picker, since both live on the same Agent Settings panel.
  - All three routers registered in `app/main.py`, matching the existing
    `app.include_router(...)` pattern.
- **Block-until-empty/unused: business layer returns a result dict, the
  router raises `409`.** `delete_section`/`remove_provider` never raise for
  ordinary control flow — they return `{"deleted": bool,
  "blocked_by_agent_ids": [str]}`, mirroring the existing `_invoke_action`/
  `trigger_action` result-dict convention. The router composes the `409`
  message by resolving each blocking id's display name via
  `agent_registry.get_agent(id)["name"]`.
- **Credential handling: plaintext at rest (the same trust boundary
  `compass_api_key` already lives inside), never returned by any
  endpoint.** No new encryption mechanism — no Accepted requirement asks
  for one, and `compass_api_key` is already plaintext in `.env` with no
  prior objection. `GET /providers` never includes a `credential` field,
  not even masked/partial; the approved prototype's masked
  `sk-live-••••••••••••` display is frontend-only decoration shown once
  `credential_set` is `true`.
- **Provider-availability enforcement for chat/action triggering** lives
  at the one shared funnel both the direct-action-trigger and
  chat-triggered paths already go through, `agents_router.py::
  _invoke_action`: before its existing `_ACTION_HANDLERS.get(...)` lookup,
  it resolves the agent's Provider and checks
  `provider_registry.has_real_client(provider_id)`; if unavailable, it
  short-circuits with an honest `{"status": "error", "message": "<Provider
  name> is not available yet — no client has been built for it."}`
  **without invoking the handler at all** — no silent fallback to Compass,
  no fabricated response (REQ-SB-19 Scenario 7). Safe for this pass since
  the only currently-real handler is itself LLM-backed via Compass; a
  future non-LLM-backed real action would need to revisit this blanket
  gate.
- **`layoutAgents.ts` becomes N-section-generic** — see "Frontend
  Application Architecture", above, and `ADR-014` point 6 for the full
  hub-angle/divider-line/neutral-hub-color reasoning.
- **Full reasoning, alternatives considered, and every consequence:**
  [ADR-014](ADR.md).

### Skills Repository — registration & per-agent access (REQ-SB-27-US-01, plumbing only — applies [ADR-015](ADR.md), no new ADR)

This story is the first concrete implementation of `ADR-015` point 9's
"`REQ-SB-27`'s skills become new `@mcp.tool()` entries" extensibility
path, resolved as an ordinary CRUD-pattern extension of `ADR-014`'s
already-`Accepted` "new persisted concern composed alongside a hardcoded
registry" shape, one concept over (skill *access*, not agent Sections/
Providers). `ADR-015` already settles the one genuinely architectural
question here ("what is a skill") — everything below is ordinary
`/plan-tasks` implementation latitude the ADR itself explicitly left open
(its own text: "the exact enforcement point is ordinary `/plan-tasks`
implementation latitude, not a further open architectural fork"). This
story is plumbing only — see the story's own `## Non-Goals` for what is
deliberately deferred (the first real skill's implementation).

- **Skill catalog: code-level, sourced from a new sibling module,
  `app/business/skill_tools.py`** (parallel to `app/business/
  vault_query_tools.py`, both siblings of `app/business/
  agent_orchestration/`, per `ADR-015` point 3's "a general capability,
  not orchestration-specific" placement) — holds the actual
  `@mcp.tool()`-decorated skill functions. This story registers exactly
  one illustrative stub skill (exact name/description left to the
  decomposer/coder, mirroring `ADR-015` point 11's "first tools are
  illustrative, not mandated by this pass" framing for
  `vault_query_tools.py`) whose body unconditionally returns the honest
  "not yet available" response (the story's own `## Constraints`
  stub-body pattern, mirroring `model_factory.py`'s / `ADR-011` point 3's
  / `ADR-014` point 7's same honesty shape one layer over) — demonstrating
  Scenario 1 (registration) and Scenario 4 (honest non-fabrication)
  without building the first real skill. `app/api/mcp_server.py` registers
  `skill_tools.py`'s functions as `@mcp.tool()`s the same way it already
  registers `vault_query_tools.py`'s — one shared server (`ADR-015` point
  9), two source modules feeding it.
- **The catalog is not derived by introspecting the MCP server's live,
  full tool list** (which would also surface `vault_query_tools.py`'s
  non-skill tools). `skill_tools.py` additionally exposes its own small,
  literal, enumerable registry of skill metadata (`id`, `name`,
  `description`), mirroring `agent_registry.py`'s own `AGENTS: dict` shape
  one concept over, that `skill_registry.py` reads directly — this
  sidesteps relying on any MCP SDK-level tagging/namespacing feature this
  project hasn't verified exists, per `ADR-015` point 2's own "genuinely
  unverified fact, not silently assumed" discipline.
- **New business module, `app/business/skill_registry.py`** — the new,
  persisted, user-mutable concern (mirrors `section_registry.py`/
  `provider_registry.py`'s `ADR-014` shape exactly): `list_skills()`
  (reads `skill_tools.py`'s catalog, unaffected by agent-access state),
  `list_agent_skills(agent_id)`, `grant_skill_access(agent_id, skill_id)
  -> bool`, `revoke_skill_access(agent_id, skill_id) -> bool`,
  `has_skill_access(agent_id, skill_id) -> bool` (the one reusable
  primitive both this story's own invocation entry point, below, and a
  future `agent_orchestration/` tool-binding step are expected to call —
  per the story's own Constraints, that graph-level tool-binding step is
  "most plausibly" where enforcement additionally lives once `REQ-SB-25`/
  `REQ-SB-20` are further along; designed now so that future integration
  reuses this exact check rather than duplicating it), and
  `invoke_skill(agent_id, skill_id) -> dict` (Scenarios 3/4's
  plumbing-only invocation path, below). **Deliberately no self-healing
  default-assignment** (unlike `section_registry.py`/`provider_registry.py`,
  which self-heal every known agent onto a default) — Scenario 2's
  explicit-grant-only model is this story's own scoped ACs, and which
  skills (if any) should default to all-agents access is an open question
  the story's own `## Non-Goals` explicitly leaves unresolved; no agent is
  auto-granted any skill by this pass.
- **New persisted state, `.second-brain/agent_skills.json`** —
  `{"assignments": {<agent_id>: [<skill_id>, ...]}}`, extending the
  established flat-JSON-file convention to a further concern (alongside
  `processed_email_ids.json`, `conversation_index.json`,
  `last_capture_run.json`, `processed_meeting_ids.json`,
  `agent_communication_history.json`, `agent_sections.json`/
  `agent_providers.json`). **No top-level catalog list** in this file
  (unlike `agent_sections.json`'s `"sections"` array) — unlike Sections,
  the skill catalog itself is never user-created or persisted; it is
  `skill_tools.py`'s own code-level registry, above. New
  `vault_writer.py` primitives, `load_skills_state()`/`save_skills_state()`,
  mirror `load_sections_state()`/`save_sections_state()`'s exact pure-I/O
  shape.
- **New API surface, `app/api/skills_router.py`**:
  - `GET /skills` → `[{"id", "name", "description"}]` — the catalog
    (Scenario 1).
  - `GET /agents/{agent_id}/skills` → that agent's granted skills
    (Scenario 2).
  - `POST /agents/{agent_id}/skills/{skill_id}` → grants access (Scenario
    2); `404` if either id is unknown.
  - `DELETE /agents/{agent_id}/skills/{skill_id}` → revokes access
    (Scenario 5).
  - `POST /agents/{agent_id}/skills/{skill_id}/invoke` → the plumbing-only
    invocation entry point (Scenarios 3, 4): `skill_registry.invoke_skill`
    checks `has_skill_access` first — no access returns a refusal result
    distinct from "not available" (Scenario 3); granted access invokes
    `skill_tools.py`'s stub function in-process and returns its honest
    "not yet available" result (Scenario 4) verbatim, never a fabricated
    one. **Chosen over extending `agent_registry.py`'s static per-agent
    action/trigger-phrase mechanism** (`ADR-011`) — skills are
    cross-cutting and dynamically grantable to any agent, unlike
    `agent_registry.py`'s fixed per-agent action list, and this keeps
    `agent_registry.py`/`agent_chat.py` untouched (`ADR-011` point 2's
    "agent identity/actions stay hardcoded" reasoning, undisturbed).
    Satisfies the story's own Constraint that an invocation entry point
    can "reuse whatever mechanism already triggers agent actions today...
    the exact entry point is an implementation detail left to
    `/plan-tasks`" — this is that `/plan-tasks` decision. Registered in
    `app/main.py` alongside the existing routers.
- **Relationship to `app/business/agent_orchestration/` — not built by
  this story, genuinely depended on.** As of this pass, `agent_
  orchestration/`/`app/api/mcp_server.py` do not yet exist in code
  (`ADR-015`'s own scaffolding, expected to land as part of
  `REQ-SB-25-US-01`); this story's `skill_tools.py` registration onto the
  shared MCP server, and `skills_router.py`'s invocation path, both
  require that scaffolding to exist first. This is an ordinary task-level
  `depends_on` for the decomposer to wire, not a new architectural
  question — already named in the story's own `## Dependencies`.
- **No ADR.** Every decision above is a direct, same-shape extension of
  already-`Accepted` structural decisions — `ADR-003`'s layering,
  `ADR-014`'s "new persisted concern composed alongside a hardcoded
  registry" pattern, and `ADR-015`'s own already-settled "skill capability
  = code-registered `@mcp.tool()` entry; skill access = a new persisted,
  per-agent concern" resolution (see the story's own `## Context`/
  `## Constraints`) — with no new tool, framework, storage mechanism, or
  trust-surface decision, and nothing here contradicts any `Accepted`
  ADR, the PRD, or a `MEMORY.md` constraint.

#### Amendment — unified capability model, phase 1: read-only Actions migrated to Skills (REQ-SB-39-US-01, see [ADR-028](ADR.md))

`REQ-SB-39` is an operator-confirmed "genuine architecture reversal" of
`ADR-011` point 2's "agent identity/actions stay hardcoded" framing:
every capability any agent has — including capabilities that exist today
as hardcoded `agent_registry.py` Actions — becomes a Skill, granted/
revoked through the one mechanism above, **including already-shipped
agents, not just future wizard-created ones.** Split into two sequential
stories (`ESCALATIONS.md` → `ESC-029`) so a mutating capability is never
observably ungated even transiently. This amendment covers only `US-01`'s
own scope: the capability model itself, plus the 3 currently
`"mutates": False` action ids (`view_last_run` — `email-capture`,
`meeting-capture`, `todo-capture`, `people-producer`; `ask_question` and
`view_channel_status` — `vault-qa`). The mutating-Action migration and the
working-mode gate extension are `REQ-SB-39-US-02`'s own scope, deliberately
not touched here. Full reasoning, every alternative considered, and every
consequence: [ADR-028](ADR.md).

- **`skill_tools.SKILLS` gains a `"mutates": bool` field on every entry**
  (all 5, post-migration — `diagram-understanding`/`web-research` both
  `False`, same as the 3 newly-migrated ids), mirroring `ADR-020` point 1's
  `agent_registry.py` action shape one layer over, fail-safe-defaulting to
  `True` if a future entry omits it. **Not consulted by any gate this
  pass** — a structural field `REQ-SB-39-US-02` reads directly for its own
  extension, not a behaviour change here.
- **`skill_registry.invoke_skill(agent_id, skill_id, args, trigger)` gains
  a required `trigger: Literal["chat", "direct", "hub_routed"])`
  parameter**, mirroring `_invoke_action`'s existing shape/discipline
  exactly (no default; every call site explicit). Threaded through, not
  yet branched on. Real call sites: `skills_router.py`'s invoke endpoint
  hardcodes `trigger="direct"` server-side (never client-supplied, same
  trust-boundary posture as `trigger_action`'s own hardcoded `"direct"`);
  `knowledge_bootstrap.py`'s existing Hub-routed `invoke_skill` call gains
  `trigger="hub_routed"` — the first real call site anywhere to pass that
  value, on either the Actions or Skills path.
- **`ADR-011`'s chat funnel is extended at its dispatch step only —
  `agent_registry.py` and `agent_chat.py` are both left completely
  unmodified.** The 3 migrated ids' existing action entries (id, label,
  `trigger_phrases`, `"mutates": False`) stay exactly where they are;
  `agent_chat.handle_chat_message` keeps matching off them unchanged.
  `agents_router.py`'s `trigger_action`/`chat()` dispatch is what changes:
  a matched/requested id that is a member of `skill_tools.SKILLS` routes to
  `skill_registry.invoke_skill(...)` instead of `_invoke_action(...)`;
  every other id (the still-real Actions) is unaffected. This membership
  check is the only new "is this migrated" logic anywhere — no separate
  migration-id constant, since the migrated Skill ids deliberately reuse
  their exact former Action id string. A small result-shape translation
  normalizes `invoke_skill`'s varying return shapes into the
  `{"status", "message"}` envelope `agents_router.py`'s existing
  post-dispatch code already expects (exact helper name is decomposer/
  coder latitude).
- **3 new zero-arg `@mcp_server.tool()` stub handlers in `skill_tools.py`**
  (`view_last_run`, `ask_question`, `view_channel_status`), each
  unconditionally honest-unavailable — no real handler exists for any of
  the three today on either the old Action path or the new Skill path.
  Registered as ordinary skill tools (not excluded from the LangGraph
  conversational loop the way `web-research` was) — `mcp_client.
  load_agent_tools`'s existing `has_skill_access` filter (`ADR-022` point
  6) already governs them generically, with zero change to that filter.
- **Retrofit of the 4 real already-shipped agents: a one-time, explicitly-
  scoped migration seed inside `skill_registry._load_state()`**, granting
  the 3 migrated ids to their real prior agents via a small literal
  mapping, idempotent (seeds once, reuses `grant_skill_access`'s own
  already-idempotent behaviour thereafter) — the same "seed once, on first
  load" shape `provider_registry._seed_state()` already established for
  the pre-seeded "Compass" Provider. **Deliberately not a reopening of
  this module's own "no self-healing default-assignment" principle** —
  scoped to exactly this known, fixed, named migration set; a genuinely
  new future Skill still needs its own explicit grant, no auto-default.
  This is the concrete task the decomposer must create for "retrofit
  existing agents," separate from building the new mechanism itself — the
  operator's own directive ("Everything, including existing shipped
  agents") is not satisfied by the mechanism alone.
- **New `skill_registry.list_agent_capabilities(agent_id) -> list[dict]`**
  — merges the agent's still-real Actions (`agent_registry.py`'s array,
  filtered to exclude any `skill_tools.SKILLS`-member id) with its granted
  Skills (`list_agent_skills`) into one list. `agents_router.py::get_agent`
  changes `"actions": [...]` to `"capabilities": [...]` (the `"actions"`
  key is removed, not kept alongside a new key) — directly satisfies
  Scenario 7's "no separate 'Actions' section shown alongside a separate
  'Skills' section." `AgentDetailPanel.tsx`'s "Available actions" block
  becomes a unified capability list sourced from this field, with a real
  grant/revoke control reusing the already-existing `GET /skills` /
  `GET,POST,DELETE /agents/{agent_id}/skills[/{id}]` endpoints (no new
  endpoint needed for grant/revoke) — no `/design` pass gates this build:
  the operator explicitly decided to skip `/design` for this entire batch
  of work (`REQ-SB-28/29/37/38/39/40/41`, `REVIEW-QUEUE.md` 2026-08-13
  update) and build directly, matching the established Section/Provider/
  Keywords/Working-mode kv-list row pattern; a new `skillsApiClient.ts`
  (mirroring `settingsApiClient.ts`'s thin fetch-wrapper shape) is the
  concrete new frontend file.
- **New ADR — [ADR-028](ADR.md).** A genuine structural addition (a new
  field on a shared catalog's own entry shape, a new required parameter on
  a cross-cutting invocation function, a new dispatch fork in the chat/
  direct-trigger funnel) — not a same-shape extension of already-Accepted
  structure the way most `architecture.md`-only amendments in this file
  are. Extends `ADR-011`, `ADR-014`, `ADR-015`, `ADR-020`, `ADR-022`;
  reopens none of them.

#### Amendment — unified capability model, phase 2: the working-mode gate extended to Skills, the 4 mutating Actions migrated (REQ-SB-39-US-02, see [ADR-029](ADR.md))

The safety-critical second half of the same reversal (`ESCALATIONS.md` →
`ESC-029`): every mutating capability — including today's 4 hardcoded
mutating Actions (`run_capture_now`, `pause_schedule`,
`rebuild_person_note`, `build_knowledge`) — keeps honoring the agent's own
working mode after becoming a Skill, with zero transient window where a
mutating capability is invocable ungated. Full reasoning, every
alternative considered, and every consequence: [ADR-029](ADR.md).

- **The gate lives inside `skill_registry.invoke_skill` itself**, not
  mirrored into `agents_router.py` the way `_invoke_action` (`ADR-020`)
  does — the one function all three real call sites (`skills_router.py`'s
  direct invoke endpoint, `agents_router.py`'s dispatch fork,
  `knowledge_bootstrap.py`'s Hub-routed call) already pass through
  unconditionally, so no caller can bypass it, and putting it in
  `agents_router.py` would be structurally unreachable from
  `knowledge_bootstrap.py` (a business module) without violating `ADR-003`.
  Inserted between the existing `has_skill_access` check and the existing
  handler dispatch — same Manual+`hub_routed`-refuses /
  Supervised+`mutates`-defers / everything-else-falls-through decision
  table as `ADR-020` point 2, keyed off `skill_tools.SKILLS[skill_id][
  "mutates"]`. A Supervised+mutating proposal reuses
  `pending_approval_registry.create_pending_approval` unedited, storing the
  `skill_id` in the existing generic `action_id` field (the same field
  `ADR-021` point 5's Tier-2 ids already use) and the invocation's own
  `args` in the existing `payload` field.
- **New `skill_registry._dispatch_skill(agent_id, skill_id, args)`** — the
  pre-this-ADR body of `invoke_skill`, extracted unchanged as a raw,
  ungated primitive, mirroring `_execute_action`'s own "thin gate wraps
  unconditional dispatch" split. `pending_approvals_router.py`'s Approve
  endpoint gains one new branch, checked before its existing
  `_APPROVAL_HANDLERS`/`_execute_action` chain, calling `_dispatch_skill`
  directly for a pending record whose `action_id` is a `skill_tools.SKILLS`
  member — mirroring the file's own already-existing cross-module private-
  function import of `agents_router._execute_action`.
- **Migration preserves exactly today's real/honest-unavailable split —
  no new real behavior is built.** Direct code inspection confirms
  `_ACTION_HANDLERS` wires a real handler to only 2 of the 4 mutating ids'
  agent pairs today (`("email-capture", "run_capture_now")`,
  `("compass-expert", "build_knowledge")`); the other 5 real pairs
  (`meeting-capture`/`todo-capture`'s own `run_capture_now`, all 3 agents'
  `pause_schedule`, `people-producer`'s `rebuild_person_note`) have no
  wired handler today and already return an honest "not yet available" via
  `_execute_action`. The migrated `run_capture_now`/`build_knowledge` Skill
  handlers call through to the same real functions
  (`run_capture_and_record_completion`, `knowledge_bootstrap.
  bootstrap_agent_knowledge` via the existing `_run_build_knowledge`
  translation); the migrated `pause_schedule`/`rebuild_person_note` Skill
  handlers are honest unconditional stubs, identical posture to `ADR-028`
  point 4's 3 read-only stubs.
- **`agent_registry.py`'s per-agent action arrays for these 4 ids stay in
  place, unedited** — vestigial, chat-funnel-matching only, mirroring
  `ADR-028` point 3's identical "leave in place" precedent. No new
  dispatch-fork code is needed in `agents_router.py`: the already-built
  `id in skill_tools.SKILLS` membership check (`ADR-028` point 3)
  automatically routes these 4 ids to `invoke_skill` once they join the
  catalog. The 2 real `_ACTION_HANDLERS` entries become dead code post-
  migration — left in place, a named consequence, not a cleanup this story
  performs.
- **Retrofit: the existing one-time migration-grant seed
  (`skill_registry._load_state()`, `ADR-028` point 5) gains 4 new
  id→agent-list entries**, same idempotent shape as the 3 already there —
  `run_capture_now`/`pause_schedule` → `["email-capture", "meeting-
  capture", "todo-capture"]`, `rebuild_person_note` → `["people-
  producer"]`, `build_knowledge` → `["compass-expert"]`. **5 distinct real
  agents in total** carry these 4 mutating ids today (confirmed by direct
  reading of `agent_registry.py`'s own `AGENTS` catalog — 3 agents share
  `run_capture_now`+`pause_schedule`, 2 each carry one distinct id):
  `email-capture`, `meeting-capture`, `todo-capture`, `people-producer`,
  `compass-expert`.
- **Atomicity, concretely defined for this single-process app with no
  staged rollout:** the gate-logic task, the Approve-endpoint task, and the
  4-id-migration-plus-retrofit task must be `depends_on`-chained (migration
  depends on gate, never the reverse or a parallel-independent ordering) —
  there is no real deploy boundary to enforce this technically, so it is a
  decomposer-level task-sequencing discipline, not a code mechanism. See
  [ADR-029](ADR.md) point 8 for the full reasoning.
- **New ADR — [ADR-029](ADR.md).** Extends `ADR-020`, `ADR-028`, and
  `ADR-021` point 5's `action_id`-reuse precedent; reopens none of them.

#### Amendment — Skills grouped by Tool: collapsible multi-select tree with icons (REQ-SB-48-US-01, no new ADR)

A presentation/interaction-only upgrade of `AgentDetailPanel.tsx`'s
Capabilities section — no new backend behavior, no new endpoint, no new
persisted store, no new dispatch fork or trust-boundary decision, so
nothing here rises to the same "genuine structural addition" bar `ADR-028`/
`ADR-029` cleared. `/design` was explicitly skipped for this story (operator
confirmation, 2026-08-14, matching the established "well-understood,
coder-improvisable UI pattern" precedent already used for this batch of
work) — the analyst's own resolved Tool taxonomy and fixed-icon-per-Tool
decision are adopted as final, not re-derived here.

- **Taxonomy re-confirmed against the current, real `skill_tools.SKILLS`
  catalog, not re-derived.** Direct re-read at this pass confirms the
  catalog is still exactly the same 11 entries the analyst's own pass
  enumerated (`diagram-understanding`, `web-research`, `view_last_run`,
  `ask_question`, `view_channel_status`, `run_capture_now`,
  `pause_schedule`, `rebuild_person_note`, `build_knowledge`,
  `write-to-vault-draft`, `summarize-file`) — `REQ-SB-47-US-01`'s own
  architecture pass (the only work landed since the analyst's pass) reads
  `skill_tools.SKILLS[capability_id]["mutates"]` but adds no new catalog
  entry. The analyst's per-Skill Tool assignment (Outlook: 3, Vault: 4,
  Web: 1, Compass: 3) is accurate against this confirmed-unchanged catalog
  and is adopted verbatim, including the one disclosed adjustment
  (`summarize-file` → Compass, not the PRD breadcrumb's own proposed
  Vault) and the one disclosed pragmatic default (`view_channel_status` →
  Vault).
- **`skill_tools.SKILLS` gains a `"tool": "Outlook" | "Vault" | "Web" |
  "Compass"` field on every entry** — a plain, code-literal classification
  field, the same shape as the existing `"mutates": bool` field `ADR-028`
  already added one layer over. **Server-side, not a frontend static
  lookup table** — chosen over a frontend-only mapping because
  `skill_tools.SKILLS` is this project's own already-established single
  source of truth for a Skill's catalog metadata (`ADR-015` point 9,
  `skill_registry.py`'s own docstring: "composed alongside
  `skill_tools.py`, not inside it"); a frontend-side lookup keyed by Skill
  id would need to be kept in sync by hand on every future Skill addition,
  the exact drift risk `skill_tools.py`'s own module docstring already
  warns against for the catalog generally. No default/fallback value is
  defined — every one of today's 11 entries carries an explicit `"tool"`
  value; a future new Skill needs its own explicit Tool placement decision
  at the time it's added (the story's own Constraints), mirroring
  `"mutates"`'s "fail-safe-defaulting" caution but requiring an explicit
  value rather than defaulting, since an un-classified Skill has no safe
  default Tool group the way an un-classified `mutates` has a safe
  default (`True`, gate-first).
- **Passed through by two already-existing read paths, no new endpoint:**
  `skill_registry.list_skills()`'s existing `list(skill_tools.SKILLS.
  values())` passthrough carries the new field automatically (`GET
  /skills`, feeding `AgentDetailPanel.tsx`'s not-yet-granted `skillCatalog`
  list); `skill_registry.list_agent_capabilities`'s skill-kind branch adds
  `"tool": skill["tool"]` to its per-item dict alongside the existing
  `"id"`/`"label"`/`"kind"` keys (feeding `GET /agents/{agent_id}`'s
  `capabilities` array, the already-granted half of the tree). The
  action-kind branch is unchanged and carries no `"tool"` key — Scenario
  9's "Built-in capabilities stay outside the Tool tree entirely" is true
  by construction (the frontend tree only ever groups items that carry a
  `"tool"` key), not a new conditional.
- **Icon sourcing: 4 fixed Tool-level icons, frontend-only static lookup,
  not a backend field.** Recommended and adopted over a backend `"icon"`
  field on `skill_tools.SKILLS` because the drift risk a server-side field
  guards against (many, growing Skills) does not apply symmetrically to a
  4-entry, rarely-changing Tool taxonomy — the same reasoning that makes
  `"tool"` worth centralizing server-side makes a dedicated backend `icon`
  field unnecessary ceremony for 4 fixed glyphs. Mirrors `Sidebar.tsx`'s
  own existing plain-Unicode-glyph `.nav-icon` convention (no icon
  library/SVG asset pipeline introduced). A new small `TOOL_ICONS: Record<
  string, string>` constant (frontend, exact file left to the
  decomposer/coder — plausibly a sibling of the new tree component) maps
  the same 4 literal Tool names the backend now emits.
- **New frontend tree component replacing `AgentDetailPanel.tsx`'s flat
  Capabilities `kv-list`** (exact component boundary — inline in
  `AgentDetailPanel.tsx` vs. a new sibling file — is decomposer/coder
  latitude, not resolved by this architecture pass, consistent with this
  story's own net-new, prototype-uncovered UI territory): groups
  `agent.capabilities` (skill-kind rows) and the not-yet-granted, filtered
  `skillCatalog` rows by their shared `"tool"` value into one merged,
  per-Tool section, expanded by default (Scenario 1), collapsible without
  ever calling grant/revoke (Scenario 2/3), each Tool header and each
  Skill row rendering `TOOL_ICONS[tool]` (Scenario 4). Multi-select is a
  same-grant-state-only selection model (Scenario 7) that, on a bulk
  Grant/Revoke trigger, issues N sequential calls against the already-
  existing `grantAgentSkill`/`revokeAgentSkill` (`skillsApiClient.ts`,
  unchanged) — one `POST`/`DELETE
  /agents/{agent_id}/skills/{skill_id}` per selected Skill, exactly
  today's per-row mechanism repeated, never a new batch endpoint
  (Scenarios 5/6/8, the story's own Constraints). Action-kind capabilities
  keep rendering exactly as today, outside the tree (Scenario 9).
- **Frontend type changes, additive only:** `skillsApiClient.ts`'s
  `SkillSummary` interface gains `tool: string`; `agentsApiClient.ts`'s
  `AgentCapability` interface gains `tool?: string` (present for
  `kind: 'skill'` rows, absent/undefined for `kind: 'action'` rows,
  mirroring the field's own absence server-side on the action-kind
  branch).
- **No ADR.** Every decision above is an additive field on an
  already-`Accepted` catalog shape (`ADR-015`'s `skill_tools.SKILLS`,
  extended the same way `ADR-028`'s `"mutates"` field already was) plus a
  frontend rendering/interaction upgrade with no new mechanism, endpoint,
  persisted store, or trust-boundary decision — nothing here contradicts
  any `Accepted` ADR, the PRD, or a `MEMORY.md` constraint.

### Agent Working Modes & Pending Approvals (REQ-SB-21-US-01, see [ADR-018](ADR.md) + [ADR-020](ADR.md))

Every agent gains a third new mutable, persisted property — its working
mode (Autonomous/Supervised/Manual) — composed *alongside*
`agent_registry.py` exactly the way Sections/Providers already are
(`ADR-014`), plus a genuinely new concern neither of those introduced: a
**Pending Approvals workflow**, since "Supervised" means a proposed
action must be durably held, visible, and separately resolved (approved
or declined), not just read/written like a simple property. Full
reasoning, every alternative considered, and every consequence:
[ADR-018](ADR.md) (state files, registries, Approve/Decline endpoints,
background-pipeline gate, `"proposal"` history kind, merged
`working_mode` field — all still current) and
[ADR-020](ADR.md) (the chat/direct-action gate's corrected two-axis
design, superseding `ADR-018` points 3 and 5 only, `ESCALATIONS.md` →
`ESC-013`).

- **`app/business/agent_registry.py` gains a `"mutates": bool` field on
  every action definition** (still a fully static, hardcoded module,
  `ADR-011` point 2 unaffected) plus a new `get_action(agent_id,
  action_id) -> dict | None` lookup helper. Today's real classification:
  `run_capture_now` and `rebuild_person_note` → `True` (write to the
  vault); `pause_schedule` → `True` (a control-plane state mutation, even
  though it has no real handler yet); `view_last_run`, `ask_question`,
  `view_channel_status` → `False` (read-only). An action id the gate
  cannot resolve defaults fail-safe to `True` (see [ADR-020](ADR.md)).

- **Two new sibling `.second-brain/` state files (8th, 9th):**
  `agent_working_modes.json` (`{"assignments": {<agent_id>: "autonomous" |
  "supervised" | "manual"}}` — a fixed 3-value enum, no user-created
  catalog half the way Sections/Providers have one) and
  `agent_pending_approvals.json` (`{"pending": [{"id", "agent_id",
  "trigger": "chat" | "direct" | "background" | "hub_routed", "action_id",
  "description", "status": "pending" | "approved" | "declined",
  "created_at", "resolved_at"}, ...]}` — `"hub_routed"` added by
  [ADR-020](ADR.md), reserved for a future story; no code path produces it
  yet). `app/data_access/vault_writer.py` gains the
  paired `load_working_modes_state()`/`save_working_modes_state()` and
  `load_pending_approvals_state()`/`save_pending_approvals_state()`
  primitives, pure I/O, mirroring every existing state-file primitive's
  shape.
- **`app/business/working_mode_registry.py`** (new) — self-healing
  default assignment (`"autonomous"`, the operator-resolved,
  behavior-preserving default) for any known agent absent from
  `assignments`, folded into one `_load_state()` (no separate seed step —
  there is no non-trivial starting catalog to compute, unlike Sections).
  Exposes `get_agent_working_mode(agent_id) -> str` (never `None`) and
  `set_agent_working_mode(agent_id, mode) -> bool`.
- **`app/business/pending_approval_registry.py`** (new, a separate
  concern from working mode itself — a workflow record with a lifecycle,
  not a settable property) — `list_pending_approvals(status=None,
  agent_id=None)`, `get_pending_approval(approval_id)`,
  `create_pending_approval(agent_id, trigger, action_id, description,
  payload=None, dedupe_key=None)`
  (idempotent for `trigger="background"` only — reuses an existing
  unresolved record for that agent rather than piling up a duplicate
  every scheduler tick; `"chat"`/`"direct"` proposals are never
  deduplicated by THIS check), `resolve_pending_approval(approval_id,
  status)`. `id`s are `uuid.uuid4().hex[:12]` — this project's first
  `uuid` usage (stdlib only, no new dependency).
  - **Target-aware `dedupe_key` idempotency check (`BUGFIX-08-US-01`,
    see [ADR-056](ADR.md))** — additive alongside the `trigger ==
    "background"` guard above, never replacing it. When a caller supplies
    `dedupe_key` (opaque `str`, caller's own convention — mirrors
    `payload`'s existing opaque-to-the-registry shape), a second check
    matches an existing `status == "pending"` record sharing the SAME
    `agent_id` AND the SAME `dedupe_key`, **regardless of `trigger`**, and
    returns it instead of creating a duplicate. Closes the gap the
    `"background"`-only guard deliberately left open: two DIFFERENT
    non-`"background"` triggers (or the SAME trigger repeated across
    ticks) both targeting the exact same real thing. The stored record
    gains one additive field, `"dedupe_key": str | None`, `None` on every
    pre-existing record (never matched — the check is skipped entirely
    when the caller passes no `dedupe_key`). Real call sites wired to this
    check, each namespaced `"{action_id}:{stable_target_identifier}"` so
    two different action kinds under one `agent_id` never collide:
    `skill_registry.py::invoke_skill`'s own Supervised+mutates gate
    (`dedupe_key = f"{agent_id}:{skill_id}"`, computed inside
    `invoke_skill` itself — zero change needed to any of its own callers,
    including `agent_schedule_registry.dispatch_with_shared_lock`, closing
    `BUG-029`'s own scheduled-vs-direct race for ANY Supervised mutating
    Skill, not just `meeting-capture`/`run_capture_now`);
    `email_classification.py::route_to_project`
    (`f"route_thread_to_project:{conversation_id}"`) and
    `::_create_classification_failure_pending_approval`
    (`f"acknowledge_classification_failure:{conversation_id}"`); and
    `librarian_housekeeping.py::propose_customer_backfill`
    (`f"propose_customer_backfill_routing:{customer}"`, per batch) and
    `::propose_customer_archival_candidates`
    (`f"propose_customer_archival_candidate:{customer}"`, per candidate) —
    closing `BUG-030`'s staged-email/Thread reprocessing duplication and
    the same-shaped gap `ADR-055`'s own Consequences already disclosed for
    Customer-backfill batches. `agent_schedule_registry.py`'s shared
    dispatch lock is unmodified — the fix is deliberately independent of
    lock timing (see `ADR-056`'s Context for why the literal race is not
    reproducible against the current, already lock-consolidated
    `dispatch_with_shared_lock` path, and why the dedupe_key check is the
    correct guarantee regardless).
- **The chat/direct-action gate: `agents_router.py::_invoke_action` split
  into a thin gate plus the existing unconditional dispatch, renamed
  `_execute_action`.** The gate takes a new `trigger: "chat" | "direct" |
  "hub_routed"` parameter (`trigger_action` passes `"direct"`, `chat`'s
  matched-action branch passes `"chat"`, `"hub_routed"` is reserved for a
  future story — no call site produces it yet, see below; the story's own
  Available-Actions-button question is resolved here: yes, same gate,
  since both already share this one funnel per `ADR-011`). **Corrected
  two-axis check ([ADR-020](ADR.md), supersedes `ADR-018` point 3):**
  resolves both `mode = working_mode_registry.get_agent_working_mode(...)`
  and `action = agent_registry.get_action(agent_id, action_id)`. **Manual
  + `trigger == "hub_routed"`** refuses outright (no pending record, no
  execution — currently unreachable in practice, since `ADR-017`'s routing
  node never invokes a target agent's action, but recorded for when a
  future story adds that). **Supervised + `action["mutates"] is True`**
  short-circuits before the existing Provider-availability check
  (`ADR-014` point 7) or the handler dispatch — creates a pending-approval
  record and returns `{"status": "pending", "message": ...,
  "pending_approval_id": ...}` — **regardless of `trigger`** (chat,
  direct, or hub_routed). **Supervised + `action["mutates"] is False`**
  (a read-only action), **Autonomous** (any trigger), and **Manual** with
  `trigger` in `("chat", "direct")` all fall straight through to
  `_execute_action`, unchanged from today's behaviour.
- **Manual vs. Supervised, corrected ([ADR-020](ADR.md), supersedes
  `ADR-018` point 5):** the two modes now gate on genuinely different
  axes, not the same trigger-source switch. **Manual** gates on **trigger
  source only** — a direct human ask (a trigger-phrase match or an
  Available Actions click, the one mechanism this codebase has for
  "explicitly asking," `ADR-011`; no NLU exists, `ADR-007`) always
  executes immediately, whether the action reads or writes; neither a
  background/scheduled trigger (below) nor another agent's Hub-routed
  request ever executes. **Supervised** gates on the **action's own
  read-only-vs-mutating nature only** — a read-only action (`view_last_run`,
  `ask_question`, `view_channel_status`) proceeds immediately for any
  trigger, identical to Autonomous; a write/mutating action always
  proposes-and-waits, for any trigger (chat, direct, or background). The
  two modes' behaviour happens to coincide for the background trigger
  today (both real background pipelines only ever run mutating actions —
  see below), but for the chat/direct funnel they now genuinely diverge
  by action nature, not by whether the trigger was background or not.
- **The background-pipeline gate: two explicit per-agent checks inside
  `email_classification.py::run_capture_and_record_completion`** (not a
  generic dispatch loop — matches this codebase's explicit-sibling-code
  style), one for `"email-capture"` before its `classify_recent_emails`
  call, one for `"meeting-capture"` before its
  `meeting_classification.classify_recent_meetings()` call. Autonomous
  runs the step (via a new shared `run_capture_for_agent(agent_id, limit)`
  helper, reused by the approval path below); Supervised creates a
  `trigger="background"` pending-approval record instead of running it;
  Manual skips silently — no record, no history entry at all. **Unchanged
  by [ADR-020](ADR.md):** both gated steps are always `"mutates": True`
  actions today, so the corrected mutates-based Supervised rule and the
  original trigger-based rule produce the identical outcome here by
  construction — the behavioural change from `ADR-020` is confined to the
  chat/direct funnel, above. `app/scheduling/capture_scheduler.py`
  requires **zero changes** — this conditionality lives entirely inside
  the one function it already treats as an opaque unit, extending (not
  reopening) `ADR-005`/`ADR-008` point 4. **Amendment (REQ-SB-09-US-01,
  [ADR-027](ADR.md)):** `"todo-capture"` gains this same third gated
  block, structurally identical to the two above — see "Task Notes &
  Outlook-Tasks Capture", below, and [ADR-027](ADR.md) point 5 for the
  full reasoning. This sentence previously read "`todo-capture` has no
  real background pipeline yet" — no longer current, corrected in place
  rather than left stale.
- **New API surface, `app/api/pending_approvals_router.py`**,
  `APIRouter(prefix="/pending-approvals")`: `GET /pending-approvals`
  (optional `status`/`agent_id` filters), `GET /pending-approvals/{id}`,
  `POST /pending-approvals/{id}/approve` (`404`/`409` guards; executes
  the deferred action **directly** via `_execute_action`/
  `run_capture_for_agent` — bypassing the working-mode gate entirely,
  since re-entering it would find the agent still Supervised and defer
  forever instead of ever running), `POST /pending-approvals/{id}/decline`
  (same guards; discards, no action taken). Both are agent-agnostic and
  shared by every UI surface that can trigger them — the approved
  prototype's inline chat `.chat-proposal` state-switcher and the
  standalone Pending Approvals page call the identical two endpoints.
  Registered in `app/main.py`.
- **Communication history gains one new entry kind, `"proposal"`**
  (additive to `ADR-011`'s `"chat_user" | "chat_agent" | "run_event"`
  enum), carrying an optional `pending_approval_id`. Created by both
  gates above at the moment a Supervised proposal is created. The
  frontend renders it as the approved prototype's `.chat-proposal` card,
  resolving its **live** Pending/Approved/Declined state via `GET
  /pending-approvals/{id}` (the history entry's own text never changes
  after creation — history stays append-only).
- **`GET /agents`/`GET /agents/{agent_id}` gain a merged `working_mode`
  field; `PATCH /agents/{agent_id}` gains an optional `working_mode`
  body field** (`400` on an invalid enum value — distinct from the
  existing `404 Unknown section/provider` lookup-failure pattern).
  Composition happens at the router, exactly like `section_id`/
  `provider_id` — `agent_registry.py` stays fully unmodified.
- **`app/business/my_day.py`/`app/api/my_day_router.py` are untouched.**
  The new My Day "Pending Approvals" 5th dashboard card and its
  `/my-day/approvals` drill-down page fetch `GET /pending-approvals`
  directly — Pending Approvals is a cross-agent workflow concept, not a
  read-only projection over Email/Meeting notes the way My Day's existing
  three sections are, so it does not belong inside `my_day.py`'s
  aggregation.
- **Frontend:** `AgentDetailPanel.tsx` gains a Working-mode `<select>`
  kv-row (same pattern as the Section/Provider rows) and a `.chat-proposal`
  card renderer for `"proposal"`-kind history entries (Approve/Decline
  buttons calling the new endpoints, live-polling the record's own
  status); `agentsApiClient.ts`'s shared assignment call gains
  `working_mode?`, plus new `fetchPendingApprovals()`/
  `approvePendingApproval(id)`/`declinePendingApproval(id)` calls (new
  `pendingApprovalsApiClient.ts`, co-located under `features/agents-map/`,
  reused by both the detail panel and the new My Day page); a new
  `src/frontend/src/pages/MyDayApprovalsPage.tsx` at route
  `/my-day/approvals` (mirroring `MyDayCalendarPage.tsx`'s exact
  `.item-list`/`.item-row` shape, `.item-row-actions` holding
  Approve/Decline buttons), added to `App.tsx`'s route table and
  `MyDayPage.tsx`'s card grid as a 5th `SECTIONS` entry.

## System Health View — read-only status aggregation + chat-path crash-gap fix (REQ-SB-31-US-01)

A new top-level nav page surfacing whether Second Brain's own moving
pieces are genuinely working — MCP/agent-orchestration reachability,
per-agent Provider availability, last capture run completion — plus a
separate, backend-only robustness fix closing a real gap in the chat
path's own exception handling. **No new ADR** — see "No ADR" note at the
end of this section for the full reasoning; every piece below is an
ordinary, same-shape extension of already-`Accepted` structural
decisions.

- **New business module `app/business/system_health.py`** — a **read-only
  aggregation** module, the same shape as `app/business/my_day.py`
  (REQ-SB-12-US-02): it writes no new persisted state at all, composing
  only already-existing signals:
  - `mcp_mount_reachable() -> bool` — the one real (but local, in-process,
    zero-external-cost) HTTP call this story adds: a bare `GET` against
    the same hardcoded loopback `http://127.0.0.1:8001/mcp` URL
    `agent_orchestration/mcp_client.py` already calls (this project's own
    documented port convention — `tools/run-backend.cmd --port 8001`,
    `.claude/launch.json` — reused as-is, not a new port-discovery
    mechanism). `True` only on an `HTTP 406` response (the mount's own
    proven "alive" signal, confirmed live 2026-08-12 per the story's own
    Context); any other status code, connection error, or timeout →
    `False`. A short `httpx.get(..., timeout=...)` call, mirroring
    `compass_client.py`'s existing synchronous `httpx` usage — no new HTTP
    library.
  - Provider availability is **not recomputed** — `provider_registry.
    list_providers()` (`REQ-SB-19-US-01`, `Done`) already returns each
    Provider rolled up with `has_real_client`/`agent_ids`, exactly the
    "per distinct Provider, from each agent's own selection" shape this
    story's Context calls for. `system_health.py` calls it directly
    (business-to-business composition, the same shape
    `people_extraction.py` already uses to compose
    `customer_hub_linking.py`'s primitives) rather than re-deriving
    anything from `GET /agents`.
  - `list_disabled_agents() -> list[dict]` — iterates
    `agent_registry.list_agents()`, and for each agent whose
    `provider_registry.get_agent_provider()` is `None` or fails
    `has_real_client()`, includes it as `{"agent_id", "agent_name",
    "provider_name"}`. This is the one new roll-up direction Providers
    CRUD didn't already need — "which agents are Disabled," not "which
    Provider serves which agents" — computed here, not added to
    `provider_registry.py` itself (which stays exactly `REQ-SB-19`'s
    `Done` shape, unmodified).
  - `last_capture_run() -> dict | None` — a thin passthrough to
    `vault_writer.load_last_capture_run()` (`REQ-SB-07-US-01`, `Done`),
    unchanged, returning its existing `{"finished_at": iso8601}` or `None`
    as-is — no new interpretation, no staleness/pass-fail judgment added
    (the story's own Non-Goals).
  - `get_system_health() -> dict` composes the four signals above into one
    response, recomputed **fresh on every call** — no caching layer, the
    same "recomputes fresh on every call, never cached" precedent already
    established for My Day's rolling window (`REQ-SB-22-US-01`), satisfying
    Scenario 7 by construction (nothing to invalidate).
- **New router `app/api/system_health_router.py`**,
  `APIRouter(prefix="/system-health")`, one endpoint, `GET
  /system-health`, returning `system_health.get_system_health()` verbatim.
  Registered in `app/main.py` alongside the existing routers — the same
  `api → business → data_access` layering (`ADR-003`) every other router
  already follows; this router calls `system_health.py` only, no direct
  `data_access`/`provider_registry`/`agent_registry` reach-around.
- **Frontend:** a new page, `src/frontend/src/pages/SystemHealthPage.tsx`,
  at route `/system-health` (added to `App.tsx`'s route table, wrapped in
  the existing `<AppShell>` like every other page), plus a new
  `src/frontend/src/features/system-health/client.ts` (`fetchSystemHealth()`
  wrapping `GET /system-health` via the existing `api/client.ts` `fetch`
  convention, `ADR-010`). `Sidebar.tsx` gains one new `<NavLink>` ("System
  Health"), positioned after Settings — matching the approved prototype's
  own sidebar order across every prototype page. Renders the four regions
  the approved prototype (`html-prototype/system-health.html`) already
  validates — Health Issues (composed client-side from `mcp.reachable ===
  false` plus each entry in `disabled_agents`, mirroring the prototype's
  own "two different reasons render two different rows" framing), MCP
  status, Providers status, and Last capture run — reusing only
  already-ported classes (`.card`, `.badge*`, `.kv-list`, `.item-list`,
  `.empty-state`) with **zero new CSS**, per the prototype's own "composed
  entirely from existing tokens/components" header note. A manual Refresh
  affordance re-calls `fetchSystemHealth()`; no polling/auto-refresh
  interval (the story's own Non-Goals).
- **Separate, backend-only fix: `app/business/agent_orchestration/
  graph.py::run_agent_conversation`'s own body** (`REQ-SB-25-US-01`,
  `Done`) had one remaining, real gap — its own `await mcp_client.
  load_vault_query_tools()` and `await _GRAPH.ainvoke(initial_state)`
  calls were not wrapped in the honest-failure-funnel pattern `_call_model`
  (the graph's own node, inside `_GRAPH`) already uses (`ADR-015`'s
  mechanism decision). Scenario 8 closes this by wrapping both remaining
  calls in the identical `try/except Exception as exc: return {"error":
  f"..."}` shape — applying an already-`Accepted` pattern to a second call
  site in the same function, not inventing a new one. This is unrelated to
  the System Health page's own read path (no new region reads this fix's
  outcome — the story's own Non-Goals: no persisted "last unhandled
  exception" signal exists yet) and has no dependency on
  `system_health.py`/`system_health_router.py` — it can be built
  independently, first if desired.
- **No ADR.** Every piece above is an ordinary, same-shape extension of
  already-`Accepted` structural decisions: the aggregation module mirrors
  `my_day.py`'s exact "read-only, composes existing business/data_access
  signals, no new persisted state" shape (`REQ-SB-12-US-02`'s own "No ADR"
  reasoning applies here even more directly, since this module persists
  *nothing* new at all, not even an additive field); the router is a
  straight `ADR-003`-layered addition, the same shape as `my_day_router.py`/
  `agents_router.py`; the frontend page is an ordinary new route/page/nav
  item within `ADR-010`'s already-`Accepted` routing/styling/component
  conventions (the same shape `BUGFIX-02-US-01`'s new `SectionDrilldown.tsx`
  page-level component added without a new ADR); and the `graph.py` fix
  applies `ADR-015`'s already-established honest-failure-funnel pattern to
  a second call site, the same "extends, does not reopen" shape
  `REQ-SB-33-US-01`'s grounding-guardrail pass used on the same function
  family. No new tool, framework, storage mechanism, external round-trip,
  or trust-surface decision; nothing here contradicts any `Accepted` ADR,
  the PRD, or a `MEMORY.md` constraint. This also does not reopen or edit
  `ADR-011` point 3 / `ADR-014` point 7 — the Disabled/Health-Issue display
  override is a per-view UI presentation decision (this story's own
  Constraints/Notes), not a change to either ADR's underlying honesty
  convention or to any other screen relying on it.

## Agent Activity & Error Observability (REQ-SB-11-US-01)

A new top-level nav page — related to, but explicitly not overlapping,
System Health (above): System Health is a current-snapshot status board
("is each piece healthy right now"); this page is a chronological
history/log ("every background capture run, in order, with its own
recorded outcome"), plus one net-new channel-status check System Health
does not cover (direct Outlook COM reachability). **No new ADR** — see
"No ADR" note at the end of this section; every piece below is an
ordinary, same-shape extension of already-`Accepted` structural
decisions, the same class of "no new ADR" call `REQ-SB-31-US-01`'s own
architect pass made for its structurally identical read-only status page.

- **Honest-failure-recording fix — `app/business/email_classification.py::
  run_capture_and_record_completion`, this file only.** Two confirmed,
  real gaps (the story's own Context, grounded in direct code reading):
  (1) meeting-capture's Autonomous branch calls `run_capture_for_agent(
  "meeting-capture")` and discards the result with no history entry at
  all — the only capture step of the two that had no success-recording
  parity; (2) neither capture step's call inside this function is wrapped
  in a `try/except` — an exception escaping `classify_recent_emails`'s or
  `classify_recent_meetings`'s own per-item handling (e.g.
  `outlook_com.OutlookUnavailable` if Outlook desktop isn't running)
  propagates all the way up through `capture_scheduler.run_capture_if_idle`
  uncaught, with zero history entry ever written.
  - **Fix site: the call site inside `run_capture_and_record_completion`,
    not inside `classify_recent_emails`/`classify_recent_meetings`
    themselves.** This mirrors `ADR-015`'s own established
    honest-failure-funnel shape exactly — `run_agent_conversation`'s
    `REQ-SB-31-US-01` Scenario-8 fix wraps the *call* to
    `mcp_client.load_vault_query_tools()`/`_GRAPH.ainvoke(...)` at the
    orchestrating function's own body, not inside those callees — never
    changing either capture function's own `list[dict]`-of-per-item-
    results return contract. Each of the two capture steps (email,
    meeting) gets its own independent `try/except Exception as exc:` around
    its `run_capture_for_agent(...)` call, so one agent's failure this
    tick can never suppress the other's success being recorded (Scenario
    3) — the same "independent per-branch funnel" shape, not one
    all-or-nothing `try` around the whole function.
  - **Clarifies the story's own Constraints wording.** "Each capture
    pipeline's own top-level entry point (`email_classification.py`,
    `meeting_classification.py`)" names the two *pipelines*/files this
    scope covers (as distinct from, say, a future to-do-capture pipeline),
    not a mandate to edit both files — `run_capture_and_record_completion`
    is the one genuine top-level orchestration entry point for both
    pipelines today, and it already lives entirely in
    `email_classification.py`. `meeting_classification.py` itself needs no
    change: its `classify_recent_meetings()` keeps its existing shape
    unedited, exactly as `REQ-SB-31-US-01`'s own Non-Goal ("no general
    exception-catching/logging middleware") already establishes as the
    right boundary — the funnel closes the gap one level up, at the one
    place both pipelines are already orchestrated, not by adding
    unrelated error-handling inside a pipeline's own per-item loop.
  - **New `kind` value: `"run_error"`**, alongside the existing
    `"run_event"` / `"chat_user"` / `"chat_agent"` / `"proposal"` set
    (`vault_writer.append_agent_history_entry`, unmodified signature) —
    chosen over adding an `"outcome"` field to the existing `"run_event"`
    shape because it needs zero changes to either existing consumer of
    `"kind"`: `agent_orchestration/state.py::history_entries_to_messages`
    already excludes every kind it doesn't explicitly match
    (`"chat_user"`/`"chat_agent"` only — confirmed by direct reading, a
    new kind falls through its existing no-op case unchanged), and
    `AgentDetailPanel.tsx`'s Communication History tab already renders any
    non-`"proposal"` kind via its existing generic `entry.text` +
    timestamp fallback (confirmed by direct reading — no `switch`/kind
    check beyond the `"proposal"` branch). Both of `REQ-SB-13-US-01`'s own
    consumers of this file are therefore genuinely unaffected, confirming
    that story's own Dependencies claim ("its per-agent panel is
    unaffected/unchanged by this story") without needing to touch either
    file.
  - **`vault_writer.record_capture_run_completed()`'s existing
    "only reached when nothing raised" semantics are deliberately
    preserved, not silently broken by this fix.** `REQ-SB-31-US-01`'s own
    Context already documents `last_capture_run.json`'s `finished_at` as a
    proxy failure signal precisely *because* an escaping exception used to
    mean this call was never reached — a currently-failing run shows up as
    an "increasingly stale timestamp," per that already-`Done` story's own
    recorded reasoning. Now that both capture steps' exceptions are
    funneled into a recorded history entry instead of propagating, this
    call would otherwise fire unconditionally every tick regardless of a
    funneled failure, quietly invalidating that already-documented System
    Health signal. Fix: `run_capture_and_record_completion` tracks whether
    either step's own `try/except` fired this tick (two local booleans) and
    calls `vault_writer.record_capture_run_completed()` only when neither
    did — the exact same observable `last_capture_run.json` behavior as
    before this fix, on top of the new, additional `"run_error"` history
    entry REQ-SB-11 needs. This is a considered design choice (grounded in
    a real, already-`Done` story's own documented reliance on the prior
    behavior), not an assumption filling an unaddressed gap — recorded here
    for durability since neither story's own Acceptance Criteria says so
    explicitly.
- **New business module `app/business/agent_activity.py`** — a **read-only
  aggregation** module, the same shape as `app/business/system_health.py`/
  `app/business/my_day.py`: writes no new persisted state, composes only
  already-existing signals, recomputes fresh on every call (Scenario 7):
  - `list_activity_log() -> list[dict]` — iterates every known agent via
    `agent_registry.list_agents()` (the same "discover ids generically,
    don't hardcode two capture agents" precedent the story's own
    Dependencies section calls for, so a future `todo-capture` agent's
    entries appear with zero code change here), reads each one's
    `vault_writer.load_agent_history(agent_id)`, keeps only `"run_event"`/
    `"run_error"`-kind entries (excluding `"chat_user"`/`"chat_agent"`/
    `"proposal"`, per the story's own Constraints scope), attaches
    `agent_name` (resolved via `agent_registry.get_agent`, the same
    display-name-resolution shape `system_health.py::
    _providers_with_agent_names` already established), and merges/sorts
    the combined list newest-first by `timestamp` — matching the approved
    prototype's own "newest first" ordering.
  - `get_agent_activity() -> dict` composes `list_activity_log()` and one
    new Outlook-reachability read (below) into `{"activity_log": [...],
    "outlook_channel": {"reachable": bool, "detail": str | None}}`.
- **New `outlook_com.py::check_reachable() -> dict`** — the one new,
  lightweight, real (but local, zero-external-cost) check this story
  needs, mirroring `system_health.py::mcp_mount_reachable()`'s own "reuse
  an already-proven connection mechanism, one cheap new check" precedent:
  attempts the exact same `Dispatch("Outlook.Application")` →
  `GetNamespace("MAPI")` connection every existing Outlook read (mail,
  calendar) already makes via the module's own `_connect_namespace()`,
  purely to report reachability. Returns `{"reachable": True, "detail":
  None}` on success, or `{"reachable": False, "detail": str(exc)}` — the
  real `OutlookUnavailable` message, e.g. "couldn't connect to Outlook —
  is it running? (...)" — on failure; never raises past its own body,
  same "honest, never left to propagate" discipline `mcp_mount_reachable()`
  already established. Sited in `data_access` (not composed ad hoc from
  `agent_activity.py` reaching into `outlook_com.py`'s private
  `_connect_namespace`) because every other Outlook COM mechanic
  (`pythoncom.CoInitialize()`, the `Dispatch`/`GetNamespace` calls, and
  now their honest failure-message construction) already lives there —
  `agent_activity.py` calls this one new public function only, the
  ordinary `api → business → data_access` layering (`ADR-003`) every
  other business module already follows.
- **New router `app/api/agent_activity_router.py`**,
  `APIRouter(prefix="/agent-activity")`, one endpoint, `GET
  /agent-activity`, returning `agent_activity.get_agent_activity()`
  verbatim. Registered in `app/main.py` alongside the existing routers —
  calls `agent_activity.py` only, no direct `data_access`/
  `agent_registry`/`outlook_com` reach-around.
- **Frontend:** a new page, `src/frontend/src/pages/AgentActivityPage.tsx`,
  at route `/agent-activity` (added to `App.tsx`'s route table, wrapped in
  the existing `<AppShell>`), plus a new `src/frontend/src/features/
  agent-activity/client.ts` (`fetchAgentActivity()` wrapping `GET
  /agent-activity` via the existing `api/client.ts` `fetch` convention,
  `ADR-010`). `Sidebar.tsx` gains one new `<NavLink>` ("Agent Activity"),
  positioned after System Health — matching the approved prototype's own
  sidebar order across every prototype page. Renders the two regions the
  approved prototype (`html-prototype/agent-activity.html`) already
  validates — the chronological Activity log (each entry's own
  success/error badge driven by `kind === "run_error"`, an error entry's
  detail rendered as a muted line beneath its summary, an honest
  empty-state when the log is empty) and the Outlook channel-status card
  (`.badge-success`/`.badge-danger` off `outlook_channel.reachable`, the
  real `detail` message shown on the unreachable state) — reusing only
  already-ported classes (`.log-list`/`.log-item`, `.badge*`, `.kv-list`,
  `.empty-state`) with **zero new CSS**, per the prototype's own "composed
  entirely from existing tokens/components" header note. A manual Refresh
  affordance re-calls `fetchAgentActivity()`; no polling/auto-refresh
  interval (the story's own Non-Goals).
- **No ADR.** Every piece above is an ordinary, same-shape extension of
  already-`Accepted` structural decisions: the honest-failure-recording
  fix applies `ADR-015`'s already-established call-site honest-failure-
  funnel pattern to a second orchestration function (extending, not
  reopening, `ADR-015` — the same "extends, does not reopen" shape
  `REQ-SB-31-US-01`'s own Scenario-8 fix and `REQ-SB-33-US-01`'s grounding-
  guardrail pass both already used on the same function family); the
  aggregation module mirrors `system_health.py`/`my_day.py`'s exact
  "read-only, composes existing business/data_access signals, no new
  persisted state" shape; `outlook_com.check_reachable()` is a same-shape
  sibling to `mcp_mount_reachable()`'s "one new lightweight in-process
  check reusing an already-proven mechanism" precedent, sited in
  `data_access` per `ADR-003`'s existing layering (Outlook COM mechanics
  already live there, nowhere else); the router is a straight
  `ADR-003`-layered addition, the same shape as `system_health_router.py`/
  `my_day_router.py`; the frontend page is an ordinary new route/page/nav
  item within `ADR-010`'s already-`Accepted` routing/styling/component
  conventions. No new tool, framework, storage mechanism, external
  round-trip, or trust-surface decision; nothing here contradicts any
  `Accepted` ADR, the PRD, or a `MEMORY.md` constraint. This also does not
  reopen or edit `ADR-011`'s `"kind"` enum — `"run_error"` is an additive
  value, the same "grow the set, don't redefine it" shape `ADR-018` point
  7 already used when it added `"proposal"` to the same field.

## Real-Time Agent Activity Pulses (REQ-SB-42-US-01, see [ADR-035](ADR.md))

A new, additive, data-driven layer over the Agents Map overview and a
Section's drill-down Agents Tree — replaces nothing (the existing
decorative `kb-pulse-dot` KB↔Hub spoke animation is unaffected by
construction, Scenario 8). Full reasoning, alternatives, and consequences:
[ADR-035](ADR.md). This section records the resulting module shape only.

- **New in-memory, module-level module `app/business/agent_presence.py`
  — no `.second-brain/` persistence, mirroring `ADR-024`'s
  `vault_indexing.py` shape one layer over.** Holds two small ephemeral
  dicts (`_active`: `agent_id -> {"kind": "capture" | "chat", "since"}`;
  `_hub_routes`: `token -> {"from_agent_id", "to_agent_id", "since"}`) plus
  an in-process `asyncio.Queue`-per-client subscriber set. `get_snapshot()`
  composes both dicts with a fresh, live read of
  `pending_approval_registry`'s own already-persisted open-approvals list
  — the steady/pending-approval highlight (Scenario 4) is never a second,
  separately-tracked copy of that state. `start_activity`/`end_activity`/
  `start_hub_routing`/`end_hub_routing` each mutate state then call
  `broadcast_snapshot()`, pushing the fresh snapshot to every connected
  client.
- **Five real dispatch call sites gain start/end (or, for pending
  approvals, a broadcast-only) instrumentation** — see `ADR-035` point 3
  for the exact call sites: `email_classification.run_capture_for_agent`
  (capture/Skill via the scheduled/Approve paths), `skill_registry.
  _dispatch_skill` (an explicit, non-conversational Skill invocation),
  `agents_router.py::chat`'s call to `run_agent_conversation` (chat
  generation — this single wrap also covers a Skill invoked mid-
  conversation via the model's own tool-calling, so that path is not
  separately marked), each real caller of `graph.
  route_cross_section_request(...)` that goes on to invoke the matched
  agent (the Hub-routed traveling pulse — currently `knowledge_bootstrap.
  bootstrap_agent_knowledge`'s two hops), and `pending_approval_registry`'s
  create/resolve functions (broadcast-only, no new state).
- **New router `app/api/agent_presence_router.py`, `GET
  /agent-presence/stream`** (SSE, `text/event-stream`) — registered in
  `main.py` alongside the existing routers. Yields an initial snapshot on
  connect, then every subsequent broadcast.
- **Frontend: new `src/frontend/src/features/agent-presence/client.ts`**,
  a thin wrapper over the browser's native `EventSource` (no new npm
  dependency) — feeds parsed snapshots into the Agents Map's existing
  per-agent-id node lookup, applying the approved prototype's own new CSS
  classes (`.agent-node--activity-glow`, `.agent-node--pending-approval`,
  `.route-pulse-dot` + `.affinity-line.active`/the drill-down's own
  captioned `.cluster-line` treatment) exactly as `html-prototype/
  agents-map.html`'s approved `REQ-SB-42` design-pass revision defines
  them.

## In-App Agent Orchestration (LangGraph) & Shared MCP Server (REQ-SB-20, REQ-SB-25, REQ-SB-26, REQ-SB-27, see [ADR-015](ADR.md))

`ADR-007`'s original "no agent-orchestration framework in Second Brain's
own stack" stance is superseded by [ADR-015](ADR.md), **bounded
specifically to Second Brain's own in-app Agents Map agent behavior** —
chat (`REQ-SB-25`), Section-Hub routing (`REQ-SB-20`), agent memory
(`REQ-SB-26`), and skill invocation (`REQ-SB-27`). Hermes's own
orchestration for its external-channel integration (`REQ-SB-03`, not yet
built) is untouched — `ADR-007`'s "Hermes owns orchestration on its own
side of the integration boundary" claim carries forward unchanged. This
section describes the mechanism this pass settles; the concrete node/
tool-level detail for each of the four requirements above is left to
their own future `/plan-tasks` passes, the same "settled home, not
pre-designed pipeline" shape `ADR-005` already established for
`app/scheduling/`.

### LangGraph — where it lives, what it composes with

- **New sub-package, `app/business/agent_orchestration/`** — the first
  sub-package under `business/` (every existing module there is a flat
  file; this is the first concern with enough internal structure to
  warrant one): `state.py` (the graph's state schema), `model_factory.py`
  (resolves a per-agent `langchain_openai.ChatOpenAI` from
  `provider_registry.get_agent_provider`/`has_real_client` — an honest
  "unavailable" signal before any model is constructed, mirroring
  `agents_router.py::_invoke_action`'s existing funnel-gate shape one
  layer over), `mcp_client.py` (a `langchain_mcp_adapters.client.
  MultiServerMCPClient` pointed at Second Brain's own MCP server, below),
  and `graph.py` (compiles **one** `langgraph.graph.StateGraph`, exposing
  `run_agent_conversation(agent_id, message, history) -> dict` as the
  module's one public entry point).
- **One graph, extended by node, not replaced per requirement.** This
  pass needs only a single model-call node (reply, tool-bound from the
  start per the operator's "build now" directive). `REQ-SB-20`/`26`/`27`
  are each expected to extend this **same** graph with additional nodes/
  conditional edges (a Hub-routing decision node; a memory-retrieval
  node; skill-invocation tool nodes) — mirroring, one layer over, the MCP
  server's own "grow by registering, not by spinning up a new instance"
  extensibility story, below.
- **Model integration: `langchain_openai.ChatOpenAI`, not an extension of
  `app/data_access/compass_client.py`.** `compass_client.py` is
  **untouched** — it keeps its one existing fixed-shape `classify_email`
  function, called only by the linear email-classification pipeline
  (`ADR-007`'s original "simple linear pipelines stay outside any
  orchestration framework" carve-out, unaffected and unreconsidered by
  `ADR-015`). `ChatOpenAI` is instantiated per-call with `base_url`/
  `api_key`/`model` sourced from the agent's resolved Provider record —
  `REQ-SB-19`'s Provider registry stays the single source of LLM
  connection configuration for this new surface too. Confirmed
  compatible with Compass by `compass_client.py`'s own docstring
  ("Compass speaks the same wire format as OpenAI's `/chat/completions`")
  — the same reason `ChatOpenAI`'s `base_url` override works against it.
- **`ADR-011`'s keyword-match fast path is kept, unedited — coexistence,
  not supersession.** `app/business/agent_chat.py` is **not modified**.
  Only `app/api/agents_router.py::chat`'s no-trigger-phrase-match branch
  changes: instead of returning the old static canned fallback string, it
  calls `agent_orchestration.run_agent_conversation(agent_id, message,
  history)` and returns its real reply (or an honest unavailability/
  failure message) in its place. A trigger-phrase match still bypasses
  this entirely, exactly as today — no LLM call, no behaviour change.
- **Conversation-state source of truth stays `.second-brain/
  agent_communication_history.json` — no LangGraph persistent
  checkpointer for cross-request state.** `agents_router.py::chat` reads
  that agent's existing history (`vault_writer.load_agent_history`,
  already used for `GET /agents/{id}/history`) and passes the relevant
  recent turns into `run_agent_conversation`'s `history` argument as the
  graph's initial state on every call; the graph itself runs statelessly
  per HTTP request (`.invoke()`), not via a persistent, thread-ID-keyed
  checkpoint. This deliberately avoids a second, potentially-divergent
  conversation-history store — consistent with this project's repeated
  rejection of adding a database/SQLite for local state (`ADR-005`,
  `ADR-011`, `ADR-014`). No entry-`kind` schema change to
  `agent_communication_history.json` results.
- **Package: `langgraph` (`>=1,<2`, pinned to the current stable major —
  pin-then-verify-at-real-install, per this project's own established
  `react-router` pattern), plus `langchain-openai` and
  `langchain-mcp-adapters`.** Python floor `>=3.10`, comfortably inside
  this project's Python 3.14 (`ADR-001`). The genuinely open,
  honestly-flagged risk — whether every transitive compiled dependency
  (chiefly `pydantic-core`) has a prebuilt Windows `cp314` wheel — is
  partially de-risked already: `pydantic-core` (via the already-installed
  `pydantic-settings`) already works on this exact host's real `.venv`
  today. The remaining surface must be confirmed by the coder task's own
  real `pip install`, not assumed. Full reasoning: [ADR-015](ADR.md).

### Shared MCP server — vault-query tools, one implementation reused both ways

- **New `app/business/vault_query_tools.py`** — the actual tool
  *implementations*, thin business-layer functions over already-existing
  read-only `vault_writer` primitives (`list_known_customers`,
  `list_known_kinds`, `list_known_partners`, `list_notes_in_kind_folder`)
  — no new `data_access` reads, per `ADR-003`. Sibling to
  `agent_orchestration/`, not nested inside it — a general capability,
  not orchestration-specific.
- **New `app/api/mcp_server.py`**, api-adjacent (a protocol/transport-
  translation layer, analogous to a router but mounted, not included) —
  builds an `mcp.server.fastmcp.FastMCP` instance, registers
  `vault_query_tools.py`'s functions as `@mcp.tool()`s, and is wired into
  `app/main.py` via `app.mount("/mcp", ...)` (Streamable HTTP transport)
  alongside the existing `app.include_router(...)` calls — no new port,
  no new process, the same single-process precedent `ADR-005` already
  established. Hermes reaches this MCP server over the same host:port as
  every other Second Brain HTTP surface.
- **The in-app LangGraph agents consume the *same* server, not a second
  parallel tool-registration path.** `agent_orchestration/mcp_client.py`'s
  `MultiServerMCPClient` connects to the same mounted `/mcp` endpoint
  over a loopback HTTP call — the in-app agent is simply another MCP
  client, indistinguishable in principle from Hermes — rather than
  importing `vault_query_tools.py`'s functions directly and re-wrapping
  them a second time with LangChain's own `@tool` decorator. A tool's
  name/description/argument-schema is therefore declared **exactly
  once**, in the MCP server's own registration, consumed identically by
  both callers.
- **Extensibility: register new tools on the same server, not a new
  server per capability.** `REQ-SB-27`'s skills, once that story resolves
  its own "what is a skill" question, become new `@mcp.tool()` entries on
  this same server — a second MCP server is the exception (a genuinely
  separate concern), not the default extension path.
- **Relation to the existing REST API — parallel, not a replacement.**
  `agents_router.py`'s existing endpoints are unchanged in shape (only
  the chat fallback body, above) and continue to serve the in-app
  frontend's own settings/actions/chat/history UI. The MCP server exposes
  read/query-style vault tools using MCP's own tool-invocation semantics
  for LLM/agent tool-calling — a structurally different consumer, at a
  distinct path prefix, in the same process.
- **First tools are illustrative, not mandated by this pass** — since
  `REQ-SB-01`/`REQ-SB-02` (Vault Indexing & Browse/Search) don't exist
  yet, the first genuinely useful tools are thin wrappers over the
  read-only primitives named above. Exact task-level sequencing is each
  implementing story's own `/plan-tasks` decision.
- **Package: the official `mcp` Python SDK** (`mcp`, PyPI) — its
  `FastMCP` high-level API, over a hand-rolled JSON-RPC/protocol
  implementation, per this project's repeated "prefer an already-solved
  library" precedent (`ADR-005`, `ADR-008`). Python floor `>=3.10`.

### Addendum (REQ-SB-04-US-01, 2026-08-13) — `/mcp` shared-secret authentication + a write-capable MCP tool that always routes through Pending Approvals, see [ADR-025](ADR.md)

`REQ-SB-04-US-01` (Agent Vault Write Access) is the first story to (a) put
any authentication at all on `/mcp` and (b) register a write-capable tool on
the shared MCP server. Both extend, rather than reopen, the "Shared MCP
server" subsection directly above.

- **New `app/api/mcp_auth.py`** — a small ASGI middleware,
  `require_hermes_shared_secret(app)`, wrapping only the `/mcp` mount (not
  the whole FastAPI app — `app.mount()` takes a raw ASGI app and has no
  `Depends()`-style hook to attach to). Loopback callers
  (`scope["client"][0]` in `{"127.0.0.1", "::1"}`) pass through unchecked —
  Second Brain's own in-app LangGraph agent (`agent_orchestration/
  mcp_client.py`, already live since `REQ-SB-25-US-01`) is unaffected by
  construction, not by a conditional exemption. Any other caller must
  present a matching `X-Hermes-Shared-Secret` header or is rejected `401`
  before the underlying FastMCP app ever sees the request. `app/main.py`
  now mounts `require_hermes_shared_secret(mcp_server.streamable_http_app())`
  in place of the bare app. New `Settings.hermes_mcp_shared_secret: str`
  (`.env`-sourced), mirroring `compass_api_key`/`anthropic_api_key`'s
  existing shape exactly. **This mechanism is shared infrastructure, not
  `REQ-SB-04`-specific** — `REQ-SB-03-US-01`'s own future `/plan-tasks` pass
  (still `status: Draft`, unbuilt) inherits it as already-decided; see
  `ADR-025` point 3.
- **New `app/business/vault_write_tools.py`** (sibling to
  `vault_query_tools.py`) — `propose_vault_write(agent_id, subfolder,
  filename_stem, frontmatter, body) -> dict`, registered as a fifth
  `@mcp_server.tool()` on the same shared FastMCP instance (`ADR-015`
  point 9's "register, never a new server" rule). It **never writes
  directly.** An unknown `agent_id` (not resolvable via `agent_registry.
  get_agent`) is rejected outright. A known agent's proposed target is
  checked against its `REQ-SB-29`-assigned scope via a seam function,
  `_is_within_assigned_scope(...)` — **fail-closed**: since
  `REQ-SB-29-US-01` has no real scope registry yet (still `status: Draft`,
  never decomposed), this seam's body is `return False` until that story
  ships one, so every write is honestly rejected as out-of-scope for now,
  never silently allowed. Once in scope, `pending_approval_registry.
  create_pending_approval(agent_id, trigger="hermes", action_id=
  "hermes_vault_write", payload={...})` is called — a new `trigger` value,
  added the same way `ADR-020` added `"hub_routed"` — and the tool returns
  a `pending` status with the new record's id. **This check is
  unconditional, regardless of the agent's own working mode** — it never
  consults `working_mode_registry`, extending `ADR-021` point 5's own
  Tier-2 "bypasses the working-mode gate by construction" precedent to a
  second, independent case (a materially bigger trust surface than in-app
  actions, per the story's own Context).
- **`pending_approvals_router.py`'s existing `_APPROVAL_HANDLERS` table
  gains one entry**, `"hermes_vault_write":
  vault_write_tools.finalize_hermes_write` — calls `vault_writer.write_note`
  with the record's stored `payload` and returns `{"path": ...}`, matching
  `finalize_new_top_level_area`'s own return shape (`ADR-021` point 5). No
  new collision-avoidance/merge primitive — reuses `write_note`'s existing
  unconditional-overwrite semantics as-is, matching the story's own
  Scenario 1 text ("a new *or modified* note appears"). Decline needs no
  new code — the existing decline endpoint already handles any
  `"pending"` record regardless of `action_id`/`trigger`.
- **Full reasoning, alternatives, and consequences:** `ADR-025`.
  `REQ-SB-04-US-01`'s own scope-enforcement (Scenarios 1/2) cannot be
  live-verified until `REQ-SB-29-US-01` ships a real scope registry — a
  real, load-bearing, honestly-recorded blocker (`ESCALATIONS.md` →
  `ESC-026`), not silently worked around.

### Agent-to-Tag/Folder Vault Scoping — assignment & scope-bounded retrieval (`REQ-SB-29-US-01`, no new ADR)

The operator resolved the retrieval-mechanism question on 2026-08-12 (see the
story's own `## Notes`, `ESC-008` → `Resolved`): a narrower, story-scoped ad
hoc primitive built directly against the vault, not a wait on `REQ-SB-01`/
`REQ-SB-02` (neither has a story yet). Everything below is the architect's
confirmation of *shape* against already-`Accepted` precedent — no genuinely
new tool, framework, storage mechanism, or trust-surface decision is made
here, so **no new ADR**, matching this codebase's own repeated "same-shape
extension of already-Accepted structure" precedent (e.g. the
`REQ-SB-12-US-02`/`REQ-SB-30-US-01` passes, above).

- **Assignment storage: mirrors `agent_keywords.json`'s shape, not
  `agent_sections.json`'s.** A vault scope (one or more tags/folders per
  agent) carries no separate, shared, renameable identity the way a Section
  or Provider does — the same reasoning `ADR-017`'s own keyword-storage
  decision already recorded. New sibling `.second-brain/agent_scopes.json`,
  `{agent_id: [tag_or_folder: str, ...]}`. New `vault_writer.py`
  primitives, `load_agent_scope(agent_id)` / `save_agent_scope(agent_id,
  scope)` / `load_all_agent_scopes()`, mirroring `load_agent_keywords`/
  `save_agent_keywords`/`load_all_agent_keywords`'s exact shape. New
  `app/business/scope_registry.py` (sibling to `agent_keywords.py`,
  composed *alongside* `agent_registry.py`, unmodified): `get_agent_scope`/
  `set_agent_scope` (whole-list replace, the same free-text kv-list editing
  UX already used for Keywords).
- **API: one more optional field on the existing `PATCH
  /agents/{agent_id}`**, not a new sub-resource — `agents_router.py`'s
  `AgentAssignmentUpdateBody` (already `section_id | provider_id | keywords
  | working_mode`, all optional) gains `scope: list[str] | None = None`;
  `update_agent_assignment` gains one more `if body.scope is not None:
  scope_registry.set_agent_scope(agent_id, body.scope)` branch, mirroring
  the existing `keywords` branch exactly. `GET /agents/{agent_id}`'s
  response gains `"scope": scope_registry.get_agent_scope(agent_id)`,
  alongside the existing `"keywords"` key.
- **Retrieval primitive: `vault_writer.list_notes_matching_scope(scope:
  list[str]) -> list`, mirroring `list_known_customers()`'s/
  `list_notes_in_kind_folder()`'s exact shape** — iterates
  `list_all_note_paths()`, reads each note's frontmatter, and matches a
  note whose `tags` list intersects `scope` or whose vault-relative path
  falls under a folder named in `scope`. **Must NOT compose
  `vault_indexing.get_index()` or anything in `vault_search.py`**
  (`ADR-024`/`ADR-026`, `REQ-SB-01`/`REQ-SB-02`) — the story's own
  Constraints are explicit that this primitive is independent of those
  still-unbuilt requirements; reusing the indexer, even though it now
  technically exists, would silently reintroduce the exact dependency the
  operator's 2026-08-12 decision rejected. Tag-vs-folder disambiguation
  inside the primitive is ordinary `/plan-tasks` implementation latitude,
  not a further architectural fork.
- **Tool wiring: a new `@mcp_server.tool()`, registered on the SAME shared
  MCP server** (`ADR-015` point 9's "register, never a new server per
  capability" rule — the same rule `vault_write_tools.propose_vault_write`
  already extended it with), **not a plain passthrough like
  `vault_query_tools.py`'s existing four read-only tools.** Scenarios 4 and
  6 require the tool itself, not the calling model, to determine and
  enforce the requesting agent's scope — so the new tool follows
  `vault_write_tools.propose_vault_write`'s established shape instead:
  an explicit, required `agent_id` parameter the calling agent supplies (an
  unknown `agent_id` is rejected outright, matching
  `propose_vault_write`'s own unknown-agent handling), with the business
  layer resolving that agent's real assigned scope server-side via
  `scope_registry.get_agent_scope(agent_id)` — the tool never accepts a
  freeform `tags`/`folders` argument from the model. An empty assigned
  scope returns an explicit "no bounded vault query access" result
  (Scenario 6), never a silent whole-vault search; a non-empty scope with
  no matching notes returns an explicit "nothing found" result (Scenario
  5), never a fabricated one — both compose with `REQ-SB-33`'s already-
  live grounding/honest-uncertainty system-prompt instruction
  (`history_entries_to_messages`), not a new honesty mechanism. Exact
  module placement (a new sibling module, e.g. `scope_query_tools.py`, or
  a new function inside `vault_query_tools.py`) is decomposer/coder
  latitude.
- **Load-bearing for `ADR-025` point 6 (`ESC-026`) — but that seam's own
  real implementation is NOT this story's task.** `ADR-025` point 6
  fail-closes `vault_write_tools._is_within_assigned_scope(...)` pending
  "a real per-agent scope lookup this seam can call." `scope_registry.
  get_agent_scope(agent_id)` (above) is that lookup — its module/function
  name and signature are a small stable contract a future
  `REQ-SB-04-US-01` task depends on, so the decomposer should treat it as
  effectively public API, not private to this story's own retrieval
  feature. Wiring `_is_within_assigned_scope`'s body to actually call it
  is `REQ-SB-04-US-01`'s own future task (still blocked, no task id exists
  yet — `ESC-026` stays `Open` until that story is decomposed and built;
  this story does not close `ESC-026` by itself).
- **Frontend: a new "Vault scope" row on `AgentDetailPanel.tsx`'s existing
  Settings `kv-list`, following the Keywords row's pattern, not the
  Section/Provider `<select>` pattern.** Scope is user-typed, multi-value,
  free-form tags/folder paths — not a small fixed catalog — so it follows
  Keywords' exact "single `<input>`, comma-separated, `onBlur` commit via
  `updateAgentAssignment(agentId, { scope: [...] })`" shape (own local
  `scopeDraft` state, split-trim-filter on blur), not the Section/Provider
  `<select>`-against-a-fetched-list shape. `agentsApiClient.ts`'s
  `AgentDetail`/`updateAgentAssignment` gain a `scope: string[]` field, the
  same additive-field precedent `keywords` already established. No new
  component, panel, or interaction pattern — this is the story's own
  established "not net-new-design" instruction: match
  `REQ-SB-18/19/20/21`'s already-built row language exactly (per the
  operator's decision to skip `/design` for this story), not invent a new
  visual shape for the missing prototype coverage.
- **Non-Goals respected by construction:** no boolean/compound scope
  queries (the primitive is a straightforward tag/folder membership
  match); no automatic scope inference (assignment is explicit,
  user-typed, via the kv-row above only); no change to `REQ-SB-20`'s
  Keywords field or Hub-routing mechanism (a fully separate
  `.second-brain/` file, business module, and kv-row).

### Addendum (REQ-SB-50-US-01, tag/folder autocomplete on the Vault Scope field, no new ADR)

The already-shipped `scopeDraft`/`handleScopeCommit` free-text `<input>`
(above) gains a suggestion dropdown sourced from the new `GET
/vault-search/scope-suggestions` endpoint (see "Tag/Folder Scope
Suggestions" under "Browse & Search", above) — the field's own established
free-text/comma-separated/`onBlur`-commit mechanism is unchanged;
suggestions are additive UI on top of it, not a replacement input control
(`REQ-SB-50-US-01`'s own Constraints). Scope confirmed narrow to this one
field only — `CreateAgentWizard.tsx`'s Worker-step Scope field is
deliberately deferred to a follow-on once `REQ-SB-46`'s still-`Draft`
wizard redesign settles that field's own eventual shape (see the story's
own Context).

- New `fetchScopeSuggestions()` (`features/vault-browser/client.ts`)
  imported cross-feature into `AgentDetailPanel.tsx`.
- **Fetched once per agent-switch inside the panel's existing agent-load
  `useEffect`**, mirroring `fetchSections()`/`fetchProviders()`'s identical
  fetch-on-mount shape — even though the suggestion data itself is
  vault-wide, not agent-specific, this keeps the fetch inside the same
  already-established lifecycle rather than introducing a second,
  differently-scoped effect.
- New local `scopeSuggestions` state (`{tags, folders} | null`), filtered
  client-side against the in-progress last comma-segment of `scopeDraft`
  as the user types (substring/prefix match — no fuzzy matching, per the
  story's own Non-Goals) — rendered as a small suggestion dropdown beneath
  the existing Vault Scope `<input>`, offered as two labeled groups (Tags /
  Folders) matching the endpoint's own two-list shape. No new component or
  route — this augments the existing `kv-row` in place, matching the
  story's own "not net-new-design" scope decision (this row already has no
  approved prototype coverage, a pre-existing, unresolved-by-this-story
  gap — see the story's own Notes → Prototype parity).
- **Interaction-order note for the coder:** the field's existing
  `onBlur={handleScopeCommit}` already commits the draft on blur.
  Selecting a suggestion by click must use `onMouseDown` (not `onClick`)
  on the suggestion item — a plain click fires the input's `onBlur` first,
  committing the draft (and unmounting the dropdown) before any `onClick`
  handler would ever run, silently losing the selection. This is a genuine
  interaction-order pitfall the existing Keywords/Vault-scope
  `onBlur`-commit pattern never previously had to consider (no dropdown
  existed before this story) — recorded explicitly so the coder does not
  discover it mid-build.
- Selecting or committing a typed suggestion joins the existing
  comma-separated list via the same `split → trim → filter → join`
  round-trip `handleScopeCommit` already performs — no change to that
  function's own dedup/ordering behaviour (Scenario 4).

### Addendum (REQ-SB-25-US-01 architecture-scoping confirmation, 2026-08-12) — message shape for `run_agent_conversation`, no ADR change

At `/plan-tasks` for `REQ-SB-25-US-01`, the architect confirmed `ADR-015`
already covers everything that story's own build needs — package set,
`agent_orchestration/` layering, the `model_factory.py` unavailability
funnel-gate (Scenario 4), the coexistence-not-supersession composition
with `ADR-011` and the exact `agents_router.py::chat` edit (Decision
point 5), the `agent_communication_history.json`-as-source-of-truth
call (Scenario 3, Scenario 5's honest-failure-recording), and the
broad/reusable-over-narrow reusability decision the story's own flagged
sub-question raised. **No new or changed ADR resulted.** One genuine,
narrower gap remained — `ADR-015`'s own `run_agent_conversation(agent_id,
message, history: list[dict]) -> dict` signature settles the *interface*
but not how `history` (already exactly `vault_writer.load_agent_history(
agent_id)`'s existing shape — `[{"kind": "chat_user" | "chat_agent" |
"run_event", "text": str, "timestamp": iso8601}, ...]`) becomes the
graph's replayed LangChain message list. Resolved now, as an ordinary
mechanism-filling detail within `ADR-015`'s already-decided shape (not a
new tool/framework/structural-boundary choice, so no ADR is warranted):

- `state.py`'s history-to-messages step maps `"chat_user"` entries to
  `HumanMessage(content=text)` and `"chat_agent"` entries to
  `AIMessage(content=text)`; `"run_event"` entries are **excluded** from
  the replayed message list — they are action-trigger audit-log entries
  (`ADR-011`/`REQ-SB-13-US-01`'s own shape), not conversational turns, and
  presenting one to the model as something the user or agent "said" would
  be actively misleading, not merely noisy.
- One `SystemMessage` is prepended, sourced from
  `agent_registry.get_agent(agent_id)`'s existing `name`/`type` fields
  (e.g. "You are the {name} agent for the user's personal Second Brain
  knowledge base.") — minimal identity/purpose grounding only; nothing in
  `REQ-SB-25`'s acceptance text asks for a longer persona/instruction
  prompt, so none is invented.
- **No history window/truncation this pass** — the full existing history
  list for that agent is replayed on every call, matching Scenario 3's
  "aware of the earlier turns" literally. A token-budget/cost concern is
  `REQ-SB-24`'s own separate, not-yet-built scope (per-agent token/cost
  tracking) — not pre-empted here; revisit if a real conversation's
  length becomes a genuine problem in practice.

### Addendum (REQ-SB-33-US-01 agent grounding & honest-uncertainty guardrail, 2026-08-12) — system-prompt instruction only, no ADR change

`REQ-SB-33-US-01` extends `history_entries_to_messages`'s existing
prepended `SystemMessage` (the exact one the REQ-SB-25-US-01 addendum
above already settles the shape of) with one additional instruction,
appended to that same message's own content string — **not** a second
`SystemMessage`. This is a deliberate distinction from the
`_retrieve_memory`/`ADR-016` precedent (which *does* insert a second
`SystemMessage`, because stored per-agent memory is a genuinely separate,
per-conversation-varying concern): grounding/honest-uncertainty guidance
is the same *category* of content as the existing identity/purpose
sentence — static, agent-generic, present on every call — so it belongs
in the one static identity `SystemMessage`, not a second message. Ordinary
mechanism-filling detail within `ADR-015`'s already-decided shape — no new
node, no new state file, no new tool/framework/structural boundary — so no
ADR is warranted, confirming the story's own `## Notes` resolution trail
(the analyst's own reasoning is independently concurred with here, not
merely accepted on faith).

- The instruction's substance (exact coder-owned wording is a task-level
  detail, not fixed here): answer only from what this conversation's own
  tool results, replayed history, and stored memory actually contain;
  when nothing relevant was retrieved for an in-scope question, say so
  honestly rather than answering from the model's own general training
  knowledge as if it were a vault fact; a failed/erroring tool call
  (surfaced to the model as a `ToolMessage` reading `"Tool call failed:
  ..."`, per `_execute_tools`'s existing shape) is not license to
  fabricate a substitute answer — the model must instead honestly report
  that it could not retrieve one.
- **Global, not agent-specific — no new parameter, no new branch.**
  `history_entries_to_messages` is the one shared function every agent's
  conversation already runs through (`REQ-SB-25`); the added instruction
  text is unconditional, present in the one `SystemMessage` on every call
  for every agent, matching the story's own "every agent's... grounded"
  requirement-text reading. No per-agent opt-out field, no new
  `agent_registry.py`/Agent Settings surface — `ADR-011` point 2's "which
  agents exist is app/deployment configuration, not vault content"
  boundary is untouched.
- **No verification/citation node; `_call_model` itself is not
  restructured.** This story's own Constraints explicitly scope the
  mechanism to the prompt input only — a real check-the-reply-against-
  real-tool-results step is named, explicitly, as legitimate future
  escalation, not this pass's scope. `_execute_tools`, `_retrieve_memory`,
  `_extract_memory` are unmodified; only `history_entries_to_messages`'s
  own `SystemMessage` construction changes.
- **Honest limitation carried forward, not newly invented:** a
  system-prompt instruction is not a hard technical enforcement
  guarantee — this mirrors the exact same limitation `ADR-016`'s own
  `extract_memory` "never invent a fact" instruction already accepts for
  memory extraction; verification for both is live prompting behavior,
  not a mechanical check.

### What this pass does not decide

- **`REQ-SB-20`'s per-agent keyword storage and routing-node mechanism** —
  **now resolved, 2026-08-12, by [ADR-017](ADR.md)** (`REQ-SB-20-US-01`'s
  own architecture pass) — see "Section-Hub cross-Section routing —
  keyword storage & routing-node mechanism," below. Its own Context/
  Constraints text (recorded before `ADR-015` existed, "keyword
  matching... no `ADR-007` tension... no superseding ADR needed") has
  been reconciled in its own `## Notes`, closing `ESCALATIONS.md` →
  `ESC-010`. Its externally observable Acceptance Criteria remain
  unaffected by either ADR.
- **`REQ-SB-26`'s memory extraction/summarization mechanism** — was only
  the storage location this ADR settled (a new sibling `.second-brain/
  agent_memory.json`, consumed by a graph memory-retrieval node). **Now
  resolved, 2026-08-12, by [ADR-016](ADR.md)** (`REQ-SB-26-US-01`'s own
  architecture pass) — see "Agent Memory — extraction mechanism," below.
- **`REQ-SB-27`'s "what is a skill" architectural shape** (`ESC-006`,
  still `Open`) — this ADR only settles that whatever shape it resolves
  to plugs into this same graph and MCP server as additional nodes/tools,
  not a separate mechanism. **Update, 2026-08-12:** the registration/
  per-agent-access plumbing half of `REQ-SB-27` is now scoped — see
  "Skills Repository — registration & per-agent access", above; the first
  real skill's implementation remains deferred, and `ESC-006`'s
  default-vs-explicit-access and `REQ-SB-28` sub-questions remain `Open`.
- **`REQ-SB-21`'s Supervised working-mode/approval interaction** with a
  graph-based conversational surface (e.g. LangGraph's own `interrupt()`
  primitive) — genuinely relevant, not resolved here.

Full reasoning, every alternative considered, and every consequence:
[ADR-015](ADR.md).

### Agent Memory — extraction mechanism (`REQ-SB-26`, see [ADR-016](ADR.md))

`REQ-SB-26-US-01`'s own architecture pass resolves the one question
`ADR-015` point 13 deliberately left open — *what* the memory-retrieval
node actually stores/reads, not just *where*. Extraction is **LLM-based**
(a real Provider-backed completion extracting durable facts), not a
hand-rolled heuristic — the acceptance text places no constraint on what
shape of information a user might share, the same "prefer the real
mechanism over a hand-rolled heuristic for open-ended natural language"
reasoning `REQ-SB-25`/`ADR-015` already applied to conversational replies
themselves.

- **Two new nodes on `ADR-015`'s single existing compiled graph**
  (`app/business/agent_orchestration/graph.py`) — not a second graph:
  - **`retrieve_memory`** (read path, before `call_model`): performs no
    file I/O itself — `agents_router.py::chat` loads the agent's stored
    memory via a new `vault_writer.load_agent_memory(agent_id) ->
    list[dict]` primitive (mirrors `load_agent_history`) and passes it
    into `run_agent_conversation` as a new `memory: list[dict]`
    parameter, alongside the existing `history` parameter.
    `retrieve_memory` folds those facts into the graph's initial message
    list (a second `SystemMessage`, appended after the existing
    agent-identity one) before `call_model` runs.
  - **`extract_memory`** (write path, after `call_model`, same graph,
    same `.invoke()` call — no second Provider resolution): reuses the
    already-resolved/bound model to issue one additional, narrowly-scoped
    completion identifying any new durable fact(s) worth remembering from
    the latest exchange (explicitly instructed to return none rather than
    inventing one — Scenario 3's "honest, not fabricated" posture one
    layer over), producing `extracted_facts: list[str]` on graph state —
    not written to disk by the graph. Skipped entirely when `call_model`
    itself errors. `run_agent_conversation`'s return shape gains
    `extracted_facts` (additive to the existing `{"reply"} | {"error"}`
    shape). `agents_router.py::chat` persists any returned facts via a
    new `vault_writer.append_agent_memory_entries(agent_id, facts:
    list[str]) -> None` primitive, called alongside its existing
    `append_agent_history_entry` calls — the same "router persists
    post-graph side effects" shape already established for conversation
    history.
- **New state, `.second-brain/agent_memory.json`** (`ADR-015` point 13's
  already-settled location): `{agent_id: [{"fact": str, "recorded_at":
  iso8601}, ...]}` — a flat, append-only list of short extracted-fact
  strings per agent, not raw message objects. No dedup/merge/
  consolidation this pass; a growing list, not a maintained profile.
- **Retrieval is unfiltered** — the full stored fact list for that
  `agent_id` is folded into every call, no similarity search/ranking/
  vector index, mirroring the "no truncation this pass" precedent already
  established for conversation-history replay. Revisit only once real
  memory volume is observed to strain a real Provider's context window.
- **A second real LLM completion now happens on every successful
  conversational reply** (extraction, alongside the reply) — a genuine
  cost/latency consequence, named explicitly, accepted for a personal
  single-user assistant at today's expected volume.
- Full reasoning, alternatives considered (including why raw
  cross-conversation replay, a hand-rolled heuristic extractor, a
  separate out-of-graph LLM call, a single combined structured-output
  call, and embedding-similarity retrieval were each rejected), and every
  consequence: [ADR-016](ADR.md).

### Section-Hub cross-Section routing — keyword storage & routing-node mechanism (`REQ-SB-20`, see [ADR-017](ADR.md))

`REQ-SB-20-US-01`'s own architecture pass resolves the two questions
`ADR-015` point 12 deliberately left open — per-agent keyword storage
shape, and the concrete node/edge design implementing "how a Hub
decides." The routing **algorithm** itself is unchanged from that
story's own original operator resolution: deterministic, case-insensitive
keyword-substring matching, first-match-wins, exactly `ADR-011`'s
existing posture — no LLM is involved in the match. Only the algorithm's
*housing* moves onto `ADR-015`'s graph.

- **New sibling `.second-brain/agent_keywords.json`**, `{agent_id:
  [keyword: str, ...]}` — a flat, per-agent-id-keyed list, mirroring
  `agent_communication_history.json`/`agent_memory.json`'s existing
  shape (`ADR-011`/`ADR-016`), not `agent_sections.json`/
  `agent_providers.json`'s registry+assignments shape — keywords carry no
  separate, shared, renameable identity the way a Section or Provider
  does, so the simpler per-agent-list mirror is the closer fit. New
  `vault_writer.py` primitives: `load_agent_keywords(agent_id)`,
  `save_agent_keywords(agent_id, keywords)`, and a new whole-file read,
  `load_all_agent_keywords() -> dict[str, list[str]]` (needed by the
  routing node's cross-agent scan — no existing primitive reads an entire
  per-agent-keyed store at once).
- **New `app/business/agent_keywords.py`** (sibling to
  `section_registry.py`/`provider_registry.py`, composed *alongside*
  `agent_registry.py`, unmodified): `get_agent_keywords`/
  `set_agent_keywords` (whole-list replace, matching the free-text
  kv-list editing UX already used elsewhere on the Agent Settings panel),
  and `list_candidate_agents_for_keyword_match(requesting_agent_id,
  need_description)` — composes `section_registry.get_agent_section`/
  `list_sections` (to exclude the requester's own Section — cross-Section
  only, per this story's own Constraint deferring within-Section routing)
  and `agent_registry.list_agents`. An agent with an empty keyword list
  is structurally never a match candidate (Scenario 4, satisfied by
  construction).
- **One new node, `route_hub_request`, on `ADR-015`'s SAME compiled
  `app/business/agent_orchestration/graph.py` `StateGraph`** — not a
  second graph — reached via a new conditional edge from the existing
  `call_model` node, triggered by a new, **orchestration-internal**
  LangChain tool, `request_cross_section_help(need_description: str)`,
  bound to the model alongside the existing vault-query tools. This is
  this codebase's first real tool-execution loop (today's `call_model`
  binds tools but has no conditional edge/loop-back at all): on a tool
  call, the graph routes to `route_hub_request` instead of `END`, then
  loops back to `call_model` with the routing outcome as a `ToolMessage`
  so the requesting agent's own model composes its final reply around it
  (Scenario 3's honest-no-fabrication bar). The module also exposes
  `route_cross_section_request(requesting_agent_id, need_description) ->
  dict` directly, the same "public entry point, directly testable"
  convention `T07` already established for `run_agent_conversation`.
- **The mandatory "own Hub, then target Hub" two-hop relay is two
  sequential lookups inside the ONE node**, not two separate nodes
  (unlike `ADR-016`'s `retrieve_memory`/`extract_memory` split — the
  "own Hub" hop here has no real branch/failure mode of its own, unlike
  each of `ADR-016`'s two genuinely separate LLM completions): (a)
  `section_registry.get_agent_section(requesting_agent_id)` — the first
  hop; (b) `agent_keywords.list_candidate_agents_for_keyword_match(...)`
  — the second hop, cross-Section only. Returns `{"matched": True,
  "agent_id", "section_id"}` on the first match, or `{"matched": False}`
  on an exhaustive no-match (Scenario 3) — both hops recorded as explicit
  result fields, a real inspectable property, not just a narrative
  description of the code path.
- **`request_cross_section_help` is deliberately NOT registered on the
  shared MCP server** (`app/api/mcp_server.py`) — it stays a local,
  `agent_orchestration`-internal LangChain tool, never loaded through
  `mcp_client.py`'s loopback client. The shared server's whole purpose
  (`ADR-015` points 7-9) is one tool surface reused identically by Hermes
  and the in-app agents; Hermes has its own, separate, external Section/
  Department/Hub concept (`MEMORY.md`), and this story's own Non-Goals
  explicitly reject syncing with it — registering this tool on the
  shared server would hand Hermes a callable into Second Brain's own
  internal agent-routing machinery.
- Full reasoning, alternatives considered (including why the literal
  `agent_sections.json` mirror, an MCP-server-registered tool, an
  LLM-based match, a standalone non-graph function, and a two-node hop
  split were each rejected), and every consequence: [ADR-017](ADR.md).

### Vault Filing Expert — placement decision, Tier-1 write, Tier-2 approval override (`REQ-SB-35`, see [ADR-021](ADR.md))

**A new registry agent, `"vault-filing-expert"`** (type `expert`), a plain
new `app/business/agent_registry.py` entry — reached exclusively via
`ADR-017`'s already-real `graph.route_cross_section_request(...)`, never a
shared skill (operator-confirmed, "This is an Agent"). Its own placement/
write mechanism lives in a new `app/business/vault_filing_expert.py`:

- `determine_placement_and_file(content, source_description,
  requesting_agent_id) -> dict` pre-fetches `list_known_kinds()`/
  `list_known_customers()`/`list_known_partners()` deterministically (plain
  Python calls, not a bound-tool reasoning loop), embeds them plus the
  vault's own design-methodology guidance into one `model_factory.
  resolve_agent_model("vault-filing-expert")` completion, and gets back a
  structured `{"kind", "is_new_top_level_area", "tags", "filename_stem",
  "body", "confidence", "uncertainty_note"}` decision. `is_new_top_level_
  area` is re-checked in Python (`kind in list_known_kinds()`), never
  trusted from the model's own boolean alone.
- **Tier 1** (existing `kind`, or a new tag/subfolder within one) writes
  immediately via the already-fully-generic `vault_writer.write_note(
  f"Work/{kind}", ...)` — no new low-level write primitive needed, since
  `write_note`'s own `mkdir(parents=True, exist_ok=True)` already handles a
  brand-new folder transparently. Low-confidence decisions are prefixed
  with a visible uncertainty marker (Scenario 6), independent of the Tier
  axis.
- **Tier 2** (genuinely new top-level area) never reaches
  `agents_router.py::_invoke_action`'s working-mode-gated funnel at all —
  it unconditionally calls `pending_approval_registry.
  create_pending_approval(agent_id="vault-filing-expert", trigger="direct",
  action_id="propose_new_top_level_area", description=...)`, bypassing the
  working-mode gate **by construction**, not by an override flag on it —
  the concrete mechanism behind the operator's "not a change to the
  agent's own general working-mode assignment" framing. `ADR-018`'s
  `agent_pending_approvals.json` schema (unedited by `ADR-020`) gains one
  additive `"payload": dict | null` field carrying the proposed
  `kind`/`tags`/`filename_stem`/`body`; `pending_approvals_router.py`'s
  Approve path gains a small `_APPROVAL_HANDLERS` dispatch table
  (mirrors `agents_router.py`'s `_ACTION_HANDLERS`/`skill_registry.py`'s
  `_SKILL_HANDLERS`) mapping `"propose_new_top_level_area"` to a second
  public function, `vault_filing_expert.finalize_new_top_level_area(
  payload)`, which performs the actual `write_note` call only once
  approved. Decline takes no further action — the content is never filed
  under the declined area, never silently retried elsewhere.

**A real, currently unmet blocking prerequisite, not silently assumed
satisfied:** Tier 2's own coder task needs `REQ-SB-21-US-01`'s Pending-
Approvals mechanism (`pending_approval_registry.py`,
`agent_pending_approvals.json`, `pending_approvals_router.py`) to actually
exist in code. Direct inspection during this pass found `REQ-SB-21-US-01`
is `status: Draft`, `gate: flagged`, and none of that mechanism has been
built — see [ADR-021](ADR.md)'s own Context and `ESCALATIONS.md` →
`ESC-017`. Tier 1 (Scenarios 1, 2, 5, 6, 7, 8) has no such dependency.

Full reasoning, every alternative considered, and every consequence:
[ADR-021](ADR.md).

### The Librarian — Vault Filing Expert generalized to a Pipeline-Job caller + cross-cutting-update detection (`REQ-SB-63`, extends [ADR-021](ADR.md)/[ADR-004](ADR.md)/[ADR-042](ADR.md), no new ADR)

`REQ-SB-63`'s own analyst pass argued extending `vault_filing_expert.py` with a
new caller and a new decision outcome is implementation-latitude composition
of an already-`Accepted` `ADR-021`, not a new architectural boundary —
independently verified, not taken on faith, by direct inspection during this
pass:

- **The "new caller" half needs no new mechanism at all.**
  `determine_placement_and_file` is already, TODAY, a plain business-layer
  function called directly (never through `agents_router.py`'s chat/
  working-mode funnel) from **three** structurally different real call
  sites: `agents_router.py`'s chat-attachment handler, `agent_orchestration/
  knowledge_bootstrap.py`'s delegated research chain (`ADR-023`), and
  `knowledge_gap_tracking.py`'s human-answer/research-closing paths
  (`ADR-032`) — confirmed by direct reading of all three. A fourth caller
  (a plain function Job inside `app/business/pipelines/
  email_capture_pipeline.py`'s graph, `ADR-043`) composes it exactly the
  same way `knowledge_gap_tracking.resolve_gap_with_human_answer` already
  does — "Composes the already-Done Vault Filing Expert unchanged," that
  module's own docstring, verbatim, applies unchanged to this new caller.
  No new call topology, no new registry entry, no Hub-routing involvement.
- **The "new decision outcome" half is the exact case `ADR-021`'s own
  Consequences already pre-authorized:** "A future second Tier-2-shaped
  action (any other 'always pauses regardless of mode' decision) reuses the
  same `payload` field and `_APPROVAL_HANDLERS` dispatch-table pattern
  rather than inventing a third approval mechanism." The operator-confirmed
  Option B (Pending Approval, `REQ-SB-63-US-01`'s own `## Notes`) is exactly
  this — no new call contract, no new persistence store, no new tool or
  framework.

**Concrete design for this pass (architect proposal — see this story's own
gate reasoning: flagged, trigger-1, not trigger-3, since no ADR was
created):**

1. **`determine_placement_and_file` gains one additive, keyword-only
   parameter: `already_filed_path: str | None = None`.** All three existing
   callers omit it (behavior byte-for-byte unchanged — mirrors this
   codebase's own established additive-parameter precedent,
   `skill_registry.invoke_skill`'s `args` parameter, `ADR-022`). When a
   pipeline Job caller supplies it (the content it's asking the Librarian
   about is ALREADY filed at a deterministic path the Pipeline's own Job
   controls — a Thread's path, never the Librarian's to decide), the
   function skips the Tier-1/Tier-2 write branch entirely (writing a SECOND,
   redundant note for content that already has a real, deterministic home
   would be wrong) and instead runs `_link_referenced_entity(already_filed_
   path, decision)` against the already-filed note — Scenario 2's own text
   ("the written note is mechanically linked... exactly as already proven
   for the chat-uploaded-attachment caller") is satisfied against the
   ALREADY-filed note, not a new one. The SAME single grounded completion
   (`known_kinds`/`known_customers`/`known_partners`, one `model.invoke`
   call) still runs — Scenario 1's "receives a real placement decision
   grounded in the live vault structure... the SAME Tier 1 vs Tier 2
   boundary... governs this decision" is satisfied by construction: the
   boundary is still evaluated (a Thread's own `kind` is always already
   known, so it always resolves Tier 1 for the primary axis), just without
   redundantly re-writing content the caller already placed.
2. **The model's own returned JSON decision gains one additive, optional
   field, evaluated in the SAME completion, never a second Provider
   round-trip:** `"cross_cutting_implication": {"customer": str | null,
   "partner": str | null, "reason": str} | null`. Independent of the
   Tier 1/Tier 2 axis (Scenario 4) — re-checked in Python, never trusted
   from the model's own naming alone (mirrors `ADR-021` point 2's own
   Tier-boundary discipline, applied a second time): the named
   customer/partner must both (a) already appear in the SAME pre-fetched
   `known_customers`/`known_partners` lists (a genuinely NEW entity is not
   "elsewhere" — normal Tier 1/2 new-entity handling already covers that
   case) and (b) differ from whatever `referenced_customer`/
   `referenced_partner` the SAME decision already names for the content's
   own primary placement (the same entity is not "elsewhere", it's already
   mechanically hub-linked by step 1's own `_link_referenced_entity`).
   Failing either check silently discards the field (Scenario 4's own
   regression guard) rather than raising or fabricating a proposal.
3. **A new, independent Pending Approval, `action_id=
   "propose_cross_cutting_update"`,** created via a new sibling function,
   `_create_cross_cutting_proposal` (mirrors `_create_tier_2_proposal`'s own
   shape exactly), payload carrying `already_filed_path` (or the just-
   written Tier-1 path), the named customer/partner, and the model's own
   `reason` string. Independent of whatever Tier 1/Tier 2 outcome the
   primary axis produced (Scenario 4) — a Tier-1 write and a cross-cutting
   proposal can both happen for the same call.
4. **A new `finalize_cross_cutting_update(payload)`**, registered in
   `pending_approvals_router.py`'s existing `_APPROVAL_HANDLERS` table
   alongside `propose_new_top_level_area` (no new dispatch mechanism).
   Performs the deferred write as an **additive `customer/<slug>` or
   `partner/<slug>` tag on the already-filed note** — reusing `REQ-SB-55-
   US-01-T01`'s own new unconditional frontmatter-key setter (read the
   note's current `tags`, union in the new tag, write back), the SAME
   already-established "tags for multidimensional/cross-cutting
   attributes" idiom `ADR-004` already governs, never a new evidence file
   and never `captures.md` (that file is operator-written only, per `ADR-
   042`'s own structural invariant — an agent-authored write there would be
   a real `ADR-042` deviation, not attempted).
- **Honest, disclosed forward dependency, not silently assumed satisfied
  (mirrors `ADR-021`'s own Tier-2/`REQ-SB-21` disclosure style above):**
  `REQ-SB-63-US-01`'s own `## Notes` expects this write to "become new
  evidence, letting `REQ-SB-57`'s own already-designed evidence-change
  trigger fire normally afterward." `REQ-SB-57-US-01` is still `Draft` —
  its Synthesizer does not exist, and it has not yet designed HOW it
  discovers evidence for a Customer/Project (a `customer:`/`project:`
  frontmatter scan, confirmed for a note's PRIMARY owner; a secondary,
  cross-referencing tag is a NEW discovery case `REQ-SB-57` has not yet
  committed to reading). The tag write above is real, immediately visible,
  vault-inspectable evidence the moment it lands — satisfying Scenario 3's
  own "never silently dropped, never silently applied with no trace" bar —
  but does **not**, on its own, cause any Glimpse to actually regenerate
  until `REQ-SB-57` is built and extended to scan for it. This is NOT a
  blocking prerequisite for `REQ-SB-63-US-01` itself (unlike `ADR-021`'s
  own Tier-2/`REQ-SB-21` case) — the Pending Approval and the tag write are
  both fully buildable and verifiable today; it is named here so a future
  `REQ-SB-57` build does not silently assume this tag convention already
  feeds synthesis without deliberately reading and honoring it.
- **Pipeline wiring point (`REQ-SB-55`'s own Thread pipeline, the one
  concrete integration this story builds):** a new branch Job,
  `Consult-Librarian`, mirrors `Detect-Recurring-Pattern`'s own additive-
  branch shape (fires on every Thread update, never gates `Route-to-
  Project` or the graph's own terminal step, per `ADR-041`'s "consulting an
  Expert is additive, not a replacement for the Pipeline's own terminal
  step"). A new plain function in `email_classification.py`, called after
  `Thread-Match/Merge` regenerates the Thread's `## Summary`, invokes
  `vault_filing_expert.determine_placement_and_file(content=<the Thread's
  own regenerated Summary>, source_description=f"Thread update: {thread_
  note_path}", requesting_agent_id="email-capture-pipeline",
  already_filed_path=thread_note_path)`. Exact `StateGraph` node wiring
  (parallel to vs. sequential after `Route-to-Project`) is left to the
  decomposer, per `ADR-043`'s own established "Job wiring specifics belong
  to the decomposer" precedent.

**Why no new ADR:** every piece above is a parameter-additive extension of
an already-`Accepted` module (`ADR-021`) reusing an already-`Accepted`
approval-dispatch pattern (`ADR-021` point 5, explicitly pre-authorized for
exactly this reuse) and an already-`Accepted` tag idiom (`ADR-004`) — no new
tool, framework, external dependency, or structural boundary (module family,
persisted-store shape, or call topology) is introduced. The one genuinely
new judgement call this pass makes — WHAT the deferred cross-reference write
concretely consists of — is recorded as a flagged architect proposal
(trigger-1, material assumption) in `REQ-SB-63-US-01`'s own `## Notes`,
not folded silently into an unflagged implementation detail.

### Real Anthropic Provider integration & web-research skill (`REQ-SB-36-US-01`, see [ADR-022](ADR.md))

`app/business/provider_registry.py`'s `_REAL_CLIENT_PROVIDER_IDS` gains
`"anthropic-claude"`; `_seed_state()` additionally auto-seeds an
`"Anthropic Claude"` Provider entry (mirrors the existing `"Compass"`
self-seed) from two new required `Settings` fields, `anthropic_api_key`/
`anthropic_model` (`.env.example` gains `ANTHROPIC_API_KEY`/
`ANTHROPIC_MODEL`). A new `app/data_access/anthropic_client.py`
(sibling to `compass_client.py`, plain `anthropic` SDK client, **not**
`langchain-anthropic`/`model_factory.py` — this skill is never routed
through `run_agent_conversation`'s LangGraph loop) exposes `web_search(
api_key, model, query) -> {"found": bool, "summary": str, "sources":
list[str]}`, calling Anthropic's own server-side web-search tool (the
operator-confirmed mechanism). `app/business/skill_tools.py` gains
`web_research(query: str, agent_id: str) -> dict` (`@mcp_server.tool()`,
same catalog shape `REQ-SB-27-US-01` established) — resolves the
**invoking agent's own linked Provider**
(`provider_registry.get_agent_provider(agent_id)`, corrected mid-build,
2026-08-12, operator-directed — supersedes this section's original
fixed-`"anthropic-claude"`-id design, see `ADR-022`'s own "Correction"
addendum) and `has_real_client`, dispatching to `anthropic_client.
web_search` only when that Provider is `"anthropic-claude"` — honestly
unavailable (Scenario 4) for any other linked Provider (Compass has no
real hosted web-search, confirmed live) or before the real client exists,
honestly empty (Scenario 3) when the search finds nothing relevant, never
fabricated. `skill_registry.invoke_skill` additively injects `agent_id`
into the handler call whenever the resolved handler's own signature
declares it, so `skills_router.py`'s own request-body contract and
`diagram-understanding`'s zero-arg call are both unaffected.

`skill_registry.invoke_skill(agent_id, skill_id, args: dict | None =
None)` gains an additive `args` parameter (existing zero-arg callers
unaffected) and `skills_router.py`'s invoke endpoint gains an optional
JSON body — the mechanism Scenario 1's "invokes the skill with a research
subject/query" needs. The web-research skill is invoked exclusively
through this existing REST/`invoke_skill` plumbing (directly, by
`ADR-023`'s orchestration, or via the router) — not bound into the
conversational tool loop this pass (general chat-triggered web search is
out of scope, `REQ-SB-36-US-01`'s own Non-Goals).

**A live-discovered, load-bearing gap closed by this pass:** `app/business/
agent_orchestration/mcp_client.py::load_vault_query_tools()` was found,
by direct reading, to return **every** tool on the shared MCP server with
no filtering — meaning any agent's ordinary chat turn could already reach
`skill_tools.py`'s catalog (harmlessly, while it held only the
`diagram_understanding` stub) regardless of `skill_registry.
has_skill_access`. This would have silently falsified `REQ-SB-36-US-01`
Scenario 2 the moment `web_research` became real. Fixed now: `mcp_client.py`
gains `load_agent_tools(agent_id: str) -> list`, filtering the full server
tool list so a skill-catalog tool is only included when
`skill_registry.has_skill_access(agent_id, skill_id)` is `True` (the four
core vault-query tools stay always-available, never gated);
`graph.py::run_agent_conversation` calls this in place of the old
`load_vault_query_tools()` (removed, no other caller existed). Both
`web_research` and `diagram_understanding` are correctly gated in the
conversational path as a result, reusing `has_skill_access` exactly as
`skill_registry.py`'s own docstring already anticipated.

Full reasoning, every alternative considered, and every consequence:
[ADR-022](ADR.md).

### Delegated knowledge-bootstrap orchestration (`REQ-SB-36-US-02`, see [ADR-023](ADR.md))

A new `app/business/agent_orchestration/knowledge_bootstrap.py` (sibling
to `graph.py`), exposing `async def bootstrap_agent_knowledge(agent_id,
subject) -> dict` — the delegation chain's one public entry point,
composing already-real (or already-designed) pieces deterministically
rather than a second layer of recursive, model-driven agent-to-agent
conversation:

1. Hop 1 — `graph.route_cross_section_request(agent_id, need_description=
   f"real web research about {subject}")` (`ADR-017`) finds a Research
   Expert candidate, or honestly reports no match (Scenario 4).
2. A working-mode check (`working_mode_registry.get_agent_working_mode(...)
   == "autonomous"`, `REQ-SB-21`) gates unattended completion.
3. Research — `skill_registry.invoke_skill(research_expert_agent_id,
   "web-research", {"query": subject})` (`ADR-022`) gathers real content,
   or honestly reports no results (Scenario 5).
4. Hop 2 — `graph.route_cross_section_request(research_expert_agent_id,
   need_description="file this content into the vault")` finds a Vault
   Filing Expert candidate.
5. Filing — `vault_filing_expert.determine_placement_and_file(...)`
   (`ADR-021`) writes immediately (Tier 1) or creates a pending-approval
   record and the chain honestly reports `"status": "pending_approval"`
   (Tier 2, Scenario 2).

**Hub routing is used to identify *who*; the specific capability invoked
at each hop is composed directly by this module** (`invoke_skill(...,
"web-research", ...)`, `determine_placement_and_file(...)`) — not a
generic role-name-keyed dynamic dispatch (deliberately not built; see
[ADR-023](ADR.md)'s Alternatives Considered). Triggered through the
existing action-trigger funnel: a new pilot Expert agent (e.g.
`"compass-expert"`, a plain code-level `agent_registry.AGENTS` addition,
`ADR-011` point 2) declares one new action, `"build_knowledge"`, dispatched
through the existing `_ACTION_HANDLERS`/`_invoke_action` mechanism
(`ADR-011`) — reachable by chat trigger phrase or a direct Available-
Actions button, identically to every existing action. Any future pilot
Expert agent reuses the identical one-line registry addition (Scenario 6).
The whole chain's outcome is recorded as one `run_event` history entry on
the originating agent, via the existing `vault_writer.
append_agent_history_entry`.

**Two real, currently unmet blocking prerequisites, inherited from
`ADR-021`'s own finding, not new to this pass:** the working-mode check
(step 2) needs `working_mode_registry.py`, and Tier 2's own resolution
(step 5) needs `pending_approval_registry.py`/`pending_approvals_router.py`
— neither exists in code yet (`REQ-SB-21-US-01` is `status: Draft`,
unbuilt). See `ESCALATIONS.md` → `ESC-017`.

Full reasoning, every alternative considered, and every consequence:
[ADR-023](ADR.md).

### Agent Knowledge-Gap Tracking & Expert Readiness (`REQ-SB-40-US-01`, see [ADR-032](ADR.md))

Records every honest "I don't know" an Expert agent gives
(`REQ-SB-33-US-01`'s guardrail) as a trackable, closeable knowledge gap,
via a **structured, intercepted-tool-call signal** — not a text
pattern-match — reusing `ADR-017`'s already-real `request_cross_section_
help` precedent one concept over. `/design` was explicitly skipped for
this batch (operator-directed); the display-surface placement decision
below is this pass's own architectural call, not a prototype port.

- **Detection (`graph.py`/`state.py`).** A new bound tool,
  `record_knowledge_gap(topic: str)`, sits alongside
  `request_cross_section_help` — bound to the model, but its own body is
  never actually invoked. `history_entries_to_messages`'s existing single
  `SystemMessage` (`state.py`) gains one more appended instruction
  (mirrors `REQ-SB-33-US-01`'s own append-not-replace precedent):
  producing an honest decline means calling this tool first, then
  replying honestly as normal text. `_route_after_model` gains one more
  branch, checked alongside the existing hub-routing interception: a
  `record_knowledge_gap` call routes to a new node,
  `_record_knowledge_gap` (mirrors `_route_hub_request`'s exact shape) —
  it reads the turn's real originating `HumanMessage` deterministically
  from `current_state["messages"]` (never trusting the model's own
  `topic` argument for the durable question text), calls
  `knowledge_gap_tracking.record_gap(agent_id, question, topic)`, appends
  a confirming `ToolMessage`, and edges back to `call_model` so the
  model's own real final reply text is produced afterward — identical
  control flow to `route_hub_request -> call_model`.
  `AgentConversationState` gains one additive optional field,
  `gap_recorded: dict | None` (mirrors `hub_routing_result`'s own
  addition, `ADR-017`).
- **Storage — new `app/business/knowledge_gap_tracking.py`, a tenth
  `.second-brain/` state file (`agent_knowledge_gaps.json`), deliberately
  NOT folded into `agent_activity.py`** (confirmed by direct read that
  `_ACTIVITY_KINDS = {"run_event", "run_error"}` stays background-run-only
  per that `Done` story's own Constraints). Mirrors `skill_registry.py`'s
  exact "one business module + one dedicated JSON file, pure I/O in
  `vault_writer`" shape: `list_agent_gaps(agent_id, status=None)`,
  `record_gap(agent_id, question, topic) -> dict`, `close_gap(gap_id,
  resolution) -> bool`, `count_open_gaps(agent_id) -> int` (the
  readiness signal — a simple current count, no rate/window/threshold,
  per the story's own Constraints). New `vault_writer.py` primitives
  `load_knowledge_gaps_state()`/`save_knowledge_gaps_state()`, mirroring
  `load_skills_state()`/`save_skills_state()`.
- **Closing paths compose already-`Done` mechanisms unchanged, never
  reimplemented.** Scenario 3 (human-provided answer) routes through
  `vault_filing_expert.determine_placement_and_file(...)`
  (`REQ-SB-35-US-01`/`ADR-021`) — the gap closes once content is actually
  filed (immediately for Tier 1, at Tier-2 approval-finalization time for
  Tier 2), never before, and needs no additional correctness-verification
  step (mirrors `MEMORY.md`'s standing no-staging-gate constraint).
  Scenario 4/7 (directed research) routes through
  `knowledge_bootstrap.bootstrap_agent_knowledge(agent_id, subject)`
  (`REQ-SB-36-US-02`/`ADR-023`) unchanged — a real written/pending-approval
  outcome closes the gap; an honest `"no_results"` outcome (the same
  honest-empty behavior `REQ-SB-36-US-01` Scenario 3 already established)
  leaves it open, producing Scenario 7's regression guard by composition.
- **Display — a fourth, conditionally-rendered tab on the existing
  `AgentDetailPanel.tsx`, gated to Expert-type agents, not a new
  top-level nav page and not `REQ-SB-41`.** Direct read confirms this
  panel carries exactly 3 tabs today (`TABS = ['chat', 'history',
  'settings']`) — "Available actions" is a subsection inside `settings`,
  not a fourth tab. `TABS` gains `'gaps'` (`'Knowledge gaps'`), omitted
  from the array entirely (not disabled/shown-empty) when
  `agent.type !== 'expert'`. A new `GET /agents/{agent_id}/
  knowledge-gaps` endpoint on `agents_router.py` mirrors the existing
  `/history`/`/skills` per-agent sub-resource convention, returning
  `{"gaps": [...], "open_count": int}`; the tab's gap-closing form posts
  to a new resolve endpoint composing the Scenario-3 path above. Does not
  depend on, and does not modify, `REQ-SB-41` (Agent Overview, still
  unspecced) — narrows, does not close, that story's own eventual
  "where does readiness surface" question, the same relationship
  `ADR-031` already established for Purpose's own data source.

Full reasoning, every alternative considered, and every consequence:
[ADR-032](ADR.md).

### File upload, Compass summarization & Vault Filing Expert handoff (`REQ-SB-28-US-01`, see [ADR-034](ADR.md))

**`/design` was explicitly skipped for this batch (operator-directed)** —
this pass's own attach-affordance and status-indication placement below is
this pass's own architectural call, not a prototype port, mirroring
`REQ-SB-40-US-01`'s identical "`/design` explicitly skipped... this pass's
own architectural call" precedent, above.

- **New temporary, non-vault blob storage, `.second-brain/uploads/`.** A
  new `app/data_access` module (exact name left to `/plan-tasks`, e.g.
  `upload_storage.py`) writes the raw uploaded bytes to a generated-id-
  named file under this directory on attach, and deletes it once its
  Compass summary has been produced and handed off (Scenario 5) or on
  validation rejection (Scenario 7). This is the flat-file `.second-brain/`
  state convention's first extension to raw bytes rather than JSON — see
  [ADR-034](ADR.md)'s Consequences.
- **New API surface — an additive sub-resource route on the existing
  `app/api/agents_router.py`**, e.g. `POST /agents/{agent_id}/chat/
  attachment` (exact path left to `/plan-tasks`/decomposer), accepting
  `multipart/form-data` (`message: str`, `file: UploadFile`). Validates
  type (`.pdf`/`.txt`/`.md` — see below) and the 20 MB size cap before
  writing to `.second-brain/uploads/`; a failing file is rejected with a
  clear message and nothing is stored (Scenario 7). **Does not modify the
  existing `POST /agents/{agent_id}/chat` JSON-only endpoint
  (`REQ-SB-25-US-01`, `Done`)** — that contract, and Scenario 6's "a plain
  message is unaffected," stay byte-for-byte unchanged.
- **New Compass function, `summarize_content(content: str,
  source_description: str) -> dict`, in `app/data_access/
  compass_client.py`** — same payload construction and `CompassError`
  handling shape as `classify_email`/`classify_task`; no generic summarize
  function existed there before this story.
- **PDF text extraction — `pypdf` (new dependency).** `.pdf` uploads are
  extracted to plain text before being handed to `summarize_content`;
  `.txt`/`.md` are read directly. Compass itself never receives a PDF
  binary.
- **The summarization capability is registered as a new Skill,
  `summarize-file`, through the already-`Done` Skills mechanism** ("Skills
  Repository — registration & per-agent access," above; `ADR-015` point 9)
  — one new `skill_tools.py` catalog entry + handler, one new
  `_SKILL_HANDLERS` row in `skill_registry.py`, granted to whichever
  agent(s) accept uploads. Invoked as `skill_registry.invoke_skill(agent_id,
  "summarize-file", {"content": ..., "source_description": ...})`, mirroring
  `knowledge_bootstrap.bootstrap_agent_knowledge`'s own existing
  `invoke_skill(..., "web-research", ...)` → `vault_filing_expert.
  determine_placement_and_file(...)` composition shape (`ADR-023`), one
  concept over. This is this project's first real (non-stub) Skill
  implementation.
- **Handoff to the Vault Filing Expert — zero changes to that module.**
  `vault_filing_expert.determine_placement_and_file(content=<Compass
  summary>, source_description=<original filename + uploading agent>,
  requesting_agent_id=<agent_id>)` (`REQ-SB-35-US-01`, `ADR-021`, `Done`)
  is called exactly as its existing signature already accepts — confirmed
  by direct reading, no interface change needed. A Compass failure
  (Scenario 8) or a Filing Expert failure (Scenario 9) is surfaced
  honestly and does not lose the summary already produced, mirroring this
  project's standing honesty posture (`ADR-011`/`ADR-014`/`REQ-SB-33`).
- **Image (PNG/JPG) support is explicitly deferred, not built, by this
  story.** Direct reading of `skill_tools.py` confirms `diagram-
  understanding` unconditionally returns `{"available": False, ...}` — no
  multimodal-capable Provider exists yet, and `compass_client.py` is
  confirmed text-only. Composing either into an image "summary" would
  either fabricate content or add real code for a capability that does not
  exist today. This pass's real, buildable scope is **text-bearing files
  only — `.pdf`, `.txt`, `.md`.** Full reasoning and the deferred-work note
  for a follow-up story: [ADR-034](ADR.md).
- **Frontend — `AgentDetailPanel.tsx`'s Chat tab gains an attach-file
  control.** An attach control in the message-compose bar (accepted types/
  size enforced client-side, mirroring the backend's own validation, per
  Scenario 7) plus a chat-thread rendering of: the attached filename on
  the sent message (Scenario 1), a summarization-in-progress indicator, and
  a filed-note confirmation (linking to the new note) or an honest failure
  message (Scenarios 8/9) — composed via `agentsApiClient.ts`'s existing
  per-agent chat call pattern, extended with one new multipart call to the
  new attachment endpoint above. Exact visual shape (spinner style, chip
  design, inline vs. banner failure message) is coder-level latitude, per
  the operator's own "skip `/design`, build directly" instruction for this
  batch.

Full reasoning, every alternative considered, and every consequence:
[ADR-034](ADR.md).

### Glimpse-First `vault-qa` Answers — entity resolution + Glimpse/Background context injection, evidence drill-down unchanged (`REQ-SB-58`, extends [ADR-015](ADR.md)/[ADR-026](ADR.md)/[ADR-042](ADR.md), no new ADR)

**Grounded in direct reading, not assumed:** `vault-qa`'s only always-bound
read-capable tools today are the four "core" MCP tools
(`list_known_customers`/`list_known_kinds`/`list_known_partners`/
`list_notes_in_kind_folder` — metadata only, never note body content) plus
`retrieve_notes_in_agent_scope(agent_id)` (`REQ-SB-29-US-01`, `Done`) — the
ONE existing tool that returns real note body content, and the ONLY one
that is scope-gated. With no scope assigned, it honestly returns
`"no_scope"`; with a scope assigned (e.g. `customer/<slug>`), it bulk-reads
**every** note matching that scope — every linked Thread, Meeting, and
manual Capture — into the model's context in one call. This bulk,
scope-wide bulk-read **is** the "full vault search re-synthesizing an
answer from scratch every time" the PRD's own `REQ-SB-58` text names as
the baseline this story routes around for the common case, while keeping it
completely intact and unchanged for the drill-down case (see below). No
`vault_search.search()`/`vault_search.py` (`REQ-SB-02`/`ADR-026`) function
is registered as an MCP tool today — `vault-qa` cannot call it directly;
this story reuses it as a **business-layer composition inside the graph**,
not as a new bound tool.

**Mechanism — new business module, one new graph node, zero new MCP
tools:**

1. **New `app/business/glimpse_first_qa.py`** (sibling to `vault_search.py`/
   `project_customer_synthesizer.py`, `ADR-003` layering; mirrors
   `route_cross_section_request`'s own "directly-callable, independently
   testable public entry point wrapping the exact logic a graph node uses"
   shape, `ADR-017` point 5) — one public function,
   `resolve_glimpse_first_context(question: str) -> dict | None`:
   - **Entity resolution reuses `vault_search.search(question)` verbatim —
     no new matching mechanism** (the story's own Constraint). Takes that
     function's own **rank-1 result only** (not a filtered subset re-ranked
     by this story): if the single highest-scoring note for `question`
     across the WHOLE vault has `kind` (`frontmatter["type"]`, per
     `vault_search._kind_for`) equal to `"customer"` or `"project"`
     (`ADR-042` point 1's own concept-file `type` values, confirmed by
     direct reading of `build_customer_concept_frontmatter`/
     `build_project_concept_frontmatter`), the question resolves to that
     entity; otherwise it does not (Scenario 6 — no match, honest `None`).
     This top-1-only bar is a conservative, zero-new-logic threshold: a
     Customer/Project's own concept-file `title` IS that entity's exact
     name (weighted 3× by `ADR-026`'s field weights), so a question that
     genuinely names a real Customer/Project reliably outranks any Thread/
     Meeting note that merely *mentions* it in a tag (2×) or body (1×) —
     the same "ordinary `/plan-tasks` implementation latitude, not a
     further architectural fork" judgement already used for `REQ-SB-29`'s
     own tag-vs-folder disambiguation (this file, "Agent-to-Tag/Folder
     Vault Scoping" section, above).
   - **Resolves the matched entity's own concept-file path directly from
     the search result's own `vault_indexing.get_index()` entry** (`ADR-024`,
     `Done`) — never recomputed via `customer_directory_paths`/
     `project_directory_paths` from a name/slug round-trip. It is, by
     construction, the exact same on-disk file `project_customer_
     synthesizer.py` (`REQ-SB-57`, `Done`) already owns and keeps current.
   - **Reads BOTH `## Glimpse` and `## Background`** via `vault_writer.
     read_body_section(path, header)` (`ADR-042` point 2, `Done`) —
     deliberately not a durable-vs-current-status classifier. `## Glimpse`
     is structurally incapable of carrying a durable historical fact
     (`_build_project_glimpse`/`_build_customer_glimpse` are pure
     current-state rollups, fully regenerated every pass); `## Background`
     is structurally the ONLY section a durable fact can ever land in
     (`REQ-SB-57`'s own Pending-Approval-gated amendment path is its one
     write mechanism). Reading both and letting the model draw from
     whichever one structurally contains the relevant fact satisfies
     Scenario 5 ("reads Background... rather than Glimpse") **by
     construction**, without this story inventing a new "is this a durable
     question" heuristic — the same reasoning this file's own adjacent
     "Project & Customer Synthesizer" section already used to explicitly
     decline building a `status`-inference classifier one layer over
     ("automatically inferring status is a plausible FUTURE extension, not
     proposed here").
   - Returns `{"entity_type": "customer" | "project", "entity_name": str,
     "glimpse": str, "background": str}` or `None`.
2. **New `graph.py` node, wired `retrieve_memory -> glimpse_first_context ->
   call_model`** (both edges unconditional — mirrors `_retrieve_memory`'s
   own "always runs, a no-op most of the time" shape; `ADR-015` points
   3/9's "grow this one shared graph by adding nodes" pattern, no second
   graph). **Gated to `current_state["agent_id"] == "vault-qa"` only** — the
   first literal agent-identity gate in this graph (every existing
   conditional gate so far is skill-based, `skill_registry.
   has_skill_access`, or Cockpit-context-based, never a hardcoded agent id)
   — deliberately narrow: the story's own Constraint locks this to "an
   extension of the existing `vault-qa` Expert... no new Agent," and an
   ungated version would silently change every OTHER already-`Done` agent's
   chat behavior, an out-of-scope risk this pass avoids proactively rather
   than leaving for the coder to discover at verification time. Reads the
   turn's real question from the last `HumanMessage` in `current_state[
   "messages"]` (mirrors `_record_knowledge_gap`'s own "never trust a
   model-paraphrased arg, read the real originating message" precedent,
   `ADR-032` point 1) and calls `glimpse_first_qa.
   resolve_glimpse_first_context(question)`. On a real match, inserts ONE
   new `SystemMessage` at position 1 (mirrors `_retrieve_memory`'s own
   insertion shape exactly — both may fire the same turn; final order is
   simply `[identity, glimpse-context, memory, ...]`, purely additive, no
   collision) naming the resolved entity, its Glimpse, and its Background,
   with an explicit instruction to prefer this content as the primary
   answer and to fall back to its other bound tools for more detail or a
   citation on request (Scenario 3). On no match — an unresolved question,
   OR any agent other than `vault-qa` — the node returns `{}`, a genuine
   no-op; every existing behavior (Scenario 6, every other agent) stays
   byte-for-byte unchanged. **No new `AgentConversationState` field** —
   mirrors `_retrieve_memory`'s own "no new state field needed" precedent
   exactly (`state.py`).
3. **Evidence drill-down (Scenario 3) needs NO new tool — `vault-qa`'s
   existing bound tools are reused exactly as-is.** Considered and
   REJECTED: a new, always-available "read one note by path" MCP tool —
   this would be a genuine, unflagged deviation from `REQ-SB-29`'s own
   already-`Accepted` scope-enforcement boundary (the only existing tool
   that returns raw note BODY content, `retrieve_notes_in_agent_scope`, is
   deliberately scope-gated; the four "core, never-gated" tools return only
   metadata, never body content — an ungated body-content tool would
   silently create a wider vault-read surface than a scoped agent is
   supposed to have). Instead: `_build_project_glimpse`'s own Glimpse
   bullets already carry a real `[[wikilink]]` stem to each source Thread
   (`REQ-SB-57`, unchanged) — that stem is now present in the injected
   context (point 2, above), giving the model a concrete handle to
   correlate against `retrieve_notes_in_agent_scope`'s own returned notes'
   `"path"` field and pick out "the original email" precisely, using tool
   access it already has. **Depends on `vault-qa` actually having a
   `REQ-SB-29` scope assigned** (e.g. the relevant `customer/<slug>` tag) —
   an operator/test-setup configuration step the already-`Done` `REQ-SB-29`
   Settings UI fully supports; not a gap this story closes, but a real
   precondition the decomposer's own task-level test-data design must
   account for.
4. **`REQ-SB-33`'s grounding/honest-uncertainty instruction (`state.py::
   history_entries_to_messages`'s `default_identity_and_grounding_text`)
   gains one additive clause** naming this new context source explicitly
   (e.g. "...or any Customer/Project Glimpse/Background context provided
   to you below, when present...") — its existing wording names only
   "tool calls," "conversation history," and "memory" as legitimate
   grounded sources; the injected Glimpse/Background content (point 2) is
   genuinely real vault data but is none of those three literally, so
   leaving the sentence unchanged would leave the model's own honesty
   framing silently incomplete for this new source. This is an additive
   widening of what counts as a real, named source — never a weakening of
   the "never state something as fact unless it came from a real source"
   rule itself — mirroring `REQ-SB-66`/`ADR-044`'s own already-`Accepted`
   "additive extension of this exact function, no ADR" precedent (this
   file's own 2026-08-12 Addendum, above). The `record_knowledge_gap`
   honesty-funnel mechanism itself is completely untouched — the story's
   own Constraint ("`REQ-SB-33`'s guardrail... must not be weakened") is
   satisfied, not just avoided.

**Why no new ADR:** every primitive this mechanism composes is already
`Accepted` and unmodified in its own contract — `vault_search.search`
(`ADR-026`), `vault_indexing.get_index` (`ADR-024`), `vault_writer.
read_body_section` (`ADR-042` point 2), the graph's own "grow by adding
nodes" shape (`ADR-015` points 3/9). **No new MCP tool is registered** —
the shared tool set (`ADR-015` point 9) is completely unchanged. No new
tool, framework, external dependency, or structural layering boundary is
introduced; this is a business-logic composition plus one new graph node,
the same class of "same-shape extension of already-`Accepted` structure, no
new ADR" already recorded for `REQ-SB-29`/`REQ-SB-40`/`REQ-SB-57`'s own
architect passes (this file, above).

## Meeting & Inbox Cockpits — multi-agent shared-thread workspace (REQ-SB-43-US-01, REQ-SB-44-US-01, see [ADR-036](ADR.md))

A shared 3-panel workspace pattern (approved `/design` passes,
`html-prototype/meeting-cockpit.html` / `html-prototype/inbox-cockpit.html`)
reached by clicking a meeting (My Day's Calendar) or an email (My Day's
Emails). Full reasoning, alternatives, and consequences: [ADR-036](ADR.md).
This section records the resulting module shape only.

- **New sub-package `app/business/cockpit/`** (mirrors
  `agent_orchestration/`'s "first concern with enough internal structure to
  warrant one" precedent), shared by both stories, parametrized by
  `subject_kind: "meeting" | "email"` and `subject_note_stem: str` — never
  two parallel per-kind modules:
  - `threads.py` — composes `ADR-015`'s existing, **unmodified**
    `agent_orchestration.run_agent_conversation(agent_id, message, history,
    memory)` once per currently-brought-in Expert on every user message,
    building each Expert's own `history` view of the shared thread (the
    user's own turns map to `chat_user`; every OTHER Expert's own prior
    turn maps to a `chat_user`-kind entry prefixed `"[{agent_name} said]:
    "`, framed as relayed context, never as this Expert's own past words).
    Backed by a new sibling `.second-brain/cockpit_threads.json`, keyed
    `"{subject_kind}:{subject_note_stem}"` — this codebase's first
    multi-party (not per-agent) conversation store, distinct from
    `agent_communication_history.json`.
  - `people.py` — resolves a subject note's `attendees`/`recipients`
    frontmatter list (below) into chips: a new **read-only**
    `people_extraction.find_existing_person_note(email) -> dict | None`
    lookup per person (never creates a Person note as a side effect of
    opening a cockpit), rendering a clickable chip when found, the
    approved prototype's `.tag-chip--static` plain fallback otherwise.
  - **`people.py` extended — plain wikilink-string attendee entries also
    resolve to real Person data (`BUGFIX-06-US-01`, fixes `BUG-027`).**
    The `attendees`/`recipients` frontmatter value documented above (and
    in the REQ-SB-54 section, below) as a JSON-encoded `list[dict]` string
    is that shape ONLY for Email `recipients`; direct reading of
    `meeting_classification.py`'s real, current write path confirms
    Meeting `attendees` is actually written as a plain `list[str]` of
    wikilinks (`[f"[[{stem}]]" for stem in person_stems]`) —
    `_coerce_people_list`'s own `list[dict]` docstring claim was never
    implemented for Meeting attendees; the real, shipped behaviour and the
    docstring's claimed contract had diverged (correction recorded here,
    docstring left as-is, not retrofitted). `_coerce_people_list`/
    `resolve_people_chips` now also recognize a per-item wikilink STRING
    (`"[[stem]]"`): the stem is extracted by reusing `vault_writer.py`'s
    existing wikilink-stripping regex (the SAME extraction
    `upsert_attendee_links` already performs on an `**Attendees:**` body
    line), promoted from private `_WIKILINK_PATTERN` to public
    `WIKILINK_PATTERN` per this project's own "promote a private
    `data_access` normalization helper to public the moment a second layer
    needs the identical logic" pattern (`MEMORY.md`; `vault_writer.
    _tag_slug` → public `tag_slug` precedent, `REQ-SB-10-US-01-T01`) —
    `cockpit/people.py`, a business-layer module, is now that second
    layer. The extracted stem is then looked up via `vault_indexing.
    get_index().get(stem)` — the SAME stem-keyed lookup `resolve_people_
    chips` already performs for the subject note itself. A found entry's
    `frontmatter.get("name")`/`frontmatter.get("email")` populate the
    chip; an unresolvable stem falls back to the existing "no note yet"
    `has_note: False` chip shape — no Person note is ever created
    (`ADR-036` point 7's read-only contract, unchanged). No new tool,
    framework, or layering boundary — two already-`Accepted` primitives,
    each already live elsewhere in this codebase, composed at a second
    call site; no new ADR.
  - `research.py` — the explicit save/discard flow: Save is a direct
    `vault_writer.write_note(...)` call (a new, standalone note wikilinked
    to the Meeting/Email note, never appended into it), never routed
    through `skill_registry`/`_invoke_action`. The scoped "this meeting/
    email's own research results" list is read via the subject note's own
    already-generic backlinks (`ADR-024`'s `vault_indexing.get_index()`),
    not a separate persisted list — a saved note's own forward wikilink to
    the subject note is what makes it appear, matching this codebase's
    established forward-only-linking convention.
- **Working-mode gate: untouched, unreferenced.** Confirmed by direct
  investigation (`ADR-036` point 4) that neither a brought-in Expert's own
  chat/tool-calling reply nor the user's own explicit Save/Discard click
  ever reaches `skill_registry.invoke_skill`/`agents_router.py::
  _invoke_action`'s gated dispatch path — the Cockpit is a structurally
  separate invocation surface by construction. `skill_registry.
  invoke_skill`'s `trigger` `Literal["chat", "direct", "hub_routed"]` is
  unchanged; no `"cockpit"` value is added.
- **Frontend: one shared `Cockpit` panel component** (3-column grid: chat
  thread + agents-to-bring-in/research list + subject info/people chips),
  accepting an optional attachments slot and an optional draft-reply
  affordance — mirrors `BUGFIX-02-US-01`'s "one component, optional props,
  two call sites" precedent. `MeetingCockpitPage.tsx`/`InboxCockpitPage.tsx`
  are thin route-level wrappers supplying `subject_kind`/`subject_note_stem`
  and (Inbox only) the attachments/draft-reply props — not two forked
  layouts. `my-day-calendar.html`'s/`my-day-emails.html`'s own item rows
  become clickable, opening the respective Cockpit for that item.
- **Inbox-only: attachment review reuses `REQ-SB-28`'s own mechanism
  directly** (`ADR-036` point 6) — the Cockpit calls the same
  `summarize-file` Skill / chat-attachment endpoint `REQ-SB-28-US-01`
  builds (`ADR-034`), never a second read-only preview. **Real, currently-
  unmet cross-story dependency:** `REQ-SB-28-US-01` is `status: Ready`,
  `gate: flagged`, not `Done` — the decomposer must give
  `REQ-SB-44-US-01`'s attachment-review task(s) a `depends_on` edge onto
  `REQ-SB-28-US-01-T03`/`T04`, mirroring `REQ-SB-39-US-02`'s own precedent
  for a `Ready`-not-`Done` cross-story dependency; the rest of
  `REQ-SB-44-US-01` is not blocked by it.
- **Inbox-only: a drafted reply needs no new backend concept.** Per the
  operator's own resolution (ephemeral, no persistence), it is an ordinary
  Expert chat reply the frontend renders with a distinct "draft" affordance
  (e.g. Copy) — `threads.py` above needs no draft-specific field, endpoint,
  or send capability (explicitly out of scope this pass).
- **New Email-note frontmatter field, `recipients: list[{"name","email"}]`**
  (`ADR-036` point 7) — see "Data Model", below, for the full field/capture
  addition.

## Background Agents — explicit opt-in exclusion from Hub-routing and Cockpit addressing (REQ-SB-51-US-01, applies [ADR-014](ADR.md)/[ADR-018](ADR.md), no new ADR)

A fourth new mutable, persisted, user-editable per-agent property —
`is_background_agent: bool`, default `False` — composed *alongside*
`agent_registry.py` exactly the way Section/Provider (`ADR-014`) and
Working Mode (`ADR-018`) already are: a small dedicated registry module, a
sibling `.second-brain/` JSON store, a merged `GET /agents` field, a
`PATCH /agents/{agent_id}` extension, and a real edit control on the Agent
Settings tab — never the read-only-after-creation `settings` kv-list
(`Purpose`/`Domain`-style fields have no edit control anywhere; this flag
must be live and user-toggleable, `AgentDetailPanel.tsx`'s Settings tab).
No new ADR — see "Why no new ADR," below.

- **New sibling `.second-brain/agent_background_flags.json`** —
  `{"assignments": {<agent_id>: bool}}`, extending the established
  flat-JSON-file convention one further concern (alongside
  `agent_sections.json`/`agent_providers.json`/`agent_working_modes.json`).
  `app/data_access/vault_writer.py` gains the paired
  `load_background_flags_state()`/`save_background_flags_state()`
  primitives — pure I/O, no default computed here, mirroring
  `load_working_modes_state()`/`save_working_modes_state()`'s exact shape.
- **New business module, `app/business/background_agent_registry.py`**
  — mirrors `working_mode_registry.py`'s exact shape: a fixed-value
  concern (here, boolean, not a 3-value enum), no separate user-created
  catalog, so seeding folds directly into one `_load_state()` (no separate
  `_seed_state()`). Self-healing default differs from every prior registry
  in exactly one respect: instead of one uniform default for every agent,
  it uses a small literal exception set,
  `_DEFAULT_BACKGROUND_AGENT_IDS = {"email-capture", "meeting-capture",
  "todo-capture"}` (the 3 real capture-pipeline Workers, `agent_registry.py`'s
  `_SEED_AGENTS`, Scenario 2) — any known agent
  (`agent_registry.list_agents()`) absent from `assignments` self-heals to
  `True` if its id is in that set, `False` otherwise, and persists
  immediately. Exposes `get_is_background_agent(agent_id) -> bool` (never
  raises/`None` — an unknown `agent_id` also resolves to `False`, matching
  `get_agent_working_mode`'s no-raise style) and
  `set_is_background_agent(agent_id, value: bool) -> bool`.
- **Composition at the router, not inside `agent_registry.py`** (`ADR-014`'s
  established precedent, unchanged a third time over): `app/api/
  agents_router.py`'s `GET /agents` and `GET /agents/{agent_id}` merge in
  `background_agent_registry.get_is_background_agent(agent_id)` as
  `"is_background_agent"`, the same way `"working_mode"` is merged in
  today. `AgentAssignmentUpdateBody` gains `is_background_agent: bool |
  None = None`; `PATCH /agents/{agent_id}` calls
  `background_agent_registry.set_is_background_agent(...)` when supplied,
  alongside its existing `section_id`/`provider_id`/`working_mode`/`scope`
  handling — one endpoint, one more optional field, not a new route.
- **Frontend types & edit control:** `agentsApiClient.ts`'s `AgentSummary`
  and `AgentDetail` gain `is_background_agent: boolean`;
  `updateAgentAssignment`'s body type gains the matching optional field.
  `AgentDetailPanel.tsx`'s Settings tab gains one new `.kv-row`,
  "Background Agent," with a checkbox control and a
  `handleBackgroundAgentChange` handler mirroring
  `handleWorkingModeChange`'s exact `updateAgentAssignment(agentId, {
  is_background_agent: checked }) → setAgent(updated)` shape (Scenario 1,
  9 — reads live, no cache).
- **Shared exclusion-filter helper, backend: one call site, no
  duplication.** The single real Hub-routing candidate-selection function,
  `app/business/agent_keywords.py::list_candidate_agents_for_keyword_match`,
  gains one skip inside its existing per-agent loop —
  `if background_agent_registry.get_is_background_agent(agent_id): continue`
  — evaluated alongside its existing self-id/same-Section skips, before the
  keyword-substring check (Scenario 3/4). `app/business/agent_orchestration/
  graph.py`'s `_route_hub_request` → `route_cross_section_request` calls
  this function exclusively and never re-implements candidate filtering
  itself, so this is the only backend Hub-candidate site — confirmed by
  direct inspection, not assumed.
- **Cockpit bring-in is NOT enforced inside
  `app/business/cockpit/threads.py`.** Confirmed by direct inspection:
  `threads.py` has no agent-listing code of its own — `bring_in_agent(
  subject_kind, subject_note_stem, agent_id)` only ever accepts an
  already-chosen `agent_id`, idempotently appending it; it does no
  candidate filtering. The Cockpit's own "Available Agents" list
  (Scenario 5/6) is sourced entirely from the frontend's
  `fetchAgentList()` (`GET /agents`) — the same source `AgentsMapCanvas`
  and the (not-yet-built) `REQ-SB-49-US-01` `@mention` list read, per this
  story's own Constraint. The exclusion is therefore enforced once,
  frontend-side, at that one shared source, never duplicated
  backend-side. (Backend-side defense-in-depth on `bring_in_agent` itself
  is left as ordinary coder/decomposer latitude, not mandated by this
  story's ACs, which are scoped to the visible list only.)
- **Shared exclusion-filter helper, frontend: one predicate, two real
  call sites.** A new small predicate, `isBackgroundAgent(agent:
  AgentSummary): boolean`, exported from `agentsApiClient.ts` alongside
  the `AgentSummary` type it reads — the one shared implementation both
  real consumers use, never two independent inline checks:
  - `Cockpit.tsx` filters `availableAgents` through it before rendering
    the "Available Agents" `.item-list` rows (Scenario 5/6).
  - `layoutAgents.ts`'s `layoutAgents(agents, sectionList)` partitions its
    input `agents` at the top: `backgroundAgents = agents.filter(
    isBackgroundAgent)` (returned as a new `backgroundAgents: MockAgent[]`
    field on `AgentMapLayout`, never fed into `agentsBySection` — so it is
    structurally excluded from ring placement and `VISIBLE_SLOT_CAP`
    density clustering, `REQ-SB-38-US-01`, Scenario 7) and
    `addressableAgents = agents.filter((a) => !isBackgroundAgent(a))` (the
    only set that continues into the existing Section/ring logic,
    unchanged).
  - `AgentsMapCanvas.tsx` (or a sibling in `AgentsMapPage.tsx` — exact
    mount point is coder latitude) gains a new small "Background Agents"
    rail/list component consuming `AgentMapLayout.backgroundAgents`,
    reusing the `.card`/`.item-list` vocabulary `Cockpit.tsx`'s own
    "Available Agents" card and `agents-map.html`'s demo-state legend card
    already establish — one row per background agent (name + type);
    clicking a row calls the same `onSelectAgent(agentId)` callback
    `AgentNode` clicks already use, opening the identical
    `AgentDetailPanel` (Scenario 7). No fresh `/design` pass, per the
    story's own Notes.
- **Why no new ADR.** This is an ordinary CRUD-pattern extension of
  `ADR-014`'s/`ADR-018`'s already-`Accepted` "new persisted concern
  composed alongside a hardcoded registry, self-healing default,
  `PATCH`-endpoint-plus-edit-control" shape, one boolean concept over
  (background-agent addressability, not Section/Provider/Working-mode) —
  directly mirroring the already-settled "Skills Repository ... applies
  `ADR-014`, no new ADR" precedent for `skill_registry.py` (itself a more
  novel extension — a grant/revoke access list — than this story's plain
  boolean). The two decisions this story adds beyond that already-settled
  shape — (a) a per-id exception set for the 3 seed Workers' backfilled
  default, and (b) exactly which two consumption sites read the flag for
  exclusion — are ordinary `/plan-tasks` implementation latitude, not
  further architectural forks. No `Accepted` ADR, PRD text, or `MEMORY.md`
  constraint is contradicted; no new tool, framework, or structural
  boundary is introduced.

## Cockpit Inline `@agent_id` Mention — chat-input parsing over the existing bring-in call (REQ-SB-49-US-01, applies [ADR-036](ADR.md), no new ADR)

Purely frontend, additive parsing added to `Cockpit.tsx`'s existing
`chat-input-row` — no new endpoint, no new persisted concern, no second
bring-in code path. Composes `ADR-036`'s already-Accepted Cockpit
mechanism (`threads.bring_in_agent` / `POST /cockpit/{subject_kind}/
{stem}/bring-in`) unmodified. No new ADR — see "Why no new ADR," below.

- **Single candidate source — never a duplicate list.** Both parsing modes
  (send-time resolution and live-typing suggestion) read from the exact
  same in-memory list `Cockpit.tsx`'s own "Available Agents" panel already
  renders from (`fetchAgentList()` → `AgentSummary[]`) — never a second,
  independently-fetched or independently-filtered copy. Concretely, today
  that is the `availableAgents` state variable itself (line 20); once
  `REQ-SB-51-US-01`'s `T04` lands and introduces a filtered
  `bringInCandidates` derived list (`availableAgents` minus
  `isBackgroundAgent`), this story's mention-matching source must be
  repointed at that SAME filtered variable — see "Composition with
  `REQ-SB-51-US-01`," below.
- **Send-time resolution (Scenarios 1, 2, 3, 4).** On Send/Enter, extract
  every `@token` from the full message text via `/@(\S+)/g`. For each
  token, strip the leading `@` and resolve against the candidate list by
  exact, case-insensitive match on either `agent.id` or `agent.name` with
  internal whitespace stripped (`token.toLowerCase() === agent.id
  .toLowerCase() || token.toLowerCase() === agent.name.replace(/\s+/g,
  '').toLowerCase()`) — no fuzzy/partial/ranked matching, per the story's
  own pre-resolved Context. Every token that resolves to a real,
  not-yet-brought-in agent triggers the existing `bringInAgent(subjectKind,
  subjectNoteStem, agent.id)` call — awaited before `sendCockpitMessage`
  fires, mirroring the "+ Bring in" button's own "bring in, then the
  thread includes this agent for this and every subsequent message"
  sequencing. An already-brought-in agent's repeated mention triggers no
  additional call (`bringInAgent`'s own existing idempotency, unmodified,
  covers Scenario 2 — no new dedupe logic needed client-side). A token
  that resolves to no real agent is left exactly as typed, plain text,
  and triggers no call (Scenario 3).
- **Live suggestion (Scenario 5).** While typing, detect an in-progress
  `@`-token immediately before the cursor (`/@(\S*)$/` against the text up
  to the cursor position) and, once at least one character follows the
  `@`, filter the same candidate list by prefix/substring match on `id` or
  `name` (case-insensitive) to populate a small dropdown — a looser filter
  than send-time resolution's exact-match requirement, intentionally: a
  suggestion affordance that only ever appeared for a complete exact match
  would be useless while typing. This dropdown is visual-only; selecting a
  suggestion (or continuing to type an exact token) does not itself call
  `bringInAgent` — only Send/Enter's resolution pass does, keeping exactly
  one call site. Dropdown visual treatment (position, styling) is coder
  latitude against the existing `.card`/`.item-list` vocabulary, per the
  story's own Notes — not decided here.
- **Real, load-bearing interaction with the current `chat-input-row`
  disabled state.** `Cockpit.tsx`'s Send button and text input are
  currently gated `disabled={!hasExperts}` — disabled until at least one
  agent is already brought in. Scenario 1 requires sending a message that
  itself brings in the first agent via `@mention`, with zero agents
  brought in beforehand — the existing hard gate must be relaxed (e.g. to
  also allow Send when the current message text contains at least one
  `@token`) or the mention-resolution pass must run ahead of that check.
  Recorded here as a real, confirmed-by-direct-inspection conflict for the
  decomposer/coder to resolve, not a new architectural decision — the
  exact mechanism (relaxed condition vs. reordered check) is ordinary task
  implementation latitude, bounded by Scenario 1 already requiring SOME
  resolution.
- **Composition with `REQ-SB-51-US-01` (Background Agents, `Ready`, not
  yet `Done`) — a soft, same-source dependency, not a hard `depends_on`.**
  `REQ-SB-51-US-01`'s own Context already states this story "inherits the
  exclusion automatically once built" because both read the same
  `fetchAgentList()`-sourced list. This composes correctly in either build
  order with one small follow-on edit, never a redesign:
  - If `REQ-SB-51-US-01` lands first, this story's own tasks wire mention-
    matching directly against the already-filtered `bringInCandidates`
    list `T04` introduces — a Background Agent is excluded from
    `@mention` matching for free, no separate check.
  - If this story lands first, its tasks wire mention-matching against
    today's unfiltered `availableAgents` (the only list that exists yet);
    when `REQ-SB-51-US-01`'s `T04` later lands and introduces the filtered
    `bringInCandidates` variable inside this same `Cockpit.tsx`, that
    task's own coder must additionally repoint this story's
    mention-matching source at it — a small, same-file, mechanical
    follow-on, not a new design (recorded here so it is not missed,
    since `T04`'s own current scope, written before this story's
    architecture pass, does not yet mention it).
  - Not wired as a hard cross-story `depends_on` edge — mirrors
    `REQ-SB-51-US-01`'s own explicit "not blocked by, either direction"
    position for this pair. The decomposer may still choose to leave a
    task-level note pointing at whichever of the two stories lands second.
- **Why no new ADR.** This is client-side parsing and UI logic layered
  over a single, already-`Accepted`, unmodified backend call
  (`ADR-036`'s `bring_in_agent`) — no new tool, framework, endpoint,
  persisted store, or structural boundary is introduced. It is a smaller
  extension than the already-settled "Skills grouped by Tool ... applies
  `ADR-015`, no new ADR" and "Background Agents ... applies `ADR-014`/
  `ADR-018`, no new ADR" precedents (both of which touched a real backend
  field/endpoint; this story touches neither). No `Accepted` ADR, PRD
  text, or `MEMORY.md` constraint is contradicted.

## Cockpit Person-Directed Instruction (`@PersonName`) — gate-preserving proposed Person-note edit (`REQ-SB-49-US-02`, see [ADR-038](ADR.md))

A deliberate, narrow carve-out from `ADR-036`'s own "Cockpit actions bypass
`invoke_skill`'s gate by construction" precedent — the Cockpit's first
real, autonomous, LLM-initiated vault-mutation candidate gets the SAME
working-mode-gate protection every other mutating action in this codebase
already has, via a new, gate-preserving call path, not the ordinary
chat/tool-calling loop `ADR-036` found never reaches the gate.

- **A third bound-tool interception, mirroring `ADR-017`'s `request_
  cross_section_help` and `ADR-032`'s `record_knowledge_gap` shape
  exactly.** `graph.py` gains `propose_person_note_update(person_name,
  instruction)`, never registered on the shared MCP server, never
  reachable via the generic `execute_tools` node — `_route_after_model`
  intercepts it before the fallthrough, routing to a new
  `_propose_person_note_update` node. Deliberately, this is the ONE
  structural difference from its two siblings: it is bound to a given
  agent's model only when `skill_registry.has_skill_access(agent_id,
  "propose_person_note_update")` is true (mirrors `mcp_client.load_agent_
  tools`'s own existing access-grant filtering, applied to a graph-bound
  tool for the first time), not unconditionally to every agent — because,
  unlike its two siblings, this tool composes with a real, declared,
  per-agent-granted Skill (below), not a generic ungated graph capability.
- **A new, real `mutates: True` Skill, `propose_person_note_update`**,
  added to `skill_tools.SKILLS`/`skill_registry._SKILL_HANDLERS`, granted
  to `people-producer` via one new `_MIGRATION_GRANT_SEED` row — mirrors
  `ADR-029` point 7's exact per-id, per-agent seeding shape.
- **Read-only resolution first, gate only on a real match.** The
  interception node resolves `@PersonName` against a new, name-keyed,
  read-only sibling of `people_extraction.find_existing_person_note`
  directly (no gate involvement — mirrors `_record_knowledge_gap`'s own
  direct business-module call). No match → an honest "not found" reply,
  no Skill call, no proposal, no note created (Scenario 4). A match →
  `skill_registry.invoke_skill(agent_id, "propose_person_note_update",
  args, trigger="cockpit_mention")` — the FULL existing two-axis
  working-mode gate (`ADR-029`) applies exactly as it would for any other
  mutating Skill (Scenario 3), by construction.
- **New trigger literal, `"cockpit_mention"`** — deliberately not a reuse
  of `"chat"`/`"direct"`/`"hub_routed"`/`ADR-037`'s `"scheduled"`: this is
  the first dispatch in this codebase whose Skill `args` are determined by
  an LLM's own interpretation of free text rather than a deterministic
  caller, and `"hub_routed"` would incorrectly refuse it in Manual mode.
  Requires zero new gate branches — `invoke_skill`'s existing two `if`
  checks already compose correctly with any new literal, mirroring
  `ADR-037` point 8's own identical consequence.
- **"Propose" deliberately deviates from this Skill's own standard
  post-gate dispatch behavior for Manual/Autonomous mode only — a real,
  documented precedent-break, not an oversight.** Supervised mode needs no
  extra step: approving the gate's own existing Pending Approval IS the
  human confirmation (Scenario 2 — approve writes immediately, exactly as
  any other mutating Skill's approval already does). Manual/Autonomous
  mode's dispatch, unmodified, has zero human click at all in its own path
  — correct for every other mutating Skill, but exactly the "direct,
  unconfirmed side effect" this story's own unqualified Constraint forbids
  for THIS one. `_dispatch_skill` gains one new opt-in, signature-
  introspected keyword, `already_approved: bool = False` (mirrors the
  existing `agent_id` auto-injection seam — a no-op for every other
  handler), passed `True` only by `pending_approvals_router.py`'s
  Approve branch. The Skill's own handler: `already_approved=True` writes
  directly via `vault_writer`; `already_approved=False` (Manual/Autonomous
  direct dispatch) never writes — it records an explicitly confirmable/
  discardable in-thread proposal instead (new `app/business/cockpit/
  person_note_proposals.py`, mirrors `cockpit/research.py`'s own scoped-
  list-plus-direct-`vault_writer`-on-explicit-Save shape, stored inside the
  owning thread's own `cockpit_threads.json` record, not a new top-level
  file). This deviation lives entirely inside the Skill's own handler body
  — the shared gate's own axis logic (Supervised → pending, Manual/
  Autonomous → dispatch) is untouched, satisfying Scenario 3's own "never
  a special-cased, ungated bypass" wording, which describes the gate, not
  a Skill's own per-handler dispatch behavior.
- **Refines, does not reopen, `ADR-036`'s own finding.** `cockpit/
  research.py::trigger_research` already calls `invoke_skill(...,
  trigger="direct")` directly for the (non-mutating) `web-research` Skill
  — `ADR-036`'s "the Cockpit never reaches the gate" finding was always
  really about the model's OWN bound-tool-calling loop
  (`_execute_tools`, MCP-loaded tools only); this story is the first
  Cockpit-originated call to reach the gate for a MUTATING Skill, the
  first time that finding's own scope is consequential.
- See `ADR-038` for the full reasoning, including every alternative
  considered and rejected (extending `ADR-036`'s bypass to this
  capability; reusing `trigger="direct"`/`"hub_routed"`; an always- or
  never-explicit-confirm design; a wholly new, bespoke gate mechanism).

## Cockpit Chat — Addressed-Reply Dispatch, Send-on-Enter, and Pending-State Live Update (`BUGFIX-04-US-01`, `BUG-022`/`BUG-023`/`BUG-024`, extends `ADR-036`, no new ADR)

Three independent defects in the already-`Accepted` Meeting & Inbox Cockpit
send flow (`ADR-036` point 1, `threads.py::send_user_message` above),
fixed without reopening that mechanism's own shape — each composes an
already-`Accepted` precedent rather than introducing a new one. Full
per-bug root cause: `BUGFIX-04-US-01`'s own `## Context`. No new ADR — see
"Why no new ADR," below.

- **BUG-022 — addressed-reply dispatch reuses `REQ-SB-49-US-01`'s existing
  mention resolution as the dispatch signal, never a second parsing
  implementation.** `threads.py::send_user_message` gains one new optional
  parameter, `addressed_agent_ids: list[str] | None = None`. Its per-agent
  loop changes from unconditionally iterating
  `thread["brought_in_agent_ids"]` to iterating
  `addressed_agent_ids if addressed_agent_ids else
  thread["brought_in_agent_ids"]` — an empty/omitted addressee list falls
  back to today's broadcast-to-every-brought-in-agent behavior unchanged
  (the story's own Constraint: a no-mention message in a single- or
  multi-agent thread must keep working exactly as it does today).
  `POST /cockpit/{subject_kind}/{subject_note_stem}/message`'s body gains
  a matching optional `addressed_agent_ids: list[str]` field;
  `cockpit_router.py::send_message` passes it straight through, no
  validation logic added at the router. **The addressee list is computed
  exactly once, frontend-side** — `Cockpit.tsx`'s existing
  `resolveMentionedAgents(messageInput, bringInCandidates)` (built for
  `REQ-SB-49-US-01`, until now used ONLY to drive `bringInAgent(...)`
  calls) becomes a SECOND consumer of that same computed
  `mentionedAgents` list: after its existing `bringInAgent(...)` calls
  resolve, `handleSendMessage` passes
  `mentionedAgents.map((agent) => agent.id)` as `sendCockpitMessage`'s new
  `addressedAgentIds` argument. This mirrors `REQ-SB-49-US-01`'s own
  "single candidate source — never a duplicate list" precedent one layer
  over: Second Brain now has exactly one `@mention`-parsing
  implementation (JS, client-side), never a second, independently
  maintained Python regex re-deriving the same result.
- **BUG-023 — `Cockpit.tsx`'s `chat-input-row` becomes a real
  `<form onSubmit={...}>`, mirroring `AgentDetailPanel.tsx`'s own already-
  working precedent exactly.** `handleSendMessage` gains a
  `(event: React.FormEvent) => { event.preventDefault(); ... }` signature;
  the Send `<button>` becomes `type="submit"`; the existing `<input
  type="text">` needs no new handler of its own — a form's native
  Enter-submits-on-focused-text-input behavior fires `onSubmit` for free,
  the same mechanism `AgentDetailPanel.tsx`'s `chat-input-row` already
  relies on. The `@mention` suggestion dropdown's own row buttons
  (`Cockpit.tsx`'s `mention-suggestion-list`) stay `type="button"` — a
  real, load-bearing detail: an un-typed `<button>` inside a `<form>`
  defaults to `type="submit"`, so leaving them unspecified would make a
  suggestion click also submit the in-progress (unresolved) message.
- **BUG-024 — pending-state UI mirrors `AgentDetailPanel.tsx`'s existing
  `sending`/typing-dot pattern; no new live-update mechanism.**
  `Cockpit.tsx` gains a `const [sending, setSending] = useState(false)`,
  set `true` before the `bringInAgent(...).then(sendCockpitMessage...)`
  chain begins and `false` in a trailing `.finally(...)`. The chat input
  and Send button gain `disabled={sending}` (composed with their existing
  `disabled={!canSend}` condition); the chat thread gains a
  `sending && <div className="chat-message chat-message--agent
  chat-message--pending">` block reusing the SAME `.chat-typing-dot` CSS
  class `AgentDetailPanel.tsx` already defines and uses — no new CSS.
  **Also folds in one real, related simplification, not just a spinner:**
  `sendCockpitMessage`'s response is already the fully updated
  `CockpitThread` — confirmed live, `threads.py::send_user_message`
  already returns the thread with every dispatched agent's reply
  appended, and `cockpitApiClient.ts::sendCockpitMessage` already types
  its return as `Promise<CockpitThread>` — yet `handleSendMessage`
  discards that response and fires a SEPARATE `reload()`
  (`fetchCockpit(...)` GET) afterward. The fix applies the send response
  directly via `setData(...)`, removing that redundant round trip rather
  than merely adding a loading indicator on top of it. **No SSE,
  websocket, or polling is introduced or needed:** `send_user_message`'s
  own real, synchronous, sequential per-agent dispatch (`ADR-036` point 1,
  untouched in shape by the BUG-022 fix above beyond which agents are in
  the loop) already returns the complete post-turn thread state in its
  one awaited HTTP response — there is no server-side asynchrony left to
  bridge. `REQ-SB-42`'s existing `GET /agent-presence/stream` SSE channel
  (`ADR-035`) is a considered-and-rejected reuse candidate, not an
  oversight: it is a broadcast-only, ephemeral, cross-agent ACTIVITY
  signal (who is currently running), structurally unrelated to relaying
  one specific Cockpit thread's own completed message content back to one
  specific requesting browser tab.
- **Why no new ADR.** All three fixes compose an already-`Accepted`
  mechanism (`ADR-036`'s Cockpit shape, `REQ-SB-49-US-01`'s mention
  resolution) without introducing a new tool, framework, endpoint,
  persisted store, or live-update transport — smaller in weight than the
  already-settled "Cockpit Inline `@agent_id` Mention ... applies
  `ADR-036`, no new ADR" and "Background Agents ... applies `ADR-014`/
  `ADR-018`, no new ADR" precedents directly above/below this section (both
  of which added a real new field or endpoint; BUG-022's one new optional
  parameter/body field is the closest analog and is smaller than either).
  No `Accepted` ADR, PRD text, or `MEMORY.md` constraint is contradicted.

## Chat Rich-Text Rendering — `react-markdown` (`BUGFIX-04-US-01`, first real delivery of `REQ-SB-32`, see [ADR-050](ADR.md))

`BUG-025` found all real chat surfaces render message text as a raw
literal string. Direct code + `package.json` inspection (the triage
analyst's own confirmed root cause, and this architecture pass's own
re-confirmation) established this is genuinely NET-NEW capability, not a
regression — `REQ-SB-32` ("Rich Text Rendering in Agent Chat") was never
actually spec'd or built. Full reasoning, alternatives, and consequences:
[ADR-050](ADR.md). This section records the resulting module shape only.

- **One new shared presentational component,
  `src/frontend/src/components/ChatMessageText.tsx`**
  (`<ChatMessageText text={string} />`), wrapping `react-markdown` with
  ZERO additional remark/rehype plugins — CommonMark's own default
  feature set already covers the operator-resolved markdown subset
  (bold/italic, bulleted/numbered lists, links, inline/block code,
  headings; not full CommonMark/GFM — no tables, strikethrough, task
  lists, footnotes this pass).
- **Exactly two real call sites — confirmed by direct inspection that a
  third, separate "Agents Map chat panel" component does not exist:**
  `Cockpit.tsx`'s chat-thread map (both `chat-message--user` and
  `chat-message--agent` rows — Meeting Cockpit and Inbox Cockpit share
  this one component) and `AgentDetailPanel.tsx`'s chat-thread map (both
  `role === 'user'` and `role === 'agent'` rows — this component IS "the
  Agents Map's own embedded agent chat panel" the story's `## Story`
  section names). Each site's literal `{message.text}` is replaced with
  `<ChatMessageText text={message.text} />` — no `message.speaker`/`role`
  branch on whether to apply it, directly implementing the operator's own
  "All Text Should be Rich Text in Chat" resolution (both user- and
  agent-authored messages render symmetrically).
- **Sanitization posture: default-safe by omission, not a second
  sanitizer dependency.** `react-markdown` never invokes
  `dangerouslySetInnerHTML` and never parses/renders raw HTML embedded in
  message text unless the `rehype-raw` plugin is explicitly added — this
  pass adds no such plugin, so the story's own Constraint ("never raw
  `dangerouslySetInnerHTML` of unsanitized content") is satisfied
  structurally. Link/image URLs render through `react-markdown`'s own
  built-in `defaultUrlTransform`, unmodified — it already strips
  non-`http(s)`/`mailto`/`tel` link schemes (blocking `javascript:`-style
  injection) with no custom `urlTransform` override needed.
- **Package: `react-markdown`** (current stable v9.x — pin-then-verify-at-
  real-install, this project's established `react-router`/`langgraph`
  pattern), the first markdown/rich-text dependency in `src/frontend/
  package.json`.

A generalized, per-`(agent_id, capability_id)` recurring-schedule
mechanism (configure/edit/remove/run-now/run-history via a new Schedule
tab), built together with the shared serialization guarantee that no two
Outlook-COM-touching runs ever execute concurrently, regardless of trigger
source — per the operator's own confirmed decision to build both
requirements as one piece of work. Extends `ADR-005` (the existing
`app/scheduling/` layer and its one hardcoded hourly job) and `ADR-029`
(the Skills working-mode gate). Full reasoning, every alternative
considered, and every consequence: [ADR-037](ADR.md).

- **New sibling `.second-brain/agent_schedules.json`** —
  `{"schedules": {"<agent_id>::<capability_id>": {"agent_id",
  "capability_id", "interval_value": int, "interval_unit": "minutes" |
  "hours", "created_at", "updated_at"}}}`, a composite string key (not a
  uuid-keyed list) — this project's structural guarantee that at most one
  active schedule exists per (agent, capability) pair. `app/data_access/
  vault_writer.py` gains the paired `load_agent_schedules_state()`/
  `save_agent_schedules_state()` primitives, pure I/O, mirroring
  `load_working_modes_state()`/`save_working_modes_state()`'s exact shape.
- **New business module, `app/business/agent_schedule_registry.py`** —
  the single owner of three related concerns, deliberately kept together
  rather than split into three modules:
  1. **Persisted schedule CRUD**, `list_schedules(agent_id=None)`,
     `create_or_update_schedule(agent_id, capability_id, interval_value,
     interval_unit)` (refuses — Scenario 9 — unless `capability_id` is
     both granted, per `skill_registry.list_agent_skills(agent_id)`, and
     `skill_tools.SKILLS[capability_id]["mutates"] is True`),
     `remove_schedule(agent_id, capability_id)`.
  2. **The live `AsyncIOScheduler` reference.** `capture_scheduler.
     lifespan()` calls `set_live_scheduler(scheduler)` once, at startup,
     right after building it — this is what lets `create_or_update_schedule`/
     `remove_schedule` call `.add_job(..., replace_existing=True)`/
     `.remove_job(...)` directly on the live process's own scheduler,
     making Scenario 4/5's "no restart required" true without `app/
     business/` ever importing `app.scheduling` (the object being
     manipulated is a plain third-party `AsyncIOScheduler` instance, not
     `app.scheduling`-owned code — see [ADR-037](ADR.md) point 2 for the
     full reasoning behind this seam).
  3. **The shared dispatch lock** — one module-level `asyncio.Lock()`,
     `get_shared_dispatch_lock()`, and `dispatch_with_shared_lock(agent_id,
     capability_id, trigger: Literal["scheduled", "direct"]) -> dict` — the
     ONE function every real scheduled/on-demand trigger source now passes
     through (mirrors `ADR-005` point 3's own "one concurrency guard spans
     both trigger sources," generalized). Skips (never queues) and records
     an honest `"skipped — another run is already in progress"` run-history
     entry if the lock is already held; otherwise acquires it and calls
     `await asyncio.to_thread(skill_registry.invoke_skill, agent_id,
     capability_id, None, trigger)`. **Explicitly in-process only** — this
     is a plain Python `asyncio.Lock` object, one per running interpreter;
     it does not, and is not intended to, prevent two independent OS
     processes from racing against the same real Outlook/Compass session
     (the literal `SPRINT-030` collision `REQ-SB-45`'s own PRD text cites)
     — that remains a deliberate, disclosed, out-of-scope operational-
     hygiene risk (see [ADR-037](ADR.md)'s Context and Alternatives
     Considered for the full reasoning).
- **`app/scheduling/capture_scheduler.py` — surgically edited, not
  rewritten.** Its own private `_capture_run_lock` is removed;
  `run_capture_if_idle` (the existing hourly blob tick) now acquires
  `agent_schedule_registry.get_shared_dispatch_lock()` instead — the one
  change that makes the blob tick and any newly-configured per-agent
  schedule targeting the same capture agent correctly serialize against
  each other. `build_scheduler()` still registers the existing hardcoded
  `hourly_capture` job unchanged, and additionally reads
  `agent_schedule_registry.list_schedules()` at boot, registering one
  APScheduler job per persisted schedule (`id=f"schedule:{agent_id}:
  {capability_id}"`, same `coalesce=True, misfire_grace_time=None,
  max_instances=1` configuration as the existing job), each job's callback
  calling `agent_schedule_registry.dispatch_with_shared_lock(agent_id,
  capability_id, trigger="scheduled")`. The existing blob tick's own
  bespoke per-capture-type Autonomous/Supervised/Manual gate inside
  `email_classification.py` (`ADR-018`/`ADR-020`) is untouched — the two
  mechanisms coexist, sharing only the dispatch lock, never each other's
  gating logic.
- **`skill_registry.invoke_skill` gains a new `"scheduled"` trigger
  literal** — `Literal["chat", "direct", "hub_routed", "scheduled"]`.
  **Manual mode gains one new branch**, `mode == "manual" and trigger ==
  "scheduled"` → `{"status": "skipped_manual", "reason": "This agent is in
  Manual mode — its scheduled runs stay dormant."}`, with **zero** history
  entry — mirroring the blob tick's own already-established "Manual skips
  silently" precedent, generalized to any scheduled capability. **"Run
  now" reuses the existing `"direct"` literal, unchanged** — no new
  branch needed, since Manual mode already lets an explicit user-initiated
  `"direct"` call through today. Supervised + mutating + `"scheduled"`
  falls into the existing pending-approval branch, unchanged — identical
  decision table, one more `trigger` value over.
- **New API surface, `app/api/agent_schedules_router.py`**,
  `APIRouter(prefix="/agents/{agent_id}/schedules")`: `GET` (list), `POST`
  (create, `400` on Scenario 9's refusal), `PATCH /{capability_id}` (edit),
  `DELETE /{capability_id}` (remove), `POST /{capability_id}/run-now`
  (`await agent_schedule_registry.dispatch_with_shared_lock(agent_id,
  capability_id, trigger="direct")`). Registered in `app/main.py`. **Run
  history needs no new endpoint** — the Schedule tab reuses the existing
  `GET /agents/{agent_id}/history` (`REQ-SB-11`).
- **`meeting-capture`'s/`todo-capture`'s `run_capture_now` stays the
  existing honest "not yet available" stub** — schedulable through the
  new capability picker (any granted `"mutates": True` Skill, Scenario 2),
  but a tick or run-now against it always produces the same honest
  "not available" outcome the direct/chat path already produces today,
  recorded to run history like any other outcome — operator-relayed
  scoping decision (see [ADR-037](ADR.md)'s Context): this pass
  generalizes the scheduling mechanism only, it does not build real
  on-demand handlers for either capability.
- **Frontend — net-new, no approved prototype coverage today.**
  `AgentDetailPanel.tsx` gains a 5th tab, "Schedule" (alongside
  `overview`/`chat`/`history`/`settings`/`gaps`): a capability picker
  scoped to the agent's own granted, mutating capabilities (Scenario 2), an
  interval value+unit control, Save/Edit/Remove, a "Run now" button per
  schedulable capability, and a run-history list reusing the same
  agent-history fetch the History tab already calls. A new
  `agentSchedulesApiClient.ts` (or an extension of the existing
  `agentsApiClient.ts`) carries `fetchSchedules`/`createSchedule`/
  `updateSchedule`/`removeSchedule`/`runScheduleNow`. **Exact layout is
  decomposer/coder latitude, not resolved by this architecture pass** — no
  tab-bar or schedule-configuration control pattern exists anywhere in
  `html-prototype/agents-map.html` today (confirmed by direct inspection,
  per the story's own Notes); a `/design` pass or an explicit operator
  sign-off to skip one remains open, independent of this section's own
  backend-mechanism scope.

## Capture Pipeline Split — Pull/Tag/Link/Store Agent Stages (`REQ-SB-53-US-01`/`US-02`/`US-03`, see [ADR-040](ADR.md)) — SUPERSEDED, see [ADR-041](ADR.md)

**Superseded 2026-08-15 — kept below for historical record, do not build
against this section.** The taxonomy discussion that produced
[ADR-041](ADR.md) (see "Agent / Pipeline / Job / Hub Domain Model", near
the top of this file) established that a Pipeline is a user-extensible
DAG of lightweight Jobs, not a fixed chain of 4 separately-visible, Type-
assigned Agents. `REQ-SB-53` and its 3 stories are parked pending a
re-spec against that model. The section below describes what `ADR-040`
designed, unedited, for continuity only. **`REQ-SB-55` (below, see
[ADR-043](ADR.md)) is the real story that actually supersedes
`REQ-SB-53-US-01`'s own Email-capture scope** — build against "Email
Capture & Threading Pipeline — First Concrete Pipeline", below, not this
section.

Each of the 3 monolithic capture Workers (`email-capture`/`meeting-capture`/
`todo-capture`) is split into 4 separate, individually-visible,
individually-gated agent identities — Puller (`type: "worker"`) → Tagger
(`type: "worker"`) → Linker (`type: "producer"`) → Storer
(`type: "producer"`) — running in-process, in one atomic pipeline pass per
fetched item, on the SAME existing `capture_scheduler.py` trigger (no new
schedule, no persisted queue/staging). Full reasoning, every alternative
considered, and every consequence: [ADR-040](ADR.md).

- **New shared, capture-type-agnostic `app/business/capture_pipeline.py`**
  — mirrors the Cockpit's own `app/business/cockpit/` "one shared module,
  generic over a per-application parameter, not N parallel copies"
  precedent ([ADR-036](ADR.md)). Owns exactly four concerns: the per-stage
  working-mode gate check, the per-item buffered/deferred history commit,
  Supervised-stage Pending-Approval creation and resumption, and the
  top-level tick entry point `run_capture_pipeline(capture_type,
  stage_agent_ids, pull_fn, tag_fn, link_fn, store_fn) -> list[dict]`. It
  never imports `outlook_com`/`compass_client`/`customer_hub_linking`/
  `people_extraction` directly and never contains any capture-type-specific
  business logic.
- **Each capture type's own real Pull/Tag/Link/Store logic stays inside
  that type's own existing file** (`email_classification.py`,
  `meeting_classification.py`, `todo_classification.py`), split from one
  monolithic function into 4 stage functions with the contract `pull_fn()
  -> list[dict]`, `tag_fn`/`link_fn`/`store_fn(items) -> StageResult`
  where `StageResult = {"succeeded": [...], "failed": [(item, exc), ...]}`
  — each type's own real divergences (Compass-vs-majority-vote Tag,
  EntryID-keyed-vs-recompute-and-`exists()` dedup, a narrower
  no-Person-linking Link stage for To-Do) are fully preserved, invisible
  to the shared engine.
- **Working-mode gate — per-stage, per-tick (batch-level), generalizing
  [ADR-018](ADR.md) point 4's existing two-explicit-block, direct
  `working_mode_registry` check (never `skill_registry.invoke_skill`) to 4
  blocks.** Autonomous runs the stage against the whole batch; Manual
  skips silently (no history entry, no downstream stage runs this tick);
  Supervised creates exactly ONE Pending Approval covering the whole batch
  that reached this stage this tick, reusing `trigger="background"`'s
  existing per-agent-per-tick idempotency-dedup guard verbatim (zero new
  dedup code), with `action_id` set to a new synthetic, colon-bearing
  value (`"pipeline:email:store"`) and `payload={"pipeline_resume":
  {capture_type, stage_agent_ids, resume_stage, items}}`.
- **Partial-failure rollback — buffered/deferred per-item history commit,
  never immediate-write-then-mutate** (history stays append-only, per
  [ADR-018](ADR.md) point 7). Each item's per-stage outcomes are held in
  memory until its fate for the tick is known: full success commits one
  real `"run_event"` entry per stage; a failure commits a `"run_error"`
  for the failing stage and a new, additive `"reverted"` history-entry
  kind for every earlier stage that item had already tentatively passed —
  so a human browsing that earlier stage's own Agent Activity never sees a
  stray success for an item that ultimately failed downstream. Store never
  runs for a failed item; it naturally retries whole from Pull next tick
  via each type's own existing dedup mechanism (no explicit retry state).
- **`pending_approvals_router.py`'s Approve endpoint gains one new
  branch** (checked before the 2 pre-existing background/direct branches):
  a `payload` containing `"pipeline_resume"` calls
  `capture_pipeline.resume_pipeline_from_stage(...)` directly, bypassing
  the gate (mirrors [ADR-018](ADR.md) point 6's "the approval is itself the
  authorization" precedent), resuming the walk at the stage after the one
  just approved — a downstream stage may itself be Supervised too,
  producing a cascaded second approval, which is intended, not a bug.
- **`skill_registry.invoke_skill`/`_dispatch_skill` are untouched** — no
  new `trigger` literal, no new branch. These 4 stages are never
  `skill_tools.SKILLS` catalog entries; they are gated by the same direct
  `working_mode_registry` check [ADR-018](ADR.md) point 4 already
  established for an internal pipeline step, never through `invoke_skill`.
- **`_SEED_AGENTS` gains 4 new entries per capture type** (12 total across
  the 3 sibling stories), replacing that type's one retired monolithic
  entry; `background_agent_registry.py`'s `_DEFAULT_BACKGROUND_AGENT_IDS`
  literal exception set is extended to the 12 new ids, inheriting the
  retired agent's own Hub-routing/Cockpit-`@mention` exclusion.
- **Zero new `.second-brain/` state files** — reuses
  `agent_working_modes.json`, `agent_pending_approvals.json`, and
  `agent_communication_history.json` exactly as they exist today; the only
  additive surface is the new `"reverted"` history `kind` and the new
  `pipeline_resume` payload convention on existing Pending Approval
  records.

## Email Capture & Threading Pipeline — First Concrete Pipeline (REQ-SB-55, see [ADR-043](ADR.md))

The first real Pipeline built under [ADR-041](ADR.md)'s directional
Agent/Pipeline/Job/Hub taxonomy — replaces the monolithic
`email_classification.classify_recent_emails` Worker with a genuine
`Fetch`→`Classify`→`Thread-Match/Merge`→`Route-to-Project` chain, plus two
branch Jobs (`Summarize-Attachment`, `Detect-Recurring-Pattern`), populating
the Thread evidence shape [ADR-042](ADR.md) already established. Full
architectural reasoning, every alternative considered, and every
consequence: [ADR-043](ADR.md).

- **Module layout — a new `app/business/pipelines/` subpackage, this
  codebase's first home for a Pipeline's own DAG assembly, kept separate
  from each capture type's own business-logic module.**
  `app/business/pipelines/email_capture_pipeline.py` owns exactly: the
  `langgraph.graph.StateGraph` construction/compile, a typed pipeline
  state, and the public entry point `run_email_capture_pipeline(limit:
  int = 10) -> list[dict]` — what `run_capture_for_agent`/
  `run_capture_and_record_completion` call for the new Agent-tier identity
  (below) that replaces `email-capture`. Never imports `outlook_com`/
  `compass_client` directly — every graph node is a thin callable wrapping
  a PLAIN function living in `email_classification.py` (`Fetch` reuses
  `outlook_com.list_recent_mail` unchanged; `Classify` extends the
  existing `compass_client.classify_email` call with two new outcomes —
  does this belong to an existing Thread or start a new one; does this
  look like a recurring/structured artifact; `Thread-Match/Merge`,
  `Route-to-Project`, `Summarize-Attachment`, and
  `Detect-Recurring-Pattern` are new plain functions, each independently
  callable/testable outside any LangGraph context, taking/returning
  ordinary Python data, never a graph-state dict — this is deliberate, so
  `Thread-Match/Merge`/`Route-to-Project` stay cleanly consultable by a
  future generalized Vault Filing Expert consult call (`REQ-SB-63`, not
  built here) without this story anticipating that integration's shape).
  Future Pipelines (Meeting-capture's own eventual migration, `REQ-SB-56`;
  To-Do) get their own sibling module in this same subpackage, not a
  forced-generic shared engine invented ahead of a second real example.
- **`Fetch` is a pre-graph, per-tick batch step — the compiled
  `StateGraph` (`Classify`→`Thread-Match/Merge`→`Route-to-Project`, plus
  the two branch Jobs) runs once PER FETCHED EMAIL,** mirroring
  `classify_recent_emails`'s existing per-email loop shape. No persisted
  queue/staging between `Fetch` and the rest of the graph, and no
  cross-email graph state, per this story's own Non-Goals. `list_recent_
  mail`'s own already-processed-id dedup stays exactly where it is today,
  in the per-tick loop, outside the graph.
- **Fork/merge shape:** `Classify` is the fork point — routes
  unconditionally to `thread_match_merge`; in parallel, to
  `summarize_attachment` (once per real attachment) when the email has
  any, whose output feeds back INTO `thread_match_merge`'s own input (a
  fan-in — the Attachments section and the regenerated Summary land in
  the same pass); and, independently, to `detect_recurring_pattern` when
  `Classify`'s new recurring-candidate outcome fires — this branch never
  feeds back into `thread_match_merge`, it terminates on its own once it
  creates its own Pending Approval. `thread_match_merge` conditionally
  routes to `route_to_project` **only when this pass created a brand-new
  Thread** (first message in the conversation) — an update to an
  already-existing Thread routes straight to the graph's end for this
  item, the concrete mechanism behind Scenario 4 (no re-routing/
  re-approval on a later message in an already-routed conversation).
  **`thread_match_merge` also, unconditionally, feeds a seventh, additive
  branch Job, `consult_librarian`** (`REQ-SB-63`, not this story's own
  scope to design further — see "The Librarian..." above), mirroring
  `detect_recurring_pattern`'s own terminates-on-its-own branch shape:
  never gates `route_to_project` or the graph's own end, and calls
  `vault_filing_expert.determine_placement_and_file(..., already_filed_
  path=thread_note_path)` — the one concrete `REQ-SB-63` integration point
  this Pipeline exposes.
- **Mid-pipeline human approval is a flat-JSON Pending-Approval-payload
  deferred write, never a LangGraph checkpointer suspension.**
  `route_to_project` and `detect_recurring_pattern` each run their own
  branch to a clean, ordinary completion on every invocation — never
  `interrupt()`, never a suspended/checkpointed graph state. Each creates
  a Pending Approval whose `payload` carries everything needed to finish
  the deferred write (the Thread's own path plus the guessed/candidate
  Project or new-Project proposal; the seed content for the Agent
  Creation Wizard pre-fill) — the actual "finish the routing"/"hand off
  to the wizard" side effect on Approve is dispatched via two new entries
  in `pending_approvals_router.py`'s existing `_APPROVAL_HANDLERS`
  dispatch table (mirroring the Vault Filing Expert Tier-2 precedent,
  [ADR-021](ADR.md) point 5), never a graph resume. This sidesteps
  `MemorySaver`/`SqliteSaver` and any cross-restart durability question
  entirely.
- **Approval gating composes with, rather than replaces, the Pipeline's
  own top-level working-mode gate.** Exactly ONE working-mode check gates
  the whole per-tick Pipeline run (Autonomous/Manual/Supervised),
  evaluated once against the single new Agent-tier identity below —
  mirroring today's existing single `working_mode_registry.get_agent_
  working_mode("email-capture")` check, **not** the now-superseded
  `capture_pipeline.py`'s own rejected per-stage 4-gate shape.
  Independently, and regardless of that top-level gate's own resolution
  (even Autonomous), `route_to_project` and `detect_recurring_pattern`
  ALWAYS create their own Pending Approval — [ADR-021](ADR.md)'s
  "independent of the agent's own working mode" precedent, applied a
  second time.
- **One new Agent-tier identity replaces `email-capture` 1:1 in
  `agent_registry.py`'s `_SEED_AGENTS`** (`type: "worker"`, matching the
  retired entry's own type — zero changes needed to any existing
  type-keyed Map/Section-coloring code or `background_agent_registry.py`'s
  literal exception set). None of the six Jobs get their own
  `agent_registry` entry, Map node, chat surface, or Working Mode — the
  Job-tier default [ADR-041](ADR.md) already defines. Satisfies Scenario 8
  (`email-capture` no longer appears as its own agent) by direct
  construction. **Every real `email-capture`-referencing file this
  retirement touches, confirmed by direct search this pass:**
  `agent_registry.py`, `background_agent_registry.py`, `skill_tools.py`,
  `skill_registry.py`, `agent_schedule_registry.py`, `agents_router.py`,
  `demo_taxonomy.py`, `email_classification.py` itself — the
  decomposer's own retirement task must enumerate all of them explicitly.
- **Thread's own baseline frontmatter family ([ADR-042](ADR.md) point 5)
  gains additive keys, extended rather than reopened:** `customer`
  (written by `Thread-Match/Merge`, mirroring Email's old per-note
  `customer` field) and `project` (absent on a newly created Thread;
  written only once `Route-to-Project`'s Pending Approval resolves).
  **This pass also claims ownership — closing the flag left open by the
  "Meeting → Thread Linking" section, below — of `participants`/
  `last_message_at`,** the two Thread fields `REQ-SB-56`'s own
  fallback-linking heuristic needs: `Thread-Match/Merge` is their natural
  writer, being the only code path that touches every Thread's
  frontmatter on every message.
- **`customer_hub_linking.ensure_hub_note_and_link`'s inline-body-wikilink
  half is NOT reused by `Thread-Match/Merge`** — only
  `ensure_customer_hub_note` (ensures the Customer's OKF directory
  skeleton exists) is called. The inline `**Customer:** [[Hub]]` wikilink
  was Email's own per-note linking convention, superseded by the OKF
  concept file's own `sources:` provenance field, populated at synthesis
  time (`REQ-SB-57`, out of this story's own scope) —
  `Thread-Match/Merge` does not itself write `sources:`.
- **Tags accumulate (unioned, never pruned) on every Thread update** —
  Scenario 7, matching [ADR-042](ADR.md)'s own already-established Thread
  Tags cadence.
- **New `vault_writer.py` primitives needed, both mechanical extensions
  of already-shipped shapes, no new mechanism family:**
  - A header-SCOPED body append (`## Transcript` and the new `##
    Attachments` section are both independently growing — only one of a
    note's sections can be "physically last" for the existing EOF-blind
    `append_person_note_update_line` to correctly target; reuses
    `replace_body_section`'s own header/next-header location logic,
    inserting just before the region's own end instead of replacing it).
  - An enumeration of a Customer's own `projects/*/` subdirectories and
    each one's `status`, for `Route-to-Project`'s "currently open
    Projects" guess — a mechanical extension of
    `list_known_customers()`'s own frontmatter-scan shape, bounded to one
    customer's own projects subtree.
- **`record_conversation_note`/`conversation_index.json` and
  `find_related_note_stems`/`## Related Emails` become dead code for the
  email path once this Pipeline ships** (a `conversation_id`-scoped
  Thread already IS "the related emails, merged") — not deleted by
  `ADR-043` itself; confirming and retiring dead code is a coder-level
  task-scoping decision.
- **Does not decide the Pipeline Builder** ([ADR-041](ADR.md) point 6) —
  stays deferred, now genuinely closer (one real Pipeline exists).

### Pipeline Job Tree Visualization — read-only `StateGraph` introspection (`REQ-SB-65`, extends `ADR-043` point 1, no new ADR)

Renders the Email Capture Pipeline's own real, compiled Job structure as a
connected tree on the Agents Map's Data Gathering Section, replacing the
single opaque `email-capture-pipeline` node with its six real Jobs
(`classify`, `summarize_attachment`, `detect_recurring_pattern`,
`thread_match_merge`, `route_to_project`, `consult_librarian` — confirmed by
direct reading of `email_capture_pipeline.py`'s own current `_build_graph`
this pass, six nodes today, one more than the PRD's own pre-`REQ-SB-63`
prose). Resolves the story's own genuinely-open architecture question
(`gate: flagged`, trigger-8 at `/spec`) as **Option A — a new, read-only
endpoint that inspects the real, compiled graph's own structure; Jobs stay
non-addressable, `ADR-043` point 6 fully intact, not reopened.** Option B
(a genuine per-Job `agent_registry` entry) was considered and rejected —
see Alternatives, below.

- **Verified, not assumed, before deciding:** this codebase's installed
  `langgraph` (`1.2.11`, `requirements.txt`) already exposes exactly the
  introspection primitive Option A needs, as a real, already-public API —
  confirmed by direct reading of the installed package, not inferred from
  documentation. `langgraph.graph.StateGraph.compile()` returns a
  `CompiledStateGraph`, which is a `langgraph.pregel.Pregel` — and
  `Pregel.get_graph(config=None, xray=False)` (`langgraph/pregel/main.py`)
  calls `langgraph.pregel._draw.draw_graph`, returning a real
  `langchain_core.runnables.graph.Graph` object: `.nodes: dict[str, Node]`
  (`Node.id`/`Node.name`) and `.edges: list[Edge]` (`Edge.source`/
  `Edge.target`/`Edge.conditional`/`Edge.data`), built by actually walking
  the compiled graph's own real trigger/write wiring — not a static
  re-statement of whatever `add_node`/`add_edge` calls were made, a live
  structural read. `langgraph`/`langchain_core` are both already-installed,
  already-imported dependencies of this exact module (`ADR-015`/`ADR-041`
  point 5) — this is a new READ call against an existing object, never a
  new dependency, never a new subpackage, never a new tool.
  `langgraph.constants.START`/`END` (`"__start__"`/`"__end__"`) are the
  graph's own synthetic entry/exit sentinel node ids and must be filtered
  out of any Job list — they are not real Jobs.
- **New function, same module, same owner (`ADR-043` point 1's own module
  boundary extended, not reopened):**
  `app/business/pipelines/email_capture_pipeline.py` gains
  `get_job_tree() -> list[dict]`, calling `_GRAPH.get_graph()` on the
  SAME already-compiled, module-level `_GRAPH` singleton
  `run_email_capture_pipeline` already calls (never recompiles a second
  graph instance), filtering `START`/`END`, and shaping the result into
  `{"id": str, "name": str, "depends_on": list[str]}` entries —
  `depends_on` derived directly from the real edges (every edge whose
  `target` is this node contributes its `source` to `depends_on`), which
  is exactly the shape `AgentSummary.depends_on`
  (`agentsApiClient.ts`) and `layoutAgents.ts`'s `computeAgentDepth`/
  `assignTreeAngles`/`buildDependencyEdges` already consume — no new
  frontend data shape is invented, the existing one is finally fed real
  data for the first time (`list_agents()`'s own comment,
  `agents_router.py`, already named `depends_on: []`/
  `branch_target_agent_id: None` as "honest, structurally-correct empty
  defaults, not fabricated data... no real pipeline-dependency source
  exists yet" — this is that source, arriving). This never bakes in a
  static 5-or-6-name Job list (Scenario 3's own bar) — it reads
  `_GRAPH.get_graph()` fresh on every call, so a future Job added, removed,
  or rewired in `_build_graph` changes the returned tree with zero code
  change here.
- **New route, existing router, existing per-agent-subresource
  convention:** `GET /agents/{agent_id}/jobs` in `agents_router.py` —
  mirrors the already-established `GET /agents/{agent_id}/history` /
  `GET /agents/{agent_id}/knowledge-gaps` shape (one more per-agent
  sub-resource, not a new top-level `/pipelines` resource — no second real
  Pipeline exists yet to generalize toward, mirroring `ADR-041`'s own
  "prove one real thing before generalizing" sequencing one layer down).
  Read-only (`GET` only). For `agent_id == "email-capture-pipeline"`,
  returns `email_capture_pipeline.get_job_tree()`'s shaped list, each
  entry additionally carrying `section_id` — the SAME
  `section_registry.get_agent_section("email-capture-pipeline")` value
  `GET /agents`/`GET /agents/{agent_id}` already resolve for this Agent's
  own identity, looked up fresh on every call (Scenario 4's own "resolved
  live, never hardcoded" bar — a future Section reassignment of
  `email-capture-pipeline` moves its whole rendered Job tree with it, with
  zero code change). For any other real `agent_id`, returns `[]` — an
  honest empty list (no Job tree exists for that agent), never a 404 and
  never a fabricated tree; this is what keeps the endpoint's own shape
  generic (not a hardcoded single-agent special case at the router layer)
  while its only real, populated answer today stays exactly the one
  Pipeline this story targets (Scenario 5's own scope bound). Composes
  `app/business/pipelines/email_capture_pipeline.py` directly from the API
  layer, matching `list_agents()`'s own existing multi-registry-composition
  shape (`ADR-003` layering).
- **Frontend integration — reuses `layoutAgents.ts` verbatim, zero changes
  to its own tree/dependency-edge math (`AC` bar: "not a new, parallel
  rendering mechanism"):** a new thin adapter (`features/agents-map/`)
  shapes each fetched Job into an `AgentSummary`-compatible object —
  `id`/`name`/`depends_on`/`section_id` from the endpoint above,
  `type`/`working_mode`/`icon`/`color`/`is_background_agent`/`description`
  all INHERITED from `email-capture-pipeline`'s own already-fetched
  `AgentSummary` entry (so no new CSS class, no new visual affordance is
  needed — the Non-Goals bar) — then REMOVES that one pipeline `AgentSummary`
  entry from the list handed to `layoutAgents()` and splices in its Jobs in
  its place, before `layoutAgents()` ever runs. `layoutAgents()`'s own
  `computeAgentDepth`/`assignTreeAngles`/`buildDependencyEdges` need no
  changes at all — they already operate generically over any
  `AgentSummary[]`; this is the concrete mechanism satisfying "reusing the
  already-built tree/dependency-edge layout math, not a new, parallel
  rendering mechanism." `agentsApiClient.ts` gains one new call,
  `fetchAgentJobs(agentId)`, mirroring `fetchAgentHistory`'s own shape.
  **Left open for the decomposer/coder, disclosed here rather than decided:**
  whether the frontend fetches `/jobs` only for the one, literally-known
  `email-capture-pipeline` id (tighter scope match to this story's own
  explicit single-Pipeline bound, Scenario 5) or fetches it for every
  returned agent and merges whichever responses are non-empty (fully
  generic, zero hardcoded id, marginally more network chatter against
  today's small agent count) — both are real, honest, non-fabricating
  options; neither reopens any tier boundary.
- **`ADR-043` point 6 stays fully intact, not reopened:** none of the six
  Jobs gain an `agent_registry` entry, a chat surface, an independent
  Working Mode, or a Pending-Approval `agent_id` — their SHAPE becomes
  visible on the Map; their addressability does not change at all. This is
  the concrete reason no new ADR is needed: nothing here reverses,
  narrows, or reinterprets any `Accepted` decision — it is a new READ path
  over an already-compiled object, inside the already-established module
  boundary (`ADR-043` point 1), returning data through the already-
  established `api → business` layering (`ADR-003`), reusing an
  already-approved frontend visual language and an already-built,
  already-generic layout module with zero changes to either.

**Alternatives Considered:**

- **Option B — a genuine, lightweight per-Job `agent_registry` entry.**
  Would let `GET /agents` return Jobs alongside real Agents with ZERO new
  frontend code (`layoutAgents.ts` already consumes `AgentSummary[]`
  directly). Rejected: this reopens `ADR-043` point 6's own explicit,
  same-day decision for no functional gain this story's own Acceptance
  bar needs — every one of Option A's real technical requirements
  (grounded tree data, live Section resolution, reuse of the existing
  layout math) is already fully satisfiable without it. It would also
  require every downstream `GET /agents` consumer (chat routing, action
  triggers, the Agent Detail panel, Working Mode toggles) to defensively
  distinguish "a real Agent" from "a Job wearing an Agent's registry
  shape" to avoid exposing chat/Working-Mode/Pending-Approval affordances
  `ADR-041`'s own Job-tier default explicitly withholds — the exact
  structural blurring `ADR-041`/`ADR-043` deliberately built the two-tier
  split to avoid. The operator's own fresh mid-`/spec` context ("the API
  needed anyway" for a future visual tool, distinct from the already-
  deferred Builder) independently confirms a READ-only API is what's
  actually needed now, not a registry/authoring surface.
- **A brand-new top-level `/pipelines` router/resource.** Considered, not
  chosen — no second real Pipeline exists yet to generalize a shared
  resource shape toward (`ADR-041`'s own repeated "prove one real thing
  first" sequencing); nesting under the existing per-agent
  `/agents/{agent_id}/...` sub-resource convention needs no new router
  file and matches this story's own explicit single-Pipeline scope bound
  exactly. Revisit once a second real Pipeline (`REQ-SB-56`) needs the
  same treatment.
- **Recomputing/re-deriving the Job list by re-reading `_build_graph`'s own
  source structure by hand (a hardcoded 6-name list), instead of calling
  the real compiled graph's own introspection API.** Rejected outright —
  directly contradicts Scenario 3's own explicit "never fabricated, never
  hardcoded" bar; would silently go stale the next time this graph's own
  topology changes, exactly the failure mode the story's own Context
  section calls out by name (the PRD's pre-`REQ-SB-63` 5-Job prose already
  having gone stale once).

### Real Thread Summary Synthesis + Opening-Line + One-Shot Backfill (`REQ-SB-67`, extends `ADR-043`/`ADR-044`, no new ADR)

Reverses one narrow, story-level (not ADR-level) Constraint from the
already-`Done` `REQ-SB-55-US-01`'s own text — "this Job never makes a
second Compass call" — via a NEW story, per `Implementation/Pipeline.md`
hard rule 1 (specs are append-only; `REQ-SB-55-US-01` itself is never
edited). Confirmed by direct re-reading: `ADR-043`'s own seven numbered
Decision points never assert this as an architectural rule themselves —
it was purely `REQ-SB-55-US-01`'s own story-level Constraint text, citing
`ADR-041`'s "no second, independent classification/routing call chain"
precedent for the CLASSIFY/ROUTE chain specifically. Adding exactly ONE
new real Compass call inside the already-existing `thread_match_merge`
Job therefore narrows a story-level scoping decision, not any
`Accepted` ADR's own Decision — mirrors `REQ-SB-56-US-01`'s own architect
pass reasoning ("parameter/business-rule choices made WITHIN an
already-`Accepted` data model... neither introduces a new tool,
framework, or structural boundary").

- **Job/node placement — extends `thread_match_merge` in place; no new
  Job, no new graph node/edge.** The new synthesis call lives inside
  `email_classification.py`'s existing `thread_match_merge` function (a
  new plain helper it calls, same module — `ADR-043` point 1's module
  boundary is unchanged). `email_capture_pipeline.py`'s compiled
  `StateGraph` topology is completely unchanged — `get_job_tree()`
  (`REQ-SB-65-US-01`) continues returning the same six Jobs, byte-for-byte.
- **Exactly ONE new real Compass call per `thread_match_merge`
  invocation, covering BOTH the Summary and the opening line together** —
  the parent story's own Constraint ("this story adds exactly the ONE new
  synthesis call... does not reopen or duplicate Classify/Route-to-Project's
  own existing Compass calls") settles this directly; two separate calls
  (one per output) was considered and rejected as an unnecessary doubling
  of real Provider round-trips on every single captured message.
  `compass_client.summarize_content` is reused VERBATIM — same signature,
  same `{"summary": <string>}` parse/error shape (`ADR-034` point 3) — **no
  change to `compass_client.py` at all** (the parent story's own task
  table left this open as "if a narrower prompt shape is warranted"; it is
  not — `summarize_content`'s existing `content`/`source_description`/
  `prompt_override` signature is already generic enough). The new
  `prompt_override` text (default: a hardcoded literal in
  `email_classification.py`, mirroring every sibling Job's own
  `default_instructions` shape; override: `agent_prompts.get_prompt(
  "thread_match_merge")`, below) instructs Compass to return its one
  `"summary"` string as two parts — a first-line "current state at a
  glance" sentence, then a blank line, then the fuller synthesized
  abstract. `thread_match_merge` splits that ONE returned string on the
  first blank line: part 1 → the new opening-line primitive (below); part
  2 (or the whole string, if the model returns no blank line — a graceful
  single-string fallback, not an error) → `## Summary` via the
  already-existing `replace_body_section`. This split lives entirely in
  `email_classification.py` (the Thread-owning module) —
  `compass_client.summarize_content`'s own shared parsing is untouched, so
  every other real caller (`summarize_attachment`, `skill_tools.
  summarize_file`, `vault_filing_expert`) is provably unaffected.
- **Grounding — composed from the Thread's own currently-PERSISTED state,
  not from a full raw-body history that doesn't exist anywhere in this
  data model.** Confirmed by direct reading: `## Transcript`
  (`append_body_section_line`) only ever accumulates a terse one-line
  `- **{received}** — {sender}: {subject}` entry per message — it never
  carries a message's own body text, and this story's own Constraints
  (Scenario 2/3) forbid changing that shape ("unchanged in shape"/
  "completely unchanged"). The richest available grounding is therefore:
  the Thread's OWN existing `## Summary` region (read via the
  already-existing `vault_writer.read_body_section`, BEFORE it gets
  overwritten — on live capture this is the PRIOR real synthesis; empty on
  the very first message; on backfill it's the OLD raw-dump content) + the
  FULL current `## Transcript` region (same `read_body_section`, giving
  Compass the whole conversation's own chronological subject/sender/date
  shape) +, live-capture only, the NEW message's own full body as the
  explicit "what just arrived" delta (backfill passes no delta — a pure
  resynthesis of what's already persisted). This is a rolling/incremental
  synthesis, not a full-history reconstruction — the prior Summary IS the
  accumulated memory of everything before it, since it was itself
  synthesized the same way on the previous message. One new plain helper
  in `email_classification.py` (naming left to the decomposer, e.g.
  `_synthesize_thread_summary(existing_summary, transcript,
  new_message_body, prompt_override) -> dict`) composes this and is called
  IDENTICALLY by both `thread_match_merge` (live capture) and the new
  backfill function (below) — one shared mechanism, not two divergent
  ones, mirroring this codebase's own repeated "generic-primitive-first"
  precedent (`Implementation/Learnings.md`, `SPRINT-048`).
- **Honest, non-fabricating failure posture, mirroring
  `summarize_attachment`'s own `"summary_error"` pattern exactly** —
  `compass_client.CompassError` is caught locally around the one new call;
  on failure, the Thread's existing `## Summary` and opening line are left
  completely untouched (no write attempted), an honest failure outcome is
  recorded for that one item, and the surrounding per-email (live capture)
  or per-Thread (backfill) loop continues — never a raised exception that
  aborts the run (Scenario 5/6).
- **`route_to_project`'s own grounding is repointed; `_build_thread_
  summary_content` is retired as dead code.** `_build_thread_summary_
  content(email)` had exactly two real callers: `thread_match_merge`
  (replaced by the above) and `route_to_project` (used only to ground
  `guess_project_for_thread`'s prompt, and only ever on a brand-new
  Thread's first message — `route_to_project` no-ops immediately when
  `thread_result["created"]` is False). `route_to_project` now reads the
  just-written, REAL synthesized Summary directly —
  `vault_writer.read_body_section(Path(thread_result["thread_path"]),
  "## Summary")` — instead of recomputing a second, divergent summary of
  the same message. This keeps `guess_project_for_thread`'s own call shape
  completely unchanged (still exactly one call — `REQ-SB-55-US-01`'s own
  "no second, independent classification/routing call chain" Constraint
  stays airtight) while improving its grounding text for free.
  `_build_thread_summary_content` itself is deleted — zero remaining
  callers once this lands.
- **New `vault_writer.py` primitive for the opening line (`REQ-SB-54`
  point 11's first real implementation) — a mechanical generalization of
  `replace_body_section`'s own bounded-region-replace mechanism, no new
  mechanism family.** `replace_body_section` locates a GIVEN header's own
  line as the region start; this new primitive (naming left to the
  decomposer, e.g. `replace_body_opening_line(path, new_line)`) instead
  locates the end of the frontmatter block (the SECOND literal `---` line
  in the file — confirmed by direct reading of `_write_frontmatter_note`'s
  own `---\n...\n---\n\n<body>` layout) as the region start, and the FIRST
  `## `-level header line as the region end — the "opening" region,
  regenerated wholesale on every call (create AND update alike), exactly
  like every other `replace_body_section` call site.
  `create_thread_note_baseline`'s own body literal
  (`"## Summary\n\n## Transcript\n"`) needs NO change — the opening region
  starts empty and is filled by this same primitive on `thread_match_
  merge`'s very first invocation, mirroring how `## Summary` itself starts
  empty and is immediately regenerated with real content the same way.
- **Config surface — the new call's prompt composition routes through the
  already-`Accepted` `agent_prompts.py` sibling-store mechanism
  (`ADR-044`), keyed `"thread_match_merge"`, mirroring
  `summarize_attachment`'s own exact wiring**
  (`compass_client.summarize_content(content, source_description,
  prompt_override=agent_prompts.get_prompt("thread_match_merge"))`) —
  never a bare Python literal with no override path. `thread_match_merge`
  gains a real Compass call site for the FIRST time (previously it had
  none — `ADR-044`'s own Decision text explicitly named
  `thread_match_merge`, alongside `detect_recurring_pattern`, as one of
  exactly two Jobs whose Job-Settings `GET` response omits the `prompt`
  key entirely, "a disclosed, hand-maintained fact, deliberately not
  self-healing — if a future story gives either Job a real LLM call site,
  this endpoint's own small exclusion check must be updated by hand").
  This story is exactly that future story: the hand-maintained exclusion
  set in `agents_router.py`'s `/agents/{agent_id}/jobs/{job_id}/settings`
  `GET` handler shrinks from `{"thread_match_merge",
  "detect_recurring_pattern"}` to `{"detect_recurring_pattern"}` — a
  mechanical update `ADR-044`'s own Consequences already anticipated
  verbatim, not a reopening of that ADR.
- **No other new tunables.** The existing shared `content[:8000]`
  truncation inside `compass_client.summarize_content` (pre-existing,
  shared by every caller) remains the only length/token cap on the
  synthesis input — this story does not introduce a second, narrower cap.
  The backfill discovers however many Thread notes exist under
  `Work/Threads/` at run time (iterates `vault_writer.list_all_note_
  paths()`, filtering `frontmatter.get("type") == "Thread"` — mirrors
  `tag_backfill.py`'s own iterate-and-filter shape; no new enumeration
  primitive) — no hardcoded count, so nothing to route through config.
  Sequential, no artificial delay between per-Thread calls, mirroring
  `classify_recent_emails`'s/`summarize_attachment`'s own established
  no-rate-limit precedent at this data volume — nothing new to make
  tunable there either.
- **Backfill module/endpoint — the established `/poc/...` one-shot
  pattern, confirmed by direct reading of all six existing endpoints.**
  New `app/business/thread_summary_backfill.py` (mirrors
  `tag_backfill.py`'s one-module-per-maintenance-operation naming),
  exposing `backfill_thread_summaries() -> list[dict]`, calling the SAME
  shared `_synthesize_thread_summary` helper `thread_match_merge` uses
  (`new_message_body=None`), same per-item honest `try/except
  CompassError` + continue posture. New `POST
  /poc/backfill-thread-summaries` in `app/api/email_poc_router.py`, a thin
  wrapper — identical shape to the six existing endpoints there.

**Alternatives Considered (no new ADR, recorded here for the same reason
`REQ-SB-56-US-01`'s architect pass recorded its own reasoning in prose
rather than a new ADR):**

- **Two separate `summarize_content` calls (one for the Summary, one for
  the opening line).** Rejected — the parent story's own Constraint
  explicitly settles this to exactly ONE new synthesis call; two calls
  would also double real Provider round-trip latency/cost on every single
  captured message for no locked-AC benefit.
- **A new, dedicated `compass_client.py` function (e.g.
  `synthesize_thread_summary`, multi-key JSON response) mirroring
  `classify_email`'s own multi-key-JSON shape.** Considered — this
  codebase does have real precedent for one call returning several named
  fields (`classify_email`'s `customer`/`kind`/`confidence`/
  `recurring_candidate`). Rejected specifically for this story: the
  parent story's own Constraint locks reuse of `summarize_content`
  DIRECTLY ("no second, divergent summarization call shape is invented"),
  and `summarize_content`'s own parsing is shared by several other
  callers this story must not risk — a same-shape split performed
  entirely in the Thread-owning module satisfies the Constraint literally
  with zero shared-file risk.
- **Growing `## Transcript`'s own per-message entries to carry full
  message bodies, enabling a true full-history reconstruction instead of
  a rolling synthesis.** Rejected — a genuinely bigger, unrequested
  Transcript-shape change; the parent story's own Constraints explicitly
  require Transcript's shape/content to stay unchanged (Scenario 2/3).
- **A generic, structural "does this Job have a real call site" probe**
  (mirroring `ADR-044`'s own already-rejected equivalent for the same
  2-item exclusion set) instead of hand-updating the exclusion set.
  Rejected for the identical reason `ADR-044` already recorded: no such
  introspection exists or is warranted for a fixed, small, already-known
  Job set.

### Thread Attachment Capture — Silent-Loss Fix + Per-Message Collision Safety (`BUGFIX-03-US-01`, `BUG-014`, extends `ADR-043`, no new ADR)

Closes `BUG-014`'s two confirmed gaps against the live `Summarize-Attachment`
Job chain (`ADR-043` point 3) — a genuine, code-confirmed silent-loss defect
(gap 1, real root cause below, NOT the mechanism `BUG-014`'s own ledger
entry originally named — see `ESCALATIONS.md` → `ESC-041`, `Resolved`) and
`write_attachments`'s already-confirmed missing filename-collision
protection (gap 2). **No new ADR** — both fixes are mechanical extensions
of already-`Accepted` primitives/conventions (`write_attachments`'s own
save path; `summarize_attachment`'s own already-established "honest,
non-fabricating" return-value convention), never a new tool, framework, or
structural boundary; `ADR-043`'s own seven Decision points are unchanged.

- **Root-cause investigation (resolves `ESC-041`) — the real gap-1
  mechanism, confirmed by direct reading, not `BUG-014`'s own originally
  stated one:** `_summarize_attachment_node`
  (`app/business/pipelines/email_capture_pipeline.py`) only appends an
  entry to `thread_match_merge`'s `attachment_entries` list when
  `email_classification.summarize_attachment(...)` returns a real
  `dated_entry` string — produced ONLY on a genuinely successful
  save-then-summarize path. Every OTHER real outcome of a real,
  non-inline, genuinely-attached file collapses to a `summary_error` key
  that this node silently discards (no exception, no log, no fallback
  entry): an oversized attachment (`outlook_com.py`'s own
  `_MAX_ATTACHMENT_BYTES = 20MB` cap already sets `attachment["content"]`
  to `None` upstream, before `write_attachments` ever sees it), a
  saved-but-non-text-extractable file type, or a real
  `compass_client.CompassError` during summarization. For the oversized
  case specifically, `vault_writer.write_attachments`'s own `.mkdir()`
  call sits INSIDE its per-attachment `if attachment["content"] is None`
  early-continue branch (confirmed by direct reading, lines ~478-483) —
  it is never reached, so the whole `attachments/<thread-slug>/`
  directory itself never comes into existence for that Thread. **This
  single, confirmed mechanism independently explains BOTH of `BUG-014`'s
  own live-observed symptoms** (a real captured Thread missing its own
  `## Attachments` section AND missing its own `attachments/` folder
  anywhere in the vault) from one cause, without needing any unverifiable
  claim about Outlook's own COM behavior for that specific message.
  - **Corroborating evidence, not just structural reading:** the still-live
    sibling path, `email_classification.classify_recent_emails` (dead code
    for the live Thread pipeline, but real, unmodified, and still reachable
    via `app/api/email_poc_router.py`'s `/poc/classify-emails`), already
    carries an honest fallback line for exactly this case —
    `f"- {att['filename']} (not saved — {att['size']} bytes exceeds the
    size cap)"` — proving "record an unsaved attachment's own existence
    anyway" was already an established convention in this codebase BEFORE
    the new Thread pipeline shipped. `REQ-SB-55-US-01-T05`'s own
    `summarize_attachment` Job deliberately chose not to fabricate a
    `dated_entry` for a failed real summary (`MEMORY.md`, 2026-08-16 —
    "`summary_error` was chosen as the equivalent honest signal") but no
    downstream node/function was ever built to actually surface
    `summary_error` into a visible Thread-note artifact — the "equivalent
    honest signal" was designed at the Job level but never wired at the
    pipeline/node level. This is the real, confirmed regression: not "an
    attachment is never extracted," but "an attachment that fails to save
    or summarize for ANY reason vanishes from the Thread note without a
    trace" — a genuine loss of a convention the OLD per-email path already
    had.
  - **What this finding does NOT settle — folded into `T01`'s own
    live-verification scope, not blocking this design:** which of several
    real-world causes explains the specific "Presight Agent Academy Demo"
    Thread's own historical repro — (a) the real attachment's own byte
    size genuinely exceeded the 20MB cap (most probable given a
    presentation file with embedded media, but not provable from code
    alone); (b) it was actually a OneDrive/SharePoint cloud-attachment
    link, which modern M365-signed-in Outlook's own "Attach File" flow can
    insert as a body hyperlink rather than a real `Attachments`-collection
    entry — Outlook's own behavior, not a defect in this codebase, and
    would need a live `item.Attachments.Count` read against the real
    message to confirm or rule out; (c) the specific message was processed
    once via a direct, pre-`T07`-pipeline-wiring dev-verification call
    during `SPRINT-049`'s own same-day build-out (`thread_match_merge`
    shipped at `T03`, `summarize_attachment` at `T05`, the two only wired
    together by `T07`) — `vault_writer.mark_email_processed` is called
    ONLY by `run_email_capture_pipeline`'s own per-tick loop, never by any
    Job function directly, so a message captured once outside that loop
    during development, then later revisited by a real tick as an
    Thread-`update` (`created: False`), is structurally indistinguishable
    from (a)/(b) by static reading; (d) a real, silently-swallowed
    per-attachment COM read failure inside `_extract_attachments`'s own
    broad `except Exception: continue`/`except Exception: return results`
    guards, which log nothing on failure. None of (a)-(d) changes the fix
    below — each is already covered by the SAME honest-signal mechanism
    this fix restores — so the fix proceeds on the strength of the
    confirmed code-read mechanism above; `T01` additionally carries a
    live-diagnostic verification sub-step (mirroring
    `REQ-SB-56-US-01-T00`'s own precedent for "confirm live, don't guess")
    so the coder records which of (a)-(d) actually applied, without that
    confirmation gating the fix itself.

- **Fix scope, gap 1 (silent-loss) — restore the honest-signal convention
  at the pipeline layer, never fabricate a summary that never happened:**
  a real, non-inline attachment must leave SOME durable, visible trace on
  the Thread note regardless of whether it was ultimately saved and/or
  summarized. Concretely: `_summarize_attachment_node`'s loop (or
  `summarize_attachment`'s own return contract — the exact layer is a
  decomposer/coder-level implementation choice, not decided here, since
  either preserves `ADR-043` unchanged) gains a fallback entry, synthesized
  from `result["summary_error"]` + `result["filename"]` (+
  `result.get("relative_link")` when the file WAS actually saved to disk
  but only failed to summarize), appended into `attachment_entries`
  whenever `dated_entry` is absent — mirroring `classify_recent_emails`'s
  own already-established "record even when unsaved/unsummarized" wording
  convention, never a new mechanism family. `summarize_attachment`'s own
  already-AC-tested contract (never fabricate a `dated_entry` implying a
  real summary that never happened) stays intact — the fallback entry is
  visibly distinct wording (e.g. "not saved — exceeds size cap" vs. "saved
  but could not be summarized"), never disguised as a genuine summary.
- **Fix scope, gap 2 (per-message collision safety) — nests one level
  deeper per message, using the message's own `received` timestamp as the
  path segment, not a rename/hash-check scheme (the story's own adopted
  direction):** `vault_writer.write_attachments` gains one new required
  parameter, `message_segment: str`, threaded into its own directory
  composition (`attachments_dir = settings.vault_path / subfolder /
  "attachments" / note_slug / _slugify(message_segment)`) and into its
  returned `relative_link`'s own path. `email_classification.
  summarize_attachment`'s one live call site passes
  `message_segment=received` — `received` is already one of
  `summarize_attachment`'s own existing parameters (used today for the
  `dated_entry`'s own date prefix), so this needs zero new plumbing
  upstream of that one call site. `received` (Outlook's own
  `str(ReceivedTime)`, full timestamp, not a bare `YYYY-MM-DD` truncation)
  is deliberately chosen over a day-only date: a Thread routinely receives
  multiple messages on the same calendar day, and a day-only segment would
  simply relocate `BUG-014`'s own collision window one level down (two
  same-day messages, same-named attachment) rather than closing it; a
  genuine same-second collision within one Thread is not realistically
  reachable. Reuses the SAME `_slugify` primitive `note_stem` already runs
  through (its own 80-char truncation ceiling, the mechanism `BUG-011` — a
  different, still-`Open`, explicitly out-of-scope bug — targets, applies
  unchanged here too, but `received`'s own raw string is well under 80
  chars, so no new truncation-collision surface is introduced by this
  specific segment).
  - **The OTHER live caller of `write_attachments`**
    (`classify_recent_emails`, line ~652 — dead code for the live Thread
    pipeline but still reachable via `/poc/classify-emails`) is NOT part of
    this story's own repro/regression scope: its own `note_stem` already
    embeds a per-email Outlook EntryID suffix
    (`email['received'][:10]}-{email['subject']}-{email['id'][-8:]}`), so
    it is one note ↔ one email ↔ one attachments folder — already
    collision-safe by construction, with no cross-message sharing at all.
    Making `message_segment` a REQUIRED parameter still needs this call
    site updated purely to keep it compiling (a mechanical follow-through,
    not a design question) — an empty-string or id-derived segment is
    equally correct there since no real collision risk exists on that
    path.

**Alternatives considered (why no new ADR):** teaching `outlook_com.py` to
"read `Attachments`" (`BUG-014`'s own originally-stated gap-1 fix) was
rejected outright — it already does, and building against a contradicted
premise would be redundant, non-closing work; a rename/hash-check
collision scheme for gap 2 was rejected in favor of the story's own
adopted per-message nesting, which matches `summarize_attachment`'s own
existing "dated sub-entry per attachment" convention already used in the
Thread body, rather than introducing a second, divergent collision
mechanism.

## Universal Prompt Override + Guardrails Placeholder — Agents and Pipeline Jobs (REQ-SB-66, see [ADR-044](ADR.md))

Replaces four scattered, hardcoded prompt-building call sites plus the
per-turn Chat system message with a real, operator-editable override,
additively layered over today's existing default text; adds a
structure-only Guardrails field with zero enforcement behavior. Applies
uniformly to every real Agent (Worker/Producer/Expert) and every real Job
of the Email Capture Pipeline. The Job-Settings-detail-view
addressability question (how a Job's own Settings becomes reachable at
all) is `ADR-044`'s own decision — this section covers the whole
mechanism; `ADR-044` covers only that one boundary-crossing piece.

- **New sibling store, same shape this codebase already repeats:**
  `app/business/agent_prompts.py` + `.second-brain/agent_prompts.json`,
  composed alongside `agent_registry.py` (never inside it, `agent_
  registry.py` stays byte-for-byte unmodified by this story), keyed
  directly by `id` — a real Agent id (e.g. `"vault-filing-expert"`) and a
  real Job id (e.g. `"classify"`) share one flat namespace, no
  special-casing between the two (mirrors `agent_keywords.py`/`scope_
  registry.py`/`working_mode_registry.py`'s own already-`Accepted`
  shape, `ADR-011` point 2/`ADR-030`; no new ADR needed for this part —
  see `ADR-044`'s own Consequences). An unset id's own Prompt/Guardrails
  both read back as absent/empty — additive layering only, never a
  behavior change for an id nobody has edited yet.
- **Prompt override wiring — four owning call sites in
  `compass_client.py`, plus two more elsewhere, each an additive
  override-or-default read, mirroring `working_mode_registry.py`'s own
  self-healing-default shape (never a required field, never a crash on
  absence):**
  - `classify_email` (owned by the `classify` Job).
  - `classify_task` (owned by the `todo-capture` Agent).
  - `guess_project_for_thread` (owned by the `route_to_project` Job).
  - `summarize_content`, wired ONLY at its `summarize_attachment` Job
    call site — `skill_tools.summarize_file`'s own separate, multi-agent
    shared call to the same function is explicitly left unwired (no
    single owning identity reaches that call site, disclosed scoping
    call, parent story's own `## Non-Goals`).
  - `vault_filing_methodology.build_placement_prompt`'s own
    `_METHODOLOGY_EXCERPT` half (owned unambiguously by the
    `vault-filing-expert` Agent — `determine_placement_and_file` always
    resolves that one identity's model regardless of caller, confirmed by
    direct reading).
  - `agent_orchestration/state.py`'s `history_entries_to_messages` (the
    real, only per-turn Chat `SystemMessage`, read by `graph.py` on every
    Agent's chat turn, Worker/Producer/Expert alike — the override
    replaces the DEFAULT TEXT only; `REQ-SB-33`'s own honest-uncertainty/
    grounding mechanism itself is untouched, it just reads whichever text
    is currently in effect).
- **Guardrails: storage only, zero enforcement call sites anywhere** —
  the same `agent_prompts.json` entry carries a `guardrails` value per
  id, editable and persisted, read by nothing except the Settings view
  itself. Distinct from, and does not touch, `AgentDetailPanel.tsx`'s
  pre-existing, hardcoded Overview-tab `GUARDRAILS_STATEMENT` row
  (`REQ-SB-33-US-01`) — that row is left byte-for-byte unchanged.
- **Settings-tab extension for real Agents — `AgentDetailPanel.tsx`'s
  existing Settings tab gains two new `kv-list` rows (Prompt, Guardrails),
  unconditionally shown for every real Agent Type (Worker/Producer/
  Expert), on the SAME existing tab, alongside the existing per-Type-
  conditional-field convention (Domain-for-Expert/Purpose-for-Producer) —
  never a new tab, never a new screen.** This is the only piece of this
  story that touches `AgentDetailPanel.tsx` itself.
- **Job Settings — a genuinely separate surface, `ADR-044`'s own
  decision, not an `AgentDetailPanel.tsx` extension:** a new `GET`/`PATCH
  /agents/{agent_id}/jobs/{job_id}/settings` pair in `agents_router.py`
  (`agent_id` scopes/validates against `email_capture_pipeline.
  get_job_tree()`, never the storage key) and a new, small, standalone
  frontend component mounted by `AgentsMapPage.tsx` in place of
  `AgentDetailPanel` whenever the clicked Map node's id is a known Job id
  (reusing the SAME already-fetched `fetchAgentJobs(EMAIL_CAPTURE_
  PIPELINE_AGENT_ID)` list `pipelineJobTreeAdapter.ts` already consumes —
  no new fetch). `GET` omits the `prompt` key entirely for
  `thread_match_merge`/`detect_recurring_pattern` (no real call site of
  their own, `ESC-039` Resolved) — `guardrails` is always present. Full
  reasoning, every alternative considered, every consequence:
  [ADR-044](ADR.md).
- **`ADR-043` point 6 stays intact except for this one, explicit,
  bounded exception** — a Job still has no Chat, no History, no
  independent Working Mode, no Schedule, no Pending-Approval `agent_id`,
  no Skills grant; only its own Settings (Prompt where a real call site
  exists, Guardrails always) becomes reachable by clicking its Map node.

## Non-Blocking Manual Capture Dispatch + Scheduling Monitor (REQ-SB-68-US-01, see [ADR-045](ADR.md))

Fixes a real 2026-08-17 production incident (a manual "Run Capture Now"
click froze the entire backend for the full duration of a real, slow
Outlook-COM-plus-Compass capture pass, confirmed live via a concurrent
`GET /agents` returning nothing until it finished) and adds a real
running/duration/outcome monitor for the three capture-style jobs
`agent_schedule_registry`'s shared dispatch lock already covers
(`email-capture-pipeline`, `meeting-capture`, `todo-capture`). Full
reasoning, every alternative considered, every consequence: `ADR-045`.

- **A material grounding correction, found by direct re-reading, not
  assumed.** The story's own analyst-authored Context named
  `agents_router.py::_execute_action`'s `_ACTION_HANDLERS` dispatch as
  the blocking call site. Both of `_ACTION_HANDLERS`'s only two entries
  (`run_capture_now`, `build_knowledge`) are ALSO `skill_tools.SKILLS`
  members (migrated there by `REQ-SB-39-US-02`/`ADR-029` point 5); every
  real caller (`trigger_action`, `chat`, `pending_approvals_router.py`'s
  Approve endpoint) checks `action_id in skill_tools.SKILLS` first and
  branches away before `_execute_action` is ever reached for either id.
  **`_execute_action`/`_ACTION_HANDLERS`/`_run_build_knowledge`/
  `_execute_async_action` are confirmed dead code today** — left
  unchanged, disclosed to `REVIEW-QUEUE.md` as a separate future cleanup
  item, not fixed by this story. The REAL manual dispatch path is
  `agents_router.py::trigger_action`/`chat` → `_invoke_capability` →
  `skill_registry.invoke_skill` → `_dispatch_skill` →
  `skill_tools.run_capture_now` → `email_classification.
  run_capture_and_record_completion` — fully synchronous end-to-end, no
  thread offload anywhere in the chain. This is the path this story
  actually fixes.
- **The fix: reroute through `ADR-037`'s own `dispatch_with_shared_lock`,
  not a new mechanism.** `_invoke_capability` becomes `async def`; when
  `capability_id == "run_capture_now"` (the one id shared by exactly the
  three covered agents, no other agent/capability pair), it calls
  `await agent_schedule_registry.dispatch_with_shared_lock(agent_id,
  capability_id, trigger=trigger)` instead of calling `skill_registry.
  invoke_skill` directly — gaining `asyncio.to_thread` (the non-blocking
  fix) AND the shared Outlook-COM lock (closing the race-condition risk
  the story's own Non-Goals left open, resolved here as "yes, join it")
  in one already-`Accepted`, already-proven function. Every other
  `capability_id` is unaffected — this is a single-id routing branch,
  not a rewrite. Both of `_invoke_capability`'s two real call sites
  (`trigger_action`'s button dispatch, `chat`'s keyword-matched
  dispatch — both already `async def`) add `await` at their existing,
  unchanged call-site lines; `dispatch_with_shared_lock`'s own `trigger`
  Literal widens to include `"chat"` alongside `"scheduled"`/`"direct"`.
  A translated `"skipped"` status (the lock-already-held case) and a new
  `"history_recorded": True` flag (avoiding a duplicate history entry,
  since `dispatch_with_shared_lock` already records its own outcome)
  round out `_invoke_capability`'s existing result-shape translation.
- **`build_knowledge`/`compass-expert` keeps its own, structurally
  identical, already-live blocking gap** (`skill_tools.build_knowledge`'s
  own `ThreadPoolExecutor(...).result()` call still blocks its own
  calling thread) — disclosed, not fixed, explicitly out of this story's
  own three-covered-jobs scope boundary.
- **New run-state persistence — a new sibling store,
  `.second-brain/job_run_state.json`**, via two new pure-I/O primitives
  on `vault_writer.py` (`load_job_run_state()`/`save_job_run_state()`),
  keyed by the same `"{agent_id}::{capability_id}"` composite string
  `agent_schedules.json` already uses. Two new functions on
  `agent_schedule_registry.py` (already `ADR-037`'s canonical home for
  this class of concern) mark start/finish, called from inside
  `dispatch_with_shared_lock`'s own lock-held block, gated to
  `capability_id == "run_capture_now"` — the same structural gate the
  dispatch-routing fix uses, so run-state tracking stays scoped to
  exactly the three covered jobs with no hardcoded agent-id list. A new
  `get_job_run_states()` read accessor computes an in-flight run's
  elapsed duration fresh at read time (`now − started_at`, never
  persisted incrementally) — mirroring `REQ-SB-31-US-01`'s own
  established recompute-fresh-on-refresh convention for this exact page.
  A covered job with no run yet is honestly omitted, never fabricated
  (Scenario 5).
- **No new API surface — extends the existing `GET /system-health`
  only.** `system_health.py::get_system_health()` gains a new
  `"scheduling"` key composing `get_job_run_states()`; the existing
  `"last_capture_run"` key is REMOVED (superseded for display purposes —
  see below). `system_health_router.py` needs no change.
- **`.second-brain/last_capture_run.json`: superseded for display,
  left alone for storage.** The new per-job record for
  `email-capture-pipeline` is a strict superset of what
  `last_capture_run.json` ever tracked. `SystemHealthPage.tsx`'s
  existing `<h2>Last capture run</h2>` + card region is REPLACED outright
  (not left to coexist) by the new "Scheduling" section, at the same
  position (immediately after the "Providers" card), reusing that same
  page's already-established `item-list`/`item-row` visual idiom (one
  row per covered job: running state, elapsed/most-recent duration, last
  outcome — success, or the real error message on failure).
  `record_capture_run_completed()`'s own call site
  (`email_classification.py`, `ADR-008`) and the underlying JSON file are
  left byte-for-byte unchanged — a harmless, disclosed redundancy, not a
  defect; removing that write path is not required by any Scenario here.

## Decoupled Email Pull + Human-Readable, Graph-Connected Thread Notes (REQ-SB-69-US-01, see [ADR-046](ADR.md))

Fixes a real, repeated 2026-08-17 production incident (the shared
Outlook-COM dispatch lock wedged twice the same night, inside `Fetch`'s
own single synchronous `outlook_com.list_recent_mail` call, ahead of
`Classify`/`Thread-Match/Merge`/`Route-to-Project`) by retiring `Fetch`
from the pre-graph batch step (`ADR-043` point 2) and replacing it with
an independently-dispatched, incrementally-staged Pull step, plus a
second, Outlook-lock-free step that drains the staging area. Also makes
Thread notes read like a human wrote them (filename, dates, wikilinks).
Full architectural reasoning, every alternative considered, and every
consequence: [ADR-046](ADR.md).

- **Not a staging/promotion gate on ingested vault data** (`MEMORY.md`'s
  own standing constraint) — a transient, pre-note raw-content buffer
  only, existing solely so an Outlook-COM stall can't lose already-
  fetched content; a staged email becomes a real Thread note through the
  SAME already-`Accepted` graph and approval gates, with no new
  review/promotion step interposed.
- **Staging: a new `app/data_access/email_staging.py` module, one
  directory per staged email under `.second-brain/email_staging/
  <entry_id>/`** (`email.json` metadata + attachment shape identical to
  `outlook_com.list_recent_mail`'s own returned dict, minus raw
  attachment bytes; `attachments/<filename>` — raw bytes on disk,
  mirroring `ADR-034`'s own blob-storage precedent). `stage_email`/
  `list_staged_emails`/`remove_staged_email` are the three primitives;
  `already_processed`/`mark_email_processed` (`ADR-043` point 2) are
  unchanged and consulted a second time, at processing time.
- **`outlook_com.list_recent_mail` gains one new, optional,
  backward-compatible `on_item_fetched` callback**, invoked per item
  immediately after it's fully resolved — never buffered until the whole
  COM loop returns. This is what makes staging genuinely live-updating
  and resumable: a mid-loop stall still leaves every already-fetched item
  durably staged.
- **A new `app/business/pipelines/email_pull.py` module** (sibling to
  `email_capture_pipeline.py`) owns `pull_and_stage_emails` — the ONLY
  function in the email path that still imports `outlook_com`.
  `email_capture_pipeline.py` itself drops that import entirely and now
  reads its per-item input from `email_staging.list_staged_emails()`
  instead of calling `Fetch` — its own compiled
  `Classify`→`Thread-Match/Merge`→`Route-to-Project` DAG (`ADR-043`
  points 1/3/4) is structurally unchanged.
- **Pull and Processing become two independently-dispatchable
  capabilities of the SAME `email-capture-pipeline` Agent-tier identity —
  `pull_email` (joins the shared Outlook-COM dispatch lock, `ADR-037`/
  `ADR-045`) and `process_staged_email` (its own separate, lightweight
  guard — never the Outlook lock).** This is what makes "a stalled Pull
  never blocks already-staged mail" and "stalled processing never blocks
  the next Pull" true by construction — the two capabilities share no
  lock. `run_capture_now` stays the unchanged composite email+meeting+
  todo manual/chat dispatch it is today. Pull does NOT earn its own
  Agent-tier identity (a real, disclosed open question the story left to
  this pass) — it stays a second capability of the existing Agent, per
  `ADR-041`'s Job-tier default, extended one capability further.
- **Thread filename: `<slug(thread_name)>-<date>-<hash8(conversation_id)>.md`**,
  mirroring `meeting_note_filename_stem`'s own shape. `thread_name` (new,
  additive frontmatter) is the FIRST message's own subject, captured once
  at creation, never recomputed. `date` = `last_message_at[:10]`. The
  hash suffix is derived from `conversation_id` alone (not the mutable
  date), keeping it stable across renames. `thread_note_path`'s own
  "deterministic from `conversation_id` alone" contract (`ADR-042` point
  5) is retired for lookup purposes and replaced by a frontmatter-scan
  lookup (`resolve_thread_note_path`, built on the already-shipped
  `list_thread_notes()`) — no new persisted index. A new
  `rename_thread_note` primitive physically renames the file in place,
  preserving content, whenever the date component changes (Scenario 7).
- **A real, previously-latent correctness gap, found and fixed by this
  pass:** `route_to_project`'s Pending-Approval payload now also carries
  `conversation_id`, and `finalize_thread_project_routing` re-resolves
  the Thread's CURRENT path at Approve time via `resolve_thread_note_
  path`, rather than trusting a `thread_path` string captured at proposal
  time — which could go stale the moment a Thread's filename is no
  longer permanently stable.
- **A new, deterministically-regenerated `## Related` body section**
  (via the already-shipped `replace_body_section`) carries Thread's real
  `[[wikilink]]`s to Customer/Person/Project — NOT Email's existing
  `insert_body_line_if_missing`-based inline primitives, which would
  silently conflict with `replace_body_opening_line`'s own full
  ownership of the same pre-first-header region (a genuine primitive
  conflict found by direct reading). Regenerated from real, currently-
  resolvable data only on every `thread_match_merge` call — an honest
  absence, never a fabricated link, for Unsorted/unresolved entities.
- **Human-readable dates without breaking `_date_proximity_gap_days`'s
  real, already-shipped parsing:** a new, additive `last_message_at_
  display` frontmatter sibling field; `last_message_at` itself stays
  byte-for-byte unchanged (still ISO-8601). `## Transcript` entries
  format their own timestamp human-readably at write time.
- **Out of scope, disclosed:** Meeting-capture's/Todo-capture's own
  triggering is unchanged (still bundled with `pull_email` under one
  shared-lock hold in the hourly/app-start composite tick); backfilling
  already-captured Thread notes onto the new filename/date/wikilink shape
  is deferred, not built here.

## Vault Indexing Layer (REQ-SB-01-US-01, see [ADR-024](ADR.md))

The first **real, persistent, re-runnable index** of the vault's notes —
frontmatter, tags, and outgoing/incoming wikilinks. Before this story, every
vault-query primitive (`vault_writer.list_all_note_paths`/
`list_known_customers`/`list_known_kinds`/`list_known_partners` and their
`vault_query_tools.py` pass-throughs, built for `REQ-SB-25`'s agent
tool-calling) re-scanned the filesystem fresh on every call — stateless,
request-scoped I/O, never a cached or persisted structure. No wikilink graph
(forward or backward) existed anywhere in this codebase; this is the first.
Full storage/rebuild reasoning, every alternative considered, and every
consequence: [ADR-024](ADR.md).

- **New `app/business/vault_indexing.py`** — a module-level, in-memory-only
  singleton (`_vault_index: dict[str, dict]`, keyed by each note's filename
  stem — the same identity `write_note()`/wikilinks this project already
  writes use), rebuilt wholesale on every trigger by `rebuild_index()`
  (walks `vault_writer.list_all_note_paths()` — unchanged, already scoped
  to `Work/*/*.md`, so `.obsidian/`/`Templates/` are excluded with zero new
  filtering code — reads each note via `vault_writer.read_note()`, derives
  each note's tags and outgoing wikilink targets, then a second pass
  inverts outgoing links into incoming/backlinks). Assembles a brand-new
  dict, then atomically reassigns the module-level reference — no explicit
  lock (a single-reference rebind is GIL-safe), and discarding the old
  dict wholesale is what gives deletions honest reconciliation for free.
  `get_index()` is a plain whole-dict accessor (no filter/query
  parameters) — internal/test use and the substrate `REQ-SB-02`'s
  browse/search will build on, deliberately **not** a browse/search API
  itself (this story's own Non-Goals boundary).
- **New `app/api/vault_index_router.py`**, `APIRouter(prefix="/vault-index")`,
  registered in `app/main.py`: `POST /vault-index/rebuild` → calls
  `rebuild_index()` synchronously, returns rebuild stats (notes indexed,
  timestamp) — the explicit on-demand re-index path (Scenario 8, `ESC-021`'s
  resolved trigger design). Independent of `capture_scheduler.py`'s
  `_capture_run_lock` — that lock guards overlapping *vault-writing* capture
  runs, a concern this read-only, side-effect-free rebuild does not share.
- **Scheduler-tick wiring: one new, unconditional call, zero scheduler-layer
  changes (Scenario 9).** `app/business/email_classification.py::
  run_capture_and_record_completion` (the function `app/scheduling/
  capture_scheduler.py` already treats as an opaque unit, per `ADR-005`)
  gains one additional call to `vault_indexing.rebuild_index()` —
  **unconditional**, not gated by `email-capture`'s or `meeting-capture`'s
  own working mode (`ADR-018`/`ADR-020`), since vault indexing is core
  plumbing, not an Agents Map agent action. `capture_scheduler.py` itself
  needs no changes, mirroring the precedent `REQ-SB-08`'s meeting capture
  already set for adding a second concern to the same tick.
- **A real, pre-existing gap in `vault_writer.read_note()`, fixed as part
  of this story, in `data_access`:** `_parse_frontmatter_value` had no
  branch for a bracketed list value — a `tags: ["a", "b"]` line read back
  as the literal unparsed string, not a Python list, silently breaking
  "correctly captures that note's tags." Fixed with one more branch,
  mirroring `REQ-SB-30-US-01`'s already-shipped boolean-value branch
  precedent exactly — still not a general YAML parser (unchanged
  docstring caveat), just one more recognized literal shape. No new ADR
  for this fix — same-shape extension of an already-`Accepted` primitive.
- **Wikilink resolution:** a wikilink target is matched against each
  indexed note's own filename stem, case-insensitively — the identity this
  project's own capture pipelines already use when writing wikilinks
  (`upsert_attendee_links`, `record_conversation_note`/
  `find_related_note_stems`). An unresolved target (dangling link, or a
  manually-authored note's free-text wikilink that doesn't match) is kept
  as an outgoing-only entry — no crash, no fabricated target, satisfying
  Scenario 5's "handled honestly" requirement for a deleted note's
  now-dangling incoming reference.
- **No browse/search/query surface added by this story** — confirmed
  against the story's own Non-Goals (`REQ-SB-02`'s job) and Acceptance
  text (indexing only). `vault_indexing.get_index()` is the only read
  accessor this pass adds.

## Browse & Search (REQ-SB-02-US-01, see [ADR-026](ADR.md))

The first browse/search/query surface over `vault_indexing.get_index()` —
`REQ-SB-01-US-01`'s own Non-Goals deliberately left this to `REQ-SB-02`.
List/browse all indexed notes, filter/navigate by tag, a note's own
forward-link/backlink list (textual, clickable — not a visual graph canvas,
`ESC-022` Resolved), and ranked keyword/full-text search (field-weighted
BM25-style, not a bare substring match, not embeddings — `ADR-026`, below,
for the full ranking-mechanism reasoning). Read-only throughout — no new
vault-write capability, no staging/promotion gate on any of it (standing
`MEMORY.md` constraint).

### Index-readiness signal — a small, additive extension of `vault_indexing.py`, not a reopening of `ADR-024`

`ADR-024`'s own `_vault_index: dict[str, dict]` starts empty at module load
and is only ever populated by a call to `rebuild_index()` — there was no way,
before this story, to distinguish "the index has never been rebuilt this
process lifetime" (Scenario 7 — an honest "nothing indexed yet" state) from
"the index was rebuilt and is genuinely empty." `app/business/
vault_indexing.py` gains one small additive piece: a module-level
`_last_rebuilt_at: str | None = None`, set to an ISO-8601 UTC timestamp at
the end of every successful `rebuild_index()` call, plus a new
`get_last_rebuilt_at() -> str | None` accessor. This does not touch
`get_index()`'s own signature or `ADR-024`'s "no filter/query parameters"
decision (a second, independent accessor, not a parameter on the existing
one) — no new ADR; the same "extends X, does not reopen it" posture already
used elsewhere in this file. In practice, `REQ-SB-01-US-01-T04`'s own
unconditional app-start scheduler-tick wiring means the index has almost
always already been rebuilt at least once by the time this story's UI is
reachable — the honest "not indexed yet" state exists for correctness (the
brief startup window, or a future deployment shape without that tick), not
because it is the expected common case.

### `app/business/vault_search.py` (new) — read-only, composes `vault_indexing.get_index()` (and, for `search()` only, `vault_writer.read_note()`)

Mirrors `my_day.py`'s/`system_health.py`'s own "one-module-per-feature,
read-only aggregation, no vault writes" shape. `list_notes`/
`get_note_detail` compose `vault_indexing` only. `search()` additionally
composes `vault_writer.read_note()` directly, one call per candidate note,
to read body text for BM25 scoring — `vault_indexing`'s own index entries
(`ADR-024`, `REQ-SB-01-US-01-T02`) deliberately never store a note's raw
body, only `outgoing_wikilinks` already extracted from it, so there is
nothing to compose *from* `vault_indexing` for the body field. This
directly mirrors `my_day.py`'s own already-`Accepted` precedent of
composing `vault_writer` directly, read fresh on every request, no
caching (`ADR-026` for the full reasoning/cost tradeoff).

- **`list_notes(page, page_size, tag=None) -> {"total", "page",
  "page_size", "notes"}`** — Scenarios 1, 2, 6. Reads the current
  `get_index()` snapshot, optionally narrowed to entries whose `tags` list
  contains the given `tag` (exact, case-sensitive match against the tag
  strings this project's own capture pipelines already write, e.g.
  `customer/masdar`, `kind/email`), sorted by stem (a stable, deterministic
  default ordering — no note-kind-specific date field is universal across
  every indexed kind, so stem is the one field every entry always has),
  then paginated. An empty result (no notes at all, or a tag with zero
  matches) returns `"notes": []` honestly — Scenario 6 is this same
  function returning a correctly-empty list, not a distinct code path.
- **`get_note_detail(stem) -> dict | None`** — Scenario 3. Looks up one
  entry by stem; returns its `frontmatter`/`tags` plus two resolved link
  lists:
  - **Backlinks** — `entry["incoming_wikilinks"]` is already a list of
    resolved source stems (`ADR-024` point 3 derives these at rebuild
    time) — each is looked up directly in the index for its own
    title/kind.
  - **Forward links** — `entry["outgoing_wikilinks"]` is deliberately
    *raw, unresolved* wikilink target text (`REQ-SB-01-US-01-T02`'s own
    shape — resolution happens only in the backlink-deriving pass, against
    the *target*'s entry, not stored back onto the source).
    `get_note_detail` applies the identical case-insensitive
    stem-matching rule `ADR-024` point 3 already established, a second
    time, at read time, to resolve each raw forward-link target to its own
    entry for display (title/kind); a target that doesn't resolve to any
    indexed note (a dangling link, or a manually-authored free-text
    wikilink — `ADR-024`'s own documented honest-handling case) is simply
    omitted from the shown forward-links list, the same "no crash, no
    fabricated entry" posture `ADR-024` already applies to backlink
    derivation, not a new rule.
  - **Title/kind display convention** — `title = frontmatter.get("subject")
    or stem`; `kind = frontmatter.get("type", "Unknown")`. Ordinary
    projection (not every kind's frontmatter carries `subject` — a
    Customer/Person/Partner hub note doesn't — falling back to the note's
    own filename stem, which this project's own filename convention
    already makes a reasonable display name).
- **`search(query, limit=20) -> {"query", "results"}`** — Scenarios 4, 5.
  Field-weighted BM25-style ranking over the current `get_index()`
  snapshot — `ADR-026` for the full mechanism/alternatives reasoning. An
  empty `results` list for a query matching nothing is Scenario 5's own
  honest empty state, not an error — the same function, not a distinct
  code path, mirroring `list_notes`'s own empty-tag-filter handling above.
- **`list_tags() -> {"tags": [{"tag", "count"}]}`** — Scenario 2's own
  prerequisite: the frontend's tag-filter UI needs a real list of tags
  that actually exist in the index to offer the user (the approved
  prototype's own fixed chip buttons are illustrative-only, not a real
  tag-discovery mechanism) rather than requiring the user to already know
  an exact tag string to type. A simple aggregation over the current
  `get_index()` snapshot (a plain per-tag count over every entry's `tags`
  list), sorted by count descending then tag name — no new storage, no new
  mechanism, an ordinary read-only projection alongside `list_notes`.

  <!-- Not a locked-AC-bearing function on its own -- it is the concrete,
  real mechanism the frontend's own AC-02 tag-filter UI needs to be more
  than a mockup; the decomposer's own task split records this explicitly
  rather than leaving it an implicit gap for the coder to discover
  mid-build. -->

### `app/api/vault_search_router.py` (new), `APIRouter(prefix="/vault-search")`

Registered in `app/main.py` alongside the other routers (`ADR-003`
layering — this router calls `vault_search`/`vault_indexing` only, never
`vault_writer`/filesystem directly).

- **`GET /vault-search/status`** → `{"indexed": bool, "last_rebuilt_at":
  str | null}`, reading `vault_indexing.get_last_rebuilt_at()` directly.
  The frontend calls this first, on page load; `indexed: false` replaces
  the **entire** browse/search surface with the honest "nothing indexed
  yet" state (Scenario 7), matching the approved prototype's own top-level
  state-switcher shape (`vault-browser.html`'s
  `data-group="vault-index-state"`) — not a per-endpoint empty-vs-not-
  indexed distinction duplicated three times over.
- **`GET /vault-search/notes?tag=&page=&page_size=`** → `list_notes(...)`
  (Scenarios 1, 2, 6). `tag` omitted = all notes; `page`/`page_size`
  default to `1`/`20` (implementation-internal defaults, not locked by any
  AC).
- **`GET /vault-search/notes/{stem}`** → `get_note_detail(stem)`
  (Scenario 3); `404` for an unknown stem.
- **`GET /vault-search/search?q=&limit=`** → `search(...)` (Scenarios 4, 5).
- **`GET /vault-search/tags`** → `list_tags()` — the real, current tag list
  (with counts) the frontend's tag-filter chip row renders, so Scenario 2's
  filter offers real, discoverable tags rather than requiring the user to
  already know an exact tag string.

### Frontend — `pages/VaultBrowserPage.tsx` + `pages/NoteDetailPage.tsx` (new), routes `/browse` and `/browse/:stem`

New `features/vault-browser/client.ts` (fetch wrapper over the four
`/vault-search/...` endpoints above, same thin-`fetch`-client convention as
`features/my-day/client.ts`). `App.tsx` gains the two new routes;
`Sidebar.tsx` gains a new "Browse & Search" nav item (matching the approved
prototype's own sidebar placement, after the existing nav items — the
prototype's own trailing "Screens (catalog)" entry has no equivalent in the
real shell, so it is not ported).

`VaultBrowserPage.tsx` composes a search box (Scenarios 4, 5), a
tag-filter chip row + paginated browse list (Scenarios 1, 2, 6), and —
first — the `/vault-search/status` not-indexed check (Scenario 7) gating
the rest of the page, matching `vault-browser.html` region-for-region.
`NoteDetailPage.tsx` (route param `:stem`) renders one note's
frontmatter/tags plus its forward-links/backlinks lists as real, clickable
`<Link>`s to `/browse/:stem` (`react-router`'s own client-side navigation
standing in for the prototype's own `button[data-state-target]`/hash-
deep-link mechanic — a real route param plus `react-router`'s own
navigation *is* this project's already-`Accepted` client-side navigation
mechanism, `ADR-010`, not a new one), matching `note-detail.html`
region-for-region — an empty forward-links or backlinks list renders
inline, honestly, exactly as `ADR-024` Scenario 6 already established for
an empty-links index entry.

**CSS: two small additive rules ported verbatim from
`html-prototype/styles.css`** into a new `src/frontend/src/styles/
vault-browser.css` (imported globally, alongside the existing per-feature
stylesheets) — `a.item-row`/`button.item-row` (a real clickable variant of
the existing plain-`<div>` `.item-row`) and `.tag-chip` (a clickable,
pill-shaped tag button) — both already ported into `html-prototype/
styles.css` itself during the `/design` pass; no new class invented here,
no renaming (`ADR-010` Decision 3's own "no renaming/translation step"
convention). Every other visible region reuses existing tokens/primitives
(`.card`, `.badge*`, `.item-list`, `.kv-list`/`.kv-row`, `.empty-state`,
`.input`/`.btn`/`.btn-primary`, `.mono`, `.text-muted`) already ported for
earlier stories — no other new CSS.

**No ADR for the query/API/frontend shape above** — an ordinary, same-shape
extension of already-`Accepted` structural decisions: `ADR-003`'s
layering, the one-module-per-feature `business/`/`api/` pattern already
established repeatedly (`my_day.py`/`system_health.py` and their routers),
and `ADR-010`'s frontend routing/styling/data-fetching conventions. The one
genuinely new mechanism decision — ranked search — is `ADR-026`, below /
[ADR.md](ADR.md).

### Tag/Folder Scope Suggestions — new composing endpoint over already-real enumeration functions (`REQ-SB-50-US-01`, no new ADR)

A new, additive `GET /vault-search/scope-suggestions` endpoint feeding
`AgentDetailPanel.tsx`'s Vault Scope field typeahead (see "Agent-to-Tag/
Folder Vault Scoping" addendum, below) — composing two already-`Accepted`,
already-shipped read-only enumeration functions with zero new
vault-scanning logic of its own, the same "ordinary same-shape extension"
posture already established for every other endpoint in this section
(`ADR-003` layering, `list_tags()`'s own precedent). **No new ADR:** no new
tool, framework, storage mechanism, or trust surface — a pure
recomposition of `vault_search.list_tags()` (business-layer aggregation,
already shipped `REQ-SB-02-US-01`) and `vault_writer.list_known_kinds()`
(data_access-layer folder enumeration, already shipped, previously
reachable only via the MCP tool surface / `vault_query_tools.
list_known_kinds()`, never over HTTP) into one HTTP-reachable shape — the
one genuine gap the story's own Context identified.

- **`app/business/vault_search.py` gains `list_scope_suggestions() ->
  {"tags": [{"tag", "count"}], "folders": [str]}`.** Calls its own existing
  `list_tags()` internally (no duplicated tag-aggregation logic) and
  `vault_writer.list_known_kinds()` directly — mirroring this same
  module's existing precedent of calling `vault_writer.read_note()`
  directly inside `search()`, above. Tags and folders are returned as two
  distinct, un-merged lists, not flattened into one combined suggestion
  array — this mirrors `scope_registry`'s own tag-vs-folder matching
  distinction (a scope value matches either a note's `tags` list or its
  folder name, never conflated — see "Agent-to-Tag/Folder Vault Scoping",
  below) and lets the frontend render two labeled suggestion groups
  without an artificial merge/dedup step. **No `q=` filter parameter** —
  the endpoint always returns the vault's full current tag/folder lists
  (matching this vault's real, small scale, and `agents-map.html`'s own
  already-established "fetch once, filter client-side" tag-filter-chip
  precedent — `list_tags()`'s own existing consumer) rather than a
  server-side search; keystroke-level narrowing happens client-side
  against this one fetched snapshot. This is an implementation-internal
  shape decision, not AC-locked — matching `list_notes`'s own
  page/page_size default precedent, above.
- **`app/api/vault_search_router.py` gains `GET /vault-search/
  scope-suggestions` → `vault_search.list_scope_suggestions()`.** No
  change to this router's own "calls `vault_search`/`vault_indexing` only,
  never `vault_writer`/filesystem directly" rule — the
  `vault_writer.list_known_kinds()` call lives inside the new
  business-layer function, not the router itself.
- **Frontend fetch wrapper: `features/vault-browser/client.ts` gains
  `fetchScopeSuggestions()`**, alongside its existing `fetchTags()` — the
  file that already owns every other `/vault-search/...` fetch wrapper —
  imported cross-feature into `AgentDetailPanel.tsx` (see addendum,
  below), the same already-established cross-feature-import shape this
  panel already uses for `settingsApiClient`/`pendingApprovalsApiClient`/
  `skillsApiClient`.

## The Vault — Knowledge Graph Screen (REQ-SB-75-US-01, no new ADR)

A new interactive force-directed graph screen over the SAME
`vault_indexing.get_index()` snapshot `Browse & Search`, above, already
reads — every note a node (grouped/colored by its own real `frontmatter.
type`, the same field `_kind_for` already reads), every real, resolved
wikilink an edge, click-through into the existing, unmodified `/browse/
:stem` route. Design sign-off happened directly against a live Artifact,
not `/design` (disclosed operator override, see the story's own
`## Context`); this section covers only the mechanism-level choices left
open to `/plan-tasks`.

**No new ADR — a pure composition of two already-`Accepted` decisions,
applied to a new screen, not reopened:** `ADR-003`'s layered `data_access
→ business → api` boundary (the new endpoint composes `vault_indexing`/
`vault_search` only, exactly like every other `/vault-search/*` route);
and `ADR-010`'s frontend routing/styling/data-fetching/component-structure
conventions, including its own Alternatives-Considered posture against
adding a dependency without a concrete, non-speculative need (Decision 2
rejecting React Query/SWR "ahead of any real endpoint," `ADR-002`/`ADR-007`'s
own "no speculative dependency" precedent). Nothing here introduces a new
tool, framework, storage mechanism, or trust surface — the same "ordinary,
same-shape extension" posture the `Browse & Search` section above already
recorded for its own no-ADR endpoints (`ADR-003` layering, the
one-module-per-feature `business/`/`api/` pattern, `ADR-010`'s conventions).

### `app/business/vault_search.py` gains `get_graph() -> {"nodes": [...], "edges": [...]}`

Composes `vault_indexing.get_index()` directly — zero new indexing/caching,
never a second, divergent graph-construction mechanism (the story's own
Constraint 1). Lives in this SAME module (not a new module/router) since it
is an ordinary read-only aggregation over the index, exactly like
`list_notes`/`search`/`list_tags` above.

- **Nodes** — `[_summary(entry) for entry in index.values()]`, reusing this
  module's own existing `_summary()` (`{"stem", "title", "kind", "tags"}`)
  verbatim — the exact same projection `list_notes`/`search` results
  already use, so `kind` is `_kind_for(entry)`
  (`frontmatter.get("type", "Unknown")`), the exact reuse point the story's
  own `## Notes` identified. **No kind-to-fixed-enum mapping table** — every
  real `type` value currently in use (`Customer`, `Thread`, `Meeting`,
  `Person`, `File`, `Partner`, `RawMessage`, `Task`, `Research`, and any
  future value) renders as its own real node kind, never coerced into one
  of only the 5 named-in-Scenario-5 kinds — the PRD's own "every real note"
  acceptance text (the story's own `## Notes` already confirms this
  directly against the real corpus).
- **Edges** — for each entry, each raw `outgoing_wikilinks` target is
  resolved via the identical case-insensitive stem-matching rule
  `_resolve_forward_links`/`ADR-024` point 3 already establish, emitting
  `{"source": entry["stem"], "target": matched_stem}` for a match; a
  target that doesn't resolve to any indexed note's stem (a dangling link)
  or resolves to the entry itself (a self-link) is silently omitted — the
  same "no crash, no fabricated entry" posture `ADR-024`/`get_note_detail`
  already apply, not a new rule (Scenario 2). No dedup of reciprocal
  A→B/B→A pairs — an implementation-internal shape decision, not AC-locked;
  the frontend's own rendering may collapse them visually if desired.
- **No pagination, no `q=`/`tag=` filter parameters** — the endpoint always
  returns the full current graph in one call (matching this vault's real,
  small scale, ~680 notes, and the story's own explicit "large-corpus
  performance work... out of scope at the vault's current real scale"
  Constraint); kind-filtering, name search, and live per-kind counts are
  all a client-side concern over this one fetched snapshot — not a new
  backend aggregation endpoint, since Scenario 3's "the count reflects the
  hidden node count" requirement is inherently a live, client-side-only
  computation regardless (there is no server round-trip on a filter
  toggle). Mirrors `agents-map.html`'s/`scope-suggestions`'s own
  already-established "fetch once, filter client-side" precedent, above.

### `app/api/vault_search_router.py` gains `GET /vault-search/graph`

`GET /vault-search/graph` → `vault_search.get_graph()` directly, registered
alongside this router's existing routes — no new router, no new module
(the story's own Constraint 2). No change to this router's own "calls
`vault_search`/`vault_indexing` only, never `vault_writer`/filesystem
directly" rule.

### Frontend — new `pages/VaultGraphPage.tsx`, route `/vault`, nav label "The Vault"

- **Route path `/vault`** — the natural short-segment continuation of this
  app's existing single-segment route convention (`/browse`, `/settings`,
  `/crawlers`, `/my-day`); `App.tsx` gains `<Route path="/vault"
  element={<VaultGraphPage />} />`, alongside the existing routes.
- **Nav label "The Vault"** — `Sidebar.tsx` gains a new `<NavLink to="/vault">`
  after the existing "Browse & Search" nav item (this file's own established
  "append after existing nav items" placement, already used for `Browse &
  Search` itself). **Resolves the story's own disclosed "Vault Browser" vs.
  "The Vault" naming concern:** direct reading of the real, current
  `Sidebar.tsx` (2026-08-19) confirms the existing `/browse` nav item's own
  real, on-screen label is **"Browse & Search," never "Vault Browser"** — so
  the human-facing naming collision the PRD flagged does not actually exist
  in the shipped UI today; only the internal PascalCase component name
  (`VaultBrowserPage`) shares the "Vault" prefix. This new screen's own
  component/feature names (`VaultGraphPage.tsx`, `features/vault-graph/`,
  below) are deliberately chosen distinct from `VaultBrowserPage`/
  `vault-browser` at the CODE level too, so no future grep for "vault" under
  `pages/`/`features/` collides, even though the nav-facing name is "The
  Vault." The PRD's own naming-overlap concern stays explicitly
  non-blocking/deferred, per the story's own Non-Goals — this decision
  only prevents a NEW collision from this story, it does not rename the
  existing "Browse & Search" screen.
- **New `features/vault-graph/`:**
  - `client.ts` — thin fetch wrapper over `GET /vault-search/graph`, the
    same thin-`fetch`-client convention as `features/vault-browser/
    client.ts`/`features/my-day/client.ts` (`ADR-010` Decision 2).
  - `VaultGraphCanvas.tsx` — a literal HTML5 `<canvas>` element with a 2D
    drawing context, a hand-rolled `requestAnimationFrame` force-directed
    physics loop (repulsion + edge-spring + centering forces) plus
    drag/zoom/pan pointer handling — a direct, zero-new-dependency port of
    the signed-off Artifact's own named technique (the story's own
    Objective #4: "hand-rolled canvas force-directed layout with no
    external libraries"). Confirmed against the real, current
    `src/frontend/package.json`: no graph/visualization dependency exists
    today (`react`, `react-dom`, `react-markdown`, `react-router` only) —
    adding one (e.g. `d3`, `react-force-graph`, `vis-network`) is
    explicitly rejected, no concrete need this screen's own scale (~680
    nodes, a one-time layout computation plus incremental physics ticks,
    not a large-N production-grade rendering problem) doesn't already meet
    with plain `<canvas>` — the exact same "no speculative dependency"
    posture `ADR-010`/`ADR-002`/`ADR-007` already established, applied
    here, not reopened. **Not a reuse of `AgentsMapCanvas.tsx`** — that
    component is an SVG-plus-positioned-`<div>` renderer for a fixed,
    non-physics-simulated radial layout (`polarLayout.ts`), a
    structurally different visualization; `VaultGraphCanvas.tsx` is a new,
    sibling "one component owns one bespoke visualization" instance
    (`ADR-010` Decision 4's own precedent, applied a second time to a
    genuinely different visualization technique, not a new pattern).
  - `forceLayout.ts` — a pure physics/geometry module (node position state,
    one simulation-tick function), mirroring `polarLayout.ts`'s own
    "pure, testable geometry function, not hand-derived per-node
    coordinates inline" precedent (`ADR-010` Decision 4's Alternatives
    Considered explicitly rejected hardcoded per-node coordinates for
    exactly this reason).
  - Kind-filter chips (with live counts) + name search — computed
    client-side over the one already-fetched `{nodes, edges}` snapshot (no
    backend aggregation call), per `get_graph()`'s own "no pagination/
    filter parameters" decision above. Unchecking a kind filters the
    node/edge arrays passed into `VaultGraphCanvas.tsx` before render —
    fully removing, never dimming (Scenario 3; a filtered-out node/edge is
    simply absent from what gets drawn to the canvas that frame, not drawn
    at reduced opacity).
  - Click-to-navigate — `react-router`'s existing `useNavigate()` to
    `/browse/:stem` on node click; zero new note-viewing mechanism
    (`ADR-010`, the story's own Constraint 3). Connection-highlighting and
    any on-canvas inspector panel are coder-level polish within this
    component, not separately AC-locked (see the story's own `## Notes` —
    "Design reference parity").
- **CSS: new `src/frontend/src/styles/vault-graph.css`**, imported
  globally alongside the existing per-feature stylesheets — every node-
  fill-per-kind/edge-stroke/background/chip/search/panel color resolves
  through a real `tokens.css` custom property, zero hardcoded color values
  (Scenario 6), the same posture `vault-browser.css` already established
  for its own two additive rules.

## Data Model

The vault has three top-level roots: `Personal/` (untouched by Second Brain),
`Work/` (everything Second Brain's backend writes lands here — see
[MEMORY.md](../../MEMORY.md)), and `Templates/` (Obsidian core-Templates-plugin
template files — human-authored vault content, not backend-written; see
[ADR-006](ADR.md) / REQ-SB-15, below). Vault structure and note-writing conventions
follow *Beyond the Second Brain* (Mo Elkholy), adopted as a standing
architecture reference — see `Documentation/References/beyond-the-second-
brain-methodology.md` for the full summary and `ADR-004` for the concrete
folder-vs-tag decision it drove. Current state, not full adoption:

- **Folder level:** `Kind` only — `Work/<Kind>/` (`Emails`, `Files`,
  `Notifications`, and any new kind Compass proposes; see `list_known_kinds`
  in `app/data_access/vault_writer.py`). No `Customer` folder level.
- **Frontmatter, per note:** `type` (= kind), `customer`, `tags`
  (`customer/<slug>`, `kind/<slug>`), `classification_confidence`, plus
  source metadata (`subject`, `sender`, `sender_email`, `received`,
  `outlook_entry_id`, `conversation_id`).
- **Email notes gain `recipients: list[{"name","email"}]`
  (`REQ-SB-44-US-01`, [ADR-036](ADR.md) point 7)** — merged To + CC
  recipients, mirroring the Meeting note's own `attendees` field shape
  exactly (below), captured via `outlook_com.py`'s existing
  `_resolve_attendees(item)` mechanism generalized to mail items (a
  `MailItem`'s own `Recipients` collection uses numeric type values that
  coincide with the meeting-recipient ones already filtered on). Additive
  only — an Email note captured before this change simply has no
  `recipients` field; readers must treat a missing field as an empty list,
  not an error. Deliberately does **not** extend `people_extraction.
  ensure_person_note` to CC'd/thread participants — only the sender still
  gets a Person note ensured at capture time (see the Cockpit section,
  above, for why).
- **Linking:** same-thread notes (matched on Outlook `conversation_id`) get
  a `## Related Emails` section with `[[wikilinks]]` to prior notes in the
  thread — Obsidian computes the reverse link automatically, so only the
  newer note needs to link forward. No reference/conceptual/tension link
  taxonomy yet (the book's Chapter 6 distinction) — everything so far is a
  reference-style link.
- **Attachments:** real (non-inline) files saved to `<subfolder>/
  attachments/<note-slug>/`, linked from the note body. Inline signature/
  logo images are filtered at capture time, never saved (`app/data_access/
  outlook_com.py`'s `_is_inline_attachment`).
- **Filename convention:** `<date>-<subject>-<entry-id-suffix>.md` — the
  EntryID suffix is required (same-subject/same-day items collide without
  it; see `MEMORY.md`).

### Customer Hub Notes & Graph Linking (REQ-SB-14)

- **Hub note per customer:** `Work/Customers/<Customer>.md` — `Customers` is a
  `kind` folder like any other (`Work/Emails/`, `Work/Files/`, ...), holding
  one `Customer`-type note per customer/affiliate; not a reversal of ADR-004
  (`customer` still never becomes a folder level for *content* classification
  — this folder holds the hub notes themselves, not customer-classified
  email/file content). Schema:
  `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md`.
- **Wikilink placement — inline body, not frontmatter.** Every customer-tagged
  note gets a single line near the top of its body, e.g.
  `**Customer:** [[Acme Corp]]`, linking to its hub note — extending the existing
  inline-body-wikilink convention already used for same-thread email linking
  (`## Related Emails`, above) rather than introducing a frontmatter-property
  link. Frontmatter-resolved wikilinks are a newer, version-dependent Obsidian
  behaviour; inline body links have always reliably driven the graph view,
  matching this project's established durable-over-clever preference
  (ADR-001, ADR-002). This is a direct extension of the linking convention
  already documented above, not a new structural boundary — no ADR.
- **"Ensure hub note exists, then link" logic lives in
  `app/business/customer_hub_linking.py`** (new module — see Source Layout,
  above), following ADR-003's layering and the existing `tag_backfill.py` /
  `vault_restructure.py` precedent of a dedicated business module per
  maintenance operation:
  - `app/data_access/vault_writer.py` gains the file-I/O primitives (hub-note
    path resolution, existence check, baseline-frontmatter creation reusing
    `write_note`, and a surgical "insert this body line if not already
    present" helper mirroring `insert_tags_line`'s "surgical insert, not full
    rewrite" precedent) — it does the actual reading/writing, no business
    rules.
  - `app/business/customer_hub_linking.py` orchestrates "ensure the hub note
    exists, then link this note to it" as one reusable operation, called from
    two places: the one-time retrofit (batch, over every existing
    customer-tagged note) and `email_classification.py`'s per-write hook
    (going forward) — the same shared mechanism the story requires, not two
    parallel implementations.
  - The retrofit is exposed as a new one-off endpoint,
    `POST /poc/retrofit-customer-hub-links`, in `app/api/email_poc_router.py`
    — matching the existing `/poc/backfill-tags` and
    `/poc/flatten-customer-folders` one-off-migration-endpoint precedent.
- **Preserving manually-added hub-note content (REQ-SB-10 pattern, extended).**
  "Baseline fields" are concretely the hub note's frontmatter keys only —
  `type`, `customer`, `tags`, `affiliate_of` — never its body. On first
  creation, `write_note` writes the full baseline (frontmatter + a short
  auto-generated body stub inviting the user to add their own overview). On
  every later touch (retrofit rerun, or a new note for that customer
  captured), the hub note is **never** rewritten wholesale again: each
  baseline frontmatter key is inserted only if missing (mirroring
  `insert_tags_line`'s surgical-line-insert precedent, generalized to "insert
  this line if this key is absent"), and `affiliate_of` is only ever written
  when absent — never reset to `""` once a real value exists. The body is
  never programmatically touched past initial creation, so user-added
  overview/contacts/focus content is preserved absolutely, not merely
  diffed-and-merged.

### Vault Content Conventions — Templates & In-Vault Guide (REQ-SB-15)

- **A third top-level vault root, `Templates/`** (sibling to `Personal/` and
  `Work/` — see [ADR-006](ADR.md)), holding exactly the four Obsidian
  core-Templates-plugin template files (`Templates/Customer.md`,
  `Templates/Opportunity.md`, `Templates/Agreement.md`,
  `Templates/Consumption-Snapshot.md`), each pre-filling its resolved schema
  from `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md`
  field-for-field, plus the customer wikilink placement convention above.
  Configuring Obsidian's Settings → Templates → "Template folder location" to
  point at `Templates/` is a one-time manual step in the user's own Obsidian
  install — not code, not automated or tracked by `src/backend`.
- **The in-vault guide note lives at `Work/Guides/Manual-Entry-Guide.md`** —
  a new, dynamically-discoverable `kind` folder under the existing
  `Work/<Kind>/` convention (`list_known_kinds` already scans folder names, no
  code change needed for it to be found) — deliberately **not** inside
  `Templates/`, since Obsidian's Templates feature lists every file in the
  configured template folder as insertable; a guide note living there would
  wrongly appear in the "Insert Template" picker. See [ADR-006](ADR.md).
- This entire story is vault-content authoring — four template files and one
  guide note, written directly into the real vault at `VAULT_PATH` — not
  `src/backend`/`src/frontend` code; no source-layout or tech-stack change
  results from it.
- **A fifth template, `Templates/Research.md` (REQ-SB-17), and a fifth
  guide-note entry — a direct extension of this same mechanism, no new
  ADR.** `Templates/` (ADR-006) gains one more file, pre-filling the
  resolved Research schema (`Implementation/Plans/2026-08-10-vault-
  taxonomy-draft.md` → "Researches"): `type: Research`, `title:`, `author:`,
  `tags: [kind/research]` — placeholder values follow the same
  `REPLACE_WITH_...` convention the existing four templates already use
  (e.g. `Templates/Customer.md`'s `REPLACE_WITH_CUSTOMER_NAME`), and the
  body is left free-form (no forced headings), matching the schema
  resolution's own "frontmatter stays deliberately thin" framing.
  **Deliberately no customer/company wikilink or tag** — a book/read isn't
  inherently tied to a customer relationship (the same reasoning already
  applied to a Person note with no known company); this is a real absence
  of a link target, not an overlooked one, per `MEMORY.md`'s standing
  tags-and-wikilinks rule. `Work/Guides/Manual-Entry-Guide.md` (ADR-006)
  gains a fifth `## Research` section, matching the existing four sections'
  exact shape (`**Folder:** ... · **Template:** ...` line plus a short
  explanatory paragraph), and its opening paragraph's "four note types"
  count is updated to five — additive only, the four existing entries are
  untouched (append-only extension of vault content, not a rewrite of the
  `Done` REQ-SB-15-US-01 story's own file). Both files live in the real
  vault at `VAULT_PATH`, not `src/backend`/`src/frontend`.

### Person Notes & Email-Sender Extraction (REQ-SB-10)

- **Person notes** — `Work/People/<slug-of-email-address>.md` (`People` is
  another dynamically-discovered `kind` folder, per `list_known_kinds`, no
  code change needed). Schema resolved in `Implementation/Plans/
  2026-08-10-vault-taxonomy-draft.md` → "People": `type`, `name`, `email`,
  `phone`, `linkedin`, `tags` frontmatter; an inline body wikilink to the
  sender's company's Customer hub note when (and only when) the company
  matches a known customer, extending the same inline-body-link convention
  `customer_hub_linking.py` established (see "Customer Hub Notes & Graph
  Linking", above) rather than a new linking mechanism.
- **Filename / dedup key: the sender's email address, lowercased and
  slugified — never the display name.** Two people can share an identical
  display name; email addresses are the schema's own dedup key ("deduped by
  email address (names vary in formatting, addresses don't)" per the
  resolved schema). Lowercasing before slugifying prevents a second,
  spurious Person note when the same address is captured with different
  casing across different emails (e.g. Exchange does not guarantee
  consistent `sender_email` casing). This is a straight reuse of the
  existing `_slugify` filename-safety helper already used for
  `hub_note_path`/`write_note` — email addresses do not contain any of the
  characters `_slugify` strips, so this is effectively a lossless,
  collision-safe identity mapping (per `MEMORY.md`'s filename-uniqueness
  constraint). The `email:` frontmatter field itself still stores the
  sender's address exactly as captured (not lowercased), so the filename
  normalization is a lookup-key concern only, not a display-value edit.
- **Company derivation from the sender's email domain** (`app/business/
  people_extraction.py::derive_company_from_email`): take the substring
  after `@` in `sender_email`, lowercase it, and check it against a small
  **hardcoded** set of well-known personal/free email-provider domains
  (`gmail.com`, `googlemail.com`, `outlook.com`, `hotmail.com`, `live.com`,
  `msn.com`, `yahoo.com`, `ymail.com`, `icloud.com`, `me.com`, `aol.com`,
  `protonmail.com`, `proton.me`, `gmx.com`, `mail.com`, `yandex.com`,
  `zoho.com`). A domain on that list yields no company at all (Scenario 5 —
  tag/link both absent). Otherwise the company slug/name is derived from the
  domain's first label — `core42.ai` → slug `core42`, display name
  `Core42` (`slug[0].upper() + slug[1:]`) — matching the resolved schema's
  own worked example verbatim. **This blocklist is deliberately fixed, not
  vault-derived like `list_known_customers`/`list_known_kinds`.** Those two
  lists enumerate values that are genuinely open-ended per-vault content (a
  new customer or a new Compass-proposed kind can appear any day); the
  universe of major personal/free email providers is a small, well-known,
  externally-stable set that has nothing to do with this vault's own
  content — there is no vault signal that could ever grow or shrink it the
  way real customer/kind values do, so hardcoding it is not the same
  shortcut `list_known_customers` deliberately replaced. Revisit only if a
  real captured sender surfaces a personal-domain provider missing from
  this list (extend the constant then — no architecture change needed).
- **Company-to-known-customer matching** (`app/business/
  people_extraction.py::find_matching_customer`): compares the derived
  company name against every name `vault_writer.list_known_customers()`
  returns, **not** by exact string equality but by comparing each side's
  tag-slug form (`core42` vs `Core42` vs `CORE42` must all match). This
  reuses the exact slugging rule tags already use rather than inventing a
  second normalization scheme: `vault_writer`'s previously-private
  `_tag_slug` helper is promoted to a public `tag_slug(text: str) -> str`
  (pure rename, no behaviour change, existing internal call sites updated)
  so business-layer code has one shared, public normalization function
  instead of duplicating slug logic outside `data_access`. Returns the
  matching known-customer's original (non-slugified) name — the exact
  string `customer_hub_linking`'s hub-note primitives expect — or `None`.
- **Layering — new Person-note primitives in `data_access`, orchestration in
  a new `app/business/people_extraction.py`,** following ADR-003 and the
  same one-module-per-maintenance-operation shape as `tag_backfill.py` /
  `vault_restructure.py` / `customer_hub_linking.py`:
  - `app/data_access/vault_writer.py` gains: `person_note_path(email)`,
    `person_note_exists(email)`, `build_person_tags(company: str | None)`
    (returns `["kind/person"]` alone, or `["company/<slug>", "kind/person"]`
    when a company was derived — mirrors `build_tags`'s shape but for the
    People schema's separate `company/` tag namespace), and
    `create_person_note_baseline(name, email, tags)` /
    `ensure_person_note_baseline_frontmatter(path, name, email, tags)`
    (baseline keys: `type`, `name`, `email`, `phone`, `linkedin`, `tags` —
    same surgical insert-if-missing contract as the hub-note baseline
    functions). The existing generic `insert_body_line_if_missing` is
    reused as-is for the company wikilink line — no Person-specific
    variant needed, it already takes an arbitrary `path`/`line`.
  - `app/business/people_extraction.py` (new) owns
    `derive_company_from_email`, `find_matching_customer`, and
    `ensure_person_note(name, email)` — the shared "ensure this sender's
    Person note exists and is up to date" operation, called once as a
    one-time batch (`retrofit_people_from_emails`, iterating
    `vault_writer.list_all_note_paths()` and reading each note's `sender`/
    `sender_email` frontmatter — Person and Customer hub notes are silently
    skipped by construction, since neither carries a `sender_email` field)
    and once as a per-write hook
    (`ensure_person_note_for_captured_email(sender_name, sender_email)`).
    Both entry points skip (no error) when `sender_email` is blank
    (Scenario 9).
  - **`ensure_person_note` calls `customer_hub_linking`'s two granular
    primitives directly (`ensure_customer_hub_note`,
    `link_note_to_customer_hub`), never the combined
    `ensure_hub_note_and_link`, and only after `find_matching_customer`
    confirms a real match.** This is the load-bearing carve-out the story's
    Constraints require: `ensure_hub_note_and_link` unconditionally creates
    a Customer hub note for whatever string it's given, correct for email
    classification (every classified note already belongs to a real
    customer) but wrong for an arbitrary derived company name, most of
    which are not customers at all. Gating on `find_matching_customer`
    first, then calling only the two granular primitives, reuses
    REQ-SB-14's actual file-I/O work (hub note creation/top-up, idempotent
    body-line insertion) without its unconditional-creation entry point —
    a company with no match gets its `company/<slug>` tag and nothing else,
    per `MEMORY.md`'s standing tags-and-wikilinks rule ("a tag with no link
    target is a real absence, not an overlooked link").
  - **This is the first time one `business/` module calls into another
    `business/` module** (`people_extraction.py` → `customer_hub_linking.py`).
    ADR-003 constrains `business/` to no HTTP and no direct filesystem/data
    I/O of its own — it does not forbid one business module composing
    another's already-layered orchestration. This is a horizontal call
    within the same layer, not a boundary violation, and is recorded here
    explicitly so it reads as an intentional, permitted shape rather than an
    unreviewed precedent for future stories.
  - The retrofit is exposed as a new one-off endpoint,
    `POST /poc/retrofit-people-from-emails`, in `app/api/
    email_poc_router.py` — matching the existing `/poc/backfill-tags`,
    `/poc/flatten-customer-folders`, and `/poc/retrofit-customer-hub-links`
    one-off-migration-endpoint precedent. One endpoint is sufficient; the
    retrofit is a single operation over all already-captured Email notes,
    the same shape as REQ-SB-14's own single retrofit endpoint.
  - **Going-forward hook:** `app/business/email_classification.py`'s
    `classify_recent_emails` gains one additional call,
    `people_extraction.ensure_person_note_for_captured_email(email["sender_name"],
    email["sender_email"])`, placed immediately after the existing
    `customer_hub_linking.ensure_hub_note_and_link(note_path, customer)`
    call (REQ-SB-14) — added alongside it, not replacing it; the two hooks
    serve different note types (Customer hub notes keyed by the email's own
    customer classification; Person notes keyed by the email's sender) and
    are independently idempotent.
- **Preserving manually-added Person-note content** follows the exact
  baseline-preservation contract already established for Customer hub notes
  (see above): baseline frontmatter keys (`type`, `name`, `email`, `phone`,
  `linkedin`, `tags`) are inserted only if missing, never overwritten once a
  real value exists; the body, once created, is never programmatically
  rewritten wholesale — only the company wikilink line may be surgically
  inserted later if a company becomes a known customer after the Person
  note already existed (Scenario 8), reusing `insert_body_line_if_missing`
  exactly as `customer_hub_linking.link_note_to_customer_hub` already does.
- **Meeting-attendee-based extraction is explicitly out of scope for this
  pass** (blocked on REQ-SB-08, which does not yet exist) — `ensure_person_note`
  is written generically enough (`name`, `email` in, no email-specific
  parameters beyond the two call sites' own inputs) that a future
  meeting-attendee story can call it the same way, but that wiring is not
  built here.
- **Email → Person wikilink, the inbound direction (`BUGFIX-01`, closes
  `BUG-001`).** The per-write hook and the original retrofit above only ever
  created/updated the sender's Person note as a side effect — the Email
  note's own body never linked back to it, so a Person note rendered as a
  disconnected graph node relative to every Email that actually mentions it
  despite existing (`MEMORY.md`'s 2026-08-11 standing constraint: a
  referencing note must link out, not just cause the referenced note to be
  created). This is closed with the exact same inline-body-wikilink
  mechanism already in place for Customer hub links, not a new one:
  - `app/business/people_extraction.py` gains one small primitive,
    `link_email_to_person(email_note_path, person_note_path) -> bool`,
    mirroring `customer_hub_linking.link_note_to_customer_hub`'s shape —
    it derives the Person note's filename stem and inserts a
    `**Sender:** [[PersonStem]]` line into the Email note's own body via
    the same `vault_writer.insert_body_line_if_missing` primitive the
    Email note's existing `**Customer:** [[Hub]]` line already uses (a
    second surgical first-line insertion into the same note, not a new
    mechanism). Because `insert_body_line_if_missing` always inserts at the
    top of the body, calling it a second time places the newer line above
    the one inserted by the earlier call in the same write — the Email
    note ends up with `**Sender:** [[...]]` above `**Customer:** [[...]]`
    given the two calls' existing order; cosmetic only, no AC depends on
    relative line order.
  - `app/business/email_classification.py`'s `classify_recent_emails`
    captures the already-existing return value of its
    `people_extraction.ensure_person_note_for_captured_email(...)` call
    (previously discarded) and, when it is not `None`, calls
    `people_extraction.link_email_to_person(note_path, person_result["note_path"])`
    — `note_path` is the just-written Email note's own path, already in
    scope at that call site (`note_path = vault_writer.write_note(...)`,
    above). No new plumbing, no signature change to
    `ensure_person_note_for_captured_email` itself (left untouched so any
    future caller, e.g. a `REQ-SB-08` meeting-attendee hook, is
    unaffected).
  - A new one-time batch, `people_extraction.retrofit_email_sender_links`,
    mirrors `retrofit_customer_hub_links`'s and
    `retrofit_people_from_emails`'s exact shape: iterate
    `vault_writer.list_all_note_paths()`, skip a note with no
    `sender_email` (Person/Customer-hub notes are skipped by construction,
    same as the existing retrofits), otherwise call `ensure_person_note`
    (guaranteeing the Person note exists/is current — safe and idempotent
    to call again even if `retrofit_people_from_emails` already ran) then
    `link_email_to_person`. Exposed as a new one-off endpoint,
    `POST /poc/retrofit-email-sender-links`, in
    `app/api/email_poc_router.py`, matching the three existing
    one-off-migration-endpoint precedents
    (`/poc/retrofit-customer-hub-links`, `/poc/retrofit-people-from-emails`,
    `/poc/backfill-tags`).
  - No new structural boundary, tool, or framework decision — this closes a
    coverage gap in the already-Accepted inline-body-wikilink convention
    (established for Customer hub links, already reused as-is for
    Person→Company), applied to a relationship direction the original
    `REQ-SB-10` pass didn't check. No ADR.

### Meeting Notes & Calendar-Attendee Extraction (REQ-SB-08)

- **Meeting notes** — `Work/Meetings/<subject>-<date>-<suffix>.md` (the
  8-hex-char suffix's source changed 2026-08-11, [ADR-013](ADR.md); see
  below) (`Meetings` is another dynamically-discovered `kind` folder, per
  `list_known_kinds`, no code change needed). Schema resolved in
  `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md` → "Meetings":
  `type`, `customer`, `subject`, `start`, `end`, `location`, `organizer`,
  `tags` frontmatter; inline body `**Customer:** [[Hub]]` (when an
  attendee's company matches a known customer) followed by `**Attendees:**
  [[Person1]], [[Person2]], ...`. One note per meeting — no separate
  Meeting-Minutes type; free-form minutes/notes live below the
  auto-populated baseline, never programmatically rewritten once added,
  same living-document rule as Person/Customer-hub notes.
- **Calendar read — `app/data_access/outlook_com.py::list_calendar_events`
  (new, [ADR-008](ADR.md)).** Ports agentic-map's
  `list_upcoming_events`/`list_calendar_since` COM mechanics
  (`ns.GetDefaultFolder(9)`, `items.IncludeRecurrences = True`) into this
  codebase's own `list_recent_mail`-shaped conventions (plain sync
  function, `pythoncom.CoInitialize`/`CoUninitialize`, best-effort
  per-item skip). **The sync window is one bounded date range around
  "now"** (`[now - days_back, now + days_ahead]`) rather than either of
  agentic-map's two narrower semantics alone — this is what "the sync
  window" in the PRD's acceptance text concretely means for this project.
  Per-event fields: `id` (EntryID), `subject`, `start`/`end`, `location`,
  `organizer`, `attendees: list[{"name", "email"}]` (`To` + `Cc` merged
  into one flat list — the resolved schema makes no required/optional
  distinction). Full reasoning, including the alternatives rejected:
  [ADR-008](ADR.md).
- **Occurrence dedup key: a SHA-256 hash of `subject` + the occurrence's
  own full, precise start timestamp — no Outlook-provided identity field
  at all ([ADR-019](ADR.md), 2026-08-12, supersedes [ADR-013](ADR.md)
  points 1 and 2).** This is the **third** dedup-key mechanism this project
  has tried, named plainly rather than glossed over: `ADR-008` originally
  chose `EntryID`, live-confirmed non-unique per occurrence
  (`ESCALATIONS.md` → `ESC-002`); `ADR-013` then replaced it with
  `AppointmentItem.GlobalAppointmentID` (Outlook's own documented
  guaranteed-unique-per-occurrence identifier), which live verification
  found has the **exact same defect** on this Outlook installation —
  identical across every real occurrence of two separate recurring series,
  with its documented `PropertyAccessor`/DASL fallback erroring on every
  occurrence too (`ESCALATIONS.md` → `ESC-012`). Rather than search for a
  third Outlook-native identity field to trust empirically, `ADR-019` stops
  depending on Outlook-provided identity altogether: the filename/dedup
  suffix is an **8-hex-char prefix of a SHA-256 hash of
  `f"{subject}|{start}"`**, where `start` is the full precise timestamp
  string `list_calendar_events` already returns (not the coarse
  `start[:10]` date-only slice the filename's own display component still
  uses). This is a **structural**, not empirical, uniqueness guarantee —
  two distinct real occurrences of the same recurring series cannot share
  an identical exact start moment; the subject is combined in so two
  different, unrelated meetings that happen to start at the same instant
  still get distinct notes. `list_calendar_events` no longer resolves or
  depends on any per-occurrence identity field for dedup purposes (the
  `GlobalAppointmentID`-resolution helper and its DASL fallback, added by
  the now-superseded `ADR-013` fix, are removed); `id` (`EntryID`) is still
  returned, load-bearing again for one narrow purpose only — the
  legacy-path lookup below. `.second-brain/processed_meeting_ids.json`
  still mirrors `processed_email_ids.json`'s flat-set-of-IDs shape
  (`load_processed_meeting_ids()`/`mark_meeting_processed(marker)`), now
  recording the resolved note's own filename stem as its `marker` value;
  its existing heterogeneous `EntryID`-era and `GlobalAppointmentID`-era
  entries (written before this fix) are left untouched — it remains an
  append-only audit trail, never a schema-enforced lookup structure.
  **No migration of the 39 already-captured Meeting notes** — note-existence
  resolution checks the new precise-timestamp-hash path first, then falls
  back to the original pre-`ADR-013` legacy `EntryID`-suffix path;
  whichever is found on disk gets topped up. **`ADR-013`'s own middle
  `GlobalAppointmentID`-hash fallback tier is deliberately dropped, not
  carried forward** — confirmed live that zero real notes were ever
  created under that scheme, so keeping it would be dead code carrying a
  live-confirmed defect rather than a genuine safety net. Full reasoning,
  every alternative considered, and the one honestly-named residual risk
  the legacy-path fallback still does **not** fully close (unchanged from
  `ADR-013`, a bounded, shrinking-over-time edge case limited to the
  38/39 already-known dates): [ADR-019](ADR.md); `ADR-013` itself is
  `Status: Superseded by ADR-019` (points 1/2), its point 3 unmodified and
  reused.
- **Customer derivation tie-break: majority vote among attendee-company
  matches, first-encountered match as the tie-break.** For each attendee
  (after the vault-owner self-email exclusion, below), `meeting_
  classification.py` calls the existing, unchanged
  `people_extraction.derive_company_from_email` /
  `find_matching_customer` per attendee email and tallies how many
  attendees matched each known customer; the customer with the most
  matches wins, and a tie is broken by whichever matched customer was
  first encountered in Outlook's own attendee order (`To` then `Cc`). No
  match among any attendee means no `customer` tag/wikilink (per the
  resolved schema). **Majority, not organizer-priority or first-match, and
  why:** majority correctly reflects "who this meeting is really about"
  when several attendees share one company (the common real case — a
  customer meeting typically has multiple people from the customer's
  side), where a pure first-match would key off whichever attendee
  Outlook happens to return first (an ordering artifact, not a real
  signal). Organizer-priority was also considered and rejected: Outlook's
  `Organizer` COM property is a display-name string with no readily
  available email address to run `derive_company_from_email` against
  (unlike attendees, resolved to real addresses via `Recipients`/
  `GetExchangeUser`) — reliably resolving an organizer's own address would
  be new, unproven COM mechanism this story's port-don't-design-fresh
  constraint discourages. This is a business-rule/algorithm decision
  within already-established primitives, not a new tool/framework/
  structural-boundary choice — recorded here, not as its own ADR.
- **Vault-owner self-email exclusion (Scenario 11, operator-confirmed
  behaviour) — sourced from a new `Settings.self_email` config value, not
  a dynamic Outlook COM lookup.** `app/config.py`'s `Settings` gains a
  required `self_email: str` field (`.env`-sourced, alongside
  `VAULT_PATH`/`COMPASS_*`). `meeting_classification.py` filters
  `self_email` (case-insensitive) out of `list_calendar_events`'s
  attendee list before any attendee reaches
  `people_extraction.ensure_person_note` or customer derivation — no
  Person note about the vault owner, and their own company (if any) never
  participates in the majority vote above. Full reasoning (why config over
  a `Session.CurrentUser` COM lookup): [ADR-008](ADR.md).
- **Attendee Person notes — direct reuse, no new mechanism.** Every
  attendee (post-exclusion) gets the exact `people_extraction.
  ensure_person_note(name, email)` treatment already built for email
  senders (REQ-SB-10) — the function was already written generically
  enough for this (`architecture.md`'s own prior note); this story calls
  it once per attendee, unchanged. Customer-hub linking for a meeting's
  derived customer reuses the same granular-primitives-only-after-a-
  confirmed-match carve-out `people_extraction.ensure_person_note` already
  established for company matches — `meeting_classification.py` must not
  call `customer_hub_linking.ensure_hub_note_and_link` directly for an
  unconfirmed match, per the story's Constraints.
- **Scheduler wiring — rides REQ-SB-07's existing hourly job, no new job.**
  `email_classification.run_capture_and_record_completion` gains one
  additional call, `meeting_classification.classify_recent_meetings()`,
  alongside its existing `classify_recent_emails()` call, before the one
  shared `vault_writer.record_capture_run_completed()` call.
  `app/scheduling/capture_scheduler.py` requires zero code changes — it
  already treats `run_capture_and_record_completion` as an opaque unit.
  Extends ADR-005 (which explicitly anticipated "generalizing the one job
  to run multiple pipelines" as the intended path) without rewriting or
  contradicting it. Full reasoning: [ADR-008](ADR.md).
- **New vault_writer primitives (data_access, REQ-SB-08).** Meeting-note
  path resolution and baseline-frontmatter create/top-up follow the exact
  same insert-only-if-missing contract already established for
  Person/Customer-hub notes. The `**Attendees:** [[P1]], [[P2]], ...]`
  body line needs a **new** primitive, distinct from the single-target
  `insert_body_line_if_missing` reused as-is for the `**Customer:**
  [[Hub]]` line: unlike a single-target link (present or not), the
  Attendees line can legitimately grow across reruns as new attendees are
  confirmed (Scenario 6), so it needs a per-attendee-wikilink upsert, not
  a whole-line insert-if-missing. Exact function shape left to the
  decomposer/coder; this generalizes the existing "insert this line/key if
  absent" philosophy already applied twice (frontmatter keys, then a
  single body line) rather than introducing a new one.

### Task Notes & Outlook-Tasks Capture (REQ-SB-09, see [ADR-027](ADR.md))

- **Task notes — `Work/Tasks/<subject>-<capture-date>-<entry-id-
  suffix>.md`.** `Tasks` is another fixed, dynamically-discovered `kind`
  folder (per `list_known_kinds`, no code change needed), mirroring
  `Work/Meetings/`'s own shape — Task, like Meeting, is its own note type,
  never a Compass-classified `kind`. Schema (confirmed by the story, see
  `REQ-SB-09-US-01`'s own `## Context`): `type: Task`, `customer` (present
  only when a match is found), `subject`, `due` (omitted, not written as a
  placeholder, when Outlook has no due date set), `status: Not Started |
  In Progress | Completed` (three-value mapping from Outlook's own
  `Complete`/`Status` fields — see [ADR-027](ADR.md) point 2), `tags`,
  `source: outlook-task`, `outlook_entry_id`. Body starts with `**Customer:**
  [[Hub]]` when a match exists (reusing `insert_body_line_if_missing` as-is,
  the same single-target line Email/Meeting already use for their own
  Customer line), followed by free-form space for the user's own notes —
  never programmatically rewritten once added, the same living-document
  rule every other captured note type already follows. **Unlike Meeting
  notes, a Task note links no Person** — an Outlook Task has no attendee/
  contact list, so there is no natural entity relationship to wikilink
  beyond the optional customer match; this is an intentional absence
  (the story's own Constraints), not a gap in the standing tags-and-
  wikilinks rule.
- **`capture-date` in the filename is the date the note was FIRST
  captured — never recomputed from Outlook's own (mutable) `due` field on
  a later run.** This is the load-bearing reason Task's own dedup mechanism
  (below) genuinely diverges from Meeting's: Scenario 6 requires a due-date
  change between runs to still resolve to the *same* note, which a
  recompute-from-`due` filename (Meeting's own `ADR-019` pattern,
  substituted field-for-field) would break.
- **Tasks-folder read — `app/data_access/outlook_com.py::
  list_outlook_tasks` (new, [ADR-027](ADR.md)).** `ns.GetDefaultFolder(13)`
  (`_OL_FOLDER_TASKS`), no date-window parameters (unlike
  `list_calendar_events`) — a flat `limit`, mirroring `list_recent_mail`'s
  simpler shape, since a task has no natural "occurs near now" framing.
  Per-item fields: `id` (`EntryID`), `subject`, `due` (`None` when
  Outlook's own "no date set" sentinel is detected — a defensive guard,
  not optional polish, since it is what makes the schema's "omitted if
  none is set" possible), `status`, `body`. **No `IncludeRecurrences`-
  equivalent exists on the Tasks folder's `Items` collection at all** — a
  structural fact about the Outlook Object Model (that property is
  Calendar-folder-specific), and the reason a recurring Task never expands
  into multiple simultaneously-returned occurrence-items the way a
  recurring meeting does — the specific mechanism that broke `EntryID`/
  `GlobalAppointmentID` for Calendar (`ESC-002`, `ESC-012`) structurally
  does not apply to Tasks. Full reasoning, including the alternatives
  rejected: [ADR-027](ADR.md).
- **Dedup/top-up key: `EntryID`, looked up through a new load-bearing
  `.second-brain/task_note_index.json` (`{entry_id: note_filename_stem}`),
  consulted BEFORE any path is computed from current Outlook fields —
  not a recomputed-deterministic-path check the way Meeting's
  `resolve_meeting_note_path` works.** A first-time-seen `entry_id` (not
  yet in the index) creates a new note and records the mapping; a
  known `entry_id` tops up whichever note the index already names,
  regardless of what `due`/`status`/`subject` now read as in Outlook. This
  is a genuine, reasoned divergence from Meeting's own `ADR-019`
  mechanism, forced by Scenario 6's own AC text — full reasoning,
  including the honestly-disclosed residual risk (EntryID stability was
  not live-verified this pass — the architect had no live-Outlook
  execution capability available in this environment) and the coder's own
  assigned live-verification step: [ADR-027](ADR.md).
- **Customer classification: `app/data_access/compass_client.py::
  classify_task(subject, body, known_customers)` (new, [ADR-027](ADR.md)),
  customer-only, not a reuse of `classify_email`.** A Task has no sender
  and needs no `kind` axis (folder placement is fixed, above) —
  `classify_email`'s combined customer+kind, sender-framed prompt does not
  fit without discarding half its own output and misrepresenting an absent
  sender. `classify_task` lives alongside `classify_email` in the same
  module, one more classification prompt function, not a new client.
- **Scheduler/working-mode wiring — rides `REQ-SB-07`'s existing hourly
  job, no new job.** `email_classification.run_capture_and_record_completion`
  gains a third gated block (mirroring the existing `"meeting-capture"`
  one exactly), calling a new `todo_classification.classify_recent_todos()`
  via `run_capture_for_agent("todo-capture", ...)`. `"todo-capture"` is
  already a registered agent (`agent_registry.py`, pre-seeded ahead of this
  story); `working_mode_registry`'s existing self-healing default already
  covers it. `app/scheduling/capture_scheduler.py` requires zero code
  changes — the third pipeline in a row to ride the same opaque
  `run_capture_and_record_completion` unit. Full reasoning, including why
  `run_capture_and_record_completion` stays inside `email_classification.py`
  rather than being extracted into a dedicated orchestration module (an
  explicit fork `ADR-008` itself flagged for revisit at exactly this
  point): [ADR-027](ADR.md). **Extends `REQ-SB-11-US-01`'s honest-failure-
  funnel to a third branch, per that story's own already-established
  pattern, not a new one:** the new `"todo-capture"` gated block gets its
  own independent `try/except Exception as exc:` around its
  `run_capture_for_agent("todo-capture", ...)` call (mirroring the
  existing email/meeting branches exactly, per "Agent Activity & Error
  Observability", above) — one branch's failure this tick must never
  suppress another's success being recorded, the same reasoning that
  section already documents for the first two branches.
- **New `vault_writer.py` primitives (data_access, REQ-SB-09).** Task-note
  path resolution (via the index above, not a recompute-and-check),
  baseline-frontmatter create/top-up, and the EntryID-keyed index's own
  load/lookup/record primitives follow the existing insert-only-if-missing/
  paired-state-file-primitive contracts already established
  (Person/Customer-hub/Meeting, and `conversation_index.json`'s own
  real key→value lookup shape, respectively) — no new philosophy, two
  existing ones combined for a genuinely new load-bearing (not merely
  audit) lookup shape. Exact function names left to the decomposer/coder.

### Partner Hub Notes & Mutually-Exclusive Company Taxonomy (REQ-SB-16)

- **Partner hub note per partner:** `Work/Partners/<Partner>.md` —
  `Partners` is a `kind` folder like `Work/Customers/`, holding one
  `Partner`-type note per partner. Schema (`Implementation/Plans/
  2026-08-10-vault-taxonomy-draft.md` → "Partners"):
  `type: Partner`, `partner: <Name>`, `tags: [partner/<slug>, kind/partner]`
  — deliberately **no** `affiliate_of` key (Partner has no Affiliate
  concept) and **no** Pipeline/Agreements/Consumption-Snapshot-equivalent
  sub-entities (operator's explicit scoping — a partner relationship isn't
  a sales/Azure-consumption relationship). Body: the same living-document
  convention as the Customer hub note (auto-generated baseline stub, then
  user-added overview/contacts never programmatically rewritten again).
- **`partner/<slug>` is mutually exclusive with `customer/<slug>`.** A
  company is a Customer, a Partner, or neither, never both (operator's
  explicit choice, `MEMORY.md` 2026-08-11). `people_extraction.
  ensure_person_note` checks `find_matching_customer(company)` first
  (unchanged) and only calls the new `find_matching_partner(company)` when
  no Customer match was found — at most one of `customer_matched`/
  `partner_matched` is ever non-`None` on a given call. `find_matching_partner`
  mirrors `find_matching_customer` exactly (tag-slug comparison via
  `vault_writer.tag_slug`, against a new vault-derived
  `vault_writer.list_known_partners()` mirroring `list_known_customers()`'s
  frontmatter-scan pattern — never hardcoded).
- **New module, `app/business/partner_hub_linking.py` — a parallel sibling
  to `customer_hub_linking.py`, not an extension of it** (full reasoning:
  [ADR-009](ADR.md)). Structurally mirrors `customer_hub_linking.py`'s two
  granular primitives exactly:
  - `ensure_partner_hub_note(partner: str) -> dict` — mirrors
    `ensure_customer_hub_note`: creates the hub note if missing, tops up
    missing baseline frontmatter keys (`type`, `partner`, `tags`) if it
    already exists, never touches the body.
  - `link_note_to_partner_hub(note_path, partner: str) -> bool` — mirrors
    `link_note_to_customer_hub`: inserts a `**Partner:** [[Hub]]` inline
    body line (same `vault_writer.insert_body_line_if_missing` primitive,
    same idempotent insert-if-not-present contract), replacing the
    `**Customer:**`-labelled line the linking mechanism would otherwise
    have written for a company later reclassified as a Partner.
  - `ensure_person_note` calls these two granular primitives directly on a
    confirmed Partner match — the exact same "granular primitives only,
    never a combined unconditional-creation entry point, only after a
    confirmed match" carve-out already established for Customer (see
    "Person Notes & Email-Sender Extraction", above). No
    `ensure_hub_note_and_link`-equivalent combined function is added for
    Partner, and no per-write capture-pipeline hook is wired into
    `email_classification.py`/`meeting_classification.py` for it — the
    story's own Non-Goals scope Partner linking to the Person-note
    orchestration only, mirroring how Customer linking is reached from
    `ensure_person_note` today.
  - **New `vault_writer.py` primitives**, mirroring the Customer hub-note
    baseline family exactly but with Partner's shorter baseline-key set
    (`type`, `partner`, `tags` — no `affiliate_of`): `partner_hub_note_path`,
    `partner_hub_note_exists`, `create_partner_hub_note_baseline`,
    `ensure_partner_hub_note_baseline_frontmatter`, `build_partner_tags`
    (returns `[f"partner/{tag_slug(partner)}", "kind/partner"]`, mirroring
    `build_tags`'s shape), and `list_known_partners`.
- **One-time migration: `Work/Customers/Microsoft.md` → `Work/Partners/
  Microsoft.md`, plus a generic vault-wide retag** —
  `partner_hub_linking.migrate_customer_to_partner(customer_name: str)`
  (parameterised, not hardcoded to "Microsoft", even though Microsoft is
  the only real data today). Two steps:
  1. **Move the hub note** — `vault_writer.move_note_and_attachments`
     (already exists, used by `vault_restructure.flatten_customer_folders`)
     moves `Work/Customers/<name>.md` to `Work/Partners/<name>.md`, then its
     frontmatter is rewritten: `type: Customer` → `Partner`, `customer:
     <name>` → `partner: <name>` (the `affiliate_of` key is dropped —
     Partner has no such key), `tags` swaps `customer/<slug>` →
     `partner/<slug>` and `kind/customer` → `kind/partner`. Obsidian
     resolves `[[wikilinks]]` by filename, not full path, so existing
     `[[Microsoft]]` links elsewhere keep resolving unchanged.
  2. **Generic retag pass — matches on a union of two signals, not
     frontmatter alone.** Iterates every vault note via the existing
     `list_all_note_paths()`/`read_note()` scan (the same pattern
     `retrofit_customer_hub_links`/`retrofit_people_from_emails` already
     use). A note is in scope if **either**:
     - **Signal A (frontmatter):** its `customer` frontmatter equals
       `customer_name` — the original `ADR-009` point 4 condition, still
       correct for the hub note itself and every Email/Newsletter/
       Notification note that was actually given a `customer:` field; or
     - **Signal B (inline body wikilink, [ADR-012](ADR.md)):** its body
       contains the exact line `**Customer:** [[<hub note filename
       stem>]]`, regardless of whether `customer` frontmatter is present
       at all.

     Both signals are read from the **same** `read_note(path)` call already
     made once per note in the existing loop — no second vault scan, no
     extra file I/O. For an in-scope note the pass then: renames the
     `customer` frontmatter key to `partner` (same value; a no-op for a
     note with no `customer` key), swaps the `customer/<slug>` tag for
     `partner/<slug>` (no-op if absent), and — only where the inline
     `**Customer:** [[<name>]]` body line is present — relabels it to
     `**Partner:** [[<name>]]` (this is the only change that fires for a
     Signal-B-only note). **This is a generic scan, not a hardcoded list of
     specific notes** — live vault inspection during the original
     architecture pass found the mistagged set is larger than the story's
     own illustrative count (1 Newsletter note, 4 Notification notes also
     carry `customer: Microsoft`/`customer/microsoft`), and a second live
     inspection (`ESC-001`, during `REQ-SB-16-US-01-T04`'s pre-migration
     sanity check) found the 5 real `Work/People/*.md` Microsoft Person
     notes carry **no** `customer` frontmatter or tag at all — Person notes
     were never designed to carry one (`REQ-SB-10`'s schema only ever gives
     them a `company/<slug>` tag) — only the inline `**Customer:**
     [[Microsoft]]` wikilink Signal B now catches. Full reasoning:
     [ADR-009](ADR.md) (original generic-scan design, points 1–3/5
     unaffected and still `Accepted`) and [ADR-012](ADR.md) (the Signal-B
     extension to point 4's match predicate).
  3. **Idempotency.** Three new **generic** (not Partner-specific)
     `vault_writer.py` primitives make reruns safe: a frontmatter-key
     rename (no-op once the old key is already absent), a tags-list swap
     (no-op once the old tag is already absent), and a body-line-label
     replace (no-op once the old line is already absent) — each mirrors the
     existing insert-if-missing family's "return whether it did anything"
     contract, generalized from "insert if absent" to "replace if present."
  4. **Endpoint:** `POST /poc/migrate-customer-to-partner` (accepts a
     `customer_name` parameter) in `app/api/email_poc_router.py`, matching
     the existing one-off-migration-endpoint precedent
     (`/poc/flatten-customer-folders`, `/poc/retrofit-customer-hub-links`,
     `/poc/retrofit-people-from-emails`, `/poc/retrofit-email-sender-links`).
- **`ensure_person_note`'s return dict gains a `partner_matched` key**
  alongside the existing `company`/`customer_matched`/`linked` keys —
  additive only; existing callers reading the prior keys are unaffected.

**Explicitly not yet adopted** from the book (tracked as open questions, not
silent gaps): atomic notes (today's notes are full raw captures, not
one-idea distillations), output-oriented structure (organized around
`Customer`, an input entity, not around what gets produced from the vault),
and the AI Staging review gate for AI-generated classification (deferred by
the operator 2026-08-10 — direct-write stands until real misclassifications
justify revisiting it).

### Vault Knowledge Model Redesign — Threads, Manual Captures, OKF-Conformant Customer & Project Directories (REQ-SB-54, see [ADR-042](ADR.md))

Replaces the vault's note-per-email capture shape with a layered model: an
**evidence layer** (Thread, Meeting, manual Captures — raw, append-only,
never silently rewritten) feeding a **synthesis layer** (Customer and
Project — living documents, regenerated from current evidence). This
section defines the target data shape only — the capture pipeline that
populates Threads (`REQ-SB-55`), the Meeting↔Thread link (`REQ-SB-56`),
and the actual Glimpse/History/Background synthesis mechanism
(`REQ-SB-57`) are separate, dependent stories built on top of it. Full
architectural reasoning: [ADR-042](ADR.md).

**Evidence layer:**

- **Thread — `Work/Threads/<slug-of-conversation-id>.md`, one note per
  Outlook `ConversationID`.** `Threads` is a new, dynamically-discovered
  `kind` folder (`list_known_kinds` already scans folder names, no code
  change needed). The path is resolved **deterministically from
  `conversation_id` alone** (`vault_writer.thread_note_path`), mirroring
  `hub_note_path`/`meeting_note_path`'s existing "deterministic path from
  a stable key, no separate lookup index" precedent — deliberately NOT a
  repurposing of `conversation_index.json`/`record_conversation_note`
  (still owned by today's live `email_classification.py`, unaffected
  here; see [ADR-042](ADR.md) Alternatives). Body = `## Summary` (fully
  regenerated on every new message in the same conversation, via the new
  `replace_body_section` primitive below — never incrementally patched)
  + `## Transcript` (append-only, one dated entry per message, via the
  existing generic append primitive). `Tags` accumulate (unioned, never
  pruned) across updates — the opposite cadence from `## Summary`.
  `ConversationID` stability was verified live 2026-08-16 against the
  real Outlook installation (no false merge across 41 real multi-message
  threads) — see `REQ-SB-54-US-01`'s own `## Notes`. `ConversationID`
  under-merging (one real conversation legitimately spanning multiple
  `ConversationID`s) is explicitly out of scope here — reserved for a
  future `Conversation` note kind (`REQ-SB-60`, not yet spec'd); Thread
  stays exactly one note per `ConversationID`.
- **Meeting gains one additive, currently-empty `thread` frontmatter
  field** — reserved for `REQ-SB-56`'s own future Meeting→Thread linking,
  not populated by this pass. Ordinary additive field on the existing
  `Work/Meetings/` schema (see "Meeting Notes & Calendar-Attendee
  Extraction", above) — no new primitive, no ADR.
- **Manual Captures — a third evidence source, operator-written directly
  into a Customer/Project's own `captures.md`** (below), same tier as a
  Thread or Meeting, feeding the same synthesis. Never rewritten by any
  agent, under any circumstance — a hard invariant, structurally enforced
  by `captures.md` being a physically separate file a Glimpse/Background
  regeneration never opens (see below), not merely a respected convention.

**Synthesis layer — Customer and Project, each a small OKF v0.2-conformant
directory, not a single file:**

- **Shape, identical for both (operator-confirmed 2026-08-16 for
  Project — "Yes, Project gets the same directory shape as Customer",
  `ESCALATIONS.md` → `ESC-037`, `Resolved`):**
  ```
  Work/Customers/<customer-slug>/
    index.md        — OKF reserved: directory listing, pure
                       auto-generated bullet links + descriptions,
                       zero user-owned content — whole-file swap on
                       every directory-membership change.
    <customer-slug>.md — the OKF concept file: frontmatter (`type`,
                       OKF's one required field, plus title/
                       description/tags/status/stale_after/
                       generated/verified/sources) + a body of
                       exactly two `##`-headed sections, `## Glimpse`
                       (regenerated on every relevant evidence
                       change) and `## Background` (changes only on
                       a new DURABLE fact — see `REQ-SB-54` point 5).
    log.md           — OKF reserved: History. Date-headed prose,
                       append-only.
    captures.md       — NOT an OKF-reserved name, same
                       isolate-append-only-content-into-its-own-file
                       principle, extended.
  Work/Customers/<customer-slug>/projects/<project-slug>/ — identical
    four-file shape, nested one level inside its own Customer's
    directory.
  ```
  `Work/Customers/` remains the existing `kind` folder — this changes
  what lives *inside* an already-established kind folder (directories
  instead of flat files), it does not introduce a new kind-folder
  concept. **This does not reopen [ADR-004](ADR.md)** ("Customer is a tag,
  never a folder level") — that rule governs real, multidimensional
  content notes (Emails/Files/Notifications, now Threads/Meetings), which
  stay flat and cross-link via `customer:`/`project:` frontmatter + tags +
  an OKF `sources:` entry only, exactly as before. This extends the
  separate, already-established carve-out (first used for the single-file
  Customer hub note, `REQ-SB-14`) that a `kind` folder may hold the
  hub/synthesis entities of that kind themselves — now one level deeper
  for Project nested inside Customer, by explicit operator confirmation.
- **New `vault_writer.py` primitive family** (mirrors the existing
  hub-note-baseline shape — path-resolution / exists-check /
  create-baseline / top-up-if-partial — applied to a 4-file directory
  instead of 1 file), shared by Customer and Project, not two parallel
  implementations:
  - Directory path resolution + baseline creation/top-up for the 4-file
    shape above.
  - **`replace_body_section(path, header, new_content)` (new, general
    purpose — not Customer/Project-only).** Locates the `header` line
    (e.g. `"## Glimpse"`) and the next `##`-level header (or EOF),
    replaces everything strictly between them, leaves everything outside
    that bounded region byte-for-byte untouched regardless of how many
    times the file has already been edited. This is the canonical
    mechanism for **every** full-regeneration write this requirement
    introduces (a concept file's `## Glimpse`/`## Background`; a Thread's
    own `## Summary`, above) — it replaces `insert_body_line_if_missing`'s
    fixed-byte-offset mechanism, an already-documented fragility for a
    note touched many times over its life (`MEMORY.md`, `BUG-003`/
    `ESC-003`, `Open`) that repeated Glimpse regeneration would otherwise
    lean directly on.
  - `log.md`/`captures.md` appends reuse the existing generic
    unconditional-append primitive (`append_person_note_update_line` —
    already fully generic over `path`/`line` despite its Person-era name;
    may be renamed by the coder to reflect its now-multi-purpose role, no
    new append primitive is needed).
  - **`generated`/`verified` (OKF's nested actor-provenance fields, e.g.
    `generated: {by: <agent-id>, at: <timestamp>}`) are written as
    JSON-encoded STRINGS under their own literal field names** — the
    existing `_format_frontmatter_value`/`_parse_frontmatter_value` pair
    round-trips a string or a list-of-strings only; a native dict write
    silently corrupts on read. This extends, rather than duplicates, the
    already-`Accepted` list-of-dicts workaround already shipped twice
    (Meeting `attendees`, [ADR-036](ADR.md) point 7; Email `recipients`,
    2026-08-14) to a single-dict value.
- **Correction (`BUGFIX-06-US-01`, 2026-08-19):** the "already shipped
  twice" claim in the bullet immediately above is only accurate for Email
  `recipients`. Meeting `attendees` is, and has always actually been,
  written as a plain `list[str]` of wikilinks, not the JSON-encoded
  `list[dict]` string shape — direct reading of `meeting_classification.
  py`'s real write path found the earlier claim never matched shipped
  behaviour. See "Meeting & Inbox Cockpits" → `people.py` extended bullet,
  above, for the corrected read-side mechanism and the fix this enabled.
- **Correction (`BUGFIX-07-US-01`, 2026-08-19, `BUG-028`):**
  `create_okf_directory_baseline`/`ensure_okf_directory_baseline` wrote
  `log.md`/`captures.md` as a bare empty string on first creation, and
  never retrofitted a header onto an already-existing headerless file —
  every Customer's/Project's `log.md`/`captures.md` opened completely
  anonymous in Obsidian's own tab bar/quick switcher/file explorer (all
  identically named, no content identifying which Customer/Project they
  belong to). Fixed by extending the SAME shared primitive both functions
  already are (no fork, no Customer-only/Project-only patch):
  - Both functions gain a new explicit `identifying_name: str` parameter
    (the real display name, e.g. `customer`/`project` — the same value
    already passed into `index_listing_body`) — a new parameter, not a
    parse of `index_listing_body`'s own first line, since every one of
    the four Customer/Project wrapper functions already has the display
    name in local scope and string-parsing an unrelated parameter back
    apart is needless fragility for zero benefit.
  - One shared helper writes `# {identifying_name}\n\n` as `log.md`'s/
    `captures.md`'s header — the bare `# {name}` HALF of `index.md`'s own
    already-`Accepted` header convention only, deliberately without its
    trailing wikilink-listing line (`index.md`-specific, not applicable)
    and without a `— Log`/`— Captures` differentiating suffix (`BUG-028`'s
    own complaint is "no place to see the customer name" across
    identically-named tabs from DIFFERENT Customers/Projects — Obsidian's
    own tab title already differentiates `log.md` from `captures.md`
    WITHIN one Customer/Project, so no further differentiation is needed
    or asked for).
  - The SAME helper both creates the header fresh (`create_okf_directory_
    baseline`, file did not exist) and backfills it onto an
    already-existing file (`ensure_okf_directory_baseline`) — one
    generic-primitive-first mechanism for both Scenario 1 and Scenario 2,
    not two. "Headerless" is detected as: the file's CURRENT first line
    does not start with `# `. Confirmed safe against every real line any
    current caller has ever written to these files — `append_person_note_
    update_line`'s three real call sites (`project_customer_synthesizer.
    py`'s date-headed History lines, e.g. `"2026-08-19 — Project ... status
    changed to ..."`; `person_note_proposals.py`'s/`skill_tools.py`'s
    `"- <instruction>"` bullets) — none begin with `# `, so an
    already-appended real file is detected as headerless and gets the
    header PREPENDED, every existing byte preserved unchanged afterward.
    An already-headered file (a second `ensure_*` run, post-fix) is
    correctly detected as NOT headerless and left untouched — idempotent.
  - This is a content-only change to `log.md`/`captures.md`'s OWN
    creation/top-up logic — a different code path from `<slug>.md`'s
    Glimpse/Background regeneration entirely. `ADR-042` Decision point 1's
    actual guarantee (a `<slug>.md` full-file regeneration can never reach
    `captures.md`, by construction) is unchanged and unreachable by this
    fix. `create_okf_directory_baseline`'s own docstring sentence
    "`captures.md` is never opened by this function beyond that one
    existence check" becomes stale wording once this ships (the function
    now reads/writes `captures.md`'s own content for the header) — a
    docstring-precision correction for the coder to make in-scope, not an
    architectural reopening; the guarantee the sentence was protecting
    (isolation from `<slug>.md` regeneration) still holds exactly as
    `ADR-042` decided.
  - **No new ADR** — reuses the already-`Accepted` `# {name}` header
    convention verbatim (invents nothing new), does not change the 4-file
    directory shape, does not touch `ADR-004`'s folder/tag boundary, and
    does not weaken or reach through `ADR-042`'s captures.md-isolation
    guarantee. A new parameter plus one small shared helper on an
    already-shared primitive is mechanical composition, not a new
    tool/framework/structural-boundary decision.
- **Structural (not conventional) update-ownership boundary.** Physically
  separating `captures.md`/`log.md` from `<slug>.md` means a full-file
  open-and-regenerate of the concept file (Glimpse/Background) **cannot**
  reach either of them, by construction — this upgrades `REQ-SB-54` point
  7's single-owner rule from a discipline to a structural guarantee for
  the Captures axis specifically. The Glimpse/History "exactly one
  synthesizer" half of that rule is still convention-only (caller
  discipline, no enforcement code yet) — the actual regeneration-trigger
  mechanism is `REQ-SB-57`'s own scope, not built here.
- **`customer_hub_linking.py` is substantially restructured, not merely
  extended**, by this shape change — its single-file
  `ensure_customer_hub_note`/`create_customer_hub_note_baseline` contract
  no longer matches the new directory shape. `email_classification.py`'s
  existing live call site (`ensure_hub_note_and_link`) is a real,
  currently-running caller — whatever replaces the single-file functions
  must either preserve that call's existing signature/behavior for the
  transition period, or the cutover must become an explicit task
  dependency; this is a real, load-bearing consequence
  ([ADR-042](ADR.md)), not an incidental side effect.
- **Flagged consequence, not yet resolved by this pass:**
  `list_all_note_paths()`'s current one-level `Work/*/*.md` glob cannot
  discover the new two-levels-deep directory shape
  (`Work/Customers/<slug>/<slug>.md`,
  `Work/Customers/<slug>/projects/<slug>/<slug>.md`) — without an explicit
  recursion extension (or an equivalent), every OKF concept file is
  structurally invisible to `list_known_customers()`, `vault_indexing`,
  and search. Whoever picks up `T04`/`T05` must turn this into an
  explicit task, not discover it live.
- **`REQ-SB-55`/`REQ-SB-56`/`REQ-SB-57` inherit this data model as
  settled** — they call the primitives established here rather than
  re-deriving path-resolution or write-primitive shape themselves.

### Meeting → Thread Linking — ConversationID Primary Strategy, Attendee-Overlap/Date-Proximity Fallback (REQ-SB-56, extends [ADR-042](ADR.md), no new ADR)

Adds a `Link-to-Thread` Job onto the existing, unmodified `meeting-capture`
Worker (`app/business/meeting_classification.py::classify_recent_meetings`),
populating the currently-empty, already-reserved Meeting `thread`
frontmatter field (`REQ-SB-54-US-01`/T03) once a real Thread match is
found. Two strategies, tried in priority order — the second only applies
when the first structurally cannot (no shared `conversation_id`):

1. **Primary — `conversation_id` match.** `app/data_access/outlook_com.py::
   list_calendar_events` does not read `ConversationID` off the underlying
   `AppointmentItem` COM object today (confirmed by direct reading) — this
   is a **code gap, not a data gap**: a live, read-only sample of 100 real
   calendar items on this Outlook installation (2026-08-16, see
   `REVIEW-QUEUE.md` → `REQ-SB-56-US-01`) found `ConversationID` non-empty
   on 100/100. The primary strategy's own task adds
   `"conversation_id": getattr(item, "ConversationID", None) or ""` to the
   returned dict, mirroring `list_recent_mail`'s existing field exactly,
   then joins against `vault_writer.thread_note_path(conversation_id)` —
   free, no separate matching logic, identical to every other
   `conversation_id` join in this batch.
2. **Fallback — attendee-overlap + date-range-proximity heuristic**, for
   meetings created directly (no shared `conversation_id` with any
   Thread). **Architect proposal (2026-08-16), concrete and buildable,
   recorded as a PROPOSAL awaiting operator confirmation in
   `REQ-SB-56-US-01`'s own `## Notes` — not yet final:**
   - **Attendee sets, both self-excluded.** Compares the meeting's own
     attendee list (`outlook_com._resolve_attendees`, already
     `{"name","email"}` pairs, organizer/resource types already excluded)
     against the candidate Thread's own accumulated participant set — a
     NEW, purely additive Thread frontmatter field, `participants:
     list[str]` (lower-cased email addresses, unioned/accumulated across
     every message the Thread's own `Thread-Match/Merge` Job processes,
     mirroring the already-`Accepted` Tags-accumulate cadence exactly —
     an ordinary flat list-of-strings, no JSON-string round-trip
     workaround needed, unlike `generated`/`verified`). **Ownership
     resolved 2026-08-16, by the `REQ-SB-55` architect pass ([ADR-043](ADR.md)):
     `Thread-Match/Merge` (now real, see "Email Capture & Threading
     Pipeline", above) is the writer of both fields — the flagged
     either-ordering decision below no longer applies.** Both sets exclude
     the vault owner's own `settings.self_email` before comparison,
     mirroring `meeting_classification._exclude_self` exactly — without
     this, the operator's own presence on virtually every captured
     meeting and thread would trivially inflate every candidate pair's
     overlap count.
   - **Overlap bar (deliberately conservative — false-positive links are
     worse than no link, this story's own Constraint):** clears if EITHER
     (a) **≥2 shared attendees** (raw count) — a single shared external
     contact alone is not sufficient signal, since one recurring
     point-of-contact will legitimately appear across MANY unrelated
     meetings/threads for the same account, not just the one that's
     actually related; OR (b) **exactly 1 shared attendee AND that
     attendee is the entirety of the smaller of the two sets**
     (`min(|meeting attendees|, |thread participants|) == 1`) — covers
     the common genuine 1:1-call-matches-1:1-thread case without
     weakening the ≥2 bar for any larger meeting/thread.
   - **Date-range-proximity bar:** the meeting's own `start` timestamp
     must fall within **7 calendar days (inclusive, either direction)**
     of the candidate Thread's own most-recently-captured-message
     timestamp — a second NEW, additive Thread frontmatter field,
     `last_message_at` (ISO-8601 string, overwritten — not accumulated —
     on every Thread update). Grounded in this vault's own real observed
     thread cadence, not an arbitrary round number: the live
     `ConversationID` verification (`REQ-SB-54-US-01`'s own `## Notes`)
     found a real, genuinely-threaded 3-message conversation ("G42/Data
     Lake RFP Discussion") spanning exactly 7 days end-to-end
     (2026-08-07 to 2026-08-14) — reusing that same order of magnitude as
     the meeting-to-thread proximity window keeps the fallback's temporal
     bar consistent with this vault's own observed "still the same live
     topic" cadence: tight enough to reject a same-contact-but-months-stale
     Thread, loose enough to survive ordinary invite-scheduling lag.
   - **Both bars must clear (AND)** for the fallback to fire; either bar
     failing leaves the meeting explicitly unlinked (Scenario 3) — never
     a forced link to the closest-but-still-weak match.
   - **Tie-break, multiple qualifying Threads:** prefer the higher
     attendee-overlap COUNT; if still tied, prefer the smaller
     date-proximity gap; if still tied on both axes, leave the meeting
     unlinked rather than arbitrarily choose one — an unresolved tie is
     itself weak evidence, the same false-positive-conservative reasoning
     as the bars themselves.
   - **`participants`/`last_message_at` are a purely additive extension
     of the already-`Accepted` Thread shape** (`ADR-042` point 5,
     `REQ-SB-54-US-01`/T02's own `_THREAD_NOTE_BASELINE_KEYS`) — both are
     ordinary scalar/list-of-string values `_format_frontmatter_value`
     already round-trips natively; neither introduces a new primitive,
     and neither reopens `ADR-042` or any of `T02`'s own locked ACs
     (its baseline key set was never closed/exhaustive). **Ownership
     RESOLVED 2026-08-16 by the `REQ-SB-55` architect pass ([ADR-043](ADR.md)):**
     `REQ-SB-55`'s own `Thread-Match/Merge` Job (now real, see "Email
     Capture & Threading Pipeline", above) is the writer of both fields —
     `REQ-SB-56`'s own `Link-to-Thread` Job task reads them, it does not
     originate them. This closes the either-ordering decision previously
     left open here; `REQ-SB-56`'s decomposer pass should record a
     `depends_on` edge onto `REQ-SB-55`'s `Thread-Match/Merge` task rather
     than re-deciding this.

Once linked, the Meeting feeds the same Project Glimpse its linked Thread
feeds (`REQ-SB-57`, below) — this story only produces the link.

### Project & Customer Synthesizer — the "genuinely concludes" History-line bar (REQ-SB-57, extends [ADR-042](ADR.md), no new ADR)

Defines the concrete trigger the Project/Customer Synthesizer Job(s) use
to decide when a `log.md` line is warranted versus routine Glimpse-only
activity (`REQ-SB-54` point 5, `REQ-SB-57`'s own Scenario 2/4). **Architect
proposal (2026-08-16), concrete and buildable, recorded as a PROPOSAL
awaiting operator confirmation in `REQ-SB-57-US-01`'s own `## Notes` — not
yet final:**

- **Project concept-file `status` enum** — the first concrete value set
  defined for OKF's already-`Accepted`, previously-unconstrained generic
  `status` field (`ADR-042` point 1): **`active | on_hold | won | lost |
  renewed`**. `active` is the default/ongoing value; `on_hold` is an
  explicit pause, not a conclusion.
- **History-line trigger:** on every Synthesizer run, compare the
  Project's `status` value as read at the START of this pass (its prior,
  on-disk value — a full read always precedes a full rewrite, per the
  "regenerate, don't patch" convention) against the value active DURING
  this pass. Append a dated `log.md` line **iff that value differs from
  the previous pass's own observed value AND the new value is one of
  `won` / `lost` / `renewed`** — never on `active`/`on_hold`, and never on
  a re-observation of an already-terminal value (idempotent: a Project
  that stays `won` across many later re-syntheses — e.g. a linked Thread
  still receiving replies — never re-appends). This directly
  operationalizes the operator's own two named conclusion examples
  (`REQ-SB-54` point 5: "a Project closes, a renewal lands") — `won`/
  `lost` together cover "closes" (a defensible pairing: a loss is exactly
  as much a genuine conclusion as a win, and routine-noise-vs-conclusion
  is about FINALITY, not favorability), `renewed` is the operator's own
  second named case verbatim.
- **Customer rollup rule:** the Customer's own Glimpse "active Project"
  rollup (`REQ-SB-57` Scenario 5) lists every Project whose `status` ∈
  `{active, on_hold}`; a Project's transition into `{won, lost, renewed}`
  both appends the Customer's own `log.md` line and drops that Project
  from the rollup, in the SAME synthesis pass (Scenario 2) — the Customer
  Synthesizer is TRIGGERED BY (never independently deciding) the
  Project's own status change, per the ownership rule (`REQ-SB-54` point
  7).
- **Who writes `status`:** the operator, directly in the Project's own
  frontmatter in Obsidian — the same "Obsidian is the authoring surface"
  convention already established for narrative body content
  (`REQ-SB-54-US-01`'s own `## Notes`). The Synthesizer only READS and
  reacts to it; it does not itself infer a conclusion from evidence text
  (a materially larger, unscoped NLP-classification problem this story's
  own scope does not include — automatically inferring `status` is a
  plausible FUTURE extension, not proposed here).

## Vault Migration — One-Time Full Vault Migration to the New Knowledge Model (REQ-SB-59, see [ADR-047](ADR.md))

A one-time, operator-triggered backfill: wipes the legacy per-email
`Work/Emails/` notes and their now-dead-code cross-link stores, re-runs
capture over Outlook history through the already-`Done` `REQ-SB-55`/
`REQ-SB-56` pipelines, and regenerates every Customer note onto the new
OKF shape (`ADR-042`) while preserving durable pre-migration content. Full
architectural reasoning, every alternative considered, and every
consequence: [ADR-047](ADR.md).

- **New module — `app/business/vault_migration.py`, the fifth instance of
  this codebase's existing one-off-migration-module shape**
  (`tag_backfill.py`, `vault_restructure.py`,
  `partner_hub_linking.migrate_customer_to_partner`) — three public
  functions, one per the story's own T01/T02/T03 split, each exposed as
  its own new flat `POST /poc/<verb>` endpoint in `email_poc_router.py`
  (matching `/poc/backfill-tags`/`/poc/flatten-customer-folders`'s own
  existing naming convention, operator-triggered, no scheduler wiring, no
  UI):
  - `wipe_legacy_email_notes() -> dict`
  - `recapture_outlook_history(email_limit: int, meeting_days_back: int) -> dict`
  - `regenerate_customer_notes() -> dict`
- **`.second-brain/migration_backup/<UTC-run-timestamp>/` — this
  project's first archive-not-delete ("soft delete") location.** Every
  Note this migration removes from `Work/` is moved, never
  `Path.unlink()`-deleted, via the EXISTING, unmodified
  `vault_writer.move_note_and_attachments(note_path, target_dir)`
  primitive (`target_dir` pointed under this new archive root instead of
  another `Work/` location — the primitive itself already accepts any
  `Path`, no code change) — preserving each note and its own sibling
  `attachments/<slug>/` folder byte-for-byte, just relocated. This is what
  makes every function below naturally idempotent (a rerun finds nothing
  left to move, mirroring `vault_restructure.py`'s own existing
  idempotency framing) while giving the operator a real, inspectable,
  restorable safety net with zero new backup mechanism invented. Any
  FUTURE similarly destructive one-off migration should reuse this same
  location/shape rather than inventing a second archive convention.
- **`wipe_legacy_email_notes()` (T01):**
  1. Moves every note currently under `Work/Emails/` into
     `.second-brain/migration_backup/<run-timestamp>/Emails/` via
     `move_note_and_attachments`, then `vault_writer.remove_empty_dirs`
     on the now-empty `Work/Emails/` (mirrors `vault_restructure.py`'s own
     cleanup step; non-blocking — Scenario 1 only requires zero notes, not
     folder removal).
  2. **Archives, never deletes, the two now-stale `.second-brain/` stores
     this migration's "stale cross-links...cleaned up" language refers
     to**, via a plain `Path.rename` inside `vault_migration.py` itself
     (direct `pathlib` use for non-Note filesystem bookkeeping, mirroring
     `vault_restructure.py`'s own precedent of touching
     `settings.vault_path` directly for mechanical operations, rather than
     inventing new `vault_writer` primitives for a one-time move of
     already-owned files):
     - `processed_email_ids.json` — **load-bearing, not merely tidy.**
       Outlook `EntryID`s are stable across a same-mailbox rerun; leaving
       this file in place would make `run_email_capture_pipeline`'s own
       existing `email["id"] in already_processed` check (unchanged,
       `ADR-043` point 2) silently skip every real historical email as
       "already processed," making `recapture_outlook_history()` below a
       silent no-op. Moving the file out of its canonical path lets
       `vault_writer.load_processed_email_ids()`'s own existing
       `if not path.exists(): return set()` branch transparently take
       over — **zero new `vault_writer` code needed for the reset
       itself.**
     - `conversation_index.json` — the retired
       `record_conversation_note`/`find_related_note_stems`/`## Related
       Emails` mechanism this same architecture file's own "Vault
       Knowledge Model Redesign" section above already flagged as dead
       code for the email path post-`ADR-046`; archived for the same
       "stale, not silently left dangling" reason, never read by the new
       pipeline either way.
  3. **Never touches `Work/Meetings/`.** Scenario 5 ("Meeting notes and
     their own stale cross-links are also cleaned up") needs no wipe at
     all — `meeting_classification.mark_meeting_processed`/
     `processed_meeting_ids.json` is already a non-gating, top-up-only
     audit trail (confirmed by that function's own docstring), so
     `recapture_outlook_history()`'s own wide-window
     `classify_recent_meetings` call (below) naturally re-visits and tops
     up every pre-migration Meeting note in place, and — since
     `REQ-SB-56`'s `Link-to-Thread` Job already runs unconditionally
     inside that same existing call — also naturally re-links every
     historical Meeting to its now-recaptured Thread, with zero code
     change.
- **`recapture_outlook_history(email_limit, meeting_days_back)` (T02):**
  reuses existing, already-parametrized read functions with an
  operator-supplied large history-window value — **no new Outlook-COM
  primitive.** Both parameters are required call-site inputs, never a
  hardcoded magic number inside this function's own body (this project's
  standing "config, not constants" convention):
  1. `email_pull.pull_and_stage_emails(limit=email_limit)` once — since
     `outlook_com.list_recent_mail` iterates its own `Items` collection
     until EITHER `limit` items are collected OR the collection is
     exhausted, an `email_limit` set at/above the mailbox's real Inbox
     item count fetches its full history in this one call.
  2. `email_capture_pipeline.run_email_capture_pipeline()` once — this
     function's own current body already loops over EVERY currently
     staged, not-yet-processed email in a single call (its own `limit`
     parameter is retained only for call-site backward compatibility,
     per its own docstring), so one call drains everything T02 just
     staged.
  3. `meeting_classification.classify_recent_meetings(days_back=
     meeting_days_back, days_ahead=14, limit=<a matching large value>)`
     once — `list_calendar_events` applies a real COM `Restrict()` date
     filter on `days_back`, so this genuinely reaches full calendar
     history, not merely a large item cap.
  - **Inherited scope boundary, not a new limitation:** both underlying
    Outlook reads are scoped to the default Inbox/Calendar folders only
    (unchanged, pre-existing behavior) — this migration does not reach
    into Sent Items or any other mailbox folder; "Outlook history" here
    means the same scope the live hourly capture already reads from.
- **`regenerate_customer_notes()` (T03) — also resolves `ESC-046` as a
  direct, in-scope consequence, not a separately deferred bugfix:**
  1. Enumerates every note `vault_writer.list_all_note_paths()` already
     returns whose `frontmatter.get("type") == "Customer"` AND whose
     `path.parent.name == "Customers"` (a flat file directly under
     `Work/Customers/`, never a `<slug>/<slug>.md` OKF concept file, whose
     own parent directory is the slug, not `"Customers"`) — a generic,
     vault-wide scan mirroring `partner_hub_linking.
     migrate_customer_to_partner`'s own established "never a hardcoded
     name list" precedent, so it correctly covers however many real
     legacy flat Customer notes exist at run time (`ESC-046` found 14
     colliding, of 17 migrated Customers, on 2026-08-18 — not assumed
     fixed at that count).
  2. For each: `customer_hub_linking.ensure_customer_hub_note(customer)`
     guarantees its OKF directory exists (a no-op for an already-migrated
     Customer; creates the directory from scratch for one that only ever
     had the old flat shape).
  3. Reads the flat note's full body (`vault_writer.read_note`), then
     calls the SAME, unmodified, already-`Accepted`
     `project_customer_synthesizer.synthesize_customer(customer,
     evidence_text=<flat note body>)` the ongoing Synthesizer itself uses
     going forward (`REQ-SB-57`) — never a migration-only bypass. This
     both regenerates `## Glimpse` from current evidence (a harmless,
     idempotent re-regeneration) and, via that function's own internal
     `compass_client.detect_customer_durable_fact` call, proposes a
     normal `propose_background_amendment` Pending Approval for any
     durable fact the legacy note's body contains that isn't already
     reflected in the new OKF `## Background` — the exact same
     human-reviewed gate every other Background amendment already goes
     through.
  4. Archives the flat file itself via `move_note_and_attachments` into
     `.second-brain/migration_backup/<run-timestamp>/Customers/` — the
     same reused primitive T01 uses. **This step is what removes the
     filename-stem collision from `vault_indexing.rebuild_index()`'s
     index (`ADR-024`):** once the flat file no longer exists anywhere
     under `Work/`, only the OKF concept file remains at that stem, so
     `get_index()[stem]` can no longer silently resolve to the wrong
     file — closing `ESC-046` directly, per that escalation's own
     recorded option (a) ("a one-time cleanup pass deleting/archiving
     each stale legacy flat Customer hub note once its OKF directory
     concept file exists").
  - **Out of scope, no evidence either currently exists:** the Partner
    namespace (never migrated to an OKF directory by design, `ADR-009`)
    and any legacy flat Project-kind note (no such file is known to
    exist) — if the coder discovers either during implementation, that is
    a scope-internal finding to log, not something pre-decided here.
- **Pending Approvals `regenerate_customer_notes()` produces are
  explicitly NOT part of this story's own Definition of Done** — resolving
  them is ordinary, ongoing operator review through the existing Pending
  Approvals surface (unmodified), decoupled from "migration complete." The
  migration's own job is to surface every real durable fact for review,
  never to force approval before the story can close.
- **No new "already ran" state marker anywhere** — every function above is
  naturally idempotent through the same "nothing left to act on" mechanism
  its sibling migration modules already rely on (see `.second-brain/
  migration_backup/` above and `ADR-047`'s own Alternatives Considered).

## Vault Base Provisioning + Redesigned Email/Meeting Capture — Raw/Distilled Evidence Split, Section-Ownership Enforcement, Files/OKF Companions, People Nested Under Customer (`REQ-SB-70`, `REQ-SB-71`, see [ADR-048](ADR.md))

One coherent redesign, worked out turn-by-turn with the operator in a
dedicated vault-structure conversation immediately after `REQ-SB-59`'s own
migration was paused mid-run over a live reliability concern. Four stories
implement it (`REQ-SB-70-US-01`, `REQ-SB-71-US-01/-02/-03`); this section
covers all four together, matching how they were designed. Full
architectural reasoning, every alternative considered, and every
consequence: [ADR-048](ADR.md).

### Superseded vs. unchanged — read this first

- **Superseded, going forward:** the single-file Thread shape described
  under "Vault Knowledge Model Redesign" above (`ADR-042` point 5) and its
  own human-readable/renamable-filename mechanism described under
  "Decoupled Email Pull + Human-Readable, Graph-Connected Thread Notes"
  above (`ADR-046` Decisions 6/7/9/10, Thread-specific parts only). Those
  sections stay as an accurate historical record of what shipped and
  remains true for already-captured Thread notes (no backfill is built by
  this redesign); this section describes what NEW capture produces going
  forward.
- **Unchanged, still exactly as described above:** the Customer/Project
  OKF 4-file directory family (`ADR-042` points 1-4), `replace_body_
  section`'s own core region-location mechanism (`ADR-042` point 2, now
  gated — see below, but the header/next-header logic itself is untouched),
  the Project & Customer Synthesizer's own "genuinely concludes" bar
  (`REQ-SB-57`), Meeting→Thread Linking's own conversation_id-primary /
  attendee-overlap-fallback strategy (`REQ-SB-56`, still the mechanism
  `_link_to_thread_by_conversation_id`/`_link_to_thread_by_fallback_
  heuristic` use — only the shape of what they read/write changes, per
  below), and every scheduled trigger (`pull_email`, `process_staged_
  email`, `meeting-capture`) — same capability ids, same cadence, zero new
  `agent_schedule_registry` entries anywhere in this redesign.

### Vault Base Provisioning (`REQ-SB-70-US-01`)

New `app/business/vault_provisioning.py` — mirrors `vault_migration.py`'s
own module shape but is explicitly NOT a migration (no archive, no wipe,
no re-run over Outlook history): one function, `provision_vault_base()
-> dict`, idempotent `mkdir(parents=True, exist_ok=True)` for exactly
`Work/Customers/`, `Work/Threads/`, `Work/Meetings/`, `Work/Resources/`,
`Work/Archive/{Opportunities,Customers,Resources}/` — mirroring
`_write_frontmatter_note`'s/`write_attachments`'s own already-proven
idempotent-mkdir convention. Creates nothing else — no individual Customer
OKF directory, no `Work/Opportunities/`, `Work/Websites/`, `Work/Notes/`.
Exposed as `POST /poc/provision-vault-base` in the existing `app/api/
email_poc_router.py` (already this codebase's general home for flat,
operator-triggered one-off `/poc/*` operations regardless of subject
area — a new sibling router would fragment an already-established
convention for no gain).

### Section-Ownership Enforcement (`REQ-SB-71-US-01`)

New, composed-alongside `app/data_access/section_ownership.py` (data_access
layer — `ADR-003`'s layer boundary means `replace_body_section` itself,
which performs this check, cannot depend on `app/business`). Two
independent, structural rules:

1. **`_HUMAN_OWNED_HEADERS: frozenset[str] = frozenset({"## Personal
   Notes", "## Actions"})`** — checked FIRST and unconditionally in
   `is_header_allowed(caller, header)`, never overridable by any caller's
   own registered allow-list. Header text alone is the key, vault-wide —
   both headers carry the identical human-owned meaning on a Thread, a
   Meeting, a File companion, or any future note kind that reuses either
   name.
2. **`_CALLER_ALLOW_LISTS: dict[str, frozenset[str]]`** — deny-by-default
   per-caller registry, granularity = the calling FUNCTION
   (`module.function`), not the calling module (least-privilege). Current
   registrations:
   | Caller | Allowed headers |
   |---|---|
   | `email_classification.thread_match_merge` (retired once `synthesize_thread` ships — dead entry, see below) | `## Summary`, `## Related` |
   | `email_classification.synthesize_thread` (new, `REQ-SB-71-US-02`) | `## Summary`, `## Related` |
   | `thread_summary_backfill.backfill_thread_summaries` | `## Summary` |
   | `project_customer_synthesizer.synthesize_project` | `## Glimpse` |
   | `project_customer_synthesizer.synthesize_customer` | `## Glimpse` |
   | `project_customer_synthesizer.finalize_background_amendment_proposal` | `## Background` |
   | `meeting_classification.classify_recent_meetings` (new, `REQ-SB-71-US-03`) | `## Summary` |
   | `email_classification.write_file_companion` (new, `REQ-SB-71-US-02`, exact module left to the coder) | `## Summary` |

`vault_writer.replace_body_section(path, header, new_content, *, caller:
str)` — `caller` is a REQUIRED keyword-only parameter (a deliberate
breaking-signature change: every call site, present and future, must
explicitly declare identity; there is no default). Raises `section_
ownership.SectionWriteNotAllowed` (a `PermissionError` subclass) when
`caller` may not write `header` — a real, observable, honest failure,
never a silent no-op indistinguishable from this same function's own
separate, unchanged "header not found in THIS file" contract (still
returns `False` for that case only). `read_body_section`/`append_body_
section_line`/`replace_body_opening_line`/`insert_body_line_if_missing`
are all UNCHANGED — scope is exactly `replace_body_section`.

### Email Capture Redesign — Thread Raw/Distilled Split, Stage 1/Stage 2 (`REQ-SB-71-US-02`)

- **Thread directory shape — `Work/Threads/<slug-of-conversation_id>/`,
  permanently deterministic from `conversation_id` alone** (reverts to
  `ADR-042` point 5's ORIGINAL scheme, superseding `ADR-046`'s own
  human-readable/renamable-filename mechanism — no longer needed once the
  human-readable identity lives in the concept file's `thread_name`
  frontmatter rather than the directory/file name itself):
  ```
  Work/Threads/<conversation-id-slug>/
    <conversation-id-slug>.md   — distilled concept file
    messages/
      <received[:10]>-<hash8(message_id)>.md   — raw, immutable, write-once
  ```
  `thread_directory_paths(conversation_id) -> dict` (`{"directory",
  "concept", "messages"}`) is the new deterministic path-resolution
  primitive — mirrors `okf_directory_paths`' own shape but WITHOUT
  `index.md`/`log.md`/`captures.md` (a genuinely different, simpler
  2-part convention; `ADR-042` point 1's own "Customer and Project are
  the ONLY two 4-file-OKF-shaped kinds" scope-lock is not reopened).
- **Distilled concept file body:** `## Summary` (agent-owned, regenerated)
  + `## Personal Notes` (human-owned) + `## Actions` (human-owned, a
  literal checklist — never backed by `todo_classification` in either
  direction) + `## Related` (agent-owned, regenerated, unchanged mechanism
  from `ADR-046` Decision 9). `## Transcript` is RETIRED — superseded by
  the `messages/` directory itself.
- **Raw message note** — `raw_message_note_path`/`raw_message_note_
  exists`/`create_raw_message_note` (new `vault_writer` primitives); the
  caller MUST check `raw_message_note_exists()` first and never write the
  same `message_id` twice.
- **Stage 1 — zero Compass calls, reuses `email_pull.pull_and_stage_
  emails`/`email_staging` verbatim as its raw-fetch substrate.** New `app/
  business/pipelines/raw_message_capture.py` (sibling to `email_capture_
  pipeline.py`/`email_pull.py`), owning `capture_raw_thread_messages(limit:
  int = 10) -> dict`: calls `pull_and_stage_emails` (joins `agent_schedule_
  registry.get_shared_dispatch_lock()`, the SAME lock `pull_email` already
  joins — concurrency-safety reuse, never a new schedule entry), then
  drains every staged-but-not-yet-message-noted email: `create_raw_
  message_note` (write-once) + ensures the Thread's own distilled note
  exists (`create_thread_note_baseline` if `thread_directory_paths(...)
  ["concept"]` doesn't exist yet), then `email_staging.remove_staged_
  email`. Zero `compass_client` import anywhere in this module. Exposed as
  `POST /poc/capture-raw-thread-messages` — a new, independent capability
  id (`capture_raw_thread_messages`) of the EXISTING `"email-capture-
  pipeline"` Agent-tier identity — no new Agent, no new Map node.
- **Stage 2 — the real Compass-backed judgment, no shared lock with Stage
  1.** `email_classification.synthesize_thread(conversation_id: str) ->
  dict` replaces `thread_match_merge`'s own prior role: reads EVERY raw
  message currently under that Thread's own `messages/` directory (full
  reconstruction on every call, never a rolling/incremental delta — a
  deliberate reversal of `REQ-SB-67`'s own rolling-synthesis design, now
  that full raw content is durably, cheaply re-readable), calls
  `classify_email` ONCE against the FIRST raw message's own body (customer/
  kind — preserves the existing "decided once, on the first message, never
  contradicted later" Constraint), does the real merge-vs-new-Thread
  judgment, and regenerates `## Summary` + `## Related` via the
  allow-list-checked `replace_body_section(..., caller="email_
  classification.synthesize_thread")`. `route_to_project`'s own existing
  Pending-Approval shape (`ADR-043` point 4) is preserved, now triggered
  from `synthesize_thread`'s own end. Exposed as `POST /poc/synthesize-
  thread?conversation_id=<id>` — a second new, independent capability id
  (`synthesize_thread`) of the SAME Agent-tier identity, sharing no lock
  with `capture_raw_thread_messages` (Scenario 5's own proof obligation).
- **The EXISTING scheduled `pull_email`/`process_staged_email` capability
  ids stay wired exactly as-is — their own underlying implementation was
  INTENDED to compose the two functions above in sequence.** ⚠
  **Correction (`BUGFIX-05-US-01` architect pass, 2026-08-19): this was
  this batch's own stated INTENT, not yet the real live wiring — direct
  code reading during that later pass confirmed `process_staged_email`
  still ran the OLD `email_capture_pipeline.run_email_capture_pipeline`/
  `thread_match_merge` path end-to-end, unchanged, until `BUGFIX-05-US-01`
  actually retargeted it (`BUG-026`/`ESC-048`/`ESC-050`).** See
  "`process_staged_email` Retargeted onto Stage 1/Stage 2 Composition"
  below (after "The Librarian Section") for the real, now-accurate design.
  The hourly tick keeps fully capturing mail automatically with zero new
  registration, while each stage is ALSO independently, directly
  operator-triggerable — that part was, and remains, accurate.

### Files/OKF Companion Convention (`REQ-SB-71-US-02`)

New, generic `vault_writer.write_file_companion(subfolder: str, note_stem:
str, file_slug: str, original_filename: str, content: bytes, summary: str)
-> dict` — parameterized by `(subfolder, note_stem)` exactly like
`write_attachments` already is, renamed `attachments/` → `files/`:
`<subfolder>/files/<slug-of-file_slug>/<original_filename>` (raw bytes,
untouched) beside `<subfolder>/files/<slug-of-file_slug>/<slug-of-
file_slug>.md` (an OKF-lite companion note: frontmatter + `## Summary`
agent-owned + `## Personal Notes` human-owned) — replacing today's buried,
unlinked dated sub-entry with a first-class, backlink-discoverable note.
Built once, against the one real concrete need (Email/Thread attachments);
generic enough that Meeting/Customer/Person/a future Opportunity reuse it
UNCHANGED the moment a second real files-capturing need exists. Reuses
`compass_client.summarize_content` + `upload_storage.save_upload/
extract_text_content/delete_upload` verbatim — the identical technique
`summarize_attachment` already established, no new extraction/
summarization mechanism. The companion's own `## Summary` write is
allow-list-checked (new caller id, see the Section-Ownership table above);
`## Personal Notes` is human-owned, uniformly, with zero extra code beyond
the guard already covering it.

### Meeting Capture Redesign — One-Time/Recurring Split (`REQ-SB-71-US-03`)

Reuses the EXISTING `POST /poc/classify-meetings` endpoint and
`"meeting-capture"` capability id unchanged — `meeting_classification.
classify_recent_meetings` is rewritten IN PLACE to produce the new shape;
no new endpoint is built. The existing scheduled trigger keeps running
exactly as wired, now producing the new shape on its next tick.

- **One-time — unchanged filename scheme,** `Work/Meetings/<meeting-
  slug>.md` (`meeting_note_filename_stem`, `hash8("{subject}|{start}")`,
  `ADR-019`, untouched).
- **Recurring — a new directory shape, `Work/Meetings/<series-slug>/
  <series-slug>.md`, `series-slug` keyed by `item.GlobalAppointmentID`** —
  a direct, deliberate reuse of the exact fact `ADR-013`/`ESC-012` already
  live-confirmed (identical across every occurrence of a series) and
  rejected as a per-OCCURRENCE dedup key; that same "constant across
  occurrences" property is exactly right for series identity.
  `outlook_com.list_calendar_events` gains `is_recurring: bool` and
  `series_id: str` (`getattr(item, "GlobalAppointmentID", None) or ""`).
- **Frontmatter-only logistics, raw invite dropped entirely, never
  archived** (a deliberate, operator-authorized, named exception to this
  project's own archive-not-delete discipline). `teams_link`/`dial_in` are
  extracted via regex from `item.Body` TRANSIENTLY inside `list_calendar_
  events` (or a small helper it calls) — the raw body string itself is
  NEVER included in the returned dict and never reaches any caller or
  disk. Surviving frontmatter: `teams_link`, `dial_in`, `organizer`,
  `attendees` (wikilinks), `recurrence`, `calendar_event_id` (`id`, one-time)
  or `calendar_series_id` (`series_id`, recurring).
- **Body — identical shape for one-time and recurring** (one shared code
  path): `## Summary` (agent-owned, regenerated, allow-list-checked, new
  caller `meeting_classification.classify_recent_meetings`) + `## History`
  (agent-owned, GROWING via the existing, unguarded `append_body_section_
  line` — one dated entry per occurrence; a one-time meeting ends up with
  exactly one entry, ever) + `## Personal Notes`/`## Actions` (human-owned).
  Each `## History` entry is synthesized (new Compass call, reusing
  `compass_client.summarize_content` verbatim) from the occurrence's own
  calendar logistics AND, when linked, its Thread's current `## Summary`
  (`read_body_section` against `synthesize_thread`'s own just-written
  output — never a second, divergent Thread-summarization call).

### People — Nested Under Primary Customer (`REQ-SB-71-US-03`)

Extends `ADR-004`'s folder-vs-tag boundary a second time (after `ADR-042`'s
own Customer/Project hub-entity carve-out), deliberately and narrowly, for
Person only — Thread, Meeting, and Files all stay flat/tag-linked,
unchanged.

- `vault_writer.person_note_dedup_key(name, email) -> str` (new) —
  lowercased email when one exists (unchanged `REQ-SB-10` convention), or
  a slug of the display name when it does not (closes `meeting_
  classification.py`'s own silent no-email-attendee `continue`, line
  271-279's `if not email: continue`). A name-based key cannot
  structurally distinguish two different no-email people sharing an exact
  display name — a real, disclosed, narrow residual limitation.
- `vault_writer.person_note_path(dedup_key, customer) -> Path` — SIGNATURE
  CHANGE from `person_note_path(email)`: `Work/Customers/<slug>/People/
  <slug-of-dedup_key>.md` when `customer` is a real, matched Customer name;
  the existing flat `Work/People/<slug-of-dedup_key>.md` otherwise
  (operator-confirmed 2026-08-18 fallback for a Person with no derivable/
  matched Customer at all — including every no-email attendee, since there
  is no email domain to derive a company from).
- `vault_writer.find_person_note_path(dedup_key) -> Path | None` (new) —
  vault-wide lookup (`Work/Customers/*/People/<stem>.md` +
  `Work/People/<stem>.md`), mirroring `resolve_thread_note_path`'s own "no
  persisted index, a live bounded scan" precedent for the identical class
  of problem (a Person's home is no longer deterministic from `dedup_key`
  alone once nesting depends on a per-caller Customer match that can
  differ across callers/time).
- `people_extraction.ensure_person_note(name, email)` (signature otherwise
  unchanged; `email` may now be `None`/`""`) checks `find_person_note_
  path` FIRST — an already-existing note is topped up in place, NEVER
  moved or duplicated, even when this call's own newly-derived Customer
  differs from where the note already lives (a Person spanning multiple
  Customers is wikilinked from the others via the SAME forward-link
  mechanism already used everywhere in this codebase, plus Obsidian's own
  automatic backlinks — no new linking mechanism). Only when no note
  exists anywhere yet is a new one created, nested under the matched
  Customer or, absent one, at the flat fallback. `customer_hub_linking.
  ensure_customer_hub_note`/`link_note_to_customer_hub` are called exactly
  as they already are today, layered on top, unmodified.
- **Explicitly out of scope for this batch:** Person's own PRD-named
  `## Glimpse` (agent-owned, rolled up from every Thread/Meeting mention)
  + `## Personal Notes` body redesign — none of `REQ-SB-71-US-03`'s own AC
  Scenarios test Person body content, only existence/dedup/nesting
  location. Person's own body stays exactly as it is today for this batch;
  a future Person-Synthesizer story is where that lands.

### `list_all_note_paths()` generalization (cross-cutting)

Replaces the 1-level flat glob plus two hardcoded Customer/Project-specific
2-level globs with one bounded recursive scan:
```python
def list_all_note_paths() -> list:
    work_root = settings.vault_path / _WORK_ROOT
    if not work_root.exists():
        return []
    return sorted(
        path for path in work_root.rglob("*.md")
        if path.name not in _OKF_RESERVED_FILENAMES
    )
```
Strictly behavior-preserving for every existing caller (a superset of the
old result); newly, correctly discovers Thread's own distilled concept
file, a recurring Meeting series' own concept file, every raw message
note, and every File OKF companion note — all real, normally-frontmattered
notes this redesign nests at varying depths. `list_thread_notes()`
(composed by `list_threads_for_project`, Meeting's own fallback linker,
and `_link_to_thread_by_conversation_id`'s existence check) is similarly
rewritten for the new 2-level shape (`Work/Threads/*/*.md`, filtered to
`path.parent.name == path.stem` — excludes `messages/*.md`).

### Disclosed, unresolved-by-this-pass regression risks

- **`inbox-cockpit.html`'s backend** (`app/business/cockpit/attachments.py`,
  hardcoded `Work/Emails/attachments`) **and `meeting-cockpit.html`'s own
  backend** both have a real, disclosed regression risk against these new
  shapes (raw `files/` layout; recurring Meeting's own `## History`-per-
  occurrence shape) — named here, not silently left broken. Whether each
  is fixed inside these same stories' own tasks or filed as a separate,
  disclosed follow-up is a decomposer-level scoping call.
- **Backfilling already-captured Thread/Meeting/Person notes onto any of
  these new shapes is explicitly out of scope** (mirrors `REQ-SB-67`/
  `REQ-SB-69`'s own "capture vs. backfill are separable concerns"
  precedent) — going-forward capture only.

## The Librarian Section — First Housekeeping Pipeline (`REQ-SB-72-US-01`, see [ADR-049](ADR.md))

The first Section built as ongoing, self-running vault hygiene rather than
operator-triggered capture — the "housekeeping runs itself" half of this
project's own capture-vs-housekeeping split (`REQ-SB-70`/`REQ-SB-71` are
explicitly manual/API-only; this Section is the deliberate opposite). Full
architectural reasoning, every alternative considered, and every consequence
(including a real, escalated finding against the still-live `thread_match_
merge` pipeline): [ADR-049](ADR.md).

### Thread lookup — frontmatter-based, again (partially supersedes `ADR-048` Decision 3)

A new, shared, read-only primitive is the ONE place the "does a Thread for
this `conversation_id` already exist, and if so, where" question is answered
going forward:

```python
def resolve_thread_directory(conversation_id: str) -> Path | None:
    """Frontmatter-based scan over list_thread_notes() (never a second,
    independent Thread-enumeration mechanism), matching frontmatter.get(
    "conversation_id") == conversation_id. Returns the Thread's own
    DIRECTORY (path.parent), or None. This is the THIRD swing of this
    project's own Thread-matching mechanism (ADR-046 frontmatter-scan ->
    ADR-048 deterministic-path -> back to frontmatter-scan), justified by
    real steady-state capture volume (~10 emails/hour) being cheap enough
    to scan -- the 400-email bulk-retrofit volume ADR-048 was optimized
    for is a separate, disclosed concern (bulk/retrofit callers may still
    compose thread_directory_paths(conversation_id) directly)."""
```

- **`resolve_thread_note_path(conversation_id) -> Path | None`** — PUBLIC
  SIGNATURE UNCHANGED, retargeted to a thin wrapper over
  `resolve_thread_directory` (`directory / f"{directory.name}.md"` or `None`)
  — every existing caller (`_link_to_thread_by_conversation_id`,
  `_trigger_project_resynthesis`, `synthesize_thread`'s own create-vs-update
  check) keeps working with ZERO call-site change.
- **`raw_message_note_path(conversation_id, message_id, received)`** —
  retargeted to resolve-first-with-deterministic-fallback: composes `resolve_
  thread_directory` first; if found, writes under THAT directory's own
  `messages/`; only when the Thread genuinely does not exist yet (Stage 1's
  own very-first message for a new conversation) does it fall back to the
  deterministic `thread_directory_paths(conversation_id)["messages"]` — the
  same two-tier "resolve, else deterministic-create-path" shape `resolve_
  meeting_note_path` already established for Meeting.
- **Two more real callers, found by direct reading, migrated off directly
  composing `thread_directory_paths(conversation_id)` (which silently
  resolves to the WRONG, since-renamed, now-nonexistent path once a Thread
  has been renamed):**
  - `raw_message_capture.capture_raw_thread_messages`'s own "does the Thread
    concept file exist yet" check — swapped for `resolve_thread_note_path`,
    matching Stage 2's own existing semantics exactly.
  - `meeting_classification._synthesize_history_entry`'s own linked-Thread
    `## Summary` read for a Meeting's own `## History` entry — swapped for
    `resolve_thread_note_path`, so a Meeting linked to a since-renamed Thread
    still finds its real, current Summary instead of silently falling back to
    empty.
  - `synthesize_thread`'s own `messages/` directory read is reordered to
    derive from the ALREADY-resolved `existing_path`'s own parent directory
    (falling back to the deterministic path only on the genuinely-new-Thread
    branch) — the exact mechanism Scenario 2's own "further message in the
    SAME conversation still correctly matches the renamed Thread" requires.
- **`thread_directory_paths(conversation_id)` itself is UNCHANGED** — still
  the deterministic path a brand-new Thread is always FIRST created at, and
  still available for bulk/retrofit internal use per this story's own
  Constraint carve-out. Nothing about Thread's own directory-vs-single-file
  shape, its permanent `conversation_id` grouping key, the Stage 1/Stage 2
  split, or the write-once raw-message contract changes — only WHERE an
  ALREADY-EXISTING Thread's current location is looked up.

### Legacy flat-shape Thread recognition — self-healing migration on first touch (`BUGFIX-05-US-01`, narrows `ADR-049` Decision 1's "purely read-only" framing, see [ADR-052](ADR.md))

`ESC-055` (`BUGFIX-05-US-01`'s own decomposer pass) found that the section
above is still, on its own, blind to a genuinely flat, pre-redesign `Work/
Threads/<name>.md` note — `list_thread_notes()`'s own `Work/Threads/*/*.md`
glob structurally cannot match it, so `resolve_thread_directory()` never
even offered it as a scan candidate, independent of which composing
function (`thread_match_merge` OR `synthesize_thread`) called it. Confirmed
already live: 8 real flat notes in the vault at this pass, one already
diverged into a real, duplicate directory-shaped Thread
(`conversation_id ED0954959F6F4A4C88F9E2ACA3D7113A`, see `ESC-055`).
Full reasoning, why "just widen the glob and return the flat note's own
path unmigrated" is not actually viable given `synthesize_thread`'s own
existing update-branch code, and every alternative considered:
[ADR-052](ADR.md).

`resolve_thread_directory(conversation_id)` gains a second scan tier, tried
ONLY on a miss from the first (existing, directory-shaped) scan above:

```python
def resolve_thread_directory(conversation_id: str) -> Path | None:
    """... existing directory-shaped scan first (unchanged) ...
    On a miss, a second tier globs Work/Threads/*.md directly (flat notes
    only, never folded into list_thread_notes() itself) for the same
    frontmatter.get("conversation_id") == conversation_id match. On a
    match, immediately calls migrate_flat_thread_to_directory(flat_path)
    -- moving it to the standard thread_directory_paths(conversation_id)
    location (concept file + empty messages/) -- and returns the NEW
    directory. Never returns a flat file's own path/parent directly. A
    one-time, idempotent, self-healing WRITE for this one legacy-shape
    case only -- the ONE deliberate exception to this function's own
    otherwise purely-read-only contract."""
```

- **Ordering is load-bearing:** directory-shaped scan first, flat-note scan
  second, only on a miss — this is what correctly, silently no-ops for a
  `conversation_id` that already has BOTH shapes (the already-diverged
  Azure Forecast case) instead of attempting a redundant migration of the
  already-orphaned flat note. That already-diverged case is NOT fixed by
  this mechanism — a deliberate, disclosed non-goal (see `ESC-055`'s own
  resolution note for the separate, deferred data-remediation decision).
- **`migrate_flat_thread_to_directory(flat_path: Path) -> Path`** (new,
  `vault_writer.py`) — mirrors `rename_thread_directory`'s own
  refuse-to-overwrite discipline (raises `FileExistsError` on the
  structurally near-impossible deterministic-slug collision, never
  silently overwrites); reuses `thread_directory_paths(conversation_id)`
  unchanged for the target location — no second naming scheme. The
  Librarian's own already-scheduled `rename_threads()` Job picks up a
  freshly-migrated Thread on its own very next pass and renames it to the
  human-readable `<date> <subject>` stem exactly like any other Thread — no
  special-casing needed there.
- **`list_thread_notes()` itself is UNCHANGED** — still directory-shape-only
  by contract; every one of its own callers (`list_threads_for_project`,
  every Librarian Job) sees a migrated former-flat-note for free on its own
  next pass, once any `resolve_thread_directory` call has touched it — no
  caller anywhere else needs to change.
- Of the 8 real flat Threads confirmed live at this pass, 7 have no known
  directory-shaped duplicate yet and self-heal correctly, losslessly, the
  next time a new message lands for their own `conversation_id` — no human
  action needed. Only the 1 already-diverged case needs separate handling.

### Migration content-preservation — the `pre_migration_summary.md` sidecar (`BUGFIX-05-US-01-T04` finding, `ESC-056`, see [ADR-053](ADR.md))

`ESC-056` (`T04`'s own live verification of `AC-01`) found that the
section above, while a correct and lossless SHAPE migration on its own,
is not sufficient once composed with `synthesize_thread` in the SAME
pipeline tick: `synthesize_thread` always regenerates `## Summary` by
full reconstruction from every raw message currently under `messages/`
(see "Email Capture Redesign — Thread Raw/Distilled Split, Stage 1/Stage 2"
above, `REQ-SB-71-US-02`'s own "full reconstruction... never a rolling/
incremental delta" Stage 2 design); a
just-migrated flat Thread's `messages/` starts empty (by
`migrate_flat_thread_to_directory`'s own correct, `ADR-052` design), so
the FIRST post-migration synthesis silently replaces the flat note's
own real, substantive, pre-migration `## Summary` (written over real
history by the OLD `thread_match_merge` pipeline) with a synopsis of
just the one new message. Confirmed live, fully repaired before this
fix (`Compass Alert- Failed API Calls`, byte-identical restore).
`## Summary` is confirmed, by direct reading, the ONLY at-risk section —
`## Related` ownership already transferred to the Librarian
(`ADR-049` Decision 4), `## Personal Notes`/`## Actions` are human-owned
and never agent-written, and the legacy `## Transcript` section is dead
and untouched by `synthesize_thread` either way.

**The fix is a one-time, self-consuming sidecar file, not a change to
`ADR-048`'s "full reconstruction, never a rolling/incremental delta"
design** (that design is extended, not reopened — this exception is
scoped exclusively to a freshly-migrated Thread's own pre-migration
history, real content otherwise represented nowhere under `messages/`):

```python
def migrate_flat_thread_to_directory(flat_path: Path) -> Path:
    """... unchanged shape-migration steps, PLUS: reads the flat note's
    own pre-migration ## Summary via the existing read_body_section
    primitive, BEFORE the rename. If non-empty, writes it verbatim to a
    new sidecar file, <new-directory>/pre_migration_summary.md -- plain
    text, no frontmatter, the same 'reserved, non-frontmatter sidecar'
    shape index.md/log.md/captures.md already established for OKF
    directories (ADR-042 point 1), here for a Thread directory instead.
    Lives OUTSIDE messages/, so it is structurally invisible to
    list_thread_notes() and to synthesize_thread's own messages_dir
    glob -- never pollutes the messages list, first-message
    classification, participant accumulation, or message_count."""
```

```python
def synthesize_thread(conversation_id: str) -> dict:
    """... unchanged Stage 2 body, PLUS: immediately before composing
    full_content for its existing Compass call, checks for path.parent /
    'pre_migration_summary.md'. If present, its text is prepended to
    full_content as an explicitly-labeled prior-history block -- the SAME
    existing Compass call, never a second one, never a new function. On a
    SUCCESSFUL synthesis only, the sidecar is renamed in place to
    pre_migration_summary.consumed.md -- never deleted, archive-not-
    delete (mirrors ADR-047 Decision 2's own soft-delete convention at
    the smallest possible scope), and never fed again on any later call
    (the renamed file no longer matches the check). On a FAILED
    synthesis, the sidecar is left untouched, exactly like the Thread's
    own existing ## Summary -- retried on the next successful run."""
```

- **`list_all_note_paths()` excludes both `pre_migration_summary.md` and
  `pre_migration_summary.consumed.md` by filename** — the same mechanism
  already used for `index.md`/`log.md`/`captures.md`, so this plain,
  non-frontmatter sidecar is never surfaced to "every real note" callers
  (search/browse indexing, Librarian Jobs).
- **No `section_ownership.py` change.** The sidecar carries no `## `
  header of its own and is never written via `replace_body_section` —
  `## Summary`'s own allow-list stays exactly `{"email_classification.
  synthesize_thread"}`, one writer, unchanged.
- **Deliberately scoped to `## Summary` only** — the one section
  confirmed at risk. `migrate_flat_thread_to_directory`'s own move/rename
  already preserves every other section losslessly (unchanged from
  `ADR-052`); a second, whole-note `.second-brain/migration_backup/`
  archive was considered and rejected as redundant, not because
  redundancy is undesirable in principle but because no second at-risk
  section has been found (see `ADR-053` Alternatives Considered).

Full reasoning, every alternative considered (including why `ESC-056`'s
own three candidate options were each rejected in favor of this narrower
design), and every consequence: [ADR-053](ADR.md).

### Thread rename — a real, atomic whole-directory move

```python
def rename_thread_directory(old_directory: Path, new_directory: Path) -> Path:
    """Mirrors rename_thread_note's own refuse-to-overwrite discipline, one
    level up (a directory, not a single file): no-op if old == new; raises
    FileExistsError if new_directory already exists (a genuine <date>
    <subject> collision -- surfaced, never silently overwritten); otherwise
    old_directory.rename(new_directory) moves the WHOLE tree -- concept
    file, messages/, and any files/ -- in one atomic filesystem op, then the
    concept file inside is itself renamed from <old-slug>.md to <new-slug>.md,
    preserving the <slug>/<slug>.md invariant list_thread_notes() depends
    on. Returns the new concept file path."""
```

The Librarian's own Rename Job computes each Thread's new slug as `<date>
<subject-without-Re->` (e.g. `2026-08-16 Ewec Discussion`) from the Thread's
own already-captured `thread_name`/`last_message_at` frontmatter — no hash
suffix (unlike Meeting's/legacy Thread's own schemes); a genuine collision
surfaces via `rename_thread_directory`'s own raise, handled per-Thread
(skip-and-report, never silently dropping one Thread's rename to save
another's). The OLD `rename_thread_note`/`thread_note_path_for`/`thread_
note_filename_stem` primitives (`ADR-046`) are left completely UNTOUCHED —
still the still-live (though `supervised`-only) `thread_match_merge`'s own
internal mechanism; see Consequences/`ESC-050` below for why this pass does
NOT touch them.

### Files/OKF backfill + `## Files` section

The Files Backfill Job scans `staged_attachment_files(conversation_id,
message_id)` for every raw message under a Thread's own (resolved, current)
`messages/` directory, and for any attachment with no `files/<slug>/`
companion yet, calls `write_file_companion` (`REQ-SB-71-US-02`, UNCHANGED) —
never a second, divergent companion primitive. A new caller id registers
`## Files` in `section_ownership.py` (below); the writer composes each
companioned attachment's own filename/date/`## Summary`-derived blurb/working
link into a structured list, distinct from `## Summary`'s own prose.
Re-running is idempotent by construction: an attachment with an existing
companion is skipped (matches Scenario 4).

### `## Related` ownership transfer

`email_classification.synthesize_thread`'s own `section_ownership.py`
allow-list entry narrows from `{"## Summary", "## Related"}` to `{"##
Summary"}` alone, in the EXACT SAME change that registers the Librarian's own
new `## Related`-writing caller — never a window where both are simultaneously
permitted (Scenario 6/8's own "sole ownership by construction" requirement).
The Librarian's own `populate_thread_related_links` Job reuses `_build_
thread_related_wikilinks`'s existing honest-omission contract (a participant
with no real Person note is omitted, never guessed) and extends it with the
new company-mention detection below, for every other real company genuinely
mentioned in a Thread's own content.

### Company-mention detection & the ambiguous-finding Pending Approval

A NEW, dedicated Compass call — reuses `compass_client.summarize_content`'s
own structured-JSON-call TECHNIQUE, never `vault_filing_expert.determine_
placement_and_file` itself (that function decides WHERE ONE piece of brand-new
content is filed; this is a different-shaped problem — extracting WHICH
already-known/plausible companies an already-filed Thread's content mentions).
Re-checked in Python against the live `known_customers`/`known_partners`
lists before ever acting — never trusted from the model's own naming alone,
mirroring `_maybe_create_cross_cutting_proposal`'s own exact discipline
(`ADR-021` point 2):

- **Genuinely new, unambiguous company name** (no fuzzy/partial match against
  either known list) → auto-creates via `ensure_customer_hub_note`
  (`REQ-SB-63`, UNCHANGED) directly — Tier-1-shaped, no approval (Scenario 9).
- **A name that plausibly matches an existing `known_customers`/`known_
  partners` entry under a different spelling, or that the model itself flags
  low-confidence** → a new Pending Approval, `action_id=
  "propose_librarian_company_link"`, payload mirroring `_create_cross_
  cutting_proposal`'s own shape (`entity_type`, `entity_name`, `reason`,
  `thread_path`, `requesting_agent_id="librarian-housekeeping"`), finalized by
  a new `finalize_librarian_company_link` handler that performs the deferred
  create-or-link action on approval, and nothing on decline (Scenario 10) —
  never a second, divergent placement/proposal mechanism (`ADR-021` point 2's
  own precedent, reused by analogy).

### Section-ownership registrations (new `section_ownership.py` entries)

| Caller | Allowed headers |
|---|---|
| `librarian_housekeeping.backfill_files` (exact module path left to the coder) | `## Files` |
| `librarian_housekeeping.populate_thread_related_links` | `## Related` |
| `email_classification.synthesize_thread` (narrowed) | `## Summary` only |

### Librarian Section/Agent identity, endpoints, and scheduling

- **Section:** `section_registry.create_section("Librarian")` →
  `"librarian"` (existing, unmodified mechanism, `REQ-SB-18`/`ADR-014`).
- **Agent:** `agent_registry.create_agent("Librarian Housekeeping",
  type="worker", settings=[...])` → `"librarian-housekeeping"` (mirrors
  `email-capture-pipeline`'s own "worker" type + Pipeline-shaped
  settings-block convention), then `section_registry.set_agent_section
  ("librarian-housekeeping", "librarian")`. No new Section-creation
  machinery — `REQ-SB-61`'s own separately-deferred Location/Tags
  generalization is not built here (per this story's own explicit scoping
  call).
- **Endpoints — reuse the EXISTING `app/api/email_poc_router.py`** (already
  this codebase's general home for flat, operator-triggered one-off `/poc/*`
  operations regardless of subject area, per `ADR-048` Decision 1's own
  precedent — no new sibling router):
  - `POST /poc/librarian-rename-threads`
  - `POST /poc/librarian-backfill-files`
  - `POST /poc/librarian-populate-related`
  - `POST /poc/librarian-backfill-company-folders`
  - `POST /poc/librarian-run-housekeeping-pass` — the ORCHESTRATING
    capability, running all four Jobs in sequence (rename first, so
    downstream Jobs operate on each Thread's own final, current directory;
    Files/Related/Company-folder Jobs have no ordering dependency among
    themselves) — the ONE capability id `agent_schedule_registry` targets.
  Each Job is its own independent, directly operator-triggerable capability
  of the NEW `"librarian-housekeeping"` Agent-tier identity (mirrors Stage
  1/Stage 2's own "independently triggerable AND composed by the scheduled
  tick" shape, generalized here to five capabilities of one brand-new Agent
  identity rather than two of an already-existing one).
- **Scheduling — a REAL, disclosed, deliberate opposite of `REQ-SB-70`/
  `REQ-SB-71`'s own standing no-scheduler constraint**, per this story's own
  explicit PRD mandate: `agent_schedule_registry.create_schedule(agent_id=
  "librarian-housekeeping", capability_id="run_housekeeping_pass",
  interval_value=6, interval_unit="hours")` — a reasonable, operator-
  adjustable DEFAULT (never a locked-AC value, mirrors this codebase's own
  "no locked AC tests a specific field value" pattern), editable/pausable via
  the existing Schedule tab like any other `agent_schedule_registry` entry.
  Directly, manually triggerable too, via the endpoints above.

### Disclosed, escalated consequence — NOT fixed by this pass

Reverting `resolve_thread_note_path` to a frontmatter scan restores this
pipeline's own ability to find an ALREADY-RENAMED Thread — but the still-live,
`supervised`-only `thread_match_merge` (`email_capture_pipeline.py`,
`ESC-048`) ALSO composes `resolve_thread_note_path` for its own create-vs-
update check, and then — independently, via its own still-live legacy `thread_
note_path_for`/`rename_thread_note` calls (`ADR-046`, deliberately left
untouched by this pass) — computes a FLAT, hash-suffixed legacy path and
renames the concept file onto it, ORPHANING that Thread's `messages/`/`files/`
subdirectories. This is NOT a new risk this story introduces — direct reading
confirms it already fires TODAY for ANY already-existing new-shape
(`ADR-048`) Thread the moment `thread_match_merge` runs against it, entirely
independent of whether this story ships — but it is materially WORSE than
`ESC-048`'s own original description (directory-orphaning data corruption,
not merely duplicate-Thread creation), and this story's own rename mechanism
means MORE real Threads become exposed to it over time. `email_capture_
pipeline.py`/`thread_match_merge` are OUTSIDE this story's own `## Files to
Modify` (per its own Non-Goals) — named here, not silently fixed or left
undisclosed. See [ADR-049](ADR.md) Consequences and `ESCALATIONS.md` →
`ESC-050`.

**Fixed (`BUGFIX-05-US-01`, 2026-08-19):** `thread_match_merge`'s live call
site is retired from `process_staged_email`'s real path — see
"`process_staged_email` Retargeted onto Stage 1/Stage 2 Composition" below,
[ADR-051](ADR.md).

## `process_staged_email` Retargeted onto Stage 1/Stage 2 Composition (`BUGFIX-05-US-01`, see [ADR-051](ADR.md))

Closes `BUG-026`/`ESC-048`/`ESC-050`. `process_staged_email` (the only
capability the real, scheduled `email-capture-pipeline` Agent invokes to
process staged mail) previously ran the OLD compiled `email_capture_
pipeline.py` `StateGraph` end-to-end — including its still-buggy
`thread_match_merge` node — despite `ADR-048`/`ADR-049` and this file's own
prior "stays wired... composes the two [Stage 1/Stage 2] functions" bullet
above having already stated the INTENT to retarget it. That intent was
never actually implemented until this pass. Full architectural reasoning,
every alternative considered, and every consequence: [ADR-051](ADR.md).

### What backs `process_staged_email` now

`skill_registry.py`'s `"process_staged_email": skill_tools.
process_staged_email` mapping and `skill_tools.process_staged_email`'s own
signature/deferred-import call site (`email_capture_pipeline.
run_email_capture_pipeline`) are UNCHANGED — the fix is entirely inside
`run_email_capture_pipeline`'s own function body, same module, same name,
same zero-argument call shape. That body no longer builds or invokes the
`StateGraph`; it is now a plain, sequential composing function:

1. Calls `raw_message_capture.capture_raw_thread_messages(limit=...)`
   once (Stage 1 — zero-Compass raw capture, unchanged). Its own return
   dict gains one additive key, `conversation_ids_touched: list[str]`
   (derived from its own already-in-scope per-item loop over newly
   processed messages) — a pure superset of its existing `pulled`/
   `processed`/`skipped_already_noted` keys; the `/poc/capture-raw-thread-
   messages` endpoint's response shape is unaffected for any existing
   consumer.
2. For each distinct `conversation_id` in `conversation_ids_touched`,
   calls `email_classification.synthesize_thread(conversation_id)`
   (Stage 2, unchanged) — which already internally performs create-vs-
   update, customer/tags/participants, `## Summary` regeneration, the
   Files/OKF companion writes, and `route_to_project`'s created-only
   Pending-Approval trigger (confirmed by direct reading; no separate call
   needed for any of these).
3. For each such Thread, three of the old graph's OTHER real branch
   effects — which have NO equivalent anywhere in the `REQ-SB-71`/
   `REQ-SB-72` redesign — are explicitly, directly re-composed as plain
   calls in this SAME function, never re-implemented (mirrors
   `librarian_housekeeping.run_housekeeping_pass`'s own "one orchestrator,
   direct sequential calls to existing plain Jobs" shape, `ADR-049`
   Decision 7):
   - **`detect_recurring_pattern`** — for each NEWLY captured raw message
     this run (Stage 1's `processed` list only, not `skipped_already_
     noted`), reads back that message's own just-written raw note,
     reconstructs an `email`-shaped dict, calls `classify_captured_email_
     with_fallback` once against it (a genuine, additional per-message
     Compass classify call — `synthesize_thread`'s own internal classify
     is Thread-lifetime-scoped, always the FIRST message, the wrong signal
     for a later message's own recurring-pattern check), and calls
     `detect_recurring_pattern(email, classification)` when
     `recurring_candidate` is true. Wrapped in its own try/except — never
     gates the Thread's own already-successful capture/synthesis.
   - **`consult_librarian`** — called once per synthesized Thread
     (`synthesized: True`), passing `synthesize_thread`'s own result dict
     directly, unconditional for both a brand-new and an updated Thread
     alike. NOTE: this is a DIFFERENT "Librarian" than the `REQ-SB-72`
     `librarian-housekeeping` Agent below — `consult_librarian` calls the
     GENERALIZED Vault Filing Expert (`vault_filing_expert.determine_
     placement_and_file`, `ADR-021`/`REQ-SB-63`), an unrelated mechanism
     the confusingly similar name should not be conflated with.
   - **`project_customer_synthesizer.resync_project_from_thread`** —
     called once per synthesized Thread, passing `thread_result[
     "thread_path"]` directly (its own existing signature/no-op-for-
     unrouted-Thread contract unchanged), unconditional — the ongoing
     Project-`## Glimpse`-resync-on-every-update behavior `REQ-SB-57`
     Scenario 1/AC-01 requires, which `synthesize_thread`'s own
     `route_to_project` call (created-only) does not provide.
4. The whole per-`conversation_id` unit (Stage 2 plus its three composed
   side effects) is wrapped in one outer try/except at the loop level,
   mirroring the old per-email try/except+continue+honest-error-result
   posture — a genuinely unexpected exception is reported as
   `{"conversation_id", "error"}` and the run continues to the next
   Thread, never aborting the rest of the tick.

`summarize_attachment`'s own old role needs NO equivalent on this new
path — it is already, deliberately superseded by the Files/OKF companion
mechanism (`write_file_companion`, called from `synthesize_thread`'s own
end) plus the Librarian's structured `## Files` backfill
(`REQ-SB-72-US-01-T04`); `## Attachments` does not exist in the new
distilled concept-file body shape at all.

### Return-shape change (disclosed behavior change, not a signature change)

`run_email_capture_pipeline()` now returns one row per synthesized THREAD
this run, not one row per fetched email. `skill_tools.process_staged_
email`'s own `"error"`-key-presence convention
(`filed = [r for r in results if "error" not in r]`) stays compatible
as-is; its success-message wording ("N email(s) filed" → "N thread(s)
updated") is a task-level detail for the coder.

### `email_capture_pipeline.py`'s `StateGraph` — deprecated, not deleted

`_build_graph()`/`_GRAPH`/`get_job_tree()` and `email_classification.
thread_match_merge`'s own function body all remain in the codebase,
unchanged, fully functional — but no longer on any live execution path for
real capture. Kept specifically because `get_job_tree()` (`REQ-SB-65-US-01`)
is a real, separate, currently-shipped read-only capability
(`agents_router.py`'s Pipeline Job Tree endpoints, consumed by the Agents
Map) that introspects this SAME compiled `_GRAPH` singleton via
`langgraph`'s own `Pregel.get_graph()` — deleting it outright would break
that surface as an uncontrolled side effect of a bugfix whose own scope
never named it.

**Disclosed, not fixed by this pass:** `get_job_tree()`'s own Pipeline Job
Tree visualization now reflects a topology (`Classify`→`Thread-Match/
Merge`→...) that is no longer what `process_staged_email` actually
executes — a real, known staleness, named here rather than silently left
broken. Rebuilding it against the new Stage-1/Stage-2-plus-three-composed-
side-effects shape is recommended as its own future, separately-scoped
follow-up story.

`thread_match_merge` keeps its already-live `section_ownership.py`
allow-list entry (`## Summary`, `## Related`) — unchanged; see the Section-
Ownership table above (already annotated "retired once `synthesize_thread`
ships — dead entry" ahead of this pass actually retiring its call site).

## The Librarian — Bidirectional Thread ↔ Message Linking (`REQ-SB-73-US-01`, see [ADR-054](ADR.md))

A new Job under the ALREADY-EXISTING Librarian Section/`librarian-
housekeeping` Agent (`REQ-SB-72-US-01`) — no new Section, no new Agent, no
new `vault_writer.py` primitive. Full architectural reasoning, why every
mechanism-level question resolves by reuse, and every alternative
considered: [ADR-054](ADR.md).

### `link_thread_messages()` — `## Messages` + `thread:` backlink, retrofit and self-heal in one Job

```python
def link_thread_messages() -> dict:
    """For every real Thread (list_thread_notes()), regenerates ## Messages
    wholesale from the Thread's own CURRENT messages/*.md glob (sorted) as
    "- [[<message-stem>]]" bullets, via insert_body_section_if_missing +
    replace_body_section(..., caller="librarian_housekeeping.link_thread_
    messages") -- never incrementally patched, mirroring ## Files' own
    "regenerated each pass" contract. For every message under that same
    glob, calls vault_writer.upsert_frontmatter_key(message_path, "thread",
    f"[[{concept_path.stem}]]") -- the Thread's own CURRENT stem -- which
    inserts if absent, self-heals a stale value, and is a true no-op if
    already correct, all from ONE existing primitive."""
```

`upsert_frontmatter_key` (already shipped, used live by `meeting_
classification.py`'s own `thread:` field) is the load-bearing reuse here —
unlike `insert_frontmatter_key_if_missing` (every OTHER baseline-field
top-up in this codebase), it OVERWRITES an already-present key holding a
different value, which is what makes this one Job satisfy write-new,
self-heal-stale, AND true-no-op-on-rerun from a single primitive.

### `rename_threads()` fan-out extension — zero-staleness-window, not "eventually consistent"

A bounded addition to the already-Accepted `ADR-049` Decision 2 Job: on a
successful `rename_thread_directory` call, in the SAME loop iteration,
`rename_threads()` now also globs the renamed Thread's own (now-current)
`messages/*.md` and calls `upsert_frontmatter_key(message_path, "thread",
f"[[{new_concept_path.stem}]]")` for each — a genuinely new invariant
`ADR-049` Decision 2 did not provide (its own shipped docstring is explicit
that it "touches nothing INSIDE `messages/`", confirmed by direct reading).
This is a zero-staleness-window guarantee: no message is ever left pointing
at a Thread's own stale, pre-rename slug, even momentarily — not merely
"corrected on the next scheduled `link_thread_messages()` pass." `rename_
threads()`'s own external contract (return shape, per-Thread collision
handling) is otherwise unchanged.

### `section_ownership.py` — new entry

| Caller | Allowed headers |
|---|---|
| `librarian_housekeeping.link_thread_messages` | `## Messages` |

### Job-chain placement & endpoint

`link_thread_messages()` runs SECOND in `run_housekeeping_pass()`,
immediately after `rename_threads()` — grouping the two Jobs that together
own the Thread↔Message relationship, though not load-bearing for
correctness (Scenario 4's own fan-out already keeps `thread:` correct
independent of ordering). New endpoint: `POST /poc/librarian-link-thread-
messages`, mirroring the existing `/poc/librarian-*` convention.

### `vault_indexing.py` extension (cross-cutting — closes a real, independently-found gap)

`_build_entry`'s own `outgoing_wikilinks` was, until this pass, derived from
`body` alone (`extract_wikilink_targets(body)`) — every existing wikilink
convention in this codebase lives in a note's body (`**Customer:** [[Hub]]`,
`**Attendees:** [[P1]], [[P2]]`, `index.md`'s own listing); there was no
precedent for a wikilink embedded as a FRONTMATTER field's own string value,
which is exactly what `thread:` must be (the story's own Gherkin locks this
to a frontmatter field, never a body line, precisely because a `RawMessage`
note's body is the immutable, verbatim email content, `ADR-048` Decision 3).
Left unfixed, a Thread's own real, correctly-written `thread:` value would
have been silently invisible to both the already-shipped backlinks panel and
graph view (`REQ-SB-14`) — breaking Scenario 3/4/5's own "resolves to its
owning Thread" requirement and the story's own "no prototype change needed"
premise. Fixed generically, not by a `thread:`-named special case:

```python
def _build_entry(path) -> dict:
    """... outgoing_wikilinks = extract_wikilink_targets(body) + <targets
    found in any frontmatter string value or string-list element, via the
    SAME extract_wikilink_targets primitive, reused unchanged> -- strictly
    additive: a note with no wikilink-shaped frontmatter value contributes
    zero extra targets, byte-identical to today for every existing note."""
```

Mirrors `list_all_note_paths()`'s own "generalize without reopening the
underlying invariant" precedent (`Implementation/Learnings.md`,
`SPRINT-048`) — this is why the fix does not need its own standalone ADR; it
is folded into `ADR-054` only because `REQ-SB-73`'s own correctness
genuinely depends on it. **Decomposer note: add `app/business/vault_
indexing.py` to this story's own file scope** — it is not named in the
story's own `## Implementation Tasks` table.

## The Librarian — Customer Backfill (`REQ-SB-74-US-01`, see [ADR-055](ADR.md))

A new, manually-triggered (NOT scheduled) Job pair under the ALREADY-
EXISTING Librarian Section/`librarian-housekeeping` Agent — no new Section,
no new Agent. Full architectural reasoning, why the batched-approval shape
needs zero registry change, and every alternative considered:
[ADR-055](ADR.md).

### Detection — `compass_client.detect_customer_for_thread` (new, narrower sibling of `classify_task`)

```python
def detect_customer_for_thread(
    thread_content: str, known_customers: list[str],
    prompt_override: str | None = None,
) -> dict:
    """Narrower sibling of classify_task (ADR-027 point 4's own precedent,
    applied a fourth time) -- asks Compass for this Thread's own primary
    Customer: reuse an exact known name when it clearly matches one,
    propose a new proper-noun name when it clearly relates to a real
    company not yet known, or answer "Unsorted" rather than guess. Returns
    {"customer": str, "confidence": float} -- the SAME honest-"Unsorted"
    contract classify_email/classify_task already established, no extra
    Python-side confidence threshold needed."""
```

`known_customers` here is `vault_writer.list_customer_folders()`'s own
`"customer"` values — the real 26 (+growing) Customer FOLDER names,
deliberately NOT `vault_writer.list_known_customers()` (which scans
`customer:` frontmatter USAGE, currently near-empty since nothing has been
routed yet — a real, disclosed enumeration gap found by direct reading, not
assumed).

### `vault_writer.list_customer_folders()` (new)

```python
def list_customer_folders() -> list[dict]:
    """Every real Customer OKF directory under Work/Customers/ -- mirrors
    list_customer_projects()'s own "enumerate this directory level, read
    title from concept file" shape one level up. Returns [{"customer":
    <title>, "slug": <dir name>, "directory": Path}, ...]; [] if Work/
    Customers/ does not exist yet."""
```

### `propose_customer_backfill()` / `propose_customer_archival_candidates()` — one evidence pass, two proposal kinds

`propose_customer_backfill()` iterates every real Thread still `customer:
"Unsorted"` (`list_thread_notes()`, filtering out any already-routed Thread
for free — Scenario 9's own idempotency), calls `detect_customer_for_
thread` against each, and groups every non-`"Unsorted"` result into ONE
batched Pending Approval per distinct proposed Customer name (`trigger=
"direct"`, mirroring `_create_librarian_company_link_proposal`'s own
reasoning — one pass can legitimately produce multiple distinct findings,
which `"background"`'s idempotency guard would silently collapse). Returns
`{"proposed_batches": [...], "matched_existing_customer_names": [...]}` —
the second key feeds directly into `propose_customer_archival_candidates(
matched_existing_customer_names)`, which surfaces every `list_customer_
folders()` entry NOT in that set as its own archival-candidate Pending
Approval — one evidence pass, never two independently-run Compass sweeps
that could disagree.

**Batched-per-Customer payload convention** (`ADR-055` Decision 1 — reuses
`pending_approval_registry.create_pending_approval`/`pending_approvals_
router.py`'s `_APPROVAL_HANDLERS` dispatch UNMODIFIED; confirmed by direct
reading that both are already fully payload-shape-agnostic):

- **Routing batch:** `action_id="propose_customer_backfill_routing"`,
  `payload={"customer": <name>, "is_new_customer": <bool>, "thread_paths":
  [<str>, ...]}`.
- **Archival candidate:** `action_id="propose_customer_archival_candidate"`,
  `payload={"customer": <name>, "source_directory": <str>}`.

### Finalize handlers (deferred writes, mechanical — never a second Compass call, mirrors `finalize_background_amendment_proposal`'s own precedent)

```python
def finalize_customer_backfill_routing(payload: dict) -> dict:
    """If is_new_customer: customer_hub_linking.ensure_customer_hub_note(
    customer) -- UNCHANGED, reused exactly as backfill_company_folders
    already does for a new_unambiguous mention. For every thread_path:
    vault_writer.upsert_frontmatter_key(path, "customer", customer); and
    upsert_frontmatter_key(path, "tags", <existing tags with any customer/
    entry replaced by customer/<slug-of-customer>>) -- mirrors synthesize_
    thread's own existing tags-mutation shape, both existing primitives,
    zero new vault_writer.py code."""


def finalize_customer_archival(payload: dict) -> dict:
    """vault_writer.move_okf_directory(Path(payload["source_directory"]),
    settings.vault_path / "Work/Archive/Customers") -- content byte-for-
    byte unchanged by construction (a directory rename, never a per-file
    copy)."""
```

### `vault_writer.move_okf_directory()` (new, generic — not Customer-specific)

```python
def move_okf_directory(source_directory: Path, target_parent_directory: Path) -> Path:
    """Mirrors rename_thread_directory's own atomic-move-plus-refuse-to-
    overwrite discipline, widened to a DIFFERENT parent directory (not just
    a new slug under the same parent) and narrowed by NOT renaming the
    concept file inside -- the directory keeps its own name, only its
    location moves, so every file inside is moved byte-for-byte in one
    atomic Path.rename(). Raises FileExistsError on a genuine collision,
    never silently overwrites."""
```

`target_parent_directory = settings.vault_path / "Work/Archive/Customers"`
is already provisioned (`vault_provisioning.provision_vault_base`,
`REQ-SB-70-US-01`, confirmed live) — no new directory-provisioning code.

### Endpoint & scheduling

`POST /poc/librarian-propose-customer-backfill` (new, `email_poc_router.py`)
runs `propose_customer_backfill()` then `propose_customer_archival_
candidates()` in one orchestrating call. Deliberately NOT added to `run_
housekeeping_pass()`'s own scheduled chain — manually-triggered only, per
the story's own explicit Constraint (`REQ-SB-70`/`71`'s standing "live/
ongoing capture stays manual" posture, reaffirmed by the operator).

### Disclosed, not fixed by this pass

A second manual trigger before an already-created batch is approved/
declined re-proposes the SAME still-`"Unsorted"` Threads into a NEW,
separate pending batch (`"direct"` trigger, not idempotency-guarded the way
`"background"` is) — a real, disclosed operational risk, not a defect
Scenario 9's own locked AC (which only covers already-APPROVED Threads)
requires fixing. Left to ordinary operator discipline for a one-time,
manually-triggered backfill. See [ADR-055](ADR.md) Consequences.

**Superseded in practice by "The Librarian — Company Review," below
(`REQ-SB-76-US-01`, 2026-08-19):** this Job pair, `detect_customer_for_
thread`, and `POST /poc/librarian-propose-customer-backfill` are left
byte-for-byte unedited (`Done`, frozen, `Implementation/Pipeline.md` hard
rule 1) but are no longer the operator's own live mechanism going forward —
not deleted, not hidden, simply unused. See [ADR-057](ADR.md).

## The Librarian — Company Review (`REQ-SB-76-US-01`, see [ADR-057](ADR.md))

A new, manually-triggered (NOT scheduled) Job pair under the SAME
already-existing Librarian Section/`librarian-housekeeping` Agent — no new
Section, no new Agent, mirroring `REQ-SB-74-US-01`'s own precedent exactly.
Replaces `propose_customer_backfill`'s own direct-routing mechanism going
forward (left physically unedited, see above) with a two-step extract-
then-classify flow offering five real outcomes — Customer, Partner,
Affiliate-of-an-existing-Customer-or-Partner, Merge-into-an-existing-
Customer-or-Partner, or Decline — batched per company, reusing `ADR-055`'s
own batched-per-company Pending Approval convention verbatim. Full
architectural reasoning, every alternative considered, and every
consequence: [ADR-057](ADR.md).

### Extraction — `compass_client.extract_thread_companies_for_review` (new, boilerplate-aware sibling)

```python
def extract_thread_companies_for_review(
    thread_content: str, known_companies: list[str],
    prompt_override: str | None = None,
) -> dict:
    """A new, narrower sibling of detect_mentioned_companies (ADR-049
    Decision 5's own multi-mention TECHNIQUE), never an edit to the frozen,
    Done detect_customer_for_thread (ADR-055 Decision 2) -- REQ-SB-76-US-01,
    ADR-057 Decision 1. Explicitly instructs Compass to DISREGARD any
    company/product/device name appearing ONLY inside an email-client or
    device signature line ("Sent from my iPhone," "Get Outlook for
    Android"), a mailing-list footer, or a legal disclaimer -- these are
    NOT genuine mentions, the root-cause fix for this requirement's own
    self-reinforcing-noise finding. Identifies EVERY real company the
    Thread's own substantive content genuinely relates to (not scoped to
    "besides an already-known primary Customer" -- detect_mentioned_
    companies's own different framing), reusing an exact known name from
    known_companies (the UNION of list_customer_folders() + list_known_
    partners(), never hardcoded) when it clearly matches one. Returns
    {"companies": [{"name": str, "confidence": float}, ...]}. Malformed/
    missing "companies" raises CompassError, mirroring every sibling
    primitive's own honest-failure contract."""
```

### `propose_company_review()` / `finalize_company_review()` — the new Job pair

`propose_company_review()` iterates every real Thread (`list_thread_
notes()`, NOT filtered to `"Unsorted"` only — Scenario 9 needs an
already-routed Thread considered too), calls the extraction function above
once per Thread, and skips any returned company mention whose exact
`customer/<slug>`/`partner/<slug>` tag is already present on that Thread
(the per-mention idempotency floor, generalizing `propose_customer_
backfill`'s own per-Thread "already routed" skip). Every remaining mention
groups into ONE batched Pending Approval per distinct company name:

- `action_id="propose_company_review"`, `trigger="direct"`, `payload =
  {"company": <name>, "thread_paths": [<str>, ...]}`, `dedupe_key=
  f"propose_company_review:{company}"` (`ADR-056`'s own target-aware
  convention, applied from day one).

A single transient `CompassError` for one Thread is recorded in a
`"failed"` list and skipped, mirroring `propose_customer_backfill`'s own
`T06`-found honest-failure handling. Returns `{"proposed_batches": [...],
"failed": [...]}`.

```python
def finalize_company_review(payload: dict) -> dict:
    """Called only once the operator approves a propose_company_review
    Pending Approval, with the operator's own decision (outcome/parent_
    name/parent_kind) already merged into payload by the router (below) --
    REQ-SB-76-US-01-T02, ADR-057 Decisions 3/7/8. Branches on payload
    ["outcome"] ("customer" | "partner" | "affiliate" | "merge") -- ONE
    registered handler, not four, since exactly one Pending Approval
    record ever exists per company. A parent_name the server cannot
    independently confirm is a real, existing Customer/Partner of the
    claimed parent_kind raises before any write happens -- the existing
    call order (handler runs BEFORE resolve_pending_approval) already
    leaves the record "pending", never silently half-applied."""
```

- **Customer** — `customer_hub_linking.ensure_customer_hub_note(company)`
  (UNCHANGED), then `_apply_company_to_threads(thread_paths, company,
  "customer")`.
- **Partner** — `partner_hub_linking.ensure_partner_hub_note(company)`
  (UNCHANGED), then `_apply_company_to_threads(thread_paths, company,
  "partner")`.
- **Affiliate** — ensures the entity (Customer or Partner, per `payload
  ["parent_kind"]` naming which NEW-entity kind the operator chose) exactly
  as above, then `vault_writer.upsert_frontmatter_key(<entity path>,
  "affiliate_of", payload["parent_name"])` (already-existing generic
  primitive, zero new write code), then `_apply_company_to_threads`.
- **Merge** — validates `parent_name`/`parent_kind` are a real, existing
  entity; `_apply_company_to_threads(thread_paths, parent_name,
  parent_kind)` routes every batch Thread to the CANONICAL entity (no new
  entity ever created for `company`); if `company` already has a real prior
  entity of its own (`customer_concept_file_exists`/`hub_note_exists`/
  `partner_hub_note_exists`), calls `partner_hub_linking.retarget_company_
  references(company, <company's own real kind>, parent_name, parent_kind)`
  (below) to redirect every OTHER vault note's reference, then archives the
  now-unreferenced duplicate via `vault_writer.move_okf_directory` (OKF-
  shaped) or `vault_writer.move_note_and_attachments` (legacy-flat-shaped)
  to `Work/Archive/Customers/` — reusing `finalize_customer_archival`'s own
  exact call shape as a plain same-module function call (`REQ-SB-74-US-01`'s
  own archival-candidate mechanism, `ADR-055` Decision 4), never a new
  archival primitive. **Disclosed, not fixed by this pass:** a Partner-
  shaped duplicate is correctly retargeted but its own now-unreferenced
  flat file is left in place, untouched — no `Work/Archive/Partners/` root
  is provisioned yet. See [ADR-057](ADR.md) Consequences.

### `_apply_company_to_threads(thread_paths, target_name, target_kind)` (new, shared by all four outcomes above)

For each Thread, freshly reads its CURRENT `customer`/`partner`
frontmatter AT FINALIZE TIME (never snapshotted into the proposal payload
— `ADR-057` Decision 8): if still unset/`"Unsorted"`, writes `target_name`
to the primary field plus the `target_kind/<slug>` tag (Scenarios 3-6/10's
"primary write" path, mirroring `finalize_customer_backfill_routing`'s own
tag-correction shape); if ALREADY set to a DIFFERENT real company, leaves
the primary field byte-for-byte untouched and instead adds an ADDITIVE
`target_kind/<slug>` tag plus regenerates that Thread's own `## Related`
section via `email_classification.build_thread_related_wikilinks` directly
(the SAME composition primitive `populate_thread_related_links` itself
calls — never that whole-vault batch Job, which has no per-Thread entry
point), written via `vault_writer.replace_body_section(concept_path, "##
Related", ..., caller="librarian_housekeeping.populate_thread_related_
links")` — the SAME already-registered `section_ownership.py` caller id
(Scenario 9).

### `partner_hub_linking._retag_company_references()` / `retarget_company_references()` — generalized retag-scan primitive

`migrate_customer_to_partner`'s own Step 2 (the generic vault-wide retag
scan, `ADR-009` point 4/`ADR-012`) is extracted into a new, parameterized
internal helper:

```python
def _retag_company_references(
    old_name: str, old_kind: str, new_name: str, new_kind: str,
) -> list[dict]:
    """old_kind/new_kind in {"customer", "partner"} -- the SAME two-signal
    scan (frontmatter-field-equals-old_name / inline **<Old label>:**
    [[old hub stem]] body wikilink) and the SAME four per-note rewrite
    primitives (rename_frontmatter_key/remove_frontmatter_key_if_present/
    swap_tag/replace_body_line) migrate_customer_to_partner already uses,
    generalized from hardcoded Customer->Partner values to the four
    parameters -- REQ-SB-76-US-01-T04, ADR-057 Decisions 5/6. The
    affiliate_of-drop step is REMOVED (Partner now legitimately carries
    affiliate_of -- ADR-057 Decision 4); an entity's own affiliate_of
    value, real or empty, always carries forward untouched."""
```

`migrate_customer_to_partner(customer_name)` becomes a thin wrapper —
`_retag_company_references(customer_name, "customer", customer_name,
"partner")` plus its own Step 1 — behaviourally IDENTICAL to today, zero
external contract change, zero call-site changes. Step 1 itself gains an
OKF-directory-first branch, tried BEFORE the existing legacy-flat check
(mirrors `resolve_thread_directory`'s own "directory-shaped scan first,
flat-note scan second" ordering, `ADR-052`): if `vault_writer.customer_
concept_file_exists(customer_name)`, the WHOLE OKF directory moves via
`vault_writer.move_okf_directory(vault_writer.customer_directory_paths
(customer_name)["directory"], vault_writer.partner_hub_note_path
(customer_name).parent)` — the exact already-`Accepted` `REQ-SB-74-US-01`
primitive, reused verbatim. A new, thin, PUBLIC sibling —

```python
def retarget_company_references(
    old_name: str, old_kind: str, new_name: str, new_kind: str,
) -> list[dict]:
    """One-line pass-through to _retag_company_references -- the Merge
    outcome's own entry point (ADR-057 Decision 7), supporting a
    same-kind (Customer->Customer/Partner->Partner) or cross-kind name
    change alike, never a new, third move/retag primitive."""
    return _retag_company_references(old_name, old_kind, new_name, new_kind)
```

### `affiliate_of` — restored onto Customer's current OKF shape, added to Partner's shape

`vault_writer.build_customer_concept_frontmatter` gains `"affiliate_of":
""` (one additive dict key — flows through `create_customer_directory_
baseline`/`ensure_customer_directory_baseline` with zero further code
change, since both already iterate whatever this function returns).
`vault_writer._PARTNER_HUB_NOTE_BASELINE_KEYS` gains `"affiliate_of"`
(`("type", "partner", "tags", "affiliate_of")`); `create_partner_hub_note_
baseline`/`ensure_partner_hub_note_baseline_frontmatter` both gain the same
`"affiliate_of": ""` default, mirroring the legacy Customer hub note's own
4-key shape. **Narrowly, additively revises `ADR-009` point 3 only** — see
[ADR-057](ADR.md) Decision 4 and `ADR-009`'s own updated `**Status:**` line.
Setting a REAL value reuses the already-existing generic `vault_writer.
upsert_frontmatter_key`, zero new write primitive.

### Approve endpoint — additive decision body (`pending_approvals_router.py`)

```python
class CompanyReviewDecisionBody(BaseModel):
    outcome: str
    parent_name: str | None = None
    parent_kind: str | None = None


@router.post("/{approval_id}/approve")
def approve_pending_approval(
    approval_id: str, decision: CompanyReviewDecisionBody | None = None,
) -> dict:
    ...
    elif record["action_id"] in _APPROVAL_HANDLERS:
        effective_payload = {**record["payload"], **(decision.model_dump() if decision else {})}
        result = _APPROVAL_HANDLERS[record["action_id"]](effective_payload)
    ...
```

Every one of the other 8 registered handlers keeps its exact existing
one-argument `(payload: dict) -> dict` signature, completely unaffected —
`ADR-057` Decision 3. `_APPROVAL_HANDLERS["propose_company_review"] =
finalize_company_review` (new entry). `Decline` is untouched — `POST
/pending-approvals/{id}/decline` needs no body for this or any proposal
kind, since it never invokes a handler (Scenario 7).

### `GET /pending-approvals/known-companies` (new)

`{"customers": [<name>, ...], "partners": [<name>, ...]}`, composed from
`vault_writer.list_customer_folders()` + `vault_writer.list_known_
partners()` — both already-existing, vault-derived enumerations, zero new
`vault_writer.py` code. Called fresh by the frontend on every Approvals
page load (never baked into a proposal's own stored payload, which would
go stale the moment any OTHER Company Review batch resolves first).

### Frontend — `MyDayApprovalsPage.tsx` branches on `action_id`, new decision control

`PendingApproval` (`pendingApprovalsApiClient.ts`) gains an additive
`payload: Record<string, unknown> | null` field (already present on the
real API response — `pending_approval_registry.py` already stores/returns
it — simply not yet typed). `approvePendingApproval(id: string, decision?:
{ outcome: string; parent_name?: string; parent_kind?: string }):
Promise<PendingApproval>` gains an optional second parameter, POSTed as the
JSON body only when supplied — every OTHER existing call site (`handleApprove
(id)`, unchanged) keeps sending no body, zero behavior change. New
`fetchKnownCompanies(): Promise<{ customers: string[]; partners: string[] }>`
composes the new endpoint above.

`MyDayApprovalsPage.tsx`'s render loop branches: `item.action_id ===
"propose_company_review"` renders a NEW decision-control component (five
buttons — Customer/Partner/Affiliate/Merge/Decline — with the Affiliate
button revealing a parent picker plus a Customer-or-Partner kind choice,
and the Merge button revealing a parent picker only, both pickers sourced
from `fetchKnownCompanies()`, using the app's own existing form/control
vocabulary per this story's own operator-approved "no `/design` pass, build
directly" override, see the story's own `## Notes`) in place of the generic
`.item-row-actions` Approve/Decline pair; every OTHER `action_id` renders
the EXISTING generic pair completely unchanged (Decline, for THIS proposal
kind too, reuses the existing `declinePendingApproval(id)` call verbatim —
no new Decline mechanism).

### Section-ownership, scheduling & endpoint

No new `section_ownership.py` entry — `_apply_company_to_threads`'s own
`## Related` write registers under the SAME already-existing `librarian_
housekeeping.populate_thread_related_links` caller id (above). `POST
/poc/librarian-propose-company-review` (new, `email_poc_router.py`, mirrors
the existing `/poc/librarian-*` convention) runs `propose_company_review()`.
Deliberately NOT added to `run_housekeeping_pass()`'s own scheduled chain —
manually-triggered only, mirroring `ADR-055`'s own explicit precedent.

### Disclosed, not fixed by this pass

Same re-proposal risk `ADR-055`'s own Consequences already disclosed for
`propose_customer_backfill` (a second manual trigger before an
already-created batch resolves re-proposes the same still-unconfirmed
mentions into a new batch) applies identically here, mitigated identically
by `dedupe_key`. A Partner-shaped Merge duplicate is retargeted but not
archived (no `Work/Archive/Partners/` root exists yet). See
[ADR-057](ADR.md) Consequences for both, plus the permanent Partner
shape asymmetry (natively-created Partner stays flat-file; a migrated-or-
merged-in Partner is directory-shaped).

## People Notes Retroactively Linked to Company/Partner (`REQ-SB-77-US-01`, no new ADR — composes [ADR-009](ADR.md)/`REQ-SB-10-US-01`)

Closes `ESC-057`'s own real, disclosed gap: the matched-company linking
mechanism itself (`people_extraction.ensure_person_note`, `Done`,
`REQ-SB-10`/`ADR-009`) already re-derives a Person's company match on
EVERY call and already writes the real `**Customer:**`/`**Partner:**
[[Hub]]` wikilink the moment a match is confirmed — this story closes the
REACH gap only (the mechanism was reachable exclusively via the
POC-prefixed `POST /poc/retrofit-people-from-emails`), never rebuilds the
mechanism itself.

### New: `people_extraction.relink_people_for_thread_paths(thread_paths: list[str]) -> list[dict]`

A bounded, per-Thread sibling of the already-existing whole-vault
`retrofit_people_from_emails()` — for each given Thread's own
`messages/*.md` raw notes (the same `sender`/`sender_email` frontmatter
shape `librarian_housekeeping._thread_full_content` already reads),
dedupes by email within this one call (mirrors `retrofit_people_from_
emails`'s own dedup exactly), and calls the existing `ensure_person_note
(sender_name, sender_email)` — zero new linking primitive. Lives in
`people_extraction.py` (the composing module), not `librarian_
housekeeping.py` — mirrors `ensure_person_note_for_captured_email`'s own
"one bounded per-event wrapper around the same shared operation" shape.

### Two real trigger points (Scenario 6), not one

1. **Instant, on a company's status changing.** `librarian_housekeeping.
   finalize_company_review` (`Done`, `REQ-SB-76-US-01-T06`) is
   retargeted: its own existing 4-branch body (Customer/Partner/
   Affiliate/Merge) is renamed in place to a private `_finalize_company_
   review_outcome(payload) -> dict` — zero behavior change to any
   branch — and a new, thin public wrapper composes it:

   ```python
   def finalize_company_review(payload: dict) -> dict:
       result = _finalize_company_review_outcome(payload)
       people_extraction.relink_people_for_thread_paths(payload["thread_paths"])
       return result
   ```

   ONE call, not four — `thread_paths` is identical across all four
   outcomes, and every branch already creates/confirms its own target
   entity before returning, so by the time this wrapper's second line
   runs, `find_matching_customer`/`find_matching_partner` can always see
   the freshly-created/confirmed entity. The existing "raises before any
   write" honest-failure contract is preserved by construction — an
   `_finalize_company_review_outcome` raise propagates straight through
   the wrapper, before the relink call ever runs. `librarian_
   housekeeping.py` gains one new import, `people_extraction` —
   business-to-business composition, reusing `people_extraction.py`'s own
   already-established "intentional, permitted horizontal call within the
   business layer, not an `ADR-003` boundary violation" precedent a
   second time.
2. **Scheduled, self-healing catch-all.** `REQ-SB-79-US-01`'s new `run_
   company_partner_building_pass()` (below) additionally calls the
   ALREADY-EXISTING, already-`Done` `people_extraction.retrofit_people_
   from_emails()` on its own 6-hour default schedule — zero new mechanism
   for this half, pure wiring.

### Real cross-story dependency (architect finding, for the decomposer)

Trigger point 1 needs nothing from `REQ-SB-79` — `finalize_company_review`
already exists today (`Done`). Trigger point 2 needs `REQ-SB-79-US-01`'s
own new `run_company_partner_building_pass()` function to exist FIRST —
there is no scheduled Company/Partner pipeline capability to hook into
before that story lands. **The decomposer should split `REQ-SB-77-US-01`'s
Scenario-6 work into at least two backend tasks: one for the instant hook
(no cross-story dependency), one for the scheduled self-heal wiring
(`depends_on` a `REQ-SB-79-US-01` task — specifically the one that creates
`run_company_partner_building_pass()`), and the product-owner should
sequence the two stories' sprints accordingly (same sprint, or
`REQ-SB-79` first with a recorded `depends_on_sprints` edge) — never route
the scheduled-wiring task around this real dependency.**

### Why no new ADR

Every real decision here is composition of already-`Accepted` patterns:
`ensure_person_note` (`ADR-009`) is reused verbatim, `relink_people_for_
thread_paths` introduces no new linking primitive (only a narrower,
bounded input to the same operation `retrofit_people_from_emails` already
performs), and both trigger points are plain function calls into
already-existing (or, for `run_company_partner_building_pass`,
already-architected-below) capabilities. No new tool, framework, or
structural module boundary.

## Pending Approvals — Grouped, Color-Coded Review (`REQ-SB-78-US-01`, no new ADR — composes [ADR-018](ADR.md)/[ADR-021](ADR.md)/[ADR-057](ADR.md))

### Grouping key — `action_id`, not `agent_id`

`action_id` is the real "proposal type" the requirement's own language
("approve all requests for a certain type") asks for — a single agent
identity (e.g. the pre-`REQ-SB-79` `librarian-housekeeping`, or its two
post-split successors below) can own several distinct `action_id`s
(`propose_customer_backfill_routing`, `propose_customer_archival_
candidate`, `propose_company_review`, `propose_librarian_company_link`),
so grouping by `action_id` gives a materially finer, more useful sweep
than grouping by agent alone. No new backend field — `GET
/pending-approvals` already returns `action_id` on every record.

### Label + color — a new, small, static frontend-only lookup table

```ts
// src/frontend/src/features/agents-map/pendingApprovalGroups.ts (new)
const KNOWN_GROUPS: Record<string, { label: string; colorClass: string }> = {
  propose_company_review:             { label: 'Company Review',         colorClass: 'group-color-1' },
  propose_customer_backfill_routing:  { label: 'Customer Backfill',      colorClass: 'group-color-2' },
  propose_customer_archival_candidate:{ label: 'Customer Archival',      colorClass: 'group-color-3' },
  propose_librarian_company_link:     { label: 'Company Link',           colorClass: 'group-color-4' },
  route_thread_to_project:            { label: 'Thread Routing',         colorClass: 'group-color-5' },
  propose_recurring_pipeline:         { label: 'Recurring Pipeline',     colorClass: 'group-color-6' },
  propose_cross_cutting_update:       { label: 'Cross-Cutting Update',   colorClass: 'group-color-7' },
  propose_background_amendment:       { label: 'Background Amendment',   colorClass: 'group-color-8' },
  propose_new_top_level_area:         { label: 'New Top-Level Area',     colorClass: 'group-color-9' },
  hermes_vault_write:                 { label: 'Hermes Write',           colorClass: 'group-color-10' },
  acknowledge_classification_failure: { label: 'Classification Failure', colorClass: 'group-color-11' },
};
const OTHER_GROUP = { label: 'Other', colorClass: 'group-color-other' };
```

Every `action_id` NOT in `KNOWN_GROUPS` (including a `null` background-
trigger `action_id`, and every migrated mutating Skill id —
`run_capture_now`/`pause_schedule`/`rebuild_person_note`/`build_
knowledge`/etc. — none named individually here, since a Skill-approval's
own real "type" is better read from its own `description` text than an
invented duplicate label) falls into the ONE `OTHER_GROUP` catch-all
(Scenario 4) — correct and forward-compatible by construction: a
brand-new `action_id` a future story adds needs no code change here to
stay visibly, honestly grouped; only an OPTIONAL new `KNOWN_GROUPS` entry
to earn its own named section. `.group-color-N` classes are new, small,
`--color-accent`-family CSS custom-property variants added to the
frontend's own stylesheet (mirrors the existing `--node-color`/`--hub-
color` per-item CSS-custom-property pattern the Agents Map canvas already
uses) — never a per-agent `agent_visual_registry` color (that registry
defaults every agent to `None`/no override, so it cannot structurally
guarantee a distinct color per GROUP the way a dedicated, complete static
lookup table can).

### Empty-group suppression / catch-all rendering (Scenarios 3/4)

`MyDayApprovalsPage.tsx`'s render loop groups the already-fetched `items`
array by `action_id` (via the lookup table above, `Other` for a miss),
THEN renders only the groups with `items.length > 0` — never a hardcoded
static group list.

### Bulk-approve eligibility (Scenario 7) — reuses the existing per-item branch condition, generalized

```ts
const BRANCHING_DECISION_ACTION_IDS = new Set([COMPANY_REVIEW_ACTION_ID]); // today: exactly one
```

A rendered group offers its own bulk-approve control if and only if EVERY
item currently inside it has an `action_id` NOT in `BRANCHING_DECISION_
ACTION_IDS` — computed per rendered group (not per group KEY), so even
the heterogeneous `Other` catch-all is handled correctly by this same one
check, with zero special-casing. Bulk-approve itself is a plain frontend
loop calling the ALREADY-EXISTING `approvePendingApproval(id)` (no
decision body) once per item in the group, refreshing once at the end —
zero new backend endpoint, zero new backend capability, mirrors
`handleApprove`'s own existing per-item call verbatim. A future new
branching-decision `action_id` needs to be added to BOTH this set AND
`MyDayApprovalsPage.tsx`'s own existing per-item render branch — the
same "each new decision control names itself" precedent the Company
Review control already established, not a new gap this story introduces.

### Why no new ADR

Every mechanism above is a plain composition of already-`Accepted`
primitives: no new backend field, no new endpoint, no new linking/write
primitive — bulk-approve loops the existing single-item Approve endpoint
verbatim, grouping/color reuses fields `GET /pending-approvals` already
returns plus a new, purely presentational frontend lookup table. No new
tool, framework, or structural module boundary.

## The Librarian — Two Sub-Pipelines: Threads Cleaning, Company and Partner Building (`REQ-SB-79-US-01`, see [ADR-058](ADR.md))

Splits the single shared `librarian-housekeeping` identity into two real,
independently-schedulable Agent-tier identities under the SAME
already-existing "Librarian" Section — no new Section, no new Agent per
Job (5 agents), per the operator's own explicit "2 Pipelines, not 5"
direction. Full architectural reasoning, every alternative considered,
and every consequence: [ADR-058](ADR.md).

### Two new Agent identities, same Section, no new Section

- `agent_registry.create_agent("Threads Cleaning", type="worker",
  settings=[...])` → id `threads-cleaning`.
- `agent_registry.create_agent("Company and Partner Building",
  type="worker", settings=[...])` → id `company-and-partner-building`.
- Both `section_registry.set_agent_section(<id>, "librarian")` — the SAME
  already-existing Section (Constraint).

### `agent_registry.py` gains its first "retire without delete" primitive

No rename/delete capability exists for an agent identity today, and
building one is out of this story's own scope. A CREATED agent's own
record (never a `_SEED_AGENTS` entry) gains an additive `retired: bool`
key (default `False`); `retire_agent(agent_id: str) -> bool` sets it
(idempotent no-op if already retired, `False` for an unknown or
`_SEED_AGENTS` id — a shipped, static agent can never be retired);
`list_agents(include_retired: bool = False)` gains the optional filter
(default excludes retired agents — the shape `GET /agents`/the Agents Map
already calls); `get_agent(agent_id)` is UNCHANGED — always resolves ANY
agent regardless of `retired`, so every already-existing Pending Approval/
Agent History record's own stored `agent_id` keeps resolving a real,
honest `agent_name` forever (Scenario 6). The already-existing
`librarian-housekeeping` identity is retired via this new primitive,
idempotently, at every app start — self-healing, mirroring this
codebase's own dominant "idempotent startup bootstrap" convention rather
than a one-off migration script (`MEMORY.md` — API-first, no script
workarounds).

### Job → new-owning-agent mapping (confirmed by direct reading)

| Job | New owning agent | Pending-Approval `agent_id` change? |
|---|---|---|
| `rename_threads` | `threads-cleaning` | none — creates zero Pending Approvals |
| `link_thread_messages` | `threads-cleaning` | none |
| `backfill_files` | `threads-cleaning` | none |
| `populate_thread_related_links` | `threads-cleaning` | none |
| `backfill_company_folders` (+ `_create_librarian_company_link_proposal`) | `company-and-partner-building` | `"librarian-housekeeping"` → `"company-and-partner-building"` (2 sites: the function's own default `requesting_agent_id` param; the one real call site inside `backfill_company_folders`) |
| `propose_customer_backfill` | `company-and-partner-building` | same |
| `propose_customer_archival_candidates` | `company-and-partner-building` | same |
| `propose_company_review` | `company-and-partner-building` | same |
| `finalize_company_review` / `finalize_customer_backfill_routing` / `finalize_customer_archival` / `finalize_librarian_company_link` | (no `agent_id` of their own — dispatched by `action_id`) | n/a |

Confirmed by direct reading: ALL FIVE literal
`agent_id="librarian-housekeeping"`-shaped call sites in `librarian_
housekeeping.py` belong to Company-and-Partner-Building's own four Jobs
— the four Threads Cleaning jobs create zero Pending Approvals and need
no per-call-site identity edit at all, only their new schedule/Skill
grant (below).

### Orchestrating capability split — `run_housekeeping_pass()` → two siblings

```python
def run_threads_cleaning_pass() -> dict:
    """Renamed from run_housekeeping_pass (REQ-SB-79-US-01) -- now chains
    ONLY the 4 Threads Cleaning jobs, in the SAME fixed order (rename
    first), on Threads Cleaning's own independent schedule. Behaviourally
    identical for these 4 jobs (Scenario 2/7) -- backfill_company_folders
    moves to its own sibling below."""
    return {
        "rename_threads": rename_threads(),
        "link_thread_messages": link_thread_messages(),
        "backfill_files": backfill_files(),
        "populate_thread_related_links": populate_thread_related_links(),
    }


def run_company_partner_building_pass() -> dict:
    """New (REQ-SB-79-US-01) -- Company and Partner Building's own
    scheduled capability. Wraps backfill_company_folders() (the ONE Job
    of this pipeline previously on run_housekeeping_pass's shared
    schedule, Scenario 3) plus people_extraction.retrofit_people_from_
    emails() (REQ-SB-77-US-01 Scenario 6b's own self-healing catch-all --
    already-existing, already-Done, zero new mechanism, pure wiring).
    propose_customer_backfill/propose_customer_archival_candidates/
    propose_company_review stay individually, manually triggered via
    their own already-existing /poc/* endpoints -- never folded into
    this scheduled wrapper (ADR-055/057's own explicit 'manually-
    triggered only' precedent, untouched)."""
    return {
        "backfill_company_folders": backfill_company_folders(),
        "retrofit_people_from_emails": people_extraction.retrofit_people_from_emails(),
    }
```

`librarian_housekeeping.py` gains one new import, `people_extraction`
(business-to-business composition, see "People Notes Retroactively
Linked to Company/Partner" above).

### Skill / grant / schedule split (`skill_tools.py`, `skill_registry.py`, `main.py`)

- `skill_tools.SKILLS["run_housekeeping_pass"]` is REPLACED by two catalog
  entries, `"run_threads_cleaning_pass"` / `"run_company_partner_building_
  pass"` (same `"mutates": True`, `"tool": "Vault"` shape), each with its
  own `@mcp_server.tool()` thin wrapper delegating to the two new
  orchestrators above.
- `skill_registry._SKILL_HANDLERS` / `_MIGRATION_GRANT_SEED` gain the
  matching two entries, granted to `threads-cleaning` /
  `company-and-partner-building` respectively, REPLACING the single
  `"run_housekeeping_pass": ["librarian-housekeeping"]` line — mirrors
  this seed dict's own established "reuse this same mechanism for a
  genuinely new grant" precedent (`ADR-046`/`ADR-049`).
- `main.py`'s lifespan: `ensure_librarian_agent_and_section()` is renamed/
  generalized to `ensure_librarian_agents_and_section()` — idempotent-
  checks and creates BOTH new agents (mirrors the existing per-agent
  existence-check-first shape, applied twice), and additionally,
  unconditionally, idempotently RETIRES `"librarian-housekeeping"`
  (`agent_registry.retire_agent`, a no-op once already retired) and
  removes its own now-stale schedule entry (`agent_schedule_registry.
  remove_schedule("librarian-housekeeping", "run_housekeeping_pass")`,
  already idempotent/safe if absent) — a real, self-healing startup step,
  never a one-off migration script. `create_or_update_schedule` is called
  twice, once per new `(agent_id, capability_id)` pair, both defaulting to
  the SAME 6-hour interval `REQ-SB-72-US-01` originally chose —
  independently adjustable from the first tick onward (Scenario 3).

### `email_poc_router.py`

`/poc/librarian-run-housekeeping-pass` is REPLACED by `/poc/librarian-run-
threads-cleaning-pass` / `/poc/librarian-run-company-partner-building-
pass`. Every per-Job endpoint (`/poc/librarian-rename-threads`,
`-link-thread-messages`, `-backfill-files`, `-populate-related`,
`-backfill-company-folders`, `-propose-customer-backfill`,
`-propose-company-review`) is UNCHANGED — same function, same route.

### Confirmed needing ZERO change

- `section_ownership.py`'s `_CALLER_ALLOW_LISTS` — keyed by dotted
  FUNCTION name (`"librarian_housekeeping.backfill_files"` etc.), never
  by agent identity.
- `email_classification.py` — only a comment references the module; no
  functional coupling to any agent_id.
- `pending_approvals_router.py`'s `_APPROVAL_HANDLERS` — dispatches by
  `action_id`, never `agent_id`; all 4 registered Librarian-family
  handlers are unaffected.

### Scenario 6 (no orphaned/misattributed historical records) — satisfied by construction, not by rewriting history

`librarian-housekeeping`'s own already-existing Pending Approval/Agent
History records are NEVER touched or reclassified — `get_agent
("librarian-housekeeping")` keeps resolving correctly (the `retired` flag
only affects `list_agents()`'s default listing, never `get_agent()`), so
`_resolved()` (`pending_approvals_router.py`) and every agent-history-name
lookup keep returning the real, honest, AT-THE-TIME name for every old
record, forever.

Full architectural reasoning, every alternative considered, and every
consequence: [ADR-058](ADR.md).

## Authentication & Authorisation

[Describe the auth approach — likely none/local-only for a single-user tool, to be
confirmed at `/plan-tasks`.]

## Local Development

Backend (from `src/backend`):

```
.venv\Scripts\pip.exe install -r requirements.txt   # first time / after changes
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
.venv\Scripts\python.exe -m pytest -q
```

Frontend (from `src/frontend`, after dot-sourcing `tools/use-node.ps1` once per
shell session so `npm`/`npx` resolve to the portable toolchain):

```
. ..\..\tools\use-node.ps1
npm install     # first time / after dependency changes
npm run dev
```

No admin rights are available on the development host, so neither toolchain is
system-installed — see [ADR-001](ADR.md) and [ADR-002](ADR.md).

**Scheduler runs automatically with the app (see [ADR-005](ADR.md)):** once
`app/scheduling/` is wired into `app/main.py`'s `lifespan`, every
`uvicorn app.main:app --reload` start (including each dev-server reload) fires
one real capture run immediately, then continues on an hourly interval for as
long as that process stays up. This hits the real Outlook/Compass integration
the same way `POST /poc/classify-emails` already does — be aware of this when
restarting the dev server repeatedly during REQ-SB-07 work.

Vault path is already configurable via `VAULT_PATH` in `.env`
(`app/config.py::Settings.vault_path`, used by every capture pipeline and,
as of `REQ-SB-01-US-01`, the vault indexing layer — see [ADR-024](ADR.md)).
Correcting a stale note left from before that config value existed in code.

## External Services

Hermes (MCP-based multi-channel communication) — planned integration, not yet
built.
