---
id: REQ-SB-73-US-01
title: Bidirectional Thread ↔ Message Linking (Retrofit + Rename-Safe)
requirement_ids: [REQ-SB-73]
requirement_section: "REQ-SB-73: Bidirectional Thread ↔ Message Linking (Retrofit + Rename-Safe)"
phase: P1
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-054 created) — standing architect-level review item, unresolved by the coder, see REVIEW-QUEUE.md"
sprint: "SPRINT-067"
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-73-US-01 — Bidirectional Thread ↔ Message Linking (Retrofit + Rename-Safe)

## Story

**As a** Second Brain operator
**I want** every real Thread note and its own raw `RawMessage` notes to carry
a real, Obsidian-visible link to each other in both directions — a Thread's
own `## Messages` section listing every message under it, and every message
carrying a `thread:` frontmatter backlink that stays correct even after the
Librarian renames the Thread — retrofitted across the whole real corpus and
self-healing going forward
**So that** the link graph, backlinks panel, and graph view actually show
the real relationship between a Thread and its own raw messages, instead of
that relationship existing only as invisible filesystem nesting

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-73: Bidirectional Thread ↔ Message
  Linking (Retrofit + Rename-Safe)*. Raised 2026-08-19, operator: "Emails are
  not linked to threads" — confirmed live against the real vault before
  scoping (a raw message note's frontmatter carries only `conversation_id`/
  `message_id`/`sender`/`subject`/`received`, no back-reference; a Thread's
  own `## Related` never lists its own messages). The retrofit-vs-routing
  priority ("do the linking retrofit first, keep routing manual for now")
  and the rename-safety design (fan-out on rename vs. one-directional-only)
  were each proposed with named tradeoffs and confirmed directly by the
  operator turn-by-turn, including the operator's own explicit prompt to
  think through the Librarian's rename interaction before scoping this at
  all — the fan-out design (below) is a direct response to that prompt, not
  an unprompted addition. No `<!-- Draft -->` marker on this requirement.
- **This story builds a new Job under the ALREADY-EXISTING "Librarian"
  Section/`librarian-housekeeping` Agent `REQ-SB-72-US-01` created — no new
  Section, no new Agent.** Directly confirmed by reading the real, shipped
  `app/business/pipelines/librarian_housekeeping.py` (`REQ-SB-72-US-01`,
  `Done`, `SPRINT-063`): it already houses `rename_threads()`,
  `backfill_files()`, `populate_thread_related_links()`,
  `backfill_company_folders()`, and the orchestrating `run_housekeeping_
  pass()` that runs them in a fixed order (rename first, so the later Jobs
  operate on each Thread's own final, current directory). This story adds
  ONE more Job, `link_thread_messages()`, to that same module and that same
  orchestration chain — mirroring exactly how `REQ-SB-72-US-01-T04`
  (`backfill_files`) added a Job to the Librarian Section without inventing
  a new one, the PRD's own explicitly named precedent.
- **The rename-staleness problem this story's own fan-out design solves is
  real and already-shipped, not hypothetical** — directly confirmed by
  reading `rename_threads()` (`REQ-SB-72-US-01-T03`, `ADR-049` Decision 2,
  already `Done`): it renames a Thread's WHOLE directory (concept file +
  everything under it, via `vault_writer.rename_thread_directory`'s atomic
  move) but touches nothing INSIDE `messages/` — a message's own `thread:`
  field, once written, is not itself updated by that existing Job today.
  This is the exact same class of staleness `ADR-052` already had to fix
  once for a different lookup path (named directly in the PRD). This
  story's resolution — extending `rename_threads()` itself to fan out
  immediately after each successful move, in the SAME operation — is a
  bounded addition to that already-shipped, currently-running function, not
  a new mechanism.
- **Real code read directly to ground this story, not assumed:**
  - `app/data_access/vault_writer.py::raw_message_note_path` /
    `create_raw_message_note` — confirmed live: a `RawMessage` note's own
    frontmatter today carries exactly `type`/`conversation_id`/
    `message_id`/`sender`/`sender_email`/`subject`/`received` — no `thread:`
    field exists yet. Its own filename (`<received[:10]>-<hash8(message_
    id)>.md`) is deterministic from `message_id` alone and is never renamed
    by anything in this codebase — confirmed by reading every write path —
    which is exactly why the Thread → Messages direction (`## Messages`) is
    safe by construction across a Thread rename with no extra handling, per
    the PRD's own text.
  - `app/data_access/vault_writer.py::list_thread_notes` /
    `resolve_thread_directory` — the existing primitives this story's own
    `link_thread_messages()` Job composes to enumerate every real Thread and
    its own CURRENT `messages/` directory, unchanged, mirroring every other
    Job in `librarian_housekeeping.py`.
  - `app/data_access/section_ownership.py::_CALLER_ALLOW_LISTS` — confirmed
    live: a deny-by-default, per-calling-function registry already carries
    entries for `librarian_housekeeping.backfill_files` (`{"## Files"}`) and
    `librarian_housekeeping.populate_thread_related_links` (`{"## Related"}`)
    — this story's own new `## Messages` writer needs its own new entry in
    this SAME registry, mirroring that exact precedent (left to the
    architect — see `## Notes`).
  - `app/business/pipelines/librarian_housekeeping.py::run_housekeeping_
    pass` — confirmed live: the fixed Job-chain order is `rename_threads()`
    → `backfill_files()` → `populate_thread_related_links()` →
    `backfill_company_folders()`. `link_thread_messages()` needs a place in
    (or alongside) this chain — a real, disclosed sequencing question left
    to the architect (see `## Notes`), since unlike the three later Jobs it
    reads/writes on BOTH sides of the Thread ↔ Message relationship, not
    just the Thread's own concept file.
  - Real corpus counts, confirmed live 2026-08-19 (grown from `REQ-SB-72`'s
    own 2026-08-18 count of 127/252, ordinary organic capture growth, not a
    discrepancy): 137 real Thread directories, 257 real raw message notes
    under `Work/Threads/`.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: A Thread's own ## Messages section lists a working wikilink to every raw message under it

```gherkin
Given a real Thread directory with one or more real raw message notes under
    its own current messages/ directory
When the Librarian's link_thread_messages() Job processes that Thread
Then the Thread's own concept file carries a ## Messages section listing one
    "- [[<message-stem>]]" bullet per raw message currently under messages/,
    every wikilink resolving to a real, existing note
```
<!-- AC-ID: REQ-SB-73-US-01-AC-01 -->

### Scenario 2: ## Messages is fully regenerated each pass, never incrementally patched

```gherkin
Given a real Thread's ## Messages section already lists every raw message
    that existed under its own messages/ directory at the time of the last
    pass, and a further real message has since been captured under that SAME
    Thread's messages/ directory
When the Librarian's link_thread_messages() Job processes that Thread again
Then ## Messages is fully rebuilt to list every message currently under
    messages/, including the newly-arrived one, proving the section is a
    mechanical, from-scratch rollup — mirroring ## Glimpse's own existing
    "regenerated each pass, never incrementally patched" contract — not an
    incremental append
```
<!-- AC-ID: REQ-SB-73-US-01-AC-02 -->

### Scenario 3: Every raw message note carries a thread: frontmatter backlink resolving to its owning Thread's current file

```gherkin
Given a real raw message note under a real Thread's own messages/ directory
    with no thread: frontmatter field yet
When the Librarian's link_thread_messages() Job processes that Thread
Then the message note's own frontmatter gains a real thread: wikilink field
    that correctly resolves to its owning Thread's CURRENT concept file
```
<!-- AC-ID: REQ-SB-73-US-01-AC-03 -->

### Scenario 4: Renaming a Thread updates every one of its own messages' thread: field in the same pass — zero staleness

```gherkin
Given a real Thread's own messages already carry a correct thread: field
    pointing at the Thread's own CURRENT slug
When the Librarian's existing rename_threads() Job renames that Thread's
    whole directory to a new human-readable stem
Then every raw message note under that Thread's own (now-renamed)
    messages/ directory has its own thread: field rewritten to the new slug,
    in that SAME rename_threads() run — no message is ever left pointing at
    the Thread's own stale, pre-rename slug, even momentarily
```
<!-- AC-ID: REQ-SB-73-US-01-AC-04 -->

### Scenario 5: link_thread_messages() self-heals a message whose thread: field is missing or points at a stale slug

```gherkin
Given a real raw message note whose own thread: field is either absent
    (never linked) or still points at a Thread's own stale, pre-rename slug
    (e.g. renamed by some path other than Scenario 4's own live fan-out)
When the Librarian's link_thread_messages() Job processes that message's
    owning Thread
Then the message note's own thread: field is written or corrected to the
    Thread's own CURRENT slug — the same self-healing safety net this Job
    provides for the one-time retrofit across the full real corpus (137
    Threads / 257 messages) and for anything a future capture pass misses
```
<!-- AC-ID: REQ-SB-73-US-01-AC-05 -->

### Scenario 6: Re-running link_thread_messages() against an already-fully-linked corpus is a true no-op

```gherkin
Given every real Thread's ## Messages section and every real raw message's
    thread: field are already fully, correctly populated
When the Librarian's link_thread_messages() Job is run again
Then no Thread concept file and no raw message note has its own content
    changed by this run — verified byte-for-byte identical before and after
    — proving the Job is idempotent and safe to re-run on every scheduled
    pass, not just the one-time retrofit
```
<!-- AC-ID: REQ-SB-73-US-01-AC-06 -->

## Affected Screens

None new — backend and vault-content only. `html-prototype/note-detail.html`
(`REQ-SB-14-US-01`, already `Done`) already renders any real note's
frontmatter, outgoing wikilinks, and incoming backlinks generically — the
exact machinery the PRD's own text names as currently unable to show a
Thread ↔ Message relationship only because the underlying `## Messages`
section and `thread:` field don't exist yet. Once this story writes them,
the already-shipped backlinks panel and graph view surface them
automatically, with no prototype change needed.

**Prototype parity:** N/A — no new screen region introduced. See
`REQ-SB-14-US-01`'s own note-detail backlinks/outgoing-links panels, which
already render generically over whatever real wikilinks exist in a note's
frontmatter/body.

## Dependencies

- **Blocked by (hard):** `REQ-SB-72-US-01` (The Librarian Section — First
  Housekeeping Pipeline, `Done`, `SPRINT-063`) — this story extends that
  story's own already-shipped `rename_threads()` (fan-out, Scenario 4) and
  adds a new Job to that SAME `librarian_housekeeping.py` module, Section,
  and Agent; nothing in this story is buildable before that shape exists.
- **Blocked by (hard):** `REQ-SB-71-US-02` (Email Capture Redesign, `Done`,
  `SPRINT-061`) — the `RawMessage` note shape, `messages/` directory
  convention, and `raw_message_note_path` this story retrofits.
- **Blocked by (hard):** `REQ-SB-71-US-01` (Section-Ownership Enforcement,
  `Done`, `SPRINT-060`) — this story's own new `## Messages` writer must
  register its own correct `_CALLER_ALLOW_LISTS` entry in that same
  guarded registry from day one, mirroring `## Files`/`## Related`'s own
  precedent.
- **Related to:** `REQ-SB-14-US-01` (Vault Graph Connectivity, `Done`) — the
  already-shipped backlinks panel/graph view this story's own new wikilinks
  become visible in, with zero prototype change required (see `## Affected
  Screens`).
- **Related to:** `REQ-SB-60` (Conversation — Merging Related Threads, P2,
  explicitly not yet spec'd) — NOT a dependency; that requirement groups
  multiple Threads into one Conversation, a separate concern from this
  story's own single-Thread ↔ its-own-messages linking.
- **External:** none new.

## Constraints

- **`## Messages` is Agent-owned and fully regenerated every pass, never
  incrementally patched** — mirrors `## Glimpse`'s own existing mechanical-
  rollup contract (`REQ-SB-54` point 8), per the PRD's own explicit framing.
- **The Thread → Messages direction is safe by construction** — a raw
  message's own filename is never renamed by anything in this codebase
  (confirmed by direct reading, see `## Context`), so `## Messages` needs no
  Thread-rename-specific handling of its own.
- **The Messages → Thread direction is NOT safe by construction** — the
  `thread:` fan-out must happen inside `rename_threads()` itself, in the
  SAME operation as the Thread's own directory move, never a separate
  follow-up pass — a zero-staleness-window requirement, not merely
  "eventually consistent" (Scenario 4).
- **`link_thread_messages()` must be idempotent and safe to re-run** — the
  single vehicle for both the one-time retrofit across the real corpus AND
  ongoing self-healing on every future scheduled pass, mirroring
  `backfill_files()`'s own already-shipped precedent — never a one-off
  script (`MEMORY.md` — API-first, no script workarounds).
- **Stage 1 capture (`raw_message_capture.capture_raw_thread_messages`) is
  NOT modified to write these links itself at capture time** — structured
  post-capture enrichment stays the Librarian's job, the same division of
  labor `REQ-SB-72` already established for `## Files`/`## Related`, per
  the PRD's own explicit deferral.
- **No new Section, no new Agent** — this story's own new Job is added to
  the already-existing `librarian_housekeeping.py` module and the already-
  existing "Librarian" Section / `librarian-housekeeping` Agent
  (`REQ-SB-72-US-01-T08`), mirroring how `backfill_files` was added without
  inventing a new Section.
- **Every real capability this Job exposes is reachable via a real HTTP
  endpoint** (standing project convention, same as every other
  `librarian_housekeeping.py` Job's own `/poc/librarian-*` endpoint).
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).

## Implementation Tasks

<!-- Analyst-authored starting point, non-authoritative — the decomposer's
own table at /plan-tasks supersedes this. Task count/shape is provisional
until the architect resolves the mechanism-level open questions in ## Notes
(section-ownership registration shape, Job-chain placement, and whether
## Messages needs a new "insert-if-missing" header primitive mirroring
## Files' own precedent). -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-73-US-01-T01 | backend | `link_thread_messages()` — new Job in `librarian_housekeeping.py`: regenerates `## Messages` for every real Thread from its own current `messages/` glob (via `insert_body_section_if_missing`/`replace_body_section`); writes/corrects `thread:` on every message via `upsert_frontmatter_key` (write-new, self-heal, true no-op); registers its own `_CALLER_ALLOW_LISTS` entry for `## Messages`; extends `vault_indexing.py::_build_entry` so `outgoing_wikilinks` also scans frontmatter string/string-list values, additively | `app/business/pipelines/librarian_housekeeping.py`, `app/data_access/section_ownership.py`, `app/business/vault_indexing.py` | `../Tasks/REQ-SB-73-US-01-T01-link-thread-messages-job.md` |
| REQ-SB-73-US-01-T02 | backend | `rename_threads()` fan-out extension — after each successful `rename_thread_directory` call, in the SAME loop iteration, globs the renamed Thread's own current `messages/*.md` and calls `upsert_frontmatter_key(..., "thread", new_stem)` for each — zero-staleness-window guarantee, not "eventually consistent" | `app/business/pipelines/librarian_housekeeping.py` | `../Tasks/REQ-SB-73-US-01-T02-rename-fan-out.md` |
| REQ-SB-73-US-01-T03 | backend | Wire `link_thread_messages()` into `run_housekeeping_pass()`'s own Job chain, SECOND, immediately after `rename_threads()` (`ADR-054` Decision 4) + a new `POST /poc/librarian-link-thread-messages` endpoint, mirroring every other Job's own reachability convention | `app/business/pipelines/librarian_housekeeping.py`, `app/api/email_poc_router.py` | `../Tasks/REQ-SB-73-US-01-T03-orchestration-and-endpoint.md` |
| REQ-SB-73-US-01-T04 | backend | One-time retrofit run of `link_thread_messages()` against the full real corpus (137 Threads / 257 messages), via the real `/poc/librarian-link-thread-messages` endpoint, + a real, byte-for-byte idempotency re-run verification | `app/business/pipelines/librarian_housekeeping.py` | `../Tasks/REQ-SB-73-US-01-T04-retrofit-run-and-idempotency-verification.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — manual mode still in effect, per `Implementation/Pipeline.md` (all 6 locked ACs verified via the manual steps in each task's own `## Tests` block)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints (none new emerged — the mechanisms this sprint hit are already-recorded `MEMORY.md` constraints, re-confirmed live; see `SPRINT-067`'s own Retrospective)
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Stage 1 capture writing `thread:`/`## Messages` synchronously at capture
  time** — explicitly deferred by the PRD; a freshly captured message
  becomes linked on the Librarian's next scheduled/triggered pass, not
  synchronously at capture.
- **`REQ-SB-60` Conversation-level merging of related Threads** — a
  separate, still-unspec'd P2 requirement; this story links a Thread to its
  own messages only, never across Threads.
- **Meaningful/topic tags, cross-Thread recurring-artifact linking** —
  `REQ-SB-72`'s own explicit deferrals, unaffected and unrevisited here.
- **Backfilling any pre-`REQ-SB-71-US-02` flat-shape Thread notes** (if any
  remain) — the same disclosed, out-of-scope carve-out `REQ-SB-72-US-01`
  already established (`ESC-048`), not reopened by this story.
- **Any new screen or UI widget** — the already-shipped, generic
  backlinks/graph-view machinery (`REQ-SB-14-US-01`) is the entire
  presentation layer this story needs; see `## Affected Screens`.

## Notes

**Prototype parity:** N/A — no new `html-prototype/` screen region; see
`## Affected Screens` above.

**Mechanism-level questions left to `/plan-tasks`, not resolved by this pass
(the Gherkin above specifies the OUTCOME, not the mechanism — mirrors
`REQ-SB-72-US-01`'s own identical precedent):**

1. **Whether `## Messages` needs a new "insert section header if missing"
   primitive** — the existing Thread baseline template
   (`create_thread_note_baseline`) does not yet include a `## Messages`
   header, so the first pass over an already-existing Thread needs to add
   the header, not just replace its content. `REQ-SB-72-US-01-T04`'s own
   `## Files` backfill already solved this exact problem once (an
   "idempotent `## Files` header top-up primitive") — left to the architect
   to decide whether that same primitive is reused/generalized or a new one
   is written.
2. **The exact `_CALLER_ALLOW_LISTS` caller id and header set for the new
   `## Messages` writer** — mirrors `librarian_housekeeping.backfill_files`
   → `{"## Files"}` and `librarian_housekeeping.populate_thread_related_
   links` → `{"## Related"}`'s own precedent exactly; the concrete function
   name is a decomposer/architect naming decision, not asserted here.
3. **Where `link_thread_messages()` sits in `run_housekeeping_pass()`'s own
   fixed Job chain** — unlike the three later Jobs (which only read/write a
   Thread's own concept file), this Job also writes to every message note
   under `messages/`, and Scenario 4's own rename fan-out already keeps
   `thread:` correct independent of Job-chain ordering. The Gherkin above is
   written so it holds regardless of where this Job is placed relative to
   the other three — left to the architect, mirroring `ADR-049`'s own
   established fork/merge/branch-shape latitude for this exact pipeline.
4. **The exact new endpoint route name** — follows the existing
   `/poc/librarian-*` convention already established by `REQ-SB-72-US-01-
   T08`; no specific route is asserted here.

**Why this does NOT trip trigger 1 (material assumption):** every open item
above is a MECHANISM question this project's own role boundaries assign to
the architect at `/plan-tasks` — the PRD's own text, confirmed turn-by-turn
with the operator, resolves every SCOPE-level question directly (what the 3
building blocks are, that this is a new Job under the already-existing
Librarian Section/Agent, that Stage 1 capture is not touched, that the Job
must be idempotent and double as ongoing self-healing). This pass adds no
scope the PRD did not already state.

**Why this does NOT trip trigger 2:** `REQ-SB-73` carries no `<!--
Draft -->` marker in the PRD — its own footnote confirms the retrofit-vs-
routing priority and the rename-safety design were each individually
proposed and confirmed directly by the operator, finalized text.

**Why this does NOT trip trigger 3:** ADR creation/change is the
architect's own trigger, not this role's — this pass discloses the bounded
`rename_threads()` extension clearly (see `## Context`/`## Constraints`)
but does not itself create or edit `Implementation/Architecture/ADR.md`.
Whether this bounded addition needs its own ADR note (vs. simply extending
`ADR-049`'s own already-Accepted text) is left to the architect.

**Why this does NOT trip trigger 4:** no `ESCALATIONS.md` entry was
written — nothing in this pass is a backward pipeline step or an
out-of-scope event.

**Why this does NOT trip trigger 5 (oversized):** 4 starting tasks, smaller
than `REQ-SB-67-US-01`'s own comparable 3-task/S-M shape and well under
`REQ-SB-72-US-01`'s own proven 9-task/L ceiling for the SAME module — not
oversized.

**Why this does NOT trip trigger 7:** no contradictory PRD inputs found —
the PRD's own text is internally consistent, and direct reading of the real,
already-shipped `librarian_housekeeping.py`/`vault_writer.py`/
`section_ownership.py` confirms every mechanism the PRD names (Job-chain
orchestration, atomic rename, deny-by-default caller registry) already
exists exactly as described, with no discrepancy.

**Why this does NOT trip trigger 8:** the one story-shape decision this pass
makes (ONE story covering all 3 PRD-named building blocks — `## Messages`,
`thread:`, and the rename fan-out — plus the retrofit Job) is grounded
directly in the PRD's own explicit framing of these as facets of a single
"bidirectional linking" concern, not three independently-scoped features —
mirrors `REQ-SB-72-US-01`'s own identical "kept as one story since they are
all facets of the same mechanism" precedent, not a coin-flip among
equally-valid splits.

gate: clear 2026-08-19 — no MUST-FLAG trigger fired (see the itemized
trigger-by-trigger reasoning above).

**What to do next:** eligible for `/plan-tasks REQ-SB-73-US-01` — the
architect resolves the 4 mechanism-level questions above (including
whether the bounded `rename_threads()` extension needs its own ADR note),
then the decomposer locks ACs and writes tasks.

---

**Architect pass (`/plan-tasks` step 1, 2026-08-19):** all 4 mechanism-level
questions above resolved, one new ADR appended — [ADR-054](../Architecture/ADR.md)
(reuses already-shipped `insert_body_section_if_missing`/`replace_body_
section`/`upsert_frontmatter_key` for `link_thread_messages()` and the
`rename_threads()` fan-out — zero new `vault_writer.py` primitives — plus a
new `vault_indexing.py` extension, found independently while grounding this
story, so `outgoing_wikilinks` also scans frontmatter string values, not
body text alone; without it, the new `thread:` field would have been
silently invisible to the already-shipped backlinks panel/graph view this
story's own `## Affected Screens` relies on). Full mechanism detail: "The
Librarian — Bidirectional Thread ↔ Message Linking" in `Implementation/
Architecture/architecture.md`.

**Architecture scope:** §"The Librarian — Bidirectional Thread ↔ Message
Linking (`REQ-SB-73-US-01`, see ADR-054)" (all four subsections — `link_
thread_messages()`, the `rename_threads()` fan-out extension, the new
`section_ownership.py` entry, and the `vault_indexing.py` extension) in
`Implementation/Architecture/architecture.md` — this is the coder's own
bound at `/implement-sprint`. Note for the decomposer: `app/business/vault_
indexing.py` must be added to this story's own file scope (a new task, or
folded into `T01`) — it is not named in the story's own analyst-authored
`## Implementation Tasks` table above, but Scenario 3/4/5's own correctness
depends on it.

**Gate:** `flagged` — `trigger-3` (this pass created `ADR-054`). Per
`Implementation/Pipeline.md`, this does NOT halt the stage: the decomposer
still runs, so the human reviews the ADR and the resulting tasks together in
one pass. See `REVIEW-QUEUE.md` → `REQ-SB-73-US-01`.

---

## Decomposer pass (`/plan-tasks` step 2, 2026-08-19)

**All 6 Gherkin scenarios above are locked as `REQ-SB-73-US-01-AC-01`
through `AC-06`**, one-to-one against the analyst's own untagged scenarios —
wording kept essentially verbatim (already precise and buildable; no scope
change), each AC-ID tag appended immediately after its own scenario's
closing Gherkin fence, all locked by default (none marked `locked: false` —
every locked AC has a real, observable outcome: a real `## Messages` section
on disk, a real `thread:` frontmatter value, a real before/after byte
comparison for the no-op case — none found unverifiable).

**Task table above supersedes the analyst's own 4-task starting point**,
grounded directly in `ADR-054`'s own real mechanism text and the
architecture's own decomposer note (`app/business/vault_indexing.py` folded
into `T01`, per the architect's own explicit either/or — a new task would
have been artificially small, one additive helper function with no
independent Gherkin scenario of its own; `T01` is where its correctness is
actually exercised, Scenario 3/4/5's own `thread:` resolution): `T01`
(`link_thread_messages()` + the `## Messages` header primitive reuse +
`section_ownership.py` entry + the `vault_indexing.py` extension) and `T02`
(`rename_threads()` fan-out) are independent roots — different functions,
composing already-shipped primitives, zero shared new code between them —
both `depends_on: []`. `T03` (Job-chain wiring + endpoint) needs `T01`'s
`link_thread_messages()` to exist before it can be inserted into `run_
housekeeping_pass()` and exposed via a real endpoint — `depends_on: [T01]`.
`T04` (the real, full-corpus retrofit run + idempotency re-run) needs the
Job (`T01`), the fan-out extension deployed alongside it (`T02`, so the
retrofit run exercises the SAME shipped state the whole story ships as one
unit), and the real reachable endpoint (`T03`, this pipeline's own standing
"every capability reachable via HTTP" constraint) — `depends_on: [T01, T02,
T03]`. No cycles.

**AC → task mapping:** AC-01/AC-02/AC-03/AC-05 → `T01` (the Job's own
regenerate/write/self-heal behavior, each independently verifiable via a
direct Python-shell call against the real vault before the endpoint exists —
this codebase's own established "function-level proof before HTTP-level
proof" technique, `REQ-SB-72-US-01`'s own identical precedent); AC-04 →
`T02` (the rename fan-out, a real Thread rename exercised directly); AC-06
→ `T04` (idempotency proven for real, at full-corpus scale, which is this
task's own explicit mandate — a small-scale idempotency check would be a
weaker substitute for a Scenario whose own wording is about the corpus-wide
retrofit-and-self-heal Job being "safe to re-run on every scheduled pass").
`T03` is a building-block/wiring task with no directly-locked AC of its own
(mirrors `T01`/`T05`'s own established precedent in `REQ-SB-72-US-01`) —
its own Tests block is a plain component check (endpoint reachability,
Job-chain ordering), consumed and AC-verified downstream in `T04`. Every
locked AC has at least one AC-tagged manual verification step in exactly
the task named above; no locked AC is left without a tagged step (confirmed
by direct cross-check against all 4 task files' own `## Tests` blocks
before finalizing this pass).

**No cross-story dependency with `REQ-SB-74-US-01`, confirmed directly** —
both stories add Jobs to the same `librarian_housekeeping.py` module, but
this story's own `T01`/`T02` touch only `link_thread_messages`/`rename_
threads`, neither of which `REQ-SB-74-US-01`'s own Customer-backfill Jobs
call, read, or depend on in either direction; `T03`'s own `run_housekeeping_
pass()` edit and `REQ-SB-74-US-01`'s own endpoint are independent insertions
into two different functions (`run_housekeeping_pass()` vs. a new,
standalone, deliberately-NOT-scheduled endpoint) in the same file — a real,
disclosed shared-file overlap (both stories edit `librarian_housekeeping.py`
and `email_poc_router.py`), never a functional dependency. No `depends_on`
edge is added between the two stories' task sets.

**Why this pass does NOT fire a NEW trigger, beyond the architect's own
already-standing `ADR-054` flag (which this role does not clear, per
`Implementation/Pipeline.md`):**
- **Trigger 1 (material assumption):** no gap-filling assumption made — every
  task-shaping choice above (the `vault_indexing.py` fold-into-`T01`
  placement, the dependency edges) follows directly from `ADR-054`'s own
  Decision text and the architecture's own explicit decomposer note.
- **Trigger 5 (oversized):** 4 tasks — well under this project's own proven
  ceilings for this SAME module (`REQ-SB-72-US-01`'s 9-task/L shape); not
  oversized.
- **Trigger 6 (unverifiable AC):** every locked AC has a concrete, real,
  observable verification path (a real `## Messages` section on disk, a
  real `thread:` frontmatter value, a real before/after byte comparison) —
  none found unverifiable.
- **Trigger 7 (contradictory inputs):** none found — `ADR-054`'s own text is
  internally consistent with the story's own Gherkin and Constraints.
- **Trigger 8 (multiple equally-valid / unclear):** the task split above is
  grounded directly in `ADR-054`'s own real mechanism text (which primitives
  compose which Job, where the `vault_indexing.py` fix belongs), not a
  coin-flip among equally-valid shapes.

**Status:** `Draft → Ready` — every AC is locked, every locked AC has a
tagged verification step in at least one task, and `depends_on` is acyclic
(confirmed above). `gate` stays `flagged` (`gate_reason` unchanged —
`trigger-3`, `ADR-054`) — the decomposer does not clear an architect's own
ADR flag; the human reviews `ADR-054` and this pass's own 4 tasks together,
per the architect's own Notes above and the existing `REVIEW-QUEUE.md`
pointer. All 4 new task files are written at `status: Ready` in lockstep
with this story's own transition, per `Implementation/Pipeline.md`'s "task
status moves in lockstep with the story" rule.

**What to do next:** this story is now `status: Ready` with a complete,
locked task graph, but `gate: flagged` — per `Implementation/Pipeline.md`'s
"Promotion of a flagged item" human gate, the human resolves the flag (reads
`ADR-054` at `REVIEW-QUEUE.md`, reviews this pass's own 4 tasks alongside
it) before `/plan-sprints` picks this story up.

---

## Product-owner pass (`/plan-sprints`, 2026-08-19)

Grouped into its own single-story sprint, `SPRINT-067` — kept separate from
the sibling `REQ-SB-74-US-01` (`SPRINT-068`, also `Ready`/ungrouped this
pass) since the decomposer confirmed no task-level dependency between them
and combining would exceed this project's own proven 9-task single-sprint
ceiling. Full grouping rationale: `Implementation/Sprints/SPRINT-067-
bidirectional-thread-message-linking.md` → `## Grouping Rationale & Sizing`
/ `## Notes`. This story's own `gate: flagged` (`ADR-054`) is unchanged —
the product-owner does not clear an architect's own ADR flag; `SPRINT-067`
itself is `gate: clear`, `status: Ready` (its own grouping decision was
unambiguous), eligible for `/implement-sprint SPRINT-067` once `ADR-054` is
reviewed.

---

## Coder pass (`/implement-sprint SPRINT-067`, 2026-08-19)

All 4 tasks built and live-verified against the real, configured vault, in
dependency order (`T01`/`T02` independent roots, then `T03`, then `T04`):

- **`T01`** — `link_thread_messages()` added to `librarian_housekeeping.py`
  (composes `insert_body_section_if_missing`/`replace_body_section`/
  `upsert_frontmatter_key`, zero new `vault_writer.py` primitives, per
  `ADR-054`); new `section_ownership.py` entry; `vault_indexing.py::_build_
  entry` extended with a generic frontmatter-wikilink scan. `AC-01/02/03/05`
  all live-verified `PASS`.
- **`T02`** — `rename_threads()` extended with the zero-staleness-window
  `thread:` fan-out, in the same loop iteration as each successful rename.
  `AC-04` live-verified `PASS`, including 5 genuine real stem collisions
  encountered live in the corpus, correctly caught with no fan-out
  attempted.
- **`T03`** — `link_thread_messages()` wired into `run_housekeeping_pass()`
  SECOND (after `rename_threads()`); new `POST /poc/librarian-link-thread-
  messages` endpoint. Component-verified live (real `200`, real result
  shape; Job-chain ordering confirmed both by source reading and a real
  full-corpus `run_housekeeping_pass()` call).
- **`T04`** — real, full-corpus retrofit run via the real endpoint (132
  Thread directories, 258 raw message notes) + a real, byte-for-byte
  SHA-256 idempotency proof across all 390 real files, run twice
  back-to-back (baseline == after-run-A == after-run-B). Full-corpus
  consistency re-check: 0 `thread:` mismatches anywhere in the real corpus.
  `AC-06` live-verified `PASS`.

**All 6 locked ACs verified, all `PASS`** — see each task's own
Implementation Log for the full real evidence. No code deviation from
`ADR-054`'s own Decision text; no new `vault_writer.py` primitive was
needed, confirming the architect's own zero-new-primitives premise held in
practice. No `ESCALATIONS.md`/new `REVIEW-QUEUE.md` entry from this pass —
`ADR-054`'s own standing human-review item (see `REVIEW-QUEUE.md`) is
unresolved by this role (not the coder's to clear) and was updated with a
build-completion note, per the `SPRINT-060`/`ADR-048` precedent (a standing
architect-level ADR-review flag does not block the build).

**Status:** `Ready -> Done` — every Implementation Task complete, every
locked AC verified, all Constraints respected (`## Messages` fully
regenerated every pass; the Messages->Thread direction's rename fan-out
lives inside `rename_threads()` itself, zero staleness window; `link_
thread_messages()` proven idempotent at full-corpus scale; Stage 1 capture
untouched; no new Section/Agent; every capability reachable via a real
`/poc/librarian-*` endpoint; `ADR-003` layer boundary respected throughout).
`gate` stays `flagged` (`ADR-054` review, unchanged) — the coder does not
clear an architect's own ADR flag.
