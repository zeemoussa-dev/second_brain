---
id: REQ-SB-95-US-01
title: Operator Profile — one record of who the agent acts for, published into every agent's context
requirement_ids: [REQ-SB-95]
requirement_section: "REQ-SB-95: An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution"
phase: P2
status: Done
gate: clear
gate_reason: "RESOLVED operator accepted the export carrying the team's names, 2026-10-17 — was: trigger-8 (carried forward, decomposer re-pass 2026-10-16, still unresolved) — publication writes colleague names into every agent's SOUL.md and an Agent export copies that file verbatim AND ships Hermes' own profile.tar.gz (opaque bytes, ADR-014), which carries a second copy. Strip-on-export vs accept-the-leak is the operator's privacy call; AC-08 is deliberately `locked: false` and no task implements either answer. The ADR-036 trigger-3 half is CLEARED (operator rejected the SELF_EMAIL retirement; ADR-038 Accepted); the architect re-pass created and changed NO ADR."
sprint: SPRINT-086
created: 2026-10-16
updated: 2026-10-18  # coder: T04 Done — the Profile provably cannot travel in a bundle (guard only; the exclusion already held by construction, artifact_export.py unchanged). All five tasks Done; story → Done
---

# REQ-SB-95-US-01 — Operator Profile — one record of who the agent acts for, published into every agent's context

## Story

**As a** Second Brain operator
**I want** one place that records who I am, which mail addresses are mine, and
who is on my team
**So that** every agent acts for a known person with a known team, and a request
naming my own organisation ("the actions assigned to my team") can be served
instead of refused

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-95: An Agent Can Only Do What the App Can
  Do* — Finding 1 ("the agent does not know who it acts for") and the first
  **What is wanted** bullet ("An Operator Profile. One place for who the agent
  acts for: the operator's identity and mail addresses, and their team as a list
  of emails and roles. Published into every agent's context. It holds
  *membership*, not copies of people").
- **Architecture is already settled — `ADR-032`** (Accepted 2026-10-16, pending a
  human look): the Operator Profile is **configuration, not a catalogue** — one
  record at `<DATA_PATH>/data/Operator/Profile.json`, edited in Settings,
  published into every agent's context; it holds the team as emails and roles,
  never copies of people, because the vault's Person notes are filenamed by
  email; and it is **excluded from artifact export by default** because it
  carries personal data about named colleagues. *(`ADR-032`'s "it absorbs
  `self_email`" is formally dead — narrowed by `ADR-035`, then settled by
  `ADR-038`: the setting stays as it is and the Profile **mirrors** it.)*
- **Sibling stories.** `REQ-SB-95` is specced as five stories because its four
  named pieces share a spine (publish real facts into agent context, then enforce
  against them) but are not one unit of work — the same large-requirement
  precedent as `REQ-SB-82` (six-way), `REQ-SB-87` (five-way) and `REQ-SB-85`
  (three-way). This story is the **first and smallest**: a singleton record and
  the seam that publishes real operator facts into agent context.
  `REQ-SB-95-US-03` reuses that same publication seam for the Action catalogue,
  so this story deliberately lands first.
- **Grounded against the real code, not guessed.** An agent's SOUL.md text is
  composed from `prompt` + `guardrails` + `scope` in
  `AgentManager._soul_text()` (`app/business/core/agents/agent_manager.py`) —
  confirmed by direct reading. That is the one real place agent context is
  composed today, and nothing in it carries an operator fact.
- **`self_email` is not a greenfield field, and it is not changed here.** It
  exists as a real System setting (`system_settings.py`: label "Your Email
  Address", `env_key: SELF_EMAIL`, with its own `_check_email` validation), it is
  listed in `app/config.py`'s `REQUIRED_FOR_STARTUP`, it has a setup-wizard step
  (`app/business/setup_wizard.py`), and it is read by capture scripts that are
  **payload deployed into live Hermes worker profiles**. That blast radius is
  exactly why `ADR-038` leaves every one of those untouched: this story only
  *reads* the setting.

## Acceptance Criteria

<!-- Locked by the decomposer, re-authored 2026-10-16 against `ADR-038` (the
previous decomposition was discarded with the `ADR-036` SELF_EMAIL retirement).
Each scenario carries its AC-ID on the line after its closing fence. Scenario 4
is re-authored around the MIRROR; the old Scenario 7 (fresh-install boot path)
is DROPPED — `ADR-038` takes that path out of this story's blast radius
entirely, so it has nothing left to assert — and the old Scenario 8 is now
Scenario 7. Scenario 8 is the one open privacy question and is deliberately
`locked: false` (see Notes → Decomposer re-pass). -->

### Scenario 1: The operator records their own identity and team in one place

```gherkin
Given the operator opens the Operator Profile page in Settings
When the operator records their own name, their other mail addresses, their
    timezone, and their team as a list of email addresses each with a role, and
    saves
Then the facts are stored as ONE record at
    `<DATA_PATH>/data/Operator/Profile.json` — a singleton with no list, no
    create, no delete and no id namespace
  And reopening the page shows exactly what was saved
  And the Operator Profile is the only surface in the app that offers to record
    those facts
```
<!-- AC-ID: REQ-SB-95-US-01-AC-01 -->

### Scenario 2: Operator facts reach every agent's context without being hand-copied

```gherkin
Given the Operator Profile records the operator's name, their other mail
    addresses, and a team of colleagues with their roles
When the Profile is saved
Then every agent's SOUL.md carries one auto-generated, marker-delimited block
    headed `## Who you work for`, holding identical text in every agent and
    naming the operator and each recorded colleague with their role
  And that heading is never `## Guardrails` or `## Scope`, and re-saving
    replaces the agent's own prior block rather than appending a second one,
    leaving every character outside the block's own markers byte-identical
  And no agent prompt is hand-edited to carry the same facts — editing the
    Profile is the only action taken
  And an agent asked who its operator's team is answers from that block, naming
    the recorded colleagues and no one else
```
<!-- AC-ID: REQ-SB-95-US-01-AC-02 -->

### Scenario 3: A team member is a membership entry, never a copy of the person

```gherkin
Given the Operator Profile lists a team member as an email address and a role
  And the vault holds a Person note filenamed by that same email address
When the stored Profile record is read back
Then the team entry holds that email and that role and nothing else about the
    person — no name, no title, no second description
  And that email address is what reaches the real Person note, through the
    person-note lookup the app already has
```
<!-- AC-ID: REQ-SB-95-US-01-AC-03 -->

### Scenario 4: The Profile mirrors the operator's own address and never writes it

```gherkin
Given the operator's own email address is the app's own `SELF_EMAIL` setting,
    edited on Settings → System, exactly as it is today
When the Operator Profile is read, saved, and published into agent context
Then the Profile MIRRORS that address — it reads the setting, shows it on the
    Profile page as read-only text pointing at Settings → System for editing,
    and publishes it in the `## Who you work for` block alongside the facts the
    Profile does own
  And nothing in the Profile path writes it: `Profile.json` holds no copy of
    the address, `system_settings._FIELDS` still carries `self_email` with its
    `SELF_EMAIL` env key and `_check_email` validation,
    `config.REQUIRED_FOR_STARTUP` still names it, and saving the Profile does
    not call `setup_wizard.sync_settings_to_hermes(...)`
  And changing the address on Settings → System changes what the Profile
    returns and what the next publication writes, with no second edit anywhere
```
<!-- AC-ID: REQ-SB-95-US-01-AC-04 -->

### Scenario 5: An unconfigured profile is answered honestly, not invented around

```gherkin
Given this install has no Operator Profile recorded yet
When agent context is published
Then the `## Who you work for` block is still present in every agent's SOUL.md
    — it is not removed when there is nothing to say — and it states that no
    Operator Profile is configured and where to configure it
  And an agent asked who its operator's team is says exactly that, rather than
    guessing a team from mail traffic, vault notes, or anything else
```
<!-- AC-ID: REQ-SB-95-US-01-AC-05 -->

### Scenario 6: The Profile itself is not an exportable artifact

```gherkin
Given the Operator Profile records named colleagues and their email addresses
When the operator exports artifacts from this install as a portable bundle
Then the Operator Profile is not an exportable artifact kind — it cannot be
    selected for export, it is never pulled into a closure as another
    artifact's dependency, and no `Operator/Profile.json` payload is written
    into the bundle
  And nothing else about exporting changes: the artifact kinds that travel
    today still travel, with byte-identical payloads
```
<!-- AC-ID: REQ-SB-95-US-01-AC-06 -->

### Scenario 7: Publishing to every agent is one pass, not one Registry boot per agent

```gherkin
Given this install has many agents
When the Operator Profile is saved
Then the republish walks every agent once, writes each agent's soul, and
    reloads the Registry exactly ONCE for the whole pass
  And it does not call `AgentManager.update()` per agent, whose
    `_reload_registry()` is a full `asyncio.run(registry_loader.boot())`
```
<!-- AC-ID: REQ-SB-95-US-01-AC-07 -->

### Scenario 8: No colleague travels inside an exported Agent (OPEN — not locked)

```gherkin
Given the Profile's colleague names and addresses have been published into
    every agent's SOUL.md
When the operator exports an Agent artifact as a portable bundle
Then no colleague name or email address that came from the Profile appears
    anywhere in that bundle — neither in the exported agent's own `soul.md` nor
    inside the `profile.tar.gz` the export takes from Hermes
```
<!-- AC-ID: REQ-SB-95-US-01-AC-08 | locked: false -->

## Affected Screens

- **New** `src/frontend/src/pages/SettingsOperatorPage.tsx` (name indicative) —
  the Operator Profile editor: identity, own mail addresses, and the team as
  email+role rows. Reuses the already-approved live Settings conventions
  (`.card.settings-card` grid entry on `SettingsPage.tsx`,
  `.item-list`/`.item-row`/`.input` as used on `SettingsSystemPage.tsx`).
- `src/frontend/src/pages/SettingsPage.tsx` — one more card in the live
  `SETTINGS_SECTIONS` grid.
- `src/frontend/src/pages/SettingsSystemPage.tsx` — **unchanged** (`ADR-038`).
  It keeps the "Your Email Address" field and remains the one editor of that
  address; the Operator Profile page shows the same value read-only and points
  back here.
- `html-prototype/settings.html` — **not** the design authority here; the real
  `SettingsPage.tsx` card grid superseded it on 2026-08-27 (see Notes →
  Prototype parity).

## Dependencies

- **Blocked by:** none.
- **Related to:** `REQ-SB-95-US-03` (published catalogue + enforcement) — reuses
  this story's agent-context publication seam; `REQ-SB-85-US-02` (artifact
  export) — Scenario 6 constrains its default inclusion set.
- **External:** the live install's own `SELF_EMAIL` value and the Hermes worker
  profiles that already carry capture scripts reading it (see the gate flag).

## Constraints

- **One record, not a catalogue.** The Operator Profile is a singleton — no
  list/create/delete surface, no artifact kind, no id namespace.
- **Membership, not copies.** The profile stores an email and a role per team
  member and nothing else about them; the vault's Person notes remain the one
  place a person is described.
- **Excluded from artifact export by default** (`ADR-032`).
- **No second source of truth for the operator's own email** (`ADR-038`). The
  `SELF_EMAIL` setting is the one editable place; the Profile reads it and
  never writes it, and offers no editor for it.
- Publication into agent context must be **derived**, not hand-copied into any
  agent's prompt text — editing the profile must be enough.

## Implementation Tasks

Final split, decomposer re-pass, 2026-10-16 (the `ADR-036`-based split was
discarded with its task files). Dependency order is
`T01 → (T02, T03)`, `T02 → T04`, `T03 → T05`.

| ID | Type | Task | ACs | Depends on | Task File |
|---|---|---|---|---|---|
| REQ-SB-95-US-01-T01 | backend | Operator Profile entity + singleton Manager + data access over `<DATA_PATH>/data/Operator/Profile.json`, with the mirrored own-address read | AC-01, AC-03, AC-04 | — | `../Tasks/REQ-SB-95-US-01-T01-operator-profile-entity-manager-data-access.md` |
| REQ-SB-95-US-01-T02 | backend | The fourth SOUL.md marker block (`## Who you work for`) + the one-pass, one-reload republish | AC-02, AC-04, AC-05, AC-07 | T01 | `../Tasks/REQ-SB-95-US-01-T02-fourth-soul-marker-block-and-republish-pass.md` |
| REQ-SB-95-US-01-T03 | backend | `GET`/`PUT /operator/profile` — the singleton's two routes | AC-01, AC-04 | T01 | `../Tasks/REQ-SB-95-US-01-T03-operator-profile-api.md` |
| REQ-SB-95-US-01-T04 | backend | Keep the Profile out of an exported bundle, and disclose what a real Agent bundle still carries | AC-06, AC-08 (non-locked, disclosure only) | T01, T02 | `../Tasks/REQ-SB-95-US-01-T04-keep-profile-out-of-exported-bundles.md` |
| REQ-SB-95-US-01-T05 | frontend | Operator Profile Settings page + landing-grid card; the own address read-only, System page untouched | AC-01, AC-04 | T03 | `../Tasks/REQ-SB-95-US-01-T05-operator-profile-settings-page.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass — the seven locked ACs (`AC-01` …
      `AC-07`) are each verified by an AC-tagged automated test. `AC-08` is
      `locked: false` and was **disclosed, not implemented** (`T04`), which is
      what the decomposer scoped; the operator accepted the leak on 2026-10-17.
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing — `733 passed, 0 failed`
      (2026-10-18, whole backend suite)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints — **could
      not be**: the file is 86 KB against the 40 KB budget its own rule 1 sets,
      which forbids appending while over. `T04`'s constraint is parked in
      `REVIEW-QUEUE.md` with its text.
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Actions, Workflows, and entity resolution** — `REQ-SB-95-US-02`/`US-03`/
  `US-04`/`US-05`.
- **Org-chart modelling** — reporting lines, hierarchies, multiple teams. One
  flat team list of email+role is what the PRD asks for.
- **Creating or editing Person notes** from this screen — the vault owns those.
- **Multi-operator installs.** One install, one operator.

## Notes

**Operator decision, 2026-10-16 — flag cleared.** Operator, 2026-10-16: `self_email` is written at provisioning and belongs in BOTH Hermes' `.env` and the Profile -- one editable source, two written locations, kept in step by the existing `setup_wizard.sync_settings_to_hermes(..., self_email)`. Deployed capture scripts keep reading the variable they read today; nothing redeploys. Accepted limitation: a running gateway does not re-read `.env`, so a changed address reaches running agents after a restart ("you don't change your email every day"). Recorded in `ADR-035`.

**Architecture scope (architect re-pass, 2026-10-16, on `ADR-038`) — the
sections that bound the coder.** This **supersedes** the scope recorded earlier
the same day, which was written around `ADR-036`'s `SELF_EMAIL` retirement. The
operator rejected that retirement; `ADR-038` (Accepted, 2026-10-16) records the
decision and this scope matches it.

`Implementation/Architecture/architecture.md` → §An Agent Acts From a Published
Catalogue (`REQ-SB-95`) → **§Operator Profile — the Singleton Record, and the
Address It Mirrors** and **§Operator Facts in Agent Context — the Fourth Marker
Block**. Read-only context: §Catalogue Publication Into Agent Context (`US-03`
reuses the republish seam this story builds). ADRs: `ADR-032`, `ADR-035`
(Decision 2), `ADR-036` (its marker-block decision only), **`ADR-038`** (binding
— it supersedes `ADR-036`'s `SELF_EMAIL` retirement).

**Explicitly OUT OF SCOPE for this story — the coder does not touch these:**

- `app/business/system_settings.py` — `self_email` **stays** in `_FIELDS`, with
  its label "Your Email Address", its `env_key: SELF_EMAIL` and its
  `_check_email` validation. Not removed, not changed.
- `app/config.py` — `REQUIRED_FOR_STARTUP` is **not touched**. `self_email`
  stays a startup-required setting and `missing_required_settings` keeps naming
  it.
- `app/business/setup_wizard.py` — the setup-wizard step is **unchanged**, and
  `sync_settings_to_hermes(vault_path, data_path, self_email)` keeps its
  **current** source. Saving the Profile does not call it.
- `app/api/setup_router.py` and the fresh-install boot path (`REQ-SB-89`) —
  **entirely outside this story's blast radius** (`ADR-038`).
- `src/frontend/src/pages/SettingsSystemPage.tsx` — **unchanged**. It keeps the
  "Your Email Address" field and remains the one editor of that address.
- The deployed payload capture scripts (`ingest_email.py`, `ingest_meeting.py`,
  `retrofit_conversation_index.py`) — unchanged, nothing redeploys.

What is settled, so the build does not have to choose:

- **The Profile MIRRORS the operator's own address** (`ADR-038`) — it reads the
  `SELF_EMAIL` setting rather than owning it, shows it read-only on the Profile
  page pointing at Settings → System for editing, and publishes it into agent
  context with the rest of the profile.
- **The Profile solely owns everything the setting does not**: the operator's
  name, their other mail addresses, the team roster as `email` + `role` entries
  (never copies of people), and timezone. Singleton at
  `<DATA_PATH>/data/Operator/Profile.json`; excluded from artifact export by
  default.
- **Publication rides the same mechanism as the Action catalogue** (`ADR-036`,
  untouched by `ADR-038`) — a fourth auto-generated marker block in the agent's
  own SOUL.md, heading `## Who you work for`, never `## Guardrails`/`## Scope`
  (which `_split_soul_sections()` matches exactly and would mis-parse). The
  reason it cannot be a compose-time injection into `_soul_text()`: SOUL.md IS
  the store — `_to_agent()` reads it back and that is where `Agent.prompt` comes
  from.
- **The block is not removed when the Profile is unconfigured** — it says so and
  points at where to configure it. That is what makes Scenario 5 answerable.
- **One republish pass, reloading the Registry once**, not `update()` per agent
  (`update()` runs a full `registry_loader.boot()` each time — 41 of them on the
  reporting install). `US-03` reuses this exact seam.

**Prototype parity (`html-prototype/settings.html` is the only prototype screen
in scope):**

- Settings landing navigation — **Superseded**: the real `SettingsPage.tsx`
  icon-card grid replaced the prototype's flat card stack on 2026-08-27 (its own
  header comment records the operator's instruction), and the prototype is
  additionally stale on Providers. The new Operator Profile card reuses the live
  approved grid.
- The Operator Profile editor itself — **Specced** (Scenarios 1, 4) using the
  already-approved `.item-list`/`.item-row`/`.input`/`Save changes` pattern live
  on `SettingsSystemPage.tsx`. The only genuinely new interaction is the
  repeating email+role team row, which is a list of the same approved input
  controls rather than a new visual system.
- **No `/design` pass is being requested for this story.** Following the operator's
  own 2026-08-31 precedent (recorded in `REQ-SB-85-US-01`'s `gate_reason`, applied
  again on `REQ-SB-78`): build functional-first using existing app conventions,
  and take the visual pass afterwards. If the human disagrees, `/design REQ-SB-95`
  before `/plan-tasks` is the cheap correction.

**Architect pointers for `/plan-tasks` (context, not decisions):**

- Agent context is composed in `AgentManager._soul_text()` from
  `prompt`+`guardrails`+`scope` — that is where "published into every agent's
  context" has to land, and `REQ-SB-95-US-03` will want the same seam.
- `self_email` consumers found by direct search: `app/config.py`,
  `app/business/system_settings.py`, `app/business/setup_wizard.py`,
  `app/api/setup_router.py`, and three **deployed payload** scripts under
  `business/core/skills/catalog/graph/*` (`ingest_email.py`, `ingest_meeting.py`,
  `retrofit_conversation_index.py`). The payload copies already live inside real
  Hermes worker profiles, so any cutover has a redeployment component.

**Why `gate: flagged`** (the **analyst's original** MUST-FLAG review, trigger by
trigger — kept as the record of that pass. Its trigger 8 is superseded: the
`self_email` question was answered by the operator in `ADR-038`, and the flag
now stands on the export-privacy question instead. The live reasoning is in the
*Decomposer RE-pass* note below and in the frontmatter `gate_reason`.):

1. **Material assumption** — avoided rather than made: Scenario 4 asserts the
   observable outcome ("exactly one editable place, every existing consumer still
   resolves the same value") without choosing which store wins, precisely because
   choosing would be a material assumption.
2. **Unfinalised requirement** — no. `REQ-SB-95` carries no `<!-- Draft -->`
   marker (the PRD uses none anywhere) and has a complete **Acceptance**
   paragraph.
3. N/A (architect/ADR trigger). No ADR created or changed by this pass; `ADR-032`
   is pre-existing. Noted for the human: `ADR-032` is itself still awaiting a
   look and is not in `REVIEW-QUEUE.md`.
4. No `ESCALATIONS.md` entry written for this story.
5. **Oversized** — no, and avoided by the five-way split; this is the smallest
   piece (~5 tasks, S/M).
6. N/A (coder trigger).
7. **Contradictory inputs** — not contradictory, but see trigger 8.
8. **FIRED — the controlling flag.** `self_email` absorption has two defensible
   readings and real live blast radius. See the frontmatter `gate_reason` and
   `REVIEW-QUEUE.md`.

**Decomposer RE-pass, 2026-10-16 — 7 locked ACs + 1 non-locked, 5 tasks,
`Draft → Ready`.** This replaces the earlier decomposer pass (whose note is
superseded here and whose five task files were deleted with the `ADR-036`
`SELF_EMAIL` retirement). Nothing was patched — the story was re-decomposed
from `ADR-038`.

- **AC-01 … AC-07 are locked. AC-08 is `locked: false`** (reason below). Every
  locked AC has at least one AC-ID-tagged step in a task's `## Tests` — checked
  AC by AC, not assumed: AC-01 (`T01`, `T03`, `T05`), AC-02 (`T02`), AC-03
  (`T01`), AC-04 (`T01`, `T02`, `T03`, `T05`), AC-05 (`T02`), AC-06 (`T04`),
  AC-07 (`T02`). `depends_on` is acyclic (`T01 → T02 → T04`, `T01 → T03 → T05`).
  Tasks move to `Ready` with the story.
- **What happened to the stale ACs the architect flagged.**
  - *AC-04 is re-authored around the mirror.* It no longer asserts `self_email`
    is gone from `system_settings._FIELDS` / `config.REQUIRED_FOR_STARTUP`. It
    now asserts the opposite, as `ADR-038` decided — those stay, the Profile
    reads the setting, holds no copy of the address, offers no editor for it,
    and does not call `sync_settings_to_hermes`. The "exactly one editable
    place" property survives; only which surface holds it changed.
  - *The old AC-07 (fresh-install boot path) is **dropped**, and its ID is
    retired rather than reused.* `ADR-038` removes `config.REQUIRED_FOR_STARTUP`,
    the wizard step and the `REQ-SB-89` boot path from this story's blast radius
    entirely, so the scenario has nothing left to assert that this story causes.
    What remains of its value — "none of that moved" — is a regression clause
    inside the re-authored AC-04 and a `## Constraints`/`Out of Scope` line in
    every task, which is where a *don't touch this* belongs. The old AC-08
    (one republish pass) is unaffected and is now **AC-07**; the ACs are
    renumbered with no gaps, and nothing outside this story referenced the old
    numbering (checked).
- **Scenario 7 (the republish pass) stays decomposer-authored.** "One pass, one
  Registry reload" is a correctness-shaped decision (41
  `asyncio.run(registry_loader.boot())` calls on the reporting install);
  without a locked AC it is a comment a coder may reason their way past.
  `ADR-036`'s marker-block half is untouched by `ADR-038` and still binds.
- **Why AC-08 is non-locked, and why the plan does not settle it.** Publication
  writes colleague names into every agent's SOUL.md (`ADR-036` Consequences,
  accepted as local instance data). Export then copies that file verbatim —
  `content[f"agents/{id}/soul.md"] = soul_path.read_text(...)` in
  `business/logic/artifact_export.py`, confirmed by direct reading. **New this
  pass, and it enlarges the question:** the same export also writes
  `agents/<id>/profile.tar.gz`, the raw unmodified output of
  `HermesCLI.export_profile`, which `ADR-014` fixes as an **opaque-bytes**
  boundary — and a Hermes profile carries its own SOUL.md. So "strip on export"
  is not one `soul.md` substitution; it either reaches inside an
  explicitly-opaque tarball or leaves a second copy of the roster in the bundle.
  That is a privacy decision with a real cost either way, it belongs to the
  operator, and it is **not** settled here. AC-08 therefore carries
  `locked: false`, no task implements either answer, and `T04` only *discloses*
  what a real exported Agent bundle actually contains so the decision can be
  made on facts. `REVIEW-QUEUE.md` carries it. **This is the trigger-8 half of
  the gate, and it is still open.**
- **No `ESCALATIONS.md` entry written by this pass.** No oversized task — the
  heaviest (`T02`) is one marker-block pair plus one republish method in a file
  that already owns two of them.

**Architect pass, 2026-10-16 — re-flagged under trigger 3.** The analyst's
trigger-8 flag is cleared (the operator decided it; `ADR-035`). This pass fires
**trigger 3 only**: `ADR-036` was created. No assumption was made (every open
point was decided against read code, named in the ADR with its alternatives), no
`ESCALATIONS.md` entry was written, and nothing here contradicts `ADR-032`,
`ADR-035`, the PRD or `MEMORY.md`. The decomposer still runs — the human reviews
`ADR-036` and the resulting tasks in one pass.

**Architect RE-pass, 2026-10-16 — `ADR-038`, and why this story went back to
`Draft`.**

- **The previous decomposition of this story was discarded.** Its five task
  files (`T01`–`T05`) are **deleted** and the story was reset `Ready → Draft`,
  specifically because that decomposition was built on `ADR-036`'s **retirement**
  of `SELF_EMAIL` — `T03` was the retirement cutover, `T05` removed the field
  from `SettingsSystemPage.tsx`, and `T01`/`T02` inherited the "Profile is the
  one writer" shape. The operator rejected the retirement (`ADR-038`: *"Keep
  SELF_EMAIL as is, smaller change"*), so the plan was re-based rather than
  patched. No code existed, so nothing is being unwound.
- **Stale artefacts this re-pass deliberately did NOT edit** (they belong to the
  decomposer, which re-runs next): the `## Acceptance Criteria` block — **AC-04
  and AC-07 contradict `ADR-038`** as written (they assert `self_email` is gone
  from `system_settings._FIELDS` and `config.REQUIRED_FOR_STARTUP`, and that the
  wizard writes the Profile) and must be re-authored or dropped; the
  `## Implementation Tasks` table, whose five rows point at deleted files; and
  the `## Affected Screens` / `## Context` bullets written around the absorption
  question. AC-01, AC-02, AC-03, AC-05, AC-06 and AC-08 survive `ADR-038`
  untouched.
- **No ESCALATIONS entry.** Those stale ACs contradict an `Accepted` ADR, which
  is normally an `adr-deviation` escalation — but the contradiction is already
  recorded and resolved inside `ADR-038` itself ("`REQ-SB-95-US-01` is re-planned
  against this: the architect's scope and the decomposer's ACs for that story are
  redone, before any code exists"), and the re-plan is the operator's own
  instruction. Logging it again would be noise, not a record.
- **No new ADR was written, and none is needed.** `ADR-038` already records the
  decision, with its own context, supersession line and consequences. Writing an
  ADR-039 would only restate it. **Trigger 3 did not fire on this pass.**
- **`ADR-036` is left exactly as written.** It is `Accepted`, and its
  marker-block decision still stands in full; only its `SELF_EMAIL` paragraph is
  superseded, and `ADR-038` states that supersession in its own header. Rewriting
  an `Accepted` ADR is forbidden (hard rule 1), so the lineage stays visible
  across `ADR-032 → ADR-035 → ADR-036 → ADR-038`.
- **The gate is still `flagged`, but for one reason only** — the decomposer's
  trigger-8 finding, which `ADR-038` does not touch: publication writes colleague
  names into every agent's SOUL.md, and `artifact_export.py` reads an exported
  Agent's `soul.md` verbatim, so Scenario 6's second clause fails unless the
  `## Who you work for` block is stripped on export. Accepting the leak and
  weakening AC-06 is the defensible alternative. That was never written to
  `REVIEW-QUEUE.md`; this pass writes it. The earlier trigger-3 half is cleared
  (the `ADR-036` queue item is now resolved: marker block approved, retirement
  rejected).
- **Superseded pointer for the earlier "Architect pointers" bullet below/above:**
  the `self_email` consumer list is still accurate as a map of the code, but its
  closing sentence — "any cutover has a redeployment component" — no longer
  applies. Under `ADR-038` there is **no cutover**: every consumer keeps reading
  exactly what it reads today.
