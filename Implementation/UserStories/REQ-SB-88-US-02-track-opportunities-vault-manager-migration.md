---
id: REQ-SB-88-US-02
title: Migrate track-opportunities' Link write mechanics (link_opportunity.py) onto its own already-deployed vault_manager.py
requirement_ids: [REQ-SB-88]
requirement_section: "REQ-SB-88: Close the Remaining `vault_manager.py` Migration Gaps — Attachment Summarization + Opportunity Linking"
phase: P1
status: Done
gate: clear
gate_reason: ""
sprint: SPRINT-085
created: 2026-09-02
updated: 2026-09-02
---

# REQ-SB-88-US-02 — Migrate track-opportunities' Link Write Mechanics onto vault_manager.py

## Story

**As** the operator who links Threads/Meetings to Opportunities mid-chat via
`track-opportunities`' Job 3
**I want** `link_opportunity.py`'s own hand-rolled read/write primitives
(`_format_frontmatter_value`/`_parse_frontmatter_value`/`read_note`/
`insert_body_section_if_missing`/`read_body_section`/`replace_body_section`)
replaced with calls through `vault_manager.py`'s shared engine — the SAME copy
already deployed, unused, in this Skill's own `scripts/` folder
**So that** every real write this Skill performs goes through the one canonical
engine (REQ-SB-87 point 7's own binding principle, "never a second, bespoke write
path"), instead of a real, dead engine copy sitting unused next to a script that
still duplicates it, without changing the linking behavior itself.

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-88*, Finding 2 + "Real scope" point 3.
- **Real diagnosis performed directly against the live code this session, not
  assumed:** `link_opportunity.py`
  (`Hermes-Provisioning/skills/company-review/track-opportunities/scripts/
  link_opportunity.py`, 229 lines) never imports `vault_manager.py` — it maintains
  its own separate `_format_frontmatter_value`/`_parse_frontmatter_value`/
  `read_note`/`insert_body_section_if_missing`/`read_body_section`/
  `replace_body_section` clone, plus its own `_RELATED_CALLER`/
  `_CALLER_ALLOW_LISTS = {_RELATED_CALLER: frozenset({"## Related"})}` guard.
  **Confirmed live: `track-opportunities/scripts/vault_manager.py` already exists**
  (a real, deployed copy, one of the nine in `architecture.md`'s own deployment
  inventory, fully resynced to the canonical, byte-current version by
  [[REQ-SB-87-US-01]] — includes `merge_tags`, `read_note`/`write_note`,
  `get_section_content`, dynamic-children/per-caller-access support, everything the
  other eight copies have) — it is simply **never imported by `link_opportunity.py`
  at all**, a dead file sitting in the same folder. No new copy needs deploying for
  this story; only the resync-freshness of the EXISTING copy needs reconfirming
  before use.
- **Real functions confirmed by direct read, grounding what stays hand-written vs.
  what moves:**
  - `link_opportunity()` — the main entry: resolves the target note, resolves the
    Opportunity, appends the `opportunities` frontmatter wikilink, appends the
    `## Related` section wikilink. This is the mechanics this story migrates.
  - `resolve_opportunity()`/`_iter_opportunity_notes()` — title (+ optional
    `--customer`) matching across every real `Work/Customers/**/Opportunities/*/*.md`
    note, reporting genuine ambiguity (same title under >1 Customer) rather than
    guessing. This is real, Opportunity-specific business logic (the PRD's own
    words: "Opportunity-specific business logic ... stays hand-written") and is
    unaffected by this migration.
  - The `_RELATED_CALLER` allow-list guard on `## Related` — a real per-caller write
    restriction, currently enforced by `link_opportunity.py`'s own hand-rolled
    dict. `vault_manager.py`'s own canonical copy already supports the equivalent
    concept natively (`Template.json`'s own `allowed_callers` per section,
    `ADR-017`) for a note that IS on this engine's template system — but the notes
    `link_opportunity.py` writes into (a Thread or a Meeting) are identified here by
    a bare, agent-supplied `note_path`, not resolved via a template lookup, so
    whether this migration reaches into the target note's OWN template declaration
    (if any) or keeps a local, script-level guard is a real, open implementation-
    shape question for `/plan-tasks` — see Notes.
- **Precedent to follow (adapted, not copied verbatim):** [[REQ-SB-87-US-04]]
  (`Done`) is the closest real migration shape in this codebase, but that story's
  target note (a Thread) WAS resolved via the engine's own template/`id` lookup.
  Here, `link_opportunity.py`'s target note is a bare path the agent already
  resolved itself (a Thread or Meeting, not looked up by this script at all) — so
  the migration reuses `vault_manager.py`'s lower-level primitives (`read_note`,
  `write_note`, `get_section_content`, and the section-region-replace logic
  `_set_section_content` currently encapsulates) rather than its template-driven
  `modify_section()` entry point. Exact function-level shape (import the
  underscore-prefixed helpers directly vs. `vault_manager.py` gaining a small,
  public equivalent) is left to `/plan-tasks`, matching this engine's own documented
  practice of leaving "exact CLI/JSON shape" decisions to that stage (`ADR-017`'s own
  precedent).
- **No live production dependency today** — confirmed via SKILL.md: `track-
  opportunities` is "Live and conversational, not cron-triggered ... runs mid-chat
  the moment the operator's own message matches its purpose." There is no recurring
  job this migration could silently disrupt, unlike [[REQ-SB-87-US-02]]/
  [[REQ-SB-87-US-04]]'s own already-resolved rollout risk.
- **Depends on** [[REQ-SB-87-US-01]] (`Done`) only insofar as the already-deployed
  copy in this Skill's own folder is that story's own resync output — no further
  action needed unless a freshness check finds real drift (unexpected; confirmed
  current this session).

## Acceptance Criteria

### Scenario 1: The opportunities frontmatter list gains the linked wikilink, exactly as today
```gherkin
Given a Thread or Meeting note not yet linked to a given real Opportunity
When link_opportunity.py runs (now reading/writing the note's own opportunities
  frontmatter list via vault_manager.py's read_note/write_note instead of its own
  hand-rolled frontmatter regex clone)
Then the note's own opportunities frontmatter list gains a [[<Opportunity title>]]
  wikilink, exactly as today
  And the script still prints {linked, note_path, opportunity_path} with the same
  meaning as today
```
<!-- AC-ID: REQ-SB-88-US-02-AC-01 -->

### Scenario 2: The ## Related section gains the same wikilink, idempotently
```gherkin
Given the same Thread or Meeting note, now linked once
When link_opportunity.py runs again for the SAME Opportunity
Then the note's own ## Related section already lists the Opportunity's wikilink and
  is left unchanged -- linked is reported false, no duplicate line is added
  And the opportunities frontmatter list is likewise left unchanged (no duplicate
  wikilink entry)
```
<!-- AC-ID: REQ-SB-88-US-02-AC-02 -->

### Scenario 3: Opportunity resolution by title (+ optional --customer) is unaffected
```gherkin
Given more than one real Opportunity note shares the same title across different
  Customers
When link_opportunity.py runs without --customer
Then it reports the real candidate paths and refuses to guess, exactly as today
  And re-running it with the correct --customer resolves to the single intended
  Opportunity and links it
```
<!-- AC-ID: REQ-SB-88-US-02-AC-03 -->

### Scenario 4: Linking to a non-existent Opportunity is refused, never fabricated
```gherkin
Given no real Opportunity note matches the given title (with or without --customer)
When link_opportunity.py runs
Then it returns a real {"error": ...}, creates nothing, and links nothing, exactly
  as today
```
<!-- AC-ID: REQ-SB-88-US-02-AC-04 -->

### Scenario 5: Migration is retrofit-safe against already-linked real notes
```gherkin
Given a real Thread or Meeting note this Skill already linked to a real Opportunity
  before this migration
When the migrated link_opportunity.py runs again with the same note/opportunity pair
Then its own opportunities frontmatter list and ## Related section are both left
  byte-identical -- no duplicate wikilink, no lost content
```
<!-- AC-ID: REQ-SB-88-US-02-AC-05 -->

## Affected Screens

None — backend only (Hermes-Provisioning Skill scripts; no `src/frontend` or
`html-prototype/` surface).

## Dependencies

- **Blocked by:** none live — [[REQ-SB-87-US-01]] is `Done` and its resync output is
  already the copy deployed in this Skill's own folder (confirmed live).
- **Related:** [[REQ-SB-87-US-04]] — closest available precedent for the migration
  shape, though its own target note was template-resolved, unlike this story's
  bare-path target (see Context). [[REQ-SB-88-US-01]] — the sibling migration under
  the same requirement, genuinely independent (different note kind, different Skill
  folder, no shared files).
- **External:** none.

## Constraints

- `resolve_opportunity()`/`_iter_opportunity_notes()` (title/customer matching,
  ambiguity handling) stay exactly as-is, hand-written — real, Opportunity-specific
  business logic, not mechanics.
- The "never fabricate a Customer/Opportunity" discipline (Job 2/3's own documented
  Pitfall) must hold exactly as today — an unresolvable target is always a real
  error, never a created stand-in.
- This story stays manual-only, mid-chat-triggered — Job 3's own 2026-08-22 operator
  decision ("never a proactive/automatic guess") is unaffected; nothing here adds
  automatic/proactive linking.
- Job 1 (Create) and Job 2 (Update) — already plain `vault_manager.py` calls per
  SKILL.md's own 2026-08-30 note — are NOT touched by this story; only Job 3's own
  `link_opportunity.py` script is in scope.
- No new `vault_manager.py` copy is deployed — reuse the already-current, resynced
  copy already in `track-opportunities/scripts/`; if a freshness check finds real
  drift from the canonical source, resync it first rather than building against a
  stale copy.
- Confirm before removing `link_opportunity.py`'s own local `_CALLER_ALLOW_LISTS`
  guard that an equivalent real restriction on `## Related` still holds after
  migration (either via a script-level guard or the target note's own
  Template.json-declared `allowed_callers`, per Context's own disclosed open
  question) — never a silent widening of who may write that section.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-88-US-02-T01 | backend | Confirm deployed vault_manager.py freshness; migrate opportunities-frontmatter write | `Hermes-Provisioning/skills/company-review/track-opportunities/scripts/link_opportunity.py` | `REQ-SB-88-US-02-T01-confirm-freshness-migrate-frontmatter-write.md` |
| REQ-SB-88-US-02-T02 | backend | Migrate ## Related section write; resolve the per-caller access-guard question + Thread Template.json `## Related` `allowed_callers` edit | `.../scripts/link_opportunity.py`, `.second-brain/data/Templates/thread/Template.json` | `REQ-SB-88-US-02-T02-migrate-related-section-write-and-template-edit.md` |
| REQ-SB-88-US-02-T03 | backend | Scratch-vault verification + real-vault retrofit check against an already-linked note | (verification only, no code changes) | `REQ-SB-88-US-02-T03-scratch-proving-and-real-vault-retrofit-check.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — n/a, no pytest harness for this Skill yet; verified via scratch-vault + real-vault CLI runs, per each task's own Tests block
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- Job 1 (Create) / Job 2 (Update) — already migrated, plain `vault_manager.py`
  calls, untouched here.
- Job 4 (Answer questions) — no script involved at all, untouched here.
- Any change to Opportunity resolution rules, ambiguity handling, or the
  never-fabricate discipline — real business logic, unaffected.
- [[REQ-SB-88-US-01]]'s own `summarize-and-tag-files` migration + cron job — a
  genuinely independent Skill, different note kind, no shared files, its own story.
- Structural changes to `vault_manager.py`'s own public API beyond what this
  migration's own low-level primitive reuse needs (see Notes) — any broader engine
  change is an architecture-level decision, not this story's own scope.

## Notes

**Prototype parity:** not applicable — this story has no `html-prototype/` surface
(backend-only, no UI).

**Disclosed open implementation question (not a flag trigger):** `link_opportunity.
py`'s target note (a Thread or Meeting) is identified by a bare, agent-supplied
`note_path` — never looked up via `vault_manager.py`'s own template/`id` machinery
the way every other migrated caller's target is. The engine's own public,
template-driven entry points (`create`/`update`/`modify_section`) all assume a
template-resolved target; the lower-level primitives that would fit here
(`get_section_content`, and the region-replace logic `_set_section_content`
currently encapsulates) are underscore-prefixed today, i.e. not designed as public
API. Whether `/plan-tasks` resolves this by importing them directly (a
Skill-internal script reusing another module's private helpers, same folder, same
project convention already tolerated elsewhere) or by promoting a small, public
equivalent inside `vault_manager.py` itself is a genuine implementation-shape
decision, not a requirement-intent ambiguity — the outcome required (mechanics move,
behavior unchanged) is unambiguous either way, so this is left to the architect/
decomposer rather than guessed here, consistent with `ADR-017`'s own documented
"exact CLI/JSON shape is decomposer/coder-level" precedent.

**Resolution record (2026-09-02, analyst):** the one point that could otherwise read
as open (which primitives to call, per above) does not affect what this story's
own acceptance criteria require — every scenario is written against observable
behavior (what the note ends up containing), not against which specific function
name performs the write. No fact was fabricated, no PRD requirement contradicted,
and no story-level ambiguity remains — so no flag fired.

gate: clear 2026-09-02 — no MUST-FLAG trigger fired (no live production dependency,
no Draft/unfinalised requirement, no ADR touched, no contradictory inputs, the one
disclosed open point is implementation-shape, not requirement-intent).

**Architect pass (2026-09-02):** `architecture.md` §`track-opportunities`
Link-Write Migration (`REQ-SB-88-US-02`) — read `link_opportunity.py`, the
deployed `track-opportunities/scripts/vault_manager.py` copy (confirmed
byte-current against the canonical source), and the real, deployed
`thread`/`meeting` Template.json files directly before deciding.

**Architecture scope: §`track-opportunities` Link-Write Migration
(`REQ-SB-88-US-02`)** (`Implementation/Architecture/architecture.md`) — the
coder is bounded to this section.

**No new ADR — confirmed, not assumed.** Purely additive/consumptive of
`ADR-017`'s already-built `vm.modify_section`/`allowed_callers` mechanism,
plus one ordinary Template.json data edit (below) — no new engine capability.

**Open scoping question 2, resolved:** the disclosed "reach into
underscore-private helpers vs. promote a public equivalent" question is a
false choice once the real engine code is read directly — **neither.** The
already-PUBLIC, template-driven `vm.modify_section` entry point (the exact
same one `REQ-SB-87-US-04` already proved for `apply_thread_review.py`) is
sufficient: it resolves a target purely by `note_id` (no `title` lookup
required), which `link_opportunity.py` can mint/read via `vm.update` exactly
like the Thread-migration precedent — the only genuinely new piece is
picking which Template to load (`"thread"` vs. `"meeting"`), trivially
derivable from `note_path`'s own `Work/Threads/` vs. `Work/Meetings/`
prefix. No reach into `_set_section_content`, and nothing needs promoting to
public. This is decomposer/coder-level wiring, not an architecture decision.

**A real, confirmed correctness requirement for the decomposer, not just an
implementation-shape footnote:** the Constraint's own "confirm... an
equivalent real restriction on `## Related` still holds... never a silent
widening" is not hypothetical — it is load-bearing. Confirmed directly
against both real Template.json files: Thread's `## Related` already
restricts `allowed_callers` to `["link_person_to_thread"]` only (`ADR-017`)
— a migrated `vm.modify_section` call with `caller="link_opportunity"`
would be REFUSED for a Thread target unless `link_opportunity` is added to
that same array (Scenario 2's own AC fails against a Thread target
otherwise). Meeting's `## Related` carries no `allowed_callers` key at all
(open to any machine-write caller already) — zero edit needed there. Adding
`link_opportunity` to the Thread template's `## Related` allowed_callers is
the required Template.json data edit — the same ordinary extension `ADR-017`
already built for exactly this purpose (widening a section to one more
named, real caller), not a silent/undisclosed widening and not a new
architecture decision.

**Decomposer pass (2026-09-02):** all 5 scenarios locked as
`REQ-SB-88-US-02-AC-01`..`AC-05` (untagged Gherkin tightened for
buildability, wording otherwise preserved). Three tasks created,
`T01`→`T02`→`T03`, each `depends_on` its immediate predecessor: `T01`
(freshness reconfirm + `opportunities` frontmatter write), `T02` (`##
Related` write via the already-public `vm.modify_section`, carrying the
architect-flagged Thread `Template.json` `## Related` `allowed_callers`
data edit as its own in-scope task item, plus retiring the now-fully-
superseded local `_CALLER_ALLOW_LISTS` guard), `T03` (scratch regression
+ real-vault retrofit check + deployment). Every locked AC has at least
one AC-tagged manual verification step in its owning task's `## Tests`;
`depends_on` is a straight, acyclic chain. Story `status: Draft → Ready`;
all three tasks written at `status: Ready` in lockstep. `gate: clear` —
no new MUST-FLAG trigger fired at this stage.

gate: clear 2026-09-02 (decomposer) — no MUST-FLAG trigger fired: no
material assumption made (the one disclosed open implementation-shape
question was already resolved by the architect, not guessed here), no
Draft/unfinalised requirement, no ADR touched, no `ESCALATIONS.md` entry,
no oversized task (each of the 3 tasks is a bounded, single-session unit),
every locked AC has a verifiable, tagged step, no contradictory inputs,
and the task breakdown follows the architect's own already-resolved
implementation shape rather than being one of several equally valid
options.
