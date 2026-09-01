---
id: REQ-SB-87-US-01
title: vault_manager.py convergence + Thread/RawMessage Template authoring
requirement_ids: [REQ-SB-87]
requirement_section: "REQ-SB-87: Email Thread Capture — a New, LLM-Driven Pipeline (Classify, Skip Noise, Summarize, Find Pending Actions)"
phase: P1
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-017 created — vault_manager.py dynamic-children primitive + per-caller section-access model) — see REVIEW-QUEUE.md"
sprint: "SPRINT-082"
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-01 — vault_manager.py Convergence + Thread/RawMessage Template Authoring

## Story

**As a** vault-writing Skill maintainer relying on `vault_manager.py` as the one
canonical engine ("edit in exactly ONE place, then re-copy")
**I want** the three currently-drifted `vault_manager.py` copies reconciled to the
single newest/most-capable version, and real `thread`/`raw-message` `Template.json`
definitions authored in the vault's own template engine
**So that** `email-thread-capture` (REQ-SB-87-US-02) has everything it needs to
migrate its own write mechanics onto the shared engine, without the engine
re-diverging into a fourth hand-maintained copy and without inventing template
capability ad hoc mid-migration.

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-87: Email Thread Capture — a New,
  LLM-Driven Pipeline (Classify, Skip Noise, Summarize, Find Pending Actions)*
- Precedent 1: `Hermes-Provisioning/skills/vault-rebuild/meeting-capture/` —
  `ingest_meeting.py` already calls `vault_manager.py`'s `load_template`/
  `find_by_id`/`create`/`bump_folder_date`/`modify_section`/`get_section_content`
  (migrated 2026-08-25→27). Its own `vault_manager.py` copy has drifted — it lacks
  `merge_tags`, `upsert_namespaced_tag`, `insert_body_line_if_missing`,
  `_tag_slugify`, `_child_note_name`, `root.children` support, and
  `parent.on_missing: "auto_create"` — every one of which
  `create-companies-partners`'s own copy already has (confirmed by direct
  file comparison, 2026-09-01).
- Precedent 2:
  `Hermes-Provisioning/skills/company-review/create-companies-partners/scripts/
  create_companies_partners.py` — imports `vault_manager.py` directly
  (same-process, not a CLI subprocess) and is the NEWEST/most-capable of the
  three real deployed copies (confirmed via direct diff, 2026-09-01) — the
  version this story propagates outward, not a further-diverged fourth variant.
- Related: [[REQ-SB-87-US-02]] — consumes this story's resynced engine + new
  templates to actually migrate `email-thread-capture`'s write mechanics. This
  story does not touch `email-thread-capture`'s own scripts at all.
- Real, current template inventory confirmed directly (2026-09-01, live vault
  `.second-brain/data/Templates/`): `azure-kb-doc`, `compass-kb-doc`,
  `research-kb-doc`, `customer`, `file`, `meeting`, `meeting-series`, `note`,
  `opportunity`, `partner` — no `thread` or `raw-message`/equivalent template
  exists anywhere yet, confirming the PRD's own stated gap.
- **Scope expanded 2026-09-01, same day, alongside REQ-SB-87's own scope
  expansion.** The Thread template this story authors is now also the
  foundation two downstream Enrich/Capture stories build on:
  [[REQ-SB-87-US-03]] (Capture-time noise definition + Internal/Partner/
  Customer classification — needs a new classification frontmatter field
  declared here) and [[REQ-SB-87-US-05]] (Enrich-stage pending-action
  extraction — needs `## Actions` to become machine-writable by a specific,
  new caller, which it is NOT today). Scenario 2 below is revised accordingly
  — see the inline note there and MUST-FLAG.
- **Real, confirmed engine gap found reading `vault_manager.py` directly
  (2026-09-01):** the CURRENT engine's own `Template.json`-declared section
  access (`_section_access`/`_require_machine_write`) is only a binary
  `machine_write`/human-owned flag per section — it has no notion of WHICH
  caller may write a `machine_write` section, unlike `vault_lib.py`'s own
  per-caller `_CALLER_ALLOW_LISTS` (only `link_person_to_thread` may write
  `## Related`, etc.). Reproducing today's real per-caller restrictions (this
  story's own Scenario 2, unchanged from its original scope) therefore
  requires a genuine engine capability addition, not just a `Template.json`
  declaration — confirmed real, not assumed.

## Acceptance Criteria

### Scenario 1: The three deployed vault_manager.py copies converge to one canonical version
```gherkin
Given meeting-capture's own vault_manager.py copy is missing functions
  create-companies-partners's own copy already has (merge_tags,
  upsert_namespaced_tag, insert_body_line_if_missing, _tag_slugify,
  _child_note_name, template.root.children support, parent.on_missing:
  "auto_create", optional note_name auto-derivation from a resolved parent)
When the newest, most-capable copy (create-companies-partners's own) is
  re-copied into meeting-capture's own scripts/ folder, and into every other
  real, active deployment location that already carries a vault_manager.py
  copy
Then every deployed vault_manager.py copy is byte-identical to the canonical
  source
  And meeting-capture's own ingest_meeting.py, and every other existing real
  caller of vault_manager.py, continues to work unchanged -- the newer copy is
  a strict superset of the functions/behavior the older copy already exposed
```
<!-- AC-ID: REQ-SB-87-US-01-AC-01 -->

### Scenario 2: A Thread template expresses today's real Thread concept-note shape, plus the requirement's new classification field
```gherkin
Given no `thread` Template.json exists yet under the vault's own
  `.second-brain/data/Templates/`
When a `thread` Template.json is authored, matching the real frontmatter
  (type, conversation_id, tags, thread_name, last_message_at,
  last_summarized_at) and body sections (## Summary, ## Related, ## Files as
  machine-writable; ## Personal Notes as human-owned, never machine-writable)
  that email-thread-capture's own hand-written Thread notes already carry
  today, PLUS a new classification frontmatter field ([[REQ-SB-87-US-03]]'s
  own Internal-only/Partner-related/Customer-related value) declared from the
  start
Then vault_manager.py's load_template/create/find_by_id/get_section_content/
  modify_section can resolve, create, and update a Thread concept note through
  the template alone, with zero Thread-specific code
  And the template's own section-access declarations reproduce today's real
  per-caller write restrictions (only link_person_to_thread may write
  ## Related; only capture_attachments/capture_file_link may write ## Files)
  at least as strictly as vault_lib.py's own _CALLER_ALLOW_LISTS guard does
  today
  And ## Actions is declared machine-writable by exactly ONE caller identity
  (apply_thread_review.py's own, per [[REQ-SB-87-US-05]]'s new pending-action
  write) and refused to every other caller, including every one of
  email-thread-capture's own five scripts — a real, deliberate NARROWING of
  today's blanket "never machine-writable" rule for this one section only,
  not a general opening-up
  And ## Personal Notes remains refused to every caller, machine or not, with
  no exception — unchanged from today
```
<!-- AC-ID: REQ-SB-87-US-01-AC-02 -->

**Revised 2026-09-01** (originally: "## Personal Notes, ## Actions as
human-owned, never machine-writable" / "at least as strictly as vault_lib.py's
own `_CALLER_ALLOW_LISTS` guard does today," with no exception carved out for
`## Actions`). REQ-SB-87's own scope expansion (point 2: real pending-action
extraction, genuinely new) makes `## Actions` machine-writable by exactly the
one new mechanism that needs it ([[REQ-SB-87-US-05]]), while `## Personal
Notes` stays exclusively human-owned with no exception — confirmed necessary
by reading both `vault_lib.py`'s own `_HUMAN_OWNED_HEADERS` and
`apply_thread_review.py`'s own separate, identically-named constant directly:
today BOTH refuse `## Actions` unconditionally. This is a genuine, PRD-mandated
change to a previously-locked constraint, not a silent narrowing — disclosed
here and in MUST-FLAG below.

### Scenario 3: A RawMessage note can be created under its own Thread's messages/ folder, unbounded
```gherkin
Given a Thread that already has zero or more RawMessage notes under its own
  messages/ folder
When a new email is captured for that Thread's conversation_id
Then a new RawMessage note is created under that Thread's own messages/
  folder, carrying the real frontmatter shape (type, conversation_id,
  message_id, sender, sender_email, subject, received, participant_links)
  vault_lib.create_raw_message_note produces today
  And this works identically for the 1st and the Nth captured email on the
  same Thread -- the messages/ folder is never treated as a small, fixed
  sibling set, and no ceiling on how many RawMessage notes a Thread can hold
  is ever hit
```
<!-- AC-ID: REQ-SB-87-US-01-AC-03 -->

### Scenario 4: Idempotent RawMessage lookup avoids a duplicate for the same message
```gherkin
Given a RawMessage note already exists for a given (conversation_id,
  message_id) pair
When the same email is captured again
Then no duplicate RawMessage note is created, matching today's real
  idempotent behavior
```
<!-- AC-ID: REQ-SB-87-US-01-AC-04 -->

### Scenario 5: The resynced engine and new templates don't regress any already-Done, template-driven note kind
```gherkin
Given the real vault's own already-captured Customer/Partner, Opportunity,
  Meeting/meeting-series, and Note/File notes -- every one created by an
  already-`Done`, template-driven Skill
When the resynced vault_manager.py copies and the two new templates are
  deployed
Then every one of those pre-existing note kinds is still found/created/
  updated correctly by its own existing template and calling Skill, with no
  regression to any already-`Done` capability
```
<!-- AC-ID: REQ-SB-87-US-01-AC-05 -->

## Affected Screens

None — backend only (Hermes-Provisioning Skill scripts + vault template
config; no `src/frontend` or `html-prototype/` surface).

## Dependencies

- **Blocks:** [[REQ-SB-87-US-02]] — the actual `email-thread-capture` write-
  mechanics migration consumes this story's resynced engine + new templates.
- **Blocks:** [[REQ-SB-87-US-03]] (Capture-time classification — needs the new
  classification frontmatter field), [[REQ-SB-87-US-04]] (`apply_thread_
  review.py` mechanics migration — needs the resynced engine + `## Summary`
  caller access), [[REQ-SB-87-US-05]] (pending-action extraction — needs the
  widened `## Actions` caller access).
- **Related:** `Implementation/Plans/2026-08-25-vault-writer-standardization.md`,
  `Implementation/Plans/2026-08-30-vault-manager-template-trees.md` — the
  design docs this story's own engine/template shape extends.
- **External:** none.

## Constraints

- Templates are authored directly at the live vault path
  (`.second-brain/data/Templates/<id>/Template.json`) — matching the already-
  established convention that a `Template.json` change needs no separate
  deploy step (`MEMORY.md`, 2026-08-30 Decision).
- The `vault_manager.py` resync must reach every real, active Hermes profile
  deployment location this file is actually running from today, not only the
  `Hermes-Provisioning/` repo copies — per this project's own standing manual-
  deploy pattern (`[[feedback_deploy_hermes_provisioning_manually]]`).
- **The growing, one-per-item children shape (Thread's own `messages/`) is a
  genuine, unresolved architecture question, deliberately NOT decided here**:
  whether to build a real, reusable `Template.json`-declared dynamic-child-
  folder primitive (which would also let `meeting-capture`'s own analogous,
  never-solved-declaratively `occurrences/` folder adopt it later), or to
  hand-build the Thread-specific `messages/` path construction the same
  pragmatic way `ingest_meeting.py` already hand-builds its own
  `<series-folder>/Recurrences/` nesting today. This is `/plan-tasks`'s
  architect call, not this story's.
- Must never weaken any already-established section-ownership guard (a
  section a caller could not write before this migration must still be
  refused after it) — **except the one deliberate, PRD-mandated exception**:
  `## Actions` becomes machine-writable by exactly the one new caller
  [[REQ-SB-87-US-05]] introduces, per Scenario 2's revision. `## Personal
  Notes` keeps zero exceptions.
- **The engine's own section-access model must gain real per-caller
  granularity** (see Context's "confirmed engine gap" note) — declaring a
  section `machine_write` is not, by itself, enough to reproduce today's real
  per-caller restrictions; this is in scope for this story's own engine work,
  not deferred.
- Do not touch `email-thread-capture`'s own scripts — that is
  [[REQ-SB-87-US-02]]'s scope. Do not touch `summarize-and-tag-threads`'s own
  scripts (`apply_thread_review.py`) — that is [[REQ-SB-87-US-04]]'s scope;
  this story only authors the Template.json declarations both downstream
  stories consume.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-87-US-01-T01 | backend | Engine: dynamic (unbounded) child-note primitive (`growth: dynamic`) | `Hermes-Provisioning/shared/vault_manager.py`, `Hermes-Provisioning/shared/tests/test_vault_manager.py` | `REQ-SB-87-US-01-T01-vault-manager-dynamic-children.md` |
| REQ-SB-87-US-01-T02 | backend | Engine: per-caller section-write access (`allowed_callers`) | `Hermes-Provisioning/shared/vault_manager.py`, `Hermes-Provisioning/shared/tests/test_vault_manager.py` | `REQ-SB-87-US-01-T02-vault-manager-per-caller-access.md` |
| REQ-SB-87-US-01-T03 | backend | Resync canonical `vault_manager.py` to all nine real deployment locations | Nine `Hermes-Provisioning/skills/**/scripts/vault_manager.py` copies | `REQ-SB-87-US-01-T03-resync-nine-deployment-copies.md` |
| REQ-SB-87-US-01-T04 | backend | Retrofit `meeting-capture`/`create-companies-partners` callers for the new caller-identity argument | `Hermes-Provisioning/skills/vault-rebuild/meeting-capture/scripts/ingest_meeting.py`, `Hermes-Provisioning/skills/company-review/create-companies-partners/scripts/create_companies_partners.py` | `REQ-SB-87-US-01-T04-retrofit-existing-callers-caller-identity.md` |
| REQ-SB-87-US-01-T05 | backend | Author `thread`/`raw-message` `Template.json` definitions | `.second-brain/data/Templates/thread/Template.json`, `.second-brain/data/Templates/raw-message/` (or equivalent dynamic-child declaration) | `REQ-SB-87-US-01-T05-thread-raw-message-templates.md` |
| REQ-SB-87-US-01-T06 | backend | Full regression verification across every already-`Done` template-driven note kind | (verification only — no new files) | `REQ-SB-87-US-01-T06-regression-verification.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) —
      this codebase's own real precedent is `Hermes-Provisioning/shared/tests/
      test_vault_manager.py` (pytest, 44/44 passing as of the 2026-08-31
      Opportunity Log/Captures work) — new engine capability here should
      extend that same suite
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- Migrating `email-thread-capture`'s own scripts (`ingest_email.py`,
  `rename_thread.py`, `capture_attachments.py`, `capture_file_link.py`,
  `link_person_to_thread.py`, `run_full_capture.py`, `run_delta_capture.py`)
  onto the engine — that is [[REQ-SB-87-US-02]].
- Retrofitting `meeting-capture`'s own `occurrences/` folder onto whichever
  growing-children resolution this story's own Scenario 3 lands on — out of
  scope unless/until a future story explicitly picks it up; mentioned only as
  precedent/context.
- Any change to `summarize-and-tag-threads`'s own Enrich-phase JUDGMENT logic
  (what the agent reads, how it writes a summary, which companies it
  recognizes) — untouched by this story, stays hand-written/agent-driven, per
  the PRD's own point 7. **Revised 2026-09-01:** this story originally framed
  `summarize-and-tag-threads` as entirely out of scope for the whole
  requirement ("only write-mechanics move" was read as email-thread-capture
  only) — REQ-SB-87's own expansion now DOES bring `apply_thread_review.py`'s
  own write MECHANICS into scope, via the sibling stories
  [[REQ-SB-87-US-04]] (mechanics migration onto `vault_manager.py`) and
  [[REQ-SB-87-US-05]] (new pending-action capability) — neither built by this
  story, both consuming what this story authors. Only the Enrich-phase
  JUDGMENT itself (never the write mechanics) remains permanently out of this
  requirement's scope everywhere.

## Notes

**Prototype parity:** not applicable — this story has no `html-prototype/`
surface (backend-only, no UI).

**MUST-FLAG trigger fired:** trigger 8 (multiple equally-valid options / the
work is genuinely unclear) — the growing-children primitive question (a real,
reusable `Template.json` dynamic-child-folder mechanism vs. a Thread-specific
hand-built path, mirroring `ingest_meeting.py`'s own un-generalized
`occurrences/` precedent) is a genuine architecture fork with real, differently-
shaped consequences (engine capability that also benefits Meeting's own future
cleanup, vs. a smaller, more contained change) — not something to guess at
`/spec`. Also present: trigger 1 (this story's own template-shape scenarios
assume Thread/RawMessage's real current frontmatter/section shape as ground
truth, verified directly against `vault_lib.py` and live vault content, but the
EXACT `Template.json` schema fields needed to express Scenario 3 depend on
the architecture decision above). See `REVIEW-QUEUE.md` for the queued item.

**Revision breadcrumb (2026-09-01, analyst, same-day re-spec against REQ-SB-87's
own same-day scope expansion):** Scenario 2, Dependencies, Constraints, and
Non-Goals updated to (1) add the new classification frontmatter field
[[REQ-SB-87-US-03]] needs, (2) narrow `## Actions` from "never
machine-writable" to "machine-writable by exactly one new caller"
([[REQ-SB-87-US-05]]'s own pending-action mechanism) while keeping
`## Personal Notes` fully human-owned with no exception, and (3) record the
real engine gap found reading `vault_manager.py` directly (binary
machine/human section access today, no per-caller granularity — already
implied by this story's own original Scenario 2, now confirmed, not new
scope). None of this changes the growing-children flag above, which remains
open exactly as originally recorded — this revision does not resolve it and
does not need to; `gate` stays `flagged` for that original, still-unresolved
reason.

gate: flagged 2026-09-01 — see `gate_reason` and the trigger note above.

**Architect resolution (2026-09-01):** the growing-children fork is
resolved — build the real, reusable `Template.json`-declared dynamic-child
primitive (Option A), not a hand-built Thread-specific path, per `ADR-017`.
The engine's own module docstring (written 2026-08-30, before this
requirement existed) already named this exact case ("fixed/dynamic
children (OKF, Thread's messages/) are a real, later addition to this same
shape") as the anticipated evolution — this decision fulfils that, it does
not invent new complexity. `ADR-017` also resolves the confirmed
per-caller-access engine gap (a new `allowed_callers` Template.json field +
a caller-identity argument on every mutating call) and `REQ-SB-87-US-05`'s
own flagged `## Actions` replace-vs-coexist Constraint (replace, mirroring
`## Summary`). The `vault_manager.py` copy-drift question is resolved
separately, directly (no ADR needed — enforces an already-Accepted
convention): the canonical source already exists at `Hermes-Provisioning/
shared/vault_manager.py`; only `meeting-capture`'s own deployed copy has
actually drifted behind it (confirmed by direct diff — `create-companies-
partners`'s own copy already matches). The real, full deployment inventory
is nine copies, not three — see `architecture.md`'s own §Canonical
`vault_manager.py` Source & Deployment for the full list; all nine should be
re-synced as part of this story's own Scenario 1.

**Architecture scope:** `architecture.md` → §Canonical `vault_manager.py`
Source & Deployment, §`vault_manager.py` Engine Extensions — Dynamic
Children & Per-Caller Access (`REQ-SB-87-US-01`, `ADR-017`) — the decomposer
and coder are bounded by these two sections plus `ADR-017`'s own full
Decision text.

**MUST-FLAG trigger 3 fired (ADR created):** `ADR-017` — `gate` stays
`flagged` for human review of the ADR alongside the resulting tasks (the
decomposer still runs; see `REVIEW-QUEUE.md`).

**Decomposer pass (2026-09-01):** all 5 scenarios locked
(`REQ-SB-87-US-01-AC-01`..`AC-05`), 6 tasks created (`T01`..`T06`,
`depends_on: [] → T01 → T02 → {T03 → T04, T05} → T06`), every locked AC has
at least one AC-tagged verification step, `depends_on` is acyclic — `status`
advances `Draft → Ready`, all 6 tasks written at `status: Ready`. `gate`
left untouched (`flagged`, per the architect's own `ADR-017` human-review
requirement) — not this role's call to clear.

**Coder close-out (2026-09-01, `T06`):** all 6 tasks `Done`, every locked AC
(`AC-01`..`AC-05`) verified live with a real positive result — `T06`'s own
full regression pass (52/52 `test_vault_manager.py`, a real scratch-vault
`ingest_meeting.py` run, a real scratch-vault `create_companies_partners.py`
run, a live spot-check of every remaining already-`Done` note kind against
the real vault, and a re-confirmed 82/82 byte-identical deployment sync)
found zero regression to any already-`Done` capability. `status` advances
`Ready → Done`. `gate` stays `flagged` — the `ADR-017` human-review
requirement is not this role's call to clear; the open `REVIEW-QUEUE.md`
item remains for the human to resolve independently, on its own timeline.
