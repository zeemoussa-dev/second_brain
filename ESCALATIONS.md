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

**Follow-up, 2026-08-13 — PRD rewrite + re-spec + 3-way split.** The
operator rewrote `REQ-SB-37` the same day (title now "Agent Creation
Wizard," not "Agent Creation") with a per-Type wizard breadcrumb (Worker:
Skills + Vault Scope + Section; Expert: domain, starts empty/honest;
Producer: Purpose + output action). `/spec REQ-SB-37` was re-run against
this rewrite. The original custom-bespoke-actions fork named in this
entry's own **Trigger** is now **resolved**, not still open: the same
breadcrumb that prompted the rewrite directly answers it — "we have no
Custom Action, we need to Convert those Custom Actions to Skills" — which
forced `REQ-SB-39` (Unify Agent Capabilities Under Skills) into existence
as its own new requirement. No separate custom-action mechanism is needed
or built by any `REQ-SB-37` story.

The persisted-registry-mechanism half of this entry remains **open,
unchanged** — still an ADR-level call for the architect at `/plan-tasks`.

The existing `REQ-SB-37-US-01` story was updated in place (not replaced)
and split into three per-type stories, since the rewrite's three wizard
shapes have genuinely different build-readiness:
`REQ-SB-37-US-01` (entry point + Expert flow — NOT blocked by `REQ-SB-39`,
only carries the persisted-registry ADR question forward),
`REQ-SB-37-US-02` (Worker flow — hard-blocked on both halves of
`REQ-SB-39` and on `REQ-SB-29-US-01`), and `REQ-SB-37-US-03` (Producer flow
— hard-blocked on both halves of `REQ-SB-39`, plus its own new, genuinely
unresolved fork: the PRD's own text leaves the Producer "output action"
mechanism open, Skill vs. destination/write-mode, flagged rather than
guessed). This split is itself a new analyst judgment call, recorded here
rather than as a separate escalation entry since it is a direct
continuation of this same requirement's open architectural questions, not
new ground.

A further judgment call, also recorded here rather than guessed silently:
`REQ-SB-37-US-01`'s Expert flow does **not** hard-depend on `REQ-SB-40`
(Agent Knowledge-Gap Tracking & Expert Readiness, itself `Draft`/flagged,
unbuilt) — an Expert created by the wizard is fully functional the moment
`REQ-SB-33`'s already-`Done` honest-uncertainty guardrail applies to it;
`REQ-SB-40` adds gap-tracking observability on top, later, without
requiring anything from the Expert flow to change.

**Status:** Open (persisted-registry ADR question unresolved; Worker/
Producer stories additionally blocked on `REQ-SB-39`; Producer story
additionally carries its own new output-action fork).

**Follow-up, 2026-08-13 — architect pass (`/plan-tasks REQ-SB-37-US-01`
step 1).** The persisted-registry-mechanism half of this entry (the only
half `REQ-SB-37-US-01` itself still carried) is now **resolved for
`REQ-SB-37-US-01`**: `ADR-030` (`Implementation/Architecture/ADR.md`)
supersedes `ADR-011` point 2 only — `agent_registry.py`'s static `AGENTS`
dict becomes `_SEED_AGENTS` (byte-identical, unchanged, stays in code)
merged at read time with a new persisted `.second-brain/
agents_registry.json` overlay for runtime-created agents, per the
operator's own relayed mechanism decision (mirrors `skill_registry.py`'s
`_load_state`/`_save_state` JSON-file pattern). `architecture.md` was
updated to record the resulting file-level shape. This does not resolve
`REQ-SB-37-US-02`/`US-03`'s own separate blockers (`REQ-SB-39`,
`REQ-SB-29-US-01`, the Producer output-action fork) — those remain open.

**Resolving artefact (persisted-registry half, `REQ-SB-37-US-01` only):**
`ADR-030`. Still pending a human decision: approving/rejecting `ADR-030`
itself (`REVIEW-QUEUE.md`) before this story's tasks are built.

**Status:** Open (human review of `ADR-030` pending via `REVIEW-QUEUE.md`;
`REQ-SB-37-US-02`/`US-03`'s own separate blockers unresolved).

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

## ESC-029: REQ-SB-39 (Unify Agent Capabilities Under Skills) is a genuine, operator-confirmed full-scope architecture reversal of `ADR-011` point 2 and `ADR-020`'s entire two-axis working-mode gate — split into two sequential stories so a mutating capability is never observably ungated even transiently; the mutates-classification mechanism for Skills, the fate of the ADR-011 chat funnel, and Skills-UI coverage are all left open — 2026-08-13

**Category:** unclear-requirement

**Trigger:** `REQ-SB-39`'s own PRD breadcrumb (2026-08-13, operator-directed)
was raised in direct response to `REQ-SB-37`'s own "can a user-created agent
define custom actions?" open question: "We have no Custom Action, we need
to Convert those Custom Actions to Skills. Example, Read Mail is a Skill
under Outlook COM Tool we need to have that in our tool set." Asked how far
this should go, the operator confirmed: **"Everything, including existing
shipped agents"** — not just new wizard-created agents; every
already-shipped, already-verified Action this session built gets
refactored, for one consistent model going forward. The breadcrumb itself
names this "a genuine architecture reversal, not a wizard feature — flagged
explicitly to the operator as such before this requirement was written, and
confirmed as the intended scope." Direct, live inspection of the real code
(not PRD-text assumption) confirms the surface this touches is real and
large:
- `app/business/agent_registry.py`'s static `AGENTS` catalog — 7 agents,
  14 action entries, 7 distinct action ids; 4 classified `"mutates": True`
  (`run_capture_now`, `pause_schedule`, `rebuild_person_note`,
  `build_knowledge`), 3 classified `"mutates": False` (`view_last_run`,
  `ask_question`, `view_channel_status`).
- `app/api/agents_router.py::_invoke_action` (`ADR-020`) — the real,
  current two-axis working-mode gate: Manual refuses Hub-routed triggers
  outright; Supervised short-circuits into a pending-approval record only
  when the resolved action's own `mutates` flag is `True` (fail-safe
  default `True` for an unresolvable action); every other combination falls
  through to immediate execution.
- `app/business/skill_registry.py::invoke_skill` / `app/api/
  skills_router.py`'s `POST /agents/{agent_id}/skills/{skill_id}/invoke` —
  confirmed **completely ungated** by working mode today: only
  `has_skill_access` (the grant/revoke concern) is checked before
  dispatching to the registered handler; there is no `trigger` parameter
  anywhere on this path, no working-mode lookup, no pending-approval
  integration. Exactly right for `REQ-SB-27`'s own narrow, largely
  read-only skills (`web-research`, `diagram-understanding`) — this
  requirement is what changes that for mutating Skills.
- `app/business/agent_orchestration/mcp_client.py::load_agent_tools`
  (`ADR-022` point 6) — a separate, already-existing access-grant filter
  for the in-app chat's own tool-calling loop (`has_skill_access` decides
  which tools a conversation can even see), not a working-mode gate; this
  requirement's own gate extension is an additional layer on top, not a
  replacement.
- **A genuine gap found while resolving this, not silently carried
  forward:** `REQ-SB-27-US-01` (Skills Repository, `Done`) shipped **zero
  UI** — confirmed by direct inspection of `html-prototype/` (no
  Skills-related screen anywhere) and `src/frontend/src` (no match at all).
  Today's only agent-capability UI is `agents-map.html`'s "Available
  actions" panel — a static button list rendered directly from
  `agent_registry.py`'s hardcoded array, with no grant/revoke affordance and
  zero Skills awareness. The requirement's own Acceptance text implies
  reusing "the surfaces those requirements already built" (echoing
  `REQ-SB-37`'s own phrasing) — **not factually true for Skills today**:
  the API mechanism exists, but no screen anywhere calls it.

The PRD's own breadcrumb explicitly names four genuinely open questions,
none decided in the PRD, all "left to `/spec`/`/plan-tasks` — expect this to
need serious architectural design work and likely more than one superseding
ADR, not a quick extension": (1) whether `mutates` becomes a per-Skill
classification mirroring `agent_registry.py`'s action field exactly, or
Skills need a materially different approval model; (2) whether Skill
invocation for a mutating capability needs to gain the same
Manual/Supervised/Autonomous gating chat/direct Actions already have (the
requirement's own answer is yes, behaviourally — but not how); (3) migration
mechanics — auto-convert every existing agent's action set to equivalent
Skill grants at once, or roll out incrementally; (4) whether `ADR-011`'s
chat-triggered keyword-match funnel itself needs to change to dispatch to
Skills instead of Actions, or stays Action-shaped and calls into Skills
internally.

**Resolution:** Not resolved in this pass — no operator was available to
decide the mechanism-level questions live, and per `Implementation/
Pipeline.md`'s own role boundary, these are architect-level calls (MUST-FLAG
trigger 3 is explicitly not the analyst's to make) — guessing at them here
would risk locking `/plan-tasks` against a shape the architect would
otherwise have rejected. The analyst split `REQ-SB-39` into two sequential
stories rather than one oversized story or two independently-orderable
ones, specifically so the requirement's own safety invariant ("a mutating
Skill's invocation still honors working mode") is never violated even for a
transient build window:
- **`REQ-SB-39-US-01`** — the capability model itself, plus migrating every
  currently *read-only* Action (`view_last_run`, `ask_question`,
  `view_channel_status`) to a Skill. Needs no gate-mechanism change at all,
  since a read-only capability is never gated under any working mode today.
- **`REQ-SB-39-US-02`** — extending the working-mode gate to cover Skills,
  and migrating every currently *mutating* Action (`run_capture_now`,
  `pause_schedule`, `rebuild_person_note`, `build_knowledge`) to a Skill,
  landed together in the same release so a mutating capability is never
  observably ungated even transiently. Hard-depends on `REQ-SB-39-US-01`
  landing first (its own affected-screens question cannot even be answered
  until that story's unified capability-list UI exists to invoke a Skill
  from in the first place).
Both stories describe only OBSERVABLE BEHAVIOR in untagged Gherkin, not the
mechanism; both are `gate: flagged`. Neither attempts to resolve the
mutates-classification mechanism, the chat-funnel restructuring question, or
migration ordering beyond the two-story split itself — all left named, not
guessed, in each story's own `## Notes`.

**Resolving artefact:** _pending_ — needs a human/architect decision at
`/plan-tasks` on (a) the mutates-classification shape for Skills (`ADR-020`'s
own most direct extension point vs. a materially different model), (b)
whether `invoke_skill`/its endpoint gains a `trigger` concept and how it
threads through every real call site, (c) the fate of `ADR-011`'s chat
keyword-match funnel, and (d) confirmation that this two-story build order
is acceptable. Also needs a `/design` pass — no Skills grant/revoke UI
exists anywhere yet, and `REQ-SB-39-US-01`'s own unified capability-list
surface is a hard prerequisite for `REQ-SB-39-US-02`'s own screen questions.

**Status:** Open

## ESC-030: REQ-SB-40 (Agent Knowledge-Gap Tracking & Expert Readiness) — the PRD breadcrumb itself names two genuinely open mechanism questions and one open placement question, and no `html-prototype/` screen (nor its own named likely display surface, REQ-SB-41) covers a knowledge-gaps view anywhere — 2026-08-13

**Category:** unclear-requirement

**Trigger:** `REQ-SB-40`'s own PRD breadcrumb (2026-08-13, operator-directed),
answering "what makes an Expert agent actually ready/complete": "I guess we
need both the wizard, and the Agent can say I don't know as a start, and a
human input is needed to fill the gap — by time it will be Expert (the
number of I don't know is how we close this Expert gap in future)." This
builds directly on `REQ-SB-33` (Agent Grounding & Honest-Uncertainty
Guardrail, `Done`) — that requirement made an agent say "I don't know"
honestly instead of fabricating, but the reply itself is never captured
anywhere beyond the chat transcript. Direct, live inspection of the real
code (not PRD-text assumption) confirms the surface this touches:
- `app/business/agent_orchestration/state.py::history_entries_to_messages`
  (`REQ-SB-33-US-01`) confirms the honest-uncertainty behavior is
  prompt-level only — no structured signal anywhere distinguishes an honest
  "I don't know" reply from an ordinary answered reply today; the model's
  raw `response.content` is returned as `reply` either way.
- `app/business/agent_registry.py`'s static `AGENTS` catalog confirms
  "Expert" is already a real, structural `"type": "expert"` marker
  (`vault-qa`, `vault-filing-expert`, `compass-expert`) — not merely a role
  description with nothing to key off.
- `app/business/agent_activity.py` (`REQ-SB-11-US-01`) confirms its own
  `_ACTIVITY_KINDS = {"run_event", "run_error"}` scope deliberately
  excludes conversational entries — a knowledge gap does not fit that
  existing log mechanism as-is.
- No `html-prototype/` screen anywhere shows a knowledge-gaps view, a gap
  count, or a gap-closing affordance — confirmed by direct inspection. The
  PRD breadcrumb's own named "obvious fit, but not confirmed" display
  surface, `REQ-SB-41` (Agent Overview), is itself unspecced (PRD-only, no
  story) with its own breadcrumb stating plainly "a `/design` pass is also
  needed (no prototype shows this)."

The PRD's own breadcrumb explicitly names four genuinely open questions:
(1) the exact mechanism for detecting/recording an "I don't know" — a
structured signal the model itself emits, vs. a pattern-match over the
reply text; (2) what "human input fills the gap" looks like concretely — a
chat reply filed via the Vault Filing Expert (`REQ-SB-35-US-01`), the same
way `REQ-SB-23`'s My Day Intake Agent already files conversational input,
or a dedicated gap-resolution UI; (3) where the gap count/readiness signal
is surfaced — `REQ-SB-41` named as the likely fit but itself unspecced and
with no prototype coverage; (4) whether a closed gap needs any verification
that it was actually answered correctly.

**Resolution:** Questions (1)-(3) are genuinely open mechanism/placement
decisions correctly left to `/plan-tasks`/a future `/design` pass, per
`Implementation/Pipeline.md`'s own role boundary (MUST-FLAG trigger 3 is not
the analyst's to make) — guessing at them here would risk locking
`/plan-tasks` against a shape the architect or a `/design` pass would
otherwise have rejected. `REQ-SB-40-US-01`'s Acceptance Criteria are written
at the observable-behavior level only (an honest "I don't know" results in a
recorded, viewable, closeable open gap whose count declines as gaps close),
not presuming any of the three open mechanisms. Question (4) **was**
resolved directly, not guessed: this project's own standing `MEMORY.md`
constraint (2026-08-10, "No staging/promotion gate on ingested vault data")
applies directly — content filed through the already-`Done`, already-trusted
`REQ-SB-35-US-01` Vault Filing Expert mechanism unconditionally counts as
closing the gap it addresses, with no additional correctness-verification
step layered on top. Separately, whether "declining rate" needs a
threshold/time-window was also resolved directly from the requirement's own
Acceptance text (a simple, always-current open-gap count, not a computed
rate) — not a genuinely open question requiring a flag.

**Resolving artefact:** `ADR-032` (`/plan-tasks` step 1, architect pass,
2026-08-13) — resolves all three previously-open questions. (a) Detection:
a new bound tool, `record_knowledge_gap(topic)`, intercepted before generic
tool execution exactly like `ADR-017`'s already-real
`request_cross_section_help` — a structured, model-emitted signal, not a
text pattern-match, reusing this graph's only existing structured-signal
channel (confirmed by direct read of `graph.py::_call_model`: no
`with_structured_output`/response-format mechanism exists anywhere in it).
(b) "Human input fills the gap": routed through the already-`Done` Vault
Filing Expert (`REQ-SB-35-US-01`), per the operator's own relayed
direction, composing that mechanism unchanged rather than a dedicated new
UI. (c) Display placement: the operator directed skipping `/design` for
this batch and building directly, which cleared the display-surface
prototype blocker; the architect's own placement call is a new,
conditionally-rendered "Knowledge gaps" tab on the existing
`AgentDetailPanel.tsx`, gated to Expert-type agents — not `REQ-SB-41`
(Agent Overview), which remains unspecced and is not depended on. Full
mechanism, every alternative considered: `Implementation/Architecture/
ADR.md` → `ADR-032`. The story (`REQ-SB-40-US-01`) is `gate: flagged`
again, but now for the standard ADR-creation review (trigger 3), not for
an unresolved mechanism question — see `REVIEW-QUEUE.md`.

**Status:** Resolved

## ESC-031: REQ-SB-41 (Agent Overview Surface) — the PRD's own "before or instead of" phrasing leaves the Overview's navigation shape genuinely open, and no dedicated purpose/description data field exists anywhere in the real code despite the PRD breadcrumb's own implication that one already does — 2026-08-13

**Category:** unclear-requirement

**Trigger:** `REQ-SB-41`'s own PRD breadcrumb (2026-08-13, operator-directed),
verbatim: "The Agents Tab now Opens Straight to Chat I need to have an
Overview Of what the Agent do, Scope, Guardrails and Is It Autonomous Etc
before [I] Can Chat with it." Direct, live inspection of the real code (not
PRD-text assumption) confirms two genuinely open points, one of them a real
discrepancy against the breadcrumb's own claim:

1. **Navigation shape.** The requirement's own Acceptance text says the
   overview must be shown "before or instead of landing directly on the
   Chat tab" — this does not commit to one shape. `AgentDetailPanel.tsx`
   (`REQ-SB-13`/`REQ-SB-21`, both `Done`) confirms `TABS =
   ['chat', 'history', 'settings']` with `activeTab` defaulting (and
   resetting on every agent switch) to `'chat'` — exactly the behavior the
   operator is complaining about. At least three equally-valid shapes exist
   to fix it: a new 4th "Overview" tab, a new default landing tab
   (replacing Chat's current default position), or a one-time interstitial
   shown before Chat. None is named or implied more strongly than another
   by the PRD's own text.
2. **No dedicated Purpose/description field exists anywhere.** The PRD
   breadcrumb's own framing implies "purpose/description (already on every
   agent's existing Settings tab)" is real, existing data this requirement
   just needs to surface earlier. Direct inspection of
   `app/business/agent_registry.py`'s static `AGENTS` catalog,
   `src/frontend/src/features/agents-map/agentsApiClient.ts`, and
   `html-prototype/agents-map.html` confirms this is **not literally true**
   — no `description`/`purpose` field exists anywhere; an agent's "what it
   does" today is only ever implicitly conveyed via its `name`, its `type`
   badge (`worker`/`producer`/`expert`), and its `settings`/`actions`
   kv-list rows (operational configuration, not a purpose narrative). This
   is a real gap between the breadcrumb's own claim and the real code, not
   a guess.

Separately, confirmed by direct inspection: no `html-prototype/` screen
shows any Overview region, Guardrails statement, or Vault Scope display
anywhere, for any agent — net-new-design-needed in addition to these two
open questions.

**Resolution:** Neither open question is guessed here. `REQ-SB-41-US-01`'s
Acceptance Criteria are written at the observable-behavior level (an
overview exists and is reachable "before or instead of" Chat; it states
purpose, working mode, and guardrail behavior; it shows Vault Scope
honestly whether assigned or not) without presuming the navigation shape or
the Purpose region's exact data source — both left to `/plan-tasks`/a
`/design` pass. The story is NOT wholly blocked on `REQ-SB-29-US-01`
(Vault Scope, `Draft`, unbuilt) — only the real-assigned-scope-value
scenario needs it; the honest "no scope assigned yet" state is buildable
today and specced directly. The `REQ-SB-40-US-01` (`ESC-030`) knowledge-gaps
cross-reference is explicitly punted, not silently dropped: `REQ-SB-40`'s
own detection mechanism and data model are still undecided, so no
placeholder region is built here for data that does not exist yet; a future
`REQ-SB-40` pass is expected to extend this Overview once resolved.

**Resolving artefact:** `ADR-033` (`/plan-tasks` step 1, architect pass,
2026-08-13) — resolves both previously-open questions. (a) Navigation
shape: Overview becomes `AgentDetailPanel.tsx`'s new default-landing tab
(`TABS` gains `'overview'`, first in the array; `activeTab` no longer
defaults to `'chat'`), directly answering the operator's own "before...
Can Chat with it" framing — not a new 4th tab reached only after Chat, and
not a one-time interstitial. (b) Purpose data source: reads the existing
`settings` kv-list (`"Purpose"`, falling back to `"Domain"`), composing
`ADR-030`/`ADR-031`'s already-established Expert-Domain/Producer-Purpose
mechanism directly, not a new dedicated field. Two further real judgment
calls, resolved not guessed: all 7 shipped agents are backfilled with a
real, authored one-line Purpose settings entry (rather than shown an
honest-empty state), since they are real, already-understood, already-
`Done` agents; and the Overview now composes `ADR-032`'s already-built
`GET /agents/{agent_id}/knowledge-gaps` `open_count` field for Expert-type
agents, since the objection that motivated `REQ-SB-40-US-01`'s original
punt no longer applies now that story is `Ready` with a real endpoint.
`/design` stays skipped for this batch, operator-directed, unchanged — no
`/design REQ-SB-41` pass follows. Full mechanism, every alternative
considered: `Implementation/Architecture/ADR.md` → `ADR-033`. The story
(`REQ-SB-41-US-01`) is `gate: flagged` again, but now for the standard
ADR-creation review (trigger 3), not for an unresolved navigation/data-
source question — see `REVIEW-QUEUE.md`.

**Status:** Resolved

## ESC-032: REQ-SB-46 (Agent Creation Wizard Redesign) — no popup-modal/step-bar/FAB pattern exists anywhere in `html-prototype/`, and the PRD's own generic 4-step field-bucket wording does not say which of REQ-SB-37's already-shipped per-type fields (Domain/Purpose/Skills/Scope) lands in which step — 2026-08-14

**Category:** unclear-requirement

**Trigger:** `REQ-SB-46`'s own PRD breadcrumb (2026-08-14, operator-directed)
names two genuinely open questions explicitly: (1) the exact Step 1
Type/Scope conditional-visibility interaction (delegated to `/spec`'s own
judgment as an ordinary wizard pattern, not flagged further here — resolved
directly in `REQ-SB-46-US-01`'s own `## Context`); (2) the Step 4 Trigger
concept's own scope and whether "Schedule" composes with `REQ-SB-47`
(likewise delegated and resolved conservatively — recorded intent only, no
inline schedule-configuration UI built). Beyond those two named questions,
direct inspection of the real, already-shipped code
(`CreateAgentWizard.tsx`, `agents_router.py`'s `POST /agents`) found the
PRD's own Step 1-4 Acceptance wording ("Description," "Instructions/
Guardrails," "output plus what it does with that output," "Tools/Skills")
is generic across all three agent types, while the real, already-shipped
per-type field set is not (Expert: Domain only; Worker: Skills grant +
Vault Scope; Producer: Purpose + a single output Skill) — the PRD text does
not say which existing field lands in which of the four new generic step
buckets for which type, and more than one internally-consistent mapping is
plausible. Separately, direct grep of `html-prototype/agents-map.html`,
`styles.css`, `app.js`, and `settings.html` for
`modal|dialog|overlay|backdrop|fab|floating|bottom-right` and any Create
Agent affordance confirmed the PRD breadcrumb's own assertion that no
popup-modal-with-step-bar pattern or Map-mounted FAB exists anywhere — the
only existing overlay pattern in the whole prototype is the agent-detail
side panel's slide-in `.side-panel-overlay`, a structurally different shape
with no step-bar concept, and `settings.html` never had a Create Agent
affordance designed at all (matching `REQ-SB-37-US-01`'s own prior,
independent finding).

**Resolution:** Not resolved live in this pass — no operator was available
to decide. The analyst (`REQ-SB-46-US-01`) resolved the field-to-step
mapping with a single, disclosed, reasoned judgment call (Description →
Expert's Domain only; Instructions/Guardrails → the agent's existing
Working-mode selector, all types; "output plus what it does with it" →
Producer's existing Purpose + single output Skill only; Tools/Skills →
today's flat Skills multi-select, required for Worker exactly as today,
newly optional for Expert/Producer since `grantAgentSkill` was never
type-restricted at the backend) — chosen because it is the only mapping
under which every one of `REQ-SB-37`'s already-shipped fields appears in
exactly one step and no step bucket is structurally empty for every type.
This mapping does not change any backend mechanism, required-field
validation, or call sequence — it is presentation-and-sequencing only, per
the PRD's own explicit "entry point, container, step-progress treatment,
and step-to-field grouping only" framing. The missing prototype coverage is
separately flagged `net-new-design-needed`, with `/design REQ-SB-46`
recommended before `/plan-tasks` commits to a concrete layout. Both are
named in full in `REQ-SB-46-US-01`'s own `## Context`/`## Notes`, not
silently guessed, and the story's `gate:` is set `flagged` accordingly.

**Resolving artefact:** _pending_ — needs a human decision confirming (or
redirecting) the field-to-step mapping, and ideally a `/design` pass
producing an approved popup-modal/step-bar/FAB prototype screen, before
`/plan-tasks` proceeds with confidence.

**Status:** Open

## ESC-033: REQ-SB-47 (Per-Agent Scheduler) merged with REQ-SB-45 (Shared Serialization) per operator-confirmed direction — the shared lock's real mechanism/scope, one genuine capability-scope fork, and Schedule-tab UI all left open by direct code inspection — 2026-08-14

**Category:** unclear-requirement

**Trigger:** Per REQ-SB-45's own "Update, 2026-08-14 — Activated" breadcrumb
and REQ-SB-47's own mirrored breadcrumb, the operator confirmed building
REQ-SB-45's shared-lock generalization as part of REQ-SB-47's own work
rather than as a separate later pass — both were specced together as one
story (`REQ-SB-47-US-01`, anchored on REQ-SB-47 per the analyst's own
task-level instruction). Direct reading of the real code (not the PRD's own
abstraction) surfaced three genuine open points beyond the requirements'
own text:

1. `app/scheduling/capture_scheduler.py`'s existing `_capture_run_lock` is a
   plain in-process `asyncio.Lock`. REQ-SB-45's own breadcrumb cites, as its
   motivating real evidence, `SPRINT-030`'s own live verification session
   accidentally running two full capture passes concurrently because a
   coder mistakenly started **two separate backend processes**. An
   in-process lock — however correctly generalized across job types within
   one process — cannot physically prevent that exact cross-process
   collision; only a cross-process-safe mechanism (e.g. an on-disk lock
   file) would. The PRD text does not say whether REQ-SB-45's own
   Acceptance ("only one actually runs... across all of them") is meant to
   reach the cross-process case or is understood more narrowly as
   "across job types within one process."
2. `skill_tools.py`'s `run_capture_now` is real only for `email-capture`
   today; `meeting-capture`/`todo-capture` have real capture logic
   (confirmed live, already running correctly every hour via the existing
   background blob tick, `email_classification.
   run_capture_and_record_completion`) that is not wired to this on-demand
   Skill path at all. Whether REQ-SB-47-US-01 should also wire real
   on-demand handlers for these two agents, or ship with this gap honestly
   disclosed, is a genuine scope fork with two defensible answers.
3. No Schedule tab, or any tab-bar interaction pattern at all, exists
   anywhere in `html-prototype/agents-map.html`'s agent detail
   `.side-panel-agent` block today — confirmed by direct inspection
   (Settings/Chat/History-equivalent sections only).

**Resolution:** Not resolved live in this pass — no operator was available
to decide. The analyst (`REQ-SB-47-US-01`) resolved what it reasonably could
with sane, disclosed defaults (interval-only schedule shape; reusing
REQ-SB-11's existing Agent Activity log for run history unchanged; a
capability picker restricted to the agent's own granted `"mutates": True`
Skills, with stub capabilities honestly reported exactly as they already are
today) and wrote its Acceptance Criteria's shared-lock scenario (Scenario 7)
at the OBSERVABLE-property level — no two Outlook-COM-touching runs ever
overlap, regardless of trigger source or originating process — rather than
committing to one specific lock mechanism, so the property holds regardless
of which of the two lock-mechanism readings above the architect ultimately
picks. The three points above are left genuinely open, named in full in the
story's own `## Context`/`## Notes`, and the story's `gate:` is set
`flagged` accordingly — not silently guessed.

**Resolving artefact:** _pending_ — needs a human/architect decision on the
shared lock's real cross-process scope and mechanism (likely a
superseding/extending ADR on `ADR-005`/`ADR-029`), a scope decision on the
meeting-capture/todo-capture on-demand gap, and ideally a `/design` pass
producing an approved Schedule-tab prototype screen, before `/plan-tasks`
proceeds with confidence.

**Status:** Open

## ESC-034: REQ-SB-48 (Skills Grouped by Tool) — no `html-prototype/` screen anywhere covers the Capabilities/Skills grant-revoke region at all, and the PRD breadcrumb left the Tool taxonomy and icon-sourcing approach genuinely open — 2026-08-14

**Category:** unclear-requirement

**Trigger:** REQ-SB-48's own PRD breadcrumb (2026-08-14, operator-directed,
verbatim: "Skills should be Grouped by Tools Outlook as a Tool with the
Skills in it. Icons should be Added and we need to be able to Multiselect
those tools in the Agent in a Collapse tree like Approach.") explicitly
names the Tool taxonomy and icon-sourcing decision as open, left to
`/spec`, and proposes only a starting, unconfirmed default taxonomy.
Direct read of the real, current `skill_tools.SKILLS` catalog (11 entries)
and `AgentDetailPanel.tsx`'s real flat-list Capabilities mechanism confirmed
the ground truth the taxonomy had to be resolved against. Separately, direct
search of every file in `html-prototype/` for the Capabilities/Skills
grant-revoke region found it does not exist anywhere — the only prototype
side-panel content is `REQ-SB-20`/`21`'s Chat/Working-mode/Keywords
(`agents-map.html`'s own inline comment confirms this); the real
Capabilities section was added later, directly in code (`SPRINT-030-T09`),
and was never ported back into the prototype.

**Resolution:** The analyst (`REQ-SB-48-US-01`) resolved both open product
decisions the PRD breadcrumb named, rather than leaving them unresolved: (1)
a final Tool taxonomy placing all 11 real Skills — confirming 3 of the PRD
breadcrumb's 4 proposed groups verbatim (Outlook, Web, and Vault's other
three members), with one direct-evidence adjustment (`summarize-file` moves
from the breadcrumb's proposed "Vault" to "Compass" — its real handler
literally calls `compass_client.summarize_content`, Compass-generated
synthesis, not a vault read/write); (2) icon sourcing — one fixed icon per
Tool group (4 total), inherited by every Skill row under it, matching this
codebase's own existing Unicode-glyph `.nav-icon` convention rather than
sourcing 11+ distinct per-Skill icons. Both are named and reasoned in full
in the story's own `## Context`. The missing prototype coverage is
separately flagged `net-new-design-needed`, with `/design REQ-SB-48`
recommended before `/plan-tasks` commits to a concrete layout — along with
three further disclosed interaction defaults (Tool groups expand by
default; a same-grant-state-only multi-select model; Built-in Action rows
stay outside the tree) that a human should confirm. All of this is named in
full in `REQ-SB-48-US-01`'s own `## Context`/`## Notes`, not silently
guessed, and the story's `gate:` is set `flagged` accordingly.

**Resolving artefact:** `REQ-SB-48-US-01`'s architect pass (2026-08-14,
`/plan-tasks` step 1) — the operator explicitly confirmed the analyst's
resolved Tool taxonomy and fixed-icon-per-Tool decision as final, and
decided to skip a formal `/design` pass for this story (matching this
session's established precedent for well-understood, coder-improvisable UI
patterns), superseding the `net-new-design-needed` recommendation above.
The three further disclosed interaction defaults (Tool groups expand by
default; a same-grant-state-only multi-select model; Built-in Action rows
stay outside the tree) are likewise adopted as final. See
`REQ-SB-48-US-01`'s own `## Notes` → "Architect pass (2026-08-14)."

**Status:** Resolved

## ESC-035: `REQ-SB-48-US-01-T02`'s own AC-06 live-verification found a genuine, pre-existing bug in `skill_registry._load_state` unrelated to this task's own scope — 2026-08-14

**Category:** other

**Trigger:** Live multi-select-revoke verification (Scenario 6 /
`REQ-SB-48-US-01-AC-06`) against `email-capture`'s Outlook Tool group.
DELETE calls fired correctly (confirmed exact-count, exact-URL via a
`window.fetch` spy) and each returned `{"revoked": true}`, but the
revoked Skills (`view_last_run`, `run_capture_now`) reappeared as granted
on the very next state read — reproduced twice independently: once via a
real CDP-driven browser round trip against the actual running app, and
once via a direct, UI-free `skill_registry.revoke_skill_access(...)`
Python-shell call, ruling out any bug in this task's own new Tool-tree/
multi-select frontend code. Root cause, confirmed by direct code read:
`skill_registry._load_state()` unconditionally re-applies EVERY entry in
`_MIGRATION_GRANT_SEED` (`REQ-SB-39-US-02`/`ADR-029` point 7,
`SPRINT-031`) on every single call, not just once — so an explicit revoke
of any of the 7 migration-seeded ids against one of its own named seed
agents self-heals back to granted the instant any other code path (e.g.
the bulk action's own trailing `fetchAgent` refetch) triggers another
state read. This is a genuine defect in a shared primitive
(`skill_registry.py`'s `_load_state`/`_MIGRATION_GRANT_SEED`) neither
`REQ-SB-48-US-01-T01` nor `-T02` is allowed to touch per their own
`## Files to Modify` — out of scope for both, and unrelated to the
Tool-tree grouping/multi-select mechanism itself.

**Resolution:** Not fixed at the primitive level (out of this task's
declared scope). `AC-06` was instead verified live using a genuine,
durable revoke against a Skill/agent pair NOT in
`_MIGRATION_GRANT_SEED` (Vault-group Skills granted to `email-capture`,
which has no Vault-group migration seed at all) — confirmed both the
exact multi-select DELETE call count/URLs AND that the revoked Skills
stayed durably un-granted across a follow-up state read. Captured as
`BUGS.md` → `BUG-013` (`Open`) for future formal triage; not fixed here.

**Resolving artefact:** `BUGS.md` → `BUG-013` (captured 2026-08-14). Still
needs `/triage` to batch it into a `BUGFIX-NN-US-01` fix story before the
underlying primitive itself is hardened.

**Status:** Resolved (formally tracked as `BUG-013`; the underlying fix
itself is separate forward work, tracked there — not blocked here)

## ESC-036: Operator raised, mid-`/plan-tasks` (before the decomposer ran), whether `ADR-040`'s hand-rolled capture-pipeline suspension/rollback mechanism should instead adopt LangGraph's checkpointer + `interrupt()` primitive — reconsidered directly, `ADR-040` confirmed unchanged — 2026-08-15

**Category:** other

**Trigger:** The coordinator relayed a direct operator question after
`ADR-040` was written but before the decomposer's own pass ran: "shouldn't
LangGraph handle this agent-to-agent retry and stuff?" — specifically
asking whether `ADR-040`'s buffered/deferred per-item history-commit-plus-
rollback mechanism, and its mid-pipeline Supervised-stage-suspend-then-
resume mechanism, should be built on LangGraph's own checkpointer +
`interrupt()`/human-in-the-loop primitives instead of hand-rolled, given
`langgraph` is already a real, installed dependency (`ADR-015`), not a
hypothetical new one — a genuinely different and more specific question
than the general "no orchestration framework" MEMORY.md entry (2026-08-11)
the coordinator's own framing initially cited, since that entry is already
narrowed/superseded by `ADR-015`'s later adoption of LangGraph for this
project's own in-app conversational orchestration. This is a backward
pipeline step per `Pipeline.md` hard rule 6 (any reconsideration of
already-Accepted architectural work escalates), triggered by direct
operator question, not a self-discovered contradiction.

**Resolution:** Reconsidered directly against the real, concrete
comparison (verified, not assumed): `src/backend/requirements.txt`
confirms `langgraph>=1,<2` is already present — this was never a
new-dependency decision. `ADR-015` point 6's own Alternatives Considered
already rejected LangGraph's persistent checkpointer for conversation
state, citing this project's repeated, explicit rejection of SQLite/any
database for local state (`ADR-005`, `ADR-011`, `ADR-014`) in favour of
the flat-JSON `.second-brain/` convention; `ADR-015`'s own Consequences
went further and explicitly named this exact future scenario (a
Supervised-agent approval flow wanting `interrupt()`), leaving it open for
`REQ-SB-21`'s own later architecture pass — which became `ADR-018`, and
did **not** adopt `interrupt()`, building the hand-rolled
`pending_approval_registry.py` mechanism instead, now on its THIRD reuse
(`ADR-029`, `ADR-037`, and this ADR). Four concrete, code-grounded reasons
kept `ADR-040` hand-rolled rather than reversing that lived-with
precedent: (1) this project already directly confronted and declined this
exact idea twice, on the record (`ADR-015` point 6 + Consequences); (2)
this ADR's own Pending Approvals are routinely unresolved for hours/days
across real, already-documented `uvicorn --reload` restarts
(`Learnings.md`, `SPRINT-021`/`022`/`027`/`028`) — genuine cross-restart
durability would need `SqliteSaver` (`langgraph-checkpoint-sqlite`, not
installed), a real new persistence technology, not the in-memory
`MemorySaver` `ADR-015` judged sufficient for a single synchronous request;
(3) this pipeline has zero dynamic, LLM-driven branching for a graph
engine to manage — Pull/Link/Store make no LLM call at all, Tag makes one
deterministic classification call per item, and the only real conditional
logic is the working-mode gate, already solved with a few lines of direct
registry calls, reused unchanged 3 times over; (4) bridging LangGraph's
own thread/checkpoint model into this app's real Pending-Approvals surface
(a flat list, `GET`/`POST .../approve|decline`, an idempotent-per-tick
dedup guard, existing UI cards) would still require essentially all of
`ADR-040`'s own hand-rolled bridging code, now duplicated by a second,
divergence-risking state representation alongside it — more code and a
new dependency surface, not less, the literal "worst of both worlds" the
operator's own question anticipated. `ADR-040` is kept exactly as
originally written; its own Alternatives Considered section now carries
this full reasoning directly (not merely a MEMORY.md citation), plus a
dated "Reconsidered note" under its Status/Date header pointing here.

**Resolving artefact:** `ADR-040` (`Implementation/Architecture/ADR.md`) —
"Reconsidered note" + new Alternatives Considered entry, both appended
2026-08-15; Decision/Consequences unchanged. All 3 `REQ-SB-53` stories'
own `## Notes` cross-reference this entry.

**Status:** Resolved

## ESC-037: REQ-SB-54 point 6 — whether a Project note gets the same Background/History/Glimpse three-way split as Customer is genuinely unresolved by the operator — 2026-08-16

**Category:** unclear-requirement

**Trigger:** `/spec REQ-SB-54` (analyst pass over the freshly-drafted
`REQ-SB-54` through `REQ-SB-59` batch). `REQ-SB-54`'s own PRD comment block
(point 6) states directly: "Open, explicitly NOT resolved by the operator —
flag for architect/decomposer: does a Project note get the SAME
Background/History/Glimpse three-way split as Customer, or a simpler shape
(just a live Glimpse, no Background/History)? The operator was asked
directly and the conversation moved on before it was answered; treat the
three-way split as the default (for structural consistency with Customer)
but this is a MATERIAL ASSUMPTION per the MUST-FLAG list, not an
operator-confirmed decision — flag it." This is a genuine, PRD-acknowledged
product-design ambiguity, not a technical-verification gap (contrast
`REQ-SB-54` point 9's `ConversationID`-stability question, handled as a
Constraints/Definition-of-Done precondition in the same story rather than
an `ESCALATIONS.md` entry, since it's an empirical check, not an unresolved
product decision).

**Resolution:** Not resolved by this analyst pass — per this project's own
Forbidden-section rule ("Inventing requirements. If the PRD is unclear,
append an `ESCALATIONS.md` entry... flag the story, and move on"), the
three-way split is adopted as `REQ-SB-54-US-01`'s own explicit **working
default** (Scenario 5), matching the PRD's own instruction to treat it as
the default pending confirmation, but the story is `gate: flagged`
(trigger 1, material assumption) and a `REVIEW-QUEUE.md` entry asks the
human to confirm or correct this default before `/plan-tasks` builds
against it.

**Resolving artefact:** Operator, direct confirmation, 2026-08-16: "Yes,
Project gets the same directory shape as Customer." The working default
adopted in `REQ-SB-54-US-01`'s own Scenario 5 (and mirrored into PRD
`REQ-SB-54` point 6) is now a confirmed decision, not an assumption —
Project gets the full OKF-conformant directory shape (`index.md`/
`<slug>.md`/`log.md`/`captures.md`), identical to Customer.
`REQ-SB-54-US-01`'s `gate:` reset to `clear`; its `REVIEW-QUEUE.md` entry
removed.

**Status:** Resolved

## ESC-038: `REQ-SB-65-US-01-T02` — the real `email-capture-pipeline` agent is `is_background_agent: true`, so it is already invisible on the Agents Map ring today (moved to `CrawlersPage.tsx` by `REQ-SB-51-US-01`); inheriting that field verbatim onto the spliced Job entries, exactly as the architect/decomposer's own design requires, makes every Job invisible too — directly contradicting locked `AC-01`/`AC-02` — 2026-08-16

**Category:** unclear-requirement

**Trigger:** `REQ-SB-65-US-01-T02` build + live verification against the real
backend (`GET /agents`, `GET /agents/email-capture-pipeline/jobs`, `GET
/sections`, `T01`'s already-`Done` real data — not fixture/sample data).
The parent story's own Scenario 1 premise ("the single opaque
`email-capture-pipeline` node it renders today") and the architect's
confirmed design (recorded in `architecture.md` → "Pipeline Job Tree
Visualization" and restated in this task's own `## Constraints`: "`type`/
`working_mode`/`icon`/`color`/`is_background_agent`/`description` are all
INHERITED from the original `email-capture-pipeline` `AgentSummary`, never
independently set") both assume `email-capture-pipeline` currently renders
as one node on the Agents Map ring. Direct inspection of the real running
system found this premise is false: `GET /agents` returns
`email-capture-pipeline` with `"is_background_agent": true`, and
`layoutAgents.ts`'s own `layoutAgents()` (confirmed by reading its current,
real source — REQ-SB-51-US-01's own already-shipped change) filters
`agents.filter((agent) => !isBackgroundAgent(agent))` **before** building
`agentsBySection`/`mapAgents` — a Background Agent never occupies a ring
slot at all. `email-capture-pipeline` was moved off the Agents Map
entirely by `REQ-SB-51-US-01` onto the separate `CrawlersPage.tsx`
(confirmed by that file's own comment: "`AgentsMapCanvas.tsx`'s own
now-removed 'Background Agents' card"). Built the task exactly as
specified (a new adapter, `src/frontend/src/features/agents-map/
pipelineJobTreeAdapter.ts`, splicing 6 real Job entries in place of the
single `email-capture-pipeline` `AgentSummary`, inheriting
`is_background_agent` verbatim per the task's own explicit instruction) and
verified it against real fetched data (via an isolated Node harness running
the actual `spliceEmailCapturePipelineJobTree()` + real `layoutAgents()`
functions against real `GET /agents`/`GET /agents/email-capture-pipeline/
jobs`/`GET /sections` JSON, `T01`'s own established TestClient-based
verification method reused since the live dev server on port 8001 could
not be restarted to pick up `T01`'s already-`Done` code — see this task's
own Implementation Log for that separate finding). Result: the adapter
itself is correct (returns exactly 6 Job-derived entries, no
`email-capture-pipeline` entry, every field correctly inherited, every
OTHER Section/agent passes through byte-identical — `AC-05` genuinely
passes) but because every spliced entry inherits `is_background_agent:
true`, `layoutAgents()`'s own real, unmodified filtering excludes all 6
from `mapAgents` — the Data Gathering Section's own `mapAgents` count is
**0**, not 6 (`AC-01` fails), and `dependencyEdges` is empty since it's
built from `mapAgents` (`AC-02` fails). The task's own Constraint
("`layoutAgents.ts`... must receive ZERO changes") forbids fixing this by
changing the filter; the task's own Constraint ("`is_background_agent`...
copied verbatim") forbids fixing this by not inheriting the field. These
two locked instructions are now in direct, unresolvable tension with each
other and with locked `AC-01`/`AC-02` — not a matter of coder judgement,
since any unilateral choice either silently breaks a locked AC or silently
overrides an explicit, decomposer-authored design constraint.

**Resolution:** Not resolved by this coder pass — per this project's own
Forbidden-section rule, a locked AC cannot be silently weakened or
worked around; the task is marked `Blocked`, not `Done`. The likely fix is
architect-level, not coder-level: e.g. the spliced Job `AgentSummary`
entries should NOT inherit `is_background_agent` verbatim (set to `false`
so they occupy ring slots, since the whole point of this story is making
them visible where the aggregate pipeline agent is not) while every OTHER
inherited field (`type`/`working_mode`/`icon`/`color`/`description`) stays
verbatim as designed — or an equally deliberate alternative the architect
picks. This single-line adapter change (in the already-written
`pipelineJobTreeAdapter.ts`) is very likely sufficient once confirmed; not
applied unilaterally here because it contradicts this task's own explicit,
locked Constraint prose word-for-word.

**Resolving artefact:** Operator decision, 2026-08-16: "Jobs always render,
regardless of parent's flag" — the spliced Job `AgentSummary` entries get
`is_background_agent: false` hardcoded (never inherited from the parent
`email-capture-pipeline` entry); every other inherited field
(`type`/`working_mode`/`icon`/`color`/`description`) stays verbatim as
originally designed. `email-capture-pipeline`'s own real registry flag is
unchanged — it still appears on `CrawlersPage.tsx`; this is scoped only to
the synthetic Job entries the adapter produces. Recorded in
`Implementation/Tasks/REQ-SB-65-US-01-T02-agents-map-job-tree-rendering.md`'s
own `## Constraints`, superseding the original verbatim-inheritance design.

**Status:** Resolved

## ESC-039: `REQ-SB-66`'s own blanket "Prompt shows for every Type including Jobs" rule collides with two real Jobs that have no LLM prompt/call site of their own at all — Thread-Match/Merge and Detect-Recurring-Pattern — 2026-08-16

**Category:** unclear-requirement

**Trigger:** `REQ-SB-66-US-01`'s own `/spec` pass, direct reading of
`app/business/email_classification.py`'s six real Email Capture Pipeline Job
functions (the same six `REQ-SB-65-US-01` already renders as tree nodes).
Four of them make a real `compass_client` call and therefore have a real,
hardcoded prompt this requirement can make overridable
(`classify_captured_email` → `classify_email`; `summarize_attachment` →
`summarize_content`; `route_to_project` → `guess_project_for_thread`;
`consult_librarian` → `vault_filing_expert.determine_placement_and_file` →
`vault_filing_methodology.build_placement_prompt`). The remaining two —
`thread_match_merge` and `detect_recurring_pattern` — are confirmed, by
direct reading, to be purely deterministic Python: neither calls
`compass_client` or any other model at all; `thread_match_merge` mechanically
writes frontmatter/body sections from already-classified data,
`detect_recurring_pattern` only branches on `classification["recurring_
candidate"]` (a signal itself produced upstream by `classify_email`'s own
extended prompt) to decide whether to create a Pending Approval. `REQ-SB-66`'s
own operator-resolved Decision 1 ("Prompt and Guardrails are added to every
Type's own Settings, including Jobs... A Job's own Settings ends up genuinely
minimal — Prompt + Guardrails only") is a blanket, per-Type structural rule
that does not distinguish "a Job with a real prompt to override" from "a Job
with none" — because this distinction was not visible until the six real Job
functions were read directly, none of the operator's three already-resolved
`REQ-SB-66` decisions (per-type Settings shape, storage shape, default-
fallback) addresses it. Displaying a Prompt field for these two Jobs anyway
(per the blanket rule) with no real runtime call site to wire an override
into directly contradicts the requirement's own explicit acceptance bar:
"a real, persisted... value... that the real call site actually reads at run
time (not just a UI field that does nothing)."

**Resolution:** Resolved 2026-08-16, operator decision (option (b) of the
three named below): the Prompt field is OMITTED entirely for a Job with no
real runtime call site — never shown-but-inert. Decision 1's own blanket
"Prompt shows for every Type" rule is narrowed to "Prompt shows for every
Agent/Job WITH a real call site to wire an override into"; Guardrails still
shows unconditionally for every Type/Job regardless (it is structure-only
and identity-agnostic, so no call site is needed for it to make sense).
`REQ-SB-66-US-01`'s Scenario 10, `## Constraints`, and `gate_reason` all
updated to record this.

**Resolving artefact:** `Implementation/UserStories/
REQ-SB-66-US-01-real-editable-prompt-and-guardrails-placeholder.md` →
Scenario 10 ("A Job with no real LLM call site of its own omits the Prompt
field entirely").

**Status:** Resolved

## ESC-040: `REQ-SB-56-US-01-T00`'s own independent live `ConversationID` verification is NEGATIVE — contradicts the referenced 100/100-non-empty figure for a material 40.5% of the real sample, all on `IncludeRecurrences`-expanded recurring-occurrence items — 2026-08-17

**Category:** other

**Trigger:** `REQ-SB-56-US-01-T00`'s own explicit brief: run an
independently-executed, live, read-only COM probe against real Outlook
calendar items this session — not a copy of the architect's own
2026-08-16 "100/100 sampled real calendar items carried a non-empty
`ConversationID`" figure already referenced by `architecture.md`,
`REVIEW-QUEUE.md`, and `BACKLOG.md`. The probe mirrored
`list_calendar_events`'s own exact connection/window mechanics
(`GetDefaultFolder(9)`, `IncludeRecurrences = True`, the same `[Start]`
`Restrict()` window at its own default `days_back=7, days_ahead=14`).
Across the real 37-item sample this produced: **22/37 (59.5%)** carried a
genuine, usable, distinct `ConversationID` string (example:
`'E20C7692EED748E082340F21ED08451A'`, subject "Summary preparation for
Masdar workshop"). **15/37 (40.5%)** — a material fraction, not noise —
returned a broken value: `getattr(item, "ConversationID", None)` resolves
to a non-string bound-method object (`bool()` of it is truthy, so the
naive `getattr(...) or ""` pattern `list_recent_mail` already uses for
mail would silently pass this garbage value through as if it were a real
id); explicitly invoking it raises COM error `-2147352573 'Member not
found.'`; a follow-up raw-MAPI `PropertyAccessor.GetProperty` read of
`PR_CONVERSATION_ID` (proptag `0x3013001F`) against the same 15 items
also fails on every one, `-2147352571 'Type mismatch.'`. **Every one of
the 15 broken items has `IsRecurring = True` and `RecurrenceState` 2
(`olApptOccurrence`) or 3 (`olApptException`)** — i.e. every one is an
individual occurrence of a recurring series, expanded specifically by
`IncludeRecurrences = True`, the exact mechanism `list_calendar_events`'s
own docstring says is required to turn a recurring series into
individual occurrence items. 5 distinct real recurring series are
represented in the broken set. This directly contradicts the referenced
100/100-non-empty figure and falls squarely within `T00`'s own
Constraints' "material fraction" bar for a NOT-usable verdict — the task
therefore cannot record "T01 may proceed unchanged," per its own explicit
instruction not to force a pass. This is also the **third** independent,
live-confirmed instance on this same Outlook installation of a per-item
COM identity/relationship property being unreliable specifically on
`IncludeRecurrences`-expanded occurrence items, after `EntryID`
(`ESC-002`) and `GlobalAppointmentID` (`ESC-012`) — each failed
differently (non-unique-but-present vs. this one's outright
non-string/inaccessible), so this is a recurring *class* of finding on
this installation, not a one-off.

**Resolution:** Not resolved in this pass — no operator was available to
decide live. Per `T00`'s own Constraints, the finding is recorded exactly
as observed (see `REQ-SB-56-US-01`'s own `## Notes`, 2026-08-17 entry) and
is **not** silently narrowed or reinterpreted into a smaller scope for
`T01`. `T00` itself is `status: Done` (its own job — probe and record —
was correctly performed regardless of the outcome). `REQ-SB-56-US-01-T01`
is set `status: Blocked`, `gate: flagged`, with a pointer to this entry;
its own scope/Files-to-Modify/Tests/AC sections are otherwise untouched —
no attempt was made to build or re-scope it. `T02` was not touched at
all (it depends on `T01`, which never started). What still needs a
human/architect decision: how the primary ConversationID-match strategy
should treat recurring-occurrence meetings, given roughly 2 in 5 real
meetings in this calendar are exactly that — e.g. (a) treat a
non-string/invalid `ConversationID` as absent and route those meetings to
`T02`'s fallback strategy only (the primary strategy still works for the
59.5% single-occurrence majority), (b) investigate whether reading the
recurring series' own master item (rather than each expanded occurrence
proxy) resolves it before concluding the property is unusable for these
meetings at all, or (c) some other resolution — genuinely open, not
guessed here.

**Resolving artefact:** _pending_ — needs a human/architect decision on
how `T01`'s primary strategy should treat recurring-occurrence meetings,
recorded in `REQ-SB-56-US-01`'s own `## Notes` and
`REQ-SB-56-US-01-T01`'s own task file, before `T01` can resume.

**Update, 2026-08-17 (overnight, operator's own standing best-guess
authorization — no urgent human decision was available):** took the
Option (a) path listed above — a non-string/COM-inaccessible
`ConversationID` is treated identically to an absent one, never
fabricated into a link, falls through to `T02`'s fallback untouched.
Option (b) (recurring series' own master item) was deliberately NOT
attempted, left open for morning review. `REQ-SB-56-US-01-T01` reset
`Blocked → Ready` with a concrete scope addition (safe `""`-on-failure
guard, see the task file's own Constraints). Full reasoning:
`REQ-SB-56-US-01`'s own `## Notes`, 2026-08-17 resolution entry.

**Status:** Open — this is a provisional overnight call, not a genuine
operator confirmation; stays Open until the operator spot-checks it.

## ESC-041: `/triage BUG-014` — the bug's own stated gap-1 root cause ("outlook_com.py never reads Attachments") is directly contradicted by direct re-reading of the current live code — 2026-08-17

**Category:** other

**Trigger:** `/triage`'s own analyst pass on `BUG-014` ("Thread email
attachments are never captured, and the underlying save path has no
filename-collision protection"). The bug's own detail section in
`BUGS.md` states gap 1's root cause as: "`outlook_com.py` never reads a
`MailItem`'s `Attachments` COM collection at all — the word 'attachment'
does not appear anywhere in that file." Per this project's own standing
"confirm via direct code reading, not guessed" discipline, the analyst
re-read `src/backend/app/data_access/outlook_com.py` directly before
drafting the fix story and found this claim factually false for the
current file: it contains a full, real `_extract_attachments(item)`
function (COM `Attachments`-collection enumeration, save-to-temp/read/
delete technique, `_is_inline_attachment` filtering, `_MAX_ATTACHMENT_
BYTES` size cap), and `list_recent_mail()` — the SAME fetch function both
the legacy `classify_recent_emails` and the new `pipelines.email_capture_
pipeline.run_email_capture_pipeline` call — already sets
`"attachments": _extract_attachments(item)` on every returned email dict.
The word "attachment" (case-insensitive) occurs 15 times in the file, not
zero. The live production call chain was traced end-to-end (not assumed):
`capture_scheduler.py::run_capture_if_idle` →
`email_classification.run_capture_and_record_completion` →
`pipelines.email_capture_pipeline.run_email_capture_pipeline` →
`outlook_com.list_recent_mail` — the exact path `BUG-014` names as
producing an always-empty `email.get("attachments") or []` loop in
`_summarize_attachment_node`, yet that path's own fetch function already
populates the key it's accused of never populating. `CHANGELOG.md`'s own
history places this attachment-extraction plumbing among the very
earliest features of the project (well before `REQ-SB-55`'s Thread
pipeline, `SPRINT-049`, even existed) — not something added moments
before this triage pass. This is a genuine, material contradiction
between the bug ledger's own recorded investigation and the real code,
not a semantic quibble: a fix built literally to `BUG-014`'s own stated
mechanism (teach `outlook_com.py` to read `Attachments`) would be
redundant work that does not close the bug's own live-observed symptom (a
real captured Thread note, `01D26A7530444A23803A002210620160.md`,
genuinely has no `## Attachments` section and no `attachments/` folder on
disk — that live observation itself is NOT in dispute, only its named
cause is).

**Resolution (architect pass, `/plan-tasks` step 1, 2026-08-17):**
`BUGFIX-03-US-01` was still drafted (`status: Draft`, `gate: flagged`)
rather than blocked entirely at `/triage` time, since the bug's own
required observable outcome (a real attachment ends up saved + linked on
the Thread note, and same-filename attachments from different messages
never collide) is unambiguous and specable regardless of which exact
mechanism turns out to explain the live symptom. `BUG-014` itself was
still flipped `Open → In Sprint` in both `BUGS.md` and `BACKLOG.md`'s
`## Bugs` mirror, with `Fixed by: BUGFIX-03-US-01`, per `/triage`'s own
unconditional lifecycle rule.

The architect pass has now done the direct-code investigation this entry
called for and found the REAL, confirmed gap-1 mechanism (not `BUG-014`'s
own originally-stated one, and genuinely different from the four
candidate hypotheses this triage pass merely listed without deciding
between): `email_capture_pipeline.py`'s `_summarize_attachment_node`
only appends an entry to `## Attachments` when `summarize_attachment`
returns a real `dated_entry` — produced only on a fully successful
save-then-summarize path. Every other real outcome (an oversized
attachment over `outlook_com.py`'s 20MB `_MAX_ATTACHMENT_BYTES` cap, a
non-text-extractable saved file, or a real `CompassError`) collapses to a
`summary_error` this node silently discards — and for the oversized case
specifically, `vault_writer.write_attachments`'s own `.mkdir()` call is
never reached (it sits inside the `attachment["content"] is None`
early-continue branch), so the `attachments/` folder itself never comes
into existence. This ONE mechanism independently explains BOTH of
`BUG-014`'s own live-observed symptoms (missing `## Attachments` section
AND missing `attachments/` folder) with no unverifiable claim about
Outlook's own COM behavior, and is corroborated — not just structurally
read — by direct comparison against the still-live sibling
`classify_recent_emails` path, which already carries an honest "not
saved — exceeds the size cap" fallback line the new Thread pipeline never
inherited (a genuine, confirmed regression, not a never-built feature).
Full write-up, fix design for both gaps, and the honestly-unresolved
residual (which of several real-world variants — oversized cap, a
OneDrive/SharePoint cloud-attachment link, or a stale-dedup timing
artifact from `SPRINT-049`'s own same-day build-out — applied to the ONE
already-captured historical Thread specifically, which does not change
the fix's own design) is in `Implementation/Architecture/architecture.md`
→ "Thread Attachment Capture — Silent-Loss Fix + Per-Message Collision
Safety" and `BUGFIX-03-US-01`'s own `## Notes`.

**Resolving artefact:** Architect's `/plan-tasks` step 1 pass, 2026-08-17
— `Implementation/Architecture/architecture.md` → "Thread Attachment
Capture — Silent-Loss Fix + Per-Message Collision Safety" (root-cause
finding + fix scope for both gaps); `BUGFIX-03-US-01`'s own `## Notes`.
`/plan-tasks` proceeds with `T01` scoped to the confirmed mechanism above
(not `BUG-014`'s own originally-stated one), with one non-blocking
live-diagnostic verification sub-step folded into `T01` (mirroring
`REQ-SB-56-US-01-T00`'s own precedent) so the coder confirms which
real-world variant applied to the specific historical Thread, without
that confirmation gating the fix itself.

**Status:** Resolved

## ESC-042: `GET /system-health` was already returning a real, live `HTTP 500` before any `REQ-SB-68-US-01-T03` change landed — a pre-existing, unrelated data-integrity defect in `provider_registry.py`/`agent_providers.json`, not `system_health.py` itself — 2026-08-17

**Category:** other

**Trigger:** `REQ-SB-68-US-01-T03`'s own coder pass. Before making any
change, a direct `curl http://127.0.0.1:8001/system-health` against the
real running backend (port `8001`) returned `HTTP 500` consistently
across 3 separate real requests. A real traceback was captured by
invoking `system_health.get_system_health()` directly in a Python shell
against the real app (`.venv/Scripts/python.exe`, not guessed from the
outside via `curl` alone):

```
File "...\app\business\system_health.py", line 74, in get_system_health
    "providers": _providers_with_agent_names(),
File "...\app\business\system_health.py", line 66, in _providers_with_agent_names
    agent_registry.get_agent(agent_id)["name"] for agent_id in provider["agent_ids"]
TypeError: 'NoneType' object is not subscriptable
```

**Root cause, confirmed by direct inspection, not guessed:**
`app/business/provider_registry.py`'s persisted state
(`.second-brain/agent_providers.json`'s own `"assignments"` map, keyed by
agent id) carries a stale, orphaned key: `"email-capture": "compass"`.
No agent with id `"email-capture"` exists in `agent_registry.py`'s
`_SEED_AGENTS` today — it was renamed to `"email-capture-pipeline"` by
`REQ-SB-55-US-01-T08`/`ADR-043` point 6 (an already-`Done`, unrelated,
prior story), whose own docstring records the rename directly
("replaces the former single-stage `email-capture` Worker 1:1... same
three real Action ids"). `provider_registry.py::_load_state()` only ever
**adds** an assignment for an agent id newly seen in
`agent_registry.list_agents()` — it never **prunes** an assignment for
an agent id that no longer exists after a rename, so the orphaned
`"email-capture"` key has sat in `agent_providers.json` ever since that
rename, silently, with no consumer that dereferenced it until
`system_health.py::_providers_with_agent_names()` (built by the
already-`Done` `REQ-SB-31-US-01`, `SPRINT-019`) started calling
`agent_registry.get_agent(agent_id)["name"]` for every id in
`provider["agent_ids"]` without a None-guard. `agent_registry.get_agent`
returns `None` for the orphaned `"email-capture"` id, and `None["name"]`
raises the `TypeError`, surfaced by FastAPI as an unhandled `500`. This
is a genuine, real bug, live-confirmed **before** any of this task's own
changes — not something introduced by `REQ-SB-68-US-01-T03`, and not
caused by tonight's session (the rename predates tonight; confirmed the
identical crash, at the identical line, occurs against the pre-T03
`system_health.py` and again, unchanged, after T03's own change landed —
T03's own new `"scheduling"` key is never even reached). Ruled out as
candidates, by direct testing: `mcp_mount_reachable()`'s own `httpx.get`
self-call (confirmed working — a direct `curl -L http://127.0.0.1:8001/mcp`
and a direct in-process call both return the expected `406`, and the
crash traceback shows `_providers_with_agent_names()` failing before
`mcp_mount_reachable()` even matters to the outcome); `list_disabled_agents()`
(never reached — the traceback fails one key earlier, at `"providers"`).

**Why this is NOT `REQ-SB-68-US-01-T03`'s own fix to make:** the real
fault lines are (a) `provider_registry.py::_load_state()`'s own
reconciliation logic — a file not named anywhere in `T03`'s `## Files to
Modify` — or (b) a defensive None-guard inside
`system_health.py::_providers_with_agent_names()`, which `T03`'s own
task file explicitly places `## Out of Scope`: "Any change to
`mcp_mount_reachable`/`list_disabled_agents`/`_providers_with_agent_names`
beyond the import-list addition needed for `agent_schedule_registry` —
those three functions are otherwise untouched." Both real fix locations
belong to a different, already-`Done` story
(`REQ-SB-31-US-01`/`REQ-SB-55-US-01-T08`/`ADR-014`/`ADR-043`), not to
`REQ-SB-68-US-01-T03`'s own declared scope — per `Implementation/
Pipeline.md` hard rule 5 ("ANY out-of-scope event → immediate
escalation, no improvisation"), this is escalated rather than patched
in-place. No file outside `T03`'s own `## Files to Modify`
(`src/backend/app/business/system_health.py`) was touched to work around
this — not even `.second-brain/agent_providers.json`'s own stale data
key, despite that being the most surgical possible fix, since it is not
listed in `## Files to Modify` either.

**Practical consequence for `T03`:** `T03`'s own in-scope code change
(composing `agent_schedule_registry.get_job_run_states()` into the
`"scheduling"` key, removing `"last_capture_run"`) is built exactly per
spec and verified correct in isolation (direct calls to
`agent_schedule_registry.get_job_run_states()` and to
`system_health.mcp_mount_reachable()` both succeed and return the
expected shape). But `GET /system-health` cannot be live-verified
end-to-end returning `HTTP 200` while this pre-existing, unrelated
defect remains — every real request still 500s at `_providers_with_agent_names()`,
before `T03`'s own new key is ever reached. `T03` is left `status:
Blocked` rather than `Done` (mirroring `ESC-012`'s own identical
precedent: the already-built, faithful, non-regressive code is left in
place, not reverted).

**Resolution:** Not resolved by the coder pass — correctly escalated
rather than improvised. Resolved by direct operator decision, 2026-08-17:
**Option (a)** — prune orphaned assignment keys inside
`provider_registry.py::_load_state()`'s own reconciliation loop,
self-healing on every read, symmetric with that same function's existing
add-missing-assignment behavior. Chosen over Option (b) (a defensive
None-guard in `_providers_with_agent_names()`) because it fixes the real
root cause (stale data in `agent_providers.json`) rather than just
hiding the symptom — Option (b) alone would leave the orphaned
`"email-capture"` key sitting in the JSON file forever, silently, ready
to bite the next consumer that dereferences it without a guard, which is
inconsistent with this codebase's own repeated self-healing-reconciliation
convention (`working_mode_registry.py`, `background_agent_registry.py`,
and this same function's own existing add-side logic). `.second-brain/
agent_providers.json`'s stale key gets cleaned up automatically the next
time `_load_state()` runs post-fix — not hand-edited.
`REQ-SB-68-US-01-T03` is unblocked to resume under this resolution.

**Resolving artefact:** _pending_ — needs an architect/human decision on
the fix shape (`provider_registry.py::_load_state()` reconciliation vs.
`system_health.py::_providers_with_agent_names()` defensive guard),
most plausibly landing as a small follow-up task before
`REQ-SB-68-US-01-T03` (and its downstream `T04`) can resume and reach
`Done`.

**Status:** Open

**Update, 2026-08-17 — Resolved operationally.** `provider_registry.py::
_load_state()` now prunes any `"assignments"` key whose agent id is not
in the current, real `agent_registry.list_agents()` id set — a small,
surgical addition, symmetric with that same function's existing
add-missing-assignment loop (the exact Option (a) shape the Resolution
above named). Live-verified against the real running backend
(`.venv/Scripts/python.exe -m uvicorn app.main:app --port 8001`) and the
real vault:

- **Before:** direct read of `.second-brain/agent_providers.json`
  confirmed the stale `"email-capture": "compass"` key was present.
- **Trigger:** a real `GET /system-health` request (which calls
  `provider_registry.list_providers()` → `_load_state()`).
- **After:** the same file, re-read directly, no longer carries the
  `"email-capture"` key — pruned automatically by `_load_state()`'s own
  reconciliation loop, not hand-edited.
- **`GET /system-health` now returns a real, live `200`**, with the exact
  shape `{"mcp", "providers", "disabled_agents", "scheduling"}` and no
  `"last_capture_run"` key — confirmed via direct `curl` against the real
  running backend.
- `REQ-SB-68-US-01-T03`'s own 3 non-AC smoke checks, blocked by this
  defect in the original coder pass, all passed live: (1) the
  `"scheduling"` list carries exactly the 3 covered-agent entries, each
  shape-correct and honest (one already `has_run: true` from a real
  earlier capture pass this session, two genuinely `has_run: false`);
  (2) a real manually-triggered `run_capture_now` dispatch was observed
  transitioning through the live endpoint from `"running": true` (a real,
  growing `"elapsed_seconds"`, sampled repeatedly) to `"running": false`
  with a real `"last_duration_seconds"` (`597.1s`) and
  `"last_outcome": "success"`; (3) an uncovered action
  (`compass-expert`/`build_knowledge`) was dispatched and confirmed to
  never appear in `"scheduling"`, with the other 3 response keys
  unaffected.
- `system_health_router.py` confirmed byte-for-byte unchanged (`git diff`
  shows no changes to that file) — the fix required no change to it, per
  `T03`'s own original prediction.

`REQ-SB-68-US-01-T03` is now `status: Done`, `gate: clear`.
`MEMORY.md`'s matching Constraint entry (2026-08-17, `REQ-SB-68-US-01-T03`)
is updated in place to record the fix rather than describe an open defect.

**Resolving artefact:** `src/backend/app/business/provider_registry.py`
(`_load_state()`'s new pruning loop) and
`Implementation/Tasks/REQ-SB-68-US-01-T03-scheduling-system-health-extension.md`
(`status: Done`) — confirmed live, not just designed.

**Status:** Resolved

## ESC-043: `BUGFIX-03-US-01-T02`'s own required `write_attachments` per-message nesting silently breaks Inbox Cockpit's flat-path attachment lookup for future `classify_recent_emails` captures — 2026-08-17

**Category:** shared-interface-change

**Trigger:** `BUGFIX-03-US-01-T02`'s own verification pass. Before
verifying, `grep write_attachments` across `src/backend` (confirming the
task's own claim that `summarize_attachment` and `classify_recent_emails`
are the only two live callers) surfaced a THIRD real file matching:
`app/business/cockpit/attachments.py` (Inbox Cockpit, `ADR-036`, exposed
live via `cockpit_router.py`'s `GET .../attachments` and `POST
.../attachments/{filename}/hand-off` endpoints). It does not call
`write_attachments` itself, but its own `_attachments_dir()` hardcodes the
identical save-path CONVENTION `write_attachments` used to produce for
`classify_recent_emails`-sourced email notes: a FLAT
`Work/Emails/attachments/<email_note_stem>/<filename>` — justified in its
own docstring as "confirmed live against real vault fixtures... byte-
identical to write_attachments' own `note_slug`." Neither the analyst's
story (`BUGFIX-03-US-01`), the architect's `architecture.md` design
("Thread Attachment Capture — Silent-Loss Fix + Per-Message Collision
Safety"), nor the decomposer's task file considered this downstream
reader when adopting the `message_segment`-nesting fix for
`classify_recent_emails`'s own call site — that call site's own update
was framed throughout as "mechanical, no-real-collision-risk... an
empty-string or id-derived segment is equally correct there since no real
collision risk exists on that path," which is true for the WRITE side
(no filename collision) but does not address the READ side
(`cockpit/attachments.py` now looks in the wrong, one-level-too-shallow
directory). `classify_recent_emails` is still live (reachable via
`app/api/email_poc_router.py`'s `/poc/classify-emails`), so this is a
real, reachable regression, not a theoretical one — any email captured
through that path AFTER this fix will have its attachments silently
invisible to Cockpit's `list_attachments` (returns `[]`, no error) and
`hand_off_attachment_to_chat` (returns `{"status": "not_found"}`, no
error) — a genuine functional loss with no exception, no log.
Already-saved historical attachments at the old flat path are unaffected
(this fix does not move or delete anything already on disk).

**Resolution:** Not resolved in this pass. `BUGFIX-03-US-01-T02`'s own
fix is correctly built and live-verified exactly as the story/architecture
adopted (per that story's own Constraints, gap 2's fix direction was
"adopted, not open" — not this coder's call to redesign to avoid the
newly-found consequence). The consequence lies entirely in
`app/business/cockpit/attachments.py`, a file explicitly outside `T02`'s
own `## Files to Modify` — per `Implementation/Pipeline.md` hard rule 5,
left unfixed and undisturbed, not improvised on. `T02` itself proceeds to
`Done` (both locked ACs, `AC-01`/`AC-02`, verified live and passing; this
finding does not touch either) — mirrors `BUGFIX-03-US-01-T01`'s own
established precedent this same story of recording, not fixing, a
real-but-out-of-scope finding (`BUG-017`).

**What still needs a human/architect decision:** the fix shape for
`cockpit/attachments.py::_attachments_dir` — most plausibly either (a)
thread `message_segment`/the email's own id into Cockpit's own path
resolution (mirroring `write_attachments`'s new contract exactly), or (b)
have Cockpit enumerate/glob one level deeper instead of assuming a flat
directory. A `/bug` capture is recommended so this is tracked and triaged
through the normal bug-fix flow rather than decided ad hoc here.

**Resolution:** Resolved directly, 2026-08-17, same day — logged as
`BUG-018` (`BUGS.md`, `Closed`) and fixed immediately rather than parked.
Took **Option (b)**: `cockpit/attachments.py` gained a new
`_iter_attachment_files(email_note_stem)` generator that yields files
sitting directly in the attachments directory (the real, already-saved
historical flat shape — untouched, never migrated) AND files one level
deeper inside any per-message-segment subdirectory (the new nested
shape from `T02`). Chosen over Option (a) since it needs no new coupling
to the exact `message_segment` value, and `classify_recent_emails` only
ever writes exactly one segment per email note, so the glob is
unambiguous. Verified live against the real vault both directions: a
real historical flat attachment ("Product Exhibit 2 - Compass Core42
210726.docx") still found correctly; a scratch nested attachment
(mirroring the new shape) also found correctly via both
`list_attachments` and `hand_off_attachment_to_chat`, scratch data
cleaned up afterward.

**Resolving artefact:** Direct fix, 2026-08-17 —
`app/business/cockpit/attachments.py::_iter_attachment_files` (see
`BUG-018` in `BUGS.md` for the full write-up).

**Status:** Open

## ESC-044: `ADR-046`'s own Consequences section mischaracterizes `thread_note_exists`/`thread_note_path` as "becoming dead code" — a real, live second caller in `meeting_classification.py` silently breaks — 2026-08-17

**Category:** adr-deviation

**Trigger:** `REQ-SB-69-US-01-T06`'s own verification pass. Before
declaring `thread_note_exists`/`thread_note_path` untouched-but-superseded
per the task's own Constraint ("left completely unmodified and
undeleted... any other real caller must be confirmed first"), a
repo-wide `grep` for both names across `src/backend` (not just the one
call site `T06`'s own task file named, `thread_match_merge`) surfaced a
real, live SECOND caller: `app/business/meeting_classification.py::
_link_to_thread_by_conversation_id` — `REQ-SB-56-US-01`'s own Link-to-
Thread Job's PRIMARY (exact-match) strategy, which calls `vault_writer.
thread_note_exists(conversation_id)` to decide whether a Meeting should
be linked to a matching Thread by an exact `conversation_id` match,
before falling through to `T02`'s own weaker date-proximity fallback
heuristic. `ADR-046`'s own Consequences section (`Implementation/
Architecture/ADR.md`) states: *"`thread_note_path`/`thread_note_exists`
... become dead code for the Thread-note-creation-and-lookup path once
this ships."* This is factually wrong — `meeting_classification.py` is a
real, live, currently-reachable caller the architect's own pass did not
find or name. Once `T06` ships (Thread filenames become
`<thread_name>-<date>-<hash8>.md` instead of the old deterministic
`<slug-of-conversation_id>.md`, `ADR-046` Decision 6/7),
`thread_note_exists(conversation_id)` — which still checks the OLD path
— silently returns `False` for every genuinely-existing Thread created
AFTER this ships, confirmed live: a real, disposable post-`ADR-046`
Thread was created via `thread_match_merge`, then
`vault_writer.thread_note_exists(conv)` returned `False` while
`vault_writer.resolve_thread_note_path(conv)` correctly resolved the
Thread's real, current path. This permanently starves `REQ-SB-56-US-01`'s
own PRIMARY linking strategy in favor of its weaker fallback, for every
future new Thread — a real, silent, ongoing quality regression (not a
hard crash, no exception, no log), directly caused by `T06`'s own
in-scope filename change, in a file (`meeting_classification.py`)
explicitly outside `T06`'s own `## Files to Modify`.

**Resolution:** Resolved directly, same pass, 2026-08-17 — mirrors
`ESC-043`/`BUG-018`'s own established "found live during this task's own
verification, small and causally inseparable from the change that
exposed it, fixed same day rather than left dangling for a separate
triage cycle" precedent. Logged as `BUG-019` (`BUGS.md`, `Closed`).
`_link_to_thread_by_conversation_id`'s existence check swapped from
`vault_writer.thread_note_exists(conversation_id)` to `vault_writer.
resolve_thread_note_path(conversation_id) is not None` — the same real,
current-path lookup `T05`/`T06` already built and live-verified for
`thread_match_merge` itself; a one-line, surgical fix (this function only
ever consumed the old helper's boolean existence signal, never its
returned path, so no further change was needed). `thread_note_exists`/
`thread_note_path` themselves are still left completely unmodified and
undeleted, per `T05`'s own Constraint (their own retirement stays a
future, separately-scoped cleanup task) — only their one remaining real
caller was moved onto the new lookup. `ADR-046` itself is not edited
(specs are append-only) — its Consequences section's "becomes dead code"
claim is now known-incomplete; a future ADR touching `Work/Threads/`
lookups should re-grep before repeating that assumption. Verified live:
a real disposable post-`ADR-046` Thread + a disposable Meeting note
confirmed `_link_to_thread_by_conversation_id` now returns `True` and
correctly writes the Meeting's own `thread` frontmatter field; scratch
data cleaned up afterward. `T06` itself proceeds to `Done` — all of its
own locked ACs (`AC-05`/`AC-06`/`AC-07`) and the stale-payload fix are
verified live and unaffected by this finding, mirroring `ESC-043`'s own
"this finding does not touch either locked AC" precedent.

**Resolving artefact:** Direct fix, 2026-08-17 —
`app/business/meeting_classification.py::_link_to_thread_by_conversation_id`
(see `BUG-019` in `BUGS.md` for the full write-up).

**Status:** Resolved

---

## ESC-045: `agent_schedules_router.py::run_now` hardcodes the shared Outlook-COM dispatch lock for every `capability_id` — a real, disclosed residual lock-sharing gap for `process_staged_email`'s own manual on-demand trigger — 2026-08-17

**Category:** shared-interface-change (out-of-scope, non-blocking)

**Trigger:** `REQ-SB-69-US-01-T04`'s own build pass. Before finalizing
lock separation, re-read every real caller of `agent_schedule_registry.
dispatch_with_shared_lock` to confirm `process_staged_email` never
reaches it. Found `app/api/agent_schedules_router.py::run_now` (`POST
/agents/{agent_id}/schedules/{capability_id}/run-now`, a real, already-
shipped, reachable endpoint, `ADR-037` point 7) unconditionally calls
`agent_schedule_registry.dispatch_with_shared_lock(agent_id,
capability_id, trigger="direct")` for ANY `capability_id` — this file is
explicitly outside `T04`'s own `## Files to Modify`. Once `process_
staged_email` became a real, granted, mutating skill this task (`ADR-046`
Decision 4), a human manually calling this endpoint with
`capability_id="process_staged_email"` would incorrectly acquire the
SHARED Outlook-COM lock instead of the new, dedicated `_processing_lock`
— reintroducing, for this one specific manual trigger path only, exactly
the lock-sharing `T04` exists to eliminate. The two OTHER real locations
that route a PERSISTED recurring schedule for `process_staged_email`
(`agent_schedule_registry.py::_make_scheduled_tick_callback`, the live-
mutation path, and `capture_scheduler.py::_build_scheduled_tick`, the
cold-start path) were both inside `T04`'s own `## Files to Modify` and
were fixed with a matching conditional in each. `T04`'s own hard
Constraint — lock separation must hold "for at least one real, reachable
trigger path (the hourly/app-start scheduled tick)" — is unaffected: that
specific trigger path is correctly lock-separated; `run_now` is a
different, additional, manual trigger surface the Constraint's own
wording does not bind.

**Resolution:** Not resolved in this pass. Fixing `agent_schedules_
router.py::run_now` would be a small, one-line conditional mirroring the
two fixes already made elsewhere (route `process_staged_email` through
`agent_schedule_registry.dispatch_with_dedicated_processing_lock`
instead), but the file is outside `T04`'s own `## Files to Modify` — per
`Implementation/Pipeline.md` hard rule 5, left unfixed and undisturbed,
not improvised on. `T04` itself proceeds to `Done` — all 3 of its own
locked ACs (`AC-01`/`AC-02`/`AC-03`) plus the `run_capture_now` backward-
compatibility regression are verified live and unaffected by this
finding, mirroring `ESC-043`'s own "this finding does not touch either
locked AC" precedent.

**What still needs a human/architect decision:** none, strictly — the fix
shape is unambiguous and small (mirror the two already-made fixes). A
lightweight follow-up task is recommended so it is tracked and built
through the normal flow rather than decided ad hoc here; not urgent
enough to warrant a `/bug` capture on its own (no real trigger has yet
reached this endpoint with `process_staged_email` in production use).

**Resolving artefact:** Direct fix, 2026-08-17 —
`app/api/agent_schedules_router.py::run_now` now selects
`agent_schedule_registry.dispatch_with_dedicated_processing_lock` for
`capability_id == "process_staged_email"` and keeps `dispatch_with_
shared_lock` for every other id, mirroring `agent_schedule_registry.
_make_scheduled_tick_callback`'s/`capture_scheduler._build_scheduled_
tick`'s own identical dispatch-selection shape (the fix this entry's own
`## Resolution` note anticipated, applied verbatim). While reading this
file's own sibling manual-dispatch entry point per the resolving task's
own instruction, also found and fixed a related, previously-undisclosed
gap in `app/api/agents_router.py::_invoke_capability`: that function
special-cased only `capability_id == "run_capture_now"` for lock
routing — `pull_email`/`process_staged_email` (both real, reachable
`skill_tools.SKILLS` members since `T04`) fell through to the generic,
UN-locked `skill_registry.invoke_skill` branch entirely (not merely the
wrong lock — no lock at all), since `POST /agents/{agent_id}/actions/
{action_id}` also routes any `SKILLS` member through this function.
Fixed the same way: `pull_email` now joins `run_capture_now` through the
shared Outlook-COM lock, `process_staged_email` through the dedicated
processing lock; `history_recorded` widened to match so no duplicate
history entry is written for either. Verified live: real backend
process, `email_pull.pull_and_stage_emails` monkeypatched to a real
15s sleep (simulating a real stalled Pull, mirroring `T04`'s own AC-02
induced-stall technique) and `email_capture_pipeline.classify_captured_
email` monkeypatched to fail fast per item (same technique, isolates
timing from real Compass latency); against the 4 real items already
staged in the configured vault's `.second-brain/email_staging/`, a
separately-dispatched `process_staged_email` completed in 0.55s (via
`run_now`) and 0.64s (via `_invoke_capability`) while the shared lock
was confirmed still held and `pull_email` was still genuinely mid-sleep
(completing at 15.01s in both cases) — through BOTH fixed entry points.
All 4 staged items remained staged afterward (no data loss, per-item
try/except holding as already established by `T04`).

**Status:** Resolved

---

## ESC-046: Real, pre-existing legacy-flat-vs-OKF-directory filename-stem collision shadows most already-migrated real Customers in `vault_indexing`'s stem-keyed index — 2026-08-18

**Category:** unanticipated-file (out-of-scope, non-blocking)

**Trigger:** `REQ-SB-58-US-01-T01`'s own mandated live smoke-check verification
(step 1, real Customer with real, non-empty `## Glimpse` content) against
the real configured vault. Direct inspection found that for the large
majority of real Customers already migrated to `ADR-042`'s OKF directory
shape (`Masdar`, `ADNOC`, `G42`, `EWEC`, `Core42`, `Dubai Future
Foundation`, `Government of Azerbaijan`, `Sindan`, `Department of
Government Enablement`, `Mubadala Investment Company`, `ILOE`, `TAQA`,
`SimplAI`, `Presight` — 14 of 17 migrated Customers), a **stale, legacy,
pre-migration flat hub note still exists on disk at `Work/Customers/
<Name>.md`, side by side with the new `Work/Customers/<slug>/<slug>.md`
OKF concept file `customer_hub_linking.ensure_customer_hub_note` (`ADR-042`
Consequences) now writes.** Both files share the identical filename stem
(e.g. `"Core42"`), and `vault_indexing.rebuild_index()` keys its index
purely by stem (`ADR-024`) — confirmed live: `vault_indexing.get_index()
["Core42"]["frontmatter"]["type"]` returns `"Customer"` (the legacy flat
note's own, differently-cased, non-OKF-conformant frontmatter shape — no
`## Glimpse`/`## Background`, no `title`/`status`/`generated`/`verified`
fields at all), never `"customer"` (the real, current OKF concept file
`REQ-SB-57`'s Synthesizer actually keeps up to date) — because
`vault_writer.list_all_note_paths()`'s sorted-path iteration visits the
OKF concept file first and the legacy flat file second, and `rebuild_
index`'s `new_index[entry["stem"]] = entry` assignment lets the
later-visited one silently win. This is a real, load-bearing consequence
`ADR-042`'s own "first vault locations where a kind folder's contents are
not flat `.md` files" Consequence (which `REQ-SB-54-US-01-T06` already
fixed the *discovery* half of, per `Implementation/Learnings.md`
`SPRINT-048`) did not fully anticipate: fixing discovery so BOTH files
are found is not the same as the two files not colliding once found. No
code anywhere retires/deletes a Customer's old flat hub note once
`ensure_customer_hub_note` migrates it onto the new directory shape
(`app/business/customer_hub_linking.py`'s own docstring confirms the old
flat-file primitives are deliberately kept alive, unmodified, for
`partner_hub_linking.py`'s separate, still-live Customer→Partner use —
not because the stale per-Customer flat file itself is still meant to
exist). Concretely, for these 14 Customers, this story's own `glimpse_
first_qa.resolve_glimpse_first_context` (and, more broadly, `vault_
search.search`/`get_note_detail` and anything else keyed off `vault_
indexing.get_index()[stem]`) reads the wrong file entirely — editing the
REAL OKF concept file's `## Glimpse` (the exact test setup `T02`'s own
locked-AC live verification, e.g. `AC-01`, calls for) has **zero
observable effect** on what this mechanism actually resolves, since the
index entry for that stem never points at it. Only 3 of 17 migrated
Customers are collision-free (`Microsoft Azure`, `Azerbaijan Ministry of
Digital Development and Transport`, `Unsorted`) — and none of those 3 yet
carry real, non-empty, Synthesizer-produced Glimpse content (their own
Glimpse/Background are still the untouched `create_customer_directory_
baseline` empty default, since `REQ-SB-57`'s Synthesizer has never had
real evidence to run against for them). `T01`'s own `## Files to Modify`
is exactly one new file, `app/business/glimpse_first_qa.py` — fixing the
underlying collision would mean editing `vault_indexing.py` (index
uniqueness/precedence) and/or `vault_writer.py`/`customer_hub_linking.py`
(retiring the stale legacy file on migration) and/or deleting real vault
files outright, all explicitly outside this task's own Constraints
("Do not modify `vault_search.py`, `vault_indexing.py`, or `vault_writer.
py`") and none of them this task's call to make unilaterally.

**Resolution:** Open — not fixed at the primitive level (out of `REQ-SB-
58-US-01-T01`'s declared scope). `T01` itself is built and verified using
a disposable Customer/Project fixture (`vault_writer.create_customer_
directory_baseline`/`create_project_directory_baseline` +
`replace_body_section`, explicitly sanctioned as an alternative by this
task's own `## Tests` step 1/2 wording), created, verified, and fully
cleaned up (directory removed) during this pass — real pre-existing vault
content (`Core42.md`/`Core42/Core42.md` and every other Customer)
confirmed byte-for-byte/mtime-unchanged afterward. This real, disclosed
collision is named honestly rather than silently routed around or hidden,
mirroring this project's own established `ESC-027`/`ESC-035`/`ESC-042`
precedent (a real, out-of-scope, root-caused defect discovered via
due-diligence live verification does not block the task that found it).
**Directly informs `REQ-SB-58-US-01-T02`'s own live-verification test-data
design**, next in this same sprint (`SPRINT-058`): `T02`'s locked-AC
checks (`AC-01`/`AC-02`/`AC-04`/`AC-05`, each naming "a real test
Customer's OKF concept file `## Glimpse`/`## Background`... deliberately
edited") must pick a real Customer OUTSIDE this collision list (`Microsoft
Azure`/`Azerbaijan Ministry of Digital Development and Transport`) or a
disposable one, never one of the 14 shadowed Customers, or the edited
content will be silently invisible to the mechanism under test.

**What still needs a human/architect decision:** whether the fix is (a) a
one-time cleanup pass deleting/archiving each stale legacy flat Customer
hub note once its OKF directory concept file exists, (b) a `vault_
indexing`-level precedence rule (OKF concept file always wins a stem
collision against a flat file in the same top-level kind folder), or (c)
both — a genuine design choice for a dedicated fix story to make, not
decided here.

**Resolving artefact:** _pending_ — recommend `/bug` capture (Area:
Logic) so it can be batched into a `BUGFIX-NN-US-01` fix story.

**Status:** Open

**Status:** Resolved

## ESC-047: `retrieve_notes_in_agent_scope`'s own MCP tool schema requires the CALLING model to self-report its own literal internal `agent_id` — the model is never told that literal string anywhere in its own context, and reliably guesses wrong — 2026-08-18

**Category:** out-of-scope (non-blocking)

**Trigger:** `REQ-SB-58-US-01-T02`'s own mandated live verification of
`AC-02`/`AC-03` (Scenario 2/3 — the "existing full-search baseline" and
the evidence-drill-down follow-up) against the real running app, real
Compass Provider, and a disposable Customer/Project/Thread fixture.
Direct, repeated live observation (8 real `vault-qa` chat turns across
this pass, including 3 explicitly-instrumented diagnostic attempts that
captured the exact tool-call arguments the model actually sent):
`retrieve_notes_in_agent_scope(agent_id: str)` (`app/api/mcp_server.py`,
`REQ-SB-29-US-01`, `Done`, unmodified by this task) is registered with
`agent_id` as a required argument the CALLING model itself must supply —
the server never auto-binds/injects the real caller's id. **No system
message anywhere in this graph's own message list (`state.py::history_
entries_to_messages`'s identity/grounding text, unmodified by this
task's own additive clause; T01/T02's own new Glimpse-first context
message) ever states `vault-qa`'s literal internal id string** — the
identity sentence only ever names the human-readable display name
(`agent["name"]`, `"Vault Q&A"`). Confirmed live via a captured tool-call
argument: one real attempt sent `{"agent_id": "vault_qa_agent"}` — a
plausible-looking but wrong guess (neither the real internal id
`"vault-qa"` nor the real display name `"Vault Q&A"`) — which the server
honestly rejected (`{"status": "rejected", "message": "Unknown agent
'vault_qa_agent' -- request refused."}`), and the model then gave an
honest, non-fabricated "I don't have bounded query access" reply
(`REQ-SB-33`'s grounding guardrail working exactly as designed on the
rejection path). In every other observed attempt across this pass, the
model simply never attempted the call at all, apparently for the same
underlying reason (no confident belief in its own callable id). **This
is a real, pre-existing `REQ-SB-29-US-01` tool-contract fragility,
confirmed unrelated to and unaffected by this task's own new
`glimpse_first_context` node** — reproduced identically with Glimpse-
first monkeypatched OFF (a byte-identical no-op vs. pre-`REQ-SB-58`
behavior), so the SAME failure mode would occur for `vault-qa`'s
pre-`REQ-SB-58` full-search baseline calling this same tool today, with
or without this story ever having been built. Fixing it would mean
either changing `retrieve_notes_in_agent_scope`'s own MCP signature
(`app/api/mcp_server.py`, to auto-resolve the caller's id server-side
instead of trusting a model-supplied argument) or adding the literal
internal id string into every agent's own identity system message
(`state.py`) — both squarely outside this task's own `## Files to
Modify`/Constraints (which permit exactly one prescribed additive clause
to `state.py`'s grounding text, not a new, unprescribed identity
disclosure), and neither is this task's call to make unilaterally against
an already-`Done`, frozen story (Pipeline hard rule 1).

**Resolution:** Open — not fixed at the primitive level (out of `REQ-SB-
58-US-01-T02`'s declared scope). `T02`'s own new node, gating, and graph
wiring are independently confirmed fully correct and unaffected: (a) the
tool remains bound and reachable for `vault-qa` exactly as before (no
existing tool/node/routing branch removed or narrowed, satisfying this
story's own Constraint); (b) a live chat turn genuinely attempts the call
for a real drill-down follow-up (confirmed via captured tool-call
arguments, above) — the graph's own tool-execution loop, MCP client
plumbing, and business-layer function (`scope_query_tools.retrieve_
notes_in_agent_scope`) all execute exactly as designed end-to-end,
including an honest, non-fabricated failure path when given a wrong
argument; (c) a direct, independent call with the CORRECT argument
(`scope_query_tools.retrieve_notes_in_agent_scope("vault-qa")`) returns
the real fixture Thread note, correlatable via the Glimpse's own
`[[wikilink]]` stem, confirming the underlying mechanism `AC-02`/`AC-03`
need proven is genuinely intact. `AC-02`/`AC-03` are recorded as verified
via this closest-available, fully-disclosed combination of real live
tool-call-attempt evidence plus a real, independent direct-call
confirmation — mirroring this project's own established `ESC-022`/
`ESC-025`/`ESC-046` precedent ("root-cause a live failure fully before
deciding build-defect vs. out-of-scope finding; escalate the latter
formally rather than loosening the check to make it pass" /
"a real, out-of-scope, root-caused defect discovered via due-diligence
live verification does not block the task that found it"). Full
reasoning and captured evidence recorded in `REQ-SB-58-US-01-T02`'s own
`## Implementation Log`.

**What still needs a human/architect decision:** whether the fix is (a)
`retrieve_notes_in_agent_scope`'s own MCP signature drops the `agent_id`
argument entirely and resolves the real caller id server-side (would
need a caller-identity channel this MCP tool-call boundary doesn't
currently carry), (b) every agent's own identity system message is
extended to also state its literal internal id (a `REQ-SB-33`/`state.py`
-adjacent change), or (c) both — a genuine design choice for a dedicated
fix story to make, not decided here.

**Resolving artefact:** _pending_ — recommend `/bug` capture (Area:
Logic) so it can be batched into a `BUGFIX-NN-US-01` fix story.

---

## ESC-048: `REQ-SB-71-US-02`'s own mandated retargeting of `resolve_thread_note_path` (`T02`) breaks the still-live, scheduled `thread_match_merge` pipeline's create-vs-update check for every pre-redesign, flat-shape Thread note — 2026-08-18

**Category:** out-of-scope (non-blocking)

**Trigger:** `/implement-sprint SPRINT-061`'s own real, live build of
`REQ-SB-71-US-02`. Direct code reading plus real, live verification
(found and confirmed, not assumed): `T01`'s revived `thread_directory_
paths`/`create_thread_note_baseline` and `T02`'s own explicitly-mandated
retargeting of `resolve_thread_note_path(conversation_id) -> Path | None`
(`ADR-048` Decision 7) change that function's own internal mechanism from
a frontmatter scan over `list_thread_notes()` to a direct, deterministic
existence check against `thread_directory_paths(conversation_id)
["concept"]`. This is exactly correct and required for the redesign's own
new-capture path — but `resolve_thread_note_path` is also the SAME
primitive `thread_match_merge` (`email_classification.py`,
`REQ-SB-55-US-01`, `Done`) already uses for its own create-vs-update
decision, and `thread_match_merge` is still the live implementation
behind the SCHEDULED `email-capture-pipeline` Agent's `process_staged_
email` capability (`REQ-SB-69-US-01`, `Done`, `ADR-046`) — explicitly
required by this SAME story's own Constraint to "stay wired exactly as
it is today, completely untouched by this story."

Confirmed live, not merely reasoned: `list_thread_notes()` (retargeted
by `T02` to `Work/Threads/*/*.md` filtered to `path.parent.name ==
path.stem`) returns **zero** matches for any of this vault's real,
pre-existing OLD-shape flat `Work/Threads/<name>.md` notes (dozens
observed, e.g. `RE- Azure-Net New Revenue Forecast for H2 for AM
Updates-2026-07-27-8cd2025b.md`) — those notes simply do not live at a
`*/*.md` depth at all. This means: the moment `thread_match_merge` next
runs (via a further real scheduled tick, or a manual "Run Capture Now"/
Pending-Approval-approve action) against a NEW message in an ALREADY-
EXISTING OLD-shape conversation, `resolve_thread_note_path` will
incorrectly report "not found," `thread_match_merge` will treat it as
`created=True`, and will create a SECOND, DUPLICATE Thread note for that
same real conversation under the OLD renamable-filename scheme — silently
splitting that conversation's own continuity (tags/participants/summary)
across two separate files, a genuine live data-correctness regression to
a currently-`Done`, explicitly-protected capability.

Neither `T01` nor `T02` (nor any other task in this story) lists
`app/business/pipelines/email_capture_pipeline.py` (the module whose own
graph still calls `thread_match_merge`) in its `## Files to Modify` — the
decomposer's own addendum explicitly left "confirming and retiring
`thread_match_merge` itself" as an optional, coder-level, NOT-mandated
scope-internal judgment call for whichever task's coder finds it clean to
do so (`ADR-048` Consequences, `T05`'s own decomposer Notes) — but doing
so would require editing a file no task declares, a real "unanticipated
file required" trigger this role must not improvise past.

**Protective action taken (real, not merely proposed):** before writing
any code this session, `email-capture-pipeline`'s working mode was
flipped `autonomous` → `supervised` via the real, existing `PATCH
/agents/email-capture-pipeline` endpoint (`{"working_mode":
"supervised"}`) — confirmed live, and confirmed still `supervised` after
every server restart this session (state persists in `agent_working_
modes.json`, unaffected by the code changes). This prevents the live
hourly scheduler (`run_capture_if_idle`, `ADR-005`) from auto-running the
old `thread_match_merge` path at all — a Supervised-mode tick creates a
Pending Approval instead of executing. **Deliberately left `supervised`
at task/sprint completion** — reverting to `autonomous` before the
underlying conflict is resolved would re-expose the live duplication
risk on the very next scheduled tick.

**Resolution:** Open. `REQ-SB-71-US-02`'s own 7 tasks and 7 locked ACs
are unaffected and independently verified `Done` (none of them exercise
`thread_match_merge`/the old path) — this finding blocks nothing in this
story, per this project's own established `ESC-022`/`ESC-025`/`ESC-046`/
`ESC-047` precedent ("a real, out-of-scope, root-caused defect discovered
via due-diligence live verification does not block the task that found
it"). The real fix is squarely `architecture.md`'s own already-stated,
not-yet-mandated intent: rewire `process_staged_email`'s own underlying
implementation to compose `capture_raw_thread_messages` +
`synthesize_thread` instead of `pull_and_stage_emails` +
`run_email_capture_pipeline`/`thread_match_merge` (Email Capture
Redesign section, "their own underlying implementation now composes the
two functions above in sequence") — retiring `thread_match_merge` for
real capture, closing this gap by construction, exactly the outcome this
whole redesign was building toward.

**What still needs a human/architect decision:** whether to (a) file a
`/bug` (Area: Logic) batched into a `BUGFIX-NN-US-01` fix story that
rewires `process_staged_email`'s own implementation and formally retires
`thread_match_merge`'s live call site, restoring `email-capture-
pipeline` to `autonomous` once that ships, or (b) leave `email-capture-
pipeline` in `supervised` mode indefinitely until `REQ-SB-71-US-03`
(`SPRINT-062`, the sibling Meeting redesign, already sequenced behind
this sprint) or a dedicated follow-up naturally addresses it — a real
operational-priority call, not decided here.

**Resolving artefact:** _pending_ — recommend `/bug` capture (Area:
Logic) so it can be batched into a `BUGFIX-NN-US-01` fix story. See
`REVIEW-QUEUE.md`.

**Resolution (`/triage`, analyst pass, 2026-08-19):** the operational-
priority call this entry's own "what still needs a human/architect
decision" section named — (a) file a `/bug` batched into a `BUGFIX-NN-
US-01` fix story, or (b) leave `email-capture-pipeline` `supervised`
indefinitely — is now decided: (a). `BUG-026` was captured (Area: Logic,
consolidating this entry and `ESC-050`, same root cause) and batched into
`BUGFIX-05-US-01`, `Draft`, `gate: clear`. This triage pass additionally
re-confirmed, by direct reading of the current live code (not restated
from this entry's own text alone), that `process_staged_email`'s real call
chain (`skill_tools.process_staged_email` →
`email_capture_pipeline.run_email_capture_pipeline` → the compiled
graph's `thread_match_merge` node → `email_classification.
thread_match_merge`) still runs the old path end-to-end exactly as
disclosed here, and that `capture_raw_thread_messages`/`synthesize_thread`
already exist and already work, reachable today only via `app/api/
email_poc_router.py`'s `/poc`-prefixed dev endpoints, never any real Agent
capability. `email-capture-pipeline`'s working mode stays `supervised`
until `BUGFIX-05-US-01` ships and is verified live, per that story's own
Constraints — this entry's protective measure is not undone by this
triage pass alone.

**Resolving artefact:** `BUGFIX-05-US-01`
(`Implementation/UserStories/BUGFIX-05-US-01-email-thread-processing-retires-legacy-thread-match-merge.md`).

**Status:** Resolved

---

## ESC-049: `REQ-SB-71-US-03-T01`'s own mandated dropping of Meeting `subject`/`start`/`end`/`location` from frontmatter breaks `my_day.py::list_calendar_items` for every new-shape Meeting note going forward — 2026-08-18

**Category:** out-of-scope (non-blocking)

**Trigger:** `/implement-sprint SPRINT-062`'s own real, live build of
`REQ-SB-71-US-03-T01`. Direct code reading (not assumed): `app/business/
my_day.py::list_calendar_items` reads a captured Meeting note's own
`subject`/`start` frontmatter fields directly — `frontmatter.get("start",
"")`, then used BOTH as the response's own `"start"` field AND as the
7-day rolling-window filter input (`_within_window(start, ...)`) — and
`frontmatter.get("subject", "")` for the response's own `"subject"`
field. `REQ-SB-71-US-03-T01` (`ADR-048` Decision 5, this story's own
explicit, deliberate, three-times-repeated design: analyst Scenario 1,
architect End-State text, `ADR.md` Decision 5) drops exactly these four
fields from every NEW-shape Meeting note's frontmatter — a genuinely
correct, intentional change for Meeting Capture's own shape, but
`my_day.py` was never updated to match (no task in this story's own `##
Files to Modify` lists `my_day.py` — the decomposer's own task breakdown
does not name this file at all, and this story's own `## Affected
Screens` section names ONLY `meeting-cockpit.html`'s own regression risk
as disclosed, not My Day's).

**Concrete, live-confirmed impact:** for every Meeting note captured
under the NEW shape going forward, `list_calendar_items` will render an
empty `"subject"` — cosmetic — but, far more seriously, `frontmatter.get
("start", "")` will be `""`, and `_within_window("", ...)` returns `False`
unconditionally (its own documented "a missing/empty date value is
treated as outside the window (excluded), not a crash" contract) — so
every NEW-shape Meeting note is silently, permanently EXCLUDED from My
Day's own Calendar tab and its own `summary()` count, regardless of how
recently it was actually captured. This is a real, live, structural
regression to a currently-`Done` capability (`REQ-SB-12-US-02`/
`REQ-SB-22-US-01`), not a hypothetical one — confirmed by direct reading
of both functions' own real code, not merely reasoned abstractly.

**Why not fixed in-scope:** `my_day.py` is not named in any of `REQ-SB-71-
US-03`'s own three tasks' `## Files to Modify` — fixing it here would mean
editing an unanticipated file, a real "unanticipated file required"
MUST-FLAG trigger this role must not improvise past (`Implementation/
Pipeline.md` hard rule 5). This mirrors this SAME story's own sibling
`ESC-048` finding's precedent exactly (a real, disclosed, out-of-scope
regression found via due-diligence direct reading during a `/plan-tasks`
-adjacent redesign, not caused by carelessness, not blocking the task
that found it).

**Resolution:** Open. `REQ-SB-71-US-03-T01`'s own locked `AC-01` and this
story's other 6 locked ACs are unaffected and independently verified real
and live — none of them exercise `my_day.py`. The real fix is
straightforward and well-scoped: `list_calendar_items` needs either (a) a
fallback read path (e.g., derive a display subject/date from the note's
own filename stem / `## History`'s own first entry, for a note lacking
`subject`/`start`), or (b) a dedicated `list_calendar_items`-only
frontmatter field this story's own new shape could still carry
specifically for My Day's own window-filtering need (e.g., a lightweight
`captured_at`/`last_occurrence_at` field, distinct from the raw calendar
logistics this story deliberately drops) — a genuine design choice, not
decided here.

**What still needs a human/architect decision:** whether to (a) file a
`/bug` (Area: Logic) batched into a `BUGFIX-NN-US-01` fix story that adds
a My-Day-specific display/window-filter field or fallback read path to
the new Meeting shape, or (b) treat this as an acceptable, temporary
regression until a dedicated My-Day-refresh story naturally addresses it
— an operational-priority call, not decided here. Unlike `ESC-048`, no
protective mode-flip was available/applicable here (My Day is a read-only
projection, not an Agent capability with a working-mode switch) — the
regression is live starting the moment any new-shape Meeting note is
captured, which already happened multiple times during this same
session's own real verification work.

**Resolving artefact:** _pending_ — recommend `/bug` capture (Area:
Logic) so it can be batched into a `BUGFIX-NN-US-01` fix story.

**Status:** Open

---

## ESC-050: `thread_match_merge`'s still-live, `supervised`-only pipeline already ORPHANS a Thread's `messages/`/`files/` subdirectories for any new-shape Thread — a materially worse failure mode than `ESC-048` disclosed, found while architecting `REQ-SB-72-US-01` — 2026-08-18

**Category:** out-of-scope (non-blocking)

**Trigger:** `/plan-tasks REQ-SB-72-US-01`'s own architect pass (`ADR-049`).
Direct, full-body reading of `email_classification.thread_match_merge`
(lines 191-418), done specifically to scope this story's own reopening of
`resolve_thread_note_path` (`ADR-048` Decision 3), found a second, more
severe failure mode `ESC-048` (2026-08-18, `SPRINT-061`) did not name.

`ESC-048` disclosed that `thread_match_merge`'s own create-vs-update check
(`resolve_thread_note_path`) silently creates a DUPLICATE Thread for a
pre-redesign, FLAT-shape conversation, since the retargeted lookup no
longer finds it. This entry is about the OPPOSITE case: a conversation with
an ALREADY-EXISTING, NEW-shape (`ADR-048`, directory-based) Thread.
`resolve_thread_note_path` DOES find it (both today, via the deterministic
path, and after `ADR-049`, via the frontmatter scan) — but `thread_match_
merge` then proceeds, near the end of its own body, to compute a rename
target via its own still-live legacy `thread_note_path_for(thread_name,
date, conversation_id)` (`ADR-046`'s flat, hash-suffixed filename scheme)
and, when that differs from the Thread's own real current path (which it
almost always will, since one is a flat file and the other lives inside a
directory), calls `rename_thread_note(path, new_path)` — physically moving
the CONCEPT FILE alone out of its own directory onto a flat path, leaving
that directory's own `messages/` (every raw message note) and any `files/`
(companioned attachments) ORPHANED — disconnected from the concept file
that used to sit alongside them, invisible to `synthesize_thread`'s own
`messages/`-directory read from that point on.

**Confirmed to already fire TODAY, independent of `REQ-SB-72-US-01`
shipping:** this is not a new risk `REQ-SB-72-US-01`'s own Thread-rename
Job introduces — direct reading confirms `thread_match_merge` already
computes an incompatible flat rename target for ANY new-shape Thread the
moment it processes a further message in that conversation, regardless of
whether the Librarian has renamed anything. `REQ-SB-72-US-01`'s own rename
work does not cause this defect, but it does mean MORE real Threads
accumulate `messages/`/`files/` content over time that would be orphaned
the moment `thread_match_merge` runs against them.

**Why not fixed in-scope:** `app/business/pipelines/email_capture_
pipeline.py` (the module defining/wiring `thread_match_merge`) is outside
`REQ-SB-72-US-01`'s own `## Files to Modify`/`## Non-Goals` — the story is
explicit that it does not touch this file. `ESC-048` already named the
correct fix (rewire `process_staged_email` onto `capture_raw_thread_
messages`/`synthesize_thread`, retiring `thread_match_merge`'s own live
call site) and left it as an open, human operational-priority call, not
yet resolved. Absorbing that decision here — inside a story whose own scope
never named `email_capture_pipeline.py` — would itself be scope creep
(`Implementation/Pipeline.md` hard rule 5), even at the architect layer.
Mirrors this project's own established `ESC-022`/`ESC-025`/`ESC-046`/
`ESC-048` precedent: a real, out-of-scope, root-caused defect discovered
via due-diligence direct reading does not block the task that found it,
but must be disclosed, not buried.

**Resolution:** Open. Reinforces, does not replace, `ESC-048`'s own still-
open finding — `email-capture-pipeline`'s working mode should stay
`supervised` (never flipped back to `autonomous`) until `ESC-048`'s own
named fix ships; a human could still trigger this pipeline manually while
`supervised`, so the risk remains live, not merely dormant. See `ADR-049`
(`Implementation/Architecture/ADR.md`) Consequences for the full
architectural reasoning.

**What still needs a human/architect decision:** the same open choice
`ESC-048` already named — (a) file a `/bug` (Area: Logic) batched into a
`BUGFIX-NN-US-01` fix story that rewires `process_staged_email`'s own
underlying implementation and formally retires `thread_match_merge`'s live
call site, restoring `email-capture-pipeline` to `autonomous` once that
ships; or (b) leave `email-capture-pipeline` in `supervised` mode
indefinitely until a dedicated follow-up naturally addresses it — a real
operational-priority call, not decided here. Given this entry's own sharper
severity finding (data-integrity corruption, not merely a duplicate note),
recommend treating `ESC-048`'s own fix with higher priority than its
original framing implied.

**Resolving artefact:** _pending_ — recommend `/bug` capture (Area: Logic)
so it can be batched into a `BUGFIX-NN-US-01` fix story that resolves both
`ESC-048` and this entry together (same root cause: `thread_match_merge`'s
own live call site).

**Resolution (`/triage`, analyst pass, 2026-08-19):** resolved together
with `ESC-048`, exactly as this entry's own "what still needs a human/
architect decision" section anticipated. `BUG-026` (Area: Logic) was
captured consolidating BOTH this entry and `ESC-048` under one bug — same
root cause, same fix — and batched into `BUGFIX-05-US-01`, `Draft`,
`gate: clear`. This story's own acceptance scenario carries both this
entry's own orphaning failure mode AND `ESC-048`'s duplication failure
mode as its two `When`/`Then` facets, so neither regression can be marked
closed without the other also being closed. `email-capture-pipeline`
stays `supervised` — per this entry's own severity note, unwinding that
protective measure requires `BUGFIX-05-US-01` to actually ship and be
verified live, not merely be batched.

**Resolving artefact:** `BUGFIX-05-US-01`
(`Implementation/UserStories/BUGFIX-05-US-01-email-thread-processing-retires-legacy-thread-match-merge.md`).

**Status:** Resolved

---

## ESC-051: `write_attachments`'s own `_slugify(..., max_len=80)` truncation silently collapses near-identical, long Outlook `message_id`s onto the SAME attachment directory — found live coding `REQ-SB-72-US-01-T04`'s Files backfill Job — 2026-08-18

**Category:** out-of-scope (non-blocking)

**Trigger:** `/implement-sprint SPRINT-063`, coder pass building/verifying
`REQ-SB-72-US-01-T04` (Files/OKF backfill Job) against the real, live
vault. `backfill_files()`'s own real-attachment count came back
materially higher (121 `(message_id, attachment)` associations) than the
real, on-disk attachment file count (56 files, direct filesystem scan) —
investigated via direct reading rather than assumed a T04-introduced bug.

**Root cause, confirmed by direct reading:** `vault_writer.write_
attachments` (`REQ-SB-71-US-02-T03`, already `Done`, UNCHANGED/reused by
this story per its own Constraints) persists each message's own real
attachment bytes at `Work/Threads/attachments/<slug-of-conversation_id>/
<slug-of-message_id>/<filename>`, where the message-segment directory name
is `_slugify(message_segment, max_len=80)` — a hard 80-character
truncation. Real Outlook `message_id` (EntryID-shaped) values captured
live in this vault run well past 80 characters and, for a message
delivered to multiple recipients/copies of the same real email, differ
from each other ONLY in their final few characters — past the 80-char
truncation point. Three real, distinct raw message notes in the same real
Thread (`Work/Threads/2026-07-28 Azerbaijan Engagement…/messages/*.md`,
`conversation_id=160ECC4CA3630647BB160686DECB8E98`) were confirmed live to
carry three DIFFERENT full `message_id` values that share an IDENTICAL
first-80-character prefix — `_slugify` collapses all three onto the exact
same `attachments/<cid>/<80-char-prefix>/` directory. 16 such collision
groups were confirmed across the real vault's current 66 real
`(message_id, attachment)` pairs.

**Consequence, disclosed not fixed:** this does not corrupt or lose any
real attachment byte content (multiple messages simply read back the SAME
real file, since they resolve to the same directory) — but it means
`T04`'s own Files Backfill Job (and any other real caller of `staged_
attachment_files`) currently produces one SEPARATE `files/<slug>/`
companion PER distinct `message_id` that collides onto a shared attachment
directory, even though the underlying bytes are identical across those
companions — redundant, not lossy or crashing. A worse, latent risk this
same truncation collision opens (not yet observed live, but real given the
mechanism): two DIFFERENT real attachments, from two DIFFERENT messages
whose `message_id`s share an 80-char prefix, with the SAME filename, could
silently overwrite one another at `write_attachments`' own write time —
this project's own standing filename-collision-must-surface, never-
silently-overwrite discipline (`MEMORY.md`) is violated at this one path
construction, though not proven to have actually fired for any real
attachment in this vault today (no evidence of lost real content found).

**Why not fixed in-scope:** `vault_writer.write_attachments`/`_slugify`
(`REQ-SB-71-US-02-T03`, already `Done`) are explicitly UNCHANGED/reused by
`REQ-SB-72-US-01`'s own Constraints ("This story's Files backfill
re-derives that same deterministic location; the rename mechanism (task 1)
does not touch it") — outside this story's own `## Files to Modify`.
Widening `_slugify`'s own `max_len` (or hashing `message_id` instead of
truncating it, mirroring `raw_message_note_path`'s/`meeting_note_filename_
stem`'s own hash-suffix precedent elsewhere in this codebase) is a real,
scoped fix but touches an already-`Done` story's own established
convention — a decision for a dedicated follow-up, not silently absorbed
here. Mirrors this project's own established `ESC-046`/`ESC-048`/`ESC-050`
precedent: a real, out-of-scope, root-caused defect discovered via
due-diligence live verification does not block the task that found it, but
must be disclosed, not buried. `T04`'s own Job itself is NOT broken by
this — its own idempotency contract (re-running never creates a duplicate
companion for the SAME `message_id`) holds exactly as specified; the
redundancy described above is a property of the UPSTREAM directory key,
not a T04 defect.

**Resolution:** Open.

**What still needs a human/architect decision:** whether to (a) file a
`/bug` (Area: Logic) batched into a `BUGFIX-NN-US-01` fix story that
widens/hashes the message-segment slug in `write_attachments`/`staged_
attachment_files` (and, if warranted, a one-time backfill to de-duplicate
any companions this collision already produced); or (b) leave as-is,
since no real attachment content loss has been observed and the redundant-
companion consequence is cosmetic, not corrupting.

**Resolving artefact:** _pending_ — recommend `/bug` capture (Area: Logic).

**Status:** Open

---

## ESC-052: `write_file_companion`'s own `file_slug` convention produces a companion DIRECTORY literally named `*.md` when the original attachment's own filename already ends in `.md` — crashes `vault_indexing.rebuild_index()`'s live scan — found live coding `REQ-SB-72-US-01-T04` — 2026-08-18

**Category:** out-of-scope (non-blocking) — one defensive guard applied
in-scope, root cause left disclosed, not fixed

**Trigger:** `/implement-sprint SPRINT-063`, coder pass verifying `REQ-SB-72-
US-01-T04` live: the freshly-restarted real backend's own scheduled
`run_capture_if_idle` -> `vault_indexing.rebuild_index()` background task
crashed with a real `PermissionError: [Errno 13] Permission denied` trying
to `read_note()` `Work/Threads/2026-08-01 Fw- Project scaffold/files/
0fb3d1c8-project-scaffold.md` — confirmed by direct inspection to be a
DIRECTORY, not a file.

**Root cause, confirmed by direct reading:** a real attachment in this
Thread was itself named `project-scaffold.md` (a Markdown file sent as an
email attachment — a real, plausible case never considered by `REQ-SB-71-
US-02-T07`'s own `file_slug = f"{hash8(message_id)}-{filename}"`
convention). `vault_writer.write_file_companion` (already `Done`, UNCHANGED
by this story per its own Constraint: "Reuses `email_classification.
write_file_companion` UNCHANGED") creates `files_dir = <subfolder>/files/
<slug-of-file_slug>` as the companion's own DIRECTORY — when `filename`
already ends in `.md`, `file_slug` (and therefore the directory's own name)
ends in `.md` too, producing a directory literally named `....md`.
`vault_writer.list_all_note_paths()`'s own `work_root.rglob("*.md")` scan
matches directories whose name ends in `.md`, not only regular files, so
`vault_indexing.rebuild_index()` (and every other real caller of `list_
all_note_paths`) then tries to `read_note()` that DIRECTORY and crashes.
Exposed live by this task's own `backfill_files()` Job companioning a real
attachment with this exact filename shape for the first time — `write_file_
companion` itself is unchanged; this is a pre-existing gap in `REQ-SB-71-
US-02-T07`'s own convention, newly triggered by real content.

**Mitigated in-scope, root cause left disclosed:** `list_all_note_paths()`
(already inside `T04`'s own `## Files to Modify`) gained a defensive
`path.is_file()` guard — a one-line, purely defensive change with ZERO
behavior change for any well-formed note (always a regular file); this
stops the crash for THIS and any future occurrence, letting `rebuild_
index()`/every other real caller simply skip a malformed `.md`-named
directory instead of crashing on it. The ROOT CAUSE — `write_file_
companion`'s own `file_slug` convention not accounting for an attachment
filename that already ends in `.md` — is NOT fixed: `email_classification.
write_file_companion` is outside `T04`'s own `## Files to Modify`, and
`REQ-SB-72-US-01`'s own Constraint requires reusing it UNCHANGED. The one
real, already-existing malformed companion directory (`Work/Threads/2026-
08-01 Fw- Project scaffold/files/0fb3d1c8-project-scaffold.md/`) is left
as-is on disk — its own real content (the original attachment + companion
note, both correctly readable once found by their own real path) is
intact and undamaged, just cosmetically double-`.md`-suffixed; it is now
silently skipped by `list_all_note_paths()`'s own scan rather than crashing
it.

**Confirmed scope:** only 1 real companion directory in the current vault
carries this shape (direct scan of every real `files/` companion
directory under `Work/Threads/`); the underlying condition (an attachment
whose own filename ends in `.md`) will recur for any FUTURE attachment
with this shape, via either `synthesize_thread`'s own going-forward
companioning or `T04`'s own `backfill_files()` re-run.

**Why not fixed further in-scope:** fixing `file_slug`'s own convention
(e.g. stripping/escaping a trailing `.md` before use, mirroring `raw_
message_note_path`'s/`meeting_note_filename_stem`'s own hash-suffix
precedent) touches `email_classification.write_file_companion` itself —
outside every one of this story's own 9 tasks' `## Files to Modify` lists,
and explicitly required to stay UNCHANGED by `T04`'s/the story's own
Constraints. Mirrors this project's own established `ESC-046`/`ESC-048`/
`ESC-050`/`ESC-051` precedent: a real, out-of-scope, root-caused defect
discovered via due-diligence live verification does not block the task
that found it (the defensive `is_file()` guard keeps the live system
healthy in the meantime), but the root cause itself is disclosed, not
silently fixed by improvisation.

**Resolution:** Partially mitigated (crash prevented); root cause open.

**What still needs a human/architect decision:** whether to `/bug` capture
(Area: Logic) a fix to `write_file_companion`'s own `file_slug` convention
(e.g. strip/escape a trailing `.md` from `filename` before composing
`file_slug`, or hash the whole `filename` the way `raw_message_note_path`
already hashes `message_id`) — batched into a `BUGFIX-NN-US-01` fix story
alongside `ESC-051` (same module, same class of slug-construction gap).

**Resolving artefact:** the defensive `list_all_note_paths()` guard, this
session, `src/backend/app/data_access/vault_writer.py` (crash prevention
only — root cause itself _pending_, recommend `/bug` capture).

**Status:** Open (crash mitigated; root cause unresolved)

## ESC-053: `/triage BUG-025` — the bug's own "already shipped once (`REQ-SB-32`), should hold across all three chat surfaces" framing is directly contradicted by `BACKLOG.md`, `Documentation/PRD.md`, and the real frontend code — `REQ-SB-32` was never actually specced or built — 2026-08-19

**Category:** unclear-requirement

**Trigger:** `/triage`'s own analyst pass batching `BUG-022`/`BUG-023`/
`BUG-024`/`BUG-025` into `BUGFIX-04-US-01`. The triage brief and `BUG-025`'s
own `## Bug Details` in `BUGS.md` both frame the rich-text gap as a
regression: "this already shipped once (`REQ-SB-32`, 'Rich Text Rendering
in Agent Chat') and should hold across all three chat surfaces." Per this
project's own standing "confirm via direct reading, not guessed"
discipline, the analyst checked `REQ-SB-32`'s real delivery state before
drafting the fix scenario and found this premise false:
- `BACKLOG.md` row 53: `| REQ-SB-32 | Rich Text Rendering in Agent Chat |
  — | — | — | — |` — no story link, no status, no sprint. Every other row
  in that table carries at minimum a story link or an explicit `Draft`
  status; `REQ-SB-32` carries neither.
- `Documentation/PRD.md`'s own `REQ-SB-32` section carries an explicit,
  unresolved comment: "Raised 2026-08-12, operator-directed... explicitly
  logged as a discussion topic, not scoped or built this pass ('mark it as
  a discussion to avoid going back to this everytime')... Left to
  `/spec`, whenever picked up," and names three genuinely open design
  questions (which markdown subset, which rendering approach/library,
  whether user-sent messages also render as rich text or only agent
  replies).
- Direct reading of the real frontend confirms zero prior implementation:
  `src/frontend/src/features/cockpit/Cockpit.tsx` (line ~135) and
  `src/frontend/src/features/agents-map/AgentDetailPanel.tsx` (line ~775)
  both render `{message.text}` as a bare string with no markdown handling
  of any kind; `src/frontend/package.json` lists exactly `react`,
  `react-dom`, `react-router` as dependencies — no markdown/rich-text
  library exists anywhere in the codebase to have shipped, let alone
  regressed.

`BUG-025`'s own live-observed symptom (raw `**`/`-` markdown syntax
literally renders in all 3 chat surfaces today) is real and not in
dispute — only its characterization as a regression against prior,
working functionality is false. There is no prior working state to have
regressed FROM; this is undelivered net-new work against a requirement
the PRD itself still marks unfinalised/discussion-only.

**Resolution:** `BUGFIX-04-US-01` was still drafted with all 4 requested
scenarios (`status: Draft`, `gate: flagged`) rather than dropping
`BUG-025` from the batch — its own Expected text ("rich text renders as
formatted content") is unambiguous and specable as an observable outcome
regardless of the shipped-vs-never-built discrepancy, and `BUG-022`/
`BUG-023`/`BUG-024` are unaffected, clean, code-confirmed regressions that
should not be blocked behind this one bug's discrepancy. All 4 bugs were
still flipped `Open → In Sprint` in both `BUGS.md` and `BACKLOG.md`'s
`## Bugs` mirror, with `Fixed by: BUGFIX-04-US-01`, per `/triage`'s own
unconditional lifecycle rule. The story's own `## Notes` records that
Scenario 4's fix is net-new capability-building (library choice,
sanitization approach, markdown-subset decision all left open for
`/plan-tasks`), not a small patch, and recommends the human decide whether
`REQ-SB-32`'s own PRD entry should be reconciled (its Draft/discussion
comment resolved, the requirement formally marked satisfied) once
Scenario 4 ships — `BACKLOG.md` will otherwise keep showing `REQ-SB-32` as
unlinked/unbuilt even after this bugfix story closes `BUG-025`.

**Resolving artefact:** `BUGFIX-04-US-01`'s own `## Notes` (this same
reasoning) + `gate_reason`; `REVIEW-QUEUE.md` entry pointing here.
`/plan-tasks`, when it picks up `BUGFIX-04-US-01`, resolves the concrete
rendering-approach/library/scope decisions this entry leaves open.

**Status:** Open (flagged for human review before `/plan-tasks` proceeds
on Scenario 4/`BUG-025`; Scenarios 1-3 are unaffected and may proceed)

## ESC-054: Long-running (30-90+ minute) real-vault housekeeping Jobs, invoked via the real `/poc/librarian-*` endpoints, repeatedly had their backing backend process reclaimed by the coding session's own tool sandbox before completing — 2026-08-19

**Category:** other

**Trigger:** `/implement-sprint SPRINT-063`, resuming `REQ-SB-72-US-01-T06`
through `T09` (a session itself launched to continue after two PRIOR coder
sessions on this same task both died mid-run from infrastructure issues,
per this session's own launch context). `librarian_housekeeping.
populate_thread_related_links()`/`backfill_company_folders()` each iterate
the FULL real Thread corpus (126 real Threads) with one real Compass call
per Thread apiece, no per-call scope/limit — an honest, correct design
(`T06`/`T07`'s own task files), but a genuinely 30-90+ minute real
operation end-to-end at observed live latency (~15-30s/call, sometimes
slower).

Called the real `POST /poc/librarian-populate-related` and `POST /poc/
librarian-backfill-company-folders` endpoints — never a raw script, never
two concurrent calls to the same mutating function (verified before every
further action via live log tailing + process-absence checks, per this
session's own standing constraint) — a total of 4 separate real attempts
across this session. Every single attempt's own client-side `curl` call
timed out first (client-side timeout, not a server error); live log
tailing then confirmed, every time, that the JOB ITSELF was still
genuinely progressing server-side (continuing `HTTP Request: POST
https://api.core42.ai/v1/chat/completions "200 OK"` lines, one per real
Thread processed, with real, verified on-disk `## Related` content
changes and real Pending Approval / Customer-folder creation as
corroborating evidence) — never a crash, never an application-level
error. Three of the four attempts were eventually terminated by an
explicit `[SYSTEM NOTIFICATION]` reporting the backgrounded backend
process itself as `killed`/`stopped` by the coding session's own tool
harness, at roughly 35-55 minutes of that process's own age each time —
independent of request activity (the job was actively succeeding the
moment before each kill). This is the SAME failure class disclosed as
having stopped the two prior coder sessions on this exact task (per this
session's launch context) — now reproduced a third time within a single
session, with the root cause narrowed specifically to this coding
session's own background-process lifecycle management, not the
application code, not the real Compass API (every logged call to it
succeeded), and not a genuinely-orphaned/duplicate mutating call (none
occurred — confirmed by process-state checks before every retry).

**Real, concrete progress was still made honestly, not lost:** `##
Related` population went from 20/126 to 87/126 real Threads across the
session's several attempts; 10 real `propose_librarian_company_link`
Pending Approvals were created (5 approved/declined live to prove the
mechanism, 5 left `pending` for genuine operator review); multiple real
new Customer folders were created. See `REQ-SB-72-US-01-T06`/`T07`'s own
Implementation Logs for the itemized real evidence.

**Resolution:** Not a code defect to fix — `T09`'s own real, persisted
6-hour `agent_schedule_registry` entry (verified live, idempotent across
2 restarts) will complete the remaining backfill autonomously, running on
the OPERATOR'S OWN normally-launched backend process, which is not
subject to this coding session's own tool-sandbox background-process
reclaim policy. `REQ-SB-72-US-01-T09`'s own `AC-11` verification carries a
disclosed, itemized gap (2 of 5 `/poc/librarian-*` endpoints have a
captured live `200`; the other 3 have strong real execution evidence via
logs/on-disk state/Pending-Approval lifecycle but no captured `200` within
this session) — flagged `gate: flagged` on that task rather than silently
treated as fully clean. Recommend, as a future `/plan-tasks` consideration
for the NEXT housekeeping-pipeline story: give bulk Jobs like this an
optional `limit`/chunking parameter so a coder session (or the operator's
own UI) can drive them to completion in smaller, session-safe slices,
rather than requiring one uninterrupted 30-90+ minute call.

**Resolving artefact:** `REQ-SB-72-US-01-T06`/`T07`/`T09`'s own
Implementation Logs (this same reasoning + itemized real evidence);
`REVIEW-QUEUE.md` entry pointing here; `SPRINT-063`'s own retrospective.

**Status:** Open (informational/process finding — the story itself is not
blocked; flagged for human awareness and for `Implementation/Learnings.md`
propagation via the sprint retro, per this project's own "the human
harvests learnings" rule)

---

## ESC-055: `BUGFIX-05-US-01`'s own `AC-01` (flat-shape Thread duplication) is NOT actually closed by `ADR-051`'s composed-function rewire — `resolve_thread_directory`/`list_thread_notes()` itself is blind to pre-redesign, flat `Work/Threads/<name>.md` notes, confirmed by a REAL, already-manifested duplicate in the live vault — found live, `/plan-tasks BUGFIX-05-US-01` step 2 (decomposer) — 2026-08-19

**Category:** adr-deviation

**Trigger:** `/plan-tasks BUGFIX-05-US-01`'s own decomposer pass, locking
`AC`s and building tasks against `ADR-051`. Direct reading of
`vault_writer.list_thread_notes()` (`app/data_access/vault_writer.py`,
lines ~1446-1464) — globs `Work/Threads/*/*.md`, filtered to
`path.parent.name == path.stem` — confirms it can only ever match a
DIRECTORY-shaped Thread (`<slug>/<slug>.md`); a flat, top-level
`Work/Threads/<name>.md` file has zero intermediate directory segments and
can never match this pattern. `resolve_thread_directory()` and
`resolve_thread_note_path()` (the primitives `synthesize_thread`,
`capture_raw_thread_messages`, and `librarian_housekeeping.rename_threads()`
all compose from `list_thread_notes()` alone) inherit the SAME blindness.
`ADR-051`'s own Context/Decision claims `synthesize_thread` "already
internally re-implements `thread_match_merge`'s create-vs-update...
responsibilities... (confirmed by direct reading of `email_
classification.py` lines 461-671 this pass)" — true only for an
ALREADY-directory-shaped Thread; that architect pass did not re-verify
this specifically against a genuinely flat, pre-redesign note — the exact
precondition `BUG-026`'s own duplication facet, and this story's own
`AC-01`, name.

Confirmed live against the real, configured vault (`VAULT_PATH`), not
merely reasoned: 8 real, genuinely flat, pre-redesign
`Work/Threads/<name>.md` notes still exist today (e.g. `RE- Azure-Net New
Revenue Forecast for H2 for AM Updates-2026-07-27-8cd2025b.md`,
`conversation_id: "ED0954959F6F4A4C88F9E2ACA3D7113A"`), alongside 126
already-migrated directory-shaped Threads. Searching for that SAME
`conversation_id` string across `Work/Threads/` finds a SECOND,
directory-shaped Thread already exists for it —
`2026-08-17 Azure-Net New Revenue Forecast for H2 for AM Updates/`, with 4
real raw messages under its own `messages/` (dated 2026-07-28, 07-29,
08-10, 08-17) that rightfully belonged to the SAME conversation as the
original 2026-07-27 flat note. **This is `BUG-026`'s own duplication
failure mode ALREADY live, currently manifested, in the real vault** —
proof, not hypothesis, that `resolve_thread_directory`/`list_thread_
notes()`'s own blindness to flat notes is the TRUE, deeper root cause of
the duplication facet, independent of which composing function
(`thread_match_merge` OR the new `synthesize_thread`/`capture_raw_thread_
messages`) calls it. `ADR-051`'s own rewire (retargeting `process_staged_
email` onto Stage 1/Stage 2) does not touch `vault_writer.py` at all, so
it structurally CANNOT close this — a NEW message arriving for
`ED0954959F6F4A4C88F9E2ACA3D7113A` today, even after `T01`'s own rewire
ships, would still either create a THIRD duplicate or (more likely)
simply update the already-existing 08-17 directory duplicate — never
finding/reuniting with the ORIGINAL 07-27 flat note.

**Resolution:** Open. This story's own `AC-02` (the orphaning facet) is
unaffected — `resolve_thread_note_path` correctly finds an
ALREADY-directory-shaped Thread, and `synthesize_thread` never
computes/calls a rename, so `T01`'s rewire genuinely closes `AC-02` by
construction, confirmed by direct reading, independent of this finding.
Only `AC-01` is blocked. `AC-01` is marked `locked: false` in the story
pending this decision, per `Implementation/Pipeline.md`'s "decomposer is
the sole role that may mark an AC non-locked" rule; the story stays
`Draft`, `gate: flagged`, not `Ready`. `email-capture-pipeline`'s own
working mode stays `supervised` — this finding is, if anything, a
STRONGER reason to keep it that way (the duplication risk is confirmed
still fully live, not merely theoretical, and would remain live even
after `T01` ships).

**What still needs a human/architect decision:** how `resolve_thread_
directory()`/`list_thread_notes()` (a shared primitive with several real
callers — `synthesize_thread`, `capture_raw_thread_messages`,
`librarian_housekeeping.rename_threads()`, `meeting_classification.py`'s
linked-Thread lookups, `list_threads_for_project`) should be extended to
also recognize a flat, pre-redesign `Work/Threads/<name>.md` note for a
given `conversation_id` — genuinely multiple, non-equivalent options, none
decided here: (a) extend `list_thread_notes()`'s own glob to ALSO match
`Work/Threads/*.md` (one level up), treating a flat note's own file as
both its "directory" and its "concept file" for callers that expect
`directory / "messages"` to exist (needs `messages`/`files` subfolder
semantics reconciled against a note that has neither yet); (b) build a
one-time (or on-first-touch) MIGRATION step that renames/restructures a
found flat note into the new 2-level directory shape (mirroring
`librarian_housekeeping.rename_threads()`'s own already-`Accepted` rename
mechanism, but migrating SHAPE, not just the directory's own name) before
`synthesize_thread` ever operates on it; (c) some other design. This is
squarely an architecture-level, shared-multi-caller-interface decision
(`CLAUDE.md`'s own `ADR.md` definition — "architectural choices involving
... structural boundaries") — not a decomposer-level call, and not
something this pass invents or silently absorbs into `T01`'s own
already-`Accepted` `ADR-051` scope.

Also worth the human's attention, separately from the fix itself: the
ALREADY-live duplicate found (`ED0954959F6F4A4C88F9E2ACA3D7113A`, the
07-27 flat note + the 08-17 directory note) is real, current, already-split
conversation content in the operator's own real vault — likely worth a
dedicated manual reconciliation once the underlying primitive gap is
fixed, separate from (and not blocking) this story's own scope, per
`BUGFIX-05-US-01`'s own Non-Goals ("Backfilling/repairing any already-
orphaned Thread from a PAST live `thread_match_merge` run... out of scope
unless a human explicitly asks for a retrofit/repair pass").

**Resolution (architect pass, `/plan-tasks` step 1, 2026-08-19):** a new
`ADR-052` decides the concrete design — option (b) from this entry's own
list above, narrowed to LAZY, on-first-touch migration (never a proactive
bulk pass): `resolve_thread_directory()` gains a second scan tier, tried
only on a miss from the existing directory-shaped scan, that also matches
a flat `Work/Threads/<name>.md` note by its own `conversation_id`
frontmatter and, on a match, migrates it in place to the standard
`thread_directory_paths(conversation_id)` shape (a new `migrate_flat_
thread_to_directory` primitive in `vault_writer.py`) before returning it —
never returning a flat note's own path/parent unmigrated (option (a),
above, was re-examined and confirmed NOT viable as-is: direct reading of
`synthesize_thread`'s own update branch shows `existing_path.parent` would
resolve to the SHARED `Work/Threads/` root for a flat note, not a private
per-Thread directory, so naively widening the glob alone would silently
share one `messages/`/`files/` folder across every unmigrated flat
Thread — worse than the bug being fixed). `list_thread_notes()` itself,
and every one of its OWN callers, is unchanged — each sees a migrated
former-flat-note for free on its own next pass. Full reasoning, every
alternative considered, and every consequence: `ADR-052`.

This is a genuine, disclosed WRITE side effect added to a primitive
`ADR-049` Decision 1 previously characterized as "purely read-only" —
`ADR-049`'s own `Status` line was updated to reflect this narrowing
(Decision 1's framing only; every other Decision in that ADR is
unchanged, unreopened).

**On the ALREADY-live duplicate (this entry's own "also worth the human's
attention" paragraph, above, refined, not reversed):** re-examined against
`ADR-052`'s own design — that migration mechanism deliberately does NOT
retroactively fix `ED0954959F6F4A4C88F9E2ACA3D7113A` (the directory-shaped
scan finds the existing 08-17 duplicate first and returns it, by design —
see `ADR-052` Consequences). This architect pass's own judgement, on
reflection, revises the earlier "likely worth a dedicated manual
reconciliation" framing above: a genuine MERGE of two already-diverged
Thread notes (combining `## Summary`/`## Personal Notes`/`## Actions`/
`messages/`/`files/` content, not just a shape migration) is a capability
this codebase does not have yet, and there may be other, not-yet-surfaced
instances of the same root cause beyond this one confirmed case — a
one-off manual fix here would not catch those. Recommended instead: a new,
separately-scoped backlog item extending the Librarian's own future
housekeeping scope (`REQ-SB-72`) with a systematic "detect and merge
duplicate/split Threads sharing a `conversation_id`" Job, naming this
conversation as its first concrete real case — NOT done inside
`BUGFIX-05-US-01`, consistent with that story's own already-stated
Non-Goals. See `REVIEW-QUEUE.md` for the human's own choice on this point
(accept the deferral, or ask for a one-off reconciliation instead) — this
does not block `BUGFIX-05-US-01` itself, which is fully verifiable without
touching this specific conversation.

**Resolving artefact:** `ADR-052`
(`Implementation/Architecture/ADR.md`); `architecture.md`'s new "Legacy
flat-shape Thread recognition — self-healing migration on first touch"
section. The decomposer re-locks `AC-01` against this concrete design at
the next `/plan-tasks` pass, recommended live-verification target: one of
the 7 flat notes with no known directory-shaped duplicate yet (not
`ED0954959F6F4A4C88F9E2ACA3D7113A`, per the point above). See
`REVIEW-QUEUE.md`.

**Status:** Resolved

---

## ESC-056: `BUGFIX-05-US-01-T04`'s own live verification of `AC-01` found `ADR-052`'s migration mechanism does NOT actually satisfy `AC-01`'s own "preserving its own prior content" clause — a freshly-migrated flat Thread's real, pre-migration `## Summary` text is silently overwritten and lost the FIRST time `synthesize_thread` runs on it — found live, `T04` live verification — 2026-08-19

**Category:** adr-deviation

**Trigger:** `T04`'s own live verification of `AC-01`, run against a real,
clean flat Thread note (`Work/Threads/Compass Alert- Failed API Calls-
2026-07-27-61c91877.md`, `conversation_id
041969487D51E942B77F5CD4A13A6CC2`) via the real `process_staged_email`
capability endpoint. `T03`'s own `migrate_flat_thread_to_directory`
primitive performed EXACTLY as designed — confirmed again here, byte-
identical shape migration, no content touched by that step alone. But the
SAME composed `run_email_capture_pipeline` call (`T01`, `ADR-051`,
unmodified by this finding) immediately calls `synthesize_thread
(conversation_id)` next, in the SAME pipeline tick — and `synthesize_
thread`'s own body (unchanged by `BUGFIX-05-US-01`, per `T01`'s own
Constraint "must NOT modify `email_classification.py`") regenerates
`## Summary` PURELY from whatever raw message notes exist under the
Thread's own (now-migrated) `messages/` directory. `migrate_flat_thread_
to_directory` creates that `messages/` directory EMPTY — it does not, and
per `ADR-052`'s own explicit Decision 1 ("touches only filesystem SHAPE...
never note body or frontmatter content") was never designed to,
back-fill a raw message note capturing the flat note's own PRE-migration
`## Summary` content as history. The observable, real result: a Thread
that had a real, substantive `## Summary` describing its original content
(confirmed directly: "On Jul 27, 2026 at 5:01 PM, an automated status
email from status.notification@compass.core42.ai... reported a 'Failed
API Calls' alert... The per-minute failure rate hit 100.0%...") has that
ENTIRE original summary silently REPLACED by a summary describing ONLY the
new message that triggered the migration ("Single-message thread: a
verification notice from 'BUGFIX-05-US-01-T04 verification'... regarding
AC-01 flat-thread migration check...") — the real, original content is
gone from `## Summary`, not merged, not preserved, not even referenced.
(The legacy `## Transcript` section on the pre-migration note, a dead,
pre-redesign artifact `synthesize_thread` never touches either way, still
shows the one-line original entry — but `## Transcript` is not `## Summary`,
is not part of the new distilled-note shape at all, and is not what
`AC-01`'s own locked wording names.)

This is a genuine gap in `ADR-052`'s own design, not a `T01`/`T03` coding
defect — both tasks did exactly what their own specs said, and both
task-level smoke tests (T01's own composition checks, T03's own five
`resolve_thread_directory` checks) passed cleanly, because NEITHER task's
own test plan happened to chain "migrate a flat note" directly into
"immediately synthesize it," the one sequence that exposes this. `ADR-052`
Decision 1's own "touches only filesystem SHAPE... never note body or
frontmatter content" framing is TRUE of `migrate_flat_thread_to_directory`
in isolation — but the STORY's own locked `AC-01` wording ("the flat Thread
note is migrated in place to the standard... shape, preserving its own
prior content") describes the observable outcome of the WHOLE composed
flow (migration immediately followed by threading, exactly as `T04`'s own
`## Tests` steps 1-4 specify), not `migrate_flat_thread_to_directory` in
isolation — and against that whole-flow standard, real content is lost.

**Real vault impact and repair (immediate, before any further action):**
the coder restored `Compass Alert- Failed API Calls-2026-07-27-61c91877.md`
byte-identical from a pre-test backup (both frontmatter and body,
including the original real `## Summary` text), fully reversing BOTH the
migration and the lossy re-synthesis — the real vault is confirmed back in
its exact pre-`T04` state (`diff`-confirmed byte-identical). No permanent
data loss occurred. This is a deliberate, disclosed departure from `T04`'s
own task-file Constraint ("do NOT revert the migration itself... the
migration itself... is the intended, permanent, correct end state") —
that instruction assumed a successful, content-preserving migration; the
story's own overriding, standing Constraint ("no-data-loss is load-bearing,
not a convenience") takes precedence once a real content-loss defect was
found, per this project's own "no-data-loss overrides task-level
assumptions that predate a real finding" posture (mirrors `BUGFIX-03-
US-01-T02`'s own precedent of prioritizing real-vault safety over a
task's own literal instructions when a live finding changes the picture).

**Resolution:** Open. `AC-01` (duplication facet) is NOT verified passing
as currently designed — `T04` is marked `Blocked` for this reason.
`AC-02` (orphaning facet, `T02`) remains genuinely verified PASS,
unaffected by this finding — `ADR-052`'s migration mechanism is not on
`AC-02`'s own call path (a directory-shaped Thread never triggers the
second scan tier at all). `email-capture-pipeline`'s working mode STAYS
`supervised` — the story's own Constraint requires BOTH `AC-01` AND
`AC-02` verified passing before the flip; that precondition is not met.

**What still needs a human/architect decision:** how the composed
migration-plus-synthesis flow should preserve a freshly-migrated flat
Thread's own real, pre-migration `## Summary` content — genuinely multiple,
non-equivalent options, none decided here: (a) `migrate_flat_thread_to_
directory` additionally back-fills ONE synthetic-but-real raw message note
under the new `messages/` directory, reconstructing it from the flat
note's own pre-migration frontmatter/body (subject from `thread_name`,
body from the pre-migration `## Summary` text or the full pre-migration
body), so `synthesize_thread`'s own next run has real history to
regenerate FROM rather than starting from nothing — mirrors this
project's own "compose around the REAL current file, never silently drop
context" posture, but stretches `create_raw_message_note`'s own "verbatim
real email content" contract to cover a reconstructed entry, which may not
be the right shape; (b) `synthesize_thread` (or a new, narrow variant)
detects a Thread with pre-existing `## Summary` content and NO raw
messages yet, and MERGES (via an additional Compass call, or a simple
prose concatenation) the old `## Summary` with the new message's own
content, rather than regenerating from scratch — changes `synthesize_
thread`'s own contract, which `T01`'s Constraint explicitly protected
("must NOT modify `email_classification.py`") for good reason (a shared,
several-caller function); (c) `migrate_flat_thread_to_directory` copies
the pre-migration `## Summary` text verbatim into the new concept file's
own `## Summary` region UNCONDITIONALLY as part of the migration itself
(not via a raw message, a direct body-preservation step), and `synthesize_
thread`'s own regeneration is changed to APPEND to / update in place
rather than wholesale-replace when a Thread has no raw messages yet but a
non-empty pre-existing `## Summary` — a narrower, more surgical variant of
option (b); (d) some other design. This is squarely an architecture-level
decision about how two already-`Accepted` mechanisms (`ADR-051`'s
composition, `ADR-052`'s migration) interact when chained — not a
decomposer-level call, and not something a coder should invent
unilaterally inside a verification-only task (`Pipeline.md` hard rule 5).

**Also worth the human's attention:** the SAME structural question applies
to `capture_raw_thread_messages`'s own "does the Thread concept file exist
yet" check (`vault_writer.resolve_thread_note_path`) for a Thread that
migrates via a completely organic new-message arrival outside a coder's
own test harness — this is not a test-artifact-only risk; it will recur
for every one of the 7 (now 6, after `T03`'s own smoke test already
migrated one) remaining real flat Threads in the live vault the FIRST time
a genuinely new message arrives for any of them, until this gap is closed.

**Resolution (architect pass, `/plan-tasks` step 1, re-opened, 2026-08-19):**
decided a concrete fix, none of `ESC-056`'s own three candidate options
taken as-is — each was directly evaluated against the real code
(`migrate_flat_thread_to_directory`, `synthesize_thread`,
`read_body_section`/`replace_body_section`, `section_ownership.py`) and
found to have real, disclosed problems (option (a) would corrupt
`first_message`/classification and `message_count` by entering
`messages/`; option (b) doubles Compass cost or produces disjointed
prose; option (c) makes `vault_writer.py` a second, uncoordinated writer
of a `section_ownership.py`-governed header). Adopted instead: a
one-time, self-consuming `pre_migration_summary.md` sidecar file, OUTSIDE
`messages/` — `migrate_flat_thread_to_directory` writes the flat note's
own pre-migration `## Summary` to it verbatim before the move;
`synthesize_thread` folds its content into the SAME existing Compass call
as prior-history grounding, then renames it in place to
`pre_migration_summary.consumed.md` on a successful synthesis only
(archive-not-delete, never fed twice; left untouched on a failed
synthesis, exactly like the Thread's own `## Summary`). Confirmed by
direct reading that `## Summary` is the only section any live code path
puts at risk. Does not reopen `ADR-048`'s "full reconstruction, never a
rolling/incremental delta" design — a narrow, one-time exception for
genuine pre-migration history, not a standing rolling-context mechanism.
Full Decision/Alternatives/Consequences: `ADR-053`
(`Implementation/Architecture/ADR.md`); architecture write-up:
`architecture.md` → "Migration content-preservation — the
`pre_migration_summary.md` sidecar" (new subsection, appended directly
after "Legacy flat-shape Thread recognition — self-healing migration on
first touch"). Story `BUGFIX-05-US-01`'s own `## Notes` records the
concrete fix shape for the decomposer to re-lock `AC-01` against and for
a replacement/amended `T04` to live-verify. `REVIEW-QUEUE.md` entry
written (trigger-3, `ADR-053` created) — does not halt `/plan-tasks`; the
decomposer still runs this same pass.

**Resolving artefact:** `ADR-053` (`Implementation/Architecture/ADR.md`);
`architecture.md`'s new "Migration content-preservation —
the `pre_migration_summary.md` sidecar" section; `BUGFIX-05-US-01`'s own
`## Notes`.

**Status:** Resolved

## ESC-057: `/spec REQ-SB-77` — the requirement's own "Person notes carry a company/<slug> tag only, no real wikilink" premise is directly contradicted by real, already-shipped `people_extraction.py`/`customer_hub_linking.py`/`partner_hub_linking.py` code — 2026-08-19

**Category:** unclear-requirement

**Trigger:** `/spec REQ-SB-77`'s own analyst pass. Per this project's own
standing "ground ACs in real current code, do not guess" discipline, the
analyst read `app/business/people_extraction.py::ensure_person_note`
(already `Done` — `REQ-SB-10`, extended by `REQ-SB-71-US-03-T03`/
`ADR-048` Decision 6, and by `ADR-009`'s Partner-matching addition) before
drafting any scenario, and found the requirement's own premise false as
stated:

- `ensure_person_note` already derives a Person's company from their email
  domain (`derive_company_from_email`), tags it `company/<slug>`
  (`build_person_tags`) — AND, whenever that company already matches a
  known Customer (`find_matching_customer` against
  `vault_writer.list_known_customers()`) or, failing that, a known Partner
  (`find_matching_partner` against `list_known_partners()`, `ADR-009`) —
  ensures that company's hub note exists and writes a real inline
  `**Customer:**`/`**Partner:** [[Hub]]` wikilink to it
  (`customer_hub_linking.link_note_to_customer_hub` /
  `partner_hub_linking.link_note_to_partner_hub`), plus nests a
  newly-created note under `Work/Customers/<slug>/People/` for a Customer
  match.
- This matching is explicitly re-checked on **every** call, not only at
  note creation — the function's own docstring: "a company that later
  becomes a known customer or partner gets its wikilink added retroactively
  on the next call, without touching anything else."
- A retrofit entry point that re-runs this for every real Email sender
  already exists (`retrofit_people_from_emails`) and is already reachable
  via `POST /poc/retrofit-people-from-emails`
  (`app/api/email_poc_router.py:66-68`) — confirmed live, not assumed.

The requirement's premise IS accurate for the real, disclosed residual case
— a company that is NOT (yet) a known Customer or Partner gets its
`company/<slug>` tag and nothing else (there is no hub note yet to link
to), and "no company at all" (personal/free email domain, or no email)
gets neither tag nor link. The operator's own live observation of an
unlinked Person note is real and consistent with this residual case; the
PRD's own blanket "no real wikilink" framing is the part that overstates
it — the mechanism substantially already exists for the matched case, and
the deferral note also cites "in the People Section if no Company is
found," which is likewise already the existing fallback-location behavior
(`person_note_path`'s flat `Work/People/` fallback).

**Resolution:** `REQ-SB-77-US-01` was still drafted (`status: Draft`,
`gate: flagged`) rather than closing the requirement as a documentation-only
correction — the requirement's own real, buildable residual gap (the
retroactive-linking mechanism is reachable only through a `/poc/` route,
with no durable, on-demand or automatic trigger point tied to a company's
Customer/Partner/Affiliate status actually changing) is genuine and
in-scope. The story's own 7 Gherkin scenarios lock the already-correct
OUTCOME (regression coverage for the matched/unmatched/no-company cases)
plus the one new capability (a real, durable reachable trigger for the
retroactive re-link, Scenario 6) at the outcome level, deliberately leaving
the exact trigger mechanism (manual action, automatic hook off
`REQ-SB-76`'s batch-apply, scheduled Librarian pass, or other) open to the
architect — multiple equally-valid shapes exist with no operator direction
narrowing the choice (trigger 8), which is why the story stays `gate:
flagged` rather than auto-advancing.

**Resolving artefact:** `REQ-SB-77-US-01`'s own `## Context`/`## Notes`
(this same finding, restated); `REVIEW-QUEUE.md` entry pointing here, where
the human confirms the scoping choice before/alongside `/plan-tasks`.

**Status:** Open (flagged for human review before `/plan-tasks REQ-SB-77-US-01`
proceeds — see `REVIEW-QUEUE.md`)

## ESC-058: Pending Approvals state file has no concurrent-write locking — N simultaneous `POST /pending-approvals/{id}/approve` calls silently clobber each other (only the last writer survives) — found live, `REQ-SB-78-US-01-T03` live verification — 2026-08-19

**Category:** out-of-scope

**Trigger:** `REQ-SB-78-US-01-T03`'s own live verification of `AC-06`
(bulk-approve). The task's own Tests/Constraints text explicitly allowed
either "sequential or `Promise.all`" for looping the existing single-item
`approvePendingApproval(id)` call across a group's items — the initial
implementation used `Promise.all` (N concurrent HTTP requests). Live
verification against 2 disposable test Pending Approvals sharing one
`action_id` found only ONE of the two records actually resolved to
`approved`; the other stayed `pending` with no error surfaced to the
frontend. Root-caused directly (not assumed): `pending_approval_registry.
create_pending_approval`/`resolve_pending_approval` both call
`vault_writer.save_pending_approvals_state`, a plain
`path.write_text(json.dumps(state))` with no file lock and no
read-modify-write atomicity — under FastAPI/uvicorn's default sync-endpoint
threadpool, two concurrent Approve requests each read the SAME starting
state, mutate their own in-memory copy, then write it back; whichever
request's write lands last silently overwrites the other's mutation. This
is a genuine, pre-existing structural gap in `vault_writer.py`'s own
pending-approvals persistence (not introduced by this story, not specific
to `route_thread_to_project` or any one `action_id`) — reproduced a second
time independently with a wholly different, unmapped `action_id`, ruling
out any per-handler cause.

**Resolution (in-scope, within this task's own explicit "coder's own
implementation choice" latitude):** `REQ-SB-78-US-01-T03`'s own
`handleBulkApprove` was built/kept SEQUENTIAL (`for...of` + `await`, never
`Promise.all`) specifically because of this finding — the task's own
Tests/Constraints already permitted this choice; switching to it is not a
scope deviation, and the live-verified sequential version correctly
resolved 2/2 real disposable test records with zero data loss. The
underlying `vault_writer.py` concurrency gap itself is NOT fixed here — out
of this story's own `## Files to Modify` (a data_access-layer primitive,
not this story's own frontend scope), and every existing single-item
Approve/Decline call site already only ever issues one write at a time
today, so this story's own bulk-approve feature is the FIRST caller in
this codebase that could have exercised the race at all; building it
sequentially removes that risk for this feature without touching the
shared primitive.

**Resolving artefact:** `REQ-SB-78-US-01-T03`'s own Implementation Log
(this same finding, restated, plus the sequential-loop code comment);
`REVIEW-QUEUE.md` entry recommending `/bug` capture for the underlying
`vault_writer.py` primitive gap, since ANY future caller that fires
concurrent writes against the same state-file family (not just Pending
Approvals — the same `path.write_text(json.dumps(...))`-with-no-lock shape
appears across most of `vault_writer.py`'s other state files too) would hit
the identical race.

## ESC-059: `REQ-SB-82-US-04`'s own story file (`status: Draft`, `gate: flagged`, dated 2026-08-25) is stale relative to its real, already-shipped, CHANGELOG-documented scope — found while grounding `REQ-SB-82-US-06`'s own `/spec` pass — 2026-08-31

**Category:** other

**Trigger:** `/spec REQ-SB-82` (drafting `REQ-SB-82-US-06`, per
`Implementation/Plans/2026-08-31-cockpit-live-routing-and-reply-to-message.md`).
Per this project's own standing "ground every technical claim in the real
code, do not trust an input document blindly" discipline, before scoping the
new story the analyst read `app/business/cockpit/chat_turn.py` and
`app/business/cockpit/moderator.py` directly (the same two files the new
plan's own Origin section cites as still purely deterministic/keyword-only)
and found this premise only partially true as of 2026-08-31:

- `moderator.py`'s own module docstring ("no LLM call, no Hermes profile
  involvement") and its deterministic tokenized-overlap `route_question`
  are confirmed CURRENT — the plan's core diagnosis (why "Yes" mis-routes)
  is accurate.
- But `chat_turn.py::send_user_message`/`_dispatch_reply` — live
  per-question routing scoped to the brought-in roster, an explicit
  `@mention` override, a genuine tie-break (falls back to the Research
  Agent, never guesses), a "no real Expert here, suggest one" honest
  system message, a Customer-Section fallback agent, fully async
  background dispatch with an "X is typing…" indicator, and a real
  `reply_to_message_id` threaded-reply mechanism — are ALL already built
  and live, not open questions. `chat_store.py::append_message` already
  gives every message a real `id` and an optional `reply_to_message_id`
  (its own docstring cites this as "(REQ-SB-82-US-04)"). `Cockpit.tsx`
  already renders the threaded "↳ replying to: …" strip for these
  auto-threaded replies. `CHANGELOG.md` has multiple real, dated `feat:
  REQ-SB-82-US-04`/`fix: REQ-SB-82-US-04` entries (e.g. the routing/
  dispatch build, the `@mention` override, the Research-Agent-fallback
  stopword fix) confirming this was built and shipped directly — evidently
  outside the formal `/plan-tasks → /plan-sprints → /implement-sprint`
  pipeline that story's own frontmatter still awaits (its inline code
  comments cite live operator sessions dated 2026-08-26/27/28, all AFTER
  the story file's own `updated: 2026-08-25`).
- The genuinely still-open parts of `REQ-SB-82-US-04`'s own scope are
  narrower than its current file states: the routing-decision MECHANISM
  and tie-break rule are, in fact, decided and shipped (deterministic
  tokenized overlap + explicit tie→Research-Agent fallback); threaded-reply
  RENDERING is, in fact, shipped (`Cockpit.tsx`'s `chat-message-reply-to`).
  What is undecided is only whatever `REQ-SB-82-US-04`'s own remaining,
  never-updated Notes still name as open beyond that (if anything) — a
  question this pass does not resolve, since editing another story is out
  of `/spec`'s own scope for this run.
- This directly affects `REQ-SB-82-US-06`'s own `## Dependencies`: it
  extends the SAME already-shipped `chat_turn.py`/`moderator.py` functions,
  not a not-yet-built mechanism — but it cannot honestly be described as
  "blocked by `REQ-SB-82-US-04`, Done" while that story's own file still
  says `Draft`/`flagged`. `BACKLOG.md`'s `REQ-SB-82` row is equally stale
  ("US-04 still flagged (design/routing decisions remain)").

**Resolution:** Not resolved here — `REQ-SB-82-US-04`'s own story file,
`gate`/`status`, and `BACKLOG.md`'s row are left untouched by this pass
(editing another story's frontmatter/scope is out of this `/spec` run's own
bounds; `Documentation/PRD.md`'s "specs are append-only" rule also cautions
against silently rewriting a flagged story out from under a pending human
review). `REQ-SB-82-US-06` is drafted to depend on the REAL, verified
current state of `chat_turn.py`/`moderator.py` (see its own Context/
Dependencies), not on `REQ-SB-82-US-04` reaching `Done` through the
pipeline. Recommending the human reconcile `REQ-SB-82-US-04`'s own
`status`/`gate`/Notes against its real shipped scope (very likely: much of
it can advance, with only its still-genuinely-open remainder, if any,
staying flagged) as part of resolving `REQ-SB-82-US-06`'s own
`REVIEW-QUEUE.md` entry.

**Resolving artefact:** `REQ-SB-82-US-06`'s own `## Context`/`## Notes`
(this same finding, restated); `REVIEW-QUEUE.md` entry pointing here, where
the human reconciles `REQ-SB-82-US-04`'s own status against its real shipped
scope before/alongside `/plan-tasks REQ-SB-82-US-06`.

**Resolved 2026-08-31:** `REQ-SB-82-US-04`'s `status`/`gate` updated to
`Done`/`clear` with a full `## Reconciliation Note` added to its own file,
citing the same `CHANGELOG.md`/`MEMORY.md` evidence this escalation found.
`BACKLOG.md`'s `REQ-SB-82` row updated to match. Resolving artefact:
`Implementation/UserStories/REQ-SB-82-US-04-meeting-moderator-live-routing-
and-async-research.md`'s own `## Reconciliation Note` (2026-08-31).

**Status:** Resolved

**Status:** Open (recommend `/bug` capture of the underlying
`vault_writer.py` no-locking primitive gap; this story's own `AC-06` is
unaffected/passing via the sequential-loop choice — see `REVIEW-QUEUE.md`)

## ESC-060: The real, runtime `.env` file's Compass credentials are NOT blank — contradicts `ADR-011`'s Consequences and `REQ-SB-82-US-06`'s own Dependencies, both of which checked only `.env.example` — 2026-08-31

**Category:** other

**Trigger:** `REQ-SB-82-US-06-T02`'s own Constraints/Tests block (and this
build pass's own launch instructions) state real Compass `gpt-oss-120b`
credentials are "still blank placeholders" and direct verifying `AC-06`'s
degrade path against "`settings.compass_base_url`/`compass_api_key` left
at their real, currently-blank values." Direct reading of the REAL,
`.env`-backed `Settings()` object `config.py` actually loads at runtime
(`Settings(env_file=".env")`) — not `.env.example`, which genuinely IS
blank — found `COMPASS_BASE_URL`/`COMPASS_API_KEY` are NOT blank:
`src/backend/.env` has a real-looking `COMPASS_BASE_URL=https://
api.core42.ai/v1/chat/completions`, a real-looking `COMPASS_API_KEY`
value, and `COMPASS_MODEL=gpt-5` (not `gpt-oss-120b`, the model name
`ADR-011`'s own title and this story's Context/Dependencies name
throughout). Tracing the source of the wrong premise: `ADR-011`'s own
Consequences paragraph and `REQ-SB-82-US-06`'s own Dependencies section
both cite `.env.example` specifically ("`.env.example`'s
`COMPASS_BASE_URL`/`COMPASS_API_KEY`/`COMPASS_MODEL` are still blank
placeholders") — true for `.env.example` — but neither checked the actual
runtime `.env` file. `T02`'s own Constraints then restated this as "real
credentials... are still blank placeholders," conflating the two files.

**Resolution:** Not resolved here. `T02` does not spend the real `.env`
credentials on its own scoped verification — `AC-06` was independently,
fully verified via a deliberately-unreachable-URL real induced failure
instead (the task's own named Test-step alternative), which keeps `T02`
inside its declared Out-of-Scope boundary ("confirming the real Compass
request/response contract live" is explicitly `T03`/`T05`'s job, not
`T02`'s) — spending a real, possibly-paid/production API key without
explicit human authorization is not this task's call to make
unilaterally. Flagging for the human: (a) whether `COMPASS_MODEL=gpt-5`
is genuinely the intended live Compass `gpt-oss-120b` deployment (the
mismatched model name could mean these are stale/leftover credentials
from an unrelated setup, not necessarily "the real thing" `ADR-011` was
written for) before trusting them for `T03`/`T05`'s own real happy-path
verification; (b) if confirmed genuine, `T03`/`T05` may be able to verify
`REQ-SB-82-US-06-AC-02`'s real happy path live, rather than
"blocked-pending-credentials" as both currently assume.

**Resolving artefact:** Pending human review — no resolving artefact yet.

**Status:** Open

## ESC-061: `REQ-SB-87-US-02-T01`'s own locked `AC-01` cannot be fully closed — `vault_manager.py`'s `create_dynamic_child()` has no way to write a RawMessage's real flat, headerless body, and resolving it needs a file outside this task's own `## Files to Modify` — 2026-09-01

**Category:** out-of-scope

**Trigger:** `REQ-SB-87-US-01-T05`'s own Implementation Log already disclosed
this gap as a `MEMORY.md` Constraint entry (2026-09-01) for this exact task
to resolve: `create_dynamic_child()` can only write a dynamic child's body
via its own declared `"## Header"`-style `sections` list (`body_parts` in
`vault_manager.py` iterates ONLY `child_spec.get("sections", [])`, silently
dropping any caller-supplied `sections` dict key that isn't declared there)
— it has no primitive for a flat, unheaded body string the way
`email-thread-capture/scripts/vault_lib.py::create_raw_message_note` writes
a real RawMessage body today (a plain email body, no `## Header` at all,
confirmed by direct reading, `_write_frontmatter_note(path, frontmatter,
body)`). The real `thread/Template.json` (`REQ-SB-87-US-01-T05`, live vault
copy read directly, 2026-09-01) deliberately declares NO `sections` on its
`messages` dynamic-child entry, so calling `create_dynamic_child()` for a
RawMessage today would create the note with an EMPTY body — a genuine,
real content-loss regression against `AC-01`'s own locked wording ("the
exact same real frontmatter, body-section, and file/folder layout... today"
and the return contract), not an acceptable additive normalization the way
`REQ-SB-87-US-01-T05`'s own empty `## Files`-at-creation judgement call was.

Two ways to actually close this gap, both requiring a file OUTSIDE this
task's own `## Files to Modify`
(`Hermes-Provisioning/skills/vault-rebuild/email-thread-capture/scripts/
ingest_email.py` + `scripts/vault_manager.py` **(new copy)**, i.e. the
DEPLOYED copy, not a place to fork new engine capability per the engine's
own explicit deployment-model docstring: "Editing the engine happens in
exactly ONE place [the canonical `Hermes-Provisioning/shared/
vault_manager.py`], then re-copy" — confirmed live, 82 real deployed copies
today, `REQ-SB-87-US-01-T06`'s own CHANGELOG entry):
1. **Declare a `"Body"` section on the `messages` dynamic-child entry** in
   `.second-brain/data/Templates/thread/Template.json` — a live vault DATA
   file `T05` already authored and closed out, not this task's own file.
2. **Extend `create_dynamic_child()`** (canonical
   `Hermes-Provisioning/shared/vault_manager.py`) to accept a raw,
   unheaded body string, then re-deploy to all 82 real active copies — a
   genuine engine-contract change with system-wide blast radius, an
   architectural decision, not a local coder judgement call, and well
   outside a single migration task's own scope.

Neither was attempted — no parallel hand-rolled write path was built to
route around this (that would silently reinvent what
`REQ-SB-87-US-01-T01`'s own `create_dynamic_child()` primitive already
owns, directly contrary to this task's own launch instructions). Instead:
Thread resolve/create and the `last_message_at` advances-only stamp WERE
migrated onto `vault_manager.py` (fully in-scope, no blocker) and verified
live end-to-end against a real ~100-email scratch-vault sample (51 distinct
Threads, 100 messages, zero regressions vs. a same-sample pre-migration
baseline run — see the task's own Implementation Log for the full live
evidence). RawMessage creation stays on `vault_lib.create_raw_message_note`,
UNCHANGED, preserving its exact real body content — confirmed byte-for-byte
identical across all 100 RawMessage notes and all 156 Person notes between
the baseline and migrated runs.

**Resolution:** Pending human decision on which of the two options above
(or a third) to take before `AC-01`'s own RawMessage-creation clause can be
migrated. `REQ-SB-87-US-02-T01` is marked `Blocked` (not `Done`) —
`AC-01` cannot be verified as fully passing; `AC-02` (idempotency,
advances-only `last_message_at`) DOES verify live and fully passes for the
code as built. `T02`-`T05` (siblings, same story) are not blocked by
this — they don't touch RawMessage creation.

**Resolving artefact:** Pending human review — no resolving artefact yet.

**Status:** Open

---

**Resolution (2026-09-01, same day, operator-directed direct fix -- no
new story, per this project's own `BUG-041` precedent):** a THIRD option,
replacing both of the two named above -- extend `create_dynamic_child()`
(canonical `Hermes-Provisioning/shared/vault_manager.py`) to accept an
optional, flat, unheaded `body: str | None` parameter, mutually exclusive
with `sections`, written to the dynamic child's own body exactly as
given. Preserves the real, current RawMessage body shape exactly (a plain
email body, never a synthetic `## Header`-wrapped document) -- confirmed
against `vault_lib.py::create_raw_message_note`'s own real write shape,
byte-for-byte matched via a direct separator-construction comparison. The
original `sections`-based path is completely unchanged for any other
dynamic-child consumer. New automated tests added
(`Hermes-Provisioning/shared/tests/test_vault_manager.py`, 5 new cases,
56/56 passing overall). All 84 real deployed `vault_manager.py` copies
(11 repo + 73 live Hermes profile) resynced and SHA-256-confirmed
byte-identical to the canonical source post-fix. `ingest_email.py`'s
RawMessage creation then migrated onto the new mode and re-verified live
end-to-end against a fresh real ~100-email scratch-vault sample: 100/100
RawMessage bodies confirmed byte-for-byte identical to a true
pre-migration baseline run, 0 real frontmatter mismatches beyond the
already-`REQ-SB-87-US-01-T05`-accepted additive keys, idempotency and
advances-only `last_message_at` reconfirmed. `REQ-SB-87-US-02-T01` is now
marked `Done` -- both its locked ACs (`AC-01`, `AC-02`) verified with a
real, live positive result. One disclosed, non-blocking scope-internal
judgement call carried forward (the RawMessage filename now follows
`create_dynamic_child()`'s own generic ingestion-date-based naming, not
`vault_lib`'s bespoke received-date-based one -- content/idempotency both
unaffected) -- see the task's own Implementation Log and the new
`REVIEW-QUEUE.md` entry.

**Resolving artefact:** `REQ-SB-87-US-02-T01`'s own completion (this
same-day follow-up coder pass); canonical `Hermes-Provisioning/shared/
vault_manager.py` + `Hermes-Provisioning/skills/vault-rebuild/
email-thread-capture/scripts/ingest_email.py`.

**Status:** Resolved

---

## ESC-062: A sibling task's own real-vault cron cutover (`REQ-SB-87-US-02-T05`) went live DURING `SPRINT-085`'s own real-vault work window, changing state after this sprint's own start-of-session concurrency check — a real, disclosed near-miss with the project's own standing concurrent-write-race constraint, though forensic verification found no actual file collision — 2026-09-02

**Category:** `out-of-scope`

**Trigger:** `SPRINT-085`'s own dispatch explicitly named `REQ-SB-87-US-02-T05`
(the sibling email-thread-capture real-vault retrofit + cron cutover) as a
task that "may still be running in the background as of this dispatch"
and instructed a live cron/process check before either of `SPRINT-085`'s
own two real-vault-touching tasks (`REQ-SB-88-US-01-T03`,
`REQ-SB-88-US-02-T03`). That check was performed and passed at
session start (~13:41 AST): `REQ-SB-87-US-02-T05` was `status: Ready`
(not started), and the `email-delta-capture` cron job was confirmed
`"enabled": false`/`"state": "paused"` via a direct read of the real,
live `cron/jobs.json`. Both of `SPRINT-085`'s own real-vault touches
(`REQ-SB-88-US-01-T03` at ~13:54, `REQ-SB-88-US-02-T03` at ~13:56) ran
against that confirmed-safe state, sequenced one at a time as required.

However, `REQ-SB-87-US-02-T05` was picked up and completed by a
CONCURRENT session sometime between ~13:52 and ~14:22 — discovered only
when `REQ-SB-88-US-01-T04` (this sprint's own cron-provisioning task, a
real-vault-writing action in its own right, not one of the two tasks the
dispatch explicitly named as needing a fresh pre-check) triggered its own
new cron job and a routine post-run sweep of the real vault's own file
mtimes surfaced `email-delta-capture` with `"enabled": true`,
`last_run_at: "2026-09-02T14:22:20"`, `completed: 303` — a state neither
present nor possible at the 13:41 check. Direct confirmation:
`REQ-SB-87-US-02-T05`'s own task file is now `status: Done`.

**A genuine, disclosed process gap on this session's own part:** the
concurrency check was performed once, correctly, before each of the two
tasks the dispatch explicitly named — but NOT re-performed immediately
before `REQ-SB-88-US-01-T04`'s own cron-job creation/trigger, even though
that action is equally real-vault-writing (a new recurring cron job that
calls the migrated `apply_file_review.py` against the real vault).
`REQ-SB-88-US-01-T04` was not one of the two tasks the dispatch named as
needing the check, but in hindsight it should have received the same
fresh pre-check, since "provisioning a live cron job" is exactly the
same class of real-vault-write risk as the two tasks that were checked.

**Forensic verification performed (not assumed):** a direct sweep of
every real vault `.md` file's own mtime across the full real-vault-write
windows of BOTH this sprint's own actions (`REQ-SB-88-US-01-T03`'s single
write at 13:54:06; `REQ-SB-88-US-02-T03`'s own touch produced no write at
all, confirmed idempotent/no-op; `REQ-SB-88-US-01-T04`'s `job5-
summarize-tag-files` cron run's own writes, 14:20:15-14:21:12) against
the sibling job's own real write activity (a burst of new Thread/
RawMessage creation, 14:01:00-14:03:00 — the actual live cutover moment —
then a genuinely empty, no-op `email-delta-capture` tick at 14:22:20,
confirmed zero files touched in that window) found **zero overlapping
write timestamps and zero touched-by-both files** — no actual data
collision or corruption occurred. The two real-vault-writing capabilities
were simultaneously LIVE (both enabled, both capable of firing at any
moment) for a real window, but never actually fired against the same file
at the same moment, by timing alone, not by design.

**Resolution:** No file-level damage found; nothing to repair. This
entry is filed to make the near-miss visible, not to reverse any of
`SPRINT-085`'s own already-verified work (its own tasks' real-vault
checks each independently confirmed correct, byte-identical/expected-diff
results). Filed as a standing process note for future sprints: (1) when
a dispatch names a specific sibling task as a live concurrent-writer
risk, treat EVERY real-vault-writing action in the current sprint as
needing a fresh, immediate pre-check — not just the tasks the dispatch
happened to name explicitly, since a decomposer/product-owner drafting a
sprint ahead of time cannot always enumerate every real-vault-touching
task a later architect/decomposer pass might add (here, `T04`'s own cron
provisioning); (2) consider whether this project needs a stronger
structural safeguard (e.g., a shared, filesystem-level "real vault write
lock" file both this pipeline's own coder role and any live Hermes cron
tick check/respect) rather than relying solely on point-in-time manual
checks, now that multiple concurrent sessions/cron ticks against the same
real vault are a demonstrated, real occurrence, not just a theoretical
risk.

**Resolving artefact:** Pending human decision on whether a structural
concurrency safeguard is warranted; no code change made by this entry
itself — `REQ-SB-88-US-01-T04`'s own real-vault write is independently
confirmed clean (see its own Implementation Log).

**Status:** Open
