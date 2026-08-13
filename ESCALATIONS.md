# ESCALATIONS

Append-only log of every backward pipeline step (re-spec, re-architect, re-plan)
and out-of-scope event. Never edit a resolved entry. Every resolved entry names a
concrete resolving artefact (story ID, ADR number, or commit hash).

Categories: `unclear-requirement | out-of-scope | new-dependency |
shared-interface-change | adr-deviation | unanticipated-file | oversized-story |
other`

<!-- Entry format:
## ESC-NNN: [Short description] — YYYY-MM-DD
**Category:** [category from list above]
**Trigger:** What caused the escalation
**Resolution:** What was decided
**Resolving artefact:** story-id / ADR-NNN / commit abc123
**Status:** Resolved | Open
-->

## ESC-001: Migration's generic scan (ADR-009) never touches the 5 real Microsoft Person notes AC-06 names — 2026-08-11

**Category:** unclear-requirement

**Trigger:** `REQ-SB-16-US-01-T04`'s pre-migration live-vault sanity check (run
before calling the mutating `POST /poc/migrate-customer-to-partner` endpoint,
per the coder's own brief). `REQ-SB-16-US-01`'s Context and locked
`REQ-SB-16-US-01-AC-06` both assert "the 5 Person notes and 2 Email notes
already carrying `customer: Microsoft` frontmatter and a `customer/microsoft`
tag." Live inspection of the real vault (`VAULT_PATH`) found this premise is
factually wrong for the 5 Person notes: `Work/People/{amraze, karimlouis,
lumazohlof, m365copilotupdates, maccount}@microsoft.com.md` carry **no**
`customer` frontmatter field and **no** `customer/microsoft` tag at all — only
a `company/microsoft` tag (per `people_extraction.build_person_tags`'s actual
schema, which has never had a `customer:` frontmatter field for Person notes).
All 5 do carry an inline `**Customer:** [[Microsoft]]` body wikilink (written
by `customer_hub_linking.link_note_to_customer_hub` when Microsoft was
classified as a Customer), confirming they are genuinely in-scope for the
"relabel the inline wikilink" half of AC-06 — but `partner_hub_linking.
migrate_customer_to_partner`'s generic scan (built exactly per `ADR-009`
point 4/5 and `REQ-SB-16-US-01-T02`'s own literal code) filters on
`frontmatter.get("customer") == customer_name`, which structurally excludes
every one of these 5 notes (their `customer` key doesn't exist, so the very
first `if` skips them). Running the migration as specified would correctly
move the hub note and retag the 8 notes that do carry the `customer` field
(1 hub + 2 Email + 1 Newsletter + 4 Notification — matching the architect's
own already-flagged Newsletter/Notification undercount finding), but would
silently leave all 5 Person notes' `**Customer:** [[Microsoft]]` body line
unrelabeled — a stale, internally-inconsistent label pointing at a company
that is no longer a Customer, exactly the "stranded data" outcome the
story's own `## Story` section says this migration exists to prevent. This is
not a quantity difference (the architect's already-resolved Newsletter/
Notification finding); it's a data-shape difference the generic scan's own
matching condition cannot see, so AC-06 cannot be verified as passing for
5 real, already-identified notes without either (a) accepting AC-06 is
partially unmet, or (b) a design change to the scan/migration (e.g. an
additional pass matching on `company/<slug>` tag + inline wikilink presence,
rather than `customer` frontmatter equality) — the latter being an
architecture-level decision (which notes are in-scope for the retag, and by
what signal) that `ADR-009` itself settled a specific way, so it is not this
coder's call to unilaterally broaden.

**Resolution:** Resolved 2026-08-11 (architect pass, `/plan-tasks` step 1,
resuming `T04`). Operator decision, 2026-08-11: extend the migration's
match predicate rather than accept `AC-06` as satisfied only for
frontmatter-bearing notes. `ADR-009` itself is not edited (still
`Accepted`) — a new ADR, `ADR-012`, extends its point 4 match predicate to
a union of the original frontmatter-equality signal and a new
inline-`**Customer:** [[name]]`-body-wikilink signal, both read from the
existing scan's single `read_note()` call per note (no second vault scan,
no new `vault_writer.py` primitives — every retag primitive already
no-ops if its target is absent). `Implementation/Tasks/
REQ-SB-16-US-01-T04-migration-endpoint.md`'s own scope/spec is corrected
to carry this fix (routed through `T04` rather than reopening the
already-`Done`, frozen `T02`); its `status:` is reset `Blocked → Ready`,
`gate: flagged` (`trigger-3`, naming `ADR-012`). `REQ-SB-16-US-01`'s own
`status:` is likewise reset `Blocked → Ready`. The mutating `POST
/poc/migrate-customer-to-partner` endpoint still has **not** been called
against the real vault — no live Microsoft data has been touched by this
escalation or its resolution; `/implement-sprint` may now resume `T04`
with the corrected match predicate.

**Resolving artefact:** `ADR-012` (`Implementation/Architecture/ADR.md`)
and the corrected `REQ-SB-16-US-01-T04`
(`Implementation/Tasks/REQ-SB-16-US-01-T04-migration-endpoint.md`).

**Status:** Resolved

## ESC-002: Live confirmation of ADR-008's own honestly-flagged EntryID-stability risk across recurring-occurrence expansion — 2026-08-11

**Category:** other

**Trigger:** `REQ-SB-08-US-01-T03`/`T05`'s own live verification against the
real Outlook calendar (Scenario 9 / `REQ-SB-08-US-01-AC-09`). ADR-008's
Decision point 2 states "every expanded occurrence returned by
`items.IncludeRecurrences = True` is treated as a plain item with its own
`EntryID`," and its own Consequences section separately, honestly flagged
this as unverified: "Outlook's documented behaviour for EntryID stability
across `IncludeRecurrences = True` occurrence expansion is not something
either this codebase or agentic-map's has had to stress-test against a real
recurring series yet... grounds for a superseding ADR... not a silent
workaround" if a live collision were ever observed. A real recurring
meeting on the live calendar ("Weekly Forecast l Strategic Clients", 3
occurrences within the default sync window: 2026-08-10, 2026-08-17,
2026-08-24) was inspected directly via `list_calendar_events` during live
verification. **All 3 distinct occurrences return the exact same, full
`EntryID` string** — not a coincidental 8-character-suffix collision, the
entire ID is identical. This falsifies ADR-008's stated assumption that
`IncludeRecurrences`-expanded occurrences each carry their own EntryID.
**Today's actual pipeline output is still correct** — each of the 3
occurrences produced its own distinct Meeting note, verified via
`REQ-SB-08-US-01-T05`'s live run — solely because
`meeting_note_filename_stem` incorporates the event's *date* as well as the
EntryID suffix, and these 3 real occurrences happen to fall on different
dates. The identified risk: a future recurring meeting with two occurrences
landing on the **same calendar date** (e.g. a twice-daily recurring
meeting, or a rescheduled occurrence colliding with another) would produce
an identical filename for both (same subject, same date, same
EntryID-suffix, since the suffix is now confirmed non-unique per
occurrence) — the second occurrence would be silently treated by
`meeting_note_exists()` as "already exists, top up only," merging two
distinct meetings into one note. This would violate both
`REQ-SB-08-US-01-AC-07`'s and `AC-09`'s no-collision guarantees for that
specific edge case, and the story's own Constraints name no-data-loss as
"load-bearing, not a convenience."

**Resolution:** Fix designed, 2026-08-11 (not yet built/verified — see
below). Operator decision, 2026-08-11: "fix this now," per ADR-008's own
pre-authorized path. A new superseding ADR, `ADR-013`, replaces `EntryID`
with `AppointmentItem.GlobalAppointmentID` (an 8-hex-char SHA-256 hash of
the full ID string, not a raw slice — the internal `GlobalObjectId`
structure's per-occurrence-varying bytes aren't reliably within any fixed
trailing slice, so a raw slice would risk silently reproducing this exact
class of defect on the new field) as the Meeting-occurrence dedup/filename
key. No migration/rename of the 38 already-captured real Meeting notes or
`processed_meeting_ids.json`'s existing `EntryID` entries — a new
backward-compatible legacy-path fallback check (checks the new
`GlobalAppointmentID`-hash path, then the pre-fix `EntryID`-suffix path)
prevents the duplicate-note regression a naive forward-only scheme switch
would otherwise cause for still-in-window, already-captured events. One
honestly-named residual risk remains even after this fix (a narrower,
bounded, shrinking-over-time edge case — see `ADR-013`'s own Consequences
section) — not eliminated by design, only reduced. New task
`REQ-SB-08-US-01-T06` implements this; `REQ-SB-08-US-01`'s own `status:`
stays `Done` (this is additive work against a frozen story, per Pipeline.md
hard rule 1 — not a reopening); `T06` needs a new `SPRINT-NNN` at the next
`/plan-sprints` pass (its parent story's own `SPRINT-006` is already
`Done`).

**Resolving artefact:** `ADR-013` (`Implementation/Architecture/ADR.md`)
and `REQ-SB-08-US-01-T06`
(`Implementation/Tasks/REQ-SB-08-US-01-T06-global-appointment-id-dedup-key-fix.md`)
— design-complete; **not yet built or live-verified**, so this entry stays
`Open` rather than `Resolved` per this file's own convention (a resolved
entry names a *concrete* resolving artefact and is never edited again —
this fix has not yet been confirmed live, so it is not yet that concrete).
Flip to `Resolved` once `T06` is `Done` and its own live regression checks
(re-verifying the exact recurring series that triggered this escalation)
pass.

**Status:** Open (fix designed; implementation and live verification
pending `T06`)

**Update, 2026-08-12 (`REQ-SB-08-US-01-T06` built and live-verified):**
`T06` is built exactly per `ADR-013`'s design and live-verified against
the real Outlook calendar/vault. The coexistence/no-duplicate mechanism
(new-scheme-then-legacy-path lookup) is confirmed working correctly — no
duplicate created, no existing note renamed/altered, across all 39
real pre-existing Meeting notes. **However, this entry stays `Open`, not
`Resolved`:** live verification found `ADR-013`'s own core premise
(`GlobalAppointmentID` is unique per occurrence) is **itself falsified**
on this Outlook installation, for the exact same real recurring series
this entry originally found broken for `EntryID` — see the new, separate
`ESC-012` entry below for the full finding. `T06`'s own `status:` is
`Blocked`, not `Done`, pending an architect decision on `ESC-012`. Full
detail: `Implementation/Tasks/
REQ-SB-08-US-01-T06-global-appointment-id-dedup-key-fix.md`'s own
Implementation Log.

**Update, 2026-08-12 — design-level resolved via `ADR-019` (see `ESC-012`'s
own 2026-08-12 update for the full decision).** `ADR-013` (the design this
entry's own "fix designed" status referred to) is superseded on its
Decision points 1/2 by `ADR-019` — the new dedup key no longer depends on
`GlobalAppointmentID` (or any other Outlook-provided identity field)
either, closing this escalation's own original finding at the design
level by structural construction rather than by trusting a second Outlook
identity property empirically. This entry stays `Open`, not `Resolved`,
for the same reason `ESC-012` stays open narrowly: `T06` still needs to be
rebuilt and live-verified against `ADR-019` before this closes
operationally. Flip to `Resolved` alongside `ESC-012` once that
verification passes.

**Update, 2026-08-12 — Resolved operationally.** `REQ-SB-08-US-01-T06` is
rebuilt exactly per `ADR-019` and live-verified against the real Outlook
calendar/vault: the exact recurring series this entry originally found
(`EntryID` identical across all 3 occurrences of "Weekly Forecast l
Strategic/Major Clients") now produces a structurally-guaranteed-distinct
filename suffix per occurrence (confirmed live — 6 distinct `start`
values, 6 distinct suffixes), with zero duplicate notes created and zero
of the 39 named pre-existing notes touched. Full evidence: `Implementation/
Tasks/REQ-SB-08-US-01-T06-global-appointment-id-dedup-key-fix.md`'s own
Implementation Log. One honestly-flagged, bounded, non-blocking finding
from this same live-verification pass (a pre-existing 40th Meeting note
plus a real mid-session calendar reschedule producing one recoverable
duplicate note, unrelated to the `EntryID`/`GlobalAppointmentID`
uniqueness question this escalation is about) is tracked separately as a
`REVIEW-QUEUE.md` spot-check item, not as a new escalation — it does not
reopen or qualify this resolution.

**Status:** Resolved

## ESC-003: `insert_body_line_if_missing`'s fixed body-start offset corrupts notes whose body lacks the standard blank line after frontmatter — 2026-08-11

**Category:** other

**Trigger:** `REQ-SB-16-US-01-T04`'s live migration verification (post-
`ADR-012` fix). While confirming all 6 real Microsoft Person notes were
correctly relabeled, `Work/People/karimlouis@microsoft.com.md` was found
in a corrupted state: a stray leading character glued directly onto a
`**Partner:** [[Microsoft]]` wikilink, and a separate orphaned
partial-word text fragment elsewhere in the body. Root cause:
`vault_writer.insert_body_line_if_missing` computes the insertion point as
a **fixed offset** from the frontmatter's closing `---` (`body_start = end
+ 6`), documented as assuming `write_note()`'s own `"---\n\n<body>"`
convention (a blank line between frontmatter and body). This one note's
body never had that blank line — a structural artefact of an older,
unrelated verification pass (`REQ-SB-10-US-01-T04`, predates this
session) that manually edited the file outside `write_note()`'s own
convention. Every subsequent call to `insert_body_line_if_missing` against
this note (regardless of which caller — `customer_hub_linking.
link_note_to_customer_hub` historically, then `partner_hub_linking.
link_note_to_partner_hub` live during this session's own verification, as
a legitimate side effect of a real capture run triggered by starting the
dev server) inserts at the *same* fixed byte offset every time, landing
mid-word rather than at the true start of the existing body content —
compounding the corruption further with each call rather than being a
one-off. This is a genuine, latent defect in a shared `data_access`
primitive (`REQ-SB-14`/`REQ-SB-10`-era code, unrelated to `REQ-SB-16`'s own
scope) that could recur on any other note whose body was ever hand-edited
outside the standard convention, not limited to this one instance.

**Resolution:** Open — not fixed at the primitive level (out of
`REQ-SB-16-US-01-T04`'s declared scope; `vault_writer.py`'s shared
`insert_body_line_if_missing` is used by multiple already-`Done` stories'
call sites). The one affected real note
(`Work/People/karimlouis@microsoft.com.md`) was manually repaired directly
(restored the standard blank-line body structure, kept exactly one correct
`**Partner:** [[Microsoft]]` line, preserved its existing manually-added
`## Notes` content byte-for-byte, removed the corruption fragments) —
verified byte-exact via direct file read/write, not retyped. A vault-wide
sweep found no other note exhibiting the same missing-blank-line structural
defect at this time, but the underlying primitive bug remains unfixed and
could resurface on any future manually-edited note.

**Resolving artefact:** `BUGS.md` → `BUG-003` (captured 2026-08-12, per
operator directive). Still needs `/triage` to batch it into a
`BUGFIX-NN-US-01` fix story before the underlying primitive itself is
hardened.

**Status:** Resolved (formally tracked as `BUG-003`; the underlying fix
itself is separate forward work, tracked there — not blocked here)

## ESC-004: REQ-SB-20's routing-intelligence mechanism and keyword-assignment model left undecided by the PRD, with a real ADR-007/ADR-011 tension — 2026-08-11

**Category:** unclear-requirement

**Trigger:** `REQ-SB-20`'s own PRD breadcrumb (2026-08-11, operator-authored)
explicitly names three mechanism/scope questions as "genuinely open, not
decided here... All left to `/spec`/`/plan-tasks`, not guessed here": (1)
the exact keyword-assignment mechanism — free text per agent vs. a fixed
vocabulary, and whether the user assigns them or the app infers them; (2)
what "the Hub understands" and "Hubs talk to each other to route the
request" mean mechanically — a real LLM-backed routing decision, a
keyword-match lookup table (the same shape `ADR-011` already established
for chat action-triggering), or something else; (3) whether within-Section
routing (an agent asking its own Hub for help with another agent in the
*same* Section) is in scope here, or a separate concern from cross-Section
routing. Separately, reading `ADR-007` ("No agent-orchestration framework...
Hermes owns orchestration") alongside `REQ-SB-20`'s own Hub-to-Hub routing
request: `ADR-007`'s own Consequences section pre-authorizes exactly this
class of trigger — "If a future requirement genuinely needs Second Brain
itself to coordinate multi-step or multi-agent work... that is new scope
requiring its own requirement and a superseding ADR — not assumed or
pre-built here." `REQ-SB-20`'s Hub-to-Hub, agent-needs-help-from-another-
agent routing reads as squarely that class of capability — a real tension
with `ADR-007`'s stated boundary that the architect must judge at
`/plan-tasks` (reuse `ADR-011`'s proportionate keyword-match posture and
stay inside `ADR-007`'s boundary, or conclude this genuinely needs a
superseding ADR).

**Resolution:** Operator decided all three points directly, 2026-08-11:
(1) keyword assignment is free-text, user-assigned; (2) the routing
mechanism is keyword matching, reusing `ADR-011`'s posture — confirmed to
stay inside `ADR-007`'s boundary, no superseding ADR needed for the
mechanism itself; (3) within-Section routing is deferred, out of scope —
cross-Section only this pass, reversing the analyst's provisional
inclusion. `REQ-SB-20-US-01` updated accordingly (Scenario 2, within-
Section routing, moved to Non-Goals). The story still cannot be built
until `REQ-SB-18-US-01` ships, and still needs a `/design` pass for the
new keyword field — tracked as ordinary open work in `REVIEW-QUEUE.md`,
not as an unresolved escalation.

**Resolving artefact:** Operator decision, 2026-08-11 (recorded in
`REQ-SB-20-US-01`'s `## Notes`); no new ADR needed since the mechanism
stays inside `ADR-007`'s existing boundary.

**Status:** Resolved

## ESC-005: REQ-SB-21's default working mode, and the Supervised-mode approval UI for background pipelines, left undecided by the PRD — 2026-08-11

**Category:** unclear-requirement

**Trigger:** `REQ-SB-21`'s own PRD breadcrumb (2026-08-11, operator-authored)
explicitly names two questions as "genuinely open, not decided here...
Left to `/spec`, not guessed here": (1) what "propose an action and wait
for approval" looks like concretely for a background capture pipeline
(`REQ-SB-07`/`REQ-SB-08`/`REQ-SB-09`, which currently run unconditionally
on a scheduler/app-start trigger with no UI surface open at all at the
moment of triggering) versus a chat-triggered action (`REQ-SB-13`, which
already has a live chat surface to propose into) — these may need
genuinely different UI treatments, and no `html-prototype/` screen
currently has any pending-approval affordance for either context; (2) the
default working mode for existing and newly-added agents — every agent
today behaves as if it were Autonomous by default (scheduled captures run
unconditionally, chat-triggered actions execute immediately, per
`ADR-011`), which argues for Autonomous as the behavior-preserving default,
but this is a new, deliberately-introduced trust-relevant concept and a
more conservative Supervised default is equally defensible — a genuine
product-philosophy call, not a technical one.

**Resolution:** Operator decided both points directly, 2026-08-11: (1)
default working mode is Autonomous, behavior-preserving; (2) the
Supervised background-pipeline approval gets a real, dedicated Pending
Approvals surface, built in this pass rather than deferred to REQ-SB-11.
`REQ-SB-21-US-01` updated accordingly. Exact UI placement/shape for the
new surface still needs a `/design` pass — tracked as ordinary open work
in `REVIEW-QUEUE.md`, not as an unresolved escalation.

**Resolving artefact:** Operator decision, 2026-08-11 (recorded in
`REQ-SB-21-US-01`'s `## Notes`).

**Status:** Resolved

## ESC-006: REQ-SB-27's own architectural shape ("what is a skill?") is genuinely unresolved, with multiple equally-valid interpretations — 2026-08-11

**Category:** unclear-requirement

**Trigger:** `REQ-SB-27`'s own PRD breadcrumb (2026-08-11, operator-authored)
explicitly self-assesses this as "architecturally the least-precedented
requirement captured this session and will need real design work, not a
quick extension of an existing pattern," naming four genuinely open
questions, none decided in the PRD: (1) what a "skill" actually is
architecturally — a callable capability registered somewhere, in the spirit
of `REQ-SB-19`'s Provider registry / `agent_registry.py`'s existing agent
pattern, or something else entirely; (2) how an agent gets access to a
skill — assigned per-agent like keywords/Section, or available to all
agents by default; (3) which skill(s) to actually build first — the
operator's own worked example (an agent that understands architecture/
engineering diagrams given a photo) implies multimodal input, a real
technical capability this project has zero precedent for anywhere in its
stack (no Provider, client, or architecture pattern for non-text input
exists today); (4) the relationship to REQ-SB-28 (File Upload) as the
likely input mechanism for skills like summarization. Reading the two
closest existing registry-pattern precedents (`app/business/
agent_registry.py`'s fully static, hardcoded catalog per `ADR-011`, and
`app/business/provider_registry.py`'s persisted, user-mutable concern
composed *alongside* it per `ADR-014`) confirmed neither settles the
question — both are configuration-schema patterns, and a "skill" is a
unit of specialized *capability*, a materially different kind of decision.

**Resolution:** Not resolved in this pass — no operator was available to
decide live (unlike `ESC-004`/`ESC-005`'s same-session resolutions for
REQ-SB-20/21). The analyst scoped `REQ-SB-27-US-01` down to registry-
and-per-agent-access plumbing only (mirroring the honest "declared but not
yet backed by a real handler" pattern `ADR-011`/`ADR-014` already
established for actions/Providers), explicitly deferring the first real
skill's implementation and the "what is a skill" architectural decision
itself to a human, then to a follow-on story. `REQ-SB-27-US-01` does not
fully satisfy REQ-SB-27's own PRD Acceptance text as a result — this is
disclosed directly in the story's own `## Context` and `## Notes`, not
silently narrowed.

**Resolving artefact:** _pending_ — needs a human decision on the "what is
a skill" architectural shape (recorded as open questions in
`REQ-SB-27-US-01`'s `## Notes`) before `/plan-tasks` can commit to a task
breakdown with confidence.

**Update, 2026-08-12:** `ADR-015` (LangGraph + shared MCP server,
`Accepted` 2026-08-11 — written for `REQ-SB-20`/`25`/`26`/`27`
collectively) Decision points 3/7/9 resolve sub-question (1) of this
entry's Trigger: a skill is a code-registered `@mcp.tool()` entry on
Second Brain's shared MCP server (hardcoded, mirroring `agent_registry.
py`'s existing static-catalog pattern), with per-agent access grants
composed alongside it as a new, persisted, user-mutable concern (mirroring
`section_registry.py`/`provider_registry.py`'s `ADR-014` shape) — resolved
directly in `REQ-SB-27-US-01`'s own `/spec` re-pass, 2026-08-12 (see that
story's `## Context`/`## Constraints`/`## Notes`), which flips its `gate`
to `clear`. Sub-questions (2) (default-vs-explicit access model for
*future* skills), (3) (the first real skill's implementation — still
blocked on a multimodal-capable Provider, which does not exist), and (4)
(the `REQ-SB-28` file-upload relationship) remain genuinely open — none of
them block `REQ-SB-27-US-01`'s own already-narrower, explicit-grant-only
scope, which was designed around them from the start (see that story's
`## Non-Goals`). This entry stays `Open` to keep tracking the still-open
sub-questions for whatever follow-on skill-invocation story eventually
needs them.

**Resolving artefact:** Partially resolved — `ADR-015` (2026-08-11) +
`REQ-SB-27-US-01`'s 2026-08-12 `/spec` re-pass, for sub-question (1) only.
Sub-questions (2)/(3)/(4) remain `_pending_`.

**Status:** Open (partially resolved — see 2026-08-12 update above)

**Update, 2026-08-12 — operator direction on remaining sub-questions.**
Operator gave concrete product direction, resolving most of what remained:

- **Sub-question (3) (first real skill(s)):** re-scoped from the original
  worked example (image/diagram understanding, multimodal) to a
  **different, concrete pair**: "extracting data out of a file" and
  "insert a table and format an excel file" — both **text/structured-data
  skills, not multimodal**. This changes the earlier feasibility
  assessment: the "blocked on a multimodal-capable Provider, which does
  not exist" reasoning (`REQ-SB-27-US-01`'s own Non-Goals) does **not**
  apply to these — they're plausibly buildable against the existing
  Compass Provider plus an ordinary Python library (e.g. `openpyxl` for
  Excel), not a new Provider capability.
- **Sub-question (2) (default-vs-explicit access model):** operator's own
  phrasing — "Depends on the Agent" — confirms per-agent, explicit-grant
  access, matching `REQ-SB-27-US-01`'s already-built design (not
  all-agents-by-default). No change needed to what's already shipped.
- **Sub-question (4) (`REQ-SB-28` relationship):** "extracting data out of
  a file" directly requires file input — confirms `REQ-SB-28` (File
  Upload) is a real, near-term prerequisite for at least this skill, not
  a loose/optional relationship.
- **New product signal, not a prior sub-question:** "we will create a lot
  of those skills" — the skill catalog is expected to grow substantially.
  Reinforces (does not change) `ADR-015`'s existing "grow by registering
  new `@mcp.tool()` entries on the same server" extensibility model —
  this is exactly the shape that scales to many skills without repeated
  architecture passes.

**Not yet decided (genuinely still open, not guessed):** the exact
extraction/formatting mechanism for either named skill (e.g. which
library/approach for "extracting data," precisely what "format" means for
the Excel skill), and whether these become one follow-on story or two —
left to a proper `/spec` pass when this work is actually picked up, not
decided here from a one-line product direction.

**Resolving artefact:** This update (2026-08-12, operator direction,
recorded here and cross-referenced from `REQ-SB-27-US-01`'s own `## Notes`
and `REQ-SB-28-US-01`'s dependency framing).

**Status:** Open — architecturally resolved (what a skill is, how access
works, the extensibility model), but the *first skill(s) themselves* are
still unbuilt, unspecced product work, correctly left for a future
`/spec` pass rather than guessed into existence here.

## ESC-007: REQ-SB-28 depends on REQ-SB-25 (unbuilt); storage-retention and accepted-file-type policy remain genuinely undecided — 2026-08-11

**Category:** unclear-requirement

**Trigger:** `REQ-SB-28`'s own PRD breadcrumb (2026-08-11, operator-
authored) names four genuinely open questions, none decided in the PRD:
(1) which agents accept uploads — the My Day Agent (`REQ-SB-23`)
specifically, or any agent via its own chat; (2) accepted file types; (3)
where uploaded files are stored — temporarily for processing only, vs.
retained in the vault; (4) how "summarize and file under Research" maps
onto an actual skill invocation (`REQ-SB-27`) vs. a bespoke, one-off
capability. It also names two explicit dependencies: `REQ-SB-25` (real
chat, "to receive and discuss the upload") and likely `REQ-SB-27` (skills,
"as the mechanism that actually processes the file"). Direct `BACKLOG.md`
inspection at the start of this pass confirmed **REQ-SB-25 had no story at
all yet** — not even a `Draft` one; a concurrent `/spec` pass has since
drafted `REQ-SB-25-US-01` (`Draft`, itself `gate: flagged`, not yet
`Ready`/`Done`), so the dependency is now tracked but still unbuilt. Today's
real chat mechanism (`REQ-SB-13-US-01`, Done) is exact-phrase/keyword-
substring matching (`ADR-011`), deliberately not an LLM/NLU pipeline —
asking an agent in natural language to "summarize this file and file it
under Research" would not match any declared trigger phrase today, so the
requirement's own full worked example has no meaningful way to be
demonstrated until `REQ-SB-25-US-01` actually ships.

**Resolution:** Not resolved in this pass — no operator was available to
decide live. The analyst scoped `REQ-SB-28-US-01` narrowly to the
upload/storage/raw-content-handoff mechanism only (explicitly not assuming
REQ-SB-25 has shipped — Scenario 2 is written against "whatever currently
processes the agent's messages," present or future), so this slice can be
planned and built independent of REQ-SB-25's own timeline. The
"act on the file's contents as asked" and "file the result... matching
existing schema conventions" halves of REQ-SB-28's own PRD Acceptance text
are explicit, disclosed follow-on work, not built here. Storage-retention
policy (temporary vs. vault-retained — a real privacy-relevant decision)
and accepted file-type/size limits remain undecided, named rather than
guessed, in `REQ-SB-28-US-01`'s own `## Notes`.

**Resolving artefact:** `Implementation/UserStories/REQ-SB-28-US-01-file-upload-attach-and-handoff.md`
(2026-08-12 update) — operator decided (a) storage retention: temporary-
for-processing only, never vault-retained by default; (b) accepted file
types: PDF/`.txt`/`.md`/PNG/JPG, 20MB cap; (c) `REQ-SB-25-US-01` has since
reached `Ready` on its own track, unblocking planning (full `Done` build
still recommended first, per the story's own unchanged reasoning).

**Status:** Resolved

## ESC-008: REQ-SB-29's retrieval mechanism has no underlying query primitive to build on — REQ-SB-01/02 don't exist yet, and it's unclear whether a narrower ad hoc primitive is an acceptable substitute — 2026-08-11

**Category:** unclear-requirement

**Trigger:** `REQ-SB-29`'s own PRD breadcrumb (2026-08-11, operator-authored)
explicitly names this as "genuinely open, not decided here... how this
interacts with REQ-SB-01/02 (Vault Indexing & Browse/Search, neither built
yet) as the underlying query mechanism." The requirement's Acceptance text
is not just an assignment mechanism — it commits to a real retrieval
behaviour: "when asked, the agent can retrieve and use notes matching its
assigned scope (e.g. 'get me the pipeline for Masdar' returns that
customer's actual Pipeline notes)." Checked `BACKLOG.md`: REQ-SB-01 (Vault
Indexing) and REQ-SB-02 (Browse & Search) both show "— / — / — / —" — no
story exists for either, not even `Draft`; they are the least-started
requirements in the whole PRD. Building the literal PRD acceptance text
("retrieve and use notes matching its scope") as written would normally
mean waiting on REQ-SB-01/02 to exist first — a real, large, unscoped
blocker with no target date. However, this codebase already has real
precedent for *narrower*, ad hoc, non-general vault-query primitives built
directly in `business`/`data_access` without a general indexer — e.g.
`vault_writer.list_notes_in_kind_folder(kind)` (folder-scoped),
`list_known_customers()`/`list_known_partners()` (tag-scoped, vault-derived),
and the migration-scan pattern (`ADR-009`/`ADR-012`, frontmatter+tag+
wikilink-scoped). A tag/folder-scoped retrieval primitive for this one
story could plausibly be built the same narrow way, without waiting for
REQ-SB-01/02's full general indexing/search feature. Whether that narrower
path is an acceptable substitute for the PRD's literal "retrieve and use
notes matching its scope" acceptance text, or whether the PRD's intent
really does require REQ-SB-01/02 first, is a genuine product/architecture
judgement call — not something the analyst should decide unilaterally by
guessing, per the MUST-FLAG "multiple equally-valid interpretations" and
"still-open dependency" triggers.

**Resolution:** Operator decided (2026-08-12): build the narrower,
story-scoped ad hoc primitive now, matching existing precedent
(`list_notes_in_kind_folder`/`list_known_customers`/`list_known_partners`,
the migration-scan pattern) — not a wait on `REQ-SB-01`/`REQ-SB-02`.

**Resolving artefact:** `Implementation/UserStories/REQ-SB-29-US-01-agent-to-tag-folder-scoping.md`
(2026-08-12 update).

**Status:** Resolved

## ESC-009: REQ-SB-23 revised from one-shot autonomous filing to a real conversational agent — REQ-SB-23-US-01 re-specced in place, superseding its own already-`/design`-produced prototype — 2026-08-11

**Category:** other

**Trigger:** `REQ-SB-23`'s PRD text was revised 2026-08-11 (operator-directed),
superseding its own original same-day framing. Original acceptance: "The
user can send free-form text to the My Day Agent from the My Day surface;
the agent files it into the vault as a note... classified by what it's
about" — a one-shot input+submit, autonomous-filing design.
`REQ-SB-23-US-01` was already drafted against that original text, and a
`/design` pass had already produced a matching "Quick Capture" card
(free-text input + Capture button, `html-prototype/my-day.html`) — recorded
in `REVIEW-QUEUE.md` as awaiting browser sign-off. The revised requirement
text is materially different in kind, not degree: "a real chat window,"
"the agent may ask follow-up questions before filing," "the user can
refine the note's content and supply organizational hints... mid-
conversation." This is a genuine architectural shift (single-shot classify
call vs. a real multi-turn conversation) that the existing story and its
already-designed prototype card do not describe or support. The revised
requirement's own breadcrumb also introduces a new hard dependency —
`REQ-SB-25` (Real Conversational Agent Chat) — for the conversational
mechanism itself. At the point this re-spec began, `REQ-SB-25` had no
story yet, not even `Draft` (confirmed via `Implementation/UserStories/`
listing); by the time this re-spec finished, a concurrent `/spec` run had
produced `REQ-SB-25-US-01` (`status: Draft`, `gate: flagged`, itself not
yet `Ready`/`Done`) — re-checked and corrected in `REQ-SB-23-US-01`'s own
Dependencies before this entry was closed, rather than left stale.

**Resolution:** `REQ-SB-23-US-01` re-specced in place (same file, same ID
— it never advanced past `Draft`, so no completed downstream artefact
(locked ACs, tasks) exists to unwind; this is not a violation of the
"specs are append-only for `Done` stories" hard rule). All Acceptance
Criteria scenarios rewritten as untagged Gherkin matching the new
conversational shape (real chat thread, agent-initiated follow-up
questions, mid-conversation content refinement, mid-conversation temporal/
organizational hints, classified filing). The story's `## Notes` records
what changed and why. The prior `/design` pass's "Quick Capture" card is
explicitly **not** treated as covering the revised requirement — a
one-shot input+submit card is not a real chat thread, so this is a genuine
`net-new-design-needed` flag for the NEW requirement, not reuse of
already-approved coverage. `REQ-SB-23-US-01` is now additionally blocked
by `REQ-SB-25-US-01`, which exists (`Draft`, `gate: flagged`) but is not
yet `Ready`/`Done`.

**Resolving artefact:** the revised `Implementation/UserStories/
REQ-SB-23-US-01-my-day-intake-agent.md` (this re-spec pass, 2026-08-11).
`html-prototype/my-day.html`'s "Quick Capture" card still needs its own
revision to match (designer's task, not resolved here — see the story's
own Notes).

**Status:** Resolved (the re-spec itself is complete; the story remains
`gate: flagged` for its own, separate, still-open reasons — see
`REQ-SB-23-US-01`'s own `## Notes` and the `REVIEW-QUEUE.md` entry)

## ESC-010: ADR-015 (LangGraph adoption) factually supersedes REQ-SB-20-US-01's own already-recorded routing-mechanism resolution — 2026-08-11

**Category:** adr-deviation

**Trigger:** `REQ-SB-20-US-01`'s own Context/Constraints (recorded
2026-08-11, resolving `ESC-004`) state directly: "Routing mechanism:
keyword matching, reusing `ADR-011`'s exact posture... This keeps the
mechanism comfortably inside `ADR-007`'s 'no agent-orchestration
framework' boundary — no superseding ADR needed for the mechanism choice
itself." Later the same day, the operator directly decided (after
discussion, recorded in `ADR-015`) that LangGraph is adopted for Second
Brain's own in-app agent behaviour **including Hub routing (REQ-SB-20)**,
not only chat (`REQ-SB-25`). This is a direct, factual contradiction of
`REQ-SB-20-US-01`'s own recorded resolution — the story explicitly
concluded "no `ADR-007` tension" and "no superseding ADR needed," and
`ADR-015` is exactly that: a superseding ADR whose scope explicitly names
`REQ-SB-20`. Per `Implementation/Pipeline.md`'s architect rules, a
decision that contradicts an already-recorded resolution is escalated
here rather than silently patched into the story file.

**Resolution:** `ADR-015`'s own Decision point 12 records the change
plainly: the *mechanism* backing "how a Hub decides" moves from a
hand-rolled keyword-substring lookup to a node on `ADR-015`'s LangGraph
graph, using each agent's declared keywords as that node's own routing
input. `REQ-SB-20-US-01`'s own externally-observable Acceptance Criteria
(a keyword field per agent; a cross-Section request relayed via both
Hubs, never agent-to-agent directly; an honest no-match report; a
no-keyword agent never selected) are **unaffected** — none of them
hard-codes "pure string matching" as the literal mechanism, so they
remain satisfiable under the new mechanism unchanged. Per hard rule 1
(specs are append-only), `REQ-SB-20-US-01`'s own Context/Constraints text
is **not** edited by this escalation or by `ADR-015` — the story is
`Draft`, not yet built, and per the task that produced `ADR-015`,
story-level reconciliation (updating that story's own `## Notes` to point
at `ADR-015`, and settling the new per-agent-keyword-storage question
`ADR-015` deliberately left open) is deferred to `REQ-SB-20-US-01`'s own
future `/plan-tasks` pass, not done here.

**Update, 2026-08-12 (`REQ-SB-20-US-01`'s own `/plan-tasks` architect
pass):** the deferred reconciliation is now complete. `REQ-SB-20-US-01`'s
own `## Notes` (its Context/Constraints text itself is left as-is, per
hard rule 1 — specs are append-only) now records the contradiction and
points at `ADR-015` point 12 as the now-governing mechanism decision.
The routing *algorithm* itself is confirmed unchanged (deterministic
keyword-substring matching, `ADR-011`'s exact posture) — only its
housing moves onto `ADR-015`'s graph. The one remaining open question
`ADR-015` point 12 itself deferred to this pass (per-agent keyword
storage shape, and the concrete routing-node/edge design) is now settled
by a new ADR, `ADR-017` (extends `ADR-015` point 12, mirrors `ADR-016`'s
identical role for point 13 — a new sibling
`.second-brain/agent_keywords.json`; one new `route_hub_request` node on
`ADR-015`'s same compiled graph, reached via a new conditional edge
triggered by a new, deliberately non-MCP-registered local tool,
`request_cross_section_help`). `architecture.md` gained a matching
"Section-Hub cross-Section routing — keyword storage & routing-node
mechanism" subsection. This story's own Acceptance Criteria remain
unaffected by `ADR-017`, exactly as `ADR-015` point 12 already predicted.

**Resolving artefact:** `ADR-017` (`Implementation/Architecture/ADR.md`)
and `REQ-SB-20-US-01`'s own `## Notes`
(`Implementation/UserStories/REQ-SB-20-US-01-section-hub-intelligence-and-cross-section-routing.md`).

**Status:** Resolved — the architectural contradiction is resolved at
the ADR level (`ADR-015` point 12), and `REQ-SB-20-US-01`'s own story
text is now reconciled to point at it, with the deferred keyword-storage/
routing-node design settled by `ADR-017`.

## ESC-011: REQ-SB-27-US-01's decomposer pass cannot wire its real cross-story `depends_on` onto `REQ-SB-25-US-01` — that story has not itself been decomposed into tasks yet — 2026-08-12

**Category:** other

**Trigger:** `REQ-SB-27-US-01`'s own `## Dependencies`/`## Notes` (architect
pass, 2026-08-12) already named a genuine, ordinary code dependency:
`app/business/skill_tools.py`'s `@mcp.tool()` registration requires
`app/api/mcp_server.py`'s shared `FastMCP` instance, and its placement as
a sibling of `app/business/vault_query_tools.py` presumes that module too
— both are `ADR-015`'s own scaffolding, "most plausibly" landing as part
of `REQ-SB-25-US-01` (`ADR-015` point 11). The decomposer pass launched on
`REQ-SB-27-US-01` this same day was briefed on the premise that
"`REQ-SB-25-US-01`'s decomposer ran just before this pass" and was
directed to read its resulting task files to find the specific task ID to
depend on. Direct inspection of `Implementation/Tasks/` at the start of
this pass found this premise factually wrong: **zero**
`REQ-SB-25-US-01-T*.md` files exist. Re-reading `REQ-SB-25-US-01`'s own
file confirmed its **architect** pass (`/plan-tasks` step 1) completed
2026-08-12 ("Proceeding to the decomposer"), but its own **decomposer**
step (`/plan-tasks` step 2) has evidently not yet actually run — the two
steps of `/plan-tasks` were conflated in the briefing. `depends_on` must
be a real, existing task ID (Pipeline.md hard rule 2 / the decomposer's
own contract) — there is none to point at yet.

**Resolution:** Not resolved in this pass — no operator was available to
run `REQ-SB-25-US-01`'s own decomposer step live. `REQ-SB-27-US-01`'s ACs
were locked and all 4 of its tasks were fully drafted regardless (per
Pipeline.md's "forward is autonomous by exception" rule — nothing about
this blocker prevents authoring ACs/tasks, only wiring one specific
`depends_on` edge with confidence). The one genuinely blocked task,
`REQ-SB-27-US-01-T02` (`app/business/skill_tools.py`), is left with
`depends_on: []` plus an explicit, individually-set `gate: flagged` and a
prominent "⚠️ BLOCKED — do not start" section in its own file, rather than
a fabricated task ID (which would have silently broken `/implement-sprint`
on a dangling reference) or a guess at `REQ-SB-25-US-01`'s own future task
breakdown (not this decomposer's call to make about a different story).
`REQ-SB-27-US-01`'s own `status:` stays `Draft` (not `Ready`) so all 4 of
its tasks inherit `Draft` too, per Pipeline.md's task-status-lockstep
rule — this safely prevents `/implement-sprint` from picking up any of
them before the edge is real, without needing the dangling reference as a
blocking mechanism.

**Resolving artefact:** _pending_ — needs `REQ-SB-25-US-01` to be run
through its own `/plan-tasks` decomposer step (producing a real task ID
for whichever task creates `app/api/mcp_server.py`), after which a
follow-up decomposer pass on `REQ-SB-27-US-01` replaces
`REQ-SB-27-US-01-T02`'s `depends_on: []` with that real ID and advances
the story to `Ready`. See `REQ-SB-27-US-01`'s own `## Notes` (2026-08-12
decomposer-pass entry) and `REVIEW-QUEUE.md`.

**Status:** Open

---

**Update, 2026-08-12 (follow-up decomposer pass — `REQ-SB-27-US-01`):
Resolved.**

`REQ-SB-25-US-01`'s own decomposer step has run (see that story's own
2026-08-12 entry): `status: Ready`, `gate: clear`, 8 tasks created
(`T01`-`T08`). `REQ-SB-25-US-01-T05` (`Implementation/Tasks/
REQ-SB-25-US-01-T05-mcp-server.md`) is the real task that creates
`app/api/mcp_server.py` (a module-level `FastMCP` instance named
`mcp_server`, registering `vault_query_tools.py`'s four functions,
mounted at `/mcp`).

`REQ-SB-27-US-01-T02`'s `depends_on: []` has been replaced with
`[REQ-SB-25-US-01-T05]`. `REQ-SB-27-US-01`'s `depends_on` graph across all
4 of its own tasks (`T01: []`, `T02: [REQ-SB-25-US-01-T05]`, `T03: [T01,
T02]`, `T04: [T03]`) is confirmed acyclic. `REQ-SB-27-US-01` has advanced
`status: Draft → Ready`, `gate: flagged → clear`; all 4 of its tasks moved
`Draft → Ready` in lockstep.

**Resolving artefact:** `Implementation/Tasks/
REQ-SB-27-US-01-T02-skill-tools-catalog.md` (its `depends_on` field, and
the `Implementation/UserStories/
REQ-SB-27-US-01-skills-repository-registration-and-access.md` frontmatter
transition `Draft → Ready` this same edit produced). `REVIEW-QUEUE.md`'s
`REQ-SB-27-US-01` entry has been removed as fully resolved.

**Status:** Resolved

## ESC-012: `ADR-013`'s own core premise — `AppointmentItem.GlobalAppointmentID` is unique per occurrence — is live-falsified on this Outlook installation, for the exact recurring series `ESC-002` found — 2026-08-12

**Category:** other

**Trigger:** `REQ-SB-08-US-01-T06`'s own live verification (`SPRINT-017`),
Tests step 1 (non-AC smoke check, explicitly required before the AC-tagged
regression checks). `ADR-013`'s Decision point 1 states plainly:
"`AppointmentItem.GlobalAppointmentID` (Outlook's own documented,
guaranteed-unique-per-occurrence identifier) becomes the occurrence
dedup/filename key." Live inspection via a direct Python shell script
against the real Outlook calendar (`.venv` interpreter, `list_calendar_
events`) found this premise **false** for both real recurring series in
the live sync window: "Weekly Forecast l Strategic Clients" and "Weekly
Forecast l Major Clients" (2026-08-10/17/24 each — the former is the exact
series `ESC-002` originally found broken for `EntryID`). All 3 occurrences
of each series returned the **exact same, full `global_appointment_id`
string** — not a coincidental partial match. A follow-up script isolated
the cause precisely: `item.GlobalAppointmentID`, the **native COM
property itself** (read the same direct-attribute way as `item.EntryID`,
exactly as `ADR-013` specifies), returns an identical value across all 3
occurrences on this machine/Outlook installation — this is not a bug in
`_resolve_global_appointment_id`'s own logic, which correctly reads and
returns the native property's actual live value. The documented
`PropertyAccessor`/DASL fallback (`ADR-013`'s own defense-in-depth
mechanism, the Extended MAPI tag for `PidLidGlobalObjectId`) was also
exercised directly and **errors on every occurrence**
(`com_error(-2147352567, ..., "The property \"http://schemas.
microsoft.com/mapi/id/{6ED8DA90-450B-101B-98DA-00AA003F1305}/00030102\"
is unknown or cannot be found.")`) — so even if the native path had
failed outright (rather than silently returning a non-unique value), the
fallback as designed could not have disambiguated these occurrences
either. **Practical consequence:** the specific risk `ADR-013` exists to
close — two occurrences of the same recurring series landing on the
**same calendar date** — is **not actually closed** by the fix as
approved and built; `global_appointment_id` provides zero additional
disambiguation over the already-rejected `EntryID` for this real,
already-observed class of recurring series on this Outlook installation.
Today's 39 real Meeting notes remain correct only because the filename
scheme separately incorporates the event's *date* — unchanged by `T06`,
and the exact same accidental protection `ESC-002` originally described.
Full reproduction transcript: `Implementation/Tasks/
REQ-SB-08-US-01-T06-global-appointment-id-dedup-key-fix.md`'s own
Implementation Log.

**Resolution:** Not resolved in this pass — no operator was available to
decide live. `T06` is left `status: Blocked` rather than `Done` (per
Pipeline.md hard rule 4/6 — a locked-AC-equivalent check that fails live
blocks the task; inventing a replacement disambiguation strategy is an
architecture-level decision, not this coder's call to improvise per hard
rule 5). The already-built `T06` code is left in place (not reverted) —
it is a faithful, non-regressive implementation of the approved `ADR-013`
design, and every part of it independent of the falsified uniqueness
premise (the hash-suffix mechanism itself, the legacy-path coexistence
check, zero mutation of the 38/39 pre-existing notes) is confirmed correct
and verified live. What still needs a human/architect decision: (a)
whether this is specific to this one Outlook/Exchange installation/version
(worth testing on a different mailbox/Outlook build before concluding
`GlobalAppointmentID` is unusable in general) or a broader, documented-but-
apparently-unreliable-in-practice Outlook COM behavior; (b) a genuinely
different disambiguation signal if `GlobalAppointmentID` cannot be
trusted — e.g. the occurrence's own `Start`/`RecurrenceState`/index within
the series (already available in `list_calendar_events`'s existing
`start` field, but not currently used as a *disambiguator*, only as a
display field and the existing coarse date-level filename component), a
composite key, or accepting the residual same-date-collision risk as a
named, permanent limitation rather than a "fix" claim; (c) whether
`ADR-013` itself needs a further superseding ADR, or an amendment to its
own Consequences section reclassifying this from "narrow, bounded,
shrinking-over-time" to "not actually closed for recurring series on this
installation."

**Resolving artefact:** _pending_ — needs an architect decision (a further
superseding ADR, or a directed `T06` redesign) before `REQ-SB-08-US-01-T06`
can resume and reach `Done`.

**Status:** Open

**Update, 2026-08-12 — Resolved at the design level.** Operator explicitly
delegated the technical decision ("fix it based on assumptions I don't have
an answer for"). New superseding ADR,
`Implementation/Architecture/ADR.md` → `ADR-019`, replaces `ADR-013`'s
Decision points 1 and 2: the Meeting-occurrence dedup/filename key stops
depending on any Outlook-provided identity field entirely (`EntryID` and
`GlobalAppointmentID` have now both independently failed the same live
uniqueness test on this installation) and instead uses a SHA-256 hash of
`subject` + the occurrence's own full, precise start timestamp
(`list_calendar_events`'s existing `start` field, previously only used
coarsely as the filename's date component) — a structural uniqueness
guarantee (two distinct occurrences cannot share an identical start
moment), not an empirical claim about one specific Outlook COM property's
behaviour. `ADR-013`'s point 3 (the legacy-`EntryID`-path coexistence
check, so none of the 39 already-captured real Meeting notes needs
migrating) is reused unmodified; its own middle
`GlobalAppointmentID`-hash fallback tier is deliberately dropped (confirmed
live that zero real notes were ever created under it — dead code carrying
a live-confirmed defect, not a genuine safety net). `ADR-013`'s own
`Status:` is updated to `Superseded by ADR-019` (points 1/2 only). `T06`'s
own task file (`Implementation/Tasks/REQ-SB-08-US-01-T06-global-
appointment-id-dedup-key-fix.md`) is redesigned in place around `ADR-019` —
its prior `ADR-013`-based spec and live-verification Implementation Log are
kept, unedited, at the bottom of the file as an honest record, not deleted.
`status:` reset `Blocked → Ready`.

**Resolving artefact:** `Implementation/Architecture/ADR.md` → `ADR-019`,
and `Implementation/Tasks/REQ-SB-08-US-01-T06-global-appointment-id-dedup-key-fix.md`
(redesigned in place, `status: Ready`). **Still open, narrowly:** this
resolves the design-level finding this entry recorded — `T06` itself still
needs to be rebuilt and live-verified against `ADR-019` before `ESC-002`
and `ESC-012` both close operationally (same "design vs. built-and-verified"
distinction `ESC-002` already used for `ADR-013`). `REVIEW-QUEUE.md`'s
`REQ-SB-08-US-01-T06` / `SPRINT-017` entry is updated to point at `ADR-019`
for the human's review-and-approve step, not removed.

**Update, 2026-08-12 — Resolved operationally too.** `T06` is rebuilt
exactly per `ADR-019` (`status: Done`) and live-verified against the real
Outlook calendar/vault — the exact native-COM-property non-uniqueness
this entry found (`item.GlobalAppointmentID` identical across all 3
occurrences of two real recurring series, `PropertyAccessor`/DASL fallback
erroring on every occurrence) is now structurally moot: the dedup key no
longer reads or depends on `GlobalAppointmentID` (or any other Outlook-
provided identity field) at all. Full evidence: `Implementation/Tasks/
REQ-SB-08-US-01-T06-global-appointment-id-dedup-key-fix.md`'s own
Implementation Log.

**Status:** Resolved

## ESC-013: Operator's own Manual/Supervised semantics materially differ from `ADR-018`'s built design — Supervised should gate only write/mutating actions, not every action; Manual should also exclude Hub-routed (agent-to-agent) triggers, not just background/scheduled ones — 2026-08-12

**Category:** adr-deviation

**Trigger:** `ADR-018` (`REQ-SB-21-US-01`, Working Modes) was built on two
assumptions the architect made explicit as its own judgement call, not an
operator confirmation: (1) Supervised gates the entire action — chat/
direct-triggered **and** background-triggered — uniformly, regardless of
whether the action is read-only or mutating; (2) Manual differs from
Supervised only on the background/scheduled trigger; a matched chat
message or Available-Actions button press was treated as "the user
explicitly asking," resolvable identically to Autonomous. Asked to
confirm this reading, the operator gave a materially different semantic
directly:
- **Manual:** "Can't Pull unless I asked him to... No Agent can Trigger
  an Action" — only a *direct human* ask counts as "asked." A scheduled/
  background trigger does not run it (already correct in `ADR-018`), but
  **neither does another agent's Hub-routed request** (`ADR-017`,
  `REQ-SB-20`) — a trigger source `ADR-018` never considered as a gate
  input at all, since `ADR-017`'s own routing-node design (as built)
  only returns a matched-candidate description to the requester, never
  itself invokes an action on the target agent — but the operator's own
  phrasing treats "another agent triggering an action" as a real,
  meaningful case to rule out for Manual specifically, ahead of any
  future story that would let a routed request actually invoke the
  target's action.
- **Supervised:** "It is running — but some writing or modifying needs my
  approval" — the agent operates normally and immediately for read-only/
  query actions; **only actions that write or modify something require
  approval first.** This is a real, different gating axis than `ADR-018`
  built (which gates by *trigger source*, not by the *action's own
  read/write nature*) — `agent_registry.py`'s action definitions
  currently carry no read/write classification at all, so this requires
  a genuinely new architectural concept, not a parameter tweak.
- **Autonomous:** unchanged — "doesn't need anything, runs on its own,"
  matching what's already built.

Neither `REQ-SB-20-US-01` nor `REQ-SB-21-US-01` has been built (`status:
Ready`, decomposed, not yet `/plan-sprints`'d or coded) — this is caught
before any real code exists, cheap to correct properly rather than patch
around a shipped implementation.

**Resolution:** Re-specing both stories with the corrected semantics
before `ADR-018` (and `ADR-017` for the Manual-exclusion addition) are
superseded to match. `ADR-018` itself is not edited (stays `Accepted`,
per hard rule 1) — a new superseding ADR records the corrected design.
See `REQ-SB-21-US-01`/`REQ-SB-20-US-01`'s own `## Notes` for the
resulting re-spec once it lands.

**Resolving artefact:** _pending_ — a re-spec pass on both stories,
followed by a superseding ADR and a fresh `/plan-tasks` pass, is in
progress as of this entry.

**Status:** Open

**Update, 2026-08-12 (`SPRINT-021` — `/implement-sprint` — build +
live verification complete).** The design-level resolution (analyst
re-spec, `ADR-020` superseding `ADR-018` points 3/5, decomposer's
9-task `REQ-SB-21-US-01-T01`..`T09` breakdown) was already recorded
above; this update closes the entry operationally, per this project's
own "design vs. built-and-verified" distinction (`ADR-020`'s own
Consequences named this exact follow-up). All 9 tasks are now `Done`
and every locked AC (`REQ-SB-21-US-01-AC-01`..`AC-08`) was verified
live against the real running backend/frontend/vault: a Supervised
agent's read-only action (`view_last_run`) proceeds immediately while
its write action (`run_capture_now`) proposes-and-waits, for both
chat/direct and background triggers; a Manual agent executes
immediately on a direct chat/button ask but refuses a `hub_routed`
trigger outright with no pending record; an Autonomous agent always
executes immediately regardless of trigger or action nature. Full
verification detail: each task's own Implementation Log under
`Implementation/Tasks/REQ-SB-21-US-01-T01`..`T09`, and `MEMORY.md`'s
`SPRINT-021` entry.

**Resolving artefact:** `Implementation/Sprints/SPRINT-021-agent-
working-modes.md` (`status: Done`), `Implementation/Architecture/
ADR.md` → `ADR-020`, `Implementation/Tasks/REQ-SB-21-US-01-T01`
through `T09` (all `status: Done`).

**Status:** Resolved

## ESC-014: REQ-SB-31 (System Health View) — placement and unhandled-exception-surfacing scope both genuinely open — 2026-08-12

**Category:** unclear-requirement

**Trigger:** `/spec REQ-SB-31` drafted `REQ-SB-31-US-01` from the PRD's own
breadcrumb, which explicitly names four open questions and leaves them to
`/spec`. Three of the four were resolved directly from real code (checks
available today; passive reporting over active probing, matching this
project's own consistent "reuse existing signals" preference; the
not-configured-vs-failure distinction, reusing `ADR-011`/`ADR-014`'s
existing honesty convention). Two remain genuinely open, with no PRD text,
prior design decision, or existing-code precedent settling either:
(1) **placement** — a new nav item/page, a Settings section, or a
persistent app-shell status indicator are all equally reasonable given the
breadcrumb's own framing, and no `html-prototype/` screen or prior story
settles it; (2) **whether unhandled-backend-exception surfacing is in
scope this pass.** Direct reading of `app/business/agent_orchestration/
graph.py::run_agent_conversation` (the real, `Done` chat path) confirmed a
genuine, currently-live gap: two of three failure shapes (Provider not
configured; a genuine Provider-call failure inside `call_model`) are
already funneled into an honest `{"error": ...}` result, but the function's
own outer body (`await mcp_client.load_vault_query_tools()` /
`await _GRAPH.ainvoke(...)`) is not wrapped in the same funnel — an
exception there still propagates as a raw, unhandled 500 with no
user-facing signal, the exact shape of the second real bug (a hardcoded
stale MCP port) that prompted this requirement. Whether closing that gap is
in this story's scope, or is separate follow-on hardening with this story
scoped to reading already-recorded signals only, is a genuine product/
architecture judgement call.

**Resolution:** Resolved 2026-08-12 (operator, in chat, answering both
originally-flagged questions plus one analyst-asked follow-up). (1)
**Placement:** a new top-level nav item/page (verbatim: "an new nav
page") — not a Settings section, not a persistent app-shell indicator.
(2) **Unhandled-exception surfacing:** closed in this story. Asked as a
direct follow-up once the operator's first answer (below) turned out to
address Provider-display, not the crash gap; the operator selected "In
this story (Recommended)" — `run_agent_conversation`'s own remaining call
chain (`mcp_client.load_vault_query_tools()`, `_GRAPH.ainvoke(...)`) is now
wrapped in the same honest-failure-funnel pattern `call_model` already
uses (`REQ-SB-31-US-01` Scenario 8). Additionally, **a real correction to
the story's own original design surfaced in the same exchange** (not one
of the two originally-flagged questions, but resolved here too since it
touches the same Provider-availability signal): the operator overrode the
story's proposed neutral "not configured" Provider display — on the
System Health view specifically, an agent whose Provider has no real
client is now shown as **Disabled** and listed as a **Health Issue**
(verbatim: "show the agent as Disabled and Put it as Health Issue in the
new Section"), scoped to this view only — `ADR-011` point 3 / `ADR-014`
point 7's underlying honesty convention, and every other screen relying on
it, are unchanged. See `REQ-SB-31-US-01`'s own `## Context`/`## Notes` for
the full record, including a noted-but-unresolved tension (should Agents
Map also show a "Disabled" badge for consistency — a separate product
question, not decided here).

**Resolving artefact:** `REQ-SB-31-US-01`'s own updated `## Context`/
`## Notes` (`Implementation/UserStories/
REQ-SB-31-US-01-system-health-view.md`), re-specced 2026-08-12. `gate:`
reset to `clear`. `/design REQ-SB-31` still needs to run (genuinely
net-new UI) before `/plan-tasks` — a sequencing dependency, not a reason
this escalation stays open.

**Status:** Resolved

**Update, 2026-08-12 (analyst re-spec pass — REQ-SB-21-US-01 corrected in
full; REQ-SB-20-US-01's scope narrowed mid-pass by a direct operator
correction).**

`REQ-SB-21-US-01` (`Implementation/UserStories/
REQ-SB-21-US-01-agent-working-modes.md`) is re-specced in place: Scenario
3/3b rewritten and Scenario 4 replaced so Supervised gates by the action's
own read-only-vs-mutating nature, applied uniformly across chat/direct/
background triggers, rather than by trigger source; a new Scenario 5b adds
the Manual-mode exclusion for another agent's Hub-routed request,
alongside the unchanged Scenario 5 (background trigger; direct human ask).
All 7 prior `AC-ID` tags removed (`status:` is `Draft` again — the
decomposer re-locks fresh at the next `/plan-tasks` pass). Context/
Constraints updated in place to record the correction, quoting the
operator's own words directly. `ADR-018` itself is unedited (stays
`Accepted`) — a superseding ADR is expected next `/plan-tasks` pass,
including the new read-only-vs-mutating action classification this
requires on `app/business/agent_registry.py`'s action definitions (left
for the architect to design, not designed here). `gate: clear` — the
correction is a direct, faithful application of the operator's own
verbatim semantics, not a guess.

**Mid-pass correction on `REQ-SB-20-US-01`'s scope:** this escalation's
own Trigger text originally read the operator's "No Agent can Trigger an
Action" (Manual) as implying a Manual-mode agent must also be excluded
from Hub-routing candidate selection (`REQ-SB-20`'s
`list_candidate_agents_for_keyword_match`). Before that change was made,
the operator clarified directly that this reading over-reached: "REQ-SB-20
It can be Offered but it doesn't execute — We will get to this Part when
we reach this level of the product." `ADR-017`'s already-approved
routing-node design only ever returns a matched-candidate description to
the requester; it never itself invokes an action on the target agent
(Manual-mode or otherwise) — no story yet lets a routed request execute
anything on its target, so there is nothing real to gate at `REQ-SB-20`'s
own level yet. **`REQ-SB-20-US-01`'s Acceptance Criteria, Constraints, and
candidate-selection logic are unchanged** — `AC-01`-`AC-04` and `T01`-`T06`
stand exactly as the prior decomposer pass left them. Only a Note was
added recording the deferral, for a future story that adds real
cross-agent action execution to revisit. `status:` reset directly
`Draft → Ready`, `gate: clear` — no re-decomposition was needed since
nothing substantive changed.

**Resolving artefact:** `Implementation/UserStories/
REQ-SB-21-US-01-agent-working-modes.md` (2026-08-12 re-spec) and
`Implementation/UserStories/
REQ-SB-20-US-01-section-hub-intelligence-and-cross-section-routing.md`
(2026-08-12 deferral Note). A superseding ADR over `ADR-018` and a fresh
`/plan-tasks` decomposition for `REQ-SB-21-US-01` remain the next forward
step — not yet done, tracked as ordinary open work, not a further
escalation.

**Status:** Resolved

## ESC-015: REQ-SB-35's placement mechanism (distinct agent vs. shared skill) and its new-top-level-area governance question are genuinely unresolved, and stand in real tension with REQ-SB-36's own "no approval at any step" — 2026-08-12

**Category:** unclear-requirement

**Trigger:** `REQ-SB-35`'s own PRD breadcrumb (2026-08-12, operator-
authored) explicitly names two questions as genuinely open, not decided:
(1) whether the Vault Filing Expert is a distinct agent in the registry
(routed to via `REQ-SB-20`'s Hub mechanism, mirroring the Research
Expert) or a directly-invocable shared capability/skill (`REQ-SB-27`'s
pattern) any agent can call without a routed request — the operator's own
phrasing ("Ask my Vault Expert") suggests a distinct agent, but this is
explicitly "not confirmed"; (2) what governance, if any, applies to the
Vault Filing Expert creating a genuinely new **top-level** vault area
(a materially bigger structural decision than adding a tag or a smaller
subfolder within an already-existing area) — the breadcrumb itself
observes this "may warrant a different confidence bar or even a
Supervised-style check despite `REQ-SB-36`'s own 'fully autonomous'
resolution for the rest of the chain." This second point is a real,
named tension between two PRD texts: `REQ-SB-35`'s own governance concern
versus `REQ-SB-36`'s own explicit Acceptance text, "the whole chain runs
end-to-end without requiring approval at any step." Neither text
resolves the other; recording this honestly rather than silently picking
one side is required per the analyst's own mandate to flag contradictory
inputs rather than guess.

**Resolution:** Not resolved in this pass — no operator was available to
decide live. `REQ-SB-35-US-01`'s own Acceptance Criteria are written to
be satisfiable under either placement-mechanism choice (mirrors
`REQ-SB-20-US-01`'s own precedent for handling an open mechanism
question), and its own Scenario 4 resolves the narrower "what happens on
genuine uncertainty" question via direct synthesis of `REQ-SB-33`'s
honesty standard and `REQ-SB-36`'s full-autonomy requirement (proceed and
write, but disclose uncertainty honestly rather than fabricate
confidence) — but this does NOT resolve the separate, still-open
new-top-level-area governance question, which remains a genuine
product/architecture judgement call for a human or the architect at
`/plan-tasks`.

**Resolving artefact:** _pending_ — needs a human decision on (a) the
placement mechanism (distinct agent vs. shared skill) and (b) whether
new-top-level-area creation specifically warrants a different check than
`REQ-SB-36`'s own blanket no-approval rule, before `/plan-tasks` can
commit to a task breakdown with confidence. See
`Implementation/UserStories/REQ-SB-35-US-01-vault-filing-expert.md`'s own
`## Notes` and `REVIEW-QUEUE.md`.

**Status:** Open

**Update, 2026-08-12 — Resolved.** Operator decided both points directly,
recorded verbatim in `Documentation/PRD.md`'s own `REQ-SB-35` breadcrumb:
(a) **"This is an Agent"** — the Vault Filing Expert is a distinct agent
in the registry, reached via `REQ-SB-20`'s Hub routing, not a shared
skill; (b) a tag or subfolder within an existing top-level vault area
proceeds autonomously (unchanged from `REQ-SB-36`'s own "fully
autonomous" framing), but proposing a wholly new top-level vault area
pauses for the operator's explicit approval — a scoped exception reusing
`REQ-SB-21`/`ADR-020`'s existing Supervised-mode/Pending-Approvals
machinery for this one action type only, not a change to the agent's own
general working-mode assignment. `REQ-SB-35-US-01` re-specced in place to
reflect both resolutions (two new Tier-1/Tier-2 Acceptance Criteria
scenarios plus a decline-handling edge case), `gate:` reset to `clear`.

**Resolving artefact:** `Documentation/PRD.md`'s `REQ-SB-35` breadcrumb
(2026-08-12 update) and `Implementation/UserStories/
REQ-SB-35-US-01-vault-filing-expert.md` (2026-08-12 re-spec).

**Status:** Resolved

## ESC-016: REQ-SB-36's own premise that "the Anthropic Claude Provider... [is] already configured" is contradicted by the real codebase — no real Anthropic client exists anywhere; the web-search mechanism itself is also undecided — 2026-08-12

**Category:** unclear-requirement

**Trigger:** `REQ-SB-36`'s own PRD breadcrumb (2026-08-12, operator-
authored) states directly: "the Research Expert's research comes from
both operator-supplied documents and real web search, using the
Anthropic Claude Provider (`REQ-SB-19`, already configured) specifically
for the research capability." Direct inspection of the real codebase
this pass (`src/backend/app/business/provider_registry.py`,
`src/backend/requirements.txt`, `src/backend/.env.example`,
`src/backend/app/business/agent_orchestration/model_factory.py`) found
this premise does not hold: `provider_registry._REAL_CLIENT_PROVIDER_IDS
= {"compass"}` — a small, hardcoded set confirmed both by this pass's own
direct read and by `MEMORY.md`'s own standing Constraints entry — means
no Provider other than `"compass"` has ever been wired to a real client;
no "Anthropic Claude" Provider entry is even seeded anywhere (only
`"compass"` self-seeds); `requirements.txt` has no `anthropic`/
`langchain-anthropic` package (only `langchain-openai`); `.env.example`
has no Anthropic-related config key; and `model_factory.py` (`ADR-015`)
is `langchain_openai.ChatOpenAI`-only, an OpenAI-wire-format abstraction
Anthropic's own native Messages API is not compatible with. This is a
real, code-grounded contradiction between the PRD's own stated premise
and the actual system, not a matter of interpretation.

**Resolution:** Not resolved in this pass — no operator was available to
decide live. `REQ-SB-36-US-01`'s own scope is written to account for this
honestly: it treats the real Anthropic (or equivalent) API client as new,
real work this story must build (either extending `model_factory.py` to
support a non-OpenAI-wire client, or a new standalone client module
mirroring `app/data_access/compass_client.py`'s own precedent), not
pre-existing plumbing it can simply call. Separately, the exact
web-search mechanism itself (Anthropic's own native server-side
web-search tool vs. a custom search-API-plus-synthesis approach) is also
genuinely undecided — mirrors `REQ-SB-27-US-01`'s own "what is a skill,
mechanically" flagging precedent.

**Resolving artefact:** _pending_ — needs a human/architect decision on
(a) how the real Anthropic client gets built and wired (extend
`model_factory.py`, or a new sibling client module), and (b) the exact
web-search mechanism, before `/plan-tasks` can commit to a task
breakdown with confidence. See `Implementation/UserStories/
REQ-SB-36-US-01-web-research-skill.md`'s own `## Context`/`## Notes` and
`REVIEW-QUEUE.md`.

**Status:** Open

**Update, 2026-08-12 — Resolved.** Operator decided directly, quoted
verbatim in `Documentation/PRD.md`'s own `REQ-SB-36` breadcrumb ("Yes add
Anthropic APIs Support"): building a real Anthropic Provider integration
(new `anthropic`/`langchain-anthropic` dependency, a real client,
credential wiring, extending `REQ-SB-19`'s already-`Done` Provider
registry with an actual working entry) is confirmed in scope, specifically
to give the Research Expert real web-search capability. The web-search
mechanism itself is also confirmed: Anthropic's own server-side web-search
tool, reached once the real client exists — the exact tool-use wiring is
left to `/plan-tasks` as ordinary implementation latitude, not a further
open fork. `REQ-SB-36-US-01` re-specced in place to reflect both
resolutions, `gate:` reset to `clear`.

**Resolving artefact:** `Documentation/PRD.md`'s `REQ-SB-36` breadcrumb
(2026-08-12 update) and `Implementation/UserStories/
REQ-SB-36-US-01-web-research-skill.md` (2026-08-12 re-spec).

**Status:** Resolved

## ESC-017: `REQ-SB-35-US-01`'s and `REQ-SB-36-US-02`'s own `## Dependencies` sections both assert `REQ-SB-21-US-01`/`ADR-020` is "(Done)"/"satisfied already" — direct code and story-file inspection during this architecture pass found this factually wrong; the Pending-Approvals and Working-Mode mechanisms both ADR-021 (Tier 2) and ADR-023 (Autonomous-mode check) depend on do not exist in the real codebase — 2026-08-12

**Category:** other

**Trigger:** Architect pass (`/plan-tasks` step 1) for `REQ-SB-35-US-01`/
`REQ-SB-36-US-01`/`REQ-SB-36-US-02`. Both `REQ-SB-35-US-01`'s and
`REQ-SB-36-US-02`'s own `## Dependencies` sections state, verbatim,
`REQ-SB-21-US-01`/`ADR-020 (Done)` — `REQ-SB-35-US-01`: "Already `Done`, so
this dependency is satisfied — real composition work at `/plan-tasks`, not
a blocker"; `REQ-SB-36-US-02`: listed under "Satisfied already." Per this
architect's own contract ("read `ADR-020`... to see the real current shape
of that machinery before deciding whether it already generalizes... or
needs extension"), `Implementation/UserStories/REQ-SB-21-US-01-agent-
working-modes.md` was read directly rather than trusted from the other two
stories' own prose. Its own frontmatter reads `status: Draft`, `gate:
flagged`; its own body confirms it was reset `Ready → Draft` after `ADR-020`
corrected `ADR-018` (a re-spec, resolving `ESC-013`'s "re-spec both
stories" half), and that its decomposer has **not yet re-run** since —
its `T01`-`T08` tasks are explicitly recorded as "left in place... but
flagged stale." Direct inspection of the real `src/backend` source tree
confirms zero code exists for this mechanism: no `app/business/
pending_approval_registry.py`, no `app/business/working_mode_registry.py`,
no `app/api/pending_approvals_router.py`; `app/api/agents_router.py`'s real
`_invoke_action` has no working-mode gate, no `trigger` parameter, and no
`mutates` handling of any kind — the entire mechanism `ADR-018`/`ADR-020`
*design* (both remain `Accepted`) has never been decomposed into `Ready`
tasks in its corrected shape, let alone built.

This is load-bearing for both architecture passes this session actually
needed to produce: `ADR-021`'s Vault Filing Expert Tier 2 (new-top-level-
area approval, reusing `ADR-018`'s Pending-Approvals workflow store) and
`ADR-023`'s delegated knowledge-bootstrap chain (which needs both
`working_mode_registry.get_agent_working_mode(...)` for its Autonomous-mode
Constraint check, and `pending_approval_registry`/`pending_approvals_
router.py` for Tier 2's own resolution). Both ADRs were written anyway —
designing against `ADR-018`'s already-`Accepted`, unedited-by-`ADR-020`
schema (points 1, 2, 4, 6, 7, 8) with confidence — but their own coder
tasks cannot yet be given a real `depends_on` edge onto a `Ready`
`REQ-SB-21-US-01` task, mirroring `ESC-011`'s own precedent exactly (a real
cross-story code dependency recorded honestly rather than a fabricated
task-id reference or a silent assumption that "Done" in another story's own
prose can be trusted without checking).

**Resolution:** Not resolved in this pass — resolving it means running
`REQ-SB-21-US-01` through a fresh decomposer pass (re-deriving `T04`/`T05`
against `ADR-020`'s corrected gate, per that story's own already-recorded
note) and then building all 8 of its tasks, which is real forward work for
a future `/plan-tasks` + `/implement-sprint` pass on `REQ-SB-21-US-01`
itself, not something this architecture pass can shortcut. This pass
proceeds per Pipeline.md's "forward is autonomous by exception" rule: both
`ADR-021` and `ADR-023` are written in full (nothing about this blocker
prevents authoring the design), `REQ-SB-35-US-01`'s Tier-1 scope (Scenarios
1, 2, 5, 6, 7, 8 — no Pending-Approvals dependency at all) and
`REQ-SB-36-US-01` (no dependency on `REQ-SB-21-US-01` at all) are fully
unblocked for the decomposer's next step. `REQ-SB-35-US-01`'s Tier-2
Scenarios (3, 4) and `REQ-SB-36-US-02`'s own chain (which needs both the
Autonomous-mode check and Tier 2) are real, honestly-named blocked surface
for the decomposer to handle the same way `REQ-SB-27-US-01-T02` handled its
own analogous gap (`ESC-011`) — an individually-flagged, `depends_on: []`
task with a prominent "blocked, do not start" note, not a fabricated task
ID and not silent omission.

**Resolving artefact:** _pending_ — needs `REQ-SB-21-US-01` run through its
own corrected decomposer pass (producing real, `Ready` task ids for
`working_mode_registry.py` and `pending_approval_registry.py`/
`pending_approvals_router.py`), after which a follow-up decomposer pass on
`REQ-SB-35-US-01`/`REQ-SB-36-US-02` replaces any placeholder `depends_on: []`
on their own Tier-2/Autonomous-mode-check tasks with the real ids. See
`REVIEW-QUEUE.md`.

**Status:** Open

**Update, 2026-08-12 (`REQ-SB-21-US-01`'s own `/plan-tasks` pass — the
corrected decomposer step this entry names has now run).** `REQ-SB-21-US-01`'s
`T04`/`T05` were re-derived against `ADR-020`'s corrected two-axis gate
(`T05` needed no logic change at all — `ADR-020` point 4 confirms its own
outcome is unaffected; `T04` was rewritten in place, and — a second,
independent finding — composed around the REAL current `agents_router.py`,
which had structurally drifted from the original stale sample via
`REQ-SB-25-US-01`/`REQ-SB-26-US-01`'s intervening async chat/memory work,
both shipped after the original `T01`-`T08` decomposition). One new task,
`T09` (`agent_registry.py`'s `"mutates"` classification + `get_action`
helper, `ADR-020` point 1), was created — genuinely new scope no prior task
covered. All 9 tasks (`T01`-`T09`) are now `status: Ready`; the story itself
is `status: Ready` (`gate` stays `flagged` — `ADR-020`'s own human review is
still open). The real task ids to wire onto `REQ-SB-35-US-01`'s Tier 2 and
`REQ-SB-36-US-02`'s Autonomous-mode check are recorded in
`REQ-SB-21-US-01`'s own `## Notes`: `T02` (working mode), `T03`+`T06` (the
Pending-Approvals store + its HTTP surface), and `T04`+`T09` if either
story's own gate logic needs the corrected two-axis gate itself. **This
entry stays `Open`, not `Resolved`** — the real, load-bearing gap it names
(a currently unmet blocking prerequisite) is not closed until (a)
`REQ-SB-21-US-01`'s own tasks are actually built and live-verified via
`/implement-sprint`, and (b) a follow-up decomposer pass on
`REQ-SB-35-US-01`/`REQ-SB-36-US-02` replaces their own placeholder
`depends_on: []` with these real ids — neither has happened yet.

**Status:** Open (design/task-planning complete; build + cross-story
`depends_on` wiring still pending)

**Update, 2026-08-12 (`REQ-SB-35-US-01`/`REQ-SB-36-US-01`/`REQ-SB-36-US-02`'s
own decomposer pass — the follow-up wiring step this entry named has now
run).** All three stories' decomposition is complete: `REQ-SB-35-US-01` (8
ACs locked, `T01`-`T03`), `REQ-SB-36-US-01` (4 ACs locked, `T01`-`T06`, no
`REQ-SB-21-US-01` dependency at all), `REQ-SB-36-US-02` (6 ACs locked,
`T01`-`T04`). The real task ids `REQ-SB-21-US-01`'s own `## Notes` named
are now wired in directly, not a placeholder: `REQ-SB-35-US-01-T03` (Tier
2) depends on `REQ-SB-21-US-01-T03`+`T06`; `REQ-SB-36-US-02-T01` depends
on `REQ-SB-21-US-01-T09`, and `REQ-SB-36-US-02-T02` (the Autonomous-mode
check) depends on `REQ-SB-21-US-01-T02` directly, plus
`REQ-SB-35-US-01-T02`/`T03` transitively for Tier-2's own resolution (this
story never touches `pending_approval_registry`/`pending_approvals_router`
itself, so no redundant second direct edge was added). **This entry is now
fully resolved** — every real dependency this entry named has a real,
`status: Ready` task id wired onto it; nothing further is blocked by
`REQ-SB-21-US-01` not yet being `Done` (that remains an ordinary
`/plan-sprints`-time sequencing concern, `depends_on_sprints`, not a
decomposer-level gap). One genuinely new, different finding surfaced
during this same pass (`REQ-SB-36-US-02`'s own Scenario 3, blocked on
`REQ-SB-29-US-01`, which has never been decomposed) — recorded separately
as `ESC-018`, not folded into this entry, since it names a different
blocking story with a materially different resolution shape (no decomposer
pass has run on `REQ-SB-29-US-01` at all, unlike `REQ-SB-21-US-01`).

**Resolving artefact:** `Implementation/UserStories/REQ-SB-35-US-01-vault-
filing-expert.md`, `Implementation/UserStories/REQ-SB-36-US-02-agent-
knowledge-bootstrapping-delegated-research-chain.md` (both 2026-08-12
decomposition passes), plus `Implementation/Tasks/REQ-SB-35-US-01-T03-
tier-2-approval-resolution.md` and `Implementation/Tasks/REQ-SB-36-US-02-
T01-compass-expert-agent-and-build-knowledge-action.md`/`REQ-SB-36-US-02-
T02-knowledge-bootstrap-orchestration.md`'s own real `depends_on` edges.

**Status:** Resolved

## ESC-018: `REQ-SB-36-US-02`'s own Scenario 3 ("the newly-expert agent can draw on the filed content afterward") composes entirely with `REQ-SB-29-US-01`'s own vault-scope-assignment/retrieval mechanism — that story has not been decomposed into tasks at all, unlike `REQ-SB-21-US-01`, so no real task id exists anywhere to wire this AC's own verification onto — 2026-08-12

**Category:** other

**Trigger:** Decomposer pass (`/plan-tasks` step 2) on `REQ-SB-36-US-02`.
The parent story's own `## Dependencies` already named this plainly:
"Related to, needed for Scenario 3 only: `REQ-SB-29-US-01` (`Draft`, `gate:
clear`, not yet `Ready`/built)... Scenarios 1/2 (the delegation/filing
chain itself) do not depend on it." This decomposer pass confirmed, by
direct glob against `Implementation/Tasks/`, that **zero**
`REQ-SB-29-US-01-T*.md` files exist anywhere — that story is still
`status: Draft` and has never been run through its own decomposer step at
all, a materially different (and more blocking) state than
`REQ-SB-21-US-01`'s own situation this same session (which HAD been
decomposed, just not yet built — `ESC-017`). There is no real, `Ready`
task id anywhere to wire `AC-03`'s own verification onto, and none can be
fabricated per Pipeline.md hard rule 2 / this decomposer's own contract.

**Resolution:** Not resolved in this pass. Mirroring `ESC-011`'s own
established precedent exactly: `AC-03` (Scenario 3) is locked regardless
(per Pipeline.md's "forward is autonomous by exception" rule — nothing
about this blocker prevents authoring/locking the AC), and a dedicated
task, `REQ-SB-36-US-02-T04`, is created to hold its own eventual
verification, left `depends_on: []` with a prominent "⚠️ BLOCKED — do not
start" section, rather than a fabricated task id or a silently-omitted
AC. Unlike `ESC-011`'s own precedent (which held the entire parent story
at `Draft` because of its one blocked task), this decomposer pass made a
different, explicitly-flagged judgement call: `REQ-SB-36-US-02` itself
advances to `status: Ready` (its own literal `(a)`/`(b)`/`(c)` Ready
criteria are genuinely satisfied — every AC locked, every locked AC
tagged, `depends_on` acyclic), while only `T04` is individually held at
`status: Draft`/`gate: flagged` — `T01`/`T02`/`T03` proceed to `Ready`
since none of them is actually blocked. This divergence from `ESC-011`'s
own full-story-Draft choice is recorded in `REVIEW-QUEUE.md` for explicit
human confirmation, not silently adopted as the new default going
forward.

**Resolving artefact:** _pending_ — needs `REQ-SB-29-US-01` run through its
own decomposer pass (producing at least one real, `Ready` task id for its
vault-scope-assignment/retrieval mechanism), after which a follow-up
decomposer pass on `REQ-SB-36-US-02-T04` replaces its own `depends_on: []`
with the real id and resets its `status`/`gate` to ordinary lockstep with
the rest of the story. See `REVIEW-QUEUE.md`.

## ESC-019: Operator correction mid-`/implement-sprint` (`SPRINT-022`) reverses `ADR-022` point 3's fixed-`"anthropic-claude"`-Provider-id design for `web_research` — invoking agent's own linked Provider must be resolved instead, and Compass's own real web-search capability had to be investigated, not assumed — 2026-08-12

**Category:** adr-deviation

**Trigger:** Mid-build on `REQ-SB-36-US-01-T04`/`T05` (all of `T01`-`T03`
already built and verified against `ADR-022` point 3's original design —
`web_research` resolving credentials via a single hardcoded
`provider_registry.get_provider("anthropic-claude")` by-id lookup, not by
whichever agent invoked it), the operator sent a direct correction, quoted
verbatim: "The Anthropic_API_KEY Should be a Provider added to the
Providers List — if I linked the Research Agent to Compass, use Compass.
Don't Halt on that." This is a genuine reversal of `ADR-022` point 3's own
explicit design choice (and narrows, without overturning, point 5's own
rejected-alternative reasoning about leaking `agent_id` into an MCP tool's
public schema) — the invoking agent's own linked Provider
(`provider_registry.get_agent_provider(agent_id)`, the exact per-agent
lookup `ADR-022` point 3 explicitly said "no existing per-agent lookup
fits" for) must now be resolved instead, dispatching to whichever real
backend that agent's own linked Provider actually supports.

**A second, real technical question was raised and had to be investigated
before implementing, per the operator's own explicit instruction — not
guessed either way:** does Compass/GPT-5 (Core42's gateway) expose a real,
hosted server-side web-search tool structurally equivalent to Anthropic's
own? Investigated live: `app/data_access/compass_client.py`'s own real
request payload carries no `tools`/search parameter of any kind; the
sibling `agentic-map` project's own `services/gateway/compass.py` supports
generic OpenAI-style client-side function-calling (the caller declares a
tool, the model requests it, the caller must still execute it itself) but
not a hosted server-side tool; and that same sibling project's own
`services/gateway/providers.py` routes its own `web_search`-capable agents
through a **separate, dedicated Perplexity Sonar provider** specifically
because Compass/GPT-5 itself cannot do this — real, independent evidence
from a team that already solved this exact problem. Fabricating a
"researched" result from a plain Compass completion would violate
`REQ-SB-33`'s own already-shipped grounding/no-hallucination guardrail.

**Resolution:** `web_research(query: str, agent_id: str) -> dict`
resolves `provider_registry.get_agent_provider(agent_id)`; dispatches to
the real `anthropic_client.web_search` call only when that Provider's id
is `"anthropic-claude"` and `has_real_client("anthropic-claude")`;
otherwise (Compass, or no Provider) returns the exact same honest "not yet
available" shape Scenario 4/`AC-04` already defines — never a fabricated
result for any linked Provider. `skill_registry.invoke_skill` injects
`agent_id` into the handler call only when the resolved handler's own
signature declares that parameter (`inspect.signature`), so
`skills_router.py`'s own request-body contract and
`diagram-understanding`'s zero-arg call are both unaffected; `agent_id`
comes from `invoke_skill`'s own already-authenticated parameter, never
from the request body. `T01`-`T03` (dependency, Anthropic client, Provider
seeding) are unaffected — the operator's own words explicitly confirm the
"Anthropic Claude" Provider entry is "still being added, just not the ONLY
path." Verified live end-to-end against the corrected design (real HTTP,
`REQ-SB-36-US-01-T05`'s own AC-01/AC-02 round trip): a `todo-capture`
agent linked to `"compass"` gets the honest not-available response; the
same agent reassigned to `"anthropic-claude"` correctly dispatches a real
Anthropic API call (confirmed via the real, honest `401` it returns, since
no real `ANTHROPIC_API_KEY` is provisioned in this environment — see the
separate, purely-environmental credential gap recorded in
`REVIEW-QUEUE.md`, unrelated to this correction's own correctness); a
`vault-qa` agent with no grant still gets `403`, unaffected.

**Resolving artefact:** `Implementation/Architecture/ADR.md` → `ADR-022`'s
own "Correction" addendum (this same date); `Implementation/Tasks/
REQ-SB-36-US-01-T04-web-research-skill-tool.md` and `-T05-invoke-skill-args-
and-router-body.md`'s own Implementation Logs record the as-built deviation
from each task's own literal code sample.

**Status:** Resolved

**Status:** Open

---

## ESC-020: REQ-SB-37 (Agent Creation) directly reverses `ADR-011` point 2 — the persisted-registry mechanism needs a superseding ADR, and the PRD's own breadcrumb leaves whether a user-created agent can define bespoke actions genuinely open — 2026-08-13

**Category:** unclear-requirement

**Trigger:** `REQ-SB-37`'s own PRD breadcrumb (2026-08-13, operator-
directed, verbatim: "Add the Creation of Agents As we have no place to
create an agent") is explicit that this reverses a standing decision, not
extends one: `ADR-011` point 2 established "agent identity/type/actions
stay hardcoded... not a persisted/mutable concern," and every subsequent
ADR that touched agents this session (`ADR-014`, `ADR-017`, `ADR-018`,
`ADR-020`, `ADR-021`, `ADR-023`) built on that same assumption without
reopening it — each was careful to compose *alongside* `agent_registry.py`
without modifying it. `REQ-SB-37` cannot be built the same way: live
inspection of `section_registry.py`, `provider_registry.py`,
`agent_keywords.py`, `working_mode_registry.py`, and `skill_registry.py`
confirms every one of them self-heals its own default per-agent assignment
by iterating `agent_registry.list_agents()` — so a user-created agent only
gets picked up by all five already-`Done` property registries automatically
if `list_agents()`/`get_agent()` themselves start reporting it. That is a
real, load-bearing change to a read path five already-`Done` modules
depend on, not a "compose alongside, don't touch" extension like every
prior agent ADR this session. Separately, the breadcrumb names a second,
independent open question, explicit that it is "a real, load-bearing open
question, not an implementation detail": each of this codebase's existing
actions (`run_capture_now`, `rebuild_person_note`, `ask_question`, etc.) is
backed by specific, real Python code in `agents_router.py`'s
`_ACTION_HANDLERS` — there is no generic "any action" mechanism anywhere —
so whether a user-created agent should ever be able to define its own
bespoke action is a genuine architectural fork (zero-actions/chat-routing-
only vs. a much larger, separate generic/no-code action mechanism), not
something `/spec` can resolve by picking one side.

**Resolution:** Not resolved in this pass — no operator decision was
requested live during `/spec`. `REQ-SB-37-US-01` is written to be
satisfiable under the narrower, safely-precedented reading only: a created
agent's Section/Provider/Keywords/Working-mode/Skill-grants are made
configurable via the exact surfaces `REQ-SB-18/19/20/21/27` already built
(directly grounded in the PRD's own Acceptance text, which does not list
actions among the configurable properties), and a created agent starts with
an empty `actions: []` list — mirroring the already-`Done`
`vault-filing-expert`/`compass-expert` "start empty" precedent from
`REQ-SB-36`. The custom-bespoke-actions fork itself is left open, flagged
for a human product decision, not guessed. The persisted-registry mechanism
(new sibling `.second-brain/agents.json` + module, mirroring `ADR-014`'s
Section/Provider shape, vs. some other persisted shape) is left for the
architect's own `/plan-tasks` pass to resolve via a superseding ADR over
`ADR-011` point 2 — an ADR-creation trigger, not an analyst-level call.
Also found and recorded honestly, not silently carried forward: the PRD's
Acceptance text calls Vault Scope one of the "already-existing" properties,
but `REQ-SB-29-US-01` (Vault Scope) is still `Draft` with no built surface
— `REQ-SB-37-US-01` excludes Vault Scope from its own scope accordingly.

**Resolving artefact:** _pending_ — needs a human decision on the
custom-bespoke-actions fork (at minimum, confirming "zero actions,
chat/routing-only" is acceptable for this pass), and the architect's own
`/plan-tasks` pass to write the superseding ADR over `ADR-011` point 2 for
the persisted-registry mechanism. See
`Implementation/UserStories/REQ-SB-37-US-01-agent-creation.md`'s own
`## Notes` and `REVIEW-QUEUE.md`.

**Status:** Open

## ESC-021: REQ-SB-01's re-index trigger mechanism (on-demand vs. scheduled vs. live file-watch) is genuinely undecided by the PRD — 2026-08-13

**Category:** unclear-requirement

**Trigger:** `/spec REQ-SB-01` (first-ever spec pass on this requirement —
neither `REQ-SB-01` nor `REQ-SB-02` had any story, not even `Draft`, before
this run, despite being the actual MVP). The PRD's own Acceptance text —
"re-running the index after the vault changes picks up additions, edits, and
deletions without manual intervention" — commits to what a re-index run must
accomplish (a full, honest reconciliation, not a manually-fed diff) but says
nothing about when or how re-indexing itself is triggered. Direct inspection
of the real codebase found no precedent that settles this either way: this
project already has a recurring-schedule pattern (`REQ-SB-07`, hourly +
app-start, with missed-run catch-up) that a vault re-index could plausibly
reuse; but it also has no precedent anywhere for live filesystem watching,
which would be a materially bigger, unprecedented addition. An explicit
on-demand rebuild call/endpoint is the most literal reading of "the index is
re-run" and the smallest addition. All three readings equally satisfy the
PRD's literal wording; picking one silently would be guessing on foundational
work every other vault-query feature depends on, per the analyst's
"flag rather than guess" mandate.

**Resolution:** Resolved 2026-08-13 — operator's delegated "sane defaults"
decision (relayed via the coordinating session, rather than the operator
deciding each individual open question personally): **both** an explicit
on-demand re-index call/endpoint (needed regardless, for immediate
correctness after any vault change) **and** wiring into `REQ-SB-07`'s
already-`Done` hourly-plus-app-start scheduled capture cadence, mirroring
that story's own established pattern exactly. Live filesystem watching is
explicitly excluded this pass — disproportionate technical lift (watcher
infrastructure, debouncing) for a personal, single-user vault, matching
this project's own repeated "proportionate first, escalate only if proven
insufficient" precedent (`ADR-011`'s reasoning).

**Resolving artefact:**
`Implementation/UserStories/REQ-SB-01-US-01-vault-indexing.md` (2026-08-13
update — Context, Constraints, Non-Goals, and Acceptance Criteria Scenarios
8-9 all updated to match; `gate:` reset to `clear`).

**Status:** Resolved

## ESC-022: REQ-SB-02's search-ranking technique and wikilink-graph navigation's visual shape are genuinely undecided by the PRD — 2026-08-13

**Category:** unclear-requirement

**Trigger:** `/spec REQ-SB-02`. The PRD's own Acceptance text commits to a
real, ranked-not-substring search ("a search query that returns relevant
notes ranked by relevance, not just notes containing an exact substring
match") and to wikilink-graph navigation ("filter or navigate by tag and by
wikilink graph"), but names neither a concrete ranking technique nor a
concrete navigation shape. `Documentation/PRD.md`'s own P2 section
(`REQ-SB-06`) and `Implementation/Plans/2026-08-10-agentic-map-requirement-
port.md` together resolve the *class* of mechanism (a real ranked keyword/
full-text mechanism this pass, semantic/embedding search explicitly deferred
to `REQ-SB-06`/P2) — but not the *specific* algorithm within that class
(e.g. term-frequency/field-weighted scoring vs. another concrete technique),
which is an architecture-level decision. Separately, "navigate... by
wikilink graph" is genuinely ambiguous between a textual forward-link/
backlink list on a note-detail view and a visual graph canvas (this project
already has two very different precedents for each shape elsewhere —
Obsidian's own native graph view, and Agents Map's rendered canvas) — a
design decision, not a spec decision. Confirmed separately: no
`html-prototype/` screen covers any part of this requirement at all
(`net-new-design-needed`, recorded on the story itself, not duplicated as
its own ESC entry).

**Resolution:** Resolved 2026-08-13 — operator's delegated "sane defaults"
decision (relayed via the coordinating session): ranking is a real ranked
keyword/full-text relevance score (e.g. BM25-style term-frequency scoring
across frontmatter/tags/body, boosted by field) — not a bare substring
match, not embeddings/semantic search (already correctly deferred to
`REQ-SB-06`/P2); the exact library/implementation choice within that class
is ordinary `/plan-tasks` latitude, not a requirement-level question.
Wikilink-graph navigation is a link list — forward/outgoing links and
backward/incoming links (backlinks), both textual and clickable — not a
visual/interactive graph canvas (force-directed layout, zoom/pan), which is
disproportionate scope for the MVP's first browse/search pass and deferred
as a possible future enhancement. The separate, still-open
`net-new-design-needed` flag (no `html-prototype/` screen exists for this
requirement at all) is **not** resolved by this decision — it still needs a
real `/design REQ-SB-02` pass and human browser sign-off; see the story's
own `## Notes` and `REVIEW-QUEUE.md`.

**Resolving artefact:**
`Implementation/UserStories/REQ-SB-02-US-01-browse-and-search.md`
(2026-08-13 update — Context, Constraints, and Non-Goals all updated to
match; `gate:` stays `flagged`, narrowed to `net-new-design-needed` only).

**Status:** Resolved

**Status:** Open

## ESC-023: REQ-SB-03/04/05 (the real, external Hermes integration) have no live Hermes connection anywhere in this codebase; the shared MCP server ADR-015 built is architecturally reusable but unauthenticated and never exercised by an external client; REQ-SB-03 also has a hard, unbuilt dependency on REQ-SB-01/REQ-SB-02 — 2026-08-13

**Category:** unclear-requirement

**Trigger:** `/spec` pass on `REQ-SB-03` (Conversational Agent Access via
Hermes), `REQ-SB-04` (Agent Vault Write Access), `REQ-SB-05` (Content
Ingestion Path) — the three PRD requirements that together constitute
Second Brain's actual, real integration with the external Hermes system,
none of which has ever had a story before this pass. Direct grep across
`src/backend` and `Implementation/Architecture/` for "hermes" (case-
insensitive) confirmed the operator's own suspicion precisely: every
existing mention is either a docstring/comment naming Hermes as a *future*
consumer of infrastructure built for a different purpose, or `MEMORY.md`'s
own standing constraint that Hermes is external, not something this project
builds. `Implementation/Architecture/architecture.md` → *External Services*
still reads "Hermes ... — planned integration, not yet built." **No real
Hermes connection, credential, endpoint configuration, or live round-trip
exists anywhere in this codebase.**

Two things were found that meaningfully change the shape of this
uncertainty from what a from-scratch read of the PRD would suggest:

1. **The client/server direction question is already architecturally
   settled, not open.** `ADR-015` (`Accepted`, 2026-08-11, written for
   `REQ-SB-20`/`25`/`26`/`27` — Second Brain's own in-app LangGraph agent
   orchestration) adopted a **shared MCP server**: `app/api/mcp_server.py`
   is a real, live `FastMCP` instance mounted at `app.mount("/mcp", ...)` in
   `app/main.py`, registering four read-only `@mcp.tool()`s
   (`app/business/vault_query_tools.py`'s thin wrappers over
   `vault_writer` primitives). Both the module's own docstring and
   `architecture.md` state directly that this server exists to be "reused
   both ways" — by Second Brain's own in-app agent (via
   `agent_orchestration/mcp_client.py`'s loopback client) **and by Hermes's
   own external orchestration, over the same mounted endpoint.**
   Confirmed: Second Brain is architecturally the MCP **server**; a
   Hermes-side agent would be an MCP **client** reaching `/mcp` — the same
   shape as the in-app agent's own loopback client, just from off-machine.
   This was built for a different requirement, not REQ-SB-03, but is
   directly reusable.
2. **That endpoint has never been exercised by anything other than the
   same-process loopback client, and carries zero authentication today.**
   Direct reading of `app/main.py` confirms `CORSMiddleware` is scoped only
   to the Vite dev server's browser origins (irrelevant to a server-to-
   server MCP client, which CORS does not apply to at all), and
   `app.mount("/mcp", mcp_server.streamable_http_app())` has no auth
   dependency, API key, or bearer-token check of any kind. This is a
   real, concrete, material gap for wiring a genuinely external system to
   this endpoint — more so once `REQ-SB-04` would add write-capable tools
   to the same unauthenticated server.

Beyond the shared foundation, each story surfaces its own additional,
genuinely open question, none guessable from this repo alone:

- **`REQ-SB-03`:** its own PRD text names its mechanism explicitly — "the
  agent reasons over the indexed vault (per REQ-SB-01/REQ-SB-02)." Both are
  confirmed `Draft`/`gate: flagged`, unbuilt (`REQ-SB-01-US-01`,
  `REQ-SB-02-US-01` — "the least-started requirements in the whole PRD,"
  per `ESC-008`). The four tools currently registered on the shared MCP
  server are narrow folder/tag-enumeration helpers built for `REQ-SB-35`'s
  Vault Filing Expert, not a search/retrieval tool over arbitrary note
  content — there is no real vault-reasoning tool to expose to Hermes
  until REQ-SB-01/02 ship. This is a hard, literal blocking dependency.
- **`REQ-SB-04`:** the PRD's own text explicitly defers "what an agent may
  create/modify, and under what confirmation" to this spec pass. A scoping
  approach is proposed (tag/folder scope reusing `REQ-SB-29`'s concept, plus
  a confirmation step reusing `REQ-SB-21`'s Supervised/Pending-Approvals
  precedent) — but both source concepts are themselves `Draft`/unbuilt
  (`REQ-SB-29-US-01`'s own "how scope is assigned" question is still open)
  or were designed for a different, in-app-only surface (`REQ-SB-21`'s
  approval UI has no established analog for a Hermes-originated proposal).
  Whether this proposal is real product direction, versus the analyst's own
  best-fit guess, is not decided here.
- **`REQ-SB-05`:** the transport mechanism by which a Hermes-side
  attachment would actually reach Second Brain (a new MCP tool, a dedicated
  HTTP endpoint Hermes posts to, or whatever Hermes's own skill-wrapping
  convention dictates, per `MEMORY.md`'s integration-sourcing precedence
  constraint) is a real external-protocol unknown this repo has no record
  of. Its own literal PRD text ("lands as a new vault note") also reads as
  a materially different retention default than the closest existing
  precedent, `REQ-SB-28`'s in-app-chat upload story (temporary-for-
  processing-only, never vault-retained by default) — resolved here by a
  literal reading of REQ-SB-05's own Acceptance text, not by assuming
  REQ-SB-28's default carries over.

**Resolution:** Not resolved in this pass — no operator was available to
decide live. Three `Draft` stories were written
(`REQ-SB-03-US-01`/`REQ-SB-04-US-01`/`REQ-SB-05-US-01`, one per requirement,
each with its own Acceptance Criteria, Dependencies, and Constraints,
cross-referencing this shared foundational finding rather than repeating a
full investigation three times), each `gate: flagged`. All three are
genuinely `Draft`-appropriate — none was guessed into a build-ready shape.

**Resolving artefact:** _pending_ — needs human decisions on (a) whether a
real, reachable Hermes deployment exists today and how it would reach/be
reached by Second Brain; (b) the `/mcp` endpoint's authentication approach
before any external client is wired to it; (c) `REQ-SB-04`'s proposed
scoping/confirmation approach (confirm, reject, or redirect); (d)
`REQ-SB-05`'s transport mechanism and content policy. See
`REQ-SB-03-US-01`/`REQ-SB-04-US-01`/`REQ-SB-05-US-01`'s own `## Notes` and
the `REVIEW-QUEUE.md` entry for the concrete next steps. `REQ-SB-03` is
additionally blocked, independent of any human decision, on `REQ-SB-01`/
`REQ-SB-02` actually shipping.

**Status:** Open

**Update, 2026-08-13 — Operator decided two of the four open items directly
(via the coordinator), explicitly declined to guess on a third, and left a
fourth (REQ-SB-05's own transport mechanism) unaddressed:**

1. **(b) `/mcp` authentication — Resolved.** Yes, add real authentication
   before any non-loopback caller reaches `/mcp` — firmly in scope, not
   deferred, given `REQ-SB-04` would add write tools to the same server.
   Minimum-viable shape: a shared secret/API key check, mirroring this
   project's own existing `COMPASS_API_KEY`/`ANTHROPIC_API_KEY`
   Settings-based credential pattern (a new `HERMES_MCP_SHARED_SECRET`-
   shaped config value). The exact scheme (bearer token vs. another
   header-based mechanism) is left as ordinary `/plan-tasks` architect
   latitude — only the requirement-level "yes, real auth, minimum-viable
   shared-secret shape" was decided here. Landed as a new Scenario 4 and
   Constraint on `REQ-SB-03-US-01` (the story that first makes `/mcp`
   reachable from outside), not a separate requirement. `REQ-SB-04-US-01`
   inherits the same decision, at higher stakes (write-capable tools).
2. **(c) `REQ-SB-04`'s proposed scoping/confirmation approach — Confirmed
   as the accepted direction.** Tag/folder scope reusing `REQ-SB-29`'s
   concept, plus a confirmation step reusing `REQ-SB-21`'s Supervised/
   Pending-Approvals precedent, most plausibly by extending that existing
   in-app surface rather than inventing a Hermes-channel-native mechanism.
   This creates a real, load-bearing (but not spec-blocking) dependency:
   `REQ-SB-04-US-01`'s own scope-enforcement cannot be built for real until
   `REQ-SB-29-US-01` (still `Draft`/unbuilt, its own "how scope is
   assigned" question still open) actually ships — noted plainly in
   `REQ-SB-04-US-01`'s own `## Dependencies`/`## Notes`, not silently
   assumed away.
3. **(a) Real Hermes deployment reachability — explicitly, deliberately
   NOT resolved.** The operator was direct: this "genuinely cannot be
   decided by me, needs the operator's own real-world knowledge." This
   stays open, tracked here. **However, the operator drew a sharp line
   this entry now records precisely: this fact does NOT block `/spec`
   finalization or `/plan-tasks` architecture/task creation for any of the
   three stories — it only blocks real, live end-to-end verification at
   `/implement-sprint` time** (a coder can build and unit-test the `/mcp`
   server-side auth and, once `REQ-SB-01`/`REQ-SB-02` exist, the
   vault-query tools themselves, entirely without a live Hermes peer; what
   cannot be verified without one is an actual Hermes-to-Second-Brain round
   trip). This distinction is now reflected in all three stories' own
   `gate:` status (below) and is the same "design/build-complete vs.
   live-verified" split this file already uses elsewhere (e.g. `ESC-002`
   staying `Open` after `ADR-013`'s design while live verification was
   still pending).
4. **(d) `REQ-SB-05`'s own transport mechanism, and whether it composes
   with `REQ-SB-04`'s trust rule — untouched by this round of decisions,
   still fully open.** Neither the auth decision nor the REQ-SB-04 scoping
   decision resolves how a Hermes-side attachment would actually reach
   Second Brain, or whether an ingested write needs REQ-SB-04's own
   confirmation step. `REQ-SB-05-US-01` stays `gate: flagged` for this
   reason alone.

**Gate status after this update:** `REQ-SB-03-US-01` → `gate: clear` (both
of its own flagged questions resolved or explicitly reclassified as a
downstream `/implement-sprint` verification constraint; its REQ-SB-01/
REQ-SB-02 dependency is an ordinary sequencing fact, not a scope ambiguity).
`REQ-SB-04-US-01` → `gate: clear` (scoping approach confirmed, `/mcp` auth
resolved; its `REQ-SB-29-US-01` dependency is likewise an ordinary
sequencing fact, recorded plainly, not a flag). `REQ-SB-05-US-01` → stays
`gate: flagged` (item 4 above is entirely its own, unresolved).

**Status:** Open — items (b) and (c) resolved; item (a) deliberately left
open (by design, not oversight — needs the operator's own real-world
knowledge, and does not block forward progress on `/spec`/`/plan-tasks`);
item (d) unaddressed, still fully open, the reason `REQ-SB-05-US-01` alone
stays `gate: flagged`.

## ESC-024: REQ-SB-09's own concrete task source (Outlook tasks / agent-created follow-ups / manually-flagged emails) and its Task-note schema are both genuinely undecided by the PRD — 2026-08-13

**Category:** unclear-requirement

**Trigger:** `/spec REQ-SB-09`. The PRD's own acceptance text for
REQ-SB-09 states, verbatim, that "the concrete source of tasks (Outlook
tasks, agent-created follow-ups, manually flagged emails) is an open
question for `/spec` time, not decided here" — an explicit deferral, not
an oversight. Direct inspection of `app/data_access/outlook_com.py`
confirmed Outlook's own Tasks folder IS technically reachable today via
the same COM mechanism already used for mail/calendar
(`OlDefaultFolders.olFolderTasks = 13`), resolving the "does a reachable
API exist" half of the question — but the PRD names three candidate
sources with no stated preference among them, and the other two
(agent-created follow-ups, manually-flagged emails) would each require a
materially different, currently-nonexistent interaction mechanism, not a
same-pattern parameter change. Separately, a direct grep of
`Implementation/Plans/2026-08-10-vault-taxonomy-draft.md` (the document
that pre-resolved every other capture pipeline's schema, including
Meeting's, before its own story was written) found **zero matches** for
"Task"/"To-Do"/"Todo" — unlike Meeting, REQ-SB-09 has no resolved schema
anywhere in this codebase. Picking a source and inventing a schema
silently would be exactly the kind of guess among multiple equally-valid
options the analyst is required to flag rather than make, especially for
a schema every downstream task (My Day's To-Do drill-down, dedup
mechanics) would then be locked against.

**Resolution:** Resolved 2026-08-13 — the operator delegated this
decision to the orchestrating agent directly ("make the call yourself,
using sane defaults") rather than answering it personally. The
orchestrating agent confirmed `REQ-SB-09-US-01`'s own proposed default as
the final product decision: Outlook Tasks folder as the sole source for
this pass, with the Meeting/Email-shaped schema that story's own Context
proposed. No part of the original analysis was overridden or redirected.

**Resolving artefact:** `REQ-SB-09-US-01` (`## Context`/`## Notes`,
updated 2026-08-13)

**Status:** Resolved

## ESC-025: REQ-SB-11's own UI placement is genuinely undecided, and today's `agent_communication_history.json` recording is confirmed incomplete for the PRD's own "success, or error with detail" acceptance text — 2026-08-13

**Category:** unclear-requirement

**Trigger:** `/spec REQ-SB-11`. Two separate findings, both grounded in
direct code/file inspection, not assumed:

1. **No `html-prototype/` screen shows a chronological cross-agent
   activity log or a per-channel communication-status indicator** —
   confirmed by direct inspection of every existing screen, including
   `system-health.html` (`REQ-SB-31-US-01`, `Done`, that story's own
   Notes explicitly distinguishing its current-snapshot shape from this
   requirement's history/log shape and flagging this exact placement
   decision for whichever of the two was specced second). Two live
   placement candidates exist with no PRD text or precedent favoring
   either: a new top-level nav page (mirroring `REQ-SB-31-US-01`'s own
   resolved precedent), or an added section on the already-approved
   System Health page. `net-new-design-needed`, and the placement choice
   itself is a genuine multiple-equally-valid-options case (MUST-FLAG
   trigger 8).
2. **Today's `agent_communication_history.json` recording cannot satisfy
   REQ-SB-11's own literal acceptance text ("outcome — success, or error
   with detail") without a real fix, confirmed by direct reading of
   `app/business/email_classification.py`/`meeting_classification.py`:**
   meeting-capture's Autonomous branch writes no history entry at all on
   a successful run (only email-capture does, per that module's own
   comment); and neither pipeline's own top-level orchestration function
   is wrapped in a `try`/`except` — an exception escaping today's
   narrower per-item error handling (e.g. `outlook_com.OutlookUnavailable`,
   the same failure mode `BUG-007`/`BUG-008` already document as real and
   `Open`) propagates uncaught with zero recorded trace, the identical
   "crash gap" shape `REQ-SB-31-US-01`'s own Scenario 8 already found and
   fixed for the real-time chat path. This is not a guess-worthy scoping
   question (the fix is directly required by the acceptance text's own
   "error with detail" half) but is recorded here because it materially
   changes this story's size/shape beyond "a new UI over already-recorded
   data" — worth a human's awareness alongside the placement decision.

**Resolution:** Resolved 2026-08-13 — the operator delegated the
placement decision to the orchestrating agent directly ("make the call
yourself, using sane defaults") rather than answering it personally. The
orchestrating agent decided a **new top-level nav page**, not a section
grafted onto the existing System Health page. Reasoning: `REQ-SB-31-US-01`
(System Health) was deliberately built as a current-snapshot status board
with its own dedicated nav item specifically because a chronological log
has a different shape/interaction model than a snapshot board — this
project already treats "log/history over time" as a distinct UI pattern
from "status right now" (My Day's own day-navigator precedent draws this
same distinction elsewhere); crowding a chronological, potentially
long-scrolling activity log into System Health's own page would
contradict that page's own designed purpose; this also matches the
precedent that System Health itself just got its own new nav page rather
than being folded into Settings. `/design REQ-SB-11` still needs to run
(genuinely net-new UI, no prototype exists yet) before `/plan-tasks` — a
sequencing dependency, not a further gating decision. The
recording-completeness fix (finding 2) was never a decision-blocker and
remains scoped into `REQ-SB-11-US-01`'s own Constraints/Implementation
Tasks (`T01`) regardless of the placement outcome.

**Resolving artefact:** `REQ-SB-11-US-01` (`## Context`/`## Notes`,
updated 2026-08-13)

**Status:** Resolved

## ESC-026: `REQ-SB-04-US-01`'s own Scenarios 1/2 (scope-enforcement) compose entirely with `REQ-SB-29-US-01`'s own vault-scope-assignment mechanism — that story has not been decomposed into tasks at all, so no real task id exists anywhere to wire this AC's own verification onto — 2026-08-13

**Category:** other

**Trigger:** Decomposer pass (`/plan-tasks` step 2) on `REQ-SB-04-US-01`.
The parent story's own `## Dependencies`/`## Notes` already named this
plainly: "this story's own scope-enforcement (Scenarios 1/2) cannot be
built for real until `REQ-SB-29-US-01` actually ships with its own
assignment mechanism resolved." This decomposer pass confirmed, by direct
glob against `Implementation/Tasks/`, that **zero**
`REQ-SB-29-US-01-T*.md` files exist anywhere — that story is still
`status: Draft`, `gate: clear`, and has never been run through its own
decomposer step at all, the same materially-blocking state `ESC-018`
already found for `REQ-SB-36-US-02`'s own analogous composition with this
identical story. There is no real, `Ready` task id anywhere to wire `AC-01`
(Scenario 1, a within-scope confirmed write lands)/`AC-02` (Scenario 2, an
out-of-scope write is rejected) onto, and none can be fabricated per
Pipeline.md hard rule 2 / this decomposer's own contract.

**Resolution:** Not resolved in this pass. Mirroring `ESC-011`'s and
`ESC-018`'s own established precedent, and the operator's own 2026-08-12
confirmation (`REVIEW-QUEUE.md` → `ESC-018` entry) that per-task blocking
is the correct going-forward default (not `ESC-011`'s own older
full-story-`Draft` posture): `AC-01`/`AC-02` are locked regardless (per
Pipeline.md's "forward is autonomous by exception" rule — nothing about
this blocker prevents authoring/locking the ACs), and a dedicated task,
`REQ-SB-04-US-01-T03`, is created to hold their own eventual verification,
left `depends_on: []` with a prominent "⚠️ BLOCKED — do not start" section,
rather than a fabricated task id or a silently-omitted AC. The parent
story itself advances to `status: Ready` (its own literal Ready criteria
are genuinely satisfied — every AC locked, every locked AC tagged,
`depends_on` acyclic), while only `T03` is individually held at `status:
Draft`/`gate: flagged` — `T01` (the `/mcp` shared-secret auth mechanism,
no `REQ-SB-29-US-01` dependency at all) and `T02` (the propose→pending→
approve/decline plumbing, verified independently of the scope gate via a
direct `pending_approval_registry` seed) proceed to `Ready` since neither
is actually blocked.

**Resolving artefact:** _pending_ — needs `REQ-SB-29-US-01` run through its
own decomposer pass (producing at least one real, `Ready` task id for its
vault-scope-assignment mechanism), after which a follow-up decomposer pass
on `REQ-SB-04-US-01-T03` replaces its own `depends_on: []` with the real
id and resets its `status`/`gate` to ordinary lockstep with the rest of
the story. See `REVIEW-QUEUE.md`.

**Status:** Open

## ESC-027: Real, pre-existing filename-stem collision in the live vault — two distinct real notes silently collapse to one `vault_indexing` index entry, `_slugify`'s 80-char truncation eats the disambiguating hash suffix — 2026-08-13

**Category:** other

**Trigger:** `REQ-SB-01-US-01-T02`'s own mandated live `AC-01` verification
(`len(index) == len(vault_writer.list_all_note_paths())` against the real
vault). The two counts genuinely disagreed: 503 real note files under
`Work/`, but only 502 unique filename stems. Root-caused by direct
inspection: `Work/Emails/2026-07-30-RE- [ Core42 @UAE ] SimplAI Agentic AI
Operating System - Demo (deep .md` and `Work/Notifications/2026-07-30-RE-
[ Core42 @UAE ] SimplAI Agentic AI Operating System - Demo (deep .md` are
two genuinely distinct, correctly-captured real items (different
`outlook_entry_id`, different sender — one a real email from
`gurpreet.singh@simplai.ai`, the other a Google Calendar notification —
different `conversation_id`, received one second apart) that happen to
share an identical subject line. `email_classification.classify_recent_
emails` builds each one's `filename_stem` as `f"{date}-{subject}-
{entry_id[-8:]}"` — subject *before* the disambiguating id-suffix — then
`vault_writer.write_note` passes that whole string through `_slugify(text,
max_len=80)`, which truncates to the first 80 characters. This subject
alone is long enough to consume the full 80-character budget, silently
cutting off the trailing `-{entry_id[-8:]}` suffix entirely — so both
notes' *files* land in different kind-subfolders (no file was ever
overwritten on disk, both exist intact today), but their **filename
stems** (the identity `ADR-024` point 1 keys the new vault index by,
"the same identity this project's own capture pipelines already use
throughout") are byte-identical. `vault_indexing.rebuild_index()`
faithfully builds exactly what `ADR-024` specifies — a plain
`stem`-keyed dict — so this pre-existing real-data collision causes one
of the two entries to silently overwrite the other on every rebuild
(whichever `list_all_note_paths()`'s sorted order visits last), with the
other real note absent from the index and no error raised. This is a
genuine, real gap in `ADR-024`'s own founding assumption ("filename stem
is a unique identity across the whole vault") — the assumption holds for
every one of this project's *own* already-`Done` disambiguation schemes
individually (Email's own EntryID-suffix rule, Meeting's own SHA-256-hash
rule) but was never checked against `_slugify`'s **separate**,
independent 80-character truncation, which can silently discard whatever
disambiguating suffix a caller appended. `REQ-SB-01-US-01-T02`'s own
`Files to Modify` is exactly one new file, `app/business/vault_indexing.py`
— fixing this would mean changing `_slugify`/`email_classification.py`'s
stem-construction order (already-`Done`, out-of-scope files) or making an
unauthorized architecture-level collision-handling decision `ADR-024`
itself never specified (e.g. keying by full relative path instead of bare
stem) — neither is this task's call to make unilaterally.

**Resolution:** Open — not fixed at the primitive level (out of
`REQ-SB-01-US-01-T02`'s declared scope; `_slugify`/`email_classification.
py`'s stem-construction are both already-`Done`, unrelated files). `T02`
itself is built and verified exactly as `ADR-024` specifies, with this
one, real, disclosed exception recorded in its own Implementation Log
rather than silently accepted or hidden — `AC-01` is verified PASS for
every one of the vault's 502 unique-stem notes (exact match against an
independent direct read, for the sampled note and every other check this
task's own Tests block runs), with this single real collision (2 notes,
0.2% of 503) named honestly as a live, disclosed gap rather than blocking
the task, mirroring this project's own established `ESC-002`/`ESC-003`/
`ESC-012` precedent (a real, out-of-scope, root-caused defect discovered
via due-diligence live verification does not block the task that found
it). No vault file was touched, renamed, or repaired — this story's own
Non-Goals explicitly forbid any vault write, unlike `ESC-003`'s one-off
manual repair.

**Resolving artefact:** _pending_ — recommend `/bug` capture (Area: Logic)
so it can be batched into a `BUGFIX-NN-US-01` fix story; the underlying
fix most likely belongs in `email_classification.classify_recent_emails`'s
own stem-construction (e.g. compute the disambiguating suffix first, or
hash the whole candidate string before any truncation, mirroring
`meeting_note_filename_stem`'s own already-correct "hash before
truncate" precedent) or in `_slugify` itself (truncate before appending a
caller-supplied disambiguator, never after) — a genuine design choice for
that dedicated fix story to make, not decided here. `REQ-SB-02-US-01`
(Browse & Search, built directly on `vault_indexing.get_index()`) should
also be made aware this exists, since a real search/browse result could
silently omit one of these two colliding notes.

**Status:** Open

## ESC-028: `BUG-011`'s own `_slugify` 80-char-truncation defect is confirmed to also affect Task notes — and here causes a literal, real note *overwrite* (not just an index-invisible collision), since Task notes land in one flat `Work/Tasks/` subfolder — 2026-08-13

**Category:** other

**Trigger:** `REQ-SB-09-US-01-T03`'s own mandated live `AC-07` verification
(two real Outlook Task items sharing an identical subject must produce
two distinct notes). Running the real, unbounded scheduled capture
(`REQ-SB-09-US-01-T04`'s own `AC-04` live app-start trigger, 100 real
Outlook Tasks processed) surfaced three genuinely distinct real Outlook
Task items — `EntryID` suffixes `...89040000`, `...89070000`,
`...89090000` — all sharing the identical subject `"Re: Azerbaijan
Engagement – Data Lake Opportunity & Core42 Participation"` (72
characters). `vault_writer.task_note_filename_stem` correctly built
three DISTINCT stems (`<subject>-2026-08-13-<entry-id[-8:]>`, 92
characters each, confirmed via `task_note_index.json`, which correctly
recorded all three as separate `entry_id -> stem` mappings), but
`vault_writer._slugify(text, max_len=80)` — the same pre-existing,
already-tracked defect as `BUG-011`/`ESC-027`, unmodified by this
story's own `T02` (additive-only per its own Constraints) — truncates
each of the three 92-character stems down to an identical 80-character
filename, so `write_note()` wrote all three to the exact same physical
path, `Work/Tasks/Re- Azerbaijan Engagement – Data Lake Opportunity &
Core42 Participation-2026-08.md`, one overwriting the previous.
Confirmed directly: only the LAST of the three writes (`...89090000`,
customer `"Government of Azerbaijan"`) survives on disk; the earlier
two (`...89040000`, same customer, and `...89070000`, no customer
match) are gone — their content, not just their index visibility, is
lost. **This is a materially worse consequence than `BUG-011`'s own
documented case:** Email's/Notification's own collision (`ESC-027`)
landed in two DIFFERENT kind-subfolders (`Work/Emails/` vs.
`Work/Notifications/`), so both files survived intact on disk and only
the vault-wide index silently dropped one; Task notes all share one
flat `Work/Tasks/` subfolder (no Compass-classified `kind` split, per
`ADR-027` point 3), so the identical collision here causes a literal
same-path file overwrite — real content loss, not just index
invisibility. The disambiguation MECHANISM this story's own `T02`/`T03`
built is confirmed CORRECT in isolation — a controlled real short-subject
pair (`"AC07 Verify Dup Subject"`, well under the 80-char budget)
produced two genuinely distinct, correctly-disambiguated notes, neither
overwritten (see `REQ-SB-09-US-01-T03`'s own Implementation Log) — the
defect is entirely inside the pre-existing, out-of-scope `_slugify`
function, not this story's own new code. Real production data was also
found to name-collide harmlessly under the 80-char budget with no
truncation (three distinct real `"ADNOC Account Plan Review &
Discussion Session - H2 FY26"` tasks, 57-character subject, correctly
produced three distinct files) — confirming the mechanism only fails
once the combined stem exceeds 80 characters, exactly `BUG-011`'s own
already-diagnosed root cause.

**Resolution:** Open — not fixed at the primitive level, per this same
project precedent (`ESC-027`): fixing `_slugify`/`task_note_filename_stem`'s
own truncation order is out of `REQ-SB-09-US-01`'s declared task scope
(`_slugify` is a pre-existing, shared, already-`Done` function; `T02`'s
own Constraints forbid modifying any existing function's behavior).
Treated as a real, disclosed, non-blocking finding for `AC-07` — the
locked AC's own disambiguation MECHANISM is verified correct via a
controlled real short-subject pair; the real long-subject collision is
root-caused entirely to this same pre-existing, already-tracked defect,
mirroring `ESC-027`'s own "a real, out-of-scope, root-caused defect
discovered via due-diligence live verification does not block the task
that found it" precedent.

**Resolving artefact:** _pending_ — recommend `BUG-011`'s own `BUGS.md`
entry be extended (not a new bug — same root cause, same fix) to name
Task notes as a second, confirmed-affected note type, and to record the
worse "same-subfolder literal overwrite" severity finding explicitly
(Task notes have no `kind`-subfolder split at all, so EVERY Task-note
collision this defect causes is a same-path overwrite, unlike Email's
own cross-subfolder near-miss) — worth a `Severity` re-review at the
next `/triage` pass. The recommended fix (compute/truncate the
disambiguating suffix *before* the human-readable subject text, or hash
the whole candidate string before any truncation, mirroring
`meeting_note_filename_stem`'s/`vault_writer.meeting_note_filename_stem`'s
own already-correct "hash before truncate" precedent) applies identically
to both `email_classification.classify_recent_emails`'s and
`vault_writer.task_note_filename_stem`'s own stem-construction — one fix
story can plausibly close both. `REQ-SB-09-US-01`'s own real vault state
today still carries this exposure (confirmed: 100 real `task_note_index.json`
entries vs. 82 real files under `Work/Tasks/` at end of this story's own
live verification — an 18-entry gap, all attributable to this same
truncation collision across the real capture run).

**Status:** Open
