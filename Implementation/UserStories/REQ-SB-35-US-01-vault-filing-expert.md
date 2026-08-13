---
id: REQ-SB-35-US-01
title: Vault Filing Expert — methodology-grounded placement/tag decision and write, including proposing genuinely new categories
requirement_ids: [REQ-SB-35]
requirement_section: "REQ-SB-35: Vault Filing Expert"
phase: P1
status: Done
gate: clear
gate_reason: "Built and verified end-to-end 2026-08-12 (/implement-sprint, SPRINT-023) — all 8 locked ACs verified live against the real backend/vault/Compass Provider; ADR-021's own human-review flag is resolved by this successful build, mirroring REQ-SB-20-US-01/REQ-SB-21-US-01's own identical precedent (both closed the same way). See ## Notes."
sprint: SPRINT-023
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-35-US-01 — Vault Filing Expert — methodology-grounded placement/tag decision and write, including proposing genuinely new categories

## Story

**As a** Second Brain user (and every other agent that produces new content)
**I want** a distinct agent, reachable via Hub routing, that decides where
new content belongs in the vault and with what tags — reusing an existing
category when one genuinely fits, or proposing a genuinely new one when it
doesn't — grounded in the vault's own design methodology and taxonomy
conventions, and then writes it, pausing for my explicit approval only when
it proposes a wholly new top-level vault area
**So that** every agent's output lands in a consistent, correctly-tagged,
correctly-connected place without each agent inventing its own placement
logic, the vault's structure grows the same deliberate way a human curator
would grow it, and I keep a meaningful say over the rare, structurally
bigger decision (a new top-level area) without being pulled into every
ordinary filing decision

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-35: Vault Filing Expert* — "A
  dedicated agent capability that, given new content another agent has
  produced (e.g. research output), determines where it belongs in the
  vault and with what tags — consistent with the vault's existing design
  methodology (`Documentation/References/beyond-the-second-brain-
  methodology.md`) and taxonomy conventions (tags for multidimensional
  attributes, folders for single-home entities, per `ADR-004`) — and then
  writes it. The decision is not limited to already-existing categories:
  when the content genuinely doesn't fit anywhere that already exists, the
  Vault Filing Expert can propose and create a new category/folder,
  following the same 'read what's already there, let the model propose new
  values' pattern this project already applies to `kind`/`customer`
  (`Implementation/Learnings.md`) rather than being limited to a fixed enum
  decided in advance. Other agents consult this capability before filing
  new content rather than each agent inventing its own placement/tagging
  logic." Acceptance: "Given new content to file, the Vault Filing Expert
  determines a vault location and tags consistent with the vault's
  existing design methodology and taxonomy conventions, and writes the
  content there; when the content doesn't fit any existing category, the
  Vault Filing Expert can identify and use a genuinely new one instead of
  forcing a stretch-fit into something that already exists; other agents
  that produce new content route it through this capability rather than
  deciding placement themselves."
- **History of this requirement's own scope correction.** REQ-SB-35 was
  originally drafted alongside a sibling `REQ-SB-34` ("Tech Knowledge
  Area") that prescribed a new, fixed top-level "Tech" vault area. One
  exchange later the same day the operator corrected this directly: "The
  Tech Folder is just an Example the Vault Expert should follow the
  Guidelines we had in the book in deciding where to store stuff — may be
  it's just a research or a new Category we don't know of yet." `REQ-SB-34`
  was withdrawn as a result (its ID retired, not reused) and its real
  intent folded into *this* requirement's own Acceptance text.
- **Resolved 2026-08-12, operator-directed, quoted verbatim ("This is an
  Agent"):** the Vault Filing Expert is a **distinct agent in the
  registry, reached via `REQ-SB-20`'s Hub routing like any other
  cross-Section request** — not a shared skill (`REQ-SB-27`'s pattern).
  This settles the requirement's own previously-open question (1) — "the
  operator's own phrasing ('Ask my Vault Expert') suggests a distinct
  agent" was the correct reading. `REQ-SB-20-US-01`'s Hub-to-Hub
  cross-Section routing is now a firm, real dependency (see `##
  Dependencies`), not an "if built as a routable agent" hedge.
- **Resolved by direct precedent, not a fresh guess (unchanged from the
  original spec pass):** *mechanically, how it applies "the book's
  guidelines" to a live placement decision* — grounded in both (a) the
  methodology document (`Documentation/References/beyond-the-second-brain-
  methodology.md`) as instructional grounding text, mirroring
  `REQ-SB-33-US-01`'s own already-`Done` system-prompt-grounding
  precedent, and (b) real, live inspection of the vault's actual current
  structure via the already-built MCP read tools (`app/business/
  vault_query_tools.py`'s `list_known_customers`/`list_known_kinds`/
  `list_known_partners`, extendable) — not a static hardcoded rules table
  alone and not pure LLM improvisation either.
- **Resolved 2026-08-12, operator-directed — the new-top-level-area
  governance question, quoted verbatim:** "a tag or subfolder within an
  existing area proceeds autonomously, same as the rest of `REQ-SB-36`'s
  chain; but proposing a wholly new top-level vault area pauses for the
  operator's explicit approval first — a scoped exception to `REQ-SB-36`'s
  own 'fully autonomous end-to-end' resolution, reusing `REQ-21`'s
  existing Supervised-mode machinery for just this one action type rather
  than inventing a new approval mechanism." This is a genuine **two-tier**
  placement-autonomy model, not a uniform one:
  - **Tier 1 — ordinary placement (existing category, or a new tag/
    subfolder within an already-existing top-level area):** proceeds
    autonomously, never pauses.
  - **Tier 2 — proposing a genuinely new TOP-LEVEL vault area:** pauses
    for the operator's explicit approval before the new area is created or
    the content is written, reusing the exact Pending-Approval workflow
    store/Approve-Decline mechanism `REQ-SB-21-US-01`/`ADR-020` already
    built for Supervised-mode mutating actions.
  - **This is a scoped exception applied to one specific action type
    (new-top-level-area creation), not a change to the Vault Filing Expert
    agent's own general working-mode setting.** The operator's own words
    ("reusing... machinery... for just this one action type") are explicit
    that this is not "set the whole agent to Supervised" — doing so would
    incorrectly gate Tier 1's ordinary, always-autonomous placements too
    (per `ADR-020`'s own Supervised-mode semantics, which gate an agent's
    *mutating actions* uniformly once set). Instead, this action type
    (`propose_new_top_level_area`, naming left to `/plan-tasks`) always
    creates a Pending-Approval record and waits, **regardless of the
    agent's own configured working mode** — the same way `REQ-SB-36`'s own
    "fully autonomous end-to-end... except the one new-top-level-vault-area
    exception" framing describes it: a requirement-level carve-out, not a
    working-mode toggle.
- **Resolved by synthesis of two other requirements' own explicit texts,
  unchanged from the original spec pass — what happens on genuine
  uncertainty:** `REQ-SB-36`'s own text requires the chain to complete
  "without requiring approval at any step" (Tier 1 cases), and this
  requirement's own breadcrumb relates it to `REQ-SB-33`'s honesty/
  grounding standard. Reconciling both: for a **Tier 1** decision the
  Vault Filing Expert always proceeds and writes (never silently blocks or
  waits for a human), but when genuinely uncertain, it discloses that
  uncertainty honestly in what it writes, rather than presenting a guessed
  placement as a confident, settled decision (Scenario 6, below). **This
  uncertainty-disclosure axis is independent of the Tier-1/Tier-2 axis
  above** — confidence level never exempts a genuinely new top-level area
  from Tier 2's approval gate, and a confident Tier-1 decision never pauses
  for approval regardless of how novel the specific tag/subfolder is.
- **Distinct from `REQ-SB-29` (Agent-to-Tag/Folder Scoping)** — that
  requirement bounds what slice of the vault an agent can *read*; this
  requirement is about correctly deciding where *new* content should be
  *written*, a different concern the operator named separately.
- **Standing tags-and-wikilinks rule applies (`MEMORY.md`, operator
  directive):** every note-type schema must define both tags AND
  wikilinks, and every note that *references* another vault entity must
  carry an actual `[[wikilink]]` to that entity's own note, not just an
  identifying frontmatter field — checked in both directions. Whatever the
  Vault Filing Expert writes must satisfy this standing constraint.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first
(Tier 1, existing category), then the Tier-1/Tier-2 split with its
approval-gated exception and decline handling, then methodology-grounding/
honesty, then the "other agents consult this" and non-destructive-write
guarantees. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: Filing content that fits an existing category (Tier 1 — autonomous)

```gherkin
Given the Vault Filing Expert is consulted with new content (e.g. research
    output) produced by another agent
  And an existing vault category genuinely fits the content
When the Vault Filing Expert determines placement
Then it selects that existing category
  And it determines tags consistent with the vault's existing taxonomy
    conventions (tags for multidimensional attributes, folders for
    single-home entities, per ADR-004)
  And it writes the content to the determined location with the
    determined tags, without pausing for approval
```
<!-- AC-ID: REQ-SB-35-US-01-AC-01 -->

### Scenario 2: Filing content that needs a new tag or subfolder within an existing top-level area (Tier 1 — autonomous)

```gherkin
Given the Vault Filing Expert is consulted with new content that does not
    genuinely fit any existing tag/subfolder combination, but the
    containing top-level vault area itself already exists
When the Vault Filing Expert determines placement
Then it proposes and creates the new tag/subfolder within that existing
    top-level area, without pausing for approval — consistent with
    REQ-SB-36's autonomous chain
  And it writes the content there with tags consistent with the vault's
    taxonomy conventions
  And the new tag/subfolder is discoverable the same way existing
    categories already are (e.g. via a vault-derived listing, mirroring
    list_known_kinds/list_known_customers)
```
<!-- AC-ID: REQ-SB-35-US-01-AC-02 -->

### Scenario 3: Proposing a genuinely new top-level vault area pauses for explicit operator approval (Tier 2)

```gherkin
Given the Vault Filing Expert determines that the content genuinely does
    not fit within any existing top-level vault area
When it proposes creating a wholly new top-level vault area
Then it does not create the new area or write the content immediately
  And it raises a Pending-Approval request (reusing REQ-SB-21/ADR-020's
    existing Supervised-mode workflow store, applied to this one action
    type regardless of the Vault Filing Expert's own configured working
    mode) describing the proposed new area and the content awaiting it
  And the content is written, and the new area created, only after the
    operator explicitly approves the request
```
<!-- AC-ID: REQ-SB-35-US-01-AC-03 -->

### Scenario 4: A declined new-top-level-area proposal does not silently lose or misfile the content

```gherkin
Given a pending new-top-level-vault-area proposal (Scenario 3) exists
When the operator declines it
Then the content is not filed under the declined area
  And the pending request is honestly recorded as declined, mirroring
    REQ-SB-21/ADR-020's own existing decline handling — not silently
    retried under a fabricated alternative location, and not silently
    discarded without record
```
<!-- AC-ID: REQ-SB-35-US-01-AC-04 -->

### Scenario 5: Placement and tagging are grounded in the vault's documented design methodology, not an ad hoc guess

```gherkin
Given the Vault Filing Expert is determining where new content belongs
When it reasons about placement and tags
Then its reasoning is grounded in the vault's documented design
    methodology (Documentation/References/beyond-the-second-brain-
    methodology.md) and its existing taxonomy conventions
  And the resulting tags/wikilinks satisfy the standing tags-and-wikilinks
    rule — the written note both carries the correct tags and links out to
    every vault entity it references, not just an identifying field
```
<!-- AC-ID: REQ-SB-35-US-01-AC-05 -->

### Scenario 6: Genuine uncertainty is disclosed honestly, never presented as confident

```gherkin
Given the Vault Filing Expert cannot confidently determine the correct
    Tier-1 placement even after reasoning from the methodology and the
    vault's existing structure
When it still proceeds to file the content under Tier 1 (never pausing for
    approval for an ordinary placement)
Then it honestly records its own uncertainty in what it writes (e.g. a
    visible low-confidence marker), rather than presenting a guessed
    placement as a settled, confident decision
```
<!-- AC-ID: REQ-SB-35-US-01-AC-06 -->

### Scenario 7: Other agents consult the Vault Filing Expert instead of inventing their own placement logic

```gherkin
Given another agent has produced new content it needs to file into the
    vault
When that agent needs to determine where the content belongs
Then it consults the Vault Filing Expert (via REQ-SB-20's Hub routing)
    rather than applying its own ad hoc placement rules
  And the content is written through the Vault Filing Expert's own write
    step, not a separate write path the calling agent implements itself
```
<!-- AC-ID: REQ-SB-35-US-01-AC-07 -->

### Scenario 8: Filing does not corrupt or silently overwrite existing content

```gherkin
Given the vault already has content at or near the determined location
    (e.g. an existing hub note, or other notes already tagged with the
    same category)
When the Vault Filing Expert writes the new content
Then it does not overwrite or corrupt any existing note's own content
  And the new content is added additively — a new note, or a well-formed
    insertion into an existing note — consistent with this project's
    existing living-document/insert-if-missing conventions
```
<!-- AC-ID: REQ-SB-35-US-01-AC-08 -->

## Affected Screens

- **None new.** As a distinct registry agent, the Vault Filing Expert
  composes into the already-approved Agent Settings/Actions/Chat/History
  panel shape (`html-prototype/agents-map.html`) exactly like any existing
  agent — that panel already renders generically from `agent_registry.py`'s
  own per-agent data, not hardcoded per agent. Tier 2's approval-gated
  behaviour (Scenario 3/4) reuses the already-approved Pending Approvals
  surface (`html-prototype/my-day-approvals.html`, its own My Day card,
  and Meeting Capture's existing `.chat-proposal` card pattern —
  approved 2026-08-12 for `REQ-SB-21-US-01`) as another entry in that same
  generic approval list — no new visual concept required. Since Affected
  Screens = None, the mandatory prototype-reconciliation rule does not
  itself force a `net-new-design-needed` flag for this story.

## Dependencies

- **Blocked by:** `REQ-SB-20-US-01` (`status: Ready`, not yet `Done`/
  built) — the Vault Filing Expert is confirmed to be a distinct agent
  reached via this story's own Hub-to-Hub cross-Section routing mechanism;
  not satisfied yet as of this spec pass.
- **Blocked by (Tier 2 only):** `REQ-SB-21-US-01`/`ADR-020` (Done) — the
  Pending-Approval workflow store/Approve-Decline mechanism Scenario 3/4
  reuse for the one new-top-level-area exception. Already `Done`, so this
  dependency is satisfied — real composition work at `/plan-tasks`, not a
  blocker.
- **Related to:** `ADR-004` — the tag-for-multidimensional/folder-for-
  single-home convention this story's placement decisions must stay
  consistent with.
- **Related to:** `Documentation/References/beyond-the-second-brain-
  methodology.md` — the design-methodology grounding text this story's
  reasoning draws on.
- **Related to:** `REQ-SB-33-US-01` (Done) — the honesty/grounding standard
  this story extends from conversational replies to placement *decisions*
  specifically (Scenario 6).
- **Related to:** `REQ-SB-36-US-02` — the end-to-end delegated-research
  bootstrapping chain that consults this capability as its own final hop
  (that story's own scope, not built here); its own Scenario reflecting
  the Tier-2 pause composes directly with Scenario 3/4 here.
- **External:** none new.

## Constraints

- **The Vault Filing Expert is a distinct agent in the registry, reached
  via `REQ-SB-20`'s Hub-to-Hub cross-Section routing** — not a shared
  skill. Confirmed, not left open.
- Grounded in `Documentation/References/beyond-the-second-brain-
  methodology.md` plus `ADR-004`'s tag/folder conventions, plus real, live
  inspection of the vault's actual current structure via the already-built
  MCP read tools — never a hardcoded, exhaustive enum of allowed
  destinations.
- New-category proposal follows the "design for the extensibility point,
  not the enum" pattern (`Implementation/Learnings.md`).
- **Two-tier placement autonomy (operator-resolved, confirmed):** an
  existing category, or a new tag/subfolder within an existing top-level
  area, proceeds autonomously (Tier 1); proposing a genuinely new
  top-level vault area pauses for explicit operator approval (Tier 2),
  reusing `REQ-SB-21`/`ADR-020`'s existing Pending-Approval machinery for
  this one action type specifically — **not** a change to the agent's own
  general working-mode assignment (see Context).
- **Never fabricate confidence in a placement decision** (extends
  `REQ-SB-33-US-01`'s honesty standard) — genuine uncertainty in a Tier-1
  decision must be disclosed in what is written, never hidden behind a
  confidently-stated guess; this is independent of, and never a substitute
  for, Tier 2's own mandatory approval gate.
- The standing tags-and-wikilinks rule (`MEMORY.md`) applies to whatever
  this capability writes, in both directions.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-35-US-01-T01 | backend | New `"vault-filing-expert"` registry agent entry (`agent_registry.py`, data only) + persisted Hub-routing keyword assignment | `business/agent_registry.py` | `REQ-SB-35-US-01-T01-vault-filing-expert-agent-registry-entry.md` |
| REQ-SB-35-US-01-T02 | backend | New `vault_filing_expert.py` — `determine_placement_and_file`, Tier-1 write path, uncertainty marker, collision-safe filenames | `business/vault_filing_expert.py` | `REQ-SB-35-US-01-T02-vault-filing-expert-tier-1-placement-and-write.md` |
| REQ-SB-35-US-01-T03 | backend | Tier-2 resolution — `finalize_new_top_level_area`, `pending_approval_registry.py`'s additive `payload` field, `pending_approvals_router.py`'s `_APPROVAL_HANDLERS` dispatch entry | `business/vault_filing_expert.py`, `business/pending_approval_registry.py`, `api/pending_approvals_router.py` | `REQ-SB-35-US-01-T03-tier-2-approval-resolution.md` |

`depends_on` graph (acyclic): `T01: [REQ-SB-20-US-01-T02]`,
`T02: [REQ-SB-35-US-01-T01, REQ-SB-20-US-01-T05]`,
`T03: [REQ-SB-35-US-01-T02, REQ-SB-21-US-01-T03, REQ-SB-21-US-01-T06]`. Two
real cross-story edges: `REQ-SB-20-US-01-T02`/`T05` (`agent_keywords.py`,
`route_cross_section_request` — Hub-routing composition, Scenario 7) and
`REQ-SB-21-US-01-T03`/`T06` (the Pending-Approvals store + its HTTP
surface — Tier 2, per this story's own ADR-021 finding and the guidance
recorded in `REQ-SB-21-US-01`'s own `## Notes`). All four target tasks are
real, `status: Ready` files — no placeholder/fabricated task id.

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — still manual-mode, per project's own current verification-mode default; every locked AC verified live against the real backend/vault
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **`REQ-SB-36`'s own end-to-end delegation chain and its Compass pilot**
  — a separate story (`REQ-SB-36-US-02`), which consumes this capability
  but is not built here.
- **The Research Expert's own information-gathering mechanism** (web
  search, document ingestion) — separate stories/requirements
  (`REQ-SB-36-US-01`, `REQ-SB-28`), not built here.
- **Any UI** — no new screen region required (see `## Affected Screens`).
- **Automatic enforcement of any not-yet-public/visibility marker** on
  filed content — this requirement's own Acceptance text does not name
  this; if a future requirement introduces such a marker, enforcing it is
  that requirement's own scope.
- **A general-purpose working-mode toggle for Tier 2** — the approval gate
  is a fixed, requirement-level exception for the new-top-level-area
  action type specifically, not a configurable per-agent setting exposed
  anywhere.

## Notes

**Prototype parity:** not applicable — this story ships zero new UI (see
`## Affected Screens`); no `html-prototype/` screen needs reconciliation.

**Why `gate: clear` — re-checked against every MUST-FLAG trigger, not
assumed:**

1. **No remaining material assumption.** Both of this story's previously
   open, genuinely forkable questions — the placement mechanism (agent vs.
   skill) and the new-top-level-area governance question — are now
   resolved by direct operator decision, quoted verbatim in Context. The
   two remaining resolved-by-precedent points (methodology+live-inspection
   grounding; uncertainty-disclosure synthesis) were already defensible,
   singular, non-forking readings at the original spec pass and remain so.
2. `REQ-SB-35` is not marked `<!-- Draft -->`/unfinalised — it carries a
   "Scope resolved" breadcrumb whose own named sub-questions are now all
   resolved. Trigger 2 does not apply.
3. N/A directly (architect/ADR trigger) — though `/plan-tasks` should
   expect real, new architecture work: a new agent-registry entry, its
   Hub-routing composition, and wiring Tier 2's approval gate onto the
   existing Pending-Approval mechanism for one specific action type. Not a
   blocker for this analyst pass.
4. No new `ESCALATIONS.md` entry opened by this pass — this pass instead
   **resolves** `ESC-015`, naming this story's own 2026-08-12 update as
   the resolving artefact (see `ESCALATIONS.md`).
5. Not oversized — one story, comparable to `REQ-SB-27-US-01`'s own scope;
   no cross-sprint dependency edge had to be introduced by this analyst
   pass (`REQ-SB-20-US-01`'s own not-yet-`Done` status is recorded plainly
   in `## Dependencies`, the same way `REQ-SB-20-US-01` itself recorded its
   own then-unmet dependency on `REQ-SB-18-US-01` without that alone
   driving its gate).
6. N/A (coder trigger).
7. **The prior contradiction/tension is resolved, not merely noted.** The
   operator's own explicit new-top-level-area resolution directly
   reconciles what was previously a real, named tension between this
   requirement's own governance concern and `REQ-SB-36`'s blanket
   "no approval at any step" — the two-tier model *is* the reconciliation.
8. **No remaining multiple-equally-valid-options fork.** The placement
   mechanism has one confirmed answer (distinct agent); the governance
   question has one confirmed answer (two-tier, Tier-2 approval-gated).

`gate: clear` 2026-08-12. `REVIEW-QUEUE.md`'s combined entry for this
story is updated to reflect resolution. `ESCALATIONS.md` → `ESC-015`
flipped to `Resolved`, naming this update as the resolving artefact. This
story is ready for `/plan-tasks`.

**Architecture pass (2026-08-12, `/plan-tasks` step 1 — architect).**
`ADR-021` written (new, appended to `Implementation/Architecture/ADR.md`):
a new registry agent, `"vault-filing-expert"` (plain `agent_registry.py`
entry, `ADR-011` point 2 unaffected), reached exclusively via `ADR-017`'s
already-real `graph.route_cross_section_request(...)`; a new
`app/business/vault_filing_expert.py` whose `determine_placement_and_file(
content, source_description, requesting_agent_id)` pre-fetches
`list_known_kinds()`/`list_known_customers()`/`list_known_partners()`
deterministically, issues one `model_factory.resolve_agent_model(
"vault-filing-expert")` completion grounded in `beyond-the-second-brain-
methodology.md` for a structured placement decision, writes Tier 1
immediately via the already-fully-generic `vault_writer.write_note()`
(re-checking `is_new_top_level_area` against `list_known_kinds()` in
Python, never trusting the model's boolean alone), and — for Tier 2 —
unconditionally calls `pending_approval_registry.create_pending_approval(
...)`, bypassing the working-mode gate **by construction** (this code path
never reaches `agents_router.py::_invoke_action`'s funnel at all), per the
operator's own "not a change to the agent's own general working-mode
assignment" framing. `ADR-018`'s `agent_pending_approvals.json` schema
(unedited by `ADR-020`) gains one additive `"payload"` field; the Approve
path gains a new `_APPROVAL_HANDLERS` dispatch table resolving to
`vault_filing_expert.finalize_new_top_level_area(payload)`. Full reasoning:
`Implementation/Architecture/ADR.md` → `ADR-021`; `architecture.md` →
"Vault Filing Expert — placement decision, Tier-1 write, Tier-2 approval
override."

**A real, load-bearing finding, not silently patched:** this story's own
`## Dependencies` above states `REQ-SB-21-US-01`/`ADR-020` is "(Done)...
Already `Done`, so this dependency is satisfied." Direct inspection of
`Implementation/UserStories/REQ-SB-21-US-01-agent-working-modes.md` during
this pass found this **false** — that story is `status: Draft`, `gate:
flagged`; its decomposer has not re-run since `ADR-020` corrected
`ADR-018`, and zero of its 8 tasks have been built. Direct inspection of
the real `src/backend` source tree confirms: no `app/business/
pending_approval_registry.py`, no `app/business/working_mode_registry.py`,
no `app/api/pending_approvals_router.py` exist anywhere. Recorded as
`ESCALATIONS.md` → `ESC-017` (`Open`), plus a `REVIEW-QUEUE.md` pointer —
not silently asserted satisfied, mirroring `ESC-011`'s own precedent for a
real cross-story dependency that cannot yet be wired to a real task id.
**Concretely, this means:** Scenarios 1, 2, 5, 6, 7, 8 (Tier 1 — no
Pending-Approvals dependency at all) have no blocker and can be
decomposed/built independently; Scenarios 3, 4 (Tier 2) have a real
blocking prerequisite on `REQ-SB-21-US-01` actually shipping — the
decomposer's own next pass should individually flag whichever task(s)
implement Tier 2's approval-creation/resolution with `depends_on: []` and
an explicit "blocked, do not start" note, per `ESC-011`'s own established
resolution shape, rather than fabricate a task-id reference or silently
build against code that does not exist.

**Architecture scope (bounds the decomposer/coder for this story):**
`Implementation/Architecture/architecture.md` → "Vault Filing Expert —
placement decision, Tier-1 write, Tier-2 approval override" and "Section-
Hub cross-Section routing — keyword storage & routing-node mechanism" (for
`route_cross_section_request`'s existing shape this story's Scenario 7
composes with, read-only). Concretely: `app/business/agent_registry.py`
(one new agent entry, data only), `app/business/vault_filing_expert.py`
(new), `app/business/agent_orchestration/model_factory.py`
(read-only composition, unmodified), `app/data_access/vault_writer.py`
(`write_note` reused as-is; no new low-level primitive required for Tier 1),
`Documentation/References/beyond-the-second-brain-methodology.md`
(read-only grounding text). Tier 2 additionally touches
`app/business/pending_approval_registry.py` (extends `ADR-018`'s schema
with the additive `payload` field — real code not yet built, see the
finding above) and `app/api/pending_approvals_router.py` (new
`_APPROVAL_HANDLERS` dispatch entry). Full reasoning: `Implementation/
Architecture/ADR.md` → `ADR-021`.

Gate stays `flagged` per this project's own convention — the decomposer
still runs in this same `/plan-tasks` pass (Pipeline.md's "do NOT halt the
stage" rule); the human reviews `ADR-021` and the resulting tasks together.
A `REVIEW-QUEUE.md` pointer has been added.

**Decomposition pass (2026-08-12, `/plan-tasks` step 2 — decomposer,
resolves `ESCALATIONS.md` → `ESC-017`'s "wire the real ids in" step for
this story).** All 8 untagged Gherkin scenarios tightened for buildability
(wording only — no scenario weakened, omitted, or deleted) and locked as
`REQ-SB-35-US-01-AC-01` through `AC-08`, each carrying its trailing
`<!-- AC-ID: ... -->` tag. 3 tasks created at the flat `Implementation/
Tasks/` root:

- **`T01`** — the new `"vault-filing-expert"` registry agent entry
  (`agent_registry.py`, data only, `ADR-011` point 2 unaffected) plus a
  real, persisted keyword assignment (via `agent_keywords.
  set_agent_keywords`, not reverted — this agent needs real, standing
  keywords for Scenario 7's Hub-routing composition to work in production,
  unlike a task's own throwaway verification fixture) — depends on
  `REQ-SB-20-US-01-T02` (`agent_keywords.py`, not yet built).
- **`T02`** — `vault_filing_expert.py`'s `determine_placement_and_file`,
  covering Tier 1 in full (`AC-01`, `AC-02`, `AC-05`, `AC-06`, `AC-08`) and
  the Hub-routing composition check (`AC-07`) — depends on `T01` and
  `REQ-SB-20-US-01-T05` (`route_cross_section_request`, not yet built).
  **A genuine risk not silently left implicit:** the Tier-2 branch inside
  this same function calls into `pending_approval_registry.
  create_pending_approval(...)`, which does not exist in code yet
  (`REQ-SB-21-US-01-T03`, `Ready`, unbuilt) — per `ADR-021`'s own
  Consequences ("Tier 1... has no such dependency and can be built and
  verified independently"), `T02`'s own file uses a local (function-body)
  import for that one call, not a module-level import, so the whole module
  — and every Tier-1 scenario — loads and works correctly regardless of
  whether `REQ-SB-21-US-01-T03` has shipped yet. `T02`'s own `## Tests`
  never exercises the Tier-2 branch. **Also newly specified here, not left
  implicit:** `write_note`'s own unconditional overwrite-on-collision
  behavior (confirmed by direct reading of `vault_writer.write_note`) is a
  real risk for a model-proposed `filename_stem` that isn't guaranteed
  unique — `T02` adds a collision check before calling `write_note`,
  applying this project's own standing filename-uniqueness Constraint
  (`MEMORY.md`) to satisfy `AC-08`'s "does not overwrite or corrupt any
  existing note."
- **`T03`** — Tier-2's own resolution: extends `vault_filing_expert.py`
  (`finalize_new_top_level_area`), `pending_approval_registry.py` (the
  additive `payload` field `ADR-021` point 4 designs), and
  `pending_approvals_router.py` (the `_APPROVAL_HANDLERS` dispatch entry)
  — covers `AC-03`/`AC-04`. Depends on `T02` **and** the real, `Ready`
  cross-story tasks `REQ-SB-21-US-01-T03` (`pending_approval_registry.py`)
  and `REQ-SB-21-US-01-T06` (`pending_approvals_router.py`), per the
  guidance recorded in `REQ-SB-21-US-01`'s own `## Notes` and
  `ESCALATIONS.md` → `ESC-017`. These are real, existing, `Ready` task
  files (confirmed by direct read) — not a fabricated reference and not
  the `depends_on: []` placeholder `ESC-017` describes; `ESC-017` is
  updated to record this story's own half of its "wire the real ids in"
  resolution step as done.

`depends_on` graph across all 3 tasks plus the 4 cross-story edges
(acyclic): `T01: [REQ-SB-20-US-01-T02]`, `T02: [T01, REQ-SB-20-US-01-T05]`,
`T03: [T02, REQ-SB-21-US-01-T03, REQ-SB-21-US-01-T06]`. Every locked AC has
at least one AC-tagged manual verification step — `AC-01/02/05/06/07/08` in
`T02`, `AC-03/04` in `T03` — no locked AC without a tagged step, hard rule
4 satisfied. `status: Draft → Ready`; all 3 tasks written directly at
`status: Ready` (lockstep with the story) — none of them is individually
blocked the way `ESC-011`'s precedent required, since every real
prerequisite this story's own tasks need now has a real, `Ready` task id to
depend on (unlike `REQ-SB-36-US-02`'s own Scenario 3, see that story's own
Notes). **`gate` intentionally left `flagged`, `gate_reason` updated to
record decomposition is complete** — this decomposer did not itself
trigger a new flag (no new material assumption, no new ADR, no new
`ESCALATIONS.md` entry opened by this pass for this story) and does not
clear a flag it did not set; the human still reviews `ADR-021` and this
task breakdown together.

**Build pass (2026-08-12, `/implement-sprint`, `SPRINT-023`, coder).** All
3 tasks built in dependency order (`T01` → `T02` → `T03`) against the real,
directly-read current source of all 4 cross-story dependencies
(`REQ-SB-20-US-01-T02`/`T05`, `REQ-SB-21-US-01-T03`/`T06` — all confirmed
`Done` before writing anything). New `app/business/agent_registry.py` entry
(`"vault-filing-expert"`, data-only), new `app/business/
vault_filing_methodology.py` (`build_placement_prompt`), new `app/
business/vault_filing_expert.py` (`determine_placement_and_file`,
`finalize_new_top_level_area`), additive `payload` field on `app/business/
pending_approval_registry.create_pending_approval`, and a new
`_APPROVAL_HANDLERS` dispatch table on `app/api/pending_approvals_router.py`'s
Approve endpoint. All 8 locked ACs verified live against the real backend
`.venv`, real vault, and a real Compass Provider call (`AC-01/02/05/06/07/
08` in `T02`; `AC-03/04` in `T03`) — no locked AC blocked or weakened.

**Two scope-internal judgement calls, logged in `T02`/`T03`'s own
Implementation Logs for human spot-check (not escalations):** (1) the
model's decision JSON schema and the Tier-1/Tier-2 write frontmatter were
both extended with `referenced_customer`/`referenced_partner` /
`customer`/`partner` fields — required to satisfy `AC-02`'s own explicit
"discoverable via `list_known_customers()`" wording, found live when
`T02`'s own literal `{"tags": ...}`-only sample produced a note tagged
`customer/<slug>` that `list_known_customers()` (a frontmatter-only scan,
confirmed by direct reading) still could not see; (2) a local, untracked
`.env` gained two empty placeholder lines so `app/config.py` (extended by
a sibling story, unrelated to this one) could load at all in this
environment — no project source file touched.

**The critical Tier-2 design point — `_create_tier_2_proposal` never
checks `working_mode_registry.get_agent_working_mode(...)` at all — was
verified live, not just by code inspection:** the identical genuinely-new-
top-level-area content produced the identical `{"status":
"pending_approval", ...}` outcome with `vault-filing-expert` set to both
`"autonomous"` and `"supervised"`; a `grep` for `working_mode` across
`vault_filing_expert.py` returns zero matches.

`status: Ready → Done`. `gate: flagged → clear` — mirrors `REQ-SB-20-US-01`/
`REQ-SB-21-US-01`'s own identical precedent (both stories closed their own
architect-set `ADR`-review flag the same way once the build fully
verified all locked ACs). No new `ESCALATIONS.md`/`REVIEW-QUEUE.md` entry
from this build pass.
